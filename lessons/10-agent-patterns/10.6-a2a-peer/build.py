"""Build lesson 10.6 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The A2A peer, traced. documind-agent is an agent another team would build: ADK's LlmAgent, the lane's four tools
discovered over MCP, served to other agents over A2A - an agent card at /.well-known/agent-card.json and JSON-RPC
message/send at /. Its permissions are a chain: Cloud Run admits two callers (ui-sa, chat-sa); A2A carries no identity,
so the peer reaches documind-mcp as itself (documind-agent-sa, an invoker there, on acme's roster alone); the server
reaches rag-api as documind-mcp-sa. Offline: the chain as the kit writes it - lesson-8.4.sh, lesson-7.2.sh, roster_plan,
sa.tf's roles, agent.py's imports and the Dockerfile's COPY. Live: the card refused without a token and read with one,
make smoke-agent (the module's A2A gate), and one task traced - its history, then the two logs that name the peer and
the deputy, and never the caller.

Build-time proof: the offline cell runs here on the kit's files. The live cells run against the kit's own agent.py,
served by the kit's own to_a2a in a venv holding the peer image's pins (google-adk 2.8.0, a2a-sdk 1.1.2), calling the
kit's own server.py over MCP - with Gemini, the metadata server's token, Cloud Run's IAM check, the MCP token
signatures, rag-api and Firestore stood in. The gate's lines are the kit's smoke_agent.py against that peer.
"""
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "10.6"
title = "<title>Lesson 10.6 Trace the implemented A2A peer and its permissions - one task through three protocols | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
SA = lambda name: f"documind-{name}-sa@{PROJ}.iam.gserviceaccount.com"  # noqa: E731
QG = "After how many years of continuous service does gratuity become payable?"
LANE_AGENT = "https://documind-agent-NUMBER.asia-south1.run.app"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.hops{list-style:none;margin:0;padding:0;counter-reset:hop;}
.hops li{position:relative;padding:6px 8px 6px 34px;border-left:2px solid var(--border);margin-left:10px;font-size:12.5px;overflow-wrap:anywhere;}
.hops li::before{counter-increment:hop;content:counter(hop);position:absolute;left:-12px;top:6px;width:22px;height:22px;border-radius:50%;background:var(--teal);color:#fff;font-family:var(--mono);font-size:11px;display:flex;align-items:center;justify-content:center;}
.hops li.stop::before{background:#c2410c;}
.hops li.skip{color:var(--slate-light);}
.hops li.skip::before{background:var(--slate-light);}
.hops b{color:var(--navy);}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
AGP, DEP84, DOCK = "services/agent/agent.py", "commands/lesson-8.4.sh", "services/agent/Dockerfile"
EXCERPTS = {
    "peer": ("services/agent/agent.py - the peer: the lane's tools, discovered over MCP, and a credential minted per call",
             block(AGP, "def build_agent() -> LlmAgent:", n=22)),
    "token": ("services/agent/agent.py - the token for documind-mcp: the metadata server's, as documind-agent-sa",
              block(AGP, "    return {\"Authorization\": f\"Bearer {google.oauth2.id_token.fetch_id_token(request, MCP_URL)}\"}", n=1)),
    "serve": ("services/agent/agent.py - served over A2A: the card and message/send, from the agent",
              block(AGP, "agent = build_agent()", n=4)),
    "knock": ("commands/lesson-8.4.sh - who may call the peer",
              block(DEP84, "for sa in documind-ui-sa documind-chat-sa; do", n=5)),
}
assert "header_provider=_mcp_headers," in EXCERPTS["peer"][1] and "tools=[lane]," in EXCERPTS["peer"][1]
assert "app = to_a2a(agent, host=_host, port=_port, protocol=_protocol)" in EXCERPTS["serve"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
ag_src, dep84, dep72, dock, satf = ((KIT / p).read_text(encoding="utf-8") for p in (AGP, DEP84, "commands/lesson-7.2.sh", DOCK, "terraform/sa.tf"))
import ast  # noqa: E402
_tree = ast.parse(ag_src)
IMPORTED = {(n.module or "").split(".")[0] for n in ast.walk(_tree) if isinstance(n, ast.ImportFrom)} | \
           {a.name.split(".")[0] for n in ast.walk(_tree) if isinstance(n, ast.Import) for a in n.names}
assert "shared" not in IMPORTED and "services" not in IMPORTED, IMPORTED                                # the peer holds no kit code
assert "tools/check_auth_wiring.py" in ag_src and not (KIT / "tools/check_auth_wiring.py").exists() and not (ROOT / "tools/check_auth_wiring.py").exists()
assert "COPY --chown=app:app services/agent/ ./" in dock and "shared" not in [ln.split()[1] for ln in dock.splitlines() if ln.startswith("COPY")]
assert "request.headers" not in ag_src and "log.info" in ag_src and ag_src.count("log.") == 1                    # it logs start-up only, never a caller
assert "gcloud builds submit" in dep84                                                                   # this script builds its own image
assert "for who in documind-ui-sa documind-agent-sa documind-outsider-sa; do" in dep72                    # agent-sa may call documind-mcp
agent_roles = re.search(r"agent_roles = \[(.*?)\]", satf, re.S).group(1)
assert '"roles/aiplatform.user"' in agent_roles and "run.invoker" not in re.sub(r"#.*", "", agent_roles)
sys.path[:0] = [str(KIT), str(KIT / "commands")]
from lane import roster_plan  # noqa: E402
PLAN, _ = roster_plan(PROJ, "acme", [])
ROSTER = {}
for t, e in PLAN:
    ROSTER.setdefault(e, []).append(t)
assert ROSTER[SA("agent")] == ["acme"]
reqs = dict(re.findall(r"^([a-z0-9\-\[\],]+)==([\d.]+)$", (KIT / "services/agent/requirements.txt").read_text(encoding="utf-8"), re.M))
assert reqs["google-adk[a2a,mcp]"] == "2.8.0" and reqs["a2a-sdk[http-server]"] == "1.1.2"
smoke_src = (KIT / "smoke/smoke_agent.py").read_text(encoding="utf-8")
assert '(ok if status in (401, 403) else bad)("card refused without a token"' in smoke_src

# ------------------------------------------------------------------ the cells
PERMS_PY = """import ast, re, sys
sys.path[:0] = [".", "commands"]
from lane import roster_plan
deploy = open("commands/lesson-8.4.sh").read().split("# ---- DEPLOY ----")[1].split("# ---- SMOKE ----")[0]
env = dict(kv.split("=", 1) for kv in re.search(r'--set-env-vars="\\^\\|\\^([^"]+)"', deploy).group(1).split("|"))
print("documind-agent, as commands/lesson-8.4.sh deploys it:")
print("  runs as", re.search(r"--service-account=([\\w-]+)@", deploy).group(1), " model", env["AGENT_MODEL"], " knows one URL: MCP_URL")
print("  who may call it:", ", ".join(re.search(r"for sa in ([\\w\\- ]+); do", deploy).group(1).split()))
mcp = open("commands/lesson-7.2.sh").read()
print("  documind-agent-sa may call documind-mcp:", "documind-agent-sa" in re.search(r"for who in ([\\w\\- ]+); do", mcp).group(1))
roles = re.search(r"agent_roles = \\[(.*?)\\]", open("terraform/sa.tf").read(), re.S).group(1)
print("  its project roles:", ", ".join(re.findall(r'"roles/([\\w.]+)"', roles)))
tenants = [t for t, e in roster_plan("PROJECT", "acme", [])[0] if e.startswith("documind-agent-sa@")]
print("  the rosters it is on:", ", ".join(tenants))
tree = ast.parse(open("services/agent/agent.py").read())
mods = sorted({(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
              | {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
print("  agent.py imports:", ", ".join(m for m in mods if m))
print("  the image copies:", ", ".join(l.split()[-2] for l in open("services/agent/Dockerfile") if l.startswith("COPY")))"""

CARD = ('export AGENT="https://documind-agent-$NUMBER.$REGION.run.app" SINCE123="$(date -u +%FT%TZ)"\n'
        'curl -s -o /dev/null -w "the card without a token: HTTP %{http_code}\\n" "$AGENT/.well-known/agent-card.json"\n'
        'curl -s -H "Authorization: Bearer $(tok "$AGENT")" "$AGENT/.well-known/agent-card.json" > /tmp/card123.json\n')
CARD_PY = """import json
card = json.load(open("/tmp/card123.json"))
iface = (card.get("supportedInterfaces") or [{}])[0]
print(f"the card with a token: {card['name']}, version {card['version']}")
print(f"  answers at {iface.get('url')} over {iface.get('protocolBinding')}, A2A {iface.get('protocolVersion')}")
print(f"  streaming {card['capabilities'].get('streaming')}, input {card['defaultInputModes']}, output {card['defaultOutputModes']}")
print("  skills:", ", ".join(s["name"] for s in card["skills"]))"""

GATE = 'make smoke-agent PROJECT="$PROJECT" REGION="$REGION"   # the module\'s A2A gate: five checks'

TRACE_PY = """import json, os, urllib.request, uuid
body = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "message/send", "params": {"message": {
    "role": "user", "kind": "message", "messageId": str(uuid.uuid4()),
    "parts": [{"kind": "text", "text": "After how many years of continuous service does gratuity become payable?"}]}}}
req = urllib.request.Request(os.environ["AGENT"] + "/", data=json.dumps(body).encode(),
                             headers={"Authorization": "Bearer " + os.environ["AGENT_TOKEN"], "Content-Type": "application/json"})
task = json.loads(urllib.request.urlopen(req, timeout=180).read())["result"]
print(f"a {task['kind']}, state {task['status']['state']}, {len(task['history'])} messages in its history:")
for m in task["history"]:
    for p in m["parts"]:
        if p["kind"] == "text":
            print(f"  {m['role']:5} text      {p['text'][:66]!r}")
        elif p["metadata"].get("adk_type") == "function_call":
            print(f"  {m['role']:5} calls     {p['data']['name']}({', '.join(f'{k}={str(v)[:34]!r}' for k, v in p['data']['args'].items())})")
        else:
            r = p["data"]["response"]
            got = "an error" if r.get("isError") else f"{len(r.get('structuredContent', {}).get('citations', []))} citations"
            print(f"  {m['role']:5} receives  {p['data']['name']}: {got}")
print("the answer:", " ".join(p["text"] for a in task["artifacts"] for p in a["parts"] if p["kind"] == "text")[:84])"""

LOGS_PY = """import json, os, subprocess
def rows(service, flt):
    f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}" AND {flt} '
         f'AND timestamp>="{os.environ["SINCE123"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    return [e["jsonPayload"] for e in json.loads(out or "[]")]
print("documind-mcp - who asked it:")
for j in rows("documind-mcp", 'jsonPayload.event="mcp_call"'):
    print(f"  {j['tool']:15} tenant {j['tenant']:6} caller {j['caller'].split('@')[0]}")
print("documind-api - who it served:")
for j in rows("documind-api", 'jsonPayload.brain="mcp"'):
    print(f"  retrieve        tenant {j['tenant']:6} user   {j['user'].split('@')[0]}")"""


def heredoc(body: str, prefix: str = "", python: str = "python") -> str:
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


CELLS = {
    "perms": heredoc(PERMS_PY),
    "card": CARD + heredoc(CARD_PY),
    "gate": GATE,
    "trace": heredoc(TRACE_PY, 'AGENT_TOKEN="$(tok "$AGENT")" '),
    "logs": "sleep 20   # Cloud Logging needs a moment to show the lines\n" + heredoc(LOGS_PY),
}

T = Path(tempfile.mkdtemp(prefix="lesson123-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "REGION": "asia-south1"}


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.stdout[-800:], r.stderr[-1500:])
    return r.stdout


def reply(h, code: int, body) -> None:
    data = json.dumps(body, separators=(",", ":")).encode()
    h.send_response(code)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(data)))
    h.end_headers()
    h.wfile.write(data)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ---- step 3: the chain as the kit writes it
OUT = {"perms": run_cell(PERMS_PY, cwd=KIT)}
P3 = OUT["perms"]
assert "  who may call it: documind-ui-sa, documind-chat-sa" in P3 and "documind-agent-sa may call documind-mcp: True" in P3, P3
assert "  the rosters it is on: acme" in P3 and "shared" not in P3.split("agent.py imports:")[1].split("\n")[0], P3

# ---- the peer's venv: the image's pins, made once and kept (a2a-sdk 1.1.2 wants protobuf < 7, so not this interpreter)
VENV = Path(tempfile.gettempdir()) / "agents_workshop" / "venv-a2a"
VPY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not VPY.exists():
    print(f"making {VENV} with services/agent/requirements.txt (once)")
    subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    subprocess.run([str(VPY), "-m", "pip", "install", "-q", "-r", str(KIT / "services/agent/requirements.txt")], check=True)
got = json.loads(subprocess.run([str(VPY), "-c", "import json, importlib.metadata as m; print(json.dumps({p: m.version(p) for p in ('google-adk', 'a2a-sdk')}))"],
                                capture_output=True, text=True, check=True).stdout)
assert got == {"google-adk": "2.8.0", "a2a-sdk": "1.1.2"}, got

# ---- steps 4 to 6: rag-api (stand-in) <- documind-mcp (the kit's server.py) <- documind-agent (the kit's agent.py over A2A)
SEEN = []


class Rag(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        SEEN.append({"tenant": req["tenant_id"], "user": SA("mcp"), "brain": req.get("brain")})
        cites = [{"chunk_id": f"{req['tenant_id']}:payment_of_gratuity_act_1972#{4 + i}", "source_uri": f"gs://{PROJ}-uploads/{req['tenant_id']}/payment_of_gratuity_act_1972.pdf",
                  "page": 2, "quote": "not less than five years", "score": round(0.9 - i * 0.03, 2)} for i in range(5)]
        reply(self, 200, {"answer": "Gratuity is payable after not less than five years of continuous service [1].", "citations": cites,
                          "answerable": True, "confidence": "high"})


rag = ThreadingHTTPServer(("127.0.0.1", 0), Rag)
threading.Thread(target=rag.serve_forever, daemon=True).start()
MCP_PORT, PEER_PORT = free_port(), free_port()
MCP_URL, PEER_URL = f"http://localhost:{MCP_PORT}", f"http://localhost:{PEER_PORT}"
FRONT = """class FrontDoor:                                   # Cloud Run's IAM check, stood in: only the bound invokers' tokens pass
    def __init__(self, app, invokers): self.app, self.invokers = app, invokers
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            token = dict(scope["headers"]).get(b"authorization", b"").decode().removeprefix("Bearer ")
            if token not in self.invokers:
                await send({"type": "http.response.start", "status": 403, "headers": [(b"content-type", b"text/html")]})
                await send({"type": "http.response.body", "body": b"<html><title>403 Forbidden</title></html>"})
                return
        await self.app(scope, receive, send)
"""
MCP_STAND = f"""import sys
sys.path.insert(0, ".")
import shared.documind_tools as dt, shared.iap as iap, shared.tenancy as tenancy
dt._id_token = lambda audience: "MCP-SA"
WHO = {{"AGENT": {SA('agent')!r}, "MEMBER": {SA('ui')!r}, "OUTSIDER": {SA('outsider')!r}}}
ROSTER = {ROSTER!r}
def identity(headers, bearer_audience=None):
    who = headers.get("authorization", "").removeprefix("Bearer ")
    if who not in WHO:
        raise iap.IapError("the bearer token carries no verified email")
    return {{"email": WHO[who], "via": "iam", "aud": bearer_audience}}
iap.identity = identity
tenancy.tenant_for = lambda email: (ROSTER.get(email) or [None])[0]
tenancy.is_member = lambda email, tenant: tenant in ROSTER.get(email, [])
class Snap:
    def __init__(self, d): self.d = d
    def to_dict(self): return self.d
class Q:
    def __init__(self, name): self.name, self.tenant = name, None
    def where(self, filter): self.tenant = filter.value; return self
    def select(self, fields): return self
    def stream(self):
        for f, n in (("hr_policy_2026.md", 41), ("inv_2026_0412.md", 3), ("payment_of_gratuity_act_1972.pdf", 38)):
            yield Snap({{"tenant_id": self.tenant, "gcs_uri": "gs://{PROJ}-uploads/" + self.tenant + "/" + f, "status": "indexed", "chunks": n,
                        "indexed_at": "2026-09-20T10:00:00+00:00"}})
class DB:
    def collection(self, name): return Q(name)
import services.mcp.server as server
server._db = lambda: DB()
{FRONT}
import uvicorn
uvicorn.run(FrontDoor(server.app, {{"AGENT", "MEMBER", "OUTSIDER"}}), host="127.0.0.1", port={MCP_PORT}, log_level="warning")
"""
PEER_STAND = f"""import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "services/agent")
import google.oauth2.id_token
google.oauth2.id_token.fetch_id_token = lambda request, audience: "AGENT"   # the metadata server's token for documind-agent-sa, stood in
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_response import LlmResponse
from google.genai import types as gt
def said(**kw): return LlmResponse(content=gt.Content(role="model", parts=[gt.Part(**kw)]))
async def scripted(self, llm_request, stream=False):                        # Gemini, stood in: it calls the tool a request names
    parts = [p for c in llm_request.contents for p in (c.parts or [])]
    done = [p.function_response.response for p in parts if p.function_response]
    q = [p.text for p in parts if p.text][-1]
    if not done:
        if "cost" in q:
            name, args = "calculate_processing_cost", {{"total_pages": 283, "processing_type": "priority"}}
        elif "documents do you hold" in q:
            name, args = "list_documents", {{}}
        else:
            name, args = "retrieve", {{"query": q.split(": ", 1)[-1], **({{"tenant": "zeta"}} if "tenant zeta" in q else {{}})}}
        yield said(function_call=gt.FunctionCall(name=name, args=args))
        return
    r = done[-1]
    if r.get("isError"):
        yield said(text="The DocuMind server refused this: " + r["content"][0]["text"])
        return
    s = r.get("structuredContent") or {{}}
    if "answer" in s:
        c = s["citations"][0]
        text = s["answer"] + " Source: " + c["source_uri"].rsplit("/", 1)[-1] + ", page " + str(c["page"]) + "."
    elif "documents" in s:
        text = "The " + s["tenant"] + " corpus holds " + str(len(s["documents"])) + " documents: " + ", ".join(d["file"] for d in s["documents"]) + "."
    else:
        text = str(s["total_pages"]) + " pages at " + s["processing_type"] + " cost USD " + str(s["cost_usd"]) + ", Rs " + str(s["cost_inr"]) + "."
    yield said(text=text)
Gemini.generate_content_async = scripted
import logging
import agent
logging.disable(logging.WARNING)
{FRONT}
import uvicorn
uvicorn.run(FrontDoor(agent.app, {{"MEMBER", "CHAT"}}), host="127.0.0.1", port={PEER_PORT}, log_level="warning")
"""
LOG = T / "mcp123.log"
PEER_LOG = T / "peer123.log"
env_mcp = {**ENV, "SELF_URL": MCP_URL, "RAG_API_URL": f"http://127.0.0.1:{rag.server_address[1]}", "GOOGLE_CLOUD_PROJECT": PROJ}
env_peer = {**ENV, "MCP_URL": MCP_URL, "SELF_URL": PEER_URL, "GOOGLE_CLOUD_PROJECT": PROJ, "GOOGLE_GENAI_USE_VERTEXAI": "1",
            "GOOGLE_CLOUD_LOCATION": "global", "AGENT_MODEL": "gemini-3.6-flash"}
FAKE_MINT = ("import subprocess\n"
             "class _Out:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
             "def run(cmd, **kw):\n"
             "    acct = next(c.split('=', 1)[1] for c in cmd if c.startswith('--impersonate-service-account='))\n"
             "    return _Out('OUTSIDER' if 'outsider' in acct else 'CHAT' if 'chat' in acct else 'MEMBER')\n"
             "subprocess.run = run                        # only gcloud is stood in; the rest of subprocess stays\n")


def wait(url: str, token: str, what: str, log: Path) -> None:
    for _ in range(300):
        try:
            urllib.request.urlopen(urllib.request.Request(url + "/health", headers={"Authorization": f"Bearer {token}"}), timeout=1).read()
            return
        except Exception:                          # noqa: BLE001 - not up yet
            time.sleep(0.2)
    raise SystemExit(f"{what} did not start: " + log.read_text(encoding="utf-8")[-1200:])


def send(text: str, token: str) -> tuple[int, dict]:
    body = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "message/send", "params": {"message": {
        "role": "user", "kind": "message", "messageId": str(uuid.uuid4()), "parts": [{"kind": "text", "text": text}]}}}
    try:
        with urllib.request.urlopen(urllib.request.Request(PEER_URL + "/", data=json.dumps(body).encode(),
                                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}), timeout=120) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}


with open(LOG, "w", encoding="utf-8") as logf, open(PEER_LOG, "w", encoding="utf-8") as peerf:
    mcp = subprocess.Popen([sys.executable, "-c", MCP_STAND], cwd=str(KIT), env=env_mcp, stdout=logf, stderr=subprocess.STDOUT)
    peer = None
    try:
        wait(MCP_URL, "MEMBER", "the MCP server", LOG)
        peer = subprocess.Popen([str(VPY), "-c", PEER_STAND], cwd=str(KIT), env=env_peer, stdout=peerf, stderr=subprocess.STDOUT)
        wait(PEER_URL, "MEMBER", "the peer", PEER_LOG)
        # step 4: the card, as the page's two curls and its python read it
        try:
            urllib.request.urlopen(PEER_URL + "/.well-known/agent-card.json", timeout=10)
            code = 200
        except urllib.error.HTTPError as e:
            code = e.code
        card = urllib.request.urlopen(urllib.request.Request(PEER_URL + "/.well-known/agent-card.json", headers={"Authorization": "Bearer MEMBER"})).read().decode()
        (T / "card123.json").write_text(card.replace(PEER_URL, LANE_AGENT), encoding="utf-8")
        OUT["card"] = f"the card without a token: HTTP {code}\n" + run_cell(CARD_PY.replace("/tmp/card123.json", (T / "card123.json").as_posix()))
        # step 5: the gate, the kit's smoke_agent.py as make smoke-agent runs it
        gate = run_cell("import runpy\nrunpy.run_path('smoke/smoke_agent.py', run_name='__main__')\n", FAKE_MINT, cwd=KIT,
                        env={"DOCUMIND_AGENT_URL": PEER_URL, "DOCUMIND_IMPERSONATE_SA": SA("ui")})
        OUT["gate"] = gate.replace(PEER_URL.split("//", 1)[1], LANE_AGENT.split("//", 1)[1]).replace("http://", "https://").strip("\n") + "\n"
        SEEN.clear()
        LOG_BEFORE = LOG.read_text(encoding="utf-8")
        # step 6: one task traced
        OUT["trace"] = run_cell(TRACE_PY, env={"AGENT": PEER_URL, "AGENT_TOKEN": "MEMBER"})
        time.sleep(0.5)
        TRACE_MCP = [json.loads(ln) for ln in LOG.read_text(encoding="utf-8")[len(LOG_BEFORE):].splitlines() if ln.startswith('{"event": "mcp_call"')]
        TRACE_API = list(SEEN)
        # the panel: four requests, as ui-sa and as chat-sa - the peer answers both the same, because it never sees who asked
        REQUESTS = {"gratuity": QG, "zeta": f"For tenant zeta: {QG}", "documents": "Which documents do you hold?",
                    "price": "What would 283 pages cost at priority processing?"}
        PANEL = {}
        for key, text in REQUESTS.items():
            outcomes = []
            for token in ("MEMBER", "CHAT"):
                before, n_seen = len(LOG.read_text(encoding="utf-8")), len(SEEN)
                status, j = send(text, token)
                time.sleep(0.3)
                calls = [p["data"] for m in j["result"]["history"] for p in m["parts"] if p["kind"] == "data" and p["metadata"].get("adk_type") == "function_call"]
                resp = [p["data"]["response"] for m in j["result"]["history"] for p in m["parts"] if p["kind"] == "data" and p["metadata"].get("adk_type") == "function_response"]
                lines = [json.loads(ln) for ln in LOG.read_text(encoding="utf-8")[before:].splitlines() if ln.startswith('{"event": "mcp_call"')]
                outcomes.append({"state": j["result"]["status"]["state"], "tool": calls[0]["name"], "args": calls[0]["args"],
                                 "error": resp[0]["content"][0]["text"].replace(f"@{PROJ}.iam.gserviceaccount.com", "") if resp[0].get("isError") else "",
                                 "mcp": [(m["tool"], m["tenant"], m["caller"].split("@")[0]) for m in lines],
                                 "api": [(s["tenant"], s["user"].split("@")[0]) for s in SEEN[n_seen:]],
                                 "answer": " ".join(p["text"] for a in j["result"]["artifacts"] for p in a["parts"] if p["kind"] == "text")})
            assert outcomes[0] == outcomes[1], (key, outcomes)          # the caller changes nothing past the door
            PANEL[key] = outcomes[0]
        DOOR = {who: send(QG, tok)[0] for who, tok in (("none", ""), ("outsider", "OUTSIDER"), ("ui", "MEMBER"), ("chat", "CHAT"))}
    finally:
        for p in (peer, mcp):
            if p:
                p.terminate()
                p.wait(timeout=20)
        rag.shutdown()

C4, G5, T6 = OUT["card"], OUT["gate"], OUT["trace"]
assert C4.startswith("the card without a token: HTTP 403\nthe card with a token: documind_peer, version 0.0.1") and f"answers at {LANE_AGENT} over JSONRPC, A2A 1.0" in C4, C4
assert C4.rstrip().endswith("skills: model"), C4                                    # no tools: see the next two lines
# why: ADK builds the card once, at start-up, by listing the tools with no request context, and McpToolset mints the
# header only when it has one - so the listing reaches documind-mcp with no token, and Cloud Run's door refuses it
ADK = VENV / ("Lib/site-packages" if os.name == "nt" else f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages") / "google/adk"
assert "canonical_tools = await agent.canonical_tools()" in (ADK / "a2a/utils/agent_card_builder.py").read_text(encoding="utf-8")
assert "if self._header_provider and readonly_context:" in (ADK / "tools/mcp_tool/mcp_toolset.py").read_text(encoding="utf-8")
assert "final_agent_card = await card_builder.build()" in (ADK / "a2a/utils/agent_to_a2a.py").read_text(encoding="utf-8")
assert "skills = [s.get(\"id\") for s in card.get(\"skills\", [])]" in smoke_src and "in str(addr) else bad)(\"agent card\"" in smoke_src
assert "5 passed, 0 failed" in G5 and "[PASS] card refused without a token  status=403" in G5 and "[PASS] task answered  state=completed" in G5, G5
assert "[PASS] zeta refused by the roster" in G5 and "[PASS] outsider refused at the door  status=403" in G5, G5
assert re.search(r"a task, state completed, 4 messages in its history:\n  user  text .*\n  agent calls     retrieve\(query='.*'\)\n  agent receives  retrieve: 5 citations\n  agent text ", T6), T6
assert [(m["tool"], m["tenant"], m["caller"]) for m in TRACE_MCP] == [("retrieve", "acme", SA("agent"))] and TRACE_API == [{"tenant": "acme", "user": SA("mcp"), "brain": "mcp"}], (TRACE_MCP, TRACE_API)
assert DOOR == {"none": 403, "outsider": 403, "ui": 200, "chat": 200}, DOOR
assert PANEL["zeta"]["error"] == "documind-agent-sa is not on tenant 'zeta''s roster" and PANEL["zeta"]["api"] == [] and PANEL["zeta"]["state"] == "completed"
assert PANEL["documents"]["tool"] == "list_documents" and PANEL["documents"]["api"] == [] and PANEL["price"]["mcp"] == []
FAKE_LOGS = ("import json, subprocess\n"
             "class _Out:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
             f"MCP_LINES, API_ROWS = json.loads({json.dumps(json.dumps(TRACE_MCP))}), json.loads({json.dumps(json.dumps(TRACE_API))})\n"
             "def run(cmd, **kw):\n"
             "    rows = MCP_LINES if 'documind-mcp' in cmd[3] else API_ROWS\n"
             "    return _Out(json.dumps([{'jsonPayload': r} for r in rows]))\n"
             "subprocess.run = run\n")
OUT["logs"] = run_cell(LOGS_PY, FAKE_LOGS, env={"SINCE123": "YYYY-MM-DDTHH:MM:SSZ"})
assert "retrieve        tenant acme   caller documind-agent-sa" in OUT["logs"] and "user   documind-mcp-sa" in OUT["logs"], OUT["logs"]
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "perms": "run in the operator shell, in the kit (the peer's permissions, as the kit writes them; no network)",
    "card": "run in the operator shell, in the kit (the card, without a token and with one)",
    "gate": "run in the operator shell, in the kit (the module's A2A gate)",
    "trace": "run in the operator shell, in the kit (one task, and its history)",
    "logs": "run in the operator shell, in the kit (who the lane saw)",
}
OUT_LABELS = {
    "perms": "(this cell run on the kit's own files)",
    "card": "(the kit's agent.py, served by the kit's to_a2a with the image's pins, its tools listed from the kit's server.py; Cloud Run's check stood in)",
    "gate": "(the kit's smoke_agent.py against that peer; Gemini, Cloud Run's check, the tokens, rag-api and Firestore stood in, so your answer's words differ)",
    "trace": "(the same peer and stand-ins)",
    "logs": "(from a fake gcloud, filled with what that stack recorded)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: follow one task through three services
CALLERS = {"ui": "documind-ui-sa (bound on the peer)", "chat": "documind-chat-sa (bound on the peer)",
           "outsider": "documind-outsider-sa (not bound)", "none": "no token"}
REQ_LABELS = {"gratuity": "the gratuity question", "zeta": "the same, naming tenant zeta", "documents": "which documents do you hold?",
              "price": "what would 283 pages cost?"}
UI_JS = r"""var root = document.getElementById('tr'); if (!root) return;
  var P = %s, DOOR = %s, CALLERS = %s, REQS = %s, $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, html){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = html; return e; }
  function hop(cls, head, text){ var li = el('li', cls, ''); li.appendChild(el('b', '', head + ' ')); li.appendChild(document.createTextNode(text)); return li; }
  function render(){ var who = $('tr-who').value, p = P[$('tr-req').value], out = $('tr-out'), code = DOOR[who];
    out.textContent = '';
    if (code !== 200) {
      out.appendChild(hop('stop', 'Cloud Run, at documind-agent:', 'HTTP ' + code + '. The caller is not bound as an invoker, so the peer never sees the task.'));
      ['The peer', 'documind-mcp', 'rag-api', 'The task'].forEach(function(h){ out.appendChild(hop('skip', h + ':', 'never reached')); });
      return; }
    out.appendChild(hop('', 'Cloud Run, at documind-agent:', 'admits ' + CALLERS[who].split(' ')[0] + '. After this door, nothing records who asked.'));
    var args = Object.keys(p.args).map(function(k){ return k + '=' + JSON.stringify(p.args[k]); }).join(', ');
    out.appendChild(hop('', 'The peer:', 'its model calls ' + p.tool + '(' + args + ') on documind-mcp, as documind-agent-sa, with a token minted for that call.'));
    out.appendChild(hop(p.error ? 'stop' : '', 'documind-mcp:', p.error ? 'refuses: ' + p.error
      : p.mcp.length ? 'admits documind-agent-sa and logs caller ' + p.mcp[0][2] + ', tenant ' + p.mcp[0][1] + '.' : 'answers without asking who: the cost tool reads no tenant, and logs nothing.'));
    out.appendChild(hop(p.api.length ? '' : 'skip', 'rag-api:', p.api.length ? 'serves ' + p.api[0][1] + ' for ' + p.api[0][0] + ', brain mcp.'
      : p.tool === 'list_documents' ? 'not asked: the server read Firestore itself.' : 'not asked.'));
    out.appendChild(hop('', 'The task:', p.state + '. ' + p.answer)); }
  Object.keys(CALLERS).forEach(function(k){ var o = el('option', '', CALLERS[k]); o.value = k; $('tr-who').appendChild(o); });
  Object.keys(REQS).forEach(function(k){ var o = el('option', '', REQS[k]); o.value = k; $('tr-req').appendChild(o); });
  $('tr-who').addEventListener('change', render); $('tr-req').addEventListener('change', render); render();""" % (json.dumps(PANEL), json.dumps(DOOR), json.dumps(CALLERS), json.dumps(REQ_LABELS))

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"N_REQ": str(len(REQ_LABELS))}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(json.dumps(PANEL, indent=1)[:1500], DOOR)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print("kit: the chain from the kit's files; the card, the gate and the trace from the kit's agent.py over A2A, calling the kit's server.py"
      f" | {len(PANEL)} requests in the panel, answered alike for ui-sa and chat-sa | Gemini and the lane stood in")
