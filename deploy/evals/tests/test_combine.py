"""evals/combine.py, the Desk's arms combined (workshop lesson 10.5): the vote and its tie rule, the proposals read from
a run's sections, the figure check on a member's answer, a combine over saved runs with a tie in it, the selftest at
two and three layers (the aggregator's figure flagged at every layer, the abstaining split, the calls each combiner
adds), what it refuses, and the make target.

Run with ``python -m unittest discover -s evals/tests -p test_combine.py`` from deploy/. Stdlib only; CI runs it with
evals/tests.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]
KIT = EVALS.parent
for _p in (str(KIT), str(EVALS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import agent_eval  # noqa: E402  - the lane's chunk of a clause
import combine  # noqa: E402
import route_eval  # noqa: E402
from shared import desk_calc  # noqa: E402

ROWS = route_eval.load_rows(combine.ARMS_FILE)
BY_ID = {r["id"]: r for r in ROWS}
BUCKET = "gs://documind-ai-YOUR-ID-uploads"
CODE = {"source_uri": f"{BUCKET}/acme/code_on_social_security_2020.pdf", "quote": combine.PASSAGE}
P240 = (("gratuity_estimate", "240000"),)
P210 = (("gratuity_estimate", "210000"),)


def calc(name, **args):
    return {**desk_calc.calculate(name, **args), "args": args}


def clause(tenant, code):
    chunk = agent_eval.clause_chunk(tenant, code)
    book = "hr_policy_2026.md" if tenant == "acme" else "hr_policy_zeta_2026.md"
    return {"source_uri": f"{BUCKET}/{tenant}/{book}", "quote": desk_calc.clause_text(chunk, code)}


def pred(rid, arm, answer, calcs=(), cites=()):
    """A saved prediction as route_eval.py --live --save writes one for a desk turn."""
    return {"id": rid, "route": BY_ID[rid]["expected_route"], "arm": arm, "outcome": "answer", "answer": answer,
            "citations": list(cites), "retrieve_calls": 1, "model_calls": 1,
            "sections": [{"desk": BY_ID[rid]["expected_route"], "mode": "agent" if calcs else "direct",
                          "refusals": [], "calculations": list(calcs)}]}


def quiet(fn, *a, **kw):
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
        code = fn(*a, **kw)
    return code, out.getvalue()


class TheVote(unittest.TestCase):
    def test_the_proposal_more_members_make_wins(self):
        self.assertEqual(combine.vote({"B": P240, "C": None, "Astar": P240}), (P240, 2, ""))
        self.assertEqual(combine.vote({"B": P240, "C": P210, "Astar": P240}), (P240, 2, ""))
        self.assertEqual(combine.vote({"B": None, "C": None, "Astar": P210}), (P210, 1, ""))

    def test_a_tie_abstains_to_a_person(self):
        self.assertEqual(combine.vote({"B": P240, "Astar": P210}), (None, 0, "a tie, 2 proposals made by 1 member each"))
        third = (("gratuity_estimate", "230769"),)
        self.assertEqual(combine.vote({"B": P240, "C": third, "Astar": P210})[:2], (None, 0))
        self.assertEqual(combine.vote({"B": None, "C": None}), (None, 0, "no member's answer holds a calculation"))

    def test_a_proposal_is_what_code_returned(self):
        self.assertEqual(combine.proposal(pred("fig-05", "B", "x", [calc("carry_forward", days=34, cap=18)])),
                         (("carry_forward", "18.0"),))
        self.assertIsNone(combine.proposal(pred("fig-05", "C", "You can carry forward 18 days [1].")))
        both = pred("jn-03", "B", "x", [calc("notice_end", ack_date="2026-10-05", days=60),
                                         calc("encashable_days", balance=50, cap=45)])
        self.assertEqual(combine.proposal(both), (("encashable_days", "45.0"), ("notice_end", '"2026-12-04"')))
        self.assertEqual(combine.said(combine.proposal(both)), "encashable_days = 45, notice_end = 2026-12-04")
        self.assertEqual(combine.said(combine.proposal(pred("fig-06", "B", "x", [
            calc("gratuity_estimate", monthly_wage=52000, years=3, months=2)]))), "gratuity_estimate = no figure")
        self.assertEqual(combine.said((("threshold_check", "true"), ("carry_forward", "18.0"))),
                         "threshold_check = yes, carry_forward = 18")


class TheFigureCheck(unittest.TestCase):
    def test_a_figure_no_calculation_returned_and_no_source_writes(self):
        row = BY_ID["fig-01"]
        self.assertEqual(combine.invented(row, pred("fig-01", "C", "About Rs 2,30,000 [1].", cites=[CODE])),
                         ["2,30,000"])
        g = calc("gratuity_estimate", monthly_wage=52000, years=7, months=8)
        backed = pred("fig-01", "B", f"About Rs 2,40,000 [1].\n\nWorked out in code:\n- {g['formula']}.", [g], [CODE])
        self.assertEqual(combine.invented(row, backed), [])

    def test_a_figure_a_cited_passage_writes(self):
        row = BY_ID["lk-06"]
        quoted = pred("lk-06", "C", "It is 60 days [1].", cites=[clause("acme", "NP-03")])
        self.assertEqual(combine.invented(row, quoted), [])
        self.assertEqual(combine.invented(row, pred("lk-06", "C", "It is 60 days.")), ["60"])

    def test_an_in_force_line_code_added_is_a_source(self):
        row = BY_ID["lk-17"]
        cgst = {"source_uri": f"{BUCKET}/acme/cgst_act_2017.pdf", "quote": "a section"}
        text = "See [1].\n\nCentral Goods and Services Tax Act, 2017: the text here is as on 1 August 2021."
        self.assertEqual(combine.invented(row, pred("lk-17", "C", text, cites=[cgst])), [])
        self.assertEqual(combine.invented(row, pred("lk-17", "C", text)), ["2021-08-01"])


def runs_with_a_tie():
    """Three saved runs on the arms set: B and Astar compute every figure row, C answers them directly; on fig-02
    Astar's calculator was given seven years six months read as eight months, so B and Astar tie there."""
    out = {"B": [], "C": [], "Astar": []}
    wrong_c = {"fig-01": "About Rs 2,30,000 [1].", "fig-02": "About Rs 2,25,000 [1].",
               "fig-03": "It ends on 5 December 2026 [1].", "fig-05": "You can carry forward 18 days [1].",
               "fig-06": "Gratuity needs five years of continuous service [1].",
               "jn-03": "45 days are encashed [1] and your notice is 60 days [2]."}
    for r in ROWS:
        rid = r["id"]
        if rid.startswith("fig-") or rid == "jn-03":
            args = {"fig-01": ("gratuity_estimate", {"monthly_wage": 52000, "years": 7, "months": 8}),
                    "fig-02": ("gratuity_estimate", {"monthly_wage": 52000, "years": 7, "months": 6}),
                    "fig-03": ("notice_end", {"ack_date": "2026-10-05", "days": 60}),
                    "fig-05": ("carry_forward", {"days": 34, "cap": 18}),
                    "fig-06": ("gratuity_estimate", {"monthly_wage": 52000, "years": 3, "months": 2}),
                    "jn-03": ("encashable_days", {"balance": 50, "cap": 45})}[rid]
            codes = {"fig-03": ["NP-03"], "fig-05": ["LV-01"], "jn-03": ["LV-07", "NP-03"]}.get(rid, [])
            cites = [CODE] if r["expected_route"] == "statute" else [clause(r["tenant"], c) for c in codes]
            for arm in ("B", "Astar"):
                a = dict(args[1], months=8) if (arm, rid) == ("Astar", "fig-02") else args[1]
                c = calc(args[0], **a)
                lead = "Your notice is 60 days [2]. " if rid == "jn-03" else ""
                out[arm].append(pred(rid, arm, f"{lead}See [1].\n\nWorked out in code:\n- {c['formula']}.", [c], cites))
            out["C"].append(pred(rid, "C", wrong_c[rid], cites=cites))
        else:                                           # a lookup: every arm quotes the clause that writes it
            where = {"lk-01": ("acme", "EXP-12"), "lk-04": ("acme", "PB-02"), "lk-06": ("acme", "NP-03"),
                     "lk-07": ("acme", "LV-01"), "iso-01": ("zeta", "EXP-12")}.get(rid)
            for arm in out:
                out[arm].append(pred(rid, arm, f"It is {r['must_contain'][0]} [1].",
                                     cites=[clause(*where) if where else CODE]))
    return out


class OverSavedRuns(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.paths = {}
        for arm, preds in runs_with_a_tie().items():
            self.paths[arm] = self.write(f"{arm}.jsonl", preds)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, preds):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(json.dumps(p) + "\n" for p in preds))
        return path

    def test_the_combined_report(self):
        runs = combine.load_runs([self.paths[a] for a in ("B", "C", "Astar")], set(BY_ID))
        got = combine.combine(runs, ROWS, combine.ARMS_FILE, "dev", out=io.StringIO())
        self.assertEqual(got, {"agree": {"all": 8, "some": 4}, "voted": 6, "right": 5, "wrong": 0, "abstained": 1,
                               "flagged": {"B": 0, "C": 3, "Astar": 0}})
        code, out = quiet(combine.main, [self.paths[a] for a in ("B", "C", "Astar")])
        self.assertEqual(code, 0)
        self.assertIn("fig-02 B right, C wrong, Astar wrong; vote: a tie, 2 proposals made by 1 member each, to a "
                      "person\n", out)
        self.assertIn("fig-06 B right, C right, Astar right; vote: gratuity_estimate = no figure from 2 of 3 members, "
                      "B's answer: right\n", out)
        self.assertIn(f"  {'B':<30}{route_eval.rate(12, 12)}\n  {'C':<30}{route_eval.rate(8, 12)}\n"
                      f"  {'Astar':<30}{route_eval.rate(11, 12)}\n  all right on 8 rows, some on 4, none on 0", out)
        self.assertIn("the vote, on the 6 rows where a member ran a calculator\n  right 5, wrong 0, abstained 1 (a tie: "
                      f"to a person); right {route_eval.rate(5, 6)}\n  the best single arm there: B "
                      f"{route_eval.rate(6, 6)}", out)
        self.assertIn("  C      fig-01: 2,30,000; fig-02: 2,25,000; fig-03: 2026-12-05\n", out)

    def test_what_it_refuses(self):
        b = self.paths["B"]
        mixed = self.write("mixed.jsonl", [dict(p, arm="C") if p["id"] == "lk-06" else p
                                           for p in runs_with_a_tie()["B"]])
        unarmed = self.write("unarmed.jsonl", [{k: v for k, v in p.items() if k != "arm"}
                                               for p in runs_with_a_tie()["B"]])
        routes_only = self.write("routes.jsonl", [{"id": p["id"], "route": p["route"], "arm": "C"}
                                                  for p in runs_with_a_tie()["C"]])
        for paths, words in (([b, b], "a second run of arm B"), ([mixed, self.paths["C"]], "score one arm at a time"),
                             ([unarmed, self.paths["C"]], "name no arm"), ([b, routes_only], "no answer text")):
            with self.assertRaises(SystemExit) as stop:
                combine.main(paths)
            self.assertIn(words, str(stop.exception))
        for argv in ([b], [], [b, self.paths["C"], "--layers", "2"], ["--selftest", b], ["--selftest", "--layers", "0"],
                     ["--selftest", "--layers", str(combine.LAYERS_MAX + 1)]):
            with self.assertRaises(SystemExit) as stop:
                quiet(combine.main, argv)
            self.assertEqual(stop.exception.code, 2, argv)


class TheSelftest(unittest.TestCase):
    def test_two_layers(self):
        code, out = quiet(combine.main, ["--selftest", "--layers", "2"])
        self.assertEqual(code, 0, out)
        lines = out.splitlines()
        self.assertEqual(sum("; unsupported: 2,25,000; 1 model call" in line for line in lines), 2)
        first = next(i for i, x in enumerate(lines) if x.startswith("  layer 1 "))
        self.assertTrue(lines[first + 1].startswith("  layer 2 "))
        self.assertIn(f"  {'P3':<10} no calculation, it writes \"About Rs 2,10,000 [1]: fifteen days' wages for each of "
                      "the 7 completed years.\"; wrong; unsupported: 2,10,000", out)
        self.assertIn(f"  {'':<10} a tie, 3 proposals made by 1 member each: the row goes to a person; 0 model calls",
                      out)
        self.assertIn(f"  {'calls':<10} the vote 0, the arbiter 1, the aggregator 2 (one a layer)", out)
        self.assertNotIn("FAIL", out)
        self.assertEqual(lines[-1], "the vote and the arbiter wrote no figure of their own; the aggregator wrote one no "
                                    "member computed, flagged at every layer")

    def test_one_and_three_layers(self):
        code, out = quiet(combine.main, ["--selftest"])
        self.assertEqual(code, 0, out)
        self.assertNotIn("  layer 2 ", out)
        self.assertIn("the aggregator 1 (one a layer)", out)
        code, out = quiet(combine.main, ["--selftest", "--layers", "3"])
        self.assertEqual(code, 0, out)
        self.assertEqual(out.count("; unsupported: 2,25,000; 1 model call"), 3)
        self.assertIn("the aggregator 3 (one a layer)", out)

    def test_its_row_is_the_sets(self):
        self.assertEqual(BY_ID[combine.SELF_ROW]["must_contain"], ["2,40,000"])
        self.assertIn("I earn Rs 52,000 a month and leave after 7 years 8 months", BY_ID[combine.SELF_ROW]["question"])


class Wiring(unittest.TestCase):
    def test_the_make_target_and_its_row(self):
        agents = (KIT / "mk" / "agents.mk").read_text(encoding="utf-8")
        self.assertIn('\narms-combine:\n\t$(PY) evals/combine.py $(foreach f,$(SAVES),"$(f)")', agents)
        self.assertIn("`arms-combine`", (KIT / "mk" / "README.md").read_text(encoding="utf-8"))
        unowned = (KIT / "UNOWNED.md").read_text(encoding="utf-8")
        row = next((line for line in (KIT / "INDEX.md").read_text(encoding="utf-8").splitlines()
                    if line.startswith("| `evals/combine.py` |")), "")    # INDEX.md names its page once a page quotes it
        self.assertTrue("| `evals/combine.py` | **10.5** |" in unowned or row.split(" | ")[2:3] not in ([], ["-"]),
                        "no UNOWNED.md row for evals/combine.py")


if __name__ == "__main__":
    unittest.main()
