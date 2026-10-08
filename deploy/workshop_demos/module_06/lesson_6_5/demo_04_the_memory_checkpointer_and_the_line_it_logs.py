"""Lesson 6.5: The memory checkpointer, and the line it logs

Do it

Run order inside this file:
1. Do it (source window 13)

Prerequisites: demo_03_one_turn_taken_apart.
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


# Original CLI workflow for step_01_the_memory_checkpointer_and_the_line_it_lo.
COMMANDS_01 = """~/graph-venv/bin/python - <<'PY'
import logging, os, sys, tempfile, warnings
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
    print(f"   after a restart: {held(saver)} messages")
PY

"""

def step_01_the_memory_checkpointer_and_the_line_it_lo(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the chat service's checkpointer with CHECKPOINT_DSN=memory, then a restart).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1. the chat service's own checkpointer, with CHECKPOINT_DSN=memory
    WARNING documind.chat.agent: CHECKPOINT_DSN=memory: conversations die with the instance (8.5). Tests only - never a deployment.
       InMemorySaver: 2 messages in acme:you@example.com:lesson111
    WARNING documind.chat.agent: CHECKPOINT_DSN=memory: conversations die with the instance (8.5). Tests only - never a deployment.
       after a restart: 0 messages
    2. the laptop lane's SqliteSaver, a file (agent.py's DOCUMIND_PROFILE=local branch)
       after a restart: 2 messages
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_the_memory_checkpointer_and_the_line_it_lo),
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
