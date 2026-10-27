"""Offline tests of make smoke-deployed and make incident (lesson 11.3): commands/release.py's smoke-deployed and
incident, and the lesson's controlled failure end to end through the Makefile's own recipes. Nothing reaches Google
Cloud.

The stand-in is test_release_gate.py's (lesson 11.2), loaded from that file with its lane classes, its stand-in gate
and its MiniMake, and extended here by what this lesson reads and changes: documind-api's spec.template, which an update
starts from (env vars merge across revisions, F43) and a traffic move leaves alone; gcloud run services update, which
makes a revision from the template and moves the candidate tag; gcloud run services list per region; gcloud run
revisions list, with when each revision was made; GET /version from the env of the revision a URL reaches; and make,
for the smokes. A smoke that goes through the API fails while the revision serving it names a model Vertex AI does not
serve: a mistyped model's 404 is re-raised as a 500 (generator._call_or_fallback). The stand-in make sits on disk: two
tests let smoke-deployed's own run_smoke start it, stream it and filter it, and the rest ask it in-process.

Covered: smoke-deployed runs exactly the smokes whose services are deployed, in smoke-all's order and with its exports,
the gateway's and the SLM's when they are (the SLM in SLM_REGION); a red smoke, and a smoke whose own exit status says
red; GET /version recorded, or what stopped it; the traffic moving during the run; every refusal. incident's timeline,
the gated state and each way out of it (a revision no gate judged, a red revision serving, the template's drift after a
rollback, a red candidate recorded, the image or a setting make candidate does not pass) with the repair it names, the
window and the log's other lines. Where a POSIX sh is installed (CI's runner; Git Bash): the controlled failure through
the recipes, from promote-gated to the gated state again, and make smoke-deployed itself, its one HTTP request caught by
a local proxy. Cloud Run's timestamps and a secret's reference. And the wiring: the targets, .PHONY, the recipes,
smoke-all's smokes against the URLs their recipes set, make candidate's settings, mk/README.md and UNOWNED.md.
"""
import copy
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load("release_gate_for_repair_test", HERE / "test_release_gate.py")     # its lane, stand-in and MiniMake
release = gate.release                                                       # the release.py its classes patch
PROJECT, NUMBER, REGION, REPO, AUDIENCE = gate.PROJECT, gate.NUMBER, gate.REGION, gate.REPO, gate.AUDIENCE
SLM_REGION = "us-central1"
OLD, GOOD = "documind-api-00040-abc", "documind-api-00041-kel"
BAD, FIX = "documind-api-00042-typ", "documind-api-00043-fix"
SHA, MODEL, TYPO = "abc1234", "gemini-3.6-flash", "gemini-3.6-flsh"
SEVEN = ["documind-ingest", "documind-api", "documind-admin", "documind-ui", "documind-chat", "documind-mcp",
         "documind-agent"]                                                   # make up's services; no gateway, no SLM
THROUGH_THE_API = ["smoke", "smoke-mcp", "smoke-chat", "smoke-agent", "smoke-media", "smoke-reindex"]
# A revision's env as make deploy-services leaves it, with make candidate's settings at the Makefile's defaults.
ENV = {"GOOGLE_CLOUD_PROJECT": PROJECT, "RETRIEVAL_BACKEND": "vector", "SELF_URL": AUDIENCE, "DEMO_MODE": "1",
       "GENERATOR_MODEL": MODEL, "RAG_MODEL_BASE": MODEL, "ROUTING": "off", "MODEL_BACKEND": "vertex", "ARMOR": "off",
       "SEMANTIC_CACHE": "off", "RETRIEVAL_CURRENT_ONLY": "off", "RETRIEVAL_GRAPH": "off", "GRAPH_BACKEND": "firestore",
       "SPANNER_INSTANCE": "documind-graph", "SPANNER_DATABASE": "documind", "RAG_LOCATION": "us-central1",
       "GIT_SHA": SHA}


def revision(created: str, env: dict) -> dict:
    image = f"{REPO}:{env['GIT_SHA']}"
    return {"image": image, "env": dict(env), "service": "documind-api", "ready": True, "created": created,
            "digest": f"{REPO}@sha256:{hashlib.sha256(image.encode()).hexdigest()}"}


def held(git_sha: str) -> str:
    """What a revision of api:<git_sha> holds, as incident shows it: the digest the tag named, to 12 hex digits."""
    return f"api@sha256:{hashlib.sha256(f'{REPO}:{git_sha}'.encode()).hexdigest()[:12]}"


# The lane once lesson 11.2 has promoted GOOD through the gate: OLD, which make up released, more than a day old.
WORLD = {"project": PROJECT, "number": NUMBER, "region": REGION, "latest": GOOD,
         "traffic": [{"revisionName": GOOD, "percent": 100}, {"revisionName": GOOD, "tag": "candidate"}],
         "revisions": {OLD: revision("2026-11-15T08:00:00.000000Z", ENV),
                       GOOD: revision("2026-11-16T09:40:00.183520Z", ENV)},
         "template": {"image": f"{REPO}:{SHA}", "env": dict(ENV)},
         "services": {REGION: SEVEN, SLM_REGION: []}, "no_mint": []}

EXTENSION = r'''

# ---- test_release_repair.py (lesson 11.3) extends the stand-in: documind-api's spec.template and the revision an
# update makes from it, the service and revision lists, GET /version from a revision's env, and make for the smokes.
import datetime
import hashlib

VALUED = VALUED + ("--service", "--image", "--tag", "--update-env-vars", "--remove-env-vars")
SERVED = ("gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-3.1-pro-preview")      # names Vertex AI serves
AROUND_THE_API = ("smoke-gateway", "smoke-slm")
_answer_before = answer


def routed(world, base):
    """The revision a URL reaches: the tag URL the tagged one, the service's URL the one serving the most."""
    traffic = world["traffic"]
    if base == "https://candidate---documind-api-%s.%s.run.app" % (world["number"], world["region"]):
        return next((t["revisionName"] for t in traffic if t.get("tag") == "candidate"), None)
    if base == "https://documind-api-%s.%s.run.app" % (world["number"], world["region"]):
        return max((t for t in traffic if t.get("percent")), key=lambda t: t["percent"])["revisionName"]
    return None


def version(world, base):
    """GET /version: main.py's fields, from the env of the revision the URL reaches."""
    name = routed(world, base)
    if name is None:
        return None
    env = world["revisions"][name]["env"]
    return {"model_backend": env.get("MODEL_BACKEND", "vertex"), "prompt": "documind-rag@v3",
            "generator_model": env.get("GENERATOR_MODEL", "gemini-3.6-flash"), "git_sha": env.get("GIT_SHA", "unknown")}


def env_json(env):
    return [{"name": k, "value": v} for k, v in env.items()] + [
        {"name": "CHECKPOINT_DSN", "valueFrom": {"secretKeyRef": {"key": "latest", "name": "dsn"}}}]


def revision_json(world, name):
    """A revision as Cloud Run describes it: its spec holds the digest its image's tag named when it was made, never the
    tag, which only the service's spec.template keeps (a live lane's revision, 22 October 2026)."""
    rev = world["revisions"][name]
    return {"apiVersion": "serving.knative.dev/v1", "kind": "Revision",
            "metadata": {"name": name, "creationTimestamp": rev["created"],
                         "labels": {"serving.knative.dev/service": rev["service"]}},
            "spec": {"containers": [{"image": rev["digest"], "env": env_json(rev["env"])}]},
            "status": {"imageDigest": rev["digest"],
                       "conditions": [{"type": "Ready", "status": "True" if rev["ready"] else "False"}]}}


def update(world, flags):
    """gcloud run services update: a revision made from spec.template with these changes, the template moved to it;
    --no-traffic leaves the traffic where it is, --tag moves the tag."""
    template = world["template"]
    env = dict(template["env"])
    spec = flags.get("--update-env-vars")
    if isinstance(spec, str):
        sep = ","
        if spec.startswith("^"):
            sep, spec = spec[1:].split("^", 1)
        for pair in spec.split(sep):
            key, value = pair.split("=", 1)
            env[key] = value
    gone = flags.get("--remove-env-vars")
    for key in gone.split(",") if isinstance(gone, str) else []:
        env.pop(key, None)
    image = flags["--image"] if isinstance(flags.get("--image"), str) else template["image"]
    n = 1 + max(int(name.split("-")[2]) for name in world["revisions"])
    name = "documind-api-%05d-%s" % (n, chr(97 + n % 26) * 3)
    world["revisions"][name] = {
        "image": image, "env": env, "service": "documind-api", "ready": True,
        "created": world.get("now") or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "digest": image.split(":")[0] + "@sha256:" + hashlib.sha256(image.encode()).hexdigest()}
    world["template"], world["latest"] = {"image": image, "env": dict(env)}, name
    tag = flags.get("--tag") if isinstance(flags.get("--tag"), str) else None
    served = [t for t in world["traffic"] if t.get("percent")] if "--no-traffic" in flags else [
        {"revisionName": name, "percent": 100}]
    world["traffic"] = served + [t for t in world["traffic"] if t.get("tag") and t["tag"] != tag] + (
        [{"revisionName": name, "tag": tag}] if tag else [])
    return 0, "", "Service [documind-api] revision [%s] has been deployed and is serving 0 percent of traffic.\n" % name


def smoke(world, args, env):
    """make <smoke>: a smoke that goes through the API fails while the revision serving it names a model Vertex AI does
    not serve. world["smoke_exit"] gives a smoke its own exit status whatever it prints; world["move_during"] moves the
    traffic while one smoke runs."""
    target = next(a for a in args if not a.startswith("-") and "=" not in a)
    serving = routed(world, "https://documind-api-%s.%s.run.app" % (world["number"], world["region"]))
    healthy = target in AROUND_THE_API or world["revisions"][serving]["env"].get("GENERATOR_MODEL") in SERVED
    out = ["", "  DocuMind AI - a stand-in for make %s" % target, "  target: %s" % env.get("DOCUMIND_API_URL", ""),
           "  " + "-" * 56, '  [PASS] health  {"status":"ok"}']
    out += (["  [PASS] query  answerable=True citations=2", "  2 pass · 0 fail"] if healthy else
            ["  [FAIL] query  status=500 body=Internal Server Error", "  1 pass · 1 fail"])
    move = world.get("move_during") or {}
    if move.get("smoke") == target:
        tags = [t for t in world["traffic"] if t.get("tag")]
        world["traffic"] = [{"revisionName": move["to"], "percent": 100}] + tags
    with open(os.path.join(HOME, "smokes.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"target": target, "args": args, "serving": serving, "env": {k: env.get(k) for k in (
            "DOCUMIND_PROJECT", "DOCUMIND_API_URL", "DOCUMIND_TENANT", "DOCUMIND_IMPERSONATE_SA")}}) + "\n")
    return world.get("smoke_exit", {}).get(target, 0 if healthy else 1), "\n".join(out) + "\n", ""


def answer(world, tool, args):
    flags, words = parse(args)
    project, region = world["project"], world["region"]
    if tool == "make":
        return smoke(world, args, os.environ)
    if words[:3] == ["run", "services", "list"] and flags.get("--format") == "json":
        if flags.get("--project") != project:
            return 1, "", "ERROR: (gcloud.run.services.list) PERMISSION_DENIED: project [%s]\n" % flags.get("--project")
        where = flags.get("--region")
        return 0, json.dumps([{"apiVersion": "serving.knative.dev/v1", "kind": "Service", "metadata": {
            "name": name, "labels": {"cloud.googleapis.com/location": where}}}
            for name in world["services"].get(where, [])]), ""
    if words[:1] == ["run"] and (flags.get("--project"), flags.get("--region")) != (project, region):
        return _answer_before(world, tool, args)                         # its refusal of another lane
    if words[:4] == ["run", "services", "describe", "documind-api"] and flags.get("--format") == "json":
        template = world["template"]
        return 0, json.dumps({"apiVersion": "serving.knative.dev/v1", "kind": "Service",
                              "metadata": {"name": "documind-api"},
                              "spec": {"template": {"spec": {"containers": [
                                  {"image": template["image"], "env": env_json(template["env"])}]}}},
                              "status": {"latestCreatedRevisionName": world["latest"],
                                         "traffic": world["traffic"]}}), ""
    if words[:4] == ["run", "services", "update", "documind-api"]:
        return update(world, flags)
    if words[:3] == ["run", "revisions", "list"] and flags.get("--format") == "json":
        return 0, json.dumps([revision_json(world, name) for name in sorted(world["revisions"])
                              if world["revisions"][name]["service"] == flags.get("--service")]), ""
    if words[:3] == ["run", "revisions", "describe"] and flags.get("--format") == "json":
        if words[3] not in world["revisions"]:
            return 1, "", "ERROR: (gcloud.run.revisions.describe) Cannot find revision [%s].\n" % words[3]
        return 0, json.dumps(revision_json(world, words[3])), ""
    return _answer_before(world, tool, args)
'''
FAKE = gate.FAKE.replace('\nif __name__ == "__main__":', EXTENSION + '\nif __name__ == "__main__":')
assert FAKE != gate.FAKE, "test_release_gate.py's stand-in no longer ends with its __main__ block"
RUN_SMOKE = release.run_smoke


def red_report() -> dict:
    """run_eval.py's report on the mistyped model: no row came back 200."""
    report = gate.eval_report(failed=("request_success_rate", "correct_rate"))
    report["scores"].update(request_success_rate=0.0, correct_rate=0.0)
    return report


RED_WHY = "correct_rate: 0% < 68%; request_success_rate: 0% < 100%"           # what blocked red_report, as listed


class Repair(gate.InProcess):
    """test_release_gate.py's lane in-process (release.run, get_version, live_gate and the clock at their seams), with
    this file's stand-in and world and the kit's Makefile in the kit copy. run_smoke asks the stand-in make in-process;
    the tests that need the real one, which starts the stand-in make on disk, put it back."""

    def setUp(self):
        super().setUp()
        for key in ("SLM_REGION", "TENANT"):
            os.environ.pop(key, None)
        patcher = mock.patch.object(release, "run_smoke", self.fake_smoke)
        patcher.start()
        self.addCleanup(patcher.stop)
        (self.home / "fake.py").write_text(FAKE, encoding="utf-8")
        self.fake = load("release_repair_fake", self.home / "fake.py")
        shutil.copyfile(KIT / "Makefile", self.kit / "Makefile")
        self.set_world(copy.deepcopy(WORLD))
        self.bin = self.home / "bin"
        self.bin.mkdir()
        py, fake = Path(sys.executable).as_posix(), (self.home / "fake.py").as_posix()
        for tool in ("gcloud", "curl", "make"):
            path = self.bin / tool
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(f'#!/bin/sh\nexec "{py}" "{fake}" {tool} "$@"\n')
            path.chmod(0o755)
        if os.name == "nt":                     # what release.py finds through PATHEXT, as it finds gcloud.cmd
            for tool in ("gcloud", "make"):
                with open(self.bin / f"{tool}.cmd", "w", encoding="utf-8", newline="\r\n") as f:
                    f.write(f'@echo off\n"{sys.executable}" "{self.home / "fake.py"}" {tool} %*\n'
                            "exit /b %errorlevel%\n")
        self.make_exe = str(self.bin / ("make.cmd" if os.name == "nt" else "make"))
        self.log = self.kit / "evals" / "reports" / "smoke-deployed.jsonl"
        self.previous = self.kit / ".previous-revision"

    def fake_smoke(self, make, target, variables, env):
        """run_smoke in-process: the stand-in make's answer, the lines smoke-all's filter keeps printed, its status."""
        world = self.world()
        code, out, _ = self.fake.smoke(world, ["--no-print-directory", target, *variables], env)
        self.set_world(world)
        for line in out.splitlines():
            if release.SMOKE_LINE.search(line):
                print(line)
        return code

    def smokes(self) -> list:
        path = self.home / "smokes.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def runs(self) -> list:
        lines = self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []
        return [json.loads(line) for line in lines]

    def smoke_deployed(self, *extra: str) -> tuple:
        return self.main("smoke-deployed", "--project", PROJECT, "--region", REGION, "--slm-region", SLM_REGION,
                         "--make", self.make_exe, *extra)

    def incident(self, *extra: str) -> tuple:
        return self.main("incident", "--project", PROJECT, "--region", REGION, *extra)

    def updated(self, name: str, **settings) -> None:
        """What gcloud run services update --no-traffic leaves: a revision made from the template with these settings
        (GIT_SHA names the image's tag), the template moved to it, the traffic and the tags where they were."""
        world = self.world()
        world["revisions"][name] = revision(release.stamp(self.clock), {**world["template"]["env"], **settings})
        world["template"] = {"image": world["revisions"][name]["image"], "env": dict(world["revisions"][name]["env"])}
        world["latest"] = name
        self.set_world(world)

    def candidate_revision(self, name: str, **settings) -> None:
        """What make candidate leaves: the update above, the candidate tag on its revision, and its name in
        .candidate-revision."""
        self.updated(name, **settings)
        world = self.world()
        untagged = [t for t in world["traffic"] if not t.get("tag")]
        world["traffic"] = untagged + [{"revisionName": name, "tag": "candidate"}]
        self.set_world(world)
        self.candidate.write_text(name + "\n", encoding="utf-8")

    def serve(self, name: str) -> None:
        world = self.world()
        world["traffic"] = [{"revisionName": name, "percent": 100}] + [t for t in world["traffic"] if t.get("tag")]
        self.set_world(world)

    def promote_by_hand(self, name: str) -> None:
        """What make promote does, whatever the gate said: the serving revision to .previous-revision, then traffic."""
        serving = next(t["revisionName"] for t in self.world()["traffic"] if t.get("percent"))
        self.previous.write_text(serving + "\n", encoding="utf-8")
        self.serve(name)

    def later(self, minutes: int) -> None:
        self.clock += datetime.timedelta(minutes=minutes)

    def through_the_rollback(self) -> tuple:
        """Lesson 11.3 up to its repair: GOOD gated green and serving; BAD, the mistyped model, gated red and promoted
        by hand all the same; a red smoke; make rollback's move back to GOOD; a green smoke."""
        self.gated(GOOD)                                                  # lesson 11.2's record; GOOD serves already
        self.later(5)
        self.candidate_revision(BAD, GENERATOR_MODEL=TYPO)
        self.rc, self.report = 1, red_report()
        self.assertEqual(self.gate()[0], 1)
        self.rc, self.report = 0, gate.eval_report()
        self.later(2)
        self.promote_by_hand(BAD)
        self.later(1)
        red = self.smoke_deployed()
        self.later(1)
        self.serve(self.previous.read_text(encoding="utf-8").strip())     # make rollback
        self.later(1)
        green = self.smoke_deployed()
        return red, green


class SmokeDeployedTests(Repair):
    def real_run_smoke(self) -> None:
        """run_smoke itself: it starts the stand-in make on disk, streams it and filters it."""
        real = mock.patch.object(release, "run_smoke", RUN_SMOKE)
        real.start()
        self.addCleanup(real.stop)

    def test_the_smokes_of_the_deployed_services(self):
        self.real_run_smoke()
        code, out, err = self.smoke_deployed()
        self.assertEqual((code, err), (0, ""), out + err)
        smokes = self.smokes()
        self.assertEqual([s["target"] for s in smokes], THROUGH_THE_API)     # smoke-all's order, Module 9's left out
        for s in smokes:
            self.assertEqual(s["args"], ["--no-print-directory", s["target"], f"PROJECT={PROJECT}", f"REGION={REGION}",
                                         f"SLM_REGION={SLM_REGION}", "TENANT=acme"])
            self.assertEqual(s["env"], {"DOCUMIND_PROJECT": PROJECT, "DOCUMIND_API_URL": AUDIENCE,
                                        "DOCUMIND_TENANT": "acme",       # smoke-all's exports: make smoke reads these
                                        "DOCUMIND_IMPERSONATE_SA": f"documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"})
        lines = out.splitlines()
        self.assertEqual(lines[:4], [
            f">> smoke-deployed: documind-api in {PROJECT}, {REGION}, serving {GOOD}",
            "   GET /version: git_sha abc1234, gemini-3.6-flash, documind-rag@v3",
            "   deployed: " + ", ".join(sorted(SEVEN)),
            ">> 6 of smoke-all's 8 smokes; skipped, a service not deployed: smoke-gateway (documind-gateway); "
            "smoke-slm (documind-slm in us-central1, documind-gateway)"])
        self.assertEqual(lines[4:8], ["== smoke", '  [PASS] health  {"status":"ok"}',
                                      "  [PASS] query  answerable=True citations=2", "  2 pass · 0 fail"])
        self.assertNotIn("target:", out)                                   # smoke-all's filter drops the rest
        self.assertEqual(lines[-1], ">> PASS: 6 passed, 2 skipped. Recorded in evals/reports/smoke-deployed.jsonl")
        [run] = self.runs()
        self.assertEqual(run, {
            "format": "documind-smoke/1", "project": PROJECT, "region": REGION, "slm_region": SLM_REGION,
            "tenant": "acme", "serving": GOOD, "candidate": GOOD,
            "version": {"model_backend": "vertex", "prompt": "documind-rag@v3", "generator_model": MODEL,
                        "git_sha": SHA},
            "deployed": sorted(SEVEN), "ran": dict.fromkeys(THROUGH_THE_API, 0),
            "skipped": {"smoke-gateway": ["documind-gateway"], "smoke-slm": ["documind-slm", "documind-gateway"]},
            "verdict": "pass", "started": "2026-11-16T10:02:11Z", "finished": "2026-11-16T10:02:11Z"})
        lists = [c["args"] for c in self.calls() if c["args"][:3] == ["run", "services", "list"]]
        self.assertEqual(lists, [["run", "services", "list", f"--region={where}", f"--project={PROJECT}",
                                  "--format=json"] for where in (REGION, SLM_REGION)])
        mints = [c["args"] for c in self.calls() if c["args"][:2] == ["auth", "print-identity-token"]]
        self.assertEqual(mints, [["auth", "print-identity-token", "--include-email",
                                  f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com",
                                  f"--audiences={AUDIENCE}"]])
        for call in self.calls():                                          # it moves no traffic and changes nothing
            self.assertTrue(call["tool"] == "make" or "update" not in call["args"][:3], call)
        self.assertNotIn("token.", out + err)

    def test_module_9s_services_when_they_are_deployed(self):
        self.change(services={REGION: SEVEN + ["documind-gateway"], SLM_REGION: ["documind-slm"]})
        code, out, err = self.smoke_deployed()
        self.assertEqual(code, 0, out + err)
        self.assertEqual([s["target"] for s in self.smokes()], [target for target, _ in release.SMOKES])
        self.assertIn(">> 8 of smoke-all's 8 smokes\n", out)
        self.assertEqual(self.runs()[-1]["skipped"], {})
        (self.home / "smokes.jsonl").unlink()
        self.change(services={REGION: SEVEN + ["documind-gateway", "documind-slm"], SLM_REGION: []})
        self.assertEqual(self.smoke_deployed()[0], 0)                      # an SLM outside SLM_REGION: not smoke-slm's
        self.assertEqual(self.runs()[-1]["skipped"], {"smoke-slm": ["documind-slm"]})
        (self.home / "smokes.jsonl").unlink()
        calls = len(self.calls())
        code, out, err = self.main("smoke-deployed", "--project", PROJECT, "--region", REGION, "--slm-region", REGION,
                                   "--make", self.make_exe)               # SLM_REGION=REGION: one list, the SLM in it
        self.assertEqual(code, 0, out + err)
        self.assertEqual(len(self.smokes()), 8)
        self.assertEqual(len([c for c in self.calls()[calls:] if c["args"][:3] == ["run", "services", "list"]]), 1)

    def test_a_red_smoke_and_a_smokes_own_exit_status(self):
        self.candidate_revision(BAD, GENERATOR_MODEL=TYPO)
        self.promote_by_hand(BAD)
        code, out, err = self.smoke_deployed()
        self.assertEqual((code, err), (1, ""), out + err)
        self.assertIn(f">> smoke-deployed: documind-api in {PROJECT}, {REGION}, serving {BAD}\n"
                      "   GET /version: git_sha abc1234, gemini-3.6-flsh, documind-rag@v3\n", out)
        self.assertIn("== smoke\n  [PASS] health  {\"status\":\"ok\"}\n  [FAIL] query  status=500 body=Internal Server "
                      "Error\n  1 pass · 1 fail\n== smoke: FAILED (exit 1)\n== smoke-mcp\n", out)
        self.assertEqual(out.splitlines()[-1], f">> FAIL: {', '.join(THROUGH_THE_API)} failed; 0 passed, 2 skipped. "
                                               "Recorded in evals/reports/smoke-deployed.jsonl")
        self.assertEqual((self.runs()[-1]["verdict"], self.runs()[-1]["ran"]),
                         ("fail", dict.fromkeys(THROUGH_THE_API, 1)))
        self.serve(GOOD)
        self.change(smoke_exit={"smoke-chat": 3})                          # PASS lines, and exit 3: the exit decides
        self.real_run_smoke()                                              # through a process's own exit status
        code, out, err = self.smoke_deployed()
        self.assertEqual(code, 1, out + err)
        self.assertNotIn("[FAIL]", out)
        self.assertIn("  2 pass · 0 fail\n== smoke-chat: FAILED (exit 3)\n== smoke-agent\n", out)
        self.assertEqual(self.runs()[-1]["ran"]["smoke-chat"], 3)
        self.assertIn(">> FAIL: smoke-chat failed; 5 passed, 2 skipped.", out)

    def test_what_version_said_or_what_stopped_it(self):
        self.change(no_mint=["documind-ui-sa"])
        code, out, err = self.smoke_deployed()
        self.assertEqual(code, 0, out + err)                               # the smokes still ran, and were green
        self.assertEqual(len(self.smokes()), 6)
        error = self.runs()[-1]["version"]["error"]
        self.assertTrue(error.startswith(f"could not mint a token as documind-ui-sa@{PROJECT}.iam.gserviceaccount.com "
                                         "(exit 1): ERROR: (gcloud.auth.print-identity-token) PERMISSION_DENIED"),
                        error)
        self.assertIn(f"   GET /version: no answer ({error})\n", out)
        os.environ["DOCUMIND_ID_TOKEN"] = f"token.ci-member.{AUDIENCE}"      # a token from the environment, as it is
        calls = len(self.calls())
        self.assertEqual(self.smoke_deployed()[0], 0)
        self.assertEqual(self.runs()[-1]["version"]["git_sha"], SHA)
        self.assertFalse([c for c in self.calls()[calls:] if c["args"][:1] == ["auth"]])

    def test_the_traffic_moving_during_the_run(self):
        self.change(move_during={"smoke": "smoke-chat", "to": OLD})
        code, out, err = self.smoke_deployed()
        self.assertEqual(code, 0, out + err)
        self.assertEqual((self.runs()[-1]["serving"], self.runs()[-1]["serving_after"]), (GOOD, OLD))
        self.assertIn(f">> the traffic moved during the smokes, from {GOOD} to {OLD}: the results may come from both\n",
                      out)

    def test_refusals(self):
        code, out, err = self.main("smoke-deployed", "--project", PROJECT, "--region", SLM_REGION, "--make",
                                   self.make_exe)                          # the Makefile's REGION, not the lane's
        self.assertEqual((code, out), (2, ""), err)
        self.assertIn(f"STOP: documind-api is not deployed in us-central1 ({PROJECT}), so there is no lane to smoke "
                      "there: REGION is the region the lane runs in, and the Makefile's default is us-central1", err)
        calls = len(self.calls())
        code, out, err = self.smoke_deployed("--make", str(self.home / "no-make-here"))
        self.assertEqual(code, 2)
        self.assertIn("no-make-here is not on PATH: the smokes are make targets, as smoke-all's are", err)
        self.assertEqual(len(self.calls()), calls)                         # refused before Cloud Run is read
        self.assertIn("STOP: pass --slm-region", self.smoke_deployed("--slm-region", "nowhere")[2])
        self.assertIn("STOP: pass --tenant", self.smoke_deployed("--tenant", "Two Words")[2])
        makefile = self.kit / "Makefile"
        text = makefile.read_text(encoding="utf-8")
        makefile.write_text(text.replace(" smoke-gateway smoke-slm; do", " smoke-gateway; do"),
                            encoding="utf-8")                              # a smoke dropped from smoke-all
        code, out, err = self.smoke_deployed()
        self.assertEqual(code, 2)
        self.assertIn("STOP: make smoke-all runs smoke smoke-mcp smoke-chat smoke-agent smoke-media smoke-reindex "
                      "smoke-gateway, and smoke-deployed knows smoke smoke-mcp smoke-chat smoke-agent smoke-media "
                      "smoke-reindex smoke-gateway smoke-slm: change SMOKES in commands/release.py with smoke-all", err)
        self.assertEqual((self.smokes(), self.runs()), ([], []))           # no smoke ran, nothing recorded

    def test_interrupted(self):
        with mock.patch.object(release, "run_smoke", side_effect=[0, KeyboardInterrupt]) as run:
            code, out, err = self.smoke_deployed()
        self.assertEqual(code, 2)
        self.assertIn("STOP: interrupted during the smokes: nothing recorded", err)
        self.assertEqual((run.call_count, self.runs()), (2, []))


class IncidentTests(Repair):
    def test_the_gated_state_after_a_gated_promote(self):
        record = self.gated(GOOD)
        code, out, err = self.incident()
        self.assertEqual((code, err), (0, ""), out + err)
        self.assertEqual(out.splitlines(), [
            f">> documind-api in {PROJECT}, {REGION}: the last 24 hours, from the lane and this checkout's records",
            f"   2026-11-16T09:40:00Z  revision  {GOOD}  made: {held(SHA)}, GENERATOR_MODEL=gemini-3.6-flash  gate: "
            "pass, evals/reports/gate.json",                               # OLD, made 26 hours ago, is not listed
            f"   2026-11-16T10:12:11Z  gate      {GOOD}  PASS  (evals/reports/gate.json)",
            ">> now",
            f"   serving              {GOOD}  gate: pass, evals/reports/gate.json",
            f"   the candidate tag    {GOOD}  gate: pass, evals/reports/gate.json",
            f"   .candidate-revision  {GOOD}",
            "   .previous-revision   none in this checkout",
            "   spec.template        api:abc1234, GENERATOR_MODEL=gemini-3.6-flash",       # the tag; GOOD, its digest
            f">> the gated state: {GOOD} serves, judged green (evals/reports/gate.json); spec.template is what serves; "
            "no red candidate is recorded"])
        self.assertEqual(record["revision"], GOOD)
        for call in self.calls():                                          # it only reads
            self.assertNotIn("update", call["args"][:3], call)

    def test_the_controlled_failure_and_its_repair(self):
        red, green = self.through_the_rollback()
        self.assertEqual((red[0], green[0]), (1, 0), red[1] + green[1])
        code, out, err = self.incident()
        self.assertEqual((code, err), (1, ""), out + err)
        failed = ", ".join(THROUGH_THE_API)
        self.assertEqual(out.splitlines(), [
            f">> documind-api in {PROJECT}, {REGION}: the last 24 hours, from the lane and this checkout's records",
            f"   2026-11-16T09:40:00Z  revision  {GOOD}  made: {held(SHA)}, GENERATOR_MODEL=gemini-3.6-flash  gate: "
            f"pass, evals/reports/gate-{GOOD}.json",
            f"   2026-11-16T10:17:11Z  revision  {BAD}  made: {held(SHA)}, GENERATOR_MODEL=gemini-3.6-flsh  gate: fail "
            "(correct_rate: 0% < 68%; request_success_rate: 0% < 100%), evals/reports/gate.json",
            f"   2026-11-16T10:27:11Z  gate      {BAD}  FAIL  correct_rate: 0% < 68%; request_success_rate: 0% < 100%  "
            "(evals/reports/gate.json)",
            f"   2026-11-16T10:30:11Z  smoke     FAIL  serving {BAD}  /version git_sha abc1234, gemini-3.6-flsh, "
            f"documind-rag@v3  failed: {failed}; 0 passed, 2 skipped",
            f"   2026-11-16T10:32:11Z  traffic   {BAD} -> {GOOD}: seen between the smoke runs of "
            "2026-11-16T10:30:11Z and 2026-11-16T10:32:11Z",
            f"   2026-11-16T10:32:11Z  smoke     PASS  serving {GOOD}  /version git_sha abc1234, gemini-3.6-flash, "
            "documind-rag@v3  6 passed, 2 skipped",
            ">> now",
            f"   serving              {GOOD}  gate: pass, evals/reports/gate-{GOOD}.json",
            f"   the candidate tag    {BAD}  gate: fail (correct_rate: 0% < 68%; request_success_rate: 0% < 100%), "
            "evals/reports/gate.json",
            f"   .candidate-revision  {BAD}",
            f"   .previous-revision   {GOOD}",
            "   spec.template        api:abc1234, GENERATOR_MODEL=gemini-3.6-flsh",
            ">> not the gated state:",
            f"   - spec.template is not what serves: GENERATOR_MODEL gemini-3.6-flsh in the template, "
            f"gemini-3.6-flash on {GOOD}. make rollback moves traffic and leaves the template as the last update made "
            "it, and make candidate and make release-candidate start from the template (env vars merge across "
            "revisions, F43): the next candidate would carry it",
            f"   - .candidate-revision names {BAD}, which the gate judged red (evals/reports/gate.json): make promote "
            "reads no record, and would move traffic to it again",
            "   Repair: make candidate GENERATOR_MODEL=gemini-3.6-flash; then make gate; then make promote-gated"])

        self.later(3)                                                      # the template put back, not yet promoted
        self.candidate_revision(FIX, GENERATOR_MODEL=MODEL)
        code, out, err = self.incident()
        self.assertEqual(code, 0, out + err)
        self.assertIn(f">> the gated state: {GOOD} serves, judged green (evals/reports/gate-{GOOD}.json); "
                      "spec.template is what serves; no red candidate is recorded\n", out)
        self.assertIn(f"  revision  {FIX}  made: {held(SHA)}, GENERATOR_MODEL=gemini-3.6-flash  no gate in this "
                      "checkout judged it\n", out)
        self.assertEqual(self.gate()[0], 0)                                # the repair, gated and promoted
        self.promote_by_hand(FIX)
        self.later(1)
        self.assertEqual(self.smoke_deployed()[0], 0)
        code, out, err = self.incident()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.splitlines()[-1], f">> the gated state: {FIX} serves, judged green "
                                               "(evals/reports/gate.json); spec.template is what serves; no red "
                                               "candidate is recorded")
        events = [line.split()[1] for line in out.splitlines() if line.startswith("   2026-")]
        self.assertEqual(events, ["revision", "revision", "smoke", "traffic", "smoke", "revision", "gate", "traffic",
                                  "smoke"])                                # by time, not in the order they were read
        self.assertIn(f"   .previous-revision   {GOOD}\n", out)                # make rollback would return to GOOD
        self.assertIn(f"  revision  {BAD}  made: {held(SHA)}, GENERATOR_MODEL=gemini-3.6-flsh  gate: fail "
                      f"({RED_WHY}), evals/reports/gate-{BAD}.json\n", out)
        self.assertIn(f"  traffic   {GOOD} -> {FIX}: seen between the smoke runs of ", out)

    def test_a_red_revision_serving(self):
        self.gated(GOOD)
        self.candidate_revision(BAD, GENERATOR_MODEL=TYPO)
        self.rc, self.report = 1, red_report()
        self.gate()
        self.promote_by_hand(BAD)                                          # the forced promote, before the rollback
        code, out, err = self.incident()
        self.assertEqual(code, 1, out + err)
        self.assertEqual(out.splitlines()[-3:], [
            ">> not the gated state:",
            f"   - {BAD} serves, and the gate judged it red (evals/reports/gate.json: correct_rate: 0% < 68%; "
            "request_success_rate: 0% < 100%)",
            f"   Repair: make rollback, which moves traffic back to {GOOD} (.previous-revision); then make "
            "incident again"])
        self.previous.unlink()                                             # a promote made in another checkout
        self.assertIn(f"   Repair: gcloud run services update-traffic documind-api --region {REGION} --project "
                      f"{PROJECT} --to-revisions <a revision the gate judged green>=100; then make incident again\n",
                      self.incident()[1])

    def test_a_revision_no_gate_judged(self):
        self.set_world({**copy.deepcopy(WORLD), "traffic": [{"revisionName": OLD, "percent": 100}],
                        "template": {"image": f"{REPO}:{SHA}", "env": dict(ENV)}})       # as make up left it
        code, out, err = self.incident()
        self.assertEqual(code, 1, out + err)
        self.assertEqual(out.splitlines()[-3:], [
            ">> not the gated state:",
            f"   - {OLD} serves, and no gate record or gate report in this checkout judged it: make up and make "
            "deploy-services release the API with no gate",
            "   Repair: make candidate; then make gate; then make promote-gated"])
        self.assertIn("   no revision made, gate finished or make smoke-deployed run in that time\n",
                      self.incident("--hours", "0.3")[1])

    def test_the_repair_for_each_kind_of_drift(self):
        self.gated(GOOD)
        newer = "documind-api-00044-new"
        self.candidate_revision(newer, GIT_SHA="def5678")                  # make release-candidate, not yet promoted
        code, out, err = self.incident()
        self.assertEqual(code, 1, out + err)
        self.assertIn(f"   - spec.template is not what serves: image api:def5678 ({held('def5678')}) in the template, "
                      f"{held(SHA)} on {GOOD}; GIT_SHA def5678 in the template, abc1234 on {GOOD}. make rollback", out)
        self.assertEqual(out.splitlines()[-2:], [
            f"   If {newer}, the recorded candidate and what spec.template holds, is the change you mean to release: "
            "make gate, then make promote-gated. Otherwise put the template back to what serves:",
            "   Repair: make release-candidate GIT_SHA=abc1234; then make gate; then make promote-gated"])
        world = self.world()                       # GOOD serves ARMOR=on, which an older candidate set: not the default
        world["revisions"][GOOD]["env"]["ARMOR"] = "on"
        self.set_world(world)
        self.updated("documind-api-00045-upd", GIT_SHA=SHA, ARMOR="on", DEMO_MODE="0", ROUTING="on",
                     RETRIEVAL_BACKEND="rag_engine", GENERATOR_LOCATION="us-central1")    # by hand: GOOD's image again
        out = self.incident()[1]
        self.assertIn("   - spec.template is not what serves: DEMO_MODE 0 in the template, 1 on", out)
        self.assertIn("GENERATOR_LOCATION us-central1 in the template, (unset) on", out)
        self.assertNotIn(f"If {newer}", out)                               # the template is no longer its settings
        self.assertEqual(out.splitlines()[-1], (
            f"   Repair: gcloud run services update documind-api --region {REGION} --project {PROJECT} --no-traffic "
            "--update-env-vars DEMO_MODE=1; then make candidate ROUTING=off ARMOR=on RETRIEVAL_BACKEND=vector; "
            "then make gate; then make promote-gated"))                    # GENERATOR_LOCATION: make candidate drops it
        world = self.world()
        world["revisions"][GOOD]["env"].pop("RETRIEVAL_BACKEND")           # set on the template, not on what serves
        self.set_world(world)
        self.assertIn("--update-env-vars DEMO_MODE=1 --remove-env-vars RETRIEVAL_BACKEND; then make candidate "
                      "ROUTING=off ARMOR=on; then", self.incident()[1])

    def test_the_window_and_the_logs_other_lines(self):
        self.through_the_rollback()
        lines = self.log.read_text(encoding="utf-8").splitlines()
        other = json.loads(lines[0])
        self.log.write_text("\n".join([lines[0], json.dumps({**other, "region": "us-central1"}), "{not json",
                                       json.dumps({"format": "something/1"}), lines[1]]) + "\n", encoding="utf-8")
        out = self.incident("--hours", "0.02")[1]                          # 72 seconds back from 10:32:11
        events = [line for line in out.splitlines() if line.startswith("   2026-")]
        self.assertEqual([line.split()[1] for line in events], ["traffic", "smoke"])
        self.assertIn("   (3 lines of evals/reports/smoke-deployed.jsonl not this lane's smoke-deployed runs)\n", out)
        self.assertIn("STOP: --hours must be more than 0", self.incident("--hours", "0")[2])
        self.record.write_text("{", encoding="utf-8")
        out = self.incident()[1]
        self.assertIn("   (evals/reports/gate.json is not JSON)\n", out)
        self.assertIn(f"   the candidate tag    {BAD}  gate: fail ({RED_WHY}), evals/reports/gate-{BAD}.json\n",
                      out)                                                 # its report still says what the gate found

    def test_refusals(self):
        self.assertIn("STOP: pass --region", self.main("incident", "--project", PROJECT)[2])
        code, out, err = self.main("incident", "--project", PROJECT, "--region", "us-central1")
        self.assertEqual((code, out), (2, ""), err)
        self.assertIn("STOP: gcloud run services describe failed (exit 1): ERROR: (gcloud.run.services.describe) "
                      "Cannot find service [documind-api] in region [us-central1].", err)
        self.change(traffic=[{"revisionName": "documind-api-00099-zzz", "percent": 100}])
        self.assertIn("STOP: gcloud run revisions list has no documind-api-00099-zzz, which the traffic table says "
                      "serves documind-api", self.incident()[2])
        self.change(traffic=[{"revisionName": GOOD, "tag": "candidate"}])
        self.assertIn("STOP: no revision serves documind-api", self.incident()[2])


class Proxy:
    """A local HTTPS proxy that refuses every tunnel and remembers where each was asked to go: what release.py run as a
    program asks of the network, caught before anything leaves this machine."""

    def __init__(self):
        self.asked = []
        asked = self.asked

        class Refuse(BaseHTTPRequestHandler):
            def do_CONNECT(self):
                asked.append(self.path)
                self.send_response(403)
                self.end_headers()

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Refuse)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class MiniMake(gate.MiniMake):
    """test_release_gate.py's MiniMake, which also evaluates $(if condition,then[,else]): make candidate's recipe has
    two."""

    @staticmethod
    def expand(line: str, variables: dict) -> str:
        return gate.MiniMake.expand(MiniMake.conditionals(line, variables), variables)

    @staticmethod
    def conditionals(line: str, variables: dict) -> str:
        start = line.find("$(if ")
        if start < 0:
            return line
        depth, i, parts, mark = 1, start + 5, [], start + 5
        while depth:
            depth += {"(": 1, ")": -1}.get(line[i], 0)
            if line[i] == "," and depth == 1:
                parts, mark = parts + [line[mark:i]], i + 1
            i += 1
        parts.append(line[mark:i - 1])
        condition = gate.MiniMake.expand(MiniMake.conditionals(parts[0], variables), variables).strip()
        chosen = parts[1] if condition else (parts[2] if len(parts) > 2 else "")
        return line[:start] + MiniMake.conditionals(chosen, variables) + MiniMake.conditionals(line[i:], variables)


@unittest.skipUnless(gate.SH, "no POSIX sh to run the recipes in (CI's Linux runner has one; on Windows, Git Bash's)")
class RecipeTests(Repair):
    """The Makefile's recipes as make hands them to sh, against the stand-in on PATH, in the kit copy, on the real
    clock: candidate, record-candidate, release-candidate, promote, promote-gated, rollback, incident and
    smoke-deployed. make gate's work runs in-process, as in test_release_gate.py, and so does smoke-deployed in the
    controlled failure: run as a program it asks GET /version over the network, which the last test catches."""

    def setUp(self):
        super().setUp()
        real_clock = mock.patch.object(release, "now", gate.ORIGINAL_NOW)
        real_clock.start()
        self.addCleanup(real_clock.stop)
        self.proxy = Proxy()
        self.addCleanup(self.proxy.close)
        env = {"PATH": os.pathsep.join([str(self.bin), str(Path(gate.SH).parent)]), "HOME": str(self.home),
               "USERPROFILE": str(self.home), "APPDATA": str(self.home), "CLOUDSDK_CONFIG": str(self.home / "gcloud"),
               "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "HTTPS_PROXY": self.proxy.url,
               "https_proxy": self.proxy.url}
        for key in ("SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR", "TEMP", "TMP", "LANG"):
            if key in os.environ:
                env[key] = os.environ[key]
        text = gate.make_text()
        names = ("GATE_FILE", "SLM_REGION", "TENANT", *release.candidate_settings(text))
        defaults = {name: re.search(rf"^{name}[ \t]*\?=[ \t]*(.*?)[ \t]*$", text, re.M) for name in names}
        variables = {name: m.group(1) if m else "" for name, m in defaults.items()}
        variables.update(PY=shlex.quote(Path(sys.executable).as_posix()), PROJECT=PROJECT, REGION=REGION, GIT_SHA=SHA,
                         IMAGE_REPO=f"{REGION}-docker.pkg.dev/{PROJECT}/documind")
        self.make = MiniMake(self.kit, env, variables)

    def run_target(self, target: str, **overrides) -> tuple:
        self.make.output = []
        code = self.make.run(target, overrides)
        return code, "".join(self.make.output)

    def serving(self) -> str:
        return next(t["revisionName"] for t in self.world()["traffic"] if t.get("percent"))

    def test_the_controlled_failure_through_the_recipes(self):
        self.set_world({**copy.deepcopy(WORLD), "traffic": [{"revisionName": OLD, "percent": 100},
                                                            {"revisionName": GOOD, "tag": "candidate"}]})
        self.assertEqual(self.run_target("record-candidate")[0], 0)        # lesson 11.2: GOOD gated and promoted
        self.assertEqual(self.gate()[0], 0)
        code, out = self.run_target("promote-gated")
        self.assertEqual((code, self.serving()), (0, GOOD), out)

        code, out = self.run_target("candidate", GENERATOR_MODEL=TYPO)     # the controlled failure: a mistyped model
        self.assertEqual(code, 0, out)
        bad = self.candidate.read_text(encoding="utf-8").strip()
        self.assertEqual(self.world()["revisions"][bad]["env"], {**ENV, "GENERATOR_MODEL": TYPO})
        self.assertEqual(self.serving(), GOOD)                             # a candidate takes no traffic
        self.rc, self.report = 1, red_report()
        self.assertEqual(self.gate()[0], 1)                                # gated red
        code, out = self.run_target("promote-gated")
        self.assertNotEqual(code, 0)
        self.assertIn(f"  - red: the gate judged {bad} red ({RED_WHY})", out)
        self.assertEqual(self.serving(), GOOD)
        code, out = self.run_target("promote")                             # forced: make promote reads no record
        self.assertEqual((code, self.serving()), (0, bad), out)
        self.assertEqual(self.previous.read_text(encoding="utf-8"), GOOD + "\n")
        self.assertEqual(self.smoke_deployed()[0], 1)                      # a red smoke
        code, out = self.run_target("rollback")                            # the timed rollback: time make rollback
        self.assertEqual((code, self.serving()), (0, GOOD), out)
        self.assertIn(f">> traffic on {GOOD}", out)
        self.assertEqual(self.smoke_deployed()[0], 0)
        self.assertEqual(self.world()["template"]["env"]["GENERATOR_MODEL"], TYPO)   # the rollback left the template
        code, out = self.run_target("incident")
        self.assertEqual(code, 1, out)
        self.assertIn(f"   - spec.template is not what serves: GENERATOR_MODEL gemini-3.6-flsh in the template, "
                      f"gemini-3.6-flash on {GOOD}.", out)
        self.assertIn("   Repair: make candidate GENERATOR_MODEL=gemini-3.6-flash; then make gate; then make "
                      "promote-gated\n", out)

        code, out = self.run_target("release-candidate")                   # what a release would start from now
        self.assertEqual(code, 0, out)
        inherited = self.candidate.read_text(encoding="utf-8").strip()
        self.assertEqual(self.world()["revisions"][inherited]["env"]["GENERATOR_MODEL"], TYPO)
        self.assertEqual(self.gate()[0], 1)                                # and the gate judges it red again

        code, out = self.run_target("candidate", GENERATOR_MODEL=MODEL)    # the repair: incident's make line
        self.assertEqual(code, 0, out)
        fix = self.candidate.read_text(encoding="utf-8").strip()
        self.assertEqual(self.world()["revisions"][fix]["env"], ENV)       # what GOOD runs, on a new revision
        self.rc, self.report = 0, gate.eval_report()
        self.assertEqual(self.gate()[0], 0)
        code, out = self.run_target("promote-gated")
        self.assertEqual((code, self.serving()), (0, fix), out)
        self.assertEqual(self.previous.read_text(encoding="utf-8"), GOOD + "\n")
        self.assertEqual(self.smoke_deployed()[0], 0)
        code, out = self.run_target("incident")
        self.assertEqual(code, 0, out)
        self.assertIn(f">> the gated state: {fix} serves, judged green (evals/reports/gate.json); spec.template is "
                      "what serves; no red candidate is recorded\n", out)
        self.assertEqual([u[9].split("=")[0] for u in self.updates()], [GOOD, bad, GOOD, fix])   # every traffic move
        self.assertNotIn(bad, [t["revisionName"] for t in self.world()["traffic"] if t.get("percent")])

    def test_make_smoke_deployed_itself(self):
        self.change(services={REGION: SEVEN + ["documind-gateway"], SLM_REGION: []}, smoke_exit={"smoke-gateway": 1})
        code, out = self.run_target("smoke-deployed")
        self.assertEqual(code, 1, out)                                     # the gateway's smoke said red, by its exit
        self.assertEqual([s["target"] for s in self.smokes()], THROUGH_THE_API + ["smoke-gateway"])
        self.assertIn(">> 7 of smoke-all's 8 smokes; skipped, a service not deployed: smoke-slm (documind-slm in "
                      "us-central1)\n", out)                               # SLM_REGION and TENANT from the Makefile
        self.assertIn("  2 pass · 0 fail\n== smoke-gateway: FAILED (exit 1)\n>> FAIL: smoke-gateway failed; 6 "
                      "passed, 1 skipped. Recorded in evals/reports/smoke-deployed.jsonl", out)
        self.assertEqual({s["env"]["DOCUMIND_TENANT"] for s in self.smokes()}, {"acme"})
        [run] = self.runs()
        self.assertEqual(self.proxy.asked, [f"documind-api-{NUMBER}.{REGION}.run.app:443"] * 2)   # tried twice, caught
        self.assertTrue(run["version"]["error"].startswith(f"GET {AUDIENCE}/version failed twice: "), run["version"])
        self.assertIn("Tunnel connection failed", run["version"]["error"])  # the proxy refused; nothing answered


class PureTests(unittest.TestCase):
    def test_cloud_run_times(self):
        utc = datetime.timezone.utc
        self.assertEqual(release.lane_time("2026-11-16T09:40:00.183520Z"),
                         datetime.datetime(2026, 11, 16, 9, 40, 0, 183520, tzinfo=utc))
        self.assertEqual(release.lane_time("2026-11-16T09:40:00.5Z"),
                         datetime.datetime(2026, 11, 16, 9, 40, 0, 500000, tzinfo=utc))
        self.assertEqual(release.lane_time("2026-11-16T09:40:00.123456789Z"),     # nanoseconds, cut to micro
                         datetime.datetime(2026, 11, 16, 9, 40, 0, 123456, tzinfo=utc))
        nine_forty = datetime.datetime(2026, 11, 16, 9, 40, tzinfo=utc)
        self.assertEqual(release.lane_time("2026-11-16T15:10:00+05:30"), nine_forty)              # IST
        self.assertEqual(release.lane_time("2026-11-16T04:40:00-05:00"), nine_forty)
        for text in ("", None, "2026-11-16 09:40:00", "2026-11-16T09:40:00"):
            self.assertIsNone(release.lane_time(text), text)

    def test_a_secret_is_its_reference(self):
        spec = {"containers": [{"image": "api:1", "env": [
            {"name": "A", "value": "1"}, {"name": "EMPTY"},
            {"name": "DSN", "valueFrom": {"secretKeyRef": {"name": "dsn", "key": "latest"}}}]}, {"image": "sidecar:2"}]}
        self.assertEqual(release.container_of(spec), ("api:1", {"A": "1", "EMPTY": "", "DSN": "<secret dsn:latest>"}))
        self.assertEqual(release.container_of(None), ("", {}))


class WiringTests(unittest.TestCase):
    def read(self, *parts: str) -> str:
        return KIT.joinpath(*parts).read_text(encoding="utf-8")

    def test_the_make_targets(self):
        mk, readme = self.read("Makefile"), self.read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                       # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        for target in ("smoke-deployed", "incident"):
            self.assertIn(target, phony)
            self.assertIn(f"`{target}`", readme)
        make = MiniMake(KIT, {}, {})
        self.assertEqual(make.rule("smoke-deployed"), (["guard-project"], [
            "@$(PY) commands/release.py smoke-deployed --project $(PROJECT) --region $(REGION) "
            "--slm-region $(SLM_REGION) --tenant $(TENANT)"]))             # no $(MAKE): make -n runs nothing
        self.assertEqual(make.rule("incident"), (["guard-project"], [
            "@$(PY) commands/release.py incident --project $(PROJECT) --region $(REGION) --gate-file $(GATE_FILE) "
            "--hours $${HOURS:-24}"]))
        self.assertEqual(re.search(r"(?m)^SLM_REGION \?= (\S+)$", mk).group(1), release.SLM_REGION_DEFAULT)

    def test_smoke_alls_smokes_and_the_services_their_recipes_call(self):
        text = gate.make_text()
        self.assertEqual(release.smoke_all_targets(text), [target for target, _ in release.SMOKES])
        loop = release.recipe_of(text, "smoke-all")
        self.assertIn("DOCUMIND_API_URL=https://documind-api-$$NUMBER.$(REGION).run.app", loop)      # to every smoke
        url = re.compile(r"https://(documind-[a-z]+)-\$\$NUMBER\.\$\(([A-Z_]+)\)")
        for target, needs in release.SMOKES:
            urls = set(url.findall(release.recipe_of(text, target)))
            self.assertEqual(set(needs), {name for name, _ in urls} or {"documind-api"}, target)
            for name, where in urls:
                self.assertEqual(where, "SLM_REGION" if name in release.IN_SLM_REGION else "REGION", (target, name))

    def test_make_candidates_settings(self):
        text = self.read("Makefile")
        settings = release.candidate_settings(text)
        recipe = release.recipe_of(text, "candidate")
        for name, default in settings.items():
            self.assertIn(f"{name}=$({name})", recipe)
            found = re.search(rf"(?m)^{name}[ \t]*\?=[ \t]*(.*?)[ \t]*$", text)
            self.assertEqual(default, found.group(1) if found else None, name)
        self.assertLessEqual({"GENERATOR_MODEL", "RETRIEVAL_BACKEND", "RAG_LOCATION", "GENERATOR_LOCATION"},
                             set(settings))
        self.assertEqual((settings["RETRIEVAL_BACKEND"], settings["GENERATOR_LOCATION"]), (None, ""))

    def test_the_lanes_project_and_region_are_no_candidate_settings(self):
        """13 October 2026: the recipe's record-candidate line passes PROJECT=$(PROJECT) REGION=$(REGION), and both came
        back as settings of the candidate - harmless for documind-api's drift check, and wrong."""
        text = self.read("Makefile")
        self.assertIn("record-candidate PROJECT=$(PROJECT) REGION=$(REGION)", release.recipe_of(text, "candidate"))
        self.assertFalse({"PROJECT", "REGION"} & set(release.candidate_settings(text)))

    def test_the_files_are_listed(self):
        # An UNOWNED.md row until a lesson page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = self.read("UNOWNED.md"), self.read("INDEX.md")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        for f in ("commands/release.py", "mk/release.mk", "commands/tests/test_release_repair.py"):
            self.assertTrue(f"`{f}`" in unowned or f in quoted, f)
        self.assertIn("evals/reports/", self.read(".gitignore").splitlines())     # the smoke log beside the gate's


if __name__ == "__main__":
    unittest.main()
