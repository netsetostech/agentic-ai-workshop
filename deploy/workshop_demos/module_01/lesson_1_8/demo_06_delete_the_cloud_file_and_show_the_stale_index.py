"""Lesson 1.8: Delete the cloud file and show the stale index

The local original stays safe. Delete only this demonstration's live object.

Run order inside this file:
1. Delete the cloud file and show the stale index (source window 15)

Prerequisites: demo_05_prove_the_document_works.
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


# Original CLI workflow for step_01_delete_the_cloud_file_and_show_the_stale_i.
COMMANDS_01 = """sha256sum -c "$DEMO_DIR/note.sha256" &&
  gcloud storage rm "$OBJECT" &&
  ch44_source &&
  ch44_ask present

"""

def step_01_delete_the_cloud_file_and_show_the_stale_i(session):
    """Run Delete the cloud file and show the stale index at this checkpoint.

    The local original stays safe. Delete only this demonstration's live object.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — check the backup before deleting; observe before running reconciliation.
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
        ('source_15', step_01_delete_the_cloud_file_and_show_the_stale_i),
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
