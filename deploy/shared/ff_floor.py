#!/usr/bin/env python3
"""The statutory floor under a full and final settlement (the Case Room, Phase 0): what Indian law sets under every
employee's exit whatever a company's handbook says, and what a company's own handbook bars, each rule with its source,
the date it is reported to apply from, and whether a person has checked it. Standard library only.

A DRAFT FOR THE AUTHOR'S REVIEW. Every entry was written by a model on 25 October 2026 from the kit's corpus and from
the research behind the Case Room report (reports/DocuMind multi agent swarm design.md); none is a legal opinion, and
nothing here is shown to a person as settled until a person has checked it (checked: the date they did, else None).

    FLOOR          the rules, by key. Each is one of three kinds:
                   corpus     quoted from the kit's own copy of the Code (evals/corpus/acme/...), so --selftest reads
                              the cited lines and fails when the quote is not there; a rule shared/desk_calc.py already
                              quotes is named by its RULES key instead of quoted twice
                   secondary  a reading the corpus does not hold - a Central Rule, a law firm's or a payroll vendor's -
                              by its URL; never more than "reported"
                   contested  sources disagree, so a person decides it, case by case
    HANDBOOK       a company's own clauses that bar a step of the settlement (NP-03: no set-off of leave against
                   notice; LV-07: no encashment during probation, no shortening of notice), by tenant, quoted from each
                   handbook
    REPORTED       the dates the Codes and their Central Rules are reported to apply from, with the source. The kit
                   shows an in-force date only once a person has checked it against the Gazette (shared/desk_law.py,
                   IN_FORCE): nothing here moves IN_FORCE, and --selftest fails if a date here is marked checked while
                   IN_FORCE still says None
    JURISDICTIONS  the states and union territories whose final rules under each Code were reported as of 1 October
                   2026, and the ones whose rules change a figure of the settlement (fixed-term gratuity), each with
                   its source. A state not listed has no final rules reported: rules_status() says so, and the Case
                   Room never fills that gap with a guess

TRACKS. A settlement has two tracks, so that a disagreement never holds a statutory clock hostage. pay_now is what is
paid within the clock whatever else is argued about: the wages and, for a worker, the leave wages. dispute is anything
a person must decide first: a deduction that needs the employee's explanation, a recovery the Code may not authorise,
a figure whose condition is not yet met. A clock is a due date; a bar is a step the law or the handbook forbids; a
figure is how a calculator works one out (shared/desk_calc.py).

WHO READS IT. The Case Room's Auditor (commands/case_room.py, Phase 1) cites a floor entry in every finding it raises -
a proposed notice-pay recovery is the dispute track's, by notice_pay_not_a_head; a hold until exit clearance meets
no_clearance_condition - and evals/case_eval.py --check holds the case set's escalations to entries here. The Advocate
of Phase 2 reads the whole table against a draft.

    python shared/ff_floor.py --selftest          (from deploy/; standard library only)
    python shared/ff_floor.py --table             the table as a person reviews it
"""
from __future__ import annotations

import re
import sys
from datetime import date

try:                                    # the package import (the services, the tests), and the flat one (this file
    from shared import desk_calc, desk_law      # run as a script, or an image that copies shared/ beside its code)
except ImportError:                     # pragma: no cover
    import desk_calc                    # type: ignore
    import desk_law                     # type: ignore

WAGES, CSS, OSH = desk_calc.WAGES, desk_calc.CSS, desk_law.OSH
RESEARCHED = "2026-10-25"               # the day these entries were written, from the sources each one names

# The sources a secondary entry or a reported date rests on, each read on RESEARCHED for the Case Room report.
SOURCES: dict[str, dict] = {
    "ey_nov_2025": {"who": "EY India tax alert, November 2025",
                    "url": "https://www.ey.com/content/dam/ey-unified-site/ey-com/en-in/alerts-hub/2025/11/"
                           "new-labour-codes-implemented-across-the-country-effective-21-november-2025.pdf"},
    "ey_may_2026": {"who": "EY India alert, 10 May 2026",
                    "url": "https://www.ey.com/en_in/technical/alerts-hub/2026/05/"
                           "final-rules-published-by-central-government-under-new-labour-codes"},
    "bar_bench_may_2026": {"who": "Bar & Bench (Obhan & Associates), 28 May 2026",
                           "url": "https://www.barandbench.com/law-firms/view-point/the-next-phase-of-workforce-"
                                  "compliance-what-the-newly-notified-central-labour-rules-mean-for-employers"},
    "sam_oct_2026": {"who": "Shardul Amarchand Mangaldas, ELB Fine Print, October 2026",
                     "url": "https://www.amsshardul.com/wp-content/uploads/2026/10/ELB-Newsletter-October-2026.pdf"},
    "livelaw_oct_2026": {"who": "LiveLaw, 3 October 2026",
                         "url": "https://www.livelaw.in/articles/two-working-days-code-wages-employee-final-"
                                "settlement-552780"},
    "zoho_aug_2026": {"who": "Zoho Payroll Academy, 19 August 2026",
                      "url": "https://zdblogs.zohocorp.com/payroll/academy/in/payroll-administration/fnf.html"},
}

PARTS = ("wages", "leave", "gratuity", "deductions", "clearance")
TRACKS = ("pay_now", "dispute", "clock", "bar", "figure")
KINDS = ("corpus", "secondary", "contested")


def _floor(kind: str, part: str, track: str, what: str, *, instrument: str | None = None, section: str | None = None,
           rule: str | None = None, file: str | None = None, lines: str | None = None, quote: str | None = None,
           sources=(), applies_to: str = "employee", effective: str | None = "labour_codes", use: str = "",
           note: str = "") -> dict:
    """One floor entry. A corpus entry carries rule (desk_calc.RULES' key) or file, lines and quote; a secondary or
    contested one carries its sources (SOURCES' keys)."""
    return {"kind": kind, "part": part, "track": track, "what": what, "instrument": instrument, "section": section,
            "rule": rule, "file": file, "lines": lines, "quote": quote, "sources": list(sources),
            "applies_to": applies_to, "effective": effective, "use": use, "note": note, "checked": None}


FLOOR: dict[str, dict] = {
    # ------------------------------------------------------------------ wages and the clock
    "wages_two_working_days": _floor(
        "corpus", "wages", "clock",
        "The wages of an employee who resigns, or is removed, dismissed or retrenched, are paid within two working "
        "days of the resignation, removal, dismissal or retrenchment.",
        instrument=WAGES, section="s.17(2)", rule="wages_s17_2",
        use="the Clock Keeper's wages-due clock, worked out by desk_calc.statutory_deadline from the last working day",
        note="The desk counts from the last working day, Monday to Friday, with no holiday calendar: a holiday in "
             "between makes the true date later, never earlier."),
    "wages_other_time_limit": _floor(
        "corpus", "wages", "clock",
        "The appropriate Government may set another time limit for paying wages.",
        instrument=WAGES, section="s.17(3)", rule="wages_s17_3",
        use="a state's rule may move the wages-due clock: rules_status() says whether the state's rules are final"),
    "leave_wages_two_working_days": _floor(
        "corpus", "leave", "pay_now",
        "A worker who quits, or is discharged or dismissed, is paid wages in lieu of unused leave before the expiry of "
        "the second working day from the date of quitting, discharge or dismissal.",
        instrument=OSH, section="s.32(1)(vi)(a)", file="acme/osh_code_2020.md", lines="1545-1547",
        quote="where such worker is discharged or dismissed or quits employment before the expiry of the second "
              "working day from the date of such discharge, dismissal or quitting;",
        applies_to="worker (the OSH Code's s.2(1)(zzl) leaves out, among others, a person employed mainly in a "
                   "managerial or administrative capacity)",
        use="the pay-now track for a worker's leave; for a manager the Auditor raises leave_encashment_bucket",
        note="The figure is the handbook's: LV-07 encashes earned leave on exit at basic pay, up to its cap."),
    "leave_encashment_bucket": _floor(
        "contested", "leave", "dispute",
        "Whether leave encashment is wages that fall due within the two working days of s.17(2) is read both ways: a "
        "lawyer's reading says it is likely to be contested, a payroll vendor's guide puts it in the two-day bucket.",
        instrument=WAGES, section="s.17(2), with s.2(y)", sources=("livelaw_oct_2026", "zoho_aug_2026"),
        use="for an employee who is not a worker, a contested point for the legal reviewer; the encashed days are "
            "still worked out under LV-07"),
    # ------------------------------------------------------------------ deductions
    "deductions_authorised_only": _floor(
        "corpus", "deductions", "bar",
        "No deduction is made from wages except one the Code authorises.",
        instrument=WAGES, section="s.18(1)", file="acme/code_on_wages_2019.md", lines="472-473",
        quote="there shall be no deductions from the wages of the employee, except those as are authorised under "
              "this Code.",
        use="every proposed deduction is checked against the heads of s.18(2) before it can reach any track"),
    "deductions_heads": _floor(
        "corpus", "deductions", "bar",
        "A deduction may be made only for the purposes s.18(2) lists: fines, absence, damage or loss of goods "
        "entrusted, housing and amenities, advances and overpayment, loans, taxes, social security, and the rest.",
        instrument=WAGES, section="s.18(2)", file="acme/code_on_wages_2019.md", lines="496-497",
        quote="Deductions from the wages of an employee shall be made in accordance with the provisions of this Code, "
              "and may be made only for the following purposes",
        use="a proposed deduction whose head is not listed is refused for the pay-now track"),
    "deductions_damage_or_loss": _floor(
        "corpus", "deductions", "dispute",
        "Damage to or loss of goods expressly entrusted to the employee, directly attributable to their neglect or "
        "default, is a head a deduction may be made for.",
        instrument=WAGES, section="s.18(2)(c)", file="acme/code_on_wages_2019.md", lines="500-502",
        quote="deductions for damage to or loss of goods expressly entrusted to the employee for custody; or for loss "
              "of money for which he is required to account, where such damage or loss is directly attributable to "
              "his neglect or default;",
        use="a proposed damage deduction goes to the dispute track: see damage_show_cause"),
    "deductions_advances": _floor(
        "corpus", "deductions", "dispute",
        "Recovery of an advance, with its interest, or of an overpayment of wages is a head a deduction may be made "
        "for.",
        instrument=WAGES, section="s.18(2)(f)(i)", file="acme/code_on_wages_2019.md", lines="516-518",
        quote="advances of whatever nature (including advances for travelling allowance or conveyance allowance), and "
              "the interest due in respect thereof, or for adjustment of overpayment of wages;",
        use="a proposed advance recovery is a dispute-track item a person confirms; the 50% cap holds"),
    "deductions_cap_fifty_per_cent": _floor(
        "corpus", "deductions", "bar",
        "The deductions in a wage period never exceed fifty per cent of the wages.",
        instrument=WAGES, section="s.18(3)", file="acme/code_on_wages_2019.md", lines="552-554",
        quote="the total amount of deductions which may be made under sub-section (2) in any wage period from the "
              "wages of an employee shall not exceed fifty per cent. of such wages.",
        use="the Advocate's check (Phase 2), once a calculator works out the final wages in rupees"),
    "damage_not_above_loss": _floor(
        "corpus", "deductions", "bar",
        "A deduction for damage or loss never exceeds the damage or loss the employee's negligence or default caused.",
        instrument=WAGES, section="s.21(1)", file="acme/code_on_wages_2019.md", lines="605-607",
        quote="A deduction under clause (c) or clause (n) of sub-section (2) of section 18 for damage or loss shall "
              "not exceed the amount of the damage or loss caused to the employer by negligence or default of the "
              "employee.",
        use="the legal reviewer's brief on a damage deduction"),
    "damage_show_cause": _floor(
        "corpus", "deductions", "dispute",
        "No damage or loss deduction is made until the employee has had an opportunity to show cause against it.",
        instrument=WAGES, section="s.21(2)", file="acme/code_on_wages_2019.md", lines="608-609",
        quote="A deduction shall not be made under sub-section (1) until the employee has been given an opportunity "
              "of showing cause against the deduction",
        use="the two-track split: the explanation cannot fit inside the two-day clock, so the deduction waits on the "
            "dispute track and the wages are paid on time"),
    "damage_seven_days": _floor(
        "secondary", "deductions", "dispute",
        "The Central Wages Rules give the employee seven days to explain before a damage or loss deduction (Rule 18).",
        instrument="Code on Wages (Central) Rules, 2026", section="r.18", sources=("bar_bench_may_2026",),
        effective="central_rules", applies_to="an establishment whose appropriate Government is the Centre",
        use="the length of the dispute track's wait for a damage deduction, where the Central Rules apply"),
    "notice_pay_not_a_head": _floor(
        "secondary", "deductions", "dispute",
        "Recovering unserved notice pay, a joining bonus or a training bond from the final wages is not among the "
        "heads of s.18(2), so setting it off is hard to reconcile with the Code; the employer may pursue it "
        "separately.",
        instrument=WAGES, section="s.18(2)", sources=("livelaw_oct_2026",),
        use="never on the pay-now track: a proposed notice-pay recovery is a dispute-track point for the legal "
            "reviewer"),
    "no_clearance_condition": _floor(
        "secondary", "clearance", "bar",
        "Payment of the final wages cannot be made conditional on exit clearance or a no-dues declaration; a "
        "deduction for lost entrusted goods may be allowed, withholding the whole payment is not.",
        instrument=WAGES, section="s.17(2), s.18", sources=("livelaw_oct_2026",),
        use="a proposed hold until clearance is refused for the pay-now track and raised to the legal reviewer"),
    "excess_deductions_carry_forward": _floor(
        "secondary", "deductions", "dispute",
        "Deductions above fifty per cent carry forward to later wage periods, under the same cap (Central Wages Rules, "
        "Rule 13).",
        instrument="Code on Wages (Central) Rules, 2026", section="r.13", sources=("bar_bench_may_2026",),
        effective="central_rules", applies_to="an establishment whose appropriate Government is the Centre"),
    # ------------------------------------------------------------------ gratuity
    "gratuity_five_years": _floor(
        "corpus", "gratuity", "figure",
        "Gratuity is payable on the end of employment after five years of continuous service.",
        instrument=CSS, section="s.53(1)", rule="gratuity_service", use="desk_calc.gratuity_estimate"),
    "gratuity_five_years_waived": _floor(
        "corpus", "gratuity", "figure",
        "The five years are not needed when employment ends by death or disablement, or on the expiry of a fixed "
        "term.",
        instrument=CSS, section="s.53(1), second proviso", rule="gratuity_no_five_years",
        use="desk_calc.gratuity_estimate: a fixed term under five years is conditional until the term has expired"),
    "gratuity_rate": _floor(
        "corpus", "gratuity", "figure",
        "Fifteen days' wages for every completed year of service, or part of one in excess of six months; for a "
        "monthly-rated employee, the monthly wage divided by twenty-six and multiplied by fifteen.",
        instrument=CSS, section="s.53(2), Explanation 3", rule="gratuity_rate", use="desk_calc.gratuity_estimate"),
    "gratuity_fixed_term_pro_rata": _floor(
        "corpus", "gratuity", "figure",
        "A fixed-term employee is paid gratuity pro rata.",
        instrument=CSS, section="s.53(2), third proviso", rule="gratuity_fixed_term",
        use="desk_calc.gratuity_estimate(fixed_term=True)"),
    "gratuity_ceiling": _floor(
        "corpus", "gratuity", "figure",
        "Gratuity never exceeds the amount the Central Government notifies; the corpus does not hold the amount.",
        instrument=CSS, section="s.53(3)", rule="gratuity_ceiling",
        use="no ceiling is applied (desk_calc.NO_CEILING): a large estimate is a point for the legal reviewer",
        note="The notified amount must be entered by a person who has read the notification; until then the "
             "estimate says no ceiling was applied."),
    "gratuity_better_terms": _floor(
        "corpus", "gratuity", "figure",
        "An award, agreement or contract that gives better gratuity terms wins.",
        instrument=CSS, section="s.53(5)", file="acme/code_on_social_security_2020.md", lines="2259-2260",
        quote="Nothing in this section shall affect the right of an employee to receive better terms of gratuity "
              "under any award or agreement or contract with the employer.",
        use="the estimate's note; a contract term a person states is a point for the legal reviewer"),
    "gratuity_forfeiture": _floor(
        "corpus", "gratuity", "dispute",
        "Gratuity is forfeited to the extent of the damage or loss when services are terminated for an act, wilful "
        "omission or negligence that caused it, and may be forfeited for riotous or disorderly conduct, violence, or "
        "an offence involving moral turpitude in the course of employment.",
        instrument=CSS, section="s.53(6)", file="acme/code_on_social_security_2020.md", lines="2262-2265",
        quote="the gratuity of an employee, whose services have been terminated for any act, wilful omission or "
              "negligence causing any damage or loss to, or destruction of, property belonging to the employer, "
              "shall be forfeited to the extent of the damage or loss so caused;",
        use="after a dismissal, the gratuity line is a dispute-track point: the estimate counts no forfeiture"),
    "gratuity_determine_and_notify": _floor(
        "corpus", "gratuity", "clock",
        "As soon as gratuity becomes payable, the employer determines it and gives notice in writing of the amount, "
        "whether or not the employee has applied.",
        instrument=CSS, section="s.56(2)", file="acme/code_on_social_security_2020.md", lines="2361-2364",
        quote="As soon as gratuity becomes payable, the employer shall, whether an application referred to in "
              "sub-section (1) has been made or not, determine the amount of gratuity and give notice in writing",
        use="the statement's gratuity line is that determination, made by a person: the case's sign-off"),
    "gratuity_thirty_days": _floor(
        "corpus", "gratuity", "clock",
        "Gratuity is paid within thirty days from the date it becomes payable.",
        instrument=CSS, section="s.56(3)", file="acme/code_on_social_security_2020.md", lines="2365-2366",
        quote="The employer shall arrange to pay the amount of gratuity within thirty days from the date it becomes "
              "payable to the person to whom the gratuity is payable.",
        use="the gratuity clock: thirty days from the last working day, the desk's reading of when it becomes "
            "payable on a resignation"),
    "gratuity_interest": _floor(
        "corpus", "gratuity", "clock",
        "Gratuity paid late carries simple interest from the date it became payable, at a rate the Central Government "
        "notifies.",
        instrument=CSS, section="s.56(4)", file="acme/code_on_social_security_2020.md", lines="2367-2369",
        quote="If the amount of gratuity payable under sub-section (3) is not paid by the employer within the period "
              "specified in sub-section (3), the employer shall pay, from the date on which the gratuity becomes "
              "payable to the date on which it is paid, simple interest",
        use="why the gratuity clock is a clock, not a target"),
    "fixed_term_rounding": _floor(
        "secondary", "gratuity", "figure",
        "Under the Central Social Security Rules a fixed-term employee's later part-year over six months but under a "
        "year counts as a full year (Rule 33); some states set a one-year minimum, and Gujarat five years under the "
        "contract.",
        instrument="Code on Social Security (Central) Rules, 2026", section="r.33",
        sources=("bar_bench_may_2026", "sam_oct_2026"), effective="central_rules",
        applies_to="a fixed-term employee", use="JURISDICTIONS: a fixed-term case's state can change its gratuity"),
}

# A company's own clauses that bar a step of the settlement, by tenant: the handbook passage is the source, so each is
# quoted from that tenant's file. A tenant with no handbook (globex holds none) has no bar here, and no clause to
# work a notice date or an encashment from either.
HANDBOOK: dict[str, dict[str, dict]] = {
    tenant: {
        "no_leave_set_off": {"clause": "NP-03", "file": f"{tenant}/{name}", "lines": "8-9", "track": "bar",
                             "quote": "Unused earned leave may not be set off against the notice period.",
                             "use": "a proposal to set leave off against the notice is refused; the notice end date "
                                    "stays NP-03's"},
        "no_probation_encashment": {"clause": "LV-07", "file": f"{tenant}/{name}", "lines": "24-25", "track": "bar",
                                    "quote": "Leave cannot be encashed during probation and cannot be used to shorten "
                                             "notice.",
                                    "use": "a leaver still on probation has no encashment line to pay; the days are "
                                           "worked out and marked barred"},
    }
    for tenant, name in (("acme", "hr_policy_2026.md"), ("zeta", "hr_policy_zeta_2026.md"))
}

# The dates the Codes and their Central Rules are reported to apply from. desk_law.IN_FORCE holds the date a person
# checked against the Gazette, and until they do, the kit shows none.
REPORTED: dict[str, dict] = {
    "labour_codes": {"what": "The four Labour Codes", "from": "2025-11-21", "sources": ["ey_nov_2025"],
                     "note": "Notifications S.O. 5319(E) to 5322(E), as the source reports them; the transition keeps "
                             "the relevant provisions of the repealed laws in force meanwhile.",
                     "checked": None},
    "central_rules": {"what": "The final Central Rules under all four Codes", "from": "2026-05-08",
                      "sources": ["ey_may_2026", "bar_bench_may_2026"],
                      "note": "Bar & Bench gives 8 and 9 May 2026. They apply only where the Centre is the "
                              "appropriate Government (railways, mines, banking, insurance, central public sector "
                              "undertakings, per the ministry's FAQs of 16 March 2026); other establishments follow "
                              "their state's rules.",
                      "checked": None},
}

CODES = ("wages", "social_security", "industrial_relations", "osh")
_SAM = "sam_oct_2026"
# As of 1 October 2026 (the source's own date): the states and union territories with final rules under each Code, and
# the fixed-term gratuity rule where a state's differs from the Code's. Every other state: no final rules reported.
_FINAL = {
    "Andhra Pradesh": CODES, "Arunachal Pradesh": CODES, "Bihar": CODES, "Gujarat": CODES,
    "Jammu and Kashmir": ("industrial_relations", "osh"), "Ladakh": CODES, "Lakshadweep": CODES,
    "Rajasthan": ("wages", "industrial_relations", "osh"), "Uttarakhand": ("wages", "industrial_relations"),
    "Uttar Pradesh": ("wages", "social_security", "osh"),
}
_FIXED_TERM = {
    "Gujarat": "five years of service under the contract before gratuity is payable",
    "Arunachal Pradesh": "a one-year minimum; fifteen days' wages a completed year or part over six months",
    "Ladakh": "a one-year minimum; fifteen days' wages a completed year or part over six months",
    "Lakshadweep": "a one-year minimum; fifteen days' wages a completed year or part over six months",
    "Uttar Pradesh": "a one-year minimum; fifteen days' wages a completed year or part over six months",
}
AS_OF = "2026-10-01"
JURISDICTIONS: dict[str, dict] = {
    state: {"final_rules": tuple(codes), "fixed_term_gratuity": _FIXED_TERM.get(state), "sources": [_SAM],
            "as_of": AS_OF, "checked": None}
    for state, codes in sorted(_FINAL.items())
}


def entry(key: str) -> dict:
    """A floor entry by key; an unknown key is a programming error, never a silent default."""
    return FLOOR[key]


def basis(key: str) -> str:
    """How a finding cites a floor entry: the instrument and section, then its kind when it is not the corpus's."""
    e = FLOOR[key]
    where = ", ".join(x for x in (e["instrument"], e["section"]) if x)
    if e["kind"] == "corpus":
        return where
    return f"{where} ({e['kind']}: {', '.join(SOURCES[s]['who'] for s in e['sources'])})"


def rules_status(state: str | None, code: str) -> str:
    """Whether a state's final rules under a Code were reported by AS_OF: "final", "not reported final", or
    "unknown state" when the case names none. Reported, never checked, until a person checks it."""
    if code not in CODES:
        raise KeyError(code)
    if not state:
        return "unknown state"
    row = JURISDICTIONS.get(state)
    return "final" if row and code in row["final_rules"] else "not reported final"


def fixed_term_rule(state: str | None) -> str | None:
    """A state's own fixed-term gratuity rule, as reported, or None where the Code's stands."""
    return (JURISDICTIONS.get(state or "") or {}).get("fixed_term_gratuity")


def table() -> str:
    """The floor as a person reviews it: one block an entry, its kind, track and source, then the handbook bars, the
    reported dates and the jurisdictions."""
    out = [f"The statutory floor of a full and final settlement: {len(FLOOR)} entries, a draft of {RESEARCHED} for the "
           f"author's review; nothing is checked yet.", ""]
    for key, e in FLOOR.items():
        src = (f"{e['file']}:{e['lines']}" if e["file"] else f"desk_calc.RULES[{e['rule']!r}]" if e["rule"]
               else "; ".join(SOURCES[s]["url"] for s in e["sources"]))
        out += [f"{key}  [{e['kind']}, {e['part']}, {e['track']}]  {basis(key)}", f"    {e['what']}",
                f"    applies to: {e['applies_to']}; source: {src}"]
        if e["use"]:
            out.append(f"    in the Case Room: {e['use']}")
        if e["note"]:
            out.append(f"    note: {e['note']}")
    out += ["", "Handbook bars:"]
    for tenant, bars in HANDBOOK.items():
        for key, b in bars.items():
            out.append(f"  {tenant} {b['clause']} {key}: \"{b['quote']}\" ({b['file']}:{b['lines']})")
    out += ["", "Reported dates (desk_law.IN_FORCE shows none until a person checks one against the Gazette):"]
    for key, r in REPORTED.items():
        out.append(f"  {key}: {r['what']}, from {r['from']} ({', '.join(SOURCES[s]['who'] for s in r['sources'])}); "
                   f"checked: {r['checked'] or 'no'}")
    out += ["", f"Final rules reported as of {AS_OF} ({SOURCES[_SAM]['who']}); every other state: none reported:"]
    for state, j in JURISDICTIONS.items():
        extra = f"; fixed-term gratuity: {j['fixed_term_gratuity']}" if j["fixed_term_gratuity"] else ""
        out.append(f"  {state}: {', '.join(j['final_rules'])}{extra}")
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------- the selftest
def selftest() -> int:
    failures = []

    def check(ok: bool, what: str) -> None:
        print(("ok    " if ok else "FAIL  ") + what)
        if not ok:
            failures.append(what)

    url = re.compile(r"^https://[^\s]+$")
    for key, s in SOURCES.items():
        check(bool(url.match(s["url"])) and bool(s["who"]), f"source {key}: a name and an https URL")
    for key, e in FLOOR.items():
        check(e["kind"] in KINDS and e["part"] in PARTS and e["track"] in TRACKS, f"{key}: kind, part and track known")
        check(e["checked"] is None, f"{key}: unchecked, as a draft is")
        check(e["effective"] in (None, *REPORTED), f"{key}: its effective date is a reported one")
        if e["kind"] == "corpus":
            if e["rule"]:
                check(e["rule"] in desk_calc.RULES and not e["quote"],
                      f"{key}: desk_calc.RULES[{e['rule']!r}], which desk_calc's own selftest holds to its lines")
            else:
                got = desk_calc._squash(desk_calc._corpus_text(e["file"], e["lines"]))
                check(desk_calc._squash(e["quote"]) in got, f"{key}: {e['file']}:{e['lines']} says it")
        else:
            check(bool(e["sources"]) and all(s in SOURCES for s in e["sources"]) and not e["quote"],
                  f"{key}: {e['kind']}, by its sources, with no corpus quote")
    for tenant, bars in HANDBOOK.items():
        for key, b in bars.items():
            got = desk_calc._squash(desk_calc._corpus_text(b["file"], b["lines"]))
            held = desk_calc._squash(desk_calc._clause_passage(b["file"], b["clause"])["text"])
            check(desk_calc._squash(b["quote"]) in got and desk_calc._squash(b["quote"]) in held,
                  f"{tenant} {key}: {b['file']}:{b['lines']} says it, inside {b['clause']}")
    for key, r in REPORTED.items():
        try:
            date.fromisoformat(r["from"])
            parsed = True
        except ValueError:
            parsed = False
        check(parsed and all(s in SOURCES for s in r["sources"]), f"reported {key}: a date and its sources")
    check(desk_law.IN_FORCE["labour_codes"] is None or REPORTED["labour_codes"]["checked"] is not None,
          "no in-force date is shown that a person has not checked (desk_law.IN_FORCE)")
    for state, j in JURISDICTIONS.items():
        check(set(j["final_rules"]) <= set(CODES) and j["sources"] == [_SAM], f"{state}: its Codes and its source")
    check(rules_status("Gujarat", "social_security") == "final"
          and rules_status("Karnataka", "wages") == "not reported final"
          and rules_status(None, "wages") == "unknown state", "rules_status: final, not reported final, unknown")
    check(fixed_term_rule("Gujarat").startswith("five years") and fixed_term_rule("Karnataka") is None,
          "Gujarat's fixed-term gratuity rule, and none where the Code's stands")
    check(desk_calc.WAGE_DAYS == 2 and "two working days" in desk_calc.RULES["wages_s17_2"]["quote"],
          "the wages clock is desk_calc's two working days")
    check(desk_calc.GRATUITY_MIN_YEARS == 5, "the gratuity floor is desk_calc's five years")
    check("thirty days" in FLOOR["gratuity_thirty_days"]["quote"], "gratuity within thirty days (s.56(3))")
    check("fifty per cent" in FLOOR["deductions_cap_fifty_per_cent"]["quote"], "deductions capped at fifty per cent")
    tracks = {e["track"] for e in FLOOR.values()}
    check({"clock", "dispute", "bar", "figure", "pay_now"} <= tracks, "every track has an entry")
    print(f"{len(failures)} failed" if failures else
          f"every corpus entry says what its lines say; {sum(e['kind'] != 'corpus' for e in FLOOR.values())} entries "
          f"rest on secondary sources, and none is checked yet")
    return 1 if failures else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--table"]:
        print(table())
        sys.exit(0)
    if sys.argv[1:] != ["--selftest"]:
        print("usage: python shared/ff_floor.py --selftest | --table", file=sys.stderr)
        sys.exit(2)
    sys.exit(selftest())
