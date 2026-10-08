"""The case queue (workshop lesson 5.6): a request handed to the person the law or the company names, kept as a record.

A case lives at cases/{case_id}, one collection for every tenant, each record carrying its tenant. Ids are
secrets.token_hex(16), so an id says nothing and cannot be guessed. Every read is a point read that checks the
record's tenant and then the reader - the person who raised it, or a holder of its queue's role (shared/roles.py,
shared/desk_law.QUEUES) - and answers 404 to anyone else, so a stranger cannot tell a case from a missing one.

    draft()      a proposal for the person to read: the queue, the clock, the basis, an editable summary, and
                 expire_at 30 minutes out. Nobody else sees a draft, or any record that was never opened, and no
                 audit event is written for one.
    confirm()    the person's own confirmed words become the case, in a transaction carrying a client token: the same
                 token again returns the same case, and a draft past expire_at is 410 (checked here; the TTL on
                 cases.expire_at only cleans up). expire_at is cleared, the clock starts, and case.open is written.
    open_posh()  POSH has no draft and no text: the person picks the unit and which Internal Committee members to
                 contact, and the case opens at once, with a client token, so a doubled press opens one case. At
                 least one chosen member must hold that unit's ic_member role, or nobody could read it (409).
    cancel()     the person withdraws a draft (the record is deleted, with their words: no case existed, and no
                 event) or an open case (case.close).
    set_status() the queue moves a case along: acknowledged, in_progress, resolved, closed (case.update, case.close).
    list_for()   the reader's inbox, queue by queue - every active case, then the latest finished ones - and the
                 cases they raised themselves.
    overdue()    cases within 24 hours of due_at and still unacknowledged, and breached cases: the hourly job's list.

A record's fields: tenant, requester, case_type, queue, unit and chosen_contacts (posh), status (draft, open,
acknowledged, in_progress, resolved, closed, withdrawn), source (rule, model, desk, button), via (the door the person
came through: "direct" for the kit's own surfaces), created_at, opened_at, due_at, sla_basis, route_trace,
route_tried, partial_answer_citations (the ids of the passages a desk cited before it handed over), summary (the
person's confirmed words, 1,000 characters at most; null for posh), statutory_flags, question_sha256, expire_at
(drafts only), people_ops_opt_in (a grievance the person chose to share with the People team). A POSH record holds
the unit and the chosen contacts and no text at all.

The audit actor of a case event is the case reference, case:<case_id>, never an email: the audit bucket refuses every
delete (terraform/storage.tf), and an email in it could never be taken back. A sensitive type (posh, grievance,
privacy_request) is "sensitive" in the event, with no queue name. An event is first written into the record, in the
same transaction as the change it records (audit_pending), and then to the bucket by _flush(), which claims it, writes
it and clears it; an event a failed write left behind is written by the next call that touches the case. So an event
is never lost, and is written twice only when a claim outlives AUDIT_LEASE.

The database client is passed in; google.cloud.firestore (the transaction, DELETE_FIELD) and shared/audit_log.py
(google.cloud.storage) are imported where they are used, so the chat service imports this module without either at
the top, and the offline tests run it against a fake.
"""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import date, datetime, timedelta, timezone

try:                                   # the package import (the services, the tests) and the flat one (an image
    from shared import desk_law, roles as roles_mod   # that copies shared/ beside its own code)
except ImportError:                    # pragma: no cover
    import desk_law                    # type: ignore
    import roles as roles_mod          # type: ignore

STATUSES = ("draft", "open", "acknowledged", "in_progress", "resolved", "closed", "withdrawn")
ACTIVE = ("open", "acknowledged", "in_progress")
DONE = ("resolved", "closed", "withdrawn")
NEXT = {"open": ("acknowledged", "in_progress", "resolved", "closed"),
        "acknowledged": ("in_progress", "resolved", "closed"),
        "in_progress": ("resolved", "closed"),
        "resolved": ("in_progress", "closed")}
SOURCES = ("rule", "model", "desk", "button")
TYPES = tuple(desk_law.CASE_TYPES)
DRAFT_TTL = timedelta(minutes=30)
TOKEN_TTL = timedelta(days=1)
DUE_SOON = timedelta(hours=24)
SUMMARY_MAX = 1000
LIMIT = 50                       # the latest finished cases per queue, and the cases a person raised
ACTIVE_LIMIT = 500               # active cases per queue: all of them, in any company the kit is sized for
AUDIT_LEASE = timedelta(minutes=2)
IST = timezone(timedelta(hours=5, minutes=30))     # India has no daylight saving: a fixed offset, no tz database
ID = re.compile(r"^[0-9a-f]{32}$")
TOKEN = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
EMAIL = re.compile(r"^[^@\s:]+@[^@\s:]+\.[^@\s:]+$")
UNIT = re.compile(r"^[a-z0-9_-]{1,40}$")
PREFIX = re.compile(r"^[A-Z]{1,5}$")
SECTIONS = ("posh", "grc", "privacy", "payroll", "people", "clause_prefixes")
EXIT_LATE = "exit_dues_date_may_have_passed"
VIEW = ("case_id", "tenant", "requester", "case_type", "queue", "unit", "chosen_contacts", "status", "source", "via",
        "created_at", "opened_at", "acknowledged_at", "status_at", "due_at", "sla_basis", "summary", "statutory_flags", "route_trace",
        "route_tried", "partial_answer_citations", "expire_at", "people_ops_opt_in", "last_working_day")


class CaseError(Exception):
    """A refusal with its HTTP status: services/chat/desk.py turns it into the response."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


def _fs():
    from google.cloud import firestore   # lazy: the transaction and DELETE_FIELD, only where a record is written
    return firestore


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ref(db, case_id: str):
    return db.collection("cases").document(case_id)


def _iso(v):
    return v.isoformat() if isinstance(v, (datetime, date)) else v


def sensitive(case_type: str) -> bool:
    return case_type in desk_law.SENSITIVE_CASES


# ---------------------------------------------------------------- the queues the operator configures
def _section_errors(name: str, sec, allow_extra=()) -> list[str]:
    if not isinstance(sec, dict):
        return [f"{name}: an object with name, contact and sla_days"]
    errs = []
    if not str(sec.get("name") or "").strip():
        errs.append(f"{name}.name is empty")
    if not EMAIL.match(str(sec.get("contact") or "")):
        errs.append(f"{name}.contact is not an email address")
    days = sec.get("sla_days")
    if days is not None and (not isinstance(days, int) or isinstance(days, bool) or not 0 < days <= 365):
        errs.append(f"{name}.sla_days is {days!r}: a whole number of days, 1 to 365, or null")
    extra = set(sec) - {"name", "contact", "sla_days", *allow_extra} - {k for k in sec if str(k).startswith("_")}
    if extra:
        errs.append(f"{name}: unknown field(s) {sorted(extra)}")
    return errs


def posh_errors(cfg) -> list[str]:
    """What the POSH section lacks: every unit's Internal Committee (one member at least, each with an email) and its
    district's Local Committee contact. An empty list: the section is complete."""
    posh = (cfg or {}).get("posh") if isinstance(cfg, dict) else None
    if not isinstance(posh, dict):
        return ["posh: no POSH section - every unit's Internal Committee and its Local Committee contact"]
    units = posh.get("units")
    if not isinstance(units, dict) or not units:
        return ["posh.units: no unit"]
    errs = []
    for unit, u in units.items():
        if not UNIT.match(str(unit)):
            errs.append(f"posh.units.{unit}: a unit id is lower case letters, digits, _ or -")
        u = u if isinstance(u, dict) else {}
        ic = u.get("ic")
        if not isinstance(ic, list) or not ic:
            errs.append(f"posh.units.{unit}.ic: no Internal Committee member")
        else:
            for i, m in enumerate(ic):
                if not isinstance(m, dict) or not EMAIL.match(str(m.get("email") or "")):
                    errs.append(f"posh.units.{unit}.ic[{i}]: no email address")
        lc = u.get("local_committee")
        if not isinstance(lc, dict) or not str(lc.get("name") or "").strip() or not str(lc.get("contact") or "").strip():
            errs.append(f"posh.units.{unit}.local_committee: the district's Local Committee needs a name and a contact")
    days = posh.get("sla_days")
    if days is not None and (not isinstance(days, int) or isinstance(days, bool) or not 0 < days <= 365):
        errs.append(f"posh.sla_days is {days!r}: a whole number of days, 1 to 365, or null")
    return errs


def posh_offer(cfg) -> dict | None:
    """The POSH card, one copy for every place that shows it (GET /v1/cases/offer, and the routed Desk's reply to a
    POSH disclosure): each office's name, its Internal Committee members (name and email) and its district's Local
    Committee contact. None while the POSH section is incomplete (posh_errors), so no card names an office without
    its committee and its Local Committee."""
    if posh_errors(cfg):
        return None
    units = cfg["posh"]["units"]
    return {u: {"name": spec.get("name") or u,
                "members": [{"name": m.get("name"), "email": str(m.get("email") or "").lower()} for m in spec.get("ic") or []],
                "local_committee": spec.get("local_committee")} for u, spec in sorted(units.items())}


def queue_errors(cfg) -> list[str]:
    """Everything wrong with a case_queues document (make desk-queues refuses it). A POSH section, when present, must
    be complete; the other sections are optional, and a type whose queue is absent cannot be raised."""
    if not isinstance(cfg, dict):
        return ["case_queues: a JSON object"]
    errs = [f"unknown section {k!r}: one of {list(SECTIONS)}" for k in cfg if k not in SECTIONS and not str(k).startswith("_")]
    if "posh" in cfg:
        errs += posh_errors(cfg)
    for name in ("grc", "privacy", "payroll", "people"):
        if name in cfg:
            errs += _section_errors(name, cfg[name], ("accepts_desk_case",) if name == "grc" else ())
    if "accepts_desk_case" in (cfg.get("grc") or {}) and not isinstance(cfg["grc"]["accepts_desk_case"], bool):
        errs.append("grc.accepts_desk_case: true or false")
    prefixes = cfg.get("clause_prefixes", {})
    if not isinstance(prefixes, dict):
        errs.append("clause_prefixes: an object of PREFIX -> queue")
    else:
        for k, v in prefixes.items():
            if not PREFIX.match(str(k)) or v not in desk_law.QUEUES:
                errs.append(f"clause_prefixes.{k}={v!r}: a prefix of capital letters -> one of {list(desk_law.QUEUES)}")
    return errs


def reader_gaps(db, tenant: str, cfg) -> dict:
    """Who would read a case here, by the roles the tenant holds now: {"posh_units": the units no Internal Committee
    member of which holds ic_member:<unit> (a POSH case there could not be opened), "ic": "<unit>: <email>" for each
    member who does not (they are shown on the card but read nothing here), "queues": the configured queues no member
    holds a role to read}. The operator's check (commands/desk_ops.py); open_posh() checks the chosen members again."""
    cfg = cfg if isinstance(cfg, dict) else {}
    out: dict[str, list[str]] = {"posh_units": [], "ic": [], "queues": []}
    for unit, u in sorted((((cfg.get("posh") or {}).get("units")) or {}).items()):
        readers = 0
        for m in (u or {}).get("ic") or []:
            email = str((m or {}).get("email") or "").lower()
            if f"ic_member:{unit}" in roles_mod.roles_for(db, tenant, email):
                readers += 1
            else:
                out["ic"].append(f"{unit}: {email}")
        if not readers:
            out["posh_units"].append(unit)
    held = {r for e in roles_mod.list_roles(db, tenant) for r in roles_mod.roles_for(db, tenant, e)}
    for q, spec in desk_law.QUEUES.items():
        if configured(q, cfg) and not held & (set(spec["read"]) | set(spec["status"])):
            out["queues"].append(q)
    return out


def configured(queue: str, queues: dict) -> bool:
    sec = (queues or {}).get(queue)
    return isinstance(sec, dict) and bool(EMAIL.match(str(sec.get("contact") or "")))


def queue_for(case_type: str, queues: dict, unit: str | None = None, clause: str | None = None) -> str | None:
    """The queue a case of this type goes to on this tenant, or None when none is configured."""
    spec = desk_law.CASE_TYPES[case_type]
    if case_type == "posh":
        units = (((queues or {}).get("posh") or {}).get("units") or {})
        return desk_law.IC_QUEUE + unit if unit in units and not posh_errors(queues) else None
    if case_type == "people_query" and clause:
        mapped = ((queues or {}).get("clause_prefixes") or {}).get(clause.split("-", 1)[0].upper())
        if mapped and configured(mapped, queues):
            return mapped
    for q in (spec["queue"], spec["fallback"]):
        if q and configured(q, queues):
            return q
    return None


def _due(case_type: str, queue: str, queues: dict, at: datetime) -> tuple[datetime | None, str | None]:
    """When the case is due, and why: the committee's thirty days when the company's GRC takes a case raised here as
    the application (s.4(6) says "may complete"), else the queue's own target, labelled as the company's."""
    if case_type == "grievance" and queue == "grc" and ((queues or {}).get("grc") or {}).get("accepts_desk_case") is True:
        return at + timedelta(days=30), "Industrial Relations Code, 2020, s.4(6): the committee may complete within 30 days"
    key = "posh" if queue.startswith(desk_law.IC_QUEUE) else queue
    days = ((queues or {}).get(key) or {}).get("sla_days")
    if isinstance(days, int) and not isinstance(days, bool) and days > 0:
        return at + timedelta(days=days), f"the company's own target: {days} days (case_queues.{key}.sla_days)"
    return None, None


def working_days_after(day: date, n: int) -> date:
    """The n-th working day after `day`, Monday to Friday (no holiday calendar is loaded)."""
    d, left = day, n
    while left:
        d += timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


def exit_flags(last_working_day: date | None, today: date) -> list[str]:
    """The desk's own reading of s.17(2): two working days from the last working day the person gave. Not legal advice;
    the clock text says so."""
    if last_working_day is None:
        return []
    return [EXIT_LATE] if today > working_days_after(last_working_day, 2) else []


# ---------------------------------------------------------------- reading
def access(rec: dict, email: str, roles) -> tuple[bool, bool]:
    """(may read it, may move its status). The person who raised it reads it; a draft, and any record that was never
    opened, is theirs alone. A POSH case is read only by the chosen Internal Committee members of its unit."""
    email, roles = (email or "").lower(), set(roles or ())
    mine = rec.get("requester") == email
    if rec.get("status") == "draft" or rec.get("opened_at") is None:
        return mine, False
    q = rec.get("queue") or ""
    if q.startswith(desk_law.IC_QUEUE):
        on = f"ic_member:{q[len(desk_law.IC_QUEUE):]}" in roles and email in [c.lower() for c in rec.get("chosen_contacts") or []]
        return on or mine, on
    spec = desk_law.QUEUES.get(q) or {}
    moves = bool(roles & set(spec.get("status", ())))
    reads = moves or bool(roles & set(spec.get("read", ()))) or (
        bool(roles & set(spec.get("opt_in", ()))) and rec.get("people_ops_opt_in") is True)
    return reads or mine, moves


def read(db, case_id: str, tenant: str, email: str, roles) -> dict:
    """One case, by a point read: 404 for a malformed id, a missing case, another tenant's, or one the reader may not
    read."""
    if not ID.match(case_id or ""):
        raise CaseError(404, "no such case")
    snap = _ref(db, case_id).get()
    rec = (snap.to_dict() or {}) if snap.exists else None
    if not rec or rec.get("tenant") != tenant or not access(rec, email, roles)[0]:
        raise CaseError(404, "no such case")
    return rec


def list_for(db, tenant: str, email: str, roles, limit: int = LIMIT) -> dict:
    """{"inbox": the cases of every queue the reader's roles read, newest first - every active case, then the latest
    finished ones, so a finished case never hides an open one; "mine": the cases they raised; "more": true when a list
    was cut at its limit}. A POSH queue is asked only for the cases whose contacts name the reader."""
    email, held = (email or "").lower(), set(roles or ())
    queues = [q for q, spec in desk_law.QUEUES.items()
              if held & (set(spec["read"]) | set(spec["status"]) | set(spec["opt_in"]))]
    queues += [desk_law.IC_QUEUE + u for u in sorted(roles_mod.ic_units(held))]
    inbox, seen, more = [], set(), False
    for q in queues:
        base = db.collection("cases").where("tenant", "==", tenant).where("queue", "==", q)
        if q.startswith(desk_law.IC_QUEUE):
            base = base.where("chosen_contacts", "array_contains", email)
        for statuses, n in ((ACTIVE, ACTIVE_LIMIT), (DONE, limit)):
            rows = list(base.where("status", "in", list(statuses))
                        .order_by("created_at", direction="DESCENDING").limit(n).stream())
            more = more or len(rows) >= n
            for s in rows:
                rec = s.to_dict() or {}
                if rec.get("case_id") not in seen and access(rec, email, held)[0]:
                    seen.add(rec.get("case_id"))
                    inbox.append(rec)
    raised = list(db.collection("cases").where("tenant", "==", tenant).where("requester", "==", email)
                  .order_by("created_at", direction="DESCENDING").limit(limit).stream())
    more = more or len(raised) >= limit
    mine = [r for r in (s.to_dict() or {} for s in raised) if r.get("opened_at") is not None]
    inbox.sort(key=lambda r: (r.get("status") in ACTIVE, _iso(r.get("created_at")) or ""), reverse=True)
    return {"inbox": inbox, "mine": mine, "more": more}


def tenant_cases(db, tenant: str, now: datetime | None = None) -> list[dict]:
    """The tenant's open cases for the operator (make cases): each with its state - open, due (within 24 hours and
    unacknowledged) or breached."""
    now = now or _now()
    out = []
    for s in (db.collection("cases").where("tenant", "==", tenant).where("status", "in", list(ACTIVE))
              .order_by("due_at").stream()):
        rec = s.to_dict() or {}
        out.append({**rec, "state": _state(rec, now) or "open"})
    return out


def _state(rec: dict, now: datetime) -> str | None:
    due = rec.get("due_at")
    if not isinstance(due, datetime) or rec.get("status") not in ACTIVE:
        return None
    if due < now:
        return "breached"
    if due <= now + DUE_SOON and rec.get("status") == "open":
        return "due"
    return None


def overdue(db, now: datetime | None = None) -> list[dict]:
    """Every tenant's cases within 24 hours of due and still open (unacknowledged), and every breached case: the id,
    the queue and due_at only, which is all the hourly job logs. A sensitive case's queue is "sensitive": a queue
    such as ic:<unit> would say what the case is about."""
    now = now or _now()
    out = []
    for s in (db.collection("cases").where("status", "in", list(ACTIVE))
              .where("due_at", "<=", now + DUE_SOON).stream()):
        rec = s.to_dict() or {}
        state = _state(rec, now)
        if state:
            out.append({"case_id": rec.get("case_id"),
                        "queue": "sensitive" if sensitive(rec.get("case_type")) else rec.get("queue"),
                        "due_at": _iso(rec.get("due_at")), "state": state})
    return out


def owner(rec: dict, queues: dict) -> dict:
    """Who has the case, as the person and the queue see it. A POSH case names the chosen members and, always, the
    district's Local Committee."""
    q = rec.get("queue") or ""
    if q.startswith(desk_law.IC_QUEUE):
        unit = (((queues or {}).get("posh") or {}).get("units") or {}).get(rec.get("unit")) or {}
        chosen = set(rec.get("chosen_contacts") or [])
        return {"queue_name": "Internal Committee", "unit": rec.get("unit"),
                "members": [{"email": m.get("email"), "name": m.get("name")} for m in unit.get("ic") or []
                            if str(m.get("email") or "").lower() in chosen],
                "local_committee": unit.get("local_committee")}
    sec = (queues or {}).get(q) or {}
    return {"queue_name": sec.get("name") or desk_law.QUEUES.get(q, {}).get("name"), "contact": sec.get("contact")}


def clock(rec: dict, queues: dict) -> list[str]:
    """The clock shown with a case: what the law says, and the company's own target when it set one."""
    t = rec["case_type"]
    key = desk_law.CASE_TYPES[t]["clock"]
    if t == "grievance" and rec.get("queue") == "grc" and ((queues or {}).get("grc") or {}).get("accepts_desk_case") is True:
        key = "grievance_accepted"
    out = [desk_law.CLOCKS[key]] if key else []
    if EXIT_LATE in (rec.get("statutory_flags") or []):
        out.append(desk_law.CLOCKS["exit_dues_late"])
    if str(rec.get("sla_basis") or "").startswith("the company's own target") and t != "privacy_request":
        out.append(desk_law.CLOCKS["company_target"])
    return out


def view(rec: dict, queues: dict | None = None) -> dict:
    """A case as the routes return it: its fields (never the token or the question's hash), who has it, the clock and
    the basis."""
    out = {k: _iso(rec.get(k)) for k in VIEW if k in rec}
    out["sensitive"] = sensitive(rec["case_type"])
    out["owner"] = owner(rec, queues or {})
    out["clock"] = clock(rec, queues or {})
    out["basis"] = desk_law.basis_for(rec["case_type"])
    return out


# ---------------------------------------------------------------- writing
def _new(tenant: str, requester: str, case_type: str, queue: str, source: str, via: str, now: datetime) -> dict:
    if source not in SOURCES:
        raise CaseError(422, f"source {source!r}: one of {list(SOURCES)}")
    if not re.match(r"^[a-z]{1,16}$", via or ""):
        raise CaseError(422, "via: a short lower-case name")
    return {"case_id": secrets.token_hex(16), "tenant": tenant, "requester": requester.lower(),
            "case_type": case_type, "queue": queue, "unit": None, "chosen_contacts": [], "source": source, "via": via,
            "created_at": now, "opened_at": None, "status_at": now, "due_at": None, "sla_basis": None,
            "route_trace": None, "route_tried": None, "partial_answer_citations": [], "summary": None,
            "statutory_flags": [], "question_sha256": None, "people_ops_opt_in": False, "token_sha256": None,
            "audit_open": None, "audit_pending": []}


def _summary(text) -> str:
    text = "" if text is None else str(text).strip()
    if len(text) > SUMMARY_MAX:
        raise CaseError(422, f"the summary is {len(text)} characters: {SUMMARY_MAX} at most")
    return text


def _today(now: datetime) -> date:
    """The day in India: the last working day a person gives is an Indian date."""
    return now.astimezone(IST).date()


def draft(db, tenant: str, requester: str, case_type: str, queues: dict, *, summary: str | None = None,
          source: str = "button", via: str = "direct", clause: str | None = None, route_trace=None,
          route_tried: str | None = None, partial_answer_citations=None, question_sha256: str | None = None,
          last_working_day: date | None = None, people_ops_opt_in: bool = False, now: datetime | None = None) -> dict:
    """A draft for the person to read, edit and confirm, or cancel. Nobody else reads it, and it expires in 30
    minutes. posh has no draft: open_posh()."""
    if case_type not in desk_law.CASE_TYPES:
        raise CaseError(422, f"case_type {case_type!r}: one of {list(TYPES)}")
    if not desk_law.CASE_TYPES[case_type]["draft"]:
        raise CaseError(422, f"a {case_type} case has no draft: it opens directly, with no text")
    queue = queue_for(case_type, queues, clause=clause)
    if queue is None:
        raise CaseError(409, f"{case_type}: this company has not set up the queue for it yet - ask the People team")
    if question_sha256 is not None and not re.match(r"^[0-9a-f]{64}$", question_sha256):
        raise CaseError(422, "question_sha256: 64 hex digits")
    cited = [str(c) for c in (partial_answer_citations or [])][:20]
    now = now or _now()
    rec = _new(tenant, requester, case_type, queue, source, via, now)
    rec.update({"status": "draft", "summary": _summary(summary), "expire_at": now + DRAFT_TTL,
                "route_trace": route_trace, "route_tried": route_tried, "partial_answer_citations": cited,
                "question_sha256": question_sha256, "people_ops_opt_in": bool(people_ops_opt_in) and case_type == "grievance"})
    if case_type == "exit_dues" and last_working_day is not None:
        rec["last_working_day"] = last_working_day.isoformat()
        rec["statutory_flags"] = exit_flags(last_working_day, _today(now))
    _ref(db, rec["case_id"]).set(rec)
    return rec


def _target(rec: dict) -> dict:
    if sensitive(rec["case_type"]):
        return {"case_id": rec["case_id"], "case_type": "sensitive"}
    return {"case_id": rec["case_id"], "case_type": rec["case_type"], "queue": rec["queue"]}


def _actor(rec: dict) -> dict:
    return {"tenant_id": rec["tenant"], "case_ref": "case:" + rec["case_id"]}


def _pending(rec: dict, action: str, meta: dict) -> list[dict]:
    """The record's audit_pending with one more event, written in the same transaction as the change it records."""
    return [*(rec.get("audit_pending") or []), {"pid": secrets.token_hex(8), "action": action, "meta": meta,
                                                "claimed_at": None}]


def _flush(db, case_id: str) -> dict:
    """Write the case's pending audit events to the bucket, oldest first, and return the record. Each is claimed in a
    transaction, written, then cleared in another; a failed write gives its claim back and raises, so the next call
    that touches the case writes it. A claim older than AUDIT_LEASE (a process that died between the two) is taken
    over."""
    from shared import audit_log          # lazy: it opens google.cloud.storage
    fs, ref = _fs(), _ref(db, case_id)

    @fs.transactional
    def _claim(tx):
        snap = ref.get(transaction=tx)
        rec = (snap.to_dict() or {}) if snap.exists else {}
        pend, t = list(rec.get("audit_pending") or []), _now()
        for p in pend:
            c = p.get("claimed_at")
            if not isinstance(c, datetime) or t - c > AUDIT_LEASE:
                p["claimed_at"] = t
                tx.update(ref, {"audit_pending": pend})
                return rec, dict(p)
        return rec, None

    @fs.transactional
    def _settle(tx, pid, upd):
        snap = ref.get(transaction=tx)
        rec = (snap.to_dict() or {}) if snap.exists else {}
        pend = list(rec.get("audit_pending") or [])
        if upd is None:                   # the write failed: give the claim back
            for p in pend:
                if p.get("pid") == pid:
                    p["claimed_at"] = None
            tx.update(ref, {"audit_pending": pend})
        else:
            tx.update(ref, {**upd, "audit_pending": [p for p in pend if p.get("pid") != pid]})

    while True:
        rec, p = _claim(db.transaction())
        if p is None:
            return rec
        try:
            event = audit_log.emit(p["action"], _actor(rec), _target(rec), p["meta"])
        except Exception:
            _settle(db.transaction(), p["pid"], None)
            raise
        _settle(db.transaction(), p["pid"], {"audit_open": event} if p["action"] == "case.open" else {})


def confirm(db, case_id: str, tenant: str, requester: str, token: str, queues: dict, *, summary: str | None = None,
            people_ops_opt_in: bool | None = None, now: datetime | None = None) -> dict:
    """The person confirms their draft: it becomes an open case with their own words, and its clock starts. The same
    token again returns the same case; another token on an opened case is 409; a draft past expire_at is 410."""
    if not TOKEN.match(token or ""):
        raise CaseError(422, "token: 8 to 128 letters, digits, _ or -")
    if not ID.match(case_id or ""):
        raise CaseError(404, "no such case")
    fs, now, th, requester = _fs(), now or _now(), _sha(token), requester.lower()
    ref = _ref(db, case_id)

    @fs.transactional
    def _tx(tx):
        snap = ref.get(transaction=tx)
        rec = (snap.to_dict() or {}) if snap.exists else None
        if not rec or rec.get("tenant") != tenant or rec.get("requester") != requester:
            raise CaseError(404, "no such case")
        if rec.get("status") != "draft":
            if rec.get("token_sha256") == th:
                return rec                      # the same press again: the same case
            raise CaseError(409, f"this case is already {rec.get('status')}")
        expire = rec.get("expire_at")
        if isinstance(expire, datetime) and now > expire:
            raise CaseError(410, "this draft expired after 30 minutes: raise the case again")
        upd = {"status": "open", "opened_at": now, "status_at": now, "token_sha256": th, "expire_at": fs.DELETE_FIELD}
        if summary is not None:
            upd["summary"] = _summary(summary)
        if people_ops_opt_in is not None and rec["case_type"] == "grievance":
            upd["people_ops_opt_in"] = bool(people_ops_opt_in)
        if rec.get("last_working_day"):
            upd["statutory_flags"] = exit_flags(date.fromisoformat(rec["last_working_day"]), _today(now))
        upd["due_at"], upd["sla_basis"] = _due(rec["case_type"], rec["queue"], queues, now)
        upd["audit_pending"] = _pending(rec, "case.open", {"status": "open", "source": rec.get("source"),
                                                           "via": rec.get("via")})
        tx.update(ref, upd)
        return rec

    _tx(db.transaction())
    return _flush(db, case_id)


def open_posh(db, tenant: str, requester: str, unit: str, contacts, queues: dict, *, token: str,
              source: str = "button", via: str = "direct", now: datetime | None = None) -> dict:
    """A POSH case, opened at once: the unit and the Internal Committee members the person chose to contact, and no
    text. The client token makes a second press with it return the first case. At least one chosen member must hold
    the unit's ic_member role here, or nobody could read the case: then it is 409, and the card's contacts (the
    members, the Local Committee) are the way to reach them."""
    if posh_errors(queues):
        raise CaseError(409, "posh: this company has not set up its Internal Committee contacts yet - ask the People team")
    units = queues["posh"]["units"]
    if unit not in units:
        raise CaseError(422, f"unit {unit!r}: one of {sorted(units)}")
    members = {str(m.get("email") or "").lower() for m in units[unit]["ic"]}
    chosen = sorted({str(c).strip().lower() for c in contacts or [] if str(c).strip()})
    if not chosen:
        raise CaseError(422, "choose at least one Internal Committee member to contact")
    if not set(chosen) <= members:
        raise CaseError(422, f"not on the {unit} Internal Committee: {sorted(set(chosen) - members)}")
    if not TOKEN.match(token or ""):
        raise CaseError(422, "token: 8 to 128 letters, digits, _ or -")
    held = [roles_mod.roles_for(db, tenant, c) for c in chosen]
    if any(roles_mod.UNREAD in h for h in held):
        raise CaseError(503, "the committee's roles could not be read: try again in a minute")
    if not any(f"ic_member:{unit}" in h for h in held):
        raise CaseError(409, "none of the members you chose can receive a case here yet: contact them, or the Local "
                             "Committee, directly with the details on this card")
    now = now or _now()
    rec = _new(tenant, requester, "posh", desk_law.IC_QUEUE + unit, source, via, now)
    rec.update({"status": "open", "unit": unit, "chosen_contacts": chosen, "opened_at": now, "token_sha256": _sha(token)})
    rec["due_at"], rec["sla_basis"] = _due("posh", rec["queue"], queues, now)
    rec["audit_pending"] = _pending(rec, "case.open", {"status": "open", "source": source, "via": via})
    fs = _fs()
    claim = db.collection("case_tokens").document(_sha(f"{tenant}:{rec['requester']}:{token}"))

    @fs.transactional
    def _tx(tx):
        taken = claim.get(transaction=tx)
        if taken.exists:
            first = _ref(db, (taken.to_dict() or {}).get("case_id") or "-").get(transaction=tx)
            if not first.exists:
                raise CaseError(409, "this request was already handled")
            return (first.to_dict() or {}).get("case_id")
        tx.set(_ref(db, rec["case_id"]), rec)
        tx.set(claim, {"case_id": rec["case_id"], "tenant": tenant, "expire_at": now + TOKEN_TTL})
        return rec["case_id"]

    return _flush(db, _tx(db.transaction()))


def cancel(db, case_id: str, tenant: str, requester: str, *, now: datetime | None = None) -> dict:
    """The person withdraws their own case. A draft is deleted, with the words in it (no case existed, so no event);
    an open one becomes withdrawn and writes case.close. A withdrawn case stays withdrawn; a closed one cannot be."""
    if not ID.match(case_id or ""):
        raise CaseError(404, "no such case")
    fs, now, requester = _fs(), now or _now(), requester.lower()
    ref = _ref(db, case_id)

    @fs.transactional
    def _tx(tx):
        snap = ref.get(transaction=tx)
        rec = (snap.to_dict() or {}) if snap.exists else None
        if not rec or rec.get("tenant") != tenant or rec.get("requester") != requester:
            raise CaseError(404, "no such case")
        if rec["status"] == "draft":
            tx.delete(ref)
            return {**rec, "status": "withdrawn", "status_at": now}, False
        if rec["status"] == "withdrawn":
            return rec, True
        if rec["status"] == "closed":
            raise CaseError(409, "this case is closed")
        upd = {"status": "withdrawn", "status_at": now,
               "audit_pending": _pending(rec, "case.close", {"status": "withdrawn", "from": rec["status"],
                                                             "by": "requester"})}
        tx.update(ref, upd)
        return {**rec, **upd}, True

    rec, kept = _tx(db.transaction())
    return _flush(db, case_id) if kept else rec


def set_status(db, case_id: str, tenant: str, email: str, roles, status: str, *, now: datetime | None = None) -> dict:
    """The queue moves a case along. 404 for anyone who may not read it, 403 for a reader who is not the queue (the
    person who raised it), 409 for a move the status does not allow. The same status again changes nothing."""
    if status not in ("acknowledged", "in_progress", "resolved", "closed"):
        raise CaseError(422, f"status {status!r}: acknowledged, in_progress, resolved or closed")
    if not ID.match(case_id or ""):
        raise CaseError(404, "no such case")
    fs, now = _fs(), now or _now()
    ref = _ref(db, case_id)

    @fs.transactional
    def _tx(tx):
        snap = ref.get(transaction=tx)
        rec = (snap.to_dict() or {}) if snap.exists else None
        if not rec or rec.get("tenant") != tenant:
            raise CaseError(404, "no such case")
        reads, moves = access(rec, email, roles)
        if not reads:
            raise CaseError(404, "no such case")
        if not moves:
            raise CaseError(403, "only the case's queue changes its status")
        was = rec["status"]
        if status == was:
            return
        if status not in NEXT.get(was, ()):
            raise CaseError(409, f"a {was} case cannot become {status}")
        upd = {"status": status, "status_at": now,
               "audit_pending": _pending(rec, "case.close" if status == "closed" else "case.update",
                                         {"status": status, "from": was, "by": "queue"})}
        if was == "open":
            upd["acknowledged_at"] = now
        tx.update(ref, upd)

    _tx(db.transaction())
    return _flush(db, case_id)
