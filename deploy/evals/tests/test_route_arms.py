"""Lesson 10.5's arms set and the route eval's arms half (workshop lesson 10.5): every figure of evals/route_arms.jsonl
recomputed by shared/desk_calc.py from the row's own question and its tenant's clause; the rows held to the route set's
rules; what a --live run keeps of each desk turn and what --report puts beside each verdict; --compare against
evals/paired.py's own arithmetic, and what it refuses; a live run of the three arms on the arms set against a stand-in
chat service, end to end (save, report, compare, combine); and the make targets.

Run with ``python -m unittest discover -s evals/tests -p test_route_arms.py`` from deploy/. Stdlib only; CI runs it
with evals/tests. It is not part of route_eval.py --selftest, whose output lesson 10.4's desk-check cell prints, nor
of make desk-check.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]
KIT = EVALS.parent
for _p in (str(KIT), str(EVALS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import agent_eval  # noqa: E402  - the lane's chunk of a clause, as agent_eval.py --check reads it
import build_routes  # noqa: E402
import combine  # noqa: E402
import paired  # noqa: E402
import route_eval  # noqa: E402
from run_eval import contains  # noqa: E402
from shared import desk_calc, desk_rules  # noqa: E402

ARMS_FILE = str(EVALS / "route_arms.jsonl")
ARMS = route_eval.load_rows(ARMS_FILE)
BY_ID = {r["id"]: r for r in ARMS}
ROUTES = route_eval.load_rows()
ROUTES_BY_ID = {r["id"]: r for r in ROUTES}
FIG = ("fig-01", "fig-02", "fig-03", "fig-05", "fig-06")
LOOKUPS = ("lk-01", "lk-04", "lk-06", "lk-07", "lk-17", "iso-01")

# Each row's figures, recomputed. The calculator calls: the calculator, its arguments as the question states them,
# and the handbook clause its handbook figure is written in (None for a Code's calculator, whose inputs are all the
# person's). The figures a clause writes as they stand: (the figure, a handbook clause code or a desk_calc.RULES key).
FIGURES = {
    "fig-01": ([("gratuity_estimate", {"monthly_wage": 52000, "years": 7, "months": 8}, None)], []),
    "fig-02": ([("gratuity_estimate", {"monthly_wage": 52000, "years": 7, "months": 6}, None)], []),
    "fig-03": ([("notice_end", {"ack_date": "2026-10-05", "days": 60}, "NP-03")], []),
    "fig-05": ([("carry_forward", {"days": 34, "cap": 18}, "LV-01")], []),
    "fig-06": ([("gratuity_estimate", {"monthly_wage": 52000, "years": 3, "months": 2}, None)], []),
    "jn-03": ([("encashable_days", {"balance": 50, "cap": 45}, "LV-07")], [("60", "NP-03")]),
    "lk-01": ([], [("40,000", "EXP-12")]),
    "lk-04": ([], [("15", "PB-02")]),
    "lk-06": ([], [("60", "NP-03")]),
    "lk-07": ([], [("1.75", "LV-01")]),
    "lk-17": ([], [("fifteen days", "gratuity_rate")]),
    "iso-01": ([], [("25,000", "EXP-12")]),
}


def clause_text(tenant: str, where: str) -> str:
    """A handbook clause's words in the tenant's chunk of it, or a Code's line as desk_calc quotes it."""
    if where in desk_calc.RULES:
        return desk_calc.RULES[where]["quote"]
    chunk = agent_eval.clause_chunk(tenant, where)
    return desk_calc.clause_text(chunk, where) if chunk else ""


def run(name: str, args: dict, tenant: str, clause: str | None, question: str) -> dict:
    """One calculator call as the desk makes it: check_args on the question and the clause's chunk, then calculate()."""
    passages = [agent_eval.clause_chunk(tenant, clause)] if clause else []
    refused, found = desk_calc.check_args(name, args, passages, question)
    if refused:
        raise AssertionError(f"{name}{args}: {refused}")
    where = {k: "your message" if v == desk_calc.MESSAGE else f"{v['clause']} [{v['n']}]" for k, v in found.items()}
    return {**desk_calc.calculate(name, found=found, **args), "args": args, "found": where}


def quiet(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        code = fn(*a, **kw)
    return code, out.getvalue()


# ================================================================== the set
class TheSet(unittest.TestCase):
    def test_twelve_dev_route_rows(self):
        self.assertEqual(route_eval.check_rows(ARMS), [])
        self.assertEqual([r["id"] for r in ARMS], list(FIG) + ["jn-03"] + list(LOOKUPS))
        self.assertNotIn("fig-04", BY_ID)                 # the notice-and-wages chain waits for its chain edge
        for r in ARMS:
            self.assertEqual((r["split"], r["expected_outcome"], r["language"]), ("dev", "answer", "en"), r["id"])
            self.assertNotIn(r["tenant"], route_eval.SINGLE)          # every arm routes: globex runs one desk
        self.assertEqual({r["tenant"] for r in ARMS}, {"acme", "zeta"})

    def test_rows_from_the_route_set_are_unchanged_and_in_bs_index(self):
        index = {r["id"] for r in route_eval.index_rows(ROUTES)}
        texts = {route_eval.normalise(r["question"]) for r in ROUTES}
        texts |= {route_eval.normalise(r["prev_question"]) for r in ROUTES if r["prev_question"]}
        for r in ARMS:
            with self.subTest(row=r["id"]):
                if r["source"] == "new":
                    self.assertNotIn(r["id"], ROUTES_BY_ID)
                    self.assertNotIn(route_eval.normalise(r["question"]), texts)     # B's exemplar index lacks it
                    self.assertEqual(r["author"], "model-draft")
                else:
                    self.assertEqual(r, ROUTES_BY_ID[r["id"]])
                    self.assertIn(r["id"], index)                                    # make route-index embeds it
        self.assertEqual(sorted(r["id"] for r in ARMS if r["source"] == "new"), sorted(FIG))

    def test_nothing_the_prompt_has_seen(self):
        exemplars = {i for i, _, _ in route_eval.router()[1].PROMPT_EXEMPLARS}
        self.assertFalse(exemplars & set(BY_ID))
        self.assertFalse(route_eval.prompt_groups(ROUTES) & {r["group"] for r in ARMS})
        self.assertEqual(route_eval.prompt_groups(ARMS), set())          # so --live scores every row

    def test_the_labelling_rule_the_gate_and_the_mask(self):
        self.assertEqual(build_routes.label_errors(ARMS), [])
        for r in ARMS:
            self.assertIsNone(desk_rules.gate(r["question"]), r["id"])  # no row is taken to a case by rule
            self.assertEqual(desk_rules.mask(r["question"])[1], [], r["id"])

    def test_arm_b_asks_the_classifier_on_every_figure_row(self):
        """Arm B answers in agent mode only when L1 says needs_calculation: an identifier anchor that decided a figure
        row at Rs 0 would send it to a direct answer. The router in process, on route_eval --local's scripted models,
        asks L1 on each figure row and on jn-03."""
        _, desk_routes = route_eval.router()
        rows = [BY_ID[i] for i in FIG + ("jn-03",)]
        pool = route_eval.index_rows(ROUTES)
        vectors = {r["id"]: route_eval.offline_embed(r["question"]) for r in pool + rows}
        classes = route_eval._tenant_classes()
        base = route_eval.build_index(pool, vectors)
        indexes = {t: [e for e in base if e["route"] in desk_routes.enabled_routes(classes.get(t, ()))]
                   for t in route_eval.TENANTS if t not in route_eval.SINGLE}
        for x in route_eval.route_run(rows, indexes, route_eval.ScriptedModels(rows, vectors)):
            self.assertNotIn(x["decision"]["method"], ("anchor", "rule", "single"), x["id"])
            self.assertIsNotNone(x["decision"]["l1"], x["id"])


# ================================================================== every figure
class EveryFigure(unittest.TestCase):
    def test_the_table_covers_the_set(self):
        self.assertEqual(set(FIGURES), set(BY_ID))

    def test_every_figure_recomputed(self):
        held = agent_eval._holdings()
        for rid, (calls, lookups) in FIGURES.items():
            r = BY_ID[rid]
            with self.subTest(row=rid):
                texts = []
                for name, args, clause in calls:
                    spec = desk_calc.CALCULATORS[name]
                    self.assertEqual(spec["desk"], r["expected_route"])           # the row's desk runs it
                    if spec["needs"]:
                        self.assertIn(spec["needs"], held[r["tenant"]])           # its Code is the tenant's
                    texts.append(run(name, args, r["tenant"], clause, r["question"])["formula"])
                for figure, where in lookups:
                    self.assertTrue(contains(clause_text(r["tenant"], where), figure), (figure, where))
                    self.assertIn(figure, r["must_contain"])
                    texts.append(clause_text(r["tenant"], where))
                for want in r["must_contain"]:
                    self.assertTrue(any(contains(t, want) for t in texts), want)   # each figure accounted for

    def test_a_figure_row_asks_for_a_figure_only_code_works_out(self):
        """Arm C answers directly and runs no calculator: on fig-01 to fig-05 a figure the row asks for is in neither
        the question nor what the calculation reads (the clause, or the whole Code), so copying cannot give it."""
        for rid in ("fig-01", "fig-02", "fig-03", "fig-05"):
            r = BY_ID[rid]
            read = [r["question"]]
            for name, _, clause in FIGURES[rid][0]:
                need = desk_calc.CALCULATORS[name]["needs"]
                read.append(clause_text(r["tenant"], clause) if clause else
                            (EVALS / "corpus" / r["tenant"] / f"{need}.md").read_text(encoding="utf-8"))
            only = [w for w in r["must_contain"] if not any(contains(t, w) for t in read)]
            self.assertTrue(only, rid)

    def test_fig_06_has_no_figure_and_guards_the_sum_that_ignores_five_years(self):
        r = BY_ID["fig-06"]
        result = run("gratuity_estimate", {"monthly_wage": 52000, "years": 3, "months": 2}, "acme", None, r["question"])
        self.assertIsNone(result["value"])
        self.assertIs(result["eligible"], False)
        self.assertTrue(contains(result["formula"], "five years"))
        ignored = int(52000 / desk_calc.GRATUITY_DIVISOR * desk_calc.GRATUITY_DAYS * 3)    # 2 months count for none
        self.assertEqual(r["must_not_contain"], [desk_calc.inr(ignored).removeprefix("Rs ")])
        self.assertFalse(contains(result["formula"], r["must_not_contain"][0]))

    def test_fig_05_tells_zetas_cap_from_acmes(self):
        r = BY_ID["fig-05"]
        acme = desk_calc.carry_forward(34, 30)                       # acme's LV-01 cap, the other tenant's figure
        self.assertTrue(contains(clause_text("acme", "LV-01"), "30"))
        self.assertFalse(any(contains(acme["formula"], w) for w in r["must_contain"]))
        refused, _ = desk_calc.check_args("carry_forward", {"days": 34, "cap": 30},
                                          [agent_eval.clause_chunk("zeta", "LV-01")], r["question"])
        self.assertTrue(refused)                                     # zeta's LV-01 does not write 30

    def test_jn_03_is_the_trap_and_iso_01_the_other_tenants_figure(self):
        jn = run("encashable_days", {"balance": 50, "cap": 45}, "acme", "LV-07", BY_ID["jn-03"]["question"])
        self.assertEqual((jn["value"], jn["found"]), (45, {"balance": "your message", "cap": "LV-07 [1]"}))
        self.assertTrue(contains(clause_text("acme", "LV-07"), "45"))     # LV-07 writes the answer too
        self.assertEqual(BY_ID["iso-01"]["must_not_contain"], ["40,000"])
        self.assertTrue(contains(clause_text("acme", "EXP-12"), "40,000"))
        self.assertFalse(contains(clause_text("zeta", "EXP-12"), "40,000"))


# ================================================================== what a live run keeps
def agent_reply(row: dict, arm: str, refusals=()) -> dict:
    """A /v1/desk reply in agent mode: the figures a clause writes, then each calculation desk_calc returns for the
    row, its line written by code."""
    calls, lookups = FIGURES[row["id"]]
    calcs = [run(n, a, row["tenant"], c, row["question"]) for n, a, c in calls]
    answer = (" ".join(f"It is {figure} [1]." for figure, _ in lookups) or "From the passages [1].") + \
        "\n\nWorked out in code:\n" + "\n".join(f"- {c['formula']}." for c in calcs)
    return {"tenant": row["tenant"], "outcome": "answer", "answer": answer, "citations": [], "retrieve_calls": 1,
            "sections": [{"desk": row["expected_route"], "title": "t", "answer": answer, "mode": "agent",
                          "calculations": calcs, "refusals": list(refusals), "tool_calls": [], "citations": []}],
            "model_calls": 4, "limits": {"model_calls": 4, "cost_inr": 1.2345, "stopped_by": None}, "latency_ms": 5000}


class WhatALiveRunKeeps(unittest.TestCase):
    ROUTE = {"route": "handbook", "model_calls": 1, "decision": {"desk": "handbook"}}

    def test_a_desk_turn_keeps_its_sections_calls_rupees_and_latency(self):
        row = BY_ID["jn-03"]
        reply = agent_reply(row, "Astar", refusals=["encashable_days"])
        p = route_eval.live_prediction(row, self.ROUTE, reply, "Astar", 6123.4)
        self.assertEqual(p["sections"], [{"desk": "handbook", "mode": "agent", "refusals": ["encashable_days"],
                                          "calculations": reply["sections"][0]["calculations"]}])
        self.assertEqual(p["sections"][0]["calculations"][0]["found"], {"balance": "your message", "cap": "LV-07 [1]"})
        self.assertEqual((p["desk_model_calls"], p["desk_cost_inr"], p["desk_latency_ms"]), (4, 1.2345, 6123))
        self.assertEqual(p["model_calls"], 1)                       # the router's /v1/route calls, as before

    def test_a_measure_the_reply_lacks_is_left_out(self):
        row = BY_ID["lk-06"]
        bare = route_eval.live_prediction(row, self.ROUTE, {"outcome": "answer", "answer": "60", "citations": [],
                                                            "retrieve_calls": 1}, "B")
        self.assertEqual(bare["sections"], [])
        for key in route_eval.DESK_MEASURES:
            self.assertNotIn(key, bare)                               # never written as 0
        no_desk = route_eval.live_prediction(row, {"route": "out_of_scope", "model_calls": 1}, None, "B")
        self.assertNotIn("sections", no_desk)

    def test_report_rows_put_the_turn_beside_the_verdict(self):
        row = BY_ID["jn-03"]
        p = route_eval.live_prediction(row, self.ROUTE, agent_reply(row, "B", ["encashable_days"]), "B", 900.0)
        verdicts = [{"id": "jn-03", "correct": True}, {"id": "lk-06", "correct": False}]
        rows = route_eval.report_rows(verdicts, {"jn-03": p, "lk-06": {"id": "lk-06", "route": "handbook"}})
        self.assertEqual(rows[0], {"id": "jn-03", "correct": True, "desk_model_calls": 4, "desk_cost_inr": 1.2345,
                                   "desk_latency_ms": 900, "modes": ["agent"], "calculators": ["encashable_days"],
                                   "refusals": ["encashable_days"]})
        self.assertEqual(rows[1], verdicts[1])                        # no desk turn: the verdict alone, as before


# ================================================================== a live run of the three arms, end to end
C_SAYS = {"fig-01": "About Rs 2,30,000 [1]: fifteen days' wages for 7 years 8 months, pro rata.",
          "fig-02": "About Rs 2,25,000 [1].",
          "fig-03": "Your notice ends on 5 December 2026 [1].",
          "fig-05": "You can carry forward 18 days [1]; the rest lapses.",
          "fig-06": "Gratuity needs five years of continuous service [1], so none is due yet.",
          "jn-03": "45 days are encashed, the cap in LV-07 [1], and you serve 60 days' notice [2]."}
CLAUSES = {"fig-03": ["NP-03"], "fig-05": ["LV-01"], "jn-03": ["LV-07", "NP-03"], "lk-01": ["EXP-12"],
           "lk-04": ["PB-02"], "lk-06": ["NP-03"], "lk-07": ["LV-01"], "iso-01": ["EXP-12"]}
COST, CALLS = {"B": 0.62, "C": 0.41, "Astar": 1.85}, {"B": 3, "C": 1, "Astar": 4}
CODE_QUOTE = " ".join(desk_calc.RULES[k]["quote"] for k in ("gratuity_service", "gratuity_rate", "gratuity_monthly"))


class StandIn:
    """The chat service, scripted for the arms set: /v1/route gives the row's own route; /v1/desk answers as each arm
    would - B in agent mode on a row that needs a calculator and directly otherwise, A* in agent mode on every row, C
    directly on every row, writing a figure of its own on fig-01 to fig-05 - and cites the clause or the Code."""

    def __init__(self):
        self.sent = []

    @staticmethod
    def minter(account, audience):
        return "token-" + account.split("@")[0]

    def poster(self, base, path, token, body, **kw):
        self.sent.append((path, body))
        arm = body.get("arm", "B")
        row = next(r for r in ARMS if r["question"] == body["question"])
        if path == "/v1/route":
            return 200, {"tenant": row["tenant"], "route": row["expected_route"], "case_type": None,
                         "model_calls": int(arm == "B"), "router_ms": 40, "cost_inr": 0.02 if arm == "B" else 0.0,
                         "decision": {"desk": None}}
        calls, lookups = FIGURES[row["id"]]
        if row["expected_route"] == "statute":
            cites = [{"source_uri": f"gs://documind-ai-YOUR-ID-uploads/{row['tenant']}/code_on_social_security_2020.pdf",
                      "quote": CODE_QUOTE}]
        else:
            book = "hr_policy_2026.md" if row["tenant"] == "acme" else "hr_policy_zeta_2026.md"
            cites = [{"source_uri": f"gs://documind-ai-YOUR-ID-uploads/{row['tenant']}/{book}",
                      "quote": clause_text(row["tenant"], c)} for c in CLAUSES[row["id"]]]
        agent = arm == "Astar" or (arm == "B" and bool(calls))
        reply = agent_reply(row, arm, ["encashable_days"] if (arm, row["id"]) == ("Astar", "jn-03") else ()) \
            if agent and calls else {"sections": [{"desk": row["expected_route"], "mode": "agent" if agent else "direct",
                                                   "refusals": [], "calculations": []}]}
        if calls and not agent:
            reply["answer"] = C_SAYS[row["id"]]
        elif not calls:
            reply["answer"] = " ".join(f"It is {figure} [1]." for figure, _ in lookups)
        reply.update(tenant=row["tenant"], outcome="answer", citations=cites, retrieve_calls=1, model_calls=CALLS[arm],
                     limits={"model_calls": CALLS[arm], "cost_inr": COST[arm]})
        return 200, reply


class ALiveRunOfTheArms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.files, cls.out, cls.sent = {}, {}, {}
        for arm in ("B", "C", "Astar"):
            save, rep = (os.path.join(cls.tmp.name, f"arms_{arm}.{ext}") for ext in ("jsonl", "json"))
            service = StandIn()
            a = types.SimpleNamespace(arm=arm, chat_url="https://documind-chat-NUMBER.asia-south1.run.app",
                                      project="documind-ai-YOUR-ID", routes=ARMS_FILE, split="dev", registry=None,
                                      save=save, report=rep)
            code, cls.out[arm] = quiet(route_eval.run_live, a, minter=service.minter, poster=service.poster)
            assert code == 0, cls.out[arm][-800:]
            cls.files[arm], cls.sent[arm] = (save, rep), service.sent

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def saved(self, arm):
        with open(self.files[arm][0], encoding="utf-8") as f:
            return {p["id"]: p for p in map(json.loads, f)}

    def test_every_row_to_both_routes(self):
        for arm, sent in self.sent.items():
            self.assertEqual(sum(p == "/v1/route" for p, _ in sent), 12, arm)
            self.assertEqual(sum(p == "/v1/desk" for p, _ in sent), 12, arm)      # every row is an answer row
            self.assertTrue(all(b.get("arm") == (None if arm == "B" else arm) for _, b in sent), arm)

    def test_the_saves_keep_each_turn(self):
        b, c, astar = self.saved("B"), self.saved("C"), self.saved("Astar")
        self.assertEqual([s["mode"] for s in b["fig-01"]["sections"]], ["agent"])
        self.assertEqual(b["fig-01"]["sections"][0]["calculations"][0]["value"], 240000)
        self.assertEqual([s["mode"] for s in b["lk-06"]["sections"]], ["direct"])
        self.assertEqual([s["mode"] for s in astar["lk-06"]["sections"]], ["agent"])
        self.assertEqual(astar["jn-03"]["sections"][0]["refusals"], ["encashable_days"])
        self.assertFalse(any(combine.calculations(p) for p in c.values()))          # C runs no calculator
        self.assertEqual({(p["desk_model_calls"], p["desk_cost_inr"]) for p in c.values()}, {(1, 0.41)})
        self.assertTrue(all(isinstance(p["desk_latency_ms"], int) for p in b.values()))

    def test_compare_the_three_reports(self):
        code, out = quiet(route_eval.main, ["--compare", self.files["Astar"][1], self.files["C"][1], self.files["B"][1]])
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(lines[0], "compare: arms B, C, Astar on the same 12 rows, split dev")
        rate = route_eval.rate
        for arm, right, turn in (("B", 12, "3.0"), ("C", 8, "1.0"), ("Astar", 12, "4.0")):
            block = out.split(f"arm {arm} (", 1)[1].split("\narm ", 1)[0].split("\nB against", 1)[0]
            self.assertIn(f"  {'correct_rate (answer rows)':<30}{rate(right, 12)}", block)
            self.assertIn(f"  {'authority_rate':<30}{rate(12, 12)}", block)
            self.assertIn(f"Rs {12 * COST[arm]:.4f} in all, Rs {COST[arm]:.4f} a turn; {12 * CALLS[arm]} model calls, "
                          f"{turn} a turn", block)
            self.assertIn("p50 ", block)
        self.assertIn(f"  {'agent mode':<30}6 of 12 turns; 6 calculator results, 0 refused tool calls",
                      out.split("arm B (", 1)[1].split("\narm C", 1)[0])
        self.assertIn(f"  {'agent mode':<30}0 of 12 turns; 0 calculator results, 0 refused tool calls", out)
        self.assertIn(f"  {'agent mode':<30}12 of 12 turns; 6 calculator results, 1 refused tool calls", out)
        # B against C on correct, through evals/paired.py: C right on 8 rows, B on all 12
        d, lo, hi = paired.newcombe(8, 0, 4, 0)
        self.assertIn("B against C, row by row\n  paired (correct), 12 rows: both 8, C only 0, B only 4, neither 0\n"
                      f"  B - C = {100 * d:+.1f} points, 95% [{100 * lo:+.1f}, {100 * hi:+.1f}] (Newcombe), "
                      f"exact McNemar p = {paired.mcnemar(0, 4):.3f}\n  {paired.verdict(lo, hi, 'C', 'B')} "
                      f"(margin {100 * paired.MARGIN:g} points, registered {paired.MARGIN_REGISTERED})", out)
        d, lo, hi = paired.newcombe(12, 0, 0, 0)
        self.assertIn("B against Astar, row by row\n  paired (correct), 12 rows: both 12, Astar only 0, B only 0, "
                      f"neither 0\n  B - Astar = {100 * d:+.1f} points, 95% [{100 * lo:+.1f}, {100 * hi:+.1f}]", out)
        self.assertIn("no conclusion at this many rows", out)
        self.assertEqual(lines[-1], "indicative, not a ship decision: the rows are dev rows, not a test split people "
                                    "wrote; B's exemplar index (make route-index: the dev rows of evals/routes.jsonl) "
                                    "holds 7 of these 12 rows, so on them B's figures are an upper bound; C and Astar "
                                    "read no index")

    def test_combine_the_three_saves(self):
        code, out = quiet(combine.main, [self.files[arm][0] for arm in ("B", "C", "Astar")])
        self.assertEqual(code, 0)
        self.assertIn("combine: arms B, C, Astar on 12 answer rows of evals/route_arms.jsonl, split dev", out)
        self.assertIn("fig-01 B right, C wrong, Astar right; vote: gratuity_estimate = 240000 from 2 of 3 members, B's "
                      "answer: right", out)
        self.assertIn("lk-06  B right, C right, Astar right\n", out)
        self.assertIn("  all right on 8 rows, some on 4, none on 0", out)
        self.assertIn("the vote, on the 6 rows where a member ran a calculator\n  right 6, wrong 0, abstained 0", out)
        self.assertIn("  C      fig-01: 2,30,000; fig-02: 2,25,000; fig-03: 2026-12-05\n", out)
        self.assertIn("  B      none\n", out)
        self.assertIn("  Astar  none\n", out)


# ================================================================== --compare's refusals
def a_report(arm, rows, split="dev"):
    return {"arm": arm, "split": split, "tally": {}, "confusion": {}, "rows": rows}


class CompareRefuses(unittest.TestCase):
    def write(self, tmp, name, obj):
        path = os.path.join(tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(obj if isinstance(obj, str) else json.dumps(obj))
        return path

    def test_what_it_refuses(self):
        rows = [{"id": "lk-06", "correct": True, "authority_ok": True}]
        with tempfile.TemporaryDirectory() as tmp:
            b, c = self.write(tmp, "b.json", a_report("B", rows)), self.write(tmp, "c.json", a_report("C", rows))
            cases = {"one report an arm": [b, self.write(tmp, "b2.json", a_report("B", rows))],
                     "give B's report too": [c, self.write(tmp, "a.json", a_report("Astar", rows))],
                     "compare runs of one split": [b, self.write(tmp, "t.json", a_report("C", rows, "test"))],
                     "scores other rows": [b, self.write(tmp, "o.json", a_report("C", [{"id": "lk-04"}]))],
                     "not a --report file": [b, self.write(tmp, "x.json", "[1, 2]")]}
            for words, paths in cases.items():
                with self.assertRaises(SystemExit) as stop:
                    quiet(route_eval.compare, paths)
                self.assertIn(words, str(stop.exception))
            for argv in (["--compare", b], ["--compare"], ["--compare", b, c, "--local"], ["--compare", b, c, b, c]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stop:
                    route_eval.main(argv)
                self.assertEqual(stop.exception.code, 2, argv)
            code, out = quiet(route_eval.main, ["--compare", b, c])          # reports with no desk turn
            self.assertEqual(code, 0)
            self.assertIn(f"  {'desk turns':<30}not measured", out)
            self.assertIn("paired (correct), 1 rows: both 1, C only 0, B only 0, neither 0", out)


# ================================================================== the make targets
class Wiring(unittest.TestCase):
    def read(self, *parts):
        return KIT.joinpath(*parts).read_text(encoding="utf-8")

    def test_the_targets_and_route_evals_line(self):
        mk, agents, readme = self.read("Makefile"), self.read("mk", "agents.mk"), self.read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                         # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        for target in ("route-compare", "arms-combine"):
            self.assertIn(target, phony)
            self.assertIn(f"`{target}`", readme)
            self.assertGreater(agents.index(f"\n{target}:\n"), agents.index("\nroute-eval: guard-project\n"))  # appended
        self.assertIn('\nroute-compare:\n\t$(PY) evals/route_eval.py --compare $(foreach f,$(REPORTS),"$(f)")\n', agents)
        self.assertIn('\narms-combine:\n\t$(PY) evals/combine.py $(foreach f,$(SAVES),"$(f)") '
                      '$(if $(ROUTES),--routes "$(ROUTES)",)\n', agents)
        lines = agents.splitlines()
        at = lines.index("route-eval: guard-project") + 2                   # lesson 10.4's own derivation
        self.assertEqual(at, 214)
        self.assertIn("evals/route_eval.py --live", lines[at + 1])
        self.assertTrue(lines[at + 1].endswith(' $(if $(ROUTES),--routes "$(ROUTES)",)'))   # on its existing line
        self.assertNotIn("--registry", lines[at + 1])

    def test_out_of_the_selftest_and_desk_check_and_in_unowned(self):
        code, out = quiet(route_eval.selftest)
        self.assertEqual(code, 0)
        self.assertNotIn("route_arms", out)
        self.assertNotIn("test_route_arms", self.read("commands", "desk-check.sh"))
        unowned, index = self.read("UNOWNED.md"), self.read("INDEX.md").splitlines()

        def quoted(f):                    # its row moves to INDEX.md once a page quotes it (the page PR adopts it)
            row = next((line for line in index if line.startswith(f"| `{f}` |")), "")
            return row.split(" | ")[2:3] not in ([], ["-"])

        for f in ("evals/route_arms.jsonl", "evals/combine.py", "evals/tests/test_route_arms.py",
                  "evals/tests/test_combine.py"):
            self.assertTrue(f"| `{f}` | **10.5** |" in unowned or quoted(f), f"no UNOWNED.md row for {f}")


if __name__ == "__main__":
    unittest.main()
