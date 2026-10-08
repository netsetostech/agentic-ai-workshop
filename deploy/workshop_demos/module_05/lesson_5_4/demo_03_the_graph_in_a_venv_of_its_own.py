"""Lesson 5.4: The graph, in a venv of its own

Do it: the venv Do it: the graph

Run order inside this file:
1. Do it: the venv (source window 7)
2. Do it: the graph (source window 9)

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
COMMANDS_01 = """python -m venv ~/graph-venv && ~/graph-venv/bin/pip install -q "langchain==1.4.0" "langchain-core==1.6.2" "requests==2.34.2" "google-auth==2.57.1"
~/graph-venv/bin/python -c 'import langchain, langgraph; print("graph-venv ok: langchain", langchain.__version__)'

"""

def step_01_the_venv(session):
    """Run Do it: the venv at this checkpoint.

    Do it: the venv

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a small venv with the chat image's LangChain pins; a minute or two).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: graph-venv ok: langchain 1.4.0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_graph.
COMMANDS_02 = """~/graph-venv/bin/python - <<'PY'
import sys, warnings
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
    print(f"  {e.source:>9} -> {e.target:<9}{'  (route decides)' if e.conditional else ''}")
PY

"""

def step_02_the_graph(session):
    """Run Do it: the graph at this checkpoint.

    Do it: the graph

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's graph, built and listed; no network, no model).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: nodes: __start__, agent, tools, refuse, __end__
      __start__ -> agent    
          agent -> __end__    (route decides)
          agent -> refuse     (route decides)
          agent -> tools      (route decides)
         refuse -> agent    
          tools -> agent
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
        ('source_9', step_02_the_graph),
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
