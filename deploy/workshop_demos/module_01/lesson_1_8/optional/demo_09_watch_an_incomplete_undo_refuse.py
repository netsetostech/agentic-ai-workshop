"""Lesson 1.8: Watch an incomplete undo refuse

Run this only after the successful round trip. It deliberately removes one retired row from this chapter's fixture. The worker will not reactivate a partial version. It compares the retained row count with the claim's count and checks the age of retirement. A shortfall or a closed window emits reactivate_incomplete, leaves the incomplete undo unapplied, and sends the document through fresh ingestion. This variation deletes a retired fixture row; it is separate from the main demonstration and from unrelated tenant documents. The worker will not reactivate a partial version. It compares the retained row count with the claim's count and checks the age of retirement. A shortfall or a closed window emits reactivate_incomplete, leaves the incomplete undo unapplied, and sends the document through fresh ingestion. This variation deletes a retired fixture row; it is separate from the main demonstration and from unrelated tenant documents. Checkpoint: a reactivate_incomplete event explains the shortfall, followed by fresh ingest_ok; the restored source and answer are valid again. The reused-N/embedded-0 checkpoint belongs to the successful undo in step 8, not this fault. The strict generation filter may exclude reactivate_incomplete because that event is emitted by the lower-level undo function; use the read below to see it for this version and time window.

Run order inside this file:
1. Watch an incomplete undo refuse (source window 26)
2. Watch an incomplete undo refuse (source window 27)
3. Watch an incomplete undo refuse (source window 28)
4. Watch an incomplete undo refuse (source window 29)

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


# Original CLI workflow for step_01_watch_an_incomplete_undo_refuse.
COMMANDS_01 = """sha256sum -c "$DEMO_DIR/note.sha256" &&
  ch44_plan clean &&
  gcloud storage rm "$OBJECT" &&
  ch44_plan retire &&
  make reconcile PROJECT="$PROJECT" TENANT_ONLY=acme APPLY=1

"""

def step_01_watch_an_incomplete_undo_refuse(session):
    """Run Watch an incomplete undo refuse at this checkpoint.

    Run this only after the successful round trip. It deliberately removes one retired row from this chapter's fixture. The worker will not reactivate a partial version. It compares the retained row count with the claim's count and checks the age of retirement. A shortfall or a closed window emits reactivate_incomplete, leaves the incomplete undo unapplied, and sends the document through fresh ingestion. This variation deletes a retired fixture row; it is separate from the main demonstration and from unrelated tenant documents.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — retire the fixture again; require the exact one-item plan.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_watch_an_incomplete_undo_refuse(session):
    """Run Watch an incomplete undo refuse at this checkpoint.

    Run this only after the successful round trip. It deliberately removes one retired row from this chapter's fixture. The worker will not reactivate a partial version. It compares the retained row count with the claim's count and checks the age of retirement. A shortfall or a closed window emits reactivate_incomplete, leaves the incomplete undo unapplied, and sends the document through fresh ingestion. This variation deletes a retired fixture row; it is separate from the main demonstration and from unrelated tenant documents.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional deliberate fault: remove one verified retired row of this fixture.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    import json, os, warnings
    from pathlib import Path
    from google.cloud import firestore
    warnings.filterwarnings("ignore", category=UserWarning)
    db=firestore.Client(project=os.environ["PROJECT"])
    key=os.environ["DOC_KEY"]
    source=db.collection("sources").document(os.environ["SOURCE"].replace("/", "~")).get().to_dict() or {}
    claim=db.collection("documents").document(key).get().to_dict() or {}
    assert source.get("status")=="retired" and source.get("doc_key")==key
    assert claim.get("status")=="superseded", "Only the retired fixture's claim may be used."
    rows=list(db.collection("chunks").where("doc_key", "==", key).stream())
    n=int(Path(os.environ["DEMO_DIR"], "initial-chunks.txt").read_text())
    assert len(rows)==n==int(claim["chunks"]), "The complete retained version must exist first."
    assert all(r.to_dict().get("current") is False
               and r.to_dict().get("source_uri")==os.environ["OBJECT"] for r in rows)
    victim=sorted(rows, key=lambda r:r.id)[0]
    victim.reference.delete()
    print("Removed one retired fixture row:", victim.id, "| claim still expects", n)

# Original CLI workflow for step_03_watch_an_incomplete_undo_refuse.
COMMANDS_03 = """ch44_upload && ch44_logs
ch44_source
ch44_ask present
ch44_plan clean

"""

def step_03_watch_an_incomplete_undo_refuse(session):
    """Run Watch an incomplete undo refuse at this checkpoint.

    Run this only after the successful round trip. It deliberately removes one retired row from this chapter's fixture. The worker will not reactivate a partial version. It compares the retained row count with the claim's count and checks the age of retirement. A shortfall or a closed window emits reactivate_incomplete, leaves the incomplete undo unapplied, and sends the document through fresh ingestion. This variation deletes a retired fixture row; it is separate from the main demonstration and from unrelated tenant documents.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — return the same bytes, then inspect the refused undo and fresh ingestion.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_watch_an_incomplete_undo_refuse.
COMMANDS_04 = """gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND jsonPayload.doc_key=\\"$DOC_KEY\\" AND jsonPayload.event=\\"reactivate_incomplete\\" AND timestamp>=\\"$CH44_SINCE\\"" \\
  --project "$PROJECT" --limit 5 \\
  --format='table(timestamp,jsonPayload.event,jsonPayload.rows,jsonPayload.chunks,jsonPayload.reason)'

"""

def step_04_watch_an_incomplete_undo_refuse(session):
    """Run Watch an incomplete undo refuse at this checkpoint.

    The worker will not reactivate a partial version. It compares the retained row count with the claim's count and checks the age of retirement. A shortfall or a closed window emits reactivate_incomplete, leaves the incomplete undo unapplied, and sends the document through fresh ingestion. This variation deletes a retired fixture row; it is separate from the main demonstration and from unrelated tenant documents. Checkpoint: a reactivate_incomplete event explains the shortfall, followed by fresh ingest_ok; the restored source and answer are valid again. The reused-N/embedded-0 checkpoint belongs to the successful undo in step 8, not this fault. The strict generation filter may exclude reactivate_incomplete because that event is emitted by the lower-level undo function; use the read below to see it for this version and time window.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — read the undo refusal for this version; no cloud writes.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_watch_an_incomplete_undo_refuse),
        ('source_27', step_02_watch_an_incomplete_undo_refuse),
        ('source_28', step_03_watch_an_incomplete_undo_refuse),
        ('source_29', step_04_watch_an_incomplete_undo_refuse),
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
