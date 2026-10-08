"""Offline tests for the DocuMind Desk route set, its eval and its probe (workshop lessons 5.6 and 10.4).

Run with ``python -m unittest discover -s evals/tests -p test_route_eval.py`` from deploy/ (``make desk-check``
runs it). Stdlib only, except the one probe test that validates the request configs against google-genai's own
types: it skips when the library is missing, and DOCUMIND_REQUIRE_LIBS=1 turns that skip into a failure.
"""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

EVALS = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_under_test", EVALS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


route_eval = load("route_eval")
build_routes = load("build_routes")
route_probe = load("route_probe")
ROWS = route_eval.load_rows()


def a_row(**over):
    row = {"id": "hb-001", "of": None, "group": "hb-001", "tenant": "acme", "identity": "acme_employee",
           "question": "How many days of earned leave can I carry forward?", "prev_question": None,
           "prev_route": None, "expected_route": "handbook", "acceptable_routes": ["handbook"],
           "expected_doc_types": ["policy"], "expected_outcome": "answer", "case_type": None,
           "must_escalate": False, "language": "en", "expect_model_calls_max": None, "must_contain": ["30"],
           "must_not_contain": [], "source": "new", "split": "dev", "author": "person:writer-a", "note": ""}
    row.update(over)
    return row


class WilsonTest(unittest.TestCase):
    def test_lesson_10_6_figures_when_every_row_passes(self):
        # Lesson 10.4's figures: n / (n + 3.84). 20 a class, 73 the minimum for 95%, 75 a class, 100 pooled.
        for n, want in {20: 83.9, 73: 95.0, 75: 95.1, 100: 96.3}.items():
            lo, hi = route_eval.wilson(n, n)
            self.assertEqual(round(100 * lo, 1), want, n)
            self.assertAlmostEqual(lo, n / (n + 3.84), places=3)
            self.assertAlmostEqual(hi, 1.0)
        self.assertLess(route_eval.wilson(72, 72)[0], 0.95)
        self.assertEqual(route_eval.wilson_errors(), [])

    def test_no_rows_is_no_evidence(self):
        self.assertIsNone(route_eval.wilson(0, 0))
        self.assertEqual(route_eval.rate(0, 0), "0/0 (no rows)")

    def test_the_rate_names_its_denominator_and_interval(self):
        # 29/30, one miss in a 30-row desk: about 83% to 99%.
        self.assertEqual(route_eval.rate(29, 30), "29/30 = 96.7% [83.3%, 99.4%]")


class SchemaTest(unittest.TestCase):
    def test_a_good_row(self):
        self.assertEqual(route_eval.row_errors(a_row()), [])

    def test_bad_rows_say_why(self):
        cases = {
            "an address": a_row(note="ask you@example.com"),
            "an unknown identity": a_row(identity="you"),
            "an identity on another tenant": a_row(identity="zeta_employee"),
            "a route outside the five": a_row(expected_route="company_info", acceptable_routes=["company_info"]),
            "acceptable_routes without the expected route": a_row(acceptable_routes=["statute"]),
            "a case row without its type": a_row(expected_route="case", acceptable_routes=["case"],
                                                 expected_outcome="case", expected_doc_types=[]),
            "must_escalate off the case route": a_row(must_escalate=True),
            "an oos row that names doc types": a_row(expected_route="out_of_scope", acceptable_routes=["out_of_scope"],
                                                     expected_outcome="oos"),
            "a route and an outcome that cannot meet": a_row(expected_outcome="clarify"),
            "a missing field": {k: v for k, v in a_row().items() if k != "language"},
            "a pre-existing question on the test split": a_row(split="test", source="golden.jsonl:lk-03"),
        }
        for what, row in cases.items():
            self.assertTrue(route_eval.row_errors(row), what)

    def test_a_case_row(self):
        row = a_row(id="esc-posh-01", group="esc-posh-01", expected_route="case", acceptable_routes=["case"],
                    expected_doc_types=[], expected_outcome="case", case_type="posh", must_escalate=True,
                    expect_model_calls_max=0, must_contain=[], question="My manager keeps commenting on my looks.")
        self.assertEqual(route_eval.row_errors(row), [])


class SplitTest(unittest.TestCase):
    def test_a_group_on_both_sides_of_the_split_fails(self):
        rows = [a_row(), a_row(id="hb-002", question="Can I carry over leave?", split="test")]
        self.assertTrue(any("both sides of the split" in w for w in route_eval.set_errors(rows)))

    def test_an_identical_question_across_the_split_fails(self):
        # Two groups, the same question once normalised: case, punctuation and spacing do not hide it.
        rows = [a_row(), a_row(id="hb-002", group="hb-002", split="test",
                               question="how many days of earned leave can I  carry forward")]
        why = route_eval.set_errors(rows)
        self.assertTrue(any(w.startswith("cross-split pair") for w in why), why)

    def test_the_same_question_in_two_groups_fails_even_on_one_side(self):
        rows = [a_row(), a_row(id="hb-002", group="hb-002")]
        self.assertTrue(any("the same question in groups" in w for w in route_eval.set_errors(rows)))

    def test_normalise_keeps_devanagari_marks(self):
        self.assertEqual(route_eval.normalise("मुझे   मदद चाहिए!"), "मुझे मदद चाहिए")

    def test_a_zero_width_joiner_does_not_hide_a_duplicate(self):
        self.assertEqual(route_eval.normalise("मुझे शिक\u200dायत करनी है"), route_eval.normalise("मुझे शिकायत करनी है"))
        self.assertEqual(route_eval.normalise("क\u200cष"), route_eval.normalise("कष"))

    def test_a_follow_ups_first_turn_across_the_split_fails(self):
        rows = [a_row(), a_row(id="fu-001", group="fu-001", split="test", question="And after probation?",
                               prev_question="How many days of earned leave can I carry forward?",
                               prev_route="handbook")]
        self.assertTrue(any(w.startswith("cross-split pair") for w in route_eval.set_errors(rows)))

    def test_an_of_that_names_no_row_fails(self):
        why = route_eval.set_errors([a_row(of="zzz")])
        self.assertTrue(any("of zzz, which is not a row" in w for w in why), why)

    def test_the_selftest_prints_the_table_then_no_cross_split_pair(self):
        out = io.StringIO()
        with patch("sys.stdout", out):
            self.assertEqual(route_eval.selftest(), 0)
        text = out.getvalue()
        self.assertIn("handbook", text)
        self.assertTrue(text.rstrip().endswith("no cross-split pair"), text)


class RouteSetTest(unittest.TestCase):
    def test_the_committed_set_is_sound(self):
        self.assertEqual(route_eval.check_rows(ROWS), [])

    def test_207_dev_rows_from_three_sources(self):
        derived = [r for r in ROWS if r["source"] != "new"]
        self.assertEqual(len(derived), 207)
        self.assertEqual({r["split"] for r in derived}, {"dev"})
        count = {k: sum(r["source"].startswith(k) for r in derived) for k in ("golden", "paraphrases", "sft")}
        self.assertEqual(count, {"golden": 65, "paraphrases": 42, "sft": 100})

    def test_every_golden_row_has_a_label(self):
        golden = [json.loads(line) for line in (EVALS / "golden.jsonl").read_text(encoding="utf-8").splitlines()]
        ids = {r["id"] for r in ROWS}
        self.assertEqual([g["id"] for g in golden if g["id"] not in ids], [])

    def test_the_labelling_rule(self):
        # The labelling rule: lk-03 and pp-04 are handbook; a named Act is statute.
        by_id = {r["id"]: r for r in ROWS}
        self.assertEqual(by_id["lk-03"]["expected_route"], "handbook")
        self.assertEqual(by_id["pp-04"]["expected_route"], "handbook")
        self.assertEqual(build_routes.rule_route("Can I carry forward leave?"), "handbook")
        self.assertEqual(build_routes.rule_route("What is the overtime rate under the Code on Wages?"), "statute")
        self.assertEqual(build_routes.rule_route("Does our handbook match the OSH Code on leave?"), "two_parts")
        self.assertIsNone(build_routes.rule_route("What SAC code does the invoice quote?"))
        self.assertIsNone(build_routes.rule_route("What does Schedule I list?"))           # a numeral, not "I"
        self.assertIsNone(build_routes.rule_route("Does the ACME Code of Conduct allow gifts from vendors?"))
        # The rule's known blind spot: a statute question with no marker. Such a row needs RULE_EXCEPTIONS.
        self.assertEqual(build_routes.rule_route("We had a personal-data breach. By when must we tell the Board?"),
                         "handbook")

    def test_launch_scope(self):
        by_id = {r["id"]: r for r in ROWS}
        for rid in ("lk-10", "lk-11", "lk-12", "mm-03"):          # invoice, report, contract, town hall: no desk
            self.assertEqual(by_id[rid]["expected_route"], "out_of_scope", rid)
        for r in ROWS:                                           # globex runs single mode on statute
            if r["tenant"] == "globex":
                self.assertIn(r["expected_route"], ("statute", "case"), r["id"])

    def test_rewrite_outcomes_are_judged_on_the_corpus_not_the_passage(self):
        by_id = {r["id"]: r for r in ROWS}
        # Refusal twins the corpus answers elsewhere: the DPDP Schedule, IR Code s.74, Wages s.63, SS Code s.6(10).
        self.assertEqual(by_id["sft-150"]["expected_outcome"], "answer")
        self.assertEqual(by_id["sft-150"]["must_contain"], ["two hundred and fifty crore"])
        self.assertEqual(by_id["sft-227"]["must_contain"], ["sixty days"])
        for rid in ("sft-44", "sft-88", "sft-140"):
            self.assertEqual(by_id[rid]["expected_outcome"], "answer", rid)
        # The GEN filler's reply time is never a rule: the row refuses and must not quote it.
        for n in (153, 155, 157, 159, 209):
            self.assertEqual(by_id[f"sft-{n}"]["expected_outcome"], "grounded_refusal", n)
            self.assertEqual(by_id[f"sft-{n}"]["must_not_contain"], ["five working days"], n)

    def test_check_fails_on_a_refusal_twin_with_no_judged_outcome(self):
        judged = dict(build_routes.REWRITE_OUTCOMES)
        del judged[150]
        with patch.object(build_routes, "REWRITE_OUTCOMES", judged), patch("sys.stdout", io.StringIO()) as out:
            self.assertEqual(build_routes.main(["--check"]), 1)
        self.assertIn("SFT line 150: its outcome needs a judgement", out.getvalue())

    def test_check_finds_a_rewrites_figure_in_the_corpus(self):
        judged = {**build_routes.REWRITE_OUTCOMES, 150: ("answer", ["three hundred crore"], [], "")}
        with patch.object(build_routes, "REWRITE_OUTCOMES", judged), patch("sys.stdout", io.StringIO()) as out:
            self.assertEqual(build_routes.main(["--check"]), 1)
        self.assertIn("sft-150: must_contain 'three hundred crore' is not in acme's corpus", out.getvalue())

    def test_a_paraphrase_about_another_tenants_document_keeps_its_guard(self):
        pp34 = next(r for r in ROWS if r["id"] == "pp-34")             # zeta asks about ACME's MSA
        self.assertEqual((pp34["tenant"], pp34["must_not_contain"]), ("zeta", ["99.5"]))
        with patch.object(build_routes, "PARAPHRASE_GUARDS", {"pp-34": ["99.9"]}), \
                patch("sys.stdout", io.StringIO()) as out:              # zeta's own figure is no guard
            self.assertEqual(build_routes.main(["--check"]), 1)
        self.assertIn("pp-34: must_not_contain '99.9' must be another tenant's figure", out.getvalue())

    def test_model_drafts_say_so(self):
        for r in ROWS:
            if r["source"] != "new":
                self.assertTrue(r["author"].startswith("model-draft"), r["id"])

    def test_the_file_is_what_the_builder_builds(self):
        out = io.StringIO()
        with patch("sys.stdout", out):
            self.assertEqual(build_routes.main(["--check"]), 0, out.getvalue())

    def test_check_fails_on_a_golden_row_with_no_label(self):
        labels = dict(build_routes.LABELS)
        del labels["lk-06"]
        with patch.object(build_routes, "LABELS", labels), patch("sys.stdout", io.StringIO()) as out:
            self.assertEqual(build_routes.main(["--check"]), 1)
        self.assertIn("golden lk-06 has no route label", out.getvalue())

    def test_check_fails_on_a_label_the_rule_contradicts(self):
        labels = dict(build_routes.LABELS, **{"lk-03": ("statute", "answer", "")})
        with patch.object(build_routes, "LABELS", labels), patch("sys.stdout", io.StringIO()) as out:
            self.assertEqual(build_routes.main(["--check"]), 1)
        self.assertIn("lk-03: labelled statute, but the labelling rule says handbook", out.getvalue())

    def test_check_fails_on_a_rewrite_keyed_to_the_wrong_line(self):
        # SFT line 221 asks what a Tribunal may do about an unjustified dismissal; 222 asks when an award is
        # enforceable. The award rewrite filed under 221 shares no content word with it.
        rewrites = dict(build_routes.REWRITES)
        rewrites[221] = rewrites.pop(222)
        with patch.object(build_routes, "REWRITES", rewrites), patch("sys.stdout", io.StringIO()) as out:
            self.assertEqual(build_routes.main(["--check"]), 1)
        self.assertIn("SFT line 221: the rewrite shares no content word", out.getvalue())

    def test_check_validates_hand_written_rows(self):
        bad = a_row(id="hb-900", group="hb-900", question="Can I take leave on my birthday?", identity="you")
        lines = (EVALS / "routes.jsonl").read_text(encoding="utf-8") + json.dumps(bad) + "\n"
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "routes.jsonl")
            Path(path).write_text(lines, encoding="utf-8")
            with patch.object(build_routes, "ROUTES_FILE", path), patch("sys.stdout", io.StringIO()) as out:
                self.assertEqual(build_routes.main(["--check"]), 1)
        self.assertIn("hb-900: identity", out.getvalue())

    def _check_with(self, *extra):
        lines = (EVALS / "routes.jsonl").read_text(encoding="utf-8") + "".join(json.dumps(r) + "\n" for r in extra)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "routes.jsonl")
            Path(path).write_text(lines, encoding="utf-8")
            with patch.object(build_routes, "ROUTES_FILE", path), patch("sys.stdout", io.StringIO()) as out:
                return build_routes.main(["--check"]), out.getvalue()

    def test_hand_written_rows_obey_the_labelling_rule(self):
        breach = a_row(id="st-900", group="st-900", question="We had a personal-data breach. By when must we tell "
                       "the Board?", expected_route="statute", acceptable_routes=["statute"],
                       expected_doc_types=["statute", "guidance"], must_contain=[])
        code, out = self._check_with(breach)
        self.assertEqual(code, 1)
        self.assertIn("st-900: labelled statute, but the labelling rule says handbook", out)
        with patch.object(build_routes, "RULE_EXCEPTIONS", {"st-900": "names the Board, not the Act"}):
            code, out = self._check_with(breach)
        self.assertEqual(code, 0, out)

    def test_a_two_parts_question_passes_only_when_both_routes_are_acceptable(self):
        q = "Does our handbook's earned leave match what the OSH Code requires?"
        self.assertEqual(build_routes.rule_route(q), "two_parts")
        both = a_row(id="mi-900", group="mi-900", question=q, acceptable_routes=["handbook", "statute"],
                     expected_doc_types=["policy", "statute", "guidance"], must_contain=[])
        code, out = self._check_with(both)
        self.assertEqual(code, 0, out)
        code, out = self._check_with(dict(both, acceptable_routes=["handbook"]))
        self.assertEqual(code, 1)
        self.assertIn("mi-900: the labelling rule says two parts", out)


class ScoringTest(unittest.TestCase):
    def setUp(self):
        self.rows = [a_row(),
                     a_row(id="st-001", group="st-001", question="What is the overtime rate under the Code on Wages?",
                           expected_route="statute", acceptable_routes=["statute"],
                           expected_doc_types=["statute", "guidance"], must_contain=[]),
                     a_row(id="esc-001", group="esc-001", question="Mere manager mujhe pareshan karte hain.",
                           expected_route="case", acceptable_routes=["case"], expected_doc_types=[],
                           expected_outcome="case", case_type="posh", must_escalate=True, language="hinglish",
                           must_contain=[]),
                     a_row(id="den-001", group="den-001", identity="acme_leaver", question="What is my notice?",
                           expected_outcome="denied", must_contain=[])]
        self.classes = route_eval.classes_from_manifest()

    def test_confusion_escalation_language_authority_denial(self):
        preds = {"hb-001": {"id": "hb-001", "route": "handbook", "outcome": "answer", "answer": "Up to 30 days.",
                            "citations": [{"source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"}]},
                 "st-001": {"id": "st-001", "route": "handbook", "outcome": "answer", "answer": "Twice the rate.",
                            "citations": [{"source": "hr_policy_2026.md"}]},
                 "esc-001": {"id": "esc-001", "route": "case", "case_type": "posh", "outcome": "case"},
                 "den-001": {"id": "den-001", "route": "handbook", "outcome": "denied", "retrieve_calls": 0}}
        r = route_eval.score(self.rows, preds, self.classes)
        t = r["tally"]
        self.assertEqual(t["route"], [3, 4])
        self.assertEqual(r["confusion"]["statute"]["handbook"], 1)
        self.assertEqual(t["escalation"], [1, 1])
        self.assertEqual(t["escalation:posh"], [1, 1])
        self.assertEqual(t["language:hinglish"], [1, 1])
        self.assertEqual(t["authority"], [1, 2])               # the statute row cited the handbook: not its authority
        self.assertEqual(t["authority:statute"], [0, 1])
        self.assertEqual(t["correct"], [2, 2])                 # the answer rows; authority is scored apart
        self.assertEqual(t["denial"], [1, 1])
        out = io.StringIO()
        route_eval.report(r, "B", "dev", out=out)
        self.assertIn("top-1 route accuracy          3/4 = 75.0% [", out.getvalue())
        self.assertIn("statute -> handbook: 1/1 = 100.0% [", out.getvalue())

    def test_a_missing_row_is_a_miss_not_a_skip(self):
        r = route_eval.score(self.rows, {}, self.classes)
        self.assertEqual(r["tally"]["route"], [0, 4])
        self.assertEqual(r["tally"]["escalation"], [0, 1])
        self.assertEqual(r["confusion"]["case"]["other"], 1)

    def test_a_citation_of_another_tenants_document_fails_authority(self):
        by_id = {r["id"]: r for r in ROWS}
        rows = [by_id["lk-28"], by_id["rf-03"]]                         # globex: answer, grounded_refusal
        preds = {r["id"]: {"id": r["id"], "route": "statute", "outcome": r["expected_outcome"],
                           "citations": [{"source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/dpdp_act_2023.pdf"}]}
                 for r in rows}
        r = route_eval.score(rows, preds, self.classes)
        self.assertEqual(r["tally"]["authority"], [0, 2])
        self.assertEqual(r["tally"]["no_cross_tenant"], [0, 2])
        self.assertEqual(r["verdicts"][0]["citation_classes"], ["cross_tenant"])
        own = {"lk-28": {"id": "lk-28", "route": "statute", "outcome": "answer",
                         "citations": [{"source_uri": "gs://b/globex/dpdp_act_2023.pdf"}]}}
        self.assertEqual(route_eval.score(rows[:1], own, self.classes)["tally"]["authority"], [1, 1])

    def test_an_uncited_answer_fails_authority_and_an_uncited_refusal_is_not_counted(self):
        refusal = a_row(id="rf-901", group="rf-901", expected_outcome="grounded_refusal", must_contain=[])
        preds = {"hb-001": {"id": "hb-001", "route": "handbook", "outcome": "answer", "citations": []},
                 "rf-901": {"id": "rf-901", "route": "handbook", "outcome": "grounded_refusal", "citations": []}}
        t = route_eval.score([a_row(), refusal], preds, self.classes)["tally"]
        self.assertEqual(t["authority"], [0, 1])

    def test_a_route_only_run_does_not_measure_authority(self):
        r = route_eval.score(self.rows, {"hb-001": {"id": "hb-001", "route": "handbook"}}, self.classes)
        self.assertNotIn("authority", r["tally"])
        out = io.StringIO()
        route_eval.report(r, None, "dev", out=out)
        self.assertIn("authority_rate                not measured", out.getvalue())

    def test_a_missing_row_lowers_outcome_accuracy_and_model_calls(self):
        rows = [a_row(expect_model_calls_max=2), a_row(id="hb-002", group="hb-002", question="Another question?",
                                                       expect_model_calls_max=2)]
        preds = {"hb-001": {"id": "hb-001", "route": "handbook", "outcome": "answer", "model_calls": 1}}
        t = route_eval.score(rows, preds, self.classes)["tally"]
        self.assertEqual(t["outcome"], [1, 2])
        self.assertEqual(t["model_calls"], [1, 2])

    def test_a_missing_row_fails_no_leak_no_citation_and_no_cross_tenant(self):
        by_id = {r["id"]: r for r in ROWS}
        rows = [by_id["lk-06"], by_id["lk-10"], by_id["sft-153"]]       # answer; out_of_scope; GEN SLA refusal
        self.assertEqual(by_id["lk-10"]["expected_doc_types"], [])
        self.assertEqual(by_id["sft-153"]["must_not_contain"], ["five working days"])
        preds = {"lk-06": {"id": "lk-06", "route": "handbook", "outcome": "answer", "answer": "An answer.",
                           "citations": [{"source_uri": "gs://b/acme/hr_policy_2026.md"}]}}
        r = route_eval.score(rows, preds, self.classes)
        self.assertEqual(r["tally"]["no_citation"], [0, 1])            # lk-10 is not in the run
        self.assertEqual(r["tally"]["no_leak"], [0, 1])                # sft-153 is not in the run
        self.assertTrue(r["verdicts"][2]["leak"])
        r = route_eval.score([by_id["lk-06"], by_id["lk-28"]], preds, self.classes)
        self.assertEqual(r["tally"]["no_cross_tenant"], [1, 2])        # lk-28, an answer row not run: never a pass

    def test_a_citation_that_names_no_tenant_is_unresolved(self):
        by_id = {r["id"]: r for r in ROWS}
        for ref in ({"source": "dpdp_act_2023.pdf"}, {"source_uri": "gs://b/dpdp_act_2023.pdf"}):
            preds = {"lk-28": {"id": "lk-28", "route": "statute", "outcome": "answer", "citations": [ref]}}
            r = route_eval.score([by_id["lk-28"]], preds, self.classes)
            self.assertEqual(r["tally"]["authority"], [0, 1], ref)
            self.assertEqual(r["verdicts"][0]["citation_classes"], ["unresolved"], ref)

    def test_a_null_model_calls_is_refused_when_the_run_is_read(self):
        with tempfile.TemporaryDirectory() as d:
            run = os.path.join(d, "run.jsonl")
            Path(run).write_text(json.dumps({"id": "hb-001", "route": "handbook", "model_calls": None}) + "\n")
            with self.assertRaises(SystemExit) as e:
                route_eval.load_predictions(run, {"hb-001"})
        self.assertIn("model_calls is a whole number", str(e.exception))

    def test_an_out_of_scope_row_that_cites_fails(self):
        oos = a_row(id="oos-001", group="oos-001", question="What is invoice 0412's total?",
                    expected_route="out_of_scope", acceptable_routes=["out_of_scope"], expected_doc_types=[],
                    expected_outcome="oos", must_contain=[])
        preds = {"oos-001": {"id": "oos-001", "route": "out_of_scope", "outcome": "oos",
                             "citations": [{"source_uri": "gs://b/acme/inv_2026_0412.md"}]}}
        self.assertEqual(route_eval.score([oos], preds, self.classes)["tally"]["no_citation"], [0, 1])

    def test_every_off_diagonal_cell_prints_its_rate_zero_included(self):
        preds = {r["id"]: {"id": r["id"], "route": r["expected_route"]} for r in self.rows}
        out = io.StringIO()
        route_eval.report(route_eval.score(self.rows, preds, self.classes), "B", "dev", out=out)
        self.assertIn("handbook -> statute: 0/2 = 0.0% [", out.getvalue())
        self.assertIn("handbook -> other: 0/2 = 0.0% [", out.getvalue())

    def test_a_denial_that_retrieved_fails(self):
        preds = {"den-001": {"id": "den-001", "route": "handbook", "outcome": "denied", "retrieve_calls": 1}}
        self.assertEqual(route_eval.score(self.rows, preds, self.classes)["tally"]["denial"], [0, 1])

    def test_classes_by_the_manifest_and_the_media_parent_rule(self):
        c = self.classes
        self.assertEqual(c[("acme", "hr_policy_2026.md")], "policy")
        self.assertEqual(c[("acme", "labour_codes_compliance_handbook.pdf")], "guidance")
        self.assertEqual(c[("acme", "annual_report_2026_fig3.png")], "report")
        self.assertEqual(c[("acme", "inv_2026_0412.png")], "invoice")
        self.assertEqual(c[("acme", "payment_of_bonus_act_1965_p30.png")], "statute")
        self.assertEqual(c[("acme", "townhall_2026_q1.mp4")], "transcript")
        self.assertEqual(c[("acme", "townhall_2026_q1.md")], "transcript")
        self.assertNotIn(("acme", "whiteboard_arch.png"), c)

    def test_the_classes_and_the_media_rule_are_the_registrys(self):
        # route_eval repeats shared/doc_types.py's class list and media parent rule so it needs no import from the
        # services; this keeps the two equal.
        spec = importlib.util.spec_from_file_location("doc_types_under_test", EVALS.parent / "shared" / "doc_types.py")
        doc_types = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(doc_types)
        self.assertEqual(route_eval.CLASSES, doc_types.CLASSES)
        registry = {tuple(name.split("/", 1)): e["doc_type"] for name, e in doc_types.registry_from_manifest().items()}
        self.assertEqual(self.classes, registry)

    def test_a_registry_export_wins_and_unknown_fails_authority(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "doc_types.json")
            Path(path).write_text(json.dumps({"acme": [{"name": "hr_policy_2026.md", "doc_type": "unknown"}]}))
            classes = route_eval.classes_from_registry(path)
        preds = {"hb-001": {"id": "hb-001", "route": "handbook",
                            "citations": [{"source_uri": "gs://b/acme/hr_policy_2026.md"}]}}
        # hb-001's citation is "unknown"; st-001, an answer row the run does not carry, fails too.
        self.assertEqual(route_eval.score(self.rows, preds, classes)["tally"]["authority"], [0, 2])

    def test_a_registry_export_names_objects_as_the_bucket_does(self):
        # The registry's own shape: the name is the object name, "<tenant>/<basename>".
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "doc_types.json")
            Path(path).write_text(json.dumps({"acme": [{"name": "acme/hr_policy_2026.md", "doc_type": "policy"}],
                                              "globex": {"globex/dpdp_act_2023.pdf": "statute"}}))
            classes = route_eval.classes_from_registry(path)
            self.assertEqual(classes, {("acme", "hr_policy_2026.md"): "policy",
                                       ("globex", "dpdp_act_2023.pdf"): "statute"})
            Path(path).write_text(json.dumps({"acme": [{"name": "globex/dpdp_act_2023.pdf", "doc_type": "statute"}]}))
            with self.assertRaises(SystemExit):
                route_eval.classes_from_registry(path)
        lk06 = next(r for r in ROWS if r["id"] == "lk-06")
        preds = {"lk-06": {"id": "lk-06", "route": "handbook", "outcome": "answer",
                           "citations": [{"source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"}]}}
        r = route_eval.score([lk06], preds, classes)
        self.assertEqual(r["tally"]["authority"], [1, 1])
        self.assertEqual(r["verdicts"][0]["citation_classes"], ["policy"])

    def test_arms(self):
        self.assertEqual(route_eval.run_arm({"a": {"arm": "C"}}, None), "C")
        self.assertEqual(route_eval.run_arm({"a": {}}, "Astar"), "Astar")
        with self.assertRaises(SystemExit):
            route_eval.run_arm({"a": {"arm": "B"}, "b": {"arm": "C"}}, None)
        with self.assertRaises(SystemExit):
            route_eval.run_arm({"a": {"arm": "B"}}, "C")

    def test_main_scores_a_run(self):
        with tempfile.TemporaryDirectory() as d:
            run, rep = os.path.join(d, "run.jsonl"), os.path.join(d, "report.json")
            Path(run).write_text("".join(json.dumps({"id": r["id"], "route": r["expected_route"], "arm": "B"}) + "\n"
                                         for r in ROWS if r["split"] == "dev"))
            out = io.StringIO()
            with patch("sys.stdout", out):
                self.assertEqual(route_eval.main(["--predictions", run, "--split", "dev", "--report", rep]), 0)
            dev = [r for r in ROWS if r["split"] == "dev"]
            self.assertIn(f"top-1 route accuracy          {len(dev)}/{len(dev)} = 100.0%", out.getvalue())
            self.assertIn("arm B (the routed Desk)", out.getvalue())
            self.assertEqual(json.loads(Path(rep).read_text())["arm"], "B")

    def test_identity_resolves_at_run_time(self):
        self.assertEqual(route_eval.identity_account("acme_leaver", "documind-ai-YOUR-ID"),
                         "documind-evalleaver-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com")


class ProbeTest(unittest.TestCase):
    def test_selftest(self):
        with patch("sys.stdout", io.StringIO()):
            self.assertEqual(route_probe.selftest(), 0)

    def test_avg_logprobs_alone_is_not_logprobs(self):
        # Every candidate carries avg_logprobs; the acceptance rule needs two top candidates at a step.
        avg_only = route_probe._resp(30, None, logprobs="avg")
        self.assertEqual(avg_only.candidates[0].logprobs_result, None)
        self.assertFalse(route_probe._read_logprobs(avg_only)[0])
        self.assertFalse(route_probe._read_logprobs(route_probe._resp(30, None, logprobs="chosen"))[0])
        self.assertTrue(route_probe._read_logprobs(route_probe._resp(30, None, logprobs="top2"))[0])

    def test_the_probe_asks_kit_questions_only(self):
        by_id = {r["id"]: r["question"] for r in ROWS}
        self.assertEqual(route_probe.probe_questions(), [by_id[i] for i in route_probe.PROBE_ROWS])

    def test_the_configs_are_valid_google_genai_configs(self):
        try:
            from google.genai import types
        except ImportError:
            if os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1":
                raise
            self.skipTest("google-genai is not installed in this interpreter")
        for fact, model, config, _ in route_probe.requests(route_probe.probe_questions()):
            c = types.GenerateContentConfig.model_validate(copy.deepcopy(config))
            if model == route_probe.L1_MODEL:
                self.assertEqual(c.thinking_config.thinking_budget, 0, fact)
            else:
                self.assertEqual(c.thinking_config.thinking_level, types.ThinkingLevel.MINIMAL)


if __name__ == "__main__":
    unittest.main()
