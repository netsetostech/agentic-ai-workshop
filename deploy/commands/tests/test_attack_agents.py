"""Offline checks for lesson 10.8's agents' doors run from make (workshop lesson 10.8): make attack-agents
(commands/attack-agents.sh), make mcp-local, and the line the Chat page shows when documind-chat scrubbed an answer.

    python -m unittest commands/tests/test_attack_agents.py -v          # from deploy/

TheTargets reads the kit: both targets appended to mk/agents.mk, in .PHONY and in mk/README.md; the Makefile's 888
lines; attack-agents's guard and the variables it hands the script; the script's mint, the one make attack-eval makes;
mk/evaluation.mk without them; both CI lines and the UNOWNED.md row.

TheScript runs commands/attack-agents.sh in bash against a stub gcloud that records every call and answers with a fixed
project number and token, and evals/tests/test_attacks.py's stand-in documind-chat and peer on 127.0.0.1 (CHAT= and
DOCUMIND_PEER_URL point the runner there). PATH holds the stub first and no directory with any other gcloud, so nothing
reaches Google. Covered: the default run (the chat and Desk rows, one token minted as documind-ui-sa for
documind-chat's canonical URL, exit 0, no token in the report); DOCUMIND_ID_TOKEN used instead of a mint; the peer
added; the peer alone (no gcloud call, no PROJECT, no token sent); an api surface refused; no project number; and a
reply with another tenant's text failing the run with the runner's exit status.

TheLocalServerRecipe reads make mcp-local's two commands: the seed in the kit's root, then the server in services/mcp on
127.0.0.1, both on one absolute Chroma directory, the one make chat-local names, which a probe started where each
command starts resolves to the same place.

TheLocalServer needs fastmcp and uvicorn, the kit's MCP server's pins (CI's agent-pins steps install them and set
DOCUMIND_REQUIRE_LIBS=1). It runs the recipe's server command as written, on a free port: /health says local, and its
tools listed over the MCP wire as the peer's client lists them, with no token, are the four services/agent/tool_pins.json
pins, unchanged, so a peer with TOOL_PINS=on keeps them all. Then, in process, with the store held in memory as the seed
writes it (shared/local_corpus.py's chunks for acme), the tools answer with no token: acme's question with acme's
citations, and atk-17's GLOBEX ask naming globex with nothing - the local profile takes a named tenant as given, and the
store holds acme alone.

TheChatPage runs services/frontend/chat.py's _scrubbed_line() without importing Streamlit: empty for a reply with no
`scrubbed` (AGENT_SCRUB off), with 0, or with something that is not a count; one line naming the count otherwise. And
chat_page() shows it as a caption under the brain's caption, in the agent brains' branch only.
"""
from __future__ import annotations

import ast
import asyncio
import importlib.util
import json
import logging
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
import urllib.request
from collections import Counter
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[2]
ROOT = KIT.parent
PROJECT, NUMBER, REGION = "documind-course-demo", "123456789012", "asia-south1"
CANONICAL = f"https://documind-chat-{NUMBER}.{REGION}.run.app"
UI_SA = f"documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"
TOKEN = "stub-token-for-documind-chat"
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
CI_LINE = "DOCUMIND_REQUIRE_LIBS=1 /tmp/agent-venv/bin/python -m unittest commands/tests/test_attack_agents.py -v"
GCLOUDS = ("gcloud", "gcloud.cmd", "gcloud.CMD", "gcloud.ps1", "gcloud.exe")


def read(*parts: str) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def _has(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


HAS_SERVER = _has("fastmcp") and _has("uvicorn") and _has("requests")


def recipe(text: str, target: str) -> tuple[str, list[str]]:
    """A rule's prerequisites, and its commands as the shell receives them: one per recipe line, a backslash-newline
    joined."""
    m = re.search(rf"^{re.escape(target)}:(.*)\n", text, re.M)
    assert m, f"no rule for {target}"
    commands, line = [], ""
    for raw in text[m.end():].split("\n"):
        if not raw.startswith("\t"):
            break
        line += raw[1:]
        if line.endswith("\\"):
            line = line[:-1]
            continue
        commands.append(line)
        line = ""
    return m.group(1).strip(), commands


def start(command: str, port: str = "8000") -> tuple[Path, dict, list[str]]:
    """Where a recipe command starts, the variables it sets and the program it runs: each `cd DIR &&` moves it, the
    NAME=value words before the program are its environment. $(CURDIR), $(PY) and the port are expanded as make would."""
    *moves, run = [part.strip() for part in command.split("&&")]
    cwd = KIT
    for move in moves:
        word, where = shlex.split(move)
        assert word == "cd", move
        cwd = cwd / where
    run = (run.replace("$(or $(PORT),8000)", port).replace("$(CURDIR)", KIT.as_posix())
           .replace("$(PY)", Path(sys.executable).as_posix()))
    words = shlex.split(run)
    assert not any("$(" in w for w in words), f"a make variable this test does not expand: {run}"
    env = {}
    while words and re.fullmatch(r"[A-Z_][A-Z0-9_]*=.*", words[0]):
        name, value = words.pop(0).split("=", 1)
        env[name] = value
    return cwd, env, words


def clean_env(home: Path) -> dict:
    """This process's environment with no DocuMind or Google variable in it, no proxy, and a fresh home and gcloud
    config: a process started with it can reach no project through Application Default Credentials."""
    drop = ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT", "PYTHONPATH", "PYTHONSAFEPATH")
    env = {k: v for k, v in os.environ.items()
           if k not in drop and not k.startswith("DOCUMIND_") and "proxy" not in k.lower()}
    env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), CLOUDSDK_CONFIG=str(home / "gcloud"),
               PYTHONIOENCODING="utf-8", NO_PROXY="127.0.0.1,localhost")
    return env


def no_gcloud_path(*first: str) -> str:
    """PATH with `first` before it and every directory that holds a gcloud left out: a gcloud the test did not write
    cannot be reached."""
    rest = [p for p in os.environ.get("PATH", "").split(os.pathsep)
            if p and not any(os.path.exists(os.path.join(p, g)) for g in GCLOUDS)]
    return os.pathsep.join([*first, *rest])


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def defs(src: str, *names: str) -> str:
    """The source of the named top-level functions, to exec without importing the module."""
    nodes = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == len(names), (names, [n.name for n in nodes])
    return "\n\n".join(ast.get_source_segment(src, n) for n in nodes)


# ------------------------------------------------------------------ the kit's paperwork
class TheTargets(unittest.TestCase):

    def setUp(self):
        self.agents = read("mk", "agents.mk")

    def test_both_targets_are_appended_to_agents_mk_and_listed(self):
        mk, readme = read("Makefile"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                  # tests and lesson 9.3 count it
        for t in ("mcp-local", "attack-agents"):
            self.assertRegex(self.agents, rf"(?m)^{t}:")
            # after the targets lesson 10.8's earlier PRs appended (append-only: lesson 10.4 reads route-eval by line)
            self.assertGreater(self.agents.index(f"\n{t}:"), self.agents.index("\nevil-mcp:"))
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")]
        self.assertTrue({"mcp-local", "attack-agents"} <= set(phony.replace("\\", " ").split()), phony[-120:])
        row = next(line for line in readme.splitlines() if line.startswith("| `agents.mk` |"))
        self.assertTrue(all(f"`{t}`" in row for t in ("mcp-local", "attack-agents")), row)
        # lesson 4.9 quotes mk/evaluation.mk's attack recipes to the end of the file: nothing of this is there
        self.assertNotIn("attack-agents", read("mk", "evaluation.mk"))

    def test_attack_agents_needs_a_project_unless_it_runs_the_peer_alone(self):
        prereq, commands = recipe(self.agents, "attack-agents")
        self.assertEqual(prereq, "$(if $(filter peer,$(SURFACES)),,guard-project)")
        self.assertEqual(commands, ['@PROJECT=$(PROJECT) REGION=$(REGION) SURFACES=$(SURFACES) CHAT=$(CHAT) '
                                    'REPORT="$(REPORT)" LABEL="$(LABEL)" PY=$(PY) bash commands/attack-agents.sh'])

    def test_the_script_mints_as_make_attack_eval_does_for_the_chat_service(self):
        script, evaluation = read("commands", "attack-agents.sh"), read("mk", "evaluation.mk")
        self.assertIn('AUD="https://documind-chat-$NUMBER.$REGION.run.app"', script)
        self.assertIn('DOCUMIND_ID_TOKEN="${DOCUMIND_ID_TOKEN:-$(gcloud auth print-identity-token --include-email \\\n'
                      '    --impersonate-service-account="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" '
                      '--audiences="$AUD")}"', script)
        # make attack-eval's member token, for rag-api: the same account, flags and fallback
        self.assertIn("TOKEN=$${DOCUMIND_ID_TOKEN:-$$(gcloud auth print-identity-token --include-email \\\n"
                      "\t  --impersonate-service-account=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com "
                      "--audiences=$$AUD)}", evaluation)
        self.assertIn('exec "$PY" evals/run_attacks.py "${args[@]}"', script)
        self.assertTrue(script.startswith("#!/usr/bin/env bash\n") and "\nset -euo pipefail\n" in script)

    def test_the_ci_lines_and_the_row(self):
        self.assertIn(CI_LINE, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = ROOT / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                         # the authoring repository's; a learner's has none
            self.assertIn(CI_LINE, repo_ci.read_text(encoding="utf-8"))
        # An UNOWNED.md row until a lesson page quotes the file; from then on INDEX.md names the lesson.
        unowned = read("UNOWNED.md")
        f = "commands/tests/test_attack_agents.py"
        row = next((l for l in read("INDEX.md").splitlines() if l.startswith(f"| `{f}` |")), "")
        self.assertTrue(f"| `{f}` | **10.8**" in unowned or row.split(" | ")[2:3] not in ([], ["-"]), f)


# ------------------------------------------------------------------ make attack-agents, in bash
STUB = r'''
import json, os, sys, time

home, args = os.environ["ATTACK_STUB_HOME"], sys.argv[1:]
with open(os.path.join(home, "calls", "%d-%d.json" % (time.time_ns(), os.getpid())), "w", encoding="utf-8") as log:
    json.dump(args, log)
if args[:2] == ["projects", "describe"]:
    print(os.environ.get("ATTACK_STUB_NUMBER", ""))
elif args[:2] == ["auth", "print-identity-token"]:
    print(os.environ["ATTACK_STUB_TOKEN"])
else:
    sys.stderr.write("stub: unexpected call: gcloud " + " ".join(args) + "\n")
    sys.exit(3)
'''


class TheScript(unittest.TestCase):
    """commands/attack-agents.sh against the stub gcloud and test_attacks.py's stand-in chat service and peer."""

    @classmethod
    def setUpClass(cls):
        cls.bash = shutil.which("bash")
        if not cls.bash:
            raise unittest.SkipTest("bash is not on PATH (CI's Linux runner has one; on Windows, Git Bash's)")
        cls.ta = ta = load(KIT / "evals" / "tests" / "test_attacks.py", "attack_agents_test_attacks")

        class Seen(ta._Good):
            """The stand-in, answering every row as the kit should; it notes the door and the bearer of each request."""
            def do_POST(self):
                self.server.seen.append((self.path, self.headers.get("Authorization")))
                super().do_POST()

        class Leaky(Seen):
            """The same, but documind-chat answers with globex's figures and citation: another tenant's text."""
            def do_POST(self):
                if self.path != "/v1/chat":
                    return super().do_POST()
                self.server.seen.append((self.path, self.headers.get("Authorization")))
                self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0)
                reply = ta.jbody(answer="GLOBEX sets 120 days of notice and 99.0% availability [1].",
                                 citations=[ta.GLOBEX_CITE], brain="langchain", scrubbed=0)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(reply)))
                self.end_headers()
                self.wfile.write(reply)

        cls.Seen, cls.Leaky = Seen, Leaky
        rows = ta.ra.load_set()
        cls.lane_ids = [r["id"] for r in ta.ra.select(rows, ["chat", "desk"])]
        cls.peer_ids = [r["id"] for r in ta.ra.select(rows, ["peer"])]

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="attack_agents_test_"))
        self.addCleanup(shutil.rmtree, self.home, True)
        for d in ("bin", "calls", "gcloud"):
            (self.home / d).mkdir()
        (self.home / "stub.py").write_text(STUB, encoding="utf-8")
        path = self.home / "bin" / "gcloud"
        with open(path, "w", encoding="utf-8", newline="\n") as f:    # text mode would write CRLF on Windows
            f.write(f'#!/bin/sh\nexec "{Path(sys.executable).as_posix()}" "{(self.home / "stub.py").as_posix()}" "$@"\n')
        path.chmod(0o755)
        self.report = self.home / "report.json"

    def serve(self, handler) -> str:
        srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        srv.seen = []
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        self.srv = srv
        return f"http://127.0.0.1:{srv.server_address[1]}"

    def run_script(self, **values) -> subprocess.CompletedProcess:
        env = {"PATH": no_gcloud_path(str(self.home / "bin")), "PY": Path(sys.executable).as_posix(),
               "REGION": REGION, "PYTHONIOENCODING": "utf-8", "NO_PROXY": "127.0.0.1,localhost",
               "HOME": str(self.home), "USERPROFILE": str(self.home), "APPDATA": str(self.home),
               "CLOUDSDK_CONFIG": str(self.home / "gcloud"), "ATTACK_STUB_HOME": str(self.home),
               "ATTACK_STUB_NUMBER": NUMBER, "ATTACK_STUB_TOKEN": TOKEN}
        for key in ("SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR", "TEMP", "TMP"):    # what Windows itself needs
            if key in os.environ:
                env[key] = os.environ[key]
        env.update({k: v for k, v in values.items() if v is not None})
        self.assertIsNone(shutil.which("gcloud", path=no_gcloud_path()))   # only the stub can answer
        return subprocess.run([self.bash, "commands/attack-agents.sh"], cwd=str(KIT), env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=300)

    def calls(self) -> list:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.home / "calls").glob("*.json"))]

    def records(self) -> list:
        return json.loads(self.report.read_text(encoding="utf-8"))["records"]

    def test_the_default_run_mints_one_token_as_the_ui_for_the_chat_service(self):
        url = self.serve(self.Seen)
        r = self.run_script(PROJECT=PROJECT, CHAT=url, REPORT=self.report.as_posix(), LABEL="fence and scrub on")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.calls(), [
            ["projects", "describe", PROJECT, "--format=value(projectNumber)"],
            ["auth", "print-identity-token", "--include-email", f"--impersonate-service-account={UI_SA}",
             f"--audiences={CANONICAL}"]])                    # the canonical URL, though CHAT= sends elsewhere
        self.assertTrue(r.stdout.startswith(f">> {url}\n"), r.stdout[:200])
        self.assertEqual(Counter(p for p, _ in self.srv.seen), {"/v1/chat": 3, "/v1/desk": 2})
        self.assertEqual({a for _, a in self.srv.seen}, {f"Bearer {TOKEN}"})
        self.assertEqual([x["id"] for x in self.records()], self.lane_ids)
        self.assertIn("Every structural row held", r.stdout)
        report = self.report.read_text(encoding="utf-8")
        self.assertNotIn(TOKEN, report)                                # never a token in a report
        self.assertEqual(json.loads(report)["label"], "fence and scrub on")

    def test_a_token_already_set_is_used_instead_of_a_mint(self):
        url = self.serve(self.Seen)
        r = self.run_script(PROJECT=PROJECT, CHAT=url, DOCUMIND_ID_TOKEN="minted-by-hand")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.calls(), [["projects", "describe", PROJECT, "--format=value(projectNumber)"]])
        self.assertEqual({a for _, a in self.srv.seen}, {"Bearer minted-by-hand"})

    def test_the_peer_joins_the_lane_rows_at_the_local_peer(self):
        url = self.serve(self.Seen)
        r = self.run_script(PROJECT=PROJECT, CHAT=url, DOCUMIND_PEER_URL=url, SURFACES="chat,desk,peer",
                            REPORT=self.report.as_posix())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f">> {url} (the A2A peer on this machine)", r.stdout)
        self.assertEqual(Counter(p for p, _ in self.srv.seen), {"/v1/chat": 3, "/v1/desk": 2, "/": 1})
        self.assertEqual(sorted(x["id"] for x in self.records()), sorted(self.lane_ids + self.peer_ids))

    def test_the_peer_alone_mints_nothing_needs_no_project_and_sends_no_token(self):
        url = self.serve(self.Seen)
        r = self.run_script(DOCUMIND_PEER_URL=url, SURFACES="peer", DOCUMIND_ID_TOKEN="left-in-the-shell",
                            REPORT=self.report.as_posix())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.calls(), [])                             # no gcloud at all
        self.assertEqual(self.srv.seen, [("/", None)])                 # and no token to the local peer
        self.assertEqual([x["id"] for x in self.records()], self.peer_ids)

    def test_an_api_surface_is_refused_before_anything_is_sent(self):
        url = self.serve(self.Seen)
        r = self.run_script(PROJECT=PROJECT, CHAT=url, SURFACES="chat,api")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("not api (rag-api's rows are make attack-eval's); no attack sent.", r.stderr)
        self.assertEqual((self.calls(), self.srv.seen), ([], []))

    def test_no_project_number_sends_nothing(self):
        url = self.serve(self.Seen)
        r = self.run_script(PROJECT=PROJECT, CHAT=url, ATTACK_STUB_NUMBER="")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ERROR: gcloud did not return a project number; no attack sent.", r.stderr)
        self.assertEqual((len(self.calls()), self.srv.seen), (1, []))

    def test_another_tenants_text_fails_the_run_with_the_runners_status(self):
        url = self.serve(self.Leaky)
        r = self.run_script(PROJECT=PROJECT, CHAT=url, REPORT=self.report.as_posix())
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("Blocked: ", r.stdout)
        self.assertIn("atk-16", json.loads(self.report.read_text(encoding="utf-8"))["failed"])


# ------------------------------------------------------------------ make mcp-local
class TheLocalServerRecipe(unittest.TestCase):
    """The seed and the server open one store, the one make chat-local seeds: the probe runs where each command
    starts, with the variables it sets, and prints the directory shared/profile.py's build_store() would open."""

    PROBE = "import os, shared.profile as p; print(os.path.abspath(p.CHROMA_DIR))"

    @classmethod
    def setUpClass(cls):
        prereq, commands = recipe(read("mk", "agents.mk"), "mcp-local")
        assert prereq == "" and len(commands) == 2, (prereq, commands)       # the seed, then the server
        cls.seed, cls.server = (start(c) for c in commands)
        _, cls.chat_local = recipe(read("Makefile"), "chat-local")

    def test_it_seeds_acmes_corpus_from_the_root_then_serves_the_mcp_server_on_loopback(self):
        cwd, env, run = self.seed
        self.assertEqual((cwd, env.get("DOCUMIND_PROFILE"), run[1:]), (KIT, "local", ["-m", "shared.local_corpus", "acme"]))
        cwd, env, run = self.server
        self.assertEqual(cwd.resolve(), (KIT / "services" / "mcp").resolve())
        self.assertEqual((env.get("DOCUMIND_PROFILE"), env.get("PYTHONPATH"), run[1:]),
                         ("local", "../..", ["-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8000"]))

    def test_it_names_the_directory_make_chat_local_seeds(self):
        mine = {env["DOCUMIND_CHROMA_DIR"] for _, env, _ in (self.seed, self.server)}
        theirs = {start(c)[1].get("DOCUMIND_CHROMA_DIR") for c in self.chat_local}
        self.assertEqual(mine, theirs)
        self.assertEqual(len(mine), 1)
        self.assertTrue(os.path.isabs(next(iter(mine))))

    def test_the_seed_and_the_server_open_one_directory(self):
        home = Path(tempfile.mkdtemp(prefix="mcp_local_probe_"))
        self.addCleanup(shutil.rmtree, home, True)
        opened = []
        for cwd, env, _ in (self.seed, self.server):
            r = subprocess.run([sys.executable, "-c", self.PROBE], cwd=str(cwd), env={**clean_env(home), **env},
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            opened.append(Path(r.stdout.strip()).resolve())
        self.assertEqual(opened[0], opened[1], "the server would open an empty store: local corpus is empty")
        self.assertEqual(opened[0], (KIT / "documind_chroma").resolve())


class _Store:
    """The local store, held in memory: Chroma's get(where=...) over the rows shared/local_corpus.py's seed() writes
    (the stand-in tools/check_local_lane.py and commands/thread_replay.py use)."""

    def __init__(self, tenant: str):
        from shared import local_corpus as lc
        self.rows = lc.chunks_for(tenant)
        self._collection = types.SimpleNamespace(count=lambda: len(self.rows))

    def get(self, where=None, include=None):
        conds = [where] if "$and" not in (where or {}) else where["$and"]

        def ok(c, k, v):
            return c.get(k) in v["$in"] if isinstance(v, dict) and "$in" in v else c.get(k) == v
        keep = [c for c in self.rows if all(ok(c, k, v) for cond in conds for k, v in cond.items())]
        return {"ids": [c["chunk_id"] for c in keep], "documents": [c["text"] for c in keep],
                "metadatas": [{"tenant_id": c["tenant_id"], "doc_type": c["doc_type"], "page": c["page_start"],
                               "source_uri": c["source_uri"], "chunk_id": c["chunk_id"]} for c in keep]}


@unittest.skipUnless(HAS_SERVER or REQUIRE, "needs fastmcp and uvicorn, the kit's MCP server's pins (the agent-pins CI step)")
class TheLocalServer(unittest.TestCase):
    """The kit's MCP server in the local profile, as make mcp-local serves it and the peer's client reaches it."""

    @classmethod
    def setUpClass(cls):
        for p in (str(KIT), str(KIT / "commands"), str(KIT / "services" / "agent")):
            if p not in sys.path:
                sys.path.insert(0, p)
        _, commands = recipe(read("mk", "agents.mk"), "mcp-local")
        cls.command = commands[1]
        atk = {r["id"]: r for r in (json.loads(l) for l in read("evals", "adversarial", "attacks.jsonl").splitlines() if l.strip())}
        cls.globex_ask, cls.forbid = atk["atk-17"]["question"], atk["atk-17"]["forbid"]

    def test_the_recipes_server_lists_the_four_pinned_tools_over_the_wire_with_no_token(self):
        import pin_tools
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = str(s.getsockname()[1])
        cwd, env, run = start(self.command, port)
        home = Path(tempfile.mkdtemp(prefix="mcp_local_serve_"))
        self.addCleanup(shutil.rmtree, home, True)
        env = {**clean_env(home), **env, "DOCUMIND_CHROMA_DIR": str(home / "chroma")}   # listing tools opens no store
        with open(home / "server.log", "w", encoding="utf-8") as log:
            proc = subprocess.Popen(run, cwd=str(cwd), env=env, stdout=log, stderr=subprocess.STDOUT)
        self.addCleanup(proc.wait, 30)
        self.addCleanup(proc.terminate)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        health, deadline = None, time.time() + 90
        while health is None and time.time() < deadline and proc.poll() is None:
            try:
                with opener.open(f"http://127.0.0.1:{port}/health", timeout=2) as r:
                    health = json.loads(r.read())
            except OSError:
                time.sleep(0.5)
        self.assertIsNotNone(health, (home / "server.log").read_text(encoding="utf-8", errors="replace")[-2000:])
        self.assertEqual((health["status"], health["profile"], health["self_url"]), ("ok", "local", None))
        with mock.patch.dict(os.environ, {"NO_PROXY": "127.0.0.1,localhost"}):
            tools = pin_tools.list_tools(url=f"http://127.0.0.1:{port}/mcp", server_local=False)
        doc = json.loads(read("services", "agent", "tool_pins.json"))
        self.assertEqual(sorted(t[0] for t in tools), sorted(doc["tools"]))
        self.assertEqual(pin_tools.check(tools, doc), [])        # a peer with TOOL_PINS=on keeps all four

    def test_in_process_it_answers_acme_and_finds_nothing_for_a_named_globex(self):
        from fastmcp import Client
        import shared.profile as profile
        from shared import documind_tools as dt
        from services.mcp import server
        store = _Store("acme")
        files = {m["source_uri"].rsplit("/", 1)[-1] for m in store.get({"tenant_id": "acme"})["metadatas"]}

        async def calls():
            async with Client(server.mcp) as c:
                out = {}
                for key, args in (("acme", {"query": "What is the notice period for a confirmed E3?"}),
                                  ("globex", {"query": self.globex_ask, "tenant": "globex"})):
                    out[key] = (await c.call_tool("retrieve", args)).structured_content
                out["docs"] = (await c.call_tool("list_documents", {})).structured_content
                out["docs_globex"] = (await c.call_tool("list_documents", {"tenant": "globex"})).structured_content
                return out

        logging.disable(logging.INFO)                     # the server's mcp_call lines and fastmcp's request lines
        try:
            with mock.patch.object(dt, "PROFILE", "local"), mock.patch.object(server, "AUDIT_BUCKET", ""), \
                    mock.patch.object(profile, "build_store", lambda embeddings=None: store):
                out = asyncio.run(calls())
        finally:
            logging.disable(logging.NOTSET)
        acme = out["acme"]
        self.assertTrue(acme["answerable"] and acme["citations"], acme)
        self.assertTrue(all("/acme/" in c["source_uri"] for c in acme["citations"]), acme["citations"])
        globex = out["globex"]                            # taken as given, and the store holds acme alone
        self.assertEqual((globex["answerable"], globex["citations"]), (False, []))
        self.assertFalse([w for w in self.forbid if w in json.dumps(globex)])
        self.assertEqual((out["docs"]["tenant"], {d["file"] for d in out["docs"]["documents"]}), ("acme", files))
        self.assertEqual((out["docs_globex"]["tenant"], out["docs_globex"]["documents"]), ("globex", []))


# ------------------------------------------------------------------ the Chat page's line
class TheChatPage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.src = read("services", "frontend", "chat.py")
        ns: dict = {}
        exec(defs(cls.src, "_scrubbed_line"), ns)
        cls.line = staticmethod(ns["_scrubbed_line"])

    def test_nothing_is_shown_when_nothing_was_scrubbed_or_the_switch_is_off(self):
        self.assertEqual(self.line({"answer": "Rs 40,000 [1]."}), "")       # AGENT_SCRUB off: no scrubbed at all
        for value in (0, None, True, False, "1", 1.0, -1):
            self.assertEqual(self.line({"scrubbed": value}), "", value)

    def test_a_count_is_said_plainly(self):
        self.assertEqual(self.line({"scrubbed": 1}), "scrubbed: 1 image, tag or link was replaced by a marker before "
                                                     "the answer left the chat service (AGENT_SCRUB)")
        self.assertEqual(self.line({"scrubbed": 3}), "scrubbed: 3 images, tags or links were replaced by markers before "
                                                     "the answer left the chat service (AGENT_SCRUB)")

    def test_its_docstring_names_the_markers_the_scrub_writes(self):
        if str(KIT) not in sys.path:
            sys.path.append(str(KIT))
        from shared import spotlight
        fn = next(n for n in ast.parse(self.src).body if isinstance(n, ast.FunctionDef) and n.name == "_scrubbed_line")
        doc = ast.get_docstring(fn)
        self.assertTrue(all(m in doc for m in (spotlight.IMAGE, spotlight.HTML, spotlight.LINK)), doc)

    def test_it_is_a_caption_under_the_brains_caption_for_the_agent_brains_only(self):
        page = next(n for n in ast.parse(self.src).body if isinstance(n, ast.FunctionDef) and n.name == "chat_page")
        agent = next(n for n in page.body if isinstance(n, ast.If) and ast.unparse(n.test) == "brain != 'direct'")
        seg = ast.get_source_segment(self.src, agent)
        caption, line, shown = (seg.index('st.caption(f"brain: '), seg.index("scrubbed = _scrubbed_line(body)"),
                                seg.index("st.caption(scrubbed)"))
        self.assertTrue(caption < line < shown < seg.index('st.session_state.messages.append'), seg[caption:shown + 40])
        self.assertEqual(self.src.count("_scrubbed_line("), 2)           # the definition and that one call
        direct = self.src[self.src.index(seg) + len(seg):self.src.index("def transcribe_from_mic")]
        self.assertNotIn("scrubbed", direct)                              # rag-api's stream has no scrub to report


if __name__ == "__main__":
    unittest.main()
