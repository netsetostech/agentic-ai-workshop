"""Lesson 10.8: Verify it yourself, and withdraw the note

The kit's three test files, twelve checks each one block above, then make retire and the switches off. First, the kit's own tests for the three pieces. They run offline. Two of the files hold tests that need the chat image's or the peer image's libraries and skip without them, saying so (6 of test_spotlight.py's 21, "needs the chat image's pins: pip install -r services/chat/requirements.txt"; 3 of test_pins.py's 16, "needs google-adk (the peer image's pins)"); the kit's dry-run workflow installs those pins and runs every one with DOCUMIND_REQUIRE_LIBS=1. In step 10's venv, $PY -m unittest commands/tests/test_pins.py runs all 16.

Run order inside this file:
1. Verify it yourself, and withdraw the note (source window 81)

Prerequisites: demo_10_poisoned_tools_on_your_machine_the_pins.
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


# Original CLI workflow for step_01_verify_it_yourself_and_withdraw_the_note.
COMMANDS_01 = """python -m unittest commands/tests/test_spotlight.py 2>&1 | tail -3
python -m unittest commands/tests/test_pins.py 2>&1 | tail -3
python -m unittest discover -s evals/tests -p test_attacks.py 2>&1 | tail -3

"""

def step_01_verify_it_yourself_and_withdraw_the_note(session):
    """Run Verify it yourself, and withdraw the note at this checkpoint.

    The kit's three test files, twelve checks each one block above, then make retire and the switches off. First, the kit's own tests for the three pieces. They run offline. Two of the files hold tests that need the chat image's or the peer image's libraries and skip without them, saying so (6 of test_spotlight.py's 21, "needs the chat image's pins: pip install -r services/chat/requirements.txt"; 3 of test_pins.py's 16, "needs google-adk (the peer image's pins)"); the kit's dry-run workflow installs those pins and runs every one with DOCUMIND_REQUIRE_LIBS=1. In step 10's venv, $PY -m unittest commands/tests/test_pins.py runs all 16.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the three test files: offline, Rs 0; times vary).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Ran 21 tests

    OK (skipped=6)
    Ran 16 tests

    OK (skipped=3)
    Ran 39 tests

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
        ('source_81', step_01_verify_it_yourself_and_withdraw_the_note),
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
