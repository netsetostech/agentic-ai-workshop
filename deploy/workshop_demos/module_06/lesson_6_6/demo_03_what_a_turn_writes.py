"""Lesson 6.6: What a turn writes

Do it: the venv Do it: two turns

Run order inside this file:
1. Do it: the venv (source window 7)
2. Do it: two turns (source window 9)

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
~/graph-venv/bin/pip install -q "langchain==1.4.0" "langchain-core==1.6.2" "requests==2.34.2" "google-auth==2.57.1" "google-adk==2.8.0" \\
  "cloud-sql-python-connector[pg8000]==1.22.0" "pg8000==1.31.5"   # the chat image's pins, and the Cloud SQL connector
~/graph-venv/bin/python -c 'import google.cloud.sql.connector as c, pg8000; print("graph-venv ok: connector", c.__version__)'

"""

def step_01_the_venv(session):
    """Run Do it: the venv at this checkpoint.

    Do it: the venv

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (lesson 5.4's venv, with the Cloud SQL connector added).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: graph-venv ok: connector 1.22.0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_two_turns.
COMMANDS_02 = """~/graph-venv/bin/python - <<'PY'
import logging, os, sys, warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s", stream=sys.stdout)
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
import shared.documind_tools as dt
import brains
QUOTE = ("Gratuity shall be payable to an employee on the termination of his employment after he has rendered "
         "continuous service for not less than five years, on his superannuation, or on his retirement or resignation.")
dt.retrieve = lambda query, **kw: {"answerable": True, "confidence": "high", "citations": [   # five passages, no network
    {"chunk_id": f"acme:payment_of_gratuity_act_1972#{4 + i}", "quote": QUOTE, "score": 0.9} for i in range(5)]}
class Script(FakeMessagesListChatModel):           # a model that says what it is told
    def bind_tools(self, tools, **kw): return self
saver = InMemorySaver()                            # PostgresSaver's interface: a row per checkpoint, a blob per new version
thread = {"configurable": {"thread_id": "acme:you@example.com:lesson112"}}
def turn(question, tool):                          # one turn of the kit's LangChain brain, with or without retrieve
    said = [AIMessage("", tool_calls=[{"name": "retrieve", "args": {"query": question}, "id": "c1"}])] if tool else []
    brains.LangChainBrain(saver, llm=Script(responses=said + [AIMessage("Five years of continuous service [1].")])).answer(
        question, config=thread, context={"tenant_id": "acme", "brain": "langchain"})
def kept():                                        # the thread's checkpoints, and each version of messages they stored
    cps, versions = list(saver.list(thread))[::-1], {}
    for c in cps:
        v = c.checkpoint["channel_versions"].get("messages")
        if v and v not in versions:
            msgs = c.checkpoint["channel_values"]["messages"]
            versions[v] = (len(msgs), len(saver.serde.dumps_typed(msgs)[1]))
    return cps, versions
done = (0, 0)
for question, tool in (("Remember this word for me: tamarind.", False), ("After how many years is gratuity payable?", True)):
    turn(question, tool)
    cps, versions = kept()
    print(f"a turn {'with retrieve' if tool else 'with no tool':14} +{len(cps) - done[0]} checkpoints, +{len(versions) - done[1]} versions of messages")
    done = (len(cps), len(versions))
print("the messages channel, every version kept:")
for i, (n, size) in enumerate(versions.values(), 1):
    print(f"   version {i}  {n} message{'s' if n > 1 else ' '}  {size:>6,} bytes")
sizes = [size for _, size in versions.values()]
print(f"   {sum(sizes):,} bytes kept, for a conversation whose latest version is {sizes[-1]:,} bytes")
print("the ADK brain, given the lane's DSN, with google-adk and no SQLAlchemy - as the chat image has them:")
os.environ["CHECKPOINT_DSN"] = "postgresql://chat:PASSWORD@/documind?host=/cloudsql/PROJECT:REGION:documind-checkpoint"
print(f"   it keeps its sessions in {type(brains.AdkBrain._sessions()).__name__}")
PY

"""

def step_02_two_turns(session):
    """Run Do it: two turns at this checkpoint.

    Do it: two turns

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two turns, their checkpoints and versions counted; no model, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: a turn with no tool   +3 checkpoints, +2 versions of messages
    a turn with retrieve  +5 checkpoints, +4 versions of messages
    the messages channel, every version kept:
       version 1  1 message      211 bytes
       version 2  2 messages     472 bytes
       version 3  3 messages     687 bytes
       version 4  4 messages   1,001 bytes
       version 5  5 messages   2,760 bytes
       version 6  6 messages   3,021 bytes
       8,152 bytes kept, for a conversation whose latest version is 3,021 bytes
    the ADK brain, given the lane's DSN, with google-adk and no SQLAlchemy - as the chat image has them:
    WARNING documind.chat.brains: ADK DatabaseSessionService unavailable (The 'sqlalchemy' package is required to use this feat
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_the_venv),
        ('source_9', step_02_two_turns),
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
