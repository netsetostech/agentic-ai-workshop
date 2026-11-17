"""Offline tests of make capstone-check and make handover (lesson 11.8): commands/capstone_check.py's check, handover
and selftest. Nothing reaches Google Cloud.

The canned fork is commands/tests/capstone_fork/: a made-up company's capstone (Sahyadri Freight), its four documents,
its corpus in a tenant of its own, its golden rows (golden.jsonl.add, appended to the kit's golden.jsonl), and the
records lesson 11.3's controlled failure leaves (make smoke-deployed's four runs, the repair's gate report and record).
Each test lays it over a copy of the kit files the check reads, in a temporary directory, and changes that copy. The
lane is a stand-in, in-process at the two seams every read goes through: release.run, which runs gcloud, and
http_json, which makes the GETs.

Covered: the canned fork passes every component offline; the lesson's Change-it, one FAILURE-MODES command deleted,
fails component 7 and nothing else; each component broken alone fails that component alone; the kit as it ships passes
the eval suite and nothing else; with the lane, every component's reads (all PASS, then the outsider answered, IAP
off, the member on no roster, a document not indexed, the lane's services gone, the rollback another lane's, another
lane's records, documind-api not deployed), and nothing asked but READS and the two tokens, a write refused before it
runs; handover offline and with the lane, a failed read listed under Not read with exit 1, --out, the file whole and
LF; the command line's exits; the selftest; the page counts of the kit's real PDFs against evals/real_sources.json;
and the wiring: the targets, .PHONY, the Makefile's 888 lines, FORK never declared, mk/README.md, UNOWNED.md, and the
kit facts the check reads.
"""
import contextlib
import copy
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1]
CANNED = HERE / "capstone_fork"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cc = load("capstone_check_under_test", KIT / "commands" / "capstone_check.py")
PROJECT, NUMBER, REGION, SLM_REGION = "documind-course-demo", "123456789012", "asia-south1", "us-central1"
OLD, GOOD, BAD, FIX = "documind-api-00040-abc", "documind-api-00041-kel", "documind-api-00042-typ", "documind-api-00043-fix"
TENANT, API = "sahyadri", f"https://documind-api-{NUMBER}.{REGION}.run.app"
REPO, REPO_ID = "example-learner/agents-workshop-fork", "987654321"
# The kit files the check and the handover read: every fork starts as these, and capstone_fork/ goes over them.
KIT_FILES = ("Makefile", "commands/lesson-12.4.sh", "commands/incident-drill.sh", "ops/gotchas.json", "ops/runbooks.json",
             "evals/run_eval.py", "evals/golden.jsonl", "evals/required.json", "evals/manifest.json")
KIT_GLOBS = ("mk/*.mk", "terraform/*.tf", "evals/demo/*.md", "evals/demo/*.txt", "evals/corpus/*/*.md",
             "evals/corpus/*/*.txt")
TOKENS = {"documind-ui-sa": "tok-member", "documind-outsider-sa": "tok-outsider"}
BASE = {}


def kit_copy(dest: Path) -> Path:
    for rel in [*KIT_FILES, *(p.relative_to(KIT).as_posix() for g in KIT_GLOBS for p in sorted(KIT.glob(g)))]:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(KIT / rel, dest / rel)
    return dest


def assemble(dest: Path) -> Path:
    """The canned fork in dest: the kit's files, then capstone_fork/'s over them; a file whose name ends in .add is
    appended to the one of its name without it. The records name the lane's URLs with the course's placeholder,
    documind-api-NUMBER (the publish refuses a project number in a run.app URL): the stand-in's number goes in here."""
    kit_copy(dest)
    for path in sorted(CANNED.rglob("*")):
        if path.is_file():
            target = dest / path.relative_to(CANNED)
            target.parent.mkdir(parents=True, exist_ok=True)
            data = path.read_bytes().replace(b"documind-api-NUMBER.", f"documind-api-{NUMBER}.".encode())
            with open(target.with_suffix("") if path.suffix == ".add" else target, "ab" if path.suffix == ".add" else
                      "wb") as f:
                f.write(data)
    return dest


def setUpModule():
    BASE["dir"] = Path(tempfile.mkdtemp(prefix="capstone_base_"))
    assemble(BASE["dir"] / "fork")


def tearDownModule():
    shutil.rmtree(BASE["dir"], ignore_errors=True)


def run_main(*argv: str) -> tuple:
    """capstone_check.py's command line, in-process: (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cc.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def verdicts(out: str) -> dict:
    return {int(n): v for n, v in re.findall(r"(?m)^   (\d)  (PASS|FAIL)  ", out)}


def edit(path: Path, old: str, new: str = "") -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, (path, old)
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


def runs_of(fork: Path) -> list:
    return [json.loads(line) for line in (fork / cc.SMOKE_LOG).read_text(encoding="utf-8").splitlines()]


def save_runs(fork: Path, runs: list) -> None:
    (fork / cc.SMOKE_LOG).write_text("".join(json.dumps(r) + "\n" for r in runs), encoding="utf-8", newline="\n")


class ForkCase(unittest.TestCase):
    """A fresh copy of the canned fork for each test, with no token in the environment."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="capstone_test_"))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.fork = self.home / "fork"
        shutil.copytree(BASE["dir"] / "fork", self.fork)
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        for key in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "PROJECT", "REGION", "SLM_REGION"):
            os.environ.pop(key, None)

    def check(self, *extra: str) -> tuple:
        code, out, err = run_main("check", "--fork", str(self.fork), *extra)
        return code, verdicts(out), out + err

    def without_make_eval(self):
        """For a test about another component: make eval's own run, a few seconds each, said to pass."""
        patcher = mock.patch.object(cc, "run_eval_offline", lambda fork: (0, ""))
        patcher.start()
        self.addCleanup(patcher.stop)


# ---------------------------------------------------------------- the fork alone

def break_1(fork: Path):            # the UI deployed without IAP
    edit(fork / cc.UI_SCRIPT, "--no-allow-unauthenticated --iap", "--no-allow-unauthenticated")


def break_2(fork: Path):            # the manual's pages run together: 1 page and the handbook's 8
    path = fork / "evals" / "corpus" / TENANT / "fleet_safety_manual_2026.md"
    path.write_text(path.read_text(encoding="utf-8").replace("\f", "\n"), encoding="utf-8", newline="\n")


def break_3(fork: Path):            # four isolation rows left
    path, kept, seen = fork / "evals" / "golden.jsonl", [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        seen += json.loads(line)["shape"] == "isolation"
        if json.loads(line)["shape"] != "isolation" or seen <= 4:
            kept.append(line)
    path.write_text("\n".join(kept) + "\n", encoding="utf-8", newline="\n")


def break_4(fork: Path):            # the last smoke run passed no lane's smoke
    runs = runs_of(fork)
    runs[-1]["ran"].update({"smoke-chat": 1, "smoke-media": 1})
    save_runs(fork, runs)


def break_5(fork: Path):            # two rejected options left
    edit(fork / "ARCHITECTURE.md", "- A second vector database (Pinecone): it would hold tenant text outside asia-south1, "
                                   "which our customers' contracts\n  forbid.\n")


def break_6(fork: Path):            # no date
    edit(fork / "COST-MODEL.md", "Dated 2026-11-18, at", "At")


def break_7(fork: Path):            # the lesson's Change-it: one FAILURE-MODES command deleted
    edit(fork / "FAILURE-MODES.md", "Command: `make gotcha-drill ID=pinned-traffic`\n")


def break_8(fork: Path):            # the runs around the rollback gone: a promote is no rollback
    runs = runs_of(fork)
    save_runs(fork, [runs[0], runs[-1]])


BREAKS = {1: (break_1, "deploys documind-ui without --iap"), 2: (break_2, "9 pages as the ingest worker counts them"),
          3: (break_3, "4 of them isolation rows"), 4: (break_4, "passed no lane's smoke"),
          5: (break_5, "names 2 rejected options with a reason"), 6: (break_6, "carries no date"),
          7: (break_7, '"Pinned traffic hides a change": no command in backticks'),
          8: (break_8, "no two successive make smoke-deployed runs show a rollback")}


class ForkTests(ForkCase):
    def test_the_canned_fork_passes_every_component(self):
        code, found, out = self.check()
        self.assertEqual((code, found), (0, {n: "PASS" for n in range(1, 9)}), out)
        for line in ("the fork deploys documind-ui behind IAP: --iap and --no-allow-unauthenticated",
                     "a member was answered: GET /version said git_sha abc1234, gemini-3.6-flash, documind-rag@v3",
                     "every isolation row (11) answered 403 to the outsider "
                     "(evals/reports/gate-documind-api-00043-fix.json)",
                     "sahyadri's corpus: 2 documents, 32 pages as the ingest worker counts them",
                     "a query cites one: sh-01 cited fleet_safety_manual_2026.md and passed",
                     "67 golden rows, 11 of them isolation rows", "make eval: evals/run_eval.py offline exits 0",
                     "chat: make smoke-chat passed", "media: make smoke-media passed",
                     "names 3 rejected options with a reason: GKE Autopilot for the API; A second vector database "
                     "(Pinecone); Fine-tuning before prompting", "dual-priced", "dated 2026-11-18",
                     "4 entries proved by a command the fork runs", '"A poison upload pages an hour later": make poison',
                     "a recorded rollback, the traffic left the revision the candidate tag names: "
                     "documind-api-00042-typ -> documind-api-00041-kel", "/version before: git_sha abc1234, "
                     "gemini-3.6-flsh", "complete: every one of the eight components PASSes"):
            self.assertIn(line, " ".join(out.split()), line)

    def test_an_exported_project_is_not_the_lane(self):
        """Every lesson's shell exports PROJECT, REGION and SLM_REGION: on 22 October 2026 that made this fork's
        offline check read the lane. Without --project it stays offline, and passes as above."""
        self.without_make_eval()
        os.environ.update(PROJECT="documind-ai-YOUR-ID", REGION="us-central1", SLM_REGION="us-central1")
        code, found, out = self.check()
        self.assertTrue(out.startswith(f">> capstone-check: the fork at {self.fork}, offline: "), out[:200])
        self.assertEqual((code, found), (0, {n: "PASS" for n in range(1, 9)}), out)

    def test_change_it_one_failure_modes_command_deleted_fails_that_component_only(self):
        break_7(self.fork)
        code, found, out = self.check()
        self.assertEqual((code, found), (1, {n: "FAIL" if n == 7 else "PASS" for n in range(1, 9)}), out)
        flat = " ".join(out.split())
        self.assertIn("3 entries proved, 4 or more", flat)
        self.assertIn('"Pinned traffic hides a change": no command in backticks', flat)
        self.assertIn("incomplete: component 7 FAILs", flat)

    def test_each_component_broken_alone_fails_alone(self):
        for n, (breaker, says) in BREAKS.items():
            with self.subTest(component=n):
                fork = self.home / f"broken-{n}"
                shutil.copytree(BASE["dir"] / "fork", fork)
                breaker(fork)
                code, out, err = run_main("check", "--fork", str(fork))
                self.assertEqual((code, verdicts(out)), (1, {k: "FAIL" if k == n else "PASS" for k in range(1, 9)}),
                                 out + err)
                self.assertIn(says, " ".join(out.split()))

    def test_a_command_the_fork_cannot_run_names_why(self):
        self.without_make_eval()
        edit(self.fork / "FAILURE-MODES.md", "make gotcha-drill ID=pinned-traffic", "make gotcha-detect ID=pinned-traffic")
        edit(self.fork / "FAILURE-MODES.md", "bash commands/incident-drill.sh", "bash commands/hold-fault.sh")
        code, found, out = self.check()
        self.assertEqual((code, found[7]), (1, "FAIL"))
        flat = " ".join(out.split())
        self.assertIn("make gotcha-detect detects a gotcha, it does not reproduce one", flat)
        self.assertIn("the fork holds no commands/hold-fault.sh", flat)
        self.assertIn("2 entries proved", flat)

    def test_the_kit_as_it_ships_is_no_capstone(self):
        kit = kit_copy(self.home / "kit")
        code, out, _ = run_main("check", "--fork", str(kit))
        self.assertEqual((code, verdicts(out)), (1, {n: "PASS" if n == 3 else "FAIL" for n in range(1, 9)}), out)
        flat = " ".join(out.split())
        self.assertIn("evals/corpus/ holds no tenant of your own, only the kit's (acme, globex, zeta)", flat)
        self.assertIn("ARCHITECTURE.md is missing from the fork's root", flat)
        self.assertIn("no make smoke-deployed run in evals/reports/smoke-deployed.jsonl", flat)

    def test_the_newest_report_that_asked_decides(self):
        self.without_make_eval()
        report = json.loads((self.fork / cc.REPORTS / f"gate-{FIX}.json").read_text(encoding="utf-8"))
        leaked = dict(report, scores=dict(report["scores"], isolation_403_rate=10 / 11),
                      isolation=["iso-03: a non-member asking zeta got 200, expected 403"])
        newer = self.fork / cc.REPORTS / "eval-live.json"
        newer.write_text(json.dumps(leaked), encoding="utf-8")
        later = (self.fork / cc.REPORTS / f"gate-{FIX}.json").stat().st_mtime + 60
        os.utime(newer, (later, later))
        code, found, out = self.check()
        self.assertEqual((code, found[1], found[2]), (1, "FAIL", "PASS"), out)
        self.assertIn("isolation_403_rate 91%; iso-03: a non-member asking zeta got 200", " ".join(out.split()))
        scoped = dict(leaked, judged=[k for k in leaked["judged"] if k != "isolation_403_rate"], source="x")
        newer.write_text(json.dumps(scoped), encoding="utf-8")       # asked no isolation row: the older report decides
        os.utime(newer, (later, later))
        self.assertEqual(self.check()[1][1], "PASS")


# ---------------------------------------------------------------- the lane, a stand-in

def service(name: str, floor: str = "0", iap: bool = False) -> dict:
    notes = {"autoscaling.knative.dev/minScale": floor, "autoscaling.knative.dev/maxScale": "10"}
    return {"metadata": {"name": name, "annotations": {"run.googleapis.com/iap-enabled": "true"} if iap else {}},
            "spec": {"template": {"metadata": {"annotations": notes}}}}


def revision(name: str, model: str = "gemini-3.6-flash") -> dict:
    return {"metadata": {"name": name, "creationTimestamp": "2026-11-17T09:00:00Z"},
            "spec": {"containers": [{"image": f"{REGION}-docker.pkg.dev/{PROJECT}/documind/api:abc1234",
                                     "env": [{"name": "GIT_SHA", "value": "abc1234"},
                                             {"name": "GENERATOR_MODEL", "value": model}]}]}}


POLICIES = [{"displayName": "API p95 latency > 3s", "enabled": True, "notificationChannels": ["projects/p/n/1"]},
            {"displayName": "Ingest failed", "enabled": True, "notificationChannels": []},
            {"displayName": "A policy made by hand", "enabled": False}]
WORLD = {
    "project": PROJECT, "number": NUMBER,
    "services": {REGION: [service("documind-api"), service("documind-ui", "1", iap=True), service("documind-chat"),
                          service("documind-mcp"), service("documind-ingest"), service("documind-admin"),
                          service("documind-agent")],
                 SLM_REGION: []},
    "revisions": [revision(OLD), revision(GOOD), revision(BAD, "gemini-3.6-flsh"), revision(FIX)],
    "traffic": [{"revisionName": FIX, "percent": 100}, {"revisionName": FIX, "tag": "candidate"}],
    "version": {"model_backend": "vertex", "generator_model": "gemini-3.6-flash", "prompt": "documind-rag@v3",
                "retrieval_graph": "off", "git_sha": "abc1234"},
    "sources": {"tok-member": (200, {"tenant_id": TENANT, "sources": [
        {"name": f"{TENANT}/fleet_safety_manual_2026.md", "status": "indexed"},
        {"name": f"{TENANT}/driver_handbook_2026.md", "status": "indexed"}]}), "tok-outsider": (403, None)},
    "scheduler": {"state": "ENABLED", "schedule": "0 23 * * *", "timeZone": "Asia/Kolkata",
                  "lastAttemptTime": "2026-11-17T17:30:00.512Z", "status": {}},
    "condition": (f"assertion.repository_id == '{REPO_ID}' && assertion.repository == '{REPO}' && "
                  "assertion.ref == 'refs/heads/main'"),
    "billing": {"billingAccountName": "billingAccounts/ABCDEF-123456-A1B2C3", "billingEnabled": True},
    "budgets": [{"displayName": "DocuMind monthly budget",
                 "amount": {"specifiedAmount": {"currencyCode": "INR", "units": "5000"}},
                 "thresholdRules": [{"thresholdPercent": 0.5}, {"thresholdPercent": 0.8}, {"thresholdPercent": 1.0},
                                    {"thresholdPercent": 1.2, "spendBasis": "FORECASTED_SPEND"}]}],
    "bucket": {"location": "ASIA-SOUTH1", "versioning_enabled": True, "public_access_prevention": "enforced",
               "uniform_bucket_level_access": True, "soft_delete_policy": {"retentionDurationSeconds": "604800"}},
    "object": {"size": 482113, "update_time": "2026-11-17T08:00:00+0000"},
    "policies": POLICIES,
    "fail": {},                     # a read's first words -> the error gcloud prints
}


class Lane:
    """The stand-in lane: release.run's place (gcloud, recording every call) and http_json's (the GETs)."""

    def __init__(self, world: dict):
        self.world, self.calls, self.gets = world, [], []

    def done(self, out=None, code=0, err=""):
        return subprocess.CompletedProcess([], code, out if isinstance(out, str) or out is None else json.dumps(out),
                                           err)

    def run(self, argv, cwd=None):
        self.calls.append(list(argv))
        w, args = self.world, list(argv[1:])
        flags = dict(a[2:].split("=", 1) for a in args if a.startswith("--") and "=" in a)
        words = [a for a in args if not a.startswith("-")]
        for start, error in w["fail"].items():
            if " ".join(words).startswith(start):
                return self.done(None, 1, error)
        if words[:2] == ["projects", "describe"]:
            return self.done({"projectId": w["project"], "projectNumber": w["number"]} if words[2] == w["project"] else
                             None, 0 if words[2] == w["project"] else 1, f"ERROR: NOT_FOUND: {words[2]}")
        if flags.get("project") not in (None, w["project"]):
            return self.done(None, 1, "ERROR: (gcloud) PERMISSION_DENIED: another project")
        if words[:3] == ["run", "services", "list"]:
            return self.done(w["services"].get(flags["region"], []))
        if words[:3] == ["run", "services", "describe"]:
            found = next((s for s in w["services"][REGION] if s["metadata"]["name"] == words[3]), None)
            if found is None:
                return self.done(None, 1, f"ERROR: (gcloud.run.services.describe) Cannot find service [{words[3]}]")
            found = copy.deepcopy(found)
            if words[3] == "documind-api":
                found["status"] = {"traffic": w["traffic"]}
            return self.done(found)
        if words[:3] == ["run", "revisions", "list"]:
            return self.done(w["revisions"])
        if words[:2] == ["auth", "print-identity-token"]:
            account = flags["impersonate-service-account"].split("@", 1)[0]
            assert flags["audiences"] == f"https://documind-api-{w['number']}.{REGION}.run.app", flags
            return self.done(TOKENS[account] + "\n")
        if words[:2] == ["auth", "print-access-token"]:
            return self.done("tok-access\n")
        if words[:3] == ["scheduler", "jobs", "describe"]:
            return self.done(w["scheduler"])
        if words[:4] == ["iam", "workload-identity-pools", "providers", "describe"]:
            return self.done({"name": "providers/github-oidc", "attributeCondition": w["condition"]})
        if words[:3] == ["billing", "projects", "describe"]:
            return self.done(w["billing"])
        if words[:3] == ["billing", "budgets", "list"]:
            return self.done(w["budgets"])
        if words[:3] == ["storage", "buckets", "describe"]:
            return self.done(w["bucket"])
        if words[:3] == ["storage", "objects", "describe"]:
            return self.done(w["object"])
        return self.done(None, 99, "stand-in: unexpected call " + " ".join(argv))

    def http(self, url, token):
        self.gets.append((url, token))
        w = self.world
        if url == f"https://documind-api-{w['number']}.{REGION}.run.app/version" and token == "tok-member":
            return 200, w["version"], ""
        if url.startswith(f"https://documind-api-{w['number']}.{REGION}.run.app/v1/sources?tenant_id="):
            status, body = w["sources"][token]
            return status, body, "" if status == 200 else f"HTTP {status}"
        if url.startswith(f"https://monitoring.googleapis.com/v3/projects/{w['project']}/alertPolicies") and \
                token == "tok-access":
            return 200, {"alertPolicies": w["policies"]}, ""
        return 404, None, "HTTP 404"


class LaneCase(ForkCase):
    def setUp(self):
        super().setUp()
        self.world = copy.deepcopy(WORLD)
        self.lane = Lane(self.world)
        self.without_make_eval()
        for target, name, value in ((cc.release, "run", self.lane.run), (cc, "http_json", self.lane.http)):
            patcher = mock.patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def live(self, *extra: str) -> tuple:
        return self.check("--project", PROJECT, "--region", REGION, *extra)


class LaneTests(LaneCase):
    def test_every_component_passes_with_the_lanes_reads(self):
        code, found, out = self.live()
        self.assertEqual((code, found), (0, {n: "PASS" for n in range(1, 9)}), out)
        flat = " ".join(out.split())
        for line in (f"and the lane {PROJECT} in {REGION}, read only",
                     "lane: GET /version as documind-ui-sa: 200, git_sha abc1234",
                     f"lane: GET /v1/sources?tenant_id={TENANT} as documind-outsider-sa, on no roster: 403",
                     "lane: documind-ui has IAP on", f"lane: GET /v1/sources?tenant_id={TENANT}, the Documents page's "
                     "read, lists all 2 documents indexed", "lane: chat's services are deployed: documind-chat",
                     "lane: media's services are deployed: documind-api, documind-mcp",
                     f"lane: both are documind-api revisions on {PROJECT}"):
            self.assertIn(line, flat)

    def test_only_reads_are_asked(self):
        self.live()
        self.assertTrue(self.lane.calls)
        for argv in self.lane.calls:
            self.assertTrue(cc.is_read(argv) or argv[:3] == ["gcloud", "auth", "print-identity-token"], argv)
        self.assertEqual({token for _, token in self.lane.gets}, {"tok-member", "tok-outsider"})
        self.assertTrue(all(url.startswith(API) for url, _ in self.lane.gets))

    def test_a_write_is_refused_before_it_runs(self):
        for argv in (["gcloud", "run", "services", "update", "documind-api", "--min-instances=0"],
                     ["gcloud", "run", "services", "update-traffic", "documind-api", "--to-latest"],
                     ["gcloud", "scheduler", "jobs", "pause", "documind-off-nightly"], ["make", "rollback"]):
            with self.assertRaises(cc.Stop):
                cc.gcloud_json(argv)
        self.assertEqual(self.lane.calls, [])

    def test_the_outsider_answered(self):
        self.world["sources"]["tok-outsider"] = (200, {"sources": []})
        code, found, out = self.live()
        self.assertEqual((code, found[1]), (1, "FAIL"))
        self.assertIn("on no roster, answered HTTP 200, not 403: the roster no longer decides", " ".join(out.split()))

    def test_iap_off(self):
        self.world["services"][REGION][1] = service("documind-ui", "1")
        code, found, out = self.live()
        self.assertEqual((code, found[1]), (1, "FAIL"))
        self.assertIn("lane: documind-ui does not have IAP on", " ".join(out.split()))

    def test_the_member_on_no_roster_of_the_tenants(self):
        self.world["sources"]["tok-member"] = (403, None)
        code, found, out = self.live()
        self.assertEqual((code, found[2]), (1, "FAIL"))
        self.assertIn(f"make roster TENANT={TENANT} MEMBERS=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com",
                      " ".join(out.split()))

    def test_a_document_not_indexed(self):
        self.world["sources"]["tok-member"][1]["sources"][1]["status"] = "withdrawn"
        code, found, out = self.live()
        self.assertEqual((code, {n: v for n, v in found.items() if v == "FAIL"}), (1, {2: "FAIL"}), out)
        self.assertIn("does not list these as indexed: driver_handbook_2026.md", " ".join(out.split()))

    def test_the_lanes_services_gone(self):
        self.world["services"][REGION] = [s for s in self.world["services"][REGION]
                                          if s["metadata"]["name"] not in ("documind-chat", "documind-mcp")]
        code, found, out = self.live()
        self.assertEqual((code, {n: v for n, v in found.items() if v == "FAIL"}), (1, {4: "FAIL"}), out)
        self.assertIn("lane: none of those lanes is deployed now", " ".join(out.split()))

    def test_the_rollback_is_another_lanes(self):
        self.world["revisions"] = [revision(GOOD), revision(FIX)]
        code, found, out = self.live()
        self.assertEqual((code, {n: v for n, v in found.items() if v == "FAIL"}), (1, {8: "FAIL"}), out)
        self.assertIn("documind-api has no documind-api-00042-typ: the recorded rollback is another lane's",
                      " ".join(out.split()))

    def test_another_lanes_records_do_not_count(self):
        self.world.update(project="documind-other-lane", number="210987654321")
        code, out, err = run_main("check", "--fork", str(self.fork), "--project", "documind-other-lane", "--region",
                                  REGION)
        self.assertEqual({n: v for n, v in verdicts(out).items() if v == "FAIL"},
                         {1: "FAIL", 2: "FAIL", 4: "FAIL", 8: "FAIL"}, out + err)
        self.assertIn("no make smoke-deployed run of documind-other-lane in asia-south1", " ".join(out.split()))

    def test_no_documind_api_in_region_stops(self):
        self.world["services"][REGION] = self.world["services"][REGION][1:]
        code, found, out = self.live()
        self.assertEqual((code, found), (2, {}))
        self.assertIn(f"STOP: documind-api is not deployed in {REGION} ({PROJECT})", out)

    def test_refusals_before_any_read(self):
        for extra, says in ((("--project", "Not_A_Project", "--region", REGION), "pass --project"),
                            (("--project", PROJECT, "--region", "nowhere"), "pass --region")):
            code, out, err = run_main("check", "--fork", str(self.fork), *extra)
            self.assertEqual(code, 2)
            self.assertIn(says, err)
        self.assertEqual(self.lane.calls, [])


# ---------------------------------------------------------------- the handover

class HandoverTests(LaneCase):
    def handover(self, *extra: str) -> tuple:
        code, out, err = run_main("handover", "--fork", str(self.fork), *extra)
        path = self.fork / "HANDOVER.md"
        return code, out + err, path.read_text(encoding="utf-8") if path.is_file() else ""

    def lane_files(self):
        (self.fork / ".candidate-revision").write_text(FIX + "\n", encoding="utf-8")
        (self.fork / ".previous-revision").write_text(GOOD + "\n", encoding="utf-8")
        inputs = {"project_id": PROJECT, "region": REGION, "billing_account_id": "ABCDEF-123456-A1B2C3",
                  "github_repository": REPO, "github_repository_id": REPO_ID, "deploy_ref": "refs/heads/main"}
        (self.fork / "terraform" / cc.release.infra.INPUT_FILE).write_text(json.dumps(inputs), encoding="utf-8")
        state = self.fork / "terraform" / ".terraform" / "terraform.tfstate"
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({"version": 3, "backend": {"type": "gcs", "config": {
            "bucket": f"{PROJECT}-tfstate", "prefix": f"documind/{PROJECT}"}}}), encoding="utf-8")

    def test_offline_writes_the_checkouts_half(self):
        code, out, text = self.handover()
        self.assertEqual(code, 0, out)
        self.assertIn(f">> handover: {self.fork / 'HANDOVER.md'}, from this checkout only", out)
        self.assertNotIn("\r", text)
        self.assertTrue(text.startswith("# Handover: DocuMind, this checkout\n") and text.endswith("\n"))
        for line in ("## Alert policies", "17 policies declared in terraform/*.tf",     # ingest_backlog: 13 October 2026
                     "| API p95 latency > 3s | alerts.tf | always | make remediate proposes a rollback | - |",
                     "| Nightly reconcile failed | alerts.tf | when RECONCILE_JOB=true | a person: ",
                     "## The night job", "the Cloud Scheduler job `documind-off-nightly`: `0 23 * * *` in "
                     "Asia/Kolkata, 23:00 IST", "floors documind-slm, documind-vllm, documind-gateway, documind-ui to "
                     "min-instances 0", "## Floors", "`MIN_INSTANCES ?= 0`", "## Revisions",
                     "- `.candidate-revision`: none in this checkout",
                     f"- the gate record (`evals/reports/gate.json`): {FIX}, PASS, finished 2026-11-17T10:12:00Z",
                     f"- the last make smoke-deployed run: 2026-11-17T10:30:00Z, serving {FIX}, PASS",
                     "## CI trust", "No confirmed inputs in this checkout", "## Budget",
                     "`DocuMind monthly budget`, `BUDGET_AMOUNT ?= 5000`", "alerting at 50%, 80%, 100%, 120% forecast",
                     "## State bucket", "`gs://<project>-tfstate/documind/<project>/default.tfstate` (the Makefile's",
                     "## Not read", "- the lane: no PROJECT was given"):
            self.assertIn(line, text, line)
        self.assertEqual(self.lane.calls, [])

    def test_with_the_lane_both_halves(self):
        self.lane_files()
        code, out, text = self.handover("--project", PROJECT, "--region", REGION)
        self.assertEqual(code, 0, out)
        for line in (f"# Handover: DocuMind on {PROJECT}", "17 policies declared in terraform/*.tf, each with what "
                     "ops/runbooks.json says to do when it pages; 2 of them on the lane.",
                     "| make remediate proposes a rollback | enabled, 1 channel |",
                     "| Ingest failed | alerts.tf | always | make remediate proposes a rollback | enabled, no channel: it "
                     "notifies nobody |", "| when RECONCILE_JOB=true |", "not on the lane |",
                     "On the lane and declared by no .tf file in this checkout: A policy made by hand.",
                     "On the lane: ENABLED, `0 23 * * *` in Asia/Kolkata; last attempt 2026-11-17T17:30:00.512Z.",
                     "| documind-ui | asia-south1 | 1 | 10 |", f"- `.candidate-revision`: {FIX} (make promote moves",
                     f"- `.previous-revision`: {GOOD} (make rollback returns", f"| {FIX} | 100 |  |", f"| {FIX} | 0 | "
                     "candidate |", f"4 revisions of documind-api on the lane", f"the serving one, {FIX}, runs GIT_SHA "
                     "abc1234 and GENERATOR_MODEL gemini-3.6-flash", f"{REPO} (repository ID {REPO_ID}), refs/heads/main",
                     "refs/heads/main: the same as the checkout's.", "On the lane: 5000 INR a month, alerting at 50%, "
                     "80%, 100%, 120%.", f"`gs://{PROJECT}-tfstate/documind/{PROJECT}/default.tfstate` (terraform/"
                     ".terraform/terraform.tfstate", "On the lane: the bucket is in ASIA-SOUTH1, versioning on, public "
                     "access prevention enforced, uniform access on, soft delete 7 days.",
                     "The state object: 482113 bytes", "## Not read\n\n- nothing\n"):
            self.assertIn(line, text, line)
        self.assertNotIn("ABCDEF-123456-A1B2C3", text)                    # the billing account stays out of the file
        for argv in self.lane.calls:
            self.assertTrue(cc.is_read(argv) or argv[:3] == ["gcloud", "auth", "print-identity-token"], argv)

    def test_a_failed_read_is_listed_and_the_rest_written(self):
        self.world["fail"]["billing budgets list"] = "ERROR: (gcloud.billing.budgets.list) PERMISSION_DENIED: no access"
        code, out, text = self.handover("--project", PROJECT, "--region", REGION)
        self.assertEqual(code, 1, out)
        self.assertIn("1 lane read failed, each listed under Not read", out)
        self.assertIn("- the budget (gcloud billing budgets list): gcloud billing budgets list failed (exit 1): ERROR: "
                      "(gcloud.billing.budgets.list) PERMISSION_DENIED: no access", text)
        self.assertIn("On the lane: ENABLED", text)                         # the other sections were still read
        self.assertIn("## State bucket", text)

    def test_out_elsewhere(self):
        target = self.home / "elsewhere" / "handover.md"
        code, out, err = run_main("handover", "--fork", str(self.fork), "--out", str(target))
        self.assertEqual(code, 0, out + err)
        self.assertTrue(target.is_file())
        self.assertFalse((self.fork / "HANDOVER.md").exists())
        self.assertFalse(target.with_name("handover.md.part").exists())


# ---------------------------------------------------------------- the command line, the selftest, the PDFs

class CommandLineTests(unittest.TestCase):
    def test_the_selftest(self):
        code, out, _ = run_main("--selftest")
        self.assertEqual(code, 0)
        self.assertIn("capstone_check selftest:", out)

    def test_no_subcommand(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stop:
            cc.main([])
        self.assertEqual(stop.exception.code, 2)

    def test_a_fork_that_is_not_a_directory(self):
        code, _, err = run_main("check", "--fork", str(KIT / "no-such-fork"))
        self.assertEqual(code, 2)
        self.assertIn("is not a directory", err)

    def test_the_page_trees_of_the_kits_pdfs(self):
        sources = json.loads((KIT / "evals" / "real_sources.json").read_text(encoding="utf-8"))
        pdfs = [(KIT / "evals" / "corpus" / s["tenants"][0] / f"{s['slug']}.pdf", s["pages"]) for s in sources]
        pdfs = [(path, pages) for path, pages in pdfs if path.is_file()]
        if not pdfs:
            self.skipTest("no real PDF in evals/corpus/")
        for path, pages in pdfs:
            self.assertEqual(cc.pdf_pages(path.read_bytes()), pages, path.name)


# ---------------------------------------------------------------- the wiring

class WiringTests(unittest.TestCase):
    def read(self, *parts: str) -> str:
        return KIT.joinpath(*parts).read_text(encoding="utf-8")

    def test_the_make_targets(self):
        mk, capstone_mk, readme = self.read("Makefile"), self.read("mk", "capstone.mk"), self.read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                       # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        lane = ("$(if $(filter command line,$(origin PROJECT)),--project $(PROJECT) --region $(REGION) "
                "--slm-region $(SLM_REGION),)")                          # an exported PROJECT does not count
        for target, sub in (("capstone-check", "check"), ("handover", "handover")):
            self.assertIn(target, phony)
            self.assertIn(f"`{target}`", readme)
            self.assertIn(f'\n{target}:\n\t@$(PY) commands/capstone_check.py {sub} --fork "$(or $(FORK),.)" {lane}\n',
                          capstone_mk)                                    # no guard-project: offline needs no PROJECT
        row = next(line for line in readme.splitlines() if line.startswith("| `capstone.mk` | "))
        self.assertIn("`capstone-check`, `handover`", row)
        self.assertIn("`capstone_check.py`", readme)

    def test_fork_is_never_declared(self):
        # make replay (mk/memory.mk, lesson 6.8) reads a FORK of its own from the command line: a default here would
        # hand it --fork . on every run.
        for path in [KIT / "Makefile", *sorted((KIT / "mk").glob("*.mk"))]:
            self.assertNotRegex(path.read_text(encoding="utf-8"), r"(?m)^\s*(?:override\s+)?FORK\s*[:?+!]?=", path.name)

    def test_the_files_are_listed(self):
        # An UNOWNED.md row until a lesson page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = self.read("UNOWNED.md"), self.read("INDEX.md")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        for f in ("commands/capstone_check.py", "mk/capstone.mk", "commands/tests/test_capstone_check.py",
                  "commands/tests/capstone_fork/"):
            self.assertTrue(f"`{f}`" in unowned or f in quoted, f)

    def test_the_kit_facts_the_check_reads(self):
        lane = self.read("commands", "lane.py")
        self.assertEqual(set(re.findall(r'"(\w+)"', re.search(r"GOLDEN_TENANTS = \(([^)]*)\)", lane).group(1))),
                         set(cc.KIT_TENANTS))
        deploy = cc.shell_command(self.read(*cc.UI_SCRIPT.split("/")), "gcloud run deploy documind-ui").split()
        self.assertTrue(set(cc.IAP_FLAGS) <= set(deploy))
        self.assertLessEqual({smoke for _, smoke in cc.LANES} | {"smoke"}, set(dict(cc.release.SMOKES)))
        ingest = self.read("services", "ingest", "main.py")
        self.assertIn('return text, max(1, text.count("\\f") + 1)', ingest)      # text_pages() is this rule
        types = re.search(r"MEDIA_TYPES = \{(.*?)\}", ingest, re.S).group(1)
        self.assertEqual(set(re.findall(r'"(\w+/[\w.-]+)"', types)), {"image/png", "image/jpeg", "video/mp4",
                                                                       "audio/mpeg"})
        self.assertIn("a .md whose .pdf twin exists stays home", self.read("evals", "upload.sh"))
        self.assertIn('"isolation": 5', self.read("evals", "run_eval.py"))      # MIN_ROWS, the rubric's five
        self.assertEqual(cc.ISOLATION_MIN, 5)
        self.assertRegex(self.read("Makefile"), r"(?m)^DOWN_SERVICES_GPU = documind-slm documind-vllm$")
        self.assertEqual(cc.IN_SLM_REGION, ("documind-slm", "documind-vllm"))
        self.assertIn('name        = "documind-off-nightly"', self.read("terraform", "off.tf"))
        self.assertIn('display_name    = "DocuMind monthly budget"', self.read("terraform", "budget.tf"))
        for name in ("MIN_INSTANCES", "BUDGET_AMOUNT", "TFSTATE_BUCKET", "TFSTATE_PREFIX"):
            self.assertIsNotNone(cc.make_default(self.read("Makefile"), name), name)
        self.assertIn("evals/reports/", self.read(".gitignore").splitlines())   # the records: the checkout's only


if __name__ == "__main__":
    unittest.main()
