#!/usr/bin/env python3
"""The Desk's arms combined (workshop lesson 10.5): saved runs of arms B, C and A* on the same rows, read as the
members of an ensemble, at Rs 0.

    python evals/combine.py arms_B.jsonl arms_C.jsonl arms_Astar.jsonl [--routes evals/route_arms.jsonl] [--split dev]
    python evals/combine.py --selftest [--layers 2]        # scripted members, no model call      (from deploy/)

Standard library only. Each file is a run evals/route_eval.py --live --save wrote, one arm each (make route-eval
ROUTES=evals/route_arms.jsonl ARM=B|C|Astar SAVE=...), on the rows of --routes in --split; rows in the groups of the
router's prompt examples are left out, as the live run leaves them out. For every answer row it prints which members
are right - route_eval's own correct verdict: the outcome answer, every must_contain on its boundary, no
must_not_contain - and on a row where some member ran a calculator, THE VOTE: each member proposes the (calculator,
value) pairs its answer's calculations hold, which code returned and no model wrote, and the proposal more members make
than any other wins; the answer of the first member that made it ships as it stands. A member whose answer holds no
calculation proposes nothing. A tie abstains: the row goes to a person, since a regulated figure is not settled by a
coin. Then each member's rate, the rows where all, some or none were right, the vote beside the best single arm on the
rows it voted on, and THE FIGURE CHECK: every figure a member's answer writes in digits, and every whole date, that no
calculation of that answer's turn returned and that neither the question nor a passage the answer cites writes (nor
the in-force lines code adds for a cited Act or Code) - shared/desk_calc.py's unsupported(), the agent bench's
provenance rule. Such a figure was worked out by a model.

--selftest (--layers N, 1 by default) runs the combiners on scripted members of one figure row, fig-01 of
evals/route_arms.jsonl, with no model call: three members, two whose calculator returned Rs 2,40,000 and one that
writes Rs 2,10,000 itself; the vote; a three-way split, which abstains to a person; an arbiter, which picks one
member's answer from an enum of their names and ships it word for word; and N layers of a mixture-of-agents
aggregator, each reading every answer of the layer before and writing a new one - this one averages the figures it
reads, so it writes one no member computed, and unsupported() flags it at every layer. Then the model calls each
combiner adds: none for the vote, one for the arbiter, one a layer for the aggregator. A vote and an arbiter only
choose among the members' answers; an aggregator writes new text, so its figures need the same check as an agent's.
On a lane the arbiter and the aggregator would be model calls of their own; this file runs them scripted only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
for _p in (KIT, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import route_eval  # noqa: E402  - the rows, the runs, the verdicts and the rates, as the route eval reads them
from shared import desk_calc, desk_law  # noqa: E402

ARMS_FILE = os.path.join(HERE, "route_arms.jsonl")
LAYERS_MAX = 5


def shown_path(path: str) -> str:
    """A path as the learner's shell, run from deploy/, would write it."""
    full = os.path.abspath(path)
    return os.path.relpath(full, KIT).replace(os.sep, "/") if full.startswith(KIT + os.sep) else path


# --------------------------------------------------------------------- the members
def load_runs(paths: list[str], known: set[str]) -> list[tuple[str, dict]]:
    """[(arm, {row id: prediction})] in the order given: one arm a file, no arm twice, each with its answer text."""
    runs = []
    for path in paths:
        preds = route_eval.load_predictions(path, known)
        arm = route_eval.run_arm(preds, None)
        if arm is None:
            raise SystemExit(f"{path}: its rows name no arm (route_eval.py --live --save writes each row's arm)")
        if arm in [a for a, _ in runs]:
            raise SystemExit(f"{path}: a second run of arm {arm}: one run an arm")
        if not any("answer" in p for p in preds.values()):
            raise SystemExit(f"{path}: no answer text (a /v1/route run): combine reads route_eval.py --live --save runs")
        runs.append((arm, preds))
    return runs


def calculations(pred: dict) -> list[dict]:
    """What code returned in this answer's turn: every section's calculations."""
    return [c for s in pred.get("sections") or () if isinstance(s, dict)
            for c in s.get("calculations") or () if isinstance(c, dict)]


def proposal(pred: dict) -> tuple | None:
    """A member's proposal: the (calculator, value) pairs its calculations hold, each value as JSON, sorted; None when
    its answer holds no calculation."""
    return tuple(sorted({(str(c.get("calculator")), json.dumps(c.get("value"))) for c in calculations(pred)})) or None


def said(prop: tuple) -> str:
    """A proposal as the report prints it: gratuity_estimate = 240000."""
    def value(raw: str):
        v = json.loads(raw)
        if v is None:
            return "no figure"
        if isinstance(v, bool):
            return "yes" if v else "no"
        return int(v) if isinstance(v, float) and v.is_integer() else v
    return ", ".join(f"{name} = {value(v)}" for name, v in prop)


def vote(proposals: dict[str, tuple | None]) -> tuple[tuple | None, int, str]:
    """(the winning proposal, how many members made it, "") - or (None, 0, why) when no member proposed anything or
    the most-made proposals tie: then the row goes to a person."""
    counts = Counter(p for p in proposals.values() if p)
    if not counts:
        return None, 0, "no member's answer holds a calculation"
    ranked = counts.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        tied = sum(1 for _, n in ranked if n == ranked[0][1])
        return None, 0, f"a tie, {tied} proposals made by {ranked[0][1]} member{'s' if ranked[0][1] > 1 else ''} each"
    return ranked[0][0], ranked[0][1], ""


def sources(row: dict, pred: dict) -> list[str]:
    """The texts a figure in this answer may be read from as they stand: the question (and a follow-up's first turn),
    each passage the answer cites, and the in-force lines code adds for a cited Act or Code."""
    cites = [c for c in pred.get("citations") or () if isinstance(c, dict)]
    names = [str(c.get("source_uri") or c.get("source") or "") for c in cites]
    return ([row["question"], row.get("prev_question") or ""] + [str(c.get("quote") or "") for c in cites]
            + desk_law.in_force_lines(names))


def invented(row: dict, pred: dict, calcs=None) -> list[str]:
    """The figures this answer writes that no calculation of its turn (or calcs, when given) returned and no source
    writes."""
    return desk_calc.unsupported(str(pred.get("answer") or ""), calculations(pred) if calcs is None else calcs,
                                 *sources(row, pred))


# --------------------------------------------------------------------- the saved runs, combined
def combine(runs: list[tuple[str, dict]], rows: list[dict], routes: str, split: str, out=None) -> dict:
    """Each answer row's members and, where a member ran a calculator, the vote; then the members' rates, their
    agreement, the vote beside the best single arm, and the figures no calculation returned. Returns the counts."""
    out = out or sys.stdout
    arms = [a for a, _ in runs]
    classes = route_eval.classes_from_manifest()
    right = {arm: {v["id"]: bool(v.get("correct")) for v in route_eval.score(rows, preds, classes)["verdicts"]}
             for arm, preds in runs}
    preds_of = dict(runs)
    width = max([len(r["id"]) for r in rows] + [6])
    print(f"combine: arms {', '.join(arms)} on {len(rows)} answer rows of {shown_path(routes)}, split {split} "
          f"(the saved runs, Rs 0)", file=out)
    agree, voted, flagged = Counter(), [], {arm: [] for arm in arms}
    for r in rows:
        oks = [right[arm][r["id"]] for arm in arms]
        agree["all" if all(oks) else "none" if not any(oks) else "some"] += 1
        line = f"  {r['id']:<{width}} " + ", ".join(f"{arm} {'right' if ok else 'wrong'}" for arm, ok in zip(arms, oks))
        props = {arm: proposal(preds_of[arm].get(r["id"]) or {}) for arm in arms}
        if any(props.values()):
            win, n, why = vote(props)
            if win is None:
                voted.append((r["id"], None))
                line += f"; vote: {why}, to a person"
            else:
                first = next(arm for arm in arms if props[arm] == win)
                voted.append((r["id"], right[first][r["id"]]))
                line += (f"; vote: {said(win)} from {n} of {len(arms)} members, {first}'s answer: "
                         f"{'right' if right[first][r['id']] else 'wrong'}")
        print(line, file=out)
        for arm in arms:
            p = preds_of[arm].get(r["id"])
            got = invented(r, p) if p else []
            if got:
                flagged[arm].append(f"{r['id']}: {', '.join(got)}")
    print("members, right on these rows (route_eval's correct verdict)", file=out)
    for arm in arms:
        print(f"  {arm:<30}{route_eval.rate(sum(right[arm][r['id']] for r in rows), len(rows))}", file=out)
    print(f"  all right on {agree['all']} rows, some on {agree['some']}, none on {agree['none']}", file=out)
    ids = [i for i, _ in voted]
    won = sum(1 for _, ok in voted if ok)
    lost = sum(1 for _, ok in voted if ok is False)
    tied = sum(1 for _, ok in voted if ok is None)
    if voted:
        best = max(arms, key=lambda arm: sum(right[arm][i] for i in ids))
        print(f"the vote, on the {len(voted)} rows where a member ran a calculator", file=out)
        print(f"  right {won}, wrong {lost}, abstained {tied} (a tie: to a person); right "
              f"{route_eval.rate(won, len(voted))}", file=out)
        print(f"  the best single arm there: {best} {route_eval.rate(sum(right[best][i] for i in ids), len(ids))}",
              file=out)
    else:
        print("the vote: no member ran a calculator on any row, so there is nothing to vote on", file=out)
    print("figures no calculation returned and no source writes (shared/desk_calc.py's unsupported())", file=out)
    for arm in arms:
        print(f"  {arm:<6} {'; '.join(flagged[arm]) or 'none'}", file=out)
    return {"agree": dict(agree), "voted": len(voted), "right": won, "wrong": lost, "abstained": tied,
            "flagged": {arm: len(v) for arm, v in flagged.items()}}


# --------------------------------------------------------------------- the selftest: scripted members
SELF_ROW = "fig-01"
CODE_URI = "gs://documind-ai-YOUR-ID-uploads/acme/code_on_social_security_2020.pdf"     # the Code, as the desk cites it
PASSAGE = " ".join(desk_calc.RULES[k]["quote"] for k in ("gratuity_service", "gratuity_rate", "gratuity_monthly"))
_RUPEES = re.compile(r"Rs ([\d,]+)")


def member(args: dict | None, said_text: str) -> dict:
    """A scripted member's prediction on the selftest's row: with args, the gratuity calculator run on them (desk_calc
    computes the figure) and its line written by code after the member's sentence, as the desk composes an answer in
    agent mode; without, the sentence alone and no calculation."""
    calcs, answer = [], said_text
    if args is not None:
        calc = {**desk_calc.calculate("gratuity_estimate", **args), "args": args}
        calcs = [calc]
        answer += f"\n\nWorked out in code:\n- Gratuity, an estimate ({calc['cites']}): {calc['formula']}."
    return {"id": SELF_ROW, "outcome": "answer", "answer": answer, "citations": [{"source_uri": CODE_URI,
            "quote": PASSAGE}], "sections": [{"desk": "statute", "mode": "agent" if calcs else "direct",
                                              "refusals": [], "calculations": calcs}]}


def aggregate(answers: list[str]) -> str:
    """The scripted aggregator of one layer: it reads every answer of the layer before and averages the rupee figures
    their first lines state - a mixture-of-agents step that writes new text, here a figure no member computed."""
    figures = sorted({int(m.group(1).replace(",", "")) for a in answers
                      for m in [_RUPEES.search(a.split("\n", 1)[0])] if m})
    return f"About {desk_calc.inr(round(sum(figures) / len(figures)))} [1], between the figures the answers give."


def selftest(layers: int = 1, out=None) -> int:
    out = out or sys.stdout
    failures = []

    def check(ok: bool, what: str) -> None:
        print(("ok    " if ok else "FAIL  ") + what, file=out)
        if not ok:
            failures.append(what)

    row = next(r for r in route_eval.load_rows(ARMS_FILE) if r["id"] == SELF_ROW)
    asked = {"monthly_wage": 52000, "years": 7, "months": 8}
    members = {"P1": member(asked, "About Rs 2,40,000 [1], an estimate under s.53(2) of the Code."),
               "P2": member(asked, "Rs 2,40,000 [1]: fifteen days' wages for every year counted, an estimate."),
               "P3": member(None, "About Rs 2,10,000 [1]: fifteen days' wages for each of the 7 completed years.")}
    verdict = {name: route_eval.score([row], {SELF_ROW: p}, {})["verdicts"][0].get("correct")
               for name, p in members.items()}
    flags = {name: invented(row, p) for name, p in members.items()}
    print(f"combine.py --selftest: the combiners on scripted members of {SELF_ROW}, no model call (Rs 0)", file=out)
    print(f"  {'question':<10} {row['question']}", file=out)
    print(f"  {'right':<10} must_contain {', '.join(row['must_contain'])}", file=out)
    for name, p in members.items():
        prop = proposal(p)
        how = f"{said(prop)} by code" if prop else f"no calculation, it writes \"{p['answer']}\""
        print(f"  {name:<10} {how}; {'right' if verdict[name] else 'wrong'}; unsupported: "
              f"{', '.join(flags[name]) or 'none'}", file=out)
    props = {name: proposal(p) for name, p in members.items()}
    win, n, _ = vote(props)
    shipped = next(name for name in members if props[name] == win) if win else None
    print(f"  {'vote':<10} {said(win)} from {n} of {len(members)} members: {shipped}'s answer ships as it stands; "
          f"{'right' if verdict[shipped] else 'wrong'}; 0 model calls", file=out)
    split = {"S1": member(asked, "About Rs 2,40,000 [1]."),
             "S2": member({**asked, "months": 6}, "About Rs 2,10,000 [1]."),
             "S3": member({**asked, "monthly_wage": 50000}, "About Rs 2,30,769 [1].")}
    split_props = {name: proposal(p) for name, p in split.items()}
    split_win, _, split_why = vote(split_props)
    print(f"  {'split':<10} three other members, a different figure by code each:", file=out)
    for name, p in split.items():
        args = ", ".join(f"{k}={v}" for k, v in calculations(p)[0]["args"].items())
        print(f"  {'':<10} {name} {said(split_props[name])} ({args})", file=out)
    print(f"  {'':<10} {split_why}: the row goes to a person; 0 model calls", file=out)
    pick = "P2"                                         # the scripted arbiter's choice from the enum of names
    arbiter = members[pick]["answer"]
    arbiter_flags = desk_calc.unsupported(arbiter, calculations(members[pick]), *sources(row, members[pick]))
    print(f"  {'arbiter':<10} an enum of {', '.join(members)}; its scripted pick, {pick}: that answer ships word for "
          f"word; {'right' if verdict[pick] else 'wrong'}; no figure of its own; 1 model call", file=out)
    every_calc = [c for p in members.values() for c in calculations(p)]
    read, layer_flags = [p["answer"] for p in members.values()], []
    for layer in range(1, layers + 1):
        text = aggregate(read)
        got = invented(row, {"answer": text, "citations": members["P1"]["citations"]}, every_calc)
        layer_flags.append(got)
        print(f"  {f'layer {layer}':<10} the aggregator reads {len(read)} answer{'s' if len(read) > 1 else ''} and "
              f"writes \"{text}\"; unsupported: {', '.join(got) or 'none'}; 1 model call", file=out)
        read = [text]
    print(f"  {'calls':<10} the vote 0, the arbiter 1, the aggregator {layers} (one a layer)", file=out)
    check(win == (("gratuity_estimate", "240000"),) and n == 2 and shipped == "P1" and verdict["P1"],
          "the vote ships a member's figure, from two members of three, and adds no model call")
    check(split_win is None and split_why.startswith("a tie"), "a three-way split abstains to a person")
    check(arbiter == members[pick]["answer"] and not arbiter_flags and verdict[pick],
          "the arbiter ships one member's answer word for word")
    check(len(layer_flags) == layers and all(f == ["2,25,000"] for f in layer_flags),
          f"the aggregator writes Rs 2,25,000 at each of its {layers} layer{'s' if layers > 1 else ''}, which no "
          f"member computed, and unsupported() flags it")
    check(flags == {"P1": [], "P2": [], "P3": ["2,10,000"]} and not verdict["P3"],
          "P3's figure, which no calculation returned, is flagged; P1's and P2's are not")
    print(f"{len(failures)} failed" if failures else "the vote and the arbiter wrote no figure of their own; the "
          "aggregator wrote one no member computed, flagged at every layer", file=out)
    return 1 if failures else 0


# --------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="*", metavar="SAVE", help="two or three saved runs (route_eval.py --live --save), "
                                                            "one arm each")
    ap.add_argument("--routes", default=ARMS_FILE, help="the rows the runs answered (default evals/route_arms.jsonl)")
    ap.add_argument("--split", choices=route_eval.SPLITS + ("all",), default="dev")
    ap.add_argument("--selftest", action="store_true", help="the combiners on scripted members (no model, Rs 0)")
    ap.add_argument("--layers", type=int, help=f"--selftest: the aggregator's layers, 1 to {LAYERS_MAX} (default 1)")
    a = ap.parse_args(argv)
    if a.selftest:
        if a.runs:
            ap.error("--selftest runs on scripted members: it takes no saved run")
        layers = 1 if a.layers is None else a.layers
        if not 1 <= layers <= LAYERS_MAX:
            ap.error(f"--layers is 1 to {LAYERS_MAX}")
        return selftest(layers)
    if a.layers is not None:
        ap.error("--layers is the selftest's aggregator: python evals/combine.py --selftest --layers N")
    if not 2 <= len(a.runs) <= len(route_eval.ARMS):
        ap.error('two or three saved runs, one arm each: make arms-combine SAVES="b.jsonl c.jsonl astar.jsonl"')
    every = route_eval.load_rows(a.routes)
    why = route_eval.check_rows(every)
    if why:
        print("\n".join(f"FAIL  {w}" for w in why))
        return 1
    held = route_eval.prompt_groups(every)
    rows = [r for r in every if (a.split == "all" or r["split"] == a.split) and r["group"] not in held
            and r["expected_outcome"] == "answer"]
    combine(load_runs(a.runs, {r["id"] for r in every}), rows, a.routes, a.split)
    return 0


if __name__ == "__main__":
    sys.exit(main())
