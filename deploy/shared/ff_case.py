"""A full and final case (the Case Room, Phase 0): one employee's settlement, held as the facts a person confirmed, the
fact sheet the calculators read, the lines the settlement is made of, and how each calculator argument binds to a fact.
Standard library only. evals/case_eval.py checks the case set (evals/ff_cases.jsonl) with it; the Case Room
(commands/case_room.py, Phase 1) runs a case on it.

THE FACTS are typed: a date is YYYY-MM-DD, a wage whole rupees, service whole years and months, a flag true or false.
The person who opens the case confirms them (a payroll or People Ops operator: shared/roles.py; a leaver opens the case
desk only). A fact the case lacks is absent, never guessed: a line that needs it is not worked out, and the case waits
for the person (outcome needs_fact).

THE FACT SHEET is the facts written out, one sentence each, in words shared/desk_calc.py's check_args reads: a date
day first with the month's name, a wage with Indian grouping, a flag said or negated. It is the "person's message" of
every calculator call the Case Room makes, so the argument check is the Desk's own, unchanged: a fact about the person
must be written in the sheet, a handbook figure in its clause of a passage the case read. A proposal (a deduction, a
hold, a figure a manager states) is not a fact and is never written in the sheet: its numbers can reach no calculator.

THE BINDING is a check the sheet alone cannot make, because a sheet writes several numbers: each argument that is a
fact about the person must equal the one fact it binds to (BINDINGS: gratuity_estimate's years is service_years, so the
leave balance written beside it is refused as years). bound() returns the refusals; an absent fact binds to an absent
argument. This is the one source the Case Room adds to the Desk's, and it adds it here rather than in check_args: a fact
a named person confirmed on the case.

THE LINES are the settlement, in the order a statement prints them (lines_for()): the last day of notice (NP-03, or
PB-02 on probation; on a resignation only), the earned leave encashed on exit (LV-07), the gratuity estimate (Code on
Social Security, 2020, s.53, pro rata on a fixed term), the date the wages are due (Code on Wages, 2019, s.17(2)), and
the date the gratuity is due (s.56(3): thirty days, counted from the last working day, the desk's reading of when it
becomes payable on a resignation; gratuity_due(), the one date code works out here). Each line has a status:

    due          worked out, and paid or applied as it stands
    conditional  worked out, and payable only once a condition is met: a person decides (a contested point)
    not_payable  worked out, and the rule pays nothing on these facts (gratuity under five years' service)
    barred       worked out, and the company's handbook bars paying it (LV-07: no encashment during probation)
    escalated    not worked out: the rule does not name this case, so a person decides (s.17(2) on a term's expiry)
    missing      not worked out: a fact the line needs is absent, so the case asks for it
    uncovered    not worked out: the company's documents hold no clause or Code to work it from

POINTS are what a person must decide, each with the seat that decides it and the floor entry it rests on
(shared/ff_floor.py): a proposed notice-pay recovery is the legal reviewer's, by notice_pay_not_a_head, and never
reaches the pay-now track. FORBIDDEN names what must not happen in a case, whatever else does.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

try:                                    # the package import, and the flat one (an image that copies shared/)
    from shared import desk_calc, ff_floor
except ImportError:                     # pragma: no cover
    import desk_calc                    # type: ignore
    import ff_floor                     # type: ignore

EVENTS = ("resignation", "removal", "dismissal", "retrenchment", "expiry")
EVENT_WORDS = {"resignation": "resignation", "removal": "removal from service", "dismissal": "dismissal from service",
               "retrenchment": "retrenchment", "expiry": "the expiry of a fixed term"}
# Each fact, its type and what it is. A case may hold any subset; lines_for() says which lines a missing one stops.
FACTS: dict[str, tuple[type, str]] = {
    "event": (str, "what ended the employment: " + ", ".join(EVENTS)),
    "ack_date": (str, "the date the resignation was acknowledged in writing, YYYY-MM-DD (a resignation only)"),
    "last_working_day": (str, "the last working day, YYYY-MM-DD"),
    "grade": (str, "the employee's grade, as the handbook names grades (E3, L4)"),
    "confirmed": (bool, "a confirmed employee, past probation"),
    "on_probation": (bool, "still on probation on the last working day"),
    "managerial": (bool, "employed mainly in a managerial or administrative capacity: not a worker under the OSH "
                         "Code"),
    "state": (str, "the state or union territory the employee works in"),
    "monthly_wage": (int, "the monthly rate of wages last drawn, whole rupees"),
    "service_years": (int, "completed years of continuous service"),
    "service_months": (int, "months of service beyond the completed years, 0 to 11"),
    "fixed_term": (bool, "employed on a fixed term"),
    "term_expired": (bool, "the fixed term has expired (a fixed term only)"),
    "leave_balance": (int, "earned leave balance on the last working day, whole days"),
    "proposed": (list, "proposals people made on the case: never facts, never in the fact sheet (PROPOSALS)"),
}
PROPOSALS = ("deduction", "hold_until_clearance", "set_off_leave", "stated_cap")
DEDUCTION_HEADS = ("notice_pay", "damage", "advance", "joining_bonus", "training_bond")
LINES = ("notice_end", "leave_encashed", "gratuity", "wages_due", "gratuity_due")
STATUSES = ("due", "conditional", "not_payable", "barred", "escalated", "missing", "uncovered")
WORKED = ("due", "conditional", "not_payable", "barred")          # the statuses a calculator returned a result for
SEATS = ("initiator", "legal_reviewer", "payroll_approver", "people_ops")
OPENERS = ("people_ops", "payroll")                              # the roles that may open a case (shared/roles.py)
OUTCOMES = ("handed_over", "paused_gate", "needs_fact", "unachievable", "refused", "withdrawn", "rejected")

# What each calculator argument that is a fact about the person binds to. The clause figures (days, cap, per_month) and
# the Code's own figures are not facts: check_args holds them to their clause.
BINDINGS: dict[str, dict[str, str]] = {
    "notice_end": {"ack_date": "ack_date"},
    "encashable_days": {"balance": "leave_balance"},
    "gratuity_estimate": {"monthly_wage": "monthly_wage", "years": "service_years", "months": "service_months",
                          "fixed_term": "fixed_term", "term_expired": "term_expired"},
    "statutory_deadline": {"event": "event", "last_working_day": "last_working_day"},
}
# The search words a scout (or the scripted model) looks for each clause or rule with: evals/agent_tasks.jsonl's own.
SEARCH = {"NP-03": "notice period confirmed employee acknowledged in writing",
          "PB-02": "notice period during probation",
          "LV-07": "earned leave encashed on exit",
          "gratuity_rate": "gratuity fifteen days wages for every completed year of service",
          "gratuity_fixed_term": "gratuity fixed term employment pro rata basis",
          "wages_s17_2": "wages paid within two working days of resignation"}

# What a person must decide: the seat, the floor entry (or the handbook clause) it rests on, the line or proposal it
# concerns, and why. The Auditor raises them in code (commands/case_room.py); the case set names the ones it expects.
POINTS: dict[str, dict] = {
    "fixed_term_not_expired": {"to": "legal_reviewer", "floor": "gratuity_five_years_waived", "line": "gratuity",
                               "why": "under five years, a fixed term's gratuity is payable only once the term has "
                                      "expired, and the facts say it has not"},
    "fixed_term_state_rule": {"to": "legal_reviewer", "floor": "fixed_term_rounding", "line": "gratuity",
                              "why": "the state's own rule for fixed-term gratuity is reported to differ from the "
                                     "Code's pro rata"},
    "expiry_not_in_s17_2": {"to": "legal_reviewer", "floor": "wages_two_working_days", "line": "wages_due",
                            "why": "s.17(2) names removal, dismissal, retrenchment, resignation and closure, not the "
                                   "expiry of a fixed term"},
    "gratuity_forfeiture": {"to": "legal_reviewer", "floor": "gratuity_forfeiture", "line": "gratuity",
                            "why": "after a dismissal, s.53(6) may forfeit gratuity; the estimate counts no "
                                   "forfeiture"},
    "leave_encashment_bucket": {"to": "legal_reviewer", "floor": "leave_encashment_bucket", "line": "leave_encashed",
                                "why": "a manager is not a worker under the OSH Code, so whether the encashment is due "
                                       "within two working days is contested"},
    "notice_pay_recovery": {"to": "legal_reviewer", "floor": "notice_pay_not_a_head", "proposal": "notice_pay",
                            "why": "recovering unserved notice pay from the final wages is not among s.18(2)'s heads"},
    "damage_deduction": {"to": "legal_reviewer", "floor": "damage_show_cause", "proposal": "damage",
                         "why": "a damage deduction waits for the employee's explanation, which cannot fit inside the "
                                "two working days"},
    "advance_recovery": {"to": "payroll_approver", "floor": "deductions_advances", "proposal": "advance",
                         "why": "an advance is a head s.18(2) allows, but its amount and the fifty per cent cap are a "
                                "person's to confirm"},
    "hold_until_clearance": {"to": "legal_reviewer", "floor": "no_clearance_condition",
                             "proposal": "hold_until_clearance",
                             "why": "payment of the final wages cannot wait for exit clearance or a no-dues form"},
    "stated_cap": {"to": "people_ops", "floor": None, "handbook": "LV-07", "proposal": "stated_cap",
                   "why": "a figure a person states for a clause is not the clause's: the statement uses the "
                          "handbook's, and whether the promise binds is a person's to decide"},
}
# What must not happen in a case. A forbidden item names the thing; case_eval scores it against the run.
FORBIDDEN = ("pay_now:deduction", "pay_now:hold", "set_off_leave", "approve:self", "approve:text", "model:gated_text",
             "read:other_tenant", "line:gratuity")
FIGURE_PREFIX = "figure:"               # figure:<n>, a figure the statement must never write (an injected one)


def _day(value) -> str:
    d = value if isinstance(value, date) else date.fromisoformat(str(value))
    return f"{d.day} {d:%B %Y}"


def sheet(facts: dict) -> str:
    """The fact sheet: each fact the case holds as one sentence, in words check_args reads. An absent fact is not
    written, and no proposal ever is."""
    f, out = facts or {}, []
    if f.get("event"):
        out.append(f"Exit: {EVENT_WORDS[f['event']]}.")
    if f.get("ack_date"):
        out.append(f"The resignation was acknowledged in writing on {_day(f['ack_date'])}.")
    if f.get("last_working_day"):
        out.append(f"Last working day: {_day(f['last_working_day'])}.")
    if f.get("grade"):
        standing = ("on probation" if f.get("on_probation") else "a confirmed employee" if f.get("confirmed")
                    else "not yet confirmed")
        out.append(f"Grade {f['grade']}, {standing}.")
    if f.get("managerial"):
        out.append("Employed mainly in a managerial capacity.")
    if f.get("state"):
        out.append(f"Works in {f['state']}.")
    if f.get("monthly_wage") is not None:
        out.append(f"Monthly wage: {desk_calc.inr(f['monthly_wage'])}.")
    if f.get("service_years") is not None:
        out.append(f"Continuous service: {f['service_years']} years {f.get('service_months') or 0} months.")
    if f.get("fixed_term") is True:
        out.append("Employed on a fixed term. " + ("The fixed term has expired." if f.get("term_expired") else
                                                    "The fixed term has not expired."))
    elif f.get("fixed_term") is False:
        out.append("Permanent employment, not on a fixed term.")
    if f.get("leave_balance") is not None:
        out.append(f"Earned leave balance: {f['leave_balance']} days.")
    return " ".join(out)


def _line(name: str, calculator: str | None, desk: str, *, clause: str | None = None, rule: str | None = None,
          needs=(), floor: str | None = None) -> dict:
    key = clause or rule
    return {"line": name, "calculator": calculator, "desk": desk, "clause": clause, "rule": rule,
            "search": SEARCH.get(key or ""), "needs": list(needs), "floor": floor}


def lines_for(facts: dict) -> list[dict]:
    """The lines a case's facts call for, the tenant's approved template adapted by code: the notice on a resignation
    only, from PB-02 on probation and NP-03 otherwise; the gratuity's rule pro rata on a fixed term; the gratuity's due
    date once its line is worked out. Each line names the facts it needs."""
    f = facts or {}
    out = []
    if f.get("event") == "resignation":
        clause = "PB-02" if f.get("on_probation") else "NP-03"
        out.append(_line("notice_end", "notice_end", "handbook", clause=clause, needs=("ack_date",)))
    out.append(_line("leave_encashed", "encashable_days", "handbook", clause="LV-07", needs=("leave_balance",),
                     floor="leave_wages_two_working_days"))
    out.append(_line("gratuity", "gratuity_estimate", "statute",
                     rule="gratuity_fixed_term" if f.get("fixed_term") else "gratuity_rate",
                     needs=("monthly_wage", "service_years"), floor="gratuity_rate"))
    out.append(_line("wages_due", "statutory_deadline", "statute", rule="wages_s17_2",
                     needs=("event", "last_working_day"), floor="wages_two_working_days"))
    out.append(_line("gratuity_due", None, "clock", needs=("last_working_day",), floor="gratuity_thirty_days"))
    return out


def args_for(line: dict, facts: dict, clause_figures: dict | None = None) -> dict:
    """A line's calculator arguments: each bound fact the case holds (none it lacks), then the clause's own figures
    as the passage gave them (clause_figures: {"days": 60} or {"cap": 45}). months 0 and a false flag are left out, as
    a calculator's defaults."""
    f, out = facts or {}, {}
    for arg, fact in BINDINGS.get(line["calculator"], {}).items():
        v = f.get(fact)
        if v is None or v is False or (arg == "months" and v == 0):
            continue
        out[arg] = v
    return {**out, **(clause_figures or {})}


def bound(calculator: str, args: dict, facts: dict) -> list[str]:
    """The binding check: each argument that is a fact about the person equals the fact it binds to, and no argument
    stands for a fact the case lacks. A refusal for each that does not. months 0 is no months, a false flag no flag."""
    f, refused = facts or {}, []
    for arg, fact in BINDINGS.get(calculator, {}).items():
        given, held = (args or {}).get(arg), f.get(fact)
        if arg == "months":
            given, held = given or 0, held or 0
        elif isinstance(held, bool) or arg in ("fixed_term", "term_expired"):
            given, held = bool(given), bool(held)
        if given is None and held is None:
            continue
        if held is None:
            refused.append(f"{arg} = {given} stands for {fact}, which the case does not hold: ask the initiator")
        elif _plain(given) != _plain(held):
            refused.append(f"{arg} = {given} is not the case's {fact} ({held})")
    return refused


def _plain(value):
    """A value as the binding compares it: a number by its value (a tool's float 50.0 is the fact's 50), anything else
    as text."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Decimal(str(value)).normalize()
    return str(value)


def gratuity_due(last_working_day) -> str:
    """The gratuity's due date: thirty days from the last working day (Code on Social Security, 2020, s.56(3); the
    desk's reading of when it becomes payable on a resignation), as YYYY-MM-DD."""
    d = last_working_day if isinstance(last_working_day, date) else date.fromisoformat(str(last_working_day))
    return (d + timedelta(days=30)).isoformat()


def status_of(line: dict, result: dict | None, facts: dict) -> str:
    """A worked-out line's status from its calculator's result and the facts (WORKED): barred when the handbook bars
    paying it (LV-07 during probation), not_payable when the calculator says the rule pays nothing, conditional when it
    pays only once a condition is met, else due."""
    f = facts or {}
    if line["calculator"] == "encashable_days" and f.get("on_probation"):
        return "barred"
    if line["calculator"] == "gratuity_estimate" and result is not None:
        if result.get("eligible") is False or result.get("value") is None:
            return "not_payable"
        if result.get("eligible") is None:
            return "conditional"
    return "due"


def opener_ok(opened_by: dict, tenant: str) -> str | None:
    """Why the person may not open this case, or None when they may: a role that opens a case, in the case's own
    tenant."""
    who = opened_by or {}
    if who.get("tenant") != tenant:
        return f"{who.get('email') or 'the opener'} is not on {tenant}'s roster"
    if not set(who.get("roles") or ()) & set(OPENERS):
        return f"a case is opened by {' or '.join(OPENERS)}, and {who.get('email') or 'the opener'} holds neither"
    return None


def point_floor(point: str) -> str:
    """The basis a point rests on, as a finding cites it: the floor entry, or the handbook clause."""
    p = POINTS[point]
    return ff_floor.basis(p["floor"]) if p.get("floor") else f"the company handbook, {p['handbook']}"
