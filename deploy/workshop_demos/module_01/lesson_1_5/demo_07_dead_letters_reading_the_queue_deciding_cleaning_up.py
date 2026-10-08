"""Lesson 1.5: Dead letters: reading the queue, deciding, cleaning up

The poison message from step 5 reaches the queue about an hour after its first refusal. Run the first line then; an empty listing earlier is the retries still running, not a fault. The second read decodes the message's own record, the same JSON the worker refused, to see the size of zero with your own eyes.

Run order inside this file:
1. Read it, when it has landed (source window 34)

Prerequisites: demo_06_the_batch_lane_the_250_page_decision_the_queued_claim_the_job.
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


def step_01_when_it_has_landed(session):
    """Run Read it, when it has landed at this checkpoint.

    The poison message from step 5 reaches the queue about an hour after its first refusal. Run the first line then; an empty listing earlier is the retries still running, not a fault. The second read decodes the message's own record, the same JSON the worker refused, to see the size of zero with your own eyes.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, about an hour after step 5 (both peek; nothing is acknowledged).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: MESSAGE_ID         OBJECT_ID                    EVENT_TIME                DELIVERY_ATTEMPT
    12345678901234567  acme/poison-1758542871.pdf   2026-09-22T12:17:52.318Z  1
    {'name': 'acme/poison-1758542871.pdf', 'size': '0', 'contentType': 'application/pdf', 'generation': '1758542872123456', 'timeCreated': '2026-09-22T12:17:52.101Z'}
    """
    manual_checkpoint("Dead-letter delivery can take about an hour. Inspect the drill's dead letter only once it has landed. Stop here and rerun this demo later; the steps already completed will not run again.")
    from workshop_helpers.poison import inspect_dead_letter
    inspect_dead_letter(session)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_when_it_has_landed),
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
