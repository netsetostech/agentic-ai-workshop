"""Lesson 6.1: The thread rides every call too

Do it: offline Do it: on your lane

Run order inside this file:
1. Do it: offline (source window 46)
2. Do it: on your lane (source window 48)

Prerequisites: demo_08_change_it_top_k_and_which_part_of_the_bill_moves.
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


# Original CLI workflow for step_01_offline.
COMMANDS_01 = """make context-sources OFFLINE=1 BRAIN=langchain TURNS=3

"""

def step_01_offline(session):
    """Run Do it: offline at this checkpoint.

    Do it: offline

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (three offline turns on one local thread: Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: context sources: one turn on brain langchain, tenant acme, turn 3 of one thread, after 2 earlier questions; each search sends the model's top_k, or tools.py's default of 5
      OFFLINE=1: a scripted model at the google-genai boundary (the brain, its adapter, tools and limits run
      as on the lane) and the Rs 0 lane's retrieve over evals/corpus: no network, no credential, nothing
      billed. Tokens are estimated: a quarter of the characters each part carries (rag-api's estimator,
      context_budget.estimate_tokens), so the residual is 0. On your lane count_tokens counts each source.
    question: After how many years of continuous service is gratuity payable?
      sent with every call: a system prompt of 42
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_on_your_lane.
COMMANDS_02 = """make context-sources PROJECT=$PROJECT BRAIN=langchain TURNS=3

"""

def step_02_on_your_lane(session):
    """Run Do it: on your lane at this checkpoint.

    Do it: on your lane

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (three real turns on one local thread, the last measured).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/lane_langchain_turns3.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_46', step_01_offline),
        ('source_48', step_02_on_your_lane),
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
