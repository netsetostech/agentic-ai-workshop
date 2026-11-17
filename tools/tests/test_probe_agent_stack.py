"""tools/probe_agent_stack.py - the Agent Engine probe the author runs in batch 0 (PR 10.9-A) - offline, on a fake Google.

Nothing here reaches Google. The probe sends every call through one Cloud layer, which takes a backend factory: these
tests pass FakeBackend, which answers as the APIs would and carries real-looking identifiers (a project id, a number,
instance and session ids, a person's email), so the scrub is tested on what a live run would carry; the dry-run tests
pass a factory that fails the test if it is ever called. The deployed agent's own module runs under google-adk 2.8.0
on a scripted model when the chat pins are installed (CI's chat-pins step sets DOCUMIND_REQUIRE_LIBS=1); elsewhere
that half is skipped, and says so.
"""
import asyncio
import base64
import contextlib
import importlib.metadata
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("probe_agent_stack_under_test", ROOT / "tools" / "probe_agent_stack.py")
probe = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = probe          # dataclasses look their module up by name
_spec.loader.exec_module(probe)
from tools.leakscan import scan_text  # noqa: E402  (the probe put the repo root on sys.path)

PROJECT = "lane-for-tests-4821"        # not documind-ai-*: the scrub must replace it by name, not by pattern
NUMBER = "246813579024"
PERSON = "someone.real@gmail.com"
SESSION = "4471950381092315136"
try:
    ADK = importlib.util.find_spec("google.adk") is not None
except ModuleNotFoundError:
    ADK = False
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"


def refusal(code: int, message: str, status: str) -> "probe.Refused":
    return probe.Refused(code, json.dumps({"error": {"code": code, "message": message, "status": status}}))


class FakeBackend:
    """Google, as these tests need it: every call recorded, any call made to fail by name."""

    def __init__(self, project=PROJECT, fail=None):
        self.project, self.fail = project, dict(fail or {})
        self.calls, self.alive, self.created, self.deleted = [], {}, [], []
        self.sessions, self.memory, self.staged = {}, "", {}
        self.ids = iter(range(9100000000000000001, 9200000000000000000))

    def _hit(self, method, *args):
        self.calls.append((method, args))
        rule = self.fail.get(method)
        error = rule(*args) if callable(rule) else rule
        if error is not None:
            raise error

    def methods(self):
        return [m for m, _ in self.calls]

    def versions(self, region):
        self._hit("versions", region)
        return {"python": "3.12.10", "google-adk": "2.8.0", "google-cloud-aiplatform": "1.130.0", "google-genai": "2.22.0",
                "google-auth": "2.57.1", "pip_check": "No broken requirements found.",
                "namespaces": {"agent_engines": True, "agent_engines.sessions": True, "agent_engines.memories": True,
                               "runtimes": True}}

    def create_instance(self, region, display_name):
        self._hit("create_instance", region, display_name)
        name = f"projects/{NUMBER}/locations/{region}/reasoningEngines/{next(self.ids)}"
        self.alive[name] = display_name
        self.created.append(name)
        return name

    def get_instance(self, name):
        self._hit("get_instance", name)
        if name not in self.alive:
            raise refusal(404, f"{name} not found", "NOT_FOUND")
        return {"name": name, "displayName": self.alive[name],
                "spec": {"serviceAccount": f"documind-agent-sa@{self.project}.iam.gserviceaccount.com",
                         "deploymentSpec": {"maxInstances": 1, "containerConcurrency": 9,      # minInstances 0 is left out
                                            "resourceLimits": {"cpu": "4", "memory": "4Gi"},
                                            "env": [{"name": "PROBE_MODEL", "value": "gemini-3.6-flash"}]}}}

    def list_instances(self, region):
        self._hit("list_instances", region)
        return [{"name": n, "displayName": d} for n, d in self.alive.items() if probe.region_of(n) == region]

    def delete_instance(self, name):
        self._hit("delete_instance", name)
        self.alive.pop(name, None)
        self.deleted.append(name)

    def deploy(self, name, folder, env_file, config_file, display_name):
        self._hit("deploy", name, folder, env_file, config_file, display_name)
        self.staged = {"folder": Path(folder), "env_file": Path(env_file),
                       "agent": (Path(folder) / "agent.py").read_text(encoding="utf-8"),
                       "config": json.loads(Path(config_file).read_text(encoding="utf-8")),
                       "env": Path(env_file).read_text(encoding="utf-8")}
        engine = name.rsplit("/", 1)[-1]
        return (f"Reading agent platform config from {config_file}\nDeployed to Agent Platform: {name}\n"
                f"https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/asia-south1/agent-engines/"
                f"{engine}/playground?project={self.project}\n")

    def query(self, name, message, user_id, as_sa=None):
        self._hit("query", name, message, user_id, as_sa)
        if as_sa and "outsider" in as_sa:
            raise refusal(403, f"Permission 'aiplatform.reasoningEngines.query' denied on resource "
                               f"'//aiplatform.googleapis.com/{name}' (or it may not exist).", "PERMISSION_DENIED")
        account = f"documind-agent-sa@{self.project}.iam.gserviceaccount.com"
        audience = f"https://documind-mcp-{NUMBER}.asia-south1.run.app"
        token = {"minted": True, "aud": audience, "email": account, "iss": "https://accounts.google.com", "lifetime_s": 3600}
        facts = {"env": {"GOOGLE_CLOUD_LOCATION": probe.region_of(name), "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": "false",
                         "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true"},
                 "env_names": ["GOOGLE_CLOUD_AGENT_ENGINE_ID", "GOOGLE_CLOUD_LOCATION", "GOOGLE_CLOUD_PROJECT", "K_SERVICE"],
                 "versions": {"google-adk": "2.8.0", "google-cloud-aiplatform": "1.130.0", "google-genai": "2.22.0"},
                 "metadata": {"service_account": account, "project_number": NUMBER}, "audience": audience,
                 "id_token_metadata": token, "id_token_fetch": token, "mcp_door": {"status": 200}}
        events = []
        if probe.NO_MODEL not in message:
            marker = re.search(r"pm[0-9a-f]{8}", message).group(0)
            facts["gemini"] = {
                "environment": {"answered": False, "error": f"ClientError: 404 NOT_FOUND. Publisher Model `projects/"
                                                            f"{self.project}/locations/asia-south1/publishers/google/models/"
                                                            f"gemini-3.6-flash` was not found"},
                "global": {"answered": True, "text": "ok"}}
            events += [{"author": "probe_model", "content": {"role": "model", "parts": [
                           {"function_call": {"name": "probe_tool", "args": {"marker": marker}}}]}},
                       {"author": "probe_model", "content": {"role": "model", "parts": [{"text": "ok"}]}}]
        events.append({"author": "documind_probe",
                       "content": {"role": "model", "parts": [{"text": "PROBE_FACTS " + json.dumps(facts)}]}})
        return {"status": 200, "events": events, "first_event_s": 3.4, "total_s": 7.9}

    def create_session(self, name, user_id, ttl):
        self._hit("create_session", name, user_id, ttl)
        self.sessions[SESSION] = user_id
        return SESSION

    def append_event(self, name, session_id, text):
        self._hit("append_event", name, session_id, text)

    def get_session(self, name, session_id, user_id):
        self._hit("get_session", name, session_id, user_id)
        if self.sessions.get(session_id) != user_id:       # google-adk 2.8.0's own words
            raise ValueError(f"Session {session_id} does not belong to user {user_id}.")
        return {"user_id": user_id, "id": session_id, "events": 1}

    def raw_get_session(self, name, session_id):
        self._hit("raw_get_session", name, session_id)
        return {"name": f"{name}/sessions/{session_id}", "user_id": self.sessions[session_id],
                "expire_time": "2026-10-19T10:15:00Z"}

    def list_sessions(self, name):
        self._hit("list_sessions", name)
        return [{"user_id": user, "id": sid} for sid, user in self.sessions.items()]

    def delete_session(self, name, session_id, user_id):
        self._hit("delete_session", name, session_id, user_id)
        self.sessions.pop(session_id, None)

    def add_memory(self, name, user_id, fact):
        self._hit("add_memory", name, user_id, fact)
        self.memory = fact

    def search_memory(self, name, user_id, query):
        self._hit("search_memory", name, user_id, query)
        return [self.memory]

    def sa_policy(self, email):
        self._hit("sa_policy", email)
        return {"version": 1, "etag": "BwYabc=", "bindings": [{"role": "roles/iam.serviceAccountUser", "members": [
            f"serviceAccount:sa-documind-cicd@{self.project}.iam.gserviceaccount.com", f"user:{PERSON}"]}]}

    def sa_permissions(self, email, permissions):
        self._hit("sa_permissions", email, permissions)
        return ["iam.serviceAccounts.actAs"]

    def engine_policy(self, name):
        self._hit("engine_policy", name)
        raise refusal(404, "Method not found.", "NOT_FOUND")

    def trace_spans(self, start, end):
        self._hit("trace_spans", start, end)
        return [{"trace": "a1b2", "name": "invocation", "labels": {}},
                {"trace": "a1b2", "name": "invoke_agent documind_probe", "labels": {"gen_ai.agent.name": "documind_probe"}},
                {"trace": "a1b2", "name": "generate_content gemini-3.6-flash",
                 "labels": {"gen_ai.request.model": "gemini-3.6-flash", "gcp.vertex.agent.llm_request": "{}"}},
                {"trace": "a1b2", "name": "execute_tool probe_tool",
                 "labels": {"gen_ai.tool.name": "probe_tool", "gcp.vertex.agent.tool_call_args": "{}"}},
                {"trace": "zz99", "name": "POST /v1/query",
                 "labels": {"/http/url": f"https://documind-api-{NUMBER}.asia-south1.run.app/v1/query"}}]


def no_sleep(seconds):
    return None


def table_rows(facts: str) -> dict:
    """{row: (status cell, finding cell)} from the facts table's summary."""
    rows = {}
    for line in facts.splitlines():
        m = re.match(r"\| (\d+) \| .*? \| (.*?) \| (.*) \|$", line)
        if m:
            rows[m.group(1)] = (m.group(2), m.group(3))
    return rows


def evidence(facts: str, row: str) -> str:
    """One row's evidence section."""
    start = facts.index(f"\n### {row}. ")
    end = facts.find("\n### ", start + 1)
    return facts[start:end if end > 0 else facts.index("\n## Left behind")]


class Live(unittest.TestCase):
    """A live run, on FakeBackend: main() exactly as the author runs it with --yes."""

    def run_live(self, backend, *argv):
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(probe, "_git_commit", return_value="abc1234"):
            path = Path(tmp) / "facts.md"
            code = probe.main(["--project", PROJECT, "--yes", "--date", "2026-10-19", "--out", str(path), *argv],
                              backend_factory=lambda project: backend, out=out, sleep=no_sleep)
            facts = path.read_text(encoding="utf-8") if path.exists() else ""
        return code, out.getvalue(), facts


class DryRun(unittest.TestCase):
    def dry(self, *argv):
        def no_backend(project):
            raise AssertionError("a dry run built a backend")

        def no_sleep_allowed(seconds):
            raise AssertionError("a dry run slept")

        out, before = io.StringIO(), set(sys.modules)
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch("subprocess.run") as run, mock.patch("subprocess.Popen") as popen, \
                mock.patch("tempfile.mkdtemp") as mkdtemp:
            path = Path(tmp) / "facts.md"
            code = probe.main(["--project", probe.PLACEHOLDER, "--out", str(path), *argv],
                              backend_factory=no_backend, out=out, sleep=no_sleep_allowed)
            self.assertFalse(path.exists(), "a dry run wrote the facts table")
        for spy in (run, popen, mkdtemp):
            spy.assert_not_called()
        loaded = sorted(m for m in set(sys.modules) - before if m.split(".")[0] in ("vertexai", "google", "requests"))
        self.assertEqual(loaded, [], "a dry run imported a cloud library")
        self.assertEqual(code, 0)
        return out.getvalue()

    def test_dry_run_makes_no_call_and_prints_every_one(self):
        text = self.dry("--dry-run")
        self.assertNotIn("] call:", text)                       # every line says "would call"
        for region in ("us-central1", "asia-south1"):
            self.assertIn(f"location='{region}').agent_engines.create(config=", text)
        self.assertEqual(text.count(".agent_engines.create("), 3)  # two empty instances and the runtime
        self.assertEqual(text.count(".agent_engines.delete("), 3)  # and each deleted by name
        for call in ("cli_deploy.to_agent_engine(", ":streamQuery?alt=sse", "VertexAiSessionService(",
                     "VertexAiMemoryBankService(", ":getIamPolicy", ":testIamPermissions", "cloudtrace.googleapis.com",
                     "delete_session(", "# expect 404", "pip check"):
            self.assertIn(call, text)
        self.assertLess(text.index("Cost note"), text.index("== preflight"))
        self.assertIn("RUN NOTE", text)
        self.assertEqual(scan_text(text, []), [])

    def test_the_default_is_a_dry_run(self):
        text = self.dry()
        self.assertIn("DRY RUN", text.splitlines()[0])
        self.assertIn("would call", text)

    def test_cleanup_mode_dry_runs_too(self):
        text = self.dry("--cleanup")
        self.assertIn("would call: GET https://us-central1-aiplatform.googleapis.com/v1/projects/", text)
        self.assertNotIn(".delete(", text)


class Cleanup(Live):
    def test_cleanup_runs_after_a_failure(self):
        fake = FakeBackend(fail={"deploy": RuntimeError("Cloud Build failed: step 2 exited 1")})
        code, text, facts = self.run_live(fake)
        self.assertEqual(len(fake.created), 3)
        self.assertEqual(sorted(fake.deleted), sorted(fake.created))
        self.assertEqual(fake.alive, {})
        self.assertEqual(fake.sessions, {})
        methods = fake.methods()
        self.assertLess(methods.index("delete_session"), methods.index("delete_instance"))   # the session by name first
        self.assertEqual(code, 0)
        self.assertIn("Left behind: nothing", text)
        rows = table_rows(facts)
        self.assertTrue(rows["2"][0].startswith("not tested"), rows["2"])
        self.assertIn("Cloud Build failed", rows["2"][1])

    def test_cleanup_runs_after_an_interrupt(self):
        fake = FakeBackend(fail={"query": KeyboardInterrupt()})
        code, text, facts = self.run_live(fake)
        self.assertEqual(code, 130)
        self.assertEqual(fake.alive, {})
        self.assertIn("Interrupted", text)
        self.assertTrue(facts)

    def test_what_is_left_behind_is_listed_with_its_delete_command(self):
        stuck = lambda name: refusal(500, "Internal error.", "INTERNAL") if "/us-central1/" in name else None  # noqa: E731
        fake = FakeBackend(fail={"delete_instance": stuck})
        code, text, facts = self.run_live(fake)
        self.assertEqual(code, 3)
        (left,) = fake.alive
        self.assertIn("NOT SCRUBBED", text)                     # the real name, so the command runs as printed
        self.assertIn(f"agent_engines.delete(name='{left}', force=True)", text)
        self.assertIn(f"--project {PROJECT} --region us-central1 --cleanup --yes", text)
        section = facts.split("## Left behind")[1]
        self.assertIn("reasoningEngines/ENGINE_ID", section)
        self.assertIn("--cleanup --yes", section)
        for secret in (left.rsplit("/", 1)[-1], NUMBER, PROJECT):
            self.assertNotIn(secret, facts)

    def test_an_orphan_of_this_run_is_found_and_deleted(self):
        fake = FakeBackend()
        real_create = fake.create_instance

        def created_but_lost(region, display_name):     # the API made it, and the client never heard back
            real_create(region, display_name)
            raise TimeoutError("the create's operation did not finish in time")

        fake.create_instance = lambda region, display: (created_but_lost if region == "us-central1" and
                                                        display.endswith("-us-central1") else real_create)(region, display)
        code, text, _ = self.run_live(fake)
        self.assertEqual(fake.alive, {})
        self.assertEqual(code, 0)
        self.assertIn("an orphan of this run", text)

    def test_cleanup_mode_deletes_only_probe_instances(self):
        fake = FakeBackend()
        fake.alive = {f"projects/{NUMBER}/locations/us-central1/reasoningEngines/11": "documind-probe-20261019-0930-us-central1",
                      f"projects/{NUMBER}/locations/us-central1/reasoningEngines/12": "the-authors-own-agent",
                      f"projects/{NUMBER}/locations/asia-south1/reasoningEngines/13": "documind-probe-20261019-0930-runtime"}
        out = io.StringIO()
        code = probe.main(["--project", PROJECT, "--cleanup", "--yes"], backend_factory=lambda project: fake, out=out,
                          sleep=no_sleep)
        self.assertEqual(code, 0)
        self.assertEqual(list(fake.alive.values()), ["the-authors-own-agent"])
        self.assertNotIn(NUMBER, out.getvalue())


class Isolation(Live):
    def test_one_refused_step_does_not_stop_the_others(self):
        def not_in_mumbai(region, display):
            if region == "asia-south1" and display.endswith("-asia-south1"):
                return refusal(400, "Reasoning Engine is not supported in asia-south1.", "INVALID_ARGUMENT")
        fake = FakeBackend(fail={"create_instance": not_in_mumbai,
                                 "add_memory": refusal(403, "Memory Bank is not enabled for this project.", "PERMISSION_DENIED")})
        code, _, facts = self.run_live(fake)
        rows = table_rows(facts)
        self.assertIn("observed (us-central1)", rows["1"][0])
        self.assertIn("refused (asia-south1)", rows["1"][0])
        self.assertIn("Reasoning Engine is not supported in asia-south1", rows["1"][1])
        self.assertIn("refused (us-central1)", rows["10"][0])
        self.assertIn("not tested (asia-south1)", rows["10"][0])
        for row in ("2", "3", "5", "7"):                      # the runtime, the token and the trace still ran
            self.assertTrue(rows[row][0].startswith("observed"), (row, rows[row]))
        self.assertIn("refused (ADK get as another user)", rows["9"][0])   # on us-central1's instance instead
        self.assertRegex(rows["9"][0], r"observed \([^)]*raw sessions\.get")
        self.assertIn("/us-central1/", "".join(str(a) for m, a in fake.calls if m == "create_session"))
        self.assertEqual(fake.alive, {})
        self.assertEqual(code, 0)

    def test_a_refused_deploy_names_the_grant_and_the_rest_still_runs(self):
        words = ("Failed to deploy to Agent Platform: 403 PERMISSION_DENIED. Permission "
                 "'iam.serviceAccounts.getAccessToken' denied on documind-agent-sa@" + PROJECT + ".iam.gserviceaccount.com "
                 "for service-" + NUMBER + "@gcp-sa-aiplatform-re.iam.gserviceaccount.com")
        fake = FakeBackend(fail={"deploy": refusal(403, words, "PERMISSION_DENIED")})
        code, _, facts = self.run_live(fake)
        self.assertEqual(code, 0)
        rows = table_rows(facts)
        self.assertIn("refused (deploy)", rows["2"][0])
        self.assertIn("observed (grant)", rows["2"][0])
        self.assertIn("grant roles/iam.serviceAccountTokenCreator on documind-agent-sa@documind-ai-YOUR-ID", evidence(facts, "2"))
        self.assertIn("--member=serviceAccount:service-NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com "
                      "--role=roles/iam.serviceAccountTokenCreator", evidence(facts, "2"))
        for row in ("4", "5", "6", "7", "8"):
            self.assertIn("not tested", rows[row][0])
        self.assertTrue(rows["9"][0])
        self.assertTrue(rows["1"][0].startswith("observed"))
        self.assertEqual(fake.alive, {})


class FactsTable(Live):
    def test_the_facts_table_has_every_row(self):
        fake = FakeBackend()
        code, _, facts = self.run_live(fake)
        self.assertEqual(code, 0)
        rows = table_rows(facts)
        self.assertEqual(list(rows), probe.ROW_IDS)
        for row, title, _ in probe.ROWS:
            self.assertIn(f"| {row} | {title} |", facts)
            self.assertIn(f"### {row}. {title}", facts)
            for part in re.split(r";\s*", rows[row][0]):
                self.assertTrue(part.startswith(probe.STATUSES), (row, part))
        self.assertIn("2026-10-19", facts.splitlines()[0])
        self.assertIn("abc1234", facts)
        # what each row found, as the fake Google answered it
        self.assertEqual(rows["2"][0], "observed")
        self.assertIn("the account the deploy asked for", evidence(facts, "2"))
        self.assertIn("no binding on documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com was needed",
                      evidence(facts, "2"))
        self.assertIn("minInstances absent (proto3 JSON leaves out a zero", evidence(facts, "3"))
        self.assertIn("first event after 3.4 s, reply complete after 7.9 s", evidence(facts, "4"))
        self.assertIn("not tested (pricing page)", rows["4"][0])
        self.assertIn("AUTHOR: quote the pricing page's line on idle time", evidence(facts, "4"))
        self.assertEqual(rows["5"][0], "observed")
        self.assertIn("an ID token for https://documind-mcp-NUMBER.asia-south1.run.app", evidence(facts, "5"))
        self.assertIn("GET /health answered 200", evidence(facts, "5"))
        self.assertIn("'asia-south1' - the region, not global", evidence(facts, "6"))
        self.assertIn("refused (Gemini on that location)", rows["6"][0])
        self.assertEqual(rows["7"][0], "observed")
        self.assertIn("execute_tool probe_tool", evidence(facts, "7"))
        self.assertNotIn("POST /v1/query", evidence(facts, "7"))     # another service's trace is not the probe's
        self.assertIn("marker is in no span label", evidence(facts, "7"))
        self.assertRegex(rows["8"][0], r"refused \(instance IAM policy, as documind-outsider-sa\)")
        self.assertIn("observed (as documind-ui-sa)", rows["8"][0])
        self.assertIn("does not belong to user", evidence(facts, "9"))
        self.assertIn("expireTime 2026-10-19T10:15:00Z", evidence(facts, "9"))
        self.assertEqual(rows["10"][0], "observed")
        self.assertIn("google-cloud-aiplatform 1.130.0", evidence(facts, "11"))
        self.assertIn("ADK's deploy installed google-adk 2.8.0", evidence(facts, "11"))
        self.assertIn(probe.PRICING_URL, evidence(facts, "12"))
        self.assertIn("Nothing: every resource", facts)

    def test_no_identifier_reaches_the_table_or_the_console(self):
        fake = FakeBackend()
        code, text, facts = self.run_live(fake)
        self.assertEqual(code, 0)
        for secret in (PROJECT, NUMBER, PERSON, SESSION, *(n.rsplit("/", 1)[-1] for n in fake.created)):
            self.assertNotIn(secret, facts, secret)
            self.assertNotIn(secret, text, secret)
        self.assertEqual(scan_text(facts, []), [])
        self.assertIn("user:yours", facts)
        self.assertIn("serviceAccount:sa-documind-cicd@documind-ai-YOUR-ID.iam.gserviceaccount.com", facts)

    def test_the_staged_agent_and_its_config(self):
        fake = FakeBackend()
        self.run_live(fake)
        self.assertEqual(fake.staged["agent"], probe.AGENT_SOURCE)
        self.assertEqual(fake.staged["config"], {"service_account": f"documind-agent-sa@{PROJECT}.iam.gserviceaccount.com",
                                                 "min_instances": 0, "max_instances": 1})
        names = {line.split("=", 1)[0] for line in fake.staged["env"].splitlines()}
        self.assertEqual(names, {"PROBE_MODEL", "PROBE_MCP_REGION"})
        self.assertFalse(names & probe.RESERVED_ENV)
        self.assertNotEqual(fake.staged["env_file"].parent, fake.staged["folder"])    # beside, so never shipped
        self.assertFalse(fake.staged["folder"].exists(), "the staging folder outlived the deploy")

    def test_a_second_run_on_the_same_day_takes_the_next_name(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(probe, "_git_commit", return_value=""):
            path = Path(tmp) / "agent-engine-probe-2026-10-19.md"
            for _ in range(2):
                probe.main(["--project", PROJECT, "--yes", "--out", str(path)], backend_factory=lambda p: FakeBackend(),
                           out=io.StringIO(), sleep=no_sleep)
            self.assertTrue(path.exists())
            self.assertTrue((Path(tmp) / "agent-engine-probe-2026-10-19-2.md").exists())


class Scrub(unittest.TestCase):
    def test_scrubbing_removes_ids_numbers_and_emails(self):
        scrub = probe.Scrubber(PROJECT)
        text = (f"projects/{NUMBER}/locations/asia-south1/reasoningEngines/9100000000000000001/sessions/{SESSION} "
                f"https://documind-mcp-{NUMBER}.asia-south1.run.app "
                f"documind-agent-sa@{PROJECT}.iam.gserviceaccount.com "
                f"service-{NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com {NUMBER}-compute@developer.gserviceaccount.com "
                f"user:{PERSON} owner@company.co.in project {NUMBER}, \"projectNumber\": \"{NUMBER}\" "
                f"resource=projects%2F{PROJECT}%2Flocations "
                "Bearer eyJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJodHRwcyJ9.c2lnbmF0dXJlLWJ5dGVz ya29.a0AfH6SMBxTokenTokenToken "
                r"C:\Users\someone\AppData\Local\Temp\ae109-x /home/someone/probe-venv")
        out = scrub(text)
        for secret in (PROJECT, NUMBER, "9100000000000000001", SESSION, "someone", "company.co.in", "eyJ", "ya29."):
            self.assertNotIn(secret, out, secret)
        for placeholder in ("projects/NUMBER/locations/asia-south1/reasoningEngines/ENGINE_ID/sessions/SESSION_ID",
                            "https://documind-mcp-NUMBER.asia-south1.run.app",
                            "documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
                            "service-NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com",
                            "NUMBER-compute@developer.gserviceaccount.com", "user:yours", "project NUMBER",
                            "[REDACTED TOKEN]", r"C:\Users\YOU", "/home/YOU"):
            self.assertIn(placeholder, out, placeholder)
        self.assertEqual(scan_text(out, []), [])
        self.assertEqual(scrub(out), out)                       # a second pass changes nothing

    def test_a_number_learned_from_a_name_is_caught_bare(self):
        scrub = probe.Scrubber(PROJECT)
        scrub("projects/1234567890/locations/us-central1/reasoningEngines/77")
        self.assertEqual(scrub("numeric-project-id 1234567890, engine 77"), "numeric-project-id NUMBER, engine 77")
        scrub.learn_number("98765432101")
        self.assertEqual(scrub("project 98765432101"), "project NUMBER")

    def test_text_is_scrubbed_before_it_is_cut(self):
        rec = probe.Recorder(False, probe.Scrubber(PROJECT))
        rec.add("1", "us-central1", "refused", "x" * 880 + PROJECT, "y" * 590 + PROJECT + " " + NUMBER)
        rec.add("2", "deploy", "refused", "z", PROJECT + "/" + NUMBER + " " + "w" * 700, keep_end=True)
        for part in rec.parts:
            for fragment in ("lane-for", "2468135"):
                self.assertNotIn(fragment, part.finding + part.evidence)

    def test_service_accounts_and_placeholders_stay(self):
        scrub = probe.Scrubber(probe.PLACEHOLDER)
        text = ("documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com you@example.com "
                "https://documind-mcp-NUMBER.asia-south1.run.app gemini-3.6-flash 2026-10-19T10:15:00Z 1791400167.62")
        self.assertEqual(scrub(text), text)

    def test_your_publish_deny_strings_are_redacted(self):
        with mock.patch.dict(os.environ, {"PUBLISH_DENY": "lane-secret-word"}):
            self.assertNotIn("lane-secret-word", probe.Scrubber(PROJECT)("a lane-secret-word here"))


class Pieces(unittest.TestCase):
    def test_the_project_has_no_default_and_yes_needs_a_real_one(self):
        with contextlib.redirect_stderr(io.StringIO()):
            for argv in ([], ["--project", probe.PLACEHOLDER, "--yes"], ["--project", PROJECT, "--yes", "--dry-run"],
                         ["--project", "Not_A_Project"], ["--project", PROJECT, "--only", "everything"]):
                with self.assertRaises(SystemExit, msg=argv):
                    probe.parse_args(argv)
        args = probe.parse_args(["--project", PROJECT, "--region", "us-central1", "--region", "us-central1"])
        self.assertEqual(args.regions, ["us-central1"])
        self.assertFalse(args.yes)
        self.assertEqual(probe.parse_args(["--project", PROJECT]).regions, ["us-central1", "asia-south1"])

    def test_only_adds_what_a_step_needs(self):
        args = probe.parse_args(["--project", PROJECT, "--only", "access"])
        p = probe.Probe(args, probe.Cloud(PROJECT, dry_run=True, backend_factory=None, say=print), print,
                        probe.Scrubber(PROJECT))
        self.assertEqual(p.selected(), ["preflight", "runtime", "access", "author"])

    def test_the_grant_a_refusal_names(self):
        sa = f"documind-agent-sa@{PROJECT}.iam.gserviceaccount.com"
        hint = probe.grant_hint(f"Permission 'iam.serviceAccounts.getAccessToken' denied for "
                                f"service-{NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com", sa)
        self.assertIn("--role=roles/iam.serviceAccountTokenCreator", hint)
        self.assertIn(f"--member=serviceAccount:service-{NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com", hint)
        self.assertIn("roles/iam.serviceAccountUser", probe.grant_hint("iam.serviceAccounts.actAs denied", sa))
        self.assertEqual(probe.grant_hint("Quota exceeded for reasoning engines", sa), "")

    def test_a_stream_reply_is_read_line_by_line(self):
        facts = {"metadata": {"service_account": "a@b.iam.gserviceaccount.com"}}
        lines = ['data: {"author": "probe_model", "content": {"parts": [{"text": "ok"}]}}', "",
                 "data: " + json.dumps({"content": {"parts": [{"text": "PROBE_FACTS " + json.dumps(facts)}]}}),
                 '{"content": {"parts": [{"text": "PROBE_MODEL_ERROR ClientError: 429"}]}}', "data: [DONE]"]
        got, error, texts = probe.probe_facts(probe.stream_events(lines))
        self.assertEqual(got, facts)
        self.assertEqual(error, "ClientError: 429")
        self.assertEqual(texts, ["ok"])

    def test_the_run_note_names_prerequisites_and_commands(self):
        note = probe.run_note(probe.parse_args(["--project", probe.PLACEHOLDER]))
        for needle in ("aiplatform.googleapis.com", "telemetry.googleapis.com", "iamcredentials.googleapis.com",
                       "make operators", "documind-agent-sa", "gcloud auth application-default login",
                       '"google-adk[a2a]==2.8.0" "google-cloud-aiplatform[agent_engines]"', "pip check",
                       "--dry-run --ignore-installed", "deploy/services/agent/requirements.txt", "--yes",
                       "--cleanup --yes", "--only runtime,access,telemetry", "roles/iam.serviceAccountTokenCreator",
                       probe.PRICING_URL, "--idle-wait 900"):
            self.assertIn(needle, note)
        self.assertEqual(scan_text(note, []), [])

    def test_the_agent_source_compiles_and_is_never_published(self):
        compile(probe.AGENT_SOURCE, "agent.py", "exec")
        self.assertIn("root_agent = ProbeAgent(", probe.AGENT_SOURCE)
        self.assertNotIn("fetch_id_token(", probe.AGENT_SOURCE.split("def _claims")[1].split("def _version")[0])
        publish = (ROOT / "tools" / "publish_learner.py").read_text(encoding="utf-8")
        self.assertIn('PREFIX = "deploy/"', publish)                # tools/ never reaches the learner repository


@unittest.skipUnless(ADK or REQUIRE, "needs google-adk 2.8.0: pip install -r deploy/services/chat/requirements.txt")
class ProbeAgentUnderAdk(unittest.TestCase):
    """The deployed agent's own module, under the pinned ADK, on a scripted model and a fake metadata server."""

    def setUp(self):
        if not ADK:
            self.fail("DOCUMIND_REQUIRE_LIBS=1 but google-adk is not installed")
        from google.adk.models.base_llm import BaseLlm
        from google.adk.models.llm_response import LlmResponse
        from google.genai import types as gt

        self.gt = gt
        self.module = types.ModuleType("documind_probe_agent_under_test")
        sys.modules[self.module.__name__] = self.module
        self.addCleanup(sys.modules.pop, self.module.__name__, None)
        exec(compile(probe.AGENT_SOURCE, "agent.py", "exec"), self.module.__dict__)

        class Script(BaseLlm):
            model: str = "script"
            sent: list = []
            broken: bool = False

            async def generate_content_async(self, llm_request, stream=False):
                self.sent.append(llm_request)
                if self.broken:
                    raise RuntimeError("429 RESOURCE_EXHAUSTED")
                if len(self.sent) == 1:
                    seen = " ".join(p.text or "" for c in llm_request.contents for p in (c.parts or []))
                    marker = re.search(r"pm[0-9a-f]{8}", seen).group(0)
                    yield LlmResponse(content=gt.Content(role="model", parts=[
                        gt.Part(function_call=gt.FunctionCall(name="probe_tool", args={"marker": marker}))]))
                else:
                    yield LlmResponse(content=gt.Content(role="model", parts=[gt.Part(text="ok")]))

        self.script = Script(sent=[])
        self.module.root_agent.sub_agents[0].model = self.script
        self.account = "documind-agent-sa@lane.iam.gserviceaccount.com"
        self.audience = f"https://documind-mcp-{NUMBER}.asia-south1.run.app"
        claims = {"aud": self.audience, "email": self.account, "iss": "https://accounts.google.com", "iat": 1000, "exp": 4600}
        self.token = "eyJhbGciOiJSUzI1NiJ9." + base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=") \
            + ".c2lnbmF0dXJl"
        answers = {"instance/service-accounts/default/email": self.account, "project/numeric-project-id": NUMBER}

        def metadata(path, timeout=3.0):
            if path.startswith("instance/service-accounts/default/identity?audience="):
                return self.token
            return answers[path]

        class Genai:
            def __init__(self, **kwargs):
                self.location, self.models = kwargs.get("location"), self

            def generate_content(self, model, contents):
                if self.location == "global":
                    return types.SimpleNamespace(text="ok")
                raise RuntimeError(f"404 NOT_FOUND: Publisher Model {model} was not found in asia-south1")

        self.module._metadata = metadata
        self.module.Client = Genai
        door = mock.MagicMock()
        door.__enter__.return_value.status = 200
        for patch in (mock.patch("google.oauth2.id_token.fetch_id_token", return_value=self.token),
                      mock.patch("urllib.request.urlopen", return_value=door),
                      mock.patch.dict(os.environ, {"GOOGLE_CLOUD_LOCATION": "asia-south1"})):
            patch.start()
            self.addCleanup(patch.stop)

    def ask(self, message):
        from google.adk.runners import InMemoryRunner

        async def go():
            runner = InMemoryRunner(agent=self.module.root_agent, app_name="documind_probe")
            session = await runner.session_service.create_session(app_name="documind_probe", user_id="probe-operator")
            return [e async for e in runner.run_async(user_id="probe-operator", session_id=session.id,
                                                      new_message=self.gt.Content(role="user", parts=[self.gt.Part(text=message)]))]
        return [e.model_dump(mode="json", exclude_none=True) for e in asyncio.run(go())]

    def test_one_tool_call_then_the_facts(self):
        events = self.ask("Probe pm1a2b3c4d: call probe_tool with the marker pm1a2b3c4d, then report the runtime facts.")
        facts, model_error, texts = probe.probe_facts(events)
        self.assertIsNone(model_error)
        self.assertIn("ok", texts)
        calls = [p["function_call"] for e in events for p in e.get("content", {}).get("parts", []) if "function_call" in p]
        self.assertEqual([(c["name"], c["args"]) for c in calls], [("probe_tool", {"marker": "pm1a2b3c4d"})])
        self.assertEqual(facts["metadata"]["service_account"], self.account)
        self.assertEqual(facts["audience"], self.audience)
        for key in ("id_token_metadata", "id_token_fetch"):
            self.assertEqual(facts[key], {"minted": True, "aud": self.audience, "email": self.account,
                                          "iss": "https://accounts.google.com", "lifetime_s": 3600})
        self.assertEqual(facts["mcp_door"], {"status": 200})
        self.assertEqual(facts["env"]["GOOGLE_CLOUD_LOCATION"], "asia-south1")
        self.assertTrue(facts["gemini"]["global"]["answered"])
        self.assertFalse(facts["gemini"]["environment"]["answered"])
        self.assertEqual(facts["versions"]["google-adk"], importlib.metadata.version("google-adk"))
        self.assertNotIn(self.token.split(".")[1], json.dumps(events))     # the token itself never leaves the agent

    def test_no_model_means_the_facts_alone(self):
        facts, _, _ = probe.probe_facts(self.ask(f"Probe pm1a2b3c4d {probe.NO_MODEL}: the runtime facts only."))
        self.assertEqual(self.script.sent, [])
        self.assertNotIn("gemini", facts)
        self.assertTrue(facts["id_token_fetch"]["minted"])

    def test_a_failed_model_turn_still_sends_the_facts(self):
        self.script.broken = True
        facts, model_error, _ = probe.probe_facts(self.ask("Probe pm1a2b3c4d: call probe_tool."))
        self.assertIn("429 RESOURCE_EXHAUSTED", model_error)
        self.assertEqual(facts["metadata"]["service_account"], self.account)


class _Answer(types.SimpleNamespace):
    """An SDK object as ADK reads it: attributes, and model_dump() like vertexai's pydantic types."""

    def model_dump(self, **kwargs):
        return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in vars(self).items()}


async def _aiter(items):
    for item in items:
        yield item


class FakeVertexai:
    """The vertexai module, exactly as far as google-adk 2.8.0's deploy, VertexAiSessionService and
    VertexAiMemoryBankService - and the probe's LiveBackend - call it. Nothing leaves the process."""

    def __init__(self):
        import datetime
        self.now = datetime.datetime(2026, 10, 19, 10, 0, tzinfo=datetime.timezone.utc)
        self.calls, self.sessions, self.memories, self.update = [], {}, [], {}

    def module(self):
        fake, mod = self, types.ModuleType("vertexai")

        class Sessions:
            def __init__(self):
                self.events = types.SimpleNamespace(append=self.append, list=self.list_events)

            def answer(self, name):
                return _Answer(name=name, user_id=fake.sessions[name.rsplit("/", 1)[-1]], update_time=fake.now,
                               session_state=None, expire_time=fake.now)

            async def create(self, name, user_id, config):
                fake.calls.append(("sessions.create", name, user_id, dict(config)))
                fake.sessions["7001"] = user_id
                return _Answer(response=self.answer(f"{name}/sessions/7001"))

            async def get(self, name):
                fake.calls.append(("sessions.get", name))
                return self.answer(name)

            async def list_events(self, name, **kwargs):
                return _aiter([])

            async def append(self, name, author, invocation_id, timestamp, config):
                fake.calls.append(("sessions.events.append", name, author))

            async def list(self, name, config):
                fake.calls.append(("sessions.list", name, dict(config)))
                return _aiter([self.answer(f"{name}/sessions/{sid}") for sid in fake.sessions])

            async def delete(self, name):
                fake.calls.append(("sessions.delete", name))
                fake.sessions.pop(name.rsplit("/", 1)[-1], None)

        class Memories:
            async def create(self, name, fact, scope, config):
                fake.calls.append(("memories.create", name, fact, scope))
                fake.memories.append(fact)

            async def retrieve(self, name, scope, similarity_search_params):
                fake.calls.append(("memories.retrieve", name, scope))
                return _aiter([_Answer(memory=_Answer(fact=f, update_time=fake.now)) for f in fake.memories])

        class AsyncClient:
            def __init__(self):
                self.agent_engines = types.SimpleNamespace(sessions=Sessions(), memories=Memories())

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
                               "requirements": Path("agents/documind_probe/requirements.txt").read_text()}

            def delete(self, name, force=False):
                fake.calls.append(("delete", name, force))

        class Client:
            def __init__(self, project=None, location=None, credentials=None, http_options=None, api_key=None):
                fake.calls.append(("Client", project, location, credentials))
                self.agent_engines, self.aio = Engines(), AsyncClient()

        mod.Client = Client
        return mod


class FakeRest:
    """google.auth's AuthorizedSession, answering each REST call the probe makes from a table."""

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
            facts = {"metadata": {"service_account": "documind-agent-sa@x.iam.gserviceaccount.com"}}
            return self.Response(200, lines=['data: {"content": {"parts": [{"text": "ok"}]}}', "",
                                              "data: " + json.dumps({"content": {"parts": [
                                                  {"text": "PROBE_FACTS " + json.dumps(facts)}]}})])
        if url.endswith("reasoningEngines/123:getIamPolicy"):
            return self.Response(404, {"error": {"code": 404, "message": "Method not found.", "status": "NOT_FOUND"}})
        if url.endswith(":getIamPolicy"):
            return self.Response(200, {"bindings": [], "etag": "x"})
        if url.endswith(":testIamPermissions"):
            return self.Response(200, {"permissions": body["permissions"][:1]})
        if "cloudtrace" in url:
            return self.Response(200, {"traces": [{"traceId": "t1", "spans": [{"name": "invocation", "labels": {}}]}]})
        if url.endswith("/reasoningEngines"):
            return self.Response(200, {"reasoningEngines": [{"name": "n", "displayName": "documind-probe-x"}]})
        return self.Response(200, {"name": url.split("/v1/", 1)[-1]})


@unittest.skipUnless(ADK or REQUIRE, "needs google-adk 2.8.0: pip install -r deploy/services/chat/requirements.txt")
class LiveBackendOffline(unittest.TestCase):
    """The one class only a live run uses, driven through google-adk's own deploy, sessions and Memory Bank code on a
    fake vertexai, and through google.auth on a fake AuthorizedSession. What it would send is what is checked."""

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
        self.live = probe.LiveBackend(PROJECT)
        self.name = f"projects/{NUMBER}/locations/asia-south1/reasoningEngines/123"

    def test_adks_own_deploy_sends_the_probe_config(self):
        if importlib.metadata.version("google-adk") != "2.8.0":
            self.skipTest("ADK's deploy is read at the kit's pin, 2.8.0")
        args = probe.parse_args(["--project", PROJECT])
        with tempfile.TemporaryDirectory() as tmp:
            staged = probe.stage_agent(Path(tmp), *probe.deploy_inputs(args, PROJECT))
            log = self.live.deploy(self.name, *staged, "documind-probe-20261019-0930-runtime")
        sent = self.vertex.update
        config = sent["config"]
        self.assertEqual(sent["name"], self.name)
        self.assertIn(("Client", PROJECT, "asia-south1", None), self.vertex.calls)
        self.assertFalse([c for c in self.vertex.calls if c[0] in ("create", "delete")])   # the id is given: no create
        self.assertEqual((config["service_account"], config["min_instances"], config["max_instances"]),
                         (f"documind-agent-sa@{PROJECT}.iam.gserviceaccount.com", 0, 1))
        self.assertEqual(config["display_name"], "documind-probe-20261019-0930-runtime")
        self.assertEqual(config["env_vars"], {"PROBE_MODEL": "gemini-3.6-flash", "PROBE_MCP_REGION": "asia-south1",
                                              "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
                                              "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": "false"})
        self.assertEqual(config["agent_framework"], "google-adk")
        self.assertEqual(config["source_packages"], ["agents/documind_probe", "Dockerfile"])
        self.assertIn("async_stream_query", [m["name"] for m in config["class_methods"]])
        self.assertIn("ENV GOOGLE_CLOUD_LOCATION=asia-south1", sent["dockerfile"])       # row 6, from ADK's source
        self.assertIn("--otel_to_cloud", sent["dockerfile"])
        self.assertIn("google-cloud-aiplatform[adk,agent_engines]", sent["requirements"])  # row 11's appended line
        self.assertIn("Deployed to Agent Platform", log)

    def test_instances_sessions_and_memory_go_through_adk(self):
        name = self.live.create_instance("asia-south1", "documind-probe-x-asia-south1")
        self.assertEqual(name, self.name)
        self.assertIn(("create", {"display_name": "documind-probe-x-asia-south1"}), self.vertex.calls)
        sid = self.live.create_session(name, "acme:probe-a", "900s")
        self.assertIn(("sessions.create", "reasoningEngines/123", "acme:probe-a", {"ttl": "900s"}), self.vertex.calls)
        self.live.append_event(name, sid, "probe event pm1")
        with self.assertRaisesRegex(ValueError, "does not belong to user zeta:probe-b"):
            self.live.get_session(name, sid, "zeta:probe-b")
        self.assertEqual(self.live.get_session(name, sid, "acme:probe-a"), {"user_id": "acme:probe-a", "id": sid, "events": 0})
        raw = self.live.raw_get_session(name, sid)
        self.assertEqual((raw["user_id"], raw["expire_time"]), ("acme:probe-a", "2026-10-19T10:00:00+00:00"))
        self.assertEqual(self.live.list_sessions(name), [{"user_id": "acme:probe-a", "id": sid}])
        self.assertIn(("sessions.list", "reasoningEngines/123", {}), self.vertex.calls)          # no user filter sent
        self.live.add_memory(name, "acme:probe-a", "The probe's marker is pm1.")
        self.assertEqual(self.live.search_memory(name, "acme:probe-a", "marker?"), ["The probe's marker is pm1."])
        self.assertIn(("memories.create", "reasoningEngines/123", "The probe's marker is pm1.",
                       {"app_name": "documind_probe", "user_id": "acme:probe-a"}), self.vertex.calls)
        self.live.delete_session(name, sid, "acme:probe-a")
        self.live.delete_instance(name)
        self.assertEqual(self.vertex.sessions, {})
        self.assertIn(("delete", name, True), self.vertex.calls)

    def test_the_rest_calls_and_their_refusals(self):
        email = f"documind-agent-sa@{PROJECT}.iam.gserviceaccount.com"
        with mock.patch("subprocess.run", return_value=types.SimpleNamespace(stdout="No broken requirements found.\n",
                                                                             stderr="")):
            versions = self.live.versions("asia-south1")
        self.assertTrue(versions["namespaces"]["agent_engines"])
        self.assertEqual(versions["pip_check"], "No broken requirements found.")
        self.assertEqual(self.live.get_instance(self.name)["name"], self.name)
        self.assertEqual(self.live.list_instances("asia-south1"), [{"name": "n", "displayName": "documind-probe-x"}])
        self.assertEqual(self.live.sa_policy(email), {"bindings": [], "etag": "x"})
        self.assertEqual(self.live.sa_permissions(email, probe.ACT_AS), ["iam.serviceAccounts.actAs"])
        with self.assertRaises(probe.Refused) as refused:
            self.live.engine_policy(self.name)
        self.assertEqual(refused.exception.status, 404)
        self.assertEqual(self.live.trace_spans("a", "b"), [{"trace": "t1", "name": "invocation", "labels": {}}])
        reply = self.live.query(self.name, "Probe pm1 [no-model]", "probe-operator")
        self.assertEqual(probe.probe_facts(reply["events"])[0]["metadata"]["service_account"],
                         "documind-agent-sa@x.iam.gserviceaccount.com")
        self.assertIsNotNone(reply["first_event_s"])
        urls = [(m, u.split("googleapis.com", 1)[-1]) for m, u, *_ in self.rest.sent]
        self.assertIn(("GET", f"/v1/{self.name}"), urls)
        self.assertIn(("POST", f"/v1/{self.name}:streamQuery"), urls)
        self.assertIn(("POST", f"/v1/projects/{PROJECT}/serviceAccounts/{email}:getIamPolicy"), urls)
        method, url, body, params, _ = next(s for s in self.rest.sent if s[1].endswith(":streamQuery"))
        self.assertEqual((body, params), ({"class_method": "async_stream_query",
                                           "input": {"user_id": "probe-operator", "message": "Probe pm1 [no-model]"}},
                                          {"alt": "sse"}))
        self.assertTrue(url.startswith("https://asia-south1-aiplatform.googleapis.com/v1/projects/"))

    def test_a_query_as_another_account_mints_first_and_says_when_it_cannot(self):
        minted = mock.MagicMock()
        with mock.patch("google.auth.impersonated_credentials.Credentials", return_value=minted) as make:
            self.live.query(self.name, "Probe pm1 [no-model]", "probe-ui", as_sa="documind-ui-sa@x.iam.gserviceaccount.com")
        self.assertEqual(make.call_args.kwargs["target_principal"], "documind-ui-sa@x.iam.gserviceaccount.com")
        minted.refresh.assert_called_once()
        self.assertIs(self.rest.sent[-1][4], minted)            # the query went out as that account
        minted.refresh.side_effect = RuntimeError("Permission 'iam.serviceAccounts.getAccessToken' denied")
        with mock.patch("google.auth.impersonated_credentials.Credentials", return_value=minted), \
                self.assertRaises(probe.NotTested) as stopped:
            self.live.query(self.name, "Probe pm1", "probe-out", as_sa="documind-outsider-sa@x.iam.gserviceaccount.com")
        self.assertIn("make operators", str(stopped.exception))


if __name__ == "__main__":
    unittest.main()
