"""Lesson 5.4: The refuse node, forced to fire

Do it

Run order inside this file:
1. Do it (source window 13)

Prerequisites: demo_03_the_graph_in_a_venv_of_its_own.
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


# Original CLI workflow for step_01_the_refuse_node_forced_to_fire.
COMMANDS_01 = """~/graph-venv/bin/python - <<'PY'
import sys, warnings
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
              AIMessage("Nothing was done: that request needs manual approval.")])
PY

"""

def step_01_the_refuse_node_forced_to_fire(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (three scripted turns through the kit's own graph; no network, no model).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: plain    agent -> tools -> agent          tool_calls ['retrieve']  refusals []
               answer: After five years of continuous service [1].
      blocked  agent -> refuse -> agent         tool_calls ['delete_document']  refusals ['delete_document']
               error result for delete_document: {"error": "delete_document requires manual approval"}
               answer: I could not delete the invoice: deleting a document requires manual approval, so
      mixed    agent -> refuse -> agent         tool_calls ['retrieve', 'delete_document']  refusals ['retrieve', 'delete_document']
               error result for retrieve: {"error": "retrieve requires manual approval"}
               error result for delete_docum
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_the_refuse_node_forced_to_fire),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
