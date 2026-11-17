"""Offline tests for evals/agreement.py (workshop lesson 4.5): Cohen's kappa, raw agreement, the 2x2, and the
true-pass and false-pass rates with route_eval's Wilson interval; then judge_agree.py's arithmetic on hand-made labels.

Run with ``python -m unittest discover -s evals/tests -p test_agreement.py`` from deploy/. Standard library only.
"""
import contextlib
import io
import math
from pathlib import Path
import sys
import unittest

EVALS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EVALS))
import agreement as ag  # noqa: E402
import judge_agree  # noqa: E402
import route_eval  # noqa: E402


def wilson_by_hand(k, n, z=1.96):
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - margin, centre + margin


class KappaTest(unittest.TestCase):
    def test_the_worked_table_of_fifty_rows_gives_0_40(self):
        # 20 both yes, 5 A yes and B no, 10 A no and B yes, 15 both no. p_o = 35/50 = 0.70. A says yes to 25 of 50
        # and B to 30 of 50, so p_e = 0.5 x 0.6 + 0.5 x 0.4 = 0.50, and kappa = (0.70 - 0.50) / (1 - 0.50) = 0.40.
        a, b = ag.expand(true_pass=20, false_fail=5, false_pass=10, true_fail=15)
        self.assertEqual((sum(a), sum(b), len(a)), (25, 30, 50))
        self.assertEqual(ag.agreement(a, b), (35, 50))
        self.assertAlmostEqual(ag.chance(a, b), 0.50, places=12)
        self.assertAlmostEqual(ag.cohen_kappa(a, b), 0.40, places=12)
        self.assertEqual(ag.fmt_kappa(ag.cohen_kappa(a, b)), "0.40")
        self.assertEqual(ag.table(a, b), ag.WORKED)
        self.assertEqual(ag.cohen_kappa(b, a), ag.cohen_kappa(a, b))        # symmetric: neither reader is the truth

    def test_a_second_table_worked_by_hand(self):
        # 20 rows: 10 both yes, 2 and 3 split, 5 both no. p_o = 15/20; A yes 12, B yes 13: p_e = (12 x 13 + 8 x 7) / 400
        # = 212/400; kappa = (15 x 20 - 212) / (400 - 212) = 88/188.
        a, b = ag.expand(10, 2, 3, 5)
        self.assertAlmostEqual(ag.chance(a, b), 212 / 400, places=12)
        self.assertAlmostEqual(ag.cohen_kappa(a, b), 88 / 188, places=12)
        self.assertEqual(ag.fmt_kappa(ag.cohen_kappa(a, b)), "0.47")

    def test_all_agree_is_1_when_both_labels_are_used(self):
        a, _ = ag.expand(7, 0, 0, 3)
        self.assertEqual(ag.cohen_kappa(a, a), 1.0)
        self.assertEqual(ag.agreement(a, a), (10, 10))

    def test_no_variance_is_undefined_not_perfect(self):
        # Both readers say yes to every row: they agree on all of them, and chance alone would too (p_e = 1).
        self.assertIsNone(ag.cohen_kappa([True] * 8, [True] * 8))
        self.assertIsNone(ag.cohen_kappa(["no"] * 3, ["no"] * 3))
        self.assertEqual(ag.chance([True] * 8, [True] * 8), 1.0)
        self.assertEqual(ag.agreement([True] * 8, [True] * 8), (8, 8))
        self.assertEqual(ag.fmt_kappa(None), "undefined")

    def test_one_reader_without_variance_is_0(self):
        # A passes everything; B fails two rows. Every agreement A has is what chance gives it: exactly 0.
        self.assertEqual(ag.cohen_kappa([True] * 6, [True] * 4 + [False] * 2), 0.0)

    def test_two_readers_each_with_one_label_but_different_ones(self):
        self.assertEqual(ag.cohen_kappa([True] * 4, [False] * 4), 0.0)       # p_o = 0 and p_e = 0

    def test_perfect_disagreement_is_minus_1(self):
        self.assertEqual(ag.cohen_kappa([True, False, True, False], [False, True, False, True]), -1.0)

    def test_any_label_set(self):
        # Three classes: 3 of 4 alike; A x2 y1 z1, B x3 y1: p_e = (2 x 3 + 1 x 1) / 16 = 7/16; kappa = (12 - 7) / (16 - 7).
        self.assertAlmostEqual(ag.cohen_kappa(["x", "y", "z", "x"], ["x", "y", "x", "x"]), 5 / 9, places=12)

    def test_no_rows_is_no_evidence(self):
        self.assertIsNone(ag.cohen_kappa([], []))
        self.assertIsNone(ag.chance([], []))
        self.assertEqual(ag.agreement([], []), (0, 0))

    def test_two_readers_of_the_same_rows_give_the_same_number_of_labels(self):
        with self.assertRaises(ValueError):
            ag.cohen_kappa([True], [True, False])


class RatesTest(unittest.TestCase):
    def test_the_2x2_counts_each_kind_of_row(self):
        people = [True, True, False, False, True]
        judge = [True, False, True, False, True]
        self.assertEqual(ag.table(people, judge), {"true_pass": 2, "false_fail": 1, "false_pass": 1, "true_fail": 1})
        self.assertEqual(ag.expand(**ag.table(people, judge)), ([True, True, True, False, False], [True, True, False, True, False]))

    def test_true_pass_and_false_pass_on_the_worked_table(self):
        self.assertEqual(ag.true_pass(ag.WORKED), (20, 25))       # of the 25 rows people pass, the judge passes 20
        self.assertEqual(ag.false_pass(ag.WORKED), (10, 25))      # of the 25 rows people fail, the judge passes 10

    def test_the_interval_is_route_evals_wilson(self):
        self.assertIs(ag.wilson, route_eval.wilson)
        lo, hi = ag.wilson(10, 25)
        want = wilson_by_hand(10, 25)
        self.assertAlmostEqual(lo, want[0], places=12)
        self.assertAlmostEqual(hi, want[1], places=12)
        self.assertEqual(route_eval.rate(10, 25), f"10/25 = 40.0% [{100 * want[0]:.1f}%, {100 * want[1]:.1f}%]")

    def test_no_failing_rows_is_no_false_pass_evidence(self):
        t = ag.table([True, True], [True, False])
        self.assertEqual(ag.false_pass(t), (0, 0))
        self.assertIsNone(ag.wilson(*ag.false_pass(t)))
        self.assertEqual(route_eval.rate(*ag.false_pass(t)), "0/0 (no rows)")

    def test_the_selftest_prints_the_worked_kappa(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ag.selftest(), 0)
        self.assertIn("kappa 0.40", out.getvalue())
        self.assertIn("35/50 = 70.0%", out.getvalue())


class JudgeAgreeArithmeticTest(unittest.TestCase):
    def test_groundedness_is_the_judges_0_or_1_and_the_second_metric_is_cut(self):
        self.assertEqual(judge_agree.verdicts({"a": 1.0, "b": 0.0}, "groundedness"), {"a": True, "b": False})
        scores = {"a": 5.0, "b": 4.0, "c": 3.0, "d": 1.0}
        self.assertEqual(judge_agree.verdicts(scores, "answers_the_question", 4), {"a": True, "b": True, "c": False, "d": False})
        self.assertEqual(judge_agree.verdicts(scores, "answers_the_question", 3), {"a": True, "b": True, "c": True, "d": False})
        self.assertEqual(judge_agree.CUT, 4)
        self.assertEqual(judge_agree.SECOND, ("fulfillment", "instruction_following", "question_answering_quality"))

    def test_compare_takes_the_rows_both_readers_gave(self):
        c = judge_agree.compare({"a": True, "b": False, "c": True}, {"a": True, "b": True}, ["a", "b", "c"])
        self.assertEqual(c["ids"], ["a", "b"])
        self.assertEqual(c["table"], {"true_pass": 1, "false_fail": 0, "false_pass": 1, "true_fail": 0})
        self.assertEqual(c["differ"], ["b"])
        self.assertEqual(c["agree"], (1, 2))

    def test_a_higher_cut_never_passes_more(self):
        people = {"a": True, "b": True, "c": False, "d": False, "e": True, "f": False}
        scores = {"a": 5.0, "b": 3.0, "c": 4.0, "d": 2.0, "e": 4.0, "f": 1.0}
        rows = judge_agree.sweep(scores, people, list(people))
        self.assertEqual([r["cut"] for r in rows], [1, 2, 3, 4, 5])
        passes = [r["table"]["true_pass"] + r["table"]["false_pass"] for r in rows]
        self.assertEqual(passes, [6, 5, 4, 3, 1])
        self.assertEqual([ag.false_pass(r["table"]) for r in rows], [(3, 3), (2, 3), (1, 3), (1, 3), (0, 3)])
        self.assertEqual([ag.true_pass(r["table"]) for r in rows], [(3, 3), (3, 3), (3, 3), (2, 3), (1, 3)])


if __name__ == "__main__":
    unittest.main()
