"""Build lesson 10.5 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

A desk run as an agent with checked calculator arguments. When the router says a question asks for a figure
(needs_calculation), the handbook or statute desk runs as a small agent (services/chat/desk_agent.py): the model reads
this turn's passages and chooses the calls, shared/desk_calc.py does the arithmetic, and check_args() first takes every
argument from its one source - a fact about the person from their message, a handbook figure from its clause of a
passage the turn read - or refuses it in words the model reads. Then the Desk's three eval arms on the same twelve dev
rows (evals/route_arms.jsonl): B the routed Desk, C code only, A* one agent; side by side with a paired difference
labelled indicative (evals/route_eval.py --compare), and combined (evals/combine.py: a vote over what code returned, a
tie to a person; a scripted arbiter and mixture-of-agents aggregator).

Build-time proof. Every verdict of the Level 0 panel is desk_agent._calc() run here, on the lane's own handbook chunks
(evals/agent_eval.clause_chunk) and s.53's sentences as desk_calc quotes them, with the line desk_agent.calc_line()
writes. Three of test_desk.py's agent tests run here as the kit is, and again in a subprocess on a copy of
desk_agent.py that the Change-it cell's own code has edited. One Desk turn runs on the kit's own graph
(desk_graph.build() and run_turn(), with test_desk.py's stand-ins: a scripted model, and rag-api as a table holding the
lane's chunks) to show what the thread checkpoints. combine.py --selftest --layers 2 and the kit's two K-10.5 test files
run here. Every output from a lane is the author's recorded run (pagebuild.recorded(), RUN_LIST.md); until it is
recorded the page shows a marked stand-in. Nothing here reads a clock into the page: test times are shown as N.NNN.
"""
import html
import importlib.util
import io
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import warnings
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "10.5"
title = ("<title>Lesson 10.5 Run a desk as an agent with checked calculator arguments - every number from the question "
         "or its clause, then three arms on the same rows | Netsetos</title>\n")
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)                   # the kit's own log lines are not the page's

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:1fr;gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;width:100%;}
@media (min-width:640px){.pc-in.two{grid-template-columns:1fr 1fr;}}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:13px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box p{margin:4px 0;}
.ac-h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:10px 0 4px;}
.ac-words{font-size:14px;color:var(--navy);background:#f1f5f9;border-radius:8px;padding:8px 10px;margin:4px 0;}
.ac-pass{border-left:3px solid var(--teal);padding:2px 10px;margin:6px 0;white-space:pre-wrap;}
.ac-pass b{font-family:var(--mono);font-size:12px;color:var(--navy);}
.ac-reads{font-family:var(--mono);font-size:12px;color:#0e7490;margin:2px 0 6px;}
.ac-call{font-family:var(--mono);font-size:13px;background:var(--code-bg);color:var(--code-text);border-radius:8px;padding:6px 10px;margin:6px 0;}
.ac-verdict{font-size:13.5px;padding:8px 10px;border-radius:8px;margin:6px 0;}
.ac-verdict.ok{background:#ccfbf1;color:#134e4a;}.ac-verdict.no{background:#fee2e2;color:#7f1d1d;}
.ac-note{font-size:12.5px;color:#92400e;margin:4px 0;}
"""

setup = setup_section()


def load(name: str, rel: str):
    """A kit module loaded from its file under a name of the build's choosing."""
    spec = importlib.util.spec_from_file_location(name, KIT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ the kit's modules
for p in (str(KIT / "evals"), str(KIT / "services/chat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ["CHECKPOINT_DSN"] = "memory"           # agent.py's InMemorySaver, said out loud (its rule 4)
import desk_agent  # noqa: E402  - services/chat/desk_agent.py: LangChain, from the chat image's pins
import desk_graph  # noqa: E402
import desk_router  # noqa: E402
import limits  # noqa: E402
from langchain_core.tools import ToolException  # noqa: E402
from shared import desk_calc, desk_law, prices  # noqa: E402
import agent_eval  # noqa: E402  - evals/agent_eval.py: the lane's chunk of a clause
import combine  # noqa: E402
import paired  # noqa: E402
import route_eval  # noqa: E402
from commands import desk_ops  # noqa: E402

td = load("commands.tests.test_desk", "commands/tests/test_desk.py")      # the name the learner's unittest prints
tra = load("kit_test_route_arms_105", "evals/tests/test_route_arms.py")    # FIGURES: every row's figure, recomputed

DA, GR, DC, CD = ("services/chat/desk_agent.py", "services/chat/desk_graph.py", "shared/desk_calc.py",
                  "services/chat/desk.py")
TD, RE, CB, PD, MK = ("commands/tests/test_desk.py", "evals/route_eval.py", "evals/combine.py", "evals/paired.py",
                      "mk/agents.mk")

# ------------------------------------------------------------------ verbatim excerpts
TESTS = ("test_a_number_in_neither_the_passages_nor_the_message_is_refused",
         "test_a_codes_calculator_runs_only_on_its_codes_passage_and_its_own_desk",
         "test_a_model_error_is_the_direct_answer_under_the_same_limits")
EXCERPTS = {
    "agentanswer": (f"{GR} - _answer() and _agent_answer(): agent mode on a figure, the direct answer on a model error",
                    block(GR, "def _answer(desk: str, state: DeskState, runtime: Runtime) -> dict:") + "\n\n\n"
                    + block(GR, "def _agent_answer(desk: str, question: str, filt: list, state: DeskState, ctx: dict) -> dict:")),
    "toolsets": (f"{DA} - TOOLSETS: each desk's tools, and a refusal as an error result the model reads",
                 block(DA, "CALCULATORS = {t.name: t for t in (accrued_leave", end="the agents")),
    "tool": (f"{DA} - one calculator as the model sees it: its docstring is the tool's description",
             "@tool\n" + block(DA, "def encashable_days(balance: float, cap: float, runtime: ToolRuntime = None) -> dict:", n=8)),
    "calc": (f"{DA} - _calc(): the desk's list, the argument check, the Code's own text, then the arithmetic",
             block(DA, "def _calc(runtime, name: str, **args) -> dict:", end="@tool")),
    "calculators": (f"{DC} - CALCULATORS: each argument's one source",
                    block(DC, "# What each calculator is: its function; each argument's one source", end="_BAR = re.compile")),
    "checkargs": (f"{DC} - check_args(): every argument from where CALCULATORS says, or refused in words",
                  block(DC, "def check_args(name: str, args: dict, passages, message: str) -> tuple[list[str], dict]:",
                        end="# ------")),
    "clause": (f"{DC} - clause_text() and _in_clause(): a clause is its code's words, up to the next code",
               block(DC, "def clause_text(passage: dict, code: str) -> str:") + "\n\n\n"
               + block(DC, "def _in_clause(want: Decimal, codes, passages) -> dict | None:")),
    "numbers": (f"{DC} - numbers_in() and said(): how the check reads a text",
                block(DC, "def numbers_in(text: str) -> set[Decimal]:") + "\n\n\n"
                + block(DC, "def said(pattern: str, message: str) -> bool:")),
    "prompt": (f"{DA} - system_prompt(), DeskTurnLimits and agent(): the agent's rules, its limits, how it is built",
               block(DA, "def system_prompt(kind: str) -> str:", end="def _guard():") + "\n\n\n"
               + block(DA, "def agent(kind: str):")),
    "calcline": (f"{DA} - calc_line() and compose(): the lines code writes after the model's answer",
                 block(DA, "def calc_line(c: dict) -> str:") + "\n\n\n" + block(DA, "def compose(got: dict) -> str:")),
    "tests": (f"{TD} - three of the agent tests, on a scripted model and a table for rag-api",
              block(TD, f"    def {TESTS[0]}(self):", n=11) + "\n\n" + block(TD, f"    def {TESTS[1]}(self):", n=21)
              + "\n\n" + block(TD, f"    def {TESTS[2]}(self):", n=22)),
    "deskrow": (f"{CD} - _desk_row(): the one row a Desk turn logs",
                block(CD, "def _desk_row(surface: str, who: dict, session_id: str | None, mode: str, arm: str | None")),
    "deskstate": (f"{GR} - DeskState: what the Desk's thread checkpoints",
                  block(GR, "class DeskState(TypedDict, total=False):", n=11)),
    "citation": (f"{DA} - citation(): a passage as the section cites it",
                 block(DA, "def citation(p: dict) -> dict:")),
    "deskturn": (f"{RE} - desk_turn(): what a live run keeps of each desk turn",
                 block(RE, 'DESK_MEASURES = ("desk_model_calls"', n=1) + "\n\n\n"
                 + block(RE, "def desk_turn(desk: dict, latency_ms: float | None = None) -> dict:")),
    "paired": (f"{RE} - paired_lines() and the end of compare(): B against each arm, and why it is indicative",
               block(RE, "def paired_lines(other: dict, b: dict, name: str, what: str) -> list[str]:") + "\n    ...\n\n"
               + block(RE, '    held = {r["id"] for r in index_rows(load_rows(ROUTES_FILE))}', n=8)),
    "margin": (f"{PD} - the margin, written down before any run, and how an interval is read against it",
               block(PD, "MARGIN = 0.03", n=2) + "\n\n\n" + block(PD, "def verdict(lo: float, hi: float")),
    "vote": (f"{CB} - proposal() and vote(): what code returned, voted on; a tie goes to a person",
             block(CB, "def proposal(pred: dict) -> tuple | None:") + "\n\n\n"
             + block(CB, "def vote(proposals: dict[str, tuple | None]) -> tuple[tuple | None, int, str]:")),
    "aggregate": (f"{CB} - aggregate(): the scripted mixture-of-agents step, which writes new text",
                  block(CB, "def aggregate(answers: list[str]) -> str:")),
    "mk": (f"{MK} - route-eval's recipe passes ROUTES; route-compare and arms-combine",
           block(MK, "route-eval: guard-project", n=4) + "\n\n" + block(MK, "route-compare:", n=2, nth=2) + "\n\n"
           + block(MK, "arms-combine:", n=2, nth=2)),
}
assert EXCERPTS["calc"][1].rstrip().endswith("return result") and "refused, found = desk_calc.check_args(" in EXCERPTS["calc"][1]
assert EXCERPTS["toolsets"][1].rstrip().endswith('"astar": [retrieve_classes] + list(CALCULATORS.values())}')
assert EXCERPTS["tool"][1].rstrip().endswith('return _calc(runtime, "encashable_days", balance=balance, cap=cap)')
assert EXCERPTS["calculators"][1].rstrip().endswith("}") and '"needs": "code_on_social_security_2020"},' in EXCERPTS["calculators"][1]
assert EXCERPTS["checkargs"][1].rstrip().endswith("return refused, found")
assert EXCERPTS["clause"][1].rstrip().endswith("return None") and EXCERPTS["numbers"][1].rstrip().endswith(
    "for m in re.finditer(pattern, message, re.I))")
assert "class DeskTurnLimits(limits.TurnLimitsMiddleware):" in EXCERPTS["prompt"][1]
assert EXCERPTS["prompt"][1].rstrip().endswith("return built") and "checkpointer=False" in EXCERPTS["prompt"][1]
assert EXCERPTS["calcline"][1].rstrip().endswith("return text")
assert EXCERPTS["agentanswer"][1].rstrip().endswith('"refusals": got["refusals"], "stopped_by": got["stopped_by"]}, chips)')
assert EXCERPTS["tests"][1].count("    def test_") == 3 and EXCERPTS["tests"][1].rstrip().endswith(
    '([], limits.STOP_ANSWER, 0, "turn_budget"))')
assert EXCERPTS["deskrow"][1].rstrip().endswith('"prompt_version": rec["prompt_version"], "rules_version": rec["rules_version"]}')
assert EXCERPTS["deskstate"][1].rstrip().endswith("case_draft_id: str | None                   # the open draft, when the handler records one")
assert EXCERPTS["citation"][1].rstrip().endswith('"kind": p.get("kind") or "text", "doc_type": p.get("doc_type"), "section": p.get("section")}')
assert EXCERPTS["deskturn"][1].rstrip().endswith("return out")
assert EXCERPTS["paired"][1].rstrip().endswith("return 0") and "indicative, not a ship decision" in EXCERPTS["paired"][1]
assert EXCERPTS["margin"][1].rstrip().endswith('return "no conclusion at this many rows: the interval crosses the margin"')
assert EXCERPTS["vote"][1].rstrip().endswith('return ranked[0][0], ranked[0][1], ""')
assert EXCERPTS["aggregate"][1].rstrip().endswith('between the figures the answers give."')
assert "$(if $(ROUTES),--routes \"$(ROUTES)\",)" in EXCERPTS["mk"][1] and EXCERPTS["mk"][1].count("$(PY) evals/") == 3
assert "\nroute-compare:\n" in EXCERPTS["mk"][1] and "\narms-combine:\n" in EXCERPTS["mk"][1]

fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts, asserted
TOOL_NAMES = {k: [t.name for t in v] for k, v in desk_agent.TOOLSETS.items()}
assert TOOL_NAMES == {"handbook": ["retrieve", "accrued_leave", "carry_forward", "encashable_days", "notice_end"],
                      "statute": ["retrieve", "gratuity_estimate", "statutory_deadline", "threshold_check"],
                      "astar": ["retrieve"] + list(desk_calc.CALCULATORS)}, TOOL_NAMES
assert desk_agent.TOOLSETS["astar"][0] is desk_agent.retrieve_classes and desk_agent.TOOLSETS["handbook"][0] is desk_agent.retrieve_desk
PROMPT = desk_agent.system_prompt("handbook")
RULE = re.search(r"Give a calculator only numbers.*?say which one is missing\.", PROMPT).group(0)
KEPT = "Work every figure out with a calculator, never yourself."
assert KEPT + " " + RULE in PROMPT
assert (desk_agent.AGENT_MODEL, desk_agent.GEN_LOCATION, desk_agent.THINKING_LEVEL) == ("gemini-3.6-flash", "global", "low")
assert (desk_agent.TOP_K, desk_agent.QUOTE_CHARS) == (5, 500)
assert (limits.MAX_MODEL_CALLS, limits.TURN_BUDGET_INR, limits.TURN_DEADLINE_S) == (12, 5.0, 100.0)
assert desk_router.L1_MODEL == "gemini-3.1-flash-lite"
NOTES = desk_ops.load_notes(str(KIT / "evals/desk/clause_notes.acme.json"))
assert sorted(NOTES) == ["LV-01", "LV-07"]
HOLD = agent_eval._holdings()
assert "code_on_social_security_2020" in HOLD["acme"] and "code_on_social_security_2020" in HOLD["zeta"]
assert "code_on_social_security_2020" not in HOLD["globex"]

# ------------------------------------------------------------------ Level 0: the argument check, run here
ROWS = route_eval.load_rows(combine.ARMS_FILE)
RB = {r["id"]: r for r in ROWS}
TASKS = {r["id"]: r for r in map(json.loads, (KIT / "evals/agent_tasks.jsonl").read_text(encoding="utf-8").splitlines())}
NO_BALANCE = "I am an E3 and I am leaving. How many days of earned leave will be encashed?"
DAY_FIRST = "I am a confirmed E3 employee and my resignation was acknowledged in writing on 05/10/2026. What is my last day of notice?"
WRONG_CAP = TASKS["calc-encash-invented-cap"]["question"]
assert desk_calc.dates_in(DAY_FIRST) == desk_calc.dates_in(RB["fig-03"]["question"])
assert not desk_calc.numbers_in(NO_BALANCE)                     # "E3" is a grade, a name: no number in it


def task_call(tid: str) -> dict:
    """The one calculator call a row of evals/agent_tasks.jsonl expects."""
    (c,) = TASKS[tid]["calcs"]
    return dict(c["args"])


def fig_call(rid: str) -> dict:
    """The calculator call test_route_arms.py's FIGURES recomputes for a row of evals/route_arms.jsonl."""
    ((_, args, _),) = tra.FIGURES[rid][0]
    return dict(args)


# calculator -> (the argument whose value is chosen, its values, [(label, tenant, question, where from, the row's call
# or None when no call can pass, the call's other arguments)])
PANEL = {
    "encashable_days": ("cap", [45, 30, 60, 100, 7, 50], [
        ("jn-03: an E3 leaving with 50 days", "acme", RB["jn-03"]["question"], "evals/route_arms.jsonl, jn-03",
         fig_call("jn-03"), {"balance": 50}),
        ("a manager's cap of 100 days", "acme", WRONG_CAP, "evals/agent_tasks.jsonl, calc-encash-invented-cap",
         task_call("calc-encash-invented-cap"), {"balance": 80}),
        ("no balance given", "acme", NO_BALANCE, "this page's own", None, {"balance": 50})]),
    "carry_forward": ("cap", [30, 18, 31, 45, 1.75], [
        ("acme: 34 days left at the year's end", "acme", TASKS["calc-carry-forward"]["question"],
         "evals/agent_tasks.jsonl, calc-carry-forward", task_call("calc-carry-forward"), {"days": 34}),
        ("zeta: fig-05, the same 34 days", "zeta", RB["fig-05"]["question"], "evals/route_arms.jsonl, fig-05",
         fig_call("fig-05"), {"days": 34})]),
    "accrued_leave": ("per_month", [1.75, 30, 45, 8], [
        ("8 completed months", "acme", TASKS["calc-accrued"]["question"], "evals/agent_tasks.jsonl, calc-accrued",
         task_call("calc-accrued"), {"months": 8})]),
    "notice_end": ("days", [60, 15, 6, 30, 45], [
        ("fig-03: a confirmed E3", "acme", RB["fig-03"]["question"], "evals/route_arms.jsonl, fig-03",
         fig_call("fig-03"), {"ack_date": "2026-10-05"}),
        ("on probation", "acme", TASKS["calc-notice-probation"]["question"],
         "evals/agent_tasks.jsonl, calc-notice-probation", task_call("calc-notice-probation"), {"ack_date": "2026-10-05"}),
        ("fig-03, the date written day first", "acme", DAY_FIRST, "this page's own", fig_call("fig-03"),
         {"ack_date": "2026-10-05"})]),
    "gratuity_estimate": ("years", [7, 8, 5, 15], [
        ("fig-01: Rs 52,000, 7 years 8 months", "acme", RB["fig-01"]["question"], "evals/route_arms.jsonl, fig-01",
         fig_call("fig-01"), {"monthly_wage": 52000, "months": 8}),
        ("no years given", "acme", TASKS["refuse-gratuity-years"]["question"],
         "evals/agent_tasks.jsonl, refuse-gratuity-years", None, {"monthly_wage": 60000})]),
}
assert TASKS["refuse-gratuity-years"]["missing"] == "years" and task_call("refuse-gratuity-years") == {"monthly_wage": 60000}
PASSAGE_SETS = [("none: the turn has read nothing yet", []), ("LV-01", ["LV-01"]), ("LV-07", ["LV-07"]),
                ("NP-03", ["NP-03"]), ("PB-02", ["PB-02"]), ("NP-03, then LV-07", ["NP-03", "LV-07"]),
                ("s.53 of the Code on Social Security", ["s.53"])]
BOOK = {"acme": "hr_policy_2026.md", "zeta": "hr_policy_zeta_2026.md"}


def passage(tenant: str, code: str) -> dict:
    """One passage as the desk's agent reads it: the lane's handbook chunk of a clause, or s.53's sentences."""
    if code == "s.53":
        return {"chunk_id": f"{tenant}:code_on_social_security_2020#s.53", "page": 1, "doc_type": "statute",
                "source_uri": f"gs://documind-ai-YOUR-ID-uploads/{tenant}/code_on_social_security_2020.pdf",
                "kind": "text", "section": "s.53", "text": combine.PASSAGE}
    c = agent_eval.clause_chunk(tenant, code)
    assert c["source_uri"].endswith("/" + BOOK[tenant]) and c["doc_type"] == "policy", c
    return {"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "page": c["page_start"], "doc_type": "policy",
            "kind": "text", "section": c["section"], "text": c["text"]}


def ledger(tenant: str, codes) -> list:
    """The turn's ledger: the passages it read, numbered from 1 in the order it read them."""
    return [{"n": i, **passage(tenant, code)} for i, code in enumerate(codes, 1)]


def shown(v) -> str:
    """An argument as the call shows it: 50, 1.75, "2026-10-05"."""
    return json.dumps(v) if isinstance(v, str) else desk_calc.num(v)


def call_text(name: str, args: dict) -> str:
    """The call as the agent would make it."""
    return f"{name}({', '.join(f'{k}={shown(v)}' for k, v in args.items())})"


def run_calc(name: str, args: dict, tenant: str, codes, message: str):
    """desk_agent._calc() itself on a stand-in turn: (accepted, the calculator's line or the refusal's words)."""
    rt = types.SimpleNamespace(context={
        "desk_ledger": ledger(tenant, codes), "desk_message": message, "desk_calcs": [],
        "desk_tools": tuple(t.name for t in desk_agent.TOOLSETS[desk_calc.CALCULATORS[name]["desk"]])})
    try:
        result = desk_agent._calc(rt, name, **args)
    except ToolException as e:
        return False, str(e)
    line = desk_agent.calc_line(result)
    assert line.startswith("- ")
    return True, line[2:]


def reads(text: str) -> str:
    """The numbers and whole dates check_args reads in a text."""
    nums = sorted(desk_calc.numbers_in(text))
    days = sorted(desk_calc.dates_in(text))
    return (f"numbers: {', '.join(desk_calc.num(n) for n in nums) or 'none'}; "
            f"dates: {', '.join(d.isoformat() for d in days) or 'none'}")


def clause_reads(tenant: str, code: str) -> str:
    """What check_args may take from one passage."""
    if code == "s.53":
        return ("a statute passage: check_args takes no figure from it; it is the Code's own text, "
                "which lets a Code's calculator run")
    p = passage(tenant, code)
    nums = sorted(desk_calc.numbers_in(desk_calc.clause_text(p, code)))
    return f"numbers in its {code} clause: {', '.join(desk_calc.num(n) for n in nums) or 'none'}"


STR, VERDICTS = [], []


def sid(text: str) -> int:
    """The index of a string in the panel's table, added once."""
    if text not in STR:
        STR.append(text)
    return STR.index(text)


def vid(v: tuple) -> int:
    """The index of a verdict in the panel's table, added once."""
    if v not in VERDICTS:
        VERDICTS.append(v)
    return VERDICTS.index(v)


SPEC_WORDS = {desk_calc.MESSAGE: "the person's message"}
CALCS, KEY = [], {}
COUNT = Counter()
EDGE = []                                    # accepted calls with a figure the row does not expect
for name, (arg, values, questions) in PANEL.items():
    spec = desk_calc.CALCULATORS[name]
    parts_spec = [f"<code>{a}</code>: " + (SPEC_WORDS[s] if s == desk_calc.MESSAGE else
                                         f"{' or '.join(s)} of a handbook passage this turn read")
                  for a, s in spec["numbers"].items()]
    parts_spec += [f"<code>{a}</code>: the person's message (a date)" for a in spec["dates"]]
    parts_spec += [f"<code>{a}</code>: true only when the message says it" for a in spec.get("flags", {})]
    if spec["needs"]:
        parts_spec.append(f"runs only on a passage of the {html.escape(desk_law.STATUTES[spec['needs']]['title'])}")
    qs, calls, grid = [], [], []
    for label, tenant, question, src, expect, fixed in questions:
        row_calls, qgrid = [], []
        for value in values:
            args = {**fixed, arg: value}
            if name == "gratuity_estimate" and "months" in fixed:            # the call's order: wage, years, months
                args = {"monthly_wage": fixed["monthly_wage"], "years": value, "months": fixed["months"]}
            row_calls.append(call_text(name, args))
        for _, codes in PASSAGE_SETS:
            pgrid = []
            for value in values:
                args = {**fixed, arg: value}
                ok, text = run_calc(name, args, tenant, codes, question)
                if expect is None:
                    note = ("No call can pass on this question: the person has not given the "
                            f"{'balance' if name == 'encashable_days' else arg}, so the desk asks for it.")
                    assert not ok, (name, question, codes, value, text)
                elif ok and float(value) == float(expect[arg]):
                    note = "The call the kit's row expects."
                elif ok:
                    note = (f"Accepted, though the kit's row expects {arg} = {shown(expect[arg])}: the check shows "
                            "where a number is written, not what it stands for.")
                    EDGE.append((name, arg, value, tuple(codes), label))
                else:
                    note = ""
                COUNT["ok" if ok else "no"] += 1
                KEY[(name, label, tuple(codes), value)] = (ok, text)
                pgrid.append(vid((1 if ok else 0, sid(text), sid(note))))
            qgrid.append(pgrid)
        grid.append(qgrid)
        calls.append(row_calls)
        qs.append({"label": label, "text": question, "t": tenant, "src": src, "reads": reads(question),
                   "expect": call_text(name, expect) if expect else "none: the question does not give what it needs"})
    CALCS.append({"name": name, "arg": arg, "values": [shown(v) for v in values], "spec": " &middot; ".join(parts_spec),
                  "qs": qs, "calls": calls, "r": grid})
PASS = {t: [[{"sec": p["section"], "text": p["text"], "reads": clause_reads(t, code)}
             for code, p in ((c, passage(t, c)) for c in codes)] for _, codes in PASSAGE_SETS] for t in ("acme", "zeta")}
N_VERDICTS = COUNT["ok"] + COUNT["no"]


def verdict_of(name, label, codes, value):
    """A verdict the panel shows, for the build's own checks and the page's prose."""
    return KEY[(name, label, tuple(codes), value)]


JN, WC, NB = (q[0] for q in PANEL["encashable_days"][2])
ok, text = verdict_of("encashable_days", JN, ["NP-03", "LV-07"], 45)
assert ok and text.endswith("The balance from your message; the cap from LV-07 [2]. Condition: LV-07 bars encashment "
                            "during probation: this figure holds only once probation is over."), text
REFUSE_60 = verdict_of("encashable_days", JN, ["NP-03", "LV-07"], 60)[1]
assert REFUSE_60 == ("refused: cap = 60 is not written in LV-07 of a handbook passage this turn read: search for that "
                     "clause and use the figure it states"), REFUSE_60
REFUSE_100 = verdict_of("encashable_days", WC, ["LV-07"], 100)[1]
assert REFUSE_100.startswith("refused: cap = 100 is not written in LV-07") and verdict_of("encashable_days", WC, ["LV-07"], 45)[0]
REFUSE_BAL = verdict_of("encashable_days", NB, ["LV-07"], 45)[1]
assert REFUSE_BAL == ("refused: balance = 50 is a fact about the person that their message does not state: ask them for "
                      "it"), REFUSE_BAL
REFUSE_7 = verdict_of("encashable_days", JN, ["LV-07"], 7)[1]
assert REFUSE_7.startswith("refused: cap = 7 is not written in LV-07")
CF_A, CF_Z = (q[0] for q in PANEL["carry_forward"][2])
assert verdict_of("carry_forward", CF_Z, ["LV-01"], 18)[0] and not verdict_of("carry_forward", CF_Z, ["LV-01"], 30)[0]
assert verdict_of("carry_forward", CF_A, ["LV-01"], 30)[0] and not verdict_of("carry_forward", CF_A, ["LV-01"], 31)[0]
GR1, GR0 = (q[0] for q in PANEL["gratuity_estimate"][2])
ok, GRAT_OK = verdict_of("gratuity_estimate", GR1, ["s.53"], 7)
assert ok and "Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000" in GRAT_OK, GRAT_OK
REFUSE_CODE = verdict_of("gratuity_estimate", GR1, ["LV-07"], 7)[1]
assert REFUSE_CODE == ("refused: this calculator runs on the Code on Social Security, 2020, which no passage of this turn "
                       "holds: search for its section first"), REFUSE_CODE
REFUSE_FIVE = verdict_of("gratuity_estimate", GR1, ["s.53"], 5)[1]
assert REFUSE_FIVE.startswith("refused: years = 5 is a fact about the person that their message does not state")
NE1, NE2, NE3 = (q[0] for q in PANEL["notice_end"][2])
assert verdict_of("notice_end", NE3, ["NP-03"], 60)[0]                          # 05/10/2026 is read day first
assert "cites" not in verdict_of("notice_end", NE2, ["PB-02"], 15)[1] and "(PB-02, NP-03)" in verdict_of("notice_end", NE2, ["PB-02"], 15)[1]
# the check's edge, which the page names: a number written in the right source, standing for something else
EDGE_SEEN = {(n, v) for n, _, v, _, _ in EDGE}
assert {("accrued_leave", 30), ("notice_end", 6), ("gratuity_estimate", 8), ("carry_forward", 1.75)} <= EDGE_SEEN, EDGE_SEEN
ok, EDGE_ACCRUED = verdict_of("accrued_leave", PANEL["accrued_leave"][2][0][0], ["LV-01"], 30)
assert ok and EDGE_ACCRUED.startswith("Earned leave accrued (LV-01): 8 completed months x 30 days = 240 days."), EDGE_ACCRUED
ok, EDGE_NOTICE = verdict_of("notice_end", NE1, ["PB-02"], 6)
assert ok and "2026-10-05 + 6 days = 2026-10-11" in EDGE_NOTICE, EDGE_NOTICE
ok, EDGE_YEARS = verdict_of("gratuity_estimate", GR1, ["s.53"], 8)
assert ok and "8 years 8 months counts as 9 years" in EDGE_YEARS and "Rs 2,70,000" in EDGE_YEARS, EDGE_YEARS
N_EDGE = len(EDGE)
PB02_NUMS = clause_reads("acme", "PB-02")
assert PB02_NUMS == "numbers in its PB-02 clause: 3, 6, 15", PB02_NUMS
LV01_NUMS = clause_reads("acme", "LV-01")
assert LV01_NUMS == "numbers in its LV-01 clause: 1.75, 30", LV01_NUMS             # 31 December is a date
DATA = {"calcs": CALCS, "pass": PASS, "psets": [label for label, _ in PASSAGE_SETS], "v": VERDICTS, "s": STR}

# ------------------------------------------------------------------ the arms set
FIG_ROWS = [r["id"] for r in ROWS if tra.FIGURES[r["id"]][0]]
LOOK_ROWS = [r["id"] for r in ROWS if not tra.FIGURES[r["id"]][0]]
INDEXED = {r["id"] for r in route_eval.index_rows(route_eval.load_rows())}
SEEN = [r["id"] for r in ROWS if r["id"] in INDEXED]
NEW = [r["id"] for r in ROWS if r["source"] == "new"]
assert len(ROWS) == 12 and all(r["split"] == "dev" and r["expected_outcome"] == "answer" for r in ROWS)
assert FIG_ROWS == ["fig-01", "fig-02", "fig-03", "fig-05", "fig-06", "jn-03"] and len(SEEN) == 7 and NEW == FIG_ROWS[:5]
assert SEEN == ["jn-03"] + LOOK_ROWS and LOOK_ROWS == ["lk-01", "lk-04", "lk-06", "lk-07", "lk-17", "iso-01"]
assert RB["fig-03"]["must_contain"] == ["2026-12-04"] and RB["fig-05"]["must_contain"] == ["18", "16"]
assert RB["fig-06"]["must_contain"] == ["five years"] and RB["fig-06"]["must_not_contain"] == ["90,000"]
assert not route_eval.prompt_groups(ROWS)                    # the live run leaves no row out
BY_DESK = Counter(r["expected_route"] for r in ROWS)
BY_TENANT = Counter(r["tenant"] for r in ROWS)
assert BY_DESK == {"handbook": 8, "statute": 4} and BY_TENANT == {"acme": 10, "zeta": 2}


def least(gate: float, n: int) -> int:
    """The fewest rows of n that meet a dev gate, as gate_failures() compares (k / n under the gate fails)."""
    return next(k for k in range(n + 1) if not k / n < gate)


GATES = route_eval.DEV_GATES
MIN_ROUTE, MIN_HB, MIN_LAW = least(GATES["route"], 12), least(GATES["per_desk"], 8), least(GATES["per_desk"], 4)
assert (MIN_ROUTE, MIN_HB, MIN_LAW) == (12, 8, 4)
WILSON12 = route_eval.rate(12, 12)
SAME = paired.newcombe(12, 0, 0, 0)
SAME_VERDICT = paired.verdict(SAME[1], SAME[2], "C", "B")
assert SAME_VERDICT.startswith("no conclusion at this many rows")
# the fewest rows B alone gets right, with every other row right for both, that clear the margin
NONINF = next((k for k in range(13) if paired.verdict(*paired.newcombe(12 - k, 0, k, 0)[1:], "C", "B").startswith(
    "B non-inferior") or paired.verdict(*paired.newcombe(12 - k, 0, k, 0)[1:], "C", "B").startswith("B better")), None)
BETTER = next((k for k in range(13) if paired.verdict(*paired.newcombe(12 - k, 0, k, 0)[1:], "C", "B").startswith("B better")), None)
ONE_WRONG = paired.newcombe(11, 1, 0, 0)
assert NONINF is not None and BETTER is not None and NONINF <= BETTER


def pts(x: float) -> str:
    """A difference in points, signed, to one decimal."""
    return f"{100 * x:+.1f}"


ROW_TABLE = []
for r in ROWS:
    calls, looks = tra.FIGURES[r["id"]]
    decides = "; ".join([call_text(n, a) + (f", with {c}'s figure" if c else "") for n, a, c in calls]
                        + [f"{where} writes {fig}" if not where.startswith("gratuity") else f"s.53(2) writes “{fig}”"
                           for fig, where in looks])
    says = ", ".join(r["must_contain"]) + (f"; never {', '.join(r['must_not_contain'])}" if r["must_not_contain"] else "")
    ROW_TABLE.append(f'<tr><td><strong>{r["id"]}</strong></td><td data-label="Company, desk">{r["tenant"]}, '
                     f'{r["expected_route"]}</td><td data-label="What decides it"><code>{html.escape(decides)}</code></td>'
                     f'<td data-label="Must say">{html.escape(says)}</td><td data-label="In B\'s index">'
                     f'{"yes" if r["id"] in INDEXED else "no"}</td></tr>')

# ------------------------------------------------------------------ the cells
SA_FN = 'sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }'
ETOK_FN = ('etok() { gcloud auth print-identity-token --include-email --audiences="$CHAT" \\\n'
           '         --impersonate-service-account="$(sa "$1")"; }')


def heredoc(body: str, prefix: str = "") -> str:
    """A Python cell as the page shows it: pasted into bash."""
    return f"{prefix}python - <<'PY'\n{body}\nPY"


PASSAGES_PY = """import json, os, sys, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from shared import desk_calc
row = next(r for r in map(json.loads, open("evals/route_arms.jsonl", encoding="utf-8")) if r["id"] == "jn-03")


def passages(query):
    \"\"\"acme's handbook passages for a query: rag-api's POST /v1/passages as documind-ui-sa, no model call.\"\"\"
    body = {"query": query, "tenant_id": "acme", "user_id": "agent", "top_k": 5, "stream": False,
            "filters": {"doc_type": ["policy"]}, "brain": "desk"}
    req = urllib.request.Request(os.environ["API"] + "/v1/passages", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ["TOKEN"]})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r).get("passages") or []


read = [p for p in passages("earned leave encashed on exit") if p.get("doc_type") == "policy"]
for i, p in enumerate(read, 1):                       # numbered from 1, as the desk's agent numbers what it reads
    print(f"[{i}] {p['section']}: {' '.join(p['text'].split())[:72]}...")
for cap in (60, 45):
    refused, found = desk_calc.check_args("encashable_days", {"balance": 50, "cap": cap}, read, row["question"])
    if refused:
        print(f"cap = {cap}: refused: {' '.join(refused)}")
    else:
        print(f"cap = {cap}: accepted: the balance from the message, the cap from "
              f"{found['cap']['clause']} [{found['cap']['n']}]")"""

EDIT_PY = """from pathlib import Path
p = Path("services/chat/desk_agent.py")
lines = p.read_text(encoding="utf-8").split("\\n")
i = next(k for k, line in enumerate(lines) if "Give a calculator only numbers" in line)
print("before:", *(line.strip() for line in lines[i:i + 3]), sep="\\n  ")
lines[i:i + 3] = ['            "- Work every figure out with a calculator, never yourself.\\\\n"']
p.write_text("\\n".join(lines), encoding="utf-8")
print("after:", lines[i].strip(), sep="\\n  ")"""

REST_PY = """import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
row = next(r for r in map(json.loads, open("evals/route_arms.jsonl", encoding="utf-8")) if r["id"] == "jn-03")


def post(path, body):
    \"\"\"POST a JSON body to the chat service as evalacme: (status, reply).\"\"\"
    req = urllib.request.Request(os.environ["CHAT"] + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ["T_ACME"]})
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


for arm in ("B", "Astar"):
    status, b = post("/v1/desk", {"question": row["question"], "session_id": f"lesson105-{arm}", "arm": arm})
    if status != 200:
        print(f"arm {arm}: {status} {b.get('detail')}")
        continue
    print(f"arm {b['arm']}: route {b['route']}  method {b['method']}  outcome {b['outcome']}")
    print(f"  model_calls {b['model_calls']}  limits.cost_inr {b['limits']['cost_inr']}  retrieve_calls {b['retrieve_calls']}")
    for s in b["sections"]:
        print(f"  section {s['desk']}: mode {s['mode']}  tool_calls {s['tool_calls']}  refusals {s['refusals']}")
        for c in s.get("calculations") or []:
            args = ", ".join(f"{k}={v}" for k, v in c["args"].items())
            print(f"    {c['calculator']}({args}) = {c['value']} {c['unit']}  found {c['found']}")
    print(f"  the answer says {row['must_contain']}: {all(w in b['answer'] for w in row['must_contain'])}")"""

ROWS_PY = """import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND '
     f'jsonPayload.event="desk" AND timestamp>="{os.environ["SINCE105"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc",
                      "--limit", "20", "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j = e["jsonPayload"]
    who = "evalacme" if str(j["user"]).startswith("documind-evalacme-sa@") else "you"
    print(f"{who:8} mode {j['mode']}  arm {j['arm']:5} route {j['route']:9} method {j['method']:8} outcome {j['outcome']}")
    print(f"         model_calls {j['model_calls']}  tool_calls {j['tool_calls']}  refusals {j['refusals']}"
          f"  cost_usd {j['cost_usd']}  latency_ms {j['latency_ms']}")"""

TEST_CMD = ("# three of the Desk's agent tests: a scripted model, rag-api as a table; no lane, no model call, Rs 0\n"
            "OFFLINE=1 DOCUMIND_REQUIRE_LIBS=1 bash commands/agent-turn.sh -m unittest commands/tests/test_desk.py -v \\\n"
            "  -k test_a_number_in_neither -k test_a_codes_calculator -k test_a_model_error")
CELLS = {
    "notes": ('export SINCE105="$(date -u +%FT%TZ)" UI="https://documind-ui-$NUMBER.$REGION.run.app"\n'
              'make desk PROJECT="$PROJECT" TENANT=acme NOTES=evals/desk/clause_notes.acme.json\n'
              'echo "the Desk page: $UI"'),
    "passages": heredoc(PASSAGES_PY, 'TOKEN="$(tok "$API")" '),
    "tests": TEST_CMD,
    "edit": heredoc(EDIT_PY) + "\ngit status --short services/chat/",
    "tests2": TEST_CMD,
    "turns": ('make agent-turn PROJECT="$PROJECT" REGION="$REGION" DESK=handbook TENANT=acme \\\n'
              f'  Q="{RB["jn-03"]["question"]}"\n'
              'make agent-turn PROJECT="$PROJECT" REGION="$REGION" DESK=handbook TENANT=acme \\\n'
              f'  Q="{NO_BALANCE}"'),
    "restore": ("git checkout -- services/chat/desk_agent.py\n"
                "git status --short services/chat/     # prints nothing: the rule is back"),
    "rest": ('export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"\n' + SA_FN + "\n" + ETOK_FN + "\n"
             + heredoc(REST_PY, 'T_ACME="$(etok evalacme)" ')),
    "rows": (heredoc(ROWS_PY) + '\nmake thread PROJECT="$PROJECT" EMAIL="$(sa evalacme)" | sed -n \'1,6p\''
             "   # its label, then the latest threads first"),
    "evalb": ('mkdir -p "$HOME/arms"\n'
              'make route-eval PROJECT="$PROJECT" REGION="$REGION" ROUTES=evals/route_arms.jsonl ARM=B \\\n'
              '  SAVE="$HOME/arms/arms_B.jsonl" REPORT="$HOME/arms/arms_B.json"'),
    "evalc": ('make route-eval PROJECT="$PROJECT" REGION="$REGION" ROUTES=evals/route_arms.jsonl ARM=C \\\n'
              '  SAVE="$HOME/arms/arms_C.jsonl" REPORT="$HOME/arms/arms_C.json"'),
    "evala": ('make route-eval PROJECT="$PROJECT" REGION="$REGION" ROUTES=evals/route_arms.jsonl ARM=Astar \\\n'
              '  SAVE="$HOME/arms/arms_Astar.jsonl" REPORT="$HOME/arms/arms_Astar.json"'),
    "compare": 'make route-compare REPORTS="$HOME/arms/arms_B.json $HOME/arms/arms_C.json $HOME/arms/arms_Astar.json"',
    "selftest": "python evals/combine.py --selftest --layers 2      # scripted members: no model call, Rs 0",
    "combine": 'make arms-combine SAVES="$HOME/arms/arms_B.jsonl $HOME/arms/arms_C.jsonl $HOME/arms/arms_Astar.jsonl"',
    "kittests": ("python -m unittest discover -s evals/tests -p test_route_arms.py\n"
                 "python -m unittest discover -s evals/tests -p test_combine.py"),
}
CELL_LABELS = {
    "notes": "acme's clause notes, and the time this lesson starts",
    "passages": "your lane's passages for LV-07, then check_args with cap 60, then 45 (Rs 0)",
    "tests": "three agent tests, offline",
    "edit": "the Change-it: delete the prompt's rule, in your checkout only",
    "tests2": "the same three tests, with the rule gone",
    "turns": "two agent turns on your lane, with the rule gone",
    "restore": "put the rule back",
    "rest": "jn-03 to POST /v1/desk as evalacme, on arm B, then arm Astar",
    "rows": "the Desk's rows since step 3, then evalacme's threads",
    "evalb": "arm B, the routed Desk, on the twelve rows",
    "evalc": "arm C, code only, on the same rows",
    "evala": "arm Astar, one agent, on the same rows",
    "compare": "the three reports side by side (Rs 0)",
    "selftest": "the combiners on scripted members (Rs 0)",
    "combine": "the three saved runs as an ensemble (Rs 0)",
    "kittests": "lesson 10.5's own tests, offline",
}

# ------------------------------------------------------------------ the offline outputs, run here
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
       "CHECKPOINT_DSN": "memory", "DOCUMIND_REQUIRE_LIBS": "1"}


def unittest_shape(text: str) -> str:
    """unittest's output with its timing masked, as the page shows it."""
    text = re.sub(r"^[.sxEF]+\n", "", text, flags=re.M)
    return re.sub(r"Ran (\d+) tests? in [\d.]+s", r"Ran \1 tests in N.NNNs", text)


def run_tests(module) -> str:
    """The three agent tests, run in this process: unittest's verbose output."""
    suite = unittest.TestSuite(module.GraphTests(n) for n in sorted(TESTS))
    buf = io.StringIO()
    result = unittest.TextTestRunner(stream=buf, verbosity=2).run(suite)
    assert result.wasSuccessful(), buf.getvalue()
    return unittest_shape(buf.getvalue())


OUT_TESTS = run_tests(td)
assert OUT_TESTS.count(" ... ok\n") == 3 and "Ran 3 tests in N.NNNs" in OUT_TESTS and OUT_TESTS.rstrip().endswith("OK")
assert "(commands.tests.test_desk.GraphTests.test_a_number_in_neither" in OUT_TESTS

# the Change-it, on a copy: the cell's own code edits it, and the tests run in a subprocess that imports the copy
T = Path(tempfile.mkdtemp(prefix="lesson105-"))
(T / "services/chat").mkdir(parents=True)
shutil.copy(KIT / DA, T / DA)
here = os.getcwd()
os.chdir(T)
try:
    with redirect_stdout(io.StringIO()) as buf:
        exec(compile(EDIT_PY, "<cell>", "exec"), {"__name__": "__cell__"})
finally:
    os.chdir(here)
EDITED = (T / DA).read_text(encoding="utf-8")
compile(EDITED, DA, "exec")
assert "Give a calculator only numbers" not in EDITED and '"- Work every figure out with a calculator, never yourself.\\n"' in EDITED
assert len(EDITED.splitlines()) == len((KIT / DA).read_text(encoding="utf-8").splitlines()) - 2
OUT_EDIT = buf.getvalue() + " M services/chat/desk_agent.py\n"
RUNNER = """import importlib.util, os, sys, unittest, warnings
warnings.filterwarnings("ignore")
T, KIT = sys.argv[1], sys.argv[2]
sys.path[:0] = [os.path.join(T, "services", "chat"), os.path.join(KIT, "services", "chat"), KIT]
spec = importlib.util.spec_from_file_location("commands.tests.test_desk", os.path.join(KIT, "commands", "tests", "test_desk.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
import desk_agent
assert os.path.abspath(desk_agent.__file__).startswith(os.path.abspath(T)), desk_agent.__file__
assert "Give a calculator only numbers" not in desk_agent.system_prompt("handbook")
result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(
    unittest.TestSuite(mod.GraphTests(n) for n in sorted(sys.argv[3:])))
sys.exit(0 if result.wasSuccessful() else 1)
"""
proc = subprocess.run([sys.executable, "-c", RUNNER, str(T), str(KIT), *TESTS], capture_output=True, text=True,
                      encoding="utf-8", env=ENV, cwd=str(KIT))
assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
OUT_TESTS2 = unittest_shape(proc.stdout)
assert OUT_TESTS2 == OUT_TESTS, (OUT_TESTS2, OUT_TESTS)
shutil.rmtree(T, ignore_errors=True)

# a Desk turn on the kit's own graph, with test_desk.py's stand-ins: what its thread checkpoints
td.GraphTests.setUpClass()
STAND = td.GraphTests(TESTS[0])
STAND.setUp()
STAND.passages = [{"n": 1, **passage("acme", "LV-07")}, {"n": 1, **passage("acme", "NP-03")}]
STAND_LLM = STAND.script(td.asks("retrieve", query="earned leave encashed on exit"),
                         td.asks("encashable_days", balance=80, cap=100),
                         td.asks("encashable_days", balance=80, cap=45),
                         td.said("45 of your 80 days are encashed on exit [1]."))
dec, rctx = STAND.decided(WRONG_CAP, td.l1("handbook", calc=True))
assert dec["needs_calculation"] and dec["route"] == "handbook"
TURN = STAND.g.run_turn(STAND.graph, dec, STAND.turn_ctx(meter=rctx["meter"], clause_notes=NOTES), STAND.config)
STATE = STAND.graph.get_state(STAND.config).values
SEC = STATE["sections"][0]
((ERR_NAME, _, ERR_TEXT),) = td.tool_results(STAND_LLM, "error")
STAND.doCleanups()
assert [m.type for m in STATE["messages"]] == ["human", "ai"] and STATE["last_question"] == WRONG_CAP
assert (SEC["mode"], SEC["tool_calls"], SEC["refusals"]) == ("agent", ["retrieve", "encashable_days", "encashable_days"], ["encashable_days"])
assert ERR_TEXT == REFUSE_100, ERR_TEXT
(CALC,) = SEC["calculations"]
assert (CALC["value"], CALC["args"], CALC["found"]) == (45.0, {"balance": 80.0, "cap": 45.0}, {"balance": "your message", "cap": "LV-07 [1]"})
assert [n["clause"] for n in SEC["notes"]] == ["LV-07"] and all(len(c["quote"]) <= desk_agent.QUOTE_CHARS for c in SEC["citations"])
assert "capped at 45" not in json.dumps([m.content for m in STATE["messages"]]) and TURN["outcome"] == "answer"
THREAD = STAND.config["configurable"]["thread_id"]
cites = "; ".join(f"[{c['n']}] {c['section']}, quote {len(c['quote'])} characters" for c in SEC["citations"])
OUT_STATE = "\n".join([
    f"graph.get_state() on the thread {THREAD}, after one turn of the wrong-cap question",
    f"  messages        {', '.join(m.type for m in STATE['messages'])}: the masked question and the reply; no passage, "
    f"no tool call, no argument",
    f"  last_route      {STATE['last_route']}",
    f"  sections[0]     desk {SEC['desk']}, mode {SEC['mode']}, retrieve_calls {SEC['retrieve_calls']}, answerable "
    f"{SEC['answerable']}",
    f"    tool_calls    {SEC['tool_calls']}",
    f"    refusals      {SEC['refusals']}",
    f"    calculations  {call_text(CALC['calculator'], {k: int(v) for k, v in CALC['args'].items()})} = "
    f"{desk_calc.num(CALC['value'])} {CALC['unit']}, found {CALC['found']}",
    f"    citations     {cites}",
    f"    notes         {', '.join(n['clause'] for n in SEC['notes'])}",
    "the refused call, as the agent read it:",
    f"  {ERR_NAME}: {ERR_TEXT}"])

# combine.py --selftest --layers 2, and lesson 10.5's own test files
buf = io.StringIO()
assert combine.selftest(2, out=buf) == 0
OUT_SELFTEST = buf.getvalue()
assert "unsupported: 2,25,000; 1 model call" in OUT_SELFTEST and "the aggregator 2 (one a layer)" in OUT_SELFTEST
assert OUT_SELFTEST.count("\nok    ") == 5 and "the row goes to a person; 0 model calls" in OUT_SELFTEST
AGG = re.search(r'layer 1 +the aggregator reads 3 answers and writes "(About Rs [\d,]+)', OUT_SELFTEST).group(1)
assert AGG == "About Rs 2,25,000", AGG
EDGE_KINDS = Counter("person" if (n == "notice_end" and v in (15, 60)) else "role" for n, _, v, _, _ in EDGE)
assert EDGE_KINDS == {"role": 7, "person": 4}, EDGE_KINDS
KITTESTS = []
for pattern in ("test_route_arms.py", "test_combine.py"):
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "evals/tests", "-p", pattern],
                          capture_output=True, text=True, encoding="utf-8", env=ENV, cwd=str(KIT))
    assert proc.returncode == 0, proc.stderr[-3000:]
    KITTESTS.append(unittest_shape(proc.stdout + proc.stderr))
OUT_KITTESTS = "".join(KITTESTS)
N_KITTESTS = [int(n) for n in re.findall(r"Ran (\d+) tests", OUT_KITTESTS)]
assert N_KITTESTS == [21, 12], N_KITTESTS

# ------------------------------------------------------------------ the windows
RECORDED = {"deskpage": "desk_page.txt", "passages": "passages_check.txt", "turns": "turn_changeit.txt",
            "rest": "rest_arms.txt", "rows": "desk_rows.txt", "evalb": "arms_B.txt", "evalc": "arms_C.txt",
            "evala": "arms_Astar.txt", "compare": "arms_compare.txt", "combine": "arms_combine.txt"}
OUT = {k: pb.recorded(LESSON, name) for k, name in RECORDED.items()}
OUT.update({"tests": OUT_TESTS, "edit": OUT_EDIT, "tests2": OUT_TESTS2, "restore": "(no output)",
            "selftest": OUT_SELFTEST, "kittests": OUT_KITTESTS})
OUT_LABELS = {
    "deskpage": "make desk, then the two answers as the Desk page shows them (the author's run)",
    "passages": "output (the author's run)",
    "tests": "output (run when this page was built)",
    "edit": "output (run when this page was built, on a copy of the file)",
    "tests2": "output (run when this page was built, on the edited copy)",
    "turns": "output, both turns (the author's run)",
    "restore": "output",
    "rest": "output (the author's run)",
    "rows": "output (the author's run)",
    "evalb": "output (the author's run)",
    "evalc": "output (the author's run)",
    "evala": "output (the author's run)",
    "compare": "output (the author's run)",
    "selftest": "output (run when this page was built)",
    "combine": "output (the author's run)",
    "kittests": "output (run when this page was built)",
}
LEAK = re.compile(r"AppData|site-packages|[A-Za-z]:[\\/](?:Users|Program|netsetos)|lesson105-[a-z0-9_]{6,}")
for k in ("tests", "edit", "tests2", "selftest", "kittests"):
    assert not LEAK.search(OUT[k]), (k, LEAK.search(OUT[k]).group(0))
assert not LEAK.search(OUT_STATE)


def bash_window(label: str, code: str) -> str:
    """A command window with a copy button."""
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    """An expected output, read only."""
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
WIN["OUT_STATE"] = ('<div class="cw"><div class="ch-bar"><span>output of a stand-in turn on the kit\'s own graph, run when '
                    'this page was built (a scripted model, not your lane)</span><span class="ro">read only</span></div>'
                    '<pre tabindex="0">' + html.escape(OUT_STATE, quote=False) + "</pre></div>\n")

# ------------------------------------------------------------------ the widget
UI_JS = r"""var D = %s, $ = function(id){ return document.getElementById(id); };
function fill(sel, items){ sel.innerHTML = ''; items.forEach(function(t, i){ var o = document.createElement('option'); o.value = String(i); o.textContent = t; sel.appendChild(o); }); }
function line(cls, text){ var p = document.createElement('p'); p.className = cls; p.textContent = text; return p; }
function calc(){ return D.calcs[+$('ac-calc').value]; }
function choose(){ var c = calc(); fill($('ac-q'), c.qs.map(function(q){ return q.label; })); fill($('ac-v'), c.values); $('ac-arg').textContent = 'The value of ' + c.arg; render(); }
function render(){
  var c = calc(), qi = +$('ac-q').value, pi = +$('ac-p').value, vi = +$('ac-v').value, q = c.qs[qi];
  $('ac-spec').innerHTML = c.spec;
  $('ac-words').textContent = q.text;
  $('ac-mreads').textContent = 'From ' + q.src + ', ' + q.t + '. check_args reads ' + q.reads + '.';
  var box = $('ac-pass'); box.innerHTML = '';
  var ps = D.pass[q.t][pi];
  if(!ps.length){ box.appendChild(line('ac-reads', 'No passage: nothing this turn read can be a source.')); }
  ps.forEach(function(p, i){ var d = document.createElement('div'); d.className = 'ac-pass'; var b = document.createElement('b'); b.textContent = '[' + (i + 1) + '] ' + p.sec + ' (' + q.t + ')'; d.appendChild(b); d.appendChild(document.createTextNode('\n' + p.text)); box.appendChild(d); box.appendChild(line('ac-reads', p.reads)); });
  $('ac-call').textContent = c.calls[qi][vi];
  var v = D.v[c.r[qi][pi][vi]], out = $('ac-verdict');
  out.className = 'ac-verdict ' + (v[0] ? 'ok' : 'no');
  out.textContent = (v[0] ? 'Accepted. The line under the answer: ' : 'Refused. The error result the model reads: ') + D.s[v[1]];
  $('ac-note').textContent = D.s[v[2]];
  $('ac-expect').textContent = 'The kit’s row expects: ' + q.expect;
}
fill($('ac-calc'), D.calcs.map(function(c){ return c.name; }));
fill($('ac-p'), D.psets);
$('ac-calc').addEventListener('change', choose);
['ac-q', 'ac-p', 'ac-v'].forEach(function(id){ $(id).addEventListener('change', render); });
choose();
$('ac-p').value = '5'; $('ac-v').value = '2'; render();
""" % json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))
assert CALCS[0]["name"] == "encashable_days" and PASSAGE_SETS[5][1] == ["NP-03", "LV-07"] and PANEL["encashable_days"][1][2] == 60
JS = "<script>\n(function(){\n'use strict';\n" + UI_JS.replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

# ------------------------------------------------------------------ the numbers the prose states
E = lambda v: html.escape(str(v), quote=False)  # noqa: E731


def and_join(items: list) -> str:
    """Items as prose: "3, 6 and 15"."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]
WORDS = {0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
         10: "ten", 11: "eleven", 12: "twelve"}
L1_IN = len(desk_router.prompt(RB["jn-03"]["question"])) // 4
CALL_IN, CALL_OUT = 3000, 300                    # an illustration: the price of one flash call of this size


def rs(model: str, tokens_in: int, tokens_out: int) -> float:
    """Rupees for one call at list price (shared/prices.py)."""
    return prices.inr(prices.usd(model, tokens_in, tokens_out))


CALL = rs(desk_agent.AGENT_MODEL, CALL_IN, CALL_OUT)          # one agent call: prompt, tools, passages so far, thinking
DIRECT = rs(desk_agent.AGENT_MODEL, 2000, 300)                # one rag-api answer, the course's typical answer
L1 = rs(desk_router.L1_MODEL, L1_IN, 30)                      # the classifier's call
AGENT = (3 * CALL + L1, 4 * CALL + L1)                        # a figure in agent mode: search, calculator, answer (+1)
N_FIG, N_LK = len(FIG_ROWS), len(LOOK_ROWS)
COSTS = {                                                     # the run list's estimates, low and high
    "desk_page.txt": (2 * AGENT[0], 2 * AGENT[1]),
    "turn_changeit.txt": (2 * 3 * CALL, 2 * 4 * CALL),        # make agent-turn runs the agent alone: no router
    "rest_arms.txt": (AGENT[0] + 3 * CALL, AGENT[1] + 4 * CALL),
    "arms_B.txt": (N_FIG * AGENT[0] + N_LK * (DIRECT + L1) + 12 * L1, N_FIG * AGENT[1] + N_LK * (DIRECT + L1) + 12 * L1),
    "arms_C.txt": (12 * DIRECT, 12 * DIRECT),
    "arms_Astar.txt": (N_FIG * 3 * CALL + N_LK * 2 * CALL, N_FIG * 4 * CALL + N_LK * 3 * CALL),
}
RUN_LO, RUN_HI = sum(lo for lo, _ in COSTS.values()), sum(hi for _, hi in COSTS.values())
GLOBEX_HOLDS = " and the ".join(desk_law.STATUTES[k]["title"] for k in sorted(HOLD["globex"]))
STATS = {
    "MODEL": desk_agent.AGENT_MODEL, "THINKING": desk_agent.THINKING_LEVEL, "TOP_K": str(desk_agent.TOP_K),
    "QUOTE": str(desk_agent.QUOTE_CHARS), "MAXCALLS": str(limits.MAX_MODEL_CALLS),
    "BUDGET": f"{limits.TURN_BUDGET_INR:g}", "DEADLINE": f"{limits.TURN_DEADLINE_S:g}", "L1_MODEL": desk_router.L1_MODEL,
    "TOOLS_HB": ", ".join(f"<code>{t}</code>" for t in TOOL_NAMES["handbook"]),
    "TOOLS_LAW": ", ".join(f"<code>{t}</code>" for t in TOOL_NAMES["statute"]),
    "N_TOOLS_ASTAR": str(len(TOOL_NAMES["astar"])), "N_CALCULATORS": WORDS[len(desk_calc.CALCULATORS)],
    "N_HB_CALCS": WORDS[len(desk_calc.for_desk("handbook"))], "N_LAW_CALCS": WORDS[len(desk_calc.for_desk("statute"))],
    "RULE": E(RULE), "KEPT": E(KEPT), "NOTE_CODES": " and ".join(sorted(NOTES)), "NOTE_LIST": E(json.dumps(sorted(NOTES))),
    "JN03": E(RB["jn-03"]["question"]), "WRONGCAP": E(WRONG_CAP), "NOBAL": E(NO_BALANCE),
    "REFUSE_60": E(REFUSE_60), "REFUSE_100": E(REFUSE_100), "REFUSE_BAL": E(REFUSE_BAL), "REFUSE_CODE": E(REFUSE_CODE),
    "REFUSE_FIVE": E(REFUSE_FIVE), "REFUSE_7": E(REFUSE_7),
    "N_VERDICTS": str(N_VERDICTS), "N_ACCEPT": str(COUNT["ok"]), "N_REFUSE": str(COUNT["no"]), "N_EDGE": str(N_EDGE),
    "N_EDGE_ROLE": str(EDGE_KINDS["role"]), "N_EDGE_PERSON": str(EDGE_KINDS["person"]),
    "EDGE_ACCRUED": E(re.search(r"8 completed months x 30 days = 240 days", EDGE_ACCRUED).group(0)),
    "EDGE_NOTICE": E(re.search(r"2026-10-05 \+ 6 days = 2026-10-11", EDGE_NOTICE).group(0)),
    "EDGE_YEARS": E(re.search(r"8 years 8 months counts as 9 years[^;]*", EDGE_YEARS).group(0)),
    "PB02_NUMS": E(and_join(PB02_NUMS.split(": ")[1].split(", "))),
    "LV01_NUMS": E(and_join(LV01_NUMS.split(": ")[1].split(", "))),
    "WILSON12_LO": re.search(r"\[([\d.]+%),", WILSON12).group(1),
    "N_ROWS": str(len(ROWS)), "N_ROWS_W": WORDS[len(ROWS)], "N_CALC": str(len(FIG_ROWS)), "N_CALC_W": WORDS[len(FIG_ROWS)],
    "N_LOOK": str(len(LOOK_ROWS)), "N_LOOK_W": WORDS[len(LOOK_ROWS)], "N_NEW_W": WORDS[len(NEW)], "N_SEEN": str(len(SEEN)),
    "N_SEEN_W": WORDS[len(SEEN)], "N_HB": str(BY_DESK["handbook"]), "N_LAW": str(BY_DESK["statute"]),
    "N_ACME": str(BY_TENANT["acme"]), "N_ZETA_W": WORDS[BY_TENANT["zeta"]],
    "ROW_TABLE": "\n".join(ROW_TABLE),
    "GATE_ROUTE": f"{GATES['route']:.0%}", "GATE_DESK": f"{GATES['per_desk']:.0%}", "MIN_ROUTE": str(MIN_ROUTE),
    "MIN_HB": str(MIN_HB), "MIN_LAW": str(MIN_LAW), "WILSON12": E(WILSON12),
    "SAME_LO": pts(SAME[1]), "SAME_HI": pts(SAME[2]), "SAME_VERDICT": E(SAME_VERDICT),
    "ONE_LO": pts(ONE_WRONG[1]), "ONE_HI": pts(ONE_WRONG[2]),
    "NONINF": str(NONINF), "BETTER": str(BETTER), "NONINF_W": WORDS[NONINF], "BETTER_W": WORDS[BETTER],
    "MARGIN": f"{100 * paired.MARGIN:g}", "MARGIN_REG": "8 October 2026",
    "AGG": E(AGG), "LAYERS_MAX": str(combine.LAYERS_MAX), "N_ARMS_TESTS": str(N_KITTESTS[0]), "N_COMBINE_TESTS": str(N_KITTESTS[1]),
    "QSEC": E(SEC["citations"][0]["section"]), "THREAD": E(THREAD),
    "CALL_IN": f"{CALL_IN:,}", "CALL_OUT": str(CALL_OUT),
    "CALL_INR": f"{prices.inr(prices.usd(desk_agent.AGENT_MODEL, CALL_IN, CALL_OUT)):.2f}",
    "DIRECT_INR": f"{prices.inr(prices.usd(desk_agent.AGENT_MODEL, 2000, 300)):.2f}",
    "L1_INR": f"{L1:.3f}", "AGENT_LO": f"{AGENT[0]:.2f}", "AGENT_HI": f"{AGENT[1]:.2f}",
    "RATIO_LO": WORDS[round(AGENT[0] / DIRECT)], "RATIO_HI": WORDS[round(AGENT[1] / DIRECT)],
    "RUN_LO": f"{math.floor(RUN_LO)}", "RUN_HI": f"{math.ceil(RUN_HI)}", "GLOBEX_HOLDS": E(GLOBEX_HOLDS),
    "TURN_LO": f"{3 * CALL:.1f}", "TURN_HI": f"{4 * CALL:.1f}", "N_ROWS_CAP": WORDS[len(ROWS)].capitalize(),
    "COST_B": f"{COSTS['arms_B.txt'][0]:.0f} to {COSTS['arms_B.txt'][1]:.0f}", "COST_C": f"{COSTS['arms_C.txt'][0]:.0f}",
    "COST_A": f"{COSTS['arms_Astar.txt'][0]:.0f} to {COSTS['arms_Astar.txt'][1]:.0f}",
}
assert STATS["CALL_INR"] == f"{CALL:.2f}" and STATS["DIRECT_INR"] == f"{DIRECT:.2f}"
assert paired.MARGIN_REGISTERED == "2026-10-08" and STATS["MARGIN"] == "3"
assert STATS["N_ROWS"] == "12" and STATS["MIN_ROUTE"] == "12"


if os.environ.get("CELLS_ONLY"):                 # for the author: the computed outputs and numbers, no page
    for k in ("tests", "edit", "tests2", "selftest", "kittests"):
        print(f"===== {k}\n{OUT[k]}")
    print(f"===== state\n{OUT_STATE}")
    print("===== edge", *EDGE, sep="\n")
    print("===== costs", *(f"{k}: Rs {lo:.2f} to {hi:.2f}" for k, (lo, hi) in COSTS.items()),
          f"total Rs {RUN_LO:.2f} to {RUN_HI:.2f}; a call Rs {CALL:.4f}, direct Rs {DIRECT:.4f}, L1 Rs {L1:.4f} "
          f"({L1_IN} tokens in)", sep="\n")
    print({k: v for k, v in STATS.items() if k != "ROW_TABLE"})
    sys.exit(0)


def subst(text: str) -> str:
    """Every %%NAME%% of a part, filled from the windows and the numbers."""
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    assert "%%" not in text, re.findall(r"%%\w+%%", text)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: _calc() on {N_VERDICTS} calls ({COUNT['ok']} accepted, {COUNT['no']} refused, {N_EDGE} at the check's edge); "
      f"3 agent tests, twice; one stand-in Desk turn; combine --selftest --layers 2; {sum(N_KITTESTS)} K-10.5 tests")
