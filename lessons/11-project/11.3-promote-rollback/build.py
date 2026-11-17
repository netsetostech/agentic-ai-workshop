"""Build lesson 11.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Promote, roll back and repair a controlled failure. make promote-gated promotes lesson 11.2's gated candidate. A
candidate with a mistyped model (make candidate GENERATOR_MODEL=gemini-3.6-flsh) is judged red by make gate and refused
by make promote-gated, and plain make promote, which reads no record, moves traffic to it anyway. make smoke-deployed
(commands/release.py smoke-deployed) runs smoke-all's smokes whose Cloud Run services are deployed, and goes red; make
incident (release.py incident) reads the lane and the records and names make rollback. time make rollback moves the
traffic back, and the template still holds the typo, so make incident names the repair: make candidate with what
serves, make gate, make promote-gated. Then make smoke-deployed is green and make incident exits 0: the gated state.

Computed here, offline, from the kit:
  - the fifteen commands, run through the Makefile's own recipes by the kit test's MiniMake (commands/tests/
    test_release_repair.py's, built on test_release_gate.py's) in sh, against the kit test's stand-in gcloud, curl and
    make on PATH, in a copy of the kit's release files. release.py runs as make runs it, through a launcher that holds
    its clock, its GET /version and its rows at the seams the kit's InProcess tests patch. The stand-in's rows fail on
    a revision whose GENERATOR_MODEL Vertex AI does not serve and pass on any other: the rule its smokes follow;
  - the stepper in step 1: the lane after each command, and make incident's verdict on it (release.py in-process, held
    equal to make incident's own output at the three steps that run it);
  - what make release-candidate would make after the rollback (the stand-in put back as it was afterwards);
  - the facts the prose states: the recipes and their line numbers, smoke-all's smokes and the services they call, make
    candidate's settings, the 500 a mistyped model becomes, the kit tests' count, and the rupees from shared/prices.py;
  - the two Python cells, each run against stand-ins.
Recorded from the author's lane with pb.recorded(): the fifteen commands in ten cells, the template read after the
rollback and the request logs read at the end (RUN_LIST.md says how). The build needs a POSIX sh (Git Bash on
Windows), as the kit test's recipe tests do; nothing it runs reaches Google Cloud.

    python pagekit/build.py 11.3
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
import re
import shlex
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

LESSON = "11.3"
NAME = MANIFEST["modules"]["11"]["lessons"][LESSON]["name"]
NEXT = MANIFEST["modules"]["11"]["lessons"]["11.4"]["name"]
title = (f"<title>Lesson 11.3 {NAME} - a forced promote of a red candidate, rolled back in seconds, and the template "
         "the rollback leaves repaired through the gate | Netsetos</title>\n")
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


REPAIR = load_file(KIT / "commands" / "tests" / "test_release_repair.py", "test_release_repair_l113")
GATE = REPAIR.gate                                 # test_release_gate.py: its stand-in, eval_report() and MiniMake
release = REPAIR.release                           # the release.py those tests patch
SH = GATE.SH
assert SH, "lesson 11.3's build runs the Makefile's recipes in a POSIX sh, as the kit test does: install one (Git Bash)"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the stepper: the fifteen commands on the stand-in lane, the lane after each, and make incident's three checks */
.cf-steps{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px;}
.cf-steps button,.cf-nav button{font:inherit;font-size:13px;line-height:1.3;text-align:left;padding:6px 11px;border:1px solid var(--border);border-radius:16px;background:var(--card);color:var(--navy);cursor:pointer;min-height:max(36px,var(--touch));-webkit-tap-highlight-color:transparent;}
.cf-steps button.no{border-color:#fca5a5;}
.cf-steps button[aria-pressed="true"]{border:2px solid var(--teal);background:var(--teal-light);color:var(--teal-dark);font-weight:700;}
.cf-steps button:active,.cf-nav button:active{transform:scale(.98);}
.cf-nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px;}
.cf-nav button:disabled{opacity:.45;cursor:default;}
.cf-head{font-family:var(--mono);font-size:13px;line-height:1.5;color:var(--navy);font-weight:700;margin:0 0 2px;overflow-wrap:anywhere;}
.cf-what{font-size:var(--small-size);color:var(--slate);margin:0 0 8px;}
.cf-v{border-radius:10px;padding:8px 12px;margin:0 0 8px;font-size:var(--small-size);line-height:1.5;font-weight:600;}
.cf-v.ok{background:#d1fae5;border:1px solid #6ee7b7;color:#065f46;}
.cf-v.no{background:#fee2e2;border:1px solid #fca5a5;color:#991b1b;}
.cf-term{font-family:var(--mono);font-size:12px;line-height:1.55;background:var(--code-bg);color:var(--code-text);border-radius:10px;padding:10px 12px;margin:0 0 8px;white-space:pre-wrap;overflow-wrap:anywhere;}
.cf-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:10px;}
.cf-box{border:1px solid var(--border);border-radius:10px;padding:8px 10px;background:var(--card);min-width:0;font-size:12.5px;line-height:1.5;}
.cf-label{font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--navy);margin:0 0 4px;}
.cf-row{font-family:var(--mono);font-size:12px;padding:3px 0;border-top:1px dashed var(--border);overflow-wrap:anywhere;}
.cf-row.live{font-weight:700;color:var(--teal-dark);}
.cf-row .bad{color:#b91c1c;font-weight:700;}
.cf-checks{list-style:none;margin:0;padding:0;}
.cf-checks li{display:grid;grid-template-columns:20px minmax(0,1fr);gap:4px;padding:3px 0;border-top:1px dashed var(--border);}
.cf-checks li.ok b{color:var(--teal-dark);}
.cf-checks li.no b,.cf-checks li.no span{color:#b91c1c;font-weight:700;}
@media (hover:hover) and (pointer:fine){.cf-steps button:hover,.cf-nav button:hover{border-color:var(--teal);}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson's two gates ask acme's golden rows, as lesson 11.2's gate did, and that gate judged its candidate "
         "with acme on the kit's own index: keep the pin for the duration, so every verdict on this page is about one "
         "lane, and put it back at the end."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head. <code>make smoke-deployed</code> asks <code>GET /version</code> as the "
         "first, and step 3 asks the UI as yourself.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)

# ================================================================== the kit, read
REL, MK_REL, GEN, MAIN = ("commands/release.py", "mk/release.mk", "services/rag-api/generator.py",
                          "services/rag-api/main.py")
MK, RMK, GEN_SRC, MAIN_SRC = kit("Makefile"), kit(MK_REL), kit(GEN), kit(MAIN)
MAKE_TEXT = GATE.make_text()                                        # the Makefile and mk/*.mk, as make reads them
recipe = lambda text, name: text[text.index(f"\n{name}:") + 1:].split("\n\n", 1)[0]   # noqa: E731

# mk/release.mk: the two new targets, and the recipe lines make names when a release.py line fails
GATE_RECIPE, PG_RECIPE = recipe(RMK, "gate").splitlines(), recipe(RMK, "promote-gated").splitlines()
SD_RECIPE, INC_RECIPE = recipe(RMK, "smoke-deployed").splitlines(), recipe(RMK, "incident").splitlines()
assert SD_RECIPE == ["smoke-deployed: guard-project",
                     "\t@$(PY) commands/release.py smoke-deployed --project $(PROJECT) --region $(REGION) --slm-region "
                     "$(SLM_REGION) --tenant $(TENANT)"], SD_RECIPE
assert INC_RECIPE == ["incident: guard-project",
                      "\t@$(PY) commands/release.py incident --project $(PROJECT) --region $(REGION) --gate-file "
                      "$(GATE_FILE) --hours $${HOURS:-24}"], INC_RECIPE
assert GATE_RECIPE[1].startswith("\t@$(PY) commands/release.py gate ") and "gate-check" in PG_RECIPE[1]
assert PG_RECIPE[2] == "\t@$(MAKE) --no-print-directory promote PROJECT=$(PROJECT) REGION=$(REGION)"
RMK_LINES = RMK.splitlines()
LINE = {"gate": RMK_LINES.index(GATE_RECIPE[1]) + 1, "promote-gated": RMK_LINES.index(PG_RECIPE[1]) + 1,
        "smoke-deployed": RMK_LINES.index(SD_RECIPE[1]) + 1, "incident": RMK_LINES.index(INC_RECIPE[1]) + 1}
assert "make rollback moves traffic and leaves\n# spec.template as the last update made it" in RMK
PHONY = MK[MK.index(".PHONY:"):MK.index("# ---------- the module files")].replace("\\", " ").split()
assert {"smoke-deployed", "incident", "promote", "rollback", "candidate", "smoke-all", "smoke"} <= set(PHONY)


def make_error(target: str, code: int) -> str:
    """The line GNU make 4 prints when a recipe line in mk/release.mk fails."""
    return f"make: *** [{MK_REL}:{LINE[target]}: {target}] Error {code}"


# the Makefile: promote and rollback move traffic by name and read no record; candidate and release-candidate update
PROMOTE, ROLLBACK, CANDIDATE, RELEASE_C = (recipe(MK, t) for t in ("promote", "rollback", "candidate",
                                                                    "release-candidate"))
assert ('echo ">> serving before the flip: $$PREV (deploy/.previous-revision - make rollback returns to it)"' in PROMOTE
        and 'echo ">> live: $$CAND"' in PROMOTE and "--to-revisions $$CAND=100" in PROMOTE)
assert "gate.json" not in PROMOTE and "release.py" not in PROMOTE              # make promote reads no gate record
assert "--to-revisions $$PREV=100" in ROLLBACK and 'echo ">> traffic on $$PREV"' in ROLLBACK
assert "services update-traffic" in ROLLBACK and "services update " not in ROLLBACK   # traffic only: no template
assert "Fifteen seconds;\n# the fastest rollback there is, because that revision never went away." in MK
assert ("gcloud run services update documind-api" in CANDIDATE and "--no-traffic --tag candidate" in CANDIDATE
        and '--update-env-vars "^|^GENERATOR_MODEL=$(GENERATOR_MODEL)|' in CANDIDATE and "record-candidate" in CANDIDATE)
assert "--update-env-vars GIT_SHA=$(GIT_SHA)" in RELEASE_C and "GENERATOR_MODEL" not in RELEASE_C
assert "# Env vars MERGE across revisions: a re-tag without GENERATOR_LOCATION removes it (F43)" in MK
GENERATOR = re.search(r"^GENERATOR_MODEL \?= (\S+)$", MK, re.M).group(1)
MODEL, TYPO = REPAIR.MODEL, REPAIR.TYPO
assert (GENERATOR, MODEL, TYPO) == ("gemini-3.6-flash", "gemini-3.6-flash", "gemini-3.6-flsh")
SETTINGS = release.candidate_settings(MAKE_TEXT)                   # what make candidate passes, with the defaults
assert SETTINGS["GENERATOR_MODEL"] == GENERATOR and "GIT_SHA" not in SETTINGS
CAND_ENV = [n for n in SETTINGS if n not in ("PROJECT", "REGION")]  # those two come from its record-candidate line
N_SETTINGS = len(CAND_ENV)
assert N_SETTINGS == 14 and CAND_ENV[-3:] == ["RETRIEVAL_BACKEND", "RAG_LOCATION", "GENERATOR_LOCATION"], CAND_ENV
assert ("$(if $(RETRIEVAL_BACKEND),|RETRIEVAL_BACKEND=$(RETRIEVAL_BACKEND)|RAG_LOCATION=$(RAG_LOCATION),)" in CANDIDATE
        and "$(if $(GENERATOR_LOCATION),,--remove-env-vars GENERATOR_LOCATION)" in CANDIDATE)

# the API: nothing checks the model's name at startup; a refused call on the default model is re-raised (a 500)
CFG = kit("services/rag-api/config.py")
assert 'generator_model: str = "gemini-3.6-flash"' in CFG and not re.search(r'field_validator\([^)]*"generator_model"', CFG)
assert "if not _exhausted_tier(e, model):\n            raise" in GEN_SRC
assert 'getattr(e, "code", None) == 429 and model != settings.generator_model' in GEN_SRC
assert '"generator_model": settings.generator_model,' in MAIN_SRC and 'def health(): return {"status": "ok"}' in MAIN_SRC
assert "generate_stream yields this list before its first token" in MAIN_SRC      # the stream's citations come first

# smoke-all's eight smokes, the services each calls, and the ones a lane without Module 9's services runs
SMOKES = list(release.SMOKES)
assert release.smoke_all_targets(MAKE_TEXT) == [t for t, _ in SMOKES] and len(SMOKES) == 8
SEVEN = list(REPAIR.SEVEN)                                         # make up's services: no gateway, no SLM
RUN_SMOKES, SKIPPED = release.choose_smokes(set(SEVEN))
assert RUN_SMOKES == REPAIR.THROUGH_THE_API and list(SKIPPED) == ["smoke-gateway", "smoke-slm"]
SLM_REGION = release.SLM_REGION_DEFAULT
assert re.search(r"^SLM_REGION \?= (\S+)$", MK, re.M).group(1) == SLM_REGION == "us-central1"
assert "the eight smokes in one run" in MK      # smoke-all's comment says eight, as its loop runs (13 October 2026)

# the kit's own tests of this lesson
TEST_SRC = kit("commands/tests/test_release_repair.py")
N_TESTS = len(re.findall(r"^    def test_\w+\(self", TEST_SRC, re.M))
N_RECIPE_TESTS = len(re.findall(r"^    def test_\w+\(self", TEST_SRC.split("class RecipeTests(Repair):", 1)[1]
                                .split("class PureTests", 1)[0], re.M))
assert N_TESTS >= 22 and N_RECIPE_TESTS == 2, (N_TESTS, N_RECIPE_TESTS)

# the rows and a gate's rupees (as lesson 11.2 computes them), and the answers one healthy smoke-deployed run asks
GOLDEN = [json.loads(line) for line in kit("evals/golden.jsonl").splitlines() if line.strip()]
N_ROWS = len(GOLDEN)
N_ISO = sum(r.get("shape") == "isolation" for r in GOLDEN)
PRICES = {}
exec(compile(kit("shared/prices.py"), "prices.py", "exec"), PRICES)
RATE_IN, RATE_OUT = PRICES["PRICES"][GENERATOR]
TYPICAL = (2000, 300)              # the course's typical answer (lessons 4.3, 4.4, 11.1, 11.2 and 11.6): 2,000 in, 300 out
RS_ANSWER = (TYPICAL[0] * RATE_IN + TYPICAL[1] * RATE_OUT) / 1_000_000 * PRICES["USD_INR"]
RS_GATE = round(RS_ANSWER * N_ROWS)
assert (PRICES["USD_INR"], RATE_IN, RATE_OUT, N_ROWS, N_ISO, RS_GATE) == (85, 1.50, 7.50, 65, 11, 29)
SMOKE_SRC = {t: kit(f"smoke/{t.replace('-', '_')}.py") for t in RUN_SMOKES}
assert SMOKE_SRC["smoke"].count('call("POST", "/v1/query", token, body=q)') == 2          # once, and again only
assert 'cache_on = ver.get("semantic_cache") == "on"' in SMOKE_SRC["smoke"]                # with the answer cache on,
assert re.search(r"^SEMANTIC_CACHE\s*\?= off$", MK, re.M)                                    # which is off by default
assert "3. retrieve(the gratuity question)   -> answerable with citations, as a roster member" in SMOKE_SRC["smoke-mcp"]
assert 'BRAINS = ("direct", "langchain", "langgraph", "adk")' in SMOKE_SRC["smoke-chat"]
assert "3. message/send (selected fixture) -> a completed task" in SMOKE_SRC["smoke-agent"]
assert "1. POST /v1/media/generate as a roster member" in SMOKE_SRC["smoke-media"]
assert "3. POST /v1/query, the Figure 3 question" in SMOKE_SRC["smoke-media"]
assert SMOKE_SRC["smoke-reindex"].count("st, body = ask(token)") == 2
assert 'resp = requests.post(f"{RAG_API_URL}/v1/query"' in kit("shared/documind_tools.py")   # every retrieve() is an
for rel in ("services/mcp/server.py", "services/chat/tools.py", "services/chat/brains.py"):    # answer of the API's
    assert "passages=True" not in kit(rel), rel
ANSWERS = {"smoke": 1, "smoke-mcp": 1, "smoke-chat": 4, "smoke-agent": 1, "smoke-media": 1, "smoke-reindex": 2}
assert list(ANSWERS) == RUN_SMOKES
N_SMOKE_ANSWERS = sum(ANSWERS.values())
RS_SMOKE = N_SMOKE_ANSWERS * RS_ANSWER
RS_TOTAL = round(RS_GATE + 2 * RS_SMOKE)          # the repair's gate and two healthy smoke runs; the typo bills no tokens
assert (N_SMOKE_ANSWERS, f"{RS_SMOKE:.1f}", RS_TOTAL) == (10, "4.5", 38)
RUN_LIST = (HERE / "RUN_LIST.md").read_text(encoding="utf-8")
for fact in (f"about Rs {RS_GATE}", f"Rs {RS_ANSWER:.2f}", f"{N_ROWS} golden rows", f"the outsider's {N_ISO}",
             f"at least {N_SMOKE_ANSWERS} answers", f"about Rs {RS_SMOKE:.1f}", f"about Rs {RS_TOTAL}",
             f"Ran {N_TESTS} tests", *(make_error(t, 1) for t in LINE)):
    assert fact in RUN_LIST, f"RUN_LIST.md no longer says {fact!r}: the kit's rows, prices, smokes or lines moved"

# ================================================================== verbatim kit excerpts
EXCERPTS = {
    "mk_candidate": ("Makefile - make candidate: a revision with no traffic, made from the template, tagged and recorded",
                     block("Makefile", "# A candidate revision of the API with another model behind it and NO traffic",
                           end="# Eval CANDIDATES from the feed")),
    "mk_promote": ("Makefile - make promote and make rollback: traffic by name, and .previous-revision between them",
                   block("Makefile", "# Traffic to the recorded candidate, by name.", end="# 12.8's full smoke")),
    "gen_fallback": ("services/rag-api/generator.py - _call_or_fallback(): only a routed tier's 429 falls back",
                     block(GEN, "def _exhausted_tier(", end="def _quote_limit(")),
    "main_version": ("services/rag-api/main.py - /version reports the setting, whatever the model makes of it",
                     block(MAIN, '@app.get("/version")', n=8)),
    "mk_smoke_all": ("Makefile - make smoke-all: eight smokes, each one's own exit status",
                     block("Makefile", "# 12.8's full smoke: the eight smokes in one run", end="# 12.3: tenant_daily")),
    "mk_release": ("mk/release.mk - make smoke-deployed and make incident",
                   block(MK_REL, "# ---------- Promote, roll back and repair a controlled failure, lesson 11.3 ----------")),
    "rel_smokes": ("commands/release.py - SMOKES and choose_smokes(): smoke-all's smokes and the services each calls",
                   block(REL, "# smoke-all's smokes, in its order", end="def run_smoke(")),
    "rel_sd_a": ("commands/release.py - cmd_smoke_deployed(), first half: what is deployed, what serves, what /version says",
                 block(REL, "def cmd_smoke_deployed(a) -> int:", end="    env = dict(os.environ, DOCUMIND_PROJECT=project")),
    "rel_sd_b": ("commands/release.py - cmd_smoke_deployed(), second half: the smokes through make, and the log line",
                 block(REL, "    env = dict(os.environ, DOCUMIND_PROJECT=project", end="def lane_time(")),
    "rel_judged": ("commands/release.py - judged(): a revision's verdict, from the gate record or its own report",
                   block(REL, "def judged(name: str", end="def smoke_runs(")),
    "rel_drift": ("commands/release.py - drift() and repair_steps(): what differs from what serves, and the make lines",
                  block(REL, "def drift(template: tuple", end="def cmd_incident(")),
    "rel_inc_a": ("commands/release.py - cmd_incident(), first half: the reads and the timeline",
                  block(REL, "def cmd_incident(a) -> int:", end="    serving_verdict = judged(serving, record, gate_file)")),
    "rel_inc_b": ("commands/release.py - cmd_incident(), second half: now, and the three checks of the gated state",
                  block(REL, "    serving_verdict = judged(serving, record, gate_file)",
                        end="# ---------------------------------------------------------------- the command line")),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["mk_candidate"].splitlines()[-1].startswith('\techo ">> candidate: https://candidate---documind-api-')
assert E["mk_promote"].rstrip().endswith('&& echo ">> traffic on $$PREV"') and "Fifteen seconds;" in E["mk_promote"]
assert E["gen_fallback"].rstrip().endswith("settings.generator_model), settings.generator_model")
assert E["main_version"].rstrip().endswith('"prompt": f"{settings.prompt_id}@{settings.prompt_version}",')
assert E["mk_smoke_all"].rstrip().endswith('done; rm -f $$ST; exit $$rc')
assert E["mk_release"].rstrip().endswith("--hours $${HOURS:-24}")
assert E["rel_smokes"].rstrip().endswith("    return chosen, skipped")
assert E["rel_sd_b"].rstrip().endswith("    return 0") and E["rel_judged"].rstrip().endswith('+ f", {verdict[1]}"')
assert E["rel_drift"].rstrip().endswith('    return steps + ["make gate", "make promote-gated"]')
assert E["rel_inc_b"].rstrip().endswith("    return RED")
fill = filler(EXCERPTS)

# ================================================================== the stand-in lane: the kit test's, run through make's recipes
SP_PROJECT, SP_NUMBER, REGION = "documind-ai-your-id", "100000000011", "asia-south1"   # release.py wants a lower-case id
REPO = f"{REGION}-docker.pkg.dev/{SP_PROJECT}/documind/api"
AUDIENCE = f"https://documind-api-{SP_NUMBER}.{REGION}.run.app"
TAG_URL = f"https://candidate---documind-api-{SP_NUMBER}.{REGION}.run.app"
OLD, GOOD = REPAIR.OLD, REPAIR.GOOD                # the revision make up released, and lesson 11.2's gated candidate
START = GATE.START                                 # 2026-11-16 10:02:11 UTC: lesson 11.2's gate starts
ENV = {**REPAIR.ENV, "GOOGLE_CLOUD_PROJECT": SP_PROJECT, "SELF_URL": AUDIENCE}
assert set(ENV) == set(REPAIR.ENV) and ENV["GENERATOR_MODEL"] == GENERATOR
assert all(ENV[k] == (SETTINGS[k] or ENV[k]) for k in SETTINGS if k in ENV)       # the candidate's settings at defaults


def revision(created: str, git_sha: str) -> dict:
    """One stand-in revision, in the kit test's shape: its image tagged with its GIT_SHA, the kit test's env."""
    image = f"{REPO}:{git_sha}"
    return {"image": image, "env": {**ENV, "GIT_SHA": git_sha}, "service": "documind-api", "ready": True,
            "created": created, "digest": f"{REPO}@sha256:{hashlib.sha256(image.encode()).hexdigest()}"}


WORLD = {"project": SP_PROJECT, "number": SP_NUMBER, "region": REGION, "latest": GOOD,
         "traffic": [{"revisionName": OLD, "percent": 100}, {"revisionName": GOOD, "tag": "candidate"}],
         "revisions": {OLD: revision(REPAIR.WORLD["revisions"][OLD]["created"], "PREVIOUS"),
                       GOOD: revision(REPAIR.WORLD["revisions"][GOOD]["created"], "COMMIT")},
         "template": {"image": f"{REPO}:COMMIT", "env": {**ENV, "GIT_SHA": "COMMIT"}},
         "services": {REGION: SEVEN, SLM_REGION: []}, "no_mint": []}
GREEN = {**GATE.eval_report(rows=N_ROWS), "api_url": TAG_URL}
RED = {**REPAIR.red_report(), "api_url": TAG_URL, "rows": N_ROWS}
RED_WHY = REPAIR.RED_WHY
assert release.report_blocked(GREEN) == [] and "; ".join(release.report_blocked(RED)) == RED_WHY


def placeholders(text: str) -> str:
    """The stand-in's project and number as the course's placeholders; nothing of the kit test's lane reaches the page."""
    out = text.replace(SP_PROJECT, PROJ).replace(SP_NUMBER, "NUMBER")
    assert GATE.PROJECT not in out and GATE.NUMBER not in out, out
    return out


# release.py as make runs it: a subprocess of sh, through this launcher, with three seams held as the kit's InProcess
# tests hold them (the clock, GET /version, the rows); every gcloud, curl and make it calls is the stand-in on PATH.
LAUNCHER = r'''"""release.py as make runs it, with the stand-in lane's clock, GET /version and rows at the seams the kit's
InProcess tests patch (lesson 11.3's build). make promote's own $(PY) -c line runs as python would run it."""
import datetime, importlib.util, json, os, sys

HOME = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[1:]
if argv[:1] == ["-c"]:
    sys.argv = ["-c"] + argv[2:]
    exec(compile(argv[1], "<string>", "exec"), {"__name__": "__main__"})
    sys.exit(0)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


release = load("release", os.path.abspath(argv[0]))
fake = load("standin", os.path.join(HOME, "fake.py"))
with open(os.path.join(HOME, "state.json"), encoding="utf-8") as f:
    state = json.load(f)
clock = [datetime.datetime.fromisoformat(state["now"])]


def world():
    with open(os.path.join(HOME, "world.json"), encoding="utf-8") as f:
        return json.load(f)


def get_version(url, token):
    if not token.endswith("." + state["audience"]):
        raise release.Stop("GET %s/version answered HTTP 401: the token was refused" % url)
    return fake.version(world(), url)


def live_gate(url, report, member, outsider):
    w = world()
    served = w["revisions"][fake.routed(w, url)]["env"].get("GENERATOR_MODEL") in fake.SERVED
    clock[0] += datetime.timedelta(minutes=10)
    os.makedirs(os.path.dirname(str(report)), exist_ok=True)
    with open(report, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(state["green"] if served else state["red"], indent=1))
    return 0 if served else 1


release.now = lambda: clock[0]
release.get_version = get_version
release.live_gate = live_gate
code = release.main(argv[1:])
state["now"] = clock[0].isoformat()
with open(os.path.join(HOME, "state.json"), "w", encoding="utf-8") as f:
    json.dump(state, f)
sys.exit(code)
'''
VARIABLES = {}
for _name in ("GATE_FILE", "SLM_REGION", "TENANT", *SETTINGS):
    _m = re.search(rf"^{_name}[ \t]*\?=[ \t]*(.*?)[ \t]*$", MAKE_TEXT, re.M)
    VARIABLES[_name] = _m.group(1) if _m else ""
VARIABLES.update(PROJECT=SP_PROJECT, REGION=REGION, GIT_SHA="COMMIT",
                 IMAGE_REPO=f"{REGION}-docker.pkg.dev/{SP_PROJECT}/documind")
assert (VARIABLES["GATE_FILE"], VARIABLES["TENANT"], VARIABLES["SLM_REGION"]) == ("evals/reports/gate.json", "acme",
                                                                               SLM_REGION)


class StandInLane:
    """A temporary home: the kit test's stand-in (its FAKE) as gcloud, curl and make on PATH, a copy of the kit's release
    files and Makefile, the launcher, a proxy that refuses every tunnel, and the kit test's MiniMake to run the recipes."""

    def __init__(self):
        self.home = Path(tempfile.mkdtemp(prefix="lesson113_"))
        self.kit = self.home / "kit"
        for rel in (*GATE.FILES, "Makefile"):
            (self.kit / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(KIT / rel, self.kit / rel)
        (self.home / "fake.py").write_text(REPAIR.FAKE, encoding="utf-8", newline="\n")
        (self.home / "launch.py").write_text(LAUNCHER, encoding="utf-8", newline="\n")
        self.fake = load_file(self.home / "fake.py", "lesson113_fake")
        bin_dir = self.home / "bin"
        bin_dir.mkdir()
        py, fake = Path(sys.executable).as_posix(), (self.home / "fake.py").as_posix()
        for tool in ("gcloud", "curl", "make"):
            path = bin_dir / tool
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(f'#!/bin/sh\nexec "{py}" "{fake}" {tool} "$@"\n')
            path.chmod(0o755)
        if os.name == "nt":                     # what release.py finds through PATHEXT, as the kit test writes them
            for tool in ("gcloud", "make"):
                with open(bin_dir / f"{tool}.cmd", "w", encoding="utf-8", newline="\r\n") as f:
                    f.write(f'@echo off\n"{sys.executable}" "{self.home / "fake.py"}" {tool} %*\nexit /b %errorlevel%\n')
        self.proxy = REPAIR.Proxy()
        env = {"PATH": os.pathsep.join([str(bin_dir), str(Path(SH).parent)]), "HOME": str(self.home),
               "USERPROFILE": str(self.home), "APPDATA": str(self.home), "CLOUDSDK_CONFIG": str(self.home / "gcloud"),
               "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "HTTPS_PROXY": self.proxy.url,
               "https_proxy": self.proxy.url}
        for key in ("SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR", "TEMP", "TMP", "LANG"):
            if key in os.environ:
                env[key] = os.environ[key]
        launcher = shlex.quote(py) + " " + shlex.quote((self.home / "launch.py").as_posix())
        self.make = REPAIR.MiniMake(self.kit, env, dict(VARIABLES, PY=launcher))
        self.clock = START
        self.set_world(copy.deepcopy(WORLD))

    def set_world(self, world: dict) -> None:
        (self.home / "world.json").write_text(json.dumps(world), encoding="utf-8")

    def world(self) -> dict:
        return json.loads((self.home / "world.json").read_text(encoding="utf-8"))

    def target(self, name: str, **overrides) -> tuple:
        """make <name> through MiniMake: (its exit code, each sh line with what it printed to stdout and to stderr).
        The clock goes to the launcher in state.json and comes back moved by any gate's ten minutes."""
        state = {"now": self.clock.isoformat(), "audience": AUDIENCE, "green": GREEN, "red": RED}
        (self.home / "state.json").write_text(json.dumps(state), encoding="utf-8")
        world = self.world()
        world["now"] = self.clock.strftime("%Y-%m-%dT%H:%M:%S.%fZ")      # when the stand-in's update makes a revision
        self.set_world(world)
        cap, real = [], subprocess.run

        def run(*a, **kw):
            """MiniMake's sh call, unchanged; what each line printed is kept apart, stdout from stderr."""
            r = real(*a, **kw)
            cap.append((a[0][2], r.stdout, r.stderr))
            return r
        with mock.patch.object(subprocess, "run", run):
            code = self.make.run(name, overrides)
        self.clock = datetime.datetime.fromisoformat(json.loads((self.home / "state.json").read_text(encoding="utf-8"))["now"])
        return code, cap

    def run_inprocess(self, argv, cwd=None):
        """release.run() in-process: every gcloud call to the stand-in."""
        assert argv[0] == "gcloud", argv
        code, out, err = self.fake.handle(argv[0], list(argv[1:]))
        return subprocess.CompletedProcess(argv, code, out, err)

    @contextlib.contextmanager
    def inprocess(self):
        """release.py's own functions on this lane: its KIT, its gcloud and its clock at the seams."""
        with contextlib.ExitStack() as stack:
            for name, value in (("KIT", self.kit), ("run", self.run_inprocess), ("now", lambda: self.clock)):
                stack.enter_context(mock.patch.object(release, name, value))
            yield

    def incident(self) -> tuple:
        """make incident's work, in-process: (exit code, what it printed)."""
        out, err = io.StringIO(), io.StringIO()
        with self.inprocess(), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = release.main(["incident", "--project", SP_PROJECT, "--region", REGION])
        assert not err.getvalue(), err.getvalue()
        return code, out.getvalue()

    def read(self, rel: str) -> str:
        path = self.kit / rel
        return path.read_text(encoding="utf-8").strip() if path.exists() else ""

    def snapshot(self) -> dict:
        """The lane now: the files, the template, every revision with its traffic, tag, model and verdict, and make
        incident's verdict."""
        w = self.world()
        record_path = self.kit / "evals" / "reports" / "gate.json"
        record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else None
        code, out = self.incident()
        revs = []
        with self.inprocess():
            for name in sorted(w["revisions"]):
                verdict = release.judged(name, record, record_path)
                revs.append({"name": name, "pct": sum(t.get("percent", 0) for t in w["traffic"] if t["revisionName"] == name),
                             "tag": ",".join(t["tag"] for t in w["traffic"] if t["revisionName"] == name and t.get("tag")),
                             "model": w["revisions"][name]["env"].get("GENERATOR_MODEL"),
                             "gate": verdict[0] if verdict else ""})
        return {"world": w, "record": record, "incident": (code, out), "revs": revs,
                "cand": self.read(".candidate-revision"), "prev": self.read(".previous-revision"),
                "tpl": w["template"]["env"].get("GENERATOR_MODEL")}

    def saved(self) -> dict:
        """Every file this lane's commands change, as it is now: the world, the two revision files, the reports."""
        files = {p: p.read_bytes() for p in (self.kit / "evals").rglob("*") if p.is_file()}
        for rel in (".candidate-revision", ".previous-revision"):
            if (self.kit / rel).exists():
                files[self.kit / rel] = (self.kit / rel).read_bytes()
        return {"world": self.world(), "files": files, "clock": self.clock}

    def restore(self, saved: dict) -> None:
        """The lane put back as saved() found it."""
        for p in list((self.kit / "evals").rglob("*")) + [self.kit / ".candidate-revision", self.kit / ".previous-revision"]:
            if p.is_file() and p not in saved["files"]:
                p.unlink()
        for p, body in saved["files"].items():
            p.write_bytes(body)
        self.set_world(saved["world"])
        self.clock = saved["clock"]

    def close(self) -> None:
        self.proxy.close()
        shutil.rmtree(self.home, ignore_errors=True)


def output(target: str, code: int, cap: list) -> str:
    """What make <target> printed, as the page shows it: release.py's lines whole (stdout, then its STOP or REFUSED on
    stderr), the recipes' own echo lines, and make's error line when a recipe line failed. The stand-in gcloud's own
    progress lines on stderr are left out."""
    text = "".join(so + se if "commands/release.py" in line else so for line, so, se in cap)
    if code:
        text += make_error(target, code) + "\n"
    return placeholders(text)


CHECKS = (("serves", "the revision serving was judged green by a gate"),
          ("template", "spec.template is what serves"),
          ("candidate", "no revision the gate judged red is the recorded candidate"))


def checks_of(code: int, out: str) -> tuple:
    """make incident's three checks, read from what it printed: (held or not, for each; its reasons; its Repair line)."""
    reasons = [line[5:] for line in out.splitlines() if line.startswith("   - ")]
    failed = []
    for r in reasons:
        kinds = [k for k, hit in (("serves", " serves, and " in r), ("template", r.startswith("spec.template is not what serves")),
                                  (("candidate", r.startswith(".candidate-revision names ")))) if hit]
        assert len(kinds) == 1, r
        failed += kinds
    assert (code == 0) == (not reasons), (code, out)
    repair = next((line.strip() for line in out.splitlines() if line.startswith("   Repair: ")), "")
    return [k not in failed for k, _ in CHECKS], reasons, repair


# the fifteen commands of the author's run (SP/kr3_facts.md), with the minutes before each and what the page says of it
STEPS = [
    ("promote-gated", {}, 2, "make promote-gated", "promote-gated", "lesson 11.2's green candidate, promoted through the gate"),
    ("candidate", {"GENERATOR_MODEL": TYPO}, 3, f"make candidate GENERATOR_MODEL={TYPO}", "candidate flsh",
     "the mistyped model, on a new revision with no traffic, made from the template"),
    ("gate", {}, 0, "make gate", "gate", "every golden row asked of the candidate: red, and recorded"),
    ("promote-gated", {}, 1, "make promote-gated", "promote-gated", "refused: the record says red"),
    ("promote", {}, 1, "make promote", "promote", "forced: plain make promote reads no record"),
    ("smoke-deployed", {}, 1, "make smoke-deployed", "smoke-deployed", "the smokes of the deployed services: red"),
    ("incident", {}, 1, "make incident", "incident", "a revision the gate judged red serves: roll back"),
    ("rollback", {}, 1, "time make rollback", "rollback", "traffic back to .previous-revision, by name"),
    ("smoke-deployed", {}, 1, "make smoke-deployed", "smoke-deployed", "green again"),
    ("incident", {}, 1, "make incident", "incident", "still not the gated state: the template holds the typo"),
    ("candidate", {"GENERATOR_MODEL": MODEL}, 3, f"make candidate GENERATOR_MODEL={MODEL}", "candidate flash",
     "the repair: a candidate made with what serves"),
    ("gate", {}, 0, "make gate", "gate", "green, and recorded"),
    ("promote-gated", {}, 1, "make promote-gated", "promote-gated", "promoted through the gate"),
    ("smoke-deployed", {}, 1, "make smoke-deployed", "smoke-deployed", "the proof: green"),
    ("incident", {}, 1, "make incident", "incident", "the gated state: exit 0"),
]
assert len(STEPS) == 15
lane = StandInLane()
try:
    assert lane.target("record-candidate")[0] == 0                    # lesson 11.2's state: its candidate recorded,
    G0_CODE, G0_CAP = lane.target("gate")                             # judged green
    assert G0_CODE == 0, G0_CAP
    SNAP = [lane.snapshot()]
    RAN = []
    RC_OUT = None
    for i, (target, overrides, minutes, _cmd, _short, _what) in enumerate(STEPS, 1):
        lane.clock += datetime.timedelta(minutes=minutes)
        code, cap = lane.target(target, **overrides)
        RAN.append((target, code, output(target, code, cap)))
        SNAP.append(lane.snapshot())
        if target == "incident":                                      # make incident's own words, in-process and through make
            assert (code, RAN[-1][2]) == (SNAP[-1]["incident"][0],
                                          placeholders(SNAP[-1]["incident"][1]) + (make_error("incident", code) + "\n" if code else "")), i
        if i == 10:                                                   # what make release-candidate would make now
            kept = lane.saved()
            rc_code, rc_cap = lane.target("release-candidate")
            inherited = lane.read(".candidate-revision")
            inherited_env = lane.world()["revisions"][inherited]["env"]
            rg_code, rg_cap = lane.target("gate")
            RC_OUT = (rc_code, output("release-candidate", rc_code, rc_cap), inherited, inherited_env,
                      rg_code, output("gate", rg_code, rg_cap))
            lane.restore(kept)
    END_CALLS = (lane.home / "calls.jsonl").read_text(encoding="utf-8")
finally:
    lane.close()

CODES = [code for _, code, _ in RAN]
assert CODES == [0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0], CODES
OUT = [text for _, _, text in RAN]
BAD = SNAP[2]["cand"]                                                  # the stand-in names the revisions it makes
FIX = SNAP[11]["cand"]
assert BAD != FIX and {BAD, FIX}.isdisjoint({OLD, GOOD}) and SNAP[15]["prev"] == GOOD
serving = lambda s: next(t["revisionName"] for t in s["world"]["traffic"] if t.get("percent"))   # noqa: E731
assert [serving(s) for s in SNAP] == [OLD, GOOD, GOOD, GOOD, GOOD, BAD, BAD, BAD, GOOD, GOOD, GOOD, GOOD, GOOD, FIX, FIX, FIX]
assert [s["tpl"] for s in SNAP] == [MODEL, MODEL] + [TYPO] * 9 + [MODEL] * 5
assert SNAP[2]["world"]["revisions"][BAD]["env"] == {**ENV, "GIT_SHA": "COMMIT", "GENERATOR_MODEL": TYPO}
assert SNAP[11]["world"]["revisions"][FIX]["env"] == SNAP[0]["world"]["revisions"][GOOD]["env"]   # what GOOD runs
CHECKED = [checks_of(*s["incident"]) for s in SNAP]
GATED = [all(c[0]) for c in CHECKED]
assert GATED == [False, True] + [False] * 9 + [True] * 5, GATED
assert [c[0] for c in CHECKED[2:11]] == [[True, False, True], [True, False, False], [True, False, False],
                                          [False, True, True], [False, True, True], [False, True, True],
                                          [True, False, False], [True, False, False], [True, False, False]]
assert CHECKED[5][2].startswith(f"Repair: make rollback, which moves traffic back to {GOOD} (.previous-revision)")
assert CHECKED[8][2] == f"Repair: make candidate GENERATOR_MODEL={MODEL}; then make gate; then make promote-gated"
assert release.REFUSED == 1 and f"  - red: the gate judged {BAD} red ({RED_WHY})" in OUT[3]
assert f">> serving before the flip: {GOOD} (deploy/.previous-revision - make rollback returns to it)" in OUT[4]
assert OUT[7] == f">> traffic on {GOOD}\n"
assert f"   {BAD}  FAIL  {RED_WHY}" in OUT[2] and f"GET /version on {placeholders(TAG_URL)}: git_sha COMMIT, {TYPO}," in OUT[2]
assert f">> FAIL: {', '.join(RUN_SMOKES)} failed; 0 passed, {len(SKIPPED)} skipped." in OUT[5]
assert OUT[8].rstrip().endswith(f">> PASS: {len(RUN_SMOKES)} passed, {len(SKIPPED)} skipped. Recorded in "
                                "evals/reports/smoke-deployed.jsonl")
assert OUT[14].rstrip().endswith(f">> the gated state: {FIX} serves, judged green (evals/reports/gate.json); "
                                 "spec.template is what serves; no red candidate is recorded")
assert f"  traffic   {BAD} -> {GOOD}: seen between the smoke runs of " in OUT[9]
assert not re.search(r'"args": \["run", "services", "update",', END_CALLS.split(f'"{FIX}=100"')[-1])   # nothing after
RC_CODE, RC_TEXT, INHERITED, INHERITED_ENV, RG_CODE, RG_TEXT = RC_OUT
assert (RC_CODE, RG_CODE, INHERITED_ENV["GENERATOR_MODEL"], INHERITED_ENV["GIT_SHA"]) == (0, 1, TYPO, "COMMIT")
assert INHERITED == FIX       # the stand-in was put back, so the repair's revision takes the same number and name
N_RUN, N_SMOKES = len(RUN_SMOKES), len(SMOKES)

# ================================================================== the stepper's data, and node's check of its script
STEP0 = ("(lesson 11.2's state)", "start",
         "where lesson 11.2 left the lane: its candidate judged green, the revision make up released still serving")


def key_lines(target: str, text: str) -> str:
    """The lines of one command's output the stepper shows: all of a short one; a smoke run's summary; make incident
    from its now block on."""
    lines = text.rstrip("\n").splitlines()
    if target == "smoke-deployed":
        lines = [x for x in lines if x.startswith(">>") or x.startswith("   GET /version") or "FAILED (exit" in x
                 or x.startswith("make: ")]
    elif target == "incident":
        lines = lines[next(k for k, x in enumerate(lines) if x == ">> now"):]
    return "\n".join(lines)


def exit_line(target: str, code: int) -> str:
    """How the step ended: release.py's exit code and make's, or the recipe's."""
    if not code:
        return "exit 0"
    return f"release.py exit {code}; make exits 2"


CF_STEPS = []
for i, s in enumerate(SNAP):
    if i == 0:
        cmd, short, what = STEP0
        target, code, text = "gate", 0, "\n".join(x for x in output("gate", G0_CODE, G0_CAP).splitlines()
                                                  if x.startswith(">> gate record") or "  PASS  " in x)
    else:
        target, _ov, _m, cmd, short, what = STEPS[i - 1]
        code, text = CODES[i - 1], key_lines(target, OUT[i - 1])
    checks, reasons, repair = CHECKED[i]
    CF_STEPS.append({"short": short, "cmd": cmd, "what": what, "ok": code == 0, "exit": exit_line(target, code),
                     "out": text, "cand": s["cand"] or "none", "prev": s["prev"] or "none", "tpl": s["tpl"],
                     "revs": [[r["name"], r["pct"], r["tag"], r["model"], r["gate"]] for r in s["revs"]],
                     "checks": checks, "gated": all(checks)})
CF_DATA = {"steps": CF_STEPS, "checks": [t for _, t in CHECKS], "model": MODEL,
           "say": {"gated": "make incident exits 0: the gated state.",
                   "not": "make incident exits 1: not the gated state.",
                   "lane": "the lane after it", "printed": "what it printed",
                   "files": "the files and the template", "state": "make incident's three checks"}}
CF_JS = r"""var D = __DATA__;
function node(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
function view(i){
  var s = D.steps[i], f = document.createDocumentFragment();
  f.appendChild(node('p', 'cf-head', 'Step ' + i + ' of ' + (D.steps.length - 1) + ': ' + s.cmd + '  (' + s.exit + ')'));
  f.appendChild(node('p', 'cf-what', s.what));
  if (s.out) { f.appendChild(node('div', 'cf-term', s.out)); }
  var grid = node('div', 'cf-grid'), lane = node('div', 'cf-box'), files = node('div', 'cf-box'), state = node('div', 'cf-box');
  lane.appendChild(node('p', 'cf-label', D.say.lane));
  s.revs.forEach(function(r){
    var row = node('div', 'cf-row' + (r[1] ? ' live' : ''));
    row.appendChild(document.createTextNode(r[0] + '  ' + r[1] + '%' + (r[2] ? '  tag ' + r[2] : '') + '  '));
    row.appendChild(node('span', r[3] === D.model ? '' : 'bad', r[3]));
    row.appendChild(document.createTextNode(r[4] ? '  gate: ' + r[4] : '  no gate'));
    lane.appendChild(row);
  });
  files.appendChild(node('p', 'cf-label', D.say.files));
  [['.candidate-revision', s.cand], ['.previous-revision', s.prev]].forEach(function(p){ files.appendChild(node('div', 'cf-row', p[0] + '  ' + p[1])); });
  var t = node('div', 'cf-row');
  t.appendChild(document.createTextNode('spec.template  GENERATOR_MODEL='));
  t.appendChild(node('span', s.tpl === D.model ? '' : 'bad', s.tpl));
  files.appendChild(t);
  state.appendChild(node('p', 'cf-label', D.say.state));
  var list = node('ul', 'cf-checks');
  D.checks.forEach(function(c, k){
    var li = node('li', s.checks[k] ? 'ok' : 'no');
    li.appendChild(node('b', '', s.checks[k] ? '✓' : '✗'));
    li.appendChild(node('span', '', c));
    list.appendChild(li);
  });
  state.appendChild(list);
  grid.appendChild(lane); grid.appendChild(files); grid.appendChild(state);
  f.appendChild(node('p', 'cf-v ' + (s.gated ? 'ok' : 'no'), s.gated ? D.say.gated : D.say.not));
  f.appendChild(grid);
  return f;
}
window.__cf = {view: view, steps: D.steps.length};
var root = document.getElementById('cf'); if (!root) { return; }
var btns = Array.prototype.slice.call(root.querySelectorAll('.cf-steps button'));
var out = document.getElementById('cf-out'), prev = document.getElementById('cf-prev'), next = document.getElementById('cf-next');
var cur = 0;
function show(i){
  cur = i;
  btns.forEach(function(b){ b.setAttribute('aria-pressed', +b.getAttribute('data-i') === i ? 'true' : 'false'); });
  out.textContent = '';
  out.appendChild(view(i));
  prev.disabled = i === 0;
  next.disabled = i === D.steps.length - 1;
}
btns.forEach(function(b){ b.addEventListener('click', function(){ show(+b.getAttribute('data-i')); }); });
prev.addEventListener('click', function(){ if (cur > 0) { show(cur - 1); } });
next.addEventListener('click', function(){ if (cur < D.steps.length - 1) { show(cur + 1); } });
show(0);"""
CF_JS = CF_JS.replace("__DATA__", json.dumps(CF_DATA, ensure_ascii=False, separators=(",", ":")))
JS = "<script>\n(function(){\n'use strict';\n" + CF_JS.replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS and "—" not in JS and "–" not in JS and SP_PROJECT not in JS and SP_NUMBER not in JS
NODE = r"""function E(tag){ this.tag = tag; this.kids = []; this.className = ''; this.own = ''; this.attrs = {}; }
E.prototype.appendChild = function(c){ this.kids.push(c); return c; };
E.prototype.setAttribute = function(k, v){ this.attrs[k] = v; };
Object.defineProperty(E.prototype, 'textContent', {get: function(){ return this.own + this.kids.map(function(c){ return c.textContent; }).join('|'); },
                                                   set: function(v){ this.own = String(v); this.kids = []; }});
var document = {createElement: function(t){ return new E(t); }, createDocumentFragment: function(){ return new E('#'); },
                createTextNode: function(t){ var e = new E('#text'); e.own = t; return e; }, getElementById: function(){ return null; }};
var window = {};
(new Function('window', 'document', __JS__))(window, document);
var got = [];
for (var i = 0; i < window.__cf.steps; i++) { got.push(window.__cf.view(i).textContent); }
process.stdout.write(JSON.stringify(got));
"""
node = subprocess.run(["node", "-"], input=NODE.replace("__JS__", json.dumps(CF_JS)), capture_output=True, text=True,
                      encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
VIEWS = json.loads(node.stdout)
assert len(VIEWS) == len(CF_STEPS) == 16
for i, (view, s) in enumerate(zip(VIEWS, CF_STEPS)):
    assert f"Step {i} of 15: {s['cmd']}" in view and s["exit"] in view and s["what"] in view, (i, view[:200])
    assert all(r[0] in view for r in s["revs"]) and f"spec.template  GENERATOR_MODEL=|{s['tpl']}" in view
    assert (CF_DATA["say"]["gated"] if s["gated"] else CF_DATA["say"]["not"]) in view, i
CF_PANEL = (
    '<div class="cf-steps" role="group" aria-label="The fifteen commands, and the state before them">'
    + "".join(f'<button type="button" data-i="{i}" aria-pressed="{"true" if i == 0 else "false"}"'
              + ("" if s["ok"] else ' class="no"') + f'>{i} {html.escape(s["short"])}</button>'
              for i, s in enumerate(CF_STEPS))
    + '</div>\n<div class="cf-nav"><button type="button" id="cf-prev">&larr; previous</button>'
      '<button type="button" id="cf-next">next &rarr;</button></div>\n<div id="cf-out" aria-live="polite"></div>\n')

# ================================================================== the cells, and what each prints
# Each cell sits between its own blank lines and is stripped of them; triple single quotes, because the Python cells
# carry docstrings.
LANE_ARGS = 'PROJECT="$PROJECT" REGION="$REGION"'
CELLS = {
    "tests": r'''
python commands/tests/test_release_repair.py
''',
    "promote": f'''
make promote-gated {LANE_ARGS}; echo "exit $?"
''',
    "typo": f'''
make candidate {LANE_ARGS} GENERATOR_MODEL={TYPO}
''',
    "gate_typo": f'''
make gate {LANE_ARGS}; echo "exit $?"
''',
    "forced": f'''
make promote-gated {LANE_ARGS}; echo "exit $?"
make promote {LANE_ARGS}; echo "exit $?"
''',
    "red": f'''
make smoke-deployed {LANE_ARGS}; echo "exit $?"
make incident {LANE_ARGS}; echo "exit $?"
''',
    "rollback": f'''
time make rollback {LANE_ARGS}
''',
    # the put-back the lesson's finish runs, and a learner who stops between the forced promote and the rollback runs:
    # it moves traffic only while the revision serving all of documind-api's traffic runs the mistyped model
    "putback": f'''
# when you finish the lesson: documind-api back on the revision before the forced promote, only while it serves {TYPO}
SERVING="$(gcloud run services describe documind-api --region="$REGION" --project="$PROJECT" --format=json |
  python -c 'import json,sys; print(next((t.get("revisionName", "") for t in json.load(sys.stdin)["status"]["traffic"] if t.get("percent") == 100), ""))')"
MODEL="$(gcloud run revisions describe "$SERVING" --region="$REGION" --project="$PROJECT" --format=json |
  python -c 'import json,sys; print({{e["name"]: e.get("value", "") for c in json.load(sys.stdin)["spec"]["containers"] for e in c.get("env", [])}}.get("GENERATOR_MODEL", ""))')"
if [ "$MODEL" = "{TYPO}" ]; then make rollback {LANE_ARGS}; else echo "documind-api serves $SERVING ($MODEL): nothing to put back"; fi
''',
    "template": r'''
python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
import google.auth
from google.auth.transport.requests import AuthorizedSession

P, R = os.environ["PROJECT"], os.environ["REGION"]
creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
run = AuthorizedSession(creds.with_quota_project(P) if hasattr(creds, "with_quota_project") else creds)
V1 = f"https://{R}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/{P}"


def read(path, **params):
    """One read of the Cloud Run Admin API's v1 resources, as JSON; a failure says which read and why."""
    r = run.get(f"{V1}/{path}", params=params or None, timeout=30)
    if r.status_code != 200:
        raise SystemExit(f"GET {path}: HTTP {r.status_code} {r.text[:200]}")
    return r.json()


def settings(spec):
    """(the image, GENERATOR_MODEL) of a spec: a revision holds a digest, spec.template the tag it was made from."""
    c = (spec.get("containers") or [{}])[0]
    env = {e.get("name"): e.get("value") for e in c.get("env") or []}
    return c.get("image", "").rsplit("/", 1)[-1], env.get("GENERATOR_MODEL")


def short(image):
    """An image cut to what an eye compares: a digest to 12 hex digits, as docker shows one; a tag as it is."""
    name, at, digest = image.partition("@sha256:")
    return f"{name}@sha256:{digest[:12]}" if at else image


svc = read("services/documind-api")
traffic = svc["status"]["traffic"]
revs = sorted(read("revisions", labelSelector="serving.knative.dev/service=documind-api")["items"],
              key=lambda r: r["metadata"]["creationTimestamp"])
spec = {r["metadata"]["name"]: r["spec"] for r in revs}
serving = max((t for t in traffic if t.get("percent")), key=lambda t: t["percent"])["revisionName"]
for rev in revs[-4:]:
    name = rev["metadata"]["name"]
    pct = sum(t.get("percent", 0) for t in traffic if t.get("revisionName") == name)
    tag = ",".join(t["tag"] for t in traffic if t.get("revisionName") == name and t.get("tag")) or "-"
    image, model = settings(rev["spec"])
    print(f"{name:26} {pct:>3}%  tag {tag:9}  {short(image):23}  GENERATOR_MODEL={model}")
template = settings(svc["spec"]["template"]["spec"])
print(f"{'spec.template':26} {'':4}  {'':13}  {short(template[0]):23}  GENERATOR_MODEL={template[1]}")
now = settings(spec[serving])
made = settings(spec[svc["status"]["latestCreatedRevisionName"]])[0]      # the digest the template's tag named
if (made, template[1]) == now:
    print(f"the template is what serves: {serving}")
else:
    print(f"the template is NOT what serves: {serving} runs GENERATOR_MODEL={now[1]}.")
    print("The next revision any update makes starts from the template, not from what serves.")
PY
''',
    "repair": f'''
make candidate {LANE_ARGS} GENERATOR_MODEL={MODEL}
make gate {LANE_ARGS}; echo "exit $?"
''',
    "errors": r'''
python - <<'PY'
import collections, datetime, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
import google.auth
from google.auth.transport.requests import AuthorizedSession

P = os.environ["PROJECT"]
HOURS = float(os.environ.get("HOURS", "3"))
creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
logs = AuthorizedSession(creds.with_quota_project(P) if hasattr(creds, "with_quota_project") else creds)
since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=HOURS)
FILTER = (f'logName="projects/{P}/logs/run.googleapis.com%2Frequests" AND resource.type="cloud_run_revision" '
          f'AND resource.labels.service_name="documind-api" AND timestamp>="{since:%Y-%m-%dT%H:%M:%SZ}"')


def entries():
    """documind-api's request log lines in the window, oldest first: every page of Cloud Logging's entries:list."""
    body = {"resourceNames": [f"projects/{P}"], "filter": FILTER, "orderBy": "timestamp asc", "pageSize": 1000}
    while True:
        r = logs.post("https://logging.googleapis.com/v2/entries:list", json=body, timeout=60)
        if r.status_code != 200:
            raise SystemExit(f"entries:list: HTTP {r.status_code} {r.text[:200]}")
        page = r.json()
        yield from page.get("entries", [])
        if not page.get("nextPageToken"):
            return
        body["pageToken"] = page["nextPageToken"]


count = collections.defaultdict(collections.Counter)
failed = collections.defaultdict(collections.Counter)
span = {}
for e in entries():
    rev = (e.get("resource", {}).get("labels") or {}).get("revision_name") or "(no revision)"
    req = e.get("httpRequest") or {}
    status = int(req.get("status") or 0)
    count[rev]["2xx" if 200 <= status < 300 else "4xx" if 400 <= status < 500 else "5xx" if status >= 500 else "other"] += 1
    if status >= 500:
        failed[rev][req.get("requestUrl", "").split(".run.app", 1)[-1].split("?", 1)[0] or "?"] += 1
        t = e["timestamp"][:19] + "Z"
        span[rev] = (min(span.get(rev, (t, t))[0], t), max(span.get(rev, (t, t))[1], t))
print(f"documind-api's requests in the last {HOURS:g} hours, by the revision that answered:")
for rev in sorted(count):
    c = count[rev]
    line = f"  {rev:26}" + "".join(f"  {k} {c[k]:>4}" for k in ("2xx", "4xx", "5xx"))
    if rev in failed:
        line += f"   5xx {span[rev][0]} to {span[rev][1]}: " + ", ".join(f"{p} {n}" for p, n in failed[rev].most_common())
    print(line)
PY
''',
}
CELLS["after"] = CELLS["red"]
CELLS["promote_fix"] = CELLS["promote"]
CELLS["proof"] = CELLS["red"]
CELLS = {k: v.strip("\n") for k, v in CELLS.items()}
CELL_LABELS = {
    "tests": "run in the operator shell, in the kit (stand-ins only: no Google call, no cost)",
    "promote": "run in the operator shell, in the kit (gate-check, then one traffic move)",
    "typo": "run in the operator shell, in the kit (a revision with no traffic and a mistyped model)",
    "gate_typo": "run in the operator shell, in the kit (every golden row, about ten minutes; no model call succeeds)",
    "forced": "run in the operator shell, in the kit (the refusal, then the forced traffic move: your API answers 500 until the rollback)",
    "red": "run in the operator shell, in the kit, straight after (the smokes, then the incident read)",
    "rollback": "run in the operator shell, in the kit, straight after (one traffic move, timed)",
    "putback": "run in the operator shell, in the kit, when you finish the lesson, not now (a traffic move only while the mistyped model serves)",
    "after": "run in the operator shell, in the kit, after the rollback (the smokes, then the incident read)",
    "template": "run in the operator shell, in the kit, before the repair (two Cloud Run Admin API reads; writes nothing)",
    "repair": "run in the operator shell, in the kit (the Repair line make incident printed, then every golden row)",
    "promote_fix": "run in the operator shell, in the kit (gate-check, then one traffic move)",
    "proof": "run in the operator shell, in the kit (the proof: the smokes, then the incident read)",
    "errors": "run in the operator shell, in the kit, after the proof (Cloud Logging reads; writes nothing)",
}
assert set(CELL_LABELS) == set(CELLS)
for name, cell in CELLS.items():                            # every function a cell defines carries a one-line docstring
    for m in re.finditer(r"^def (\w+)\(.*\):\n( +)(.*)$", cell, re.M):
        assert m.group(3).startswith('"""') and m.group(3).endswith('"""'), (name, m.group(1))
    if "<<'PY'" in cell:
        assert 'warnings.filterwarnings("ignore", category=UserWarning)' in cell and cell.count("\nPY") >= 1, name
for name in ("promote", "typo", "gate_typo", "forced", "red", "rollback", "repair", "tests"):
    assert f"```bash\n{CELLS[name]}\n```" in RUN_LIST, f"RUN_LIST.md's copy of the {name} cell differs from the page's"
assert "update-traffic" not in "".join(CELLS.values()) and "--to-revisions" not in "".join(CELLS.values())

# the two Python cells, each run against stand-ins before any lane runs it: their code works before it is recorded
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


GOOGLE_STANDIN = r'''import json as _json, sys as _sys, types as _types
_DOCS = _json.loads(%r)
class _Creds:
    def with_quota_project(self, p): return self
class _Resp:
    def __init__(self, doc): self.status_code, self._doc, self.text = 200, doc, _json.dumps(doc)
    def json(self): return self._doc
class _Session:
    def __init__(self, creds): pass
    def get(self, url, params=None, timeout=None):
        key = url.split("/namespaces/", 1)[1].split("/", 1)[1]
        if params:
            key += "?" + "&".join(k + "=" + str(v) for k, v in sorted(params.items()))
        return _Resp(_DOCS[key])
    def post(self, url, json=None, timeout=None):
        assert url == "https://logging.googleapis.com/v2/entries:list", url
        with open("posts.jsonl", "a", encoding="utf-8") as f:
            f.write(_json.dumps(json) + "\n")
        return _Resp(_DOCS["pages"][json.get("pageToken", "first")])
_g, _ga, _gt, _gtr = (_types.ModuleType(n) for n in ("google", "google.auth", "google.auth.transport", "google.auth.transport.requests"))
_ga.default = lambda scopes=None: (_Creds(), "stand-in")
_gtr.AuthorizedSession = _Session
_g.auth, _ga.transport, _gt.requests = _ga, _gt, _gtr
_sys.modules.update({"google": _g, "google.auth": _ga, "google.auth.transport": _gt, "google.auth.transport.requests": _gtr})
'''


def standin_docs(world: dict) -> dict:
    """The service and its revision list as the Cloud Run Admin API's v1 resources return them, from the kit test's
    stand-in's own JSON (gcloud's describe and list print the same resources)."""
    home = Path(tempfile.mkdtemp(prefix="lesson113_docs_"))
    try:
        (home / "fake.py").write_text(REPAIR.FAKE, encoding="utf-8", newline="\n")
        (home / "world.json").write_text(json.dumps(world), encoding="utf-8")
        fake = load_file(home / "fake.py", "lesson113_docs_fake")
        code_s, svc, _ = fake.handle("gcloud", ["run", "services", "describe", "documind-api", "--region", REGION,
                                                "--project", SP_PROJECT, "--format", "json"])
        code_r, revs, _ = fake.handle("gcloud", ["run", "revisions", "list", "--service=documind-api", f"--region={REGION}",
                                                 f"--project={SP_PROJECT}", "--format=json"])
        assert (code_s, code_r) == (0, 0)
        return {"services/documind-api": json.loads(svc),
                "revisions?labelSelector=serving.knative.dev/service=documind-api": {"items": json.loads(revs)}}
    finally:
        shutil.rmtree(home, ignore_errors=True)


CELL_HOME = Path(tempfile.mkdtemp(prefix="lesson113_cells_"))
try:
    out_tpl = run_cell(heredoc_of(CELLS["template"]), CELL_HOME, GOOGLE_STANDIN % json.dumps(standin_docs(SNAP[10]["world"])))
    TPL_LINES = out_tpl.splitlines()
    assert [line.split()[0] for line in TPL_LINES[:4]] == [OLD, GOOD, BAD, "spec.template"], out_tpl
    assert TPL_LINES[1].split()[1] == "100%" and TPL_LINES[2].split()[3] == "candidate", out_tpl
    assert TPL_LINES[2].endswith(f"GENERATOR_MODEL={TYPO}") and TPL_LINES[3].endswith(f"GENERATOR_MODEL={TYPO}")
    assert TPL_LINES[4:] == [f"the template is NOT what serves: {GOOD} runs GENERATOR_MODEL={MODEL}.",
                             "The next revision any update makes starts from the template, not from what serves."], out_tpl
    out_ok = run_cell(heredoc_of(CELLS["template"]), CELL_HOME, GOOGLE_STANDIN % json.dumps(standin_docs(SNAP[15]["world"])))
    assert out_ok.splitlines()[-1] == f"the template is what serves: {FIX}", out_ok
    url = f"https://documind-api-{SP_NUMBER}.{REGION}.run.app"

    def entry(rev: str, status: int, path: str, t: str) -> dict:
        """One request log line, in the shape Cloud Logging returns for Cloud Run."""
        return {"timestamp": t, "resource": {"type": "cloud_run_revision", "labels": {"revision_name": rev,
                "service_name": "documind-api"}}, "httpRequest": {"status": status, "requestUrl": url + path}}
    pages = {"first": {"entries": [entry(GOOD, 200, "/v1/query", "2026-11-16T10:20:01.5Z"),
                                   entry(BAD, 500, "/v1/query", "2026-11-16T10:21:02.25Z"),
                                   entry(BAD, 403, "/v1/query", "2026-11-16T10:21:03Z")], "nextPageToken": "p2"},
             "p2": {"entries": [entry(BAD, 500, "/v1/query", "2026-11-16T10:30:04.1Z"),
                                entry(BAD, 200, "/health", "2026-11-16T10:30:05Z"),
                                entry(FIX, 200, "/v1/query?x=1", "2026-11-16T10:46:06Z")]}}
    out_err = run_cell(heredoc_of(CELLS["errors"]), CELL_HOME, GOOGLE_STANDIN % json.dumps({"pages": pages}))
    assert out_err.splitlines() == [
        "documind-api's requests in the last 3 hours, by the revision that answered:",
        f"  {GOOD:26}  2xx    1  4xx    0  5xx    0",
        f"  {BAD:26}  2xx    1  4xx    1  5xx    2   5xx 2026-11-16T10:21:02Z to 2026-11-16T10:30:04Z: /v1/query 2",
        f"  {FIX:26}  2xx    1  4xx    0  5xx    0"], out_err
    posts = [json.loads(line) for line in (CELL_HOME / "posts.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(posts) == 2 and posts[1]["pageToken"] == "p2" and posts[0]["resourceNames"] == [f"projects/{SP_PROJECT}"]
    assert ('resource.labels.service_name="documind-api"' in posts[0]["filter"]
            and f'logName="projects/{SP_PROJECT}/logs/run.googleapis.com%2Frequests"' in posts[0]["filter"])
finally:
    shutil.rmtree(CELL_HOME, ignore_errors=True)

# ================================================================== what the windows show
RECORDED = {k: pb.recorded(LESSON, f"{k}.txt") for k in
            ("promote_gated", "candidate_typo", "gate_typo", "promote_refused_forced", "smoke_incident_red",
             "rollback_timed", "smoke_incident_after", "template_read", "candidate_gate_repair", "promote_repair",
             "smoke_incident_proof", "errors_by_revision")}
LANE_LABEL = "(the author's lane: your revision names, commit, digests and times are yours)"
STAND_IN = "the Makefile's recipes and release.py, run when this page was built against the kit test's stand-in lane"


def with_exit(text: str, code: int) -> str:
    """A cell's output with its echo line: make exits 2 when a recipe line fails."""
    return text + f"exit {0 if code == 0 else 2}\n"


OUTS = {
    "tests": ("shape (the kit's own tests on your machine: the time is yours)",
              "." * N_TESTS + "\n" + "-" * 70 + f"\nRan {N_TESTS} tests in Ns\n\nOK"),
    "s_gate": (f"({STAND_IN}: the stand-in's names, commit and digest; on your lane run_eval.py prints its rows between "
               "the two >> blocks; make's last line as GNU make 4 prints it)", with_exit(OUT[2], CODES[2])),
    "s_forced": (f"({STAND_IN}: make promote's own lines, the stand-in gcloud's left out; yours prints its progress "
                 "between them)", with_exit(OUT[3], CODES[3]) + with_exit(OUT[4], CODES[4])),
    "s_red": (f"({STAND_IN}: each stand-in smoke prints two checks; yours print their own)",
              with_exit(OUT[5], CODES[5]) + with_exit(OUT[6], CODES[6])),
    "s_after": (f"({STAND_IN}, after make rollback)", with_exit(OUT[8], CODES[8]) + with_exit(OUT[9], CODES[9])),
    "s_proof": (f"({STAND_IN}, after the repair)", with_exit(OUT[13], CODES[13]) + with_exit(OUT[14], CODES[14])),
    "s_rc": (f"(make release-candidate and make gate, {STAND_IN} in its state after the rollback, then put back as it "
             "was, so the repair's revision later takes the same name; the third line is this page's read of the "
             "revision it made)",
             RC_TEXT + f"{INHERITED}: api:COMMIT with GENERATOR_MODEL={INHERITED_ENV['GENERATOR_MODEL']} (the image and "
             "GIT_SHA from the command, every other setting from spec.template)\n"
             + "\n".join(x for x in RG_TEXT.splitlines() if "  FAIL  " in x or x.startswith("make: "))),
    "promote": (LANE_LABEL, RECORDED["promote_gated"]),
    "typo": (LANE_LABEL, RECORDED["candidate_typo"]),
    "gate_typo": ("(the author's lane: the gate on the mistyped model; your rates, names and times are yours)",
                  RECORDED["gate_typo"]),
    "forced": (LANE_LABEL, RECORDED["promote_refused_forced"]),
    "red": (LANE_LABEL, RECORDED["smoke_incident_red"]),
    "rollback": ("(the author's lane: your names and your real line are yours)", RECORDED["rollback_timed"]),
    "after": (LANE_LABEL, RECORDED["smoke_incident_after"]),
    "template": (LANE_LABEL, RECORDED["template_read"]),
    "repair": ("(the author's lane: the repair gated; your rates, names and times are yours)",
               RECORDED["candidate_gate_repair"]),
    "promote_fix": (LANE_LABEL, RECORDED["promote_repair"]),
    "proof": (LANE_LABEL, RECORDED["smoke_incident_proof"]),
    "errors": (LANE_LABEL, RECORDED["errors_by_revision"]),
}
assert placeholders(RC_TEXT).startswith(f">> candidate revision: {INHERITED} (deploy/.candidate-revision - make promote "
                                        "moves traffic to it by name)")


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
SMOKES_TABLE = tw(["Smoke", "The Cloud Run services its target calls", "Answers it asks of documind-api",
                   "On a lane without Module 9's services"], [
    [code(t), ", ".join(code(n) + (f" in {code('SLM_REGION')} ({SLM_REGION})" if n in release.IN_SLM_REGION else "")
                        for n in needs),
     str(ANSWERS[t]) if t in ANSWERS else "-", "runs" if t in RUN_SMOKES else "skipped, named with what it lacks"]
    for t, needs in SMOKES])
COST_TABLE = tw(["Run", "What it costs", "On your lane"], [
    [f"{code('make promote-gated')}, {code('make promote')}, {code('time make rollback')}",
     "traffic moves, and make promote's one GET /version", "Rs 0"],
    [f"{code('make candidate')}, twice", "revisions with no traffic; the API's floor is zero instances", "Rs 0"],
    [f"{code('make gate')} on the mistyped model",
     f"{N_ROWS} rows, and every model call refused by Vertex AI, which bills no tokens for a model it does not serve; the "
     f"outsider's {N_ISO} requests refused at the roster", "Rs 0 in model tokens"],
    [f"{code('make gate')} on the repair",
     f"{N_ROWS} answers at the course's typical 2,000 tokens in and 300 out (Rs {RS_ANSWER:.2f} each)",
     f"about Rs {RS_GATE}; {code('make usage')} prints yours"],
    [f"{code('make smoke-deployed')}, three runs",
     f"at least {N_SMOKE_ANSWERS} answers of documind-api on a healthy revision (the table above), none billed while the "
     "mistyped model serves; and in every run, calls this price table does not hold: the agent brains' and the A2A "
     "peer's own model calls, one generated image and the indexing of two uploads",
     f"about Rs {RS_SMOKE:.1f} a healthy run for the answers, Rs {2 * RS_SMOKE:.1f} for the two; the rest on your bill"],
    [f"{code('make incident')}, the template read, the request logs read", "reads", "Rs 0"],
    ["All of it", "what shared/prices.py prices", f"about Rs {RS_TOTAL}, plus the smokes' other calls"],
])

# ================================================================== numbers for the prose
STATS = {
    "TYPO": TYPO, "MODEL": MODEL, "OLD": OLD, "GOOD": GOOD, "BAD": BAD, "FIX": FIX, "INHERITED": INHERITED,
    "N_RUN": str(N_RUN), "N_SMOKES": str(N_SMOKES), "N_SKIPPED": str(len(SKIPPED)), "N_TESTS": str(N_TESTS),
    "N_RECIPE_TESTS": str(N_RECIPE_TESTS), "N_ROWS": str(N_ROWS), "N_ISO": str(N_ISO), "N_SETTINGS": str(N_SETTINGS),
    "RS_GATE": str(RS_GATE), "RS_ANSWER": f"{RS_ANSWER:.2f}", "N_SMOKE_ANSWERS": str(N_SMOKE_ANSWERS),
    "RS_SMOKE": f"{RS_SMOKE:.1f}", "RS_TOTAL": str(RS_TOTAL), "RED_WHY": html.escape(RED_WHY),
    "LINE_GATE": str(LINE["gate"]), "LINE_PG": str(LINE["promote-gated"]), "LINE_SD": str(LINE["smoke-deployed"]),
    "LINE_INC": str(LINE["incident"]), "SLM_REGION": SLM_REGION,
    "CF_PANEL": CF_PANEL, "SMOKES_TABLE": SMOKES_TABLE, "COST_TABLE": COST_TABLE,
    "NEXT_TITLE": html.escape(NEXT), "TITLE": html.escape(NAME),
}


def subst(text: str) -> str:
    """Every %%NAME%% in a part: a window, a table or a number computed above."""
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {N_SMOKES} smokes ({N_RUN} run without Module 9's services), {N_SETTINGS} candidate settings, {N_TESTS} "
      f"tests | the stand-in lane: 15 commands through make's recipes, exits {''.join(map(str, CODES))}, gated at "
      f"{''.join('1' if g else '0' for g in GATED)} | release-candidate after the rollback inherits {TYPO} | two Python "
      f"cells run against stand-ins | a gate: about Rs {RS_GATE}; the run: about Rs {RS_TOTAL}")
