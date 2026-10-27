"""Build lesson 6.8 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Resume a paused or cut-off turn. A turn is a run of steps and LangGraph saves a checkpoint after each one; a turn that
stops halfway keeps a `next`, and graph.invoke(None, config) runs exactly that. The page reads the learner's own UI
conversation back from the lane (make thread), finishes the kit's cut-off turn offline and replays a finished one to
match (make replay OFFLINE=1), shows what /v1/chat does instead (a new question that makes LangGraph discard the pending
search, and limits.repair_thread), exports the lane thread and replays and forks it on the learner's machine with
Gemini (make replay FILE=), with a Change-it on the prompt, and reads the table directly to show the lane unchanged.

Build it with the chat image's pins (LangGraph 1.2.12): venvs312/chat's python, `python pagekit/build.py 6.8`.
Computed here, on the kit: the offline replays and step 5's offline cell, run as the page runs them; the Level 0
panel, which is the fixture evals/threads/cut_off_turn.json plus four ways on from its cut, each run here on the kit's
LangGraph brain with make replay OFFLINE=1's script; LangGraph's discard, checked at the pinned version's own line;
the Change-it's edit and restore, on a copy. The lane cells are checked here against stand-ins (the kit test's fake
gcloud and connector over rows the kit's brain wrote, a scripted model, a fake Cloud SQL), and the page shows the
author's recorded runs (pb.recorded; RUN_LIST.md says which command records which file).
"""
import base64
import contextlib
import html
import importlib.metadata
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "6.8"
NAME = MANIFEST["modules"]["06"]["lessons"][LESSON]["name"]
NEXT_LID = "6.9"
NEXT_NAME = MANIFEST["modules"]["06"]["lessons"][NEXT_LID]["name"]
title = (f"<title>Lesson {LESSON} {NAME} - your conversation read back step by step, a cut-off turn finished from its "
         "last checkpoint, and a replay and a fork on your machine | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
ME = "you@your-company.com"
UI_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
Q1 = "After how many years of continuous service is gratuity payable?"     # step 3's two questions in the UI
Q2 = "Is it payable to a contract employee?"
ASK = "Is gratuity payable to an apprentice?"                               # step 5's next question, and the panel's
FORK_Q = "Is it payable to an apprentice?"                                  # step 7's fork: another follow-up
SID = "5e2b9c41d0a7"                                                        # the stand-in UI session (12 hex, as the UI makes)

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,8em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.cr-chain{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 8px;}
.cr-chip{font:inherit;font-family:var(--mono);font-size:12.5px;min-width:44px;min-height:44px;padding:4px 10px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--slate);cursor:pointer;}
.cr-chip[aria-pressed="true"]{background:var(--navy);color:#fff;border-color:var(--navy);}
.cr-chip.cut{box-shadow:inset 0 0 0 2px #f59e0b;}
.cr-chip.new{border-style:dashed;border-color:var(--teal);}
.cr-btn{font:inherit;font-size:13px;min-height:44px;padding:6px 12px;border-radius:8px;border:1px solid var(--border);background:var(--card);cursor:pointer;color:var(--navy);margin:0 6px 8px 0;}
.cr-btn:disabled{opacity:.45;cursor:default;}
.cr-chip:active,.cr-btn:active{transform:scale(.97);}
.cr-msgs{margin:8px 0 0;padding-left:26px;font-family:var(--mono);font-size:12px;line-height:1.5;}
.cr-msgs li{margin:2px 0;overflow-wrap:anywhere;}
.cr-msgs li.newest{color:var(--navy);font-weight:600;}
.cr-wait{margin:6px 0 0;font-family:var(--mono);font-size:12px;line-height:1.5;color:#92400e;overflow-wrap:anywhere;}
.cr-say{margin:8px 0 0;font-size:13px;line-height:1.55;color:var(--slate);}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
TR, RP, MK, GV = "commands/thread_read.py", "commands/thread_replay.py", "mk/memory.mk", "commands/graph-venv.sh"
FX, BR, LM, AG = "evals/threads/cut_off_turn.json", "services/chat/brains.py", "services/chat/limits.py", "services/chat/agent.py"
FE, CFG, AP = "services/frontend/chat.py", "services/rag-api/config.py", "services/chat/approval.py"

FIX = json.loads((KIT / FX).read_text(encoding="utf-8"))
fx_lines = (KIT / FX).read_text(encoding="utf-8").splitlines()
LAST_ID = FIX["checkpoints"][-1]["checkpoint_id"]
fx_start = next(k for k, line in enumerate(fx_lines) if f'"checkpoint_id": "{LAST_ID}"' in line)
fx_end = next(k for k in range(fx_start, len(fx_lines)) if fx_lines[k] == "  }")       # the checkpoint's own closing brace

EXCERPTS = {
    "mk_thread": ("mk/memory.mk - make thread: thread_read.py in ~/graph-venv with the connector; EMAIL is documind-ui-sa unless you name one",
                  block(MK, "thread: guard-project", n=4)),
    "read_sql": ("commands/thread_read.py - the session made read only first, then SELECT statements only",
                 block(TR, 'READ_ONLY = "SET default_transaction_read_only = on"', end="class Refused(Exception):")),
    "read_lane": ("commands/thread_read.py - lane(): lesson 6.6's connection as a function, refusing anything but a SELECT",
                  block(TR, "@contextlib.contextmanager", end="def threads(")),
    "fixture": ("evals/threads/cut_off_turn.json - the thread's last checkpoint: the model's call saved, next tools",
                block(FX, f'"checkpoint_id": "{LAST_ID}"', n=fx_end - fx_start)),
    "cut": ("commands/thread_replay.py - write_fixture(): the second turn's stream closed right after the model asked for retrieve",
            block(RP, "        _, state, ctx = brains._turn(SECOND, dict(who))", n=8)),
    "copy": ("commands/thread_replay.py - as_node() and copy_thread(): each checkpoint copied as the node that wrote it, then checked",
             block(RP, "def as_node(new: list, lane_next: list) -> str:",
                   end="# ----------------------------------------------------------------------------- offline")),
    "run": ("commands/thread_replay.py - run(): resuming is graph.invoke(None, config)",
            block(RP, "def run(graph, cfg: dict, ctx: dict):", end="def ledger_of(")),
    "compare": ("commands/thread_replay.py - shape() and compare(): what a replay is compared on",
                block(RP, "def shape(messages: list) -> dict:", end="def _ids(")),
    "answer": ("services/chat/brains.py - LangGraphBrain.answer(): every turn is graph.invoke() with a new question; a repair only after a recursion error",
               block(BR, "    def answer(self, question: str, *, config: dict, context: dict) -> dict:", end="# ---", nth=2)),
    "repair": ("services/chat/limits.py - repair_thread(): every open call answered with an error, then the stop answer",
               block(LM, "def repair_thread(graph, config: dict, as_node: str) -> None:", end="# -----")),
    "decode": ("commands/thread_read.py - decode(): a checkpoint's values are its inline values plus each channel's blob at its version",
               block(TR, "def decode(thread_id: str, checkpoint_rows: list, blob_rows: list, write_rows: list, serde=None) -> list:",
                     end="def _config(")),
    "serde": ("commands/thread_read.py - serializer(): strict, so a blob revives only langgraph's safe types",
              block(TR, "def serializer():", end="def _bytes(")),
    "snapshots": ("commands/thread_read.py - snapshots(): each checkpoint read through the graph of the brain that wrote it",
                  block(TR, "def snapshots(tuples: list) -> list[dict]:", end="def export(")),
    "mk_replay": ("mk/memory.mk - make replay: no project with OFFLINE=1; otherwise Gemini, your rag-api and documind-ui-sa",
                  block(MK, "replay: $(if $(OFFLINE),,guard-project)", n=6)),
    "fork": ("commands/thread_replay.py - replay(): the fork, a new question written onto the turn's input checkpoint",
             block(RP, '        fcfg = brain.graph.update_state(configs[s], {"messages": [HumanMessage(fork_q, id=str(uuid.uuid4()))]},', n=5)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["mk_thread"].count("\n") == 3 and "--connector commands/thread_read.py" in E["mk_thread"]
assert E["read_sql"].startswith("READ_ONLY = ") and E["read_sql"].rstrip().endswith("}")
assert E["read_lane"].rstrip().endswith("db.close()") and 'raise Refused(f"thread_read runs SELECT statements only' in E["read_lane"]
assert '"next": [\n    "tools"\n   ],' in E["fixture"] and E["fixture"].rstrip().endswith('"input": []')
assert E["cut"].rstrip().endswith("tuples = list(saver.list(cfg))[::-1]") and "stream.close()" in E["cut"]
assert E["copy"].rstrip().endswith("return configs, problems") and 'as_node="__input__"' in E["copy"]
assert "graph.invoke(None, config=" in E["run"] and E["run"].rstrip().endswith('"recursion_limit"')
assert E["compare"].rstrip().endswith('return f"{head}: " + ", ".join(parts)')
assert "out = self.graph.invoke(state, config=" in E["answer"] and 'limits.repair_thread(self.graph, config, as_node="agent")' in E["answer"]
assert E["repair"].rstrip().endswith('graph.update_state(config, {"messages": patch + [stop_message()]}, as_node=as_node)')
assert E["decode"].rstrip().endswith("return out") and 'blobs[(channel, version)][0] != "empty"' in E["decode"]
assert "JsonPlusSerializer(allowed_msgpack_modules=None)" in E["serde"]
assert E["snapshots"].rstrip().endswith("return out") and "graphs[brain].get_state(t.config)" in E["snapshots"]
assert E["mk_replay"].count("\n") == 5 and "DOCUMIND_IMPERSONATE_SA=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com" in E["mk_replay"]
assert 'as_node="__start__")' in E["fork"] and E["fork"].rstrip().endswith('"meter": fork_meter})')
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (TR, RP, MK, GV, BR, LM, AG, FE, CFG, AP)}
mk_all = (KIT / "Makefile").read_text(encoding="utf-8")
assert re.search(r"(?m)^thread: guard-project$", src[MK]) and re.search(r"(?m)^replay: \$\(if \$\(OFFLINE\),,guard-project\)$", src[MK])
for flag in ('$(if $(SESSION),--session "$(SESSION)",)', '$(if $(AT),--at="$(AT)",)', '$(if $(EXPORT),--export "$(EXPORT)",)',
             '$(if $(OFFLINE),--offline,)', '$(if $(FILE),--file "$(FILE)",)', '$(if $(FORK),--fork "$(FORK)",)',
             '--email "$(or $(EMAIL),documind-ui-sa@$(PROJECT).iam.gserviceaccount.com)"',
             'RAG_API_URL=https://documind-api-$$NUMBER.$(REGION).run.app'):
    assert flag in src[MK], flag
phony = mk_all[mk_all.index(".PHONY:"):mk_all.index("# ---------- the module files")]
assert {"thread", "replay"} <= set(phony.split())
assert 'extra=("cloud-sql-python-connector[pg8000]==1.22.0" "pg8000==1.31.5")' in src[GV] and 'VENV="${GRAPH_VENV:-$HOME/graph-venv}"' in src[GV]
assert '"$VENV/bin/pip" install -q -r services/chat/requirements.txt' in src[GV]
assert "which nothing in the service\nprevents yet" in src[TR] or "which nothing in the service prevents yet" in " ".join(src[TR].split())
assert 'DESK = "desk~"' in src[TR] and "is listed and not decoded" in " ".join(src[TR].split())
assert "LangGraph works it out from the\ncheckpoint's versions and the graph's edges" in src[TR] or "LangGraph works it out from the checkpoint's versions and the graph's edges" in " ".join(src[TR].split())
reqs = dict(re.findall(r"^([a-z-]+)==([\d.]+)$", (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8"), re.M))
LG_VER, PG_VER = reqs["langgraph"], reqs["langgraph-checkpoint-postgres"]
assert (LG_VER, PG_VER) == ("1.2.12", "3.1.2"), (LG_VER, PG_VER)
try:
    LG_HERE = importlib.metadata.version("langgraph")
except importlib.metadata.PackageNotFoundError:
    LG_HERE = None
assert LG_HERE == LG_VER, f"build lesson 6.8 with the chat image's pins (venvs312/chat): langgraph here is {LG_HERE}, the image's {LG_VER}"
# LangGraph's own line: new input discards a checkpoint's unfinished tasks; invoke(None) and a Command resume instead
import langgraph.pregel._loop as lg_loop  # noqa: E402
loop_lines = Path(lg_loop.__file__).read_text(encoding="utf-8").splitlines()
LG_LINE = next(k + 1 for k, line in enumerate(loop_lines) if "# discard any unfinished tasks from previous checkpoint" in line)
assert LG_LINE == 978, LG_LINE
assert "self.input is None" in "\n".join(loop_lines[855:870]) and "input_is_command" in "\n".join(loop_lines[855:870])
# the service: every turn is new input, nothing resumes, a repair only after a recursion error, no fork route
lg_cls = re.search(r"class LangGraphBrain:.*?\nclass ", src[BR], re.S).group(0)
assert "out = self.graph.invoke(state, config=" in lg_cls and lg_cls.count("limits.repair_thread(") == 1
assert re.search(r"except GraphRecursionError:.*?\n.*?\n\s+limits\.repair_thread\(self\.graph", lg_cls)
chat_py = [p for p in (KIT / "services/chat").glob("*.py")]
assert not any("invoke(None" in p.read_text(encoding="utf-8") for p in chat_py)                            # nothing resumes a turn
writers = sorted(p.name for p in chat_py if re.search(r"update_state|get_state_history", p.read_text(encoding="utf-8")))
assert writers == ["limits.py"] and src[LM].count("update_state(") == 1                                     # repair_thread's, alone
assert not any(w in src[AG] for w in ("update_state", "get_state_history", "Command("))                     # no fork or resume route
chat_fn = src[AG][src[AG].index('@app.post("/v1/chat")'):src[AG].index("# The DocuMind Desk")]
assert "brain.answer(" in chat_fn and "try:" not in chat_fn                                                 # an exception is the request's 500
# Lesson 5.8's approval graph pauses with interrupt() and resumes with Command(resume=); since 13 October 2026 the service
# reaches it through one module, approval_routes.py, for a company whose agent_actions switch is approval (off by default).
assert "THE SERVICE REACHES THIS MODULE THROUGH ONE SWITCH, OFF UNTIL AN OPERATOR SETS IT" in src[AP]
assert "interrupt(request)" in src[AP] and "Command(resume=" in src[AP]
assert sorted(p.name for p in chat_py if re.search(r"^\s*(import approval\b|from approval import)", p.read_text(encoding="utf-8"), re.M)) == ["approval_routes.py"]
assert 'SWITCH, ON = "agent_actions", "approval"' in (KIT / "services/chat/approval_routes.py").read_text(encoding="utf-8")
CHANGE_FROM, CHANGE_TO = "document question, a follow-up too, and cite", "document question, and cite"
assert src[BR].count(CHANGE_FROM) == 1 and sum("a follow-up too" in line for line in src[BR].splitlines()) == 1
assert "st.session_state.session_id = uuid.uuid4().hex[:12]" in src[FE] and 'BRAINS = ("direct", "langchain", "langgraph", "adk")' in src[FE]
assert 'brain = st.radio("Brain", BRAINS, index=0,' in src[FE] and 'st.caption(f"brain: {body.get(\'brain\')}' in src[FE]
GEN_MODEL = re.search(r'generator_model: str = "([^"]+)"', src[CFG]).group(1)

# the kit's modules, imported here as the cells import them
sys.path[:0] = [str(KIT / "commands" / "tests"), str(KIT / "commands"), str(KIT / "services" / "chat"), str(KIT)]
os.environ.pop("DOCUMIND_PROFILE", None)
os.environ.pop("CHAT_MODEL", None)
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
import thread_read as tr  # noqa: E402
import thread_replay as rp  # noqa: E402
import test_thread_read as tt  # noqa: E402 - the kit test's own stand-ins: a fake gcloud, a fake connector, PostgresSaver's rows
import brains  # noqa: E402
import limits  # noqa: E402
from shared import prices  # noqa: E402
from langgraph.checkpoint.memory import InMemorySaver  # noqa: E402

assert tr.READ_ONLY == "SET default_transaction_read_only = on" and all(s.startswith("SELECT ") for s in tr.SQL.values())
assert rp.FIXTURE == KIT / FX and rp.NODE == {"model": "agent"}
assert brains.MODEL == GEN_MODEL == prices.DEFAULT_MODEL == "gemini-3.6-flash" and prices.PROFILE == "gcp"
DOC = rp.load(rp.FIXTURE)
CHAIN = DOC["checkpoints"]
N_CK, CUT_STEP = len(CHAIN), CHAIN[-1]["step"]
TURN_STARTS = [cp["step"] for cp in CHAIN if cp["source"] == "input"]
assert (N_CK, CUT_STEP, TURN_STARTS) == (8, 6, [-1, 4]) and CHAIN[-1]["next"] == ["tools"] and CHAIN[-1]["source"] == "loop"
CUT_CALL = CHAIN[-1]["messages"][-1]
assert CUT_CALL.type == "ai" and [c["name"] for c in CUT_CALL.tool_calls] == ["retrieve"]
CUT_CALL_ID = CUT_CALL.tool_calls[0]["id"]
assert [m.content for cp in CHAIN for m in cp["input"]] == [rp.FIRST, rp.SECOND]
N_FIRST = sum(1 for cp in CHAIN if cp["step"] < TURN_STARTS[1])
assert N_FIRST == 5


# ------------------------------------------------------------------ the cells
def heredoc(body: str, prefix: str = "", python: str = "python") -> str:
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


GV_PY = "~/graph-venv/bin/python"

THREADS_SH = """make thread EMAIL="$ME" | tee /tmp/lesson68-threads.txt          # your threads, the latest written first
SID=$(awk '$1 == "acme" && $2 !~ /^desk~/ {print $2; exit}' /tmp/lesson68-threads.txt)   # the newest chat thread: the UI's
echo "SID=$SID"
make thread EMAIL="$ME" SESSION="$SID"                              # that thread, a row per checkpoint"""

NEXT_PY = """import logging, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
logging.disable(logging.WARNING)                         # the tool layer's timing lines are not this cell's output
sys.path[:0] = [".", "services/chat", "commands"]
from langgraph.checkpoint.memory import InMemorySaver
import brains, limits, thread_read as tr, thread_replay as rp
doc = rp.load(rp.FIXTURE)                                # the cut-off thread step 4 resumed
ASK = "%s"
WHO = {"tenant_id": doc["tenant"], "user_id": doc["user"], "assertion": "", "brain": "langgraph"}
def open_calls(messages):
    \"\"\"The tool calls in a thread that no tool message answers.\"\"\"
    answered = {m.tool_call_id for m in messages if m.type == "tool"}
    return [c for m in messages for c in getattr(m, "tool_calls", None) or [] if c["id"] not in answered]
def next_turn(repair):
    \"\"\"The cut-off thread copied into a new saver, repaired or not, then one more question, as /v1/chat sends it.\"\"\"
    brain = brains.LangGraphBrain(InMemorySaver(), llm=rp.scripted([]))
    rp.copy_thread(brain.graph, doc["thread_id"], doc["checkpoints"])
    cfg = {"configurable": {"thread_id": doc["thread_id"]}}
    if repair:
        limits.repair_thread(brain.graph, cfg, as_node="agent")
    brain.answer(ASK, config=cfg, context=dict(WHO))
    snap = brain.graph.get_state(cfg)
    print(("repaired by limits.repair_thread, then " if repair else "as it was cut off, then ") + f"the question {ASK!r}:")
    for i, m in enumerate(snap.values["messages"][5:], 6):  # from the cut-off turn's call on
        print(f"  {i:>3}. {tr.describe(m, 96)}")
    left = ", ".join(f"{c['name']} {c['id']}" for c in open_calls(snap.values["messages"])) or "none"
    print(f"  now at step {snap.metadata['step']}; tool calls no tool message answers: {left}")
with rp.offline(list(doc["by_id"].values())):            # make replay OFFLINE=1's guard: a script, the Rs 0 lane, no network
    next_turn(repair=False)
    next_turn(repair=True)""" % ASK

GEMINI_ENV = 'GOOGLE_CLOUD_PROJECT="$PROJECT" RAG_API_URL="$API" DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" \\\n  '
GEMINI_PY = """import logging, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
logging.disable(logging.WARNING)
sys.path[:0] = [".", "services/chat", "commands"]
from langgraph.checkpoint.memory import InMemorySaver
import brains, limits, thread_read as tr, thread_replay as rp
doc = rp.load(rp.FIXTURE)
ASK = "%s"
brain = brains.LangGraphBrain(InMemorySaver())           # Gemini on location global, as the lane builds the brain
rp.copy_thread(brain.graph, doc["thread_id"], doc["checkpoints"])
cfg, meter = {"configurable": {"thread_id": doc["thread_id"]}}, limits.Meter(model=brains.MODEL)
try:
    out = brain.answer(ASK, config=cfg, context={"tenant_id": doc["tenant"], "user_id": doc["user"], "assertion": "",
                                                "brain": "langgraph", "meter": meter})
    print(f"the next turn answered; tools: {', '.join(out['tool_calls']) or 'none'}")
except Exception as exc:                                 # what /v1/chat would answer with a 500
    print(f"the next turn failed: {type(exc).__name__}: {tr.short(str(exc), 240)}")
messages = brain.graph.get_state(cfg).values["messages"]
for i, m in enumerate(messages[5:], 6):                  # from the cut-off turn's call on
    print(f"  {i:>3}. {tr.describe(m, 96)}")
answered = {m.tool_call_id for m in messages if m.type == "tool"}
left = [f"{c['name']} {c['id']}" for m in messages for c in getattr(m, "tool_calls", None) or [] if c["id"] not in answered]
print(f"tool calls no tool message answers: {', '.join(left) or 'none'}")
print(f"{meter.model_calls} model call(s), Rs {meter.spent_inr():.2f} at list price with the searches")""" % ASK

AT_SH = """SID=${SID:-$(make thread EMAIL="$ME" | awk '$1 == "acme" && $2 !~ /^desk~/ {print $2; exit}')}   # step 3's session, in a new shell too
make thread EMAIL="$ME" SESSION="$SID" AT=1 EXPORT="$HOME/lesson68.json\""""

REPLAY_LANE_SH = f'make replay FILE="$HOME/lesson68.json" FORK="{FORK_Q}"'
EDIT_SH = f"""sed -i 's/{CHANGE_FROM}/{CHANGE_TO}/' services/chat/brains.py
grep -c "a follow-up too" services/chat/brains.py         # 0: the clause is gone from your clone, and never was on the lane"""
RESTORE_SH = """git checkout -q -- services/chat/brains.py                # the kit's prompt back
grep -c "a follow-up too" services/chat/brains.py"""

TABLE_PY = """import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from urllib.parse import unquote, urlparse
from google.cloud.sql.connector import Connector
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
def gc(*args):
    \"\"\"One gcloud read in your project, as text.\"\"\"
    return subprocess.run(["gcloud", *args, "--project", os.environ["PROJECT"]], capture_output=True, text=True, check=True).stdout.strip()
def said(m):
    \"\"\"One message in a few words: the tools it asks for, the citations it returned, or its first words.\"\"\"
    calls = [c["name"] for c in getattr(m, "tool_calls", None) or []]
    text = m.content if isinstance(m.content, str) else " ".join(b.get("text", "") for b in m.content if isinstance(b, dict))
    if calls:
        return "asks " + ", ".join(calls)
    if m.type == "tool" and text.startswith("{"):
        return f"{len(json.loads(text).get('citations', []))} citations"
    return " ".join(text.split())[:64]
dsn = urlparse(gc("secrets", "versions", "access", "latest", "--secret", "documind-checkpoint-dsn"))   # the password stays in memory
instance = gc("sql", "instances", "describe", "documind-checkpoint", "--format", "value(connectionName)")
export = json.load(open(os.path.expanduser("~/lesson68.json"), encoding="utf-8"))   # step 6's file
thread = export["thread_id"]
serde = JsonPlusSerializer(allowed_msgpack_modules=None)            # strict, as thread_read.py builds it
with Connector() as connector:
    db = connector.connect(instance, "pg8000", user=dsn.username, password=unquote(dsn.password), db=dsn.path.lstrip("/"))
    db.autocommit = True
    cur = db.cursor()
    cur.execute("SET default_transaction_read_only = on", ())       # as make thread does: nothing below can write
    def q(sql, *args):
        \"\"\"One read on the read-only session; pg8000 takes a tuple of arguments, empty or not.\"\"\"
        cur.execute(sql, args)
        return cur.fetchall()
    (n,) = q("SELECT count(*) FROM checkpoints WHERE thread_id = %s AND checkpoint_ns = ''", thread)[0]
    print(f"session {export['session']}: {n} checkpoints on the lane; step 6's export holds {len(export['checkpoints'])}")
    (version,) = q("SELECT checkpoint->'channel_versions'->>'messages' FROM checkpoints WHERE thread_id = %s "
                   "AND checkpoint_ns = '' ORDER BY checkpoint_id DESC LIMIT 1", thread)[0]
    typ, blob = q("SELECT type, blob FROM checkpoint_blobs WHERE thread_id = %s AND checkpoint_ns = '' "
                  "AND channel = 'messages' AND version = %s", thread, version)[0]
    messages = serde.loads_typed((typ, bytes(blob)))
    print(f"the newest checkpoint names messages version {int(version.split('.')[0])}: a {typ} blob of {len(blob):,} bytes, decoded:")
    for m in messages:
        print(f"   {type(m).__name__:12} {said(m)}")
    db.close()"""

CELLS = {
    "ui": 'echo "open https://documind-ui-$NUMBER.$REGION.run.app and sign in as $ME"',
    "threads": THREADS_SH,
    "replay": "make replay OFFLINE=1",
    "match": "make replay OFFLINE=1 AT=0",
    "next": heredoc(NEXT_PY, python=GV_PY),
    "gemini": heredoc(GEMINI_PY, prefix=GEMINI_ENV, python=GV_PY),
    "at": AT_SH,
    "replay_lane": REPLAY_LANE_SH,
    "edit": EDIT_SH,
    "change": REPLAY_LANE_SH,
    "restore": RESTORE_SH,
    "table": heredoc(TABLE_PY, python=GV_PY),
}
assert all(not v.endswith("\\") for v in CELLS.values())

T = Path(tempfile.mkdtemp(prefix="lesson68-"))
HOME = T / "home"
HOME.mkdir()
ENV = {k: v for k, v in os.environ.items() if k not in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT",
                                                        "DOCUMIND_PROFILE", "CHAT_MODEL", "RAG_API_URL", "DOCUMIND_IMPERSONATE_SA")}
ENV.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "REGION": "asia-south1",
            "HOME": str(HOME), "USERPROFILE": str(HOME), "CLOUDSDK_CONFIG": str(T / "gcloud"), "APPDATA": str(T / "appdata")})


def run(argv: list, stdin: str = "", env: dict | None = None, cwd: Path = KIT) -> str:
    """A command as the page runs it, from the kit's root; it must succeed and print nothing to stderr."""
    r = subprocess.run(argv, input=stdin, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (argv[:3], r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout.rstrip("\n")


def cell(body: str, prelude: str = "", env: dict | None = None) -> str:
    """A page cell's Python, run from the kit's root with the build's own interpreter (the chat image's pins)."""
    return run([sys.executable, "-"], stdin=prelude + body, env=env)


# ---- step 4: make replay OFFLINE=1 and AT=0, the kit's own script (memory.mk runs it with --offline and --at="0")
OUT = {"ui": f"open https://documind-ui-NUMBER.asia-south1.run.app and sign in as {ME}"}
OUT["replay"] = run([sys.executable, RP, "--offline"])
OUT["match"] = run([sys.executable, RP, "--offline", "--at=0"])
R4, M4 = OUT["replay"], OUT["match"]
assert R4.startswith(f"thread {DOC['thread_id']}\n  from {FX}: {N_CK} checkpoints, steps -1 to {CUT_STEP}, 2 turns"), R4[:300]
assert f"1. the copy: {N_CK} checkpoints in a local InMemorySaver, one update_state() each; every step's number, next and messages are the file's" in R4
assert f"2. replay from step {CUT_STEP} (next tools)" in R4 and f"step {CUT_STEP} is where the recorded turn stopped: the model had asked retrieve(" in R4
assert f"nothing was recorded after step {CUT_STEP}: the replay finished the turn: 2 messages, 1 model call" in R4, R4
RESUMED = re.findall(r"^     \+ (.*)$", R4.split("\n3. fork")[0], re.M)
assert [r.split()[0] for r in RESUMED] == ["tool", "ai"], RESUMED
FORK_FROM = int(re.search(r"^3\. fork from step (-?\d+), the turn's input", R4, re.M).group(1))
HIST_N, HIST_BRANCHES = map(int, re.search(r"^4\. graph\.get_state_history\(thread\): (\d+) checkpoints, in (\d+) branches$", R4, re.M).groups())
assert FORK_FROM == TURN_STARTS[1] and (HIST_N, HIST_BRANCHES) == (14, 2), (FORK_FROM, HIST_N, HIST_BRANCHES)
RCALLS = tuple(map(int, re.search(r"Model calls: the replay (\d+), the fork (\d+); Rs 0 \(a script, not a model\)", R4).groups()))
assert RCALLS == (1, 2) and R4.rstrip().endswith("Rs 0 (a script, not a model)") and "only the local copy was written; the lane never is." in R4
MATCH = re.search(r"the replay matches the recorded turn: the same steps \(([^)]*)\), the same sources \((\d+) citations\), the same answer", M4)
assert MATCH and MATCH.group(1) == "ai asks retrieve, tool, ai" and "2. replay from step 0 (next agent)" in M4, M4
MATCH_CITES = int(MATCH.group(2))

# ---- step 5: the next question on the cut-off thread, offline, as the page's cell runs it
OUT["next"] = cell(NEXT_PY)
N5 = OUT["next"]
STEPS5 = [int(s) for s in re.findall(r"now at step (\d+);", N5)]
OPEN5 = re.findall(r"tool calls no tool message answers: (.*)$", N5, re.M)
assert OPEN5 == [f"retrieve {CUT_CALL_ID}", "none"], OPEN5
assert N5.startswith(f"as it was cut off, then the question {ASK!r}:\n    6. ai     asks retrieve(query={rp.SECOND!r})\n    7. human  {ASK}"), N5[:400]
assert "repaired by limits.repair_thread, then" in N5 and 'tool   retrieve: {"error": "the turn stopped before this call ran"}' in N5
assert f"ai     {limits.STOP_ANSWER[:40]}" in N5

# ---- step 7's Change-it: the edit and the restore, on a copy of brains.py (sed's s/// is a plain replace here: no
# character in either text is special to sed), and the line count grep -c prints
edited = src[BR].replace(CHANGE_FROM, CHANGE_TO, 1)
compile(edited, BR, "exec")
OUT["edit"] = str(sum("a follow-up too" in line for line in edited.splitlines()))
OUT["restore"] = str(sum("a follow-up too" in line for line in src[BR].splitlines()))
assert (OUT["edit"], OUT["restore"]) == ("0", "1")
assert re.search(r'" Search for every document question, and cite each passage you use as \[n\],"', edited)


# ------------------------------------------------------------------ the Level 0 panel: the fixture, and four ways on from its cut
MSGS, MIDX = [], {}
WHO = {"tenant_id": DOC["tenant"], "user_id": DOC["user"], "assertion": "", "brain": "langgraph"}
CFG_T = {"configurable": {"thread_id": DOC["thread_id"]}}


def mref(m) -> int:
    """The panel's index of one message: each kind-and-words pair is stored once."""
    key = (m.type, tr.describe(m, 96)[7:])
    if key not in MIDX:
        MIDX[key] = len(MSGS)
        MSGS.append(list(key))
    return MIDX[key]


def view(step, source, nxt, parent_step, messages, inp) -> dict:
    """One checkpoint as the panel shows it."""
    return {"step": step, "src": source, "next": list(nxt), "from": parent_step, "m": [mref(m) for m in messages],
            "inp": [mref(m) for m in inp], "ids": [m.id for m in messages]}


def branch(saver, ids: set, hist: list) -> list:
    """The checkpoints of `hist` (oldest first) whose ids are in `ids`, with each one's pending input."""
    step_of = {h.config["configurable"]["checkpoint_id"]: h.metadata.get("step") for h in hist}
    out = []
    for h in hist:
        if h.config["configurable"]["checkpoint_id"] not in ids:
            continue
        start = saver.get_tuple(h.config).checkpoint["channel_values"].get("__start__")
        inp = list(start.get("messages") or []) if tuple(h.next) == ("__start__",) and isinstance(start, dict) else []
        parent = (h.parent_config or {}).get("configurable", {}).get("checkpoint_id")
        out.append(view(h.metadata.get("step"), h.metadata.get("source"), h.next, step_of.get(parent), h.values.get("messages", []), inp))
    return out


step_by_id = {cp["checkpoint_id"]: cp["step"] for cp in CHAIN}
PANEL_CHAIN = [view(cp["step"], cp["source"], cp["next"], step_by_id.get(cp["parent_checkpoint_id"]), cp["messages"], cp["input"])
               for cp in CHAIN]

# resume and fork: the kit's own replay(), offline, from the cut, with the panel's question as the fork's
saver_rf = InMemorySaver()
with contextlib.redirect_stdout(io.StringIO()) as said_rf:
    res = rp.replay(DOC, offline_mode=True, fork=ASK, saver=saver_rf)
W_RESUME = branch(saver_rf, res["replay_ids"], res["history"])
W_FORK = branch(saver_rf, res["fork_ids"], res["history"])
assert "2. replay from step 6 (next tools)" in said_rf.getvalue()


def next_turn(repair: bool):
    """Step 5's cell, for the panel: the cut-off thread copied, repaired or not, then ASK as /v1/chat sends it."""
    saver = InMemorySaver()
    with rp.offline(list(DOC["by_id"].values())):
        brain = brains.LangGraphBrain(saver, llm=rp.scripted([]))
        rp.copy_thread(brain.graph, DOC["thread_id"], CHAIN)
        copied = {t.config["configurable"]["checkpoint_id"] for t in saver.list(CFG_T)}
        if repair:
            limits.repair_thread(brain.graph, CFG_T, as_node="agent")
        brain.answer(ASK, config=CFG_T, context=dict(WHO))
        hist = list(brain.graph.get_state_history(CFG_T))[::-1]
    return branch(saver, {h.config["configurable"]["checkpoint_id"] for h in hist} - copied, hist), hist[-1].values["messages"]


W_ASK, ASK_MSGS = next_turn(False)
W_REPAIR, REPAIR_MSGS = next_turn(True)


def open_ids(messages) -> list:
    """The ids of the tool calls no tool message answers."""
    answered = {m.tool_call_id for m in messages if m.type == "tool"}
    return [c["id"] for m in messages for c in getattr(m, "tool_calls", None) or [] if c["id"] not in answered]


# each way, held to the kit's own runs above: step 4's output, step 5's output, and LangGraph's rules
assert [(c["step"], c["src"], c["next"]) for c in W_RESUME] == [(7, "loop", ["agent"]), (8, "loop", [])], W_RESUME
assert [MSGS[i][0] + " " + MSGS[i][1] for i in W_RESUME[-1]["m"][-2:]] == [" ".join(r.split(None, 1)) for r in RESUMED]
assert W_ASK[0]["src"] == "input" and [MSGS[i][1] for i in W_ASK[0]["inp"]] == [ASK] and W_ASK[0]["from"] == CUT_STEP
assert [c["step"] for c in W_ASK] == list(range(CUT_STEP + 1, STEPS5[0] + 1)) and W_ASK[-1]["next"] == []
assert open_ids(ASK_MSGS) == [CUT_CALL_ID] and open_ids(REPAIR_MSGS) == []
assert (W_REPAIR[0]["src"], W_REPAIR[0]["next"], W_REPAIR[0]["from"]) == ("update", [], CUT_STEP) and W_REPAIR[-1]["step"] == STEPS5[1]
assert [f"{MSGS[i][0]:6} {MSGS[i][1]}" for i in W_ASK[-1]["m"][5:]] == re.findall(r"^\s+\d+\. (.*)$", N5.split("repaired by")[0], re.M)
assert (W_FORK[0]["src"], W_FORK[0]["from"], W_FORK[-1]["next"]) == ("update", FORK_FROM, []) and CUT_CALL.id not in W_FORK[-1]["ids"]
assert [MSGS[i][1] for i in W_FORK[0]["m"]][-1] == ASK


def say(c: dict, cut: bool = False, after_cut: bool = False) -> str:
    """What one checkpoint means, from its source, its next and its newest message."""
    last = MSGS[c["m"][-1]] if c["m"] else None
    if c["inp"]:
        text = "A question arrived as input. It waits there, outside the messages, until the next step applies it."
        if after_cut:
            text += f" The search step {CUT_STEP} was waiting for is dropped here: new input discards a checkpoint's unfinished tasks."
        return text
    if c["src"] == "update" and not c["next"]:
        return ("repair_thread() wrote these as the agent node: an error result for the open call, then the stop answer. "
                "Nothing is due: the turn is closed.")
    if c["src"] == "update" and c["next"] == ["agent"]:
        return (f"update_state() wrote the fork's question here, as the __start__ node, on a copy of step {c['from']}. "
                "The agent node is due: the model has not been called.")
    if c["next"] == ["agent"] and last[0] == "human":
        return "The question is in the messages. The agent node is due: the model has not been called yet."
    if c["next"] == ["tools"]:
        return ("The model asked for retrieve. The tools node is due: the search has not run."
                + (" This is where the stream was closed: the turn's last checkpoint." if cut else ""))
    if c["next"] == ["agent"] and last[0] == "tool":
        return "The search's result is in the messages. The agent node is due: the model reads it next."
    if not c["next"] and last[0] == "ai":
        return "The model answered. Nothing is due: the turn has ended."
    raise AssertionError(c)


for k, c in enumerate(PANEL_CHAIN):
    c["say"] = say(c, cut=k == len(PANEL_CHAIN) - 1)
for way in (W_RESUME, W_ASK, W_REPAIR, W_FORK):
    for k, c in enumerate(way):
        c["say"] = say(c, after_cut=way is W_ASK and k == 0)
for c in PANEL_CHAIN + W_RESUME + W_ASK + W_REPAIR + W_FORK:
    del c["ids"]

WAYS = {
    "resume": {"label": f"resume: graph.invoke(None) at step {CUT_STEP}", "cps": W_RESUME,
               "say": (f"LangGraph ran only what step {CUT_STEP} said was due: the tools node, then the agent node. The turn finished "
                       f"with {RCALLS[0]} model call, and nothing before step {CUT_STEP} ran again. Step 4 does this in your shell.")},
    "ask": {"label": "a new question, as /v1/chat sends one", "cps": W_ASK,
            "say": (f"New input: LangGraph discarded the search step {CUT_STEP} was waiting for. The new question was answered, and "
                    f"the model's call at message 6 never was: {len(open_ids(ASK_MSGS))} call left open, which every later turn "
                    "sends to the model again. Step 5 does this in your shell.")},
    "repair": {"label": "repair_thread(), then the new question", "cps": W_REPAIR,
               "say": ("The open call got an error result and the turn a stop answer, so nothing was left due. The question "
                       "then started on a whole thread, with no call left open. Step 5 does this too.")},
    "fork": {"label": f"fork: the new question from step {FORK_FROM}", "cps": W_FORK,
             "say": (f"update_state() on step {FORK_FROM}, the second turn's input, then graph.invoke(None): a new branch beside "
                     f"the old one. The cut-off question and its open call stay on the old branch, untouched.")},
}
PANEL = {"msgs": MSGS, "chain": PANEL_CHAIN, "cut": len(PANEL_CHAIN) - 1, "order": ["resume", "ask", "repair", "fork"],
         "ways": WAYS, "none": "nothing yet: stay at the cut",
         "cutSay": (f"Step {CUT_STEP} is the cut: the model's call is saved and the search never ran. Choose what happens next, "
                    "then step through the checkpoints it adds, dashed.")}
PANEL_JSON = json.dumps(PANEL, ensure_ascii=True, separators=(",", ":"))
assert len(PANEL_JSON) < 20000, len(PANEL_JSON)


# ------------------------------------------------------------------ the lane cells, checked against stand-ins
# A stand-in of your UI conversation: two turns of the kit's LangGraph brain with the offline script, under your email
# and a 12-hex session, turned into the rows PostgresSaver stores (the kit test's pg_rows) and served to thread_read
# by the kit test's fake gcloud and connector, beside a newer Desk thread the awk filter must skip.
saver_ui = InMemorySaver()
TID = f"acme:{ME}:{SID}"
with rp.offline([]):
    ui_brain = brains.LangGraphBrain(saver_ui, llm=rp.scripted([]))
    for q in (Q1, Q2):
        ui_brain.answer(q, config={"configurable": {"thread_id": TID}}, context={**WHO, "user_id": ME})
UI_ROWS = tt.pg_rows(saver_ui, TID)
DESK_TID = f"acme:{ME}:desk~gc-0a1b"
DESK_ROWS = ([(f"dk{k:03d}", f"dk{k - 1:03d}" if k else None, json.dumps({"ts": f"2999-01-01T00:0{k}:00+00:00"}),
               json.dumps({"source": "input" if k == 0 else "loop", "step": k - 1, "parents": {}})) for k in range(3)], [], [])


def read(*argv) -> str:
    """make thread on the stand-in lane: thread_read.main with the kit test's fakes."""
    out, err = io.StringIO(), io.StringIO()
    db = tt.Database({TID: UI_ROWS, DESK_TID: DESK_ROWS})
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = tr.main(["--project", PROJ, *argv], gcloud=tt.gcloud, connector=tt.connector(db))
    assert code == 0 and not err.getvalue(), (argv, err.getvalue())
    assert db.statements[0] == (tr.READ_ONLY, (), True) and db.closed
    return out.getvalue()


def awk_sid(listing: str) -> str:
    """The cell's awk: the first row whose tenant is acme and whose session is not a Desk thread's."""
    return next(f[1] for f in (line.split() for line in listing.splitlines()) if len(f) > 1 and f[0] == "acme" and not f[1].startswith("desk~"))


SI = {"list": read("--email", ME)}
assert SI["list"].index("desk~gc-0a1b") < SI["list"].index(SID) and awk_sid(SI["list"]) == SID, SI["list"]
SI["thread"] = read("--email", ME, "--session", SID)
assert f"thread {TID}: 10 checkpoints, 2 turns" in SI["thread"], SI["thread"]
SI_ROWS = re.findall(r"^\s+(-?\d+)  \d\d:\d\d:\d\d  (\w+)\s+(\w+)\s+(\S+)\s+(\d+)  ", SI["thread"], re.M)
assert [(int(s), src_, nx) for s, src_, _, nx, _ in SI_ROWS] == [(-1, "input", "__start__"), (0, "loop", "agent"), (1, "loop", "tools"),
                                                                 (2, "loop", "agent"), (3, "loop", "-"), (4, "input", "__start__"),
                                                                 (5, "loop", "agent"), (6, "loop", "tools"), (7, "loop", "agent"), (8, "loop", "-")]
EXPORT = HOME / "lesson68.json"
SI["at"] = read("--email", ME, "--session", SID, "--at=1", "--export", str(EXPORT))
assert "step 1: checkpoint " in SI["at"] and "source loop, brain langgraph, next tools" in SI["at"] and "the messages saved at step 1 (2):" in SI["at"]
assert f"wrote {EXPORT}: 10 checkpoints and 8 messages." in SI["at"]
# make replay FILE= on that export, offline here (the page's run is Gemini's): the flags, the default AT and the history
out_rp = io.StringIO()
with contextlib.redirect_stdout(out_rp):
    assert rp.main(["--offline", "--file", str(EXPORT), "--fork", FORK_Q]) == 0
SI["replay"] = out_rp.getvalue()
assert "2. replay from step 5 (next agent)" in SI["replay"] and f"the fork's question: {FORK_Q!r}" in SI["replay"], SI["replay"]
assert "the replay matches the recorded turn: the same steps (ai asks retrieve, tool, ai)" in SI["replay"] and "in 3 branches" in SI["replay"]
# step 5's Gemini cell: the same code, with a scripted model and the Rs 0 lane standing in, and no network
GEMINI_PRELUDE = ("import sys\nsys.path[:0] = ['.', 'services/chat', 'commands']\nimport thread_replay as rp\nimport brains\n"
                  "_offline = rp.offline(list(rp.load(rp.FIXTURE)['by_id'].values()))   # held: a dropped guard closes, and puts it all back\n"
                  "_offline.__enter__()\nbrains.build_llm = lambda: rp.scripted([])\n")
SI["gemini"] = cell(GEMINI_PY, GEMINI_PRELUDE, env={"GOOGLE_CLOUD_PROJECT": PROJ, "RAG_API_URL": "https://documind-api-NUMBER.asia-south1.run.app",
                                                   "DOCUMIND_IMPERSONATE_SA": UI_SA})
assert SI["gemini"].startswith("the next turn answered; tools: retrieve\n    6. ai     asks retrieve(") and \
    f"tool calls no tool message answers: retrieve {CUT_CALL_ID}\n2 model call(s), Rs 0.00 at list price with the searches" in SI["gemini"], SI["gemini"]
# step 8's cell: a fake Cloud SQL over the stand-in's rows, a fake gcloud, and step 6's export in a stand-in home
cps_rows, blob_rows, _ = UI_ROWS
TABLE_PRELUDE = ("import base64, json, sys, types\n"
                 f"D = json.loads({json.dumps(json.dumps({'thread': TID, 'cps': [list(r) for r in cps_rows], 'blobs': [[c, v, t, base64.b64encode(b).decode() if b is not None else None] for c, v, t, b in blob_rows]}))})\n"
                 "CPS = D['cps']\nBLOBS = [(c, v, t, base64.b64decode(b) if b is not None else None) for c, v, t, b in D['blobs']]\n"
                 "class Cur:\n"
                 "    def execute(self, sql, args=()):\n"
                 "        len(args)                                   # as pg8000 does: None has no len()\n"
                 "        if sql == 'SET default_transaction_read_only = on': self.rows = None; return\n"
                 "        assert sql.lstrip().upper().startswith('SELECT') and args[0] == D['thread'], (sql, args)\n"
                 "        if sql.startswith('SELECT count(*) FROM checkpoints'): self.rows = [[len(CPS)]]\n"
                 "        elif \"channel_versions'->>'messages'\" in sql: self.rows = [[json.loads(CPS[-1][2])['channel_versions']['messages']]]\n"
                 "        elif sql.startswith('SELECT type, blob FROM checkpoint_blobs'): self.rows = [[t, b] for c, v, t, b in BLOBS if c == 'messages' and v == args[1]]\n"
                 "        else: raise AssertionError(sql)\n"
                 "    def fetchall(self):\n        assert self.rows is not None\n        return self.rows\n"
                 "class Conn:\n    autocommit = False\n    def cursor(self): return Cur()\n    def close(self): pass\n"
                 "class Connector:\n"
                 "    def __enter__(self): return self\n    def __exit__(self, *a): return False\n"
                 "    def connect(self, instance, driver, **kw):\n"
                 "        assert driver == 'pg8000' and kw == {'user': 'chat', 'password': 'PASSWORD', 'db': 'documind'}, kw\n"
                 "        return Conn()\n"
                 "con = types.ModuleType('google.cloud.sql.connector'); con.Connector = Connector\n"
                 "sys.modules['google.cloud.sql'] = types.ModuleType('google.cloud.sql'); sys.modules['google.cloud.sql.connector'] = con\n"
                 "class _Out:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
                 f"def run(cmd, **kw): return _Out('postgresql://chat:PASSWORD@/documind?host=/cloudsql/x' if cmd[1] == 'secrets' else '{PROJ}:asia-south1:documind-checkpoint')\n"
                 "import subprocess as _real   # every other name stays real: the libraries the cell imports use them\n"
                 "fake = types.ModuleType('subprocess'); fake.__dict__.update(_real.__dict__); fake.run = run; sys.modules['subprocess'] = fake\n")
SI["table"] = cell(TABLE_PY, TABLE_PRELUDE)
assert SI["table"].startswith(f"session {SID}: 10 checkpoints on the lane; step 6's export holds 10\n"), SI["table"]
assert "the newest checkpoint names messages version " in SI["table"] and "a msgpack blob of " in SI["table"]
TABLE_KINDS = re.findall(r"^   (\w+Message)\s", SI["table"], re.M)
assert TABLE_KINDS == ["HumanMessage", "AIMessage", "ToolMessage", "AIMessage"] * 2, TABLE_KINDS
assert "PASSWORD" not in "".join(SI.values())
shutil.rmtree(T, ignore_errors=True)
logging.disable(logging.NOTSET)

# ------------------------------------------------------------------ the author's run, recorded
RECORDED = {"threads": "ui_thread.txt", "gemini": "next_turn.txt", "at": "thread_at.txt", "replay_lane": "replay_fork.txt",
            "change": "changeit.txt", "table": "table_read.txt"}
REC = {k: pb.recorded(LESSON, name) for k, name in RECORDED.items()}
waiting = lambda text: text.startswith("[awaiting the author's run")  # noqa: E731
SHAPES = {   # what each recording must hold, from the kit's own printing, so a run of the wrong command is refused
    "threads": ["threads of ", "the latest written first:", "checkpoints, 2 turns", "the newest message"],
    "gemini": ["tool calls no tool message answers:", "at list price with the searches"],
    "at": ["step 1: checkpoint ", "next tools", "the messages saved at step 1", "wrote "],
    "replay_lane": ["1. the copy:", "2. replay from step", "3. fork from step", "4. graph.get_state_history(thread):", "the lane never is"],
    "change": ["2. replay from step", "the lane never is"],
    "table": ["checkpoints on the lane; step 6's export holds", "the newest checkpoint names messages version"],
}
for k, text in REC.items():
    if not waiting(text):
        missing = [s for s in SHAPES[k] if s not in text]
        assert not missing, f"data/{RECORDED[k]} lacks {missing}: record it again with the command RUN_LIST.md gives"
        assert "documind-ai-" not in text.replace(PROJ, ""), f"data/{RECORDED[k]}: replace the project id with {PROJ}"

# ------------------------------------------------------------------ what the runs cost: shared/prices.py at the course's typical answer
TYPICAL = (2000, 300)            # the course's typical answer (lessons 4.3, 4.4 and 11.6): 2,000 tokens in, 300 out
CALL_RS = prices.inr(prices.usd(brains.MODEL, *TYPICAL))
TURN_RS = 3 * CALL_RS            # an agent turn with one search: the model's call, rag-api's grounded answer, the model's answer
COSTS = [  # (step, what is billed, rupees or None for free, the note)
    ("3, two questions in the UI", "two agent turns, each a model call, a search and an answer", 2 * TURN_RS, "estimated; the UI's caption prints each turn's own"),
    ("3 and 6, make thread", "reads, in a session that cannot write", None, "free"),
    ("4 and 5, offline", "a script and the Rs 0 lane, on your machine", None, "Rs 0"),
    ("5, the next question with Gemini", "one agent turn at most", TURN_RS, "at most; nothing if Gemini refuses the history"),
    ("7, the replay and the fork", "two agent turns", 2 * TURN_RS, "estimated; the replay prints its own"),
    ("7, Change it", "two agent turns, or less if the model does not search", 2 * TURN_RS, "at most; the replay prints its own"),
    ("8, the table", "one short connection, reading only", None, "free"),
]
TOTAL_RS = sum(c[2] for c in COSTS if c[2])
assert 7 < TOTAL_RS < 10, TOTAL_RS                       # the plan's Rs 7-10 for this lesson's runs
cost_rows = "\n".join(f'<tr><td>{html.escape(s)}</td><td data-label="Costs">{html.escape(w)}</td><td data-label="On your lane">'
                      + (f"about Rs {rs:.2f}, {html.escape(n)}" if rs else html.escape(n)) + "</td></tr>" for s, w, rs, n in COSTS)


# ------------------------------------------------------------------ the windows
def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "ui": "run in the operator shell (the address of your UI)",
    "threads": "run in the operator shell, in the kit (your threads, then the newest decoded; reads only)",
    "replay": "run in the operator shell, in the kit (the kit's cut-off thread, resumed on your machine; no network, Rs 0)",
    "match": "run in the operator shell, in the kit (a finished turn replayed from step 0; no network, Rs 0)",
    "next": "run in the operator shell, in the kit (the next question on the cut-off thread, as it is and repaired; no network, Rs 0)",
    "gemini": "run in the operator shell, in the kit (the same question with Gemini and your rag-api; one turn at most)",
    "at": "run in the operator shell, in the kit (one step read back, and the thread written to a file; reads only)",
    "replay_lane": "run in the operator shell, in the kit (your thread replayed and forked on your machine; a few model calls)",
    "edit": "run in the operator shell, in the kit (edits one line of your clone's brains.py)",
    "change": "run in the operator shell, in the kit (the same replay, with the edited prompt)",
    "restore": "run in the operator shell, in the kit (the kit's prompt back)",
    "table": "run in the operator shell, in the kit (your thread's rows, read directly; reads only)",
}
LANE = "(the author's lane: your session, times, words and rupees are yours)"
OUT_LABELS = {
    "ui": "",
    "threads": LANE,
    "replay": "(the kit's own output, produced when this page was built; yours matches it line for line)",
    "match": "(the kit's own output, produced when this page was built)",
    "next": "(this cell run on the kit's brains.py, limits.py and thread_replay.py when this page was built)",
    "gemini": "(the author's lane: Gemini's answer, or its error, is the point; the call ids are the fixture's)",
    "at": LANE,
    "replay_lane": LANE,
    "edit": "(the cell's own output, produced when this page was built on a copy of brains.py)",
    "change": LANE,
    "restore": "(the kit's own output after the checkout, produced when this page was built)",
    "table": LANE,
}
SHOWN = {**OUT, **REC}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], SHOWN[k]) for k in CELLS})

STATS = {
    "Q1": html.escape(Q1), "Q2": html.escape(Q2), "ASK": html.escape(ASK), "FORK_Q": html.escape(FORK_Q),
    "N_CK": str(N_CK), "CUT_STEP": str(CUT_STEP), "FORK_FROM": str(FORK_FROM), "HIST_N": str(HIST_N), "HIST_BRANCHES": str(HIST_BRANCHES),
    "MATCH_CITES": str(MATCH_CITES), "LG_VER": LG_VER, "LG_LINE": str(LG_LINE), "PG_VER": PG_VER, "CUT_CALL_ID": CUT_CALL_ID,
    "STEP5_ASK": str(STEPS5[0]), "STEP5_REPAIR": str(STEPS5[1]), "N_FIRST": str(N_FIRST),
    "CALL_RS": f"{CALL_RS:.2f}", "TURN_RS": f"{TURN_RS:.2f}", "TOTAL_RS": f"{TOTAL_RS:.2f}", "COST_ROWS": cost_rows,
    "MODEL": brains.MODEL, "NEXT_NAME": html.escape(NEXT_NAME), "STOP_START": html.escape(limits.STOP_ANSWER.split(",")[0]),
}

if os.environ.get("CELLS_ONLY"):
    for k, v in {**OUT, **{f"standin_{k}": v for k, v in SI.items()}}.items():
        print(f"===== {k}\n{v}")
    print(STATS)
    sys.exit(0)

# ------------------------------------------------------------------ the panel's script
UI_JS = r"""var root = document.getElementById('cr'); if (!root) return;
  var D = __PANEL__, $ = function(id){ return document.getElementById(id); }, at = D.cut, way = 'none';
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
  function line(){ return way === 'none' ? D.chain : D.chain.concat(D.ways[way].cps); }
  function words(i){ var m = D.msgs[i]; return m[0] + '  ' + m[1]; }
  function render(){
    var L = line(), c = L[at], box = $('cr-chain'), out = $('cr-out'), ol = $('cr-msgs');
    box.textContent = '';
    L.forEach(function(p, i){
      var added = i >= D.chain.length, b = el('button', 'cr-chip' + (i === D.cut ? ' cut' : '') + (added ? ' new' : ''), String(p.step));
      b.type = 'button'; b.setAttribute('aria-pressed', String(i === at));
      b.setAttribute('aria-label', 'step ' + p.step + ', ' + p.src + (added ? ', added by the way on' : ''));
      b.addEventListener('click', function(){ at = i; render(); });
      box.appendChild(b); });
    out.textContent = '';
    [['Step', String(c.step)], ['Source', c.src], ['next', c.next.length ? c.next.join(', ') : '- (nothing due)'],
     ['Follows', c.from === null ? '- (the thread\'s first)' : 'step ' + c.from], ['Messages', String(c.m.length)], ['What it says', c.say]
    ].forEach(function(r){ out.appendChild(el('b', '', r[0])); out.appendChild(el('span', '', r[1])); });
    ol.textContent = '';
    c.m.forEach(function(i, k){ ol.appendChild(el('li', k === c.m.length - 1 && !c.inp.length ? 'newest' : '', words(i))); });
    $('cr-wait').textContent = c.inp.length ? 'Waiting as input, not yet a message: ' + c.inp.map(words).join('; ') : '';
    $('cr-wait').hidden = !c.inp.length;
    $('cr-prev').disabled = at === 0; $('cr-next').disabled = at === L.length - 1;
    $('cr-say').textContent = way === 'none' ? D.cutSay : D.ways[way].say; }
  var sel = $('cr-way');
  [['none', D.none]].concat(D.order.map(function(k){ return [k, D.ways[k].label]; })).forEach(function(o){
    var opt = el('option', '', o[1]); opt.value = o[0]; sel.appendChild(opt); });
  sel.addEventListener('change', function(){ way = sel.value; at = way === 'none' ? D.cut : D.chain.length; render(); });
  $('cr-prev').addEventListener('click', function(){ if (at > 0) { at--; render(); } });
  $('cr-next').addEventListener('click', function(){ if (at < line().length - 1) { at++; render(); } });
  render();""".replace("__PANEL__", PANEL_JSON)

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS
# the script parses (node --check) and, run against a minimal DOM, renders every checkpoint of every way without an error
node_js = Path(tempfile.mkdtemp(prefix="lesson68-js-")) / "panel.js"
node_js.write_text(
    "var made = {}; function E(tag){ return {tagName: tag, children: [], className: '', textContent: '', disabled: false, value: '', "
    "attrs: {}, listeners: {}, setAttribute: function(k, v){ this.attrs[k] = v; }, appendChild: function(c){ this.children.push(c); }, "
    "addEventListener: function(k, f){ this.listeners[k] = f; }}; }\n"
    "var document = {getElementById: function(id){ return made[id] = made[id] || E(id); }, createElement: E};\n"
    "(function(){\n" + squeeze(UI_JS) + "\n})();\n"
    "var seen = 0, ways = ['none'].concat(" + json.dumps(PANEL["order"]) + ");\n"
    "ways.forEach(function(w){ made['cr-way'].value = w; made['cr-way'].listeners.change();\n"
    "  while (!made['cr-next'].disabled) { made['cr-next'].listeners.click(); seen++; }\n"
    "  while (!made['cr-prev'].disabled) { made['cr-prev'].listeners.click(); seen++; } });\n"
    "console.log(seen, made['cr-chain'].children.length, made['cr-say'].textContent.length > 0);\n", encoding="utf-8", newline="\n")
nd = subprocess.run(["node", str(node_js)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(node_js.parent, ignore_errors=True)
assert nd.returncode == 0, nd.stderr[-800:]
seen, chips, said_ok = nd.stdout.split()
assert int(seen) > 4 * N_CK and said_ok == "true", nd.stdout


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: the fixture's {N_CK} checkpoints, cut at step {CUT_STEP} | make replay OFFLINE=1 resumed it ({RCALLS[0]} model call) and AT=0 "
      f"matched ({MATCH_CITES} sources) | step 5: the open call left by a new question, closed by repair_thread | langgraph {LG_VER} "
      f"_loop.py:{LG_LINE} | the panel: four ways on, each the kit's own run, rendered in node | lane cells checked against stand-ins | "
      f"runs: about Rs {TOTAL_RS:.2f} at {TYPICAL[0]:,} in / {TYPICAL[1]} out a call")
