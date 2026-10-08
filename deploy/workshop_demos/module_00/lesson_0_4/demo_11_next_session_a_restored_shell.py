"""Lesson 0.4: Next session: a restored shell

A new shell, one function, and proof that it found the same project and region, and an API that answers. Next weekend, the shell you saved from is gone. Open a new one and restore it:

Run order inside this file:
1. Next session: a restored shell (source window 66)

Prerequisites: demo_10_what_still_bills_when_nothing_runs.
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


# Original CLI workflow for step_01_next_session_a_restored_shell.
COMMANDS_01 = """cd ~/deploy_module_rag && source commands/session-restart.sh && rag_resume
echo "PROJECT=$PROJECT REGION=$REGION API_URL=$API_URL"

"""

def step_01_next_session_a_restored_shell(session):
    """Run Next session: a restored shell at this checkpoint.

    A new shell, one function, and proof that it found the same project and region, and an API that answers. Next weekend, the shell you saved from is gone. Open a new one and restore it:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in a new shell at the start of your next session.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_66', step_01_next_session_a_restored_shell),
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
