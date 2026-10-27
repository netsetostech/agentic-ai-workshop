"""Offline tests of the Ralph loop's egress proxy (workshop lesson 10.10, RALPH_EGRESS=proxy): commands/ralph/egress.py
and its wiring in commands/ralph.py. Nothing reaches a model, Google Cloud or the network: the proxy runs on this
machine's loopback, with a stand-in upstream in place of the model endpoint and a dialler that refuses everything
else, and the loop and the probe run against test_ralph.py's stub docker, taught here to answer docker network, docker
run -d, docker logs and the probe's reach run.

Covered: the rules (an allowed CONNECT; another host, port, suffix or IP; a plain request; a malformed, oversized or
slow head; an endpoint that cannot be reached), and that a refused request is never dialled; the tunnel carrying bytes
both ways, those sent with the head included; the log, a line a request, never a URL's path or query; the proxy's own
command line end to end on loopback; the standard library alone; the allowlist and its reasons (Vertex AI on global,
settings.json's vertex-ai); the switch (off by default, the flag, RALPH_EGRESS, a wrong word refused, offline never
reading it); the docker commands around an iteration (the internal network, the proxy and its alias, the agent's line
with --network and HTTPS_PROXY added and nothing else changed, the log kept, the proxy and the network removed), a
refused host counted, a proxy that does not start or never listens stopping the loop with nothing left, the default
untouched, the dry run, the probe's three free checks and its calls behind the proxy; mk/coding.mk's recipes and the
UNOWNED.md rows.
"""
import ast
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1]
for _p in (str(HERE), str(KIT / "commands")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import ralph  # noqa: E402
import test_ralph as tr  # noqa: E402 - its stub docker and Stubbed; only the module is bound, so none of its tests run twice

_spec = importlib.util.spec_from_file_location("ralph_egress_proxy", ralph.EGRESS_PY)
egress = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(egress)

ALLOWED = ralph.EGRESS_ALLOW[0]
NEW_FILES = ("commands/ralph/egress.py", "commands/tests/test_ralph_egress.py")


def read(*parts: str) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def reply_of(sock: socket.socket) -> bytes:
    """A response's head, to its blank line (or to the close)."""
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data


def status_of(sock: socket.socket) -> str:
    return reply_of(sock).split(b"\r\n", 1)[0].decode("latin-1")


def echo_server() -> socket.socket:
    """A loopback server that sends back each connection's bytes upper-cased: the stand-in model endpoint."""
    server = socket.create_server(("127.0.0.1", 0))

    def one(conn: socket.socket) -> None:
        with conn:
            while True:
                data = conn.recv(4096)
                if not data:
                    return
                conn.sendall(data.upper())

    def serve() -> None:
        while True:
            try:
                conn, _ = server.accept()
            except OSError:
                return
            threading.Thread(target=one, args=(conn,), daemon=True).start()

    threading.Thread(target=serve, daemon=True).start()
    return server


# ----------------------------------------------------------------------------- the proxy, on loopback
class Proxying(unittest.TestCase):
    """egress.Proxy on loopback. Its dialler connects ALLOWED to the stand-in and records every call, and refuses
    anything else, so a refused request that dialled would show; nothing leaves the machine."""

    def setUp(self):
        self.upstream = echo_server()
        self.addCleanup(self.upstream.close)
        self.dialled, self.lines, self.unreachable = [], [], False
        self.proxy = egress.Proxy(("127.0.0.1", 0), [ALLOWED], dial=self.dial, log=self.lines.append,
                                  head_timeout_s=0.5)
        threading.Thread(target=self.proxy.serve_forever, daemon=True).start()
        self.addCleanup(self.proxy.server_close)
        self.addCleanup(self.proxy.shutdown)

    def dial(self, want: str) -> socket.socket:
        self.dialled.append(want)
        if want != ALLOWED or self.unreachable:
            raise OSError("stand-in: unreachable")
        return socket.create_connection(self.upstream.getsockname(), 5)

    def ask(self, data: bytes) -> socket.socket:
        s = socket.create_connection(self.proxy.server_address[:2], 5)
        self.addCleanup(s.close)
        s.sendall(data)
        return s

    def connect(self, where: str, extra: bytes = b"") -> socket.socket:
        return self.ask(f"CONNECT {where} HTTP/1.1\r\nHost: {where}\r\n\r\n".encode() + extra)

    def test_an_allowed_connect_is_a_tunnel_both_ways(self):
        s = self.connect(ALLOWED)
        self.assertEqual(status_of(s), "HTTP/1.1 200 Connection established")
        s.sendall(b"ping")
        self.assertEqual(s.recv(16), b"PING")
        self.assertEqual(self.dialled, [ALLOWED])
        self.assertEqual(self.lines, [f"allowed {ALLOWED}"])

    def test_bytes_sent_with_the_head_reach_the_endpoint(self):
        s = self.connect(ALLOWED, b"hello")
        head = reply_of(s)
        self.assertTrue(head.startswith(b"HTTP/1.1 200 "), head)
        rest = head.partition(b"\r\n\r\n")[2]
        while len(rest) < 5:
            rest += s.recv(16)
        self.assertEqual(rest, b"HELLO")

    def test_the_host_is_matched_exactly_and_a_refusal_dials_nothing(self):
        s = self.connect("AIPlatform.GoogleAPIs.com.:443")          # case and a trailing dot are folded
        self.assertEqual(status_of(s), "HTTP/1.1 200 Connection established")
        self.assertEqual(self.dialled, [ALLOWED])
        for where in ("example.com:443", "aiplatform.googleapis.com:80", "googleapis.com:443",
                      "aiplatform.googleapis.com.example.com:443", "evil-aiplatform.googleapis.com:443",
                      "169.254.169.254:80", "[::1]:443", "aiplatform.googleapis.com", "localhost:443",
                      "aiplatform.googleapis.com:443:443", "*.googleapis.com:443"):
            with self.subTest(where=where):
                self.assertEqual(status_of(self.connect(where)), "HTTP/1.1 403 Forbidden")
        self.assertEqual(self.dialled, [ALLOWED])
        self.assertIn("refused example.com:443: not on the allowlist", self.lines)
        self.assertIn("refused [::1]:443: not host:port", self.lines)

    def test_a_plain_request_is_refused_and_its_url_never_logged(self):
        for line, words in (("GET http://example.com/v1/x?key=SECRET-123 HTTP/1.1", "refused GET example.com"),
                            (f"POST http://{ALLOWED.split(':')[0]}/v1/models?key=SECRET-123 HTTP/1.1",
                             f"refused POST {ALLOWED.split(':')[0]}"),
                            ("GET /?key=SECRET-123 HTTP/1.1", "refused GET a path")):
            with self.subTest(line=line):
                s = self.ask(f"{line}\r\nHost: example.com\r\n\r\n".encode())
                self.assertEqual(status_of(s), "HTTP/1.1 403 Forbidden")
                self.assertEqual(self.lines[-1], f"{words}: only CONNECT tunnels, to an allowed host:port")
        self.assertEqual(self.dialled, [])
        self.assertFalse([line for line in self.lines if "SECRET" in line or "/v1" in line])

    def test_a_malformed_oversized_or_slow_head_is_a_400(self):
        # one byte over the limit: the proxy reads every byte sent before it refuses, so its close is not a reset
        for data in (b"HELLO\r\n\r\n", f"CONNECT {ALLOWED} HTTP/2.0\r\n\r\n".encode(), b"X" * (egress.HEAD_LIMIT + 1)):
            with self.subTest(data=data[:30]):
                self.assertEqual(status_of(self.ask(data)), "HTTP/1.1 400 Bad Request")
        started = time.monotonic()
        self.assertEqual(status_of(self.ask(b"")), "HTTP/1.1 400 Bad Request")        # nothing sent: cut at 0.5 s
        self.assertLess(time.monotonic() - started, 5)
        self.assertEqual(self.dialled, [])

    def test_an_endpoint_that_cannot_be_reached_is_a_502(self):
        self.unreachable = True
        self.assertEqual(status_of(self.connect(ALLOWED)), "HTTP/1.1 502 Bad Gateway")
        self.assertEqual(self.lines, [f"failed {ALLOWED}: OSError: stand-in: unreachable"])

    def test_the_log_counted_as_the_loop_counts_it(self):
        self.assertEqual(status_of(self.connect(ALLOWED)), "HTTP/1.1 200 Connection established")
        self.assertEqual(status_of(self.connect("example.com:443")), "HTTP/1.1 403 Forbidden")
        self.assertEqual(status_of(self.connect("example.com:443")), "HTTP/1.1 403 Forbidden")
        seen = ralph.egress_seen("\n".join(self.lines))
        self.assertEqual(seen, {"allowed": {ALLOWED: 1}, "refused": {"example.com:443": 2}, "failed": {}})
        self.assertEqual(ralph.egress_words(seen), f"allowed {ALLOWED} (1); refused example.com:443 (2)")


class CommandLine(unittest.TestCase):
    def test_the_proxy_end_to_end_on_loopback(self):
        # egress.py as its container runs it (python -I -B -u), allowing only the stand-in's loopback address. The
        # refused target is a loopback port nothing listens on: had the proxy dialled it, the answer would be a 502.
        upstream = echo_server()
        self.addCleanup(upstream.close)
        port = upstream.getsockname()[1]
        p = subprocess.Popen([sys.executable, "-I", "-B", "-u", str(ralph.EGRESS_PY), "--listen", "127.0.0.1:0",
                              "--allow", f"127.0.0.1:{port}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8")
        self.addCleanup(p.kill)
        first = p.stdout.readline().strip()
        self.assertTrue(first.startswith("egress: listening on 127.0.0.1:"), first)
        self.assertTrue(first.endswith(f"; allowed: 127.0.0.1:{port}"), first)
        listen = int(first.split("127.0.0.1:")[1].split(";")[0])
        with socket.create_connection(("127.0.0.1", listen), 5) as s:
            s.sendall(f"CONNECT 127.0.0.1:{port} HTTP/1.1\r\n\r\n".encode())
            self.assertEqual(status_of(s), "HTTP/1.1 200 Connection established")
            s.sendall(b"over")
            self.assertEqual(s.recv(16), b"OVER")
        with socket.create_connection(("127.0.0.1", listen), 5) as s:
            s.sendall(b"CONNECT 127.0.0.1:1 HTTP/1.1\r\n\r\n")
            self.assertEqual(status_of(s), "HTTP/1.1 403 Forbidden")
        p.kill()
        out, _ = p.communicate(timeout=30)
        self.assertEqual(out.splitlines(), [f"allowed 127.0.0.1:{port}", "refused 127.0.0.1:1: not on the allowlist"])

    def test_a_bad_allowlist_entry_stops_it(self):
        for bad in ("*.googleapis.com:443", "googleapis", "aiplatform.googleapis.com", "aiplatform.googleapis.com:0",
                    "aiplatform.googleapis.com:65536", "https://aiplatform.googleapis.com", "[::1]:443",
                    "localhost:443", "aiplatform.googleapis.com:4²3"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                egress.target(bad)
        with mock.patch.object(sys, "stderr", new=open(os.devnull, "w", encoding="utf-8")) as err:
            self.addCleanup(err.close)
            self.assertEqual(egress.main(["--allow", "*.googleapis.com:443", "--listen", "127.0.0.1:0"]), 2)

    def test_the_standard_library_alone(self):
        tree = ast.parse(ralph.EGRESS_PY.read_text(encoding="utf-8"))
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertLessEqual(names, set(sys.stdlib_module_names) | {"__future__"})


# ----------------------------------------------------------------------------- commands/ralph.py, no docker
class Wiring(unittest.TestCase):
    def test_the_model_endpoint_alone_and_why(self):
        self.assertEqual(ralph.EGRESS_ALLOW, ("aiplatform.googleapis.com:443",))
        self.assertEqual(egress.target(ALLOWED), ALLOWED)               # the proxy takes the entry as written
        settings = json.loads(read("commands", "ralph", "settings.json"))
        self.assertEqual(settings["security"]["auth"]["selectedType"], "vertex-ai")
        values = ralph.GeminiCliAgent("docker", "documind-ralph", "gemini-3.6-flash", tr.KEY,
                                      "documind-ai-YOUR-ID").env_values()
        self.assertEqual((values["GOOGLE_GENAI_USE_VERTEXAI"], values["GOOGLE_CLOUD_LOCATION"]), ("true", "global"))

    def test_the_switch(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("RALPH_EGRESS", None)
            self.assertEqual(ralph.egress_mode(), "off")
            self.assertEqual(ralph.egress_mode("proxy"), "proxy")
            os.environ["RALPH_EGRESS"] = "proxy"
            self.assertEqual(ralph.egress_mode(), "proxy")
            self.assertEqual(ralph.egress_mode("off"), "off")              # the flag wins
            os.environ["RALPH_EGRESS"] = " "
            self.assertEqual(ralph.egress_mode(), "off")
            os.environ["RALPH_EGRESS"] = "squid"
            with self.assertRaises(ralph.Refused):
                ralph.egress_mode()

    def test_the_commands_around_an_iteration(self):
        e = ralph.Egress("docker", "documind-ralph", "ralph-abcd1234-01")
        net, run, join = e.up_commands()
        self.assertEqual(net, ["docker", "network", "create", "--internal", "ralph-abcd1234-01-net"])
        self.assertEqual(run[:5], ["docker", "run", "-d", "--name", "ralph-abcd1234-01-egress"])
        line = " ".join(run)
        for words in ("--network bridge", "--read-only", "--cap-drop ALL", "--security-opt no-new-privileges",
                      "--memory 256m", "--pids-limit 128",
                      f"--mount type=bind,source={ralph.EGRESS_PY},target=/egress/egress.py,readonly",
                      f"documind-ralph python3 -I -B -u /egress/egress.py --listen 0.0.0.0:3128 --allow {ALLOWED}"):
            self.assertIn(words, line)
        for never in ("--env-file", "target=/work", "--workdir", "GOOGLE_", "docker.sock", "--privileged", "--publish",
                      " -p "):                       # the workspace mount and the agent's workdir, never the proxy's
            self.assertNotIn(never, line)
        self.assertEqual(join, ["docker", "network", "connect", "--alias", "egress", "ralph-abcd1234-01-net",
                                "ralph-abcd1234-01-egress"])
        self.assertEqual(e.down_commands(), [["docker", "logs", "ralph-abcd1234-01-egress"],
                                             ["docker", "rm", "-f", "ralph-abcd1234-01-egress"],
                                             ["docker", "network", "rm", "ralph-abcd1234-01-net"]])
        self.assertTrue(ralph.EGRESS_PY.is_file())

    def test_the_agents_line_gains_two_flags_and_nothing_else(self):
        plain = ralph.GeminiCliAgent("docker", "documind-ralph", "gemini-3.6-flash", tr.KEY)
        held = ralph.EgressAgent("docker", "documind-ralph", "gemini-3.6-flash", tr.KEY)
        where = (Path("/r/workspace"), Path("/r/agent.env"), "ralph-abcd1234-01")
        a, b = plain.command(*where), held.command(*where)
        at = a.index("--name") + 2
        self.assertEqual(b, a[:at] + ["--network", "ralph-abcd1234-01-net", "--env", "HTTPS_PROXY=http://egress:3128"]
                         + a[at:])
        self.assertNotIn("--network", a)                                   # off: the line as it was
        self.assertEqual(held.env_values(), plain.env_values())            # the env file holds the key alone, as before

    def test_the_reach_check_is_one_line_of_python(self):
        compile(ralph.REACH_SOURCE, "reach", "exec")                        # compiled, never run here: it dials out
        self.assertEqual(ast.literal_eval(ralph.REACH[len("exec("):-1]), ralph.REACH_SOURCE)
        for ch in "\n\r&|<>^%":                                             # nothing a shell or cmd.exe would act on
            self.assertNotIn(ch, ralph.REACH)
        self.assertIn(f'via("{ALLOWED}")', ralph.REACH_SOURCE)

    def test_the_recipes_and_the_rows(self):
        coding = read("mk", "coding.mk").splitlines()
        for target in ("ralph", "ralph-probe"):
            recipe = coding[coding.index(next(x for x in coding if x.startswith(f"{target}:"))) + 1]
            self.assertTrue(recipe.endswith(" $(if $(RALPH_EGRESS),--egress $(RALPH_EGRESS),)"), recipe)
        self.assertIn("# RALPH_EGRESS=proxy, here and on make ralph", "\n".join(coding))
        unowned, index = read("UNOWNED.md"), read("INDEX.md").splitlines()

        def quoted(f):
            row = next((x for x in index if x.startswith(f"| `{f}` |")), "")
            return row.split(" | ")[2:3] not in ([], ["-"])

        self.assertIn("## Coding agents (lesson 10.10)", unowned)
        for f in NEW_FILES:
            self.assertTrue((KIT / f).exists(), f)
            self.assertTrue(f"`{f}`" in unowned or quoted(f), f)


# ----------------------------------------------------------------------------- through the stub docker
EGRESS_STUB = '''
if args[:1] == ["network"]:
    record(kind="network", verb=args[1])
    if world.get("network_fails") == args[1]:
        sys.stderr.write("Error response from daemon: the stub refuses network " + args[1] + "\\n")
        sys.exit(1)
    sys.exit(0)
if args[:2] == ["run", "-d"]:
    record(kind="proxy")
    if world.get("proxy_fails"):
        sys.stderr.write("docker: Error response from daemon: the stub refuses the proxy\\n")
        sys.exit(125)
    print("0123456789abcdef")
    sys.exit(0)
if args[:1] == ["logs"]:
    record(kind="logs")
    if not world.get("proxy_silent"):
        print("egress: listening on 0.0.0.0:3128; allowed: aiplatform.googleapis.com:443")
        print("\\n".join(world.get("proxy_log", ["allowed aiplatform.googleapis.com:443"])))
    sys.exit(0)
if args[:1] == ["run"] and "ralph-probe-reach" in args:
    record(kind="reach")
    print("\\n".join(world.get("reach", [])))
    sys.exit(0)
'''
ANCHOR = 'if args[:2] == ["image", "inspect"]:'
REACHED = ["NAME example.com did not resolve",
           "DIRECT example.com:443 gaierror: [Errno -3] Temporary failure in name resolution",
           "DIRECT 169.254.169.254:80 OSError: [Errno 101] Network is unreachable",
           "PROXY example.com:443 HTTP/1.1 403 Forbidden",
           f"PROXY {ALLOWED} HTTP/1.1 200 Connection established"]


class BehindStub(tr.Stubbed):
    """test_ralph.py's stub docker with the egress answers (no tests of its own)."""

    def setUp(self):
        super().setUp()
        self.assertIn(ANCHOR, tr.STUB)
        (self.home / "stub.py").write_text(tr.STUB.replace(ANCHOR, EGRESS_STUB + ANCHOR, 1), encoding="utf-8")

    def behind(self, kind=ralph.EgressAgent, **caps) -> dict:
        self.lines, say = tr.quiet()
        agent = kind(self.docker, "documind-ralph", "gemini-3.6-flash", tr.KEY, None, 120)
        oracle = ralph.Oracle("strong", image="documind-ralph", docker=self.docker)
        return ralph.run_loop(ralph.TASKS["deadline"], agent, oracle, out=self.tmp / "runs", say=say, **caps)

    def sequence(self) -> list:
        """The docker calls but the oracle's, as (kind, verb)."""
        return [(c["kind"], c.get("verb")) for c in self.calls() if c["kind"] != "oracle"]


class Behind(BehindStub):
    """The loop run behind the proxy, through the stub."""

    def test_the_loop_behind_the_proxy(self):
        self.scenario({"file": self.file_with("placeholder"), "tick": True},
                      {"file": self.file_with("reference"), "tick": True, "response": "Done.\n" + ralph.DONE},
                      proxy_log=[f"allowed {ALLOWED}", f"allowed {ALLOWED}"])
        s = self.behind(max_iters=5, budget_inr=100)
        self.assertEqual((s["stopped_by"], [r["oracle"] for r in s["iterations"]]), ("oracle_passed", ["FAIL", "PASS"]))
        self.assertEqual(s["egress"], {"mode": "proxy", "allow": [ALLOWED], "logs": "iterations/NN-egress.txt"})
        run = Path(s["run"])
        for i, rec in enumerate(s["iterations"], 1):
            self.assertEqual(rec["egress"], {"allowed": {ALLOWED: 2}, "refused": {}, "failed": {}})
            log = (run / "iterations" / f"{i:02d}-egress.txt").read_text(encoding="utf-8")
            self.assertEqual(log.splitlines(), ["egress: listening on 0.0.0.0:3128; allowed: " + ALLOWED,
                                                f"allowed {ALLOWED}", f"allowed {ALLOWED}"])
        one = [("network", "create"), ("proxy", None), ("network", "connect"), ("logs", None), ("agent", None),
               ("logs", None), ("rm", None), ("network", "rm")]
        self.assertEqual(self.sequence(), one + one)
        self.assertIn(f"  egress: RALPH_EGRESS=proxy, each iteration's agent on an internal network of its own; its "
                      f"proxy opens a tunnel to {ALLOWED} and refuses everything else", self.lines)
        self.assertEqual(self.lines.count(f"    egress: allowed {ALLOWED} (2); refused nothing"), 2)
        # each agent's line is GeminiCliAgent's own, held to its iteration's network, and nothing else
        plain = ralph.GeminiCliAgent(self.docker, "documind-ralph", "gemini-3.6-flash", tr.KEY)
        for i, c in enumerate(self.calls("agent"), 1):
            name = f"ralph-{run.name[-8:]}-{i:02d}".lower()
            line = plain.command(Path(s["workspace"]), run / "agent.env", name)
            self.assertEqual(c["args"], ralph.held_to(line, ralph.Egress(self.docker, "documind-ralph", name))[1:])
            self.assertEqual(c["env_names"], ["GOOGLE_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI"])
            self.assertTrue(c["key_ok"])
        nets = [c["args"] for c in self.calls("network")]
        self.assertEqual(nets[0], ["network", "create", "--internal", f"ralph-{run.name[-8:]}-01-net".lower()])
        for c in self.calls("proxy"):
            self.assertNotIn("--env-file", c["args"])
        for c in self.calls("oracle"):
            self.assertEqual(c["args"][c["args"].index("--network") + 1], "none")
        self.assertFalse((run / "agent.env").exists())
        everything = "\n".join(self.lines) + json.dumps(self.calls()) + "".join(
            p.read_text(encoding="utf-8") for p in run.rglob("*") if p.is_file() and p.suffix in (".json", ".txt"))
        self.assertNotIn(tr.KEY, everything)

    def test_a_refused_host_is_counted_and_shown(self):
        self.scenario({"file": self.file_with("reference")},
                      proxy_log=[f"allowed {ALLOWED}", "refused example.com:443: not on the allowlist"])
        s = self.behind(max_iters=2, budget_inr=50)
        self.assertEqual(s["iterations"][0]["egress"]["refused"], {"example.com:443": 1})
        self.assertIn(f"    egress: allowed {ALLOWED} (1); refused example.com:443 (1)", self.lines)

    def test_a_proxy_that_does_not_start_stops_the_loop_and_leaves_nothing(self):
        self.scenario({"file": self.file_with("reference")}, proxy_fails=True)
        s = self.behind(max_iters=3, budget_inr=50)
        self.assertEqual((s["stopped_by"], s["iterations"]), ("error", []))
        self.assertIn("the egress proxy did not start: docker run -d: docker: Error response from daemon", s["why"])
        self.assertEqual(self.sequence(), [("network", "create"), ("proxy", None), ("logs", None), ("rm", None),
                                           ("network", "rm")])

    def test_a_proxy_that_never_listens_stops_the_loop_and_leaves_nothing(self):
        self.scenario({"file": self.file_with("reference")}, proxy_silent=True)
        with mock.patch.object(ralph, "EGRESS_WAIT_S", 0.3):
            s = self.behind(max_iters=3, budget_inr=50)
        self.assertEqual(s["stopped_by"], "error")
        self.assertIn("the egress proxy did not listen within 0.3 s", s["why"])
        self.assertFalse(self.calls("agent"))
        self.assertEqual(self.sequence()[-3:], [("logs", None), ("rm", None), ("network", "rm")])
        self.assertEqual(self.sequence().count(("network", "create")), 1)

    def test_a_network_that_will_not_go_is_named(self):
        self.scenario({"file": self.file_with("reference")}, network_fails="rm")
        s = self.behind(max_iters=1, budget_inr=50)
        self.assertIn("docker network rm ralph-", s["iterations"][0]["egress"]["error"])
        self.assertTrue(any(x.startswith("    egress: allowed ") and "docker network rm" in x for x in self.lines))

    def test_off_nothing_changes(self):
        self.scenario({"file": self.file_with("reference")})
        s = self.behind(kind=ralph.GeminiCliAgent, max_iters=1, budget_inr=50)
        self.assertEqual(self.sequence(), [("agent", None)])
        self.assertNotIn("--network", self.calls("agent")[0]["args"])
        self.assertNotIn("egress", s)
        self.assertNotIn("egress", s["iterations"][0])
        self.assertFalse([x for x in self.lines if "egress" in x])
        self.assertFalse(list((Path(s["run"]) / "iterations").glob("*-egress.txt")))


class BehindCommand(BehindStub):
    """ralph.main's loop --dry-run, loop --offline and probe, with the switch on and off, through the stub."""

    def main(self, *argv, env=None) -> tuple[int, str]:
        """ralph.main with the stub as the only docker; env values of None are unset for the call."""
        lines, say = tr.quiet()
        env = {"RALPH_API_KEY": tr.KEY, "RALPH_BUDGET_INR": None, "RALPH_EGRESS": None, **(env or {})}
        with mock.patch.dict(os.environ, {k: v for k, v in env.items() if v is not None}), \
                mock.patch.object(ralph.shutil, "which", lambda name: self.docker):
            for k in [k for k, v in env.items() if v is None]:
                os.environ.pop(k, None)
            code = ralph.main(list(argv), say)
        return code, "\n".join(lines)

    def test_the_dry_run_behind_the_proxy(self):
        code, out = self.main("loop", "--dry-run", "--egress", "proxy")
        self.assertEqual(code, 0)
        d = self.docker
        self.assertEqual(out.count(f"{d} run "), 3)                     # the proxy, the agent, the oracle
        for words in (f"{d} network create --internal ralph-<run>-01-net",
                      f"{d} run -d --name ralph-<run>-01-egress --network bridge",
                      f"--allow {ALLOWED}", f"{d} network connect --alias egress ralph-<run>-01-net ralph-<run>-01-egress",
                      "--name ralph-<run>-01 --network ralph-<run>-01-net --env HTTPS_PROXY=http://egress:3128 --cap-drop ALL",
                      f"{d} logs ralph-<run>-01-egress", f"{d} rm -f ralph-<run>-01-egress",
                      f"{d} network rm ralph-<run>-01-net", "--network none", "(values never printed)"):
            self.assertIn(words, out)
        self.assertFalse(self.calls())
        self.assertEqual(self.main("loop", "--dry-run", env={"RALPH_EGRESS": "proxy"}), (0, out))
        code, off = self.main("loop", "--dry-run", env={"RALPH_EGRESS": "off"})
        self.assertEqual((code, off.count(f"{d} run "), f"{d} network " in off, "egress" in off), (0, 2, False, False))
        self.assertEqual(self.main("loop", "--dry-run"), (0, off))
        code, out = self.main("loop", "--dry-run", env={"RALPH_EGRESS": "squid"})
        self.assertEqual(code, 2)
        self.assertIn("ERROR: RALPH_EGRESS is off or proxy, not 'squid'", out)
        self.assertFalse(self.calls())

    def test_offline_never_reads_the_switch(self):
        code, out = self.main("loop", "--offline", "--max-iters", "1", "--out", str(self.tmp / "o"),
                              env={"RALPH_EGRESS": "squid"})
        self.assertEqual(code, 1)
        self.assertNotIn("egress", out.lower())
        self.assertFalse(self.calls())

    def test_the_probe_behind_the_proxy(self):
        self.scenario({"response": "OK"}, {"response": "NO-WEB-TOOL"}, image=True, label="9.9.9", reach=REACHED,
                      proxy_log=[f"allowed {ALLOWED}", "refused example.com:443: not on the allowlist"])
        code, out = self.main("probe", "--egress", "proxy")
        self.assertEqual(code, 0)
        self.assertIn("model gemini-3.6-flash, RALPH_EGRESS=proxy", out)
        self.assertIn("3. the oracle's container (--network none) reaches example.com: refused, as it must be", out)
        self.assertIn("4. what the agent's container holds: observed - env names ['GOOGLE_API_KEY', "
                      "'GOOGLE_GENAI_USE_VERTEXAI', 'HOME', 'HTTPS_PROXY', 'PATH', 'RALPH_MODEL']", out)
        self.assertIn("5. the agent's container reaches example.com and 169.254.169.254 directly: refused, as it must "
                      "be - example.com did not resolve; example.com:443: gaierror: [Errno -3] Temporary failure in "
                      "name resolution; 169.254.169.254:80: OSError: [Errno 101] Network is unreachable", out)
        self.assertIn("6. the egress proxy opens a tunnel to example.com:443: refused, as it must be - "
                      "HTTP/1.1 403 Forbidden", out)
        self.assertIn(f"7. the egress proxy opens a tunnel to {ALLOWED}: observed - HTTP/1.1 200 Connection "
                      "established (nothing sent through it, Rs 0)", out)
        self.assertIn(f"   the proxy's log: allowed {ALLOWED} (1); refused example.com:443 (1)", out)
        self.assertIn("8. one headless call: not tested - add YES=1", out)
        self.assertEqual(self.sequence()[-9:], [("network", "create"), ("proxy", None), ("network", "connect"),
                                                ("logs", None), ("holds", None), ("reach", None), ("logs", None),
                                                ("rm", None), ("network", "rm")])
        for c in self.calls("holds") + self.calls("reach"):
            a = c["args"]
            self.assertEqual(a[a.index("--network") + 1], "ralph-probe-net")
            self.assertIn("HTTPS_PROXY=http://egress:3128", a)
        self.assertEqual(self.calls("reach")[0]["args"][-4:], ["python3", "-I", "-c", ralph.REACH])
        self.assertFalse(self.calls("agent"))
        code, out = self.main("probe", "--egress", "proxy", "--yes")
        self.assertEqual(code, 0)
        self.assertIn("8. one headless call: observed", out)
        self.assertIn("9. the web tools excluded: observed", out)
        self.assertEqual(out.count(f"   the egress proxy on this call: allowed {ALLOWED} (1); refused example.com:443 "
                                   "(1)"), 2)
        agents = self.calls("agent")
        self.assertEqual([a["args"][a["args"].index("--network") + 1] for a in agents],
                         ["ralph-probe-8-net", "ralph-probe-9-net"])
        self.assertNotIn(tr.KEY, out)

    def test_the_probe_when_the_proxy_does_not_start(self):
        self.scenario(image=True, proxy_fails=True)
        code, out = self.main("probe", "--egress", "proxy")
        self.assertEqual(code, 0)
        self.assertIn("4. the egress proxy and its network: refused - the egress proxy did not start", out)
        self.assertFalse(self.calls("holds"))
        self.assertEqual([c["verb"] for c in self.calls("network")], ["create", "rm"])

    def test_the_probe_off_is_the_probe_as_it_was(self):
        self.scenario(image=True, label="9.9.9")
        code, out = self.main("probe")
        self.assertEqual(code, 0)
        self.assertIn("5. one headless call: not tested - add YES=1", out)
        self.assertNotIn("egress", out.lower())
        self.assertFalse([c for c in self.calls() if c["kind"] in ("network", "proxy", "logs", "reach")])


if __name__ == "__main__":
    unittest.main()
