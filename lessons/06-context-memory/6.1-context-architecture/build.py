"""Build lesson 6.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Assemble the context: what rides every model call. A brain sends its model far more than the question, and sends most
of it again on every call of the turn. make context-sources (commands/context_sources.py, mk/memory.mk) runs one turn on
a brain, reads every model call where the brain's adapter hands it to google-genai, and splits each into six sources:
the system prompt, the tool declarations, the thread so far, the question, the model's own calls and the tool results,
each with its tokens and its rupees at list price, the turn's total held equal to the turn's limits.Meter. A search on
a chat brain has a model call of its own inside it (rag-api's answer), printed under the search; the Desk's search
(/v1/passages) has none. TOP_K= is the Change-it; TURNS=3 puts a thread under the measured turn.

Computed here, offline, by running the kit's own command in the chat image's pins (so this build runs under the chat
venv's python), as the kit's own test runs it: context_sources.main() with --offline --json on every brain (langchain,
langgraph, adk, direct, desk) with TOP_K unset and 3, and the three chat brains on a fresh thread and on turn 3 of one:
sixteen records for the Level 0 widget, in five processes side by side, each search of the Rs 0 lane ranked once a
process and handed out as a copy. Two more runs print as make context-sources OFFLINE=1 prints (BRAIN=langgraph, and
BRAIN=langchain TURNS=3), and two show the command's refusal of TURNS on a brain that keeps no thread. The Change-it's
comparison cell runs here on the two records its bash cell writes. Every fact the prose states about the kit is
asserted below, from the records or from the kit's source.

Recorded from the author's lane with pb.recorded(): batch 1's probe (BRAIN=langgraph and BRAIN=adk: does count_tokens on
location global honour the system instruction and the declarations, and how close is its count to the bill), batch
2's five brains, TOP_K=3 on langgraph and on the Desk, and TURNS=3 on langchain. RUN_LIST.md says how.

    <venvs312/chat python> pagekit/build.py 6.1
"""
import ast
import html
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True                     # nothing below leaves a __pycache__ in deploy/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "6.1"
title = ("<title>Lesson 6.1 Assemble the context: what rides every model call - the system prompt, the tool declarations, "
         "the thread, the question and the tool results, each in tokens and rupees | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"

# the kit's brains import LangChain, LangGraph and google-adk: the build runs them, so it needs the chat image's pins
MISSING = [m for m in ("langchain", "langgraph", "langchain_google_genai", "google.adk", "google.genai")
           if importlib.util.find_spec(m.split(".")[0]) is None or importlib.util.find_spec(m) is None]
assert not MISSING, f"build lesson 6.1 with the chat image's pins (venvs312/chat): {MISSING} missing from {sys.executable}"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* one turn by source: the six sources wear six slots of the validated categorical palette in an order whose every touching pair passes (CVD 17.6, normal 29.0 on white); rag-api's own call is two greys */
.cx{--k-system:#1baf7a;--k-tools:#4a3aa7;--k-thread:#e87ba4;--k-question:#008300;--k-calls:#2a78d6;--k-results:#eb6834;--k-ragfix:#c3c2b7;--k-chunks:#898781;--k-grid:#e7e5e4;}
.cx-ctl{display:flex;flex-wrap:wrap;gap:8px 18px;margin:0 0 10px;}
.cx-grp{min-width:0;}
.cx-grp b{display:block;font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--slate);margin:0 0 4px;}
.cx-seg{display:flex;flex-wrap:wrap;gap:4px;}
.cx-seg button{font:inherit;font-size:13px;line-height:1.2;padding:6px 10px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);min-height:max(44px,var(--touch));cursor:pointer;-webkit-tap-highlight-color:transparent;}
.cx-seg button[aria-pressed="true"]{border:2px solid var(--teal);background:var(--teal-light);font-weight:700;}
.cx-seg button:disabled{opacity:.45;cursor:not-allowed;}
.cx-seg button:active,button.cx-row:active{transform:scale(.98);}
.cx-chart{background:#fff;border:1px solid var(--border);border-radius:12px;padding:10px 12px;min-width:0;}
.cx-legend{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12.5px;line-height:1.4;color:var(--slate);margin:0 0 8px;}
.cx-legend span{display:inline-flex;align-items:center;gap:6px;}
.cx-key{display:inline-block;width:12px;height:12px;border-radius:3px;flex:none;}
.k-system{background:var(--k-system);}.k-tools{background:var(--k-tools);}.k-thread{background:var(--k-thread);}.k-question{background:var(--k-question);}
.k-calls{background:var(--k-calls);}.k-results{background:var(--k-results);}.k-ragfix{background:var(--k-ragfix);}.k-chunks{background:var(--k-chunks);}
.cx-row{display:grid;grid-template-columns:9.5em minmax(0,1fr);gap:4px 10px;align-items:center;width:100%;font:inherit;font-size:12.5px;line-height:1.35;text-align:left;color:var(--navy);background:none;border:1px solid transparent;border-radius:8px;padding:6px;margin:0 0 2px;min-height:max(44px,var(--touch));cursor:pointer;-webkit-tap-highlight-color:transparent;}
.cx-row[aria-pressed="true"]{border-color:var(--teal);background:var(--teal-light);}
.cx-row.cx-static{cursor:default;}
.cx-l{min-width:0;overflow-wrap:anywhere;}
.cx-l b{display:block;font-size:12.5px;}
.cx-l span{display:block;font-family:var(--mono);font-size:11.5px;color:var(--slate);}
.cx-track{display:block;min-width:0;padding:4px 0;border-right:1px solid var(--k-grid);background-image:linear-gradient(to right,var(--k-grid) 1px,transparent 1px);}
.cx-bar{display:flex;gap:2px;height:18px;max-width:100%;}
.cx-bar i{display:block;height:100%;min-width:3px;flex-basis:0;}
.cx-bar i:last-child{border-radius:0 4px 4px 0;}
.cx-none{display:block;font-size:12.5px;color:var(--slate);padding:2px 0;}
.cx-axis{display:grid;grid-template-columns:9.5em minmax(0,1fr);gap:0 10px;padding:0 7px;font-family:var(--mono);font-size:11px;color:var(--slate);}
.cx-ticks{position:relative;height:1.5em;min-width:0;}
.cx-ticks span{position:absolute;top:0;transform:translateX(-50%);white-space:nowrap;}
.cx-ticks span:first-child{transform:none;}
.cx-ticks span:last-child{transform:translateX(-100%);}
.cx-detail{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:10px 12px;margin:10px 0 0;font-size:var(--small-size);line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.cx-detail h5{font-size:var(--small-size);color:var(--navy);margin:0 0 6px;}
.cx-detail p{font-size:var(--small-size);margin:6px 0 0;}
.cx-list{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:minmax(0,1fr) auto auto auto;gap:2px 12px;font-size:12.5px;}
.cx-list li{display:contents;}
.cx-list span{min-width:0;}
.cx-list .v{font-family:var(--mono);text-align:right;white-space:nowrap;}
.cx-list .nm{display:inline-flex;align-items:center;gap:6px;}
.cx-note{font-size:var(--small-size);line-height:1.55;color:var(--slate);margin:10px 0 0;}
.cx-tot{margin:10px 0 0;}
.cx-tot table{width:100%;border-collapse:collapse;font-size:12.5px;color:var(--slate);}
.cx-tot th,.cx-tot td{padding:4px 6px;border-top:1px solid var(--border);text-align:left;vertical-align:top;}
.cx-tot th{font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--slate);border-top:0;}
.cx-tot td.v,.cx-tot th.v{font-family:var(--mono);text-align:right;white-space:nowrap;}
.cx-tot small{display:block;font-size:11.5px;color:var(--slate);}
.cx-tot tr.sum td{color:var(--navy);font-weight:700;}
.cx-tot tr.sum small{font-weight:400;}
@media (hover:hover) and (pointer:fine){.cx-seg button:hover:not(:disabled),button.cx-row:hover{border-color:var(--teal);}}
/* on a phone the row's label takes its own line and the bar the full width beneath it */
@media (max-width: 640px){.cx-row{grid-template-columns:minmax(0,1fr);}.cx-axis{grid-template-columns:minmax(0,1fr);}.cx-axis > span:first-child{display:none;}.cx-list{grid-template-columns:minmax(0,1fr) auto auto;}.cx-list .pc{display:none;}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("Every <code>make</code> target on these pages is a one-line entry in the kit's <code>mk/ingestion.mk</code> or "
         "<code>mk/lifecycle.mk</code>.",
         "Every <code>make</code> target on these pages is a short entry in one of the kit's <code>mk/*.mk</code> files; "
         "this lesson's, <code>context-sources</code>, is in <code>mk/memory.mk</code>."),
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson reads what a search hands the chat model, so point acme at the kit's own index for the duration, "
         "whose citations carry the kit's chunk ids and pages as the offline runs' do, and put the pin back at the end."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head: step 3 asks in the browser as you, and every lane run from step 6 on searches "
         "as <code>documind-ui-sa</code>.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)

# ------------------------------------------------------------------ verbatim kit excerpts
BR, CT, DA, LIM = "services/chat/brains.py", "services/chat/tools.py", "services/chat/desk_agent.py", "services/chat/limits.py"
CS, MK, TS = "commands/context_sources.py", "mk/memory.mk", "commands/tests/test_context_sources.py"
GEN, CB, DS, PR, FE = ("services/rag-api/generator.py", "services/rag-api/context_budget.py", "shared/documind_schemas.py",
                       "shared/prices.py", "services/frontend/chat.py")
EXCERPTS = {
    "caption": ("services/frontend/chat.py - the caption under an agent brain's answer: the turn's limits, its rupees among them",
                block(FE, '            lim = body.get("limits") or {}', n=6)),
    "system": ("services/chat/brains.py - SYSTEM: the chat brains' own prompt, 426 characters",
               block(BR, "SYSTEM = (", end="def _summary(")),
    "assembly": ("services/chat/brains.py - where each brain puts it: create_agent's system_prompt, the LangGraph node's own list, ADK's instruction",
                 block(BR, "        self.agent = create_agent(model=llm or build_llm(), tools=TOOLS, system_prompt=SYSTEM,", n=3)
                 + "\n...\n" + block(BR, "        model = (llm or build_llm()).bind_tools(TOOLS)", n=1)
                 + "\n...\n" + block(BR, "            # The system prompt is prepended per call, never stored", n=4)
                 + "\n...\n" + block(BR, '        root = LlmAgent(name="documind_adk", model=model, instruction=SYSTEM,', n=2)),
    "decl": ("services/chat/tools.py - retrieve: the name, the docstring and three arguments become the declaration the model reads",
             block(CT, "@tool", n=10)),
    "proj": ("services/chat/tools.py - search(): what a chat brain's tool result carries back to the model",
             block(CT, '    citations = answer.get("citations", [])', end="    if cited is not None and delivered:")),
    "desk": ("services/chat/desk_agent.py - the Desk's search: /v1/passages, top_k 5, and each passage's whole text in the result",
             block(DA, "TOP_K = 5", n=1) + "\n...\n"
             + block(DA, '    r = documind_tools.retrieve(text, tenant_id=ctx["tenant"], top_k=TOP_K, doc_type=list(classes),', n=2)
             + "\n...\n" + block(DA, '            out.append({"n": n, "source": str(p.get("source_uri") or "").rsplit("/", 1)[-1],', n=2)),
    "direct": ("services/chat/brains.py - the direct brain: one retrieve, and rag-api's answer is the turn's whole cost",
               block(BR, '        r = documind_tools.retrieve(question, tenant_id=context.get("tenant_id", ""), top_k=5,', n=4)),
    "mk": ("mk/memory.mk - context-sources: the project's number for RAG_API_URL, documind-ui-sa, and the command in ~/graph-venv",
           block(MK, "context-sources: $(if $(OFFLINE),,guard-project)", n=7)),     # the target alone (6.9's follows)
    "capture": ("commands/context_sources.py - Calls: every generate_content call, read where the adapter hands it to google-genai",
                block(CS, "        real_sync, real_async = gm.Models.generate_content, gm.AsyncModels.generate_content",
                      end="        async def agenerate_content(")
                + "\n...\n" + block(CS, "        gm.Models.generate_content, gm.AsyncModels.generate_content = generate_content, agenerate_content", n=1)),
    "record": ("commands/context_sources.py - _record(): the system instruction, the declarations and the contents the call was handed",
               block(CS, "    def _record(self, model, contents, config) -> dict:", end="    @staticmethod")),
    "label": ("commands/context_sources.py - label(): each content's source, split at the turn's question",
              block(CS, "def label(contents: list[dict], question: str | None = None) -> list[str]:", end="def estimated_sources(")),
    "tokens": ("commands/context_sources.py - OFFLINE=1's count: rag-api's own estimator, a quarter of the characters",
               block(CS, "def tokens(text: str) -> int:", n=4)),
    "rag_prompt": ("commands/context_sources.py - rag_prompt(): rag-api's own prompt inside a search, estimated from generator.py",
                   block(CS, "def rag_prompt(query: str, chunks: list[dict]) -> dict:", end="class Searches:")),
    "t_sum": ("commands/tests/test_context_sources.py - every call's sources sum to what the call was sent, each content once",
              block(TS, "    def test_each_calls_sources_sum_to_what_it_was_sent(self):",
                    end="    def test_the_declarations_and_the_system_prompt_are_what_the_brain_sends(self):")),
    "count": ("commands/context_sources.py - on your lane: the model's own count_tokens, each source added in turn",
              block(CS, "def count_tokens_on(client, model: str):", end="# -----") + "\n\n\n"
              + block(CS, "def counted_pieces(raw: dict, req: dict, labels: list[str], counter: Counter) -> tuple[list, dict]:", n=5)
              + "\n...\n" + block(CS, '    if system is not None and req["system"]:', n=10)),
    "usage": ("services/chat/limits.py and shared/prices.py - what a call bills: thinking is output, a cached token a tenth",
              block(LIM, "def usage_of(message) -> tuple:", n=5) + "\n...\n"
              + block(PR, "    usd_in, usd_out = PRICES.get(model or DEFAULT_MODEL, PRICES[DEFAULT_MODEL])", n=3)),
    "topk": ("commands/context_sources.py - Searches: TOP_K is sent with every search, whatever top_k the model asked",
             block(CS, '    def __call__(self, query, tenant_id="", top_k=5, doc_type=None, assertion=None, brain=None, passages=False):', n=4)),
    "gen": ("services/rag-api/generator.py - rag-api's own call: the packed chunks in its prompt, a quote of one clause, and resolve() against what it packed",
            block(GEN, 'SYSTEM = """You are DocuMind, a retrieval-grounded assistant.', n=8) + "\n...\n"
            + block(GEN, "    context, packed = _pack(query, chunks)", n=2) + "\n...\n"
            + block(GEN, "    ans = resolve(draft, packed)", n=1)),
    "resolve": ("shared/documind_schemas.py - resolve(): a citation for each source the answer cited, and no other",
                block(DS, "    cits: List[Citation] = []", n=10) + "\n...\n"
                + block(DS, '            quote=(quote or c.get("text", ""))[:500],', n=1) + "\n...\n"
                + block(DS, "    for d in draft.citations:", n=6)),
    "t_topk": ("commands/tests/test_context_sources.py - offline, TOP_K=3 moves the tool results and nothing else",
               block(TS, "    def test_top_k_moves_the_tool_results_and_nothing_else(self):",
                     end="    def test_a_third_turn_carries_the_thread(self):")),
    "turns": ("commands/context_sources.py - TURNS: the earlier questions, asked first on one local thread",
              block(CS, "QUESTION = ", n=4) + "\n...\n" + block(CS, "    b = brains.build(brain, InMemorySaver())", n=9)),
    "history": ("services/rag-api/context_budget.py - TokenBudget's history line: the chat brains resend the whole thread",
                block(CB, "    history: int = 2_000", n=1)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert "Rs {lim['cost_inr']:.2f}" in E["caption"] and "tools: {', '.join(body.get('tool_calls') or []) or 'none'}" in E["caption"]
assert E["system"].startswith("SYSTEM = (") and E["system"].rstrip().endswith(")")
assert "system_prompt=SYSTEM" in E["assembly"] and "[SystemMessage(content=SYSTEM)] + state[\"messages\"]" in E["assembly"]
assert "instruction=SYSTEM" in E["assembly"] and "for f in for_adk()" in E["assembly"] and ".bind_tools(TOOLS)" in E["assembly"]
assert "top_k: How many passages to return" in E["decl"] and E["decl"].rstrip().endswith('"""')
assert '"citations": [' in E["proj"] and '"quote"' in E["proj"] and E["proj"].rstrip().endswith("}")
assert "passages=True" in E["desk"] and '"text": p["text"]' in E["desk"] and E["desk"].startswith("TOP_K = 5")
assert "top_k=5" in E["direct"] and "meter.charge_rag" in E["direct"]
assert '--tenant "$(TENANT)" $(if $(JSON),--json,)' in E["mk"] and "$(if $(TOP_K),--top-k \"$(TOP_K)\",)" in E["mk"]
assert "documind-ui-sa@$(PROJECT)" in E["mk"]
assert "real_sync(self_, model=model, contents=contents," in E["capture"] and "calls._answered(entry, got)" in E["capture"]
assert '"system_instruction"' in E["record"] and '"tools"' in E["record"]
assert E["label"].count("out.append(") == 5 and '"results"' in E["label"]
assert "estimate_tokens(text) if text else 0" in E["tokens"]
assert "pack_chunks" in E["rag_prompt"] and E["rag_prompt"].rstrip().endswith('"dropped": len(dropped)}')
assert 'self.assertEqual(row["residual"], 0, name)' in E["t_sum"]
assert "CountTokensConfig(system_instruction=system, tools=tools)" in E["count"] and 'f"honoured: +{got - at:,}"' in E["count"]
assert "cached_tokens * usd_in * 0.10" in E["usage"] and "output counts thinking" in E["usage"]
assert "sent = self.top_k or top_k" in E["topk"]
assert "at most twenty-five words" in E["gen"] and "_pack(query, chunks)" in E["gen"]
assert "for d in draft.citations:" in E["resolve"] and "[:500]" in E["resolve"] and "if chunk_id in seen:" in E["resolve"]
assert E["resolve"].rstrip().endswith('            cite(n, "")') and "for n in cited_numbers(draft.answer):" in E["resolve"]
assert "(5, 3)" in E["t_topk"] and "if s != \"results\":" in E["t_topk"]
assert "untrimmed" in E["history"]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts, read from its source
CS_SRC, GEN_SRC, BR_SRC = ((KIT / p).read_text(encoding="utf-8") for p in (CS, GEN, BR))


def literal(src: str, name: str):
    """A module-level literal of a kit file, read with ast (nothing of it is imported or run)."""
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) == name:
            return ast.literal_eval(node.value)
    raise KeyError(name)


QUESTION, EARLIER, TOP_K_MAX = literal(CS_SRC, "QUESTION"), literal(CS_SRC, "EARLIER"), literal(CS_SRC, "TOP_K_MAX")
BRAINS, SOURCES, LABELS = literal(CS_SRC, "BRAINS"), literal(CS_SRC, "SOURCES"), literal(CS_SRC, "LABELS")
assert BRAINS == ("langchain", "langgraph", "adk", "direct", "desk") and len(EARLIER) == 2 and TOP_K_MAX == 20
assert SOURCES == ("system", "tools", "thread", "question", "calls", "results", "other")
SRC6 = SOURCES[:6]
CHAT_SYSTEM = literal(BR_SRC, "SYSTEM")
RAG_SYSTEM = literal(GEN_SRC, "SYSTEM")
assert "5. A quote is the clause that answers - at most twenty-five words, never a whole section." in RAG_SYSTEM
cfg_src = (KIT / "services/rag-api/config.py").read_text(encoding="utf-8")
MAX_CTX = int(re.search(r"(?m)^\s+max_context_tokens: int = (\d+)$", cfg_src).group(1))
MAX_ANS = int(re.search(r"(?m)^\s+max_answer_tokens: int = (\d+)$", cfg_src).group(1))
DS_SRC = (KIT / DS).read_text(encoding="utf-8")
assert 'quote: str = Field(max_length=200, description="Exact words from that source")' in DS_SRC   # the draft's quote
assert "    quote: str = Field(max_length=500)" in DS_SRC                                               # the citation's
LIM_SRC = (KIT / LIM).read_text(encoding="utf-8")
LIMITS = {k: re.search(rf'^{k} = \w+\(os\.environ\.get\("\w+", "([\d.]+)"\)\)', LIM_SRC, re.M).group(1)
          for k in ("MAX_MODEL_CALLS", "TURN_BUDGET_INR", "TURN_DEADLINE_S")}
assert LIMITS == {"MAX_MODEL_CALLS": "12", "TURN_BUDGET_INR": "5", "TURN_DEADLINE_S": "100"}, LIMITS
PRICES = {}
exec(compile((KIT / PR).read_text(encoding="utf-8"), "prices.py", "exec"), PRICES)
FLASH = PRICES["DEFAULT_MODEL"]
RATE_IN, RATE_OUT = PRICES["PRICES"][FLASH]
USD_INR = PRICES["USD_INR"]
assert FLASH == "gemini-3.6-flash" and (RATE_IN, RATE_OUT) == (1.50, 7.50) and USD_INR == 85
RS_K_IN, RS_K_OUT = RATE_IN * USD_INR / 1000, RATE_OUT * USD_INR / 1000           # rupees per 1,000 tokens
DA_SRC = (KIT / DA).read_text(encoding="utf-8")
assert re.search(r"(?m)^TOP_K = 5$", DA_SRC) and "checkpointer=False" in DA_SRC and 'THINKING_LEVEL = "low"' in DA_SRC
PROFILE_SRC = (KIT / "shared/profile.py").read_text(encoding="utf-8")
assert 'location="global", thinking_level="low",' in PROFILE_SRC                    # the chat brains' model, thinking low
ADK_SRC = BR_SRC[BR_SRC.index("class AdkBrain:"):BR_SRC.index("class DirectBrain:")]
assert "thinking" not in ADK_SRC                                                       # ADK's brain sets no thinking level
DT_SRC = (KIT / "shared/documind_tools.py").read_text(encoding="utf-8")
assert 'f"{RAG_API_URL}/v1/passages"' in DT_SRC and 'f"{RAG_API_URL}/v1/query"' in DT_SRC
INGEST = (KIT / "services/ingest/contracts.py").read_text(encoding="utf-8")
assert '    doc_type: str = "unknown"' in INGEST                                          # a row's class until 10.4 pins one
assert "doc = doc_types.assign(_db, doc, msg.name)" in (KIT / "services/ingest/main.py").read_text(encoding="utf-8")
RAG_MAIN = (KIT / "services/rag-api/main.py").read_text(encoding="utf-8")
assert "no model call, no answer cache, no retry" in RAG_MAIN and '"event": "passages"' in RAG_MAIN
MIN_CACHE = int(re.search(r"(?m)^MIN_CACHE_TOKENS = ([\d_]+) ", (KIT / "services/rag-api/cache_manager.py").read_text(
    encoding="utf-8")).group(1).replace("_", ""))
assert MIN_CACHE == 4096, MIN_CACHE                                                  # Gemini 3's explicit-cache floor
MK_SRC = (KIT / MK).read_text(encoding="utf-8")
assert MK_SRC.count("context-sources:") == 1 and "guard-project" in MK_SRC
CAPTION = re.search(r'st\.caption\(f"brain: \{body\.get\(\'brain\'\)\} (.) tools:', (KIT / FE).read_text(encoding="utf-8")).group(1)
assert CAPTION == "·"
DRYRUN = (KIT / ".github/workflows/documind-dryrun.yml").read_text(encoding="utf-8")
assert "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_context_sources.py -v" in DRYRUN
TEST_SRC = (KIT / TS).read_text(encoding="utf-8")
N_TESTS = len(re.findall(r"(?m)^    def test_\w+\(self\):", TEST_SRC))

# ------------------------------------------------------------------ the offline runs: the kit's own command, in parallel
TMP = Path(tempfile.mkdtemp(prefix="lesson61_"))
HOME = TMP / "home"
(HOME / "AppData").mkdir(parents=True)
ENV = {k: v for k, v in os.environ.items()
       if k not in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT", "DOCUMIND_PROFILE")}
ENV.update(HOME=str(HOME), USERPROFILE=str(HOME), APPDATA=str(HOME / "AppData"), CLOUDSDK_CONFIG=str(HOME / "gcloud"),
           PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
THREADED = ("langchain", "langgraph", "adk")           # the brains with a thread: direct and the Desk keep none


def args_for(brain: str, top_k: int | None, turns: int) -> list:
    return (["--offline", "--brain", brain] + (["--top-k", str(top_k)] if top_k else [])
            + (["--turns", str(turns)] if turns > 1 else []))


JOBS = {}
for brain in BRAINS:
    for top_k in (None, 3):
        for turns in ((1, 3) if brain in THREADED else (1,)):
            JOBS[("json", brain, top_k, turns)] = args_for(brain, top_k, turns) + ["--tenant", "acme", "--json"]
# as make context-sources OFFLINE=1 (JSON=1 for the records) runs it: TENANT is the Makefile's acme
JOBS[("text", "langgraph", None, 1)] = args_for("langgraph", None, 1) + ["--tenant", "acme"]
JOBS[("text", "langchain", None, 3)] = args_for("langchain", None, 3) + ["--tenant", "acme"]
JOBS[("refuse", "direct", None, 3)] = args_for("direct", None, 3) + ["--tenant", "acme"]
JOBS[("refuse", "desk", None, 3)] = args_for("desk", None, 3) + ["--tenant", "acme"]


# As the kit's own test runs them (commands/tests/test_context_sources.py): the command's main(), argv as above, in a
# process of the chat pins, each distinct search of the Rs 0 lane ranked once and handed out as a copy (the ranking is
# deterministic and pure Python, a few seconds a search). Five such processes run side by side, one per group of jobs.
DRIVER = r'''import contextlib, copy, io, json, sys, warnings
sys.path.insert(0, "commands")
import context_sources as cs
from shared import documind_tools as dt
warnings.filterwarnings("ignore")
ranked, real = {}, dt._retrieve_local


def remembered(*args):
    key = json.dumps(args, default=str)
    if key not in ranked:
        ranked[key] = real(*args)
    return copy.deepcopy(ranked[key])


dt._retrieve_local = remembered
out = {}
for name, argv in json.loads(sys.stdin.read()).items():
    so, se = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
        code = cs.main(argv)
    out[name] = {"code": code, "stdout": so.getvalue(), "stderr": se.getvalue()}
print(json.dumps(out))
'''
(TMP / "driver.py").write_text(DRIVER, encoding="utf-8", newline="\n")


def group_of(job: tuple) -> str:
    """Which worker runs a job: one per chat brain's records, one for direct and the Desk, one for the printed runs."""
    kind, brain = job[0], job[1]
    return "printed" if kind == "text" else "direct, desk" if brain in ("direct", "desk") else brain


GROUPS = sorted({group_of(job) for job in JOBS})


def run_group(group: str) -> dict:
    jobs = {json.dumps(job): argv for job, argv in JOBS.items() if group_of(job) == group}
    r = subprocess.run([sys.executable, str(TMP / "driver.py")], input=json.dumps(jobs), cwd=str(KIT), env=ENV,
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (group, r.stderr[-1500:])
    return {tuple(json.loads(k)): v for k, v in json.loads(r.stdout.strip().splitlines()[-1]).items()}


with ThreadPoolExecutor(max_workers=len(GROUPS)) as pool:
    DONE = {k: v for got in pool.map(run_group, GROUPS) for k, v in got.items()}
assert set(DONE) == {tuple(json.loads(json.dumps(job))) for job in JOBS}, sorted(set(map(str, JOBS)) ^ set(map(str, DONE)))
for job, r in DONE.items():
    want = 2 if job[0] == "refuse" else 0
    assert r["code"] == want, (job, r["code"], r["stderr"][-800:])
DONE = {(kind, b, k, t): r for (kind, b, k, t), r in DONE.items()}
REC = {(b, k or 5, t): json.loads(DONE[("json", b, k, t)]["stdout"]) for (kind, b, k, t) in JOBS if kind == "json"}
RAW = {(b, k or 5, t): DONE[("json", b, k, t)]["stdout"] for (kind, b, k, t) in JOBS if kind == "json"}
TEXT_LG = DONE[("text", "langgraph", None, 1)]["stdout"]
TEXT_T3 = DONE[("text", "langchain", None, 3)]["stdout"]
REFUSED = {b: DONE[("refuse", b, None, 3)]["stderr"].strip() for b in ("direct", "desk")}
assert REFUSED["direct"] == ("refused: direct keeps no thread (brains.DirectBrain answers one retrieve), so its turns are "
                             "all first turns: leave TURNS out"), REFUSED
assert REFUSED["desk"].startswith("refused: desk keeps no thread (desk_agent: checkpointer=False)"), REFUSED

# what every record must hold for the page to say what it says
for (b, k, t), rec in REC.items():
    assert rec["offline"] and rec["counter"] == "estimate" and rec["question"] == QUESTION and rec["tenant"] == "acme"
    assert rec["meter"]["stopped_by"] is None and rec["meter"]["model_calls"] == len(rec["calls"])
    assert abs(rec["totals"]["model_inr"] - rec["meter"]["model_inr"]) < 1e-12           # the turn's Meter, to the paisa
    assert abs(rec["totals"]["rag_inr"] - rec["meter"]["rag_inr"]) < 1e-12
    for c in rec["calls"]:
        assert sum(c["sources"].values()) == c["usage"]["input"] and c["residual"] == 0 and c["sources"]["other"] == 0
        assert c["usage"]["thinking"] == 0 and c["usage"]["cached"] == 0                # the script neither thinks nor caches
    if rec["calls"]:
        first, last = rec["calls"][0]["sources"], rec["calls"][-1]["sources"]
        assert len(rec["calls"]) == 2 and (first["calls"], first["results"]) == (0, 0) and last["results"] > 0
        assert [s["call"] for s in rec["searches"]] == [1]                               # one search, asked by call 1
        for s in ("system", "tools", "thread", "question"):                              # these ride every call
            assert first[s] == last[s], (b, s)
    assert [s["sent"] for s in rec["searches"]] == [k] and [s["found"] for s in rec["searches"]] == [k]
L1, L3, A1, D1, K1 = REC[("langgraph", 5, 1)], REC[("langgraph", 3, 1)], REC[("adk", 5, 1)], REC[("direct", 5, 1)], REC[("desk", 5, 1)]
K3, C1, C3 = REC[("desk", 3, 1)], REC[("langchain", 5, 1)], REC[("langchain", 5, 3)]
for b in ("langgraph", "adk"):                         # LangChain and LangGraph send the same request; ADK its own
    for k in (5, 3):
        for t in (1, 3):
            same = REC[("langchain", k, t)]["calls"] == REC[(b, k, t)]["calls"]
            assert same == (b == "langgraph"), (b, k, t)
assert C1["system"]["added"] is None and L1["system"]["added"] is None and K1["system"]["added"] is None
ADK_LINE = A1["system"]["added"]
assert ADK_LINE == 'You are an agent. Your internal name is "documind_adk".', ADK_LINE
assert L1["system"]["own"] == CHAT_SYSTEM and L1["system"]["characters"] == len(CHAT_SYSTEM) == 426
assert (L1["parameters_key"], A1["parameters_key"], K1["parameters_key"]) == ("parameters", "parametersJsonSchema", "parameters")
assert L1["declarations"] == A1["declarations"] == ["retrieve", "calculate_processing_cost"]
DESK_TOOLS = K1["declarations"]
assert DESK_TOOLS == ["retrieve", "gratuity_estimate", "statutory_deadline", "threshold_check"]
assert D1["calls"] == [] and D1["totals"]["model_inr"] == 0 and D1["totals"]["turn_inr"] == D1["totals"]["rag_inr"]
assert K1["totals"]["rag_inr"] == 0 and K1["searches"][0]["passages"] and not L1["searches"][0]["passages"]
assert all(rec["searches"][0].get("rag") is None for (b, _, _), rec in REC.items() if b == "desk")
# TOP_K=3, offline: only the tool results move in the chat model's calls; rag-api's own prompt packs 3 chunks, not 5
for base, changed in ((L1, L3), (K1, K3), (A1, REC[("adk", 3, 1)]), (C1, REC[("langchain", 3, 1)])):
    for x, y in zip(base["calls"], changed["calls"]):
        assert all(x["sources"][s] == y["sources"][s] for s in SRC6 if s != "results")
    assert changed["totals"]["tokens"]["results"] < base["totals"]["tokens"]["results"]
P5, P3 = L1["searches"][0]["rag"]["prompt"], L3["searches"][0]["rag"]["prompt"]
assert (P5["packed"], P3["packed"], P5["dropped"], P3["dropped"]) == (5, 3, 0, 0) and P5["system"] == P3["system"]
assert D1["searches"][0]["rag"]["prompt"] == P5 and REC[("direct", 3, 1)]["searches"][0]["rag"]["prompt"] == P3
# TURNS=3: the thread rides both calls, the same tokens in each; the rest is the fresh turn's, token for token
T1, T2 = C3["calls"]
assert T1["sources"]["thread"] == T2["sources"]["thread"] > 0 and C3["earlier"]["turns"] == 2
assert all(C3["totals"]["tokens"][s] == C1["totals"]["tokens"][s] for s in SRC6 if s != "thread")
assert REC[("langchain", 3, 3)]["calls"][0]["sources"]["thread"] < T1["sources"]["thread"]   # TOP_K reaches the earlier turns
# the printed runs are the records' own turns
assert "model call 1 of 2 (gemini-3.6-flash): in 361, out 21" in TEXT_LG and "the turn                       0.5018" in TEXT_LG
assert "turn 3 of one thread, after 2 earlier questions" in TEXT_T3


def comma(n: int) -> str:
    return f"{n:,}"


def rs(x: float) -> str:
    return f"{x:.4f}"


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.0f}"


LG1, LG2 = L1["calls"]
FIXED1 = LG1["sources"]["system"] + LG1["sources"]["tools"]
DK1, DK2 = K1["calls"]
AK1, _ = A1["calls"]
TOT = L1["totals"]

# ------------------------------------------------------------------ the Change-it's comparison cell, on the records its bash cell writes
PY_COMPARE = r'''python - <<'PY'
import json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
NAMES = {"system": "system prompt", "tools": "tool declarations", "thread": "thread so far", "question": "question",
         "calls": "the model's calls", "results": "tool results"}


def load(name):
    """One record, as context_sources.py --json printed it."""
    with open(os.path.expanduser(f"~/{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def rag(rec):
    """rag-api's own calls inside the turn's searches: their tokens in, and the chunks packed when the record knows."""
    calls = [s["rag"] for s in rec["searches"] if s.get("rag")]
    packed = [r["prompt"]["packed"] for r in calls if r.get("prompt")]
    return sum(int(r["tokens_in"] or 0) for r in calls), (sum(packed) if packed else None)


a, b = load("cs_default"), load("cs_top3")
print(f"{'':20}{'TOP_K unset':>12}{'TOP_K=3':>10}")
for key, name in NAMES.items():
    x, y = a["totals"]["tokens"][key], b["totals"]["tokens"][key]
    print(f"{name:20}{x:>12,}{y:>10,}" + ("   moved" if x != y else ""))
(ra, ka), (rb, kb) = rag(a), rag(b)
print(f"{'rag-api, inside':20}{ra:>12,}{rb:>10,}   moved" + (f": {ka} chunks packed, then {kb}" if ka is not None else ""))
print(f"{'the model calls, Rs':20}{a['totals']['model_inr']:>12.4f}{b['totals']['model_inr']:>10.4f}")
print(f"{'rag-api, Rs':20}{a['totals']['rag_inr']:>12.4f}{b['totals']['rag_inr']:>10.4f}")
print(f"{'the turn, Rs':20}{a['totals']['turn_inr']:>12.4f}{b['totals']['turn_inr']:>10.4f}")
PY'''
WRITE_JSON = ("make context-sources OFFLINE=1 BRAIN=langgraph JSON=1 > ~/cs_default.json\n"
              "make context-sources OFFLINE=1 BRAIN=langgraph TOP_K=3 JSON=1 > ~/cs_top3.json")
assert JOBS[("json", "langgraph", None, 1)] == ["--offline", "--brain", "langgraph", "--tenant", "acme", "--json"]
assert JOBS[("json", "langgraph", 3, 1)] == ["--offline", "--brain", "langgraph", "--top-k", "3", "--tenant", "acme", "--json"]
(HOME / "cs_default.json").write_text(RAW[("langgraph", 5, 1)], encoding="utf-8")   # what the two redirections write
(HOME / "cs_top3.json").write_text(RAW[("langgraph", 3, 1)], encoding="utf-8")
body = PY_COMPARE.split("\n", 1)[1].rsplit("\nPY", 1)[0]
cmp_run = subprocess.run([sys.executable, "-"], input=body, cwd=str(TMP), env=ENV, capture_output=True, text=True,
                         encoding="utf-8")
assert cmp_run.returncode == 0, cmp_run.stderr
COMPARE = cmp_run.stdout
assert f"tool results{L1['totals']['tokens']['results']:>20,}{L3['totals']['tokens']['results']:>10,}   moved" in COMPARE, COMPARE
assert COMPARE.count("moved") == 2 and f"{P5['packed']} chunks packed, then {P3['packed']}" in COMPARE, COMPARE
shutil.rmtree(TMP, ignore_errors=True)


# ------------------------------------------------------------------ the recorded lane outputs, and the probe sliced from batch 1's
def probe_of(text: str) -> str:
    """The probe block at the end of a lane run's output (what the page's sed prints), or the stand-in while it awaits."""
    if text.startswith("[awaiting"):
        return text
    lines = text.splitlines()
    at = next((i for i, line in enumerate(lines) if line.startswith("probe (")), None)
    return "\n".join(lines[at:]) if at is not None else text


LANE = {name: pb.recorded(LESSON, f"{name}.txt") for name in (
    "probe_langgraph", "probe_adk", "lane_langchain", "lane_langgraph", "lane_adk", "lane_direct", "lane_desk",
    "lane_langgraph_topk3", "lane_desk_topk3", "lane_langchain_turns3")}
PROBE = "== BRAIN=langgraph\n" + probe_of(LANE["probe_langgraph"]) + "\n== BRAIN=adk\n" + probe_of(LANE["probe_adk"])

# ------------------------------------------------------------------ the cells and the outputs
UI_SHAPE = (f"brain: langgraph {CAPTION} tools: retrieve {CAPTION} NNNN ms {CAPTION} Rs N.NN      (the first answer)\n"
            f"brain: langgraph {CAPTION} tools: retrieve {CAPTION} NNNN ms {CAPTION} Rs N.NN      (the same question, asked again)")
CELLS = {
    "offline": "make context-sources OFFLINE=1 BRAIN=langgraph",
    "probe": ("for b in langgraph adk; do\n"
              "  echo \"== BRAIN=$b\"; make context-sources PROJECT=$PROJECT BRAIN=$b | sed -n '/^probe (/,$p'\n"
              "done"),
    "brains": ("for b in langchain langgraph adk direct desk; do\n"
               "  echo \"== BRAIN=$b\"; make context-sources PROJECT=$PROJECT BRAIN=$b\n"
               "done"),
    "write_json": WRITE_JSON,
    "compare": PY_COMPARE,
    "topk_lane": "make context-sources PROJECT=$PROJECT BRAIN=langgraph TOP_K=3",
    "topk_desk": "make context-sources PROJECT=$PROJECT BRAIN=desk TOP_K=3",
    "turns_offline": "make context-sources OFFLINE=1 BRAIN=langchain TURNS=3",
    "turns_lane": "make context-sources PROJECT=$PROJECT BRAIN=langchain TURNS=3",
}
CELL_LABELS = {
    "offline": "run in the operator shell, in the kit (a scripted model and the kit's corpus on your machine: no network, Rs 0)",
    "probe": "run in the operator shell, in the kit (two real turns on your lane, a few rupees; only each run's probe is printed)",
    "brains": "run in the operator shell, in the kit (one real turn on each brain, a few rupees each)",
    "write_json": "run in the operator shell, in the kit (two offline turns, written as records: Rs 0)",
    "compare": "run in the operator shell, in the kit (reads the two records; no network)",
    "topk_lane": "run in the operator shell, in the kit (one real turn, every search sent top_k 3)",
    "topk_desk": "run in the operator shell, in the kit (one real turn on the statute desk, top_k 3)",
    "turns_offline": "run in the operator shell, in the kit (three offline turns on one local thread: Rs 0)",
    "turns_lane": "run in the operator shell, in the kit (three real turns on one local thread, the last measured)",
}
BUILT = "(the command, run on the kit when this page was built: a scripted model, Rs 0; your offline run prints the same)"
AUTHOR = "(the author's lane: your tokens, rupees and answers are yours)"
OUT = {
    "ui": ("shape (chat.py's caption: your milliseconds and rupees are yours)", UI_SHAPE),
    "offline": (BUILT, TEXT_LG),
    "probe": ("(the author's lane, batch 1: the probe at the end of each run; your counts are yours)", PROBE),
    "lane_langchain": ("== BRAIN=langchain " + AUTHOR, LANE["lane_langchain"]),
    "lane_langgraph": ("== BRAIN=langgraph " + AUTHOR, LANE["lane_langgraph"]),
    "lane_adk": ("== BRAIN=adk " + AUTHOR, LANE["lane_adk"]),
    "lane_direct": ("== BRAIN=direct " + AUTHOR, LANE["lane_direct"]),
    "lane_desk": ("== BRAIN=desk " + AUTHOR, LANE["lane_desk"]),
    "compare": ("(the cell, run on the two records the command wrote when this page was built)", COMPARE),
    "topk_lane": (AUTHOR, LANE["lane_langgraph_topk3"]),
    "topk_desk": (AUTHOR, LANE["lane_desk_topk3"]),
    "turns_offline": (BUILT, TEXT_T3),
    "turns_lane": (AUTHOR, LANE["lane_langchain_turns3"]),
}


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUT.items()})


# ------------------------------------------------------------------ the widget's data: every record, as the widget draws it
def rides(per: list, s: str) -> str:
    """How a source rode the turn's calls, in the words the command's own turn table uses."""
    if not any(per):
        return "not in this turn"
    if s in ("calls", "results"):
        return f"from call {next(i for i, x in enumerate(per, 1) if x)} on"
    if len(per) > 1 and len(set(per)) == 1:
        return f"{per[0]:,} in each of {len(per)} calls"
    return " + ".join(f"{x:,}" for x in per)


def asked(row: dict) -> str:
    """What a call asked for, as the command prints it under the call: the tool calls, or the answer."""
    if not row["asked"]:
        return "It asked for no tool: this call wrote the answer."
    return "It asked for " + "; ".join(
        f"{a['name']}(" + ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in a["args"].items()) + ")"
        for a in row["asked"]) + "."


BRAIN_NOTE = {
    "langchain": ("LangChain's create_agent sends brains.SYSTEM and the two tools as langchain-google-genai serialises them, "
                  "on every call. The hand-built LangGraph brain sends the same request, token for token."),
    "langgraph": ("The hand-built LangGraph node puts brains.SYSTEM in front of the thread on every call, and its model is "
                  "bound to the same two tools: the same request as LangChain's, token for token."),
    "adk": (f"ADK sends brains.SYSTEM and then a line of its own, '{ADK_LINE}', and declares the same two tools as "
            "parametersJsonSchema, with titles and defaults: more tokens on every call for the same tools."),
    "direct": ("No model call of the chat's own: one retrieve, and rag-api's grounded answer is the turn "
               "(brains.DirectBrain). Everything the turn pays for rides rag-api's own call."),
    "desk": (f"The statute desk's own prompt and {len(DESK_TOOLS)} tools. Its search is /v1/passages: every passage's whole "
             "text and no model call inside, so the passages themselves are the tool results."),
}
TOPK_NOTE = {
    "chat": ("Offline, the search returns every one of the top_k passages, as if rag-api had cited all it packed, so the "
             "tool results shrink here. On your lane a chat brain's search returns only the citations rag-api's answer "
             "chose: TOP_K moves rag-api's grey bar more than the orange (step 8)."),
    "direct": "TOP_K moves the one thing the direct brain pays for: the chunks rag-api packs.",
    "desk": "/v1/passages returns all of its top_k passages, whole, so TOP_K moves the Desk's tool results on your lane too.",
}
TURN_NOTE = ("Turn 3 of one thread: the two earlier questions, the model's calls, their results and answers ride every call "
             "as the thread. TOP_K reaches every search of the run, the earlier turns' too, so at 3 the thread is smaller as well.")


def widget_run(b: str, k: int, t: int) -> dict:
    rec = REC[(b, k, t)]
    calls = []
    for c in rec["calls"]:
        calls.append({"n": c["n"], "in": c["usage"]["input"], "out": c["usage"]["output"],
                      "s": [c["sources"][s] for s in SRC6], "rs_s": [round(c["inr"]["sources"][s], 6) for s in SRC6],
                      "rs_out": round(c["inr"]["output"], 6), "rs": round(c["inr"]["call"], 6), "asked": asked(c)})
    s0 = rec["searches"][0]
    search = {"sent": s0["sent"], "asked": s0["top_k"], "found": s0["found"], "chars": s0["chars"],
              "kind": "passages" if s0["passages"] else "citations"}
    rag = s0.get("rag")
    tot = rec["totals"]
    note = BRAIN_NOTE[b]
    if b not in THREADED:
        note += f" Turn 3 is off for this brain: make context-sources answers TURNS=3 with \"{REFUSED[b]}\"."
    if k == 3:
        note += " " + TOPK_NOTE["desk" if b == "desk" else "direct" if b == "direct" else "chat"]
    if t == 3:
        note += " " + TURN_NOTE
    return {"calls": calls, "search": search,
            "rag": None if not rag else {"in": rag["tokens_in"], "out": rag["tokens_out"], "parts": [rag["prompt"]["system"], rag["prompt"]["chunks"], rag["prompt"]["question"]],
                                         "packed": rag["prompt"]["packed"], "rs": round(tot["rag_inr"], 6)},
            "tot": {"s": [tot["tokens"][s] for s in SRC6], "rs_s": [round(tot["inr"][s], 6) for s in SRC6],
                    "rides": [rides([c["sources"][s] for c in rec["calls"]], s) for s in SRC6],
                    "input": tot["input"], "output": tot["output"], "rs_out": round(tot["output_inr"], 6),
                    "model": round(tot["model_inr"], 6), "ragrs": round(tot["rag_inr"], 6), "turn": round(tot["turn_inr"], 6)},
            "earlier": {"turns": rec["earlier"]["turns"], "calls": rec["earlier"]["model_calls"],
                        "searches": rec["earlier"]["searches"], "rs": round(rec["earlier"]["inr"], 6)},
            "note": note}


TOP = max(max([c["usage"]["input"] for c in r["calls"]] + [s["rag"]["tokens_in"] for s in r["searches"] if s.get("rag")])
          for r in REC.values())
TICKS = math.ceil(TOP / 1000)
DATA = {
    "sources": [{"key": s, "name": LABELS[s]} for s in SRC6],
    "order": list(BRAINS), "start": {"brain": "langgraph", "topk": 5, "turns": 1},
    "brains": {b: {"thread": b in THREADED, "why": "" if b in THREADED else REFUSED[b].removeprefix("refused: ")} for b in BRAINS},
    "scale": TICKS * 1000, "ticks": TICKS,
    "runs": {f"{b}|{k}|{t}": widget_run(b, k, t) for (b, k, t) in REC},
}
assert len(DATA["runs"]) == 16 and TICKS == 3, (len(DATA["runs"]), TOP)
UI_JS = r"""var root = document.getElementById('cx'); if (!root) return;
  var st = {brain: D.start.brain, topk: D.start.topk, turns: D.start.turns, sel: -1};
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function num(x){ return Math.round(x).toLocaleString('en-US'); }
  function rs(x){ return 'Rs ' + x.toFixed(4); }
  function pct(a, b){ return b ? (100 * a / b).toFixed(1) + '%' : ''; }
  function run(){ return D.runs[st.brain + '|' + st.topk + '|' + (D.brains[st.brain].thread ? st.turns : 1)]; }
  function seg(id, items, now, pick, off){
    var box = document.getElementById(id); box.textContent = '';
    items.forEach(function(it){
      var b = el('button', '', it[1]); b.type = 'button';
      b.setAttribute('aria-pressed', now === it[0] ? 'true' : 'false');
      var why = off ? off(it[0]) : '';
      if (why) { b.disabled = true; b.title = why; b.setAttribute('aria-pressed', 'false'); }
      b.addEventListener('click', function(){ pick(it[0]); st.sel = -1; draw(); });
      box.appendChild(b); }); }
  function bar(parts, total){
    var w = el('span', 'cx-bar'); w.style.width = (100 * total / D.scale) + '%';
    parts.forEach(function(p){ if (!p[1]) return; var s = el('i', 'k-' + p[0]); s.style.flexGrow = p[1];
      s.title = p[2] + ': ' + num(p[1]) + ' tokens'; w.appendChild(s); });
    return w; }
  function row(i, name, n, money, b, aria){
    var r = el('button', 'cx-row'); r.type = 'button';
    r.setAttribute('aria-pressed', st.sel === i ? 'true' : 'false'); r.setAttribute('aria-label', aria);
    var l = el('span', 'cx-l'); l.appendChild(el('b', '', name)); l.appendChild(el('span', '', num(n) + ' tokens in'));
    l.appendChild(el('span', '', rs(money)));
    var t = el('span', 'cx-track'); t.style.backgroundSize = (100 / D.ticks) + '% 100%'; t.appendChild(b);
    r.appendChild(l); r.appendChild(t);
    r.addEventListener('click', function(){ st.sel = i; draw(); });
    return r; }
  function key(cls, text){ var s = el('span', 'nm'); s.appendChild(el('i', 'cx-key ' + cls)); s.appendChild(document.createTextNode(text)); return s; }
  function li(list, cls, name, n, of, money){
    var x = el('li'); x.appendChild(key(cls, name)); x.appendChild(el('span', 'v', num(n)));
    x.appendChild(el('span', 'v pc', pct(n, of))); x.appendChild(el('span', 'v', money == null ? '' : rs(money))); list.appendChild(x); }
  function detail(c){
    var box = document.getElementById('cx-detail'); box.textContent = '';
    var n = c.calls.length;
    if (st.sel < n) {
      var k = c.calls[st.sel];
      box.appendChild(el('h5', '', 'Model call ' + k.n + ' of ' + n + ': ' + num(k.in) + ' tokens in, ' + num(k.out) + ' out: ' + rs(k.rs)));
      var ul = el('ul', 'cx-list');
      D.sources.forEach(function(s, j){ if (k.s[j]) li(ul, 'k-' + s.key, s.name, k.s[j], k.in, k.rs_s[j]); });
      var o = el('li'); o.appendChild(el('span', '', 'output, at the output price')); o.appendChild(el('span', 'v', num(k.out)));
      o.appendChild(el('span', 'v pc', '')); o.appendChild(el('span', 'v', rs(k.rs_out))); ul.appendChild(o);
      box.appendChild(ul);
      box.appendChild(el('p', '', k.asked));
      return; }
    if (c.rag) {
      box.appendChild(el('h5', '', "rag-api's own call, inside the search: " + num(c.rag.in) + ' tokens in, ' + num(c.rag.out) + ' out: ' + rs(c.rag.rs)));
      var ur = el('ul', 'cx-list');
      li(ur, 'k-ragfix', 'its system prompt', c.rag.parts[0], c.rag.in, null);
      li(ur, 'k-chunks', 'the ' + c.rag.packed + ' chunks it packed', c.rag.parts[1], c.rag.in, null);
      li(ur, 'k-ragfix', 'the question', c.rag.parts[2], c.rag.in, null);
      box.appendChild(ur);
      box.appendChild(el('p', '', 'Estimated from generator.py\'s prompt, as rag-api packs it. The search sent top_k ' + c.search.sent
        + '; ' + c.search.found + ' ' + c.search.kind + ' came back, ' + num(c.search.chars) + ' characters: '
        + (n ? 'the tool result model call ' + n + ' reads.' : 'rag-api\'s answer is the turn.')));
    } }
  function totals(c){
    var box = document.getElementById('cx-tot'); box.textContent = '';
    var t = el('table'), h = el('tr');
    ['The turn by source', 'Tokens', 'Rs'].forEach(function(x, j){ h.appendChild(el('th', j ? 'v' : '', x)); });
    var hd = el('thead'); hd.appendChild(h); t.appendChild(hd);
    var tb = el('tbody');
    function add(name, sub, n, money, cls){
      var r = el('tr', cls || ''), a = el('td'); a.appendChild(document.createTextNode(name));
      if (sub) a.appendChild(el('small', '', sub));
      r.appendChild(a); r.appendChild(el('td', 'v', n == null ? '' : num(n))); r.appendChild(el('td', 'v', money == null ? '' : rs(money)));
      tb.appendChild(r); }
    if (c.calls.length) {
      D.sources.forEach(function(s, j){ add(s.name, c.tot.rides[j], c.tot.s[j], c.tot.rs_s[j]); });
      add('output', 'what the model wrote, at the output price', c.tot.output, c.tot.rs_out);
      add('the model calls', c.calls.length + ' calls: the Meter charged the same', null, c.tot.model, 'sum'); }
    if (c.rag) add('rag-api, inside the search', 'its own answer, estimated', c.rag.in, c.tot.ragrs, 'sum');
    else add('rag-api, inside the search', '/v1/passages: no model call', null, 0, 'sum');
    if (c.earlier.turns) add('the ' + c.earlier.turns + ' earlier turns', c.earlier.calls + ' model calls and ' + c.earlier.searches + ' searches, not measured', null, c.earlier.rs);
    add('the turn', 'at list price; offline, nothing is billed', null, c.tot.turn, 'sum');
    t.appendChild(tb); box.appendChild(t); }
  function draw(){
    var c = run(), B = D.brains;
    seg('cx-brain', D.order.map(function(b){ return [b, b]; }), st.brain, function(v){ st.brain = v; });
    seg('cx-topk', [[5, '5, the default'], [3, '3']], st.topk, function(v){ st.topk = v; });
    seg('cx-turn', [[1, 'a fresh thread'], [3, 'turn 3 of one']], B[st.brain].thread ? st.turns : 1, function(v){ st.turns = v; },
        function(v){ return (v === 3 && !B[st.brain].thread) ? B[st.brain].why : ''; });
    var n = c.calls.length;
    if (st.sel < 0 || st.sel > n || (st.sel === n && !c.rag)) st.sel = n ? n - 1 : 0;
    var rows = document.getElementById('cx-rows'); rows.textContent = '';
    c.calls.forEach(function(k, i){
      var parts = D.sources.map(function(s, j){ return [s.key, k.s[j], s.name]; });
      rows.appendChild(row(i, 'Model call ' + k.n, k.in, k.rs, bar(parts, k.in),
        'Model call ' + k.n + ' of ' + n + ': ' + num(k.in) + ' tokens in, ' + rs(k.rs) + '. Show its sources.')); });
    if (c.rag) rows.appendChild(row(n, "rag-api's own call", c.rag.in, c.rag.rs,
      bar([['ragfix', c.rag.parts[0], 'its system prompt'], ['chunks', c.rag.parts[1], 'the chunks it packed'], ['ragfix', c.rag.parts[2], 'the question']], c.rag.in),
      "rag-api's own call, inside the search: " + num(c.rag.in) + ' tokens in, ' + rs(c.rag.rs) + '. Show its parts.'));
    else { var r = el('div', 'cx-row cx-static'); r.appendChild(el('span', 'cx-l', 'Inside the search')); r.appendChild(el('span', 'cx-none', '/v1/passages: every passage\'s whole text, and no model call')); rows.appendChild(r); }
    var ax = document.getElementById('cx-axis'); ax.textContent = '';
    ax.appendChild(el('span', '', 'tokens in'));
    var tk = el('span', 'cx-ticks');
    for (var i = 0; i <= D.ticks; i++) { var s = el('span', '', num(i * D.scale / D.ticks)); s.style.left = (100 * i / D.ticks) + '%'; tk.appendChild(s); }
    ax.appendChild(tk);
    detail(c); totals(c);
    document.getElementById('cx-note').textContent = c.note; }
  draw();"""
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\nvar D = " + json.dumps(DATA, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
      + ";\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert "<div" not in JS and "<tr" not in JS and "<td" not in JS and "—" not in JS and "–" not in JS

# ------------------------------------------------------------------ numbers for the prose
LC_DECL, ADK_DECL = LG1["sources"]["tools"], AK1["sources"]["tools"]
STATS = {
    "QUESTION": html.escape(QUESTION), "EARLIER1": html.escape(EARLIER[0]), "EARLIER2": html.escape(EARLIER[1]),
    "SYS_CHARS": comma(len(CHAT_SYSTEM)), "SYS_TOK": comma(LG1["sources"]["system"]),
    "ADK_SYS_CHARS": comma(A1["system"]["characters"]), "ADK_SYS_TOK": comma(AK1["sources"]["system"]),
    "ADK_LINE": html.escape(ADK_LINE), "LC_DECL": comma(LC_DECL), "ADK_DECL": comma(ADK_DECL),
    "DESK_SYS_CHARS": comma(K1["system"]["characters"]), "DESK_SYS": comma(DK1["sources"]["system"]),
    "DESK_DECL": comma(DK1["sources"]["tools"]), "N_DESK_TOOLS": str(len(DESK_TOOLS)),
    "DESK_TOOLS": ", ".join(f"<code>{t}</code>" for t in DESK_TOOLS),
    "Q_TOK": comma(LG1["sources"]["question"]), "CALLS_TOK": comma(LG2["sources"]["calls"]),
    "CALL1": comma(LG1["usage"]["input"]), "CALL2": comma(LG2["usage"]["input"]), "FIXED1": comma(FIXED1),
    "FIXED1_PCT": pct(FIXED1, LG1["usage"]["input"]), "RES5": comma(LG2["sources"]["results"]),
    "RES5_PCT": pct(LG2["sources"]["results"], LG2["usage"]["input"]),
    "RES3": comma(L3["calls"][1]["sources"]["results"]), "N_CIT5": str(L1["searches"][0]["found"]),
    "CHARS5": comma(L1["searches"][0]["chars"]), "CHARS3": comma(L3["searches"][0]["chars"]),
    "DESK_RES5": comma(DK2["sources"]["results"]), "DESK_RES3": comma(K3["calls"][1]["sources"]["results"]),
    "DESK_CHARS5": comma(K1["searches"][0]["chars"]), "DESK_CALL2": comma(DK2["usage"]["input"]),
    "DESK_FIXED_PCT": pct(DK1["sources"]["system"] + DK1["sources"]["tools"], DK1["usage"]["input"]),
    "RAG_IN5": comma(P5["tokens_in"]), "RAG_CHUNKS5": comma(P5["chunks"]), "RAG_SYS": comma(P5["system"]),
    "RAG_Q": comma(P5["question"]), "RAG_IN3": comma(P3["tokens_in"]), "RAG_CHUNKS3": comma(P3["chunks"]),
    "TURN_INPUT": comma(TOT["input"]), "TURN_INR": rs(TOT["turn_inr"]), "MODEL_INR": rs(TOT["model_inr"]),
    "RAG_INR": rs(TOT["rag_inr"]), "RAG_INR3": rs(L3["totals"]["rag_inr"]), "MODEL_INR3": rs(L3["totals"]["model_inr"]),
    "TURN_INR3": rs(L3["totals"]["turn_inr"]), "DECL_TURN": comma(TOT["tokens"]["tools"]),
    "DECL_INR": rs(TOT["inr"]["tools"]), "Q_INR": rs(TOT["inr"]["question"]), "SYS_INR": rs(TOT["inr"]["system"]),
    "RES_INR": rs(TOT["inr"]["results"]), "OUT_INR": rs(TOT["output_inr"]),
    "DECL_X_Q": f"{TOT['inr']['tools'] / TOT['inr']['question']:.0f}",
    "ADK_TURN_INR": rs(A1["totals"]["turn_inr"]), "ADK_MODEL_INR": rs(A1["totals"]["model_inr"]),
    "DESK_TURN_INR": rs(K1["totals"]["turn_inr"]), "DIRECT_INR": rs(D1["totals"]["turn_inr"]),
    "THREAD3": comma(T1["sources"]["thread"]), "THREAD3_PCT": pct(T1["sources"]["thread"], T1["usage"]["input"]),
    "THREAD3_TURN": comma(C3["totals"]["tokens"]["thread"]), "THREAD3_INR": rs(C3["totals"]["inr"]["thread"]),
    "T3_CALL1": comma(T1["usage"]["input"]), "T3_MODEL_INR": rs(C3["totals"]["model_inr"]),
    "T3_TURN_INR": rs(C3["totals"]["turn_inr"]), "T3_EARLIER_INR": rs(C3["earlier"]["inr"]),
    "T3_EARLIER_CALLS": str(C3["earlier"]["model_calls"]), "T3_EARLIER_SEARCHES": str(C3["earlier"]["searches"]),
    "THREAD3_K3": comma(REC[("langchain", 3, 3)]["calls"][0]["sources"]["thread"]),
    "RATE_IN": f"{RATE_IN:.2f}", "RATE_OUT": f"{RATE_OUT:.2f}", "RS_K_IN": f"{RS_K_IN:.4f}", "RS_K_OUT": f"{RS_K_OUT:.4f}",
    "USD_INR": str(USD_INR), "MAX_CTX": comma(MAX_CTX), "MAX_ANS": comma(MAX_ANS), "TOP_K_MAX": str(TOP_K_MAX),
    "MAX_CALLS": LIMITS["MAX_MODEL_CALLS"], "BUDGET_INR": LIMITS["TURN_BUDGET_INR"], "DEADLINE_S": LIMITS["TURN_DEADLINE_S"],
    "N_TESTS": str(N_TESTS), "N_RUNS": str(len(DATA["runs"])), "SCALE": comma(DATA["scale"]), "MIN_CACHE": comma(MIN_CACHE),
    "DIRECT_REFUSAL": html.escape(REFUSED["direct"]), "DESK_REFUSAL": html.escape(REFUSED["desk"]),
}
assert int(STATS["DECL_X_Q"]) > 10 and float(STATS["FIXED1_PCT"]) > 90


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body_html = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body_html, JS)
print(f"kit: {len(DATA['runs'])} offline records ({len(JOBS)} runs of context_sources.py) | langgraph: call 1 {LG1['usage']['input']}, "
      f"call 2 {LG2['usage']['input']}, rag-api {P5['tokens_in']}, turn Rs {TOT['turn_inr']:.4f} | TOP_K=3: results "
      f"{LG2['sources']['results']} -> {L3['calls'][1]['sources']['results']}, rag-api {P5['packed']} -> {P3['packed']} chunks | "
      f"turn 3: thread {T1['sources']['thread']} a call | {len(pb.AWAITING)} lane outputs awaited")
