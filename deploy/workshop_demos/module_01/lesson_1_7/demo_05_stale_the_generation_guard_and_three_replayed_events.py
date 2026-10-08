"""Lesson 1.7: Stale: the generation guard, and three replayed events

The block reads the handbook's generation off the ledger, then publishes three records into the ingest topic exactly as Cloud Storage would, with the generation before the ledger's, the ledger's own, and one after it. The push subscription delivers them to the worker, and the worker's three lines say what it did with each. Nothing on the lane changes.

Run order inside this file:
1. Do it: three events, three verdicts, Rs 0 (source window 19)

Prerequisites: demo_04_superseded_the_retired_rows_bookkeeping_and_the_clock_that_removes_them.
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


# Original CLI workflow for step_01_three_events_three_verdicts_rs_0.
COMMANDS_01 = """GEN="$(curl -s "$API/v1/sources?tenant_id=acme" -H "Authorization: Bearer $(tok "$API")" \\
  | python -c "import json,sys; print(next(r['generation'] for r in json.load(sys.stdin)['sources'] if r['name'].endswith('hr_policy_2026.md')))")"
SIZE="$(stat -c %s evals/corpus/acme/hr_policy_2026.md)"; echo "the ledger's generation for the handbook: $GEN"
SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
for G in $((GEN - 1)) $GEN $((GEN + 1)); do
  gcloud pubsub topics publish documind-ingest --project "$PROJECT" \\
    --message "{\\"bucket\\":\\"$PROJECT-uploads\\",\\"name\\":\\"acme/hr_policy_2026.md\\",\\"generation\\":\\"$G\\",\\"size\\":\\"$SIZE\\",\\"contentType\\":\\"text/markdown\\"}" >/dev/null
done
sleep 25
gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND jsonPayload.event:\\"ingest_\\" AND timestamp>=\\"$SINCE\\"" \\
  --project "$PROJECT" --limit 5 --format='table(timestamp,jsonPayload.event,jsonPayload.generation,jsonPayload.ledger_generation,jsonPayload.reason)'

"""

def step_01_three_events_three_verdicts_rs_0(session):
    """Run Do it: three events, three verdicts, Rs 0 at this checkpoint.

    The block reads the handbook's generation off the ledger, then publishes three records into the ingest topic exactly as Cloud Storage would, with the generation before the ledger's, the ledger's own, and one after it. The push subscription delivers them to the worker, and the worker's three lines say what it did with each. Nothing on the lane changes.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (three messages; nothing is indexed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the ledger's generation for the handbook: 1758554107123456
    TIMESTAMP                 EVENT               GENERATION        LEDGER_GENERATION  REASON
    2026-09-22T15:02:31.512Z  ingest_stale_event  1758554107123457                     generation gone: the object was overwritten
    2026-09-22T15:02:30.907Z  ingest_duplicate
    2026-09-22T15:02:30.211Z  ingest_stale_event  1758554107123455  1758554107123456   older than the ledger
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_three_events_three_verdicts_rs_0),
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
