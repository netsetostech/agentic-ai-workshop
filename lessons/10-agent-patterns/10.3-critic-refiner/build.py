"""Build lesson 10.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Check, retry or choose. The agent bench (commands/agent_patterns.py) puts one critic to work three ways on the task
set's calculator rows. Re-roll: the loop's first k runs, pass@k, the ceiling a perfect chooser reaches. Choose: best-of-k,
the run evals/agent_eval.py's best_of() picks with the figure check. Retry: verify, the loop, then figure_check(), then
after a failed check one reflect call whose note goes into the next attempt's system prompt, at most MAX_ATTEMPTS
attempts. The critic is code: figure_check() reads every figure (desk_calc.unsupported()), every [n] and the stop.

Offline, at build time, with the chat image's pins (build with the chat venv's python), no credential and no network:
agent_turn.py --offline --pattern verify as the page's cells run it (as the prompt stands, --invent and --launder); the
Change-it, the line marked THE QUESTION edited as the page's sed edits it in a scratch repository and run in memory (the
file on disk is never touched), with git's diff --stat for it and for the lane step's deleted prompt rule; the figure
check and the reflect call's input through the page's two standard-library cells; agent_eval.py --check, then --offline
on the calc and trap rows (the loop three runs a row, verify one), saved, replayed side by side with --best-of 3, and
read back by the page's own cell. The Level 0 panel is built from those saved runs with the kit's own scorer and
chooser, and their calls price the lane's runs for RUN_LIST.md. The live outputs come from the author's lane:
pb.recorded() reads them from data/ (RUN_LIST.md says how each is recorded).

    python pagekit/build.py 10.3        (the chat venv; a few minutes, most of them the offline evals)
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

LESSON = "10.3"
title = ("<title>Lesson 10.3 Check, retry or choose: the critic and refiner pattern - pass@1, re-rolls, best-of-3 and "
         "verify on the same calculator rows | Netsetos</title>\n")
warnings.filterwarnings("ignore")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the Level 0 panel: one row's re-rolls, the run best-of picks, and verify's attempts */
.cc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:8px 12px;margin:4px 0 10px;}
.cc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.cc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;width:100%;}
.cc-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:10px;align-items:start;}
.cc-col{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;min-width:0;overflow-wrap:anywhere;}
.cc-name{font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--teal);}
.cc-how{font-size:12px;line-height:1.45;color:var(--slate);margin:2px 0 6px;}
.cc-c{border-top:1px dashed var(--border);padding:6px 0 4px;font-size:12.5px;line-height:1.5;}
.cc-c.pick{border-top:2px solid var(--teal);}
.cc-h{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--teal-dark);}
.cc-h.code{color:var(--cyan);}
.cc-c p{margin:2px 0;}
.cc-c pre{font-family:var(--mono);font-size:11.5px;line-height:1.45;white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f5f9;border-radius:6px;padding:4px 6px;margin:2px 0;color:var(--slate);}
.cc-c .bad{color:#991b1b;}
.cc-c .good{color:#065f46;}
.cc-c pre.note{background:#fffbeb;color:#78350f;}
.cc-ways{margin:10px 0 0;font-size:12.5px;}
.cc-ways table{width:100%;border-collapse:collapse;}
.cc-ways th,.cc-ways td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--border);vertical-align:top;}
.cc-ways th{font-family:var(--mono);font-size:11px;color:var(--navy);}
.cc-ways caption{text-align:left;font-family:var(--mono);font-size:11px;font-weight:700;color:var(--teal-dark);padding:4px 0;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim kit excerpts
AP, AT, AE, MK, TV, DA, DC = ("commands/agent_patterns.py", "commands/agent_turn.py", "evals/agent_eval.py", "mk/agents.mk",
                              "commands/tests/test_agent_verify.py", "services/chat/desk_agent.py", "shared/desk_calc.py")
EXCERPTS = {
    "unsupported": ("shared/desk_calc.py - unsupported(): every figure in an answer that nothing of the turn writes",
                    block(DC, "def unsupported(", end="# ------")),
    "check": ("commands/agent_patterns.py - figure_check() and said_check(): the critic, and its verdict in words",
              block(AP, "def figure_check(", end="def cut_note(")),
    "prompts": ("commands/agent_patterns.py - MAX_ATTEMPTS and NOTE_CHARS, REFLECTOR and NOTES: the limits, and what the reflect call and a later attempt are told",
                block(AP, "MAX_ATTEMPTS = 3", n=2) + "\n...\n" + block(AP, "REFLECTOR = (", end="CHECK_ROLES = ")),
    "reflect": ("commands/agent_patterns.py - cut_note(), noted(), did_lines() and ask_reflect(): what the reflect call reads, and where its note goes",
                block(AP, "def cut_note(", end="def retry_context(")),
    "verify": ("commands/agent_patterns.py - retry_context() and _verify(): each attempt a turn of its own, the line marked THE QUESTION",
               block(AP, "def retry_context(", end="@dataclass(frozen=True)")),
    "wage": ("commands/tests/test_agent_verify.py - the kit's test that a note's figure is refused as a calculator's argument",
             block(TV, "    def test_a_notes_figure_is_refused_as_an_argument(self):", end="    def test_the_retry_cap(self):")),
    "scripted": ("commands/agent_patterns.py - slips() and reflect_note(): when the offline model slips, and the note it writes",
                 block(AP, "def slips(", end="def scripted_usage(") + "\n...\n" + block(AP, "def reflect_note(", end="def checked_step(")),
    "best": ("evals/agent_eval.py - passes() and best_of(): best-of-k, chosen by the figure check, never the expected figure",
             block(AE, "def passes(", end="def pass_at_k(")),
    "critic": ("evals/agent_eval.py - critic(): the four ways side by side, each with its calls and rupees, then the check's precision",
               block(AE, "def critic(", end="def compared(")),
    "rule": ("services/chat/desk_agent.py - system_prompt(): step 9 takes out its calculator rule, the three lines from \"- Work every figure out\"",
             block(DA, "def system_prompt(", end="class DeskTurnLimits")),
    "at": ("commands/agent_turn.py - --invent and --launder, the offline flags of verify's cells",
           block(AT, '    ap_.add_argument("--invent"', n=5)),
    "mk": ("mk/agents.mk - make agent-eval, whose REPLAY takes several saved files",
           block(MK, "agent-eval: $(if $(or $(OFFLINE),$(CHECK),$(REPLAY),$(COMPARE)),,guard-project)", n=2)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["unsupported"].startswith("def unsupported(") and "A number in words is prose here" in " ".join(E["unsupported"].split())
assert E["unsupported"].rstrip().endswith("+ [d.isoformat() for d in sorted(dates_in(answer) - days)])")
assert "a note, a plan or a critic's remark is never one" in " ".join(E["unsupported"].split())
assert E["check"].startswith("def figure_check(") and 'return "failed: " + "; ".join(why)' in E["check"]
assert 'return {"passed": not flagged and not uncited and not stopped_by,' in E["check"]
assert E["prompts"].startswith("MAX_ATTEMPTS = 3 ") and "NOTE_CHARS = 300 " in E["prompts"] and "NOTES = (" in E["prompts"]
assert E["prompts"].rstrip().endswith('"again.")')
assert "def cut_note(" in E["reflect"] and "def noted(" in E["reflect"] and "def did_lines(" in E["reflect"]
assert 'lines.append("   returned: a figure")' in E["reflect"] and E["reflect"].rstrip().endswith('+ did_lines(steps) + ["", f"The figure check {said_check(check)}"])')
assert E["verify"].startswith("def retry_context(") and E["verify"].rstrip().endswith("return messages")
assert "asked = question  # THE QUESTION: the person's own, which check_args and the figure check read; never a note" in E["verify"]
assert 'reply, _ = _ask(Runtime(context=actx), {"messages": []}, llm, reflector, ask_reflect(**failed), wrappers,' in E["verify"]
assert 'refused["result"]["error"].startswith("refused: monthly_wage = 60000 is a fact about the "' in E["wage"]
assert 'return run == 0' in E["scripted"] and 'zlib.crc32(f"{task[\'id\']}:{run}".encode()) % 5 == 0' in E["scripted"]
assert 'return max(first, key=lambda r: (passes(r), backed(r), -r["run"]))' in E["best"]
assert E["critic"].startswith("def critic(") and E["critic"].rstrip().endswith("return out")
assert "- Work every figure out with a calculator, never yourself." in E["rule"]
assert 'ap_.add_argument("--launder", nargs="?", const="Rs 2,40,000", metavar="FIGURE",' in E["at"]
assert '$(if $(REPLAY),--replay $(foreach f,$(REPLAY),"$(f)"),' in E["mk"]
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
MODEL = da.AGENT_MODEL
RATE_IN, RATE_OUT = prices.PRICES[MODEL]
assert (MODEL, RATE_IN, RATE_OUT, prices.USD_INR) == ("gemini-3.6-flash", 1.50, 7.50, 85)
assert (ap.MAX_ATTEMPTS, ap.NOTE_CHARS, ap.CHECK_ROLES, ap.PLANNED) == (3, 300, ("answer", "reflect"), {})
_v = ap.PATTERNS["verify"]
assert (_v.lessons, _v.checked, _v.text, _v.executor) == ("10.3", True, False, False)
assert [n for n, p in ap.PATTERNS.items() if p.checked] == ["verify"]
assert (limits.MAX_MODEL_CALLS, limits.TURN_BUDGET_INR, limits.TURN_DEADLINE_S) == (12, 5.0, 100.0)
assert da.THINKING_LEVEL == "low" and ap.SCRIPTED_THINKING["low"] == 64 and ap.CHARS_PER_TOKEN == 4
AP_SRC = (KIT / AP).read_text(encoding="utf-8")
AT_SRC = (KIT / AT).read_text(encoding="utf-8")
AE_SRC = (KIT / AE).read_text(encoding="utf-8")
MK_SRC = (KIT / MK).read_text(encoding="utf-8")
DA_SRC = (KIT / DA).read_text(encoding="utf-8")
# the one line the Change-it edits, set once; MAX_ATTEMPTS and NOTE_CHARS set once each, no flag and no make variable
QUESTION_LINE = "asked = question  # THE QUESTION"
assert [ln.strip() for ln in AP_SRC.splitlines() if "THE QUESTION" in ln] == [
    "asked = question  # THE QUESTION: the person's own, which check_args and the figure check read; never a note"]
assert len(re.findall(r"^MAX_ATTEMPTS\s*=", AP_SRC, re.M)) == 1 and len(re.findall(r"^NOTE_CHARS\s*=", AP_SRC, re.M)) == 1
for _flag in ("--attempts", "--max-attempts", "--note-chars", "--reflect-on", "--reflect"):
    assert _flag not in AT_SRC and _flag not in AE_SRC, _flag
assert "ATTEMPTS" not in MK_SRC and "REFLECT" not in MK_SRC
assert ' INVENT="$(INVENT)" LAUNDER="$(LAUNDER)" ' in MK_SRC          # the cells' offline flags, as make variables
for _flag in ("INVENT", "LAUNDER"):
    assert (f'if [ -n "${{{_flag}:-}}" ]; then ARGS+=(--{_flag.lower()}); [ "${_flag}" = 1 ] || ARGS+=("${_flag}"); fi'
            in (KIT / "commands" / "agent-turn.sh").read_text(encoding="utf-8")), _flag
assert "NotesMiddleware" not in AP_SRC and "ReflectAndRetry" not in AP_SRC
# notes live in one turn: verify's store is made fresh by every turn, and nothing reads notes from an earlier one
assert 'kept = ctx["bench_verify"] = {"attempts": [], "notes": [], "shipped": None}' in AP_SRC
# the reflect call binds no tool, and its thinking level is the turn's, as every call's
assert 'ask_reflect(**failed), wrappers,\n                            "reflect")' in AP_SRC
# nothing deployed runs the check or the bench: the Desk and the chat brains answer without either
for _p in list((KIT / "services").rglob("*.py")) + list((KIT / "shared").rglob("*.py")):
    _t = _p.read_text(encoding="utf-8", errors="replace")
    assert "agent_patterns" not in _t and "figure_check" not in _t, _p
    if _p.name != "desk_calc.py":
        assert "unsupported(" not in _t, _p
assert "TOOLS = [retrieve, calculate_processing_cost]" in (KIT / "services" / "chat" / "tools.py").read_text(encoding="utf-8")
FRONT = (KIT / "services" / "frontend" / "chat.py").read_text(encoding="utf-8")
assert "st.session_state.session_id = uuid.uuid4().hex[:12]   # one conversation per browser session" in FRONT
assert "st.caption(f\"brain: {body.get('brain')} · tools: {', '.join(body.get('tool_calls') or []) or 'none'}\"" in FRONT
# the rule the lane step deletes: three lines, each phrase once in the file
RULE_FROM, RULE_TO = "Work every figure out with a calculator", "say which one is missing"
_da_lines = DA_SRC.splitlines()
_i = [k for k, ln in enumerate(_da_lines) if RULE_FROM in ln]
_j = [k for k, ln in enumerate(_da_lines) if RULE_TO in ln]
assert len(_i) == 1 and len(_j) == 1 and _j[0] - _i[0] == 2, (_i, _j)
RULE_TEXT = "".join(re.findall(r'"([^"]*)"', "\n".join(_da_lines[_i[0]:_j[0] + 1])))
assert RULE_TEXT.startswith("- Work every figure out with a calculator, never yourself.") and RULE_TEXT.endswith("say which one is missing.\\n")
RULE_TOKENS = math.ceil(len(RULE_TEXT) / ap.CHARS_PER_TOKEN)
sh_src = (KIT / "commands" / "agent-turn.sh").read_text(encoding="utf-8")
assert 'exec "$VENV/bin/python" "$@"' in sh_src and 'REGION="${REGION:-us-central1}"' in sh_src
assert "Two signals disagree about which desk of a company help desk should take this employee question." in (
    KIT / "services" / "chat" / "desk_router.py").read_text(encoding="utf-8")      # lesson 10.4's arbiter: a choice made by a model
ae_spec = importlib.util.spec_from_file_location("agent_eval_lesson_103", KIT / AE)
ae = importlib.util.module_from_spec(ae_spec)
ae_spec.loader.exec_module(ae)
SLICE = "calc,trap"
TASKS = ap.tasks()
ROWS = {r["id"]: r for r in ae.select(TASKS, SLICE)}
N_CALC = sum(r["kind"] == "calc" for r in ROWS.values())
assert len(ROWS) == 12 and N_CALC == 11 and [r["id"] for r in ROWS.values() if r["kind"] == "trap"] == ["trap-encash-cap"]
assert {r["tenant"] for r in ROWS.values()} == {"acme", "zeta"}             # the setup line classes both tenants' rows
GRATUITY = ROWS["calc-gratuity-7y8m"]
GRC, TRAP = ROWS["calc-grc-threshold"], ROWS["trap-encash-cap"]
assert GRATUITY["question"] == "I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?"
assert at.DEFAULT_ROW == GRATUITY["id"] and GRATUITY["expected"] == 240000
assert (GRC["unit"], GRC["expected"], TRAP["expected"], TRAP["unit"]) == ("yes/no", True, 45, "days")
RUNS = 3
# which of the loop's first three runs the offline script slips on: the page's prose names these rows
SLIPS = {rid: [r for r in range(RUNS) if ap.slips(row, r)] for rid, row in ROWS.items()}
assert {k: v for k, v in SLIPS.items() if v} == {"calc-gratuity-7y8m": [0], "calc-gratuity-7y6m": [2], "calc-notice-e3": [2],
                                                 "calc-wages-due": [1], "calc-grc-threshold": [0], "trap-encash-cap": [0]}
N_SLIPS = sum(len(v) for v in SLIPS.values())
DECL = "\n".join(json.dumps(d, ensure_ascii=False) for d in ap.declarations("astar"))
DECL_TOKENS = math.ceil(len(DECL) / ap.CHARS_PER_TOKEN)                # the desk's tools, as Gemini receives them bound
N_TOOLS = len(da.TOOLSETS["astar"])
assert N_TOOLS == 8 and paired.MARGIN == 0.03 and paired.MARGIN_REGISTERED == "2026-10-08"
# LV-07's sentence, as the acme corpus writes it: the trap's figure is the clause's own
LV07_SENT = next(" ".join(s.split()) for c in ap.CorpusStore.chunks("acme") if "LV-07" in str(c.get("text") or "")
                 for s in re.split(r"(?<=[.;])\s+|\n+(?=[^a-z\s])", str(c.get("text") or "")) if "capped at 45 days" in s)
assert LV07_SENT == "Earned leave is encashed on exit at basic pay, capped at 45 days.", LV07_SENT
# ADK's own form of a reflect-and-retry, in the chat image's pin, read from the installed file
import importlib.metadata as md  # noqa: E402
assert md.version("google-adk") == "2.8.0"
ADK_RR = Path(md.distribution("google-adk").locate_file("google/adk/plugins/reflect_retry_tool_plugin.py")).read_text(encoding="utf-8")
assert "class ReflectAndRetryToolPlugin(BasePlugin):" in ADK_RR and "max_retries: int = 3," in ADK_RR
assert "tracking_scope: TrackingScope = TrackingScope.INVOCATION," in ADK_RR and "async def extract_error_from_result(" in ADK_RR
assert "max_retries: Maximum consecutive failures before giving up" in ADK_RR
assert "By overriding this method, you can trigger retry logic on these successful" in ADK_RR   # the default finds none

# ------------------------------------------------------------------ the offline runs: the kit's own output, no network
SCRATCH = Path(tempfile.mkdtemp(prefix="lesson103_"))


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


# the long ones first, in the background: the loop three times a row and verify once, each saved, as on the lane
PLAIN_OFF, VERIFY_OFF = HOME_P + "/plain-offline.jsonl", HOME_P + "/verify-offline.jsonl"
PLAIN_ARGS = [AE, "--offline", "--patterns", "loop", "--slice", SLICE, "--runs", str(RUNS), "--save", PLAIN_OFF]
VERIFY_ARGS = [AE, "--offline", "--patterns", "verify", "--slice", SLICE, "--save", VERIFY_OFF]
PLAIN_JOB = background(PLAIN_ARGS, "plain")
VERIFY_JOB = background(VERIFY_ARGS, "verify")

OUT = {}
TRIM = r"^(         \[|  - |  Worked out in code:)"            # the cells' grep -vE: passage lists and code's lines


def trimmed(text: str) -> str:
    """What the cell's grep -vE leaves of a turn's printout."""
    return "\n".join(ln for ln in text.splitlines() if not re.match(TRIM, ln)) + "\n"


plain_full, err = run_py([AT, "--offline", "--pattern", "verify"])
assert not err.strip(), err
OUT["turn_plain"] = trimmed(plain_full)
TURN_JSON, err = run_py([AT, "--offline", "--pattern", "verify", "--json"])
assert not err.strip(), err
TURN = json.loads(TURN_JSON)                       # the same turn, as its record: the lane turn's price is read from it
assert at.render(TURN, True) + "\n" == plain_full
invent_full, err = run_py([AT, "--offline", "--pattern", "verify", "--invent"])
assert not err.strip(), err
OUT["invent"] = trimmed(invent_full)
launder_full, err = run_py([AT, "--offline", "--pattern", "verify", "--launder"])
assert not err.strip(), err
OUT["launder"] = trimmed(launder_full)

T_P, T_I, T_L = OUT["turn_plain"], OUT["invent"], OUT["launder"]
assert "attempt 1: the loop, a turn of its own\n" in T_P and "attempt 2:" not in T_P
assert "the answer that ships: attempt 1's, the first the figure check passed" in T_P
assert "3 model calls in 1 attempt and 0 reflect calls (12 at most an attempt)" in T_P
assert (TURN["shipped"], TURN["model_calls"], TURN["notes"], TURN["check"]["passed"]) == (1, 3, [], True)
assert "  the attempt's answer: Gratuity, an estimate: Rs 2,50,000 [2].\n" in T_I
assert "failed: no calculator, question or passage of the turn wrote 2,50,000" in T_I
assert "attempt 2: the loop, a turn of its own, after a note" in T_I and "the answer that ships: attempt 2's, the first the figure check passed" in T_I
assert "6 model calls in 2 attempts and 1 reflect call (12 at most an attempt)" in T_I
assert "= Rs 2,40,000: 7 years 8 months counts as 8 years" in T_I
NOTE = re.search(r"never its question: (My answer stated a figure that no calculator of that turn returned\.[^\n]*)\n", T_I).group(1)
assert desk_calc.unsupported(NOTE) == [] and len(NOTE) <= ap.NOTE_CHARS
assert "the answer that ships: attempt 3's, the last of 3: the figure check passed none" in T_L
assert "8 model calls in 3 attempts and 2 reflect calls (12 at most an attempt)" in T_L
assert T_L.count("  the note writes 2,40,000: a note is never a source") == 2 and T_L.count("wrote 2,40,000\n") == 3
assert "1 search, 0 calculations, 0 refused or failed tool calls" in T_L
assert "figure check: no calculator, question or passage wrote 2,40,000 (desk_calc.unsupported)" in T_L
LAUNDER_NOTE = re.search(r"never its question: ([^\n]*The figure is Rs 2,40,000\.)\n", T_L).group(1)
assert LAUNDER_NOTE == NOTE + " The figure is Rs 2,40,000."
TOTALS = re.compile(r"\n(\d+) model calls in (\d) attempts? and (\d) reflect calls?.*\ntokens: in [\d,]+, thinking [\d,]+, visible [\d,]+; Rs ([\d.]+) ")
INV_CALLS, _, _, INV_RS = TOTALS.search(T_I).groups()
LAU_CALLS, _, _, LAU_RS = TOTALS.search(T_L).groups()
PLN_CALLS, _, _, PLN_RS = TOTALS.search(T_P).groups()
INV_REFLECT_RS = re.search(r"model call 3 \(reflect, gemini-3\.6-flash, thinking low\): in [\d,]+, thinking \d+, visible \d+ tokens, Rs ([\d.]+)", T_I).group(1)

# git's own words for the two edits and their restores, in a scratch repository holding the same files
REPO = SCRATCH / "kit"
(REPO / "commands").mkdir(parents=True)
(REPO / "services" / "chat").mkdir(parents=True)
shutil.copyfile(KIT / AP, REPO / AP)
shutil.copyfile(KIT / DA, REPO / DA)
GIT_ENV = {**os.environ, "HOME": str(HOME), "USERPROFILE": str(HOME), "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": str(SCRATCH / "gitconfig"), "LC_ALL": "C", "LANG": "C"}


def git(*args) -> str:
    """git in the scratch repository: what it prints, stdout and stderr together, as a terminal shows them."""
    r = subprocess.run([GIT, "-c", "core.autocrlf=false", "-c", "color.ui=never", *args], cwd=str(REPO),
                       capture_output=True, text=True, encoding="utf-8", env=GIT_ENV)
    assert r.returncode == 0, (args, r.stderr)
    return r.stdout + r.stderr


git("init", "-q")
git("add", AP, DA)
git("-c", "user.name=kit", "-c", "user.email=kit@example.com", "commit", "-q", "-m", "kit")
# the Change-it, as the page's sed writes it: the line marked THE QUESTION asks the question with every note after it
CHANGED_LINE = 'asked = " ".join([question] + kept["notes"])'
SED_CHANGE = f"sed -i 's/{QUESTION_LINE}.*/{CHANGED_LINE}/' {AP}"
assert "'" not in QUESTION_LINE + CHANGED_LINE and "/" not in CHANGED_LINE and "&" not in CHANGED_LINE and "\\" not in CHANGED_LINE
_lines = (REPO / AP).read_text(encoding="utf-8").splitlines(keepends=True)
with open(REPO / AP, "w", encoding="utf-8", newline="") as f:          # sed: the first match on each line, to its end
    f.writelines(re.sub(re.escape(QUESTION_LINE) + r".*", CHANGED_LINE, ln, count=1) for ln in _lines)
CHANGED_SRC = (REPO / AP).read_text(encoding="utf-8")
assert CHANGED_SRC.count(CHANGED_LINE) == 1 and "THE QUESTION" not in CHANGED_SRC
compile(CHANGED_SRC, AP, "exec")
STAT = git("diff", "--stat")
assert re.fullmatch(r" commands/agent_patterns\.py \| 2 \+-\n 1 file changed, 1 insertion\(\+\), 1 deletion\(-\)\n", STAT), STAT
CHANGE_PY = """import importlib.util, sys
from pathlib import Path
sys.path[:0] = ["commands", "services/chat", "."]
path = Path("commands/agent_patterns.py").resolve()
changed = Path(sys.argv[1]).read_text(encoding="utf-8")       # the file as the page's sed leaves it
mod = importlib.util.module_from_spec(importlib.util.spec_from_loader("agent_patterns", loader=None, origin=str(path)))
mod.__file__ = str(path)
sys.modules["agent_patterns"] = mod
exec(compile(changed, str(path), "exec"), mod.__dict__)
import agent_turn
sys.exit(agent_turn.main(["--offline", "--pattern", "verify", "--launder"]))
"""
change_full, err = run_py(["-", str(REPO / AP)], stdin=CHANGE_PY)
assert not err.strip(), err
OUT["change"] = STAT + trimmed(change_full)
T_C = trimmed(change_full)
assert "the answer that ships: attempt 2's, the first the figure check passed" in T_C
assert "5 model calls in 2 attempts and 1 reflect call" in T_C and "1 search, 0 calculations, 0 refused or failed tool calls" in T_C
assert f"\nquestion: {GRATUITY['question']} {LAUNDER_NOTE}\n" in T_C
assert "figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)" in T_C
CHG_CALLS, _, _, CHG_RS = TOTALS.search(T_C).groups()
RESTORED = git("checkout", "-q", "--", AP) + git("diff", "--stat")
assert RESTORED == "", RESTORED
assert (REPO / AP).read_text(encoding="utf-8") == AP_SRC
Q_COUNT = sum(QUESTION_LINE in ln for ln in AP_SRC.splitlines())
assert Q_COUNT == 1                                                       # grep -c 'asked = question  # THE QUESTION'
OUT["restore"] = RESTORED + f"{Q_COUNT}\n"
# the lane step's edit: the prompt's calculator rule deleted, sed's line range from its first line to its last
SED_RULE = f"sed -i '/{RULE_FROM}/,/{RULE_TO}/d' {DA}"
_lines = (REPO / DA).read_text(encoding="utf-8").splitlines(keepends=True)
_keep, _inside = [], False
for ln in _lines:
    if not _inside and RULE_FROM in ln:
        _inside = True
    if not _inside:
        _keep.append(ln)
    elif RULE_TO in ln:
        _inside = False
with open(REPO / DA, "w", encoding="utf-8", newline="") as f:
    f.writelines(_keep)
RULE_GONE = (REPO / DA).read_text(encoding="utf-8")
compile(RULE_GONE, DA, "exec")
assert RULE_FROM not in RULE_GONE and RULE_TO not in RULE_GONE and len(_lines) - len(_keep) == 3
assert '"- Say what each calculator returned and its formula. A gratuity figure is an estimate: call it one.\\n"' in RULE_GONE
RULE_STAT = git("diff", "--stat")
assert re.fullmatch(r" services/chat/desk_agent\.py \| 3 ---\n 1 file changed, 3 deletions\(-\)\n", RULE_STAT), RULE_STAT
RULE_RESTORED = git("checkout", "-q", "--", DA) + git("diff", "--stat")
assert RULE_RESTORED == "" and (REPO / DA).read_text(encoding="utf-8") == DA_SRC
R_COUNT = sum(RULE_FROM in ln for ln in DA_SRC.splitlines())
assert R_COUNT == 1
OUT["rule_del"] = RULE_STAT
OUT["rule_restore"] = RULE_RESTORED + f"{R_COUNT}\n"

OUT["check"], err = run_py([AE, "--check", "--slice", SLICE])
assert not err.strip(), err
assert OUT["check"].rstrip().endswith("every question let through by the hard gate")
assert "12 rows (11 calc, 0 lookup, 1 trap, 0 refuse, 0 chained)" in OUT["check"] and OUT["check"].count("\nok    ") == 11
assert "trap-encash-cap: encashable_days(balance=50, cap=45) = 45 days (LV-07); LV-07 writes 45 days itself: the trap" in OUT["check"]

# ------------------------------------------------------------------ the critic on its own, at Rs 0 (the standard library)
Q_GRAT, Q_GRC, Q_TRAP = GRATUITY["question"], GRC["question"], TRAP["question"]
CRITIC_PY = r'''import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["commands", "."]
import agent_patterns as ap      # the figure check needs the standard library and shared/ only: no framework, no model
from shared import desk_calc

Q = "%(q)s"
S53 = {"n": 1, "text": desk_calc.RULES["gratuity_rate"]["quote"]}          # the Code's own words: no digit in them
CALC = desk_calc.calculate("gratuity_estimate", monthly_wage=52000, years=7, months=8)
NOTE = "My answer stated a figure that no calculator of that turn returned. The figure is Rs 2,40,000."
GRC_Q, S4 = "%(grc)s", {"n": 1, "text": desk_calc.RULES["ir_s4_1"]["quote"]}
TRAP_Q, LV07 = "%(trap)s", {"n": 1, "text": "LV-07 Leave on exit. %(lv07)s"}
print(f"the calculator returned {desk_calc.inr(CALC['value'])}")
for what, answer, calcs, question, passages, stop in [
        ("its figure, from the calculator", "Gratuity, an estimate: Rs 2,40,000 [1].", [CALC], Q, [S53], None),
        ("the same figure, no calculator", "Gratuity, an estimate: Rs 2,40,000 [1].", [], Q, [S53], None),
        ("a figure of its own", "Gratuity, an estimate: Rs 2,50,000 [1].", [CALC], Q, [S53], None),
        ("a passage it never read", "Gratuity, an estimate: Rs 2,40,000 [3].", [CALC], Q, [S53], None),
        ("a turn its limits stopped", "I stopped at one of my limits.", [], Q, [], "model_calls"),
        ("a yes in words, no calculator", "A Grievance Redressal Committee: yes, it must have one [1].", [], GRC_Q, [S4], None),
        ("LV-07's 45 copied, no calculator", "Earned leave encashed on exit: 45 days [1].", [], TRAP_Q, [LV07], None),
        ("no calculator, the note in the question", "Gratuity, an estimate: Rs 2,40,000 [1].", [], Q + " " + NOTE, [S53], None)]:
    print(f"{what:<40} {ap.said_check(ap.figure_check(answer, calcs, question, passages, stop))}")
WAGE = {"monthly_wage": 60000, "years": 7, "months": 8}                      # a wage no message of the person's states
for whose, asked in (("the person's question", Q), ("a note put into it", Q + " The wage is Rs 60,000.")):
    refused, _ = desk_calc.check_args("gratuity_estimate", WAGE, [], asked)
    print(f"check_args on {whose}: {refused[0] if refused else 'monthly_wage = 60000 taken'}")''' % {
    "q": Q_GRAT, "grc": Q_GRC, "trap": Q_TRAP, "lv07": LV07_SENT}
OUT["critic"], err = run_py(["-"], stdin=CRITIC_PY)
assert not err.strip(), err
CR = OUT["critic"]
PASSED = "passed: every figure is a calculator's, the question's or a passage's, and every [n] a passage read"
assert CR.startswith("the calculator returned Rs 2,40,000\n")
assert re.search(r"\nits figure, from the calculator +" + re.escape(PASSED) + "\n", CR)
assert re.search(r"\nthe same figure, no calculator +failed: no calculator, question or passage of the turn wrote 2,40,000\n", CR)
assert re.search(r"\na figure of its own +failed: no calculator, question or passage of the turn wrote 2,50,000\n", CR)
assert re.search(r"\na passage it never read +failed: it cites \[3\], which no passage the turn read carries\n", CR)
assert re.search(r"\na turn its limits stopped +failed: the turn stopped at its model_calls limit\n", CR)
assert re.search(r"\na yes in words, no calculator +" + re.escape(PASSED) + "\n", CR)
assert re.search(r"\nLV-07's 45 copied, no calculator +" + re.escape(PASSED) + "\n", CR)
assert re.search(r"\nno calculator, the note in the question +" + re.escape(PASSED) + "\n", CR)
assert ("check_args on the person's question: monthly_wage = 60000 is a fact about the person that their message does not "
        "state: ask them for it\n") in CR and CR.endswith("check_args on a note put into it: monthly_wage = 60000 taken\n")
REFUSAL = "monthly_wage = 60000 is a fact about the person that their message does not state: ask them for it"

REFLECT_PY = r'''import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["commands", "."]
import agent_patterns as ap      # the standard library and shared/ only
from shared import desk_calc

Q = "%(q)s"
CALC = desk_calc.calculate("gratuity_estimate", monthly_wage=52000, years=7, months=8)
S53 = {"n": 1, "source": "code_on_social_security_2020.pdf", "section": None,
       "text": desk_calc.RULES["gratuity_rate"]["quote"]}
steps = [{"tools": [                                  # what the attempt did, as its trace keeps it
    {"name": "retrieve", "args": {"query": "gratuity fifteen days wages"}, "status": "success",
     "result": {"passages": [S53]}},
    {"name": "gratuity_estimate", "args": {"monthly_wage": 52000, "years": 7, "months": 8}, "status": "success",
     "result": CALC}]}]
answer = "Gratuity, an estimate: Rs 2,50,000 [1]."  # the calculator returned one figure; the answer wrote another
check = ap.figure_check(answer, [CALC], Q, [S53])
sent = ap.ask_reflect(Q, answer, steps, check)
print(sent)
print("the calculator's figure in what the reflect call reads:", "2,40,000" in sent or "240000" in sent)
reply = ("I wrote Rs 2,50,000 although `gratuity_estimate` returned another figure.\n\nNext time: call "
         "gratuity_estimate with the wage and the service the question states, state exactly the figure it "
         "returns, cite the passage, and give its formula. I will not round, estimate or work out any figure "
         "myself, and I will check every figure in my answer against the calculator's result before I answer.")
note = ap.cut_note(reply)
print(f"\nthe reply, {len(reply)} characters; the note code keeps, {len(note)}:\n{note}")
print("figures the note writes:", ", ".join(desk_calc.unsupported(note)) or "none")''' % {"q": Q_GRAT}
OUT["reflect"], err = run_py(["-"], stdin=REFLECT_PY)
assert not err.strip(), err
RF = OUT["reflect"]
assert RF.startswith(f"Question: {Q_GRAT}\n\nYour answer: Gratuity, an estimate: Rs 2,50,000 [1].\n\nWhat you did:\n")
assert '   call: gratuity_estimate {"monthly_wage": 52000, "years": 7, "months": 8}\n   returned: a figure\n' in RF
assert "\nThe figure check failed: no calculator, question or passage of the turn wrote 2,50,000\n" in RF
assert "the calculator's figure in what the reflect call reads: False\n" in RF
REPLY_LEN, KEPT_LEN = map(int, re.search(r"the reply, (\d+) characters; the note code keeps, (\d+):", RF).groups())
assert REPLY_LEN > ap.NOTE_CHARS >= KEPT_LEN and RF.endswith("figures the note writes: 2,50,000\n")
PY_CELL = re.compile(r"(?:#[^\n]*\n\s*)*python3?\s+-\s+<<['\"]?PY['\"]?\s*(?:#[^\n]*)?\n(.*?)\nPY\s*", re.S)  # the demo builder's

# ------------------------------------------------------------------ the offline evals, saved, then replayed side by side
plain_out, plain_err = collect(PLAIN_JOB)
quiet_err(plain_err)
OUT["plain_off"] = as_learner(plain_out)
verify_out, verify_err = collect(VERIFY_JOB)
quiet_err(verify_err)
OUT["verify_off"] = as_learner(verify_out)
PO, VO = OUT["plain_off"], OUT["verify_off"]
assert PO.startswith("OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 12 rows, 1 arm, 3 runs each")
assert "saved 36 runs to /home/you/plain-offline.jsonl" in PO and "== loop, thinking default (low), desk astar: 12 rows x 3 runs" in PO
assert VO.startswith("OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 12 rows, 1 arm, 1 run each")
assert "saved 12 runs to /home/you/verify-offline.jsonl" in VO and "== verify, thinking default (low), desk astar: 12 rows x 1 run" in VO
assert "  first runs: correct    12/12 = 100.0%" in PO and "              verified   9/12 = 75.0%" in PO
assert "  first runs: correct    12/12 = 100.0%" in VO and "              verified   10/12 = 83.3%" in VO
WITH_NOTES = re.search(r"\n  with notes: ([^\n]+)\n", VO).group(1)
assert WITH_NOTES.startswith("the figure check passed on attempt 1 in 11, on attempt 2 in 1, on attempt 3 in 0 and on none in 0 of 12 runs")
assert "0 of 1 notes write a figure, which no check takes from a note" in WITH_NOTES
REPLAY_ARGS = [AE, "--replay", PLAIN_OFF, VERIFY_OFF, "--best-of", "3"]
replay_full, err = run_py(REPLAY_ARGS)
assert not err.strip(), err
replay_full = as_learner(replay_full)
_rl = replay_full.splitlines()
_from = next(i for i, ln in enumerate(_rl) if ln.startswith("  paired (correct)"))
OUT["replay_off"] = "\n".join([_rl[0]] + _rl[_from:]) + "\n"           # the cell's sed -n '1p;/^  paired (correct)/,$p'
RO = OUT["replay_off"]
assert RO.startswith("replayed 48 saved runs of /home/you/plain-offline.jsonl, /home/you/verify-offline.jsonl: rescored at Rs 0, no model call")
assert "== check, retry or choose (lesson 10.3): loop against verify, on the 12 rows both ran" in RO
assert "no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08)" in RO
CRITIC_RE = re.compile(r"  (?P<label>[^:\n]+): correct (?P<c>\d+)/(?P<n>\d+) = [^\]\n]*\], verified (?P<v>\d+)/\d+ = "
                       r"[^\]\n]*\]; (?P<calls>[\d.]+) calls and Rs (?P<rs>[\d.]+) a row")
CRIT = {m.group("label"): m.groupdict() for m in CRITIC_RE.finditer(RO)}
L_P1, L_RR, L_BO = "pass@1, loop's first run", "pass@3 re-rolls, any of its first 3 runs (the ceiling a perfect chooser reaches)", \
    "best-of-3, the run the figure check chooses (code, no model)"
L_V = "pass@3 with notes, verify's answer that ships (up to 3 attempts, a note before each retry)"
assert list(CRIT) == [L_P1, L_RR, L_BO, L_V], list(CRIT)
PREC = re.search(r"\n  the figure check's precision: of the (\d+) of loop's (\d+) runs it passes, (\d+) correct \((\d+)%\) and (\d+) "
                 r"verified; of the (\d+) of verify's (\d+) attempts it passes, (\d+) correct \((\d+)%\) and (\d+) verified\n", RO)
PREC_PASS, PREC_RUNS, PREC_OK, _, PREC_VER, PREC_VPASS, PREC_VTRIES, PREC_VOK, _, PREC_VVER = PREC.groups()
assert (PREC_PASS, PREC_RUNS, PREC_OK, PREC_VER) == ("32", "36", "32", "30")
assert (PREC_VPASS, PREC_VTRIES, PREC_VOK, PREC_VVER) == ("12", "13", "12", "10")
PAIRED_V = re.search(r"\n  paired \(verified\), 12 rows: both (\d+), loop only (\d+), verify only (\d+), neither (\d+)\n", RO).groups()
assert PAIRED_V == ("9", "0", "1", "2")

READ_PY = r'''import json, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["evals", "commands", "."]
import agent_eval as ae          # the scorer, the figure check and best-of: the standard library and shared/ only

SAVED = %s      # the files make agent-eval's SAVE= wrote
rows = {r["id"]: r for r in ae.load_tasks()}
runs = [json.loads(line) for name in SAVED for line in open(os.path.expanduser(name), encoding="utf-8") if line.strip()]
word = {True: "pass", False: "fail"}
for rid in dict.fromkeys(r["row"] for r in runs):
    loop = sorted((r for r in runs if r["row"] == rid and r["arm"]["pattern"] == "loop"), key=lambda r: r["run"])
    ver = next((r for r in runs if r["row"] == rid and r["arm"]["pattern"] == "verify"), None)
    print(rid)
    if loop:
        good = ["yes" if ae.passed(ae.score(rows[rid], r), "verified") else "no" for r in loop]
        print(f"  loop runs: check {'/'.join(word[ae.passes(r)] for r in loop)}, verified {'/'.join(good)}; "
              f"best-of-{len(loop)} ships run {ae.best_of(loop, len(loop))['run'] + 1}")
    if ver:
        good = "yes" if ae.passed(ae.score(rows[rid], ver), "verified") else "no"
        print(f"  verify: check {' -> '.join(word[a['check']['passed']] for a in ver['attempts'])}; "
              f"ships attempt {ver['shipped']}, verified {good}")
        for a in ver["attempts"][1:]:
            print(f"    the note before attempt {a['n']}: {a['note'] or '(none: the reflect call wrote nothing)'}")
            print(f"    figures it writes: {', '.join(a['note_figures']) or 'none'}")'''
READ_OFF_PY = READ_PY % json.dumps(["~/plain-offline.jsonl", "~/verify-offline.jsonl"])
READ_LANE_PY = READ_PY % json.dumps(["~/plain.jsonl", "~/verify.jsonl"])
read_out, err = run_py(["-"], stdin=READ_OFF_PY)          # ~ is the scratch home, where SAVE= wrote them
assert not err.strip(), err
OUT["read_off"] = as_learner(read_out)
RD = OUT["read_off"]
assert RD.startswith("calc-gratuity-7y8m\n  loop runs: check fail/pass/pass, verified no/yes/yes; best-of-3 ships run 2\n"), RD[:300]
assert "  verify: check fail -> pass; ships attempt 2, verified yes\n" in RD
assert f"    the note before attempt 2: {NOTE}\n    figures it writes: none\n" in RD
assert "calc-grc-threshold\n  loop runs: check pass/pass/pass, verified no/yes/yes; best-of-3 ships run 2\n  verify: check pass; ships attempt 1, verified no\n" in RD
assert "trap-encash-cap\n  loop runs: check pass/pass/pass, verified no/yes/yes; best-of-3 ships run 2\n  verify: check pass; ships attempt 1, verified no\n" in RD
for _src in (CRITIC_PY, REFLECT_PY, READ_OFF_PY, READ_LANE_PY):
    assert PY_CELL.fullmatch("python - <<'PY'\n" + _src + "\nPY")       # a native Python cell for tools/build_workshop_demos.py
    assert "\ndef " not in _src                                         # no function: none to give a docstring


# ------------------------------------------------------------------ the saved runs, scored with the kit's own functions
def jsonl(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


PLAIN_RECS, VERIFY_RECS = jsonl(PLAIN_OFF), jsonl(VERIFY_OFF)
LOOP = {rid: sorted((r for r in PLAIN_RECS if r["row"] == rid), key=lambda r: r["run"]) for rid in ROWS}
VER = {rid: next(r for r in VERIFY_RECS if r["row"] == rid) for rid in ROWS}
assert all(len(v) == RUNS for v in LOOP.values()) and all(v["run"] == 0 for v in VER.values())
for rid, runs in LOOP.items():                     # the script slips where slips() says, and nowhere else
    assert [r["run"] for r in runs if not ae.backed(r)] == SLIPS[rid], rid
SLIP_ROWS = [rid for rid, v in SLIPS.items() if v]
N_FIRST_SLIPS = sum(0 in v for v in SLIPS.values())                      # the rows whose first run slips: pass@1's misses
SLIP_CHECKED = [ae.passes(LOOP[rid][r]) for rid in SLIP_ROWS for r in SLIPS[rid]]
N_SLIP_FAILED, N_SLIP_PASSED = SLIP_CHECKED.count(False), SLIP_CHECKED.count(True)
assert (len(SLIP_ROWS), N_FIRST_SLIPS, N_SLIP_FAILED, N_SLIP_PASSED) == (6, 3, 4, 2)
assert all(ae.backed(ae.best_of(LOOP[rid], RUNS)) for rid in ROWS)        # best-of-3 ships a calculator-backed run on every row
assert sum(len(r["notes"]) for r in VERIFY_RECS) == 1                     # the one note offline: the gratuity row's
assert [rid for rid in ROWS if VER[rid]["shipped"] > 1] == ["calc-gratuity-7y8m"]


def hit(row: dict, rec: dict) -> dict:
    """correct and verified for one run, by the eval's scorer."""
    s = ae.score(row, rec)
    return {"correct": s["correct"], "verified": ae.passed(s, "verified")}


def spent(recs: list) -> tuple:
    """Calls and rupees (model and rag-api), as critic() counts them."""
    return (sum(r.get("model_calls") or 0 for r in recs), sum((r.get("inr") or 0) + (r.get("rag_inr") or 0) for r in recs))


def four_ways(rid: str, k: int) -> list:
    """One row's four ways at k: (label, hit, (calls, rupees))."""
    row, runs, v = ROWS[rid], LOOP[rid][:k], VER[rid]
    any_hit = {w: any(hit(row, r)[w] for r in runs) for w in ("correct", "verified")}
    return [("pass@1", hit(row, runs[0]), spent(runs[:1])), (f"pass@{k} re-rolls", any_hit, spent(runs)),
            (f"best-of-{k}", hit(row, ae.best_of(runs, k)), spent(runs)),
            (f"pass@{ap.MAX_ATTEMPTS} with notes", hit(row, v), spent([v]))]


SLICE_AT = {}
for k in range(1, RUNS + 1):
    per = [four_ways(rid, k) for rid in ROWS]
    SLICE_AT[k] = []
    for i in range(4):
        label = per[0][i][0]
        n_c = sum(p[i][1]["correct"] for p in per)
        n_v = sum(p[i][1]["verified"] for p in per)
        calls = sum(p[i][2][0] for p in per) / len(per)
        rs = sum(p[i][2][1] for p in per) / len(per)
        SLICE_AT[k].append([label, f"{n_c}/{len(per)}", f"{n_v}/{len(per)}", f"{calls:.1f}", f"{rs:.4f}"])
for (label, c, v, calls, rs), key in zip(SLICE_AT[3], (L_P1, L_RR, L_BO, L_V)):     # the panel's k = 3 is critic()'s own line
    got = CRIT[key]
    assert (c, v, calls, rs) == (f"{got['c']}/{got['n']}", f"{got['v']}/{got['n']}", got["calls"], got["rs"]), (label, got)
P1, RR, BO, VV = (CRIT[k] for k in (L_P1, L_RR, L_BO, L_V))


def tools_of(rec: dict) -> str:
    return " -> ".join(rec.get("tool_calls") or ()) or "no tool"


def run_card(row: dict, rec: dict) -> dict:
    """One of the loop's runs as the panel shows it: its tools, its answer, the figure check's verdict and the eval's."""
    chk = ap.figure_check(rec["answer"], rec["calculations"], rec["question"], rec["passages"], rec["stopped_by"])
    s = ae.score(row, rec)
    return {"n": rec["run"] + 1, "tools": tools_of(rec), "ans": rec["answer"], "chk": ap.said_check(chk),
            "pass": chk["passed"], "backed": ae.backed(rec), "ok": s["correct"], "ver": ae.passed(s, "verified"),
            "why": s["why"], "calls": rec["model_calls"], "rs": f"{rec['inr']:.4f}"}


def attempt_card(a: dict, calls: list) -> dict:
    """One of verify's attempts: its note, its tools, its answer and the check's verdict, its calls and rupees."""
    mine = [c for c in calls if c.get("attempt") == a["n"]]
    reflect = next((c for c in mine if c.get("role") == "reflect"), None)
    return {"n": a["n"], "note": a.get("note") or "", "nf": a.get("note_figures") or [],
            "reflect": f"{reflect['inr']:.4f}" if reflect else "", "tools": " -> ".join(a.get("tool_calls") or ()) or "no tool",
            "ans": a["answer"], "chk": ap.said_check(a["check"]), "pass": a["check"]["passed"],
            "calls": a["model_calls"], "rs": f"{a['inr']:.4f}"}


def figure(row: dict) -> str:
    v, unit = row["expected"], row["unit"]
    if unit == "INR":
        return desk_calc.inr(v)
    if unit == "days":
        return f"{desk_calc.num(v)} days"
    if unit == "yes/no":
        return "yes" if v else "no"
    return str(v)


def hint(rid: str) -> str:
    """What happens on the row, from its runs: which run writes its figure with no calculator, and what verify did."""
    slipped = [run_card(ROWS[rid], r) for r in LOOP[rid] if not ae.backed(r)]
    if not slipped:
        return "every run calls its calculator"
    words = "; ".join(f"run {c['n']} skips the calculator, the check {'passes' if c['pass'] else 'fails'} it" for c in slipped)
    return words + ("; verify retries" if VER[rid]["shipped"] > 1 else "")


ORDER = ["calc-gratuity-7y8m", "calc-grc-threshold", "trap-encash-cap"] + [
    r for r in ROWS if r not in ("calc-gratuity-7y8m", "calc-grc-threshold", "trap-encash-cap")]
PANEL = {"rows": [{"id": rid, "label": f"{rid}: {figure(ROWS[rid])} ({hint(rid)})"} for rid in ORDER],
         "max": ap.MAX_ATTEMPTS, "data": {}, "all": {str(k): v for k, v in SLICE_AT.items()}}
for rid in ORDER:
    row, v = ROWS[rid], VER[rid]
    vh = hit(row, v)
    PANEL["data"][rid] = {
        "q": row["question"], "runs": [run_card(row, r) for r in LOOP[rid]],
        "best": {str(k): ae.best_of(LOOP[rid][:k], k)["run"] for k in range(1, RUNS + 1)},
        "ver": {"attempts": [attempt_card(a, v["calls"]) for a in v["attempts"]], "shipped": v["shipped"],
                "ok": vh["correct"], "vok": vh["verified"], "calls": v["model_calls"], "rs": f"{v['inr']:.4f}"},
        "ways": {str(k): [[lab, h["correct"], h["verified"], c, f"{rs:.4f}"] for lab, h, (c, rs) in four_ways(rid, k)]
                 for k in range(1, RUNS + 1)}}
_g = PANEL["data"]["calc-gratuity-7y8m"]
assert [a["pass"] for a in _g["ver"]["attempts"]] == [False, True] and _g["ver"]["attempts"][1]["note"] == NOTE
assert _g["best"] == {"1": 0, "2": 1, "3": 1}
for _rid in ("calc-grc-threshold", "trap-encash-cap"):
    _d = PANEL["data"][_rid]
    assert _d["runs"][0]["pass"] and not _d["runs"][0]["ver"] and _d["best"]["3"] == 1 and not _d["ver"]["vok"]
JS = """<script>
(function(){
  'use strict';
  var D = __DATA__;
  var root = document.getElementById('cc'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var rowSel = $('cc-row'), kSel = $('cc-k'), cols = $('cc-cols'), ways = $('cc-ways'), all = $('cc-all');
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function said(ok, yes, no){ return el('span', ok ? 'good' : 'bad', ok ? yes : no); }
  function line(box, parts){ var p = el('p'); parts.forEach(function(x){ p.appendChild(typeof x === 'string' ? document.createTextNode(x) : x); }); box.appendChild(p); }
  function col(name, how){ var c = el('div', 'cc-col'); c.appendChild(el('div', 'cc-name', name)); c.appendChild(el('p', 'cc-how', how)); return c; }
  function runCard(r, pick){
    var box = el('div', 'cc-c' + (pick ? ' pick' : ''));
    box.appendChild(el('div', 'cc-h', 'run ' + r.n + ' · ' + r.calls + ' calls · Rs ' + r.rs + (pick ? ' · the one best-of ships' : '')));
    line(box, ['tools: ' + r.tools]);
    box.appendChild(el('pre', '', r.ans));
    line(box, ['figure check: ', said(r.pass, r.chk, r.chk)]);
    line(box, ['the eval: ', said(r.ok, 'correct', 'not correct'), ', ', said(r.ver, 'verified', 'not verified' + (r.why ? ' (' + r.why + ')' : ''))]);
    return box;
  }
  function table(caption, rows){
    var t = el('table'), head = el('tr');
    t.appendChild(el('caption', '', caption));
    ['way', 'correct', 'verified', 'calls', 'Rs'].forEach(function(h){ head.appendChild(el('th', '', h)); });
    t.appendChild(head);
    rows.forEach(function(r){
      var tr = el('tr');
      [r[0], r[1] === true ? 'yes' : r[1] === false ? 'no' : r[1], r[2] === true ? 'yes' : r[2] === false ? 'no' : r[2], String(r[3]), r[4]].forEach(function(v){ tr.appendChild(el('td', '', v)); });
      t.appendChild(tr);
    });
    return t;
  }
  function render(){
    var d = D.data[rowSel.value], k = kSel.value, best = d.best[k];
    cols.textContent = '';
    var a = col('Re-roll', 'The loop, its first ' + k + ' run' + (k === '1' ? '' : 's') + '. Each is a whole turn; pass@' + k + ' counts the row when any is right.');
    d.runs.slice(0, Number(k)).forEach(function(r, i){ a.appendChild(runCard(r, false)); });
    cols.appendChild(a);
    var b = col('Choose', 'Best-of-' + k + ': the figure check first, then a calculator\\'s figure stated, then the earliest. It never reads the expected figure.');
    d.runs.slice(0, Number(k)).forEach(function(r, i){
      var box = el('div', 'cc-c' + (i === best ? ' pick' : ''));
      box.appendChild(el('div', 'cc-h code', 'run ' + r.n + (i === best ? ' · shipped' : '')));
      line(box, ['the check: ', said(r.pass, 'passes it', 'fails it')]);
      line(box, ['a calculator\\'s figure stated: ', said(r.backed, 'yes', 'no')]);
      b.appendChild(box);
    });
    cols.appendChild(b);
    var c = col('Retry', 'verify: the loop once; a failed check gets one reflect call and its note, then the loop again, at most ' + D.max + ' attempts.');
    d.ver.attempts.forEach(function(t){
      var box = el('div', 'cc-c' + (t.n === d.ver.shipped ? ' pick' : ''));
      box.appendChild(el('div', 'cc-h', 'attempt ' + t.n + ' · ' + t.calls + ' calls · Rs ' + t.rs + (t.n === d.ver.shipped ? ' · ships' : '')));
      if (t.note) { line(box, ['the reflect call (Rs ' + t.reflect + ') wrote the note, put into this attempt\\'s system prompt:']); box.appendChild(el('pre', 'note', t.note)); line(box, ['figures the note writes: ' + (t.nf.length ? t.nf.join(', ') : 'none')]); }
      line(box, ['tools: ' + t.tools]);
      box.appendChild(el('pre', '', t.ans));
      line(box, ['figure check: ', said(t.pass, t.chk, t.chk)]);
      c.appendChild(box);
    });
    var end = el('div', 'cc-c');
    line(end, ['the eval on what ships: ', said(d.ver.ok, 'correct', 'not correct'), ', ', said(d.ver.vok, 'verified', 'not verified')]);
    c.appendChild(end);
    cols.appendChild(c);
    ways.textContent = '';
    ways.appendChild(table('This row, k = ' + k + ': each way, and what it cost', d.ways[k]));
    all.textContent = '';
    all.appendChild(table('All ' + D.rows.length + ' rows, k = ' + k + ': rows right, and calls and rupees a row', D.all[k]));
  }
  D.rows.forEach(function(r){ var o = el('option', '', r.label); o.value = r.id; rowSel.appendChild(o); });
  rowSel.value = D.rows[0].id;
  rowSel.addEventListener('change', render);
  kSel.addEventListener('change', render);
  render();
})();
</script>
""".replace("__DATA__", json.dumps(PANEL, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"))
assert "<div" not in JS and "font-size" not in JS and "innerHTML" not in JS


# ------------------------------------------------------------------ what the lane's runs cost, before thinking
def bound(c: dict) -> bool:
    """A call that binds the desk's tools: every loop call, and verify's answer calls; the reflect call binds none."""
    return (c.get("role") or "answer") == "answer"


def base_rs(c: dict) -> float:
    """Input and visible output at the call's model, the tools' declarations added where Gemini receives them."""
    return prices.inr(prices.usd(c["model"], c["tokens_in"] + (DECL_TOKENS if bound(c) else 0), c["visible_tokens"]))


def per_k(c: dict) -> float:
    """What 1,000 thinking tokens cost on this call: thinking is billed as output."""
    return prices.inr(prices.usd(c["model"], 0, 1000))


def estimate(calls: list) -> tuple:
    return sum(base_rs(c) for c in calls), sum(per_k(c) for c in calls), len(calls)


def stop_at(calls: list) -> int:
    """The thinking tokens a call at which one Meter's spend reaches Rs 5 before its last call, so the Meter stops it."""
    before = sum(base_rs(c) for c in calls[:-1])
    k = sum(per_k(c) for c in calls[:-1])
    return int((limits.TURN_BUDGET_INR - before) * 1000 / k)


def attempts_of(rec: dict) -> list:
    """A verify run's calls, one list an attempt: each attempt has a Meter of its own, its reflect call counted on it."""
    return [[c for c in rec["calls"] if c.get("attempt") == n] for n in range(1, rec["shipped"] + 1)]


RUN_CALLS = {"turn_verify": TURN["calls"], "eval_plain": [c for r in PLAIN_RECS for c in r["calls"]],
             "eval_verify": [c for r in VERIFY_RECS for c in r["calls"]]}
N_TURNS = {"turn_verify": 1, "eval_plain": len(PLAIN_RECS), "eval_verify": len(VERIFY_RECS)}
assert N_TURNS == {"turn_verify": 1, "eval_plain": 36, "eval_verify": 12}
EST = {k: estimate(v) for k, v in RUN_CALLS.items()}
ALL_RS = sum(v[0] for v in EST.values())
ALL_K = sum(v[1] for v in EST.values())
ALL_CALLS = sum(v[2] for v in EST.values())
ALL_TURNS = sum(N_TURNS.values())
_retry = [c for c in VER["calc-gratuity-7y8m"]["calls"] if c.get("attempt") == 2]
assert [c["role"] for c in _retry] == ["reflect", "answer", "answer", "answer"]
RETRY_RS, RETRY_K, RETRY_N = estimate(_retry)
STOP_LOOP = min(stop_at(r["calls"]) for r in PLAIN_RECS)
STOP_VERIFY = min(stop_at(a) for r in VERIFY_RECS + [TURN] for a in attempts_of(r) if len(a) > 1)
STOP_MIN = min(STOP_LOOP, STOP_VERIFY)
CAP_TURN = limits.TURN_BUDGET_INR * ap.MAX_ATTEMPTS                     # verify: a Meter an attempt
CAP_ALL = N_TURNS["eval_plain"] * limits.TURN_BUDGET_INR + (N_TURNS["eval_verify"] + 1) * CAP_TURN
RS_K_OUT = prices.inr(prices.usd(MODEL, 0, 1000))


def money(x: float) -> str:
    return f"{x:,.2f}"


COST = {f"EST_{k.upper()}": money(v[0]) for k, v in EST.items()}
COST.update({f"K_{k.upper()}": money(v[1]) for k, v in EST.items()})
COST.update({f"N_{k.upper()}": str(v[2]) for k, v in EST.items()})
COST.update({"EST_ALL": money(ALL_RS), "K_ALL": money(ALL_K), "N_ALL_CALLS": str(ALL_CALLS), "N_ALL_TURNS": str(ALL_TURNS),
             "CAP_ALL": money(CAP_ALL), "CAP_TURN": money(CAP_TURN), "EST_RETRY": money(RETRY_RS), "K_RETRY": money(RETRY_K),
             "N_RETRY": str(RETRY_N), "STOP_LOOP": f"{STOP_LOOP:,}", "STOP_VERIFY": f"{STOP_VERIFY:,}", "STOP_MIN": f"{STOP_MIN:,}",
             # the thinking a call that keeps these runs within the lesson plan's Rs 60 and Rs 90 (its estimate, Rs 60-90)
             "T60": f"{int((60 - ALL_RS) * 1000 / ALL_K):,}", "T90": f"{int((90 - ALL_RS) * 1000 / ALL_K):,}"})

# ------------------------------------------------------------------ the author's runs: what a live lane printed
REC_NAMES = ("ui_twice", "turn_verify", "eval_plain", "eval_verify", "eval_side", "records_read")
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
GREP_TRIM = "grep -vE '" + TRIM + "'"
TURN_CMD = "make agent-turn OFFLINE=1 PATTERN=verify"
SIDE = "sed -n '1p;/^  paired (correct)/,$p'"
CELLS = {
    "classes": ("run in the operator shell, in the kit (once, if lesson 10.1's setup line has not run: acme's and zeta's stored rows get their classes)",
                'for t in acme zeta; do make doc-types PROJECT="$PROJECT" TENANT=$t SEED=manifest APPLY=1; done'),
    "critic": ("run in the operator shell, in the kit (a Python cell; Rs 0, the standard library: the figure check and check_args, no model)",
               heredoc(CRITIC_PY)),
    "reflect": ("run in the operator shell, in the kit (a Python cell; Rs 0: what a reflect call reads, and the note code keeps)",
                heredoc(REFLECT_PY)),
    "turn_plain": ("run in the operator shell, in the kit (Rs 0: verify on the gratuity row as the prompt stands; the first run builds ~/graph-venv)",
                   f"{TURN_CMD} 2>&1 | {GREP_TRIM}"),
    "invent": ("run in the operator shell, in the kit (Rs 0: a first attempt that writes a figure of its own)",
               f"{TURN_CMD} INVENT=1 2>&1 | {GREP_TRIM}"),
    "launder": ("run in the operator shell, in the kit (Rs 0: notes that carry a figure)",
                f"{TURN_CMD} LAUNDER=1 2>&1 | {GREP_TRIM}"),
    "change": ("run in the operator shell, in the kit (the Change-it: the notes put into the question, then the same run)",
               f"{SED_CHANGE} && git diff --stat\n{TURN_CMD} LAUNDER=1 2>&1 | {GREP_TRIM}"),
    "restore": ("run in the operator shell, in the kit (put the line back)",
                f"git checkout -q -- {AP} && git diff --stat && grep -c '{QUESTION_LINE}' {AP}"),
    "check": (f"run in the operator shell, in the kit (Rs 0, the standard library: every figure of the {len(ROWS)} rows recomputed)",
              f"make agent-eval CHECK=1 SLICE={SLICE}"),
    "plain_off": ("run in the operator shell, in the kit (Rs 0: the loop, three scripted runs a row, saved)",
                  f'make agent-eval OFFLINE=1 PATTERNS=loop SLICE={SLICE} RUNS={RUNS} SAVE="$HOME/plain-offline.jsonl"'),
    "verify_off": ("run in the operator shell, in the kit (Rs 0: verify, one scripted run a row, saved)",
                   f'make agent-eval OFFLINE=1 PATTERNS=verify SLICE={SLICE} SAVE="$HOME/verify-offline.jsonl"'),
    "replay_off": ("run in the operator shell, in the kit (Rs 0: the two saves side by side; the first line, then what the two reports above do not print)",
                   f'make agent-eval REPLAY="$HOME/plain-offline.jsonl $HOME/verify-offline.jsonl" BEST_OF={RUNS} | {SIDE}'),
    "read_off": ("run in the operator shell, in the kit (a Python cell; Rs 0: the saved runs read back, row by row)",
                 heredoc(READ_OFF_PY)),
    "turn_verify": (f"run in the operator shell, in the kit (one live verify turn, about Rs {COST['EST_TURN_VERIFY']} before thinking if its first attempt passes)",
                    f"make agent-turn {LANE} PATTERN=verify"),
    "rule_del": ("run in the operator shell, in the kit (delete the prompt's calculator rule, for the next two runs only)",
                 f"{SED_RULE} && git diff --stat"),
    "eval_plain": (f"run in the operator shell, in the kit ({N_TURNS['eval_plain']} live turns, about Rs {COST['EST_EVAL_PLAIN']} before thinking)",
                   f'make agent-eval {LANE} PATTERNS=loop SLICE={SLICE} RUNS={RUNS} SAVE="$HOME/plain.jsonl"'),
    "eval_verify": (f"run in the operator shell, in the kit ({N_TURNS['eval_verify']} live verify runs, about Rs {COST['EST_EVAL_VERIFY']} before thinking, more for each retry)",
                    f'make agent-eval {LANE} PATTERNS=verify SLICE={SLICE} SAVE="$HOME/verify.jsonl"'),
    "rule_restore": ("run in the operator shell, in the kit (put the rule back, at once)",
                     f"git checkout -q -- {DA} && git diff --stat && grep -c '{RULE_FROM}' {DA}"),
    "eval_side": ("run in the operator shell, in the kit (Rs 0: your two saves side by side)",
                  f'make agent-eval REPLAY="$HOME/plain.jsonl $HOME/verify.jsonl" BEST_OF={RUNS} | {SIDE}'),
    "records_read": ("run in the operator shell, in the kit (a Python cell; Rs 0: your lane's saved runs read back)",
                     heredoc(READ_LANE_PY)),
}
OUTS = {
    "critic": ("(the kit's own functions, run when this page was built)", OUT["critic"]),
    "reflect": ("(the kit's own functions, run when this page was built)", OUT["reflect"]),
    "turn_plain": ("(the kit's own output, trimmed as the cell trims it; produced when this page was built)", OUT["turn_plain"]),
    "invent": ("(the kit's own output, trimmed as the cell trims it)", OUT["invent"]),
    "launder": ("(the kit's own output, trimmed as the cell trims it)", OUT["launder"]),
    "change": ("(git's stat for the edit, then the kit's own output with the notes in the question)", OUT["change"]),
    "restore": ("(git's stat prints nothing: the file is the kit's again)", OUT["restore"]),
    "check": ("(the kit's own output, produced when this page was built)", OUT["check"]),
    "plain_off": ("(stdout, produced when this page was built; one progress line a run goes to stderr)", OUT["plain_off"]),
    "verify_off": ("(stdout, produced when this page was built)", OUT["verify_off"]),
    "replay_off": ("(the kit's own output, as the cell's sed leaves it)", OUT["replay_off"]),
    "read_off": ("(the kit's own saved runs, read back when this page was built)", OUT["read_off"]),
    "rule_del": ("(git's stat: three lines gone from the prompt)", OUT["rule_del"]),
    "rule_restore": ("(git's stat prints nothing, and the rule is there once)", OUT["rule_restore"]),
    "ui_twice": ("(the author's lane: your answers, figures, times and rupees are yours)", REC["ui_twice"]),
    "turn_verify": ("(the author's lane: the answer and any note are Gemini's own, so yours differ)", REC["turn_verify"]),
    "eval_plain": ("(the author's lane, stdout: every figure in it is the lane's)", REC["eval_plain"]),
    "eval_verify": ("(the author's lane, stdout)", REC["eval_verify"]),
    "eval_side": ("(the author's lane's saved runs, side by side)", REC["eval_side"]),
    "records_read": ("(the author's lane's saved runs, read back)", REC["records_read"]),
}
WIN = {f"CELL_{k.upper()}": bash_window(*v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})

# ------------------------------------------------------------------ the numbers the prose states
NEXT = MANIFEST["modules"]["10"]["lessons"]["10.4"]["name"]
PREV = MANIFEST["modules"]["10"]["lessons"]["10.2"]["name"]
FIRST = MANIFEST["modules"]["10"]["lessons"]["10.1"]["name"]
ROW_TABLE = []
for rid, row in ROWS.items():
    c = row["calcs"][0]
    args = ", ".join(f"{k}={v}" for k, v in c["args"].items())
    ROW_TABLE.append(f'<tr><td><code>{rid}</code></td><td data-label="Its calculator and figure"><code>{c["calculator"]}'
                     f'({html.escape(args)})</code> = {html.escape(figure(row))}, {html.escape(row["clause"])}</td>'
                     f'<td data-label="Offline, the loop\'s three runs">{html.escape(hint(rid))}</td></tr>')
STATS = {
    "MODEL": MODEL, "RATE_IN": f"{RATE_IN:.2f}", "RATE_OUT": f"{RATE_OUT:.2f}", "USD_INR": str(prices.USD_INR),
    "RS_K_OUT": f"{RS_K_OUT:.4f}", "MAX_CALLS": str(limits.MAX_MODEL_CALLS), "BUDGET": f"{limits.TURN_BUDGET_INR:g}",
    "DEADLINE": f"{limits.TURN_DEADLINE_S:g}", "DEFAULT_LEVEL": da.THINKING_LEVEL, "N_TOOLS": str(N_TOOLS),
    "MAX_ATTEMPTS": str(ap.MAX_ATTEMPTS), "MAX_RETRIES": str(ap.MAX_ATTEMPTS - 1), "NOTE_CHARS": str(ap.NOTE_CHARS),
    "N_ROWS": str(len(ROWS)), "N_CALC": str(N_CALC), "N_TASKS": str(len(TASKS)), "RUNS": str(RUNS),
    "N_RUNS_LOOP": str(len(PLAIN_RECS)), "N_SLIPS": str(N_SLIPS), "ROW_TABLE": "\n".join(ROW_TABLE),
    "DECL_TOKENS": f"{DECL_TOKENS:,}", "RULE_TOKENS": str(RULE_TOKENS), "SCRIPT_TH": str(ap.SCRIPTED_THINKING[da.THINKING_LEVEL]),
    "QUESTION": html.escape(Q_GRAT), "GRAT_ID": GRATUITY["id"], "GRAT_FIG": desk_calc.inr(GRATUITY["expected"]),
    "LV07_SENT": html.escape(LV07_SENT), "NOTE": html.escape(NOTE), "REFUSAL": html.escape(REFUSAL),
    "REPLY_LEN": str(REPLY_LEN), "KEPT_LEN": str(KEPT_LEN),
    "PLN_CALLS": PLN_CALLS, "PLN_RS": PLN_RS, "INV_CALLS": INV_CALLS, "INV_RS": INV_RS, "INV_REFLECT_RS": INV_REFLECT_RS,
    "LAU_CALLS": LAU_CALLS, "LAU_RS": LAU_RS, "CHG_CALLS": CHG_CALLS, "CHG_RS": CHG_RS,
    "P1_C": f"{P1['c']}/{P1['n']}", "P1_V": f"{P1['v']}/{P1['n']}", "P1_CALLS": P1["calls"], "P1_RS": P1["rs"],
    "RR_C": f"{RR['c']}/{RR['n']}", "RR_V": f"{RR['v']}/{RR['n']}", "RR_CALLS": RR["calls"], "RR_RS": RR["rs"],
    "BO_C": f"{BO['c']}/{BO['n']}", "BO_V": f"{BO['v']}/{BO['n']}", "BO_CALLS": BO["calls"], "BO_RS": BO["rs"],
    "V_C": f"{VV['c']}/{VV['n']}", "V_V": f"{VV['v']}/{VV['n']}", "V_CALLS": VV["calls"], "V_RS": VV["rs"],
    "PREC_PASS": PREC_PASS, "PREC_RUNS": PREC_RUNS, "PREC_OK": PREC_OK, "PREC_VER": PREC_VER,
    "PREC_VPASS": PREC_VPASS, "PREC_VTRIES": PREC_VTRIES, "PREC_VOK": PREC_VOK, "PREC_VVER": PREC_VVER,
    "PREC_BLIND": str(int(PREC_OK) - int(PREC_VER)), "MARGIN": f"{100 * paired.MARGIN:g}",
    "N_SLIP_ROWS": str(len(SLIP_ROWS)), "N_FIRST_SLIPS": str(N_FIRST_SLIPS), "N_SLIP_FAILED": str(N_SLIP_FAILED),
    "N_SLIP_PASSED": str(N_SLIP_PASSED), "N_LIVE_LOOP": str(N_TURNS["eval_plain"]), "N_LIVE_VERIFY": str(N_TURNS["eval_verify"]),
    "N_LIVE_RUNS": str(N_TURNS["eval_plain"] + N_TURNS["eval_verify"]),
    "NEXT_TITLE": html.escape(NEXT), "PREV_TITLE": html.escape(PREV), "FIRST_TITLE": html.escape(FIRST), **COST,
}
assert int(PREC_PASS) == int(PREC_RUNS) - 4 and int(PREC_OK) - int(PREC_VER) == 2   # the two passes with no calculator behind them
if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(json.dumps({k: v for k, v in STATS.items() if k not in ("ROW_TABLE",)}, indent=1))
    print("panel bytes:", len(JS))
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
for k in ("T60", "T90", "STOP_LOOP", "STOP_VERIFY"):
    if f"about {COST[k]} thinking tokens" not in run_list:
        print(f"note: RUN_LIST.md does not state {k} = about {COST[k]} thinking tokens a call")
print(f"kit: {len(ROWS)} rows, the loop x {RUNS} and verify x 1 offline | pass@1 {P1['v']}/{P1['n']} verified, re-rolls "
      f"{RR['v']}, best-of-3 {BO['v']}, verify {VV['v']} | precision {PREC_PASS}/{PREC_RUNS} passed, {PREC_VER} verified | "
      f"lane before thinking: all Rs {COST['EST_ALL']} over {ALL_CALLS} calls in {ALL_TURNS} turns, Rs {COST['K_ALL']} for "
      f"each 1,000 thinking tokens a call | an attempt reaches Rs 5 at about {STOP_MIN} thinking tokens a call | "
      f"declarations ~{DECL_TOKENS} tokens a call")
