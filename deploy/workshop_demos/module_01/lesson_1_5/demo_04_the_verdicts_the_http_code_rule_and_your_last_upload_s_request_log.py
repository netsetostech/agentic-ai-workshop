"""Lesson 1.5: The verdicts: the HTTP-code rule, and your last upload's request log

Every delivery writes a request log entry (Cloud Run's, with the status the worker answered and how long it took) and, from the worker, a JSON line with the verdict. The first read below lists the last few POSTs the subscription made to the worker; the second lists the worker's own verdicts for the same window. Your note from lesson 1.4 should be there twice: once as the duplicate the unchanged bytes produced, once as the indexed version.

Run order inside this file:
1. Read the two records your 1.4 upload left (source window 16)

Prerequisites: demo_03_the_plumbing_read_the_notification_the_topic_and_the_subscription_off_your_lane.
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


# Original CLI workflow for step_01_read_the_two_records_your_1_4_upload_left.
COMMANDS_01 = """gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND logName=\\"projects/$PROJECT/logs/run.googleapis.com%2Frequests\\" AND timestamp>=\\"$(date -u -d '-3 hours' +%Y-%m-%dT%H:%M:%SZ)\\"" \\
  --project "$PROJECT" --limit 6 --format='table(timestamp,httpRequest.requestMethod,httpRequest.status,httpRequest.latency)'

gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND jsonPayload.event:\\"ingest_\\" AND timestamp>=\\"$(date -u -d '-3 hours' +%Y-%m-%dT%H:%M:%SZ)\\"" \\
  --project "$PROJECT" --limit 6 --format='table(timestamp,jsonPayload.event,jsonPayload.doc_key,jsonPayload.chunks,jsonPayload.lane)'

"""

def step_01_read_the_two_records_your_1_4_upload_left(session):
    """Run Read the two records your 1.4 upload left at this checkpoint.

    Every delivery writes a request log entry (Cloud Run's, with the status the worker answered and how long it took) and, from the worker, a JSON line with the verdict. The first read below lists the last few POSTs the subscription made to the worker; the second lists the worker's own verdicts for the same window. Your note from lesson 1.4 should be there twice: once as the duplicate the unchanged bytes produced, once as the indexed version.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (both read-only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: TIMESTAMP                 REQUEST_METHOD  STATUS  LATENCY
    2026-09-22T12:06:41.118Z  POST            200     7.412s
    2026-09-22T11:58:07.902Z  POST            200     0.611s
    TIMESTAMP                 EVENT             DOC_KEY                 CHUNKS  LANE
    2026-09-22T12:06:41.001Z  ingest_ok         acme_9c41d0e2b7f5...    3       push
    2026-09-22T11:58:07.844Z  ingest_duplicate  acme_111510fcf0a6...
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_read_the_two_records_your_1_4_upload_left),
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
