"""Build lesson 3.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Recognise prompt failure modes and fix them in the prompt. The eval gate judges every golden row by one rule,
run_eval.row_verdict(), and a row that fails says why: refused, answered without its figure, answered without a
citation, answered when it should refuse, or no answer at all. DOCUMIND_EVAL_PASSAGES=1 reads each answerable row's
pool again, so a failing row also says whether its must_retrieve anchors reached the model. A failure is the
prompt's only when they did; this page calls where a fix lives its address. The fixes are tried in the prompt
bench (evals/prompt_bench.py): one rule added to generator.SYSTEM in memory, the row re-asked on its own fixed
pool beside the 8 refusal rows, which guard against a rule that makes the model answer where it must not. Nothing
is committed: SYSTEM stays equal to evals/make_trainset.py's copy (commands/tests/test_prompt_versions.py).

Computed here, offline, from the kit you clone:
  - the failure desk (Level 0): eight golden rows, each with a pool of the kit's own chunks (shared/local_corpus)
    and a reply written for the page as an illustration. Their verdicts are run_eval.row_verdict()'s, their quote
    checks quote_check()'s and their anchors anchors_found()'s, ported to JavaScript; node runs the port over every
    case and its variants, and every result must equal the kit's;
  - the read cell's address() rule, run in the build on the same cases, and node's port held equal to it;
  - the offline cells: SYSTEM's rules read as the bench reads them, the three recipe rules applied in memory, and
    the SYSTEM equality with the kit's own test;
  - the lane cells, tested before a lane runs them: run_eval.live() against a stub API with
    DOCUMIND_EVAL_PASSAGES=1, the read cell over the stub's report with /v1/passages stood in, the bench's main()
    over services/rag-api/generator.py lifted with a scripted model, and the fix cell over the bench's reports, in
    two scripted scenes that reach all four of its verdicts;
  - what the runs cost: every golden row's prompt on the Rs 0 lane's pools (lesson 2.6's method: the kit's
    lexical rank, packed and counted the way generate() packs and counts), at shared/prices.py's list prices.
Recorded from the author's lane with pb.recorded() (RUN_LIST.md says how): the live eval, the failing rows read
with their passages, the three one-rule bench runs and the fix cell over their reports.

    python pagekit/build.py 3.3          (the 3.12 venv; about two minutes: the Rs 0 lane ranks a tenant's corpus per row)
"""
import ast
import contextlib
import functools
import hashlib
import html
import importlib.util
import io
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "3.3"
title = ("<title>Lesson 3.3 Recognise prompt failure modes and fix them in the prompt - a failing row read with its "
         "passages, one rule tried in memory, and the refusal rows as the guard | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
API = "https://documind-api-NUMBER.asia-south1.run.app"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the failure desk: a row, its pool, a reply you can edit, and the gate's verdict with the fix's address */
.fd-cases{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px;}
.fd-case{font:inherit;font-size:13px;line-height:1.3;text-align:left;padding:7px 11px;border:1px solid var(--border);border-radius:9px;background:var(--card);color:var(--navy);cursor:pointer;min-height:max(40px,var(--touch));max-width:100%;overflow-wrap:anywhere;-webkit-tap-highlight-color:transparent;}
.fd-case b{font-family:var(--mono);font-size:11.5px;color:var(--teal-dark);margin-right:6px;}
.fd-case[aria-pressed="true"]{border:2px solid var(--teal);background:var(--teal-light);}
.fd-case:active,.fd-tg label:active{transform:scale(.98);}
.fd-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,290px),1fr));gap:10px;}
.fd-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:10px 12px;margin:0 0 10px;font-size:var(--small-size);line-height:1.5;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.fd-card h5{font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--navy);margin:0 0 6px;}
.fd-card p{margin:0 0 6px;font-size:var(--small-size);}
.fd-p{border-left:3px solid var(--border);padding:2px 0 2px 9px;margin:7px 0;font-size:13px;line-height:1.45;}
.fd-p.hit{border-left-color:var(--teal);}
.fd-p i{display:block;font-style:normal;font-family:var(--mono);font-size:11.5px;color:var(--navy);}
.fd-l{display:flex;flex-direction:column;gap:4px;font-size:var(--small-size);color:var(--navy);min-width:0;}
.fd-l textarea{font:inherit;font-family:var(--mono);font-size:16px;line-height:1.35;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);resize:vertical;min-height:44px;max-width:100%;}
.fd-tg{display:flex;flex-wrap:wrap;gap:2px 16px;margin:8px 0 0;}
.fd-tg label{display:flex;align-items:center;gap:7px;font-size:var(--small-size);color:var(--navy);min-height:max(36px,var(--touch));cursor:pointer;}
.fd-tg input{width:18px;height:18px;margin:0;accent-color:var(--teal);flex:0 0 auto;}
.fd-tg label.off{opacity:.45;}
.fd-out{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--teal);border-radius:12px;padding:10px 12px;font-size:var(--small-size);line-height:1.55;min-width:0;overflow-wrap:anywhere;}
.fd-out p{margin:0 0 6px;font-size:var(--small-size);}
.fd-v{font-family:var(--mono);font-weight:700;}
.fd-v.ok{color:#065f46;}
.fd-v.no{color:#b91c1c;}
.fd-at{font-weight:700;color:var(--teal-dark);}
.fd-rule{font-family:var(--mono);font-size:12.5px;background:var(--teal-light);border-radius:6px;padding:6px 8px;display:block;margin:4px 0 0;}
@media (hover:hover) and (pointer:fine){.fd-case:hover{border-color:var(--teal);}}
@media (forced-colors: active){.fd-case,.fd-card,.fd-out{border:1px solid CanvasText;}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson reads each failing row's passages by the kit's own chunk ids and pages, so point acme at the kit's "
         "index for the duration and put the pin back at the end."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head: step 3 asks as you, in the browser, and steps 5 to 7 ask as documind-ui-sa.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)

# ------------------------------------------------------------------ verbatim kit excerpts
RE_, PBF, GEN = "evals/run_eval.py", "evals/prompt_bench.py", "services/rag-api/generator.py"
MT, TPV = "evals/make_trainset.py", "commands/tests/test_prompt_versions.py"
EXCERPTS = {
    "ui_stream": ("services/frontend/chat.py - stream_answer(): the Chat page asks /v1/stream for five passages",
                  block("services/frontend/chat.py", "def stream_answer(query: str, tenant_id: str):", n=5)),
    "stream_cites": ("services/rag-api/generator.py - generate_stream(): no schema, and the sources are the packed set",
                     block(GEN, "    No response_schema here on purpose: you cannot usefully stream structured", n=6)),
    "system": ("services/rag-api/generator.py - SYSTEM's five rules, and the sixth held back for a dated source",
               block(GEN, 'SYSTEM = """You are DocuMind', end="def _dated_rule(")),
    "prompt_line": ("services/rag-api/generator.py - generate(): the packed passages, then the prompt every answer starts from",
                    block(GEN, "def _dated_rule(", n=2) + "\n...\n" + block(GEN, "    context, packed = _pack(query, chunks)", n=2)),
    "thresholds": ("evals/run_eval.py - THRESHOLDS: rates over many rows, so a row can fail and the gate still pass",
                   block(RE_, "THRESHOLDS = {", end="MIN_ROWS = ")),
    "row_verdict": ("evals/run_eval.py - row_verdict(): the gate's judgment of one reply, and the why it gives",
                    block(RE_, "def row_verdict(", end="QUOTE_VERDICTS = (")),
    "normalise": ("evals/run_eval.py - normalise() and contains(): the figure, not its spelling",
                  block(RE_, "def normalise(text: str) -> str:", end="# --------------------------------------------------------------------- live checks")),
    "kept": ("evals/run_eval.py - live(): what each row's record keeps of the reply, and the switch that reads its pool again",
             block(RE_, "        # What was said, so a failing row can be read from the report without asking again (W2-A).", n=4)
             + "\n...\n" + block(RE_, "    # DOCUMIND_EVAL_PASSAGES=1: each answerable row's pool read again", n=3)),
    "quote_check": ("evals/run_eval.py - quote_check(): one verdict per citation, against the pool its row retrieves",
                    block(RE_, "def quote_check(", end="def anchors_found(")),
    "anchors": ("evals/run_eval.py - anchors_found(): each must_retrieve anchor looked for in the pool",
                block(RE_, "def anchors_found(", end="def passage_checks(")),
    "eval_live": ("Makefile - eval-live: REPORT= keeps every row's record; the environment passes straight through",
                  block("Makefile", "eval-live: guard-project", n=9)),
    "bench_mk": ("mk/generation.mk - bench: your lane's pools, your shell's generator, the gate's rule",
                 block("mk/generation.mk", "# The prompt bench (evals/prompt_bench.py", end="# The prompt bound to its version")),
    "in_memory": ("evals/prompt_bench.py - the docstring: SYSTEM, in memory",
                  block(PBF, "SYSTEM, IN MEMORY.", n=4)),
    "edit_system": ("evals/prompt_bench.py - rules_of() and edit_system(): a rule appended, the rules renumbered",
                    block(PBF, "def rules_of(", end="def prompt_sha(")),
    "arms": ("evals/prompt_bench.py - arms(): the kit's prompt, and one arm carrying every change",
             block(PBF, "def arms(", end="# --------------------------------------------------------------------- the recorder around generator._client")),
    "bench_loop": ("evals/prompt_bench.py - bench(): one pool a row, every arm on it, and the kit's SYSTEM put back",
                   block(PBF, "def bench(", end="# --------------------------------------------------------------------- the summary")),
    "disk": ("evals/prompt_bench.py - main(): the file's bytes, before and after the run",
             block(PBF, "    if before and after:", n=4) + "\n...\n" + block(PBF, "    if before and after and before != after:", n=2)),
    "trainset": ("evals/make_trainset.py - the tuning set's copy of SYSTEM",
                 block(MT, 'SYSTEM = """You are DocuMind', n=8)),
    "same_test": ("commands/tests/test_prompt_versions.py - the test that holds the two copies equal",
                  block(TPV, "    def test_make_trainset_keeps_the_generators_system(self):", n=4)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert '"top_k": 5, "brain": "ui"' in E["ui_stream"] and E["stream_cites"].rstrip().endswith("cites from it before the first token.")
assert E["system"].count("\n1. ") == 1 and "5. A quote is the clause that answers" in E["system"] and E["system"].rstrip().endswith('from when it applies.")')
assert 'prompt = f"{SYSTEM}{_dated_rule(packed)}\\n\\nContext:\\n{context}\\n\\nQuestion: {query}"' in E["prompt_line"]
assert E["row_verdict"].rstrip().endswith("    return v") and 'v["why"] = "refused"' in E["row_verdict"]
assert E["normalise"].rstrip().endswith("return re.search(r\"(?<![\\w.])\" + re.escape(w) + r\"(?![\\w]|\\.\\d)\", normalise(text)) is not None")
assert 'rec["answer"] = body["answer"][:600]' in E["kept"] and 'os.environ.get("DOCUMIND_EVAL_PASSAGES") == "1"' in E["kept"]
assert E["quote_check"].rstrip().endswith('return "absent"') and E["anchors"].rstrip().endswith('for a in row.get("must_retrieve", [])}')
assert E["eval_live"].rstrip().endswith("$(if $(REPORT),--report $(REPORT),)") and "DOCUMIND_EVAL_PASSAGES" not in E["eval_live"]
assert E["bench_mk"].rstrip().endswith("$(PY) evals/prompt_bench.py --api-url $$API $(BENCH_ARGS)")
assert E["in_memory"].startswith("SYSTEM, IN MEMORY.") and "(12.1)" in E["in_memory"]
assert E["edit_system"].rstrip().endswith('return "\\n".join(head + [f"{i}. {r}" for i, r in enumerate(kept, 1)]) + "\\n"')
assert E["arms"].rstrip().endswith("return out") and E["bench_loop"].rstrip().endswith("return answers")
assert "gen.SYSTEM, gen._client = kit_system, kit_client" in E["bench_loop"] and "finally:" in E["bench_loop"]
assert E["trainset"].rstrip().endswith('"""') and E["same_test"].rstrip().endswith('strings(KIT / GEN, "SYSTEM"))')
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit, imported: the gate, the bench, the packer, the prices
sys.path[:0] = [str(KIT / "evals"), str(KIT)]


def load(path: Path, name: str):
    """A kit module loaded from its file under a name of the build's own, so nothing on sys.path is shadowed."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import run_eval as rv  # noqa: E402
import prompt_bench as bench  # noqa: E402
from shared import local_corpus, prices  # noqa: E402

assert bench.run_eval is rv
prices.PROFILE = "gcp"            # list prices, whatever DOCUMIND_PROFILE the build's own shell carries: the page prices a lane
budget = load(KIT / "services" / "rag-api" / "context_budget.py", "context_budget_lesson33")
schemas = load(KIT / "services" / "rag-api" / "schemas.py", "schemas_lesson33")
decide = load(KIT / "evals" / "decide.py", "decide_lesson33")

GOLDEN = rv.load_golden()
BY_ID = {r["id"]: r for r in GOLDEN}
N_ROWS, N_ANS = len(GOLDEN), sum(r["answerable"] for r in GOLDEN)
SHAPE_N = {s: sum(r["shape"] == s for r in GOLDEN) for s in bench.SHAPES}
REFUSAL = [r["id"] for r in GOLDEN if r["shape"] == "refusal"]
ISO = [r["id"] for r in GOLDEN if r["shape"] == "isolation"]
assert (N_ROWS, N_ANS, len(REFUSAL), len(ISO)) == (65, 47, 8, 11), (N_ROWS, N_ANS, len(REFUSAL), len(ISO))
assert all(not BY_ID[i]["answerable"] and not BY_ID[i].get("must_not_contain") for i in REFUSAL)
for r in GOLDEN:   # the desk's port writes these as Python's repr does: in single quotes, or double when one holds an apostrophe
    for s in r.get("must_contain", []) + r.get("must_not_contain", []):
        assert re.fullmatch(r"[ -~]+", s) and '"' not in s and "\\" not in s, (r["id"], s)
        assert repr(s) == (f'"{s}"' if "'" in s else f"'{s}'"), s

gen_src = (KIT / GEN).read_text(encoding="utf-8")
K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(gen_src).body
     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
SYS_HEAD, SYS_RULES = bench.rules_of(K["SYSTEM"])
N_RULES = len(SYS_RULES)
assert N_RULES == 5 and K["DATED_RULE"].startswith("\n6. ") and SYS_RULES[2].startswith("If the context does not contain the answer")
mt_src = (KIT / MT).read_text(encoding="utf-8")
MT_SYSTEM = next(ast.literal_eval(n.value) for n in ast.parse(mt_src).body
                 if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SYSTEM")
assert MT_SYSTEM == K["SYSTEM"]
PROMPT_SHA = bench.prompt_sha(K["SYSTEM"], K["DATED_RULE"])
assert PROMPT_SHA == hashlib.sha256((K["SYSTEM"] + K["DATED_RULE"]).encode("utf-8")).hexdigest()
REGISTRY = json.loads((KIT / "services" / "rag-api" / "prompt_versions.json").read_text(encoding="utf-8"))["versions"]
cfg = (KIT / "services" / "rag-api" / "config.py").read_text(encoding="utf-8")
PROMPT_LABEL = "{}@{}".format(re.search(r'prompt_id: str = "([\w-]+)"', cfg).group(1), re.search(r'prompt_version: str = "(\w+)"', cfg).group(1))
assert REGISTRY[PROMPT_LABEL] == PROMPT_SHA, "the kit's prompt is the one its version names"
GEN_MODEL = re.search(r'generator_model: str = "([^"]+)"', cfg).group(1)
MAX_CTX = int(re.search(r"max_context_tokens: int = (\d+)", cfg).group(1))
MAX_ANS = int(re.search(r"max_answer_tokens: int = (\d+)", cfg).group(1))
assert (GEN_MODEL, MAX_CTX, MAX_ANS) == ("gemini-3.6-flash", 8000, 2048)
LITE = "gemini-3.1-flash-lite"
assert LITE in prices.PRICES and prices.USD_INR == 85
TOP_K = int(re.search(r'"top_k": (\d+)\}\)\.encode\(\)', (KIT / RE_).read_text(encoding="utf-8")).group(1))
assert TOP_K == bench.TOP_K == 6 and bench.KIT_LEVEL == "LOW" and 'thinking_level="LOW"' in gen_src
UI_TOPK = int(re.search(r'"top_k": (\d+), "brain": "ui"', (KIT / "services" / "frontend" / "chat.py").read_text(encoding="utf-8")).group(1))
assert UI_TOPK == 5 and 'BRAINS = ("direct",' in (KIT / "services" / "frontend" / "chat.py").read_text(encoding="utf-8")
assert "No response_schema here on purpose" in gen_src and "def generate_stream(" in gen_src
TH = rv.THRESHOLDS
MAIN_SRC = (KIT / "services" / "rag-api" / "main.py").read_text(encoding="utf-8")
assert 'row = usage_row(req, user, 0, 0, 0, latency, bool(out), None, "passages"' in MAIN_SRC   # /v1/passages: a row, no tokens
assert "search_query(" not in MAIN_SRC.split('@app.post("/v1/passages")', 1)[1].split("def ", 2)[1]   # the passages route searches the question
MK_ALL = (KIT / "Makefile").read_text(encoding="utf-8") + "".join(p.read_text(encoding="utf-8") for p in (KIT / "mk").glob("*.mk"))
for target in ("eval-live", "bench", "tenant-backend"):
    assert re.search(rf"^{target}:", MK_ALL, re.M), target
assert "evals/reports/" in (KIT / ".gitignore").read_text(encoding="utf-8")

# ------------------------------------------------------------------ the Rs 0 lane: every golden row's pool and prompt (lesson 2.6's method)
CHUNK = {c["chunk_id"]: c for t in sorted({r["tenant"] for r in GOLDEN}) for c in local_corpus.chunks_for(t)}
dt = decide._tools()
true_rank, last = dt._lexical_rank, {}


def recorder(q, rows):
    """documind_tools._lexical_rank, kept: LocalLane calls it, and the ranked list is read for the generator's top six."""
    last["ranked"], last["idf"] = got = true_rank(q, rows)
    return got


def prompt_tokens(question: str, chunks: list) -> int:
    """generate()'s prompt for this pool: _budget(), _pack() and the prompt line, counted by estimate_tokens (len // 4)."""
    fit = budget.TokenBudget.fit(MAX_CTX, f"{K['SYSTEM']}{K['DATED_RULE']}\n\nContext:\n\n\nQuestion: {question}",
                                 budget.estimate_tokens, answer=MAX_ANS)
    context, packed, _ = budget.pack_chunks(chunks, fit.chunks, budget.estimate_tokens)
    dated = K["DATED_RULE"] if any(c.get("effective_from") for c in packed) else ""
    return budget.estimate_tokens(f"{K['SYSTEM']}{dated}\n\nContext:\n{context}\n\nQuestion: {question}")


def passage(n: int, c: dict) -> dict:
    """One chunk in /v1/passages' shape (main.py's passages()): its number, id, source, page, type, kind, section, text."""
    return {"n": n, "chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "page": c["page_start"],
            "doc_type": c["doc_type"], "kind": c.get("kind", "text"), "section": c.get("section"), "text": c["text"]}


lane0 = decide.LocalLane(sorted({r["tenant"] for r in GOLDEN}), 0.0)
TOK, POOL6, RANKED = {}, {}, {}
dt._lexical_rank = recorder
try:
    for r in GOLDEN:
        lane0.pool(r["question"], r["tenant"], 5)
        RANKED[r["id"]] = [x[3]["chunk_id"] for x in last["ranked"]]
        top = [dict(CHUNK[i]) for i in RANKED[r["id"]][:TOP_K]]
        TOK[r["id"]] = prompt_tokens(r["question"], top)
        POOL6[r["id"]] = [passage(n, c) for n, c in enumerate(top, 1)]
finally:
    dt._lexical_rank = true_rank
assert all(len(p) == TOP_K for p in POOL6.values())
from shared import documind_corpus as dcorp  # noqa: E402

assert not any(c.get("effective_from") for c in CHUNK.values())       # no corpus document declares a date: no golden prompt holds rule 6
DEMO_DATED = sorted(p.name for p in (KIT / "evals" / "demo").glob("*.md") if dcorp._EFFECTIVE.search(p.read_text(encoding="utf-8")[:3000]))
assert len(DEMO_DATED) == 3 and "hr_policy_2026_v2.md" in DEMO_DATED, DEMO_DATED
TOK_MAX = max(TOK.values())
assert TOK_MAX < MAX_CTX          # every golden pool fits the budget whole on this lane: the pool is the prompt's evidence
# and on any lane: six of the corpus's largest chunks, with SYSTEM, DATED_RULE and the longest question, still fit
BIG6 = sorted(CHUNK.values(), key=lambda c: len(budget.source_header(1, c)) + len(c["text"]), reverse=True)[:TOP_K]
LONGEST_Q = max((r["question"] for r in GOLDEN), key=len)
WORST = budget.estimate_tokens(f"{K['SYSTEM']}{K['DATED_RULE']}\n\nContext:\n"
                               + "\n\n".join(f"{budget.source_header(n, c)}\n{c['text']}" for n, c in enumerate(BIG6, 1))
                               + f"\n\nQuestion: {LONGEST_Q}")
assert TOK_MAX <= WORST < MAX_CTX, (WORST, MAX_CTX)


def rs(model: str, tin: int, tout: int) -> float:
    """One call at list price, in rupees (shared/prices.py)."""
    return prices.inr(prices.usd(model, tin, tout))


TYPICAL_OUT = 300                 # the course's typical answer (lessons 4.3, 4.4 and 11.6): 300 tokens out
ANS_IDS = [r["id"] for r in GOLDEN if r["answerable"]]
FIX_ROW_TOK = max(TOK[i] for i in ANS_IDS)                  # a fix's row priced at the largest answerable prompt
REF_TOK = sum(TOK[i] for i in REFUSAL)
FIX_CALLS = 2 * (1 + len(REFUSAL))                          # two arms, the row and the eight refusal rows, one run
FIX_IN_TOK = 2 * (FIX_ROW_TOK + REF_TOK)
COST = {
    "eval_in": sum(rs(GEN_MODEL, TOK[r["id"]], 0) for r in GOLDEN),
    "eval_typ": sum(rs(GEN_MODEL, TOK[r["id"]], TYPICAL_OUT) for r in GOLDEN),
    "eval_cap": sum(rs(GEN_MODEL, TOK[r["id"]], MAX_ANS) for r in GOLDEN),
    "fix_in": rs(GEN_MODEL, FIX_IN_TOK, 0),
    "fix_typ": rs(GEN_MODEL, FIX_IN_TOK, TYPICAL_OUT * FIX_CALLS),
    "fix_cap": rs(GEN_MODEL, FIX_IN_TOK, MAX_ANS * FIX_CALLS),
    "lite_in": sum(rs(LITE, TOK[i], 0) for i in ANS_IDS if BY_ID[i]["shape"] in ("lookup", "join")),
    "lite_cap": sum(rs(LITE, TOK[i], MAX_ANS) for i in ANS_IDS if BY_ID[i]["shape"] in ("lookup", "join")),
    "guard_in": rs(GEN_MODEL, 2 * REF_TOK, 0),
    "guard_cap": rs(GEN_MODEL, 2 * REF_TOK, MAX_ANS * 2 * len(REFUSAL)),
    "ans_in": sum(rs(GEN_MODEL, 2 * TOK[i], 0) for i in ANS_IDS if BY_ID[i]["shape"] in ("lookup", "join")),
    "ans_cap": sum(rs(GEN_MODEL, 2 * TOK[i], 2 * MAX_ANS) for i in ANS_IDS if BY_ID[i]["shape"] in ("lookup", "join")),
}
N_LITE = sum(1 for i in ANS_IDS if BY_ID[i]["shape"] in ("lookup", "join"))
assert N_LITE == SHAPE_N["lookup"] + SHAPE_N["join"] == 45


def need(rate: float, n: int) -> int:
    """The fewest rows of n that clear a rate threshold: live() compares k / n with the rate itself."""
    k = 0
    while k / n < rate:
        k += 1
    return k


N_UN = N_ROWS - N_ANS
NEED_CORRECT, NEED_REFUSED, NEED_ANSWERED = need(rv.THRESHOLDS["correct_rate"], N_ANS), need(rv.THRESHOLDS["refusal_rate"], N_UN), \
    need(rv.THRESHOLDS["answerable_rate"], N_ANS)
assert (NEED_CORRECT, NEED_REFUSED, NEED_ANSWERED) == (32, 17, 38)
COST["all_in"] = COST["eval_in"] + 3 * COST["fix_in"]
COST["all_typ"] = COST["eval_typ"] + 3 * COST["fix_typ"]
COST["all_cap"] = COST["eval_cap"] + 3 * COST["fix_cap"]
assert abs(COST["eval_in"] - 17.57) < 0.005 and abs(COST["eval_cap"] - 102.43) < 0.005, COST   # lesson 2.6's figures, same pools


def money(x: float) -> str:
    return f"{x:,.2f}"


# ------------------------------------------------------------------ the three recipes: one rule a failure kind, each run beside the refusal rows
RECIPES = [
    {"var": "FIX1", "kind": "refused", "label": "Refused with the clause in the pool",
     "rule": "If a source answers the question in other words, or states a rule that covers the case asked about, answer from it and cite it."},
    {"var": "FIX2", "kind": "join", "label": "Half of a two-part question",
     "rule": "If the question asks more than one thing, answer every part, each from the source that states it, and cite each source."},
    {"var": "FIX3", "kind": "lookup", "label": "The answer without its figure",
     "rule": "Begin the answer with the figure, name or term that answers the question, written as the source writes it."},
]
OTHER_RULES = {   # two more a failing row may call for; this page runs neither (step 9 says why)
    "cite": "Every answer with answerable=true cites at least one source, with the words it relied on.",
    "refuse": "If no source states what the question asks for, set answerable=false, even when a source covers a nearby subject.",
}
for rule in [x["rule"] for x in RECIPES] + list(OTHER_RULES.values()):
    assert "\n" not in rule and not set(rule) & set("'\"$`\\#;") and len(rule.split()) <= 25, rule
    assert bench.rules_of(bench.edit_system(K["SYSTEM"], add=[rule]))[1][-1] == rule


# ------------------------------------------------------------------ address(): where a failing row's fix lives (the read cell's rule, and the desk's)
ADDRESS_DEF = r'''def address(row, rec):
    """Where the fix for one eval row lives, from its golden row and its report record: (place, reason)."""
    why = rec.get("why") or ""
    if rec.get("outcome") != "ok":
        return "the code", "no answer came back to judge: " + (why or rec.get("outcome", ""))
    if why.startswith("answer contained"):
        return ("the ledger" if row["shape"] == "version" else "tenancy"), why
    if not row["answerable"]:
        if rec.get("pass"):
            return "none", "refused, as it should"
        return "the prompt", "answered a question no document answers"
    flags = sorted({c.get("check") for c in rec.get("cites") or []} & {"elsewhere", "absent", "substituted"})
    if rec.get("pass"):
        return ("the prompt", "passed, but a quote is " + " and ".join(flags)) if flags else ("none", "passed")
    anchors = rec.get("anchors")
    if anchors is None:
        return "unread", "no pool was read for it"
    missing = [a for a, found in anchors.items() if not found]
    if missing:
        return "retrieval", "not in the pool: " + ", ".join(missing)
    if why.startswith("cited no "):
        return "media", why
    if "ledger" in why:
        return "the ledger", why
    if why == "refused" or why.startswith("answered without"):
        return "the prompt", why + ", every anchor in the pool"
    return "tenancy", why'''
NS: dict = {}
exec(compile(ADDRESS_DEF, "address", "exec"), NS)
address = NS["address"]
PLACES = ("the prompt", "retrieval", "the code", "media", "tenancy", "the ledger", "unread", "none")

# ------------------------------------------------------------------ the failure desk: golden rows, the kit's chunks, illustrative replies
DASH = str.maketrans({"\u2014": "-", "\u2013": "-"})      # the corpus's dashes, shown as the page's hyphens


def chunk(cid: str) -> dict:
    return CHUNK[cid]


def rank_fill(rid: str, have: list, n: int, skip=lambda c: False) -> list:
    """The row's own ranked chunks on the Rs 0 lane, after the ones given, until there are n."""
    out = list(have)
    for cid in RANKED[rid]:
        if len(out) >= n:
            break
        if cid not in out and not skip(CHUNK[cid]):
            out.append(cid)
    return out


def flat(s: str) -> str:
    return " ".join(str(s or "").split())


def pool_of(ids: list) -> list:
    """A desk pool: /v1/passages' shape with the header generate() would write over each passage; dashes as hyphens."""
    out = []
    for n, cid in enumerate(ids, 1):
        p = passage(n, chunk(cid))
        p["head"] = budget.source_header(n, chunk(cid)).translate(DASH)
        p["text"] = p["text"].translate(DASH)
        p["section"] = (p["section"] or "").translate(DASH) or None
        out.append(p)
    return out


def cut(p: dict, needles: list) -> dict:
    """What the page carries of a desk passage: its id, source and header, and its text from the first needle it holds to
    the last (the figures, anchors and quotes), with a margin, whitespace collapsed; pre and post mark what was cut."""
    t = flat(p["text"])
    low = t.lower()
    hits = [(low.find(x.lower()), len(x)) for x in needles if x and low.find(x.lower()) >= 0]
    if len(t) <= 420:                                   # a handbook clause: shown whole
        a, b = 0, len(t)
    else:
        a, b = ((max(0, min(h for h, _ in hits) - 90), min(len(t), max(h + n for h, n in hits) + 120)) if hits else (0, 220))
        a = t.rfind(" ", 0, a) + 1 if a else 0          # on word boundaries
        b = len(t) if t.find(" ", b) < 0 else t.find(" ", b)
    return {"chunk_id": p["chunk_id"], "source_uri": p["source_uri"], "head": p["head"], "text": t[a:b], "pre": a > 0, "post": b < len(t)}


def cite(cid: str, quote: str) -> dict:
    """A resolved citation as /v1/query returns it: the chunk's id, source, page and kind, and the words quoted."""
    c = chunk(cid)
    assert flat(quote).lower() in flat(c["text"].translate(DASH)).lower() or quote.startswith("During probation"), (cid, quote)
    return {"chunk_id": cid, "source_uri": c["source_uri"], "page": c["page_start"], "kind": c.get("kind", "text"),
            "quote": quote, "score": 0.9}


HB = "acme:hr_policy_2026#"
MAT = "acme:maternity_benefit_amendment_act_2017#p2-0"
MAT61 = "acme:maternity_benefit_act_1961#p5-0"
IRC = "acme:industrial_relations_code_2020#p17-0"
assert "twenty-six weeks of which not more than eight weeks" in flat(chunk(MAT)["text"])
assert "maximum period for which any woman shall be entitled to maternity benefit shall be twelve weeks" in flat(chunk(MAT61)["text"])
assert "three hundred or more than three hundred workers" in flat(chunk(IRC)["text"])
for cid, words in ((HB + "FIN-02", "Above that, the CFO approves."), (HB + "LV-07", "capped at 45 days"),
                   (HB + "NP-03", "serves a notice period of 60 days"), (HB + "LV-01", "accrues at 1.75 days per completed month"),
                   (HB + "LV-01", "A maximum of 30 days may be carried forward"), (HB + "PB-02", "During probation the notice period is 15 days"),
                   ("acme:msa_acme_2026#MSA-04", "terminate for convenience on 90 days written notice")):
    assert words in flat(chunk(cid)["text"]), (cid, words)

CASES = [
    {"key": "refused", "label": "Refused, the clause in the pool", "row": "lk-08",
     "pool_in": [HB + "FIN-02"], "fill": 3,
     "reply": {"answerable": False, "confidence": "low",
               "answer": "The handbook does not say who approves a purchase of Rs 3,00,000.", "cites": []},
     "note": "FIN-02 sends every purchase above Rs 2,00,000 to the CFO. The reply needed one comparison the question leaves "
             "to the reader, and declined instead."},
    {"key": "half", "label": "Half of a two-part question", "row": "jn-03",
     "pool_in": [HB + "LV-07", HB + "NP-03"], "fill": 3,
     "reply": {"answerable": True, "confidence": "high",
               "answer": "A confirmed E3 serves a notice period of 60 days [2].",
               "cites": [(HB + "NP-03", "serves a notice period of 60 days")]},
     "note": "Two clauses, two figures: LV-07 caps encashment at 45 days and NP-03 sets 60 days of notice. The reply "
             "answers the second question and drops the first. Type the missing half into the reply and the row passes."},
    {"key": "neighbour", "label": "The neighbouring figure", "row": "lk-03",
     "pool_in": [HB + "LV-01"], "fill": 3,
     "reply": {"answerable": True, "confidence": "high",
               "answer": "Earned leave accrues at 1.75 days per completed month [1].",
               "cites": [(HB + "LV-01", "Earned leave accrues at 1.75 days per completed month")]},
     "note": "LV-01 holds two figures: 1.75 days accrue a month, and at most 30 days carry forward. The reply cites the "
             "right clause and gives the wrong one of its two figures."},
    {"key": "overanswer", "label": "An answer where none exists", "row": "rf-06",
     "pool_in": [MAT], "fill": 3,
     "reply": {"answerable": True, "confidence": "medium",
               "answer": "The Maternity Benefit Act provides twenty-six weeks [1].",
               "cites": [(MAT, "twenty-six weeks of which not more than eight weeks")]},
     "note": "The golden row's own note: the Act provides no paternity leave, and a model that answers with a figure fails "
             "this row. The words quoted are real; the answer is to a question nobody asked."},
    {"key": "miss", "label": "The clause never arrived", "row": "lk-12",
     "pool_in": ["acme:msa_acme_2026#MSA-04", HB + "NP-03", HB + "PB-02"],
     "pool_out": [HB + "NP-03", HB + "PB-02", HB + "LV-07"], "clause_in": False,
     "reply": {"answerable": True, "confidence": "medium",
               "answer": "Termination needs a notice period of 60 days [1].",
               "cites": [(HB + "NP-03", "serves a notice period of 60 days")]},
     "note": "Unticked, the pool holds the handbook's notice clauses and none of the MSA: 60 days is a real figure from "
             "the wrong document. Ticked, MSA-04 is in the pool, and the same reply becomes the prompt's failure."},
    {"key": "cutoff", "label": "Cut off twice", "row": "jn-08",
     "pool_in": [MAT61, MAT], "fill": 3, "status": 502,
     "reply": {"answerable": True, "confidence": "high",
               "answer": "The 2017 amendment raised the maximum from twelve weeks [1] to twenty-six weeks [2].",
               "cites": [(MAT61, "shall be twelve weeks"), (MAT, "twenty-six weeks of which not more than eight weeks")]},
     "note": "The second live eval (7 Sept 2026) scored fourteen cut-off answers as refusals. generate() asks once more "
             "with three times the room, and an answer it still cannot parse is a 502, never a refusal. Tick 'came back' "
             "to see the reply it might have given."},
    {"key": "spelling", "label": "Three hundred, written 300", "row": "lk-23",
     "pool_in": [IRC], "fill": 3,
     "reply": {"answerable": True, "confidence": "high",
               "answer": "The standing orders chapter applies to every industrial establishment with 300 or more workers [1].",
               "cites": [(IRC, "three hundred or more than three hundred workers")]},
     "note": "The third live eval (7 Sept 2026) scored this answer as wrong: the row says three hundred. The fix went into "
             "the gate, not the prompt: normalise() reads both spellings as one figure."},
    {"key": "quote", "label": "The right answer, the wrong quote", "row": "lk-06",
     "pool_in": [HB + "NP-03", HB + "PB-02"], "fill": 3,
     "reply": {"answerable": True, "confidence": "high",
               "answer": "A confirmed E3 serves a notice period of 60 days [1].",
               "cites": [(HB + "NP-03", "During probation the notice period is 15 days for either side.")]},
     "note": "The answer and its citation are right, and the gate passes it. The quote is PB-02's words filed under NP-03: "
             "rule 5's failure, which only the passage check sees (lesson 3.6 measures quotes across the set)."},
]
assert [c["row"] for c in CASES] == ["lk-08", "jn-03", "lk-03", "rf-06", "lk-12", "jn-08", "lk-23", "lk-06"]


def needles_of(row: dict, case: dict) -> list:
    return list(row.get("must_contain", [])) + list(row.get("must_retrieve", [])) + [q for _, q in case["reply"]["cites"]]


DESK = []
for case in CASES:
    row = BY_ID[case["row"]]
    pin = case["pool_in"] if "fill" not in case else rank_fill(case["row"], case["pool_in"], case["fill"])
    pout = case.get("pool_out")
    if pout is None and row.get("must_retrieve"):
        anchor_doc = lambda c, row=row: any(a.lower() in f"{c['chunk_id']}\n{c['source_uri']}\n{c['text']}".lower()
                                            for a in row["must_retrieve"])
        pout = rank_fill(case["row"], [], len(pin), skip=anchor_doc)
    DESK.append({
        "key": case["key"], "label": case["label"], "note": case["note"], "needles": needles_of(row, case),
        "row": {k: row.get(k) for k in ("id", "shape", "tenant", "question", "answerable", "must_contain", "must_not_contain",
                                        "must_retrieve", "must_cite_kind") if k in row},
        "pool_in": pool_of(pin), "pool_out": pool_of(pout) if pout else None,
        "clause_in": case.get("clause_in", True), "status": case.get("status", 200), "cite_on": True,
        "reply": {"answerable": case["reply"]["answerable"], "confidence": case["reply"]["confidence"],
                  "answer": case["reply"]["answer"], "cites": [cite(cid, q) for cid, q in case["reply"]["cites"]]},
    })
for d in DESK:     # the dash swap changes no quote check: every quote sits away from a heading's dash
    for key in ("pool_in", "pool_out"):
        for p in d[key] or []:
            raw = passage(p["n"], chunk(p["chunk_id"]))
            for c in d["reply"]["cites"]:
                assert rv.quote_check(c, [raw]) == rv.quote_check(c, [p]), (d["key"], c["quote"])


def desk_record(d: dict, answer: str, answerable: bool, cite_on: bool, clause_in: bool, status: int) -> dict:
    """What live() and passage_checks() would write for this reply: the verdict, the cites with their checks, the anchors."""
    row = d["row"]
    pool = d["pool_in"] if (clause_in or not d["pool_out"]) else d["pool_out"]
    body = ({"answer": answer, "citations": [dict(c) for c in d["reply"]["cites"]] if cite_on else [], "answerable": answerable,
             "confidence": d["reply"]["confidence"]} if status == 200 else {})
    v = rv.row_verdict(row, status, body, None, {}, "")     # no ledger, no manifest: the checks the desk cannot hold are skipped
    rec = {"outcome": v["outcome"], "pass": bool(v["pass"]), "why": v["why"]}
    v_out = {k: v[k] for k in ("outcome", "why", "answered", "refused", "cited", "valid", "kind_ok", "contained", "leaks", "stale")}
    v_out["pass"] = bool(v["pass"])
    if status == 200 and v["outcome"] == "ok":
        rec["answerable"] = answerable
        rec["cites"] = [dict(c) for c in body["citations"]]
        if row["answerable"]:
            for c in rec["cites"]:
                c["check"] = rv.quote_check(c, pool)
            rec["anchors"] = rv.anchors_found(row, pool)
    place, reason = address(row, rec)
    return {"v": v_out, "checks": [c.get("check") for c in rec.get("cites", [])], "anchors": rec.get("anchors"),
            "place": place, "reason": reason}


DEFAULT = {d["key"]: desk_record(d, d["reply"]["answer"], d["reply"]["answerable"], True, d["clause_in"], d["status"]) for d in DESK}
WANT = {"refused": ("the prompt", "refused"), "half": ("the prompt", "answered without ['45', '60']"),
        "neighbour": ("the prompt", "answered without ['30']"), "overanswer": ("the prompt", "answered, should refuse"),
        "miss": ("retrieval", "answered without ['90']"), "cutoff": ("the code", "HTTP 502"),
        "spelling": ("none", ""), "quote": ("the prompt", "")}
for k, (place, why) in WANT.items():
    assert (DEFAULT[k]["place"], DEFAULT[k]["v"]["why"]) == (place, why), (k, DEFAULT[k])
assert DEFAULT["spelling"]["v"]["pass"] and DEFAULT["quote"]["v"]["pass"] and DEFAULT["quote"]["checks"] == ["elsewhere"]
assert DEFAULT["miss"]["anchors"] == {"MSA-04": False, "msa_acme_2026": False}
assert all(DEFAULT[k]["anchors"] and all(DEFAULT[k]["anchors"].values()) for k in ("refused", "half", "neighbour", "quote", "spelling"))
MISS_IN = desk_record(DESK[4], DESK[4]["reply"]["answer"], True, True, True, 200)
assert (MISS_IN["place"], MISS_IN["v"]["why"]) == ("the prompt", "answered without ['90']")      # the toggle's lesson
HALF_FIXED = desk_record(DESK[1], "LV-07 caps encashment at 45 days, and a confirmed E3 serves 60 days [1, 2].", True, True, True, 200)
assert HALF_FIXED["v"]["pass"] and HALF_FIXED["place"] == "none"
assert rv.contains("300 or more workers", "three hundred") and not rv.contains("160 days", "60")

PLACE_TEXT = {
    "the prompt": "This lesson. The evidence reached the model, and the reply mishandled it: one new rule in SYSTEM, tried "
                  "in the bench beside the refusal rows (step 7).",
    "retrieval": "Module 2. No instruction can make the model answer from a passage it was never shown: lessons 2.2, 2.3 "
                 "and 2.5 widen, reorder and rewrite the search.",
    "the code": "Lessons 3.5 and 3.7. No answer came back, so there is nothing for a prompt line to improve.",
    "media": "Lesson 7.5. A figure or segment citation needs the media in the pool and the image beside the prompt.",
    "tenancy": "Lessons 4.6 and 4.7. Another tenant's figure or passage in an answer is an isolation fault, not wording.",
    "the ledger": "Lesson 1.7. A retired version's figure or passage is the ledger's to keep out.",
    "unread": "Run the eval again with DOCUMIND_EVAL_PASSAGES=1: without the pool, a refusal and a retrieval miss look the same.",
    "none": "Nothing to fix.",
}
RECIPE_OF = {"refused": RECIPES[0]["rule"], "join": RECIPES[1]["rule"], "lookup": RECIPES[2]["rule"],
             "cite": OTHER_RULES["cite"], "refuse": OTHER_RULES["refuse"]}

# ------------------------------------------------------------------ the desk's JavaScript: the kit's rules, ported; then node holds them equal
PORT_JS = r"""var SMALL = D.small, SCALE = D.scale, WORDS = D.words;
var NUMWORDS = new RegExp('(?<![\\p{L}\\p{N}_])(?:(?:' + WORDS + ')(?:[\\s-]+(?:' + WORDS + '))*)(?![\\p{L}\\p{N}_])', 'gu');
function toInt(run){ var total = 0, current = 0;
  run.split(/[\s-]+/).forEach(function(w){
    if (Object.prototype.hasOwnProperty.call(SMALL, w)) current += SMALL[w];
    else if (w === 'hundred') current = (current || 1) * 100;
    else if (Object.prototype.hasOwnProperty.call(SCALE, w)) { total += (current || 1) * SCALE[w]; current = 0; } });
  return total + current; }
function normalise(text){ var t = String(text).toLowerCase().split(',').join('').split('-').join(' ');
  [' per cent', 'per cent', ' percent', 'percent'].forEach(function(s){ t = t.split(s).join('%'); });
  return t.replace(NUMWORDS, function(m){ return String(toInt(m)); }); }
function esc(s){ return s.replace(/[\\^$.*+?()[\]{}|\/]/g, '\\$&'); }
function contains(text, want){ var w = normalise(want).trim(); if (!w) return false;
  return new RegExp('(?<![\\p{L}\\p{N}_.])' + esc(w) + '(?![\\p{L}\\p{N}_]|\\.\\p{Nd})', 'u').test(normalise(text)); }
function pyrepr(s){ return s.indexOf("'") >= 0 ? '"' + s + '"' : "'" + s + "'"; }
function pylist(a){ return a == null ? 'None' : '[' + a.map(pyrepr).join(', ') + ']'; }
function isStr(x){ return typeof x === 'string'; }
function validateBody(b){
  if (!b || typeof b !== 'object' || Array.isArray(b)) return 'body is not an object';
  var kinds = [['answer', isStr, 'str'], ['citations', Array.isArray, 'list'], ['answerable', function(x){ return typeof x === 'boolean'; }, 'bool']];
  for (var i = 0; i < kinds.length; i++) if (!kinds[i][1](b[kinds[i][0]])) return kinds[i][0] + ' missing or not a ' + kinds[i][2];
  if (['high', 'medium', 'low'].indexOf(b.confidence) < 0) return 'confidence not one of high / medium / low';
  for (var j = 0; j < b.citations.length; j++){ var c = b.citations[j];
    if (!c || typeof c !== 'object' || !['chunk_id', 'source_uri', 'quote'].every(function(k){ return isStr(c[k]) && c[k]; }))
      return 'citation ' + j + ' lacks chunk_id / source_uri / quote'; }
  return null; }
function judge(row, cites){ var valid = true, why = [];
  cites.forEach(function(c){ var cid = c.chunk_id || '', uri = c.source_uri || '';
    if (cid.indexOf(row.tenant + ':') !== 0){ valid = false; why.push('chunk ' + cid.slice(0, 40) + ' is not ' + row.tenant + "'s"); }
    var parts = uri.split('/'), obj = uri.indexOf('gs://') === 0 ? (parts.length > 3 ? parts.slice(3).join('/') : parts[parts.length - 1]) : uri;
    if (obj.split('/')[0] !== row.tenant){ valid = false; why.push('source ' + uri.slice(0, 60) + ' is not under ' + row.tenant + '/'); } });
  return {valid: valid, why: why}; }
function rowVerdict(row, status, body){
  var v = {outcome: 'ok', pass: false, why: '', answered: false, refused: false, cited: false, valid: null, kind_ok: null, contained: null, leaks: [], stale: []};
  if (status !== 200){ var err = body && typeof body === 'object' && !Array.isArray(body) ? body.error : null;
    v.outcome = (status === 401 || status === 403) ? 'denied' : 'error'; v.why = 'HTTP ' + status + (err ? ' ' + err : ''); return v; }
  var problem = validateBody(body); if (problem){ v.outcome = 'malformed'; v.why = problem; return v; }
  var text = normalise(body.answer);
  (row.must_not_contain || []).forEach(function(never){ if (contains(text, never)){
    v[row.shape === 'version' ? 'stale' : 'leaks'].push(row.id + ': answer contained ' + pyrepr(never)); v.why = 'answer contained ' + pyrepr(never); } });
  if (!row.answerable){ if (body.answerable) v.why = 'answered, should refuse'; else { v.refused = true; v.pass = !v.why; } return v; }
  if (!body.answerable){ v.why = 'refused'; return v; }
  v.answered = true; v.cited = body.citations.length > 0; v.valid = false;
  if (v.cited){ var j = judge(row, body.citations); v.valid = j.valid; if (!j.valid) v.why = j.why.join('; '); }
  else v.why = 'answered without a citation';
  if (row.must_cite_kind){ var want = row.must_cite_kind;
    v.kind_ok = body.citations.some(function(c){ return (Object.prototype.hasOwnProperty.call(c, 'kind') ? c.kind : 'text') === want; });
    if (!v.kind_ok) v.why = 'cited no ' + want; }
  v.contained = (row.must_contain || []).every(function(w){ return contains(text, w); });
  if (!v.contained) v.why = 'answered without ' + pylist(row.must_contain);
  v.pass = !!(v.contained && v.valid && v.kind_ok !== false && v.why.indexOf('answer contained') !== 0);
  return v; }
function flat(s){ return String(s || '').replace(/\s+/g, ' ').trim().toLowerCase(); }
function quoteCheck(c, pool){
  var own = null; for (var i = 0; i < pool.length; i++) if (pool[i].chunk_id && pool[i].chunk_id === c.chunk_id){ own = pool[i]; break; }
  if (!own) return 'unread';
  var quote = c.quote || '', text = own.text || '';
  if (flat(quote) === flat(text.slice(0, 500))) return 'substituted';
  var words = flat(quote); if (words.slice(-3) === '...') words = words.slice(0, -3).replace(/\s+$/, '');
  if (!words) return 'absent';
  if (flat(text).indexOf(words) >= 0) return 'own';
  for (var k = 0; k < pool.length; k++) if (pool[k] !== own && flat(pool[k].text).indexOf(words) >= 0) return 'elsewhere';
  return 'absent'; }
function anchorsFound(row, pool){
  var hay = pool.map(function(p){ return (p.chunk_id || '') + '\n' + (p.source_uri || '') + '\n' + (p.text || ''); }).join('\n').toLowerCase();
  var out = {}; (row.must_retrieve || []).forEach(function(a){ out[a] = hay.indexOf(a.toLowerCase()) >= 0; }); return out; }
function address(row, rec){
  var why = rec.why || '';
  if (rec.outcome !== 'ok') return ['the code', 'no answer came back to judge: ' + (why || rec.outcome || '')];
  if (why.indexOf('answer contained') === 0) return [row.shape === 'version' ? 'the ledger' : 'tenancy', why];
  if (!row.answerable){ if (rec.pass) return ['none', 'refused, as it should']; return ['the prompt', 'answered a question no document answers']; }
  var flags = []; (rec.cites || []).forEach(function(c){ if (['elsewhere', 'absent', 'substituted'].indexOf(c.check) >= 0 && flags.indexOf(c.check) < 0) flags.push(c.check); });
  flags.sort();
  if (rec.pass) return flags.length ? ['the prompt', 'passed, but a quote is ' + flags.join(' and ')] : ['none', 'passed'];
  var anchors = rec.anchors; if (anchors == null) return ['unread', 'no pool was read for it'];
  var missing = Object.keys(anchors).filter(function(a){ return !anchors[a]; });
  if (missing.length) return ['retrieval', 'not in the pool: ' + missing.join(', ')];
  if (why.indexOf('cited no ') === 0) return ['media', why];
  if (why.indexOf('ledger') >= 0) return ['the ledger', why];
  if (why === 'refused' || why.indexOf('answered without') === 0) return ['the prompt', why + ', every anchor in the pool'];
  return ['tenancy', why]; }
function record(d, answer, answerable, citeOn, clauseIn, status){
  var row = d.row, pool = (clauseIn || !d.pool_out) ? d.pool_in : d.pool_out;
  var body = status === 200 ? {answer: answer, citations: citeOn ? d.reply.cites.map(function(c){ return Object.assign({}, c); }) : [],
                               answerable: answerable, confidence: d.reply.confidence} : {};
  var v = rowVerdict(row, status, body), rec = {outcome: v.outcome, pass: v.pass, why: v.why}, anchors = null;
  if (status === 200 && v.outcome === 'ok'){ rec.answerable = answerable; rec.cites = body.citations;
    if (row.answerable){ rec.cites.forEach(function(c){ c.check = quoteCheck(c, pool); }); anchors = anchorsFound(row, pool); rec.anchors = anchors; } }
  var a = address(row, rec);
  return {v: v, checks: (rec.cites || []).map(function(c){ return c.check || null; }), anchors: anchors, place: a[0], reason: a[1], pool: pool}; }"""

UI_JS = r"""var root = document.getElementById('fd'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var cases = $('fd-cases'), rowEl = $('fd-row'), poolEl = $('fd-pool'), out = $('fd-out'), ta = $('fd-answer');
  var cbOk = $('fd-ok'), cbAns = $('fd-ans'), cbCite = $('fd-cite'), cbIn = $('fd-in'), buttons = [], cur = 0;
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function line(parent, label, text, cls){ var p = el('p'); p.appendChild(el('b', '', label + ' ')); p.appendChild(el('span', cls || '', text)); parent.appendChild(p); return p; }
  function lab(cb, on){ cb.disabled = !on; cb.parentNode.className = on ? '' : 'off'; }
  function paint(){
    var d = D.cases[cur], r = record(d, ta.value, cbAns.checked, cbCite.checked, cbIn.checked, cbOk.checked ? 200 : 502);
    lab(cbAns, cbOk.checked); lab(cbCite, cbOk.checked && d.reply.cites.length > 0); lab(cbIn, !!d.pool_out); ta.disabled = !cbOk.checked;
    poolEl.textContent = ''; poolEl.appendChild(el('h5', '', 'The pool: ' + r.pool.length + ' passages'));
    r.pool.forEach(function(p){ var hit = (d.row.must_retrieve || []).some(function(a){ return ((p.chunk_id || '') + ' ' + (p.source_uri || '') + ' ' + p.text).toLowerCase().indexOf(a.toLowerCase()) >= 0; });
      var box = el('div', 'fd-p' + (hit ? ' hit' : '')); box.appendChild(el('i', '', p.head + (hit ? '  (holds an anchor)' : '')));
      box.appendChild(document.createTextNode((p.pre ? '... ' : '') + p.text + (p.post ? ' ...' : ''))); poolEl.appendChild(box); });
    out.textContent = '';
    var v = r.v, verdict = v.outcome !== 'ok' ? 'ERROR' : (v.pass ? 'pass' : 'FAIL');
    var p = line(out, 'The gate:', verdict + (v.why ? ' - ' + v.why : ''), 'fd-v ' + (v.pass ? 'ok' : 'no'));
    if (r.checks.length && r.checks[0]) line(out, 'Quote check:', r.checks.map(function(c, i){ return '[' + (i + 1) + '] ' + c; }).join(', '));
    if (r.anchors) line(out, 'Anchors in the pool:', Object.keys(r.anchors).map(function(a){ return a + (r.anchors[a] ? ' yes' : ' NO'); }).join(', '));
    var at = el('p'); at.appendChild(el('b', '', 'Where the fix lives: ')); at.appendChild(el('span', 'fd-at', r.place)); at.appendChild(document.createTextNode(' (' + r.reason + '). ' + D.places[r.place])); out.appendChild(at);
    var key = null;
    if (r.place === 'the prompt'){ if (!d.row.answerable) key = 'refuse'; else if (v.why === 'refused') key = 'refused';
      else if (v.why === 'answered without a citation') key = 'cite'; else if (v.why.indexOf('answered without') === 0) key = d.row.shape === 'join' ? 'join' : 'lookup'; }
    if (key){ var rp = el('p'); rp.appendChild(el('b', '', key === 'refuse' ? 'A rule toward refusing, guarded by the answerable rows (step 9):' : 'A rule to try in the bench:'));
      rp.appendChild(el('span', 'fd-rule', D.recipes[key])); out.appendChild(rp); }
    out.appendChild(el('p', '', d.note)); }
  function show(i){ cur = i; var d = D.cases[i];
    buttons.forEach(function(b, j){ b.setAttribute('aria-pressed', j === i ? 'true' : 'false'); });
    rowEl.textContent = ''; rowEl.appendChild(el('h5', '', d.row.id + ' - ' + d.row.shape + ' - ' + d.row.tenant));
    rowEl.appendChild(el('p', '', d.row.question));
    if (d.row.answerable){ line(rowEl, 'must contain:', d.row.must_contain.join(', ')); line(rowEl, 'must retrieve:', (d.row.must_retrieve || []).join(', ') || 'none'); }
    else line(rowEl, 'answerable:', 'no. The right reply is a refusal.');
    ta.value = d.reply.answer; cbAns.checked = d.reply.answerable; cbCite.checked = d.cite_on; cbIn.checked = d.clause_in; cbOk.checked = d.status === 200;
    $('fd-cite-q').textContent = d.reply.cites.length ? d.reply.cites.map(function(c){ return '"' + c.quote + '"'; }).join(', ') : '(this reply cites nothing)';
    paint(); }
  D.cases.forEach(function(d, i){ var b = el('button', 'fd-case'); b.type = 'button'; b.setAttribute('aria-pressed', 'false');
    b.appendChild(el('b', '', d.row.id)); b.appendChild(document.createTextNode(d.label));
    b.addEventListener('click', function(){ show(i); }); cases.appendChild(b); buttons.push(b); });
  [cbOk, cbAns, cbCite, cbIn].forEach(function(cb){ cb.addEventListener('change', paint); });
  ta.addEventListener('input', paint);
  show(0);"""

DESK_PAGE = [{**{k: v for k, v in d.items() if k not in ("needles", "pool_in", "pool_out", "reply")},
              "pool_in": [cut(p, d["needles"]) for p in d["pool_in"]],
              "pool_out": [cut(p, d["needles"]) for p in d["pool_out"]] if d["pool_out"] else None,
              "reply": {**d["reply"], "cites": [{k: c[k] for k in ("chunk_id", "source_uri", "kind", "quote")} for c in d["reply"]["cites"]]}}
             for d in DESK]
DESK_DATA = {"small": rv._SMALL, "scale": rv._SCALE, "words": rv._WORD, "cases": DESK_PAGE, "places": PLACE_TEXT, "recipes": RECIPE_OF}
assert rv._WORD == "|".join(list(rv._SMALL) + list(rv._SCALE))

# node runs the port over every case and its variants; every verdict, check, anchor set and address must equal the kit's
VARIANTS = {
    "refused": ["The CFO approves a purchase of Rs 3,00,000 [1].", "Above Rs 2,00,000 the function head approves."],
    "half": ["LV-07 caps encashment at 45 days, and a confirmed E3 serves 60 days [1, 2].", "Forty-five days are encashed; notice is sixty days."],
    "neighbour": ["A maximum of 30 days may be carried forward [1].", "Up to thirty days carry forward.", "130 days."],
    "overanswer": ["The Act provides no paternity leave.", "Twenty six weeks."],
    "miss": ["Either party may terminate for convenience on 90 days written notice [1].", "Ninety days' notice.", "190 days"],
    "cutoff": ["Twelve weeks became twenty-six weeks [1].", "twelve weeks"],
    "spelling": ["three hundred or more workers", "3000 workers", "300,000 workers", "300 or more"],
    "quote": ["Sixty days [1].", "60 days, or 160 for a director.", "6.0 days"],
}
COMBOS = []
for d in DESK:
    answers = [d["reply"]["answer"], ""] + VARIANTS[d["key"]]
    for answer in answers:
        for ans in (True, False):
            for cite_on in (True, False):
                for clause_in in ((True, False) if d["pool_out"] else (True,)):
                    for status in (200, 502):
                        COMBOS.append((d["key"], answer, ans, cite_on, clause_in, status))
KIT_RESULTS = []
for key, answer, ans, cite_on, clause_in, status in COMBOS:
    d, dp = next(x for x in DESK if x["key"] == key), next(x for x in DESK_PAGE if x["key"] == key)
    r = desk_record(dp, answer, ans, cite_on, clause_in, status)
    assert r == desk_record(d, answer, ans, cite_on, clause_in, status), (key, answer)   # the cut passages judge as the whole chunks do
    KIT_RESULTS.append(r)
TEXTS = ["300 or more", "three hundred", "Twelve weeks", "12 weeks", "set-on and set-off", "set on", "5.2%", "5.2 per cent",
         "twenty-six weeks", "Rs 1,84,500", "1.75", "one lakh twenty thousand", "two crore", "ninety-nine", "sixteen",
         "sixty", "eighteen hundred", "a hundred and five", "often tenth attention", "eight-hour day", "Forty Five", "ZERO"]
PAIRS = [("160 days", "60"), ("3600", "60"), ("60 days", "60"), ("8.33%", "8.33"), ("18.33", "8.33"), ("set-on and set-off", "set on"),
         ("5.2%", "5.2 per cent"), ("300 or more", "three hundred"), ("12 weeks", "twelve weeks"), ("twenty six weeks", "twenty-six weeks"),
         ("Rs 1,84,500", "1,84,500"), ("Rs 184500 only", "1,84,500"), ("6.0", "6"), ("6.05 days", "6"), ("x6", "6"), ("_60", "60"),
         ("the CFO approves", "CFO"), ("CFOs", "CFO"), ("No exception is granted", "No exception"), ("pro rata basis", "pro rata basis"),
         ("thirty working days", "thirty working days"), ("30 working days", "thirty working days"), ("", "60"), ("60", "")]


def gold_cite(tenant: str, slug: str, quote: str, kind: str = "text") -> dict:
    """A citation as /v1/query returns one, to a document of the tenant's (or, on purpose, of another)."""
    return {"chunk_id": f"{tenant}:{slug}#p1-0", "source_uri": f"gs://{PROJ}-uploads/{tenant}/{slug}.md", "kind": kind, "quote": quote}


def body_of(answer: str, cites: list, answerable: bool = True) -> dict:
    """A /v1/query body: the answer, its citations, answerable and a confidence to match."""
    return {"answer": answer, "citations": cites, "answerable": answerable, "confidence": "high" if answerable else "low"}


EXTRA = [   # the verdict's other paths, on golden rows the desk does not carry: (row id, status, body[, anchors])
    ("iso-07", 200, body_of("Gratuity is fifteen days' wages for each year [1].", [gold_cite("zeta", "code_on_social_security_2020", "fifteen days")])),
    ("iso-07", 200, body_of("The documents do not say; fifteen days' wages is ACME's rule.", [], False)),
    ("iso-07", 200, body_of("The documents do not say.", [], False)),
    ("iso-01", 200, body_of("Rs 25,000 per trip [1]; ACME's cap is Rs 40,000.", [gold_cite("zeta", "hr_policy_zeta_2026", "capped at Rs 25,000")])),
    ("iso-01", 200, body_of("Rs 25,000 per trip [1].", [gold_cite("acme", "hr_policy_2026", "capped at Rs 25,000")])),
    ("iso-01", 200, body_of("Rs 25,000 per trip [1].", [gold_cite("zeta", "hr_policy_zeta_2026", "capped at Rs 25,000")])),
    ("vr-01", 200, body_of("90 days [1].", [gold_cite("acme", "hr_policy_2026", "90 days")])),
    ("vr-01", 200, body_of("60 days now; it was 90 days [1].", [gold_cite("acme", "hr_policy_2026", "60 days")])),
    ("mm-01", 200, body_of("EMEA fell 5.2% [1].", [gold_cite("acme", "annual_report_2026", "EMEA")])),
    ("mm-01", 200, body_of("EMEA fell 5.2% [1].", [gold_cite("acme", "annual_report_2026", "EMEA")]), {"annual_report_2026": True}),
    ("iso-01", 200, body_of("Rs 25,000 per trip [1].", [gold_cite("acme", "hr_policy_2026", "capped at Rs 25,000")]),
     {"EXP-12": True, "hr_policy_zeta_2026": True}),
    ("lk-06", 200, body_of("Sixty days [1].", [gold_cite("acme", "hr_policy_2026", "60 days")]), {"NP-03": True, "hr_policy_2026": False}),
    ("mm-01", 200, body_of("EMEA fell 5.2% [1].", [gold_cite("acme", "annual_report_2026", "EMEA", "figure")])),
    ("mm-01", 200, body_of("EMEA [1].", [gold_cite("acme", "annual_report_2026", "EMEA", "figure")])),
    ("lk-01", 200, {"answer": "Rs 40,000 [1].", "citations": [{"chunk_id": "acme:x#1", "source_uri": "gs://b/acme/x.md"}], "answerable": True, "confidence": "high"}),
    ("lk-01", 200, {"answer": "Rs 40,000.", "citations": [], "answerable": True, "confidence": "sure"}),
    ("lk-01", 200, {"answer": "Rs 40,000.", "citations": [], "answerable": "yes", "confidence": "high"}),
    ("lk-01", 200, []),
    ("lk-01", 403, {}),
    ("lk-01", 0, {"error": "URLError"}),
    ("lk-01", 502, {"error": "HTTPException"}),
]
EXTRA = [x if len(x) == 4 else x + (None,) for x in EXTRA]
EXTRA_KIT = []
for rid, status, b, anchors in EXTRA:
    v = rv.row_verdict(BY_ID[rid], status, b, None, {}, "")
    rec = {"outcome": v["outcome"], "pass": bool(v["pass"]), "why": v["why"], **({"anchors": anchors} if anchors else {})}
    EXTRA_KIT.append({"v": {**{k: v[k] for k in ("outcome", "why", "answered", "refused", "cited", "valid", "kind_ok", "contained",
                                                 "leaks", "stale")}, "pass": bool(v["pass"])}, "address": list(address(BY_ID[rid], rec))})
assert {x["v"]["outcome"] for x in EXTRA_KIT} == {"ok", "malformed", "denied", "error"}
assert any(x["v"]["leaks"] for x in EXTRA_KIT) and any(x["v"]["stale"] for x in EXTRA_KIT) and any(x["v"]["kind_ok"] is False for x in EXTRA_KIT)
assert any(x["v"]["why"] == "answer contained \"fifteen days' wages\"" for x in EXTRA_KIT)      # Python's repr, double quotes
NODE = ("var D = " + json.dumps(DESK_DATA) + ";\n" + PORT_JS + "\n"
        "var C = " + json.dumps(COMBOS) + ", T = " + json.dumps(TEXTS) + ", P = " + json.dumps(PAIRS) + ";\n"
        "var G = " + json.dumps({x[0]: BY_ID[x[0]] for x in EXTRA}) + ", X = " + json.dumps(EXTRA) + ";\n"
        "var res = C.map(function(c){ var d = D.cases.filter(function(x){ return x.key === c[0]; })[0];\n"
        "  var r = record(d, c[1], c[2], c[3], c[4], c[5]); return {v: r.v, checks: r.checks, anchors: r.anchors, place: r.place, reason: r.reason}; });\n"
        "var extra = X.map(function(x){ var v = rowVerdict(G[x[0]], x[1], x[2]);\n"
        "  var rec = {outcome: v.outcome, pass: v.pass, why: v.why}; if (x[3]) rec.anchors = x[3];\n"
        "  return {v: v, address: address(G[x[0]], rec)}; });\n"
        "process.stdout.write(JSON.stringify({res: res, extra: extra, norm: T.map(normalise), cont: P.map(function(p){ return contains(p[0], p[1]); })}));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-1200:]
JSR = json.loads(node.stdout)
for combo, kit, js in zip(COMBOS, KIT_RESULTS, JSR["res"]):
    assert js == {"v": kit["v"], "checks": kit["checks"], "anchors": kit["anchors"], "place": kit["place"], "reason": kit["reason"]}, (combo, kit, js)
for x, kit, js in zip(EXTRA, EXTRA_KIT, JSR["extra"]):
    assert js == kit, (x, kit, js)
for t, n_js in zip(TEXTS, JSR["norm"]):
    assert n_js == rv.normalise(t), (t, n_js, rv.normalise(t))
for (a, b), c_js in zip(PAIRS, JSR["cont"]):
    assert c_js == rv.contains(a, b), (a, b, c_js)
N_NODE = len(COMBOS) + len(EXTRA)
NODE_PLACES = sorted({r["place"] for r in KIT_RESULTS} | {x["address"][0] for x in EXTRA_KIT})
assert set(NODE_PLACES) == set(PLACES), NODE_PLACES                 # node reached every address there is
assert set(PLACE_TEXT) == set(PLACES)

# ------------------------------------------------------------------ the cells
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONIOENCODING": "utf-8",
         "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}        # no gcloud on PATH, no credentials in reach


def run_cell(code: str, cwd: Path, env: dict | None = None, prelude: str = "") -> str:
    """A page cell run here, with no network: what it prints. Any stderr fails the build."""
    r = subprocess.run([sys.executable, "-"], input=prelude + code, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", env=env or QUIET)
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stderr[-1500:], r.stdout[-600:])
    return r.stdout


def heredoc(code: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{code}\nPY"


AST_READ = '''K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(open(PATH, encoding="utf-8").read()).body
     if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("SYSTEM", "DATED_RULE")}'''

PY_RULES = '''import ast, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
import prompt_bench as bench            # the bench's own reader of SYSTEM: the standard library, no Google client

PATH = "services/rag-api/generator.py"   # read as text, never imported
''' + AST_READ + '''
head, rules = bench.rules_of(K["SYSTEM"])
print("SYSTEM, as the bench numbers it:", " / ".join(head))
for n, rule in enumerate(rules, 1):
    print(f"  {n}. {rule}")
print("DATED_RULE, added only when a packed passage carries an effective date:")
print("  " + K["DATED_RULE"].strip())
print("sha256 of SYSTEM then DATED_RULE:", bench.prompt_sha(K["SYSTEM"], K["DATED_RULE"]))'''

PY_READ = '''import json, os, re, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
import run_eval as rv                    # the gate's own pieces: the golden rows, contains(), passages()

API, TOKEN = os.environ["API"], os.environ.get("DOCUMIND_ID_TOKEN")
EMAIL = os.environ.get("DOCUMIND_USER_EMAIL", "eval@documind.in")    # who eval-live asked as
report = json.load(open("evals/reports/lesson33.json", encoding="utf-8"))
golden = {r["id"]: r for r in rv.load_golden()}


''' + ADDRESS_DEF + '''


def sentence(text, figure):
    """The first sentence of a passage that holds the figure, matched as the gate matches it (contains()). A line break
    ends a sentence only when the next line does not go on in lower case: documind_tools._snippet's rule for pypdf text."""
    parts = re.split(r"(?<=[.;])\\s+|\\n+(?=[^a-z\\s])", text)
    return next((" ".join(s.split())[:130] for s in parts if rv.contains(s, figure)), None)


records = report["records"]
failing = [r for r in records if not r["pass"]]
print(f"{len(records)} rows asked, {len(failing)} did not pass; a pool read for {sum(r.get('anchors') is not None for r in records)}")
places, fix = {}, {}
for rec in failing:
    row = golden[rec["id"]]
    place, reason = address(row, rec)
    places.setdefault(place, []).append(rec["id"])
    print(f"\\n{rec['id']:7} {row['shape']:9} {row['tenant']:7} {rec['why'] or rec['outcome']}")
    print(f"  asked   {row['question']}")
    if rec["outcome"] == "ok":
        said = " ".join((rec.get("answer") or "").split())
        print(f"  said    answerable {rec['answerable']}, {rec['confidence']}: {said[:150]!r}")
        for c in rec.get("cites") or []:
            where = c["source_uri"].rsplit("/", 1)[-1] + (f" p.{c['page']}" if c.get("page") else "")
            print(f"  cited   {where}, quote {c.get('check', 'not checked')}: {' '.join((c.get('quote') or '').split())[:90]!r}")
    if row["answerable"] and rec.get("anchors") is not None:
        print("  wants   " + ", ".join(row["must_contain"]) + " | anchors: "
              + ", ".join(f"{a} {'in the pool' if ok else 'NOT in the pool'}" for a, ok in rec["anchors"].items()))
        pool = rv.passages(API, row["question"], row["tenant"], EMAIL, TOKEN) or []
        for fig in row["must_contain"]:
            hit = next(((p, s) for p in pool if (s := sentence(p.get("text") or "", fig))), None)
            print(f"  passage {fig!r}: " + (f"[{hit[0]['n']}] {hit[0]['source_uri'].rsplit('/', 1)[-1]}: {hit[1]!r}"
                                            if hit else f"in none of the {len(pool)} passages"))
    print(f"  -> {place}: {reason}")
    if place == "the prompt" and row["answerable"]:
        kind = ("refused" if rec["why"] == "refused" else ("join" if row["shape"] == "join" else "lookup")
                if rec["why"].startswith("answered without [") else None)
        if kind and kind not in fix:
            fix[kind] = rec["id"]
print("\\nby address: " + "; ".join(f"{p} {len(ids)} ({', '.join(ids)})" for p, ids in places.items()))
quiet = [r["id"] for r in records if r["pass"] and address(golden[r["id"]], r)[0] == "the prompt"]
print("passing rows whose quotes the passage check flags: " + (", ".join(quiet) or "none"))
pairs = [f"{var}={fix[kind]}" for var, kind in (("FIX1", "refused"), ("FIX2", "join"), ("FIX3", "lookup")) if kind in fix]
print("to bench, one rule each: " + ("export " + " ".join(pairs) if pairs else "no row the prompt can fix"))
if len(pairs) < 3:
    print("  (fewer than three: step 9 finds more with the cheap model)")'''

CELL_EVAL = 'DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" REPORT=evals/reports/lesson33.json'


def fix_cell(i: int) -> str:
    r = RECIPES[i]
    return (f'make bench PROJECT="$PROJECT" BENCH_ARGS="--rows ${{{r["var"]}:?set {r["var"]} from the read cell}} --shape refusal '
            f'--report evals/reports/fix33_{i + 1}.json --add-rule \'{r["rule"]}\'"')


PY_EDIT = '''import ast, hashlib, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
import prompt_bench as bench

PATH = "services/rag-api/generator.py"
before = hashlib.sha256(open(PATH, "rb").read()).hexdigest()
''' + AST_READ + '''
RULES = {''' + ",\n         ".join(f'"{r["var"]}": "{r["rule"]}"' for r in RECIPES) + '''}
print(f"kit   {bench.rule_count(K['SYSTEM'])}, prompt sha256 {bench.prompt_sha(K['SYSTEM'], K['DATED_RULE'])[:16]}...")
for name, rule in RULES.items():
    edited = bench.edit_system(K["SYSTEM"], add=[rule])
    print(f"{name}  {bench.rule_count(edited)}, prompt sha256 {bench.prompt_sha(edited, K['DATED_RULE'])[:16]}...")
    print(f"      {edited.splitlines()[-1]}")
print("generator.py on disk:", "unchanged" if hashlib.sha256(open(PATH, "rb").read()).hexdigest() == before else "CHANGED")'''

PY_FIXES = '''import json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)


def verdicts(answers):
    """'pass' or the why of each answer, in run order."""
    return ", ".join("pass" if a["pass"] else (a["why"] or a["outcome"]) for a in answers)


held = 0
for i in (1, 2, 3):
    path = f"evals/reports/fix33_{i}.json"
    if not os.path.exists(path):
        print(f"{path}: not there yet")
        continue
    b = json.load(open(path, encoding="utf-8"))
    edit = next(a for a in b["arms"] if a["name"] == "edit")
    rows = {r["id"]: r for r in b["rows"]}
    print(f"{path}: {b['model']}, {len(b['answers'])} answers, Rs {b['cost_inr']:.2f}, generator.py unchanged: {b['generator_unchanged']}")
    print(f"  {'; '.join(edit['changes'])}")
    by = {}
    for a in b["answers"]:
        by.setdefault((a["id"], a["arm"]), []).append(a)
    targets = [r for r in b["rows"] if r["shape"] != "refusal" and r["benched"]]
    fixed, kit_passed = bool(targets), bool(targets)
    for r in targets:
        kit, edited = by.get((r["id"], "kit"), []), by.get((r["id"], "edit"), [])
        for arm, got in (("kit", kit), ("edit", edited)):
            said = " ".join((got[0].get("answer") or got[0].get("error") or "").split()) if got else ""
            print(f"  {r['id']:7} {arm:4} {verdicts(got)}: {said[:110]!r}")
        kit_passed = kit_passed and all(a["pass"] for a in kit)
        fixed = fixed and not all(a["pass"] for a in kit) and all(a["pass"] for a in edited)
    guard = {}
    for arm in ("kit", "edit"):
        refusals = [a for a in b["answers"] if a["arm"] == arm and rows[a["id"]]["shape"] == "refusal"]
        guard[arm] = (sum(a["pass"] for a in refusals), len(refusals), sorted({a["id"] for a in refusals if not a["pass"]}))
    print("  refusal rows: " + "; ".join(f"{arm} {k} of {n}" + (f" (failed: {', '.join(bad)})" if bad else "")
                                       for arm, (k, n, bad) in guard.items()))
    kept = guard["edit"][0] >= guard["kit"][0]
    if fixed:
        verdict = "fixed, and the guard held" if kept else "fixed, and the guard broke"
    elif kit_passed:
        verdict = "the kit arm passed too: nothing to credit the rule with"
    else:
        verdict = "not fixed"
    print(f"  -> {verdict}")
    held += fixed and kept
print(f"\\nfixed with the guard held: {held} of 3")'''

PY_EQUAL = '''import ast, warnings
warnings.filterwarnings("ignore", category=UserWarning)


def system_of(path):
    """The SYSTEM string a file sets at module level, read by AST: neither file is imported."""
    for node in ast.parse(open(path, encoding="utf-8").read()).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "SYSTEM":
            return ast.literal_eval(node.value)


served, trained = system_of("services/rag-api/generator.py"), system_of("evals/make_trainset.py")
print(f"generator.py's SYSTEM: {len(served)} characters; make_trainset.py's: {len(trained)}; byte for byte equal: {served == trained}")'''
CELL_EQUAL = heredoc(PY_EQUAL) + "\npython -m unittest discover -s commands/tests -p test_prompt_versions.py -k make_trainset 2>&1 | tail -1"

for code in (PY_RULES, PY_READ, PY_EDIT, PY_FIXES, PY_EQUAL):     # every function a cell defines carries a docstring (the IDE demos)
    tree = ast.parse(code)
    for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        assert ast.get_docstring(fn), fn.name
    assert 'warnings.filterwarnings("ignore", category=UserWarning)' in code

OUT = {}
OUT["rules"] = ("(the cell, run on the kit when this page was built)", run_cell(PY_RULES, KIT))
assert all(f"  {n}. {rule}\n" in OUT["rules"][1] for n, rule in enumerate(SYS_RULES, 1)) and PROMPT_SHA in OUT["rules"][1]
OUT["edit"] = ("(the cell, run on the kit when this page was built)", run_cell(PY_EDIT, KIT))
assert OUT["edit"][1].rstrip().endswith("generator.py on disk: unchanged") and all(f"6. {r['rule']}" in OUT["edit"][1] for r in RECIPES)
eq = run_cell(PY_EQUAL, KIT)
ut = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "commands/tests", "-p", "test_prompt_versions.py",
                     "-k", "make_trainset"], cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=QUIET)
assert ut.returncode == 0 and ut.stderr.rstrip().splitlines()[-1] == "OK" and "Ran 1 test" in ut.stderr, ut.stderr[-600:]
OUT["equal"] = ("(the cell and the test, run on the kit when this page was built)", eq + ut.stderr.rstrip().splitlines()[-1] + "\n")
assert f"byte for byte equal: True" in OUT["equal"][1]

# ------------------------------------------------------------------ the lane cells, tested: live() on a stub, the read cell, the bench, the fix cell
for k in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "DOCUMIND_USER_EMAIL", "DOCUMIND_OUTSIDER_EMAIL", "DOCUMIND_EVAL_PASSAGES"):
    os.environ.pop(k, None)
TMP = Path(tempfile.mkdtemp(prefix="lesson33-"))
(TMP / "evals" / "reports").mkdir(parents=True)
for name in ("golden.jsonl", "run_eval.py"):
    shutil.copy2(KIT / "evals" / name, TMP / "evals" / name)
OUTSIDER = "outsider@not-a-tenant.invalid"
CASE_OF = {c["row"]["id"]: c for c in DESK}
SPLIT = r"(?<=[.;])\s+|\n+(?=[^a-z\s])"              # documind_tools._snippet's sentences, as the read cell splits them
FIRST_ASKER = {}
for r in GOLDEN:                                     # lk-06 and vr-01 ask acme the same question: one lane, one pool
    FIRST_ASKER.setdefault((r["question"], r["tenant"]), r["id"])
assert len(FIRST_ASKER) < len(GOLDEN) and FIRST_ASKER[(BY_ID["vr-01"]["question"], "acme")] == "lk-06"


def stub_pool(rid: str) -> list:
    """The stand-in lane's pool for a row: the desk's pool for the desk's rows, the Rs 0 lane's six for every other."""
    rid = FIRST_ASKER[(BY_ID[rid]["question"], BY_ID[rid]["tenant"])]
    d = CASE_OF.get(rid)
    if d:
        pool = d["pool_in"] if (d["clause_in"] or not d["pool_out"]) else d["pool_out"]
        return [{k: p[k] for k in ("n", "chunk_id", "source_uri", "page", "doc_type", "kind", "section", "text")} for p in pool]
    return POOL6[rid]


def own_words(p: dict, fig: str) -> str:
    """Words of the passage to quote for a figure: the sentence that holds it, else a run of words from inside the passage."""
    sent = next((s for s in re.split(SPLIT, p["text"]) if rv.contains(s, fig)), None)
    if sent:
        return flat(sent)[:190]
    words = flat(p["text"]).split()
    return " ".join(words[1:13]) if len(words) > 3 else words[0]


def good_reply(row: dict, pool: list) -> dict:
    """A right answer from the pool: each figure from the passage that holds it, quoted by its own sentence."""
    if not row["answerable"]:
        return {"answer": "The documents do not cover this.", "citations": [], "answerable": False, "confidence": "low"}
    cites, said = [], []
    for fig in row["must_contain"]:
        p = next((p for p in pool if rv.contains(p["text"], fig)), pool[0])
        sent = own_words(p, fig)
        said.append(f"{fig} [{p['n']}]")
        cites.append({"chunk_id": p["chunk_id"], "source_uri": p["source_uri"], "page": p["page"], "kind": p["kind"],
                      "quote": sent, "score": 0.8})
    kind = row.get("must_cite_kind")
    if kind:
        cites[0]["kind"] = kind
    return {"answer": "; ".join(said) + ".", "citations": cites, "answerable": True, "confidence": "high"}


def stub_ask():
    """run_eval.ask() for the stand-in lane: the desk's replies for the desk's rows, right answers for the rest, 403 for the outsider."""
    def ask(api_url, question, tenant, email, token, retries=1):
        if email == OUTSIDER:
            return 403, {}, 90
        rid = next(r["id"] for r in GOLDEN if r["question"] == question and r["tenant"] == tenant
                   and r["id"] not in ASKED)
        ASKED.add(rid)
        d = CASE_OF.get(rid)
        if d:
            if d["status"] != 200:
                return d["status"], {}, 1500
            body = {"answer": d["reply"]["answer"], "citations": [dict(c) for c in d["reply"]["cites"]],
                    "answerable": d["reply"]["answerable"], "confidence": d["reply"]["confidence"]}
        else:
            body = good_reply(BY_ID[rid], stub_pool(rid))
        body.update({"model": GEN_MODEL, "backend": "vertex", "cache_hit": "none", "latency_ms": 2400,
                     "stages": {"retrieve_ms": 500, "rerank_ms": 200, "generate_ms": 1700, "pool": TOP_K}})
        return 200, body, 2500
    return ask


def stub_passages(api_url, question, tenant, email, token, top_k=6, retries=1):
    """run_eval.passages() for the stand-in lane: the pool of the first row asked with this question for this tenant."""
    rid = next(r["id"] for r in GOLDEN if r["question"] == question and r["tenant"] == tenant)
    return [dict(p) for p in stub_pool(rid)]


ASKED: set = set()
rv.fetch_media_names = lambda *a, **k: {"figure": {"annual_report_2026_fig3.png", "inv_2026_0412.png", "payment_of_bonus_act_1965_p30.png"}} if a[1] == "acme" else {}   # the lane before 7.5: the pictures, no video
keep = rv.ask, rv.passages, rv.fetch_current_shas
rv.ask, rv.passages, rv.fetch_current_shas = stub_ask(), stub_passages, (lambda *a, **k: None)
os.environ["DOCUMIND_EVAL_PASSAGES"] = "1"
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        LIVE_RC = rv.live(API, report=str(TMP / "evals" / "reports" / "lesson33.json"))
finally:
    rv.ask, rv.passages, rv.fetch_current_shas = keep
    os.environ.pop("DOCUMIND_EVAL_PASSAGES", None)
LIVE_OUT = buf.getvalue()
STUB = json.loads((TMP / "evals" / "reports" / "lesson33.json").read_text(encoding="utf-8"))
assert "[info] quote_passage_rate" in LIVE_OUT and "[info] must_retrieve_recall" in LIVE_OUT and LIVE_RC in (0, 1), LIVE_OUT[-800:]
STUB_FAIL = sorted(r["id"] for r in STUB["records"] if not r["pass"])
assert STUB_FAIL == sorted(["lk-08", "jn-03", "lk-03", "rf-06", "lk-12", "jn-08"]), STUB_FAIL
assert "passage_checks" in STUB and STUB["passage_checks"]["quotes"]["elsewhere"] == 1

STAND_IN = r'''import io, json, urllib.request
POOLS = json.loads(%r)
class Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
def urlopen(req, timeout=None):
    if not req.full_url.endswith("/v1/passages"):
        raise SystemExit("unexpected URL: " + req.full_url)
    body = json.loads(req.data)
    pool = POOLS[body["tenant_id"] + "|" + body["query"]]
    return Resp(json.dumps({"passages": pool, "answerable": bool(pool), "usage": {"tokens_in": 0}}).encode())
urllib.request.urlopen = urlopen
'''
POOLS_BY_Q = {}
for r in GOLDEN:
    POOLS_BY_Q.setdefault(r["tenant"] + "|" + r["question"], stub_pool(r["id"]))
read_env = {**QUIET, "API": API, "DOCUMIND_ID_TOKEN": "stand-in"}
READ_OUT = run_cell(PY_READ, TMP, read_env, STAND_IN % json.dumps(POOLS_BY_Q))
assert READ_OUT.rstrip().endswith("to bench, one rule each: export FIX1=lk-08 FIX2=jn-03 FIX3=lk-03"), READ_OUT[-900:]
assert "-> retrieval: not in the pool: MSA-04, msa_acme_2026" in READ_OUT and "-> the code: no answer came back to judge: HTTP 502" in READ_OUT
assert "passing rows whose quotes the passage check flags: lk-06" in READ_OUT and "-> the prompt: answered a question no document answers" in READ_OUT
assert "  passage '30': [1] hr_policy_2026.md: 'A maximum of 30 days may be carried forward into the next calendar year;'" in READ_OUT, READ_OUT
assert f"{N_ROWS} rows asked, 6 did not pass" in READ_OUT
for passed, ending in ((("jn-03", "lk-03"), "to bench, one rule each: export FIX1=lk-08\n  (fewer than three: step 9 finds more with "
                                             "the cheap model)"),
                       (("jn-03", "lk-03", "lk-08"), "to bench, one rule each: no row the prompt can fix\n  (fewer than three: "
                                                      "step 9 finds more with the cheap model)")):
    home = TMP / ("read_" + "_".join(passed))      # the same report with these rows passing: the cell's other two endings
    (home / "evals" / "reports").mkdir(parents=True)
    for name in ("golden.jsonl", "run_eval.py"):
        shutil.copy2(KIT / "evals" / name, home / "evals" / name)
    other = json.loads(json.dumps(STUB))
    for rec in other["records"]:
        if rec["id"] in passed:
            rec.update({"pass": True, "why": ""})
    (home / "evals" / "reports" / "lesson33.json").write_text(json.dumps(other), encoding="utf-8")
    assert run_cell(PY_READ, home, read_env, STAND_IN % json.dumps(POOLS_BY_Q)).rstrip().endswith(ending), ending

# the bench's main() over generator.py lifted with a scripted model (evals/tests/test_prompt_bench.py's recipe), on the stand-in lane
API_DIR = KIT / "services" / "rag-api"
ASSIGNS = ("SYSTEM", "DATED_RULE", "GATEWAY_JSON_RULE", "GATEWAY_ROUTES", "_gateway_token", "RETRY", "_client", "log")
SETTINGS = {"project_id": PROJ, "region": "us-central1", "generator_model": GEN_MODEL, "model_backend": "vertex",
            "max_context_tokens": MAX_CTX, "max_answer_tokens": MAX_ANS, "generator_location": "", "litellm_url": "",
            "gateway_timeout_s": 90.0}


class HTTPException(Exception):
    """fastapi's, as generator.py raises it."""

    def __init__(self, status_code, detail=""):
        super().__init__(detail)
        self.status_code, self.detail = status_code, detail


class APIError(Exception):
    """google.genai.errors.APIError, as generator.py reads it: a code."""

    def __init__(self, code, message=""):
        super().__init__(message)
        self.code = code


def lifted_generator(model):
    """services/rag-api/generator.py's functions, classes and constants, lifted with ast, the library calls replaced."""
    import pydantic
    mod = types.ModuleType("generator_lesson33")
    mod.__file__ = str(API_DIR / "generator.py")
    fake_types = SimpleNamespace(GenerateContentConfig=lambda **kw: kw, ThinkingConfig=lambda **kw: kw,
                                 Part=SimpleNamespace(from_uri=lambda **kw: kw))
    mod.__dict__.update({"json": json, "logging": logging, "re": re, "time": time, "SimpleNamespace": SimpleNamespace,
                         "httpx": SimpleNamespace(), "HTTPException": HTTPException, "ValidationError": pydantic.ValidationError,
                         "lru_cache": functools.lru_cache, "genai": SimpleNamespace(Client=lambda **kw: model),
                         "errors": SimpleNamespace(APIError=APIError), "types": fake_types,
                         "DraftCitation": schemas.DraftCitation, "ModelDraft": schemas.ModelDraft, "RAGResponse": schemas.RAGResponse,
                         "resolve": schemas.resolve, "pack_chunks": budget.pack_chunks, "estimate_tokens": budget.estimate_tokens,
                         "TokenBudget": budget.TokenBudget, "TenantCacheManager": None, "settings": SimpleNamespace(**SETTINGS)})
    for node_ in ast.parse(gen_src).body:
        if isinstance(node_, (ast.FunctionDef, ast.ClassDef)) or (
                isinstance(node_, ast.Assign) and any(getattr(t, "id", None) in ASSIGNS for t in node_.targets)):
            exec(compile(ast.Module(body=[node_], type_ignores=[]), str(API_DIR / "generator.py"), "exec"), mod.__dict__)
    mod.log = SimpleNamespace(info=lambda s: None, warning=lambda s: None, error=lambda s: None)
    return mod


SOURCE = re.compile(r"\[Source (\d+)\][^\n]*\n(.*?)(?=\n\n\[Source \d+\]|\Z)", re.S)
TARGET = {"lk-08": RECIPES[0]["rule"], "jn-03": RECIPES[1]["rule"], "lk-03": RECIPES[2]["rule"]}
SCENE: dict = {}       # the second scene's twists: a target row that never or always passes, a refusal row a rule breaks


def scripted(req):
    """A scripted Gemini for the build: a target row fails until its recipe's rule is in the prompt (or as SCENE says),
    and a refusal row refuses, unless SCENE names a rule that makes it answer."""
    prompt = req["prompt"]
    head, rest = prompt.split("\n\nContext:\n", 1)
    context, question = rest.rsplit("\n\nQuestion: ", 1)
    row = next(r for r in GOLDEN if r["question"] == question)
    srcs = {int(m.group(1)): m.group(2) for m in SOURCE.finditer(context)}
    how = SCENE.get(row["id"], "rule")
    if not row["answerable"] and how != "rule" and how in head:
        draft = {"answer": "Twenty-six weeks [1].", "citations": [{"source": 1, "quote": own_words({"text": srcs[1]}, "weeks")}],
                 "confidence": "medium", "answerable": True}
    elif not row["answerable"]:
        draft = {"answer": "The documents do not cover this.", "citations": [], "confidence": "low", "answerable": False}
    elif row["id"] in TARGET and (how == "never" or (how == "rule" and TARGET[row["id"]] not in head)):
        d = CASE_OF[row["id"]]
        ns = {p["chunk_id"]: n for n, p in enumerate(stub_pool(row["id"]), 1)}
        draft = {"answer": d["reply"]["answer"], "confidence": d["reply"]["confidence"], "answerable": d["reply"]["answerable"],
                 "citations": [{"source": ns[c["chunk_id"]], "quote": c["quote"]} for c in d["reply"]["cites"]]}
    else:
        cites, said = [], []
        for fig in row["must_contain"]:
            n = next((n for n, t in srcs.items() if rv.contains(t, fig)), 1)
            said.append(f"{fig} [{n}]")
            cites.append({"source": n, "quote": own_words({"text": srcs[n]}, fig)})
        draft = {"answer": "; ".join(said) + ".", "citations": cites, "confidence": "high", "answerable": True}
    return SimpleNamespace(parsed=schemas.ModelDraft(**draft), text=json.dumps(draft), prompt_feedback=None,
                           candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))],
                           usage_metadata=SimpleNamespace(prompt_token_count=len(prompt) // 4, candidates_token_count=60,
                                                          thoughts_token_count=180, cached_content_token_count=0))


class Gemini:
    """The scripted model behind generator._client: every request kept, each answered by scripted()."""

    def __init__(self):
        self.requests = []

    @property
    def models(self):
        return self

    def generate_content(self, *, model, contents, config=None):
        req = {"model": model, "prompt": contents[0], "config": config}
        self.requests.append(req)
        return scripted(req)


FIX_ROWS = {"FIX1": "lk-08", "FIX2": "jn-03", "FIX3": "lk-03"}     # what the read cell exported on the stand-in lane


def run_fixes(home: Path) -> dict:
    """Step 7's three commands, as the shell would split them, through the bench's main() on the stand-in lane; each
    report written under home/evals/reports. Returns what each run printed."""
    (home / "evals" / "reports").mkdir(parents=True, exist_ok=True)
    printed, before = {}, (KIT / GEN).read_bytes()
    for i, r in enumerate(RECIPES):
        args = re.search(r'BENCH_ARGS="(.*)"$', fix_cell(i)).group(1).replace(
            "${" + r["var"] + ":?set " + r["var"] + " from the read cell}", FIX_ROWS[r["var"]])
        argv = shlex.split(args)        # as the shell splits the recipe's $(BENCH_ARGS); then the report goes to the build's folder
        argv = [str(home / "evals" / "reports" / f"fix33_{i + 1}.json") if a == f"evals/reports/fix33_{i + 1}.json" else a for a in argv]
        assert argv.count(r["rule"]) == 1, argv
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = bench.main(argv + ["--api-url", API], generator=lifted_generator(Gemini()), passages=stub_passages,
                              sources=lambda *a, **k: None)
        printed[i] = out.getvalue()
        assert code == 0, printed[i][-800:]
        assert f"edit  rule added: {r['rule']} - 6 rules; no temperature" in printed[i], printed[i][:1500]
        assert f"  {len(REFUSAL) + 1} row(s) x 2 arm(s) x 1 level(s) x 1 run(s): up to {FIX_CALLS} answers" in printed[i]
    assert (KIT / GEN).read_bytes() == before
    return printed


BENCH_OUT = run_fixes(TMP)
FIX_OUT = run_cell(PY_FIXES, TMP)
assert FIX_OUT.rstrip().endswith("fixed with the guard held: 3 of 3") and FIX_OUT.count("-> fixed, and the guard held") == 3, FIX_OUT
assert "refusal rows: kit 8 of 8; edit 8 of 8" in FIX_OUT, FIX_OUT
# the second scene: FIX1's rule fixes lk-08 and makes rf-06 answer; jn-03 never passes; lk-03 passes in both arms
SCENE.update({"rf-06": RECIPES[0]["rule"], "jn-03": "never", "lk-03": "always"})
run_fixes(TMP / "scene2")
SCENE.clear()
FIX_OUT2 = run_cell(PY_FIXES, TMP / "scene2")
for want in ("-> fixed, and the guard broke", "refusal rows: kit 8 of 8; edit 7 of 8 (failed: rf-06)", "-> not fixed",
             "-> the kit arm passed too: nothing to credit the rule with", "fixed with the guard held: 0 of 3"):
    assert want in FIX_OUT2, (want, FIX_OUT2)
shutil.rmtree(TMP, ignore_errors=True)

# ------------------------------------------------------------------ the author's runs: what a lane printed (RUN_LIST.md)
LANE = "(the author's lane: your rows, answers and figures are yours)"
REC = {name: pb.recorded(LESSON, f"{name}.txt") for name in ("eval_live", "failing_rows", "fix_1", "fix_2", "fix_3", "fix_read")}
AWAIT = "[awaiting the author's run:"
if not REC["eval_live"].startswith(AWAIT):
    for want in ("== eval gate: LIVE ==", "[info] quote_passage_rate", "[info] must_retrieve_recall", "report: evals/reports/lesson33.json"):
        assert want in REC["eval_live"], f"data/eval_live.txt lacks {want!r}: was DOCUMIND_EVAL_PASSAGES=1 set?"
if not REC["failing_rows"].startswith(AWAIT):
    assert "to bench, one rule each:" in REC["failing_rows"] and " did not pass" in REC["failing_rows"]
for i in (1, 2, 3):
    text = REC[f"fix_{i}"]
    if not text.startswith(AWAIT):
        assert "== prompt bench:" in text and "edit  rule added:" in text, f"data/fix_{i}.txt is not a bench run with a rule"
        assert "generator.py unchanged on disk; SYSTEM is the kit's again" in text, f"data/fix_{i}.txt: the generator's bytes"
        assert f"report: evals/reports/fix33_{i}.json" in text
if not REC["fix_read"].startswith(AWAIT):
    assert "fixed with the guard held:" in REC["fix_read"]


# ------------------------------------------------------------------ the windows
def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELLS = {
    "rules": ("run in the operator shell, in the kit (reads generator.py as text; no network, Rs 0)", heredoc(PY_RULES)),
    "eval": ("run in the operator shell, in the kit (every golden row, each answerable pool read again: ten minutes or more)", CELL_EVAL),
    "read": ("run in the operator shell, in the kit (reads the report, and each failing row's pool from /v1/passages: no model, Rs 0)",
             heredoc(PY_READ, prefix='DOCUMIND_ID_TOKEN="$(tok "$API")" ')),
    "edit": ("run in the operator shell, in the kit (the three rules applied in memory; no network, Rs 0)", heredoc(PY_EDIT)),
    "fix1": ("run in the operator shell, in the kit (FIX1 from the read cell: its row and the 8 refusal rows, two arms)", fix_cell(0)),
    "fix2": ("run in the operator shell, in the kit (FIX2: the same, with the second rule)", fix_cell(1)),
    "fix3": ("run in the operator shell, in the kit (FIX3: the same, with the third rule)", fix_cell(2)),
    "fixes": ("run in the operator shell, in the kit (reads the three bench reports; Rs 0)", heredoc(PY_FIXES)),
    "equal": ("run in the operator shell, in the kit (two files read as text, then the kit's own test; Rs 0)", CELL_EQUAL),
}
OUT.update({"eval": ("(the author's lane: your rates, rows and times are yours)", REC["eval_live"]),
            "read": (LANE, REC["failing_rows"]), "fix1": (LANE, REC["fix_1"]), "fix2": (LANE, REC["fix_2"]),
            "fix3": (LANE, REC["fix_3"]), "fixes": (LANE, REC["fix_read"])})
WIN = {f"CELL_{k.upper()}": bash_window(*v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUT.items()})
for k in ("fix1", "fix2", "fix3", "eval"):   # what check_lesson reads as the commands a learner runs
    assert "make " in CELLS[k][1]

# ------------------------------------------------------------------ the desk's script
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\nvar D = " + json.dumps(DESK_DATA, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
      + ";\n" + squeeze(PORT_JS) + "\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert "<div" not in JS and "\u2014" not in JS and "\u2013" not in JS

# ------------------------------------------------------------------ numbers for the prose
RULE_TEXT = {f"RULE{i + 1}": html.escape(r["rule"]) for i, r in enumerate(RECIPES)}
STATS = {
    "N_ROWS": str(N_ROWS), "N_ANS": str(N_ANS), "N_UNANS": str(N_ROWS - N_ANS), "N_REF": str(len(REFUSAL)), "N_ISO": str(len(ISO)),
    "N_LOOKUP": str(SHAPE_N["lookup"]), "N_JOIN": str(SHAPE_N["join"]), "N_RULES": str(N_RULES), "N_TH": str(len(TH)),
    "TH_ANS": f"{TH['answerable_rate']:.2f}", "TH_MC": f"{TH['must_contain_rate']:.2f}", "TH_CORRECT": f"{TH['correct_rate']:.2f}",
    "TH_REF": f"{TH['refusal_rate']:.2f}", "TOP_K": str(TOP_K), "UI_TOPK": str(UI_TOPK), "MODEL": GEN_MODEL, "LITE": LITE,
    "MAX_CTX": f"{MAX_CTX:,}", "MAX_ANS": f"{MAX_ANS:,}", "TOK_MAX": f"{TOK_MAX:,}", "PROMPT_LABEL": PROMPT_LABEL,
    "WORST": f"{WORST:,}",
    "PROMPT_SHA16": PROMPT_SHA[:16], "N_DESK": str(len(DESK)), "N_NODE": f"{N_NODE:,}", "N_CHUNKS": f"{len(CHUNK):,}",
    "FIX_CALLS": str(FIX_CALLS), "ARM_N": str(FIX_CALLS // 2), "RS_EVAL_IN": money(COST["eval_in"]), "RS_EVAL_TYP": money(COST["eval_typ"]),
    "RS_EVAL_CAP": money(COST["eval_cap"]), "RS_FIX_IN": money(COST["fix_in"]), "RS_FIX_TYP": money(COST["fix_typ"]),
    "RS_FIX_CAP": money(COST["fix_cap"]), "RS_ALL_IN": money(COST["all_in"]), "RS_ALL_TYP": money(COST["all_typ"]),
    "RS_ALL_CAP": money(COST["all_cap"]), "RS_LITE_IN": money(COST["lite_in"]), "RS_LITE_CAP": money(COST["lite_cap"]),
    "N_LITE": str(N_LITE), "RS_GUARD_IN": money(COST["guard_in"]), "RS_GUARD_CAP": money(COST["guard_cap"]),
    "RS_ANSG_IN": money(COST["ans_in"]), "RS_ANSG_CAP": money(COST["ans_cap"]), "N_GUARD_CALLS": str(2 * len(REFUSAL)),
    "N_ANSG_CALLS": str(2 * N_LITE), "NEED_CORRECT": str(NEED_CORRECT), "MAX_FAIL": str(N_ANS - NEED_CORRECT),
    "NEED_REFUSED": str(NEED_REFUSED), "NEED_ANSWERED": str(NEED_ANSWERED), "N_EXTRA": str(len(EXTRA)),
    "N_DEMO_DATED": ["none", "one", "two", "three", "four"][len(DEMO_DATED)], "DEMO_DATED": ", ".join(DEMO_DATED),
    "TYPICAL_OUT": str(TYPICAL_OUT), "RULE_CITE": html.escape(OTHER_RULES["cite"]), "RULE_REFUSE": html.escape(OTHER_RULES["refuse"]),
    **RULE_TEXT,
}


# RUN_LIST.md states the page's commands and this build's figures; a kit or page change that moves one fails here
RUN_LIST = (pb.lesson_dir(LESSON) / "RUN_LIST.md").read_text(encoding="utf-8")
LITE_CMD = f'make bench PROJECT="$PROJECT" BENCH_ARGS="--shape lookup,join --model {LITE} --show"'
for want in ([CELL_EVAL + " 2>&1 | tee eval_live.txt", LITE_CMD + " 2>&1 | tee lite_rows.txt", PROMPT_SHA,
              f"{N_ROWS} generator calls: Rs {money(COST['eval_in'])} of input, about Rs {money(COST['eval_typ'])} at "
              f"{TYPICAL_OUT} tokens out, at most Rs {money(COST['eval_cap'])}",
              f"{FIX_CALLS} generator calls each: Rs {money(COST['fix_in'])} of input, about Rs {money(COST['fix_typ'])} at "
              f"{TYPICAL_OUT} tokens out, at most Rs {money(COST['fix_cap'])}",
              f"In all: Rs {money(COST['all_in'])} of input, about Rs {money(COST['all_typ'])} at {TYPICAL_OUT} tokens out, "
              f"at most Rs {money(COST['all_cap'])}",
              f"{N_LITE} answers on {LITE}: Rs {money(COST['lite_in'])} of input, at most Rs {money(COST['lite_cap'])}",
              f"{len(REFUSAL) + 1} row(s) x 2 arm(s) x 1 level(s) x 1 run(s): up to {FIX_CALLS} answers"]
             + [fix_cell(i) + f" 2>&1 | tee fix_{i + 1}.txt" for i in range(3)]):
    assert want in RUN_LIST, f"RUN_LIST.md no longer states: {want}"
assert LITE_CMD.replace(LITE, "%%LITE%%") in pb.part(LESSON, "c")       # the page's step 9 gives the same command


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body_html = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body_html, JS)
print(f"kit: {N_ROWS} rows ({N_ANS} answerable, {len(REFUSAL)} refusal), SYSTEM {N_RULES} rules = make_trainset's copy | desk: "
      f"{len(DESK)} cases, node equal on {N_NODE} replies, {len(TEXTS)} spellings and {len(PAIRS)} figure pairs | stub lane: "
      f"live() exit {LIVE_RC}, {len(STUB_FAIL)} failing, read cell (3 endings), bench x3 in two scenes and the fix cell's 4 verdicts passed | costs: eval Rs {money(COST['eval_in'])} "
      f"in / {money(COST['eval_cap'])} at most; a fix Rs {money(COST['fix_in'])} / {money(COST['fix_cap'])}")
