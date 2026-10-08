"""The Google Chat bridge's duplicate claims (the Google Chat door, workshop lesson 10.4).

Chat may deliver an event more than once, Pub/Sub delivers at least once, and a person may press a button twice. A
claim is one document, gchat_events/{key}, in the bridge's own Firestore database, documind-gchat (never the default
database, where the rosters and the roles live: the bridge's roles/datastore.user is conditioned on this database,
terraform/gchat.tf). It holds {kind, state, attempts, created_at, leased_at, expire_at}: no text and no email. The key
is a hash of the message name (events.event_key, events.press_key). expire_at is 24 hours out, and a TTL policy
deletes the document after it.

    take(key, kind)     the synchronous handler, in a transaction, as services/ingest/idempotency.py claims a
                        document: True when this request may go on. A received claim older than RETAKE_S is taken
                        back (the request that wrote it died); a queued, working or answered one is a duplicate.
    queued(key)         the question is published: the next duplicate repeats the acknowledgement
    drop(key)           a synchronous refusal after the claim: the next delivery is answered the same way
    lease(key)          the worker, in a transaction: (state, attempts) after adding one attempt. "answered" means
                        acknowledge and do nothing; "busy" means another delivery holds it (a 5xx, so Pub/Sub retries)
    answered(key)       the answer is posted
    release(key)        the worker failed: back to queued, the attempts kept, so the fifth attempt is counted

A gate hit is never claimed: it is answered every time (services/gchat/main.py).

google-cloud-firestore is imported inside client() and _transactional(), so the module imports without it.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

DATABASE = "documind-gchat"
COLLECTION = "gchat_events"
TTL = timedelta(hours=24)
RETAKE_S = 60                # a received claim older than this is taken back
LEASE_S = 300                # the push subscription's ack deadline: a working claim older than this is taken back
STATES = ("received", "queued", "working", "answered")

_client = None


def client():
    global _client
    if _client is None:
        from google.cloud import firestore
        _client = firestore.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT") or None, database=DATABASE)
    return _client


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _transactional(fn):
    """firestore.transactional: fn(transaction) runs, and is run again, until the transaction commits."""
    from google.cloud import firestore
    return firestore.transactional(fn)


def _age(value, now: datetime) -> float:
    return (now - value).total_seconds() if isinstance(value, datetime) else float("inf")


def _ref(db, key: str):
    return db.collection(COLLECTION).document(key)


def take(key: str, kind: str, db=None) -> bool:
    db = db or client()
    ref, now = _ref(db, key), _now()

    @_transactional
    def _tx(tx) -> bool:
        snap = ref.get(transaction=tx)
        rec = snap.to_dict() if snap.exists else None
        if rec and not (rec.get("state") == "received" and _age(rec.get("created_at"), now) > RETAKE_S):
            return False
        tx.set(ref, {"kind": kind, "state": "received", "attempts": 0, "created_at": now, "leased_at": None,
                     "expire_at": now + TTL})
        return True

    return _tx(db.transaction())


def queued(key: str, db=None) -> None:
    _ref(db or client(), key).update({"state": "queued"})


def drop(key: str, db=None) -> None:
    _ref(db or client(), key).delete()


def lease(key: str, kind: str = "message", db=None) -> tuple[str, int]:
    db = db or client()
    ref, now = _ref(db, key), _now()

    @_transactional
    def _tx(tx) -> tuple[str, int]:
        snap = ref.get(transaction=tx)
        rec = (snap.to_dict() or {}) if snap.exists else {}
        attempts = int(rec.get("attempts") or 0)
        if rec.get("state") == "answered":
            return "answered", attempts
        if rec.get("state") == "working" and _age(rec.get("leased_at"), now) < LEASE_S:
            return "busy", attempts
        attempts += 1
        tx.set(ref, {"kind": rec.get("kind") or kind, "state": "working", "attempts": attempts,
                     "created_at": rec.get("created_at") or now, "leased_at": now,
                     "expire_at": rec.get("expire_at") or now + TTL})
        return "working", attempts

    return _tx(db.transaction())


def answered(key: str, db=None) -> None:
    _ref(db or client(), key).update({"state": "answered", "leased_at": None})


def release(key: str, db=None) -> None:
    _ref(db or client(), key).update({"state": "queued", "leased_at": None})
