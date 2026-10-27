"""Offline tests for evals/paired.py: the paired difference of two arms, its interval, the exact test and the margin
(workshop lessons 10.1-10.3 and 10.5).

Run with ``python -m unittest discover -s evals/tests -p test_paired.py`` from deploy/ (``make agent-tests`` runs it).
Standard library only.
"""
import importlib.util
import io
import math
import unittest
from contextlib import redirect_stdout
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_under_test", EVALS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


paired = load("paired")
route_eval = load("route_eval")


class Wilson(unittest.TestCase):
    def test_it_is_route_evals(self):
        for k, n in ((0, 1), (3, 7), (18, 18), (9, 12), (56, 70), (0, 0)):
            self.assertEqual(paired.wilson(k, n), route_eval.wilson(k, n), (k, n))


class SquareAndAdd(unittest.TestCase):
    def test_newcombes_published_example(self):
        """Method 10 of Newcombe (Stat Med 1998;17:873-90): 56/70 - 48/80 = 0.2000, 95% 0.0524 to 0.3339."""
        lo, hi = paired.square_and_add(56 / 70, paired.wilson(56, 70), 48 / 80, paired.wilson(48, 80))
        self.assertEqual((round(lo, 4), round(hi, 4)), (0.0524, 0.3339))

    def test_a_positive_phi_narrows_the_interval(self):
        args = (12 / 18, paired.wilson(12, 18), 10 / 18, paired.wilson(10, 18))
        lo0, hi0 = paired.square_and_add(*args, phi=0.0)
        lo1, hi1 = paired.square_and_add(*args, phi=0.6)
        self.assertLess(hi1 - lo1, hi0 - lo0)
        self.assertTrue(lo0 < lo1 < 12 / 18 - 10 / 18 < hi1 < hi0)


class Newcombe(unittest.TestCase):
    def test_the_difference_is_b_minus_a_from_the_discordant_rows(self):
        d, lo, hi = paired.newcombe(10, 1, 4, 3)                 # 18 rows: B wins 4, A wins 1
        self.assertAlmostEqual(d, (4 - 1) / 18)
        self.assertTrue(-1 <= lo < d < hi <= 1)

    def test_swapping_the_arms_negates_the_interval(self):
        d, lo, hi = paired.newcombe(10, 1, 4, 3)
        d2, lo2, hi2 = paired.newcombe(10, 4, 1, 3)
        self.assertAlmostEqual(d, -d2)
        self.assertAlmostEqual(lo, -hi2)
        self.assertAlmostEqual(hi, -lo2)

    def test_concordant_rows_give_zero_inside_an_interval(self):
        d, lo, hi = paired.newcombe(8, 1, 1, 8)
        self.assertEqual(d, 0)
        self.assertEqual((round(100 * lo), round(100 * hi)), (-14, 14))      # the docstring's 18-row width
        d, lo, hi = paired.newcombe(10, 0, 0, 8)
        self.assertTrue(lo < 0 < hi and hi - lo < 0.05)

    def test_with_an_empty_margin_phi_is_zero(self):
        self.assertEqual(paired.phi(18, 0, 0, 0), 0.0)
        self.assertEqual(paired.phi(0, 0, 0, 18), 0.0)
        self.assertAlmostEqual(paired.phi(9, 0, 0, 9), 1.0)
        lo, hi = paired.square_and_add(1.0, paired.wilson(18, 18), 1.0, paired.wilson(18, 18))
        self.assertEqual(paired.newcombe(18, 0, 0, 0)[1:], (lo, hi))

    def test_b_winning_every_discordant_row_of_enough_rows_is_better(self):
        d, lo, hi = paired.newcombe(5, 0, 8, 5)
        self.assertGreater(lo, 0)
        self.assertTrue(paired.verdict(lo, hi).startswith("B better than A"))

    def test_no_rows_is_no_evidence(self):
        self.assertIsNone(paired.newcombe(0, 0, 0, 0))
        self.assertIsNone(paired.wilson(0, 0))


class McNemar(unittest.TestCase):
    def test_the_exact_two_sided_p(self):
        self.assertEqual(paired.mcnemar(0, 6), 2 / 64)
        self.assertEqual(paired.mcnemar(1, 9), 2 * (1 + 10) / 1024)
        self.assertEqual(paired.mcnemar(3, 3), 1.0)                      # capped at 1
        self.assertEqual(paired.mcnemar(0, 0), 1.0)                      # no discordant row: no evidence
        self.assertEqual(paired.mcnemar(2, 7), paired.mcnemar(7, 2))
        self.assertAlmostEqual(paired.mcnemar(2, 7), 2 * sum(math.comb(9, i) for i in range(3)) / 2 ** 9)


class Margin(unittest.TestCase):
    def test_pre_registered(self):
        self.assertEqual((paired.MARGIN, paired.MARGIN_REGISTERED), (0.03, "2026-10-08"))
        src = (EVALS / "paired.py").read_text(encoding="utf-8")
        self.assertIn("MARGIN = 0.03 ", src)
        self.assertIn("before any arm of\nthe agent bench had run on a lane", src)

    def test_the_verdicts(self):
        self.assertTrue(paired.verdict(0.01, 0.2).startswith("B better than A"))
        self.assertTrue(paired.verdict(-0.02, 0.2).startswith("B non-inferior to A"))
        self.assertTrue(paired.verdict(-0.3, -0.05).startswith("B worse than A"))
        self.assertTrue(paired.verdict(-0.1, 0.1).startswith("no conclusion"))
        self.assertTrue(paired.verdict(-0.1, 0.1, "low", "high").startswith("no conclusion"))
        self.assertTrue(paired.verdict(0.01, 0.2, "low", "high").startswith("high better than low"))


class Report(unittest.TestCase):
    def test_it_pairs_the_shared_rows(self):
        a = {"r1": True, "r2": True, "r3": False, "r4": False, "only-a": True}
        b = {"r1": True, "r2": False, "r3": True, "r4": True, "only-b": False}
        self.assertEqual(paired.pairs(a, b), (1, 1, 2, 0))
        text = paired.report(a, b, "low", "high")
        self.assertIn("paired (correct), 4 rows: both 1, low only 1, high only 2, neither 0", text)
        self.assertIn("high - low = +25.0 points", text)
        self.assertIn("registered 2026-10-08", text)
        self.assertIn("indicative", text)
        self.assertEqual(paired.report({}, {"x": True}), "  paired (correct): no row in common")

    def test_the_selftest(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(paired.selftest(), 0)
        self.assertTrue(out.getvalue().rstrip().endswith("the interval, the test and the margin hold"))


if __name__ == "__main__":
    unittest.main()
