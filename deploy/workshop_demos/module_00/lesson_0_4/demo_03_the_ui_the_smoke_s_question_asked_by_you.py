"""Lesson 0.4: The UI: the smoke's question, asked by you

Before any command, use the lane the way a person does, and notice which identity is asking. The smoke test in step 5 asks one question. Ask it yourself first, in the browser, so that you know what a working answer looks like before a script judges one. The UI's address is built from your project number and region, the same way the setup block built API:

Run order inside this file:
1. The UI: the smoke's question, asked by you (source window 6)

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


# Original CLI workflow for step_01_the_ui_the_smoke_s_question_asked_by_you.
COMMANDS_01 = """echo "https://documind-ui-$NUMBER.$REGION.run.app"     # open it in the browser signed in to Google as yourself

"""

def step_01_the_ui_the_smoke_s_question_asked_by_you(session):
    """Run The UI: the smoke's question, asked by you at this checkpoint.

    Before any command, use the lane the way a person does, and notice which identity is asking. The smoke test in step 5 asks one question. Ask it yourself first, in the browser, so that you know what a working answer looks like before a script judges one. The UI's address is built from your project number and region, the same way the setup block built API:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (prints your UI's address).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: https://documind-ui-NUMBER.asia-south1.run.app
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_the_ui_the_smoke_s_question_asked_by_you),
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
