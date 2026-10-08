"""Lesson 1.5: Dead letters: reading the queue, deciding, cleaning up

At lesson end: This dead letter deserves the second choice: the object was never meant to be indexed. Acknowledge the message to remove it from the queue, and delete the empty object from the bucket, because an object with no ledger row is exactly what the nightly walk of lesson 1.8 looks for, and it would rewrite the object onto itself and send the same poison round again every night. Both commands change your lane; both act only on the drill's own artefacts.

Run order inside this file:
1. Decide, then clean up (source window 36)

Prerequisites: workshop setup; see this lesson README.
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


def step_01_decide_then_clean_up(session):
    """Run Decide, then clean up at this checkpoint.

    This dead letter deserves the second choice: the object was never meant to be indexed. Acknowledge the message to remove it from the queue, and delete the empty object from the bucket, because an object with no ledger row is exactly what the nightly walk of lesson 1.8 looks for, and it would rewrite the object onto itself and send the same poison round again every night. Both commands change your lane; both act only on the drill's own artefacts.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (removes the dead letter and the empty object; nothing else).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme/poison-1758542871.pdf
    Removing gs://documind-ai-YOUR-ID-uploads/acme/poison-1758542871.pdf...
    """
    from workshop_helpers.poison import finish_drill
    finish_drill(session)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_36', step_01_decide_then_clean_up),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=True, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
