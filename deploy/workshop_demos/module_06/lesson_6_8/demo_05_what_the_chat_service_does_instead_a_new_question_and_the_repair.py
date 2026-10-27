"""Lesson 6.8: What the chat service does instead: a new question, and the repair

Do it: the next question, offline The script above accepts any history. Gemini is the model your lane runs, so this cell asks it the same question on a copy of the cut-off thread, through the kit's LangGraph brain, with your lane's rag-api as documind-ui-sa: what /v1/chat would do. It prints the answer, or the error that would have been the request's 500, then the messages from the open call on, the calls left open and what the turn cost.

Run order inside this file:
1. Do it: the next question, offline (source window 24)
2. Do it: the next question, with Gemini (source window 26)

Prerequisites: demo_04_a_turn_cut_off_mid_flight_resumed_from_its_checkpoint.
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


# Original CLI workflow for step_01_the_next_question_offline.
COMMANDS_01 = """~/graph-venv/bin/python - <<'PY'
import logging, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
logging.disable(logging.WARNING)                         # the tool layer's timing lines are not this cell's output
sys.path[:0] = [".", "services/chat", "commands"]
from langgraph.checkpoint.memory import InMemorySaver
import brains, limits, thread_read as tr, thread_replay as rp
doc = rp.load(rp.FIXTURE)                                # the cut-off thread step 4 resumed
ASK = "Is gratuity payable to an apprentice?"
WHO = {"tenant_id": doc["tenant"], "user_id": doc["user"], "assertion": "", "brain": "langgraph"}
def open_calls(messages):
    \"\"\"The tool calls in a thread that no tool message answers.\"\"\"
    answered = {m.tool_call_id for m in messages if m.type == "tool"}
    return [c for m in messages for c in getattr(m, "tool_calls", None) or [] if c["id"] not in answered]
def next_turn(repair):
    \"\"\"The cut-off thread copied into a new saver, repaired or not, then one more question, as /v1/chat sends it.\"\"\"
    brain = brains.LangGraphBrain(InMemorySaver(), llm=rp.scripted([]))
    rp.copy_thread(brain.graph, doc["thread_id"], doc["checkpoints"])
    cfg = {"configurable": {"thread_id": doc["thread_id"]}}
    if repair:
        limits.repair_thread(brain.graph, cfg, as_node="agent")
    brain.answer(ASK, config=cfg, context=dict(WHO))
    snap = brain.graph.get_state(cfg)
    print(("repaired by limits.repair_thread, then " if repair else "as it was cut off, then ") + f"the question {ASK!r}:")
    for i, m in enumerate(snap.values["messages"][5:], 6):  # from the cut-off turn's call on
        print(f"  {i:>3}. {tr.describe(m, 96)}")
    left = ", ".join(f"{c['name']} {c['id']}" for c in open_calls(snap.values["messages"])) or "none"
    print(f"  now at step {snap.metadata['step']}; tool calls no tool message answers: {left}")
with rp.offline(list(doc["by_id"].values())):            # make replay OFFLINE=1's guard: a script, the Rs 0 lane, no network
    next_turn(repair=False)
    next_turn(repair=True)
PY

"""

def step_01_the_next_question_offline(session):
    """Run Do it: the next question, offline at this checkpoint.

    Do it: the next question, offline

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the next question on the cut-off thread, as it is and repaired; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: as it was cut off, then the question 'Is gratuity payable to an apprentice?':
        6. ai     asks retrieve(query='Is gratuity payable to a contract employee?')
        7. human  Is gratuity payable to an apprentice?
        8. ai     asks retrieve(query='Is gratuity payable to an apprentice?')
        9. tool   retrieve: 5 citations [1]-[5]
       10. ai     (offline, scripted) The first passage says: "the amount of gratuity so determined. (3) The em...
      now at step 11; tool calls no tool message answers: retrieve call_21c9aa740d14
    repaired by limits.repair_thread, then the question 'Is gratuity payable to an apprentice?':
        6. ai     asks retrieve(query='Is gratuity payable to a contract employee?')
    
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_next_question_with_gemini.
COMMANDS_02 = """GOOGLE_CLOUD_PROJECT="$PROJECT" RAG_API_URL="$API" DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" \\
  ~/graph-venv/bin/python - <<'PY'
import logging, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
logging.disable(logging.WARNING)
sys.path[:0] = [".", "services/chat", "commands"]
from langgraph.checkpoint.memory import InMemorySaver
import brains, limits, thread_read as tr, thread_replay as rp
doc = rp.load(rp.FIXTURE)
ASK = "Is gratuity payable to an apprentice?"
brain = brains.LangGraphBrain(InMemorySaver())           # Gemini on location global, as the lane builds the brain
rp.copy_thread(brain.graph, doc["thread_id"], doc["checkpoints"])
cfg, meter = {"configurable": {"thread_id": doc["thread_id"]}}, limits.Meter(model=brains.MODEL)
try:
    out = brain.answer(ASK, config=cfg, context={"tenant_id": doc["tenant"], "user_id": doc["user"], "assertion": "",
                                                "brain": "langgraph", "meter": meter})
    print(f"the next turn answered; tools: {', '.join(out['tool_calls']) or 'none'}")
except Exception as exc:                                 # what /v1/chat would answer with a 500
    print(f"the next turn failed: {type(exc).__name__}: {tr.short(str(exc), 240)}")
messages = brain.graph.get_state(cfg).values["messages"]
for i, m in enumerate(messages[5:], 6):                  # from the cut-off turn's call on
    print(f"  {i:>3}. {tr.describe(m, 96)}")
answered = {m.tool_call_id for m in messages if m.type == "tool"}
left = [f"{c['name']} {c['id']}" for m in messages for c in getattr(m, "tool_calls", None) or [] if c["id"] not in answered]
print(f"tool calls no tool message answers: {', '.join(left) or 'none'}")
print(f"{meter.model_calls} model call(s), Rs {meter.spent_inr():.2f} at list price with the searches")
PY

"""

def step_02_the_next_question_with_gemini(session):
    """Run Do it: the next question, with Gemini at this checkpoint.

    The script above accepts any history. Gemini is the model your lane runs, so this cell asks it the same question on a copy of the cut-off thread, through the kit's LangGraph brain, with your lane's rag-api as documind-ui-sa: what /v1/chat would do. It prints the answer, or the error that would have been the request's 500, then the messages from the open call on, the calls left open and what the turn cost.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same question with Gemini and your rag-api; one turn at most).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/next_turn.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_24', step_01_the_next_question_offline),
        ('source_26', step_02_the_next_question_with_gemini),
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
