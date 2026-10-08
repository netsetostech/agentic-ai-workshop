"""Build lesson 5.5 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Where each failure of a tool call surfaces, and what the model, the caller and the logs are told. Offline, in the
chat image's pins (~/graph-venv from 10.2): the kit's own LangChain brain with a scripted model and five failures -
a blocked name, an argument of the wrong type, a tool that does not exist, a retrieval whose rag-api answers too
late for RAG_TIMEOUT_S, and a retrieval cut at its tool budget - with the tool results, refusals, tool_timeouts and
log lines each produces. Then a turn that will not stop: a looping scripted model stopped at its call cap, and the
next turn on the thread answering; make limits-check, make limits and make limits-drill STOP=model_calls. Live:
three identities at the chat service's door (the outsider's 403, a token without an email's 401, a member's 200),
and a filter argument the corpus cannot honour, read back from rag-api's rows as an empty pool.

Build-time proof: the offline cells are the page's own and run here on the kit's brains.py and limits.py with
LangChain; the refusals, the result statuses and texts, the limits and the log lines are their own printing. make
limits-check's output is the kit's test file, run here with DOCUMIND_REQUIRE_LIBS=1. make limits is lane.py's
cmd_limits over the kit's own health(); the drill is the kit's limits-drill.sh and smoke_chat.py against a fake
gcloud and a stand-in chat service whose limits come from the kit's Meter. The 401 and 403 texts and the empty-pool
answer are read from agent.py, shared/iap.py and main.py. The live cells run against local stubs.
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

LESSON = "5.5"
title = "<title>Lesson 5.5 Diagnose tool arguments, access failures and timeouts - where each failure surfaces, what the model reads, and what the logs keep | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
QG = "After how many years of continuous service does gratuity become payable?"
QI = "What is the total payable on invoice INV-2026-0412?"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,9em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid code{overflow-wrap:anywhere;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
CT, BR, AG, DT, IAP = "services/chat/tools.py", "services/chat/brains.py", "services/chat/agent.py", "shared/documind_tools.py", "shared/iap.py"
LIM = "services/chat/limits.py"
EXCERPTS = {
    "limits": ("services/chat/tools.py - the names refused before dispatch, and the budgets",
               block(CT, "BLOCKED = {", n=5)),
    "guard": ("services/chat/brains.py - the LangChain brain's guard: refuse a blocked name, run every other call within its budget",
              block(BR, "        def wrap_tool_call(self, request, handler):", end="    return GuardMiddleware()")),
    "timed": ("services/chat/limits.py - timed_tool_call(): the call runs in a pool, and the turn waits no longer than its budget",
              block(LIM, "def _payload_error(name: str, budget: float) -> dict:", end="async def timed_async(")),
    "meter": ("services/chat/limits.py - the defaults, and the Meter's check before each model call",
              block(LIM, 'MAX_MODEL_CALLS = int(os.environ.get("CHAT_MAX_MODEL_CALLS", "12"))', n=6) + "\n...\n"
              + block(LIM, "    def allow_model_call(self) -> bool:", n=15) + "\n...\n"
              + block(LIM, "    def tool_budget_s(self, name: str) -> float:", n=3)),
    "mw": ("services/chat/limits.py - TurnLimitsMiddleware: the Meter at LangChain's model call",
           block(LIM, "class TurnLimitsMiddleware(AgentMiddleware):", end="    async def awrap_model_call(")),
    "asdata": ("shared/documind_tools.py - a failed request comes back as data; the token is minted before the try",
               block(DT, '    headers = {"Authorization": f"Bearer {_id_token(RAG_API_URL)}"}', n=1) + "\n...\n"
               + block(DT, "    started = time.monotonic()", n=9)),
    "adapter": ("services/chat/tools.py - the chat adapter: doc_type passed through, a failure reshaped for the model",
                block(CT, "            doc_type=None if doc_type == \"all\" else doc_type,", n=1) + "\n...\n"
                + block(CT, "    if \"error\" in answer:", n=6)),
    "door": ("services/chat/agent.py - who is asking (401) and whether they may (403)",
             block(AG, "    except iap.IapError as e:", n=4) + "\n...\n" + block(AG, "    if tenant_id is None:", n=2)),
}
assert EXCERPTS["limits"][1].rstrip().endswith('TIMEOUTS = {"retrieve": documind_tools.RAG_TIMEOUT_S + 5, "calculate_processing_cost": 10}')
assert EXCERPTS["guard"][1].rstrip().endswith("return limits.timed_tool_call(request, handler)")
assert "return future.result(timeout=budget)" in EXCERPTS["timed"][1] and "logger.warning if elapsed > budget else logger.info" in EXCERPTS["timed"][1]
assert "# the first call is always allowed" in EXCERPTS["meter"][1] and 'MIN_MODEL_S = float(os.environ.get("CHAT_MIN_MODEL_S", "5"))' in EXCERPTS["meter"][1]
assert "return stop_message()" in EXCERPTS["mw"][1] and 'meter.stop("turn_deadline")' in EXCERPTS["mw"][1]
assert 'return {"error": "document retrieval is unavailable",' in EXCERPTS["asdata"][1]
assert 'return {"error": "document search is unavailable",' in EXCERPTS["adapter"][1]
assert 'raise HTTPException(401, str(e))' in EXCERPTS["door"][1] and 'raise HTTPException(403, "not a member of any tenant")' in EXCERPTS["door"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
ct_src, br_src, ag_src, dt_src, lim_src = ((KIT / p).read_text(encoding="utf-8") for p in (CT, BR, AG, DT, LIM))
main_src = (KIT / "services/rag-api/main.py").read_text(encoding="utf-8")
assert "import TIMEOUTS" not in br_src and "_timeouts().get(name, 30)" in lim_src                                      # the budget is read in limits.py
assert "ToolNode(TOOLS, wrap_tool_call=limits.timed_tool_call)" in br_src and "FunctionTool(limits.timed_adk(f))" in br_src  # every brain cuts a slow tool
assert br_src.count("limits.TurnLimitsMiddleware()") == 1 and "RunConfig(max_llm_calls=limits.MAX_MODEL_CALLS)" in br_src
assert '"limits": meter.summary()' in ag_src and '"limits": limits.published()' in ag_src
assert "raise ToolException(str(exc)) from None" in ct_src and "calculate_processing_cost.handle_tool_error = True" in ct_src   # an unknown tier, an error result
assert "        def tool_failed(tool, args, tool_context, error):" in br_src and "if not (unknown or isinstance(error, ToolException)):" in br_src   # the mint still raises
assert dt_src.index('headers = {"Authorization": f"Bearer {_id_token(RAG_API_URL)}"}') < dt_src.index("    try:\n        resp = requests.post(")
guard_logs = re.findall(r'logger\.(?:warning|info)\("([^"]+)"', br_src)
assert "refused %s (blocked list)" in guard_logs and '"%s took %.2fs (budget %ss)"' in lim_src                         # names and times, no arguments
chat_row = re.search(r'logger\.info\(json\.dumps\(\{"event": "chat",(.*?)\}\)\)', ag_src, re.S).group(1)
assert "args" not in chat_row and '"tool_calls": out.get("tool_calls", [])' in chat_row and '"stopped_by": used["stopped_by"]' in chat_row
assert 'WHERE jsonPayload.event IN ("query", "stream", "media")' in (KIT / "terraform/sql/tenant_daily.sql").read_text(encoding="utf-8")  # the month counts rag-api's rows
assert "rag-api still bills it" in lim_src and '"max_llm_calls"' not in (KIT / "services/agent/agent.py").read_text(encoding="utf-8")  # the peer has no cap of its own
usage = re.search(r"def usage_row\(.*?\n    return \{(.*?)\n\n\n", main_src, re.S).group(1)
assert '"pool"' in usage and "filters" not in usage                                                                  # the row keeps no filter
assert 'doc_type: Filter by type (policy, contract, invoice, form, research_paper, all)' in ct_src
assert 'doc_type: str = "unknown"' in (KIT / "services/ingest/contracts.py").read_text(encoding="utf-8")
assert "gcs_uri=msg.gcs_uri, pages=0)" in (KIT / "services/ingest/main.py").read_text(encoding="utf-8")                # a text upload keeps "unknown"
NO_EMAIL = re.search(r'raise IapError\("(the bearer token carries no verified email)"\)', (KIT / IAP).read_text(encoding="utf-8")).group(1)
EMPTY = re.search(r'EMPTY_POOL_ANSWER = \((.*?)\)\n', main_src, re.S).group(1)
EMPTY = "".join(re.findall(r'"([^"]*)"', EMPTY))
assert EMPTY.startswith("The corpus holds nothing near this question")
reqs = dict(re.findall(r"^([a-z-]+)==([\d.]+)$", (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8"), re.M))
PINS = {k: reqs[k] for k in ("langchain", "langchain-core", "requests", "google-auth")}
assert "RAG_TIMEOUT_S=90" in (KIT / "commands/lesson-12.8.sh").read_text(encoding="utf-8")

# ------------------------------------------------------------------ the cells
VENV = ("[ -x ~/graph-venv/bin/python ] || { python -m venv ~/graph-venv && ~/graph-venv/bin/pip install -q "
        + " ".join(f'"{k}=={v}"' for k, v in PINS.items()) + "; }   # lesson 5.4's venv, made here if it is missing\n"
        "~/graph-venv/bin/python -c 'import langchain; print(\"graph-venv ok: langchain\", langchain.__version__)'")

FAIL_PY = """import io, logging, sys, threading, time, warnings
warnings.filterwarnings("ignore")                  # the framework warns about a dict context; harmless
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
import shared.documind_tools as dt
import tools, brains, limits
class Slow(BaseHTTPRequestHandler):                # a rag-api that answers after two seconds
    def log_message(self, *a): pass
    def do_POST(self):
        time.sleep(2)
        try: self.send_response(200); self.end_headers(); self.wfile.write(b"{}")
        except OSError: pass                       # the client stopped waiting
srv = ThreadingHTTPServer(("127.0.0.1", 0), Slow)
threading.Thread(target=srv.serve_forever, daemon=True).start()
dt.RAG_API_URL, dt.RAG_TIMEOUT_S, dt._id_token = f"http://127.0.0.1:{srv.server_address[1]}", 0.5, lambda aud: "TOKEN"
log = io.StringIO()
for name in ("documind.chat.brains", "documind.chat.limits", "documind.chat.tools", "documind.agents.tools"):
    h = logging.StreamHandler(log); h.setFormatter(logging.Formatter("%(levelname)-7s %(message)s"))
    logging.getLogger(name).addHandler(h); logging.getLogger(name).setLevel(logging.INFO)
class Scripted(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kw): return self
def run(label, name, **args):
    turns = [AIMessage("", tool_calls=[{"name": name, "args": args, "id": "c1"}]), AIMessage("(the model explains what it read)")]
    b = brains.LangChainBrain(InMemorySaver(), llm=Scripted(responses=turns))
    cfg, meter = {"configurable": {"thread_id": "acme:you:" + label}}, limits.Meter()
    t = time.time()
    out = b.answer("...", config=cfg, context={"tenant_id": "acme", "brain": "langchain", "meter": meter})
    res = [m for m in b.agent.get_state(cfg).values["messages"] if isinstance(m, ToolMessage)][0]
    print(f"  {label:9} {time.time() - t:3.1f} s  refusals {out['refusals']}  tool_timeouts {meter.tool_timeouts}")
    print(f"            result [{res.status}] {str(res.content)[:72]}")
run("blocked", "delete_document", doc="inv_2026_0412")
run("bad args", "calculate_processing_cost", total_pages="many")
run("no such", "summon_rain")
run("timed out", "retrieve", query="gratuity")     # the client gives up first: RAG_TIMEOUT_S is 0.5 s here
dt.RAG_TIMEOUT_S, tools.TIMEOUTS["retrieve"] = 5, 1   # now the client would wait 5 s, and the budget is 1 s
run("cut", "retrieve", query="gratuity")
limits.TOOL_POOL.shutdown(wait=True)               # the abandoned call runs on until rag-api answers; wait for it
srv.shutdown()
print("  the log lines, from the guard's timer, the adapter and the one retrieve():")
for line in log.getvalue().splitlines():
    print("   ", line[:92])"""

LOOP_PY = """import sys, warnings
warnings.filterwarnings("ignore")                  # the framework warns about a dict context; harmless
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.checkpoint.memory import InMemorySaver
import brains, limits
class Model(BaseChatModel):                        # loop=True: asks for the cost tool again, every call
    loop: bool = True
    calls: int = 0
    @property
    def _llm_type(self): return "scripted"
    def bind_tools(self, tools, **kw): return self
    def _generate(self, messages, stop=None, run_manager=None, **kw):
        self.calls += 1
        ask = [{"name": "calculate_processing_cost", "args": {"total_pages": 283, "processing_type": "priority"}, "id": f"c{self.calls}"}]
        msg = AIMessage("", tool_calls=ask) if self.loop else AIMessage("USD 33.96 at the priority tier, about Rs 2,886.60.")
        return ChatResult(generations=[ChatGeneration(message=msg)])
saver, cfg = InMemorySaver(), {"configurable": {"thread_id": "acme:you:loop"}}
for n, question, model in ((1, "What would 283 pages cost at the priority tier?", Model(loop=True)),
                          (2, "Just give me the priority price, then.", Model(loop=False))):
    brain, meter = brains.LangChainBrain(saver, llm=model), limits.Meter(max_model_calls=3)   # a cap of 3, for a short run
    out = brain.answer(question, config=cfg, context={"tenant_id": "acme", "meter": meter})
    lim = meter.summary()
    print(f"  turn {n}  model calls {lim['model_calls']} of {lim['max_model_calls']}  tool calls {len(out['tool_calls'])}"
          f"  stopped_by {lim['stopped_by']}")
    print(f"          answer: {out['answer']}")
msgs = saver.get(cfg)["channel_values"]["messages"]
answered = {m.tool_call_id for m in msgs if isinstance(m, ToolMessage)}
asked = [c["id"] for m in msgs for c in getattr(m, "tool_calls", None) or []]
print(f"  the thread: {len(msgs)} messages, {len(asked)} tool calls, {len([c for c in asked if c not in answered])} left open")"""

ACCESS = ('export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"\n'
          "chatas() {   # one /v1/chat turn with the token in $1: the status, then the start of the body\n"
          f'  code=$(curl -s -o /tmp/chat103.json -w "%{{http_code}}" -X POST "$CHAT/v1/chat" -H "Authorization: Bearer $1" \\\n'
          f"    -H \"Content-Type: application/json\" -d '{{\"question\": \"{QG}\", \"session_id\": \"lesson103\"}}')\n"
          '  echo "  $code  $(head -c 100 /tmp/chat103.json)"\n'
          "}\n"
          'chatas "$(gcloud auth print-identity-token --include-email --audiences="$CHAT" \\\n'
          '    --impersonate-service-account="documind-outsider-sa@$PROJECT.iam.gserviceaccount.com" 2>/dev/null)"   # admitted by IAM, on no roster\n'
          'chatas "$(gcloud auth print-identity-token --audiences="$CHAT" \\\n'
          '    --impersonate-service-account="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" 2>/dev/null)"          # no --include-email\n'
          'chatas "$(tok "$CHAT")"                                                                                  # a roster member')

FILTER_PY = """from shared.documind_tools import retrieve
for doc_type in (None, "invoice"):
    r = retrieve("What is the total payable on invoice INV-2026-0412?", tenant_id="acme", top_k=5, doc_type=doc_type)
    print(f"  doc_type {str(doc_type):8} {len(r['citations'])} citations | answerable {r['answerable']} | {(r.get('answer') or '')[:58]}")"""

ROWS_PY = """import json, os, subprocess
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" '
     f'AND jsonPayload.tenant="acme" AND timestamp>="{os.environ["SINCE103"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "10",
                      "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j = e["jsonPayload"]
    print(f"  pool {j['pool']:>2}  answerable {str(j['answerable']):5}  backend {j['model_backend']:6}  Rs {j['cost_usd'] * 85:.4f}")"""


def heredoc(body: str, prefix: str = "", python: str = "python") -> str:
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


CELLS = {
    "venv": VENV,
    "fail": heredoc(FAIL_PY, python="~/graph-venv/bin/python"),
    "loop": heredoc(LOOP_PY, python="~/graph-venv/bin/python"),
    "check": "make limits-check   # the kit's own test file, in ~/graph-venv with the chat image's pins: no credential, no cost",
    "limits": 'make limits PROJECT="$PROJECT" REGION="$REGION"   # what the deployed chat publishes on /health',
    "drill": 'make limits-drill PROJECT="$PROJECT" REGION="$REGION" STOP=model_calls   # a minute or two; every chat turn stops meanwhile',
    "access": ACCESS,
    "filter": (heredoc(FILTER_PY, 'export SINCE103="$(date -u +%FT%TZ)"\nDOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" RAG_API_URL="$API" ')
               + "\nsleep 20   # Cloud Logging needs a moment to show the rows\n" + heredoc(ROWS_PY)),
}

T = Path(tempfile.mkdtemp(prefix="lesson103-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "SINCE103": "YYYY-MM-DDTHH:MM:SSZ"}


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout


ENV.pop("RAG_TIMEOUT_S", None)                     # the learner's shell does not set it: retrieve's budget is its default + 5
FAIL_RAW = re.sub(r"port=\d+", "port=PORT", run_cell(FAIL_PY, cwd=KIT))
TOOK = [float(t) for t in re.findall(r"took (\d+\.\d\d)s", FAIL_RAW)]
assert TOOK and all(min(abs(t - n) for n in (0, 0.5, 1, 2)) < 0.05 for t in TOOK), TOOK                # instant, the client, the budget, rag-api
# the log's times shown to the tenth, so a rebuild does not churn on the hundredths; the label says yours differ
OUT = {"fail": re.sub(r"took (\d+\.\d\d)s", lambda m: f"took {round(float(m.group(1)), 1):.2f}s", FAIL_RAW)}
F = OUT["fail"]
SHELL_RAG_S = float(re.search(r'RAG_TIMEOUT_S = float\(os\.environ\.get\("RAG_TIMEOUT_S", "(\d+)"\)\)',
                              (KIT / "shared/documind_tools.py").read_text(encoding="utf-8")).group(1))
assert re.search(rf"INFO    retrieve took 0\.\d\ds \(budget {SHELL_RAG_S + 5:g}s\)", F), F                         # the timed-out run's budget
assert '_id_token = f"http://127.0.0.1:{srv.server_address[1]}", 0.5,' in FAIL_PY and 'tools.TIMEOUTS["retrieve"] = 5, 1' in FAIL_PY   # step 3's budget sentence
assert "blocked   0.0 s  refusals ['delete_document']  tool_timeouts []" in F and "refusals ['calculate_processing_cost']" in F and "refusals ['summon_rain']" in F, F
assert re.search(r"timed out 0\.[5-9] s  refusals \[\]  tool_timeouts \[\]\n\s+result \[success\] \{\"error\": \"document search is unavailable\"", F), F
assert re.search(r"cut       1\.\d s  refusals \[\]  tool_timeouts \['retrieve'\]\n\s+result \[success\] \{\"error\": \"retrieve did not answer within 1s and was abandoned\"", F), F
assert "WARNING refused delete_document (blocked list)" in F and "WARNING rag-api query failed: document retrieval is unavailable" in F
assert re.search(r"WARNING retrieve took 1\.\d\ds \(budget 1s\)", F) and re.search(r"INFO    calculate_processing_cost took 0\.\d\ds \(budget 10s\)", F), F
OUT["venv"] = f"graph-venv ok: langchain {PINS['langchain']}\n"

# step 4: the looping model, the kit's own test file, make limits and the drill
OUT["loop"] = run_cell(LOOP_PY, cwd=KIT)
L = OUT["loop"]
assert "turn 1  model calls 3 of 3  tool calls 3  stopped_by model_calls" in L and "turn 2  model calls 1 of 3  tool calls 0  stopped_by None" in L, L
assert "the thread: 10 messages, 3 tool calls, 0 left open" in L and L.count("answer: I stopped this turn at one of its limits") == 1, L
chk = subprocess.run([sys.executable, "-m", "unittest", "commands/tests/test_chat_limits.py", "-v"], cwd=str(KIT), capture_output=True, text=True,
                     encoding="utf-8", env={**ENV, "DOCUMIND_REQUIRE_LIBS": "1"})
assert chk.returncode == 0 and chk.stderr.rstrip().endswith("OK") and "skipped" not in chk.stderr, chk.stderr[-1500:]
N_TESTS = int(re.search(r"Ran (\d+) tests in", chk.stderr).group(1))
OUT["check"] = re.sub(r"Ran (\d+) tests in [\d.]+s", r"Ran \1 tests in N.NNNs", chk.stderr)    # the run time is yours

HEALTH = json.loads(run_cell("import sys, json\nsys.path[:0] = ['.', '../..']\nimport agent\nprint(json.dumps(agent.health()))\n",
                             cwd=KIT / "services/chat", env={"CHECKPOINT_DSN": "memory", "RAG_TIMEOUT_S": "90"}))    # the lane's 90, from lesson-12.8.sh
LIMS = HEALTH["limits"]
assert (LIMS["max_model_calls"], LIMS["budget_inr"], LIMS["deadline_s"], LIMS["tool_budgets_s"]["retrieve"]) == (12, 5.0, 100.0, 95.0), LIMS
PEER_KEYS = re.search(r"JSONResponse\(\{(.*?)\}\)", (KIT / "services/agent/agent.py").read_text(encoding="utf-8"), re.S).group(1)
PEER = {k: "..." for k in re.findall(r'"(\w+)":', PEER_KEYS)}                                 # the peer's /health keys, as its code names them
OUT["limits"] = run_cell("import sys, json, argparse\nsys.path.insert(0, 'commands')\nimport lane\n"
                         f"H = {{'documind-chat': {HEALTH!r}, 'documind-agent': {PEER!r}}}\n"
                         "lane._health = lambda svc, project, region: (f'https://{svc}-NUMBER.{region}.run.app', H[svc])\n"
                         f"sys.exit(lane.cmd_limits(argparse.Namespace(project={PROJ!r}, region='asia-south1')))\n", cwd=KIT)
assert "model calls a turn    12" in OUT["limits"] and "retrieve 95 s" in OUT["limits"] and "not on its /health (ADK defaults to 500)" in OUT["limits"], OUT["limits"]

# the drill: the kit's limits-drill.sh and smoke_chat.py, with a fake gcloud that keeps the service's env in a file,
# against a stand-in chat whose /health is the kit's health() and whose limits are the kit's Meter at that env
sys.path[:0] = [str(KIT), str(KIT / "services/chat")]
import limits  # noqa: E402
D = Path(tempfile.mkdtemp(prefix="lesson103-drill-"))
(D / "env.json").write_text("{}", encoding="utf-8")
STAND_TOKENS = ((1850, 40), (3900, 95))            # invented: a call that asks for the search, and the one that answers
RAG_USD = 0.003331                                 # one rag-api answer, as on step 6's row
CITES = [{"chunk_id": f"acme:payment_of_gratuity_act_1972#{4 + k}", "quote": "..."} for k in range(5)]
ANSWERS = {"direct": ("Gratuity becomes payable after not less than five years of continuous service [1].", 3120),
           "langchain": ("Gratuity becomes payable once you have rendered at least five years of continuous service [1].", 11840),
           "langgraph": ("Gratuity is payable after at least five years of continuous service [1].", 9730),
           "adk": ("After five years of continuous service, gratuity becomes payable [1].", 14260)}


def reply(h, code: int, body) -> None:
    data = json.dumps(body, separators=(",", ":")).encode()
    h.send_response(code)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(data)))
    h.end_headers()
    h.wfile.write(data)


class Chat(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        env = json.loads((D / "env.json").read_text(encoding="utf-8"))
        cap = int(env.get("CHAT_MAX_MODEL_CALLS", LIMS["max_model_calls"]))
        reply(self, 200, {**HEALTH, "limits": {**LIMS, "max_model_calls": cap}})

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        env = json.loads((D / "env.json").read_text(encoding="utf-8"))
        meter = limits.Meter(max_model_calls=int(env.get("CHAT_MAX_MODEL_CALLS", LIMS["max_model_calls"])),
                             model="gemini-3.6-flash")
        brain = req.get("brain") or HEALTH["default_brain"]
        text, ms = ANSWERS[brain]
        if brain == "direct":                       # rag-api answers; the chat service makes no model call of its own
            meter.charge_rag({"cost_usd": RAG_USD})
        else:
            for k, (t_in, t_out) in enumerate(STAND_TOKENS):
                if not meter.allow_model_call():
                    text = limits.STOP_ANSWER
                    break
                meter.charge_model(t_in, t_out)
                if k == 0:
                    meter.charge_rag({"cost_usd": RAG_USD})
        cites = [dict(c, n=k) for k, c in enumerate(CITES, 1)] if brain != "direct" else CITES
        reply(self, 200, {"answer": text, "tool_calls": ["retrieve"], "refusals": [], "citations": cites, "brain": brain,
                          "session_id": req["session_id"], "latency_ms": ms, "limits": meter.summary()})


chat = ThreadingHTTPServer(("127.0.0.1", 0), Chat)
threading.Thread(target=chat.serve_forever, daemon=True).start()
chat_url = f"http://127.0.0.1:{chat.server_address[1]}"
(D / "bin").mkdir()
(D / "bin/gcloud").write_text(f"""#!{sys.executable}
import json, sys
a, env = " ".join(sys.argv[1:]), json.load(open({str(D / "env.json")!r}))
if a.startswith("projects describe"): print("123456789012")
elif a.startswith("auth print-identity-token"): print("TOKEN")
elif "describe --format=json" in a:
    print(json.dumps({{"spec": {{"template": {{"spec": {{"containers": [{{"env": [{{"name": k, "value": v}} for k, v in env.items()]}}]}}}}}},
                      "status": {{"traffic": [{{"latestRevision": True, "percent": 100}}]}}}}))
elif "--update-env-vars=" in a:
    k, v = a.split("--update-env-vars=")[1].split()[0].split("=", 1); env[k] = v
    json.dump(env, open({str(D / "env.json")!r}, "w"))
elif "--remove-env-vars=" in a:
    env.pop(a.split("--remove-env-vars=")[1].split()[0], None); json.dump(env, open({str(D / "env.json")!r}, "w"))
""", encoding="utf-8")
(D / "bin/py").write_text(f'#!/usr/bin/env bash\n[ "$1" = smoke/smoke_chat.py ] && export DOCUMIND_CHAT_URL={chat_url}\nexec {sys.executable} "$@"\n',
                          encoding="utf-8")
for f in ("gcloud", "py"):
    (D / "bin" / f).chmod(0o755)
drill = subprocess.run(["bash", "commands/limits-drill.sh"], cwd=str(KIT), capture_output=True, text=True, encoding="utf-8",
                       env={**ENV, "PATH": f"{D / 'bin'}:{os.environ['PATH']}", "PROJECT": PROJ, "REGION": "asia-south1",
                            "STOP": "model_calls", "PY": str(D / "bin/py")})
chat.shutdown()
assert drill.returncode == 0 and not drill.stderr.strip(), drill.stdout[-1500:] + drill.stderr[-800:]
assert json.loads((D / "env.json").read_text(encoding="utf-8")) == {}, "the drill left the cap on"
shutil.rmtree(D, ignore_errors=True)
OUT["drill"] = drill.stdout.replace(chat_url, "https://documind-chat-NUMBER.asia-south1.run.app")
DR = OUT["drill"]
assert DR.count("[PASS] brain langchain stopped  stopped_by=model_calls calls=1") == 1 and DR.count("5 passed, 0 failed") == 2, DR
assert ">> restored: CHAT_MAX_MODEL_CALLS unset, the default applies" in DR and DR.rstrip().endswith("5 passed, 0 failed"), DR
assert "limits=1 calls, Rs 5.0, 100.0 s" in DR and "limits=12 calls, Rs 5.0, 100.0 s" in DR, DR

# the access cell: the three identities, against a local stub that answers the way agent.py does
ANSWER = "Gratuity becomes payable after not less than five years of continuous service [1]."
REPLIES = {"outsider": (403, {"detail": "not a member of any tenant"}), "noemail": (401, {"detail": NO_EMAIL}),
           "member": (200, {"answer": ANSWER, "tool_calls": ["retrieve"], "refusals": [], "brain": "langchain", "session_id": "lesson103", "latency_ms": 7020})}
OUT["access"] = "".join(f"  {c}  {json.dumps(b, separators=(',', ':'))[:100]}\n" for c, b in REPLIES.values())
assert 'raise HTTPException(401, str(e))' in ag_src

# the filter cell: the kit's retrieve() against a local stub of rag-api that filters the way the lane does - doc_type
# is "unknown" on every text document, so "invoice" empties the pool and the API answers with its empty-pool text
CITES = [{"chunk_id": f"acme:{'b' * 8}#{i}", "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/inv_2026_0412.md", "page": 1, "quote": "...", "score": 0.9} for i in range(5)]
INV = "The total payable on invoice INV-2026-0412 is Rs 1,84,500 [1]."
SEEN = []


class Api(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        SEEN.append(req)
        empty = (req.get("filters") or {}).get("doc_type") not in (None, "unknown")
        body = ({"answer": EMPTY, "citations": [], "confidence": "low", "answerable": False} if empty
                else {"answer": INV, "citations": CITES, "confidence": "high", "answerable": True})
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


api = ThreadingHTTPServer(("127.0.0.1", 0), Api)
threading.Thread(target=api.serve_forever, daemon=True).start()
filt = run_cell(FILTER_PY, "import shared.documind_tools as _d\n_d._id_token = lambda audience: 'TOKEN'\n",
                env={"RAG_API_URL": f"http://127.0.0.1:{api.server_address[1]}"}, cwd=KIT)
api.shutdown()
assert SEEN[1]["filters"] == {"doc_type": "invoice"} and "filters" not in SEEN[0], SEEN
FAKE_GCLOUD = ("import json, sys, types\n"
               "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
               "ROWS = [{'pool': 20, 'answerable': True, 'model_backend': 'vertex', 'cost_usd': 0.003331}, {'pool': 0, 'answerable': False, 'model_backend': 'none', 'cost_usd': 0.0}]\n"
               "def run(cmd, **kw): return R(json.dumps([{'jsonPayload': r} for r in ROWS]))\n"
               "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
rows = run_cell(ROWS_PY, FAKE_GCLOUD)
assert 'backend="none", cost_usd=0.0, tokens_in=0, tokens_out=0, latency_ms=0, cache_hit="none")' in main_src      # the empty pool is free
OUT["filter"] = filt + rows
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "venv": "run in the operator shell, in the kit (the venv from lesson 5.4, made if it is missing)",
    "fail": "run in the operator shell, in the kit (five failures through the kit's LangChain brain; no model, no network beyond your machine)",
    "loop": "run in the operator shell, in the kit (a model that never stops asking, then the next turn on its thread; offline)",
    "check": "run in the operator shell, in the kit (every agent brain against the limits, offline)",
    "limits": "run in the operator shell, in the kit (reads /health as documind-ui-sa; changes nothing)",
    "drill": "run in the operator shell, in the kit (caps the deployed chat at one model call, smokes it, and puts it back)",
    "access": "run in the operator shell, in the kit (three identities at the chat service's door)",
    "filter": "run in the operator shell, in the kit (one question with and without a doc_type filter, then rag-api's rows)",
}
OUT_LABELS = {
    "venv": "",
    "fail": "(this cell run on the kit's own brains.py and limits.py; the error texts are the installed LangChain's, the log's times are shown to the tenth and yours differ by a few hundredths, and the port is picked at random)",
    "loop": "(this cell run on the kit's own brains.py and limits.py)",
    "check": "(the kit's own test file, run when this page was built; your times differ)",
    "limits": "(lane.py's cmd_limits over the kit's own health() with RAG_TIMEOUT_S=90, as lesson-12.8.sh sets it, and the peer's /health keys as its code names them; your region and NUMBER are yours)",
    "drill": "(the kit's limits-drill.sh and smoke_chat.py against a fake gcloud and a stand-in chat whose limits are the kit's Meter; the answers, timings, token counts and rupees are invented)",
    "access": "(against a local stub; the 401 and 403 texts are agent.py's and shared/iap.py's own)",
    "filter": "(the kit's retrieve() against a local stub that filters as the lane does, then a fake gcloud)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: where each failure surfaces
line_of = lambda label: re.search(rf"  {re.escape(label)}\s+\S+ s  refusals (\[.*?\])  tool_timeouts (\[.*?\])\n\s+result \[(\w+)\] (.*)", F)  # noqa: E731
FAIL = {}
for key, label in (("blocked", "blocked"), ("badargs", "bad args"), ("nosuch", "no such"), ("timeout", "timed out"), ("cut", "cut")):
    m = line_of(label)
    FAIL[key] = {"refusals": m.group(1), "timeouts": m.group(2), "status": m.group(3), "text": m.group(4).strip()}
W = {
    "outsider": {"label": "an account on no roster calls the chat service", "layer": "the chat service's roster check, before any brain runs",
                 "caller": "HTTP 403 not a member of any tenant", "model": "nothing: no turn starts", "lists": "no answer, so no lists",
                 "logs": "the request log: 403", "waits": "no", "find": "the status and the detail; the roster in tenants/{t}/members"},
    "noemail": {"label": "a token that names nobody", "layer": "shared/iap.identity(), the bearer leg", "caller": f"HTTP 401 {NO_EMAIL}",
                "model": "nothing: no turn starts", "lists": "no answer, so no lists", "logs": "the request log: 401", "waits": "no",
                "find": "the token was minted without --include-email"},
    "blocked": {"label": "the model asks for a blocked tool", "layer": "the guard, before dispatch", "caller": "HTTP 200, and the model's explanation",
                "model": FAIL["blocked"]["text"], "lists": f"refusals {FAIL['blocked']['refusals']}", "logs": "WARNING refused ... (blocked list)", "waits": "no",
                "find": "refusals names it; the log says blocked list"},
    "badargs": {"label": "the model sends an argument of the wrong type", "layer": "LangChain's argument check, inside the tool call",
                "caller": "HTTP 200, and the model's explanation", "model": FAIL["badargs"]["text"], "lists": f"refusals {FAIL['badargs']['refusals']}",
                "logs": "only the guard's timing line; the arguments are logged nowhere", "waits": "no", "find": "refusals names the tool, the same way it names a blocked one"},
    "nosuch": {"label": "the model names a tool that does not exist", "layer": "LangChain's tool lookup", "caller": "HTTP 200, and the model's explanation",
               "model": FAIL["nosuch"]["text"], "lists": f"refusals {FAIL['nosuch']['refusals']}", "logs": "the guard's timing line, with the default budget",
               "waits": "no", "find": "refusals names a tool that is not in the kit"},
    "timeout": {"label": "rag-api answers after RAG_TIMEOUT_S", "layer": "requests' read timeout inside the one retrieve()", "caller": "HTTP 200, and the model's explanation",
                "model": FAIL["timeout"]["text"], "lists": f"refusals {FAIL['timeout']['refusals']}: a timeout is data, not a refusal",
                "logs": "WARNING rag-api query failed: document retrieval is unavailable",
                "waits": f"until RAG_TIMEOUT_S, 90 seconds on the lane; the tool's budget, {LIMS['tool_budgets_s']['retrieve']:g} s, is behind it",
                "find": "the answer says search is unavailable; the chat log's warning"},
    "cut": {"label": "a tool call runs past its budget", "layer": "limits.timed_tool_call: the smaller of the tool's budget and the turn's time left",
            "caller": "HTTP 200, the model's explanation, and limits.tool_timeouts", "model": FAIL["cut"]["text"],
            "lists": f"refusals {FAIL['cut']['refusals']}: a cut call is data; tool_timeouts {FAIL['cut']['timeouts']}",
            "logs": "WARNING retrieve took 1.00s (budget 1s), and tool_timeouts on the chat row",
            "waits": "no: the turn goes on at the budget, and the abandoned call runs on in its thread", "find": "limits.tool_timeouts on the answer and the row"},
    "loop": {"label": "the model never stops asking for tools", "layer": "the Meter, checked before each model call (TurnLimitsMiddleware)",
             "caller": "HTTP 200, the stop sentence, and limits.stopped_by model_calls", "model": "nothing more: the call over the cap is never made",
             "lists": "tool_calls as asked, refusals [], stopped_by model_calls", "logs": "the chat row: model_calls, cost_usd, stopped_by",
             "waits": f"no: at most {LIMS['max_model_calls']} model calls a turn", "find": "stopped_by on the answer and the row; the next turn answers"},
    "hung": {"label": "the model does not answer", "layer": "the model call's own timeout, set per call from the turn's time left",
             "caller": "HTTP 200, the stop sentence, and limits.stopped_by turn_deadline", "model": "nothing: its call timed out",
             "lists": "stopped_by turn_deadline", "logs": "the chat row: stopped_by turn_deadline",
             "waits": f"up to min({LIMS['model_timeout_s']:g} s, time left / {LIMS['model_attempts']}) an attempt, {LIMS['model_attempts']} attempts",
             "find": "stopped_by turn_deadline on the answer and the row"},
    "doctype": {"label": "the model filters by a doc_type the corpus does not stamp", "layer": "rag-api's retrieval: the filter empties the pool",
                "caller": "HTTP 200, and an answer that the corpus holds nothing", "model": "citations [], answerable false: a normal, empty result",
                "lists": "tool_calls ['retrieve'], refusals []", "logs": "rag-api's row: pool 0, answerable false; the filter itself is logged nowhere",
                "waits": "no", "find": "pool 0 on the row beside a question the corpus can answer"},
}
UI_JS = r"""var root = document.getElementById('fs'); if (!root) return;
  var W = %s, $ = function(id){ return document.getElementById(id); };
  var ROWS = [['layer', 'Caught by'], ['caller', 'The caller gets'], ['model', 'The model reads'], ['lists', 'The four keys'], ['logs', 'The logs keep'], ['waits', 'The turn waits'], ['find', 'How you find it']];
  function esc(s){ return String(s).replace(/[&<>]/g, function(c){ return {'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c]; }); }
  function render(){ var w = W[$('fs-f').value];
    $('fs-out').innerHTML = ROWS.map(function(r){ return '<b>' + r[1] + '</b><span>' + esc(w[r[0]]) + '</span>'; }).join(''); }
  $('fs-f').innerHTML = Object.keys(W).map(function(k){ return '<option value="' + k + '">' + esc(W[k].label) + '</option>'; }).join('');
  $('fs-f').value = 'cut';
  $('fs-f').addEventListener('change', render); render();""" % json.dumps(W)

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"PIN_LC": PINS["langchain"], "NO_EMAIL": NO_EMAIL, "N_FAIL": str(len(W)), "N_TESTS": str(N_TESTS),
         "MAX_CALLS": str(LIMS["max_model_calls"]), "BUDGET_INR": f"{LIMS['budget_inr']:g}", "DEADLINE_S": f"{LIMS['deadline_s']:g}",
         "MODEL_S": f"{LIMS['model_timeout_s']:g}", "ATTEMPTS": str(LIMS["model_attempts"]), "MIN_S": f"{LIMS['min_model_s']:g}",
         "RETRIEVE_S": f"{LIMS['tool_budgets_s']['retrieve']:g}", "COST_S": f"{LIMS['tool_budgets_s']['calculate_processing_cost']:g}",
         "BACKSTOP": str(limits.recursion_limit()), "SHELL_RAG_S": f"{SHELL_RAG_S:g}", "SHELL_RETRIEVE_S": f"{SHELL_RAG_S + 5:g}"}

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
print(f"kit: five failures through the kit's LangChain brain, their refusals, results and log lines its own | a looping model stopped at 3 |"
      f" {N_TESTS} limits tests green | {len(W)} failures in the panel, their texts from the runs and from agent.py, shared/iap.py and main.py |"
      f" live cells against stand-ins")
