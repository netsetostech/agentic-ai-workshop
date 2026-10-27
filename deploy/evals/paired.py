#!/usr/bin/env python3
"""Two arms on the same rows (workshop lessons 10.1-10.3 and 10.5): the paired difference in their pass rates,
Newcombe's 95% interval for it, an exact McNemar test, and the margin they are read against. Standard library only.

    python evals/paired.py --selftest          (from deploy/)

Two arms answering the same rows are not two samples. A row both arms get right, or both get wrong, says nothing about
which arm is better; only the discordant rows do: a_only, the rows arm A passes and B fails, and b_only, the other way
round. The difference in pass rates is B - A = (b_only - a_only) / n.

    newcombe(both, a_only, b_only, neither)   B - A with its 95% interval: Newcombe's hybrid score interval for paired
                                              data (Stat Med 1998;17:2635-50, no continuity correction) - each arm's
                                              own Wilson interval, squared and added with the arms' correlation (phi)
                                              taken off - so it stays inside [-1, 1] and is never a point at 0 or n
    mcnemar(a_only, b_only)                   the exact two-sided p: under no difference each discordant row is a fair
                                              coin, so p is twice the binomial tail of the smaller count, capped at 1;
                                              no discordant row is p = 1, no evidence either way
    verdict(lo, hi)                           the interval read against MARGIN

MARGIN is pre-registered: 3 points of pass rate, written here on 8 October 2026 (MARGIN_REGISTERED), before any arm of
the agent bench had run on a lane. B is non-inferior to A when the interval's lower bound is above -MARGIN, better when
it is above 0, worse when its upper bound is below -MARGIN; anything else is no conclusion at this many rows. A margin
chosen after the runs, or moved to fit them, turns the test into a story: it changes only with a new date and a reason,
never to rescue a run.

At a few dozen rows every interval is wide: 18 rows with one discordant row each way span 28 points (-14 to +14). A
comparison on evals/agent_tasks.jsonl, whose rows are model-written until people write a held-out split, is indicative,
and evals/agent_eval.py prints it so. One outcome a row, from its first run: pairing several runs of one row would count
one question many times.
"""
from __future__ import annotations

import math
import sys

MARGIN = 0.03                       # the non-inferiority margin: 3 points of pass rate
MARGIN_REGISTERED = "2026-10-08"    # the day MARGIN was written down, before any lane run of the bench
Z95 = 1.96                          # two-sided 95%, as evals/route_eval.py


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float] | None:
    """The Wilson score interval for k of n, as evals/route_eval.py computes it. None for n = 0: no rows is no
    evidence."""
    if n <= 0:
        return None
    p, z2 = k / n, z * z
    centre, margin = p + z2 / (2 * n), z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return max(0.0, (centre - margin) / (1 + z2 / n)), min(1.0, (centre + margin) / (1 + z2 / n))


def square_and_add(p1: float, lim1: tuple[float, float], p2: float, lim2: tuple[float, float],
                   phi: float = 0.0) -> tuple[float, float]:
    """Newcombe's interval for p1 - p2 from each rate's own interval: the distances from each rate to its limits,
    squared and added, less 2 phi times their product. With phi = 0 it is his method 10 for two independent rates
    (Stat Med 1998;17:873-90), where 56/70 against 48/80 gives 0.0524 to 0.3339."""
    (l1, u1), (l2, u2) = lim1, lim2
    d = p1 - p2
    lo = d - math.sqrt(max(0.0, (p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2))
    hi = d + math.sqrt(max(0.0, (u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2))
    return max(-1.0, lo), min(1.0, hi)


def phi(both: int, a_only: int, b_only: int, neither: int) -> float:
    """The arms' correlation over the rows, the phi coefficient of the 2x2 table; 0 when a margin of the table is
    empty, as Newcombe sets it."""
    den = (both + a_only) * (b_only + neither) * (both + b_only) * (a_only + neither)
    return (both * neither - a_only * b_only) / math.sqrt(den) if den else 0.0


def newcombe(both: int, a_only: int, b_only: int, neither: int,
             z: float = Z95) -> tuple[float, float, float] | None:
    """(B - A, its lower limit, its upper limit) over paired rows, or None for no rows. both: the rows both arms
    pass; a_only: A passes and B fails; b_only: B passes and A fails; neither: both fail."""
    n = both + a_only + b_only + neither
    if n <= 0:
        return None
    pa, pb = (both + a_only) / n, (both + b_only) / n
    lo, hi = square_and_add(pb, wilson(both + b_only, n, z), pa, wilson(both + a_only, n, z),
                            phi(both, a_only, b_only, neither))
    return pb - pa, lo, hi


def mcnemar(a_only: int, b_only: int) -> float:
    """The exact two-sided McNemar p for the discordant rows."""
    m = a_only + b_only
    if m == 0:
        return 1.0
    tail = sum(math.comb(m, i) for i in range(min(a_only, b_only) + 1)) / 2 ** m
    return min(1.0, 2 * tail)


def verdict(lo: float, hi: float, a: str = "A", b: str = "B", margin: float = MARGIN) -> str:
    """The interval for b - a read against the pre-registered margin."""
    if lo > 0:
        return f"{b} better than {a}: the whole interval is above 0"
    if lo > -margin:
        return f"{b} non-inferior to {a}: the lower bound is above -{100 * margin:g} points"
    if hi < -margin:
        return f"{b} worse than {a}: the whole interval is below -{100 * margin:g} points"
    return "no conclusion at this many rows: the interval crosses the margin"


def pairs(a: dict, b: dict) -> tuple[int, int, int, int]:
    """(both, a_only, b_only, neither) over the rows the two {row id: passed} maps share."""
    shared = set(a) & set(b)
    both = sum(1 for r in shared if a[r] and b[r])
    a_only = sum(1 for r in shared if a[r] and not b[r])
    b_only = sum(1 for r in shared if b[r] and not a[r])
    return both, a_only, b_only, len(shared) - both - a_only - b_only


def report(a: dict, b: dict, name_a: str = "A", name_b: str = "B", what: str = "correct") -> str:
    """The paired comparison of two {row id: passed} maps, as evals/agent_eval.py prints it."""
    both, a_only, b_only, neither = pairs(a, b)
    n = both + a_only + b_only + neither
    if n == 0:
        return f"  paired ({what}): no row in common"
    diff, lo, hi = newcombe(both, a_only, b_only, neither)
    return "\n".join([
        f"  paired ({what}), {n} rows: both {both}, {name_a} only {a_only}, {name_b} only {b_only}, neither {neither}",
        f"  {name_b} - {name_a} = {100 * diff:+.1f} points, 95% [{100 * lo:+.1f}, {100 * hi:+.1f}] (Newcombe), "
        f"exact McNemar p = {mcnemar(a_only, b_only):.3f}",
        f"  {verdict(lo, hi, name_a, name_b)} (margin {100 * MARGIN:g} points, registered {MARGIN_REGISTERED}); "
        f"indicative: the task set's model-written rows, one run each"])


def selftest() -> int:
    failures = []

    def check(ok: bool, what: str) -> None:
        print(("ok    " if ok else "FAIL  ") + what)
        if not ok:
            failures.append(what)

    lo, hi = square_and_add(56 / 70, wilson(56, 70), 48 / 80, wilson(48, 80))
    check((round(lo, 4), round(hi, 4)) == (0.0524, 0.3339), "56/70 - 48/80: 0.0524 to 0.3339, Newcombe's method 10")
    d, lo, hi = newcombe(8, 1, 1, 8)
    check(d == 0 and (round(100 * lo), round(100 * hi)) == (-14, 14), "18 rows, one discordant each way: -14 to +14")
    check(mcnemar(0, 6) == 1 / 32 and mcnemar(3, 3) == 1.0 and mcnemar(0, 0) == 1.0, "exact McNemar: 0 of 6 is 1/32")
    check(MARGIN == 0.03 and MARGIN_REGISTERED == "2026-10-08", "the margin: 3 points, registered 8 October 2026")
    print(f"{len(failures)} failed" if failures else "the interval, the test and the margin hold")
    return 1 if failures else 0


if __name__ == "__main__":
    if sys.argv[1:] != ["--selftest"]:
        print("usage: python evals/paired.py --selftest", file=sys.stderr)
        sys.exit(2)
    sys.exit(selftest())
