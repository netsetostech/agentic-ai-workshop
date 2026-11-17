"""Offline checks for the A2A peer's cap and make agent-drill (workshop lesson 10.7).

    python -m unittest commands/tests/test_agent_drill.py -v          # from deploy/

No network, no credential, no Google library: the standard library and bash. The first class reads the kit: agent.py
sets ADK_MAX_LLM_CALLS to 12 unless the environment already holds a value, and publishes it on /health as
max_llm_calls; commands/lesson-8.4.sh deploys the same 12, and so does commands/managed_peer.py where it exists (lesson
10.9's managed peer); smoke_agent.py keeps its five checks and the helpers the drill borrows; the target, its .PHONY
entry and mk/README.md row; the Makefile's 888 lines; the UNOWNED.md rows.

The second runs commands/agent-drill.sh against a stub gcloud that keeps documind-agent's environment and traffic in a
file and records every call, and a stand-in peer on 127.0.0.1 whose /health publishes the cap in that file and whose
message/send needs two model calls, a retrieve and the answer. It answers as google-adk 2.8.0 and a2a-sdk 1.1.2 do,
which agent.py served offline on 13 October 2026 with Gemini scripted: over the cap the task is `failed` with "Max
number of llm calls limit of `1` exceeded" as its status message, under it `completed` with the answer as an artifact.
PATH holds the stubs first, so every gcloud the drill runs is the stub; the drill's Python mints nothing (it is handed
the token the script minted through the stub), and no Google credential is in its environment.

Covered: the drill end to end (the cap set to 1, the task failed, the 12 put back, the task completed); a lane where
the variable was unset (removed again, not set to 12); a peer whose /health names no cap and traffic pinned to an old
revision (both stop before any change); a revision that does not take the traffic, a peer that ignores the cap and a
task that fails for another reason (each fails the drill, and the trap puts the variable back).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
PROJECT, NUMBER, REGION = "documind-course-demo", "123456789012", "asia-south1"
AGENT_URL = f"https://documind-agent-{NUMBER}.{REGION}.run.app"
UI_SA = f"documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"


def read(*parts: str) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


AGENT = read("services", "agent", "agent.py")
DEFAULT_CAP = int(re.search(r'os\.environ\.setdefault\("ADK_MAX_LLM_CALLS", "(\d+)"\)', AGENT).group(1))
QUESTION = re.search(r'^DEFAULT_QUESTION = "([^"]+)"$', read("smoke", "smoke_agent.py"), re.M).group(1)
ANSWER = "Gratuity becomes payable after five years of continuous service. Source: payment_of_gratuity_act_1972.pdf, page 2."
LIMIT = "Max number of llm calls limit of `{}` exceeded"          # google-adk 2.8.0, agents/invocation_context.py


class TheCapInTheKit(unittest.TestCase):
    """What needs no bash: the cap where the kit sets it and publishes it, and the drill's entries."""

    def test_agent_py_sets_twelve_unless_the_environment_says_otherwise_and_publishes_it(self):
        self.assertEqual(DEFAULT_CAP, 12)
        self.assertIn('MAX_LLM_CALLS = int(os.environ.setdefault("ADK_MAX_LLM_CALLS", "12"))', AGENT)
        model, cap, built = (AGENT.index('MODEL = os.environ.get("AGENT_MODEL"'), AGENT.index("MAX_LLM_CALLS = int("),
                             AGENT.index("agent = build_agent()"))
        self.assertLess(model, cap)
        self.assertLess(cap, built)                    # set before to_a2a builds the app; RunConfig reads it per task
        health = AGENT.split("async def health(", 1)[1].split("\n\n", 1)[0]
        self.assertIn('"max_llm_calls": MAX_LLM_CALLS', health)
        self.assertIn('"kit_import": False', health)

    def test_the_deploy_sets_the_same_cap(self):
        deploy = read("commands", "lesson-8.4.sh").split("# ---- DEPLOY ----")[1].split("# ---- SMOKE ----")[0]
        env = dict(kv.split("=", 1) for kv in re.search(r'--set-env-vars="\^\|\^([^"]+)"', deploy).group(1).split("|"))
        self.assertEqual(env["ADK_MAX_LLM_CALLS"], str(DEFAULT_CAP))
        self.assertEqual(env["AGENT_MODEL"], "gemini-3.6-flash")     # lesson 10.6 reads the model from the same line

    def test_the_managed_peer_deploys_the_same_cap(self):
        managed = KIT / "commands" / "managed_peer.py"
        if not managed.exists():
            self.skipTest("commands/managed_peer.py (lesson 10.9) is not in this kit yet")
        self.assertRegex(managed.read_text(encoding="utf-8"), rf"(?m)^PEER_MAX_LLM_CALLS = {DEFAULT_CAP}\b")

    def test_the_smoke_keeps_five_checks_and_the_helpers_the_drill_borrows(self):
        smoke = read("smoke", "smoke_agent.py")
        self.assertIn("five checks", smoke.splitlines()[1])   # tools/check_authz.py and lesson 10.6's gate count them
        for helper in ("def http(path: str, token", "def send(token", "def task_answer_matches(",
                       "def expected_answer_pattern("):
            self.assertIn(helper, smoke)
        drill = read("commands", "agent-drill.sh")
        self.assertIn("import smoke_agent as s", drill)
        self.assertNotIn("smoke/smoke_agent.py", read("mk", "agents.mk").split("\nagent-drill:", 1)[1])

    def test_the_target_its_phony_entry_and_its_readme_row(self):
        mk, agents, readme = read("Makefile"), read("mk", "agents.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")]
        self.assertIn("agent-drill", phony.split())     # later kits append after it
        recipe = agents.split("\nagent-drill: guard-project\n", 1)[1].split("\n\n", 1)[0]
        self.assertEqual(recipe.strip(), "@PROJECT=$(PROJECT) REGION=$(REGION) PY=$(PY) bash commands/agent-drill.sh")
        row = next(line for line in readme.splitlines() if line.startswith("| `agents.mk` |"))
        self.assertIn("`agent-drill`", row)
        self.assertIn("`agent-drill.sh`", readme)

    def test_the_new_files_have_their_unowned_rows(self):
        # An UNOWNED.md row until lesson 10.7's page quotes the file; from then on INDEX.md names the lesson.
        unowned = read("UNOWNED.md")
        for f in ("commands/agent-drill.sh", "commands/tests/test_agent_drill.py"):
            row = next((l for l in read("INDEX.md").splitlines() if l.startswith(f"| `{f}` |")), "")   # a page quotes it
            self.assertTrue(f"| `{f}` | **10.7**" in unowned or row.split(" | ")[2:3] not in ([], ["-"]), f)
            self.assertTrue((KIT / f).exists(), f)


# One script plays gcloud; it answers from service.json and records every call in calls/.
STUB = r'''
import json, os, sys, time

home, args = os.environ["DRILL_STUB_HOME"], sys.argv[1:]
with open(os.path.join(home, "calls", "%d-%d.json" % (time.time_ns(), os.getpid())), "w", encoding="utf-8") as log:
    json.dump(args, log)
path = os.path.join(home, "service.json")
with open(path, encoding="utf-8") as f:
    svc = json.load(f)


def flag(name):
    return next((a.split("=", 1)[1] for a in args if a.startswith(name + "=")), None)


# `gcloud run services VERB [flags] documind-agent --project=... --region=...`, as the drill's svc() spells it
here = ([a for a in args[3:] if not a.startswith("--")] == ["documind-agent"]
        and flag("--project") == svc["project"] and flag("--region") == svc["region"])
if args[:3] == ["projects", "describe", svc["project"]] and flag("--format") == "value(projectNumber)":
    print(svc["number"])
elif args[:2] == ["auth", "print-identity-token"]:
    print("stub-id-token")
elif args[:3] == ["run", "services", "describe"] and here and flag("--format") == "json":
    print(json.dumps({"spec": {"template": {"spec": {"containers": [
        {"env": [{"name": k, "value": v} for k, v in svc["env"].items()]}]}}}, "status": {"traffic": svc["traffic"]}}))
elif args[:3] == ["run", "services", "update"] and here and "--quiet" in args:
    if flag("--update-env-vars"):
        key, value = flag("--update-env-vars").split("=", 1)
        svc["env"][key] = value
    elif flag("--remove-env-vars"):
        svc["env"].pop(flag("--remove-env-vars"), None)
    else:
        sys.exit(98)
    if svc.get("pin_after_update"):             # the new revision does not take the traffic
        svc["traffic"] = [{"revisionName": "documind-agent-00007-abc", "percent": 100}]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(svc, f)
    sys.stderr.write("Deploying...\n")
else:
    sys.stderr.write("stub: unexpected call: gcloud " + " ".join(args) + "\n")
    sys.exit(99)
'''


class Peer(BaseHTTPRequestHandler):
    """documind-agent, stood in: /health and message/send, the cap read from the stub's service.json."""

    def log_message(self, *a):
        pass

    def reply(self, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def service(self) -> dict:
        return json.loads((self.server.home / "service.json").read_text(encoding="utf-8"))

    def do_GET(self):
        svc = self.service()
        self.server.seen.append(("GET", self.path, self.headers.get("Authorization"), None))
        body = {"status": "ok", "mcp_url": f"https://documind-mcp-{NUMBER}.{REGION}.run.app", "self_url": AGENT_URL,
                "model": "gemini-3.6-flash", "kit_import": False}
        if svc["publishes_cap"]:
            body["max_llm_calls"] = int(svc["env"].get("ADK_MAX_LLM_CALLS", DEFAULT_CAP))
        self.reply(body)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        svc = self.service()
        text = req["params"]["message"]["parts"][0]["text"]
        self.server.seen.append(("POST", req["method"], self.headers.get("Authorization"), text))
        cap = int(svc["env"].get("ADK_MAX_LLM_CALLS", DEFAULT_CAP)) if svc["honours_cap"] else 500
        task = {"kind": "task", "id": "task-1", "contextId": "context-1", "metadata": {},
                "history": [req["params"]["message"]]}
        said = lambda words: {"kind": "message", "messageId": "m-1", "role": "agent",   # noqa: E731
                              "parts": [{"kind": "text", "text": words}]}
        if svc.get("mcp_down"):                     # a failure that is not the cap
            task["status"] = {"state": "failed", "message": said("Failed to create MCP session: connection refused")}
        elif cap < 2:                               # the retrieve call fits; the answer's call is over the cap
            task["status"] = {"state": "failed", "message": said(LIMIT.format(cap))}
        else:
            task["status"] = {"state": "completed"}
            task["artifacts"] = [{"artifactId": "a-1", "parts": [{"kind": "text", "text": ANSWER}]}]
        self.reply({"jsonrpc": "2.0", "id": req["id"], "result": task})


class TheDrill(unittest.TestCase):
    """commands/agent-drill.sh against the stub gcloud and the stand-in peer."""

    @classmethod
    def setUpClass(cls):
        cls.bash = shutil.which("bash")
        if not cls.bash:
            raise unittest.SkipTest("bash is not on PATH")

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="agent_drill_test_"))
        self.addCleanup(shutil.rmtree, self.home, True)
        (self.home / "bin").mkdir()
        (self.home / "calls").mkdir()
        (self.home / "stub.py").write_text(STUB, encoding="utf-8")
        self.peer = ThreadingHTTPServer(("127.0.0.1", 0), Peer)
        self.peer.home, self.peer.seen = self.home, []
        threading.Thread(target=self.peer.serve_forever, daemon=True).start()
        self.addCleanup(self.peer.server_close)
        self.addCleanup(self.peer.shutdown)
        python = Path(sys.executable).as_posix()
        self.script("gcloud", f'exec "{python}" "{(self.home / "stub.py").as_posix()}" "$@"')
        # PY, as the drill runs it, reaches the stand-in instead of the run.app url the drill exports
        self.script("py", f'DOCUMIND_AGENT_URL=http://127.0.0.1:{self.peer.server_address[1]}\n'
                          f'export DOCUMIND_AGENT_URL\nexec "{python}" "$@"')
        self.service = {"project": PROJECT, "region": REGION, "number": NUMBER, "publishes_cap": True,
                        "honours_cap": True, "env": {"GOOGLE_CLOUD_LOCATION": "global", "ADK_MAX_LLM_CALLS": "12"},
                        "traffic": [{"latestRevision": True, "percent": 100, "revisionName": "documind-agent-00006-xyz"}]}

    def script(self, name: str, body: str) -> None:
        path = self.home / "bin" / name
        with open(path, "w", encoding="utf-8", newline="\n") as f:     # text mode would write CRLF on Windows
            f.write(f"#!/bin/sh\n{body}\n")
        path.chmod(0o755)

    def drill(self) -> subprocess.CompletedProcess:
        (self.home / "service.json").write_text(json.dumps(self.service), encoding="utf-8")
        env = {"PATH": str(self.home / "bin") + os.pathsep + os.environ.get("PATH", ""), "DRILL_STUB_HOME": str(self.home),
               "PROJECT": PROJECT, "REGION": REGION, "PY": str(self.home / "bin" / "py"), "PYTHONIOENCODING": "utf-8",
               "HOME": str(self.home), "USERPROFILE": str(self.home), "APPDATA": str(self.home),
               "CLOUDSDK_CONFIG": str(self.home / "gcloud")}
        for key in ("SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR", "TEMP", "TMP"):    # what Windows itself needs
            if key in os.environ:
                env[key] = os.environ[key]
        return subprocess.run([self.bash, "commands/agent-drill.sh"], cwd=str(KIT), env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=180)

    def calls(self) -> list:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.home / "calls").glob("*.json"))]

    def updates(self) -> list:
        return [next(a for a in c if a.startswith(("--update-env-vars=", "--remove-env-vars=")))
                for c in self.calls() if c[:3] == ["run", "services", "update"]]

    def env_now(self) -> dict:
        return json.loads((self.home / "service.json").read_text(encoding="utf-8"))["env"]

    def tasks(self) -> list:
        return [s for s in self.peer.seen if s[0] == "POST"]

    def test_the_task_fails_at_one_and_completes_with_the_twelve_put_back(self):
        r = self.drill()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = r.stdout
        for line in (">> documind-agent: /health names max_llm_calls 12", ">> documind-agent: ADK_MAX_LLM_CALLS=1",
                     ">> /health: max_llm_calls 1", "  [PASS] task failed  status=200 state=failed  "
                     "'Max number of llm calls limit of `1` exceeded'", ">> restored ADK_MAX_LLM_CALLS=12",
                     ">> /health: max_llm_calls 12; the same task, with the cap put back",
                     f"  [PASS] task completed  status=200 state=completed  {ANSWER!r}"):
            self.assertIn(line, out)
        self.assertLess(out.index("[PASS] task failed"), out.index(">> restored"))
        self.assertEqual(self.updates(), ["--update-env-vars=ADK_MAX_LLM_CALLS=1", "--update-env-vars=ADK_MAX_LLM_CALLS=12"])
        self.assertEqual(self.env_now(), self.service["env"])
        # the token make smoke-agent mints, once: as documind-ui-sa, for the peer's run.app url
        mints = [c for c in self.calls() if c[:2] == ["auth", "print-identity-token"]]
        self.assertEqual(len(mints), 1)
        self.assertIn(f"--impersonate-service-account={UI_SA}", mints[0])
        self.assertIn(f"--audiences={AGENT_URL}", mints[0])
        self.assertEqual([(m, auth, text) for _, m, auth, text in self.tasks()],
                         [("message/send", "Bearer stub-id-token", QUESTION)] * 2)
        self.assertTrue(all(auth == "Bearer stub-id-token" for _, _, auth, _ in self.peer.seen))

    def test_a_variable_that_was_unset_is_removed_again(self):
        del self.service["env"]["ADK_MAX_LLM_CALLS"]
        r = self.drill()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(">> documind-agent: /health names max_llm_calls 12", r.stdout)       # agent.py's default
        self.assertIn(">> restored: ADK_MAX_LLM_CALLS unset, agent.py's default applies", r.stdout)
        self.assertEqual(self.updates(), ["--update-env-vars=ADK_MAX_LLM_CALLS=1", "--remove-env-vars=ADK_MAX_LLM_CALLS"])
        self.assertEqual(self.env_now(), {"GOOGLE_CLOUD_LOCATION": "global"})

    def test_a_peer_whose_health_names_no_cap_is_left_alone(self):
        self.service["publishes_cap"] = False                      # an image from before 13 October 2026
        r = self.drill()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ERROR: documind-agent's /health names no max_llm_calls: its image is from before the peer's cap; "
                      "nothing changed.", r.stderr)
        self.assertIn("make build deploy-services SERVICES=agent SCRIPTS=commands/lesson-8.4.sh", r.stderr)
        self.assertEqual((self.updates(), self.tasks()), ([], []))

    def test_traffic_pinned_to_an_old_revision_stops_before_any_change(self):
        self.service["traffic"] = [{"revisionName": "documind-agent-00005-old", "percent": 100}]
        r = self.drill()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("traffic is pinned away from its latest revision", r.stderr)
        self.assertIn("gcloud run services update-traffic documind-agent --to-latest --region=asia-south1", r.stderr)
        self.assertEqual((self.updates(), self.tasks()), ([], []))

    def test_a_revision_that_does_not_take_the_traffic_is_put_back(self):
        self.service["pin_after_update"] = True
        r = self.drill()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ERROR: the new revision does not take all the traffic.", r.stderr)
        self.assertEqual(self.updates(), ["--update-env-vars=ADK_MAX_LLM_CALLS=1", "--update-env-vars=ADK_MAX_LLM_CALLS=12"])
        self.assertEqual((self.env_now(), self.tasks()), (self.service["env"], []))

    def test_a_peer_that_ignores_the_cap_fails_the_drill_and_the_trap_puts_it_back(self):
        self.service["honours_cap"] = False
        r = self.drill()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("  [FAIL] task failed  status=200 state=completed", r.stdout)
        self.assertIn("  (it completed under a cap of 1: a task that asks for no tool needs one model call", r.stdout)
        self.assertIn(">> restored ADK_MAX_LLM_CALLS=12", r.stdout)
        self.assertNotIn("task completed", r.stdout)
        self.assertEqual(self.env_now(), self.service["env"])
        self.assertEqual(len(self.tasks()), 1)

    def test_a_task_that_fails_for_another_reason_is_not_the_cap(self):
        self.service["mcp_down"] = True
        r = self.drill()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("  [FAIL] task failed  status=200 state=failed  'Failed to create MCP session: connection refused'",
                      r.stdout)
        self.assertIn(">> restored ADK_MAX_LLM_CALLS=12", r.stdout)
        self.assertEqual(self.env_now(), self.service["env"])


if __name__ == "__main__":
    unittest.main()
