"""Own the lesson 1.5 empty-object drill and match its exact dead letter.

No wildcard object deletion or arbitrary subscription acknowledgement is used.
The worker's ingest_poison log lacks an object ID: its time-window count remains
illustrative; the DLQ payload supplies the exact name, bucket and generation.
"""
import base64
import json

from .artifacts import write_json
from .session import utc_now


def create_drill(session):
    """Create the same zero-byte PDF as make poison with a saved unique identity.
    
    Example: create_drill(session) saves this run's unique zero-byte PDF identity
    """
    from google.api_core.exceptions import NotFound
    from google.cloud import storage
    bucket = storage.Client(project=session.config.project, credentials=session.credentials).bucket(session.config.uploads_bucket)
    saved = session.state.setdefault("poison_drill", {"bucket": bucket.name,
        "name": f"acme/poison-{session.directory.name}.pdf", "since": utc_now()})
    session.save()  # Record intent before uploading.
    session.set_environment(POISON_SINCE=saved["since"])
    blob = bucket.blob(saved["name"])
    try:
        blob.reload(retry=None, timeout=15)
    except NotFound:
        blob.metadata = {"workshop_session": session.directory.name}
        blob.upload_from_string(b"", content_type="application/pdf", if_generation_match=0, timeout=30)
        blob.reload(retry=None, timeout=15)
    if blob.size != 0 or (blob.metadata or {}).get("workshop_session") != session.directory.name:
        raise RuntimeError("Drill path is occupied by an object this session does not own.")
    saved["generation"] = str(blob.generation)
    session.save()
    print("Created empty PDF:", saved)
    print("Retries and DLQ forwarding are asynchronous; inspect the next checkpoints.")


def matches(payload, saved):
    """Require all object identity fields, not a similar filename or tenant alone.
    
    Example: matches(payload, saved)
    """
    return isinstance(payload, dict) and all(saved.get(key) is not None and str(payload.get(key)) == str(saved[key])
                                             for key in ("bucket", "name", "generation"))


def inspect_dead_letter(session, *, acknowledge=False):
    """Read a bounded batch, acknowledging only this run's exact object generation.
    
    Unrelated messages are left unacknowledged and immediately made available again.
    No match means pending, never success; rerun this read later if the DLQ is busy.
    
    Example: inspect_dead_letter(session, acknowledge=True)
    """
    from google.auth.transport.requests import AuthorizedSession
    saved = session.state.get("poison_drill")
    if not saved:
        if acknowledge:
            print("No drill belongs to this run; no DLQ message touched.")
            return
        raise RuntimeError("Run the poison-creation demo first.")
    if saved.get("acknowledged"):
        print("This run's dead letter was already acknowledged.")
        return
    url = f"https://pubsub.googleapis.com/v1/projects/{session.config.project}/subscriptions/ingest-dlq-sub"
    with AuthorizedSession(session.credentials) as client:
        response = client.post(url + ":pull", json={"maxMessages": 100}, timeout=30)
        response.raise_for_status()
        received = response.json().get("receivedMessages", [])
        matching, release, evidence = [], [], []
        for row in received:
            try:
                payload = json.loads(base64.b64decode(row["message"]["data"]))
            except (KeyError, ValueError):
                payload = {}
            if matches(payload, saved):
                matching.append(row["ackId"])
                evidence.append(payload)
            else:
                release.append(row["ackId"])
        if acknowledge and matching:
            result = client.post(url + ":acknowledge", json={"ackIds": matching}, timeout=30)
            result.raise_for_status()
            saved["acknowledged"] = True
            session.save()
        else:
            release += matching
        if release:
            result = client.post(url + ":modifyAckDeadline", json={"ackIds": release, "ackDeadlineSeconds": 0}, timeout=30)
            result.raise_for_status()
    write_json(session.attempt / "drill_dead_letters.json", evidence)
    if not matching:
        raise RuntimeError("This drill's exact generation was not in the pulled batch. It may still be retrying or outside this batch. No unrelated message was acknowledged; retry this read later.")
    print("Matching dead-letter payloads:", evidence, "| acknowledged:", acknowledge)


def finish_drill(session):
    """Delete only the saved empty object generation; still try exact DLQ cleanup.
    
    Example: finish_drill(session) removes only this run's owned fixture
    """
    from google.api_core.exceptions import NotFound
    from google.cloud import storage
    saved = session.state.get("poison_drill")
    if not saved:
        print("No owned drill to delete. Older untracked poison objects require manual inspection.")
        return
    blob = storage.Client(project=session.config.project, credentials=session.credentials).bucket(saved["bucket"]).blob(saved["name"])
    if not saved.get("object_deleted"):
        try:
            blob.reload(retry=None, timeout=15)
            if (blob.metadata or {}).get("workshop_session") != session.directory.name or blob.size != 0:
                raise RuntimeError("Drill object was replaced; refusing deletion.")
            generation = saved.get("generation")
            if generation is None:
                generation = str(blob.generation)  # A failed upload can precede saving its generation.
                saved["generation"] = generation
                session.save()
            blob.delete(if_generation_match=int(generation), retry=None, timeout=15)
        except NotFound:
            pass
        saved["object_deleted"] = True
        session.save()
    inspect_dead_letter(session, acknowledge=True)
