#!/usr/bin/env python3
"""The DocuMind Desk router's thresholds, swept on the dev split (workshop lesson 10.4), the way
evals/cache_threshold.py sweeps the cache's.

    python deploy/evals/route_threshold.py --selftest                              # OFFLINE - the arithmetic
    python deploy/evals/route_threshold.py --local                                 # OFFLINE - the sweep, scripted
    python deploy/evals/route_threshold.py --project documind-ai-YOUR-ID [--write-signals sig.jsonl]   # LIVE
    python deploy/evals/route_threshold.py --signals sig.jsonl                     # a saved live run, re-swept

Two thresholds decide whether a turn is accepted without the arbiter (services/chat/desk_router.accept()): TAU_OOS,
under which L1's out_of_scope is accepted when the nearest exemplar is that far away (rule C), and ACCEPT_VOTES, the
k=7 vote L1 must agree with (rule A). For every pair of candidates the sweep replays stage 6 on each dev row's
signals - L1's answer, the leave-one-group-out vote (route_eval.knn_vote) and the anchors - and measures:

    accepted accuracy   of the turns accepted without L2, how many took an acceptable route     target 98% or more
    L1 errors to L2     of the turns where L1 was wrong, how many went to the arbiter           target 70% or more
    L2 share            of all turns, how many went to the arbiter                              cap 15% to start

It recommends the pair that meets all three with the smallest L2 share, and prints it beside the router's current
values; it writes nothing, because a threshold changes in desk_router.py, by a person, in a reviewed commit. Rows a
rule decides before stage 6 (the gate, a single-mode tenant, an anchor at Rs 0) never meet the thresholds and are
left out, as are the groups of the classifier's prompt examples (the prompt has seen them; route_eval.py leaves
them out too) and rows whose L1 call failed, which go to the fallback and are counted as l1_failed - a failed call
never stops a paid run. The router's thresholds are starting values until people write and review the dev rows:
--local's sweep runs on a scripted classifier and offline embeddings, so its numbers show that the sweep works, not
where the thresholds belong. A live run embeds the index's dev rows (about 200) and makes one flash-lite call for
each dev row that reaches stage 6 (about 130, about Rs 2 at four characters a token), and nothing else.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import route_eval  # noqa: E402  - the route set, the index and the one knn_vote

TAU_CANDIDATES = (0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85)
VOTE_CANDIDATES = (4, 5, 6, 7)
TARGETS = {"accepted_accuracy": 0.98, "l1_errors_to_l2": 0.70, "l2_share": 0.15}


def signals(rows: list[dict], indexes: dict[str, list[dict]], models, vectors: dict[str, list[float]],
            skip_groups=frozenset()) -> list[dict]:
    """Each dev row's stage-6 signals, for the rows that reach stage 6: {id, acceptable, l1, knn, anchors}. Rows in
    skip_groups (the prompt's examples) are left out. An L1 call that fails is l1 None, so a paid run keeps going."""
    desk_router, _ = route_eval.router()
    from shared import desk_rules
    out = []
    for r in rows:
        if r["group"] in skip_groups or r["tenant"] in route_eval.SINGLE or desk_rules.gate(r["question"]):
            continue
        masked, _ = desk_rules.mask(r["question"])
        hints = desk_router.anchors(masked, route_eval._clause_prefixes(r["tenant"]))
        if len(hints) == 1 and not desk_rules.near(masked):
            continue                                                     # decided at Rs 0
        if hasattr(models, "begin"):
            models.begin(r)
        try:
            raw, _ = models.l1(desk_router.prompt(masked, r["prev_question"], r["prev_route"]))
        except Exception as e:  # noqa: BLE001 - a timeout or an error is a missing answer, counted as l1_failed
            print(f"  {r['id']}: L1 failed ({type(e).__name__})", file=sys.stderr)
            raw = None
        l1 = desk_router.parse_l1(raw)
        knn = route_eval.knn_vote(r, indexes.get(r["tenant"], []), vector=vectors.get(r["id"]))
        out.append({"id": r["id"], "acceptable": r["acceptable_routes"], "l1": l1, "anchors": hints,
                    "knn": {k: knn[k] for k in ("route", "share", "sim", "votes", "case_types")}})
    return out


def measure(sigs: list[dict], tau: float, votes: int) -> dict:
    """One candidate pair's three figures, as (k, n) pairs."""
    desk_router, _ = route_eval.router()
    live = [s for s in sigs if s["l1"] is not None]
    accepted = ok = to_l2 = wrong = caught = 0
    for s in live:
        verdict = desk_router.accept(s["l1"], s["knn"], s["anchors"], tau_oos=tau, accept_votes=votes)
        l1_wrong = s["l1"]["route"] not in s["acceptable"]
        wrong += l1_wrong
        if verdict is None:
            to_l2 += 1
            caught += l1_wrong
        else:
            accepted += 1
            ok += verdict[0] in s["acceptable"]
    return {"tau_oos": tau, "accept_votes": votes, "accepted_accuracy": (ok, accepted),
            "l1_errors_to_l2": (caught, wrong), "l2_share": (to_l2, len(live)), "l1_failed": len(sigs) - len(live)}


def sweep(sigs: list[dict]) -> list[dict]:
    return [measure(sigs, t, v) for t in TAU_CANDIDATES for v in VOTE_CANDIDATES]


def _frac(pair: tuple[int, int], empty: float) -> float:
    k, n = pair
    return k / n if n else empty


def meets(row: dict) -> bool:
    return (_frac(row["accepted_accuracy"], 1.0) >= TARGETS["accepted_accuracy"]
            and _frac(row["l1_errors_to_l2"], 1.0) >= TARGETS["l1_errors_to_l2"]
            and _frac(row["l2_share"], 0.0) <= TARGETS["l2_share"])


def recommend(rows: list[dict]) -> dict | None:
    """The pair that meets every target with the smallest L2 share, then the best accepted accuracy; None when no
    pair does - then the starting values stay, and the sweep says so."""
    good = [r for r in rows if meets(r)]
    if not good:
        return None
    return min(good, key=lambda r: (_frac(r["l2_share"], 0.0), -_frac(r["accepted_accuracy"], 1.0),
                                    abs(r["tau_oos"] - 0.70), abs(r["accept_votes"] - 5)))


def show(rows: list[dict], best: dict | None) -> None:
    desk_router, _ = route_eval.router()
    print(f"  {'tau_oos':>7} {'votes':>5}   {'accepted accuracy':<34}{'L1 errors to L2':<34}{'L2 share':<34}")
    for r in rows:
        mark = " <" if best is r else ""
        print(f"  {r['tau_oos']:>7.2f} {r['accept_votes']:>5}   {route_eval.rate(*r['accepted_accuracy']):<34}"
              f"{route_eval.rate(*r['l1_errors_to_l2']):<34}{route_eval.rate(*r['l2_share']):<34}{mark}")
    print(f"targets: accepted accuracy >= {TARGETS['accepted_accuracy']:.0%}, L1 errors to L2 >= "
          f"{TARGETS['l1_errors_to_l2']:.0%}, L2 share <= {TARGETS['l2_share']:.0%}")
    print(f"the router now: TAU_OOS {desk_router.TAU_OOS}, ACCEPT_VOTES {desk_router.ACCEPT_VOTES} (starting values)")
    if best:
        print(f"recommended: TAU_OOS {best['tau_oos']}, ACCEPT_VOTES {best['accept_votes']} - change them in "
              f"services/chat/desk_router.py, in a reviewed commit")
    else:
        print("no candidate meets every target: keep the starting values and look at the rows L1 gets wrong")


def _run(models, vectors_for) -> list[dict]:
    rows = route_eval.load_rows()
    dev = [r for r in rows if r["split"] == "dev"]
    pool = route_eval.index_rows(rows)
    vectors = vectors_for(pool)
    _, desk_routes = route_eval.router()
    classes = route_eval._tenant_classes()
    base = route_eval.build_index(pool, vectors)
    indexes = {t: [e for e in base if e["route"] in desk_routes.enabled_routes(classes.get(t, ()))]
               for t in route_eval.TENANTS if t not in route_eval.SINGLE}
    return signals(dev, indexes, models, vectors, route_eval.prompt_groups(rows))


def selftest() -> int:
    """The arithmetic on hand-made signals: one accepted right, one accepted wrong, one L1 error sent to L2."""
    l1 = (lambda route: {"route": route, "second_route": "none", "case_type": "none", "needs_calculation": False,
                         "followup": False})
    knn = (lambda route, votes, sim: {"route": route, "share": votes / 7, "sim": sim, "votes": {route: votes},
                                      "case_types": {}})
    sigs = [{"id": "a", "acceptable": ["handbook"], "l1": l1("handbook"), "knn": knn("handbook", 6, 0.9), "anchors": []},
            {"id": "b", "acceptable": ["handbook"], "l1": l1("statute"), "knn": knn("statute", 5, 0.9), "anchors": []},
            {"id": "c", "acceptable": ["statute"], "l1": l1("handbook"), "knn": knn("statute", 4, 0.9), "anchors": []},
            {"id": "d", "acceptable": ["out_of_scope"], "l1": l1("out_of_scope"), "knn": knn("statute", 3, 0.6),
             "anchors": []},
            {"id": "e", "acceptable": ["handbook"], "l1": None, "knn": knn("handbook", 7, 0.9), "anchors": []}]
    at5 = measure(sigs, 0.70, 5)
    assert at5["accepted_accuracy"] == (2, 3) and at5["l1_errors_to_l2"] == (1, 2) and at5["l2_share"] == (1, 4), at5
    assert at5["l1_failed"] == 1
    at6 = measure(sigs, 0.70, 6)                       # b's 5 votes no longer accept: its error goes to L2
    assert at6["accepted_accuracy"] == (2, 2) and at6["l1_errors_to_l2"] == (2, 2) and at6["l2_share"] == (2, 4), at6
    at_low = measure(sigs, 0.55, 6)                    # d's 0.6 is no longer far enough: L2
    assert at_low["accepted_accuracy"] == (1, 1) and at_low["l2_share"] == (3, 4), at_low
    rows = sweep(sigs)
    assert len(rows) == len(TAU_CANDIDATES) * len(VOTE_CANDIDATES)
    assert recommend(rows) is None                     # every pair sends 50% or more to L2: over the cap
    TARGETS["l2_share"], saved = 0.5, TARGETS["l2_share"]
    try:
        best = recommend(rows)
        assert best and best["accept_votes"] == 6 and best["tau_oos"] >= 0.65, best
    finally:
        TARGETS["l2_share"] = saved
    print(f"route_threshold selftest: accepted accuracy, L1 errors to L2 and L2 share count right on hand-made "
          f"signals; {len(rows)} candidate pairs; no recommendation when none meets the targets")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--local", action="store_true", help="the sweep on a scripted classifier and offline embeddings")
    ap.add_argument("--signals", help="a JSON-lines file of signals a live run wrote (--write-signals)")
    ap.add_argument("--project", default=os.environ.get("PROJECT"), help="your lane: live L1 and embeddings")
    ap.add_argument("--write-signals", help="with --project: keep the signals here, to sweep again for free")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.signals:
        with open(a.signals, encoding="utf-8") as f:
            sigs = [json.loads(line) for line in f if line.strip()]
    elif a.local:
        rows = route_eval.load_rows()
        vectors = {r["id"]: route_eval.offline_embed(r["question"]) for r in route_eval.index_rows(rows)}
        sigs = _run(route_eval.ScriptedModels(rows, vectors), lambda pool: vectors)
        print("local: the classifier is scripted and the embeddings offline - this shows the sweep works, not where "
              "the thresholds belong")
    elif a.project:
        desk_router, _ = route_eval.router()
        models = desk_router.GeminiModels.for_project(a.project)
        sigs = _run(models, lambda pool: dict(zip([r["id"] for r in pool],
                                                  models.embed_many([r["question"] for r in pool]))))
        if a.write_signals:
            with open(a.write_signals, "w", encoding="utf-8") as f:
                f.writelines(json.dumps(s) + "\n" for s in sigs)
    else:
        ap.error("--selftest, --local, --signals or --project")
    rows = sweep(sigs)
    print(f"{len(sigs)} dev rows reach stage 6 ({sum(1 for s in sigs if s['l1'] is None)} with no L1 answer)")
    show(rows, recommend(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
