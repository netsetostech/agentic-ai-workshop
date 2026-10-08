"""Offline checks for the DocuMind Desk's case queue, its roles and the chat door (workshop lesson 5.6).

    python -m unittest commands/tests/test_cases.py -v                         # from deploy/
    DOCUMIND_REQUIRE_LIBS=1 python -m unittest commands/tests/test_cases.py     # CI's chat-pins step, make desk-check

The first half needs only the standard library. shared/roles.py and shared/cases.py run against a fake Firestore and
a fake audit bucket: a member with no role document is an employee, a leaver is not, a failed read leaves the case desk
only; every grant and revoke is an event; a draft expires (410), a confirm with one token is one case, another token
is 409; another tenant and a stranger get 404; a POSH case holds no text and one token opens one; the inbox, the
overdue states, the exit-dues flag and the queue files; the case table against the corpus's own lines and the
manifest's URLs; an audit actor is a case reference, never an email; the wiring in Terraform, the deploy script and
the Makefile; and commands/desk_ops.py's roles, queues, cases and its refusal to turn desk_route on or single without
a complete POSH queue (the gate needs none).

The second half runs services/chat/desk.py and needs the chat image's pins (pip install -r
services/chat/requirements.txt): the chat door against a fake app (the bytes replayed when the gate is off, the rules
for a tenant that set nothing and for the local profile's LOCAL_TENANT with no setting read, an Aadhaar number masked
unless the gate is off, the model check for a tenant whose gate is on, the 64 KiB cap), the real chat
service (a refused caller gets the same bytes whether or not the question hit the gate; a gated turn calls no model and
writes no checkpoint), and the case routes end to end. Without the pins it is skipped and says so; with
DOCUMIND_REQUIRE_LIBS=1 a missing pin is an error instead.
"""
import asyncio
import contextlib
import copy
import importlib.util
import io
import json
import logging
import os
import re
import sys
import types
import unittest
import warnings
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[2]
for p in (str(KIT / "services/chat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from shared import cases, desk_law, desk_recall, desk_rules, identifiers, roles  # noqa: E402

FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "google.adk", "fastapi"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
T0 = datetime(2026, 9, 28, 9, 0, tzinfo=timezone.utc)                  # a Monday
ME, GRC, HR, PAY, PRIV, OTHER = ("you@example.com", "grc@example.com", "hr@example.com", "pay@example.com",
                                 "dpo@example.com", "colleague@example.com")
POSH = "My manager keeps making sexual comments about my body. What can I do?"
PLAIN = "How many days of earned leave can I carry forward?"
MISS = "He grabbed my hand in the lift yesterday and I keep thinking about it"   # no pattern catches it; the model check may


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


desk_ops = _load("desk_ops_for_cases", KIT / "commands" / "desk_ops.py")
desk_overdue = _load("desk_overdue_under_test", KIT / "services" / "chat" / "desk_overdue.py")


def queues_file(tenant: str) -> dict:
    return desk_ops._notes_off(json.loads((KIT / "evals" / "desk" / f"queues.{tenant}.json").read_text(encoding="utf-8")))


# ------------------------------------------------------------------ a fake Firestore, enough for the case queue
DELETE = object()


class Snap:
    def __init__(self, id_, data):
        self.id, self._d, self.exists = id_, data, data is not None

    def to_dict(self):
        return copy.deepcopy(self._d)


class Ref:
    def __init__(self, db, path):
        self.db, self.path, self.id = db, path, path.rsplit("/", 1)[-1]

    def get(self, transaction=None):
        if self.db.fail_reads:
            raise RuntimeError("firestore is unwell")
        return Snap(self.id, copy.deepcopy(self.db.docs.get(self.path)))

    def set(self, data, merge=False):
        data = copy.deepcopy(data)
        if merge is True and self.path in self.db.docs:
            self.db.docs[self.path].update(data)
        elif isinstance(merge, list) and self.path in self.db.docs:
            self.db.docs[self.path].update({k: data[k] for k in merge})
        else:
            self.db.docs[self.path] = data
        self.db.writes.append((self.path, data, merge))

    def update(self, data):
        if self.path not in self.db.docs:
            raise KeyError(f"no document to update: {self.path}")
        doc = self.db.docs[self.path]
        for k, v in copy.copy(data).items():
            if v is DELETE:
                doc.pop(k, None)
            else:
                doc[k] = copy.deepcopy(v)

    def delete(self):
        self.db.docs.pop(self.path, None)

    def collection(self, name):
        return Query(self.db, f"{self.path}/{name}")


class Query:
    def __init__(self, db, path, filters=(), order=(), lim=None):
        self.db, self.path, self.filters, self.order, self.lim = db, path, filters, order, lim

    def document(self, id_):
        return Ref(self.db, f"{self.path}/{id_}")

    def where(self, field, op, value):
        return Query(self.db, self.path, self.filters + ((field, op, value),), self.order, self.lim)

    def order_by(self, field, direction="ASCENDING"):
        return Query(self.db, self.path, self.filters, self.order + ((field, direction),), self.lim)

    def limit(self, n):
        return Query(self.db, self.path, self.filters, self.order, n)

    def stream(self, **kw):                        # retry= and timeout=, as shared/desk_recall reads, are taken
        if self.db.fail_reads:
            raise RuntimeError("firestore is unwell")
        self.db.queries.append((self.path, self.filters, self.order))
        rows = []
        for path, doc in self.db.docs.items():
            head, _, id_ = path.rpartition("/")
            if head != self.path:
                continue
            ok = True
            for field, op, value in self.filters:
                v = doc.get(field)
                ok = ok and ((op == "==" and v == value) or (op == "in" and v in value) or
                             (op == "<=" and v is not None and v <= value) or
                             (op == "array_contains" and isinstance(v, list) and value in v))
            if ok:
                rows.append(Snap(id_, copy.deepcopy(doc)))
        for field, direction in reversed(self.order):
            rows.sort(key=lambda s: (s._d.get(field) is not None, s._d.get(field) or 0), reverse=direction == "DESCENDING")
        return iter(rows[: self.lim] if self.lim else rows)


class Tx:
    def __init__(self, db):
        self.db, self.ops = db, []

    def set(self, ref, data, merge=False):
        self.ops.append(("set", ref, data))

    def update(self, ref, data):
        self.ops.append(("update", ref, data))

    def delete(self, ref):
        self.ops.append(("delete", ref, None))


class FakeDB:
    def __init__(self):
        self.docs, self.writes, self.queries, self.fail_reads = {}, [], [], False

    def collection(self, name):
        return Query(self, name)

    def transaction(self):
        return Tx(self)

    def cases(self):
        return {p.split("/", 1)[1]: d for p, d in self.docs.items() if p.startswith("cases/")}


def _transactional(fn):
    def run(tx, *args, **kwargs):
        out = fn(tx, *args, **kwargs)     # a CaseError raised here commits nothing
        for op, ref, data in tx.ops:
            getattr(ref, op)(*(() if op == "delete" else (data,)))
        return out
    return run


FS = types.SimpleNamespace(transactional=_transactional, DELETE_FIELD=DELETE, SERVER_TIMESTAMP="SERVER_TIMESTAMP",
                           Client=None)


# ------------------------------------------------------------------ a fake audit bucket
def _audit_module():
    """shared.audit_log, imported with a stand-in google.cloud.storage when the real one is missing."""
    try:
        from shared import audit_log
        return audit_log
    except ImportError:
        pass
    fake = types.ModuleType("google.cloud.storage")
    mods = {"google.cloud.storage": fake}
    try:
        import google.cloud  # noqa: F401
    except ImportError:
        g, gc = types.ModuleType("google"), types.ModuleType("google.cloud")
        g.__path__, gc.__path__, g.cloud, gc.storage = [], [], gc, fake
        mods.update({"google": g, "google.cloud": gc})
    with patch.dict(sys.modules, mods):
        sys.modules.pop("shared.audit_log", None)
        from shared import audit_log
    sys.modules["shared.audit_log"] = audit_log
    return audit_log


audit_log = _audit_module()


def _storage(events):
    class Blob:
        def __init__(self, name):
            self.name = name

        def upload_from_string(self, data, content_type=None):
            events.append(json.loads(data))

    bucket = types.SimpleNamespace(blob=Blob)
    return types.SimpleNamespace(Client=lambda *a, **k: types.SimpleNamespace(bucket=lambda name: bucket))


@contextlib.contextmanager
def cloud_modules(**mods):
    """google.cloud.<name> stand-ins for code that imports them where it uses them (desk_ops.py)."""
    entries = {f"google.cloud.{k}": v for k, v in mods.items()}
    with contextlib.ExitStack() as stack:
        try:
            import google.cloud as gc
            stack.enter_context(patch.dict(sys.modules, entries))
            for k, v in mods.items():
                stack.enter_context(patch.object(gc, k, v, create=True))
        except ImportError:
            g, gc = types.ModuleType("google"), types.ModuleType("google.cloud")
            g.__path__, gc.__path__, g.cloud = [], [], gc
            for k, v in mods.items():
                setattr(gc, k, v)
            stack.enter_context(patch.dict(sys.modules, {"google": g, "google.cloud": gc, **entries}))
        yield


class Lane(unittest.TestCase):
    """A fake database with acme's queues and people, and a fake audit bucket that keeps every event."""

    def setUp(self):
        self.db, self.events = FakeDB(), []
        self.queues = queues_file("acme")
        for p in (patch.object(cases, "_fs", lambda: FS), patch.object(audit_log, "storage", _storage(self.events)),
                  patch.object(audit_log, "_bucket", None),
                  patch.dict(os.environ, {"AUDIT_BUCKET": "documind-ai-YOUR-ID-audit"})):
            p.start()
            self.addCleanup(p.stop)
        for t, people in (("acme", (ME, GRC, HR, PAY, PRIV, OTHER)), ("zeta", ("z@example.com",))):
            for e in people:
                self.db.collection("tenants").document(t).collection("members").document(e).set({"email": e})
        for e, held in ((GRC, ["employee", "grc_member"]), (HR, ["employee", "people_ops"]), (PAY, ["payroll"]),
                        (PRIV, ["privacy"]), (ME, ["employee", "ic_member:hyderabad"])):
            roles.role_ref(self.db, "acme", e).set({"roles": held})

    def roles(self, email, tenant="acme"):
        return roles.roles_for(self.db, tenant, email)

    def opened(self, case_type="grievance", who=ME, token="press-0001", now=T0, **kw):
        d = cases.draft(self.db, "acme", who, case_type, self.queues, summary="my words", now=now, **kw)
        return cases.confirm(self.db, d["case_id"], "acme", who, token, self.queues, now=now)

    def actions(self):
        return [e["action"] for e in self.events]


# ------------------------------------------------------------------ roles
class RolesTests(Lane):
    def test_who_holds_what(self):
        self.assertEqual(self.roles(OTHER), ["employee"])                      # no document: an employee
        roles.role_ref(self.db, "acme", OTHER).set({"roles": ["leaver"]})
        self.assertEqual(self.roles(OTHER), ["leaver"])                        # a document lists every role it grants
        self.assertEqual(roles.desks(self.roles(OTHER)), {"case"})
        self.assertEqual(self.roles("nobody@example.com"), [])                 # on no roster: no role at all
        self.assertEqual(self.roles(ME, "zeta"), [])                           # another tenant's member is not one here
        self.db.fail_reads = True
        self.assertEqual(self.roles(OTHER), [roles.UNREAD])                    # a failed read: the case desk only
        self.assertEqual(roles.desks([roles.UNREAD]), {"case"})
        self.assertEqual(roles.desks(["employee"]), set(roles.ANSWER_DESKS) | {"case"})
        self.assertEqual(roles.desks(["people_ops"]), set())
        self.assertEqual(roles.ic_units(["ic_member:pune", "employee", "ic_member:Pune"]), {"pune"})
        self.assertTrue(roles.valid("desk_reviewer") and not roles.valid("admin") and not roles.valid("ic_member:"))

    def test_every_grant_and_revoke_is_an_event(self):
        out = roles.set_roles(self.db, "acme", OTHER, ["employee", "grc_member"], by=HR)
        self.assertEqual((out["before"], out["granted"], out["revoked"]), (["employee"], ["grc_member"], []))
        out = roles.revoke(self.db, "acme", OTHER, ["grc_member"], by=HR)
        self.assertEqual((out["after"], out["revoked"]), (["employee"], ["grc_member"]))
        roles.set_roles(self.db, "acme", OTHER, ["leaver"], by=HR)
        out = roles.revoke(self.db, "acme", OTHER, "all", by=HR)
        self.assertEqual((out["after"], self.roles(OTHER)), (["employee"], ["employee"]))
        self.assertNotIn("tenants/acme/roles/" + OTHER, self.db.docs)          # back to no document
        # employee is held without a document, so leaving it is a revoke and coming back to it a grant
        self.assertEqual(self.actions(), ["role.grant", "role.revoke", "role.grant", "role.revoke", "role.grant",
                                          "role.revoke"])
        self.assertEqual(self.events[0]["actor"], {"tenant_id": "acme", "email": HR})
        self.assertEqual(self.events[0]["target"], {"email": OTHER, "roles": ["grc_member"]})
        with self.assertRaises(PermissionError):
            roles.set_roles(self.db, "acme", "nobody@example.com", ["employee"], by=HR)
        with self.assertRaises(ValueError):
            roles.set_roles(self.db, "acme", OTHER, ["admin"], by=HR)
        self.assertEqual(len(self.events), 6)                                   # a refusal writes nothing


# ------------------------------------------------------------------ cases
class CaseTests(Lane):
    def test_a_draft_then_one_case_per_token(self):
        d = cases.draft(self.db, "acme", ME, "grievance", self.queues, summary="my words", now=T0)
        self.assertEqual((d["status"], d["queue"], d["source"], d["via"], d["expire_at"]),
                         ("draft", "grc", "button", "direct", T0 + timedelta(minutes=30)))
        self.assertRegex(d["case_id"], r"^[0-9a-f]{32}$")
        self.assertEqual(self.events, [])                                       # a draft is no case yet
        first = cases.confirm(self.db, d["case_id"], "acme", ME, "press-0001", self.queues, now=T0 + timedelta(minutes=5))
        stored = self.db.cases()[d["case_id"]]
        self.assertEqual((stored["status"], stored["summary"]), ("open", "my words"))
        self.assertNotIn("expire_at", stored)                                   # a record, not a draft: no TTL
        self.assertEqual(stored["due_at"], T0 + timedelta(minutes=5, days=15))
        self.assertEqual(stored["sla_basis"], "the company's own target: 15 days (case_queues.grc.sla_days)")
        again = cases.confirm(self.db, d["case_id"], "acme", ME, "press-0001", self.queues, now=T0 + timedelta(minutes=9))
        self.assertEqual((again["case_id"], again["opened_at"]), (first["case_id"], first["opened_at"]))
        self.assertEqual(self.actions(), ["case.open"])                         # the same press again: no second event
        with self.assertRaises(cases.CaseError) as e:
            cases.confirm(self.db, d["case_id"], "acme", ME, "press-0002", self.queues)
        self.assertEqual(e.exception.status, 409)
        self.assertEqual(len(self.db.cases()), 1)

    def test_an_expired_draft_is_410(self):
        d = cases.draft(self.db, "acme", ME, "exit_dues", self.queues, now=T0)
        with self.assertRaises(cases.CaseError) as e:
            cases.confirm(self.db, d["case_id"], "acme", ME, "press-0001", self.queues, now=T0 + timedelta(minutes=31))
        self.assertEqual(e.exception.status, 410)
        self.assertEqual(self.db.cases()[d["case_id"]]["status"], "draft")
        self.assertEqual(self.events, [])

    def test_nobody_else_can_tell_a_case_exists(self):
        d = cases.draft(self.db, "acme", ME, "grievance", self.queues, now=T0)
        for tenant, who in (("acme", GRC), ("zeta", ME)):                      # a draft is the requester's alone
            with self.assertRaises(cases.CaseError) as e:
                cases.read(self.db, d["case_id"], tenant, who, self.roles(who))
            self.assertEqual(e.exception.status, 404)
        case = cases.confirm(self.db, d["case_id"], "acme", ME, "press-0001", self.queues, now=T0)
        self.assertEqual(cases.read(self.db, case["case_id"], "acme", GRC, self.roles(GRC))["case_id"], case["case_id"])
        self.assertEqual(cases.read(self.db, case["case_id"], "acme", ME, self.roles(ME))["case_id"], case["case_id"])
        for tenant, who in (("zeta", "z@example.com"), ("acme", OTHER), ("acme", HR), ("acme", PAY)):
            with self.assertRaises(cases.CaseError) as e:
                cases.read(self.db, case["case_id"], tenant, who, self.roles(who, tenant))
            self.assertEqual(e.exception.status, 404, who)
        for bad in ("../tenants", "A" * 32, ""):
            with self.assertRaises(cases.CaseError):
                cases.read(self.db, bad, "acme", ME, ["employee"])
        with self.assertRaises(cases.CaseError) as e:                          # the person who raised it is not its queue
            cases.set_status(self.db, case["case_id"], "acme", ME, self.roles(ME), "resolved")
        self.assertEqual(e.exception.status, 403)
        with self.assertRaises(cases.CaseError) as e:
            cases.set_status(self.db, case["case_id"], "acme", OTHER, self.roles(OTHER), "resolved")
        self.assertEqual(e.exception.status, 404)
        cases.set_status(self.db, case["case_id"], "acme", GRC, self.roles(GRC), "acknowledged", now=T0)
        cases.set_status(self.db, case["case_id"], "acme", GRC, self.roles(GRC), "acknowledged", now=T0)   # no change
        cases.set_status(self.db, case["case_id"], "acme", GRC, self.roles(GRC), "closed", now=T0)
        with self.assertRaises(cases.CaseError) as e:
            cases.set_status(self.db, case["case_id"], "acme", GRC, self.roles(GRC), "in_progress")
        self.assertEqual(e.exception.status, 409)
        self.assertEqual(self.actions(), ["case.open", "case.update", "case.close"])
        self.assertEqual(self.db.cases()[case["case_id"]]["acknowledged_at"], T0)

    def test_a_posh_case_holds_no_text_and_one_press_opens_one(self):
        with self.assertRaises(cases.CaseError):                                # posh has no draft
            cases.draft(self.db, "acme", ME, "posh", self.queues)
        one = cases.open_posh(self.db, "acme", OTHER, "hyderabad", [ME], self.queues, token="press-0001", now=T0)
        two = cases.open_posh(self.db, "acme", OTHER, "hyderabad", [ME], self.queues, token="press-0001", now=T0)
        self.assertEqual(one["case_id"], two["case_id"])
        self.assertEqual(len(self.db.cases()), 1)
        rec = self.db.cases()[one["case_id"]]
        self.assertEqual((rec["status"], rec["queue"], rec["unit"], rec["chosen_contacts"]),
                         ("open", "ic:hyderabad", "hyderabad", [ME]))
        self.assertEqual((rec["summary"], rec["route_trace"], rec["question_sha256"], rec["partial_answer_citations"]),
                         (None, None, None, []))
        texts = {k: v for k, v in rec.items() if isinstance(v, str)}
        self.assertEqual(sorted(texts), ["audit_open", "case_id", "case_type", "queue", "requester", "sla_basis", "source",
                                         "status", "tenant", "token_sha256", "unit", "via"])
        self.assertEqual(rec["audit_pending"], [])                               # written, and cleared
        self.assertEqual(self.actions(), ["case.open"])
        self.assertEqual(self.events[0]["target"], {"case_id": one["case_id"], "case_type": "sensitive"})
        self.assertNotIn("hyderabad", json.dumps(self.events))
        # only the chosen members of that unit read it; the Local Committee is always named
        self.assertTrue(cases.access(rec, ME, self.roles(ME))[0])
        self.assertFalse(cases.access(rec, "ic.hyderabad.member@example.com", ["ic_member:hyderabad"])[0])
        self.assertFalse(cases.access(rec, ME, ["employee"])[0])
        self.assertEqual(cases.owner(rec, self.queues)["local_committee"]["contact"], "lc.hyderabad@example.com")
        for unit, chosen, token, status in (("hyderabad", ["lc.pune@example.com"], "press-0002", 422),
                                            ("chennai", [ME], "press-0002", 422), ("hyderabad", [], "press-0002", 422),
                                            ("hyderabad", [ME], "", 422), ("hyderabad", [ME], None, 422)):
            with self.assertRaises(cases.CaseError) as e:
                cases.open_posh(self.db, "acme", OTHER, unit, chosen, self.queues, token=token)
            self.assertEqual(e.exception.status, status)
        broken = copy.deepcopy(self.queues)
        del broken["posh"]["units"]["pune"]["local_committee"]
        with self.assertRaises(cases.CaseError) as e:
            cases.open_posh(self.db, "acme", OTHER, "hyderabad", [ME], broken, token="press-0002")
        self.assertEqual(e.exception.status, 409)
        self.assertEqual(len(self.db.cases()), 1)

    def test_a_posh_case_goes_only_to_a_member_who_can_read_it(self):
        member = "ic.hyderabad.member@example.com"                              # listed, but on no roster here
        with self.assertRaises(cases.CaseError) as e:
            cases.open_posh(self.db, "acme", OTHER, "hyderabad", [member], self.queues, token="press-0001")
        self.assertEqual(e.exception.status, 409)
        self.assertIn("Local Committee", e.exception.detail)
        self.assertEqual(self.db.cases(), {})
        both = cases.open_posh(self.db, "acme", OTHER, "hyderabad", [member, ME], self.queues, token="press-0002")
        self.assertEqual(both["chosen_contacts"], sorted([member, ME]))         # one reader is enough
        with patch.object(roles, "roles_for", lambda db, t, e: [roles.UNREAD]):
            with self.assertRaises(cases.CaseError) as e:
                cases.open_posh(self.db, "acme", OTHER, "hyderabad", [ME], self.queues, token="press-0003")
        self.assertEqual(e.exception.status, 503)
        gaps = cases.reader_gaps(self.db, "acme", self.queues)
        self.assertEqual(gaps["posh_units"], ["pune"])                           # nobody here holds ic_member:pune
        self.assertIn(f"hyderabad: {member}", gaps["ic"])
        self.assertEqual(gaps["queues"], [])
        # an IC member's inbox asks only for the cases that name them
        theirs = cases.list_for(self.db, "acme", ME, self.roles(ME))
        self.assertEqual([c["case_id"] for c in theirs["inbox"]], [both["case_id"]])
        self.assertIn(("chosen_contacts", "array_contains", ME), self.db.queries[-3][1])

    def test_the_inbox_is_the_readers_queues(self):
        g = self.opened("grievance", token="press-0001")
        x = self.opened("exit_dues", token="press-0002")
        p = self.opened("privacy_request", token="press-0003")
        shared = cases.draft(self.db, "acme", OTHER, "grievance", self.queues, people_ops_opt_in=True, now=T0)
        shared = cases.confirm(self.db, shared["case_id"], "acme", OTHER, "press-0004", self.queues, now=T0)

        def inbox(who):
            return {c["case_id"] for c in cases.list_for(self.db, "acme", who, self.roles(who))["inbox"]}

        self.assertEqual(inbox(GRC), {g["case_id"], shared["case_id"]})
        self.assertEqual(inbox(HR), {x["case_id"], shared["case_id"]})         # payroll's queue, and the shared grievance
        self.assertEqual(inbox(PAY), {x["case_id"]})
        self.assertEqual(inbox(PRIV), {p["case_id"]})
        self.assertEqual(inbox(OTHER), set())
        mine = cases.list_for(self.db, "acme", ME, self.roles(ME))["mine"]
        self.assertEqual({c["case_id"] for c in mine}, {g["case_id"], x["case_id"], p["case_id"]})
        self.assertEqual(cases.list_for(self.db, "zeta", "z@example.com", ["employee"]),
                         {"inbox": [], "mine": [], "more": False})

    def test_finished_cases_never_hide_an_open_one(self):
        old = self.opened("grievance", token="press-0000", now=T0 - timedelta(days=40))       # breached, still open
        for i in range(cases.LIMIT + 3):
            c = self.opened("grievance", token=f"press-{i + 1:04d}", now=T0 - timedelta(days=1, minutes=-i))
            cases.set_status(self.db, c["case_id"], "acme", GRC, self.roles(GRC), "closed", now=T0)
        got = cases.list_for(self.db, "acme", GRC, self.roles(GRC))
        self.assertEqual(got["inbox"][0]["case_id"], old["case_id"])             # active first
        self.assertEqual(len(got["inbox"]), 1 + cases.LIMIT)
        self.assertTrue(got["more"])

    def test_a_withdrawn_draft_is_gone(self):
        d = cases.draft(self.db, "acme", ME, "grievance", self.queues, summary="my manager shouted at me", now=T0)
        out = cases.cancel(self.db, d["case_id"], "acme", ME, now=T0)
        self.assertEqual(out["status"], "withdrawn")
        self.assertEqual(self.db.cases(), {})                                    # the record and its words are deleted
        with self.assertRaises(cases.CaseError) as e:
            cases.read(self.db, d["case_id"], "acme", GRC, self.roles(GRC))
        self.assertEqual(e.exception.status, 404)
        self.assertEqual(cases.list_for(self.db, "acme", GRC, self.roles(GRC))["inbox"], [])
        self.assertEqual(self.events, [])
        with self.assertRaises(cases.CaseError) as e:
            cases.cancel(self.db, d["case_id"], "acme", ME)
        self.assertEqual(e.exception.status, 404)
        # a record that was never opened is the requester's alone, whatever its status says
        never = {"tenant": "acme", "requester": ME, "case_type": "grievance", "queue": "grc", "status": "withdrawn",
                 "opened_at": None}
        self.assertEqual((cases.access(never, GRC, ["grc_member"]), cases.access(never, ME, ["employee"])),
                         ((False, False), (True, False)))

    def test_an_audit_event_survives_a_failed_write(self):
        c = self.opened("grievance", token="press-0001")
        real = audit_log.emit
        with patch.object(audit_log, "emit", side_effect=RuntimeError("bucket unwell")):
            with self.assertRaises(RuntimeError):
                cases.set_status(self.db, c["case_id"], "acme", GRC, self.roles(GRC), "closed", now=T0)
        rec = self.db.cases()[c["case_id"]]
        self.assertEqual((rec["status"], [p["action"] for p in rec["audit_pending"]], rec["audit_pending"][0]["claimed_at"]),
                         ("closed", ["case.close"], None))                       # kept, and its claim given back
        self.assertIs(audit_log.emit, real)
        cases.set_status(self.db, c["case_id"], "acme", GRC, self.roles(GRC), "closed", now=T0)   # the retry writes it
        self.assertEqual(self.actions(), ["case.open", "case.close"])
        self.assertEqual(self.db.cases()[c["case_id"]]["audit_pending"], [])
        cases.set_status(self.db, c["case_id"], "acme", GRC, self.roles(GRC), "closed", now=T0)
        self.assertEqual(self.actions(), ["case.open", "case.close"])            # once, not twice
        # a confirm whose event failed: the same press writes it, once
        d = cases.draft(self.db, "acme", ME, "exit_dues", self.queues, now=T0)
        with patch.object(audit_log, "emit", side_effect=RuntimeError("bucket unwell")):
            with self.assertRaises(RuntimeError):
                cases.confirm(self.db, d["case_id"], "acme", ME, "press-0002", self.queues, now=T0)
        again = cases.confirm(self.db, d["case_id"], "acme", ME, "press-0002", self.queues, now=T0)
        self.assertEqual((again["status"], self.actions()[-1], self.actions().count("case.open")), ("open", "case.open", 2))
        self.assertTrue(again["audit_open"])
        # a claim another process holds is left to it until AUDIT_LEASE has passed
        held = {"pid": "x1", "action": "case.update", "meta": {"status": "acknowledged"}, "claimed_at": cases._now()}
        self.db.docs[f"cases/{d['case_id']}"]["audit_pending"] = [held]
        cases.cancel(self.db, d["case_id"], "acme", ME)
        self.assertEqual(self.actions()[-1], "case.close")
        self.assertEqual([p["pid"] for p in self.db.cases()[d["case_id"]]["audit_pending"]], ["x1"])
        self.db.docs[f"cases/{d['case_id']}"]["audit_pending"][0]["claimed_at"] = cases._now() - cases.AUDIT_LEASE * 2
        cases.cancel(self.db, d["case_id"], "acme", ME)
        self.assertEqual((self.actions()[-1], self.db.cases()[d["case_id"]]["audit_pending"]), ("case.update", []))

    def test_due_and_breached(self):
        soon = self.opened("exit_dues", token="press-0001", now=T0 - timedelta(days=2) + timedelta(hours=3))   # due in 3 h
        late = self.opened("human_requested", token="press-0002", now=T0 - timedelta(days=6))                 # 1 day late
        calm = self.opened("people_query", token="press-0003", now=T0)                                         # 5 days left
        acked = self.opened("exit_dues", token="press-0004", now=T0 - timedelta(days=2) + timedelta(hours=3))
        grave = self.opened("grievance", token="press-0005", now=T0 - timedelta(days=16))                       # 1 day late
        cases.set_status(self.db, acked["case_id"], "acme", PAY, self.roles(PAY), "acknowledged", now=T0)
        self.assertEqual(cases.tenant_cases(self.db, "acme", T0)[0]["case_id"], late["case_id"])   # soonest due first
        logs = []
        with patch.object(desk_overdue.log, "info", side_effect=lambda line: logs.append(json.loads(line))):
            rows = desk_overdue.scan(self.db, T0)
        self.assertEqual({r["case_id"]: r["state"] for r in rows},
                         {soon["case_id"]: "due", late["case_id"]: "breached", grave["case_id"]: "breached"})
        self.assertEqual({r["case_id"]: r["queue"] for r in rows}[grave["case_id"]], "sensitive")   # not grc
        self.assertNotIn(calm["case_id"], json.dumps(logs))
        self.assertNotIn(acked["case_id"], json.dumps(logs))                     # acknowledged and not yet late
        for line in logs[:-1]:
            self.assertEqual(sorted(line), ["case_id", "due_at", "event", "queue", "state"])
        self.assertEqual(logs[-1], {"event": "case_overdue_scan", "due": 1, "breached": 2})
        self.assertNotIn('"grc"', json.dumps(logs))

    def test_the_overdue_job_loads_where_the_image_puts_it(self):
        import shutil
        import tempfile
        here = Path(tempfile.mkdtemp())                                          # /app: one level, no services/ above
        self.addCleanup(shutil.rmtree, here)
        shutil.copy(KIT / "services" / "chat" / "desk_overdue.py", here / "desk_overdue.py")
        mod = _load("desk_overdue_in_the_image", here / "desk_overdue.py")
        self.assertEqual(mod.KIT, here)
        self.assertEqual(desk_overdue.KIT, KIT)

    def test_exit_dues_may_have_passed(self):
        friday = date(2026, 9, 25)
        self.assertEqual(cases.working_days_after(friday, 2), date(2026, 9, 29))
        self.assertEqual(cases.exit_flags(friday, date(2026, 9, 29)), [])
        self.assertEqual(cases.exit_flags(friday, date(2026, 9, 30)), [cases.EXIT_LATE])
        d = cases.draft(self.db, "acme", ME, "exit_dues", self.queues, last_working_day=friday,
                        now=datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc))
        self.assertEqual(d["statutory_flags"], [cases.EXIT_LATE])
        late_night = datetime(2026, 9, 29, 20, 0, tzinfo=timezone.utc)          # 01:30 on 30 September in India
        d2 = cases.draft(self.db, "acme", ME, "exit_dues", self.queues, last_working_day=friday, now=late_night)
        self.assertEqual(d2["statutory_flags"], [cases.EXIT_LATE])
        view = cases.view(d, self.queues)
        self.assertIn(desk_law.CLOCKS["exit_dues_late"], view["clock"])
        self.assertEqual([b["section"] for b in view["basis"]], ["s.17(2)", "s.32(1)(vi)", "s.56(3)"])

    def test_the_queue_files_and_where_a_case_goes(self):
        for t in ("acme", "zeta", "globex"):
            cfg = queues_file(t)
            self.assertEqual((cases.queue_errors(cfg), cases.posh_errors(cfg)), ([], []), t)
            self.assertNotRegex(json.dumps(cfg), r"@(?!example\.com)", "placeholder contacts only")
        self.assertEqual(sorted(queues_file("acme")["posh"]["units"]), ["hyderabad", "pune"])   # townhall_2026_q1.md:7
        broken = copy.deepcopy(self.queues)
        del broken["posh"]["units"]["pune"]["local_committee"]
        broken["posh"]["units"]["hyderabad"]["ic"][0].pop("email")
        broken["clause_prefixes"]["pr"] = "payroll"
        broken["grc"]["sla_days"] = 0
        broken["helpdesk"] = {}
        errs = cases.queue_errors(broken)
        self.assertEqual(len(errs), 5, errs)
        self.assertEqual(cases.posh_errors({}), ["posh: no POSH section - every unit's Internal Committee and its "
                                                 "Local Committee contact"])
        self.assertEqual(cases.queue_for("people_query", self.queues, clause="PR-05"), "payroll")
        self.assertEqual(cases.queue_for("people_query", self.queues, clause="LV-07"), "people")
        no_privacy = {k: v for k, v in self.queues.items() if k != "privacy"}
        self.assertEqual(cases.queue_for("privacy_request", no_privacy), "people")     # the type is kept
        with self.assertRaises(cases.CaseError) as e:
            cases.draft(self.db, "acme", ME, "grievance", {k: v for k, v in self.queues.items() if k != "grc"})
        self.assertEqual(e.exception.status, 409)
        accepted = copy.deepcopy(self.queues)
        accepted["grc"]["accepts_desk_case"] = True
        self.assertEqual(cases._due("grievance", "grc", accepted, T0),
                         (T0 + timedelta(days=30), "Industrial Relations Code, 2020, s.4(6): the committee may complete within 30 days"))
        self.assertEqual(cases.clock({"case_type": "grievance", "queue": "grc"}, accepted),
                         [desk_law.CLOCKS["grievance_accepted"]])

    def test_the_audit_actor_is_a_case_reference(self):
        self.opened("grievance", token="press-0001")
        self.opened("exit_dues", token="press-0002")
        case = cases.open_posh(self.db, "acme", ME, "hyderabad", [ME], self.queues, token="press-0003")
        cases.cancel(self.db, case["case_id"], "acme", ME)
        self.assertEqual(self.actions(), ["case.open", "case.open", "case.open", "case.close"])
        for e in self.events:
            self.assertEqual(sorted(e["actor"]), ["case_ref", "tenant_id"])
            self.assertTrue(e["actor"]["case_ref"].startswith("case:"))
            self.assertNotIn("@", json.dumps(e))
        self.assertEqual(self.events[1]["target"]["queue"], "payroll")         # not sensitive: its queue is named
        d = cases.draft(self.db, "acme", ME, "people_query", self.queues)
        cases.cancel(self.db, d["case_id"], "acme", ME)                          # a draft withdrawn quietly
        self.assertEqual(len(self.events), 4)
        self.assertNotIn("hyderabad", json.dumps(self.events))


# ------------------------------------------------------------------ the case table against the corpus
class LawTests(unittest.TestCase):
    def corpus(self, name):
        return (KIT / "evals" / "corpus" / "acme" / name).read_text(encoding="utf-8").split("\n")

    def test_every_basis_is_the_corpus_own_text(self):
        phrases = {"ir_s4_1": "twenty or more workers", "ir_s4_5": "within one year", "ir_s4_6": "within thirty days",
                   "dpdp_s8_9": "Data Protection Officer", "dpdp_s13_2": "within such period as may be prescribed",
                   "wages_s17_2": "within two working days", "osh_s32_1_vi": "second working day",
                   "css_s56_3": "within thirty days"}
        manifest = {(r["slug"], r.get("source_url")) for r in json.loads((KIT / "evals" / "manifest.json").read_text(encoding="utf-8"))}
        for slug, url in desk_law.URLS.items():
            self.assertIn((slug, url), manifest, slug)
        for key, b in desk_law.BASIS.items():
            if b["lines"] is None:
                self.assertEqual((key, b["section"], b["file"]), ("posh_act", None, "posh_act_2013.pdf"))
                continue
            first, last = map(int, b["lines"].split("-"))
            lines = self.corpus(b["file"])
            text = " ".join(lines[first - 1:last])
            self.assertIn(phrases[key], re.sub(r"\s+", " ", text.replace("( ", "(")), key)
            number, sub = re.match(r"s\.(\d+)", b["section"]).group(1), re.findall(r"\(\w+\)", b["section"])[-1]
            self.assertIn(sub, lines[first - 1], key)                          # the range opens on its sub-section
            heading = next(m.group(1) for ln in reversed(lines[:last]) if (m := re.match(r"^(\d+)\.\s", ln)))
            self.assertEqual(heading, number, key)                              # inside that section
        quote = re.search(r'"(the wages payable.*?resignation\.)"', desk_law.CLOCKS["exit_dues"]).group(1)
        self.assertIn(quote, " ".join(self.corpus("code_on_wages_2019.md")[458:464]))

    def test_the_instrument_table(self):
        for name, row in desk_law.INSTRUMENTS.items():
            first, last = map(int, row["lines"].split("-"))
            self.assertIn(name, " ".join(self.corpus(row["file"])[first - 1:last]), name)
            self.assertEqual(row["status"], "repealed")
        self.assertEqual(desk_law.IN_FORCE, {"labour_codes": None, "dpdp_rights": None})   # none shown until checked

    def test_the_table_agrees_with_the_gate_and_the_queues(self):
        self.assertEqual(desk_law.SENSITIVE_CASES, desk_rules.SENSITIVE)
        self.assertEqual(set(desk_law.CASE_TYPES), set(desk_rules.CLASSES) | {"people_query"})
        for t, spec in desk_law.CASE_TYPES.items():
            self.assertIn(spec["queue"], set(desk_law.QUEUES) | {"ic"}, t)
            self.assertTrue(all(k in desk_law.BASIS for k in spec["basis"]), t)
            self.assertTrue(spec["clock"] is None or spec["clock"] in desk_law.CLOCKS, t)
        self.assertNotRegex(desk_law.CLOCKS["posh"], r"\d")                    # no period stated until checked
        self.assertIn("not a legal opinion", desk_law.CLOCKS["exit_dues_late"])
        src = (KIT / "shared" / "audit_log.py").read_text(encoding="utf-8")
        self.assertLess(src.index('"doc.mirror"'), src.index('"desk.route_denied", "case.open", "case.update", "case.close", '
                                                             '"role.grant", "role.revoke",'))
        self.assertTrue({"case.open", "case.update", "case.close", "role.grant", "role.revoke"} <= audit_log.AUDIT_ACTIONS)


# ------------------------------------------------------------------ the wiring
class WiringTests(unittest.TestCase):
    def read(self, *parts):
        return (KIT.joinpath(*parts)).read_text(encoding="utf-8")

    def test_terraform(self):
        tf = self.read("terraform", "desk.tf")
        for coll in ("cases", "case_tokens"):
            self.assertRegex(tf, r'collection = "' + coll + r'"\n  field      = "expire_at"\n\n  ttl_config \{\}')
        idx = dict(re.findall(r"^    (\w+)\s+= (\[\[.*\]\])$", tf, re.M))
        self.assertEqual({k: json.loads(v) for k, v in idx.items()}, {
            "inbox": [["tenant", "ASCENDING"], ["queue", "ASCENDING"], ["status", "ASCENDING"], ["created_at", "DESCENDING"]],
            "inbox_ic": [["tenant", "ASCENDING"], ["queue", "ASCENDING"], ["chosen_contacts", "CONTAINS"],
                         ["status", "ASCENDING"], ["created_at", "DESCENDING"]],
            "mine": [["tenant", "ASCENDING"], ["requester", "ASCENDING"], ["created_at", "DESCENDING"]],
            "overdue": [["status", "ASCENDING"], ["due_at", "ASCENDING"]],
            "tenant": [["tenant", "ASCENDING"], ["status", "ASCENDING"], ["due_at", "ASCENDING"]]})
        src = self.read("shared", "cases.py")                                   # the queries those indexes serve
        for q in ('base = db.collection("cases").where("tenant", "==", tenant).where("queue", "==", q)',
                  'base = base.where("chosen_contacts", "array_contains", email)',
                  'rows = list(base.where("status", "in", list(statuses))\n                        .order_by("created_at", direction="DESCENDING")',
                  '.where("tenant", "==", tenant).where("requester", "==", email)\n                  .order_by("created_at", direction="DESCENDING")',
                  '.where("status", "in", list(ACTIVE))\n              .where("due_at", "<=", now + DUE_SOON)',
                  '.where("tenant", "==", tenant).where("status", "in", list(ACTIVE))\n              .order_by("due_at")'):
            self.assertIn(q, src)
        self.assertIn('local.desk_job = var.desk_job && var.chat_image != ""'.replace("local.desk_job", "desk_job"), tf)
        self.assertEqual(tf.count("count    = local.desk_job ? 1 : 0") + tf.count("count       = local.desk_job ? 1 : 0"), 3)
        self.assertIn('schedule    = "0 * * * *"', tf)
        self.assertIn('time_zone   = "Asia/Kolkata"', tf)
        self.assertIn('args    = ["desk_overdue.py", "--project", var.project_id]', tf)
        for acct in ("evalacme", "evalzeta", "evalglobex", "evalleaver", "evalgrc"):
            self.assertRegex(tf, rf"\n    {acct}\s+= \"DocuMind Desk eval: ")
            self.assertLessEqual(len(f"documind-{acct}-sa"), 30)
        self.assertIn('account_id   = "documind-gchat-sa"', tf)
        storage = self.read("terraform", "storage.tf")
        self.assertRegex(storage, r'resource "google_storage_bucket_iam_member" "chat_audit" \{\n  bucket = '
                                  r'google_storage_bucket\.audit\.name\n  role   = "roles/storage\.objectCreator"\n'
                                  r'  member = "serviceAccount:\$\{google_service_account\.chat\.email\}"')

    def test_the_deploy_script_and_the_pins(self):
        sh = self.read("commands", "lesson-12.8.sh")
        self.assertIn("|AUDIT_BUCKET=$PROJECT-audit|", sh)
        loop = re.search(r"for who in ([^;]+); do", sh.replace("\\\n", " ")).group(1).split()
        self.assertEqual(loop, ["documind-ui-sa", "documind-outsider-sa", "documind-evalacme-sa", "documind-evalzeta-sa",
                                "documind-evalglobex-sa", "documind-evalleaver-sa", "documind-evalgrc-sa", "documind-gchat-sa"])
        req = self.read("services", "chat", "requirements.txt")
        self.assertRegex(req, r"(?m)^google-cloud-storage==3\.13\.1$")
        self.assertRegex(req, r"(?m)^langgraph==1\.2\.12$")
        agent = self.read("services", "chat", "agent.py")
        self.assertTrue(agent.rstrip().endswith("import desk  # noqa: E402\n"
                                                "desk.install(app, caller=caller, tenant_for=tenant_for, thread_config=thread_config)"))

    def test_the_makefile(self):
        mk = self.read("Makefile")
        self.assertEqual(len(mk.splitlines()), 885)                             # workshop lesson 9.3 counts it
        self.assertIn("\n.DEFAULT_GOAL := dryrun\n", mk)
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        agents = self.read("mk", "agents.mk")
        for target in ("roles", "desk-queues", "cases", "cases-overdue", "smoke-cases", "desk-operators"):
            self.assertIn(target, phony)
            self.assertIn(f"\n{target}: guard-project\n", agents)
            self.assertIn(f"`{target}`", self.read("mk", "README.md"))
        for line in ("DESK_JOB   ?= false", "CHAT_IMAGE ?= $(IMAGE_REPO)/chat:$(GIT_SHA)",
                     "TF_EXTRA_VARS += -var desk_job=$(DESK_JOB) -var chat_image=$(CHAT_IMAGE)"):
            self.assertIn(f"\n{line}\n", agents)
        self.assertLess(mk.index("TF_EXTRA_VARS = "), mk.index("include mk/*.mk"))   # += appends to the recursive list
        self.assertIn("INFRA_VARS = $(subst -var ,--var ,$(TF_EXTRA_VARS))", mk)


# ------------------------------------------------------------------ commands/desk_ops.py
class DeskOpsTests(Lane):
    def run_ops(self, *args):
        fs = types.SimpleNamespace(Client=lambda project=None: self.db, SERVER_TIMESTAMP="SERVER_TIMESTAMP")
        with cloud_modules(firestore=fs), patch.dict(os.environ, {"DOCUMIND_OPERATOR": HR}), \
                redirect_stdout(io.StringIO()) as out:
            code = desk_ops.main(["--project", "documind-ai-YOUR-ID", *args])
        return code, out.getvalue()

    def test_the_gate_needs_no_queue_and_the_routed_desk_waits_for_a_posh_queue(self):
        self.db.collection("tenant_settings").document("acme").set({"data_region": "in"})
        # the gate's replies are fixed: every value, with no case queue at all
        for value in ("on", "off", "rules"):
            code, out = self.run_ops("desk", "--tenant", "acme", "--gate", value)
            self.assertEqual((code, self.db.docs["tenant_settings/acme"]["desk_gate"]), (0, value), out)
            self.assertEqual(json.loads(out)["desk_gate"], value)
            # on says what it costs, and how to keep the rules without it; rules and off print no such note
            self.assertEqual("model_check" in json.loads(out), value == "on", value)
            if value == "on":
                self.assertIn("make desk TENANT=acme DESK_GATE=rules", json.loads(out)["model_check"])
        # the routed Desk answers a POSH disclosure with the card: on is refused until the POSH queue is complete
        code, out = self.run_ops("desk", "--tenant", "acme", "--route", "on")
        self.assertEqual(code, 2)
        self.assertIn("posh: no POSH section", out)
        self.assertNotIn("desk_route", self.db.docs["tenant_settings/acme"])
        code, out = self.run_ops("queues", "--tenant", "acme", "--file", str(KIT / "evals/desk/queues.acme.json"))
        self.assertEqual(code, 0, out)
        doc = self.db.docs["tenant_settings/acme"]
        self.assertEqual((doc["data_region"], doc["case_queues"], doc["case_queues_set_by"]), ("in", self.queues, HR))
        self.assertNotIn("_note", json.dumps(doc["case_queues"]))
        self.assertIn("ic pune: ic.pune.presiding@example.com", json.loads(out)["not_readers"])
        code, out = self.run_ops("desk", "--tenant", "acme", "--route", "on")   # pune: nobody here reads its cases
        self.assertEqual(code, 2)
        self.assertIn("posh.units.pune: no Internal Committee member holds ic_member:pune", out)
        roles.role_ref(self.db, "acme", ME).set({"roles": ["employee", "ic_member:hyderabad", "ic_member:pune"]})
        # the queue complete and every office read: the routed Desk is accepted, on and single, then off again
        for args, mode in ((("--route", "on"), "on"), (("--route", "single", "--single", "handbook"), "single")):
            code, out = self.run_ops("desk", "--tenant", "acme", *args)
            self.assertEqual((code, self.db.docs["tenant_settings/acme"]["desk_route"], json.loads(out)["desk_route"]),
                             (0, mode, mode), out)
        code, out = self.run_ops("desk", "--tenant", "acme", "--route", "off")
        self.assertEqual((code, self.db.docs["tenant_settings/acme"]["desk_route"]), (0, "off"), out)
        # while only the gate is on, a queue file that drops POSH is written: the gate's reply needs no queue
        no_posh = {k: v for k, v in self.queues.items() if k != "posh"}
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(no_posh, f)
        self.addCleanup(os.unlink, f.name)
        self.run_ops("desk", "--tenant", "acme", "--gate", "on")
        code, out = self.run_ops("queues", "--tenant", "acme", "--file", f.name)
        self.assertEqual(code, 0, out)
        self.assertNotIn("posh", self.db.docs["tenant_settings/acme"]["case_queues"])
        code, out = self.run_ops("queues", "--tenant", "acme", "--file", str(KIT / "evals/desk/queues.acme.json"))
        self.assertEqual(code, 0, out)
        # the routed Desk on or single answers a POSH disclosure with the card, so the queue must stay complete
        for mode in ("on", "single"):
            self.db.collection("tenant_settings").document("acme").set({"desk_route": mode, "desk_single": "handbook"},
                                                                         merge=True)
            for change in (("--revoke", "ic_member:pune"), ("--revoke", "all"), ("--set", "employee,ic_member:hyderabad")):
                code, out = self.run_ops("roles", "--tenant", "acme", "--email", ME, *change)
                self.assertEqual(code, 2, (mode, change))
                self.assertIn(f"desk_route is {mode}", out)
            code, out = self.run_ops("queues", "--tenant", "acme", "--file", f.name)
            self.assertEqual(code, 2, mode)
            self.assertIn(f"desk_route is {mode}, so the POSH queue must stay complete and readable", out)
        self.assertEqual(sorted(self.roles(ME)), ["employee", "ic_member:hyderabad", "ic_member:pune"])
        self.assertIn("posh", self.db.docs["tenant_settings/acme"]["case_queues"])
        presiding = "ic.pune.presiding@example.com"                            # a second reader for pune
        self.db.collection("tenants").document("acme").collection("members").document(presiding).set({"email": presiding})
        roles.role_ref(self.db, "acme", presiding).set({"roles": ["employee", "ic_member:pune"]})
        code, out = self.run_ops("roles", "--tenant", "acme", "--email", ME, "--revoke", "ic_member:pune")
        self.assertEqual((code, json.loads(out)["after"]), (0, ["employee", "ic_member:hyderabad"]))
        self.db.collection("tenant_settings").document("acme").set({"desk_route": "shadow"}, merge=True)
        code, out = self.run_ops("roles", "--tenant", "acme", "--email", ME, "--revoke", "ic_member:hyderabad")
        self.assertEqual(code, 0, out)                                         # shadow answers no one

    def test_a_bad_queue_file_writes_nothing(self):
        import tempfile
        broken = copy.deepcopy(self.queues)
        del broken["posh"]["units"]["pune"]["local_committee"]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(broken, f)
        self.addCleanup(os.unlink, f.name)
        code, out = self.run_ops("queues", "--tenant", "acme", "--file", f.name)
        self.assertEqual(code, 2)
        self.assertIn("posh.units.pune.local_committee", out)
        self.assertNotIn("tenant_settings/acme", self.db.docs)
        code, out = self.run_ops("queues", "--tenant", "acme", "--file", str(KIT / "evals/desk/queues.zeta.json"), "--dry-run")
        self.assertEqual((code, json.loads(out)["action"]), (0, "would write"))
        self.assertNotIn("tenant_settings/acme", self.db.docs)

    def test_roles_and_cases(self):
        code, out = self.run_ops("roles", "--tenant", "acme", "--email", OTHER, "--set", "grc_member")
        line = json.loads(out)
        self.assertEqual((code, line["after"], line["revoked"]), (0, ["grc_member"], ["employee"]))
        self.assertIn("no employee or leaver role", line["note"])
        code, out = self.run_ops("roles", "--tenant", "acme", "--email", OTHER, "--revoke", "all")
        self.assertEqual((code, json.loads(out)["after"]), (0, ["employee"]))
        code, out = self.run_ops("roles", "--tenant", "acme", "--email", "nobody@example.com", "--set", "employee")
        self.assertEqual(code, 2)
        code, out = self.run_ops("roles", "--tenant", "acme")
        self.assertIn(json.dumps({"tenant": "acme", "email": GRC, "roles": ["employee", "grc_member"]}), out)
        self.assertEqual(self.actions(), ["role.grant", "role.revoke", "role.grant", "role.revoke"])
        g = self.opened("grievance", token="press-0001")
        x = self.opened("exit_dues", token="press-0002")
        code, out = self.run_ops("cases", "--tenant", "acme", "--json")
        rows = {r["case_id"]: r for r in map(json.loads, out.splitlines())}
        self.assertEqual((rows[g["case_id"]]["type"], rows[x["case_id"]]["type"]), ("sensitive", "exit_dues"))
        self.assertEqual((rows[g["case_id"]]["queue"], rows[x["case_id"]]["queue"]), ("sensitive", x["queue"]))
        self.assertNotIn(g["queue"], out)                       # grc would say what the case is about
        self.assertNotIn(ME, out)
        self.assertNotIn("my words", out)


# ------------------------------------------------------------------ the chat door and the routes (the chat pins)
def synthetic_aadhaar(first11="23456789012"):
    """A 12-digit number that passes Verhoeff, made here for the test; it belongs to nobody."""
    return first11 + identifiers.verhoeff_digit(first11)


class _OnTenants:
    """shared/desk_recall.OnTenants as the door reads it, over a set the test may change: claim() is None until
    refresh() has read once, as at a process's first turn; every claim and every read is counted. tenants() is the
    real one, the doors' own path."""
    tenants = desk_recall.OnTenants.tenants

    def __init__(self, tenants):
        self.set, self.reads, self.claims = tenants, 0, 0

    def claim(self):
        self.claims += 1
        return frozenset(self.set) if self.reads else None

    def refresh(self):
        self.reads += 1
        return frozenset(self.set)


class _App:
    """The downstream app: records what reached it and answers 200."""

    def __init__(self):
        self.calls = []

    async def __call__(self, scope, receive, send):
        msg = await receive()
        self.calls.append((scope, msg["body"]))
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": b'{"handler":true}'})


def _run(door, body: bytes, headers=(), path="/v1/chat"):
    scope = {"type": "http", "method": "POST", "path": path, "query_string": b"",
             "headers": [(b"content-type", b"application/json")] + list(headers)}
    queue = [{"type": "http.request", "body": body, "more_body": False}]
    sent = []

    async def receive():
        return queue.pop(0) if queue else {"type": "http.disconnect"}

    async def send(msg):
        sent.append(msg)

    asyncio.run(door(scope, receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    return start["status"], dict(start["headers"]), b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class ChatDoorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        import desk
        from starlette.exceptions import HTTPException
        cls.desk, cls.HTTPException = desk, HTTPException
        cls.real_check = staticmethod(desk._check)       # setUp patches it; one test runs the real one
        cls.real_checked = desk.CHECKED                  # and CHECKED, whose real read one test runs

    def setUp(self):
        self.app, self.door = _App(), self.desk.ChatDoor(_App())
        self.door.app = self.app
        self.reads, self.callers, self.shadows = [], [], []
        self.flags = {"acme": {"desk_gate": "on"}}
        self.checked, self.checks, self.verdict = set(), [], None
        self.door_checked = _OnTenants(self.checked)

        def caller(request):
            self.callers.append(1)
            email = request.headers.get("x-test-email")
            if not email:
                raise self.HTTPException(401, "no identity")
            return {"email": email, "assertion": None}

        def settings(tenant):
            self.reads.append(tenant)
            return self.flags.get(tenant, {})

        async def shadow(scope, question, tenant):
            self.shadows.append((question, tenant))

        def check(question):
            self.checks.append(question)
            out = {**desk_recall._result(), "tokens_in": 900, "tokens_out": 4, "ms": 400,
                   "cost_usd": desk_recall.prices.usd(desk_recall.MODEL, 900, 4)}
            if self.verdict == "error":
                out.update(outcome="error", error="TimeoutError")
            elif self.verdict:
                out.update(case=self.verdict, outcome="case")
            return out

        for p in (patch.dict(self.desk._hooks, {"caller": caller, "tenant_for": lambda e: "acme" if e == ME else None}),
                  patch.object(self.desk, "settings", settings), patch.object(self.desk, "PROFILE", "gcp"),
                  patch.object(self.desk, "_shadow", shadow), patch.object(self.desk, "CHECKED", self.door_checked),
                  patch.object(self.desk, "_check", check), patch.dict(self.desk._GATE_SEEN, {}, clear=True)):
            p.start()
            self.addCleanup(p.stop)

    def body(self, q, **extra):
        return json.dumps({"question": q, "session_id": "s1", **extra}).encode()

    def test_the_gate_off_replays_the_bytes(self):
        self.flags["acme"] = {"desk_gate": "off"}
        for raw in (self.body(POSH, brain="langchain"), b'{"question":  "' + PLAIN.encode() + b'"}'):
            status, _, out = _run(self.door, raw, [(b"x-test-email", ME.encode())])
            self.assertEqual((status, out, self.app.calls[-1][1]), (200, b'{"handler":true}', raw))
        self.assertEqual((len(self.callers), self.reads), (1, ["acme"]))       # the plain question was never verified
        self.assertEqual([t for _, t in self.shadows], ["acme", None])

    def test_the_local_profile_has_the_rules_and_reads_no_setting(self):
        touched = []

        def boom(*a):
            touched.append(a)                       # recorded: gate_state() would swallow the exception itself
            raise AssertionError("the local profile read a setting, verified a caller or looked for a check")
        self.checked.add("zeta")                                                 # never read on the local profile
        a = synthetic_aadhaar()
        masked_q = f"My Aadhaar is {a[:4]} {a[4:8]} {a[8:]}. How do I update my address in the records?"
        with patch.object(self.desk, "PROFILE", "local"), patch.object(self.desk, "settings", boom), \
                patch.object(self.desk, "gate_state", boom), \
                patch.dict(self.desk._hooks, {"caller": boom, "tenant_for": boom}), patch.object(self.desk, "_check", boom), \
                patch.dict(os.environ, {"LOCAL_TENANT": "zeta"}):
            status, _, out = _run(self.door, self.body(POSH))                     # a hit: the fixed reply, no model
            self.assertEqual((status, json.loads(out)["answer"], json.loads(out)["model"], self.app.calls),
                             (200, desk_law.template("posh"), "none", []))
            raw = self.body(PLAIN)                                                # no hit: chat() as before
            _run(self.door, raw)
            self.assertEqual((self.app.calls[-1][1], self.shadows), (raw, [(PLAIN, "zeta")]))
            _run(self.door, self.body(masked_q))                                  # a number: masked
            self.assertNotIn(a[8:], self.app.calls[-1][1].decode())
        self.assertEqual((self.door_checked.claims, self.door_checked.reads, touched), (0, 0, []))

    def test_an_aadhaar_number_is_masked_unless_the_gate_is_off(self):
        a = synthetic_aadhaar()
        q = f"My Aadhaar is {a[:4]} {a[4:8]} {a[8:]}. How do I update my address in the records?"
        self.assertIsNone(desk_rules.gate(q))
        status, _, out = _run(self.door, self.body(q, brain="adk"), [(b"x-test-email", ME.encode())])
        scope, got = self.app.calls[-1]
        sent = json.loads(got)
        self.assertEqual(sent, {"question": "My Aadhaar is [Aadhaar]. How do I update my address in the records?",
                                "session_id": "s1", "brain": "adk"})
        self.assertNotIn(a[8:], got.decode())
        self.assertIn((b"content-length", str(len(got)).encode()), scope["headers"])
        self.assertEqual(self.shadows[-1], (sent["question"], "acme"))           # the shadow sees what chat() sees
        self.flags["acme"] = {}                                                   # nothing set: the rules, masked too
        _run(self.door, self.body(q), [(b"x-test-email", ME.encode())])
        self.assertNotIn(a[8:], self.app.calls[-1][1].decode())
        self.flags["acme"] = {"desk_gate": "off"}
        raw = self.body(q)
        _run(self.door, raw, [(b"x-test-email", ME.encode())])
        self.assertEqual(self.app.calls[-1][1], raw)                             # off: unchanged

    def test_a_tenant_that_set_nothing_has_the_rules(self):
        for doc in ({}, {"desk_gate": "rules"}, {"desk_gate": "maybe"}):
            self.flags["acme"] = doc
            status, _, out = _run(self.door, self.body(POSH), [(b"x-test-email", ME.encode())])
            self.assertEqual((status, json.loads(out)["answer"], self.app.calls), (200, desk_law.template("posh"), []), doc)

    def test_a_failed_settings_read_keeps_the_rules_or_the_last_state(self):
        def unwell(tenant):
            raise RuntimeError("firestore is unwell")
        with patch.object(self.desk, "settings", unwell):
            status, _, out = _run(self.door, self.body(POSH), [(b"x-test-email", ME.encode())])
        self.assertEqual((status, json.loads(out)["brain"], self.app.calls), (200, "desk_gate", []))   # never off
        # a state read before stands while the switch cannot be read: an operator's off stays off
        self.flags["acme"] = {"desk_gate": "off"}
        a = synthetic_aadhaar()
        q = f"My Aadhaar is {a[:4]} {a[4:8]} {a[8:]}. How do I update my address in the records?"
        self.assertIsNone(desk_rules.gate(q))
        _run(self.door, self.body(q), [(b"x-test-email", ME.encode())])          # an identifier: the switch is read
        self.assertEqual(self.desk._GATE_SEEN["acme"], "off")
        with patch.object(self.desk, "settings", unwell):
            raw = self.body(POSH)
            _run(self.door, raw, [(b"x-test-email", ME.encode())])
        self.assertEqual(self.app.calls[-1][1], raw)
        # and it is the tenant's own: zeta's off never stands in for acme's unread switch
        self.desk._GATE_SEEN.clear()
        self.flags["zeta"] = {"desk_gate": "off"}
        with patch.dict(self.desk._hooks, {"tenant_for": lambda e: {ME: "acme", OTHER: "zeta"}.get(e)}):
            _run(self.door, self.body(q), [(b"x-test-email", OTHER.encode())])
            self.assertEqual(self.desk._GATE_SEEN, {"zeta": "off"})
            n = len(self.app.calls)
            with patch.object(self.desk, "settings", unwell):
                status, _, out = _run(self.door, self.body(POSH), [(b"x-test-email", ME.encode())])
        self.assertEqual((status, json.loads(out)["answer"], len(self.app.calls)), (200, desk_law.template("posh"), n))

    # ---------------------------------------------------------------- the model check (shared/desk_recall.py)
    def test_the_model_check_answers_what_the_rules_miss(self):
        self.assertIsNone(desk_rules.gate(MISS))
        self.checked.add("acme")
        self.verdict = "posh"
        records = self.records()
        self.assertEqual((self.door_checked.claims, self.door_checked.reads), (0, 0))   # a process's first turn
        status, _, out = _run(self.door, self.body(MISS, brain="langchain"), [(b"x-test-email", ME.encode())])
        body = json.loads(out)
        self.assertEqual((status, self.app.calls, self.checks, self.door_checked.reads), (200, [], [MISS], 1))
        self.assertEqual((body["answer"], body["brain"], body["model"], body["limits"]["model_calls"],
                          body["case_offer"]), (desk_law.template("posh"), "desk_gate", desk_recall.MODEL, 1,
                                                {"case_type": "posh"}))
        self.assertGreater(body["limits"]["cost_inr"], 0)
        self.assertEqual([r["event"] for r in records], ["desk_gate_check", "desk_gate"])
        self.assertEqual((records[0]["outcome"], records[0]["tenant"]), ("case", "acme"))
        self.assertEqual(records[1], {"event": "desk_gate", "surface": "chat", "tenant": "acme", "user": None,
                                      "class": "sensitive", "rules_version": desk_rules.RULES_VERSION, "method": "model"})
        self.assertNotIn(MISS, json.dumps(records))
        self.assertEqual(self.shadows, [])                                        # answered at the door: no shadow

    def test_a_model_hit_that_carries_a_number_is_answered_and_the_number_never_leaves(self):
        a = synthetic_aadhaar()
        q = f"{MISS}. My Aadhaar is {a[:4]} {a[4:8]} {a[8:]}"
        self.assertIsNone(desk_rules.gate(q))
        self.checked.add("acme")
        self.verdict = "posh"
        records = self.records()
        status, _, out = _run(self.door, self.body(q), [(b"x-test-email", ME.encode())])
        body = json.loads(out)
        self.assertEqual((status, self.app.calls, body["answer"], body["model"]),
                         (200, [], desk_law.template("posh"), desk_recall.MODEL))
        self.assertEqual(self.checks, [f"{MISS}. My Aadhaar is [Aadhaar]"])
        self.assertEqual(records[-1]["method"], "model")
        self.assertNotIn(a[8:], json.dumps(records) + out.decode())

    def test_the_check_and_the_read_run_on_the_kits_threads_with_the_requests_context(self):
        import contextvars
        import threading
        var, seen = contextvars.ContextVar("request", default=None), []
        self.checked.add("acme")
        self.verdict = "posh"
        check, claim, refresh = self.desk._check, self.door_checked.claim, self.door_checked.refresh
        self.door_checked.claim = lambda: (seen.append(("claim", threading.current_thread().name, var.get())), claim())[1]
        self.door_checked.refresh = lambda: (seen.append(("read", threading.current_thread().name, var.get())), refresh())[1]
        wrapped = (lambda q: (seen.append(("check", threading.current_thread().name, var.get())), check(q))[1])
        token = var.set("the request")                     # a request's trace span is a contextvar like this one
        try:
            with patch.object(self.desk, "_check", wrapped):
                _run(self.door, self.body(MISS), [(b"x-test-email", ME.encode())])
        finally:
            var.reset(token)
        self.assertEqual([(k, t.rsplit("_", 1)[0], v) for k, t, v in seen],       # the claim on the event loop's
                         [("claim", threading.current_thread().name, "the request"),   # thread, no worker's
                          ("read", "desk-check-read", "the request"), ("check", "desk-check", "the request")])

    def test_a_question_with_no_words_costs_no_check(self):
        self.checked.add("acme")
        self.verdict = "posh"
        for q in ("   ", "\n\t"):
            raw = self.body(q)
            _run(self.door, raw, [(b"x-test-email", ME.encode())])
            self.assertEqual((self.app.calls[-1][1], self.checks, self.callers, self.door_checked.claims),
                             (raw, [], [], 0), repr(q))

    def test_through_the_door_a_turn_never_queues_behind_the_read(self):
        import threading
        started, release, reads = threading.Event(), threading.Event(), []

        def slow_read():
            reads.append(threading.current_thread().name)
            started.set()
            release.wait(5)
            return frozenset({"acme"})
        on = desk_recall.OnTenants(slow_read, self.desk.log, "chat", ttl_s=60)

        async def burst():                                  # five turns at the same moment, before any thread has run
            turns = [asyncio.ensure_future(self.door._checking()) for _ in range(5)]
            await asyncio.get_running_loop().run_in_executor(None, started.wait, 5)
            waiting = sum(not t.done() for t in turns)      # only the turn that claimed the read waits for it
            release.set()
            return waiting, sorted(await asyncio.gather(*turns))
        with patch.object(self.desk, "CHECKED", on):
            self.assertEqual(asyncio.run(burst()), (1, [False] * 4 + [True]))
            started.clear()
            release.clear()
            on._at -= 61                                    # the minute's end: one turn reads again, four do not wait
            self.assertEqual(asyncio.run(burst()), (1, [True] * 5))
        self.assertEqual(len(reads), 2)
        self.assertTrue(all(r.startswith("desk-check-read") for r in reads), reads)

    def test_the_real_check_passes_the_routed_desks_client(self):
        class _Usage:
            prompt_token_count, candidates_token_count, thoughts_token_count, cached_content_token_count = 900, 4, 0, 0

        class _Gen:
            def __init__(self):
                self.models, self.calls = self, []

            def generate_content(self, model, contents, config):
                self.calls.append(model)
                return types.SimpleNamespace(parsed={"case": "posh"}, text=None, usage_metadata=_Usage())
        gen = _Gen()
        with patch.object(self.desk, "_models", lambda: types.SimpleNamespace(gen=gen)):
            got = self.real_check("masked words")
        self.assertEqual((got["case"], got["outcome"], gen.calls), ("posh", "case", [desk_recall.MODEL]))
        with patch.object(self.desk, "_models", lambda: None):                   # no client: no check, and why
            self.assertEqual(self.real_check("masked words"), desk_recall.unavailable())

    def test_the_model_check_reads_the_masked_question_and_a_miss_goes_on(self):
        a = synthetic_aadhaar()
        q = f"My Aadhaar is {a}. How do I update my address in the records?"
        self.checked.add("acme")
        levels = []
        handler = logging.Handler()
        handler.emit = lambda r: levels.append((r.levelno, json.loads(r.getMessage()).get("outcome")))
        lg = logging.getLogger("documind.chat.desk")
        lg.addHandler(handler)
        self.addCleanup(lg.removeHandler, handler)
        self.addCleanup(setattr, lg, "level", lg.level)
        lg.setLevel(logging.INFO)
        disabled = logging.root.manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, disabled)
        for verdict in (None, "error"):
            self.verdict = verdict
            _run(self.door, self.body(q), [(b"x-test-email", ME.encode())])
            self.assertEqual(self.checks[-1], "My Aadhaar is [Aadhaar]. How do I update my address in the records?")
            self.assertNotIn(a, self.app.calls[-1][1].decode())                  # masked, then on to chat()
        # a failed check is a WARNING, the stand-in for an alert until one exists; none is INFO
        self.assertEqual(levels, [(logging.INFO, "none"), (logging.WARNING, "error")])
        raw = self.body(PLAIN)
        _run(self.door, raw, [(b"x-test-email", ME.encode())])
        self.assertEqual(self.app.calls[-1][1], raw)                             # no identifier: the bytes as sent

    def test_the_real_checked_reads_the_routed_desks_firestore(self):
        seen = []

        class _Query:
            def where(self, field, op, value):
                seen.append((field, op, value))
                return self

            def stream(self, **kw):
                seen.append(kw)
                return [types.SimpleNamespace(id="acme")]
        db = types.SimpleNamespace(collection=lambda name: (seen.append(name), _Query())[1])
        on = desk_recall.OnTenants(self.real_checked._read, self.desk.log, "chat")   # the module's own read
        with patch.object(self.desk, "_client", lambda: db):
            self.assertEqual(on.get(), frozenset({"acme"}))
        self.assertEqual(seen, ["tenant_settings", ("desk_gate", "in", ["on", True]),
                                {"retry": None, "timeout": desk_recall.READ_TIMEOUT_S}])

    def test_the_model_check_runs_only_for_a_tenant_whose_gate_is_on(self):
        raw = self.body(MISS)
        _run(self.door, raw, [(b"x-test-email", ME.encode())])                   # nobody's gate is on: no lookup
        self.assertEqual((self.callers, self.reads, self.checks, self.app.calls[-1][1]), ([], [], [], raw))
        self.checked.add("zeta")                                                 # someone else's is on
        for doc in ({}, {"desk_gate": "rules"}, {"desk_gate": "off"}):
            self.flags["acme"] = doc
            _run(self.door, raw, [(b"x-test-email", ME.encode())])
            self.assertEqual((self.checks, self.app.calls[-1][1]), ([], raw), doc)
        self.assertEqual(len(self.callers), 3)                                   # looked up, then not checked
        self.flags["acme"] = {"desk_gate": "on"}
        _run(self.door, raw)                                                      # a caller chat() refuses: its own 401
        self.assertEqual((self.checks, self.app.calls[-1][1]), ([], raw))
        self.verdict = "posh"
        claims = self.door_checked.claims
        _run(self.door, self.body(POSH), [(b"x-test-email", ME.encode())])       # a rule hit: the rule answers,
        self.assertEqual((self.checks, self.door_checked.claims), ([], claims))  # and the list is not asked for
        _run(self.door, raw, [(b"x-test-email", ME.encode())])
        self.assertEqual(self.checks, [MISS])

    def records(self) -> list:
        records = []
        handler = logging.Handler()
        handler.emit = lambda r: records.append(json.loads(r.getMessage()))
        lg = logging.getLogger("documind.chat.desk")
        lg.addHandler(handler)
        lg.setLevel(logging.INFO)
        self.addCleanup(lg.removeHandler, handler)
        self.addCleanup(setattr, lg, "propagate", lg.propagate)
        lg.propagate = False
        disabled = logging.root.manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, disabled)
        return records

    def test_a_lone_surrogate_reaches_the_handler(self):
        a = synthetic_aadhaar()
        raw = ('{"question": "My Aadhaar is ' + a + ' \\ud800", "session_id": "s1"}').encode()
        status, _, out = _run(self.door, raw, [(b"x-test-email", ME.encode())])
        self.assertEqual(status, 200)                                            # the fake handler: no 500 at the door
        got = self.app.calls[-1][1]
        self.assertNotIn(a, got.decode())
        self.assertIn(b"\\ud800", got)

    def test_the_64_kib_cap(self):
        status, headers, out = _run(self.door, b"x" * (64 * 1024 + 1))
        self.assertEqual((status, out), (413, b'{"detail":"request body over 65536 bytes"}'))
        self.assertEqual(self.app.calls, [])
        status, _, _ = _run(self.door, b"{}", [(b"content-length", b"999999")])
        self.assertEqual(status, 413)

    def test_a_hit_is_answered_at_the_door(self):
        records = []
        handler = logging.Handler()
        handler.emit = lambda r: records.append(json.loads(r.getMessage()))
        lg = logging.getLogger("documind.chat.desk")
        lg.addHandler(handler)
        lg.setLevel(logging.INFO)
        self.addCleanup(lg.removeHandler, handler)
        self.addCleanup(setattr, lg, "propagate", lg.propagate)
        lg.propagate = False                                                     # the row is read here, not printed
        disabled = logging.root.manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, disabled)
        status, headers, out = _run(self.door, self.body(POSH), [(b"x-test-email", ME.encode())])
        body = json.loads(out)
        self.assertEqual(status, 200)
        self.assertEqual(self.app.calls, [])
        self.assertEqual(out, json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode())   # FastAPI's bytes
        self.assertEqual((body["answer"], body["brain"], body["model"], body["tool_calls"], body["refusals"],
                          body["citations"], body["session_id"], body["limits"]["cost_inr"], body["limits"]["model_calls"]),
                         (desk_law.template("posh"), "desk_gate", "none", [], [], [], "s1", 0, 0))
        self.assertEqual(body["case_offer"], {"case_type": "posh"})              # the case to offer, not the words
        self.assertEqual(records[-1], {"event": "desk_gate", "surface": "chat", "tenant": "acme", "user": None,
                                       "class": "sensitive", "rules_version": desk_rules.RULES_VERSION, "method": "rule"})
        status, _, out = _run(self.door, self.body(POSH), [(b"x-test-email", OTHER.encode())])   # on no roster
        self.assertEqual((status, out), (403, b'{"detail":"not a member of any tenant"}'))
        status, _, out = _run(self.door, self.body(POSH))
        self.assertEqual((status, out), (401, b'{"detail":"no identity"}'))
        self.assertEqual(self.app.calls, [])
        self.assertEqual(self.shadows, [])


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class ChatServiceTests(unittest.TestCase):
    """The real chat service: agent.py's app, with the door install() put in front of it."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.CRITICAL)
        with patch.dict(os.environ, {"CHECKPOINT_DSN": "memory"}):
            sys.modules.pop("agent", None)
            import agent
        import brains
        import desk
        from fastapi.testclient import TestClient
        from langchain_core.language_models.chat_models import BaseChatModel
        from langchain_core.messages import AIMessage
        from langchain_core.outputs import ChatGeneration, ChatResult
        from pydantic import Field
        from shared import iap

        class Model(BaseChatModel):
            """Answers at once, and keeps a note of every call."""
            seen: list = Field(default_factory=list)

            @property
            def _llm_type(self):
                return "script"

            def bind_tools(self, tools, **kw):
                return self.bind(**kw)

            def _generate(self, messages, stop=None, run_manager=None, **kw):
                self.seen.append(len(messages))
                msg = AIMessage("done", usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15})
                return ChatResult(generations=[ChatGeneration(message=msg)])

        cls.agent, cls.brains, cls.desk, cls.TestClient, cls.Model, cls.iap = agent, brains, desk, TestClient, Model, iap

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def lane(self, tenants, flags=None, db=None, queues=None):
        """The chat service on the gcp profile: the identity from an x-test-email header (the bearer leg), the tenant
        from `tenants`, tenant_settings from `flags` and `queues`."""
        def identity(headers, bearer_audience=None):
            email = headers.get("x-test-email")
            if not email:
                raise self.iap.IapError("no identity: neither an IAP assertion nor a bearer token")
            return {"email": email, "via": "bearer"}

        def tenant_for(email):
            return tenants.get(email)

        def settings(tenant):
            return {**(flags or {}).get(tenant, {}), "case_queues": (queues or {}).get(tenant, {})}

        stack = contextlib.ExitStack()
        for p in (patch.object(self.iap, "identity", identity), patch.object(self.agent, "PROFILE", "gcp"),
                  patch.object(self.desk, "PROFILE", "gcp"), patch.object(self.agent, "tenant_for", tenant_for),
                  patch.dict(self.desk._hooks, {"tenant_for": tenant_for}), patch.object(self.desk, "settings", settings),
                  patch.object(self.desk, "_client", lambda: db), patch.object(self.desk, "CHECKED", _OnTenants(set())),
                  patch.object(self.desk, "SHADOWING", desk_recall.OnTenants(frozenset, self.desk.log, "test"))):
            stack.enter_context(p)
        self.addCleanup(stack.close)
        return self.TestClient(self.agent.app)

    def test_a_refused_caller_gets_the_same_bytes_on_a_hit_and_a_miss(self):
        with self.lane({ME: "acme"}, {"acme": {"desk_gate": "on"}}) as client:
            for headers in ({}, {"x-test-email": OTHER}):                       # no identity (401); on no roster (403)
                hit = client.post("/v1/chat", json={"question": POSH, "session_id": "s1"}, headers=headers)
                miss = client.post("/v1/chat", json={"question": PLAIN, "session_id": "s1"}, headers=headers)
                self.assertIn(hit.status_code, (401, 403))
                self.assertEqual((hit.status_code, hit.content, list(hit.headers.items())),
                                 (miss.status_code, miss.content, list(miss.headers.items())))

    def test_a_gated_turn_reaches_no_brain(self):
        from langgraph.checkpoint.memory import InMemorySaver  # noqa: F401 - the memory checkpointer is the lane's here
        with self.lane({ME: "acme"}, {"acme": {"desk_gate": "on"}}) as client:
            saver, model = client.app.state.checkpointer, self.Model()
            client.app.state.brains["langchain"] = self.brains.build("langchain", saver, llm=model)
            r = client.post("/v1/chat", json={"question": POSH, "session_id": "gated", "brain": "langchain"},
                            headers={"x-test-email": ME})
            self.assertEqual((r.status_code, r.json()["brain"], r.json()["model"]), (200, "desk_gate", "none"))
            self.assertEqual(model.seen, [])
            cfg = self.agent.thread_config("acme", ME, "gated")
            self.assertEqual(list(saver.list(cfg)), [])
            # the same lane and the same brain answer a question the gate does not take: the brain was reachable
            r = client.post("/v1/chat", json={"question": PLAIN, "session_id": "gated", "brain": "langchain"},
                            headers={"x-test-email": ME})
            self.assertEqual((r.status_code, r.json()["brain"], len(model.seen)), (200, "langchain", 1))
            self.assertGreater(len(list(saver.list(cfg))), 0)

    def test_the_offer_says_the_gate_as_the_doors_read_it(self):
        db, flags = FakeDB(), {"acme": {}}
        db.collection("tenants").document("acme").collection("members").document(ME).set({"email": ME})
        with self.lane({ME: "acme"}, flags, db=db, queues={"acme": queues_file("acme")}) as client:
            for value, want in ((None, "rules"), ("rules", "rules"), ("off", "off"), ("on", "on"), (True, "on"),
                                (False, "off"), ("On", "rules")):
                flags["acme"] = {} if value is None else {"desk_gate": value}
                got = client.get("/v1/cases/offer", headers={"x-test-email": ME})
                self.assertEqual((got.status_code, got.json()["desk_gate"]), (200, want), value)

    def test_the_case_routes(self):
        db, events = FakeDB(), []
        people = {ME: "acme", GRC: "acme", HR: "acme", OTHER: "acme", "z@example.com": "zeta"}
        for e, t in people.items():
            db.collection("tenants").document(t).collection("members").document(e).set({"email": e})
        roles.role_ref(db, "acme", GRC).set({"roles": ["employee", "grc_member"]})
        roles.role_ref(db, "acme", HR).set({"roles": ["people_ops"]})
        roles.role_ref(db, "acme", OTHER).set({"roles": ["leaver"]})
        roles.role_ref(db, "acme", ME).set({"roles": ["employee", "ic_member:pune"]})
        with patch.object(cases, "_fs", lambda: FS), patch.object(audit_log, "storage", _storage(events)), \
                patch.object(audit_log, "_bucket", None), patch.dict(os.environ, {"AUDIT_BUCKET": "documind-ai-YOUR-ID-audit"}), \
                self.lane(people, db=db, queues={"acme": queues_file("acme"), "zeta": queues_file("zeta")}) as client:
            def call(method, path, who, body=None):
                return client.request(method, path, json=body, headers={"x-test-email": who} if who else {})

            r = call("POST", "/v1/cases", ME, {"case_type": "grievance", "summary": "my words"})
            self.assertEqual(r.status_code, 200, r.text)
            d = r.json()
            self.assertEqual((d["status"], d["queue"], d["via"], d["sensitive"]), ("draft", "grc", "direct", True))
            self.assertNotIn("token_sha256", d)
            cid = d["case_id"]
            one = call("POST", f"/v1/cases/{cid}/confirm", ME, {"token": "press-0001"}).json()
            two = call("POST", f"/v1/cases/{cid}/confirm", ME, {"token": "press-0001"}).json()
            self.assertEqual((one["status"], two["case_id"], two["opened_at"]), ("open", cid, one["opened_at"]))
            self.assertEqual(call("POST", f"/v1/cases/{cid}/confirm", ME, {"token": "press-0002"}).status_code, 409)
            self.assertEqual(call("POST", f"/v1/cases/{cid}/confirm", ME, {}).status_code, 422)    # the token is required
            inbox = call("GET", "/v1/cases", GRC).json()
            self.assertEqual(([c["case_id"] for c in inbox["inbox"]], inbox["roles"], inbox["email"]),
                             ([cid], ["employee", "grc_member"], GRC))           # the person as the service saw them
            self.assertEqual([c["case_id"] for c in call("GET", "/v1/cases", ME).json()["mine"]], [cid])
            for who in ("z@example.com", HR):
                self.assertEqual(call("GET", f"/v1/cases/{cid}", who).status_code, 404, who)
            self.assertEqual(call("POST", f"/v1/cases/{cid}/status", ME, {"status": "resolved"}).status_code, 403)
            self.assertEqual(call("POST", f"/v1/cases/{cid}/status", GRC, {"status": "acknowledged"}).json()["status"],
                             "acknowledged")
            # posh: no text, one press one case, the Local Committee always named
            self.assertEqual(call("POST", "/v1/cases", ME, {"case_type": "posh", "summary": "what happened"}).status_code, 422)
            press = {"case_type": "posh", "unit": "pune", "contacts": [ME], "token": "press-0003"}
            no_token = {k: v for k, v in press.items() if k != "token"}
            self.assertEqual(call("POST", "/v1/cases", OTHER, no_token).status_code, 422)   # a POSH press needs one
            p1, p2 = call("POST", "/v1/cases", OTHER, press).json(), call("POST", "/v1/cases", OTHER, press).json()
            self.assertEqual((p1["status"], p2["case_id"], p1["summary"]), ("open", p1["case_id"], None))
            self.assertEqual(p1["owner"]["local_committee"]["contact"], "lc.pune@example.com")
            self.assertEqual(sum(c["case_type"] == "posh" for c in db.cases().values()), 1)
            # who may raise one: a leaver may (above); people_ops alone may not; nobody off the roster
            self.assertEqual(call("POST", "/v1/cases", HR, {"case_type": "human_requested"}).status_code, 403)
            self.assertEqual(call("POST", "/v1/cases", "stranger@example.com", {"case_type": "human_requested"}).status_code, 403)
            self.assertEqual(call("GET", "/v1/cases", None).status_code, 401)
            # a draft withdrawn: gone, and the queue never sees it
            w = call("POST", "/v1/cases", ME, {"case_type": "grievance", "summary": "second thoughts"}).json()
            self.assertEqual(call("POST", f"/v1/cases/{w['case_id']}/cancel", ME).json()["status"], "withdrawn")
            self.assertEqual(call("GET", f"/v1/cases/{w['case_id']}", GRC).status_code, 404)
            self.assertNotIn(w["case_id"], json.dumps(call("GET", "/v1/cases", GRC).json()))
            # what a person may raise: the switches, the configured types, the POSH card; no case read, no text
            offer = call("GET", "/v1/cases/offer", ME).json()
            self.assertEqual((offer["email"], offer["tenant"], offer["desk_gate"], offer["desk_route"]),
                             (ME, "acme", "rules", "off"))                     # nothing set: the gate's rules
            self.assertEqual(offer["types"], list(desk_law.CASE_TYPES))
            self.assertEqual(sorted(offer["posh"]), ["hyderabad", "pune"])
            self.assertEqual(offer["posh"]["pune"]["local_committee"]["contact"], "lc.pune@example.com")
            self.assertIn({"name": "Member (placeholder)", "email": ME}, offer["posh"]["pune"]["members"])
            self.assertEqual(call("GET", "/v1/cases/offer", HR).status_code, 403)                  # cannot raise one
            self.assertEqual(call("GET", "/v1/cases/offer", "z@example.com").json()["tenant"], "zeta")
            r = call("GET", "/v1/cases/" + "0" * 31 + "g", ME)                    # not a case id: no route at all
            self.assertEqual((r.status_code, r.json()), (404, {"detail": "Not Found"}))
            self.assertEqual(call("GET", "/v1/cases/" + "f" * 32, ME).json(), {"detail": "no such case"})
            with patch.object(self.desk, "PROFILE", "local"):
                self.assertEqual(call("GET", "/v1/cases", ME).status_code, 501)
        self.assertEqual([e["action"] for e in events], ["case.open", "case.update", "case.open"])
        self.assertNotIn("@", json.dumps([e["actor"] for e in events]))


if __name__ == "__main__":
    unittest.main()
