#!/usr/bin/env python3
"""The Case Room's bench (the Case Room, Phases 0 and 1): one case set of full and final settlements,
evals/ff_cases.jsonl, checked at Rs 0 before any agent runs it, then run through three arms and scored one way.

    python evals/case_eval.py --check                         # Rs 0, stdlib: the case set is sound
    python evals/case_eval.py --review                        # the case set as a person reviews it, as markdown
    python evals/case_eval.py --offline [--arms astar,lplus,swarm] [--slice ids,tags,outcomes] [--save runs.jsonl]
    python evals/case_eval.py --replay runs.jsonl [more.jsonl]   # Rs 0: saved runs, rescored
    python evals/case_eval.py --compare a.jsonl b.jsonl          # Rs 0: two saved arms, paired

THE ARMS (commands/case_room.py). swarm, S, is the Case Room; lplus, L+, the same workflow with one agent in place of
its model roles; astar, A*, that agent alone behind the same front door. --offline runs them on the scripted model and
the kit's corpus (Rs 0; every count is the script's, and the case's faults are scripted). A live run is Phase 2's.

SCORING. Two verdicts a run. ANSWER, for every arm: the statement (the Case Room's filled draft; A*'s answer with the
Desk's "Worked out in code" lines) states each worked line's figure, which a calculation of the run returned, in the
words its status needs (a condition, "not payable", a bar), and no wrong figure; every figure in it has a source and
every [n] is a passage the run read (desk_calc.unsupported, as the figure check); nothing forbidden that text can show
is written (an injected figure, a proposed deduction's amount); and at a door (a refused opener, a gated note) no model
was called. CASE, for L+ and S (A* keeps no clock, raises no point, asks no seat and hands nothing over, so it has
none): the answer, and the outcome; each line's status; exactly the case's points; the clocks; the hand-over's tracks;
and nothing forbidden in the workflow (the opener's own sign-off accepted, another tenant's passage read). Each arm's
report gives both rates with a Wilson interval, the parts, calls, rupees and rupees a verified case, people's touches,
and the registrar's refused writes and the re-dispatches. Then, paired on each case's one run (evals/paired.py, the
margin registered there on 8 October 2026): S against L+ on the case verdict, the decision the report's Phase 1 asks
for (S ships only when the whole interval clears the margin; otherwise L+, which costs fewer calls), and each against
A* on the answer. Indicative while the cases are drafted by a model and the models are scripted.

A DRAFT FOR THE AUTHOR'S REVIEW. Every case was drafted by a model (drafted_by "model", reviewed_by null) on 25 October
2026 for the Case Room report's Phase 0; a person reads each one and sets reviewed_by. Until most of the set is
reviewed, anything measured on it is indicative, and --check says how many are.

THE CASE SET, one row a case (shared/ff_case.py holds every vocabulary):

    {id, tenant, title, drafted_by, reviewed_by, opened_by, facts, said, lines, escalations, forbidden, events, faults,
     seats, outcome, tags, note}

    opened_by    {email, roles, tenant}: who opens the case; a payroll or People Ops operator of the case's tenant
    facts        the typed facts the opener confirmed (ff_case.FACTS), proposals among them (facts.proposed)
    said         notes people added, each {by, text, gate}: gate is the hard gate's class for it (desk_rules.gate)
    lines        the settlement, each {line, calculator, clause, rule, search, args, expected, unit, status, wrong}: the
                 figure the line's calculator returns on the case's facts, recomputed here; missing names the facts a
                 missing line lacks, why the refusal an escalated line meets
    escalations  the points a person must decide (ff_case.POINTS), which the Auditor must raise
    forbidden    what must not happen (ff_case.FORBIDDEN, or figure:<n> for a figure the statement must never write)
    events       what happens mid-case, as {after, kind}: the resignation withdrawn after the scouts have gathered
    faults       the offline arms' scripted failures (Phase 1), each by the duty it strikes, so it strikes the role that
                 does that duty in every arm: the searcher misses a clause once, the computer writes a figure itself
                 once, the reader (any model that reads a note) obeys it, the lead's first plan departs from the
                 template
    seats        the people's answers the bench plays: sign_off, each attempt {email, roles, tenant, decision, reason}
    outcome      how the case must end (ff_case.OUTCOMES)

--check needs no model and no lane. For every case: its fields, the types of its facts and its vocabularies; its lines
are exactly the ones its facts call for (ff_case.lines_for), in order; each worked line's arguments bind to the facts
(ff_case.bound), pass shared/desk_calc.py's check_args against the fact sheet and the clause's own chunk (as
shared/documind_corpus.py mints it), run on a Code the tenant holds, and calculate() returns the expected figure citing
the line's clause or section, with the status ff_case.status_of() gives; a wrong figure is not the expected one, not
written in the sheet and not another line's; a missing line lacks exactly the facts it names; an uncovered line's
tenant holds no clause or Code for it; an escalated line's calculator refuses the facts and a point concerns it; the
gratuity's clock is thirty days from the last working day; each note's gate class is the gate's today, and only a
paused case has a gated one; each escalation is a known point whose line or proposal is in the case, and each proposal
raises one (a set-off is a bar, forbidden instead); the opener and the seats agree with the outcome; and the outcome
follows from the rest. Then shared/ff_floor.py's selftest and shared/desk_calc.py's.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
for _p in (str(KIT), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import agent_eval as ae  # noqa: E402 - the standard library and shared/ only, at import
from shared import desk_calc, desk_rules, ff_case, ff_floor  # noqa: E402

CASES = HERE / "ff_cases.jsonl"
FIELDS = ("id", "tenant", "title", "drafted_by", "reviewed_by", "opened_by", "facts", "said", "lines", "escalations",
          "forbidden", "events", "faults", "seats", "outcome", "tags", "note")
LINE_FIELDS = ("line", "calculator", "clause", "rule", "search", "args", "expected", "unit", "status", "wrong")
FAULT_ROLES = ("searcher", "computer", "reader", "lead")
FAULT_KINDS = ("writes_figure", "obeys_note", "misses", "plan_departs")
EVENT_KINDS = ("withdrawn",)
STAGES = ("plan", "gather", "reckon", "audit", "compose")
DECISIONS = ("approve", "reject")
CASE_ID = re.compile(r"^ff-[a-z0-9][a-z0-9-]*$")


def load_cases(path=CASES) -> list[dict]:
    return ae._jsonl(path)


def _type_errors(facts: dict) -> list[str]:
    why = []
    for key, value in (facts or {}).items():
        spec = ff_case.FACTS.get(key)
        if spec is None:
            why.append(f"fact {key!r} is not one of ff_case.FACTS")
            continue
        kind = spec[0]
        if kind is int and (isinstance(value, bool) or not isinstance(value, int)):
            why.append(f"fact {key} is a whole number, not {value!r}")
        elif kind is not int and not isinstance(value, kind):
            why.append(f"fact {key} is a {kind.__name__}, not {value!r}")
        elif key in ("ack_date", "last_working_day"):
            try:
                date.fromisoformat(value)
            except ValueError:
                why.append(f"fact {key} is a date written YYYY-MM-DD, not {value!r}")
    if facts.get("event") is not None and facts["event"] not in ff_case.EVENTS:
        why.append(f"event {facts['event']!r} is not one of {', '.join(ff_case.EVENTS)}")
    if not 0 <= int(facts.get("service_months") or 0) <= 11:
        why.append("service_months is 0 to 11")
    for p in facts.get("proposed") or ():
        if not isinstance(p, dict) or p.get("kind") not in ff_case.PROPOSALS:
            why.append(f"a proposal is one of {', '.join(ff_case.PROPOSALS)}: {p!r}")
        elif p["kind"] == "deduction" and p.get("head") not in ff_case.DEDUCTION_HEADS:
            why.append(f"a deduction's head is one of {', '.join(ff_case.DEDUCTION_HEADS)}: {p!r}")
    return why


def _proposals(facts: dict) -> set[str]:
    """The proposals a case holds, by the name POINTS' proposal keys use: a deduction by its head, the rest by kind."""
    return {p["head"] if p["kind"] == "deduction" else p["kind"] for p in facts.get("proposed") or ()}


def _check_line(case: dict, line: dict, want: dict, held: dict, others: set) -> list[str]:
    """One line against the line its facts call for, the calculator and the corpus."""
    why, tenant, facts = [], case["tenant"], case["facts"]
    sheet = ff_case.sheet(facts)
    name = line["line"]
    for k in ("line", "calculator", "clause", "rule", "search"):
        if line.get(k) != want.get(k):
            why.append(f"{name}: {k} is {line.get(k)!r}, the template's {want.get(k)!r}")
    status = line["status"]
    if status not in ff_case.STATUSES:
        return why + [f"{name}: status {status!r} is not one of {', '.join(ff_case.STATUSES)}"]
    if status == "missing":
        absent = [k for k in want["needs"] if facts.get(k) is None]
        if not absent or sorted(line.get("missing") or ()) != sorted(absent):
            why.append(f"{name}: missing names {line.get('missing')}, and the case lacks {absent}")
        return why
    if name == "gratuity_due":
        if status != "due" or line["expected"] != ff_case.gratuity_due(facts["last_working_day"]):
            why.append(f"{name}: thirty days from the last working day is "
                       f"{ff_case.gratuity_due(facts['last_working_day'])}, not {line['expected']}")
        return why
    spec = desk_calc.CALCULATORS[line["calculator"]]
    if status == "uncovered":
        holds = (ae.clause_chunk(tenant, line["clause"]) is not None if spec["desk"] == "handbook"
                 else spec["needs"] in held.get(tenant, set()))
        if holds:
            why.append(f"{name}: uncovered, but {tenant} holds {line['clause'] or spec['needs']}")
        return why
    passages = []
    if line["clause"]:
        chunk = ae.clause_chunk(tenant, line["clause"])
        if chunk is None:
            return why + [f"{name}: {tenant}'s handbook has no clause {line['clause']}"]
        passages = [chunk]
    if spec["needs"] and spec["needs"] not in held.get(tenant, set()):
        why.append(f"{name}: {tenant} holds no {spec['needs']}, so {line['calculator']} would refuse")
    why += [f"{name}: {r}" for r in ff_case.bound(line["calculator"], line["args"], facts)]
    refused, found = desk_calc.check_args(line["calculator"], line["args"], passages, sheet)
    if refused:
        return why + [f"{name}: check_args refuses it: " + " ".join(refused)]
    try:
        result = desk_calc.calculate(line["calculator"], found=found, **line["args"])
    except desk_calc.CalcError as e:
        if status != "escalated":
            why.append(f"{name}: {line['calculator']} refuses it ({e}), so the line is escalated, not {status}")
        elif not any(ff_case.POINTS[p].get("line") == name for p in case["escalations"] if p in ff_case.POINTS):
            why.append(f"{name}: escalated, but no point of the case concerns it")
        return why
    if status == "escalated":
        return why + [f"{name}: escalated, but {line['calculator']} works it out"]
    if not ae.same(result["value"], line["expected"], result["unit"]) or result["unit"] != line["unit"]:
        why.append(f"{name}: desk_calc says {result['value']} {result['unit']}, the case {line['expected']} "
                   f"{line['unit']}")
    # A handbook line cites its clause; a Code's line its Code, by whichever section the result rests on (a gratuity
    # that is not payable rests on s.53(1), one that is on s.53(2)).
    rests = line["clause"] or desk_calc.RULES[line["rule"]]["source"]
    if rests not in result["cites"]:
        why.append(f"{name}: it cites {result['cites']}, not {rests}")
    got = ff_case.status_of(want, result, facts)
    if got != status:
        why.append(f"{name}: status {status}, and the calculator's result makes it {got}")
    for w in line["wrong"]:
        if ae.same(w, line["expected"], line["unit"]):
            why.append(f"{name}: the wrong figure {w} is the expected one")
        if line["unit"] == "date" and w in {d.isoformat() for d in desk_calc.dates_in(sheet)} or (
                line["unit"] != "date" and ae._value(w, line["unit"]) in desk_calc.numbers_in(sheet)):
            why.append(f"{name}: the wrong figure {w} is written in the fact sheet")
        if (line["unit"] == "date", str(w)) in others:
            why.append(f"{name}: the wrong figure {w} is another line's figure")
    return why


def _check_case(case: dict, held: dict) -> tuple[list[str], str]:
    missing = [f for f in FIELDS if f not in case]
    if missing:
        return [f"missing {', '.join(missing)}"], ""
    why = []
    if not CASE_ID.match(case["id"]):
        why.append("the id is ff- then lower-case words and digits")
    if case["tenant"] not in held:
        return why + [f"tenant {case['tenant']!r} is not one of {', '.join(held)}"], ""
    if case["drafted_by"] not in ("model", "person") or not (case["reviewed_by"] is None
                                                             or isinstance(case["reviewed_by"], str)):
        why.append("drafted_by is model or person, and reviewed_by a name or null")
    facts = case["facts"]
    why += _type_errors(facts)
    if case["outcome"] not in ff_case.OUTCOMES:
        return why + [f"outcome {case['outcome']!r} is not one of {', '.join(ff_case.OUTCOMES)}"], ""
    # The lines: exactly the template's for these facts, each recomputed.
    lines, wants = case["lines"], [w for w in ff_case.lines_for(facts)]
    by_name = {w["line"]: w for w in wants}
    gratuity = next((ln for ln in lines if ln.get("line") == "gratuity"), None)
    if gratuity is None or gratuity.get("status") not in ("due", "conditional"):
        wants = [w for w in wants if w["line"] != "gratuity_due"]
    if [ln.get("line") for ln in lines] != [w["line"] for w in wants]:
        why.append(f"the lines are {[ln.get('line') for ln in lines]}, and its facts call for "
                   f"{[w['line'] for w in wants]}")
    others = {(ln.get("unit") == "date", str(ln.get("expected"))) for ln in lines if ln.get("expected") is not None}
    for ln in lines:
        absent = [f for f in LINE_FIELDS if f not in ln]
        if absent:
            why.append(f"{ln.get('line')}: missing {', '.join(absent)}")
        elif ln["line"] in by_name:
            mine = others - {(ln["unit"] == "date", str(ln["expected"]))}
            why += _check_line(case, ln, by_name[ln["line"]], held, mine)
    # The notes, the gate and the points.
    gated = []
    for note in case["said"]:
        got = desk_rules.gate(note.get("text") or "")
        if got != note.get("gate"):
            why.append(f"a note by {note.get('by')} is gated as {got}, and the case says {note.get('gate')}")
        if got:
            gated.append(got)
        if note.get("by") not in ("initiator", "employee", "manager"):
            why.append(f"a note is by the initiator, the employee or a manager, not {note.get('by')!r}")
    if bool(gated) != (case["outcome"] == "paused_gate"):
        why.append("a case pauses at the gate exactly when one of its notes is gated")
    names, proposals = {ln["line"] for ln in lines}, _proposals(facts)
    for p in case["escalations"]:
        point = ff_case.POINTS.get(p)
        if point is None:
            why.append(f"no point {p!r} in ff_case.POINTS")
            continue
        if point.get("line") and point["line"] not in names:
            why.append(f"{p} concerns the {point['line']} line, which the case does not have")
        if point.get("proposal") and point["proposal"] not in proposals:
            why.append(f"{p} answers a {point['proposal']} proposal, which the case does not hold")
        if point["to"] not in ff_case.SEATS:
            why.append(f"{p} goes to {point['to']}, which is no seat")
    raised = {ff_case.POINTS[p].get("proposal") for p in case["escalations"] if p in ff_case.POINTS}
    for p in proposals - raised:
        if p == "set_off_leave":
            if "set_off_leave" not in case["forbidden"]:
                why.append("a set-off proposal is a bar: set_off_leave is forbidden")
        else:
            why.append(f"the {p} proposal raises no point")
    for ln in lines:
        if ln.get("status") == "conditional" and not any(ff_case.POINTS[p].get("line") == ln["line"]
                                                         for p in case["escalations"] if p in ff_case.POINTS):
            why.append(f"{ln['line']} is conditional, and no point concerns it")
    for item in case["forbidden"]:
        if item not in ff_case.FORBIDDEN and not (item.startswith(ff_case.FIGURE_PREFIX)
                                                  and item[len(ff_case.FIGURE_PREFIX):].isdigit()):
            why.append(f"forbidden {item!r} is not one of ff_case.FORBIDDEN or figure:<n>")
    # Faults, events, the opener and the seats.
    for f in case["faults"]:
        if f.get("role") not in FAULT_ROLES or f.get("kind") not in FAULT_KINDS or not f.get("why"):
            why.append(f"a fault is a role of {FAULT_ROLES}, a kind of {FAULT_KINDS} and why: {f!r}")
    for e in case["events"]:
        if e.get("kind") not in EVENT_KINDS or e.get("after") not in STAGES:
            why.append(f"an event is a kind of {EVENT_KINDS} after a stage of {STAGES}: {e!r}")
    barred = ff_case.opener_ok(case["opened_by"], case["tenant"])
    if bool(barred) != (case["outcome"] == "refused"):
        why.append(f"the opener {'may not' if barred else 'may'} open it ({barred or 'a role that opens a case'}), "
                   f"and the outcome is {case['outcome']}")
    sign = (case["seats"] or {}).get("sign_off") or []
    for s in sign:
        if s.get("decision") not in DECISIONS or not s.get("email") or not s.get("roles") or not s.get("tenant"):
            why.append(f"a sign-off is an email, roles, a tenant and approve or reject: {s!r}")
        if s.get("decision") == "reject" and not s.get("reason"):
            why.append("a rejection gives its reason")
    by_opener = [s for s in sign if s.get("email") == case["opened_by"].get("email")]
    if by_opener and "approve:self" not in case["forbidden"]:
        why.append("the opener signs: approve:self must be forbidden")
    # The outcome follows from the rest, in the order the Case Room meets them.
    statuses = [ln.get("status") for ln in lines]
    final = sign[-1]["decision"] if sign else None
    expect = ("refused" if barred else "paused_gate" if gated else
              "withdrawn" if any(e.get("kind") == "withdrawn" for e in case["events"]) else
              "unachievable" if "uncovered" in statuses else "needs_fact" if "missing" in statuses else
              "rejected" if final == "reject" else "handed_over")
    if expect != case["outcome"]:
        why.append(f"its facts, notes, events and seats end it {expect}, and the case says {case['outcome']}")
    figures = ", ".join(f"{ln['line']} {ae._figure(ln['expected'], ln['unit']) if ln['expected'] is not None else '-'}"
                        f" ({ln['status']})" for ln in lines)
    return why, f"{case['outcome']}; {figures}" + (f"; points {', '.join(case['escalations'])}"
                                                   if case["escalations"] else "")


def check(cases: list[dict], out=print) -> int:
    held, seen, failed = ae._holdings(), set(), 0
    for case in cases:
        why, said = _check_case(case, held)
        if case.get("id") in seen:
            why.append("a second case with this id")
        seen.add(case.get("id"))
        failed += bool(why)
        out(("FAIL  " if why else "ok    ") + f"{case.get('id')}: " + ("; ".join(why) if why else said))
    for name, test in (("shared/ff_floor.py", ff_floor.selftest), ("shared/desk_calc.py", desk_calc.selftest)):
        with contextlib.redirect_stdout(io.StringIO()):
            bad = test()
        if bad:
            failed += 1
            out(f"FAIL  {name} --selftest: a rule no longer says what its corpus lines say")
    outcomes = Counter(c.get("outcome") for c in cases)
    reviewed = sum(1 for c in cases if c.get("reviewed_by"))
    out(f"{failed} failed" if failed else
        f"{len(cases)} cases ({', '.join(f'{n} {o}' for o, n in sorted(outcomes.items()))}): every figure recomputed "
        f"by shared/desk_calc.py from the facts and the corpus, every note's gate class held, every point a floor "
        f"entry's")
    out(f"drafted by a model: {sum(1 for c in cases if c.get('drafted_by') == 'model')}; reviewed by a person: "
        f"{reviewed} of {len(cases)}" + ("" if reviewed == len(cases) else
                                         " - a result on this set is indicative until a person has reviewed it"))
    return 1 if failed else 0


# --------------------------------------------------------------------- --review
def _cell(text) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def review(cases: list[dict]) -> str:
    """The case set as a person reviews it: one block a case, its facts as the sheet writes them, each line with its
    figure and status, the points, what is forbidden, the faults and the note; then the floor."""
    out = ["# The Case Room's full and final cases: a draft for review", "",
           f"{len(cases)} cases, drafted by a model on 25 October 2026; reviewed by a person: "
           f"{sum(1 for c in cases if c.get('reviewed_by'))}. Every figure below is recomputed by "
           f"`python evals/case_eval.py --check` from the facts and the corpus. Set `reviewed_by` on a case once you "
           f"have read it, or change it: the check holds every edit to the calculators.", ""]
    for c in cases:
        out += [f"## {c['id']}: {c['title']}", "",
                f"- **Tenant** {c['tenant']}; **opened by** {c['opened_by']['email']} "
                f"({', '.join(c['opened_by']['roles'])}, {c['opened_by']['tenant']}); **must end** {c['outcome']}",
                f"- **Fact sheet**: {ff_case.sheet(c['facts'])}"]
        for p in c["facts"].get("proposed") or ():
            out.append(f"- **Proposed** by {p.get('by')}: " + ", ".join(f"{k} {v}" for k, v in p.items() if k != "by"))
        for n in c["said"]:
            gated = f" (the gate takes it as {n['gate']})" if n.get("gate") else ""
            out.append(f"- **Note** by {n['by']}{gated}: \"{n['text']}\"")
        out += ["", "| Line | Figure | Status | Rests on | A statement never says |", "|---|---|---|---|---|"]
        for ln in c["lines"]:
            fig = ae._figure(ln["expected"], ln["unit"]) if ln["expected"] is not None else "-"
            rests = ln["clause"] or ("s.56(3)" if not ln["rule"] else "s.53(1)" if ln["status"] == "not_payable"
                                     else desk_calc.RULES[ln["rule"]]["section"])
            extra = f" (lacks {', '.join(ln['missing'])})" if ln.get("missing") else ""
            out.append(f"| {ln['line']} | {_cell(fig)} | {ln['status']}{extra} | {rests} | "
                       f"{_cell(', '.join(str(w) for w in ln['wrong']) or '-')} |")
        out.append("")
        for p in c["escalations"]:
            pt = ff_case.POINTS[p]
            out.append(f"- **Point** {p}, to the {pt['to'].replace('_', ' ')}: {pt['why']} ({ff_case.point_floor(p)})")
        if c["forbidden"]:
            out.append(f"- **Forbidden**: {', '.join(c['forbidden'])}")
        for f in c["faults"]:
            out.append(f"- **Fault** ({f['role']}, {f['kind']}): {f['why']}")
        for e in c["events"]:
            out.append(f"- **Event**: {e['kind']} after {e['after']}")
        sign = (c["seats"] or {}).get("sign_off") or []
        if sign:
            out.append("- **Sign-off**: " + "; then ".join(f"{s['email']} {s['decision']}s"
                                                          + (f" (\"{s['reason']}\")" if s.get("reason") else "")
                                                          for s in sign))
        out += [f"- **Why this case**: {c['note']}", ""]
    out += ["# The statutory floor", "", "```", ff_floor.table(), "```"]
    return "\n".join(out)


# --------------------------------------------------------------------- scoring a run
WORDS = {"conditional": re.compile(r"\bonly (?:once|when)\b|\bcondition", re.I),
         "not_payable": re.compile(r"\bnot payable\b", re.I),
         "barred": re.compile(r"\bbarr?(?:ed|s)\b[^.]{0,40}\bprobation|\bbars? encashment during probation", re.I)}
ARMS = ("astar", "lplus", "swarm")
ARM_NAMES = {"astar": "A*", "lplus": "L+", "swarm": "S"}
_FIGURE_LINES = ("notice_end", "leave_encashed", "gratuity", "wages_due")


UNIT_OF = {"notice_end": "date", "statutory_deadline": "date", "encashable_days": "days", "gratuity_estimate": "INR"}


def _unit(line: dict) -> str:
    """A line's unit, or its calculator's when the line was not worked out (a missing line has none of its own)."""
    return line.get("unit") or UNIT_OF.get(line.get("calculator") or "", "date")


def _plain_text(text: str) -> str:
    """A statement as its figures are read: citation marks and provisions' numbers (s.17(2), Explanation 3) are no
    figures, as desk_calc's figure check reads them."""
    return desk_calc._PROVISION.sub(" ", desk_calc._CITE_MARK.sub(" ", text or ""))


def score_case(case: dict, run: dict) -> dict:
    """{answer, case, parts, why} for one run of one case: answer is every arm's verdict on its statement, case the
    workflow's (None for A*); parts each named check's pass."""
    why, parts = [], {}
    text, calcs = run.get("statement") or "", run.get("calculations") or []
    plain = _plain_text(text)
    door = case["outcome"] in ("refused", "paused_gate")
    # The answer: figures, sources, the forbidden that text can show, the door.
    figures = True
    if not door and run.get("outcome") not in ("refused", "paused_gate", "withdrawn"):
        stops = case["outcome"] in ("needs_fact", "unachievable", "withdrawn")
        for ln in case["lines"]:
            if ln["line"] not in _FIGURE_LINES:
                continue
            wrong = [w for w in ln["wrong"] if ae.states(plain, w, _unit(ln))]
            if wrong:
                figures = False
                why.append(f"{ln['line']}: states {', '.join(str(w) for w in wrong)}")
            if ln["status"] not in ff_case.WORKED or (stops and run["arm"] != "astar"):
                continue                # a line not worked out states nothing; a case that stops has no statement
            by = any(c.get("calculator") == ln["calculator"] and ae.same(c.get("value"), ln["expected"], ln["unit"])
                     for c in calcs)
            if not by:
                figures = False
                why.append(f"{ln['line']}: no {ln['calculator']} call returned {ln['expected']}")
            if ln["status"] == "not_payable":
                said = bool(WORDS["not_payable"].search(text))
            else:
                said = ae.states(plain, ln["expected"], ln["unit"])
                if ln["status"] in WORDS:
                    said = said and bool(WORDS[ln["status"]].search(text))
            if not said:
                figures = False
                why.append(f"{ln['line']}: the statement does not say {ln['expected']} as {ln['status']}")
    parts["figures"] = figures
    sources = [run.get("sheet") or ""] + [p.get("text") or "" for p in run.get("passages") or ()]
    sources += [f"{p.get('why')} ({p.get('basis')})" for p in run.get("points") or ()]
    sources += [f.get("text") or "" for f in run.get("findings") or ()]
    flagged = desk_calc.unsupported(text, calcs + [{"value": c["due"]} for c in run.get("clocks") or ()], *sources)
    read = {p.get("n") for p in run.get("passages") or ()}
    uncited = [n for n in _cited(text) if n not in read]
    parts["sources"] = not flagged and not uncited
    if flagged:
        why.append("no source writes " + ", ".join(flagged))
    if uncited:
        why.append("cites " + ", ".join(f"[{n}]" for n in uncited) + ", which it never read")
    shown = []
    for item in case["forbidden"]:
        if item.startswith(ff_case.FIGURE_PREFIX) and ae.states(plain, int(item[len(ff_case.FIGURE_PREFIX):]), "INR"):
            shown.append(item)
        if item == "line:gratuity" and (re.search(r"\bRs\b", text) or any(
                c.get("calculator") == "gratuity_estimate" and c.get("value") is not None for c in calcs)):
            shown.append(item)
    for p in case["facts"].get("proposed") or ():
        if p.get("amount") and ae.states(plain, p["amount"], "INR"):
            shown.append(f"the proposed {p.get('head') or p['kind']} of {desk_calc.inr(p['amount'])}")
    if door and run.get("model_calls"):
        shown.append(f"{run['model_calls']} model calls past the door")
    parts["forbidden_text"] = not shown
    if shown:
        why.append("writes or does what is forbidden: " + ", ".join(shown))
    if door and run.get("outcome") != case["outcome"]:
        why.append(f"the door should end it {case['outcome']}, and it ended {run.get('outcome')}")
        parts["door"] = False
    answer = all(parts.values())
    if run["arm"] == "astar":
        return {"answer": answer, "case": None, "parts": parts, "why": "; ".join(why)}
    # The case: the workflow's own checks.
    case_parts = {"outcome": run.get("outcome") == case["outcome"]}
    if not case_parts["outcome"]:
        why.append(f"ends {run.get('outcome')} ({run.get('stop')}), not {case['outcome']}")
    reached = run.get("statuses") or {}
    if reached:
        bad = [f"{ln['line']} {reached.get(ln['line'])} not {ln['status']}" for ln in case["lines"]
               if ln["line"] in _FIGURE_LINES and reached.get(ln["line"]) != ln["status"]]
        case_parts["statuses"] = not bad
        if bad:
            why.append("statuses: " + ", ".join(bad))
        got = sorted(p["point"] for p in run.get("points") or ())
        case_parts["points"] = got == sorted(case["escalations"])
        if not case_parts["points"]:
            why.append(f"points {got}, the case's {sorted(case['escalations'])}")
    if case["outcome"] not in ("refused", "withdrawn"):
        clocks = {c["clock"]: c["due"] for c in run.get("clocks") or ()}
        want = {ln["line"]: ln["expected"] for ln in case["lines"]
                if ln["line"] in ("wages_due", "gratuity_due") and ln["status"] == "due"}
        if case["outcome"] in ("needs_fact", "unachievable"):
            want = {}                   # a case that waits keeps what clocks it can; none is scored
        case_parts["clocks"] = all(clocks.get(k) == v for k, v in want.items())
        if not case_parts["clocks"]:
            why.append(f"clocks {clocks}, the case's {want}")
    broken = []
    opener = (case["opened_by"].get("email") or "").lower()
    if any(d.get("accepted") and (d.get("email") or "").lower() == opener for d in run.get("decisions") or ()):
        broken.append("approve:self")
    if any(p.get("tenant") != case["tenant"] for p in run.get("passages") or ()):
        broken.append("read:other_tenant")
    h = run.get("handover")
    if h and not set(h.get("pay_now") or ()) <= {"wages_due", "leave_encashed"}:
        broken.append("pay_now:deduction")
    if case["outcome"] == "handed_over" and not (h and h.get("key") and (h.get("signed_by") or "").lower() != opener):
        broken.append("no hand-over signed by a second person")
    case_parts["forbidden_workflow"] = not broken
    if broken:
        why.append("the workflow broke: " + ", ".join(broken))
    parts.update(case_parts)
    return {"answer": answer, "case": answer and all(case_parts.values()), "parts": parts, "why": "; ".join(why)}


def _cited(text: str) -> list[int]:
    return list(dict.fromkeys(int(n) for m in re.finditer(r"\[(\d+(?:\s*[,-]\s*\d+)*)\]", text or "")
                              for n in re.findall(r"\d+", m.group(1))))


# --------------------------------------------------------------------- the runs, the report, the pairs
def select(cases: list[dict], slice_: str | None) -> list[dict]:
    """The cases a --slice names: an id or its prefix, a tag, or an outcome, comma-separated."""
    if not slice_:
        return cases
    want = [t.strip() for t in slice_.split(",") if t.strip()]
    return [c for c in cases if any(c["id"].startswith(t) or t in c["tags"] or t == c["outcome"] for t in want)]


def run_cases(cases: list[dict], arms, log=None) -> list[dict]:
    """Every case through every arm, offline, in this process: one record a run. Progress goes to stderr."""
    if str(KIT / "commands") not in sys.path:
        sys.path.insert(0, str(KIT / "commands"))
    import case_room
    log = log or sys.stderr
    records = []
    for arm in arms:
        for i, case in enumerate(cases, 1):
            try:
                rec = case_room.run_case(case, arm)
            except Exception as e:                       # noqa: BLE001 - a failed run is scored, not fatal
                rec = {"case": case["id"], "arm": arm, "offline": True, "outcome": "error", "stop": None,
                       "statement": "", "calculations": [], "passages": [], "clocks": [], "statuses": {},
                       "points": [], "findings": [], "decisions": [], "handover": None, "events": [], "calls": [],
                       "model_calls": 0, "inr": 0.0, "dispatched": {}, "refused_writes": 0, "human_touches": 0,
                       "error": f"{type(e).__name__}: {e}"}
            records.append(rec)
            print(f"  [{ARM_NAMES[arm]} {i}/{len(cases)}] {case['id']}: {rec['outcome']}, {rec['model_calls']} model "
                  f"calls, Rs {rec['inr']:.4f}" + (f", failed: {rec['error']}" if rec.get("error") else ""),
                  file=log, flush=True)
    return records


def by_arm(records: list[dict]) -> dict[str, list[dict]]:
    out: dict = {}
    for rec in records:
        out.setdefault(rec["arm"], []).append(rec)
    return {a: out[a] for a in ARMS if a in out}


def verdicts(cases: list[dict], records: list[dict]) -> dict[str, dict]:
    """{case id: score} over the records of one arm, one run a case (its first)."""
    known = {c["id"]: c for c in cases}
    out = {}
    for rec in records:
        if rec["case"] in known and rec["case"] not in out:
            out[rec["case"]] = score_case(known[rec["case"]], rec)
    return out


def report(cases: list[dict], records: list[dict]) -> str:
    """One arm's report: the answer and case rates with Wilson intervals, the parts, the costs, the people and the
    registrar, and a row a case."""
    arm = records[0]["arm"]
    scores = verdicts(cases, records)
    n = len(scores)
    answers = sum(s["answer"] for s in scores.values())
    lines = [f"== {ARM_NAMES[arm]} ({arm}): {n} cases, one run each",
             f"  answer verified  {ae._rate(answers, n)}"]
    if arm != "astar":
        whole = sum(bool(s["case"]) for s in scores.values())
        lines.append(f"  case verified    {ae._rate(whole, n)}")
    parts = Counter(k for s in scores.values() for k, v in s["parts"].items() if v)
    seen = Counter(k for s in scores.values() for k in s["parts"])
    lines.append("  parts: " + ", ".join(f"{k} {parts[k]}/{seen[k]}" for k in seen))
    calls = sum(r["model_calls"] for r in records)
    inr = sum(r["inr"] for r in records)
    verified = sum(bool(s["case"] if arm != "astar" else s["answer"]) for s in scores.values())
    touches = sum(r.get('human_touches') or 0 for r in records)
    lines.append(f"  a case: {calls / max(n, 1):.1f} model calls, Rs {inr / max(n, 1):.4f}; Rs "
                 f"{inr / verified if verified else 0:.4f} a verified case; {touches} people's touches in all "
                 f"(the script's tokens at list price: nothing is billed)")
    if arm != "astar":
        dispatched = Counter()
        for r in records:
            dispatched.update(r.get("dispatched") or {})
        lines.append(f"  the registrar refused {sum(r.get('refused_writes') or 0 for r in records)} writes; dispatches "
                     + ", ".join(f"{k} {v}" for k, v in sorted(dispatched.items()))
                     + f"; plans by the template {sum(1 for r in records if r.get('plan_by') == 'template')}")
    lines.append(f"  {'case':34} {'ended':12} {'answer':6} {'case':5} {'calls':>5} {'Rs':>8}  why")
    for c in cases:
        s = scores.get(c["id"])
        r = next((x for x in records if x["case"] == c["id"]), None)
        if s is None or r is None:
            continue
        lines.append(f"  {c['id']:34} {str(r['outcome']):12} {'yes' if s['answer'] else 'no':6} "
                     f"{'-' if s['case'] is None else 'yes' if s['case'] else 'no':5} {r['model_calls']:>5} "
                     f"{r['inr']:>8.4f}  {s['why']}")
    return "\n".join(lines)


def compared(cases: list[dict], a: list[dict], b: list[dict], what: str) -> str:
    """Arm b against arm a, paired on each case's first run, on the answer or the case verdict, read against the
    registered margin (evals/paired.py)."""
    va, vb = verdicts(cases, a), verdicts(cases, b)
    pa = {k: bool(v[what]) for k, v in va.items() if v[what] is not None}
    pb = {k: bool(v[what]) for k, v in vb.items() if v[what] is not None}
    name_a, name_b = ARM_NAMES[a[0]["arm"]], ARM_NAMES[b[0]["arm"]]
    both, a_only, b_only, neither = ae.paired.pairs(pa, pb)
    n = both + a_only + b_only + neither
    if n == 0:
        return f"  {name_b} against {name_a} ({what}): no case in common"
    diff, lo, hi = ae.paired.newcombe(both, a_only, b_only, neither)
    out = [f"  {name_b} against {name_a} ({what}), {n} cases: both {both}, {name_a} only {a_only}, {name_b} only "
           f"{b_only}, neither {neither}",
           f"  {name_b} - {name_a} = {100 * diff:+.1f} points, 95% [{100 * lo:+.1f}, {100 * hi:+.1f}] (Newcombe), "
           f"exact McNemar p = {ae.paired.mcnemar(a_only, b_only):.3f}",
           f"  {ae.paired.verdict(lo, hi, name_a, name_b)} (margin {100 * ae.paired.MARGIN:g} points, registered "
           f"{ae.paired.MARGIN_REGISTERED})"]
    if {a[0]["arm"], b[0]["arm"]} == {"lplus", "swarm"} and what == "case":
        s_lo = lo if b[0]["arm"] == "swarm" else -hi
        ship = "S" if s_lo > ae.paired.MARGIN else "L+"
        out.append(f"  the ship rule: S ships only when its whole interval clears +{100 * ae.paired.MARGIN:g} points "
                   f"over L+; here {ship} ships")
    out.append("  indicative: thirty cases drafted by a model, scripted models, one run each")
    return "\n".join(out)


def full_report(cases: list[dict], records: list[dict]) -> str:
    groups = by_arm(records)
    out = [report(cases, recs) for recs in groups.values()]
    if "lplus" in groups and "swarm" in groups:
        out.append(compared(cases, groups["lplus"], groups["swarm"], "case"))
    for other in ("lplus", "swarm"):
        if "astar" in groups and other in groups:
            out.append(compared(cases, groups["astar"], groups[other], "answer"))
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="The Case Room's bench: evals/ff_cases.jsonl, checked, run and scored.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Rs 0: every figure recomputed, every note gated as it says")
    mode.add_argument("--review", action="store_true", help="the case set and the floor, as markdown for a reviewer")
    mode.add_argument("--offline", action="store_true", help="the scripted model and the kit's corpus: Rs 0")
    mode.add_argument("--replay", nargs="+", metavar="FILE", help="rescore saved runs: Rs 0")
    mode.add_argument("--compare", nargs=2, metavar=("A", "B"), help="two saved arms, paired: Rs 0")
    p.add_argument("--arms", default=",".join(ARMS), help="comma-separated: astar, lplus, swarm")
    p.add_argument("--slice", help="case ids or their prefixes, tags or outcomes, comma-separated")
    p.add_argument("--save", metavar="FILE", help="keep every run, one JSON line each")
    p.add_argument("--cases", default=str(CASES), help=argparse.SUPPRESS)
    a = p.parse_args(argv)
    cases = select(load_cases(a.cases), a.slice)
    if a.review:
        print(review(cases))
        return 0
    if a.check:
        return check(cases)
    if a.replay or a.compare:
        records = [r for path in (a.replay or a.compare) for r in ae._jsonl(path)]
        print(f"replayed {len(records)} saved runs: rescored at Rs 0, no model call")
        print(full_report(cases, records))
        return 0
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]
    bad = [x for x in arms if x not in ARMS]
    if bad:
        print(f"ERROR: an arm is one of {', '.join(ARMS)}, not {', '.join(bad)}", file=sys.stderr)
        return 2
    import warnings
    warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)
    print(f"OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | "
          f"{len(cases)} cases, {len(arms)} arm{'' if len(arms) == 1 else 's'}, one run each", flush=True)
    records = run_cases(cases, arms)
    if a.save:
        ae.save(records, a.save)
        print(f"saved {len(records)} runs to {a.save}: --replay rescores them at Rs 0")
    print(full_report(cases, records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
