"""Build lesson 3.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

See run-to-run variance and thinking levels in the same prompt. The prompt bench (evals/prompt_bench.py, make bench)
reads one golden row's pool once from /v1/passages and asks the kit's own generate() the row's question again and
again on it: five runs at thinking level LOW and five at HIGH, then five with a temperature of 2.0 beside five
without. Every answer is judged by run_eval.row_verdict(), the eval gate's own rule, and priced from shared/prices.py.

The row is jn-03, not lk-06 (the example in prompt_bench.py's docstring and mk/generation.mk): B.5 already asked lk-06
five times on a bare prompt, and jn-03 joins two clauses and applies a cap (50 days of leave, encashed only up to 45),
so its two figures give the verdict room to move and the thinking level something to do. ROW_ID names it, the cells
carry it as a literal (asserted below), and the prose is written for it: another row means new prose.

Offline, at build time, with no network and no credential (the children run with Google's variables unset and
fresh profile folders):
  - the kit's own tests of the bench, as step 5's first cell runs them;
  - step 5's second cell: prompt_bench.main() over services/rag-api/generator.py itself, imported as make bench
    imports it, with a scripted model behind generator._client and /v1/passages stood in; its --report twin is the
    test recording that exercises the recorded paths below on every build;
  - the Level 0 widget: run_eval's normalise(), contains() and the text half of row_verdict(), ported to JS and held
    equal in node to the kit on every illustration, chip and probe;
  - the REST, report and usage cells, run against stand-ins (patched gcloud and urlopen) to prove they run and print
    the shapes the recorded files are checked against;
  - jn-03's prompt size on the Rs 0 lane's pool (evals/decide.py's LocalLane), which prices the runs in RUN_LIST.md.
Live, from the author's runs (pb.recorded, RUN_LIST.md): rest_five.txt, bench_levels.txt and .json,
bench_temperature.txt and .json, usage_rows.txt. Every figure the prose gives for Gemini is computed from those files.

    python pagekit/build.py 3.1            (the 3.12 sys venv: rag-api's pins import generator.py; about half a minute)
    CELLS_ONLY=1 python pagekit/build.py 3.1    prints the cells the run list carries, and stops
"""
import ast
import html
import importlib.util
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True                         # the kit modules imported below leave no __pycache__ in deploy/
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402

LESSON, ROW_ID = "3.1", "jn-03"
title = ("<title>Lesson 3.1 See run-to-run variance and thinking levels in the same prompt - five runs of one golden "
         "row at LOW and HIGH, judged by the gate's rule | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the variance bench: one golden row's answers, judged by the gate's text rule */
.vb-src{font-size:var(--small-size);color:var(--slate);margin:0 0 10px;}
.vb-try{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 12px;margin:0 0 12px;min-width:0;}
.vb-l{display:flex;flex-direction:column;gap:4px;font-size:var(--small-size);color:var(--navy);min-width:0;}
.vb-l input,.vb-a textarea{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:#fff;color:var(--navy);min-height:44px;width:100%;max-width:100%;box-sizing:border-box;}
.vb-a textarea{font-family:var(--mono);line-height:1.4;min-height:84px;resize:vertical;}
.vb-chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0;}
.vb-chips button,.vb-reset{font:inherit;font-size:var(--small-size);padding:4px 12px;border:1px solid var(--border);border-radius:16px;background:var(--teal-light);color:var(--navy);cursor:pointer;min-height:max(36px,var(--touch));}
.vb-chips button:active,.vb-reset:active{transform:scale(.97);}
.vb-out,.vb-v,.vb-n{font-family:var(--mono);font-size:12.5px;line-height:1.6;color:var(--slate);overflow-wrap:anywhere;}
.vb-out .ok,.vb-v .ok{color:var(--teal-dark);font-weight:700;}
.vb-out .no,.vb-v .no{color:#b91c1c;font-weight:700;}
.vb-sets{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:12px;}
.vb-set{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 12px;min-width:0;}
.vb-h{font-size:var(--small-size);font-weight:700;color:var(--navy);margin:0 0 8px;}
.vb-a{margin:0 0 10px;}
.vb-err{font-family:var(--mono);font-size:12.5px;color:#b91c1c;overflow-wrap:anywhere;}
.vb-n{color:var(--navy);border-top:1px solid var(--border);padding-top:8px;margin:4px 0 8px;}
"""

setup = setup_section()

# ------------------------------------------------------------------ the kit, read and imported (nothing is called)
PB_REL, RE_REL, GEN_REL, MAIN_REL, CHAT_REL, MK_REL, CFG_REL = (
    "evals/prompt_bench.py", "evals/run_eval.py", "services/rag-api/generator.py", "services/rag-api/main.py",
    "services/frontend/chat.py", "mk/generation.mk", "services/rag-api/config.py")
sys.path[:0] = [str(KIT), str(KIT / "evals"), str(KIT / "services" / "rag-api")]
_spec = importlib.util.spec_from_file_location("prompt_bench_lesson_31", KIT / PB_REL)
bench = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bench)
run_eval = bench.run_eval
from context_budget import TokenBudget, estimate_tokens, pack_chunks  # noqa: E402
from google.genai import types as genai_types  # noqa: E402
from route_eval import rate  # noqa: E402
from shared import prices  # noqa: E402

prices.PROFILE = "gcp"            # list prices, whatever DOCUMIND_PROFILE the build's own shell carries

GEN = (KIT / GEN_REL).read_text(encoding="utf-8")
CFG = (KIT / CFG_REL).read_text(encoding="utf-8")
CHAT = (KIT / CHAT_REL).read_text(encoding="utf-8")
MAIN = (KIT / MAIN_REL).read_text(encoding="utf-8")
MODEL = re.search(r'^    generator_model: str = "([^"]+)"$', CFG, re.M).group(1)
CAP = int(re.search(r"^    max_answer_tokens: int = (\d+)$", CFG, re.M).group(1))
MAX_CTX = int(re.search(r"^    max_context_tokens: int = (\d+)$", CFG, re.M).group(1))
PV = (re.search(r'^    prompt_id: str = "([^"]+)"$', CFG, re.M).group(1) + "@"
      + re.search(r'^    prompt_version: str = "([^"]+)"$', CFG, re.M).group(1))
CACHE_DEFAULT = re.search(r'^    semantic_cache: str = Field\("(\w+)", alias="SEMANTIC_CACHE"\)$', CFG, re.M).group(1)
assert MODEL == prices.DEFAULT_MODEL == "gemini-3.6-flash", MODEL          # what the page says of the knobs is this model's
assert (CAP, MAX_CTX, PV, CACHE_DEFAULT) == (2048, 8000, "documind-rag@v3", "off"), (CAP, MAX_CTX, PV, CACHE_DEFAULT)
assert GEN.count("settings.max_answer_tokens * 3") == 2                    # generate(): one retry with three times the room
CAP3 = CAP * 3
TREE = ast.parse(GEN)
FUNCS = {n.name: ast.get_source_segment(GEN, n) for n in TREE.body if isinstance(n, ast.FunctionDef)}
K = {n.targets[0].id: ast.literal_eval(n.value) for n in TREE.body
     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
LOW_LINE = 'thinking_config=types.ThinkingConfig(thinking_level="LOW")'
assert LOW_LINE in FUNCS["_call"] and LOW_LINE in FUNCS["_vertex_stream"]               # the answer and the stream: LOW
assert "response_schema=ModelDraft" in FUNCS["_call"] and "response_schema" not in FUNCS["_vertex_stream"]
for knob in ("temperature=", "top_p=", "top_k=", "seed="):
    assert knob not in GEN, knob                                          # generator.py sends none of them
assert "NO temperature / top_p / top_k: gemini-3.6-flash ignores all" in FUNCS["_call"]
assert '"tokens_out": n("candidates_token_count") + n("thoughts_token_count")' in FUNCS["_usage"]
assert "billed = _add(billed, " in FUNCS["generate"]                      # a cut-off attempt is billed with its retry
assert 'yield "packed", packed' in FUNCS["generate_stream"]              # the stream cites the packed set first
LEVELS = list(bench.LEVELS)
assert {m.value for m in genai_types.ThinkingLevel} - {"THINKING_LEVEL_UNSPECIFIED"} == set(LEVELS)
assert (bench.KIT_LEVEL, bench.TOP_K, bench.ANSWER_CHARS) == ("LOW", 6, 600)
assert '"top_k": 6}).encode()' in (KIT / RE_REL).read_text(encoding="utf-8")   # ask(): the gate's own top_k, as the bench's
KIT_LEVEL, TOPK = bench.KIT_LEVEL, bench.TOP_K
UI_TOPK = int(re.search(r'json=\{"query": query, "tenant_id": tenant_id, "top_k": (\d+), "brain": "ui"\}', CHAT).group(1))
assert UI_TOPK == 5 and 'f"{RAG_API_URL}/v1/stream"' in CHAT
assert "No temperature or top_p. gemini-3.6-flash ignores temperature, top_p" in CHAT
assert MAIN.count('row = usage_row(') == 3 and '"passages", modality=' in MAIN    # query, stream, passages: one row each
assert "def sources(tenant_id: str" in MAIN and "usage_row" not in MAIN.split("def sources(tenant_id: str", 1)[1].split("@app", 1)[0]
PB_SRC = (KIT / PB_REL).read_text(encoding="utf-8")
assert "record(_fs(), usd)" in MAIN and "import budget" not in PB_SRC and "from budget" not in PB_SRC   # the bench never counts
assert "incremented\nby the cost of every answer it logs (main.py), read by choose_model_for()" in \
    (KIT / "services/rag-api/budget.py").read_text(encoding="utf-8")   # the month's counter: the breaker's reading
MK = (KIT / MK_REL).read_text(encoding="utf-8")
assert "GOOGLE_CLOUD_PROJECT=$(PROJECT)" in MK and "documind-ui-sa@$(PROJECT)" in MK and "$(BENCH_ARGS)" in MK

# the golden row
GOLDEN = run_eval.load_golden()
ROW = next(r for r in GOLDEN if r["id"] == ROW_ID)
assert (ROW["shape"], ROW["tenant"], ROW["answerable"], ROW["must_contain"], ROW["must_retrieve"]) == \
    ("join", "acme", True, ["45", "60"], ["LV-07", "NP-03"]) and not ROW.get("must_not_contain"), ROW
N_GOLDEN, N_JOIN = len(GOLDEN), sum(r["shape"] == "join" for r in GOLDEN)
assert (N_GOLDEN, N_JOIN) == (65, 11)
HANDBOOK = (KIT / "evals/corpus/acme/hr_policy_2026.md").read_text(encoding="utf-8")
assert "capped at 45 days" in HANDBOOK and "serves a notice period of 60 days" in HANDBOOK and "50 days" not in HANDBOOK
MANIFEST_OBJ = run_eval.load_manifest_objects()
CORPUS_TEXT = re.sub(r"\s+", " ", run_eval.haystack(run_eval.load_corpus(), ROW["tenant"]))

# the prompt the kit arm sends is the registered prompt version's text
KIT_SHA = bench.prompt_sha(K["SYSTEM"], K["DATED_RULE"])
REGISTRY = json.loads((KIT / "services/rag-api/prompt_versions.json").read_text(encoding="utf-8"))["versions"]
assert REGISTRY[PV] == KIT_SHA, (REGISTRY, KIT_SHA)
N_RULES = len(bench.rules_of(K["SYSTEM"])[1])
assert N_RULES == 5

# prices: shared/prices.py, as the bench's call_inr() prices a call
USD_IN, USD_OUT = prices.PRICES[MODEL]
USD_INR = prices.USD_INR


def inr(tokens_in: int, tokens_out: int) -> float:
    """shared/prices.py's usd() at its USD_INR: the bench's own arithmetic for one call with no cached tokens."""
    return prices.inr(prices.usd(MODEL, tokens_in, tokens_out))


INR_PER_K_OUT, INR_PER_K_IN = inr(0, 1000), inr(1000, 0)
assert round(INR_PER_K_OUT, 4) == 0.6375 and USD_OUT / USD_IN == 5
assert abs(bench.call_inr({"model": MODEL, "tokens_in": 1000, "visible": 300, "thought": 700}) - inr(1000, 1000)) < 1e-12
W = {5: [rate(k, 5) for k in range(6)]}         # pass k/5 as the bench prints it, for k = 0 to 5
W55_LO = re.search(r"\[([\d.]+%),", W[5][5]).group(1)
assert W55_LO == "56.6%"

# the kit's tests script these thought tokens; step 5's cell uses the same two
TEST_SRC = (KIT / "evals/tests/test_prompt_bench.py").read_text(encoding="utf-8")
THOUGHT_T = ast.literal_eval(re.search(r"^THOUGHT = (\{[^}]*\})", TEST_SRC, re.M).group(1))

# ------------------------------------------------------------------ jn-03's prompt on the Rs 0 lane's pool: the run list's prices
_dspec = importlib.util.spec_from_file_location("decide_lesson_31", KIT / "evals" / "decide.py")
decide = importlib.util.module_from_spec(_dspec)
_dspec.loader.exec_module(decide)


def prompt_tokens(question: str, passages: list) -> int:
    """generate()'s prompt for this pool, counted by estimate_tokens (len // 4): _budget(), pack_chunks(), the prompt line."""
    chunks = bench.chunks_of(passages)
    budget = TokenBudget.fit(MAX_CTX, f"{K['SYSTEM']}{K['DATED_RULE']}\n\nContext:\n\n\nQuestion: {question}", estimate_tokens,
                             answer=CAP)
    context, packed, _ = pack_chunks(chunks, budget.chunks, estimate_tokens)
    dated = K["DATED_RULE"] if any(c.get("effective_from") for c in packed) else ""
    return estimate_tokens(f"{K['SYSTEM']}{dated}\n\nContext:\n{context}\n\nQuestion: {question}")


_lane = decide.LocalLane([ROW["tenant"]], 0.0)
EST = {k: prompt_tokens(ROW["question"], _lane.pool(ROW["question"], ROW["tenant"], k)[0].get("passages") or [])
       for k in (UI_TOPK, TOPK)}
assert 800 < EST[UI_TOPK] < EST[TOPK] < MAX_CTX, EST

# ------------------------------------------------------------------ verbatim kit excerpts
EXCERPTS = {
    "chat_stream": ("services/frontend/chat.py - stream_answer(): the Chat page's request, five passages, /v1/stream",
                    block(CHAT_REL, "def stream_answer(", end="def chat_page(")),
    "chat_knobs": ("services/frontend/chat.py - the sidebar: why there is no temperature slider",
                   block(CHAT_REL, "        # No temperature or top_p. gemini-3.6-flash ignores temperature, top_p", n=3)),
    "call": ("services/rag-api/generator.py - _call(): every answer's one request and its config",
             block(GEN_REL, "def _call(", end="def _exhausted_tier(")),
    "usage": ("services/rag-api/generator.py - _usage(): the thinking is added into tokens_out",
              block(GEN_REL, "def _usage(", end="def _add(")),
    "retry": ("services/rag-api/generator.py - generate(): an answer cut off at the cap, asked once more",
              block(GEN_REL, '    if draft is None and _finish_reason(r) == "MAX_TOKENS":', end="    if draft is None:")),
    "passages": ("services/rag-api/main.py - /v1/passages: the pool, and no model",
                 block(MAIN_REL, '@app.post("/v1/passages")', n=8)),
    "mk_bench": ("mk/generation.mk - make bench", block(MK_REL, "# The prompt bench", end="# The prompt bound to its version")),
    "recorder": ("evals/prompt_bench.py - sent(), usage_of() and the Recorder around generator._client",
                 block(PB_REL, "def sent(config) -> dict:", end="def call_inr(")),
    "call_inr": ("evals/prompt_bench.py - call_inr(): one call at list price", block(PB_REL, "def call_inr(", end="rows and pools")),
    "bench_loop": ("evals/prompt_bench.py - bench(): every row, arm, level and run, interleaved", block(PB_REL, "def bench(", end="the summary")),
    "summarise": ("evals/prompt_bench.py - summarise(): what each column of the table counts",
                  block(PB_REL, "def summarise(", end="def summary_lines(")),
    "golden": ("evals/golden.jsonl - the row this page asks", block("evals/golden.jsonl", f'"id": "{ROW_ID}"', n=1)),
    "row_verdict": ("evals/run_eval.py - row_verdict(): the gate's judgment of one reply", block(RE_REL, "def row_verdict(", end="QUOTE_VERDICTS = (")),
    "figures": ("evals/run_eval.py - normalise() and contains(): a figure on its own boundary", block(RE_REL, "def normalise(", end="live checks")),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["chat_stream"].count('"top_k": 5') == 1 and E["chat_knobs"].count("\n") == 2
assert E["call"].rstrip().endswith("    )") and "thinking_level=\"LOW\"" in E["call"]
assert E["retry"].rstrip().endswith("draft = _draft(r)") and "settings.max_answer_tokens * 3" in E["retry"]
assert E["passages"].rstrip().endswith('is passages [] and answerable False."""')
assert E["mk_bench"].rstrip().endswith("$(PY) evals/prompt_bench.py --api-url $$API $(BENCH_ARGS)")
assert E["recorder"].rstrip().endswith("return r") and "class Recorder:" in E["recorder"]
assert E["call_inr"].rstrip().endswith('call.get("visible", 0) + call.get("thought", 0), call.get("cached", 0)))')
assert E["bench_loop"].rstrip().endswith("return answers") and E["summarise"].rstrip().endswith("return out")
assert E["row_verdict"].rstrip().endswith("return v") and E["figures"].rstrip().endswith('normalise(text)) is not None')
assert json.loads(E["golden"]) == ROW
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the cells: what the page shows, the run list carries and the build runs
T0_SH = 'export T0="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "lesson 3.1 from $T0 (UTC): step 9 reads the usage rows written since then"'

REST_PY = r'''import json, os, re, subprocess, sys, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["evals", "."]
import run_eval
from route_eval import rate
from shared.prices import USD_INR, usd
API, PROJECT = os.environ["API"], os.environ["PROJECT"]
ROW = next(r for r in run_eval.load_golden() if r["id"] == "jn-03")
TOKEN = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                        f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"],
                       capture_output=True, text=True, check=True).stdout.strip()
version = json.load(urllib.request.urlopen(urllib.request.Request(f"{API}/version", headers={"Authorization": f"Bearer {TOKEN}"}),
                                           timeout=30))
print(f"/version: {version['generator_model']} | prompt {version['prompt']} | semantic_cache {version['semantic_cache']}")
current = run_eval.fetch_current_shas(API, ROW["tenant"], TOKEN)          # the ledger's current versions, as the gate reads them
if current is None:
    print("[info] GET /v1/sources was unavailable: the version check is skipped")
manifest = run_eval.load_manifest_objects()
corpus = re.sub(r"\s+", " ", run_eval.haystack(run_eval.load_corpus(), ROW["tenant"]))
said, cited, passed, rupees = [], [], 0, 0.0
for run in range(1, 6):
    status, body, ms = run_eval.ask(API, ROW["question"], ROW["tenant"], "eval@documind.in", TOKEN)   # the gate's own request
    v = run_eval.row_verdict(ROW, status, body, current, manifest, corpus)                               # and its own rule
    if v["outcome"] != "ok":
        print(f"run {run}: {v['outcome']} | {v['why']}")
        continue
    passed += v["pass"]
    said.append(" ".join(body["answer"].split()))
    cited.append(frozenset(c["chunk_id"] for c in body["citations"]))
    rs = usd(body["model"], body["tokens_in"], body["tokens_out"]) * USD_INR       # tokens_out: the answer and the thinking
    rupees += rs
    print(f"run {run}: {'pass' if v['pass'] else 'FAIL'} | tokens {body['tokens_in']} in + {body['tokens_out']} out | "
          f"generate_ms {body['stages'].get('generate_ms')} | cache {body['cache_hit']} | Rs {rs:.4f}"
          + (f" | {v['why']}" if v["why"] else ""))
    for c in body["citations"]:
        print(f"       cites {c['source_uri'].rsplit('/', 1)[-1]}#{c['chunk_id'].rsplit('#', 1)[-1]}: {c['quote'][:60]!r}")
    print(f"       {said[-1][:240]}")
print(f"distinct answers {len(set(said))} of {len(said)} | cite sets {len(set(cited))} of {len(said)} | "
      f"pass {rate(passed, 5)} | Rs {rupees:.4f} for the five")'''

TESTS_SH = "python -m unittest discover -s evals/tests -p test_prompt_bench.py -v"   # no -W: load_corpus closes its files

SCRIPT_PY = r'''import hashlib, json, os, re, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["GOOGLE_CLOUD_PROJECT"] = "documind-ai-YOUR-ID"   # config.py wants a project id; nothing here calls Google
sys.path[:0] = ["evals", "."]
import prompt_bench as pb
from shared import documind_corpus
from types import SimpleNamespace as NS

gen = pb.load_generator()                       # services/rag-api/generator.py, imported as make bench imports it
RAW = open("evals/corpus/acme/hr_policy_2026.md", "rb").read()
SHA, URI = hashlib.sha256(RAW).hexdigest(), "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"
CLAUSES = documind_corpus.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "text": RAW.decode("utf-8"),
                                          "source_uri": URI}, "acme")
POOL = [{"n": n, "chunk_id": f"acme:{SHA}#{i}", "source_uri": URI, "page": CLAUSES[i]["page_start"], "doc_type": "policy",
         "kind": "text", "section": CLAUSES[i]["section"], "text": CLAUSES[i]["text"]} for n, i in enumerate(range(1, 7), 1)]
WORDINGS = [                                    # the script's answers, in turn; {LV} and {NP} become the [Source N] it saw
    "You can encash 45 of your 50 days, the cap on exit, and you serve a notice period of 60 days [{LV}, {NP}].",
    "Encashment is capped at 45 days, so 45 days are paid at basic pay [{LV}]. As a confirmed E3 you serve 60 days' notice [{NP}].",
    "Forty-five days are encashed and the notice period is sixty days [{LV}, {NP}].",
    "You can encash 45 of your 50 days, the cap on exit, and you serve a notice period of 60 days [{LV}, {NP}].",
    "All 50 days of earned leave are encashed at basic pay, and the notice period is 60 days [{LV}, {NP}].",
]
QUOTES = {"LV": ("LV-07", "capped at 45 days"), "NP": ("NP-03", "serves a notice period of 60 days")}
THOUGHT = {"LOW": 120, "HIGH": 900}             # the thought tokens evals/tests/test_prompt_bench.py scripts


class Script:
    """Gemini, stood in behind generator._client: the five wordings in turn, its thought tokens set by the level."""

    def __init__(self):
        """Count the calls per level and temperature, and keep what each one was sent."""
        self.turn, self.sent = {}, []

    @property
    def models(self):
        """client.models, as google-genai's client has it."""
        return self

    def generate_content(self, *, model, contents, config=None):
        """One reply in the shape generator._draft(), _usage() and _finish_reason() read."""
        key = (config.thinking_config.thinking_level.value, config.temperature)
        self.sent.append(key)
        k = self.turn[key] = self.turn.get(key, -1) + 1
        n = {code: int(i) for i, code in re.findall(r"\[Source (\d+)\] [^\n]*?(LV-07|NP-03)", contents[0])}
        src = {tag: n[code] for tag, (code, _) in QUOTES.items()}
        draft = {"answer": WORDINGS[k % len(WORDINGS)].format(**src), "confidence": "high", "answerable": True,
                 "citations": [{"source": src[tag], "quote": quote} for tag, (_, quote) in QUOTES.items()]}
        text = json.dumps(draft)
        usage = NS(prompt_token_count=len(contents[0]) // 4, candidates_token_count=len(text) // 4,
                   thoughts_token_count=THOUGHT[key[0]], cached_content_token_count=None)
        return NS(parsed=None, text=text, candidates=[NS(finish_reason=NS(name="STOP"))], usage_metadata=usage,
                  prompt_feedback=None)


def passages(api_url, question, tenant, email, token, top_k=6):
    """POST /v1/passages, stood in: the handbook's first six clauses, in the route's shape."""
    return POOL


def sources(api_url, tenant, token):
    """GET /v1/sources, stood in: the handbook's sha256 is acme's current version."""
    return {SHA}


for arm in (["--levels", "LOW,HIGH", "--show"], ["--temperature", "2.0"]):
    gen._client = script = Script()
    pb.main(["--rows", "jn-03", "--runs", "5", "--api-url", "http://stand-in.invalid"] + arm,
            generator=gen, passages=passages, sources=sources)
    print("  the script was sent: " + "; ".join(f"thinking_level {lv}, temperature {t}: {script.sent.count((lv, t))} calls"
                                                for lv, t in sorted(set(script.sent), key=str)) + "\n")'''

ARGS_LEVELS = f"--rows {ROW_ID} --runs 5 --levels LOW,HIGH --show --report evals/reports/bench-levels.json"
ARGS_TEMP = f"--rows {ROW_ID} --runs 5 --temperature 2.0 --report evals/reports/bench-temperature.json"
LEVELS_SH = f'make bench PROJECT="$PROJECT" REGION="$REGION" BENCH_ARGS="{ARGS_LEVELS}"'
TEMP_SH = f'make bench PROJECT="$PROJECT" REGION="$REGION" BENCH_ARGS="{ARGS_TEMP}"'

SENT_PY = r'''import json
rep = json.load(open("evals/reports/bench-temperature.json", encoding="utf-8"))
print(f"{rep['model']} | levels {', '.join(rep['levels'])} | {rep['runs']} runs | arms: "
      + "; ".join(f"{a['name']} with temperature {a['temperature']}, prompt sha256 {a['prompt_sha256'][:12]}" for a in rep["arms"]))
for a in rep["answers"]:
    for c in a["calls"]:
        print(f"  {a['arm']:4} run {a['run']} | sent thinking_level {c['thinking_level']}, temperature {c['temperature']}, "
              f"max_output_tokens {c['max_output_tokens']} | thought {c.get('thought', 0):>5} visible {c.get('visible', 0):>4} "
              f"| {c.get('ms', 0):>6} ms | {c.get('finish') or c.get('error')} | {'pass' if a['pass'] else 'FAIL'}")'''

USAGE_PY = r'''import json, os, subprocess, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from shared.prices import USD_INR
EVENTS = ("query", "stream", "passages")
FILTER = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND ('
          + " OR ".join(f'jsonPayload.event="{e}"' for e in EVENTS) + f') AND timestamp>="{os.environ["T0"]}"')
got = subprocess.run(["gcloud", "logging", "read", FILTER, "--project", os.environ["PROJECT"], "--limit", "200",
                      "--format=json"], capture_output=True, text=True, check=True).stdout
rows = [e["jsonPayload"] for e in json.loads(got or "[]")][::-1]          # Cloud Logging lists the newest first
for r in rows:
    print(f"{r['event']:8} {r['tenant']:5} tokens {r['tokens_in']:>5} in + {r['tokens_out']:>5} out | "
          f"Rs {(r.get('cost_usd') or 0) * USD_INR:.4f} | answerable {r['answerable']} | {r['model']} | "
          f"{r['prompt_version']} | generate_ms {r.get('generate_ms')}")
print("rows since T0: " + ", ".join(f"{e} {sum(r['event'] == e for r in rows)}" for e in EVENTS)
      + f" | tokens out {sum(r['tokens_out'] for r in rows):,} | Rs {sum(r.get('cost_usd') or 0 for r in rows) * USD_INR:.4f}")'''


def heredoc(body: str) -> str:
    """A Python cell as the page prints it: wrapped so that it pastes into bash."""
    return f"python - <<'PY'\n{body}\nPY"


CELLS = {"t0": T0_SH, "rest": heredoc(REST_PY), "tests": TESTS_SH, "script": heredoc(SCRIPT_PY), "levels": LEVELS_SH,
         "temp": TEMP_SH, "sent": heredoc(SENT_PY), "usage": heredoc(USAGE_PY)}
for body in (REST_PY, SCRIPT_PY, SENT_PY, USAGE_PY):
    tree = ast.parse(body)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            assert ast.get_docstring(node), f"{node.name} has no docstring: the IDE demos need one"
SC = {n.targets[0].id: n.value for n in ast.parse(SCRIPT_PY).body
      if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
WORDINGS, QUOTES, THOUGHT_S = (ast.literal_eval(SC[name]) for name in ("WORDINGS", "QUOTES", "THOUGHT"))
assert THOUGHT_S == {k: THOUGHT_T[k] for k in ("LOW", "HIGH")} == {"LOW": 120, "HIGH": 900}, (THOUGHT_S, THOUGHT_T)
assert all(q in HANDBOOK for _, q in QUOTES.values())
for args in (ARGS_LEVELS, ARGS_TEMP):
    assert args.split()[0] == "--rows" and ROW_ID in args
assert f'"id"] == "{ROW_ID}")' in REST_PY and f'"--rows", "{ROW_ID}"' in SCRIPT_PY

if os.environ.get("CELLS_ONLY"):                  # the cells as the page has them, for the run list, and stop
    for name, body in CELLS.items():
        print(f"===== {name}\n{body}")
    sys.exit(0)

# ------------------------------------------------------------------ the offline runs: no network, no credential
WORK = Path(tempfile.mkdtemp(prefix="lesson31_"))
_PROFILE = {k: str(WORK / "profile" / k.lower()) for k in ("APPDATA", "LOCALAPPDATA", "USERPROFILE", "HOME", "CLOUDSDK_CONFIG")}
for _d in _PROFILE.values():
    os.makedirs(_d, exist_ok=True)
CHILD_ENV = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
             "TEMP": str(WORK), "TMP": str(WORK), "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
             **_PROFILE}                       # no gcloud on PATH, no GOOGLE_* or DOCUMIND_* variables, an empty profile


def run_py(args: list, stdin: str | None = None, cwd: Path = KIT, env: dict | None = None) -> tuple:
    """This interpreter on args (or a cell on stdin), in cwd, with the child environment: (stdout, stderr)."""
    r = subprocess.run([sys.executable] + args, input=stdin, capture_output=True, text=True, encoding="utf-8",
                       cwd=str(cwd), env={**CHILD_ENV, **(env or {})})
    assert r.returncode == 0, (args[:3], r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout, r.stderr


# step 5's first cell: the kit's own tests (unittest reports on stderr; the seconds are the machine's)
_, TESTS_ERR = run_py(TESTS_SH.split()[1:])
TESTS_ERR = TESTS_ERR.replace("\r\n", "\n").rstrip("\n")
N_TESTS = int(re.search(r"^Ran (\d+) tests in [\d.]+s$", TESTS_ERR, re.M).group(1))
assert TESTS_ERR.endswith("\nOK") and TESTS_ERR.count(" ... ok") == N_TESTS and "skipped" not in TESTS_ERR, TESTS_ERR[-600:]
assert "Warning" not in TESTS_ERR, TESTS_ERR[:600]                  # the cell hides none: a warning would print here
assert "test_the_level_and_the_temperature_are_sent_and_nothing_else_changes" in TESTS_ERR
OUT_TESTS = re.sub(r"^Ran (\d+) tests in [\d.]+s$", r"Ran \1 tests in N.NNNs", TESTS_ERR, flags=re.M)

# step 5's second cell, as the page prints it, then its --report twin: the scripted run's records
OUT_SCRIPT = run_py(["-"], SCRIPT_PY)[0].replace("\r\n", "\n").rstrip("\n")
_ANCHOR = '"--api-url", "http://stand-in.invalid"] + arm,'
assert SCRIPT_PY.count(_ANCHOR) == 1
TWIN = SCRIPT_PY.replace(_ANCHOR, '"--api-url", "http://stand-in.invalid", "--report", os.environ["P31_REPORT"] + arm[0] + ".json"] + arm,')
run_py(["-"], TWIN, env={"P31_REPORT": str(WORK / "script")})
SREP = {k: json.loads((WORK / f"script--{k}.json").read_text(encoding="utf-8")) for k in ("levels", "temperature")}
for k, rep in SREP.items():                       # the twin printed what the page prints: one run, twice
    for line in bench.summary_lines(rep["summary"]):
        assert line in OUT_SCRIPT, (k, line)
assert OUT_SCRIPT.count("generator.py unchanged on disk; SYSTEM is the kit's again") == 2
assert OUT_SCRIPT.count(f"prompt sha256 {KIT_SHA}") == 3                     # the kit arm twice, the edit arm once: one text
assert "the script was sent: thinking_level HIGH, temperature None: 5 calls; thinking_level LOW, temperature None: 5 calls" in OUT_SCRIPT
assert "the script was sent: thinking_level LOW, temperature 2.0: 5 calls; thinking_level LOW, temperature None: 5 calls" in OUT_SCRIPT
assert "edit  generator.py's SYSTEM - 5 rules; temperature 2" in OUT_SCRIPT
S_LOW, S_HIGH = (next(s for s in SREP["levels"]["summary"] if s["level"] == level) for level in ("LOW", "HIGH"))
S_EDIT = next(s for s in SREP["temperature"]["summary"] if s["arm"] == "edit")
for s in (S_LOW, S_HIGH, S_EDIT):
    assert (s["answers"], s["ok"], s["passed"], s["distinct_answers"], s["distinct_citations"], s["errors"], s["retried"]) == \
        (5, 5, 4, 4, 1, 0, 0), s
assert (S_LOW["thought"], S_HIGH["thought"]) == (5 * THOUGHT_S["LOW"], 5 * THOUGHT_S["HIGH"]) and S_LOW["visible"] == S_HIGH["visible"]
SCRIPT_TEXTS = [a["answer"] for a in SREP["levels"]["answers"] if a["level"] == "LOW"]
_n = {p["text"].split()[0]: p["n"] for p in SREP["levels"]["rows"][0]["pool"]}     # each clause's [Source N] in the pool
assert SCRIPT_TEXTS == [w.format(LV=_n["LV-07"], NP=_n["NP-03"]) for w in WORDINGS], SCRIPT_TEXTS
FAILED_WORDING = next(a for a in SREP["levels"]["answers"] if not a["pass"])
assert FAILED_WORDING["why"] == "answered without ['45', '60']" and FAILED_WORDING["run"] == 5


def body_for(text: str) -> dict:
    """A /v1/query reply carrying this answer and two valid acme citations: what row_verdict() is handed."""
    sha = SREP["levels"]["answers"][0]["cites"][0]["chunk_id"].split(":", 1)[1].split("#")[0]
    uri = "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"
    return {"answer": text, "answerable": True, "confidence": "high",
            "citations": [{"chunk_id": f"acme:{sha}#{i}", "source_uri": uri, "quote": q, "page": 1}
                          for i, q in ((4, "capped at 45 days"), (1, "serves a notice period of 60 days"))]}


def kit_verdict(text: str) -> tuple:
    """run_eval.row_verdict() on a 200 carrying this answer, valid citations, the version check skipped: (pass, why)."""
    v = run_eval.row_verdict(ROW, 200, body_for(text), None, MANIFEST_OBJ, CORPUS_TEXT)
    return bool(v["pass"]), v["why"]


# ------------------------------------------------------------------ the author's runs: recorded once, every figure computed from them
AWAIT = "[awaiting the author's run: data/{}]"
REC = {name: pb.recorded(LESSON, name) for name in ("rest_five.txt", "bench_levels.txt", "bench_levels.json",
                                                     "bench_temperature.txt", "bench_temperature.json", "usage_rows.txt")}
HAVE = {name: not text.startswith("[awaiting the author's run:") for name, text in REC.items()}
RUN_LIST = (HERE / "RUN_LIST.md").read_text(encoding="utf-8")
assert T0_SH in RUN_LIST and SENT_PY not in RUN_LIST       # T0 first; the report cell needs no run of the author's
for code, files in ((REST_PY, ("rest_five.txt",)), (LEVELS_SH, ("bench_levels.txt", "bench_levels.json")),
                    (TEMP_SH, ("bench_temperature.txt", "bench_temperature.json")), (USAGE_PY, ("usage_rows.txt",))):
    if not all(HAVE[f] for f in files):       # while awaited, the run list must carry the command, verbatim
        assert code in RUN_LIST, (f"RUN_LIST.md must carry the cell that records {files}, verbatim, while it is awaited: "
                                  "CELLS_ONLY=1 python pagekit/build.py 3.1 prints the cells as the page has them")
        assert all(f"data/{f}" in RUN_LIST for f in files)
REP = {k: (json.loads(REC[f"bench_{k}.json"]) if HAVE[f"bench_{k}.json"] else None) for k in ("levels", "temperature")}


def check_bench_files(key: str, txt: str, rep: dict) -> None:
    """A recorded make bench: its JSON and its text are one run (the kit's own summary lines, in the text), on this row,
    with these arguments, and nothing private left in either."""
    assert rep["model"] == MODEL and [r["id"] for r in rep["rows"]] == [ROW_ID] and rep["runs"] == 5, key
    for line in bench.summary_lines(rep["summary"]):
        assert line in txt, (key, line)
    assert re.search(r"^== prompt bench: \S+, against https://documind-api-NUMBER\.asia-south1\.run\.app ==$", txt, re.M), key
    assert "generator.py unchanged on disk; SYSTEM is the kit's again" in txt, key
    for text in (txt, json.dumps(rep)):
        assert not re.search(r"documind-api-\d{6,}", text), f"{key}: a project number in the API's address"


for key, name in (("levels", "bench_levels"), ("temperature", "bench_temperature")):
    if REP[key] is not None:
        assert HAVE[f"{name}.txt"], f"data/{name}.json is recorded without data/{name}.txt: record both from one run"
        check_bench_files(key, REC[f"{name}.txt"], REP[key])
if REP["levels"] is not None:
    assert REP["levels"]["levels"] == ["LOW", "HIGH"] and [a["name"] for a in REP["levels"]["arms"]] == ["kit"]
if REP["temperature"] is not None:
    assert REP["temperature"]["levels"] == ["LOW"] and [(a["name"], a["temperature"]) for a in REP["temperature"]["arms"]] == \
        [("kit", None), ("edit", 2.0)]
REST_RX = [r"^/version: \S+ \| prompt \S+ \| semantic_cache \w+$",
           r"^distinct answers \d of \d \| cite sets \d of \d \| pass \d/5 = [\d.]+% \[[\d.]+%, [\d.]+%\] \| Rs \d+\.\d{4} for the five$"]
USAGE_RX = [r"^rows since T0: query \d+, stream \d+, passages \d+ \| tokens out [\d,]+ \| Rs \d+\.\d{4}$"]
if HAVE["rest_five.txt"]:
    assert all(re.search(rx, REC["rest_five.txt"], re.M) for rx in REST_RX), REC["rest_five.txt"][:400]
    assert len(re.findall(r"^run [1-5]: ", REC["rest_five.txt"], re.M)) == 5
if HAVE["usage_rows.txt"]:
    assert all(re.search(rx, REC["usage_rows.txt"], re.M) for rx in USAGE_RX), REC["usage_rows.txt"][-400:]

# ------------------------------------------------------------------ the REST, report and usage cells, run against stand-ins
STANDIN = r'''import io as _io, json as _json, subprocess as _sp, urllib.request as _ur
_SHA = __SHA__
_URI = "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"
_ANSWERS = __ANSWERS__
_ROWS = [{"event": e, "tenant": "acme", "tokens_in": t, "tokens_out": o, "cost_usd": c, "answerable": True, "model": m,
          "prompt_version": "v3", "generate_ms": g} for e, t, o, c, m, g in __ROWS__]
_N = {"query": 0}


class _Reply(_io.BytesIO):
    """An HTTP reply, stood in: a status and a JSON body, usable with `with`."""
    status = 200


def _run(argv, *a, **k):
    """gcloud, stood in: an identity token, or the usage rows."""
    out = "stand-in-token\n" if argv[:3] == ["gcloud", "auth", "print-identity-token"] else _json.dumps(
        [{"jsonPayload": r} for r in reversed(_ROWS)])
    return _sp.CompletedProcess(argv, 0, stdout=out, stderr="")


def _urlopen(req, timeout=None):
    """The lane's API, stood in: /version, GET /v1/sources and POST /v1/query."""
    url = req.full_url if hasattr(req, "full_url") else req
    if url.endswith("/version"):
        body = {"generator_model": "gemini-3.6-flash", "prompt": "documind-rag@v3", "semantic_cache": "off"}
    elif "/v1/sources" in url:
        body = {"sources": [{"doc_key": "acme_" + _SHA, "status": "indexed"}]}
    else:
        text = _ANSWERS[_N["query"] % len(_ANSWERS)]
        _N["query"] += 1
        body = {"answer": text, "answerable": True, "confidence": "high", "model": "gemini-3.6-flash", "backend": "vertex",
                "cost_usd": None, "tokens_in": 1584, "tokens_out": 300 + 10 * _N["query"], "cached_tokens": 0,
                "latency_ms": 2100, "cache_hit": "none", "stages": {"generate_ms": 1900, "pool": 20},
                "citations": [{"chunk_id": f"acme:{_SHA}#{i}", "source_uri": _URI, "page": 1, "quote": q, "score": 0.9,
                               "kind": "text"} for i, q in ((4, "capped at 45 days"), (1, "serves a notice period of 60 days"))]}
    return _Reply(_json.dumps(body).encode())


_sp.run, _ur.urlopen = _run, _urlopen
'''
_sha = SREP["levels"]["answers"][0]["cites"][0]["chunk_id"].split(":", 1)[1].split("#")[0]
_rows = [("stream", 1216, 420, 0.00497, MODEL, 2400)] * 5 + [("query", 1584, 310, 0.00470, MODEL, 1900)] * 5 + \
        [("passages", 0, 0, 0.0, "none", 0)] * 2
STANDIN = (STANDIN.replace("__SHA__", repr(_sha)).replace("__ANSWERS__", repr(SCRIPT_TEXTS))
           .replace("__ROWS__", repr(_rows)))
ENV_LANE = {"API": "https://documind-api-NUMBER.asia-south1.run.app", "PROJECT": "documind-ai-YOUR-ID",
            "T0": "2026-11-14T05:30:00Z"}
DRY_REST = run_py(["-"], STANDIN + REST_PY, env=ENV_LANE)[0]
assert all(re.search(rx, DRY_REST, re.M) for rx in REST_RX), DRY_REST
assert len(re.findall(r"^run [1-5]: (pass|FAIL) \| tokens \d+ in \+ \d+ out ", DRY_REST, re.M)) == 5, DRY_REST
assert "distinct answers 4 of 5 | cite sets 1 of 5 | pass 4/5 = 80.0%" in DRY_REST and "answered without ['45', '60']" in DRY_REST
DRY_USAGE = run_py(["-"], STANDIN + USAGE_PY, env=ENV_LANE)[0]
assert all(re.search(rx, DRY_USAGE, re.M) for rx in USAGE_RX) and "rows since T0: query 5, stream 5, passages 2" in DRY_USAGE, DRY_USAGE
assert DRY_USAGE.index("stream  ") < DRY_USAGE.index("query   ") < DRY_USAGE.index("passages")   # oldest first


def run_sent(report: dict) -> str:
    """Step 8's second cell on this report, from a kit-shaped folder holding it where the cell looks."""
    folder = Path(tempfile.mkdtemp(prefix="sent_", dir=WORK))
    (folder / "evals" / "reports").mkdir(parents=True)
    (folder / "evals" / "reports" / "bench-temperature.json").write_text(json.dumps(report), encoding="utf-8")
    return run_py(["-"], SENT_PY, cwd=folder)[0].replace("\r\n", "\n").rstrip("\n")


DRY_SENT = run_sent(SREP["temperature"])
assert DRY_SENT.count("sent thinking_level LOW, temperature 2.0, max_output_tokens 2048") == 5, DRY_SENT
assert DRY_SENT.count("sent thinking_level LOW, temperature None, max_output_tokens 2048") == 5, DRY_SENT
OUT_SENT = run_sent(REP["temperature"]) if REP["temperature"] is not None else AWAIT.format("bench_temperature.json")
if REP["temperature"] is not None:
    assert OUT_SENT.count(", temperature 2.0, ") >= 5 and OUT_SENT.count(", temperature None, ") >= 5, OUT_SENT[:600]


# ------------------------------------------------------------------ the Level 0 widget: the gate's text rule, in the browser
def text_rule(text: str) -> tuple:
    """The text half of row_verdict() for jn-03, in Python, for an answer whose citations are taken as valid."""
    norm = run_eval.normalise(text)
    why = ""
    for never in ROW.get("must_not_contain", []):
        if run_eval.contains(norm, never):
            why = f"answer contained {never!r}"
    contained = all(run_eval.contains(norm, w) for w in ROW["must_contain"])
    if not contained:
        why = f"answered without {ROW['must_contain']}"
    return contained and not why.startswith("answer contained"), why


def sets_from_report(rep: dict) -> list:
    """The kit arm's answers per level from a bench --report, as the widget shows them: an answer the text rule cannot
    judge as the bench did (a refusal, a citation's verdict, an answer cut at 600 characters) carries the bench's own
    verdict, locked while its text is unedited; an error has no text."""
    out = []
    for level in rep["levels"]:
        answers = []
        for a in (x for x in rep["answers"] if x["arm"] == "kit" and x["level"] == level):
            if a["outcome"] != "ok":
                answers.append({"t": "", "err": f"{a['outcome']}: {a['why']}"})
                continue
            item = {"t": a["answer"]}
            if text_rule(a["answer"]) != (bool(a["pass"]), a["why"]):
                item["lock"] = {"pass": bool(a["pass"]), "why": a["why"]}
            answers.append(item)
        out.append({"name": f"{level}: Gemini's {len(answers)} answers, the author's run", "answers": answers})
    return out


TRIES = [("sixty days", "Encashment is capped at forty-five days, and the notice period is sixty days."),
         ("160 days", "45 days are encashed, and the notice period is 160 days."),
         ("60.5 days", "45 days are encashed, and the notice period is 60.5 days."),
         ("two months", "45 days are encashed, and you serve two months' notice."),
         ("all 50 days", "All 50 days are encashed, and the notice period is 60 days."),
         ("45 rupees, 60 hours", "You are paid 45 rupees and you work 60 hours.")]
ILLUSTRATION = [{"name": "Five wordings: the scripted model's, an illustration", "answers": [{"t": t} for t in SCRIPT_TEXTS]}]
TEST_SETS = sets_from_report(SREP["levels"])      # the recorded path, exercised on the scripted run's report every build
assert [a["t"] for s in TEST_SETS for a in s["answers"]] == SCRIPT_TEXTS * 2 and not any("lock" in a for s in TEST_SETS for a in s["answers"])
_locked = json.loads(json.dumps(SREP["levels"]))
_locked["answers"][0].update(why="refused", **{"pass": False})
_locked["answers"][1].update(outcome="error", why="HTTP 502 HTTPException: generation produced no parseable answer (MAX_TOKENS)",
                             **{"pass": False})
_lk = sets_from_report(_locked)
assert _lk[0]["answers"][0]["lock"] == {"pass": False, "why": "refused"} and _lk[1]["answers"][0]["err"].startswith("error: HTTP 502")
SETS = sets_from_report(REP["levels"]) if REP["levels"] is not None else ILLUSTRATION
SRC_NOTE = ("The author's run, recorded in step 7: Gemini's answers to jn-03 at LOW and at HIGH, each with the verdict the "
            "bench gave it. Edit one and the widget judges your text by the same rule." if REP["levels"] is not None else
            "An illustration until the author's run is recorded: the five answers step 5's scripted model writes, numbered as "
            "its stand-in pool numbers the clauses (LV-07 is [%d], NP-03 is [%d]). They are written for this page; Gemini's "
            "own ten, five at LOW and five at HIGH, take their place when step 7's run is in." % (_n["LV-07"], _n["NP-03"]))

PORT_JS = r"""var SMALL = {zero:0,one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10,eleven:11,twelve:12,thirteen:13,fourteen:14,fifteen:15,sixteen:16,seventeen:17,eighteen:18,nineteen:19,twenty:20,thirty:30,forty:40,fifty:50,sixty:60,seventy:70,eighty:80,ninety:90};
var SCALE = {hundred:100,thousand:1000,lakh:100000,crore:10000000};
var W = '[\\p{L}\\p{N}_]', WORD = Object.keys(SMALL).concat(Object.keys(SCALE)).join('|');
var NUMWORDS = new RegExp('(?<!' + W + ')(?:(?:' + WORD + ')(?:[\\s-]+(?:' + WORD + '))*)(?!' + W + ')', 'gu');
var has = function(o, k){ return Object.prototype.hasOwnProperty.call(o, k); };
function toInt(run){ var total = 0, current = 0;                                   /* run_eval._to_int() */
  run.split(/[\s-]+/).forEach(function(w){ if (has(SMALL, w)) current += SMALL[w]; else if (w === 'hundred') current = (current || 1) * 100;
    else if (has(SCALE, w)) { total += (current || 1) * SCALE[w]; current = 0; } });
  return total + current; }
function normalise(text){ var t = String(text).toLowerCase().split(',').join('').split('-').join(' ');   /* run_eval.normalise() */
  [' per cent', 'per cent', ' percent', 'percent'].forEach(function(s){ t = t.split(s).join('%'); });
  return t.replace(NUMWORDS, function(m){ return String(toInt(m)); }); }
function contains(text, want){ var w = normalise(want).trim(); if (!w) return false;          /* run_eval.contains() */
  return new RegExp('(?<![\\p{L}\\p{N}_.])' + w.replace(/[.*+?^${}()|[\]\\\/]/g, '\\$&') + '(?!' + W + '|\\.\\d)', 'u').test(normalise(text)); }
function pyrepr(s){ return (s.indexOf("'") >= 0 && s.indexOf('"') < 0) ? '"' + s + '"' : "'" + s.replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'"; }
function flat(t){ return String(t).split(/\s+/).filter(function(x){ return x; }).join(' '); }   /* prompt_bench.flat() */
function verdict(row, answer){                    /* run_eval.row_verdict() on a 200 whose citations are valid: the text half */
  var text = normalise(answer), why = '', found = [];
  row.mnc.forEach(function(n){ if (contains(text, n)) why = 'answer contained ' + pyrepr(n); });
  row.mc.forEach(function(w){ found.push([w, contains(text, w)]); });
  var contained = found.every(function(f){ return f[1]; });
  if (!contained) why = 'answered without [' + row.mc.map(pyrepr).join(', ') + ']';
  return {pass: contained && why.indexOf('answer contained') !== 0, why: why, found: found, text: text}; }"""

PROBES = [(t, w) for t in SCRIPT_TEXTS + [x[1] for x in TRIES] for w in ROW["must_contain"]]
PROBES += [("The notice period is 160 days", "60"), ("3600 rupees", "60"), ("8.33%", "8.33"), ("18.33%", "8.33"),
           ("forty-five days", "45"), ("sixty-day notice", "60"), ("Rs 1,84,500 payable", "1,84,500"), ("it is 60.", "60"),
           ("60.5 days", "60"), ("E3", "3"), ("4560 days", "45"), ("45-day cap", "45"), ("one lakh twenty thousand", "120000")]
VERDICT_TEXTS = SCRIPT_TEXTS + [x[1] for x in TRIES] + [a["t"] for s in SETS for a in s["answers"] if a["t"] and "lock" not in a]
JS_ROW = {"id": ROW_ID, "q": ROW["question"], "mc": ROW["must_contain"], "mnc": ROW.get("must_not_contain") or []}
test_js = ("'use strict';\n" + PORT_JS + "\nvar probes = " + json.dumps(PROBES) + ", texts = " + json.dumps(VERDICT_TEXTS)
           + ", row = " + json.dumps(JS_ROW) + ";\nprocess.stdout.write(JSON.stringify({c: probes.map(function(p){ return contains(p[0], p[1]); }),"
           " v: texts.map(function(t){ var v = verdict(row, t); return [v.pass, v.why]; }), f: texts.map(flat)}));\n")
_tjs = WORK / "port.js"
_tjs.write_text(test_js, encoding="utf-8")
_node = subprocess.run(["node", str(_tjs)], capture_output=True, text=True, encoding="utf-8")
assert _node.returncode == 0, _node.stderr[-800:]
JSR = json.loads(_node.stdout)
for (text, want), got in zip(PROBES, JSR["c"]):
    assert got == run_eval.contains(text, want), (text, want, got)
for text, (jpass, jwhy), jflat in zip(VERDICT_TEXTS, JSR["v"], JSR["f"]):
    assert (jpass, jwhy) == kit_verdict(text) == text_rule(text), (text, jpass, jwhy, kit_verdict(text))
    assert jflat == bench.flat(text), text
N_CHECKED = len(PROBES) + len(VERDICT_TEXTS)
TRY_V = {label: kit_verdict(text) for label, text in TRIES}
assert [TRY_V[k][0] for k, _ in TRIES] == [True, False, False, False, False, True], TRY_V
ILL_V = [kit_verdict(t) for t in SCRIPT_TEXTS]
ILL_PASS, ILL_DISTINCT = sum(p for p, _ in ILL_V), len({bench.flat(t) for t in SCRIPT_TEXTS})
assert (ILL_PASS, ILL_DISTINCT) == (S_LOW["passed"], S_LOW["distinct_answers"]) == (4, 4)   # the widget and the bench agree

DATA = {"row": JS_ROW, "sets": SETS, "tries": TRIES, "note": SRC_NOTE,
        "rates": {str(n): W[n] if n in W else [rate(k, n) for k in range(n + 1)] for n in {len(s["answers"]) for s in SETS}}}
UI_JS = r"""var root = document.getElementById('vb'); if (!root) return;
var $ = function(id){ return document.getElementById(id); };
function el(tag, cls, text){ var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
$('vb-src').textContent = D.note;
var tryIn = $('vb-try-in'), tryOut = $('vb-try-out'), chips = $('vb-chips');
function line(v){ return v.pass ? ['ok', 'PASS'] : ['no', 'FAIL: ' + v.why]; }
function showTry(){
  var v = verdict(D.row, tryIn.value), l = line(v);
  tryOut.textContent = '';
  tryOut.appendChild(el('div', '', 'normalised: ' + v.text));
  v.found.forEach(function(f){ tryOut.appendChild(el('div', '', f[0] + ': ' + (f[1] ? 'found, on its own boundary' : 'not found on its own boundary'))); });
  tryOut.appendChild(el('div', l[0], l[1]));
}
D.tries.forEach(function(t){ var b = el('button', '', t[0]); b.type = 'button'; b.addEventListener('click', function(){ tryIn.value = t[1]; showTry(); }); chips.appendChild(b); });
tryIn.value = D.tries[0][1];
tryIn.addEventListener('input', showTry);
showTry();
var holder = $('vb-sets');
D.sets.forEach(function(s, si){
  var card = el('div', 'vb-set'), boxes = [], counts = el('div', 'vb-n');
  card.appendChild(el('div', 'vb-h', s.name));
  s.answers.forEach(function(a, ai){
    var wrap = el('div', 'vb-a'), v = el('div', 'vb-v');
    if (a.err) { wrap.appendChild(el('div', 'vb-err', 'run ' + (ai + 1) + ': ' + a.err)); card.appendChild(wrap); boxes.push(null); return; }
    var box = el('textarea'); box.value = a.t; box.rows = 3; box.setAttribute('aria-label', s.name + ', run ' + (ai + 1));
    wrap.appendChild(box); wrap.appendChild(v); card.appendChild(wrap);
    boxes.push({box: box, v: v, a: a});
    box.addEventListener('input', render);
  });
  card.appendChild(counts);
  var reset = el('button', 'vb-reset', 'Put the answers back'); reset.type = 'button';
  reset.addEventListener('click', function(){ boxes.forEach(function(b){ if (b) b.box.value = b.a.t; }); render(); });
  card.appendChild(reset);
  holder.appendChild(card);
  function render(){
    var seen = {}, distinct = 0, ok = 0, passed = 0;
    boxes.forEach(function(b, i){
      if (!b) return;
      ok++;
      var t = flat(b.box.value), lk = b.a.lock && b.box.value === b.a.t, v = lk ? b.a.lock : verdict(D.row, b.box.value);
      if (!seen[t]) { seen[t] = 1; distinct++; }
      if (v.pass) passed++;
      var l = v.pass ? ['ok', 'PASS'] : ['no', 'FAIL: ' + v.why];
      b.v.textContent = 'run ' + (i + 1) + ' ';
      b.v.appendChild(el('span', l[0], l[1]));
      if (lk) b.v.appendChild(el('span', '', " (the bench's verdict on this answer)"));
    });
    counts.textContent = 'distinct answers ' + distinct + ' of ' + ok + ' | pass ' + D.rates[String(s.answers.length)][passed];
  }
  render();
});"""
_squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731


def make_js(data: dict) -> str:
    """The widget's script for this data: the port, then the UI, in one closure."""
    return ("(function(){\n'use strict';\nvar D = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
            + ";\n" + _squeeze(PORT_JS) + "\n" + _squeeze(UI_JS) + "\n})();\n")


JS = "<script>\n" + make_js(DATA) + "</script>\n"
assert "%%" not in JS and "@@" not in JS and not re.search(r"<(div|span|p|tr|svg)\b", JS)

# the script itself, run in node against a small DOM stand-in: what it renders, and what an edit and a reset do
DOM_STUB = r"""function El(tag){ this.tag = tag; this.children = []; this.className = ''; this._t = ''; this.value = ''; this.listeners = {}; this.attrs = {}; }
El.prototype.appendChild = function(c){ this.children.push(c); return c; };
El.prototype.addEventListener = function(t, f){ (this.listeners[t] = this.listeners[t] || []).push(f); };
El.prototype.setAttribute = function(k, v){ this.attrs[k] = String(v); };
Object.defineProperty(El.prototype, 'textContent', {get: function(){ return this._t + this.children.map(function(c){ return c.textContent; }).join(''); },
  set: function(v){ this._t = String(v); this.children = []; }});
var ids = {}; ['vb', 'vb-src', 'vb-try-in', 'vb-try-out', 'vb-chips', 'vb-sets'].forEach(function(id){ ids[id] = new El('div'); });
var document = {getElementById: function(id){ return ids[id] || null; }, createElement: function(t){ return new El(t); }};
function fire(e, t){ (e.listeners[t] || []).forEach(function(f){ f(); }); }
function find(e, cls, out){ out = out || []; if (e.className === cls || e.tag === cls) out.push(e); e.children.forEach(function(c){ find(c, cls, out); }); return out; }
"""
DOM_DRIVE = r"""
var sets = ids['vb-sets'].children, snap = {src: ids['vb-src'].textContent, try0: ids['vb-try-out'].textContent, sets: []};
fire(ids['vb-chips'].children[1], 'click');
snap.tryChip = [ids['vb-try-in'].value, ids['vb-try-out'].textContent];
sets.forEach(function(s){
  var one = {counts: [find(s, 'vb-n')[0].textContent], verdicts: find(s, 'vb-v').map(function(e){ return e.textContent; }), errs: find(s, 'vb-err').map(function(e){ return e.textContent; })};
  var boxes = find(s, 'textarea'), last = boxes[boxes.length - 1];
  last.value = 'You can encash 45 of your 50 days, and you serve 60 days of notice.'; fire(last, 'input');
  one.counts.push(find(s, 'vb-n')[0].textContent);
  boxes[1].value = boxes[2].value; fire(boxes[1], 'input');
  one.counts.push(find(s, 'vb-n')[0].textContent);
  fire(find(s, 'vb-reset')[0], 'click');
  one.counts.push(find(s, 'vb-n')[0].textContent);
  snap.sets.push(one);
});
process.stdout.write(JSON.stringify(snap));
"""


def dom_run(data: dict) -> dict:
    """make_js(data) in node over the DOM stand-in, driven: a chip, an edit that passes, a duplicate, then the reset."""
    path = WORK / "dom.js"
    path.write_text(DOM_STUB + make_js(data) + DOM_DRIVE, encoding="utf-8")
    r = subprocess.run(["node", str(path)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr[-1500:]
    return json.loads(r.stdout)


def counts(sets: list) -> list:
    """What each set's counter line should say, from the kit's own functions: distinct answers and pass k/N."""
    out = []
    for s in sets:
        ok = [a for a in s["answers"] if not a.get("err")]
        passed = sum((a["lock"]["pass"] if "lock" in a else kit_verdict(a["t"])[0]) for a in ok)
        out.append(f"distinct answers {len({bench.flat(a['t']) for a in ok})} of {len(ok)} | pass {rate(passed, len(s['answers']))}")
    return out


DOM = dom_run(DATA)
assert DOM["src"] == SRC_NOTE and DOM["tryChip"][0] == TRIES[1][1] and "FAIL: answered without ['45', '60']" in DOM["tryChip"][1]
assert DOM["try0"].startswith("normalised: encashment is capped at 45 days and the notice period is 60 days.") and DOM["try0"].endswith("PASS")
for s, got, want in zip(SETS, DOM["sets"], counts(SETS)):
    assert got["counts"][0] == got["counts"][3] == want, (got["counts"], want)      # as built, and after the reset
    assert len(got["verdicts"]) + len(got["errs"]) == len(s["answers"])
for data_sets in (TEST_SETS, _lk):                  # the recorded path: two levels, then a locked verdict and an error
    dom = dom_run({**DATA, "sets": data_sets, "rates": {"5": W[5]}})
    assert [x["counts"][0] for x in dom["sets"]] == counts(data_sets), ([x["counts"][0] for x in dom["sets"]], counts(data_sets))
assert "the bench" in dom["sets"][0]["verdicts"][0] and dom["sets"][1]["errs"][0].startswith("run 1: error: HTTP 502")
assert DOM["sets"][0]["counts"][1:3] == [f"distinct answers 4 of 5 | pass {W[5][5]}", f"distinct answers 3 of 5 | pass {W[5][5]}"] \
    if REP["levels"] is None else True


# ------------------------------------------------------------------ the author's figures, computed from the recordings
def level_figures(rep: dict, arm: str, level: str) -> dict:
    """One arm and level of a recorded bench: the summary's counts, per-answer tokens and rupees, and the median time."""
    s = next(x for x in rep["summary"] if x["arm"] == arm and x["level"] == level)
    ms = [c["ms"] for a in rep["answers"] if a["arm"] == arm and a["level"] == level for c in a["calls"] if "ms" in c]
    return {"dist": f"{s['distinct_answers']} of {s['ok']}", "cite": f"{s['distinct_citations']} of {s['ok']}",
            "pass": rate(s["passed"], s["answers"]), "th": s["thought"] / s["answers"], "vis": s["visible"] / s["answers"],
            "rs": s["cost_inr"] / s["answers"], "ms": statistics.median(ms) if ms else 0, "retried": s["retried"],
            "errors": s["errors"], "n": s["answers"], "passed": s["passed"]}


def many(n: float, base: float) -> str:
    """'3.2 times as many' or '80% as many', or a plain 'more' or 'fewer' when the base is too small to divide by."""
    if base >= 1:
        return f"{n / base:.1f} times as many" if n >= base else f"{n / base:.0%} as many"
    return "more" if n > base else ("as many" if n == base else "fewer")


R = {}
if REP["levels"] is not None:
    L, H = level_figures(REP["levels"], "kit", "LOW"), level_figures(REP["levels"], "kit", "HIGH")
    R["R_LEVELS"] = (f"On the author's lane, at LOW the five answers held {L['dist']} distinct wordings and {L['cite']} cite sets, and "
                     f"passed {L['pass']}; at HIGH, {H['dist']}, {H['cite']} and {H['pass']}. HIGH thought {H['th']:,.0f} tokens an "
                     f"answer against {L['th']:,.0f} at LOW ({many(H['th'], L['th'])}), wrote {H['vis']:,.0f} visible tokens against "
                     f"{L['vis']:,.0f}, cost Rs {H['rs']:.4f} an answer against Rs {L['rs']:.4f}, and took {H['ms']:,.0f} ms a call "
                     f"(the median) against {L['ms']:,.0f}."
                     + (f" {H['retried'] + L['retried']} answer(s) were cut off at the cap and asked again." if H["retried"] + L["retried"] else "")
                     + (f" {H['errors'] + L['errors']} came back as an error, not an answer." if H["errors"] + L["errors"] else ""))
else:
    R["R_LEVELS"] = AWAIT.format("bench_levels.json") + " The figures for each level are computed here from the recorded file."
if REP["temperature"] is not None:
    KT, ED = level_figures(REP["temperature"], "kit", "LOW"), level_figures(REP["temperature"], "edit", "LOW")
    sent2 = sum(1 for a in REP["temperature"]["answers"] if a["arm"] == "edit" for c in a["calls"] if c.get("temperature") == 2.0)
    sent0 = sum(1 for a in REP["temperature"]["answers"] if a["arm"] == "kit" for c in a["calls"] if c.get("temperature") is None)
    R["R_TEMP"] = (f"On the author's lane the recorder's log shows {sent2} calls sent with temperature 2.0 and {sent0} with none. "
                   f"At 2.0 the five answers held {ED['dist']} distinct wordings and {ED['cite']} cite sets, and passed {ED['pass']}, "
                   f"thinking {ED['th']:,.0f} tokens an answer; the kit arm beside them held {KT['dist']} and {KT['cite']}, and passed "
                   f"{KT['pass']}, thinking {KT['th']:,.0f}."
                   + (f" The kit arm at LOW in step 7 held {L['dist']} and {L['cite']}, and passed {L['pass']}."
                      if REP["levels"] is not None else ""))
else:
    R["R_TEMP"] = AWAIT.format("bench_temperature.json") + " The two arms' figures are computed here from the recorded file."
if HAVE["rest_five.txt"]:
    m = re.search(r"^distinct answers (\d) of (\d) \| cite sets (\d) of \d \| pass (\S+ = [\d.]+% \[[\d.]+%, [\d.]+%\])",
                  REC["rest_five.txt"], re.M)
    R["R_REST"] = (f"On the author's lane the five replies held {m.group(1)} of {m.group(2)} distinct answers and {m.group(3)} of "
                   f"{m.group(2)} cite sets, and passed {m.group(4)}.")
else:
    R["R_REST"] = AWAIT.format("rest_five.txt")
if HAVE["usage_rows.txt"]:
    m = re.search(r"^rows since T0: query (\d+), stream (\d+), passages (\d+)", REC["usage_rows.txt"], re.M)
    q, s, p = (int(x) for x in m.groups())
    R["R_USAGE"] = (f"On the author's lane the read found {q} query rows, {s} stream rows and {p} passages rows since T0"
                    + (": step 6's five, the Chat page's five and the bench's two pool reads, and nothing for the bench's "
                       "twenty answers." if (q, s, p) == (5, 5, 2) else
                       ", not the five, five and two this page expects: something else asked the API since T0, or a step "
                       "was skipped or repeated."))
else:
    R["R_USAGE"] = AWAIT.format("usage_rows.txt")


# ------------------------------------------------------------------ windows
def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


RS = lambda x: f"{x:,.2f}"     # noqa: E731
COST = {"UI_IN": 5 * inr(EST[UI_TOPK], 0), "REST_IN": 5 * inr(EST[TOPK], 0), "BENCH_IN": 10 * inr(EST[TOPK], 0),
        "CAP_CALL": inr(0, CAP), "RETRY_CALL": inr(0, CAP3)}
COST.update({"UI_MAX": COST["UI_IN"] + 5 * COST["CAP_CALL"], "REST_MAX": COST["REST_IN"] + 5 * COST["CAP_CALL"],
             "BENCH_MAX": COST["BENCH_IN"] + 10 * COST["CAP_CALL"]})
COST["ALL_IN"] = COST["UI_IN"] + COST["REST_IN"] + 2 * COST["BENCH_IN"]
COST["ALL_MAX"] = COST["UI_MAX"] + COST["REST_MAX"] + 2 * COST["BENCH_MAX"]
LANE = "the operator shell, in $DEMO_ROOT"
CELL_LABELS = {
    "t0": f"run in {LANE}, before you ask in the UI (Rs 0: it notes the time)",
    "rest": (f"run in {LANE} (five /v1/query answers at LOW: about Rs {RS(COST['REST_IN'])} of input by the kit's count, "
             f"at most Rs {RS(COST['REST_MAX'])} with every answer at the {CAP:,}-token cap)"),
    "tests": f"run in {LANE} (Rs 0: the kit's tests of the bench, no network)",
    "script": f"run in {LANE} (a Python cell; Rs 0: the kit's generate() over a scripted model, nothing leaves the machine)",
    "levels": (f"run in {LANE} (ten answers, five at LOW and five at HIGH: about Rs {RS(COST['BENCH_IN'])} of input, "
               f"at most Rs {RS(COST['BENCH_MAX'])} at the cap; a cut-off answer asked again adds up to Rs {RS(COST['RETRY_CALL'])})"),
    "temp": (f"run in {LANE} (ten answers at LOW, five with a temperature of 2.0: about Rs {RS(COST['BENCH_IN'])} of input, "
             f"at most Rs {RS(COST['BENCH_MAX'])} at the cap)"),
    "sent": f"run in {LANE} (a Python cell; Rs 0: it reads the report step 8's run wrote)",
    "usage": f"run in {LANE}, a minute after step 8 (a Python cell; Rs 0: one Cloud Logging read)",
}
OUT_LABELS = {
    "t0": ("(your time, in UTC)", "lesson 3.1 from YYYY-MM-DDTHH:MM:SSZ (UTC): step 9 reads the usage rows written since then"),
    "rest": ("(the author's lane, recorded: your words, tokens, times and rupees are your own)", REC["rest_five.txt"]),
    "tests": ("(the kit's own tests, run when this page was built: the seconds are your machine's)", OUT_TESTS),
    "script": ("(the kit's own bench over the stand-ins, run when this page was built: yours prints the same)", OUT_SCRIPT),
    "levels": ("(the author's lane, recorded: your answers, tokens and rupees are your own)", REC["bench_levels.txt"]),
    "temp": ("(the author's lane, recorded)", REC["bench_temperature.txt"]),
    "sent": ("(this cell over the author's recorded report)", OUT_SENT),
    "usage": ("(the author's lane, recorded: your counts depend on what you asked since T0)", REC["usage_rows.txt"]),
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUT_LABELS.items()})

NEXT = MANIFEST["modules"]["03"]["lessons"]["3.2"]["name"]
STATS = {
    "ROW": ROW_ID, "Q": html.escape(ROW["question"]), "N_JOIN": str(N_JOIN), "MODEL": MODEL, "CAP": f"{CAP:,}",
    "CAP3": f"{CAP3:,}", "KIT_LEVEL": KIT_LEVEL, "LEVELS": ", ".join(LEVELS), "TOPK": str(TOPK), "UI_TOPK": str(UI_TOPK),
    "PV": PV, "SHA12": KIT_SHA[:12], "USD_IN": f"{USD_IN:.2f}", "USD_OUT": f"{USD_OUT:.2f}", "USD_INR": str(USD_INR),
    "INR_PER_K_OUT": f"{INR_PER_K_OUT:.2f}", "INR_PER_K_IN": f"{INR_PER_K_IN:.2f}", "RATIO": f"{USD_OUT / USD_IN:g}",
    "W55": W[5][5], "W55_LO": W55_LO, "W35": W[5][3], "CACHE_DEFAULT": CACHE_DEFAULT, "NEXT_TITLE": html.escape(NEXT),
    "N_TESTS": str(N_TESTS), "TH_LOW": str(THOUGHT_S["LOW"]), "TH_HIGH": str(THOUGHT_S["HIGH"]),
    "S_DIST": f"{S_LOW['distinct_answers']} of {S_LOW['ok']}", "S_CITE": f"{S_LOW['distinct_citations']} of {S_LOW['ok']}",
    "S_PASS": rate(S_LOW["passed"], S_LOW["answers"]), "S_RS_LOW": f"{S_LOW['cost_inr'] / 5:.4f}",
    "S_RS_HIGH": f"{S_HIGH['cost_inr'] / 5:.4f}", "S_RS_DIFF": f"{(S_HIGH['cost_inr'] - S_LOW['cost_inr']) / 5:.4f}",
    "S_TH_DIFF": f"{THOUGHT_S['HIGH'] - THOUGHT_S['LOW']:,}", "S_FAIL_RUN": str(FAILED_WORDING["run"]),
    "LV_N": str(_n["LV-07"]), "NP_N": str(_n["NP-03"]), "N_CHECKED": str(N_CHECKED), "EST6": f"{EST[TOPK]:,}",
    "RS_UI_IN": RS(COST["UI_IN"]), "RS_UI_MAX": RS(COST["UI_MAX"]),
    **{k: html.escape(v) for k, v in R.items()},
}
assert all(f"%%{k}%%" in "".join(pb.part(LESSON, p) for p in "abc") for k in STATS), "a figure no part uses"


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
shutil.rmtree(WORK, ignore_errors=True)

# the run list's prices, from the same figures: a stale line is named here, not silently kept
for k in ("UI_IN", "UI_MAX", "REST_IN", "REST_MAX", "BENCH_IN", "BENCH_MAX", "ALL_IN", "ALL_MAX", "CAP_CALL", "RETRY_CALL"):
    if f"Rs {RS(COST[k])}" not in RUN_LIST:
        print(f"note: RUN_LIST.md does not state {k} = Rs {RS(COST[k])}")
print(f"kit: {MODEL}, thinking {KIT_LEVEL}, no temperature, cap {CAP} (retry {CAP3}) | row {ROW_ID}: prompt about {EST[TOPK]} "
      f"tokens on the Rs 0 lane | {N_TESTS} bench tests ok | scripted run {S_LOW['distinct_answers']} of 5 distinct, "
      f"{S_LOW['passed']}/5 pass | widget port held equal on {N_CHECKED} checks | recorded: "
      f"{', '.join(k for k, v in HAVE.items() if v) or 'none yet'}")
