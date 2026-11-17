"""Lesson 8.2: The kit's code: two lines, one rule, and the test that holds them

From the kit, with nothing changed. The grep keeps the lines that matter: each failure's name and message, the count and the verdict.

Run order inside this file:
1. Do it: the twin test on the kit as it is, Rs 0 (source window 11)

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


# Original CLI workflow for step_01_the_twin_test_on_the_kit_as_it_is_rs_0.
COMMANDS_01 = """python -m unittest commands/tests/test_twin_chunker.py 2>&1 | grep -E "^(FAIL:|AssertionError|Ran |OK|FAILED)"

"""

def step_01_the_twin_test_on_the_kit_as_it_is_rs_0(session):
    """Run Do it: the twin test on the kit as it is, Rs 0 at this checkpoint.

    From the kit, with nothing changed. The grep keeps the lines that matter: each failure's name and message, the count and the verdict.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (no credentials, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Ran 11 tests in ...s
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
        ('source_11', step_01_the_twin_test_on_the_kit_as_it_is_rs_0),
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
