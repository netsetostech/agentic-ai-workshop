"""Roles in a tenant (workshop lesson 5.6): which desks a person may use and which case queues they read.

A role document is tenants/{tenant}/roles/{email}, {roles, set_by, set_at}, written only by the operator (make roles,
commands/desk_ops.py roles). It is a document of its own, beside the member document, because shared/tenancy.py's
add_member writes the member document whole, without merge: a role kept there would be erased by the next make roster.

    employee           the answer desks (handbook, statute, clarify, out_of_scope) and the case desk
    leaver             the case desk only; the answer desks are denied (set by hand, for a grace period)
    people_ops         the people queue; grievance cases only when the person who raised one chose to share it
    payroll            the payroll queue (exit dues); people_ops reads it too
    ic_member:<unit>   the POSH cases of that unit, and only those whose contacts name this person
    grc_member         grievance cases and their status
    privacy            privacy requests
    desk_eval          the Desk's eval routes, for the eval accounts (the routed Desk, workshop lesson 10.4)

roles_for() is the one reader. A member with no role document is ["employee"]. A document lists every role it grants,
so "employee" is never implied beside it: ["leaver"] is a leaver and nothing else. A person on no roster has no role
at all. A read that fails allows the case desk only (UNREAD), so a person can still reach a human while Firestore is
unwell, and reads no queue. desk_reviewer and desk_pilot are reserved names for a pilot's review sample and its group;
an operator may write them, and nothing reads them.

The database client is passed in and nothing here imports a cloud library at the top, so the chat service, the
operator's commands and the offline tests share one copy. A grant and a revoke are audit events (shared/audit_log.py,
role.grant and role.revoke), written after the document.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

EMPLOYEE, LEAVER = "employee", "leaver"
ROLES = (EMPLOYEE, LEAVER, "people_ops", "payroll", "grc_member", "privacy", "desk_eval")
RESERVED = ("desk_reviewer", "desk_pilot")
IC_ROLE = re.compile(r"^ic_member:([a-z0-9_-]{1,40})$")
UNREAD = "unread"            # what a failed read returns; never written
ANSWER_DESKS = ("handbook", "statute", "clarify", "out_of_scope")
DESKS: dict[str, tuple[str, ...]] = {EMPLOYEE: ANSWER_DESKS + ("case",), LEAVER: ("case",), UNREAD: ("case",)}


def valid(role: str) -> bool:
    return role in ROLES or role in RESERVED or bool(IC_ROLE.match(role or ""))


def ic_units(roles) -> set[str]:
    """The units whose Internal Committee this person sits on."""
    return {m.group(1) for m in (IC_ROLE.match(r) for r in roles or ()) if m}


def desks(roles) -> set[str]:
    """The desks a set of roles opens: the union of each role's."""
    return {d for r in roles or () for d in DESKS.get(r, ())}


def _key(email: str) -> str:
    return (email or "").strip().lower()


def role_ref(db, tenant: str, email: str):
    return db.collection("tenants").document(tenant).collection("roles").document(_key(email))


def _member(db, tenant: str, email: str) -> bool:
    """shared/tenancy.is_member's point read, with the client passed in."""
    return db.collection("tenants").document(tenant).collection("members").document(_key(email)).get().exists


def roles_for(db, tenant: str, email: str) -> list[str]:
    """The person's roles in the tenant. Not a member: []. No document: ["employee"]. A failed read: [UNREAD]."""
    if not tenant or not email:
        return []
    try:
        if not _member(db, tenant, email):
            return []
        snap = role_ref(db, tenant, email).get()
    except Exception:  # noqa: BLE001 - an unreadable role is the case desk only, never more
        return [UNREAD]
    if not snap.exists:
        return [EMPLOYEE]
    return [r for r in ((snap.to_dict() or {}).get("roles") or []) if isinstance(r, str) and valid(r)]


def _emit(action: str, tenant: str, email: str, roles: list[str], by: str) -> str:
    from shared import audit_log          # lazy: it opens google.cloud.storage, which only a writer needs
    actor = {"tenant_id": tenant, "email": by}
    target = {"email": _key(email), "roles": roles}
    if action == "role.grant":
        return audit_log.emit("role.grant", actor, target)
    return audit_log.emit("role.revoke", actor, target)


def set_roles(db, tenant: str, email: str, roles, by: str, now: datetime | None = None, audit: bool = True) -> dict:
    """Write the person's role document: exactly these roles. An empty list deletes it, which makes the person an
    employee again. Refuses a non-member (shared/tenancy.add_member first, make roster) and a role it does not know.
    Returns {email, before, after, granted, revoked}; each grant and each revoke is one audit event."""
    email = _key(email)
    wanted = sorted({r.strip() for r in roles or () if r and r.strip()})
    bad = [r for r in wanted if not valid(r)]
    if bad:
        raise ValueError(f"unknown role(s) {bad}: one of {list(ROLES + RESERVED)} or ic_member:<unit>")
    if not _member(db, tenant, email):
        raise PermissionError(f"{email} is not on {tenant}'s roster: make roster TENANT={tenant} MEMBERS={email} first")
    ref = role_ref(db, tenant, email)
    snap = ref.get()
    before = sorted((snap.to_dict() or {}).get("roles") or []) if snap.exists else None
    if wanted:
        ref.set({"roles": wanted, "set_by": by, "set_at": now or datetime.now(timezone.utc)})
    elif snap.exists:
        ref.delete()
    held = before if before is not None else [EMPLOYEE]
    after = wanted or [EMPLOYEE]
    granted, revoked = sorted(set(after) - set(held)), sorted(set(held) - set(after))
    if audit and granted:
        _emit("role.grant", tenant, email, granted, by)
    if audit and revoked:
        _emit("role.revoke", tenant, email, revoked, by)
    return {"email": email, "before": held, "after": after, "granted": granted, "revoked": revoked}


def revoke(db, tenant: str, email: str, roles, by: str, now: datetime | None = None, audit: bool = True) -> dict:
    """Take roles away; "all" deletes the document (the person is an employee again)."""
    if roles == "all" or list(roles or ()) == ["all"]:
        return set_roles(db, tenant, email, [], by, now, audit)
    snap = role_ref(db, tenant, email).get()
    held = ((snap.to_dict() or {}).get("roles") or []) if snap.exists else [EMPLOYEE]
    return set_roles(db, tenant, email, [r for r in held if r not in set(roles)], by, now, audit)


def list_roles(db, tenant: str) -> dict[str, list[str]]:
    """Every role document of the tenant: email -> roles. A member with none is an employee and is not listed."""
    return {s.id: list((s.to_dict() or {}).get("roles") or [])
            for s in db.collection("tenants").document(tenant).collection("roles").stream()}
