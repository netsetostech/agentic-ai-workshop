"""Build lesson 5.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

A tool is a contract: a name, a description and the arguments the model may fill, and a result shape the runtime
returns. The kit keeps one retrieve() (shared/documind_tools.py) and adapts it per brain (services/chat/tools.py):
the tenant and the person's assertion reach the tool through the runtime context, never through an argument the
model sees. The direct brain has no loop - one retrieve(), rag-api's own grounded answer - and is the floor the
agent brains must beat. The lane walk: the chat service deployed in the lane's region (the kit's chat script
named us-central1 everywhere; fixed in this change), what the model reads, the one retrieve() from the shell, the
direct brain (retrieve in tool_calls), the LangChain loop on the same question and on a cost question, and the rows
both services write.

Build-time proof: the model-facing schema the page's cell prints (read from the source, no LangChain needed on the
learner's machine) equals LangChain's own tool_call_schema for every tool; _summary() and DirectBrain.answer() are
executed on stand-ins for the widget's traces; the cost tool is the kit's own. The cells run against stand-ins: the
retrieve cell against a local stub of rag-api, the chat cells against a local stub of the chat service, the rows
cell against a fake gcloud.
"""
import ast
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "5.1"
title = "<title>Lesson 5.1 Understand tool contracts and the direct agent loop - what the model reads, what the runtime adds, one retrieve() for every brain, and the floor they must beat | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
Q_GRAT = "After how many years of continuous service does gratuity become payable?"
Q_COST = "The ACME handbook has 283 pages. What would processing it cost at the priority tier?"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.tc-schema{font-family:var(--mono);font-size:12px;color:var(--navy);white-space:pre-wrap;margin:4px 0;}
.pc-steps{margin:6px 0 0;padding-left:20px;}
.pc-steps li{margin:4px 0;}
.pc-steps li.model{color:#1e3a8a;}.pc-steps li.tool{color:#065f46;}.pc-steps li.rt{color:#7c2d12;}.pc-steps li.skip{color:#94a3b8;}
.pc-out{font-family:var(--mono);font-size:12.5px;padding:5px 10px;border-radius:8px;display:inline-block;margin-top:6px;background:#f1f5f9;color:var(--navy);}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
DT, CT, BR, AG = "shared/documind_tools.py", "services/chat/tools.py", "services/chat/brains.py", "services/chat/agent.py"
EXCERPTS = {
    "one": ("shared/documind_tools.py - retrieve(): THE single retrieval entry point, and failures returned as data",
            block(DT, "def retrieve(query: str, tenant_id: str, top_k: int = 5,", n=3) + "\n...\n"
            + block(DT, '    payload: dict[str, Any] = {', n=18) + "\n...\n"
            + block(DT, "    except requests.RequestException as exc:", n=4)),
    "adapter": ("services/chat/tools.py - the chat adapter: the tenant from the runtime, never from the model, and search(), where every brain's retrieve ends",
                block(CT, "@tool", n=10) + "\n...\n" + block(CT, "    tenant_id = _ctx(runtime, \"tenant_id\")", n=5) + "\n\n\n"
                + block(CT, "def search(", n=2) + "\n...\n" + block(CT, "        answer = documind_tools.retrieve(", n=4) + "\n...\n"
                + block(CT, "    # A call cut at its budget (limits.timed_tool_call)", n=4) + "\n...\n"
                + block(CT, "    if cited is not None and delivered:", n=3)),
    "summary": ("services/chat/brains.py - _summary() and _turn(): the same four keys from every brain, for this turn",
                block(BR, "def _summary(messages", end="# -----")),
    "direct": ("services/chat/brains.py - DirectBrain: no loop, one retrieve(), rag-api's own answer",
               block(BR, "class DirectBrain:", n=19)),
    "request": ("services/chat/agent.py - the request has nowhere to name a tenant",
                block(AG, "class ChatRequest(BaseModel):", n=11)),
    "turn": ("services/chat/agent.py - the tenant looked up, then carried in the runtime context",
             block(AG, "        tenant_id = tenant_for(user[\"email\"])", n=1) + "\n...\n" + block(AG, "    out = brain.answer(", n=5)),
}
assert EXCERPTS["one"][1].count("return {\"error\": \"document retrieval is unavailable\",") == 1
assert "runtime: ToolRuntime = None) -> dict:" in EXCERPTS["adapter"][1] and "documind_tools.retrieve(" in EXCERPTS["adapter"][1]
assert "    return search(query, doc_type, top_k, tenant_id=tenant_id, assertion=assertion, brain=brain," in EXCERPTS["adapter"][1]
assert EXCERPTS["adapter"][1].rstrip().endswith("return out") and "_number(out[\"citations\"], cited)" in EXCERPTS["adapter"][1]
assert '"refusals": [m.name for m in messages if isinstance(m, ToolMessage) and m.status == "error"],' in EXCERPTS["summary"][1]
assert '"citations": sorted(citations or [], key=lambda c: c["n"]),' in EXCERPTS["summary"][1] and "raise ValueError(" in EXCERPTS["summary"][1]
assert EXCERPTS["summary"][1].rstrip().endswith('return turn, {"messages": [HumanMessage(content=question, id=turn)]}, ctx')
assert 'ctx = {**context, "cited": []}' in EXCERPTS["summary"][1] and "limits.meter_of(ctx)" in EXCERPTS["summary"][1]
assert EXCERPTS["direct"][1].rstrip().endswith('"citations": r["citations"]}')
assert "brain: Optional[Literal[\"langchain\", \"langgraph\", \"adk\", \"direct\"]] = None" in EXCERPTS["request"][1]
assert 'context={"tenant_id": tenant_id, "user_id": user["email"],' in EXCERPTS["turn"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
dt_src, ct_src, br_src, ag_src = ((KIT / p).read_text(encoding="utf-8") for p in (DT, CT, BR, AG))
main_src = (KIT / "services/rag-api/main.py").read_text(encoding="utf-8")
ROUTES = re.findall(r'@app\.(?:get|post)\("([^"]+)"', main_src)
assert ROUTES == ["/health", "/version", "/v1/sources", "/ready", "/v1/query", "/v1/stream", "/v1/passages"], ROUTES   # one retrieval-only route
assert "passages=" not in ct_src and "passages=" not in br_src                                              # which the chat brains do not call yet
assert 'out["answer"] = answer["answer"]    # rag-api\'s grounded answer; the direct brain\'s whole job' in dt_src
chat_row = re.search(r'logger\.info\(json\.dumps\(\{"event": "chat",(.*?)\}\)\)', ag_src, re.S).group(1)
assert '"tool_calls"' in chat_row and all(f'"{k}": used["{k}"]' in chat_row for k in ("model_calls", "tokens_in", "cost_usd", "rag_cost_usd"))   # the chat row prices the turn (10.3)
assert 'WHERE jsonPayload.event IN ("query", "stream", "media")' in (KIT / "terraform/sql/tenant_daily.sql").read_text(encoding="utf-8")   # no chat rows in the month
assert 'service: str = "documind-api"' in (KIT / "evals/usage_rows.py").read_text(encoding="utf-8")                                       # make usage: rag-api's rows
assert "get_usage_stats" not in ct_src.split('"""', 2)[2] and "RATES" not in ct_src                         # no stub, no second price list
assert "        return documind_tools.calculate_processing_cost(total_pages, num_documents, processing_type)" in ct_src
assert "        raise ToolException(str(exc)) from None" in ct_src and "calculate_processing_cost.handle_tool_error = True" in ct_src
assert '"tool_calls": ["retrieve"]' in br_src and br_src.count('"tool_calls": ["retrieve"]') == 3            # the floor's list is written, not chosen
assert 'BRAINS = ("langchain", "langgraph", "adk", "direct")' in br_src and 'DEFAULT_BRAIN = os.environ.get("DOCUMIND_BRAIN", "langchain")' in br_src
assert "(`python tools/check_one_retrieval.py deploy/` does it properly)" in dt_src                          # a gate the kit does not ship
assert not (KIT / "tools").exists()
assert "location      = var.region" in (KIT / "terraform/registry.tf").read_text(encoding="utf-8")                  # the registry is in REGION
assert '.where("email", "==", email.lower()).limit(1).get())' in (KIT / "shared/tenancy.py").read_text(encoding="utf-8")
chat_sh = (KIT / "commands/lesson-12.8.sh").read_text(encoding="utf-8")
dep = chat_sh[chat_sh.index("# ---- DEPLOY ----"):]
assert dep.count("${REGION:-us-central1}") == 14 and dep.replace("${REGION:-us-central1}", "").count("us-central1") == 0   # this change
# who may invoke the chat service: the loop's list, the UI's account and the outsider first, then the Desk's six,
# each bound only once Terraform has created it
INVOKERS = re.search(r"^for who in ([^;]+); do$", dep.replace("\\\n", " "), re.M).group(1).split()
assert INVOKERS[:2] == ["documind-ui-sa", "documind-outsider-sa"] and len(INVOKERS) == 8 and INVOKERS[-1] == "documind-gchat-sa"
assert all(re.fullmatch(r"documind-eval[a-z]+-sa", a) for a in INVOKERS[2:7])
assert '|| { echo ">> $who does not exist yet (terraform/desk.tf: make plan up; documind-gchat-sa only with GCHAT_DOOR=true) - not bound"; continue; }' in dep
# the Google Chat bridge's account exists only on a lane planned with GCHAT_DOOR=true (off by default): the loop's line
NOT_BOUND = re.search(r'echo "(>> \$who does not exist yet [^"]*)"', dep).group(1).replace("$who", INVOKERS[-1])
assert "GCHAT_DOOR ?= false" in (KIT / "mk/agents.mk").read_text(encoding="utf-8")
mk = (KIT / "Makefile").read_text(encoding="utf-8")
assert "commands/lesson-12.4.sh commands/lesson-12.8.sh" in mk and re.search(r"^REGION\s+\?= us-central1$", mk, re.M)
assert "DOCUMIND_CHAT_URL=https://documind-chat-$$NUMBER.$(REGION).run.app" in mk

# the chat tools, imported the way the service imports them, for the model-facing schemas
sys.path[:0] = [str(KIT), str(KIT / "services/chat")]
spec = importlib.util.spec_from_file_location("chat_tools_101", KIT / CT)
chat_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat_tools)
from shared import documind_tools as shared_tools  # noqa: E402
SCHEMAS = {}
for t in chat_tools.TOOLS:
    s = t.tool_call_schema.model_json_schema()
    SCHEMAS[t.name] = {"params": [[k, v.get("type"), v.get("default", None), k in s.get("required", [])] for k, v in s["properties"].items()],
                       "doc": t.description.strip().splitlines()[0]}
assert "runtime" not in json.dumps(SCHEMAS) and "tenant" not in json.dumps(SCHEMAS)
COST = chat_tools.calculate_processing_cost.invoke({"total_pages": 283, "processing_type": "priority"})
assert COST == {"num_documents": 1, "total_pages": 283, "processing_type": "priority", "rate_per_page": 0.12, "cost_usd": 33.96, "cost_inr": 2886.6}, COST
assert COST == shared_tools.calculate_processing_cost(283, processing_type="priority")                      # one function, delegated to
TIER = chat_tools.calculate_processing_cost.invoke({"total_pages": 283, "processing_type": "express"})
try:
    shared_tools.calculate_processing_cost(283, processing_type="express")
    raise AssertionError("the shared cost tool accepted an unknown tier")
except ValueError as exc:
    assert TIER == str(exc), TIER                                                                          # refused, as the shared one refuses it

# ------------------------------------------------------------------ _summary() and DirectBrain.answer(), executed on stand-ins
cls_src = {n.name: ast.get_source_segment(br_src, n) for n in ast.parse(br_src).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}


class ToolMessage:                                  # the only thing _summary asks of a ToolMessage: name, status
    def __init__(self, name, status="success"):
        self.name, self.status, self.content = name, status, ""


class AIMessage:
    def __init__(self, content="", tool_calls=None):
        self.content, self.tool_calls = content, tool_calls or []


ns = {"ToolMessage": ToolMessage}
exec(cls_src["_summary"], ns)
TRACES = {                                             # the widget's langchain traces: model turns and tool results
    "policy": [AIMessage(tool_calls=[{"name": "retrieve", "args": {"query": Q_GRAT, "top_k": 5}, "id": "1"}]), ToolMessage("retrieve"),
               AIMessage("After five years of continuous service [1].")],
    "cost": [AIMessage(tool_calls=[{"name": "retrieve", "args": {"query": "ACME handbook page count"}, "id": "1"}]), ToolMessage("retrieve"),
             AIMessage(tool_calls=[{"name": "calculate_processing_cost", "args": {"total_pages": 283, "processing_type": "priority"}, "id": "2"}]),
             ToolMessage("calculate_processing_cost"), AIMessage("USD 33.96, about Rs 2,886.60, at the priority tier.")],
    "zeta": [AIMessage(tool_calls=[{"name": "retrieve", "args": {"query": "zeta travel reimbursement cap"}, "id": "1"}]), ToolMessage("retrieve"),
             AIMessage("I can only search your own organisation's documents, and they hold ACME's cap, not zeta's.")],
}
SUMMARIES = {k: ns["_summary"](v) for k, v in TRACES.items()}
assert SUMMARIES["cost"]["tool_calls"] == ["retrieve", "calculate_processing_cost"] and all(not s["refusals"] for s in SUMMARIES.values())
seen = {}
dns = {"documind_tools": types.SimpleNamespace(retrieve=lambda q, **kw: seen.update(q=q, **kw) or {"citations": [{"chunk_id": "acme:SHA#3"}], "answerable": True,
                                                                                                          "confidence": "high", "answer": "..."}),
       "SYSTEM": "", "build_llm": None, "limits": importlib.import_module("limits")}     # the kit's limits.py: stdlib only
exec(cls_src["DirectBrain"], dns)
d = dns["DirectBrain"]().answer(Q_COST, config={}, context={"tenant_id": "acme", "assertion": "", "brain": "direct"})
assert d["tool_calls"] == ["retrieve"] and seen["tenant_id"] == "acme" and seen["brain"] == "direct" and seen["top_k"] == 5, (d, seen)

# ------------------------------------------------------------------ the cells
CONTRACT_PY = """import ast
src = open("services/chat/tools.py", encoding="utf-8").read()
for fn in ast.parse(src).body:
    if isinstance(fn, ast.FunctionDef) and any(getattr(d, "id", "") == "tool" for d in fn.decorator_list):
        a = fn.args.args
        dflt = [None] * (len(a) - len(fn.args.defaults)) + fn.args.defaults
        shown = [f"{x.arg}: {ast.unparse(x.annotation)}" + (f" = {ast.unparse(v)}" if v is not None else "") for x, v in zip(a, dflt) if x.arg != "runtime"]
        hidden = [x.arg for x in a if x.arg == "runtime"]
        print(f"  {fn.name}({', '.join(shown)})" + (f"    hidden: {hidden[0]}" if hidden else ""))
        print(f"      {ast.get_docstring(fn).splitlines()[0]}")
from shared.documind_tools import calculate_processing_cost   # the function the chat's cost tool hands its arguments to
try:
    calculate_processing_cost(283, processing_type="express")
except ValueError as exc:
    print(f"  'express' refused: {exc}")"""

RETRIEVE_PY = """import time
from shared.documind_tools import retrieve
t = time.time()
r = retrieve("After how many years of continuous service does gratuity become payable?", tenant_id="acme", top_k=5)
print(f"  {len(r['citations'])} citations | answerable {r['answerable']} | confidence {r['confidence']} | {time.time() - t:.1f} s")
if r["citations"]:
    print("  first:", {k: r["citations"][0].get(k) for k in ("chunk_id", "page", "score")})
print("  rag-api's own answer:", (r.get("answer") or r.get("error") or "")[:90])"""

CHAT_PY = """import json, os, urllib.error, urllib.request
def text(answer):   # a chat service built before 24 September 2026 can send Gemini's content blocks instead of a string
    return answer if isinstance(answer, str) else "".join(p if isinstance(p, str) else p.get("text", "") for p in answer
                                                          if isinstance(p, str) or p.get("type") == "text")
body = json.dumps({"question": os.environ["Q"], "session_id": "lesson101-" + os.environ["B"], "brain": os.environ["B"]}).encode()
req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", data=body, method="POST",
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
try:
    a = json.load(urllib.request.urlopen(req, timeout=300))
    n = [c["n"] for c in a.get("citations", []) if "n" in c]   # an agent brain numbers this turn's citations from 1
    print(f"  {a['brain']:9} tool_calls {a['tool_calls']}  refusals {a['refusals']}  citations {len(a.get('citations', []))}"
          + (f" n {n}" if n else "") + f"  {a['latency_ms']} ms")
    print(f"      {text(a['answer'])[:96]}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}  {e.read().decode(errors='replace')[:100]}")"""

ROWS_PY = """import json, os, subprocess
def rows(service, event):
    f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}" AND jsonPayload.event="{event}" '
         f'AND timestamp>="{os.environ["SINCE101"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "30",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    return [e["jsonPayload"] for e in json.loads(out or "[]")]
print("  rag-api, one row per retrieve():")
for j in rows("documind-api", "query"):
    print(f"    brain {j.get('brain', ''):9}  in {j['tokens_in']:>6}  out {j['tokens_out']:>4}  Rs {j['cost_usd'] * 85:.4f}  {j['latency_ms']:>5} ms")
print("  the chat service, one row per turn:")
for j in rows("documind-chat", "chat"):
    print(f"    brain {j['brain']:9}  tool_calls {j['tool_calls']}  {j['latency_ms']:>6} ms  (keys: {', '.join(sorted(j))})")"""

WHERE_PY = """import json, sys
s = json.load(sys.stdin)
env = {e["name"]: e.get("value") for e in s["spec"]["template"]["spec"]["containers"][0].get("env", [])}
print("  RAG_API_URL", env.get("RAG_API_URL"), "| SELF_URL", env.get("SELF_URL"), "| DOCUMIND_BRAIN", env.get("DOCUMIND_BRAIN"))"""
WHERE_ONE = "; ".join(WHERE_PY.splitlines())
assert "'" not in WHERE_ONE                            # it goes inside single quotes on the page


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


CELLS = {
    "deploy": 'make deploy-services PROJECT="$PROJECT" REGION="$REGION" SCRIPTS=commands/lesson-12.8.sh ADMIN_EMAILS="$ME"',
    "where": ('export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"\n'
              'gcloud run services describe documind-chat --region "$REGION" --project "$PROJECT" --format=json \\\n'
              f"  | python -c '{WHERE_ONE}'\n"
              'curl -s "$CHAT/health" -H "Authorization: Bearer $(tok "$CHAT")"; echo'),
    "contract": heredoc(CONTRACT_PY),
    "retrieve": heredoc(RETRIEVE_PY, 'export SINCE101="$(date -u +%FT%TZ)"\nDOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" RAG_API_URL="$API" '),
    "direct": ("chat10() {   # one /v1/chat turn as documind-ui-sa: $1 = the brain, $2 = the question\n"
               "TOKEN=\"$(tok \"$CHAT\")\" B=\"$1\" Q=\"$2\" python - <<'PY'\n" + CHAT_PY + "\nPY\n}\n"
               f'chat10 direct "{Q_GRAT}"'),
    "loop": (f'chat10 langchain "{Q_GRAT}"\n'
             f'chat10 langchain "{Q_COST}"\n'
             f'chat10 direct "{Q_COST}"'),
    "rows": heredoc(ROWS_PY),
}
assert "; " in CELLS["where"] and "import json, sys; s = json.load(sys.stdin)" in CELLS["where"]

# ------------------------------------------------------------------ run the cells against stand-ins
T = Path(tempfile.mkdtemp(prefix="lesson101-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "TOKEN": "TOKEN",
       "SINCE101": "YYYY-MM-DDTHH:MM:SSZ"}


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T, stdin: str | None = None, argv: list | None = None) -> str:
    cmd = [sys.executable] + (argv or ["-"])
    r = subprocess.run(cmd, input=(stdin if stdin is not None else prelude + body), cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout


OUT = {"contract": run_cell(CONTRACT_PY, cwd=KIT)}
PYT = {"string": "str", "integer": "int"}
for name, sch in SCHEMAS.items():                    # the printed contract equals LangChain's own model-facing schema
    line = next(l for l in OUT["contract"].splitlines() if l.strip().startswith(name + "("))
    shown = line.split("(", 1)[1].split(")", 1)[0]
    assert shown == ", ".join(f"{p}: {PYT[typ]}" + ("" if req else f" = {default!r}") for p, typ, default, req in sch["params"]), (name, shown, sch)
assert OUT["contract"].count("hidden: runtime") == 1
assert OUT["contract"].rstrip("\n").endswith(f"  'express' refused: {TIER}"), OUT["contract"]     # as the chat tool refuses it

# the one retrieve(), against a local stub of rag-api; the ID token is stood in, everything else is the kit's function
CITES = [{"chunk_id": f"acme:{'a' * 8}#{i}", "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/payment_of_gratuity_act_1972.pdf", "page": 3,
          "quote": "...", "score": round(0.94 - 0.07 * i, 2)} for i in range(5)]
GRAT = "Gratuity is payable on termination after not less than five years of continuous service [1]."
REQS = []


class Api(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        REQS.append(json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)))))
        data = json.dumps({"answer": GRAT, "citations": CITES, "confidence": "high", "answerable": True, "model": "gemini-3.6-flash",
                           "backend": "vertex", "tokens_in": 1790, "tokens_out": 96, "latency_ms": 2600, "cache_hit": "none"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


api = ThreadingHTTPServer(("127.0.0.1", 0), Api)
threading.Thread(target=api.serve_forever, daemon=True).start()
PRE_TOKEN = "import shared.documind_tools as _d\n_d._id_token = lambda audience: 'TOKEN'\n"
OUT["retrieve"] = run_cell(RETRIEVE_PY, PRE_TOKEN, env={"RAG_API_URL": f"http://127.0.0.1:{api.server_address[1]}"}, cwd=KIT)
api.shutdown()
OUT["retrieve"] = re.sub(r"\| \d+\.\d s", "| 2.7 s", OUT["retrieve"])
assert REQS and REQS[0]["tenant_id"] == "acme" and REQS[0]["top_k"] == 5 and "brain" not in REQS[0] and REQS[0]["stream"] is False, REQS

# the chat service, against a local stub that answers the way agent.py does (the four keys, the brain, the latency)
LANE_RAG_TIMEOUT_S = float(re.search(r"\|RAG_TIMEOUT_S=(\d+)\|", (KIT / "commands/lesson-12.8.sh").read_text(encoding="utf-8")).group(1))
LIM_SRC = (KIT / "services/chat/limits.py").read_text(encoding="utf-8")
LIM = {k: float(re.search(rf'^{v} = \w+\(os\.environ\.get\("\w+", "([\d.]+)"\)\)', LIM_SRC, re.M).group(1))
       for k, v in (("max_model_calls", "MAX_MODEL_CALLS"), ("budget_inr", "TURN_BUDGET_INR"), ("deadline_s", "TURN_DEADLINE_S"),
                    ("model_timeout_s", "MODEL_TIMEOUT_S"), ("model_attempts", "MODEL_ATTEMPTS"), ("min_model_s", "MIN_MODEL_S"))}
for k in ("max_model_calls", "model_attempts"):
    LIM[k] = int(LIM[k])                                # int() in the kit: printed without a decimal point
LIM["tool_budgets_s"] = {"retrieve": LANE_RAG_TIMEOUT_S + 5, "calculate_processing_cost": 10}   # tools.TIMEOUTS on the lane
assert '"limits": limits.published()}' in ag_src and 'TIMEOUTS = {"retrieve": documind_tools.RAG_TIMEOUT_S + 5, "calculate_processing_cost": 10}' in ct_src
HEALTH = {"status": "ok", "profile": "gcp", "brains": ["langchain", "langgraph", "adk", "direct"], "default_brain": "langchain", "limits": LIM}
DIRECT_COST = "The documents give no per-page price for processing the handbook; the April invoice bills priority processing at Rs 12.00 a unit [1]."
# an agent brain's citations, numbered from 1 for its turn by the kit's own tools._number(); the cost turn's search found three
NUMBERED = {}
for key, k in (("policy", 5), ("cost", 3)):
    NUMBERED[key] = []
    chat_tools._number([dict(c) for c in CITES[:k]], NUMBERED[key])
    assert [c["n"] for c in NUMBERED[key]] == list(range(1, k + 1))
PLAN = {("direct", Q_GRAT): {"answer": GRAT, "tool_calls": ["retrieve"], "refusals": [], "citations": CITES, "latency_ms": 3180},
        ("langchain", Q_GRAT): {**SUMMARIES["policy"], "citations": NUMBERED["policy"],
                                "answer": "After five years of continuous service, under the Payment of Gratuity Act, 1972 [1].", "latency_ms": 7240},
        ("langchain", Q_COST): {**SUMMARIES["cost"], "citations": NUMBERED["cost"],
                                "answer": f"The handbook has 283 pages [1]. At the priority tier (USD {COST['rate_per_page']} a page) they cost USD {COST['cost_usd']}, about Rs {COST['cost_inr']:,.2f}.",
                                "latency_ms": 11350},
        ("direct", Q_COST): {"answer": DIRECT_COST, "tool_calls": ["retrieve"], "refusals": [], "citations": CITES[:3], "latency_ms": 3420}}


class Chat(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        out = {**PLAN[(req["brain"], req["question"])], "brain": req["brain"], "session_id": req["session_id"]}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


chat = ThreadingHTTPServer(("127.0.0.1", 0), Chat)
threading.Thread(target=chat.serve_forever, daemon=True).start()
ask = lambda b, q: run_cell(CHAT_PY, env={"CHAT": f"http://127.0.0.1:{chat.server_address[1]}", "B": b, "Q": q})  # noqa: E731
OUT["direct"] = ask("direct", Q_GRAT)
OUT["loop"] = ask("langchain", Q_GRAT) + ask("langchain", Q_COST) + ask("direct", Q_COST)
chat.shutdown()
assert "tool_calls ['retrieve']" in OUT["direct"] and " n " not in OUT["direct"] and "['retrieve', 'calculate_processing_cost']" in OUT["loop"]
assert "citations 5 n [1, 2, 3, 4, 5]" in OUT["loop"] and "citations 3 n [1, 2, 3]" in OUT["loop"], OUT["loop"]   # each turn from 1

# the rows: rag-api's usage rows (one per retrieve) and the chat service's turn rows, as the kit writes them
FAKE_BQ = types.ModuleType("google.cloud.bigquery")
FAKE_BQ.Client = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no BigQuery at build time"))
FAKE_GC = types.ModuleType("google.cloud")
FAKE_GC.bigquery = FAKE_BQ
fakes = {"google.cloud": FAKE_GC, "google.cloud.bigquery": FAKE_BQ}
if importlib.util.find_spec("google") is None:
    fakes["google"] = types.ModuleType("google")
saved = {k: sys.modules.get(k) for k in fakes}
sys.modules.update(fakes)
try:
    cspec = importlib.util.spec_from_file_location("cost101", KIT / "services/rag-api/cost.py")
    costmod = importlib.util.module_from_spec(cspec)
    cspec.loader.exec_module(costmod)
finally:
    for k, v in saved.items():
        sys.modules.pop(k, None) if v is None else sys.modules.__setitem__(k, v)
price = lambda tin, tout: costmod.price("gemini-3.6-flash", tin, tout, 0)["usd"]  # noqa: E731
API_ROWS = [{"brain": b, "tokens_in": tin, "tokens_out": tout, "cost_usd": round(price(tin, tout), 6), "latency_ms": ms}
            for b, tin, tout, ms in (("ui", 1790, 96, 2600), ("direct", 1790, 96, 2710), ("langchain", 1812, 101, 2840),
                                      ("langchain", 1650, 88, 2390), ("direct", 1705, 92, 2620))]
CHAT_KEYS = re.findall(r'"(\w+)":', chat_row)
CHAT_ROWS = [dict({k: "" for k in ["event"] + CHAT_KEYS}, event="chat", surface="chat", brain=b, tenant="acme", user="documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
                  session_id=f"lesson101-{b}", latency_ms=ms, tool_calls=tc, refusals=[])
             for b, tc, ms in (("direct", ["retrieve"], 3180), ("langchain", ["retrieve"], 7240),
                               ("langchain", ["retrieve", "calculate_processing_cost"], 11350), ("direct", ["retrieve"], 3420))]
FAKE_GCLOUD = ("import json, sys, types\n"
               "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
               f"API, CHAT = json.loads({json.dumps(json.dumps(API_ROWS))}), json.loads({json.dumps(json.dumps(CHAT_ROWS))})\n"
               "def run(cmd, **kw):\n"
               "    rows = API if 'service_name=\"documind-api\"' in cmd[3] else CHAT\n"
               "    return R(json.dumps([{'jsonPayload': r} for r in rows]))\n"
               "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
OUT["rows"] = run_cell(ROWS_PY, FAKE_GCLOUD)
assert OUT["rows"].count("brain langchain") == 4 and all(k in OUT["rows"].split("the chat service")[1] for k in ("model_calls", "cost_usd", "rag_cost_usd"))

# where the chat service runs: the describe cell's own parsing over the service's shape, then /health
SVC = {"spec": {"template": {"spec": {"containers": [{"env": [
    {"name": "GOOGLE_CLOUD_PROJECT", "value": PROJ}, {"name": "DOCUMIND_PROFILE", "value": "gcp"},
    {"name": "RAG_API_URL", "value": "https://documind-api-NUMBER.asia-south1.run.app"},
    {"name": "SELF_URL", "value": "https://documind-chat-NUMBER.asia-south1.run.app"}, {"name": "RAG_TIMEOUT_S", "value": "90"},
    {"name": "DOCUMIND_BRAIN", "value": "langchain"}]}]}}}}
assert re.search(r"RAG_API_URL=https://documind-api-\$PROJECT_NUMBER\.\$\{REGION:-us-central1\}\.run\.app\|SELF_URL=https://documind-chat-\$PROJECT_NUMBER\.\$\{REGION:-us-central1\}\.run\.app\|RAG_TIMEOUT_S=90\|DOCUMIND_BRAIN=langchain", dep)
OUT["where"] = run_cell("", stdin=json.dumps(SVC), argv=["-c", WHERE_ONE]) + json.dumps(HEALTH, separators=(",", ":")) + "\n"
assert 'return {"status": "ok", "profile": PROFILE, "brains": list(BRAINS), "default_brain": DEFAULT_BRAIN,' in ag_src
OUT["deploy"] = (">> commands/lesson-12.8.sh (DEPLOY block)\n"
                 "Creating temporary archive of ... file(s) totalling ... MiB before compression.\n...\n"
                 f"DONE ... asia-south1-docker.pkg.dev/{PROJ}/documind/chat:COMMIT\n"
                 "Deploying container to Cloud Run service [documind-chat] in project [documind-ai-YOUR-ID] region [asia-south1]\n...\n"
                 "Service URL: https://documind-chat-NUMBER.asia-south1.run.app\n"
                 f"Updated IAM policy for service [documind-chat].   (seven times, one per account: {', '.join(INVOKERS[:3])},\n"
                 f"   {', '.join(INVOKERS[3:6])},\n   {', '.join(INVOKERS[6:-1])})\n"
                 f"{NOT_BOUND}\n"
                 "... job exists - continuing   (or: Job [documind-checkpoint-setup] has successfully been created.)\n"
                 "Execution [documind-checkpoint-setup-xxxxx] has successfully completed.\n...\n"
                 ">> you@example.com may mint tokens as documind-ui-sa\n>> you@example.com may mint tokens as documind-outsider-sa\n")
assert 'echo ">> $$who may mint tokens as $$sa"' in mk and '|| echo "job exists - continuing"' in dep
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "deploy": "run in the operator shell, in the kit (the chat service built and deployed in your region; several minutes)",
    "where": "run in the operator shell, in the kit (where the chat service points, and its brains)",
    "contract": "run in the operator shell, in the kit (what the model reads of each tool; reads the source, installs nothing)",
    "retrieve": "run in the operator shell, in the kit (the one retrieve(), called from your shell as a roster member)",
    "direct": "run in the operator shell, in the kit (a small chat function, and the direct brain)",
    "loop": "run in the operator shell, in the kit (the LangChain loop on the same question, then a cost question on both brains)",
    "rows": "run in the operator shell, in the kit (the rows both services wrote since the retrieve cell; reads only)",
}
OUT_LABELS = {
    "deploy": "shape (Cloud Build's and gcloud's own lines are cut down)",
    "where": "(the cell's parsing over a stand-in of the service; your URLs carry your project number)",
    "contract": "(this cell run on the kit's own tools.py; the build checks it against LangChain's own schema)",
    "retrieve": "(the kit's retrieve() against a local stub of rag-api; your citations and time differ)",
    "direct": "(against a local stub of the chat service; your words and times differ)",
    "loop": "(against a local stub; the model decides which tools it calls, and your lists are the truth)",
    "rows": "(against a fake gcloud, priced by the kit's own price(); your numbers differ)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: one turn, two brains
STEPS = {
    ("direct", "policy"): [["rt", "the chat service looks up the tenant from the roster: acme"], ["tool", f"retrieve(query=the question, tenant_id=acme, top_k=5, brain=direct), called by the code"],
                           ["tool", "rag-api retrieves, reranks and generates: citations and its own grounded answer"], ["skip", "no model turn in the chat service"]],
    ("direct", "cost"): [["rt", "the tenant from the roster: acme"], ["tool", "retrieve(query=the question, tenant_id=acme, top_k=5, brain=direct), called by the code"],
                         ["tool", "rag-api answers from the documents; nothing multiplies 283 by a rate"], ["skip", "no second tool: the floor has no loop"]],
    ("direct", "zeta"): [["rt", "the tenant from the roster: acme, whatever the question names"], ["tool", "retrieve(query=the question, tenant_id=acme, top_k=5, brain=direct)"],
                         ["tool", "rag-api searches acme's documents only"], ["skip", "no model turn in the chat service"]],
    ("langchain", "policy"): [["rt", "the tenant from the roster: acme, placed in the runtime context, not in the prompt"],
                              ["model", "the model reads the question and two tool schemas, none with a tenant, and calls retrieve(query, top_k=5)"],
                              ["tool", "the adapter reads tenant_id=acme from the runtime and calls the one retrieve()"],
                              ["tool", "rag-api answers in full; the adapter passes on the citations, numbered from 1 for this turn, and drops rag-api's answer"],
                              ["model", "the model writes its own answer from the citations, and cites them as [n]"]],
    ("langchain", "cost"): [["rt", "the tenant from the roster: acme, in the runtime context"], ["model", "the model calls retrieve to find the page count, as the system prompt asks"],
                            ["tool", "retrieve() through the adapter, tenant from the runtime"], ["model", "the model calls calculate_processing_cost(total_pages=283, processing_type=priority)"],
                            ["tool", f"the cost tool: {COST['total_pages']} x USD {COST['rate_per_page']} = USD {COST['cost_usd']}, Rs {COST['cost_inr']:,.2f}"],
                            ["model", "the model writes the answer from both results"]],
    ("langchain", "zeta"): [["rt", "the tenant from the roster: acme"], ["model", "the model calls retrieve(query mentioning zeta); it has no tenant argument to change"],
                            ["tool", "the adapter searches acme, the runtime's tenant"], ["model", "the model can only report what acme's documents hold"]],
}
ANSWERS = {("direct", k): {"tool_calls": ["retrieve"], "refusals": []} for k in ("policy", "cost", "zeta")}
ANSWERS.update({("langchain", k): {"tool_calls": SUMMARIES[k]["tool_calls"], "refusals": SUMMARIES[k]["refusals"]} for k in ("policy", "cost", "zeta")})
ROWS_PER = {("direct", k): 1 for k in ("policy", "cost", "zeta")}
ROWS_PER.update({("langchain", k): SUMMARIES[k]["tool_calls"].count("retrieve") for k in ("policy", "cost", "zeta")})
DATA = {"steps": {f"{b}|{q}": v for (b, q), v in STEPS.items()}, "answers": {f"{b}|{q}": v for (b, q), v in ANSWERS.items()},
        "rows": {f"{b}|{q}": v for (b, q), v in ROWS_PER.items()}, "schemas": SCHEMAS}
UI_JS = r"""var root = document.getElementById('turn'); if (!root) return;
  var D = %s, $ = function(id){ return document.getElementById(id); };
  function esc(s){ return String(s).replace(/[&<>]/g, function(c){ return {'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c]; }); }
  function schema(){
    return Object.keys(D.schemas).map(function(n){ var s = D.schemas[n];
      return n + '(' + s.params.map(function(p){ return p[0] + ': ' + p[1] + (p[3] ? '' : ' = ' + JSON.stringify(p[2])); }).join(', ') + ')\n    ' + s.doc; }).join('\n'); }
  function render(){
    var k = $('tu-b').value + '|' + $('tu-q').value, st = D.steps[k], a = D.answers[k], agent = $('tu-b').value !== 'direct';
    $('tu-schema').textContent = agent ? schema() : 'the direct brain shows the model no tools: it calls retrieve() itself, once';
    $('tu-steps').innerHTML = st.map(function(s){ return '<li class="' + s[0] + '">' + esc(s[1]) + '</li>'; }).join('');
    $('tu-out').textContent = 'tool_calls ' + JSON.stringify(a.tool_calls) + '   refusals ' + JSON.stringify(a.refusals) + '   rag-api rows ' + D.rows[k]
      + (agent ? '   + the agent\'s own model turns, on the chat row' : '');
  }
  ['tu-b', 'tu-q'].forEach(function(id){ $(id).addEventListener('change', render); });
  render();""" % json.dumps(DATA)

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"N_TOOLS": str(len(SCHEMAS)), "COST_USD": f"{COST['cost_usd']}", "COST_INR": f"{COST['cost_inr']:,.2f}", "Q_GRAT": Q_GRAT, "Q_COST": Q_COST}

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
print(f"kit: {len(SCHEMAS)} tools, the printed contract equal to LangChain's tool_call_schema | _summary() and DirectBrain.answer() executed on stand-ins"
      f" | the chat deploy block honours REGION | retrieve, chat and rows cells run against stand-ins")
