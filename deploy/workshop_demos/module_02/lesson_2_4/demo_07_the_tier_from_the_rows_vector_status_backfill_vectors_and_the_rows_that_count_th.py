"""Lesson 2.4: The tier from the rows: vector-status, backfill-vectors, and the rows that count the rung

Do it: count the tier, plan its refill, read the rows by rung, Rs 0

Run order inside this file:
1. Do it: count the tier, plan its refill, read the rows by rung, Rs 0 (source window 37)

Prerequisites: demo_06_the_probe_the_kit_s_read_only_check_of_the_combined_filters.
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


# Original CLI workflow for step_01_count_the_tier_plan_its_refill_read_the_ro.
COMMANDS_01 = """python commands/lane.py vector-status                             # the same as: make vector-status PROJECT=$PROJECT
python commands/lane.py backfill-vectors --tenant acme            # the same as: make backfill-vectors PROJECT=$PROJECT TENANT_ONLY=acme
make usage PROJECT=$PROJECT HOURS=1 | sed -n '/by retrieval backend/,/^$/p'

"""

def step_01_count_the_tier_plan_its_refill_read_the_ro(session):
    """Run Do it: count the tier, plan its refill, read the rows by rung, Rs 0 at this checkpoint.

    Do it: count the tier, plan its refill, read the rows by rung, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (read-only: the plan writes nothing without --apply).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: index: documind-chunks  datapoints: 4xxx  shards: 1  update: STREAM_UPDATE
    endpoint: documind-endpoint  deployed: documind_chunks_v1  synced: 2026-09-2xT1x:xx:xx.xxxxxxZ
    {"event": "backfill_vectors_plan", "index": "projects/NUMBER/locations/asia-south1/indexes/1234567890123456789", "tenant": "acme", "current_chunks": 1xxx, "needs_document_embedding": 0, "invalid_chunks": 0, "embedding_task_type": "RETRIEVAL_DOCUMENT", "note": "Pause uploads/undo/batch writers; keep answer caches off during repair and validation."}

    by retrieval backend (which store served the pool; 13 September 2026)
    retrieval_backend      answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ------------------------
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_37', step_01_count_the_tier_plan_its_refill_read_the_ro),
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
