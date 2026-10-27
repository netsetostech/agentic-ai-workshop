#!/usr/bin/env python3
"""The LLM judge checked against people (workshop lesson 4.5): agreement on the frozen judge set. Standard library
only, Rs 0.

    python evals/judge_agree.py people evals/reports/judge_labels.csv evals/judge_labels.L1.csv  # make judge-agree PEOPLE=1
    python evals/judge_agree.py judge evals/judge_set.ratings.jsonl evals/reports/judge_labels.csv [--cut 4] [--sweep]
                                                                                                # make judge-agree
people A B: two people's label sheets on the same frozen rows (build_judge_set.py --emit, filled, then --check),
rubric by rubric - groundedness and answers_the_question: the 2x2, raw agreement with its Wilson interval, the
agreement chance alone would give, Cohen's kappa (evals/agreement.py), and the rows they differ on, with their notes.

judge RATINGS SHEET: the judge's per-row ratings of the same rows (judge.py --save-rows; make judge-frozen) against
one person's labels, which are the reference. Groundedness is the judge's 0 or 1. The second metric - the one the
SDK names, FULFILLMENT, INSTRUCTION_FOLLOWING or QUESTION_ANSWERING_QUALITY, scored 1 to 5 - is cut: CUT or more is a
pass (default 4, a starting value: the cut is the lesson's slider). Per rubric: the 2x2; the true-pass rate (of the rows people pass, the share the judge passes) and
the false-pass rate (of the rows people fail, the share the judge passes: the bad answers it would let through), each
with a Wilson interval; raw agreement and kappa; the false-pass rate on constructed and natural rows apart; and the
rows they differ on. --sweep adds every cut from 1 to 5, so the trade a cut makes is on one screen.

A row is compared only where the judge rated the very answer the person labelled (the same row_sha): ratings of
other answers are left out, row by row, and named. Exit 2 when an input is missing or unreadable, or a sheet fails
build_judge_set.py --check; otherwise 0, whatever the agreement - this measures the judge, it gates nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agreement as ag  # noqa: E402
import build_judge_set as bjs  # noqa: E402
from judge import SECOND_METRIC  # noqa: E402  - the second metric's names, in judge.py's order of preference
from route_eval import rate  # noqa: E402

SECOND = tuple(m.lower() for m in SECOND_METRIC)        # as the metrics table names them: instruction_following, ...
CUT = 4
RUBRICS = bjs.RUBRICS                                    # groundedness, answers_the_question


# ----------------------------------------------------------------------------- inputs
def read_sheet(path: str, frozen: list[dict]) -> tuple[str, dict[str, dict[str, bool]], dict[str, str]]:
    """(reader, {id: {rubric: True for yes}}, {id: note}) of a sheet that passes build_judge_set.py --check."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{bjs.shown(path)}: not found. make label-sheet writes a blank one; fill it, then "
                                "python evals/build_judge_set.py --check on it")
    header, rows = bjs.load_sheet(path)
    why = bjs.sheet_errors(header, rows, frozen)
    if why:
        raise ValueError(f"{bjs.shown(path)} fails build_judge_set.py --check ({len(why)} problem(s)): " + "; ".join(why[:4])
                         + ("; ..." if len(why) > 4 else ""))
    notes = {r["id"].strip(): (r.get("note") or "").strip() for r in rows}
    return rows[0]["reader"].strip(), bjs.labels_of(rows), notes


def read_ratings(path: str, frozen: list[dict]) -> dict:
    """The judge's ratings of the frozen rows, from a judge.py --save-rows file: {"runs", "second" (the second metric's
    name), "scores" ({rubric: {id: score}}), "other" (ids whose rating is of another answer), "extra" (rated rows not
    in the frozen set)}. A score outside its metric's scale stops the comparison."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{bjs.shown(path)}: not found. judge.py --save-rows writes it: make judge-frozen rates "
                                "the frozen rows on your lane, then RUN=evals/reports/judge_set.ratings.jsonl (lesson 4.5, "
                                "step 6); the author's ratings ship with the kit once recorded")
    with open(path, encoding="utf-8") as f:
        lines = [json.loads(x) for x in f if x.strip()]
    if not lines or not all(isinstance(x, dict) and "id" in x and isinstance(x.get("ratings"), dict) for x in lines):
        raise ValueError(f"{bjs.shown(path)} is not a judge.py --save-rows file (one JSON line per row, with ratings)")
    sha = {r["id"]: bjs.row_sha(r) for r in frozen}
    held = sorted({m for x in lines for m in x["ratings"]})
    seconds = [m for m in SECOND if m in held]
    if "groundedness" not in held or not seconds:
        raise ValueError(f"{bjs.shown(path)} needs groundedness and one of {', '.join(SECOND)}; it rates {held}")
    second = seconds[0]
    scores: dict[str, dict[str, float]] = {k: {} for k in RUBRICS}
    other, extra = [], []
    for x in lines:
        rid = x["id"]
        if rid not in sha:
            extra.append(rid)
            continue
        if bjs.row_sha(x) != sha[rid]:
            other.append(rid)
            continue
        for rubric, metric in (("groundedness", "groundedness"), ("answers_the_question", second)):
            s = (x["ratings"].get(metric) or {}).get("score")
            if s is not None:
                scores[rubric][rid] = float(s)
    off = sorted({s for s in scores["groundedness"].values() if s not in (0.0, 1.0)})
    if off:
        raise ValueError(f"groundedness scores other than 0 and 1 in {bjs.shown(path)} ({off[:5]}): this SDK's scale is "
                         "not the one lesson 4.2 reads. Read the ratings before cutting them")
    off = sorted({s for s in scores["answers_the_question"].values() if not 1 <= s <= 5})
    if off:
        raise ValueError(f"{second} scores outside 1 to 5 in {bjs.shown(path)} ({off[:5]}). Read the ratings before cutting them")
    return {"runs": sorted({str(x.get("run") or "?") for x in lines}), "second": second, "scores": scores,
            "other": other, "extra": extra}


# ----------------------------------------------------------------------------- the comparison
def compare(ref: dict[str, bool], test: dict[str, bool], ids: list[str]) -> dict:
    """Two readers' verdicts on the rows both gave one: the 2x2 with `ref` as the reference, raw agreement, chance,
    kappa and the rows they differ on."""
    ids = [i for i in ids if i in ref and i in test]
    r, t = [ref[i] for i in ids], [test[i] for i in ids]
    return {"ids": ids, "table": ag.table(r, t), "agree": ag.agreement(r, t), "chance": ag.chance(r, t),
            "kappa": ag.cohen_kappa(r, t), "differ": [i for i in ids if ref[i] != test[i]]}


def verdicts(scores: dict[str, float], rubric: str, cut: int = CUT) -> dict[str, bool]:
    """The judge's pass or fail per row: groundedness is its 0 or 1; the second metric passes at `cut` or more."""
    return {i: (s >= 1 if rubric == "groundedness" else s >= cut) for i, s in scores.items()}


def sweep(scores: dict[str, float], ref: dict[str, bool], ids: list[str]) -> list[dict]:
    """The second metric at every cut from 1 to 5, against the reference: what the CUT slider moves."""
    return [{"cut": c, **compare(ref, verdicts(scores, "answers_the_question", c), ids)} for c in range(1, 6)]


# ----------------------------------------------------------------------------- printing
def grid(t: dict[str, int], rows: str, cols: str, yes: str, no: str) -> list[str]:
    """The 2x2 as three lines: the reference down the side, the reader under test across."""
    a, b = f"{cols} {yes}", f"{cols} {no}"
    w = max(len(rows) + len(yes) + 1, len(rows) + len(no) + 1)
    return [f"    {'':{w}}  {a:>{len(a)}}  {b:>{len(b)}}",
            f"    {rows + ' ' + yes:{w}}  {t['true_pass']:>{len(a)}}  {t['false_fail']:>{len(b)}}",
            f"    {rows + ' ' + no:{w}}  {t['false_pass']:>{len(a)}}  {t['true_fail']:>{len(b)}}"]


def agree_line(c: dict) -> str:
    chance = "-" if c["chance"] is None else f"{c['chance']:.2f}"
    kappa = ag.fmt_kappa(c["kappa"]) + (" (both gave one label throughout: nothing to agree on beyond chance)"
                                        if c["kappa"] is None and c["ids"] else "")
    return f"    agree {rate(*c['agree'])}; by chance {chance}; kappa {kappa}"


def differ_line(c: dict, show, limit: int = 12) -> str:
    if not c["differ"]:
        return "    they differ on no row"
    more = f", and {len(c['differ']) - limit} more" if len(c["differ"]) > limit else ""
    return f"    they differ on {len(c['differ'])}: " + ", ".join(show(i) for i in c["differ"][:limit]) + more


def head(frozen: list[dict], set_path: str) -> list[str]:
    built = sum(bool(r.get("constructed")) for r in frozen)
    return [f"the frozen set: {bjs.shown(set_path)}, {len(frozen)} rows ({built} constructed)"]


def people(a_path: str, b_path: str, frozen: list[dict], set_path: str) -> list[str]:
    ra, la, na = read_sheet(a_path, frozen)
    rb, lb, nb = read_sheet(b_path, frozen)
    if ra == rb:
        ra, rb = f"{ra} ({os.path.basename(a_path)})", f"{rb} ({os.path.basename(b_path)})"
    built = {r["id"] for r in frozen if r.get("constructed")}
    ids = [r["id"] for r in frozen]
    out = head(frozen, set_path) + [f"{ra} ({bjs.shown(a_path)}) against {rb} ({bjs.shown(b_path)}), {len(ids)} rows each"]
    for k in RUBRICS:
        c = compare({i: v[k] for i, v in la.items()}, {i: v[k] for i, v in lb.items()}, ids)

        def show(i, k=k):
            yn = lambda v: "yes" if v else "no"  # noqa: E731
            notes = "; ".join(f"{who}: {n[i][:60]!r}" for who, n in ((ra, na), (rb, nb)) if n.get(i))
            return (f"{i}{' (constructed)' if i in built else ''} ({ra} {yn(la[i][k])}, {rb} {yn(lb[i][k])})"
                    + (f" {notes}" if notes else ""))
        out += ["", f"  {k}"] + grid(c["table"], ra, rb, "yes", "no") + [agree_line(c), differ_line(c, show)]
    return out


def judge(ratings_path: str, sheet_path: str, frozen: list[dict], set_path: str, cut: int = CUT,
          with_sweep: bool = False) -> list[str]:
    rt = read_ratings(ratings_path, frozen)
    reader, labels, notes = read_sheet(sheet_path, frozen)
    built = {r["id"] for r in frozen if r.get("constructed")}
    ids = [r["id"] for r in frozen]
    rated = {i for s in rt["scores"].values() for i in s}
    out = head(frozen, set_path) + [
        f"the judge: {bjs.shown(ratings_path)}, run {', '.join(rt['runs'])}: {len(rated)} of the frozen rows rated",
        f"the people: {reader} ({bjs.shown(sheet_path)}), {len(labels)} rows - the reference",
        f"the second metric: {rt['second']}, 1 to 5, a pass at {cut} or more (CUT={cut})"]
    if rt["other"]:
        out.append(f"left out, rated on another answer than the frozen one: {', '.join(rt['other'])}")
    if rt["extra"]:
        out.append(f"left out, rated but not in the frozen set: {len(rt['extra'])} row(s)")
    for k in RUBRICS:
        ref = {i: v[k] for i, v in labels.items()}
        jv = verdicts(rt["scores"][k], k, cut)
        c = compare(ref, jv, ids)
        scale = "the judge's 0 or 1" if k == "groundedness" else f"{rt['second']} >= {cut}"

        def show(i, k=k):
            note = f" {notes[i][:60]!r}" if notes.get(i) else ""
            return (f"{i}{' (constructed)' if i in built else ''} (people {'pass' if ref[i] else 'fail'}, judge "
                    f"{rt['scores'][k][i]:g})" + note)
        tp, fp = ag.true_pass(c["table"]), ag.false_pass(c["table"])
        out += ["", f"  {k} ({scale})"] + grid(c["table"], "people", "judge", "pass", "fail") + [
            f"    true-pass   {rate(*tp)}   of the rows people pass, the judge passes",
            f"    false-pass  {rate(*fp)}   of the rows people fail, the judge passes",
            agree_line(c)]
        if built:
            parts = []
            for name, keep in (("constructed", built), ("natural", set(ids) - built)):
                t = compare({i: ref[i] for i in keep if i in ref}, {i: jv[i] for i in keep if i in jv}, ids)["table"]
                parts.append(f"{name} rows {rate(*ag.false_pass(t))}")
            out.append("    false-pass on " + "; on ".join(parts))
        missing = [i for i in ids if i not in jv]
        if missing:
            out.append(f"    not rated: {', '.join(missing)}")
        out.append(differ_line(c, show))
        if with_sweep and k == "answers_the_question":
            out += ["", f"  every cut ({rt['second']} at the cut or more is a pass):",
                    "    cut  judge passes  true-pass                        false-pass                       kappa"]
            for s in sweep(rt["scores"][k], ref, ids):
                t = s["table"]
                passes = f"{t['true_pass'] + t['false_pass']}/{len(s['ids'])}"
                mark = "   <- CUT" if s["cut"] == cut else ""
                out.append(f"    {s['cut']:>3}  {passes:>12}  {rate(*ag.true_pass(t)):31}  {rate(*ag.false_pass(t)):31}  "
                           f"{ag.fmt_kappa(s['kappa']):>9}{mark}")
    return out


# ----------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--set", default=bjs.JUDGE_SET, help="the frozen rows (default evals/judge_set.json)")
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("people", parents=[common], help="two people's sheets on the same rows")
    p.add_argument("a")
    p.add_argument("b")
    j = sub.add_parser("judge", parents=[common], help="the judge's ratings against one person's sheet")
    j.add_argument("ratings")
    j.add_argument("sheet")
    j.add_argument("--cut", type=int, default=CUT, choices=range(1, 6), metavar="1-5",
                   help=f"the second metric passes at this score or more (default {CUT})")
    j.add_argument("--sweep", action="store_true", help="also every cut from 1 to 5")
    a = ap.parse_args(argv)
    try:
        frozen = bjs.load_set(a.set)
        lines = (people(a.a, a.b, frozen, a.set) if a.mode == "people"
                 else judge(a.ratings, a.sheet, frozen, a.set, a.cut, a.sweep))
    except (OSError, ValueError) as e:
        print(e)
        return 2
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
