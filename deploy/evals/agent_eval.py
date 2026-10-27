#!/usr/bin/env python3
"""The agent bench's eval (workshop lessons 10.1-10.3 and 10.5): one task set, scored one way for every agent pattern,
thinking level and desk, offline or on a lane.

    python evals/agent_eval.py --check                                      # Rs 0, stdlib: the task set is sound
    python evals/agent_eval.py --offline [--patterns loop] [--thinking low,high] [--runs 3] [--slice calc]
                                         [--desk astar|row|handbook|statute] [--best-of 3] [--save runs.jsonl]
                                         [--exec-model default,gemini-3.1-flash-lite]
    python evals/agent_eval.py --live ...                                   # your lane: make agent-eval sets it up
    python evals/agent_eval.py --replay runs.jsonl [more.jsonl] [--best-of 3]   # Rs 0: saved runs, rescored
    python evals/agent_eval.py --compare low.jsonl high.jsonl               # Rs 0: two saved arms, paired

THE TASK SET, evals/agent_tasks.jsonl, one row a question:

    {id, kind, tenant, desk, question, calcs, expected, unit, clause, rule, wrong, search, of, tags, note}
    refuse rows add {missing, invented, says}
    chained rows are {id, kind, tenant, desk, question, parts, of, tags, note}, each part
    {calcs, expected, unit, clause, rule, wrong, search} as a calc row's, and stated when the question states a figure
    for an argument a clause must give

    kind      calc     a figure a calculator works out from the question and a clause (desk_calc.CALCULATORS)
              lookup   a figure a clause states, one hop, no arithmetic
              trap     a calc row whose figure the clause also writes, so a copied figure is right without a calculator
              refuse   a figure the question cannot give: the answer names the missing input and states no figure
              chained  several figures in one question (lesson 10.2), from both desks (desk astar), each a search and
                       then its calculator; no figure feeds another calculator, since check_args takes a calculator's
                       inputs from the question or a clause only. stated is a figure the question states that is not
                       the clause's (a manager's cap): check_args refuses it, so a plan that takes it meets a refusal
    expected  the figure (a number, a date YYYY-MM-DD, true or false), recomputed by desk_calc in --check; null on refuse
    clause    the clause or section the figure rests on; rule the desk_calc.RULES key quoting a Code's words
    wrong     figures a right answer never states: the other count, the wrong clause's figure, another company's
    search    the words the scripted model searches with (OFFLINE only); of the golden row asking the same question

--check needs no model and no lane. For every row: the hard gate (shared/desk_rules.gate) lets the question through and
the router masks nothing in it, since a gated question never reaches an agent; a calc or trap row's arguments pass
desk_calc.check_args against the question and the clause's own chunk (as shared/documind_corpus.py mints it), its
calculator runs on the right desk and on a Code the tenant holds, and calculate() returns the expected figure citing
the row's clause; a lookup's figure is written in its clause; a trap's figure is also the clause's own; a refuse row's
calculator cannot run on what the question states and check_args refuses the input a model might invent; no wrong
figure is the expected one or in the question; a golden row's must_contain holds the figure; a chained row's every part
passes as a calc row of its calculator's desk on the row's question, and check_args refuses each stated figure. Then
desk_calc's selftest, which holds every RULES quote to its corpus lines.

SCORING. The answer scored is the model's own text, never desk_agent.compose()'s "Worked out in code" lines, which code
writes from the calculator and so always agree with it.

    correct     the expected figure is stated (a number in digits or words, a date in any form desk_calc reads; the
                one yes/no row by an unnegated "must", "required", "yes") and no wrong figure is; a refuse row
                names its missing input, states no figure without a source, and no calculator worked one out; a
                chained row, every part's figure stated and no part's wrong figure
    provenance  calc and trap: a call of the row's calculator returned the expected figure, and
                desk_calc.unsupported() finds no figure in the answer that a calculator, the question or a passage the
                turn read did not write; lookup: a passage of the row's clause holding the figure was read, and
                unsupported() finds nothing; refuse: unsupported() finds nothing; chained: every part's calculator
                returned its figure, and unsupported() finds nothing
    verified    correct, with its provenance
    tokens      each model call's input, thinking and visible tokens and its rupees (agent_patterns' recorder)

A row is scored on every run; the rates with a Wilson interval are over each row's first run. pass@k is the chance at
least one of k runs passes, pass^k that all k do (the unbiased estimates over each row's n runs, averaged over rows),
for correct and for verified. --best-of N keeps one of a row's first N runs, chosen without the expected figure - a run
the check passes first (commands/agent_patterns.py's figure_check(), verify's critic: no unsupported figure, every [n]
a passage the run read, no stop; a failed run never passes), then a calculator's figure stated, then the earliest - so
the choice never reads the expected figure; an arm with fewer runs a row than N says so instead. Two arms in one run,
or --compare, print the paired difference on each row's first run, correct and verified: Newcombe's interval and an
exact McNemar test (evals/paired.py), read against its pre-registered margin.

CHECK, RETRY OR CHOOSE (lesson 10.3). A verify arm's run is its answer that ships, scored as any run; its report adds on
which attempt the figure check passed, the attempts, reflect calls and notes a run, the notes that write a figure (a
note is never a source: each is refused or flagged), and the ceiling, a row with any attempt correct. With verify and
another arm in the same records (one run, or one --replay of several saves), the three ways print side by side, each
with its calls and rupees a row: that arm's pass@1 (its first run), pass@k re-rolls (any of its first k runs correct:
the ceiling a perfect chooser reaches) and best-of-k (the run the figure check chooses), k being --best-of or its runs
a row; verify's pass@3 with notes, the answer it ships; then the check's precision, the runs and attempts it passes
that are correct. All of it rescores saved runs, so --replay prints it at Rs 0.

THE RUNS. Every row through every arm: each pattern of --patterns (commands/agent_patterns.py) at each level of
--thinking (comma-separated; default is the desk agent's own, low), on --desk (astar, the default: one agent with every
class and calculator; row: each row's own desk), --runs times. --inproc, the default and so far the only way, runs the
patterns in this process: --offline on the scripted model and the kit's corpus (Rs 0; every count is the script's, and
the script slips on about one run in five, agent_patterns.py says how), --live on Gemini and the lane's rag-api, which
make agent-eval sets up (commands/agent-turn.sh): a few gemini-3.6-flash calls a row and run. --save keeps every run,
one JSON line each, with its passages by file name, so --replay rescores it at Rs 0 and --compare pairs two arms.

THE EXECUTOR (lesson 10.2). --exec-model (comma-separated; default is the planner's own model) runs plan_execute and
rewoo once for each executor model named, their act and extract calls on it (agent_patterns' EXEC_MODELS: gemini-3.1-
flash-lite the cheaper one); the other patterns run once, as they are. Each of their arms adds a line of calls and
rupees a run by role, each role with its model, and one of how its plans went: runs replanned, plans refused before any
tool ran, waves a run.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import os
import re
import sys
import warnings
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
for _p in (str(KIT), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import paired  # noqa: E402
from shared import desk_calc, desk_rules  # noqa: E402

# The model's tools check their input with pydantic, which warns about the ToolRuntime context once a tool call.
warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)

TASKS = HERE / "agent_tasks.jsonl"
GOLDEN = HERE / "golden.jsonl"
MANIFEST = HERE / "manifest.json"
FIELDS = ("id", "kind", "tenant", "desk", "question", "calcs", "expected", "unit", "clause", "rule", "wrong", "search",
          "of", "tags", "note")
REFUSE_FIELDS = ("missing", "invented", "says")
CHAINED_FIELDS = ("id", "kind", "tenant", "desk", "question", "parts", "of", "tags", "note")
PART_FIELDS = ("calcs", "expected", "unit", "clause", "rule", "wrong", "search")
KINDS = ("calc", "lookup", "trap", "refuse", "chained")
ROLES = ("plan", "act", "extract", "replan", "solve")     # a planning pattern's calls, as agent_patterns.ROLES
UNITS = ("INR", "days", "date", "yes/no", "years", "days a month")
DESKS = ("handbook", "statute")
ROW_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
YES = r"\b(?:yes|must|required|mandatory|obliged|obligatory|has\s+to|have\s+to|needs?\s+to)\b"
_CITE = re.compile(r"\[\d+(?:\s*[,-]\s*\d+)*\]")


def _jsonl(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_tasks(path=TASKS) -> list[dict]:
    return _jsonl(path)


# --------------------------------------------------------------------- figures
def _value(v, unit: str):
    if unit == "date":
        return date.fromisoformat(str(v))
    if unit == "yes/no":
        return bool(v)
    return Decimal(str(v)).normalize()


def same(value, want, unit: str) -> bool:
    """A calculator's value is the row's figure."""
    if value is None or want is None:
        return value is None and want is None
    try:
        return _value(value, unit) == _value(want, unit)
    except (ValueError, ArithmeticError):
        return False


def states(text: str, value, unit: str) -> bool:
    """The text states the figure: a number in digits or words (desk_calc.numbers_in, lakh and 40,000 read), a date as
    desk_calc.dates_in reads one, or for yes/no an unnegated yes, must or required (desk_calc.said)."""
    text = _CITE.sub(" ", text or "")
    if unit == "yes/no":
        return desk_calc.said(YES, text) == bool(value)
    if unit == "date":
        return _value(value, unit) in desk_calc.dates_in(text)
    return _value(value, unit) in desk_calc.numbers_in(text)


def _stem(name) -> str:
    return str(name or "").rsplit("/", 1)[-1].rsplit(".", 1)[0]


def rests_on(row: dict, passage: dict) -> bool:
    """The passage is the row's clause and holds its figure: a handbook clause's own words (desk_calc.clause_text), or
    a window of the Code the row's rule quotes."""
    want = _value(row["expected"], row["unit"])
    if row["rule"]:
        file = desk_calc.RULES[row["rule"]]["file"]
        return (_stem(passage.get("source") or passage.get("source_uri")) == _stem(file)
                and want in desk_calc.numbers_in(passage.get("text") or ""))
    return want in desk_calc.numbers_in(desk_calc.clause_text(passage, row["clause"]))


def score(row: dict, run: dict) -> dict:
    """{correct, provenance, unsupported, why} for one run of one row."""
    answer, calcs = run.get("answer") or "", run.get("calculations") or []
    flagged = desk_calc.unsupported(answer, calcs, run.get("question") or row["question"],
                                    *[p.get("text") or "" for p in run.get("passages") or ()])
    unit, want, why = row.get("unit"), row.get("expected"), []
    if row["kind"] == "chained":                 # each part as a calc row: every figure stated, every one a calculator's
        correct = by_all = True
        for part in row["parts"]:
            names = {c["calculator"] for c in part["calcs"]}
            label = ", ".join(sorted(names))
            stated = states(answer, part["expected"], part["unit"])
            wrong = [w for w in part["wrong"] if states(answer, w, part["unit"])]
            by = any(c.get("calculator") in names and same(c.get("value"), part["expected"], part["unit"]) for c in calcs)
            correct, by_all = correct and stated and not wrong, by_all and by
            if not by:
                why.append(f"no {label} call returned it")
            if not stated:
                why.append(f"{label}: the figure is not stated")
            if wrong:
                why.append(f"{label}: states " + ", ".join(str(w) for w in wrong))
        provenance = by_all and not flagged
    elif row["kind"] == "refuse":
        worked = [c for c in calcs if c.get("value") is not None]
        says = any(re.search(r"\b" + re.escape(w), answer, re.I) for w in row["says"])
        correct, provenance = says and not worked and not flagged, not flagged
        if worked:
            why.append("a calculator worked a figure out")
        if not says:
            why.append(f"never names the {row['missing']}")
    else:
        stated = states(answer, want, unit)
        wrong = [w for w in row["wrong"] if states(answer, w, unit)]
        correct = stated and not wrong
        if row["kind"] == "lookup":
            by = any(rests_on(row, p) for p in run.get("passages") or ())
            if not by:
                why.append(f"read no passage of {row['clause']} holding it")
        else:
            names = {c["calculator"] for c in row["calcs"]}
            by = any(c.get("calculator") in names and same(c.get("value"), want, unit) for c in calcs)
            if not by:
                why.append(f"no {', '.join(sorted(names))} call returned it")
        provenance = by and not flagged
        if not stated:
            why.append("the figure is not stated")
        if wrong:
            why.append("states " + ", ".join(str(w) for w in wrong))
    if flagged:
        why.append("unsupported: " + ", ".join(flagged))
    if run.get("error"):
        why.insert(0, f"failed: {run['error']}")
    elif run.get("stopped_by"):
        why.insert(0, f"stopped by {run['stopped_by']}")
    return {"correct": bool(correct), "provenance": bool(provenance), "unsupported": flagged, "why": "; ".join(why)}


def backed(run: dict) -> bool:
    """The answer states a figure a calculator returned this run (label-free: the calculator's own value)."""
    return any(c.get("value") is not None and states(run.get("answer") or "", c["value"], c.get("unit") or "")
               for c in run.get("calculations") or () if c.get("unit") in ("INR", "days", "date", "yes/no"))


def _ap():
    """commands/agent_patterns.py, which needs the standard library and shared/ only at import: its figure check."""
    if str(KIT / "commands") not in sys.path:
        sys.path.insert(0, str(KIT / "commands"))
    import agent_patterns
    return agent_patterns


def passes(run: dict) -> bool:
    """The figure check passes a saved run, as it passes an attempt of verify (agent_patterns.figure_check()): no
    figure its calculations, question and passages do not write, every [n] a passage it read, no stop. A run that
    failed never passes."""
    return not run.get("error") and _ap().figure_check(run.get("answer") or "", run.get("calculations") or [],
                                                       run.get("question") or "", run.get("passages") or [],
                                                       run.get("stopped_by"))["passed"]


def best_of(runs: list[dict], n: int) -> dict:
    """One of the first n runs, chosen by the figure check alone: a run it passes, then a calculator's figure stated,
    then the earliest. It never reads the row's expected figure."""
    first = sorted(runs, key=lambda r: r["run"])[:n]
    return max(first, key=lambda r: (passes(r), backed(r), -r["run"]))


def pass_at_k(n: int, c: int, k: int) -> float:
    """At least one of k runs correct, from c correct of n (the unbiased estimate)."""
    return 1.0 if n - c < k else 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """All k runs correct, from c correct of n."""
    return math.comb(c, k) / math.comb(n, k)


# --------------------------------------------------------------------- --check
_CHUNKS: dict = {}


def clause_chunk(tenant: str, code: str) -> dict | None:
    """The tenant's handbook chunk of a clause, as shared/documind_corpus.py mints it (the lane's chunk)."""
    if tenant not in _CHUNKS:
        from shared import documind_corpus
        with warnings.catch_warnings():                # the loader leaves its files to the garbage collector
            warnings.simplefilter("ignore", ResourceWarning)
            docs = [d for d in documind_corpus.load_documents(tenant, str(HERE), "documind-ai-YOUR-ID")
                    if d["doc_type"] == "policy"]
        _CHUNKS[tenant] = [c for d in docs for c in documind_corpus.chunk_document(d, tenant)]
    return next((dict(c, source=c["source_uri"]) for c in _CHUNKS[tenant] if c.get("locator") == code), None)


def _holdings() -> dict:
    """{tenant: the STATUTES keys of the Acts and Codes it holds} from evals/manifest.json."""
    out = defaultdict(set)
    for m in json.loads(MANIFEST.read_text(encoding="utf-8")):
        if m["doc_type"] == "statute":
            out[m["tenant_id"]].add(m["slug"])
    return out


def _figure(value, unit: str) -> str:
    if value is None:
        return "no figure"
    if unit == "INR":
        return desk_calc.inr(value)
    if unit in ("days", "years", "days a month"):
        return f"{desk_calc.num(value)} {unit}"
    if unit == "yes/no":
        return "yes" if value else "no"
    return str(value)


def _cites(row: dict, result: dict) -> bool:
    if row["rule"]:
        r = desk_calc.RULES[row["rule"]]
        return r["source"] in result["cites"] and r["section"] in result["cites"]
    return row["clause"] in result["cites"].split(", ")


def _check_calc(row: dict, held: dict) -> tuple[list[str], str]:
    why, result, done = [], None, []
    passages = [] if row["rule"] else [clause_chunk(row["tenant"], row["clause"])]
    if None in passages:
        return [f"{row['tenant']}'s handbook has no clause {row['clause']}"], ""
    for c in row["calcs"] or ():
        name, spec = c["calculator"], desk_calc.CALCULATORS.get(c["calculator"])
        if spec is None:
            why.append(f"no calculator {name}")
            continue
        if spec["desk"] != row["desk"]:
            why.append(f"{name} is the {spec['desk']} desk's, not the {row['desk']} desk's")
        if spec["needs"] and spec["needs"] not in held[row["tenant"]]:
            why.append(f"{row['tenant']} holds no {spec['needs']}, so {name} would refuse")
        refused, found = desk_calc.check_args(name, c["args"], passages, row["question"])
        if refused:
            why.append("check_args refuses it: " + " ".join(refused))
            continue
        try:
            result = desk_calc.calculate(name, found=found, **c["args"])
        except desk_calc.CalcError as e:
            why.append(f"{name}: {e}")
            continue
        done.append(f"{name}({', '.join(f'{k}={v}' for k, v in c['args'].items())})")
    if not row["calcs"]:
        why.append("no calculator call")
    if result is not None:
        if not same(result["value"], row["expected"], row["unit"]):
            why.append(f"desk_calc says {result['value']}, the row {row['expected']}")
        if not _cites(row, result):
            why.append(f"it cites {result['cites']}, not {row['clause']}")
    if row["kind"] == "trap" and not why and not _in_clause(row):
        why.append(f"{row['clause']} does not write {row['expected']} itself: no trap")
    said = f"{' then '.join(done)} = {_figure(row['expected'], row['unit'])} ({result['cites'] if result else '-'})"
    if row["kind"] == "trap":
        said += f"; {row['clause']} writes {_figure(row['expected'], row['unit'])} itself: the trap"
    return why, said


def _in_clause(row: dict) -> bool:
    want = _value(row["expected"], row["unit"])
    if row["rule"]:
        return want in desk_calc.numbers_in(desk_calc.RULES[row["rule"]]["quote"])
    chunk = clause_chunk(row["tenant"], row["clause"])
    return bool(chunk) and want in desk_calc.numbers_in(desk_calc.clause_text(chunk, row["clause"]))


def _check_chained(row: dict, held: dict) -> tuple[list[str], str]:
    """A chained row: its fields, its question through the gate and the mask, then each part as a calc row of its
    calculator's desk on the row's question, its wrong figures, and check_args refusing each stated figure."""
    missing = [f for f in CHAINED_FIELDS if f not in row]
    missing += [f"part {i} {f}" for i, p in enumerate(row.get("parts") or (), 1) for f in PART_FIELDS if f not in p]
    if missing:
        return [f"missing {', '.join(missing)}"], ""
    if row["tenant"] not in held:
        return [f"tenant {row['tenant']!r} is not one of {', '.join(held)}"], ""
    if row["desk"] != "astar":
        return [f"desk {row['desk']!r}: a chained row's figures are both desks', so it runs on astar"], ""
    why, said, q = [], [], row["question"]
    if not ROW_ID.match(row["id"]):
        why.append("the id is not lower-case words and digits")
    if len(row["parts"]) < 2:
        why.append("a chained row has two figures or more")
    if desk_rules.gate(q) is not None:
        why.append(f"the hard gate takes it as {desk_rules.gate(q)}: no agent would see it")
    if desk_rules.mask(q)[1]:
        why.append("it holds an identifier the router masks")
    for i, part in enumerate(row["parts"], 1):
        spec = desk_calc.CALCULATORS.get(part["calcs"][0]["calculator"]) if len(part["calcs"]) == 1 else None
        if spec is None or part["unit"] not in UNITS or (part["rule"] is not None and part["rule"] not in desk_calc.RULES):
            why.append(f"part {i} is not one known calculator, a unit of {', '.join(UNITS)} and a rule or none")
            continue
        sub = {**part, "kind": "calc", "tenant": row["tenant"], "question": q, "desk": spec["desk"]}
        more, done = _check_calc(sub, held)
        why += [f"part {i}: {w}" for w in more]
        if not str(part["search"] or "").strip():
            why.append(f"part {i}: no search words for the scripted model")
        for w in part["wrong"]:
            if same(w, part["expected"], part["unit"]):
                why.append(f"part {i}: the wrong figure {w} is the expected one")
            if states(q, w, part["unit"]):
                why.append(f"part {i}: the wrong figure {w} is written in the question")
        stated = part.get("stated") or {}
        if stated:
            calc = part["calcs"][0]
            passages = [] if part["rule"] else [clause_chunk(row["tenant"], part["clause"])]
            refused, _ = desk_calc.check_args(calc["calculator"], {**calc["args"], **stated}, passages, q)
            for k, v in stated.items():
                if not states(q, v, "date" if k in spec["dates"] else "days"):
                    why.append(f"part {i}: the stated {k} = {v} is not written in the question")
                elif not any(m.startswith(f"{k} ") for m in refused):
                    why.append(f"part {i}: check_args takes the stated {k} = {v}")
            done += "; " + ", ".join(f"the stated {k} = {v} is refused by check_args" for k, v in stated.items())
        said.append(done)
    return why, "; ".join(said)


def _check_row(row: dict, golden: dict, held: dict) -> tuple[list[str], str]:
    if row.get("kind") == "chained":
        return _check_chained(row, held)
    need = FIELDS + (REFUSE_FIELDS if row.get("kind") == "refuse" else ())
    missing = [f for f in need if f not in row]
    if missing:
        return [f"missing {', '.join(missing)}"], ""
    why, said = [], ""
    if not ROW_ID.match(row["id"]):
        why.append("the id is not lower-case words and digits")
    for field, allowed in (("kind", KINDS), ("unit", UNITS), ("desk", DESKS), ("tenant", tuple(held))):
        if row[field] not in allowed:
            return [f"{field} {row[field]!r} is not one of {', '.join(allowed)}"], ""
    if row["rule"] is not None and row["rule"] not in desk_calc.RULES:
        return [f"no rule {row['rule']!r} in desk_calc.RULES"], ""
    if row["rule"] and desk_calc.RULES[row["rule"]]["source"] not in row["clause"]:
        why.append(f"the clause names another instrument than rule {row['rule']}'s")
    q = row["question"]
    gate = desk_rules.gate(q)
    if gate is not None:
        why.append(f"the hard gate takes it as {gate}: no agent would see it")
    if desk_rules.mask(q)[1]:
        why.append("it holds an identifier the router masks")
    if not str(row["search"] or "").strip():
        why.append("no search words for the scripted model")
    for w in row["wrong"]:
        if row["expected"] is not None and same(w, row["expected"], row["unit"]):
            why.append(f"the wrong figure {w} is the expected one")
        if states(q, w, row["unit"]):
            why.append(f"the wrong figure {w} is written in the question")
    if row["kind"] in ("calc", "trap"):
        more, said = _check_calc(row, held)
        why += more
    elif row["kind"] == "lookup":
        if row["calcs"]:
            why.append("a lookup takes no calculator")
        if not _in_clause(row):
            why.append(f"{row['clause']} does not write {row['expected']}")
        said = f"{_figure(row['expected'], row['unit'])} is written in {row['clause']}"
    else:
        why += _check_refuse(row)
        said = (f"{row['calcs'][0]['calculator']} needs the {row['missing']}, which the question does not state, and "
                f"check_args refuses an invented {row['missing']}") if row["calcs"] else ""
    if row["of"]:
        g = golden.get(row["of"])
        if g is None or g["question"] != q:
            why.append(f"golden {row['of']} does not ask this question")
        elif not any(_value(row["expected"], row["unit"]) in desk_calc.numbers_in(s) for s in g.get("must_contain") or ()):
            why.append(f"golden {row['of']}'s must_contain does not hold {row['expected']}")
        else:
            said += f" (golden {row['of']})"
    return why, said


def _check_refuse(row: dict) -> list[str]:
    why = []
    if row["expected"] is not None:
        why.append("a refuse row expects no figure")
    if len(row["calcs"] or ()) != 1:
        return why + ["a refuse row names the one calculator its question needs"]
    c = row["calcs"][0]
    spec = desk_calc.CALCULATORS.get(c["calculator"])
    if spec is None or row["missing"] not in spec["numbers"]:
        return why + [f"{row['missing']} is not an input of {c['calculator']}"]
    try:
        desk_calc.calculate(c["calculator"], **c["args"])
        why.append(f"{c['calculator']} runs without the {row['missing']}")
    except desk_calc.CalcError:
        pass
    refused, _ = desk_calc.check_args(c["calculator"], {**c["args"], **row["invented"]}, [], row["question"])
    if not any(m.startswith(row["missing"] + " ") for m in refused):
        why.append(f"check_args takes an invented {row['missing']}")
    if not row["says"]:
        why.append("no words the refusal must use")
    return why


def check(rows: list[dict], out=print) -> int:
    golden = {r["id"]: r for r in _jsonl(GOLDEN)}
    held, seen, failed = _holdings(), set(), 0
    for row in rows:
        why, said = _check_row(row, golden, held)
        if row.get("id") in seen:
            why.append("a second row with this id")
        seen.add(row.get("id"))
        failed += bool(why)
        out(("FAIL  " if why else "ok    ") + f"{row.get('id')}: " + ("; ".join(why) if why else said))
    with contextlib.redirect_stdout(io.StringIO()):
        selftest = desk_calc.selftest()
    if selftest:
        failed += 1
        out("FAIL  shared/desk_calc.py --selftest: a rule no longer says what its corpus line says")
    kinds = ", ".join(f"{sum(r.get('kind') == k for r in rows)} {k}" for k in KINDS)
    out(f"{failed} failed" if failed else
        f"{len(rows)} rows ({kinds}): every figure recomputed by shared/desk_calc.py, every clause in the corpus, every "
        f"question let through by the hard gate")
    return 1 if failed else 0


# --------------------------------------------------------------------- the runs
def arm_name(arm: dict) -> str:
    return (f"{arm['pattern']}, thinking {arm['thinking'] or 'default (low)'}, desk {arm['desk']}"
            + (f", executor {arm['executor']}" if arm.get("executor") else ""))


def short_names(a: dict, b: dict) -> tuple[str, str]:
    """Two arms named by what differs between them: low and high, loop and plan_execute."""
    keys = [k for k in ("pattern", "thinking", "desk", "executor") if a.get(k) != b.get(k)] or ["pattern"]
    name = (lambda arm: "/".join(str(arm.get(k) or "default") for k in keys))
    return (name(a), name(b)) if name(a) != name(b) else ("A", "B")


def select(rows: list[dict], slice_: str | None) -> list[dict]:
    """The rows a --slice names: a kind, a tag, an id, or an id's prefix, comma-separated."""
    if not slice_:
        return rows
    want = [t.strip() for t in slice_.split(",") if t.strip()]
    return [r for r in rows if any(t == r["kind"] or t in r["tags"] or r["id"].startswith(t) for t in want)]


def _failed_run(row: dict, arm: dict, desk: str, error: str) -> dict:
    return {"answer": "", "passages": [], "calculations": [], "tool_calls": [], "refusals": [], "retrieve_calls": 0,
            "answerable": False, "stopped_by": None, "pattern": arm["pattern"], "desk": desk, "tenant": row["tenant"],
            "question": row["question"], "thinking": arm["thinking"], "composed": "", "calls": [], "model_calls": 0,
            "tokens_in": 0, "cached_tokens": 0, "thinking_tokens": 0, "visible_tokens": 0, "tokens_out": 0, "inr": 0.0,
            "rag_inr": 0.0, "error": error}


def run_rows(rows: list[dict], arms: list[dict], runs: int, offline: bool, log=None) -> list[dict]:
    """Every row through every arm, `runs` times, in this process (--inproc): one record a run. Progress goes to
    stderr, one line a run."""
    sys.path.insert(0, str(KIT / "commands"))
    import agent_patterns as ap
    log = log or sys.stderr
    llm = None if offline else ap.gemini()
    executors: dict = {}                 # live: one client for each executor model an arm names
    records = []
    with (ap.offline() if offline else contextlib.nullcontext()):
        for arm in arms:
            for i, row in enumerate(rows, 1):
                desk = row["desk"] if arm["desk"] == "row" else arm["desk"]
                for r in range(runs):
                    model = (ap.scripted(row["question"], row["tenant"], run=r, task=row, slips_on=True,
                                         pattern=arm["pattern"]) if offline else llm)
                    executor, named = None, arm.get("executor")
                    if named:
                        executor = (ap.scripted(row["question"], row["tenant"], run=r, task=row, slips_on=True,
                                                pattern=arm["pattern"], model=named) if offline
                                    else executors.get(named) or executors.setdefault(named, ap.gemini(named)))
                    try:
                        turn = ap.run(arm["pattern"], row["question"], llm=model, desk=desk, thinking=arm["thinking"],
                                      tenant=row["tenant"], executor=executor)
                        turn.setdefault("error", None)
                    except Exception as e:                       # noqa: BLE001 - a failed run is scored, not fatal
                        turn = _failed_run(row, arm, desk, type(e).__name__)
                    turn.pop("trace", None)
                    for attempt in turn.get("attempts") or ():          # verify's: each attempt's, too
                        attempt.pop("trace", None)
                    records.append({"row": row["id"], "arm": dict(arm), "run": r, "offline": offline, **turn})
                    print(f"  [{i}/{len(rows)}] {row['id']} run {r + 1}: {turn['model_calls']} model calls, "
                          f"Rs {turn['inr']:.4f}" + (f", failed: {turn['error']}" if turn.get("error") else ""),
                          file=log, flush=True)
    return records


def save(records: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def by_arm(records: list[dict]) -> dict:
    out: dict = {}
    for rec in records:
        out.setdefault(json.dumps(rec["arm"], sort_keys=True), []).append(rec)
    return out


# --------------------------------------------------------------------- the report
def _rate(k: int, n: int) -> str:
    if n == 0:
        return "0/0 (no rows)"
    lo, hi = paired.wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.1f}% [{100 * lo:.1f}%, {100 * hi:.1f}%]"


def scored(rows: list[dict], records: list[dict]) -> dict:
    """{row id: [(record, score), ...] in run order} for the rows the records cover."""
    known = {r["id"]: r for r in rows}
    out = defaultdict(list)
    for rec in sorted(records, key=lambda x: x["run"]):
        if rec["row"] in known:
            out[rec["row"]].append((rec, score(known[rec["row"]], rec)))
    return out


def passed(s: dict, what: str) -> bool:
    """correct, provenance, or verified: correct with its provenance."""
    return s["correct"] and s["provenance"] if what == "verified" else s[what]


def first_runs(rows: list[dict], records: list[dict], what: str = "correct") -> dict:
    """{row id: passed on its first run}, for a paired comparison."""
    return {rid: passed(s, what) for rid, runs in scored(rows, records).items() for rec, s in runs[:1]}


def report(rows: list[dict], records: list[dict], title: str, best: int | None = None) -> str:
    known = {r["id"]: r for r in rows}
    got = scored(rows, records)
    runs = max((len(v) for v in got.values()), default=0)
    out = [f"== {title}: {len(got)} rows x {runs} run{'' if runs == 1 else 's'}",
           f"  {'row':<28} {'kind':<7} {'correct':>7} {'provenance':>10} {'calls':>5} {'thinking':>8} {'visible':>7} "
           f"{'Rs':>8}  why, first run"]
    for rid, rs in got.items():
        n = len(rs)
        c, p = sum(s["correct"] for _, s in rs), sum(s["provenance"] for _, s in rs)
        shown = (lambda k: ("yes" if k else "no") if n == 1 else f"{k}/{n}")
        mean = (lambda key: sum(rec.get(key) or 0 for rec, _ in rs) / n)
        out.append(f"  {rid:<28} {known[rid]['kind']:<7} {shown(c):>7} {shown(p):>10} {mean('model_calls'):>5.1f} "
                   f"{mean('thinking_tokens'):>8.0f} {mean('visible_tokens'):>7.0f} {mean('inr'):>8.4f}  {rs[0][1]['why']}")
    if not got:
        return "\n".join(out + ["  no run of these rows"])
    firsts = [rs[0][1] for rs in got.values()]
    for what in ("correct", "provenance", "verified"):
        out.append(f"  {'first runs:' if what == 'correct' else '':<11} {what:<10} "
                   f"{_rate(sum(passed(s, what) for s in firsts), len(firsts))}")
    if runs > 1:
        for k in sorted({1, runs}):
            parts = []
            for what in ("correct", "verified"):
                counts = [(len(rs), sum(passed(s, what) for _, s in rs)) for rs in got.values()]
                parts.append(f"{what} pass@{k} {sum(pass_at_k(n, c, k) for n, c in counts) / len(counts):.3f}, "
                             f"pass^{k} {sum(pass_hat_k(n, c, k) for n, c in counts) / len(counts):.3f}")
            out.append(f"  {'; '.join(parts)}" + ("   (over each row's runs, averaged over rows)" if k == 1 else ""))
    fewest = min(len(rs) for rs in got.values())
    if best and fewest < best:
        out.append(f"  best-of-{best}: not for this arm, which has {fewest} run{'' if fewest == 1 else 's'} a row")
    elif best:
        chosen = [score(known[rid], best_of([rec for rec, _ in rs], best)) for rid, rs in got.items()]
        out.append(f"  best-of-{best}, chosen by the figure check alone: " + ", ".join(
            f"{what} {_rate(sum(passed(s, what) for s in chosen), len(chosen))}" for what in ("correct", "verified")))
    out += attempt_lines(known, got)
    every = [rec for rs in got.values() for rec, _ in rs]
    mean = (lambda key: sum(rec.get(key) or 0 for rec in every) / len(every))
    note = " (the script's tokens at list price: nothing is billed)" if all(r.get("offline") for r in every) else ""
    out += [f"  a run: {mean('model_calls'):.1f} model calls, {mean('retrieve_calls'):.1f} searches, thinking "
            f"{mean('thinking_tokens'):.0f} and visible {mean('visible_tokens'):.0f} tokens, Rs {mean('inr'):.4f} for "
            f"the model and Rs {mean('rag_inr'):.4f} for rag-api{note}",
            f"  in all: {sum(rec.get('model_calls') or 0 for rec in every)} model calls, Rs "
            f"{sum(rec.get('inr') or 0 for rec in every):.4f} for the model and Rs "
            f"{sum(rec.get('rag_inr') or 0 for rec in every):.4f} for rag-api"]
    return "\n".join(out + by_role(every))


def by_role(records: list[dict]) -> list[str]:
    """A planning pattern's runs (lesson 10.2): a run's calls and rupees by role, each role with its model, and how its
    plans went: runs replanned, plans refused before any tool ran, waves a run. Nothing for the other patterns."""
    planned = [rec for rec in records if rec.get("roles")]
    if not planned:
        return []
    totals: dict = {}
    for rec in planned:
        for role, r in rec["roles"].items():
            t = totals.setdefault(role, {"model": r.get("model"), "calls": 0, "inr": 0.0})
            t["calls"] += r.get("calls") or 0
            t["inr"] += r.get("inr") or 0
    n, order = len(planned), {r: i for i, r in enumerate(ROLES)}
    out = ["  by role, a run: " + "; ".join(
        f"{role} {t['calls'] / n:.1f} calls, Rs {t['inr'] / n:.4f} ({t['model']})"
        for role, t in sorted(totals.items(), key=lambda kv: order.get(kv[0], len(ROLES))))]
    plans, went = [rec.get("plan") or {} for rec in planned], []
    if any("replans" in p for p in plans):
        went.append(f"replanned in {sum(bool(p.get('replans')) for p in plans)} of {n} runs")
    if any("waves" in p for p in plans):
        went.append(f"refused before any tool ran in {sum(bool(p.get('refused')) for p in plans)} of {n} runs, "
                    f"{sum(len(p.get('waves') or ()) for p in plans) / n:.1f} waves a run")
    return out + ([f"  the plans: {'; '.join(went)}"] if went else [])


def _attempt(rec: dict, a: dict) -> dict:
    """One attempt of a verify run, as a run for score(): its own answer, calculations, passages and stop."""
    return {**a, "question": a.get("question") or rec.get("question"), "error": None}


def attempt_lines(known: dict, got: dict) -> list[str]:
    """A verify arm's runs (lesson 10.3): on which attempt the figure check passed, the attempts, reflect calls and notes
    a run, the notes that write a figure, and the ceiling, each row's first run counted correct (or verified) when any
    of its attempts is. Nothing for the other patterns."""
    runs = [rec for rs in got.values() for rec, _ in rs if rec.get("attempts")]
    if not runs:
        return []
    cap, n = _ap().MAX_ATTEMPTS, len(runs)
    passed_on = [rec["shipped"] if (rec.get("check") or {}).get("passed") else 0 for rec in runs]
    notes = [a for rec in runs for a in rec["attempts"] if a.get("note")]
    tries = sum(len(rec["attempts"]) for rec in runs)
    reflects = sum(c.get("role") == "reflect" for rec in runs for c in rec.get("calls") or ())
    figured = sum(bool(a.get("note_figures")) for a in notes)
    out = ["  with notes: the figure check passed " + ", ".join(f"on attempt {k} in {passed_on.count(k)}"
                                                               for k in range(1, cap + 1))
           + f" and on none in {passed_on.count(0)} of {n} run{'' if n == 1 else 's'} (at most {cap} attempts a run); "
           f"{tries / n:.1f} "
           f"attempts, {reflects / n:.1f} reflect calls and {len(notes) / n:.1f} notes a run; {figured} of "
           f"{len(notes)} notes write a figure, which no check takes from a note"]
    ceiling = {what: [] for what in ("correct", "verified")}
    for rid, rs in got.items():
        rec = rs[0][0]
        if rec.get("attempts"):
            tried = [score(known[rid], _attempt(rec, a)) for a in rec["attempts"]]
            for what in ceiling:
                ceiling[what].append(any(passed(s, what) for s in tried))
    out.append("  any attempt (the ceiling, each row's first run): " + ", ".join(
        f"{what} {_rate(sum(v), len(v))}" for what, v in ceiling.items()))
    return out


def critic(rows: list[dict], groups: dict, best: int | None) -> list[str]:
    """Lesson 10.3's three ways side by side, when the records hold a verify arm and another: the other arm's pass@1
    (its first run), pass@k re-rolls (any of its first k runs correct: the ceiling a perfect chooser reaches) and
    best-of-k (the run the figure check chooses, best_of()), k being --best-of or its runs a row, and verify's pass@3
    with notes (the answer its first run ships: up to three attempts, a note before each retry), each with its calls
    and rupees a row (model and rag-api); then the figure check's precision, the share of the runs and attempts it
    passes that are correct. Rs 0: the records, rescored. Nothing without both arms."""
    arms, checked = list(groups.values()), {n for n, p in _ap().PATTERNS.items() if p.checked}
    notes = next((recs for recs in arms if recs[0]["arm"]["pattern"] in checked), None)
    base = next((recs for recs in arms if recs[0]["arm"]["pattern"] not in checked), None)
    if notes is None or base is None:
        return []
    known = {r["id"]: r for r in rows}
    a, v = scored(rows, base), scored(rows, notes)
    ids = [rid for rid in a if rid in v]
    if not ids:
        return []
    k = min(min(best or len(a[rid]), len(a[rid])) for rid in ids)
    first_k = {rid: a[rid][:k] for rid in ids}
    name, other = base[0]["arm"]["pattern"], notes[0]["arm"]["pattern"]
    hit = (lambda s: {"correct": s["correct"], "verified": passed(s, "verified")})
    spent = (lambda recs: (sum(r.get("model_calls") or 0 for r in recs),
                           sum((r.get("inr") or 0) + (r.get("rag_inr") or 0) for r in recs)))

    def line(label: str, hits: list[dict], costs: list[tuple]) -> str:
        """One way: correct and verified over the rows, then its calls and rupees a row."""
        rates = ", ".join(f"{w} {_rate(sum(h[w] for h in hits), len(hits))}" for w in ("correct", "verified"))
        calls, inr = sum(c for c, _ in costs) / len(costs), sum(i for _, i in costs) / len(costs)
        return f"  {label}: {rates}; {calls:.1f} calls and Rs {inr:.4f} a row"

    out = [f"== check, retry or choose (lesson 10.3): {name} against {other}, on the {len(ids)} rows both ran",
           line(f"pass@1, {name}'s first run", [hit(a[rid][0][1]) for rid in ids],
                [spent([a[rid][0][0]]) for rid in ids])]
    if k > 1:
        k_costs = [spent([rec for rec, _ in first_k[rid]]) for rid in ids]
        out += [line(f"pass@{k} re-rolls, any of its first {k} runs (the ceiling a perfect chooser reaches)",
                     [{w: any(hit(s)[w] for _, s in first_k[rid]) for w in ("correct", "verified")} for rid in ids],
                     k_costs),
                line(f"best-of-{k}, the run the figure check chooses (code, no model)",
                     [hit(score(known[rid], best_of([rec for rec, _ in first_k[rid]], k))) for rid in ids], k_costs)]
    cap = _ap().MAX_ATTEMPTS
    out.append(line(f"pass@{cap} with notes, {other}'s answer that ships (up to {cap} attempts, a note before each "
                    "retry)", [hit(v[rid][0][1]) for rid in ids], [spent([v[rid][0][0]]) for rid in ids]))
    runs = [hit(s) for rid in ids for rec, s in first_k[rid] if passes(rec)]
    tried = [(rid, _attempt(v[rid][0][0], at)) for rid in ids for at in v[rid][0][0].get("attempts") or ()]
    tries = [hit(score(known[rid], at)) for rid, at in tried if (at.get("check") or {}).get("passed")]
    share = (lambda hits: f"{sum(h['correct'] for h in hits)} correct"
             + (f" ({100 * sum(h['correct'] for h in hits) / len(hits):.0f}%)" if hits else "")
             + f" and {sum(h['verified'] for h in hits)} verified")
    out.append(f"  the figure check's precision: of the {len(runs)} of {name}'s {len(ids) * k} runs it passes, "
               f"{share(runs)}; of the {len(tries)} of {other}'s {len(tried)} attempts it passes, {share(tries)}")
    return out


def compared(rows: list[dict], a: list[dict], b: list[dict]) -> str:
    name_a, name_b = short_names(a[0]["arm"], b[0]["arm"])
    return "\n".join(paired.report(first_runs(rows, a, what), first_runs(rows, b, what), name_a, name_b, what)
                     for what in ("correct", "verified"))


def executor_arms(arms: list[dict], exec_model: str | None, ap) -> list[dict]:
    """--exec-model: each arm of a pattern with an executor (plan_execute, rewoo) once for every model named, default
    being the planner's own; the other patterns' arms as they are."""
    if not exec_model:
        return arms
    models = list(dict.fromkeys(None if m.strip() in ("", "default") else m.strip() for m in exec_model.split(",")))
    for m in models:
        if m is not None and m not in ap.EXEC_MODELS:
            raise ValueError(f"--exec-model {m!r} is not one of {', '.join(ap.EXEC_MODELS)}, default")
    if models == [None]:
        return arms
    if not any(ap.pattern(arm["pattern"]).executor for arm in arms):
        raise ValueError(f"--exec-model is for {', '.join(n for n, p in ap.PATTERNS.items() if p.executor)}, and "
                         f"--patterns names neither")
    return [dict(arm, **({"executor": m} if m else {})) for arm in arms
            for m in (models if ap.pattern(arm["pattern"]).executor else [None])]


def _one_arm(records: list[dict], path: str) -> list[dict]:
    arms = by_arm(records)
    if len(arms) != 1:
        raise SystemExit(f"ERROR: {path} holds {len(arms)} arms; --compare pairs two files of one arm each")
    return records


# --------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="The agent bench's eval: evals/agent_tasks.jsonl through agent patterns.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Rs 0: every figure recomputed, every question gated")
    mode.add_argument("--offline", action="store_true", help="the scripted model and the kit's corpus: Rs 0")
    mode.add_argument("--live", action="store_true", help="Gemini and your lane's rag-api: make agent-eval")
    mode.add_argument("--replay", nargs="+", metavar="FILE", help="rescore saved runs, from one file or more: Rs 0")
    mode.add_argument("--compare", nargs=2, metavar=("A", "B"), help="two saved arms, paired: Rs 0")
    p.add_argument("--inproc", action="store_true", default=True,
                   help="run the patterns in this process: the default, and so far the only way")
    p.add_argument("--patterns", default="loop", help="comma-separated: commands/agent_patterns.py's")
    p.add_argument("--thinking", help="comma-separated levels (minimal, low, medium, high, default); unset: default")
    p.add_argument("--desk", default="astar", choices=("astar", "row", "handbook", "statute"))
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--slice", help="kinds, tags, ids or id prefixes, comma-separated")
    p.add_argument("--best-of", type=int, help="one of each row's first N runs, chosen by the figure check")
    p.add_argument("--save", metavar="FILE", help="keep every run, one JSON line each")
    p.add_argument("--exec-model", help="comma-separated: plan_execute's and rewoo's executor (default, the planner's "
                                        "own; or gemini-3.1-flash-lite)")
    p.add_argument("--tasks", default=str(TASKS), help=argparse.SUPPRESS)
    a = p.parse_args(argv)
    rows = select(load_tasks(a.tasks), a.slice)
    if a.check:
        return check(rows)
    if a.compare:
        sets = [_one_arm(_jsonl(f), f) for f in a.compare]
        print(f"== {a.compare[1]} ({arm_name(sets[1][0]['arm'])}) against {a.compare[0]} "
              f"({arm_name(sets[0][0]['arm'])}), each row's first run, Rs 0")
        print(compared(rows, sets[0], sets[1]))
        return 0
    if a.replay:
        records = [rec for path in a.replay for rec in _jsonl(path)]
        cost = sum(rec.get("inr") or 0 for rec in records) + sum(rec.get("rag_inr") or 0 for rec in records)
        script = "; offline, the script" if all(r.get("offline") for r in records) else ""
        print(f"replayed {len(records)} saved runs of {', '.join(a.replay)}: rescored at Rs 0, no model call (they cost "
              f"Rs {cost:.4f} when they ran{script})")
        groups = by_arm(records)
        for recs in groups.values():
            print(report(rows, recs, arm_name(recs[0]["arm"]), a.best_of))
        if len(groups) == 2:
            print(compared(rows, *groups.values()))
        for line in critic(rows, groups, a.best_of):
            print(line)
        return 0
    if a.runs < 1 or (a.best_of and a.best_of > a.runs):
        print("ERROR: --runs is 1 or more, and --best-of N needs N runs or more", file=sys.stderr)
        return 2
    thinking = [None if t in ("", "default") else t for t in (a.thinking or "default").split(",")]
    arms = [{"pattern": pat, "thinking": t, "desk": a.desk} for pat in a.patterns.split(",") for t in thinking]
    sys.path.insert(0, str(KIT / "commands"))
    import agent_patterns as ap
    try:
        for arm in arms:
            ap.pattern(arm["pattern"])
            if arm["thinking"] is not None and arm["thinking"] not in ap.THINKING_LEVELS:
                raise ValueError(f"thinking {arm['thinking']!r} is not one of {', '.join(ap.THINKING_LEVELS)}, default")
        arms = executor_arms(arms, a.exec_model, ap)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if a.live:
        missing = [k for k in ("GOOGLE_CLOUD_PROJECT", "RAG_API_URL", "DOCUMIND_IMPERSONATE_SA") if not os.environ.get(k)]
        if missing:
            print(f"ERROR: --live needs {', '.join(missing)}: make agent-eval PROJECT=<id> sets them "
                  f"(commands/agent-turn.sh)", file=sys.stderr)
            return 2
    named = sorted({arm["executor"] for arm in arms if arm.get("executor")})
    print(("OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's"
           if a.offline else "LIVE: gemini-3.6-flash on location global, and your lane's rag-api") +
          (f"; an executor on {', '.join(named)}" if named else "") +
          f" | {len(rows)} rows, {len(arms)} arm{'' if len(arms) == 1 else 's'}, {a.runs} run{'' if a.runs == 1 else 's'}"
          " each, in this process (--inproc)", flush=True)
    records = run_rows(rows, arms, a.runs, a.offline)
    if a.save:
        save(records, a.save)
        print(f"saved {len(records)} runs to {a.save}: --replay rescores them at Rs 0")
    groups = by_arm(records)
    for recs in groups.values():
        print(report(rows, recs, arm_name(recs[0]["arm"]), a.best_of))
    if len(groups) == 2:
        print(compared(rows, *groups.values()))
    for line in critic(rows, groups, a.best_of):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
