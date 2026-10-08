"""Build lesson 6.5 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Three kinds of memory, and where each one lives. Agent state: the messages one turn builds - the question, the model's
tool call, the tool result, the answer - checkpointed after every step. Conversation history: those checkpoints, kept
by the checkpointer under the thread id tenant:user:session, and read back on the next turn. Knowledge: the tenant's
corpus in rag-api, looked up per question and shared by every conversation - and copied into the history as a tool
result, where a later change to the corpus never reaches it. Offline, in ~/graph-venv: one turn taken apart (what the
thread keeps, how many checkpoints, the system prompt not among them), a second turn by another brain on the same
thread after the corpus changed, and a new session; then the chat service's own start-up with CHECKPOINT_DSN=memory -
the warning line - and what a restart forgets, against the laptop lane's SQLite file. Live: one conversation across
the four brains and two sessions, and the checkpointer your lane's service is configured with.

Build-time proof: both offline cells run here on the kit's agent.py and brains.py; the messages, the checkpoint count,
the quotes, the warning line and the restart counts are their own printing. The live cells run against a local
stand-in of the chat service that keeps history the way the kit does, and a fake gcloud.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "6.5"
title = "<title>Lesson 6.5 Distinguish agent state, conversation history and knowledge - what one turn keeps, where it lives, and what forgets it | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.mk{display:inline-block;font-family:var(--mono);font-size:var(--chip-size);letter-spacing:.5px;padding:2px 10px;border-radius:999px;background:var(--teal-light);color:var(--teal-dark);border:1px solid var(--teal);margin:2px 0 8px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,9em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
AG, BR, FE = "services/chat/agent.py", "services/chat/brains.py", "services/frontend/chat.py"
EXCERPTS = {
    "thread": ("services/chat/agent.py - the thread id: tenant, then person, then session, built by the server",
               block(AG, "def thread_config(tenant_id: str, user_id: str, session_id: str) -> dict:", n=9)),
    "saver": ("services/chat/agent.py - the three checkpointers, and the one that says so",
              block(AG, "def build_checkpointer(stack: ExitStack):", n=16)),
    "prompt": ("services/chat/brains.py - the LangGraph brain: the system prompt is sent with every call and never stored",
               block(BR, "        def agent(state, runtime):", n=1) + "\n...\n"
               + block(BR, "            # The system prompt is prepended per call, never stored", n=4)),
    "adk": ("services/chat/brains.py - the ADK brain keeps its conversation under the same thread id, in its own store",
            block(BR, '        session_id = config["configurable"]["thread_id"]', n=2)),
}
assert 'return {"configurable": {"thread_id": f"{tenant_id}:{user_id}:{session_id}"}}' in EXCERPTS["thread"][1]
assert 'CHECKPOINT_DSN=memory: conversations die with the instance (8.5). "' in EXCERPTS["saver"][1] and "SqliteSaver" in EXCERPTS["saver"][1]
assert "never stored" in EXCERPTS["prompt"][1] and "[SystemMessage(content=SYSTEM)] + state[\"messages\"]" in EXCERPTS["prompt"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
ag_src, br_src, fe_src = ((KIT / p).read_text(encoding="utf-8") for p in (AG, BR, FE))
saver_src = ag_src[ag_src.index("def build_checkpointer("):ag_src.index("def thread_config(")]
assert len(re.findall(r"logger\.\w+\(", saver_src)) == 1 and "logger.warning(" in saver_src          # only the memory branch says which
assert 'return PostgresSaver(pool)' in saver_src and 'os.environ.get("DOCUMIND_THREADS_DB", "./documind_threads.db")' in saver_src
assert 'raise RuntimeError("CHECKPOINT_DSN is not set.' in saver_src
code = [p for p in pb.kit_runtime_files("*.py")] + list(pb.kit_runtime_files("*.sh")) + list(pb.kit_runtime_files("*.tf")) + [KIT / "Makefile"] + list(KIT.glob("mk/*.mk"))
assert not [p for p in code if re.search(r"delete_thread|adelete_thread", p.read_text(encoding="utf-8", errors="ignore"))]     # nothing deletes a thread
assert "@app.delete" not in ag_src and "ttl" not in saver_src.lower()
lane_src = (KIT / "commands/lane.py").read_text(encoding="utf-8")
ingest_src = "".join(p.read_text(encoding="utf-8") for p in (KIT / "services/ingest").glob("*.py"))
assert "thread_id" not in lane_src + ingest_src and "CHECKPOINT_DSN" not in lane_src + ingest_src                  # a corpus change never reaches a thread
assert "st.session_state.session_id = uuid.uuid4().hex[:12]" in fe_src and 'st.radio("Brain", BRAINS' in fe_src          # one session id, any brain
assert 'if dsn.startswith("postgresql://"):' in br_src and "DatabaseSessionService" in br_src and "return InMemorySessionService()" in br_src
chat_reqs = (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8")
assert re.search(r"^google-adk==[\d.]+$", chat_reqs, re.M) and "sqlalchemy" not in chat_reqs.lower()                # so ADK falls back to memory
direct = br_src[br_src.index("class DirectBrain:"):br_src.index("_REGISTRY = ")]
assert "checkpointer" not in direct.split("def answer", 1)[1]                                                      # the direct brain keeps nothing
assert "session.state" not in br_src and ".state[" not in br_src.replace('state["messages"]', "")                    # ADK's session state is unused
mk = (KIT / "Makefile").read_text(encoding="utf-8")
assert 'CHAT_SQL_FLAGS="--add-cloudsql-instances=$(PROJECT):$(REGION):documind-checkpoint --set-secrets=CHECKPOINT_DSN=documind-checkpoint-dsn:latest"' in mk
assert "CHAT_EXTRA_ENV=; \\" in mk                                                                                  # no make target deploys memory
assert 'secret_data = "postgresql://chat:' in (KIT / "terraform/cloudsql.tf").read_text(encoding="utf-8")
WARN = re.search(r'logger\.warning\("(CHECKPOINT_DSN=memory: [^"]+)"\s*\n\s*"([^"]+)"\)', saver_src)
WARN = WARN.group(1) + WARN.group(2)
assert WARN == "CHECKPOINT_DSN=memory: conversations die with the instance (8.5). Tests only - never a deployment.", WARN
reqs = dict(re.findall(r"^([a-z-]+)==([\d.]+)$", (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8"), re.M))
reqs.update(re.findall(r"^([a-z-]+)==([\d.]+)$", (KIT / "services/chat/requirements-local.txt").read_text(encoding="utf-8"), re.M))
PINS = {k: reqs[k] for k in ("langchain", "langchain-core", "requests", "google-auth", "fastapi", "langgraph-checkpoint-sqlite")}

# ------------------------------------------------------------------ the cells
VENV = ("[ -x ~/graph-venv/bin/python ] || python -m venv ~/graph-venv   # lesson 5.4's venv, made here if it is missing\n"
        "~/graph-venv/bin/pip install -q " + " ".join(f'"{k}=={v}"' for k, v in list(PINS.items())[:4]) + " \\\n"
        "  " + " ".join(f'"{k}=={v}"' for k, v in list(PINS.items())[4:]) + "   # the chat image's web layer, and the laptop lane's checkpointer\n"
        "~/graph-venv/bin/python -c 'import fastapi, langgraph.checkpoint.sqlite; print(\"graph-venv ok: fastapi\", fastapi.__version__)'")

TURN_PY = """import json, logging, sys, threading, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
import shared.documind_tools as dt
import brains
CORPUS = {"NP-03": "The notice period is 60 days."}   # what a stand-in rag-api's corpus says today
class Api(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        body = {"answerable": True, "confidence": "high",
                "citations": [{"chunk_id": "acme:hr_policy_2026#NP-03", "quote": CORPUS["NP-03"], "score": 0.9}]}
        self.send_response(200); self.end_headers(); self.wfile.write(json.dumps(body).encode())
srv = ThreadingHTTPServer(("127.0.0.1", 0), Api)
threading.Thread(target=srv.serve_forever, daemon=True).start()
dt.RAG_API_URL, dt._id_token = f"http://127.0.0.1:{srv.server_address[1]}", lambda aud: "TOKEN"
class Script(FakeMessagesListChatModel):           # a model that says what it is told
    def bind_tools(self, tools, **kw): return self
saver = InMemorySaver()                            # one checkpointer for both brains, as in the chat service
thread = {"configurable": {"thread_id": "acme:you@example.com:lesson111"}}   # agent.thread_config's shape
ctx = {"tenant_id": "acme", "user_id": "you@example.com", "assertion": ""}
lc = brains.LangChainBrain(saver, llm=Script(responses=[
    AIMessage("", tool_calls=[{"name": "retrieve", "args": {"query": "notice period"}, "id": "c1"}]), AIMessage("Sixty days [1].")]))
lc.answer("What is the notice period?", config=thread, context={**ctx, "brain": "langchain"})
kept = lc.agent.get_state(thread).values["messages"]
print("1. turn 1, the LangChain brain, thread", thread["configurable"]["thread_id"])
for m in kept:
    what = m.tool_calls[0]["name"] + "(...)" if getattr(m, "tool_calls", None) else str(m.content)[:64]
    print(f"   kept  {type(m).__name__:12} {what}")
print(f"   the system prompt among them: {any(type(m).__name__ == 'SystemMessage' for m in kept)};"
      f" checkpoints written: {len(list(saver.list(thread)))}")
CORPUS["NP-03"] = "The notice period is 90 days."    # the corpus changes: lesson 6.3's second handbook
lg = brains.LangGraphBrain(saver, llm=Script(responses=[AIMessage("(the model answers)")]))
lg.answer("And what was the answer?", config=thread, context={**ctx, "brain": "langgraph"})
kept = lg.graph.get_state(thread).values["messages"]
print(f"2. turn 2, the LangGraph brain, the same thread: {len(kept)} messages, turn 1's among them")
print("   the history still quotes:", [json.loads(m.content)["citations"][0]["quote"] for m in kept if isinstance(m, ToolMessage)][0])
print("   the corpus now says:     ", dt.retrieve("notice period", tenant_id="acme")["citations"][0]["quote"])
other = {"configurable": {"thread_id": "acme:you@example.com:lesson111-b"}}
print(f"3. a new session, the same person: {len(lc.agent.get_state(other).values.get('messages', []))} messages")
srv.shutdown()"""

SAVER_PY = """import logging, os, sys, tempfile, warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s", stream=sys.stdout)
os.environ["CHECKPOINT_DSN"] = "memory"            # agent.py reads it at import, as the service does at start-up
sys.path[:0] = [".", "services/chat"]
from contextlib import ExitStack
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import agent, brains
class Script(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kw): return self
thread = agent.thread_config("acme", "you@example.com", "lesson111")
def talk(saver):                                   # one turn, no tool: a word to remember
    b = brains.LangChainBrain(saver, llm=Script(responses=[AIMessage("Got it: tamarind.")]))
    b.answer("Remember this word for me: tamarind.", config=thread, context={"tenant_id": "acme", "brain": "langchain"})
def held(saver):                                   # what the next turn would find in this thread
    return len(brains.LangChainBrain(saver, llm=Script(responses=[])).agent.get_state(thread).values.get("messages", []))
print("1. the chat service's own checkpointer, with CHECKPOINT_DSN=memory")
with ExitStack() as stack:
    saver = agent.build_checkpointer(stack)
    talk(saver)
    print(f"   {type(saver).__name__}: {held(saver)} messages in {thread['configurable']['thread_id']}")
with ExitStack() as stack:                         # a restart: the new instance builds its own checkpointer
    print(f"   after a restart: {held(agent.build_checkpointer(stack))} messages")
print("2. the laptop lane's SqliteSaver, a file (agent.py's DOCUMIND_PROFILE=local branch)")
path = os.path.join(tempfile.mkdtemp(), "threads.db")
with SqliteSaver.from_conn_string(path) as saver:
    talk(saver)
with SqliteSaver.from_conn_string(path) as saver:  # the process restarts, and opens the same file
    print(f"   after a restart: {held(saver)} messages")"""

CONVO_PY = """import json, os, urllib.error, urllib.request
def text(answer):   # a chat service built before 24 September 2026 can send Gemini's content blocks instead of a string
    return answer if isinstance(answer, str) else "".join(p if isinstance(p, str) else p.get("text", "") for p in answer
                                                          if isinstance(p, str) or p.get("type") == "text")
S = {"A": f"lesson111-{os.getpid()}", "B": f"lesson111-{os.getpid()}-b"}   # two fresh sessions each run
TURNS = [("langchain", "A", "Remember this word for me: tamarind. Just confirm you have it."),
         ("langgraph", "A", "Which word did I ask you to remember?"),
         ("adk", "A", "Which word did I ask you to remember?"),
         ("direct", "A", "Which word did I ask you to remember?"),
         ("langchain", "B", "Which word did I ask you to remember?"),
         ("langchain", "B", "After how many years of continuous service does gratuity become payable?")]
for brain, s, q in TURNS:
    req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", method="POST",
                                 data=json.dumps({"question": q, "session_id": S[s], "brain": brain}).encode(),
                                 headers={"Authorization": "Bearer " + os.environ["CHAT_TOKEN"], "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            b = json.loads(r.read())
        said = " ".join(text(b["answer"]).split())
        print(f"  {brain:9} session {s}  tools {str(b['tool_calls']):13} tamarind {'yes' if 'tamarind' in said.lower() else 'no '}  {said[:40]!r}")
    except urllib.error.HTTPError as e:
        print(f"  {brain:9} session {s}  HTTP {e.code}  {e.read()[:80]!r}")"""

LANE_PY = """import json, os, subprocess
def gc(*args):
    return subprocess.run(["gcloud", *args, "--project", os.environ["PROJECT"]], capture_output=True, text=True, check=True).stdout
tpl = json.loads(gc("run", "services", "describe", "documind-chat", "--region", os.environ["REGION"], "--format", "json"))["spec"]["template"]
env = {e["name"]: e for e in tpl["spec"]["containers"][0].get("env", [])}
dsn = env.get("CHECKPOINT_DSN", {})
ref = dsn.get("valueFrom", {}).get("secretKeyRef")
print("  CHECKPOINT_DSN  " + (f"from the secret {ref['name']}, version {ref['key']}" if ref else f"= {dsn.get('value')!r}"))
print("  Cloud SQL       " + tpl["metadata"].get("annotations", {}).get("run.googleapis.com/cloudsql-instances", "none"))
seen = gc("logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" '
          'AND textPayload:"CHECKPOINT_DSN=memory"', "--freshness", "30d", "--limit", "1", "--format", "value(timestamp)").strip()
print("  the memory warning in 30 days of the service's log: " + (seen or "none"))"""


def heredoc(body: str, prefix: str = "", python: str = "python") -> str:
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


CELLS = {
    "venv": VENV,
    "turn": heredoc(TURN_PY, python="~/graph-venv/bin/python"),
    "saver": heredoc(SAVER_PY, python="~/graph-venv/bin/python"),
    "convo": 'export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"\n' + heredoc(CONVO_PY, 'CHAT_TOKEN="$(tok "$CHAT")" '),
    "lane": heredoc(LANE_PY),
}

T = Path(tempfile.mkdtemp(prefix="lesson111-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ,
       "REGION": "asia-south1", "CHECKPOINT_DSN": ""}


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.stdout[-800:], r.stderr[-1500:])
    return r.stdout


def reply(h, code: int, body) -> None:
    data = json.dumps(body, separators=(",", ":")).encode()
    h.send_response(code)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(data)))
    h.end_headers()
    h.wfile.write(data)


# ---- step 3: one turn taken apart, on the kit
OUT = {"turn": run_cell(TURN_PY, cwd=KIT)}
F = OUT["turn"]
KEPT = re.findall(r"^   kept  (\w+)\s+(.*)$", F, re.M)
assert [k for k, _ in KEPT] == ["HumanMessage", "AIMessage", "ToolMessage", "AIMessage"] and KEPT[1][1] == "retrieve(...)", KEPT
N_CK = int(re.search(r"checkpoints written: (\d+)", F).group(1))
assert "the system prompt among them: False;" in F and N_CK >= 4, F
assert "2. turn 2, the LangGraph brain, the same thread: 6 messages, turn 1's among them" in F, F
assert "the history still quotes: The notice period is 60 days." in F and "the corpus now says:      The notice period is 90 days." in F, F
assert "3. a new session, the same person: 0 messages" in F, F
OUT["venv"] = f"graph-venv ok: fastapi {PINS['fastapi']}\n"

# ---- step 4: the chat service's own start-up with CHECKPOINT_DSN=memory - the proof line - then what a restart forgets
OUT["saver"] = run_cell(SAVER_PY, cwd=KIT)
S = OUT["saver"]
assert S.count(f"WARNING documind.chat.agent: {WARN}") == 2, S
assert "   InMemorySaver: 2 messages in acme:you@example.com:lesson111" in S and "   after a restart: 0 messages" in S, S
assert S.rstrip().endswith("   after a restart: 2 messages"), S

# ---- step 5: one conversation across four brains and two sessions, against a stand-in that keeps history as the kit does:
# LangChain and LangGraph share the checkpointer's thread, ADK keeps its own session, the direct brain keeps nothing
WORD, STORES = "tamarind", {}
GRAT = "Gratuity becomes payable after not less than five years of continuous service [1]."


class Chat(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        brain, q, sid = req["brain"], req["question"], req["session_id"]
        store = {"langchain": "graph", "langgraph": "graph", "adk": "adk"}.get(brain)
        mem = STORES.setdefault((store, sid), []) if store else []
        tools = []
        if "Remember this word" in q:
            answer = f"Got it: {WORD}. I'll keep it for this conversation."
        elif "gratuity" in q:
            tools, answer = ["retrieve"], GRAT
        elif brain == "direct":
            tools, answer = ["retrieve"], "The documents do not say which word you asked me to remember."
        elif any(WORD in m for m in mem):
            answer = f"You asked me to remember \"{WORD}\"."
        else:
            answer = "I don't have a word from you in this conversation."
        mem += [q, answer]
        reply(self, 200, {"answer": answer, "tool_calls": tools, "refusals": [], "brain": brain, "session_id": sid, "latency_ms": 4200})


chat = ThreadingHTTPServer(("127.0.0.1", 0), Chat)
threading.Thread(target=chat.serve_forever, daemon=True).start()
OUT["convo"] = run_cell(CONVO_PY, env={"CHAT": f"http://127.0.0.1:{chat.server_address[1]}", "CHAT_TOKEN": "TOKEN"})
chat.shutdown()
C = OUT["convo"]
assert [ln.split("tamarind ")[1][:3] for ln in C.splitlines()] == ["yes", "yes", "no ", "no ", "no ", "no "], C
assert "session B  tools ['retrieve']" in C, C

# ---- step 6: the service's configuration and 30 days of its log, from a fake gcloud
SVC = {"spec": {"template": {"metadata": {"annotations": {"run.googleapis.com/cloudsql-instances": f"{PROJ}:asia-south1:documind-checkpoint"}},
                             "spec": {"containers": [{"env": [{"name": "GOOGLE_CLOUD_PROJECT", "value": PROJ},
                                                              {"name": "CHECKPOINT_DSN", "valueFrom": {"secretKeyRef": {"name": "documind-checkpoint-dsn", "key": "latest"}}}]}]}}}}
FAKE_GCLOUD = ("import json, sys, types\n"
               "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
               f"SVC = json.loads({json.dumps(json.dumps(SVC))})\n"
               "def run(cmd, **kw): return R(json.dumps(SVC) if cmd[1] == 'run' else '')\n"
               "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
OUT["lane"] = run_cell(LANE_PY, FAKE_GCLOUD)
assert "from the secret documind-checkpoint-dsn, version latest" in OUT["lane"] and OUT["lane"].rstrip().endswith("log: none"), OUT["lane"]
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "venv": "run in the operator shell, in the kit (lesson 5.4's venv, with the web layer and the SQLite checkpointer added)",
    "turn": "run in the operator shell, in the kit (one turn taken apart; no model, no network beyond your machine)",
    "saver": "run in the operator shell, in the kit (the chat service's checkpointer with CHECKPOINT_DSN=memory, then a restart)",
    "convo": "run in the operator shell, in the kit (one conversation, four brains, two sessions)",
    "lane": "run in the operator shell, in the kit (the checkpointer your chat service is configured with)",
}
OUT_LABELS = {
    "venv": "",
    "turn": "(this cell run on the kit's own brains.py; the checkpoint count is the installed LangChain's)",
    "saver": "(this cell run on the kit's own agent.py and brains.py; the WARNING lines are agent.py's own)",
    "convo": "(against a local stand-in that keeps history as the kit does; its answers are invented, and the model's words on your lane will differ)",
    "lane": "(from a fake gcloud; your line shows your project and region)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: where each thing lives
HIST = {"kind": "conversation history", "where": "the checkpointer's thread: Cloud SQL on your lane",
        "key": "the thread id, tenant:person:session", "until": "nothing deletes it",
        "who": "the next turn of the same tenant, person and session, in LangChain or LangGraph",
        "memory": "gone when the instance stops, and never seen by another instance"}
W = {
    "question": {"label": "the question you just asked", **HIST, "kind": "agent state during the turn, then history",
                 "where": "the turn's messages; checkpointed after each step, to the thread"},
    "call": {"label": "the model's request for retrieve", **HIST, "kind": "agent state during the turn, then history",
             "where": "an AIMessage with a tool call, checkpointed to the thread"},
    "passages": {"label": "the passages retrieve() brought back", "kind": "knowledge, copied into history",
                 "where": "rag-api's index, and a copy in the thread as the tool result",
                 "key": "the tenant for the index; the thread id for the copy",
                 "until": "the index: until retired or reindexed. The copy: nothing deletes it, and no corpus change reaches it",
                 "who": "the index: every member of the tenant. The copy: this thread",
                 "memory": "the copy goes with the instance; the index is untouched"},
    "answer": {"label": "the answer", **HIST},
    "prompt": {"label": "the system prompt", "kind": "configuration, not memory",
               "where": "SYSTEM in brains.py, sent with every model call, never stored",
               "key": "none", "until": "the next deploy of the chat service", "who": "every conversation, old threads included",
               "memory": "no difference"},
    "tenant": {"label": "the tenant", "kind": "identity, not memory", "where": "the roster in Firestore; the server puts it in the thread id and the tool context",
               "key": "the person's verified email", "until": "the roster changes", "who": "the server; never a message the model can read or write",
               "memory": "no difference"},
    "docs": {"label": "the tenant's documents", "kind": "knowledge", "where": "rag-api's index: the tenant's chunks",
             "key": "the tenant", "until": "retired or reindexed", "who": "every member of the tenant, in every conversation",
             "memory": "no difference"},
    "adk": {"label": "the same session, in the ADK brain", "kind": "conversation history, in another store",
            "where": "ADK's session service, in the instance's memory: the image has no SQLAlchemy to open the database store",
            "key": "the same thread id, as ADK's session id",
            "until": "the instance stops", "who": "the ADK brain on that instance only: it cannot read the LangChain thread, nor they its session",
            "memory": "no difference: ADK's sessions are in memory already"},
    "direct": {"label": "the direct brain's last turn", "kind": "nothing kept", "where": "nowhere: the direct brain takes no checkpointer",
               "key": "none", "until": "the end of the request", "who": "nobody: the next turn starts blank",
               "memory": "no difference"},
    "checkpoint": {"label": "a checkpoint", "kind": "the unit of history", "where": f"the checkpoint tables, one per step: {N_CK} for a turn with one tool call",
                   "key": "the thread id, then the checkpoint id", "until": "nothing deletes it",
                   "who": "the checkpointer, when the next turn of the thread loads the latest", "memory": "a dict in the instance's memory"},
}
ROWS = [["kind", "It is"], ["where", "It lives in"], ["key", "Keyed by"], ["until", "Kept until"], ["who", "Who reads it"], ["memory", "With CHECKPOINT_DSN=memory"]]
assert all(set(w) == {"label"} | {r[0] for r in ROWS} for w in W.values())
UI_JS = r"""var root = document.getElementById('sm'); if (!root) return;
  var W = %s, R = %s, $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = text; return e; }
  function render(){ var w = W[$('sm-f').value], out = $('sm-out'); out.textContent = '';
    $('sm-k').textContent = w.kind;
    R.forEach(function(r){ out.appendChild(el('b', '', r[1])); out.appendChild(el('span', '', w[r[0]])); }); }
  Object.keys(W).forEach(function(k){ var o = el('option', '', W[k].label); o.value = k; $('sm-f').appendChild(o); });
  $('sm-f').value = 'passages'; $('sm-f').addEventListener('change', render); render();""" % (json.dumps(W), json.dumps(ROWS))

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"WARN": html.escape(WARN, quote=False), "N_CK": str(N_CK), "N_ITEMS": str(len(W))}

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
print(f"kit: one turn taken apart and the memory checkpointer's start-up, on the kit's agent.py and brains.py, their own printing"
      f" | {len(W)} things in the panel | live cells against stand-ins")
