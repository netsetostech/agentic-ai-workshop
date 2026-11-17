"""Lesson 4.9: Verify it yourself: the checklist

Thirteen checks, each one block above, each with the value that proves it on your lane. First, the kit's own tests for the two tools. They run offline, on the same fixture step 5 read and on the stand-in step 7 ran.

Run order inside this file:
1. Verify it yourself: the checklist (source window 56)

Prerequisites: demo_11_the_two_reports_row_by_row.
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


# Original CLI workflow for step_01_verify_it_yourself_the_checklist.
COMMANDS_01 = """python -m unittest discover -s evals/tests -p "test_triage.py" 2>&1 | tail -3
python -m unittest discover -s evals/tests -p "test_attacks.py" 2>&1 | tail -3

"""

def step_01_verify_it_yourself_the_checklist(session):
    """Run Verify it yourself: the checklist at this checkpoint.

    Thirteen checks, each one block above, each with the value that proves it on your lane. First, the kit's own tests for the two tools. They run offline, on the same fixture step 5 read and on the stand-in step 7 ran.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's own tests for both tools; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Ran 13 tests in N.NNNs

    OK
    Ran 39 tests in N.NNNs

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
        ('source_56', step_01_verify_it_yourself_the_checklist),
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
