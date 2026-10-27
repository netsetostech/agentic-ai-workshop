"""Approval records (workshop lesson 5.8): what a paused turn on the chat service waits for, who may end it, and what
became of it.

A record lives at approvals/{approval_id}, one collection for every tenant, each record carrying its tenant. The id
is the first 32 hex digits of the sha256 of the thread id and the checkpoint the pause is kept in, so the same pause
opened twice gives one record, and a route that knows only the thread finds it. Every read is a point read that checks
the record's tenant and then the reader - the person who asked, or, for a withdrawal, a holder of doc_approver
(shared/roles.py) - and answers 404 to anyone else, as the case queue does (shared/cases.py).

    open_request()  the pause as a record: the waiting calls (services/chat/approval.paused()'s items), status pending,
                    expire_at TTL_H hours out, and an approval.request event. The same pause gives the same record back.
    decidable()     what the decision route checks before services/chat/approval.decide() runs: 410 for a pending
                    record past expire_at (marked expired here, in code; no TTL policy touches a record), 409 for one
                    already decided.
    settle()        after decide() ran: the decisions, who made them, each waiting call's result, the resumed turn's
                    answer, tool calls and refusals, and the status they amount to - approved, rejected, cancelled,
                    answered or failed - with an approval.approve or approval.reject event for a withdrawal.
    executor()      the `withdraw` that services/chat/approval.withdraw_document calls on the resumed turn. It
                    withdraws nothing: it writes the approved withdrawal on the record, and the operator runs it,
                    make withdraw-run APPROVAL=<id> (services/ingest/reconcile.py --approved).
    recheck()       what --approved checks again, from the record alone, before the tombstone: approved, by a second
                    person who still holds doc_approver in the record's own tenant, for a document of that tenant.
    withdrawn()     after the tombstone: status withdrawn, who ran it, and a doc.withdraw event.
    lost()          a record whose turn no longer waits (decide() found no pause: a question sent while the switch
                    was off dropped it, or an operator moved the thread): status lost, the route's 409.
    read()          the point read with its 404; list_for() the person's own records and, for a doc_approver, the
                    tenant's pending withdrawals; view() what a route answers, with every time as ISO text.

A record's fields: approval_id, tenant, requester, session_id, thread, brain, kind (approval: a call a second person
approves waits; answer: only ask_user waits, and the person who asked alone reads it), waiting (the calls: tool, args,
call_id, allowed_decisions, description), status (pending, approved, rejected, cancelled, answered, failed, expired,
lost, withdrawn), created_at, expire_at, decisions, decided_by, decided_at, results, turn (the resumed turn's answer,
tool_calls and refusals), withdrawal (tenant, name, requested_by, approved_by, approved_at), withdrawn_at, run_by.

The audit actor is the person who acted, as role.grant's is (shared/roles.py): who asked, who approved and who ran it
is the point of the record. The target names the record, the tool and the document, never the question, a reason or
an answer. The event is written after the record, as roles.py writes role.grant; a bucket write that fails is kept on
the record as audit_pending and tried again at the record's next change, so the pause stands and the event is not lost.

The database client is passed in and nothing here imports a cloud library at the top: the chat service, reconcile.py
and the offline tests share one copy, and shared/audit_log.py (google.cloud.storage) is imported where a writer needs
it. Written 13 October 2026, with services/chat/approval_routes.py.
"""
from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timedelta, timezone

from shared import roles

TTL_H = float(os.environ.get("APPROVAL_TTL_H", "24"))    # a pending record expires this long after the pause
APPROVER = "doc_approver"                                 # the role that approves or rejects a withdrawal (make roles)
STATUSES = ("pending", "approved", "rejected", "cancelled", "answered", "failed", "expired", "lost", "withdrawn")
LIMIT = 50
ID = re.compile(r"^[0-9a-f]{32}$")


class ApprovalError(Exception):
    """A refusal with its HTTP status: the routes turn it into the response, reconcile.py into its exit line."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _at(v) -> datetime | None:
    """A stored time as an aware datetime (Firestore gives one back; a test may hold ISO text)."""
    if isinstance(v, str):
        v = datetime.fromisoformat(v)
    return v.replace(tzinfo=timezone.utc) if isinstance(v, datetime) and v.tzinfo is None else v


def _iso(v):
    return v.isoformat() if isinstance(v, datetime) else v


def _key(email) -> str:
    return str(email or "").strip().lower()


def _ref(db, approval_id: str):
    return db.collection("approvals").document(approval_id)


def approval_id(thread: str, checkpoint_id: str) -> str:
    """The record's id: one pause, one id, however often it is read."""
    return hashlib.sha256(f"{thread}|{checkpoint_id}".encode("utf-8")).hexdigest()[:32]


def kind_of(waiting: list) -> str:
    """approval when a waiting call takes approve (a second person's); answer when only ask_user waits."""
    return "approval" if any("approve" in (w.get("allowed_decisions") or []) for w in waiting) else "answer"


def document_of(rec: dict) -> str | None:
    """tenant/name of the withdrawal a record waits for, or carries; None for an answer record."""
    w = rec.get("withdrawal") or {}
    if w.get("name"):
        return f"{w.get('tenant') or rec['tenant']}/{w['name']}"
    for ask in rec.get("waiting") or []:
        if ask.get("tool") == "withdraw_document":
            name = str((ask.get("args") or {}).get("name") or "").strip()
            return name if "/" in name else f"{rec['tenant']}/{name}"
    return None


# ----------------------------------------------------------------------------- the audit events
def _emit(action: str, actor: dict, target: dict, meta: dict) -> str:
    from shared import audit_log          # lazy: it opens google.cloud.storage, which only a writer needs
    if action == "approval.request":
        return audit_log.emit("approval.request", actor, target, meta)
    if action == "approval.approve":
        return audit_log.emit("approval.approve", actor, target, meta)
    if action == "approval.reject":
        return audit_log.emit("approval.reject", actor, target, meta)
    if action == "doc.withdraw":
        return audit_log.emit("doc.withdraw", actor, target, meta)
    raise ValueError(f"{action!r} is not an approval event")


def _audit(db, rec: dict, action: str, by: str, meta: dict) -> dict:
    """One event for the record, written after it. A bucket write that fails stays on the record as audit_pending;
    flush() writes it at the record's next change."""
    event = {"action": action, "by": _key(by), "meta": meta}
    try:
        _emit(action, {"tenant_id": rec["tenant"], "email": _key(by)},
              {"approval": rec["approval_id"], "tool": (rec["waiting"][0]["tool"] if rec.get("waiting") else None),
               "document": document_of(rec)}, meta)
    except Exception:  # noqa: BLE001 - the record is the truth; the event follows at the next change
        pending = [*(rec.get("audit_pending") or []), event]
        _ref(db, rec["approval_id"]).set({"audit_pending": pending}, merge=True)
        rec["audit_pending"] = pending
    return rec


def flush(db, rec: dict) -> dict:
    """Write the events a failed bucket write left on the record, oldest first; stop at the first that fails again."""
    pending = list(rec.get("audit_pending") or [])
    while pending:
        e = pending[0]
        try:
            _emit(e["action"], {"tenant_id": rec["tenant"], "email": e["by"]},
                  {"approval": rec["approval_id"], "tool": (rec["waiting"][0]["tool"] if rec.get("waiting") else None),
                   "document": document_of(rec)}, e.get("meta") or {})
        except Exception:  # noqa: BLE001
            break
        pending.pop(0)
    if pending != (rec.get("audit_pending") or []):
        _ref(db, rec["approval_id"]).set({"audit_pending": pending}, merge=True)
        rec["audit_pending"] = pending
    return rec


def _write(db, rec: dict, update: dict) -> dict:
    """Merge a change into the record as it stands (the executor may have written since it was read), after any event
    an earlier change left pending."""
    rec = flush(db, get(db, rec["approval_id"]) or rec)
    _ref(db, rec["approval_id"]).set(update, merge=True)
    return {**rec, **update}


# ----------------------------------------------------------------------------- the record's life
def open_request(db, approval_id_: str, tenant: str, requester: str, session_id: str, thread: str, brain: str,
                 waiting: list, *, now: datetime | None = None) -> dict:
    """The pause as a record, or the record this pause already has. A withdrawal's pause is an approval.request
    event; a question's (ask_user) is not: no one but the person who asked is involved."""
    if not ID.match(approval_id_ or ""):
        raise ValueError("an approval id is 32 hex digits")
    snap = _ref(db, approval_id_).get()
    if snap.exists:
        return snap.to_dict() or {}
    now = now or _now()
    rec = {"approval_id": approval_id_, "tenant": tenant, "requester": _key(requester), "session_id": session_id,
           "thread": thread, "brain": brain, "kind": kind_of(waiting),
           "waiting": [{"tool": w["tool"], "args": dict(w.get("args") or {}), "call_id": w["call_id"],
                        "allowed_decisions": list(w["allowed_decisions"]), "description": w.get("description", "")}
                       for w in waiting],
           "status": "pending", "created_at": now, "expire_at": now + timedelta(hours=TTL_H),
           "decisions": None, "decided_by": None, "decided_at": None, "results": None, "turn": None,
           "withdrawal": None, "withdrawn_at": None, "run_by": None, "audit_pending": []}
    _ref(db, approval_id_).set(rec)
    if rec["kind"] == "approval":
        _audit(db, rec, "approval.request", requester, {"session_id": session_id, "expire_at": _iso(rec["expire_at"])})
    return rec


def get(db, approval_id_: str) -> dict | None:
    if not ID.match(approval_id_ or ""):
        return None
    snap = _ref(db, approval_id_).get()
    return (snap.to_dict() or {}) if snap.exists else None


def may_read(rec: dict, tenant: str, email: str, *, approver: bool = False) -> bool:
    """The person who asked reads their own record; a doc_approver of the same tenant reads a withdrawal's."""
    if rec.get("tenant") != tenant:
        return False
    return _key(email) == rec.get("requester") or (approver and rec.get("kind") == "approval")


def read(db, approval_id_: str, tenant: str, email: str, *, approver: bool = False) -> dict:
    """One record, by a point read: 404 unless the reader may read it, so a stranger cannot tell it exists."""
    rec = get(db, approval_id_)
    if rec is None or not may_read(rec, tenant, email, approver=approver):
        raise ApprovalError(404, "no such approval")
    return rec


def expired(rec: dict, now: datetime | None = None) -> bool:
    """A pending record past expire_at: nobody decided in time."""
    at = _at(rec.get("expire_at"))
    return rec.get("status") == "pending" and at is not None and at <= (now or _now())


def expire(db, rec: dict, now: datetime | None = None) -> dict:
    """A pending record past expire_at, marked expired in code (no TTL policy touches a record); any other as it is."""
    return _write(db, rec, {"status": "expired"}) if expired(rec, now) else rec


def decidable(db, rec: dict, *, now: datetime | None = None) -> dict:
    """The record a decision may still end: 410 when it expired (and it is marked so), 409 when already decided."""
    now = now or _now()
    if expired(rec, now):
        rec = expire(db, rec, now)
        raise ApprovalError(410, f"approval {rec['approval_id']} expired at {_iso(rec['expire_at'])}, {TTL_H:g} hours "
                                 "after the pause: nothing was done, and the person who asked asks again")
    if rec.get("status") != "pending":
        raise ApprovalError(409, f"approval {rec['approval_id']} is already {rec['status']}"
                                 + (f", by {rec['decided_by']}" if rec.get("decided_by") else ""))
    return rec


def status_of(rec: dict, decisions: list, by: str, results: list) -> str:
    """What the decisions and the resumed turn amount to: a reject is cancelled by the person who asked and rejected
    by a second person; respond alone is answered; approve is approved when the tool ran, failed when it refused."""
    kinds = [d.get("type") for d in decisions]
    if "reject" in kinds:
        return "cancelled" if _key(by) == rec.get("requester") else "rejected"
    if all(k == "respond" for k in kinds):
        return "answered"
    return "approved" if all(r.get("status") == "success" for r in results) else "failed"


def settle(db, rec: dict, decisions: list, by: str, results: list, turn: dict, *, now: datetime | None = None) -> dict:
    """The decision and its outcome on the record: results is one {call_id, tool, status, content} per waiting
    call, turn the resumed turn's answer, tool_calls and refusals. A withdrawal's outcome is one event."""
    status = status_of(rec, decisions, by, results)
    rec = _write(db, rec, {"status": status, "decisions": decisions, "decided_by": _key(by), "decided_at": now or _now(),
                           "results": results, "turn": turn})
    if rec["kind"] == "approval":
        _audit(db, rec, "approval.approve" if status in ("approved", "failed") else "approval.reject", by,
               {"status": status, "by": "requester" if _key(by) == rec["requester"] else "second_person"})
    return rec


def lost(db, rec: dict) -> dict:
    """The turn no longer waits, and nobody decided: the record says so, and the route answers 409."""
    return _write(db, rec, {"status": "lost"}) if rec.get("status") == "pending" else rec


def executor(db, approval_id_: str):
    """The `withdraw` the resumed turn's withdraw_document calls, with the thread's tenant and person and the
    approver decide() named. It withdraws nothing: the approved withdrawal goes on the record for the operator's
    make withdraw-run, and the tool's result says so."""
    def withdraw(*, tenant: str, name: str, requested_by: str, approved_by: str) -> dict:
        rec = get(db, approval_id_)
        if rec is None or rec.get("tenant") != tenant or _key(requested_by) != rec.get("requester"):
            raise ValueError(f"approval {approval_id_} is not this conversation's withdrawal")
        at = _now()
        _write(db, rec, {"withdrawal": {"tenant": tenant, "name": name, "requested_by": _key(requested_by),
                                        "approved_by": _key(approved_by), "approved_at": at}})
        return {"status": "approved", "approval": approval_id_,
                "next": f"the operator runs make withdraw-run APPROVAL={approval_id_}; until then the document is still in search"}
    return withdraw


def recheck(db, approval_id_: str) -> dict:
    """Before the tombstone, from the record alone: the record exists and is approved, not yet withdrawn; the
    withdrawal names a document of the record's own tenant; the approver is not the person who asked and still holds
    doc_approver in that tenant. Each refusal is an ApprovalError with the reason."""
    try:
        rec = get(db, approval_id_)
    except Exception as e:  # noqa: BLE001 - a record that cannot be read runs nothing
        raise ApprovalError(503, f"approval {approval_id_} could not be read ({type(e).__name__}): try again")
    if rec is None:
        raise ApprovalError(404, f"no such approval: {approval_id_}")
    if rec.get("status") == "withdrawn":
        raise ApprovalError(409, f"approval {approval_id_} was already run at {_iso(rec.get('withdrawn_at'))}"
                                 f" by {rec.get('run_by')}")
    if rec.get("status") != "approved":
        raise ApprovalError(409, f"approval {approval_id_} is {rec.get('status')}, not approved: nothing to run")
    w = rec.get("withdrawal") or {}
    if w.get("tenant") != rec["tenant"] or not w.get("name") or "/" in str(w["name"]):
        raise ApprovalError(409, f"approval {approval_id_} names no document of {rec['tenant']}: nothing to run")
    if not w.get("approved_by") or w["approved_by"] == rec["requester"] or w.get("requested_by") != rec["requester"]:
        raise ApprovalError(403, f"approval {approval_id_} was not approved by a second person: nothing runs")
    held = roles.roles_for(db, rec["tenant"], w["approved_by"])
    if roles.UNREAD in held:
        raise ApprovalError(503, f"{rec['tenant']}'s roster could not be read, so the approver cannot be checked: try again")
    if APPROVER not in held:
        raise ApprovalError(403, f"{w['approved_by']} no longer holds {APPROVER} in {rec['tenant']}: the approval does not stand")
    return rec


def withdrawn(db, rec: dict, *, run_by: str, now: datetime | None = None) -> dict:
    """After the tombstone: the record says who ran it and when, and the bucket gets doc.withdraw."""
    rec = _write(db, rec, {"status": "withdrawn", "withdrawn_at": now or _now(), "run_by": _key(run_by)})
    return _audit(db, rec, "doc.withdraw", run_by, {"approved_by": (rec.get("withdrawal") or {}).get("approved_by"),
                                                     "requested_by": rec.get("requester")})


# ----------------------------------------------------------------------------- what a route answers
def who_decides(rec: dict) -> str:
    if rec.get("kind") == "answer":
        return "the person who asked, with a respond decision"
    return f"a second person on {rec['tenant']}'s roster who holds {APPROVER} (approve or reject); the person who asked may reject"


def view(rec: dict) -> dict:
    """The record as a route answers it: every field but the audit outbox, each time as ISO text, and how to decide."""
    out = {k: v for k, v in rec.items() if k != "audit_pending"}
    for k in ("created_at", "expire_at", "decided_at", "withdrawn_at"):
        out[k] = _iso(out.get(k))
    if out.get("withdrawal"):
        out["withdrawal"] = {**out["withdrawal"], "approved_at": _iso(out["withdrawal"].get("approved_at"))}
    out["document"] = document_of(rec)
    out["decide"] = f"POST /v1/approvals/{rec['approval_id']}/decide"
    out["who_decides"] = who_decides(rec)
    return out


def list_for(db, tenant: str, email: str, *, approver: bool = False, now: datetime | None = None) -> dict:
    """The person's own records, newest first, and for a doc_approver the tenant's pending withdrawals, oldest first.
    A pending record past expire_at is shown as expired (and marked so)."""
    now = now or _now()

    def rows(query):
        return [view(expire(db, s.to_dict() or {}, now)) for s in query.stream()]

    mine = rows(db.collection("approvals").where("tenant", "==", tenant).where("requester", "==", _key(email)).limit(LIMIT))
    mine.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    out = {"mine": mine, "approver": approver}
    if approver:
        pending = [r for r in rows(db.collection("approvals").where("tenant", "==", tenant).where("status", "==", "pending")
                                   .limit(LIMIT)) if r["kind"] == "approval" and r["status"] == "pending"]
        pending.sort(key=lambda r: r.get("created_at") or "")
        out["pending"] = pending
    return out
