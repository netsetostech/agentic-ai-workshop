"""Lesson 1.8: The nightly job, the number it ends on, and the lane older than the ledger

Read the deployed job and backfill plan

Run order inside this file:
1. Read the deployed job and backfill plan (source window 35)

Prerequisites: demo_08_restore_the_exact_bytes_and_prove_reuse.
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


# Original CLI workflow for step_01_read_the_deployed_job_and_backfill_plan.
COMMANDS_01 = """gcloud run jobs describe documind-reconcile --region "$REGION" --project "$PROJECT" --format='value(name)' 2>/dev/null \\
  || echo "no nightly job on this lane: make reconcile-job declares and schedules it (RECONCILE_JOB=true, a Terraform plan and apply)"
gcloud scheduler jobs describe documind-reconcile-nightly --location "$REGION" --project "$PROJECT" --format='value(schedule,timeZone,state)' 2>/dev/null \\
  || echo "no schedule either: make reconcile from a shell is the walk until then"

python services/ingest/reconcile.py --project "$PROJECT" --backfill

"""

def step_01_read_the_deployed_job_and_backfill_plan(session):
    """Run Read the deployed job and backfill plan at this checkpoint.

    Read the deployed job and backfill plan

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (all read-only; the backfill is printed, not applied).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: no nightly job on this lane: make reconcile-job declares and schedules it (RECONCILE_JOB=true, a Terraform plan and apply)
    no schedule either: make reconcile from a shell is the walk until then
    {"event": "reconcile_backfill", "chunks": 0, "sources": N, "applied": false}

    documind-reconcile
    30 23 * * *	Asia/Kolkata	ENABLED
    {"event": "reconcile_backfill", "chunks": 0, "sources": N, "applied": false}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_35', step_01_read_the_deployed_job_and_backfill_plan),
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
