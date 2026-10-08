"""Build lesson 4.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

What the page prints is the kit's own output wherever a build can produce it. The offline gate and the judge's
self-test are run here. The live gate's expected block, the report's arithmetic and the gate-beside-judge cell are
printed by run_eval.live() and the lesson's own cells over a stub API that misses two rows on purpose (the page
says so, and masks the values that belong to a lane). CI's verdict comes from the public GitHub API, captured once
into data/dryrun_runs.json. The judge's metric names, their scales and its template hash are the pinned SDK's
(google-cloud-aiplatform 2.1.0, read when the page was written). The threshold board ports live()'s aggregate
arithmetic to JavaScript; for every preset the build runs the kit's live() on a stub that answers each row the way
the preset says, and node must reproduce its nine scores, failed thresholds, required failures, exit code and verdict.
"""
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

LESSON = "4.2"
title = "<title>Lesson 4.2 Separate offline checks, live scoring and LLM judgment - the gate on every push, the gate on a deployment, and the judge that explains but never decides | Netsetos</title>\n"
LANE = "/home/you/deploy_module_rag"
API = "https://documind-api-NUMBER.asia-south1.run.app"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.tb-presets{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px;}
.tb-presets button{font:inherit;font-size:13px;background:#f0fdfa;color:var(--teal-dark);border:1px solid #99f6e4;border-radius:999px;padding:6px 12px;min-height:44px;cursor:pointer;}
.tb-shape{font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;color:var(--slate);margin:6px 0 4px;}
.tb-chips{display:flex;flex-wrap:wrap;gap:4px;}
.tb-chips button{font-family:var(--mono);font-size:11.5px;min-width:52px;min-height:44px;padding:2px 6px;border-radius:8px;border:1px solid #a7f3d0;background:#ecfdf5;color:#065f46;cursor:pointer;}
.tb-chips button.no{border-color:#fca5a5;background:#fef2f2;color:#991b1b;}
.tb-chips button.req{box-shadow:inset 0 -3px 0 #0f766e;}
.tb-chips button.sel{outline:2px solid var(--navy);outline-offset:1px;}
.tb-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:10px 0;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.tb-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.tb-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;margin-top:6px;}
.tb-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.tb-row{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,.9fr) minmax(0,.9fr) minmax(0,.7fr);gap:6px;font-family:var(--mono);font-size:12px;padding:3px 0;border-bottom:1px solid var(--border);align-items:baseline;}
.tb-row span{min-width:0;overflow-wrap:anywhere;}
.tb-row small{display:block;color:var(--slate);font-size:10.5px;}
.tb-pass{color:#047857;font-weight:700;}.tb-fail{color:#b91c1c;font-weight:700;}.tb-off{color:#94a3b8;}
.tb-exit{font-family:var(--mono);font-size:13px;font-weight:700;padding:6px 10px;border-radius:8px;display:inline-block;margin-bottom:6px;}
.tb-exit.e0{background:#d1fae5;color:#065f46;}.tb-exit.e1{background:#fef3c7;color:#92400e;}.tb-exit.e2{background:#fee2e2;color:#991b1b;}
@media (hover:hover) and (pointer:fine){.tb-presets button:hover,.tb-chips button:hover{filter:brightness(.96);}}
.tb-presets button:active,.tb-chips button:active{filter:brightness(.9);}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
RE_, JG = "evals/run_eval.py", "evals/judge.py"
DRY, CD = ".github/workflows/documind-dryrun.yml", ".github/workflows/documind-cd.yml"

EXCERPTS = {
    "dryrun": (".github/workflows/documind-dryrun.yml - on every push, the offline half last",
               block(DRY, "on:", n=4) + "\n...\n" + block(DRY, "      # The eval gate, offline half.", n=5)),
    "cd_path": (".github/workflows/documind-cd.yml - the release path: a no-traffic candidate, the live gate on it, a person, the flip",
                block(CD, "  # Module 10's seam as a pipeline, keyless.", n=5) + "\n...\n" + block(CD, "      - name: The live gate, on the candidate", n=4)),
    "eval_live": ("Makefile - eval-live: two tokens for the service's own URL, then the live half",
                  block("Makefile", "# The token's audience is the SERVICE's canonical URL", n=12)),
    "thresholds": ("evals/run_eval.py - THRESHOLDS: nine numbers in one place",
                   block(RE_, "# What a green run has to clear.", end="MIN_ROWS = ")),
    "every_row": ("evals/run_eval.py - live(): every row is sent, answerable or not",
                  block(RE_, "    # EVERY row is sent, not just the answerable ones.", n=7)),
    "outsider_guard": ("evals/run_eval.py - live(): no outsider token, no run",
                       block(RE_, '    if token and not outsider_token and any(r["shape"] == "isolation" for r in golden):', n=6)),
    "rates": ("evals/run_eval.py - live(): nine rates, each over its own rows",
              block(RE_, "    scores = {", n=11)),
    "exit_logic": ("evals/run_eval.py - live(): a leak is exit 2, anything else that fails is exit 1",
                   block(RE_, "    # A must_not_contain hit is not in the thresholds, on purpose - see")),
    "judge_doc": ("evals/judge.py - the other judge",
                  block(JG, "run_eval.py is the gate: nine thresholds", n=6)),
    "judge_target": ("Makefile - judge: the same token, the judge's own flags",
                     block("Makefile", "# The second judge (10.4)", n=4) + "\n...\n" + block("Makefile", "	  $(PY) evals/judge.py --api-url $$API --project $(PROJECT)", n=2)),
    "enrich": ("evals/judge.py - enrich_context(): the judge reads the chunks the answer cited, in full",
               block(JG, "def enrich_context(", n=6)),
    "prompt_shape": ("evals/judge.py - to_frame(): the context goes into the prompt, because the template reads nothing else",
                     block(JG, "    # The catalogue's GROUNDEDNESS reads `prompt` and `response` and nothing else", n=8)),
    "metrics": ("evals/judge.py - pointwise_metrics(): the second metric, resolved by name",
                block(JG, "def pointwise_metrics():", end="def revision_sha(")),
    "by_shape": ("evals/judge.py - evaluate(): groundedness by shape, because a refusal has nothing to be grounded in",
                 block(JG, "    # By shape, from the per-row table:", n=9)),
    "traj": ("evals/judge.py - the reference trajectory, and three ways to match it",
             block(JG, 'REFERENCE_TRAJECTORY = [{"tool_name": "retrieve"}]', n=1) + "\n...\n" + block(JG, "def trajectory_metrics(", end="def trajectories(")),
    "judge_close": ("evals/judge.py - main(): the judge's last line",
                    block(JG, "the gate (run_eval.py) still decides", n=1)),
}
assert EXCERPTS["dryrun"][1].startswith("on:\n  push:") and EXCERPTS["dryrun"][1].rstrip().endswith("run: python evals/run_eval.py")
assert EXCERPTS["cd_path"][1].rstrip().endswith('API="https://candidate---documind-api-$NUMBER.$REGION.run.app"')
assert EXCERPTS["eval_live"][1].rstrip().endswith("$(if $(REPORT),--report $(REPORT),)"), EXCERPTS["eval_live"][1][-80:]
assert EXCERPTS["thresholds"][1].rstrip().endswith("}") and EXCERPTS["thresholds"][1].count(":") >= 9
assert EXCERPTS["every_row"][1].rstrip().endswith("a clean 100%.")
assert EXCERPTS["outsider_guard"][1].rstrip().endswith("return 2")
assert EXCERPTS["rates"][1].rstrip().endswith("}") and '"correct_rate": correct / n' in EXCERPTS["rates"][1]
assert EXCERPTS["exit_logic"][1].rstrip().endswith("return 0")
assert EXCERPTS["prompt_shape"][1].rstrip().endswith('f"\\n\\nQuestion: {r[\'question\']}" for r in rows],'), EXCERPTS["prompt_shape"][1][-80:]
assert EXCERPTS["by_shape"][1].rstrip().endswith("pass")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's numbers
sys.path.insert(0, str(KIT / "evals"))
import run_eval as rv  # noqa: E402
import judge as jd  # noqa: E402

golden = rv.load_golden()
required = set(rv.load_required())
N_ANS = sum(r["answerable"] for r in golden)
per_tenant = {t: sum(r["tenant"] == t for r in golden) for t in ("acme", "zeta", "globex")}
ISO = [r for r in golden if r["shape"] == "isolation"]
MEDIA = [r for r in golden if r.get("must_cite_kind")]
OUTSIDER = "outsider@not-a-tenant.invalid"
for k in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "DOCUMIND_USER_EMAIL", "DOCUMIND_OUTSIDER_EMAIL"):
    os.environ.pop(k, None)

# ------------------------------------------------------------------ a stub API: each row answered the way a scenario says
NOFIG = {"jn-06": "EMEA revenue fell in FY2026 [1]."}


def reply(row: dict, outcome: str) -> tuple:
    t, mc, mnc = row["tenant"], row.get("must_contain", []), row.get("must_not_contain", [])
    other = "globex" if t != "globex" else "acme"

    def cite(tenant=t, kind=None):
        return {"chunk_id": f"{tenant}:lesson#0", "source_uri": f"gs://lesson/{tenant}/doc.md", "quote": mc[0] if mc else "lesson",
                "kind": kind or row.get("must_cite_kind") or "text"}

    def body(answer, cites, answerable, conf="high"):
        return 200, {"answer": answer, "citations": cites, "answerable": answerable, "confidence": conf, "model": "gemini-3.6-flash",
                     "backend": "vertex", "cache_hit": "none", "stages": {"retrieve_ms": 400, "rerank_ms": 200, "generate_ms": 1500, "pool": 12}}
    fig = " and ".join(mc)
    if outcome == "err":
        return 500, {}
    if outcome == "bad":
        return 200, {}
    if outcome == "denied":
        return 403, {}
    if row["answerable"]:
        table = {"ok": (f"{fig} [1].", [cite()], True), "refused": ("The documents do not say.", [], False),
                 "nofig": (NOFIG.get(row["id"], "The documents cover this [1]."), [cite()], True),
                 "badcite": (f"{fig} [1].", [cite(other)], True), "nocite": (f"{fig}.", [], True),
                 "kind": (f"{fig} [1].", [cite(kind="text")], True)}
        if mnc:
            table["leak"] = (f"{fig}, and {mnc[0]} [1].", [cite()], True)
            table["stale"] = (f"{mnc[0]} [1].", [cite()], True)
    else:
        table = {"ok": ("The documents do not say.", [], False), "answered": ("Here is what the documents say [1].", [cite()], True)}
        if mnc:
            table["leak"] = (f"{mnc[0]} [1].", [cite()], True)
    answer, cites, answerable = table[outcome]
    return body(answer, cites, answerable, "high" if answerable else "low")


def stub_ask(scenario: dict, let_in: int = 0):
    member, outsider = [0], [0]

    def ask(api_url, question, tenant, email, token, retries=1):
        if email == OUTSIDER:
            outsider[0] += 1
            return (200, {"answer": "x", "citations": [], "answerable": False, "confidence": "low"}, 900) if let_in and outsider[0] == 1 else (403, {}, 120)
        row = golden[member[0] % len(golden)]
        member[0] += 1
        assert row["question"] == question and row["tenant"] == tenant, (row["id"], question)
        status, b = reply(row, scenario.get(row["id"], "ok"))
        return status, b, 1000
    return ask


rv.fetch_current_shas = lambda *a, **k: set()           # the ledger answers; the stub's ids carry no worker sha to check
TMP = Path(tempfile.mkdtemp(prefix="lesson72-"))


def run_live(scenario: dict, let_in: int = 0) -> tuple:
    rv.ask = stub_ask(scenario, let_in)
    report = TMP / "evals" / "reports" / "lesson72.json"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = rv.live(API, report=str(report))
    return buf.getvalue(), rc, json.loads(report.read_text(encoding="utf-8"))


# the page's live run: two rows missed on purpose, and the lane's own values masked
MISSES = {"lk-27": "refused", "jn-06": "nofig"}
live_out, live_rc, live_report = run_live(MISSES)
assert live_rc == 0 and not live_report["failed"], (live_rc, live_report["failed"])


def mask(text: str) -> str:
    out = []
    for line in text.splitlines():
        if line.startswith(("  latency ms", "  retrieve_ms", "  rerank_ms", "  generate_ms", "  pool")):
            line = re.sub(r"(p50|p95|avg)\s+[\d.]+", lambda m: f"{m.group(1)}   ...", line)
            line = re.sub(r"semantic cache hits \d+", "semantic cache hits ...", line)
        if "[info] quote_support_rate" in line:
            line = re.sub(r"\d+\.\d%", "  ...", line)
        out.append(line.replace(str(TMP / "evals" / "reports" / "lesson72.json"), "evals/reports/lesson72.json"))
    return "\n".join(out) + "\n"


OUT = {"live": f">> {API}\n== eval gate: LIVE ==\n" + mask(live_out)}
assert "rows that cost a point (2):" in OUT["live"] and "All thresholds met." in OUT["live"]

# the judge's collection over the same stub, for the side-by-side cell
jd.ask = stub_ask(MISSES)
collected = jd.collect(API, golden, None, "eval@documind.in")
(TMP / "evals" / "reports" / "judge72.json").write_text(json.dumps(collected, ensure_ascii=False), encoding="utf-8")
shutil.copy2(KIT / "evals" / "golden.jsonl", TMP / "evals" / "golden.jsonl")
shutil.copy2(KIT / "evals" / "run_eval.py", TMP / "evals" / "run_eval.py")
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}


def run_cell(body: str, cwd: Path) -> str:
    r = subprocess.run([sys.executable, "-"], input=body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env=ENV)
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout


# ------------------------------------------------------------------ the cells
PY_CI = """import json, subprocess, urllib.request
url = "https://api.github.com/repos/netsetos/agents_workshop_learner/actions/workflows/documind-dryrun.yml/runs?per_page=3"
runs = json.load(urllib.request.urlopen(url, timeout=30))["workflow_runs"]
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
print("your kit is at", head[:7])
for r in runs:
    mark = "  <- the commit you run" if r["head_sha"] == head else ""
    print(f"  {r['head_sha'][:7]}  {r['event']:5} {r['conclusion'] or r['status']:8} {r['created_at'][:10]}{mark}")"""

PY_ARITH = """import json
r = json.load(open("evals/reports/lesson72.json", encoding="utf-8"))
gold = {g["id"]: g for g in map(json.loads, open("evals/golden.jsonl", encoding="utf-8"))}
rec = r["records"]
A = [x for x in rec if gold[x["id"]]["answerable"]]
answered = [x for x in A if x["outcome"] == "ok" and x["answerable"]]
contained = [x for x in answered if not x["why"].startswith("answered without")]
U = [x for x in rec if not gold[x["id"]]["answerable"]]
refused = [x for x in U if x["outcome"] == "ok" and not x["answerable"]]
print(f"  answerable_rate    {len(answered):2} answered          of {len(A)} answerable rows")
print(f"  must_contain_rate  {len(contained):2} with the figure   of {len(answered)} ANSWERED")
print(f"  correct_rate       {sum(x['pass'] for x in A):2} right             of {len(A)} ANSWERABLE")
print(f"  refusal_rate       {len(refused):2} refused           of {len(U)} unanswerable rows")
for k, v in r["scores"].items():
    verdict = "FAIL" if k in r["failed"] else "pass" if k in r["judged"] else " -- "
    print(f"  {verdict}  {k:21} {v:6.1%}  (needs {r['thresholds'][k]:.0%})")
print("  cost a point:", ", ".join(f"{x['id']} ({x['why'] or x['outcome']})" for x in rec if not x["pass"]) or "nothing")"""

PY_SIDE = """import json, sys; sys.path.insert(0, "evals")
from run_eval import contains
gate = json.load(open("evals/reports/lesson72.json", encoding="utf-8"))["records"]
judged = {x["id"]: x for x in json.load(open("evals/reports/judge72.json", encoding="utf-8"))}
missed = [x for x in gate if not x["pass"]]
print(f"{len(missed)} row(s) cost the gate a point. The judge's own run answered them:")
for x in missed:
    j = judged.get(x["id"], {})
    figs = [f"{w} {'present' if contains(j.get('response', ''), w) else 'absent'}" for w in j.get("must_contain", [])]
    print(f"  {x['id']:6} gate: {x['why'] or x['outcome']}")
    print(f"         judge's answer: {j.get('response', '')[:80]!r}, {len(j.get('cited') or [])} cited")
    print(f"         {'; '.join(figs) or 'a refusal row: no figure to look for'}")"""


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


JV = '"$HOME/judge-venv/bin/python"'
CELLS = {
    "ci": heredoc(PY_CI),
    "gate": "make eval",
    "live": 'make eval-live PROJECT="$PROJECT" REPORT=evals/reports/lesson72.json',
    "arith": heredoc(PY_ARITH),
    "usage": "make usage PROJECT=\"$PROJECT\" HOURS=1 | sed -n '1,8p'",
    "judge_env": ('python -m venv "$HOME/judge-venv"            # its own venv: the SDK is a major version ahead of the kit\'s\n'
                  f'{JV} -m pip install -q "google-cloud-aiplatform[evaluation]==2.1.0" pandas google-cloud-firestore\n'
                  f"{JV} evals/judge.py --selftest"),
    "judge": ("mkdir -p evals/reports\n"
              'make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" JUDGE_ARGS="--reuse evals/reports/judge72.json"'),
    "side": heredoc(PY_SIDE),
    "traj": ('if gcloud run services describe documind-chat --region "$REGION" --project "$PROJECT" --format=\'value(metadata.name)\' >/dev/null 2>&1; then\n'
             '  CHAT_URL="https://documind-chat-$NUMBER.$REGION.run.app"   # its SELF_URL, not status.url: the token is minted for it\n'
             '  make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" CHAT_URL="$CHAT_URL" \\\n'
             '    JUDGE_ARGS="--reuse evals/reports/judge72.json --no-vertex --trajectory-rows 3" | grep -E "reused|trajectory"\n'
             'else echo "no documind-chat service on this lane: trajectories need one"; fi'),
}

# the offline gate, as it runs in CI
r = subprocess.run([sys.executable, "evals/run_eval.py"], cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=ENV)
assert r.returncode == 0 and "[PASS] coverage" in r.stdout, r.stdout[-400:]
OUT["gate"] = "python evals/run_eval.py\n" + r.stdout
runs = json.loads(pb.data(LESSON, "dryrun_runs.json").read_text(encoding="utf-8"))["workflow_runs"]
OUT["ci"] = f"your kit is at {runs[0]['head_sha'][:7]}\n" + "".join(
    f"  {x['head_sha'][:7]}  {x['event']:5} {x['conclusion'] or x['status']:8} {x['created_at'][:10]}{'  <- the commit you run' if i == 0 else ''}\n"
    for i, x in enumerate(runs))
OUT["arith"] = run_cell(PY_ARITH, TMP)
OUT["side"] = run_cell(PY_SIDE, TMP)
assert "2 row(s) cost the gate a point" in OUT["side"] and "45 right" in OUT["arith"], (OUT["side"], OUT["arith"])
r = subprocess.run([sys.executable, "evals/judge.py", "--selftest"], cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=ENV)
assert r.returncode == 0 and r.stdout.startswith("selftest:"), (r.stdout, r.stderr[-400:])
OUT["judge_env"] = r.stdout
OUT["usage"] = (f"{len(golden)} answers from documind-api in the last 1 h; USD_INR=85\n\nby tenant\n"
                + f"{'tenant':22}{'answers':>8} {'tok_in':>9} {'tok_out':>8} {'USD':>9} {'INR':>9} {'p95 ms':>7} {'unans':>6}\n"
                + "-" * 82 + "\n"
                + "".join(f"{t:22}{n:>8} {'...':>9} {'...':>8} {'...':>9} {'...':>9} {'...':>7} {'...':>6}\n" for t, n in per_tenant.items()))
TEMPLATE_HASH, SECOND = "cd7070", "INSTRUCTION_FOLLOWING"          # google-cloud-aiplatform 2.1.0: judge.template_hash(), pointwise_metrics()
OUT["judge"] = (f">> {API}\n"
                f"  {len(golden)}/{len(golden)} answers collected from {API} in ...s (model gemini-3.6-flash)\n"
                "  context: .../... cited chunks read in full from the store\n"
                "  trajectories: off (no --chat-url)\n"
                f"  pointwise: GROUNDEDNESS + {SECOND}  (templates {TEMPLATE_HASH}; run api-GITSHA-YYYYMMDD-HHMM-t{TEMPLATE_HASH})\n"
                "  pairwise: off (no --api-b)\n"
                "  judge: the service default (pass --judge-model to pin one)\n\n"
                f"  Experiments run documind-eval/api-GITSHA-YYYYMMDD-HHMM-t{TEMPLATE_HASH}:\n"
                + "".join(f"    {k:48} ...\n" for k in ["groundedness/mean"] + [f"groundedness/mean[{s}]" for s in sorted({g['shape'] for g in golden})]
                          + ["groundedness/std", "instruction_following/mean", "instruction_following/std"])
                + f"    {'row_count':48} {float(len(golden)):.3f}\n\n"
                "  the gate (run_eval.py) still decides; this judge explains. Where they disagree, read the row.\n")
for s in ('"  {len(ok)}/{len(rows)} answers collected from {a.api_url} in', '"  pairwise: off (no --api-b)"', '"  trajectories: off (no --chat-url)"',
          '"  judge: the service default (pass --judge-model to pin one)"', "    print(f\"\\n  Experiments run {a.experiment}/"):
    assert s in (KIT / JG).read_text(encoding="utf-8"), s
OUT["traj_none"] = "no documind-chat service on this lane: trajectories need one\n"
OUT["traj_chat"] = (f"  {len(golden)} rows reused from evals/reports/judge72.json (delete it to collect again)\n"
                    + "".join(f"  trajectory {b:10} exact .../3  in-order .../3  any-order .../3  mean calls ...\n" for b in jd.BRAINS))


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "ci": "run in the operator shell, in the kit (one unauthenticated call to GitHub's public API)",
    "gate": "run in the operator shell, in the kit (the offline half, as CI runs it)",
    "live": "run in the operator shell, in the kit (every row as the member, every isolation row as the outsider: about ten minutes)",
    "arith": "run in the operator shell, in the kit (reads the report; changes nothing)",
    "usage": "run in the operator shell, in the kit (the usage rows of the last hour, priced)",
    "judge_env": "run in the operator shell, in the kit (a second venv for the judge, then its offline self-test)",
    "judge": "run in the operator shell, in the kit (the lane answers every row again, then Vertex AI Evaluation reads them)",
    "side": "run in the operator shell, in the kit (reads both files; changes nothing)",
    "traj": "run in the operator shell, in the kit (nine chat turns if your lane has the chat service; nothing otherwise)",
}
OUT_LABELS = {
    "ci": "(captured when this page was built; a newer commit lists first on your lane)",
    "gate": "(the gate's own output, captured when this page was built)",
    "live": "shape (run_eval.py's own code over a stub API that misses two rows on purpose; your rates, rows and times are your lane's)",
    "arith": "(this cell over the stub's report above)",
    "usage": "shape (the counts assume nothing else asked the API in that hour; the rupees are your lane's)",
    "judge_env": "(the self-test's own line, captured when this page was built)",
    "judge": "shape (the metric names and the template hash are SDK 2.1.0's; every ... is your lane's; the SDK's progress lines are left out)",
    "side": "(this cell over the stub's two files)",
    "traj_none": "on a lane without the chat service",
    "traj_chat": "shape on a lane with it (the counts are your lane's)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the threshold board: presets, checked against the kit's live()
A_ROWS = [r for r in golden if r["answerable"]]
U_ROWS = [r for r in golden if not r["answerable"]]
PRESETS = [
    ("every row right", {}, 0),
    ("a 500 on one lookup", {"lk-08": "err"}, 0),
    ("four figures missed", {i: "nofig" for i in ("lk-01", "lk-02", "lk-03", "lk-05")}, 0),
    ("eight figures missed", {i: "nofig" for i in ("lk-01", "lk-02", "lk-03", "lk-05", "lk-07", "lk-09", "lk-10", "lk-11")}, 0),
    ("refuses everything", {r["id"]: "refused" for r in A_ROWS}, 0),
    ("answers everything", {r["id"]: "answered" for r in U_ROWS}, 0),
    ("a figure citation missing", {"mm-01": "kind"}, 0),
    ("the outsider let in once", {}, 1),
    ("one leak", {"iso-01": "leak"}, 0),
    ("a stale version", {"vr-01": "stale"}, 0),
    ("a 200 with an empty body", {"rf-02": "bad"}, 0),
]
KIT_RESULTS = []
for label, scenario, let_in in PRESETS:
    out, rc, rep = run_live(scenario, let_in)
    verdict = [line.strip() for line in out.splitlines() if line.strip()][-1]
    if rc == 2:
        verdict = next(line.strip() for line in out.splitlines() if "A must_not_contain row fired" in line)
    KIT_RESULTS.append({"scores": rep["scores"], "failed": rep["failed"], "req": [s.split(":")[0] for s in rep["required_failed"]],
                        "leaks": [s.split(":")[0] for s in rep["leaks"]], "stale": [s.split(":")[0] for s in rep["stale"]], "exit": rc, "verdict": verdict})
shutil.rmtree(TMP, ignore_errors=True)
assert [k["exit"] for k in KIT_RESULTS] == [0, 1, 0, 1, 1, 1, 1, 1, 2, 1, 1], [k["exit"] for k in KIT_RESULTS]

ROWS = [{"i": r["id"], "s": r["shape"], "t": r["tenant"], "a": int(r["answerable"]), "r": int(r["id"] in required),
         "k": r.get("must_cite_kind", ""), "m": int(bool(r.get("must_not_contain"))), "q": r["question"]} for r in golden]
BOARD = {"rows": ROWS, "thr": rv.THRESHOLDS, "presets": [[label, scenario, let_in] for label, scenario, let_in in PRESETS]}

CALC_JS = r"""function pct(x, d){ var v = x * Math.pow(10, 2 + d), f = Math.floor(v), r = Math.abs(v - f - 0.5) < 1e-9 ? (f % 2 ? f + 1 : f) : Math.round(v);
    return (d ? (r / 10).toFixed(1) : String(r)) + '%'; }                                 /* Python's .0% and .1%, half to even */
  function compute(B, outc, letIn){                                                        /* the aggregate half of run_eval.live() */
    var N = B.rows.length, n = 0, u = 0, ok = 0, answered = 0, cited = 0, citRows = 0, citValid = 0, contained = 0, correct = 0, refused = 0,
        kindRows = 0, kindHits = 0, isoN = 0, leaks = [], stale = [], req = [];
    B.rows.forEach(function(r){
      var o = outc[r.i] || 'ok', pass = false;
      if (r.a) n++; else u++;
      if (r.s === 'isolation') isoN++;
      if (o === 'err' || o === 'bad' || o === 'denied') { if (r.r) req.push(r.i); return; }
      ok++;
      var leak = o === 'leak' || o === 'stale';
      if (leak) (r.s === 'version' ? stale : leaks).push(r.i);
      if (r.a) {
        if (o !== 'refused') {
          answered++;
          var valid = false, kindOk = true;
          if (o !== 'nocite') { cited++; citRows++; valid = o !== 'badcite'; if (valid) citValid++; }
          if (r.k) { kindRows++; kindOk = o !== 'kind'; if (kindOk) kindHits++; }
          var has = o !== 'nofig' && o !== 'stale';
          if (has) contained++;
          pass = has && valid && kindOk && o !== 'leak';
          if (pass) correct++;
        }
      } else if (o === 'ok') { refused++; pass = true; }
      if (r.r && !pass) req.push(r.i);
    });
    var S = {request_success_rate: N ? ok / N : 0, answerable_rate: n ? answered / n : 0, citation_rate: cited / Math.max(answered, 1),
             citation_valid_rate: citValid / Math.max(citRows, 1), must_contain_rate: contained / Math.max(answered, 1), correct_rate: n ? correct / n : 0,
             refusal_rate: u ? refused / u : 0, media_kind_rate: kindHits / Math.max(kindRows, 1), isolation_403_rate: isoN ? (isoN - (letIn ? 1 : 0)) / isoN : 0};
    var behind = {request_success_rate: N, answerable_rate: n, citation_rate: answered, citation_valid_rate: citRows, must_contain_rate: answered,
                  correct_rate: n, refusal_rate: u, media_kind_rate: kindRows, isolation_403_rate: isoN};
    var failed = Object.keys(S).filter(function(k){ return behind[k] > 0 && S[k] < B.thr[k]; }).sort();
    var failures = failed.map(function(k){ return k + ': ' + pct(S[k], 0) + ' < ' + pct(B.thr[k], 0); }), exit, verdict;
    if (leaks.length) { exit = 2; verdict = 'A must_not_contain row fired. That should be near-impossible given the retrieval filter, which makes it MORE serious, not less.'; }
    else {
      if (stale.length) failures.push('stale: a retired version was cited');
      if (req.length) failures.push('required: ' + req.length + ' mandatory row(s) did not pass');
      exit = failures.length ? 1 : 0; verdict = failures.length ? 'Blocked: ' + failures.join('; ') : 'All thresholds met.';
    }
    return {S: S, behind: behind, failed: failed, req: req, leaks: leaks, stale: stale, exit: exit, verdict: verdict}; }"""

test_js = ("'use strict';\n" + CALC_JS + "\nvar B = " + json.dumps(BOARD) + ";\n"
           "console.log(JSON.stringify(B.presets.map(function(p){ var c = compute(B, p[1], p[2]);"
           " return {scores: c.S, failed: c.failed, req: c.req, leaks: c.leaks, stale: c.stale, exit: c.exit, verdict: c.verdict}; })));\n")
tjs = Path(tempfile.mkdtemp(prefix="lesson72-js-")) / "board.js"
tjs.write_text(test_js, encoding="utf-8")
node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(tjs.parent, ignore_errors=True)
assert node.returncode == 0, node.stderr[-800:]
for (label, _, _), kit, js in zip(PRESETS, KIT_RESULTS, json.loads(node.stdout)):
    for key in ("failed", "req", "leaks", "stale", "exit", "verdict"):
        assert kit[key] == js[key], (label, key, kit[key], js[key])
    assert all(kit["scores"][k] == js["scores"][k] for k in rv.THRESHOLDS), (label, kit["scores"], js["scores"])

UI_JS = r"""var root = document.getElementById('board'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var grid = $('tb-grid'), pick = $('tb-pick'), outs = $('tb-outsider'), score = $('tb-score'), verdict = $('tb-verdict'), presets = $('tb-presets');
  var outc = {}, chosen = null, SHAPES = ['lookup', 'join', 'refusal', 'isolation', 'version'];
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function options(r){
    var o = r.a ? [['ok', 'right: the figure and a valid citation'], ['refused', 'refused'], ['nofig', 'answered without the figure'],
                   ['badcite', "cited another tenant's chunk"], ['nocite', 'answered with no citation']]
                : [['ok', 'right: refused'], ['answered', 'answered anyway']];
    if (r.a && r.k) o.push(['kind', 'cited no ' + r.k]);
    if (r.m && r.s !== 'version') o.push(['leak', r.a ? "the right figure, and the other tenant's" : "answered with the other tenant's figure"]);
    if (r.s === 'version') o.push(['stale', "the retired version's figure"]);
    return o.concat([['err', 'HTTP 500, twice'], ['bad', 'a 200 with an empty body'], ['denied', 'HTTP 403 for the member']]); }
  function render(){
    var c = compute(B, outc, +outs.value);
    grid.innerHTML = SHAPES.map(function(s){ return '<p class="tb-shape">' + s + '</p><p class="tb-chips">' + B.rows.filter(function(r){ return r.s === s; }).map(function(r){
      var o = outc[r.i] || 'ok'; return '<button type="button" data-i="' + r.i + '" class="' + (o === 'ok' ? '' : 'no') + (r.r ? ' req' : '') + (chosen === r.i ? ' sel' : '') + '">' + r.i + '</button>'; }).join('') + '</p>'; }).join('');
    var r = chosen && B.rows.filter(function(x){ return x.i === chosen; })[0];
    pick.innerHTML = r ? '<b class="h">' + r.i + ' &middot; ' + r.s + ' &middot; ' + r.t + (r.r ? ' &middot; required' : '') + '</b>' + esc(r.q)
      + '<label class="tb-l">What the API replies<select id="tb-o">' + options(r).map(function(p){ return '<option value="' + p[0] + '"' + ((outc[r.i] || 'ok') === p[0] ? ' selected' : '') + '>' + esc(p[1]) + '</option>'; }).join('') + '</select></label>'
      : '<b class="h">Pick a row</b>Tap a row to choose what the API replies to it. A dark underline marks a required row.';
    if (r) $('tb-o').addEventListener('change', function(e){ if (e.target.value === 'ok') delete outc[r.i]; else outc[r.i] = e.target.value; render(); });
    score.innerHTML = '<p class="tb-row"><span>threshold</span><span>score</span><span>needs</span><span></span></p>' + Object.keys(c.S).map(function(k){
      var judged = c.behind[k] > 0, bad = c.failed.indexOf(k) >= 0;
      return '<p class="tb-row"><span>' + k + '<small>' + c.behind[k] + ' rows behind it</small></span><span>' + pct(c.S[k], 1) + '</span><span>' + pct(B.thr[k], 0) + '</span><span class="'
        + (bad ? 'tb-fail">FAIL' : judged ? 'tb-pass">pass' : 'tb-off">--') + '</span></p>'; }).join('');
    verdict.innerHTML = '<span class="tb-exit e' + c.exit + '">exit ' + c.exit + '</span> ' + esc(c.verdict)
      + (c.leaks.length ? '<br>leaked: ' + c.leaks.join(', ') : '') + (c.stale.length ? '<br>stale: ' + c.stale.join(', ') : '')
      + (c.req.length ? '<br>required rows that did not pass: ' + c.req.join(', ') : ''); }
  presets.innerHTML = B.presets.map(function(p, j){ return '<button type="button" data-j="' + j + '">' + esc(p[0]) + '</button>'; }).join('');
  presets.addEventListener('click', function(e){ var b = e.target.closest('button'); if (!b) return; var p = B.presets[+b.getAttribute('data-j')];
    outc = JSON.parse(JSON.stringify(p[1])); outs.value = String(p[2]); chosen = Object.keys(outc)[0] || null; render(); });
  grid.addEventListener('click', function(e){ var b = e.target.closest('button'); if (!b) return; chosen = b.getAttribute('data-i'); render(); });
  outs.addEventListener('change', render);
  render();"""

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\nvar B = " + json.dumps(BOARD, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n"
      + squeeze(CALC_JS) + "\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert JS.count("<div") == JS.count("</div>") and "<tr" not in JS

# ------------------------------------------------------------------ numbers for the prose
cost_txt = (KIT / "services" / "rag-api" / "cost.py").read_text(encoding="utf-8")
RATE_IN, RATE_OUT = (float(x) for x in re.search(r'"gemini-3.6-flash": \(([\d.]+), ([\d.]+)\)', cost_txt).groups())
pins = {}
for req_file in ("services/rag-api/requirements.txt", "services/ingest/requirements.txt"):
    for line in (KIT / req_file).read_text(encoding="utf-8").splitlines():
        if line.startswith("google-cloud-aiplatform=="):
            pins[req_file] = line.split("==")[1].strip()
assert set(pins.values()) == {"1.153.1"}, pins
STATS = {
    "N_ROWS": str(len(golden)), "N_ANS": str(N_ANS), "N_UNANS": str(len(golden) - N_ANS), "N_REQ": str(len(required)),
    "N_ISO": str(len(ISO)), "N_MEDIA": str(len(MEDIA)), "N_THRESHOLDS": str(len(rv.THRESHOLDS)), "N_PRESETS": str(len(PRESETS)),
    "N_JUDGE_REQ": str(2 * len(golden)), "AIP_PIN": "1.153.1", "TEMPLATE_HASH": TEMPLATE_HASH, "SECOND": SECOND,
    "RATE_IN": f"{RATE_IN:.2f}", "RATE_OUT": f"{RATE_OUT:.2f}",
    "CORRECT_MIN": f"{rv.THRESHOLDS['correct_rate']:.2f}", "MC_MIN": f"{rv.THRESHOLDS['must_contain_rate']:.2f}",
    "ANS_MIN": f"{rv.THRESHOLDS['answerable_rate']:.2f}", "REF_MIN": f"{rv.THRESHOLDS['refusal_rate']:.2f}",
    "N_ACME": str(per_tenant["acme"]), "N_ZETA": str(per_tenant["zeta"]), "N_GLOBEX": str(per_tenant["globex"]),
    "CI_SHA": runs[0]["head_sha"][:7],
}


if os.environ.get("CELLS_ONLY"):                  # CELLS_ONLY=1 python build.py: the expected blocks, nothing written
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {len(golden)} rows ({N_ANS} answerable), {len(required)} required, {len(rv.THRESHOLDS)} thresholds | stub run exit {live_rc} with 2 misses"
      f" | {len(PRESETS)} board presets equal to run_eval.live() in node | judge self-test ok | CI {runs[0]['head_sha'][:7]} {runs[0]['conclusion']}")
