"""Build lesson 4.9 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Read the failures first, then attack your own pipeline. The first half reads a live eval's failing rows with
evals/triage.py: as the gate saw them and with no cause named (open coding), then the eight causes and the kit's
reading of each row, then the learner's own labels counted by cause. The second half runs evals/run_attacks.py over
evals/adversarial/attacks.jsonl: offline against the stand-in that runs rag-api's own door functions, then on the
lane, once with the guard off and once on a candidate with ARMOR=on, and the two runs side by side.

Computed here, offline, from the kit (Rs 0, no credential):
  - the interactive: run_attacks.py --offline --json, all combinations of the controls, each row's verdict and reason
    from the runner's own run() over the same stand-in (asserted equal to the JSON's outcomes);
  - make attack-offline, and make attack-offline OFF=armor_prompt, as the kit prints them;
  - one attack row as python -m json.tool prints it; the table of the set; the eight causes from triage.TAXONOMIES;
  - the kit's reading of its own triage fixture (evals/tests/test_triage.py: run_eval.live() over a stub that fails
    twelve ways), written once with DOCUMIND_EVAL_PASSAGES=1 and once without, and the template line's shape;
  - the doors cell (step 8) and the reports cell (step 11), run against the stand-in served on a local port, the
    second over two reports the runner's own live path wrote there (guard off, then on);
  - the kit's tests, evals/tests/test_triage.py and test_attacks.py; make candidate's and the untag's shapes.
Recorded from the author's lane with pb.recorded(): the two eval reports, the three triage views of them, both attack
runs and their comparison (RUN_LIST.md says how).

    python pagekit/build.py 4.9
"""
import contextlib
import html
import importlib.util
import io
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, ROOT, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "4.9"
title = ("<title>Lesson 4.9 Read the failures first, then attack your own pipeline - ten failing rows in your own words "
         "before the eight causes, then an attack set on rag-api's doors with the guard off and on | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
API = "https://documind-api-NUMBER.asia-south1.run.app"
CAND = "https://candidate---documind-api-NUMBER.asia-south1.run.app"
LITE = "gemini-3.1-flash-lite"
REPORTS = "evals/reports/live49.json evals/reports/cand49.json"
SHEET = "evals/reports/triage49.csv"
ATTACK_REPORTS = "evals/reports/attacks_off.json evals/reports/attacks_on.json"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the attack panel: six controls as toggles, fifteen rows, one row's detail */
.ak-ctl{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin:0 0 10px;}
.ak-btn{display:flex;justify-content:space-between;align-items:center;gap:6px;font:inherit;font-size:12.5px;text-align:left;color:var(--navy);background:var(--teal-light);border:2px solid var(--teal);border-radius:10px;padding:6px 10px;cursor:pointer;min-height:max(44px,var(--touch));min-width:0;-webkit-tap-highlight-color:transparent;}
.ak-btn b{font-family:var(--mono);font-size:12px;min-width:0;overflow-wrap:anywhere;}
.ak-state{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--teal-dark);}
.ak-btn[aria-pressed="false"]{background:#fef2f2;border:2px dashed #ef4444;}
.ak-btn[aria-pressed="false"] .ak-state{color:#991b1b;}
.ak-sum{font-family:var(--mono);font-size:12.5px;line-height:1.5;color:var(--navy);background:var(--card);border:1px solid var(--border);border-radius:10px;padding:6px 10px;margin:0 0 8px;overflow-wrap:anywhere;}
.ak-row{display:grid;grid-template-columns:56px minmax(0,1fr) auto;gap:4px 8px;align-items:center;width:100%;font:inherit;font-size:12.5px;line-height:1.35;text-align:left;color:var(--slate);background:var(--card);border:1px solid var(--border);border-radius:9px;padding:5px 8px;margin:0 0 4px;cursor:pointer;min-height:max(40px,var(--touch));-webkit-tap-highlight-color:transparent;}
.ak-row[aria-pressed="true"]{border:2px solid var(--cyan);}
.ak-id{font-family:var(--mono);font-weight:700;color:var(--navy);}
.ak-what{min-width:0;overflow-wrap:anywhere;}
.ak-v{font-family:var(--mono);font-size:11px;padding:3px 7px;border-radius:6px;white-space:nowrap;}
.v-held{background:#d1fae5;color:#065f46;}.v-open{background:#fee2e2;color:#991b1b;}
.ak-detail{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:10px 12px;margin:10px 0 0;font-size:var(--small-size);line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.ak-detail h5{font-family:var(--mono);font-size:12.5px;color:var(--navy);margin:0 0 4px;}
.ak-detail p{margin:0 0 6px;font-size:var(--small-size);}
.ak-q{font-style:italic;color:var(--navy);}
.ak-out{font-weight:700;color:var(--navy);}
.ak-btn:active,.ak-row:active{transform:scale(.98);}
@media (hover:hover) and (pointer:fine){.ak-btn:hover,.ak-row:hover{border-color:var(--cyan);}}
@media (max-width: 640px){.ak-ctl{grid-template-columns:repeat(2,minmax(0,1fr));}.ak-row{grid-template-columns:52px minmax(0,1fr);}.ak-v{grid-column:2;justify-self:start;white-space:normal;}}
@media (forced-colors: active){.ak-btn,.ak-row,.ak-v{border:1px solid CanvasText;}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson reads acme's answers, pools and citations by the kit's own chunk ids, so point acme at its index "
         "for the duration and put the pin back at the end."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head; step 8 uses both, and the outsider's token besides.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)

# ------------------------------------------------------------------ verbatim kit excerpts
RE_, TRI, RA, EV = "evals/run_eval.py", "evals/triage.py", "evals/run_attacks.py", "mk/evaluation.mk"
EXCERPTS = {
    "passages_switch": ("evals/run_eval.py - live(): the switch, read once every row has been asked",
                        block(RE_, "    # DOCUMIND_EVAL_PASSAGES=1: each answerable row's pool read again", n=3)),
    "passage_checks": ("evals/run_eval.py - passage_checks(): each answerable row's pool read again, its quotes and anchors looked for in it",
                       block(RE_, "def passage_checks(", end="def passage_info(")),
    "failures": ("evals/triage.py - failures(): every record the gate did not pass, then each outsider who was not refused",
                 block(TRI, "def failures(", end="def _flat(")),
    "triage_mk": ("mk/evaluation.mk - triage: one script, the standard library, Rs 0",
                  block(EV, "# Read the failures first (lesson 4.9)", end="# The attack set on rag-api's doors")),
    "template": ("evals/triage.py - write_template(): an empty note and an empty class a row, and never over a file",
                 block(TRI, "def write_template(", end="def read_labels(")),
    "taxonomy": ("evals/triage.py - TAXONOMIES: each cause as a name, what it means, its lever, its lessons, what catches it and what a report can tell",
                 block(TRI, "TAXONOMIES = {", n=6) + "\n        ...\n" + block(TRI, '        ("row", "the golden row or the gate', end="COLUMNS = (")),
    "reading": ("evals/triage.py - reading(): the cause the evidence decides, in this order, or why it decides none",
                block(TRI, "def reading(", end="# ------------------------------------------------------------------ what is printed")),
    "show_counts": ("evals/triage.py - show_counts(): each cause counted with its lever, and your labels beside the kit's readings",
                    block(TRI, "def show_counts(", end="def main(")),
    "controls": ("evals/run_attacks.py - CONTROLS: what holds a row, where it lives in the kit, and the lesson that shows it",
                 block(RA, "CONTROLS = {", end='DOORS = {"/v1/query"')),
    "lift": ("evals/run_attacks.py - lift(): the stand-in runs rag-api's own door functions, as written",
             block(RA, "def lift(", end="def kit_constant(")),
    "verdict": ("evals/run_attacks.py - verdict(): held or open, FAILED for a structural row, LEAKED whatever the kind",
                block(RA, "def verdict(", end="# ------------------------------------------------------------------ a run")),
    "attack_offline_mk": ("mk/evaluation.mk - attack-offline: the stand-in, no credentials, Rs 0",
                          block(EV, "# The attack set on rag-api's doors (lesson 4.9", end="# The attack set against your lane")),
    "attack_eval_mk": ("mk/evaluation.mk - attack-eval: your lane, with the two tokens make eval-live mints",
                       block(EV, "# The attack set against your lane")),
    "summary": ("evals/run_attacks.py - summary(): what fails a run, and the rate per attack and language",
                block(RA, "def summary(", end="def _rate(")),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["passages_switch"].rstrip().endswith('if os.environ.get("DOCUMIND_EVAL_PASSAGES") == "1" else None'), E["passages_switch"]
assert E["passage_checks"].rstrip().endswith('"must_retrieve_recall": found / asked if asked else None}'), E["passage_checks"][-90:]
assert E["failures"].rstrip().endswith("    return out") and "rep.get(\"isolation\")" in E["failures"]
assert E["triage_mk"].rstrip().endswith("$(if $(LABELS),--labels $(LABELS),)"), E["triage_mk"][-90:]
assert E["template"].rstrip().endswith('_flat(rec.get("answer"), 200), evidence(x), "", ""])') and "never overwrites" in E["template"]
assert E["taxonomy"].rstrip().endswith("}") and '"no: a person\'s label"' in E["taxonomy"]
assert E["reading"].rstrip().endswith('    return None, "the evidence does not decide it"'), E["reading"][-90:]
assert E["show_counts"].rstrip().endswith("    return lines")
assert E["controls"].rstrip().endswith("}") and E["controls"].count('": "') == 6
assert E["lift"].rstrip().endswith("    return _LIFTED[(rel, names)]")
assert E["verdict"].rstrip().endswith('return held, "held" if held else ("FAILED" if row["kind"] == "structural" else "open")')
assert E["attack_offline_mk"].rstrip().endswith("$(if $(SURFACES),--surfaces $(SURFACES),))"), E["attack_offline_mk"][-90:]
assert E["attack_eval_mk"].rstrip().endswith("$(if $(SURFACES),--surfaces $(SURFACES),)") and "attack-eval: guard-project" in E["attack_eval_mk"]
assert E["summary"].rstrip().endswith('"rates": rates}')
fill = filler(EXCERPTS, window)


# ------------------------------------------------------------------ the kit's modules, loaded from their files
def load(name: str, rel: str):
    """One kit file as a module, under a name of this build's own."""
    spec = importlib.util.spec_from_file_location(name, KIT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


for k in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "DOCUMIND_USER_EMAIL", "DOCUMIND_OUTSIDER_EMAIL",
          "DOCUMIND_FORGE_EMAIL", "DOCUMIND_EVAL_PASSAGES"):
    os.environ.pop(k, None)
ra = load("lesson49_run_attacks", RA)
tt = load("lesson49_test_triage", "evals/tests/test_triage.py")   # the kit's own triage fixture, and triage.py with it
tri, rv = tt.tri, tt.tri.run_eval

# ------------------------------------------------------------------ the attack set: its rows and its registries
# This lesson is rag-api's doors. Lesson 10.8 (kit PR 10.8-C) appended rows on the chat, Desk and peer surfaces to the
# same file and new controls to the runner; --surfaces api keeps this page to its own rows, which are unchanged.
ROWS = ra.select(ra.load_set(), ["api"])
assert ra.check_set(ROWS, rv.load_corpus()) == []
KIND_N = Counter(r["kind"] for r in ROWS)
CONTROLS = ra.controls_of(ROWS)
assert CONTROLS == ["roster", "iap_identity", "filter_check", "tenant_filter", "armor_prompt", "refusal_rule"], CONTROLS
assert {r["door"] for r in ROWS} == {"/v1/query", "/v1/stream", "/v1/passages"} and {r["surface"] for r in ROWS} == {"api"}
assert sorted(KIND_N.items()) == [("behavioural", 5), ("plain", 1), ("structural", 9)], KIND_N
LANG_N = Counter(r["lang"] for r in ROWS)
assert set(ra.LANGS) == {"en", "hinglish"} and LANG_N["hinglish"] == 1
src48 = (ROOT / "lessons" / "04-evals-safety" / "4.8-dlp-guard-audit" / "build.py").read_text(encoding="utf-8")
assert all(r["question"] in src48 for r in ROWS[:4]) and all(r["from"].startswith("4.8 step 6") for r in ROWS[:4])
MODEL_ROWS = [r for r in ROWS if r["caller"] == "member" and not r.get("filters") and r["door"] != "/v1/passages"]
SCREENED = [r for r in ROWS if r["caller"] == "member" and not r.get("filters")]
assert len(MODEL_ROWS) == 8 and len(SCREENED) == 9 and "eight of the fifteen at most" in ra.__doc__
ARMOR_CALLS = len(SCREENED) + len(MODEL_ROWS)
assert "an injected document" in ra.__doc__ and "--repeat" not in (KIT / RA).read_text(encoding="utf-8")
GOLD = rv.load_golden()
N_GOLDEN, N_ANS = len(GOLD), sum(r["answerable"] for r in GOLD)
N_ISO = sum(r["shape"] == "isolation" for r in GOLD)
assert (N_GOLDEN, N_ANS, N_ISO) == (65, 47, 11), (N_GOLDEN, N_ANS, N_ISO)
auth = (KIT / "services" / "rag-api" / "auth.py").read_text(encoding="utf-8")
assert 'AUTH_MODE = os.environ.get("AUTH_MODE", "iap")' in auth
ROW13 = next(r for r in ROWS if r["id"] == "atk-13")
assert ROW13["filters"] == {"tenant_id": "globex"} and ROW13["expect"] == ["rejected"]
ROW15 = next(r for r in ROWS if r["id"] == "atk-15")
assert ROW15["caller"] == "forged" and ROW15["control"] == ["iap_identity"]

# ------------------------------------------------------------------ offline: the runner, as make attack-offline runs it
TMP = Path(tempfile.mkdtemp(prefix="lesson49-"))
(TMP / "evals" / "reports").mkdir(parents=True)
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}


def kit_cli(*args: str, cwd: Path = KIT) -> tuple:
    """Run one kit command with this interpreter, from deploy/, and return its exit code and what it printed."""
    r = subprocess.run([sys.executable, *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env=ENV)
    return r.returncode, r.stdout, r.stderr


EVMK = (KIT / EV).read_text(encoding="utf-8")
ATTACK_RECIPE = "$(PY) evals/run_attacks.py $(if $(COMPARE),--compare $(COMPARE),--offline $(if $(OFF),--off $(OFF),) $(if $(SURFACES),--surfaces $(SURFACES),))"
TRIAGE_RECIPE = "$(PY) evals/triage.py $(REPORT) $(if $(TEMPLATE),--template $(TEMPLATE),) $(if $(CLASSES),--classes,) $(if $(LABELS),--labels $(LABELS),)"
assert f"attack-offline:\n\t{ATTACK_RECIPE}\n" in EVMK and f"triage:\n\t{TRIAGE_RECIPE}\n" in EVMK
assert re.search(r"^PY\s+\?= python$", (KIT / "Makefile").read_text(encoding="utf-8"), re.M)
rc, OFFLINE_OUT, err = kit_cli(RA, "--offline")
assert rc == 0 and not err.strip(), (rc, err[-600:])
for line in ("[PASS] the set", "[PASS] all on", "[PASS] vacuity", "Every row is held, and every structural row by the control it names."):
    assert line in OFFLINE_OUT, line
rc, OFF_ARMOR_OUT, err = kit_cli(RA, "--offline", "--off", "armor_prompt")
assert rc == 0 and "controls off: armor_prompt" in OFF_ARMOR_OUT and not err.strip(), err[-600:]
assert re.search(r"atk-04 .* answered +open", OFF_ARMOR_OUT) and "guard: 0 of 15 rows" in OFF_ARMOR_OUT, OFF_ARMOR_OUT
rc, _, err = kit_cli(RA, "--offline", "--json", str(TMP / "matrix.json"))
assert rc == 0, err[-600:]
MATRIX = json.loads((TMP / "matrix.json").read_text(encoding="utf-8"))
assert list(MATRIX["controls"]) == CONTROLS and [r["id"] for r in MATRIX["rows"]] == [r["id"] for r in ROWS]
COMBOS = ["+".join(c) for n in range(len(CONTROLS) + 1) for c in itertools.combinations(CONTROLS, n)]
assert sorted(MATRIX["configs"]) == sorted(COMBOS) and len(COMBOS) == 2 ** len(CONTROLS)

# the same combinations through the runner's own run(), in this process: each row's verdict word and reason, and the
# JSON's outcome and held asserted equal to them, so the panel reads one run of the kit, not two that might differ
OUTS, VERDS, WHYS, CONFIGS = [], [], [""], {}
OPENS = {}
for key in COMBOS:
    off = [c for c in key.split("+") if c]
    recs = ra.run(ROWS, ra.StandIn(ROWS, off), ra.STAND_IN_IDS)
    cells = []
    for r in recs:
        want = MATRIX["configs"][key][r["id"]]
        assert (want["outcome"], want["held"]) == (r["outcome"], r["held"]), (key, r["id"], want, r["outcome"], r["held"])
        assert r["held"] is not None
        for lst, v in ((OUTS, r["outcome"]), (VERDS, r["verdict"]), (WHYS, r["why"])):
            if v not in lst:
                lst.append(v)
        cells.append([OUTS.index(r["outcome"]), 1 if r["held"] else 0, VERDS.index(r["verdict"]), WHYS.index(r["why"])])
    CONFIGS[key] = cells
    OPENS[key] = [r["id"] for r in recs if r["held"] is False]
assert OPENS[""] == []
assert OPENS["roster"] == ["atk-10", "atk-11", "atk-12", "atk-15"] and OPENS["iap_identity"] == ["atk-15"]
assert OPENS["filter_check"] == ["atk-13", "atk-14"] and OPENS["tenant_filter"] == ["atk-01", "atk-07", "atk-08", "atk-09"]
assert OPENS["armor_prompt"] == ["atk-04"] and OPENS["refusal_rule"] == []
TF_OFF = {r["id"]: r for r in ra.run(ROWS, ra.StandIn(ROWS, ["tenant_filter"]), ra.STAND_IN_IDS)}
assert TF_OFF["atk-01"]["verdict"] == "LEAKED" and "cited from another tenant" in TF_OFF["atk-01"]["why"]
DEEP = [r["id"] for r in ROWS if r["kind"] != "plain" and len(r["control"]) > 1
        and all(r["id"] not in OPENS[c] for c in r["control"])]
assert DEEP == ["atk-02", "atk-03", "atk-05", "atk-06"], DEEP
assert f"held by more than one control, each alone enough: {DEEP[0]} (armor_prompt or refusal_rule)" in OFFLINE_OUT
assert "\u2014" not in json.dumps(WHYS + [r["note"] + r["question"] for r in ROWS], ensure_ascii=False)


def ids(xs: list, last: str = " and ") -> str:
    """atk-10, atk-11 and atk-12, as the prose names them."""
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + last + xs[-1]


def either(xs: list) -> str:
    """blocked, withheld or refused: a row's outcomes, as the prose names them."""
    return ids(xs, " or ")


WIDGET = {
    "controls": [{"name": c, "text": ra.CONTROLS[c]} for c in CONTROLS],
    "rows": [{"id": r["id"], "kind": r["kind"], "attack": r["attack"], "door": r["door"], "caller": r["caller"],
              "lang": r["lang"], "control": r["control"], "expect": r["expect"], "question": r["question"],
              "filters": json.dumps(r["filters"]) if r.get("filters") else "", "note": r["note"]} for r in ROWS],
    "outcomes": OUTS, "verdicts": VERDS, "whys": WHYS, "configs": CONFIGS,
    "n": {"structural": KIND_N["structural"], "behavioural": KIND_N["behavioural"]},
}

# ------------------------------------------------------------------ one row, as python -m json.tool prints it
LINE13 = (KIT / "evals" / "adversarial" / "attacks.jsonl").read_text(encoding="utf-8").splitlines()[12]
assert json.loads(LINE13)["id"] == "atk-13"
r = subprocess.run([sys.executable, "-m", "json.tool"], input=LINE13 + "\n", capture_output=True, text=True, encoding="utf-8", env=ENV)
assert r.returncode == 0 and r.stdout.startswith('{\n    "id": "atk-13",'), r.stdout[:80]
ROW13_TOOL = r.stdout

# ------------------------------------------------------------------ triage: the kit's own fixture, read three ways
FX = TMP / "fixture"
(FX / "evals" / "reports").mkdir(parents=True)
with contextlib.chdir(FX):
    live_fx = tt.write_report("evals/reports/live49.json")
    cand_fx = tt.write_report("evals/reports/cand49.json", passages_on=False)


def triage(*argv: str) -> tuple:
    """triage.py's main() over the fixture, from the fixture's folder: its exit code, stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.chdir(FX), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = tri.main(list(argv))
    return code, out.getvalue(), err.getvalue()


rc, FX_ROWS_OUT, _ = triage(live_fx)
assert rc == 0 and "12 failing rows of live49, as the gate saw them" in FX_ROWS_OUT
for word in ("retrieval", "omission", "unsupported", "overreach", "infra", "lever", "caught by"):
    assert word not in FX_ROWS_OUT, word     # no cause before the notes (version, isolation and row are also shape words)
assert "Before you read the causes" in FX_ROWS_OUT
OUTSIDER_EXPECT = re.search(r"iso-01  outsider .*\n      asked .*\n      expected  (an answer)", FX_ROWS_OUT)
assert OUTSIDER_EXPECT, "the outsider's row: triage's open view names the member's expectation"   # a kit gap the page names
rc, TEMPLATE_OUT, _ = triage(live_fx, cand_fx, "--template", SHEET)
assert rc == 0 and TEMPLATE_OUT.startswith(f"  24 failing rows of live49, cand49 written to {SHEET}: write a one-line note"), TEMPLATE_OUT
rc, _, err = triage(live_fx, cand_fx, "--template", SHEET)
assert rc == 2 and "never overwrites a sheet" in err
TEMPLATE_SHAPE = re.sub(r"^  24 failing rows", "  N failing rows", TEMPLATE_OUT)
with open(FX / SHEET, encoding="utf-8", newline="") as f:
    SHEET_HEAD = f.readline().strip()
assert SHEET_HEAD == ",".join(tri.COLUMNS)
FS_POOL = tri.failures(tri.load_reports([str(FX / live_fx)]))
FS_NOPOOL = {(f["id"], f["leg"]): f for f in tri.failures(tri.load_reports([str(FX / cand_fx)]))}
assert [(f["id"], f["leg"]) for f in FS_POOL] == list(FS_NOPOOL)
FX_TABLE, POOL_DECIDED, NOPOOL_DECIDED = [], 0, 0
for f in FS_POOL:
    (c1, why1), (c2, why2) = tri.reading(f), tri.reading(FS_NOPOOL[(f["id"], f["leg"])])
    POOL_DECIDED += bool(c1)
    NOPOOL_DECIDED += bool(c2)
    FX_TABLE.append((f["id"], f["leg"], f["record"].get("why") or "failed", c1, why1, c2, why2))
assert (len(FS_POOL), POOL_DECIDED, NOPOOL_DECIDED) == (12, 12, 7), (len(FS_POOL), POOL_DECIDED, NOPOOL_DECIDED)
NOPOOL_WHY = "no pool was read: make eval-live with DOCUMIND_EVAL_PASSAGES=1 tells retrieval from omission"
assert sum(w2 == NOPOOL_WHY for *_, w2 in FX_TABLE) == 5 and "row" not in {t[3] for t in FX_TABLE}
JN01 = next(t for t in FX_TABLE if t[0] == "jn-01")
assert JN01[2].startswith("answered without [") and JN01[3] == "isolation"    # a later why hid the citation; the kit finds it

# the eight causes, as --classes prints them, from the one table the tool reads
TAX = tri.TAXONOMIES["rag"]
assert [c[0] for c in TAX] == ["retrieval", "version", "omission", "unsupported", "overreach", "isolation", "infra", "row"]
LESSONS_OF = {c[0]: c[3] for c in TAX}
assert "kappa" not in (KIT / TRI).read_text(encoding="utf-8")

# ------------------------------------------------------------------ the doors cell and the reports cell, against the stand-in
class Serve(BaseHTTPRequestHandler):
    """The stand-in as an HTTP server on a local port: the runner's live path and the page's cells call it."""
    lane = None

    def log_message(self, *a):
        """Print nothing per request."""

    def do_POST(self):
        """Hand the request to the stand-in and send back what it answered."""
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        headers = {k.lower(): v for k, v in self.headers.items()}
        status, ctype, raw, _ = type(self).lane.send(self.path, body, headers)
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


srv = ThreadingHTTPServer(("127.0.0.1", 0), Serve)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_address[1]}"

PY_DOORS = '''import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
API, MEMBER = os.environ["API"], f"documind-ui-sa@{os.environ['PROJECT']}.iam.gserviceaccount.com"


def post(body, token, email=None):
    """POST one body to /v1/query with this token, and this x-user-email if given; return the status and the detail."""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    if email:
        headers["x-user-email"] = email
    req = urllib.request.Request(API + "/v1/query", data=json.dumps(body).encode(), method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read()).get("answer", "")[:70]
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}").get("detail")


filtered = {"query": "What termination notice does the agreement set?", "tenant_id": "acme", "top_k": 6,
            "filters": {"tenant_id": "globex"}}
print("atk-13, the member, a body filter naming globex:", *post(filtered, os.environ["TOKEN"]))
plain = {"query": "What is the notice period for a confirmed E3?", "tenant_id": "acme", "top_k": 6}
print("atk-15, the outsider's token, the member's email:", *post(plain, os.environ["OUTSIDER"], MEMBER))'''
assert json.loads(re.search(r"filtered = (\{.*?\})\n", PY_DOORS, re.S).group(1).replace("\n", " ")) == ra.request_of(ROW13)
assert ROW15["question"] in PY_DOORS and ra.request_of(ROW15) == {"query": ROW15["question"], "tenant_id": "acme", "top_k": 6}

PY_READ = '''import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
runs = [json.load(open(f"evals/reports/attacks_{x}.json", encoding="utf-8")) for x in ("off", "on")]
off, on = runs
print(f"{off['label']} -> {on['label']}: the same rows {off['rows_sha256'] == on['rows_sha256']}; "
      f"a token in either report {any('Bearer' in json.dumps(r) for r in runs)}")
after = {r["id"]: r for r in on["records"]}
for r in off["records"]:
    if r["kind"] == "structural":
        continue
    s = after[r["id"]]
    print(f"\\n{r['id']} {r['attack']} {r['lang']}: {r['outcome']} -> {s['outcome']} ({s['verdict']})")
    for x in (r, s):
        said = " ".join((x["answer"] or x["detail"] or x["why"] or "-").split())
        print(f"  {x['status']}  {said[:92]}")'''

CELL_ENV = {**ENV, "PROJECT": PROJ, "API": URL, "TOKEN": "stand-in:member", "OUTSIDER": "stand-in:outsider"}
for k in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT"):
    CELL_ENV.pop(k, None)


def run_cell(code: str, cwd: Path) -> str:
    """One page cell, as the learner pastes it, with this interpreter: what it printed; it must not fail."""
    r = subprocess.run([sys.executable, "-"], input=code, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       env=CELL_ENV)
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stderr[-1200:])
    return r.stdout


Serve.lane = ra.StandIn(ROWS, ["armor_prompt"])          # the live revision: ARMOR=off; neither request reaches the screen
DOORS_OUT = run_cell(PY_DOORS, TMP)
assert DOORS_OUT == ("atk-13, the member, a body filter naming globex: 400 unknown filter key(s) tenant_id; allowed: doc_type, kind\n"
                     "atk-15, the outsider's token, the member's email: 403 not a member of this tenant\n"), DOORS_OUT

REPORT_OF = {}
for name, off, label in (("off", ["armor_prompt"], "guard off"), ("on", [], "guard on")):
    Serve.lane = ra.StandIn(ROWS, off)
    path = TMP / "evals" / "reports" / f"attacks_{name}.json"
    with patch.dict(os.environ, {"DOCUMIND_ID_TOKEN": "stand-in:member", "DOCUMIND_OUTSIDER_TOKEN": "stand-in:outsider"}), \
            contextlib.redirect_stdout(io.StringIO()):
        assert ra.live(ROWS, URL, str(path), label) == 0, name
    REPORT_OF[name] = json.loads(path.read_text(encoding="utf-8"))
assert REPORT_OF["off"]["guard_seen"] == 0 and REPORT_OF["on"]["guard_seen"] == 5
assert [x["rate"] for x in REPORT_OF["off"]["rates"] if (x["attack"], x["lang"]) == ("all", "all")] == [0.2]
with contextlib.redirect_stdout(io.StringIO()) as buf:
    assert ra.compare(str(TMP / "evals" / "reports" / "attacks_off.json"), str(TMP / "evals" / "reports" / "attacks_on.json")) == 0
assert "atk-02  refused -> blocked" in buf.getvalue() and re.search(r"structural rows held +9/9 +9/9", buf.getvalue())
READ_OUT = run_cell(PY_READ, TMP)
assert READ_OUT.startswith("guard off -> guard on: the same rows True; a token in either report False\n"), READ_OUT[:200]
srv.shutdown()
srv.server_close()

# ------------------------------------------------------------------ the kit's tests, offline
TESTS = {}
for name in ("test_triage.py", "test_attacks.py"):
    rc, out, err = kit_cli("-m", "unittest", "discover", "-s", "evals/tests", "-p", name)
    m = re.search(r"\nRan (\d+) tests? in [\d.]+s\n\nOK\s*$", err)
    assert rc == 0 and m, (name, err[-800:])
    TESTS[name] = int(m.group(1))
assert TESTS == {"test_triage.py": 13, "test_attacks.py": 39}, TESTS       # 10.8-C extended test_attacks.py (10.8-C)

# ------------------------------------------------------------------ make candidate and the untag, as make echoes them
MK = (KIT / "Makefile").read_text(encoding="utf-8")
recipe = lambda name: MK[MK.index(f"\n{name}:") + 1:].split("\n\n", 1)[0]      # noqa: E731
CAND_RECIPE = recipe("candidate")
env_part = CAND_RECIPE.split('"^|^', 1)[1].split("$(if", 1)[0]
PAIRS = re.findall(r"([A-Z_]+)=\$\(([A-Z_]+)\)", env_part)
DEFAULTS = {v: re.search(rf"^{v} +\?= *(\S*)$", MK, re.M).group(1) for _, v in PAIRS}
assert len(PAIRS) == 11 and all(k == v for k, v in PAIRS) and all(DEFAULTS.values()), (PAIRS, DEFAULTS)
assert DEFAULTS["ARMOR"] == "off" and DEFAULTS["SEMANTIC_CACHE"] == "off" and DEFAULTS["GENERATOR_MODEL"] == "gemini-3.6-flash"
assert "$(if $(GENERATOR_LOCATION),,--remove-env-vars GENERATOR_LOCATION)" in CAND_RECIPE
ECHO_REV = re.search(r'echo ">> candidate revision: \$\$REV (\(deploy/\.candidate-revision - [^"]+\))"', recipe("record-candidate")).group(1)
ECHO_CAND = re.search(r'echo ">> candidate: https://candidate---documind-api-\$\$NUMBER\.\$\(REGION\)\.run\.app ([^"]+)"', CAND_RECIPE).group(1)


def candidate_shape(**over: str) -> str:
    """make candidate's echo with these overrides and the Makefile's defaults, then make's two >> lines."""
    env = "^|^" + "|".join(f"{k}={over.get(v, DEFAULTS[v])}" for k, v in PAIRS)
    return (f"gcloud run services update documind-api --region asia-south1 --project {PROJ} --no-traffic --tag candidate \\\n"
            f"  --update-env-vars \"{env}\" --remove-env-vars GENERATOR_LOCATION\n...\n"
            f">> candidate revision: documind-api-000NN-yyy {ECHO_REV}\n>> candidate: {CAND} {ECHO_CAND}\nCAND={CAND}\n")


assert "$${API:-$$AUD}" in recipe("eval-live") and "$${API:-$$AUD}" in E["attack_eval_mk"]
assert "DOCUMIND_FORGE_EMAIL=$${DOCUMIND_FORGE_EMAIL:-documind-ui-sa@$(PROJECT).iam.gserviceaccount.com}" in E["attack_eval_mk"]
SETUP_TXT = setup_section()
assert 'otok() { gcloud auth print-identity-token --include-email --audiences="$API"' in SETUP_TXT
assert 'tok()  { gcloud auth print-identity-token --include-email --audiences="$1"' in SETUP_TXT

# ------------------------------------------------------------------ the cells
def heredoc(code: str, prefix: str = "") -> str:
    """A Python cell wrapped so it pastes into bash."""
    return f"{prefix}python - <<'PY'\n{code}\nPY"


UNTAG = ('gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate\n'
         'rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag (lesson 4.4)\n'
         'curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"')
CELLS = {
    "eval_live": 'DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" REPORT=evals/reports/live49.json',
    "cand_lite": (f'make candidate PROJECT="$PROJECT" GENERATOR_MODEL={LITE} RAG_MODEL_BASE={LITE}\n'
                  'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"'),
    "eval_cand": 'DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" API="$CAND" REPORT=evals/reports/cand49.json',
    "untag": UNTAG,
    "triage": f'make triage REPORT="{REPORTS}"',
    "template": f'make triage REPORT="{REPORTS}" TEMPLATE={SHEET}',
    "classes": f'make triage REPORT="{REPORTS}" CLASSES=1',
    "labels": f'make triage REPORT="{REPORTS}" LABELS={SHEET}',
    "row": "sed -n 13p evals/adversarial/attacks.jsonl | python -m json.tool",
    "offline": "make attack-offline",
    "off_armor": "make attack-offline OFF=armor_prompt",
    "doors": heredoc(PY_DOORS, prefix='TOKEN="$(tok "$API")" OUTSIDER="$(otok)" '),
    "attack_off": 'make attack-eval PROJECT="$PROJECT" REPORT=evals/reports/attacks_off.json LABEL="guard off"',
    "cand_armor": ('make candidate PROJECT="$PROJECT" ARMOR=on\n'
                   'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"'),
    "attack_on": 'make attack-eval PROJECT="$PROJECT" API="$CAND" REPORT=evals/reports/attacks_on.json LABEL="guard on"',
    "compare": f'make attack-offline COMPARE="{ATTACK_REPORTS}"',
    "read": heredoc(PY_READ),
    "tests": ('python -m unittest discover -s evals/tests -p "test_triage.py" 2>&1 | tail -3\n'
              'python -m unittest discover -s evals/tests -p "test_attacks.py" 2>&1 | tail -3'),
}
CELL_LABELS = {
    "eval_live": "run in the operator shell, in the kit (every golden row to the live revision, each pool read again: about ten minutes)",
    "cand_lite": "run in the operator shell, in the kit (a revision on the cheap model, with no traffic)",
    "eval_cand": "run in the operator shell, in the kit (the same rows to the candidate)",
    "untag": "run in the operator shell, in the kit (the candidate's tag and its recorded name removed)",
    "triage": "run in the operator shell, in the kit (reads the two reports; no network)",
    "template": "run in the operator shell, in the kit (writes the sheet; never over a file)",
    "classes": "run in the operator shell, in the kit (only after your ten notes)",
    "labels": "run in the operator shell, in the kit (your filled sheet, counted)",
    "row": "run in the operator shell, in the kit (one row of the set, laid out)",
    "offline": "run in the operator shell, in the kit (the stand-in; no credentials, Rs 0)",
    "off_armor": "run in the operator shell, in the kit (the stand-in with Model Armor off)",
    "doors": "run in the operator shell, in the kit (two requests, both refused before any retrieval)",
    "attack_off": "run in the operator shell, in the kit (the set against the live revision)",
    "cand_armor": "run in the operator shell, in the kit (a revision with ARMOR=on and no traffic)",
    "attack_on": "run in the operator shell, in the kit (the set against the candidate)",
    "compare": "run in the operator shell, in the kit (the two reports side by side; no network)",
    "read": "run in the operator shell, in the kit (reads the two reports; changes nothing)",
    "tests": "run in the operator shell, in the kit (the kit's own tests for both tools; no network)",
}
LANE = "(the author's lane: your rows, answers and counts are yours)"
TIME = re.compile(r"Ran (\d+) tests in [\d.]+s")
OUT = {
    "eval_live": ("(the author's lane: the live revision's rows; your rates, rows and pools are yours)", pb.recorded(LESSON, "eval_live.txt")),
    "cand_lite": ("shape (make echoes the gcloud line; gcloud's own progress lines are left out; the two >> lines are make's)",
                  candidate_shape(GENERATOR_MODEL=LITE, RAG_MODEL_BASE=LITE)),
    "eval_cand": ("(the author's lane: the candidate's rows; yours are yours)", pb.recorded(LESSON, "eval_cand.txt")),
    "untag": ("shape (gcloud's traffic table first)", "...\nthe candidate URL now: HTTP 404\n"),
    "triage": (LANE, pb.recorded(LESSON, "triage_rows.txt")),
    "template": ("shape (make's echo, then the tool's one line; N is your count of failing rows)",
                 TRIAGE_RECIPE.replace("$(PY)", "python").replace("$(REPORT)", REPORTS)
                 .replace("$(if $(TEMPLATE),--template $(TEMPLATE),)", f"--template {SHEET}")
                 .replace("$(if $(CLASSES),--classes,)", "").replace("$(if $(LABELS),--labels $(LABELS),)", "").rstrip()
                 + "\n" + TEMPLATE_SHAPE),
    "classes": (LANE, pb.recorded(LESSON, "triage_classes.txt")),
    "labels": ("(the author's lane and the author's labels: yours are yours)", pb.recorded(LESSON, "triage_labels.txt")),
    "row": ("(the kit's row, laid out when this page was built)", ROW13_TOOL),
    "offline": ("(make attack-offline, run on the kit when this page was built)", "python evals/run_attacks.py --offline\n" + OFFLINE_OUT),
    "off_armor": ("(make attack-offline OFF=armor_prompt, run on the kit when this page was built)",
                  "python evals/run_attacks.py --offline --off armor_prompt\n" + OFF_ARMOR_OUT),
    "doors": ("(this cell against the stand-in, served on a local port when this page was built: the kit's own check_filters, verify_iap and enforce_membership answered)", DOORS_OUT),
    "attack_off": ("(the author's lane: the live revision; your answers and rate are yours)", pb.recorded(LESSON, "attack_off.txt")),
    "cand_armor": ("shape (make echoes the gcloud line; gcloud's own progress lines are left out; the two >> lines are make's)",
                   candidate_shape(ARMOR="on")),
    "attack_on": ("(the author's lane: the candidate with ARMOR=on; yours are yours)", pb.recorded(LESSON, "attack_on.txt")),
    "compare": ("(the author's two runs side by side; yours are yours)", pb.recorded(LESSON, "attack_compare.txt")),
    "read": ("(this cell over two reports the runner's own live path wrote against the stand-in, guard off then on; your lane's answers differ)", READ_OUT),
    "tests": ("(your times differ)", "".join(f"Ran {n} tests in N.NNNs\n\nOK\n" for n in TESTS.values())),
}
for k, (_, text) in OUT.items():
    assert "\u2014" not in text or k in ("read", "offline", "off_armor"), k
assert set(OUT) == set(CELLS) and not TIME.search(OUT["tests"][1])


def bash_window(label: str, code: str) -> str:
    """A command to paste: the label starts with bash, and the window has a copy button."""
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    """What a cell prints: the label starts with expected, and the window is read only."""
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUT.items()})


# ------------------------------------------------------------------ the tables, from the kit
def td(label: str, inner: str) -> str:
    return f'<td data-label="{label}">{inner}</td>'


def code(text: str) -> str:
    return "<code>" + html.escape(text) + "</code>"


CAUSE_ROWS = "\n".join(
    f"<tr><td><strong>{html.escape(name)}</strong></td>{td('What it means', html.escape(means))}"
    f"{td('The lever (lessons)', html.escape(lever) + ' (' + html.escape(lessons) + ')')}"
    f"{td('What can catch it', html.escape(catcher))}{td('What a report can tell', html.escape(tells))}</tr>"
    for name, means, lever, lessons, catcher, tells in TAX)
FX_ROWS = "\n".join(
    f"<tr><td><strong>{html.escape(i)}</strong>{' (outsider)' if leg == 'outsider' else ''}</td>"
    f"{td('The gate said', html.escape(why))}"
    f"{td('With the pool', '<strong>' + html.escape(c1 or 'no reading') + '</strong>: ' + html.escape(w1))}"
    f"{td('Without the pool', '<strong>' + html.escape(c2 or 'no reading') + '</strong>' + ('' if w2 == w1 else ': ' + html.escape(w2)))}</tr>"
    for i, leg, why, c1, w1, c2, w2 in FX_TABLE)
SET_ROWS = "\n".join(
    f"<tr><td><strong>{r['id']}</strong></td>{td('Door', code(r['door']))}"
    f"{td('Caller', html.escape(r['caller']) + ('' if r['lang'] == 'en' else ', ' + html.escape(r['lang'])))}"
    f"{td('Attack', html.escape(r['attack']) + (', filters ' + code(json.dumps(r['filters'])) if r.get('filters') else ''))}"
    f"{td('Kind', html.escape(r['kind']))}{td('Held by', html.escape(', '.join(r['control']) or '-'))}"
    f"{td('The row holds when the reply is', html.escape(either(r['expect'])))}</tr>"
    for r in ROWS)

# ------------------------------------------------------------------ numbers for the prose, and the rupees
PRICES = {}
exec(compile((KIT / "shared" / "prices.py").read_text(encoding="utf-8"), "prices.py", "exec"), PRICES)
TYPICAL = (2000, 300)                    # the course's typical answer (lessons 4.3, 4.4 and 11.6): 2,000 tokens in, 300 out
assert PRICES["USD_INR"] == 85 and PRICES["PRICES"][DEFAULTS["GENERATOR_MODEL"]] == (1.50, 7.50) and PRICES["PRICES"][LITE] == (0.25, 1.50)


def rs(model: str, answers: int) -> float:
    """Rupees for this many answers of the typical size, at shared/prices.py's list price."""
    usd_in, usd_out = PRICES["PRICES"][model]
    return answers * (TYPICAL[0] * usd_in + TYPICAL[1] * usd_out) / 1_000_000 * PRICES["USD_INR"]


WORDS = {5: "five", 6: "six", 8: "eight"}       # the counts the prose spells as words
RS_ANSWER, RS_LITE = rs(DEFAULTS["GENERATOR_MODEL"], 1), rs(LITE, 1)
RS_EVAL, RS_CAND = rs(DEFAULTS["GENERATOR_MODEL"], N_GOLDEN), rs(LITE, N_GOLDEN)
RS_RUN = rs(DEFAULTS["GENERATOR_MODEL"], len(MODEL_ROWS))
RS_ALL = RS_EVAL + RS_CAND + 2 * RS_RUN + RS_ANSWER
assert round(RS_EVAL) == 29 and round(RS_CAND) == 5 and round(RS_ALL) == 42, (RS_EVAL, RS_CAND, RS_ALL)

STATS = {
    "N_ATK": str(len(ROWS)), "N_DOORS": str(len({r["door"] for r in ROWS})), "N_STRUCT": str(KIND_N["structural"]),
    "N_BEH": str(KIND_N["behavioural"]), "N_PLAIN": str(KIND_N["plain"]), "N_CONTROLS": str(len(CONTROLS)),
    "N_COMBOS": str(len(COMBOS)), "N_CAUSES": str(len(TAX)), "N_GOLDEN": str(N_GOLDEN), "N_ANS": str(N_ANS),
    "N_ISO": str(N_ISO), "N_MODEL_ROWS": str(len(MODEL_ROWS)), "N_SCREENED": str(len(SCREENED)),
    "ARMOR_CALLS": str(ARMOR_CALLS),
    "OPEN_ROSTER": ids(OPENS["roster"]), "OPEN_IAP": ids(OPENS["iap_identity"]), "OPEN_FILTER": ids(OPENS["filter_check"]),
    "OPEN_TENANT": ids(OPENS["tenant_filter"]), "OPEN_ARMOR": ids(OPENS["armor_prompt"]),
    "OPEN_BOTH": ids(OPENS["armor_prompt+refusal_rule"]), "DEEP": ids(DEEP),
    "N_CAUSES_W": WORDS[len(TAX)], "N_CONTROLS_W": WORDS[len(CONTROLS)], "N_BEH_W": WORDS[KIND_N["behavioural"]],
    "PROMPT_RUN_W": WORDS[ra.PROMPT_RUN], "CAUSE_CODES": ids([code(c[0]) for c in TAX], " or "),
    "N_FX": str(len(FS_POOL)), "N_FX_POOL": str(POOL_DECIDED), "N_FX_NOPOOL": str(NOPOOL_DECIDED),
    "SHEET_HEAD": SHEET_HEAD, "T_TRIAGE": str(TESTS["test_triage.py"]), "T_ATTACKS": str(TESTS["test_attacks.py"]),
    "RS_ANSWER": f"{RS_ANSWER:.2f}", "RS_LITE": f"{RS_LITE:.2f}", "RS_EVAL": f"{RS_EVAL:.0f}", "RS_CAND": f"{RS_CAND:.0f}",
    "RS_RUN": f"{RS_RUN:.1f}", "RS_ALL": f"{RS_ALL:.0f}", "LITE": LITE,
    "L_RETRIEVAL": LESSONS_OF["retrieval"], "L_OMISSION": LESSONS_OF["omission"], "L_ROW": LESSONS_OF["row"],
    "CAUSE_ROWS": CAUSE_ROWS, "FX_ROWS": FX_ROWS, "SET_ROWS": SET_ROWS,
}
assert OPENS["armor_prompt+refusal_rule"] == ["atk-02", "atk-03", "atk-04", "atk-05", "atk-06"]

# ------------------------------------------------------------------ the panel's script
UI_JS = r"""var root = document.getElementById('ak'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var on = {}, sel = 0, cbtn = [], rbtn = [];
  D.controls.forEach(function(c){ on[c.name] = true; });
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function key(){ return D.controls.filter(function(c){ return !on[c.name]; }).map(function(c){ return c.name; }).join('+'); }
  function cell(i){ return D.configs[key()][i]; }
  function said(x){ var o = D.outcomes[x[0]], v = D.verdicts[x[2]]; return v.toLowerCase() === o ? v : v + ' (' + o + ')'; }
  D.controls.forEach(function(c){
    var b = el('button', 'ak-btn'); b.type = 'button';
    b.appendChild(el('b', '', c.name)); b.appendChild(el('span', 'ak-state', 'on'));
    b.addEventListener('click', function(){ on[c.name] = !on[c.name]; render(); });
    $('ak-ctl').appendChild(b); cbtn.push(b); });
  D.rows.forEach(function(r, i){
    var b = el('button', 'ak-row'); b.type = 'button';
    b.appendChild(el('span', 'ak-id', r.id));
    b.appendChild(el('span', 'ak-what', r.door + ' \u00b7 ' + r.caller + ' \u00b7 ' + r.attack + (r.lang !== 'en' ? ', ' + r.lang : '')));
    var v = el('span', 'ak-v'); b.appendChild(v);
    b.addEventListener('click', function(){ sel = i; render(); });
    $('ak-rows').appendChild(b); rbtn.push([b, v]); });
  function render(){
    var held = 0, open = 0, plain = '';
    cbtn.forEach(function(b, j){ var n = D.controls[j].name; b.setAttribute('aria-pressed', on[n] ? 'true' : 'false'); b.lastChild.textContent = on[n] ? 'on' : 'off'; });
    rbtn.forEach(function(p, i){
      var x = cell(i), r = D.rows[i];
      p[1].textContent = said(x); p[1].className = 'ak-v ' + (x[1] ? 'v-held' : 'v-open');
      p[0].setAttribute('aria-pressed', i === sel ? 'true' : 'false');
      p[0].setAttribute('aria-label', r.id + ', ' + r.kind + ': ' + D.outcomes[x[0]] + ', ' + D.verdicts[x[2]]);
      if (r.kind === 'structural' && x[1]) held++;
      if (r.kind === 'behavioural' && !x[1]) open++;
      if (r.kind === 'plain') plain = D.verdicts[x[2]]; });
    $('ak-sum').textContent = 'structural rows held ' + held + ' of ' + D.n.structural + (held < D.n.structural ? ': a live run exits 1' : '') +
      ' \u00b7 behavioural rows open ' + open + ' of ' + D.n.behavioural + ' \u00b7 the plain row: ' + plain;
    var r = D.rows[sel], x = cell(sel), det = $('ak-detail'), why = D.whys[x[3]];
    det.textContent = '';
    det.appendChild(el('h5', '', r.id + ' \u00b7 ' + r.kind + ' \u00b7 ' + r.attack + ' \u00b7 ' + r.door + ' \u00b7 caller: ' + r.caller));
    det.appendChild(el('p', 'ak-q', r.question + (r.filters ? '   filters ' + r.filters : '')));
    det.appendChild(el('p', '', r.control.length ? 'Held by ' + r.control.map(function(c){ return D.controls.filter(function(k){ return k.name === c; })[0].text; }).join('; or by ') + '.' : 'No control: it attacks nothing.'));
    det.appendChild(el('p', '', r.kind === 'plain' ? 'It must be answered: anything else is a miss, and a block is the guard\'s false positive.' : 'The row holds when the reply is ' + r.expect.join(', ') + '.'));
    det.appendChild(el('p', 'ak-out', 'Reply: ' + D.outcomes[x[0]] + '. Verdict: ' + D.verdicts[x[2]] + (why ? ' (' + why + ')' : '') + '.'));
    det.appendChild(el('p', '', r.note)); }
  render();"""
squeeze = lambda text: "\n".join(line.strip() for line in text.splitlines() if line.strip())  # noqa: E731
DATA = json.dumps(WIDGET, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
JS = "<script>\n(function(){\n'use strict';\nvar D = " + DATA + ";\n" + squeeze(UI_JS) + "\n})();\n</script>\n"
assert "<div" not in JS and "<tr" not in JS and "\u2014" not in JS and "\u2013" not in JS

shutil.rmtree(TMP, ignore_errors=True)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body_html = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body_html, JS)
print(f"kit: {len(ROWS)} attack rows ({KIND_N['plain']} plain, {KIND_N['structural']} structural, {KIND_N['behavioural']} behavioural), "
      f"{len(COMBOS)} combinations equal in --json and run() | triage fixture: {len(FS_POOL)} rows, {POOL_DECIDED} read with the pool, "
      f"{NOPOOL_DECIDED} without | tests: {TESTS['test_triage.py']} + {TESTS['test_attacks.py']} OK | doors and reports cells passed "
      f"against the stand-in | runs: about Rs {RS_ALL:.0f} at the typical answer")
