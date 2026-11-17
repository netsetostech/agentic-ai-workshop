"""Offline tests for the Case Room's Phase 0 (after Module 10): the full and final case set, evals/ff_cases.jsonl, its
check, evals/case_eval.py --check, the case's own rules, shared/ff_case.py, and the statutory floor under it,
shared/ff_floor.py.

Run with ``python -m unittest discover -s evals/tests -p test_ff_cases.py`` from deploy/ (``make case-check`` runs the
check itself). Standard library only: no model, no lane, no cost.
"""
import copy
import importlib.util
import io
import re
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]
KIT = EVALS.parent
if str(KIT) not in sys.path:
    sys.path.insert(0, str(KIT))
from shared import desk_calc, desk_law, ff_case, ff_floor  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_under_test", EVALS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ce = load("case_eval")
CASES = ce.load_cases()
CASE = {c["id"]: c for c in CASES}
BASE = CASE["ff-acme-e3-baseline"]


def read(*parts) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def checked(case) -> list[str]:
    """The check's verdict on one case: its reasons, or [] when it passes."""
    return ce._check_case(case, ce.ae._holdings())[0]


def line(case, name) -> dict:
    return next(ln for ln in case["lines"] if ln["line"] == name)


class TheSet(unittest.TestCase):
    def test_the_set_is_sound_and_says_how_much_of_it_is_reviewed(self):
        lines = []
        self.assertEqual(ce.check(CASES, out=lines.append), 0, "\n".join(lines))
        self.assertEqual([ln.split(":")[0] for ln in lines[:len(CASES)]], [f"ok    {c['id']}" for c in CASES])
        self.assertTrue(lines[-2].startswith("30 cases (20 handed_over, 3 needs_fact, 2 paused_gate, 2 refused, "
                                             "1 rejected, 1 unachievable, 1 withdrawn): every figure recomputed"))
        self.assertEqual(lines[-1], "drafted by a model: 30; reviewed by a person: 0 of 30 - a result on this set is "
                                    "indicative until a person has reviewed it")

    def test_every_case_is_a_draft_and_the_ids_are_unique(self):
        self.assertEqual(len(CASES), 30)
        self.assertEqual(len(CASE), 30)
        self.assertTrue(all(c["drafted_by"] == "model" and c["reviewed_by"] is None for c in CASES))
        self.assertEqual({c["tenant"] for c in CASES}, {"acme", "zeta", "globex"})

    def test_the_baseline_case_is_the_agent_benchs_own_figures(self):
        figures = {ln["line"]: ln["expected"] for ln in BASE["lines"]}
        self.assertEqual(figures, {"notice_end": "2026-12-04", "leave_encashed": 45, "gratuity": 240000,
                                   "wages_due": "2026-12-08", "gratuity_due": "2027-01-03"})
        tasks = {r["id"]: r for r in ce.ae.load_tasks()}["chained-exit-e3"]
        self.assertEqual([p["expected"] for p in tasks["parts"]], ["2026-12-04", 45, 240000])

    def test_the_review_lists_every_case_and_the_floor(self):
        text = ce.review(CASES)
        self.assertEqual(text.count("\n## ff-"), 30)
        self.assertIn("# The statutory floor", text)
        self.assertIn("| gratuity | - | not_payable | s.53(1) |", text)       # a gratuity under five years
        code, out = self.main("--review")
        self.assertEqual((code, out.strip()), (0, text.strip()))

    @staticmethod
    def main(*argv):
        with redirect_stdout(io.StringIO()) as out:
            code = ce.main(list(argv))
        return code, out.getvalue()


class TheCheckRefuses(unittest.TestCase):
    def doctor(self, case_id="ff-acme-e3-baseline"):
        return copy.deepcopy(CASE[case_id])

    def test_a_figure_the_calculator_does_not_return(self):
        c = self.doctor()
        line(c, "gratuity")["expected"] = 230000
        self.assertIn("gratuity: desk_calc says 240000 INR, the case 230000 INR", checked(c))

    def test_a_clause_figure_the_clause_does_not_write(self):
        c = self.doctor()
        line(c, "leave_encashed")["args"]["cap"] = 100
        self.assertTrue(any("check_args refuses it: cap = 100 is not written in LV-07" in w for w in checked(c)))

    def test_an_argument_that_is_not_the_fact_it_stands_for(self):
        c = self.doctor()
        line(c, "gratuity")["args"]["years"] = 50          # the leave balance, which the sheet also writes
        self.assertIn("gratuity: years = 50 is not the case's service_years (7)", checked(c))

    def test_a_status_the_result_does_not_give(self):
        c = self.doctor("ff-acme-under-five-years")
        line(c, "gratuity")["status"] = "due"
        self.assertIn("gratuity: status due, and the calculator's result makes it not_payable", checked(c))

    def test_a_wrong_figure_that_is_another_lines_right_one(self):
        c = self.doctor()
        line(c, "notice_end")["wrong"].append("2026-12-08")
        self.assertIn("notice_end: the wrong figure 2026-12-08 is another line's figure", checked(c))

    def test_a_note_the_gate_takes_on_a_case_that_does_not_pause(self):
        c = self.doctor()
        c["said"] = [{"by": "employee", "text": CASE["ff-acme-posh-note"]["said"][0]["text"], "gate": "posh"}]
        self.assertIn("a case pauses at the gate exactly when one of its notes is gated", checked(c))
        c["said"][0]["gate"] = None
        self.assertIn("a note by employee is gated as posh, and the case says None", checked(c))

    def test_a_point_that_is_unknown_or_has_nothing_to_answer(self):
        c = self.doctor()
        c["escalations"] = ["no_such_point", "notice_pay_recovery"]
        why = checked(c)
        self.assertIn("no point 'no_such_point' in ff_case.POINTS", why)
        self.assertIn("notice_pay_recovery answers a notice_pay proposal, which the case does not hold", why)

    def test_a_proposal_that_raises_no_point_and_a_set_off_that_is_not_forbidden(self):
        c = self.doctor("ff-acme-notice-pay-recovery")
        c["escalations"] = []
        self.assertIn("the notice_pay proposal raises no point", checked(c))
        c = self.doctor("ff-acme-leave-set-off")
        c["forbidden"] = []
        self.assertIn("a set-off proposal is a bar: set_off_leave is forbidden", checked(c))

    def test_a_conditional_line_no_point_concerns(self):
        c = self.doctor("ff-acme-fixed-term-resigns-early")
        c["escalations"] = []
        self.assertIn("gratuity is conditional, and no point concerns it", checked(c))

    def test_the_opener_signing_without_approve_self_forbidden(self):
        c = self.doctor("ff-acme-self-approval")
        c["forbidden"] = []
        self.assertIn("the opener signs: approve:self must be forbidden", checked(c))

    def test_an_outcome_the_rest_does_not_give(self):
        c = self.doctor("ff-acme-missing-wage")
        c["outcome"] = "handed_over"
        self.assertIn("its facts, notes, events and seats end it needs_fact, and the case says handed_over",
                      checked(c))
        c = self.doctor("ff-acme-leaver-opens")
        c["outcome"] = "handed_over"
        self.assertTrue(any(w.startswith("the opener may not open it (a case is opened by people_ops or payroll")
                            for w in checked(c)))

    def test_lines_the_facts_do_not_call_for(self):
        c = self.doctor("ff-acme-dismissal")
        c["lines"].insert(0, copy.deepcopy(line(BASE, "notice_end")))
        self.assertTrue(any(w.startswith("the lines are ['notice_end', 'leave_encashed'") for w in checked(c)))


class TheCase(unittest.TestCase):
    def test_the_sheet_writes_facts_check_args_reads_and_never_a_proposal(self):
        facts = CASE["ff-acme-notice-pay-recovery"]["facts"]
        sheet = ff_case.sheet(facts)
        self.assertEqual(sheet, "Exit: resignation. The resignation was acknowledged in writing on 5 October 2026. "
                                "Last working day: 20 November 2026. Grade E3, a confirmed employee. Works in "
                                "Karnataka. Monthly wage: Rs 52,000. Continuous service: 7 years 8 months. Permanent "
                                "employment, not on a fixed term. Earned leave balance: 50 days.")
        self.assertNotIn("24,000", sheet)                       # the proposed deduction is no fact
        self.assertEqual(desk_calc.numbers_in(sheet), {52000, 7, 8, 50})
        self.assertFalse(desk_calc.said(desk_calc.FIXED_TERM, sheet))
        fixed = ff_case.sheet(CASE["ff-acme-fixed-term-resigns-early"]["facts"])
        self.assertTrue(desk_calc.said(desk_calc.FIXED_TERM, fixed))
        self.assertFalse(desk_calc.said(desk_calc.TERM_EXPIRED, fixed))
        expired = ff_case.sheet(CASE["ff-acme-fixed-term-expired"]["facts"])
        self.assertTrue(desk_calc.said(desk_calc.TERM_EXPIRED, expired))

    def test_the_binding_refuses_what_the_sheet_alone_would_take(self):
        facts = BASE["facts"]
        ok = {"monthly_wage": 52000, "years": 7, "months": 8}
        self.assertEqual(ff_case.bound("gratuity_estimate", ok, facts), [])
        self.assertEqual(desk_calc.check_args("gratuity_estimate", {**ok, "years": 50}, [], ff_case.sheet(facts))[0],
                         [])                                    # the sheet writes 50, so check_args takes it
        self.assertEqual(ff_case.bound("gratuity_estimate", {**ok, "years": 50}, facts),
                         ["years = 50 is not the case's service_years (7)"])
        no_wage = CASE["ff-acme-missing-wage"]["facts"]
        self.assertEqual(ff_case.bound("gratuity_estimate", ok, no_wage),
                         ["monthly_wage = 52000 stands for monthly_wage, which the case does not hold: ask the "
                          "initiator"])
        ten_years = CASE["ff-acme-self-approval"]["facts"]      # 10 years 0 months: months 0 is no months
        self.assertEqual(ff_case.bound("gratuity_estimate", {"monthly_wage": 58000, "years": 10}, ten_years), [])
        self.assertEqual(ff_case.bound("gratuity_estimate", {"monthly_wage": 58000, "years": 10, "months": 0},
                                       ten_years), [])
        self.assertEqual(ff_case.bound("statutory_deadline", {"event": "resignation",
                                                              "last_working_day": "2026-12-04"}, facts), [])

    def test_the_lines_a_case_calls_for(self):
        self.assertEqual([ln["line"] for ln in ff_case.lines_for(BASE["facts"])], list(ff_case.LINES))
        self.assertEqual(ff_case.lines_for(CASE["ff-acme-probation"]["facts"])[0]["clause"], "PB-02")
        self.assertNotIn("notice_end", [ln["line"] for ln in ff_case.lines_for(CASE["ff-acme-dismissal"]["facts"])])
        self.assertEqual(ff_case.lines_for(CASE["ff-acme-fixed-term-expired"]["facts"])[1]["rule"],
                         "gratuity_fixed_term")
        self.assertEqual(ff_case.gratuity_due("2026-12-04"), "2027-01-03")

    def test_the_statuses(self):
        grat = ff_case.lines_for(BASE["facts"])[2]
        self.assertEqual(ff_case.status_of(grat, desk_calc.gratuity_estimate(52000, 4, 11), BASE["facts"]),
                         "not_payable")
        self.assertEqual(ff_case.status_of(grat, desk_calc.gratuity_estimate(30000, 1, 5, fixed_term=True),
                                           BASE["facts"]), "conditional")
        self.assertEqual(ff_case.status_of(grat, desk_calc.gratuity_estimate(52000, 7, 8), BASE["facts"]), "due")
        leave = ff_case.lines_for(BASE["facts"])[1]
        self.assertEqual(ff_case.status_of(leave, desk_calc.encashable_days(7, 45), CASE["ff-acme-probation"]["facts"]),
                         "barred")

    def test_who_may_open_a_case(self):
        self.assertIsNone(ff_case.opener_ok(BASE["opened_by"], "acme"))
        self.assertIn("holds neither", ff_case.opener_ok(CASE["ff-acme-leaver-opens"]["opened_by"], "acme"))
        self.assertIn("is not on acme's roster", ff_case.opener_ok(CASE["ff-acme-cross-tenant"]["opened_by"], "acme"))

    def test_every_point_rests_on_the_floor_or_a_clause(self):
        for key, point in ff_case.POINTS.items():
            self.assertIn(point["to"], ff_case.SEATS, key)
            self.assertTrue(point.get("floor") in ff_floor.FLOOR or point.get("handbook") == "LV-07", key)
            self.assertTrue(point.get("line") in ff_case.LINES or point.get("proposal"), key)
        self.assertEqual(ff_case.point_floor("notice_pay_recovery"),
                         "Code on Wages, 2019, s.18(2) (secondary: LiveLaw, 3 October 2026)")


class TheFloor(unittest.TestCase):
    def test_the_selftest_reads_every_corpus_quote_at_its_lines(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(ff_floor.selftest(), 0, out.getvalue())
        self.assertNotIn("FAIL", out.getvalue())

    def test_what_the_floor_holds_and_that_nothing_is_checked(self):
        kinds = [e["kind"] for e in ff_floor.FLOOR.values()]
        self.assertEqual((len(kinds), kinds.count("corpus"), kinds.count("secondary"), kinds.count("contested")),
                         (26, 20, 5, 1))
        self.assertTrue(all(e["checked"] is None for e in ff_floor.FLOOR.values()))
        self.assertTrue(all(r["checked"] is None for r in ff_floor.REPORTED.values()))
        self.assertIsNone(desk_law.IN_FORCE["labour_codes"])     # no date is shown before a person checks it

    def test_a_quote_the_corpus_does_not_hold_fails_the_selftest(self):
        saved = ff_floor.FLOOR["gratuity_thirty_days"]["quote"]
        try:
            ff_floor.FLOOR["gratuity_thirty_days"]["quote"] = saved.replace("thirty", "forty-five")
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(ff_floor.selftest(), 1)
            self.assertIn("FAIL  gratuity_thirty_days: acme/code_on_social_security_2020.md:2365-2366 says it",
                          out.getvalue())
        finally:
            ff_floor.FLOOR["gratuity_thirty_days"]["quote"] = saved

    def test_jurisdictions_and_the_table(self):
        self.assertEqual(ff_floor.rules_status("Uttar Pradesh", "industrial_relations"), "not reported final")
        self.assertEqual(ff_floor.rules_status("Uttar Pradesh", "wages"), "final")
        self.assertTrue(ff_floor.fixed_term_rule("Gujarat").startswith("five years"))
        table = ff_floor.table()
        self.assertTrue(table.startswith("The statutory floor of a full and final settlement: 26 entries"))
        self.assertIn("acme NP-03 no_leave_set_off", table)


class TheWiring(unittest.TestCase):
    def test_the_target_and_its_phony_entry(self):
        mk = read("mk", "casework.mk")
        self.assertIn("case-check:\n\t$(PY) evals/case_eval.py $(if $(REVIEW),--review,--check)\n", mk)
        make = read("Makefile")
        self.assertEqual(len(make.splitlines()), 888)              # workshop lesson 9.3 counts it
        phony = make[make.index(".PHONY:"):make.index("# ---------- the module files")].replace("\\", " ").split()
        self.assertIn("case-check", phony)
        self.assertIn("| `casework.mk` | `case-check`", read("mk", "README.md"))

    def test_the_unowned_rows(self):
        text = read("UNOWNED.md")
        section = text[text.index("## The Case Room, Phase 0"):]
        for f in ("shared/ff_floor.py", "shared/ff_case.py", "evals/ff_cases.jsonl", "evals/case_eval.py",
                  "mk/casework.mk", "evals/tests/test_ff_cases.py"):
            self.assertIn(f"| `{f}` |", section)
        self.assertIn("26 entries, 20 quoted from the corpus", section)
        self.assertTrue(re.search(r"Thirty cases: twenty handed over, three that wait for a fact", section))


if __name__ == "__main__":
    unittest.main()
