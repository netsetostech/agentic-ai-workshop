"""Offline checks for the A2A peer's delegation chain (workshop lesson 10.7): services/agent/chain.py behind PEER_CHAIN.

    python -m unittest commands/tests/test_a2a_peer.py -v          # from deploy/, in the peer image's pins

No network, no credential. The first class needs the standard library alone: agent.py's switch (PEER_CHAIN, read
once; chain.py imported only when it is on; to_a2a handed _chain_factory(); still one log call and no caller's
headers, which lesson 10.6's build asserts), chain.py's keys equal to the ones services/chat/peer.py sends and its own
logger, lesson-8.4.sh's PEER_CHAIN=${PEER_CHAIN:-off} with the cap still last on the line (lesson 5.5's build reads
it), both CI lines and the UNOWNED.md rows.

The second imports the kit's own agent.py and drives the app its to_a2a builds (Starlette's TestClient, the app's
lifespan and agent card included), with the model scripted and counted and the MCP toolset taken away, so nothing
leaves the process. It needs the peer image's pins (pip install -r services/agent/requirements.txt: google-adk 2.8.0,
a2a-sdk 1.1.2 with its server). Covered: off, to_a2a gets no factory and a request whose chain loops runs as before;
on, a looping chain and a chain of three agents each end TASK_STATE_REJECTED with the reason in the status message,
no model call, no InvalidAgentResponseError, and one a2a_refused log line (reason, chain length, hand-off id; no
words); on, a request without metadata and the chat's own chain, ["documind_adk"], each answered; on, A2A 0.3's
message/send refused as "rejected"; /health names the switch. Without the pins this class is skipped and says so;
with DOCUMIND_REQUIRE_LIBS=1, as CI's agent-pins steps set it, a missing pin is an error instead.
"""
import ast
import importlib.util
import json
import logging
import os
import re
import sys
import unittest
import uuid
import warnings
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
ROOT = KIT.parent
AGENT_DIR = KIT / "services" / "agent"
def _has(module: str) -> bool:
    """The library is importable: find_spec of a dotted name imports the parent, which may be absent (CI's shared
    interpreter has no google package), and that is a skip, not an error."""
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


LIBS = all(_has(m) for m in ("google.adk", "a2a", "httpx", "starlette"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
CI_LINE = "DOCUMIND_REQUIRE_LIBS=1 /tmp/agent-venv/bin/python -m unittest commands/tests/test_a2a_peer.py -v"


def read(*parts: str) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def constants(src: str) -> dict:
    """Module-level NAME = "literal" (and A, B = "x", "y") assignments of a source file."""
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                    out[target.id] = node.value.value
                elif isinstance(target, ast.Tuple) and isinstance(node.value, ast.Tuple):
                    for t, v in zip(target.elts, node.value.elts):
                        if isinstance(t, ast.Name) and isinstance(v, ast.Constant):
                            out[t.id] = v.value
    return out


class TheChainInTheKit(unittest.TestCase):
    """What needs no library: the switch, the keys on both sides of the hop, the deploy and the entries."""

    def test_agent_py_reads_the_switch_and_imports_chain_only_when_it_is_on(self):
        src = read("services", "agent", "agent.py")
        self.assertIn('PEER_CHAIN = os.environ.get("PEER_CHAIN", "off")', src)
        self.assertIn("app = to_a2a(agent, host=_host, port=_port, protocol=_protocol, "
                      "agent_executor_factory=_chain_factory())", src)
        tree = ast.parse(src)
        top = {a.name for n in tree.body if isinstance(n, ast.Import) for a in n.names} | \
              {n.module for n in tree.body if isinstance(n, ast.ImportFrom)}
        self.assertNotIn("chain", top)                                     # never at import: off runs as before
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_chain_factory")
        body = ast.get_source_segment(src, fn)
        self.assertIn('if PEER_CHAIN != "on":\n        return None\n    import chain\n    return chain.factory', body)
        self.assertEqual(src.count("log."), 1)                             # lesson 10.6's build: start-up only
        self.assertNotIn("request.headers", src)
        self.assertIn('"peer_chain": PEER_CHAIN', src.split("async def health(", 1)[1].split("\n\n", 1)[0])

    def test_chain_py_names_the_keys_the_chat_sends_and_logs_on_its_own(self):
        chain, peer = read("services", "agent", "chain.py"), read("services", "chat", "peer.py")
        c, p = constants(chain), constants(peer)
        self.assertEqual((c["CHAIN_KEY"], c["HANDOFF_KEY"]), (p["CHAIN_KEY"], p["HANDOFF_KEY"]))
        self.assertEqual((c["CHAIN_KEY"], c["HANDOFF_KEY"], c["MAX_HOPS"]), ("documind_chain", "documind_handoff_id", 3))
        self.assertEqual(p["ASKER"], "documind_adk")
        self.assertIn('LlmAgent(name="documind_adk"', read("services", "chat", "brains.py"))     # the asker's own name
        self.assertIn("metadata={CHAIN_KEY: [ASKER], HANDOFF_KEY: handoff_id}", peer)
        self.assertIn('log = logging.getLogger("documind.agent.chain")', chain)
        for src in (chain, read("services", "agent", "agent.py")):
            mods = {(n.module or "").split(".")[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom)} | \
                   {a.name.split(".")[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import) for a in n.names}
            self.assertFalse(mods & {"shared", "services", "commands"}, mods)   # the peer holds no kit code

    def test_the_deploy_turns_it_off_unless_asked(self):
        deploy = read("commands", "lesson-8.4.sh").split("# ---- DEPLOY ----")[1].split("# ---- SMOKE ----")[0]
        env_line = re.search(r'--set-env-vars="\^\|\^([^"]+)"', deploy)
        env = dict(kv.split("=", 1) for kv in env_line.group(1).split("|"))
        self.assertEqual(env["PEER_CHAIN"], "${PEER_CHAIN:-off}")
        self.assertTrue(deploy.split(env_line.group(1), 1)[0].endswith("^|^"))
        self.assertIn('|ADK_MAX_LLM_CALLS=12"', deploy)                    # lesson 5.5's build reads the cap there

    def test_the_ci_lines_and_the_rows(self):
        self.assertIn(CI_LINE, read(".github", "workflows", "documind-dryrun.yml"))
        self.assertIn("pip install -q -r services/agent/requirements.txt", read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = ROOT / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                               # the authoring repository's own CI
            self.assertIn(CI_LINE, repo_ci.read_text(encoding="utf-8"))
        unowned = read("UNOWNED.md")
        for f in ("services/agent/chain.py", "commands/tests/test_a2a_peer.py"):
            row = next((l for l in read("INDEX.md").splitlines() if l.startswith(f"| `{f}` |")), "")   # a page quotes it
            self.assertTrue(f"| `{f}` | **10.7**" in unowned or row.split(" | ")[2:3] not in ([], ["-"]), f)
            self.assertTrue((KIT / f).exists(), f)


@unittest.skipUnless(LIBS or REQUIRE, "needs the peer image's pins: pip install -r services/agent/requirements.txt")
class TheChainOnThePeer(unittest.TestCase):
    """The kit's agent.py over its own to_a2a, the model scripted, PEER_CHAIN off and on."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.NOTSET)
        cls.saved_env = {k: os.environ.get(k) for k in ("PEER_CHAIN", "MCP_AUTH", "ADK_MAX_LLM_CALLS")}
        if str(AGENT_DIR) not in sys.path:
            sys.path.insert(0, str(AGENT_DIR))
        from google.adk.models.base_llm import BaseLlm
        from google.adk.models.llm_response import LlmResponse
        from google.genai import types as gt
        from starlette.testclient import TestClient

        class Script(BaseLlm):
            """Gemini, scripted: every call is counted and answered in words."""
            model: str = "script"
            calls: list = []

            async def generate_content_async(self, llm_request, stream=False):
                self.calls.append(1)
                yield LlmResponse(content=gt.Content(role="model", parts=[gt.Part(text="The corpus holds 3 documents.")]))

        cls.Script = Script
        cls.peers, cls.clients = {}, {}
        for switch in ("off", "on"):
            os.environ.update(PEER_CHAIN=switch, MCP_AUTH="none")
            spec = importlib.util.spec_from_file_location(f"documind_peer_chain_{switch}", AGENT_DIR / "agent.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.agent.tools = []                    # no MCP server: the card lists no tool, and nothing is dialled
            cls.peers[switch] = mod
            cls.clients[switch] = TestClient(mod.app).__enter__()     # the lifespan: the card built, the routes added
        cls.adk_level = logging.getLogger("google_adk").level
        logging.getLogger("google_adk").setLevel(logging.ERROR)        # to_a2a sets INFO; a script has no usage to note

    @classmethod
    def tearDownClass(cls):
        for client in cls.clients.values():
            client.__exit__(None, None, None)
        for k, v in cls.saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        logging.getLogger("google_adk").setLevel(cls.adk_level)

    def ask(self, switch, metadata=None, wire="1.0"):
        """One message to the peer: (the JSON-RPC result, the model calls it took, the log records at INFO and up)."""
        mod, client = self.peers[switch], self.clients[switch]
        model = self.Script()
        mod.agent.model = model
        text = "Which documents does the corpus hold?"
        if wire == "1.0":
            params = {"message": {"messageId": str(uuid.uuid4()), "role": "ROLE_USER", "parts": [{"text": text}]}}
            body, headers = {"jsonrpc": "2.0", "id": "1", "method": "SendMessage", "params": params}, {"A2A-Version": "1.0"}
        else:
            params = {"message": {"role": "user", "kind": "message", "messageId": str(uuid.uuid4()),
                                  "parts": [{"kind": "text", "text": text}]}}
            body, headers = {"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": params}, {}
        if metadata is not None:
            params["metadata"] = metadata
        records = []
        handler = logging.Handler(logging.INFO)
        handler.emit = records.append
        root = logging.getLogger()
        level = root.level
        root.addHandler(handler)
        root.setLevel(logging.INFO)
        try:
            reply = client.post("/", json=body, headers=headers)
            health = client.get("/health").json()
        finally:
            root.removeHandler(handler)
            root.setLevel(level)
        self.assertEqual(reply.status_code, 200)
        j = reply.json()
        self.assertNotIn("error", j, j)
        self.assertFalse([r for r in records if "InvalidAgentResponseError" in (r.getMessage() + str(r.exc_info))])
        self.assertEqual(health["peer_chain"], switch)
        return j["result"], len(model.calls), records

    @staticmethod
    def refused_lines(records):
        return [json.loads(r.getMessage()) for r in records if r.name == "documind.agent.chain"]

    def test_off_to_a2a_gets_no_factory_and_a_looping_chain_runs_as_before(self):
        self.assertIsNone(self.peers["off"]._chain_factory())
        result, calls, records = self.ask("off", {"documind_chain": ["partner_agent", "documind_peer"]})
        self.assertEqual((result["task"]["status"]["state"], calls), ("TASK_STATE_COMPLETED", 1))
        self.assertEqual(result["task"]["artifacts"][0]["parts"][0]["text"], "The corpus holds 3 documents.")
        self.assertEqual(self.refused_lines(records), [])

    def test_on_a_looping_chain_is_rejected_before_any_model_call(self):
        self.assertIs(self.peers["on"]._chain_factory(), sys.modules["chain"].factory)
        result, calls, records = self.ask("on", {"documind_chain": ["partner_agent", "documind_peer"],
                                                 "documind_handoff_id": "h-loop"})
        status = result["task"]["status"]
        self.assertEqual((status["state"], calls), ("TASK_STATE_REJECTED", 0))
        self.assertEqual(status["message"]["parts"][0]["text"],
                         "delegation loop: documind_peer is already in the chain partner_agent -> documind_peer; "
                         "refused before any model call")
        (line,) = self.refused_lines(records)
        self.assertEqual({k: line[k] for k in ("event", "reason", "chain_length", "handoff_id")},
                         {"event": "a2a_refused", "reason": "loop", "chain_length": 2, "handoff_id": "h-loop"})
        self.assertEqual(line["task_id"], result["task"]["id"])
        self.assertNotIn("documents", json.dumps(line))                    # never the question's words
        self.assertNotIn("partner_agent", json.dumps(line))                # never an agent's name

    def test_on_a_chain_of_three_is_a_third_hop_and_rejected(self):
        result, calls, records = self.ask("on", {"documind_chain": ["a", "b", "c"]})
        status = result["task"]["status"]
        self.assertEqual((status["state"], calls), ("TASK_STATE_REJECTED", 0))
        self.assertTrue(status["message"]["parts"][0]["text"].startswith("too many hops: 3 (the chain a -> b -> c;"))
        self.assertEqual([(x["reason"], x["chain_length"], x["handoff_id"]) for x in self.refused_lines(records)],
                         [("hops", 3, None)])

    def test_on_no_chain_and_the_chats_own_chain_are_answered(self):
        for metadata in (None, {"documind_chain": ["documind_adk"], "documind_handoff_id": "h-1"},
                         {"documind_chain": ["documind_adk", "partner_agent"]}):
            with self.subTest(metadata=metadata):
                result, calls, records = self.ask("on", metadata)
                self.assertEqual((result["task"]["status"]["state"], calls), ("TASK_STATE_COMPLETED", 1))
                self.assertEqual(self.refused_lines(records), [])

    def test_on_the_0_3_wire_reads_rejected(self):
        result, calls, _ = self.ask("on", {"documind_chain": ["documind_peer"]}, wire="0.3")
        self.assertEqual((result["kind"], result["status"]["state"], calls), ("task", "rejected", 0))
        self.assertIn("delegation loop", result["status"]["message"]["parts"][0]["text"])

    def test_the_rule_itself(self):
        chain = sys.modules.get("chain") or importlib.import_module("chain")
        self.assertEqual(chain.chain_of({}), [])
        self.assertEqual(chain.chain_of({"documind_chain": "x"}), ["x"])
        self.assertEqual(chain.chain_of({"documind_chain": [1, "b"]}), ["1", "b"])
        self.assertIsNone(chain.refusal(["documind_adk", "partner_agent"], "documind_peer"))
        self.assertEqual(chain.refusal(["documind_peer"], "documind_peer")[0], "loop")
        self.assertEqual(chain.refusal(["documind_peer", "a", "b"], "documind_peer")[0], "loop")   # a loop first
        self.assertEqual(chain.refusal(["a"] * 20, "p")[1].count("->"), 8)                       # the words stay short


if __name__ == "__main__":
    unittest.main()
