"""Lesson 1.8: Run the broader module validation separately

The smoke leaves its own fixture indexed. That does not demonstrate that $SOURCE was retired or restored. Count embedding work from the worker's actual events; a refused undo can require fresh embeddings, while a successful reactivation reuses retained vectors. Two causes, told apart by one log read. A kit older than 23 September 2026 waits for a worker line carrying jsonPayload.tenant, and the line the worker writes for the unchanged fixture bytes, ingest_duplicate, carries only the document key, so the smoke waits its five minutes for a match that cannot come. The setup block pulls the latest kit every session; on a clone, one pull is the fix, after putting back any copy of the smoke file made by hand, and the count on the second line must be at least 1 afterwards. If the read shows nothing at all, the event never reached the worker, and the push subscription's endpoint is the place to look: it must be the worker's URL. Two causes, told apart by one log read. A kit older than 23 September 2026 waits for a worker line carrying jsonPayload.tenant, and the line the worker writes for the unchanged fixture bytes, ingest_duplicate, carries only the document key, so the smoke waits its five minutes for a match that cannot come. The setup block pulls the latest kit every session; on a clone, one pull is the fix, after putting back any copy of the smoke file made by hand, and the count on the second line must be at least 1 afterwards. If the read shows nothing at all, the event never reached the worker, and the push subscription's endpoint is the place to look: it must be the worker's URL. The check wants the answer to say bay 7 and not bay 4. Lesson 1.4's note, acme/smoke_note_v1.md, which step 5 restored, carries the same clause with bay 4 and no date, so with it current the model reads two sources that disagree; rule six tells it to follow the dated one and say from when it applies, and an answer that mentions the old bay fails the check although it is right. Withdraw the note for the smoke and restore it after: both are the kit's own targets from lesson 1.7, and the restore embeds nothing.

Run order inside this file:
1. Run the broader module validation separately (source window 40)
2. Run the broader module validation separately (source window 42)

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


# Original CLI workflow for step_01_run_the_broader_module_validation_separate.
COMMANDS_01 = """gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" AND (jsonPayload.tenant="acme" OR jsonPayload.doc_key:"acme_")' \\
  --project "$PROJECT" --freshness 20m --limit 5 --format='value(timestamp,jsonPayload.event,jsonPayload.doc_key,jsonPayload.chunks,jsonPayload.tenant)'
git -C "$DEMO_ROOT" pull -q --ff-only && grep -c 'doc_key:' smoke/smoke_reindex.py
gcloud pubsub subscriptions describe documind-ingest-push --project "$PROJECT" --format='value(pushConfig.pushEndpoint)'

"""

def step_01_run_the_broader_module_validation_separate(session):
    """Run Run the broader module validation separately at this checkpoint.

    The smoke leaves its own fixture indexed. That does not demonstrate that $SOURCE was retired or restored. Count embedding work from the worker's actual events; a refused undo can require fresh embeddings, while a successful reactivation reuses retained vectors. Two causes, told apart by one log read. A kit older than 23 September 2026 waits for a worker line carrying jsonPayload.tenant, and the line the worker writes for the unchanged fixture bytes, ingest_duplicate, carries only the document key, so the smoke waits its five minutes for a match that cannot come. The setup block pulls the latest kit every session; on a clone, one pull is the fix, after putting back any copy of the smoke file made by hand, and the count on the second line must be at least 1 afterwards. If the read shows nothing at all, the event never reached the worker, and the push subscription's endpoint is the place to look: it must be the worker's URL.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the worker's lines for the smoke's uploads; the kit pulled; the subscription's endpoint).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 2026-09-2xT1x:xx:xx.xxxxxxZ	ingest_duplicate	acme_9c41d0e2b7f5...
    1
    https://documind-ingest-NUMBER.asia-south1.run.app
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_run_the_broader_module_validation_separate(session):
    """Run Run the broader module validation separately at this checkpoint.

    Two causes, told apart by one log read. A kit older than 23 September 2026 waits for a worker line carrying jsonPayload.tenant, and the line the worker writes for the unchanged fixture bytes, ingest_duplicate, carries only the document key, so the smoke waits its five minutes for a match that cannot come. The setup block pulls the latest kit every session; on a clone, one pull is the fix, after putting back any copy of the smoke file made by hand, and the count on the second line must be at least 1 afterwards. If the read shows nothing at all, the event never reached the worker, and the push subscription's endpoint is the place to look: it must be the worker's URL. The check wants the answer to say bay 7 and not bay 4. Lesson 1.4's note, acme/smoke_note_v1.md, which step 5 restored, carries the same clause with bay 4 and no date, so with it current the model reads two sources that disagree; rule six tells it to follow the dated one and say from when it applies, and an answer that mentions the old bay fails the check although it is right. Withdraw the note for the smoke and restore it after: both are the kit's own targets from lesson 1.7, and the restore embeds nothing.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the note withdrawn, the smoke, the note restored).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"event": "reconcile_withdrawn", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/smoke_note_v1.md", ...}
      ...
      6 pass · 0 fail
    {"event": "reconcile_restored", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/smoke_note_v1.md", "generation": "...", ...}
    """
    session.shell("make retire PROJECT=$PROJECT SOURCE=acme/smoke_note_v1.md")
    try:
        session.shell("make smoke-reindex PROJECT=$PROJECT")
    finally:
        session.shell("make restore PROJECT=$PROJECT SOURCE=acme/smoke_note_v1.md")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_40', step_01_run_the_broader_module_validation_separate),
        ('source_42', step_02_run_the_broader_module_validation_separate),
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
