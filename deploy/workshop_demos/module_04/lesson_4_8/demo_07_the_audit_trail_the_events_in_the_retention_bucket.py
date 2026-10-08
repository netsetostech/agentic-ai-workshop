"""Lesson 4.8: The audit trail: the events in the retention bucket

Do it

Run order inside this file:
1. Do it (source window 25)

Prerequisites: demo_06_four_questions_to_the_candidate_plain_two_injections_a_pan.
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


def step_01_the_audit_trail_the_events_in_the_retentio(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (today's audit objects for acme, one event, the bucket's retention, and a delete it must refuse).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: YYYY/MM/DD/acme/doc.upload-UUID1.json
      YYYY/MM/DD/acme/dlp.finding-UUID2.json
      YYYY/MM/DD/acme/doc.upload-UUID3.json
        id: "UUID"
        ts: "YYYY-MM-DDTHH:MM:SS.ssssss+00:00"
        action: "dlp.finding"
        actor: {"tenant_id": "acme", "email": "system:ingest"}
        target: {"type": "document", "id": "acme_SHA", "tenant_id": "acme"}
        meta: {"types": ["INDIA_AADHAAR_INDIVIDUAL", "INDIA_GST_INDIVIDUAL", "INDIA_PAN_INDIVIDUAL", "PERSON_NAME", "PHONE_NUMBER"], "count": 5}
    retention 157680000 s (5 years), locked False
    delete refused: 403 Forbidden
    """
    import datetime, json, os
    from google.cloud import storage
    p = os.environ["PROJECT"]
    client = storage.Client(project=p)
    bucket = client.get_bucket(f"{p}-audit")
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m/%d")
    blobs = sorted(bucket.list_blobs(prefix=f"{day}/acme/"), key=lambda b: b.time_created)
    for b in blobs[-3:]:
        print(" ", b.name)
    finding = next((b for b in reversed(blobs) if "/dlp.finding-" in b.name), None)
    for k, v in (json.loads(finding.download_as_text()).items() if finding else [("dlp.finding", "none today")]):
        print(f"    {k}: {json.dumps(v)}")
    rp = bucket.retention_period or 0
    print(f"retention {rp} s ({rp / 31536000:.0f} years), locked {bucket.retention_policy_locked}")
    if finding and rp:                                   # only against a policy: the delete must be refused
        try:
            finding.delete()
            print("DELETED: this bucket did not enforce its retention policy")
        except Exception as e:
            print("delete refused:", getattr(e, "code", ""), type(e).__name__)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_the_audit_trail_the_events_in_the_retentio),
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
