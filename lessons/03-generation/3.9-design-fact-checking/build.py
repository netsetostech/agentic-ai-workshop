"""Build lesson 3.9 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

A design page: a fact desk, where a claim comes in and leaves with a verdict that stands on a quoted clause or with a
refusal, built from the kit's own stations - the Desk's door, /v1/passages, the generator's contract, quote_holds()
and the judge. The page is written in the shape of the capstone rubric (plan/capstone-rubric.md, which lesson 11.8
publishes): its sections follow the five dimensions and say what a 3 looks like on each. The proof maps to the rubric's
component 5 (three rejected options, each with the threshold that would change it) and component 6 (the cost at 1k,
10k and 100k claims a month, in rupees at USD_INR, dated).

What the page computes at build time:
  - the rubric's shape, parsed from plan/capstone-rubric.md: the components, the dimensions, the points and the pass;
  - the path's facts from the kit: the door's routes and classes, /v1/passages's row, QueryRequest's limits, the pool
    and the top_k, ModelDraft's quote limit, SYSTEM's 25 words, the reserve and the budget TokenBudget.fit() gives a
    claim (generator.py's own strings), the judge's metrics, region and verdict line;
  - the cost model: shared/prices.py's rates and USD_INR, the TokenBudget ceiling per claim (an upper bound), the
    embedding, ranking and judge prices the kit does not hold (below), and lessons/00-setup/standing_cost.py's monthly
    floor, imported, never re-derived; at 1k, 10k and 100k claims, both shard sizes;
  - the limits: documind-api's flags (commands/lesson-12.2.sh), the index's replicas (terraform/vector.tf), quota.tf's
    override and its switch (Makefile), the API's latency SLO (terraform/alerts.tf); the alert policies the kit
    declares, against the names quota.tf lists;
  - the rejected options' thresholds: the cache's floor (cache_manager.py), its read rate (cost.py) and its storage
    price (below), each tenant's corpus by the kit's estimate (run_eval.load_corpus), the cache packs
    (cache_admin.pack_for), the data_region policies make roster sets (commands/lane.py);
  - the evals: run_eval's thresholds and required rows, the golden rows that carry must_not_contain;
  - six offline cells, executed here in deploy/, whose output is the page's expected output, each held against the
    numbers above.

Prices the kit does not hold, read on 8 October 2026 from Google's pages; verify before a cohort:
  - https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing (redirected from
    cloud.google.com/vertex-ai/generative-ai/pricing; no date on the page): "Embeddings for Text (Excluding Gemini
    Embedding)", input, online requests, $0.000025 per 1,000 count (characters, as lessons 1.3, B.2 and B.4 read it;
    the API reports billable_character_count); Gemini 2.0 Flash, input text $0.15 and output text $0.60 per 1M tokens;
    "Context Cache Storage price for Explicit Caching", Gemini 3.6 Flash, $0.000001 per token per hour; and gemini-3.6-
    flash's introductory $0.75 / $3.75 per 1M tokens through 31 December 2026, the standard $1.50 / $7.50 (the kit's
    rates) from 1 January 2027.
  - https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing (redirected from
    cloud.google.com/vertex-ai/pricing), "Gen AI Evals": "For model-based metrics, charges are applied only for the
    prediction costs associated with the underlying autorater model"; the default autorater for pointwise and
    pairwise metrics is Gemini 2.0 Flash.
  - https://cloud.google.com/generative-ai-app-builder/pricing ("Agent Search pricing"), "Ranking API pricing":
    Ranking $1.00 per 1,000 count; "A query is defined as having up to 100 documents".

The one live output, make usage's by-model table, is read with pb.recorded() from data/usage_tokens.txt once the
author's run is recorded (RUN_LIST.md); until then the page shows a marked stand-in and the ceiling stands alone.
"""
import ast
import html
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules imported below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, PLAN, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "3.9"
NAME = pb.lesson_meta(LESSON)[1]["name"]
title = (f"<title>Lesson {LESSON} {NAME} - the stations a claim passes, the price at three scales, and the designs "
         "the kit's own numbers reject | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.fx-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px 16px;margin-bottom:10px;align-items:end;}
.fx-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.fx-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.fd-path{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:8px;font-size:12.5px;}
.fd-st{margin:0;background:var(--card);border:1px solid var(--border);border-left:4px solid var(--teal);border-radius:10px;padding:8px 12px;line-height:1.5;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.fd-st b{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;}
.fd-st .fd-f{display:block;font-family:var(--mono);font-size:var(--kicker-size);color:var(--cyan);margin-bottom:2px;}
.fd-st .fd-c{display:block;font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal-dark);margin-top:4px;}
.fd-st.skip{border-left-style:dashed;border-left-color:#cbd5e1;background:var(--bg);color:#64748b;}
.fd-st.held{border-left-color:#f59e0b;background:#fffbeb;}
.fd-st.stop{border-left-color:#0891b2;background:#ecfeff;}
.fd-st.side{border-left-style:dotted;}
.fx-out{font-size:var(--small-size);color:var(--navy);font-weight:700;margin:10px 0 0;}
"""

setup = setup_section()
src = lambda rel: (KIT / rel).read_text(encoding="utf-8")  # noqa: E731


def one(pattern: str, text: str, flags: int = 0) -> str:
    """The one match of a pattern's first group: a kit fact the page states, or the build stops."""
    found = re.findall(pattern, text, flags)
    assert len(found) == 1, (pattern, found)
    return found[0]


def r0(x: float) -> int:
    """Half up, as the widgets' Math.round rounds, so a page and its widget print the same rupees."""
    return int(math.floor(x + 0.5))


def inr(n: int) -> str:
    """Whole rupees grouped the Indian way: 32,157 and 2,76,393."""
    s = str(int(n))
    head, tail = s[:-3], s[-3:]
    while len(head) > 2:
        head, tail = head[:-2], head[-2:] + "," + tail
    return f"{head},{tail}" if head else tail


def esc(t: str) -> str:
    return html.escape(t, quote=False)


def word(n: int) -> str:
    """A small count as the prose says it: 'five classes', not '5 classes'."""
    return "zero one two three four five six seven eight nine ten eleven twelve".split()[n]


# ================================================================== the rubric (plan/capstone-rubric.md)
RUBRIC = (PLAN / "capstone-rubric.md").read_text(encoding="utf-8")
COMPONENTS = re.findall(r"^\| (\d) \| (.+?) \| (.+?) \| (.+?) \|$", RUBRIC, re.M)        # number, component, where from, the check
assert [int(row[0]) for row in COMPONENTS] == list(range(1, 9)), COMPONENTS
N_COMPONENTS = len(COMPONENTS)
assert "ARCHITECTURE.md" in COMPONENTS[4][1] and "rejected" in COMPONENTS[4][1]
assert COMPONENTS[4][3] == "It names at least three rejected options and why."
assert "COST-MODEL.md" in COMPONENTS[5][1] and "1k / 10k / 100k queries a month" in COMPONENTS[5][1]
assert COMPONENTS[5][3] == "Dual-priced INR, dated, at `USD_INR = 85`."
assert "FAILURE-MODES.md" in COMPONENTS[6][1] and "four entries, each proved by a script" in COMPONENTS[6][1]
DIMS = re.findall(r"^### (\d)\. (.+?) \(0–3\)$", RUBRIC, re.M)
assert [d for _, d in DIMS] == ["Architecture", "Failure modes", "Cost at 10×", "Evals", "What you would do next month"], DIMS
N_DIMS = len(DIMS)
SCORE_LINE = one(r"\*\*(\w+) dimensions, scored 0–3 each\. (\d+) points available\. (\d+) to pass, with no dimension at 0\.\*\*",
                 RUBRIC)
assert SCORE_LINE[0] == "Five" and int(SCORE_LINE[1]) == 3 * N_DIMS
POINTS, PASS = int(SCORE_LINE[1]), int(SCORE_LINE[2])
assert (POINTS, PASS) == (15, 9)
# lesson 11.8 publishes it and checks the components; the defence scores the dimensions (13 October 2026)
assert "lesson 11.8's page shows this document to learners" in RUBRIC and "`make capstone-check FORK=<the fork>`" in RUBRIC

# ================================================================== the path, from the kit
MAIN, GEN, CFG = src("services/rag-api/main.py"), src("services/rag-api/generator.py"), src("services/rag-api/config.py")
SCHEMAS, SHARED_SCHEMAS = src("services/rag-api/schemas.py"), src("shared/documind_schemas.py")
DOOR, RULES, TOOLS = src("services/rag-api/desk_door.py"), src("shared/desk_rules.py"), src("shared/documind_tools.py")
TRAINSET, JUDGE, RUN_EVAL = src("evals/make_trainset.py"), src("evals/judge.py"), src("evals/run_eval.py")
RETRIEVER = src("services/rag-api/retriever.py")

DOOR_PATHS = ast.literal_eval(one(r"^PATHS = (\{.*\})$", DOOR, re.M))
assert set(DOOR_PATHS) == {"/v1/query", "/v1/stream", "/v1/passages"}
DOOR_CLASSES = ast.literal_eval(one(r"^CLASSES = (\(.*\))$", RULES, re.M))
N_CLASSES = len(DOOR_CLASSES)
assert 'return v if isinstance(v, str) and v in GATE_STATES else "rules"' in RULES        # unset reads as rules
assert '{"passages": [], "answer": text, "answerable": False, "usage": usage}' in DOOR          # a hit on /v1/passages
assert '"backend": "desk_gate"' in DOOR and '"cost_usd": 0.0' in DOOR
PASSAGES_FN = MAIN.split('@app.post("/v1/passages")', 1)[1]
assert 'model="none", backend="none", cost_usd=0.0' in PASSAGES_FN and '"passages"' in PASSAGES_FN
assert "    if chunks:\n        with stage(stages, \"rerank\"):" in PASSAGES_FN                     # an empty pool skips the ranker
assert "vec = vec if vec is not None else embed_query(query)" in RETRIEVER                       # one embedding per claim
TOP_K = int(one(r"top_k: int = Field\(default=(\d+), ge=1, le=20\)", SCHEMAS))
QUERY_MAX = int(one(r"query: str = Field\(min_length=1, max_length=(\d+)\)", SCHEMAS))
POOL = int(one(r'top_k_retrieve: int = Field\((\d+), alias="TOP_K_RETRIEVE"\)', CFG))
assert "chunks = chunks[:200]" in RETRIEVER
TOTAL = int(one(r"max_context_tokens: int = (\d+)", CFG))
ANSWER = int(one(r"max_answer_tokens: int = (\d+)", CFG))
GEN_MODEL = one(r'generator_model: str = "([^"]+)"', CFG)
EMBED_MODEL = one(r'embed_model: str = Field\("([^"]+)", alias="EMBEDDING_MODEL"\)', CFG)
assert 'thinking_config=types.ThinkingConfig(thinking_level="LOW")' in GEN and "response_schema=ModelDraft," in GEN
DRAFT_QUOTE_MAX = int(one(r'quote: str = Field\(max_length=(\d+), description="Exact words from that source"\)', SHARED_SCHEMAS))
assert 'c["quote"] = c["quote"][: limit - 3].rstrip() + "..."' in GEN                              # _draft()'s trim
assert "at most twenty-five words" in GEN
QUOTE_WORDS = int(one(r"len\(quote\.split\(\)\) <= (\d+) and _flat\(quote\) in _flat\(passage\)", TRAINSET))
assert QUOTE_WORDS == 25
assert 'quote=(quote or c.get("text", ""))[:500],' in SHARED_SCHEMAS                              # resolve() copies the quote
assert "            cite(d.source, d.quote)" in SHARED_SCHEMAS                                       # the draft's own, as it came
assert 'return ["GROUNDEDNESS", second], [ex.Pointwise.GROUNDEDNESS, getattr(ex.Pointwise, second)]' in JUDGE
N_METRICS = 2
JUDGE_REGION = one(r'pairwise: bool, project: str, location: str = "([a-z0-9-]+)",', JUDGE)
assert 'print("\\n  the gate (run_eval.py) still decides; this judge explains. Where they disagree, read the row.")' in JUDGE

sys.path[:0] = [str(KIT), str(KIT / "services" / "rag-api"), str(KIT / "evals"), str(ROOT / "lessons" / "00-setup")]
from context_budget import TokenBudget, estimate_tokens  # noqa: E402
from shared.prices import PRICES, USD_INR  # noqa: E402
from run_eval import THRESHOLDS, load_corpus, load_golden, load_required  # noqa: E402
from cache_admin import pack_for  # noqa: E402
import standing_cost as sc  # noqa: E402
assert sc.USD_INR == USD_INR == 85

K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(GEN).body
     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
assert '    fixed = f"{SYSTEM}{DATED_RULE}\\n\\nContext:\\n\\n\\nQuestion: {query}"' in GEN       # generator._budget(), line for line
CLAIM = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
BUDGET = TokenBudget.fit(TOTAL, f"{K['SYSTEM']}{K['DATED_RULE']}\n\nContext:\n\n\nQuestion: {CLAIM}", estimate_tokens, answer=ANSWER)
TIN, TOUT = BUDGET.input_total, BUDGET.answer
assert (TIN, TOUT) == (TOTAL, ANSWER), BUDGET

# ================================================================== prices: the kit's, and the ones it does not hold
R_IN, R_OUT = PRICES[GEN_MODEL]
assert (R_IN, R_OUT) == (1.50, 7.50) and PRICES["gemini-3.1-flash-lite"] == (0.25, 1.50)
CACHED = float(one(r"\+ cached_tokens \* usd_in \* ([\d.]+)", src("services/rag-api/cost.py")))
assert CACHED == 0.10
MIN_CACHE = int(one(r"MIN_CACHE_TOKENS = ([\d_]+)", src("services/rag-api/cache_manager.py")).replace("_", ""))
PRICE_DATE = "8 October 2026"
# Google's list prices the kit does not hold, each read on 8 October 2026 and each to verify before a cohort.
# Verify: https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing, "Embedding costs", "Embeddings for
# Text (Excluding Gemini Embedding)", input, online requests, $0.000025 per 1,000 count (characters: lessons 1.3, B.2, B.4).
EMBED_USD_1K = 0.000025
# Verify: https://cloud.google.com/generative-ai-app-builder/pricing, "Ranking API pricing", Ranking $1.00 per 1,000 count;
# "A query is defined as having up to 100 documents".
RANK_USD_1K, RANK_DOCS = 1.00, 100
# Verify: https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing, "Gen AI Evals": model-based metrics are
# billed as the autorater's prediction, and the default autorater is Gemini 2.0 Flash; its price, input text $0.15 and output
# text $0.60 per 1M tokens, from https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing ("Gemini 2.0").
JUDGE_IN, JUDGE_OUT = 0.15, 0.60
# Verify: https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing, "Context Cache Storage price for
# Explicit Caching", Gemini 3.6 Flash, $0.000001 per token per hour (at or under and over 200K input tokens alike).
STORE_USD = 0.000001
# Verify: the same page, "Gemini 3.6 Flash * through December 31, 2026": $0.75 in, $3.75 out per 1M tokens; the standard
# $1.50 / $7.50, shared/prices.py's, from 1 January 2027.
INTRO_IN, INTRO_OUT = 0.75, 3.75
FLOOR_DATE = one(r"Mumbai \(asia-south1\), read on (\d+ \w+ \d{4})", Path(sc.__file__).read_text(encoding="utf-8"))

# ================================================================== the cost of a claim, at the ceiling
JUDGED = 0.05                      # the design's choice: the judge reads one claim in twenty
MODEL_USD = (TIN * R_IN + TOUT * R_OUT) / 1e6
EMBED_USD = QUERY_MAX / 1000 * EMBED_USD_1K
RANK_USD = math.ceil(POOL / RANK_DOCS) * RANK_USD_1K / 1000
assert math.ceil(POOL / RANK_DOCS) == 1
RET_USD = EMBED_USD + RANK_USD
JUDGE_USD = N_METRICS * ((TIN + TOUT) * JUDGE_IN + TOUT * JUDGE_OUT) / 1e6     # per judged claim; the verdict assumed as long as the answer
SCALES = (1_000, 10_000, 100_000)
SCALE_WORD = {1_000: "1k", 10_000: "10k", 100_000: "100k"}
SHARDS = list(sc.SHARDS)                                                         # small, medium
FLOOR = {"lane": dict(sc.PER_MONTH),
         "api": {s: r0((sc.INDEX_USD[s] + sc.item_usd("conn", s)) * sc.MONTH_H * USD_INR) for s in SHARDS}}
assert sc.item_usd("conn", "small") == sc.item_usd("conn", "medium")


def month(q: int, tin: float, tout: float, judged: float, floor: int) -> dict:
    """One scale's month in whole rupees: each part rounded half up, the total their sum, so a row adds up."""
    model = r0(q * (tin * R_IN + tout * R_OUT) / 1e6 * USD_INR)
    ret = r0(q * RET_USD * USD_INR)
    judge = r0(q * judged * N_METRICS * ((tin + tout) * JUDGE_IN + tout * JUDGE_OUT) / 1e6 * USD_INR)
    total = model + ret + judge + floor
    return {"model": model, "ret": ret, "judge": judge, "floor": floor, "total": total, "usd": r0(total / USD_INR), "per": total / q}


COST = {(q, s): month(q, TIN, TOUT, JUDGED, FLOOR["lane"][s]) for q in SCALES for s in SHARDS}
PER_CLAIM_USD = MODEL_USD + RET_USD + JUDGED * JUDGE_USD
BREAK_EVEN = {s: r0(FLOOR["lane"][s] / (PER_CLAIM_USD * USD_INR)) for s in SHARDS}
assert all(1_000 < BREAK_EVEN[s] < 100_000 for s in SHARDS), BREAK_EVEN

# ================================================================== the rejected options' numbers
CORPUS = {t: sum(estimate_tokens(x) for x in docs.values()) for t, docs in load_corpus().items()}
assert set(CORPUS) == {"acme", "globex", "zeta"}
PACKS = {t: estimate_tokens(pack_for(t)[0]) for t in CORPUS}
assert PACKS["globex"] < MIN_CACHE < min(PACKS["acme"], PACKS["zeta"]), PACKS
REPLACED_USD = BUDGET.chunks * R_IN / 1e6 + RET_USD        # what a cache replaces per claim, at the ceiling
CACHE_MAX = {q: REPLACED_USD / (CACHED * R_IN / 1e6 + STORE_USD * sc.MONTH_H / q) for q in SCALES}
CORPUS_STORE_INR = {t: n * STORE_USD * sc.MONTH_H * USD_INR for t, n in CORPUS.items()}
CORPUS_READ_INR = {t: n * CACHED * R_IN / 1e6 * USD_INR for t, n in CORPUS.items()}
assert min(CORPUS["acme"], CORPUS["zeta"]) > max(CACHE_MAX.values()) > CORPUS["globex"]
GLOBEX_CROSS = sc.MONTH_H * STORE_USD / (REPLACED_USD / CORPUS["globex"] - CACHED * R_IN / 1e6)
assert 1_000 < GLOBEX_CROSS < 10_000, GLOBEX_CROSS
LANE = src("commands/lane.py")
POLICIES = ast.literal_eval(one(r"    policies = (\[.*?\])\n", LANE))
assert POLICIES == [("acme", "any"), ("zeta", "any"), ("globex", "in")], POLICIES
TENANCY = src("shared/tenancy.py")
assert 'DATA_REGIONS = ("in", "any")' in TENANCY
DESK_OPS = src("commands/desk_ops.py")
assert "CONFIRM_RESIDENCY=1 once the company has agreed to that" in DESK_OPS
assert not re.search(r"google_search|GoogleSearch", "".join(p.read_text(encoding="utf-8", errors="replace")
                                                             for p in pb.kit_runtime_files("*.py")))     # the kit has no web search
JUDGE_ALL_INR = JUDGE_USD * USD_INR

# ================================================================== the limits at 10x
API_SH, VEC, QUOTA, MK, ALERTS = (src(p) for p in ("commands/lesson-12.2.sh", "terraform/vector.tf", "terraform/quota.tf",
                                                    "Makefile", "terraform/alerts.tf"))
flag = lambda name: int(one(rf"--{name}=(\d+)", API_SH))  # noqa: E731
CONC, MAXI, MINI, TIMEOUT = flag("concurrency"), flag("max-instances"), flag("min-instances"), flag("timeout")
assert (CONC, MAXI, MINI, TIMEOUT) == (40, 20, 0, 120)
REPLICAS = dict(re.findall(r"(min|max)_replica_count = (\d+)", VEC))
assert REPLICAS == {"min": "1", "max": "1"} and sc.VS_REPLICAS == 1
RPM = int(one(r'override_value = "(\d+)"', QUOTA))
QUOTA_SWITCH = one(r"^GEMINI_QUOTA_OVERRIDE \?= (\w+)", MK, re.M)
assert RPM == 600 and QUOTA_SWITCH == "false" and "count          = var.gemini_quota_override ? 1 : 0" in QUOTA
SLO_MS = int(one(r'"api_latency" \{.*?threshold_value\s+=\s+(\d+)', ALERTS, re.S))
SLO_FOR = int(one(r'"api_latency" \{.*?duration\s+=\s+"(\d+)s"', ALERTS, re.S))
UNANS = float(one(r'"unanswerable_rate" \{.*?threshold_value\s+=\s+([\d.]+)', ALERTS, re.S))
UNANS_FOR = int(one(r'"unanswerable_rate" \{.*?duration\s+=\s+"(\d+)s"', ALERTS, re.S))
assert (SLO_MS, SLO_FOR, UNANS, UNANS_FOR) == (3000, 300, 0.20, 1800)
SLOTS = CONC * MAXI
TURN_SLO = SLOTS * 60 * 1000 // SLO_MS
TURN_CUT = SLOTS * 60 // TIMEOUT
CROSS_S = SLOTS * 60 // RPM
assert (TURN_SLO, TURN_CUT, CROSS_S) == (16000, 400, 80)
PER_MIN = {q: q / (sc.MONTH_H * 60) for q in SCALES + (1_000_000,)}
QUOTA_X = {q: RPM / v for q, v in PER_MIN.items()}
CUT_X = {q: TURN_CUT / v for q, v in PER_MIN.items()}
GAP_S = {q: 60 / v for q, v in PER_MIN.items()}
WINDOW = {q: q / (sc.MONTH_H * 3600 / UNANS_FOR) for q in SCALES}               # claims in one of the alert's 30-minute windows
TF = {p.name: p.read_text(encoding="utf-8") for p in sorted((KIT / "terraform").glob("*.tf"))}
DECLARED = {n: f for f, t in TF.items() for n in re.findall(r'resource "google_monitoring_alert_policy" "(\w+)"', t)}
NAMED = re.findall(r"^\s+(\w+) = \"", QUOTA.split("documind_alerts = {", 1)[1].split("\n  }", 1)[0], re.M)
assert NAMED == ["unanswerable_rate", "dlq_depth", "guardrail_blocks", "cache_hit_low", "burn_rate"], NAMED
UNDECLARED = [n for n in NAMED if n not in DECLARED]
assert UNDECLARED == ["guardrail_blocks", "cache_hit_low", "burn_rate"] and "local.documind_alerts" not in "".join(TF.values())
assert not re.search(r"request_count|response_code|generation_unparsed", "".join(TF.values()))   # no policy counts the API's 5xx
assert '"event": "generation_unparsed"' in GEN and 'raise HTTPException(502, f"generation produced no parseable answer ({reason})")' in GEN
assert '(jsonPayload.event="query" OR jsonPayload.event="stream")' in ALERTS
assert "    answerable, confidence = (False, \"low\") if empty else (True, hit.confidence if hit else \"medium\")" in MAIN

# ================================================================== the evals
GOLDEN = load_golden()
REQUIRED = load_required()
NEVER = [r for r in GOLDEN if r.get("must_not_contain")]
ISO = [r for r in NEVER if r["shape"] == "isolation"]
VERSION_ROWS = [r for r in NEVER if r["shape"] == "version"]
assert len(NEVER) == len(ISO) + len(VERSION_ROWS) and [r["id"] for r in VERSION_ROWS] == ["vr-01"]
N_ANSWERABLE = sum(r["answerable"] for r in GOLDEN)
assert "isolation_403_rate" in THRESHOLDS and THRESHOLDS["isolation_403_rate"] == 1.00
assert "That is a hallucination lottery, and a gate that fires by chance" in RUN_EVAL

# ================================================================== the cells: written here, run here, their output the page's
CELLS = {
    "quotes": '''import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "evals"]
from shared import documind_corpus as dc
from make_trainset import quote_holds          # the kit's rule: in the passage, line breaks as spaces, 25 words at most
doc = {"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://uploads/acme/hr_policy_2026.md",
       "text": open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()}
passage = next(c for c in dc.chunk_document(doc, "acme") if c["locator"] == "NP-03")["text"]
flat = lambda s: " ".join(s.split())
clause = flat(passage.split("\\n", 1)[1])                                     # NP-03 under its heading, on one line
quotes = {"the sentence as written": "A confirmed employee at grade E3 or above serves a notice period of 60 days.",
          "across a line break": "Notice runs from the date the resignation is acknowledged in writing.",
          "revision 2's figure": "A confirmed employee at grade E3 or above serves a notice period of 90 days.",
          "a paraphrase": "Confirmed E3 employees must give 60 days of notice.",
          "the whole clause": clause,
          "the clause as _draft() trims it": clause[:197].rstrip() + "..."}
print(f"NP-03: {len(clause)} characters, {len(clause.split())} words under its heading")
for label, q in quotes.items():
    print(f"{label:31} {len(q.split()):2} words | in the passage {str(flat(q) in flat(passage)):5} | "
          f"25 words at most {str(len(q.split()) <= 25):5} | quote_holds {quote_holds(q, passage)}")''',
    "options": '''import ast, re, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "evals", "services/rag-api"]
from shared.prices import PRICES, USD_INR
from context_budget import TokenBudget, estimate_tokens
from run_eval import load_corpus
src = lambda p: open(p, encoding="utf-8").read()
cfg = src("services/rag-api/config.py")
K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(src("services/rag-api/generator.py")).body
     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
CLAIM = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
b = TokenBudget.fit(int(re.search(r"max_context_tokens: int = (\\d+)", cfg).group(1)), f"{K['SYSTEM']}{K['DATED_RULE']}\\n\\nContext:\\n\\n\\nQuestion: {CLAIM}",
                    estimate_tokens, answer=int(re.search(r"max_answer_tokens: int = (\\d+)", cfg).group(1)))
r_in = PRICES["gemini-3.6-flash"][0] / 1e6
cached = float(re.search(r"cached_tokens \\* usd_in \\* ([\\d.]+)", src("services/rag-api/cost.py")).group(1))
floor = int(re.search(r"MIN_CACHE_TOKENS = ([\\d_]+)", src("services/rag-api/cache_manager.py")).group(1).replace("_", ""))
# Google's prices the kit does not hold, read on %%PRICE_DATE%% - verify: cache storage, embeddings, ranking, the judge
STORE, EMBED, RANK, J_IN, J_OUT = %%STORE_PY%%, %%QUERY_MAX%% / 1000 * %%EMBED_PY%%, %%RANK_PY%% / 1000, %%JIN_PY%%, %%JOUT_PY%%
replaced = b.chunks * r_in + EMBED + RANK         # what a cache replaces per claim: the chunks at the ceiling, the embedding, the ranking
print(f"a cache would replace ${replaced:.5f} a claim: {b.chunks:,} chunk tokens at the ceiling, one embedding, one ranking query")
for q in (1_000, 10_000, 100_000):
    print(f"{q:>7,} claims a month: a cached corpus is cheaper below {replaced / (cached * r_in + STORE * 730 / q):>6,.0f} tokens;"
          f" no cache exists below {floor:,}")
for t, docs in load_corpus().items():
    n = sum(estimate_tokens(text) for text in docs.values())
    print(f"{t:7} {n:>7,} tokens: Rs {n * STORE * 730 * USD_INR:>6,.0f} a month to keep it cached, Rs {n * cached * r_in * USD_INR:.2f} a claim to read it")
for t, region in ast.literal_eval(re.search(r"policies = (\\[.*?\\])", src("commands/lane.py")).group(1)):
    print(f"{t:7} data_region {region:3}: " + ("its text stays on the kit's own rows: a web search is refused" if region == "in"
                                               else "a web search only once the tenant has agreed to it"))
judge = 2 * ((b.input_total + b.answer) * J_IN + b.answer * J_OUT) / 1e6     # two metrics, the default autorater, at the ceiling
print(f"a judge on every claim: Rs {judge * USD_INR:.2f} a claim, Rs {judge * USD_INR * 100_000:,.0f} a month at 100k; one in twenty, Rs {judge * USD_INR * 5_000:,.0f}")''',
    "alerts": '''import re, warnings
from pathlib import Path
warnings.filterwarnings("ignore", category=UserWarning)
tf = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path("terraform").glob("*.tf"))}
declared = {n: f for f, t in tf.items() for n in re.findall(r'resource "google_monitoring_alert_policy" "(\\w+)"', t)}
for f in sorted(set(declared.values())):
    print(f"{f} declares {', '.join(n for n, g in declared.items() if g == f)}")
named = re.findall(r"^\\s+(\\w+) = \\"", tf["quota.tf"].split("documind_alerts = {", 1)[1].split("\\n  }", 1)[0], re.M)
for n in named:
    print(f"quota.tf names {n:17} {'declared in ' + declared[n] if n in declared else 'declared by nothing'}")
counted = re.search(r'"google_logging_metric" "queries" \\{.*?filter\\s+= <<EOT(.*?)EOT', tf["alerts.tf"], re.S).group(1)
print("the unanswerable rate counts:", " ".join(counted.split()))
print("rows it never counts:", ", ".join(e for e in ("query", "stream", "passages", "desk_gate") if f'event="{e}"' not in counted))''',
    "cost": '''import ast, re, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/rag-api"]
from shared.prices import PRICES, USD_INR                      # the kit's rates and its rupee rate
from context_budget import TokenBudget, estimate_tokens
src = lambda p: open(p, encoding="utf-8").read()
cfg = src("services/rag-api/config.py")
K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(src("services/rag-api/generator.py")).body
     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
CLAIM = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
b = TokenBudget.fit(int(re.search(r"max_context_tokens: int = (\\d+)", cfg).group(1)), f"{K['SYSTEM']}{K['DATED_RULE']}\\n\\nContext:\\n\\n\\nQuestion: {CLAIM}",
                    estimate_tokens, answer=int(re.search(r"max_answer_tokens: int = (\\d+)", cfg).group(1)))
r_in, r_out = PRICES["gemini-3.6-flash"]
# Google's list prices the kit does not hold, read on %%PRICE_DATE%% - verify before you rely on them
EMBED_1K, RANK_1K, J_IN, J_OUT = %%EMBED_PY%%, %%RANK_PY%%, %%JIN_PY%%, %%JOUT_PY%%   # per 1,000 characters; per 1,000 queries; Gemini 2.0 Flash per 1M
FLOOR = {"SMALL": %%FLOOR_SMALL_PY%%, "MEDIUM": %%FLOOR_MEDIUM_PY%%}                # the lane's standing cost a month, Rs (lessons 0.1 and 0.4)
JUDGED = %%JUDGED_PY%%                                                     # the design's choice: the judge reads one claim in twenty
model = (b.input_total * r_in + b.answer * r_out) / 1e6
retrieval = %%QUERY_MAX%% / 1000 * EMBED_1K + RANK_1K / 1000                 # the longest claim QueryRequest takes; one ranking query
judge = JUDGED * 2 * ((b.input_total + b.answer) * J_IN + b.answer * J_OUT) / 1e6


def inr(x):                                                          # whole rupees, grouped the Indian way: 2,76,393
    s = str(int(x + 0.5))
    head, tail = s[:-3], s[-3:]
    while len(head) > 2:
        head, tail = head[:-2], head[-2:] + "," + tail
    return f"{head},{tail}" if head else tail


print(f"a claim at the ceiling, {b.input_total:,} tokens in and {b.answer:,} out: model ${model:.5f}, retrieval ${retrieval:.5f}, judge ${judge:.6f}")
for q in (1_000, 10_000, 100_000):
    parts = [int(q * usd * USD_INR + 0.5) for usd in (model, retrieval, judge)]       # whole rupees, half up
    for shard, floor in FLOOR.items():
        total = sum(parts) + floor
        print(f"{q:>7,} claims, {shard:6}: model Rs {inr(parts[0])} + retrieval Rs {inr(parts[1])} + judge Rs {inr(parts[2])}"
              f" + floor Rs {inr(floor)} = Rs {inr(total)} (${total / USD_INR:,.0f}), Rs {total / q:.2f} a claim")''',
    "limits": '''import re, warnings
warnings.filterwarnings("ignore", category=UserWarning)
src = lambda p: open(p, encoding="utf-8").read()
api, vec, quota, mk, alerts = (src(p) for p in ("commands/lesson-12.2.sh", "terraform/vector.tf", "terraform/quota.tf", "Makefile", "terraform/alerts.tf"))
flag = lambda name: int(re.search(rf"--{name}=(\\d+)", api).group(1))
conc, most, least, timeout = flag("concurrency"), flag("max-instances"), flag("min-instances"), flag("timeout")
replicas = re.findall(r"(min|max)_replica_count = (\\d+)", vec)
rpm = int(re.search(r'override_value = "(\\d+)"', quota).group(1))
switch = re.search(r"^GEMINI_QUOTA_OVERRIDE \\?= (\\w+)", mk, re.M).group(1)
slo = int(re.search(r'"api_latency" \\{.*?threshold_value = (\\d+)', alerts, re.S).group(1)) / 1000
slots = conc * most
print(f"documind-api: {conc} at a time x {most} instances = {slots} claims in flight; {least} kept warm; cut at {timeout} s")
print(f"Vector Search: {' and '.join(f'{k} {v}' for k, v in replicas)} replica: one node answers every claim's search")
print(f"quota.tf: {rpm} generate_content requests a minute for the whole project; GEMINI_QUOTA_OVERRIDE ?= {switch}")
print(f"{slots} slots turn over {slots * 60 / slo:,.0f} claims a minute at the {slo:g} s SLO and {slots * 60 / timeout:,.0f} at the {timeout} s cut;"
      f" they bind before the quota once a claim takes {slots * 60 / rpm:g} s")
for q in (1_000, 10_000, 100_000, 1_000_000):
    avg = q / (730 * 60)                                              # claims a minute; 730 hours, the price pages' month
    print(f"{q:>9,} a month: {avg:6.3f} a minute, one every {60 / avg:7,.1f} s | the quota binds at a busiest minute"
          f" {rpm / avg:>8,.1f} x the average; the slots, at {timeout} s a claim, at {slots * 60 / timeout / avg:>8,.1f} x")''',
    "evals": '''import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["evals"]
from run_eval import THRESHOLDS, load_golden, load_required
golden, required = load_golden(), set(load_required())
print(f"what blocks a release: {len(THRESHOLDS)} thresholds and {len(required)} required rows over {len(golden)} rows, scored by code")
never = [r for r in golden if r.get("must_not_contain")]
print(f"must_not_contain on {len(never)} rows: " + ", ".join(f"{sum(r['shape'] == s for r in never)} {s}" for s in sorted({r['shape'] for r in never})))
for r in never:
    if r["shape"] != "isolation":
        print(f"  {r['id']} ({r['shape']}): {r['must_not_contain']} lives only in a revision under evals/demo; a version the ledger failed to retire can say it, so it can fail")
iso = [r for r in never if r["shape"] == "isolation"]
print(f"  the {len(iso)} isolation rows: the retriever filters by tenant before the generator reads, so they fail only on an invented figure")
print(f"  what replaced them: isolation_403_rate at {THRESHOLDS['isolation_403_rate']:.2f}, asked by an account on no tenant's roster")''',
}
SUBST_CELLS = {"PRICE_DATE": PRICE_DATE, "STORE_PY": f"{STORE_USD:.6f}", "EMBED_PY": f"{EMBED_USD_1K:.6f}", "RANK_PY": f"{RANK_USD_1K:.2f}",
               "JIN_PY": f"{JUDGE_IN:.2f}", "JOUT_PY": f"{JUDGE_OUT:.2f}", "QUERY_MAX": str(QUERY_MAX), "JUDGED_PY": f"{JUDGED:.2f}",
               "FLOOR_SMALL_PY": str(FLOOR["lane"]["small"]), "FLOOR_MEDIUM_PY": str(FLOOR["lane"]["medium"])}
assert [float(SUBST_CELLS[k]) for k in ("STORE_PY", "EMBED_PY", "RANK_PY", "JIN_PY", "JOUT_PY", "JUDGED_PY")] == [
    STORE_USD, EMBED_USD_1K, RANK_USD_1K, JUDGE_IN, JUDGE_OUT, JUDGED]
for k, v in list(CELLS.items()):
    for name, val in SUBST_CELLS.items():
        v = v.replace(f"%%{name}%%", val)
    assert "%%" not in v, (k, re.findall(r"%%\w+%%", v))
    CELLS[k] = v
RUN_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}


def run_python(code: str) -> str:
    """One cell, run in deploy/ as the learner runs it in $DEMO_ROOT: python - <<'PY' ... PY."""
    r = subprocess.run([sys.executable, "-"], input=code, cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=RUN_ENV)
    assert r.returncode == 0, r.stderr[-1200:]
    return r.stdout.rstrip("\n")


OUT = {k: run_python(v) for k, v in CELLS.items()}
gate = subprocess.run([sys.executable, "evals/run_eval.py"], cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=RUN_ENV)
assert gate.returncode == 0, gate.stdout[-800:] + gate.stderr[-800:]
OUT["evals"] = gate.stdout.rstrip("\n") + "\n" + OUT["evals"]

# every cell's output, held against the numbers the page states
assert "the sentence as written         15 words | in the passage True  | 25 words at most True  | quote_holds True" in OUT["quotes"], OUT["quotes"]
assert OUT["quotes"].count("quote_holds True") == 2 and OUT["quotes"].count("quote_holds False") == 4
for q in SCALES:
    assert f"{q:>7,} claims a month: a cached corpus is cheaper below {CACHE_MAX[q]:>6,.0f} tokens" in OUT["options"], OUT["options"]
for t, n in CORPUS.items():
    assert f"{t:7} {n:>7,} tokens: Rs {CORPUS_STORE_INR[t]:>6,.0f} a month" in OUT["options"]
assert f"a judge on every claim: Rs {JUDGE_ALL_INR:.2f} a claim" in OUT["options"]
for name in UNDECLARED:
    assert f"quota.tf names {name:17} declared by nothing" in OUT["alerts"]
assert OUT["alerts"].endswith("rows it never counts: passages, desk_gate"), OUT["alerts"][-200:]
for (q, s), m in COST.items():
    assert (f"{q:>7,} claims, {s.upper():6}: model Rs {inr(m['model'])} + retrieval Rs {inr(m['ret'])} + judge Rs {inr(m['judge'])}"
            f" + floor Rs {inr(m['floor'])} = Rs {inr(m['total'])} (${m['total'] / USD_INR:,.0f}), Rs {m['per']:.2f} a claim") in OUT["cost"], (q, s, OUT["cost"])
assert f"{SLOTS} claims in flight" in OUT["limits"] and f"once a claim takes {CROSS_S:g} s" in OUT["limits"]
assert f"{1_000_000:>9,} a month: {PER_MIN[1_000_000]:6.3f} a minute" in OUT["limits"] and f"{QUOTA_X[1_000_000]:>8,.1f} x the average" in OUT["limits"]
assert "The golden set is sound." in OUT["evals"] and f"must_not_contain on {len(NEVER)} rows: {len(ISO)} isolation, {len(VERSION_ROWS)} version" in OUT["evals"]
assert f"{len(THRESHOLDS)} thresholds and {len(REQUIRED)} required rows over {len(GOLDEN)} rows" in OUT["evals"]

# ================================================================== the one live output: make usage, recorded once
USAGE = pb.recorded(LESSON, "usage_tokens.txt")
MEASURED = None
if pb.data(LESSON, "usage_tokens.txt").exists():
    rows = [ln.split() for ln in USAGE.splitlines()]
    hit = [p for p in rows if len(p) >= 9 and p[0] == GEN_MODEL and p[1] == "vertex" and p[2].isdigit()]
    assert len(hit) == 1 and int(hit[0][2]) > 0, "data/usage_tokens.txt: no gemini-3.6-flash / vertex row in make usage's by-model table"
    n_ans, t_in, t_out, p95 = int(hit[0][2]), int(hit[0][3]), int(hit[0][4]), int(hit[0][7])
    MEASURED = {"answers": n_ans, "in": t_in / n_ans, "out": t_out / n_ans, "p95": p95}

# ================================================================== the board: five fates of a claim, six stations
QUOTE_OK = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
QUOTE_BAD = QUOTE_OK.replace("60 days", "90 days")
assert QUOTE_BAD in src("evals/demo/hr_policy_2026_v2.md").replace("\n", " ")
RF01 = next(r for r in GOLDEN if r["id"] == "rf-01")
assert RF01["question"] == "What is ACME's sabbatical policy?" and not RF01["answerable"] and RF01["tenant"] == "acme"
assert not any("sabbatical" in text.lower() for text in load_corpus()["acme"].values())    # the files really are silent
RET_RS, GEN_RS, EMBED_RS, JUDGE_RS = RET_USD * USD_INR, MODEL_USD * USD_INR, EMBED_USD * USD_INR, JUDGE_USD * USD_INR
rs2 = lambda x: f"Rs {x:.2f}"  # noqa: E731
STATIONS = [("door", "1 &middot; The door", "services/rag-api/desk_door.py"),
            ("passages", "2 &middot; The passages", "POST /v1/passages, main.py"),
            ("generator", "3 &middot; The generator", "generator.py, ModelDraft"),
            ("quote", "4 &middot; The quote check", "quote_holds(), evals/make_trainset.py"),
            ("judge", "5 &middot; The judge, beside the path", "evals/judge.py"),
            ("verdict", "6 &middot; The verdict", "the fact desk's own row")]
PASSAGES_TXT = (f"One embedding of the claim, up to {POOL} candidates from the index, the Ranking API's top {TOP_K}, each with its "
                "full text. Its row says event passages and cost 0.")
DOOR_PASS = f"None of the law's {word(N_CLASSES)} classes: the body goes through as it was sent."
JUDGE_LATER = ("One standing verdict in twenty is read later, for groundedness and fulfilment. A low score sends the verdict "
               "to a person; it never changes it.")
CASES = {
    "stands": {"label": "Supported: an E3 serves 60 days' notice", "st": {
        "door": ("run", DOOR_PASS, "Rs 0"),
        "passages": ("run", PASSAGES_TXT, f"{rs2(RET_RS)} at most"),
        "generator": ("run", "answerable true, and [1] cites NP-03 with the sentence the answer rests on.", f"{rs2(GEN_RS)} at the ceiling"),
        "quote": ("run", f"\"{QUOTE_OK}\" is in NP-03, in {len(QUOTE_OK.split())} words: it holds.", "Rs 0"),
        "judge": ("side", JUDGE_LATER, f"{rs2(JUDGE_RS)} when it reads one"),
        "verdict": ("run", "Stands: the answer, NP-03's sentence, and hr_policy_2026.md, the source it cites.", "the row: stands")},
        "out": f"Stands, with its clause: {rs2(RET_RS + GEN_RS)} at the ceiling, and the check on its quote cost nothing."},
    "silent": {"label": "Silent: ACME's sabbatical policy", "st": {
        "door": ("run", DOOR_PASS, "Rs 0"),
        "passages": ("run", PASSAGES_TXT + " The nearest passages come back, and no document of acme's mentions a sabbatical.",
                     f"{rs2(RET_RS)} at most"),
        "generator": ("run", "Rule 3: the passages do not contain it, so answerable is false and there is no citation.", f"{rs2(GEN_RS)} at the ceiling"),
        "quote": ("skip", "No citation, so nothing to check.", "Rs 0"),
        "judge": ("skip", "Not sampled: a refusal has no passage to be grounded in.", "Rs 0"),
        "verdict": ("run", "Not in our files: the model read them and declined. Golden row rf-01 asks exactly this.", "the row: refused")},
        "out": f"Not in our files, said by the model after reading the passages: {rs2(RET_RS + GEN_RS)} at the ceiling."},
    "empty": {"label": "Empty pool: a filter nothing matches", "st": {
        "door": ("run", DOOR_PASS, "Rs 0"),
        "passages": ("held", "The filter matches no row: passages [] and answerable false. An empty pool skips the ranker.",
                     f"Rs {EMBED_RS:.4f}, the embedding"),
        "generator": ("skip", "Not called: there is nothing to read.", "Rs 0"),
        "quote": ("skip", "Nothing to check.", "Rs 0"),
        "judge": ("skip", "Not sampled.", "Rs 0"),
        "verdict": ("run", "Not in our files, without a generation call.", "the row: refused")},
        "out": f"Not in our files, for Rs {EMBED_RS:.4f}: the embedding was the whole bill."},
    "misquote": {"label": "Misquoted: revision 2's figure", "st": {
        "door": ("run", DOOR_PASS, "Rs 0"),
        "passages": ("run", PASSAGES_TXT, f"{rs2(RET_RS)} at most"),
        "generator": ("run", "answerable true, but the quote carries revision 2's figure, 90 days, which the current NP-03 does not say.",
                      f"{rs2(GEN_RS)} at the ceiling"),
        "quote": ("held", f"\"{QUOTE_BAD}\" is not in NP-03: it does not hold.", "Rs 0"),
        "judge": ("skip", "Not needed: a person reads every held verdict.", "Rs 0"),
        "verdict": ("held", "Held for a person, with the quote that failed and the passage it was held against.", "the row: held")},
        "out": f"Held for a person: the model was paid ({rs2(RET_RS + GEN_RS)} at the ceiling), and the free check stopped the verdict."},
    "door": {"label": f"Handed over: one of the door's {word(N_CLASSES)} classes", "st": {
        "door": ("stop", "A hit: the door answers with the law's fixed reply, model none, backend desk_gate, and logs event desk_gate.", "Rs 0"),
        "passages": ("skip", "Never reached: nothing is retrieved.", "Rs 0"),
        "generator": ("skip", "Never reached.", "Rs 0"),
        "quote": ("skip", "Nothing to check.", "Rs 0"),
        "judge": ("skip", "Not sampled.", "Rs 0"),
        "verdict": ("stop", "Handed to a person: the desk shows the door's reply as it came.", "the row: handed over")},
        "out": "Handed to a person by the door, for Rs 0: the claim never reached retrieval or a model."},
}
BOARD = {"stations": [k for k, _, _ in STATIONS], "cases": {k: {"st": c["st"], "out": c["out"]} for k, c in CASES.items()}}


def board_station(key: str, label: str, where: str, case: dict) -> str:
    state, text, cost = case["st"][key]
    return (f'<li class="fd-st {state}" data-st="{key}"><b>{label}</b><span class="fd-f">{esc(where)}</span>'
            f'<span class="fd-t">{esc(text)}</span><span class="fd-c">{esc(cost)}</span></li>')


BOARD_OPTIONS = "".join(f'<option value="{k}"{" selected" if k == "stands" else ""}>{esc(c["label"])}</option>' for k, c in CASES.items())
BOARD_STATIONS = "".join(board_station(k, lab, where, CASES["stands"]) for k, lab, where in STATIONS)

# ================================================================== the cost tables: static (both shards) and the calculator's
HEADS = ["Claims a month", "Model", "Retrieval", "Judge", "Floor", "Total", "Per claim"]


def cost_row(q: int, m: dict, shard: str | None = None) -> str:
    first = f"{SCALE_WORD[q]} ({q:,})" + (f", {shard.upper()}" if shard else "")
    cells = [f"Rs {inr(m['model'])}", f"Rs {inr(m['ret'])}", f"Rs {inr(m['judge'])}", f"Rs {inr(m['floor'])}",
             f"<strong>Rs {inr(m['total'])}</strong> (${m['usd']:,})", f"Rs {m['per']:.2f}"]
    return (f"<tr><td>{first}</td>" + "".join(f'<td data-label="{h}">{c}</td>' for h, c in zip(HEADS[1:], cells)) + "</tr>")


COST_TABLE = "\n".join(cost_row(q, COST[(q, s)], s) for q in SCALES for s in SHARDS)
CALC_ROWS = "\n".join(cost_row(q, COST[(q, "small")]) for q in SCALES)
CALC = {"rIn": R_IN, "rOut": R_OUT, "inr": USD_INR, "ret": RET_USD, "jIn": JUDGE_IN, "jOut": JUDGE_OUT, "metrics": N_METRICS,
        "scales": list(SCALES), "labels": {str(q): f"{SCALE_WORD[q]} ({q:,})" for q in SCALES}, "heads": HEADS,
        "floor": FLOOR, "tokens": {"ceiling": [TIN, TOUT]}}
TOK_OPTIONS = f'<option value="ceiling" selected>ceiling: {TIN:,} in, {TOUT:,} out</option>'
if MEASURED:
    CALC["tokens"]["measured"] = [round(MEASURED["in"]), round(MEASURED["out"])]
    TOK_OPTIONS += f'<option value="measured">measured: {round(MEASURED["in"]):,} in, {round(MEASURED["out"]):,} out</option>'
else:
    TOK_OPTIONS += '<option value="measured" disabled>measured: awaiting the run</option>'
CALC_NOTE = (f"The claims cost more than this floor above {BREAK_EVEN['small']:,} claims a month, at these settings: "
             f"Rs {PER_CLAIM_USD * USD_INR:.2f} a claim before the floor.")         # what the script writes for the defaults
if MEASURED:
    m_usd = (MEASURED["in"] * R_IN + MEASURED["out"] * R_OUT) / 1e6
    MEASURED_LINE = (f"On the author's lane, {MEASURED['answers']:,} answers averaged {round(MEASURED['in']):,} tokens in and "
                     f"{round(MEASURED['out']):,} out, p95 {MEASURED['p95']:,} ms: Rs {m_usd * USD_INR:.2f} a claim for the model, "
                     f"against {rs2(GEN_RS)} at the ceiling.")
else:
    MEASURED_LINE = ("The author's measured average goes here once the run below is recorded; until then the ceiling stands "
                     "alone, and the ceiling is the number a cost model may not exceed.")

# ================================================================== the limits table
LIMITS_TABLE = "\n".join([
    f'<tr><td>documind-api in flight</td><td data-label="Declared in"><code>commands/lesson-12.2.sh</code></td>'
    f'<td data-label="Value">{CONC} at a time x {MAXI} instances = {SLOTS}; {MINI} kept warm; cut at {TIMEOUT} s</td>'
    f'<td data-label="What it allows">{TURN_SLO:,} claims a minute at the {SLO_MS // 1000} s SLO; {TURN_CUT} at the {TIMEOUT} s cut</td>'
    f'<td data-label="At 1M a month, it binds when">the busiest minute is {CUT_X[1_000_000]:.1f} times the average, if claims run to the cut</td></tr>',
    f'<tr><td>Gemini requests</td><td data-label="Declared in"><code>terraform/quota.tf</code></td>'
    f'<td data-label="Value">{RPM} a minute for the project, behind <code>GEMINI_QUOTA_OVERRIDE</code> ({QUOTA_SWITCH} by default)</td>'
    f'<td data-label="What it allows">{RPM} generation calls a minute, shared by every caller in the project</td>'
    f'<td data-label="At 1M a month, it binds when">the busiest minute is {QUOTA_X[1_000_000]:.1f} times the average, once it is on</td></tr>',
    f'<tr><td>Vector Search</td><td data-label="Declared in"><code>terraform/vector.tf</code></td>'
    f'<td data-label="Value">{REPLICAS["min"]} replica, min and max: no autoscaling</td>'
    f'<td data-label="What it allows">not declared anywhere in the kit</td>'
    f'<td data-label="At 1M a month, it binds when">unknown until measured: the one ceiling with no number</td></tr>',
    f'<tr><td>A warm instance</td><td data-label="Declared in"><code>commands/lesson-12.2.sh</code></td>'
    f'<td data-label="Value"><code>--min-instances={MINI}</code></td>'
    f'<td data-label="What it allows">nothing idle, and nothing ready</td>'
    f'<td data-label="At 1M a month, it binds when">the other way round: at 1k a month a claim arrives every {GAP_S[1_000] / 60:.1f} minutes on average</td></tr>',
])

# ================================================================== excerpts, verbatim
EXCERPTS = {
    "door_paths": ("services/rag-api/desk_door.py - the door in front of the three routes that take a question; shared/desk_rules.py - its classes",
                   block("services/rag-api/desk_door.py", "PATHS = {", n=1) + "\n...\n"
                   + block("services/rag-api/desk_door.py", '        if surface == "passages":', n=2) + "\n...\n"
                   + block("shared/desk_rules.py", "CLASSES = (", n=1)),
    "passages_route": ("services/rag-api/main.py - /v1/passages: retrieval and rerank, then each passage's full text, and no generation call",
                       block("services/rag-api/main.py", '@app.post("/v1/passages")', n=len(MAIN.split('@app.post("/v1/passages")', 1)[1].splitlines()) + 1)),
    "passages_tool": ("shared/documind_tools.py - retrieve(passages=True): the kit's door for a caller that writes its own answer",
                      block("shared/documind_tools.py", "        passages: True for the passages themselves", n=4) + "\n...\n"
                      + block("shared/documind_tools.py", "PASSAGE_KEYS = (", n=1)),
    "system_rules": ("services/rag-api/generator.py - SYSTEM: answer only from the numbered context, cite, refuse, quote the clause",
                     block("services/rag-api/generator.py", 'SYSTEM = """You are DocuMind', n=8)),
    "model_draft": ("shared/documind_schemas.py - DraftCitation and ModelDraft: what the model is asked for",
                    block("shared/documind_schemas.py", "class DraftCitation(BaseModel):", end="def resolve(")),
    "resolve_quote": ("shared/documind_schemas.py - resolve(): the citation takes the draft's quote as it came",
                      block("shared/documind_schemas.py", "    def cite(n: int, quote: str) -> None:", n=11) + "\n...\n"
                      + block("shared/documind_schemas.py", "    for d in draft.citations:", n=3)),
    "draft_trim": ("services/rag-api/generator.py - _draft(): an over-long quote is trimmed, and the trim ends in three dots",
                   block("services/rag-api/generator.py", "    limit = _quote_limit()", n=4)),
    "quote_holds": ("evals/make_trainset.py - quote_holds(): the check the design borrows, already the kit's own",
                    block("evals/make_trainset.py", "def _flat(s: str) -> str:", end="def is_hinglish(")),
    "judge_role": ("evals/judge.py - the other judge, as its docstring opens and as its last line ends",
                   block("evals/judge.py", "run_eval.py is the gate: nine thresholds", n=1) + "\n...\n"
                   + block("evals/judge.py", '    print("\\n  the gate (run_eval.py) still decides;', n=1)),
    "judge_context": ("evals/judge.py - enrich_context(): why the judge reads the cited passages in full",
                      block("evals/judge.py", "def enrich_context(rows: list[dict], project: str, fetch=None) -> int:", n=5)),
    "cache_floor": ("services/rag-api/cache_manager.py - the floor under an explicit cache; services/rag-api/cost.py - the rate a cached token is read at",
                    block("services/rag-api/cache_manager.py", "MIN_CACHE_TOKENS = 4_096", n=2) + "\n...\n"
                    + block("services/rag-api/cost.py", "    billable_in = max(tokens_in - cached_tokens, 0)", n=4)),
    "tenancy_rule": ("shared/tenancy.py - where a tenant's text may be held: in or any, and absent means in",
                     block("shared/tenancy.py", "DATA_REGIONS = (", end="def policy_for(") + "\n...\n"
                     + block("shared/tenancy.py", "def permits(policy: str, region: str | None) -> bool:", end="RETRIEVAL_BACKENDS = (")),
    "roster_policies": ("commands/lane.py - the demo's policies, which make roster writes",
                        block("commands/lane.py", "    demo's data-region policies (13 September 2026, evening)", n=2) + "\n...\n"
                        + block("commands/lane.py", "    policies = [", n=1)),
    "gchat_residency": ("commands/desk_ops.py - the kit's own answer when a door would put an in tenant's text in another service",
                        block("commands/desk_ops.py", '    if tenancy.policy_of(_settings(db, tenant)) == "in" and not confirm_residency:', n=4)),
    "unanswerable_metric": ("terraform/alerts.tf - what the unanswerable rate counts, and what it does not",
                            block("terraform/alerts.tf", 'resource "google_logging_metric" "queries" {', n=8)),
    "stream_verdict": ("services/rag-api/main.py - the stream's verdict: answerable unless the pool was empty",
                       block("services/rag-api/main.py", "        # The row's verdict: a refusal for the empty pool;", n=3)),
    "quota_alerts": ("terraform/quota.tf - five alerts named, two declared",
                     block("terraform/quota.tf", "# The alerts that say something is wrong with the SYSTEM")),
    "api_latency": ("terraform/alerts.tf - the latency policy: the only alert on documind-api's requests themselves",
                    block("terraform/alerts.tf", "# Latency: documind-api's p95 over 3 s for 5 minutes.", end="  notification_channels = local.alert_channel_ids")),
    "budget_fn": ("services/rag-api/generator.py - _budget(): the fixed prompt counted, the chunks get the rest of max_context_tokens",
                  block("services/rag-api/generator.py", '    fixed = f"{SYSTEM}{DATED_RULE}', n=2)),
    "config_tokens": ("services/rag-api/config.py - the input total and the output reserve",
                      block("services/rag-api/config.py", "    max_context_tokens: int = 8000", n=5)),
    "prices": ("shared/prices.py - the kit's rates and its rupee rate",
               block("shared/prices.py", "USD_INR = 85", n=1) + "\n...\n" + block("shared/prices.py", "PRICES = {", n=3)),
    "api_deploy": ("commands/lesson-12.2.sh - documind-api's deploy: forty at a time, twenty instances, none kept warm",
                   block("commands/lesson-12.2.sh", "gcloud run deploy documind-api \\", n=9)),
    "vector_replica": ("terraform/vector.tf - the deployed index: one replica, and no more",
                       block("terraform/vector.tf", "  # One compatible replica.", end="# These two outputs are the whole contract")),
    "quota_override": ("terraform/quota.tf - the ceiling under the budget, off by default",
                       block("terraform/quota.tf", "# A consumer quota override", end="# The alerts that say something is wrong")),
    "thresholds": ("evals/run_eval.py - what a green run has to clear",
                   block("evals/run_eval.py", "THRESHOLDS = {", end="STAGES = (")),
    "isolation_doc": ("evals/run_eval.py - check_isolation(): why must_not_contain is not the isolation gate",
                      block("evals/run_eval.py", "def check_isolation(api_url, golden, token, outsider_token=None)", n=14)),
    "quote_support": ("evals/run_eval.py - today's quote support: the tenant's whole corpus, reported and not judged",
                      block("evals/run_eval.py", '        quote = re.sub(r"\\s+", " ", c.get("quote", "")).strip().lower()', n=3) + "\n...\n"
                      + block("evals/run_eval.py", "    if quote_rows:", n=3)),
}
assert "return await _json(send, 200, {\"passages\": [], \"answer\": text" in EXCERPTS["door_paths"][1]
assert EXCERPTS["passages_route"][1].rstrip().endswith('return {"passages": out, "answerable": bool(out), "usage": usage}')
assert "5. A quote is the clause that answers - at most twenty-five words, never a whole section." in EXCERPTS["system_rules"][1]
assert EXCERPTS["system_rules"][1].rstrip().endswith('"""')
assert '            quote=(quote or c.get("text", ""))[:500],\n...\n' in EXCERPTS["resolve_quote"][1]
assert EXCERPTS["resolve_quote"][1].rstrip().endswith('            cite(d.source, d.quote)')
assert EXCERPTS["quote_holds"][1].rstrip().endswith("return bool(quote.strip()) and len(quote.split()) <= 25 and _flat(quote) in _flat(passage)")
assert "(F39, 10 September)" in EXCERPTS["judge_context"][1]
assert EXCERPTS["tenancy_rule"][1].rstrip().endswith('return str(region or "").strip().lower().startswith(INDIA_REGION_PREFIXES)')
assert 'policies = [("acme", "any"), ("zeta", "any"), ("globex", "in")]' in EXCERPTS["roster_policies"][1]
assert "CONFIRM_RESIDENCY=1 once the company has agreed to that" in EXCERPTS["gchat_residency"][1]
assert '(jsonPayload.event="query" OR jsonPayload.event="stream")' in EXCERPTS["unanswerable_metric"][1]
assert EXCERPTS["unanswerable_metric"][1].rstrip().endswith("EOT")
assert "the other three are declared by nothing yet." in EXCERPTS["quota_alerts"][1] and EXCERPTS["quota_alerts"][1].rstrip().endswith("}")
assert EXCERPTS["api_latency"][1].rstrip().endswith("  }") and "threshold_value = 3000" in EXCERPTS["api_latency"][1]
assert "--concurrency=40 --timeout=120" in EXCERPTS["api_deploy"][1] and "--min-instances=0 --max-instances=20" in EXCERPTS["api_deploy"][1]
assert "min_replica_count = 1" in EXCERPTS["vector_replica"][1] and "max_replica_count = 1" in EXCERPTS["vector_replica"][1]
assert 'override_value = "600"' in EXCERPTS["quota_override"][1]
assert "That is a hallucination lottery" in EXCERPTS["isolation_doc"][1] and EXCERPTS["isolation_doc"][1].rstrip().endswith('"""')
assert '"isolation_403_rate": 1.00,' in EXCERPTS["thresholds"][1]
fill = filler(EXCERPTS, window)

# ================================================================== the cells' windows


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + esc(code) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + esc(text.rstrip("\n")) + "</pre></div>\n")


OFFLINE = "run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing)"
BUILT = "(the kit's own output, produced when this page was built; yours should match it line for line)"
heredoc = lambda code: "python - <<'PY'\n" + code + "\nPY"  # noqa: E731
WIN = {
    "CELL_QUOTES": bash_window(OFFLINE, heredoc(CELLS["quotes"])), "OUT_QUOTES": out_window(BUILT, OUT["quotes"]),
    "CELL_OPTIONS": bash_window(OFFLINE, heredoc(CELLS["options"])), "OUT_OPTIONS": out_window(BUILT, OUT["options"]),
    "CELL_ALERTS": bash_window(OFFLINE, heredoc(CELLS["alerts"])), "OUT_ALERTS": out_window(BUILT, OUT["alerts"]),
    "CELL_COST": bash_window(OFFLINE, heredoc(CELLS["cost"])), "OUT_COST": out_window(BUILT, OUT["cost"]),
    "CELL_LIMITS": bash_window(OFFLINE, heredoc(CELLS["limits"])), "OUT_LIMITS": out_window(BUILT, OUT["limits"]),
    "CELL_EVALS": bash_window("run in the operator shell, in $DEMO_ROOT (the offline gate, then a Python cell; Rs 0: no credential, no call)",
                              "python evals/run_eval.py\n" + heredoc(CELLS["evals"])),
    "OUT_EVALS": out_window(BUILT, OUT["evals"]),
    "CELL_USAGE": bash_window("run in the operator shell, in $DEMO_ROOT (Rs 0: one read of the last day's usage rows)",
                              "make usage PROJECT=$PROJECT HOURS=24 | sed -n '/^by model and backend/,/^$/p' | tee /tmp/usage39.txt\n"
                              "awk '$2 == \"vertex\" && $3 > 0 {printf \"%s: %d answers, %.0f tokens in and %.0f out each, p95 %s ms\\n\", "
                              "$1, $3, $4 / $3, $5 / $3, $8}' /tmp/usage39.txt"),
    "OUT_USAGE": out_window("(the author's lane, recorded once; your answers and averages are your own)", USAGE),
    "CELL_READS": bash_window("run in the operator shell, in $DEMO_ROOT (Rs 0: reads only, nothing changed)",
                              "gcloud run services describe documind-api --region \"$REGION\" --project \"$PROJECT\" \\\n"
                              "  --format='yaml(spec.template.spec.timeoutSeconds,spec.template.spec.containerConcurrency,spec.template.metadata.annotations)' \\\n"
                              "  | grep -E 'maxScale|containerConcurrency|timeoutSeconds'\n"
                              "EP=$(terraform -chdir=terraform output -raw vector_index_endpoint)\n"
                              "gcloud ai index-endpoints describe \"$(basename \"$EP\")\" --region=\"$REGION\" --project=\"$PROJECT\" \\\n"
                              "  --format='value(deployedIndexes[0].dedicatedResources.machineSpec.machineType,"
                              "deployedIndexes[0].dedicatedResources.minReplicaCount,deployedIndexes[0].dedicatedResources.maxReplicaCount)'\n"
                              "terraform -chdir=terraform state list | grep -c gemini_rpm"),
    "OUT_READS": out_window(f"(the machine is {sc.SHARDS['small']} on a SMALL shard, {sc.SHARDS['medium']} on MEDIUM; the last line counts "
                            "quota.tf's override in your state)",
                            f"        autoscaling.knative.dev/maxScale: '{MAXI}'\n      containerConcurrency: {CONC}\n      timeoutSeconds: {TIMEOUT}\n"
                            f"{sc.SHARDS['small']}\t{REPLICAS['min']}\t{REPLICAS['max']}\n0"),
}
assert "%s" in WIN["CELL_USAGE"]

# ================================================================== the numbers the parts state
STATS = {
    "N_COMPONENTS": word(N_COMPONENTS), "N_DIMS": word(N_DIMS), "POINTS": str(POINTS), "PASS": str(PASS),
    "N_CLASSES": word(N_CLASSES), "CLASSES": ", ".join(f"<code>{c}</code>" for c in DOOR_CLASSES),
    "TOP_K": str(TOP_K), "POOL": str(POOL), "QUERY_MAX": f"{QUERY_MAX:,}", "DRAFT_QUOTE_MAX": str(DRAFT_QUOTE_MAX),
    "QUOTE_WORDS": str(QUOTE_WORDS), "TOTAL": f"{TOTAL:,}", "ANSWER": f"{ANSWER:,}", "FIXED": str(BUDGET.system),
    "CHUNKS": f"{BUDGET.chunks:,}", "GEN_MODEL": GEN_MODEL, "EMBED_MODEL": EMBED_MODEL, "JUDGE_REGION": JUDGE_REGION,
    "N_METRICS_WORD": word(N_METRICS), "R_IN": f"{R_IN:.2f}", "R_OUT": f"{R_OUT:.2f}", "USD_INR": str(USD_INR),
    "INTRO_IN": f"{INTRO_IN:.2f}", "INTRO_OUT": f"{INTRO_OUT:.2f}",
    "EMBED_USD_1K": f"{EMBED_USD_1K:.6f}", "RANK_USD_1K": f"{RANK_USD_1K:.2f}", "RANK_DOCS": str(RANK_DOCS),
    "JUDGE_IN": f"{JUDGE_IN:.2f}", "JUDGE_OUT": f"{JUDGE_OUT:.2f}", "STORE_PER_M": f"{STORE_USD * 1e6:.2f}",
    "PRICE_DATE": PRICE_DATE, "FLOOR_DATE": FLOOR_DATE,
    "GEN_RS": f"{GEN_RS:.2f}", "RET_RS": f"{RET_RS:.2f}", "EMBED_RS": f"{EMBED_RS:.4f}", "RANK_RS": f"{RANK_USD * USD_INR:.3f}",
    "JUDGE_RS": f"{JUDGE_RS:.2f}",
    "FLOOR_SMALL": inr(FLOOR["lane"]["small"]), "FLOOR_MEDIUM": inr(FLOOR["lane"]["medium"]),
    "API_FLOOR_SMALL": inr(FLOOR["api"]["small"]), "API_FLOOR_MEDIUM": inr(FLOOR["api"]["medium"]),
    "MACHINE_SMALL": sc.SHARDS["small"], "MACHINE_MEDIUM": sc.SHARDS["medium"],
    "BREAK_SMALL": f"{BREAK_EVEN['small']:,}", "BREAK_MEDIUM": f"{BREAK_EVEN['medium']:,}",
    "TOTAL_100K_SMALL": inr(COST[(100_000, "small")]["total"]), "MODEL_100K": inr(COST[(100_000, "small")]["model"]),
    "PER_1K_SMALL": f"{COST[(1_000, 'small')]['per']:.2f}",
    "FLOOR_SHARE_1K": str(round(100 * FLOOR["lane"]["small"] / COST[(1_000, "small")]["total"])),
    "FLOOR_SHARE_100K": str(round(100 * FLOOR["lane"]["small"] / COST[(100_000, "small")]["total"])),
    "COST_TABLE": COST_TABLE, "CALC_ROWS": CALC_ROWS, "TOK_OPTIONS": TOK_OPTIONS, "CALC_NOTE": esc(CALC_NOTE),
    "MEASURED_LINE": esc(MEASURED_LINE), "BOARD_OPTIONS": BOARD_OPTIONS, "BOARD_STATIONS": BOARD_STATIONS,
    "BOARD_OUT": esc(CASES["stands"]["out"]),
    "CACHE_1K": f"{r0(CACHE_MAX[1_000]):,}", "CACHE_10K": f"{r0(CACHE_MAX[10_000]):,}", "CACHE_100K": f"{r0(CACHE_MAX[100_000]):,}",
    "MIN_CACHE": f"{MIN_CACHE:,}",
    "ACME_TOKENS": f"{CORPUS['acme']:,}", "ZETA_TOKENS": f"{CORPUS['zeta']:,}", "GLOBEX_TOKENS": f"{CORPUS['globex']:,}",
    "ACME_STORE": inr(r0(CORPUS_STORE_INR["acme"])), "ACME_READ": f"{CORPUS_READ_INR['acme']:.2f}",
    "ACME_X": f"{CORPUS['acme'] / CACHE_MAX[100_000]:.1f}", "GLOBEX_CROSS": f"{r0(GLOBEX_CROSS):,}", "PACK_GLOBEX": str(PACKS["globex"]),
    "JUDGE_ALL_100K": inr(r0(JUDGE_ALL_INR * 100_000)), "JUDGE_20TH_100K": inr(r0(JUDGE_ALL_INR * 100_000 * JUDGED)),
    "CONC": str(CONC), "MAXI": str(MAXI), "TIMEOUT": str(TIMEOUT), "SLOTS": str(SLOTS),
    "REPLICA": REPLICAS["min"], "RPM": str(RPM), "SLO_S": str(SLO_MS // 1000),
    "SLO_MIN": str(SLO_FOR // 60), "TURN_SLO": f"{TURN_SLO:,}", "TURN_CUT": str(TURN_CUT), "CROSS_S": str(CROSS_S),
    "PER_MIN_1M": f"{PER_MIN[1_000_000]:.1f}", "QUOTA_X_1M": f"{QUOTA_X[1_000_000]:.1f}", "CUT_X_1M": f"{CUT_X[1_000_000]:.1f}",
    "GAP_1K_MIN": f"{GAP_S[1_000] / 60:.1f}", "GAP_100K_S": f"{GAP_S[100_000]:.0f}",
    "UNANS_PCT": str(round(UNANS * 100)), "UNANS_MIN": str(UNANS_FOR // 60), "WINDOW_1K": f"{WINDOW[1_000]:.1f}",
    "WINDOW_10K": f"{WINDOW[10_000]:.1f}", "WINDOW_100K": f"{WINDOW[100_000]:.0f}", "N_NAMED": word(len(NAMED)),
    "UNDECLARED": ", ".join(f"<code>{n}</code>" for n in UNDECLARED[:-1]) + f" and <code>{UNDECLARED[-1]}</code>",
    "LIMITS_TABLE": LIMITS_TABLE,
    "N_GOLDEN": str(len(GOLDEN)), "N_ANSWERABLE": str(N_ANSWERABLE), "N_THRESHOLDS": str(len(THRESHOLDS)),
    "N_REQUIRED": str(len(REQUIRED)), "N_NEVER": str(len(NEVER)), "N_ISO": str(len(ISO)),
    "POLICY_ANY": " and ".join(t for t, r in POLICIES if r == "any"), "POLICY_IN": " and ".join(t for t, r in POLICIES if r == "in"),
    **WIN,
}


def subst(text: str) -> str:
    for k, v in STATS.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ================================================================== the widgets' script: the board's cases and the cost model
JS = """<script>
(function(){
  'use strict';
  var B = __BOARD__, C = __CALC__;
  function $(id){ return document.getElementById(id); }
  function inr(x){ var s = String(Math.round(x)), head = s.slice(0, -3), tail = s.slice(-3);
    while (head.length > 2) { tail = head.slice(-2) + ',' + tail; head = head.slice(0, -2); }
    return head ? head + ',' + tail : tail; }
  var sel = $('fd-case'), path = $('fd-path'), out = $('fd-out');
  if (sel && path && out) {
    var draw = function(){
      var c = B.cases[sel.value]; if (!c) return;
      B.stations.forEach(function(k){
        var li = path.querySelector('[data-st="' + k + '"]'); if (!li) return;
        var s = c.st[k];
        li.className = 'fd-st ' + s[0];
        li.querySelector('.fd-t').textContent = s[1];
        li.querySelector('.fd-c').textContent = s[2];
      });
      out.textContent = c.out;
    };
    sel.addEventListener('change', draw);
    draw();
  }
  var tok = $('fc-tok'), shard = $('fc-shard'), floorSel = $('fc-floor'), judgeSel = $('fc-judge'), body = $('fc-body'), note = $('fc-note');
  if (tok && shard && floorSel && judgeSel && body && note) {
    var calc = function(){
      var t = C.tokens[tok.value] || C.tokens.ceiling, fl = C.floor[floorSel.value][shard.value], share = parseFloat(judgeSel.value);
      var model = (t[0] * C.rIn + t[1] * C.rOut) / 1e6, judge = share * C.metrics * ((t[0] + t[1]) * C.jIn + t[1] * C.jOut) / 1e6;
      while (body.firstChild) body.removeChild(body.firstChild);
      C.scales.forEach(function(q){
        var m = Math.round(q * model * C.inr), r = Math.round(q * C.ret * C.inr), j = Math.round(q * judge * C.inr), total = m + r + j + fl;
        var cells = [C.labels[q], 'Rs ' + inr(m), 'Rs ' + inr(r), 'Rs ' + inr(j), 'Rs ' + inr(fl),
                     'Rs ' + inr(total) + ' ($' + Math.round(total / C.inr).toLocaleString('en-US') + ')', 'Rs ' + (total / q).toFixed(2)];
        var tr = document.createElement('tr');
        cells.forEach(function(v, i){ var cell = document.createElement('td'); if (i) cell.setAttribute('data-label', C.heads[i]);
          cell.textContent = v; tr.appendChild(cell); });
        body.appendChild(tr);
      });
      var per = (model + C.ret + judge) * C.inr;
      note.textContent = 'The claims cost more than this floor above ' + Math.round(fl / per).toLocaleString('en-US') + ' claims a month, at these settings: Rs ' + per.toFixed(2) + ' a claim before the floor.';
    };
    [tok, shard, floorSel, judgeSel].forEach(function(el){ el.addEventListener('change', calc); });
    calc();
  }
})();
</script>
""".replace("__BOARD__", json.dumps(BOARD, ensure_ascii=False, separators=(",", ":"))).replace(
    "__CALC__", json.dumps(CALC, ensure_ascii=False, separators=(",", ":")))

body = "".join([
    fill(subst(pb.part(LESSON, "a"))),
    setup,
    fill(subst(pb.part(LESSON, "b"))),
    fill(subst(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: a claim at the ceiling {TIN} in, {TOUT} out = Rs {GEN_RS:.2f} for {GEN_MODEL}, retrieval Rs {RET_RS:.2f}, judge Rs {JUDGE_RS:.2f}"
      f" when read | 1k / 10k / 100k on SMALL: Rs {', '.join(inr(COST[(q, 'small')]['total']) for q in SCALES)}"
      f" | floor {inr(FLOOR['lane']['small'])} / {inr(FLOOR['lane']['medium'])} | cache wins below {r0(CACHE_MAX[100_000]):,} tokens at 100k"
      f" | {SLOTS} slots, {REPLICAS['min']} replica, {RPM} a minute ({QUOTA_SWITCH}) | {len(NEVER)} must_not_contain rows, {len(ISO)} vacuous"
      f" | measured: {'yes' if MEASURED else 'awaiting'}")
