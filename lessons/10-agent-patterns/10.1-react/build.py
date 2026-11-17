"""Build lesson 10.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Choose where the agent reasons. The agent bench (commands/agent_patterns.py) runs one question through three patterns
on the Desk agent's toolset (arm A*: one retrieve over every class the person may read, and the seven calculators of
shared/desk_calc.py): loop, the Desk agent's own create_agent loop, whose model thinks natively between function
calls; react_text, prompted ReAct, whose model writes Thought and Action as text and stops at "Observation:", while
code parses the Action, runs it through ToolNode and writes the Observation; plan_first, the loop with an instruction
to write a plan first, which nothing executes. The recorder keeps every model call's thinking and visible tokens and
its rupees; evals/agent_eval.py scores the task set's 11 calculator rows (SLICE=calc) for each pattern.

Offline, at build time, with the chat image's pins (build with the chat venv's python), no credential and no network:
agent_turn.py --offline for the three patterns and the four thinking levels; the Change-it, the scripted text model
inventing an Observation past its Action, first with the parser's cut and then with the line marked THE CUT deleted
(agent_patterns.py loaded without it, in memory, as the kit's own test does: the file on disk is never touched) and
git's own diff --stat for that deletion in a scratch repository; agent_eval.py --check and --offline on the calculator
slice, saved, then split and paired with --compare by the page's own cell. In process: every calculator row through
every pattern, for the Level 0 panel, whose traces also price the lane's runs for RUN_LIST.md. The live cells that
cannot run here (the /v1/passages call, the log read) are run against stand-ins to prove they work, and their outputs
come from the author's lane: pb.recorded() reads them from data/ (RUN_LIST.md says how each is recorded).

    python pagekit/build.py 10.1        (the chat venv; a few minutes, most of them the offline eval and the panel's turns)
"""
import html
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "10.1"
title = ("<title>Lesson 10.1 Choose where the agent reasons: observe-think-act and ReAct - native thinking, prompted "
         "ReAct and a plan first on the same calculator rows | Netsetos</title>\n")
warnings.filterwarnings("ignore")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the Level 0 panel: one question through the three patterns, one model call at a time */
.ota-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:8px 12px;margin:4px 0 10px;}
.ota-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.ota-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;width:100%;}
.ota-in select:disabled{color:#94a3b8;background:#f1f5f9;}
.ota-nav{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 10px;}
.ota-nav button{font:inherit;font-size:var(--small-size);padding:6px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);cursor:pointer;min-height:max(40px,var(--touch));}
.ota-nav button:active{transform:scale(.97);}
.ota-nav button:disabled{color:#94a3b8;cursor:default;}
.ota-at{font-family:var(--mono);font-size:var(--kicker-size);color:var(--slate);letter-spacing:.5px;}
.ota-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:10px;align-items:start;}
.ota-col{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;min-width:0;overflow-wrap:anywhere;}
.ota-name{font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--teal);}
.ota-how{font-size:12px;line-height:1.45;color:var(--slate);margin:2px 0 6px;}
.ota-c{border-top:1px dashed var(--border);padding:6px 0 4px;font-size:12.5px;line-height:1.5;}
.ota-h{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--teal-dark);}
.ota-t{margin:2px 0;color:var(--slate);font-size:12px;}
.ota-l{margin:3px 0;}
.ota-l b{display:block;font-size:11.5px;color:var(--navy);}
.ota-l pre{font-family:var(--mono);font-size:11.5px;line-height:1.45;white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f5f9;border-radius:6px;padding:4px 6px;margin:2px 0;color:var(--slate);}
.ota-l.cut pre{text-decoration:line-through;color:#9a3412;background:#fff7ed;}
.ota-l.bad pre{color:#991b1b;background:#fef2f2;}
.ota-a{border-top:2px solid var(--teal);margin-top:4px;padding:6px 0 2px;font-size:12.5px;line-height:1.5;}
.ota-a.bad{border-top-color:#c2410c;}
.ota-a p{margin:2px 0;}
.ota-sum{font-family:var(--mono);font-size:11px;color:var(--navy);margin:6px 0 0;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim kit excerpts
AP, AT, AE, DC, DA, MK = ("commands/agent_patterns.py", "commands/agent_turn.py", "evals/agent_eval.py",
                          "shared/desk_calc.py", "services/chat/desk_agent.py", "mk/agents.mk")
EXCERPTS = {
    "loop": ("commands/agent_patterns.py - _loop(): the Desk agent's loop, with the recorder inside the turn's limits",
             block(AP, "def _loop(", end="# plan_first (lesson 10.1)")),
    "record": ("commands/agent_patterns.py - the recorder: THINKING sent with every call, and each call's tokens and rupees",
               block(AP, "        def _send(self, request):", n=4) + "\n...\n" + block(AP, "def call_record(", end="def recorder(")),
    "rule": ("services/chat/desk_agent.py - system_prompt(): the rule every pattern's prompt carries",
             block(DA, '"- Work every figure out with a calculator, never yourself.', n=3)),
    "protocol": ("commands/agent_patterns.py - REACT_PROTOCOL: the text protocol, after the desk's prompt and before its tools",
                 block(AP, "# react_text (lesson 10.1): the text protocol", end="_LABEL = ")),
    "read_step": ("commands/agent_patterns.py - read_step(): the parser, and the one line marked THE CUT",
                  block(AP, "def read_step(", end="def transcript(")),
    "think": ("commands/agent_patterns.py - _react_text(): the call that sends the stop sequence, and the think node",
              block(AP, "    def call(request):", end="    def route(state):")),
    "plan_first": ("commands/agent_patterns.py - PLAN_FIRST and _plan_first(): a plan written, never run",
                   block(AP, "# plan_first (lesson 10.1)", end="# react_text (lesson 10.1)")),
    "invent": ("commands/agent_patterns.py - the scripted text model: the stop it honours, and the Observation it invents",
               block(AP, "            if self.honours_stop:", n=3) + "\n...\n" + block(AP, "    if invents and task and", n=6)),
    "unsupported": ("shared/desk_calc.py - unsupported(): the figure check",
                    block(DC, "def unsupported(", end=" the selftest")),
    "score": ("evals/agent_eval.py - score(): correct and provenance for one run of one row",
              block(AE, "def score(", end="def backed(")),
    "mk": ("mk/agents.mk - make agent-turn and make agent-eval",
           block(MK, "agent-turn: $(if $(OFFLINE),,guard-project)", n=2) + "\n\n"
           + block(MK, "agent-eval: $(if $(or $(OFFLINE),$(CHECK),$(REPLAY),$(COMPARE)),,guard-project)", n=2)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["loop"].startswith("def _loop(") and "middleware=[da.DeskTurnLimits(), recorder, da._guard()]" in E["loop"]
assert E["loop"].rstrip().endswith("return [limits.stop_message()]")
assert '"thinking_level": thinking' in E["record"] and 'thinking = int((u.get("output_token_details") or {}).get("reasoning") or 0)' in E["record"]
assert '"visible_tokens": max(tokens_out - thinking, 0)' in E["record"] and "prices.inr(prices.usd(model, tokens_in, tokens_out, cached))" in E["record"]
assert E["rule"].rstrip().endswith('"a number you need is in neither, say which one is missing.\\n"')
assert E["protocol"].rstrip().endswith('"The tools, one JSON declaration a line (its name, what it does, its parameters):")')
cut_lines = [ln for ln in E["read_step"].splitlines() if "THE CUT" in ln]
assert len(cut_lines) == 1 and cut_lines[0].strip().startswith("text = text.split(STOP, 1)[0]"), cut_lines
assert "stop=[STOP]" in E["think"] and "turn_limits.wrap_model_call(request, lambda r: recorder.wrap_model_call(r, call))" in E["think"]
assert E["plan_first"].rstrip().endswith('prompt=PLAN_FIRST + "\\n\\n" + _da().system_prompt(desk))')
assert E["invent"].rstrip().endswith("return reply") and "text = text[:cut]" in E["invent"]
assert E["unsupported"].rstrip().endswith("+ [d.isoformat() for d in sorted(dates_in(answer) - days)])")
assert E["score"].rstrip().endswith('return {"correct": bool(correct), "provenance": bool(provenance), "unsupported": flagged, "why": "; ".join(why)}')
assert "bash commands/agent-turn.sh" in E["mk"] and "--compare $(COMPARE)" in E["mk"]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit, imported (the chat image's pins)
sys.path[:0] = [str(KIT / "commands"), str(KIT / "services" / "chat"), str(KIT), str(KIT / "evals")]
import agent_patterns as ap  # noqa: E402
import agent_turn as at  # noqa: E402
import limits  # noqa: E402
import paired  # noqa: E402
from shared import desk_calc, desk_law, prices  # noqa: E402

prices.PROFILE = "gcp"       # list prices, whatever DOCUMIND_PROFILE the build's own shell carries: the page prices a lane
da = ap._da()
MODEL = da.AGENT_MODEL
RATE_IN, RATE_OUT = prices.PRICES[MODEL]
assert (MODEL, RATE_IN, RATE_OUT, prices.USD_INR) == ("gemini-3.6-flash", 1.50, 7.50, 85)
OWN = ("loop", "react_text", "plan_first")       # this page's patterns; lessons 10.2 and 10.3 add theirs to the registry
assert all(p in ap.PATTERNS for p in OWN) and ap.STOP == "Observation:"
assert ap.THINKING_LEVELS == ("minimal", "low", "medium", "high") and da.THINKING_LEVEL == "low"
assert (limits.MAX_MODEL_CALLS, limits.TURN_BUDGET_INR, limits.TURN_DEADLINE_S) == (12, 5.0, 100.0)
assert ap.classes_for("astar") == ["policy", "statute", "guidance"]
SEARCH_CLASSES = sorted(ap.classes_for("astar"))            # documind_tools sends the doc_type list sorted
TASKS = ap.tasks()
ROWS = {r["id"]: r for r in TASKS}
KINDS = {k: sum(r["kind"] == k for r in TASKS) for k in ("calc", "lookup", "trap", "refuse", "chained")}
CALC = [r for r in TASKS if r["kind"] == "calc"]
assert {k: n for k, n in KINDS.items() if k != "chained"} == {"calc": 11, "lookup": 5, "trap": 1, "refuse": 1}, KINDS
assert len(TASKS) == 18 + KINDS["chained"] and KINDS["chained"] in (0, 3), KINDS   # lesson 10.2's kit adds 3 chained rows
CHAINED = f"{KINDS['chained']} chained rows (lesson 10.2's), " if KINDS["chained"] else ""
ae_spec = importlib.util.spec_from_file_location("agent_eval_lesson_101", KIT / AE)
ae = importlib.util.module_from_spec(ae_spec)
ae_spec.loader.exec_module(ae)
assert [r["id"] for r in ae.select(TASKS, "calc")] == [r["id"] for r in CALC]      # SLICE=calc is the 11 calc rows
assert ae.select(TASKS, "calculator") == []                                          # a slice the task set does not have
GRAT = ROWS[at.DEFAULT_ROW]
assert GRAT["id"] == "calc-gratuity-7y8m" and GRAT["expected"] == 240000
at_src = (KIT / AT).read_text(encoding="utf-8")
INVENT = re.search(r'"--invent", nargs="\?", const="([^"]+)"', at_src).group(1)
assert INVENT == "Rs 2,50,000"
DECL = "\n".join(json.dumps(d, ensure_ascii=False) for d in ap.declarations("astar"))
DECL_TOKENS = math.ceil(len(DECL) / ap.CHARS_PER_TOKEN)                # the loop's tools, as Gemini receives them
PROTOCOL_TOKENS = math.ceil(len(ap.REACT_PROTOCOL) / ap.CHARS_PER_TOKEN)
N_TOOLS = len(da.TOOLSETS["astar"])
assert N_TOOLS == 8 and [t.name for t in da.TOOLSETS["astar"]][0] == "retrieve"
RS_K_IN = prices.inr(prices.usd(MODEL, 1000, 0))
RS_K_OUT = prices.inr(prices.usd(MODEL, 0, 1000))
mk_src = (KIT / MK).read_text(encoding="utf-8")
assert "\nagent-turn: $(if $(OFFLINE),,guard-project)\n" in mk_src and "Q=\"$(Q)\"" in mk_src
assert ' INVENT="$(INVENT)" ' in mk_src                              # make agent-turn passes INVENT=1 on as --invent
sh_src = (KIT / "commands" / "agent-turn.sh").read_text(encoding="utf-8")
assert 'if [ -n "${INVENT:-}" ]; then ARGS+=(--invent); [ "$INVENT" = 1 ] || ARGS+=("$INVENT"); fi' in sh_src
assert 'if [ "$#" -gt 0 ]; then\n  exec "$VENV/bin/python" "$@"\nfi' in sh_src
assert 'REGION="${REGION:-us-central1}"' in sh_src            # the page passes REGION: the lane is asia-south1
chat_tools = (KIT / "services" / "chat" / "tools.py").read_text(encoding="utf-8")
assert "TOOLS = [retrieve, calculate_processing_cost]" in chat_tools          # Level 1: the chat brains hold no calculator
brains_src = (KIT / "services" / "chat" / "brains.py").read_text(encoding="utf-8")
assert "root = LlmAgent(name=\"documind_adk\", model=model, instruction=SYSTEM," in brains_src
ADK_BRAIN = brains_src[brains_src.index("class AdkBrain:"):brains_src.index("class DirectBrain:")]
assert "planner" not in ADK_BRAIN[ADK_BRAIN.index("root = LlmAgent("):ADK_BRAIN.index("if peer.PEER_URL:")]   # built with none
assert 'ADK_PLANNER = os.environ.get("ADK_PLANNER", "")' in brains_src         # lesson 10.2's switch, off unless set
assert re.findall(r'ADK_PLANNER == "(\w+)"', brains_src) == ["plan_react"] and "BuiltInPlanner" not in brains_src
assert 'location="global", thinking_level="low",' in (KIT / "shared" / "profile.py").read_text(encoding="utf-8")
assert '"desk"]] = None' in (KIT / "services" / "rag-api" / "schemas.py").read_text(encoding="utf-8")
assert 'brain="desk", passages=True)' in (KIT / DA).read_text(encoding="utf-8")
assert '"brain": getattr(req, "brain", None) or "ui"}' in (KIT / "services" / "rag-api" / "main.py").read_text(encoding="utf-8")
da_src = (KIT / DA).read_text(encoding="utf-8")
assert "no doc_type, no class: not this search's" in da_src                  # why the setup line classes the rows
assert "include_thoughts" not in da_src                                       # the model is asked for no thoughts, a count only
assert paired.MARGIN == 0.03 and paired.MARGIN_REGISTERED == "2026-10-08"
for _p in ("plan_execute", "rewoo"):              # step 10 names them as lesson 10.2's: registered, or planned for it
    assert _p in ap.PATTERNS or ap.PLANNED.get(_p) == "10.2", _p

# ADK's two planners, in the chat image's pin (google-adk 2.8.0): the library's own forms of two of the three patterns,
# read from the installed files (importing ADK is not needed to read what it says)
import importlib.metadata as md  # noqa: E402
assert md.version("google-adk") == "2.8.0" and md.version("langchain-google-genai") == "4.4.0"
ADK = md.distribution("google-adk")
BUILTIN = Path(ADK.locate_file("google/adk/planners/built_in_planner.py")).read_text(encoding="utf-8")
PLANREACT = Path(ADK.locate_file("google/adk/planners/plan_re_act_planner.py")).read_text(encoding="utf-8")
assert "class BuiltInPlanner(BasePlanner):" in BUILTIN and "llm_request.config.thinking_config = self.thinking_config" in BUILTIN
for tag in ("PLANNING_TAG = '/*PLANNING*/'", "REASONING_TAG = '/*REASONING*/'", "ACTION_TAG = '/*ACTION*/'",
            "FINAL_ANSWER_TAG = '/*FINAL_ANSWER*/'", "REPLANNING_TAG = '/*REPLANNING*/'"):
    assert tag in PLANREACT, tag
assert "class PlanReActPlanner(BasePlanner):" in PLANREACT
assert "# Stop at the first (group of) function calls." in PLANREACT         # its tool calls stay native function calls
assert "self._mark_as_thought(reasoning_part)" in PLANREACT                  # its written reasoning is marked as thought


# ------------------------------------------------------------------ the calculators, as the bench's desk holds them
def sources(spec: dict) -> str:
    """Where a calculator's arguments may come from, in check_args' terms."""
    out = []
    for arg, src in spec["numbers"].items():
        out.append(f"{arg}: the question" if src == desk_calc.MESSAGE else f"{arg}: {' or '.join(src)} of a handbook passage")
    out += [f"{arg}: the question" for arg in spec["dates"]]
    out += [f"{flag}: only when the question says so" for flag in spec.get("flags", {})]
    return "; ".join(out) or "event: a word the calculator checks"


CALC_ROWS = []
for name, spec in desk_calc.CALCULATORS.items():
    need = desk_law.STATUTES[spec["needs"]]["title"] if spec["needs"] else ""
    CALC_ROWS.append(f'<tr><td><code>{name}</code></td><td data-label="Works out">{html.escape(da.LABELS[name])}'
                     f'{" (" + html.escape(need) + ", once a passage of it is read)" if need else ""}</td>'
                     f'<td data-label="Its arguments, and where each must be written">{html.escape(sources(spec))}</td></tr>')
assert len(CALC_ROWS) == 7 and len(desk_calc.for_desk("handbook")) == 4 and len(desk_calc.for_desk("statute")) == 3

# ------------------------------------------------------------------ the offline runs: the kit's own output, no network
SCRATCH = Path(tempfile.mkdtemp(prefix="lesson101_"))
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


def quiet_err(err: str) -> None:
    """Nothing but the eval's own progress lines may reach stderr."""
    bad = [ln for ln in err.splitlines() if ln.strip() and not re.match(r"  \[\d+/\d+\] \S+ run \d+: ", ln)]
    assert not bad, bad[:5]


# the long one first, in the background: the offline eval on the calculator slice, saved
SAVED_OFF = HOME_P + "/bench-101-offline.jsonl"
EVAL_ARGS = ["evals/agent_eval.py", "--offline", "--patterns", "loop,react_text,plan_first", "--slice", "calc",
             "--save", SAVED_OFF]
eval_out, eval_err = open(SCRATCH / "eval.out", "w+", encoding="utf-8"), open(SCRATCH / "eval.err", "w+", encoding="utf-8")
eval_proc = subprocess.Popen([sys.executable] + EVAL_ARGS, cwd=str(KIT), stdout=eval_out, stderr=eval_err, env=QUIET)

OUT = {}
OUT["turn_loop"], err = run_py([AT, "--offline"])
assert not err.strip(), err
OUT["turn_react_off"], err = run_py([AT, "--offline", "--pattern", "react_text"])
assert not err.strip(), err
OUT["turn_plan_off"], err = run_py([AT, "--offline", "--pattern", "plan_first"])
assert not err.strip(), err
LEVEL_LINE = re.compile(r"^(  thinking:|model call|tokens:|figure check|the turn failed|make: )")
levels = []
for t in ap.THINKING_LEVELS:
    o, err = run_py([AT, "--offline", "--thinking", t])
    assert not err.strip(), err
    levels += [ln for ln in o.splitlines() if LEVEL_LINE.match(ln)]
OUT["levels_off"] = "\n".join(levels) + "\n"
assert OUT["levels_off"].count("figure check: every figure") == 4 and "the turn failed" not in OUT["levels_off"]
LEVEL_RS = re.findall(r"^tokens: in ([\d,]+), thinking ([\d,]+), visible [\d,]+; Rs ([\d.]+) for the model calls", OUT["levels_off"], re.M)
assert len(LEVEL_RS) == 4 and len({tin for tin, _, _ in LEVEL_RS}) == 1                # the input does not move with the level
assert [th for _, th, _ in LEVEL_RS] == [f"{3 * v:,}" for v in ap.SCRIPTED_THINKING.values()]
INVENT_ARGS = ["--offline", "--pattern", "react_text", "--desk", "astar", "--tenant", "acme", "--invent"]   # as make's INVENT=1
OUT["invent"], err = run_py([AT] + INVENT_ARGS)
assert not err.strip(), err

# the Change-it: the same command with the line marked THE CUT deleted, as the learner's sed deletes it
NOCUT_PY = """import importlib.util, sys
from pathlib import Path
sys.path[:0] = ["commands", "services/chat", "."]
path = Path("commands/agent_patterns.py").resolve()
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
kept = [line for line in lines if "THE CUT" not in line]
assert len(lines) - len(kept) == 1
mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("agent_patterns", loader=None, origin=str(path)))
mod.__file__ = str(path)
sys.modules["agent_patterns"] = mod
exec(compile("".join(kept), str(path), "exec"), mod.__dict__)
import agent_turn
sys.exit(agent_turn.main(__ARGS__))
""".replace("__ARGS__", repr(INVENT_ARGS))
OUT["nocut"], err = run_py(["-"], stdin=NOCUT_PY)
assert not err.strip(), err

# git's own words for the deletion and the restore, in a scratch repository holding the same file
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
with open(REPO / AP, "w", encoding="utf-8", newline="") as f:          # sed -i '/THE CUT/d'
    f.writelines(ln for ln in src_lines if "THE CUT" not in ln)
STAT = git("diff", "--stat")
assert re.fullmatch(r" commands/agent_patterns\.py \| 1 -\n 1 file changed, 1 deletion\(-\)\n", STAT), STAT
RESTORED = git("checkout", "-q", "--", AP) + git("diff", "--stat")
assert RESTORED == "", RESTORED
assert (REPO / AP).read_text(encoding="utf-8") == (KIT / AP).read_text(encoding="utf-8")
CUT_COUNT = sum("THE CUT" in ln for ln in (REPO / AP).read_text(encoding="utf-8").splitlines())   # grep -c "THE CUT"
assert CUT_COUNT == 1
OUT["cut"] = STAT + OUT["nocut"]
OUT["restore"] = RESTORED + f"{CUT_COUNT}\n"

OUT["check"], err = run_py([AE, "--check", "--slice", "calc"])
assert not err.strip(), err
assert OUT["check"].rstrip().endswith("every question let through by the hard gate") and OUT["check"].count("\nok    ") == 10

# what each run printed, checked against what the page says about it
T, R, P, I, N = OUT["turn_loop"], OUT["turn_react_off"], OUT["turn_plan_off"], OUT["invent"], OUT["nocut"]
for text in (T, R, P, I):
    assert "3 model calls (12 at most), 1 search, 1 calculation, 0 refused or failed tool calls" in text, text[-600:]
    assert "  Gratuity, an estimate: Rs 2,40,000 [2]." in text and "(desk_calc.unsupported: none)" in text
assert "0 format errors; stopped by nothing" in R and "react_text (lesson 10.1): prompted ReAct" in R
assert "  the model wrote: Plan: 1. Search for the passage the figure rests on." in P
assert ('  cut by the parser, which reads nothing from the first "Observation:" on:\n    | Observation: Rs 2,50,000\n' in I)
assert "  Final Answer: Gratuity, an estimate: Rs 2,50,000 [2]." in N and "cut by the parser" not in N
assert "2 model calls (12 at most), 1 search, 0 calculations, 0 refused or failed tool calls, 0 format errors" in N, N[-500:]
assert "figure check: no calculator, question or passage wrote 2,50,000 (desk_calc.unsupported)" in N
FORMULA = re.search(r"= Rs 2,40,000: (.+? = Rs 2,40,000)\n", T).group(1)
assert FORMULA == "7 years 8 months counts as 8 years (a part of a year over six months counts as a year); Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000"


# ------------------------------------------------------------------ every calculator row through every pattern, in process
def one_turn(mod, pattern: str, row: dict, invents: str | None = None) -> dict:
    """One single turn as make agent-turn OFFLINE=1 runs it: the row's scripted model, no slip, desk astar."""
    with mod.offline():
        llm = mod.scripted(row["question"], row["tenant"], task=row, pattern=pattern, invents=invents)
        return mod.run(pattern, row["question"], llm=llm, desk="astar", tenant=row["tenant"])


def nocut_module():
    """agent_patterns.py with the line marked THE CUT deleted, loaded in memory under its own name (the kit's test)."""
    path = KIT / AP
    kept = [ln for ln in path.read_text(encoding="utf-8").splitlines(keepends=True) if "THE CUT" not in ln]
    name = "agent_patterns_without_the_cut"
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None, origin=str(path)))
    mod.__file__ = str(path)
    sys.modules[name] = mod
    exec(compile("".join(kept), str(path), "exec"), mod.__dict__)
    return mod


def lines(text: str | None) -> list:
    return [ln.rstrip() for ln in (text or "").splitlines() if ln.strip()]


def shown(turn: dict) -> dict:
    """A turn as the panel draws it: each model call's counts, what the model wrote, what the parser cut, the calls
    code ran and the Observation code wrote; then the answer, the figure check and the totals (the script's)."""
    calls = {c["n"]: c for c in turn["calls"]}
    cards = []
    for step in turn["trace"]:
        c = calls[step["call"]]
        react = step.get("react")
        card = {"n": c["n"], "in": c["tokens_in"], "th": c["thinking_tokens"], "vis": c["visible_tokens"],
                "rs": f"{c['inr']:.4f}", "acts": [{"name": t["name"], "args": at._args(t["args"]), "obs": at._result(t),
                                                   "bad": t["status"] == "error"} for t in step["tools"]]}
        if react:
            card.update(wrote=lines(react["read"]), cut=lines(react.get("cut")), err=react.get("error"),
                        final="final" in react)
        else:                                # a plan beside a call, the answer with none, or nothing
            card.update(wrote=lines(step["text"]), cut=[], err=None, final=not step["tools"])
        cards.append(card)
    flag = desk_calc.unsupported(turn["answer"], turn["calculations"], turn["question"],
                                 *[p.get("text") or "" for p in turn["passages"]])
    return {"calls": cards, "answer": turn["answer"], "flag": flag,
            "calc": [f"{da.LABELS[c['calculator']]}: {c['formula']}" for c in turn["calculations"]],
            "tot": [turn["model_calls"], turn["tokens_in"], turn["thinking_tokens"], turn["visible_tokens"], f"{turn['inr']:.4f}"]}


TURNS = {r["id"]: {p: one_turn(ap, p, r) for p in OWN} for r in CALC}
for rid, by in TURNS.items():
    for p, turn in by.items():
        assert turn["stopped_by"] is None and turn["calculations"], (rid, p)
        assert ae.score(ROWS[rid], turn)["correct"] and ae.score(ROWS[rid], turn)["provenance"], (rid, p)
    for key in ("answer", "tool_calls", "calculations"):
        assert by["loop"][key] == by["react_text"][key] == by["plan_first"][key], (rid, key)
VARIANTS = {"held": TURNS[GRAT["id"]]["react_text"], "loose": one_turn(ap, "react_text", GRAT, INVENT),
            "nocut": one_turn(nocut_module(), "react_text", GRAT, INVENT)}
assert VARIANTS["loose"]["answer"] == "Gratuity, an estimate: Rs 2,40,000 [2]."
assert VARIANTS["nocut"]["answer"] == "Gratuity, an estimate: Rs 2,50,000 [2]." and not VARIANTS["nocut"]["calculations"]
LOOP_G, REACT_G, PLAN_G = (TURNS[GRAT["id"]][p] for p in OWN)
# the page's step 4 and 5 numbers are the CLI's: the in-process turns must be the same turns
for pat, text in (("loop", T), ("react_text", R), ("plan_first", P)):
    g = TURNS[GRAT["id"]][pat]
    assert (f"tokens: in {g['tokens_in']:,}, thinking {g['thinking_tokens']:,}, visible {g['visible_tokens']:,}; "
            f"Rs {g['inr']:.4f} for the model calls") in text, pat
assert [c["thinking_tokens"] for c in LOOP_G["calls"]] == [ap.SCRIPTED_THINKING["low"]] * 3

# ------------------------------------------------------------------ what the lane's runs cost, before thinking
def lane_estimate(turn: dict, pattern: str) -> tuple[float, int]:
    """(rupees for input and visible output, calls): the script's counts, plus the tool declarations Gemini receives
    with every loop and plan_first call (the script counts none); thinking is left out, because only the lane knows it."""
    extra = 0 if ap.PATTERNS[pattern].text else DECL_TOKENS
    rs = sum(prices.inr(prices.usd(MODEL, c["tokens_in"] + extra, c["visible_tokens"])) for c in turn["calls"])
    return rs, len(turn["calls"])


EST = {}
for p in OWN:
    rs, calls = map(sum, zip(*(lane_estimate(TURNS[r["id"]][p], p) for r in CALC)))
    EST[p] = (rs, calls)
EVAL_RS = sum(v[0] for v in EST.values())
EVAL_CALLS = sum(v[1] for v in EST.values())
G_RS = {p: lane_estimate(TURNS[GRAT["id"]][p], p)[0] for p in OWN}
LEVELS_RS, LEVELS_CALLS = 4 * G_RS["loop"], 4 * len(LOOP_G["calls"])
BATCH4_RS = G_RS["plan_first"] + EVAL_RS
BATCH4_CALLS = len(PLAN_G["calls"]) + EVAL_CALLS
ALL_RS = LEVELS_RS + G_RS["react_text"] + BATCH4_RS
ALL_CALLS = LEVELS_CALLS + len(REACT_G["calls"]) + BATCH4_CALLS
ALL_TURNS = 4 + 1 + 1 + len(CALC) * 3


def money(x: float) -> str:
    return f"{x:,.2f}"


COST = {"EST_LEVELS": money(LEVELS_RS), "EST_REACT": money(G_RS["react_text"]), "EST_PLAN": money(G_RS["plan_first"]),
        "EST_LOOP": money(G_RS["loop"]), "EST_EVAL": money(EVAL_RS), "EST_ALL": money(ALL_RS),
        "EST_BATCH4": money(BATCH4_RS), "K_EVAL": money(EVAL_CALLS * RS_K_OUT), "K_ALL": money(ALL_CALLS * RS_K_OUT),
        "K_LEVELS": money(LEVELS_CALLS * RS_K_OUT), "K_BATCH4": money(BATCH4_CALLS * RS_K_OUT),
        "N_EVAL_CALLS": str(EVAL_CALLS), "N_ALL_CALLS": str(ALL_CALLS), "N_ALL_TURNS": str(ALL_TURNS),
        "CAP_EVAL": money(len(CALC) * 3 * limits.TURN_BUDGET_INR), "CAP_ALL": money(ALL_TURNS * limits.TURN_BUDGET_INR),
        # the thinking a call that keeps batch 4's bench turns within the lesson plan's Rs 60 (section 7: Rs 40-60)
        "T60": str(int((60 - BATCH4_RS) * 1000 / (BATCH4_CALLS * RS_K_OUT)))}

# ------------------------------------------------------------------ the offline eval: its report, then the page's own paired cells
assert eval_proc.wait(timeout=1800) == 0, "the offline eval failed"
eval_out.seek(0)
eval_err.seek(0)
OUT["eval_off"] = as_learner(eval_out.read())
quiet_err(eval_err.read())
eval_out.close()
eval_err.close()
EO = OUT["eval_off"]
assert EO.startswith("OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 11 rows, 3 arms, 1 run each")
assert "saved 33 runs to /home/you/bench-101-offline.jsonl" in EO
for p in OWN:
    assert f"== {p}, thinking default (low), desk astar: 11 rows x 1 run" in EO
assert EO.count("first runs: correct    11/11 = 100.0%") == 3
SLIPS = [r["id"] for r in CALC if ap.slips(r, 0)]
assert SLIPS == ["calc-gratuity-7y8m", "calc-grc-threshold"], SLIPS
assert EO.count(f"provenance {len(CALC) - len(SLIPS)}/11") == 3 and EO.count("no gratuity_estimate call returned it; unsupported: 2,40,000") == 3
assert EO.count("no threshold_check call returned it") == 3
EVAL_OFF_RS = {p: re.search(r"== " + p + r", thinking default \(low\).*?\n  a run: [^\n]*?Rs ([\d.]+) for the model", EO, re.S).group(1)
               for p in OWN}

SPLIT_PY = r'''import json, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "commands"]
import agent_patterns as ap      # the standard library and shared/ only, at import: read_step() is the bench's own parser

saved, home = os.environ["SAVED"], os.path.expanduser("~")
runs = [json.loads(line) for line in open(saved, encoding="utf-8") if line.strip()]
print(f"{len(runs)} runs in {saved.replace(home, '~')}")
for pattern in [p for p in ap.PATTERNS if any(r["arm"]["pattern"] == p for r in runs)]:
    mine = [r for r in runs if r["arm"]["pattern"] == pattern]
    calls = [c for r in mine for c in r["calls"] if not c.get("error")]
    out = saved[:-len(".jsonl")] + f"-{pattern}.jsonl"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in mine)
    n = max(len(calls), 1)
    line = (f"{pattern:<10} {len(mine)} runs, {len(calls)} calls; a call reads {sum(c['tokens_in'] for c in calls) / n:,.0f}, "
            f"thinks {sum(c['thinking_tokens'] for c in calls) / n:,.0f}, writes {sum(c['visible_tokens'] for c in calls) / n:,.0f}; "
            f"Rs {sum(r['inr'] for r in mine):.2f} in all")
    if ap.PATTERNS[pattern].text:
        past = sum(ap.STOP in (c.get("text") or "") for c in calls)
        unread = sum("error" in ap.read_step(c.get("text") or "") for c in calls)
        line += f"; {past} replies ran past the stop, {unread} format errors"
    print(line)'''
COMPARES = [("loop", "react_text"), ("loop", "plan_first")]


def paired_cell(saved: str) -> str:
    """The page's Rs 0 cell for a saved run: split it by pattern, then two paired comparisons against the loop."""
    return (f'export SAVED="{saved}"\n' + "python - <<'PY'\n" + SPLIT_PY + "\nPY\n"
            + "\n".join(f'make agent-eval COMPARE="${{SAVED%.jsonl}}-{a}.jsonl ${{SAVED%.jsonl}}-{b}.jsonl"' for a, b in COMPARES))


split_out, err = run_py(["-"], stdin=SPLIT_PY, env={"SAVED": SAVED_OFF})
assert not err.strip(), err
compare_outs = []
for a, b in COMPARES:
    stem = SAVED_OFF[:-len(".jsonl")]
    o, err = run_py([AE, "--compare", f"{stem}-{a}.jsonl", f"{stem}-{b}.jsonl"])
    assert not err.strip(), err
    compare_outs.append(o)
OUT["paired_off"] = as_learner(split_out + "".join(compare_outs))
PO = OUT["paired_off"]
assert PO.startswith("33 runs in ~/bench-101-offline.jsonl\nloop       11 runs, 31 calls;"), PO[:200]
assert "0 replies ran past the stop, 0 format errors" in PO
for a, b in COMPARES:
    assert f"  paired (correct), 11 rows: both 11, {a} only 0, {b} only 0, neither 0" in PO
    assert f"  paired (verified), 11 rows: both 9, {a} only 0, {b} only 0, neither 2" in PO
TIE_HALF = round(100 * (1 - paired.wilson(11, 11)[0]), 1)
assert f"= +0.0 points, 95% [-{TIE_HALF:.1f}, +{TIE_HALF:.1f}] (Newcombe), exact McNemar p = 1.000" in PO, PO
assert "no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08)" in PO

# ------------------------------------------------------------------ the live cells, proved to run against stand-ins
PASSAGES_PY = r'''import json, os, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
PROJECT, API = os.environ["PROJECT"], os.environ["API"]
token = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                        f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"],
                       capture_output=True, text=True, check=True).stdout.strip()
body = {"query": "%(search)s", "tenant_id": "acme", "top_k": 5,
        "stream": False, "filters": {"doc_type": %(classes)s}, "brain": "desk"}
req = urllib.request.Request(f"{API}/v1/passages", data=json.dumps(body).encode(), method="POST",
                             headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
got = json.load(urllib.request.urlopen(req, timeout=60))
u = got["usage"]
print(f"answerable {got['answerable']} | passages {len(got['passages'])} | model {u['model']} | cost_usd {u['cost_usd']} | "
      f"tokens {u['tokens_in']} in, {u['tokens_out']} out | pool {u['stages']['pool']}")
for p in got["passages"]:
    print(f"  [{p['n']}] {p['source_uri'].rsplit('/', 1)[-1]:<38} {p['doc_type']:<9} {len(p['text']):>6,} characters")
print(f"every later call of the turn reads them again: {sum(len(p['text']) for p in got['passages']):,} characters")''' % {
    "search": GRAT["search"], "classes": json.dumps(SEARCH_CLASSES)}

ROWS_PY = r'''import json, os, subprocess, warnings
from collections import Counter
warnings.filterwarnings("ignore", category=UserWarning)
flt = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
       'AND jsonPayload.event="passages" AND jsonPayload.brain="desk"')
out = subprocess.run(["gcloud", "logging", "read", flt, "--project", os.environ["PROJECT"], "--freshness", "1d",
                      "--limit", "500", "--format", "json"], capture_output=True, text=True, check=True).stdout
rows = [e["jsonPayload"] for e in json.loads(out or "[]")]
print(f"{len(rows)} passages rows labelled brain desk in the last day; by tenant {dict(Counter(r['tenant'] for r in rows))}")
print(f"  model {sorted({r['model'] for r in rows})} | tokens {sum(r['tokens_in'] + r['tokens_out'] for r in rows)} | "
      f"cost_usd {sum(r['cost_usd'] for r in rows)} | answerable {sum(bool(r['answerable']) for r in rows)} of {len(rows)}")
print(f"  asked as {sorted({r['user'].split('@')[0] for r in rows})}")'''

# /v1/passages, stood in by the local lane's own retrieve(passages=True) over the kit's corpus, behind a token check
from shared import documind_tools  # noqa: E402


class Api(BaseHTTPRequestHandler):
    """POST /v1/passages: the local lane's passages for the body, in the route's response shape."""

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        assert self.path == "/v1/passages" and self.headers.get("Authorization") == "Bearer UI-SA", self.headers
        with ap.offline():
            got = documind_tools.retrieve(body["query"], body["tenant_id"], top_k=body["top_k"],
                                          doc_type=body["filters"]["doc_type"], brain=body["brain"], passages=True)
        out = {"passages": [{**p, "source_uri": f"gs://documind-ai-YOUR-ID-uploads/acme/{p['source_uri'].rsplit('/', 1)[-1]}"}
                            for p in got["passages"]],
               "answerable": got["answerable"], "usage": {"tokens_in": 0, "tokens_out": 0, "cached_tokens": 0, "cost_usd": 0.0,
                                                          "model": "none", "backend": "none", "latency_ms": 1,
                                                          "stages": {"pool": 20, "rerank_ms": 0}}}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


api = ThreadingHTTPServer(("127.0.0.1", 0), Api)
threading.Thread(target=api.serve_forever, daemon=True).start()
FAKE_GCLOUD = ("import json, subprocess\n"
               "class _Out:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
               "ROWS = json.loads(%r)\n"
               "def run(cmd, **kw):\n"
               "    if cmd[1:3] == ['auth', 'print-identity-token']:\n"
               "        assert '--impersonate-service-account=documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com' in cmd\n"
               "        return _Out('UI-SA\\n')\n"
               "    assert cmd[1:3] == ['logging', 'read'] and 'jsonPayload.brain=\"desk\"' in cmd[3]\n"
               "    return _Out(json.dumps([{'jsonPayload': r} for r in ROWS]))\n"
               "subprocess.run = run                        # only gcloud is stood in\n")
STAND_ROWS = [{"event": "passages", "tenant": t, "user": "documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
               "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0, "model": "none", "answerable": True, "brain": "desk"}
              for t in ("acme", "acme", "zeta")]
prelude = FAKE_GCLOUD % json.dumps(STAND_ROWS)
try:
    probe_env = {"PROJECT": "documind-ai-YOUR-ID", "API": f"http://127.0.0.1:{api.server_address[1]}"}
    stood, err = run_py(["-"], stdin=prelude + PASSAGES_PY, env=probe_env)
    assert not err.strip(), err
    assert re.match(r"answerable True \| passages 5 \| model none \| cost_usd 0\.0 \| tokens 0 in, 0 out \| pool 20\n", stood), stood
    assert re.search(r"\n  \[2\] code_on_social_security_2020\.pdf +statute +[\d,]+ characters\n", stood), stood
    assert "every later call of the turn reads them again: " in stood
    stood, err = run_py(["-"], stdin=prelude + ROWS_PY, env=probe_env)
    assert not err.strip(), err
    assert stood.startswith("3 passages rows labelled brain desk in the last day; by tenant {'acme': 2, 'zeta': 1}") and "asked as ['documind-ui-sa']" in stood, stood
finally:
    api.shutdown()
PASSAGE_CHARS = sum(len(p["text"]) for p in LOOP_G["passages"])
assert PASSAGE_CHARS / ap.CHARS_PER_TOKEN > 0.5 * LOOP_G["calls"][2]["tokens_in"]   # "most of what call 2 and call 3 read"
assert PASSAGE_CHARS / ap.CHARS_PER_TOKEN > 0.5 * LOOP_G["calls"][1]["tokens_in"]

# ------------------------------------------------------------------ the author's runs: what a live lane printed
REC_NAMES = ("ui_chat", "turn_levels", "turn_react", "turn_plan", "passages", "eval_patterns", "eval_paired", "passages_rows")
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
GREP = "grep -E '^(  thinking:|model call|tokens:|figure check|the turn failed|make: )'"
assert all(re.match(r"^(  thinking:|model call|tokens:|figure check|the turn failed|make: )", ln) for ln in levels)
INVENT_CMD = "make agent-turn OFFLINE=1 PATTERN=react_text INVENT=1"
CELLS = {
    "classes": ("run in the operator shell, in the kit (once: acme's and zeta's stored rows get the classes the bench searches)",
                'for t in acme zeta; do make doc-types PROJECT="$PROJECT" TENANT=$t SEED=manifest APPLY=1; done'),
    "turn_loop": ("run in the operator shell, in the kit (Rs 0: a scripted model and the kit's corpus; the first run builds ~/graph-venv)",
                  "make agent-turn OFFLINE=1"),
    "levels_off": ("run in the operator shell, in the kit (Rs 0: the same turn at the four levels, the per-call lines only)",
                   f"for t in minimal low medium high; do make agent-turn OFFLINE=1 THINKING=$t 2>&1 | {GREP}; done"),
    "turn_react_off": ("run in the operator shell, in the kit (Rs 0: prompted ReAct on the same question)",
                       "make agent-turn OFFLINE=1 PATTERN=react_text"),
    "turn_plan_off": ("run in the operator shell, in the kit (Rs 0: the plan-first prompt on the same question)",
                      "make agent-turn OFFLINE=1 PATTERN=plan_first"),
    "invent": ("run in the operator shell, in the kit (Rs 0: a scripted model whose stop sequence does not hold)", INVENT_CMD),
    "cut": ("run in the operator shell, in the kit (the Change-it: delete the cut, then the same run)",
            "sed -i '/THE CUT/d' commands/agent_patterns.py && git diff --stat\n" + INVENT_CMD),
    "restore": ("run in the operator shell, in the kit (put the line back)",
                'git checkout -q -- commands/agent_patterns.py && git diff --stat && grep -c "THE CUT" commands/agent_patterns.py'),
    "check": ("run in the operator shell, in the kit (Rs 0, the standard library: every figure of the slice recomputed)",
              "make agent-eval CHECK=1 SLICE=calc"),
    "eval_off": ("run in the operator shell, in the kit (Rs 0: 33 scripted turns, a few minutes)",
                 'make agent-eval OFFLINE=1 PATTERNS=loop,react_text,plan_first SLICE=calc SAVE="$HOME/bench-101-offline.jsonl"'),
    "paired_off": ("run in the operator shell, in the kit (Rs 0: the saved runs split by pattern, then paired)",
                   paired_cell("$HOME/bench-101-offline.jsonl")),
    "levels": (f"run in the operator shell, in the kit (four live turns of the loop, about Rs {COST['EST_LEVELS']} before thinking)",
               f"for t in minimal low medium high; do make agent-turn {LANE} THINKING=$t 2>&1 | {GREP}; done"),
    "react": (f"run in the operator shell, in the kit (one live turn, about Rs {COST['EST_REACT']} before thinking)",
              f"make agent-turn {LANE} PATTERN=react_text"),
    "plan": (f"run in the operator shell, in the kit (one live turn, about Rs {COST['EST_PLAN']} before thinking)",
             f"make agent-turn {LANE} PATTERN=plan_first"),
    "passages": ("run in the operator shell, in the kit (a Python cell; Rs 0: /v1/passages calls no model)", heredoc(PASSAGES_PY)),
    "eval": (f"run in the operator shell, in the kit (33 live turns, about Rs {COST['EST_EVAL']} before thinking)",
             f'make agent-eval {LANE} PATTERNS=loop,react_text,plan_first SLICE=calc SAVE="$HOME/bench-101-lane.jsonl"'),
    "paired": ("run in the operator shell, in the kit (Rs 0: your lane's saved runs split by pattern, then paired)",
               paired_cell("$HOME/bench-101-lane.jsonl")),
    "rows": ("run in the operator shell, in the kit (a Python cell; Rs 0: one Cloud Logging read)", heredoc(ROWS_PY)),
}
OUTS = {
    "turn_loop": ("(the kit's own output, produced when this page was built; yours should match it)", OUT["turn_loop"]),
    "levels_off": ("(the kit's own output; the thinking counts are the script's)", OUT["levels_off"]),
    "turn_react_off": ("(the kit's own output, produced when this page was built)", OUT["turn_react_off"]),
    "turn_plan_off": ("(the kit's own output, produced when this page was built)", OUT["turn_plan_off"]),
    "invent": ("(the kit's own output: the parser's cut in place)", OUT["invent"]),
    "cut": ("(git's stat for the deletion, then the kit's own output with the cut deleted)", OUT["cut"]),
    "restore": ("(git's stat prints nothing: the file is the kit's again)", OUT["restore"]),
    "check": ("(the kit's own output, produced when this page was built)", OUT["check"]),
    "eval_off": ("(stdout, produced when this page was built; one progress line a run goes to stderr)", OUT["eval_off"]),
    "paired_off": ("(the kit's own output on that saved file, produced when this page was built)", OUT["paired_off"]),
    "ui_chat": ("(the author's lane, langchain then adk: your words, figures, times and rupees are yours)", REC["ui_chat"]),
    "levels": ("(the author's lane: the thinking counts are the model's, so yours differ)", REC["turn_levels"]),
    "react": ("(the author's lane: the model wrote these lines, so yours differ)", REC["turn_react"]),
    "plan": ("(the author's lane: the plan is the model's own)", REC["turn_plan"]),
    "passages": ("(the author's lane)", REC["passages"]),
    "eval": ("(the author's lane, stdout: every figure in it is the lane's)", REC["eval_patterns"]),
    "paired": ("(the author's lane's saved runs)", REC["eval_paired"]),
    "rows": ("(the author's lane)", REC["passages_rows"]),
}
WIN = {f"CELL_{k.upper()}": bash_window(*v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})

# ------------------------------------------------------------------ the Level 0 panel: its data and its script
ROW_LABEL = {}
for r in CALC:
    v, unit = r["expected"], r["unit"]
    shown_v = (desk_calc.inr(v) if unit == "INR" else f"{desk_calc.num(v)} days" if unit == "days"
               else "yes" if unit == "yes/no" else str(v))
    ROW_LABEL[r["id"]] = f"{r['id']}: {shown_v}"
PANEL = {
    "order": list(OWN),
    "rows": [{"id": r["id"], "label": ROW_LABEL[r["id"]], "q": r["question"]} for r in CALC],
    "pat": {"loop": {"how": "Native thinking. The model thinks in tokens nobody sees, then calls a tool by function calling.", "text": False},
            "react_text": {"how": "Prompted ReAct. The model writes Thought and Action as text and stops at \"Observation:\". "
                                  "Code reads the Action, runs it and writes the Observation.", "text": True},
            "plan_first": {"how": "A plan first. The loop, told to write a numbered plan before its first call. Nothing runs the plan.",
                           "text": False}},
    "traces": {rid: {p: shown(t) for p, t in by.items()} for rid, by in TURNS.items()},
    "variants": {k: shown(t) for k, t in VARIANTS.items()},
    "inventRow": GRAT["id"],
}
assert PANEL["variants"]["nocut"]["flag"] == ["2,50,000"] and PANEL["variants"]["loose"]["calls"][1]["cut"][0] == "Observation: Rs 2,50,000"
JS = """<script>
(function(){
  'use strict';
  var D = __DATA__;
  var root = document.getElementById('ota'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var rowSel = $('ota-row'), stopSel = $('ota-stop'), cols = $('ota-cols'), at = $('ota-at'), step = 1;
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function fmt(n){ return String(n).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ','); }
  function trace(p){ return (p === 'react_text' && rowSel.value === D.inventRow && stopSel.value !== 'held') ? D.variants[stopSel.value] : D.traces[rowSel.value][p]; }
  function last(){ var m = 0; D.order.forEach(function(p){ m = Math.max(m, trace(p).calls.length + 1); }); return m; }
  function block(box, label, arr, cls){ if (!arr || !arr.length) return; var d = el('div', 'ota-l' + (cls ? ' ' + cls : '')); d.appendChild(el('b', '', label)); d.appendChild(el('pre', '', arr.join('\\n'))); box.appendChild(d); }
  function card(p, c){
    var box = el('div', 'ota-c'), text = D.pat[p].text;
    box.appendChild(el('div', 'ota-h', 'call ' + c.n + ': reads ' + fmt(c['in']) + ', thinks ' + fmt(c.th) + ', writes ' + fmt(c.vis) + ' tokens, Rs ' + c.rs));
    box.appendChild(el('p', 'ota-t', c.th ? 'Thinks ' + fmt(c.th) + ' tokens first: billed as output, never shown.' : 'Thinks no tokens at this level.'));
    block(box, text ? 'Writes, as text:' : (c.acts.length ? 'Writes beside its call:' : 'Writes its answer:'), c.wrote);
    block(box, 'Cut by the parser, never read:', c.cut, 'cut');
    c.acts.forEach(function(a){ block(box, (text ? 'Code reads the Action and runs ' : 'Calls, by function calling, ') + a.name + '(' + a.args + '). The Observation, written by code:', a.obs, a.bad ? 'bad' : ''); });
    if (c.err) block(box, 'The Observation, written by code: no Action it could run', [c.err], 'bad');
    return box;
  }
  function answer(t){
    var box = el('div', 'ota-a' + (t.flag.length ? ' bad' : ''));
    box.appendChild(el('p', '', 'Answer: ' + t.answer));
    box.appendChild(el('p', '', t.calc.length ? 'Worked out in code: ' + t.calc.join('; ') : 'Worked out in code: nothing. No calculator ran.'));
    box.appendChild(el('p', '', t.flag.length ? 'Figure check: no calculator, question or passage wrote ' + t.flag.join(', ') + '.' : 'Figure check: every figure has a source.'));
    box.appendChild(el('p', 'ota-sum', t.tot[0] + ' calls: reads ' + fmt(t.tot[1]) + ', thinks ' + fmt(t.tot[2]) + ', writes ' + fmt(t.tot[3]) + ' tokens, Rs ' + t.tot[4]));
    return box;
  }
  function render(){
    var n = last(); step = Math.max(1, Math.min(step, n));
    stopSel.disabled = rowSel.value !== D.inventRow;
    cols.textContent = '';
    D.order.forEach(function(p){
      var t = trace(p), col = el('div', 'ota-col');
      col.appendChild(el('div', 'ota-name', p));
      col.appendChild(el('p', 'ota-how', D.pat[p].how));
      t.calls.slice(0, step).forEach(function(c){ col.appendChild(card(p, c)); });
      if (step > t.calls.length) col.appendChild(answer(t));
      cols.appendChild(col);
    });
    at.textContent = step < n ? 'model call ' + step + ' of each turn' : 'every call, and the answers';
    $('ota-back').disabled = step <= 1; $('ota-next').disabled = step >= n;
  }
  D.rows.forEach(function(r){ var o = el('option', '', r.label); o.value = r.id; rowSel.appendChild(o); });
  rowSel.value = D.inventRow;
  rowSel.addEventListener('change', function(){ step = 1; render(); });
  stopSel.addEventListener('change', function(){ render(); });
  $('ota-back').addEventListener('click', function(){ step--; render(); });
  $('ota-next').addEventListener('click', function(){ step++; render(); });
  $('ota-all').addEventListener('click', function(){ step = last(); render(); });
  render();
})();
</script>
""".replace("__DATA__", json.dumps(PANEL, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"))
assert "<div" not in JS and "font-size" not in JS

# ------------------------------------------------------------------ the numbers the prose states
NEXT = MANIFEST["modules"]["10"]["lessons"]["10.2"]["name"]


def tok(n: int) -> str:
    return f"{n:,}"


STATS = {
    "MODEL": MODEL, "RATE_IN": f"{RATE_IN:.2f}", "RATE_OUT": f"{RATE_OUT:.2f}", "USD_INR": str(prices.USD_INR),
    "RS_K_OUT": f"{RS_K_OUT:.2f}", "RS_K_IN": f"{RS_K_IN:.2f}", "MAX_CALLS": str(limits.MAX_MODEL_CALLS),
    "BUDGET": f"{limits.TURN_BUDGET_INR:g}", "DEADLINE": f"{limits.TURN_DEADLINE_S:g}", "DEFAULT_LEVEL": da.THINKING_LEVEL,
    "N_TOOLS": str(N_TOOLS), "N_CALCS": str(len(desk_calc.CALCULATORS)), "CALC_ROWS": "\n".join(CALC_ROWS),
    "N_TASKS": str(len(TASKS)), "N_CALC": str(KINDS["calc"]), "N_LOOKUP": str(KINDS["lookup"]), "CHAINED": CHAINED,
    "DECL_TOKENS": tok(DECL_TOKENS), "PROTOCOL_TOKENS": tok(PROTOCOL_TOKENS), "QUESTION": html.escape(GRAT["question"]),
    "FORMULA": html.escape(FORMULA), "SEARCH": html.escape(GRAT["search"]), "INVENT": html.escape(INVENT),
    "SCRIPT_TH": (f"{tok(ap.SCRIPTED_THINKING['minimal'])} thinking tokens a call at minimal, "
                  f"{tok(ap.SCRIPTED_THINKING['low'])} at low, {tok(ap.SCRIPTED_THINKING['medium'])} at medium "
                  f"and {tok(ap.SCRIPTED_THINKING['high'])} at high"),
    "LOOP_IN": tok(LOOP_G["tokens_in"]), "REACT_IN": tok(REACT_G["tokens_in"]), "PLAN_IN": tok(PLAN_G["tokens_in"]),
    "LOOP_VIS": tok(LOOP_G["visible_tokens"]), "REACT_VIS": tok(REACT_G["visible_tokens"]), "PLAN_VIS": tok(PLAN_G["visible_tokens"]),
    "LOOP_RS": f"{LOOP_G['inr']:.4f}", "REACT_RS": f"{REACT_G['inr']:.4f}", "PLAN_RS": f"{PLAN_G['inr']:.4f}",
    "LOOP_IN_DECL": tok(LOOP_G["tokens_in"] + DECL_TOKENS * len(LOOP_G["calls"])),
    "PLAN_EXTRA_IN": tok(PLAN_G["calls"][1]["tokens_in"] - LOOP_G["calls"][1]["tokens_in"]),
    "PLAN_EXTRA_VIS": tok(PLAN_G["calls"][0]["visible_tokens"] - LOOP_G["calls"][0]["visible_tokens"]),
    "LOOP_C1_IN": tok(LOOP_G["calls"][0]["tokens_in"]), "REACT_C1_IN": tok(REACT_G["calls"][0]["tokens_in"]),
    "PASSAGE_CHARS": tok(PASSAGE_CHARS), "SLIPS": " and ".join(f"<code>{s}</code>" for s in SLIPS),
    "N_PROV": str(len(CALC) - len(SLIPS)), "TIE_HALF": f"{TIE_HALF:.1f}",
    "EVAL_OFF_LOOP": EVAL_OFF_RS["loop"], "EVAL_OFF_REACT": EVAL_OFF_RS["react_text"], "EVAL_OFF_PLAN": EVAL_OFF_RS["plan_first"],
    "MARGIN": f"{100 * paired.MARGIN:g}", "NEXT_TITLE": html.escape(NEXT), **COST,
    "LEV_MIN_RS": LEVEL_RS[0][2], "LEV_HIGH_RS": LEVEL_RS[-1][2], "LEV_IN": LEVEL_RS[0][0],
    "EST_MIN": money(min(G_RS.values())), "EST_MAX": money(max(G_RS.values())),
    "PLAN_C1_EXTRA_IN": tok(PLAN_G["calls"][0]["tokens_in"] - LOOP_G["calls"][0]["tokens_in"]),
    "N_SLIPS": str(len(SLIPS)),
}
if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(json.dumps(COST, indent=1))
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
shutil.rmtree(SCRATCH, ignore_errors=True)

# the run list's prices, from the same figures: a stale line is named here, not silently kept
run_list = (pb.lesson_dir(LESSON) / "RUN_LIST.md").read_text(encoding="utf-8")
for k in ("EST_LEVELS", "EST_REACT", "EST_PLAN", "EST_EVAL", "EST_ALL", "EST_BATCH4", "K_EVAL", "K_ALL", "K_LEVELS",
          "K_BATCH4", "CAP_EVAL", "CAP_ALL"):
    if f"Rs {COST[k]}" not in run_list:
        print(f"note: RUN_LIST.md does not state {k} = Rs {COST[k]}")
if f"about {COST['T60']} thinking tokens" not in run_list:
    print(f"note: RUN_LIST.md does not state T60 = about {COST['T60']} thinking tokens a call")
print(f"kit: {len(CALC)} calculator rows x {len(OWN)} patterns offline, all correct | the gratuity turn: loop Rs "
      f"{LOOP_G['inr']:.4f}, react_text Rs {REACT_G['inr']:.4f}, plan_first Rs {PLAN_G['inr']:.4f} (the script's) | "
      f"lane before thinking: levels Rs {COST['EST_LEVELS']}, react Rs {COST['EST_REACT']}, plan Rs {COST['EST_PLAN']}, "
      f"eval Rs {COST['EST_EVAL']} ({EVAL_CALLS} calls), all Rs {COST['EST_ALL']}; Rs {COST['K_ALL']} for each 1,000 thinking "
      f"tokens a call | declarations ~{DECL_TOKENS} tokens a call")
