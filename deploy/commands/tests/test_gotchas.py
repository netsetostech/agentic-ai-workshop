"""Offline tests of the production gotchas (workshop lesson 11.7): ops/gotchas.json and commands/gotchas.py, against a
stand-in of Cloud Run and, for one end-to-end run of make gotcha-detect's command, a stub gcloud on a PATH that holds
nothing else. Nothing reaches Google Cloud.

The registry: its schema (gotchas.problems), every id unique, every lesson in course-manifest.json (in the authoring
repository; the learner repository has no manifest, and the test says so), each entry's evidence word for word in the
kit, each alert policy it says pages declared in terraform, each event its log filter reads written by the services,
each drill and check it names run by gotchas.py, and a detector that does not exist refused (the page's Change-it).
The drills: every offline drill prints REPRODUCED with its marker, and CLEARED where the entry shows its lever. The two
Rs 0 drills in detail: the gcloud lines they run, the cap /health reports at each step, the lever clearing the
detector, the chat put back, and put back after a failure in the middle; and a kit that stops doing what a drill
rests on makes that drill exit 1. The deploy reader against the seven deploy scripts and the Makefile; the stand-in's
Cloud Run rules; each detector on stand-in lanes; the live drills' own lines, preconditions and make deploy-services'
argv; the make targets, .PHONY, mk/README.md, UNOWNED.md and the Makefile's 888 lines.
"""
import contextlib
import copy
import importlib.util
import io
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("gotchas", KIT / "commands" / "gotchas.py")
gotchas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gotchas)

REGISTRY = json.loads((KIT / "ops" / "gotchas.json").read_text(encoding="utf-8"))
ENTRIES = {g["id"]: g for g in REGISTRY["gotchas"]}
MANIFEST = KIT.parent / "course-manifest.json"     # the authoring repository's; the learner repository has none
CHAT, API, CAP = gotchas.CHAT, gotchas.API, gotchas.CAP
PROJECT, REGION = "documind-course-demo", "asia-south1"
SERVICES = {"documind-ingest", "documind-api", "documind-admin", "documind-ui", "documind-chat", "documind-mcp",
            "documind-agent"}


def read(*parts: str) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def run_drill(gid: str, lane=None) -> tuple[int, str]:
    out: list[str] = []
    code = gotchas.run_drill(ENTRIES[gid], out.append, lane)
    return code, "\n".join(out)


def chat_lane(project: str = gotchas.PLACEHOLDER, region: str = "us-central1") -> "gotchas.StandIn":
    lane = gotchas.StandIn(project, region)
    gotchas.initial(lane, "pinned-traffic")
    return lane


def full_lane(project: str = gotchas.PLACEHOLDER, region: str = "us-central1") -> "gotchas.StandIn":
    """Every service make deploy-services deploys, as it leaves them."""
    lane = gotchas.StandIn(project, region)
    lane.deploy_services(gotchas.default_scripts(gotchas.makefile()), "c0ffee1")
    return lane


def chat_env(lane) -> dict:
    return gotchas.literal_env(gotchas.template(gotchas.describe(lane, CHAT))["env"])


class FakeLive(gotchas.StandIn):
    """The live drills' flow on a stand-in: offline is False, so a drill takes its lane path (no fork deploy, the
    preconditions asked), while every gcloud line still lands on the stand-in."""

    offline = False

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.asked: list[str] = []

    def require_checkout(self, tag: str) -> None:
        self.asked.append(f"checkout {tag}")

    def require_admin(self) -> None:
        self.asked.append("admin")


class RegistryTests(unittest.TestCase):
    def test_the_schema(self):
        self.assertEqual(gotchas.problems(REGISTRY), [])
        self.assertEqual([g["id"] for g in gotchas.load()], list(ENTRIES))

    def test_about_twelve_unique_entries(self):
        ids = [g["id"] for g in REGISTRY["gotchas"]]
        self.assertTrue(10 <= len(ids) <= 15, len(ids))
        self.assertEqual(len(ids), len(set(ids)))
        for gid in ids:
            self.assertRegex(gid, r"^[a-z][a-z0-9]*(-[a-z0-9]+)+$")

    def test_every_lesson_is_in_the_manifest(self):
        if not MANIFEST.exists():
            self.skipTest("no course-manifest.json beside the kit: the learner repository; the authoring CI checks it")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        known = {lid for module in manifest["modules"].values() for lid in module["lessons"]}
        self.assertIn("11.7", known)                                     # the registry's own lesson
        for g in REGISTRY["gotchas"]:
            self.assertTrue(g["lessons"], g["id"])
            for lid in g["lessons"]:
                self.assertIn(lid, known, f"{g['id']}: lesson {lid} is not in the manifest")

    def test_the_kit_behind_each_entry(self):
        self.assertEqual(gotchas.kit_problems(REGISTRY["gotchas"]), [])
        for g in REGISTRY["gotchas"]:                                    # the same, one pair at a time, readably
            for rel, text in g["evidence"]:
                self.assertIn(text, read(*rel.split("/")), f"{g['id']}: {rel}")

    def test_each_detector_and_drill_exists(self):
        tf = "\n".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "terraform").glob("*.tf")))
        targets = set(re.findall(r"^([a-z][\w-]*):", read("Makefile") + "\n" + "\n".join(
            p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk"))), re.M))
        for g in REGISTRY["gotchas"]:
            det, drill = g["detector"], g["drill"]
            if det["kind"] == "check":
                self.assertIn(g["id"], gotchas.CHECKS)
            else:
                self.assertNotIn(g["id"], gotchas.CHECKS)
                self.assertTrue(det["filter"].startswith('resource.type="cloud_run_revision" AND '), g["id"])
            if det["pages"]:
                self.assertIn(f'display_name = "{det["pages"]}"', tf)
                self.assertEqual(g["signal"], "loud", g["id"])            # a policy that pages is loud
            if g["signal"] == "loud":
                self.assertTrue(g["signal_by"], g["id"])
            self.assertEqual(drill["offline"] is not None, g["id"] in gotchas.DRILLS, g["id"])
            for cmd in (det["run"], (drill["live"] or {}).get("run", "")):
                if cmd.startswith("make "):
                    self.assertIn(cmd.split()[1], targets, f"{g['id']}: {cmd}")
        self.assertEqual(set(gotchas.CHECKS) - set(ENTRIES), set())
        self.assertEqual(set(gotchas.DRILLS) - set(ENTRIES), set())

    def test_the_two_rs0_drills(self):
        self.assertEqual(set(gotchas.LIVE_DRILLS), {"pinned-traffic", "deploy-drops-hotfix"})
        for gid in gotchas.LIVE_DRILLS:
            g = ENTRIES[gid]
            self.assertIsNotNone(g["drill"]["offline"]["cleared"], gid)   # both show their lever offline
            self.assertTrue(g["drill"]["live"]["run"].startswith(f"make gotcha-drill ID={gid} LIVE=1 PROJECT="))
            self.assertTrue(g["drill"]["live"]["cost"].startswith("Rs 0"), gid)
            self.assertTrue(g["cost"].startswith("Rs 0"), gid)
            self.assertIn(CHAT, g["drill"]["live"]["changes"])

    def test_the_registry_is_ascii(self):
        raw = (KIT / "ops" / "gotchas.json").read_bytes()
        self.assertTrue(raw.isascii(), "a Windows console prints ASCII safely; the registry's text stays ASCII")
        self.assertNotIn(b"\r\n", raw)

    def test_a_detector_that_does_not_exist_is_refused(self):
        """The page's Change-it: add an entry whose detector does not exist, and this file fails."""
        data = copy.deepcopy(REGISTRY)
        made = copy.deepcopy(ENTRIES["pinned-traffic"])
        made.update(id="made-up-gotcha", detector={**made["detector"], "run": "make gotcha-detect ID=made-up-gotcha "
                                                   "PROJECT=documind-ai-YOUR-ID REGION=<region>"})
        made["drill"]["live"]["run"] = "make gotcha-drill ID=made-up-gotcha LIVE=1 PROJECT=documind-ai-YOUR-ID"
        data["gotchas"].append(made)
        found = gotchas.problems(data)
        self.assertIn("made-up-gotcha: detector.kind is check, and commands/gotchas.py has no check for this id", found)
        self.assertIn("made-up-gotcha: drill.offline names a drill commands/gotchas.py does not run", found)
        policy = copy.deepcopy(ENTRIES["poison-upload"])
        policy["detector"]["pages"] = "A policy nobody declared"
        self.assertIn("poison-upload: no alert policy in terraform/*.tf is called 'A policy nobody declared'",
                      gotchas.kit_problems([policy]))
        event = copy.deepcopy(ENTRIES["vector-search-fallback"])
        event["detector"]["filter"] = event["detector"]["filter"].replace("vector_search_fallback", "no_such_event")
        self.assertIn("vector-search-fallback: nothing in services/ or shared/ writes the event 'no_such_event' its "
                      "filter reads", gotchas.kit_problems([event]))
        gone = copy.deepcopy(ENTRIES["deploy-drops-hotfix"])
        gone["evidence"] = [["Makefile", "CHAT_EXTRA_ENV=|CHAT_MAX_MODEL_CALLS=8;"]]
        self.assertEqual(gotchas.kit_problems([gone]), ["deploy-drops-hotfix: evidence no longer in the kit: Makefile: "
                                                        "CHAT_EXTRA_ENV=|CHAT_MAX_MODEL_CALLS=8;"])

    def test_each_rule_of_the_schema(self):
        def broken(change) -> list:
            data = copy.deepcopy(REGISTRY)
            change(data["gotchas"][0])
            return gotchas.problems(data)
        self.assertIn("pinned-traffic: symptom is missing or empty", broken(lambda g: g.pop("symptom")))
        self.assertIn("pinned-traffic: unknown field owner", broken(lambda g: g.update(owner="R4")))
        self.assertIn("pinned-traffic: lessons is a list of the workshop's lesson numbers, dotted, each once",
                      broken(lambda g: g.update(lessons=["11-7"])))
        self.assertIn("pinned-traffic: lessons is a list of the workshop's lesson numbers, dotted, each once",
                      broken(lambda g: g.update(lessons=["5.5", "5.5"])))
        self.assertIn("pinned-traffic: signal_by says what pages or goes red, on a loud gotcha and only there",
                      broken(lambda g: g.update(signal="loud")))
        self.assertIn("pinned-traffic: fixed_by names the test that proves the fix, on a fixed gotcha and only there",
                      broken(lambda g: g.update(status="fixed")))
        self.assertIn("pinned-traffic: cost starts with Rs", broken(lambda g: g.update(cost="free")))
        self.assertIn("pinned-traffic: evidence is a list of [kit file, its exact text] pairs",
                      broken(lambda g: g.update(evidence=[["Makefile"]])))
        self.assertIn("pinned-traffic: a drill with a lane form has its offline rehearsal and its live line both",
                      broken(lambda g: g["drill"].update(live=None)))
        self.assertIn("pinned-traffic: detector.run is the make gotcha-detect ID=pinned-traffic line",
                      broken(lambda g: g["detector"].update(run="make limits PROJECT=x")))
        data = copy.deepcopy(REGISTRY)
        data["gotchas"].append(copy.deepcopy(data["gotchas"][0]))
        self.assertIn("pinned-traffic: the id is not unique", gotchas.problems(data))
        self.assertEqual(gotchas.problems([]), ["the registry is an object with a note and a list of gotchas"])


class OfflineDrillTests(unittest.TestCase):
    def test_every_offline_drill_prints_its_marker(self):
        for g in REGISTRY["gotchas"]:
            if not g["drill"]["offline"]:
                continue
            with self.subTest(g["id"]):
                code, out = run_drill(g["id"])
                self.assertEqual(code, 0, out)
                self.assertIn("REPRODUCED: " + g["drill"]["offline"]["marker"], out)
                if g["drill"]["offline"]["cleared"]:
                    self.assertIn("CLEARED: " + g["drill"]["offline"]["cleared"], out)
                self.assertNotIn("NOT ", out)

    def test_pinned_traffic_on_the_stand_in(self):
        lane = chat_lane()
        default = gotchas.chat_cap_default()
        self.assertEqual(default, 12)                                     # services/chat/limits.py's own default
        first = gotchas.serving_revision(gotchas.describe(lane, CHAT))
        code, out = run_drill("pinned-traffic", lane)
        self.assertEqual(code, 0, out)
        where = f"--region=us-central1 --project={gotchas.PLACEHOLDER}"
        changed = [c for c in lane.calls if c.startswith(("gcloud run services update ", "gcloud run services update-traffic "))]
        self.assertEqual(changed, [
            f"gcloud run services update-traffic {CHAT} --to-revisions={first}=100 {where} --quiet",
            f"gcloud run services update {CHAT} --update-env-vars={CAP}=3 {where} --quiet",
            f"gcloud run services update-traffic {CHAT} --to-latest {where} --quiet",
            f"gcloud run services update {CHAT} --remove-env-vars={CAP} {where} --quiet"])
        self.assertIn(f"made with {CAP}=3, takes 0% of the traffic; /health: max_model_calls {default}", out)
        self.assertIn("takes 100% of the traffic; /health: max_model_calls 3", out)
        self.assertIn(f"restored: {CAP} unset, traffic on the latest revision; /health: max_model_calls {default}", out)
        desc = gotchas.describe(lane, CHAT)                                 # the chat as it was: settings and traffic
        self.assertTrue(gotchas.follows_latest(desc))
        self.assertNotIn(CAP, chat_env(lane))
        self.assertEqual(gotchas.pinned_findings(CHAT, desc, lane), [])

    def test_the_detector_agrees_with_limits_drills_check(self):
        """latest_takes_all, limits-drill.sh's own Python, run on the stand-in's describe output."""
        code = re.search(r"latest_takes_all\(\) \{.*?\"\$PY\" -c '(.*?)'\n\}", read("commands", "limits-drill.sh"), re.S)
        self.assertIsNotNone(code, "limits-drill.sh's latest_takes_all changed: change follows_latest() with it")
        lane = chat_lane()
        following = gotchas.describe(lane, CHAT)
        first = gotchas.serving_revision(following)
        lane.gcloud("run", "services", "update-traffic", CHAT, f"--to-revisions={first}=100", *lane.where())
        pinned = gotchas.describe(lane, CHAT)
        for desc, want in ((following, True), (pinned, False)):
            r = subprocess.run([sys.executable, "-c", code.group(1)], input=json.dumps(desc), text=True,
                               capture_output=True)
            self.assertEqual(r.returncode == 0, want, r.stderr)
            self.assertEqual(gotchas.follows_latest(desc), want)

    def test_deploy_drops_hotfix_on_the_stand_in(self):
        lane = chat_lane()
        code, out = run_drill("deploy-drops-hotfix", lane)
        self.assertEqual(code, 0, out)
        self.assertIn(f"detector, before the deploy: {CAP}=8: dropped, not in commands/lesson-12.8.sh's --set-env-vars; "
                      "make deploy-services empties CHAT_EXTRA_ENV, the script's hook for more", out)
        self.assertIn(f"$ make deploy-services SCRIPTS=commands/lesson-12.8.sh PROJECT={gotchas.PLACEHOLDER} "
                      "REGION=us-central1 GIT_SHA=c0ffee1", out)
        self.assertIn(f"{CAP} gone; /health: max_model_calls 12", out)
        self.assertIn("/health: max_model_calls 8; the detector, with that deploy: nothing to drop", out)
        deploys = [c for c in lane.calls if c.startswith("make deploy-services")]
        self.assertEqual([d.split(" (")[0] for d in deploys], ["make deploy-services SCRIPTS=commands/lesson-12.8.sh "
                                                               "GIT_SHA=c0ffee1"] * 4)   # initial, routine, fork, back
        self.assertIn("(CHAT_EXTRA_ENV='|CHAT_MAX_MODEL_CALLS=8' in this fork's recipe)", deploys[2])
        self.assertNotIn(CAP, chat_env(lane))                             # the chat as the kit deploys it
        self.assertEqual(lane.limits(CHAT)["max_model_calls"], 12)
        self.assertEqual(gotchas.deploy_specs()[CHAT].changes(chat_env(lane)), [])

    def test_an_abandoned_call_on_the_chats_own_wrapper(self):
        before, log = sys.modules.get("tools"), logging.getLogger("documind.chat.limits")
        kept = (log.level, log.propagate, list(log.handlers))
        code, out = run_drill("abandoned-call-bills")
        self.assertEqual(code, 0, out)
        self.assertIs(sys.modules.get("tools"), before)                   # the stand-in for tools.py is gone again
        self.assertEqual((log.level, log.propagate, list(log.handlers)), kept)   # and the chat's logger as it was
        self.assertRegex(out, r"a search that takes 4 s, cut at its 1 s budget: the turn moved on after \d+\.\d s, and "
                              r"the model read \{\"error\": "
                              r"\"retrieve did not answer within 1s and was abandoned\", \"timed_out\": true")
        self.assertRegex(out, r"the chat's log: retrieve took \d+\.\d\ds \(budget 1s\)")
        self.assertRegex(out, r"the search ran on to its end, \d+\.\d s, then asked whether it may write into the turn: "
                              r"may_commit\(\) said False")

    def test_a_failure_in_the_middle_puts_the_chat_back(self):
        lane = chat_lane()
        lane.fail_on = "--to-latest"                                      # the lever's line fails, once
        out: list[str] = []
        with self.assertRaises(gotchas.Stop):
            gotchas.run_drill(ENTRIES["pinned-traffic"], out.append, lane)
        self.assertIn("REPRODUCED: " + ENTRIES["pinned-traffic"]["drill"]["offline"]["marker"], out)
        self.assertTrue(gotchas.follows_latest(gotchas.describe(lane, CHAT)))
        self.assertNotIn(CAP, chat_env(lane))
        lane = chat_lane()
        lane.fail_on = "make deploy-services SCRIPTS=commands/lesson-12.8.sh"   # the routine deploy fails, once
        out = []
        with self.assertRaises(gotchas.Stop):
            gotchas.run_drill(ENTRIES["deploy-drops-hotfix"], out.append, lane)
        self.assertTrue(any(line.startswith("restored: ") for line in out), out)
        self.assertNotIn(CAP, chat_env(lane))
        self.assertTrue(gotchas.follows_latest(gotchas.describe(lane, CHAT)))

    def test_a_restore_that_fails_says_what_to_run(self):
        lane = chat_lane()
        out: list[str] = []
        lane.gcloud("run", "services", "update", CHAT, f"--update-env-vars={CAP}=3", *lane.where())
        lane.fail_on = f"--remove-env-vars={CAP}"
        with self.assertRaises(gotchas.Stop):
            gotchas.restore(lane, out.append, None)
        self.assertTrue(out[-1].startswith(f"  by hand: gcloud run services update {CHAT} --remove-env-vars={CAP} "
                                           "--region=us-central1"), out)

    def test_a_kit_that_changed_is_not_reproduced(self):
        script = read("commands", "lesson-12.8.sh")
        merged = script.replace("--set-env-vars=", "--update-env-vars=")
        with mock.patch.object(gotchas, "kit_text", lambda rel: merged if rel == "commands/lesson-12.8.sh"
                               else (KIT / rel).read_text(encoding="utf-8")):
            code, out = run_drill("deploy-drops-hotfix", gotchas.StandIn())
        self.assertEqual(code, 1, out)
        self.assertIn("NOT REPRODUCED: commands/lesson-12.8.sh deploys documind-chat without --set-env-vars", out)
        flipless = read("Makefile").replace('@if echo "$(SCRIPTS)" | grep -q lesson-12.2.sh; then', '@if false; then')
        with mock.patch.object(gotchas, "makefile", lambda: flipless):
            code, out = run_drill("ungated-api-release")
        self.assertEqual(code, 1, out)
        self.assertIn("NOT REPRODUCED: ungated-api-release's drill no longer shows its gotcha", out)
        entry = copy.deepcopy(ENTRIES["rollback-keeps-template"])
        entry["evidence"].append(["Makefile", "rollback: guard-project restore-template"])
        out = []
        self.assertEqual(gotchas.run_drill(entry, out.append), 1)
        self.assertTrue(out[0].startswith("NOT REPRODUCED: the kit no longer says what rollback-keeps-template rests "
                                          "on: Makefile: rollback: guard-project restore-template."), out)


class DeployReaderTests(unittest.TestCase):
    def test_the_cut_is_test_deploy_scripts_own(self):
        tds_spec = importlib.util.spec_from_file_location("_gotchas_tds", KIT / "commands/tests/test_deploy_scripts.py")
        tds = importlib.util.module_from_spec(tds_spec)
        tds_spec.loader.exec_module(tds)
        for script in gotchas.default_scripts(gotchas.makefile()):
            text = read(*script.split("/"))
            self.assertEqual(gotchas.deploy_block(text), tds.deploy_block(text), script)
            self.assertEqual(gotchas.shell_commands(gotchas.deploy_block(text)), tds.commands(tds.deploy_block(text)))

    def test_the_seven_services_and_their_scripts(self):
        specs = gotchas.deploy_specs()
        self.assertEqual(set(specs), SERVICES)
        self.assertEqual(specs[CHAT].script, "commands/lesson-12.8.sh")
        self.assertEqual(specs[API].script, "commands/lesson-12.2.sh")
        self.assertEqual(specs["documind-admin"].spec.split("^")[1], ":")    # lesson-12.3.sh's own delimiter
        lane = gotchas.StandIn().lane_values("c0ffee1")
        for service, s in specs.items():
            written = s.writes(lane=lane)
            self.assertTrue(written, service)
            self.assertFalse([v for v in written.values() if "$" in v or gotchas.LANE in v], service)
            self.assertEqual(s.image_for(lane).rpartition(":")[2], "c0ffee1")
            self.assertTrue(s.image_for(lane).startswith(f"us-central1-docker.pkg.dev/{gotchas.PLACEHOLDER}/documind/"))

    def test_what_make_deploy_services_passes(self):
        passes = gotchas.deploy_passes(gotchas.makefile())
        self.assertEqual(passes["ARMOR"], ("make", "off"))
        self.assertEqual(passes["GENERATOR_MODEL"], ("make", "gemini-3.6-flash"))
        self.assertEqual(passes["ADMIN_EMAILS"], ("make", "admin@documind.example.com"))
        self.assertEqual(passes["SPEND_PCT"], ("make", ""))
        self.assertEqual(passes["RETRIEVAL_BACKEND"], ("recipe", "vector"))
        self.assertEqual(passes["CHAT_EXTRA_ENV"], ("recipe", ""))
        for lane_only in ("PROJECT", "REGION", "GIT_SHA", "PROJECT_NUMBER", "BATCH_JOB_NAME", "VECTOR_INDEX_ENDPOINT",
                          "RETENTION_DAYS", "CHAT_URL"):
            self.assertEqual(passes[lane_only], ("lane", None), lane_only)

    def test_what_the_chat_deploy_writes(self):
        s = gotchas.deploy_specs()[CHAT]
        self.assertEqual(set(s.writes()), {"GOOGLE_CLOUD_PROJECT", "DOCUMIND_PROFILE", "RAG_API_URL", "SELF_URL",
                                           "RAG_TIMEOUT_S", "DOCUMIND_BRAIN", "GOOGLE_GENAI_USE_VERTEXAI",
                                           "GOOGLE_CLOUD_LOCATION", "AUDIT_BUCKET", "IAP_AUDIENCE"})
        self.assertNotIn(CAP, s.writes())
        self.assertEqual(s.hooks, ["CHAT_EXTRA_ENV"])
        self.assertEqual(s.writes({"CHAT_EXTRA_ENV": f"|{CAP}=8"})[CAP], "8")
        self.assertEqual(s.writes()["RAG_TIMEOUT_S"], "90")

    def test_what_the_next_deploy_changes(self):
        lane = full_lane()
        s = gotchas.deploy_specs()[API]
        live = gotchas.literal_env(gotchas.template(gotchas.describe(lane, API))["env"])
        self.assertEqual(s.changes(live), [])                             # as the deploy left it: nothing
        live.update(ARMOR="on", QUERY_REWRITE="on", SPEND_PCT="85", DEMO_MODE="0", RETRIEVAL_BACKEND="rag_engine",
                    GENERATOR_MODEL="projects/NUMBER/locations/us-central1/endpoints/ENDPOINT",
                    SELF_URL="https://elsewhere.example.com")                # derived from the lane: never compared
        lines = {c.name: c.line for c in s.changes(live)}
        self.assertEqual(lines, {
            "ARMOR": "ARMOR=on: written back as ARMOR=off, the default, unless you pass ARMOR=on",
            "QUERY_REWRITE": "QUERY_REWRITE=on: dropped, not in commands/lesson-12.2.sh's --set-env-vars",
            "SPEND_PCT": "SPEND_PCT=85: dropped unless you pass SPEND_PCT=85",
            "DEMO_MODE": "DEMO_MODE=0: written back as DEMO_MODE=1, the default, unless you pass DEMO_MODE=0",
            "RETRIEVAL_BACKEND": "RETRIEVAL_BACKEND=rag_engine: written back as RETRIEVAL_BACKEND=vector; no variable "
                                 "of yours changes that",
            "GENERATOR_MODEL": "GENERATOR_MODEL=projects/NUMBER/locations/us-central1/endpoints/ENDPOINT: written back "
                               "as GENERATOR_MODEL=gemini-3.6-flash, the default, unless you pass "
                               "GENERATOR_MODEL=projects/NUMBER/locations/us-central1/endpoints/ENDPOINT"})
        admin = gotchas.deploy_specs()["documind-admin"]
        live = gotchas.literal_env(gotchas.template(gotchas.describe(lane, "documind-admin"))["env"])
        live["ADMIN_EMAILS"] = "operator@example.com"
        self.assertEqual([c.line for c in admin.changes(live)], [
            "ADMIN_EMAILS=operator@example.com: written back as ADMIN_EMAILS=admin@documind.example.com, the default, "
            "unless you pass ADMIN_EMAILS=operator@example.com"])

    def test_expansion_and_the_dictionary_flag(self):
        env = {"A": "1", "E": "", "L": gotchas.LANE + "L" + gotchas.LANE}
        x = gotchas.expand
        self.assertEqual(x("${A-d}|${U-d}|${E-d}|${E:-d}|${U:-d}", env), "1|d||d|d")
        self.assertEqual(x("${A+w}|${U+w}|${E+w}|${E:+w}|${A:+|B=$A}", env), "w||w||" + "|B=1")
        self.assertEqual(x("$A.$U-x/${A}", env), "1.-x/1")
        self.assertIn(gotchas.LANE, x("https://s-$L.run.app", env))
        with self.assertRaises(gotchas.Changed):
            x("${A#prefix}", env)
        self.assertEqual(gotchas.split_spec("^|^A=1|B=x,y"), [("A", "1"), ("B", "x,y")])
        self.assertEqual(gotchas.split_spec("A=1,B=2"), [("A", "1"), ("B", "2")])
        self.assertEqual(gotchas.split_spec("^:^A=x:B=y=z"), [("A", "x"), ("B", "y=z")])
        with self.assertRaises(gotchas.Changed):
            gotchas.split_spec("^|A=1")

    def test_the_candidate_and_the_cap(self):
        names = gotchas.candidate_names(gotchas.makefile())
        self.assertEqual(names[:3], ["GENERATOR_MODEL", "RAG_MODEL_BASE", "ROUTING"])
        self.assertIn("SEMANTIC_CACHE", names)
        self.assertNotIn("GIT_SHA", names)


class StandInTests(unittest.TestCase):
    """Cloud Run's rules, as the stand-in plays them."""

    def test_update_merges_and_deploy_replaces(self):
        lane = chat_lane()
        before = chat_env(lane)
        lane.gcloud("run", "services", "update", CHAT, "--update-env-vars=^|^X=1|Y=2", *lane.where())
        self.assertEqual(chat_env(lane), {**before, "X": "1", "Y": "2"})
        lane.gcloud("run", "services", "update", CHAT, "--remove-env-vars=X", *lane.where())
        self.assertNotIn("X", chat_env(lane))
        lane.deploy_services(["commands/lesson-12.8.sh"], "c0ffee1")
        self.assertEqual(chat_env(lane), before)                          # --set-env-vars: Y gone
        env = gotchas.template(gotchas.describe(lane, CHAT))["env"]
        self.assertIn({"name": "CHECKPOINT_DSN", "valueFrom": {"secretKeyRef": {"name": "documind-checkpoint-dsn",
                                                                               "key": "latest"}}}, env)

    def test_traffic(self):
        lane = full_lane()
        desc = gotchas.describe(lane, API)
        self.assertFalse(gotchas.follows_latest(desc))                    # deploy-services moved it by name (F44)
        first = gotchas.serving_revision(desc)
        lane.gcloud("run", "services", "update", API, "--no-traffic", "--tag=candidate", "--update-env-vars=A=1",
                    *lane.where())
        desc = gotchas.describe(lane, API)
        cand = gotchas.latest_created(desc)
        self.assertEqual((gotchas.serving_revision(desc), gotchas.tagged(desc, "candidate")), (first, cand))
        lane.gcloud("run", "services", "update", API, "--no-traffic", "--tag=candidate", "--update-env-vars=A=2",
                    *lane.where())
        self.assertNotEqual(gotchas.tagged(gotchas.describe(lane, API), "candidate"), cand)   # a tag moves
        chat = gotchas.describe(lane, CHAT)
        self.assertTrue(gotchas.follows_latest(chat))
        lane.gcloud("run", "services", "update", CHAT, "--no-traffic", "--update-env-vars=A=1", *lane.where())
        chat = gotchas.describe(lane, CHAT)
        self.assertFalse(gotchas.follows_latest(chat))                    # --no-traffic bound what followed the latest
        self.assertEqual(gotchas.percent_of(chat, gotchas.latest_created(chat)), 0)
        lane.gcloud("run", "services", "update-traffic", CHAT, "--to-latest", *lane.where())
        self.assertTrue(gotchas.follows_latest(gotchas.describe(lane, CHAT)))
        lane.gcloud("run", "services", "update-traffic", API, "--remove-tags=candidate", *lane.where())
        self.assertIsNone(gotchas.tagged(gotchas.describe(lane, API), "candidate"))

    def test_refusals(self):
        lane = chat_lane()
        with self.assertRaisesRegex(gotchas.Stop, "answers gcloud run lines for"):
            lane.gcloud("run", "services", "describe", CHAT, "--region=europe-west1", f"--project={lane.project}")
        with self.assertRaisesRegex(gotchas.Stop, "Cannot find service"):
            gotchas.describe(lane, "documind-nothing")
        with self.assertRaisesRegex(gotchas.Stop, "could not be found"):
            gotchas.revision(lane, "documind-chat-09999-abc")
        with self.assertRaisesRegex(gotchas.Stop, "moves 100% of the traffic to one revision"):
            lane.gcloud("run", "services", "update-traffic", CHAT, "--to-revisions=nope=100", *lane.where())
        api = full_lane()
        with self.assertRaisesRegex(gotchas.Refused, "ERROR: deploy/.previous-revision is missing - make promote records"):
            api.make_rollback()
        with self.assertRaisesRegex(gotchas.Refused, "deploy/.candidate-revision is missing"):
            api.make_promote()
        api.make_release_candidate("b2c3d4e")
        older = api.recorded(".candidate-revision")
        api.make_release_candidate("c3d4e5f", files={})                   # another checkout's newer candidate
        with self.assertRaisesRegex(gotchas.Refused, f"the candidate tag is on .* but deploy/.candidate-revision names {older}"):
            api.make_promote()


class DetectorTests(unittest.TestCase):
    def test_a_fresh_lane_is_clear(self):
        lane = full_lane()
        for gid in ("pinned-traffic", "deploy-drops-hotfix", "switch-rides-into-candidate", "rollback-keeps-template"):
            found, lines = gotchas.CHECKS[gid](lane, ENTRIES[gid], 24)
            self.assertIs(found, False, f"{gid}: {lines}")
        found, lines = gotchas.ungated_findings(lane)
        self.assertIsNone(found)                                          # no candidate recorded: it cannot tell
        self.assertIn("cannot tell how that revision reached the traffic", lines[0])

    def test_pinned_and_dropped_on_a_lane(self):
        lane = full_lane()
        first = gotchas.serving_revision(gotchas.describe(lane, CHAT))
        lane.gcloud("run", "services", "update-traffic", CHAT, f"--to-revisions={first}=100", *lane.where())
        lane.gcloud("run", "services", "update", CHAT, f"--update-env-vars={CAP}=3", *lane.where())
        found, lines = gotchas.detect_pinned(lane, ENTRIES["pinned-traffic"], 24)
        self.assertIs(found, True)
        self.assertIn(f"{CHAT}: its traffic is held on {first} 100%, not on the latest revision: every later update "
                      "and deploy lands at 0%", lines)
        self.assertEqual(sum(line.startswith("documind-") and "follows its latest revision" in line for line in lines), 5)
        found, lines = gotchas.detect_drops(lane, ENTRIES["deploy-drops-hotfix"], 24)
        self.assertIs(found, True)
        self.assertIn(f"{CHAT} (commands/lesson-12.8.sh): 1 variable the next make deploy-services would change", lines)
        self.assertEqual(sum("nothing the next make deploy-services would change" in line for line in lines), 6)

    def test_a_hand_update_of_the_api_is_stranded(self):
        lane = full_lane()
        lane.gcloud("run", "services", "update", API, "--update-env-vars=ROUTING=on", *lane.where())
        found, lines = gotchas.detect_pinned(lane, ENTRIES["pinned-traffic"], 24)
        self.assertIs(found, True)
        self.assertTrue(any(line.startswith(f"{API}: its newest revision ") and line.endswith("a change no request "
                                                                                             "reaches") for line in lines))
        found, lines = gotchas.template_findings(lane)
        self.assertIs(found, True)
        self.assertIn("  ROUTING: off on", "\n".join(lines))

    def test_a_revision_holds_the_digest_and_the_template_the_tag(self):
        """Cloud Run writes on each revision the digest its tag named, and keeps the tag on the template: on 22 October
        2026 the two compared as a change on a live lane. The detectors compare the revision the template made."""
        lane = full_lane()
        desc = gotchas.describe(lane, API)
        serves = gotchas.revision_template(gotchas.revision(lane, gotchas.serving_revision(desc)))["image"]
        self.assertTrue(gotchas.template(desc)["image"].endswith("/api:c0ffee1"))
        self.assertRegex(serves, r"/api@sha256:[0-9a-f]{64}$")
        self.assertEqual(gotchas.template_image(lane, desc), serves)

    def test_an_undo_is_no_stranded_change(self):
        """Lessons 2.4's and 2.5's undo: a tagged candidate with a switch, the switch removed, the tag removed. The
        newest revision takes no traffic, carries no tag, and holds the serving revision's settings: nothing to find."""
        lane = full_lane()
        for change in ("--update-env-vars=QUERY_REWRITE=on", "--remove-env-vars=QUERY_REWRITE"):
            lane.gcloud("run", "services", "update", API, "--no-traffic", "--tag=candidate", change, *lane.where())
        lane.gcloud("run", "services", "update-traffic", API, "--remove-tags=candidate", *lane.where())
        found, lines = gotchas.detect_pinned(lane, ENTRIES["pinned-traffic"], 24)
        self.assertIs(found, False, lines)
        self.assertIs(gotchas.template_findings(lane)[0], False)

    def test_the_template_after_a_rollback_and_while_a_candidate_waits(self):
        lane = full_lane()
        lane.make_candidate(GENERATOR_MODEL="gemini-3.6-flsh")
        found, lines = gotchas.template_findings(lane)
        self.assertIs(found, False)                                       # a candidate waiting for the gate
        self.assertIn("is the candidate waiting for the gate", lines[-1])
        lane.make_promote()
        lane.make_rollback()
        found, lines = gotchas.template_findings(lane)
        self.assertIs(found, True)
        self.assertIn("make rollback returned the traffic to", lines[-1])
        lane.files.clear()                                                # a checkout that recorded nothing
        self.assertIsNone(gotchas.template_findings(lane)[0])

    def test_the_previous_revision(self):
        lane = full_lane()
        runner: dict = {}
        lane.make_release_candidate("b2c3d4e", files=runner)
        lane.make_promote(files=runner)
        self.assertIs(gotchas.previous_findings(lane)[0], True)           # a CI promote: nothing recorded here
        lane.make_release_candidate("c3d4e5f")
        lane.make_promote()
        found, lines = gotchas.previous_findings(lane)
        self.assertIs(found, False, lines)                                # this checkout's own promote
        later: dict = {}
        lane.make_release_candidate("d4e5f60", files=later)
        lane.make_promote(files=later)                                    # a later CI promote; this checkout's files stay
        found, lines = gotchas.previous_findings(lane)
        self.assertIs(found, True)
        self.assertIn("from an older release", lines[0])

    def test_the_log_detectors(self):
        lane = full_lane()
        chat = [{"jsonPayload": {"event": "chat", "brain": "langchain", "stopped_by": None, "tool_timeouts": [],
                                 "cost_usd": 0.01}},
                {"jsonPayload": {"event": "chat", "brain": "adk", "stopped_by": "model_calls", "tool_timeouts": ["retrieve"],
                                 "cost_usd": 0.03}},
                {"jsonPayload": {"event": "chat", "brain": "adk", "stopped_by": "model_calls", "tool_timeouts": [],
                                 "cost_usd": 0.03}}]
        api = [{"jsonPayload": {"event": "query", "cost_usd": 0.0108}}]
        lane.log_rows = {'service_name="documind-chat"': chat, 'service_name="documind-api"': api}
        found, lines = gotchas.detect_log(lane, ENTRIES["looping-model-stopped"], 24)
        self.assertIs(found, True)
        self.assertEqual(lines[0], "2 entries in the last 24 h: turns that stopped at a limit, by limit and brain")
        self.assertEqual(lines[1].split(), ["2", "stopped_by=model_calls", "brain=adk"])
        found, lines = gotchas.detect_log(lane, ENTRIES["abandoned-call-bills"], 24)
        self.assertEqual((found, lines[0].split(":")[0]), (True, "1 entry in the last 24 h"))
        found, lines = gotchas.detect_spend(lane, ENTRIES["agent-spend-outside-the-month"], 6)
        self.assertIs(found, True)
        self.assertEqual(lines[0], "3 chat turns in the last 6 h: Rs 5.95 on the agents' own model calls, in no report "
                                   "of the month")
        self.assertEqual(lines[1], "rag-api's 1 row: Rs 0.92, what tenant_daily, make usage and the breaker's counter "
                                   "count")
        reads = [c for c in lane.calls if c.startswith("gcloud logging read")]
        self.assertTrue(all("--freshness=6h" in c or "--freshness=24h" in c for c in reads))
        self.assertIn('(jsonPayload.event="query" OR jsonPayload.event="stream" OR jsonPayload.event="media")', reads[-1])
        lane.log_rows = {}
        found, lines = gotchas.detect_log(lane, ENTRIES["poison-upload"], 24)
        self.assertIs(found, False)
        self.assertEqual(lines[-1], "pages: the alert policy 'Ingest dead-letter queue holds messages' (terraform)")

    def test_the_production_environment(self):
        class Release:
            Stop = RuntimeError

            def __init__(self, level):
                self.level = level

            def lane_inputs(self, tf_dir):
                return {"github_repository": "example-learner/agents-workshop-fork"}

            def production_environment(self, repo):
                return self.level, f"{repo}: {self.level}"
        for level, want in (("warn", True), ("ok", False), ("note", None)):
            with mock.patch.object(gotchas, "_module", lambda path, name, r=Release(level): r):
                found, lines = gotchas.detect_environment(None, ENTRIES["environment-without-reviewers"], 24)
            self.assertIs(found, want)
            self.assertEqual(lines, [f"example-learner/agents-workshop-fork: {level}"])
        with mock.patch.object(gotchas, "_module", lambda path, name: Release("unread")):   # gh ran and could not read
            with self.assertRaisesRegex(gotchas.Stop, "^example-learner/agents-workshop-fork: unread$"):
                gotchas.detect_environment(None, ENTRIES["environment-without-reviewers"], 24)
        broken = Release("ok")
        broken.lane_inputs = mock.Mock(side_effect=RuntimeError("no runbook-project.auto.tfvars.json in terraform"))
        with mock.patch.object(gotchas, "_module", lambda path, name: broken):
            with self.assertRaisesRegex(gotchas.Stop, "no runbook-project.auto.tfvars.json"):
                gotchas.detect_environment(None, ENTRIES["environment-without-reviewers"], 24)

    def test_the_exit_codes(self):
        lane = full_lane()
        out: list[str] = []
        self.assertEqual(gotchas.run_detector(ENTRIES["deploy-drops-hotfix"], lane, 24, out.append), 0)
        self.assertEqual(out[-1], "nothing found")
        lane.gcloud("run", "services", "update", CHAT, f"--update-env-vars={CAP}=3", *lane.where())
        self.assertEqual(gotchas.run_detector(ENTRIES["deploy-drops-hotfix"], lane, 24, out.append), 1)
        self.assertEqual(out[-1], "FOUND: " + ENTRIES["deploy-drops-hotfix"]["title"])
        self.assertEqual(gotchas.run_detector(ENTRIES["ungated-api-release"], lane, 24, out.append), 0)
        self.assertEqual(out[-1], "nothing this checkout can tell")
        lane.gcloud("run", "services", "update", API, "--no-traffic", "--update-env-vars=ROUTING=on", *lane.where())
        lane.services[API]["traffic"] = [{"revisionName": lane.services[API]["order"][0], "percent": 50},
                                         {"latestRevision": True, "percent": 50}]          # a split, by hand
        self.assertEqual(gotchas.run_detector(ENTRIES["ungated-api-release"], lane, 24, out.append), 2)
        self.assertTrue(out[-1].startswith("STOPPED: documind-api's traffic is split"))


class LiveTests(unittest.TestCase):
    def test_the_live_drills_take_the_lane_path(self):
        lane = FakeLive()
        gotchas.initial(lane, "deploy-drops-hotfix")
        out: list[str] = []
        self.assertEqual(gotchas.run_drill(ENTRIES["deploy-drops-hotfix"], out.append, lane), 0)
        self.assertEqual(lane.asked, ["checkout c0ffee1", "admin"])
        self.assertIn("the lever, carrying the value in the deploy, is a change to your fork: the offline drill shows "
                      "it (make gotcha-drill ID=deploy-drops-hotfix)", out)
        self.assertEqual(sum(c.startswith("make deploy-services") for c in lane.calls), 2)   # initial, routine; no fork
        self.assertNotIn("CLEARED: " + ENTRIES["deploy-drops-hotfix"]["drill"]["offline"]["cleared"], out)
        lane = FakeLive()
        gotchas.initial(lane, "pinned-traffic")
        out = []
        self.assertEqual(gotchas.run_drill(ENTRIES["pinned-traffic"], out.append, lane), 0)
        self.assertIn("CLEARED: " + ENTRIES["pinned-traffic"]["drill"]["offline"]["cleared"], out)

    def test_the_live_preconditions(self):
        lane = chat_lane()
        first = gotchas.serving_revision(gotchas.describe(lane, CHAT))
        lane.gcloud("run", "services", "update-traffic", CHAT, f"--to-revisions={first}=100", *lane.where())
        calls = len(lane.calls)
        with self.assertRaisesRegex(gotchas.Stop, "already pinned away from its latest revision"):
            gotchas.drill_pinned(lane, ENTRIES["pinned-traffic"], lambda line: None)
        with self.assertRaisesRegex(gotchas.Stop, "does not follow its latest revision"):
            gotchas.drill_deploy_drop(lane, ENTRIES["deploy-drops-hotfix"], lambda line: None)
        self.assertFalse([c for c in lane.calls[calls:] if " describe " not in c])   # nothing changed
        lane = chat_lane()
        lane.gcloud("run", "services", "update", CHAT, "--update-env-vars=LESSON113_RESTART=1", *lane.where())
        with self.assertRaisesRegex(gotchas.Stop, "LESSON113_RESTART=1: dropped, not in commands/lesson-12.8.sh's"):
            gotchas.drill_deploy_drop(lane, ENTRIES["deploy-drops-hotfix"], lambda line: None)

    def test_the_lanes_own_checks(self):
        with self.assertRaisesRegex(gotchas.Stop, "pass --project"):
            gotchas.Live(gotchas.PLACEHOLDER, REGION)                     # the placeholder is no project id
        live = gotchas.Live(PROJECT, REGION, "")
        with self.assertRaisesRegex(gotchas.Stop, "pass ADMIN_EMAILS=<you>"):
            live.require_admin()
        with self.assertRaisesRegex(gotchas.Stop, "pass ADMIN_EMAILS=<you>"):
            gotchas.Live(PROJECT, REGION, "admin@documind.example.com").require_admin()
        gotchas.Live(PROJECT, REGION, "operator@example.com").require_admin()
        with self.assertRaisesRegex(gotchas.Stop, "the routine deploy rebuilds the image from this checkout"):
            live.require_checkout("0000000")
        git = shutil.which("git")
        head = subprocess.run([git, "rev-parse", "HEAD"], cwd=KIT, capture_output=True, text=True).stdout.strip() if git else ""
        if head:
            live.require_checkout(head[:7])                               # this checkout's own commit passes
        self.assertEqual(live.where(), (f"--region={REGION}", f"--project={PROJECT}"))

    def test_make_deploy_services_argv(self):
        seen = {}

        def fake_run(argv, **kw):
            seen.update(argv=argv, cwd=kw.get("cwd"))
            return subprocess.CompletedProcess(argv, 0)
        live = gotchas.Live(PROJECT, REGION, "operator@example.com")
        with mock.patch.object(gotchas.shutil, "which", lambda tool: f"/usr/bin/{tool}"), \
                mock.patch.object(gotchas.subprocess, "run", fake_run):
            live.deploy_services(["commands/lesson-12.8.sh"], "c0ffee1")
        self.assertEqual(seen["argv"], ["/usr/bin/make", "deploy-services", "SCRIPTS=commands/lesson-12.8.sh",
                                        f"PROJECT={PROJECT}", f"REGION={REGION}", "GIT_SHA=c0ffee1",
                                        "ADMIN_EMAILS=operator@example.com"])
        self.assertEqual(Path(seen["cwd"]), KIT)
        with self.assertRaisesRegex(gotchas.Stop, "a change to your fork"):
            live.deploy_services(["commands/lesson-12.8.sh"], "c0ffee1", extra={"CHAT_EXTRA_ENV": "|A=1"})


class StubGcloudTests(unittest.TestCase):
    """make gotcha-detect's command end to end: a stub gcloud, the only tool on PATH, answers describe from a stand-in
    lane's JSON and records every call."""

    STUB = r'''
import json, os, sys, time
args = sys.argv[1:]
home = os.environ["GOTCHAS_STUB_HOME"]
with open(os.path.join(home, "calls", "%d-%d.json" % (time.time_ns(), os.getpid())), "w", encoding="utf-8") as log:
    json.dump(args, log)
with open(os.path.join(home, "world.json"), encoding="utf-8") as f:
    world = json.load(f)
flags = dict(a[2:].split("=", 1) for a in args if a.startswith("--") and "=" in a)
words = [a for a in args if not a.startswith("--")]
kind = {"services": "services", "revisions": "revisions"}.get(words[1] if len(words) > 1 else "")
if (kind and words[0] == "run" and words[2] == "describe" and flags.get("format") == "json"
        and flags.get("project") == world["project"] and flags.get("region") == world["region"]):
    if words[3] in world[kind]:
        sys.stdout.write(json.dumps(world[kind][words[3]]))
        sys.exit(0)
    sys.stderr.write("ERROR: (gcloud.run.%s.describe) Cannot find [%s]\n" % (kind, words[3]))
    sys.exit(1)
sys.stderr.write("stub: unexpected call: " + " ".join(args) + "\n")
sys.exit(99)
'''

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="gotchas_test_"))
        self.addCleanup(shutil.rmtree, self.home, True)
        (self.home / "calls").mkdir()
        (self.home / "bin").mkdir()
        stub = self.home / "stub.py"
        stub.write_text(self.STUB, encoding="utf-8")
        if os.name == "nt":
            (self.home / "bin" / "gcloud.cmd").write_text(f'@echo off\n"{sys.executable}" "{stub}" %*\nexit /b %errorlevel%\n',
                                                          encoding="utf-8")
        else:
            path = self.home / "bin" / "gcloud"
            path.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(stub))} \"$@\"\n",
                            encoding="utf-8")
            path.chmod(0o755)
        lane = full_lane(PROJECT, REGION)
        first = gotchas.serving_revision(gotchas.describe(lane, CHAT))
        lane.gcloud("run", "services", "update-traffic", CHAT, f"--to-revisions={first}=100", *lane.where())
        lane.gcloud("run", "services", "update", CHAT, f"--update-env-vars={CAP}=3", *lane.where())
        world = {"project": PROJECT, "region": REGION,
                 "services": {name: lane.describe_json(name) for name in lane.services},
                 "revisions": {rev: lane.revision_json(rev) for s in lane.services.values() for rev in s["order"]}}
        (self.home / "world.json").write_text(json.dumps(world), encoding="utf-8")

    def detect(self, *args: str) -> subprocess.CompletedProcess:
        env = {"PATH": str(self.home / "bin"), "GOTCHAS_STUB_HOME": str(self.home), "PYTHONIOENCODING": "utf-8",
               "HOME": str(self.home), "USERPROFILE": str(self.home), "APPDATA": str(self.home),
               "CLOUDSDK_CONFIG": str(self.home / "gcloud")}
        for key in ("SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR", "TEMP", "TMP"):    # what Windows itself needs
            if key in os.environ:
                env[key] = os.environ[key]
        return subprocess.run([sys.executable, str(KIT / "commands" / "gotchas.py"), "detect", *args, "--project",
                               PROJECT, "--region", REGION], cwd=str(self.home), env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=300)

    def test_detect_reads_the_lane_and_finds(self):
        r = self.detect("pinned-traffic")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(f"{CHAT}: its traffic is held on ", r.stdout)
        self.assertIn("FOUND: " + ENTRIES["pinned-traffic"]["title"], r.stdout)
        r = self.detect("deploy-drops-hotfix")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(f"  {CAP}=3: dropped, not in commands/lesson-12.8.sh's --set-env-vars", r.stdout)
        calls = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.home / "calls").glob("*.json"))]
        services = [a for a in calls if a[:3] == ["run", "services", "describe"]]
        revisions = [a for a in calls if a[:3] == ["run", "revisions", "describe"]]
        self.assertEqual((len(services), len(revisions), len(calls)), (14, 2, 16))   # seven services twice; the
        for args in calls:                                # chat's serving and newest revisions once each; describes only
            self.assertIn("--format=json", args)
            self.assertIn(f"--project={PROJECT}", args)
            self.assertIn(f"--region={REGION}", args)

    def test_no_gcloud_is_a_stop(self):
        (self.home / "bin" / ("gcloud.cmd" if os.name == "nt" else "gcloud")).unlink()
        r = self.detect("pinned-traffic")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)          # not one read: no proof of anything
        self.assertIn("STOPPED: gcloud is not on PATH", r.stdout)


class CliTests(unittest.TestCase):
    def main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = gotchas.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_list_and_show(self):
        code, out, _ = self.main("list")
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith(f"{len(ENTRIES)} gotchas in ops/gotchas.json (workshop lesson 11.7)."))
        self.assertEqual([line.split()[0] for line in lines[2:]], list(ENTRIES))
        code, out, _ = self.main("show", "deploy-drops-hotfix")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("deploy-drops-hotfix: A routine make deploy-services drops a setting made by hand\n"))
        self.assertIn("kit        Makefile: CHAT_EXTRA_ENV=; \\", out)
        code, _, err = self.main("show", "no-such-gotcha")
        self.assertEqual(code, 2)
        self.assertIn("STOP: no gotcha 'no-such-gotcha' in ops/gotchas.json", err)

    def test_drill_from_the_command_line(self):
        code, out, _ = self.main("drill", "rollback-keeps-template")
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("== rollback-keeps-template, offline (a stand-in, Rs 0): "))
        code, _, err = self.main("drill", "tag-audience-401")
        self.assertEqual(code, 2)
        self.assertIn("STOP: tag-audience-401 has no offline drill: on a lane it is lesson 11.2's pair", err)
        code, _, err = self.main("drill", "vector-search-fallback", "--live", "--project", PROJECT)
        self.assertEqual(code, 2)
        self.assertIn("STOP: vector-search-fallback has no live drill here: on a lane it is lesson 2.4's drill", err)
        code, _, err = self.main("drill", "--live", "--project", PROJECT)
        self.assertEqual(code, 2)
        self.assertIn("STOP: one live drill at a time", err)
        code, _, err = self.main("drill", "pinned-traffic", "--live", "--project", "")
        self.assertEqual(code, 2)
        self.assertIn("STOP: pass --project", err)

    def test_every_offline_drill_from_the_command_line(self):
        code, out, _ = self.main("drill")
        offline = [g for g in REGISTRY["gotchas"] if g["drill"]["offline"]]
        self.assertEqual(code, 0, out)
        self.assertTrue(out.rstrip().endswith(f"{len(offline)} of {len(offline)} offline drills reproduced their gotcha"))

    def test_detect_needs_a_project(self):
        code, _, err = self.main("detect", "pinned-traffic", "--project", "")
        self.assertEqual(code, 2)
        self.assertIn("STOP: pass --project", err)


class WiringTests(unittest.TestCase):
    def test_the_make_targets(self):
        mk, ops, readme = read("Makefile"), read("mk", "operations.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                       # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        for target in ("gotchas", "gotcha-drill", "gotcha-detect"):
            self.assertIn(target, phony)
            self.assertIn(f"`{target}`", readme)
        self.assertIn("\ngotchas:\n\t@$(PY) commands/gotchas.py $(if $(ID),show $(ID),list)\n", ops)
        self.assertIn("\ngotcha-drill:\n\t@$(PY) commands/gotchas.py drill $(ID) $(if $(LIVE),--live --project "
                      '"$(PROJECT)" --region "$(REGION)" --admin-emails "$(ADMIN_EMAILS)",)\n', ops)
        self.assertIn("\ngotcha-detect: guard-project\n\t@$(PY) commands/gotchas.py detect $(ID) --project $(PROJECT) "
                      "--region $(REGION) $(if $(HOURS),--hours $(HOURS),)\n", ops)
        self.assertIn("| `operations.mk` | `gotchas`, `gotcha-drill`, `gotcha-detect` |", readme)
        self.assertNotIn("--service-account", ops)                        # lesson 0.3 maps those lines to targets
        self.assertFalse(re.search(r"^[A-Z_]+\s*[:?+]?=", ops, re.M), "operations.mk declares no variable")

    def test_the_new_files_are_listed(self):
        # An UNOWNED.md row until lesson 11.7's page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = read("UNOWNED.md"), read("INDEX.md")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        self.assertIn("## Production gotchas (lesson 11.7)", unowned)
        for rel in ("ops/gotchas.json", "commands/gotchas.py", "mk/operations.mk", "commands/tests/test_gotchas.py"):
            self.assertTrue((KIT / rel).exists(), rel)
            self.assertTrue(f"| `{rel}` | **11.7** |" in unowned or rel in quoted, rel)

    def test_the_docstring_names_the_targets(self):
        doc = gotchas.__doc__
        for line in ("make gotchas", "make gotchas ID=<id>", "make gotcha-drill [ID=<id>]",
                     "make gotcha-drill ID=<id> LIVE=1 PROJECT=<id>", "make gotcha-detect [ID=<id>] PROJECT=<id>"):
            self.assertIn(line, doc)


if __name__ == "__main__":
    unittest.main()
