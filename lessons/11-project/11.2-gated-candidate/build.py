"""Build lesson 11.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Evaluate and gate the exact candidate revision. make gate (commands/release.py gate) judges the revision that
deploy/.candidate-revision names. Before any row is asked, the candidate tag must route to that revision, the
revision must be Ready with an image digest and a GIT_SHA its image tag agrees with (F43; the tag is read from the
service's spec.template, which made the revision, since the revision holds only the digest), and GET /version on the
tag URL, with a token minted for the service's canonical URL (F42), must answer as that GIT_SHA. Then evals/run_eval.py
asks every golden row of the tag URL, and the record, evals/reports/gate.json, names the revision, its digest and
GIT_SHA, the report's sha256, the verdict, the time and the sha256 of the four files the verdict was judged by.
make promote-gated runs gate-check, the files first and then the lane, and then the unchanged make promote.

Computed here, offline, from the kit:
  - release.py gate and gate-check, run in-process against the kit test's own stand-in gcloud (the FAKE of
    commands/tests/test_release_gate.py), with run(), get_version(), live_gate() and the clock replaced as its InProcess
    tests replace them: a green gate and the record it writes, a red gate, every refusal before a row is asked and
    after, and every reason gate-check gives;
  - the panel in step 1: gate-check's rules written again in JavaScript, and node's verdict on every preset and on
    hundreds of seeded random states held equal, line for line, to release.py's own gate-check run on the same files
    against the same stand-in lane;
  - the Change-it (a copy of the record naming another revision, offered through GATE_FILE), and the kit tests' count;
  - the facts the prose states: release.mk's two recipes, the Makefile's release-candidate, record-candidate and the
    flip that ends deploy-services, documind-cd.yml's job output and its promote step, main.py's /version and
    /v1/sources, run_eval.py's thresholds and golden.jsonl's rows, and a gate's rupees from shared/prices.py;
  - the four Python cells, each run against stand-ins before any lane runs it.
Recorded from the author's lane with pb.recorded(): lesson 11.1's dispatch lines, the candidate named, the audience
calls, make gate, the record read back against Cloud Run and gate-check alone (RUN_LIST.md says how).

    python pagekit/build.py 11.2
"""
import contextlib
import copy
import datetime
import hashlib
import html
import importlib.util
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section  # noqa: E402

LESSON = "11.2"
NAME = MANIFEST["modules"]["11"]["lessons"][LESSON]["name"]
NEXT = MANIFEST["modules"]["11"]["lessons"]["11.3"]["name"]
title = (f"<title>Lesson 11.2 {NAME} - a verdict bound to one revision by its digest, its GIT_SHA and its report's "
         "hash, and refused for any other | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"


def kit(rel: str) -> str:
    """One kit file's text."""
    return (KIT / rel).read_text(encoding="utf-8")


def load_file(path: Path, name: str):
    """A Python module, imported from its file."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


release = load_file(KIT / "commands" / "release.py", "release_l112")
TEST = load_file(KIT / "commands" / "tests" / "test_release_gate.py", "test_release_gate_l112")
run_eval = load_file(KIT / "evals" / "run_eval.py", "run_eval_l112")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the gate-check panel: a record, the checkout's files and the lane, through gate-check's rules */
.gk-pre{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px;}
.gk-pre button{font:inherit;font-size:13px;line-height:1.3;text-align:left;padding:6px 11px;border:1px solid var(--border);border-radius:16px;background:var(--card);color:var(--navy);cursor:pointer;min-height:max(36px,var(--touch));-webkit-tap-highlight-color:transparent;}
.gk-pre button[aria-pressed="true"]{border:2px solid var(--teal);background:var(--teal-light);color:var(--teal-dark);font-weight:700;}
.gk-pre button:active{transform:scale(.98);}
.gk-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:10px;margin:0 0 10px;}
.gk-in fieldset{border:1px solid var(--border);border-radius:10px;padding:6px 10px 10px;background:var(--card);min-width:0;}
.gk-in legend{font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--navy);padding:0 4px;}
.gk-in label{font-size:12.5px;color:var(--slate);display:flex;flex-direction:column;gap:3px;margin:6px 0 0;min-width:0;}
.gk-in select,.gk-in input[type=number]{font-family:var(--font);font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:#fff;color:var(--navy);min-height:44px;width:100%;max-width:100%;}
.gk-in .gk-box{flex-direction:row;align-items:center;gap:8px;min-height:max(30px,var(--touch));font-family:var(--mono);font-size:12px;overflow-wrap:anywhere;}
.gk-in input[type=checkbox]{width:20px;height:20px;flex:none;accent-color:var(--teal);}
.gk-sub{font-size:12.5px;color:var(--slate);margin:8px 0 0;}
.gk-v{border-radius:10px;padding:10px 12px;margin:0 0 8px;font-size:var(--small-size);line-height:1.55;font-weight:600;}
.gk-v.ok{background:#d1fae5;border:1px solid #6ee7b7;color:#065f46;}
.gk-v.no{background:#fee2e2;border:1px solid #fca5a5;color:#991b1b;}
.gk-term{font-family:var(--mono);font-size:12px;line-height:1.55;background:var(--code-bg);color:var(--code-text);border-radius:10px;padding:10px 12px;margin:0 0 8px;white-space:pre-wrap;overflow-wrap:anywhere;}
.gk-checks{list-style:none;margin:0;padding:0;font-size:12.5px;line-height:1.45;}
.gk-checks li{display:grid;grid-template-columns:20px minmax(0,1fr);gap:4px;padding:3px 0;border-top:1px dashed var(--border);}
.gk-checks li.gk-h{display:block;border:0;font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--navy);padding:8px 0 2px;}
.gk-checks li.ok b{color:var(--teal-dark);}
.gk-checks li.no b,.gk-checks li.no span{color:#b91c1c;font-weight:700;}
.gk-checks li.skip{color:var(--slate-light);}
@media (hover:hover) and (pointer:fine){.gk-pre button:hover{border-color:var(--teal);}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson's gate asks acme's golden rows, and lesson 11.1's dispatch judged the same candidate with acme on "
         "the kit's own index: pin it the same way for the duration, so the two verdicts are about one lane, and put "
         "the pin back at the end."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head. <code>make gate</code> mints a token as each, both for the API's canonical "
         "URL, and step 5 shows why the audience matters even when the tag URL is the one called.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)

# ================================================================== the kit, read
REL, MK_REL, CD_YML, MAIN, AUTH = ("commands/release.py", "mk/release.mk", ".github/workflows/documind-cd.yml",
                                   "services/rag-api/main.py", "services/rag-api/auth.py")
MK, RMK, CD, MAIN_SRC = kit("Makefile"), kit(MK_REL), kit(CD_YML), kit(MAIN)
recipe = lambda text, name: text[text.index(f"\n{name}:") + 1:].split("\n\n", 1)[0]   # noqa: E731

# mk/release.mk: the two targets, the record they share, and the order promote-gated runs its two lines in
GATE_FILE_DEFAULT = re.search(r"^GATE_FILE \?= (\S+)$", RMK, re.M).group(1)
assert GATE_FILE_DEFAULT == "evals/reports/gate.json"
GATE_RECIPE, PG_RECIPE = recipe(RMK, "gate").splitlines(), recipe(RMK, "promote-gated").splitlines()
assert GATE_RECIPE == ["gate: guard-project",
                       "\t@$(PY) commands/release.py gate --project $(PROJECT) --region $(REGION) --gate-file $(GATE_FILE)"]
assert PG_RECIPE == ["promote-gated: guard-project",
                     "\t@$(PY) commands/release.py gate-check --project $(PROJECT) --region $(REGION) --gate-file $(GATE_FILE)",
                     "\t@$(MAKE) --no-print-directory promote PROJECT=$(PROJECT) REGION=$(REGION)"], PG_RECIPE
assert not any(line.lstrip("\t").startswith("-") for line in PG_RECIPE[1:])   # no "-": a failing check stops make
CHECK_LINE = RMK.splitlines().index(PG_RECIPE[1]) + 1                  # make's error line names it
MAKE_REFUSED = f"make: *** [{MK_REL}:{CHECK_LINE}: promote-gated] Error 1"
assert "make up and make deploy-services\n# release the API with no gate at all" in RMK
assert "its path=clouddeploy would put run-service.yaml's settings on documind-api,\n# and is not to be dispatched" in RMK
PHONY = MK[MK.index(".PHONY:"):MK.index("# ---------- the module files")].replace("\\", " ").split()
assert "gate" in PHONY and "promote-gated" in PHONY

# release.py: what the record binds, how long it holds, the clock skew, the rules, the record's required fields
RULES, MAXH = list(release.RULES), release.MAX_AGE_HOURS
SKEW_S = int(release.SKEW.total_seconds())
WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 9: "nine"}
assert RULES == ["evals/run_eval.py", "evals/golden.jsonl", "evals/required.json", "evals/manifest.json"], RULES
assert (MAXH, SKEW_S, release.GATE_FORMAT) == (24.0, 300, "documind-gate/1")
assert (release.MEMBER_SA, release.OUTSIDER_SA, release.SERVICE) == ("documind-ui-sa", "documind-outsider-sa", "documind-api")
MAXH_S = f"{MAXH:g}"

# the Makefile: the candidate's two targets, the echo make record-candidate prints, the flip deploy-services ends with
RC = recipe(MK, "release-candidate")
assert ("--image $(IMAGE_REPO)/api:$(GIT_SHA) --no-traffic --tag candidate --update-env-vars GIT_SHA=$(GIT_SHA) --quiet" in RC
        and "record-candidate" in RC)
ECHO_REV = re.search(r'echo ">> candidate revision: \$\$REV (\(deploy/\.candidate-revision - [^"]+\))"',
                     recipe(MK, "record-candidate")).group(1)
assert "status.latestCreatedRevisionName" in recipe(MK, "record-candidate")
DS = recipe(MK, "deploy-services")
assert ("--to-revisions $$REV=100" in DS and "status.latestCreatedRevisionName" in DS
        and "the revision this deploy created" in DS)
UP = recipe(MK, "up")
assert "$(MAKE) drift secrets build-access build deploy-services" in UP
ALL_MK = MK + "".join("\n" + p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
UP_TARGETS = ["up"] + UP.split("$(MAKE) ", 1)[1].split()       # make up and every target it runs, deploy-services among them
for t in UP_TARGETS:                                              # none of them reads or removes the gate record
    body = recipe(ALL_MK, t)
    assert "evals/reports" not in body and "gate.json" not in body and "release.py" not in body, t

# documind-cd.yml: CI gates by job dependency, passes the name as an output, and runs plain make promote
JOB_TEXT = dict(re.findall(r"^  ([a-z-]+):\n(.*?)(?=^  [a-z-]+:\n|\Z)", CD.split("\njobs:\n", 1)[1], re.M | re.S))
assert "outputs:\n      candidate: ${{ steps.candidate.outputs.revision }}" in JOB_TEXT["release-candidate"]
assert JOB_TEXT["release-candidate"].rstrip().endswith('API="https://candidate---documind-api-$NUMBER.$REGION.run.app"')
assert "needs: release-candidate" in JOB_TEXT["promote"] and 'make promote PROJECT="$PROJECT" REGION="$REGION"' in JOB_TEXT["promote"]
assert "promote-gated" not in CD and "make gate" not in CD and "REPORT=" not in CD   # CI keeps no record and no report
assert re.search(r"options: \[candidate, clouddeploy\]\n\s+default: candidate", CD)

# main.py and auth.py: the API checks a bearer token's audience on its answering routes; /version checks nothing itself
ROUTES = dict(re.findall(r'@app\.(?:get|post)\("([^"]+)"[^)]*\)\ndef \w+\((.*)\):', MAIN_SRC))   # route -> its parameters
assert ROUTES["/version"] == "" and ROUTES["/health"] == "", ROUTES
assert all(ROUTES[r].endswith("user=Depends(verify_iap)") for r in ("/v1/sources", "/v1/query", "/v1/stream", "/v1/passages")), ROUTES
assert "return iap.identity(request.headers, bearer_audience=SELF_URL or None)" in kit(AUTH)
assert "SELF_URL=https://documind-api-$PROJECT_NUMBER.${REGION:-us-central1}.run.app" in kit("commands/lesson-12.2.sh")
CFG = kit("services/rag-api/config.py")
PROMPT = "{}@{}".format(re.search(r'prompt_id: str = "([\w-]+)"', CFG).group(1),
                        re.search(r'prompt_version: str = "(\w+)"', CFG).group(1))
GENERATOR = re.search(r"^GENERATOR_MODEL \?= (\S+)$", MK, re.M).group(1)
assert (PROMPT, GENERATOR) == ("documind-rag@v3", "gemini-3.6-flash")

# the rows and the thresholds (lessons 4.2 and 4.3 teach them), and a gate's rupees from the kit's own price table
GOLDEN = [json.loads(line) for line in kit("evals/golden.jsonl").splitlines() if line.strip()]
N_ROWS, N_THRESHOLDS = len(GOLDEN), len(run_eval.THRESHOLDS)
N_ISO = sum(r.get("shape") == "isolation" for r in GOLDEN)
N_ANS = sum(bool(r.get("answerable")) for r in GOLDEN)
PRICES = {}
exec(compile(kit("shared/prices.py"), "prices.py", "exec"), PRICES)
RATE_IN, RATE_OUT = PRICES["PRICES"][GENERATOR]
TYPICAL = (2000, 300)              # the course's typical answer (lessons 4.3, 4.4, 11.1 and 11.6): 2,000 tokens in, 300 out
RS_ANSWER = (TYPICAL[0] * RATE_IN + TYPICAL[1] * RATE_OUT) / 1_000_000 * PRICES["USD_INR"]
RS_GATE = round(RS_ANSWER * N_ROWS)
assert (PRICES["USD_INR"], RATE_IN, RATE_OUT, N_THRESHOLDS) == (85, 1.50, 7.50, 9)
RUN_LIST = (HERE / "RUN_LIST.md").read_text(encoding="utf-8")
for fact in (f"about Rs {RS_GATE}", f"Rs {RS_ANSWER:.2f}", f"{N_ROWS} golden rows", f"the outsider's {N_ISO}",
             f"{MAXH_S} hours", f"about Rs {2 * RS_GATE} in all", f"then {6 + len(RULES)} lines",
             f"{N_ROWS} rows ({N_ANS} answerable, {N_ROWS - N_ANS} not)", f"{WORDS[N_THRESHOLDS]} `[PASS]` lines",
             f"the {WORDS[len(RULES)]} rule files"):
    assert fact in RUN_LIST, f"RUN_LIST.md no longer says {fact!r}: the kit's rows, prices or rules moved"
N_TESTS = len(re.findall(r"^    def test_\w+\(self", kit("commands/tests/test_release_gate.py"), re.M))
assert N_TESTS >= 29, N_TESTS

# ================================================================== verbatim kit excerpts
EXCERPTS = {
    "mk_gate": ("mk/release.mk - GATE_FILE, make gate and make promote-gated",
                block(MK_REL, "# ---------- The gate on the exact candidate revision, lesson 11.2 ----------",
                      end="# ---------- Promote, roll back and repair a controlled failure, lesson 11.3 ----------")),
    "rel_consts": ("commands/release.py - what the gate binds: the service, its accounts, the rules, 24 hours, the shapes",
                   block(REL, 'SERVICE = "documind-api"', end="def now() -> datetime.datetime:")),
    "rel_facts": ("commands/release.py - revision_facts() and unjudgeable(): what a revision is, and why it cannot be gated",
                  block(REL, "def revision_facts(project: str, region: str, name: str) -> dict:", end="def project_number(")),
    "rel_gate_a": ("commands/release.py - cmd_gate(), first half: every refusal before a row is asked",
                   block(REL, "def cmd_gate(a) -> int:", end="    rules = rules_now()")),
    "rel_gate_b": ("commands/release.py - cmd_gate(), second half: the rows, the tag read again, the record",
                   block(REL, "    rules = rules_now()", end="def load_record(")),
    "rel_blocked": ("commands/release.py - report_blocked() and write_record(): the verdict from the report, the record whole",
                    block(REL, "def report_blocked(report) -> list[str]:", end="def cmd_gate(")),
    "rel_offline": ("commands/release.py - offline_reasons(): the files, every reason at once",
                    block(REL, "def offline_reasons(", end="def live_reasons(")),
    "rel_live": ("commands/release.py - live_reasons() and cmd_gate_check(): the lane, read only when the files agree",
                 block(REL, "def live_reasons(", end="# ----------------------------------------------------------------")),   # to the next section
    "mk_record": ("Makefile - release-candidate and record-candidate: the image on a no-traffic revision, its name in a file",
                  block("Makefile", "release-candidate: guard-project", end="# Traffic to the recorded candidate, by name.")),
    "auth_self": ("services/rag-api/auth.py - SELF_URL: the one audience a bearer token is checked against",
                  block(AUTH, "# This service's own URL - the audience every caller mints an ID token for.", n=3) + "\n...\n"
                  + block(AUTH, "        return iap.identity(request.headers, bearer_audience=SELF_URL or None)", n=6)),
    "main_routes": ("services/rag-api/main.py - /version asks for no identity; /v1/sources goes through verify_iap",
                    block(MAIN, '@app.get("/version")', n=2) + "\n...\n" + block(MAIN, '@app.get("/v1/sources")', n=2)),
    "mk_f42": ("Makefile - eval-live's comment: the audience does not move with the URL (F42)",
               block("Makefile", "# The token's audience is the SERVICE's canonical URL whichever of its URLs is called", n=3)),
    "rel_version": ("commands/release.py - get_version(): GET /version on the tag URL, twice for a cold start",
                    block(REL, "def get_version(url: str, token: str) -> dict:", end="def live_gate(")),
    "cd_ci": (".github/workflows/documind-cd.yml - CI's binding: a job output, a job dependency, plain make promote",
              block(CD_YML, "    # The candidate's NAME travels to promote as a job output", n=6) + "\n...\n"
              + block(CD_YML, "      - name: The live gate, on the candidate", n=4) + "\n\n"
              + block(CD_YML, "  promote:", n=4) + "\n...\n"
              + block(CD_YML, "      - name: Traffic to the candidate, by name", n=5)),
    "mk_ungated": ("Makefile - deploy-services ends by giving its own new revision all the traffic; make up runs it",
                   block("Makefile", "# After the API's DEPLOY block, traffic goes to the revision that block just created, explicitly", n=4)
                   + "\n...\n" + block("Makefile", '@if echo "$(SCRIPTS)" | grep -q lesson-12.2.sh; then', n=4) + "\n...\n"
                   + block("Makefile", "up: guard-project", n=3)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["mk_gate"].rstrip().endswith("@$(MAKE) --no-print-directory promote PROJECT=$(PROJECT) REGION=$(REGION)")
assert E["rel_consts"].rstrip().endswith("REFUSED = 1") and "MAX_AGE_HOURS = 24.0" in E["rel_consts"]
assert E["rel_facts"].rstrip().endswith("    return why") and "(F43)" in E["rel_facts"]
assert E["rel_gate_a"].rstrip().endswith("identity_token(project, OUTSIDER_SA, audience)")
assert E["rel_gate_b"].rstrip().endswith("    return REFUSED") and "write_record(gate_file, {" in E["rel_gate_b"]
assert E["rel_blocked"].rstrip().endswith("    os.replace(part, path)")
assert E["rel_offline"].rstrip().endswith("    return reasons") and E["rel_live"].rstrip().endswith("    return 0")
assert E["mk_record"].splitlines()[0] == "release-candidate: guard-project" and "> .candidate-revision" in E["mk_record"]
assert E["mk_ungated"].splitlines()[-3] == "up: guard-project", E["mk_ungated"]
assert E["cd_ci"].rstrip().endswith('make promote PROJECT="$PROJECT" REGION="$REGION"')
assert E["rel_version"].rstrip().endswith('raise Stop(f"GET {url}/version failed twice: {last}")')
fill = filler(EXCERPTS)

# ================================================================== the stand-in lane, as the kit's own tests build it
SP_PROJECT, SP_NUMBER, REGION = "documind-ai-your-id", "100000000011", "asia-south1"   # release.py wants a lower-case id
SERVING, CAND, NEWER = TEST.SERVING, TEST.CAND, TEST.NEWER                              # the kit test's revision names
SHA = {SERVING: "PREVIOUS", CAND: "COMMIT", NEWER: "NEWER"}
IMG = f"{REGION}-docker.pkg.dev/{SP_PROJECT}/documind/api"
AUDIENCE = f"https://documind-api-{SP_NUMBER}.{REGION}.run.app"
TAG_URL = f"https://candidate---documind-api-{SP_NUMBER}.{REGION}.run.app"
START = TEST.START                                                                       # 2026-11-16 10:02:11 UTC
FINISH = START + datetime.timedelta(minutes=10)                                          # the stand-in rows take ten
NOW = FINISH + datetime.timedelta(hours=2)                                               # the panel's clock
assert NOW.microsecond == 0


def facts_of(name: str) -> dict:
    """One stand-in revision: its image, the digest Cloud Run would report, its GIT_SHA, Ready, its service."""
    return {"image": f"{IMG}:{SHA[name]}", "digest": f"{IMG}@sha256:{hashlib.sha256(name.encode()).hexdigest()}",
            "git_sha": SHA[name], "ready": True, "service": "documind-api"}


D_OTHER = f"{IMG}@sha256:{hashlib.sha256(b'another image').hexdigest()}"
WORLD = {"project": SP_PROJECT, "number": SP_NUMBER, "region": REGION, "latest": CAND,
         "traffic": [{"revisionName": SERVING, "percent": 100}, {"revisionName": CAND, "tag": "candidate"}],
         "revisions": {n: facts_of(n) for n in (SERVING, CAND, NEWER)}, "no_mint": []}
PRISTINE = {rel: (KIT / rel).read_bytes() for rel in RULES}


def placeholders(text: str) -> str:
    """The stand-in's project and number as the course's placeholders; nothing of the kit test's lane reaches the page."""
    out = text.replace(SP_PROJECT, PROJ).replace(SP_NUMBER, "NUMBER")
    assert TEST.PROJECT not in out and TEST.NUMBER not in out, out
    return out


class StandInLane:
    """A temporary home holding the kit test's stand-in gcloud (its FAKE, imported and called in-process), one lane's
    world.json, and a copy of the files the gate reads: release.py runs against it as test_release_gate.py runs it."""

    def __init__(self):
        self.home = Path(tempfile.mkdtemp(prefix="lesson112_"))
        self.kit = self.home / "kit"
        for rel in RULES:
            (self.kit / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.kit / rel).write_bytes(PRISTINE[rel])
        (self.home / "fake.py").write_text(TEST.FAKE, encoding="utf-8")
        self.fake = load_file(self.home / "fake.py", "lesson112_fake")
        self.clock, self.rc, self.report, self.during = START, 0, TEST.eval_report(), None
        self.set_world(WORLD)

    def set_world(self, world: dict) -> None:
        (self.home / "world.json").write_text(json.dumps(world), encoding="utf-8")

    def world(self) -> dict:
        return json.loads((self.home / "world.json").read_text(encoding="utf-8"))

    def calls(self) -> list:
        path = self.home / "calls.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def forget_calls(self) -> None:
        (self.home / "calls.jsonl").unlink(missing_ok=True)

    def run(self, argv, cwd=None):
        """release.run(): every gcloud call goes to the stand-in."""
        assert argv[0] == "gcloud", argv
        code, out, err = self.fake.handle(argv[0], list(argv[1:]))
        return subprocess.CompletedProcess(argv, code, out, err)

    def version(self, url, token):
        """release.get_version(): the tag URL's /version from the stand-in's world; a token minted for any audience but
        the canonical URL is refused, as the test's own stand-in refuses it."""
        if not token.endswith("." + AUDIENCE):
            raise release.Stop(f"GET {url}/version answered HTTP 401: the token was refused")
        return self.fake.version(self.world(), url)

    def gate(self, url, report, member, outsider):
        """release.live_gate(): the rows take ten minutes, and the report run_eval.py --report writes is written."""
        if self.during:
            self.during()
        self.clock += datetime.timedelta(minutes=10)
        if self.report is not None:
            Path(report).parent.mkdir(parents=True, exist_ok=True)
            Path(report).write_bytes(json.dumps(self.report, indent=1).encode("utf-8"))
        return self.rc

    def main(self, *args: str) -> tuple:
        """release.py's command line with the stand-ins at its seams: (exit code, stdout, stderr). The four variables
        release.py would read from this shell are set aside for the call and put back after it."""
        out, err = io.StringIO(), io.StringIO()
        kept = {k: os.environ.pop(k) for k in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "PROJECT", "REGION")
                if k in os.environ}
        try:
            with contextlib.ExitStack() as stack:
                for name, value in (("KIT", self.kit), ("run", self.run), ("get_version", self.version),
                                    ("live_gate", self.gate), ("now", lambda: self.clock)):
                    stack.enter_context(mock.patch.object(release, name, value))
                stack.enter_context(contextlib.redirect_stdout(out))
                stack.enter_context(contextlib.redirect_stderr(err))
                code = release.main(list(args))
        finally:
            os.environ.update(kept)
        return code, out.getvalue(), err.getvalue()

    def close(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)


def gated(rc: int = 0, report: dict | None = None) -> tuple:
    """make gate's work on the stand-in lane: (exit code, what it printed, the record, its text, the report's bytes, the
    stand-in's calls)."""
    lane = StandInLane()
    try:
        (lane.kit / ".candidate-revision").write_text(CAND + "\n", encoding="utf-8")
        lane.rc, lane.report = rc, (report if report is not None else TEST.eval_report())
        code, out, err = lane.main("gate", "--project", SP_PROJECT, "--region", REGION)
        rec_path = lane.kit / "evals" / "reports" / "gate.json"
        rec_text = rec_path.read_text(encoding="utf-8")
        record = json.loads(rec_text)
        body = (lane.kit / record["report"]).read_bytes()
        return code, out + err, record, rec_text, body, lane.calls()
    finally:
        lane.close()


G_CODE, G_OUT, G_REC, G_REC_TEXT, G_BODY, G_CALLS = gated()
R_CODE, R_OUT, R_REC, _, R_BODY, _ = gated(1, TEST.eval_report(failed=("correct_rate",)))
assert (G_CODE, R_CODE) == (0, release.REFUSED) and (G_REC["verdict"], R_REC["verdict"]) == ("pass", "fail")
assert G_REC["finished"] == release.stamp(FINISH) and G_REC["report"] == f"evals/reports/gate-{CAND}.json"
assert G_REC["report_sha256"] == hashlib.sha256(G_BODY).hexdigest() and G_REC["revision"] == CAND
assert G_REC["digest"] == WORLD["revisions"][CAND]["digest"] and G_REC["git_sha"] == SHA[CAND]
assert G_REC["rules"] == {rel: hashlib.sha256(PRISTINE[rel]).hexdigest() for rel in RULES}
assert set(release.RECORD_FIELDS) <= set(G_REC) and len(G_REC) == 21, sorted(G_REC)
assert R_REC["blocked"] == ["correct_rate: 61% < 68%"] and R_REC["eval_exit"] == 1
for c in G_CALLS:                                          # the gate reads, mints two tokens, and writes nothing to Cloud Run
    assert c["args"][:2] == ["auth", "print-identity-token"] or "describe" in c["args"][:3], c
assert sum(c["args"][:2] == ["auth", "print-identity-token"] for c in G_CALLS) == 2
assert f">> gate: {CAND}, the revision .candidate-revision names and the candidate tag routes to" in G_OUT
assert f"   {CAND}  PASS  {G_REC['rows']} rows, eval exit 0, report sha256 {G_REC['report_sha256']}" in G_OUT
assert f"   {CAND}  FAIL  correct_rate: 61% < 68%" in R_OUT and "make promote-gated refuses it (make promote reads no record)" in R_OUT
OUT_SGATE, OUT_SRED, OUT_SRECORD = placeholders(G_OUT), placeholders(R_OUT), placeholders(G_REC_TEXT)
N_RECORD_KEYS = len(G_REC)

# ------------------------------------------------------------------ every refusal make gate gives, before and after the rows start
KEPT = '{"kept": "an earlier record"}'


def gate_stop(world_edit=None, cand=CAND, region=REGION, rc=0, report="green", during=None) -> tuple:
    """One make gate on a fresh stand-in lane that holds an earlier record: (exit code, what it printed, the earlier
    record kept or gone, rows asked or not)."""
    lane = StandInLane()
    try:
        world = copy.deepcopy(WORLD)
        if world_edit:
            world_edit(world)
        lane.set_world(world)
        if cand:
            (lane.kit / ".candidate-revision").write_text(cand + "\n", encoding="utf-8")
        rec = lane.kit / "evals" / "reports" / "gate.json"
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text(KEPT, encoding="utf-8")
        lane.rc, lane.report = rc, (TEST.eval_report() if report == "green" else None)
        asked = []

        def rows_start():
            """The stand-in gate's first moment: the rows have started, and the case's event happens now."""
            asked.append(1)
            if during:
                during(lane)
        lane.during = rows_start
        code, out, err = lane.main("gate", "--project", SP_PROJECT, "--region", region)
        kept = rec.exists() and rec.read_text(encoding="utf-8") == KEPT
        return code, placeholders(out + err), kept, bool(asked)
    finally:
        lane.close()


def rev_edit(**fields):
    """A world edit: the candidate revision with these fields changed."""
    return lambda w: w["revisions"][CAND].update(fields)


def interrupt(lane):
    """Ctrl-C while the rows are asked."""
    raise KeyboardInterrupt


def tag_moves(lane):
    """Another checkout moves the candidate tag while the rows are asked."""
    world = lane.world()
    world["traffic"] = [{"revisionName": SERVING, "percent": 100}, {"revisionName": NEWER, "tag": "candidate"}]
    lane.set_world(world)


STOP_CASES = [
    ("No <code>.candidate-revision</code> in the checkout", dict(cand=None)),
    ("The candidate tag on a newer revision", dict(world_edit=lambda w: w.update(traffic=[
        {"revisionName": SERVING, "percent": 100}, {"revisionName": NEWER, "tag": "candidate"}]))),
    ("The candidate tag removed", dict(world_edit=lambda w: w.update(traffic=[{"revisionName": SERVING, "percent": 100}]))),
    ("The revision not Ready", dict(world_edit=rev_edit(ready=False))),
    ("No image digest on the revision", dict(world_edit=rev_edit(digest=f"{IMG}:{SHA[CAND]}"))),
    ("No <code>GIT_SHA</code> on the revision", dict(world_edit=rev_edit(git_sha=""))),
    ("An image-only update (F43)", dict(world_edit=rev_edit(image=f"{IMG}:{SHA[NEWER]}"))),
    ("An update made a revision after the candidate", dict(world_edit=lambda w: w.update(latest=NEWER))),
    ("The tag URL answers as another build", dict(world_edit=rev_edit(answers={"git_sha": SHA[SERVING]}))),
    ("The outsider's token cannot be minted", dict(world_edit=lambda w: w.update(no_mint=["documind-outsider-sa"]))),
    ("<code>REGION</code> left at the Makefile's default", dict(region="us-central1")),
    ("<code>run_eval.py</code> refuses to start, so no report", dict(rc=2, report=None)),
    ("The tag moves while the rows are asked", dict(during=tag_moves)),
    ("Ctrl-C while the rows are asked", dict(during=interrupt)),
]
STOPS = []
for label, kw in STOP_CASES:
    code, text, kept, asked = gate_stop(**kw)
    stop = [line for line in text.splitlines() if line.startswith("STOP: ")]
    assert code == release.STOPPED and len(stop) == 1, (label, code, text)
    STOPS.append((label, asked, kept, stop[0]))
assert [s[1] for s in STOPS] == [False] * 11 + [True] * 3                 # eleven before the rows, three after
assert [s[2] for s in STOPS] == [True] * 11 + [False] * 3                 # an earlier record survives only the first eleven
assert "image-only update keeps the old GIT_SHA (F43)" in STOPS[6][3] and "Cannot find service" in STOPS[10][3]
assert "spec.template has made a later revision" in STOPS[7][3]
assert STOPS[12][3].startswith(f"STOP: the candidate tag moved to {NEWER} while the rows were asked")

# ------------------------------------------------------------------ gate-check, on any state of the record, the files and the lane
BASE = {"green": G_REC, "red": R_REC}
REPORT_BYTES = {rows: {"written": body, "edited": json.dumps(json.loads(body), indent=2).encode("utf-8")}
                for rows, body in (("green", G_BODY), ("red", R_BODY))}
HASH = {rows: {k: hashlib.sha256(v).hexdigest() for k, v in d.items()} for rows, d in REPORT_BYTES.items()}
BLOCKED = {rows: release.report_blocked(json.loads(REPORT_BYTES[rows]["written"])) for rows in BASE}
assert BLOCKED == {"green": [], "red": ["correct_rate: 61% < 68%"]} and HASH["green"]["written"] == G_REC["report_sha256"]
assert R_REC["report"] == G_REC["report"]                              # both gates judged the candidate: one report path
DEF = {"record": "present", "rev": CAND, "rows": "green", "verdict": "pass", "age": 7200, "region": REGION, "cand": CAND,
       "report": "written", "rules": [], "tag": CAND, "image": "same", "ready": True}


def py_record(s: dict) -> dict:
    """The record in state s: the one make gate wrote (green or red), with the panel's fields as edited."""
    rec = copy.deepcopy(BASE[s["rows"]])
    rec.update(revision=s["rev"], region=s["region"], finished=release.stamp(NOW - datetime.timedelta(seconds=s["age"])))
    if s["verdict"] == "pass":
        rec.update(verdict="pass", eval_exit=0, blocked=[])
    else:
        rec.update(verdict="fail", eval_exit=1, blocked=list(BASE["red"]["blocked"]) if s["rows"] == "red" else [])
    return rec


CHECKER = StandInLane()
ON_DISK = {rel: PRISTINE[rel] for rel in RULES}


def py_check(s: dict) -> tuple:
    """release.py gate-check on the stand-in lane in state s: (exit code, the lines it printed, whether it read the lane)."""
    lane = CHECKER
    for rel in RULES:                                       # a rule file changed since the gate: one more line in it
        want = PRISTINE[rel] + (b"\n# changed after the gate\n" if rel in s["rules"] else b"")
        if ON_DISK[rel] != want:
            (lane.kit / rel).write_bytes(want)
            ON_DISK[rel] = want
    reports = lane.kit / "evals" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    record, report, cand = reports / "gate.json", lane.kit / G_REC["report"], lane.kit / ".candidate-revision"
    if s["record"] == "missing":
        record.unlink(missing_ok=True)
    else:
        record.write_bytes(json.dumps(py_record(s), indent=1).encode("utf-8"))
    if s["report"] == "deleted":
        report.unlink(missing_ok=True)
    else:
        report.write_bytes(REPORT_BYTES[s["rows"]][s["report"]])
    if s["cand"]:
        cand.write_bytes((s["cand"] + "\n").encode("utf-8"))
    else:
        cand.unlink(missing_ok=True)
    world = copy.deepcopy(WORLD)
    world["traffic"] = [{"revisionName": SERVING, "percent": 100}] + (
        [{"revisionName": s["tag"], "tag": "candidate"}] if s["tag"] else [])
    if s["image"] == "other":
        world["revisions"][s["rev"]]["digest"] = D_OTHER
    if not s["ready"]:
        world["revisions"][s["rev"]]["ready"] = False
    lane.set_world(world)
    lane.forget_calls()
    lane.clock = NOW
    code, out, err = lane.main("gate-check", "--project", SP_PROJECT, "--region", REGION)
    assert not (out and err), (out, err)
    return code, placeholders(out + err).splitlines(), bool(lane.calls())


def state(**edits) -> dict:
    """The panel's starting state with these fields changed."""
    return {**DEF, **edits}


PRESETS = [
    ("ok", "The gated candidate, 2 hours later", {}),
    ("newer", "A newer candidate recorded", {"cand": NEWER, "tag": NEWER}),
    ("renamed", "The record renamed to the serving revision", {"rev": SERVING}),
    ("forged", "Record and file both renamed", {"rev": SERVING, "cand": SERVING}),
    ("red", "A red gate", {"rows": "red", "verdict": "fail"}),
    ("topass", "A red record edited to pass", {"rows": "red", "verdict": "pass"}),
    ("edited", "The report edited after the gate", {"report": "edited"}),
    ("stale", f"{int(MAXH) + 1} hours later", {"age": (int(MAXH) + 1) * 3600}),
    ("rules", "golden.jsonl changed since", {"rules": ["evals/golden.jsonl"]}),
    ("moved", "The tag moved on", {"tag": NEWER}),
    ("image", "Another image under that name", {"image": "other"}),
    ("pile", "Three days later, red, and a newer candidate",
     {"cand": NEWER, "tag": NEWER, "rows": "red", "verdict": "fail", "age": 72 * 3600}),
]
PRESET_STATES = {k: state(**v) for k, _, v in PRESETS}
PY = {k: py_check(s) for k, s in PRESET_STATES.items()}
assert PY["ok"][0] == 0 and all(PY[k][0] == release.REFUSED for k in PY if k != "ok"), {k: v[0] for k, v in PY.items()}
assert [k for k, v in PY.items() if v[2]] == ["ok", "forged", "moved", "image"]   # the lane is read only when the files agree
assert len(PY["forged"][1]) == 3 and len(PY["pile"][1]) == 4 and not PY["pile"][2]
assert PY["ok"][1][0] == f"gate record evals/reports/gate.json: {CAND} passed at {release.stamp(FINISH)}, 2.0 hours ago"
OUT_SCHECK = "\n".join(PY["ok"][1])

# the reference table in step 4: every reason gate-check gives, each from release.py itself
TABLE_CASES = [
    ("No record: <code>make gate</code> never ran here", state(record="missing")),
    ("A record from another region", state(region="us-central1")),
    ("A newer candidate recorded in <code>.candidate-revision</code>", PRESET_STATES["newer"]),
    ("The record renamed to the serving revision", PRESET_STATES["renamed"]),
    ("<code>.candidate-revision</code> deleted", state(cand="")),
    ("A red gate", PRESET_STATES["red"]),
    ("The report deleted", state(report="deleted")),
    ("The report edited after the gate", PRESET_STATES["edited"]),
    ("A red record edited to pass", PRESET_STATES["topass"]),
    (f"{int(MAXH) + 1} hours after the gate", PRESET_STATES["stale"]),
    ("A record stamped an hour in the future", state(age=-3600)),
    ("<code>golden.jsonl</code> and <code>run_eval.py</code> changed since", state(rules=["evals/run_eval.py", "evals/golden.jsonl"])),
    ("The candidate tag moved to a newer revision", PRESET_STATES["moved"]),
    ("Record and <code>.candidate-revision</code> both renamed to the serving revision", PRESET_STATES["forged"]),
    ("Cloud Run reports another image for that revision", PRESET_STATES["image"]),
    ("The revision not Ready", state(ready=False)),
    ("Three days later, red, and a newer candidate", PRESET_STATES["pile"]),
]
CHECKS_TABLE_ROWS = []
REFUSED_HEAD = "REFUSED: the gate record evals/reports/gate.json does not let make promote move traffic:"
for label, s in TABLE_CASES:
    code, lines, lane_read = py_check(s)
    assert code == release.REFUSED and lines[0] == REFUSED_HEAD, (label, lines)
    CHECKS_TABLE_ROWS.append((label, lane_read, [line[4:] for line in lines[1:]]))
assert [r[1] for r in CHECKS_TABLE_ROWS] == [False] * 12 + [True] * 4 + [False]

# ================================================================== the panel: gate-check's rules in JavaScript, held equal to release.py's
REV_LABEL = {CAND: f"{CAND} (the gated candidate)", NEWER: f"{NEWER} (a newer candidate)", SERVING: f"{SERVING} (serving now)"}
CHECKS = [
    ("f", "lane", "the record is this lane's: project, region, service"),
    ("f", "cand", ".candidate-revision names the record's revision"),
    ("f", "green", "the verdict is pass, eval exit 0"),
    ("f", "present", "the report is still there"),
    ("f", "hash", "the report still hashes to the record's sha256"),
    ("f", "agrees", "the report says what the record says"),
    ("f", "time", f"finished within {MAXH_S} hours, and not in the future"),
    ("f", "rules", f"judged by this checkout's {WORDS[len(RULES)]} rule files"),
    ("l", "tag", "the candidate tag is on no other revision"),
    ("l", "facts", "Cloud Run's digest and GIT_SHA are the record's"),
    ("l", "ready", "the revision is Ready"),
]
GK_DATA = {
    "lane": {"project": PROJ, "region": REGION, "service": release.SERVICE},
    "revs": {n: {"digest": placeholders(WORLD["revisions"][n]["digest"]), "sha": SHA[n]} for n in (SERVING, CAND, NEWER)},
    "other": placeholders(D_OTHER),
    "base": {rows: {k: (placeholders(v) if isinstance(v, str) else v) for k, v in BASE[rows].items()
                    if k in ("project", "service", "report", "report_sha256", "digest", "git_sha", "blocked")} for rows in BASE},
    "hash": HASH, "blocked": BLOCKED, "rules": RULES, "now": int(NOW.timestamp() * 1000), "maxh": MAXH, "skew": SKEW_S,
    "presets": {k: {**v, "age": v["age"] / 3600} for k, v in PRESET_STATES.items()},
    "checks": [{"g": g, "k": k, "t": t} for g, k, t in CHECKS],
    "say": {"files": "the files, read first", "lane": "the lane, read only when every file agrees",
            "skipped": " (not reached)", "refused": "gate-check exits 1: make stops here, and make promote never runs.",
            "passed": "gate-check exits 0, so make promote runs next and moves traffic to {rev} by name."},
}
assert GK_DATA["lane"]["project"] == GK_DATA["base"]["green"]["project"] == PROJ
GK_JS = r"""var D = __DATA__;
function stamp(ms){ return new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z'); }
function hours(sec){
  var a = Math.abs(sec), q = Math.floor(a / 360), rem = a - 360 * q;
  if (rem === 180 && (2 * q + 1) % 5 === 0) { return (sec < 0 ? '-' : '') + ((q % 2 === 0 ? q : q + 1) / 10).toFixed(1); }
  return (sec / 3600).toFixed(1);
}
function record(s){
  var b = D.base[s.rows], r = {};
  Object.keys(b).forEach(function(k){ r[k] = b[k]; });
  r.revision = s.rev; r.region = s.region; r.finished = stamp(D.now - s.age * 1000);
  if (s.verdict === 'pass') { r.verdict = 'pass'; r.eval_exit = 0; r.blocked = []; }
  else { r.verdict = 'fail'; r.eval_exit = 1; r.blocked = s.rows === 'red' ? D.base.red.blocked.slice() : []; }
  return r;
}
function files(r, s){
  var why = [], m = {}, L = D.lane, rev = r.revision;
  m.lane = r.project === L.project && r.region === L.region && r.service === L.service;
  if (!m.lane) { why.push('another lane: the record is of ' + r.service + ' in ' + r.project + ', ' + r.region + '; this is ' + L.service + ' in ' + L.project + ', ' + L.region); }
  if (!s.cand) { m.cand = false; why.push('.candidate-revision is missing: make release-candidate (or make candidate) records the revision it makes, and make promote moves traffic to that revision by name'); }
  else { m.cand = s.cand === rev; if (!m.cand) { why.push('another revision: the record names ' + rev + ', and make promote would move traffic to ' + s.cand + ' (.candidate-revision). The gate judged ' + rev + '; make gate judges ' + s.cand); } }
  m.green = r.verdict === 'pass' && r.eval_exit === 0;
  if (!m.green) { why.push('red: the gate judged ' + rev + ' red (' + (r.blocked.join('; ') || 'eval exit ' + r.eval_exit) + ')'); }
  if (s.report === 'deleted') { m.present = false; why.push('the report ' + r.report + ' is missing, so the record cannot be checked against it'); }
  else {
    m.present = true; m.hash = D.hash[s.rows][s.report] === r.report_sha256;
    if (!m.hash) { why.push('the report ' + r.report + " changed after the gate: its sha256 is not the record's"); }
    else { var bl = D.blocked[s.rows]; m.agrees = !(r.verdict === 'pass' && bl.length); if (!m.agrees) { why.push('the record says pass, and its report does not: ' + bl.join('; ')); } }
  }
  if (s.age < -D.skew) { m.time = false; why.push("the record's time, " + r.finished + ', is in the future: it was not written by make gate on this clock'); }
  else if (s.age > D.maxh * 3600) { m.time = false; why.push('stale: the gate finished ' + hours(s.age) + ' hours ago (' + r.finished + '), and a verdict holds for ' + D.maxh + ": the lane's documents, rosters and the model's answers may have moved since. make gate again"); }
  else { m.time = true; }
  var changed = D.rules.filter(function(f){ return s.rules.indexOf(f) >= 0; });
  m.rules = !changed.length;
  if (changed.length) { why.push('stale: ' + changed.join(', ') + " changed since the gate, which judged by other rules than this checkout's. make gate again"); }
  return {why: why, m: m};
}
function lane(r, s){
  var why = [], m = {}, rev = r.revision, f = D.revs[rev], digest = s.image === 'other' ? D.other : f.digest;
  m.tag = !(s.tag && s.tag !== rev);
  if (!m.tag) { why.push('the candidate tag is on ' + s.tag + ', not on ' + rev + ': a newer candidate superseded the one the gate judged (make promote refuses this too)'); }
  m.facts = digest === r.digest && f.sha === r.git_sha;
  if (!m.facts) { why.push(rev + ' is not what the gate judged: Cloud Run says ' + digest + ' with GIT_SHA ' + f.sha + ', the record ' + r.digest + ' with GIT_SHA ' + r.git_sha); }
  m.ready = !!s.ready;
  if (!m.ready) { why.push(rev + ' is not Ready'); }
  return {why: why, m: m};
}
function check(s){
  var head = 'REFUSED: the gate record evals/reports/gate.json does not let make promote move traffic:';
  if (s.record === 'missing') { return {code: 1, lane: false, f: null, l: null, lines: [head, '  - there is no gate record at evals/reports/gate.json: make gate judges the candidate and writes it']}; }
  var r = record(s), f = files(r, s), why = f.why, read = false, l = null;
  if (!why.length) { read = true; l = lane(r, s); why = l.why; }
  if (why.length) { return {code: 1, lane: read, f: f.m, l: l && l.m, lines: [head].concat(why.map(function(w){ return '  - ' + w; }))}; }
  return {code: 0, lane: true, f: f.m, l: l.m, lines: [
    'gate record evals/reports/gate.json: ' + r.revision + ' passed at ' + r.finished + ', ' + hours(s.age) + ' hours ago',
    '  digest  ' + r.digest + '  GIT_SHA ' + r.git_sha,
    '  report  ' + r.report + '  sha256 ' + r.report_sha256,
    "  .candidate-revision names it and the candidate tag is not on another revision; judged by this checkout's " + D.rules.join(', ')]};
}
window.__gk = {check: check};
var root = document.getElementById('gk'); if (!root) { return; }
var el = {};
['rev', 'rows', 'verdict', 'age', 'cand', 'report', 'tag', 'image', 'ready'].forEach(function(k){ el[k] = document.getElementById('gk-' + k); });
var boxes = Array.prototype.slice.call(root.querySelectorAll('input[data-rule]'));
var btns = Array.prototype.slice.call(root.querySelectorAll('.gk-pre button'));
var out = document.getElementById('gk-out');
function node(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
function now(){
  var h = parseFloat(el.age.value);
  return {record: 'present', region: D.lane.region, rev: el.rev.value, rows: el.rows.value, verdict: el.verdict.value,
          age: Math.round((isFinite(h) ? h : 0) * 3600), cand: el.cand.value, report: el.report.value,
          rules: boxes.filter(function(b){ return b.checked; }).map(function(b){ return b.getAttribute('data-rule'); }),
          tag: el.tag.value, image: el.image.value, ready: el.ready.checked};
}
function render(){
  var s = now(), res = check(s);
  out.textContent = '';
  out.appendChild(node('p', 'gk-v ' + (res.code ? 'no' : 'ok'), res.code ? D.say.refused : D.say.passed.replace('{rev}', s.cand)));
  out.appendChild(node('div', 'gk-term', res.lines.join('\n')));
  var list = node('ul', 'gk-checks'), group = '';
  D.checks.forEach(function(c){
    if (c.g !== group) { group = c.g; list.appendChild(node('li', 'gk-h', c.g === 'f' ? D.say.files : D.say.lane)); }
    var marks = c.g === 'f' ? res.f : (res.lane ? res.l : null), v = marks ? marks[c.k] : undefined;
    var st = v === true ? 'ok' : (v === false ? 'no' : 'skip'), li = node('li', st);
    li.appendChild(node('b', '', st === 'ok' ? '✓' : (st === 'no' ? '✗' : '·')));
    li.appendChild(node('span', '', c.t + (st === 'skip' ? D.say.skipped : '')));
    list.appendChild(li);
  });
  out.appendChild(list);
}
function unpress(){ btns.forEach(function(b){ b.setAttribute('aria-pressed', 'false'); }); }
function preset(b){
  var p = D.presets[b.getAttribute('data-p')];
  ['rev', 'rows', 'verdict', 'cand', 'report', 'tag', 'image'].forEach(function(k){ el[k].value = p[k]; });
  el.age.value = String(p.age); el.ready.checked = p.ready;
  boxes.forEach(function(x){ x.checked = p.rules.indexOf(x.getAttribute('data-rule')) >= 0; });
  btns.forEach(function(x){ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
  render();
}
btns.forEach(function(b){ b.addEventListener('click', function(){ preset(b); }); });
el.rows.addEventListener('change', function(){ el.verdict.value = el.rows.value === 'red' ? 'fail' : 'pass'; unpress(); render(); });
['rev', 'verdict', 'cand', 'report', 'tag', 'image'].forEach(function(k){ el[k].addEventListener('change', function(){ unpress(); render(); }); });
el.age.addEventListener('input', function(){ unpress(); render(); });
el.ready.addEventListener('change', function(){ unpress(); render(); });
boxes.forEach(function(b){ b.addEventListener('change', function(){ unpress(); render(); }); });
preset(btns[0]);"""
GK_JS = GK_JS.replace("__DATA__", json.dumps(GK_DATA, ensure_ascii=False, separators=(",", ":")))
JS = "<script>\n(function(){\n'use strict';\n" + GK_JS.replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS and "<tr" not in JS and "—" not in JS and "–" not in JS and SP_PROJECT not in JS

# node runs the panel's check() on every preset and on seeded random states; each must be release.py's gate-check
rng = random.Random(1102)
AGE_POOL = [0, 59, 60, 299, 300, 301, -1, -299, -300, -301, -360, -3600, 540, 900, 2700, 3600, 7200, 85500, 86399,
            86400, 86401, 87300, 89100, 90000, 172800, 259200]
CHOICES = {"rev": [CAND, NEWER, SERVING], "rows": ["green", "red"], "verdict": ["pass", "fail"],
           "cand": [CAND, NEWER, SERVING, ""], "report": ["written", "edited", "deleted"], "tag": [CAND, NEWER, ""],
           "image": ["same", "other"], "ready": [True, False], "region": [REGION, "us-central1"],
           "record": ["present", "missing"]}
STATES = list(PRESET_STATES.values()) + [s for _, s in TABLE_CASES] + [state(age=a) for a in AGE_POOL]
for _ in range(300):
    s = dict(DEF)
    for key, options in CHOICES.items():
        if rng.random() < (0.03 if key == "record" else 0.1 if key == "region" else 0.35):
            s[key] = rng.choice(options)
    if rng.random() < 0.35:
        s["age"] = rng.choice(AGE_POOL) if rng.random() < 0.6 else rng.randint(-7200, 300000)
    s["rules"] = [rel for rel in RULES if rng.random() < 0.08]
    STATES.append(s)
NODE = ("var window = {}, document = {getElementById: function(){ return null; }};\n"
        "(new Function('window', 'document', " + json.dumps(GK_JS) + "))(window, document);\n"
        "var C = " + json.dumps(STATES) + ";\n"
        "process.stdout.write(JSON.stringify(C.map(function(s){ var r = window.__gk.check(s); return [r.code, r.lines, r.lane]; })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
N_LANE_READ = N_PASS = 0
for s, got in zip(STATES, json.loads(node.stdout)):
    want = py_check(s)
    assert (got[0], got[1], got[2]) == (want[0], want[1], want[2]), (s, got, want)
    N_LANE_READ += want[2]
    N_PASS += want[0] == 0
N_CASES = len(STATES)
assert N_LANE_READ > 60 and N_PASS > 20, (N_LANE_READ, N_PASS)          # the random states reach the lane and the pass
CHECKER.close()


def opt(value: str, label: str, selected: bool = False) -> str:
    """One <option>."""
    return f'<option value="{html.escape(value)}"' + (" selected" if selected else "") + f">{html.escape(label)}</option>"


def select(key: str, label: str, options: list, default: str) -> str:
    """A labelled <select> for the panel."""
    return (f'<label for="gk-{key}">{html.escape(label)}<select id="gk-{key}">'
            + "".join(opt(v, t, v == default) for v, t in options) + "</select></label>\n")


GK_PANEL = (
    '<div class="gk-pre" role="group" aria-label="Cases to try">'
    + "".join(f'<button type="button" data-p="{k}" aria-pressed="{"true" if i == 0 else "false"}">{html.escape(t)}</button>'
              for i, (k, t, _) in enumerate(PRESETS)) + "</div>\n"
    + '<div class="gk-in">\n<fieldset><legend>The record: gate.json</legend>\n'
    + select("rev", "revision", [(n, REV_LABEL[n]) for n in (CAND, NEWER, SERVING)], CAND)
    + select("rows", "what the rows said (the report)", [("green", "every threshold met"), ("red", f"red: {BLOCKED['red'][0]}")], "green")
    + select("verdict", "the record's verdict", [("pass", "pass (eval exit 0)"), ("fail", "fail (eval exit 1)")], "pass")
    + '<label for="gk-age">finished, hours ago<input id="gk-age" type="number" inputmode="decimal" step="0.1" value="2"></label>\n'
    + "</fieldset>\n<fieldset><legend>This checkout</legend>\n"
    + select("cand", ".candidate-revision names", [(n, REV_LABEL[n]) for n in (CAND, NEWER, SERVING)] + [("", "(no file)")], CAND)
    + select("report", "the report", [("written", "as make gate wrote it"), ("edited", "edited after the gate (same verdict, new bytes)"),
                                     ("deleted", "deleted")], "written")
    + '<p class="gk-sub">changed since the gate:</p>\n'
    + "".join(f'<label class="gk-box"><input type="checkbox" data-rule="{rel}">{rel}</label>\n' for rel in RULES)
    + "</fieldset>\n<fieldset><legend>The lane: read last</legend>\n"
    + select("tag", "the candidate tag is on", [(CAND, CAND), (NEWER, REV_LABEL[NEWER]), ("", "no revision (tag removed)")], CAND)
    + select("image", "the record's revision runs", [("same", "the image the gate judged"), ("other", "another image")], "same")
    + '<label class="gk-box"><input type="checkbox" id="gk-ready" checked>the revision is Ready</label>\n'
    + "</fieldset>\n</div>\n<div id=\"gk-out\" aria-live=\"polite\"></div>\n")

# ================================================================== the cells, and what each prints
# Each cell sits between its own blank lines and is stripped of them; triple single quotes, because the Python cells
# carry docstrings.
CELLS = {
    "ci": r'''
GH_REPO="$(python -c 'import json; print(json.load(open("terraform/runbook-project.auto.tfvars.json"))["github_repository"])')"
RUN="$(gh run list --repo "$GH_REPO" --workflow documind-cd.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId')"
JOB="$(gh run view "$RUN" --repo "$GH_REPO" --json jobs --jq '.jobs[] | select(.name == "release-candidate") | .databaseId')"
echo "run $RUN, job release-candidate $JOB"
gh run view --job "$JOB" --repo "$GH_REPO" --log \
  | grep -E '>> candidate revision: |candidate /version git_sha=[^$]|== eval gate: LIVE ==| rows \(|\[(PASS|FAIL)\]|All thresholds met|Blocked:' \
  | sed -E 's/^[^\t]*\t([^\t]*)\t[^ ]* /\1: /'
''',
    "tests": r'''
python commands/tests/test_release_gate.py
''',
    "record": r'''
make record-candidate PROJECT="$PROJECT" REGION="$REGION"
python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]
svc = json.loads(subprocess.run(["gcloud", "run", "services", "describe", "documind-api", f"--project={P}", f"--region={R}",
                                 "--format=json"], capture_output=True, text=True, check=True).stdout)
traffic = svc["status"]["traffic"]
for t in traffic:
    print(f"  {t.get('percent', 0):>3}%  {t.get('revisionName')}  tag {t.get('tag', '-')}")
named = open(".candidate-revision", encoding="utf-8").read().strip()
tagged = next((t.get("revisionName") for t in traffic if t.get("tag") == "candidate"), None)
print(f".candidate-revision names {named}; the candidate tag is on {tagged or 'no revision'}: "
      + ("the same revision" if named == tagged else "NOT the same, and make gate will refuse"))
PY
''',
    "audience": r'''
python - <<'PY'
import json, os, re, subprocess, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, N, R = os.environ["PROJECT"], os.environ["NUMBER"], os.environ["REGION"]
CANONICAL = f"https://documind-api-{N}.{R}.run.app"           # SELF_URL: the audience the API checks
TAG = f"https://candidate---documind-api-{N}.{R}.run.app"     # the URL make gate calls


def token(audience):
    """An ID token for this audience as documind-ui-sa, minted as tok() and make gate mint theirs."""
    return subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={audience}",
                           f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                          capture_output=True, text=True, check=True).stdout.strip()


def get(path, tok):
    """GET one path of the tag URL with this token: (the HTTP status, the body as text)."""
    req = urllib.request.Request(TAG + path, headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


for name, audience in (("the canonical URL", CANONICAL), ("the tag URL", TAG)):
    tok = token(audience)
    print(f"a token for {name}, {audience}")
    for path in ("/version", "/v1/sources?tenant_id=acme"):
        status, body = get(path, tok)
        try:
            doc = json.loads(body)
        except ValueError:
            doc = None
        if status == 200 and path == "/version":
            said = f"git_sha {doc['git_sha']}, {doc['generator_model']}, {doc['prompt']}"
        elif status == 200:
            said = f"{len(doc['sources'])} sources of {doc['tenant_id']}"
        else:
            said = (doc.get("detail") if isinstance(doc, dict) else None) or " ".join(re.sub(r"<[^>]+>", " ", body).split())[:100]
        print(f"  GET {path:27} HTTP {status}  {said}")
PY
''',
    "gate": r'''
make gate PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
''',
    "lane": r'''
python - <<'PY'
import hashlib, json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
import google.auth
from google.auth.transport.requests import AuthorizedSession

P, R = os.environ["PROJECT"], os.environ["REGION"]
creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
run = AuthorizedSession(creds.with_quota_project(P) if hasattr(creds, "with_quota_project") else creds)
V1 = f"https://{R}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/{P}"


def read(path):
    """One read of the Cloud Run Admin API's v1 resources, as JSON; a failure says which read and why."""
    r = run.get(f"{V1}/{path}", timeout=30)
    if r.status_code != 200:
        raise SystemExit(f"GET {path}: HTTP {r.status_code} {r.text[:200]}")
    return r.json()


def sha256(path):
    """A file's sha256, as make gate and gate-check compute it."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def short(value):
    """A digest or a sha256, cut to what an eye compares: the image's name and twelve hex digits."""
    text = str(value)
    if "@sha256:" in text:
        return text.rsplit("/", 1)[-1][:23] + "..."
    return text[:12] + "..." if len(text) == 64 else text


rec = json.load(open("evals/reports/gate.json", encoding="utf-8"))
rev = read(f"revisions/{rec['revision']}")
svc = read("services/documind-api")
env = {e["name"]: e.get("value") for e in rev["spec"]["containers"][0].get("env", [])}
ready = next((c["status"] for c in rev["status"].get("conditions", []) if c["type"] == "Ready"), "unknown")
tagged = next((t.get("revisionName") for t in svc["status"]["traffic"] if t.get("tag") == "candidate"), "no revision")
print(f"{rec['revision']}: {rec['verdict']}, eval exit {rec['eval_exit']}, {rec['rows']} rows, finished {rec['finished']}")
rows = [("named by .candidate-revision", rec["revision"], open(".candidate-revision", encoding="utf-8").read().strip()),
        ("the candidate tag routes to", rec["revision"], tagged),
        ("image digest", rec["digest"], rev["status"].get("imageDigest")),
        ("GIT_SHA", rec["git_sha"], env.get("GIT_SHA")),
        ("Ready, as the gate required", "True", ready),
        ("report sha256", rec["report_sha256"], sha256(rec["report"]))]
rows += [(f"{name} sha256", digest, sha256(name)) for name, digest in rec["rules"].items()]
for what, recorded, now in rows:
    same = recorded == now
    print(f"  {'same' if same else 'DIFFERS':8}{what:31}{short(recorded)}" + ("" if same else f"  now {short(now)}"))
PY
''',
    "gatecheck": r'''
python commands/release.py gate-check --project "$PROJECT" --region "$REGION"; echo "exit $?"
''',
    "scratch": r'''
python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]
svc = json.loads(subprocess.run(["gcloud", "run", "services", "describe", "documind-api", f"--project={P}", f"--region={R}",
                                 "--format=json"], capture_output=True, text=True, check=True).stdout)
serving = max((t for t in svc["status"]["traffic"] if t.get("percent")), key=lambda t: t["percent"])["revisionName"]
rec = json.load(open("evals/reports/gate.json", encoding="utf-8"))
if serving == rec["revision"]:
    raise SystemExit(f"{serving} already serves: there is no other revision to name")
with open("evals/reports/scratch-gate.json", "w", encoding="utf-8") as f:
    json.dump({**rec, "revision": serving}, f, indent=1)
print(f"evals/reports/scratch-gate.json: your record, with {rec['revision']} replaced by {serving}, the revision serving now")
PY
make promote-gated PROJECT="$PROJECT" REGION="$REGION" GATE_FILE=evals/reports/scratch-gate.json; echo "exit $?"
rm -f evals/reports/scratch-gate.json
python commands/release.py gate-check --project "$PROJECT" --region "$REGION" > /dev/null; echo "your record: gate-check exit $?"
''',
}
CELLS = {k: v.strip("\n") for k, v in CELLS.items()}
CELL_LABELS = {
    "ci": "run in the operator shell, in the kit, if lesson 11.1's dispatch made your candidate (GitHub reads; writes nothing)",
    "tests": "run in the operator shell, in the kit (stand-ins only: no Google call, no cost)",
    "record": "run in the operator shell, in the kit (one describe; writes .candidate-revision)",
    "audience": "run in the operator shell, in the kit (two tokens, four GETs, no model call)",
    "gate": "run in the operator shell, in the kit (every golden row, about ten minutes)",
    "lane": "run in the operator shell, in the kit (two Cloud Run Admin API reads and your files; writes nothing)",
    "gatecheck": "run in the operator shell, in the kit (the check alone: nothing moves)",
    "scratch": "run in the operator shell, in the kit (a copy of your record, refused; it is deleted afterwards)",
}
assert set(CELL_LABELS) == set(CELLS)
for name, cell in CELLS.items():                            # every function a cell defines carries a one-line docstring
    for m in re.finditer(r"^def (\w+)\(.*\):\n( +)(.*)$", cell, re.M):
        assert m.group(3).startswith('"""') and m.group(3).endswith('"""'), (name, m.group(1))
    if "<<'PY'" in cell:
        assert 'warnings.filterwarnings("ignore", category=UserWarning)' in cell and cell.count("\nPY") >= 1, name
for name in ("ci", "gate", "gatecheck"):                    # the run list carries the bash cells character for character
    assert f"```bash\n{CELLS[name]}\n```" in RUN_LIST, f"RUN_LIST.md's copy of the {name} cell differs from the page's"
assert "--to-revisions" not in "".join(CELLS.values()) and "update-traffic" not in "".join(CELLS.values())

# the four Python cells, each run against stand-ins before any lane runs it: their code works before it is recorded
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONIOENCODING": "utf-8",
         "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "PROJECT": SP_PROJECT, "REGION": REGION, "NUMBER": SP_NUMBER}


def heredoc_of(cell: str) -> str:
    """The Python between a cell's PY markers."""
    return cell.split("<<'PY'\n", 1)[1].split("\nPY", 1)[0]


def run_cell(code: str, cwd: Path, prelude: str) -> str:
    """A cell's Python with stand-ins installed first, in cwd: what it printed (it must exit 0 and print no error)."""
    r = subprocess.run([sys.executable, "-"], input=prelude + "\n" + code, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", env=QUIET)
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stderr[-1500:], r.stdout[-400:])
    return r.stdout


def service_doc(world: dict) -> dict:
    """documind-api as gcloud run services describe --format=json prints it, from the kit test's stand-in."""
    lane = StandInLane()
    try:
        lane.set_world(world)
        code, out, _ = lane.fake.handle("gcloud", ["run", "services", "describe", "documind-api", "--region", REGION,
                                                   "--project", SP_PROJECT, "--format", "json"])
        assert code == 0
        return json.loads(out)
    finally:
        lane.close()


def revision_doc(world: dict, name: str) -> dict:
    """One revision as gcloud run revisions describe --format=json prints it, from the kit test's stand-in."""
    lane = StandInLane()
    try:
        lane.set_world(world)
        code, out, _ = lane.fake.handle("gcloud", ["run", "revisions", "describe", name, "--region", REGION,
                                                   "--project", SP_PROJECT, "--format", "json"])
        assert code == 0
        return json.loads(out)
    finally:
        lane.close()


SUBPROCESS_STANDIN = r'''import json as _json, sys as _sys, types as _types
class _Completed:
    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, "", 0
_SERVICE = _json.loads(%r)
def _run(cmd, **kw):
    if cmd[1:4] == ["run", "services", "describe"]:
        return _Completed(_json.dumps(_SERVICE))
    if cmd[1:3] == ["auth", "print-identity-token"]:
        return _Completed("token." + next(a.split("=", 1)[1] for a in cmd if a.startswith("--audiences=")) + "\n")
    raise SystemExit("unexpected command: " + " ".join(cmd))
_fake = _types.ModuleType("subprocess"); _fake.run = _run; _sys.modules["subprocess"] = _fake
'''
URLOPEN_STANDIN = r'''import io as _io, json as _json, urllib.error as _uerr, urllib.request as _ureq
_CANONICAL, _VERSION = %r, _json.loads(%r)
class _Resp(_io.BytesIO):
    status = 200
    def __enter__(self): return self
    def __exit__(self, *a): return False
def _urlopen(req, timeout=None):
    token = req.get_header("Authorization").split(" ", 1)[1]
    if req.full_url.endswith("/version"):
        return _Resp(_json.dumps(_VERSION).encode())
    if token == "token." + _CANONICAL:
        return _Resp(_json.dumps({"tenant_id": "acme", "sources": [{"name": "a"}, {"name": "b"}]}).encode())
    raise _uerr.HTTPError(req.full_url, 401, "Unauthorized", {}, _io.BytesIO(b'{"detail": "invalid bearer token: ValueError"}'))
_ureq.urlopen = _urlopen
'''
GOOGLE_STANDIN = r'''import json as _json, sys as _sys, types as _types
_DOCS = _json.loads(%r)
class _Creds:
    def with_quota_project(self, p): return self
class _Resp:
    def __init__(self, doc): self.status_code, self._doc, self.text = 200, doc, _json.dumps(doc)
    def json(self): return self._doc
class _Session:
    def __init__(self, creds): pass
    def get(self, url, timeout=None):
        return _Resp(_DOCS[url.split("/namespaces/", 1)[1].split("/", 1)[1]])
_g, _ga, _gt, _gtr = (_types.ModuleType(n) for n in ("google", "google.auth", "google.auth.transport", "google.auth.transport.requests"))
_ga.default = lambda scopes=None: (_Creds(), "stand-in")
_gtr.AuthorizedSession = _Session
_g.auth, _ga.transport, _gt.requests = _ga, _gt, _gtr
_sys.modules.update({"google": _g, "google.auth": _ga, "google.auth.transport": _gt, "google.auth.transport.requests": _gtr})
'''
CELL_HOME = Path(tempfile.mkdtemp(prefix="lesson112_cells_"))
try:
    for rel in RULES:                                       # a kit as make gate left it: the rules, the record, the report
        (CELL_HOME / rel).parent.mkdir(parents=True, exist_ok=True)
        (CELL_HOME / rel).write_bytes(PRISTINE[rel])
    (CELL_HOME / "evals" / "reports").mkdir(parents=True, exist_ok=True)
    (CELL_HOME / "evals" / "reports" / "gate.json").write_bytes(G_REC_TEXT.encode("utf-8"))
    (CELL_HOME / G_REC["report"]).write_bytes(G_BODY)
    (CELL_HOME / ".candidate-revision").write_bytes((CAND + "\n").encode("utf-8"))
    svc = service_doc(WORLD)
    out_record = run_cell(heredoc_of(CELLS["record"]), CELL_HOME, SUBPROCESS_STANDIN % json.dumps(svc))
    assert out_record.splitlines() == [f"  100%  {SERVING}  tag -", f"    0%  {CAND}  tag candidate",
                                       f".candidate-revision names {CAND}; the candidate tag is on {CAND}: the same revision"], out_record
    version = {"model_backend": "vertex", "generator_model": GENERATOR, "prompt": PROMPT, "git_sha": SHA[CAND]}
    out_aud = run_cell(heredoc_of(CELLS["audience"]), CELL_HOME,
                       SUBPROCESS_STANDIN % json.dumps(svc) + URLOPEN_STANDIN % (AUDIENCE, json.dumps(version)))
    assert out_aud.splitlines() == [
        f"a token for the canonical URL, {AUDIENCE}",
        f"  GET {'/version':27} HTTP 200  git_sha {SHA[CAND]}, {GENERATOR}, {PROMPT}",
        f"  GET {'/v1/sources?tenant_id=acme':27} HTTP 200  2 sources of acme",
        f"a token for the tag URL, {TAG_URL}",
        f"  GET {'/version':27} HTTP 200  git_sha {SHA[CAND]}, {GENERATOR}, {PROMPT}",
        f"  GET {'/v1/sources?tenant_id=acme':27} HTTP 401  invalid bearer token: ValueError"], out_aud
    docs = {f"revisions/{CAND}": revision_doc(WORLD, CAND), "services/documind-api": svc}
    out_lane = run_cell(heredoc_of(CELLS["lane"]), CELL_HOME, GOOGLE_STANDIN % json.dumps(docs))
    lane_lines = out_lane.splitlines()
    assert lane_lines[0] == f"{CAND}: pass, eval exit 0, {G_REC['rows']} rows, finished {release.stamp(FINISH)}", lane_lines
    assert len(lane_lines) == 1 + 6 + len(RULES) and all(line.startswith("  same    ") for line in lane_lines[1:]), out_lane
    world_moved = copy.deepcopy(WORLD)
    world_moved["revisions"][CAND]["digest"] = D_OTHER          # and a revision that is not what was judged says so
    out_diff = run_cell(heredoc_of(CELLS["lane"]), CELL_HOME, GOOGLE_STANDIN % json.dumps(
        {**docs, f"revisions/{CAND}": revision_doc(world_moved, CAND)}))
    assert [line.split()[0] for line in out_diff.splitlines()[1:]].count("DIFFERS") == 1, out_diff
    out_scratch = run_cell(heredoc_of(CELLS["scratch"]), CELL_HOME, SUBPROCESS_STANDIN % json.dumps(svc))
    scratch = json.loads((CELL_HOME / "evals" / "reports" / "scratch-gate.json").read_text(encoding="utf-8"))
    assert scratch == {**G_REC, "revision": SERVING}, scratch
    assert out_scratch == f"evals/reports/scratch-gate.json: your record, with {CAND} replaced by {SERVING}, the revision serving now\n"
finally:
    shutil.rmtree(CELL_HOME, ignore_errors=True)

# the Change-it, through make's own recipe order: gate-check on the copy refuses, so promote never starts; yours passes
lane = StandInLane()
try:
    (lane.kit / ".candidate-revision").write_text(CAND + "\n", encoding="utf-8")
    reports = lane.kit / "evals" / "reports"
    reports.mkdir(parents=True)
    (reports / "gate.json").write_text(G_REC_TEXT, encoding="utf-8")
    (lane.kit / G_REC["report"]).write_bytes(G_BODY)
    (reports / "scratch-gate.json").write_text(json.dumps({**G_REC, "revision": SERVING}, indent=1), encoding="utf-8")
    lane.clock = NOW
    code_s, out_s, err_s = lane.main("gate-check", "--project", SP_PROJECT, "--region", REGION,
                                     "--gate-file", str(reports / "scratch-gate.json"))
    calls_s = lane.calls()
    code_r, out_r, err_r = lane.main("gate-check", "--project", SP_PROJECT, "--region", REGION)
finally:
    lane.close()
assert (code_s, out_s, code_r, err_r) == (release.REFUSED, "", 0, ""), (code_s, out_s, err_s, code_r, err_r)
assert not calls_s                                           # refused from the files: the lane was not read
assert err_s.splitlines() == [
    "REFUSED: the gate record evals/reports/scratch-gate.json does not let make promote move traffic:",
    f"  - another revision: the record names {SERVING}, and make promote would move traffic to {CAND} (.candidate-revision). "
    f"The gate judged {SERVING}; make gate judges {CAND}"], err_s
OUT_SCRATCH = (out_scratch + placeholders(err_s) + MAKE_REFUSED + "\nexit 2\nyour record: gate-check exit 0")

# ================================================================== what the windows show
RECORDED = {k: pb.recorded(LESSON, f"{k}.txt") for k in
            ("ci_gate", "record_candidate", "audience", "gate", "record_vs_lane", "gate_check")}
LANE_LABEL = "(the author's lane: your revision names, commit, digests, hashes and times are yours)"
STAND_IN = "release.py run when this page was built, against the kit test's stand-in lane"
OUTS = {
    "ci": ("(the author's lane and fork, lesson 11.1's run: your run, revision and commit are yours)", RECORDED["ci_gate"]),
    "tests": ("shape (the kit's own tests on your machine: the time is yours)",
              "." * N_TESTS + "\n" + "-" * 70 + f"\nRan {N_TESTS} tests in Ns\n\nOK"),
    "sgate": (f"({STAND_IN}: the names, commit and hashes are the stand-in's; on your lane run_eval.py prints its rows "
              "between the two >> blocks)", OUT_SGATE),
    "srecord": (f"(evals/reports/gate.json as the stand-in gate wrote it: {N_RECORD_KEYS} fields, indent 1)", OUT_SRECORD),
    "sred": (f"({STAND_IN}, with a stand-in report that misses one threshold)", OUT_SRED),
    "scheck": (f"({STAND_IN}, two hours after the gate)", OUT_SCHECK),
    "record": (LANE_LABEL, RECORDED["record_candidate"]),
    "audience": (LANE_LABEL, RECORDED["audience"]),
    "gate": ("(the author's lane: the full gate on lesson 11.1's candidate; your rates, rows, names and times are yours)",
             RECORDED["gate"]),
    "lane": (LANE_LABEL, RECORDED["record_vs_lane"]),
    "gatecheck": (LANE_LABEL, RECORDED["gate_check"]),
    "scratch": (f"(the cell's lines and release.py's, run when this page was built against the kit test's stand-in lane; "
                "make's line as GNU make 4 prints it; your names are yours)", OUT_SCRATCH),
}


def bash_window(label: str, code: str) -> str:
    """A command window: the label says where to run it, the copy button copies it."""
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    """What a cell prints: read only."""
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})


# ================================================================== the tables the prose carries
def tw(head: list, rows: list) -> str:
    """A table that turns into cards on a phone: every cell after the first carries its column's name."""
    out = ['<div class="tw"><div class="tw-scroll" tabindex="0"><table class="comp-table">\n<thead><tr>'
           + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead>\n<tbody>\n"]
    for r in rows:
        out.append("<tr><td>" + r[0] + "</td>" + "".join(f'<td data-label="{html.escape(h)}">{c}</td>' for h, c in zip(head[1:], r[1:]))
                   + "</tr>\n")
    out.append('</tbody></table></div><span class="scroll-hint">&#8596; SWIPE</span></div>\n')
    return "".join(out)


code = lambda s: f"<code>{html.escape(s)}</code>"  # noqa: E731
STOPS_TABLE = tw(["What happened", "Rows asked", "An earlier record", "What make gate printed (exit 2)"], [
    [label, "yes" if asked else "no", "kept" if kept else "gone", code(stop)] for label, asked, kept, stop in STOPS])
CHECKS_TABLE = tw(["What changed", "The lane read", "What gate-check printed after its REFUSED line (exit 1)"], [
    [label, "yes" if read else "no", "<br>".join(code(r) for r in reasons)] for label, read, reasons in CHECKS_TABLE_ROWS])
COST_TABLE = tw(["Run", "What it costs", "On your lane"], [
    ["The console, and lesson 11.1's run read with <code>gh</code>", "reads", "Rs 0"],
    [f"{code('make record-candidate')} and the traffic read", "one describe", "Rs 0"],
    ["The audience calls", "two token mints and four GETs; no model call", "Rs 0"],
    [code("make gate"), f"{N_ROWS} answers at the model's rate; the outsider's {N_ISO} requests are refused at the roster "
     "before any model call", f"about Rs {RS_GATE} at the course's typical answer of 2,000 tokens in and 300 out "
     f"(Rs {RS_ANSWER:.2f} each); {code('make usage')} prints yours"],
    ["The record read back, <code>gate-check</code>, the copy refused", "Cloud Run reads and your files", "Rs 0"],
    ["The kit's tests", "stand-ins only", "Rs 0"],
    ["The candidate revision", "no traffic, and the API's floor is zero instances", "Rs 0 while nobody calls it"],
])

# ================================================================== numbers for the prose
STATS = {
    "N_ROWS": str(N_ROWS), "N_THRESHOLDS": str(N_THRESHOLDS), "MAXH": MAXH_S, "SKEW_MIN_W": WORDS[SKEW_S // 60],
    "N_RULES_W": WORDS[len(RULES)], "N_TESTS": str(N_TESTS), "N_CASES": str(N_CASES), "N_PRESETS": str(len(PRESETS)),
    "N_RECORD_KEYS": str(N_RECORD_KEYS), "N_FIELDS": str(len(release.RECORD_FIELDS)), "RS_GATE": str(RS_GATE),
    "CAND": CAND, "GATE_FILE": GATE_FILE_DEFAULT, "CHECK_LINE": str(CHECK_LINE),
    "RULE_FILES": ", ".join(code(r) for r in RULES), "GK_PANEL": GK_PANEL,
    "STOPS_TABLE": STOPS_TABLE, "CHECKS_TABLE": CHECKS_TABLE, "COST_TABLE": COST_TABLE,
    "NEXT_TITLE": html.escape(NEXT), "TITLE": html.escape(NAME),
}


def subst(text: str) -> str:
    """Every %%NAME%% in a part: a window, a table or a number computed above."""
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {N_ROWS} rows, {N_THRESHOLDS} thresholds, {len(RULES)} rule files, {MAXH_S} hours | the stand-in gate: green "
      f"and red records, {len(STOPS)} refusals ({sum(not s[1] for s in STOPS)} before the rows) | gate-check: "
      f"{len(CHECKS_TABLE_ROWS)} refusals; the panel agrees with release.py on {N_CASES} states (node; {N_LANE_READ} read "
      f"the lane, {N_PASS} pass) | four Python cells run against stand-ins | a gate: about Rs {RS_GATE}")
