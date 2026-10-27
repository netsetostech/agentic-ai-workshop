"""Build lesson 4.5 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Check the LLM judge against people. The kit (PR #109): evals/agreement.py (Cohen's kappa, the 2x2, the true-pass and
false-pass rates with route_eval's Wilson interval), evals/judge_agree.py (people: two label sheets; judge: the judge's
per-row ratings against one sheet, its 1-5 metric cut at CUT), evals/build_judge_set.py (the frozen set and its label
sheets), judge.py's --save-rows and --no-enrich, and mk/evaluation.mk's label-sheet, judge-agree and judge-frozen.

Offline, at build time, with the kit's own code and no network: agreement.py --selftest and the kit's
test_agreement.py; the agreement board's arithmetic, ported to JavaScript, which node must reproduce for every state
of the board on the kit's judge fixtures (evals/tests/judge_fixtures: nine synthetic rows, two made-up readers and the
tests' stand-in judge), on the author's set once it is recorded, and for every 2x2 table up to the larger set's size;
and the page's two standard-library cells, run on the fixtures.

Recorded with pb.recorded() (RUN_LIST.md says how): batch 1, the author's freeze of a judge capture (freeze.txt,
judge_set.json) and the judge's ratings of the frozen rows (judge_frozen.txt, judge_set.ratings.jsonl); batch 2, the
author's labels (judge_labels.L1.csv) and one peer's (judge_labels.L2.csv). Once they are recorded, each learner
command's expected output is the kit's own output over them, run here in a throwaway copy of the kit's evals/ so its
paths print as they do on a lane, and the second board shows the author's rows. A recorded file the kit also ships
(deploy/evals/) must be byte-identical to the kit's copy.

    python pagekit/build.py 4.5          (the 3.12 venv; seconds)
"""
import csv
import html
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "4.5"
title = ("<title>Lesson 4.5 Check the LLM judge against people - twenty frozen rows, your labels, a second reader, and "
         "the judge's agreement with chance taken out | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the agreement board: two readers or the judge against one, a rubric, a cut, the rows, the 2x2 */
.ab-ctl{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px;}
.ab-ctl button,.ab-pick button{font:inherit;font-size:13px;background:#f0fdfa;color:var(--teal-dark);border:1px solid #99f6e4;border-radius:999px;padding:6px 12px;min-height:44px;cursor:pointer;}
.ab-ctl button[aria-pressed="true"]{background:var(--teal);border-color:var(--teal);color:#fff;}
.ab-cut{display:flex;flex-direction:column;gap:2px;font-size:var(--small-size);color:var(--navy);margin:0 0 10px;}
.ab-cut input{width:100%;min-height:44px;accent-color:var(--teal);}
.ab-cut input:disabled{opacity:.45;}
.ab-cutv{font-family:var(--mono);font-size:12px;color:var(--teal-dark);}
.ab-chips{display:flex;flex-wrap:wrap;gap:4px;margin:0 0 8px;}
.ab-chips button{font-family:var(--mono);font-size:11.5px;min-width:56px;min-height:44px;padding:2px 6px;border-radius:8px;border:1px solid #a7f3d0;background:#ecfdf5;color:#065f46;cursor:pointer;}
.ab-chips button.no{border-color:#fca5a5;background:#fef2f2;color:#991b1b;}
.ab-chips button.off{border-color:var(--border);background:var(--card);color:#64748b;}
.ab-chips button.c{box-shadow:inset 0 -3px 0 #c2410c;}
.ab-chips button.fl{font-style:italic;font-weight:700;}
.ab-chips button.sel{outline:2px solid var(--navy);outline-offset:1px;}
.ab-grid{display:grid;grid-template-columns:minmax(0,1.1fr) repeat(2,minmax(0,1fr));gap:4px;font-size:12.5px;margin:0 0 8px;}
.ab-grid span{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 8px;line-height:1.35;min-width:0;overflow-wrap:anywhere;}
.ab-grid span.h{background:transparent;border:0;font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;color:var(--navy);letter-spacing:.5px;}
.ab-grid b{display:block;font-family:var(--mono);font-size:20px;color:var(--navy);}
.ab-grid .ok{border-left:4px solid var(--teal);}
.ab-grid .bad{border-left:4px solid #c2410c;}
.ab-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:8px 0;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.ab-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.ab-box p{margin:0 0 6px;font-size:12.5px;}
.ab-out p{font-family:var(--mono);font-size:12px;margin:0 0 3px;}
.ab-ctx{white-space:pre-wrap;font-family:var(--mono);font-size:11.5px;background:var(--bg);border-radius:6px;padding:6px 8px;}
.ab-sw p{display:grid;grid-template-columns:2.4em minmax(0,.7fr) minmax(0,1.5fr) minmax(0,1.5fr) 3.4em;gap:6px;margin:0;padding:3px 0;border-bottom:1px solid var(--border);font-family:var(--mono);font-size:11.5px;}
.ab-sw p.hd{font-weight:700;color:var(--navy);}
.ab-sw p.cur{background:var(--teal-light);font-weight:700;}
.ab-sw span{min-width:0;overflow-wrap:anywhere;}
@media (hover:hover) and (pointer:fine){.ab-ctl button:hover,.ab-chips button:hover,.ab-pick button:hover{filter:brightness(.96);}}
.ab-ctl button:active,.ab-chips button:active,.ab-pick button:active{filter:brightness(.9);}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim kit excerpts
AG, JA, BJ, JG, EV, TJ = ("evals/agreement.py", "evals/judge_agree.py", "evals/build_judge_set.py", "evals/judge.py",
                          "mk/evaluation.mk", "evals/tests/test_judge_rows.py")
EXCERPTS = {
    "label_target": ("mk/evaluation.mk - label-sheet: a blank sheet of the frozen rows for one reader",
                     block(EV, "# The judge set (lesson 4.5):", n=7)),
    "guide": ("evals/build_judge_set.py - GUIDE: the two rubrics, as every reader is told them",
              block(BJ, "GUIDE = (", end="# Constructed rows:")),
    "emit_doc": ("evals/build_judge_set.py - --emit and --check, from the module's docstring",
                 block(BJ, "--emit writes a blank label sheet (CSV) for one reader", end='"""')),
    "row_sha": ("evals/build_judge_set.py - row_sha(): a label belongs to the answer it was given on",
                block(BJ, "def row_sha(", end="# ----------------------------------------------------------------------------- freeze")),
    "kappa_doc": ("evals/agreement.py - raw agreement flatters; kappa takes chance out (the module's docstring)",
                  block(AG, "A reader is a person or a judge", end="With people as the reference")),
    "kappa_fn": ("evals/agreement.py - chance() and cohen_kappa(), counted in whole rows",
                 block(AG, "def chance(", end="def table(")),
    "compare_fn": ("evals/judge_agree.py - compare(): two readers on the rows both labelled",
                   block(JA, "def compare(", end="def verdicts(")),
    "agree_target": ("mk/evaluation.mk - judge-agree: PEOPLE=1 for two sheets, or the judge against one",
                     block(EV, "# Agreement on the judge set, Rs 0.", n=7)),
    "judge_doc": ("evals/judge_agree.py - the judge mode, from the module's docstring",
                  block(JA, "judge RATINGS SHEET:", end='"""')),
    "save_rows": ("evals/judge.py - --save-rows: evaluate() keeps the table row by row",
                  block(JG, "    if save_rows:", n=5) + "\n...\n" + block(JG, "def write_ratings(", n=6)),
    "row_match": ("evals/judge_agree.py - read_ratings(): only a rating of the very answer you labelled counts",
                  block(JA, '    sha = {r["id"]: bjs.row_sha(r) for r in frozen}', n=1) + "\n...\n"
                  + block(JA, "        if bjs.row_sha(x) != sha[rid]:", n=3)),
    "verdicts_fn": ("evals/judge_agree.py - verdicts() and sweep(): what the CUT turns into pass and fail",
                    block(JA, "def verdicts(", end="# ----------------------------------------------------------------------------- printing")),
    "rates_doc": ("evals/agreement.py - the 2x2 and the two rates, from the module's docstring",
                  block(AG, "With people as the reference and a judge under test", end='"""')),
    "table_fn": ("evals/agreement.py - table(), true_pass() and false_pass()",
                 block(AG, "def table(", end="def expand(")),
    "frozen_target": ("mk/evaluation.mk - judge-frozen: your lane's judge on the frozen rows",
                      block(EV, "# Your lane's judge on the frozen rows (lesson 4.5):", n=7)),
    "no_enrich": ("evals/judge.py - --no-enrich: the judge reads the context people labelled, not a fresh store read",
                  block(JG, '    ap.add_argument("--no-enrich"', n=2) + "\n...\n" + block(JG, "    if a.no_enrich:", n=2)),
    "freeze_rules": ("evals/build_judge_set.py - --freeze: how about twenty rows are picked, from the module's docstring",
                     block(BJ, "--freeze picks --rows rows, one per question", end="--emit writes a blank label sheet")),
    "computed_fn": ("evals/build_judge_set.py - computed(): the gate's figure and refusal rules on a frozen answer",
                    block(BJ, "def computed(", end="def rank(")),
    "added": ("evals/build_judge_set.py - ADDED: the sentences a constructed row gains",
              block(BJ, "# Constructed rows: one sentence that no answer's context supports", end="CITE = re.compile(")),
    "standin": ("evals/tests/test_judge_rows.py - rule(): the stand-in judge that rated the fixture's rows",
                block(TJ, "CITE = re.compile(", n=2) + "\n...\n" + block(TJ, "def figures(", end="def stand_in(")),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["label_target"].rstrip().endswith("--reader $(or $(READER),you)"), E["label_target"][-80:]
assert E["guide"].startswith("GUIDE = (") and E["guide"].rstrip().endswith(")") and E["guide"].count('",') == 3   # three lines: two rubrics and the note
assert E["emit_doc"].rstrip().endswith("exit 2 is a file that is missing.")
assert E["row_sha"].rstrip().endswith(".hexdigest()[:12]")
assert "kappa = (p_o - p_e) / (1 - p_e)" in E["kappa_doc"] and E["kappa_doc"].rstrip().endswith("never as perfect.")
assert E["kappa_fn"].startswith("def chance(") and E["kappa_fn"].rstrip().endswith("return (alike * n - by_chance) / (n * n - by_chance)")
assert E["compare_fn"].rstrip().endswith('"differ": [i for i in ids if ref[i] != test[i]]}')
assert E["agree_target"].rstrip().endswith("$(if $(SWEEP),--sweep,))")
assert E["judge_doc"].rstrip().endswith("this measures the judge, it gates nothing.")
assert E["save_rows"].rstrip().endswith("Rows are matched by id, or by position if the table carries none.\"\"\"")
assert E["row_match"].rstrip().endswith("continue")
assert E["verdicts_fn"].rstrip().endswith("for c in range(1, 6)]")
assert E["rates_doc"].rstrip().endswith("because at twenty rows one row moves a rate by several points.")
assert E["table_fn"].rstrip().endswith('return t["false_pass"], t["false_pass"] + t["true_fail"]')
assert E["frozen_target"].rstrip().endswith("$(JUDGE_ARGS)") and "evals/reports/judge_set.json" in E["frozen_target"]   # the learner's own freeze too
assert E["no_enrich"].rstrip().endswith('print("  context: as each row holds it (--no-enrich: no store read)")')
assert E["freeze_rules"].rstrip().endswith('written as "an endpoint": the set ships in a public kit.')
assert E["computed_fn"].rstrip().endswith('return why or "pass"')
assert E["added"].rstrip().endswith(")") and E["added"].count('("') == 5
assert E["standin"].rstrip().endswith("return grounded, follow")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit, imported
sys.path[:0] = [str(KIT / "evals"), str(KIT)]
import agreement as ag  # noqa: E402
import build_judge_set as bjs  # noqa: E402
import judge as jd  # noqa: E402
import judge_agree as ja  # noqa: E402
import run_eval as rv  # noqa: E402
from route_eval import rate, wilson  # noqa: E402
from shared import prices  # noqa: E402

prices.PROFILE = "gcp"      # list prices, whatever DOCUMIND_PROFILE the build's own shell carries
ROWS, RUBRICS, CUT, ADDED = bjs.ROWS, bjs.RUBRICS, ja.CUT, bjs.ADDED
THIRD = math.ceil(ROWS / 3)
assert (ROWS, RUBRICS, CUT, THIRD, len(ADDED)) == (20, ("groundedness", "answers_the_question"), 4, 7, 5)
assert ja.SECOND == tuple(m.lower() for m in jd.SECOND_METRIC) == ("fulfillment", "instruction_following", "question_answering_quality")
N_GOLDEN = len(rv.load_golden())
WORKED = ag.WORKED
W_REF, W_TEST = ag.expand(**WORKED)
assert ag.fmt_kappa(ag.cohen_kappa(W_REF, W_TEST)) == "0.40" and ag.agreement(W_REF, W_TEST) == (35, 50)
EV_TXT = (KIT / EV).read_text(encoding="utf-8")
assert "two Vertex AI Evaluation requests a row" in EV_TXT
FIX = KIT / "evals" / "tests" / "judge_fixtures"
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONIOENCODING": "utf-8",
         "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}        # no gcloud on PATH, no DOCUMIND_* in the environment


def clip(text: str, n: int) -> str:
    """A long text cut for the board, saying how much was left out."""
    text = text or ""
    return text if len(text) <= n else text[:n].rstrip() + f" ... ({len(text) - n} more characters)"


def dataset(frozen: list, sheet_a: Path, sheet_b: Path, ratings: Path) -> dict:
    """One board's rows: the frozen set, two readers' labels and notes (A is the reference), the judge's scores and
    explanations, each file read as judge_agree.py reads it (a sheet that fails --check, or a score off its scale,
    stops the build)."""
    ra, la, na = ja.read_sheet(str(sheet_a), frozen)
    rb, lb, nb = ja.read_sheet(str(sheet_b), frozen)
    rt = ja.read_ratings(str(ratings), frozen)
    said = {}
    for line in ratings.read_text(encoding="utf-8").splitlines():
        if line.strip():
            x = json.loads(line)
            said[x["id"]] = x["ratings"]
    rows = []
    for r in frozen:
        i = r["id"]
        g, m = rt["scores"]["groundedness"].get(i), rt["scores"]["answers_the_question"].get(i)
        rows.append({"i": i, "s": r.get("shape") or "", "c": int(bool(r.get("constructed"))), "k": r.get("computed") or "",
                     "d": r.get("added") or "", "q": r.get("question") or "", "a": r.get("response") or "",
                     "x": clip(r.get("context") or "", 1200), "A": [int(la[i][k]) for k in RUBRICS],
                     "B": [int(lb[i][k]) for k in RUBRICS], "nA": clip(na.get(i, ""), 200), "nB": clip(nb.get(i, ""), 200),
                     "g": g, "m": m,
                     "ge": clip((said.get(i, {}).get("groundedness") or {}).get("explanation") or "", 300) if g is not None else "",
                     "me": clip((said.get(i, {}).get(rt["second"]) or {}).get("explanation") or "", 300) if m is not None else ""})
    return {"A": ra, "B": rb, "second": rt["second"], "rows": rows, "built": sum(r["c"] for r in rows),
            "run": ", ".join(rt["runs"])}


# ------------------------------------------------------------------ the board's state, from the kit's own functions
def py_state(D: dict, rub: int, mode: str, cut: int, flip) -> dict:
    """What the board shows in one state, computed as judge_agree.py's people and judge modes compute it: compare(),
    verdicts() and sweep(), agreement's rates and fmt_kappa(), and route_eval.rate()."""
    rubric = RUBRICS[rub]
    ids = [r["i"] for r in D["rows"]]
    A = {r["i"]: (not r["A"][rub]) if r["i"] == flip else bool(r["A"][rub]) for r in D["rows"]}
    B = {r["i"]: bool(r["B"][rub]) for r in D["rows"]}
    S = {r["i"]: (r["m"] if rub else r["g"]) for r in D["rows"] if (r["m"] if rub else r["g"]) is not None}
    built = {r["i"] for r in D["rows"] if r["c"]}
    jv = None
    if mode == "people":
        c = ja.compare(A, B, ids)
    else:
        jv = ja.verdicts(S, rubric, cut)
        c = ja.compare(A, jv, ids)
    o = {"ids": c["ids"], "table": c["table"], "agree": list(c["agree"]), "chance": c["chance"], "kappa": c["kappa"],
         "differ": c["differ"], "agreeS": rate(*c["agree"]), "chanceS": "-" if c["chance"] is None else f"{c['chance']:.2f}",
         "kappaS": ag.fmt_kappa(c["kappa"])}
    if mode == "judge":
        o["tp"], o["fp"] = rate(*ag.true_pass(c["table"])), rate(*ag.false_pass(c["table"]))
        if built:
            for name, keep in (("fpC", built), ("fpN", set(ids) - built)):
                t = ja.compare({i: A[i] for i in keep if i in A}, {i: jv[i] for i in keep if i in jv}, ids)["table"]
                o[name] = rate(*ag.false_pass(t))
        o["missing"] = [i for i in ids if i not in jv]
        if rub == 1:
            o["sweep"] = [{"cut": w["cut"], "passes": w["table"]["true_pass"] + w["table"]["false_pass"], "n": len(w["ids"]),
                           "tp": rate(*ag.true_pass(w["table"])), "fp": rate(*ag.false_pass(w["table"])),
                           "kappa": ag.fmt_kappa(w["kappa"])} for w in ja.sweep(S, A, ids)]
    return o


ENGINE_JS = r"""function fix(x, d){                       /* Python's format(x, '.Nf'): toFixed, except an exact tie rounds to even */
  var a = Math.abs(x), t = a * Math.pow(2, d + 1);
  if (t === Math.floor(t) && t % 2 === 1) { var m = Math.floor(a * Math.pow(10, d)); if (m % 2) m += 1;
    return (x < 0 ? '-' : '') + (m / Math.pow(10, d)).toFixed(d); }
  return x.toFixed(d); }
function wilson(k, n){                                     /* route_eval.wilson(), z 1.96 */
  if (n <= 0) return null;
  var z = 1.96, p = k / n, z2 = z * z, centre = p + z2 / (2 * n), margin = z * Math.sqrt(p * (1 - p) / n + z2 / (4 * n * n));
  return [Math.max(0, (centre - margin) / (1 + z2 / n)), Math.min(1, (centre + margin) / (1 + z2 / n))]; }
function rate(k, n){                                       /* route_eval.rate() */
  if (n === 0) return '0/0 (no rows)';
  var w = wilson(k, n); return k + '/' + n + ' = ' + fix(100 * k / n, 1) + '% [' + fix(100 * w[0], 1) + '%, ' + fix(100 * w[1], 1) + '%]'; }
function counts(a, b){ var ca = {}, cb = {}, bc = 0, k;
  a.forEach(function(x){ ca[x] = (ca[x] || 0) + 1; }); b.forEach(function(x){ cb[x] = (cb[x] || 0) + 1; });
  for (k in ca) if (cb[k]) bc += ca[k] * cb[k];
  return bc; }
function chance(a, b){ var n = a.length; return n ? counts(a, b) / (n * n) : null; }          /* agreement.chance() */
function kappa(a, b){                                      /* agreement.cohen_kappa(): whole rows, undefined when p_e is 1 */
  var n = a.length, alike = 0, bc, i;
  if (!n) return null;
  for (i = 0; i < n; i++) if (a[i] === b[i]) alike++;
  bc = counts(a, b);
  return bc === n * n ? null : (alike * n - bc) / (n * n - bc); }
function fk(k){ return k === null ? 'undefined' : fix(k, 2); }                                   /* agreement.fmt_kappa() */
function table(r, t){                                      /* agreement.table(): the reference against the reader under test */
  var o = {true_pass: 0, false_fail: 0, false_pass: 0, true_fail: 0};
  for (var i = 0; i < r.length; i++) o[(!!r[i] === !!t[i] ? 'true_' : 'false_') + (t[i] ? 'pass' : 'fail')]++;
  return o; }
function has(o, k){ return Object.prototype.hasOwnProperty.call(o, k); }
function compare(ref, test, ids){                          /* judge_agree.compare() */
  var use = ids.filter(function(i){ return has(ref, i) && has(test, i); }), r = use.map(function(i){ return ref[i]; }),
      t = use.map(function(i){ return test[i]; }), al = 0;
  for (var j = 0; j < r.length; j++) if (r[j] === t[j]) al++;
  return {ids: use, table: table(r, t), agree: [al, use.length], chance: chance(r, t), kappa: kappa(r, t),
          differ: use.filter(function(i){ return ref[i] !== test[i]; })}; }
function verdicts(S, rub, cut){ var o = {}; for (var i in S) if (has(S, i)) o[i] = rub ? S[i] >= cut : S[i] >= 1; return o; }  /* judge_agree.verdicts() */
function fpOf(A, jv, ids, keep){ var a = {}, j = {};
  keep.forEach(function(i){ if (has(A, i)) a[i] = A[i]; if (has(jv, i)) j[i] = jv[i]; });
  var t = compare(a, j, ids).table; return rate(t.false_pass, t.false_pass + t.true_fail); }
function state(D, rub, mode, cut, flips){                  /* judge_agree.py's people and judge modes, on one board */
  var ids = [], A = {}, B = {}, S = {}, built = [], jv = null, o, t;
  D.rows.forEach(function(r){ ids.push(r.i); A[r.i] = flips && flips[r.i] ? !r.A[rub] : !!r.A[rub]; B[r.i] = !!r.B[rub];
    var s = rub ? r.m : r.g; if (s !== null && s !== undefined) S[r.i] = s; if (r.c) built.push(r.i); });
  if (mode === 'people') o = compare(A, B, ids); else { jv = verdicts(S, rub, cut); o = compare(A, jv, ids); }
  o.agreeS = rate(o.agree[0], o.agree[1]); o.chanceS = o.chance === null ? '-' : fix(o.chance, 2); o.kappaS = fk(o.kappa);
  if (mode === 'judge') {
    t = o.table; o.tp = rate(t.true_pass, t.true_pass + t.false_fail); o.fp = rate(t.false_pass, t.false_pass + t.true_fail);
    if (built.length) { o.fpC = fpOf(A, jv, ids, built); o.fpN = fpOf(A, jv, ids, ids.filter(function(i){ return built.indexOf(i) < 0; })); }
    o.missing = ids.filter(function(i){ return !has(jv, i); });
    if (rub === 1) o.sweep = [1, 2, 3, 4, 5].map(function(c){ var w = compare(A, verdicts(S, 1, c), ids), u = w.table;
      return {cut: c, passes: u.true_pass + u.false_pass, n: w.ids.length, tp: rate(u.true_pass, u.true_pass + u.false_fail),
              fp: rate(u.false_pass, u.false_pass + u.true_fail), kappa: fk(w.kappa)}; });
  }
  return o; }"""

UI_JS = r"""var RUB = ['groundedness', 'answers the question'];
function esc(t){ return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
function yn(v){ return v ? 'yes' : 'no'; }
Array.prototype.forEach.call(document.querySelectorAll('.ab[data-set]'), function(root){
  var D = SETS[root.getAttribute('data-set')]; if (!D) return;
  var q = function(c){ return root.querySelector('.' + c); };
  var st = {rub: 0, mode: 'people', cut: CUT, sel: null, flips: [{}, {}]};
  var rubBox = q('ab-rub'), modeBox = q('ab-mode'), cut = q('ab-slide'), cutNote = q('ab-cutv'), chips = q('ab-chips'),
      grid = q('ab-grid'), out = q('ab-out'), sw = q('ab-sw'), pick = q('ab-pick');
  rubBox.innerHTML = RUB.map(function(t, k){ return '<button type="button" data-rub="' + k + '">' + t + '</button>'; }).join('');
  modeBox.innerHTML = '<button type="button" data-mode="people">' + esc(D.A) + ' against ' + esc(D.B) + '</button>'
    + '<button type="button" data-mode="judge">the judge against ' + esc(D.A) + '</button>';
  function render(){
    var flips = st.flips[st.rub], s = state(D, st.rub, st.mode, st.cut, flips), judging = st.mode === 'judge', slid = judging && st.rub === 1;
    Array.prototype.forEach.call(rubBox.children, function(b){ b.setAttribute('aria-pressed', String(+b.getAttribute('data-rub') === st.rub)); });
    Array.prototype.forEach.call(modeBox.children, function(b){ b.setAttribute('aria-pressed', String(b.getAttribute('data-mode') === st.mode)); });
    cut.disabled = !slid; cut.value = String(st.cut);
    cutNote.textContent = slid ? 'CUT ' + st.cut + ': the judge passes a row whose ' + D.second + ' is ' + st.cut + ' or more'
      : judging ? 'groundedness is the judge\'s own 0 or 1: there is nothing to cut' : 'the cut moves only the judge\'s verdicts';
    chips.innerHTML = D.rows.map(function(r){
      var cls = s.ids.indexOf(r.i) < 0 ? ['off'] : s.differ.indexOf(r.i) >= 0 ? ['no'] : [];
      if (r.c) cls.push('c'); if (flips[r.i]) cls.push('fl'); if (st.sel === r.i) cls.push('sel');
      return '<button type="button" data-i="' + esc(r.i) + '" class="' + cls.join(' ') + '">' + esc(r.i) + '</button>'; }).join('');
    var t = s.table, X = judging ? ['judge pass', 'judge fail'] : [D.B + ' yes', D.B + ' no'],
        W = judging ? ['true pass', 'false fail', 'false pass', 'true fail'] : ['both yes', 'split', 'split', 'both no'];
    grid.innerHTML = '<span class="h">' + esc(D.A) + ' down, ' + (judging ? 'the judge' : esc(D.B)) + ' across</span><span class="h">' + esc(X[0]) + '</span><span class="h">' + esc(X[1]) + '</span>'
      + '<span class="h">' + esc(D.A) + ' yes</span><span class="ok"><b>' + t.true_pass + '</b>' + W[0] + '</span><span class="bad"><b>' + t.false_fail + '</b>' + W[1] + '</span>'
      + '<span class="h">' + esc(D.A) + ' no</span><span class="bad"><b>' + t.false_pass + '</b>' + W[2] + '</span><span class="ok"><b>' + t.true_fail + '</b>' + W[3] + '</span>';
    var lines = ['agree ' + s.agreeS + '; by chance ' + s.chanceS + '; kappa ' + s.kappaS
      + (s.kappa === null && s.ids.length ? ' (both gave one label throughout: nothing to agree on beyond chance)' : '')];
    if (judging) {
      lines.push('true-pass ' + s.tp + ': of the rows ' + D.A + ' passes, the judge passes');
      lines.push('false-pass ' + s.fp + ': of the rows ' + D.A + ' fails, the judge passes');
      if (s.fpC) lines.push('false-pass on constructed rows ' + s.fpC + '; on natural rows ' + s.fpN);
      if (s.missing.length) lines.push('not rated: ' + s.missing.join(', '));
    }
    lines.push(s.differ.length ? 'they differ on ' + s.differ.length + ': ' + s.differ.join(', ') : 'they differ on no row');
    out.innerHTML = lines.map(function(l){ return '<p>' + esc(l) + '</p>'; }).join('');
    if (slid) {
      sw.hidden = false;
      sw.innerHTML = '<b class="h">Every cut, as SWEEP=1 prints it</b><p class="hd"><span>cut</span><span>judge passes</span><span>true-pass</span><span>false-pass</span><span>kappa</span></p>'
        + s.sweep.map(function(w){ return '<p' + (w.cut === st.cut ? ' class="cur"' : '') + '><span>' + w.cut + '</span><span>' + w.passes + '/' + w.n
          + '</span><span>' + esc(w.tp) + '</span><span>' + esc(w.fp) + '</span><span>' + esc(w.kappa) + '</span></p>'; }).join('');
    } else { sw.hidden = true; sw.innerHTML = ''; }
    var r = st.sel && D.rows.filter(function(x){ return x.i === st.sel; })[0];
    if (!r) { pick.innerHTML = '<b class="h">Pick a row</b>Tap a row above to read it: the question, the answer, the context, both readers\' labels and the judge\'s scores. Red rows are labelled differently by the two sides; an underlined row is constructed.'; return; }
    var aNow = flips[r.i] ? !r.A[st.rub] : !!r.A[st.rub], sc = st.rub ? r.m : r.g, ex = st.rub ? r.me : r.ge;
    pick.innerHTML = '<b class="h">' + esc(r.i) + ' &middot; ' + esc(r.s) + ' &middot; the gate\'s rules: ' + esc(r.k) + (r.c ? ' &middot; constructed' : '') + '</b>'
      + '<p><b>Question</b> ' + esc(r.q) + '</p><p><b>Answer</b> ' + esc(r.a) + '</p>' + (r.d ? '<p><b>The added sentence</b> ' + esc(r.d) + '</p>' : '')
      + '<p class="ab-ctx">' + esc(r.x) + '</p>'
      + '<p><b>' + esc(D.A) + '</b> ' + yn(aNow) + (flips[r.i] ? ' (flipped here: the sheet says ' + yn(r.A[st.rub]) + ')' : '') + (r.nA ? ', noting: ' + esc(r.nA) : '') + '</p>'
      + '<p><b>' + esc(D.B) + '</b> ' + yn(r.B[st.rub]) + (r.nB ? ', noting: ' + esc(r.nB) : '') + '</p>'
      + '<p><b>The judge</b> ' + (sc === null ? 'did not rate this answer' : (st.rub ? D.second : 'groundedness') + ' ' + sc + (ex ? ': ' + esc(ex) : '')) + '</p>'
      + '<p><button type="button" data-flip="' + esc(r.i) + '">Flip ' + esc(D.A) + '\'s ' + RUB[st.rub] + ' label on this row</button>'
      + (Object.keys(flips).length ? ' <button type="button" data-undo="1">Undo every flip</button>' : '') + '</p>';
  }
  rubBox.addEventListener('click', function(e){ var b = e.target.closest('button'); if (!b) return; st.rub = +b.getAttribute('data-rub'); render(); });
  modeBox.addEventListener('click', function(e){ var b = e.target.closest('button'); if (!b) return; st.mode = b.getAttribute('data-mode'); render(); });
  cut.addEventListener('input', function(){ st.cut = +cut.value; render(); });
  chips.addEventListener('click', function(e){ var b = e.target.closest('button'); if (!b) return; st.sel = b.getAttribute('data-i'); render(); });
  pick.addEventListener('click', function(e){ var b = e.target.closest('button'); if (!b) return; var f = st.flips[st.rub];
    if (b.hasAttribute('data-undo')) st.flips[st.rub] = {}; else { var i = b.getAttribute('data-flip'); if (f[i]) delete f[i]; else f[i] = true; }
    render(); });
  render();
});"""


# ------------------------------------------------------------------ a throwaway copy of the kit's evals/, to run the learner's commands in
MODULES = ("agreement", "judge_agree", "build_judge_set", "judge", "route_eval", "run_eval")


def posix(text: str) -> str:
    """A path the kit printed through os.path.relpath, as a lane prints it: Windows' backslashes become slashes."""
    return re.sub(r"\bevals(?:\\[\w.-]+)+", lambda m: m.group(0).replace("\\", "/"), text)


class Layout:
    """The kit's evals/ code with the given files at their kit paths: a command runs in it exactly as the page writes
    it, from the kit's root, so every path prints as it does on a lane."""

    def __init__(self, files: dict):
        self.root = Path(tempfile.mkdtemp(prefix="lesson45-"))
        (self.root / "evals" / "reports").mkdir(parents=True)
        for m in MODULES:
            shutil.copy2(KIT / "evals" / f"{m}.py", self.root / "evals" / f"{m}.py")
        for rel, data in files.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_bytes(data)

    def run(self, args: list, stdin: str | None = None, code: int = 0) -> str:
        r = subprocess.run([sys.executable, *args], input=stdin, cwd=str(self.root), capture_output=True, text=True,
                           encoding="utf-8", env=QUIET)
        assert r.returncode == code and not r.stderr.strip(), (args, r.returncode, r.stdout[-800:], r.stderr[-800:])
        return posix(r.stdout)

    def fill(self, rel: str, labels: dict, notes: dict | None = None) -> None:
        """Labels {id: {rubric: bool}} written into an emitted sheet, as a person fills one."""
        path = self.root / rel
        with open(path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            for k in RUBRICS:
                r[k] = "yes" if labels[r["id"]][k] else "no"
            r["note"] = (notes or {}).get(r["id"], "")
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=bjs.SHEET_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        path.write_text(buf.getvalue(), encoding="utf-8", newline="")

    def close(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


MK_LINES = EV_TXT.splitlines()


def recipe(target: str) -> str:
    """The recipe line of a one-line target in mk/evaluation.mk."""
    return MK_LINES[MK_LINES.index(f"{target}:") + 1].strip()


def make_echo(target: str, **v) -> str:
    """The line make echoes for a target with no @: $(PY) is the venv's python, $(or $(X),d) is X or d, and
    $(if $(X),a,b) is a or b, innermost first."""
    s = recipe(target).replace("$(PY)", "python")
    while True:
        t = re.sub(r"\$\(or \$\((\w+)\),([^()]*)\)", lambda m: v.get(m.group(1)) or m.group(2), s)
        t = re.sub(r"\$\(if \$\((\w+)\),([^(),]*),([^()]*)\)", lambda m: m.group(2) if v.get(m.group(1)) else m.group(3), t)
        if t == s:
            break
        s = t
    assert "$(" not in s, s
    return " ".join(s.split())


assert make_echo("label-sheet") == "python evals/build_judge_set.py --emit evals/reports/judge_labels.csv --reader you"
assert make_echo("judge-agree", PEOPLE="1") == "python evals/judge_agree.py people evals/reports/judge_labels.csv evals/judge_labels.L1.csv"
assert make_echo("judge-agree") == "python evals/judge_agree.py judge evals/judge_set.ratings.jsonl evals/reports/judge_labels.csv --cut 4"
assert make_echo("judge-agree", CUT="3", SWEEP="1").endswith("--cut 3 --sweep")


def run_kit(args: list) -> subprocess.CompletedProcess:
    """A kit command run in the kit itself, with no network (the self-test and the kit's own tests)."""
    r = subprocess.run([sys.executable, *args], cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=QUIET)
    assert r.returncode == 0, (args, r.stdout[-600:], r.stderr[-600:])
    return r


heredoc = lambda body: "python - <<'PY'\n" + body + "\nPY"       # noqa: E731

# ------------------------------------------------------------------ the two standard-library cells
SHEET_FN = '''def sheet(path):
    """{id: row} of a filled label sheet: UTF-8 as make label-sheet writes it, or a spreadsheet's cp1252."""
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    return {r["id"].strip(): r for r in csv.DictReader(io.StringIO(text, newline=""))}'''

PY_HAND = '''import collections, csv, io, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
from agreement import cohen_kappa            # the kit's, only to check the count by hand below

MINE, THEIRS = "evals/reports/judge_labels.csv", "evals/judge_labels.L1.csv"
if not os.path.exists(THEIRS):                # no author's sheet in the kit yet: your colleague's (step 4)
    THEIRS = "evals/reports/judge_labels.peer.csv"


''' + SHEET_FN + '''


def by_hand(a, b):
    """Raw agreement, chance agreement and Cohen's kappa of two readers' labels, from counts alone."""
    n = len(a)
    p_o = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    p_e = sum(ca[k] * cb[k] for k in ca) / (n * n)
    return p_o, p_e, None if p_e == 1 else (p_o - p_e) / (1 - p_e)


mine, theirs = sheet(MINE), sheet(THEIRS)
ids = sorted(mine)
me, them = mine[ids[0]]["reader"].strip(), theirs[ids[0]]["reader"].strip()
print(f"{len(ids)} rows: {me} ({MINE}) against {them} ({THEIRS})")
for rubric in ("groundedness", "answers_the_question"):
    a = [mine[i][rubric].strip().lower() for i in ids]
    b = [theirs[i][rubric].strip().lower() for i in ids]
    p_o, p_e, k = by_hand(a, b)
    kit = cohen_kappa(a, b)
    same = k == kit if k is None or kit is None else abs(k - kit) < 1e-12
    print(f"  {rubric}: {me} says yes {a.count('yes')} times, {them} {b.count('yes')}; p_o {p_o:.2f}, p_e {p_e:.2f}, "
          f"kappa {'undefined' if k is None else f'{k:.2f}'} (agreement.cohen_kappa: {'the same' if same else 'DIFFERENT'})")
    split = [f"{i} ({me} {x}, {them} {y})" for i, x, y in zip(ids, a, b) if x != y]
    print(f"    split on {len(split)}: {', '.join(split) or 'no row'}")'''

PY_REASONS = '''import csv, io, json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)

MINE, RATINGS, CUT = "evals/reports/judge_labels.csv", "evals/judge_set.ratings.jsonl", 4
if not os.path.exists(RATINGS):               # no author's ratings in the kit yet: your lane's (step 6)
    RATINGS = "evals/reports/judge_set.ratings.jsonl"
SECOND = ("fulfillment", "instruction_following", "question_answering_quality")   # judge.py's names, in its order


''' + SHEET_FN + '''


mine = sheet(MINE)
rated = [json.loads(line) for line in open(RATINGS, encoding="utf-8") if line.strip()]
second = next(m for m in SECOND if any(m in x["ratings"] for x in rated))
me = next(iter(mine.values()))["reader"].strip()
for rubric, metric in (("groundedness", "groundedness"), ("answers_the_question", second)):
    print(f"{rubric}: the judge's {metric}, a pass at {1 if metric == 'groundedness' else CUT} or more")
    for x in rated:
        i, got = x["id"], x["ratings"].get(metric) or {}
        if i not in mine or got.get("score") is None:
            continue
        judge = got["score"] >= (1 if metric == "groundedness" else CUT)
        person = mine[i][rubric].strip().lower() == "yes"
        if judge != person:
            why = " ".join((got.get("explanation") or "").split())
            print(f"  {i}: {me} {'pass' if person else 'fail'}, the judge {got['score']:g}: {why[:140]}{'...' if len(why) > 140 else ''}")'''

MINE_LINE = 'MINE, THEIRS = "evals/reports/judge_labels.csv", "evals/judge_labels.L1.csv"'
REASON_LINE = 'MINE, RATINGS, CUT = "evals/reports/judge_labels.csv", "evals/judge_set.ratings.jsonl", 4'
assert PY_HAND.count(MINE_LINE) == 1 and PY_REASONS.count(REASON_LINE) == 1


def as_mine(body: str, line: str, path: str) -> str:
    """The same cell with MINE set to another sheet: how the page's windows show the author's runs of it."""
    return body.replace(line, line.replace('"evals/reports/judge_labels.csv"', f'"{path}"', 1))


# ------------------------------------------------------------------ the fixture: the Level 0 board, and the cells' test
FX_SET = bjs.load_set(str(FIX / "judge_set.json"))
FXD = dataset(FX_SET, FIX / "labels.FX1.csv", FIX / "labels.FX2.csv", FIX / "ratings.ndjson")
assert (FXD["A"], FXD["B"], FXD["second"], len(FXD["rows"]), FXD["built"]) == ("FX1", "FX2", "instruction_following", 9, 2)
F = Layout({"evals/judge_set.json": (FIX / "judge_set.json").read_bytes(),
            "evals/reports/judge_labels.csv": (FIX / "labels.FX1.csv").read_bytes(),
            "evals/judge_labels.L1.csv": (FIX / "labels.FX2.csv").read_bytes(),
            "evals/judge_set.ratings.jsonl": (FIX / "ratings.ndjson").read_bytes()})
FX_HAND, FX_REASONS = F.run(["-"], PY_HAND), F.run(["-"], PY_REASONS)
F.close()
for rub, rubric in enumerate(RUBRICS):
    want = py_state(FXD, rub, "people", CUT, None)["kappaS"]
    assert f"  {rubric}: FX1 says yes" in FX_HAND and f"kappa {want} (agreement.cohen_kappa: the same)" in FX_HAND, FX_HAND
judge_g = py_state(FXD, 0, "judge", CUT, None)["differ"]
judge_m = py_state(FXD, 1, "judge", CUT, None)["differ"]
assert all(f"  {i}: FX1 " in FX_REASONS for i in judge_g + judge_m) and FX_REASONS.count(": FX1 ") == len(judge_g) + len(judge_m), FX_REASONS
assert "the judge 0: stand-in:" in FX_REASONS and "the judge 5: stand-in:" in FX_REASONS

# the Level 0 narrative, from the fixture: every claim below is asserted, and its numbers go into the prose
FXR = {r["i"]: r for r in FXD["rows"]}
P_G, P_M = py_state(FXD, 0, "people", CUT, None), py_state(FXD, 1, "people", CUT, None)
assert P_G["differ"] == ["fx-12"] and FXR["fx-12"]["c"] and P_M["differ"] == ["fx-04"] and not FXR["fx-04"]["c"]
assert FXR["fx-12"]["A"][0] == 0 and FXR["fx-12"]["B"][0] == 1 and FXR["fx-04"]["A"][1] == 0 and FXR["fx-04"]["B"][1] == 1
assert "sabbatical" not in FXR["fx-07"]["x"] and "2024" not in FXR["fx-06"]["x"]
assert not re.search(r"\d", re.sub(r"\[\d+\]", "", FXR["fx-07"]["a"])) and "six months" in FXR["fx-07"]["a"]   # numbers in words only
FLIP_ROW = next(r["i"] for r in FXD["rows"] if r["A"][0] and r["B"][0] and not r["c"])
P_FLIP = py_state(FXD, 0, "people", CUT, FLIP_ROW)
J_G = py_state(FXD, 0, "judge", CUT, None)
assert J_G["differ"] == ["fx-06", "fx-07"] and FXR["fx-07"]["g"] == 1 and not FXR["fx-07"]["A"][0] and FXR["fx-06"]["g"] == 0 and FXR["fx-06"]["A"][0]
assert FXR["fx-07"]["s"] == "refusal" and FXR["fx-06"]["s"] == "refusal" and "sabbatical" in FXR["fx-07"]["a"] and "FY2024" in FXR["fx-06"]["a"]
J_M = {c: py_state(FXD, 1, "judge", c, None) for c in range(1, 6)}
assert J_M[3]["differ"] == ["fx-04", "fx-06", "fx-07"] and FXR["fx-04"]["m"] == 3 and J_M[1]["kappaS"] == "0.00"
assert [w["passes"] for w in J_M[CUT]["sweep"]] == [9, 8, 7, 6, 6]

# ------------------------------------------------------------------ the author's runs, recorded
REC_FILES = ("judge_set.json", "judge_set.ratings.jsonl", "judge_labels.L1.csv", "judge_labels.L2.csv")


def awaiting(name: str) -> str:
    return f"[awaiting the author's run: data/{name}]"


def recorded_bytes(name: str) -> bytes | None:
    """A recorded data file's bytes, or None while it is awaited; pb.recorded() reads it, or names it for finish()."""
    try:
        text = pb.recorded(LESSON, name)
    except UnicodeDecodeError:          # a sheet a spreadsheet saved in its own code page: build_judge_set reads it as cp1252
        return pb.data(LESSON, name).read_bytes()
    return None if text == awaiting(name) else pb.data(LESSON, name).read_bytes()


REC = {name: recorded_bytes(name) for name in REC_FILES}
TXT = {name: pb.recorded(LESSON, name) for name in ("freeze.txt", "judge_frozen.txt")}
NOTES = []
for name, data in REC.items():
    shipped = KIT / "evals" / name
    if data is not None and shipped.exists():
        assert shipped.read_bytes() == data, f"data/{name} is not the kit's evals/{name}: record the file the kit ships"
    elif data is not None:
        NOTES.append(f"note: the kit has no evals/{name} yet: the learner's commands need it (a kit PR adds it)")
MISSING = [n for n in REC_FILES if REC[n] is None]
L = AD = None
if not MISSING:
    L = Layout({f"evals/{n}": REC[n] for n in REC_FILES})
    AUTH_SET = bjs.load_set(str(L.root / "evals" / "judge_set.json"))
    AD = dataset(AUTH_SET, L.root / "evals" / "judge_labels.L1.csv", L.root / "evals" / "judge_labels.L2.csv",
                 L.root / "evals" / "judge_set.ratings.jsonl")
    assert (AD["A"], AD["B"]) == ("L1", "L2"), (AD["A"], AD["B"])


def first_missing(*names: str) -> str | None:
    """The awaiting marker of the first input an output needs that the author has not recorded yet."""
    gone = [n for n in names if REC[n] is None]
    return awaiting(gone[0]) if gone else None


OUT = {}
r = run_kit(["evals/agreement.py", "--selftest"])
tests = run_kit(["-m", "unittest", "discover", "-s", "evals/tests", "-p", "test_agreement.py"]).stderr.splitlines()[-3:]
assert re.fullmatch(r"Ran \d+ tests in [\d.]+s", tests[0]) and tests[1:] == ["", "OK"], tests
N_TESTS = int(tests[0].split()[1])
OUT["selftest"] = r.stdout + re.sub(r"in [\d.]+s", "in ...s", tests[0]) + "\n\nOK\n"
assert "kappa 0.40" in OUT["selftest"] and "35/50 = 70.0%" in OUT["selftest"]

OUT["sheet"] = first_missing("judge_set.json") or (make_echo("label-sheet") + "\n" + L.run(
    ["evals/build_judge_set.py", "--emit", "evals/reports/judge_labels.csv", "--reader", "you"]))
if AD:
    L1_LABELS = {r["i"]: {k: bool(r["A"][n]) for n, k in enumerate(RUBRICS)} for r in AD["rows"]}
    L.fill("evals/reports/judge_labels.csv", L1_LABELS)
    yours = L.run(["evals/build_judge_set.py", "--check", "evals/reports/judge_labels.csv"])
    yours, n_sub = re.subn(r"labelled by you - groundedness \d+ yes, \d+ no; answers_the_question \d+ yes, \d+ no; \d+ with a note",
                           "labelled by you - groundedness ... yes, ... no; answers_the_question ... yes, ... no; ... with a note", yours)
    assert n_sub == 1, yours
    OUT["check"] = yours + L.run(["evals/build_judge_set.py", "--check", "evals/judge_labels.L1.csv"])
    OUT["people"] = (make_echo("judge-agree", PEOPLE="1", LABELS="evals/judge_labels.L1.csv", AGAINST="evals/judge_labels.L2.csv") + "\n"
                     + L.run(["evals/judge_agree.py", "people", "evals/judge_labels.L1.csv", "evals/judge_labels.L2.csv"]))
    OUT["judge"] = (make_echo("judge-agree", LABELS="evals/judge_labels.L1.csv") + "\n"
                    + L.run(["evals/judge_agree.py", "judge", "evals/judge_set.ratings.jsonl", "evals/judge_labels.L1.csv", "--cut", str(CUT)]))
    OUT["cut"] = (make_echo("judge-agree", LABELS="evals/judge_labels.L1.csv", CUT="3", SWEEP="1") + "\n"
                  + L.run(["evals/judge_agree.py", "judge", "evals/judge_set.ratings.jsonl", "evals/judge_labels.L1.csv", "--cut", "3", "--sweep"]))
    OUT["hand"] = L.run(["-"], as_mine(PY_HAND, MINE_LINE, "evals/judge_labels.L2.csv"))
    OUT["reasons"] = L.run(["-"], as_mine(PY_REASONS, REASON_LINE, "evals/judge_labels.L1.csv"))
    for rub, rubric in enumerate(RUBRICS):          # the kit's printed kappa is the board's, on the same rows
        assert f"kappa {py_state(AD, rub, 'people', CUT, None)['kappaS']}" in OUT["people"].split(f"  {rubric}\n", 1)[1].split("\n\n")[0]
        assert f"kappa {py_state(AD, rub, 'judge', CUT, None)['kappaS']}" in OUT["judge"].split(f"  {rubric} (", 1)[1].split("\n\n")[0]
    L.close()
else:
    OUT["check"] = first_missing("judge_set.json", "judge_labels.L1.csv")
    OUT["people"] = first_missing("judge_set.json", "judge_labels.L1.csv", "judge_labels.L2.csv")
    OUT["judge"] = OUT["cut"] = first_missing("judge_set.json", "judge_set.ratings.jsonl", "judge_labels.L1.csv")
    OUT["hand"] = first_missing("judge_labels.L1.csv", "judge_labels.L2.csv")
    OUT["reasons"] = first_missing("judge_set.ratings.jsonl", "judge_labels.L1.csv")
    if L:
        L.close()
OUT["frozen"], OUT["freeze"] = TXT["judge_frozen.txt"], TXT["freeze.txt"]
if TXT["freeze.txt"] != awaiting("freeze.txt") and "(flash-lite)" not in TXT["freeze.txt"]:
    NOTES.append("note: freeze.txt names no flash-lite capture, but the diagram and step 8 say the author froze from one: fix the prose")
# "instruction_following in the SDK that lesson 4.2 pins": the second metric 4.2's build read from google-cloud-aiplatform 2.1.0
SDK_SECOND = re.search(r'TEMPLATE_HASH, SECOND = "[0-9a-f]{6}", "([A-Z_]+)"', (pb.lesson_dir("4.2") / "build.py").read_text(encoding="utf-8")).group(1)
assert SDK_SECOND in jd.SECOND_METRIC, SDK_SECOND

# ------------------------------------------------------------------ the board: node must reproduce the kit's arithmetic
SETS = {"fixture": {k: FXD[k] for k in ("A", "B", "second", "rows")}}
if AD:
    SETS["author"] = {k: AD[k] for k in ("A", "B", "second", "rows")}
NMAX = max(ROWS, *(len(s["rows"]) for s in SETS.values()))
CASES, WANT = [], []
for key, D in SETS.items():
    flips = [None] + [r["i"] for r in D["rows"]]
    for rub in (0, 1):
        for mode, cuts in (("people", (CUT,)), ("judge", (1, 2, 3, 4, 5) if rub else (CUT,))):
            for cut in cuts:
                for flip in flips:
                    CASES.append({"set": key, "rub": rub, "mode": mode, "cut": cut, "flip": flip})
                    WANT.append(py_state(D, rub, mode, cut, flip))
TABLES = [(tp, ff, fp, n - tp - ff - fp) for n in range(1, NMAX + 1) for tp in range(n + 1) for ff in range(n + 1 - tp)
          for fp in range(n + 1 - tp - ff)]
WANT_T = []
for t in TABLES:
    ref, test = ag.expand(*t)
    ch = ag.chance(ref, test)
    tt = ag.table(ref, test)
    WANT_T.append([rate(*ag.agreement(ref, test)), "-" if ch is None else f"{ch:.2f}", ag.fmt_kappa(ag.cohen_kappa(ref, test)),
                   rate(*ag.true_pass(tt)), rate(*ag.false_pass(tt))])
EXTRA = [(["x", "y", "z", "x"], ["x", "y", "x", "x"]), ([True] * 6, [True] * 6), ([True] * 6, [True] * 4 + [False] * 2),
         ([True] * 4, [False] * 4), ([True, False, True, False], [False, True, False, True]), ([], [])]
WANT_X = [[ag.cohen_kappa(a, b), ag.chance(a, b)] for a, b in EXTRA]
test_js = ("'use strict';\n" + ENGINE_JS + "\nvar SETS = " + json.dumps(SETS) + ", CASES = " + json.dumps(CASES)
           + ", TABLES = " + json.dumps(TABLES) + ", EXTRA = " + json.dumps(EXTRA) + ";\n"
           "function expand(tp, ff, fp, tn){ var r = [], j = [], c = [[true, true, tp], [true, false, ff], [false, true, fp], [false, false, tn]];\n"
           "  c.forEach(function(x){ for (var k = 0; k < x[2]; k++){ r.push(x[0]); j.push(x[1]); } }); return [r, j]; }\n"
           "console.log(JSON.stringify({\n"
           "  states: CASES.map(function(c){ var f = {}; if (c.flip !== null) f[c.flip] = true; return state(SETS[c.set], c.rub, c.mode, c.cut, f); }),\n"
           "  tables: TABLES.map(function(t){ var e = expand(t[0], t[1], t[2], t[3]), r = e[0], j = e[1], al = 0, i, u, ch;\n"
           "    for (i = 0; i < r.length; i++) if (r[i] === j[i]) al++;\n"
           "    u = table(r, j); ch = chance(r, j);\n"
           "    return [rate(al, r.length), ch === null ? '-' : fix(ch, 2), fk(kappa(r, j)), rate(u.true_pass, u.true_pass + u.false_fail),\n"
           "            rate(u.false_pass, u.false_pass + u.true_fail)]; }),\n"
           "  extra: EXTRA.map(function(x){ return [kappa(x[0], x[1]), chance(x[0], x[1])]; })}));\n")
tjs = Path(tempfile.mkdtemp(prefix="lesson45-js-")) / "board.js"
tjs.write_text(test_js, encoding="utf-8")
node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(tjs.parent, ignore_errors=True)
assert node.returncode == 0, node.stderr[-800:]
GOT = json.loads(node.stdout)
for case, want, got in zip(CASES, WANT, GOT["states"]):
    assert want == got, (case, {k: (want.get(k), got.get(k)) for k in set(want) | set(got) if want.get(k) != got.get(k)})
for t, want, got in zip(TABLES, WANT_T, GOT["tables"]):
    assert want == got, (t, want, got)
assert GOT["extra"] == WANT_X, (GOT["extra"], WANT_X)
assert len(GOT["states"]) == len(CASES) and len(GOT["tables"]) == len(TABLES)


def board_html(key: str, head: str, cap: str) -> str:
    """One agreement board: its controls, the rows, the 2x2, the kit's lines, every cut, and the row picked."""
    return (f'<div class="diagram ab" data-set="{key}">\n<div class="dg-title">{head}</div>\n'
            '<div class="ab-ctl ab-rub" role="group" aria-label="The rubric"></div>\n'
            '<div class="ab-ctl ab-mode" role="group" aria-label="Who is set against whom"></div>\n'
            f'<label class="ab-cut">The judge\'s cut on its 1 to 5 metric<input class="ab-slide" type="range" min="1" max="5" step="1" value="{CUT}"><span class="ab-cutv"></span></label>\n'
            '<div class="ab-chips"></div>\n<div class="ab-grid"></div>\n<div class="ab-box ab-out" aria-live="polite"></div>\n'
            '<div class="ab-box ab-sw" hidden></div>\n<div class="ab-box ab-pick"></div>\n'
            f'<p class="dg-cap">{cap}</p>\n</div>\n')


BOARD_FX = board_html(
    "fixture", f"Agreement board - the kit's judge fixture: {len(FXD['rows'])} synthetic rows, two made-up readers, the tests' stand-in judge",
    f"The arithmetic is <code>agreement.py</code>'s and <code>judge_agree.py</code>'s, ported. The build ran all "
    f"{sum(1 for c in CASES if c['set'] == 'fixture')} states of this board, every rubric, side, cut and single flip, through the kit's own "
    f"functions, and every 2x2 table of up to {NMAX} rows, {len(TABLES):,} of them, and the board had to print the same "
    "counts, rates, intervals and kappas.")
if AD:
    BOARD_AUTH = board_html(
        "author", f"Agreement board - the frozen set: {len(AD['rows'])} rows, the author (L1), a peer (L2), the judge's ratings",
        f"The same board on the author's recorded files: <code>evals/judge_set.json</code>, the two sheets and "
        f"<code>evals/judge_set.ratings.jsonl</code> (run {html.escape(AD['run'])}). The build ran all "
        f"{sum(1 for c in CASES if c['set'] == 'author')} of its states through the kit's functions too.")
else:
    BOARD_AUTH = ('<div class="box box-amber"><div class="box-title">The author\'s rows on the board</div>'
                  f'<p>They join this board when the frozen set, the two sheets and the judge\'s ratings are recorded: '
                  f'{html.escape(first_missing(*REC_FILES))}</p></div>\n')

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
DATA = json.dumps(SETS, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\!--")
JS = ("<script>\n(function(){\n'use strict';\nvar SETS = " + DATA + ", CUT = " + str(CUT) + ";\n"
      + squeeze(ENGINE_JS) + "\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert JS.count("<div") == JS.count("</div>") and "<tr" not in JS and "<table" not in JS

# ------------------------------------------------------------------ the windows: what you run, and what it prints
CELLS = {
    "own": (f"run in the operator shell, in the kit, in lesson 4.2's judge venv (only while there is no frozen set: "
            f"{2 * N_GOLDEN} Evaluation requests over lesson 4.2's saved answers, or {N_GOLDEN} fresh answers first if they are gone)",
            'test -f evals/judge_set.json -o -f evals/reports/judge_set.json && echo "a frozen set is in your kit: skip this block" || {\n'
            'make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" \\\n'
            '  JUDGE_ARGS="--reuse evals/reports/judge72.json --save-rows evals/reports/judge45_rows.jsonl" &&\n'
            'python evals/build_judge_set.py --freeze evals/reports/judge45_rows.jsonl --set evals/reports/judge_set.json\n'
            '}'),
    "sheet": ("run in the operator shell, in the kit (Rs 0: a blank sheet of the frozen rows for you; it never overwrites one)",
              "make label-sheet"),
    "check": ("run in the operator shell, in the kit (Rs 0: holds a filled sheet to the frozen set)",
              "python evals/build_judge_set.py --check evals/reports/judge_labels.csv\n"
              "python evals/build_judge_set.py --check evals/judge_labels.L1.csv      # the author's sheet, shipped with the kit"),
    "selftest": ("run in the operator shell, in the kit (Rs 0: the worked table, then the kit's own tests of the arithmetic)",
                 "python evals/agreement.py --selftest\npython -m unittest discover -s evals/tests -p test_agreement.py 2>&1 | tail -3"),
    "people": ("run in the operator shell, in the kit (Rs 0: two sheets, kappa per rubric)",
               "make judge-agree PEOPLE=1                       # your sheet against the author's\n"
               "make judge-agree PEOPLE=1 LABELS=evals/judge_labels.L1.csv AGAINST=evals/judge_labels.L2.csv   # the author against the peer"),
    "peer_sheet": ("run in the operator shell, in the kit (Rs 0: only while the kit has no author's sheet; a blank sheet for your colleague)",
                   "make label-sheet LABELS=evals/reports/judge_labels.peer.csv READER=peer"),
    "peer_agree": ("run in the operator shell, in the kit (Rs 0: once your colleague has filled their sheet, blind)",
                   "python evals/build_judge_set.py --check evals/reports/judge_labels.peer.csv\n"
                   "make judge-agree PEOPLE=1 AGAINST=evals/reports/judge_labels.peer.csv   # your sheet against your colleague's"),
    "judge": ("run in the operator shell, in the kit (Rs 0: the judge's ratings of the same rows against one sheet)",
              "make judge-agree                                 # the judge against your sheet, cut at 4\n"
              "make judge-agree LABELS=evals/judge_labels.L1.csv   # the judge against the author"),
    "cut": ("run in the operator shell, in the kit (Rs 0: the Change-it; nothing to restore, because CUT is not a setting)",
            "make judge-agree CUT=3 SWEEP=1                   # your sheet: a looser cut, and every cut beside it\n"
            "make judge-agree LABELS=evals/judge_labels.L1.csv CUT=3 SWEEP=1   # the author's"),
    "frozen": (f"run in the operator shell, in the kit (while the kit has no author's ratings: {2 * ROWS} Vertex AI Evaluation requests, two a row; nothing asked of the API)",
               'make judge-frozen PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python"\n'
               "make judge-agree RUN=evals/reports/judge_set.ratings.jsonl      # your lane's judge against your sheet"),
    "hand": ("run in the operator shell, in the kit (a Python cell; Rs 0: it reads two sheets)", heredoc(PY_HAND)),
    "reasons": ("run in the operator shell, in the kit (a Python cell; Rs 0: it reads your sheet and the judge's ratings)", heredoc(PY_REASONS)),
}
for k in ("people", "judge", "cut"):
    for line in CELLS[k][1].splitlines():
        assert line.startswith("make judge-agree") and "$(" not in line
REC_SAMPLE = "the author's recorded files, laid out as in your kit"
OUTS = {
    "sheet": (f"(the kit's own output over {REC_SAMPLE}: yours is the same)", OUT["sheet"]),
    "check": (f"(over {REC_SAMPLE}: your line counts your own labels, so its numbers are dots here; the author's line is exact)",
              OUT["check"]),
    "selftest": ("(the kit's own output, produced when this page was built: yours should match it)", OUT["selftest"]),
    "people": (f"(the second command, over {REC_SAMPLE}: the author against the peer. The first prints the same blocks for you against the author)",
               OUT["people"]),
    "judge": (f"(the second command, over {REC_SAMPLE}: the judge against the author. The first prints the same blocks against your sheet)",
              OUT["judge"]),
    "cut": (f"(the second command, over {REC_SAMPLE}: the author's sheet at CUT=3, then every cut)", OUT["cut"]),
    "frozen": ("(the author's lane, with RUN=evals/judge_set.ratings.jsonl: the run that rated the rows your kit ships; yours writes to evals/reports/ and names its own run)",
               OUT["frozen"]),
    "hand": ('(the same cell with MINE set to "evals/judge_labels.L2.csv", the peer\'s sheet, over the author\'s recorded files: yours reads your own)',
             OUT["hand"]),
    "reasons": ('(the same cell with MINE set to "evals/judge_labels.L1.csv", the author\'s sheet, over the recorded files: yours lists the rows you and the judge differ on)',
                OUT["reasons"]),
    "freeze": ("the author's freeze, recorded: python evals/build_judge_set.py --freeze evals/reports/judge45_rows.jsonl flash-lite=evals/reports/cand45_rows.jsonl",
               OUT["freeze"]),
}


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str, prefix: str = "expected ") -> str:
    return ('<div class="cw"><div class="ch-bar"><span>' + prefix + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(*v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items() if k != "freeze"})
WIN["OUT_FREEZE"] = out_window(*OUTS["freeze"], prefix="output, ")
WIN["BOARD_FX"], WIN["BOARD_AUTH"] = BOARD_FX, BOARD_AUTH


# ------------------------------------------------------------------ numbers for the prose
def first_sheet_row(name: str) -> dict:
    with open(FIX / name, encoding="utf-8", newline="") as f:
        return next(r for r in csv.DictReader(f) if r["id"] == "fx-03")


EX = first_sheet_row("labels.FX1.csv")
assert (EX["groundedness"], EX["answers_the_question"]) == ("yes", "no") and "40,000" in EX["context"] and "do not say" in EX["answer"]
EX_ROW = ('<tr><td><code>fx-03</code></td><td data-label="reader"><code>' + html.escape(EX["reader"]) + "</code></td>"
          f'<td data-label="groundedness"><code>{EX["groundedness"]}</code></td><td data-label="answers_the_question"><code>{EX["answers_the_question"]}</code></td>'
          f'<td data-label="note">{html.escape(EX["note"])}</td><td data-label="question">{html.escape(EX["question"])}</td>'
          f'<td data-label="answer">{html.escape(EX["answer"])}</td><td data-label="context">{html.escape(EX["context"])}</td>'
          f'<td data-label="row_sha"><code>{EX["row_sha"]}</code></td></tr>')
assert EX["row_sha"] == bjs.row_sha(next(r for r in FX_SET if r["id"] == "fx-03"))
RS = lambda model, n: prices.usd(model, 2000, 300) * prices.USD_INR * n        # noqa: E731 - the course's typical answer: 2,000 in, 300 out
LIVE_RS, CAND_RS = RS("gemini-3.6-flash", N_GOLDEN), RS("gemini-3.1-flash-lite", N_GOLDEN)
STATS = {
    "ROWS": str(ROWS), "THIRD": str(THIRD), "N_ADDED": str(len(ADDED)), "CUT": str(CUT), "N_GOLDEN": str(N_GOLDEN),
    "N_EVAL_FROZEN": str(2 * ROWS), "N_TESTS": str(N_TESTS),
    "SECOND_NAMES": ", ".join(jd.SECOND_METRIC[:-1]) + " or " + jd.SECOND_METRIC[-1],
    "W_N": str(len(W_REF)), "W_TP": str(WORKED["true_pass"]), "W_FF": str(WORKED["false_fail"]), "W_FP": str(WORKED["false_pass"]),
    "W_TF": str(WORKED["true_fail"]), "W_ALIKE": str(ag.agreement(W_REF, W_TEST)[0]),
    "W_PO": f"{ag.agreement(W_REF, W_TEST)[0] / len(W_REF):.2f}", "W_PE": f"{ag.chance(W_REF, W_TEST):.2f}",
    "W_K": ag.fmt_kappa(ag.cohen_kappa(W_REF, W_TEST)), "W_A_YES": str(sum(W_REF)), "W_B_YES": str(sum(W_TEST)),
    "THIRD_0": rate(0, THIRD), "THIRD_0_HI": f"{100 * wilson(0, THIRD)[1]:.1f}%",
    "FX_N": str(len(FXD["rows"])), "FX_BUILT": str(FXD["built"]),
    "FX_PG_AGREE": P_G["agreeS"], "FX_PG_CHANCE": P_G["chanceS"], "FX_PG_K": P_G["kappaS"],
    "FX_PM_K": P_M["kappaS"], "FX_FLIP": FLIP_ROW, "FX_FLIP_AGREE": P_FLIP["agreeS"], "FX_FLIP_K": P_FLIP["kappaS"],
    "FX_JG_K": J_G["kappaS"], "FX_JG_FP": J_G["fp"], "FX_JM4_FP": J_M[CUT]["fp"], "FX_JM4_K": J_M[CUT]["kappaS"],
    "FX_JM3_FP": J_M[3]["fp"], "FX_JM3_K": J_M[3]["kappaS"], "FX_JM1_K": J_M[1]["kappaS"],
    "SDK_SECOND": SDK_SECOND.lower(), "EX_ROW": EX_ROW, "EX_NOTE": html.escape(EX["note"]),
    "LIVE_RS": f"{LIVE_RS:.2f}", "CAND_RS": f"{CAND_RS:.2f}", "CAPTURE_RS": f"{LIVE_RS + CAND_RS:.2f}",
    "N_STATES": str(len(CASES)), "N_TABLES": f"{len(TABLES):,}", "NMAX": str(NMAX),
}
assert STATS["FX_PG_K"] == STATS["FX_PM_K"] == "0.73" and STATS["FX_JG_K"] == "0.50" and STATS["FX_JM3_K"] == "0.18"

if os.environ.get("CELLS_ONLY"):                  # CELLS_ONLY=1 python build.py: the expected blocks, nothing written
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print("===== fixture hand\n" + FX_HAND + "===== fixture reasons\n" + FX_REASONS)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)

# the run list's prices, from the same figures: a stale line is named here, not silently kept
run_list = (pb.lesson_dir(LESSON) / "RUN_LIST.md").read_text(encoding="utf-8")
for k in ("LIVE_RS", "CAND_RS", "CAPTURE_RS"):
    if f"Rs {STATS[k]}" not in run_list:
        print(f"note: RUN_LIST.md does not state {k} = Rs {STATS[k]}")
for n in NOTES:
    print(n)
print(f"kit: {ROWS} rows a set, a third {THIRD}, CUT {CUT}, {N_TESTS} agreement tests | fixture: {len(FXD['rows'])} rows, kappa "
      f"{P_G['kappaS']}/{P_M['kappaS']} between FX1 and FX2, judge {J_G['kappaS']} | node equal on {len(CASES)} board states and "
      f"{len(TABLES):,} tables up to {NMAX} rows | author's files: {'recorded' if AD else 'awaiting ' + ', '.join(MISSING)}"
      f" | capture Rs {LIVE_RS:.2f} + Rs {CAND_RS:.2f}")
