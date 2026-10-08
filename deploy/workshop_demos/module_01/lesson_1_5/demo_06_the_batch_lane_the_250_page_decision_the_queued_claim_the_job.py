"""Lesson 1.5: The batch lane: the 250-page decision, the queued claim, the job

The queue is a Firestore query the kit prints for you. The job and its schedule exist only if BATCH_JOB was set when the lane was deployed; the box above the setup read it off the worker.

Run order inside this file:
1. Read the lane, Rs 0 (source window 27)

Prerequisites: demo_05_poison_a_message_that_can_never_succeed_and_the_retries_you_can_watch.
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


# Original CLI workflow for step_01_read_the_lane_rs_0.
COMMANDS_01 = """make queued PROJECT=$PROJECT

if [ -n "$BATCH_JOB" ]; then
  gcloud run jobs describe "$BATCH_JOB" --region "$REGION" --project "$PROJECT" --format=json | python -c "
import json, sys
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('image', 'args', 'timeoutSeconds', 'maxRetries', 'taskCount'): print(f'{k}: {v}')
            walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(json.load(sys.stdin))"
  gcloud scheduler jobs describe documind-ingest-batch-hourly --location "$REGION" --project "$PROJECT" --format='value(schedule,timeZone,state)'
else
  echo "no batch job on this lane: a queued claim waits until make batch-job declares it (BATCH_JOB=true, a Terraform plan and apply)"
fi

"""

def step_01_read_the_lane_rs_0(session):
    """Run Read the lane, Rs 0 at this checkpoint.

    The queue is a Firestore query the kit prints for you. The job and its schedule exist only if BATCH_JOB was set when the lane was deployed; the box above the setup read it off the worker.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (read-only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 0 queued document(s)
    no batch job on this lane: a queued claim waits until make batch-job declares it (BATCH_JOB=true, a Terraform plan and apply)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_read_the_lane_rs_0),
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
