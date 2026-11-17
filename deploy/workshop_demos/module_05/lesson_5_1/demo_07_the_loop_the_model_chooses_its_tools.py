"""Lesson 5.1: The loop: the model chooses its tools

Do it The cell runs the kit's own LangChain brain on your machine, with a scripted model and a stand-in rag-api, so it calls nothing on your lane and costs nothing. The model asks for two searches in one message: the notice period, and the earned leave encashed on exit. The stand-in takes 1.5 seconds over the first and 1 second over the second, and both answers include LV-07, the handbook's clause on leave at exit. The cell prints when each search reached the stand-in and when it was answered, the citations each result carried, and the turn's list and citations. It runs in ~/graph-venv, lesson 5.4's venv with the chat image's pins, and the first cell makes it if it is missing.

Run order inside this file:
1. Do it (source window 22)
2. Do it: two searches at once, offline (source window 26)
3. Do it: two searches at once, offline (source window 28)

Prerequisites: demo_06_the_direct_brain_one_retrieve_no_loop.
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


# Original CLI workflow for step_01_the_loop_the_model_chooses_its_tools.
COMMANDS_01 = """chat10 langchain "After how many years of continuous service does gratuity become payable?"
chat10 langchain "The ACME handbook has 283 pages. What would processing it cost at the priority tier?"
chat10 direct "The ACME handbook has 283 pages. What would processing it cost at the priority tier?"

"""

def step_01_the_loop_the_model_chooses_its_tools(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the LangChain loop on the same question, then a cost question on both brains).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: langchain tool_calls ['retrieve']  refusals []  citations 1 n [1]  7240 ms
          After five years of continuous service, under the Payment of Gratuity Act, 1972 [1].
      langchain tool_calls ['retrieve', 'calculate_processing_cost']  refusals []  citations 1 n [1]  11350 ms
          The handbook has 283 pages [1]. At the priority tier (USD 0.12 a page) they cost USD 33.96, abou
      direct    tool_calls ['retrieve']  refusals []  citations 1  3420 ms
          The documents give no per-page price for processing the handbook; the April invoice bills priori
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_two_searches_at_once_offline.
COMMANDS_02 = """[ -x ~/graph-venv/bin/python ] || python -m venv ~/graph-venv   # lesson 5.4's venv, made here if it is missing
~/graph-venv/bin/pip install -q "langchain==1.4.0" "langchain-core==1.6.2" "langgraph==1.2.12" "requests==2.34.2" \\
  "google-auth==2.57.1" "google-genai==2.22.0" "langchain-google-genai==4.4.0"   # the chat image's pins
~/graph-venv/bin/python -c 'import langchain, langgraph; print("graph-venv ok: langchain", langchain.__version__)'

"""

def step_02_two_searches_at_once_offline(session):
    """Run Do it: two searches at once, offline at this checkpoint.

    The cell runs the kit's own LangChain brain on your machine, with a scripted model and a stand-in rag-api, so it calls nothing on your lane and costs nothing. The model asks for two searches in one message: the notice period, and the earned leave encashed on exit. The stand-in takes 1.5 seconds over the first and 1 second over the second, and both answers include LV-07, the handbook's clause on leave at exit. The cell prints when each search reached the stand-in and when it was answered, the citations each result carried, and the turn's list and citations. It runs in ~/graph-venv, lesson 5.4's venv with the chat image's pins, and the first cell makes it if it is missing.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (lesson 5.4's ~/graph-venv with the chat image's pins; a minute the first time).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: graph-venv ok: langchain 1.4.0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_two_searches_at_once_offline.
COMMANDS_03 = """~/graph-venv/bin/python - <<'PY'
import json, sys, threading, time, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
import shared.documind_tools as dt
import brains
ASK = ["notice period", "earned leave encashed on exit"]             # the two searches, in the order the model asks
TAKES = {"notice period": 1.5, "earned leave encashed on exit": 1.0}  # how long the stand-in takes over each, in seconds
FINDS = {"notice period": ["NP-03", "PB-02", "LV-07"], "earned leave encashed on exit": ["LV-07", "LV-01"]}
LOG = {}
class RagApi(BaseHTTPRequestHandler):
    \"\"\"A stand-in rag-api: each search takes its time, and both answers hold LV-07, the handbook's leave on exit.\"\"\"
    def log_message(self, *a):
        \"\"\"Print nothing for each request.\"\"\"
    def do_POST(self):
        \"\"\"Answer one /v1/query after the search's time, noting when it arrived and when it was answered.\"\"\"
        q = json.loads(self.rfile.read(int(self.headers["Content-Length"])))["query"]
        came = time.monotonic()
        time.sleep(TAKES[q])
        cites = [{"chunk_id": f"acme:hr_policy_2026#{c}", "source_uri": "gs://bucket/acme/hr_policy_2026.md", "quote": c}
                 for c in FINDS[q]]
        body = json.dumps({"answer": "(rag-api's own answer)", "citations": cites, "answerable": True,
                           "confidence": "high"}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        LOG[q] = (came, time.monotonic())
srv = ThreadingHTTPServer(("127.0.0.1", 0), RagApi)
threading.Thread(target=srv.serve_forever, daemon=True).start()
dt.RAG_API_URL, dt._id_token = f"http://127.0.0.1:{srv.server_address[1]}", lambda aud: "TOKEN"   # no lane, no token
class Scripted(FakeMessagesListChatModel):
    \"\"\"A model that says what it is told: two searches in one message, then the answer.\"\"\"
    def bind_tools(self, tools, **kw):
        \"\"\"Keep the script: the brain binds the kit's two tools, which a script never reads.\"\"\"
        return self
script = [AIMessage("", tool_calls=[{"name": "retrieve", "args": {"query": q}, "id": f"call{i}"} for i, q in enumerate(ASK, 1)]),
          AIMessage("Sixty days [3]; at most 45 days of earned leave are encashed [1].")]
brain = brains.LangChainBrain(InMemorySaver(), llm=Scripted(responses=script))
cfg = {"configurable": {"thread_id": "acme:you:lesson101-two"}}
out = brain.answer("How long is my notice period, and how much earned leave is encashed when I leave?",
                   config=cfg, context={"tenant_id": "acme", "brain": "langchain"})
srv.shutdown()
t0 = min(came for came, _ in LOG.values())
print(f"  one model message asked for {len(ASK)} searches; the stand-in rag-api's log:")
for q in ASK:
    print(f"    {q!r:33} arrived at {LOG[q][0] - t0:.1f} s, answered at {LOG[q][1] - t0:.1f} s")
both = max(came for came, _ in LOG.values()) < min(done for _, done in LOG.values())
print(f"  at once: {both} (both arrived before either was answered); {max(done for _, done in LOG.values()) - t0:.1f} s for the two,"
      f" where one after the other takes {sum(TAKES.values()):.1f} s")
print("  what the model read, one result for each call:")
results = {m.tool_call_id: json.loads(m.content) for m in brain.agent.get_state(cfg).values["messages"]
           if isinstance(m, ToolMessage)}
for i, q in enumerate(ASK, 1):
    print(f"    {q!r:33} " + "  ".join(f"[{c['n']}] {c['chunk_id'].split('#')[1]}" for c in results[f"call{i}"]["citations"]))
print(f"  tool_calls {out['tool_calls']}; the turn's citations: "
      + ", ".join(f"[{c['n']}] {c['chunk_id'].split('#')[1]}" for c in out["citations"]))
print(f"  the answer: {out['answer']}")
PY

"""

def step_03_two_searches_at_once_offline(session):
    """Run Do it: two searches at once, offline at this checkpoint.

    The cell runs the kit's own LangChain brain on your machine, with a scripted model and a stand-in rag-api, so it calls nothing on your lane and costs nothing. The model asks for two searches in one message: the notice period, and the earned leave encashed on exit. The stand-in takes 1.5 seconds over the first and 1 second over the second, and both answers include LV-07, the handbook's clause on leave at exit. The cell prints when each search reached the stand-in and when it was answered, the citations each result carried, and the turn's list and citations. It runs in ~/graph-venv, lesson 5.4's venv with the chat image's pins, and the first cell makes it if it is missing.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's LangChain brain on your machine: a scripted model, a stand-in rag-api; no lane, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: one model message asked for 2 searches; the stand-in rag-api's log:
        'notice period'                   arrived at 0.0 s, answered at 1.5 s
        'earned leave encashed on exit'   arrived at 0.0 s, answered at 1.0 s
      at once: True (both arrived before either was answered); 1.5 s for the two, where one after the other takes 2.5 s
      what the model read, one result for each call:
        'notice period'                   [3] NP-03  [4] PB-02  [1] LV-07
        'earned leave encashed on exit'   [1] LV-07  [2] LV-01
      tool_calls ['retrieve', 'retrieve']; the turn's citations: [1] LV-07, [2] LV-01, [3] NP-03, [4] PB-02
      the answer: Sixty days [3]; at most 45 days of earned leave are encashed [1].
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_the_loop_the_model_chooses_its_tools),
        ('source_26', step_02_two_searches_at_once_offline),
        ('source_28', step_03_two_searches_at_once_offline),
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
