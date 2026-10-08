"""Build lesson 5.7 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

One tool, four brains. The LangChain adapter (services/chat/tools.py: ToolRuntime keeps the tenant out of the schema,
rag-api's answer is dropped, citations are numbered, a bad argument becomes a result) beside the ADK adapter, which is
the same one (tools.for_adk(): the same two tools as plain functions, the request through tools.REQUEST, and the error
contract through on_tool_error_callback and after_tool_callback). Offline, in ~/graph-venv with google-adk added: what
each model is shown, one retrieve() through each adapter against a stand-in rag-api, four calls that go wrong, and
the turn's limits wired three ways (TurnLimitsMiddleware, the hand-built agent node, ADK's model callbacks beside
RunConfig) with a looping model stopped in each, against ModelCallLimitMiddleware's two extra nodes. Live: /health's
four names and one limits block, and the module's gate, make smoke-chat; the four cost lines from rag-api's rows and
the chat rows by brain; and each agent brain's own model calls, call by call, by running the kit's brains in the venv.

Build-time proof: the offline cell runs here on the kit's brains.py and tools.py with google-adk 2.8.0, the chat
image's pin; the declarations, what rag-api received, what each model read and the four failures are its own
printing. /health's body is the kit's own health(); make smoke-chat's lines are the kit's smoke_chat.py against a
local stand-in of the chat service whose limits are the kit's Meter; the rows come from a fake gcloud; the measuring
cell runs the kit's brains against stand-in models that count each prompt at four characters a token.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "5.7"
title = "<title>Lesson 5.7 Compare the LangChain and ADK adapters - one tool, four brains, and the cost line each one leaves | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
QG = "After how many years of continuous service does gratuity become payable?"
BRAIN_ORDER = ("direct", "langchain", "langgraph", "adk")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.cmp-sel{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 12px;margin:6px 0 10px;}
.cmp-sel label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.cmp-sel select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.cmp{display:grid;grid-template-columns:minmax(0,8em) minmax(0,1fr) minmax(0,1fr);font-size:12.5px;line-height:1.5;color:var(--slate);}
.cmp>div{padding:6px 8px;border-top:1px solid var(--border);min-width:0;overflow-wrap:anywhere;}
.cmp .k{color:var(--navy);font-weight:600;}
.cmp .d{background:var(--teal-light);}
.cmp .hd{font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;color:var(--teal-dark);border-top:0;}
.cmp-n{font-size:var(--small-size);color:var(--slate);margin:8px 0 0;}
@media (max-width:640px){.cmp{grid-template-columns:minmax(0,1fr) minmax(0,1fr);}.cmp .k{grid-column:1/-1;padding-bottom:0;}.cmp .k+div,.cmp .k+div+div{border-top:0;}.cmp .hd0{display:none;}}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
CT, BR, AG, DT, IAP = "services/chat/tools.py", "services/chat/brains.py", "services/chat/agent.py", "shared/documind_tools.py", "shared/iap.py"
LIM = "services/chat/limits.py"
EXCERPTS = {
    "lctool": ("services/chat/tools.py - the LangChain adapter: the model is shown three arguments; the tenant arrives through ToolRuntime",
               block(CT, "@tool", n=10) + "\n...\n" + block(CT, '    tenant_id = _ctx(runtime, "tenant_id")', n=3)),
    "fortools": ("services/chat/tools.py - for_adk(): the same two tools as plain functions, their arguments checked by the @tool's own schema; the request arrives through REQUEST",
                 block(CT, "def _checked(twin, **args) -> dict:", n=10) + "\n\n\n" + block(CT, "def for_adk() -> list:", n=19)),
    "adktool": ("services/chat/brains.py - the ADK brain: what goes wrong becomes an error result, as in LangChain",
                block(BR, "        def tool_failed(tool, args, tool_context, error):", n=18) + "\n...\n"
                + block(BR, '        root = LlmAgent(name="documind_adk"', n=4)),
    "wiring": ("services/chat/brains.py - the turn's limits, wired three ways: middleware, the node itself, model callbacks beside ADK's cap",
               block(BR, "        self.agent = create_agent(model=llm or build_llm(), tools=TOOLS, system_prompt=SYSTEM,", n=3) + "\n...\n"
               + block(BR, "            meter = limits.meter_of(runtime.context)", n=3) + "\n...\n"
               + block(BR, "                        before_model_callback=limits.adk_before_model", n=2) + "\n...\n"
               + block(BR, "        self.run_config = RunConfig(max_llm_calls=limits.MAX_MODEL_CALLS)", n=1)),
    "adkcb": ("services/chat/limits.py - ADK's two model callbacks: the Meter before the call is counted, the tokens after",
              block(LIM, "def adk_before_model(callback_context, llm_request):", end="def adk_model_error(")),
    "refusals": ("services/chat/brains.py - refusals: every error result, in LangChain and LangGraph and in ADK",
                 block(BR, '        "refusals": [m.name for m in messages', n=1) + "\n...\n"
                 + block(BR, "            for call in (ev.get_function_calls() or []):", n=5)),
    "health": ("services/chat/agent.py - /health: the names in a constant, and the limits every turn runs under",
               block(AG, '@app.get("/health")', n=5)),
    "sessions": ("services/chat/brains.py - where the ADK brain keeps a conversation",
                 block(BR, "    def _sessions():", n=11)),
}
assert "runtime: ToolRuntime = None) -> dict:" in EXCERPTS["lctool"][1] and 'brain = _ctx(runtime, "brain")' in EXCERPTS["lctool"][1]
assert "ctx = REQUEST.get()" in EXCERPTS["fortools"][1] and "fn.__doc__ = twin.func.__doc__" in EXCERPTS["fortools"][1]
assert "valid = twin.tool_call_schema.model_validate(args)" in EXCERPTS["fortools"][1] and "return TOOLS[1].func(**_checked(TOOLS[1]" in EXCERPTS["fortools"][1]
assert "on_tool_error_callback=tool_failed" in EXCERPTS["adktool"][1] and "FunctionTool(limits.timed_adk(f)) for f in for_adk()" in EXCERPTS["adktool"][1]
assert "[limits.TurnLimitsMiddleware(), _guard_middleware()]" in EXCERPTS["wiring"][1] and "if not meter.allow_model_call():" in EXCERPTS["wiring"][1]
assert "after_model_callback=limits.adk_after_model" in EXCERPTS["wiring"][1] and "return _adk_stop()" in EXCERPTS["adkcb"][1]
assert 'return {**tool_response, "status": "error"}' in EXCERPTS["adktool"][1] and "isinstance(error, ToolException)" in EXCERPTS["adktool"][1]
assert "refusals.append(res.name)" in EXCERPTS["refusals"][1] and EXCERPTS["refusals"][1].count('== "error"') == 2
assert '"brains": list(BRAINS)' in EXCERPTS["health"][1] and EXCERPTS["health"][1].rstrip().endswith('"limits": limits.published()}')
assert "DatabaseSessionService" in EXCERPTS["sessions"][1] and "InMemorySessionService()" in EXCERPTS["sessions"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
ct_src, br_src, ag_src, dt_src, iap_src = ((KIT / p).read_text(encoding="utf-8") for p in (CT, BR, AG, DT, IAP))
main_src = (KIT / "services/rag-api/main.py").read_text(encoding="utf-8")
assert 'BRAINS = ("langchain", "langgraph", "adk", "direct")' in br_src and 'DEFAULT_BRAIN = os.environ.get("DOCUMIND_BRAIN", "langchain")' in br_src
assert "TOOLS = [retrieve, calculate_processing_cost]" in ct_src and "def get_usage_stats" not in ct_src
assert 'args["tenant_id"]' not in br_src and "def guard_tool(tool, args, tool_context):" in br_src                 # nothing the model writes is overwritten:
assert "def retrieve(query: str, doc_type: str = \"all\", top_k: int = 5) -> dict:" in ct_src                    # it is never declared
assert "    assertion = headers.get(ASSERTION_HEADER)\n    if assertion:\n        claims = verify(assertion)" in iap_src            # verified, never a fallback
assert "on_tool_error_callback=tool_failed" in br_src and "after_tool_callback=mark_error" in br_src              # errors become results, in ADK too
assert "# Unreachable until a tool that needs approval is declared" in br_src                                    # the box: ADK's guard cannot fire yet
assert 'thinking_level="low"' in (KIT / "shared/profile.py").read_text(encoding="utf-8")
adk_src = br_src[br_src.index("class AdkBrain:"):br_src.index("class DirectBrain:")]
assert "thinking" not in adk_src and "RunConfig(max_llm_calls=limits.MAX_MODEL_CALLS)" in adk_src                 # no thinking level set
assert 'out["answer"] = answer["answer"]' in dt_src                                                               # the shared result carries rag-api's answer
lc_return = ct_src[ct_src.index("    citations = answer.get(\"citations\", [])"):ct_src.index("@tool\ndef calculate_processing_cost")]
assert '"answer"' not in lc_return                                                                                # the adapter's does not
assert 'return {"error": "document search is unavailable",' in ct_src and 'return {"error": "document retrieval is unavailable",' in dt_src
chat_row = re.search(r'logger\.info\(json\.dumps\(\{"event": "chat",(.*?)\}\)\)', ag_src, re.S).group(1)
assert '"cost_usd": used["cost_usd"]' in chat_row and '"model_calls": used["model_calls"]' in chat_row and '"brain": name' in chat_row   # the loop's own cost
assert 'WHERE jsonPayload.event IN ("query", "stream", "media")' in (KIT / "terraform/sql/tenant_daily.sql").read_text(encoding="utf-8")  # the month: rag-api's rows
assert 'service: str = "documind-api"' in (KIT / "evals/usage_rows.py").read_text(encoding="utf-8")                                         # make usage: the same
assert 'logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)' in ag_src               # the row reaches Cloud Logging
assert '"brain": getattr(req, "brain", None) or "ui"' in main_src                                                 # rag-api's row names the brain
assert 'brain="direct")' in br_src
cost_src = (KIT / "services/rag-api/cost.py").read_text(encoding="utf-8")
RATE = tuple(float(x) for x in re.search(r'FALLBACK = \{"gemini-3\.6-flash": \(([\d.]+), ([\d.]+)\)', cost_src).groups())
assert RATE == (1.50, 7.50)
assert 'secret_data = "postgresql://chat:' in (KIT / "terraform/cloudsql.tf").read_text(encoding="utf-8")        # so ADK asks for DatabaseSessionService,
chat_reqs = (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8")                                    # and the image cannot open it: google-adk
assert re.search(r"^google-adk==[\d.]+$", chat_reqs, re.M) and "sqlalchemy" not in chat_reqs.lower()                # without its db extra, no SQLAlchemy
smoke_src = (KIT / "smoke/smoke_chat.py").read_text(encoding="utf-8")
assert 'BRAINS = ("direct", "langchain", "langgraph", "adk")' in smoke_src and "set(BRAINS) <= set(body.get(\"brains\", []))" in smoke_src
mk = (KIT / "Makefile").read_text(encoding="utf-8")
assert "smoke-chat: guard-project" in mk and "DOCUMIND_CHAT_URL=https://documind-chat-$$NUMBER.$(REGION).run.app" in mk
assert 'show("by brain' in (KIT / "evals/usage_rows.py").read_text(encoding="utf-8")
reqs = dict(re.findall(r"^([a-z-]+)==([\d.]+)$", (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8"), re.M))
PINS = {k: reqs[k] for k in ("langchain", "langchain-core", "requests", "google-auth", "google-adk", "google-genai", "langchain-google-genai")}
USD_INR = 85

# ------------------------------------------------------------------ the cells
VENV = ("[ -x ~/graph-venv/bin/python ] || python -m venv ~/graph-venv   # lesson 5.4's venv, made here if it is missing\n"
        "~/graph-venv/bin/pip install -q " + " ".join(f'"{k}=={v}"' for k, v in list(PINS.items())[:4]) + " \\\n"
        "  " + " ".join(f'"{k}=={v}"' for k, v in list(PINS.items())[4:]) + "   # the chat image's pins; ADK is new here\n"
        "~/graph-venv/bin/python -c 'import google.adk, langchain; print(\"graph-venv ok: google-adk\", google.adk.__version__, \"langchain\", langchain.__version__)'")

ADAPT_PY = """import json, logging, sys, textwrap, threading, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)   # the frameworks' notices; lesson 5.5 read the logs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path[:0] = [".", "services/chat"]
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.tools import FunctionTool
from google.genai import types as gt
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.utils.function_calling import convert_to_openai_tool
from langgraph.checkpoint.memory import InMemorySaver
import shared.documind_tools as dt
import tools, brains
SEEN = []
class Api(BaseHTTPRequestHandler):                 # a stand-in rag-api: it notes what it was sent, and answers
    def log_message(self, *a): pass
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append((req["tenant_id"], req.get("brain"), self.headers.get(dt.ASSERTION_HEADER)))
        body = {"answer": "Payable after five years [1].", "answerable": True, "confidence": "high",
                "citations": [{"chunk_id": "acme:gratuity#4", "quote": "not less than five years", "score": 0.9}]}
        self.send_response(200); self.end_headers(); self.wfile.write(json.dumps(body).encode())
srv = ThreadingHTTPServer(("127.0.0.1", 0), Api)
threading.Thread(target=srv.serve_forever, daemon=True).start()
dt.RAG_API_URL, dt._id_token = f"http://127.0.0.1:{srv.server_address[1]}", lambda aud: "TOKEN"
class Script(FakeMessagesListChatModel):           # a LangChain model that says what it is told
    def bind_tools(self, tools, **kw): return self
class AdkScript(BaseLlm):                          # the same for ADK, and it keeps what it was sent
    model: str = "script"
    turns: list = []
    sent: list = []
    async def generate_content_async(self, llm_request, stream=False):
        self.sent.append(llm_request); yield self.turns.pop(0)
def said(text=None, **call):
    part = gt.Part(text=text) if text else gt.Part(function_call=gt.FunctionCall(**call))
    return LlmResponse(content=gt.Content(role="model", parts=[part]))
ctx, adk = {"tenant_id": "acme", "user_id": "you", "assertion": ""}, brains.AdkBrain(None)
def lc(label, name, args):                         # one tool call through the LangChain brain: refusals, status, what it read
    b = brains.LangChainBrain(InMemorySaver(), llm=Script(responses=[
        AIMessage("", tool_calls=[{"name": name, "args": args, "id": "c1"}]), AIMessage("(the model explains)")]))
    cfg = {"configurable": {"thread_id": "acme:you:lc" + label}}
    out = b.answer("...", config=cfg, context={**ctx, "brain": "langchain"})
    res = [m for m in b.agent.get_state(cfg).values["messages"] if isinstance(m, ToolMessage)][0]
    return out["refusals"], res.status, res.content
def ak(label, name, args):                         # the same through the ADK brain
    adk.runner.agent.model = model = AdkScript(turns=[said(name=name, args=args), said("(the model explains)")], sent=[])
    try:
        out = adk.answer("...", config={"configurable": {"thread_id": "acme:you:ak" + label}}, context={**ctx, "brain": "adk"})
    except Exception as e:
        return None, "raises", f"{type(e).__name__}: {str(e).splitlines()[0]}"
    read = [p.function_response.response for c in model.sent[-1].contents for p in c.parts or [] if p.function_response]
    return out["refusals"], read[0].get("status", "success"), json.dumps(read[0])
print("1. what each model is shown for retrieve (* = required); raw = FunctionTool over the shared retrieve(), unadapted")
shown = {"langchain": convert_to_openai_tool(tools.retrieve)["function"],
         "adk": FunctionTool(tools.for_adk()[0])._get_declaration().model_dump(mode="json", exclude_none=True),
         "raw": FunctionTool(dt.retrieve)._get_declaration().model_dump(mode="json", exclude_none=True)}
for name, d in shown.items():
    schema = d.get("parameters") or d["parameters_json_schema"]
    params = [p + ("*" if p in schema.get("required", []) else "") for p in schema["properties"]]
    print(f"   {name:9} {', '.join(params):64} {len(json.dumps(d)):,} characters")
print(f"   langchain tools: {', '.join(t.name for t in tools.TOOLS)}")
print(f"   adk tools:       {', '.join(t.name for t in adk.runner.agent.tools)}   (tools.for_adk())")
print('2. one retrieve(); the ADK model writes tenant_id "globex" and assertion "anything"')
for name, run, args in (("langchain", lc, {"query": "gratuity"}),
                        ("adk", ak, {"query": "gratuity", "tenant_id": "globex", "assertion": "anything"})):
    refusals, status, text = run("r", "retrieve", args)
    tenant, brain, assertion = SEEN[-1]
    print(f"   {name:9} rag-api got tenant {tenant}, brain {brain}, assertion header {assertion!r}")
    read = json.loads(text)
    print(f"             the model read: {', '.join(read)}; citations numbered {[c['n'] for c in read['citations']]}")
print("3. four calls that go wrong")
for i, (call, name, args) in enumerate((('delete_document(doc="x")', "delete_document", {"doc": "x"}),
        ('calculate_processing_cost(total_pages="many")', "calculate_processing_cost", {"total_pages": "many"}),
        ('calculate_processing_cost(total_pages=10, processing_type="express")', "calculate_processing_cost",
         {"total_pages": 10, "processing_type": "express"}),
        ("calculate_processing_cost()", "calculate_processing_cost", {}))):
    print("   " + call)
    for brain, run in (("langchain", lc), ("adk", ak)):
        refusals, status, text = run(str(i), name, args)
        said_ = f"the turn raises {text}" if status == "raises" else f"[{status}] {text}"
        print(f"     {brain:9} " + "\\n               ".join(textwrap.wrap(textwrap.shorten(said_, 150), 76)))
        if status != "raises":
            print(f"               refusals {refusals}")
print(f"4. ADK's sessions with no CHECKPOINT_DSN: {type(adk.svc).__name__}, at most {adk.run_config.max_llm_calls} model calls a turn")
print("5. the turn's limits, wired three ways: a model that asks for a tool on every call, at a cap of 2")
import limits
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult
class Loop(BaseChatModel):                         # asks for the cost tool on every call, each time with a new id
    n: int = 0
    @property
    def _llm_type(self): return "loop"
    def bind_tools(self, tools, **kw): return self
    def _generate(self, messages, stop=None, run_manager=None, **kw):
        self.n += 1
        ask = [{"name": "calculate_processing_cost", "args": {"total_pages": 10}, "id": f"c{self.n}"}]
        return ChatResult(generations=[ChatGeneration(message=AIMessage("", tool_calls=ask))])
def stop(name, brain):
    meter = limits.Meter(max_model_calls=2)
    out = brain.answer("...", config={"configurable": {"thread_id": "acme:you:loop" + name}}, context={**ctx, "brain": name, "meter": meter})
    return f"stopped_by {meter.stopped_by} after {meter.model_calls} model calls: {out['answer'][:44]}..."
nodes = lambda g: ", ".join(n for n in g.get_graph().nodes if not n.startswith("__"))
lcb, lgb = brains.LangChainBrain(InMemorySaver(), llm=Loop()), brains.LangGraphBrain(InMemorySaver(), llm=Loop())
print(f"   langchain  nodes {nodes(lcb.agent)}; TurnLimitsMiddleware wraps the model call\\n              {stop('langchain', lcb)}")
print(f"   langgraph  nodes {nodes(lgb.graph)}; the agent node checks the Meter itself\\n              {stop('langgraph', lgb)}")
root = adk.runner.agent
root.model = AdkScript(turns=[said(name="calculate_processing_cost", args={"total_pages": 10}) for _ in range(3)], sent=[])
print(f"   adk        {root.before_model_callback.__name__}, {root.after_model_callback.__name__}, {root.on_model_error_callback.__name__};"
      f" RunConfig max_llm_calls {adk.run_config.max_llm_calls}\\n              {stop('adk', adk)}")
def checkpoints(middleware):                       # one turn with one tool call, as each graph saves it
    saver, cfg = InMemorySaver(), {"configurable": {"thread_id": "acme:you:ck"}}
    model = Script(responses=[AIMessage("", tool_calls=[{"name": "calculate_processing_cost", "args": {"total_pages": 10}, "id": "c1"}]), AIMessage("done")])
    g = create_agent(model=model, tools=tools.TOOLS, middleware=middleware, checkpointer=saver)
    g.invoke({"messages": [{"role": "user", "content": "..."}]}, cfg, context={**ctx, "brain": "langchain"})
    return f"nodes {nodes(g)}; a turn with one tool call writes {len(list(saver.list(cfg)))} checkpoints"
print(f"   the kit's middleware:      {checkpoints([limits.TurnLimitsMiddleware(), brains._guard_middleware()])}")
print(f"   ModelCallLimitMiddleware:  {checkpoints([ModelCallLimitMiddleware(run_limit=12), brains._guard_middleware()])}")
srv.shutdown()"""

SMOKE = ('export CHAT="https://documind-chat-$NUMBER.$REGION.run.app" SINCE104="$(date -u +%FT%TZ)"\n'
         'curl -s -H "Authorization: Bearer $(tok "$CHAT")" "$CHAT/health"; echo\n'
         'make smoke-chat PROJECT="$PROJECT" REGION="$REGION"   # the module\'s gate: four brains, one question, the outsider refused')

LINES_PY = """import json, os, subprocess
from collections import defaultdict
def rows(service, event):                          # one service's rows of one event since step 4
    f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}" AND jsonPayload.event="{event}" '
         f'AND timestamp>="{os.environ["SINCE104"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--limit", "50", "--format", "json"],
                         capture_output=True, text=True, check=True).stdout
    return [e["jsonPayload"] for e in json.loads(out or "[]")]
lines = defaultdict(lambda: {"calls": 0, "rs": 0.0, "model_calls": 0, "own_rs": 0.0})
for j in rows("documind-api", "query"):            # rag-api: one row per retrieve(), naming the brain that asked
    line = lines[j.get("brain") or "ui"]
    line["calls"] += 1; line["rs"] += j["cost_usd"] * 85
for j in rows("documind-chat", "chat"):            # the chat service: one row per turn, with the loop's own model calls
    line = lines[j["brain"]]
    line["model_calls"] += j.get("model_calls", 0); line["own_rs"] += j.get("cost_usd", 0) * 85
print("            rag-api's rows        the chat rows             whole")
for brain in ("direct", "langchain", "langgraph", "adk"):
    n = lines[brain]
    print(f"  {brain:9} {n['calls']} retrieve()  Rs {n['rs']:.4f}   {n['model_calls']} model calls  Rs {n['own_rs']:.4f}   Rs {n['rs'] + n['own_rs']:.4f}")
json.dump(lines, open(os.path.expanduser("~/lesson104_lines.json"), "w"))"""

OWN_PY = """import asyncio, json, logging, os, sys, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
sys.path[:0] = [".", "services/chat"]
from langgraph.checkpoint.memory import InMemorySaver
import brains, limits
from shared import prices                          # the chat service's prices: cost.py's, gemini-3.6-flash at 1.50 and 7.50 per 1M
Q = "After how many years of continuous service does gratuity become payable?"
for name in ("langchain", "langgraph", "adk"):
    b, meter = brains.build(name, InMemorySaver()), limits.Meter(model=brains.MODEL)
    cfg = {"configurable": {"thread_id": f"acme:lesson104:{name}"}}
    b.answer(Q, config=cfg, context={"tenant_id": "acme", "user_id": "lesson104", "assertion": "", "brain": name, "meter": meter})
    if name == "adk":                              # ADK keeps each model call's usage on the session's events
        s = asyncio.run(b.svc.get_session(app_name="documind", user_id="lesson104", session_id=cfg["configurable"]["thread_id"]))
        calls = [(u.prompt_token_count or 0, (u.candidates_token_count or 0) + (u.thoughts_token_count or 0), u.thoughts_token_count or 0)
                 for u in (e.usage_metadata for e in s.events) if u]
    else:                                          # LangChain keeps it on each AIMessage; output_tokens already counts thinking
        g = b.agent if name == "langchain" else b.graph
        calls = [(u["input_tokens"], u["output_tokens"], u.get("output_token_details", {}).get("reasoning", 0))
                 for u in (getattr(m, "usage_metadata", None) for m in g.get_state(cfg).values["messages"]) if u]
    print(f"  {name:9} " + "   ".join(f"call {k}: in {i:>5,} out {o:>4,}" for k, (i, o, t) in enumerate(calls, 1))
          + f"   (thinking {sum(c[2] for c in calls):,})")
    print(f"            the Meter, as the chat row keeps it: {meter.model_calls} model calls, in {meter.tokens_in:,},"
          f" out {meter.tokens_out:,}, Rs {prices.inr(meter.cost_usd):.4f}")"""

OWN_ENV = ('GOOGLE_CLOUD_PROJECT="$PROJECT" RAG_API_URL="$API" RAG_TIMEOUT_S=90 \\\n'
           'DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" ')


def heredoc(body: str, prefix: str = "", python: str = "python") -> str:
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


CELLS = {
    "venv": VENV,
    "adapt": heredoc(ADAPT_PY, python="~/graph-venv/bin/python"),
    "smoke": SMOKE,
    "lines": "sleep 20   # Cloud Logging needs a moment to show the rows\n" + heredoc(LINES_PY),
    "own": heredoc(OWN_PY, OWN_ENV, python="~/graph-venv/bin/python"),
}

T = Path(tempfile.mkdtemp(prefix="lesson104-"))
HOME = T / "home"
HOME.mkdir()
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ,
       "SINCE104": "YYYY-MM-DDTHH:MM:SSZ", "HOME": str(HOME), "USERPROFILE": str(HOME), "CHECKPOINT_DSN": ""}


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.stdout[-800:], r.stderr[-1500:])
    return r.stdout


def serve(handler) -> tuple:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def reply(h, code: int, body) -> None:
    data = json.dumps(body, separators=(",", ":")).encode()
    h.send_response(code)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(data)))
    h.end_headers()
    h.wfile.write(data)


# ---- step 3: the offline cell, verbatim, on the kit
OUT = {"adapt": run_cell(ADAPT_PY, cwd=KIT)}
F = OUT["adapt"]
decl = {m[0]: (m[1], int(m[2].replace(",", ""))) for m in re.findall(r"^   (langchain|adk|raw)\s+(query\*.*?)\s{2,}([\d,]+) characters$", F, re.M)}
assert decl["langchain"][0] == decl["adk"][0] == "query*, doc_type, top_k", decl                          # the same three arguments
assert decl["raw"][0] == "query*, tenant_id*, top_k, doc_type, assertion, brain, passages", decl          # what for_adk() replaces
assert decl["langchain"][1] < decl["adk"][1] < decl["raw"][1], decl
assert "langchain tools: retrieve, calculate_processing_cost\n" in F and "adk tools:       retrieve, calculate_processing_cost   (tools.for_adk())" in F, F
assert "rag-api got tenant acme, brain langchain, assertion header None" in F and "rag-api got tenant acme, brain adk, assertion header None" in F, F
assert F.count("the model read: citations, answerable, confidence; citations numbered [1]\n") == 2, F
assert "adk       [error] {\"error\": \"delete_document requires manual approval\", \"status\":" in F, F
assert "langchain [error] {\"error\": \"delete_document requires manual approval\"}\n               refusals ['delete_document']" in F, F
assert "adk       [error] {\"error\": \"1 validation error for" in F and "Input should be a valid integer" in F, F   # the @tool's schema, in ADK
assert "adk       [error] {\"error\": \"unknown tier 'express'" in F and "TypeError" not in F and "ValueError" not in F, F
assert "langchain [error] Error invoking tool 'calculate_processing_cost'" in F and "langchain [error] unknown tier 'express'" in F, F
assert "total_pages: Field required" in F and "mandatory input parameters are not present" in F, F
assert "the turn raises" not in F and "[success]" not in F and "refusals []" not in F, F                  # every failure an error result, in both
assert F.count("[error]") == 8, F
assert F.count("refusals ['calculate_processing_cost']") == 6 and F.count("refusals ['delete_document']") == 2, F
assert "InMemorySessionService, at most 12 model calls a turn" in F, F
assert F.count("stopped_by model_calls after 2 model calls: I stopped this turn") == 3, F                     # the same stop, three wirings
assert "langchain  nodes model, tools; TurnLimitsMiddleware" in F and "langgraph  nodes agent, tools, refuse;" in F, F
assert "the kit's middleware:      nodes model, tools; a turn with one tool call writes 5 checkpoints" in F, F
assert "ModelCallLimitMiddleware.before_model, ModelCallLimitMiddleware.after_model; a turn with one tool call writes 9 checkpoints" in F, F
OUT["venv"] = f"graph-venv ok: google-adk {PINS['google-adk']} langchain {PINS['langchain']}\n"

# ---- step 4: /health is the kit's own health(); make smoke-chat is the kit's smoke_chat.py against a stand-in service
HEALTH = json.loads(run_cell("import sys, json\nsys.path[:0] = ['.', '../..']\nimport agent\nprint(json.dumps(agent.health()))\n",
                             cwd=KIT / "services/chat", env={"CHECKPOINT_DSN": "memory", "RAG_TIMEOUT_S": "90"}))   # the lane's 90 (lesson-12.8.sh)
LIMS = HEALTH.pop("limits")
assert HEALTH == {"status": "ok", "profile": "gcp", "brains": ["langchain", "langgraph", "adk", "direct"], "default_brain": "langchain"}, HEALTH
assert (LIMS["max_model_calls"], LIMS["budget_inr"], LIMS["deadline_s"], LIMS["tool_budgets_s"]["retrieve"]) == (12, 5.0, 100.0, 95.0), LIMS
HEALTH["limits"] = LIMS
sys.path[:0] = [str(KIT), str(KIT / "services/chat")]
import limits  # noqa: E402
# invented: rag-api's row for each brain's one retrieve(), and each agent brain's two model calls (the second carries the first,
# plus the tool result; ADK declares the same tools in more characters). The smoke's limits and step 5's chat rows are the kit's
# Meter over these, so the two steps agree.
ROWS = [{"brain": b, "tokens_in": i, "tokens_out": o, "cost_usd": round((i * RATE[0] + o * RATE[1]) / 1e6, 6), "model_backend": "vertex"}
        for b, i, o in (("direct", 2561, 68), ("langchain", 2498, 64), ("langgraph", 2504, 66), ("adk", 2537, 71))]
OWN_STAND = {"langchain": ((1180, 28), (2410, 61)), "langgraph": ((1180, 28), (2415, 63)), "adk": ((1630, 28), (2870, 66))}


def turn_meter(brain: str):
    m = limits.Meter(model="gemini-3.6-flash")
    m.charge_rag({"cost_usd": next(r["cost_usd"] for r in ROWS if r["brain"] == brain)})
    for t_in, t_out in OWN_STAND.get(brain, ()):
        assert m.allow_model_call()
        m.charge_model(t_in, t_out)
    return m
ANSWERS = {"direct": ("Gratuity becomes payable after not less than five years of continuous service [1].", 3120),
           "langchain": ("Gratuity becomes payable once you have rendered at least five years of continuous service [1].", 11840),
           "langgraph": ("Gratuity is payable after at least five years of continuous service [1].", 9730),
           "adk": ("After five years of continuous service, gratuity becomes payable [1].", 14260)}


class Chat(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        reply(self, 200, HEALTH)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        if self.headers.get("Authorization") == "Bearer OUTSIDER":
            return reply(self, 403, {"detail": "not a member of any tenant"})
        brain = req.get("brain") or HEALTH["default_brain"]
        text, ms = ANSWERS[brain]
        body = {"answer": text, "tool_calls": ["retrieve"], "refusals": [], "brain": brain, "session_id": req["session_id"], "latency_ms": ms,
                "citations": [{"chunk_id": f"acme:payment_of_gratuity_act_1972#{4 + k}", "quote": "..."} for k in range(5)],   # top_k 5, as in 10.1
                "limits": turn_meter(brain).summary()}
        if brain != "direct":                      # an agent brain numbers its citations for the turn (tools._number)
            for k, c in enumerate(body["citations"], 1):
                c["n"] = k
        reply(self, 200, body)


chat, chat_url = serve(Chat)
FAKE_TOKEN = ("import sys, types\n"
              "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
              "def run(cmd, **kw): return R('OUTSIDER' if any('outsider' in c for c in cmd) else 'MEMBER')\n"
              "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
smoke = run_cell("import runpy\nrunpy.run_path('smoke/smoke_chat.py', run_name='__main__')\n", FAKE_TOKEN, cwd=KIT, env={
    "DOCUMIND_CHAT_URL": chat_url, "DOCUMIND_IMPERSONATE_SA": f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com",
    "DOCUMIND_OUTSIDER_SA": f"documind-outsider-sa@{PROJ}.iam.gserviceaccount.com"})
chat.shutdown()
smoke = smoke.replace(chat_url, "https://documind-chat-NUMBER.asia-south1.run.app")
assert "[PASS] health  profile=gcp default=langchain limits=12 calls, Rs 5.0, 100.0 s" in smoke and "6 passed, 0 failed" in smoke, smoke
OUT["smoke"] = json.dumps(HEALTH, separators=(",", ":")) + "\n" + smoke.strip("\n") + "\n"

# ---- step 5: rag-api's rows and the chat rows by brain, from a fake gcloud; the chat rows are the kit's Meter.row() over the same turns
CHAT_ROWS = [{"event": "chat", "brain": b, **turn_meter(b).row()} for b in BRAIN_ORDER]
FAKE_GCLOUD = ("import json, sys, types\n"
               "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
               f"ROWS = json.loads({json.dumps(json.dumps(ROWS))})\n"
               f"CHAT = json.loads({json.dumps(json.dumps(CHAT_ROWS))})\n"
               "def run(cmd, **kw): return R(json.dumps([{'jsonPayload': r} for r in (CHAT if 'documind-chat' in cmd[3] else ROWS)]))\n"
               "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
OUT["lines"] = run_cell(LINES_PY, FAKE_GCLOUD)
assert (HOME / "lesson104_lines.json").exists()
RAG_RS = {r["brain"]: r["cost_usd"] * USD_INR for r in ROWS}
OWN_RS = {r["brain"]: r["cost_usd"] * USD_INR for r in CHAT_ROWS}
LN = {m[0]: m[1:] for m in re.findall(r"^  (\w+)\s+(\d) retrieve\(\)\s+Rs ([\d.]+)\s+(\d) model calls\s+Rs ([\d.]+)\s+Rs ([\d.]+)$", OUT["lines"], re.M)}
assert set(LN) == set(BRAIN_ORDER) and LN["direct"][2] == "0" and all(LN[b][2] == "2" for b in BRAIN_ORDER[1:]), OUT["lines"]
for b in BRAIN_ORDER:
    assert LN[b][1] == f"{RAG_RS[b]:.4f}" and LN[b][3] == f"{OWN_RS[b]:.4f}" and LN[b][4] == f"{RAG_RS[b] + OWN_RS[b]:.4f}", (b, OUT["lines"])
    # the same turn's rupees in step 4's smoke line (cost_inr, rounded once) and step 5's whole (two six-place rows, summed):
    # at most Rs 0.0001 apart, as the page says
    smoke_rs = float(re.search(rf"\[PASS\] brain {b} .*? Rs ([\d.]+) ", OUT["smoke"]).group(1))
    assert abs(smoke_rs - float(LN[b][4])) <= 0.0001 + 1e-9, (b, smoke_rs, LN[b][4])

# ---- step 6: the kit's brains against stand-in models that count each prompt at four characters a token
act = (KIT / "evals/corpus/acme/payment_of_gratuity_act_1972.md").read_text(encoding="utf-8")
at = act.index("rendered continuous service for not less than five years")
QUOTES = [" ".join(act[at - 400 + k * 200: at - 200 + k * 200].split()) for k in range(5)]
ANS = "Gratuity becomes payable after not less than five years of continuous service [1]."


class Rag(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        reply(self, 200, {"answer": ANS, "answerable": True, "confidence": "high", "citations": [
            {"chunk_id": f"acme:payment_of_gratuity_act_1972#{4 + k}", "source_uri": f"gs://{PROJ}-uploads/acme/payment_of_gratuity_act_1972.pdf",
             "page": 2, "quote": q, "score": round(0.91 - k * 0.04, 2)} for k, q in enumerate(QUOTES)]})


rag, rag_url = serve(Rag)
STAND = f"""import json, sys
sys.path[:0] = [".", "services/chat"]
import shared.documind_tools as _dt
_dt._id_token = lambda audience: "TOKEN"
import brains as _brains
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_response import LlmResponse
from google.genai import types as _gt
_Q, _A = {QG!r}, {ANS!r}
class _Stand(BaseChatModel):
    tools_chars: int = 0
    @property
    def _llm_type(self): return "stand-in"
    def bind_tools(self, tools, **kw):
        self.tools_chars = len(json.dumps([convert_to_openai_tool(t) for t in tools])); return self
    def _generate(self, messages, stop=None, run_manager=None, **kw):
        n_in = (sum(len(str(m.content)) + len(json.dumps(getattr(m, "tool_calls", None) or [])) for m in messages) + self.tools_chars) // 4
        if isinstance(messages[-1], ToolMessage):
            msg, n_out = AIMessage(_A), len(_A) // 4
        else:
            call = {{"name": "retrieve", "args": {{"query": _Q}}, "id": "c1"}}
            msg, n_out = AIMessage("", tool_calls=[call]), len(json.dumps(call)) // 4
        msg.usage_metadata = {{"input_tokens": n_in, "output_tokens": n_out, "total_tokens": n_in + n_out}}
        return ChatResult(generations=[ChatGeneration(message=msg)])
_brains.build_llm = lambda: _Stand()
async def _gemini(self, llm_request, stream=False):
    size = lambda xs: len(json.dumps([x.model_dump(mode="json", exclude_none=True) for x in xs]))
    n_in = (size(llm_request.contents) + len(str(llm_request.config.system_instruction or "")) + size(llm_request.config.tools or [])) // 4
    if any(p.function_response for c in llm_request.contents for p in (c.parts or [])):
        part, n_out = _gt.Part(text=_A), len(_A) // 4
    else:
        args = {{"query": _Q}}
        part, n_out = _gt.Part(function_call=_gt.FunctionCall(name="retrieve", args=args)), len(json.dumps(args)) // 4
    yield LlmResponse(content=_gt.Content(role="model", parts=[part]), usage_metadata=_gt.GenerateContentResponseUsageMetadata(
        prompt_token_count=n_in, candidates_token_count=n_out, thoughts_token_count=0, total_token_count=n_in + n_out))
Gemini.generate_content_async = _gemini
"""
OUT["own"] = run_cell(OWN_PY, STAND, cwd=KIT, env={"GOOGLE_CLOUD_PROJECT": PROJ, "RAG_API_URL": rag_url, "RAG_TIMEOUT_S": "90"})
rag.shutdown()
O = OUT["own"]
own = {}
for name, calls, n, t_in, t_out, rs in re.findall(r"^  (langchain|langgraph|adk)\s+(.*?)\s+\(thinking [\d,]+\)\n\s+the Meter, as the chat row keeps it: "
                                                   r"(\d) model calls, in ([\d,]+), out ([\d,]+), Rs ([\d.]+)$", O, re.M):
    per = [(int(a.replace(",", "")), int(b.replace(",", ""))) for a, b in re.findall(r"call \d: in\s+([\d,]+) out\s+([\d,]+)", calls)]
    assert len(per) == int(n) == 2 and sum(a for a, _ in per) == int(t_in.replace(",", "")) and sum(b for _, b in per) == int(t_out.replace(",", "")), O
    assert per[1][0] > per[0][0], O                # the second call carries the first, plus the tool result
    own[name] = (int(n), int(t_in.replace(",", "")), float(rs))
assert set(own) == {"langchain", "langgraph", "adk"} and own["adk"][1] > own["langchain"][1], O   # ADK declares the same tools in more characters
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "venv": "run in the operator shell, in the kit (lesson 5.4's venv, with google-adk added)",
    "adapt": "run in the operator shell, in the kit (the two adapters side by side; no model, no network beyond your machine)",
    "smoke": "run in the operator shell, in the kit (/health, then the module's gate)",
    "lines": "run in the operator shell, in the kit (rag-api's rows and the chat rows since step 4, one line per brain)",
    "own": "run in the operator shell, in the kit (the kit's three agent brains on your machine, each model call counted)",
}
OUT_LABELS = {
    "venv": "",
    "adapt": f"(this cell run on the kit's own brains.py and tools.py with google-adk {PINS['google-adk']}; the LangChain texts are the installed LangChain's)",
    "smoke": "(the body is the kit's own health() with RAG_TIMEOUT_S=90; the smoke lines are the kit's smoke_chat.py against a local stand-in whose limits are the kit's Meter; the timings, answers, citations and token counts are invented)",
    "lines": "(invented token counts from a fake gcloud, priced at cost.py's rate for gemini-3.6-flash; the chat rows are the kit's Meter.row() over them)",
    "own": "(the kit's brains and Meter against stand-in models that count each prompt at four characters a token and do no thinking; your run prints Gemini's own counts)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: two brains, side by side
lc_decl, adk_decl = decl["langchain"], decl["adk"]
ASPECTS = [("loop", "The loop"), ("tools", "Tools the model sees"), ("params", "retrieve, as the model sees it"),
           ("tenant", "The tenant comes from"), ("reads", "What the model reads back"), ("down", "A failed retrieval reads"),
           ("blocked", "A blocked or unknown name"), ("error", "A bad argument or a tool that raises"), ("refusals", "refusals means"),
           ("memory", "Where the conversation lives"), ("thinking", "Thinking"), ("calls", "Model calls in a turn"),
           ("limits", "The turn's limits, checked at"), ("row", "rag-api's row"), ("own", "The chat row's own model calls")]
W = {
    "langchain": {"loop": "create_agent: the model, the tools, repeat; the guard is middleware",
                  "tools": "retrieve, calculate_processing_cost (tools.TOOLS)",
                  "params": f"{lc_decl[0]}: {lc_decl[1]:,} characters",
                  "tenant": "ToolRuntime's context, set by agent.py from the roster; not in the schema",
                  "reads": "citations, answerable, confidence: rag-api's answer is dropped; each citation numbered for the turn",
                  "down": "document search is unavailable (the adapter's words)",
                  "blocked": "an error result the model reads: requires manual approval, or not a valid tool",
                  "error": "an error result the model reads, a missing argument and an unknown tier included",
                  "refusals": "every error result, whatever the reason",
                  "memory": "the checkpointer: PostgresSaver on Cloud SQL",
                  "thinking": "thinking_level low, set by shared/profile.build_llm",
                  "calls": f"two or more: one asks for retrieve, one answers; at most {LIMS['max_model_calls']}",
                  "limits": "TurnLimitsMiddleware, wrapping the model call: no node added, the same checkpoints",
                  "row": "brain langchain, with rag-api's tokens and cost",
                  "own": "model_calls, tokens and cost_usd for the loop, at cost.py's prices"},
    "adk": {"loop": "an LlmAgent run by a Runner; its tool callbacks turn what goes wrong into results",
            "tools": "retrieve, calculate_processing_cost (tools.for_adk(): the same two, as plain functions)",
            "params": f"{adk_decl[0]}: {adk_decl[1]:,} characters",
            "tenant": "tools.REQUEST, set by the brain from agent.py's context; not in the declaration",
            "reads": "citations, answerable, confidence: rag-api's answer is dropped; each citation numbered for the turn",
            "down": "document search is unavailable (the adapter's words)",
            "blocked": "an error result the model reads (on_tool_error_callback): requires manual approval, or not found",
            "error": "an error result the model reads: the @tool's schema checks the arguments; ADK's missing-argument answer is marked as one",
            "refusals": "every error result, whatever the reason",
            "memory": "ADK's own sessions, in the instance's memory: it asks for Cloud SQL, and the image has no SQLAlchemy to open it",
            "thinking": "not set: the model's default",
            "calls": f"two or more; at most {LIMS['max_model_calls']}",
            "limits": "before-model, after-model and model-error callbacks; RunConfig.max_llm_calls as a backstop",
            "row": "brain adk, with rag-api's tokens and cost",
            "own": "model_calls, tokens and cost_usd for the loop, at cost.py's prices"},
    "direct": {"loop": "none: one retrieve(), and rag-api's answer is the answer",
               "tools": "none: no model runs in the chat service",
               "params": "none: the chat service calls retrieve() itself, with top_k 5",
               "tenant": "the context, passed straight to retrieve()",
               "reads": "no model reads anything: rag-api's answer and citations are returned",
               "down": "document retrieval is unavailable, as the answer",
               "blocked": "cannot happen: no model asks for anything",
               "error": "cannot happen: no model writes arguments",
               "refusals": "always empty",
               "memory": "nowhere: every turn stands alone",
               "thinking": "rag-api's generation, as it is configured",
               "calls": "none in the chat service; rag-api makes one",
               "limits": "nothing to limit: no loop; rag-api's cost is still counted on the Meter",
               "row": "brain direct, with rag-api's tokens and cost",
               "own": "none: model_calls 0, cost_usd 0; its whole cost is rag-api's row"},
}
W["langgraph"] = {**W["langchain"], "loop": "a StateGraph drawn by hand: agent, tools and refuse nodes",
                  "limits": "the agent node itself, by hand: the Meter before the call, the call's timeout, its tokens after",
                  "blocked": "the refuse node: every call in that turn refused; an unknown name, an error result",
                  "row": "brain langgraph, with rag-api's tokens and cost"}
assert all(set(W[b]) == {k for k, _ in ASPECTS} for b in BRAIN_ORDER)
NAMES = {"langchain": "LangChain", "langgraph": "LangGraph", "adk": "ADK", "direct": "direct"}
UI_JS = r"""var root = document.getElementById('cb'); if (!root) return;
  var W = %s, A = %s, N = %s, $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = text; return e; }
  function render(){ var a = $('cb-a').value, b = $('cb-b').value, n = 0, out = $('cb-out');
    out.textContent = '';
    [['hd hd0', 'Aspect'], ['hd', N[a]], ['hd', N[b]]].forEach(function(c){ out.appendChild(el('div', c[0], c[1])); });
    A.forEach(function(r){ var x = W[a][r[0]], y = W[b][r[0]], d = x !== y ? ' d' : ''; if (d) { n++; }
      out.appendChild(el('div', 'k' + d, r[1])); out.appendChild(el('div', 'v' + d, x)); out.appendChild(el('div', 'v' + d, y)); });
    $('cb-n').textContent = a === b ? 'The same brain on both sides: choose another to compare.' : n + ' of ' + A.length + ' aspects differ; they are shaded.'; }
  ['cb-a', 'cb-b'].forEach(function(id, i){ var s = $(id);
    Object.keys(N).forEach(function(k){ var o = el('option', '', N[k]); o.value = k; s.appendChild(o); });
    s.value = i ? 'adk' : 'langchain'; s.addEventListener('change', render); });
  render();""" % (json.dumps(W), json.dumps(ASPECTS), json.dumps(NAMES))

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"LC_PARAMS": lc_decl[0], "LC_CHARS": f"{lc_decl[1]:,}", "ADK_PARAMS": adk_decl[0], "ADK_CHARS": f"{adk_decl[1]:,}",
         "RAW_PARAMS": decl["raw"][0], "RAW_CHARS": f"{decl['raw'][1]:,}",
         "N_ASPECTS": str(len(ASPECTS)), "ADK_PIN": PINS["google-adk"], "MAX_CALLS": str(LIMS["max_model_calls"]),
         "BUDGET_INR": f"{LIMS['budget_inr']:g}", "DEADLINE_S": f"{LIMS['deadline_s']:g}"}

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
print(f"kit: the two adapters side by side on the kit's brains.py and tools.py, their declarations, results and failures its own"
      f" | the limits stopping a looping model in all three | /health from agent.py, smoke lines from smoke_chat.py, chat rows from the Meter"
      f" | {len(ASPECTS)} aspects in the panel | live cells against stand-ins")
