"""Build lesson 3.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Computed from the kit when the page is built:
  - the join panel: evals/golden.jsonl's join rows, each must_contain figure and must_retrieve anchor looked up in the
    row's company's corpus as shared/documind_corpus.py cuts it, with run_eval's own contains() and anchor rule, and the
    fewest anchored passages that hold every figure;
  - the few-shot panel: desk_router.prompt() with and without desk_routes.PROMPT_EXEMPLARS, the groups the examples
    hold out of the score (route_eval.prompt_groups()), the scored rows, and the turns that reach L1 in the offline run;
  - the generator's settings (config.py), SYSTEM and DATED_RULE (read by AST), the edit arm's SYSTEM and both prompt
    sha256s (prompt_bench.edit_system() and prompt_sha()), held against services/rag-api/prompt_versions.json;
  - the schema google-genai builds from ModelDraft, and its property_ordering;
  - the offline cells' outputs, run here on the kit: the edited prompt, the kit's tests, the swap, both offline arms of
    route_eval.py --local, and the paired read over their reports;
  - every Wilson interval in the prose (route_eval.wilson()) and every rupee (shared/prices.py).
The parsers that turn the author's recorded runs into the result paragraphs are checked here against the kit's own
output: prompt_bench.py run by its offline test harness (evals/tests/test_prompt_bench.py: a scripted model, a stand-in
lane) and route_eval.py --local. Live: each output a lane prints is pb.recorded() from the author's run; RUN_LIST.md
says which command records which file, and this build checks that its rupee figures are the ones RUN_LIST.md states.
"""
import ast
import html
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from contextlib import redirect_stdout
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "3.2"
HERE = Path(__file__).resolve().parent
title = ("<title>Lesson 3.2 Prompt with chain of thought and few-shot exemplars - room to think on the join rows, one "
         "reasoning rule against it, and the router's examples taken out and put back | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.jx-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;margin:6px 0 10px;}
.jx-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.jx-out{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 12px;font-size:var(--small-size);line-height:1.55;min-width:0;overflow-wrap:anywhere;}
.jx-out p{margin:0 0 6px;font-size:var(--small-size);}
.jx-out ul{margin:4px 0 8px;padding-left:20px;font-size:var(--small-size);}
.jx-tag{display:inline-block;font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;border-radius:5px;padding:1px 6px;margin:0 4px 2px 0;background:var(--teal-light);color:var(--teal-dark);}
.jx-tag.q{background:#fffbeb;color:#92400e;}
.fx-bar{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 6px;}
.fx-b{font:inherit;font-size:var(--small-size);padding:8px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);cursor:pointer;min-height:44px;}
.fx-b.on{background:var(--teal);border-color:var(--teal);color:#fff;}
.fx-b:active{transform:scale(.98);}
.fx-prompt{background:var(--code-bg);color:var(--code-text);font-family:var(--mono);font-size:12.5px;line-height:1.5;padding:12px 14px;border-radius:10px;white-space:pre-wrap;overflow-wrap:anywhere;margin:8px 0;}
.fx-prompt mark{background:#134e4a;color:#99f6e4;border-radius:3px;padding:0 2px;}
.fx-stat{font-size:var(--small-size);margin:6px 0 10px;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
GEN = "services/rag-api/generator.py"
SCH = "shared/documind_schemas.py"
PBF = "evals/prompt_bench.py"
RT = "services/chat/desk_router.py"
RS = "services/chat/desk_routes.py"
REF = "evals/route_eval.py"
MKG = "mk/generation.mk"
MKA = "mk/agents.mk"
SUMMARY_MARK = "# --------------------------------------------------------------------- the summary"
RECORDER_MARK = "# --------------------------------------------------------------------- the recorder around generator._client"

EXCERPTS = {
    "gen_thinking": ("services/rag-api/generator.py - _call(): the cap, then the thinking level, and no temperature",
                     block(GEN, "            max_output_tokens=max_tokens,", n=6)),
    "gen_usage": ("services/rag-api/generator.py - _usage(): the thought tokens billed as output",
                  block(GEN, "def _usage(r) -> dict:", end="def _add(")),
    "draft": ("shared/documind_schemas.py - ModelDraft: four fields, none of them for working",
              block(SCH, "class ModelDraft(BaseModel):", end="def resolve(")),
    "system": ("services/rag-api/generator.py - SYSTEM: five rules and no example",
               block(GEN, 'SYSTEM = """You are DocuMind', end="# The ledger's second half")),
    "pb_levels": ("evals/prompt_bench.py - the levels, the kit's level and the shapes",
                  block(PBF, 'LEVELS = ("MINIMAL", "LOW", "MEDIUM", "HIGH")', n=3)),
    "pb_usage": ("evals/prompt_bench.py - usage_of(): the thought tokens apart from the visible ones",
                 block(PBF, "def usage_of(r) -> dict:", end="class Recorder:")),
    "pb_recorder": ("evals/prompt_bench.py - Recorder: every call sent at the level being benched, and kept",
                    block(PBF, "class Recorder:", end="def call_inr(")),
    "pb_edit": ("evals/prompt_bench.py - edit_system() and arms(): a rule added in memory, and the edit arm that carries it",
                block(PBF, "def edit_system(", end="def prompt_sha(") + "\n\n\n" + block(PBF, "def arms(", end=RECORDER_MARK)),
    "pb_bench": ("evals/prompt_bench.py - bench(): every row, arm, level and run from one pool, the kit put back after",
                 block(PBF, "def bench(gen, rows", end=SUMMARY_MARK)),
    "mk_bench": ("mk/generation.mk - make bench: the token as documind-ui-sa, then the script",
                 block(MKG, "bench: guard-project", n=7)),
    "exemplars": ("services/chat/desk_routes.py - PROMPT_EXEMPLARS: the classifier's examples",
                  block(RS, "# (row id in evals/routes.jsonl, route, question)", end="def doc_types(")),
    "prompt": ("services/chat/desk_router.py - prompt(): the desks, the rules, the examples, then the question as data",
               block(RT, "def prompt(question: str, prev_question", end="_PARTS = re.compile")),
    "l1_config": ("services/chat/desk_router.py - L1's model and its request: a thinking budget of 0",
                  block(RT, 'L1_MODEL = "gemini-3.1-flash-lite"', n=2) + "\n...\n" + block(RT, "def l1_config(", n=5)),
    "load": ("evals/route_eval.py - load_exemplars(): kit is the kit's tuple, none is no example",
             block(REF, "def load_exemplars(", n=10)),
    "swap": ("evals/route_eval.py - exemplars_in_prompt(): swapped for the run, put back whatever happens",
             block(REF, "@contextlib.contextmanager", end="def l1_alone(")),
    "prompt_groups": ("evals/route_eval.py - prompt_groups(): the groups the prompt has seen, out of every score",
                      block(REF, "def prompt_groups(", end="def _tenant_classes(")),
    "l1_alone": ("evals/route_eval.py - l1_alone(): L1's own route, before the vote and the arbiter",
                 block(REF, "def l1_alone(", end="def exemplars_line(")),
    "l1_print": ("evals/route_eval.py - run_router(): the line it prints after the usual report",
                 block(REF, "    if examples is not None:", n=4, nth=2)),
    "wilson": ("evals/route_eval.py - wilson() and rate(): every rate with its 95% interval",
               block(REF, "def wilson(", end="# Lesson 10.4's figures")),
    "mk_exemplars": ("mk/agents.mk - make exemplars: the swap from your shell, LOCAL=1 offline",
                     block(MKA, "# The classifier's examples on and off (workshop lesson 3.2)", n=10)),   # the target alone
}
X = {k: v[1] for k, v in EXCERPTS.items()}
assert X["gen_thinking"].rstrip().endswith('thinking_config=types.ThinkingConfig(thinking_level="LOW"),'), X["gen_thinking"]
assert "NO temperature" in X["gen_thinking"] and "3.2" not in X["gen_thinking"]     # the comment that names old 3.2 stays out
assert X["gen_usage"].rstrip().endswith('"cached_tokens": n("cached_content_token_count")}')
assert X["draft"].rstrip().endswith("answerable: bool") and "reasoning" not in X["draft"]
assert X["system"].startswith('SYSTEM = """') and X["system"].rstrip().endswith('"""')
assert X["pb_levels"].splitlines()[1].startswith('KIT_LEVEL = "LOW"') and X["pb_levels"].splitlines()[2].startswith("SHAPES")
assert X["pb_usage"].rstrip().endswith('"visible": n("candidates_token_count"), "thought": n("thoughts_token_count"), "finish": finish}')
assert X["pb_recorder"].rstrip().endswith("return r") and "thinking_level=self.level" in X["pb_recorder"]
assert X["pb_edit"].rstrip().endswith("return out") and "def arms(" in X["pb_edit"]
assert X["pb_bench"].rstrip().endswith("return answers") and "gen.SYSTEM, gen._client = kit_system, kit_client" in X["pb_bench"]
assert X["mk_bench"].startswith("bench: guard-project") and X["mk_bench"].rstrip().endswith("$(PY) evals/prompt_bench.py --api-url $$API $(BENCH_ARGS)")
assert X["exemplars"].rstrip().endswith(")") and X["exemplars"].count('", "') >= 8
assert X["prompt"].rstrip().endswith('return "\\n".join(out)') and "PROMPT_EXEMPLARS[:12]" in X["prompt"]
assert '"thinking_config": {"thinking_budget": 0}' in X["l1_config"]
assert X["load"].rstrip().endswith("return ()") and 'if spec == "kit":' in X["load"]
assert X["swap"].startswith("@contextlib.contextmanager") and X["swap"].rstrip().endswith("desk_router.PROMPT_EXEMPLARS = kept")
assert X["l1_alone"].rstrip().endswith('return right, len(asked), sum(1 for x in asked if x["decision"].get("l1") is None)')
assert X["l1_print"].splitlines()[1].strip() == "right, asked, failed = l1_alone(scored, runs[0])" and X["l1_print"].rstrip().endswith('f"it was asked; {failed} failed)")')
assert X["wilson"].rstrip().endswith('return f"{k}/{n} = {100 * k / n:.1f}% [{100 * lo:.1f}%, {100 * hi:.1f}%]"')
assert X["mk_exemplars"].rstrip().endswith('--exemplars $(or $(EXEMPLARS),kit) $(if $(RUNS),--runs $(RUNS),) '
                                           '$(if $(REPORT),--report "$(REPORT)",)')


def kit_window(label: str, code: str) -> str:
    """pagebuild.window(), except that a Makefile fragment is not coloured as Python: its $(...) and quotes stay plain."""
    if label.startswith("mk/"):
        return ('<div class="cw"><div class="ch-bar"><span>' + html.escape(label) + '</span><span class="ro">read only</span></div>'
                '<pre tabindex="0">' + html.escape(code) + "</pre></div>\n")
    return window(label, code)


fill = filler(EXCERPTS, kit_window)

# ------------------------------------------------------------------ the kit's modules, and the facts the prose states
sys.path[:0] = [str(KIT), str(KIT / "evals")]
import paired  # noqa: E402  - Newcombe's interval and the exact McNemar test, standard library only
import prompt_bench as bench  # noqa: E402  - imports run_eval, route_eval's rate() and shared.prices; nothing from Google
import route_eval  # noqa: E402
import run_eval  # noqa: E402
from shared import documind_corpus as dc  # noqa: E402
from shared import prices  # noqa: E402

assert prices.PROFILE == "gcp", "the build prices at list price: unset DOCUMIND_PROFILE"
desk_router, desk_routes = route_eval.router()
WORDS = ["none", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]


def word(n: int) -> str:
    """A small count as a word, a larger one as digits."""
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def phrase(items: list) -> str:
    """'a, b and c'."""
    return ", ".join(items[:-1]) + " and " + items[-1] if len(items) > 1 else items[0]


def by_route(counter: Counter) -> str:
    """'statute 129, handbook 44 and out_of_scope 14', largest first."""
    return phrase([f"{k} {v}" for k, v in counter.most_common()])


cfg = (KIT / "services" / "rag-api" / "config.py").read_text(encoding="utf-8")
grab = lambda pat, text=cfg: re.search(pat, text).group(1)  # noqa: E731
GEN_MODEL = grab(r'generator_model: str = "([^"]+)"')
MAX_ANSWER = int(grab(r"max_answer_tokens: int = (\d+)"))
PROMPT_ID = grab(r'prompt_id: str = "([^"]+)"')
PROMPT_VERSION = grab(r'prompt_version: str = "([^"]+)"')
PROMPT_LABEL = f"{PROMPT_ID}@{PROMPT_VERSION}"           # what /version reports and prompt_versions.json registers
gen_src = (KIT / GEN).read_text(encoding="utf-8")
consts = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(gen_src).body
          if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) in ("SYSTEM", "DATED_RULE")}
SYSTEM, DATED_RULE = consts["SYSTEM"], consts["DATED_RULE"]
KIT_LEVEL = bench.KIT_LEVEL
assert KIT_LEVEL == "LOW" and gen_src.count(f'thinking_config=types.ThinkingConfig(thinking_level="{KIT_LEVEL}")') == 2   # _call and the stream
assert gen_src.count("response_schema=") == 1, "only _call() sends a schema: the stream answers in plain text"
assert gen_src.count("settings.max_answer_tokens * 3") == 2, "the retry's room is three times the cap"
assert "include_thoughts" not in gen_src, "the kit never asks for the thoughts back"
MAX_RETRY = 3 * MAX_ANSWER
assert len(bench.rules_of(SYSTEM)[1]) == 5 and DATED_RULE.startswith("\n6. ")
UI_SRC = (KIT / "services" / "frontend" / "chat.py").read_text(encoding="utf-8")
UI_TOP_K = int(grab(r'"top_k": (\d+), "brain": "ui"', UI_SRC))
assert f'{{"query": query, "tenant_id": tenant_id, "top_k": {UI_TOP_K}, "brain": "ui"}}' in UI_SRC and "/v1/stream" in UI_SRC

REGISTRY = json.loads((KIT / "services" / "rag-api" / "prompt_versions.json").read_text(encoding="utf-8"))["versions"]
KIT_SHA = bench.prompt_sha(SYSTEM, DATED_RULE)
assert REGISTRY[PROMPT_LABEL] == KIT_SHA, "the kit's SYSTEM and DATED_RULE are the text the registry names"
RULE = "Show your working in the answer: name each fact the question needs and the [N] that states it, then combine them."
EDIT_SYSTEM = bench.edit_system(SYSTEM, add=[RULE])
EDIT_SHA = bench.prompt_sha(EDIT_SYSTEM, DATED_RULE)
assert EDIT_SHA not in REGISTRY.values() and bench.rules_of(EDIT_SYSTEM)[1] == bench.rules_of(SYSTEM)[1] + [RULE]
assert "'" not in RULE and '"' not in RULE and "$" not in RULE and "\\" not in RULE, "the rule rides in BENCH_ARGS inside single quotes"

# the schema google-genai builds from ModelDraft: its field order is the order the reply is asked for
try:
    import google.genai as genai_pkg
    from google.genai import _transformers as genai_transformers
except ImportError as e:   # the sys venv has it, as rag-api's image does
    raise SystemExit(f"this build needs google-genai, to read the schema it makes of ModelDraft: {e}")
from shared.documind_schemas import ModelDraft  # noqa: E402


class _VertexClient:
    """The two attributes google-genai's schema transformer reads of an API client: the Vertex AI backend."""
    vertexai = True
    _api_client = None


DRAFT_SCHEMA = genai_transformers.t_schema(_VertexClient(), ModelDraft)
DRAFT_ORDER = list(DRAFT_SCHEMA.property_ordering)
assert DRAFT_ORDER == list(ModelDraft.model_fields) == ["answer", "citations", "confidence", "answerable"], DRAFT_ORDER
GENAI_VERSION = genai_pkg.__version__
GENAI_PIN = grab(r"(?m)^google-genai==([\d.]+)$", (KIT / "services" / "rag-api" / "requirements.txt").read_text(encoding="utf-8"))

# the models, the prices and the router's settings the prose names
L1_MODEL, L2_MODEL, EMBED_MODEL, L2_THINKING = desk_router.L1_MODEL, desk_router.L2_MODEL, desk_router.EMBED_MODEL, desk_router.L2_THINKING
assert (L2_MODEL, L2_THINKING) == (GEN_MODEL, "LOW") and desk_router.l1_config()["thinking_config"] == {"thinking_budget": 0}
P_IN, P_OUT = prices.PRICES[GEN_MODEL]
L_IN, L_OUT = prices.PRICES[L1_MODEL]
USD_INR = prices.USD_INR

# ------------------------------------------------------------------ the golden join rows, taken apart against the corpus
GOLDEN = run_eval.load_golden()
JOINS = [r for r in GOLDEN if r["shape"] == "join"]
assert len(JOINS) == 11, f"{len(JOINS)} join rows: the plan and the prose say 11"
JN03 = next(r for r in JOINS if r["id"] == "jn-03")
TENANT_CHUNKS = {}
for t in sorted({r["tenant"] for r in JOINS}):
    docs = dc.load_documents(t, str(KIT / "evals"), "documind-ai-YOUR-ID")
    flat_chunks = [c for d in docs for c in dc.chunk_document(d, t)]
    TENANT_CHUNKS[t] = [dict(c, order=i, flat=" ".join(c["text"].split()), slug=c["chunk_id"].split(":", 1)[1].split("#", 1)[0])
                        for i, c in enumerate(flat_chunks)]
TENANT_SLUGS = {t: {c["slug"] for c in cs} for t, cs in TENANT_CHUNKS.items()}


def hay(c: dict) -> str:
    """run_eval.anchors_found()'s matching text for one passage: its id, its source and its text, lower-cased."""
    return f"{c['chunk_id']}\n{c['source_uri']}\n{c['text']}".lower()


def where(c: dict) -> str:
    """A passage's name on the page: its file and its clause, or its file and its page."""
    name = c["source_uri"].rsplit("/", 1)[-1]
    return f"{name} {c['locator']}" if c.get("section") else f"{name} p.{c['page_start']}"


SENT = re.compile(r"(?<=[.;])\s+(?=[A-Z(\"'0-9“*])")
LABELLED = re.compile(r"^(\||\*\*|[^:|]{1,40}: )")


def sentence_with(c: dict, fig: str) -> str:
    """The words of a passage that hold the figure, by run_eval's contains(): in a Markdown document, the table row or
    labelled line, or else the sentence; in a PDF's text mirror, whose lines and page headers break its sentences, about
    230 characters around the figure, cut on spaces."""
    text = c["text"]
    if c.get("section") and text.startswith(c["section"]):
        text = text[len(c["section"]):]                     # a handbook clause's title line is not a sentence
    if c["source_uri"].endswith(".md"):
        for para in re.split(r"\n\s*\n", text.strip()):
            lines = [line.strip() for line in para.splitlines() if line.strip()]
            units = lines if all(LABELLED.match(line) for line in lines) else SENT.split(" ".join(para.split()))
            hit = next((u for u in units if run_eval.contains(u, fig)), None)
            if hit:
                return hit
        raise AssertionError(f"{c['chunk_id']}: no line or sentence holds {fig!r}")
    flat = " ".join(text.split())
    i = flat.lower().find(fig.lower())
    assert i >= 0, (c["chunk_id"], fig)
    a, b = max(0, i - 120), min(len(flat), i + len(fig) + 110)
    a = flat.find(" ", a) + 1 if a else 0
    b = flat.rfind(" ", 0, b) if b < len(flat) else b
    return ("..." if a else "") + flat[a:b] + ("..." if b < len(flat) else "")


def join_view(row: dict) -> dict:
    """One join row against its company's corpus: each figure's anchored passages and the fewest that hold them all."""
    anchors, figs = row["must_retrieve"], row["must_contain"]
    anchored = [c for c in TENANT_CHUNKS[row["tenant"]] if any(a.lower() in hay(c) for a in anchors)]
    holders = {f: [c for c in anchored if run_eval.contains(c["flat"], f)] for f in figs}
    assert all(holders.values()), (row["id"], {f: len(v) for f, v in holders.items()})
    cands = sorted({c["order"]: c for f in figs for c in holders[f]}.values(), key=lambda c: c["order"])

    def named(combo):
        return {a for a in anchors for c in combo if a.lower() in hay(c)}

    cover = None
    for k in range(1, len(figs) + 1):
        found = [combo for combo in combinations(cands, k)
                 if all(any(c["order"] in {x["order"] for x in combo} for c in holders[f]) for f in figs)]
        if found:
            cover = max(found, key=lambda combo: (len(named(combo)), -sum(c["order"] for c in combo)))
            break
    in_cover = {c["order"] for c in cover}
    out_figs = []
    for f in figs:
        needed = [c for c in holders[f] if c["order"] in in_cover]
        out_figs.append({"f": f, "inq": run_eval.contains(row["question"], f),
                         "at": [{"src": where(c), "sent": sentence_with(c, f)} for c in needed],
                         "more": len(holders[f]) - len(needed)})
    holds = {a: any(a.lower() in hay(c) and any(run_eval.contains(c["flat"], f) for f in figs) for c in anchored) for a in anchors}
    notes = [f"{a} is named by the row but holds none of the figures the gate checks." for a in anchors if not holds[a]]
    return {"id": row["id"], "tenant": row["tenant"], "q": row["question"], "n": len(cover), "figs": out_figs,
            "anchors": [{"a": a, "holds": holds[a]} for a in anchors], "notes": notes,
            "cover": [where(c) for c in cover]}


JOIN_VIEWS = [join_view(r) for r in JOINS]
BY_JOIN = {v["id"]: v for v in JOIN_VIEWS}
assert {v["n"] for v in JOIN_VIEWS} <= {1, 2}
TWO = [v["id"] for v in JOIN_VIEWS if v["n"] == 2]
ONE = [v["id"] for v in JOIN_VIEWS if v["n"] == 1]
IN_Q = [v["id"] for v in JOIN_VIEWS if any(f["inq"] for f in v["figs"])]
assert BY_JOIN["jn-03"]["n"] == 2 and sorted(BY_JOIN["jn-03"]["cover"]) == ["hr_policy_2026.md LV-07", "hr_policy_2026.md NP-03"], BY_JOIN["jn-03"]
assert BY_JOIN["jn-02"]["notes"] == ["NP-03 is named by the row but holds none of the figures the gate checks."], BY_JOIN["jn-02"]
assert BY_JOIN["jn-06"]["figs"][0]["at"][0]["sent"].startswith("| EMEA |"), BY_JOIN["jn-06"]        # a table row, whole
assert BY_JOIN["jn-05"]["figs"][0]["at"][0]["sent"].startswith("GST @ 18%"), BY_JOIN["jn-05"]       # a labelled line, whole
assert all(len(f["at"]) == 1 for v in JOIN_VIEWS for f in v["figs"]), "each figure shows the one passage the answer needs"
# jn-04 is asked as globex: its comparison's other half is acme's agreement, in a corpus no globex question reaches
JN04 = next(r for r in JOINS if r["id"] == "jn-04")
GLOBEX_MSA = sorted(s for s in TENANT_SLUGS["globex"] if s.startswith("msa_"))
acme_docs = dc.load_documents("acme", str(KIT / "evals"), "documind-ai-YOUR-ID")
assert JN04["tenant"] == "globex" and "ACME" in JN04["question"] and GLOBEX_MSA == ["msa_globex_2026"]
assert "msa_acme_2026" in {d["slug"] for d in acme_docs} and "msa_acme_2026" not in TENANT_SLUGS["globex"] and JN04["must_contain"] == ["120"]
BY_JOIN["jn-04"]["notes"].append("Asked as globex, whose documents hold msa_globex_2026 only: ACME's agreement, msa_acme_2026, is in "
                                 "acme's documents, which no globex question can reach, and the gate asks only for globex's 120.")
# jn-02: the gate's one word is LV-07's; NP-03, which the row also names, says the same thing in its own words
JN02 = next(r for r in JOINS if r["id"] == "jn-02")
assert JN02["must_retrieve"] == ["NP-03", "LV-07"] and JN02["must_contain"] == ["cannot"]
assert [a["src"] for a in BY_JOIN["jn-02"]["figs"][0]["at"]] == ["hr_policy_2026.md LV-07"] and BY_JOIN["jn-02"]["figs"][0]["more"] == 0
NP03_FLAT = next(c["flat"] for c in TENANT_CHUNKS["acme"] if c["chunk_id"] == "acme:hr_policy_2026#NP-03")
assert "may not be set off against the notice period" in NP03_FLAT and "cannot" not in NP03_FLAT
JOIN_SUMMARY = (f"Of the {word(len(JOINS))} join rows, the figures of {word(len(TWO))} ({phrase(TWO)}) sit in two passages and "
                f"those of the other {word(len(ONE))} in one. In {phrase(IN_Q)} a figure the gate wants is already in the question. "
                f"jn-02 names NP-03 and LV-07, and only LV-07 says \"cannot\": NP-03 says the same in other words, \"may not be set "
                f"off\". jn-04 is asked as globex, which cannot see ACME's agreement.")
JOIN_OPTIONS = "".join(f'<option value="{i}"{" selected" if v["id"] == "jn-03" else ""}>{v["id"]} &middot; {html.escape(v["q"])}</option>'
                       for i, v in enumerate(JOIN_VIEWS))

# jn-03's two clauses, as the prose quotes them
HB = {c["locator"]: c for c in TENANT_CHUNKS["acme"] if c["slug"] == "hr_policy_2026"}
LV07_SENT = sentence_with(HB["LV-07"], JN03["must_contain"][0])
NP03_SENT = sentence_with(HB["NP-03"], JN03["must_contain"][1])
JN03_DAYS = int(re.search(r"with (\d+) days of earned leave", JN03["question"]).group(1))
CAP = int(re.search(r"capped at (\d+) days", LV07_SENT).group(1))
NP03_DAYS = int(re.search(r"notice period of (\d+) days", NP03_SENT).group(1))
assert JN03["must_contain"] == [str(CAP), str(NP03_DAYS)] and JN03_DAYS > CAP and "confirmed employee" in NP03_SENT
JN03_FIGS = " and ".join(JN03["must_contain"])

# ------------------------------------------------------------------ the router's prompt, its examples, and the rows it scores
ROUTE_ROWS = route_eval.load_rows()
assert not route_eval.check_rows(ROUTE_ROWS)
DEV = [r for r in ROUTE_ROWS if r["split"] == "dev"]
HELD = route_eval.prompt_groups(ROUTE_ROWS)
SCORED = [r for r in DEV if r["group"] not in HELD]
HELD_DEV = [r for r in DEV if r["group"] in HELD]
EXS = desk_routes.PROMPT_EXEMPLARS
assert len(DEV) == len(ROUTE_ROWS), "every route row is on the dev split, as the prose says"
assert set(Counter(r["expected_route"] for r in DEV)) == {"handbook", "statute", "out_of_scope"}, "no case or clarify row"
assert route_eval.load_exemplars("kit", ROUTE_ROWS, SCORED) == EXS and route_eval.load_exemplars("none", ROUTE_ROWS, SCORED) == ()
N_EX, EX_MAX = len(EXS), route_eval.EXEMPLARS_MAX
EX_ROUTES_C = Counter(route for _, route, _ in EXS)
ROUTE_ORDER = [r for r in desk_routes.ROUTES if r in EX_ROUTES_C]


EX_ROUTES =phrase([f"{route} ({EX_ROUTES_C[route]})" for route in ROUTE_ORDER])
held_rows = []
for rid, route, q in EXS:
    group = next(r["group"] for r in ROUTE_ROWS if r["id"] == rid)
    members = [r["id"] for r in DEV if r["group"] == group]
    held_rows.append(f'<tr><td><code>{rid}</code></td><td data-label="Desk">{route}</td><td data-label="Its question">{html.escape(q)}</td>'
                     f'<td data-label="Dev rows held out with it">{", ".join(members)}</td></tr>')
assert sum(len([r for r in DEV if r["group"] == g]) for g in HELD) == len(HELD_DEV)
prompt_lines = [line for line in desk_router.prompt("Q").splitlines()]
RULE_LINES = prompt_lines[prompt_lines.index("Rules:") + 1:prompt_lines.index("Examples:") - 1]
DESK_LINES = prompt_lines[prompt_lines.index("Desks:") + 1:prompt_lines.index("Rules:") - 1]
assert all(line.startswith("- ") for line in RULE_LINES + DESK_LINES) and len(DESK_LINES) == len(desk_routes.ROUTES)


def run_kit(args: list, home: Path | None = None) -> str:
    """A kit script or cell run from deploy/ as a page runs it: list prices, no bytecode, UTF-8; HOME moved when given."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    env.pop("DOCUMIND_PROFILE", None)
    if home is not None:
        env["HOME"] = env["USERPROFILE"] = str(home)
    r = subprocess.run([sys.executable, *args], cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=env)
    assert r.returncode == 0, (args, r.stdout[-600:], r.stderr[-1200:])
    return r.stdout.rstrip("\n")


def run_cell(code: str, swap: tuple = (), home: Path | None = None) -> str:
    """A page's Python cell, between its PY markers, run from the kit's root as the page runs it."""
    body = code.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    for old, new in swap:
        assert old in body, old
        body = body.replace(old, new)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    env.pop("DOCUMIND_PROFILE", None)
    if home is not None:
        env["HOME"] = env["USERPROFILE"] = str(home)
    r = subprocess.run([sys.executable, "-"], input=body, cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=env)
    assert r.returncode == 0, r.stderr[-1200:]
    return r.stdout.rstrip("\n")


# the two offline arms, each with its report in a scratch folder: what make exemplars LOCAL=1 prints, and step 10's input
SCRATCH = Path(tempfile.mkdtemp(prefix="lesson32-"))
try:
    LOCAL = {arm: run_kit(["evals/route_eval.py", "--local", "--exemplars", arm, "--report", str(SCRATCH / f"exemplars_{arm}.json")])
             for arm in ("kit", "none")}
    LOCAL_REPORTS = {arm: json.loads((SCRATCH / f"exemplars_{arm}.json").read_text(encoding="utf-8")) for arm in ("kit", "none")}
except BaseException:
    shutil.rmtree(SCRATCH, ignore_errors=True)
    raise
DECISIONS = {d["id"]: d for d in LOCAL_REPORTS["kit"]["decisions"]}
METHODS = Counter(d["method"] for d in DECISIONS.values())
ASKED = [r for r in SCORED if DECISIONS[r["id"]].get("l1") is not None or DECISIONS[r["id"]].get("l1_error") is not None]
N_L1, N_ANCHOR, N_SINGLE = len(ASKED), METHODS["anchor"], METHODS["single"]
assert N_L1 == METHODS["model"] + METHODS["arbiter"] and len(SCORED) == N_L1 + N_ANCHOR + N_SINGLE, METHODS
assert [d["id"] for d in LOCAL_REPORTS["none"]["decisions"]] == [d["id"] for d in LOCAL_REPORTS["kit"]["decisions"]]
INDEX_ROWS = route_eval.index_rows(ROUTE_ROWS)
N_INDEX = len(INDEX_ROWS)

# the panel's questions: scored rows that reach L1 offline, two handbook, two statute and one out_of_scope, in file order
picks = []
for route, k in (("handbook", 2), ("statute", 2), ("out_of_scope", 1)):
    picks += [r for r in ASKED if r["expected_route"] == route][:k]
FEW_QS = [{"id": r["id"], "route": r["expected_route"], "q": r["question"]} for r in picks]
BASE = desk_router.prompt(FEW_QS[0]["q"]).splitlines()
EX_LINES = [f"<<<{q}>>> {route}" for _, route, q in EXS]
EX_IDX = [i for i, line in enumerate(BASE) if line in EX_LINES]
assert len(EX_IDX) == N_EX and BASE[-1] == f"Question: <<<{FEW_QS[0]['q']}>>>"
for item in FEW_QS:                       # the page's JavaScript builds each prompt as the kit's prompt() does
    kit_text = desk_router.prompt(item["q"])
    assert kit_text == "\n".join(BASE[:-1] + [f"Question: <<<{item['q']}>>>"]) and kit_text.isascii()
    with route_eval.exemplars_in_prompt(desk_router, ()):
        bare = desk_router.prompt(item["q"])
    assert bare == "\n".join(line for i, line in enumerate(kit_text.splitlines()) if i not in EX_IDX)
KIT_CHARS, BARE_CHARS = len(desk_router.prompt(FEW_QS[0]["q"])), len(desk_router.prompt(FEW_QS[0]["q"])) - sum(len(BASE[i]) + 1 for i in EX_IDX)
FEW = {"lines": BASE[:-1], "ex": EX_IDX, "qs": FEW_QS, "n_l1": N_L1}
FEW_PROMPT = "\n".join(f"<mark>{html.escape(line)}</mark>" if i in EX_IDX else html.escape(line) for i, line in enumerate(BASE))
FEW_OPTIONS = "".join(f'<option value="{i}">{q["id"]} &middot; {q["route"]} &middot; {html.escape(q["q"])}</option>' for i, q in enumerate(FEW_QS))

# ------------------------------------------------------------------ the route eval's printed lines, read back
L1_RE = re.compile(r"^  L1 alone\s+(\d+)/(\d+) = ([\d.]+)% \[([\d.]+)%, ([\d.]+)%\]  \(L1's own route.*; (\d+) failed\)$", re.M)
ROUTE_RE = re.compile(r"^  top-1 route accuracy\s+(\d+)/(\d+) = ([\d.]+)% \[([\d.]+)%, ([\d.]+)%\]$", re.M)
L2_RE = re.compile(r"^  sent to L2\s+(\d+)/(\d+) = ([\d.]+)% \[([\d.]+)%, ([\d.]+)%\]$", re.M)
COST_RE = re.compile(r"^  router cost\s+Rs ([\d.]+) in all, Rs ([\d.]+) a turn$", re.M)
EXLINE_RE = re.compile(r"^  exemplars: .* - (\d+) in the L1 prompt; ", re.M)


def read_route(text: str, what: str) -> dict:
    """route_eval.py's report lines for one arm: L1 alone, the top-1 route, the arbiter's share, the cost, the examples."""
    got = {k: rx.search(text) for k, rx in (("l1", L1_RE), ("route", ROUTE_RE), ("l2", L2_RE), ("cost", COST_RE), ("ex", EXLINE_RE))}
    missing = [k for k, m in got.items() if m is None]
    assert not missing, f"{what}: no {', '.join(missing)} line: re-record it with the page's command"
    l1, rt, l2 = (tuple(int(x) for x in got[k].groups()[:2]) for k in ("l1", "route", "l2"))
    return {"l1": l1, "l1_ci": tuple(float(x) for x in got["l1"].groups()[3:5]), "route": rt,
            "route_ci": tuple(float(x) for x in got["route"].groups()[3:5]), "l2": l2, "cost": float(got["cost"].group(1)),
            "examples": int(got["ex"].group(1)), "failed": int(got["l1"].group(6))}


LOC = {arm: read_route(LOCAL[arm], f"route_eval --local --exemplars {arm}") for arm in ("kit", "none")}
assert (LOC["kit"]["examples"], LOC["none"]["examples"]) == (N_EX, 0)
assert {k: v for k, v in LOC["kit"].items() if k not in ("cost", "examples")} == {k: v for k, v in LOC["none"].items() if k not in ("cost", "examples")}
assert LOC["kit"]["l1"][1] == N_L1 and LOC["kit"]["route"][1] == len(SCORED)
DIFF_LINES = [line for line in LOCAL["none"].splitlines() if line not in LOCAL["kit"].splitlines()]
assert len(DIFF_LINES) == 2 and DIFF_LINES[0].startswith("  exemplars: none") and DIFF_LINES[1].startswith("  router cost"), DIFF_LINES
LOCAL_COST_DIFF = LOC["kit"]["cost"] - LOC["none"]["cost"]
EX_TOKENS = LOCAL_COST_DIFF / N_L1 / USD_INR / (L_IN / 1e6)
assert abs(EX_TOKENS - (KIT_CHARS - BARE_CHARS) / 4) <= 1.5, (EX_TOKENS, KIT_CHARS - BARE_CHARS)
LOCAL_L1 = route_eval.rate(*LOC["kit"]["l1"])
LOCAL_ROUTE = route_eval.rate(*LOC["kit"]["route"])

# ------------------------------------------------------------------ Wilson at the join rows' size
N = len(JOINS)
lo_all = route_eval.wilson(N, N)[0]
SEP = [(a, b) for a in range(N + 1) for b in range(a) if route_eval.wilson(b, N)[1] < route_eval.wilson(a, N)[0]]
W_GAP = min(a - b for a, b in SEP)
assert sorted(p for p in SEP if p[0] - p[1] == W_GAP) == [(W_GAP, 0), (N, N - W_GAP)], "at the smallest gap, only the two ends"
W_SEP_PAIRS = f"all {N} against {N - W_GAP}, or {W_GAP} against none"


def ci(k: int, n: int) -> str:
    """'[74.1%, 100.0%]': route_eval.rate()'s interval alone."""
    return route_eval.rate(k, n).split(" = ", 1)[1].split(" ", 1)[1]


# ------------------------------------------------------------------ cells: the commands the page asks you to paste
Q03 = JN03["question"]
assert "'" not in Q03 and '"' not in Q03
CELLS = {}
CELLS["ui"] = r"""gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="stream"' \
  --project "$PROJECT" --freshness 10m --limit 1 --format=json | python -c "
import sys, json
for e in json.load(sys.stdin):
    r = e['jsonPayload']
    print('stream | brain', r.get('brain'), '| tenant', r.get('tenant'), '| model', r.get('model'), '| pool', r.get('pool'),
          '| tokens_in', r.get('tokens_in'), '| tokens_out', r.get('tokens_out'), '| generate_ms', r.get('generate_ms'),
          '| Rs %.4f' % (85 * (r.get('cost_usd') or 0)))"
"""
CELLS["edit"] = r"""python - <<'PY'
import ast, json, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
import prompt_bench
source = open("services/rag-api/generator.py", encoding="utf-8").read()
kit = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(source).body
       if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) in ("SYSTEM", "DATED_RULE")}
RULE = "__RULE__"
edit = prompt_bench.edit_system(kit["SYSTEM"], add=[RULE])
print(edit, end="")
versions = json.load(open("services/rag-api/prompt_versions.json", encoding="utf-8"))["versions"]
for arm, system in (("kit", kit["SYSTEM"]), ("edit", edit)):
    sha = prompt_bench.prompt_sha(system, kit["DATED_RULE"])
    print(f"{arm:4} prompt sha256 {sha[:16]}...  {next((v for v, s in versions.items() if s == sha), 'no version names it')}")
PY""".replace("__RULE__", RULE)
CELLS["tests"] = r"""for t in test_prompt_bench.py test_route_exemplars.py; do
  python -m unittest discover -s evals/tests -p "$t" 2>&1 | grep -E "^(Ran|OK|FAILED)" | sed -E "s/ in [0-9.]+s$//"
done"""
POOL_FILE = "/tmp/jn03_pool.json"
CELLS["pool"] = (r"""curl -s -X POST "$API/v1/passages" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \
  -d '{"query": "__Q__", "tenant_id": "acme", "top_k": 6}' -o __POOL__
python - <<'PY'
import json, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
from run_eval import anchors_found, contains, load_golden
row = next(r for r in load_golden() if r["id"] == "jn-03")
body = json.load(open("__POOL__", encoding="utf-8"))
pool, usage = body["passages"], body["usage"]
print(f"{len(pool)} passages from {usage['stages'].get('retrieval_backend')}; the route's own bill: {usage['tokens_in']} tokens in, "
      f"{usage['tokens_out']} out")
for p in pool:
    text = " ".join(p["text"].split())
    found = [f for f in row["must_contain"] if contains(text, f)]
    name = p["source_uri"].rsplit("/", 1)[-1]
    print(f"  [{p['n']}] {name} {p.get('section') or 'p.' + str(p.get('page'))} | figures: {', '.join(found) or '-'} | {text[:60]}")
print("anchors in the pool:", anchors_found(row, pool))
PY""").replace("__Q__", Q03).replace("__POOL__", POOL_FILE)
LEVELS_ARGS = "--shape join --levels LOW,MEDIUM,HIGH"
CELLS["levels"] = f'make bench PROJECT=$PROJECT BENCH_ARGS="{LEVELS_ARGS}"'
RULE_ARGS = f"--shape join --levels LOW --add-rule '{RULE}' --report $HOME/cot_rule.json"
CELLS["rule"] = f'make bench PROJECT=$PROJECT BENCH_ARGS="{RULE_ARGS}"'
CELLS["answers"] = r"""python - <<'PY'
import json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
report = json.load(open(os.path.expanduser("~/cot_rule.json"), encoding="utf-8"))
for a in (a for a in report["answers"] if a["id"] == "jn-03"):
    thought = sum(c.get("thought", 0) for c in a["calls"])
    visible = sum(c.get("visible", 0) for c in a["calls"])
    print(f"== {a['arm']} {a['level']}: {'pass' if a['pass'] else 'did not pass: ' + a['why']} | thought {thought} | visible {visible} "
          f"| Rs {a['cost_inr']:.4f}")
    print(a.get("answer") or a.get("error"))
    for c in a.get("cites", []):
        print(f"   quote, {c['check']}: {c['quote'][:90]}")
PY"""
SWAP_Q = FEW_QS[0]["q"]
assert '"' not in SWAP_Q and "\\" not in SWAP_Q
CELLS["swap"] = r'''python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
import route_eval
desk_router, desk_routes = route_eval.router()
QUESTION = "__Q__"


def example_lines(prompt):
    """The L1 prompt's example lines: <<<question>>> desk."""
    return [line for line in prompt.splitlines() if line.startswith("<<<")]


kit = desk_router.prompt(QUESTION)
with route_eval.exemplars_in_prompt(desk_router, ()):
    bare = desk_router.prompt(QUESTION)
print(f"with the examples: {len(kit):,} characters, {len(example_lines(kit))} example lines")
print(f"inside the swap:   {len(bare):,} characters, {len(example_lines(bare))} example lines")
print("every other line unchanged:", [line for line in kit.splitlines() if line not in example_lines(kit)] == bare.splitlines())
print("after the swap, the kit's tuple again:", desk_router.PROMPT_EXEMPLARS is desk_routes.PROMPT_EXEMPLARS)
rows = route_eval.load_rows()
held = route_eval.prompt_groups(rows)
dev = [r for r in rows if r["split"] == "dev"]
print(f"{len(dev)} dev rows: {sum(r['group'] in held for r in dev)} in the examples' {len(held)} groups, out of every arm's score; "
      f"{sum(r['group'] not in held for r in dev)} scored")
PY'''.replace("__Q__", SWAP_Q)
CELLS["local_kit"] = "make exemplars LOCAL=1"
CELLS["local_none"] = "make exemplars LOCAL=1 EXEMPLARS=none"
LIVE = 'python evals/route_eval.py --live-l1 --project "$PROJECT" --exemplars {arm} --report "$HOME/exemplars_{arm}.json"'
CELLS["live_kit"] = '# make exemplars PROJECT=$PROJECT REPORT="$HOME/exemplars_kit.json" runs this line\n' + LIVE.format(arm="kit")
CELLS["live_none"] = ('# make exemplars PROJECT=$PROJECT EXEMPLARS=none REPORT="$HOME/exemplars_none.json" runs this line\n'
                      + LIVE.format(arm="none"))
assert X["mk_exemplars"].rstrip().endswith("$(PY) evals/route_eval.py $(if $(LOCAL),--local,--live-l1 --project $(PROJECT)) "
                                           "--exemplars $(or $(EXEMPLARS),kit) $(if $(RUNS),--runs $(RUNS),) "
                                           '$(if $(REPORT),--report "$(REPORT)",)')
CELLS["flips"] = r'''python - <<'PY'
import json, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
import paired
import route_eval
rows = {r["id"]: r for r in route_eval.load_rows()}


def read(arm):
    """One arm's report: its examples, L1's route on each turn it was asked, and whether each row's route was right."""
    report = json.load(open(os.path.expanduser(f"~/exemplars_{arm}.json"), encoding="utf-8"))
    l1 = {d["id"]: (d["l1"] or {}).get("route") for d in report["decisions"]
          if d.get("l1") is not None or d.get("l1_error") is not None}
    return len(report["exemplars"]["examples"]), l1, {v["id"]: v["route_ok"] for v in report["rows"]}


arms = {arm: read(arm) for arm in ("kit", "none")}
l1_right = {arm: {i: got in rows[i]["acceptable_routes"] for i, got in arms[arm][1].items()} for arm in arms}
for arm, (examples, l1, route) in arms.items():
    print(f"{arm:4} {examples} examples | L1 alone {route_eval.rate(sum(l1_right[arm].values()), len(l1))} "
          f"| top-1 route {route_eval.rate(sum(route.values()), len(route))}")
for what, a, b in (("L1 alone", l1_right["kit"], l1_right["none"]), ("top-1 route", arms["kit"][2], arms["none"][2])):
    both, kit_only, none_only, neither = paired.pairs(a, b)
    diff, lo, hi = paired.newcombe(both, kit_only, none_only, neither)
    print(f"{what}, paired over {both + kit_only + none_only + neither} rows: both right {both}, kit only {kit_only}, "
          f"none only {none_only}, neither {neither}")
    print(f"   none - kit = {100 * diff:+.1f} points [{100 * lo:+.1f}, {100 * hi:+.1f}] (Newcombe), "
          f"exact McNemar p = {paired.mcnemar(kit_only, none_only):.3f}")
kit_l1, none_l1 = arms["kit"][1], arms["none"][1]
flips = sorted(i for i in set(kit_l1) & set(none_l1) if kit_l1[i] != none_l1[i])
print(f"turns where L1's route changed with the examples out: {len(flips)}")
for i in flips:
    r = rows[i]
    print(f"  {i:8} expects {r['expected_route']:12} kit {str(kit_l1[i]):12} none {str(none_l1[i]):12} {r['question'][:58]}")
PY'''
CELLS = {k: v.rstrip("\n") for k, v in CELLS.items()}
assert all(not v.endswith("\\") for v in CELLS.values())

LABELS = {
    "ui": "run in the operator shell, after the question in the Chat page (reads the API's log; changes nothing)",
    "edit": "run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: no model is called)",
    "tests": "run in the operator shell, in $DEMO_ROOT (the kit's own tests: a scripted model and a stand-in lane; Rs 0)",
    "pool": "run in the operator shell, in $DEMO_ROOT (one /v1/passages call, then a Python cell; no model call)",
    "levels": f"run in the operator shell, in $DEMO_ROOT ({N} pools, then {3 * N} answers on your lane)",
    "rule": f"run in the operator shell, in $DEMO_ROOT ({N} pools, then {2 * N} answers at LOW, two arms)",
    "answers": "run in the operator shell (a Python cell; reads the report, Rs 0)",
    "swap": "run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0)",
    "local_kit": "run in the operator shell, in $DEMO_ROOT (offline: no project, Rs 0)",
    "local_none": "run in the operator shell, in $DEMO_ROOT (offline, the examples out: Rs 0)",
    "live_kit": f"run in the operator shell, in $DEMO_ROOT (the kit's examples: {N_L1} {L1_MODEL} calls, the arbiter's, and embeddings)",
    "live_none": "run in the operator shell, in $DEMO_ROOT (the same rows, no example)",
    "flips": "run in the operator shell (a Python cell; reads the two reports, Rs 0)",
}


def bash_window(label: str, code: str) -> str:
    """A command window: the label says where to run it, the copy button copies it."""
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    """An expected-output window: read only, no copy button."""
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


# ------------------------------------------------------------------ the offline cells, run here on the kit
OUT_EDIT = run_cell(CELLS["edit"])
assert OUT_EDIT.splitlines()[:-2] == EDIT_SYSTEM.rstrip("\n").splitlines()
assert OUT_EDIT.splitlines()[-2] == f"kit  prompt sha256 {KIT_SHA[:16]}...  {PROMPT_LABEL}"
assert OUT_EDIT.splitlines()[-1] == f"edit prompt sha256 {EDIT_SHA[:16]}...  no version names it"

test_out = []
N_TESTS = {}
for t in ("test_prompt_bench.py", "test_route_exemplars.py"):
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "evals/tests", "-p", t], cwd=str(KIT), capture_output=True,
                       text=True, encoding="utf-8", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
    lines = [re.sub(r" in [0-9.]+s$", "", line) for line in (r.stdout + r.stderr).splitlines() if re.match(r"^(Ran|OK|FAILED)", line)]
    N_TESTS[t] = int(re.search(r"Ran (\d+) tests", lines[0]).group(1))
    assert r.returncode == 0 and lines == [f"Ran {N_TESTS[t]} tests", "OK"], (t, lines)   # google-genai's own check ran too
    test_out += lines
OUT_TESTS = "\n".join(test_out)

OUT_SWAP = run_cell(CELLS["swap"])
assert OUT_SWAP.splitlines()[0] == f"with the examples: {KIT_CHARS:,} characters, {N_EX} example lines"
assert OUT_SWAP.splitlines()[1] == f"inside the swap:   {BARE_CHARS:,} characters, 0 example lines"
assert OUT_SWAP.splitlines()[2:4] == ["every other line unchanged: True", "after the swap, the kit's tuple again: True"]
assert OUT_SWAP.splitlines()[4] == (f"{len(DEV)} dev rows: {len(HELD_DEV)} in the examples' {len(HELD)} groups, out of every arm's score; "
                                    f"{len(SCORED)} scored")

MAKE_ECHO = "python evals/route_eval.py --local --exemplars {arm}"
OUT_LOCAL = {arm: MAKE_ECHO.format(arm=arm) + "\n" + LOCAL[arm] for arm in ("kit", "none")}

OUT_FLIPS_LOCAL = run_cell(CELLS["flips"], home=SCRATCH)
flip_lines = OUT_FLIPS_LOCAL.splitlines()
assert flip_lines[0].startswith(f"kit  {N_EX} examples | L1 alone {LOCAL_L1} | top-1 route {LOCAL_ROUTE}"), flip_lines[0]
assert flip_lines[1].startswith(f"none 0 examples | L1 alone {LOCAL_L1} | top-1 route {LOCAL_ROUTE}"), flip_lines[1]
assert flip_lines[-1] == "turns where L1's route changed with the examples out: 0" and "exact McNemar p = 1.000" in OUT_FLIPS_LOCAL
LOCAL_P = "1.000"

# the bench's report and printed lines, from its own offline harness: a scripted model and a stand-in lane
spec = importlib.util.spec_from_file_location("lesson32_bench_harness", KIT / "evals" / "tests" / "test_prompt_bench.py")
HARNESS = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = HARNESS
spec.loader.exec_module(HARNESS)
_, H_LEVELS, _, _, _ = HARNESS.run(["--rows", "lk-06,rf-01", "--levels", "LOW,MEDIUM,HIGH"], report=False)
_, H_RULE, _, _, H_REPORT = HARNESS.run(["--rows", "lk-06,rf-01", "--levels", "LOW", "--add-rule", RULE])
(SCRATCH / "cot_rule.json").write_text(json.dumps(H_REPORT), encoding="utf-8")
OUT_ANSWERS_HARNESS = run_cell(CELLS["answers"], swap=(('a["id"] == "jn-03"', 'a["id"] == "lk-06"'),), home=SCRATCH)
assert [line.split(":")[0] for line in OUT_ANSWERS_HARNESS.splitlines() if line.startswith("== ")] == ["== kit LOW", "== edit LOW"], OUT_ANSWERS_HARNESS
shutil.rmtree(SCRATCH, ignore_errors=True)

ANSWER_RE = re.compile(r"^    (\S+)\s+(kit|edit)\s+(MINIMAL|LOW|MEDIUM|HIGH)\s+run (\d+)\s+(pass|FAIL|ERROR)\s+thought\s+([\d,]+)\s+"
                       r"visible\s+([\d,]+)\s+Rs (\d+\.\d{4})(?:  (\d+) calls)?(?:  (.*))?$", re.M)
SUMMARY_RE = re.compile(r"^  (kit|edit)\s+(MINIMAL|LOW|MEDIUM|HIGH)\s+(\d+)/(\d+) = ([\d.]+)% \[([\d.]+)%, ([\d.]+)%\]\s+(\d+) of (\d+)\s+"
                        r"(\d+) of (\d+)\s+(\d+)\s+(\d+)\s+(\d+\.\d{4})$", re.M)
RETRIED_RE = re.compile(r"^  retried (kit|edit) (\w+): (\d+) of (\d+) were cut off", re.M)
TOTAL_RE = re.compile(r"^  Rs (\d+\.\d{4}) in all: (\d+) answers, (\d+) model calls on (.+), priced at list", re.M)


def read_bench(text: str, what: str) -> dict:
    """prompt_bench.py's printed run read back: each answer's line, each arm and level's summary row, the retries, the total."""
    answers = [{"id": m[0], "arm": m[1], "level": m[2], "run": int(m[3]), "verdict": m[4], "thought": int(m[5].replace(",", "")),
                "visible": int(m[6].replace(",", "")), "rs": float(m[7]), "calls": int(m[8] or 1)} for m in ANSWER_RE.findall(text)]
    summary = {(m[0], m[1]): {"passed": int(m[2]), "n": int(m[3]), "lo": float(m[5]), "hi": float(m[6]), "thought": int(m[11]),
                              "visible": int(m[12]), "rs": float(m[13])} for m in SUMMARY_RE.findall(text)}
    total = TOTAL_RE.search(text)
    assert answers and summary and total, f"{what}: the answer lines, the summary or the total is missing: re-record it"
    assert len(answers) == int(total.group(2)) == sum(s["n"] for s in summary.values()), what
    return {"answers": answers, "summary": summary, "retried": {(m[0], m[1]): int(m[2]) for m in RETRIED_RE.findall(text)},
            "total": float(total.group(1)), "calls": int(total.group(3))}


HB_LEVELS = read_bench(H_LEVELS, "the harness's levels run")
assert sorted(HB_LEVELS["summary"]) == [("kit", "HIGH"), ("kit", "LOW"), ("kit", "MEDIUM")] and len(HB_LEVELS["answers"]) == 6
HB_RULE = read_bench(H_RULE, "the harness's rule run")
assert sorted(HB_RULE["summary"]) == [("edit", "LOW"), ("kit", "LOW")] and len(HB_RULE["answers"]) == 4
assert "edit  rule added: " + RULE + " - 6 rules; no temperature" in H_RULE and f"prompt sha256 {EDIT_SHA}" in H_RULE

# ------------------------------------------------------------------ the author's runs, recorded
REC = {k: pb.recorded(LESSON, f"{k}.txt") for k in ("ui_stream", "passages_jn03", "join_levels", "cot_rule", "cot_answers",
                                                      "exemplars_kit", "exemplars_none", "exemplar_flips")}
awaiting = lambda text: text.startswith("[awaiting")  # noqa: E731
LEVELS = ["LOW", "MEDIUM", "HIGH"]


def grid(b: dict, arms_levels: list, heads: list) -> str:
    """One row per golden row: each arm and level's verdict and thought tokens, from the recorded answer lines."""
    rows = []
    for rid in [r["id"] for r in JOINS]:
        cells = []
        for (arm, level), head in zip(arms_levels, heads):
            got = [a for a in b["answers"] if a["id"] == rid and a["arm"] == arm and a["level"] == level]
            cells.append(f'<td data-label="{head}">' + ("-" if not got else
                         f"{got[0]['verdict']} &middot; thought {got[0]['thought']:,} &middot; visible {got[0]['visible']:,}") + "</td>")
        rows.append(f"<tr><td>{rid}</td>{''.join(cells)}</tr>")
    head = "".join(f"<th>{h}</th>" for h in heads)
    return ('<div class="tw"><div class="tw-scroll" tabindex="0"><table class="comp-table"><thead><tr><th>Row</th>' + head
            + "</tr></thead><tbody>\n" + "\n".join(rows) + '\n</tbody></table></div><span class="scroll-hint">&#8596; SWIPE</span></div>\n')


def changed(b: dict, keys: list) -> list:
    """The rows whose verdict is not the same under every arm and level named."""
    out = []
    for rid in [r["id"] for r in JOINS]:
        v = {a["verdict"] for a in b["answers"] if a["id"] == rid and (a["arm"], a["level"]) in keys}
        if len(v) > 1:
            out.append(rid)
    return out


RESULT_LEVELS = RESULT_RULE = RESULT_FEW = ""
if not awaiting(REC["join_levels"]):
    jl = read_bench(REC["join_levels"], "data/join_levels.txt")
    keys = [("kit", lv) for lv in LEVELS]
    assert sorted(jl["summary"]) == sorted(keys) and all(s["n"] == N for s in jl["summary"].values())
    s = jl["summary"]
    moved = changed(jl, keys)
    retried = sum(jl["retried"].values())
    RESULT_LEVELS = ("<p><strong>The author's lane.</strong> "
                     + "; ".join(f"{lv}: {s[('kit', lv)]['passed']} of {N} passed [{s[('kit', lv)]['lo']}%, {s[('kit', lv)]['hi']}%], "
                                 f"{s[('kit', lv)]['thought']:,} thought and {s[('kit', lv)]['visible']:,} visible tokens an answer, "
                                 f"Rs {s[('kit', lv)]['rs']:.4f}" for lv in LEVELS)
                     + f". The rows whose verdict changed between levels: {', '.join(moved) or 'none'}. "
                     + (f"{word(retried).capitalize()} answer{'s were' if retried != 1 else ' was'} cut off at the cap and asked again. " if retried else "")
                     + f"The run cost Rs {jl['total']:.2f} in all.</p>\n"
                     + grid(jl, keys, LEVELS))
if not awaiting(REC["cot_rule"]):
    cr = read_bench(REC["cot_rule"], "data/cot_rule.txt")
    keys = [("kit", "LOW"), ("edit", "LOW")]
    assert sorted(cr["summary"]) == sorted(keys) and all(s["n"] == N for s in cr["summary"].values())
    k, e = cr["summary"][("kit", "LOW")], cr["summary"][("edit", "LOW")]
    moved = changed(cr, keys)
    RESULT_RULE = (f"<p><strong>The author's lane.</strong> The kit arm passed {k['passed']} of {N} [{k['lo']}%, {k['hi']}%] with "
                   f"{k['thought']:,} thought and {k['visible']:,} visible tokens an answer; the edit arm {e['passed']} of {N} "
                   f"[{e['lo']}%, {e['hi']}%] with {e['thought']:,} thought and {e['visible']:,} visible, at Rs {e['rs']:.4f} an answer "
                   f"against Rs {k['rs']:.4f}. The rows whose verdict the rule changed: {', '.join(moved) or 'none'}. The run cost "
                   f"Rs {cr['total']:.2f} in all.</p>\n" + grid(cr, keys, ["kit, LOW", "edit, LOW"]))
if not (awaiting(REC["exemplars_kit"]) or awaiting(REC["exemplars_none"])):
    lk, ln = read_route(REC["exemplars_kit"], "data/exemplars_kit.txt"), read_route(REC["exemplars_none"], "data/exemplars_none.txt")
    assert (lk["examples"], ln["examples"]) == (N_EX, 0) and lk["route"][1] == ln["route"][1] == len(SCORED)
    overlap = lambda a, b: a[0] <= b[1] and b[0] <= a[1]  # noqa: E731
    RESULT_FEW = (f"<p><strong>The author's lane.</strong> L1 alone: {route_eval.rate(*lk['l1'])} with the examples, "
                  f"{route_eval.rate(*ln['l1'])} without; the intervals {'overlap' if overlap(lk['l1_ci'], ln['l1_ci']) else 'do not overlap'}. "
                  f"Top-1 route: {route_eval.rate(*lk['route'])} against {route_eval.rate(*ln['route'])}. Sent to the arbiter: "
                  f"{lk['l2'][0]} turns against {ln['l2'][0]}. The router's own cost: Rs {lk['cost']:.4f} against Rs {ln['cost']:.4f}. "
                  f"Step 10 pairs the two runs turn by turn.</p>\n")

# ------------------------------------------------------------------ what the runs cost: shared/prices.py and the counts
TYPICAL = (2000, 300)            # the course's typical answer, 2,000 tokens in and 300 out (lessons 4.3, 4.4 and 11.6)
RANK_USD = 1.0 / 1000            # the Ranking API's rate as lesson 2.3 states it: one US dollar per thousand requests
EMBED_USD_1K = 0.000025          # text-embedding-005, per 1,000 characters online, the rate lessons 1.6 and 3.9 use


def rs(model: str, tokens_in: int, tokens_out: int) -> float:
    """One call at list price, in rupees."""
    return prices.inr(prices.usd(model, tokens_in, tokens_out))


RS_TYPICAL = rs(GEN_MODEL, *TYPICAL)
RS_CAP = rs(GEN_MODEL, TYPICAL[0], MAX_ANSWER)
RS_RETRY = rs(GEN_MODEL, TYPICAL[0], MAX_RETRY)
RS_RANK = RANK_USD * USD_INR
EMBED_CHARS = sum(len(r["question"]) for r in INDEX_ROWS) + sum(len(r["question"]) for r in ASKED)
RS_EMBED = EMBED_CHARS / 1000 * EMBED_USD_1K * USD_INR
N_EMBED = N_INDEX + N_L1
RS_L2_CAP = rs(L2_MODEL, 0, desk_router.L2_MAX_OUTPUT_TOKENS)
N_L2_LOCAL = LOC["kit"]["l2"][0]
COSTS = [  # (step, what is billed, about with the typical answer, about with the cap)
    ("3", "one answer in the Chat page", RS_TYPICAL, RS_TYPICAL),
    ("5", "one pool read: a Ranking API request; the route bills no tokens", RS_RANK, RS_RANK),
    ("6", f"{N} pool reads; {3 * N} answers: {N} at LOW, {2 * N} at MEDIUM and HIGH",
     N * RS_RANK + 3 * N * RS_TYPICAL, N * RS_RANK + N * RS_TYPICAL + 2 * N * RS_CAP),
    ("7", f"{N} pool reads; {2 * N} answers at LOW, {N} in each arm",
     N * RS_RANK + 2 * N * RS_TYPICAL, N * RS_RANK + N * RS_TYPICAL + N * RS_CAP),
    ("9, the kit's examples", f"{N_L1} {L1_MODEL} calls, the arbiter's, and {N_EMBED} embeddings", LOC["kit"]["cost"] + RS_EMBED,
     LOC["kit"]["cost"] + RS_EMBED),
    ("9, none", f"the same rows with no example in the {N_L1} L1 prompts", LOC["none"]["cost"] + RS_EMBED, LOC["none"]["cost"] + RS_EMBED),
]
TOTAL_LOW, TOTAL_HIGH = sum(c[2] for c in COSTS), sum(c[3] for c in COSTS)


def money(rupees: float) -> str:
    """Rupees as the page and RUN_LIST.md print them: paise to two places, a figure under ten paise to three."""
    return f"Rs {rupees:.3f}" if rupees < 0.1 else f"Rs {rupees:.2f}"


cost_rows = []
for step, what, low, high in COSTS:
    cell = f"about {money(low)}" if abs(low - high) < 0.005 else f"about {money(low)} to {money(high)}"
    if step.startswith("9"):
        cell = (f"about {money(low)}: the router's own {money(low - RS_EMBED)} at the scripted token counts, and {money(RS_EMBED)} "
                f"for the embeddings; the arbiter's thinking adds at most {money(RS_L2_CAP)} a call ({N_L2_LOCAL} calls offline)")
    cost_rows.append(f'<tr><td>{step}</td><td data-label="What is billed">{html.escape(what)}</td><td data-label="Rupees">{cell}</td></tr>')
cost_rows.insert(4, '<tr><td>4, 8 and 10</td><td data-label="What is billed">the offline cells, the offline arms and the reads of the reports</td>'
                    '<td data-label="Rupees">Rs 0</td></tr>')
assert 20 < TOTAL_LOW < TOTAL_HIGH < 100, (TOTAL_LOW, TOTAL_HIGH)
RUN_LIST = (HERE / "RUN_LIST.md").read_text(encoding="utf-8") if (HERE / "RUN_LIST.md").exists() else ""
FIGURES = sorted({money(x) for x in (TOTAL_LOW, TOTAL_HIGH, RS_TYPICAL, RS_CAP, RS_RETRY, RS_L2_CAP, RS_EMBED, RS_RANK)}
                 | {money(c[2]) for c in COSTS} | {money(c[3]) for c in COSTS} | {money(c[2] - RS_EMBED) for c in COSTS[4:]})
missing = [f for f in FIGURES if f not in RUN_LIST]
assert not missing, f"RUN_LIST.md does not state {missing}: update it from this build's figures"
for k in ("ui", "pool", "levels", "rule", "answers"):           # the commands the author records are the page's own
    assert CELLS[k] in RUN_LIST, f"RUN_LIST.md's command for the {k} cell is not the page's: copy it from build.py"
for arm in ("kit", "none"):
    assert LIVE.format(arm=arm) in RUN_LIST, f"RUN_LIST.md's {arm} arm is not the page's command"
for sha in (KIT_SHA, EDIT_SHA):
    assert f"`{sha[:16]}...`" in RUN_LIST, f"RUN_LIST.md does not name the prompt sha256 {sha[:16]}..."

# ------------------------------------------------------------------ the page's numbers
OUTS = {
    "ui": ("(the author's lane: your tokens and rupees are yours)", REC["ui_stream"]),
    "edit": ("(the cell's own output, produced when this page was built; yours should match it)", OUT_EDIT),
    "tests": ("(the kit's own output, produced when this page was built)", OUT_TESTS),
    "pool": ("(the author's lane: your passages may differ)", REC["passages_jn03"]),
    "levels": ("(the author's lane: one sample a level; your answers and counts are yours)", REC["join_levels"]),
    "rule": ("(the author's lane: the same pools, two prompts)", REC["cot_rule"]),
    "answers": ("(the author's lane: the model's words are its own, run to run)", REC["cot_answers"]),
    "swap": ("(the cell's own output, produced when this page was built; yours should match it)", OUT_SWAP),
    "local_kit": ("(the kit's own output, produced when this page was built; yours should match it)", OUT_LOCAL["kit"]),
    "local_none": ("(the kit's own output, produced when this page was built: every line as above but these two)",
                   MAKE_ECHO.format(arm="none") + "\n...\n" + "\n...\n".join(DIFF_LINES)),
    "live_kit": ("(the author's lane: the routes are your models' choices)", REC["exemplars_kit"]),
    "live_none": ("(the author's lane)", REC["exemplars_none"]),
    "flips": ("(the author's lane)", REC["exemplar_flips"]),
}
WIN = {f"CELL_{k.upper()}": bash_window(LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})
WIN["OUT_FLIPS_LOCAL"] = out_window("(offline: the two --local reports, read by the same cell when this page was built)", OUT_FLIPS_LOCAL)

NEXT = MANIFEST["modules"]["03"]["lessons"]["3.3"]["name"]
STATS = {
    "KIT_LEVEL": KIT_LEVEL, "L1_MODEL": L1_MODEL, "L2_MODEL": L2_MODEL, "L2_THINKING": L2_THINKING, "EMBED_MODEL": EMBED_MODEL,
    "GEN_MODEL": GEN_MODEL, "N_EX": str(N_EX), "N_EX_WORD": word(N_EX), "EX_MAX_WORD": word(EX_MAX), "N_JOIN": str(N),
    "N_GOLDEN": str(len(GOLDEN)), "N_SCORED": str(len(SCORED)), "N_HELD": str(len(HELD_DEV)), "N_GROUPS_WORD": word(len(HELD)),
    "N_DEV": str(len(DEV)), "N_L1": str(N_L1), "N_ANCHOR": str(N_ANCHOR), "N_SINGLE": str(N_SINGLE), "N_INDEX": str(N_INDEX),
    "SCORED_BY_ROUTE": by_route(Counter(r["expected_route"] for r in SCORED)), "L1_BY_ROUTE": by_route(Counter(r["expected_route"] for r in ASKED)),
    "EX_ROUTES": EX_ROUTES, "N_DESKS_WORD": word(len(DESK_LINES)), "N_L1_RULES_WORD": word(len(RULE_LINES)),
    "W11": ci(N, N), "W_SEP_PAIRS": W_SEP_PAIRS, "W_GAP_WORD": word(W_GAP), "W_EXAMPLE": f"the offline run's L1 alone, {LOCAL_L1}",
    "JN03_Q": html.escape(Q03), "JN03_DAYS": str(JN03_DAYS), "JN03_FIGS": JN03_FIGS, "NP03_DAYS": str(NP03_DAYS),
    "LV07_SENT": html.escape(LV07_SENT), "NP03_SENT": html.escape(NP03_SENT),
    "DRAFT_ORDER": phrase([f"<code>{f}</code>" for f in DRAFT_ORDER]), "DRAFT_ORDER_CODE": "<code>" + ", ".join(DRAFT_ORDER) + "</code>",
    "GENAI_VERSION": GENAI_VERSION, "GENAI_PIN": GENAI_PIN, "MAX_ANSWER": f"{MAX_ANSWER:,}", "MAX_RETRY": f"{MAX_RETRY:,}",
    "CHUNK_CHARS": f"{dc.CHUNK_CHARS:,}", "CHUNK_OVERLAP": str(dc.CHUNK_OVERLAP), "UI_TOP_K": str(UI_TOP_K), "TOP_K": str(bench.TOP_K),
    "N_POOL_WORD": word(bench.TOP_K).capitalize(), "N_LEVELS_WORD": word(len(LEVELS)), "N_LEVEL_ANSWERS": str(3 * N),
    "ANSWER_CHARS": str(bench.ANSWER_CHARS), "RULE_HTML": html.escape(RULE), "PROMPT_LABEL": PROMPT_LABEL,
    "KIT_SHA_SHORT": KIT_SHA[:16], "EDIT_SHA_SHORT": EDIT_SHA[:16],
    "P_IN": f"{P_IN:.2f}", "P_OUT": f"{P_OUT:.2f}", "L_IN": f"{L_IN:.2f}", "L_OUT": f"{L_OUT:.2f}", "USD_INR": str(USD_INR),
    "RATIO": word(round(P_OUT / P_IN)), "TYPICAL_IN": f"{TYPICAL[0]:,}", "TYPICAL_OUT": str(TYPICAL[1]),
    "RS_TYPICAL": money(RS_TYPICAL)[3:], "RS_CAP": money(RS_CAP)[3:], "RS_RETRY": money(RS_RETRY)[3:], "RS_RANK": money(RS_RANK)[3:],
    "COST_ROWS": "\n".join(cost_rows), "TOTAL_LOW": money(TOTAL_LOW)[3:], "TOTAL_HIGH": money(TOTAL_HIGH)[3:],
    "LOCAL_L1": LOCAL_L1, "LOCAL_ROUTE": LOCAL_ROUTE, "LOCAL_COST_KIT": f"{LOC['kit']['cost']:.4f}",
    "LOCAL_COST_NONE": f"{LOC['none']['cost']:.4f}", "LOCAL_COST_DIFF": f"{LOCAL_COST_DIFF:.4f}", "EX_TOKENS": str(round(EX_TOKENS)),
    "LOCAL_P": LOCAL_P, "N_TESTS_BENCH": str(N_TESTS["test_prompt_bench.py"]), "N_TESTS_SWAP": str(N_TESTS["test_route_exemplars.py"]),
    "N_PASSAGES_ROWS": str(1 + 2 * N), "N_BENCH_ANSWERS": str(3 * N + 2 * N),
    "JOIN_OPTIONS": JOIN_OPTIONS, "JOIN_SUMMARY": html.escape(JOIN_SUMMARY), "FEW_OPTIONS": FEW_OPTIONS, "HELD_ROWS": "\n".join(held_rows),
    "FEW_PROMPT": FEW_PROMPT, "GATE_ROUTE": f"{route_eval.DEV_GATES['route']:.0%}", "GATE_DESK": f"{route_eval.DEV_GATES['per_desk']:.0%}",
    "RESULT_LEVELS": RESULT_LEVELS, "RESULT_RULE": RESULT_RULE, "RESULT_FEW": RESULT_FEW, "NEXT": html.escape(NEXT),
}


def subst(text: str) -> str:
    """Every %%NAME%% in a part, filled from the windows and the numbers above."""
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ------------------------------------------------------------------ the two panels' script
JS_BODY = r"""var J = __JOINS__, F = __FEW__;
function esc(t){ return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function num(n){ return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
var jsel = document.getElementById('jx-row'), jout = document.getElementById('jx-out');
function jrender(){
  var r = J[+jsel.value];
  var h = '<p><b>' + esc(r.id) + '</b> &middot; asked as ' + esc(r.tenant) + ' &middot; its figures sit in ' + r.n + (r.n === 1 ? ' passage' : ' passages') + ': ' + esc(r.cover.join(', ')) + '</p>';
  h += '<p><span class="jx-tag">question</span>' + esc(r.q) + '</p>';
  h += '<p>The gate wants: ' + r.figs.map(function(f){ return '<span class="jx-tag' + (f.inq ? ' q' : '') + '">' + esc(f.f) + (f.inq ? ', already in the question' : '') + '</span>'; }).join('') + '</p>';
  h += '<ul>' + r.figs.map(function(f){
    return '<li><b>' + esc(f.f) + '</b>: ' + f.at.map(function(p){ return esc(p.src) + ', &ldquo;' + esc(p.sent) + '&rdquo;'; }).join('; ') +
      (f.more ? ' (' + f.more + ' more of the row\'s passages hold it too)' : '') + '</li>'; }).join('') + '</ul>';
  h += '<p>The row names: ' + r.anchors.map(function(a){ return '<span class="jx-tag' + (a.holds ? '' : ' q') + '">' + esc(a.a) + '</span>'; }).join('') + '</p>';
  r.notes.forEach(function(n){ h += '<p>' + esc(n) + '</p>'; });
  jout.innerHTML = h;
}
if (jsel && jout){ jsel.addEventListener('change', jrender); jrender(); }
var fq = document.getElementById('fx-q'), fpre = document.getElementById('fx-prompt'), fstat = document.getElementById('fx-stat'),
    fbtns = document.querySelectorAll('.fx-b'), arm = 'kit';
function frender(){
  var q = F.qs[+fq.value], lines = F.lines.concat(['Question: <<<' + q.q + '>>>']);
  var kitText = lines.join('\n'), bareText = lines.filter(function(l, i){ return F.ex.indexOf(i) < 0; }).join('\n');
  fpre.innerHTML = lines.map(function(l, i){ var ex = F.ex.indexOf(i) >= 0; return ex ? (arm === 'kit' ? '<mark>' + esc(l) + '</mark>' : null) : esc(l); })
    .filter(function(x){ return x !== null; }).join('\n');
  fstat.innerHTML = 'This row expects <b>' + esc(q.route) + '</b>. With the examples the prompt is ' + num(kitText.length) + ' characters, about ' +
    num(Math.floor(kitText.length / 4)) + ' tokens; without them, ' + num(bareText.length) + ', about ' + num(Math.floor(bareText.length / 4)) +
    '. The examples add ' + num(kitText.length - bareText.length) + ' characters to each of the ' + F.n_l1 + ' L1 calls in a run.';
  for (var i = 0; i < fbtns.length; i++){ var on = fbtns[i].getAttribute('data-arm') === arm;
    fbtns[i].classList.toggle('on', on); fbtns[i].setAttribute('aria-pressed', on ? 'true' : 'false'); }
}
if (fq && fpre && fstat){
  for (var i = 0; i < fbtns.length; i++){ fbtns[i].addEventListener('click', function(){ arm = this.getAttribute('data-arm'); frender(); }); }
  fq.addEventListener('change', frender); frender();
}
"""
JS_BODY = (JS_BODY.replace("__JOINS__", json.dumps(JOIN_VIEWS, ensure_ascii=True, separators=(",", ":")))
           .replace("__FEW__", json.dumps(FEW, ensure_ascii=True, separators=(",", ":"))))
assert "</script" not in JS_BODY and "<!--" not in JS_BODY
JS = "<script>\n(function(){\n'use strict';\n" + JS_BODY + "})();\n</script>\n"

# node runs the two panels on a stand-in page: every join row, every question in both arms, held to the kit's figures
NODE = r"""var els = {};
function el(id){ return els[id] || (els[id] = {value: '0', innerHTML: '', on: {}, addEventListener: function(t, f){ this.on[t] = f; }}); }
function button(arm){ var b = {attrs: {'data-arm': arm}, cls: {}, on: {}, getAttribute: function(k){ return this.attrs[k]; },
  setAttribute: function(k, v){ this.attrs[k] = v; }, addEventListener: function(t, f){ this.on[t] = f; }};
  b.classList = {toggle: function(c, on){ b.cls[c] = on; }}; return b; }
var buttons = [button('kit'), button('none')];
var document = {getElementById: el, querySelectorAll: function(sel){ return sel === '.fx-b' ? buttons : []; }};
el('jx-row').value = '__JN03__';
(new Function('document', '"use strict";\n' + __BODY__))(document);
var out = {first: el('jx-out').innerHTML, joins: [], few: []};
for (var i = 0; i < __NJ__; i++){ el('jx-row').value = String(i); el('jx-row').on.change(); out.joins.push(el('jx-out').innerHTML); }
for (var q = 0; q < __NQ__; q++){ el('fx-q').value = String(q); el('fx-q').on.change();
  buttons.forEach(function(b){ b.on.click.call(b); out.few.push({arm: b.attrs['data-arm'], prompt: el('fx-prompt').innerHTML,
    stat: el('fx-stat').innerHTML, pressed: buttons.map(function(x){ return x.attrs['aria-pressed']; })}); }); }
process.stdout.write(JSON.stringify(out));
"""
JN03_INDEX = next(i for i, v in enumerate(JOIN_VIEWS) if v["id"] == "jn-03")
NODE = (NODE.replace("__BODY__", json.dumps(JS_BODY)).replace("__JN03__", str(JN03_INDEX))
        .replace("__NJ__", str(len(JOIN_VIEWS))).replace("__NQ__", str(len(FEW_QS))))
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-1200:]
panels = json.loads(node.stdout)
assert panels["first"] == panels["joins"][JN03_INDEX], "the join panel opens on jn-03, as its select does"
for view, shown in zip(JOIN_VIEWS, panels["joins"]):
    assert f"<b>{view['id']}</b>" in shown and html.escape(view["q"], quote=False) in shown, view["id"]
    assert all(html.escape(p["sent"], quote=False) in shown for f in view["figs"] for p in f["at"]), view["id"]
    assert all(html.escape(n, quote=False) in shown for n in view["notes"]), view["id"]
for k, shown in enumerate(panels["few"]):
    item, arm = FEW_QS[k // 2], shown["arm"]
    with route_eval.exemplars_in_prompt(desk_router, None if arm == "kit" else ()):
        want = desk_router.prompt(item["q"])
    assert html.unescape(re.sub(r"</?mark>", "", shown["prompt"])) == want, (item["id"], arm)
    assert shown["prompt"].count("<mark>") == (N_EX if arm == "kit" else 0) and shown["pressed"] == (["true", "false"] if arm == "kit" else ["false", "true"])
    kit_len = len(desk_router.prompt(item["q"]))
    assert f"the prompt is {kit_len:,} characters" in shown["stat"] and f"to each of the {N_L1} L1 calls" in shown["stat"], shown["stat"]
assert len(panels["joins"]) == N and len(panels["few"]) == 2 * len(FEW_QS)

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {GEN_MODEL} at {KIT_LEVEL}, cap {MAX_ANSWER} | ModelDraft {DRAFT_ORDER} (google-genai {GENAI_VERSION}, pin {GENAI_PIN}) | "
      f"joins {N}: two passages {TWO}, one {ONE}, in the question {IN_Q} | Wilson {N}/{N} {ci(N, N)}, gap {W_GAP} | router: {N_EX} "
      f"examples, {len(SCORED)} scored ({len(HELD_DEV)} held), L1 {N_L1}, offline L1 {LOCAL_L1}, cost {LOC['kit']['cost']} vs "
      f"{LOC['none']['cost']} ({EX_TOKENS:.1f} tokens a call) | tests {N_TESTS} | runs about Rs {TOTAL_LOW:.2f} to Rs {TOTAL_HIGH:.2f}")
