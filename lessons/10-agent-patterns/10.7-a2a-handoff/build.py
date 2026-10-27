"""Build lesson 10.7 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The ADK brain hands one question to the A2A peer: services/chat/peer.py's documind_peer, off unless PEER_URL is set.
Only the question crosses. A gate refuses a third hand-off in a turn, and a confused deputy, before anything is sent;
a hand-off waits at most 75 s and never past the turn's deadline; the peer stops a task at 12 model calls. Then loops
and deadlocks: a cycle among the lane's own services is refused by construction (make check-callers GRAPH=1), and a
loop through an agent the lane does not run at run time (services/agent/chain.py, PEER_CHAIN, off by default).

Build-time proof, offline, Rs 0:
  - the hand-off end to end: the kit's chat app (services/chat/agent.py under FastAPI's TestClient, the desk's door in
    front) and its ADK brain, peer.py sending through a2a-sdk's client to the kit's own peer (services/agent/agent.py
    over its own to_a2a). Gemini is scripted on both sides; the rosters, the tokens, Cloud Run's IAM check and rag-api
    are stood in, and the peer's MCP toolset is two local functions (lesson 10.6 traces the real one).
  - the peer's cap stopping a scripted loop at 12 model calls, and make agent-drill's two verdict lines from the
    drill's own Python, against the peer at a cap of 1 and at its default.
  - a cycle refused by construction (commands/check_callers.py on the kit, then on a copy with the Change-it's edge)
    and at run time (the peer with PEER_CHAIN on: a loop and a third hop rejected before any model call).
  - make handoff and make handoff OFF=1: the kit's commands/handoff.sh against a stub gcloud.
  - a ping-pong between two ADK desks, ended by a transfer cap: commands/agent_shapes.py --offline, as make
    agent-shapes OFFLINE=1 runs it, on its own scripted models.
The chat side needs the chat image's pins with a2a-sdk. The build runs in the 3.12 chat venv; a2a-sdk 1.1.2 and
protobuf 6.33 (the version the chat image resolves with it) are laid over it from the venv lesson 10.6's build keeps,
and culsans, a2a-sdk's queue backport for Python below 3.13, is stood in when it is missing. The peers run in that venv.
"""
import ast
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "10.7"
title = ("<title>Lesson 10.7 Hand one question to the A2A peer, and stop loops and deadlocks - a bounded hand-off, "
         "a capped peer, no way back | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
SA = lambda name: f"documind-{name}-sa@{PROJ}.iam.gserviceaccount.com"  # noqa: E731
REGION = "asia-south1"
LANE_AGENT = f"https://documind-agent-NUMBER.{REGION}.run.app"
LANE_MCP = f"https://documind-mcp-NUMBER.{REGION}.run.app"
STUB_NUMBER = "123456789012"                      # the stub gcloud's project number, shown as NUMBER

# ------------------------------------------------------------------ the kit's facts the page states
PEER_F, CHAIN_F, AGENT_F, BRAINS_F, LIMITS_F = ("services/chat/peer.py", "services/agent/chain.py", "services/agent/agent.py",
                                                "services/chat/brains.py", "services/chat/limits.py")
SHAPES_F = "commands/agent_shapes.py"
SRC = {p: (KIT / p).read_text(encoding="utf-8") for p in (
    PEER_F, CHAIN_F, AGENT_F, BRAINS_F, LIMITS_F, "services/chat/agent.py", "services/frontend/chat.py", "commands/handoff.sh",
    "commands/agent-drill.sh", "commands/check_callers.py", "commands/lesson-8.4.sh", "commands/lesson-12.8.sh", "mk/agents.mk",
    "smoke/smoke_handoff.py", "terraform/sa.tf", "shared/tenancy.py", SHAPES_F)}


def consts(text: str) -> dict:
    """Module-level NAME = literal (and A, B, C = x, y, z) assignments of a source file."""
    out = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                    out[target.id] = node.value.value
                elif isinstance(target, ast.Tuple) and isinstance(node.value, ast.Tuple):
                    for t, v in zip(target.elts, node.value.elts):
                        if isinstance(t, ast.Name) and isinstance(v, ast.Constant):
                            out[t.id] = v.value
    return out


P, CH = consts(SRC[PEER_F]), consts(SRC[CHAIN_F])
MAX_HANDOFFS, NAME, ASKER = P["HANDOFF_MAX_PER_TURN"], P["NAME"], P["ASKER"]
CHAIN_KEY, HANDOFF_KEY, MAX_HOPS = CH["CHAIN_KEY"], CH["HANDOFF_KEY"], CH["MAX_HOPS"]
assert (P["CHAIN_KEY"], P["HANDOFF_KEY"]) == (CHAIN_KEY, HANDOFF_KEY) == ("documind_chain", "documind_handoff_id")
assert (MAX_HANDOFFS, NAME, ASKER, MAX_HOPS) == (2, "documind_peer", "documind_adk", 3)
PEER_TIMEOUT = float(re.search(r'PEER_TIMEOUT_S = float\(os\.environ\.get\("PEER_TIMEOUT_S", "(\d+)"\)\)', SRC[PEER_F]).group(1))
TURN_DEADLINE = float(re.search(r'TURN_DEADLINE_S = float\(os\.environ\.get\("CHAT_TURN_DEADLINE_S", "(\d+)"\)\)', SRC[LIMITS_F]).group(1))
TURN_CALLS = int(re.search(r'MAX_MODEL_CALLS = int\(os\.environ\.get\("CHAT_MAX_MODEL_CALLS", "(\d+)"\)\)', SRC[LIMITS_F]).group(1))
TOOL_FLOOR = float(re.search(r"^TOOL_FLOOR_S = ([\d.]+)", SRC[LIMITS_F], re.M).group(1))
PEER_CAP = int(re.search(r'os\.environ\.setdefault\("ADK_MAX_LLM_CALLS", "(\d+)"\)', SRC[AGENT_F]).group(1))
UI_WAIT = int(re.search(r"headers=_headers\(CHAT_URL\), timeout=(\d+)\)", SRC["services/frontend/chat.py"]).group(1))
assert (PEER_TIMEOUT, TURN_DEADLINE, TURN_CALLS, TOOL_FLOOR, PEER_CAP, UI_WAIT) == (75.0, 100.0, 12, 1.0, 12, 120)
assert 'PEER_CHAIN = os.environ.get("PEER_CHAIN", "off")' in SRC[AGENT_F] and '"max_llm_calls": MAX_LLM_CALLS' in SRC[AGENT_F]
assert "PEER_CHAIN=${PEER_CHAIN:-off}|ADK_MAX_LLM_CALLS=12\"" in SRC["commands/lesson-8.4.sh"]
assert SRC[AGENT_F].count("log.") == 1 and "import chain" not in SRC[AGENT_F].split("def _chain_factory", 1)[0]
assert 'out["handoffs"] = ctx["handoffs"] = []' in SRC[BRAINS_F] and "root.tools.append(peer.tool())" in SRC[BRAINS_F]
assert 'return {**out, "brain": name, "session_id": req.session_id, "latency_ms": latency_ms,' in SRC["services/chat/agent.py"]
chat_row = re.search(r'logger\.info\(json\.dumps\(\{"event": "chat",(.*?)\}\)\)', SRC["services/chat/agent.py"], re.S).group(1)
assert "handoffs" not in chat_row and '"tool_calls": out.get("tool_calls", [])' in chat_row     # the chat row keeps its keys
assert '"request_chars": len(request or "")' in SRC[PEER_F] and '"peer_rosters": rosters' in SRC[PEER_F]
# step 10's "What the kit does not do yet": each point read from the kit here, so the box fails to build when the kit moves
MAKEFILES = (KIT / "Makefile").read_text(encoding="utf-8") + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
assert not any("smoke-handoff" in line for line in MAKEFILES.splitlines() if line.startswith("\t"))      # no recipe runs it
assert not re.search(r"^[a-z][^:\n]*:[^\n]*\bsmoke-handoff\b", MAKEFILES, re.M)                           # no gate lists it
assert "is the only mode" in SRC["commands/check_callers.py"] and "PEER_URL" not in SRC["commands/lesson-12.8.sh"]
assert 'return {"answer": task["text"], "state": task["state"]}' in SRC[PEER_F] and '"request": request,' in SRC[PEER_F]
assert SRC[BRAINS_F].count("peer.tool()") == 1 and SRC[BRAINS_F].index('name="documind_adk"') < SRC[BRAINS_F].index("peer.tool()")
assert "one that drops it starts a fresh chain" in SRC[CHAIN_F] and "PEER_DEADLINE" not in SRC[PEER_F] + SRC[CHAIN_F]


def deploy_flags(script: str, service: str) -> dict:
    """--concurrency and --max-instances of a script's gcloud run deploy of service."""
    text = SRC[script].replace("\\\n", " ")
    line = re.search(rf"gcloud run deploy {service}(?=\s)([^\n]*)", text).group(1)
    return {k: int(re.search(rf"--{k}=(?:\$\{{\w+:-)?(\d+)", line).group(1)) for k in ("concurrency", "max-instances")}


DRILL_VAL = int(re.search(r"VAR=ADK_MAX_LLM_CALLS; VAL=(\d+)", SRC["commands/agent-drill.sh"]).group(1))
assert DRILL_VAL == 1                            # the drill's cap, which the build's peer C runs at
CHAT_SLOTS, PEER_SLOTS = deploy_flags("commands/lesson-12.8.sh", "documind-chat"), deploy_flags("commands/lesson-8.4.sh", "documind-agent")
assert CHAT_SLOTS == {"concurrency": 20, "max-instances": 10} and PEER_SLOTS == {"concurrency": 20, "max-instances": 5}, (CHAT_SLOTS, PEER_SLOTS)
for name, n in (("documind-chat --concurrency=20 on at most 10 instances", 0), ("documind-agent 20 on at most 5", 0)):
    assert name in SRC["commands/check_callers.py"], name                                  # the script's own words agree

sys.path[:0] = [str(KIT), str(KIT / "commands")]
from lane import roster_plan  # noqa: E402
ROSTERS = {}
for t, e in roster_plan(PROJ, "acme", [])[0]:
    ROSTERS.setdefault(e.lower(), []).append(t)
ROSTERS = {e: sorted(ts) for e, ts in ROSTERS.items()}
assert (ROSTERS[SA("agent").lower()], ROSTERS[SA("ui").lower()], ROSTERS[SA("chat").lower()]) == (
    ["acme"], ["acme", "globex", "zeta"], ["acme", "globex", "zeta"])     # emails lower-cased, as tenancy keeps them
ZETA_ASKER = SA("evalzeta")                       # a person on zeta's roster alone: the Desk's zeta eval account (5.6)
assert "documind-evalzeta-sa" in SRC["commands/lesson-12.8.sh"]                            # an invoker on the chat

# acme's corpus as make ingest-corpus sends it (evals/upload.sh: a .md whose .pdf or .mp4 twin exists stays home)
CORPUS = KIT / "evals/corpus/acme"
FILES = sorted(f.name for f in CORPUS.iterdir() if f.is_file() and not f.name.endswith(".segments.json")
               and not (f.suffix == ".md" and (f.with_suffix(".pdf").exists() or f.with_suffix(".mp4").exists())))
assert 'if [[ "${f}" == *.md && ( -f "${f%.md}.pdf" || -f "${f%.md}.mp4" ) ]]; then' in (KIT / "evals/upload.sh").read_text(encoding="utf-8")

# ------------------------------------------------------------------ the questions
Q_ONE = "Which documents does the corpus hold, and how many are there?"
Q_THREE = "Ask the peer three things: which documents the corpus holds, how many there are, and which one is newest."
Q_MIX = "Which documents does the corpus hold, and after how many years of continuous service does gratuity become payable?"
THREE = ["Which documents does the corpus hold?", "How many documents does the corpus hold?",
         "Which document in the corpus is the newest?"]
PLAN = {Q_ONE: [[NAME, {"request": Q_ONE}]],
        Q_THREE: [[NAME, {"request": q}] for q in THREE],
        Q_MIX: [[NAME, {"request": "Which documents does the corpus hold, and how many are there?"}],
                ["retrieve", {"query": "gratuity payable after how many years of continuous service"}]]}

# ------------------------------------------------------------------ the offline stack
T = Path(tempfile.mkdtemp(prefix="lesson107-"))
ENV = {k: v for k, v in os.environ.items() if k not in ("ADK_MAX_LLM_CALLS", "PEER_URL", "PEER_ACCOUNT", "PEER_CHAIN",
                                                         "PEER_TIMEOUT_S", "GOOGLE_APPLICATION_CREDENTIALS")}
ENV.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_cell(body: str, cwd: Path = KIT, env: dict | None = None, ok=(0,), argv=()) -> tuple[int, str]:
    r = subprocess.run([sys.executable, "-", *argv], input=body, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode in ok and not r.stderr.strip(), (r.returncode, r.stdout[-800:], r.stderr[-1500:])
    return r.returncode, r.stdout


# ---- the peer's venv: the image's pins, made once and kept (lesson 10.6's build makes the same one)
VENV = Path(tempfile.gettempdir()) / "agents_workshop" / "venv-a2a"
VPY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not VPY.exists():
    print(f"making {VENV} with services/agent/requirements.txt (once)")
    subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    subprocess.run([str(VPY), "-m", "pip", "install", "-q", "-r", str(KIT / "services/agent/requirements.txt")], check=True)
probe = json.loads(subprocess.run([str(VPY), "-c", "import json, os, a2a, importlib.metadata as m; print(json.dumps({'site': "
                                   "os.path.dirname(os.path.dirname(a2a.__file__)), **{p: m.version(p) for p in ('google-adk', "
                                   "'a2a-sdk', 'protobuf')}}))"], capture_output=True, text=True, check=True).stdout)
assert (probe["google-adk"], probe["a2a-sdk"]) == ("2.8.0", "1.1.2") and probe["protobuf"].startswith("6."), probe
SITE = Path(probe["site"])
ADK_DEFAULT = int(re.search(r"^_DEFAULT_MAX_LLM_CALLS = (\d+)", (SITE / "google/adk/agents/run_config.py").read_text(encoding="utf-8"), re.M).group(1))
assert ADK_DEFAULT == 500

# ---- the chat side's pins: a2a-sdk 1.1.2 and protobuf 6.33 over the chat venv, and culsans stood in below 3.13
chat_reqs = (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8")
assert re.search(r"(?m)^a2a-sdk==1\.1\.2$", chat_reqs) and re.search(r"(?m)^google-adk==2\.8\.0$", chat_reqs)
OVERLAY = T / "overlay"
(OVERLAY / "google").mkdir(parents=True)
skip = shutil.ignore_patterns("__pycache__", "*.pyd", "*.so")
for name in ["a2a", "jsonrpc"] + [p.name for pat in ("a2a_sdk-*.dist-info", "json_rpc-*.dist-info", "protobuf-*.dist-info")
                                  for p in SITE.glob(pat)]:
    shutil.copytree(SITE / name, OVERLAY / name, ignore=skip)
shutil.copytree(SITE / "google" / "protobuf", OVERLAY / "google" / "protobuf", ignore=skip)
(OVERLAY / "google" / "_upb").mkdir()                # protobuf 6.33 in its pure-Python form: the venv's protobuf 7 C core hidden
(OVERLAY / "google" / "_upb" / "__init__.py").write_text(
    'raise ImportError("protobuf 7 upb hidden: this build runs protobuf 6.33 in its python implementation")\n', encoding="utf-8")
CULSANS ='''"""culsans, stood in for this build: a2a-sdk imports its queue on Python below 3.13 (a2a/utils/_async_queue_compat.py)."""
import asyncio


class AsyncQueueShutDown(Exception):
    """The queue was shut down."""


class AsyncQueue(asyncio.Queue):
    """asyncio.Queue with 3.13's shutdown()."""
    _closed = False

    def shutdown(self, immediate=False):
        """Close the queue: puts raise, gets drain what is left and then raise."""
        self._closed = True
        if immediate:
            while not self.empty():
                self.get_nowait()
                self.task_done()
        for getter in list(getattr(self, "_getters", [])):
            if not getter.done():
                getter.set_exception(AsyncQueueShutDown())

    async def put(self, item):
        """Put, unless shut down."""
        if self._closed:
            raise AsyncQueueShutDown()
        return await super().put(item)

    def put_nowait(self, item):
        """Put at once, unless shut down."""
        if self._closed:
            raise AsyncQueueShutDown()
        return super().put_nowait(item)

    async def get(self):
        """Get, or raise once shut down and empty."""
        if self._closed and self.empty():
            raise AsyncQueueShutDown()
        return await super().get()


class Queue:
    """culsans.Queue: its async side only."""

    def __init__(self, maxsize=0):
        self.async_q = AsyncQueue(maxsize)
'''
STOOD_IN_CULSANS = sys.version_info < (3, 13) and subprocess.run([sys.executable, "-c", "import culsans"], capture_output=True).returncode != 0
if STOOD_IN_CULSANS:
    (OVERLAY / "culsans.py").write_text(CULSANS, encoding="utf-8")
CHAT_ENV = {**ENV, "PYTHONPATH": str(OVERLAY), "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION": "python"}

PEER_STAND = r'''"""documind-agent, offline: the kit's agent.py over its own to_a2a, Gemini scripted, the MCP toolset stood in by two
local functions, behind a stand-in for Cloud Run's IAM check. STATE holds `mode` (answer, loop, slow, shut), which the
build sets before each turn, and events.jsonl, where each model call and each request at the door is noted."""
import asyncio, json, os, sys, time, warnings
warnings.filterwarnings("ignore")
KIT, PORT, STATE = sys.argv[1], int(sys.argv[2]), sys.argv[3]
sys.path.insert(0, os.path.join(KIT, "services", "agent"))
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_response import LlmResponse
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool import McpToolset
from google.genai import types as gt

FILES = json.loads(os.environ["PEER_FILES"])
SLOW_S = float(os.environ.get("PEER_SLOW_S", "3"))


def mode() -> str:
    """The behaviour the build asked of the peer for this turn."""
    try:
        with open(os.path.join(STATE, "mode"), encoding="utf-8") as f:
            return f.read().strip() or "answer"
    except OSError:
        return "answer"


def note(kind: str, **kw) -> None:
    """One line in STATE/events.jsonl: a model call, or a request at the door."""
    with open(os.path.join(STATE, "events.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": kind, "t": time.time(), **kw}) + "\n")


def list_documents(status: str = "indexed", tenant: str = "") -> dict:
    """What is in the caller's corpus: one row per uploaded document."""
    return {"tenant": "acme", "status": status, "documents": [{"file": f, "status": "indexed"} for f in FILES]}


def retrieve(query: str, doc_type: str = "all", top_k: int = 5, tenant: str = "") -> dict:
    """Search the caller's corpus, and answer with citations."""
    return {"answer": "Gratuity is payable after not less than five years of continuous service [1].",
            "citations": [{"source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/payment_of_gratuity_act_1972.pdf", "page": 2}]}


async def get_tools(self, readonly_context=None):
    """McpToolset, stood in: the two tools, with no MCP server to list them from."""
    return [FunctionTool(list_documents), FunctionTool(retrieve)]


McpToolset.get_tools = get_tools


async def scripted(self, llm_request, stream=False):
    """Gemini, stood in: list_documents for a question about documents, retrieve otherwise, then an answer from the
    result. In loop mode it asks for the tool again and again; in slow mode its first call takes SLOW_S."""
    note("model_call")
    parts = [p for c in llm_request.contents for p in (c.parts or [])]
    q = [p.text for p in parts if p.text][0]
    done = [p.function_response.response for p in parts if p.function_response]
    m = mode()
    if m == "slow" and not done:
        await asyncio.sleep(SLOW_S)
    if m == "loop" or not done:
        name = "list_documents" if "document" in q.lower() else "retrieve"
        yield LlmResponse(content=gt.Content(role="model", parts=[gt.Part(function_call=gt.FunctionCall(
            name=name, args={} if name == "list_documents" else {"query": q}))]))
        return
    r = done[-1]
    if "documents" in r:
        names = [d["file"] for d in r["documents"]]
        text = (f"The {r['tenant']} corpus holds {len(names)} indexed documents, among them "
                f"{', '.join(names[:3])} and {len(names) - 3} more.")
    else:
        text = ("Gratuity becomes payable after five years of continuous service. "
                "Source: payment_of_gratuity_act_1972.pdf, page 2.")
    yield LlmResponse(content=gt.Content(role="model", parts=[gt.Part(text=text)]))


Gemini.generate_content_async = scripted
import agent  # noqa: E402  - services/agent/agent.py, as the image runs it
TOKENS = {"MEMBER": "documind-ui-sa", "CHAT": "documind-chat-sa"}


class Door:
    """Cloud Run's IAM check, stood in: a bound invoker's token passes (in shut mode the chat's binding is gone). Each
    request is noted: who, what, and the A2A request's metadata and words."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        who = TOKENS.get(headers.get("authorization", "").removeprefix("Bearer "))
        body, more = b"", True
        while more:
            msg = await receive()
            body += msg.get("body", b"")
            more = msg.get("more_body", False)
        allowed = who is not None and not (mode() == "shut" and who == "documind-chat-sa")
        try:
            rpc = json.loads(body) if body else {}
        except ValueError:
            rpc = {}
        params = rpc.get("params") or {}
        message = params.get("message") or {}
        note("request", method=scope["method"], path=scope["path"], caller=who, status=200 if allowed else 403,
             rpc=rpc.get("method"), metadata=params.get("metadata"), message_keys=sorted(message),
             parts=[p.get("text") for p in message.get("parts") or []], a2a_version=headers.get("a2a-version"))
        if not allowed:
            await send({"type": "http.response.start", "status": 403, "headers": [(b"content-type", b"text/html")]})
            await send({"type": "http.response.body", "body": b"<html><title>403 Forbidden</title></html>"})
            return
        given = False

        async def replay():
            nonlocal given
            if not given:
                given = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()
        await self.app(scope, replay, send)


import uvicorn  # noqa: E402
print("ready", flush=True)
uvicorn.run(Door(agent.app), host="127.0.0.1", port=PORT, log_level="warning")
'''

CHAT_SIDE = r'''"""The chat side, offline: the kit's chat app (services/chat/agent.py) under FastAPI's TestClient, the desk's door in
front, its ADK brain with peer.py's documind_peer, a2a-sdk's client sending to the offline peer. Writes each turn's
response, what the model read back, the two log lines and the peer's events to OUT."""
import json, logging, os, sys, threading, time, warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
warnings.filterwarnings("ignore")
KIT, OUT, STATE = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path[:0] = [KIT, os.path.join(KIT, "services", "chat")]
CFG = json.loads(os.environ["CHAT_SIDE_CFG"])


class Api(BaseHTTPRequestHandler):
    """rag-api, stood in, for the turn that also searches."""

    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        data = json.dumps({"answer": "Gratuity is payable after not less than five years of continuous service [1].",
                           "answerable": True, "confidence": "high", "citations": [
                               {"chunk_id": "acme:payment_of_gratuity_act_1972#4", "page": 2, "score": 0.91,
                                "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/payment_of_gratuity_act_1972.pdf",
                                "quote": "not less than five years"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


api = ThreadingHTTPServer(("127.0.0.1", 0), Api)
threading.Thread(target=api.serve_forever, daemon=True).start()

from fastapi.testclient import TestClient
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_response import LlmResponse
from google.genai import types as gt
from shared import desk_recall, desk_rules, documind_tools, iap, tenancy
import agent                                       # services/chat/agent.py: its lifespan opens an InMemorySaver
import desk
import peer

LINES = []


class Keep(logging.Handler):
    """The chat row and the hand-off line, as Cloud Logging would receive them."""

    def emit(self, record):
        LINES.append(record.getMessage())


for name in ("documind.chat.agent", "documind.chat.peer"):
    logging.getLogger(name).addHandler(Keep())
PEOPLE, TENANT_OF, ROSTERS, PLAN = CFG["people"], CFG["tenant_of"], CFG["rosters"], CFG["plan"]


def identity(headers, bearer_audience=None):
    """The token check, stood in: the bearer names the account."""
    who = headers.get("authorization", "").removeprefix("Bearer ")
    if who not in PEOPLE:
        raise iap.IapError("the bearer token carries no verified email")
    return {"email": PEOPLE[who], "via": "iam", "aud": bearer_audience}


def tenant_for(email):
    """The roster lookup, stood in: the asker's tenant (the first roster it is on)."""
    return TENANT_OF.get((email or "").lower())


def no_firestore(*a, **k):
    """Nothing here reaches Firestore."""
    raise RuntimeError("no Firestore in this build")


iap.identity, agent.tenant_for, desk._hooks["tenant_for"] = identity, tenant_for, tenant_for
desk.settings, desk._client = (lambda tenant: {}), no_firestore
desk.CHECKED = desk_recall.OnTenants(lambda: frozenset(), desk.log, "chat")
desk.SHADOWING = desk_recall.OnTenants(lambda: frozenset(), desk.log, "chat", event="desk_shadow_tenants_unread")
tenancy.tenants_of = lambda email: ROSTERS.get((email or "").lower(), [])
documind_tools._id_token = lambda audience: "CHAT"          # the chat's own ID token, as documind-chat-sa
documind_tools.RAG_API_URL = f"http://127.0.0.1:{api.server_address[1]}"
for q in PLAN:                                               # the door's rules pass each question to chat() unmasked
    assert desk_rules.gate(q) is None and not desk_rules.mask(q)[1], q
READ = []


async def scripted(self, llm_request, stream=False):
    """Gemini on the chat side, stood in: the calls PLAN names for the question, side by side, then an answer made of
    what came back."""
    asked = [p.text for c in llm_request.contents if c.role == "user" for p in (c.parts or []) if p.text]
    done = [p.function_response for c in llm_request.contents for p in (c.parts or []) if p.function_response]
    if not done:
        parts = [gt.Part(function_call=gt.FunctionCall(name=n, args=a)) for n, a in PLAN[asked[-1]]]
        yield LlmResponse(content=gt.Content(role="model", parts=parts))
        return
    READ.append([{"name": fr.name, "response": fr.response} for fr in done])
    said = []
    for fr in done:
        r = fr.response or {}
        cites = r.get("citations") or []
        said.append(r.get("answer") or r.get("error") or (f"The search says: {cites[0]['quote']} [1]." if cites else ""))
    yield LlmResponse(content=gt.Content(role="model", parts=[gt.Part(text=" ".join(s for s in said if s))]))


Gemini.generate_content_async = scripted
EVENTS = os.path.join(STATE, "events.jsonl")


def events_now() -> int:
    """How many lines the peer has noted so far."""
    try:
        with open(EVENTS, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def events_since(n: int) -> list:
    """The peer's lines after the first n."""
    try:
        with open(EVENTS, encoding="utf-8") as f:
            return [json.loads(line) for line in f.readlines()[n:]]
    except OSError:
        return []


out = {"turns": {}}
with TestClient(agent.app) as client:
    for t in CFG["turns"]:
        with open(os.path.join(STATE, "mode"), "w", encoding="utf-8") as f:
            f.write(t["mode"])
        saved = (peer.PEER_ACCOUNT, peer.PEER_TIMEOUT_S)
        peer.PEER_ACCOUNT = t.get("peer_account") or peer.PEER_ACCOUNT
        peer.PEER_TIMEOUT_S = t.get("timeout_s") or peer.PEER_TIMEOUT_S
        n_lines, n_read, n_events, t0 = len(LINES), len(READ), events_now(), time.monotonic()
        r = client.post("/v1/chat", headers={"Authorization": f"Bearer {t['token']}"},
                        json={"question": t["question"], "session_id": t["session"], "brain": "adk"})
        wall = round(time.monotonic() - t0, 2)
        peer.PEER_ACCOUNT, peer.PEER_TIMEOUT_S = saved
        time.sleep(t.get("settle", 0.3))             # a cut task runs on at the peer: its calls are this turn's
        out["turns"][t["name"]] = {"status": r.status_code, "body": r.json(), "read": READ[n_read:],
                                   "lines": [json.loads(x) for x in LINES[n_lines:]], "events": events_since(n_events),
                                   "wall_s": wall}
    out["health"] = client.get("/health").json()
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f)
'''

STATE_DIRS = {k: T / f"peer-{k}" for k in ("A", "B", "C")}
for d in STATE_DIRS.values():
    d.mkdir()
PORTS = {k: free_port() for k in STATE_DIRS}
PEER_URLS = {k: f"http://127.0.0.1:{p}" for k, p in PORTS.items()}
(T / "peer_stand.py").write_text(PEER_STAND, encoding="utf-8")
(T / "chat_side.py").write_text(CHAT_SIDE, encoding="utf-8")
PEER_ENV = {**ENV, "MCP_URL": LANE_MCP, "MCP_AUTH": "none", "GOOGLE_CLOUD_PROJECT": PROJ, "GOOGLE_GENAI_USE_VERTEXAI": "1",
            "GOOGLE_CLOUD_LOCATION": "global", "AGENT_MODEL": "gemini-3.6-flash", "PEER_FILES": json.dumps(FILES)}
PEERS = {"A": {"PEER_CHAIN": "off"}, "B": {"PEER_CHAIN": "on"}, "C": {"PEER_CHAIN": "off", "ADK_MAX_LLM_CALLS": str(DRILL_VAL)}}
SLOW_BUDGET, SLOW_S = 2.0, 3.0                   # the slow peer's first model call outlasts the build's hand-off budget
PEER_ENV["PEER_SLOW_S"] = f"{SLOW_S:g}"


def wait_up(url: str, log: Path) -> dict:
    for _ in range(600):
        try:
            with urllib.request.urlopen(urllib.request.Request(url + "/health", headers={"Authorization": "Bearer MEMBER"}), timeout=2) as r:
                return json.loads(r.read())
        except Exception:                          # noqa: BLE001 - not up yet
            time.sleep(0.2)
    raise SystemExit(f"{url} did not start: " + log.read_text(encoding="utf-8", errors="replace")[-1500:])


def a2a(url: str, text: str, metadata: dict | None = None, token: str = "MEMBER") -> dict:
    """One A2A 1.0 SendMessage to a peer, as a2a-sdk's client sends it; the JSON-RPC result."""
    params = {"message": {"messageId": str(uuid.uuid4()), "role": "ROLE_USER", "parts": [{"text": text}]}}
    if metadata is not None:
        params["metadata"] = metadata
    body = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "SendMessage", "params": params}
    req = urllib.request.Request(url + "/", data=json.dumps(body).encode(), headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json", "A2A-Version": "1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.loads(r.read())
    assert "error" not in j, j
    return j["result"]


def events(k: str) -> list:
    path = STATE_DIRS[k] / "events.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def set_mode(k: str, m: str) -> None:
    (STATE_DIRS[k] / "mode").write_text(m, encoding="utf-8")


CHAIN_CELL_PY = '''import json, os, urllib.request, uuid, warnings
warnings.filterwarnings("ignore", category=UserWarning)
H = {"Authorization": "Bearer " + os.environ["AGENT_TOKEN"], "Content-Type": "application/json"}
health = json.load(urllib.request.urlopen(urllib.request.Request(os.environ["AGENT"] + "/health", headers=H)))
print(f"the peer's /health: peer_chain {health.get('peer_chain')}, max_llm_calls {health.get('max_llm_calls')}")
if health.get("peer_chain") != "on":        # None: an image from before this lesson's kit, which names no switch at all
    raise SystemExit("PEER_CHAIN is not on at this peer: deploy it with PEER_CHAIN=on first, or these two tasks reach the model")
def ask(chain):
    """One task for the peer, its request carrying this delegation chain; the task that comes back."""
    body = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "message/send", "params": {
        "message": {"role": "user", "kind": "message", "messageId": str(uuid.uuid4()),
                    "parts": [{"kind": "text", "text": "Which documents does the corpus hold?"}]},
        "metadata": {"documind_chain": chain, "documind_handoff_id": "lesson107-" + str(len(chain))}}}
    req = urllib.request.Request(os.environ["AGENT"] + "/", data=json.dumps(body).encode(), headers=H)
    return json.load(urllib.request.urlopen(req, timeout=120))["result"]
for chain in (["partner_agent", "documind_peer"], ["documind_adk", "partner_agent", "vendor_agent"]):
    task = ask(chain)
    said = " ".join(p.get("text", "") for p in task["status"].get("message", {}).get("parts", []))
    print(f"{' -> '.join(chain)}: {task['status']['state']}, history {[m['role'] for m in task.get('history', [])]}")
    print(f"  {said}")'''
procs, logs = {}, {}
TURNS = []
WHO = {"acme": ("MEMBER", None), "zeta": ("ZETA", None), "uisa": ("MEMBER", SA("ui"))}
for who, (token, account) in WHO.items():
    for sends, q in (("one", Q_ONE), ("three", Q_THREE)):
        for mode in ("answer", "loop", "slow", "shut"):
            TURNS.append({"name": f"{who}|{sends}|{mode}", "token": token, "question": q, "mode": mode,
                          "session": f"lesson107-{who}-{sends}-{mode}", "peer_account": account,
                          **({"timeout_s": SLOW_BUDGET, "settle": 3.5} if mode == "slow" else {})})
TURNS.append({"name": "mixed", "token": "MEMBER", "question": Q_MIX, "mode": "answer", "session": "lesson107-mixed"})
CFG = {"people": {"MEMBER": SA("ui"), "ZETA": ZETA_ASKER}, "tenant_of": {SA("ui").lower(): "acme", ZETA_ASKER.lower(): "zeta"},
       "rosters": {**ROSTERS, ZETA_ASKER.lower(): ["zeta"]}, "plan": PLAN, "turns": TURNS}
CHAT_OUT = T / "chat_out.json"
try:
    for k, extra in PEERS.items():
        logs[k] = open(T / f"peer-{k}.log", "w", encoding="utf-8")
        procs[k] = subprocess.Popen([str(VPY), str(T / "peer_stand.py"), str(KIT), str(PORTS[k]), str(STATE_DIRS[k])], cwd=str(KIT),
                                    env={**PEER_ENV, **extra, "SELF_URL": PEER_URLS[k]}, stdout=logs[k], stderr=subprocess.STDOUT)
    HEALTH = {k: wait_up(PEER_URLS[k], T / f"peer-{k}.log") for k in PEERS}
    assert (HEALTH["A"]["max_llm_calls"], HEALTH["A"]["peer_chain"], HEALTH["B"]["peer_chain"], HEALTH["C"]["max_llm_calls"]) == (PEER_CAP, "off", "on", 1), HEALTH

    # ---- the hand-off end to end: the kit's chat app, its ADK brain, peer.py and a2a-sdk's client, the kit's peer A
    r = subprocess.run([sys.executable, str(T / "chat_side.py"), str(KIT), str(CHAT_OUT), str(STATE_DIRS["A"])], cwd=str(KIT),
                       env={**CHAT_ENV, "PEER_URL": PEER_URLS["A"], "PEER_ACCOUNT": SA("agent"), "CHECKPOINT_DSN": "memory",
                            "GOOGLE_CLOUD_PROJECT": PROJ, "GOOGLE_GENAI_USE_VERTEXAI": "1", "GOOGLE_CLOUD_LOCATION": "global",
                            "CHAT_SIDE_CFG": json.dumps(CFG)}, capture_output=True, text=True, encoding="utf-8", timeout=900)
    (T / "chat_side.log").write_text(r.stdout + r.stderr, encoding="utf-8")
    assert r.returncode == 0 and CHAT_OUT.exists(), (r.stdout[-1500:], r.stderr[-3000:])
    CHAT = json.loads(CHAT_OUT.read_text(encoding="utf-8"))

    # ---- the peer's cap: a scripted loop, as the chat would send it, on peer A
    set_mode("A", "loop")
    n0 = len(events("A"))
    LOOP = a2a(PEER_URLS["A"], THREE[0], {CHAIN_KEY: [ASKER], HANDOFF_KEY: "build-loop"})
    LOOP_CALLS = sum(1 for e in events("A")[n0:] if e["kind"] == "model_call")
    set_mode("A", "answer")

    # ---- the chain at run time: the same requests to peer A (PEER_CHAIN off) and peer B (on)
    CHAINS = {"none": None, "chat": [ASKER], "partner": [ASKER, "partner_agent"], "loop": ["partner_agent", NAME],
              "hops": [ASKER, "partner_agent", "vendor_agent"]}
    CHAIN_RUNS = {}
    for k in ("A", "B"):
        set_mode(k, "answer")
        for c, chain in CHAINS.items():
            n0 = len(events(k))
            meta = None if chain is None else {CHAIN_KEY: chain, HANDOFF_KEY: f"build-{c}"}
            res = a2a(PEER_URLS[k], THREE[0], meta)
            task = res["task"]
            CHAIN_RUNS[(k, c)] = {"state": task["status"]["state"], "calls": sum(1 for e in events(k)[n0:] if e["kind"] == "model_call"),
                                  "words": " ".join(p.get("text", "") for p in (task["status"].get("message") or {}).get("parts", [])),
                                  "answer": " ".join(p.get("text", "") for a in task.get("artifacts", []) for p in a.get("parts", [])),
                                  "history": [m["role"] for m in task.get("history", [])]}
    time.sleep(0.5)

    # ---- the learner's chain cell (message/send, as smoke_agent sends it) against peer B, and its /health
    nB = len(events("B"))
    _, CHAIN_CELL_OUT = run_cell(CHAIN_CELL_PY, env={"AGENT": PEER_URLS["B"], "AGENT_TOKEN": "MEMBER"})
    CHAIN_CELL_CALLS = sum(1 for e in events("B")[nB:] if e["kind"] == "model_call")
    time.sleep(0.5)
    REFUSED_LINES = [json.loads(ln) for ln in (T / "peer-B.log").read_text(encoding="utf-8", errors="replace").splitlines()
                     if ln.startswith('{"event": "a2a_refused"')]

    # ---- make agent-drill's verdicts, from the drill's own Python: peer C at a cap of 1, peer A at its default
    drill = SRC["commands/agent-drill.sh"]
    DRILL_PY = drill.split("\"$PY\" - \"$@\" <<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
    assert DRILL_PY.startswith("import os, sys\nsys.path.insert(0, \"smoke\")") and "if want == \"failed\":" in DRILL_PY
    DRILL = {}
    for k, argv in (("C", ("cap",)), ("C", ("task", "failed")), ("A", ("cap",)), ("A", ("task", "completed"))):
        n0 = len(events(k))
        code, said = run_cell(DRILL_PY, env={"DOCUMIND_AGENT_URL": PEER_URLS[k], "DOCUMIND_AGENT_TOKEN": "MEMBER"}, argv=argv)
        DRILL[(k, argv[0])] = (code, said, sum(1 for e in events(k)[n0:] if e["kind"] == "model_call"))
    with urllib.request.urlopen(urllib.request.Request(PEER_URLS["A"] + "/health", headers={"Authorization": "Bearer MEMBER"}), timeout=10) as resp:
        HEALTH_RAW = resp.read().decode().replace(PEER_URLS["A"], LANE_AGENT)
finally:
    for p in procs.values():
        p.terminate()
        try:
            p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            p.kill()
    for f in logs.values():
        f.close()

# ------------------------------------------------------------------ make handoff, on and off: the kit's script, a stub gcloud
GCLOUD_STUB = r'''import json, os, sys
home, args = os.environ["HANDOFF_STUB_HOME"], sys.argv[1:]
path = os.path.join(home, "services.json")
with open(path, encoding="utf-8") as f:
    world = json.load(f)


def flag(name):
    """The value of --name=value among the arguments."""
    return next((a.split("=", 1)[1] for a in args if a.startswith(name + "=")), None)


named = [a for a in args[3:] if not a.startswith("--")]
svc = world["services"].get(named[0]) if len(named) == 1 else None
if args[:3] == ["projects", "describe", world["project"]]:
    print(world["number"])
elif args[:3] == ["run", "services", "describe"] and svc is not None and flag("--format") == "json":
    print(json.dumps({"status": {"traffic": svc["traffic"]}}))
elif args[:3] == ["run", "services", "describe"] and svc is not None:
    print(svc["account"])
elif args[:3] == ["run", "services", "get-iam-policy"] and svc is not None:
    print(json.dumps({"bindings": [{"role": "roles/run.invoker", "members": svc["invokers"]}]}))
elif args[:3] == ["run", "services", "update"] and named == ["documind-chat"]:
    for kv in filter(None, (flag("--update-env-vars") or "").split(",")):
        svc["env"].update([kv.split("=", 1)])
    for key in (flag("--remove-env-vars") or "").split(","):
        svc["env"].pop(key, None)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(world, f)
else:
    sys.stderr.write("stub gcloud: unexpected call: gcloud " + " ".join(args) + "\n")
    sys.exit(99)
'''
BASH = shutil.which("bash")
assert BASH, "bash is not on PATH: make handoff's output is computed by running commands/handoff.sh"


def run_handoff(off: bool) -> tuple[str, dict]:
    """commands/handoff.sh, as make handoff runs it, against a stub gcloud that keeps both services in a file."""
    home = T / ("stub-off" if off else "stub-on")
    (home / "bin").mkdir(parents=True)
    (home / "stub.py").write_text(GCLOUD_STUB, encoding="utf-8")
    python = Path(sys.executable).as_posix()
    for name, body in (("gcloud", f'exec "{python}" "{(home / "stub.py").as_posix()}" "$@"'), ("py", f'exec "{python}" "$@"')):
        with open(home / "bin" / name, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"#!/bin/sh\n{body}\n")
        (home / "bin" / name).chmod(0o755)
    latest = [{"latestRevision": True, "percent": 100}]
    chat_env = {"PEER_URL": f"https://documind-agent-{STUB_NUMBER}.{REGION}.run.app", "PEER_ACCOUNT": SA("agent")} if off else {}
    world = {"project": PROJ, "region": REGION, "number": STUB_NUMBER, "services": {
        "documind-chat": {"account": SA("chat"), "traffic": latest, "invokers": [], "env": chat_env},
        "documind-agent": {"account": SA("agent"), "traffic": latest, "env": {},
                           "invokers": [f"serviceAccount:{SA('ui')}", f"serviceAccount:{SA('chat')}"]}}}
    (home / "services.json").write_text(json.dumps(world), encoding="utf-8")
    env = {**ENV, "PATH": str(home / "bin") + os.pathsep + ENV.get("PATH", ""), "HANDOFF_STUB_HOME": str(home),
           "PROJECT": PROJ, "REGION": REGION, "PY": str(home / "bin" / "py"), "OFF": "1" if off else ""}
    r = subprocess.run([BASH, "commands/handoff.sh"], cwd=str(KIT), env=env, capture_output=True, text=True,
                       encoding="utf-8", timeout=180)
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout, r.stderr)
    return r.stdout.replace(STUB_NUMBER, "NUMBER"), json.loads((home / "services.json").read_text(encoding="utf-8"))["services"]["documind-chat"]["env"]


HANDOFF_ON, ENV_ON = run_handoff(False)
HANDOFF_OFF, ENV_OFF = run_handoff(True)
assert ENV_ON == {"PEER_URL": f"https://documind-agent-{STUB_NUMBER}.{REGION}.run.app", "PEER_ACCOUNT": SA("agent")} and ENV_OFF == {}, (ENV_ON, ENV_OFF)
assert HANDOFF_ON.startswith(f">> documind-chat: PEER_URL={LANE_AGENT}\n") and "the hand-off is off" in HANDOFF_OFF, (HANDOFF_ON, HANDOFF_OFF)

# ------------------------------------------------------------------ the caller graph: the kit, then copies with one binding added
CC_RECIPE = re.search(r"^check-callers:\n\t(.+)$", SRC["mk/agents.mk"], re.M).group(1)
assert CC_RECIPE == "$(PY) commands/check_callers.py $(if $(GRAPH),--graph,)", CC_RECIPE
CC_ECHO = "python commands/check_callers.py --graph"        # make prints the recipe line it runs ($(PY) is python)


def check_callers(kit: Path = KIT) -> tuple[int, str]:
    """commands/check_callers.py --graph on a kit (or a copy of its sa.tf and deploy scripts)."""
    r = subprocess.run([sys.executable, str(KIT / "commands/check_callers.py"), "--graph", "--kit", str(kit)], cwd=str(KIT),
                       capture_output=True, text=True, encoding="utf-8", env=ENV)
    assert r.returncode in (0, 1) and not r.stderr.strip(), (r.returncode, r.stdout, r.stderr)
    return r.returncode, r.stdout


def with_binding(script: str, old: str, new: str) -> tuple[tuple[str, str], int, str]:
    """A copy of sa.tf and the deploy scripts with one line changed as a sed would change it; check_callers on it."""
    copy = T / f"kit-{script}-{len(new)}"
    (copy / "terraform").mkdir(parents=True)
    (copy / "commands").mkdir()
    shutil.copy(KIT / "terraform/sa.tf", copy / "terraform/sa.tf")
    for s in (KIT / "commands").glob("*.sh"):
        shutil.copy(s, copy / "commands" / s.name)
    before = (copy / "commands" / script).read_text(encoding="utf-8")
    after = re.sub("^" + re.escape(old), new, before, flags=re.M)
    changed = [(a, b) for a, b in zip(before.splitlines(), after.splitlines()) if a != b]
    assert len(changed) == 1, (script, changed)
    with open(copy / "commands" / script, "w", encoding="utf-8", newline="\n") as f:
        f.write(after)
    return (changed[0], *check_callers(copy))


CC_CODE, CC_OUT = check_callers()
assert CC_CODE == 0 and "\nacyclic: documind-ui, documind-gchat, documind-chat, documind-agent, documind-mcp, documind-api\n" in CC_OUT, CC_OUT
SED_FROM, SED_TO = "for who in documind-ui-sa documind-outsider-sa", "for who in documind-ui-sa documind-agent-sa documind-outsider-sa"
GRAPH_CASES = {
    "kit": ((None, None), CC_CODE, CC_OUT),
    "back": with_binding("lesson-12.8.sh", SED_FROM, SED_TO),
    "self": with_binding("lesson-7.2.sh", "for who in documind-ui-sa documind-agent-sa documind-outsider-sa; do",
                         "for who in documind-ui-sa documind-agent-sa documind-mcp-sa documind-outsider-sa; do"),
    "outsider": with_binding("lesson-8.4.sh", "for sa in documind-ui-sa documind-chat-sa; do",
                             "for sa in documind-ui-sa documind-chat-sa documind-outsider-sa; do"),
}
assert GRAPH_CASES["back"][1] == 1 and "\ncycle: documind-chat -> documind-agent -> documind-chat\n" in GRAPH_CASES["back"][2]
assert GRAPH_CASES["self"][1] == 1 and "\ncycle: documind-mcp -> documind-mcp\n" in GRAPH_CASES["self"][2]
assert GRAPH_CASES["outsider"][1] == 0 and "\nacyclic: " in GRAPH_CASES["outsider"][2]

if os.environ.get("HARNESS_DUMP"):
    dump = {"chat": CHAT, "health": HEALTH, "loop": LOOP, "loop_calls": LOOP_CALLS, "chain_runs": {f"{k}|{c}": v for (k, c), v in CHAIN_RUNS.items()},
            "chain_cell": CHAIN_CELL_OUT, "chain_cell_calls": CHAIN_CELL_CALLS, "refused_lines": REFUSED_LINES,
            "drill": {f"{k}|{a}": v for (k, a), v in DRILL.items()}, "culsans": STOOD_IN_CULSANS, "files": FILES}
    Path(os.environ["HARNESS_DUMP"]).write_text(json.dumps(dump, indent=1), encoding="utf-8")
    print("dumped to", os.environ["HARNESS_DUMP"])
    sys.exit(0)
shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------ what the build ran, checked: the proof, offline
TURN = CHAT["turns"]


def records(turn: dict) -> list:
    return sorted(turn["body"].get("handoffs", []), key=lambda h: h["n"])


def door(turn: dict) -> list:
    return [e for e in turn["events"] if e["kind"] == "request"]


def peer_calls(turn: dict) -> int:
    return sum(1 for e in turn["events"] if e["kind"] == "model_call")


def lane(text: str) -> str:
    """A build-time value as it reads on a lane: the peer's address, and the project id in its placeholder's case."""
    for url in PEER_URLS.values():
        text = text.replace(url, LANE_AGENT)
    return text.replace(PROJ.lower(), PROJ)


ONE, LOOP_T, SLOW_T, SHUT_T = (TURN[f"acme|one|{m}"] for m in ("answer", "loop", "slow", "shut"))
ZETA_T, UISA_T, THREE_T, MIX_T = TURN["zeta|one|answer"], TURN["uisa|one|answer"], TURN["acme|three|answer"], TURN["mixed"]
POSTS = [e for e in door(ONE) if e["method"] == "POST"]
HLINE = next(x for x in ONE["lines"] if x["event"] == "handoff")
CROW = next(x for x in ONE["lines"] if x["event"] == "chat")
assert ONE["status"] == 200 and ONE["body"]["tool_calls"] == [NAME] and ONE["body"]["refusals"] == []
assert [(h["outcome"], h["state"], h["budget_s"]) for h in records(ONE)] == [("answered", "completed", PEER_TIMEOUT)]
assert len(POSTS) == 1 and POSTS[0]["rpc"] == "SendMessage" and POSTS[0]["parts"] == [Q_ONE]
assert POSTS[0]["message_keys"] == ["messageId", "parts", "role"] and set(POSTS[0]["metadata"]) == {CHAIN_KEY, HANDOFF_KEY}
assert POSTS[0]["metadata"][CHAIN_KEY] == [ASKER] and re.fullmatch(r"[0-9a-f]{32}", POSTS[0]["metadata"][HANDOFF_KEY])
assert POSTS[0]["metadata"][HANDOFF_KEY] == records(ONE)[0]["handoff_id"] == HLINE["handoff_id"]   # one id joins both sides
assert {e["caller"] for e in door(ONE)} == {"documind-chat-sa"} and [e["path"] for e in door(ONE)] == ["/.well-known/agent-card.json", "/"]
assert peer_calls(ONE) == 2 and HLINE["request_chars"] == len(Q_ONE) and Q_ONE not in json.dumps(HLINE) and HLINE["peer_rosters"] == 1
assert "handoffs" not in CROW and CROW["tool_calls"] == [NAME] and CROW["brain"] == "adk"
assert door(ZETA_T) == [] and [h["outcome"] for h in records(ZETA_T)] == ["refused"] and "(a confused deputy)" in records(ZETA_T)[0]["reason"]
assert next(x for x in UISA_T["lines"] if x["event"] == "handoff")["peer_rosters"] == 3 and door(UISA_T) == []
assert [h["outcome"] for h in records(THREE_T)] == ["answered", "answered", "refused"] and THREE_T["body"]["refusals"] == [NAME]
assert "(HANDOFF_MAX_PER_TURN)" in records(THREE_T)[2]["reason"] and len([e for e in door(THREE_T) if e["method"] == "POST"]) == MAX_HANDOFFS
assert MIX_T["body"]["tool_calls"] == [NAME, "retrieve"] and len(MIX_T["body"]["citations"]) == 1
assert records(LOOP_T)[0]["outcome"] == "failed" and peer_calls(LOOP_T) == PEER_CAP
assert records(SLOW_T)[0]["outcome"] == "timed_out" and records(SLOW_T)[0]["budget_s"] == SLOW_BUDGET and SLOW_T["body"]["limits"]["tool_timeouts"] == [NAME]
assert records(SHUT_T)[0]["outcome"] == "error" and [e["status"] for e in door(SHUT_T)] == [403]
for key, t in TURN.items():
    assert t["status"] == 200 and t["body"]["limits"]["stopped_by"] is None, key
    if key.startswith(("zeta|", "uisa|")):
        assert door(t) == [] and {h["outcome"] for h in records(t)} == {"refused"}, key       # nothing was sent
LOOP_TASK = LOOP["task"]
LOOP_WORDS = LOOP_TASK["status"]["message"]["parts"][0]["text"]
assert (LOOP_TASK["status"]["state"], LOOP_WORDS, LOOP_CALLS) == ("TASK_STATE_FAILED", f"Max number of llm calls limit of `{PEER_CAP}` exceeded", PEER_CAP)
for c in CHAINS:
    assert (CHAIN_RUNS[("A", c)]["state"], CHAIN_RUNS[("A", c)]["calls"]) == ("TASK_STATE_COMPLETED", 2), c          # off: all run
    want = ("TASK_STATE_REJECTED", 0) if c in ("loop", "hops") else ("TASK_STATE_COMPLETED", 2)
    assert (CHAIN_RUNS[("B", c)]["state"], CHAIN_RUNS[("B", c)]["calls"]) == want, (c, CHAIN_RUNS[("B", c)])
    if c in ("loop", "hops"):
        assert CHAIN_RUNS[("B", c)]["history"] == ["ROLE_USER"] and CHAIN_RUNS[("B", c)]["words"].endswith("refused before any model call")
assert CHAIN_CELL_OUT.count(": rejected, history ['user']") == 2 and CHAIN_CELL_CALLS == 0, CHAIN_CELL_OUT
assert [(x["reason"], x["chain_length"]) for x in REFUSED_LINES] == [("loop", 2), ("hops", 3), ("loop", 2), ("hops", 3)]
assert all(set(x) == {"event", "reason", "chain_length", "handoff_id", "task_id"} for x in REFUSED_LINES)
assert DRILL[("C", "cap")][:2] == (0, "1") and DRILL[("A", "cap")][:2] == (0, str(PEER_CAP))
assert DRILL[("C", "task")][0] == 0 and DRILL[("C", "task")][1].startswith("  [PASS] task failed  status=200 state=failed  'Max number of llm calls limit of `1` exceeded'") and DRILL[("C", "task")][2] == 1
assert DRILL[("A", "task")][0] == 0 and DRILL[("A", "task")][1].startswith("  [PASS] task completed  status=200 state=completed") and DRILL[("A", "task")][2] == 2
HEALTH_A = json.loads(HEALTH_RAW)
assert (HEALTH_A["max_llm_calls"], HEALTH_A["peer_chain"], HEALTH_A["self_url"], HEALTH_A["mcp_url"]) == (PEER_CAP, "off", LANE_AGENT, LANE_MCP)

import check_callers  # noqa: E402  - commands/check_callers.py: the standard library alone
G = check_callers.read_graph(KIT)
N_SERVICES, N_EDGES = len(G.services), sum(len(v) for v in G.edges.values())
assert (N_SERVICES, N_EDGES) == (6, 9) and check_callers.cycle(G) is None

# ------------------------------------------------------------------ verbatim excerpts
EXCERPTS = {
    "describe": (f"{PEER_F} - the name, the metadata's keys, and the description the chat's model reads",
                 block(PEER_F, 'NAME = "documind_peer"', n=11)),
    "gate": (f"{PEER_F} - the gate, and how long a hand-off may wait",
             block(PEER_F, "def gate(tenant: str, peer_tenants: list, sent: int) -> str | None:", end="async def _blocking(fn, *args):")),
    "handoff": (f"{PEER_F} - one hand-off: counted, gated, sent, and every failure returned as data",
                block(PEER_F, "async def documind_peer(request: str) -> dict:", end="    finally:")),
    "send": (f"{PEER_F} - what crosses: one message, with the chat's own token, the chain and the hand-off id",
             block(PEER_F, '    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}, timeout=wait_s) as http:', n=5)),
    "brains_tool": (f"{BRAINS_F} - the ADK brain's tool list gains the hand-off, and no other brain's does",
                    block(BRAINS_F, "        if peer.PEER_URL:                   # the A2A hand-off", n=2)),
    "brains_turn": (f"{BRAINS_F} - each turn's record, returned in the response",
                    block(BRAINS_F, "        if peer.PEER_URL:                   # this turn's hand-offs", n=2)),
    "cap": (f"{AGENT_F} - the peer's own cap, and its /health",
            block(AGENT_F, "# The peer's own cap (workshop lesson 10.7", n=5) + "\n\n\n" + block(AGENT_F, "async def health(request: Request) -> JSONResponse:", n=4)),
    "drill": ("commands/agent-drill.sh - the cap put back from a trap, so a failed drill restores it too",
              block("commands/agent-drill.sh", 'BEFORE=$(env_value "$VAR")', n=8)),
    "logline": (f"{PEER_F} - one log line per hand-off: the question's length, never its words",
                block(PEER_F, "    finally:", n=9)),
    "callers": ("terraform/sa.tf - the caller graph: each service, who may invoke it, and the script that binds them",
                block("terraform/sa.tf", "#   documind-api    <- documind-ui-sa", n=6)),
    "graph": ("commands/check_callers.py - an edge wherever a service's account may invoke another service",
              block("commands/check_callers.py", "def read_graph(kit: Path = KIT) -> Graph:")),
    "cycle": ("commands/check_callers.py - a walk that stops at the first edge back onto its own path",
              block("commands/check_callers.py", "def cycle(g: Graph) -> list[str] | None:")),
    "loopline": ("commands/lesson-12.8.sh - who may invoke documind-chat: the line the Change-it edits",
                 block("commands/lesson-12.8.sh", "for who in documind-ui-sa documind-outsider-sa", n=3)),
    "refusal": (f"{CHAIN_F} - the rule: a loop, or a third hop",
                block(CHAIN_F, 'CHAIN_KEY = "documind_chain"', n=3) + "\n\n\n" + block(CHAIN_F, "def chain_of(metadata: dict) -> list[str]:", end="class ChainExecutor(A2aAgentExecutor):")),
    "executor": (f"{CHAIN_F} - refused before the runner starts: the Task first, then rejected",
                 block(CHAIN_F, "    async def execute(self, context, event_queue) -> None:", end="def factory(runner) -> ChainExecutor:")),
    "factory": (f"{AGENT_F} - off unless PEER_CHAIN=on: chain.py is imported only then",
                block(AGENT_F, "def _chain_factory():", n=13)),
    "transfer_cap": (f"{SHAPES_F} - TransferCap: the agents a turn starts, counted in a temp: key, and the start after the "
                     "third transfer answered in that agent's place",
                     block(SHAPES_F, "MAX_TRANSFERS = 3 ", n=3) + "\n\n\n" + block(SHAPES_F, "def transfer_cap(", end="def offered(")),
    "shape": (f"{SHAPES_F} - swarm_adk(): two desks that may transfer to each other and to their root, the cap on the App",
              block(SHAPES_F, "    desks = [LlmAgent(", n=7)),
}
assert "ctx.setdefault(\"handoffs\", [])" in EXCERPTS["handoff"][1] and "return limits._payload_error(NAME, wait_s)" in EXCERPTS["handoff"][1]
assert "metadata={CHAIN_KEY: [ASKER], HANDOFF_KEY: handoff_id}" in EXCERPTS["send"][1]
assert '"request_chars": len(request or "")' in EXCERPTS["logline"][1] and EXCERPTS["callers"][1].count("documind-") >= 6
assert "trap restore EXIT" in EXCERPTS["drill"][1] and "app = to_a2a(agent, host=_host, port=_port, protocol=_protocol, agent_executor_factory=_chain_factory())" in EXCERPTS["factory"][1]
assert "await updater.reject(" in EXCERPTS["executor"][1] and 'return "loop", f"delegation loop:' in EXCERPTS["refusal"][1]
assert 'STARTS = "temp:agent_starts"' in EXCERPTS["transfer_cap"][1] and "if starts - 1 > max_transfers:" in EXCERPTS["transfer_cap"][1]
assert EXCERPTS["transfer_cap"][1].rstrip().endswith("return TransferCap()")
assert "disallow_transfer_to_peers=not peers" in EXCERPTS["shape"][1] and "plugins=[transfer_cap()]" in EXCERPTS["shape"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the cells
GATE_PY = """import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
import limits, peer
print(f"HANDOFF_MAX_PER_TURN {peer.HANDOFF_MAX_PER_TURN}, PEER_TIMEOUT_S {peer.PEER_TIMEOUT_S:g} s, the turn's deadline {limits.TURN_DEADLINE_S:g} s")
for who, tenant, rosters, sent in (("an acme member", "acme", ["acme"], 0),
                                   ("an acme member, 2 already sent this turn", "acme", ["acme"], 2),
                                   ("a zeta member", "zeta", ["acme"], 0),
                                   ("an acme member, the peer's account on 3 rosters", "acme", ["acme", "globex", "zeta"], 0)):
    why = peer.gate(tenant, rosters, sent)
    print(f"{who}: " + ("sent" if why is None else "refused, " + why))
for left in (100, 30, 0.5):
    meter = limits.Meter()
    meter.started -= meter.deadline_s - left            # a turn with this much time left
    print(f"{left:g} s left in the turn: the hand-off waits at most {peer.budget_s(meter):.0f} s")"""

DEPUTY_PY = """import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
body = {"question": "Ask DocuMind's A2A peer which documents the corpus holds, and how many there are.",
        "session_id": "lesson107-deputy", "brain": "adk"}
req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", data=json.dumps(body).encode(),
                             headers={"Authorization": "Bearer " + os.environ["CHAT_TOKEN"], "Content-Type": "application/json"})
r = json.load(urllib.request.urlopen(req, timeout=180))
print("tool_calls:", r.get("tool_calls"), " refusals:", r.get("refusals"))
for h in r.get("handoffs", []):
    print(f"hand-off {h['n']}: {h['outcome']}, budget {h['budget_s']}, the peer's task {h['state']}")
    print(f"  {h['reason']}")
print("answer:", str(r.get("answer"))[:160])"""

LOGS_PY = """import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
def rows(flt):
    \"\"\"documind-chat's log lines since SINCE107 that match flt, oldest first, as their jsonPayload.\"\"\"
    f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND {flt} '
         f'AND timestamp>="{os.environ["SINCE107"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc",
                          "--limit", "50", "--format", "json"], capture_output=True, text=True, check=True).stdout
    return [e["jsonPayload"] for e in json.loads(out or "[]")]
print("the hand-off lines:")
for j in rows('jsonPayload.event="handoff"'):
    print(f"  {j['outcome']:9} n {j['n']}  tenant {j['tenant']}  rosters {j['peer_rosters']}  {j['seconds']} s of "
          f"{j['budget_s']}  the question: {j['request_chars']} characters  id {(j['handoff_id'] or '')[:8]}")
print("the ADK brain's chat rows:")
for j in rows('jsonPayload.event="chat" AND jsonPayload.brain="adk"'):
    print(f"  tools {j['tool_calls']}  refusals {j['refusals']}  model calls {j['model_calls']}  "
          f"handoffs key: {'handoffs' in j}")"""

QD = "Ask DocuMind's A2A peer which documents the corpus holds, and how many there are."
assert QD == re.search(r'"DOCUMIND_HANDOFF_QUESTION",\n\s+"([^"]+)"\)', SRC["smoke/smoke_handoff.py"]).group(1)   # the smoke's own question
assert f'"question": "{QD}"' in DEPUTY_PY
MK = 'PROJECT="$PROJECT" REGION="$REGION"'


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


CELLS = {
    "deploy": (f"make build deploy-services SERVICES=agent SCRIPTS=commands/lesson-8.4.sh {MK}   # the peer, with its cap\n"
               f"make build deploy-services SERVICES=chat SCRIPTS=commands/lesson-12.8.sh {MK}   # the chat, with peer.py"),
    "handoff": ('export SINCE107="$(date -u +%FT%TZ)" CHAT="https://documind-chat-$NUMBER.$REGION.run.app" '
                'AGENT="https://documind-agent-$NUMBER.$REGION.run.app"\n'
                f"make handoff {MK}"),
    "gate": heredoc(GATE_PY),
    "health": 'curl -s -H "Authorization: Bearer $(tok "$AGENT")" "$AGENT/health"; echo',
    "drill": f"make agent-drill {MK}   # the peer capped at 1 for a minute or two, then 12 again",
    "smoke": f"make smoke-handoff {MK}",
    "deputy": ('gcloud run services update documind-chat --region="$REGION" --project="$PROJECT" --quiet \\\n'
               '  --update-env-vars="PEER_ACCOUNT=documind-ui-sa@$PROJECT.iam.gserviceaccount.com" >/dev/null 2>&1 \\\n'
               '  && echo ">> documind-chat: PEER_ACCOUNT=documind-ui-sa, on three rosters, for this cell" \\\n'
               '  || echo "ERROR: the env update failed; the turn below would run with PEER_ACCOUNT unchanged"\n'
               + heredoc(DEPUTY_PY, 'CHAT_TOKEN="$(tok "$CHAT")" ') + "\n"
               f"make handoff {MK}   # PEER_ACCOUNT back to the account documind-agent runs as"),
    "logs": "sleep 20   # Cloud Logging needs a moment to show the lines\n" + heredoc(LOGS_PY),
    "off": f"make handoff OFF=1 {MK}",
    "cc": "make check-callers GRAPH=1",
    "change": (f"sed -i 's/^{SED_FROM}/{SED_TO}/' commands/lesson-12.8.sh\n"
               "git diff -U0 commands/lesson-12.8.sh | grep '^[-+]for'\n"
               'python commands/check_callers.py --graph; echo "exit $?"\n'
               "git checkout -q commands/lesson-12.8.sh && python commands/check_callers.py --graph | tail -2"),
    "chain_on": (f"make deploy-services SCRIPTS=commands/lesson-8.4.sh PEER_CHAIN=on {MK}   # rebuilds the peer's image, then deploys it\n"
                 f"# later, to switch it off: the same line without PEER_CHAIN=on"),
    "chain": heredoc(CHAIN_CELL_PY, 'AGENT_TOKEN="$(tok "$AGENT")" '),
    "shapes": "make agent-shapes OFFLINE=1",
}
_, GATE_OUT = run_cell(GATE_PY)
assert GATE_OUT.splitlines()[0] == f"HANDOFF_MAX_PER_TURN {MAX_HANDOFFS}, PEER_TIMEOUT_S {PEER_TIMEOUT:g} s, the turn's deadline {TURN_DEADLINE:g} s", GATE_OUT
assert GATE_OUT.count(": sent\n") == 1 and GATE_OUT.count("(a confused deputy)") == 2 and GATE_OUT.rstrip().endswith("0.5 s left in the turn: the hand-off waits at most 1 s")
assert "30 s left in the turn: the hand-off waits at most 30 s" in GATE_OUT and "100 s left in the turn: the hand-off waits at most 75 s" in GATE_OUT

# the ping-pong (step 10): make agent-shapes OFFLINE=1 runs agent_shapes.py --offline in ~/graph-venv (the chat image's
# pins, through agent-turn.sh), so the build runs the same script on the same pins; without --offline it refuses
SHAPES_RECIPE = re.search(r"^agent-shapes:\n\t(.+)$", SRC["mk/agents.mk"], re.M).group(1)
assert SHAPES_RECIPE == "@OFFLINE=1 PY=$(PY) bash commands/agent-turn.sh commands/agent_shapes.py $(if $(OFFLINE),--offline,)"
MAX_TRANSFERS = int(re.search(r"^MAX_TRANSFERS = (\d+) ", SRC[SHAPES_F], re.M).group(1))
assert MAX_TRANSFERS == 3, MAX_TRANSFERS                  # the prose and the checklist name the fourth transfer
_shapes = subprocess.run([sys.executable, str(KIT / SHAPES_F), "--offline"], cwd=str(KIT), capture_output=True, text=True,
                         encoding="utf-8", env=ENV)
assert _shapes.returncode == 0 and not _shapes.stderr.strip(), (_shapes.returncode, _shapes.stdout[-800:], _shapes.stderr[-1500:])
SHAPES_OUT = _shapes.stdout
_refused = subprocess.run([sys.executable, str(KIT / SHAPES_F)], cwd=str(KIT), capture_output=True, text=True,
                          encoding="utf-8", env=ENV)
assert _refused.returncode == 2 and "offline only so far" in _refused.stderr and not _refused.stdout   # the only mode
SHAPE_RUNS = SHAPES_OUT.split("\n== ")[1:]
assert len(SHAPE_RUNS) == 2 and SHAPE_RUNS[0].startswith("transfers between the desks allowed")
assert SHAPE_RUNS[1].startswith("disallow_transfer_to_peers=True on both desks")
STOP_WORDS = f"Stopped after {MAX_TRANSFERS} transfers in one turn."
for _run in SHAPE_RUNS:
    _transfers = re.findall(r"^transfer (\d+): (\w+) -> (\w+)(.*)$", _run, re.M)
    assert [int(t[0]) for t in _transfers] == list(range(1, MAX_TRANSFERS + 2)), _run
    assert [bool(t[3]) for t in _transfers] == [False] * MAX_TRANSFERS + [True], _run      # the last one alone refused
    assert f"answer, written by TransferCap, in {_transfers[-1][2]}'s place: {STOP_WORDS}" in _run, _run
    assert f"model calls: {MAX_TRANSFERS + 1} | transfers made: {MAX_TRANSFERS} | session state stored after the turn: {{}}" in _run
assert "  handbook_desk  desk_root, statute_desk\n" in SHAPE_RUNS[0] and "  handbook_desk  desk_root\n" in SHAPE_RUNS[1]
assert re.findall(r"^transfer \d+: (\w+) -> (\w+)", SHAPE_RUNS[1], re.M) == [
    ("desk_root", "handbook_desk"), ("handbook_desk", "desk_root"), ("desk_root", "statute_desk"), ("statute_desk", "desk_root")]
assert not any(re.search(r"\b(sub_agents|transfer_to_agent)\b", p.read_text(encoding="utf-8"))   # no deployed agent transfers
               for p in (KIT / "services").rglob("*.py"))
BACK = GRAPH_CASES["back"]
CHANGE_OUT = (f"-{BACK[0][0]}\n+{BACK[0][1]}\n" + BACK[2] + f"exit {BACK[1]}\n" + "\n".join(CC_OUT.rstrip("\n").splitlines()[-2:]) + "\n")
assert BACK[0] == (SED_FROM + " \\", SED_TO + " \\"), BACK[0]
OUT = {"handoff": HANDOFF_ON, "gate": GATE_OUT, "health": HEALTH_RAW + "\n", "off": HANDOFF_OFF, "cc": CC_ECHO + "\n" + CC_OUT,
       "change": CHANGE_OUT, "shapes": SHAPES_OUT}
REC = {"ui": pb.recorded(LESSON, "ui_captions.txt"), "drill": pb.recorded(LESSON, "agent_drill.txt"),
       "smoke": pb.recorded(LESSON, "smoke_handoff.txt"), "deputy": pb.recorded(LESSON, "deputy.txt"),
       "logs": pb.recorded(LESSON, "logs.txt"), "chain": pb.recorded(LESSON, "chain_reject.txt")}

# ------------------------------------------------------------------ what the build ran, as the page shows it
WRAP = 104


def wrap(text: str, first: str, rest: str) -> list:
    import textwrap
    return textwrap.wrap(text, WRAP, initial_indent=first, subsequent_indent=rest, break_on_hyphens=False) or [first.rstrip()]


def show_records(turn: dict) -> list:
    out = []
    for h in records(turn):
        if h["outcome"] == "refused":
            out += wrap(f"refused before anything was sent: {h['reason']}", f"  hand-off {h['n']}: ", "    ")
        else:
            out.append(f"  hand-off {h['n']}: {h['outcome']}, the peer's task {h['state']}, its budget {h['budget_s']:g} s")
    return out


def head(turn: dict) -> str:
    b = turn["body"]
    return f"  {turn['status']}  tool_calls {b['tool_calls']}  refusals {b['refusals']}"


meta = POSTS[0]["metadata"]
E2E = [f"POST /v1/chat to the kit's chat app, brain adk, as documind-ui-sa (tenant acme):", f'  "{Q_ONE}"', head(ONE)]
E2E += show_records(ONE)
E2E += wrap(ONE["body"]["answer"], "  the answer: ", "    ")
E2E += [f"  at the peer's door, as documind-chat-sa: GET {door(ONE)[0]['path']}, then POST / {POSTS[0]['rpc']}",
        f"    the message's keys: {', '.join(POSTS[0]['message_keys'])}",
        f"    its words: {POSTS[0]['parts'][0]!r}",
        f"    the request's metadata: {CHAIN_KEY} {meta[CHAIN_KEY]}, {HANDOFF_KEY} (32 hex characters)",
        f"  the peer's own model calls for the task: {peer_calls(ONE)}",
        f"  the hand-off's log line: outcome {HLINE['outcome']}, peer_rosters {HLINE['peer_rosters']}, request_chars {HLINE['request_chars']},"
        f" the same hand-off id",
        f"  the chat row: tool_calls {CROW['tool_calls']}, and no handoffs key", "",
        "the same question, as a person on zeta's roster alone:", head(ZETA_T)]
E2E += show_records(ZETA_T) + ["  at the peer's door: nothing", "", "three questions for the peer, side by side, as documind-ui-sa:", head(THREE_T)]
E2E += show_records(THREE_T) + [f"  at the peer's door: {len([e for e in door(THREE_T) if e['method'] == 'POST'])} messages", "",
                                "a question for the peer and a search, side by side, as documind-ui-sa:",
                                head(MIX_T) + f"  citations {len(MIX_T['body']['citations'])}"]
E2E += wrap(MIX_T["body"]["answer"], "  the answer: ", "    ")
BUILD_E2E = "\n".join(E2E)

drill_c, drill_a = DRILL[("C", "task")], DRILL[("A", "task")]
BUILD_CAP = "\n".join(
    ["the kit's peer at its default cap; a task whose model asks for its tool again and again,",
     f"sent as the chat sends one (the chain {[ASKER]}):",
     f"  {LOOP_TASK['status']['state']} after {LOOP_CALLS} model calls: {LOOP_WORDS}", "",
     "make agent-drill's own Python against the kit's peer, at ADK_MAX_LLM_CALLS=1 and then at its default:",
     f"  /health: max_llm_calls {DRILL[('C', 'cap')][1]}",
     drill_c[1].rstrip("\n") + f"   ({drill_c[2]} model call)",
     f"  /health: max_llm_calls {DRILL[('A', 'cap')][1]}",
     drill_a[1].rstrip("\n") + f"   ({drill_a[2]} model calls)"])

CHAIN_SHOWN = {"none": "no chain", "chat": str([ASKER]), "partner": str([ASKER, "partner_agent"]),
               "loop": str(["partner_agent", NAME]), "hops": str([ASKER, "partner_agent", "vendor_agent"])}


def cell_of(k: str, c: str) -> str:
    run = CHAIN_RUNS[(k, c)]
    return f"{run['state'].removeprefix('TASK_STATE_').lower()}, {run['calls']} model call{'s' if run['calls'] != 1 else ''}"


W1 = max(len(v) for v in CHAIN_SHOWN.values()) + 2
W2 = max(len(cell_of('A', c)) for c in CHAINS) + 3
CH = ["the same question to the kit's peer, the request's chain in its metadata:", "",
      f"  {'the chain':<{W1}}{'PEER_CHAIN=off':<{W2}}PEER_CHAIN=on"]
CH += [f"  {CHAIN_SHOWN[c]:<{W1}}{cell_of('A', c):<{W2}}{cell_of('B', c)}" for c in CHAINS]
CH += ["", "the two refusals, each a task whose history holds the question alone:"]
for c in ("loop", "hops"):
    CH += wrap(CHAIN_RUNS[("B", c)]["words"], "  ", "    ")
CH += ["", "the peer's log line for each (services/agent/chain.py's own logger):"]
CH += ["  " + json.dumps({**x, "task_id": "(the task's id)"}) for x in REFUSED_LINES[:2]]
BUILD_CHAIN = "\n".join(CH)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


def run_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>output of the build&#39;s offline run ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "deploy": "run in the operator shell, in the kit, only if your peer or chat predate this lesson's kit (each several minutes)",
    "handoff": "run in the operator shell, in the kit (the hand-off on: one env update on documind-chat, no model call)",
    "gate": "run in the operator shell, in the kit (peer.py's gate and wait, on the kit's own code; no network)",
    "health": "run in the operator shell, in the kit (the peer's /health)",
    "drill": "run in the operator shell, in the kit (the cap tripped, then put back)",
    "smoke": "run in the operator shell, in the kit (the hand-off's smoke: two turns)",
    "deputy": "run in the operator shell, in the kit (the confused deputy, refused before anything is sent)",
    "logs": "run in the operator shell, in the kit (the hand-off lines and the chat rows since step 3)",
    "off": "run in the operator shell, in the kit (the hand-off off again)",
    "cc": "run in the operator shell, in the kit (the caller graph; offline, no gcloud)",
    "change": "run in the operator shell, in the kit (Change-it: an edge back from the peer to the chat, then the kit put back)",
    "chain_on": "run in the operator shell, in the kit (the peer deployed with PEER_CHAIN=on; no model call)",
    "chain": "run in the operator shell, in the kit (two chained tasks for the peer, each refused before a model call)",
    "shapes": ("run in the operator shell, in the kit (two ADK desks in a ping-pong, and the cap that ends it; offline, Rs 0; "
               "the first run builds ~/graph-venv)"),
}
LIVE = "(the author's run on a live lane; your ids, times, words and rupees differ)"
OUT_LABELS = {
    "handoff": "(the kit's handoff.sh against a stub gcloud; your NUMBER is yours)",
    "gate": "(this cell, run on the kit's own peer.py and limits.py)",
    "health": "(the kit's agent.py, served offline by its own to_a2a with the image's pins; your NUMBER is yours)",
    "off": "(the kit's handoff.sh against a stub gcloud)",
    "cc": "(the kit's check_callers.py on the kit's own sa.tf and deploy scripts)",
    "change": "(check_callers.py on a copy of the kit with that one line changed, then on the kit)",
    "shapes": "(the kit's agent_shapes.py on its own scripted models, with the chat image's pins; yours should match it)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
WIN.update({f"REC_{k.upper()}": out_window(LIVE, v) for k, v in REC.items()})
WIN.update({
    "BUILD_E2E": run_window("(the kit's chat app under TestClient, its ADK brain, peer.py and a2a-sdk's client, the kit's peer over its own to_a2a; Gemini scripted on both sides)", BUILD_E2E),
    "BUILD_CAP": run_window("(the kit's peer over its own to_a2a, its model scripted and counted)", BUILD_CAP),
    "BUILD_CHAIN": run_window("(the kit's peer over its own to_a2a at PEER_CHAIN=off and on, its model scripted and counted)", BUILD_CHAIN),
})

# ------------------------------------------------------------------ the widgets' data: every outcome from the run above
WHO_LABELS = {"acme": "an acme member; the peer's account on acme alone", "zeta": "a zeta member; the peer's account on acme alone",
              "uisa": "an acme member; PEER_ACCOUNT on three rosters"}
SENDS_LABELS = {"one": "one question for the peer", "three": "three questions for the peer, side by side"}
PEER_LABELS = {"answer": "answers", "loop": "loops: asks its tool again and again", "slow": "is slower than the budget",
               "shut": "is shut to the chat (no invoker binding)"}


def view(key: str) -> dict:
    t = TURN[key]
    mode = key.split("|")[2]
    recs, posts = records(t), [e for e in door(t) if e["method"] == "POST"]
    sent = [h for h in recs if h["outcome"] != "refused"]
    gate = "; ".join(f"hand-off {h['n']} refused: {h['reason']}" if h["outcome"] == "refused" else
                     f"hand-off {h['n']} sent, its budget {h['budget_s']:g} s" for h in recs)
    if not sent:
        dr, pr = "never reached: nothing was sent.", "never asked."
    elif mode == "shut":
        dr = (f"Cloud Run's check refused documind-chat-sa with {door(t)[0]['status']} at the agent card, "
              "so no message was sent.")
        pr = "never asked."
    else:
        dr = (f"documind-chat-sa fetched the card and sent one message for each of the {len(posts)} hand-offs, each holding "
              f"the question's words, the chain {[ASKER]} and its own hand-off id." if len(posts) > 1 else
              f"documind-chat-sa fetched the card and sent one message: the question's words, the chain {[ASKER]} and a hand-off id.")
        n, tasks = peer_calls(t), len(posts)
        assert n == {"answer": 2, "loop": PEER_CAP, "slow": 2}[mode] * tasks, (key, n)
        many = tasks > 1
        pr = {"answer": (f"{tasks} tasks, {n} model calls in all; each task completed." if many else
                         f"{n} model calls; the task completed."),
              "loop": (f"{tasks} tasks, {PEER_CAP} model calls each, then the cap: each task ended failed." if many else
                       f"{n} model calls, then the cap: the task ended failed."),
              "slow": ("each task's first model call outlasted the hand-off's budget. The tasks ran on at the peer, and "
                       "nothing they said reached the turn." if many else
                       "its first model call outlasted the hand-off's budget. The task ran on at the peer, and nothing it "
                       "said reached the turn.")}[mode]
    read = [lane(str(r["response"].get("answer") or r["response"].get("error"))) for batch in t["read"] for r in batch if r["name"] == NAME]
    b = t["body"]
    return {"gate": gate, "stop": not sent, "door": dr, "peer": pr, "skip": not sent or mode == "shut",
            "read": read, "resp": f"tool_calls {b['tool_calls']}, refusals {b['refusals']}, limits.tool_timeouts {b['limits']['tool_timeouts']}"}


HO = {k: view(k) for k in TURN if k != "mixed"}
assert len(HO) == len(WHO_LABELS) * len(SENDS_LABELS) * len(PEER_LABELS) == 24
GRAPH_LABELS = {"kit": "the kit as it is", "back": "+ documind-agent-sa on documind-chat (the Change-it)",
                "self": "+ documind-mcp-sa on documind-mcp", "outsider": "+ documind-outsider-sa on documind-agent"}


def graph_view(out: str, code: int) -> dict:
    blocks = out.rstrip("\n").split("\n\n")
    return {"edges": [x.strip() for x in blocks[1].splitlines()[1:]], "verdict": blocks[-1].splitlines(), "exit": code}


LP_GRAPH = {k: graph_view(v[2], v[1]) for k, v in GRAPH_CASES.items()}
LP_CHAIN = {f"{c}|{'off' if k == 'A' else 'on'}": {"state": r["state"], "calls": r["calls"], "said": r["words"] or r["answer"]}
            for (k, c), r in CHAIN_RUNS.items()}
CHAIN_LABELS = {"none": "none (a caller that sends no chain)", "chat": f"{[ASKER]}, as the chat sends it",
                "partner": f"{[ASKER, 'partner_agent']}: a partner passed it on", "loop": f"{['partner_agent', NAME]}: it has been here",
                "hops": f"{[ASKER, 'partner_agent', 'vendor_agent']}: a third hop"}

JS_SRC = r"""var HO = __HO__, WHO = __WHO__, SENDS = __SENDS__, PEER = __PEER__, G = __G__, GL = __GL__, C = __C__, CL = __CL__;
var $ = function(id){ return document.getElementById(id); };
function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = text; return e; }
function fill(id, opts){ var s = $(id); Object.keys(opts).forEach(function(k){ var o = el('option', '', opts[k]); o.value = k; s.appendChild(o); }); }
function hop(cls, head, text){ var li = el('li', cls, ''); li.appendChild(el('b', '', head + ' ')); li.appendChild(document.createTextNode(text)); return li; }
function turn(){ var t = HO[$('ho-who').value + '|' + $('ho-sends').value + '|' + $('ho-peer').value], out = $('ho-out');
  out.textContent = '';
  out.appendChild(hop(t.stop ? 'stop' : '', 'The gate, before anything is sent:', t.gate));
  out.appendChild(hop(t.skip ? 'skip' : '', 'The peer’s door:', t.door));
  out.appendChild(hop(t.skip ? 'skip' : '', 'The peer:', t.peer));
  out.appendChild(hop('', 'What the chat’s model reads back:', t.read.join(' / ')));
  out.appendChild(hop('', 'The response:', t.resp)); }
function line(box, text, cls){ box.appendChild(el('div', 'lp-line' + (cls ? ' ' + cls : ''), text)); }
function loop(){ var g = G[$('lp-bind').value], box = $('lp-graph'), c = C[$('lp-chain').value + '|' + $('lp-switch').value], task = $('lp-task');
  box.textContent = ''; task.textContent = '';
  g.edges.forEach(function(e){ line(box, e, ''); });
  g.verdict.forEach(function(v, i){ line(box, v, i ? '' : (g.exit ? 'bad' : 'good')); });
  line(box, 'exit ' + g.exit, g.exit ? 'bad' : 'good');
  line(task, c.state + ', ' + c.calls + ' model call' + (c.calls === 1 ? '' : 's'), c.calls ? 'good' : 'bad');
  line(task, c.said, ''); }
fill('ho-who', WHO); fill('ho-sends', SENDS); fill('ho-peer', PEER); fill('lp-bind', GL); fill('lp-chain', CL);
fill('lp-switch', {off: 'off (the kit’s default)', on: 'on'});
['ho-who', 'ho-sends', 'ho-peer'].forEach(function(id){ $(id).addEventListener('change', turn); });
['lp-bind', 'lp-chain', 'lp-switch'].forEach(function(id){ $(id).addEventListener('change', loop); });
turn(); loop();"""
for token, value in (("__HO__", HO), ("__WHO__", WHO_LABELS), ("__SENDS__", SENDS_LABELS), ("__PEER__", PEER_LABELS), ("__G__", LP_GRAPH),
                     ("__GL__", GRAPH_LABELS), ("__C__", LP_CHAIN), ("__CL__", CHAIN_LABELS)):
    JS_SRC = JS_SRC.replace(token, json.dumps(value))           # insertion order: the selects list their options in it
squeeze = lambda code: "\n".join(x.strip() for x in code.splitlines() if x.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\nif (!document.getElementById('ho')) { return; }\n" + squeeze(JS_SRC).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS and "__" not in JS.replace("__proto__", "")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.pc-two{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:0 12px;}
.lp-line{font-family:var(--mono);font-size:12px;margin:2px 0;overflow-wrap:anywhere;}
.lp-line.good{color:var(--teal);font-weight:600;}
.lp-line.bad{color:#c2410c;font-weight:600;}
.hops{list-style:none;margin:0;padding:0;counter-reset:hop;}
.hops li{position:relative;padding:6px 8px 6px 34px;border-left:2px solid var(--border);margin-left:10px;font-size:12.5px;overflow-wrap:anywhere;}
.hops li::before{counter-increment:hop;content:counter(hop);position:absolute;left:-12px;top:6px;width:22px;height:22px;border-radius:50%;background:var(--teal);color:#fff;font-family:var(--mono);font-size:11px;display:flex;align-items:center;justify-content:center;}
.hops li.stop::before{background:#c2410c;}
.hops li.skip{color:var(--slate-light);}
.hops li.skip::before{background:var(--slate-light);}
.hops b{color:var(--navy);}
"""

# rupees for the cost table: shared/prices.py at gemini-3.6-flash's list price
from shared import prices  # noqa: E402
STATS = {"PEER_TIMEOUT": f"{PEER_TIMEOUT:g}", "PEER_CAP": str(PEER_CAP), "MAX_HANDOFFS": str(MAX_HANDOFFS), "ASKER": ASKER,
         "TURN_DEADLINE": f"{TURN_DEADLINE:g}", "UI_WAIT": str(UI_WAIT), "ADK_DEFAULT": str(ADK_DEFAULT),
         "CHAT_CONC": str(CHAT_SLOTS["concurrency"]), "CHAT_INST": str(CHAT_SLOTS["max-instances"]),
         "PEER_CONC": str(PEER_SLOTS["concurrency"]), "PEER_INST": str(PEER_SLOTS["max-instances"]), "N_TURNS": str(len(HO)),
         "N_ALL_TURNS": str(len(TURN)),
         "SLOW_BUDGET": f"{SLOW_BUDGET:g}", "N_SERVICES": str(N_SERVICES), "N_EDGES": str(N_EDGES), "CHAIN_KEY": CHAIN_KEY,
         "HANDOFF_KEY": HANDOFF_KEY, "MAX_HOPS": str(MAX_HOPS), "TURN_CALLS": str(TURN_CALLS), "N_FILES": str(len(FILES)),
         "TOOL_FLOOR": f"{TOOL_FLOOR:g}", "QD": html.escape(QD), "Q_ONE": html.escape(Q_ONE), "Q_MIX": html.escape(Q_MIX),
         "ORDER": ", ".join(check_callers.order(G)), "USD_INR": str(prices.USD_INR), "DRILL_VAL": str(DRILL_VAL),
         "DRILL_CALLS": str(drill_c[2] + drill_a[2]), "MAX_TRANSFERS": str(MAX_TRANSFERS),
         "SHAPE_CALLS": str(MAX_TRANSFERS + 1)}
assert drill_c[2] + drill_a[2] == 3 and "Two tasks, three model calls in all." in SRC["commands/agent-drill.sh"]

if os.environ.get("CELLS_ONLY"):
    for k, v in {**OUT, "BUILD_E2E": BUILD_E2E, "BUILD_CAP": BUILD_CAP, "BUILD_CHAIN": BUILD_CHAIN}.items():
        print(f"===== {k}\n{v}")
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


setup = setup_section()
body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: the hand-off end to end ({len(TURN)} turns through the kit's chat app to the kit's peer), the cap at {PEER_CAP}, "
      f"the chain off and on, check-callers on the kit and {len(GRAPH_CASES) - 1} copies | Gemini, the rosters and the lane stood in"
      + (" | culsans stood in" if STOOD_IN_CULSANS else ""))
