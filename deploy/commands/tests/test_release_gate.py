"""Offline tests of make gate and make promote-gated (lesson 11.2): commands/release.py's gate and gate-check, with a
stand-in gcloud and a stand-in gate. Nothing reaches Google Cloud.

The stand-in gcloud (FAKE, below) keeps one lane's documind-api in a JSON file beside it: the traffic table with the
candidate tag, the latest revision, and each revision's image (the tag it was deployed by), digest, GIT_SHA and what it
answers on GET /version. As on Cloud Run, a revision holds its digest and only the service's spec.template, which made
the latest revision, keeps the tag. update-traffic moves traffic as Cloud Run does, keeping the tags, and every call is
logged. In-process, release.run (every gcloud call goes
through it) is replaced by a call into the stand-in, release.get_version by its /version, and release.live_gate by a
stand-in gate that writes the report evals/run_eval.py --report would and returns its exit code. get_version itself is
tried against a local HTTP server.

Then, where a POSIX sh is installed (CI's Linux runner; Git Bash on Windows), the same stand-in sits on PATH as gcloud
and curl, and the recipes of record-candidate, promote-gated, promote and rollback run as make hands them to the shell,
read from the Makefile and mk/*.mk, in a copy of the kit's release files: promote-gated lets the gated revision through
and stops any other before promote runs, and promote and rollback do what they did before. make is not needed: MiniMake
runs the few make rules these recipes use, and fails on any other.

Covered: the record's fields and files; a red record; a leak; a gate that stops (no report, the tag moved while the rows
were asked, interrupted) and leaves no record; each refusal before a row is asked (no candidate file, the tag on another
revision or on none, a revision not Ready, no digest, no GIT_SHA, an image-only update (F43), a later revision made from
the template, /version answering as another sha, a token that cannot be minted, gcloud missing); gate-check's pass and
each refusal (no record, not a record, another lane, another revision, a red record, a missing or edited report, a
record that says pass over a red report, stale by age, a time in the future, stale by rules, the tag moved, a revision
that is not what was judged); and the wiring: the targets, .PHONY, GATE_FILE, mk/README.md and UNOWNED.md.
"""
import contextlib
import copy
import datetime
import hashlib
import importlib.util
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load("release_under_gate_test", KIT / "commands" / "release.py")
THRESHOLDS = load("run_eval_for_gate_test", KIT / "evals" / "run_eval.py").THRESHOLDS

PROJECT, NUMBER, REGION = "documind-course-demo", "123456789012", "asia-south1"
REPO = f"{REGION}-docker.pkg.dev/{PROJECT}/documind/api"
SERVING, CAND, NEWER = "documind-api-00041-kel", "documind-api-00042-xyz", "documind-api-00043-pqr"
SHA = {SERVING: "0f1e2d3", CAND: "abc1234", NEWER: "9a8b7c6"}
AUDIENCE = f"https://documind-api-{NUMBER}.{REGION}.run.app"
TAG_URL = f"https://candidate---documind-api-{NUMBER}.{REGION}.run.app"
START = datetime.datetime(2026, 11, 16, 10, 2, 11, tzinfo=datetime.timezone.utc)
FILES = ("commands/release.py", "commands/infrastructure.py", *release.RULES)    # the kit copy the recipes run in


def revision(name: str, **extra) -> dict:
    return {"image": f"{REPO}:{SHA[name]}", "digest": f"{REPO}@sha256:{hashlib.sha256(name.encode()).hexdigest()}",
            "git_sha": SHA[name], "ready": True, "service": "documind-api", **extra}


WORLD = {"project": PROJECT, "number": NUMBER, "region": REGION, "latest": CAND,
         "traffic": [{"revisionName": SERVING, "percent": 100}, {"revisionName": CAND, "tag": "candidate"}],
         "revisions": {name: revision(name) for name in (SERVING, CAND, NEWER)}, "no_mint": []}

# The stand-in for gcloud and curl, one module: run as a program by the PATH wrappers, imported by the in-process tests.
FAKE = r'''
"""A stand-in for gcloud and curl over one lane's documind-api (test_release_gate.py): world.json beside this file
holds the traffic table, the candidate tag and the revisions; calls.jsonl gets a line per call."""
import json
import os
import sys

HOME = os.path.dirname(os.path.abspath(__file__))
VALUED = ("--region", "--project", "--format", "--to-revisions", "--audiences", "--impersonate-service-account")


def parse(args):
    """(flags, words): --name=value, --name value for the flags that take one, --name alone, and the rest."""
    flags, words, i = {}, [], 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--") and "=" in arg:
            name, value = arg.split("=", 1)
            flags[name] = value
        elif arg in VALUED and i + 1 < len(args):
            flags[arg] = args[i + 1]
            i += 1
        elif arg.startswith("--"):
            flags[arg] = True
        else:
            words.append(arg)
        i += 1
    return flags, words


def version(world, base):
    """GET /version: the tag URL answers from the tagged revision, the canonical URL from the one serving the most."""
    traffic = world["traffic"]
    if base == "https://candidate---documind-api-%s.%s.run.app" % (world["number"], world["region"]):
        name = next((t["revisionName"] for t in traffic if t.get("tag") == "candidate"), None)
    elif base == "https://documind-api-%s.%s.run.app" % (world["number"], world["region"]):
        name = max((t for t in traffic if t.get("percent")), key=lambda t: t["percent"])["revisionName"]
    else:
        name = None
    if name is None:
        return None
    rev = world["revisions"][name]
    return dict({"model_backend": "vertex", "generator_model": "gemini-3.6-flash", "prompt": "documind-rag@v3",
                 "git_sha": rev.get("git_sha") or "unknown"}, **rev.get("answers", {}))


def container(world, rev, image):
    """A revision's container as Cloud Run returns it: this image, and its env."""
    env = [{"name": "GOOGLE_CLOUD_PROJECT", "value": world["project"]}]
    env += [{"name": "GIT_SHA", "value": rev["git_sha"]}] if rev.get("git_sha") else []
    env += [{"name": "CHECKPOINT_DSN", "valueFrom": {"secretKeyRef": {"key": "latest", "name": "dsn"}}}]
    return {"image": image, "env": env}


def answer(world, tool, args):
    flags, words = parse(args)
    project, region = world["project"], world["region"]
    if tool == "curl":
        body = version(world, args[-1][:-len("/version")]) if args and args[-1].endswith("/version") else None
        return (0, json.dumps(body), "") if body else (22, "", "curl: (22) The requested URL returned error: 404")
    if words[:2] == ["projects", "describe"]:
        if words[2:3] != [project]:
            return 1, "", "ERROR: (gcloud.projects.describe) NOT_FOUND: Requested entity was not found."
        if flags.get("--format") == "value(projectNumber)":
            return 0, world["number"] + "\n", ""
        return 0, json.dumps({"projectId": project, "projectNumber": world["number"]}), ""
    if words[:2] == ["auth", "print-identity-token"]:
        account = str(flags.get("--impersonate-service-account", "")).split("@")[0]
        warning = "WARNING: This command is using service account impersonation.\n"
        if account in world["no_mint"]:
            return 1, "", warning + ("ERROR: (gcloud.auth.print-identity-token) PERMISSION_DENIED: Permission "
                                     "'iam.serviceAccounts.getOpenIdToken' denied on resource (or it may not exist).\n")
        return 0, "token.%s.%s\n" % (account, flags.get("--audiences")), warning
    if words[:1] == ["run"] and (flags.get("--project"), flags.get("--region")) != (project, region):
        return 1, "", "ERROR: (gcloud.run.%s.%s) Cannot find service [documind-api] in region [%s].\n" % (
            words[1], words[2], flags.get("--region"))
    if words[:4] == ["run", "services", "describe", "documind-api"]:
        if flags.get("--format") == "value(status.latestCreatedRevisionName)":
            return 0, world["latest"] + "\n", ""
        if flags.get("--format") == "json":
            # spec.template made the latest revision, and keeps the image as that deploy named it: by its tag.
            made = world["revisions"].get(world["latest"])
            return 0, json.dumps({"apiVersion": "serving.knative.dev/v1", "kind": "Service",
                                  "metadata": {"name": "documind-api"},
                                  "spec": {"template": {"spec": {"containers": [
                                      container(world, made, made["image"])] if made else []}}},
                                  "status": {"latestCreatedRevisionName": world["latest"],
                                             "traffic": world["traffic"]}}), ""
    if words[:4] == ["run", "services", "update-traffic", "documind-api"] and "--to-revisions" in flags:
        name, percent = flags["--to-revisions"].split("=")
        if name not in world["revisions"]:
            return 1, "", "ERROR: (gcloud.run.services.update-traffic) Revision [%s] not found.\n" % name
        tags = [{"revisionName": t["revisionName"], "tag": t["tag"]} for t in world["traffic"] if t.get("tag")]
        world["traffic"] = [{"revisionName": name, "percent": int(percent)}] + tags
        return 0, "", "Updating traffic...done.\n"
    if words[:3] == ["run", "revisions", "describe"] and flags.get("--format") == "json":
        rev = world["revisions"].get(words[3])
        if rev is None:
            return 1, "", "ERROR: (gcloud.run.revisions.describe) Cannot find revision [%s].\n" % words[3]
        # A revision holds the digest its image's tag named when it was made, as Cloud Run writes it, never the tag.
        return 0, json.dumps({
            "apiVersion": "serving.knative.dev/v1", "kind": "Revision",
            "metadata": {"name": words[3], "labels": {"serving.knative.dev/service": rev["service"]}},
            "spec": {"containers": [container(world, rev, rev["digest"])]},
            "status": {"imageDigest": rev["digest"],
                       "conditions": [{"type": "Ready", "status": "True" if rev["ready"] else "False"}]}}), ""
    return 99, "", "stand-in gcloud: unexpected call: " + " ".join([tool] + args) + "\n"


def handle(tool, args):
    path = os.path.join(HOME, "world.json")
    with open(path, encoding="utf-8") as f:
        world = json.load(f)
    with open(os.path.join(HOME, "calls.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"tool": tool, "args": args}) + "\n")
    code, out, err = answer(world, tool, args)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(world, f)
    return code, out, err


if __name__ == "__main__":
    code, out, err = handle(sys.argv[1], sys.argv[2:])
    sys.stdout.buffer.write(out.encode("utf-8"))          # bytes: no CRLF in a shell's $(...) on Windows
    sys.stderr.buffer.write(err.encode("utf-8"))
    sys.exit(code)
'''


def eval_report(failed=(), leaks=(), stale=(), required_failed=(), source=None, rows=65) -> dict:
    """The report evals/run_eval.py --report writes (its keys), with these blockers."""
    scores = {k: (THRESHOLDS[k] - 0.07 if k in failed else 1.0) for k in THRESHOLDS}
    return {"api_url": TAG_URL, "source": source, "rows": rows, "scores": scores, "thresholds": dict(THRESHOLDS),
            "judged": sorted(THRESHOLDS), "failed": sorted(failed), "leaks": list(leaks), "stale": list(stale),
            "isolation": [], "required_failed": list(required_failed), "quote_support_rate": 1.0,
            "version_check_skipped": [], "records": [{"id": "lk-01", "shape": "lookup", "pass": not failed}]}


class Lane(unittest.TestCase):
    """A temporary home: the stand-in and its world, and a copy of the kit's release files for KIT."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="release_gate_test_"))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.kit = self.home / "kit"
        for rel in FILES:
            (self.kit / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(KIT / rel, self.kit / rel)
        (self.home / "fake.py").write_text(FAKE, encoding="utf-8")
        self.fake = load("release_gate_fake", self.home / "fake.py")
        self.set_world(copy.deepcopy(WORLD))
        self.candidate = self.kit / ".candidate-revision"
        self.record = self.kit / "evals" / "reports" / "gate.json"

    def world(self) -> dict:
        return json.loads((self.home / "world.json").read_text(encoding="utf-8"))

    def set_world(self, world: dict) -> None:
        (self.home / "world.json").write_text(json.dumps(world), encoding="utf-8")

    def change(self, **fields) -> None:
        world = self.world()
        world.update(fields)
        self.set_world(world)

    def change_revision(self, name: str, **fields) -> None:
        world = self.world()
        world["revisions"][name].update(fields)
        self.set_world(world)

    def calls(self) -> list:
        path = self.home / "calls.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        return [json.loads(line) for line in lines]

    def updates(self) -> list:
        return [c["args"] for c in self.calls() if c["args"][:3] == ["run", "services", "update-traffic"]]


class InProcess(Lane):
    """release.py's functions with the stand-ins at its seams: run (gcloud), get_version, live_gate and the clock."""

    def setUp(self):
        super().setUp()
        self.clock = START
        self.rc, self.report, self.during, self.gates = 0, eval_report(), None, []
        self.version_calls = []
        for name, value in (("KIT", self.kit), ("run", self.fake_run), ("get_version", self.fake_version),
                            ("live_gate", self.fake_gate), ("now", lambda: self.clock)):
            patcher = mock.patch.object(release, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        for key in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "PROJECT", "REGION"):
            os.environ.pop(key, None)

    def fake_run(self, argv, cwd=None):
        self.assertEqual(argv[0], "gcloud", argv)
        code, out, err = self.fake.handle(argv[0], list(argv[1:]))
        return subprocess.CompletedProcess(argv, code, out, err)

    def fake_version(self, url, token):
        """The tag URL's /version, as the stand-in's world says; a token minted for any audience but the service's
        canonical URL is refused, as the API refuses it (F42)."""
        self.version_calls.append((url, token))
        if not token.endswith("." + AUDIENCE):
            raise release.Stop(f"GET {url}/version answered HTTP 401: the token was refused")
        return self.fake.version(self.world(), url)

    def fake_gate(self, url, report, member, outsider):
        self.gates.append({"url": url, "report": Path(report), "member": member, "outsider": outsider})
        if self.during:
            self.during()
        self.clock += datetime.timedelta(minutes=10)                      # the rows take a while
        if self.report is not None:
            Path(report).parent.mkdir(parents=True, exist_ok=True)
            Path(report).write_text(json.dumps(self.report, indent=1), encoding="utf-8")
        return self.rc

    def main(self, *args: str) -> tuple:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = release.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def gate(self, *extra: str) -> tuple:
        return self.main("gate", "--project", PROJECT, "--region", REGION, *extra)

    def check(self, *extra: str) -> tuple:
        return self.main("gate-check", "--project", PROJECT, "--region", REGION, *extra)

    def recorded(self) -> dict:
        return json.loads(self.record.read_text(encoding="utf-8"))

    def gated(self, name: str = CAND) -> dict:
        """A green gate on name, recorded; the clock left at its finish."""
        self.candidate.write_text(name + "\n", encoding="utf-8")
        code, out, err = self.gate()
        self.assertEqual(code, 0, out + err)
        return self.recorded()


class GateTests(InProcess):
    def test_a_green_gate_records_the_revision_it_judged(self):
        self.candidate.write_text(CAND + "\n", encoding="utf-8")
        code, out, err = self.gate()
        self.assertEqual((code, err), (0, ""), out + err)
        record = self.recorded()
        report = self.kit / "evals" / "reports" / f"gate-{CAND}.json"
        rev = WORLD["revisions"][CAND]
        fields = ("format", "project", "region", "service", "revision", "image", "digest", "git_sha", "url", "report",
                  "eval_exit", "verdict", "blocked", "rows")
        self.assertEqual({k: record[k] for k in fields},
                         {"format": "documind-gate/1", "project": PROJECT, "region": REGION, "service": "documind-api",
                          "revision": CAND, "image": rev["image"], "digest": rev["digest"], "git_sha": SHA[CAND],
                          "url": TAG_URL, "report": f"evals/reports/gate-{CAND}.json", "eval_exit": 0,
                          "verdict": "pass", "blocked": [], "rows": 65})
        self.assertEqual(record["report_sha256"], hashlib.sha256(report.read_bytes()).hexdigest())
        self.assertEqual((record["scores"], record["thresholds"]), (self.report["scores"], THRESHOLDS))
        self.assertEqual(record["answers_as"]["git_sha"], SHA[CAND])
        self.assertEqual(record["answers_as"]["generator_model"], "gemini-3.6-flash")
        self.assertEqual(record["rules"], {rel: hashlib.sha256((KIT / rel).read_bytes()).hexdigest()
                                           for rel in ("evals/run_eval.py", "evals/golden.jsonl", "evals/required.json",
                                                       "evals/manifest.json")})
        self.assertEqual((record["started"], record["finished"]), ("2026-11-16T10:02:11Z", "2026-11-16T10:12:11Z"))
        # the stand-in gate asked the tag URL, as the member and the outsider, each with a token for the canonical URL
        self.assertEqual(self.gates, [{"url": TAG_URL, "report": report, "member": f"token.documind-ui-sa.{AUDIENCE}",
                                       "outsider": f"token.documind-outsider-sa.{AUDIENCE}"}])
        self.assertEqual(self.version_calls, [(TAG_URL, f"token.documind-ui-sa.{AUDIENCE}")])
        mints = [c["args"] for c in self.calls() if c["args"][:2] == ["auth", "print-identity-token"]]
        self.assertEqual(mints, [["auth", "print-identity-token", "--include-email",
                                  f"--impersonate-service-account={sa}@{PROJECT}.iam.gserviceaccount.com",
                                  f"--audiences={AUDIENCE}"] for sa in ("documind-ui-sa", "documind-outsider-sa")])
        for call in self.calls():                                          # it moves no traffic and writes nothing
            args = call["args"]
            self.assertTrue(args[:2] == ["auth", "print-identity-token"] or "describe" in args[:3], call)
        self.assertIn(f">> gate: {CAND}, the revision .candidate-revision names and the candidate tag routes to", out)
        self.assertIn(f"   image   {rev['image']}\n", out)                  # the tag, read from spec.template
        self.assertIn(f"   digest  {rev['digest']}\n", out)
        self.assertIn(f"   GET /version on {TAG_URL}: git_sha {SHA[CAND]}, gemini-3.6-flash, documind-rag@v3\n", out)
        self.assertIn(f"   {CAND}  PASS  65 rows, eval exit 0, report sha256 {record['report_sha256']}\n", out)
        self.assertNotIn("token.", out + err)                              # a token is never printed

    def test_a_red_gate_records_red_and_exits_1(self):
        self.candidate.write_text(CAND, encoding="utf-8")
        self.rc, self.report = 1, eval_report(failed=("correct_rate",), required_failed=("lk-06: refused", "vr-01: x"))
        code, out, err = self.gate()
        self.assertEqual((code, err), (1, ""), out + err)
        record = self.recorded()
        self.assertEqual((record["verdict"], record["eval_exit"]), ("fail", 1))
        self.assertEqual(record["blocked"], ["correct_rate: 61% < 68%", "required: 2 mandatory rows did not pass"])
        self.assertIn(f"   {CAND}  FAIL  correct_rate: 61% < 68%; required: 2 mandatory rows did not pass\n", out)
        self.assertIn("make promote-gated refuses it (make promote reads no record)", out)

    def test_a_leak_is_red(self):
        self.candidate.write_text(CAND, encoding="utf-8")
        self.rc, self.report = 2, eval_report(leaks=("iso-02: answer contained 'AAACA1234B'",))
        code, out, err = self.gate()
        self.assertEqual(code, 1, out + err)
        self.assertEqual((self.recorded()["verdict"], self.recorded()["eval_exit"]), ("fail", 2))
        self.assertEqual(self.recorded()["blocked"], ["leaks: 1 must_not_contain hit"])

    def test_an_exit_the_report_does_not_explain_is_still_red(self):
        self.candidate.write_text(CAND, encoding="utf-8")
        self.rc = 1
        self.assertEqual(self.gate()[0], 1)
        record = self.recorded()
        self.assertEqual((record["verdict"], record["blocked"]), ("fail", ["evals/run_eval.py exited 1"]))

    def test_a_report_that_blocks_is_red_whatever_the_exit(self):
        self.candidate.write_text(CAND, encoding="utf-8")
        for report, blocked in ((eval_report(source="hr_policy_2026.md"),
                                 ["scoped to hr_policy_2026.md: a gate asks every row"]),
                                (eval_report(stale=("vr-01: answer contained '30 days'",)),
                                 ["stale: a version row cited a retired figure"]),
                                ({"rows": 65}, ["not a report evals/run_eval.py --report writes"])):
            self.report = report
            self.assertEqual(self.gate()[0], 1)
            self.assertEqual((self.recorded()["verdict"], self.recorded()["blocked"]), ("fail", blocked))

    def test_a_gate_that_stops_before_its_verdict_leaves_no_record(self):
        old = self.gated()                                                 # a green record from an earlier gate
        self.rc, self.report = 2, None                                     # the eval refused to start: no report
        code, out, err = self.gate()
        self.assertEqual(code, 2)
        self.assertIn("STOP: evals/run_eval.py wrote no report (exit 2): there is no verdict, and no gate record", err)
        self.assertFalse(self.record.exists(), "the earlier green record must not stand for this gate")
        self.assertTrue(old["verdict"] == "pass")

        self.rc, self.report = 0, eval_report()                            # the tag moved while the rows were asked
        self.during = lambda: self.change(traffic=[{"revisionName": SERVING, "percent": 100},
                                                   {"revisionName": NEWER, "tag": "candidate"}])
        code, out, err = self.gate()
        self.assertEqual(code, 2)
        self.assertIn(f"STOP: the candidate tag moved to {NEWER} while the rows were asked, so the answers may have "
                      "come from more than one revision: no gate record. make gate again", err)
        self.assertFalse(self.record.exists())

        self.set_world(copy.deepcopy(WORLD))
        self.during = mock.Mock(side_effect=KeyboardInterrupt)             # Ctrl-C during the rows
        code, out, err = self.gate()
        self.assertEqual(code, 2)
        self.assertIn("STOP: interrupted while the rows were asked: no gate record", err)
        self.assertFalse(self.record.exists())

    def test_refusals_before_any_row_is_asked(self):
        self.record.parent.mkdir(parents=True)
        self.record.write_text('{"kept": true}', encoding="utf-8")         # an earlier record survives a refusal
        r = self.gate()
        self.assertEqual(r[0], 2)
        self.assertIn("STOP: .candidate-revision is missing: make release-candidate (or make candidate) records", r[2])
        self.candidate.write_text("documind-chat-00001-abc", encoding="utf-8")
        self.assertIn("STOP: .candidate-revision does not name a documind-api revision: 'documind-chat-00001-abc'",
                      self.gate()[2])
        self.candidate.write_text(CAND, encoding="utf-8")
        cases = [
            (dict(traffic=[{"revisionName": SERVING, "percent": 100}, {"revisionName": NEWER, "tag": "candidate"}]),
             f"STOP: the candidate tag is on {NEWER}, but .candidate-revision names {CAND}: the tag URL would answer "
             "from a revision make promote would not move traffic to."),
            (dict(traffic=[{"revisionName": SERVING, "percent": 100}]),
             f"STOP: the candidate tag is on no revision, but .candidate-revision names {CAND}"),
        ]
        for world, message in cases:
            self.set_world({**copy.deepcopy(WORLD), **world})
            code, out, err = self.gate()
            self.assertEqual((code, out), (2, ""), err)
            self.assertIn(message, err)
        for fields, message in (
                (dict(ready=False), "it is not Ready (status.conditions)"),
                (dict(digest=f"{REPO}:{SHA[CAND]}"), "Cloud Run reports no image digest for it (status.imageDigest)"),
                (dict(git_sha=""), "it carries no GIT_SHA, so GET /version cannot say which build answers"),
                (dict(service="documind-chat"), "it belongs to documind-chat, not documind-api"),
                (dict(image=f"{REPO}:{SHA[NEWER]}"),                       # F43: the image moved, GIT_SHA did not
                 f"it runs api:{SHA[NEWER]} but its GIT_SHA says {SHA[CAND]}: env vars merge across revisions, so an "
                 f"image-only update keeps the old GIT_SHA (F43). make release-candidate GIT_SHA={SHA[NEWER]} "
                 "sets both")):
            self.set_world(copy.deepcopy(WORLD))
            self.change_revision(CAND, **fields)
            code, out, err = self.gate()
            self.assertEqual((code, out), (2, ""), err)
            self.assertIn(f"STOP: {CAND} cannot be gated: {message}", err)
        self.set_world({**copy.deepcopy(WORLD), "latest": NEWER})         # an update made a revision after the candidate
        code, out, err = self.gate()
        self.assertEqual((code, out), (2, ""), err)
        self.assertIn(f"STOP: {CAND} cannot be gated: documind-api's spec.template has made a later revision "
                      "(status.latestCreatedRevisionName), so the tag its image was deployed by cannot be read: a "
                      "revision holds only the digest, and an image-only update (F43) cannot be ruled out. make "
                      "release-candidate again", err)
        self.set_world(copy.deepcopy(WORLD))
        self.change_revision(CAND, answers={"git_sha": SHA[SERVING]})       # the tag URL answers as another build
        code, out, err = self.gate()
        self.assertEqual(code, 2)
        self.assertIn(f"STOP: {TAG_URL} answers as git_sha '{SHA[SERVING]}', but {CAND} carries GIT_SHA {SHA[CAND]}: "
                      "the tag URL is not serving the revision this gate would record", err)
        self.set_world({**copy.deepcopy(WORLD), "no_mint": ["documind-outsider-sa"]})
        code, out, err = self.gate()
        self.assertEqual(code, 2)
        self.assertIn(f"STOP: could not mint a token as documind-outsider-sa@{PROJECT}.iam.gserviceaccount.com "
                      "(exit 1): ERROR: (gcloud.auth.print-identity-token) PERMISSION_DENIED", err)
        self.assertIn(f"make operators PROJECT={PROJECT} grants the operator the token-creator role on it", err)
        code, out, err = self.main("gate", "--project", PROJECT, "--region", "us-central1")
        self.assertEqual(code, 2)
        self.assertIn("STOP: gcloud run services describe failed (exit 1): ERROR: (gcloud.run.services.describe) "
                      "Cannot find service [documind-api] in region [us-central1].", err)
        self.assertIn("STOP: pass --region", self.main("gate", "--project", PROJECT)[2])
        self.assertEqual(self.gates, [])                                   # no row was asked
        self.assertEqual(self.record.read_text(encoding="utf-8"), '{"kept": true}')

    def test_tokens_from_the_environment_are_used_as_they_are(self):
        self.candidate.write_text(CAND, encoding="utf-8")
        os.environ.update(DOCUMIND_ID_TOKEN=f"token.ci-member.{AUDIENCE}",
                          DOCUMIND_OUTSIDER_TOKEN="token.ci-outsider.x")
        self.assertEqual(self.gate()[0], 0)
        self.assertEqual((self.gates[0]["member"], self.gates[0]["outsider"]),
                         (f"token.ci-member.{AUDIENCE}", "token.ci-outsider.x"))
        self.assertFalse([c for c in self.calls() if c["args"][:1] == ["auth"]])

    def test_no_gcloud(self):
        empty = self.home / "empty"
        empty.mkdir()
        self.candidate.write_text(CAND, encoding="utf-8")
        with mock.patch.object(release, "run", ORIGINAL_RUN), mock.patch.dict(os.environ, {"PATH": str(empty)}):
            code, out, err = self.gate()
            self.assertEqual(code, 2)
            self.assertIn("STOP: gcloud is not on PATH", err)
            code, out, err = self.check()
        self.assertIn("there is no gate record", err)                      # refused from the files, before any gcloud


ORIGINAL_RUN = release.run


class GateCheckTests(InProcess):
    def test_a_fresh_green_record_of_the_recorded_candidate_passes(self):
        record = self.gated()
        self.clock += datetime.timedelta(hours=2)
        code, out, err = self.check()
        self.assertEqual((code, err), (0, ""), out + err)
        self.assertEqual(out.splitlines(), [
            f"gate record evals/reports/gate.json: {CAND} passed at 2026-11-16T10:12:11Z, 2.0 hours ago",
            f"  digest  {record['digest']}  GIT_SHA {SHA[CAND]}",
            f"  report  evals/reports/gate-{CAND}.json  sha256 {record['report_sha256']}",
            "  .candidate-revision names it and the candidate tag is not on another revision; judged by this "
            "checkout's evals/run_eval.py, evals/golden.jsonl, evals/required.json, evals/manifest.json"])
        reads = [c["args"][:3] for c in self.calls()[-2:]]
        self.assertEqual(reads, [["run", "services", "describe"], ["run", "revisions", "describe"]])
        self.change(traffic=[{"revisionName": CAND, "percent": 100}])      # promoted, and the tag removed by hand
        self.assertEqual(self.check()[0], 0)

    def refused(self, *extra: str) -> list:
        code, out, err = self.check(*extra)
        self.assertEqual((code, out), (1, ""), err)
        self.assertTrue(err.startswith("REFUSED: the gate record "), err)
        return [line[4:] for line in err.splitlines()[1:]]

    def test_no_record_or_not_a_record(self):
        self.candidate.write_text(CAND, encoding="utf-8")
        self.assertEqual(self.refused(), ["there is no gate record at evals/reports/gate.json: make gate judges the "
                                          "candidate and writes it"])
        self.record.parent.mkdir(parents=True)
        for text, why in (("{", "evals/reports/gate.json is not JSON"),
                          ('{"revision": "x"}', "evals/reports/gate.json is not a gate record (documind-gate/1, which "
                                                "make gate writes)"),
                          ('{"format": "documind-gate/1"}', "evals/reports/gate.json has no project, region, service, "
                                                            "revision, image, digest, git_sha, report, report_sha256, "
                                                            "eval_exit, verdict, rules, finished")):
            self.record.write_text(text, encoding="utf-8")
            self.assertEqual(self.refused(), [why])
        self.assertEqual(self.calls(), [])                                 # nothing asked of the lane

    def test_another_revision(self):
        self.gated()
        self.candidate.write_text(NEWER, encoding="utf-8")                 # a newer candidate, recorded here
        self.assertEqual(self.refused(), [
            f"another revision: the record names {CAND}, and make promote would move traffic to {NEWER} "
            f"(.candidate-revision). The gate judged {CAND}; make gate judges {NEWER}"])
        self.candidate.unlink()
        self.assertEqual(self.refused()[0][:45], ".candidate-revision is missing: make release-")

    def test_a_scratch_record_naming_another_revision(self):
        """Lesson 11.2's Change-it: a copy of the record, edited to name another revision, through GATE_FILE."""
        record = self.gated()
        scratch = self.home / "scratch.json"
        scratch.write_text(json.dumps({**record, "revision": NEWER}), encoding="utf-8")
        reasons = self.refused("--gate-file", str(scratch))
        self.assertEqual(reasons, [f"another revision: the record names {NEWER}, and make promote would move traffic "
                                   f"to {CAND} (.candidate-revision). The gate judged {NEWER}; make gate judges {CAND}"])
        self.assertEqual(self.check()[0], 0)                               # the real record is untouched

    def test_a_red_record(self):
        self.candidate.write_text(CAND, encoding="utf-8")
        self.rc, self.report = 1, eval_report(failed=("request_success_rate",))
        self.assertEqual(self.gate()[0], 1)
        self.assertEqual(self.refused(), [f"red: the gate judged {CAND} red (request_success_rate: 93% < 100%)"])

    def test_a_missing_or_edited_report(self):
        record = self.gated()
        report = self.kit / record["report"]
        data = json.loads(report.read_text(encoding="utf-8"))
        report.write_text(json.dumps({**data, "failed": []}, indent=2), encoding="utf-8")     # same verdict, new bytes
        self.assertEqual(self.refused(), [f"the report evals/reports/gate-{CAND}.json changed after the gate: its "
                                          "sha256 is not the record's"])
        report.unlink()
        self.assertEqual(self.refused(), [f"the report evals/reports/gate-{CAND}.json is missing, so the record cannot "
                                          "be checked against it"])

    def test_a_record_edited_to_pass(self):
        """A red gate's record with its verdict edited: the report it hashes still says red."""
        self.candidate.write_text(CAND, encoding="utf-8")
        self.rc, self.report = 1, eval_report(failed=("correct_rate",))
        self.gate()
        self.record.write_text(json.dumps({**self.recorded(), "verdict": "pass", "eval_exit": 0, "blocked": []}),
                               encoding="utf-8")
        self.assertEqual(self.refused(), ["the record says pass, and its report does not: correct_rate: 61% < 68%"])

    def test_stale_by_age_and_a_time_in_the_future(self):
        self.gated()
        self.clock += datetime.timedelta(hours=23, minutes=59)
        self.assertEqual(self.check()[0], 0)
        self.clock += datetime.timedelta(minutes=2)
        self.assertEqual(self.refused(), [
            "stale: the gate finished 24.0 hours ago (2026-11-16T10:12:11Z), and a verdict holds for 24: the lane's "
            "documents, rosters and the model's answers may have moved since. make gate again"])
        self.assertEqual(self.check("--max-age-hours", "48")[0], 0)
        self.clock = START - datetime.timedelta(hours=1)                   # stamped by another clock
        self.assertEqual(self.refused(), ["the record's time, 2026-11-16T10:12:11Z, is in the future: it was not "
                                          "written by make gate on this clock"])
        self.clock = START + datetime.timedelta(minutes=8)                 # within the five minutes of skew
        self.assertEqual(self.check()[0], 0)
        self.assertIn("STOP: --max-age-hours must be more than 0", self.check("--max-age-hours", "0")[2])

    def test_stale_by_rules(self):
        self.gated()
        golden = self.kit / "evals" / "golden.jsonl"
        golden.write_bytes(golden.read_bytes() + b'{"id": "lk-99"}\n')    # a row added after the gate
        (self.kit / "evals" / "run_eval.py").write_bytes(b"# thresholds edited\n")
        self.assertEqual(self.refused(), ["stale: evals/run_eval.py, evals/golden.jsonl changed since the gate, which "
                                          "judged by other rules than this checkout's. make gate again"])

    def test_another_lane(self):
        record = self.gated()
        self.record.write_text(json.dumps({**record, "region": "us-central1"}), encoding="utf-8")
        self.assertEqual(self.refused(), [f"another lane: the record is of documind-api in {PROJECT}, us-central1; "
                                          f"this is documind-api in {PROJECT}, {REGION}"])

    def test_the_lane_moved_on(self):
        self.gated()
        self.change(traffic=[{"revisionName": SERVING, "percent": 100}, {"revisionName": NEWER, "tag": "candidate"}])
        self.assertEqual(self.refused(), [f"the candidate tag is on {NEWER}, not on {CAND}: a newer candidate "
                                          "superseded the one the gate judged (make promote refuses this too)"])
        self.set_world(copy.deepcopy(WORLD))
        self.change_revision(CAND, digest=WORLD["revisions"][NEWER]["digest"], ready=False)    # not what was judged
        self.assertEqual(self.refused(), [
            f"{CAND} is not what the gate judged: Cloud Run says {WORLD['revisions'][NEWER]['digest']} with GIT_SHA "
            f"{SHA[CAND]}, the record {WORLD['revisions'][CAND]['digest']} with GIT_SHA {SHA[CAND]}",
            f"{CAND} is not Ready"])
        world = copy.deepcopy(WORLD)
        del world["revisions"][CAND]                                        # deleted since
        self.set_world(world)
        code, out, err = self.check()
        self.assertEqual(code, 2)
        self.assertIn(f"STOP: gcloud run revisions describe failed (exit 1): ERROR: (gcloud.run.revisions.describe) "
                      f"Cannot find revision [{CAND}].", err)

    def test_reasons_add_up_and_the_lane_waits_for_the_files(self):
        record = self.gated()
        self.candidate.write_text(NEWER, encoding="utf-8")
        self.record.write_text(json.dumps({**record, "verdict": "fail", "eval_exit": 1,
                                           "blocked": ["correct_rate: 61% < 68%"]}), encoding="utf-8")
        self.clock += datetime.timedelta(days=3)
        before = len(self.calls())
        reasons = self.refused()
        self.assertEqual([r.split(":")[0] for r in reasons], ["another revision", "red", "stale"])
        self.assertEqual(len(self.calls()), before)                        # the lane is not read until the files agree


class VersionTests(unittest.TestCase):
    """get_version against a local server: the token goes in the header, a 401 names the audience rule (F42), a server
    error is asked twice."""

    def serve(self, *answers):
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append((self.path, self.headers.get("Authorization")))
                status, body = answers[len(seen) - 1]
                data = (body if isinstance(body, str) else json.dumps(body)).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_address[1]}", seen

    def setUp(self):
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        for key in [k for k in os.environ if k.lower().endswith("_proxy")]:
            del os.environ[key]

    def test_the_body_with_the_token(self):
        url, seen = self.serve((200, {"git_sha": "abc1234", "generator_model": "gemini-3.6-flash"}))
        self.assertEqual(release.get_version(url + "/", "tok"),
                         {"git_sha": "abc1234", "generator_model": "gemini-3.6-flash"})
        self.assertEqual(seen, [("/version", "Bearer tok")])

    def test_refusals_and_retries(self):
        url, seen = self.serve((401, "{}"))
        with self.assertRaises(release.Stop) as e:
            release.get_version(url, "tok")
        self.assertIn("answered HTTP 401: the token was refused. Its audience must be the service's canonical URL, "
                      "https://documind-api-NUMBER.REGION.run.app, whichever of its URLs is called (F42)",
                      str(e.exception))
        url, seen = self.serve((403, "{}"))
        with self.assertRaises(release.Stop) as e:
            release.get_version(url, "tok")
        self.assertIn("answered HTTP 403: the token's account may not invoke documind-api", str(e.exception))
        url, seen = self.serve((503, "{}"), (200, {"git_sha": "abc1234"}))
        self.assertEqual(release.get_version(url, "tok"), {"git_sha": "abc1234"})
        self.assertEqual(len(seen), 2)
        url, seen = self.serve((500, "{}"), (500, "{}"))
        with self.assertRaises(release.Stop) as e:
            release.get_version(url, "tok")
        self.assertEqual(str(e.exception), f"GET {url}/version failed twice: HTTP 500")
        url, seen = self.serve((200, "[1, 2]"))
        with self.assertRaises(release.Stop) as e:
            release.get_version(url, "tok")
        self.assertEqual(str(e.exception), f"GET {url}/version did not return a JSON object")


SH = shutil.which("sh")


def make_text() -> str:
    """The Makefile and mk/*.mk as one text, as make reads them (the include comes after the Makefile's own rules)."""
    return (KIT / "Makefile").read_text(encoding="utf-8") + "".join(
        "\n" + p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))


class MiniMake:
    """The make these recipes need, where make is not installed: a target's prerequisites first, then each recipe line
    to `sh -c` as make hands it over (a backslash-newline kept and the next line's tab dropped, `$$` as `$`, `$(NAME)`
    from the variables, the @ and - prefixes taken off); a failing line stops the target unless it began with -;
    `$(MAKE)` runs other targets with the variables it names, as a sub-make inherits the command line's. A variable it
    does not know is a KeyError, so a recipe that starts using more of make fails here first."""

    def __init__(self, cwd: Path, env: dict, variables: dict):
        self.text, self.cwd, self.env, self.vars, self.output = make_text(), cwd, env, variables, []

    def rule(self, target: str) -> tuple:
        m = re.search(rf"^{re.escape(target)}:([^\n=]*)\n", self.text, re.M)
        assert m, f"no rule for {target}"
        lines, current = [], None
        for raw in self.text[m.end():].split("\n"):
            if current is None:
                if not raw.startswith("\t"):
                    break
                current = raw[1:]
            else:
                current += "\n" + (raw[1:] if raw.startswith("\t") else raw)
            if not current.endswith("\\"):
                lines.append(current)
                current = None
        return m.group(1).split(), lines

    @staticmethod
    def expand(line: str, variables: dict) -> str:
        return re.sub(r"\$\$|\$\(([A-Za-z_][A-Za-z0-9_]*)\)",
                      lambda m: "$" if m.group(0) == "$$" else variables[m.group(1)], line)

    def run(self, target: str, overrides: dict | None = None) -> int:
        overrides = dict(overrides or {})
        variables = {**self.vars, **overrides}
        prerequisites, lines = self.rule(target)
        for name in prerequisites:
            code = self.run(name, overrides)
            if code:
                return code
        for line in lines:
            prefix = re.match(r"[@+-]*", line).group(0)
            line, ignore_errors = line[len(prefix):], "-" in prefix
            if line.startswith("$(MAKE)"):
                words = shlex.split(self.expand(line[len("$(MAKE)"):], variables))
                sub = {**overrides, **dict(w.split("=", 1) for w in words if "=" in w)}
                for name in [w for w in words if "=" not in w and not w.startswith("-")]:
                    code = self.run(name, sub)
                    if code:
                        return code
                continue
            r = subprocess.run([SH, "-c", self.expand(line, variables)], cwd=self.cwd, env=self.env,
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            self.output.append(r.stdout + r.stderr)
            if r.returncode and not ignore_errors:
                return r.returncode
        return 0


@unittest.skipUnless(SH, "no POSIX sh to run the recipes in (CI's Linux runner has one; on Windows, Git Bash's)")
class RecipeTests(InProcess):
    """record-candidate, promote-gated, promote and rollback as make runs them, against the stand-in on PATH, in a copy
    of the kit's release files; the gate record comes from an in-process gate on the real clock."""

    def setUp(self):
        super().setUp()
        real_clock = mock.patch.object(release, "now", ORIGINAL_NOW)      # the recipes' gate-check reads the real one
        real_clock.start()
        self.addCleanup(real_clock.stop)
        bin_dir = self.home / "bin"
        bin_dir.mkdir()
        py, fake = Path(sys.executable).as_posix(), (self.home / "fake.py").as_posix()
        for tool in ("gcloud", "curl"):
            path = bin_dir / tool
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(f'#!/bin/sh\nexec "{py}" "{fake}" {tool} "$@"\n')
            path.chmod(0o755)
        if os.name == "nt":                     # what release.py finds through PATHEXT, as it finds gcloud.cmd
            with open(bin_dir / "gcloud.cmd", "w", encoding="utf-8", newline="\r\n") as f:
                f.write(f'@echo off\n"{sys.executable}" "{self.home / "fake.py"}" gcloud %*\nexit /b %errorlevel%\n')
        env = {"PATH": os.pathsep.join([str(bin_dir), str(Path(SH).parent)]), "HOME": str(self.home),
               "USERPROFILE": str(self.home), "APPDATA": str(self.home), "CLOUDSDK_CONFIG": str(self.home / "gcloud"),
               "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
        for key in ("SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR", "TEMP", "TMP", "LANG"):
            if key in os.environ:
                env[key] = os.environ[key]
        default = re.search(r"^GATE_FILE \?= (\S+)$", make_text(), re.M).group(1)
        self.make = MiniMake(self.kit, env, {"PY": shlex.quote(py), "PROJECT": PROJECT, "REGION": REGION,
                                             "GATE_FILE": default})

    def run_target(self, target: str) -> tuple:
        self.make.output = []
        code = self.make.run(target)
        return code, "".join(self.make.output)

    def traffic(self) -> list:
        return self.world()["traffic"]

    def test_the_gated_candidate_is_promoted_and_rolled_back(self):
        code, out = self.run_target("record-candidate")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.candidate.read_text(encoding="utf-8"), CAND + "\n")
        self.assertEqual(self.gate()[0], 0)                                 # make gate's work, in-process
        code, out = self.run_target("promote-gated")
        self.assertEqual(code, 0, out)
        self.assertIn(f"gate record evals/reports/gate.json: {CAND} passed at ", out)
        self.assertIn(f">> serving before the flip: {SERVING} (deploy/.previous-revision - make rollback returns to it)",
                      out)
        self.assertIn(f">> live: {CAND}\n" + json.dumps(self.fake.version(self.world(), AUDIENCE)), out)
        self.assertEqual(self.traffic(), [{"revisionName": CAND, "percent": 100},
                                          {"revisionName": CAND, "tag": "candidate"}])
        self.assertEqual((self.kit / ".previous-revision").read_text(encoding="utf-8"), SERVING + "\n")
        calls = [c["args"][:3] for c in self.calls()]
        first_update = calls.index(["run", "services", "update-traffic"])
        self.assertIn(["run", "revisions", "describe"], calls[:first_update])    # gate-check read the lane first
        self.assertEqual(self.updates(), [["run", "services", "update-traffic", "documind-api", "--region", REGION,
                                           "--project", PROJECT, "--to-revisions", f"{CAND}=100", "--quiet"]])
        code, out = self.run_target("rollback")
        self.assertEqual(code, 0, out)
        self.assertIn(f">> traffic on {SERVING}", out)
        self.assertEqual(self.traffic()[0], {"revisionName": SERVING, "percent": 100})

    def test_any_other_revision_stops_before_promote(self):
        self.assertEqual(self.run_target("record-candidate")[0], 0)
        self.assertEqual(self.gate()[0], 0)
        self.change(latest=NEWER, traffic=[{"revisionName": SERVING, "percent": 100},       # a newer candidate made,
                                           {"revisionName": NEWER, "tag": "candidate"}])    # and recorded here
        self.assertEqual(self.run_target("record-candidate")[0], 0)
        code, out = self.run_target("promote-gated")
        self.assertNotEqual(code, 0)
        self.assertIn(f"REFUSED: the gate record evals/reports/gate.json does not let make promote move traffic:\n"
                      f"  - another revision: the record names {CAND}, and make promote would move traffic to {NEWER}",
                      out)
        self.assertEqual(self.updates(), [])                               # promote never ran
        self.assertFalse((self.kit / ".previous-revision").exists())
        code, out = self.run_target("promote")                             # promote reads no record: as before
        self.assertEqual(code, 0, out)
        self.assertEqual(self.traffic()[0], {"revisionName": NEWER, "percent": 100})

    def test_a_red_record_or_a_moved_tag_stops_before_promote(self):
        self.assertEqual(self.run_target("record-candidate")[0], 0)
        self.rc, self.report = 1, eval_report(failed=("correct_rate",))
        self.assertEqual(self.gate()[0], 1)
        code, out = self.run_target("promote-gated")
        self.assertNotEqual(code, 0)
        self.assertIn(f"  - red: the gate judged {CAND} red (correct_rate: 61% < 68%)", out)
        self.rc, self.report = 0, eval_report()
        self.assertEqual(self.gate()[0], 0)
        self.change(traffic=[{"revisionName": SERVING, "percent": 100}, {"revisionName": NEWER, "tag": "candidate"}])
        code, out = self.run_target("promote-gated")                       # another checkout moved the tag
        self.assertNotEqual(code, 0)
        self.assertIn(f"  - the candidate tag is on {NEWER}, not on {CAND}", out)
        code, out = self.run_target("promote")                             # and promote's own refusal, as before
        self.assertEqual(code, 1, out)
        self.assertIn(f"ERROR: the candidate tag is on {NEWER} but deploy/.candidate-revision names {CAND} - a newer "
                      "candidate superseded this one", out)
        self.assertEqual(self.updates(), [])

    def test_promote_without_a_candidate_file_and_rollback_without_a_previous_one(self):
        code, out = self.run_target("promote")
        self.assertEqual(code, 1)
        self.assertIn("ERROR: deploy/.candidate-revision is missing", out)
        code, out = self.run_target("rollback")
        self.assertEqual(code, 1)
        self.assertIn("ERROR: deploy/.previous-revision is missing", out)
        code, out = self.run_target("promote-gated")
        self.assertNotEqual(code, 0)
        self.assertIn("  - there is no gate record at evals/reports/gate.json", out)
        self.assertEqual(self.updates(), [])


ORIGINAL_NOW = release.now


class WiringTests(unittest.TestCase):
    def read(self, *parts: str) -> str:
        return KIT.joinpath(*parts).read_text(encoding="utf-8")

    def test_the_make_targets(self):
        mk, release_mk, readme = self.read("Makefile"), self.read("mk", "release.mk"), self.read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                       # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        for target in ("gate", "promote-gated"):
            self.assertIn(target, phony)
            self.assertIn(f"`{target}`", readme)
        self.assertRegex(release_mk, r"(?m)^GATE_FILE \?= evals/reports/gate\.json$")
        self.assertIn("evals/reports/", self.read(".gitignore").splitlines())     # the record and its report
        make = MiniMake(KIT, {}, {})
        self.assertEqual(make.rule("gate"), (["guard-project"], [
            "@$(PY) commands/release.py gate --project $(PROJECT) --region $(REGION) --gate-file $(GATE_FILE)"]))
        self.assertEqual(make.rule("promote-gated"), (["guard-project"], [               # the check, then promote
            "@$(PY) commands/release.py gate-check --project $(PROJECT) --region $(REGION) --gate-file $(GATE_FILE)",
            "@$(MAKE) --no-print-directory promote PROJECT=$(PROJECT) REGION=$(REGION)"]))
        self.assertIn("`gate`, and `gate-check` before `promote-gated`'s `make promote`", readme)
        self.assertIn("`release.mk` declares `GATE_FILE`", readme)

    def test_the_files_are_listed(self):
        # An UNOWNED.md row until a lesson page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = self.read("UNOWNED.md"), self.read("INDEX.md")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        for f in ("commands/release.py", "mk/release.mk", "commands/tests/test_release_gate.py"):
            self.assertTrue(f"`{f}`" in unowned or f in quoted, f)


if __name__ == "__main__":
    unittest.main()
