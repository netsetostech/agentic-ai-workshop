"""Build lesson 6.9 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Budget working memory: what one model call is sent of a conversation. Every chat brain sends its model the whole
thread on every call today; services/chat/context_window.py (kit PR 6.9-A), which nothing in the service imports, is
the window a later change would put in front of the model: the floor (the system prompt and the newest turn, whole),
earlier turns newest first within CHAT_HISTORY_TOKENS with their results cleared, the rest brought forward in one line
written by code, and the Desk's write rules on what an earlier turn carries. Offline: make window-check's twenty turns
with the window, without it, and with a smaller budget, and one call opened up message by message. Live (the author's
runs): six turns on the lane's UI and their chat rows, make window-check LIVE=1 against Gemini, and make thread.

Build-time proof: the three make window-check outputs are commands/window_check.py's own run_offline(), on the kit's
LangChain brain, lesson 6.8's scripted model and the Rs 0 lane's search, in a subprocess. Each search is BM25 on this
machine's CPU - a fraction of a second since the lane caches each chunk's counts (13 October 2026), where a long question
once came near retrieve's 25-second budget on a busy machine - and the page must not depend on the machine: so the
subprocess first runs every query the script will send, once and outside the tool's timer
(documind_tools.retrieve on the Rs 0 lane, memoised), and then asserts that no search ran inside the timer and no row
had a tool timeout. The output is what make window-check prints when every search finishes inside its budget. The same
subprocess measures the widget's data on the thread the windowed run wrote, and checks it against window() itself for
every turn and budget; the widget's JavaScript port of plan() and of the line is checked against the Python with node.
It also runs langchain 1.4.0's ClearToolUsesEdit on the same calls (clearing alone, for step 8), and the window on a
thread whose earlier search query holds a card number (the gap step 8 names). The opened-up cell runs here verbatim on
the kit. The chat-rows cell runs against a fake gcloud; the lane outputs are the author's recordings (pb.recorded,
RUN_LIST.md), and the run list's estimates are computed here and must be the ones RUN_LIST.md states.
"""
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "6.9"
title = ("<title>Lesson 6.9 Budget working memory: windowing, compaction and write rules - a ceiling on every call "
         "while the thread keeps growing | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.wd-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px 14px;margin:0 0 6px;align-items:end;}
.wd-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.wd-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.wd-in input[type=range]{width:100%;min-height:44px;margin:0;}
.wd-h{font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);letter-spacing:.5px;margin:10px 0 3px;}
.wd-bar{position:relative;display:flex;height:22px;border-radius:6px;overflow:hidden;background:#f1f5f9;border:1px solid var(--border);}
.wd-bar span{display:block;height:100%;min-width:0;}
.wd-sys{background:#334155;}.wd-new{background:var(--cyan);}.wd-kept{background:var(--teal);}.wd-line{background:#f59e0b;}.wd-old{background:#cbd5e1;}
.wd-bar .wd-ceil{position:absolute;top:0;bottom:0;width:3px;background:#b91c1c;}
.wd-cols{display:flex;align-items:flex-end;gap:2px;height:120px;margin:14px 0 2px;border-bottom:1px solid var(--border);}
.wd-col{position:relative;flex:1 1 0;height:100%;min-width:0;}
.wd-col i{position:absolute;left:0;right:0;bottom:0;display:block;}
.wd-col .f{background:#e2e8f0;}.wd-col .w{background:var(--teal);left:22%;right:22%;}.wd-col .c{height:2px;background:#b91c1c;}
.wd-col.on .f{background:#94a3b8;}
.wd-axis{display:flex;gap:2px;font-family:var(--mono);font-size:var(--kicker-size);color:var(--slate-light);}
.wd-axis span{flex:1 1 0;text-align:center;min-width:0;}
.wd-key{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12.5px;color:var(--slate);margin:8px 0 0;}
.wd-key b{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-1px;}
.wd-key .ck{width:3px;background:#b91c1c;}
.wd-line-box{font-family:var(--mono);font-size:12px;line-height:1.55;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:8px 10px;color:#78350f;overflow-wrap:anywhere;margin:8px 0 0;}
.fs-grid{display:grid;grid-template-columns:minmax(0,12em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;margin-top:10px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid span{overflow-wrap:anywhere;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
CW, BR, CB = "services/chat/context_window.py", "services/chat/brains.py", "services/rag-api/context_budget.py"
DK, DG, MK = "services/chat/desk.py", "services/chat/desk_graph.py", "mk/memory.mk"
EXCERPTS = {
    "brains_call": ("services/chat/brains.py - the LangGraph brain's model call today: the system prompt, then the whole thread",
                    block(BR, "            # The system prompt is prepended per call, never stored", n=4)),
    "budget_line": ("services/rag-api/context_budget.py - TokenBudget's lines, a conversation's history among them",
                    block(CB, "    system: int = 1_500", n=5)),
    "constants": ("services/chat/context_window.py - the budget, the cleared result, and the line's words",
                  block(CW, "HISTORY_TOKENS = int(", n=9)),
    "plan": ("services/chat/context_window.py - plan(): the rule's arithmetic, on token counts alone",
             block(CW, "def plan(", end="# ------")),
    "window_core": ("services/chat/context_window.py - window(): turns, compaction, plan(), then the line folded in",
                    block(CW, "    system, thread = _split(messages)", end="    return sent, {")),
    "compact": ("services/chat/context_window.py - an earlier turn, compacted, and its question carried the Desk's way",
                block(CW, "def carried(", end="def _copy(") + "\n...\n" + block(CW, "def _compact(", end="def _newest(")),
    "windowed": ("services/chat/context_window.py - windowed(): the window in front of the brain's model",
                 block(CW, "        def _send(self, messages):", n=8)),
    "memory_mk": ("mk/memory.mk - window-check: the script, in ~/graph-venv",
                  block(MK, "window-check: $(if $(LIVE),guard-project,)", n=4)),
    "door": ("services/chat/desk.py - the chat door, in front of POST /v1/chat on your lane (lesson 5.6)",
             block(DK, "         - Aadhaar or card numbers and no hit:", n=3)),
    "desk_prev": ("services/chat/desk.py - the Desk's own order for a previous question: mask, then cut",
                  block(DK, "    if body.prev_question is not None:", n=4)),
    "desk_state": ("services/chat/desk_graph.py - what a Desk thread keeps of a question",
                   block(DG, "class DeskState(TypedDict, total=False):", n=11)),
    "not_used": ("services/chat/context_window.py - the docstring: what the window does not use, and why",
                 block(CW, "NOT USED, AND WHY.", n=10)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert 'msg = model.invoke([SystemMessage(content=SYSTEM)] + state["messages"], **limits.call_settings(meter))' in E["brains_call"]
assert "history: int = 2_000        # earlier turns: 0 in fit(); documind-chat's agents resend whole threads, untrimmed" in E["budget_line"]
assert 'HISTORY_TOKENS = int(os.environ.get("CHAT_HISTORY_TOKENS", "2000"))' in E["constants"] and E["constants"].rstrip().endswith('LINE_TAIL = " Search again for anything you need from them.]"')
assert E["plan"].startswith("def plan(") and E["plan"].rstrip().endswith("return kept, listed, True")
assert E["window_core"].rstrip().endswith("context = _tokens(sent, count)") and "kept, listed, has_line = plan(sizes, items, budget, head)" in E["window_core"]
assert "return masked[:PREV_CHARS], n, len(masked) > PREV_CHARS" in E["compact"] and 'out.append(m.model_copy(update={"content": CLEARED, "artifact": None}))' in E["compact"]
assert "msg = self.inner.invoke(self._send(messages), stop=stop, **kwargs)" in E["windowed"]
assert "--mode $(MODE)" in E["memory_mk"] and "bash commands/graph-venv.sh commands/window_check.py" in E["memory_mk"]
assert E["door"].rstrip().endswith("so neither the brain, the checkpoint nor the model sees them.")
assert "prev = desk_rules.mask(body.prev_question)[0][:desk_router.PREV_CHARS]" in E["desk_prev"]
assert "last_question: str | None                   # masked, 300 characters at most" in E["desk_state"]
assert E["not_used"].rstrip().endswith("never the thread (desk_agent.run(); the router's prompt holds the previous question, cut to 300 characters).")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
cw_src = (KIT / CW).read_text(encoding="utf-8")
budget_default = int(re.search(r'HISTORY_TOKENS = int\(os\.environ\.get\("CHAT_HISTORY_TOKENS", "(\d+)"\)\)', cw_src).group(1))
prev_chars = int(re.search(r"^PREV_CHARS = (\d+)$", (KIT / "services/chat/desk_router.py").read_text(encoding="utf-8"), re.M).group(1))
mask_text = dict(re.findall(r'"(aadhaar|card)": "(\[[^"]+\])"', (KIT / "shared/desk_rules.py").read_text(encoding="utf-8")))
assert (budget_default, prev_chars, mask_text) == (2000, 300, {"aadhaar": "[Aadhaar]", "card": "[card no.]"}), (budget_default, prev_chars, mask_text)
assert "history: int = 2_000" in (KIT / CB).read_text(encoding="utf-8")
assert "question: str = Field(min_length=1, max_length=4000)" in (KIT / "services/chat/agent.py").read_text(encoding="utf-8")
imports = re.compile(r"(?m)^\s*(?:import\s+context_window\b|from\s+context_window\s+import\b)|import_module\(\s*['\"]context_window['\"]")
importers = [p for root in ("services", "shared", "smoke") for p in (KIT / root).rglob("*.py")
             if p.name != "context_window.py" and imports.search(p.read_text(encoding="utf-8", errors="replace"))]
assert not importers, importers                    # nothing in the service imports the window: the page says so
trims = [p.name for p in (KIT / "services/chat").glob("*.py") if p.name != "context_window.py"
         and re.search(r"trim_messages|RemoveMessage|SummarizationMiddleware|ContextEditingMiddleware|ClearToolUsesEdit",
                       p.read_text(encoding="utf-8"))]
assert not trims, trims                            # no trim, summary or clearing anywhere else: every call resends the thread
assert "the tool declarations every call also carries are outside it" in " ".join(cw_src.split())
reqs = dict(re.findall(r"^([a-z-]+)==([\d.]+)$", (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8"), re.M))
assert (reqs["langchain"], reqs["langgraph"], reqs["google-adk"]) == ("1.4.0", "1.2.12", "2.8.0"), reqs
lim_src = (KIT / "services/chat/limits.py").read_text(encoding="utf-8")
assert 'TURN_BUDGET_INR = float(os.environ.get("CHAT_TURN_BUDGET_INR", "5"))' in lim_src
rag_timeout = float(re.search(r'RAG_TIMEOUT_S = float\(os\.environ\.get\("RAG_TIMEOUT_S", "(\d+)"\)\)',
                              (KIT / "shared/documind_tools.py").read_text(encoding="utf-8")).group(1))
assert 'TIMEOUTS = {"retrieve": documind_tools.RAG_TIMEOUT_S + 5' in (KIT / "services/chat/tools.py").read_text(encoding="utf-8")
RETRIEVE_BUDGET = int(rag_timeout + 5)
assert "EVIDENCE_FLOOR = 0.5" in (KIT / "shared/documind_tools.py").read_text(encoding="utf-8")
prices_src = (KIT / "shared/prices.py").read_text(encoding="utf-8")
assert re.search(r'"gemini-3\.6-flash": \(1\.50, 7\.50\)', prices_src) and "USD_INR = 85" in prices_src
RATE_IN, USD_INR = 1.50, 85

# ------------------------------------------------------------------ the core: make window-check offline, and the widget's data
CORE_PY = r'''import copy, io, json, math, sys, warnings
warnings.filterwarnings("ignore")
sys.path[:0] = ["commands", "services/chat", "."]
import thread_replay as rp
import window_check as wc
import context_window as cw
import brains
from shared import desk_rules
from shared import documind_tools as dt
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages.utils import count_tokens_approximately as count

# every query the script will send, searched once outside the tool's timer: a busy machine cannot time one out
real, cache, misses = dt.retrieve, {}, []
def memo(query, tenant_id="", top_k=5, doc_type=None, assertion=None, brain=None, passages=False):
    key = (query, tenant_id, int(top_k or 5), json.dumps(doc_type), bool(passages))
    if key not in cache:
        misses.append(query)
        cache[key] = real(query, tenant_id=tenant_id, top_k=top_k, doc_type=doc_type, assertion=assertion, brain=brain, passages=passages)
    return copy.deepcopy(cache[key])
dt.retrieve = memo
with rp.offline([]):
    for q in wc.QUESTIONS:
        for query in dict.fromkeys((desk_rules.mask(q)[0], q)):   # windowed, the model reads it masked; full, as typed
            dt.retrieve(query, tenant_id=wc.TENANT, top_k=5)
warm = len(misses)

captured, real_ask = {}, wc.ask
def ask(brain, model, question, config, name):
    captured.update(brain=brain, config=config)
    return real_ask(brain, model, question, config, name)
wc.ask = ask

runs = {}
for name, mode, history, brain in (("windowed", "windowed", None, "langchain"), ("full", "full", None, "langchain"),
                                   ("h500", "windowed", 500, "langchain"), ("langgraph", "windowed", None, "langgraph")):
    out = io.StringIO()
    rows = wc.run_offline(mode, 20, brain, history, out=out)
    runs[name] = (out.getvalue(), rows, wc.thread_of(captured["brain"], captured["config"]))
assert len(misses) == warm, misses[warm:]
for name, (_, rows, _) in runs.items():
    assert all(not r["usage"]["tool_timeouts"] for r in rows), name

# the widget: each turn's answering call on the windowed run's thread, and window() itself at every budget
text, rows, thread = runs["windowed"]
system = SystemMessage(content=brains.SYSTEM)
BUDGETS = (0, 500, 1000, 2000, 3000, 4000)
starts = [i for i, m in enumerate(thread) if m.type == "human"] + [len(thread)]
assert len(starts) == 21
turns, S, Q = [], None, None
for n in range(1, 21):
    ai = [i for i in range(starts[n - 1], starts[n]) if thread[i].type == "ai"]
    given = [system] + thread[:ai[-1]]
    assert cw.window(given, history_tokens=2000)[1] == rows[n - 1]["largest"], n     # the largest call is the answering one
    _, thr = cw._split(given)
    units = cw.turns(thr)
    assert len(units) == n
    comp = [cw._compact(u) for u in units[:-1]]
    widest = max(len(units), 1)
    head = count([HumanMessage(content=cw._widest_line(widest))])
    sizes = [cw._tokens(c["messages"], count) for c in comp]
    items = [[math.ceil(len(cw._item(widest, q)) / 4) for q, _, _ in c["questions"]] for c in comp]
    qs = [[q for q, _, _ in c["questions"]] for c in comp]
    if n == 20:
        S, Q = sizes, qs
    per = {}
    for b in BUDGETS:
        sent, r = cw.window(given, history_tokens=b)
        assert cw.plan(sizes, items, b, head) == (r["kept"], r["listed"], r["line"] is not None), (n, b)
        per[b] = {"earlier": r["earlier_tokens"], "kept": r["kept"], "listed": r["listed"], "line": r["line"],
                  "context": r["context_tokens"], "ceiling": r["ceiling"], "dropped": r["brought_forward"]}
    rep = cw.window(given, history_tokens=2000)[1]
    turns.append({"n": n, "f": rep["floor_tokens"], "s": rep["system_tokens"], "w": rep["system_tokens"] + rep["thread_tokens"],
                  "h": head, "sizes": sizes, "it": items, "per": per})
for t in turns:
    assert t["sizes"] == S[:t["n"] - 1]                  # a turn's compacted size does not depend on the call

# langchain's own clearing on the same calls: ClearToolUsesEdit from the first call (trigger 0), the newest three kept
from langchain.agents.middleware import ClearToolUsesEdit
clear_only = []
for n in range(1, 21):
    ai = [i for i in range(starts[n - 1], starts[n]) if thread[i].type == "ai"]
    msgs = list(thread[:ai[-1]])
    ClearToolUsesEdit(trigger=0, keep=3).apply(msgs, count_tokens=lambda ms: cw.tokens(ms))
    clear_only.append(cw.tokens([system] + msgs))

# the window masks an earlier call's arguments with the rest (13 October 2026): a number in a stored search query goes as [card no.]
card = "4111 1111 1111 1111"
probe = [HumanMessage(f"My card {card} was charged twice", id="h1"),
         AIMessage("", tool_calls=[{"name": "retrieve", "args": {"query": f"card {card} charged"}, "id": "c1", "type": "tool_call"}], id="a1"),
         ToolMessage(json.dumps({"citations": [{"quote": "x " * 50}]}), tool_call_id="c1", name="retrieve", id="t1"),
         AIMessage("Answer [1].", id="z1"), HumanMessage("And then?", id="h2")]
sent, rep = cw.window([SystemMessage("sys")] + probe, history_tokens=10**6)
args_kept = any(card in json.dumps(c["args"]) for m in sent for c in (getattr(m, "tool_calls", None) or []))
question_masked = all(card not in cw.text_of(m.content) for m in sent)

def summary(rows):
    return [{"turn": r["turn"], "question": r["question"], "thread_messages": r["thread_messages"],
             "thread_tokens": r["thread_tokens"], "answer": r["answer"], "citations": r["citations"],
             "largest": r["largest"], "calls": [{k: c[k] for k in ("context_tokens", "ceiling")} for c in r["calls"]]}
            for r in rows]

print(json.dumps({"warm": warm, "texts": {k: v[0] for k, v in runs.items()}, "rows": {k: summary(v[1]) for k, v in runs.items()},
                  "card_stored": {k: any(card in cw.text_of(m.content) for m in v[2]) for k, v in runs.items()},
                  "turns": turns, "S": S, "Q": Q, "budgets": BUDGETS, "args_kept": args_kept, "question_masked": question_masked,
                  "line_parts": [cw.LINE_HEAD, cw.LINE_ALL, cw.LINE_SOME, cw.LINE_TAIL], "questions": list(wc.QUESTIONS),
                  "cleared": cw.CLEARED, "clear_only": clear_only}))
'''

T = Path(tempfile.mkdtemp(prefix="lesson69-"))
ENV = {k: v for k, v in os.environ.items() if k not in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT",
                                                         "RAG_TIMEOUT_S", "CHAT_HISTORY_TOKENS")}
ENV.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "ME": "you@your-company.com",
            "HOME": str(T), "USERPROFILE": str(T), "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION": "python"})


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.stdout[-800:], r.stderr[-2000:])
    return r.stdout


CORE = json.loads(run_cell(CORE_PY, cwd=KIT).strip().splitlines()[-1])     # twenty-one BM25 searches on the Rs 0 lane
TX, RW, TU = CORE["texts"], CORE["rows"], CORE["turns"]
BUDGETS = CORE["budgets"]
QUESTIONS = CORE["questions"]
assert CORE["warm"] == 21 and len(QUESTIONS) == 20, CORE["warm"]   # 20 questions, and question 6 masked is a 21st query
CARD = "4111 1111 1111 1111"
q_card = [i for i, q in enumerate(QUESTIONS, 1) if CARD in q]
q_long = [i for i, q in enumerate(QUESTIONS, 1) if len(q) > prev_chars]
assert (q_card, q_long) == ([6], [9]), (q_card, q_long)
Q9_LEN = len(QUESTIONS[8])

# ---- the three offline outputs, as make window-check prints them
W, F, H = RW["windowed"], RW["full"], RW["h500"]
OUT_WIN, OUT_FULL, OUT_500 = TX["windowed"], TX["full"], TX["h500"]
for t in (OUT_WIN, OUT_500):
    assert "Every call's context was within its ceiling: yes." in t, t[-600:]
assert all(c["context_tokens"] <= c["ceiling"] for run in (W, H) for row in run for c in row["calls"])
assert [r["thread_messages"] for r in W] == list(range(4, 84, 4))
assert [r["thread_tokens"] for r in W] == sorted(r["thread_tokens"] for r in W)
assert TX["langgraph"].replace("LangGraph", "LangChain") == OUT_WIN                  # BRAIN=langgraph prints the same rows
assert CORE["card_stored"] == {"windowed": True, "full": True, "h500": True, "langgraph": True}
assert CARD not in OUT_WIN + OUT_FULL + OUT_500
last = W[-1]["largest"]
W_LAST, W_CEIL, W_SYS, W_FLOOR = last["context_tokens"], last["ceiling"], last["system_tokens"], last["floor_tokens"]
W_KEPT, W_BF, W_LISTED, W_LINE = last["kept"], last["brought_forward"], last["listed"], last["line"]
W_WHOLE = last["system_tokens"] + last["thread_tokens"]
FIRST_LINE = next(r["turn"] for r in W if r["largest"]["brought_forward"])
listed_turns = [int(x) for x in re.findall(r'\((\d+)\) "', W_LINE)]
assert listed_turns == list(range(W_BF - W_LISTED + 1, W_BF + 1)) and 1 not in listed_turns, (listed_turns, W_LINE)
assert QUESTIONS[19] == "What was the first question I asked you in this conversation?" and QUESTIONS[0] not in W_LINE
assert '(6) "My corporate card [card no.] was charged twice for one flight.' in W_LINE
masked_from = next(r["turn"] for r in W if r["largest"]["masked"])
cut_from = next(r["turn"] for r in W if r["largest"]["cut"])
assert (masked_from, cut_from) == (6, 10), (masked_from, cut_from)
assert f"in turns {W_BF - W_LISTED + 1} to {W_BF}:" in W_LINE
# full: over the ceiling from turn F_FIRST, and the factor at turn 20, as the kit's own tail line prints them
over = [r["turn"] for r in F if r["largest"]["context_tokens"] > r["largest"]["ceiling"]]
F_FIRST = over[0]
assert over == list(range(F_FIRST, 21)), over
fl = F[-1]["largest"]
F_LAST, F_CEIL = fl["context_tokens"], fl["ceiling"]
F_TIMES = f"{F_LAST / F_CEIL:.1f}"
assert f"From turn {F_FIRST} on, the largest call was over the ceiling the window would hold it to; the last call sent {F_LAST:,} tokens, {F_TIMES} times its ceiling of {F_CEIL:,}." in OUT_FULL
# turn 6: the full run's search carried the card's digits and found nothing; the windowed run's found EXP-12
assert F[5]["citations"] == [] and "found nothing to cite" in F[5]["answer"], F[5]
assert W[5]["citations"][0] == "acme:hr_policy_2026#EXP-12", W[5]["citations"]
DIFF6 = W[5]["thread_tokens"] - F[5]["thread_tokens"]
assert all(W[i]["thread_tokens"] - F[i]["thread_tokens"] == (DIFF6 if i >= 5 else 0) for i in range(20))
for i in range(20):                                # the script reads only the newest turn: the same answer but on turn 6
    assert (W[i]["answer"] == F[i]["answer"]) == (i != 5), i
# 500: the ceilings 1,500 lower; the line from H_FIRST; turn 19 carries neither turn 1 nor turn 2
H_FIRST = next(r["turn"] for r in H if r["largest"]["brought_forward"])
hl = H[-1]["largest"]
H_KEPT, H_BF = hl["kept"], hl["brought_forward"]
assert all(a["largest"]["ceiling"] - b["largest"]["ceiling"] == 1500 for a, b in zip(W, H))
h19 = H[18]["largest"]["line"]
assert QUESTIONS[0] not in h19 and f'"{QUESTIONS[1]}"' not in h19, h19
w19 = W[18]["largest"]["line"]
assert QUESTIONS[0] in w19 and f'"{QUESTIONS[1]}"' in w19, w19
H_KEPT_RANGE = sorted({r["largest"]["kept"] for r in H[4:]})
# the args probe and the masked question, for the box of what the kit does not do yet
assert CORE["args_kept"] is False and CORE["question_masked"] is True        # the call's arguments masked too (13 October 2026)
# langchain's ClearToolUsesEdit alone, on the same calls: under the whole thread, over the window, and growing every turn
CLR = CORE["clear_only"]
assert len(CLR) == 20 and all(c <= t["w"] for c, t in zip(CLR, TU)) and CLR[-1] > W_LAST, (CLR, W_LAST)
assert CLR[3] < CLR[9] < CLR[19] and CLR[19] == max(CLR), CLR       # it grows with the thread, the newest results aside
CLEAR_STEP = round((CLR[19] - CLR[9]) / 10)

# ---- the cost of the live run, by the window's estimate of the same calls (the input alone)


def est_in(rows, turns):
    return sum(c["context_tokens"] for r in rows[:turns] for c in r["calls"])


def rs_in(tokens):
    return tokens * RATE_IN / 1e6 * USD_INR


LIVE = {t: (est_in(F, t), est_in(W, t)) for t in (6, 12, 20)}
LIVE_FULL20, LIVE_WIN20 = LIVE[20]
UI6_IN = est_in(F, 6)                              # step 3's six turns, as the lane sends them today: the whole thread
cfg_src = (KIT / "services/rag-api/config.py").read_text(encoding="utf-8")
RAG_IN = int(re.search(r"max_context_tokens: int = (\d+)", cfg_src).group(1))
RAG_OUT = int(re.search(r"max_answer_tokens: int = (\d+)", cfg_src).group(1))
RAG_MAX = (RAG_IN * RATE_IN + RAG_OUT * 7.50) / 1e6 * USD_INR       # one rag-api answer, one attempt, at most
assert re.search(r'"gemini-3\.6-flash": \(1\.50, 7\.50\)', prices_src)
RUN_FIGS = [f"{UI6_IN:,} tokens", f"Rs {rs_in(UI6_IN):.1f}", f"Rs {RAG_MAX:.2f} each", f"Rs {6 * RAG_MAX:.2f}",
            f"{LIVE_FULL20 + LIVE_WIN20:,} tokens, Rs {rs_in(LIVE_FULL20 + LIVE_WIN20):.0f}",
            f"{sum(LIVE[12]):,} tokens of input by the same estimate (Rs {rs_in(sum(LIVE[12])):.0f}",
            f"{sum(LIVE[6]):,} (Rs {rs_in(sum(LIVE[6])):.1f})", f"({RAG_IN:,} tokens in, {RAG_OUT:,} out)"]
run_list = " ".join((Path(__file__).parent / "RUN_LIST.md").read_text(encoding="utf-8").split())
missing = [f for f in RUN_FIGS if f not in run_list]
assert not missing, f"RUN_LIST.md no longer states: {missing}"

# ---- the cells
VENV = 'bash commands/graph-venv.sh -c \'import langchain, langgraph; print("graph-venv ok: langchain", langchain.__version__)\''

ROWS_PY = """import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" '
     f'AND jsonPayload.event="chat" AND jsonPayload.user="{os.environ["ME"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--freshness", "2h",
                      "--limit", "40", "--format", "json"], capture_output=True, text=True, check=True).stdout
rows = [e["jsonPayload"] for e in reversed(json.loads(out or "[]"))]           # oldest first
session = rows[-1]["session_id"] if rows else ""
turns = [r for r in rows if r["session_id"] == session]
open(os.path.expanduser("~/lesson69-session.txt"), "w").write(session)          # for step 7
print(f"session {session}: {len(turns)} turns, brain {', '.join(sorted({r['brain'] for r in turns}))}")
print("  turn  model calls  tokens_in  cached  tokens_out  chat Rs  search Rs")
for n, r in enumerate(turns, 1):
    print(f"  {n:>4}  {r['model_calls']:>11}  {r['tokens_in']:>9,}  {r['cached_tokens']:>6,}  {r['tokens_out']:>10,}"
          f"  {r['cost_usd'] * 85:>7.2f}  {r['rag_cost_usd'] * 85:>9.2f}")
if len(turns) > 1:
    print(f"turn {len(turns)} sent {turns[-1]['tokens_in'] / turns[0]['tokens_in']:.1f} times turn 1's input tokens")"""

OPEN_PY = """import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["commands", "services/chat", "."]
from langgraph.checkpoint.memory import InMemorySaver
import brains, context_window as cw, thread_replay as rp, window_check as wc
import shared.documind_tools as dt
BUDGET, CARD = 600, "4111 1111 1111 1111"
def passages(query, **kw):
    \"\"\"A stand-in search with no corpus behind it: three passages, the same for every question.\"\"\"
    return {"answerable": True, "confidence": "high", "citations": [
        {"chunk_id": f"acme:stand_in#{i}", "source_uri": "gs://bucket/acme/stand_in.md", "page": 1, "score": 1.0,
         "quote": f"Stand-in passage {i}. " + "The policy text a real search would return. " * 9} for i in (1, 2, 3)]}
class Seen(type(rp.scripted([]))):
    \"\"\"Lesson 6.8's script (search for the question, answer from the first passage), keeping what each call is sent.\"\"\"
    sent: list = []
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        \"\"\"Record this call's messages, then answer as the script does.\"\"\"
        self.sent.append(list(messages))
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
dt.retrieve = passages                                      # tools.search() calls documind_tools.retrieve()
seen = Seen(play=[])
model = cw.windowed(seen, history_tokens=BUDGET)            # the window in front of the model; the brain is the kit's own
brain = brains.LangChainBrain(InMemorySaver(), llm=model)
config = wc.config_for("opened-up")
for question in wc.QUESTIONS[:10]:                          # make window-check's first ten questions
    brain.answer(question, config=config, context={"tenant_id": "acme", "user_id": "you", "assertion": "", "brain": "langchain"})
thread = brain.agent.get_state(config).values["messages"]
print(f"10 turns, {len(seen.sent)} model calls, the window's budget for earlier turns {BUDGET} tokens")
print(f"the checkpoint: {len(thread)} messages, {cw.tokens(thread):,} tokens; question 6 kept as typed: "
      f"{any(CARD in cw.text_of(m.content) for m in thread)}")
print(f"the card number in what the model was sent, all {len(seen.sent)} calls: "
      f"{sum(CARD in cw.text_of(m.content) for call in seen.sent for m in call)} times")
last, report = seen.sent[-1], model.calls[-1]
print(f"turn 10's answering call, as the model received it: {len(last)} messages, {cw.tokens(last):,} tokens, "
      f"its ceiling {report['ceiling']:,} (the floor {report['floor_tokens']:,} + {BUDGET})")
for i, m in enumerate(last, 1):
    calls = ", ".join(c["name"] for c in getattr(m, "tool_calls", None) or [])
    text = "asks " + calls if calls else " ".join(cw.text_of(m.content).split())
    print(f"  {i:>2}  {m.type:6} {cw.tokens([m]):>4}  {text[:78] + ('...' if len(text) > 78 else '')}")
print(f"the line: {report['line']}")
asked = [cw.text_of(m.content).rsplit(chr(10) * 2, 1)[-1] for m in last if m.type == "human"]
print(f"turn 9's question, as this call carries it: {len(asked[-2])} characters of {len(wc.QUESTIONS[8])}")"""


def heredoc(body: str, prefix: str = "", python: str = "python") -> str:
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


CELLS = {
    "venv": VENV,
    "open": heredoc(OPEN_PY, python="~/graph-venv/bin/python"),
    "rows": heredoc(ROWS_PY),
    "win": "make window-check            # the window in front of the kit's LangChain brain: offline, Rs 0",
    "full": "make window-check MODE=full  # the same twenty turns, every call sent the whole thread",
    "h500": "make window-check HISTORY=500   # a quarter of the budget for earlier turns",
    "live": ('# twenty turns: about Rs 80 at list price before caching; add TURNS=6 for a few rupees\n'
             'make window-check LIVE=1 PROJECT="$PROJECT" SAVE=full_vs_window.json | tee full_vs_window.txt'),
    "thread": 'make thread PROJECT="$PROJECT" EMAIL="$ME" SESSION="$(cat ~/lesson69-session.txt)"',
}
for name, cmd in (("win", "make window-check"), ("full", "make window-check MODE=full"), ("h500", "make window-check HISTORY=500")):
    assert CELLS[name].startswith(cmd)
assert OUT_WIN.startswith("make window-check MODE=windowed: 20 turns of one conversation, offline, Rs 0")
assert OUT_500.splitlines()[3].endswith("at most 500 tokens")

# ---- step 4: the venv line's Python, here with the chat pins, and the opened-up cell, verbatim on the kit
VENV_PY = re.search(r"-c '(.*)'$", VENV).group(1)
OUT = {"venv": run_cell(VENV_PY), "open": run_cell(OPEN_PY, cwd=KIT)}
assert OUT["venv"] == f"graph-venv ok: langchain {reqs['langchain']}\n", OUT["venv"]
O = OUT["open"]
m_ck = re.search(r"the checkpoint: (\d+) messages, ([\d,]+) tokens; question 6 kept as typed: True", O)
m_calls = re.search(r"the card number in what the model was sent, all (\d+) calls: 0 times", O)
m_last = re.search(r"turn 10's answering call, as the model received it: (\d+) messages, ([\d,]+) tokens, its ceiling ([\d,]+) \(the floor ([\d,]+) \+ 600\)", O)
assert m_ck and m_calls and m_last, O
OPEN_MSGS, OPEN_CALLS, OPEN_SENT = int(m_ck.group(1)), int(m_calls.group(1)), int(m_last.group(1))
assert (OPEN_MSGS, OPEN_CALLS) == (40, 20)
open_line = re.search(r"^the line: (.*)$", O, re.M).group(1)
OPEN_BF = int(re.match(r"\[Earlier in this conversation, not shown here: turns 1 to (\d+)\.", open_line).group(1))
open_listed = [int(x) for x in re.findall(r'\((\d+)\) "', open_line)]
assert OPEN_BF == 7 and open_listed == list(range(2, 8)), (OPEN_BF, open_listed)
assert '(6) "My corporate card [card no.] was charged twice' in open_line
assert f"turn 9's question, as this call carries it: {prev_chars} characters of {Q9_LEN}" in O
msg_rows = re.findall(r"^\s+(\d+)  (\w+)\s+(\d+)  (.*)$", O, re.M)
kinds = [k for _, k, _, _ in msg_rows]
assert kinds == ["system", "human", "ai", "tool", "ai", "human", "ai", "tool", "ai", "human", "ai", "tool"], kinds
assert msg_rows[1][3].startswith("[Earlier in this conversation") and msg_rows[3][3].startswith('{"cleared": true')
assert msg_rows[7][3].startswith('{"cleared": true') and msg_rows[11][3].startswith('{"citations"') and OPEN_SENT == 12
assert msg_rows[9][3] == QUESTIONS[9] and msg_rows[5][3].startswith(QUESTIONS[8][:60]) and msg_rows[6][3] == "asks retrieve"
OPEN_Q9_Q, OPEN_Q9_CALL = int(msg_rows[5][2]), int(msg_rows[6][2])
assert OPEN_Q9_CALL > OPEN_Q9_Q, (OPEN_Q9_Q, OPEN_Q9_CALL)          # the call carries the whole question as its query

# ---- step 3's cell, against a fake gcloud: an older session and six turns of the newest, as the chat service logs them
FAKE_ROWS = []
for k, (sess, n) in enumerate([("aaaaaaaaaaaa", 1), ("aaaaaaaaaaaa", 2)] + [("3f9c2a1d0b7e", i) for i in range(1, 7)]):
    FAKE_ROWS.append({"jsonPayload": {"event": "chat", "brain": "langchain", "session_id": sess, "model_calls": 2,
                                      "tokens_in": 2000 * n + 900, "cached_tokens": 0 if n == 1 else 1024 * (n - 1),
                                      "tokens_out": 300 + n, "cost_usd": 0.002 * n, "rag_cost_usd": 0.004}})
FAKE_GCLOUD = ("import json, sys, types\n"
               "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
               f"ROWS = json.loads({json.dumps(json.dumps(FAKE_ROWS[::-1]))})\n"
               "def run(cmd, **kw):\n"
               "    assert cmd[:3] == ['gcloud', 'logging', 'read'] and 'jsonPayload.user=\"you@your-company.com\"' in cmd[3], cmd\n"
               "    return R(json.dumps(ROWS))\n"
               "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
fake_rows = run_cell(ROWS_PY, FAKE_GCLOUD)
assert fake_rows.startswith("session 3f9c2a1d0b7e: 6 turns, brain langchain") and fake_rows.count("\n") == 9, fake_rows
assert (T / "lesson69-session.txt").read_text(encoding="utf-8") == "3f9c2a1d0b7e"
shutil.rmtree(T, ignore_errors=True)

# ---- the author's recordings
REC = {name: pb.recorded(LESSON, f"{name}.txt") for name in ("ui_turns", "full_vs_window", "thread")}
LIVE_REC = REC["full_vs_window"]
saved = re.search(r"the window sent (\d+)% (fewer|more) input tokens and cost (\d+)% (fewer|more) rupees than the whole thread", LIVE_REC)
same = re.search(r"the two answers cited the same sources on (\d+) of (\d+) turns", LIVE_REC)
if saved and same:
    LIVE_SAID = (f"In the author's run the window sent {saved.group(1)} per cent {saved.group(2)} input tokens than the whole "
                 f"thread and cost {saved.group(3)} per cent {saved.group(4)} rupees, and the two conversations cited the same "
                 f"sources on {same.group(1)} of {same.group(2)} turns.")
else:
    assert LIVE_REC.startswith("[awaiting the author's run"), "data/full_vs_window.txt has no totals lines: re-record it"
    LIVE_SAID = "The recording's totals say how much input and how many rupees the window saved in that run."


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "venv": "run in the operator shell, in the kit (lesson 5.4's ~/graph-venv with the chat image's pins, made if it is missing)",
    "open": "run in the operator shell, in the kit (ten turns of the kit's brain behind the window; a stand-in search, no network, Rs 0)",
    "rows": "run in the operator shell, in the kit (the six chat rows step 3's turns wrote, from Cloud Logging)",
    "win": "run in the operator shell, in the kit",
    "full": "run in the operator shell, in the kit",
    "h500": "run in the operator shell, in the kit (the Change-it)",
    "live": "run on your own machine or the operator shell, in the kit (Gemini, billed to your project)",
    "thread": "run in the operator shell, in the kit (reads only)",
}
OUT_LABELS = {
    "venv": "",
    "open": "(this cell run on the kit when this page was built; the passages are stand-ins, the brain, the script and the window are the kit's)",
    "rows": "(the author's lane, recorded; your session, tokens and rupees differ)",
    "win": "(computed when this page was built, by the kit's own window_check.py)",
    "full": "(computed when this page was built, by the kit's own window_check.py)",
    "h500": "(computed when this page was built, by the kit's own window_check.py)",
    "live": "(the author's run, recorded: gemini-3.6-flash, twenty turns; Gemini's words differ run to run)",
    "thread": "(the author's lane, recorded: the step 3 conversation)",
}
OUTS = {"venv": OUT["venv"], "open": O, "rows": REC["ui_turns"], "win": OUT_WIN, "full": OUT_FULL, "h500": OUT_500,
        "live": LIVE_REC, "thread": REC["thread"]}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUTS.items()})

# ------------------------------------------------------------------ the widget: plan() and the line, in JavaScript
P = CORE["line_parts"]
DATA = {"budgets": BUDGETS, "def": budget_default, "P": {"head": P[0], "all": P[1], "some": P[2], "tail": P[3]},
        "S": CORE["S"], "Q": CORE["Q"], "max": max(t["w"] for t in TU),
        "T": [{"f": t["f"], "s": t["s"], "w": t["w"], "h": t["h"], "it": t["it"],
               "e": {str(b): t["per"][str(b)]["earlier"] for b in BUDGETS}} for t in TU]}

UI_JS = r"""var D = __DATA__;
var root = document.getElementById('wd'); if (!root) return;
var $ = function(id){ return document.getElementById(id); };
function sum(a){ return a.reduce(function(x, y){ return x + y; }, 0); }
function plan(earlier, questions, budget, head){
  if (sum(earlier) <= budget) { return [earlier.length, 0, false]; }
  var line = head <= budget, room = budget - (line ? head : 0), kept = 0, i;
  for (i = earlier.length - 1; i >= 0; i--) { if (earlier[i] > room) { break; } room -= earlier[i]; kept++; }
  if (!line) { return [kept, 0, false]; }
  var qs = [], listed = 0;
  questions.slice(0, earlier.length - kept).forEach(function(q){ qs = qs.concat(q); });
  for (i = qs.length - 1; i >= 0; i--) { if (qs[i] > room) { break; } room -= qs[i]; listed++; }
  return [kept, listed, true];
}
function turnsTxt(a, b){ return a === b ? 'turn ' + a : 'turns ' + a + ' to ' + b; }
function lineOf(dropped, shown, asked){
  var out = D.P.head.replace('{turns}', turnsTxt(1, dropped));
  if (shown.length) {
    out += shown.length === asked ? D.P.all : D.P.some.replace('{turns}', turnsTxt(shown[0][0], shown[shown.length - 1][0]));
    shown.forEach(function(s){ out += ' (' + s[0] + ') ' + JSON.stringify(s[1]); });
  }
  return out + D.P.tail;
}
function windowOf(n, b){
  var t = D.T[n - 1], earlier = D.S.slice(0, n - 1), r = plan(earlier, t.it, b, t.h), dropped = earlier.length - r[0], qs = [], i;
  for (i = 0; i < dropped; i++) { D.Q[i].forEach(function(q){ qs.push([i + 1, q]); }); }
  var shown = r[1] ? qs.slice(qs.length - r[1]) : [];
  return {kept: r[0], listed: r[1], dropped: dropped, asked: qs.length, line: r[2] ? lineOf(dropped, shown, qs.length) : null,
          keptSum: sum(earlier.slice(dropped)), earlier: t.e[b]};
}
function fmt(x){ return String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
function pct(x, of){ return (100 * x / of).toFixed(2) + '%'; }
function seg(cls, x, of){ return x > 0 ? '<span class="' + cls + '" style="width:' + pct(x, of) + '"></span>' : ''; }
var nIn = $('wd-n'), bIn = $('wd-b');
D.budgets.forEach(function(b){ var o = document.createElement('option'); o.value = b;
  o.textContent = fmt(b) + (b === 0 ? ' (the floor alone)' : b === D.def ? ' (the kit\'s default)' : ''); bIn.appendChild(o); });
bIn.value = D.def;
var cols = $('wd-cols'), axis = $('wd-axis');
D.T.forEach(function(t, i){ var c = document.createElement('div'); c.className = 'wd-col'; cols.appendChild(c);
  var s = document.createElement('span'); s.textContent = (i + 1) % 5 === 0 || i === 0 ? String(i + 1) : ''; axis.appendChild(s); });
function render(){
  var n = +nIn.value, b = +bIn.value, t = D.T[n - 1], r = windowOf(n, b), ctx = t.f + r.earlier, ceil = t.f + b;
  var lineTok = r.earlier - r.keptSum;
  $('wd-n-v').textContent = n;
  $('wd-full').innerHTML = seg('wd-sys', t.s, t.w) + seg('wd-old', t.w - t.f, t.w) + seg('wd-new', t.f - t.s, t.w);
  $('wd-win').innerHTML = seg('wd-sys', t.s, t.w) + seg('wd-line', lineTok, t.w) + seg('wd-kept', r.keptSum, t.w) + seg('wd-new', t.f - t.s, t.w) +
    (ceil <= t.w ? '<span class="wd-ceil" style="left:calc(' + pct(ceil, t.w) + ' - 1px)"></span>' : '');
  var listing = r.listed === 0 ? 'none of the questions asked in ' + (r.dropped === 1 ? 'it' : 'them')
    : r.asked === 1 ? 'its question' : (r.listed === r.asked ? 'all ' : r.listed + ' of the ') + r.asked + ' questions asked in them';
  var rows = [['Today the call sends', fmt(t.w) + ' tokens: the system prompt and the whole thread so far'],
    ['The floor', fmt(t.f) + ' tokens: the system prompt (' + fmt(t.s) + ') and turn ' + n + ' whole (' + fmt(t.f - t.s) + ')'],
    ['Earlier turns kept whole', n === 1 ? 'none: this is the first turn' : r.kept ? r.kept + ' (' + turnsTxt(r.dropped + 1, n - 1) + '), ' + fmt(r.keptSum) + ' tokens, each search result cleared' : 'none'],
    ['Brought forward', n === 1 ? 'nothing: there is no earlier turn' : r.dropped === 0 ? 'nothing: every earlier turn fits' : r.line === null ? turnsTxt(1, r.dropped) + ', left with no line: a budget of ' + fmt(b) + ' has no room for one'
      : turnsTxt(1, r.dropped) + ', in one line of ' + fmt(lineTok) + ' tokens listing ' + listing],
    ['The call the window sends', fmt(ctx) + ' tokens, its ceiling ' + fmt(ceil) + ' (the floor plus ' + fmt(b) + '): ' + Math.round(100 * ctx / t.w) + ' per cent of today\'s call']];
  var out = $('wd-out'); out.textContent = '';
  rows.forEach(function(x){ var k = document.createElement('b'), v = document.createElement('span'); k.textContent = x[0]; v.textContent = x[1]; out.appendChild(k); out.appendChild(v); });
  $('wd-line').textContent = r.line === null ? 'No line in this call.' : r.line;
  Array.prototype.forEach.call(cols.children, function(c, i){ var u = D.T[i], v = u.f + windowOf(i + 1, b).earlier;
    c.className = 'wd-col' + (i + 1 === n ? ' on' : '');
    c.innerHTML = '<i class="f" style="height:' + pct(u.w, D.max) + '"></i><i class="w" style="height:' + pct(v, D.max) + '"></i>' +
      '<i class="c" style="bottom:' + pct(Math.min(u.f + b, D.max), D.max) + '"></i>'; });
}
nIn.addEventListener('input', render); nIn.addEventListener('change', render); bIn.addEventListener('change', render);
render();"""
UI_JS = UI_JS.replace("__DATA__", json.dumps(DATA, ensure_ascii=False, separators=(",", ":")))

# the page's plan() and line against the kit's, for every turn and budget the panel offers
FUNCS = re.search(r"(function sum\(a\).*?)\nfunction fmt\(x\)", UI_JS, re.S).group(1)
probe_js = ("var D = " + json.dumps(DATA, ensure_ascii=False) + ";\n" + FUNCS + "\nvar out = [];\n"
            "for (var n = 1; n <= 20; n++) { D.budgets.forEach(function(b){ var r = windowOf(n, b); out.push([n, b, r.kept, r.listed, r.line, r.dropped]); }); }\n"
            "console.log(JSON.stringify(out));")
node = subprocess.run(["node", "-e", probe_js], capture_output=True, text=True, encoding="utf-8", check=True)
N_CASES = 0
for n, b, kept, listed, line, dropped in json.loads(node.stdout):
    want = TU[n - 1]["per"][str(b)]
    assert (kept, listed, line, dropped) == (want["kept"], want["listed"], want["line"], want["dropped"]), (n, b, kept, listed, line, want)
    lt = want["earlier"] - sum(CORE["S"][n - 1 - kept:n - 1]) if kept else want["earlier"]
    assert lt >= 0 and (line is not None or lt == 0), (n, b, lt)
    N_CASES += 1
assert N_CASES == 20 * len(BUDGETS)

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

# ------------------------------------------------------------------ the numbers the prose states
T20 = TU[19]
STATS = {
    "BUDGET": f"{budget_default:,}", "PREV": str(prev_chars), "Q9_LEN": str(Q9_LEN), "N_CASES": str(N_CASES),
    "RETRIEVE_BUDGET": str(RETRIEVE_BUDGET),
    "W1": f"{W[0]['thread_tokens']:,}", "W20": f"{W[-1]['thread_tokens']:,}", "W20_MSGS": str(W[-1]["thread_messages"]),
    "W_LAST": f"{W_LAST:,}", "W_CEIL": f"{W_CEIL:,}", "W_SYS": f"{W_SYS:,}", "W_TURN20": f"{W_FLOOR - W_SYS:,}",
    "W_KEPT": str(W_KEPT), "W_BF": str(W_BF), "W_LISTED": str(W_LISTED), "W_LIST_FROM": str(W_BF - W_LISTED + 1),
    "W_WHOLE": f"{W_WHOLE:,}", "FIRST_LINE": str(FIRST_LINE), "LAST_ALL_KEPT": str(FIRST_LINE - 1),
    "W_KEPT_FROM": str(20 - W_KEPT), "W_TIMES": f"{W_WHOLE / W_LAST:.1f}",
    "F_FIRST": str(F_FIRST), "F_LAST": f"{F_LAST:,}", "F_CEIL": f"{F_CEIL:,}", "F_TIMES": F_TIMES, "F20": f"{F[-1]['thread_tokens']:,}",
    "DIFF6": f"{DIFF6:,}", "H_FIRST": str(H_FIRST), "H_KEPT": str(H_KEPT), "H_BF": str(H_BF),
    "H_KEPT_RANGE": " or ".join(str(x) for x in H_KEPT_RANGE),
    "OPEN_MSGS": str(OPEN_MSGS), "OPEN_CALLS": str(OPEN_CALLS), "OPEN_SENT": str(OPEN_SENT), "OPEN_BF": str(OPEN_BF),
    "OPEN_Q9_Q": str(OPEN_Q9_Q), "OPEN_Q9_CALL": str(OPEN_Q9_CALL),
    "CLEAR20": f"{CLR[19]:,}", "CLEAR_STEP": f"{CLEAR_STEP:,}",
    "SUM_FULL": f"{LIVE_FULL20:,}", "SUM_WIN": f"{LIVE_WIN20:,}",
    "LIVE_IN": f"{LIVE_FULL20 + LIVE_WIN20:,}", "LIVE_RS_IN": f"{rs_in(LIVE_FULL20 + LIVE_WIN20):.0f}",
    "LIVE6_IN": f"{sum(LIVE[6]):,}", "LIVE6_RS": f"{rs_in(sum(LIVE[6])):.1f}",
    "LIVE12_IN": f"{sum(LIVE[12]):,}", "LIVE12_RS": f"{rs_in(sum(LIVE[12])):.0f}",
    "UI6_IN": f"{UI6_IN:,}", "UI6_RS": f"{rs_in(UI6_IN):.1f}",
    "QS6": "".join(f"<li>{html.escape(q)}</li>" for q in QUESTIONS[:6]),
    "Q20": html.escape(QUESTIONS[19]), "Q19": html.escape(QUESTIONS[18]), "Q1": html.escape(QUESTIONS[0]),
    "T20_W": f"{T20['w']:,}", "LIVE_SAID": html.escape(LIVE_SAID),
    "PIN_LANGCHAIN": reqs["langchain"], "PIN_ADK": reqs["google-adk"],
}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUTS.items():
        print(f"===== {k}\n{v}")
    print(json.dumps(STATS, indent=1))
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: make window-check offline, three runs (and BRAIN=langgraph, the same rows), {CORE['warm']} searches outside the timer | "
      f"windowed {W[0]['thread_tokens']:,} -> {W[-1]['thread_tokens']:,} tokens, last call {W_LAST:,} of {W_CEIL:,} | full over from turn "
      f"{F_FIRST}, {F_TIMES}x at turn 20 | the widget's plan() and line checked in node for {N_CASES} cases | the opened-up cell on the kit")
