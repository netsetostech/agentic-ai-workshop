"""Lesson 10.5: Verify it yourself

evals/tests/test_route_arms.py recomputes every figure of the arms set, holds the rows to the route set's rules, runs the three arms end to end against a stand-in chat service (save, report, compare, combine) and checks the make targets; evals/tests/test_combine.py checks the vote, the selftest and what combine.py refuses. Standard library only, no lane, Rs 0.

Run order inside this file:
1. Do it: lesson 10.5's own tests (source window 57)

Prerequisites: demo_08_three_arms_on_the_same_twelve_rows_compared_and_combined.
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


# Original CLI workflow for step_01_lesson_10_5_s_own_tests.
COMMANDS_01 = """python -m unittest discover -s evals/tests -p test_route_arms.py
python -m unittest discover -s evals/tests -p test_combine.py

"""

def step_01_lesson_10_5_s_own_tests(session):
    """Run Do it: lesson 10.5's own tests at this checkpoint.

    evals/tests/test_route_arms.py recomputes every figure of the arms set, holds the rows to the route set's rules, runs the three arms end to end against a stand-in chat service (save, report, compare, combine) and checks the make targets; evals/tests/test_combine.py checks the vote, the selftest and what combine.py refuses. Standard library only, no lane, Rs 0.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — lesson 10.5's own tests, offline.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ----------------------------------------------------------------------
    Ran 21 tests in N.NNNs

    OK
    ----------------------------------------------------------------------
    Ran 12 tests in N.NNNs

    OK
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_57', step_01_lesson_10_5_s_own_tests),
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
