"""Lesson 1.4: Repair, expire, and what the records cost

Firestore holds everything the index holds and more: the text, the vector, the stamps and the flags. So when the index and the rows disagree, the index is rebuilt from the rows, and nothing in the rows is ever derived from the index. backfill() reads every current row (of one tenant, or all), rebuilds each datapoint with the row's own vector, re-embeds only a row whose stamp fails the check from lesson 1.3, and checkpoints the repaired vector back on the row with optimistic concurrency so that a concurrent writer is never overwritten. Its plan is the count you saw in 1.3; APPLY=1 is the repair, and the two states it exists for are a worker deployed before the index existed and an apply that lost its index and succeeded on the second run.

Run order inside this file:
1. The rows rebuild the tier (source window 43)

Prerequisites: demo_07_verify_the_two_rungs_that_read_the_records.
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


# Original CLI workflow for step_01_the_rows_rebuild_the_tier.
COMMANDS_01 = """make backfill-vectors PROJECT=$PROJECT TENANT_ONLY=acme
# make backfill-vectors PROJECT=$PROJECT TENANT_ONLY=acme APPLY=1

"""

def step_01_the_rows_rebuild_the_tier(session):
    """Run The rows rebuild the tier at this checkpoint.

    Firestore holds everything the index holds and more: the text, the vector, the stamps and the flags. So when the index and the rows disagree, the index is rebuilt from the rows, and nothing in the rows is ever derived from the index. backfill() reads every current row (of one tenant, or all), rebuilds each datapoint with the row's own vector, re-embeds only a row whose stamp fails the check from lesson 1.3, and checkpoints the repaired vector back on the row with optimistic concurrency so that a concurrent writer is never overwritten. Its plan is the count you saw in 1.3; APPLY=1 is the repair, and the two states it exists for are a worker deployed before the index existed and an apply that lost its index and succeeded on the second run.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the plan (read-only) and the repair (writes to the tier; run it only when the plan is not zero).
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
        ('source_43', step_01_the_rows_rebuild_the_tier),
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
