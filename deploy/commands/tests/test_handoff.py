"""Offline checks for the chat's hand-off to the A2A peer (workshop lesson 10.7).

    python -m unittest commands/tests/test_handoff.py -v          # from deploy/

No network beyond 127.0.0.1, no credential. The first classes need the standard library, requests (the shared tool
layer's) and bash: services/chat/peer.py's gate, cap and deadline, read as it holds them; tenancy.tenants_of() on a
fake Firestore; the hand-off's lines in brains.py, in the ADK brain alone and off unless PEER_URL is set; the pins
(a2a-sdk at the peer's version, no extra, so no database layer in the chat image); validate.py's THIRD_PARTY; the
targets, the 888 lines, both CI lines and the UNOWNED.md rows; smoke_handoff.py's verdict on the responses a lane can
give; and commands/handoff.sh against a stub gcloud that keeps the two services in a file.

The second runs the kit's own ADK brain, scripted, and needs the chat image's pins with a2a-sdk (pip install -r
services/chat/requirements.txt). The peer is a stand-in on 127.0.0.1 that answers a2a-sdk's client as the kit's
agent.py over to_a2a does (google-adk 2.8.0, a2a-sdk 1.1.2): the card, then SendMessage, and a task completed, failed
at the peer's cap or slow. Each was taken from that peer served offline with Gemini scripted, 13 October 2026; the
chat's own image cannot serve one (no http-server extra). Covered: off, the tool list and the keys unchanged; an
inventory question handed over, with only the question in the message, the chain and a hand-off id in the request's
metadata (lesson 10.7's PEER_CHAIN reads them on the peer) and the chat's token on both requests; a
question that needs the peer and a search; the confused deputy (a zeta asker; a peer account on three rosters)
refused before anything is sent; the third hand-off of a turn refused, side by side; the peer's task failed at its
cap; a slow peer cut at the budget and named in tool_timeouts; the peer's door shut; one log line per hand-off, with
the question's length and not its words. Without the pins this class is skipped and says so; with
DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins steps set it, a missing pin is an error instead.
"""
import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[2]
ROOT = KIT.parent
sys.path[:0] = [p for p in (str(KIT), str(KIT / "services/chat")) if p not in sys.path]
os.environ.pop("PEER_URL", None)                    # the switch is off unless a test turns it on
import limits  # noqa: E402
import peer  # noqa: E402
from shared import tenancy  # noqa: E402

FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "google.adk", "a2a"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
PROJECT, NUMBER, REGION = "documind-course-demo", "123456789012", "asia-south1"
AGENT_SA = f"documind-agent-sa@{PROJECT}.iam.gserviceaccount.com"
UI_SA = f"documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"
ROSTERS = {AGENT_SA: ["acme"], UI_SA: ["acme", "globex", "zeta"]}     # lane.roster_plan's, sorted, for these two
TENANT_NAMES = ("acme", "globex", "zeta")


def read(*parts: str) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


class TheHandoffAlone(unittest.TestCase):
    """What needs no framework: the rules, the switch, the pins, the entries, the script and the smoke's verdict."""

    def test_the_constants_the_lesson_names(self):
        self.assertEqual((peer.NAME, peer.HANDOFF_MAX_PER_TURN, peer.PEER_TIMEOUT_S), ("documind_peer", 2, 75.0))
        ui_wait = int(re.search(r"headers=_headers\(CHAT_URL\), timeout=(\d+)\)", read("services", "frontend", "chat.py")).group(1))
        self.assertLess(peer.PEER_TIMEOUT_S, limits.TURN_DEADLINE_S)          # 75 s inside the turn's 100 s
        self.assertLess(limits.TURN_DEADLINE_S, ui_wait)                      # inside the UI's 120 s
        self.assertEqual(peer.documind_peer.__doc__, peer.DESCRIPTION)        # what the model reads

    def test_off_unless_peer_url_is_set(self):
        self.assertEqual(peer.PEER_URL, "")
        src = read("services", "chat", "brains.py")
        self.assertIn("\nimport peer\n", src)
        self.assertRegex(src, r"on_model_error_callback=limits\.adk_model_error\)\n        if peer\.PEER_URL:  [^\n]*\n"
                              r"            root\.tools\.append\(peer\.tool\(\)\)\n")
        self.assertRegex(src, r"\n        if peer\.PEER_URL:  [^\n]*\n            out\[\"handoffs\"\] = ctx\[\"handoffs\"\] = \[\]\n")
        self.assertEqual(src.count("peer.PEER_URL"), 2)                       # the tool and the turn's record, nothing else
        adk = src.split("\nclass AdkBrain:", 1)[1].split("\nclass DirectBrain:", 1)[0]
        self.assertEqual(len(re.findall(r"\bpeer\.", src)), len(re.findall(r"\bpeer\.", adk)))   # the ADK brain alone
        peer_src = read("services", "chat", "peer.py")
        self.assertNotIn("import a2a", peer_src.split("async def _send(")[0])   # an image without it still starts
        self.assertIn('os.environ.get("PEER_URL", "")', peer_src)

    def test_the_gate_refuses_a_third_hand_off_and_a_confused_deputy(self):
        self.assertIsNone(peer.gate("acme", ["acme"], 0))
        self.assertIsNone(peer.gate("acme", ["acme"], 1))
        self.assertIn("HANDOFF_MAX_PER_TURN", peer.gate("acme", ["acme"], 2))
        for tenant, rosters in (("zeta", ["acme"]), ("acme", ["acme", "globex", "zeta"]), ("acme", []), ("", ["acme"])):
            reason = peer.gate(tenant, rosters, 0)
            self.assertIn("confused deputy", reason, (tenant, rosters))
            self.assertFalse(any(t in reason for t in TENANT_NAMES), reason)  # the asker learns no tenant's name

    def test_the_wait_is_the_smaller_of_75_s_and_the_turns_time_left(self):
        meter = limits.Meter(deadline_s=100.0)
        self.assertEqual(peer.budget_s(meter), 75.0)
        meter.started -= 90                                                     # 10 s left
        self.assertAlmostEqual(peer.budget_s(meter), 10.0, delta=0.5)
        meter.started -= 20                                                     # past the deadline
        self.assertEqual(peer.budget_s(meter), limits.TOOL_FLOOR_S)

    def test_tenants_of_reads_every_roster_an_account_is_on(self):
        class Doc:
            def __init__(self, tenant):
                self.reference = type("R", (), {"parent": type("P", (), {"parent": type("T", (), {"id": tenant})})})

        class Query:
            asked = []

            def where(self, field, op, value):
                Query.asked.append((field, op, value))
                return self

            def get(self):
                return [Doc(t) for t in ("zeta", "acme", "zeta")]

        db = type("DB", (), {"collection_group": lambda self, name: Query() if name == "members" else None})()
        with mock.patch.object(tenancy, "_db", lambda: db):
            self.assertEqual(tenancy.tenants_of("Documind-UI-SA@x.iam.gserviceaccount.com"), ["acme", "zeta"])
            self.assertEqual(tenancy.tenants_of(""), [])
        self.assertEqual(Query.asked, [("email", "==", "documind-ui-sa@x.iam.gserviceaccount.com")])

    def test_the_pins_the_hand_off_needs(self):
        chat, agent = read("services", "chat", "requirements.txt"), read("services", "agent", "requirements.txt")
        self.assertRegex(chat, r"(?m)^a2a-sdk==1\.1\.2$")                       # no extra: no server, no database layer
        self.assertEqual(re.search(r"(?m)^a2a-sdk\[http-server\]==([\d.]+)$", agent).group(1), "1.1.2")
        self.assertRegex(chat, r"(?m)^google-adk==2\.8\.0$")
        self.assertNotIn("sqlalchemy", chat.lower())                            # lessons 5.7 and 6.5-6.7 assert it
        spec = importlib.util.spec_from_file_location("validate_for_handoff", KIT / "validate.py")
        validate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validate)
        self.assertIn("a2a", validate.THIRD_PARTY)                              # peer.py imports a2a.client

    def test_the_targets_the_ci_lines_and_the_rows(self):
        mk, agents, readme = read("Makefile"), read("mk", "agents.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")]
        self.assertTrue({"handoff", "smoke-handoff"} <= set(phony.split()), phony[-120:])    # later kits append after
        self.assertIn("@PROJECT=$(PROJECT) REGION=$(REGION) OFF=$(OFF) PY=$(PY) bash commands/handoff.sh",
                      agents.split("\nhandoff: guard-project\n", 1)[1].split("\n\n", 1)[0])
        smoke = agents.split("\nsmoke-handoff: guard-project\n", 1)[1].split("\n\n", 1)[0]
        self.assertIn("DOCUMIND_IMPERSONATE_SA=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com", smoke)
        self.assertIn("$(PY) smoke/smoke_handoff.py", smoke)
        row = next(line for line in readme.splitlines() if line.startswith("| `agents.mk` |"))
        self.assertTrue(all(f"`{t}`" in row for t in ("handoff", "smoke-handoff")), row)
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_handoff.py -v"
        self.assertIn(line, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = ROOT / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                                    # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))
        unowned = read("UNOWNED.md")
        for f in ("services/chat/peer.py", "commands/handoff.sh", "smoke/smoke_handoff.py", "commands/tests/test_handoff.py"):
            row = next((l for l in read("INDEX.md").splitlines() if l.startswith(f"| `{f}` |")), "")   # a page quotes it
            self.assertTrue(f"| `{f}` | **10.7**" in unowned or row.split(" | ")[2:3] not in ([], ["-"]), f)
            self.assertTrue((KIT / f).exists(), f)

    def test_smoke_handoffs_verdict(self):
        sys.path.insert(0, str(KIT / "smoke"))
        import smoke_handoff as sh
        good = {"answer": "Three documents.", "tool_calls": ["documind_peer"],
                "handoffs": [{"n": 1, "outcome": "answered", "state": "completed", "seconds": 3.1, "budget_s": 75.0}]}
        self.assertTrue(sh.handed_off(200, good)[0])
        off = {k: v for k, v in good.items() if k != "handoffs"}
        self.assertIn("the hand-off is off", sh.handed_off(200, off)[1])
        refused = {**good, "handoffs": [{"n": 1, "outcome": "refused", "reason": "it was not asked (a confused deputy)"}]}
        verdict = sh.handed_off(200, refused)
        self.assertFalse(verdict[0])
        self.assertIn("confused deputy", verdict[1])
        failed = {**good, "handoffs": [{"n": 1, "outcome": "failed", "state": "failed", "seconds": 4, "budget_s": 75}]}
        self.assertFalse(sh.handed_off(200, failed)[0])
        late = {**good, "handoffs": [{"n": 1, "outcome": "answered", "state": "completed", "seconds": 80, "budget_s": 75}]}
        self.assertFalse(sh.handed_off(200, late)[0])
        self.assertFalse(sh.handed_off(403, {"detail": "not a member of any tenant"})[0])


# One script plays gcloud for handoff.sh: the two services in services.json, every call recorded in calls/.
GCLOUD = r'''
import json, os, sys, time

home, args = os.environ["HANDOFF_STUB_HOME"], sys.argv[1:]
with open(os.path.join(home, "calls", "%d-%d.json" % (time.time_ns(), os.getpid())), "w", encoding="utf-8") as log:
    json.dump(args, log)
path = os.path.join(home, "services.json")
with open(path, encoding="utf-8") as f:
    world = json.load(f)


def flag(name):
    return next((a.split("=", 1)[1] for a in args if a.startswith(name + "=")), None)


named = [a for a in args[3:] if not a.startswith("--")]
svc = world["services"].get(named[0]) if len(named) == 1 and flag("--project") == world["project"] \
    and flag("--region") == world["region"] else None
if args[:3] == ["projects", "describe", world["project"]]:
    print(world["number"])
elif args[:3] == ["run", "services", "describe"] and svc is not None and flag("--format") == "json":
    print(json.dumps({"status": {"traffic": svc["traffic"]}}))
elif args[:3] == ["run", "services", "describe"] and svc is not None:
    print(svc["account"])
elif args[:3] == ["run", "services", "describe"]:
    sys.stderr.write("ERROR: (gcloud.run.services.describe) Cannot find service\n")
    sys.exit(1)
elif args[:3] == ["run", "services", "get-iam-policy"] and svc is not None:
    print(json.dumps({"bindings": [{"role": "roles/run.invoker", "members": svc["invokers"]}]}))
elif args[:3] == ["run", "services", "update"] and named == ["documind-chat"] and svc is not None and "--quiet" in args:
    if flag("--update-env-vars"):
        svc["env"].update(kv.split("=", 1) for kv in flag("--update-env-vars").split(","))
    for key in (flag("--remove-env-vars") or "").split(","):
        svc["env"].pop(key, None)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(world, f)
else:
    sys.stderr.write("stub: unexpected call: gcloud " + " ".join(args) + "\n")
    sys.exit(99)
'''


@unittest.skipUnless(shutil.which("bash"), "bash is not on PATH")
class TheSwitch(unittest.TestCase):
    """commands/handoff.sh against the stub gcloud: on, off, and the two refusals that change nothing."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="handoff_test_"))
        self.addCleanup(shutil.rmtree, self.home, True)
        for d in ("bin", "calls"):
            (self.home / d).mkdir()
        (self.home / "stub.py").write_text(GCLOUD, encoding="utf-8")
        python = Path(sys.executable).as_posix()
        for name, body in (("gcloud", f'exec "{python}" "{(self.home / "stub.py").as_posix()}" "$@"'),
                           ("py", f'exec "{python}" "$@"')):
            with open(self.home / "bin" / name, "w", encoding="utf-8", newline="\n") as f:
                f.write(f"#!/bin/sh\n{body}\n")
            (self.home / "bin" / name).chmod(0o755)
        latest = [{"latestRevision": True, "percent": 100}]
        self.world = {"project": PROJECT, "region": REGION, "number": NUMBER, "services": {
            "documind-chat": {"account": f"documind-chat-sa@{PROJECT}.iam.gserviceaccount.com", "traffic": latest,
                              "invokers": [], "env": {"DOCUMIND_BRAIN": "langchain"}},
            "documind-agent": {"account": AGENT_SA, "traffic": latest, "env": {},
                               "invokers": [f"serviceAccount:documind-ui-sa@{PROJECT}.iam.gserviceaccount.com",
                                            f"serviceAccount:documind-chat-sa@{PROJECT}.iam.gserviceaccount.com"]}}}

    def switch(self, off: bool = False) -> subprocess.CompletedProcess:
        (self.home / "services.json").write_text(json.dumps(self.world), encoding="utf-8")
        env = {"PATH": str(self.home / "bin") + os.pathsep + os.environ.get("PATH", ""), "HANDOFF_STUB_HOME": str(self.home),
               "PROJECT": PROJECT, "REGION": REGION, "PY": str(self.home / "bin" / "py"), "OFF": "1" if off else "",
               "HOME": str(self.home), "USERPROFILE": str(self.home), "APPDATA": str(self.home),
               "CLOUDSDK_CONFIG": str(self.home / "gcloud"), "PYTHONIOENCODING": "utf-8"}
        for key in ("SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR", "TEMP", "TMP"):    # what Windows itself needs
            if key in os.environ:
                env[key] = os.environ[key]
        return subprocess.run([shutil.which("bash"), "commands/handoff.sh"], cwd=str(KIT), env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=180)

    def chat_env(self) -> dict:
        return json.loads((self.home / "services.json").read_text(encoding="utf-8"))["services"]["documind-chat"]["env"]

    def updates(self) -> list:
        calls = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.home / "calls").glob("*.json"))]
        return [c for c in calls if c[:3] == ["run", "services", "update"]]

    def test_on_sets_the_peers_url_and_the_account_it_runs_as(self):
        r = self.switch()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.chat_env(), {"DOCUMIND_BRAIN": "langchain", "PEER_ACCOUNT": AGENT_SA,
                                           "PEER_URL": f"https://documind-agent-{NUMBER}.{REGION}.run.app"})
        self.assertEqual(len(self.updates()), 1)
        self.assertIn(f">> documind-chat: PEER_ACCOUNT={AGENT_SA}", r.stdout)

    def test_off_removes_both(self):
        self.world["services"]["documind-chat"]["env"].update(PEER_URL="https://x", PEER_ACCOUNT=AGENT_SA)
        r = self.switch(off=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.chat_env(), {"DOCUMIND_BRAIN": "langchain"})
        self.assertIn("the hand-off is off", r.stdout)

    def test_no_peer_and_no_invoker_change_nothing(self):
        world = json.loads(json.dumps(self.world))
        del self.world["services"]["documind-agent"]
        r = self.switch()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("documind-agent is not deployed in asia-south1; nothing changed.", r.stderr)
        self.world = world
        self.world["services"]["documind-agent"]["invokers"] = self.world["services"]["documind-agent"]["invokers"][:1]
        r = self.switch()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("documind-chat-sa may not invoke documind-agent", r.stderr)
        self.assertEqual((self.updates(), self.chat_env()), ([], {"DOCUMIND_BRAIN": "langchain"}))


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins with a2a-sdk: pip install -r services/chat/requirements.txt")
class TheHandoffInTheBrain(unittest.TestCase):
    """The kit's ADK brain, scripted, handing questions to a stand-in peer through peer.py and a2a-sdk's client."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.NOTSET)                 # the hand-off's own log line is checked (assertLogs)
        cls.adk_level = logging.getLogger("google_adk").level
        logging.getLogger("google_adk").setLevel(logging.ERROR)    # ADK's notes on a scripted model's missing usage
        os.environ.setdefault("CHECKPOINT_DSN", "")
        import brains
        import shared.documind_tools as dt
        from google.adk.models.base_llm import BaseLlm
        from google.adk.models.llm_response import LlmResponse
        from google.genai import types as gt
        cls.brains, cls.dt, cls.gt, cls.LlmResponse = brains, dt, gt, LlmResponse
        cls.seen, cls.minted = [], []
        cls.mode = {"peer": "answer"}
        mode, seen = cls.mode, cls.seen

        class Peer(BaseHTTPRequestHandler):
            """documind-agent, stood in: its card, then SendMessage, as agent.py over to_a2a answers a2a-sdk's client."""

            def log_message(self, *a):
                pass

            def reply(self, code, body):
                data = json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                seen.append(("GET", self.path, self.headers.get("Authorization"), None))
                if mode["peer"] == "shut" or self.path != "/.well-known/agent-card.json":
                    return self.reply(403 if mode["peer"] == "shut" else 404, {"detail": "no"})
                url = f"http://127.0.0.1:{self.server.server_address[1]}"
                about = "Answers questions about DocuMind's documents with citations, through the DocuMind MCP server."
                self.reply(200, {"name": "documind_peer", "description": about, "version": "0.0.1",
                                 "supportedInterfaces": [{"url": url, "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}],
                                 "capabilities": {"streaming": False, "pushNotifications": False},
                                 "defaultInputModes": ["text/plain"], "defaultOutputModes": ["text/plain"],
                                 "skills": [{"id": "documind_peer", "name": "model", "description": about, "tags": ["llm"]}]})

            def do_POST(self):
                req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                seen.append(("POST", req.get("method"), self.headers.get("Authorization"), req))
                if mode["peer"] == "slow":
                    time.sleep(1.5)
                msg, n = req["params"]["message"], sum(1 for s in seen if s[0] == "POST")
                task = {"id": f"task-{n}", "contextId": f"context-{n}", "history": [msg], "metadata": {}}
                if mode["peer"] == "failed":
                    task["status"] = {"state": "TASK_STATE_FAILED", "message": {
                        "messageId": "m-1", "role": "ROLE_AGENT",
                        "parts": [{"text": "Max number of llm calls limit of `12` exceeded"}]}}
                else:
                    task["status"] = {"state": "TASK_STATE_COMPLETED"}
                    task["artifacts"] = [{"artifactId": "a-1", "parts": [{"text": "The acme corpus holds 3 documents."}]}]
                self.reply(200, {"jsonrpc": "2.0", "id": req["id"], "result": {"task": task}})

        class Api(BaseHTTPRequestHandler):
            """rag-api, stood in, for the turn that also searches."""

            def log_message(self, *a):
                pass

            def do_POST(self):
                req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                data = json.dumps({"answer": "rag-api's answer", "answerable": True, "confidence": "high", "citations": [
                    {"chunk_id": f"acme:{req['query']}#0", "source_uri": "gs://b/acme/x.pdf", "page": 1,
                     "quote": "five years", "score": 0.9}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        cls.peer_srv, cls.api = ThreadingHTTPServer(("127.0.0.1", 0), Peer), ThreadingHTTPServer(("127.0.0.1", 0), Api)
        for srv in (cls.peer_srv, cls.api):
            threading.Thread(target=srv.serve_forever, daemon=True).start()
        cls.peer_url = f"http://127.0.0.1:{cls.peer_srv.server_address[1]}"
        cls.saved = (dt.RAG_API_URL, dt._id_token, tenancy.tenants_of)
        dt.RAG_API_URL = f"http://127.0.0.1:{cls.api.server_address[1]}"
        dt._id_token = lambda aud: cls.minted.append(aud) or "TOKEN"
        tenancy.tenants_of = lambda email: ROSTERS.get(email, [])

        class AdkScript(BaseLlm):
            model: str = "script"
            turns: list = []
            sent: list = []

            async def generate_content_async(self, llm_request, stream=False):
                self.sent.append(llm_request)
                yield self.turns.pop(0)

        cls.AdkScript = AdkScript

    @classmethod
    def tearDownClass(cls):
        for srv in (cls.peer_srv, cls.api):
            srv.shutdown()
        cls.dt.RAG_API_URL, cls.dt._id_token, tenancy.tenants_of = cls.saved
        logging.getLogger("google_adk").setLevel(cls.adk_level)

    def setUp(self):
        self.seen.clear()
        self.minted.clear()
        self.mode["peer"] = "answer"
        for name, value in (("PEER_URL", self.peer_url), ("PEER_ACCOUNT", AGENT_SA)):
            patcher = mock.patch.object(peer, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def turn(self, calls, tenant="acme", label="t"):
        """One ADK turn whose model asks for `calls` - (tool, args) pairs, side by side - then answers."""
        gt, R = self.gt, self.LlmResponse
        parts = [gt.Part(function_call=gt.FunctionCall(name=n, args=a)) for n, a in calls]
        model = self.AdkScript(turns=[R(content=gt.Content(role="model", parts=parts)),
                                      R(content=gt.Content(role="model", parts=[gt.Part(text="done [1]")]))], sent=[])
        brain = self.brains.AdkBrain(None)
        brain.runner.agent.model = model
        meter = limits.Meter()
        with self.assertLogs("documind.chat.peer", level="INFO") as logs:
            out = brain.answer("q", config={"configurable": {"thread_id": f"{tenant}:you:{label}"}},
                               context={"tenant_id": tenant, "user_id": "you@example.com", "assertion": "SECRET-ASSERTION",
                                        "brain": "adk", "meter": meter})
        read = [p.function_response.response for c in model.sent[-1].contents for p in (c.parts or []) if p.function_response]
        lines = [json.loads(r.getMessage()) for r in logs.records]
        return out, read, lines, meter, brain

    def posts(self):
        return [s for s in self.seen if s[0] == "POST"]

    def test_off_the_tool_list_and_the_keys_are_as_before(self):
        with mock.patch.object(peer, "PEER_URL", ""):
            brain = self.brains.AdkBrain(None)
            self.assertEqual([t.name for t in brain.runner.agent.tools], ["retrieve", "calculate_processing_cost"])
            gt, R = self.gt, self.LlmResponse
            brain.runner.agent.model = self.AdkScript(turns=[R(content=gt.Content(role="model", parts=[gt.Part(text="hi")]))], sent=[])
            out = brain.answer("q", config={"configurable": {"thread_id": "acme:you:off"}},
                               context={"tenant_id": "acme", "user_id": "you", "assertion": "", "brain": "adk"})
        self.assertEqual(sorted(out), ["answer", "citations", "refusals", "tool_calls"])

    def test_an_inventory_question_is_handed_over_with_nothing_but_the_question(self):
        out, read, lines, meter, brain = self.turn([("documind_peer", {"request": "Which documents does the corpus hold?"})])
        self.assertEqual([t.name for t in brain.runner.agent.tools], ["retrieve", "calculate_processing_cost", "documind_peer"])
        self.assertEqual((out["tool_calls"], out["refusals"]), (["documind_peer"], []))
        (record,) = out["handoffs"]
        self.assertEqual((record["n"], record["outcome"], record["state"], record["task_id"], record["budget_s"]),
                         (1, "answered", "completed", "task-1", 75.0))
        self.assertEqual(read, [{"answer": "The acme corpus holds 3 documents.", "state": "completed"}])
        (post,) = self.posts()
        self.assertEqual(post[1], "SendMessage")
        message = post[3]["params"]["message"]
        self.assertEqual((message["role"], message["parts"]), ("ROLE_USER", [{"text": "Which documents does the corpus hold?"}]))
        # The request's metadata (workshop lesson 10.7): the chain, this brain alone, and the hand-off's id, which the
        # peer's chain.py reads with PEER_CHAIN=on; the same id is in the record and the log line.
        self.assertRegex(record["handoff_id"], r"^[0-9a-f]{32}$")
        self.assertEqual(post[3]["params"]["metadata"], {"documind_chain": ["documind_adk"],
                                                         "documind_handoff_id": record["handoff_id"]})
        body = json.dumps(post[3])
        for leak in ("acme", "you@example.com", "SECRET-ASSERTION", "tenant"):
            self.assertNotIn(leak, body)                     # only the question crosses the hop
        self.assertEqual({auth for _, _, auth, _ in self.seen}, {"Bearer TOKEN"})     # the card too
        self.assertEqual(self.minted, [self.peer_url])       # minted for the peer's url
        (line,) = lines
        self.assertEqual((line["event"], line["tenant"], line["outcome"], line["request_chars"], line["peer_rosters"]),
                         ("handoff", "acme", "answered", 37, 1))
        self.assertEqual(line["handoff_id"], record["handoff_id"])
        self.assertNotIn("Which documents", json.dumps(line))   # the length, never the words

    def test_a_question_that_needs_the_peer_and_a_search(self):
        out, read, _, _, _ = self.turn([("documind_peer", {"request": "Which documents does the corpus hold?"}),
                                        ("retrieve", {"query": "gratuity"})])
        self.assertEqual(sorted(out["tool_calls"]), ["documind_peer", "retrieve"])
        self.assertEqual([c["n"] for c in out["citations"]], [1])
        self.assertEqual([r["outcome"] for r in out["handoffs"]], ["answered"])

    def test_a_confused_deputy_is_refused_before_anything_is_sent(self):
        for tenant, account in (("zeta", AGENT_SA), ("acme", UI_SA)):     # a zeta asker; a peer on three rosters
            with self.subTest(tenant=tenant, account=account), mock.patch.object(peer, "PEER_ACCOUNT", account):
                self.seen.clear()
                out, read, lines, _, _ = self.turn([("documind_peer", {"request": "Which documents?"})], tenant=tenant)
                self.assertEqual((out["tool_calls"], out["refusals"]), (["documind_peer"], ["documind_peer"]))
                self.assertEqual((out["handoffs"][0]["outcome"], self.seen), ("refused", []))
                self.assertIn("confused deputy", read[0]["error"])
                self.assertFalse(any(t in read[0]["error"] for t in TENANT_NAMES))
                self.assertEqual((lines[0]["outcome"], lines[0]["peer_rosters"]), ("refused", len(ROSTERS[account])))

    def test_the_third_hand_off_of_a_turn_is_refused_side_by_side(self):
        out, read, lines, _, _ = self.turn([("documind_peer", {"request": f"q{k}"}) for k in range(3)])
        self.assertEqual(sorted(r["outcome"] for r in out["handoffs"]), ["answered", "answered", "refused"])
        self.assertEqual((len(self.posts()), out["refusals"]), (2, ["documind_peer"]))
        self.assertEqual(len(lines), 3)
        sent_ids = {p[3]["params"]["metadata"]["documind_handoff_id"] for p in self.posts()}
        self.assertEqual(sent_ids, {r["handoff_id"] for r in out["handoffs"] if r["outcome"] == "answered"})   # one id each

    def test_the_peers_task_failed_at_its_cap_is_data_for_the_model(self):
        self.mode["peer"] = "failed"
        out, read, _, _, _ = self.turn([("documind_peer", {"request": "Which documents?"})])
        self.assertEqual((out["handoffs"][0]["outcome"], out["handoffs"][0]["state"], out["refusals"]), ("failed", "failed", []))
        self.assertEqual(read, [{"error": "the peer's task ended failed: Max number of llm calls limit of `12` exceeded",
                                 "state": "failed"}])

    def test_a_slow_peer_is_cut_at_its_budget(self):
        self.mode["peer"] = "slow"
        with mock.patch.object(peer, "PEER_TIMEOUT_S", 0.5):
            out, read, _, meter, _ = self.turn([("documind_peer", {"request": "Which documents?"})])
        self.assertEqual(out["handoffs"][0]["outcome"], "timed_out")
        self.assertEqual(meter.tool_timeouts, ["documind_peer"])
        self.assertTrue(read[0]["timed_out"])
        self.assertEqual(read[0]["error"], "documind_peer did not answer within 1s and was abandoned")   # the floor
        self.assertEqual(out["answer"], "done [1]")                      # the turn still answers

    def test_a_shut_door_is_data_for_the_model(self):
        self.mode["peer"] = "shut"
        out, read, _, _, _ = self.turn([("documind_peer", {"request": "Which documents?"})])
        self.assertEqual(out["handoffs"][0]["outcome"], "error")
        self.assertIn("the peer could not be asked", read[0]["error"])
        self.assertEqual(out["refusals"], [])



if __name__ == "__main__":
    unittest.main()
