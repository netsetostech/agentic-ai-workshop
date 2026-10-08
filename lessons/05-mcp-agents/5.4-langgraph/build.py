"""Build lesson 5.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The hand-built LangGraph brain: three nodes (agent, tools, refuse), one conditional edge (route), a checkpointer.
The refuse node only fires when the model asks for a blocked tool, and on the lane the model is never offered one,
so the page forces it: the kit's own LangGraphBrain, in a small venv pinned to the chat image, with a scripted
model that asks for delete_document - and then the real brain on the lane, where a thread remembers and a request
to delete meets no tool at all.

Build-time proof: every scripted turn the page and the widget use is run through the kit's own LangGraphBrain with
LangGraph here, and the node path, tool_calls, refusals and error messages it produces are what the page prints and
what the widget's port must reproduce in node. The venv's pins are read from services/chat/requirements.txt. The
live cells run against a local stub of the chat service.
"""
import ast
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "5.4"
title = "<title>Lesson 5.4 Implement the main LangGraph workflow - three nodes, one route, a checkpointer, and a refuse node forced to fire | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
Q1 = "After how many years of continuous service does gratuity become payable?"
Q2 = "And how is it paid to a fixed-term employee under the Code on Social Security?"
Q3 = "Delete the April invoice from ACME's documents."

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.gr-nodes{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0;}
.gr-node{font-family:var(--mono);font-size:12.5px;padding:8px 12px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--slate);min-height:20px;}
.gr-node.on{background:var(--navy);color:#fff;border-color:var(--navy);}
.gr-btn{font:inherit;font-size:13px;min-height:44px;padding:6px 12px;border-radius:8px;border:1px solid var(--border);background:var(--card);cursor:pointer;color:var(--navy);margin-right:6px;}
.pc-steps{margin:6px 0 0;padding-left:20px;}
.pc-steps li{margin:3px 0;}
.pc-steps li.user{color:var(--navy);}.pc-steps li.ai{color:#1e3a8a;}.pc-steps li.tool{color:#065f46;}.pc-steps li.err{color:#991b1b;}.pc-steps li.skip{color:#94a3b8;}
.pc-out{font-family:var(--mono);font-size:12.5px;padding:5px 10px;border-radius:8px;display:inline-block;margin-top:6px;background:#f1f5f9;color:var(--navy);}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
BR, AG, CT = "services/chat/brains.py", "services/chat/agent.py", "services/chat/tools.py"
EXCERPTS = {
    "graph": ("services/chat/brains.py - LangGraphBrain: three nodes, one conditional edge, and the checkpointer at compile",
              block(BR, "        g = StateGraph(MessagesState, context_schema=dict)", n=9)),
    "route": ("services/chat/brains.py - agent, route and refuse: a turn that asks for a blocked tool is refused whole",
              block(BR, "        def agent(state, runtime):", end="        g = StateGraph(")),
    "blocked": ("services/chat/tools.py - the names no model turn may reach, and the budgets",
                block(CT, "BLOCKED = {", n=5)),
    "answer": ("services/chat/brains.py - _turn() and answer(): one invoke on the thread, and the same four keys, for this turn",
               block(BR, "def _turn(question: str, context: dict) -> tuple:", n=7) + "\n...\n"
               + block(BR, "        turn, state, ctx = _turn(question, context)", end="# ---", nth=2)),
    "thread": ("services/chat/agent.py - thread_config(): the thread id is the tenancy boundary",
               block(AG, "def thread_config(tenant_id: str, user_id: str, session_id: str) -> dict:", end="def brain_for(")),
    "saver": ("services/chat/agent.py - build_checkpointer(): Postgres on Cloud SQL, opened once for the process",
              block(AG, "    from langgraph.checkpoint.postgres import PostgresSaver", n=10)),
}
assert EXCERPTS["graph"][1].rstrip().endswith("self.graph = g.compile(checkpointer=checkpointer)")
assert "return \"refuse\" if any(c[\"name\"] in BLOCKED for c in calls) else \"tools\"" in EXCERPTS["route"][1]
assert 'BLOCKED = {"delete_document", "send_email", "modify_access"}' in EXCERPTS["blocked"][1]
assert "return _summary(out[\"messages\"], turn, ctx[\"cited\"])" in EXCERPTS["answer"][1] and "out = self.graph.invoke(state" in EXCERPTS["answer"][1]
assert EXCERPTS["thread"][1].rstrip().endswith('return {"configurable": {"thread_id": f"{tenant_id}:{user_id}:{session_id}"}}')
assert EXCERPTS["saver"][1].rstrip().endswith("return PostgresSaver(pool)      # setup() deliberately absent - see migrate.py")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
br_src, ct_src, ag_src = ((KIT / p).read_text(encoding="utf-8") for p in (BR, CT, AG))
reqs = dict(re.findall(r"^([a-z-]+)==([\d.]+)$", (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8"), re.M))
PINS = {k: reqs[k] for k in ("langchain", "langchain-core", "requests", "google-auth")}
assert "Verified offline by commands/tests/test_chat_brains.py" in br_src and (KIT / "commands/tests/test_chat_brains.py").exists()   # the cited proof
assert 'raise ValueError(f"turn {turn} is not in the thread;' in br_src                                     # a turn without its question is an error
lg = re.search(r"class LangGraphBrain:.*?\nclass ", br_src, re.S).group(0)
assert "ToolNode(TOOLS, wrap_tool_call=limits.timed_tool_call)" in lg and "limits.call_settings(meter)" in lg  # each tool call and model call is timed
assert "import TIMEOUTS" not in br_src and "_timeouts().get(name" in (KIT / "services/chat/limits.py").read_text(encoding="utf-8")  # the budgets are read in limits.py
assert "model = (llm or build_llm()).bind_tools(TOOLS)" in lg and "ToolNode(TOOLS," in lg                  # no blocked name is ever bound
assert 'SYSTEM = (\n    "You are DocuMind AI' in br_src and "If a tool refuses, say so plainly and explain what" in br_src
assert "`setup()` is NOT called here - `migrate.py` is a one-off job." in ag_src
assert "RAG_TIMEOUT_S=90" in (KIT / "commands/lesson-12.8.sh").read_text(encoding="utf-8")                    # retrieve's own client limit
assert not any(w in p.read_text(encoding="utf-8", errors="replace") for p in pb.kit_runtime_files("*.py") if "__pycache__" not in p.parts
               for w in ("delete_thread", "adelete_thread"))                                             # nothing deletes a thread

# ------------------------------------------------------------------ the scripted turns, through the kit's own LangGraphBrain
sys.path[:0] = [str(KIT), str(KIT / "services/chat")]
warnings.filterwarnings("ignore")
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel  # noqa: E402
from langchain_core.messages import AIMessage, ToolMessage  # noqa: E402
from langgraph.checkpoint.memory import InMemorySaver  # noqa: E402
import shared.documind_tools as dt  # noqa: E402
dt.retrieve = lambda *a, **k: {"citations": [{"chunk_id": "acme:SHA#12", "quote": "not less than five years"}], "answerable": True, "confidence": "high"}
import brains  # noqa: E402


class Scripted(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kw):
        return self


def call(name, i, **args):
    return {"name": name, "args": args, "id": f"c{i}"}


SCEN = {
    "plain": ("a policy question", [AIMessage("", tool_calls=[call("retrieve", 1, query="gratuity continuous service")]), AIMessage("After five years of continuous service [1].")]),
    "cost": ("a cost question", [AIMessage("", tool_calls=[call("retrieve", 1, query="ACME handbook page count")]),
                                 AIMessage("", tool_calls=[call("calculate_processing_cost", 2, total_pages=283, processing_type="priority")]),
                                 AIMessage("USD 33.96 at the priority tier, about Rs 2,886.60.")]),
    "blocked": ("a turn asking for a blocked tool", [AIMessage("", tool_calls=[call("delete_document", 1, doc="inv_2026_0412")]),
                                                    AIMessage("I could not delete the invoice: deleting a document requires manual approval, so nothing was removed.")]),
    "mixed": ("a turn asking for retrieve and a blocked tool together", [AIMessage("", tool_calls=[call("retrieve", 1, query="April invoice"), call("delete_document", 2, doc="inv_2026_0412")]),
                                                                          AIMessage("Nothing was done: that request needs manual approval.")]),
    "none": ("a turn that needs no tool", [AIMessage("Hello - ask me about your organisation's documents.")]),
}
RUNS = {}
for key, (label, turns) in SCEN.items():
    brain = brains.LangGraphBrain(InMemorySaver(), llm=Scripted(responses=turns))
    cfg = {"configurable": {"thread_id": f"acme:you:{key}"}}
    path = [list(u)[0] for u in brain.graph.stream({"messages": [{"role": "user", "content": "q"}]}, cfg, context={"tenant_id": "acme"}, stream_mode="updates")]
    msgs = brain.graph.get_state(cfg).values["messages"]
    RUNS[key] = {"path": path, "summary": brains._summary(msgs),
                 "errors": [[m.name, m.content] for m in msgs if isinstance(m, ToolMessage) and m.status == "error"],
                 "calls": [[c["name"] for c in (m.tool_calls or [])] for m in turns if getattr(m, "tool_calls", None)],
                 "final": turns[-1].content}
assert RUNS["blocked"]["path"] == ["agent", "refuse", "agent"] and RUNS["blocked"]["summary"]["refusals"] == ["delete_document"]
assert RUNS["mixed"]["summary"]["refusals"] == ["retrieve", "delete_document"] and RUNS["mixed"]["errors"][0] == ["retrieve", '{"error": "retrieve requires manual approval"}']
assert RUNS["cost"]["path"] == ["agent", "tools", "agent", "tools", "agent"] and RUNS["none"]["path"] == ["agent"]
G = brain.graph.get_graph()
NODES = list(G.nodes)
EDGES = sorted((e.source, e.target, bool(e.conditional)) for e in G.edges)
assert NODES == ["__start__", "agent", "tools", "refuse", "__end__"] and len(EDGES) == 6
# the checkpointer: a second invoke on the same thread carries the first turn's messages
mem = InMemorySaver()
b2 = brains.LangGraphBrain(mem, llm=Scripted(responses=[AIMessage("Five years."), AIMessage("Pro rata, as the Code says.")]))
c2 = {"configurable": {"thread_id": "acme:you:memory"}}
b2.graph.invoke({"messages": [{"role": "user", "content": Q1}]}, c2, context={"tenant_id": "acme"})
b2.graph.invoke({"messages": [{"role": "user", "content": Q2}]}, c2, context={"tenant_id": "acme"})
N_AFTER_TWO = len(b2.graph.get_state(c2).values["messages"])
assert N_AFTER_TWO == 4 and not any(getattr(m, "type", "") == "system" for m in b2.graph.get_state(c2).values["messages"])   # no system prompt stored

# ------------------------------------------------------------------ the cells
VENV = ("python -m venv ~/graph-venv && ~/graph-venv/bin/pip install -q " + " ".join(f'"{k}=={v}"' for k, v in PINS.items()) + "\n"
        "~/graph-venv/bin/python -c 'import langchain, langgraph; print(\"graph-venv ok: langchain\", langchain.__version__)'")

GRAPH_PY = """import sys, warnings
warnings.filterwarnings("ignore")                 # the framework warns about a dict context; harmless
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
import brains
class Scripted(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kw):            # the graph binds the kit's tools; a scripted model ignores them
        return self
g = brains.LangGraphBrain(InMemorySaver(), llm=Scripted(responses=[AIMessage("")])).graph.get_graph()
print("  nodes:", ", ".join(g.nodes))
for e in sorted(g.edges, key=lambda e: (e.source, e.target)):
    print(f"  {e.source:>9} -> {e.target:<9}{'  (route decides)' if e.conditional else ''}")"""

REFUSE_PY = """import sys, warnings
warnings.filterwarnings("ignore")
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
import shared.documind_tools as dt
dt.retrieve = lambda *a, **k: {"citations": [{"chunk_id": "acme:SHA#12", "quote": "not less than five years"}], "answerable": True, "confidence": "high"}
import brains
class Scripted(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kw):
        return self
def run(label, turns):
    b = brains.LangGraphBrain(InMemorySaver(), llm=Scripted(responses=turns))
    cfg = {"configurable": {"thread_id": "acme:you:" + label}}
    path = [list(u)[0] for u in b.graph.stream({"messages": [{"role": "user", "content": "..."}]}, cfg, context={"tenant_id": "acme"}, stream_mode="updates")]
    msgs = b.graph.get_state(cfg).values["messages"]
    out = brains._summary(msgs)
    print(f"  {label:8} {' -> '.join(path):32} tool_calls {out['tool_calls']}  refusals {out['refusals']}")
    for m in msgs:
        if isinstance(m, ToolMessage) and m.status == "error":
            print(f"           error result for {m.name}: {m.content}")
    print(f"           answer: {out['answer'][:80]}")
call = lambda name, i, **a: {"name": name, "args": a, "id": f"c{i}"}
run("plain", [AIMessage("", tool_calls=[call("retrieve", 1, query="gratuity continuous service")]), AIMessage("After five years of continuous service [1].")])
run("blocked", [AIMessage("", tool_calls=[call("delete_document", 1, doc="inv_2026_0412")]),
                AIMessage("I could not delete the invoice: deleting a document requires manual approval, so nothing was removed.")])
run("mixed", [AIMessage("", tool_calls=[call("retrieve", 1, query="April invoice"), call("delete_document", 2, doc="inv_2026_0412")]),
              AIMessage("Nothing was done: that request needs manual approval.")])"""

LIVE_PY = """import json, os, urllib.error, urllib.request
def text(answer):   # a chat service built before 24 September 2026 can send Gemini's content blocks instead of a string
    return answer if isinstance(answer, str) else "".join(p if isinstance(p, str) else p.get("text", "") for p in answer
                                                          if isinstance(p, str) or p.get("type") == "text")
body = json.dumps({"question": os.environ["Q"], "session_id": os.environ["S"], "brain": "langgraph"}).encode()
req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", data=body, method="POST",
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
try:
    a = json.load(urllib.request.urlopen(req, timeout=300))
    print(f"  [{a['session_id']}] tool_calls {a['tool_calls']}  refusals {a['refusals']}  {a['latency_ms']} ms")
    print(f"      {text(a['answer'])[:110]}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}  {e.read().decode(errors='replace')[:100]}")"""


def heredoc(body: str, python: str = "python") -> str:
    return f"{python} - <<'PY'\n{body}\nPY"


CELLS = {
    "venv": VENV,
    "graph": heredoc(GRAPH_PY, "~/graph-venv/bin/python"),
    "refuse": heredoc(REFUSE_PY, "~/graph-venv/bin/python"),
    "live": ('export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"\n'
             "ask102() {   # one turn to the LangGraph brain as documind-ui-sa: $1 = the session, $2 = the question\n"
             "TOKEN=\"$(tok \"$CHAT\")\" S=\"$1\" Q=\"$2\" python - <<'PY'\n" + LIVE_PY + "\nPY\n}\n"
             f'ask102 lesson102 "{Q1}"\n'
             f'ask102 lesson102 "{Q2}"          # the same thread: "it" is gratuity\n'
             f'ask102 lesson102-new "{Q2}"      # a new thread: "it" is nothing\n'
             f'ask102 lesson102 "{Q3}"'),
}

T = Path(tempfile.mkdtemp(prefix="lesson102-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "TOKEN": "TOKEN"}


def run_cell(body: str, env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout


OUT = {"graph": run_cell(GRAPH_PY, cwd=KIT), "refuse": run_cell(REFUSE_PY, cwd=KIT)}
assert OUT["graph"].count(" -> ") == 6 and OUT["graph"].count("(route decides)") == 3
assert "blocked  agent -> refuse -> agent" in OUT["refuse"] and "error result for delete_document: {\"error\": \"delete_document requires manual approval\"}" in OUT["refuse"]
assert "error result for retrieve: {\"error\": \"retrieve requires manual approval\"}" in OUT["refuse"]
OUT["venv"] = f"graph-venv ok: langchain {PINS['langchain']}\n"

A1 = "Gratuity becomes payable after not less than five years of continuous service, under the Payment of Gratuity Act, 1972 [1]."
A2 = "Under the Code on Social Security, 2020, a fixed-term employee is paid gratuity on a pro rata basis, without the five-year minimum [1]."
A2N = "Could you tell me what you would like to know about? For example, gratuity or leave for fixed-term employees under the Code on Social Security."
A3 = "I can't delete documents - I can only search and read them. Removing the April invoice needs someone with access to do it by hand."
PLAN = {("lesson102", Q1): {"tool_calls": ["retrieve"], "refusals": [], "answer": A1, "latency_ms": 7310},
        ("lesson102", Q2): {"tool_calls": ["retrieve"], "refusals": [], "answer": A2, "latency_ms": 6890},
        ("lesson102-new", Q2): {"tool_calls": [], "refusals": [], "answer": A2N, "latency_ms": 2140},
        ("lesson102", Q3): {"tool_calls": [], "refusals": [], "answer": A3, "latency_ms": 1980}}


class Chat(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        assert req["brain"] == "langgraph"
        data = json.dumps({**PLAN[(req["session_id"], req["question"])], "brain": "langgraph", "session_id": req["session_id"]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


srv = ThreadingHTTPServer(("127.0.0.1", 0), Chat)
threading.Thread(target=srv.serve_forever, daemon=True).start()
live = lambda s, q: run_cell(LIVE_PY, env={"CHAT": f"http://127.0.0.1:{srv.server_address[1]}", "S": s, "Q": q})  # noqa: E731
OUT["live"] = live("lesson102", Q1) + live("lesson102", Q2) + live("lesson102-new", Q2) + live("lesson102", Q3)
srv.shutdown()
shutil.rmtree(T, ignore_errors=True)
assert OUT["live"].count("refusals []") == 4


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "venv": "run in the operator shell, in the kit (a small venv with the chat image's LangChain pins; a minute or two)",
    "graph": "run in the operator shell, in the kit (the kit's graph, built and listed; no network, no model)",
    "refuse": "run in the operator shell, in the kit (three scripted turns through the kit's own graph; no network, no model)",
    "live": "run in the operator shell, in the kit (four turns to the LangGraph brain on your lane)",
}
OUT_LABELS = {
    "venv": "",
    "graph": "(this cell run on the kit's own brains.py)",
    "refuse": "(this cell run on the kit's own brains.py: the path, the lists and the error texts are the graph's)",
    "live": "(against a local stub of the chat service; the model decides the words and whether a turn needs a tool)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: step through the graph
SIM_JS = r"""var BLOCKED = %s;
  function route(msg){ var calls = msg.calls || []; return !calls.length ? '__end__' : calls.some(function(c){ return BLOCKED.indexOf(c) >= 0; }) ? 'refuse' : 'tools'; }
  function simulate(turns){                                   /* agent -> route -> tools | refuse | END, as LangGraphBrain wires it */
    var path = [], tool_calls = [], refusals = [], errors = [], i = 0;
    while (true) {
      var m = turns[i++]; path.push('agent'); (m.calls || []).forEach(function(c){ tool_calls.push(c); });
      var next = route(m);
      if (next === '__end__') break;
      path.push(next);
      if (next === 'refuse') (m.calls).forEach(function(c){ refusals.push(c); errors.push([c, '{"error": "' + c + ' requires manual approval"}']); });
    }
    return {path: path, tool_calls: tool_calls, refusals: refusals, errors: errors}; }""" % json.dumps(sorted(brains.BLOCKED))
WDATA = {k: {"label": SCEN[k][0], "turns": [{"calls": c} for c in RUNS[k]["calls"]] + [{"calls": [], "text": RUNS[k]["final"]}]} for k in SCEN}
test_js = ("'use strict';\n" + SIM_JS.replace("\n  ", "\n") + f"\nvar W = {json.dumps(WDATA)};\n"
           "var out = {}; Object.keys(W).forEach(function(k){ out[k] = simulate(W[k].turns); }); console.log(JSON.stringify(out));\n")
tjs = Path(tempfile.mkdtemp(prefix="lesson102-js-")) / "graph.js"
tjs.write_text(test_js, encoding="utf-8")
node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(tjs.parent, ignore_errors=True)
assert node.returncode == 0, node.stderr[-600:]
for k, js in json.loads(node.stdout).items():
    kit = RUNS[k]
    assert js["path"] == kit["path"] and js["tool_calls"] == kit["summary"]["tool_calls"] and js["refusals"] == kit["summary"]["refusals"] and js["errors"] == kit["errors"], (k, js, kit)

UI_JS = r"""var root = document.getElementById('graph'); if (!root) return;
  var W = %s, $ = function(id){ return document.getElementById(id); }, run = null, step = 0;
  function esc(s){ return String(s).replace(/[&<>]/g, function(c){ return {'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c]; }); }
  function events(k){                                          /* the turn as a list of steps: node, message */
    var t = W[k].turns, ev = [['__start__', 'user', 'the question arrives; the checkpointer loads the thread']], i = 0;
    while (true) {
      var m = t[i++];
      ev.push(['agent', 'ai', m.calls.length ? 'the model asks for ' + m.calls.join(' and ') : 'the model answers: ' + m.text]);
      var next = route(m);
      if (next === '__end__') { ev.push(['__end__', 'skip', 'route: no tool calls, so END; the thread is saved']); break; }
      if (next === 'tools') ev.push(['tools', 'tool', 'route: tools. ToolNode runs ' + m.calls.join(', ') + ' with the tenant from the runtime; the results go back to agent']);
      else ev.push(['refuse', 'err', 'route: refuse, because ' + m.calls.filter(function(c){ return BLOCKED.indexOf(c) >= 0; }).join(', ') + ' is blocked. Every call in the turn gets an error result: '
        + m.calls.map(function(c){ return c + ' requires manual approval'; }).join('; ')]);
    }
    return ev; }
  function render(){
    var k = $('gr-s').value, ev = events(k), s = simulate(W[k].turns), cur = ev[Math.min(step, ev.length - 1)][0];
    ['__start__', 'agent', 'tools', 'refuse', '__end__'].forEach(function(n){ $('gr-' + n).className = 'gr-node' + (n === cur ? ' on' : ''); });
    $('gr-log').innerHTML = ev.slice(0, step + 1).map(function(e){ return '<li class="' + e[1] + '">' + esc(e[0] + ': ' + e[2]) + '</li>'; }).join('');
    $('gr-out').textContent = step >= ev.length - 1 ? 'path ' + s.path.join(' -> ') + '   tool_calls ' + JSON.stringify(s.tool_calls) + '   refusals ' + JSON.stringify(s.refusals) : 'step ' + (step + 1) + ' of ' + ev.length;
    $('gr-next').disabled = step >= ev.length - 1;
  }
  $('gr-s').addEventListener('change', function(){ step = 0; render(); });
  $('gr-next').addEventListener('click', function(){ step++; render(); });
  $('gr-all').addEventListener('click', function(){ step = 99; render(); });
  render();""" % json.dumps(WDATA)

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(SIM_JS) + "\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"N_BLOCKED": str(len(brains.BLOCKED)), "PIN_LC": PINS["langchain"], "PIN_CORE": PINS["langchain-core"], "Q1": Q1, "Q2": Q2, "Q3": Q3}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(STATS)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {len(SCEN)} scripted turns through the kit's LangGraphBrain, each path, list and error equal in node | graph {len(NODES)} nodes, {len(EDGES)} edges"
      f" | venv pins from services/chat/requirements.txt | the live cell runs against a stand-in")
