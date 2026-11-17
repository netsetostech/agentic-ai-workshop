"""Lesson 6.8: A turn cut off mid-flight, resumed from its checkpoint

Do it: the cut-off turn, resumed At step 0 the first turn had not yet called the model, and the file recorded everything after it, so there is something to compare. The replay re-runs the turn from there and compares what it produced with what the file recorded: each message's kind and the tools it asked for, the sources each search returned, and the answer. A recording that stops mid-turn, like this thread's second turn, is compared as far as it goes, and the rest is what the replay added.

Run order inside this file:
1. Do it: the cut-off turn, resumed (source window 17)
2. Do it: a finished turn, replayed (source window 20)

Prerequisites: demo_03_your_conversation_read_back_step_by_step.
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


# Original CLI workflow for step_01_the_cut_off_turn_resumed.
COMMANDS_01 = """make replay OFFLINE=1

"""

def step_01_the_cut_off_turn_resumed(session):
    """Run Do it: the cut-off turn, resumed at this checkpoint.

    Do it: the cut-off turn, resumed

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's cut-off thread, resumed on your machine; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: thread acme:documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com:lesson68
      from evals/threads/cut_off_turn.json: 8 checkpoints, steps -1 to 6, 2 turns
    offline: the model is a script (the thread's own model messages played back, then a rule), a search the thread
      recorded is answered as recorded and any other by the kit's Rs 0 lane over evals/corpus; no network, Rs 0

    1. the copy: 8 checkpoints in a local InMemorySaver, one update_state() each; every step's number, next and messages are the file's

    2. replay from step 6 (next tools): graph.invoke(None, the config at step 6), through the kit's LangGraph brain
       the turn's question: 'Is gratuity payable to a contract employee?'
       step
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_finished_turn_replayed.
COMMANDS_02 = """make replay OFFLINE=1 AT=0

"""

def step_02_a_finished_turn_replayed(session):
    """Run Do it: a finished turn, replayed at this checkpoint.

    At step 0 the first turn had not yet called the model, and the file recorded everything after it, so there is something to compare. The replay re-runs the turn from there and compares what it produced with what the file recorded: each message's kind and the tools it asked for, the sources each search returned, and the answer. A recording that stops mid-turn, like this thread's second turn, is compared as far as it goes, and the rest is what the replay added.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a finished turn replayed from step 0; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: thread acme:documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com:lesson68
      from evals/threads/cut_off_turn.json: 8 checkpoints, steps -1 to 6, 2 turns
    offline: the model is a script (the thread's own model messages played back, then a rule), a search the thread
      recorded is answered as recorded and any other by the kit's Rs 0 lane over evals/corpus; no network, Rs 0

    1. the copy: 8 checkpoints in a local InMemorySaver, one update_state() each; every step's number, next and messages are the file's

    2. replay from step 0 (next agent): graph.invoke(None, the config at step 0), through the kit's LangGraph brain
       the turn's question: 'After how many years of continuous service is gratui
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_the_cut_off_turn_resumed),
        ('source_20', step_02_a_finished_turn_replayed),
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
