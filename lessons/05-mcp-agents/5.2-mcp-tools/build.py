"""Build lesson 5.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

MCP in three verbs, on the kit's own server. Expose: FastMCP turns four ordinary functions into tools - a name, a
description and an input schema read from the signature and the docstring. Discover: a client asks tools/list, a
JSON-RPC method, and gets those declarations. Invoke: tools/call with arguments; the result comes back as data, or as a
tool error the caller can read. Offline: the server imported, not run, and its tools listed in memory. Live, on your
machine: the kit's server started on localhost with your lane behind it (the roster in Firestore, rag-api for the one
retrieve()), tools/list sent raw over HTTP, retrieve called from fastmcp's client, three calls that fail in three
different places, and the one line the server logs per answered call.

Build-time proof: the offline cell runs here on the kit's server.py with fastmcp 3.4.7, the image's pin. The live cells
run here against the kit's own server, started on localhost exactly as the page starts it, with the token check, the
roster, rag-api and Firestore stood in. The panel's 126 outcomes are that server's own answers.
"""
import ast
import asyncio
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
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "5.2"
title = "<title>Lesson 5.2 Expose, discover and invoke MCP tools - the kit's server, four tools, and a local client | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
OUTSIDER = f"documind-outsider-sa@{PROJ}.iam.gserviceaccount.com"
PORT = 8121
QG = "After how many years of continuous service does gratuity become payable?"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.rpc{font-family:var(--mono);font-size:12px;background:var(--code-bg);color:var(--code-text);border-radius:8px;padding:8px 10px;margin:4px 0 8px;white-space:pre-wrap;overflow-wrap:anywhere;}
.ans{font-family:var(--mono);font-size:12.5px;padding:6px 10px;border-radius:8px;border:1px solid var(--border);overflow-wrap:anywhere;}
.ans.ok{background:var(--teal-light);color:var(--teal-dark);border-color:var(--teal);}
.ans.err{background:#fff7ed;color:#9a3412;border-color:#fdba74;}
.fs-grid{display:grid;grid-template-columns:minmax(0,9em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
SV = "services/mcp/server.py"
EXCERPTS = {
    "tool": ("services/mcp/server.py - a tool is a function: its name, its docstring and its signature are what a client discovers",
             block(SV, '@mcp.tool(name="retrieve")', end="    if not query.strip():")),
    "who": ("services/mcp/server.py - who is calling, and for which tenant: the token, then the roster",
            block(SV, "    try:\n        return iap.identity(headers, bearer_audience=SELF_URL)".split("\n")[1], n=4) + "\n...\n"
            + block(SV, "    email = caller[\"email\"]", n=9)),
    "app": ("services/mcp/server.py - the transport: streamable HTTP at /mcp, stateless",
            block(SV, 'app = mcp.http_app(path="/mcp", stateless_http=True)', n=1)),
}
assert EXCERPTS["tool"][1].startswith('@mcp.tool(name="retrieve")') and "tenant: Only if you belong to several tenants" in EXCERPTS["tool"][1]
assert "raise ToolError(f\"not authenticated: {e}\") from None" in EXCERPTS["who"][1] and "tenancy.is_member(email, named)" in EXCERPTS["who"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
sv_src = (KIT / SV).read_text(encoding="utf-8")
TOOLS = re.findall(r'@mcp\.tool(?:\(name="(\w+)"\))?\ndef (\w+)\(', sv_src)
TOOLS = [a or b for a, b in TOOLS]
assert TOOLS == ["retrieve", "list_documents", "corpus_stats", "calculate_processing_cost"], TOOLS
smoke_src = (KIT / "smoke/smoke_mcp.py").read_text(encoding="utf-8")
assert 'TOOLS = {"retrieve", "list_documents", "corpus_stats", "calculate_processing_cost"}' in smoke_src
cost_fn = sv_src[sv_src.index("def calculate_processing_cost("):sv_src.index("# ------------------------------------------------------------------ the two stores")]
assert "_caller()" not in cost_fn                                                                    # the cost tool asks nobody who they are
retrieve_fn = sv_src[sv_src.index('@mcp.tool(name="retrieve")'):sv_src.index("@mcp.tool\ndef list_documents")]
assert retrieve_fn.index("_audit(") > retrieve_fn.index("documind_tools.retrieve(") > retrieve_fn.index("_tenant_for(")   # the audit line only after success
assert "WWW-Authenticate" not in sv_src and "401" not in sv_src.replace("401 in spirit", "")                        # errors are tool results
assert 'DOC_TYPES = ("policy", "contract", "invoice", "report", "statute", "guidance", "form", "research_paper")' in sv_src
mcp_reqs = (KIT / "services/mcp/requirements.txt").read_text(encoding="utf-8")
PIN = re.search(r"^fastmcp==([\d.]+)$", mcp_reqs, re.M).group(1)
UVI = re.search(r"^uvicorn==([\d.]+)$", mcp_reqs, re.M).group(1)
assert PIN == "3.4.7"
deploy72 = (KIT / "commands/lesson-7.2.sh").read_text(encoding="utf-8")
assert "for who in documind-ui-sa documind-agent-sa documind-outsider-sa; do" in deploy72                      # who Cloud Run admits
assert 'doc_type: str = "unknown"' in (KIT / "services/ingest/contracts.py").read_text(encoding="utf-8")
# retrieve's doc_type list against lesson 10.4's registry: what a filter can find on a relabelled lane
sys.path.insert(0, str(KIT))
from shared import doc_types  # noqa: E402
LISTED = ast.literal_eval(re.search(r"^DOC_TYPES = (\(.*\))$", sv_src, re.M).group(1))
SEED = doc_types.registry_from_manifest()                                                          # object name -> its class
ingest_src = (KIT / "services/ingest/main.py").read_text(encoding="utf-8")
MEDIA = set(ast.literal_eval(re.search(r"^MEDIA_TYPES = (\{.*?\})$", ingest_src, re.M | re.S).group(1)).values())
HELD = {m["doc_type"] for m in json.loads(doc_types.MANIFEST.read_text(encoding="utf-8"))} | MEDIA | {doc_types.UNKNOWN}
NO_CLASS = [t for t in LISTED if t not in doc_types.CLASSES]
UNLISTED = [c for c in doc_types.CLASSES if c not in LISTED]
assert NO_CLASS == ["form", "research_paper"] and UNLISTED == ["transcript"], (NO_CLASS, UNLISTED)   # the page names all three
assert not HELD & set(NO_CLASS), HELD                         # no seeded, relabelled or worker-written row can carry either
assert "doc_type: Filter by type (policy, contract, invoice, form, research_paper, all)" in (KIT / "services/chat/tools.py").read_text(encoding="utf-8")
WORDS = {6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}

# ------------------------------------------------------------------ the cells
PIP = f'python -m pip install -q "fastmcp=={PIN}" "uvicorn=={UVI}"   # the MCP image\'s pins, in the operator venv\npython -c \'import fastmcp; print("fastmcp", fastmcp.__version__)\''

EXPOSE_PY = """import asyncio, logging, sys, textwrap, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
import services.mcp.server as server               # the kit's server, imported, not run
logging.disable(logging.WARNING)                   # its INFO lines; step 6 reads them from a running server
from fastmcp import Client
async def main():
    async with Client(server.mcp) as c:            # in memory: no HTTP and no identity, and listing needs neither
        info = c.initialize_result
        print(f"server {info.serverInfo.name}, protocol {info.protocolVersion}")
        print(f"instructions: {info.instructions[:78]}...")
        for t in await c.list_tools():
            s = t.inputSchema
            print(f"{t.name}: {textwrap.shorten(t.description.splitlines()[0], 66, placeholder='...')}")
            for p, spec in s["properties"].items():
                kind = spec.get("type") or " or ".join(a["type"] for a in spec.get("anyOf", []))
                need = "required" if p in s.get("required", []) else f"default {spec.get('default')!r}"
                print(f"   {p:16} {kind:14}  {need:19} {textwrap.shorten(spec.get('description', ''), 32, placeholder='...')}")
asyncio.run(main())"""

START = (f'PYTHONPATH=. SELF_URL=http://localhost:{PORT} RAG_API_URL="$API" GOOGLE_CLOUD_PROJECT="$PROJECT" \\\n'
         f'DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" \\\n'
         f'  python -m uvicorn services.mcp.server:app --port {PORT} > /tmp/mcp121.log 2>&1 &\n'
         'export MCP_PID=$!\n'
         f'export MCP_TOKEN="$(tok http://localhost:{PORT})"   # an ID token minted for THIS server, with your roster member\'s email\n'
         f'export NO_EMAIL_TOKEN="$(gcloud auth print-identity-token --audiences=http://localhost:{PORT} \\\n'
         '  --impersonate-service-account="documind-ui-sa@$PROJECT.iam.gserviceaccount.com")"   # the same account, no email\n'
         f'until curl -sf http://localhost:{PORT}/health; do sleep 1; done; echo')

DISCOVER_PY = f"""import json, os, urllib.request
rpc = {{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}}      # one JSON-RPC request; this server needs no session first
req = urllib.request.Request("http://localhost:{PORT}/mcp", method="POST", data=json.dumps(rpc).encode(),
                             headers={{"Authorization": "Bearer " + os.environ["MCP_TOKEN"], "Content-Type": "application/json",
                                      "Accept": "application/json, text/event-stream"}})
with urllib.request.urlopen(req) as r:
    body = r.read().decode()
    print(f"HTTP {{r.status}}, {{r.headers['Content-Type']}}, first line: {{body.splitlines()[0]}}")
msg = json.loads(next(line[6:] for line in body.splitlines() if line.startswith("data: ")))
print(f"tools/list: {{len(msg['result']['tools'])}} tools")
for t in msg["result"]["tools"]:
    s = t["inputSchema"]
    need = s.get("required", [])
    print(f"  {{t['name']:26}} needs {{', '.join(need) or 'nothing':12}} may take {{', '.join(p for p in s['properties'] if p not in need)}}")"""

INVOKE_PY = f"""import asyncio, logging, os, textwrap
logging.disable(logging.WARNING)
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError
def client(token):                                 # the transport smoke_mcp.py uses, pointed at your machine
    return Client(StreamableHttpTransport("http://localhost:{PORT}/mcp", headers={{"Authorization": f"Bearer {{token}}"}}))
async def main():
    async with client(os.environ["MCP_TOKEN"]) as c:
        out = (await c.call_tool("retrieve", {{"query": "{QG}", "tenant": "acme"}})).data
        print(f"retrieve: answerable {{out['answerable']}}, {{len(out['citations'])}} citations, confidence {{out['confidence']}}")
        print(f"  {{(out.get('answer') or '')[:74]!r}}")
        for n, cite in enumerate(out["citations"][:3], 1):
            print(f"  [{{n}}] {{cite['source_uri'].rsplit('/', 1)[-1]}} p.{{cite.get('page')}}  {{cite['quote'][:36]!r}}")
        for label, args in (("an argument it refuses", {{"query": "notice period", "doc_type": "memo"}}),
                            ("a tenant not on your roster", {{"query": "notice period", "tenant": "initech"}})):
            try:
                await c.call_tool("retrieve", args)
            except ToolError as e:
                print(textwrap.fill(f"{{label}}: {{e}}", 88, subsequent_indent="    "))
    async with client(os.environ["NO_EMAIL_TOKEN"]) as c:
        print(f"a token without an email lists {{len(await c.list_tools())}} tools, and calls:")
        try:
            await c.call_tool("retrieve", {{"query": "notice period"}})
        except ToolError as e:
            print(f"  {{e}}")
asyncio.run(main())"""

LOG_PY = """import json
for line in open("/tmp/mcp121.log"):
    if line.startswith('{"event": "mcp_call"'):
        e = json.loads(line)
        rest = {k: v for k, v in e.items() if k not in ("event", "tool", "tenant", "caller", "via", "query_sha")}
        print(f"  mcp_call {e['tool']}  tenant {e['tenant']}  caller {e['caller'].split('@')[0]}  via {e['via']}  {rest}")"""


def heredoc(body: str, prefix: str = "", python: str = "python") -> str:
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


CELLS = {
    "pip": PIP,
    "expose": heredoc(EXPOSE_PY),
    "start": START,
    "discover": heredoc(DISCOVER_PY),
    "invoke": heredoc(INVOKE_PY),
    "stop": 'kill "$MCP_PID"\n' + heredoc(LOG_PY),
}

T = Path(tempfile.mkdtemp(prefix="lesson121-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ}


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


# ---- step 3: the server imported, its tools listed in memory
OUT = {"expose": run_cell(EXPOSE_PY, cwd=KIT)}
E = OUT["expose"]
assert E.startswith("server DocuMind, protocol ") and E.count("\n   ") == 10, E
for name in TOOLS:
    assert f"\n{name}: " in "\n" + E, (name, E)
OUT["pip"] = f"fastmcp {PIN}\n"

# ---- steps 4 to 6: the kit's server on localhost:PORT, as the page starts it, with the lane stood in
EMPTY = "The corpus holds nothing near this question"
QUOTES = ["rendered continuous service for not less than five years, on his superannuation, or on his retirement",
          "the completion of continuous service of five years shall not be necessary where the termination is due to death",
          "for every completed year of service or part thereof in excess of six months, at the rate of fifteen days' wages",
          "an employee shall be said to be in continuous service for a period if he has been in uninterrupted service",
          "Gratuity is paid under the Payment of Gratuity Act, 1972, after five years of continuous service with the company"]
ANS = "Gratuity becomes payable after not less than five years of continuous service [1]."
FILES = ["payment_of_gratuity_act_1972.pdf"] * 3 + ["hr_policy_2026.md"] * 2
CLASS_OF = {f: SEED[f"acme/{f}"]["doc_type"] for f in set(FILES)}                                 # the class the relabel gave each
assert CLASS_OF == {"payment_of_gratuity_act_1972.pdf": "statute", "hr_policy_2026.md": "policy"}, CLASS_OF


class Rag(BaseHTTPRequestHandler):                 # a stand-in rag-api: a doc_type filter keeps the rows of its class, as on a relabelled lane
    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        want = (req.get("filters") or {}).get("doc_type")
        keep = [i for i in range(5) if not want or CLASS_OF[FILES[i]] in (want if isinstance(want, list) else [want])]
        if not keep:                               # rag-api's empty-pool refusal: no passage, no model call
            return reply(self, 200, {"answer": EMPTY + ".", "citations": [], "answerable": False, "confidence": "low"})
        cites = [{"chunk_id": f"{req['tenant_id']}:payment_of_gratuity_act_1972#{4 + i}", "source_uri": f"gs://{PROJ}-uploads/{req['tenant_id']}/"
                  + FILES[i], "page": 2 if i < 3 else 1,
                  "quote": QUOTES[i], "score": round(0.91 - i * 0.03, 2)} for i in keep]
        reply(self, 200, {"answer": ANS, "citations": cites, "answerable": True, "confidence": "high"})


rag = ThreadingHTTPServer(("127.0.0.1", 0), Rag)
threading.Thread(target=rag.serve_forever, daemon=True).start()
with socket.socket() as s:
    assert s.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} is taken on this machine"
DOCS = {"acme": [("hr_policy_2026.md", "indexed", 41), ("inv_2026_0412.md", "indexed", 3), ("payment_of_gratuity_act_1972.pdf", "indexed", 38),
                 ("pune_visitor_rules.md", "processing", None)],
        "zeta": [("hr_policy_zeta_2026.md", "indexed", 36), ("scan_0917.pdf", "failed", None)]}
STAND_CLASS = {f"{t}/{f}": SEED[f"{t}/{f}"]["doc_type"] for t, rows in DOCS.items() for f, _, n in rows if n}   # every indexed one is registered
assert STAND_CLASS == {"acme/hr_policy_2026.md": "policy", "acme/inv_2026_0412.md": "invoice",
                       "acme/payment_of_gratuity_act_1972.pdf": "statute", "zeta/hr_policy_zeta_2026.md": "policy"}, STAND_CLASS
STAND = f"""import json, os, sys
sys.path.insert(0, ".")
import shared.documind_tools as dt, shared.iap as iap, shared.tenancy as tenancy
dt._id_token = lambda audience: "TOKEN"
WHO = {{"MEMBER": {UI!r}, "OUTSIDER": {OUTSIDER!r}}}
ROSTER = {{{UI!r}: ["acme", "zeta", "globex"]}}
def identity(headers, bearer_audience=None):       # stands in for Google's signature check; the rest is the kit's
    who = headers.get("authorization", "").removeprefix("Bearer ")
    if who not in WHO:
        raise iap.IapError("the bearer token carries no verified email")
    return {{"email": WHO[who], "via": "iam", "aud": bearer_audience}}
iap.identity = identity
tenancy.tenant_for = lambda email: (ROSTER.get(email) or [None])[0]
tenancy.is_member = lambda email, tenant: tenant in ROSTER.get(email, [])
DOCS = {DOCS!r}
CLASS = {STAND_CLASS!r}                            # the classes lesson 10.4's relabel wrote on the chunk rows
class Snap:
    def __init__(self, d): self.d = d
    def to_dict(self): return self.d
class Q:
    def __init__(self, name): self.name, self.tenant = name, None
    def where(self, filter): self.tenant = filter.value; return self
    def select(self, fields): return self
    def stream(self):
        for file, status, chunks in DOCS.get(self.tenant, []):
            uri = f"gs://{PROJ}-uploads/{{self.tenant}}/{{file}}"
            if self.name == "documents":
                yield Snap({{"tenant_id": self.tenant, "gcs_uri": uri, "status": status, "chunks": chunks, "indexed_at": "2026-09-2{{0 if chunks else 3}}T10:00:00+00:00"}})
            else:
                for i in range(chunks or 0):
                    yield Snap({{"doc_type": CLASS.get(f"{{self.tenant}}/{{file}}", "unknown"), "kind": "table" if i == 0 and file.endswith(".pdf") else "text", "source_uri": uri}})
class DB:
    def collection(self, name): return Q(name)
import services.mcp.server as server
server._db = lambda: DB()
import uvicorn
uvicorn.run(server.app, host="127.0.0.1", port={PORT}, log_level="warning")
"""
LOG = T / "mcp121.log"
env_srv = {**ENV, "SELF_URL": f"http://localhost:{PORT}", "RAG_API_URL": f"http://127.0.0.1:{rag.server_address[1]}", "GOOGLE_CLOUD_PROJECT": PROJ}
with open(LOG, "w", encoding="utf-8") as logf:
    srv = subprocess.Popen([sys.executable, "-c", STAND], cwd=str(KIT), env=env_srv, stdout=logf, stderr=subprocess.STDOUT)
try:
    for _ in range(100):
        try:
            with urllib.request.urlopen(f"http://localhost:{PORT}/health", timeout=1) as r:
                HEALTH = r.read().decode()
            break
        except Exception:                          # noqa: BLE001 - not up yet
            time.sleep(0.2)
    else:
        raise SystemExit("the server did not start: " + LOG.read_text(encoding="utf-8")[-800:])
    assert json.loads(HEALTH) == {"status": "ok", "profile": "gcp", "self_url": f"http://localhost:{PORT}"}, HEALTH
    OUT["start"] = HEALTH + "\n"
    OUT["discover"] = run_cell(DISCOVER_PY, env={"MCP_TOKEN": "MEMBER"})
    OUT["invoke"] = run_cell(INVOKE_PY, env={"MCP_TOKEN": "MEMBER", "NO_EMAIL_TOKEN": "NOEMAIL"})
    time.sleep(0.5)
    PAGE_LOG = T / "page.log"                      # what the server logged for the page's own calls, before the panel's
    PAGE_LOG.write_text(LOG.read_text(encoding="utf-8"), encoding="utf-8")

    # the panel: every choice it offers, sent to the same running server
    SPEC = {"retrieve": [["query", [["gratuity", QG], ["blank", " "]]], ["doc_type", [["all", "all"], ["statute", "statute"], ["form", "form"], ["memo", "memo"]]],
                         ["tenant", [["", None], ["zeta", "zeta"], ["initech", "initech"]]]],
            "list_documents": [["status", [["indexed", "indexed"], ["all", "all"], ["archived", "archived"]]], ["tenant", [["", None], ["zeta", "zeta"], ["initech", "initech"]]]],
            "corpus_stats": [["tenant", [["", None], ["zeta", "zeta"], ["initech", "initech"]]]],
            "calculate_processing_cost": [["total_pages", [["283", 283], ["0", 0]]], ["processing_type", [["standard", "standard"], ["priority", "priority"], ["express", "express"]]]]}
    CALLERS = {"MEMBER": "documind-ui-sa: on acme, zeta and globex", "OUTSIDER": "documind-outsider-sa: on no roster", "NOEMAIL": "a token that carries no email"}

    def combos(spec):
        if not spec:
            yield [], {}
            return
        (arg, opts), rest = spec[0], spec[1:]
        for key, val in opts:
            for keys, args in combos(rest):
                yield [key] + keys, ({arg: val} if val is not None else {}) | args

    def summary(tool, data):
        if tool == "retrieve":
            return f"answerable {str(data['answerable']).lower()}, {len(data['citations'])} citations: {(data.get('answer') or '')[:60]}"
        if tool == "list_documents":
            return f"tenant {data['tenant']}, {len(data['documents'])} {data['status']} documents: " + ", ".join(d["file"] for d in data["documents"])[:70]
        if tool == "corpus_stats":
            return f"tenant {data['tenant']}, {data['chunks']} chunks in {data['documents']} documents, by type {data['by_doc_type']}"
        return f"{data['total_pages']} pages at {data['processing_type']}: USD {data['cost_usd']}, Rs {data['cost_inr']}"

    async def panel():
        from fastmcp import Client
        from fastmcp.client.transports import StreamableHttpTransport
        from fastmcp.exceptions import ToolError
        out = {}
        for who in CALLERS:
            async with Client(StreamableHttpTransport(f"http://localhost:{PORT}/mcp", headers={"Authorization": f"Bearer {who}"})) as c:
                for tool, spec in SPEC.items():
                    for keys, args in combos(spec):
                        try:
                            out["|".join([tool] + keys + [who])] = ["ok", summary(tool, (await c.call_tool(tool, args)).data)]
                        except ToolError as e:
                            out["|".join([tool] + keys + [who])] = ["err", str(e)]
        return out

    import logging
    logging.disable(logging.WARNING)
    OUTCOMES = asyncio.run(panel())
finally:
    srv.terminate()
    srv.wait(timeout=20)
    rag.shutdown()
OUT["stop"] = run_cell(LOG_PY.replace("/tmp/mcp121.log", PAGE_LOG.as_posix()))
assert len(OUTCOMES) == 126, len(OUTCOMES)

D, I = OUT["discover"], OUT["invoke"]
assert D.startswith("HTTP 200, text/event-stream, first line: event: message") and "tools/list: 4 tools" in D, D
assert all(re.search(rf"^  {t}\s", D, re.M) for t in TOOLS), D
assert "retrieve: answerable True, 5 citations, confidence high" in I and "an argument it refuses: doc_type must be one of" in I, I
assert f"a tenant not on your roster: {UI} is not on tenant 'initech''s roster" in " ".join(I.split()), I
assert "a token without an email lists 4 tools, and calls:\n  not authenticated: the bearer token carries no verified email" in I, I
S6 = OUT["stop"]
assert S6.count("mcp_call") == 1 and "mcp_call retrieve  tenant acme  caller documind-ui-sa  via iam  {'answerable': True, 'citations': 5, 'error': None}" in S6, S6
# the panel's facts the page names
O = OUTCOMES
assert O["calculate_processing_cost|283|priority|NOEMAIL"][0] == "ok"                                        # the cost tool asks nobody
assert O["retrieve|blank|all||NOEMAIL"] == ["err", "query cannot be empty"]                                  # arguments first
assert O["retrieve|gratuity|memo||NOEMAIL"][1].startswith("doc_type must be one of")
assert O["retrieve|gratuity|all||NOEMAIL"] == ["err", "not authenticated: the bearer token carries no verified email"]
assert O["retrieve|gratuity|all||OUTSIDER"][1].endswith("is on no tenant's roster - an operator adds members with `make roster`")
assert O["retrieve|gratuity|statute||MEMBER"][1].startswith("answerable true, 3 citations: ")              # a class: the Act's rows
assert O["retrieve|gratuity|form||MEMBER"][1].startswith("answerable false, 0 citations: " + EMPTY)        # listed, but no class
assert O["corpus_stats||MEMBER"][1].endswith("by type {'policy': 41, 'statute': 38, 'invoice': 3}"), O["corpus_stats||MEMBER"]
assert O["list_documents|archived||MEMBER"] == ["err", "status must be indexed, processing, failed or all"]
assert O["corpus_stats|zeta|MEMBER"][1].startswith("tenant zeta, 36 chunks in 1 documents")
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "pip": "run in the operator shell, in the kit (fastmcp in the operator venv)",
    "expose": "run in the operator shell, in the kit (the server imported and listed in memory; no network)",
    "start": "run in the operator shell, in the kit (the kit's server on your machine, in the background)",
    "discover": "run in the operator shell, in the kit (tools/list, raw)",
    "invoke": "run in the operator shell, in the kit (tools/call from fastmcp's client)",
    "stop": "run in the operator shell, in the kit (stop the server, read what it logged)",
}
OUT_LABELS = {
    "pip": "",
    "expose": f"(this cell run on the kit's own server.py with fastmcp {PIN})",
    "start": "(the kit's own server's /health, started as this cell starts it)",
    "discover": "(the kit's own server, with the token check stood in)",
    "invoke": "(the kit's own server, with the token check, the roster and rag-api stood in; your answer and sources will differ)",
    "stop": "(the line the kit's server logged for the answered call)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: compose a tools/call, see the kit's server answer
UI_SPEC = {tool: [[arg, [[key, val] for key, val in opts]] for arg, opts in spec] for tool, spec in SPEC.items()}
UI_JS = r"""var root = document.getElementById('mc'); if (!root) return;
  var SPEC = %s, CALLERS = %s, O = %s, $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = text; return e; }
  function label(arg, key, val){ return val === null ? '(not sent)' : arg === 'query' ? (key === 'blank' ? '" " (blank)' : 'the gratuity question') : String(val); }
  function args(){ var tool = $('mc-tool').value; return SPEC[tool].map(function(a, i){ return [a[0], a[1][+$('mc-a' + i).value]]; }); }
  function render(){ var tool = $('mc-tool').value, who = $('mc-who').value, chosen = args(), sent = {};
    chosen.forEach(function(a){ if (a[1][1] !== null) { sent[a[0]] = a[1][1]; } });
    $('mc-rpc').textContent = JSON.stringify({jsonrpc: '2.0', id: 2, method: 'tools/call', params: {name: tool, arguments: sent}}, null, 1);
    var o = O[[tool].concat(chosen.map(function(a){ return a[1][0]; })).concat([who]).join('|')];
    $('mc-ans').className = 'ans ' + o[0]; $('mc-ans').textContent = (o[0] === 'ok' ? 'result: ' : 'tool error: ') + o[1]; }
  function build(){ var tool = $('mc-tool').value, box = $('mc-args'); box.textContent = '';
    SPEC[tool].forEach(function(a, i){ var l = el('label', '', a[0]), s = el('select', '', ''); s.id = 'mc-a' + i;
      a[1].forEach(function(opt, j){ var o = el('option', '', label(a[0], opt[0], opt[1])); o.value = j; s.appendChild(o); });
      s.addEventListener('change', render); l.appendChild(s); box.appendChild(l); });
    render(); }
  Object.keys(SPEC).forEach(function(t){ var o = el('option', '', t); o.value = t; $('mc-tool').appendChild(o); });
  Object.keys(CALLERS).forEach(function(k){ var o = el('option', '', CALLERS[k]); o.value = k; $('mc-who').appendChild(o); });
  $('mc-tool').addEventListener('change', build); $('mc-who').addEventListener('change', render); build();""" % (json.dumps(UI_SPEC), json.dumps(CALLERS), json.dumps(OUTCOMES))

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"PIN": PIN, "PORT": str(PORT), "N_OUT": str(len(OUTCOMES)),
         "N_LISTED": WORDS[len(LISTED)], "N_CLASSED": WORDS[len(LISTED) - len(NO_CLASS)]}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(STATS)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: the server's tools listed in memory, then the kit's server on localhost:{PORT} answering the page's own cells"
      f" | {len(OUTCOMES)} panel outcomes from that server | the lane stood in")
