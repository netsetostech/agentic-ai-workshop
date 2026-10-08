"""Lesson 5.7: Two adapters over one tool, side by side

Do it: the venv Do it: side by side

Run order inside this file:
1. Do it: the venv (source window 13)
2. Do it: side by side (source window 15)

Prerequisites: setup_prepare.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


# Original CLI workflow for step_01_the_venv.
COMMANDS_01 = """[ -x ~/graph-venv/bin/python ] || python -m venv ~/graph-venv   # lesson 5.4's venv, made here if it is missing
~/graph-venv/bin/pip install -q "langchain==1.4.0" "langchain-core==1.6.2" "requests==2.34.2" "google-auth==2.57.1" \\
  "google-adk==2.8.0" "google-genai==2.22.0" "langchain-google-genai==4.4.0"   # the chat image's pins; ADK is new here
~/graph-venv/bin/python -c 'import google.adk, langchain; print("graph-venv ok: google-adk", google.adk.__version__, "langchain", langchain.__version__)'

"""

def step_01_the_venv(session):
    """Run Do it: the venv at this checkpoint.

    Do it: the venv

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (lesson 5.4's venv, with google-adk added).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: graph-venv ok: google-adk 2.8.0 langchain 1.4.0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_side_by_side.
COMMANDS_02 = """~/graph-venv/bin/python - <<'PY'
import json, logging, sys, textwrap, threading, warnings
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
srv.shutdown()
PY

"""

def step_02_side_by_side(session):
    """Run Do it: side by side at this checkpoint.

    Do it: side by side

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the two adapters side by side; no model, no network beyond your machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1. what each model is shown for retrieve (* = required); raw = FunctionTool over the shared retrieve(), unadapted
       langchain query*, doc_type, top_k                                          481 characters
       adk       query*, doc_type, top_k                                          635 characters
       raw       query*, tenant_id*, top_k, doc_type, assertion, brain, passages  3,420 characters
       langchain tools: retrieve, calculate_processing_cost
       adk tools:       retrieve, calculate_processing_cost   (tools.for_adk())
    2. one retrieve(); the ADK model writes tenant_id "globex" and assertion "anything"
       langchain rag-api got tenant acme, brain langchain, assertion header None
            
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_the_venv),
        ('source_15', step_02_side_by_side),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
