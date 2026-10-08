#!/usr/bin/env python3
"""The DocuMind Desk's calculators (workshop lesson 10.4): a figure the desk states is computed here, in code, and
says which clause its rule comes from. The model in agent mode reads the passages and chooses the call; it never does
the arithmetic.

    accrued_leave(months, per_month)        LV-01 of the handbook: earned leave accrues per completed month
    carry_forward(days, cap)                LV-01: at most the cap goes into the next calendar year
    encashable_days(balance, cap)           LV-07: earned leave encashed on exit, up to the cap
    notice_end(ack_date, days)              NP-03 (PB-02 on probation): notice runs from the written acknowledgement
    gratuity_estimate(monthly_wage, years, months, fixed_term, term_expired)
                                            Code on Social Security, 2020, s.53: always an estimate
    statutory_deadline(event, last_working_day)
                                            Code on Wages, 2019, s.17(2): two working days, Monday to Friday
    threshold_check(headcount)              Industrial Relations Code, 2020, s.4(1): twenty or more workers

A handbook's figures differ by company: acme carries 30 days forward and encashes up to 45, zeta 18 and 20, both
accrue 1.75 days a month. So a handbook calculator takes the company's figure as an argument, and the desk passes it
only when the right clause of this turn's passages says it. A Code's figures are the same in every company that holds
the Code, so they are fixed here, and the desk runs a statute calculator only when this turn's passages include that
Code (services/chat/desk_agent.py). A result names the clause or the section, never a corpus file, so a person reads
their own company's handbook as the source.

THE ARGUMENT CHECK. Every argument has one source (CALCULATORS' "numbers", "dates" and "flags"). A fact about the
person - months, days, a balance, a wage, years, a headcount, a date - must be written in the person's own message as
the router masked it. A handbook figure - the accrual rate and the carry-forward cap (LV-01), the encashment cap
(LV-07), the notice days (NP-03, or PB-02 on probation) - must be written in that clause of a handbook passage this turn
read: between the clause's code and the next clause code. check_args() reads digits (40,000 and 1,50,000 too), words
(fifty, twenty-six), lakh, crore and k, and dates (ISO, day first, or with the month's name); a number inside a date is
never a number of its own, and clause codes and grades (LV-07, E3) are names. A flag (fixed_term, term_expired) is true
only when the message says it, and not in a negated phrase. Anything else is refused, so a model cannot bring a figure
of its own or borrow one from the wrong clause.

RULES is each rule's corpus line, quoted: --selftest reads every cited line under evals/corpus/ and fails when the quote
is not there, then pins min(50, 45) = 45, a notice end date, a gratuity estimate from stated inputs whose displayed
arithmetic multiplies out, the two working days across a weekend, the threshold of 20 and the argument check, each
wrong source refused.

    python shared/desk_calc.py --selftest          (from deploy/; standard library only)
"""
from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

try:                                    # the package import (the services, the tests), and the flat one (this file run
    from shared import cases            # as a script, or an image that copies shared/ beside its own code)
except ImportError:                     # pragma: no cover
    import cases                        # type: ignore

CSS, WAGES, IR = "Code on Social Security, 2020", "Code on Wages, 2019", "Industrial Relations Code, 2020"
HANDBOOK = "the company handbook"

# Every rule, by the corpus file and lines it rests on and the words there. The handbook rules cite acme's file; zeta's
# handbook holds the same clauses with its own figures (its lines are cited where they differ).
RULES: dict[str, dict] = {
    "accrual": {"source": HANDBOOK, "clause": "LV-01", "file": "acme/hr_policy_2026.md", "lines": "19",
                "quote": "Earned leave accrues at 1.75 days per completed month."},
    "carry_forward": {"source": HANDBOOK, "clause": "LV-01", "file": "acme/hr_policy_2026.md", "lines": "19-20",
                      "quote": "A maximum of 30 days may be carried forward into the next calendar year; anything "
                               "above 30 lapses on 31 December."},
    "carry_forward_zeta": {"source": HANDBOOK, "clause": "LV-01", "file": "zeta/hr_policy_zeta_2026.md",
                           "lines": "19-20",
                           "quote": "A maximum of 18 days may be carried forward into the next calendar year; anything "
                                    "above 18 lapses on 31 December."},
    "encashment": {"source": HANDBOOK, "clause": "LV-07", "file": "acme/hr_policy_2026.md", "lines": "24-25",
                   "quote": "Earned leave is encashed on exit at basic pay, capped at 45 days. Leave cannot be encashed "
                            "during probation and cannot be used to shorten notice."},
    "encashment_zeta": {"source": HANDBOOK, "clause": "LV-07", "file": "zeta/hr_policy_zeta_2026.md", "lines": "24",
                        "quote": "Earned leave is encashed on exit at basic pay, capped at 20 days."},
    "notice": {"source": HANDBOOK, "clause": "NP-03", "file": "acme/hr_policy_2026.md", "lines": "7-8",
               "quote": "A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice runs from "
                        "the date the resignation is acknowledged in writing."},
    "notice_probation": {"source": HANDBOOK, "clause": "PB-02", "file": "acme/hr_policy_2026.md", "lines": "13-14",
                         "quote": "During probation the notice period is 15 days for either side."},
    "gratuity_service": {"source": CSS, "section": "s.53(1)", "file": "acme/code_on_social_security_2020.md",
                         "lines": "2212-2213",
                         "quote": "Gratuity shall be payable to an employee on the termination of his employment after "
                                  "he has rendered continuous service for not less than five years,"},
    "gratuity_no_five_years": {"source": CSS, "section": "s.53(1) second proviso",
                               "file": "acme/code_on_social_security_2020.md", "lines": "2223-2226",
                               "quote": "the completion of continuous service of five years shall not be necessary "
                                        "where the termination of the employment of any employee is due to death or "
                                        "disablement or expiration of fixed term employment"},
    "gratuity_rate": {"source": CSS, "section": "s.53(2)", "file": "acme/code_on_social_security_2020.md",
                      "lines": "2233-2236",
                      "quote": "For every completed year of service or part thereof in excess of six months, the "
                               "employer shall pay gratuity to an employee at the rate of fifteen days' wages or such "
                               "number of days as may be notified by the Central Government, based on the rate of "
                               "wages last drawn by the employee concerned:"},
    "gratuity_fixed_term": {"source": CSS, "section": "s.53(2) third proviso",
                            "file": "acme/code_on_social_security_2020.md", "lines": "2251-2252",
                            "quote": "in the case of an employee employed on fixed term employment or a deceased "
                                     "employee, the employer shall pay gratuity on pro rata basis."},
    "gratuity_ceiling": {"source": CSS, "section": "s.53(3)", "file": "acme/code_on_social_security_2020.md",
                         "lines": "2253-2254",
                         "quote": "The amount of gratuity payable to an employee shall not exceed such amount as may be "
                                  "notified by the Central Government."},
    "gratuity_monthly": {"source": CSS, "section": "s.53 Explanation 3",
                         "file": "acme/code_on_social_security_2020.md", "lines": "2278-2280",
                         "quote": "in the case of a monthly rated employee, the fifteen days' wages shall be calculated "
                                  "by dividing the monthly rate of wages last drawn by him by twenty-six and "
                                  "multiplying the quotient by fifteen."},
    "wages_s17_2": {"source": WAGES, "section": "s.17(2)", "file": "acme/code_on_wages_2019.md", "lines": "459-464",
                    "quote": "(2) Where an employee has been— (i) removed or dismissed from service; or (ii) retrenched "
                             "or has resigned from service, or became unemployed due to closure of the establishment, "
                             "the wages payable to him shall be paid within two working days of his removal, "
                             "dismissal, retrenchment or, as the case may be, his resignation."},
    "wages_s17_3": {"source": WAGES, "section": "s.17(3)", "file": "acme/code_on_wages_2019.md", "lines": "465-468",
                    "quote": "the appropriate Government may, provide any other time limit for payment of wages"},
    "ir_s4_1": {"source": IR, "section": "s.4(1)", "file": "acme/industrial_relations_code_2020.md", "lines": "397-399",
                "quote": "4. (1) Every industrial establishment employing twenty or more workers shall have one or more "
                         "Grievance Redressal Committees for resolution of disputes arising out of individual "
                         "grievances."},
    "ir_worker": {"source": IR, "section": "s.2(zr)", "file": "acme/industrial_relations_code_2020.md",
                  "lines": "371-372", "quote": "who is employed mainly in a managerial or administrative capacity;"},
}

# The Codes' own figures, fixed (each is the corpus's, above).
GRATUITY_DAYS = 15                  # fifteen days' wages a year (s.53(2))
GRATUITY_DIVISOR = 26               # the monthly rate divided by twenty-six (Explanation 3)
GRATUITY_MIN_YEARS = 5              # five years' continuous service (s.53(1))
PART_YEAR_MONTHS = 6                # a part of a year in excess of six months counts as a year (s.53(2))
WAGE_DAYS = 2                       # two working days (Code on Wages, s.17(2))
EXIT_EVENTS = ("removal", "dismissal", "retrenchment", "resignation")     # the four s.17(2) counts from
THRESHOLDS = {"grc": {"at_least": 20, "rule": "ir_s4_1",
                      "what": "must have one or more Grievance Redressal Committees"}}
NO_HOLIDAYS = "Counted Monday to Friday: no holiday calendar is loaded, so a holiday in between makes the date later."
NO_CEILING = ("No ceiling is applied: s.53(3) caps gratuity at an amount the Central Government notifies, which these "
              "documents do not hold.")


class CalcError(ValueError):
    """An argument a calculator cannot take: the agent's tool turns it into an error result."""


# ---------------------------------------------------------------------------------------------- formatting
def _dec(value, name: str) -> Decimal:
    if isinstance(value, bool):
        raise CalcError(f"{name} must be a number")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise CalcError(f"{name} must be a number, not {value!r}") from None
    if not d.is_finite():
        raise CalcError(f"{name} must be a number")
    return d


def _whole(value, name: str, low: int = 0, high: int | None = None) -> int:
    d = _dec(value, name)
    if d != d.to_integral_value():
        raise CalcError(f"{name} counts whole units: {value!r} is not a whole number")
    n = int(d)
    if n < low or (high is not None and n > high):
        raise CalcError(f"{name} must be from {low}" + (f" to {high}" if high is not None else " up"))
    return n


def num(d) -> str:
    """A figure as a person reads it: 45, 1.75, 14 (never 14.00)."""
    return format(Decimal(str(d)).normalize(), "f")


def _grouped(n: int) -> str:
    s = str(n)
    head, tail = s[:-3], s[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join(groups + [tail])


def inr(amount) -> str:
    """Rupees with Indian grouping, to the rupee: Rs 2,40,000."""
    d = Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"Rs {'-' if d < 0 else ''}{_grouped(abs(int(d)))}"


def _rupees(amount: Decimal) -> str:
    """An amount as given, paise kept: Rs 52,000 or Rs 52,000.50."""
    whole = int(amount)
    paise = (amount - whole).quantize(Decimal("0.01"))
    return f"Rs {_grouped(whole)}" + (f".{str(paise)[2:]}" if paise else "")


def day_of(value, name: str) -> date:
    """A date argument: a date, or its ISO text (YYYY-MM-DD)."""
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        raise CalcError(f"{name} must be a date written YYYY-MM-DD, not {value!r}") from None


def basis(rule: str) -> dict:
    """What a result cites: a handbook's clause, or a Code's section and its words. A handbook clause's words are each
    company's own (RULES quotes acme's for the selftest), so a result never carries them: the passage is the source."""
    r = RULES[rule]
    if "clause" in r:
        return {"source": r["source"], "clause": r["clause"]}
    return {"source": r["source"], "section": r["section"], "quote": r["quote"]}


def cites(rules) -> str:
    """The clauses, or each Code once with its sections: "PB-02, NP-03", "Code on Wages, 2019, s.17(2), s.17(3)"."""
    by_source: dict[str, list[str]] = {}
    for rule in rules:
        r = RULES[rule]
        by_source.setdefault(r["source"], []).append(r.get("clause") or r["section"])
    return "; ".join(", ".join(dict.fromkeys(v)) if s == HANDBOOK else f"{s}, " + ", ".join(dict.fromkeys(v))
                     for s, v in by_source.items())


def _years(y: int, m: int) -> str:
    return f"{y} year{'' if y == 1 else 's'} {m} month{'' if m == 1 else 's'}"


def _result(name: str, value, unit: str, formula: str, rules, *, estimate: bool = False, notes=(), conditions=(),
            **extra) -> dict:
    """One calculation. conditions are what the figure assumes and the person must check (a clause's bar, a proviso's
    condition); notes say how it was counted."""
    return {"calculator": name, "value": value, "unit": unit, "formula": formula,
            "basis": [basis(r) for r in rules], "cites": cites(rules), "estimate": estimate,
            "conditions": list(conditions), "notes": list(notes), **extra}


# ---------------------------------------------------------------------------------------------- the handbook
def accrued_leave(months, per_month) -> dict:
    """LV-01: earned leave accrues per completed month, at the rate the company's handbook sets (no default)."""
    m = _whole(months, "months")
    rate = _dec(per_month, "per_month")
    if rate <= 0:
        raise CalcError("per_month must be above 0")
    value = m * rate
    return _result("accrued_leave", float(value), "days",
                   f"{m} completed months x {num(rate)} days = {num(value)} days", ["accrual"],
                   notes=["Leave accrued over these completed months only, not a balance: leave taken is not "
                          "deducted, and no year-end lapse under LV-01 is applied."])


def carry_forward(days, cap) -> dict:
    """LV-01: at most the cap is carried into the next calendar year; the rest lapses on 31 December."""
    d, c = _dec(days, "days"), _dec(cap, "cap")
    if d < 0 or c < 0:
        raise CalcError("days and cap cannot be negative")
    kept, lapses = min(d, c), max(d - c, Decimal(0))
    return _result("carry_forward", float(kept), "days",
                   f"min({num(d)}, {num(c)}) = {num(kept)} days carried forward; {num(lapses)} lapse on 31 December",
                   ["carry_forward"], lapses=float(lapses))


def encashable_days(balance, cap, probation_bar: bool = False) -> dict:
    """LV-07: earned leave is encashed on exit, at basic pay, up to the cap. probation_bar is set by code when the
    clause the cap came from bars encashment during probation; the result then states it as a condition."""
    b, c = _dec(balance, "balance"), _dec(cap, "cap")
    if b < 0 or c < 0:
        raise CalcError("balance and cap cannot be negative")
    value = min(b, c)
    conditions = ["LV-07 bars encashment during probation: this figure holds only once probation is over."
                  ] if probation_bar else []
    return _result("encashable_days", float(value), "days", f"min({num(b)}, {num(c)}) = {num(value)} days",
                   ["encashment"], conditions=conditions)


NOTICE_RULES = {"NP-03": ["notice"], "PB-02": ["notice_probation", "notice"]}


def notice_end(ack_date, days, clause: str = "NP-03") -> dict:
    """NP-03: notice runs from the date the resignation is acknowledged in writing. The last day is that date plus the
    notice days, counting from the day after it: acme's and zeta's handbooks do not say how the days are counted, so
    the note says which count this is. clause is the clause the days came from (NP-03, or PB-02 during probation), set
    by code from the argument check, and the result cites it."""
    if clause not in NOTICE_RULES:
        raise CalcError(f"the notice days come from NP-03 or PB-02, not {clause!r}")
    start = day_of(ack_date, "ack_date")
    n = _whole(days, "days", low=1)
    end = start + timedelta(days=n)
    notes = ["The desk's count: calendar days, the first being the day after the written acknowledgement. A handbook "
             "that counts the days otherwise moves the date."]
    if clause == "PB-02":
        notes.append("The days are PB-02's notice during probation; that notice runs from the written "
                     "acknowledgement is NP-03's.")
    return _result("notice_end", end.isoformat(), "date",
                   f"{start.isoformat()} + {n} days = {end.isoformat()} ({end:%A})", NOTICE_RULES[clause], notes=notes)


# ---------------------------------------------------------------------------------------------- the Codes
def gratuity_estimate(monthly_wage, years, months=0, fixed_term: bool = False, term_expired: bool = False) -> dict:
    """Code on Social Security, 2020, s.53: the monthly rate of wages last drawn / 26 x 15 for every completed year of
    service, or part of a year in excess of six months; pro rata for fixed term employment. Always an estimate, with no
    ceiling applied. Under five years the Code pays only on death, disablement or the expiry of a fixed term (s.53(1),
    second proviso): for a fixed term the figure is then conditional unless term_expired (the message says so)."""
    wage = _dec(monthly_wage, "monthly_wage")
    if wage <= 0:
        raise CalcError("monthly_wage must be above 0")
    y, m = _whole(years, "years"), _whole(months, "months", high=11)
    if not isinstance(fixed_term, bool) or not isinstance(term_expired, bool):
        raise CalcError("fixed_term and term_expired are true or false")
    notes = ["An estimate, not the amount owed: the wages are the monthly rate last drawn as given; a better term in an "
             "award, agreement or contract wins (s.53(5)); a forfeiture under s.53(6) is not counted.", NO_CEILING]
    if not fixed_term and y < GRATUITY_MIN_YEARS:
        return _result("gratuity_estimate", None, "INR",
                       f"{_years(y, m)} is under the five years of continuous service s.53(1) asks for",
                       ["gratuity_service", "gratuity_no_five_years"], estimate=True, eligible=False,
                       notes=["Five years are not needed when the employment ends by death or disablement "
                              "(s.53(1), second proviso). An estimate, not a ruling on the case."])
    rules, conditions, eligible = ["gratuity_rate", "gratuity_monthly"], [], True
    if fixed_term:
        served = 12 * y + m
        exact = wage / GRATUITY_DIVISOR * GRATUITY_DAYS * served / 12
        expression = f"{_rupees(wage)} / {GRATUITY_DIVISOR} x {GRATUITY_DAYS} x {served} / 12"
        counted_text = f"{_years(y, m)} of fixed term employment is {served} months, pro rata"
        rules += ["gratuity_fixed_term"]
        if y < GRATUITY_MIN_YEARS:
            rules.append("gratuity_no_five_years")
            if term_expired:
                notes.append("Under five years of service: the expiry of the fixed term waives them (s.53(1), "
                             "second proviso).")
            else:
                eligible = None
                conditions.append("Payable with under five years of service only when the employment ends on the "
                                  "expiry of the fixed term (s.53(1), second proviso): the question does not say it "
                                  "has.")
    else:
        counted = y + (1 if m > PART_YEAR_MONTHS else 0)
        exact = wage / GRATUITY_DIVISOR * GRATUITY_DAYS * counted
        expression = f"{_rupees(wage)} / {GRATUITY_DIVISOR} x {GRATUITY_DAYS} x {counted}"
        counted_text = (f"{_years(y, m)} counts as {counted} years (a part of a year over six months counts "
                        f"as a year)")
        rules.insert(0, "gratuity_service")
    value = exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    rounded = ", to the nearest rupee" if value != exact else ""
    rules.append("gratuity_ceiling")
    return _result("gratuity_estimate", int(value), "INR", f"{counted_text}; {expression} = {inr(value)}{rounded}",
                   rules, estimate=True, eligible=eligible, notes=notes, conditions=conditions)


def statutory_deadline(event: str, last_working_day) -> dict:
    """Code on Wages, 2019, s.17(2): wages are paid within two working days of a removal, dismissal, retrenchment or
    resignation. Counted from the person's last working day, as the case queue's exit clock counts it
    (cases.exit_flags), on working days Monday to Friday until a holiday calendar exists (cases.working_days_after)."""
    ev = str(event or "").strip().lower()
    if ev not in EXIT_EVENTS:
        raise CalcError(f"event is one of {', '.join(EXIT_EVENTS)}: the events section 17(2) counts from")
    start = day_of(last_working_day, "last_working_day")
    due = cases.working_days_after(start, WAGE_DAYS)
    return _result("statutory_deadline", due.isoformat(), "date",
                   f"last working day {start.isoformat()} ({start:%A}), after the {ev}, + {WAGE_DAYS} working days = "
                   f"{due.isoformat()} ({due:%A})", ["wages_s17_2", "wages_s17_3"],
                   notes=[NO_HOLIDAYS, "Counted from the last working day, the desk's reading of s.17(2), as its case "
                                       "queue counts it.",
                          "The appropriate Government may set another time limit (s.17(3))."])


def threshold_check(headcount, rule: str = "grc") -> dict:
    """A headcount against a threshold a Code sets. One today: twenty or more workers, a Grievance Redressal Committee
    (Industrial Relations Code, 2020, s.4(1)). A further threshold joins only with its corpus lines in RULES."""
    t = THRESHOLDS[rule]
    n = _whole(headcount, "headcount")
    met = n >= t["at_least"]
    verdict = "at or over" if met else "under"
    return _result("threshold_check", met, "yes/no",
                   f"{n} workers is {verdict} {t['at_least']}: an industrial establishment employing "
                   f"{t['at_least']} or more workers {t['what']}", [t["rule"], "ir_worker"], threshold=t["at_least"],
                   notes=["The Code counts workers as it defines them (s.2(zr)): among others, a person employed "
                          "mainly in a managerial or administrative capacity is not one."])


# What each calculator is: its function; each argument's one source - MESSAGE (a fact about the person, written in
# their own message) or the handbook clauses a figure must be written in; the flags, true only when the message says
# them; and for a Code's calculator the instrument this turn's passages must include (shared/desk_law.STATUTES' key).
MESSAGE = "message"
FIXED_TERM = r"\bfixed[\s-]?term\b"
TERM_EXPIRED = (r"\b(?:expir\w*|(?:term|contract|employment)\s+(?:has\s+|had\s+|will\s+)?(?:ended|ends|end|"
                r"came\s+to\s+an\s+end|is\s+over|was\s+over|completed?|finished))\b")
CALCULATORS: dict[str, dict] = {
    "accrued_leave": {"fn": accrued_leave, "numbers": {"months": MESSAGE, "per_month": ("LV-01",)}, "dates": {},
                      "desk": "handbook", "needs": None},
    "carry_forward": {"fn": carry_forward, "numbers": {"days": MESSAGE, "cap": ("LV-01",)}, "dates": {},
                      "desk": "handbook", "needs": None},
    "encashable_days": {"fn": encashable_days, "numbers": {"balance": MESSAGE, "cap": ("LV-07",)}, "dates": {},
                        "desk": "handbook", "needs": None},
    "notice_end": {"fn": notice_end, "numbers": {"days": ("NP-03", "PB-02")}, "dates": {"ack_date": MESSAGE},
                   "desk": "handbook", "needs": None},
    "gratuity_estimate": {"fn": gratuity_estimate,
                          "numbers": {"monthly_wage": MESSAGE, "years": MESSAGE, "months": MESSAGE}, "dates": {},
                          "flags": {"fixed_term": FIXED_TERM, "term_expired": TERM_EXPIRED}, "desk": "statute",
                          "needs": "code_on_social_security_2020"},
    "statutory_deadline": {"fn": statutory_deadline, "numbers": {}, "dates": {"last_working_day": MESSAGE},
                           "desk": "statute", "needs": "code_on_wages_2019"},
    "threshold_check": {"fn": threshold_check, "numbers": {"headcount": MESSAGE}, "dates": {}, "desk": "statute",
                        "needs": "industrial_relations_code_2020"},
}
_BAR = re.compile(r"\b(?:cannot|can\s+not|not|no)\b[^.]{0,40}\bprobation\b", re.I)


def for_desk(desk: str) -> tuple[str, ...]:
    """The calculators an answer desk runs in agent mode: the handbook's or the Codes'."""
    return tuple(n for n, c in CALCULATORS.items() if c["desk"] == desk)


def calculate(name: str, found: dict | None = None, **args) -> dict:
    """One calculator by name, with its arguments (already checked by check_args) and what the check found, from which
    code sets what the model does not: the clause the notice days came from, and a probation bar in the encashment
    clause."""
    if name not in CALCULATORS:
        raise CalcError(f"no calculator {name!r}")
    found = found or {}
    if name == "notice_end" and isinstance(found.get("days"), dict):
        args["clause"] = found["days"]["clause"]
    if name == "encashable_days" and isinstance(found.get("cap"), dict):
        args["probation_bar"] = bool(_BAR.search(found["cap"]["text"]))
    try:
        return CALCULATORS[name]["fn"](**args)
    except TypeError as e:          # a missing or unknown argument
        raise CalcError(str(e)) from None


# ---------------------------------------------------------------------------------------------- the argument check
_UNITS = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
          "seventeen eighteen nineteen").split()
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_WORDS = re.compile(r"\b(?:(" + "|".join(_TENS) + r")(?:[\s-](" + "|".join(_UNITS[1:10]) + r"))?|(" + "|".join(_UNITS)
                    + r"))\b", re.I)
# Digits not glued to a letter on the left (E3, LV-07, IT-SEC-04 are names, not numbers): 40,000 and 1,50,000 grouped,
# a decimal part, and lakh, crore or k after it.
_DIGITS = re.compile(r"(?<![A-Za-z0-9])(?<![A-Za-z]-)(\d{1,3}(?:,\d{2,3})+|\d+)(\.\d+)?(?!\d)"
                     r"(?:\s?(lakhs?|lacs?|crores?|k)\b)?", re.I)
_SCALE = {"lakh": 100_000, "lakhs": 100_000, "lac": 100_000, "lacs": 100_000, "crore": 10_000_000,
          "crores": 10_000_000, "k": 1000}
_MONTHS = {m: i for i, names in enumerate((("jan", "january"), ("feb", "february"), ("mar", "march"), ("apr", "april"),
                                           ("may",), ("jun", "june"), ("jul", "july"), ("aug", "august"),
                                           ("sep", "sept", "september"), ("oct", "october"), ("nov", "november"),
                                           ("dec", "december")), 1) for m in names}
_MON = r"(" + "|".join(sorted(_MONTHS, key=len, reverse=True)) + r")\.?"
_ORD = r"(?:st|nd|rd|th)?"
_DATES = (
    (re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"), ("y", "m", "d")),
    (re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b"), ("d", "m", "y")),          # day first, as India writes it
    (re.compile(r"\b(\d{1,2})" + _ORD + r"\s+(?:of\s+)?" + _MON + r",?\s+(\d{4})\b", re.I), ("d", "M", "y")),
    (re.compile(r"\b" + _MON + r"\s+(\d{1,2})" + _ORD + r",?\s+(\d{4})\b", re.I), ("M", "d", "y")),
)
# Whatever reads as a date, a year or not (31 December, 05/10, October 2026): its digits are never numbers of their own.
_DATE_LIKE = re.compile(
    r"\b\d{4}-\d{1,2}-\d{1,2}\b|\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b|\b\d{1,2}/\d{1,2}\b"
    r"|\b\d{1,2}" + _ORD + r"\s+(?:of\s+)?" + _MON + r"(?:,?\s+\d{4})?\b"
    r"|\b" + _MON + r"\s+\d{1,2}" + _ORD + r"(?:,?\s+\d{4})?\b"
    r"|\b" + _MON + r",?\s+\d{4}\b", re.I)
# A clause code: LV-01, NP-03, IT-SEC-04, GEN-000.
_CLAUSE = re.compile(r"\b[A-Z]{2,4}(?:-[A-Z]{2,4})*-\d{2,3}\b")
# A negation just before a flag's words: "not fixed-term", "isn't on a fixed term", "non-fixed-term", "has not expired".
_NEGATED = re.compile(r"(?:\b(?:not|no|never|without|nor)|n't|\bnon)\W*(?:\w+\W+){0,2}$", re.I)


def numbers_in(text: str) -> set[Decimal]:
    """Every number written in the text, as digits or words, normalised (45 == 45.0; 40,000 == 40000). The digits of
    a date are not numbers here."""
    text = text or ""
    dates = [m.span() for m in _DATE_LIKE.finditer(text)]
    out: set[Decimal] = set()
    for m in _DIGITS.finditer(text):
        if any(a < m.end(1) and m.start(1) < b for a, b in dates):
            continue
        d = Decimal(m.group(1).replace(",", "") + (m.group(2) or ""))
        out.add(d.normalize())
        if m.group(3):
            out.add((d * _SCALE[m.group(3).lower()]).normalize())
    for m in _WORDS.finditer(text):
        if m.group(3):
            out.add(Decimal(_UNITS.index(m.group(3).lower())))
        else:
            out.add(Decimal(_TENS[m.group(1).lower()] + (_UNITS.index(m.group(2).lower()) if m.group(2) else 0)))
    return out


def dates_in(text: str) -> set[date]:
    """Every whole date written in the text: ISO, day first with / . or -, or with the month's name (5 October 2026,
    October 5, 2026). A date with no year is not one."""
    out: set[date] = set()
    for rx, order in _DATES:
        for m in rx.finditer(text or ""):
            parts = dict(zip(order, m.groups()))
            try:
                month = _MONTHS[parts["M"].lower().rstrip(".")] if "M" in parts else int(parts["m"])
                out.add(date(int(parts["y"]), month, int(parts["d"])))
            except (KeyError, ValueError):
                continue
    return out


def said(pattern: str, message: str) -> bool:
    """The message says it: the pattern matches, and not just after a negation."""
    message = message or ""
    return any(not _NEGATED.search(message[max(0, m.start() - 30):m.start()])
               for m in re.finditer(pattern, message, re.I))


def clause_text(passage: dict, code: str) -> str:
    """Clause `code`'s words in one passage: from each place its code is written to the next clause code or the end;
    or, when the passage's section is that clause and the code is not written in it, the text before any other code.
    Empty when the passage does not hold the clause."""
    text = str(passage.get("text") or "")
    marks = list(_CLAUSE.finditer(text))
    parts = [text[m.end():(marks[i + 1].start() if i + 1 < len(marks) else len(text))]
             for i, m in enumerate(marks) if m.group(0) == code]
    if not parts and re.match(re.escape(code) + r"\b", str(passage.get("section") or "").strip()):
        parts = [text[:marks[0].start()] if marks else text]
    return " ".join(parts)


def _in_clause(want: Decimal, codes, passages) -> dict | None:
    """The first handbook passage (doc_type policy) whose clause, one of `codes`, writes `want`: {n, clause, text}."""
    for i, p in enumerate(passages or (), 1):
        if not isinstance(p, dict) or p.get("doc_type") != "policy":
            continue
        for code in codes:
            text = clause_text(p, code)
            if text and want in numbers_in(text):
                return {"n": i, "clause": code, "text": text}
    return None


def check_args(name: str, args: dict, passages, message: str) -> tuple[list[str], dict]:
    """(refusals, found) for one calculator call. passages are this turn's, in the order the turn numbered them (from
    1), each a dict with its text, section and doc_type. Each argument must be written where CALCULATORS says: a fact
    about the person in their message, a handbook figure in its clause of a handbook passage. found says where:
    "message", or {n, clause, text} for a passage's clause. A flag is true only when the message says it, unnegated. A
    word (event) is not checked here; the calculator checks its value."""
    spec = CALCULATORS[name]
    refused, found = [], {}
    said_numbers, said_dates = numbers_in(message), dates_in(message)
    for arg, source in spec["numbers"].items():
        if args.get(arg) is None:
            continue
        try:
            want = _dec(args[arg], arg).normalize()
        except CalcError as e:
            refused.append(str(e))
            continue
        if source == MESSAGE:
            if want in said_numbers:
                found[arg] = MESSAGE
            else:
                refused.append(f"{arg} = {num(want)} is a fact about the person that their message does not state: "
                               f"ask them for it")
            continue
        hit = _in_clause(want, source, passages)
        if hit:
            found[arg] = hit
        else:
            refused.append(f"{arg} = {num(want)} is not written in {' or '.join(source)} of a handbook passage this "
                           f"turn read: search for that clause and use the figure it states")
    for arg in spec["dates"]:
        if args.get(arg) is None:
            continue
        try:
            want_day = day_of(args[arg], arg)
        except CalcError as e:
            refused.append(str(e))
            continue
        if want_day in said_dates:
            found[arg] = MESSAGE
        else:
            refused.append(f"{arg} = {want_day.isoformat()} is not a date the person's message states (a date is "
                           f"read day first): ask them for it")
    for arg, pattern in spec.get("flags", {}).items():
        if args.get(arg) is True:
            if said(pattern, message):
                found[arg] = MESSAGE
            else:
                refused.append(f"{arg} is true only when the person's message says so")
    return refused, found


# ---------------------------------------------------------------------------------------------- the selftest
def _corpus_text(rel: str, lines: str) -> str:
    root = Path(__file__).resolve().parents[1] / "evals" / "corpus"
    lo, _, hi = lines.partition("-")
    rows = (root / rel).read_text(encoding="utf-8").split("\n")      # grep -n's lines: a form feed ends none
    return " ".join(rows[int(lo) - 1:int(hi or lo)])


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("( ", "(")).strip()


def _clause_passage(rel: str, code: str) -> dict:
    """A handbook clause as the chunker makes it (its heading, then its paragraph), for the selftest."""
    rows = (Path(__file__).resolve().parents[1] / "evals" / "corpus" / rel).read_text(encoding="utf-8").split("\n")
    at = next(i for i, r in enumerate(rows) if r.startswith(f"## {code} "))
    body = []
    for r in rows[at + 1:]:
        if r.startswith("## "):
            break
        body.append(r)
    return {"text": rows[at][3:] + "\n" + "\n".join(body).strip(), "section": rows[at][3:], "doc_type": "policy"}


def _multiplies_out(formula: str) -> bool:
    """The gratuity formula's expression, evaluated as shown, gives the figure shown (to the rupee)."""
    m = re.search(r"Rs ([\d,.]+) ((?:[/x] \d+ ?)+)= Rs ([\d,]+)", formula)
    if not m:
        return False
    v = Decimal(m.group(1).replace(",", ""))
    for op, n in re.findall(r"([/x]) (\d+)", m.group(2)):
        v = v / Decimal(n) if op == "/" else v * Decimal(n)
    return v.quantize(Decimal("1"), rounding=ROUND_HALF_UP) == Decimal(m.group(3).replace(",", ""))


def selftest() -> int:
    failures = []

    def check(ok: bool, what: str) -> None:
        print(("ok    " if ok else "FAIL  ") + what)
        if not ok:
            failures.append(what)

    for key, r in RULES.items():
        got = _squash(_corpus_text(r["file"], r["lines"]))
        check(_squash(r["quote"]) in got, f"{key}: {r['file']}:{r['lines']} says it")
    check(GRATUITY_DAYS == 15 and "fifteen days' wages" in RULES["gratuity_rate"]["quote"], "fifteen days' wages")
    check(GRATUITY_DIVISOR == 26 and "twenty-six" in RULES["gratuity_monthly"]["quote"], "divided by twenty-six")
    check(GRATUITY_MIN_YEARS == 5 and "five years" in RULES["gratuity_service"]["quote"], "five years' service")
    check(WAGE_DAYS == 2 and "two working days" in RULES["wages_s17_2"]["quote"], "two working days")
    check(THRESHOLDS["grc"]["at_least"] == 20 and "twenty or more workers" in RULES["ir_s4_1"]["quote"],
          "twenty workers")
    check("1.75 days per completed month" in RULES["accrual"]["quote"], "1.75 days a completed month")
    check("maximum of 18 days" in RULES["carry_forward_zeta"]["quote"], "zeta carries 18 forward")

    check(encashable_days(50, 45)["value"] == 45, "min(50, 45) = 45 (LV-07)")
    check(encashable_days(50, 45)["basis"] == [{"source": HANDBOOK, "clause": "LV-07"}],
          "a handbook result names the clause and carries no company's words")
    check(encashable_days(30, 45)["formula"] == "min(30, 45) = 30 days", "the formula is shown")
    check(carry_forward(34, 30)["value"] == 30 and carry_forward(34, 30)["lapses"] == 4, "carry forward 30, 4 lapse")
    check(carry_forward(22, 18)["value"] == 18, "zeta's cap of 18")
    check(accrued_leave(8, 1.75)["value"] == 14 and "not a balance" in accrued_leave(8, 1.75)["notes"][0],
          "8 completed months x 1.75 = 14 days, accrued, not a balance")
    check(_raises(lambda: accrued_leave(8.5, 1.75)), "a part month is refused")
    ne = notice_end("2026-10-05", 60)
    check(ne["value"] == "2026-12-04" and ne["cites"] == "NP-03", "notice: 5 Oct 2026 + 60 days = 4 Dec 2026, NP-03")
    check(notice_end("2026-10-05", 15, clause="PB-02")["cites"] == "PB-02, NP-03", "probation notice cites PB-02")
    g = gratuity_estimate(52000, 7, 8)
    check(g["value"] == 240000 and g["estimate"] and g["formula"].endswith("Rs 52,000 / 26 x 15 x 8 = Rs 2,40,000"),
          "gratuity: Rs 52,000 / 26 x 15 x 8 (7 years 8 months) = Rs 2,40,000, an estimate")
    check(NO_CEILING in g["notes"], "no ceiling applied, and said")
    check(gratuity_estimate(52000, 7, 6)["value"] == 210000, "six months is not in excess of six months")
    g4 = gratuity_estimate(52000, 4, 11)
    check(g4["value"] is None and g4["eligible"] is False and g4["estimate"],
          "under five years: not payable, an estimate")
    g50 = gratuity_estimate(50000, 7, 8)
    check(g50["value"] == 230769 and _multiplies_out(g50["formula"]) and "nearest rupee" in g50["formula"],
          "Rs 50,000 / 26 x 15 x 8 = Rs 2,30,769: the shown arithmetic multiplies out")
    gf = gratuity_estimate(30000, 1, 5, fixed_term=True)
    check(gf["value"] == 24519 and _multiplies_out(gf["formula"]) and "x 17 / 12" in gf["formula"],
          "fixed term pro rata: Rs 30,000 / 26 x 15 x 17 / 12 = Rs 24,519")
    check(gf["eligible"] is None and "expiry of the fixed term" in gf["conditions"][0],
          "a fixed term under five years: payable only on the term's expiry, a condition")
    check(gratuity_estimate(30000, 1, 5, fixed_term=True, term_expired=True)["eligible"] is True,
          "the term expired: the five years are waived")
    check(all(r["estimate"] for r in (g, g4, gf)), "a gratuity result is always an estimate")
    sd = statutory_deadline("resignation", "2026-10-02")
    check(sd["value"] == "2026-10-06" and NO_HOLIDAYS in sd["notes"] and "last working day" in sd["formula"],
          "last working day Friday 2 Oct + 2 working days = Tuesday 6 Oct")
    check(_raises(lambda: statutory_deadline("closure", "2026-10-02")),
          "an event s.17(2) does not count from is refused")
    check(threshold_check(20)["value"] is True and threshold_check(19)["value"] is False, "20 workers and over: a GRC")
    check(inr(150000) == "Rs 1,50,000" and inr(999) == "Rs 999" and inr(12345678) == "Rs 1,23,45,678",
          "Indian grouping")

    lv01, lv07 = _clause_passage("acme/hr_policy_2026.md", "LV-01"), _clause_passage("acme/hr_policy_2026.md", "LV-07")
    np03, pb02 = _clause_passage("acme/hr_policy_2026.md", "NP-03"), _clause_passage("acme/hr_policy_2026.md", "PB-02")
    z01, z03 = (_clause_passage("zeta/hr_policy_zeta_2026.md", "LV-01"),
                _clause_passage("zeta/hr_policy_zeta_2026.md", "NP-03"))
    s53 = {"text": RULES["gratuity_service"]["quote"], "section": "53", "doc_type": "statute"}
    s41 = {"text": RULES["ir_s4_1"]["quote"], "section": "4", "doc_type": "statute"}
    msg = "I am an E3 leaving with 50 days of earned leave. How much is encashed?"
    check(check_args("encashable_days", {"balance": 50, "cap": 45}, [np03, lv07], msg)
          == ([], {"balance": MESSAGE, "cap": {"n": 2, "clause": "LV-07", "text": clause_text(lv07, "LV-07")}}),
          "50 from the message, 45 from LV-07 in passage 2")
    check(calculate("encashable_days", found=check_args("encashable_days", {"balance": 50, "cap": 45}, [lv07],
                                                        msg)[1], balance=50, cap=45)["conditions"] != [],
          "LV-07's probation bar is stated as a condition")
    check(check_args("carry_forward", {"days": 40, "cap": 30}, [lv01, lv07], "I will have 40 days left.")[0] == [],
          "acme: the cap 30 from LV-01")
    check(check_args("carry_forward", {"days": 40, "cap": 45}, [lv01, lv07], "I will have 40 days left.")[0] != [],
          "acme: LV-07's 45 is not LV-01's cap")
    check(check_args("carry_forward", {"days": 40, "cap": 31}, [lv01], "I will have 40 days left.")[0] != [],
          "LV-01's '31 December' is a date, not a cap")
    check(check_args("carry_forward", {"days": 25, "cap": 18}, [z01, z03], "I will have 25 days left.")[0] == [],
          "zeta: the cap 18 from LV-01")
    check(check_args("carry_forward", {"days": 25, "cap": 30}, [z01, z03], "I will have 25 days left.")[0] != [],
          "zeta: NP-03's 30 is not LV-01's cap")
    check(check_args("carry_forward", {"days": 25, "cap": 30}, [z01], "I have 25 days and a cap of 30.")[0] != [],
          "a cap in the message is not the handbook's")
    check(check_args("encashable_days", {"balance": 80, "cap": 100}, [lv07], "I have 80 days and my cap is 100")[0]
          != [], "encashable_days(80, cap=100) from the message is refused")
    check(check_args("threshold_check", {"headcount": 20}, [s41], "Do we need a grievance committee?")[0] != [],
          "a headcount from s.4(1)'s twenty is refused")
    check(check_args("threshold_check", {"headcount": 23}, [s41], "We are 23 workers. Do we need a GRC?")[0] == [],
          "a headcount the person states")
    check(check_args("gratuity_estimate", {"monthly_wage": 50000, "years": 5}, [s53], "I earn 50,000 a month.")[0]
          != [], "years = 5 from 'five years' in s.53 is refused")
    check(check_args("gratuity_estimate", {"monthly_wage": 50000, "years": 1}, [s41], "I earn 50,000 a month.")[0]
          != [], "years = 1 from 'one or more' in s.4(1) is refused")
    check(check_args("notice_end", {"ack_date": "2026-10-05", "days": 10}, [np03], "acknowledged on 05/10/2026")[0]
          != [], "days = 10 from the date 05/10/2026 is refused")
    check(check_args("notice_end", {"ack_date": "2026-10-05", "days": 60}, [np03], "acknowledged on 05/10/2026")
          == ([], {"days": {"n": 1, "clause": "NP-03", "text": clause_text(np03, "NP-03")}, "ack_date": MESSAGE}),
          "the notice days from NP-03, the date from the message, day first")
    found = check_args("notice_end", {"ack_date": "2026-10-05", "days": 15}, [np03, pb02],
                       "On probation; acknowledged on 5th October 2026.")[1]
    check(calculate("notice_end", found=found, ack_date="2026-10-05", days=15)["cites"] == "PB-02, NP-03",
          "probation notice days from PB-02, cited")
    check(check_args("encashable_days", {"balance": 7, "cap": 45}, [lv07], msg)[0] != [], "LV-07's 07 is not a number")
    check(check_args("encashable_days", {"balance": 3, "cap": 45}, [lv07], msg)[0] != [], "E3's 3 is not a number")
    check(check_args("gratuity_estimate", {"monthly_wage": 150000, "years": 7, "months": 8},
                     [], "My wage is Rs 1.5 lakh a month after seven years and 8 months.")[0] == [], "lakh and words")
    check(check_args("gratuity_estimate", {"monthly_wage": 52000, "years": 7, "months": 8},
                     [], "Rs 52,000 a month, 7 years 8 months")[0] == [], "40,000-style grouping")
    check(check_args("notice_end", {"ack_date": "2026-05-10", "days": 60}, [np03], "acknowledged on 05/10/2026")[0]
          != [], "the month first is not the date written")
    check(check_args("statutory_deadline", {"event": "resignation", "last_working_day": "2026-10-02"}, [],
                     "I resigned today.")[0] != [], "a date nobody wrote is refused")
    fixed = {"monthly_wage": 52000, "years": 1, "months": 6, "fixed_term": True}
    check(check_args("gratuity_estimate", fixed, [s53], "Rs 52,000 a month, 1 year 6 months")[0] != [],
          "fixed term only when the person says it")
    check(check_args("gratuity_estimate", fixed, [], "Rs 52,000 a month, a fixed-term contract of 1 year 6 months")
          == ([], {"monthly_wage": MESSAGE, "years": MESSAGE, "months": MESSAGE, "fixed_term": MESSAGE}),
          "a fixed-term contract, said")
    for negated in ("I am not on a fixed-term contract", "a permanent, non-fixed-term role", "it isn't a fixed term"):
        check(check_args("gratuity_estimate", fixed, [], f"Rs 52,000 a month, 1 year 6 months; {negated}")[0] != [],
              f"negated: {negated}")
    check(not said(TERM_EXPIRED, "my fixed term has not expired") and said(TERM_EXPIRED, "my fixed term expired"),
          "the term's expiry, said and unsaid")
    print(f"{len(failures)} failed" if failures else "every rule says what its corpus line says, and the figures hold")
    return 1 if failures else 0


def _raises(fn) -> bool:
    try:
        fn()
    except CalcError:
        return True
    return False


if __name__ == "__main__":
    if sys.argv[1:] != ["--selftest"]:
        print("usage: python shared/desk_calc.py --selftest", file=sys.stderr)
        sys.exit(2)
    sys.exit(selftest())
