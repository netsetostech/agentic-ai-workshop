"""Build lesson 10.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Plan first or decide each step. The agent bench (commands/agent_patterns.py) runs one chained question - three figures,
each a search and then its calculator - three ways on the Desk agent's toolset (arm A*: one retrieve over every class,
and the seven calculators of shared/desk_calc.py). loop is the Desk agent's own loop, which decides each call after
reading the last result. plan_execute is a planner call that writes a numbered plan, an executor that carries it out a
step at a time with the desk's tools through ToolNode, one replan after a refused or failed step, and a solver. rewoo is
one planner call that writes every step with placeholders (#E1), checked by code before any tool runs and run in waves,
an extract worker that must quote the figure it reads, and a solver, with no replan. Every call has a role and is priced
at its own model's rates; --exec-model puts the act and extract calls on gemini-3.1-flash-lite.

Offline, at build time, with the chat image's pins (build with the chat venv's python), no credential and no network:
agent_turn.py --offline for the loop and plan_execute on the stated-cap row, run as the learner runs them; the rewoo
turn in process on a warm lane (each search ranked once, as the eval ranks them after the loop), and beside it the same
turn cold through the CLI, held to differ in nothing but its passage numbers and token counts; the Change-it, MAX_REPLANS
set to 0 in memory (the file on disk is never touched), with git's own diff --stat for that edit in a scratch repository;
the plan's readers and scheduler (read_rewoo, check_rewoo, needs, next_wave, resolve, read_figure) through the page's
standard-library cell; agent_eval.py --check and --offline on the chained slice, with the planner's model and with a
flash-lite executor, saved, then read back by the page's own cell. In process: every chained row through every pattern
and both executors, for the Level 0 panel, whose traces also price the lane's runs for RUN_LIST.md. Step 10's cell: the
kit's ADK brain with ADK_PLANNER on (ADK's PlanReActPlanner, services/chat/brains.py), on a scripted model with the
search stood in, run as the learner runs it. The live outputs come from the author's lane: pb.recorded() reads them
from data/ (RUN_LIST.md says how each is recorded).

    python pagekit/build.py 10.2        (the chat venv; a few minutes, most of them the offline evals)
"""
import atexit
import html
import importlib.util
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "10.2"
title = ("<title>Lesson 10.2 Plan first or decide each step: plan-and-execute - the loop, plan-and-execute and ReWOO on "
         "the same chained rows | Netsetos</title>\n")
warnings.filterwarnings("ignore")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the Level 0 panel: one chained question through the three patterns, one card at a time */
.pe-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:8px 12px;margin:4px 0 10px;}
.pe-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pe-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;width:100%;}
.pe-nav{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 10px;}
.pe-nav button{font:inherit;font-size:var(--small-size);padding:6px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);cursor:pointer;min-height:max(40px,var(--touch));}
.pe-nav button:active{transform:scale(.97);}
.pe-nav button:disabled{color:#94a3b8;cursor:default;}
.pe-at{font-family:var(--mono);font-size:var(--kicker-size);color:var(--slate);letter-spacing:.5px;}
.pe-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:10px;align-items:start;}
.pe-col{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;min-width:0;overflow-wrap:anywhere;}
.pe-name{font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--teal);}
.pe-how{font-size:12px;line-height:1.45;color:var(--slate);margin:2px 0 6px;}
.pe-strip{display:flex;flex-wrap:wrap;gap:3px;margin:2px 0 4px;}
.pe-chip{font-family:var(--mono);font-size:10.5px;font-weight:700;line-height:1;padding:4px 5px;border-radius:4px;color:#fff;opacity:.28;}
.pe-chip.on{opacity:1;}
.r-loop{background:#334155;}.r-plan{background:#0f1729;}.r-act{background:#0d9488;}.r-extract{background:#0891b2;}.r-replan{background:#b45309;}.r-solve{background:#065f46;}
.pe-tally{font-family:var(--mono);font-size:11px;color:var(--navy);margin:0 0 4px;}
.pe-c{border-top:1px dashed var(--border);padding:6px 0 4px;font-size:12.5px;line-height:1.5;}
.pe-h{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--teal-dark);}
.pe-h.code{color:var(--cyan);}
.pe-l{margin:3px 0;}
.pe-l b{display:block;font-size:11.5px;color:var(--navy);font-weight:600;}
.pe-l pre{font-family:var(--mono);font-size:11.5px;line-height:1.45;white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f5f9;border-radius:6px;padding:4px 6px;margin:2px 0;color:var(--slate);}
.pe-l.bad pre{color:#991b1b;background:#fef2f2;}
.pe-l.bad b{color:#991b1b;}
.pe-a{border-top:2px solid var(--teal);margin-top:4px;padding:6px 0 2px;font-size:12.5px;line-height:1.5;}
.pe-a.bad{border-top-color:#c2410c;}
.pe-a p{margin:2px 0;}
.pe-sum{font-family:var(--mono);font-size:11px;color:var(--navy);margin:6px 0 0;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim kit excerpts
AP, AT, AE, MK, TP = ("commands/agent_patterns.py", "commands/agent_turn.py", "evals/agent_eval.py", "mk/agents.mk",
                      "commands/tests/test_agent_plans.py")
BR = "services/chat/brains.py"
EXCERPTS = {
    "pe_prompts": ("commands/agent_patterns.py - PLANNER, EXECUTOR, REPLANNER and SOLVER: what each of plan_execute's calls is told",
                   block(AP, "PLANNER = (", end="REWOO_PLANNER = (")),
    "pe_read": ("commands/agent_patterns.py - read_plan() and said_of(): a plan's steps, and a tool's result in three words",
                block(AP, "def read_plan(", end="def said_line(")),
    "pe_nodes": ("commands/agent_patterns.py - _plan_execute(): the step node, and the replan that rewrites the steps not yet run",
                 block(AP, "    def step(state):", end="    def solve(state, runtime):")),
    "pe_graph": ("commands/agent_patterns.py - MAX_REPLANS, and _plan_execute()'s routing and graph",
                 block(AP, "MAX_REPLANS = 1", n=1) + "\n...\n"
                 + block(AP, "    def onward(state):                   # after plan, step and replan", end="    try:")),
    "by_name": ("commands/agent_patterns.py - by_name(): what the executor reads of a search",
                block(AP, "def by_name(", end="def done_lines(")),
    "rw_prompts": ("commands/agent_patterns.py - REWOO_PLANNER and EXTRACTOR: the plan written once, and the worker",
                   block(AP, "REWOO_PLANNER = (", end="EXTRACT = ")),
    "check_rewoo": ("commands/agent_patterns.py - check_rewoo(): a plan refused before any tool runs",
                    block(AP, "def check_rewoo(", end="def needs(")),
    "waves": ("commands/agent_patterns.py - needs() and next_wave(): what each step waits for, and each wave",
              block(AP, "def needs(", end="def resolve(")),
    "fill": ("commands/agent_patterns.py - resolve() and read_figure(): a placeholder filled, a worker's figure held to its quote",
             block(AP, "def resolve(", end="def _figure_of(") + "\n...\n" + block(AP, "def read_figure(", end="def evidence_lines(")),
    "wave_msg": ("commands/agent_patterns.py - _rewoo()'s wave node: one message code builds, never sent to a model",
                 block(AP, "        if calls:                            # one message code builds and never sends", n=4)),
    "barrier": ("commands/tests/test_agent_plans.py - the kit's test that a wave's searches run side by side",
                block(TP, "    def test_a_waves_calls_run_side_by_side(self):",
                      end="    def test_a_forward_placeholder_is_refused_before_any_tool_runs(self):")),
    "score": ("evals/agent_eval.py - score(): a chained row, each part as a calculator row",
              block(AE, '    if row["kind"] == "chained":', end='    elif row["kind"] == "refuse":')),
    "roles": ("evals/agent_eval.py - by_role() and executor_arms(): calls and rupees by role, an arm per executor",
              block(AE, "def by_role(") + "\n...\n" + block(AE, "def executor_arms(", end="def _one_arm(")),
    "priced": ("commands/agent_patterns.py - EXEC_MODELS and turn_limits(): each call charged at its own model's rates",
               block(AP, "# Lesson 10.2: an executor's model", n=2) + "\n...\n" + block(AP, "def turn_limits(", end="def _ask(")),
    "gemini": ("commands/agent_patterns.py - gemini(): the planner's client, and the executor's on another model",
               block(AP, "def gemini(", end="def run(")),
    "at": ("commands/agent_turn.py - --row and --exec-model, and the turn they run",
           block(AT, '    ap_.add_argument("--row"', n=1) + "\n...\n" + block(AT, '    ap_.add_argument("--exec-model"', n=2)
           + "\n...\n" + block(AT, "        if a.offline:", end="    except Exception as e:")),
    "mk": ("mk/agents.mk - make agent-turn and make agent-eval, with ROW and EXEC_MODEL",
           block(MK, "agent-turn: $(if $(OFFLINE),,guard-project)", n=2) + "\n\n"
           + block(MK, "agent-eval: $(if $(or $(OFFLINE),$(CHECK),$(REPLAY),$(COMPARE)),,guard-project)", n=2)),
    "adk_planner": ("services/chat/brains.py - ADK_PLANNER: off unless set, and set on the ADK brain's agent once it is built",
                    block(BR, "# ADK's own planner on the ADK brain", n=4) + "\n...\n"
                    + block(BR, "        # ADK_PLANNER (workshop lesson 10.2), set on the agent once it is built", n=8)),
    "adk_join": ("services/chat/brains.py - the ADK brain's answer: the text not marked thought, or the plan, labelled",
                 block(BR, "            if ev.is_final_response() and ev.content and ev.content.parts:", n=7)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["pe_prompts"].startswith("PLANNER = (") and "SOLVER = (" in E["pe_prompts"] and "REPLANNER = (" in E["pe_prompts"]
assert E["pe_prompts"].rstrip().endswith('"tool.")')
assert E["pe_read"].startswith("def read_plan(") and 'return "failed" if isinstance(body, dict) and body.get("error") else "returned"' in E["pe_read"]
assert 'bad = next((t for t in ran if t["said"] != "returned"), None)' in E["pe_nodes"] and 'kept["replans"] += 1' in E["pe_nodes"]
assert E["pe_nodes"].rstrip().endswith('return {"messages": [reply], "plan": steps, "failed": "", "replans": state["replans"] + 1}')
assert E["pe_graph"].startswith("MAX_REPLANS = 1 ") and 'if state["failed"] and state["replans"] < MAX_REPLANS:' in E["pe_graph"]
assert E["pe_graph"].rstrip().endswith('g.add_edge("solve", END)')
assert 'p.get("doc_type") == "policy"' in E["by_name"]
assert E["rw_prompts"].startswith("REWOO_PLANNER = (") and "EXTRACTOR = (" in E["rw_prompts"]
assert E["check_rewoo"].rstrip().endswith("return None") and "if len(steps) > cap:" in E["check_rewoo"]
assert "def next_wave(" in E["waves"] and E["waves"].rstrip().endswith("return ready, never")
assert "def read_figure(" in E["fill"] and E["fill"].rstrip().endswith("return (int(figure) if figure == figure.to_integral_value() else float(figure)), quote, None")
assert 'new.append(AIMessage(content="", tool_calls=calls, id=f"rewoo-wave-{w}"))' in E["wave_msg"]
assert "threading.Barrier(3, timeout=20)" in E["barrier"] and "self.assertFalse(barrier.broken)" in E["barrier"]
assert E["score"].lstrip().startswith('if row["kind"] == "chained":') and "provenance = by_all and not flagged" in E["score"]
assert "def by_role(" in E["roles"] and "def executor_arms(" in E["roles"]
assert 'EXEC_MODELS = tuple(m for m in prices.PRICES if m.startswith("gemini-"))' in E["priced"]
assert "meter.charge_model(*limits.usage_of(m), model=model)" in E["priced"]
assert "if model not in EXEC_MODELS:" in E["gemini"] and "location=da.GEN_LOCATION, thinking_level=da.THINKING_LEVEL," in E["gemini"]
assert "executor=ap.gemini(a.exec_model) if a.exec_model else None)" in E["at"]
assert "ROW=$(ROW) EXEC_MODEL=$(EXEC_MODEL)" in E["mk"] and "--exec-model $(EXEC_MODEL)" in E["mk"]
assert 'ADK_PLANNER = os.environ.get("ADK_PLANNER", "")' in E["adk_planner"] and 'if ADK_PLANNER == "plan_react":' in E["adk_planner"]
assert "root.planner = PlanReActPlanner()" in E["adk_planner"] and E["adk_planner"].rstrip().endswith("no planner\", ADK_PLANNER)")
assert 'for p in ev.content.parts if not p.thought)' in E["adk_join"]
assert E["adk_join"].rstrip().endswith('out["answer"] = out["answer"].strip() or NO_FINAL_ANSWER + plan')
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit, imported (the chat image's pins)
sys.path[:0] = [str(KIT / "commands"), str(KIT / "services" / "chat"), str(KIT), str(KIT / "evals")]
import agent_patterns as ap  # noqa: E402
import agent_turn as at  # noqa: E402
import limits  # noqa: E402
import paired  # noqa: E402
from shared import desk_calc, prices  # noqa: E402

prices.PROFILE = "gcp"       # list prices, whatever DOCUMIND_PROFILE the build's own shell carries: the page prices a lane
da = ap._da()
MODEL, LITE = da.AGENT_MODEL, "gemini-3.1-flash-lite"
RATE_IN, RATE_OUT = prices.PRICES[MODEL]
LITE_IN, LITE_OUT = prices.PRICES[LITE]
assert (MODEL, RATE_IN, RATE_OUT, LITE_IN, LITE_OUT, prices.USD_INR) == ("gemini-3.6-flash", 1.50, 7.50, 0.25, 1.50, 85)
assert RATE_IN / LITE_IN == 6 and RATE_OUT / LITE_OUT == 5           # "a sixth of the input price and a fifth of the output"
assert ap.EXEC_MODELS == ("gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-3.1-pro-preview")
assert ap.MAX_REPLANS == 1 and ap.ROLES == ("plan", "act", "extract", "replan", "solve")
for _name in ("plan_execute", "rewoo"):
    _p = ap.PATTERNS[_name]
    assert (_p.lessons, _p.executor, _p.text) == ("10.2", True, False), _name
assert not any(ap.PATTERNS[n].executor for n in ("loop", "react_text", "plan_first"))
assert (limits.MAX_MODEL_CALLS, limits.TURN_BUDGET_INR, limits.TURN_DEADLINE_S) == (12, 5.0, 100.0)
assert da.THINKING_LEVEL == "low" and ap.classes_for("astar") == ["policy", "statute", "guidance"]
assert ap.SCRIPTED_THINKING["low"] == 64 and ap.CHARS_PER_TOKEN == 4
DT_SRC = (KIT / "shared" / "documind_tools.py").read_text(encoding="utf-8")
assert 'RAG_TIMEOUT_S = float(os.environ.get("RAG_TIMEOUT_S", "20"))' in DT_SRC
assert 'TIMEOUTS = {"retrieve": documind_tools.RAG_TIMEOUT_S + 5,' in (KIT / "services" / "chat" / "tools.py").read_text(encoding="utf-8")
assert "RAG_TIMEOUT_S=90|" in (KIT / "commands" / "lesson-12.8.sh").read_text(encoding="utf-8")   # the chat service's own
AP_SRC = (KIT / AP).read_text(encoding="utf-8")
AP_FLAT = " ".join(AP_SRC.split())                    # the kit's docstring may re-wrap (lesson 10.3's kit did)
assert "a cold wave can reach the search's 25 s budget" in AP_FLAT and "rewoo's passage numbers can differ from run to run" in AP_FLAT
assert AP_SRC.count("out = g.compile().invoke(") == 3                 # react_text, plan_execute, rewoo: no checkpointer
assert "REPLAN" not in (KIT / MK).read_text(encoding="utf-8")         # one replan, fixed: no make variable, no flag
assert "--replan" not in (KIT / AT).read_text(encoding="utf-8") and "--replan" not in (KIT / AE).read_text(encoding="utf-8")
assert re.findall(r"^\s*MAX_REPLANS\s*=.*$", AP_SRC, re.M) == [block(AP, "MAX_REPLANS = 1", n=1)]   # set once, a constant
assert "os.environ" not in block(AP, "MAX_REPLANS = 1", n=1)
assert "act_recorder=recorder(thinking, model=model_name(executor))" in AP_SRC   # one thinking level for every role
assert 'model="none", backend="none", cost_usd=0.0' in (KIT / "services" / "rag-api" / "main.py").read_text(encoding="utf-8")
assert ("check_args reads the person's question, never the step, so a plan cannot bring a number of its own"
        in " ".join(AP_SRC.split()))
assert '"tool_calls": [tc["name"] for m in messages for tc in (getattr(m, "tool_calls", None) or [])],' in (
    KIT / "services" / "chat" / "brains.py").read_text(encoding="utf-8")       # the caption's tools: each call, in order
RAG_BUDGET = 20 + 5                                                     # documind_tools' default, plus tools.TIMEOUTS' 5 s
assert '"replan"' not in AP_SRC.split("def _rewoo(", 1)[1].split("@dataclass(frozen=True)", 1)[0]   # ReWOO has no replan node
chat_tools = (KIT / "services" / "chat" / "tools.py").read_text(encoding="utf-8")
assert "TOOLS = [retrieve, calculate_processing_cost]" in chat_tools          # Level 1: the chat brains hold no calculator
assert 'location="global", thinking_level="low",' in (KIT / "shared" / "profile.py").read_text(encoding="utf-8")
TASKS = ap.tasks()
ROWS = {r["id"]: r for r in TASKS}
CHAINED = [r for r in TASKS if r["kind"] == "chained"]
assert [r["id"] for r in CHAINED] == ["chained-exit-e3", "chained-exit-saturday", "chained-exit-stated-cap"]
STATED = ROWS["chained-exit-stated-cap"]
E3 = ROWS["chained-exit-e3"]
assert [p.get("stated") for p in STATED["parts"]] == [None, {"cap": 100}, None]
assert all(not ap.slips(r, run) for r in CHAINED for run in range(5))   # a chained row never slips: eval runs = single turns
ae_spec = importlib.util.spec_from_file_location("agent_eval_lesson_102", KIT / AE)
ae = importlib.util.module_from_spec(ae_spec)
ae_spec.loader.exec_module(ae)
assert [r["id"] for r in ae.select(TASKS, "chained")] == [r["id"] for r in CHAINED]
assert paired.MARGIN == 0.03 and paired.MARGIN_REGISTERED == "2026-10-08"
DECL = "\n".join(json.dumps(d, ensure_ascii=False) for d in ap.declarations("astar"))
DECL_TOKENS = math.ceil(len(DECL) / ap.CHARS_PER_TOKEN)                # the desk's tools, as Gemini receives them bound
N_TOOLS = len(da.TOOLSETS["astar"])
assert N_TOOLS == 8 and [t.name for t in da.TOOLSETS["astar"]][0] == "retrieve"
sh_src = (KIT / "commands" / "agent-turn.sh").read_text(encoding="utf-8")
assert 'if [ -n "${ROW:-}" ]; then ARGS+=(--row "$ROW"); fi' in sh_src and 'REGION="${REGION:-us-central1}"' in sh_src

# LangChain's own form of a kept plan, in the chat image's pin, read from the installed file
import importlib.metadata as md  # noqa: E402
assert md.version("langchain") == "1.4.0" and md.version("langgraph") == "1.2.12"
TODO = Path(md.distribution("langchain").locate_file("langchain/agents/middleware/todo.py")).read_text(encoding="utf-8")
assert "class TodoListMiddleware(AgentMiddleware[PlanningState[ResponseT], ContextT, ResponseT]):" in TODO
assert 'name="write_todos",' in TODO and 'status: Literal["pending", "in_progress", "completed"]' in TODO
assert "The `write_todos` tool should never be called multiple times" in TODO
assert "TodoListMiddleware" not in AP_SRC and "write_todos" not in AP_SRC     # the kit does not use it

# ADK's own form, PlanReActPlanner, on the chat's ADK brain behind ADK_PLANNER (step 10): the switch as brains.py holds
# it, and the planner's instruction and flow read from the chat image's pin, the instruction sized and priced per call
BR_SRC = (KIT / BR).read_text(encoding="utf-8")
ADK_BRAIN = BR_SRC[BR_SRC.index("class AdkBrain:"):BR_SRC.index("class DirectBrain:")]
assert BR_SRC.count('os.environ.get("ADK_PLANNER"') == 1 and re.findall(r'ADK_PLANNER == "(\w+)"', BR_SRC) == ["plan_react"]
assert "BuiltInPlanner" not in BR_SRC and "thinking" not in ADK_BRAIN               # one planner; no thinking level set
assert "planner" not in ADK_BRAIN[ADK_BRAIN.index("root = LlmAgent("):ADK_BRAIN.index("if peer.PEER_URL:")]   # set after
OTHER_BRAINS = BR_SRC[BR_SRC.index("class LangChainBrain:"):BR_SRC.index("class AdkBrain:")] + BR_SRC[BR_SRC.index(
    "class DirectBrain:"):]
assert "planner" not in OTHER_BRAINS.lower()                                 # the ADK brain alone
assert "--set-env-vars" in (KIT / "commands" / "lesson-12.8.sh").read_text(encoding="utf-8")   # a redeploy clears it
ADK_VER = md.version("google-adk")
assert re.search(r"(?m)^google-adk==([\d.]+)$", (KIT / "services" / "chat" / "requirements.txt").read_text(
    encoding="utf-8")).group(1) == ADK_VER == "2.8.0"
from google.adk.planners import PlanReActPlanner  # noqa: E402
PR_TEXT = PlanReActPlanner().build_planning_instruction(None, None)
assert all(t in PR_TEXT for t in ("/*PLANNING*/", "/*REASONING*/", "/*ACTION*/", "/*FINAL_ANSWER*/", "/*REPLANNING*/"))
assert "The tool code snippets should be under /*ACTION*/" in PR_TEXT      # it asks for tool code as text
PR_TOKENS = math.ceil(len(PR_TEXT) / ap.CHARS_PER_TOKEN)
PR_RS = PR_TOKENS * RATE_IN * prices.USD_INR / 1e6                          # on every model call, at the input rate
NL_SRC = Path(md.distribution("google-adk").locate_file("google/adk/flows/llm_flows/_nl_planning.py")).read_text(
    encoding="utf-8")
assert "if not hasattr(agent, 'planner') or not agent.planner:" in NL_SRC   # read from the agent on every request
assert "part.thought = None" in NL_SRC                                       # the plan goes back as plain text

# ------------------------------------------------------------------ the offline runs: the kit's own output, no network
SCRATCH = Path(tempfile.mkdtemp(prefix="lesson102_"))


def remove_scratch() -> None:
    """The build's scratch folder, gone: git's read-only objects made writable first, as Windows needs."""
    def writable(func, path, _exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH, onexc=writable)


atexit.register(remove_scratch)                    # gone even when an assertion stops the build
HOME = SCRATCH / "home"
HOME.mkdir()
HOME_P = HOME.as_posix()                       # the scripts' home, written with / so a path prints as it does on a lane
GIT = shutil.which("git")
assert GIT, "git is needed for the Change-it's diff --stat"
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
         "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
         "HOME": HOME_P, "USERPROFILE": HOME_P, "APPDATA": HOME_P, "LOCALAPPDATA": HOME_P,
         "CLOUDSDK_CONFIG": HOME_P + "/gcloud", "TEMP": str(SCRATCH), "TMP": str(SCRATCH)}   # no gcloud, no ADC, no project


def as_learner(text: str) -> str:
    """This machine's scratch home written as the learner's, /home/you."""
    return text.replace(HOME_P, "/home/you")


def run_py(args: list, stdin: str | None = None, env: dict | None = None, ok=(0,)) -> tuple[str, str]:
    """A kit script or a page cell, run here with the chat venv's python in the kit's folder: (stdout, stderr)."""
    r = subprocess.run([sys.executable] + args, input=stdin, cwd=str(KIT), capture_output=True, text=True,
                       encoding="utf-8", env={**QUIET, **(env or {})})
    assert r.returncode in ok, (args, r.returncode, r.stdout[-1500:], r.stderr[-1500:])
    return r.stdout, r.stderr


def background(args: list, name: str, env: dict | None = None):
    """A long kit run started now and read later: (the process, its stdout file, its stderr file)."""
    out = open(SCRATCH / f"{name}.out", "w+", encoding="utf-8")
    err = open(SCRATCH / f"{name}.err", "w+", encoding="utf-8")
    proc = subprocess.Popen([sys.executable] + args, cwd=str(KIT), stdout=out, stderr=err, env={**QUIET, **(env or {})})
    return proc, out, err


def collect(job, timeout=1800) -> tuple[str, str]:
    """A background run's (stdout, stderr), once it has ended well."""
    proc, out, err = job
    assert proc.wait(timeout=timeout) == 0, (proc.args, out.name)
    out.seek(0)
    err.seek(0)
    got = (out.read(), err.read())
    out.close()
    err.close()
    return got


def quiet_err(err: str) -> None:
    """Nothing but the eval's own progress lines may reach stderr."""
    bad = [ln for ln in err.splitlines() if ln.strip() and not re.match(r"  \[\d+/\d+\] \S+ run \d+: ", ln)]
    assert not bad, bad[:5]


# the long ones first, in the background: the two offline evals on the chained slice, saved, and the cold rewoo turn
SAVED_OFF, SAVED_LITE = HOME_P + "/plans-offline.jsonl", HOME_P + "/plans-lite-offline.jsonl"
EVAL_ARGS = [AE, "--offline", "--patterns", "loop,plan_execute,rewoo", "--slice", "chained", "--save", SAVED_OFF]
LITE_ARGS = [AE, "--offline", "--patterns", "plan_execute,rewoo", "--slice", "chained", "--exec-model", LITE, "--save", SAVED_LITE]
EVAL_JOB = background(EVAL_ARGS, "eval")
LITE_JOB = background(LITE_ARGS, "lite")
# the rewoo turn as a learner's first offline run makes it: every search ranked cold, side by side. The page's own run
# is warm (below); this one is held to the same steps, waves, figures and calls. Time is no question here, so the
# search's budget and the turn's deadline are raised past anything a busy build machine needs.
COLD_JOB = background([AT, "--offline", "--pattern", "rewoo", "--row", E3["id"]], "cold",
                      env={"RAG_TIMEOUT_S": "300", "CHAT_TURN_DEADLINE_S": "900"})

OUT = {}
# the loop on the stated-cap row, filtered to its calls, as the page's cell filters it
LOOP_FILTER = r"^(model call|  -> |       (=|refused)|[0-9]+ model calls|the turn failed|make: )"
loop_full, err = run_py([AT, "--offline", "--row", STATED["id"]])
assert not err.strip(), err
OUT["loop_stated"] = "\n".join(ln for ln in loop_full.splitlines() if re.match(LOOP_FILTER, ln)) + "\n"
OUT["pe_stated"], err = run_py([AT, "--offline", "--pattern", "plan_execute", "--row", STATED["id"]])
assert not err.strip(), err

# the Change-it: plan_execute with MAX_REPLANS = 0, as the learner's sed leaves the file
NOREPLAN_PY = """import importlib.util, sys
from pathlib import Path
sys.path[:0] = ["commands", "services/chat", "."]
path = Path("commands/agent_patterns.py").resolve()
src = path.read_text(encoding="utf-8")
changed = src.replace("\\nMAX_REPLANS = 1 ", "\\nMAX_REPLANS = 0 ", 1)
assert changed != src
mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("agent_patterns", loader=None, origin=str(path)))
mod.__file__ = str(path)
sys.modules["agent_patterns"] = mod
exec(compile(changed, str(path), "exec"), mod.__dict__)
import agent_turn
sys.exit(agent_turn.main(["--offline", "--pattern", "plan_execute", "--row", "%s"]))
""" % STATED["id"]
noreplan_full, err = run_py(["-"], stdin=NOREPLAN_PY)
assert not err.strip(), err
TRIM = r"^(         \[|  - |  Worked out in code:)"            # the cell's grep -vE: passage lists and code's lines
OUT["noreplan"] = "\n".join(ln for ln in noreplan_full.splitlines() if not re.match(TRIM, ln)) + "\n"

# git's own words for the edit and the restore, in a scratch repository holding the same file
REPO = SCRATCH / "kit"
(REPO / "commands").mkdir(parents=True)
shutil.copyfile(KIT / AP, REPO / AP)
GIT_ENV = {**os.environ, "HOME": str(HOME), "USERPROFILE": str(HOME), "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": str(SCRATCH / "gitconfig"), "LC_ALL": "C", "LANG": "C"}


def git(*args) -> str:
    """git in the scratch repository: what it prints, stdout and stderr together, as a terminal shows them."""
    r = subprocess.run([GIT, "-c", "core.autocrlf=false", "-c", "color.ui=never", *args], cwd=str(REPO),
                       capture_output=True, text=True, encoding="utf-8", env=GIT_ENV)
    assert r.returncode == 0, (args, r.stderr)
    return r.stdout + r.stderr


git("init", "-q")
git("add", AP)
git("-c", "user.name=kit", "-c", "user.email=kit@example.com", "commit", "-q", "-m", "kit")
src_lines = (REPO / AP).read_text(encoding="utf-8").splitlines(keepends=True)
with open(REPO / AP, "w", encoding="utf-8", newline="") as f:          # sed -i 's/^MAX_REPLANS = 1 /MAX_REPLANS = 0 /'
    f.writelines(re.sub(r"^MAX_REPLANS = 1 ", "MAX_REPLANS = 0 ", ln) for ln in src_lines)
STAT = git("diff", "--stat")
assert re.fullmatch(r" commands/agent_patterns\.py \| 2 \+-\n 1 file changed, 1 insertion\(\+\), 1 deletion\(-\)\n", STAT), STAT
RESTORED = git("checkout", "-q", "--", AP) + git("diff", "--stat")
assert RESTORED == "", RESTORED
assert (REPO / AP).read_text(encoding="utf-8") == (KIT / AP).read_text(encoding="utf-8")
ONE_COUNT = sum(bool(re.match(r"^MAX_REPLANS = 1 ", ln)) for ln in (REPO / AP).read_text(encoding="utf-8").splitlines())
assert ONE_COUNT == 1                                                    # grep -c '^MAX_REPLANS = 1 '
OUT["change"] = STAT + OUT["noreplan"]
OUT["restore"] = RESTORED + f"{ONE_COUNT}\n"

OUT["check"], err = run_py([AE, "--check", "--slice", "chained"])
assert not err.strip(), err
assert OUT["check"].rstrip().endswith("every question let through by the hard gate") and OUT["check"].count("\nok    ") == 2
assert "the stated cap = 100 is refused by check_args" in OUT["check"]


# ------------------------------------------------------------------ every chained row through every pattern, in process
def one_turn(mod, pattern: str, row: dict, exec_model: str | None = None) -> dict:
    """One single turn as make agent-turn OFFLINE=1 runs it: the row's scripted models, desk astar, no slip."""
    llm = mod.scripted(row["question"], row["tenant"], task=row, pattern=pattern)
    executor = (mod.scripted(row["question"], row["tenant"], task=row, pattern=pattern, model=exec_model)
                if exec_model else None)
    return mod.run(pattern, row["question"], llm=llm, desk="astar", tenant=row["tenant"], executor=executor)


def written_order(turn: dict) -> bool:
    """A rewoo turn whose waves committed in the order the plan wrote them: each search's passages numbered after
    the one written above it, and the calculators' results kept in the order written (code's "Worked out in code"
    lines follow it). A wave's calls finish in any order; on a warm lane they come back as written."""
    waves = [s for e in turn["plan"]["log"] if e["event"] == "wave" for s in e["steps"]]
    ns = [[p["n"] for p in (s.get("result") or {}).get("passages") or ()] for s in waves if s["tool"] == "retrieve"]
    worked = [s["tool"] for s in waves if s["tool"] not in ("retrieve", ap.EXTRACT) and s.get("state") == "ok"]
    return (all(a and b and max(a) < min(b) for a, b in zip(ns, ns[1:]))
            and [c["calculator"] for c in turn["calculations"]] == worked)


EXECS = {"flash": None, "lite": LITE}
TURNS = {r["id"]: {"loop": None, "flash": {}, "lite": {}} for r in CHAINED}
with ap.offline():                          # one lane for the build: each search ranked once, as the eval ranks them
    for r in CHAINED:                       # the loop first, its searches one at a time
        TURNS[r["id"]]["loop"] = one_turn(ap, "loop", r)
    for r in CHAINED:
        for ex, model in EXECS.items():
            for p in ("plan_execute", "rewoo"):
                for _try in range(5):       # a thread race can reorder a warm wave's commits: the page keeps the written order
                    TURNS[r["id"]][ex][p] = one_turn(ap, p, r, model)
                    if p != "rewoo" or written_order(TURNS[r["id"]][ex][p]):
                        break
                assert p != "rewoo" or written_order(TURNS[r["id"]][ex][p]), (r["id"], ex)


def score(row: dict, turn: dict) -> dict:
    return ae.score(row, turn)


def flagged(turn: dict) -> list:
    return desk_calc.unsupported(turn["answer"], turn["calculations"], turn["question"],
                                 *[p.get("text") or "" for p in turn["passages"]])


for rid, by in TURNS.items():
    row = ROWS[rid]
    loop = by["loop"]
    assert loop["model_calls"] == 7 and loop["refusals"] == [] and score(row, loop)["correct"], rid
    assert loop["tool_calls"] == ["retrieve", "notice_end", "retrieve", "encashable_days", "retrieve", "gratuity_estimate"]
    for ex in EXECS:
        pe, rw = by[ex]["plan_execute"], by[ex]["rewoo"]
        assert pe["stopped_by"] is None and rw["stopped_by"] is None and not flagged(pe) and not flagged(rw), (rid, ex)
        assert score(row, pe)["correct"] and score(row, pe)["provenance"], (rid, ex)
        assert pe["answer"] == by["flash"]["plan_execute"]["answer"] and rw["answer"] == by["flash"]["rewoo"]["answer"]
        small = "act"
        for c in pe["calls"]:
            assert c["model"] == (EXECS[ex] or MODEL if c["role"] == small else MODEL), (rid, ex, c["role"])
        for c in rw["calls"]:
            assert c["model"] == (EXECS[ex] or MODEL if c["role"] == "extract" else MODEL), (rid, ex, c["role"])
        if rid == STATED["id"]:
            assert (pe["model_calls"], pe["plan"]["replans"], pe["refusals"]) == (10, 1, ["encashable_days"])
            assert [c["role"] for c in pe["calls"]] == ["plan", "act", "act", "act", "replan", "act", "act", "act", "act", "solve"]
            assert (rw["model_calls"], rw["refusals"], rw["plan"]["refused"]) == (3, ["encashable_days"], None)
            assert not score(row, rw)["correct"] and "Earned leave encashed on exit: not worked out" in rw["answer"]
            assert rw["plan"]["waves"] == [["#E1", "#E2"], ["#E3", "#E5", "#E6"], ["#E4"]]
        else:
            assert (pe["model_calls"], pe["plan"]["replans"], pe["refusals"]) == (8, 0, [])
            assert rw["model_calls"] == 4 and score(row, rw)["correct"] and score(row, rw)["provenance"]
            assert rw["plan"]["waves"] == [["#E1", "#E2", "#E3"], ["#E4", "#E5", "#E8"], ["#E6", "#E7"]]
LOOP_S, PE_S, RW_S = TURNS[STATED["id"]]["loop"], TURNS[STATED["id"]]["flash"]["plan_execute"], TURNS[STATED["id"]]["flash"]["rewoo"]
PE_SL, RW_SL = TURNS[STATED["id"]]["lite"]["plan_execute"], TURNS[STATED["id"]]["lite"]["rewoo"]
RW_E3 = TURNS[E3["id"]]["flash"]["rewoo"]
# the page's plan_execute output is the CLI's, and the in-process turns are the same turns
assert OUT["pe_stated"] == at.render(PE_S, True) + "\n"
assert f"tokens: in {LOOP_S['tokens_in']:,}, thinking {LOOP_S['thinking_tokens']:,}, visible {LOOP_S['visible_tokens']:,}; Rs {LOOP_S['inr']:.4f}" in loop_full
OUT["rewoo_e3"] = at.render(RW_E3, True) + "\n"
assert "wave 1: #E1, #E2, #E3, together" in OUT["rewoo_e3"] and "waves: 3 (#E1, #E2, #E3 | #E4, #E5, #E8 | #E6, #E7)" in OUT["rewoo_e3"]
PE_T, RW_T, NR_T = OUT["pe_stated"], OUT["rewoo_e3"], OUT["noreplan"]
assert "  the step was refused\n" in PE_T and "plans: 2 written, 1 replan (at most 1 a turn)" in PE_T
assert "10 model calls (12 at most), 3 searches, 3 calculations, 1 refused or failed tool call; stopped by nothing" in PE_T
REFUSAL = re.search(r"refused: (cap = 100 is not written in LV-07[^\n]*)\n", PE_T).group(1)    # the word once (13 October 2026)
assert REFUSAL == ("cap = 100 is not written in LV-07 of a handbook passage this turn read: search for that clause and "
                   "use the figure it states")
assert "plans: 1 written, 0 replans (at most 0 a turn)" in NR_T and "the step was refused" in NR_T
assert "Earned leave encashed on exit: not worked out, as encashable_days refused what it was given [1]." in NR_T
assert "LV-07 — Leave on exit" not in noreplan_full                    # "no passage of LV-07 was ever read"
NR_CALLS = int(re.search(r"\n(\d+) model calls \(12 at most\)", NR_T).group(1))
NR_RS = re.search(r"\ntokens: in [\d,]+, thinking [\d,]+, visible [\d,]+; Rs ([\d.]+)", NR_T).group(1)
assert NR_CALLS == 7
assert '       = 60, quoting "A confirmed employee at grade E3 or above serves a notice period of 60 days."' in RW_T
assert 'run as notice_end(ack_date="2026-10-05", days=60)' in RW_T and "4 model calls (12 at most), 3 searches, 3 calculations" in RW_T

# ------------------------------------------------------------------ the plan's readers, at Rs 0 (the standard library)
E3_PLAN = RW_E3["calls"][0]["text"]
assert ap.check_rewoo(ap.read_rewoo(E3_PLAN), {t.name for t in da.TOOLSETS["astar"]}, limits.MAX_MODEL_CALLS) is None
LV07 = next(p for p in RW_E3["passages"] if str(p.get("section") or "").startswith("LV-07"))
LV07_SENT = next(s for s in re.split(r"(?<=[.;])\s+|\n+(?=[^a-z\s])", LV07["text"]) if "45" in s)
LV07_SENT = " ".join(LV07_SENT.split())
assert LV07_SENT == "Earned leave is encashed on exit at basic pay, capped at 45 days.", LV07_SENT
DESK_TOOLS = [t.name for t in da.TOOLSETS["astar"]]
CHECK_PY = r'''import json, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["commands", "."]
import agent_patterns as ap      # the standard library and shared/ at import: the plan's readers need no framework

TOOLS = %(tools)s       # the desk's eight
PLAN = """%(plan)s"""
steps = ap.read_rewoo(PLAN)
tool = {s["id"]: s["tool"] for s in steps}
print(f"{len(steps)} steps read; check_rewoo refuses: {ap.check_rewoo(steps, TOOLS, 12) or 'nothing'}")
for sid, (values, after) in ap.needs(steps).items():
    print(f"  {sid} {tool[sid]:<17} takes {', '.join(values) or '-':<4} runs after {', '.join(after) or '-'}")
outcome, wave = {}, 0
while len(outcome) < len(steps):                     # every step returns: the waves
    ready, never = ap.next_wave(steps, outcome)
    wave += 1
    print(f"wave {wave}: {', '.join(ready)}")
    outcome.update({sid: {"state": "ok", "value": 1} for sid in ready})
done = {sid: {"state": "ok", "value": 1} for sid in ("#E1", "#E2", "#E3", "#E4", "#E8")}
done["#E5"] = {"state": "refused"}                   # suppose LV-07's cap could not be read
print("after #E5 is refused:", ap.next_wave(steps, done))
for bad in ('#E1 = notice_end[{"ack_date": "2026-10-05", "days": "#E2"}]\n#E2 = retrieve[{"query": "notice period"}]',
            '#E1 = retrieve[{"query": "earned leave encashed on exit"}]\n#E2 = encashable_days[{"balance": 80, "cap": "#E1"}]',
            '#E1 = payroll_update[{"days": 45}]',
            "\n".join(f'#E{i} = retrieve[{{"query": "q{i}"}}]' for i in range(1, 14))):
    print("refused:", ap.check_rewoo(ap.read_rewoo(bad), TOOLS, 12))
print(ap.resolve({"balance": 50, "cap": "#E5"}, {"#E5": 45}))
lv07 = [{"n": 6, "text": "%(sent)s"}]       # a passage that writes LV-07's sentence
for quote in ("%(sent)s", "Leave is encashed up to 45 days."):
    print(ap.read_figure(json.dumps({"value": 45, "quote": quote}), lv07))''' % {
    "plan": E3_PLAN, "sent": LV07_SENT, "tools": json.dumps(DESK_TOOLS)}
OUT["readers"], err = run_py(["-"], stdin=CHECK_PY)
assert not err.strip(), err
RD = OUT["readers"]
assert RD.startswith("8 steps read; check_rewoo refuses: nothing\n"), RD[:200]
assert "#E1 uses #E2 before #E2 runs: a step may use only the steps written above it" in RD
assert "#E2 gives cap the passages of #E1: a search returns passages, not a figure, so read the figure with extract" in RD
assert "#E1 calls payroll_update, which is not one of this desk's tools" in RD
assert "it has 13 steps, and a turn runs at most 12: the tools of a plan written once run with no model call between them" in RD
assert "{'balance': 50, 'cap': 45}" in RD and "(None, 'Leave is encashed up to 45 days.', 'its quote is not written in the passages it was given')" in RD
assert f"(45, '{LV07_SENT}', None)" in RD and "after #E5 is refused: (['#E6'], {'#E7': '#E5 was refused'})" in RD
assert "\nwave 1: #E1, #E2, #E3\nwave 2: #E4, #E5, #E8\nwave 3: #E6, #E7\n" in RD, RD

# ------------------------------------------------------------------ step 10: ADK's planner on the kit's own ADK brain
# The page's cell, run here as the learner runs it (the chat image's pins, in the kit): ADK_PLANNER on, a scripted model,
# the search stood in. Then the lane's cell, which only the author's run fills (data/adk_planner.txt).
PLANNER_PY = r'''import asyncio, logging, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
logging.disable(logging.WARNING)                    # ADK's notes on a scripted model's missing usage
os.environ["ADK_PLANNER"] = "plan_react"           # the switch, as the chat service reads it at import
os.environ["CHECKPOINT_DSN"] = ""                  # the ADK brain's sessions in memory
sys.path[:0] = ["services/chat", "."]
import brains
from shared import documind_tools
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types as gt

QUOTE = "A confirmed employee serves 60 days' notice."
documind_tools.retrieve = lambda query, **kw: {"answerable": True, "confidence": "high", "citations": [
    {"chunk_id": "acme:handbook#4", "source_uri": "gs://bucket/acme/handbook.pdf", "page": 4, "quote": QUOTE, "score": 0.9}]}
PLAN = "/*PLANNING*/\n1. Search the handbook for the notice period.\n2. Answer with the figure and its source."


class Script(BaseLlm):
    """Gemini, scripted: each call returns the next reply, and keeps the request it was sent."""
    model: str = "scripted"
    replies: list = []
    sent: list = []

    async def generate_content_async(self, llm_request, stream=False):
        """The next scripted reply."""
        self.sent.append(llm_request.model_copy(deep=True))
        yield self.replies.pop(0)


def reply(*parts):
    """A model reply: a string is a text part, a (name, args) pair a tool call."""
    return LlmResponse(content=gt.Content(role="model", parts=[gt.Part(text=p) if isinstance(p, str) else
                                                               gt.Part(function_call=gt.FunctionCall(name=p[0], args=p[1])) for p in parts]))


def turn(session, *replies):
    """One turn of the kit's ADK brain on the scripted replies: the brain, its model, and what answer() returned."""
    brain = brains.AdkBrain(None)
    brain.runner.agent.model = model = Script(replies=list(replies), sent=[])
    out = brain.answer("What notice does a confirmed employee serve?",
                       config={"configurable": {"thread_id": f"acme:you:{session}"}},
                       context={"tenant_id": "acme", "user_id": "you", "assertion": ""})
    return brain, model, out


brain, model, out = turn("plan", reply(PLAN, ("retrieve", {"query": "notice period confirmed employee"})),
                         reply("/*REASONING*/\nThe handbook says 60 days.\n/*FINAL_ANSWER*/\nSixty days of notice [1]."))
print("ADK_PLANNER:", brains.ADK_PLANNER, "| the agent's planner:", type(brain.runner.agent.planner).__name__)
told = str(model.sent[0].config.system_instruction)
print("call 1 is told to plan:", "/*PLANNING*/" in told and "/*FINAL_ANSWER*/" in told)
sess = asyncio.run(brain.svc.get_session(app_name="documind", user_id="you", session_id="acme:you:plan"))
for ev in sess.events:
    for p in (ev.content.parts if ev.content and ev.content.parts else []):
        if ev.author == "documind_adk" and p.text:
            print(f"  stored, thought={p.thought}: {p.text.strip()!r}")
        elif p.function_call:
            print(f"  stored, a tool call: {p.function_call.name}({dict(p.function_call.args)})")
resent = [p.thought for c in model.sent[1].contents for p in (c.parts or []) if p.text and "Search the handbook" in p.text]
print("call 2 is sent the plan back, thought =", resent)
print("the answer:", repr(out["answer"]), "| tool calls:", out["tool_calls"], "| citations:", len(out["citations"]))
_, _, out = turn("all-plan", reply(PLAN))
print("a reply that is all plan answers:")
print(out["answer"])'''
OUT["planner"], err = run_py(["-"], stdin=PLANNER_PY)
assert not err.strip(), err
PL = OUT["planner"]
assert PL.startswith("ADK_PLANNER: plan_react | the agent's planner: PlanReActPlanner\ncall 1 is told to plan: True\n"), PL
assert ("  stored, thought=True: '1. Search the handbook for the notice period.\\n2. Answer with the figure and its source.'\n"
        "  stored, a tool call: retrieve({'query': 'notice period confirmed employee'})\n") in PL, PL
assert "  stored, thought=True: 'The handbook says 60 days.'\n  stored, thought=None: 'Sixty days of notice [1].'\n" in PL, PL
assert "call 2 is sent the plan back, thought = [None]\n" in PL                    # ADK resends it as plain text
assert "the answer: 'Sixty days of notice [1].' | tool calls: ['retrieve'] | citations: 1\n" in PL, PL
assert PL.endswith("a reply that is all plan answers:\nThe model wrote a plan but no final answer. Its plan:\n"
                   "1. Search the handbook for the notice period.\n2. Answer with the figure and its source.\n"), PL

PLANNER_LANE_PY = r'''import json, os, subprocess, time, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
SVC = ["gcloud", "run", "services", "update", "documind-chat", "--region", os.environ["REGION"],
       "--project", os.environ["PROJECT"], "--quiet"]
Q = "What notice period does a confirmed E3 employee at ACME serve?"


def ask(label):
    """One ADK turn on /v1/chat, printed: its tool calls, model calls, rupees and answer."""
    body = {"question": Q, "session_id": f"lesson102-planner-{label}-{int(time.time())}", "brain": "adk"}
    req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + os.environ["CHAT_TOKEN"], "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    used = r["limits"]
    print(f"ADK_PLANNER {label}: tool calls {r['tool_calls']}, {used['model_calls']} model calls, Rs {used['cost_inr']}, "
          f"stopped by {used['stopped_by']}")
    print("  answer:", " ".join(r["answer"].split())[:400])


ask("off")
subprocess.run(SVC + ["--update-env-vars", "ADK_PLANNER=plan_react"], check=True, capture_output=True)
try:
    ask("on")
finally:                                             # the switch goes back off, whatever the turn did
    subprocess.run(SVC + ["--remove-env-vars", "ADK_PLANNER"], check=True, capture_output=True)
    print("ADK_PLANNER removed from documind-chat again")'''
assert 'os.environ["CHAT_TOKEN"]' in PLANNER_LANE_PY and '"brain": "adk"' in PLANNER_LANE_PY
for _src in (PLANNER_PY, PLANNER_LANE_PY):          # the IDE demos need a docstring on every function a cell defines
    _defs = re.findall(r"\n *(?:async )?def \w+\(.*?\):\n *(\S+)", _src)
    assert _defs and all(d.startswith('"""') for d in _defs), _defs
REDEPLOY = 'make build deploy-services SERVICES=chat SCRIPTS=commands/lesson-12.8.sh PROJECT="$PROJECT" REGION="$REGION"'
assert "build: guard-project" in (KIT / "Makefile").read_text(encoding="utf-8")
assert "gcloud run deploy documind-chat" in (KIT / "commands" / "lesson-12.8.sh").read_text(encoding="utf-8")

# ------------------------------------------------------------------ the offline evals: their reports, then the page's read cell
def as_turns(text: str, ex: str) -> bool:
    """The eval's rewoo rows cost what the page's warm turns cost, to the fourth decimal: its waves' searches
    committed in the order written. A thread race can reorder them, which moves a passage's number from [5] to [10]
    and so an extract call's input by a token."""
    block_rw = text.split("== rewoo,", 1)[1]
    return all(re.search(rf"\n  {re.escape(r['id'])} +chained .* {TURNS[r['id']][ex]['rewoo']['inr']:.4f}  ", block_rw)
               for r in CHAINED)


def settled(job, args: list, ex: str) -> tuple[str, str]:
    """A background eval's output, run again (at most four more times) until its rewoo rows are the page's turns."""
    out, err = collect(job)
    for _ in range(4):
        if as_turns(out, ex):
            break
        out, err = run_py(args)
    assert as_turns(out, ex), ex
    return out, err


eval_out, eval_err = settled(EVAL_JOB, EVAL_ARGS, "flash")
quiet_err(eval_err)
OUT["eval_off"] = as_learner(eval_out)
lite_out, lite_err = settled(LITE_JOB, LITE_ARGS, "lite")
quiet_err(lite_err)
OUT["lite_off"] = as_learner(lite_out)
EO, LO = OUT["eval_off"], OUT["lite_off"]
assert EO.startswith("OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 3 rows, 3 arms, 1 run each")
assert "saved 9 runs to /home/you/plans-offline.jsonl" in EO and "saved 6 runs to /home/you/plans-lite-offline.jsonl" in LO
for p in ("loop", "plan_execute", "rewoo"):
    assert f"== {p}, thinking default (low), desk astar: 3 rows x 1 run" in EO
for p in ("plan_execute", "rewoo"):
    assert f"== {p}, thinking default (low), desk astar, executor {LITE}: 3 rows x 1 run" in LO
assert EO.count("first runs: correct    3/3 = 100.0%") == 2 and EO.count("first runs: correct    2/3 = 66.7%") == 1
assert "  the plans: replanned in 1 of 3 runs" in EO and "  the plans: refused before any tool ran in 0 of 3 runs, 3.0 waves a run" in EO
assert "no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08)" in LO
assert "  paired (correct), 3 rows: both 2, plan_execute only 1, rewoo only 0, neither 0" in LO   # "one row split them"
LITE_PAIRED = re.search(r"\n  rewoo - plan_execute = [-+\d.]+ points, 95% \[([-+]\d+\.\d), ([-+]\d+\.\d)\] \(Newcombe\)", LO).groups()
assert float(LITE_PAIRED[0]) < -100 * paired.MARGIN and float(LITE_PAIRED[1]) > 100 * paired.MARGIN   # across the margin, both sides
ARM_RE = r"== {p}, thinking default \(low\), desk astar{x}: 3 rows x 1 run.*?\n  a run: ([\d.]+) model calls, [\d.]+ searches, thinking \d+ and visible \d+ tokens, Rs ([\d.]+) for the model"
RUN = {}
for p in ("loop", "plan_execute", "rewoo"):
    m = re.search(ARM_RE.format(p=p, x=""), EO, re.S)
    RUN[(p, "flash")] = (m.group(1), m.group(2))
for p in ("plan_execute", "rewoo"):
    m = re.search(ARM_RE.format(p=p, x=f", executor {re.escape(LITE)}"), LO, re.S)
    RUN[(p, "lite")] = (m.group(1), m.group(2))
ROLE_RE = r"== {p}, thinking default \(low\), desk astar{x}: .*?\n  by role, a run: ([^\n]+)"
ROLE_LINE = {(p, ex): re.search(ROLE_RE.format(p=p, x=x), EO if ex == "flash" else LO, re.S).group(1)
             for p in ("plan_execute", "rewoo") for ex, x in (("flash", ""), ("lite", f", executor {re.escape(LITE)}"))}
SMALL = {(p, ex): re.search(rf"(?:act|extract) [\d.]+ calls, Rs ([\d.]+) \(", ROLE_LINE[(p, ex)]).group(1)
         for p in ("plan_execute", "rewoo") for ex in ("flash", "lite")}
for p in ("plan_execute", "rewoo"):
    assert f"({LITE})" in ROLE_LINE[(p, "lite")] and f"({LITE})" not in ROLE_LINE[(p, "flash")]
    assert float(SMALL[(p, "lite")]) < float(SMALL[(p, "flash")])

READ_PY = r'''import json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
SAVED = %s      # the files make agent-eval's SAVE= wrote
for name in SAVED:
    runs = [json.loads(line) for line in open(os.path.expanduser(name), encoding="utf-8") if line.strip()]
    print(f"{name}: {len(runs)} runs")
    for r in runs:
        arm, plan = r["arm"]["pattern"] + (" on " + r["arm"]["executor"] if r["arm"].get("executor") else ""), r.get("plan") or {}
        roles = "; ".join(f"{k} {v['calls']}, Rs {v['inr']:.2f}" for k, v in (r.get("roles") or {}).items())
        print(f"  {r['row']:<24} {arm:<35} {r['model_calls']:>2} calls, Rs {r['inr']:.2f}" + (f" | {roles}" if roles else ""))
        for e in plan.get("log") or ():
            if e["event"] == "replan":
                print(f"      replanned after: {e['why'][:100]}")
            if e["event"] == "stop":
                print(f"      stopped by its limits before its {e['before']} call")
        if plan.get("refused"):
            print(f"      refused before any tool ran: {plan['refused'][:100]}")
        if plan.get("waves"):
            print("      waves: " + " | ".join(", ".join(w) for w in plan["waves"]))'''
READ_OFF_PY = READ_PY % json.dumps(["~/plans-offline.jsonl", "~/plans-lite-offline.jsonl"])
READ_LANE_PY = READ_PY % json.dumps(["~/plans.jsonl", "~/plans_lite.jsonl"])
assert SAVED_OFF.endswith("/plans-offline.jsonl") and SAVED_LITE.endswith("/plans-lite-offline.jsonl")
read_out, err = run_py(["-"], stdin=READ_OFF_PY)          # ~ is the scratch home, where SAVE= wrote them
assert not err.strip(), err
OUT["read_off"] = as_learner(read_out)
RO = OUT["read_off"]
assert RO.startswith("~/plans-offline.jsonl: 9 runs\n") and "~/plans-lite-offline.jsonl: 6 runs\n" in RO, RO[:300]
assert RO.count("replanned after: Step 3 was refused: cap = 100 is not written in LV-07") == 2
assert RO.count("waves: #E1, #E2 | #E3, #E5, #E6 | #E4") == 2

# the rewoo turn cold, as a learner's first offline run: the same steps, waves, figures and calls; only the passage
# numbers (which search committed first) and the token counts that move with them may differ
cold_out, cold_err = collect(COLD_JOB)
STRUCT = re.compile(r"^(wave |  #E|       = |       refused|       failed|  \S.*never ran|model call \d+ \(|\d+ model calls|waves: |by role: )")


def shape(text: str) -> list:
    """The turn's steps, waves, results and calls, with passage numbers, tokens and rupees written out."""
    out = []
    for ln in text.splitlines():
        if STRUCT.match(ln):
            ln = re.sub(r"\[\d+\]", "[n]", ln)
            ln = re.sub(r"in [\d,]+, thinking [\d,]+, visible [\d,]+ tokens, Rs [\d.]+", "in N tokens, Rs N", ln)
            out.append(re.sub(r"Rs \d+\.\d{4}", "Rs N", ln))
    return out


assert shape(cold_out) == shape(OUT["rewoo_e3"]), (shape(cold_out), shape(OUT["rewoo_e3"]))
assert "failed:" not in cold_out
COLD_FIRST = [m.group(1) for m in re.finditer(r"\n         \[(\d+)\] hr_policy_2026\.md, (?:NP-03|LV-07)", cold_out)]
WARM_FIRST = [m.group(1) for m in re.finditer(r"\n         \[(\d+)\] hr_policy_2026\.md, (?:NP-03|LV-07)", OUT["rewoo_e3"])]
assert WARM_FIRST == ["1", "6"], WARM_FIRST


# ------------------------------------------------------------------ the Level 0 panel: each turn as cards
def call_of(c: dict) -> dict:
    """One recorded model call, as the panel's strip and tally read it: its rupees as the recorder keeps them, so the
    tally's sum is the turn's total."""
    return {"r": c.get("role") or "loop", "m": c["model"], "rs": c["inr"]}


def head(c: dict) -> str:
    """A call's line: its n, its role and model, its tokens and its rupees (the script's)."""
    role = c.get("role") or "loop"
    return (f"call {c['n']} · {role} · {c['model']} · reads {c['tokens_in']:,}, thinks {c['thinking_tokens']:,}, "
            f"writes {c['visible_tokens']:,} tokens · Rs {c['inr']:.4f}")


def lines(text) -> list:
    return [ln.rstrip() for ln in str(text or "").splitlines() if ln.strip()]


def tool_block(label: str, tool: dict) -> dict:
    """A tool call and what it returned, refused or failed, as agent_turn.py prints it."""
    failed = tool["status"] != "error" and (tool.get("result") or {}).get("error")
    res = ([f"failed: {' '.join(str(failed).split())[:300]}"] if failed else at._result(tool))
    res = [re.sub(r"^refused: refused: ", "refused: ", ln) for ln in res]    # the CLI's word, and check_args' own, once
    return {"l": label, "t": res, "x": "bad" if tool["status"] == "error" or failed else ""}


def loop_cards(turn: dict) -> list:
    """The loop's turn: one card a model call, the tool it asked for and what came back."""
    calls, cards = {c["n"]: c for c in turn["calls"]}, []
    for step in turn["trace"]:
        c = calls[step["call"]]
        blocks = [tool_block(f"calls {t['name']}({at._args(t['args'])}); the tool:", t) for t in step["tools"]]
        if not step["tools"]:
            blocks.append({"l": "writes the answer:", "t": lines(step["text"]), "x": ""})
        cards.append({"calls": [call_of(c)], "h": head(c), "b": blocks})
    return cards


def plan_cards(turn: dict) -> list:
    """plan_execute's or rewoo's turn, from its plan's log: the plan, each step or wave, a replan, the answer."""
    calls, cards = {c["n"]: c for c in turn["calls"]}, []
    for e in turn["plan"]["log"]:
        c = calls.get(e.get("call"))
        if e["event"] == "plan" and "refused" in e:                     # rewoo's plan, written once
            cards.append({"calls": [call_of(c)], "h": head(c), "b": [
                {"l": "writes every step at once, before any tool runs:", "x": "",
                 "t": [f"{s['id']} = {s['tool']}[{json.dumps(s['args'], ensure_ascii=False)}]" for s in e["steps"]]},
                {"l": "code checks the plan:", "x": "bad" if e["refused"] else "",
                 "t": [f"refused before any tool ran: {e['refused']}" if e["refused"] else
                       "nothing to refuse: every tool is the desk's, every placeholder names a step above it"]}]})
        elif e["event"] == "plan":
            cards.append({"calls": [call_of(c)], "h": head(c), "b": [
                {"l": "writes the plan, before any tool runs:", "x": "",
                 "t": [f"{i}. {s}" for i, s in enumerate(e["steps"], 1)] or ["no numbered step"]}]})
        elif e["event"] == "step":
            blocks = [{"l": f"step {e['n']}: {e['text']}", "t": [], "x": ""}]
            blocks += [tool_block(f"calls {t['name']}({at._args(t['args'])}); the tool:", t) for t in e.get("tools") or ()]
            if "tools" in e and not e["tools"]:
                blocks.append({"l": "no tool call; the executor wrote:", "t": [e.get("wrote") or "(nothing)"], "x": "bad"})
            if e.get("status") not in (None, "done"):
                blocks.append({"l": f"the step was {e['status']}: the steps not yet run go back to the planner, "
                                    f"{ap.MAX_REPLANS} replan a turn", "t": [], "x": "bad"})
            cards.append({"calls": [call_of(c)], "h": head(c), "b": blocks})
        elif e["event"] == "replan":
            cards.append({"calls": [call_of(c)], "h": head(c), "b": [
                {"l": "reads why the step failed:", "t": [e["why"]], "x": ""},
                {"l": "writes the plan for the work still to do:", "x": "",
                 "t": [f"{i}. {s}" for i, s in enumerate(e["steps"], 1)] or ["no numbered step"]}]})
        elif e["event"] == "wave":
            ex_calls, blocks = [], []
            for s in e["steps"]:
                if s["tool"] == ap.EXTRACT:
                    xc = calls.get(s.get("call"))
                    if xc:
                        ex_calls.append(call_of(xc))
                    blocks.append({"l": f"{s['id']} = extract({at._args(s['args'])}): " + (head(xc) if xc else "no call"),
                                   "t": [f"= {s['value']}, quoting \"{s['quote']}\"" if s.get("state") == "ok"
                                         else f"refused: {s.get('why')}"], "x": "" if s.get("state") == "ok" else "bad"})
                    continue
                filled = s["written"] != s["args"]
                label = (f"{s['id']} = {s['tool']}({at._args(s['written'])})"
                         + (f", run as ({at._args(s['args'])})" if filled else "") + "; the tool:")
                blocks.append(tool_block(label, {"name": s["tool"], "status": s.get("status"), "result": s.get("result")}))
            ids = [s["id"] for s in e["steps"]]
            what = (f"wave {e['n']} · code runs {', '.join(ids)}" + (" together" if len(ids) > 1 else "")
                    + (" · no model call" if not ex_calls else f" · {len(ex_calls)} extract call{'' if len(ex_calls) == 1 else 's'}"))
            cards.append({"calls": ex_calls, "h": what, "code": True, "b": blocks})
        elif e["event"] == "skip":
            cards[-1]["b"].append({"l": f"{e['id']} never runs: {e['why']}", "t": [], "x": "bad"})
        elif e["event"] == "solve":
            cards.append({"calls": [call_of(c)], "h": head(c), "b": [
                {"l": "writes the answer from the results, no tool:", "t": lines(turn["answer"]), "x": ""}]})
        elif e["event"] == "stop":
            cards.append({"calls": [], "h": "the turn's limits", "code": True,
                          "b": [{"l": f"stopped it before its {e['before']} call", "t": [], "x": "bad"}]})
    return cards


def summary(row: dict, turn: dict, pattern: str) -> dict:
    """The answer, the eval's verdict and the figure check, then calls and rupees by role."""
    s = score(row, turn)
    roles = ([[r, v["model"], v["calls"], f"{v['inr']:.4f}"] for r, v in turn["roles"].items()] if turn.get("roles")
             else [["loop", MODEL, turn["model_calls"], f"{turn['inr']:.4f}"]])
    plan = turn.get("plan") or {}
    note = (f"plans written {len(plan.get('plans') or ())}, replans {plan['replans']}" if "replans" in plan else
            f"waves {len(plan.get('waves') or ())}" if "waves" in plan else "no plan: it decided each call")
    return {"ans": turn["answer"], "ok": s["correct"], "prov": s["provenance"], "why": s["why"], "flag": flagged(turn),
            "calc": [f"{da.LABELS[c['calculator']]}: {c['formula']}" for c in turn["calculations"]],
            "roles": roles, "tot": [turn["model_calls"], f"{turn['inr']:.4f}"], "note": note}


def figures(row: dict) -> str:
    """A chained row's three expected figures, as the panel's list names it."""
    out = []
    for p in row["parts"]:
        v, unit = p["expected"], p["unit"]
        out.append(desk_calc.inr(v) if unit == "INR" else f"{desk_calc.num(v)} days" if unit == "days" else str(v))
    return ", ".join(out)


PANEL = {
    "order": ["loop", "plan_execute", "rewoo"],
    "rows": [{"id": r["id"], "label": f"{r['id']}: {figures(r)}" + ("; the question states a cap of 100" if r is STATED else "")}
             for r in (STATED, E3, ROWS["chained-exit-saturday"])],
    "how": {"loop": "The loop. One call a pass; it decides each next call after reading the last result. One model for every call.",
            "plan_execute": "Plan-and-execute. A plan first; an executor carries it out a step at a time; one replan after a "
                            "refusal; a solver answers.",
            "rewoo": "ReWOO, plan once. Every step written at once, with placeholders; code checks it and runs it in waves; "
                     "a worker reads figures; a solver answers. No replan."},
    "letter": {"loop": "L", "plan": "P", "act": "A", "extract": "E", "replan": "R", "solve": "S"},
    "traces": {},
}
for r in CHAINED:                           # the loop has one model for every call: its trace is kept once a row
    by = TURNS[r["id"]]
    PANEL["traces"][r["id"]] = {"loop": {"cards": loop_cards(by["loop"]), "sum": summary(r, by["loop"], "loop")},
                                **{ex: {p: {"cards": plan_cards(by[ex][p]), "sum": summary(r, by[ex][p], p)}
                                        for p in ("plan_execute", "rewoo")} for ex in EXECS}}
for _rid, _t in PANEL["traces"].items():         # each column's last tally is its answer's total, call for call
    for _tr in [_t["loop"]] + [_t[ex][p] for ex in EXECS for p in ("plan_execute", "rewoo")]:
        _calls = [k for c in _tr["cards"] for k in c["calls"]]
        assert (len(_calls), f"{sum(k['rs'] for k in _calls):.4f}") == (_tr["sum"]["tot"][0], _tr["sum"]["tot"][1]), _rid
_pc = PANEL["traces"][STATED["id"]]
assert [len(_pc["loop"]["cards"]), len(_pc["flash"]["plan_execute"]["cards"]), len(_pc["flash"]["rewoo"]["cards"])] == [7, 10, 5]
assert _pc["flash"]["plan_execute"]["sum"]["ok"] and not _pc["flash"]["rewoo"]["sum"]["ok"] and _pc["loop"]["sum"]["ok"]
JS = """<script>
(function(){
  'use strict';
  var D = __DATA__;
  var root = document.getElementById('pe'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var rowSel = $('pe-row'), exSel = $('pe-ex'), cols = $('pe-cols'), at = $('pe-at'), step = 1;
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function trace(p){ var t = D.traces[rowSel.value]; return p === 'loop' ? t.loop : t[exSel.value][p]; }
  function last(){ var m = 0; D.order.forEach(function(p){ m = Math.max(m, trace(p).cards.length + 1); }); return m; }
  function block(box, b){ var d = el('div', 'pe-l' + (b.x ? ' ' + b.x : '')); d.appendChild(el('b', '', b.l)); if (b.t && b.t.length) d.appendChild(el('pre', '', b.t.join('\\n'))); box.appendChild(d); }
  function card(c){
    var box = el('div', 'pe-c');
    box.appendChild(el('div', 'pe-h' + (c.code ? ' code' : ''), c.h));
    c.b.forEach(function(b){ block(box, b); });
    return box;
  }
  function strip(t, shown){
    var s = el('div', 'pe-strip'), n = 0;
    t.cards.forEach(function(c, i){ c.calls.forEach(function(k){ n++; var chip = el('span', 'pe-chip r-' + k.r + (i < shown ? ' on' : ''), D.letter[k.r]); chip.title = 'call ' + n + ': ' + k.r + ', ' + k.m + ', Rs ' + k.rs.toFixed(4); s.appendChild(chip); }); });
    return s;
  }
  function tally(t, shown){
    var n = 0, rs = 0;
    t.cards.slice(0, shown).forEach(function(c){ c.calls.forEach(function(k){ n++; rs += k.rs; }); });
    return el('p', 'pe-tally', 'so far: ' + n + ' call' + (n === 1 ? '' : 's') + ', Rs ' + rs.toFixed(4));
  }
  function answer(s){
    var box = el('div', 'pe-a' + (s.ok ? '' : ' bad'));
    box.appendChild(el('p', '', 'Answer: ' + s.ans));
    box.appendChild(el('p', '', s.calc.length ? 'Worked out in code: ' + s.calc.join('; ') : 'Worked out in code: nothing.'));
    box.appendChild(el('p', '', 'The eval: ' + (s.ok ? 'correct' : 'not correct') + ', ' + (s.prov ? 'with its provenance' : 'without its provenance') + (s.why ? ' (' + s.why + ')' : '') + '.'));
    box.appendChild(el('p', '', s.flag.length ? 'Figure check: nothing wrote ' + s.flag.join(', ') + '.' : 'Figure check: every figure has a source.'));
    s.roles.forEach(function(r){ box.appendChild(el('p', 'pe-sum', r[0] + ': ' + r[2] + ' call' + (r[2] === 1 ? '' : 's') + ', Rs ' + r[3] + ' (' + r[1] + ')')); });
    box.appendChild(el('p', 'pe-sum', s.tot[0] + ' calls, Rs ' + s.tot[1] + '; ' + s.note));
    return box;
  }
  function render(){
    var n = last(); step = Math.max(1, Math.min(step, n));
    cols.textContent = '';
    D.order.forEach(function(p){
      var t = trace(p), col = el('div', 'pe-col'), shown = Math.min(step, t.cards.length);
      col.appendChild(el('div', 'pe-name', p));
      col.appendChild(el('p', 'pe-how', D.how[p]));
      col.appendChild(strip(t, shown));
      col.appendChild(tally(t, shown));
      t.cards.slice(0, shown).forEach(function(c){ col.appendChild(card(c)); });
      if (step > t.cards.length) col.appendChild(answer(t.sum));
      cols.appendChild(col);
    });
    at.textContent = step < n ? 'card ' + step + ' of each turn' : 'every card, and the answers';
    $('pe-back').disabled = step <= 1; $('pe-next').disabled = step >= n;
  }
  D.rows.forEach(function(r){ var o = el('option', '', r.label); o.value = r.id; rowSel.appendChild(o); });
  rowSel.value = D.rows[0].id;
  rowSel.addEventListener('change', function(){ step = 1; render(); });
  exSel.addEventListener('change', function(){ render(); });
  $('pe-back').addEventListener('click', function(){ step--; render(); });
  $('pe-next').addEventListener('click', function(){ step++; render(); });
  $('pe-all').addEventListener('click', function(){ step = last(); render(); });
  render();
})();
</script>
""".replace("__DATA__", json.dumps(PANEL, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"))
assert "<div" not in JS and "font-size" not in JS


# ------------------------------------------------------------------ what the lane's runs cost, before thinking
def lane_estimate(turn: dict, pattern: str) -> tuple:
    """(rupees for input and visible output, rupees for each 1,000 thinking tokens a call, calls): the script's counts,
    plus the tool declarations Gemini receives with every call that binds the desk's tools (the loop's calls and
    plan_execute's act calls; the script counts none), each call at its own model's rates. Thinking is left out: only
    the lane knows it."""
    rs = per_k = 0.0
    for c in turn["calls"]:
        bound = pattern == "loop" or c.get("role") == "act"
        rs += prices.inr(prices.usd(c["model"], c["tokens_in"] + (DECL_TOKENS if bound else 0), c["visible_tokens"]))
        per_k += prices.inr(prices.usd(c["model"], 0, 1000))
    return rs, per_k, len(turn["calls"])


def stop_at(turn: dict, pattern: str) -> int:
    """The thinking tokens a call at which the turn's spend reaches Rs 5 before its last call, so the Meter stops it."""
    before = per_k = 0.0
    for c in turn["calls"][:-1]:
        bound = pattern == "loop" or c.get("role") == "act"
        before += prices.inr(prices.usd(c["model"], c["tokens_in"] + (DECL_TOKENS if bound else 0), c["visible_tokens"]))
        per_k += prices.inr(prices.usd(c["model"], 0, 1000))
    return int((limits.TURN_BUDGET_INR - before) * 1000 / per_k)


def total(items) -> tuple:
    rs = per_k = calls = 0
    for turn, pattern in items:
        a, b, n = lane_estimate(turn, pattern)
        rs, per_k, calls = rs + a, per_k + b, calls + n
    return rs, per_k, calls


RUNS = {
    "turn_plan_execute": [(PE_S, "plan_execute")],
    "turn_rewoo": [(RW_E3, "rewoo")],
    "turn_lite": [(TURNS[E3["id"]]["lite"]["plan_execute"], "plan_execute")],
    "eval_plans": [(TURNS[r["id"]]["loop"], "loop") for r in CHAINED]
                  + [(TURNS[r["id"]]["flash"][p], p) for p in ("plan_execute", "rewoo") for r in CHAINED],
    "eval_lite": [(TURNS[r["id"]]["lite"][p], p) for p in ("plan_execute", "rewoo") for r in CHAINED],
}
EST = {k: total(v) for k, v in RUNS.items()}
N_TURNS = {k: len(v) for k, v in RUNS.items()}
ALL_RS = sum(v[0] for v in EST.values())
ALL_K = sum(v[1] for v in EST.values())
ALL_CALLS = sum(v[2] for v in EST.values())
ALL_TURNS = sum(N_TURNS.values())
STOPS = {"loop": min(stop_at(TURNS[r["id"]]["loop"], "loop") for r in CHAINED),
         "plan_execute": min(stop_at(TURNS[r["id"]][ex]["plan_execute"], "plan_execute") for r in CHAINED for ex in EXECS),
         "rewoo": min(stop_at(TURNS[r["id"]][ex]["rewoo"], "rewoo") for r in CHAINED for ex in EXECS)}
STOP_MIN = min(STOPS.values())
RS_K_OUT = prices.inr(prices.usd(MODEL, 0, 1000))
RS_K_OUT_LITE = prices.inr(prices.usd(LITE, 0, 1000))


def money(x: float) -> str:
    return f"{x:,.2f}"


COST = {f"EST_{k.upper()}": money(v[0]) for k, v in EST.items()}
COST.update({f"K_{k.upper()}": money(v[1]) for k, v in EST.items()})
COST.update({f"N_{k.upper()}": str(v[2]) for k, v in EST.items()})
COST.update({"EST_ALL": money(ALL_RS), "K_ALL": money(ALL_K), "N_ALL_CALLS": str(ALL_CALLS), "N_ALL_TURNS": str(ALL_TURNS),
             "CAP_ALL": money(ALL_TURNS * limits.TURN_BUDGET_INR),
             "STOP_LOOP": str(STOPS["loop"]), "STOP_PE": str(STOPS["plan_execute"]), "STOP_RW": str(STOPS["rewoo"]),
             "STOP_MIN": str(STOP_MIN),
             # the thinking a call that keeps these runs within Rs 65 (the kit PR's estimate, Rs 45-65) and Rs 100 (its ceiling)
             "T100": str(int((100 - ALL_RS) * 1000 / ALL_K)), "T65": str(int((65 - ALL_RS) * 1000 / ALL_K))})

# ------------------------------------------------------------------ the author's runs: what a live lane printed
REC_NAMES = ("ui_chat", "turn_plan_execute", "turn_rewoo", "turn_lite", "eval_plans", "eval_lite", "replay", "plans_read",
             "adk_planner")
REC = {k: pb.recorded(LESSON, f"{k}.txt") for k in REC_NAMES}


# ------------------------------------------------------------------ the windows: what you run, and what it prints
def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


heredoc = lambda src: "python - <<'PY'\n" + src + "\nPY"       # noqa: E731
LANE = 'PROJECT="$PROJECT" REGION="$REGION"'
GREP_LOOP = "grep -E '" + LOOP_FILTER + "'"
GREP_TRIM = "grep -vE '" + TRIM + "'"
SED = "sed -i 's/^MAX_REPLANS = 1 /MAX_REPLANS = 0 /' commands/agent_patterns.py && git diff --stat"
CELLS = {
    "classes": ("run in the operator shell, in the kit (once, if lesson 10.1's setup line has not run: acme's stored rows get their classes)",
                'make doc-types PROJECT="$PROJECT" TENANT=acme SEED=manifest APPLY=1'),
    "loop_stated": ("run in the operator shell, in the kit (Rs 0: the loop on the stated-cap row, its calls only; the first run builds ~/graph-venv)",
                    f"make agent-turn OFFLINE=1 ROW={STATED['id']} 2>&1 | {GREP_LOOP}"),
    "pe_stated": ("run in the operator shell, in the kit (Rs 0: plan_execute on the same row)",
                  f"make agent-turn OFFLINE=1 PATTERN=plan_execute ROW={STATED['id']}"),
    "readers": ("run in the operator shell, in the kit (a Python cell; Rs 0, the standard library: the plan's readers, no model)",
                heredoc(CHECK_PY)),
    "rewoo_e3": ("run in the operator shell, in the kit (Rs 0: rewoo on the first chained row; RAG_TIMEOUT_S gives a cold wave room)",
                 f"RAG_TIMEOUT_S=90 make agent-turn OFFLINE=1 PATTERN=rewoo ROW={E3['id']}"),
    "change": ("run in the operator shell, in the kit (the Change-it: no replan, then the same turn)",
               SED + f"\nmake agent-turn OFFLINE=1 PATTERN=plan_execute ROW={STATED['id']} 2>&1 | {GREP_TRIM}"),
    "restore": ("run in the operator shell, in the kit (put the line back)",
                "git checkout -q -- commands/agent_patterns.py && git diff --stat && grep -c '^MAX_REPLANS = 1 ' commands/agent_patterns.py"),
    "check": ("run in the operator shell, in the kit (Rs 0, the standard library: every figure of the three rows recomputed)",
              "make agent-eval CHECK=1 SLICE=chained"),
    "eval_off": ("run in the operator shell, in the kit (Rs 0: 9 scripted turns, about a minute)",
                 'make agent-eval OFFLINE=1 PATTERNS=loop,plan_execute,rewoo SLICE=chained SAVE="$HOME/plans-offline.jsonl"'),
    "lite_off": ("run in the operator shell, in the kit (Rs 0: the two planning patterns with a flash-lite executor)",
                 f'make agent-eval OFFLINE=1 PATTERNS=plan_execute,rewoo SLICE=chained EXEC_MODEL={LITE} SAVE="$HOME/plans-lite-offline.jsonl"'),
    "read_off": ("run in the operator shell, in the kit (a Python cell; Rs 0: the saved runs read back)",
                 heredoc(READ_OFF_PY)),
    "turn_plan_execute": (f"run in the operator shell, in the kit (one live turn, about Rs {COST['EST_TURN_PLAN_EXECUTE']} before thinking)",
                          f"make agent-turn {LANE} PATTERN=plan_execute ROW={STATED['id']}"),
    "turn_rewoo": (f"run in the operator shell, in the kit (one live turn, about Rs {COST['EST_TURN_REWOO']} before thinking)",
                   f"make agent-turn {LANE} PATTERN=rewoo ROW={E3['id']}"),
    "turn_lite": (f"run in the operator shell, in the kit (one live turn, about Rs {COST['EST_TURN_LITE']} before thinking)",
                  f"make agent-turn {LANE} PATTERN=plan_execute ROW={E3['id']} EXEC_MODEL={LITE}"),
    "eval_plans": (f"run in the operator shell, in the kit (9 live turns, about Rs {COST['EST_EVAL_PLANS']} before thinking)",
                   f'make agent-eval {LANE} PATTERNS=loop,plan_execute,rewoo SLICE=chained SAVE="$HOME/plans.jsonl"'),
    "eval_lite": (f"run in the operator shell, in the kit (6 live turns, about Rs {COST['EST_EVAL_LITE']} before thinking)",
                  f'make agent-eval {LANE} PATTERNS=plan_execute,rewoo SLICE=chained EXEC_MODEL={LITE} SAVE="$HOME/plans_lite.jsonl"'),
    "replay": ("run in the operator shell, in the kit (Rs 0: the saved runs rescored, no model call)",
               'make agent-eval REPLAY="$HOME/plans.jsonl"'),
    "plans_read": ("run in the operator shell, in the kit (a Python cell; Rs 0: your lane's saved runs read back)",
                   heredoc(READ_LANE_PY)),
    "planner": ("run in the operator shell, in the kit (a Python cell in ~/graph-venv; Rs 0: the kit's ADK brain with "
                "ADK_PLANNER on, on a scripted model)",
                "~/graph-venv/bin/" + heredoc(PLANNER_PY)),
    "planner_lane": (f"run in the operator shell, in the kit (optional: a chat redeploy, then two ADK turns, the switch off "
                     f"and on; at most Rs {2 * limits.TURN_BUDGET_INR:g})",
                     REDEPLOY + '\nexport CHAT="https://documind-chat-$NUMBER.$REGION.run.app"\n'
                     + 'CHAT_TOKEN="$(tok "$CHAT")" ' + heredoc(PLANNER_LANE_PY)),
}
OUTS = {
    "loop_stated": ("(the kit's own output, filtered as the cell filters it; produced when this page was built)", OUT["loop_stated"]),
    "pe_stated": ("(the kit's own output, produced when this page was built; yours should match it)", OUT["pe_stated"]),
    "readers": ("(the kit's own functions, run when this page was built)", OUT["readers"]),
    "rewoo_e3": ("(the kit's own output; your passage numbers may differ, see below)", OUT["rewoo_e3"]),
    "change": ("(git's stat for the edit, then the kit's own output with no replan, trimmed as the cell trims it)", OUT["change"]),
    "restore": ("(git's stat prints nothing: the file is the kit's again)", OUT["restore"]),
    "check": ("(the kit's own output, produced when this page was built)", OUT["check"]),
    "eval_off": ("(stdout, produced when this page was built; one progress line a run goes to stderr)", OUT["eval_off"]),
    "lite_off": ("(stdout, produced when this page was built)", OUT["lite_off"]),
    "read_off": ("(the kit's own saved runs, read back when this page was built)", OUT["read_off"]),
    "ui_chat": ("(the author's lane: your words, figures, times and rupees are yours)", REC["ui_chat"]),
    "turn_plan_execute": ("(the author's lane: the plan is Gemini's own, so yours differs)", REC["turn_plan_execute"]),
    "turn_rewoo": ("(the author's lane)", REC["turn_rewoo"]),
    "turn_lite": ("(the author's lane)", REC["turn_lite"]),
    "eval_plans": ("(the author's lane, stdout: every figure in it is the lane's)", REC["eval_plans"]),
    "eval_lite": ("(the author's lane, stdout)", REC["eval_lite"]),
    "replay": ("(the author's lane's saved runs, rescored)", REC["replay"]),
    "plans_read": ("(the author's lane's saved runs, read back)", REC["plans_read"]),
    "planner": ("(the kit's own ADK brain, run when this page was built; yours should match it)", OUT["planner"]),
    "planner_lane": ("(the author's lane: the words, calls and rupees are Gemini's and the lane's, so yours differ)",
                     REC["adk_planner"]),
}
PY_CELL = re.compile(r"(?:#[^\n]*\n\s*)*python3?\s+-\s+<<['\"]?PY['\"]?\s*(?:#[^\n]*)?\n(.*?)\nPY\s*", re.S)  # the demo builder's
for _k in ("readers", "read_off", "plans_read"):
    assert PY_CELL.fullmatch(CELLS[_k][1]), _k                     # a native Python cell for tools/build_workshop_demos.py
    assert "\ndef " not in CELLS[_k][1]                            # no function: none to give a docstring
WIN = {f"CELL_{k.upper()}": bash_window(*v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})

# ------------------------------------------------------------------ the numbers the prose states
NEXT = MANIFEST["modules"]["10"]["lessons"]["10.3"]["name"]
PREV = MANIFEST["modules"]["10"]["lessons"]["10.1"]["name"]


def tok(n: int) -> str:
    return f"{n:,}"


def role(turn: dict, name: str) -> dict:
    return turn["roles"][name]


ROW_TABLE = []
for r in CHAINED:
    parts = []
    for p in r["parts"]:
        c = p["calcs"][0]
        args = ", ".join(f"{k}={v}" for k, v in c["args"].items())
        v, unit = p["expected"], p["unit"]
        fig = desk_calc.inr(v) if unit == "INR" else f"{desk_calc.num(v)} days" if unit == "days" else str(v)
        stated = f"; the question states {', '.join(f'{k} {v}' for k, v in p['stated'].items())}" if p.get("stated") else ""
        parts.append(f"<code>{c['calculator']}({html.escape(args)})</code> = {html.escape(fig)}, {html.escape(p['clause'])}{stated}")
    ROW_TABLE.append(f'<tr><td><code>{r["id"]}</code></td><td data-label="The three figures, each a search and its calculator">'
                     + "<br>".join(parts) + "</td></tr>")
PE_SOLVE = next(c for c in PE_S["calls"] if c["role"] == "solve")
LOOP_LAST = LOOP_S["calls"][-1]
PE_ACT_IN = [c["tokens_in"] for c in PE_S["calls"] if c["role"] == "act"]
STATS = {
    "MODEL": MODEL, "LITE": LITE, "RATE_IN": f"{RATE_IN:.2f}", "RATE_OUT": f"{RATE_OUT:.2f}", "LITE_IN": f"{LITE_IN:.2f}",
    "LITE_OUT": f"{LITE_OUT:.2f}", "USD_INR": str(prices.USD_INR), "RS_K_OUT": f"{RS_K_OUT:.4f}",
    "RS_K_OUT_LITE": f"{RS_K_OUT_LITE:.4f}", "MAX_CALLS": str(limits.MAX_MODEL_CALLS),
    "BUDGET": f"{limits.TURN_BUDGET_INR:g}", "DEADLINE": f"{limits.TURN_DEADLINE_S:g}", "DEFAULT_LEVEL": da.THINKING_LEVEL,
    "N_TOOLS": str(N_TOOLS), "N_CALCS": str(len(desk_calc.CALCULATORS)), "N_TASKS": str(len(TASKS)),
    "N_CHAINED": str(len(CHAINED)), "ROW_TABLE": "\n".join(ROW_TABLE), "DECL_TOKENS": tok(DECL_TOKENS),
    "STATED_ID": STATED["id"], "E3_ID": E3["id"], "QUESTION": html.escape(STATED["question"]),
    "REFUSAL": html.escape(REFUSAL), "MAX_REPLANS": str(ap.MAX_REPLANS), "EXEC_MODELS": ", ".join(f"<code>{m}</code>" for m in ap.EXEC_MODELS),
    "LOOP_CALLS": str(LOOP_S["model_calls"]), "LOOP_RS": f"{LOOP_S['inr']:.4f}", "LOOP_IN": tok(LOOP_S["tokens_in"]),
    "LOOP_LAST_IN": tok(LOOP_LAST["tokens_in"]),
    "PE_CALLS": str(PE_S["model_calls"]), "PE_RS": f"{PE_S['inr']:.4f}", "PE_IN": tok(PE_S["tokens_in"]),
    "PE_ACT_MAX": tok(max(PE_ACT_IN)), "PE_ACT_MIN": tok(min(PE_ACT_IN)), "PE_SOLVE_IN": tok(PE_SOLVE["tokens_in"]),
    "PE_SOLVE_RS": f"{PE_SOLVE['inr']:.4f}",
    "PE_PLAN_RS": f"{role(PE_S, 'plan')['inr']:.4f}", "PE_ACT_RS": f"{role(PE_S, 'act')['inr']:.4f}",
    "PE_ACT_N": str(role(PE_S, "act")["calls"]), "PE_REPLAN_RS": f"{role(PE_S, 'replan')['inr']:.4f}",
    "PE_LITE_RS": f"{PE_SL['inr']:.4f}", "PE_LITE_ACT_RS": f"{role(PE_SL, 'act')['inr']:.4f}",
    "RW_CALLS": str(RW_S["model_calls"]), "RW_RS": f"{RW_S['inr']:.4f}", "RW_LITE_RS": f"{RW_SL['inr']:.4f}",
    "RW_E3_CALLS": str(RW_E3["model_calls"]), "RW_E3_RS": f"{RW_E3['inr']:.4f}",
    "RW_E3_EXTRACT_RS": f"{role(RW_E3, 'extract')['inr']:.4f}",
    "NR_CALLS": str(NR_CALLS), "NR_RS": NR_RS,
    "RUN_LOOP_CALLS": RUN[("loop", "flash")][0], "RUN_LOOP_RS": RUN[("loop", "flash")][1],
    "RUN_PE_CALLS": RUN[("plan_execute", "flash")][0], "RUN_PE_RS": RUN[("plan_execute", "flash")][1],
    "RUN_RW_CALLS": RUN[("rewoo", "flash")][0], "RUN_RW_RS": RUN[("rewoo", "flash")][1],
    "RUN_PE_LITE_RS": RUN[("plan_execute", "lite")][1], "RUN_RW_LITE_RS": RUN[("rewoo", "lite")][1],
    "SMALL_PE": SMALL[("plan_execute", "flash")], "SMALL_PE_LITE": SMALL[("plan_execute", "lite")],
    "SMALL_RW": SMALL[("rewoo", "flash")], "SMALL_RW_LITE": SMALL[("rewoo", "lite")],
    "LV07_SENT": html.escape(LV07_SENT), "SCRIPT_TH": str(ap.SCRIPTED_THINKING[da.THINKING_LEVEL]),
    "RAG_BUDGET": str(RAG_BUDGET), "LITE_PAIRED_LO": LITE_PAIRED[0], "LITE_PAIRED_HI": LITE_PAIRED[1],
    "MARGIN": f"{100 * paired.MARGIN:g}", "NEXT_TITLE": html.escape(NEXT), "PREV_TITLE": html.escape(PREV), **COST,
    "ADK_VER": ADK_VER, "PR_TOKENS": tok(PR_TOKENS), "PR_RS": f"{PR_RS:.2f}", "PL_CAP": f"{2 * limits.TURN_BUDGET_INR:g}",
}
if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(json.dumps({k: v for k, v in STATS.items() if k not in ("ROW_TABLE",)}, indent=1))
    print("cold first:", COLD_FIRST, "| panel bytes:", len(JS))
    sys.exit(0)                                    # remove_scratch() runs at exit


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
remove_scratch()

# the run list's prices, from the same figures: a stale line is named here, not silently kept
run_list = (pb.lesson_dir(LESSON) / "RUN_LIST.md").read_text(encoding="utf-8")
for k in [k for k in COST if k.startswith(("EST_", "K_", "CAP_"))]:
    if f"Rs {COST[k]}" not in run_list:
        print(f"note: RUN_LIST.md does not state {k} = Rs {COST[k]}")
for k in ("T100", "T65", "STOP_LOOP", "STOP_PE", "STOP_RW"):
    if f"about {COST[k]} thinking tokens" not in run_list:
        print(f"note: RUN_LIST.md does not state {k} = about {COST[k]} thinking tokens a call")
if f"at most Rs {STATS['PL_CAP']} (Rs {STATS['BUDGET']} a turn)" not in run_list:     # run 9: two ADK turns at the limit
    print(f"note: RUN_LIST.md does not state run 9's cap, at most Rs {STATS['PL_CAP']} (Rs {STATS['BUDGET']} a turn)")
print(f"kit: {len(CHAINED)} chained rows x 3 patterns offline | the stated-cap turn: loop {LOOP_S['model_calls']} calls Rs "
      f"{LOOP_S['inr']:.4f}, plan_execute {PE_S['model_calls']} Rs {PE_S['inr']:.4f} (lite {PE_SL['inr']:.4f}), rewoo "
      f"{RW_S['model_calls']} Rs {RW_S['inr']:.4f} (lite {RW_SL['inr']:.4f}) (the script's) | lane before thinking: all Rs "
      f"{COST['EST_ALL']} over {ALL_CALLS} calls in {ALL_TURNS} turns, Rs {COST['K_ALL']} for each 1,000 thinking tokens a "
      f"call | a turn reaches Rs 5 at about {STOP_MIN} thinking tokens a call | declarations ~{DECL_TOKENS} tokens a call")
