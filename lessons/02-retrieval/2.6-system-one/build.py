"""Build lesson 2.6 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Decide answer-or-refuse with a System One model (Jev). evals/decide.py scores three arms' answer-or-refuse decisions
on one pool per golden row: the kit's evidence rule (shared/documind_tools.EVIDENCE_FLOOR), the generator's own
answerable from /v1/query, and TypeSafe AI's Jev through shared/system_one.py behind JEV_MODE, off by default. Jev is
not on the request path, its adapter is PR 2.6-C and no recording of it exists, so every Jev figure on the page reads
"Jev not available" until the author's run records one; nothing here is ever a Jev output written by hand.

Offline, at build time, on the kit with no network: decide.py --local, --local --floor 0.7 and JEV_MODE=recorded
--local --tenant zeta (the rule on the kit's corpus, Rs 0); the golden row rf-01; the explain() and ask_jev() cells.
In-process, with decide.py's own LocalLane: every golden row's evidence share for the floor widget, whose counts at
0.50 and 0.70 are asserted equal to the two runs', and the generator's prompt size on the Rs 0 lane's pools, which
prices the runs at shared/prices.py's list prices. Live: pb.recorded() reads the author's runs (RUN_LIST.md):
ui_refusal.txt, decide_learner.txt, decide_live.txt and decide_run.json, the saved run every Level 5 figure for the
generator and Jev is computed from with decide.py's own scoring.

    python pagekit/build.py 2.6          (the 3.12 venv; about three minutes: the Rs 0 lane ranks a tenant's whole corpus per row)
"""
import ast
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "2.6"
title = ("<title>Lesson 2.6 Decide answer-or-refuse with a System One model (Jev) - the evidence rule, the generator "
         "and Jev on one pool, scored on the golden set | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the answer path: the slot no code fills yet */
.fs-main.slot{border:2px dashed #c2410c;background:#fff7ed;}
.fs-main.slot .fs-n{background:#c2410c;}
/* the floor widget: a slider, the matrix, the rates, the rows the floor can move, the operating plot */
.dc-top{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:0 0 10px;}
.dc-top label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:2px;flex:1 1 220px;min-width:0;}
.dc-top input[type=range]{width:100%;min-height:44px;accent-color:var(--teal);}
.dc-fv{font-family:var(--mono);font-weight:700;color:var(--teal-dark);}
.dc-pre{font:inherit;font-size:var(--small-size);padding:6px 12px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);cursor:pointer;min-height:max(40px,var(--touch));}
.dc-pre:active{transform:scale(.97);}
.dc-sum{font-size:var(--small-size);color:var(--slate);margin:0 0 10px;}
.dc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:12px;align-items:start;}
.dc-cm{display:grid;grid-template-columns:minmax(0,1.3fr) repeat(2,minmax(0,1fr));gap:4px;font-size:var(--small-size);}
.dc-cm div{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:6px 8px;line-height:1.35;}
.dc-cm .h{background:transparent;border:0;font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;color:var(--navy);text-transform:uppercase;letter-spacing:.8px;}
.dc-cm b{display:block;font-family:var(--mono);font-size:20px;color:var(--navy);}
.dc-cm .ok{border-left:4px solid var(--teal);}
.dc-cm .bad{border-left:4px solid #c2410c;}
.dc-rates{font-family:var(--mono);font-size:var(--kicker-size);line-height:1.7;color:var(--navy);margin:8px 0 0;overflow-wrap:anywhere;}
.dc-rates span{color:var(--slate);}
.dc-plot{display:block;width:100%;max-width:460px;height:auto;margin:0 auto;}
.dc-plot text{font:11px var(--mono);fill:#475569;}
.dc-plot .t{font-weight:700;fill:var(--navy);}
.dc-key{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:var(--small-size);margin:6px 0 0;}
.dc-key span::before{content:'';display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:0;background:var(--k);}
.dc-key span.ring::before{background:#fff;box-shadow:inset 0 0 0 2px var(--k);}
.dc-key span.line::before{height:3px;border-radius:0;vertical-align:3px;}
.dc-ladder{list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column;gap:4px;}
.dc-bar{display:grid;grid-template-columns:minmax(0,10.5em) minmax(60px,1fr) 3.3em 3.9em;gap:6px;align-items:center;font-size:12.5px;line-height:1.3;}
.dc-bar .dc-id{font-family:var(--mono);color:var(--navy);overflow-wrap:anywhere;}
.dc-bar .dc-id em{display:block;font-family:var(--font);font-style:normal;color:var(--slate);font-size:11.5px;}
.dc-track{position:relative;height:14px;background:var(--teal-light);border-radius:4px;}
.dc-fill{position:absolute;left:0;top:0;bottom:0;border-radius:4px;background:var(--teal);}
.dc-bar.bad .dc-fill{background:#c2410c;}
.dc-fl{position:absolute;top:-3px;bottom:-3px;width:2px;margin-left:-1px;background:var(--navy);}
.dc-sh,.dc-v{font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);}
.dc-bar.bad .dc-v{color:#9a3412;font-weight:700;}
.dc-all{font-size:var(--small-size);background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:8px 0 0;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim kit excerpts
API, GEN, DT, SO, DEC, MK, RUNEV = ("services/rag-api/main.py", "services/rag-api/generator.py", "shared/documind_tools.py",
                                    "shared/system_one.py", "evals/decide.py", "mk/retrieval.mk", "evals/run_eval.py")
EXCERPTS = {
    "handler": ("services/rag-api/main.py - query(): the empty pool refused by code, else rerank, then generate",
                block(API, "    if hit:", n=12)),
    "empty_pool": ("services/rag-api/main.py - empty_pool_answer(): the first refusal, no model, Rs 0",
                   block(API, "def empty_pool_answer(")),
    "system_rule": ("services/rag-api/generator.py - SYSTEM: rule 3 is the model's refusal",
                    block(GEN, 'SYSTEM = """You are DocuMind', end="# The ledger's second half")),
    "lexical": ("shared/documind_tools.py - EVIDENCE_FLOOR, _lexical_rank() and the local lane's gate",
                block(DT, "EVIDENCE_FLOOR = 0.5", n=2) + "\n...\n" + block(DT, "def _lexical_rank(", end="def _snippet(")
                + "\n...\n" + block(DT, "    ranked, idf = _lexical_rank(query, rows)", end="    top = ranked[0][0]")),
    "passages_doc": ("services/rag-api/main.py - /v1/passages: the pool, and nothing after it",
                     block(API, '@app.post("/v1/passages")', n=8)),
    "modes": ("shared/system_one.py - the three modes, from the module's docstring",
              block(SO, "    JEV_MODE=off        the default", n=3)),
    "decide_fn": ("shared/system_one.py - decide(): the one entry point, which never raises",
                  block(SO, "def decide(question: str")),
    "live_fn": ("shared/system_one.py - _live(): the tenant's policy first, then the masked payload, then the transport",
                block(SO, "def _live(", end="# ---------------------------------------------------------------- the one entry point")),
    "seam": ("shared/system_one.py - the adapter seam PR 2.6-C fills: headers, request, parse",
             block(SO, "def _headers()", end="def _price(")),
    "payload_fn": ("shared/system_one.py - _payload() and _policy(): what may leave, and for whom",
                   block(SO, "def _payload(", end="# ---------------------------------------------------------------- the data-region policy")
                   + "\n...\n" + block(SO, "def _policy(", end="# ---------------------------------------------------------------- the recorded file")),
    "rule_arm": ("evals/decide.py - evidence_share() and rule_arm(): the rule, on any pool",
                 block(DEC, "def evidence_share(", end="class CorpusStore:")),
    "decide_row": ("evals/decide.py - decide_row(): every arm on one row's pool; an empty pool asks no model",
                   block(DEC, "def decide_row(", end="def _not_run(")),
    "generator_live": ("evals/decide.py - list_usd() and generator_live(): /v1/query's own answerable, and its price",
                       block(DEC, "def list_usd(", end="def generator_recorded(")),
    "mk_decide": ("mk/retrieval.mk - JEV_MODE and make decide", block(MK, "# Jev (shared/system_one.py), TypeSafe", n=14)),
    "summarise": ("evals/decide.py - summarise(): the confusion matrix, the three rates, errors and skips apart",
                  block(DEC, "def summarise(", end="def kappa(")),
    "calibration": ("evals/decide.py - calibration() and rupees()",
                    block(DEC, "def calibration(", end="def by_confidence(") + "\n...\n"
                    + block(DEC, "def rupees(", end="# --------------------------------------------------------------------- the report")),
    "threshold": ("evals/run_eval.py - THRESHOLDS: the gate's refusal rate", block(RUNEV, '    "refusal_rate": 0.90,', n=1)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["handler"].startswith("    if hit:\n        ans = hit") and E["handler"].rstrip().endswith("model=model, backend=backend)"), E["handler"][-120:]
assert "elif not chunks:" in E["handler"] and "rerank(req.query" in E["handler"]
assert E["empty_pool"].rstrip().endswith('backend="none", cost_usd=0.0, tokens_in=0, tokens_out=0, latency_ms=0, cache_hit="none")')
assert "3. If the context does not contain the answer, set answerable=false and say so." in E["system_rule"]
assert E["lexical"].rstrip().endswith("ranked = []") and "EVIDENCE_MODE = \"set\"" in E["lexical"]
assert E["passages_doc"].rstrip().endswith('is passages [] and answerable False."""')
assert E["decide_fn"].rstrip().endswith('"request_id": None}') and "AdapterNotConfigured(NOT_CONFIGURED)" in E["seam"]
assert E["live_fn"].rstrip().endswith('request_id=got.get("request_id"), reason=f"live{masked}")')
assert E["rule_arm"].rstrip().endswith("ms=round((time.perf_counter() - t0) * 1000, 3), reason=why)")
assert E["generator_live"].rstrip().endswith("return res") and "cost = list_usd(" in E["generator_live"]
assert E["mk_decide"].rstrip().endswith("--region $(REGION) $(DECIDE_ARGS)") and "JEV_MODE ?= off" in E["mk_decide"]
assert E["summarise"].rstrip().endswith("return s") and E["calibration"].rstrip().endswith("len(costs) - len(priced)")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit, imported: decide.py, its scoring and its lane
sys.path[:0] = [str(KIT), str(KIT / "evals"), str(KIT / "services" / "rag-api")]
spec = importlib.util.spec_from_file_location("decide_lesson_26", KIT / "evals" / "decide.py")
decide = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decide)
from context_budget import TokenBudget, estimate_tokens, pack_chunks  # noqa: E402
from route_eval import rate, wilson  # noqa: E402
from run_eval import THRESHOLDS, pct  # noqa: E402
from shared import local_corpus, prices, system_one  # noqa: E402

prices.PROFILE = "gcp"       # list prices, whatever DOCUMIND_PROFILE the build's own shell carries: the page prices a lane
dt = decide._tools()
GOLDEN = decide.load_golden()
N_ROWS, N_ANS = len(GOLDEN), sum(1 for r in GOLDEN if r["answerable"])
N_UN = N_ROWS - N_ANS
SHAPES = decide.SHAPES
BY_SHAPE = {s: [r for r in GOLDEN if r["shape"] == s] for s in SHAPES}
N_REF_UN = sum(1 for r in BY_SHAPE["refusal"] if not r["answerable"])
N_ISO_UN = sum(1 for r in BY_SHAPE["isolation"] if not r["answerable"])
assert (N_ROWS, N_ANS, N_UN) == (65, 47, 18) and N_REF_UN == len(BY_SHAPE["refusal"]) == 8 and N_ISO_UN == 10, (N_ROWS, N_ANS)
assert N_REF_UN + N_ISO_UN == N_UN                     # decide.py's docstring: the 8 refusal rows and 10 isolation rows

FLOOR = dt.EVIDENCE_FLOOR
GATE = THRESHOLDS["refusal_rate"]
TOPK = decide.parse_args([]).top_k
run_eval_src = (KIT / RUNEV).read_text(encoding="utf-8")
GEN_TOPK = int(re.search(r'"top_k": (\d+)\}\)\.encode\(\)', run_eval_src).group(1))
assert (FLOOR, GATE, TOPK, GEN_TOPK, dt.EVIDENCE_MODE) == (0.5, 0.90, 5, 6, "set")
cfg = (KIT / "services" / "rag-api" / "config.py").read_text(encoding="utf-8")
GEN_MODEL = re.search(r'generator_model: str = "([^"]+)"', cfg).group(1)
MAX_CTX = int(re.search(r"max_context_tokens: int = (\d+)", cfg).group(1))
MAX_ANS = int(re.search(r"max_answer_tokens: int = (\d+)", cfg).group(1))
RATE_IN, RATE_OUT = prices.PRICES[GEN_MODEL]
USD_INR = prices.USD_INR
JEV_USD = system_one.USD_PER_1B_INPUT
assert JEV_USD == 42.0 and system_one.USD_PER_1B_OUTPUT is None and system_one.MODES == ("off", "recorded", "live")
lane_src = (KIT / "commands" / "lane.py").read_text(encoding="utf-8")
POLICY = dict(re.findall(r'\("(\w+)", "(any|in)"\)', re.search(r"    policies = \[(.*?)\]\n", lane_src).group(1)))
assert POLICY == {"acme": "any", "zeta": "any", "globex": "in"}, POLICY
N_ANY = sum(1 for r in GOLDEN if POLICY[r["tenant"]] == "any")
ANY_T = sorted(t for t, p in POLICY.items() if p == "any")
N_ZETA = sum(1 for r in GOLDEN if r["tenant"] == "zeta")
ZETA_ANS = sum(1 for r in GOLDEN if r["tenant"] == "zeta" and r["answerable"])
assert N_ANY == 57 and N_ZETA == 10 and ZETA_ANS == 5, (N_ANY, N_ZETA, ZETA_ANS)
FIRST10_ANS = sum(1 for r in GOLDEN[:10] if r["answerable"])        # --limit 10 would be lk-01 to lk-10: all answerable
assert FIRST10_ANS == 10 and all(r["shape"] == "lookup" for r in GOLDEN[:10])   # step 6: "all answerable lookups"
W18 = wilson(N_UN, N_UN)[0]
# the prompt generate() builds: the same two f-strings, so the estimate below packs and counts what the generator would
gen_src = (KIT / GEN).read_text(encoding="utf-8")
assert 'fixed = f"{SYSTEM}{DATED_RULE}\\n\\nContext:\\n\\n\\nQuestion: {query}"' in gen_src
assert 'prompt = f"{SYSTEM}{_dated_rule(packed)}\\n\\nContext:\\n{context}\\n\\nQuestion: {query}"' in gen_src
K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(gen_src).body
     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}

# ------------------------------------------------------------------ the offline runs: the kit's own output, no network
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONIOENCODING": "utf-8",
         "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}        # no gcloud on PATH, no JEV_* or DOCUMIND_* in the environment

GOLDEN_PY = ("import json; print(json.dumps(next(r for r in map(json.loads, open('evals/golden.jsonl', encoding='utf-8')) "
             "if r['id'] == 'rf-01'), indent=1))")

UI_PY = r'''import json, os, subprocess, sys, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from shared.prices import USD_INR, usd
PROJECT, API = os.environ["PROJECT"], os.environ["API"]
Q = "What is ACME's sabbatical policy?"                              # golden row rf-01: answerable false
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()


def post(route, body):
    """POST one JSON body to the API as documind-ui-sa and return the decoded reply."""
    req = urllib.request.Request(f"{API}{route}", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=180))


a = post("/v1/query", {"query": Q, "tenant_id": "acme", "stream": False, "top_k": 5})
s = a["stages"]
print(f"/v1/query     answerable {a['answerable']} | confidence {a['confidence']} | citations {len(a['citations'])} | backend {a['backend']} | model {a['model']}")
print(f"              pool {s['pool']} | retrieve_ms {s['retrieve_ms']} | rerank_ms {s['rerank_ms']} | generate_ms {s['generate_ms']}")
print(f"              tokens {a['tokens_in']} in + {a['tokens_out']} out | cost_usd on the answer: {a['cost_usd']} | "
      f"priced by shared/prices.py: Rs {usd(a['model'], a['tokens_in'], a['tokens_out']) * USD_INR:.4f}")
print(f"              answer: {a['answer'][:100]}")
p = post("/v1/passages", {"query": Q, "tenant_id": "acme", "top_k": 5})
u = p["usage"]
print(f"/v1/passages  passages {len(p['passages'])} | answerable {p['answerable']} | model {u['model']} | cost_usd {u['cost_usd']} | "
      f"retrieve_ms {u['stages']['retrieve_ms']} | rerank_ms {u['stages']['rerank_ms']}")
for x in p["passages"]:
    print(f"   [{x['n']}] {x['source_uri'].split('/')[-1][:30]:30} {x['text'][:56]!r}")'''

EXPLAIN_PY = r'''import json, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from shared import documind_tools as dt, local_corpus

GOLDEN = {r["id"]: r for r in (json.loads(line) for line in open("evals/golden.jsonl", encoding="utf-8") if line.strip())}


def explain(rid, top_k=5):
    """The evidence rule on one golden row, Rs 0: each content word's idf over the tenant's chunks, whether the
    top-k pool holds it, and the share against EVIDENCE_FLOOR, as the local lane's gate computes it."""
    row = GOLDEN[rid]
    ranked, idf = dt._lexical_rank(row["question"], [(c["text"], {}) for c in local_corpus.chunks_for(row["tenant"])])
    covered = {w for _, hit, _, _ in ranked[:top_k] for w in hit}
    share = sum(idf[w] for w in covered) / sum(idf.values()) if idf else 0.0
    print(f"{rid} ({row['tenant']}, {row['shape']}, answerable {row['answerable']}): {row['question']}")
    for w, v in sorted(idf.items(), key=lambda kv: -kv[1]):
        print(f"   {w:<14} idf {v:5.2f}   {'in the pool' if w in covered else 'not in the pool'}")
    common = [w for w in dt._words(row["question"]) if w not in idf]
    if common:
        print(f"   {', '.join(common)}: in more than half of the tenant's chunks, so not evidence")
    verdict = "answer" if ranked and share >= dt.EVIDENCE_FLOOR else "refuse"
    print(f"   share {share:.2f} against EVIDENCE_FLOOR {dt.EVIDENCE_FLOOR}: the rule says {verdict}")


for rid in ("rf-01", "rf-02", "lk-01"):
    explain(rid)'''

SWITCH_PY = r'''import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from shared import local_corpus, system_one

ROSTER = {"acme": "any", "zeta": "any", "globex": "in"}          # the data_region make roster writes (commands/lane.py)
invoice = next(c for c in local_corpus.chunks_for("acme") if "AAAPZ1234C" in c["text"])
POOL = [{"n": 1, "chunk_id": invoice["chunk_id"], "text": invoice["text"]}]
Q = "What is the total payable on invoice INV-2026-0412?"


def ask_jev(mode, tenant):
    """One system_one.decide() in a JEV_MODE, with make roster's data_region standing in for the Firestore read."""
    res = system_one.decide(Q, POOL, "lk-10", tenant, jev_mode=mode, policy_for=ROSTER.get)
    print(f"{mode:<9}{tenant:<7} {res['verdict']:<8} source {res['source']:<9} {res['reason']}"
          + (f" | error: {res['error']}" if res["error"] else ""))


for mode, tenant in (("off", "acme"), ("recorded", "acme"), ("live", "globex"), ("live", "acme")):
    ask_jev(mode, tenant)
payload, kinds = system_one._payload(Q, POOL)
print(f"\nwhat live mode would send: {sorted(payload)} | masked: {', '.join(kinds) or 'nothing'}")
for line in payload["passages"][0].splitlines():
    if line.startswith(("PAN", "GSTIN", "Contact", "Email")):
        print("   " + line)'''

CMD = {"local": ["evals/decide.py", "--local"], "floor": ["evals/decide.py", "--local", "--floor", "0.7"],
       "zeta_rec": ["evals/decide.py", "--local", "--tenant", "zeta"]}
tmp = tempfile.TemporaryDirectory(prefix="lesson26_")
procs = {}
for key, args in CMD.items():          # the three runs go on in the background while the shares are computed below
    env = {**QUIET, **({"JEV_MODE": "recorded"} if key == "zeta_rec" else {})}
    fo = open(os.path.join(tmp.name, key + ".out"), "w+", encoding="utf-8")
    fe = open(os.path.join(tmp.name, key + ".err"), "w+", encoding="utf-8")
    procs[key] = (subprocess.Popen([sys.executable] + args, cwd=str(KIT), stdout=fo, stderr=fe, env=env), fo, fe)


def cell(src: str, args=("-",)) -> str:
    """A page cell run here, on the kit, with no network: what it prints."""
    r = subprocess.run([sys.executable] + list(args), input=src if args == ("-",) else None, cwd=str(KIT),
                       capture_output=True, text=True, encoding="utf-8", env=QUIET)
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout.rstrip("\n")


OUT_GOLDEN = cell("", ("-c", GOLDEN_PY))
OUT_EXPLAIN = cell(EXPLAIN_PY)
OUT_SWITCH = cell(SWITCH_PY)
RF01 = next(r for r in GOLDEN if r["id"] == "rf-01")
assert json.loads(OUT_GOLDEN) == RF01 and '"answerable": false' in OUT_GOLDEN
assert OUT_SWITCH.count("\n") >= 5 and system_one.NOT_CONFIGURED in OUT_SWITCH and system_one.OFF_REASON in OUT_SWITCH, OUT_SWITCH
assert system_one.RECORDED_ABSENT in OUT_SWITCH and "tenant globex: data_region in" in OUT_SWITCH

# ------------------------------------------------------------------ every golden row's evidence share, with decide.py's LocalLane
true_rank, last = dt._lexical_rank, {}


def recorder(q, rows):
    """documind_tools._lexical_rank, kept: LocalLane calls it, the ranked list is read for the generator's top six."""
    last["ranked"], last["idf"] = got = true_rank(q, rows)
    return got


TENANTS = sorted({r["tenant"] for r in GOLDEN})
CHUNK = {c["chunk_id"]: c for t in TENANTS for c in local_corpus.chunks_for(t)}
lane0 = decide.LocalLane(TENANTS, 0.0)      # floor 0: the pool is never gated, so the share is read for every row
ROWS, TOK5, TOK6, JEV_TOK = [], {}, {}, {}


def prompt_tokens(question: str, chunks: list[dict]) -> int:
    """generate()'s prompt for this pool: _budget(), _pack() and the prompt line, counted by estimate_tokens (len // 4)."""
    budget = TokenBudget.fit(MAX_CTX, f"{K['SYSTEM']}{K['DATED_RULE']}\n\nContext:\n\n\nQuestion: {question}", estimate_tokens,
                             answer=MAX_ANS)
    context, packed, _ = pack_chunks(chunks, budget.chunks, estimate_tokens)
    dated = K["DATED_RULE"] if any(c.get("effective_from") for c in packed) else ""
    return estimate_tokens(f"{K['SYSTEM']}{dated}\n\nContext:\n{context}\n\nQuestion: {question}")


dt._lexical_rank = recorder
try:
    for r in GOLDEN:
        got, share = lane0.pool(r["question"], r["tenant"], TOPK)
        ranked = last["ranked"]
        ROWS.append({"id": r["id"], "shape": r["shape"], "tenant": r["tenant"], "ans": bool(r["answerable"]),
                     "share": round(share, 6), "pool": bool(got.get("passages"))})
        TOK5[r["id"]] = prompt_tokens(r["question"], [dict(CHUNK[x[3]["chunk_id"]]) for x in ranked[:TOPK]])
        TOK6[r["id"]] = prompt_tokens(r["question"], [dict(CHUNK[x[3]["chunk_id"]]) for x in ranked[:GEN_TOPK]])
        if POLICY[r["tenant"]] == "any":
            payload, _ = system_one._payload(r["question"], got.get("passages") or [])
            JEV_TOK[r["id"]] = estimate_tokens(payload["question"] + "".join(payload["passages"]))
finally:
    dt._lexical_rank = true_rank
assert len(ROWS) == N_ROWS and all(x["pool"] == (x["share"] > 0) for x in ROWS)
# a share within a millionth of a slider step would let the rounded share and the kit's full one fall either side of it
assert all(min(abs(x["share"] * 100 - k) for k in range(100)) > 1e-4 for x in ROWS if x["share"] < 1.0)

OUT = {}
for key, (p, fo, fe) in procs.items():
    assert p.wait(timeout=1800) == 0, key
    fo.seek(0)
    fe.seek(0)
    out, err = fo.read().rstrip("\n"), fe.read().rstrip("\n")
    fo.close()
    fe.close()
    assert all(line.startswith("  ... ") and line.endswith(" rows") for line in err.splitlines()), err[-400:]
    OUT[key] = (err + "\n" + out) if err else out          # the progress lines reach the terminal first, then the report
tmp.cleanup()


def mask_ms(text: str) -> str:
    """The rule's in-process latency is this machine's hundredths of a millisecond: written 0.0x, as the page writes a
    lane's own digits."""
    out, n = re.subn(r"(?m)^    rule \(in process\)\s+\S+\s+\S+\s+(\d+)$",
                     lambda m: f"    {'rule (in process)':<26}{'0.0x':>7}  {'0.0x':>8}  {m.group(1):>10}", text)
    assert n == 1, text[-600:]
    return out


for key in OUT:
    OUT[key] = mask_ms(OUT[key])


def confusion(floor: float) -> tuple[int, int, int, int]:
    """(answered, refused) of the answerable rows, then of the rest, at a floor: what the widget's script computes."""
    tp = sum(1 for x in ROWS if x["ans"] and x["pool"] and x["share"] >= floor)
    fp = sum(1 for x in ROWS if not x["ans"] and x["pool"] and x["share"] >= floor)
    return tp, N_ANS - tp, fp, N_UN - fp


def false_answers(floor: float) -> list[str]:
    return [x["id"] + ("*" if x["shape"] == "isolation" else "") for x in ROWS
            if not x["ans"] and x["pool"] and x["share"] >= floor]


def report_line(text: str, label: str) -> str:
    """One rate as the report printed it: 'k/n = p% [lo%, hi%]'."""
    return re.search(r"(?m)^\s+" + re.escape(label) + r"\s+(\d+/\d+ = [\d.]+% \[[\d.]+%, [\d.]+%\])", text).group(1)


for floor, key in ((FLOOR, "local"), (0.7, "floor")):
    tp, fn, fp, tn = confusion(floor)
    assert (f"confusion       answerable: {tp} answered, {fn} refused | unanswerable: {fp} answered, {tn} refused") in OUT[key], key
    shown = " ".join(re.search(r"false answers   \d+[^\n]*\n((?:\s+\S.*\n)+?)  generator", OUT[key]).group(1).split())
    assert shown == " ".join(false_answers(floor)), (key, shown)
    assert report_line(OUT[key], "refusal recall") == rate(tn, N_UN) and report_line(OUT[key], "answer rate") == rate(tp, N_ANS)
assert f"its gate the evidence rule at {FLOOR:.2f}" in OUT["local"] and "its gate the evidence rule at 0.70" in OUT["floor"]
assert system_one.OFF_REASON in OUT["local"] and system_one.RECORDED_ABSENT in OUT["zeta_rec"]
assert f"rows       {N_ZETA} golden rows: {ZETA_ANS} answerable, {N_ZETA - ZETA_ANS} not" in OUT["zeta_rec"]
BRIER_RULE = re.search(r"rule \(the evidence share, not a probability\): Brier ([\d.]+) over", OUT["local"]).group(1)

meets = lambda k, n: "yes" if n and k / n >= GATE else "no"       # noqa: E731 - run_eval compares the rate itself
L = {}
for floor, tag in ((FLOOR, "5"), (0.7, "7")):
    tp, fn, fp, tn = confusion(floor)
    L.update({f"L{tag}_AR": rate(tp, N_ANS), f"L{tag}_RR": rate(tn, N_UN), f"L{tag}_ACC": rate(tp + tn, N_ROWS),
              f"L{tag}_FA": str(fp), f"L{tag}_TN": str(tn), f"L{tag}_FN": str(fn), f"L{tag}_TP": str(tp),
              f"L{tag}_FA_IDS": ", ".join(false_answers(floor)), f"L{tag}_MEETS": meets(tn, N_UN)})
assert wilson(int(L["L5_TN"]), N_UN)[1] < GATE              # step 5: "under the gate's 0.90 with the whole interval"
ZETA_EMPTY = [x["id"] for x in ROWS if x["tenant"] == "zeta" and not (x["pool"] and x["share"] >= FLOOR)]
assert len(ZETA_EMPTY) == 1 and "(1 empty pools refused by code)" in OUT["zeta_rec"], ZETA_EMPTY   # step 5: "the one row"
L["ZETA_EMPTY"] = ZETA_EMPTY[0]
L7_LOST = [x for x in ROWS if x["ans"] and not (x["pool"] and x["share"] >= 0.7)]
assert 2 * sum(1 for x in L7_LOST if x["shape"] == "join") > len(L7_LOST)   # "most of them joins", step 5
L["L7_LOST_IDS"] = ", ".join(x["id"] for x in L7_LOST)
top_bin = re.search(r"(?m)^\s+0\.8-1\.0\s+(\d+)\s+[\d.]+\s+(\d+)/(\d+)$", OUT["local"])
L.update({"BIN_TOP_N": top_bin.group(1), "BIN_TOP_UN": str(int(top_bin.group(3)) - int(top_bin.group(2)))})
from shared import identifiers  # noqa: E402
assert not identifiers.is_gstin("27AAAPZ1234C1ZV") and "GSTIN: 27AAAPZ1234C1ZV" in OUT_SWITCH   # step 5: the invoice's GSTIN fails its check
assert "PAN: [PAN]" in OUT_SWITCH and "Contact" in OUT_SWITCH and "Email: accounts@" in OUT_SWITCH
# the rows no floor below 1 refuses, and the best the rule does on this lane
AT1 = [x for x in ROWS if x["share"] >= 1.0]
AT1_UN = [x["id"] + ("*" if x["shape"] == "isolation" else "") for x in AT1 if not x["ans"]]
BELOW = sorted((x for x in ROWS if x["share"] < 1.0), key=lambda x: x["share"])
CURVE = [(k / 100, *confusion(k / 100)) for k in range(100)]
BEST_TN = max(c[4] for c in CURVE)
BEST = next(c for c in CURVE if c[4] == BEST_TN)
assert BEST_TN == N_UN - len(AT1_UN) and BEST_TN < GATE * N_UN
SHARE = {x["id"]: x["share"] for x in ROWS}
assert f"rf-01 (acme, refusal, answerable False)" in OUT_EXPLAIN and f"share {SHARE['rf-01']:.2f} against" in OUT_EXPLAIN
assert f"share {SHARE['rf-02']:.2f} against" in OUT_EXPLAIN and f"share {SHARE['lk-01']:.2f} against" in OUT_EXPLAIN

# ------------------------------------------------------------------ what the runs cost: the kit's prompt sizes at list prices
rs = lambda tin, tout: prices.usd(GEN_MODEL, tin, tout) * USD_INR   # noqa: E731


def money(x: float) -> str:
    return f"{x:,.2f}"


ZETA_IDS = [r["id"] for r in GOLDEN if r["tenant"] == "zeta"]
COST = {
    "OUT_CAP_CALL": money(rs(0, MAX_ANS)),
    "RF01_IN": money(rs(TOK5["rf-01"], 0)), "RF01_TOK": f"{TOK5['rf-01']:,}",
    "UI_IN": money(2 * rs(TOK5["rf-01"], 0)), "UI_CAP": money(2 * rs(TOK5["rf-01"], MAX_ANS)),
    "ZETA_IN": money(sum(rs(TOK6[i], 0) for i in ZETA_IDS)), "ZETA_CAP": money(sum(rs(TOK6[i], MAX_ANS) for i in ZETA_IDS)),
    "RUN_IN": money(sum(rs(TOK6[r["id"]], 0) for r in GOLDEN)), "RUN_CAP": money(sum(rs(TOK6[r["id"]], MAX_ANS) for r in GOLDEN)),
    "TOK_MIN": f"{min(TOK6.values()):,}", "TOK_MAX": f"{max(TOK6.values()):,}",
    "JEV_TOK": f"{sum(JEV_TOK.values()):,}", "JEV_RS": money(system_one._price({"input": sum(JEV_TOK.values()), "output": 0}) * USD_INR),
}
assert len(JEV_TOK) == N_ANY

# ------------------------------------------------------------------ the author's runs: what a live lane printed, and the saved run
REC = {k: pb.recorded(LESSON, f"{k}.txt") for k in ("ui_refusal", "decide_learner", "decide_live")}
RUN_RAW = pb.recorded(LESSON, "decide_run.json")
AWAIT_RUN = "[awaiting the author's run: data/decide_run.json]"
RUN = None if RUN_RAW == AWAIT_RUN else json.loads(RUN_RAW)
JEV_NA = "Jev not available"
REC_WHO = "the author's lane"


def decided(res) -> bool:
    return decide.decided(res)


def own_rs(arm_res: dict) -> float | None:
    """One decision in rupees at the price it carries: the gateway's, an empty pool's 0, Jev's page rate (system_one
    priced it, or left it None when TypeSafe's page has no price for what was billed). Never a guess."""
    return float(arm_res["cost_usd"]) * USD_INR if isinstance(arm_res.get("cost_usd"), (int, float)) else None


def gen_rs(arm_res: dict) -> float | None:
    """One generator decision in rupees: its cost_usd when /v1/query carried one, else, for a Gemini answer, whose
    cost_usd /v1/query leaves null, its tokens at shared/prices.py's list price, as cost.py prices the usage row."""
    got = own_rs(arm_res)
    if got is not None:
        return got
    t = arm_res.get("tokens") or {}
    if isinstance(t.get("input"), int) and isinstance(t.get("output"), int):
        return prices.usd(arm_res.get("model") or GEN_MODEL, t["input"], t["output"]) * USD_INR
    return None


R5 = {}                                      # the Level 5 figures; the awaiting stand-in until the saved run is recorded
if RUN is not None:
    assert RUN.get("kind") == "decide-run" and RUN.get("pool") in ("lane", "file"), "data/decide_run.json is not a lane's saved run"
    records = RUN["rows"]
    assert len(records) == N_ROWS and [r["id"] for r in records] == [g["id"] for g in GOLDEN], "the saved run is not all 65 rows"
    S = {arm: decide.summarise(records, arm) for arm in decide.ARMS}
    assert S["generator"]["available"], "the saved run holds no generator decision"
    for arm in ("rule", "generator"):        # the saved run and the recorded report are one run
        assert f"answer rate     {rate(*S[arm]['answer_rate'])}" in REC["decide_live"], arm
        assert f"refusal recall  {rate(*S[arm]['refusal_recall'])}" in REC["decide_live"], arm
    JEV_ON = S["jev"]["available"]
    if JEV_ON:
        assert f"refusal recall  {rate(*S['jev']['refusal_recall'])}" in REC["decide_live"]
    gen_live = [r for r in records if decided(r["arms"]["generator"]) and r["arms"]["generator"].get("source") != "code"]
    GEN_EACH = [gen_rs(r["arms"]["generator"]) for r in gen_live]
    assert gen_live and all(x is not None for x in GEN_EACH), "a generator decision with neither cost_usd nor tokens"
    GEN_TOTAL = sum(GEN_EACH)

    def first(arm: str) -> dict:
        """Ask `arm` before the generator and skip the generator on its refusals: what that saves and what it loses."""
        refused = [r for r in records if decided(r["arms"].get(arm)) and r["arms"][arm]["verdict"] == "refuse"
                   and r["arms"][arm].get("source") != "code" and decided(r["arms"]["generator"])
                   and r["arms"]["generator"].get("source") != "code"]
        saved = sum(gen_rs(r["arms"]["generator"]) for r in refused)
        lost = [r["id"] for r in refused if r["answerable"] and r["arms"]["generator"]["verdict"] == "answer"]
        caught = [r["id"] + ("*" if r["shape"] == "isolation" else "") for r in refused
                  if not r["answerable"] and r["arms"]["generator"]["verdict"] == "answer"]
        own = [own_rs(r["arms"][arm]) for r in records if decided(r["arms"].get(arm)) and r["arms"][arm].get("source") != "code"]
        return {"n": len(refused), "saved": saved, "lost": lost, "caught": caught,
                "own": sum(x for x in own if x is not None), "unpriced": sum(1 for x in own if x is None)}

    def ms(arm: str) -> str:
        v = decide.latency(records, arm)
        return f"{decide._ms(pct(v, 0.5))} / {decide._ms(pct(v, 0.95))} ms over {len(v)}" if v else "-"

    def fa(arm: str) -> str:
        x = S[arm]["false_answers"]
        return f"{len(x)}" + (": " + ", ".join(x) if x else "")

    def counted(n: int, one: str, many: str) -> str:
        return f"no {many}" if n == 0 else f"1 {one}" if n == 1 else f"{n} {many}"

    def saving(who: str, f: dict, paid: bool) -> str:
        """One line of 'refusing first': the generator calls skipped and their rupees, what the decider was paid, the
        answers lost, and the generator's false answers stopped, by id."""
        gen_fp = S["generator"]["fp"]
        stopped = ("the generator gave no false answer to stop" if not gen_fp else
                   f"of the generator's {gen_fp} false answers it would have stopped "
                   + (f"{len(f['caught'])} ({', '.join(f['caught'])})" if f["caught"] else "none"))
        return (f"Refusing first with {who} would have skipped {counted(f['n'], 'generator call', 'generator calls')}, saving "
                f"Rs {money(f['saved'])} of the generator's Rs {money(GEN_TOTAL)}"
                + ((f", for Rs {money(f['own'])} paid to TypeSafe"
                    + (f" and {counted(f['unpriced'], 'decision', 'decisions')} it could not price" if f["unpriced"] else ""))
                   if paid else "")
                + f", and lost {counted(len(f['lost']), 'answer', 'answers')}" + (f" ({', '.join(f['lost'])})" if f["lost"] else "")
                + f"; {stopped}.")

    conf = decide.by_confidence(records)
    cal_rule = decide.calibration(records, "rule")
    F_RULE = first("rule")
    R5.update({
        "R_RULE_RR": rate(*S["rule"]["refusal_recall"]), "R_RULE_AR": rate(*S["rule"]["answer_rate"]),
        "R_GEN_RR": rate(*S["generator"]["refusal_recall"]), "R_GEN_AR": rate(*S["generator"]["answer_rate"]),
        "R_RULE_MEETS": meets(*S["rule"]["refusal_recall"]), "R_GEN_MEETS": meets(*S["generator"]["refusal_recall"]),
        "R_RULE_FA": fa("rule"), "R_GEN_FA": fa("generator"),
        "R_RULE_CAL": f"Brier {cal_rule['brier']:.3f} over {cal_rule['n']} rows (the share, not a probability)" if cal_rule else "no scores",
        "R_GEN_CAL": "right decisions by its confidence: " + "; ".join(f"{lv} {rate(*conf[lv])}" for lv in decide.LEVELS if conf[lv][1]),
        "R_GEN_MS": ms("generator"),
        "R_GEN_RS": f"Rs {GEN_TOTAL / len(GEN_EACH):.4f} a decision, Rs {money(GEN_TOTAL)} for the {len(GEN_EACH)} it made",
        "R_SAVE_RULE": saving(f"the rule at {RUN['floor']:.2f}", F_RULE, paid=False),
    })
    if JEV_ON:
        F_JEV = first("jev")
        cal_jev = decide.calibration(records, "jev")
        per, n_priced, n_unpriced = decide.rupees(records, "jev")
        R5.update({
            "R_JEV_RR": rate(*S["jev"]["refusal_recall"]), "R_JEV_AR": rate(*S["jev"]["answer_rate"]),
            "R_JEV_MEETS": meets(*S["jev"]["refusal_recall"]),
            "R_JEV_FA": fa("jev"),
            "R_JEV_CAL": f"Brier {cal_jev['brier']:.3f} over {cal_jev['n']} rows (its calibrated probability)" if cal_jev else "no scores",
            "R_JEV_MS": ms("jev"),
            "R_JEV_RS": (f"Rs {per:.6f} a decision over {n_priced}" if per is not None else "unpriced")
                        + (f" ({n_unpriced} unpriced: TypeSafe documents no output price)" if n_unpriced else ""),
            "R_SAVE_JEV": saving("Jev", F_JEV, paid=True),
        })
    else:
        R5.update({k: JEV_NA for k in ("R_JEV_RR", "R_JEV_AR", "R_JEV_FA", "R_JEV_CAL", "R_JEV_MS", "R_JEV_RS")})
        R5.update({"R_JEV_MEETS": "-",
                   "R_SAVE_JEV": f"{JEV_NA}: the saved run holds no decision of Jev's (JEV_MODE {RUN.get('jev_mode', 'off')})."})
else:
    for k in ("R_RULE_RR", "R_RULE_AR", "R_GEN_RR", "R_GEN_AR", "R_RULE_FA", "R_GEN_FA", "R_RULE_CAL", "R_GEN_CAL",
              "R_GEN_MS", "R_GEN_RS", "R_SAVE_RULE"):
        R5[k] = AWAIT_RUN
    R5.update({"R_RULE_MEETS": "-", "R_GEN_MEETS": "-"})
    R5.update({k: JEV_NA for k in ("R_JEV_RR", "R_JEV_AR", "R_JEV_FA", "R_JEV_CAL", "R_JEV_MS", "R_JEV_RS")})
    R5.update({"R_JEV_MEETS": "-", "R_SAVE_JEV": f"{JEV_NA}: JEV_MODE is off, TypeSafe's adapter is PR 2.6-C, and no recording exists."})


# ------------------------------------------------------------------ the floor widget: its rows, its table, its script
def arm_points(arm: str) -> dict | None:
    """The recorded arm's place on the plot and in the per-shape table, from the saved run."""
    if RUN is None or not S[arm]["available"]:
        return None
    sh = {}
    for s in SHAPES:
        d = [r for r in RUN["rows"] if r["shape"] == s and decided(r["arms"].get(arm))]
        sh[s] = [sum(decide.right(r, arm) for r in d), len(d)]
    return {"ar": list(S[arm]["answer_rate"]), "rr": list(S[arm]["refusal_recall"]), "arS": rate(*S[arm]["answer_rate"]),
            "rrS": rate(*S[arm]["refusal_recall"]), "shape": sh}


RECP = None if RUN is None else {"rule": arm_points("rule"), "generator": arm_points("generator"), "jev": arm_points("jev"),
                                 "floor": RUN["floor"], "who": REC_WHO}
DATA = {"rows": [{k: x[k] for k in ("id", "shape", "ans", "share", "pool")} for x in ROWS], "floor": FLOOR, "gate": GATE,
        "shapes": list(SHAPES), "nAns": N_ANS, "nUn": N_UN,
        "R": {str(n): [rate(k, n) for k in range(n + 1)] for n in (N_ANS, N_UN, N_ROWS)},
        "rec": RECP, "jevWhy": system_one.OFF_REASON}


def ladder_html() -> str:
    """The rows the floor can move: every row whose top five passages carry less than all of its question."""
    out = []
    for x in BELOW:
        i = next(k for k, y in enumerate(ROWS) if y["id"] == x["id"])
        truth = "answerable" if x["ans"] else "not answerable"
        out.append(f'<li class="dc-bar" data-i="{i}"><span class="dc-id">{x["id"]}<em>{x["shape"]}, {truth}</em></span>'
                   f'<span class="dc-track"><span class="dc-fill" style="width:{x["share"] * 100:.1f}%"></span><span class="dc-fl"></span></span>'
                   f'<span class="dc-sh">{x["share"]:.3f}</span><span class="dc-v"></span></li>')
    return "\n".join(out)


def shape_rows() -> str:
    """The per-shape table: the rule's cell is the script's; the generator's and Jev's are the saved run's, or absent."""
    out = []
    for s in SHAPES:
        rows = BY_SHAPE[s]
        un = sum(1 for r in rows if not r["answerable"])
        n = f"{len(rows)}" + ("" if not un else ", none answerable" if un == len(rows) else f", {un} not answerable")
        gen = ("awaiting the author's run" if RECP is None else
               f"{RECP['generator']['shape'][s][0]}/{RECP['generator']['shape'][s][1]}")
        jev = (JEV_NA if RECP is None or RECP["jev"] is None else f"{RECP['jev']['shape'][s][0]}/{RECP['jev']['shape'][s][1]}")
        out.append(f'<tr><td><strong>{s}</strong></td><td data-label="Rows">{n}</td>'
                   f'<td data-label="Rule at the floor" id="dc-s-{s}">-</td><td data-label="Generator">{gen}</td>'
                   f'<td data-label="Jev">{jev}</td></tr>')
    return "\n".join(out)


KEYS = {
    "KEY_RULE_LANE": ("" if RECP is None or RECP["rule"] is None else
                      f'<span class="ring" style="--k:#0d9488">the rule at {RECP["floor"]:.2f} on {REC_WHO}</span>'),
    "KEY_GEN": "the generator: awaiting the author's run" if RECP is None else f"the generator on {REC_WHO}",
    "KEY_JEV": (f"{JEV_NA}: JEV_MODE is off and TypeSafe's adapter is PR 2.6-C" if RECP is None or RECP["jev"] is None
                else f"Jev on {REC_WHO}"),
}


JS = """<script>
(function(){
  'use strict';
  var D = __DATA__;
  var root = document.getElementById('decider'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var slider = $('dc-floor'), plot = $('dc-plot'), W = 320, H = 250, X0 = 46, X1 = 306, Y0 = 18, Y1 = 206;
  function verdict(r, f){ return r.pool && r.share >= f ? 'answer' : 'refuse'; }
  function counts(f){
    var c = {tp: 0, fn: 0, fp: 0, tn: 0, fa: [], right: {}, dec: {}};
    D.shapes.forEach(function(s){ c.right[s] = 0; c.dec[s] = 0; });
    D.rows.forEach(function(r){
      var v = verdict(r, f);
      c.dec[r.shape]++; if ((v === 'answer') === r.ans) c.right[r.shape]++;
      if (r.ans) { if (v === 'answer') c.tp++; else c.fn++; }
      else if (v === 'answer') { c.fp++; c.fa.push(r.id + (r.shape === 'isolation' ? '*' : '')); }
      else c.tn++;
    });
    return c;
  }
  function px(ar){ return X0 + (X1 - X0) * ar; }
  function py(rr){ return Y1 - (Y1 - Y0) * rr; }
  function dot(x, y, r, fill, label, ring){
    return '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="' + r + '" fill="' + fill + '" stroke="' + (ring || '#fff') + '" stroke-width="2"><title>' + label + '</title></circle>';
  }
  function draw(f, c){
    var g = [], i, k;
    for (i = 0; i <= 2; i++) {
      var t = i / 2;
      g.push('<line x1="' + X0 + '" x2="' + X1 + '" y1="' + py(t) + '" y2="' + py(t) + '" stroke="#e7e5e4" stroke-width="1"/>');
      g.push('<line x1="' + px(t) + '" x2="' + px(t) + '" y1="' + Y0 + '" y2="' + Y1 + '" stroke="#e7e5e4" stroke-width="1"/>');
      g.push('<text x="' + (X0 - 6) + '" y="' + (py(t) + 4) + '" text-anchor="end">' + (t * 100) + '%</text>');
      g.push('<text x="' + px(t) + '" y="' + (Y1 + 16) + '" text-anchor="middle">' + (t * 100) + '%</text>');
    }
    g.push('<line x1="' + X0 + '" x2="' + X1 + '" y1="' + py(D.gate) + '" y2="' + py(D.gate) + '" stroke="#b45309" stroke-width="2"/>');
    g.push('<text x="' + (X0 + 4) + '" y="' + (py(D.gate) - 5) + '">the gate: refusal recall ' + D.gate.toFixed(2) + '</text>');
    g.push('<text class="t" x="' + ((X0 + X1) / 2) + '" y="' + (H - 4) + '" text-anchor="middle">answer rate (of ' + D.nAns + ' answerable)</text>');
    g.push('<text class="t" transform="translate(11 ' + ((Y0 + Y1) / 2) + ') rotate(-90)" text-anchor="middle">refusal recall (of ' + D.nUn + ' not)</text>');
    var pts = [];
    for (k = 0; k < 100; k++) { var cc = counts(k / 100); pts.push(px(cc.tp / D.nAns).toFixed(1) + ',' + py(cc.tn / D.nUn).toFixed(1)); }
    g.push('<polyline points="' + pts.join(' ') + '" fill="none" stroke="#0d9488" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>');
    var rec = D.rec;
    if (rec && rec.rule) g.push(dot(px(rec.rule.ar[0] / rec.rule.ar[1]), py(rec.rule.rr[0] / rec.rule.rr[1]), 5, '#fff', 'rule at ' + rec.floor.toFixed(2) + ' on ' + rec.who + ': answer rate ' + rec.rule.arS + ', refusal recall ' + rec.rule.rrS, '#0d9488'));
    if (rec && rec.generator) g.push(dot(px(rec.generator.ar[0] / rec.generator.ar[1]), py(rec.generator.rr[0] / rec.generator.rr[1]), 6, '#7c3aed', 'generator on ' + rec.who + ': answer rate ' + rec.generator.arS + ', refusal recall ' + rec.generator.rrS));
    if (rec && rec.jev) g.push(dot(px(rec.jev.ar[0] / rec.jev.ar[1]), py(rec.jev.rr[0] / rec.jev.rr[1]), 6, '#c2410c', 'Jev on ' + rec.who + ': answer rate ' + rec.jev.arS + ', refusal recall ' + rec.jev.rrS));
    g.push(dot(px(c.tp / D.nAns), py(c.tn / D.nUn), 6, '#0d9488', 'rule at ' + f.toFixed(2) + ' on the Rs 0 lane: answer rate ' + D.R[D.nAns][c.tp] + ', refusal recall ' + D.R[D.nUn][c.tn]));
    plot.innerHTML = g.join('');
  }
  function render(){
    var f = Math.round(parseFloat(slider.value) * 100) / 100, c = counts(f);
    $('dc-fv').textContent = f.toFixed(2);
    $('dc-tp').textContent = c.tp; $('dc-fn').textContent = c.fn; $('dc-fp').textContent = c.fp; $('dc-tn').textContent = c.tn;
    $('dc-ar').textContent = D.R[D.nAns][c.tp]; $('dc-rr').textContent = D.R[D.nUn][c.tn]; $('dc-acc').textContent = D.R[D.nAns + D.nUn][c.tp + c.tn];
    $('dc-fa').textContent = c.fa.length ? c.fa.length + ': ' + c.fa.join(' ') : 'none';
    $('dc-sum').textContent = 'At ' + f.toFixed(2) + ' the rule answers ' + (c.tp + c.fp) + ' of the ' + (D.nAns + D.nUn) + ' rows and refuses ' + (c.fn + c.tn) + ', for Rs 0: refusal recall ' + (c.tn >= D.gate * D.nUn ? 'meets' : 'is under') + ' the gate\\'s ' + D.gate.toFixed(2) + '.';
    D.shapes.forEach(function(s){ $('dc-s-' + s).textContent = c.right[s] + '/' + c.dec[s]; });
    Array.prototype.forEach.call(root.querySelectorAll('.dc-bar'), function(el){
      var r = D.rows[+el.getAttribute('data-i')], v = verdict(r, f);
      el.className = 'dc-bar ' + ((v === 'answer') === r.ans ? 'ok' : 'bad');
      el.querySelector('.dc-v').textContent = v;
      el.querySelector('.dc-fl').style.left = (f * 100) + '%';
    });
    draw(f, c);
  }
  slider.addEventListener('input', render); slider.addEventListener('change', render);
  Array.prototype.forEach.call(root.querySelectorAll('.dc-pre'), function(b){ b.addEventListener('click', function(){ slider.value = b.getAttribute('data-f'); render(); }); });
  render();
})();
</script>
""".replace("__DATA__", json.dumps(DATA, separators=(",", ":")).replace("</", "<\\/"))
assert "<tr" not in JS and "<svg" not in JS and "font-size" not in JS


# ------------------------------------------------------------------ the windows: what you run, and what it prints
def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


heredoc = lambda src: "python - <<'PY'\n" + src + "\nPY"       # noqa: E731
LEARNER_CMD = 'make decide PROJECT="$PROJECT" REGION="$REGION" DECIDE_ARGS="--tenant zeta --save evals/reports/decide-zeta.json"'
LIVE_CMD = 'make decide PROJECT="$PROJECT" REGION="$REGION" DECIDE_ARGS="--save evals/reports/decide-live.json"'
CELLS = {
    "golden": ("run in the operator shell, in $DEMO_ROOT (Rs 0: one line of the golden set)", f'python -c "{GOLDEN_PY}"'),
    "ui": (f"run in the operator shell, in $DEMO_ROOT (a Python cell: one generator call, about Rs {COST['RF01_IN']} of input "
           f"by the kit's own count and at most Rs {COST['OUT_CAP_CALL']} of output; the passages call costs nothing)", heredoc(UI_PY)),
    "explain": ("run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: nothing leaves the machine)", heredoc(EXPLAIN_PY)),
    "local": ("run in the operator shell, in $DEMO_ROOT (Rs 0: no lane and no model; a few minutes, because it ranks the tenant's whole corpus for every row)",
              "python evals/decide.py --local"),
    "floor": ("run in the operator shell, in $DEMO_ROOT (the Change-it: the same Rs 0 run with a higher floor)",
              "python evals/decide.py --local --floor 0.7"),
    "zeta_rec": ("run in the operator shell, in $DEMO_ROOT (Rs 0: Jev's recorded mode, on zeta's ten rows)",
                 "JEV_MODE=recorded python evals/decide.py --local --tenant zeta"),
    "switch": ("run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: no socket opens in any mode)", heredoc(SWITCH_PY)),
    "learner": (f"run in the operator shell, in $DEMO_ROOT (zeta's {N_ZETA} rows: {N_ZETA} passages calls at Rs 0 and {N_ZETA} "
                f"generator calls, about Rs {COST['ZETA_IN']} of input and at most Rs {COST['ZETA_CAP']} in all)", LEARNER_CMD),
    "live": (f"run in the operator shell, in $DEMO_ROOT (optional: all {N_ROWS} rows, about Rs {COST['RUN_IN']} of input and at "
             f"most Rs {COST['RUN_CAP']} in all)", LIVE_CMD),
}
OUTS = {
    "golden": ("(evals/golden.jsonl, read when this page was built)", OUT_GOLDEN),
    "ui": ("(the author's lane: your tokens, times and words are yours)", REC["ui_refusal"]),
    "explain": ("(the kit's own output, produced when this page was built; yours should match it)", OUT_EXPLAIN),
    "local": ("(the kit's own output, produced when this page was built; the rule's two latency figures are your machine's)", OUT["local"]),
    "floor": ("(the kit's own output at 0.70, produced when this page was built)", OUT["floor"]),
    "zeta_rec": ("(the kit's own output, produced when this page was built)", OUT["zeta_rec"]),
    "switch": ("(the kit's own output, produced when this page was built; yours should match it)", OUT_SWITCH),
    "learner": ("(the author's lane, with make's echo of the recipe: your ids, times and verdicts are yours)", REC["decide_learner"]),
    "live": ("(the author's full run, 65 rows: the figures below are computed from its saved file)", REC["decide_live"]),
}
WIN = {f"CELL_{k.upper()}": bash_window(*v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})

NEXT = MANIFEST["modules"]["03"]
STATS = {
    "N_ROWS": str(N_ROWS), "N_ANS": str(N_ANS), "N_UN": str(N_UN), "N_REF_UN": str(N_REF_UN), "N_ISO_UN": str(N_ISO_UN),
    "FLOOR": f"{FLOOR}", "FLOOR2": f"{FLOOR:.2f}", "GATE": f"{GATE:.2f}", "TOPK": str(TOPK), "GEN_TOPK": str(GEN_TOPK),
    "N_ANY": str(N_ANY), "ANY_T": " and ".join(ANY_T), "N_ZETA": str(N_ZETA), "ZETA_ANS": str(ZETA_ANS), "ZETA_UN": str(N_ZETA - ZETA_ANS),
    "JEV_USD": f"{JEV_USD:.0f}", "USD_INR": str(USD_INR), "GEN_MODEL": GEN_MODEL, "RATE_IN": f"{RATE_IN:.2f}", "RATE_OUT": f"{RATE_OUT:.2f}",
    "BRIER_RULE": BRIER_RULE, "W18": f"{100 * W18:.1f}%", "N_AT1": str(len(AT1)), "N_AT1_ANS": str(sum(1 for x in AT1 if x["ans"])),
    "N_AT1_UN": str(len(AT1_UN)), "AT1_UN_IDS": ", ".join(AT1_UN), "N_BELOW": str(len(BELOW)),
    "BEST_RR": rate(BEST_TN, N_UN), "BEST_FLOOR": f"{BEST[0]:.2f}", "BEST_AR": rate(BEST[1], N_ANS), "BEST_MEETS": meets(BEST_TN, N_UN),
    "SH_RF01": f"{SHARE['rf-01']:.2f}", "SH_RF02": f"{SHARE['rf-02']:.2f}", "NOT_CONFIGURED": html.escape(system_one.NOT_CONFIGURED),
    "LADDER": ladder_html(), "SHAPE_ROWS": shape_rows(), **KEYS, "NEXT_TITLE": html.escape(NEXT["lessons"]["3.1"]["name"]),
    **L, **COST, **{k: html.escape(v) for k, v in R5.items()},
}


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)

# the run list's prices, from the same figures: a stale line is named here, not silently kept
run_list = (pb.lesson_dir(LESSON) / "RUN_LIST.md").read_text(encoding="utf-8")
for k in ("UI_IN", "UI_CAP", "ZETA_IN", "ZETA_CAP", "RUN_IN", "RUN_CAP", "JEV_RS"):
    if f"Rs {COST[k]}" not in run_list:
        print(f"note: RUN_LIST.md does not state {k} = Rs {COST[k]}")
print(f"kit: {N_ROWS} rows ({N_ANS} answerable) | floor {FLOOR} | gate {GATE} | rule at {FLOOR:.2f}: {L['L5_RR']} refusal recall, "
      f"{L['L5_AR']} answer rate | at 0.70: {L['L7_RR']} | best on the Rs 0 lane {rate(BEST_TN, N_UN)} from {BEST[0]:.2f} "
      f"| {len(AT1)} rows at 1.00 ({len(AT1_UN)} not answerable) | prompts {COST['TOK_MIN']}-{COST['TOK_MAX']} tokens, "
      f"run Rs {COST['RUN_IN']} in / Rs {COST['RUN_CAP']} cap | Jev {COST['JEV_TOK']} tokens Rs {COST['JEV_RS']} "
      f"| recorded run: {'yes' if RUN else 'awaiting'}")
