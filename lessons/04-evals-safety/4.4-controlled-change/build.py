"""Build lesson 4.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

What the page prints is the kit's own output wherever a build can produce it. The scoped live gate's blocks and the
comparison of its two reports are printed by run_eval.live() and the lesson's cell over a stub API (the candidate
misses one row on purpose; the page says so and masks what belongs to a lane). The one-change cell and the rupee
cell are run here against a fake gcloud that returns two revisions' settings and a set of usage rows, so their code
is tested even though their real inputs are the lane's. The SDK's win-rate lines were copied from
google-cloud-aiplatform 2.1.0 into data/sdk_win_rates.txt. The planner's price arithmetic is cost.price(), ported;
node must reproduce it on a grid of cases before the page is written.
"""
import ast
import contextlib
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "4.4"
title = "<title>Lesson 4.4 Compare one controlled change against a baseline - a candidate that differs in one setting, the scoped gate on both, the pairwise judge between them, and the rupees of the difference | Netsetos</title>\n"
API = "https://documind-api-NUMBER.asia-south1.run.app"
CAND = "https://candidate---documind-api-NUMBER.asia-south1.run.app"
SOURCE = "hr_policy_2026.md"
NEW_MODEL = "gemini-3.1-flash-lite"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.cp-set{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr) minmax(0,1.2fr);gap:6px 10px;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);}
.cp-set span{min-width:0;overflow-wrap:anywhere;font-size:12.5px;color:var(--slate);}
.cp-set b{font-family:var(--mono);font-size:12px;color:var(--navy);display:block;}
.cp-set small{display:block;font-size:11px;color:var(--slate);}
.cp-set select,.cp-in input{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;width:100%;}
.cp-set.changed select{border-color:#f59e0b;background:#fffbeb;}
.cp-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:10px 0;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.cp-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.cp-box ul{margin:4px 0 0;padding-left:18px;}
.cp-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px 12px;margin:6px 0;}
.cp-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.cp-verdict{font-family:var(--mono);font-size:13px;font-weight:700;padding:6px 10px;border-radius:8px;display:inline-block;margin-bottom:4px;}
.cp-verdict.v1{background:#d1fae5;color:#065f46;}.cp-verdict.v0{background:#e2e8f0;color:#334155;}.cp-verdict.v2{background:#fee2e2;color:#991b1b;}
.cp-money{font-family:var(--mono);font-size:12.5px;white-space:pre-wrap;margin:4px 0 0;color:var(--navy);}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
RE_, JG, CFG, COST = "evals/run_eval.py", "evals/judge.py", "services/rag-api/config.py", "services/rag-api/cost.py"
EXCERPTS = {
    "candidate": ("Makefile - candidate: a revision with no traffic, its settings written over the service's latest template",
                  block("Makefile", "# A candidate revision of the API with another model behind it", n=13)),
    "every_switch": ("services/rag-api/config.py - every switch is judged on a candidate first",
                     block(CFG, "    # The ledger (12.5, 11 September 2026): `on` retrieves only chunks", n=4) + "\n...\n"
                     + block(CFG, "never an error. Judged on a candidate first", n=2)),
    "scoped": ("evals/run_eval.py - --source: the rows that cite one document, judged in minutes",
               block(RE_, "--source scopes the live half to the rows that cite one document", n=5)),
    "rows_behind": ("evals/run_eval.py - live(): a threshold with no rows behind it is not judged",
                    block(RE_, "    # A threshold with no rows behind it is not judged", n=6)),
    "judge_pairwise": ("evals/judge.py - pairwise: the candidate is judged, the live revision is the baseline",
                       block(JG, "Pairwise (10.1's A/B, 10.4's cell 5):", n=3) + "\n...\n" + block(JG, "    if a.api_b:", n=9)),
    "pair_metric": ("evals/judge.py - evaluate(): the pairwise metric joins the two pointwise ones",
                    block(JG, "    if pairwise:", n=4)),
    "price": ("services/rag-api/cost.py - price(): the three Gemini rates, cached input at a tenth, both currencies",
              block(COST, 'FALLBACK = {"gemini-3.6-flash": (1.50, 7.50),', n=3) + "\n...\n"
              + block(COST, '    if model.startswith("projects/"):', n=11)),
}
assert EXCERPTS["candidate"][1].rstrip().endswith("--remove-tags candidate)\""), EXCERPTS["candidate"][1][-80:]
assert EXCERPTS["every_switch"][1].rstrip().endswith('alias="RETRIEVAL_GRAPH")')
assert EXCERPTS["scoped"][1].rstrip().endswith("blocks on its own."), EXCERPTS["scoped"][1][-80:]
assert EXCERPTS["rows_behind"][1].rstrip().endswith("judged = {k for k in THRESHOLDS if rows_behind[k] > 0}"), EXCERPTS["rows_behind"][1][-80:]
assert EXCERPTS["judge_pairwise"][1].rstrip().endswith("# the candidate is judged; the live revision is the baseline")
assert EXCERPTS["price"][1].rstrip().endswith('"cached_tokens": cached_tokens}')
fill = filler(EXCERPTS, window)
SDK_WIN = pb.data(LESSON, "sdk_win_rates.txt").read_text(encoding="utf-8").rstrip("\n")
assert "candidate_model_win_rate" in SDK_WIN and "baseline_model_win_rate" in SDK_WIN

# ------------------------------------------------------------------ the kit's numbers
sys.path.insert(0, str(KIT / "evals"))
import run_eval as rv  # noqa: E402

golden = rv.load_golden()
corpus = rv.load_corpus()
SCOPED = [r for r in golden if rv.in_scope(r, SOURCE, corpus)]
FIRST20 = golden[:20]
for k in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "DOCUMIND_USER_EMAIL", "DOCUMIND_OUTSIDER_EMAIL"):
    os.environ.pop(k, None)


# ------------------------------------------------------------------ a stub API for the scoped gate (4.2's, per row in scope)
def reply(row: dict, outcome: str) -> tuple:
    t, mc = row["tenant"], row.get("must_contain", [])
    cite = {"chunk_id": f"{t}:lesson#0", "source_uri": f"gs://lesson/{t}/doc.md", "quote": mc[0] if mc else "lesson", "kind": "text"}
    answer = "The documents cover this [1]." if outcome == "nofig" else f"{' and '.join(mc)} [1]."
    return 200, {"answer": answer, "citations": [cite], "answerable": True, "confidence": "high", "model": "stub", "backend": "vertex",
                 "cache_hit": "none", "stages": {"retrieve_ms": 400, "rerank_ms": 200, "generate_ms": 1500, "pool": 12}}


rv.fetch_current_shas = lambda *a, **k: set()
TMP = Path(tempfile.mkdtemp(prefix="lesson73-"))


def run_live(scenario: dict, name: str, api: str) -> tuple:
    seq = [0]

    def ask(api_url, question, tenant, email, token, retries=1):
        row = SCOPED[seq[0]]
        seq[0] += 1
        assert row["question"] == question and row["tenant"] == tenant
        status, b = reply(row, scenario.get(row["id"], "ok"))
        return status, b, 1000
    rv.ask = ask
    report = TMP / "evals" / "reports" / f"{name}73.json"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = rv.live(api, source=SOURCE, report=str(report))
    return buf.getvalue(), rc


def mask(text: str, name: str) -> str:
    out = []
    for line in text.splitlines():
        if line.startswith(("  latency ms", "  retrieve_ms", "  rerank_ms", "  generate_ms", "  pool")):
            line = re.sub(r"(p50|p95|avg)\s+[\d.]+", lambda m: f"{m.group(1)}   ...", line)
            line = re.sub(r"semantic cache hits \d+", "semantic cache hits ...", line)
        if "[info] quote_support_rate" in line:
            line = re.sub(r"\d+\.\d%", "  ...", line)
        out.append(line.replace(str(TMP / "evals" / "reports" / f"{name}73.json"), f"evals/reports/{name}73.json"))
    return "\n".join(out) + "\n"


base_out, base_rc = run_live({}, "base", API)
cand_out, cand_rc = run_live({"lk-04": "nofig"}, "cand", CAND)
assert base_rc == 0 and cand_rc == 0 and "rows that cost a point (1):" in cand_out, (base_rc, cand_rc)
base_tail = "\n".join(mask(base_out, "base").rstrip("\n").split("\n")[-3:])
OUT = {"gates": f">> {API}\n" + base_tail + "\n" + f">> {CAND}\n== eval gate: LIVE ==\n" + mask(cand_out, "cand")}
assert f"scoped to {SOURCE}: {len(SCOPED)} row(s) cite it" in OUT["gates"]
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}


def run_cell(body: str, cwd: Path, prelude: str = "", env: dict | None = None) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env=env or ENV)
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout


# ------------------------------------------------------------------ the cells
PY_ONE = """import json, os, subprocess
def gcloud(*a):
    cmd = ["gcloud", *a, "--region", os.environ["REGION"], "--project", os.environ["PROJECT"], "--format=json"]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
traffic = gcloud("run", "services", "describe", "documind-api")["status"]["traffic"]
live = max((t for t in traffic if t.get("percent")), key=lambda t: t["percent"])["revisionName"]
cand = next(t["revisionName"] for t in traffic if t.get("tag") == "candidate")
env = lambda rev: {e["name"]: e.get("value", "") for e in gcloud("run", "revisions", "describe", rev)["spec"]["containers"][0].get("env", [])}
a, b = env(live), env(cand)
print(f"live {live}   candidate {cand}")
diff = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
for k in diff:
    print(f"  {k:22} {a.get(k, '(unset)'):26} -> {b.get(k, '(unset)')}")
print(f"{len(diff)} setting(s) differ" + ("" if len(diff) == 1 else " - not one controlled change yet"))"""

PY_COMPARE = """import json
base, cand = (json.load(open(f"evals/reports/{n}73.json", encoding="utf-8")) for n in ("base", "cand"))
print(f"  {'':21} {'live':>7} {'candidate':>10}  {'needs':>5}")
for k in base["scores"]:
    if k in base["judged"] or k in cand["judged"]:
        flag = "  FAIL" if k in cand["failed"] else ""
        print(f"  {k:21} {base['scores'][k]:7.1%} {cand['scores'][k]:10.1%}  {base['thresholds'][k]:5.0%}{flag}")
was = {r["id"]: r["pass"] for r in base["records"]}
moved = [r for r in cand["records"] if was.get(r["id"]) != r["pass"]]
for r in moved:
    print(f"  {r['id']}: {'pass' if was.get(r['id']) else 'fail'} on live, {'pass' if r['pass'] else 'fail'} on the candidate ({r['why'] or r['outcome']})")
med = lambda rep: sorted(x["latency_ms"] for x in rep["records"])[len(rep["records"]) // 2]
print(f"  {len(moved)} row(s) changed verdict; median round trip {med(base)} ms live, {med(cand)} ms candidate")"""

PY_DELTA = """import os, sys; sys.path.insert(0, "evals")
from usage_rows import read_rows, group
per = {g["model"]: g for g in group(read_rows(os.environ["PROJECT"], 1), ("model",))}
for m, g in per.items():
    print(f"  {m:24} {g['answers']:4} answers  Rs {g['inr']:7.2f}  Rs {g['inr'] / g['answers']:.4f} an answer")
live, cand = per.get("gemini-3.6-flash"), per.get("gemini-3.1-flash-lite")
if live and cand:
    d = live["inr"] / live["answers"] - cand["inr"] / cand["answers"]
    print(f"  the candidate costs Rs {d:.4f} less an answer: Rs {d * 1000:,.0f} per 1,000 answers")"""


def heredoc(body: str) -> str:
    return f"python - <<'PY'\n{body}\nPY"


CELLS = {
    "candidate": (f'make candidate PROJECT="$PROJECT" GENERATOR_MODEL={NEW_MODEL}\n'
                  'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"'),
    "one": heredoc(PY_ONE),
    "gates": (f'make eval-live PROJECT="$PROJECT" SOURCE={SOURCE} REPORT=evals/reports/base73.json | tail -3\n'
              f'make eval-live PROJECT="$PROJECT" SOURCE={SOURCE} REPORT=evals/reports/cand73.json API="$CAND"'),
    "compare": heredoc(PY_COMPARE),
    "judge": 'make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" API_B="$CAND" JUDGE_ARGS="--rows 20"',
    "delta": heredoc(PY_DELTA),
    "cleanup": ('gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate\n'
                'rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag\n'
                'curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"'),
}

# the comparison cell, over the stub's two reports
OUT["compare"] = run_cell(PY_COMPARE, TMP)
OUT["compare"] = re.sub(r"median round trip \d+ ms live, \d+ ms candidate", "median round trip ... ms live, ... ms candidate", OUT["compare"])
assert "lk-04: pass on live, fail on the candidate (answered without ['15'])" in OUT["compare"], OUT["compare"]

# a fake gcloud for the two lane cells: two revisions' settings, and usage rows for both models
LIVE_ENV = {"GENERATOR_MODEL": "gemini-3.6-flash", "RAG_MODEL_BASE": "gemini-3.6-flash", "ROUTING": "off", "MODEL_BACKEND": "vertex",
            "ARMOR": "off", "SEMANTIC_CACHE": "off", "RETRIEVAL_CURRENT_ONLY": "off", "RETRIEVAL_GRAPH": "off", "GIT_SHA": "abc1234"}
CAND_ENV = {**LIVE_ENV, "GENERATOR_MODEL": NEW_MODEL}
USAGE = ([{"jsonPayload": {"event": "query", "model": "gemini-3.6-flash", "tokens_in": 2000, "tokens_out": 300, "cost_usd": 0.00525, "latency_ms": 3000}}] * 30
         + [{"jsonPayload": {"event": "query", "model": NEW_MODEL, "tokens_in": 2000, "tokens_out": 300, "cost_usd": 0.00095, "latency_ms": 1800}}] * 30)
FAKE = ("import json, sys, types\n"
        "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
        f"LIVE, CAND, USAGE = {json.dumps(LIVE_ENV)}, {json.dumps(CAND_ENV)}, {json.dumps(USAGE)}\n"
        "def run(cmd, **kw):\n"
        "    if cmd[1:4] == ['run', 'services', 'describe']:\n"
        "        return R(json.dumps({'status': {'traffic': [{'revisionName': 'rev-live', 'percent': 100}, {'revisionName': 'rev-cand', 'tag': 'candidate'}]}}))\n"
        "    if cmd[1:4] == ['run', 'revisions', 'describe']:\n"
        "        env = LIVE if cmd[4] == 'rev-live' else CAND\n"
        "        return R(json.dumps({'spec': {'containers': [{'env': [{'name': k, 'value': v} for k, v in env.items()]}]}}))\n"
        "    if cmd[1:3] == ['logging', 'read']:\n"
        "        return R(json.dumps(USAGE))\n"
        "    raise SystemExit('unexpected command: ' + ' '.join(cmd))\n"
        "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
fake_env = {**ENV, "REGION": "asia-south1", "PROJECT": "documind-ai-YOUR-ID"}
one = run_cell(PY_ONE, TMP, FAKE, fake_env)
assert one.splitlines()[-1] == "1 setting(s) differ" and f"GENERATOR_MODEL        gemini-3.6-flash           -> {NEW_MODEL}" in one, one
OUT["one"] = one.replace("rev-live", "documind-api-000NN-xxx").replace("rev-cand", "documind-api-000NN-yyy")
(TMP / "evals" / "usage_rows.py").write_bytes((KIT / "evals" / "usage_rows.py").read_bytes())
delta = run_cell(PY_DELTA, TMP, FAKE, fake_env)
assert "30 answers" in delta and "less an answer" in delta, delta
OUT["delta"] = re.sub(r"Rs +[\d.,]+", "Rs ...", delta).replace("   30 answers", "  ... answers")
shutil.rmtree(TMP, ignore_errors=True)

OUT["candidate"] = ("gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\\n"
                    f"  --update-env-vars \"^|^GENERATOR_MODEL={NEW_MODEL}|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|...\" --remove-env-vars GENERATOR_LOCATION\n"
                    "...\n"
                    ">> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)\n"
                    f">> candidate: {CAND} (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)\n"
                    f"CAND={CAND}\n")
mk = (KIT / "Makefile").read_text(encoding="utf-8")
assert "(deploy/.candidate-revision - make promote moves traffic to it by name)" in mk and "(no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)" in mk
KEYS = (["groundedness/mean"] + [f"groundedness/mean[{s}]" for s in sorted({g['shape'] for g in FIRST20})] + ["groundedness/std", "instruction_following/mean",
        "instruction_following/std", "pairwise_question_answering_quality/baseline_model_win_rate", "pairwise_question_answering_quality/candidate_model_win_rate"])
OUT["judge"] = (f">> {API}\n"
                f"  20/{len(FIRST20)} answers collected from {API} in ...s (model gemini-3.6-flash)\n"
                f"  20/{len(FIRST20)} candidate answers from {CAND}\n"
                "  context: .../... cited chunks read in full from the store\n"
                "  trajectories: off (no --chat-url)\n"
                "  pointwise: GROUNDEDNESS + INSTRUCTION_FOLLOWING  (templates cd7070; run api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070)\n"
                "  judge: the service default (pass --judge-model to pin one)\n\n"
                "  Experiments run documind-eval/api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070:\n"
                + "".join(f"    {k:48} ...\n" for k in KEYS) + f"    {'row_count':48} 20.000\n\n"
                "  the gate (run_eval.py) still decides; this judge explains. Where they disagree, read the row.\n")
assert '"  {sum(r[\'status\'] == 200 for r in cand)}/{len(cand)} candidate answers from {a.api_b}"' in (KIT / JG).read_text(encoding="utf-8")
OUT["cleanup"] = "...\nthe candidate URL now: HTTP 404\n"


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "candidate": "run in the operator shell, in the kit (a new revision with no traffic; nothing moves for users)",
    "one": "run in the operator shell, in the kit (reads both revisions; changes nothing)",
    "gates": f"run in the operator shell, in the kit (the {len(SCOPED)} rows that cite the handbook, on each revision: a few minutes)",
    "compare": "run in the operator shell, in the kit (reads the two reports; changes nothing)",
    "judge": "run in the operator shell, in the kit (twenty rows on each revision, then the Evaluation service)",
    "delta": "run in the operator shell, in the kit (the last hour of usage rows, by model)",
    "cleanup": "run in the operator shell, in the kit (the candidate's tag and its recorded name removed; the live revision is untouched)",
}
OUT_LABELS = {
    "candidate": "shape (gcloud's own progress lines are left out; the two >> lines are make's)",
    "one": "(this cell, run against a fake gcloud with two revisions' settings; your revision names differ)",
    "gates": "shape (run_eval.py's own code over a stub API; the stub's candidate misses one row on purpose, and your rows, rates and times are your lane's)",
    "compare": "(this cell over the stub's two reports)",
    "judge": "shape (the metric names are SDK 2.1.0's; every ... is your lane's; the SDK's progress lines are left out)",
    "delta": "shape (this cell, run against fake usage rows; your counts and rupees are your lane's)",
    "cleanup": "(gcloud's traffic table first)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
WIN["SDK_WIN"] = ('<div class="cw"><div class="ch-bar"><span>vertexai evaluation, google-cloud-aiplatform 2.1.0 - the two win rates, as the SDK computes them</span>'
                  '<span class="ro">read only</span></div><pre tabindex="0">' + pb.hl(SDK_WIN) + "</pre></div>\n")

# ------------------------------------------------------------------ the planner: the settings make candidate writes, and cost.price()
cost_src = (KIT / COST).read_text(encoding="utf-8")
tree = ast.parse(cost_src)
FALLBACK = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")
ns = {"os": os, "USD_INR": 85.0, "FALLBACK": FALLBACK, "_prices": lambda: FALLBACK}
exec(ast.get_source_segment(cost_src, next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "price")), ns)
kit_price = ns["price"]
MODELS = ["gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-3.1-pro-preview"]
assert all(m in FALLBACK for m in MODELS)
defaults = dict(re.findall(r"^(GENERATOR_MODEL|ROUTING|ARMOR|SEMANTIC_CACHE|RETRIEVAL_CURRENT_ONLY|RETRIEVAL_GRAPH) +\?= (\S+)", mk, re.M))
deploy = (KIT / "commands" / "lesson-12.2.sh").read_text(encoding="utf-8")
for k, v in defaults.items():
    assert f"{k}=${{{k}-{v}}}" in deploy, (k, v)       # the live API is deployed with the same defaults make candidate writes
SETTINGS = [
    {"k": "GENERATOR_MODEL", "base": defaults["GENERATOR_MODEL"], "opts": MODELS, "kind": "model",
     "what": "the model behind every answer", "how": "the scoped live gate on both revisions, the pairwise judge, make usage by model"},
    {"k": "ROUTING", "base": defaults["ROUTING"], "opts": ["off", "on"], "kind": "routing",
     "what": "on: each question is classified and the budget breaker picks the tier", "how": "the full live gate, and make usage by model: the router moves answers between models"},
    {"k": "SEMANTIC_CACHE", "base": defaults["SEMANTIC_CACHE"], "opts": ["off", "on"], "kind": "cache",
     "what": "on: a near-enough earlier question is answered from Firestore, with no retrieval and no model call", "how": "lesson 6.4's threshold curve first; with it on, a repeated question replays an earlier answer, so a pairwise run compares replays"},
    {"k": "ARMOR", "base": defaults["ARMOR"], "opts": ["off", "on"], "kind": "safety",
     "what": "on: Model Armor screens the prompt and the answer", "how": "the full live gate: a blocked prompt is a 400, which the gate counts as a failed request (lesson 4.8)"},
    {"k": "RETRIEVAL_CURRENT_ONLY", "base": defaults["RETRIEVAL_CURRENT_ONLY"], "opts": ["off", "on"], "kind": "retrieval",
     "what": "on: only the chunks the ledger marks current are retrieved", "how": "retrieval only: make ablate first, with no model, then the scoped gate on a candidate"},
    {"k": "RETRIEVAL_GRAPH", "base": defaults["RETRIEVAL_GRAPH"], "opts": ["off", "on", "auto"], "kind": "retrieval",
     "what": "on or auto: the tenant's knowledge graph puts its chunks ahead of the dense pool", "how": "retrieval only: make ablate first, with no model, then the scoped gate on a candidate"},
]
PLAN = {"settings": SETTINGS, "prices": {m: list(FALLBACK[m]) for m in MODELS}, "usdInr": 85}

PRICE_JS = r"""function price(P, model, tin, tout, cached){                                       /* cost.price() */
    var p = P.prices[model] || P.prices['gemini-3.6-flash'], billable = Math.max(tin - cached, 0);
    var usd = (billable * p[0] + cached * p[0] * 0.10 + tout * p[1]) / 1e6;
    return {usd: usd, inr: usd * P.usdInr}; }"""
cases = [(m, tin, tout, c) for m in MODELS for tin, tout, c in ((2000, 300, 0), (7832, 900, 4096), (168, 1, 0), (12000, 2048, 12000), (500, 0, 600))]
test_js = ("'use strict';\n" + PRICE_JS + "\nvar P = " + json.dumps(PLAN) + ";\nvar cases = " + json.dumps(cases) + ";\n"
           "console.log(JSON.stringify(cases.map(function(c){ return price(P, c[0], c[1], c[2], c[3]); })));\n")
tjs = Path(tempfile.mkdtemp(prefix="lesson73-js-")) / "price.js"
tjs.write_text(test_js, encoding="utf-8")
node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(tjs.parent, ignore_errors=True)
assert node.returncode == 0, node.stderr[-600:]
for (m, tin, tout, c), js in zip(cases, json.loads(node.stdout)):
    k = kit_price(m, tin, tout, c)
    assert abs(k["usd"] - js["usd"]) < 5e-7 and abs(k["inr"] - js["inr"]) < 5e-5, (m, tin, tout, c, k, js)

UI_JS = r"""var root = document.getElementById('planner'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var list = $('cp-list'), verdict = $('cp-verdict'), money = $('cp-money'), fields = ['cp-tin', 'cp-tout', 'cp-cached', 'cp-vol'];
  var cand = {}; P.settings.forEach(function(s){ cand[s.k] = s.base; }); cand.GENERATOR_MODEL = 'gemini-3.1-flash-lite';
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function num(id){ var v = parseFloat($(id).value); return isFinite(v) && v > 0 ? v : 0; }
  function rs(x, d){ return 'Rs ' + x.toLocaleString('en-IN', {minimumFractionDigits: d, maximumFractionDigits: d}); }
  function render(){
    list.innerHTML = P.settings.map(function(s){ var ch = cand[s.k] !== s.base;
      return '<p class="cp-set' + (ch ? ' changed' : '') + '"><span><b>' + s.k + '</b><small>' + esc(s.what) + '</small></span><span>live: <b>' + s.base + '</b></span><span><select data-k="' + s.k + '" aria-label="' + s.k + ' on the candidate">'
        + s.opts.map(function(o){ return '<option' + (o === cand[s.k] ? ' selected' : '') + '>' + o + '</option>'; }).join('') + '</select></span></p>'; }).join('');
    var changed = P.settings.filter(function(s){ return cand[s.k] !== s.base; }), n = changed.length;
    verdict.innerHTML = '<span class="cp-verdict v' + Math.min(n, 2) + '">' + n + ' change' + (n === 1 ? '' : 's') + '</span> '
      + (n === 0 ? 'The candidate would be the live revision again: nothing to compare.'
        : n === 1 ? 'One change: whatever differs in the gate, the judge or the price belongs to ' + changed[0].k + '.'
        : 'The comparison cannot say which of ' + changed.map(function(s){ return s.k; }).join(', ') + ' moved the numbers. Split them into ' + n + ' candidates, one at a time.')
      + (n ? '<ul>' + changed.map(function(s){ return '<li><b>' + s.k + '</b>: ' + esc(s.how) + '</li>'; }).join('') + '</ul>' : '');
    var tin = num('cp-tin'), tout = num('cp-tout'), cached = Math.min(num('cp-cached'), tin), vol = num('cp-vol');
    var a = price(P, P.settings[0].base, tin, tout, cached), b = price(P, cand.GENERATOR_MODEL, tin, tout, cached), d = a.inr - b.inr;
    money.textContent = 'live       ' + P.settings[0].base + ': ' + rs(a.inr, 4) + ' an answer\ncandidate  ' + cand.GENERATOR_MODEL + ': ' + rs(b.inr, 4) + ' an answer\n'
      + (d === 0 ? 'no difference in price' : (d > 0 ? 'the candidate saves ' : 'the candidate costs ') + rs(Math.abs(d), 4) + ' an answer, ' + rs(Math.abs(d) * 1000, 2)
        + ' per 1,000, ' + rs(Math.abs(d) * vol, 0) + ' a month at ' + vol.toLocaleString('en-IN') + ' answers');
  }
  list.addEventListener('change', function(e){ var k = e.target.getAttribute('data-k'); if (k) { cand[k] = e.target.value; render(); } });
  fields.forEach(function(id){ $(id).addEventListener('input', render); });
  render();"""

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\nvar P = " + json.dumps(PLAN, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n"
      + squeeze(PRICE_JS) + "\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert JS.count("<div") == JS.count("</div>") and "<tr" not in JS

# ------------------------------------------------------------------ numbers for the prose
flash, lite = FALLBACK["gemini-3.6-flash"], FALLBACK[NEW_MODEL]
ex_flash, ex_lite = kit_price("gemini-3.6-flash", 2000, 300), kit_price(NEW_MODEL, 2000, 300)
STATS = {
    "N_SCOPED": str(len(SCOPED)), "N_ROWS": str(len(golden)), "N_THRESHOLDS": str(len(rv.THRESHOLDS)), "NEW_MODEL": NEW_MODEL,
    "FLASH_IN": f"{flash[0]:.2f}", "FLASH_OUT": f"{flash[1]:.2f}", "LITE_IN": f"{lite[0]:.2f}", "LITE_OUT": f"{lite[1]:.2f}",
    "EX_FLASH": f"{ex_flash['inr']:.4f}", "EX_LITE": f"{ex_lite['inr']:.4f}", "EX_SAVE_1K": f"{(ex_flash['inr'] - ex_lite['inr']) * 1000:,.0f}",
    "N_JUDGE_REQ": str(3 * len(FIRST20)), "N_ANSWERS": str(2 * len(SCOPED) + 2 * len(FIRST20)), "USD_INR": f"{PLAN['usdInr']}",
}
assert 'if [ -n "$$TAGGED" ] && [ "$$TAGGED" != "$$CAND" ]' in mk and "deploy/.candidate-revision is missing" in mk   # promote follows the file, not the tag


if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {len(SCOPED)} rows cite {SOURCE} | stub gates exit {base_rc}/{cand_rc} | one-change and rupee cells tested on a fake gcloud"
      f" | price() equal in node on {len(cases)} cases | {NEW_MODEL} {lite[0]}/{lite[1]} against flash {flash[0]}/{flash[1]}")
