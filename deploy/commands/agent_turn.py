#!/usr/bin/env python3
"""make agent-turn: one turn of an agent pattern, printed whole (workshop lessons 10.1-10.3 and 10.5).

    python commands/agent_turn.py --offline [--pattern loop|react_text|plan_first|plan_execute|rewoo|verify]
                                  [--desk astar|handbook|statute] [--thinking minimal|low|medium|high] [--tenant acme]
                                  [--question "..." | --row ID] [--json] [--invent ["Rs 2,50,000"]]
                                  [--launder ["Rs 2,40,000"]] [--exec-model gemini-3.1-flash-lite]    # Rs 0
    python commands/agent_turn.py --live ...         # one real turn on your lane: commands/agent-turn.sh sets it up

It prints each model call - the thinking level it was sent with, its input, thinking and visible tokens and its
rupees - then the tools that call asked for, with their arguments, and what each returned (a search's passages by n,
file and section; a calculator's figure and formula; a refusal's words), then the answer as the Desk shows it (the
model's text, then the lines code writes, desk_agent.compose()), the totals, and the figure check: every figure in the
model's text is a calculator's, the question's or a passage's (desk_calc.unsupported()). The patterns are
commands/agent_patterns.py's. The default question is the gratuity row of evals/agent_tasks.jsonl: Rs 52,000 a month
after 7 years 8 months. A model's text beside its tool calls is printed (plan_first's plan); for react_text, each call
prints the Thought and Action lines the model wrote, what the parser cut from them, and the Observation code wrote.

--invent (offline, react_text, lesson 10.1's Change-it): the scripted model writes on past its calculator's Action, an
Observation of its own (default "Rs 2,50,000") and a Final Answer from it, as a model does whose stop sequence does
not hold. The parser's cut keeps it out; with that line deleted, the invention is the answer and the figure check flags
it. (For verify, below, --invent is its first attempt's figure.)

plan_execute and rewoo (lesson 10.2) print the plan as the planner wrote it, then each step (plan_execute: its
executor call and the tools it ran, a refused or failed step and the replan after it) or each wave (rewoo: the steps
that ran together, each extract's figure and quote, a step that never ran and why), the answer's call, and the calls,
tokens and rupees by role, each role with its model. --exec-model runs their act and extract calls on another model
(gemini-3.1-flash-lite, priced at its own rates). --row asks a row of evals/agent_tasks.jsonl, as chained-exit-e3: a
chained row's three figures.

verify (lesson 10.3) prints each attempt, a turn of its own: a retry's reflect call and the note it wrote (cut at 300
characters by code, into the attempt's system prompt, never its question) with any figure the note writes, the loop's
calls and tools, the attempt's answer and the figure check's verdict (code, no model); then which attempt's answer
ships. Offline, for its cells: --invent ["Rs 2,50,000"] makes the first attempt write that figure in place of its
calculator's, which the check fails and the second attempt, after a note, corrects; --launder ["Rs 2,40,000"] makes
every note carry that figure and each later attempt write it as its own, with no calculator (the first attempt writes
the row's figure itself, so that a note is written): the check fails each, since a note is never a source.

--offline: a scripted model and the kit's own corpus, so every count is the script's (agent_patterns.py says how it
counts); the turn never slips. --live needs the lane's environment, which commands/agent-turn.sh exports:
GOOGLE_CLOUD_PROJECT (the model's project), RAG_API_URL (rag-api, for /v1/passages) and DOCUMIND_IMPERSONATE_SA (the
account a shell mints rag-api's ID token as: documind-ui-sa, which every tenant's roster holds). A live turn is a few
gemini-3.6-flash calls on location global, under the chat service's limits of 12 calls and Rs 5 (verify's, those limits
for each of its attempts). --json prints the turn's record as one JSON object instead.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_patterns as ap  # noqa: E402
from shared import desk_calc  # noqa: E402

# langchain-core's check of a tool's input serialises the ToolRuntime the desk's tools take, and pydantic warns about
# the context in it, once a tool call: the Desk's own turns do the same. The warning says nothing about the turn.
warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)
DEFAULT_ROW = "calc-gratuity-7y8m"
LIVE_ENV = ("GOOGLE_CLOUD_PROJECT", "RAG_API_URL", "DOCUMIND_IMPERSONATE_SA")


def _args(args: dict) -> str:
    return ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in (args or {}).items())


def _figure(result: dict) -> str:
    unit, value = result.get("unit"), result.get("value")
    if unit == "INR":
        return desk_calc.inr(value) if value is not None else "no figure"
    if unit == "days":
        return f"{desk_calc.num(value)} days"
    if unit == "yes/no":
        return "yes" if value else "no"
    return str(value)


def _result(tool: dict) -> list[str]:
    """What one tool returned, in a line or a few."""
    r = tool.get("result") or {}
    if tool["status"] == "error" or "error" in r:
        text = " ".join(str(r.get("error") or r.get("text") or "").split())
        return [f"refused: {text.removeprefix('refused: ')[:300]}"]      # check_args' own word once (13 October 2026)
    if tool["name"] == "retrieve":
        found = r.get("passages") or []
        out = [f"{len(found)} passage{'' if len(found) == 1 else 's'}" + ("" if r.get("answerable") else ", not answerable")
               + (f" ({r['note']})" if r.get("note") else "")]
        out += [f"  [{p.get('n')}] {p.get('source')}" + (f", {p['section']}" if p.get("section") else f" ({p.get('doc_type')})")
                for p in found]
        return out
    if "value" in r:
        return [f"= {_figure(r)}: {r.get('formula')}"]
    return [json.dumps(r, ensure_ascii=False)[:300]]


def _wrote(text: str) -> list[str]:
    """A model's text beside its tool calls (plan_first's plan), in a line or a few."""
    lines = [line.strip() for line in (text or "").strip().splitlines() if line.strip()]
    if len(lines) == 1:
        return [f"  the model wrote: {lines[0]}"]
    return ["  the model wrote:"] + [f"    {line}" for line in lines]


def _react(step: dict) -> list[str]:
    """One react_text call: the lines code read of what the model wrote, what the cut dropped, then the Action code ran
    and the Observation it wrote, or the answer."""
    react = step["react"]
    out = [f"  {line.rstrip()}" for line in react["read"].splitlines() if line.strip()]
    if react.get("cut"):
        out.append("  cut by the parser, which reads nothing from the first \"Observation:\" on:")
        out += [f"    | {line.rstrip()}" for line in react["cut"].splitlines() if line.strip()]
    if react.get("error"):
        out.append(f"  {ap.STOP} {react['error']}    <- written by code: no Action it could run")
    for tool in step["tools"]:
        out.append(f"  -> code runs {tool['name']}({_args(tool['args'])}); the Observation it writes:")
        out += ["       " + line for line in _result(tool)]
    if "final" in react:
        out.append("  -> no tool: the Final Answer is the answer")
    return out


def _call(c: dict) -> str:
    """A planning pattern's model call: its role, model, thinking level, tokens and rupees."""
    return (f"model call {c['n']} ({c.get('role')}, {c['model']}, thinking {c['thinking_level']}): in {c['tokens_in']:,}, "
            f"thinking {c['thinking_tokens']:,}, visible {c['visible_tokens']:,} tokens, Rs {c['inr']:.4f}")


ROLES_OF = {"plan_execute": ("plan, replan and solve", "act"), "rewoo": ("plan and solve", "extract")}


def plan_body(turn: dict, calls: dict) -> list[str]:
    """Lesson 10.2's turn, from its plan's log: the plan as written, then each step (plan_execute: its executor call,
    the tools it ran and what each returned, a replan after a refused or failed step) or each wave (rewoo: the steps
    run together, each extract's figure and quote, a step that never ran), then the answer's call."""
    out = []
    for e in (turn.get("plan") or {}).get("log") or ():
        c = calls.get(e.get("call"))
        if e["event"] == "plan" and "refused" in e:            # rewoo's
            out += [_call(c), "  the plan, written once:"]
            out += [f"    {s['id']} = {s['tool']}[{json.dumps(s['args'], ensure_ascii=False)}]" for s in e["steps"]]
            if e["refused"]:
                out.append(f"  refused before any tool ran: {e['refused']}")
        elif e["event"] in ("plan", "replan"):
            out.append(_call(c))
            if e["event"] == "replan":
                out.append(f"  after: {e['why']}")
            out.append(("  the plan:" if e["event"] == "plan" else "  the plan for the work still to do:")
                       + ("" if e["steps"] else " no numbered step"))
            out += [f"    {i}. {s}" for i, s in enumerate(e["steps"], 1)]
        elif e["event"] == "step":
            out += [f"step {e['n']}: {e['text']}", "  " + _call(c)]
            for tool in e.get("tools") or ():
                out.append(f"  -> {tool['name']}({_args(tool['args'])})")
                failed = tool["status"] != "error" and (tool.get("result") or {}).get("error")
                out += ([f"       failed: {' '.join(str(failed).split())[:300]}"] if failed else
                        ["       " + line for line in _result(tool)])
            if "tools" in e and not e["tools"]:
                out.append(f"  -> no tool call; the executor wrote: {' '.join((e.get('wrote') or '(nothing)').split())}")
            if e.get("status") not in (None, "done"):
                out.append(f"  the step was {e['status']}")
        elif e["event"] == "wave":
            ids = [s["id"] for s in e["steps"]]
            out.append(f"wave {e['n']}: {', '.join(ids)}" + (", together" if len(ids) > 1 else ""))
            for s in e["steps"]:
                if s["tool"] == ap.EXTRACT:
                    out.append(f"  {s['id']} = extract({_args(s['args'])})")
                    if calls.get(s.get("call")):
                        out.append("    " + _call(calls[s["call"]]))
                    out.append(f"       = {s['value']}, quoting \"{s['quote']}\"" if s.get("state") == "ok"
                               else f"       refused: {s.get('why')}")
                    continue
                filled = s["written"] != s["args"]
                out.append(f"  {s['id']} = {s['tool']}({_args(s['written'])})"
                           + (f", run as {s['tool']}({_args(s['args'])})" if filled else ""))
                if s.get("state") == "failed":          # an error the tool returned, as a search cut at its budget
                    out.append(f"       failed: {' '.join(str(s['result'].get('error') or '').split())[:300]}")
                elif "result" in s:
                    out += ["       " + line for line in _result({"name": s["tool"], "status": s.get("status"),
                                                                  "result": s["result"]})]
        elif e["event"] == "skip":
            out.append(f"  {e['id']} never ran: {e['why']}")
        elif e["event"] == "solve":
            out += [_call(c), "  -> no tool: the answer, from the steps' results"]
        elif e["event"] == "stop":
            out.append(f"the turn's limits stopped it before its {e['before']} call")
    return out


def role_lines(turn: dict) -> list[str]:
    """Lesson 10.2's totals: calls and rupees by role, each with its model, and how the plans went."""
    plan, roles = turn.get("plan") or {}, turn.get("roles") or {}
    out = ["by role: " + "; ".join(f"{role} {r['calls']} call{'' if r['calls'] == 1 else 's'}, Rs {r['inr']:.4f} "
                                   f"({r['model']})" for role, r in roles.items())]
    if "replans" in plan:
        out.append(f"plans: {len(plan.get('plans') or ())} written, {plan['replans']} "
                   f"replan{'' if plan['replans'] == 1 else 's'} (at most {ap.MAX_REPLANS} a turn)")
    if "waves" in plan:
        out.append(f"the plan was refused before any tool ran: {plan['refused']}" if plan.get("refused") else
                   f"waves: {len(plan['waves'])} ({' | '.join(', '.join(w) for w in plan['waves'])})")
    return out


def step_lines(step: dict, calls: dict) -> list[str]:
    """One model message of a turn's trace: its call's thinking level, tokens and rupees, then its text beside its tool
    calls, each tool call with its arguments and what it returned, or the answer; a react_text step as _react()."""
    c = calls.get(step["call"])
    if c is None:
        return [f"the turn's limits stopped it: {step['text']}"]
    out = [f"model call {c['n']} (thinking {c['thinking_level']}): in {c['tokens_in']:,}, thinking "
           f"{c['thinking_tokens']:,}, visible {c['visible_tokens']:,} tokens, Rs {c['inr']:.4f}"]
    if "react" in step:
        return out + _react(step)
    if step["text"] and step["tools"]:
        out += _wrote(step["text"])
    for tool in step["tools"]:
        out.append(f"  -> {tool['name']}({_args(tool['args'])})")
        out += ["       " + line for line in _result(tool)]
    if not step["tools"]:
        out.append("  -> no tool: the answer")
    return out


def check_body(turn: dict, calls: dict) -> list[str]:
    """Lesson 10.3's turn, attempt by attempt: a retry's reflect call and the note it wrote, with any figure the note
    writes; the loop's calls and tools; the attempt's answer and the figure check's verdict; then which attempt's
    answer ships."""
    out = []
    for a in turn.get("attempts") or ():
        out.append(f"attempt {a['n']}: the loop, a turn of its own" + (", after a note" if a["n"] > 1 else ""))
        for c in turn["calls"]:
            if c.get("attempt") == a["n"] and c.get("role") == "reflect":
                out += [_call(c), f"  the note, cut to {ap.NOTE_CHARS} characters by code, into this attempt's system "
                                  f"prompt, never its question: {a.get('note') or '(none)'}"]
        if a.get("note_figures"):
            out.append(f"  the note writes {', '.join(a['note_figures'])}: a note is never a source, so check_args "
                       "refuses it as an argument and the figure check flags it in an answer")
        for step in a.get("trace") or ():
            out += step_lines(step, calls)
        out += [f"  the attempt's answer: {' '.join((a.get('answer') or '(none)').split())}",
                f"  the figure check, code and no model: {ap.said_check(a['check'])}"]
    out.append(f"the answer that ships: attempt {turn.get('shipped')}'s, "
               + ("the first the figure check passed" if (turn.get("check") or {}).get("passed") else
                  f"the last of {ap.MAX_ATTEMPTS}: the figure check passed none"))
    return out


def render(turn: dict, offline: bool, invents: str | None = None, launders: str | None = None) -> str:
    da = ap._da()
    desk, thinking = turn["desk"], turn["thinking"]
    classes = ap.classes_for(desk)
    tools = [t.name for t in da.TOOLSETS[desk]]
    out = [f"agent turn: pattern {turn['pattern']}, desk {desk}, tenant {turn['tenant']}",
           f"  the desk: one retrieve over {', '.join(classes)}, and {len(tools) - 1} calculators: {', '.join(tools[1:])}",
           f"  thinking: {thinking}, sent with every call" if thinking else
           f"  thinking: {da.THINKING_LEVEL}, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)"]
    pat = ap.pattern(turn["pattern"])
    if pat.name != "loop":
        out.append(f"  {pat.name} (lesson {pat.lessons}): {pat.what}")
    if pat.executor:
        plan, (big, small) = turn.get("plan") or {}, ROLES_OF.get(pat.name, ("plan", "act"))
        out.append(f"  the planner: {plan.get('planner')} ({big}); the executor: {plan.get('executor')} ({small}; "
                   "EXEC_MODEL= names another)")
    if offline:
        level = thinking or da.THINKING_LEVEL
        out.append("  OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the "
                   f"script's: {ap.CHARS_PER_TOKEN} characters a token, {ap.SCRIPTED_THINKING[level]} thinking tokens a call "
                   f"at {level}")
        if invents and pat.checked:
            out.append(f"  --invent: the scripted model's first attempt writes {invents} in place of its calculator's "
                       "figure")
        elif invents:
            out.append(f"  --invent: past its calculator's Action the scripted model writes \"{ap.STOP} {invents}\" "
                       "and a Final Answer from it, as a model does whose stop sequence does not hold")
        if launders:
            out.append(f"  --launder: each note the scripted model writes carries {launders}, and each later attempt "
                       "writes it as its own figure, with no calculator" + ("" if invents else "; its first attempt "
                                                                            "writes the row's figure itself"))
    if pat.checked:
        out.append(f"  the figure check: code, no model (figure_check(): desk_calc.unsupported() over the attempt's "
                   f"calculations, question and passages, every [n] a passage read, no stop); at most "
                   f"{ap.MAX_ATTEMPTS} attempts, each a turn of its own, a note of at most {ap.NOTE_CHARS} characters "
                   "before each retry")
    out += [f"question: {turn['question']}", ""]
    calls = {c["n"]: c for c in turn["calls"]}
    if pat.executor:
        out += plan_body(turn, calls)
    if pat.checked:
        out += check_body(turn, calls)
    for step in ([] if pat.executor or pat.checked else turn["trace"]):
        out += step_lines(step, calls)
    for c in turn["calls"]:
        if c.get("error"):
            out.append(f"model call {c['n']} failed: {c['error']}")
    out += ["", "answer, as the Desk shows it (the model's text, then what code writes):"]
    out += ["  " + line if line else "" for line in (turn["composed"] or "(no answer)").splitlines()]
    flagged = desk_calc.unsupported(turn["answer"], turn["calculations"], turn["question"],
                                    *[p.get("text") or "" for p in turn["passages"]])
    import limits
    unread = sum(bool((s.get("react") or {}).get("error")) for s in turn["trace"])
    tried = len(turn.get("attempts") or ())
    reflects = sum(c.get("role") == "reflect" for c in turn["calls"])
    out += ["", (f"{turn['model_calls']} model calls in {tried} attempt{'' if tried == 1 else 's'} and {reflects} "
                 f"reflect call{'' if reflects == 1 else 's'} ({limits.MAX_MODEL_CALLS} at most an attempt); the "
                 f"answer that ships: " if pat.checked else
                 f"{turn['model_calls']} model calls ({limits.MAX_MODEL_CALLS} at most), ")
                + f"{turn['retrieve_calls']} search{'' if turn['retrieve_calls'] == 1 else 'es'}, "
                f"{len(turn['calculations'])} calculation{'' if len(turn['calculations']) == 1 else 's'}, "
                f"{len(turn['refusals'])} refused or failed tool call{'' if len(turn['refusals']) == 1 else 's'}"
                + (f", {unread} format error{'' if unread == 1 else 's'}" if pat.text else "")
                + f"; stopped by {turn['stopped_by'] or 'nothing'}",
            f"tokens: in {turn['tokens_in']:,}, thinking {turn['thinking_tokens']:,}, visible {turn['visible_tokens']:,}; "
            f"Rs {turn['inr']:.4f} for the model calls at list price, Rs {turn['rag_inr']:.4f} for rag-api"
            + (" (the script's tokens: nothing is billed)" if offline else ""),
            "figure check: " + ("every figure in the model's text is a calculator's, the question's or a passage's "
                                "(desk_calc.unsupported: none)" if not flagged else
                                f"no calculator, question or passage wrote {', '.join(flagged)} (desk_calc.unsupported)")]
    if pat.executor or pat.checked:
        out[-1:-1] = role_lines(turn)
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap_ = argparse.ArgumentParser(description="One turn of an agent pattern, printed whole (make agent-turn).")
    mode = ap_.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline", action="store_true", help="a scripted model and the kit's corpus: Rs 0")
    mode.add_argument("--live", action="store_true", help="one real turn on your lane (commands/agent-turn.sh)")
    ap_.add_argument("--pattern", default="loop", help=f"built: {', '.join(ap.PATTERNS)}"
                                                       + (f"; planned: {', '.join(ap.PLANNED)}" if ap.PLANNED else ""))
    ap_.add_argument("--desk", default="astar", choices=("astar", "handbook", "statute"))
    ap_.add_argument("--thinking", choices=ap.THINKING_LEVELS, help="unset: the desk agent's own, low")
    ap_.add_argument("--tenant", help="unset: acme, or the row's tenant with --row")
    ap_.add_argument("--question", help="unset: the gratuity row of evals/agent_tasks.jsonl")
    ap_.add_argument("--row", metavar="ID", help="a row of evals/agent_tasks.jsonl, by id: its question")
    ap_.add_argument("--json", action="store_true", help="the turn's record as JSON")
    ap_.add_argument("--invent", nargs="?", const="Rs 2,50,000", metavar="OBSERVATION",
                     help="offline react_text: the model writes its own Observation past its stop sequence; offline "
                          "verify: its first attempt writes this figure in place of its calculator's")
    ap_.add_argument("--launder", nargs="?", const="Rs 2,40,000", metavar="FIGURE",
                     help="offline verify: each note carries this figure, and each later attempt writes it as its own")
    ap_.add_argument("--exec-model", choices=ap.EXEC_MODELS,
                     help="plan_execute and rewoo: their act and extract calls' model (unset: the planner's)")
    a = ap_.parse_args(argv)
    try:
        ap.pattern(a.pattern)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if a.invent is not None and not (a.offline and (ap.pattern(a.pattern).text or ap.pattern(a.pattern).checked)):
        print("ERROR: --invent is for --offline --pattern react_text, where the scripted text model invents the "
              "Observation, or verify, where its first attempt invents the figure", file=sys.stderr)
        return 2
    if a.launder is not None and not (a.offline and ap.pattern(a.pattern).checked):
        print("ERROR: --launder is for --offline --pattern verify: the scripted model's notes carry the figure",
              file=sys.stderr)
        return 2
    if a.exec_model and not ap.pattern(a.pattern).executor:
        print(f"ERROR: --exec-model is for {', '.join(n for n, p in ap.PATTERNS.items() if p.executor)}: the "
              f"{a.pattern} pattern makes every call on one model", file=sys.stderr)
        return 2
    rows = {r["id"]: r for r in ap.tasks()}
    if (a.row and a.question) or (a.row and a.row not in rows):
        print(f"ERROR: --row names one row of evals/agent_tasks.jsonl ({', '.join(rows)}), in place of --question",
              file=sys.stderr)
        return 2
    question = a.question or rows[a.row or DEFAULT_ROW]["question"]
    a.tenant = a.tenant or (rows[a.row]["tenant"] if a.row else "acme")
    if a.live:
        missing = [k for k in LIVE_ENV if not os.environ.get(k)]
        if missing:
            print(f"ERROR: --live needs {', '.join(missing)}: run make agent-turn PROJECT=<id>, which sets them "
                  f"(commands/agent-turn.sh), or --offline for the scripted turn", file=sys.stderr)
            return 2
    try:
        if a.offline:
            with ap.offline():
                llm = ap.scripted(question, a.tenant, pattern=a.pattern, invents=a.invent, launders=a.launder)
                executor = ap.scripted(question, a.tenant, pattern=a.pattern, model=a.exec_model) if a.exec_model else None
                turn = ap.run(a.pattern, question, llm=llm, desk=a.desk, thinking=a.thinking, tenant=a.tenant,
                              executor=executor)
        else:
            turn = ap.run(a.pattern, question, llm=ap.gemini(), desk=a.desk, thinking=a.thinking, tenant=a.tenant,
                          executor=ap.gemini(a.exec_model) if a.exec_model else None)
    except Exception as e:                                   # noqa: BLE001 - the turn failed: say how, exit 1
        print(f"the turn failed: {type(e).__name__}: {' '.join(str(e).split())[:300]}", file=sys.stderr)
        return 1
    print(json.dumps(turn, ensure_ascii=False, indent=1) if a.json else render(turn, a.offline, a.invent, a.launder))
    return 0


if __name__ == "__main__":
    sys.exit(main())
