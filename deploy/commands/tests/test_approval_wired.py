"""Offline checks for the approval wired into the chat service (workshop lesson 5.8): shared/approvals.py, the records;
services/chat/approval_routes.py, the brain, the hold and the /v1/approvals routes behind tenant_settings.agent_actions;
and services/ingest/reconcile.py --approved, the operator's run.

    python -m unittest commands/tests/test_approval_wired.py -v          # from deploy/
    DOCUMIND_REQUIRE_LIBS=1 python -m unittest commands/tests/test_approval_wired.py   # CI's chat-pins steps

The first two classes need only the standard library. Wiring: the switch reaches the service through one call in
agent.chat() and one install line, defaults off, and is the one importer of approval.py; doc_approver is a role, the
four audit actions are registered, make, the Makefile's .PHONY, mk/README.md and both CI chat-pins steps carry the new
targets and this file; reconcile.py --approved re-checks and then re-enters --retire's own branch, so the tombstone's
code and its two mirror calls are unchanged. Records: shared/approvals.py on a fake Firestore and a fake audit bucket -
one pause, one record; who may read; 410 past expire_at and 409 once decided, checked in code; the statuses a decision
amounts to; the executor that records and withdraws nothing; recheck()'s refusals; the audit event kept on the record
when the bucket write fails, and written at the next change.

The third class runs the real chat service (agent.py's app, the approval brain on a scripted model, a stand-in rag-api)
and needs the chat image's pins (pip install -r services/chat/requirements.txt): the switch off is the brain lessons
5.4, 5.5 and 5.7 show, refuse node and all, with no record written; on, a withdrawal pauses the turn with its record,
the paused conversation is held (409), the person who asked cannot approve (403), another company's approver and a
colleague without the role cannot see the record (404), the second person's approval resumes the turn and the executor
records it, a second decision is 409, a rejection errors that call alone, the requester's own reject cancels, a
question (ask_user) is the requester's alone, an expired record is 410 and the hold then ends the pause, a lost pause
is 409, offer_case reaches the response as case_offer, and --approved runs on the record. Without the pins it is
skipped and says so; with DOCUMIND_REQUIRE_LIBS=1 a missing pin is an error instead.
"""
from __future__ import annotations

import contextlib
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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[2]
for p in (str(KIT / "services/chat"), str(KIT / "services/ingest"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from shared import approvals, roles  # noqa: E402

REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "fastapi"))
TENANT, ME, SECOND, COLLEAGUE, ZOE = "acme", "asha@example.com", "ravi@example.com", "meena@example.com", "zoe@example.com"
DOC = "townhall_2026_q1.md"
ROUTES = (KIT / "services/chat/approval_routes.py").read_text(encoding="utf-8")
AGENT = (KIT / "services/chat/agent.py").read_text(encoding="utf-8")
RECONCILE = (KIT / "services/ingest/reconcile.py").read_text(encoding="utf-8")
AP = "approval"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


tc = _load("test_cases_for_wired", KIT / "commands/tests/test_cases.py")        # the fake Firestore and audit bucket
ta = _load("test_approvals_for_wired", KIT / "commands/tests/test_approvals.py")  # scripted models and turns


def roster(db, members: dict) -> None:
    """members: email -> (tenant, roles or None)."""
    for email, (tenant, held) in members.items():
        db.collection("tenants").document(tenant).collection("members").document(email).set({"email": email})
        if held is not None:
            roles.role_ref(db, tenant, email).set({"roles": held})


def ask(tool: str, args: dict) -> dict:
    return {"tool": tool, "args": args, "call_id": "c0", "allowed_decisions": ["approve", "reject"] if tool == "withdraw_document"
            else ["respond"], "description": "what the person deciding reads", "tenant": TENANT, "requester": ME}


# ------------------------------------------------------------------ the standard library half: the wiring
class Wiring(unittest.TestCase):
    def read(self, *parts) -> str:
        return KIT.joinpath(*parts).read_text(encoding="utf-8")

    def test_one_call_in_chat_and_one_install_line_reach_the_switch(self):
        self.assertEqual(AGENT.count("approval_routes.wired(request.app, name, brain, tenant_id, user[\"email\"], req.session_id)"), 1)
        self.assertEqual(AGENT.count("approval_routes.install(app, caller=caller, tenant_for=tenant_for, thread_config=thread_config)"), 1)
        self.assertLess(AGENT.index("desk.install(app,"), AGENT.index("import approval_routes"))   # after the Desk's line
        importers = sorted(p.relative_to(KIT).as_posix() for p in (KIT / "services").rglob("*.py")
                           if p.name != "approval.py" and "__pycache__" not in p.parts
                           and re.search(r"^\s*(?:from approval import|import approval\b)", p.read_text(encoding="utf-8"), re.M))
        self.assertEqual(importers, ["services/chat/approval_routes.py"])
        self.assertIn('SWITCH, ON = "agent_actions", "approval"', ROUTES)
        self.assertIn("if name != WIRED_BRAIN or not switched_on(tenant):\n        return brain", ROUTES)   # off: the brain given
        self.assertIn('if PROFILE == "local":\n        return False', ROUTES)                                 # never on the laptop
        ops = self.read("commands", "desk_ops.py")
        self.assertIn('"agent_actions": ("off", "approval")', ops)
        self.assertIn("THE SERVICE REACHES THIS MODULE THROUGH ONE SWITCH, OFF UNTIL AN OPERATOR SETS IT.",
                      self.read("services", "chat", "approval.py"))

    def test_the_role_the_actions_and_the_targets(self):
        self.assertEqual(roles.ROLES[-1], approvals.APPROVER)
        self.assertEqual(approvals.APPROVER, "doc_approver")
        self.assertEqual(roles.desks(["doc_approver"]), set())                 # it opens no desk
        aud = self.read("shared", "audit_log.py")
        actions = re.search(r"AUDIT_ACTIONS = \{(.*?)\n\}", aud, re.S).group(1)
        for name in ("request", "approve", "reject"):
            self.assertIn(f'"{AP}.{name}"', actions)
        self.assertIn('"doc.withdraw"', actions)
        literal = re.compile(r'(?:audit_emit|audit_log\.emit|\bemit)\("([a-z_.]+)"')   # lesson 4.8 lists the kit's emitters
        self.assertEqual(sorted(literal.findall(self.read("shared", "approvals.py"))),
                         [f"{AP}.approve", f"{AP}.reject", f"{AP}.request", "doc.withdraw"])
        for src in (ROUTES, RECONCILE, self.read("smoke", "smoke_approval.py"), Path(__file__).read_text(encoding="utf-8")):
            self.assertEqual(literal.findall(src), [])
        mk, agents, readme = self.read("Makefile"), self.read("mk", "agents.mk"), self.read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                            # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        for target in ("agent-actions", "withdraw-run", "smoke-approval"):
            self.assertIn(target, phony)
            self.assertIn(f"\n{target}: guard-project\n", agents)
            self.assertIn(f"`{target}`", readme)
        self.assertLess(agents.index("\napproval-check:\n"), agents.index("\nagent-actions: guard-project\n"))   # appended
        self.assertIn("desk --tenant $(TENANT) $(if $(AGENT_ACTIONS),--actions $(AGENT_ACTIONS),)", agents)
        self.assertIn('--approved "$(APPROVAL)" $(if $(DRY),,--apply)', agents)
        self.assertIn("$(PY) smoke/smoke_approval.py", agents)
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_approval_wired.py -v"
        workflows = [self.read(".github", "workflows", "documind-dryrun.yml")]
        repo_ci = KIT.parent / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():
            workflows.append(repo_ci.read_text(encoding="utf-8"))
        for wf in workflows:
            self.assertIn(f"\n          {line}\n", wf)

    def test_reconcile_approved_rechecks_then_reenters_the_retire_branch(self):
        self.assertIn('ap.add_argument("--approved"', RECONCILE)
        self.assertIn("rec = approvals.recheck(db, a.approved)", RECONCILE)
        self.assertIn('[sys.argv[0], "--project", a.project, "--retire", source, "--apply"]', RECONCILE)
        self.assertIn("rec = approvals.withdrawn(db, rec, run_by=", RECONCILE)
        self.assertLess(RECONCILE.index("    if a.approved:"), RECONCILE.index("    if a.retire:"))
        self.assertEqual(re.findall(r"mirror\.(\w+)\(", RECONCILE), ["retired", "retired"])   # lesson 7.3's fact holds
        self.assertNotIn("import logging", RECONCILE)                                         # lesson 7.4's
        retire = RECONCILE[RECONCILE.index("    if a.retire:"):RECONCILE.index("    if a.restore:")]
        self.assertNotIn("audit", retire.replace("AUDIT_BUCKET", ""))                        # make retire writes no event


# ------------------------------------------------------------------ the records, on a fake Firestore
class Records(unittest.TestCase):
    def setUp(self):
        self.db = tc.FakeDB()
        roster(self.db, {ME: (TENANT, None), SECOND: (TENANT, ["employee", "doc_approver"]), COLLEAGUE: (TENANT, None),
                         ZOE: ("zeta", ["employee", "doc_approver"])})
        self.events = []
        stack = contextlib.ExitStack()
        for p in (patch.object(tc.audit_log, "storage", tc._storage(self.events)), patch.object(tc.audit_log, "_bucket", None),
                  patch.dict(os.environ, {"AUDIT_BUCKET": "documind-ai-YOUR-ID-audit"})):
            stack.enter_context(p)
        self.addCleanup(stack.close)
        self.now = datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc)
        self.rid = approvals.approval_id(f"{TENANT}:{ME}:s1", "1f0a-checkpoint")

    def open(self, waiting=None, now=None):
        return approvals.open_request(self.db, self.rid, TENANT, ME, "s1", f"{TENANT}:{ME}:s1", "langgraph",
                                      waiting or [ask("withdraw_document", {"name": DOC})], now=now or self.now)

    def test_one_pause_is_one_record_with_one_event(self):
        self.assertEqual(len(self.rid), 32)
        self.assertEqual(approvals.approval_id("t:u:s", "a"), approvals.approval_id("t:u:s", "a"))
        self.assertNotEqual(approvals.approval_id("t:u:s", "a"), approvals.approval_id("t:u:s", "b"))
        rec = self.open()
        again = self.open()
        self.assertEqual((rec["status"], rec["kind"], rec["expire_at"]), ("pending", AP, self.now + timedelta(hours=approvals.TTL_H)))
        self.assertEqual(approvals.TTL_H, 24.0)
        self.assertEqual(again["approval_id"], rec["approval_id"])
        self.assertEqual(len([w for w in self.db.writes if w[0] == f"approvals/{self.rid}"]), 1)   # opened once
        self.assertEqual([(e["action"], e["actor"]["email"], e["target"]) for e in self.events],
                         [(f"{AP}.request", ME, {"approval": self.rid, "tool": "withdraw_document", "document": f"{TENANT}/{DOC}"})])
        self.assertNotIn("question", json.dumps(self.events))
        self.assertEqual(approvals.view(rec)["decide"], f"POST /v1/approvals/{self.rid}/decide")
        self.assertEqual(approvals.view(rec)["document"], f"{TENANT}/{DOC}")
        question = self.open([ask("ask_user", {"question": "Which office?"})])        # the same id: the record above
        self.assertEqual(question["kind"], AP)
        other = approvals.open_request(self.db, approvals.approval_id("acme:asha@example.com:s2", "x"), TENANT, ME, "s2",
                                       "acme:asha@example.com:s2", "langgraph", [ask("ask_user", {"question": "Which office?"})])
        self.assertEqual((other["kind"], len(self.events)), ("answer", 1))             # a question is nobody's approval

    def test_who_may_read(self):
        rec = self.open()
        self.assertEqual(approvals.read(self.db, self.rid, TENANT, ME)["approval_id"], self.rid)          # who asked
        self.assertEqual(approvals.read(self.db, self.rid, TENANT, SECOND, approver=True)["approval_id"], self.rid)
        for tenant, email, approver in ((TENANT, COLLEAGUE, False), ("zeta", ZOE, True), (TENANT, SECOND, False)):
            with self.assertRaises(approvals.ApprovalError) as e:
                approvals.read(self.db, self.rid, tenant, email, approver=approver)
            self.assertEqual((e.exception.status, e.exception.detail), (404, "no such approval"))
        with self.assertRaises(approvals.ApprovalError) as e:
            approvals.read(self.db, "not-an-id", TENANT, ME)
        self.assertEqual(e.exception.status, 404)
        answer = approvals.open_request(self.db, "a" * 32, TENANT, ME, "s3", "acme:asha@example.com:s3", "langgraph",
                                        [ask("ask_user", {"question": "Which office?"})])
        with self.assertRaises(approvals.ApprovalError):                                 # an approver never reads a question
            approvals.read(self.db, "a" * 32, TENANT, SECOND, approver=True)
        self.assertEqual(approvals.read(self.db, "a" * 32, TENANT, ME)["kind"], "answer")
        listed = approvals.list_for(self.db, TENANT, SECOND, approver=True, now=self.now)
        self.assertEqual(([r["approval_id"] for r in listed["pending"]], listed["mine"]), ([self.rid], []))
        mine = approvals.list_for(self.db, TENANT, ME, now=self.now)
        self.assertEqual(sorted(r["approval_id"] for r in mine["mine"]), sorted([self.rid, "a" * 32]))
        self.assertNotIn("pending", mine)
        self.assertEqual(rec["requester"], ME)

    def test_expired_is_410_and_decided_is_409_checked_in_code(self):
        rec = self.open()
        late = self.now + timedelta(hours=approvals.TTL_H)
        self.assertEqual(approvals.decidable(self.db, rec, now=late - timedelta(seconds=1))["status"], "pending")
        with self.assertRaises(approvals.ApprovalError) as e:
            approvals.decidable(self.db, rec, now=late)
        self.assertEqual(e.exception.status, 410)
        self.assertIn("24 hours after the pause", e.exception.detail)
        self.assertEqual(self.db.docs[f"approvals/{self.rid}"]["status"], "expired")       # marked, in code
        self.assertEqual(len(self.events), 1)                                                # no event for expiry
        with self.assertRaises(approvals.ApprovalError) as e:
            approvals.decidable(self.db, approvals.get(self.db, self.rid))
        self.assertEqual(e.exception.status, 409)
        self.assertIn("already expired", e.exception.detail)
        listed = approvals.list_for(self.db, TENANT, ME, now=late)
        self.assertEqual([r["status"] for r in listed["mine"]], ["expired"])

    def test_what_a_decision_amounts_to(self):
        ok = [{"call_id": "c0", "tool": "withdraw_document", "status": "success", "content": "{}"}]
        err = [{**ok[0], "status": "error", "content": "refused"}]
        rec = self.open()
        cases = ((([{"type": "approve"}], SECOND, ok), "approved", f"{AP}.approve", "second_person"),
                 (([{"type": "approve"}], SECOND, err), "failed", f"{AP}.approve", "second_person"),
                 (([{"type": "reject", "message": "no"}], SECOND, err), "rejected", f"{AP}.reject", "second_person"),
                 (([{"type": "reject", "message": ""}], ME, err), "cancelled", f"{AP}.reject", "requester"))
        for (decisions, by, results), status, action, who in cases:
            with self.subTest(status=status):
                self.assertEqual(approvals.status_of(rec, decisions, by, results), status)
                n = len(self.events)
                settled = approvals.settle(self.db, dict(rec), decisions, by, results, {"answer": "ok", "tool_calls": [], "refusals": []},
                                           now=self.now)
                self.assertEqual((settled["status"], settled["decided_by"], settled["decided_at"]), (status, by, self.now))
                self.assertEqual((self.events[n]["action"], self.events[n]["actor"]["email"], self.events[n]["meta"]),
                                 (action, by, {"status": status, "by": who}))
        answer = approvals.open_request(self.db, "b" * 32, TENANT, ME, "s4", "acme:asha@example.com:s4", "langgraph",
                                        [ask("ask_user", {"question": "Which office?"})])
        n = len(self.events)
        settled = approvals.settle(self.db, answer, [{"type": "respond", "message": "Pune"}], ME,
                                   [{"call_id": "c0", "tool": "ask_user", "status": "success", "content": "Pune"}],
                                   {"answer": "Pune it is.", "tool_calls": [], "refusals": []})
        self.assertEqual((settled["status"], len(self.events)), ("answered", n))         # an answer writes no event
        self.assertEqual(approvals.lost(self.db, dict(rec))["status"], "lost")
        self.assertEqual(approvals.lost(self.db, settled)["status"], "answered")          # only a pending record is lost

    def test_the_executor_records_and_withdraws_nothing(self):
        rec = self.open()
        withdraw = approvals.executor(self.db, self.rid)
        done = withdraw(tenant=TENANT, name=DOC, requested_by=ME, approved_by=SECOND)
        self.assertEqual((done["status"], done["approval"]), ("approved", self.rid))
        self.assertIn(f"make withdraw-run APPROVAL={self.rid}", done["next"])
        w = self.db.docs[f"approvals/{self.rid}"]["withdrawal"]
        self.assertEqual((w["tenant"], w["name"], w["requested_by"], w["approved_by"]), (TENANT, DOC, ME, SECOND))
        self.assertEqual(self.db.docs[f"approvals/{self.rid}"]["status"], "pending")      # settle() decides the status
        with self.assertRaises(ValueError):                                                 # not this conversation's
            withdraw(tenant="zeta", name=DOC, requested_by=ME, approved_by=SECOND)
        with self.assertRaises(ValueError):
            approvals.executor(self.db, "c" * 32)(tenant=TENANT, name=DOC, requested_by=ME, approved_by=SECOND)
        self.assertEqual(rec["status"], "pending")

    def test_recheck_refuses_before_the_tombstone(self):
        rec = self.open()
        refusals = {}

        def refused(rid):
            try:
                approvals.recheck(self.db, rid)
            except approvals.ApprovalError as e:
                return e.status, e.detail
            return None

        refusals["unknown"] = refused("d" * 32)
        refusals["pending"] = refused(self.rid)
        approvals.executor(self.db, self.rid)(tenant=TENANT, name=DOC, requested_by=ME, approved_by=SECOND)
        rec = approvals.settle(self.db, approvals.get(self.db, self.rid), [{"type": "approve"}], SECOND,
                               [{"call_id": "c0", "tool": "withdraw_document", "status": "success", "content": "{}"}],
                               {"answer": "queued", "tool_calls": ["withdraw_document"], "refusals": []})
        self.assertEqual(approvals.recheck(self.db, self.rid)["status"], "approved")       # the checks pass
        roles.role_ref(self.db, TENANT, SECOND).set({"roles": ["employee"]})                # the role revoked since
        refusals["revoked"] = refused(self.rid)
        roles.role_ref(self.db, TENANT, SECOND).set({"roles": ["employee", "doc_approver"]})
        self.db.docs[f"approvals/{self.rid}"]["withdrawal"]["approved_by"] = ME             # a forged self-approval
        refusals["self"] = refused(self.rid)
        self.db.docs[f"approvals/{self.rid}"]["withdrawal"]["approved_by"] = SECOND
        self.db.docs[f"approvals/{self.rid}"]["withdrawal"]["tenant"] = "zeta"              # another company's document
        refusals["tenant"] = refused(self.rid)
        self.db.docs[f"approvals/{self.rid}"]["withdrawal"]["tenant"] = TENANT
        self.db.fail_reads = True
        refusals["unread"] = refused(self.rid)
        self.db.fail_reads = False
        done = approvals.withdrawn(self.db, approvals.get(self.db, self.rid), run_by="ops@example.com", now=self.now)
        self.assertEqual((done["status"], done["run_by"], done["withdrawn_at"]), ("withdrawn", "ops@example.com", self.now))
        self.assertEqual((self.events[-1]["action"], self.events[-1]["actor"]["email"], self.events[-1]["meta"]),
                         ("doc.withdraw", "ops@example.com", {"approved_by": SECOND, "requested_by": ME}))
        refusals["again"] = refused(self.rid)
        self.assertEqual({k: v[0] for k, v in refusals.items()},
                         {"unknown": 404, "pending": 409, "revoked": 403, "self": 403, "tenant": 409, "unread": 503, "again": 409})
        self.assertIn("no longer holds doc_approver", refusals["revoked"][1])
        self.assertIn("was not approved by a second person", refusals["self"][1])
        self.assertIn("was already run", refusals["again"][1])
        self.assertEqual(rec["status"], "approved")

    def test_an_event_the_bucket_refused_waits_on_the_record(self):
        boom = types.SimpleNamespace(Client=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("bucket down")))
        with patch.object(tc.audit_log, "storage", boom), patch.object(tc.audit_log, "_bucket", None):
            rec = self.open()
        self.assertEqual((self.events, [e["action"] for e in rec["audit_pending"]]), ([], [f"{AP}.request"]))
        self.assertEqual([e["action"] for e in self.db.docs[f"approvals/{self.rid}"]["audit_pending"]], [f"{AP}.request"])
        with patch.object(tc.audit_log, "_bucket", None):                                   # the bucket is back
            settled = approvals.settle(self.db, approvals.get(self.db, self.rid), [{"type": "reject", "message": "no"}], SECOND,
                                       [{"call_id": "c0", "tool": "withdraw_document", "status": "error", "content": "x"}],
                                       {"answer": "nothing was done", "tool_calls": [], "refusals": ["withdraw_document"]})
        self.assertEqual([e["action"] for e in self.events], [f"{AP}.request", f"{AP}.reject"])   # oldest first
        self.assertEqual((settled["audit_pending"], self.db.docs[f"approvals/{self.rid}"]["audit_pending"]), ([], []))


# ------------------------------------------------------------------ the chat service, in the chat image's pins
@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class WiredService(unittest.TestCase):
    """agent.py's app on the gcp profile over a fake Firestore: the switch read from tenant_settings, the approval
    brain on a scripted model, rag-api standing in, the audit bucket recording."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.CRITICAL)
        with patch.dict(os.environ, {"CHECKPOINT_DSN": "memory"}):
            sys.modules.pop("agent", None)
            import agent
        import approval
        import approval_routes
        import brains
        import desk
        import shared.documind_tools as dt
        from fastapi.testclient import TestClient
        from shared import iap
        cls.agent, cls.approval, cls.routes, cls.brains, cls.desk, cls.dt, cls.TestClient, cls.iap = (
            agent, approval, approval_routes, brains, desk, dt, TestClient, iap)
        cls.searched = []

        def stand_in_retrieve(query, tenant_id="", top_k=5, doc_type=None, assertion=None, brain=None, **kw):
            cls.searched.append((tenant_id, query))
            return {"answer": "rag-api's own answer", "answerable": True, "confidence": "high",
                    "citations": [{"chunk_id": "acme:np#0", "source_uri": f"gs://b/acme/{DOC}", "page": 1,
                                   "quote": "a town hall", "score": 0.9}]}
        cls.saved_retrieve, dt.retrieve = dt.retrieve, stand_in_retrieve

    @classmethod
    def tearDownClass(cls):
        cls.dt.retrieve = cls.saved_retrieve
        logging.disable(logging.NOTSET)

    def lane(self, actions="approval"):
        """The chat service with acme's agent_actions as given, and the people on their rosters."""
        db = tc.FakeDB()
        roster(db, {ME: (TENANT, None), SECOND: (TENANT, ["employee", "doc_approver"]), COLLEAGUE: (TENANT, None),
                    ZOE: ("zeta", ["employee", "doc_approver"])})
        db.collection("tenant_settings").document(TENANT).set({"agent_actions": actions, "case_queues": tc.queues_file("acme")})
        tenants = {ME: TENANT, SECOND: TENANT, COLLEAGUE: TENANT, ZOE: "zeta"}
        events, rows = [], []

        def identity(headers, bearer_audience=None):
            email = headers.get("x-test-email")
            if not email:
                raise self.iap.IapError("no identity: neither an IAP assertion nor a bearer token")
            return {"email": email, "via": "bearer"}

        def tenant_for(email):
            return tenants.get(email)

        def settings(tenant):
            return dict(db.docs.get(f"tenant_settings/{tenant}") or {})

        def row(message):                                   # the resumed turn's row (logging is off in these tests)
            rows.append(json.loads(message))

        stack = contextlib.ExitStack()
        for p in (patch.object(self.routes.log, "info", row),
                  patch.object(self.iap, "identity", identity), patch.object(self.agent, "PROFILE", "gcp"),
                  patch.object(self.desk, "PROFILE", "gcp"), patch.object(self.routes, "PROFILE", "gcp"),
                  patch.object(self.agent, "tenant_for", tenant_for),
                  patch.dict(self.desk._hooks, {"tenant_for": tenant_for}), patch.dict(self.routes._hooks, {"tenant_for": tenant_for}),
                  patch.object(self.desk, "settings", settings), patch.object(self.desk, "_client", lambda: db),
                  patch.object(self.desk, "CHECKED", tc._OnTenants(set())),
                  patch.object(self.desk, "SHADOWING", tc.desk_recall.OnTenants(frozenset, self.desk.log, "test")),
                  patch.object(tc.audit_log, "storage", tc._storage(events)), patch.object(tc.audit_log, "_bucket", None),
                  patch.dict(os.environ, {"AUDIT_BUCKET": "documind-ai-YOUR-ID-audit"})):
            stack.enter_context(p)
        self.addCleanup(stack.close)
        self.agent.app.state.approval_brain = None          # built on first use, as on a lane: each test starts without one
        return self.TestClient(self.agent.app), db, events, rows

    def brain(self, client, script):
        """The approval brain on the service's checkpointer, replying as scripted. chat() builds the plain LangGraph
        brain first (brain_for), as on a lane, so it is given a scripted model too; wired() never answers with it."""
        saver = client.app.state.checkpointer
        client.app.state.approval_brain = self.routes.ApprovalBrain(saver, llm=ta.scripted(script))
        client.app.state.brains = {"langgraph": self.brains.LangGraphBrain(saver, llm=ta.scripted([]))}

    @staticmethod
    def chat(client, who, question, session="s1"):
        r = client.post("/v1/chat", json={"question": question, "session_id": session, "brain": "langgraph"},
                        headers={"x-test-email": who})
        return r.status_code, r.json()

    @staticmethod
    def decide(client, who, rid, kind, message=""):
        r = client.post(f"/v1/approvals/{rid}/decide", json={"decisions": [{"type": kind, "message": message}]},
                        headers={"x-test-email": who})
        return r.status_code, r.json()

    def withdraw_turn(self, final="The withdrawal is approved and queued for the operator."):
        return ta.turn([("withdraw_document", {"name": DOC})], final)

    def test_switch_off_is_the_brain_lessons_5_4_and_5_7_show(self):
        client, db, events, rows = self.lane(actions="off")
        with client:
            client.app.state.brains = {"langgraph": self.brains.LangGraphBrain(client.app.state.checkpointer,
                                                                               llm=ta.scripted(ta.turn([("delete_document", {"name": DOC})], "Refused.")))}
            self.assertIsNone(client.app.state.approval_brain)
            status, body = self.chat(client, ME, f"Delete {DOC}")
            self.assertEqual((status, body["refusals"], body.get("approval")), (200, ["delete_document"], None))
            self.assertIsNone(client.app.state.approval_brain)                                   # never built
            self.assertEqual([k for k in db.docs if k.startswith("approvals/")], [])
            self.assertEqual(client.get("/v1/approvals", headers={"x-test-email": ME}).json(), {"mine": [], "approver": False})
        from langgraph.checkpoint.memory import InMemorySaver
        graph = self.brains.LangGraphBrain(InMemorySaver(), llm=ta.scripted([])).graph.get_graph()
        self.assertEqual(list(graph.nodes), ["__start__", "agent", "tools", "refuse", "__end__"])   # the refuse node stays
        self.assertEqual(sorted(self.brains.BLOCKED), ["delete_document", "modify_access", "send_email"])
        self.assertEqual(events, [])

    def test_a_withdrawal_pauses_is_held_refused_to_its_requester_and_approved_by_a_second_person(self):
        client, db, events, rows = self.lane()
        with client:
            self.brain(client, self.withdraw_turn())
            status, body = self.chat(client, ME, f"Withdraw the document {DOC} from search.")
            self.assertEqual(status, 200)
            rec = body["approval"]
            rid = rec["approval_id"]
            self.assertEqual((rec["status"], rec["kind"], rec["requester"], rec["document"], body["tool_calls"], body["refusals"]),
                             ("pending", AP, ME, f"{TENANT}/{DOC}", ["withdraw_document"], []))
            self.assertEqual([w["tool"] for w in rec["waiting"]], ["withdraw_document"])
            self.assertIn(f"Approval {rid} (POST /v1/approvals/{rid}/decide) waits until {rec['expire_at']}", body["answer"])
            self.assertEqual((body["brain"], body["session_id"], body["limits"]["model_calls"]), ("langgraph", "s1", 1))
            self.assertEqual([e["action"] for e in events], [f"{AP}.request"])
            self.assertEqual(events[0]["actor"], {"tenant_id": TENANT, "email": ME})
            # the hold: the same conversation takes no new question; another session runs
            status, body = self.chat(client, ME, "What is my notice period?")
            self.assertEqual(status, 409)
            self.assertIn(f"approval {rid} (withdraw_document)", body["detail"])
            self.assertEqual(db.docs[f"approvals/{rid}"]["status"], "pending")
            # four eyes, and who may see it
            self.assertEqual(self.decide(client, ME, rid, "approve")[0], 403)
            self.assertEqual(client.get(f"/v1/approvals/{rid}", headers={"x-test-email": ZOE}).status_code, 404)
            self.assertEqual(client.get(f"/v1/approvals/{rid}", headers={"x-test-email": COLLEAGUE}).status_code, 404)
            self.assertEqual(self.decide(client, COLLEAGUE, rid, "approve")[0], 404)
            self.assertEqual(self.decide(client, SECOND, rid, "respond", "x")[0], 422)             # the wrong kind
            self.assertEqual(client.get(f"/v1/approvals/{rid}", headers={"x-test-email": SECOND}).json()["status"], "pending")
            inbox = client.get("/v1/approvals", headers={"x-test-email": SECOND}).json()
            self.assertEqual(([r["approval_id"] for r in inbox["pending"]], inbox["approver"], inbox["mine"]), ([rid], True, []))
            self.assertEqual(client.get("/v1/approvals", headers={"x-test-email": ME}).json()["mine"][0]["status"], "pending")
            # the second person approves: the turn resumes for the person who asked; the executor records it
            status, body = self.decide(client, SECOND, rid, "approve")
            self.assertEqual(status, 200, body)
            rec, turn = body["approval"], body["turn"]
            self.assertEqual((rec["status"], rec["decided_by"], rec["decisions"]), ("approved", SECOND, [{"type": "approve", "message": ""}]))
            self.assertEqual((rec["withdrawal"]["requested_by"], rec["withdrawal"]["approved_by"], rec["withdrawal"]["name"]), (ME, SECOND, DOC))
            self.assertEqual((turn["tool_calls"], turn["refusals"], turn["answer"]),
                             (["withdraw_document"], [], "The withdrawal is approved and queued for the operator."))
            self.assertEqual((turn["brain"], turn["session_id"], turn["limits"]["model_calls"]), ("langgraph", "s1", 1))
            self.assertEqual(rec["results"][0]["status"], "success")
            self.assertIn(f"make withdraw-run APPROVAL={rid}", rec["results"][0]["content"])
            self.assertEqual([e["action"] for e in events], [f"{AP}.request", f"{AP}.approve"])
            self.assertEqual(events[1]["meta"], {"status": "approved", "by": "second_person"})
            self.assertEqual([(r["surface"], r["user"], r["approval"], r["decided_by"], r["model_calls"], r["status"]) for r in rows],
                             [("approval", ME, rid, SECOND, 1, "approved")])
            self.assertEqual(set(rows[0]) - {"approval", "decided_by", "status"},
                             {"event", "surface", "brain", "tenant", "user", "session_id", "latency_ms", "tool_calls", "refusals",
                              "model", "model_calls", "tokens_in", "tokens_out", "cached_tokens", "cost_usd", "rag_cost_usd",
                              "stopped_by", "tool_timeouts", "max_model_calls", "budget_inr"})      # agent.chat()'s row, plus three
            # decided once, and the conversation goes on
            status, body = self.decide(client, SECOND, rid, "approve")
            self.assertEqual((status, "already approved" in body["detail"]), (409, True))
            self.brain(client, ta.turn([("retrieve", {"query": "notice period"})], "Sixty days [1]."))
            status, body = self.chat(client, ME, "What is my notice period?")
            self.assertEqual((status, body["tool_calls"], body.get("approval")), (200, ["retrieve"], None))
            self.assertEqual(client.get(f"/v1/approvals/{rid}", headers={"x-test-email": ME}).json()["status"], "approved")

    def test_a_rejection_errors_that_call_alone_and_the_requester_may_cancel(self):
        client, db, events, rows = self.lane()
        with client:
            self.brain(client, ta.turn([("retrieve", {"query": "town hall"}), ("withdraw_document", {"name": DOC})],
                                       "Nothing was withdrawn; the town hall said revenue grew [1]."))
            before = len(self.searched)
            status, body = self.chat(client, ME, f"Withdraw {DOC} and tell me what it said.")
            rid = body["approval"]["approval_id"]
            self.assertEqual((status, body["tool_calls"], len(self.searched)), (200, ["retrieve", "withdraw_document"], before))
            status, body = self.decide(client, SECOND, rid, "reject", "That transcript is still in force.")
            self.assertEqual(status, 200, body)
            self.assertEqual((body["approval"]["status"], body["turn"]["refusals"], len(self.searched)), ("rejected", ["withdraw_document"], before + 1))
            self.assertIn("still in force", body["approval"]["results"][0]["content"])
            self.assertEqual(events[-1]["meta"], {"status": "rejected", "by": "second_person"})
            self.assertEqual(db.docs[f"approvals/{rid}"]["withdrawal"], None)
            # the requester's own reject: their cancel
            self.brain(client, self.withdraw_turn("Cancelled, as you asked."))
            status, body = self.chat(client, ME, f"Withdraw {DOC}.", session="s2")
            rid2 = body["approval"]["approval_id"]
            self.assertNotEqual(rid2, rid)
            status, body = self.decide(client, ME, rid2, "reject")
            self.assertEqual((status, body["approval"]["status"], body["turn"]["answer"]), (200, "cancelled", "Cancelled, as you asked."))
            self.assertEqual(events[-1]["meta"], {"status": "cancelled", "by": "requester"})
            self.assertEqual([r["status"] for r in rows], ["rejected", "cancelled"])

    def test_a_question_is_the_requesters_alone(self):
        client, db, events, rows = self.lane()
        with client:
            self.brain(client, ta.turn([("ask_user", {"question": "Which office are you in?"})], "Pune's notice period is 60 days."))
            status, body = self.chat(client, ME, "What is my notice period?")
            rec = body["approval"]
            rid = rec["approval_id"]
            self.assertEqual((status, rec["kind"], rec["status"], body["tool_calls"]), (200, "answer", "pending", ["ask_user"]))
            self.assertIn("DocuMind needs one fact from you before it can answer: Which office are you in?", body["answer"])
            self.assertEqual(events, [])                                                         # nobody's approval
            self.assertEqual(client.get(f"/v1/approvals/{rid}", headers={"x-test-email": SECOND}).status_code, 404)
            self.assertEqual(client.get("/v1/approvals", headers={"x-test-email": SECOND}).json()["pending"], [])
            self.assertEqual(self.decide(client, SECOND, rid, "respond", "Pune")[0], 404)
            self.assertEqual(self.decide(client, ME, rid, "approve")[0], 422)
            status, body = self.decide(client, ME, rid, "respond", "Pune")
            self.assertEqual((status, body["approval"]["status"], body["turn"]["answer"]), (200, "answered", "Pune's notice period is 60 days."))
            self.assertEqual(body["approval"]["results"], [{"call_id": "c0", "tool": "ask_user", "status": "success", "content": "Pune"}])
            self.assertEqual(events, [])

    def test_an_expired_record_is_410_and_the_hold_then_lets_the_next_question_through(self):
        client, db, events, rows = self.lane()
        with client:
            # the model's replies, in order: the withdrawal's call; its answer once the hold has ended the expired pause as the
            # requester's own cancel; then the next question's search and answer
            self.brain(client, self.withdraw_turn("Nothing was withdrawn: the approval expired.")
                       + ta.turn([("retrieve", {"query": "notice"})], "Sixty days [1]."))
            status, body = self.chat(client, ME, f"Withdraw {DOC}.")
            rid = body["approval"]["approval_id"]
            db.docs[f"approvals/{rid}"]["expire_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
            status, body = self.decide(client, SECOND, rid, "approve")
            self.assertEqual((status, "expired at" in body["detail"]), (410, True))
            self.assertEqual(db.docs[f"approvals/{rid}"]["status"], "expired")
            self.assertEqual(self.decide(client, SECOND, rid, "approve")[0], 409)                  # decided: expired
            status, body = self.chat(client, ME, "What is my notice period?")                       # the hold ends the pause
            self.assertEqual((status, body["tool_calls"], body["answer"]), (200, ["retrieve"], "Sixty days [1]."))
            self.assertEqual(self.approval.paused(client.app.state.approval_brain.graph,
                                                  self.agent.thread_config(TENANT, ME, "s1")), [])
            msgs = client.app.state.approval_brain.graph.get_state(self.agent.thread_config(TENANT, ME, "s1")).values["messages"]
            ended = [m for m in msgs if getattr(m, "tool_call_id", None) == "c0" and m.name == "withdraw_document"]
            self.assertEqual((len(ended), ended[0].status), (1, "error"))
            self.assertEqual(json.loads(ended[0].content)["error"],                     # the approve node's own result
                             "withdraw_document was cancelled by the person who asked for it, so nothing was done")
            self.assertIn("the approval expired before a decision came", json.loads(ended[0].content)["their_reason"])
            self.assertEqual([(r["status"], r["decided_by"], r["model_calls"]) for r in rows], [("expired", ME, 1)])   # one row, one call
            self.assertEqual([e["action"] for e in events], [f"{AP}.request"])

    def test_a_pause_that_is_gone_is_lost(self):
        client, db, events, rows = self.lane()
        with client:
            self.brain(client, self.withdraw_turn())
            status, body = self.chat(client, ME, f"Withdraw {DOC}.")
            rid = body["approval"]["approval_id"]
            graph, config = client.app.state.approval_brain.graph, self.agent.thread_config(TENANT, ME, "s1")
            self.routes.limits.repair_thread(graph, config, as_node="approve")              # the pause is gone (a repair)
            status, body = self.decide(client, SECOND, rid, "approve")
            self.assertEqual((status, "is now lost" in body["detail"], db.docs[f"approvals/{rid}"]["status"]), (409, True, "lost"))

    def test_offer_case_reaches_the_response_and_writes_nothing(self):
        client, db, events, rows = self.lane()
        with client:
            self.brain(client, ta.turn([("offer_case", {"case_type": "people_query"})], "The People team can help: press Raise a case."))
            n = len(db.writes)
            status, body = self.chat(client, ME, "Who do I talk to about my payslip?")
            self.assertEqual((status, body["tool_calls"], body["refusals"], body.get("case_offer")),
                             (200, ["offer_case"], [], {"case_type": "people_query"}))
            self.assertEqual((len(db.writes), body.get("approval"), events), (n, None, []))

    def test_reconcile_approved_runs_on_the_record(self):
        import reconcile
        client, db, events, rows = self.lane()
        with client:
            self.brain(client, self.withdraw_turn())
            rid = self.chat(client, ME, f"Withdraw {DOC}.")[1]["approval"]["approval_id"]
            self.assertEqual(self.decide(client, SECOND, rid, "approve")[0], 200)
        fs = types.SimpleNamespace(Client=lambda project=None: db, SERVER_TIMESTAMP="SERVER_TIMESTAMP", DELETE_FIELD=tc.DELETE)
        storage = tc._storage(events)
        seen = []

        def run(*argv):
            real = reconcile.main

            def reenter():
                seen.append(list(sys.argv))
                return 0
            with tc.cloud_modules(firestore=fs, storage=storage), patch.object(tc.audit_log, "_bucket", None), \
                    patch.dict(os.environ, {"DOCUMIND_OPERATOR": "ops@example.com", "AUDIT_BUCKET": "documind-ai-YOUR-ID-audit"}), \
                    patch.object(sys, "argv", ["reconcile.py", "--project", "documind-ai-YOUR-ID", *argv]), \
                    patch.object(reconcile, "main", reenter), redirect_stdout(io.StringIO()) as out:
                code = real()
            return code, out.getvalue()

        code, out = run("--approved", "e" * 32)
        self.assertEqual((code, json.loads(out)["event"], json.loads(out)["status"]), (1, "reconcile_approved_refused", 404))
        code, out = run("--approved", rid)
        self.assertEqual(code, 0)
        self.assertIn(f"would run approval {rid}: withdraw {TENANT}/{DOC}, asked for by {ME}, approved by {SECOND}", out)
        self.assertEqual((seen, db.docs[f"approvals/{rid}"]["status"]), ([], "approved"))
        code, out = run("--approved", rid, "--apply")
        self.assertEqual(code, 0, out)
        self.assertEqual(seen, [["reconcile.py", "--project", "documind-ai-YOUR-ID", "--retire", f"{TENANT}/{DOC}", "--apply"]])
        line = json.loads(out)
        self.assertEqual((line["event"], line["status"], line["run_by"], line["undo"]),
                         ("reconcile_approved", "withdrawn", "ops@example.com", f"make restore SOURCE={TENANT}/{DOC}"))
        self.assertEqual([e["action"] for e in events], [f"{AP}.request", f"{AP}.approve", "doc.withdraw"])
        self.assertEqual(events[-1]["actor"], {"tenant_id": TENANT, "email": "ops@example.com"})
        code, out = run("--approved", rid, "--apply")
        self.assertEqual((code, json.loads(out)["status"]), (1, 409))                           # run once


if __name__ == "__main__":
    unittest.main()
