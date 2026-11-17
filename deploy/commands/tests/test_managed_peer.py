"""Offline checks for the A2A peer on Vertex AI Agent Engine (workshop lesson 10.9): commands/managed_peer.py.

    python -m unittest commands/tests/test_managed_peer.py -v          # from deploy/

Nothing here reaches Google. managed_peer.py sends every call through one seam, Seam.call(), whose backend these tests
replace with FakeGoogle: it answers as the APIs would - instances, the service account's IAM policy, the query API's
event stream, the Cloud Run peer's A2A reply, sessions, spans and log rows - and records every call, so each command
is driven end to end exactly as make runs it. The first classes need only the standard library: mk/managed.mk's
targets, the .PHONY line, mk/README.md, UNOWNED.md and the CI lines; what up stages (the peer byte for byte, the
wrapper, the .env and the config with nothing the platform reserves); up, ask, trace, sessions, smoke and down on the
fake, the refusals that name a fact, and the dry run, which builds no backend and imports no Google library.

The last classes need google-adk at the kit's pin (the chat image's pins; CI's chat-pins steps set
DOCUMIND_REQUIRE_LIBS=1). The staged package is loaded through ADK's own agent loader, as `adk api_server` in ADK's
Agent Engine image loads it: root_agent is the peer's own agent, its model GlobalGemini on location global, its tools
the peer's MCP toolset with the peer's credential hook, and ADK_MAX_LLM_CALLS=12 stops a turn at twelve model calls.
a2a-sdk and mcp, which the peer imports and the chat pins do not hold, are stood in when absent (and are the real ones
in the peer's own pins). ADK's own deploy (cli_deploy.to_agent_engine) runs on a stand-in vertexai and is held to the
config, Dockerfile and requirements it would send; LiveGoogle's REST and session calls run on stand-ins of google.auth's
session and of vertexai. Without the library those classes skip and say so.
"""
import asyncio
import contextlib
import importlib.util
import io
import json
import logging
import os
import re
import sys
import tempfile
import types
import unittest
import warnings
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[2]
ROOT = KIT.parent
for _p in (str(KIT / "commands"), str(KIT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import managed_peer as mp  # noqa: E402  (the standard library at import)
from shared import prices  # noqa: E402

try:
    ADK = importlib.util.find_spec("google.adk") is not None
except ModuleNotFoundError:
    ADK = False
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
PROJECT = "lane-for-tests-4821"          # not the placeholder: live commands refuse it
NUMBER = "12345"                         # short on purpose: a published test carries no number a leak scan would refuse
AGENT = f"documind-agent-sa@{PROJECT}.iam.gserviceaccount.com"
UI = f"documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"
OUTSIDER = f"documind-outsider-sa@{PROJECT}.iam.gserviceaccount.com"
SERVICE_AGENT = f"serviceAccount:service-{NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
ANSWER = "Gratuity becomes payable after five years of continuous service [1]."
REFUSAL = f"Error executing tool retrieve: {AGENT} is not on tenant 'zeta''s roster"


def read(*parts) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def refusal(code: int, message: str, status: str) -> "mp.Refused":
    return mp.Refused(code, json.dumps({"error": {"code": code, "message": message, "status": status}}))


class FakeGoogle:
    """Google, as these tests need it: every call recorded, any call made to fail by name."""

    def __init__(self, fail=None):
        self.fail, self.calls = dict(fail or {}), []
        self.alive, self.created, self.deleted, self.staged = {}, [], [], {}
        self.policy = {"version": 1, "etag": "BwYabc=", "bindings": [
            {"role": "roles/iam.serviceAccountUser", "members": [f"serviceAccount:sa-documind-cicd@{PROJECT}.iam.gserviceaccount.com"]}]}
        self.project_iam = {"bindings": [
            {"role": "roles/aiplatform.user", "members": [f"serviceAccount:documind-{n}-sa@{PROJECT}.iam.gserviceaccount.com"
                                                          for n in ("ui", "api", "ingest", "chat", "agent")]},
            {"role": "roles/owner", "members": ["user:someone@example.com"]},
            {"role": "roles/aiplatform.user", "members": ["user:conditional@example.com"], "condition": {"title": "x"}}]}
        self.sessions = {}                   # session id -> (engine name, user id)
        self.ids = iter(range(4400000000000000001, 4500000000000000000))
        self.sids = iter(range(7001, 9000))
        self.mcp_callers = [AGENT]
        self.spans = None                    # None: the peer's trace with no content; else these spans
        self.events = None                   # None: the scripted turns; else (message -> events)

    def _hit(self, method, *args):
        self.calls.append((method, args))
        rule = self.fail.get(method)
        error = rule(*args) if callable(rule) else rule
        if error is not None:
            raise error

    def methods(self):
        return [m for m, _ in self.calls]

    def project_number(self):
        self._hit("project_number")
        return NUMBER

    def project_policy(self):
        self._hit("project_policy")
        return self.project_iam

    def create_instance(self, region, display_name):
        self._hit("create_instance", region, display_name)
        name = f"projects/{NUMBER}/locations/{region}/reasoningEngines/{next(self.ids)}"
        self.alive[name] = {"displayName": display_name, "deployed": False}
        self.created.append(name)
        return name

    def get_instance(self, name):
        self._hit("get_instance", name)
        if name not in self.alive:
            raise refusal(404, f"{name} not found", "NOT_FOUND")
        out = {"name": name, "displayName": self.alive[name]["displayName"]}
        if self.alive[name]["deployed"]:                 # minInstances 0 is left out, as proto3 JSON leaves a zero
            out["spec"] = {"serviceAccount": AGENT, "deploymentSpec": {
                "maxInstances": 1, "env": [{"name": k, "value": v} for k, v in self.staged.get("env", {}).items()]}}
        return out

    def list_instances(self, region):
        self._hit("list_instances", region)
        return [{"name": n, "displayName": v["displayName"]} for n, v in self.alive.items() if mp.region_of(n) == region]

    def delete_instance(self, name):
        self._hit("delete_instance", name)
        if name not in self.alive:
            raise refusal(404, f"{name} not found", "NOT_FOUND")
        self.alive.pop(name)
        self.deleted.append(name)
        self.sessions = {k: v for k, v in self.sessions.items() if v[0] != name}

    def deploy(self, name, folder, env_file, config_file, display_name, adk_version):
        self._hit("deploy", name, folder, env_file, config_file, display_name, adk_version)
        folder = Path(folder)
        self.staged = {"folder": folder, "files": sorted(p.name for p in folder.iterdir()),
                       "agent": (folder / "agent.py").read_bytes(), "init": (folder / "__init__.py").read_bytes(),
                       "requirements": (folder / "requirements.txt").read_text(encoding="utf-8"),
                       "config": json.loads(Path(config_file).read_text(encoding="utf-8")),
                       "env": dict(line.split("=", 1) for line in Path(env_file).read_text(encoding="utf-8").splitlines()),
                       "env_file": Path(env_file), "display_name": display_name, "adk_version": adk_version}
        self.alive[name]["deployed"] = True

    def sa_policy(self, email):
        self._hit("sa_policy", email)
        return json.loads(json.dumps(self.policy))

    def set_sa_policy(self, email, policy):
        self._hit("set_sa_policy", email, policy)
        self.policy = policy
        return policy

    def turn(self, message):
        if self.events is not None:
            return self.events(message)
        usage = lambda i, o, t: {"prompt_token_count": i, "candidates_token_count": o, "thoughts_token_count": t}  # noqa: E731
        if message.startswith("For tenant "):
            return [{"author": "documind_peer", "usage_metadata": usage(1800, 25, 40), "content": {"role": "model", "parts": [
                        {"function_call": {"name": "retrieve", "args": {"query": "gratuity", "tenant": "zeta"}}}]}},
                    {"author": "documind_peer", "content": {"role": "user", "parts": [{"function_response": {
                        "name": "retrieve", "response": {"content": [{"type": "text", "text": REFUSAL}], "isError": True}}}]}},
                    {"author": "documind_peer", "usage_metadata": usage(2100, 30, 20), "content": {"role": "model", "parts": [
                        {"text": "I cannot answer for zeta: my account is not on that tenant's roster."}]}}]
        return [{"author": "documind_peer", "usage_metadata": usage(1800, 20, 60), "content": {"role": "model", "parts": [
                    {"function_call": {"name": "retrieve", "args": {"query": "gratuity continuous service"}}}]}},
                {"author": "documind_peer", "content": {"role": "user", "parts": [{"function_response": {
                    "name": "retrieve", "response": {"content": [{"type": "text", "text": "after five years"}],
                                                     "isError": False}}}]}},
                {"author": "documind_peer", "usage_metadata": usage(2600, 40, 30), "content": {"role": "model", "parts": [
                    {"text": ANSWER}]}}]

    def query(self, name, message, user_id, as_sa):
        self._hit("query", name, message, user_id, as_sa)
        if as_sa and "outsider" in as_sa:
            raise refusal(403, f"Permission 'aiplatform.reasoningEngines.query' denied on resource '//aiplatform.googleapis"
                               f".com/{name}' (or it may not exist).", "PERMISSION_DENIED")
        if name not in self.alive or not self.alive[name]["deployed"]:
            raise refusal(404, "not found", "NOT_FOUND")
        self.sessions[str(next(self.sids))] = (name, user_id)
        return {"status": 200, "events": self.turn(message), "first_event_s": 2.1, "total_s": 6.4}

    def a2a_send(self, url, message, as_sa):
        self._hit("a2a_send", url, message, as_sa)
        if message.startswith("For tenant "):
            text = "The server refused the request: my account is not on tenant zeta's roster."
        else:
            text = "Gratuity is payable after five years of continuous service."
        reply = {"jsonrpc": "2.0", "id": "1", "result": {"kind": "task", "status": {"state": "completed"},
                 "artifacts": [{"parts": [{"kind": "text", "text": text}]}],
                 "history": [{"role": "agent", "kind": "message",
                              "metadata": {"adk_event_id": "e1", "adk_usage_metadata": {"prompt_token_count": 1700,
                                                                                        "candidates_token_count": 18}},
                              "parts": [{"kind": "data", "data": {"name": "retrieve", "args": {"query": "gratuity"}},
                                         "metadata": {"adk_type": "function_call"}}]}]}}
        return {"status": 200, "reply": reply, "text": text, "first_event_s": None, "total_s": 3.3}

    def list_sessions(self, name):
        self._hit("list_sessions", name)
        return [{"user_id": u, "id": sid, "updated": int(sid)} for sid, (n, u) in self.sessions.items() if n == name]

    def session_as(self, name, session_id, user_id):
        self._hit("session_as", name, session_id, user_id)
        owner = self.sessions[session_id][1]
        if owner != user_id:                              # google-adk 2.8.0's own words
            raise ValueError(f"Session {session_id} does not belong to user {user_id}.")
        return {"user_id": owner, "id": session_id,
                "events": ["user: text 'After how many years...'", "documind_peer: function_call retrieve({})"]}

    def raw_session(self, name, session_id):
        self._hit("raw_session", name, session_id)
        return {"name": f"{name}/sessions/{session_id}", "user_id": self.sessions[session_id][1]}

    def delete_session(self, name, session_id, user_id):
        self._hit("delete_session", name, session_id, user_id)
        self.sessions.pop(session_id, None)

    def trace_spans(self, start, end):
        self._hit("trace_spans", start, end)
        if self.spans is not None:
            return self.spans
        return [{"trace": "t1", "name": "invocation", "labels": {}},
                {"trace": "t1", "name": "invoke_agent documind_peer", "labels": {"gen_ai.agent.name": "documind_peer"}},
                {"trace": "t1", "name": "call_llm", "labels": {"gcp.vertex.agent.llm_request": "{}"}},
                {"trace": "t1", "name": "execute_tool retrieve", "labels": {"gen_ai.tool.name": "retrieve"}},
                {"trace": "t2", "name": "POST /v1/query", "labels": {"/http/url": "https://documind-api.example/v1/query"}}]

    def log_entries(self, log_filter, limit):
        self._hit("log_entries", log_filter, limit)
        if "documind-mcp" in log_filter:
            return [{"jsonPayload": {"event": "mcp_call", "tool": "retrieve", "tenant": "acme", "caller": c}}
                    for c in self.mcp_callers]
        return [{"jsonPayload": {"event": "managed_peer_up", "GOOGLE_CLOUD_LOCATION": "asia-south1", "model":
                                 "gemini-3.6-flash", "model_location": "global", "ADK_MAX_LLM_CALLS": "12",
                                 "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": "false",
                                 "versions": {"google-adk": "2.8.0", "google-cloud-aiplatform": "1.140.0"}}}]


class Lane(unittest.TestCase):
    """main() exactly as make runs it, on FakeGoogle, with the records in a temporary folder."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.records = Path(self.tmp.name) / "records"

    def run_cmd(self, fake, *argv, region="asia-south1"):
        out = io.StringIO()
        code = mp.main([argv[0], "--project", PROJECT, "--region", region, "--services-region", "asia-south1",
                        "--records", str(self.records), *argv[1:]], google_factory=lambda project: fake, out=out,
                       sleep=lambda s: None)
        return code, out.getvalue()

    def state(self):
        path = self.records / "state.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def runs(self):
        path = self.records / "runs.ndjson"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def deployed(self, fake=None):
        fake = fake or FakeGoogle()
        code, _ = self.run_cmd(fake, "up")
        self.assertEqual(code, 0)
        return fake


# ------------------------------------------------------------------------------------------- the wiring

class TheWiring(unittest.TestCase):
    TARGETS = ("managed-peer-up", "managed-peer-ask", "managed-peer-trace", "managed-peer-smoke", "managed-peer-sessions",
               "managed-peer-down")

    def test_the_targets_the_phony_line_and_the_readme(self):
        mk, managed, readme = read("Makefile"), read("mk", "managed.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                       # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        self.assertTrue(set(self.TARGETS) <= set(phony))                  # later kits append after them
        self.assertIn("| `managed.mk` |", readme)
        for target in self.TARGETS:
            self.assertRegex(managed, rf"(?m)^{target}: \$\(if \$\(DRY_RUN\),,guard-project\)$")
            self.assertIn(f"`{target}`", readme)
        self.assertNotIn("managed-peer", read("mk", "agents.mk"))         # agents.mk is append-only, and not touched
        self.assertIn("MANAGED_PEER_REGION ?= $(REGION)", managed)
        self.assertIn("MANAGED_PEER_GRANT_ROLE ?= roles/iam.serviceAccountTokenCreator", managed)
        self.assertRegex(managed, r"(?m)^AIPLATFORM_PIN \?=$")
        self.assertIn("MANAGED_PEER = $(if $(DRY_RUN),$(PY) commands/managed_peer.py,PY=$(PY) "
                      "AIPLATFORM_PIN=$(AIPLATFORM_PIN) bash commands/managed-peer.sh)", managed)
        flags = re.search(r"(?ms)^MANAGED_PEER_FLAGS = (.*?)\n\n", managed).group(1)
        for needle in ("--project $(or $(PROJECT),documind-ai-YOUR-ID)", "--region $(MANAGED_PEER_REGION)",
                       "--services-region $(REGION)", "--grant-role $(MANAGED_PEER_GRANT_ROLE)", "$(if $(DRY_RUN),--dry-run,)",
                       "$(if $(JSON),--json,)", "$(if $(ASKER),--as $(ASKER),)"):
            self.assertIn(needle, flags)
        self.assertNotRegex(managed, r"\$\(AS\)")                         # make predefines AS: the assembler
        self.assertIn("--tenant $(TENANT) $(if $(Q),--question \"$(Q)\",) $(if $(HOST),--host $(HOST),)", managed)

    def test_the_venv_script(self):
        script = read("commands", "managed-peer.sh")
        self.assertIn('VENV="${MANAGED_PEER_VENV:-$HOME/managed-peer-venv}"', script)
        self.assertIn('"$VENV/bin/pip" install -q "google-adk[a2a,mcp]==$ADK_PIN" '
                      '"google-cloud-aiplatform[adk,agent_engines]${AIPLATFORM_PIN:+==$AIPLATFORM_PIN}"', script)
        self.assertIn('exec "$VENV/bin/python" commands/managed_peer.py "$@"', script)
        # the sed reads the peer's pin as this regex does
        sed = re.search(r"sed -n 's/(.*?)/\\1/p' services/agent/requirements.txt", script).group(1)
        self.assertEqual(sed, r"^google-adk\[[^]]*\]==\([0-9.]*\)$")
        self.assertEqual(re.search(r"(?m)^google-adk\[[^]]*\]==([0-9.]*)$", read("services", "agent", "requirements.txt")).group(1),
                         mp.adk_pin())
        self.assertEqual(mp.adk_pin(), "2.8.0")

    def test_both_chat_pin_steps_run_this_file(self):
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_managed_peer.py -v"
        self.assertIn(line, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = ROOT / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                              # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))

    def test_the_new_files_have_their_unowned_rows(self):
        # An UNOWNED.md row until lesson 10.9's page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = read("UNOWNED.md"), read("INDEX.md")
        for f in ("commands/managed_peer.py", "commands/managed_peer_agent.py", "commands/managed-peer.sh", "mk/managed.mk",
                  "commands/tests/test_managed_peer.py"):
            quoted = re.search(rf"(?m)^\| `{re.escape(f)}` \| \w+ \| [^|]*\b10\.9\b", index)
            self.assertTrue(f"| `{f}` | **10.9**" in unowned or quoted, f)
            self.assertTrue((KIT / f).exists(), f)

    def test_nothing_under_services_changes_and_no_terraform_names_it(self):
        self.assertNotIn("managed_peer", "".join(p.read_text(encoding="utf-8") for p in (KIT / "services" / "agent").iterdir()
                                                 if p.is_file()))
        self.assertNotIn("managed-peer", "".join(p.read_text(encoding="utf-8") for p in (KIT / "terraform").glob("*.tf")))

    def test_the_facts_are_rows_of_the_authors_probe(self):
        probe = ROOT / "tools" / "probe_agent_stack.py"
        if not probe.exists():
            self.skipTest("the probe lives in the authoring repository only")
        rows = dict(re.findall(r'^    \("(\d+)", "([^"]+)"', probe.read_text(encoding="utf-8"), re.M))
        self.assertEqual(sorted(rows, key=int), [str(n) for n in range(1, 13)])
        self.assertTrue(set(mp.FACTS) <= set(rows), set(mp.FACTS) - set(rows))
        self.assertNotIn("10", mp.FACTS)                                  # Memory Bank: the peer uses none


class WhatUpStages(unittest.TestCase):
    def test_the_peer_byte_for_byte_and_the_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            staged = mp.stage(Path(tmp), PROJECT, f"https://documind-mcp-{NUMBER}.asia-south1.run.app", "gemini-3.6-flash")
            folder = staged["folder"]
            extras = [f for f in ("chain.py", "pins.py", "tool_pins.json") if (KIT / "services/agent" / f).exists()]
            self.assertEqual(sorted(p.name for p in folder.iterdir()),      # lessons 10.7 and 10.8 add the extras
                             sorted(["__init__.py", "agent.py", "requirements.txt"] + extras))
            self.assertEqual((folder / "agent.py").read_bytes(), (KIT / "services/agent/agent.py").read_bytes())
            self.assertEqual((folder / "requirements.txt").read_bytes(), (KIT / "services/agent/requirements.txt").read_bytes())
            self.assertEqual((folder / "__init__.py").read_bytes(), (KIT / "commands/managed_peer_agent.py").read_bytes())
            self.assertNotEqual(staged["env_file"].parent, folder)                   # beside, so never shipped
            self.assertNotEqual(staged["config_file"].parent, folder)
            self.assertTrue(staged["env_file"].is_absolute() and staged["config_file"].is_absolute())

    def test_the_env_and_the_config(self):
        mcp = f"https://documind-mcp-{NUMBER}.asia-south1.run.app"
        config, env = mp.deploy_inputs(PROJECT, mcp, "gemini-3.6-flash")
        self.assertEqual(config, {"service_account": AGENT, "min_instances": 0, "max_instances": 1})
        self.assertEqual(env, {"MCP_URL": mcp, "AGENT_MODEL": "gemini-3.6-flash", "ADK_MAX_LLM_CALLS": "12"})
        self.assertFalse(set(env) & mp.RESERVED_ENV)
        # the Cloud Run peer's own variables, less what Agent Engine sets itself
        run_env = re.search(r'--set-env-vars="\^\|\^([^"]+)"', read("commands", "lesson-8.4.sh")).group(1)
        names = {kv.split("=", 1)[0] for kv in run_env.split("|")}
        self.assertEqual(names - set(env), {"GOOGLE_CLOUD_PROJECT", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_CLOUD_LOCATION",
                                            "SELF_URL", "PEER_CHAIN"})       # PEER_CHAIN: lesson 10.7's switch, off here
        self.assertIn("GOOGLE_CLOUD_LOCATION=global", run_env)          # what GlobalGemini stands in for
        self.assertEqual(mp.cloud_run_settings()["model"], "gemini-3.6-flash")

    def test_an_aiplatform_pin_is_one_line_and_only_when_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            staged = mp.stage(Path(tmp) / "a", PROJECT, "https://m", "gemini-3.6-flash", "1.140.0")
            req = (staged["folder"] / "requirements.txt").read_text(encoding="utf-8")
            self.assertTrue(req.startswith(read("services", "agent", "requirements.txt")))
            self.assertTrue(req.endswith("google-cloud-aiplatform[adk,agent_engines]==1.140.0\n"))
            self.assertEqual(req.count("google-cloud-aiplatform"), 1)

    def test_the_peers_own_modules_are_staged_when_the_kit_has_them(self):
        """13 October 2026: stage() copied agent.py alone, and a peer that imports chain.py or reads tool_pins.json
        (PEER_CHAIN, TOOL_PINS) would start on Agent Engine without them. When they exist beside agent.py they go too."""
        extras = {"chain.py": b"CHAIN = 1\n", "pins.py": b"PINS = 1\n", "tool_pins.json": b'{"retrieve": "sha"}\n'}
        with tempfile.TemporaryDirectory() as tmp:
            peer = Path(tmp) / "agent"
            peer.mkdir()
            for name in ("agent.py", "requirements.txt"):
                (peer / name).write_bytes((KIT / "services" / "agent" / name).read_bytes())
            for name, data in extras.items():
                (peer / name).write_bytes(data)
            with mock.patch.object(mp, "PEER", peer):
                staged = mp.stage(Path(tmp) / "root", PROJECT, "https://m", "gemini-3.6-flash")
            folder = staged["folder"]
            self.assertEqual(sorted(p.name for p in folder.iterdir()),
                             ["__init__.py", "agent.py", "chain.py", "pins.py", "requirements.txt", "tool_pins.json"])
            for name, data in extras.items():
                self.assertEqual((folder / name).read_bytes(), data)

    def test_the_cloud_run_peer_as_lesson_84_deploys_it(self):
        run = mp.cloud_run_settings()
        self.assertEqual({k: run[k] for k in ("min_instances", "max_instances", "concurrency", "timeout_s", "memory", "cpu",
                                              "account", "invokers")},
                         {"min_instances": 0, "max_instances": 5, "concurrency": 20, "timeout_s": 300, "memory": "1Gi",
                          "cpu": "1", "account": "documind-agent-sa", "invokers": ["documind-ui-sa", "documind-chat-sa"]})

    def test_the_peers_one_roster_and_make_smoke_agents_words(self):
        lane = read("commands", "lane.py")
        self.assertIn('plan.append(("acme", sa("agent")))', lane)        # roster_plan: the peer's account on acme alone
        self.assertEqual(mp.PEER_TENANT, "acme")
        smoke = read("smoke", "smoke_agent.py")
        self.assertIn('send(member, f"For tenant zeta: {QUESTION}")', smoke)
        self.assertEqual(mp.question_for("zeta", mp.QUESTION), f"For tenant zeta: {mp.QUESTION}")
        self.assertIn("(" + ", ".join(f'"{w}"' for w in mp.REFUSAL_WORDS) + ")", smoke)   # check 4's own words

    def test_the_wrapper(self):
        src = read("commands", "managed_peer_agent.py")
        compile(src, "managed_peer_agent.py", "exec")
        for needle in ("from . import agent as peer", "root_agent = peer.agent",
                       "root_agent.model = GlobalGemini(model=peer.MODEL)", 'return Client(enterprise=True, location="global")',
                       '"event": "managed_peer_up"'):
            self.assertIn(needle, src)
        self.assertNotIn("os.environ[", src)                              # it reads the environment and sets nothing

    def test_the_stage_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = io.StringIO()
            code = mp.main(["stage", "--dir", str(Path(tmp) / "peer"), "--project-number", NUMBER], out=out,
                           google_factory=self.fail)
            text = out.getvalue()
            self.assertEqual(code, 0)
            for name in ("agent.py", "requirements.txt", "__init__.py"):
                self.assertRegex(text, rf"documind_peer/{re.escape(name)}\s+byte for byte")
            self.assertIn(f"https://documind-mcp-{NUMBER}.asia-south1.run.app", text)
            self.assertIn("unpinned (fact 11)", text)
            code = mp.main(["stage", "--dir", str(Path(tmp) / "peer")], out=io.StringIO(), google_factory=self.fail)
            self.assertEqual(code, 2)                                     # a folder that is not empty


# ---------------------------------------------------------------------------------------------- the runs

class Up(Lane):
    def test_up_creates_grants_stages_and_deploys_once(self):
        fake = FakeGoogle()
        code, text = self.run_cmd(fake, "up")
        self.assertEqual(code, 0, text)
        (name,) = fake.created
        methods = fake.methods()
        self.assertLess(methods.index("create_instance"), methods.index("set_sa_policy"))
        self.assertLess(methods.index("set_sa_policy"), methods.index("deploy"))      # the grant before the build
        self.assertIn(("roles/iam.serviceAccountTokenCreator", SERVICE_AGENT), mp.bindings(fake.policy))
        self.assertIn(f"serviceAccount:sa-documind-cicd@{PROJECT}.iam.gserviceaccount.com", json.dumps(fake.policy))
        staged = fake.staged
        self.assertEqual(staged["agent"], (KIT / "services/agent/agent.py").read_bytes())
        self.assertEqual(staged["init"], (KIT / "commands/managed_peer_agent.py").read_bytes())
        self.assertEqual(staged["config"], {"service_account": AGENT, "min_instances": 0, "max_instances": 1})
        self.assertEqual(staged["env"]["MCP_URL"], f"https://documind-mcp-{NUMBER}.asia-south1.run.app")
        self.assertEqual((staged["display_name"], staged["adk_version"]), ("documind-managed-peer", "2.8.0"))
        self.assertFalse(staged["folder"].exists(), "the staging folder outlived the deploy")
        state = self.state()
        self.assertEqual((state["name"], state["region"], state["asks"]), (name, "asia-south1", 0))
        self.assertEqual(state["grant"], {"role": "roles/iam.serviceAccountTokenCreator", "member": SERVICE_AGENT, "on": AGENT})
        self.assertIn("deployed_at", state)
        self.assertIn("STANDING COST", text)
        self.assertIn("documind-agent-sa, documind-api-sa, documind-chat-sa, documind-ingest-sa, documind-ui-sa, 1 person(s)",
                      text)                                               # who may query, the conditional binding left out
        self.assertIn("minInstances absent (proto3 JSON leaves out a zero", text)
        (record,) = self.runs()
        self.assertEqual((record["command"], record["host"], record["settings"]["max_llm_calls"]), ("up", "agent_engine", 12))
        self.assertEqual(record["identity"]["runtime"], "documind-agent-sa")
        # again: deployed already, so nothing is created, granted or built
        before = len(fake.calls)
        code, text = self.run_cmd(fake, "up")
        self.assertEqual(code, 0)
        self.assertIn("deployed already", text)
        self.assertNotIn("deploy", [m for m, _ in fake.calls[before:]])
        code, text = self.run_cmd(fake, "up", "--redeploy")
        self.assertEqual((code, len(fake.created), fake.methods().count("deploy")), (0, 1, 2))
        self.assertEqual(fake.methods().count("set_sa_policy"), 1)        # the grant is there already

    def test_up_adopts_its_instance_by_display_name(self):
        fake = FakeGoogle()
        name = fake.create_instance("asia-south1", "documind-managed-peer")
        fake.calls.clear()
        code, _ = self.run_cmd(fake, "up")
        self.assertEqual(code, 0)
        self.assertEqual(fake.created, [name])
        self.assertEqual(self.state()["name"], name)

    def test_no_project_number_reaches_the_record(self):
        # Google's own accounts carry the project number, and most projects grant them Editor
        fake = FakeGoogle()
        fake.project_iam["bindings"].append({"role": "roles/editor", "members": [
            f"serviceAccount:{NUMBER}-compute@developer.gserviceaccount.com",
            f"serviceAccount:{NUMBER}@cloudservices.gserviceaccount.com"]})
        code, text = self.run_cmd(fake, "up")
        self.assertEqual(code, 0, text)
        (record,) = self.runs()
        self.assertIn("NUMBER-compute", record["identity"]["may_query"])
        self.assertIn("NUMBER", record["identity"]["may_query"])
        self.assertNotIn(NUMBER, json.dumps(record["identity"]))
        self.assertNotIn(f"{NUMBER}-compute", text)
        self.assertEqual(mp.short(SERVICE_AGENT.split(":", 1)[1]), "service-NUMBER")
        self.assertEqual(mp.short(AGENT), "documind-agent-sa")            # an account the project made keeps its id

    def test_a_grant_already_held_is_not_recorded_so_down_leaves_it(self):
        fake = FakeGoogle()
        fake.policy["bindings"].append({"role": "roles/iam.serviceAccountTokenCreator", "members": [SERVICE_AGENT]})
        self.run_cmd(fake, "up")
        self.assertNotIn("grant", self.state())
        self.assertNotIn("set_sa_policy", fake.methods())
        code, text = self.run_cmd(fake, "down")
        self.assertEqual(code, 0)
        self.assertIn(("roles/iam.serviceAccountTokenCreator", SERVICE_AGENT), mp.bindings(fake.policy))
        self.assertIn("none recorded as added", text)

    def test_a_refused_deploy_names_its_fact_and_keeps_the_instance_for_down(self):
        cases = {
            "1": RuntimeError("400 INVALID_ARGUMENT: Reasoning Engine is not supported in asia-south1."),
            "2": refusal(403, f"Permission 'iam.serviceAccounts.actAs' denied on {AGENT}", "PERMISSION_DENIED"),
            "3": refusal(400, "min_instances must be at least 1", "INVALID_ARGUMENT"),
            "11": RuntimeError("Build failed: ERROR: ResolutionImpossible: protobuf<7 and protobuf>=7"),
        }
        for row, error in cases.items():
            with self.subTest(row=row):
                self.records = Path(self.tmp.name) / f"records-{row}"
                fake = FakeGoogle(fail={"deploy": error})
                code, text = self.run_cmd(fake, "up")
                self.assertEqual(code, 3, text)
                self.assertIn(f"STOPPED on fact {row} of the author's Agent Engine probe: {mp.FACTS[row]}", text)
                self.assertIn("make managed-peer-down deletes it", text)
                self.assertEqual(self.state()["name"], fake.created[0])
                if row == "2":
                    self.assertIn("MANAGED_PEER_GRANT_ROLE=roles/iam.serviceAccountUser", text)
                code, text = self.run_cmd(fake, "down")
                self.assertEqual((code, fake.alive), (0, {}))
                self.assertNotIn(("roles/iam.serviceAccountTokenCreator", SERVICE_AGENT), mp.bindings(fake.policy))
        self.records = Path(self.tmp.name) / "records-other"
        code, text = self.run_cmd(FakeGoogle(fail={"deploy": RuntimeError("deadline exceeded")}), "up")
        self.assertEqual(code, 2)
        self.assertIn("STOPPED: the deploy stopped: deadline exceeded", text)

    def test_a_read_back_naming_another_account_is_fact_2(self):
        fake = FakeGoogle()
        real = fake.get_instance
        fake.get_instance = lambda name: {**real(name), "spec": {"serviceAccount": "123-compute@developer.gserviceaccount.com"}}
        code, text = self.run_cmd(fake, "up")
        self.assertEqual(code, 3)
        self.assertIn("STOPPED on fact 2", text)

    def test_a_region_already_in_use_is_named(self):
        fake = self.deployed()
        code, text = self.run_cmd(fake, "ask", region="us-central1")
        self.assertEqual(code, 2)
        self.assertIn("the managed peer is in asia-south1", text)

    def test_a_redeploy_starts_the_idle_clock_again(self):
        fake = self.deployed()
        self.run_cmd(fake, "ask")
        self.assertIn("last_ask", self.state())
        self.run_cmd(fake, "up", "--redeploy")
        self.assertNotIn("last_ask", self.state())
        self.assertEqual(self.state()["asks"], 0)
        self.run_cmd(fake, "ask")
        self.assertTrue(self.runs()[-1]["cold"]["first_after_deploy"])

    def test_no_credentials_and_no_venv_are_said_plainly(self):
        class DefaultCredentialsError(Exception):
            pass
        for error, words in ((DefaultCredentialsError("Your default credentials were not found."),
                              "no Application Default Credentials"),
                             (ImportError("No module named 'vertexai'"), "run it through commands/managed-peer.sh")):
            with self.subTest(error=type(error).__name__):
                code, text = self.run_cmd(FakeGoogle(fail={"list_instances": error}), "up")
                self.assertEqual(code, 2)
                self.assertIn(words, text)


class Ask(Lane):
    def test_acme_answered_with_its_record(self):
        fake = self.deployed()
        code, text = self.run_cmd(fake, "ask")
        self.assertEqual(code, 0, text)
        self.assertIn(ANSWER, text)
        self.assertIn("the expected answer", text)
        (method, args) = [c for c in fake.calls if c[0] == "query"][0]
        self.assertEqual(args[1:], (mp.QUESTION, "documind-ui-sa", UI))   # as documind-ui-sa, under its own user id
        rec = self.runs()[-1]
        self.assertEqual((rec["command"], rec["host"], rec["question"], rec["answered"]), ("ask", "agent_engine", "acme", True))
        self.assertEqual(rec["tool_calls"], ["retrieve"])
        self.assertEqual(rec["latency_s"], {"first_event": 2.1, "total": 6.4})
        self.assertEqual({k: rec["model"][k] for k in ("calls", "in", "out", "thinking")},
                         {"calls": 2, "in": 4400, "out": 60, "thinking": 90})
        self.assertEqual(rec["model"]["inr"], round(prices.inr(prices.usd("gemini-3.6-flash", 4400, 150, 0)), 4))
        self.assertTrue(rec["cold"]["first_after_deploy"])
        self.assertEqual(rec["identity"]["caller"], "documind-ui-sa")
        self.assertIn("unpinned", json.dumps(self.runs()[0]))
        for secret in (PROJECT, NUMBER, "4400000000000000001"):          # a record carries no identifier
            self.assertNotIn(secret, json.dumps(rec))
        self.run_cmd(fake, "ask")
        self.assertFalse(self.runs()[-1]["cold"]["first_after_deploy"])
        self.assertEqual(self.state()["asks"], 2)

    def test_zeta_refused_by_the_roster(self):
        fake = self.deployed()
        code, text = self.run_cmd(fake, "ask", "--tenant", "zeta")
        self.assertEqual(code, 0, text)
        self.assertIn("refused by the roster", text)
        self.assertIn(f"For tenant zeta: {mp.QUESTION}", [a[1] for m, a in fake.calls if m == "query"])
        rec = self.runs()[-1]
        self.assertEqual((rec["question"], rec["refused_by_roster"], rec["answered"]), ("zeta", True, None))
        fake.events = lambda message: [{"content": {"role": "model", "parts": [{"text": "Zeta's answer is five years."}]}}]
        code, text = self.run_cmd(fake, "ask", "--tenant", "zeta")
        self.assertEqual(code, 1)
        self.assertIn("NOT refused by the roster", text)

    def test_json_prints_the_record_alone(self):
        fake = self.deployed()
        code, text = self.run_cmd(fake, "ask", "--json")
        self.assertEqual(code, 0)
        rec = json.loads([line for line in text.splitlines() if line.startswith("{")][-1])
        self.assertEqual((rec["kind"], rec["answered"]), ("managed-peer/1", True))
        self.assertNotIn("answer: ", text)

    def test_without_an_instance(self):
        code, text = self.run_cmd(FakeGoogle(), "ask")
        self.assertEqual(code, 2)
        self.assertIn("no managed peer in asia-south1: make managed-peer-up first", text)

    def test_a_failed_turn_names_its_fact(self):
        cases = [
            ("5", "no ID token", [{"error_code": "500", "error_message": "google.auth.exceptions.DefaultCredentialsError: "
                                   "Neither metadata server or valid service account credentials are found."}]),
            ("2", "the door", [{"content": {"role": "user", "parts": [{"function_response": {"name": "retrieve", "response": {
                "error": "Client error '403 Forbidden' for url 'https://documind-mcp-x.asia-south1.run.app/mcp'"}}}]}}]),
            ("6", "the region", [{"error_code": "404", "error_message": "NOT_FOUND. Publisher Model `projects/x/locations/"
                                  "asia-south1/publishers/google/models/gemini-3.6-flash` was not found."}]),
            ("2", "sessions", [{"code": 403, "message": "403 PERMISSION_DENIED. Permission 'aiplatform.sessions.create' "
                                "denied on resource 'reasoningEngines/1/sessions'"}]),
        ]
        for n, (row, why, events) in enumerate(cases):
            with self.subTest(row=row, why=why):
                self.records = Path(self.tmp.name) / f"records-{n}"
                fake = self.deployed()
                fake.events = lambda message, e=events: e
                code, text = self.run_cmd(fake, "ask")
                self.assertEqual(code, 3, text)
                self.assertIn(f"STOPPED on fact {row} of", text)
                self.assertFalse(self.runs()[-1]["answered"])

    def test_documind_ui_sa_refused_is_fact_8(self):
        fake = self.deployed()
        fake.fail["query"] = refusal(403, "Permission 'aiplatform.reasoningEngines.query' denied", "PERMISSION_DENIED")
        code, text = self.run_cmd(fake, "ask")
        self.assertEqual(code, 3)
        self.assertIn("STOPPED on fact 8", text)
        self.assertIn("documind-ui-sa may not query the instance", text)

    def test_the_cloud_run_peer_asked_the_same_way(self):
        fake = FakeGoogle()
        code, text = self.run_cmd(fake, "ask", "--host", "cloudrun")
        self.assertEqual(code, 0, text)
        (args,) = [a for m, a in fake.calls if m == "a2a_send"]
        self.assertEqual(args, (f"https://documind-agent-{NUMBER}.asia-south1.run.app", mp.QUESTION, UI))
        rec = self.runs()[-1]
        self.assertEqual((rec["host"], rec["answered"], rec["tool_calls"]), ("cloud_run", True, ["retrieve"]))
        self.assertEqual(rec["hosting"]["max_instances"], 5)
        self.assertIn("documind-ui-sa, documind-chat-sa", rec["identity"]["door"])
        self.assertEqual(rec["model"]["calls"], 1)                        # adk_usage_metadata, once per event
        self.assertNotIn("create_instance", fake.methods())               # no managed instance is needed for it
        fake.a2a_send = lambda url, message, as_sa: {"status": 404, "reply": "Not Found", "text": ""}
        code, text = self.run_cmd(fake, "ask", "--host", "cloudrun")
        self.assertEqual(code, 2)
        self.assertIn("the Cloud Run peer refused the question: HTTP 404", text)


class Trace(Lane):
    def asked(self):
        fake = self.deployed()
        self.run_cmd(fake, "ask")
        return fake

    def test_the_spans_the_callers_and_the_runtimes_line(self):
        fake = self.asked()
        code, text = self.run_cmd(fake, "trace")
        self.assertEqual(code, 0, text)
        self.assertIn("4 span(s) in 1 trace(s): invocation, invoke_agent documind_peer, call_llm, execute_tool retrieve", text)
        self.assertNotIn("POST /v1/query", text)                          # another service's trace is not ours
        self.assertIn(f"caller {AGENT}", text)
        self.assertIn("GOOGLE_CLOUD_LOCATION=asia-south1, model gemini-3.6-flash on global, ADK_MAX_LLM_CALLS=12", text)
        rec = self.runs()[-1]
        self.assertEqual((rec["spans"], rec["content_in_spans"], rec["mcp_callers"]), (4, False, ["documind-agent-sa"]))
        filters = [a[0] for m, a in fake.calls if m == "log_entries"]
        self.assertTrue(any('jsonPayload.event="mcp_call"' in f and "timestamp<=" in f for f in filters))
        self.assertTrue(any('resource.type="aiplatform.googleapis.com/ReasoningEngine"' in f for f in filters))

    def test_the_question_in_a_span_is_fact_7(self):
        fake = self.asked()
        fake.spans = [{"trace": "t1", "name": "invoke_agent documind_peer", "labels": {}},
                      {"trace": "t1", "name": "call_llm", "labels": {"gcp.vertex.agent.llm_request": json.dumps(
                          {"contents": [{"parts": [{"text": mp.QUESTION}]}]})}}]
        code, text = self.run_cmd(fake, "trace")
        self.assertEqual(code, 3)
        self.assertIn("STOPPED on fact 7", text)
        self.assertIn("call_llm: gcp.vertex.agent.llm_request", text)

    def test_another_caller_during_the_ask_is_fact_2(self):
        fake = self.asked()
        fake.mcp_callers = [AGENT, f"123-compute@developer.gserviceaccount.com"]
        code, text = self.run_cmd(fake, "trace")
        self.assertEqual(code, 3)
        self.assertIn("STOPPED on fact 2", text)
        code, _ = self.run_cmd(fake, "trace", "--since", "60")            # a wide window only lists them
        self.assertEqual(code, 0)

    def test_no_span_yet_says_so(self):
        fake = self.asked()
        fake.spans = []
        code, text = self.run_cmd(fake, "trace", "--wait", "40")
        self.assertEqual(code, 0)
        self.assertIn("no trace naming documind_peer in Cloud Trace after 40 s", text)
        self.assertEqual(fake.methods().count("trace_spans"), 3)           # polled at 0, 20 and 40 s


class Sessions(Lane):
    def test_the_sessions_and_who_may_read_one(self):
        fake = self.deployed()
        self.run_cmd(fake, "ask")
        self.run_cmd(fake, "ask", "--tenant", "zeta")
        code, text = self.run_cmd(fake, "sessions")
        self.assertEqual(code, 0, text)
        self.assertIn("2 session(s) on the instance: documind-ui-sa 2", text)
        self.assertIn("refused by ADK's session service - Session 7002 does not belong to user another-user.", text)
        self.assertIn("the API's own read, which names no user, returned it (user_id 'documind-ui-sa')", text)
        rec = self.runs()[-1]
        self.assertEqual((rec["sessions"], rec["other_user_refused"], rec["raw_read_names_user"]), (2, True, True))
        code, text = self.run_cmd(fake, "sessions", "--delete")
        self.assertEqual((code, fake.sessions), (0, {}))
        self.assertIn("deleted 2 session(s)", text)


class Down(Lane):
    def test_down_deletes_by_name_takes_the_grant_back_and_says_so_twice(self):
        fake = self.deployed()
        name = fake.created[0]
        orphan = fake.create_instance("asia-south1", "documind-managed-peer-old")
        mine = fake.create_instance("asia-south1", "the-authors-own-agent")
        elsewhere = fake.create_instance("us-central1", "documind-managed-peer")
        code, text = self.run_cmd(fake, "down")
        self.assertEqual(code, 0, text)
        self.assertEqual(sorted(fake.deleted), sorted([name, orphan]))
        self.assertEqual(sorted(fake.alive), sorted([mine, elsewhere]))   # another name, another region: untouched
        self.assertIn(f"deleted, and read back gone: {name}", text)
        self.assertIn("grant taken back: roles/iam.serviceAccountTokenCreator", text)
        self.assertNotIn(("roles/iam.serviceAccountTokenCreator", SERVICE_AGENT), mp.bindings(fake.policy))
        self.assertIn(f"serviceAccount:sa-documind-cicd@{PROJECT}.iam.gserviceaccount.com", json.dumps(fake.policy))
        self.assertEqual(self.state(), {})
        code, text = self.run_cmd(fake, "down")
        self.assertEqual(code, 0)
        self.assertIn("nothing to delete: no documind-managed-peer* instance in asia-south1", text)
        self.assertIn("none recorded as added", text)
        self.assertEqual(self.runs()[-1]["deleted"], 0)

    def test_what_cannot_be_deleted_is_left_with_its_command(self):
        fake = self.deployed()
        name = fake.created[0]
        fake.fail["delete_instance"] = refusal(500, "Internal error.", "INTERNAL")
        code, text = self.run_cmd(fake, "down")
        self.assertEqual(code, 4)
        self.assertIn(f"LEFT: {name}", text)
        self.assertIn(f"agent_engines.delete(name='{name}', force=True)", text)
        self.assertEqual(self.state()["name"], name)                     # so the next down tries again
        self.assertNotIn("grant", self.state())                          # the grant went: each step stands alone
        fake.fail.pop("delete_instance")
        code, _ = self.run_cmd(fake, "down")
        self.assertEqual((code, fake.alive), (0, {}))

    def test_still_readable_after_a_minute_is_left(self):
        fake = self.deployed()
        fake.delete_instance = lambda name: fake.calls.append(("delete_instance", (name,)))   # accepted, never gone
        code, text = self.run_cmd(fake, "down")
        self.assertEqual(code, 4)
        self.assertIn("deleted, but still readable after 60 s", text)
        self.assertEqual(fake.methods().count("get_instance") - 1, 7)    # read back seven times, ten seconds apart


class Smoke(Lane):
    def test_the_smoke_deploys_checks_compares_and_deletes(self):
        fake = FakeGoogle()
        code, text = self.run_cmd(fake, "smoke")
        self.assertEqual(code, 0, text)
        for check in ("acme answered through documind-mcp", "acme answered again, warm", "zeta refused by the roster",
                      "the outsider refused by the platform", "documind-mcp saw documind-agent-sa",
                      "spans written, message content off", "sessions kept, another user refused",
                      "the runtime's settings: the model on global, the cap of 12, content off"):
            self.assertIn(f"[PASS] {check}", text)
        self.assertIn("(GOOGLE_CLOUD_LOCATION=asia-south1: fact 6)", text)
        self.assertIn("8 passed, 0 failed, 0 skipped", text)
        self.assertEqual(fake.alive, {})                                  # it deployed one, so it deleted it
        self.assertIn("deleting what this smoke deployed", text)
        self.assertIn("Cloud Run against Agent Engine", text)
        self.assertRegex(text, r"warm calls, median s\s+\| Cloud Run: 3\.3\s+\| Agent Engine: 6\.4")
        self.assertRegex(text, r"first call \(after a deploy, or a smoke's first\), s\s+\| Cloud Run: 3\.3\s+\| "
                               r"Agent Engine: 6\.4 \(idle \d+ s before\)")
        hosts = [r["host"] for r in self.runs() if r["command"] == "ask"]
        self.assertEqual((hosts.count("agent_engine"), hosts.count("cloud_run")), (3, 3))
        self.assertEqual(self.state(), {})

    def test_keep_keeps_and_an_existing_peer_is_never_deleted(self):
        fake = FakeGoogle()
        code, text = self.run_cmd(fake, "smoke", "--keep")
        self.assertEqual(code, 0)
        self.assertEqual(len(fake.alive), 1)
        self.assertIn("kept (--keep)", text)
        code, text = self.run_cmd(fake, "smoke")                          # now there is one: the smoke uses it
        self.assertEqual(code, 0)
        self.assertEqual(len(fake.alive), 1)
        self.assertEqual(len(fake.created), 1)
        self.assertNotIn("deleting what this smoke deployed", text)

    def test_a_failed_check_fails_the_smoke_and_still_deletes(self):
        fake = FakeGoogle()
        fake.events = lambda message: [{"content": {"role": "model", "parts": [{"text": "Five years, for anyone."}]}}]
        real_logs = fake.log_entries

        def logs(log_filter, limit):
            rows = real_logs(log_filter, limit)
            if "ReasoningEngine" in log_filter:                          # the runtime kept the default cap
                rows[0]["jsonPayload"]["ADK_MAX_LLM_CALLS"] = None
            return rows
        fake.log_entries = logs
        code, text = self.run_cmd(fake, "smoke")
        self.assertEqual(code, 1)
        self.assertIn("[FAIL] zeta refused by the roster", text)
        self.assertIn("[FAIL] acme answered through documind-mcp", text)  # no retrieve: an answer from nowhere
        self.assertIn("[FAIL] the runtime's settings: the model on global, the cap of 12, content off  read "
                      "('global', None, 'false') (facts 6 and 7)", text)
        self.assertEqual(fake.alive, {})

    def test_what_cannot_be_checked_is_skipped_with_a_line(self):
        fake = FakeGoogle()
        real_query = fake.query

        def query(name, message, user_id, as_sa):
            if as_sa and "outsider" in as_sa:
                raise mp.Stop(f"could not mint a token as {as_sa} (make operators grants that to the lane's operators)")
            return real_query(name, message, user_id, as_sa)
        fake.query = query
        fake.a2a_send = lambda url, message, as_sa: {"status": 404, "reply": "Not Found", "text": ""}
        fake.spans, fake.mcp_callers = [], []
        code, text = self.run_cmd(fake, "smoke", "--wait", "0")
        self.assertEqual(code, 0, text)
        self.assertIn("[SKIP] the outsider refused by the platform  (no token as documind-outsider-sa", text)
        self.assertIn("[SKIP] documind-mcp saw documind-agent-sa", text)
        self.assertIn("[SKIP] spans written, message content off", text)
        self.assertIn("[SKIP] the Cloud Run peer", text)
        self.assertIn("5 passed, 0 failed, 3 skipped", text)
        fake = FakeGoogle()
        fake.log_entries = lambda log_filter, limit: []                  # no runtime line, and no documind-mcp row
        code, text = self.run_cmd(fake, "smoke", "--wait", "0")
        self.assertEqual(code, 0, text)
        self.assertIn("[SKIP] the runtime's settings: the model on global, the cap of 12, content off  (its line is "
                      "not in Cloud Logging", text)

    def test_a_deploy_that_stops_on_a_fact_still_deletes_the_instance(self):
        fake = FakeGoogle(fail={"deploy": RuntimeError("Reasoning Engine is not supported in asia-south1")})
        code, text = self.run_cmd(fake, "smoke")
        self.assertEqual(code, 3)
        self.assertIn("STOPPED on fact 1", text)
        self.assertEqual(fake.alive, {})


class DryRun(Lane):
    def test_every_live_command_prints_its_calls_and_makes_none(self):
        before = set(sys.modules)
        for argv in (["up"], ["ask"], ["ask", "--host", "cloudrun"], ["trace"], ["sessions"], ["smoke"], ["down"]):
            with self.subTest(argv=argv):
                out = io.StringIO()
                code = mp.main([*argv, "--dry-run", "--records", str(self.records)], out=out, sleep=self.fail,
                               google_factory=lambda project: self.fail("a dry run built a backend"))
                text = out.getvalue()
                self.assertEqual(code, 0, text)
                self.assertIn("DRY RUN", text.splitlines()[0])
                self.assertIn("would call:", text)
                self.assertNotIn("  call:", text)
        self.assertFalse(self.records.exists(), "a dry run wrote the state or a record")
        loaded = sorted(m for m in set(sys.modules) - before if m.split(".")[0] in ("vertexai", "google", "requests"))
        self.assertEqual(loaded, [], "a dry run imported a cloud library")

    def test_the_dry_up_shows_what_it_would_send(self):
        out = io.StringIO()
        mp.main(["up", "--dry-run", "--records", str(self.records)], out=out, google_factory=self.fail)
        text = out.getvalue()
        for needle in (".agent_engines.create(config={'display_name': 'documind-managed-peer'})",
                       ":setIamPolicy  # adds roles/iam.serviceAccountTokenCreator for serviceAccount:service-NUMBER@",
                       "cli_deploy.to_agent_engine(", "otel_to_cloud=True", "adk_version='2.8.0'",
                       '"ADK_MAX_LLM_CALLS": "12"', '"min_instances": 0, "max_instances": 1'):
            self.assertIn(needle, text)

    def test_a_dry_down_says_a_dry_run_records_no_grant(self):
        """13 October 2026: the dry run's down step said "none recorded as added by make managed-peer-up", as if an up
        had run and added none; a dry run records nothing, and says so - in the smoke's down step too."""
        for argv in (["down"], ["smoke"]):
            out = io.StringIO()
            code = mp.main([*argv, "--dry-run", "--records", str(self.records)], out=out, google_factory=self.fail,
                           sleep=lambda s: None)
            text = out.getvalue()
            self.assertEqual(code, 0, text)
            self.assertIn("grant: dry run, no grant recorded (a dry run records nothing); nothing to take back", text)
            self.assertNotIn("none recorded as added", text)

    def test_the_placeholder_project_is_only_for_a_dry_run(self):
        with contextlib.redirect_stderr(io.StringIO()):
            for argv in (["up"], ["down"], ["ask", "--project", "Not_A_Project", "--dry-run"],
                         ["up", "--region", "Mumbai", "--dry-run"], ["up", "--aiplatform-pin", "latest", "--dry-run"],
                         ["up", "--grant-role", "owner", "--dry-run"], ["ask", "--host", "gke"]):
                with self.assertRaises(SystemExit, msg=argv):
                    mp.parse_args(argv)
        self.assertEqual(mp.parse_args(["compare"]).command, "compare")


class Compare(Lane):
    def test_the_table_from_the_records(self):
        fake = self.deployed()
        self.run_cmd(fake, "ask")
        self.run_cmd(fake, "ask")
        out = io.StringIO()
        mp.main(["compare", "--records", str(self.records)], out=out)
        text = out.getvalue()
        self.assertIn("| Cloud Run: no record yet", text)
        self.assertIn("Agent Engine: 6.4 (idle", text)
        self.assertRegex(text, r"runs as\s+\| Cloud Run: no record yet\s+\| Agent Engine: documind-agent-sa")
        self.run_cmd(fake, "ask", "--host", "cloudrun")
        out = io.StringIO()
        mp.main(["compare", "--records", str(self.records), "--json"], out=out)
        table = json.loads(out.getvalue())["table"]
        self.assertTrue(any("roles/run.invoker on documind-agent" in line for line in table))
        self.assertTrue(any("aiplatform.reasoningEngines.query" in line for line in table))


# ------------------------------------------------------------------------------- under the pinned ADK

def _stand_in_peer_imports():
    """a2a-sdk and mcp, which the peer imports and the chat image's pins do not hold, as stand-ins - only when absent."""
    saved = {}
    try:
        from google.adk.a2a.utils.agent_to_a2a import to_a2a  # noqa: F401
        from google.adk.tools.mcp_tool import McpToolset  # noqa: F401
        return saved
    except ImportError:
        pass
    from google.adk.tools.base_toolset import BaseToolset
    from starlette.applications import Starlette

    class McpToolset(BaseToolset):
        def __init__(self, *, connection_params, header_provider=None, **kwargs):
            super().__init__()
            self.connection_params, self.header_provider = connection_params, header_provider

        async def get_tools(self, readonly_context=None):
            return []

        async def close(self):
            return None

    class StreamableHTTPConnectionParams:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    mods = {"google.adk.a2a.utils.agent_to_a2a": types.SimpleNamespace(to_a2a=lambda agent, **kw: Starlette()),
            "google.adk.tools.mcp_tool": types.SimpleNamespace(McpToolset=McpToolset, __path__=[]),
            "google.adk.tools.mcp_tool.mcp_session_manager": types.SimpleNamespace(
                StreamableHTTPConnectionParams=StreamableHTTPConnectionParams)}
    for name, module in mods.items():
        saved[name] = sys.modules.get(name)
        sys.modules[name] = module
    return saved


@unittest.skipUnless(ADK or REQUIRE, "needs google-adk at the kit's pin: pip install -r services/chat/requirements.txt")
class StagedPeerUnderAdk(unittest.TestCase):
    """The staged package, loaded the way `adk api_server` in ADK's Agent Engine image loads it."""

    def setUp(self):
        if not ADK:
            self.fail("DOCUMIND_REQUIRE_LIBS=1 but google-adk is not installed")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.mcp = f"https://documind-mcp-{NUMBER}.asia-south1.run.app"
        staged = mp.stage(Path(self.tmp.name), PROJECT, self.mcp, "gemini-3.6-flash")
        env = {"MCP_URL": self.mcp, "AGENT_MODEL": "gemini-3.6-flash", "ADK_MAX_LLM_CALLS": "12",
               "GOOGLE_CLOUD_LOCATION": "asia-south1",                   # what ADK's Dockerfile sets
               "ADK_DISABLE_LOAD_DOTENV": "1"}                           # ADK's loader would read any .env above the folder
        patch = mock.patch.dict(os.environ, env)
        patch.start()
        self.addCleanup(patch.stop)
        saved = _stand_in_peer_imports()
        self.addCleanup(lambda: [sys.modules.pop(k, None) if v is None else sys.modules.__setitem__(k, v)
                                 for k, v in saved.items()])
        self.addCleanup(lambda: [sys.modules.pop(k) for k in list(sys.modules) if k.split(".")[0] == mp.APP_NAME])
        agents_dir = str(staged["folder"].parent)
        self.addCleanup(lambda: [sys.path.remove(p) for p in list(sys.path) if p == agents_dir])
        from google.adk.cli.utils.agent_loader import AgentLoader
        with self.assertLogs("documind.managed_peer", "INFO") as logged:
            self.root = AgentLoader(agents_dir=agents_dir).load_agent(mp.APP_NAME)
        self.logged = logged.output
        self.wrapper = sys.modules[mp.APP_NAME]
        self.peer = sys.modules[f"{mp.APP_NAME}.agent"]

    def test_root_agent_is_the_peers_own_agent_on_location_global(self):
        from google.adk.agents import LlmAgent
        self.assertIsInstance(self.root, LlmAgent)
        self.assertIs(self.root, self.peer.agent)                         # the object the A2A app serves on Cloud Run
        self.assertEqual(self.root.name, "documind_peer")
        self.assertEqual(self.root.instruction, self.peer.INSTRUCTION)
        self.assertEqual(type(self.root.model).__name__, "GlobalGemini")
        self.assertEqual(self.root.model.model, "gemini-3.6-flash")
        made = []
        with mock.patch.object(self.wrapper, "Client", lambda **kw: made.append(kw) or "client"):
            self.assertEqual(self.root.model.api_client, "client")
        self.assertEqual(made, [{"enterprise": True, "location": "global"}])
        (toolset,) = self.root.tools
        self.assertIs(toolset.header_provider if hasattr(toolset, "header_provider") else toolset._header_provider,
                      self.peer._mcp_headers)                             # the peer's own credential, minted per call
        self.assertEqual(self.peer.MCP_URL, self.mcp)
        line = json.loads(self.logged[0].split(":", 2)[2])
        self.assertEqual((line["event"], line["GOOGLE_CLOUD_LOCATION"], line["model_location"], line["ADK_MAX_LLM_CALLS"]),
                         ("managed_peer_up", "asia-south1", "global", "12"))
        self.assertEqual(line["versions"]["google-adk"], "2.8.0")

    def test_the_cap_stops_a_turn_at_twelve_model_calls(self):
        from google.adk.agents.invocation_context import LlmCallsLimitExceededError
        from google.adk.agents.run_config import RunConfig
        from google.adk.models.base_llm import BaseLlm
        from google.adk.models.llm_response import LlmResponse
        from google.adk.runners import InMemoryRunner
        from google.genai import types as gt
        self.assertEqual(RunConfig().max_llm_calls, 12)

        class Loop(BaseLlm):
            model: str = "loop"
            sent: list = []

            async def generate_content_async(self, llm_request, stream=False):
                self.sent.append(llm_request)
                yield LlmResponse(content=gt.Content(role="model", parts=[
                    gt.Part(function_call=gt.FunctionCall(name="noop", args={}))]),
                    usage_metadata=gt.GenerateContentResponseUsageMetadata(prompt_token_count=10, candidates_token_count=2))

        def noop() -> dict:
            """Does nothing, so the model asks again."""
            return {"ok": True}
        loop = Loop(sent=[])
        self.root.model, self.root.tools = loop, [noop]

        async def go():
            runner = InMemoryRunner(agent=self.root, app_name=mp.APP_NAME)
            session = await runner.session_service.create_session(app_name=mp.APP_NAME, user_id="documind-ui-sa")
            async for _ in runner.run_async(user_id="documind-ui-sa", session_id=session.id,
                                            new_message=gt.Content(role="user", parts=[gt.Part(text=mp.QUESTION)])):
                pass
        with self.assertRaises(LlmCallsLimitExceededError), self.assertLogs(level="ERROR") as logged:   # ADK logs it too
            asyncio.run(go())
        self.assertEqual(len(loop.sent), 12)
        self.assertIn("Max number of llm calls limit of `12` exceeded", "\n".join(logged.output))


class _Answer(types.SimpleNamespace):
    def model_dump(self, **kwargs):
        return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in vars(self).items()}


async def _aiter(items):
    for item in items:
        yield item


class FakeVertexai:
    """The vertexai module, as far as google-adk 2.8.0's deploy and session service, and LiveGoogle, call it."""

    def __init__(self):
        import datetime
        self.now = datetime.datetime(2026, 11, 16, 10, 0, tzinfo=datetime.timezone.utc)
        self.calls, self.sessions, self.update = [], {"7001": "documind-ui-sa"}, {}

    def module(self):
        fake, mod = self, types.ModuleType("vertexai")

        class Sessions:
            def __init__(self):
                self.events = types.SimpleNamespace(list=self.list_events)

            def answer(self, name):
                return _Answer(name=name, user_id=fake.sessions[name.rsplit("/", 1)[-1]], update_time=fake.now,
                               session_state=None)

            async def get(self, name):
                fake.calls.append(("sessions.get", name))
                return self.answer(name)

            async def list_events(self, name, **kwargs):
                return _aiter([])

            async def list(self, name, config):
                fake.calls.append(("sessions.list", name, dict(config)))
                return _aiter([self.answer(f"{name}/sessions/{sid}") for sid in fake.sessions])

            async def delete(self, name):
                fake.calls.append(("sessions.delete", name))
                fake.sessions.pop(name.rsplit("/", 1)[-1], None)

        class AsyncClient:
            def __init__(self):
                self.agent_engines = types.SimpleNamespace(sessions=Sessions())

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

        class Engines:
            def create(self, config=None):
                fake.calls.append(("create", config))
                return _Answer(api_resource=_Answer(name=f"projects/{NUMBER}/locations/asia-south1/reasoningEngines/123"))

            def update(self, name, config):
                fake.update = {"name": name, "config": config, "dockerfile": Path("Dockerfile").read_text(),
                               "requirements": Path("agents/documind_peer/requirements.txt").read_text(),
                               "agent": Path("agents/documind_peer/agent.py").read_bytes(),
                               "init": Path("agents/documind_peer/__init__.py").read_bytes()}

            def delete(self, name, force=False):
                fake.calls.append(("delete", name, force))

        class Client:
            def __init__(self, project=None, location=None, credentials=None, http_options=None, api_key=None):
                fake.calls.append(("Client", project, location))
                self.agent_engines, self.aio = Engines(), AsyncClient()

        mod.Client = Client
        return mod


class FakeRest:
    """google.auth's AuthorizedSession, answering each REST call LiveGoogle makes from a table."""

    class Response:
        def __init__(self, status, body=None, lines=()):
            self.status_code, self.body, self.lines = status, body, list(lines)
            self.text = json.dumps(body) if body is not None else "\n".join(self.lines)

        def json(self):
            return self.body

        def iter_lines(self, decode_unicode=False):
            return iter(self.lines)

    def __init__(self):
        self.sent = []

    def session(self, credentials):
        rest = self

        class Session:
            def request(self, method, url, json=None, params=None, stream=False, timeout=None):
                rest.sent.append((method, url, json, params, credentials))
                return rest.answer(method, url, json)
        return Session()

    def answer(self, method, url, body):
        if url.endswith(":streamQuery"):
            return self.Response(200, lines=[": keep-alive", 'data: {"content": {"role": "model", "parts": [{"text": "ok"}]}}',
                                             "", "data: [DONE]"])
        if "cloudresourcemanager" in url and url.endswith(":getIamPolicy"):
            return self.Response(200, {"bindings": [{"role": "roles/aiplatform.user", "members": [f"serviceAccount:{UI}"]}]})
        if "cloudresourcemanager" in url:
            return self.Response(200, {"projectId": PROJECT, "projectNumber": NUMBER})
        if url.endswith(":getIamPolicy"):
            return self.Response(200, {"bindings": [], "etag": "x"})
        if url.endswith(":setIamPolicy"):
            return self.Response(200, body["policy"])
        if "cloudtrace" in url:
            return self.Response(200, {"traces": [{"traceId": "t1", "spans": [{"name": "invoke_agent documind_peer"}]}]})
        if "logging.googleapis.com" in url:
            return self.Response(200, {"entries": [{"jsonPayload": {"event": "mcp_call", "caller": AGENT}}]})
        if url.endswith("/reasoningEngines"):
            return self.Response(200, {"reasoningEngines": [{"name": "n", "displayName": "documind-managed-peer"}]})
        if url.endswith("/gone"):
            return self.Response(404, {"error": {"code": 404, "message": "not found", "status": "NOT_FOUND"}})
        return self.Response(200, {"name": url.split("/v1/", 1)[-1]})


@unittest.skipUnless(ADK or REQUIRE, "needs google-adk at the kit's pin: pip install -r services/chat/requirements.txt")
class LiveGoogleOffline(unittest.TestCase):
    """The one class only a live run uses: ADK's own deploy and session service on a stand-in vertexai, and google.auth
    on a stand-in AuthorizedSession. What it would send is what is checked."""

    def setUp(self):
        if not ADK:
            self.fail("DOCUMIND_REQUIRE_LIBS=1 but google-adk is not installed")
        self.vertex, self.rest = FakeVertexai(), FakeRest()
        for patch in (mock.patch.dict(sys.modules, {"vertexai": self.vertex.module()}),
                      mock.patch("google.auth.default", return_value=("ADC", PROJECT)),
                      mock.patch("google.auth.transport.requests.AuthorizedSession", self.rest.session),
                      mock.patch.dict(os.environ, {}, clear=False)):
            patch.start()
            self.addCleanup(patch.stop)
        for name in ("GOOGLE_API_KEY", "GOOGLE_GENAI_USE_ENTERPRISE", "GOOGLE_GENAI_USE_VERTEXAI"):
            os.environ.pop(name, None)
        progress = logging.getLogger("vertexai_genai.agentengines")       # deploy() gives it a handler
        handlers, level = list(progress.handlers), progress.level
        self.addCleanup(lambda: (setattr(progress, "handlers", handlers), progress.setLevel(level)))
        self.live = mp.LiveGoogle(PROJECT)
        self.name = f"projects/{NUMBER}/locations/asia-south1/reasoningEngines/123"

    def deploy(self, pin=""):
        import importlib.metadata
        if importlib.metadata.version("google-adk") != "2.8.0":
            self.skipTest("ADK's deploy is read at the kit's pin, 2.8.0")
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), \
                warnings.catch_warnings(record=True) as warned:
            warnings.simplefilter("always")
            staged = mp.stage(Path(tmp), PROJECT, f"https://documind-mcp-{NUMBER}.asia-south1.run.app", "gemini-3.6-flash", pin)
            self.live.deploy(self.name, staged["folder"], staged["env_file"], staged["config_file"], mp.DISPLAY_NAME,
                             mp.adk_pin())
        self.assertEqual([str(w.message) for w in warned if issubclass(w.category, DeprecationWarning)
                          and "deprecated" in str(w.message)], [])             # what the learner's deploy prints
        return self.vertex.update

    def test_adks_own_deploy_sends_the_peer(self):
        sent = self.deploy()
        config = sent["config"]
        self.assertEqual(sent["name"], self.name)
        self.assertFalse([c for c in self.vertex.calls if c[0] in ("create", "delete")])   # the id is given
        self.assertEqual((config["service_account"], config["min_instances"], config["max_instances"]), (AGENT, 0, 1))
        self.assertEqual((config["display_name"], config["description"]), (mp.DISPLAY_NAME, mp.DESCRIPTION))
        self.assertEqual(config["env_vars"], {"MCP_URL": f"https://documind-mcp-{NUMBER}.asia-south1.run.app",
                                              "AGENT_MODEL": "gemini-3.6-flash", "ADK_MAX_LLM_CALLS": "12",
                                              "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
                                              "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": "false"})
        self.assertEqual(config["agent_framework"], "google-adk")
        self.assertEqual(config["source_packages"], ["agents/documind_peer", "Dockerfile"])
        self.assertIn("async_stream_query", [m["name"] for m in config["class_methods"]])
        self.assertIn("ENV GOOGLE_CLOUD_LOCATION=asia-south1", sent["dockerfile"])          # why GlobalGemini
        self.assertIn('RUN pip install "google-adk[a2a]==2.8.0"', sent["dockerfile"])
        self.assertIn("--otel_to_cloud", sent["dockerfile"])
        self.assertEqual(sent["agent"], (KIT / "services/agent/agent.py").read_bytes())
        self.assertEqual(sent["init"], (KIT / "commands/managed_peer_agent.py").read_bytes())
        peer_reqs = read("services", "agent", "requirements.txt")
        self.assertTrue(sent["requirements"].startswith(peer_reqs))
        self.assertEqual(sent["requirements"][len(peer_reqs):],                          # fact 11: appended, unpinned
                         "google-cloud-aiplatform[adk,agent_engines]\ngoogle-adk[a2a]==2.8.0\n")

    def test_a_pin_stops_adk_appending_its_own_line(self):
        sent = self.deploy("1.140.0")
        self.assertTrue(sent["requirements"].endswith("google-cloud-aiplatform[adk,agent_engines]==1.140.0\n"))
        self.assertEqual(sent["requirements"].count("google-cloud-aiplatform"), 1)

    def test_instances_and_sessions_go_through_adk(self):
        self.assertEqual(self.live.create_instance("asia-south1", mp.DISPLAY_NAME), self.name)
        self.assertIn(("create", {"display_name": mp.DISPLAY_NAME}), self.vertex.calls)
        self.assertEqual(self.live.list_sessions(self.name)[0]["user_id"], "documind-ui-sa")
        self.assertIn(("sessions.list", "reasoningEngines/123", {}), self.vertex.calls)    # no user filter sent
        with self.assertRaisesRegex(ValueError, "does not belong to user another-user"):
            self.live.session_as(self.name, "7001", mp.OTHER_USER)
        self.assertEqual(self.live.session_as(self.name, "7001", "documind-ui-sa")["user_id"], "documind-ui-sa")
        self.assertEqual(self.live.raw_session(self.name, "7001")["user_id"], "documind-ui-sa")
        self.live.delete_session(self.name, "7001", "documind-ui-sa")
        self.assertEqual(self.vertex.sessions, {})
        self.live.delete_instance(self.name)
        self.assertIn(("delete", self.name, True), self.vertex.calls)

    def test_a_delete_of_a_missing_instance_reads_as_404(self):
        class Gone(Exception):
            code = 404
        engines = types.SimpleNamespace(delete=mock.Mock(side_effect=Gone("404 NOT_FOUND")))
        with mock.patch.object(self.live, "_client", return_value=types.SimpleNamespace(agent_engines=engines)):
            with self.assertRaises(mp.Refused) as refused:
                self.live.delete_instance(self.name)
        self.assertEqual(refused.exception.status, 404)

    def test_the_rest_calls(self):
        self.assertEqual(self.live.project_number(), NUMBER)
        self.assertEqual(mp.bindings(self.live.project_policy()), {("roles/aiplatform.user", f"serviceAccount:{UI}")})
        self.assertEqual(self.live.get_instance(self.name)["name"], self.name)
        self.assertEqual(self.live.list_instances("asia-south1"), [{"name": "n", "displayName": "documind-managed-peer"}])
        self.assertEqual(self.live.sa_policy(AGENT), {"bindings": [], "etag": "x"})
        policy = mp.with_binding({"bindings": [], "etag": "x"}, mp.GRANT_ROLE, SERVICE_AGENT)
        self.assertEqual(self.live.set_sa_policy(AGENT, policy), policy)
        self.assertEqual(self.live.trace_spans("a", "b")[0]["name"], "invoke_agent documind_peer")
        self.assertEqual(self.live.log_entries(mp.MCP_ROWS, 5)[0]["jsonPayload"]["caller"], AGENT)
        reply = self.live.query(self.name, mp.QUESTION, "operator", None)
        self.assertEqual(mp.read_turn(reply["events"])["answer"], "ok")                    # keep-alive and [DONE] skipped
        self.assertIsNotNone(reply["first_event_s"])
        urls = [(m, u) for m, u, *_ in self.rest.sent]
        self.assertIn(("POST", f"https://iam.googleapis.com/v1/projects/{PROJECT}/serviceAccounts/{AGENT}:setIamPolicy"), urls)
        _, url, body, params, _ = next(s for s in self.rest.sent if s[1].endswith(":streamQuery"))
        self.assertEqual(url, f"https://asia-south1-aiplatform.googleapis.com/v1/{self.name}:streamQuery")
        self.assertEqual((body, params), ({"class_method": "async_stream_query",
                                           "input": {"user_id": "operator", "message": mp.QUESTION}}, {"alt": "sse"}))
        _, _, body, _, _ = next(s for s in self.rest.sent if "logging.googleapis.com" in s[1])
        self.assertEqual((body["resourceNames"], body["orderBy"]), ([f"projects/{PROJECT}"], "timestamp desc"))
        with self.assertRaises(mp.Refused) as refused:
            self.live.get_instance(f"projects/{NUMBER}/locations/asia-south1/reasoningEngines/gone")
        self.assertEqual(refused.exception.status, 404)

    def test_a_question_as_an_account_mints_first_and_says_when_it_cannot(self):
        minted = mock.MagicMock()
        with mock.patch("google.auth.impersonated_credentials.Credentials", return_value=minted) as make:
            self.live.query(self.name, mp.QUESTION, "documind-ui-sa", UI)
        self.assertEqual(make.call_args.kwargs["target_principal"], UI)
        minted.refresh.assert_called_once()
        self.assertIs(self.rest.sent[-1][4], minted)                       # the question went out as that account
        minted.refresh.side_effect = RuntimeError("Permission 'iam.serviceAccounts.getAccessToken' denied")
        with mock.patch("google.auth.impersonated_credentials.Credentials", return_value=minted), \
                self.assertRaises(mp.Stop) as stopped:
            self.live.query(self.name, mp.QUESTION, "documind-outsider-sa", OUTSIDER)
        self.assertIn("make operators", str(stopped.exception))

    def test_the_cloud_run_peer_is_asked_as_make_smoke_agent_asks_it(self):
        idc = mock.MagicMock(token="id-token-for-the-peer")
        url = f"https://documind-agent-{NUMBER}.asia-south1.run.app"
        with mock.patch("google.auth.impersonated_credentials.Credentials", return_value=mock.MagicMock()), \
                mock.patch("google.auth.impersonated_credentials.IDTokenCredentials", return_value=idc) as make, \
                mock.patch.object(mp.smoke_agent, "http", return_value=(200, {"result": {"kind": "task", "artifacts": [
                    {"parts": [{"kind": "text", "text": "five years"}]}]}})) as http:
            got = self.live.a2a_send(url + "/", mp.QUESTION, UI)
        self.assertEqual(make.call_args.kwargs["target_audience"], url + "/")
        self.assertTrue(make.call_args.kwargs["include_email"])
        path, token, body = http.call_args.args
        self.assertEqual((path, token, body["method"]), ("/", "id-token-for-the-peer", "message/send"))
        self.assertEqual(body["params"]["message"]["parts"], [{"kind": "text", "text": mp.QUESTION}])
        self.assertEqual(mp.smoke_agent.AGENT_URL, url)
        self.assertEqual((got["status"], got["text"]), (200, "five years"))
        with self.assertRaisesRegex(mp.Stop, "admits documind-ui-sa and documind-chat-sa alone"):
            self.live.a2a_send(url, mp.QUESTION, None)                    # --as me: no person is an invoker


if __name__ == "__main__":
    unittest.main()
