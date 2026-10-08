"""Lesson 6.5: One turn, taken apart

Do it: the venv Do it: one turn

Run order inside this file:
1. Do it: the venv (source window 8)
2. Do it: one turn (source window 10)

Prerequisites: setup_prepare.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


# Original CLI workflow for step_01_the_venv.
COMMANDS_01 = """[ -x ~/graph-venv/bin/python ] || python -m venv ~/graph-venv   # lesson 5.4's venv, made here if it is missing
~/graph-venv/bin/pip install -q "langchain==1.4.0" "langchain-core==1.6.2" "requests==2.34.2" "google-auth==2.57.1" \\
  "fastapi==0.141.1" "langgraph-checkpoint-sqlite==3.1.1"   # the chat image's web layer, and the laptop lane's checkpointer
~/graph-venv/bin/python -c 'import fastapi, langgraph.checkpoint.sqlite; print("graph-venv ok: fastapi", fastapi.__version__)'

"""

def step_01_the_venv(session):
    """Run Do it: the venv at this checkpoint.

    Do it: the venv

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (lesson 5.4's venv, with the web layer and the SQLite checkpointer added).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: graph-venv ok: fastapi 0.141.1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_one_turn.
COMMANDS_02 = """~/graph-venv/bin/python - <<'PY'
import json, logging, sys, threading, warnings
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
srv.shutdown()
PY

"""

def step_02_one_turn(session):
    """Run Do it: one turn at this checkpoint.

    Do it: one turn

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one turn taken apart; no model, no network beyond your machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1. turn 1, the LangChain brain, thread acme:you@example.com:lesson111
       kept  HumanMessage What is the notice period?
       kept  AIMessage    retrieve(...)
       kept  ToolMessage  {"citations": [{"chunk_id": "acme:hr_policy_2026#NP-03", "quote"
       kept  AIMessage    Sixty days [1].
       the system prompt among them: False; checkpoints written: 5
    2. turn 2, the LangGraph brain, the same thread: 6 messages, turn 1's among them
       the history still quotes: The notice period is 60 days.
       the corpus now says:      The notice period is 90 days.
    3. a new session, the same person: 0 messages
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_8', step_01_the_venv),
        ('source_10', step_02_one_turn),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
