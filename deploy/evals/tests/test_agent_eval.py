"""Offline tests for the agent bench's task set and scorer (workshop lessons 10.1-10.3 and 10.5): evals/agent_tasks.jsonl
and evals/agent_eval.py --check, the score of a run, pass@k and pass^k, best-of, --replay and --compare.

Run with ``python -m unittest discover -s evals/tests -p test_agent_eval.py`` from deploy/ (``make agent-tests`` runs
it). Standard library only: no run here calls a model, and the records are written by hand.
"""
import copy
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]
KIT = EVALS.parent
if str(KIT) not in sys.path:
    sys.path.insert(0, str(KIT))
from shared import desk_calc, desk_rules  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_under_test", EVALS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ae = load("agent_eval")
ROWS = ae.load_tasks()
ROW = {r["id"]: r for r in ROWS}
ARM = {"pattern": "loop", "thinking": None, "desk": "astar"}


def calc(name, **args):
    return {**desk_calc.calculate(name, **args), "args": args}


def passage(code, tenant="acme"):
    chunk = ae.clause_chunk(tenant, code)
    return {"n": 1, "source": "hr_policy_2026.md", "section": chunk["section"], "doc_type": "policy", "text": chunk["text"]}


def statute(text, source="code_on_social_security_2020.pdf"):
    return {"n": 1, "source": source, "section": None, "doc_type": "statute", "text": text}


def run(row_id, answer, calcs=(), passages=(), r=0, arm=ARM, **extra):
    return {"row": row_id, "arm": dict(arm), "run": r, "offline": True, "question": ROW[row_id]["question"],
            "answer": answer, "calculations": list(calcs), "passages": list(passages), "model_calls": 3,
            "retrieve_calls": 1, "thinking_tokens": 192, "visible_tokens": 40, "inr": 0.5, "rag_inr": 0.0,
            "stopped_by": None, "error": None, **extra}


def main_out(*argv) -> tuple[int, str]:
    with redirect_stdout(io.StringIO()) as out:
        code = ae.main(list(argv))
    return code, out.getvalue()


class TaskSet(unittest.TestCase):
    def test_the_set_is_sound(self):
        lines = []
        self.assertEqual(ae.check(ROWS, out=lines.append), 0, "\n".join(lines))
        self.assertTrue(lines[-1].startswith("21 rows (11 calc, 5 lookup, 1 trap, 1 refuse, 3 chained): every figure "
                                             "recomputed"))
        self.assertEqual([line.split(":")[0] for line in lines[:-1]], [f"ok    {r['id']}" for r in ROWS])

    def test_every_row_has_its_figure_and_its_clause(self):
        for r in ROWS:
            for part in (r["parts"] if r["kind"] == "chained" else [r]):     # a chained row's figures are its parts'
                self.assertEqual(sorted(set(ae.FIELDS if part is r else ae.PART_FIELDS) - set(part)), [], r["id"])
                self.assertTrue(part["clause"], r["id"])
                self.assertEqual(part["expected"] is None, r["kind"] == "refuse", r["id"])
            self.assertIsNone(desk_rules.gate(r["question"]), r["id"])

    def test_the_rows_the_lessons_name(self):
        g = ROW["calc-gratuity-7y8m"]
        self.assertEqual((g["question"], g["expected"], g["calcs"][0]["args"]),
                         ("I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?", 240000,
                          {"monthly_wage": 52000, "years": 7, "months": 8}))
        self.assertEqual(desk_calc.gratuity_estimate(52000, 7, 8)["value"], 240000)
        self.assertEqual({r["calcs"][0]["calculator"] for r in ROWS if r["kind"] == "calc"}, set(desk_calc.CALCULATORS))
        self.assertEqual([r["id"] for r in ROWS if r["kind"] == "trap"], ["trap-encash-cap"])
        self.assertIn("invented-cap", ROW["calc-encash-invented-cap"]["tags"])

    def failures(self, **change):
        rid = change.pop("row")
        row = copy.deepcopy(ROW[rid])
        row.update(change)
        lines = []
        self.assertEqual(ae.check([row], out=lines.append), 1, lines)
        return lines[0]

    def test_what_check_refuses(self):
        self.assertIn("desk_calc says 240000, the row 240001", self.failures(row="calc-gratuity-7y8m", expected=240001))
        posh = "My manager keeps making sexual comments about my body. How many days of leave can I carry forward?"
        self.assertIn("the hard gate takes it as posh", self.failures(row="lookup-carry-forward", question=posh))
        self.assertIn("check_args refuses it", self.failures(
            row="calc-carry-forward", calcs=[{"calculator": "carry_forward", "args": {"days": 34, "cap": 40}}]))
        self.assertIn("LV-01 does not write 45", self.failures(row="lookup-carry-forward", expected=45, wrong=[]))
        self.assertIn("the wrong figure 30 is the expected one", self.failures(row="lookup-carry-forward", wrong=[30]))
        self.assertIn("the wrong figure 34 is written in the question", self.failures(row="calc-carry-forward", wrong=[34]))
        self.assertIn("check_args takes an invented years", self.failures(
            row="refuse-gratuity-years", question="I earn Rs 60,000 a month after 5 years. How much gratuity?"))
        self.assertIn("is the handbook desk's, not the statute desk's", self.failures(row="calc-carry-forward", desk="statute"))
        self.assertIn("globex holds no industrial_relations_code_2020", self.failures(row="calc-grc-threshold",
                                                                                       tenant="globex"))
        self.assertIn("missing note", self._missing("calc-accrued", "note"))
        self.assertIn("golden lk-03 does not ask this question", self.failures(
            row="lookup-carry-forward", question="How many days of earned leave may I carry forward?"))

    def _missing(self, rid, field):
        row = copy.deepcopy(ROW[rid])
        del row[field]
        lines = []
        ae.check([row], out=lines.append)
        return lines[0]

    def test_an_id_twice_is_refused(self):
        lines = []
        self.assertEqual(ae.check([ROW["calc-accrued"], ROW["calc-accrued"]], out=lines.append), 1)
        self.assertIn("a second row with this id", lines[1])

    def test_the_cli(self):
        code, out = main_out("--check")
        self.assertEqual(code, 0)
        self.assertIn("ok    trap-encash-cap: encashable_days(balance=50, cap=45) = 45 days (LV-07); LV-07 writes 45 days "
                      "itself: the trap", out)


class Scoring(unittest.TestCase):
    def test_the_calculators_figure_is_correct_with_provenance(self):
        s = ae.score(ROW["calc-gratuity-7y8m"], run("calc-gratuity-7y8m", "Gratuity, an estimate: Rs 2,40,000 [1].",
                                                     [calc("gratuity_estimate", monthly_wage=52000, years=7, months=8)]))
        self.assertEqual((s["correct"], s["provenance"], s["unsupported"], s["why"]), (True, True, [], ""))

    def test_the_same_figure_worked_out_by_the_model_has_no_provenance(self):
        s = ae.score(ROW["calc-gratuity-7y8m"], run("calc-gratuity-7y8m", "About Rs 2,40,000 [1]."))
        self.assertEqual((s["correct"], s["provenance"], s["unsupported"]), (True, False, ["2,40,000"]))
        self.assertIn("no gratuity_estimate call returned it", s["why"])

    def test_a_wrong_figure_beside_the_right_one_is_not_correct(self):
        g = [calc("gratuity_estimate", monthly_wage=52000, years=7, months=8)]
        self.assertFalse(ae.score(ROW["calc-gratuity-7y8m"], run("calc-gratuity-7y8m", "Rs 2,30,000.", g))["correct"])
        s = ae.score(ROW["calc-gratuity-7y8m"], run("calc-gratuity-7y8m", "Rs 2,40,000, or Rs 2,10,000 at 7 years.", g))
        self.assertFalse(s["correct"])
        self.assertIn("states 210000", s["why"])

    def test_the_trap_copied_from_the_passage_is_right_and_unproven(self):
        lv07 = passage("LV-07")
        copied = ae.score(ROW["trap-encash-cap"], run("trap-encash-cap", "45 days are encashed [1].", (), [lv07]))
        self.assertEqual((copied["correct"], copied["provenance"], copied["unsupported"]), (True, False, []))
        worked = ae.score(ROW["trap-encash-cap"], run("trap-encash-cap", "45 days are encashed [1].",
                                                      [calc("encashable_days", balance=50, cap=45)], [lv07]))
        self.assertEqual((worked["correct"], worked["provenance"]), (True, True))

    def test_dates_and_the_yes_or_no_row(self):
        ne = [calc("notice_end", ack_date="2026-10-05", days=60)]
        self.assertTrue(ae.score(ROW["calc-notice-e3"], run("calc-notice-e3", "Your notice ends on 4 December 2026.", ne))
                        ["provenance"])
        late = ae.score(ROW["calc-notice-e3"], run("calc-notice-e3", "It ends on 5 December 2026.", ne))
        self.assertEqual((late["correct"], late["unsupported"]), (False, ["2026-12-05"]))
        grc = [calc("threshold_check", headcount=23)]
        self.assertTrue(ae.score(ROW["calc-grc-threshold"], run("calc-grc-threshold", "Yes: it must have one [1].", grc))
                        ["correct"])
        self.assertFalse(ae.score(ROW["calc-grc-threshold"], run("calc-grc-threshold", "No, it is not required.", grc))
                         ["correct"])

    def test_a_lookup_rests_on_its_clause(self):
        lv01 = passage("LV-01")
        ok = ae.score(ROW["lookup-carry-forward"], run("lookup-carry-forward", "Up to 30 days [1].", (), [lv01]))
        self.assertEqual((ok["correct"], ok["provenance"]), (True, True))
        self.assertFalse(ae.score(ROW["lookup-carry-forward"], run("lookup-carry-forward", "Up to 30 days."))["provenance"])
        s53 = statute("Gratuity shall be payable ... after he has rendered continuous service for not less than five years")
        five = ae.score(ROW["lookup-gratuity-years"], run("lookup-gratuity-years", "After five years [1].", (), [s53]))
        self.assertEqual((five["correct"], five["provenance"]), (True, True))
        repealed = statute(s53["text"], source="payment_of_gratuity_act_1972.pdf")
        self.assertFalse(ae.score(ROW["lookup-gratuity-years"],
                                  run("lookup-gratuity-years", "After five years [1].", (), [repealed]))["provenance"])

    def test_a_refusal_names_the_missing_input_and_states_no_figure(self):
        row = ROW["refuse-gratuity-years"]
        good = ae.score(row, run("refuse-gratuity-years", "I need your years of service to work it out."))
        self.assertEqual((good["correct"], good["provenance"]), (True, True))
        bad = ae.score(row, run("refuse-gratuity-years", "For 5 years it would be about Rs 1,73,077."))
        self.assertEqual((bad["correct"], bad["provenance"], bad["unsupported"]), (False, False, ["5", "1,73,077"]))

    def test_a_stopped_or_failed_run_is_scored_and_says_so(self):
        s = ae.score(ROW["calc-accrued"], run("calc-accrued", "I stopped this turn at one of its limits.",
                                              stopped_by="model_calls"))
        self.assertFalse(s["correct"])
        self.assertTrue(s["why"].startswith("stopped by model_calls"))
        self.assertTrue(ae.score(ROW["calc-accrued"], run("calc-accrued", "", error="ReadTimeout"))["why"]
                        .startswith("failed: ReadTimeout"))


class Chained(unittest.TestCase):
    """Lesson 10.2's chained rows: several figures in one question, each part checked and scored as a calc row."""
    FIGURES = "Notice ends on 4 December 2026 [1]. 45 days are encashed [6]. Gratuity, about Rs 2,40,000 [12]."

    def calcs(self, *skip):
        done = [calc("notice_end", ack_date="2026-10-05", days=60), calc("encashable_days", balance=50, cap=45),
                calc("gratuity_estimate", monthly_wage=52000, years=7, months=8)]
        return [c for c in done if c["calculator"] not in skip]

    def test_the_rows(self):
        chained = [r for r in ROWS if r["kind"] == "chained"]
        self.assertEqual([r["id"] for r in chained], ["chained-exit-e3", "chained-exit-saturday",
                                                      "chained-exit-stated-cap"])
        for r in chained:
            self.assertEqual(sorted(r), sorted(ae.CHAINED_FIELDS))
            self.assertEqual(r["desk"], "astar")
            self.assertEqual([p["calcs"][0]["calculator"] for p in r["parts"]],
                             ["notice_end", "encashable_days", "gratuity_estimate"])
        self.assertEqual([[p["expected"] for p in r["parts"]] for r in chained],
                         [["2026-12-04", 45, 240000], ["2026-12-05", 45, 210000], ["2026-12-04", 45, 240000]])
        self.assertEqual(ROW["chained-exit-stated-cap"]["parts"][1]["stated"], {"cap": 100})
        self.assertEqual([r["id"] for r in ae.select(ROWS, "chained")], [r["id"] for r in chained])
        code, out = main_out("--check", "--slice", "chained-exit-stated-cap")
        self.assertEqual(code, 0)
        self.assertIn("encashable_days(balance=80, cap=45) = 45 days (LV-07); the stated cap = 100 is refused by "
                      "check_args; gratuity_estimate(", out)

    def failures(self, rid="chained-exit-stated-cap", part=None, question=None, **change):
        row = copy.deepcopy(ROW[rid])
        if part is None:
            row.update(change)
        else:
            row["parts"][part].update(change)
        row["question"] = question or row["question"]
        lines = []
        self.assertEqual(ae.check([row], out=lines.append), 1, lines)
        return lines[0]

    def test_what_check_refuses(self):
        says_45 = ROW["chained-exit-stated-cap"]["question"].replace("cap is 100 days", "cap is 45 days")
        self.assertIn("part 2: check_args takes the stated cap = 45",
                      self.failures(part=1, stated={"cap": 45}, question=says_45))
        self.assertIn("part 2: the stated cap = 90 is not written in the question", self.failures(part=1, stated={"cap": 90}))
        self.assertIn("part 1: desk_calc says 2026-12-04, the row 2026-12-05",
                      self.failures(part=0, expected="2026-12-05", wrong=[]))
        self.assertIn("part 3: the wrong figure 52000 is written in the question", self.failures(part=2, wrong=[52000]))
        self.assertIn("desk 'handbook': a chained row's figures are both desks'", self.failures(desk="handbook"))
        self.assertIn("a chained row has two figures or more", self.failures(parts=ROW["chained-exit-e3"]["parts"][:1]))
        row = copy.deepcopy(ROW["chained-exit-e3"])
        del row["parts"][1]["search"]
        lines = []
        ae.check([row], out=lines.append)
        self.assertIn("missing part 2 search", lines[0])

    def test_every_figure_by_its_calculator(self):
        r = ROW["chained-exit-e3"]
        s = ae.score(r, run("chained-exit-e3", self.FIGURES, self.calcs()))
        self.assertEqual((s["correct"], s["provenance"], s["unsupported"], s["why"]), (True, True, [], ""))
        two = ae.score(r, run("chained-exit-e3", "Notice ends on 4 December 2026 [1]. Gratuity, about Rs 2,40,000 [12].",
                              self.calcs("encashable_days")))
        self.assertEqual((two["correct"], two["provenance"]), (False, False))
        self.assertEqual(two["why"], "no encashable_days call returned it; encashable_days: the figure is not stated")
        head = ae.score(r, run("chained-exit-e3", self.FIGURES, self.calcs("gratuity_estimate")))
        self.assertEqual((head["correct"], head["provenance"], head["unsupported"]), (True, False, ["2,40,000"]))
        self.assertIn("no gratuity_estimate call returned it", head["why"])
        wrong = ae.score(r, run("chained-exit-e3", self.FIGURES + " At 7 years it would be Rs 2,10,000.", self.calcs()))
        self.assertFalse(wrong["correct"])
        self.assertIn("gratuity_estimate: states 210000", wrong["why"])


class Runs(unittest.TestCase):
    def test_pass_at_k_and_pass_hat_k(self):
        self.assertAlmostEqual(ae.pass_at_k(3, 1, 1), 1 / 3)
        self.assertEqual((ae.pass_at_k(3, 1, 3), ae.pass_hat_k(3, 1, 3), ae.pass_hat_k(3, 3, 3)), (1.0, 0.0, 1.0))
        self.assertEqual(ae.pass_at_k(3, 0, 2), 0.0)
        self.assertAlmostEqual(ae.pass_at_k(5, 2, 2), 1 - 3 / 10)
        self.assertAlmostEqual(ae.pass_hat_k(5, 2, 2), 1 / 10)

    def test_best_of_chooses_by_the_figure_check_alone(self):
        lv07 = passage("LV-07")
        copied = run("trap-encash-cap", "45 days [1].", (), [lv07], r=0)
        worked = run("trap-encash-cap", "45 days [1].", [calc("encashable_days", balance=50, cap=45)], [lv07], r=1)
        self.assertIs(ae.best_of([copied, worked], 2), worked)          # a calculator's figure stated wins
        self.assertIs(ae.best_of([copied, worked], 1), copied)          # only the first N runs are candidates
        head = run("calc-gratuity-7y8m", "About Rs 2,40,000.", r=0)
        honest = run("calc-gratuity-7y8m", "Rs 2,40,000 [1].", [calc("gratuity_estimate", monthly_wage=52000, years=7,
                                                                          months=8)], r=1)
        self.assertIs(ae.best_of([head, honest], 2), honest)            # an unsupported figure loses
        self.assertIs(ae.best_of([honest, dict(honest, run=2)], 2), honest)   # a tie: the earliest
        wrong = run("calc-gratuity-7y8m", "Rs 2,30,769 [1].", [calc("gratuity_estimate", monthly_wage=50000, years=7,
                                                                         months=8)], r=0)
        self.assertIs(ae.best_of([wrong, honest], 2), wrong)            # it never reads the expected figure

    def write(self, records) -> str:
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        self.addCleanup(os.remove, path)
        ae.save(records, path)
        return path

    def test_replay_rescores_saved_runs_at_rs_0(self):
        g = [calc("gratuity_estimate", monthly_wage=52000, years=7, months=8)]
        records = [run("calc-gratuity-7y8m", "Rs 2,40,000 [1].", g, r=0), run("calc-gratuity-7y8m", "About Rs 2,40,000.", r=1),
                   run("calc-accrued", "14 days.", [calc("accrued_leave", months=8, per_month=1.75)], r=0),
                   run("calc-accrued", "14 days.", [calc("accrued_leave", months=8, per_month=1.75)], r=1)]
        code, out = main_out("--replay", self.write(records), "--best-of", "2")
        self.assertEqual(code, 0)
        self.assertIn("replayed 4 saved runs", out)
        self.assertIn("rescored at Rs 0, no model call (they cost Rs 2.0000 when they ran; offline, the script)", out)
        self.assertIn("== loop, thinking default (low), desk astar: 2 rows x 2 runs", out)
        self.assertIn("calc-gratuity-7y8m           calc        2/2        1/2", out)
        self.assertIn("verified   2/2 = 100.0%", out)
        self.assertIn("verified pass@2 1.000, pass^2 0.500", out)
        self.assertIn("best-of-2, chosen by the figure check alone: correct 2/2", out)

    def test_compare_pairs_two_arms_on_their_first_runs(self):
        g = [calc("gratuity_estimate", monthly_wage=52000, years=7, months=8)]
        high = dict(ARM, thinking="high")
        low_runs = [run("calc-gratuity-7y8m", "About Rs 2,40,000.", r=0), run("calc-accrued", "21 days.", r=0)]
        high_runs = [run("calc-gratuity-7y8m", "Rs 2,40,000 [1].", g, arm=high),
                     run("calc-accrued", "14 days.", [calc("accrued_leave", months=8, per_month=1.75)], arm=high)]
        code, out = main_out("--compare", self.write(low_runs), self.write(high_runs))
        self.assertEqual(code, 0)
        self.assertIn("paired (correct), 2 rows: both 1, default only 0, high only 1, neither 0", out)
        self.assertIn("paired (verified), 2 rows: both 0, default only 0, high only 2, neither 0", out)
        self.assertIn("exact McNemar p = 0.500", out)
        with self.assertRaises(SystemExit):
            main_out("--compare", self.write(low_runs + high_runs), self.write(high_runs))

    def test_a_slice(self):
        self.assertEqual([r["id"] for r in ae.select(ROWS, "trap,refuse")], ["trap-encash-cap", "refuse-gratuity-years"])
        self.assertEqual(len(ae.select(ROWS, "calc-gratuity")), 3)
        self.assertEqual(len(ae.select(ROWS, "zeta")), 1)
        self.assertEqual(ae.select(ROWS, None), ROWS)


class CheckRetryChoose(unittest.TestCase):
    """Lesson 10.3: best-of by the figure check verify retries on, and the three ways side by side, on saved records
    written by hand."""
    S53 = statute("the fifteen days' wages shall be calculated by dividing the monthly rate of wages last drawn by "
                  "twenty-six and multiplying the quotient by fifteen.")

    def g(self):
        return [calc("gratuity_estimate", monthly_wage=52000, years=7, months=8)]

    def test_best_of_takes_the_figure_checks_verdict(self):
        """The check of commands/agent_patterns.py: a cited passage the run never read fails it, so does a stop and so
        does a failed run; the expected figure is never read."""
        far = run("calc-gratuity-7y8m", "Rs 2,40,000 [4].", self.g(), [self.S53], r=0)
        near = run("calc-gratuity-7y8m", "Rs 2,40,000 [1].", self.g(), [self.S53], r=1)
        self.assertEqual((ae.passes(far), ae.passes(near)), (False, True))
        self.assertIs(ae.best_of([far, near], 2), near)
        stopped = run("calc-gratuity-7y8m", "I stopped this turn at one of its limits.", r=0, stopped_by="model_calls")
        failed = run("calc-gratuity-7y8m", "", r=0, error="ReadTimeout")
        self.assertEqual((ae.passes(stopped), ae.passes(failed)), (False, False))
        self.assertIs(ae.best_of([failed, dict(near, run=1)], 2)["run"], 1)
        verdict = ae._ap().figure_check("Rs 2,40,000 [4].", self.g(), ROW["calc-gratuity-7y8m"]["question"], [self.S53])
        self.assertEqual(verdict, {"passed": False, "unsupported": [], "uncited": [4], "stopped_by": None})

    def write(self, records) -> str:
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        self.addCleanup(os.remove, path)
        ae.save(records, path)
        return path

    def attempt(self, rid, n, answer, calcs=(), passages=(), note=None):
        q = ROW[rid]["question"]
        return {"n": n, "note": note, "note_figures": desk_calc.unsupported(note) if note else [], "question": q,
                "answer": answer, "calculations": list(calcs), "passages": list(passages), "stopped_by": None,
                "check": ae._ap().figure_check(answer, list(calcs), q, list(passages)), "model_calls": 2, "inr": 0.4}

    def verified_run(self, rid, attempts, calls):
        shipped = attempts[-1]
        return run(rid, shipped["answer"], shipped["calculations"], shipped["passages"],
                   arm={"pattern": "verify", "thinking": None, "desk": "astar"}, attempts=attempts,
                   shipped=len(attempts), check=shipped["check"], notes=[a["note"] for a in attempts if a["note"]],
                   calls=[{"role": role} for role in calls], model_calls=len(calls), inr=0.25 * len(calls))

    def records(self):
        g, acc = self.g(), [calc("accrued_leave", months=8, per_month=1.75)]
        plain = [run("calc-gratuity-7y8m", "About Rs 2,40,000.", r=0),
                 run("calc-gratuity-7y8m", "Rs 2,40,000 [1].", g, [self.S53], r=1),
                 run("calc-gratuity-7y8m", "Rs 2,40,000 [1].", g, [self.S53], r=2)]
        plain += [run("calc-accrued", "14 days.", acc, r=n) for n in range(3)]
        note = "My answer stated a figure no calculator returned. Next time call gratuity_estimate."
        checked = [self.verified_run("calc-gratuity-7y8m", [
            self.attempt("calc-gratuity-7y8m", 1, "About Rs 2,40,000."),
            self.attempt("calc-gratuity-7y8m", 2, "Rs 2,40,000 [1].", g, [self.S53], note=note)],
            ["answer", "answer", "reflect", "answer", "answer", "answer"]),
            self.verified_run("calc-accrued", [self.attempt("calc-accrued", 1, "14 days.", acc)], ["answer"] * 3)]
        return plain, checked

    def test_the_three_ways_side_by_side(self):
        plain, checked = self.records()
        code, out = main_out("--replay", self.write(plain), self.write(checked), "--best-of", "3")
        self.assertEqual(code, 0)
        self.assertIn("replayed 8 saved runs of ", out)
        self.assertIn("== verify, thinking default (low), desk astar: 2 rows x 1 run", out)
        self.assertIn("  best-of-3: not for this arm, which has 1 run a row", out)
        self.assertIn("  with notes: the figure check passed on attempt 1 in 1, on attempt 2 in 1, on attempt 3 in 0 "
                      "and on none in 0 of 2 runs (at most 3 attempts a run); 1.5 attempts, 0.5 reflect calls and 0.5 "
                      "notes a run; 0 of 1 notes write a figure, which no check takes from a note", out)
        self.assertIn("  any attempt (the ceiling, each row's first run): correct 2/2 = 100.0%", out)
        block = out[out.index("== check, retry or choose"):].splitlines()
        self.assertEqual(block[0], "== check, retry or choose (lesson 10.3): loop against verify, on the 2 rows both "
                                   "ran")
        self.assertTrue(block[1].startswith("  pass@1, loop's first run: correct 2/2 = 100.0% [34.2%, 100.0%], "
                                            "verified 1/2 = 50.0% "), block[1])
        self.assertTrue(block[1].endswith("; 3.0 calls and Rs 0.5000 a row"), block[1])
        self.assertTrue(block[2].startswith("  pass@3 re-rolls, any of its first 3 runs (the ceiling a perfect "
                                            "chooser reaches): correct 2/2"), block[2])
        self.assertIn("verified 2/2 = 100.0%", block[2])
        self.assertTrue(block[2].endswith("; 9.0 calls and Rs 1.5000 a row"), block[2])
        self.assertTrue(block[3].startswith("  best-of-3, the run the figure check chooses (code, no model): correct "
                                            "2/2"), block[3])
        self.assertIn("verified 2/2 = 100.0%", block[3])
        self.assertTrue(block[4].startswith("  pass@3 with notes, verify's answer that ships (up to 3 attempts, a note "
                                            "before each retry): correct 2/2"), block[4])
        self.assertTrue(block[4].endswith("; 4.5 calls and Rs 1.1250 a row"), block[4])
        self.assertEqual(block[5], "  the figure check's precision: of the 5 of loop's 6 runs it passes, 5 correct "
                                   "(100%) and 5 verified; of the 2 of verify's 3 attempts it passes, 2 correct (100%) "
                                   "and 2 verified")
        _, alone = main_out("--replay", self.write(plain), "--best-of", "3")
        self.assertNotIn("check, retry or choose", alone)                       # nothing without verify beside it
        self.assertNotIn("with notes", alone)

    def test_a_verify_run_that_failed(self):
        """A verify run that raised is saved with no attempts (_failed_run()): it is scored, and counted, as failed."""
        plain, checked = self.records()
        broken = run("calc-accrued", "", arm=checked[1]["arm"], error="ReadTimeout", model_calls=0, inr=0.0)
        _, out = main_out("--replay", self.write(plain), self.write([checked[0], broken]), "--best-of", "3")
        self.assertIn("on none in 0 of 1 run (at most 3 attempts a run)", out)  # the attempts of the run that has them
        self.assertIn("pass@3 with notes, verify's answer that ships (up to 3 attempts, a note before each retry): "
                      "correct 1/2", out)
        self.assertIn("of the 1 of verify's 2 attempts it passes", out)

    def test_best_of_needs_its_runs(self):
        g = [calc("gratuity_estimate", monthly_wage=52000, years=7, months=8)]
        _, out = main_out("--replay", self.write([run("calc-gratuity-7y8m", "Rs 2,40,000.", g)]), "--best-of", "2")
        self.assertIn("  best-of-2: not for this arm, which has 1 run a row", out)
        self.assertNotIn("chosen by the figure check alone", out)


if __name__ == "__main__":
    unittest.main()
