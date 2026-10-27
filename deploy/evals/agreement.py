#!/usr/bin/env python3
"""How far two readers of the same rows agree (workshop lesson 4.5): Cohen's kappa, raw agreement, the 2x2 table, and
the true-pass and false-pass rates with Wilson intervals. Standard library only, so it runs anywhere at Rs 0.

    python evals/agreement.py --selftest      # the worked 50-row table: kappa 0.40

A reader is a person or a judge, and a label is anything two readers can give a row (yes and no, pass and fail, a
class). Raw agreement is the share of rows the two label alike. It flatters: two readers who pass nine rows in ten
agree on most rows by chance alone. Cohen's kappa takes chance out:

    kappa = (p_o - p_e) / (1 - p_e)

p_o is the share of rows labelled alike. p_e is the share the two would label alike if each kept their own label
counts and gave them out at random: for each label, A's share of it times B's, summed. 1 is perfect agreement, 0 is
no better than chance, below 0 is worse. Kappa is undefined when p_e is 1, which happens only when both readers gave
every row one and the same label: there is nothing left to agree on beyond chance, so it is reported as undefined,
never as perfect.

With people as the reference and a judge under test, the 2x2 table counts four kinds of row: true pass (both pass),
false fail (people pass, the judge fails), false pass (people fail, the judge passes) and true fail (both fail). The
true-pass rate is the share of the rows people pass that the judge passes too; the false-pass rate is the share of the
rows people fail that the judge passes anyway, the error that lets a bad answer through. Each is printed as k of n
with route_eval.wilson()'s 95% interval, because at twenty rows one row moves a rate by several points.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from route_eval import rate, wilson  # noqa: E402  - one Wilson interval for every rate the kit prints

# The worked table every kappa explanation uses: 50 rows, 20 both yes, 5 A yes and B no, 10 A no and B yes, 15 both no.
# p_o = 35/50 = 0.70; A says yes to 25 of 50 and B to 30 of 50, so p_e = 0.5 x 0.6 + 0.5 x 0.4 = 0.50; kappa = 0.40.
WORKED = {"true_pass": 20, "false_fail": 5, "false_pass": 10, "true_fail": 15}


def _pair(a, b) -> tuple[list, list]:
    a, b = list(a), list(b)
    if len(a) != len(b):
        raise ValueError(f"two readers of the same rows give the same number of labels: {len(a)} against {len(b)}")
    return a, b


def agreement(a, b) -> tuple[int, int]:
    """(rows the two readers labelled alike, rows): raw agreement, before chance is taken out."""
    a, b = _pair(a, b)
    return sum(x == y for x, y in zip(a, b)), len(a)


def chance(a, b) -> float | None:
    """p_e: the share of rows the two would label alike by chance, from each reader's own label counts. None for no rows."""
    a, b = _pair(a, b)
    n = len(a)
    if not n:
        return None
    ca, cb = Counter(a), Counter(b)
    return sum(ca[k] * cb[k] for k in ca) / (n * n)


def cohen_kappa(a, b) -> float | None:
    """Cohen's kappa of two readers' labels on the same rows, over any label set. None with no rows, or when both
    readers gave every row one and the same label (p_e = 1: undefined, not perfect). Counted in whole rows, so the
    worked table gives exactly 0.4 and a reader with one label throughout, against one with two, exactly 0."""
    a, b = _pair(a, b)
    n = len(a)
    if not n:
        return None
    alike = sum(x == y for x, y in zip(a, b))
    ca, cb = Counter(a), Counter(b)
    by_chance = sum(ca[k] * cb[k] for k in ca)              # p_e, in units of 1 / n^2
    if by_chance == n * n:
        return None
    return (alike * n - by_chance) / (n * n - by_chance)


def table(reference, test) -> dict[str, int]:
    """The 2x2 of pass (True) and fail (False): the reference (people) against the reader under test (a judge, or a
    second person)."""
    reference, test = _pair(reference, test)
    t = {"true_pass": 0, "false_fail": 0, "false_pass": 0, "true_fail": 0}
    for r, j in zip(reference, test):
        t[("true_" if bool(r) == bool(j) else "false_") + ("pass" if j else "fail")] += 1
    return t


def true_pass(t: dict[str, int]) -> tuple[int, int]:
    """(k, n): of the n rows the reference passes, the k the reader under test passes too."""
    return t["true_pass"], t["true_pass"] + t["false_fail"]


def false_pass(t: dict[str, int]) -> tuple[int, int]:
    """(k, n): of the n rows the reference fails, the k the reader under test passes anyway."""
    return t["false_pass"], t["false_pass"] + t["true_fail"]


def expand(true_pass: int = 0, false_fail: int = 0, false_pass: int = 0, true_fail: int = 0) -> tuple[list[bool], list[bool]]:
    """A 2x2 back into two readers' labels, row by row (the reference first): what table() counts, undone."""
    cells = ((True, True, true_pass), (True, False, false_fail), (False, True, false_pass), (False, False, true_fail))
    reference = [r for r, _, k in cells for _ in range(k)]
    test = [j for _, j, k in cells for _ in range(k)]
    return reference, test


def fmt_kappa(k: float | None) -> str:
    return "undefined" if k is None else f"{k:.2f}"


def selftest() -> int:
    ref, test = expand(**WORKED)
    assert table(ref, test) == WORKED
    assert agreement(ref, test) == (35, 50) and abs(chance(ref, test) - 0.5) < 1e-12
    assert fmt_kappa(cohen_kappa(ref, test)) == "0.40" and abs(cohen_kappa(ref, test) - 0.4) < 1e-12
    assert true_pass(WORKED) == (20, 25) and false_pass(WORKED) == (10, 25)
    assert cohen_kappa(ref, ref) == 1.0                                   # all agree, both labels used
    assert cohen_kappa([True] * 6, [True] * 6) is None                    # no variance: one label throughout
    assert cohen_kappa([True] * 6, [True] * 4 + [False] * 2) == 0.0       # one reader without variance
    assert cohen_kappa([], []) is None and wilson(0, 0) is None
    print(f"selftest: the worked table of {len(ref)} rows ({WORKED['true_pass']} both yes, {WORKED['false_fail']} and "
          f"{WORKED['false_pass']} split, {WORKED['true_fail']} both no) agrees on {rate(*agreement(ref, test))}, "
          f"{chance(ref, test):.2f} by chance, kappa {fmt_kappa(cohen_kappa(ref, test))}; identical labels 1.00; one "
          f"label throughout undefined; a reader with one label against one with two 0.00")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true", help="the worked table and the edge cases, offline")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
