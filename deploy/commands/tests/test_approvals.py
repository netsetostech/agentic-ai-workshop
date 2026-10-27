"""Offline checks for workshop lesson 5.8's person in the loop: services/chat/approval.py, which the chat service reaches
through one module, services/chat/approval_routes.py, behind tenant_settings.agent_actions = approval (off until an
operator sets it; commands/tests/test_approval_wired.py covers that side).

    python -m unittest commands/tests/test_approvals.py -v          # from deploy/
    make approval-check                                              # the same, in ~/graph-venv with the pins

The first class needs only the standard library: one module in the service imports approval.py, it writes no audit
event (workshop lesson 4.8 counts every emitter), and make, its script and both CI chat-pins steps run this file. The
second runs the module on scripted models, a stand-in rag-api and a fake Firestore that records any write: the pause;
a second process resuming the turn from the same SqliteSaver file; the requester's own approval refused; a rejection
that errors that call alone; a question the person who asked answers; a case offered with nothing written; the
approval line a resume writes twice once it sits above interrupt() (the page's Change-it); and the same pause as
LangChain middleware. It needs the chat image's pins (pip install -r services/chat/requirements.txt) and the local
lane's langgraph-checkpoint-sqlite pin (services/chat/requirements-local.txt). Without them it is skipped and says so;
with DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins step sets it, a missing pin is an error instead.
"""
import importlib.util
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import types
import unittest
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KIT = Path(__file__).resolve().parents[2]
SRC = (KIT / "services/chat/approval.py").read_text(encoding="utf-8")
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
TENANT, ASKER, SECOND, OTHER = "acme", "asha@example.com", "ravi@example.com", "meena@example.com"
DOC = "hr_policy_2026.md"
LOGGER = "documind.chat.approval"


def _found(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


FRAMEWORKS = all(_found(m) for m in ("langchain", "langgraph", "langgraph.checkpoint.sqlite"))


def cfg(session: str) -> dict:
    """ASKER's conversation, as agent.thread_config() builds its config: tenant:user:session."""
    return {"configurable": {"thread_id": f"{TENANT}:{ASKER}:{session}"}}


def scripted(responses: list):
    """A chat model that answers with these messages in turn; bind_tools hands back the same model."""
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel

    class Script(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kw):
            return self

    return Script(responses=responses)


def turn(calls: list, final: str = "done") -> list:
    """One user turn: a model message asking for these (tool, args) calls, then the model's answer."""
    from langchain_core.messages import AIMessage
    return [AIMessage("", tool_calls=[{"name": n, "args": a, "id": f"c{i}"} for i, (n, a) in enumerate(calls)]),
            AIMessage(final)]


def withdrawer():
    """The injected executor: it records the withdrawal it was asked for and withdraws nothing."""
    calls = []

    def withdraw(**kw):
        calls.append(kw)
        return {"status": "withdrawal_started"}
    return calls, withdraw


# ------------------------------------------------------------------ a fake Firestore that reads, and records any write
class Snap:
    def __init__(self, data):
        self._d, self.exists = data, data is not None

    def to_dict(self):
        return dict(self._d or {})


class Ref:
    def __init__(self, db, path):
        self.db, self.path = db, path

    def get(self, transaction=None):
        self.db.reads.append(self.path)
        return Snap(self.db.docs.get(self.path))

    def collection(self, name):
        return Col(self.db, f"{self.path}/{name}")

    def __getattr__(self, name):
        if name in ("set", "update", "create", "delete"):
            return lambda *a, **k: self.db.writes.append((name, self.path))
        raise AttributeError(name)


class Col:
    def __init__(self, db, path):
        self.db, self.path = db, path

    def document(self, id_):
        return Ref(self.db, f"{self.path}/{id_}")


class ReadOnlyDb:
    def __init__(self, docs):
        self.docs, self.reads, self.writes = dict(docs), [], []

    def collection(self, name):
        return Col(self, name)

    def batch(self):
        self.writes.append(("batch", ""))

    def transaction(self):
        self.writes.append(("transaction", ""))


def roster(roles_of: dict) -> ReadOnlyDb:
    """acme's roster: everyone named is a member; their value is their role document's roles (None: no document)."""
    docs = {}
    for email, held in roles_of.items():
        docs[f"tenants/{TENANT}/members/{email}"] = {"email": email}
        if held is not None:
            docs[f"tenants/{TENANT}/roles/{email}"] = {"roles": held}
    return ReadOnlyDb(docs)


def acme_queues() -> dict:
    return json.loads((KIT / "evals" / "desk" / "queues.acme.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ the second process (see the sqlite test)
def _second_process(db_path: str, record: str) -> None:
    """Resume the paused turn from db_path in this new process: a new graph object on the same SQLite file, the
    second person's approval through decide(), the withdrawal recorded to `record`. Prints one JSON line."""
    warnings.filterwarnings("ignore")
    sys.path[:0] = [str(KIT), str(KIT / "services/chat")]
    import approval
    from langchain_core.messages import AIMessage
    from langgraph.checkpoint.sqlite import SqliteSaver

    asked = []

    class Lines(logging.Handler):
        def emit(self, record_):
            asked.append(record_.getMessage())

    log = logging.getLogger(LOGGER)
    log.addHandler(Lines())
    log.setLevel(logging.INFO)

    def withdraw(**kw):
        with open(record, "a", encoding="utf-8") as f:
            f.write(json.dumps(kw) + "\n")
        return {"status": "withdrawal_started"}

    with SqliteSaver.from_conn_string(db_path) as saver:
        graph = approval.build_approval_graph(scripted([AIMessage("Withdrawn, from the second process.")]), saver)
        out = approval.decide(graph, cfg("sqlite"), [{"type": "approve"}], by=SECOND, context={"withdraw": withdraw})
        waiting = approval.paused(graph, cfg("sqlite"))
    print(json.dumps({"answer": out["messages"][-1].content, "asked": asked, "waiting": waiting}))


# ------------------------------------------------------------------ the standard library half
class Wiring(unittest.TestCase):
    def read(self, *parts) -> str:
        return KIT.joinpath(*parts).read_text(encoding="utf-8")

    def test_one_module_in_the_service_imports_it_behind_the_switch(self):
        """Since 13 October 2026 (workshop lesson 5.8's wired approval) approval_routes.py imports the module, and
        agent.py reaches it through that module alone, behind tenant_settings.agent_actions = approval."""
        importers = [p.relative_to(KIT).as_posix() for p in (KIT / "services").rglob("*.py")
                     if p.name != "approval.py" and "__pycache__" not in p.parts
                     and re.search(r"^\s*(?:from approval import|import approval\b)", p.read_text(encoding="utf-8"), re.M)]
        self.assertEqual(importers, ["services/chat/approval_routes.py"])
        self.assertIn("THE SERVICE REACHES THIS MODULE THROUGH ONE SWITCH, OFF UNTIL AN OPERATOR SETS IT.", SRC)
        self.assertIn('SWITCH, ON = "agent_actions", "approval"', self.read("services", "chat", "approval_routes.py"))

    def test_it_writes_no_audit_event(self):
        """Workshop lesson 4.8 lists every audit action the kit writes, from the emit literals in its runtime files
        (this one included): the module adds none."""
        literal = re.compile(r'(?:audit_emit|audit_log\.emit|\bemit)\("([a-z_.]+)"')
        for src in (SRC, Path(__file__).read_text(encoding="utf-8")):
            self.assertEqual(literal.findall(src), [])
        self.assertNotIn("audit_log", SRC)

    def test_the_versions_it_was_verified_against_are_the_pins(self):
        reqs = self.read("services", "chat", "requirements.txt") + self.read("services", "chat", "requirements-local.txt")
        for name, version in (("langchain", "1.4.0"), ("langgraph", "1.2.12"), ("langgraph-checkpoint-sqlite", "3.1.1")):
            self.assertRegex(reqs, rf"(?m)^{re.escape(name)}=={re.escape(version)}$")
            self.assertIn(f"{name} {version}", " ".join(SRC.split()))

    def test_make_its_script_and_ci_run_this_file(self):
        mk, agents, readme = self.read("Makefile"), self.read("mk", "agents.mk"), self.read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                     # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        self.assertIn("approval-check", phony)
        self.assertIn("\napproval-check:\n\t@PY=$(PY) bash commands/approval-check.sh\n", agents)  # not last
        self.assertLess(agents.index("\nroute-eval: guard-project\n"), agents.index("\napproval-check:"))  # appended
        self.assertIn("`approval-check`", readme)
        self.assertIn("`approval-check.sh`", readme)
        sh = self.read("commands", "approval-check.sh")
        self.assertIn("grep -E '^langgraph-checkpoint-sqlite==' services/chat/requirements-local.txt", sh)
        self.assertIn('"$VENV/bin/pip" install -q -r services/chat/requirements.txt "$SQLITE"', sh)
        self.assertIn('DOCUMIND_REQUIRE_LIBS=1 "$VENV/bin/python" -m unittest commands/tests/test_approvals.py -v', sh)
        pin = ("/tmp/chat-venv/bin/pip install -q "
               "\"$(grep -E '^langgraph-checkpoint-sqlite==' services/chat/requirements-local.txt)\"")
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_approvals.py -v"
        workflows = [self.read(".github", "workflows", "documind-dryrun.yml")]
        repo_ci = KIT.parent / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                            # the authoring repository's own CI
            workflows.append(repo_ci.read_text(encoding="utf-8"))
        for wf in workflows:
            self.assertIn(f"{pin}\n          {line}\n", wf)


# ------------------------------------------------------------------ the module itself, in the chat image's pins
@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins and langgraph-checkpoint-sqlite: "
                     "pip install -r services/chat/requirements.txt langgraph-checkpoint-sqlite==3.1.1")
class Approvals(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        sys.path[:0] = [str(KIT), str(KIT / "services/chat")]
        import approval
        import shared.documind_tools as dt
        import tools
        from langchain_core.messages import HumanMessage, ToolMessage
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.types import Command
        cls.approval, cls.dt, cls.tools = approval, dt, tools
        cls.HumanMessage, cls.ToolMessage, cls.InMemorySaver, cls.Command = HumanMessage, ToolMessage, InMemorySaver, Command
        cls.searched = searched = []

        class Api(BaseHTTPRequestHandler):                  # rag-api, standing in: one passage for any question
            def log_message(self, *a):
                pass

            def do_POST(self):
                req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                searched.append((req["tenant_id"], req["query"]))
                data = json.dumps({"answer": "rag-api's own answer", "answerable": True, "confidence": "high",
                                   "citations": [{"chunk_id": "acme:np#0", "source_uri": f"gs://b/acme/{DOC}",
                                                  "page": 1, "quote": "a notice period", "score": 0.9}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Api)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.saved = (dt.RAG_API_URL, dt._id_token)
        dt.RAG_API_URL, dt._id_token = f"http://127.0.0.1:{cls.srv.server_address[1]}", lambda aud: "TOKEN"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.dt.RAG_API_URL, cls.dt._id_token = cls.saved

    # helpers
    def graph(self, script: list, saver=None, module=None):
        return (module or self.approval).build_approval_graph(scripted(script), saver or self.InMemorySaver())

    def ask(self, agent, session: str, context: dict | None = None, question: str = f"Withdraw {DOC}"):
        return agent.invoke({"messages": [self.HumanMessage(question)]}, cfg(session), context=context or {})

    def results(self, out) -> dict:
        return {m.name: m for m in out["messages"] if isinstance(m, self.ToolMessage)}

    def refusals(self, out) -> list:
        return [m.name for m in out["messages"] if isinstance(m, self.ToolMessage) and m.status == "error"]

    @staticmethod
    def path(agent, config) -> list:
        """The node each checkpoint says runs next, oldest first: the turn's path through the graph."""
        return [s.next for s in reversed(list(agent.get_state_history(config)))]

    def withdraw_turn(self, final: str = "The withdrawal is done."):
        return turn([("withdraw_document", {"name": DOC})], final)

    # the pause
    def test_the_graph_pauses_for_a_second_person_and_resumes_on_approval(self):
        a = self.approval
        calls, withdraw = withdrawer()
        g = self.graph(self.withdraw_turn())
        updates = [list(u) for u in g.stream({"messages": [self.HumanMessage(f"Withdraw {DOC}")]}, cfg("pause"),
                                             context={"withdraw": withdraw}, stream_mode="updates")]
        self.assertEqual(updates, [["agent"], ["__interrupt__"]])         # agent ran; approve stopped the turn
        self.assertEqual(g.get_state(cfg("pause")).next, ("approve",))
        waiting = a.paused(g, cfg("pause"))
        self.assertEqual([(w["tool"], w["args"], w["call_id"], w["allowed_decisions"], w["tenant"], w["requester"])
                          for w in waiting],
                         [("withdraw_document", {"name": DOC}, "c0", ["approve", "reject"], TENANT, ASKER)])
        self.assertIn("A second person in the company must approve it", waiting[0]["description"])
        self.assertEqual(calls, [])                                      # nothing withdrawn while it waits
        out = a.decide(g, cfg("pause"), [{"type": "approve"}], by=SECOND,  # the turn runs for the thread's own person
                       context={"withdraw": withdraw, "tenant_id": "zeta", "user_id": OTHER})
        self.assertEqual(calls, [{"tenant": TENANT, "name": DOC, "requested_by": ASKER, "approved_by": SECOND}])
        done = self.results(out)["withdraw_document"]
        self.assertEqual((done.status, json.loads(done.content)), ("success", {
            "status": "withdrawal_started", "document": f"{TENANT}/{DOC}", "undo": f"make restore SOURCE={TENANT}/{DOC}"}))
        self.assertEqual(out["messages"][-1].content, "The withdrawal is done.")
        self.assertEqual(self.path(g, cfg("pause")), [("__start__",), ("agent",), ("approve",), ("tools",), ("agent",), ()])
        self.assertEqual(a.paused(g, cfg("pause")), [])
        with self.assertRaises(LookupError):                             # nothing waits: a route's 409
            a.decide(g, cfg("pause"), [{"type": "approve"}], by=SECOND)

    def test_a_turn_with_nothing_to_approve_does_not_pause(self):
        g = self.graph(turn([("retrieve", {"query": "notice period"})], "Two months [1]."))
        out = self.ask(g, "plain", {"tenant_id": TENANT}, question="What is the notice period?")
        self.assertNotIn("__interrupt__", out)
        self.assertEqual(self.path(g, cfg("plain")), [("__start__",), ("agent",), ("tools",), ("agent",), ()])
        self.assertEqual(self.searched[-1], (TENANT, "notice period"))

    def test_a_second_process_resumes_the_turn_from_the_sqlite_file(self):
        from langgraph.checkpoint.sqlite import SqliteSaver
        with tempfile.TemporaryDirectory() as d:
            db_path, record = os.path.join(d, "threads.db"), os.path.join(d, "withdrawn.jsonl")
            with SqliteSaver.from_conn_string(db_path) as saver:
                out = self.ask(self.graph(self.withdraw_turn(), saver), "sqlite")
                self.assertIn("__interrupt__", out)
            p = subprocess.run([sys.executable, str(Path(__file__).resolve()), "resume", db_path, record], cwd=str(KIT),
                               capture_output=True, text=True, encoding="utf-8", timeout=600)
            self.assertEqual(p.returncode, 0, p.stderr[-3000:])
            child = json.loads(p.stdout.strip().splitlines()[-1])
            self.assertEqual(child, {"answer": "Withdrawn, from the second process.",
                                     "asked": ["approval asked: withdraw_document"], "waiting": []})
            with open(record, encoding="utf-8") as f:
                self.assertEqual([json.loads(x) for x in f], [{"tenant": TENANT, "name": DOC, "requested_by": ASKER,
                                                               "approved_by": SECOND}])
            with SqliteSaver.from_conn_string(db_path) as saver:            # this process reads what the other wrote
                g = self.graph([], saver)
                state = g.get_state(cfg("sqlite"))
                self.assertEqual(state.next, ())
                self.assertEqual(state.values["messages"][-1].content, "Withdrawn, from the second process.")
                self.assertEqual(self.results(state.values)["withdraw_document"].status, "success")

    def test_the_requesters_own_approval_is_refused(self):
        a = self.approval
        calls, withdraw = withdrawer()
        g = self.graph(self.withdraw_turn())
        self.ask(g, "own", {"withdraw": withdraw})
        waiting = a.paused(g, cfg("own"))
        for me in (ASKER, "  ASHA@Example.com "):                         # case and spaces do not make another person
            with self.assertRaises(PermissionError) as refused:
                a.decide(g, cfg("own"), [{"type": "approve"}], by=me, context={"withdraw": withdraw})
            self.assertIn("cannot approve their own request", str(refused.exception))
        self.assertEqual(a.paused(g, cfg("own")), waiting)                 # still waiting, for the same call
        # A resume that skips decide() meets the approve node's own lock: the turn asks again, saying why.
        out = g.invoke(self.Command(resume={"decisions": [{"type": "approve"}], "by": ASKER}), cfg("own"),
                       context={"withdraw": withdraw, "approvals": {"c0": ASKER}})
        self.assertEqual(out["__interrupt__"][0].value["refused"],
                         ["the person who asked cannot approve their own request: a second person must"])
        self.assertEqual(a.paused(g, cfg("own")), waiting)
        with self.assertRaises(PermissionError):                         # may_approve: who else may; roster_rule below
            a.decide(g, cfg("own"), [{"type": "approve"}], by=OTHER, context={"withdraw": withdraw},
                     may_approve=lambda tenant, email: (tenant, email) == (TENANT, SECOND))
        with self.assertRaises(PermissionError):                         # nobody named
            a.decide(g, cfg("own"), [{"type": "approve"}], by="", context={"withdraw": withdraw})
        self.assertEqual(calls, [])
        a.decide(g, cfg("own"), [{"type": "approve"}], by=SECOND, context={"withdraw": withdraw},
                 may_approve=lambda tenant, email: (tenant, email) == (TENANT, SECOND))
        self.assertEqual([c["approved_by"] for c in calls], [SECOND])

    def test_who_may_approve_is_read_from_the_tenants_roster(self):
        # roster_rule(db, role), the kit's may_approve (13 October 2026): a second person on the roster of the
        # conversation's own tenant who holds the role. Each refusal says why, before anything runs.
        a = self.approval
        calls, withdraw = withdrawer()
        zoe, nobody = "zoe@example.com", "nobody@example.com"           # zoe is on globex's roster; nobody on none
        db = roster({ASKER: None, SECOND: ["employee", "people_ops"], OTHER: None})
        db.docs.update({f"tenants/globex/members/{zoe}": {"email": zoe}, f"tenants/globex/roles/{zoe}": {"roles": ["people_ops"]}})
        rule = a.roster_rule(db, "people_ops")
        g = self.graph(self.withdraw_turn())
        self.ask(g, "roster", {"withdraw": withdraw})
        waiting = a.paused(g, cfg("roster"))
        for who, kind, why in ((zoe, "approve", f"{zoe} is not on acme's roster: only a person in this company may "
                                                "decide its requests"),
                               (nobody, "reject", f"{nobody} is not on acme's roster"),
                               (OTHER, "approve", f"{OTHER} does not hold people_ops in acme, the role that may approve or "
                                                  "reject these requests (make roles grants it)")):
            with self.subTest(who=who, kind=kind):
                with self.assertRaises(PermissionError) as refused:
                    a.decide(g, cfg("roster"), [{"type": kind}], by=who, context={"withdraw": withdraw}, may_approve=rule)
                self.assertIn(why, str(refused.exception))
                self.assertEqual(a.paused(g, cfg("roster")), waiting)    # refused before anything ran

        class Unwell:                                                   # a roster that cannot be read
            def collection(self, name):
                raise RuntimeError("Firestore is unwell")
        with self.assertRaises(PermissionError) as refused:
            a.decide(g, cfg("roster"), [{"type": "approve"}], by=SECOND, context={"withdraw": withdraw},
                     may_approve=a.roster_rule(Unwell(), "people_ops"))
        self.assertIn("acme's roster could not be read, so no decision can be checked", str(refused.exception))
        with self.assertRaises(ValueError):                             # not a role make roles grants
            a.roster_rule(db, "approver")
        self.assertTrue(callable(a.roster_rule(db, "doc_approver")))     # the role the service's routes pass (5.8-B)
        self.assertEqual((calls, a.paused(g, cfg("roster"))), ([], waiting))
        a.decide(g, cfg("roster"), [{"type": "approve"}], by=SECOND, context={"withdraw": withdraw}, may_approve=rule)
        self.assertEqual([(c["requested_by"], c["approved_by"]) for c in calls], [(ASKER, SECOND)])
        self.assertEqual((a.paused(g, cfg("roster")), db.writes), ([], []))    # resumed; the roster only read

    def test_a_rejection_errors_that_call_only(self):
        a = self.approval
        calls, withdraw = withdrawer()
        g = self.graph(turn([("retrieve", {"query": "notice period"}), ("withdraw_document", {"name": DOC})],
                            "Nothing was withdrawn; the notice period is two months [1]."))
        before = len(self.searched)
        self.ask(g, "reject", {"withdraw": withdraw})
        self.assertEqual(len(self.searched), before)                     # the search waits with the turn
        with self.assertRaises(ValueError):                              # a reason is at most 200 characters
            a.decide(g, cfg("reject"), [{"type": "reject", "message": "x" * 201}], by=SECOND)
        with self.assertRaises(ValueError):                              # a withdrawal is approved or rejected
            a.decide(g, cfg("reject"), [{"type": "respond", "message": "fine"}], by=SECOND)
        with self.assertRaises(ValueError):                              # one decision for each waiting call
            a.decide(g, cfg("reject"), [{"type": "reject"}, {"type": "reject"}], by=SECOND)
        out = a.decide(g, cfg("reject"), [{"type": "reject", "message": "That handbook is still in force."}], by=SECOND,
                       context={"withdraw": withdraw, "tenant_id": "zeta"})     # the search stays in the thread's tenant
        got = self.results(out)
        self.assertEqual((got["withdraw_document"].status, json.loads(got["withdraw_document"].content)), ("error", {
            "error": "withdraw_document was rejected by a second person, so nothing was done",
            "their_reason": "That handbook is still in force."}))
        self.assertEqual(got["retrieve"].status, "success")              # the search asked for beside it ran, once
        self.assertEqual(self.searched[before:], [(TENANT, "notice period")])
        self.assertEqual((self.refusals(out), calls), (["withdraw_document"], []))
        self.assertEqual(self.path(g, cfg("reject"))[-4:], [("approve",), ("tools",), ("agent",), ()])
        # The person who asked may reject their own request: their cancel.
        g = self.graph(self.withdraw_turn("Cancelled."))
        self.ask(g, "cancel", {"withdraw": withdraw})
        out = a.decide(g, cfg("cancel"), [{"type": "reject"}], by=ASKER, context={"withdraw": withdraw})
        self.assertEqual(json.loads(self.results(out)["withdraw_document"].content)["error"],
                         "withdraw_document was cancelled by the person who asked for it, so nothing was done")
        self.assertEqual(calls, [])

    def test_ask_user_is_answered_by_the_person_who_asked(self):
        a = self.approval
        question = "Which office: Hyderabad or Pune?"
        g = self.graph(turn([("ask_user", {"question": question})], "In Pune, the notice period is two months."))
        self.ask(g, "ask", question="What is the notice period at my office?")
        self.assertEqual([(w["tool"], w["allowed_decisions"], w["description"]) for w in a.paused(g, cfg("ask"))],
                         [("ask_user", ["respond"], question)])
        with self.assertRaises(PermissionError):                         # a second person cannot answer for them
            a.decide(g, cfg("ask"), [{"type": "respond", "message": "Hyderabad"}], by=SECOND)
        with self.assertRaises(ValueError):                              # a question is answered, not approved
            a.decide(g, cfg("ask"), [{"type": "approve"}], by=ASKER)
        with self.assertRaises(ValueError):                              # an answer has words
            a.decide(g, cfg("ask"), [{"type": "respond", "message": "  "}], by=ASKER)
        out = a.decide(g, cfg("ask"), [{"type": "respond", "message": "Pune"}], by=ASKER)
        answer = self.results(out)["ask_user"]
        self.assertEqual((answer.content, answer.status), ("Pune", "success"))
        self.assertEqual(out["messages"][-1].content, "In Pune, the notice period is two months.")
        self.assertEqual(self.path(g, cfg("ask"))[-3:], [("approve",), ("agent",), ()])

    def test_offer_case_writes_nothing(self):
        from typing import get_args
        from shared import desk_law
        self.assertEqual(get_args(self.approval.CaseType), tuple(desk_law.CASE_TYPES))     # the button's six types
        db, queues = roster({ASKER: None}), acme_queues()
        for case_type in desk_law.CASE_TYPES:                            # all six, each offered, nothing written
            offers = []
            out = self.ask(self.graph(turn([("offer_case", {"case_type": case_type})], "You can raise this as a case.")),
                           f"offer-{case_type}", {"db": db, "case_queues": queues, "offers": offers},
                           question="I want to talk to a person about this")
            result = self.results(out)["offer_case"]
            self.assertEqual(result.status, "success", (case_type, result.content))
            self.assertEqual(json.loads(result.content)["case_offer"], {"case_type": case_type})
            self.assertEqual(offers, [{"case_type": case_type}])
        self.assertEqual(db.writes, [])                                  # no case, no draft, no role, no event
        self.assertIn(f"tenants/{TENANT}/members/{ASKER}", db.reads)    # the roles were read, not assumed
        # the chat door's own offer has the same key and shape
        self.assertIn('"case_offer": {"case_type": cls}', (KIT / "services/chat/desk.py").read_text(encoding="utf-8"))

        def offered(case_type, db_, queues_, session):
            out = self.ask(self.graph(turn([("offer_case", {"case_type": case_type})], "ok")), session,
                           {"db": db_, "case_queues": queues_}, question="I want to talk to a person")
            return self.results(out)["offer_case"]

        refused = offered("grievance", roster({ASKER: ["desk_eval"]}), queues, "offer-noroles")
        self.assertEqual(refused.status, "error")                        # desk_eval opens no case desk
        self.assertIn("roles do not include raising a case", refused.content)
        self.assertEqual(offered("grievance", roster({}), queues, "offer-nomember").status, "error")  # on no roster
        self.assertEqual(offered("posh", db, {}, "offer-noposh").status, "error")             # no POSH section
        people = {"people": queues["people"]}
        self.assertEqual(offered("grievance", db, people, "offer-nogrc").status, "error")      # no GRC queue
        self.assertEqual(offered("privacy_request", db, people, "offer-fallback").status, "success")   # people stands in
        self.assertEqual(offered("human_requested", roster({ASKER: ["leaver"]}), people,
                                 "offer-leaver").status, "success")      # a leaver keeps the case desk
        self.assertEqual(db.writes, [])

    def test_the_approval_line_above_interrupt_is_written_twice(self):
        """The page's Change-it: the kit writes "approval asked" below interrupt(), once. Moved above it, a resume
        writes it again, because a resumed node runs again from its first line."""
        lines = SRC.splitlines(keepends=True)
        line = [i for i, x in enumerate(lines) if 'logger.info("approval asked' in x]
        stop = [i for i, x in enumerate(lines) if "answer = interrupt(request)" in x]
        self.assertEqual((len(line), len(stop)), (1, 1))
        self.assertGreater(line[0], stop[0])                             # the kit's own place: below interrupt()
        moved = list(lines)
        indent = moved[stop[0]][:len(moved[stop[0]]) - len(moved[stop[0]].lstrip())]
        text = moved.pop(line[0]).lstrip()
        moved.insert(stop[0], indent + text)
        changed = types.ModuleType("approval_changed")
        sys.modules["approval_changed"] = changed
        try:
            exec(compile("".join(moved), "approval_changed.py", "exec"), changed.__dict__)
            for module, want in ((self.approval, (0, 1)), (changed, (1, 2))):
                calls, withdraw = withdrawer()
                g = self.graph(self.withdraw_turn(), module=module)
                with self.assertLogs(LOGGER, level="INFO") as logs:
                    logging.getLogger(LOGGER).info("start")
                    self.ask(g, f"twice-{module.__name__}", {"withdraw": withdraw})
                    at_pause = sum("approval asked" in x for x in logs.output)
                    module.decide(g, cfg(f"twice-{module.__name__}"), [{"type": "approve"}], by=SECOND,
                                  context={"withdraw": withdraw})
                    after = sum("approval asked" in x for x in logs.output)
                self.assertEqual((at_pause, after), want, module.__name__)
                self.assertEqual(len(calls), 1, module.__name__)         # the tool runs once either way
        finally:
            sys.modules.pop("approval_changed", None)

    def test_withdraw_document_never_runs_without_a_second_persons_approval(self):
        from langchain.agents import create_agent
        a = self.approval
        calls, withdraw = withdrawer()
        # Bound with no pause in front of it, the tool refuses: the last lock.
        bare = create_agent(model=scripted(self.withdraw_turn("Not done.")), tools=self.tools.TOOLS + a.PERSON_TOOLS,
                            checkpointer=self.InMemorySaver())
        out = self.ask(bare, "bare", {"withdraw": withdraw, "approvals": {"c0": ASKER}})
        self.assertEqual(self.refusals(out), ["withdraw_document"])
        self.assertIn("runs only after a second person", self.results(out)["withdraw_document"].content)
        # A resume that skips decide() carries no approval for the call: the node lets it through, the tool does not.
        g = self.graph(self.withdraw_turn("Not done."))
        self.ask(g, "skip", {"withdraw": withdraw})
        out = g.invoke(self.Command(resume={"decisions": [{"type": "approve"}], "by": SECOND}), cfg("skip"),
                       context={"withdraw": withdraw})
        self.assertEqual(self.refusals(out), ["withdraw_document"])
        self.assertEqual(calls, [])
        # Whatever a context says, the tool withdraws from the thread's own tenant, for the thread's own person.
        g = self.graph(self.withdraw_turn())
        self.ask(g, "tenant", {"withdraw": withdraw})
        g.invoke(self.Command(resume={"decisions": [{"type": "approve"}], "by": SECOND}), cfg("tenant"),
                 context={"withdraw": withdraw, "approvals": {"c0": SECOND}, "tenant_id": "zeta", "user_id": OTHER})
        self.assertEqual(calls, [{"tenant": TENANT, "name": DOC, "requested_by": ASKER, "approved_by": SECOND}])
        calls.clear()
        for name, want in ((DOC, DOC), (f"{TENANT}/{DOC}", DOC), (f"gs://YOUR-BUCKET/{TENANT}/{DOC}", DOC)):
            self.assertEqual(a.normalize_name(name, TENANT), want)
        for name in (f"zeta/{DOC}", "../secrets.md", "a/b/c.md", "x" * 201, "", "dir\\file.md"):
            with self.assertRaises(ValueError, msg=name):
                a.normalize_name(name, TENANT)

    def test_the_middleware_form_adds_a_node_and_pauses_alike(self):
        from langchain.agents import create_agent
        from langchain_core.messages import AIMessage
        a = self.approval

        def agent(script, middleware):
            return create_agent(model=scripted(script), tools=self.tools.TOOLS + a.PERSON_TOOLS,
                                middleware=middleware, checkpointer=self.InMemorySaver())

        self.assertNotIn("HumanInTheLoopMiddleware.after_model", agent([], []).get_graph().nodes)
        self.assertIn("HumanInTheLoopMiddleware.after_model", agent([], [a.hitl_middleware()]).get_graph().nodes)
        priced = turn([("calculate_processing_cost", {"total_pages": 10})], "About Rs 42.")
        for script, model_calls in (([AIMessage("Hello.")], 1), (priced, 2)):
            counts = []
            for middleware in ([], [a.hitl_middleware()]):
                ag = agent(script, middleware)
                ag.invoke({"messages": [self.HumanMessage("Hi")]}, cfg("count"))
                counts.append(len(list(ag.checkpointer.list(cfg("count")))))
            self.assertEqual(counts[1] - counts[0], model_calls)          # the hook's node: one checkpoint a model call

        calls, withdraw = withdrawer()
        mw, g = agent(self.withdraw_turn(), [a.hitl_middleware()]), self.graph(self.withdraw_turn())
        out = self.ask(mw, "mw", {"withdraw": withdraw})
        self.ask(g, "mw-graph", {"withdraw": withdraw})
        self.assertEqual(out["__interrupt__"][0].value["review_configs"],
                         [{"action_name": "withdraw_document", "allowed_decisions": ["approve", "reject"]}])
        self.assertEqual(a.paused(mw, cfg("mw")), a.paused(g, cfg("mw-graph")))      # one record shape from both
        with self.assertRaises(PermissionError):
            a.decide(mw, cfg("mw"), [{"type": "approve"}], by=ASKER, context={"withdraw": withdraw})
        self.assertEqual(len(a.paused(mw, cfg("mw"))), 1)
        out = a.decide(mw, cfg("mw"), [{"type": "approve"}], by=SECOND, context={"withdraw": withdraw})
        self.assertEqual(([c["approved_by"] for c in calls], out["messages"][-1].content),
                         ([SECOND], "The withdrawal is done."))

        rejected = agent(self.withdraw_turn("Not done."), [a.hitl_middleware()])
        self.ask(rejected, "mw-reject", {"withdraw": withdraw})
        out = a.decide(rejected, cfg("mw-reject"), [{"type": "reject", "message": "Still in force."}], by=SECOND,
                       context={"withdraw": withdraw})
        self.assertEqual(self.refusals(out), ["withdraw_document"])
        self.assertEqual(len(calls), 1)

        asking = agent(turn([("ask_user", {"question": "Which office?"})], "Pune it is."), [a.hitl_middleware()])
        self.ask(asking, "mw-ask")
        self.assertEqual(a.paused(asking, cfg("mw-ask"))[0]["description"], "Which office?")
        out = a.decide(asking, cfg("mw-ask"), [{"type": "respond", "message": "Pune"}], by=ASKER)
        self.assertEqual((self.results(out)["ask_user"].content, self.results(out)["ask_user"].status), ("Pune", "success"))


if __name__ == "__main__":
    if sys.argv[1:2] == ["resume"]:
        _second_process(*sys.argv[2:4])
    else:
        unittest.main()
