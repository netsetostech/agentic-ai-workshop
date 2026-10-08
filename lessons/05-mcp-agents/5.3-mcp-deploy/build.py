"""Build lesson 5.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Deploy MCP and verify who gets through. Three doors stand in front of a tenant's documents: Cloud Run's IAM (roles/
run.invoker, bound per caller by the deploy script), the server's token check (a Google ID token minted for its own
address, carrying an email), and the roster (the tenant must list the caller, and a named tenant must too). Behind
them the server calls rag-api as its own account, documind-mcp-sa, which every golden roster lists - so rag-api sees
the deputy, never the caller. Offline: the door as the kit writes it down - the deploy script's flags and invoker
loop, and lane.py's roster_plan. Live: the kit's own build-and-deploy, the service read back against the script,
make smoke-mcp (the module's gate: four checks, the outsider refused by the roster), one call at each door, and the
two logs - the MCP server's line naming the caller, rag-api's row naming the deputy.

Build-time proof: the offline cell runs here on the kit's lesson-7.2.sh and lane.py. The gate's lines are the kit's
smoke_mcp.py, and the door cell's answers, against the kit's own server.py on localhost, with Cloud Run's IAM check,
the token signatures, rag-api and Firestore stood in and the roster taken from roster_plan. The panel's answers are
that server's; its Cloud Run statuses are the stand-in's, and the page says so.
"""
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

LESSON = "5.3"
title = "<title>Lesson 5.3 Deploy MCP and verify authorized access - three doors, one deputy, and the gate | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
SA = lambda name: f"documind-{name}-sa@{PROJ}.iam.gserviceaccount.com"  # noqa: E731
PORT = 8122
QG = "After how many years of continuous service does gratuity become payable?"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,10em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid .pass{color:var(--teal-dark);font-weight:600;}
.fs-grid .stop{color:#9a3412;font-weight:600;}
.fs-grid .skip{color:var(--slate-light);}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
DEP, SV, LANE = "commands/lesson-7.2.sh", "services/mcp/server.py", "commands/lane.py"
EXCERPTS = {
    "deploy": ("commands/lesson-7.2.sh - the deploy: no unauthenticated calls, its own account, its own address as the audience",
               block(DEP, "gcloud run deploy documind-mcp \\", n=10)),
    "knock": ("commands/lesson-7.2.sh - who may knock: roles/run.invoker, bound per caller",
              block(DEP, "for who in documind-ui-sa documind-agent-sa documind-outsider-sa; do", n=5)),
    "roster": ("commands/lane.py - who is on which roster: the surfaces' accounts on the three golden tenants, the peer on one",
               block(LANE, "    sa = lambda name:", n=6)),
    "deputy": ("services/mcp/server.py - the caller's tenant is checked here; rag-api is then called as the server's own account",
               block(SV, "    caller = _caller()\n    tenant_id = _tenant_for(caller, tenant)".split("\n")[0], nth=1, n=4)),
}
assert "--no-allow-unauthenticated" in EXCERPTS["deploy"][1] and "--service-account=documind-mcp-sa@$PROJECT.iam.gserviceaccount.com" in EXCERPTS["deploy"][1]
assert 'for name in ("ui", "mcp", "chat"):' in EXCERPTS["roster"][1] and 'plan.append(("acme", sa("agent")))' in EXCERPTS["roster"][1]
assert "documind_tools.retrieve(query, tenant_id" in EXCERPTS["deputy"][1] and "assertion" not in EXCERPTS["deputy"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
dep_src, sv_src = ((KIT / p).read_text(encoding="utf-8") for p in (DEP, SV))
DEPLOY_BLOCK = dep_src[dep_src.index("# ---- DEPLOY ----"):dep_src.index("# ---- SMOKE ----")]
assert "gcloud builds submit" not in DEPLOY_BLOCK and "gcloud builds submit" in (KIT / "commands/lesson-12.8.sh").read_text(encoding="utf-8")   # 7.2 does not build
assert "add-iam-policy-binding" in DEPLOY_BLOCK and "remove-iam-policy-binding" not in DEPLOY_BLOCK and "set-iam-policy" not in DEPLOY_BLOCK        # bindings only added
retrieve_fn = sv_src[sv_src.index('@mcp.tool(name="retrieve")'):sv_src.index("@mcp.tool\ndef list_documents")]
assert "assertion" not in retrieve_fn and 'brain="mcp"' in retrieve_fn                                                   # the caller is not forwarded
assert retrieve_fn.index("_audit(") > retrieve_fn.index("_tenant_for(")                                                   # refused calls are not audited
main_src = (KIT / "services/rag-api/main.py").read_text(encoding="utf-8")
assert '"tenant": req.tenant_id, "user": user["email"],' in main_src                                                   # rag-api's row names its caller
mk = (KIT / "Makefile").read_text(encoding="utf-8")
assert 'echo ">> building $(IMAGE_REPO)/$$svc:$(GIT_SHA) from services/$$dir"' in mk and 'echo ">> $$f (DEPLOY block)"' in mk
assert 'echo ">> $$who may mint tokens as $$sa"' in mk and "for sa in documind-ui-sa documind-outsider-sa; do" in mk
assert "DOCUMIND_OUTSIDER_SA=documind-outsider-sa@$(PROJECT).iam.gserviceaccount.com \\\n\t  $(PY) smoke/smoke_mcp.py" in mk
# The build's account (24 September 2026): the kit names none, so Cloud Build runs as the project's default build
# account. On the lane that was the Compute Engine default account with no roles, and the first build stopped at "does
# not have storage.objects.get access" on the source gcloud had just uploaded. The box after the deploy grants that
# account what this build does: read its source, push its image, write its log lines.
BUILD_RULE = mk[mk.index("\nbuild: guard-project"):mk.index("\ntf-backend: guard-project")]
cb_src = (KIT / "cloudbuild.yaml").read_text(encoding="utf-8")
assert "--config=cloudbuild.yaml" in BUILD_RULE and "--service-account" not in BUILD_RULE and "serviceAccount" not in cb_src
assert "logging: CLOUD_LOGGING_ONLY" in cb_src and "images:\n  - ${_IMAGE}" in cb_src                                 # its log lines, its push
assert "IMAGE_REPO = $(REGION)-docker.pkg.dev/$(PROJECT)/documind" in mk
assert 'repository_id = "documind"' in (KIT / "terraform/registry.tf").read_text(encoding="utf-8")
smoke_src = (KIT / "smoke/smoke_mcp.py").read_text(encoding="utf-8")
assert 'out = asyncio.run(call(outsider, "retrieve", {"query": QUESTION, "tenant": TENANT}))' in smoke_src            # the outsider names acme
sys.path[:0] = [str(KIT), str(KIT / "commands")]
from lane import roster_plan  # noqa: E402
PLAN, _ = roster_plan(PROJ, "acme", [])
ROSTER = {}
for t, e in PLAN:
    ROSTER.setdefault(e, []).append(t)
assert ROSTER[SA("mcp")] == ["acme", "zeta", "globex"] and ROSTER[SA("agent")] == ["acme"] and SA("outsider") not in ROSTER
INVOKERS = re.search(r"for who in ([\w\- ]+); do\n  gcloud run services add-iam-policy-binding documind-mcp", DEPLOY_BLOCK).group(1).split()
assert INVOKERS == ["documind-ui-sa", "documind-agent-sa", "documind-outsider-sa"]

# ------------------------------------------------------------------ the cells
DOOR_PY = """import re, sys
sys.path[:0] = [".", "commands"]
from lane import roster_plan
deploy = open("commands/lesson-7.2.sh").read().split("# ---- DEPLOY ----")[1].split("# ---- SMOKE ----")[0]
print("documind-mcp, as commands/lesson-7.2.sh deploys it:")
print("  " + "  ".join("--" + f.replace("@$PROJECT.iam.gserviceaccount.com", "") for f in
      re.findall(r"--(no-allow-unauthenticated|ingress=\\S+|service-account=\\S+|min-instances=\\S+)", deploy)))
env = dict(kv.split("=", 1) for kv in re.search(r'--set-env-vars="\\^\\|\\^([^"]+)"', deploy).group(1).split("|"))
for k in ("SELF_URL", "RAG_API_URL", "FASTMCP_STATELESS_HTTP", "RAG_TIMEOUT_S"):
    print(f"  {k}={env[k]}")
callers = re.search(r"for who in ([\\w\\- ]+); do", deploy).group(1).split()
print("who may call it (roles/run.invoker):", ", ".join(callers))
rosters = {}
for tenant, email in roster_plan("PROJECT", "acme", [])[0]:
    rosters.setdefault(email.split("@")[0], []).append(tenant)
print("the tenants each caller may read through it (lane.py's roster_plan):")
for who in callers:
    print(f"  {who:22} {', '.join(rosters.get(who, [])) or 'none'}")
print(f"the account rag-api sees for every MCP retrieval: documind-mcp-sa, on {', '.join(rosters['documind-mcp-sa'])}")"""

DEPLOY = 'make build deploy-services PROJECT="$PROJECT" REGION="$REGION" SERVICES=mcp SCRIPTS=commands/lesson-7.2.sh ADMIN_EMAILS="$ME"'

ACCESS = ('BUILD_SA="$NUMBER-compute@developer.gserviceaccount.com"   # the account the 403 names\n'
          'gcloud storage buckets add-iam-policy-binding "gs://${PROJECT}_cloudbuild" \\\n'
          '  --member="serviceAccount:$BUILD_SA" --role=roles/storage.objectViewer --format=none\n'
          'gcloud artifacts repositories add-iam-policy-binding documind --location="$REGION" --project="$PROJECT" \\\n'
          '  --member="serviceAccount:$BUILD_SA" --role=roles/artifactregistry.writer --format=none\n'
          'gcloud projects add-iam-policy-binding "$PROJECT" \\\n'
          '  --member="serviceAccount:$BUILD_SA" --role=roles/logging.logWriter --condition=None --format=none')

READBACK_PY = """import json, os, subprocess
def gc(*a):
    return json.loads(subprocess.run(["gcloud", "run", "services", *a, "documind-mcp", "--region", os.environ["REGION"],
                                      "--project", os.environ["PROJECT"], "--format", "json"], capture_output=True, text=True, check=True).stdout)
svc, policy = gc("describe"), gc("get-iam-policy")
spec, meta = svc["spec"]["template"]["spec"], svc["spec"]["template"]["metadata"]
env = {e["name"]: e.get("value") for e in spec["containers"][0].get("env", [])}
print(f"  serving     {svc['status']['latestReadyRevisionName']} at {svc['status']['url']}")
print(f"  runs as     {spec['serviceAccountName'].split('@')[0]}")
print(f"  ingress     {svc['metadata']['annotations'].get('run.googleapis.com/ingress')}")
print(f"  SELF_URL    {env.get('SELF_URL')}")
invokers = sorted(m.split(":", 1)[1].split("@")[0] for b in policy.get("bindings", []) if b["role"] == "roles/run.invoker" for m in b["members"])
print(f"  invokers    {', '.join(invokers)}")
print(f"  the script  {', '.join(sorted(['documind-agent-sa', 'documind-outsider-sa', 'documind-ui-sa']))} - "
      + ("the same" if invokers == sorted(["documind-agent-sa", "documind-outsider-sa", "documind-ui-sa"]) else "DIFFERENT: someone bound more, or less"))"""

GATE = ('export MCP="https://documind-mcp-$NUMBER.$REGION.run.app" SINCE122="$(date -u +%FT%TZ)"\n'
        'make smoke-mcp PROJECT="$PROJECT" REGION="$REGION"   # the module\'s gate: health, tools/list, retrieve, the outsider refused')

DOORS_PY = """import json, os, subprocess, urllib.error, urllib.request
MCP, P = os.environ["MCP"], os.environ["PROJECT"]
def mint(account, email=True, audience=MCP):      # a Google ID token, as gcloud mints it for the smoke test
    cmd = ["gcloud", "auth", "print-identity-token", f"--audiences={audience}", f"--impersonate-service-account={account}@{P}.iam.gserviceaccount.com"]
    return subprocess.run(cmd + (["--include-email"] if email else []), capture_output=True, text=True, check=True).stdout.strip()
def call(token, arguments):                        # one raw tools/call to retrieve; which door answered
    rpc = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "retrieve", "arguments": arguments}}
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urllib.request.urlopen(urllib.request.Request(MCP + "/mcp", data=json.dumps(rpc).encode(), headers=headers), timeout=180) as r:
            result = json.loads(next(line[6:] for line in r.read().decode().splitlines() if line.startswith("data: ")))["result"]
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code} - Cloud Run, before the server ran"
    if result.get("isError"):
        return "tool error - " + result["content"][0]["text"].replace(f"@{P}.iam.gserviceaccount.com", "")
    return f"answered - answerable {result['structuredContent']['answerable']}, {len(result['structuredContent']['citations'])} citations"
Q = {"query": "After how many years of continuous service does gratuity become payable?"}
for label, token, args in (("no token", None, Q),
                           ("ui-sa, a token for rag-api's address", mint("documind-ui-sa", audience=os.environ["API"]), Q),
                           ("ui-sa, no email in the token", mint("documind-ui-sa", email=False), Q),
                           ("the outsider, naming acme", mint("documind-outsider-sa"), {**Q, "tenant": "acme"}),
                           ("ui-sa, naming zeta", mint("documind-ui-sa"), {**Q, "tenant": "zeta"})):
    print(f"  {label:37} {call(token, args)}")"""

LOGS_PY = """import json, os, subprocess
def rows(service, flt):
    f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}" AND {flt} '
         f'AND timestamp>="{os.environ["SINCE122"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    return [e["jsonPayload"] for e in json.loads(out or "[]")]
print("documind-mcp, a line per answered call - who asked:")
for j in rows("documind-mcp", 'jsonPayload.event="mcp_call"'):
    print(f"  {j['tool']:9} tenant {j['tenant']:6} caller {j['caller'].split('@')[0]}")
print("documind-api, a row per retrieval it served for the MCP server - who it served:")
for j in rows("documind-api", 'jsonPayload.brain="mcp"'):
    print(f"  retrieve  tenant {j['tenant']:6} user   {j['user'].split('@')[0]}")"""


def heredoc(body: str, prefix: str = "", python: str = "python") -> str:
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


CELLS = {
    "door": heredoc(DOOR_PY),
    "deploy": DEPLOY,
    "access": ACCESS,
    "readback": heredoc(READBACK_PY),
    "gate": GATE,
    "doors": heredoc(DOORS_PY),
    "logs": "sleep 20   # Cloud Logging needs a moment to show the lines\n" + heredoc(LOGS_PY),
}

T = Path(tempfile.mkdtemp(prefix="lesson122-"))
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


# ---- step 3: the door as the kit writes it down
OUT = {"door": run_cell(DOOR_PY, cwd=KIT)}
D3 = OUT["door"]
assert "who may call it (roles/run.invoker): documind-ui-sa, documind-agent-sa, documind-outsider-sa" in D3, D3
assert "  documind-agent-sa      acme\n" in D3 and "  documind-outsider-sa   none\n" in D3, D3
assert D3.rstrip().endswith("documind-mcp-sa, on acme, zeta, globex"), D3

# ---- step 4: the deploy, abridged (it is Cloud Build's and gcloud's output), and the service read back from a fake gcloud
OUT["deploy"] = (f">> building asia-south1-docker.pkg.dev/{PROJ}/documind/mcp:COMMIT from services/mcp\n"
                 "Creating temporary archive of ... file(s) totalling ... MiB before compression.\n...\n"
                 f"DONE ... asia-south1-docker.pkg.dev/{PROJ}/documind/mcp:COMMIT\n"
                 ">> commands/lesson-7.2.sh (DEPLOY block)\n"
                 f"Deploying container to Cloud Run service [documind-mcp] in project [{PROJ}] region [asia-south1]\n...\n"
                 "Service URL: https://documind-mcp-NUMBER.asia-south1.run.app\n"
                 "Updated IAM policy for service [documind-mcp].   (three times: ui, agent, outsider)\n...\n"
                 ">> you@example.com may mint tokens as documind-ui-sa\n>> you@example.com may mint tokens as documind-outsider-sa\n")
SVC = {"status": {"latestReadyRevisionName": "documind-mcp-00004-k7w", "url": "https://documind-mcp-NUMBER.asia-south1.run.app"},
       "metadata": {"annotations": {"run.googleapis.com/ingress": "all"}},
       "spec": {"template": {"metadata": {}, "spec": {"serviceAccountName": SA("mcp"), "containers": [{"env": [
           {"name": "SELF_URL", "value": "https://documind-mcp-NUMBER.asia-south1.run.app"}, {"name": "RAG_TIMEOUT_S", "value": "90"}]}]}}}}
POLICY = {"bindings": [{"role": "roles/run.invoker", "members": [f"serviceAccount:{SA(n)}" for n in ("ui", "agent", "outsider")]}]}
FAKE_READ = ("import json, sys, types\n"
             "class _Out:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
             f"SVC, POLICY = json.loads({json.dumps(json.dumps(SVC))}), json.loads({json.dumps(json.dumps(POLICY))})\n"
             "def run(cmd, **kw): return _Out(json.dumps(SVC if cmd[3] == 'describe' else POLICY))\n"
             "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
OUT["readback"] = run_cell(READBACK_PY, FAKE_READ)
assert "  invokers    documind-agent-sa, documind-outsider-sa, documind-ui-sa" in OUT["readback"] and OUT["readback"].rstrip().endswith("the same"), OUT["readback"]

# ---- steps 5 and 6: the kit's server on localhost behind a stand-in of Cloud Run's IAM check
SEEN = []                                          # what rag-api was asked, and by whom


class Rag(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        SEEN.append({"tenant": req["tenant_id"], "user": SA("mcp"), "brain": req.get("brain")})    # the token is the server's own
        cites = [{"chunk_id": f"{req['tenant_id']}:payment_of_gratuity_act_1972#{4 + i}", "source_uri": f"gs://{PROJ}-uploads/{req['tenant_id']}/doc.pdf",
                  "page": 2, "quote": "not less than five years", "score": round(0.9 - i * 0.03, 2)} for i in range(5)]
        reply(self, 200, {"answer": "Five years of continuous service [1].", "citations": cites, "answerable": True, "confidence": "high"})


rag = ThreadingHTTPServer(("127.0.0.1", 0), Rag)
threading.Thread(target=rag.serve_forever, daemon=True).start()
with socket.socket() as s:
    assert s.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} is taken on this machine"
WHO = {"MEMBER": SA("ui"), "OUTSIDER": SA("outsider"), "AGENT": SA("agent")}
STAND = f"""import sys
sys.path.insert(0, ".")
import shared.documind_tools as dt, shared.iap as iap, shared.tenancy as tenancy
dt._id_token = lambda audience: "MCP-SA-TOKEN"
WHO, ROSTER = {WHO!r}, {ROSTER!r}
def identity(headers, bearer_audience=None):       # Google's signature check stood in; the rest is the kit's
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
        for file, n in (("hr_policy_2026.md", 41), ("payment_of_gratuity_act_1972.pdf", 38)):
            uri = "gs://{PROJ}-uploads/" + self.tenant + "/" + file
            if self.name == "documents":
                yield Snap({{"tenant_id": self.tenant, "gcs_uri": uri, "status": "indexed", "chunks": n, "indexed_at": "2026-09-20T10:00:00+00:00"}})
            else:
                for i in range(n):
                    yield Snap({{"doc_type": "unknown", "kind": "text", "source_uri": uri}})
class DB:
    def collection(self, name): return Q(name)
import services.mcp.server as server
server._db = lambda: DB()
class FrontDoor:                                   # Cloud Run's IAM check, stood in: 403 without a token, 401 for another address's
    def __init__(self, app): self.app = app
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            auth = dict(scope["headers"]).get(b"authorization", b"").decode()
            code = 403 if not auth else 401 if auth.endswith("WRONG_AUDIENCE") else 0
            if code:
                await send({{"type": "http.response.start", "status": code, "headers": [(b"content-type", b"text/html")]}})
                await send({{"type": "http.response.body", "body": b"<html><title>Error</title></html>"}})
                return
        await self.app(scope, receive, send)
import uvicorn
uvicorn.run(FrontDoor(server.app), host="127.0.0.1", port={PORT}, log_level="warning")
"""
LOG = T / "mcp122.log"
URL = f"http://localhost:{PORT}"
env_srv = {**ENV, "SELF_URL": URL, "RAG_API_URL": f"http://127.0.0.1:{rag.server_address[1]}", "GOOGLE_CLOUD_PROJECT": PROJ}
with open(LOG, "w", encoding="utf-8") as logf:
    srv = subprocess.Popen([sys.executable, "-c", STAND], cwd=str(KIT), env=env_srv, stdout=logf, stderr=subprocess.STDOUT)
# gcloud stood in for minting: the account, the audience and --include-email decide which token the server sees
FAKE_MINT = ("import subprocess\n"
             "class _Out:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
             f"MCP = {URL!r}\n"
             "def run(cmd, **kw):\n"
             "    aud = next(c.split('=', 1)[1] for c in cmd if c.startswith('--audiences='))\n"
             "    acct = next(c.split('=', 1)[1] for c in cmd if c.startswith('--impersonate-service-account='))\n"
             "    if aud != MCP: return _Out('X.WRONG_AUDIENCE')\n"
             "    if '--include-email' not in cmd: return _Out('MEMBER_NOEMAIL')\n"
             "    return _Out('OUTSIDER' if 'outsider' in acct else 'AGENT' if 'agent' in acct else 'MEMBER')\n"
             "subprocess.run = run                        # only gcloud is stood in; the rest of subprocess stays\n")
try:
    for _ in range(100):
        try:
            urllib.request.urlopen(urllib.request.Request(URL + "/health", headers={"Authorization": "Bearer MEMBER"}), timeout=1).read()
            break
        except Exception:                          # noqa: BLE001 - not up yet
            time.sleep(0.2)
    else:
        raise SystemExit("the server did not start: " + LOG.read_text(encoding="utf-8")[-800:])
    # the gate: the kit's smoke_mcp.py, as make smoke-mcp runs it
    gate = run_cell("import runpy\nrunpy.run_path('smoke/smoke_mcp.py', run_name='__main__')\n", FAKE_MINT, cwd=KIT, env={
        "DOCUMIND_MCP_URL": URL, "DOCUMIND_IMPERSONATE_SA": SA("ui"), "DOCUMIND_OUTSIDER_SA": SA("outsider")})
    OUT["gate"] = gate.replace(URL, "https://documind-mcp-NUMBER.asia-south1.run.app").strip("\n") + "\n"
    OUT["doors"] = run_cell(DOORS_PY, FAKE_MINT, env={"MCP": URL, "API": "https://documind-api-NUMBER.asia-south1.run.app"})

    # the panel: every caller, tenant and tool, sent to the same server behind the same stand-in door
    CALLERS = {"NONE": "no token at all", "WRONG": "documind-ui-sa, a token for rag-api's address", "NOEMAIL": "documind-ui-sa, no email in the token",
               "MEMBER": "documind-ui-sa: on acme, zeta, globex", "AGENT": "documind-agent-sa, the A2A peer: on acme", "OUTSIDER": "documind-outsider-sa: on no roster"}
    TENANTS = ["", "acme", "zeta", "globex", "initech"]
    TOOLS = ["retrieve", "list_documents", "corpus_stats", "calculate_processing_cost", "tools/list"]
    TOKEN = {"NONE": None, "WRONG": "X.WRONG_AUDIENCE", "NOEMAIL": "MEMBER_NOEMAIL", "MEMBER": "MEMBER", "AGENT": "AGENT", "OUTSIDER": "OUTSIDER"}

    def args_for(tool, tenant):
        base = {"retrieve": {"query": QG}, "list_documents": {}, "corpus_stats": {}, "calculate_processing_cost": {"total_pages": 283}}[tool]
        return base | ({"tenant": tenant} if tenant and tool != "calculate_processing_cost" else {})

    async def panel():
        from fastmcp import Client
        from fastmcp.client.transports import StreamableHttpTransport
        from fastmcp.exceptions import ToolError
        import httpx
        out = {}
        for who, token in TOKEN.items():
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            if who in ("NONE", "WRONG"):
                code = httpx.post(URL + "/mcp", headers=headers, json={}).status_code
                for tool in TOOLS:
                    for tenant in TENANTS:
                        out[f"{who}|{tool}|{tenant}"] = {"door": code, "answer": f"HTTP {code}", "ok": False, "rag": 0}
                continue
            async with Client(StreamableHttpTransport(URL + "/mcp", headers=headers)) as c:
                for tool in TOOLS:
                    for tenant in TENANTS:
                        before = len(SEEN)
                        try:
                            if tool == "tools/list":
                                answer, ok = f"{len(await c.list_tools())} tools", True
                            else:
                                data = (await c.call_tool(tool, args_for(tool, tenant))).data
                                answer, ok = {"retrieve": lambda d: f"answerable {str(d['answerable']).lower()}, {len(d['citations'])} citations",
                                              "list_documents": lambda d: f"tenant {d['tenant']}: {len(d['documents'])} documents",
                                              "corpus_stats": lambda d: f"tenant {d['tenant']}: {d['chunks']} chunks",
                                              "calculate_processing_cost": lambda d: f"USD {d['cost_usd']}, Rs {d['cost_inr']}"}[tool](data), True
                        except ToolError as e:
                            answer, ok = str(e).replace(f"@{PROJ}.iam.gserviceaccount.com", ""), False
                        out[f"{who}|{tool}|{tenant}"] = {"door": 200, "answer": answer, "ok": ok,
                                                        "rag": SEEN[-1]["tenant"] if len(SEEN) > before else 0}
        return out

    import logging
    logging.disable(logging.WARNING)
    SEEN.clear()
    before_panel = LOG.read_text(encoding="utf-8")
    OUTCOMES = asyncio.run(panel())
finally:
    srv.terminate()
    srv.wait(timeout=20)
    rag.shutdown()

G, DR = OUT["gate"], OUT["doors"]
assert "4 passed, 0 failed" in G and "[PASS] outsider refused" in G and "is not on tenant 'acme''s roster" in G, G
assert "[PASS] tools/list  ['calculate_processing_cost', 'corpus_stats', 'list_documents', 'retrieve']" in G, G
EXP = {"no token": "HTTP 403 - Cloud Run, before the server ran", "ui-sa, a token for rag-api's address": "HTTP 401 - Cloud Run, before the server ran",
       "ui-sa, no email in the token": "tool error - not authenticated: the bearer token carries no verified email",
       "the outsider, naming acme": "tool error - documind-outsider-sa is not on tenant 'acme''s roster",
       "ui-sa, naming zeta": "answered - answerable True, 5 citations"}
for label, want in EXP.items():
    assert re.search(rf"^  {re.escape(label)}\s+{re.escape(want)}$", DR, re.M), (label, DR)
# the two logs, from what the stack above recorded: the server's mcp_call lines, and rag-api's view of the same calls
MCP_LINES = [json.loads(line) for line in before_panel.splitlines() if line.startswith('{"event": "mcp_call"')]
assert [(m["tenant"], m["caller"]) for m in MCP_LINES] == [("acme", SA("ui")), ("zeta", SA("ui"))], MCP_LINES
API_ROWS = [{"tenant": m["tenant"], "user": SA("mcp"), "brain": "mcp"} for m in MCP_LINES]
FAKE_LOGS = ("import json, sys, types\n"
             "class _Out:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
             f"MCP_LINES, API_ROWS = json.loads({json.dumps(json.dumps(MCP_LINES))}), json.loads({json.dumps(json.dumps(API_ROWS))})\n"
             "def run(cmd, **kw):\n"
             "    rows = MCP_LINES if 'documind-mcp' in cmd[3] else API_ROWS\n"
             "    return _Out(json.dumps([{'jsonPayload': r} for r in rows]))\n"
             "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
OUT["logs"] = run_cell(LOGS_PY, FAKE_LOGS, env={"SINCE122": "YYYY-MM-DDTHH:MM:SSZ"})
assert "retrieve  tenant acme   caller documind-ui-sa" in OUT["logs"] and OUT["logs"].count("user   documind-mcp-sa") == 2, OUT["logs"]
O = OUTCOMES
assert len(O) == 6 * 5 * 5 and O["NONE|retrieve|"]["answer"] == "HTTP 403" and O["WRONG|tools/list|"]["answer"] == "HTTP 401"
assert O["OUTSIDER|tools/list|"]["ok"] and O["NOEMAIL|tools/list|"]["ok"] and O["NOEMAIL|calculate_processing_cost|"]["ok"]
assert O["AGENT|retrieve|zeta"]["answer"] == "documind-agent-sa is not on tenant 'zeta''s roster" and O["AGENT|retrieve|"]["rag"] == "acme"
assert O["MEMBER|list_documents|globex"]["ok"] and O["MEMBER|list_documents|globex"]["rag"] == 0          # Firestore, not rag-api
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "door": "run in the operator shell, in the kit (the door as the kit writes it down; no network)",
    "deploy": "run in the operator shell, in the kit (build the image, deploy it, bind its callers)",
    "access": "run in the operator shell, once, as a project owner, only if the build stopped at storage.objects.get",
    "readback": "run in the operator shell, in the kit (the service as deployed, against the script)",
    "gate": "run in the operator shell, in the kit (the module's gate)",
    "doors": "run in the operator shell, in the kit (one call at each door)",
    "logs": "run in the operator shell, in the kit (both sides of the answered calls)",
}
OUT_LABELS = {
    "door": "(this cell run on the kit's own lesson-7.2.sh and lane.py)",
    "deploy": "(abridged: Cloud Build and gcloud print much more)",
    "readback": "(from a fake gcloud; your revision name differs)",
    "gate": "(the kit's smoke_mcp.py against the kit's server.py on localhost; Cloud Run's check, the signatures, rag-api and Firestore stood in)",
    "doors": "(the same stand-ins; the two HTTP statuses are the Cloud Run stand-in's, and your lane's come from Cloud Run itself)",
    "logs": "(from a fake gcloud, filled with what the stand-in stack recorded)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: which door stops the call
UI_JS = r"""var root = document.getElementById('dr'); if (!root) return;
  var O = %s, CALLERS = %s, TENANTS = %s, TOOLS = %s, $ = function(id){ return document.getElementById(id); };
  var NO_TENANT = {'calculate_processing_cost': 1, 'tools/list': 1}, NO_ID = NO_TENANT;
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = text; return e; }
  function render(){ var who = $('dr-who').value, tool = $('dr-tool').value, tenant = NO_TENANT[tool] ? '' : $('dr-ten').value;
    $('dr-ten').disabled = !!NO_TENANT[tool];
    var o = O[who + '|' + tool + '|' + tenant], rows = [], iam = o.door === 200;
    rows.push(['Cloud Run', iam ? 'admits the call' : 'stops it: HTTP ' + o.door, iam ? 'pass' : 'stop']);
    var tokenStop = /^not authenticated/.test(o.answer), rosterStop = /roster/.test(o.answer);
    rows.push(['The token check', !iam ? 'never reached' : NO_ID[tool] ? 'not asked: this call reads no tenant' : tokenStop ? 'stops it' : 'passes',
               !iam || NO_ID[tool] ? 'skip' : tokenStop ? 'stop' : 'pass']);
    rows.push(['The roster', !iam || tokenStop ? 'never reached' : NO_ID[tool] ? 'not asked' : rosterStop ? 'stops it' : 'passes',
               !iam || tokenStop || NO_ID[tool] ? 'skip' : rosterStop ? 'stop' : 'pass']);
    rows.push(['The answer', (o.ok ? 'answered: ' : iam ? 'tool error: ' : 'refused: ') + o.answer, o.ok ? 'pass' : 'stop']);
    rows.push(['rag-api sees', o.rag ? 'documind-mcp-sa, asking for ' + o.rag + ', brain mcp' : o.ok && (tool === 'list_documents' || tool === 'corpus_stats')
               ? 'nothing: the server reads Firestore itself, as documind-mcp-sa' : 'nothing', o.rag ? 'pass' : 'skip']);
    var out = $('dr-out'); out.textContent = '';
    rows.forEach(function(r){ out.appendChild(el('b', '', r[0])); out.appendChild(el('span', r[2], r[1])); }); }
  Object.keys(CALLERS).forEach(function(k){ var o = el('option', '', CALLERS[k]); o.value = k; $('dr-who').appendChild(o); });
  TOOLS.forEach(function(t){ var o = el('option', '', t); o.value = t; $('dr-tool').appendChild(o); });
  TENANTS.forEach(function(t){ var o = el('option', '', t || '(none named)'); o.value = t; $('dr-ten').appendChild(o); });
  ['dr-who', 'dr-tool', 'dr-ten'].forEach(function(id){ $(id).addEventListener('change', render); });
  $('dr-who').value = 'OUTSIDER'; $('dr-ten').value = 'acme'; render();""" % (json.dumps(OUTCOMES), json.dumps(CALLERS), json.dumps(TENANTS), json.dumps(TOOLS))

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"N_OUT": str(len(OUTCOMES)), "PORT": str(PORT)}

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
print(f"kit: the door from lesson-7.2.sh and roster_plan, the gate from smoke_mcp.py and the doors against the kit's server.py"
      f" | {len(OUTCOMES)} panel outcomes from that server behind a Cloud Run stand-in | live cells against stand-ins")
