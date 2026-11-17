"""Offline tests for the judge set (workshop lesson 4.5): judge.py --save-rows and --no-enrich against a stand-in
Vertex AI Evaluation service, build_judge_set.py's freeze, emit and check round trip, judge_agree.py on the same files,
and the three make targets.

Run with ``python -m unittest discover -s evals/tests -p test_judge_rows.py`` from deploy/. Nothing reaches Google:
vertexai is stood in by modules that rate each row by a fixed rule (stand_in()), the store is never read
(--no-enrich), and the rows are reused from a file. judge.py needs pandas, which CI's shared interpreter installs;
where it is missing those tests skip, and DOCUMIND_REQUIRE_LIBS=1 turns the skip into a failure.

The files under judge_fixtures/ are synthetic, made for these tests and for nothing else: capture.ndjson is a made-up
--save-rows capture of twelve rows, judge_set.json what --freeze --rows 9 makes of it, ratings.ndjson the stand-in's
ratings of that set through judge.py's own path, and labels.FX1.csv and labels.FX2.csv two made-up readers' sheets.
The two JSON Lines files are named .ndjson, the format's other name, so that lesson B.1's count of the kit's .jsonl
datasets stays a count of datasets; the scripts read the lines, whatever the name.
"""
import contextlib
import csv
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import warnings

EVALS = Path(__file__).resolve().parents[1]
KIT = EVALS.parent
FIX = Path(__file__).resolve().parent / "judge_fixtures"
sys.path.insert(0, str(EVALS))
import agreement as ag  # noqa: E402
import build_judge_set as bjs  # noqa: E402
import judge  # noqa: E402
import judge_agree  # noqa: E402

STAMP = "20261008-0000"                     # the stand-in runs' time, fixed so their output is byte-stable
NUMBER = "9" * 12                           # a made-up project number, built at run time: this file must name none
CITE = re.compile(r"\[\d+(?:\s*,\s*\d+)*\]")
NUM = re.compile(r"\d+(?:,\d+)*(?:\.\d+)?")


def figures(text: str) -> set:
    return {n.replace(",", "") for n in NUM.findall(CITE.sub("", text or ""))}


def rule(context: str, response: str, reference: str):
    """The stand-in judge: groundedness 0 when the answer holds a figure its context does not, else 1; the second
    metric 5, 3 or 1 as all, some or none of the reference's words are in the answer, and for a row with no
    reference (one the corpus cannot answer) 5 when the answer holds no figure, else 2. A crude rule, so it misses
    an unsupported sentence without a figure, as a real judge can."""
    loose = sorted(figures(response) - figures(context))
    grounded = (0.0, f"stand-in: {', '.join(loose)} not in the context") if loose else (1.0, "stand-in: every figure is in the context")
    want = (reference or "").split()
    if not want:
        follow = (2.0, "stand-in: a figure for a question the context cannot answer") if figures(response) else \
                 (5.0, "stand-in: it says what the context does not hold")
    else:
        hit = sum(w in response for w in want)
        follow = (5.0 if hit == len(want) else 3.0 if hit else 1.0, f"stand-in: {hit} of {len(want)} reference words in the answer")
    return grounded, follow


def stand_in(seen: dict | None = None) -> dict:
    """vertexai and vertexai.evaluation, as far as judge.py uses them. EvalTask rates each row by rule() and returns
    the dataset with the metric columns the real metrics_table carries: <metric>/score and <metric>/explanation."""
    import pandas as pd
    seen = {} if seen is None else seen
    vx, ev = types.ModuleType("vertexai"), types.ModuleType("vertexai.evaluation")
    vx.init = lambda **kw: seen.setdefault("init", kw)

    class _Template:
        def __init__(self, name):
            self.metric_prompt_template = f"{name}: the stand-in's template"

    class Pointwise:
        GROUNDEDNESS = _Template("groundedness")
        INSTRUCTION_FOLLOWING = _Template("instruction_following")

    class MetricPromptTemplateExamples:
        @staticmethod
        def get_prompt_template(name):
            return f"{name}: the stand-in's template"
    MetricPromptTemplateExamples.Pointwise = Pointwise

    class PairwiseMetric:
        def __init__(self, metric, metric_prompt_template):
            self.metric_name = metric

    class EvalTask:
        def __init__(self, dataset, metrics, experiment=None, **kw):
            self.df, self.metrics = dataset, metrics
            seen["dataset"] = dataset.copy()

        def evaluate(self, experiment_run_name=None):
            seen["run"] = experiment_run_name
            table = self.df.copy()
            rated = [rule(r["context"], r["response"], r["reference"]) for _, r in self.df.iterrows()]
            for name, k in (("groundedness", 0), ("instruction_following", 1)):
                table[f"{name}/score"] = [x[k][0] for x in rated]
                table[f"{name}/explanation"] = [x[k][1] for x in rated]
            if any(isinstance(m, PairwiseMetric) for m in self.metrics):
                table["pairwise_question_answering_quality/pairwise_choice"] = "TIE"
            summary = {"row_count": float(len(table))}
            for name in ("groundedness", "instruction_following"):
                summary[f"{name}/mean"] = float(table[f"{name}/score"].mean())
            return types.SimpleNamespace(summary_metrics=summary, metrics_table=pd.DataFrame(table))

    ev.EvalTask, ev.MetricPromptTemplateExamples, ev.PairwiseMetric = EvalTask, MetricPromptTemplateExamples, PairwiseMetric
    vx.evaluation = ev
    return {"vertexai": vx, "vertexai.evaluation": ev}


def no_store(project, ids):
    raise AssertionError("the store was read")


def run_judge(args: list, seen: dict | None = None, store=None) -> tuple[int, str]:
    """judge.py's main() over the stand-in, at STAMP; `store` stands in for the Firestore read, which by default
    fails the test if anything calls it."""
    out = io.StringIO()
    fetch = store if store is not None else no_store
    with patch.dict(sys.modules, stand_in(seen)), patch.object(sys, "argv", ["judge.py", *args]), \
            patch.object(judge.time, "strftime", lambda fmt, *a: STAMP), patch.object(judge, "chunk_texts", fetch), \
            contextlib.redirect_stdout(out):
        code = judge.main()
    return code, out.getvalue()


def frozen_args(set_path, rows_path, *more) -> list:
    """make judge-frozen's call, on a copy of a frozen set."""
    return ["--api-url", f"frozen:{set_path}", "--project", "documind-ai-YOUR-ID", "--reuse", str(set_path), "--no-enrich",
            "--label", "fixture", "--save-rows", str(rows_path), *more]


def need_pandas(test):
    try:
        import pandas  # noqa: F401
    except ImportError:
        if os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1":
            raise
        test.skipTest("pandas is not installed in this interpreter (CI's shared interpreter has it)")


def jsonl(path) -> list[dict]:
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def quiet(fn, *a, **kw):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = fn(*a, **kw)
    return code, out.getvalue()


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="judge_rows_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.frozen = bjs.load_set(str(FIX / "judge_set.json"))

    def fill(self, sheet: Path, labels: dict, reader=None, bom=False, crlf=False, upper=False):
        """Write labels {id: (groundedness, answers)} into an emitted sheet, as a person would."""
        with open(sheet, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            g, q = labels.get(r["id"], ("", ""))
            r["groundedness"], r["answers_the_question"] = (g.upper(), q.capitalize()) if upper else (g, q)
            if reader:
                r["reader"] = reader
        text = io.StringIO()
        w = csv.DictWriter(text, fieldnames=bjs.SHEET_FIELDS, lineterminator="\r\n" if crlf else "\n")
        w.writeheader()
        w.writerows(rows)
        sheet.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.getvalue().encode("utf-8"))


# ----------------------------------------------------------------------------- judge.py --save-rows, --no-enrich
class SaveRowsTest(Tmp):
    def setUp(self):
        super().setUp()
        need_pandas(self)
        warnings.simplefilter("ignore", ResourceWarning)    # judge.py's --reuse read leaves its file to the collector
        self.set = self.tmp / "judge_set.json"
        shutil.copy2(FIX / "judge_set.json", self.set)

    def test_every_rated_row_is_written_with_each_metrics_score_and_explanation(self):
        seen = {}
        code, out = run_judge(frozen_args(self.set, self.tmp / "rows.jsonl"), seen)
        self.assertEqual(code, 0, out)
        lines = jsonl(self.tmp / "rows.jsonl")
        self.assertEqual([x["id"] for x in lines], [r["id"] for r in self.frozen])
        for x, r in zip(lines, self.frozen):
            self.assertEqual({k: x[k] for k in r}, r)                        # the row as the judge read it, unchanged
            self.assertRegex(x["run"], r"^api-fixture-20261008-0000-t[0-9a-f]{6}$")
            self.assertEqual(sorted(x["ratings"]), ["groundedness", "instruction_following"])
            for m in x["ratings"].values():
                self.assertEqual(sorted(m), ["explanation", "score"])
                self.assertIsInstance(m["score"], float)
                self.assertTrue(m["explanation"].startswith("stand-in: "))
            self.assertIn(x["ratings"]["groundedness"]["score"], (0.0, 1.0))
        self.assertEqual(seen["run"], lines[0]["run"])
        self.assertIn(f"  per-row ratings: {len(lines)} rows written to {self.tmp / 'rows.jsonl'}\n", out)
        prompts = list(seen["dataset"]["prompt"])
        self.assertTrue(all(r["context"] in p for r, p in zip(self.frozen, prompts) if r["context"]))

    def test_the_fixture_ratings_are_this_code_paths_output(self):
        code, out = run_judge(frozen_args(self.set, self.tmp / "rows.jsonl"))
        self.assertEqual(code, 0, out)
        self.assertEqual((self.tmp / "rows.jsonl").read_bytes(), (FIX / "ratings.ndjson").read_bytes())

    def test_no_enrich_reads_no_store_and_says_so(self):
        code, out = run_judge(frozen_args(self.set, self.tmp / "rows.jsonl"))       # the store read would raise
        self.assertEqual(code, 0, out)
        self.assertIn("  context: as each row holds it (--no-enrich: no store read)\n", out)
        self.assertNotIn("cited chunks read in full", out)
        asked = []
        args = [a for a in frozen_args(self.set, self.tmp / "rows.jsonl") if a != "--no-enrich"]
        code, out = run_judge(args, store=lambda project, ids: asked.append(ids) or {})
        self.assertEqual(code, 0, out)
        self.assertEqual(len(asked), 1)                                               # without it, the store is read
        self.assertIn(" cited chunks read in full from the store - the judge reads the quotes only\n", out)

    def test_the_frozen_rows_are_kept_and_never_offered_for_deletion(self):
        # make judge-frozen reuses the set people labelled, evals/judge_set.json: judge.py says the rows are kept and
        # names another --reuse file to collect afresh, never "delete it" (lesson 4.5's review, 13 October 2026).
        before = self.set.read_bytes()
        code, out = run_judge(frozen_args(self.set, self.tmp / "rows.jsonl"))
        self.assertEqual(code, 0, out)
        self.assertIn(f"  {len(self.frozen)} rows reused from {self.set} (under make judge-frozen these are the frozen "
                      "rows, kept; to collect afresh, name another --reuse file)\n", out)
        self.assertNotIn("delete", out.lower())
        self.assertEqual(self.set.read_bytes(), before)                     # read, never written

    def test_without_save_rows_nothing_is_written_and_nothing_else_changes(self):
        _, with_rows = run_judge(frozen_args(self.set, self.tmp / "rows.jsonl"))
        args = frozen_args(self.set, self.tmp / "none.jsonl")
        _, without = run_judge(args[:args.index("--save-rows")])
        self.assertFalse((self.tmp / "none.jsonl").exists())
        norm = lambda s: re.sub(r" in \d+s ", " in Ns ", s)  # noqa: E731
        self.assertEqual([x for x in norm(with_rows).splitlines() if not x.startswith("  per-row ratings:")],
                         norm(without).splitlines())
        self.assertNotIn("per-row ratings", without)

    def test_a_missing_score_is_null_and_columns_are_found_by_suffix(self):
        import pandas as pd
        table = pd.DataFrame({"id": ["a", "b"], "shape": ["lookup", "refusal"],
                              "pointwise/groundedness/score": [1.0, float("nan")],
                              "pointwise/groundedness/explanation": ["fine", None],
                              "instruction_following/score": [4, 2],
                              "pairwise_question_answering_quality/pairwise_choice": ["CANDIDATE", "BASELINE"]})
        judged = [{"id": "a", "question": "q?", "response": "r", "context": "c"}, {"id": "b", "question": "q2?"}]
        n = judge.write_ratings(str(self.tmp / "sub" / "rows.jsonl"), table, judged, "api-x-t000000")
        lines = jsonl(self.tmp / "sub" / "rows.jsonl")
        self.assertEqual(n, 2)
        self.assertEqual(lines[0], {"id": "a", "question": "q?", "response": "r", "context": "c", "run": "api-x-t000000",
                                    "ratings": {"groundedness": {"score": 1.0, "explanation": "fine"},
                                                "instruction_following": {"score": 4.0},
                                                "pairwise_question_answering_quality": {"choice": "CANDIDATE"}}})
        self.assertEqual(lines[1]["ratings"]["groundedness"], {"score": None, "explanation": None})
        table = table.drop(columns=["id"])                                              # no id column: by position
        judge.write_ratings(str(self.tmp / "rows2.jsonl"), table, judged, "r")
        self.assertEqual([x["id"] for x in jsonl(self.tmp / "rows2.jsonl")], ["a", "b"])

    def test_a_file_that_cannot_be_written_never_loses_the_run(self):
        (self.tmp / "taken").mkdir()
        code, out = run_judge(frozen_args(self.set, self.tmp / "taken"))
        self.assertEqual(code, 0, out)
        self.assertIn("  per-row ratings: not written - ", out)
        self.assertIn("  Experiments run documind-eval/api-fixture-20261008-0000-t", out)

    def test_a_run_whose_requests_all_failed_is_no_verdict(self):
        nan = float("nan")                  # what the service leaves in a cell whose request failed (23 October 2026)
        with patch(f"{__name__}.rule", lambda context, response, reference: ((nan, "error"), (nan, "error"))):
            code, out = run_judge(frozen_args(self.set, self.tmp / "rows.jsonl"))
        self.assertEqual(code, 1, out)
        self.assertIn(f"  the judge rated nothing: all {2 * len(self.frozen)} requests to the Evaluation service failed", out)
        self.assertNotIn("still decides", out)

    def test_a_run_with_some_requests_failed_says_how_many(self):
        nan, real = float("nan"), rule
        with patch(f"{__name__}.rule", lambda context, response, reference: ((nan, "error"), real(context, response, reference)[1])):
            code, out = run_judge(frozen_args(self.set, self.tmp / "rows.jsonl"))
        self.assertEqual(code, 0, out)
        n = len(self.frozen)
        self.assertIn(f"  the judge rated {n} of {2 * n}: the means leave out the {n} requests that failed (above)\n", out)

    def test_no_vertex_rates_nothing_and_says_so(self):
        code, out = run_judge(frozen_args(self.set, self.tmp / "rows.jsonl", "--no-vertex"))
        self.assertEqual(code, 0, out)
        self.assertIn("  per-row ratings: none - --no-vertex rates nothing\n", out)
        self.assertFalse((self.tmp / "rows.jsonl").exists())

    def test_a_pairwise_run_saves_each_pairs_choice(self):
        base = self.tmp / "base.json"
        shutil.copy2(self.set, base)
        cand = json.loads(self.set.read_text(encoding="utf-8"))

        def ask(api_url, question, tenant, email, token, retries=1):           # the candidate, answering from the set
            r = next(x for x in cand if x["question"] == question)
            return 200, {"answer": r["response"], "citations": [], "answerable": True, "model": "fixture-model"}, 5
        with patch.object(judge, "load_golden", lambda: cand), patch.object(judge, "ask", ask):
            code, out = run_judge(frozen_args(base, self.tmp / "rows.jsonl", "--api-b", "https://candidate---fixture"))
        self.assertEqual(code, 0, out)
        lines = jsonl(self.tmp / "rows.jsonl")
        self.assertEqual({x["ratings"]["pairwise_question_answering_quality"]["choice"] for x in lines}, {"TIE"})


# ----------------------------------------------------------------------------- build_judge_set.py --freeze
class FreezeTest(Tmp):
    def freeze(self, *captures, rows=9, out=None, force=False):
        out = out or self.tmp / "judge_set.json"
        args = ["--freeze", *map(str, captures), "--rows", str(rows), "--set", str(out)] + (["--force"] if force else [])
        code, text = quiet(bjs.main, args)
        return code, text, out

    def test_the_fixture_set_is_what_freeze_makes_of_the_capture(self):
        code, text, out = self.freeze(FIX / "capture.ndjson")
        self.assertEqual(code, 0, text)
        self.assertEqual(out.read_bytes(), (FIX / "judge_set.json").read_bytes())
        code, again, _ = self.freeze(FIX / "capture.ndjson", out=self.tmp / "again.json")
        self.assertEqual(code, 0)
        self.assertEqual((self.tmp / "again.json").read_bytes(), out.read_bytes())   # the same capture, the same set

    def test_a_third_fail_and_groundedness_is_made_up_with_constructed_rows(self):
        capture = {x["id"]: x for x in bjs.read_capture(str(FIX / "capture.ndjson"))}
        natural = [r for r in self.frozen if not r["constructed"] and r["computed"] != "pass"]
        built = [r for r in self.frozen if r["constructed"]]
        self.assertEqual(len(self.frozen), 9)
        self.assertEqual(sorted(r["computed"] for r in natural),
                         sorted([bjs.REFUSED, bjs.SHOULD_REFUSE, "answered without ['60 days', '30']"]))
        self.assertEqual(len(built), 3 - 1)          # a third is 3; the row answering what it should refuse counts once
        for r in built:
            src = capture[r["id"]]                                                  # the question's own id
            phrase = next(p for s, p in bjs.ADDED if r["added"].startswith(s))
            self.assertFalse(bjs.contains(src["context"] + src["response"], phrase))
            self.assertEqual(r["response"].replace(" " + r["added"], "", 1), src["response"])
            self.assertTrue(r["added"].endswith("[1]."))                             # cited, as if its source said it
            self.assertEqual(r["computed"], "pass")                                  # the gate's rules cannot see it
        self.assertEqual(len({r["id"] for r in self.frozen}), 9)                    # one row per question
        self.assertTrue({"refusal", "isolation", "version"} <= {r["shape"] for r in self.frozen})

    def test_the_set_carries_no_judge_score_and_ignores_the_ratings(self):
        self.assertFalse(any({"ratings", "run"} & set(r) for r in self.frozen))
        flipped = self.tmp / "flipped.jsonl"
        lines = bjs.read_capture(str(FIX / "capture.ndjson"))
        for x in lines:
            for m in x["ratings"].values():
                m["score"] = 6 - m["score"] if m["score"] > 1 else 1 - m["score"]
        flipped.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        code, text, out = self.freeze(flipped)
        self.assertEqual(code, 0, text)
        self.assertEqual(out.read_bytes(), (FIX / "judge_set.json").read_bytes())

    def test_one_row_per_question_across_arms(self):
        cand = self.tmp / "cand.jsonl"
        lines = bjs.read_capture(str(FIX / "capture.ndjson"))
        for x in lines:
            if x["answerable"]:
                x["answerable_said"], x["response"] = False, "The documents do not say."      # a weaker candidate
        cand.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        code, text, out = self.freeze(FIX / "capture.ndjson", f"flash-lite={cand}", rows=12)
        self.assertEqual(code, 0, text)
        rows = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(len({r["id"] for r in rows}), len(rows))
        self.assertEqual({r["arm"] for r in rows}, {"live", "flash-lite"})
        self.assertIn("(flash-lite): 12 rows rated", text)

    def test_a_set_is_never_replaced_without_force(self):
        code, _, out = self.freeze(FIX / "capture.ndjson")
        before = out.read_bytes()
        code, text, _ = self.freeze(FIX / "capture.ndjson", rows=5)
        self.assertEqual(code, 2)
        self.assertIn("exists", text)
        self.assertEqual(out.read_bytes(), before)
        code, text, _ = self.freeze(FIX / "capture.ndjson", rows=5, force=True)
        self.assertEqual((code, len(json.loads(out.read_text(encoding="utf-8")))), (0, 5))

    def test_a_tuned_endpoint_is_written_as_an_endpoint_and_a_lane_url_is_refused(self):
        lines = bjs.read_capture(str(FIX / "capture.ndjson"))
        for x in lines:
            x["model"] = f"projects/{NUMBER}/locations/us-central1/endpoints/42"
        path = self.tmp / "tuned.jsonl"
        path.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        code, text, out = self.freeze(path)
        self.assertEqual(code, 0, text)
        self.assertEqual({r["model"] for r in json.loads(out.read_text(encoding="utf-8"))}, {"an endpoint"})
        for x in lines:                                    # every answer names the lane, so whichever is picked does
            x["response"] += f" See https://documind-api-{NUMBER}.asia-south1.run.app for more."
        path.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        code, text, out2 = self.freeze(path, out=self.tmp / "refused.json")
        self.assertEqual(code, 2)
        self.assertIn("a project number in a Cloud Run URL", text)
        self.assertFalse(out2.exists())

    def test_a_rating_of_a_frozen_set_is_not_a_capture(self):
        code, text, out = self.freeze(FIX / "ratings.ndjson")          # it holds constructed rows
        self.assertEqual(code, 2)
        self.assertIn("rates a frozen set", text)
        self.assertFalse(out.exists())

    def test_a_reuse_collection_is_refused_with_the_file_to_use(self):
        path = self.tmp / "judge45.json"
        path.write_text(json.dumps([{"id": "lk-01"}]), encoding="utf-8")
        code, text, out = self.freeze(path)
        self.assertEqual(code, 2)
        self.assertIn("freeze from the --save-rows file", text)
        self.assertFalse(out.exists())

    def test_the_computed_check_speaks_lives_words(self):
        row = {"answerable": True, "answerable_said": True, "must_contain": ["60 days"], "response": "Sixty days [1]."}
        self.assertEqual(bjs.computed(row), "pass")                                  # normalise(): sixty is 60
        self.assertEqual(bjs.computed({**row, "response": "160 days"}), "answered without ['60 days']")
        self.assertEqual(bjs.computed({**row, "answerable_said": False}), "refused")
        self.assertEqual(bjs.computed({**row, "must_not_contain": ["90 days"], "response": "60 days, once 90 days"}),
                         "answer contained '90 days'")
        self.assertEqual(bjs.computed({"answerable": False, "answerable_said": True, "response": "x"}), "answered, should refuse")
        self.assertEqual(bjs.computed({"answerable": False, "answerable_said": False, "response": "No."}), "pass")

    def test_the_added_sentence_follows_the_first_cited_sentence(self):
        self.assertEqual(bjs.add_sentence("It is 30 days [1]. Ask HR [2].", "S"), ("It is 30 days [1]. S [1]. Ask HR [2].", "S [1]."))
        self.assertEqual(bjs.add_sentence("It is 30 days [1, 2] in all", "S"), ("It is 30 days [1, 2] in all S [1, 2].", "S [1, 2]."))
        self.assertEqual(bjs.add_sentence("No citation here. ", "S"), ("No citation here. S.", "S."))


# ----------------------------------------------------------------------------- --emit, --check
class SheetTest(Tmp):
    def labels(self):
        """Every frozen row labelled yes and yes, except two."""
        out = {r["id"]: ("yes", "yes") for r in self.frozen}
        first, last = self.frozen[0]["id"], self.frozen[-1]["id"]
        out[first], out[last] = ("no", "yes"), ("yes", "no")
        return out

    def emit(self, path, reader="you"):
        return quiet(bjs.main, ["--emit", str(path), "--reader", reader, "--set", str(FIX / "judge_set.json")])

    def check(self, path):
        return quiet(bjs.main, ["--check", str(path), "--set", str(FIX / "judge_set.json")])

    def test_emit_fill_and_check_round_trip(self):
        sheet = self.tmp / "reports" / "judge_labels.csv"
        code, text = self.emit(sheet)
        self.assertEqual(code, 0, text)
        self.assertIn("groundedness: yes when every claim in the answer is supported by the context on its row", text)
        with open(sheet, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(tuple(rows[0]), bjs.SHEET_FIELDS)
        self.assertEqual([r["id"] for r in rows], [r["id"] for r in self.frozen])
        self.assertEqual([r["answer"] for r in rows], [r["response"] for r in self.frozen])
        self.assertTrue(all(r["groundedness"] == r["answers_the_question"] == "" for r in rows))
        self.assertFalse(any("constructed" in r or "computed" in r for r in rows))   # the sheet does not say
        code, text = self.check(sheet)
        self.assertEqual(code, 1)
        self.assertIn(f"{2 * len(self.frozen)} problem(s)", text)
        self.fill(sheet, self.labels())
        code, text = self.check(sheet)
        self.assertEqual(code, 0, text)
        self.assertIn(f"{len(self.frozen)} rows labelled by you - groundedness {len(self.frozen) - 1} yes, 1 no", text)
        reader, labels, _ = judge_agree.read_sheet(str(sheet), self.frozen)
        self.assertEqual(reader, "you")
        self.assertEqual(labels[self.frozen[0]["id"]], {"groundedness": False, "answers_the_question": True})

    def test_emit_never_overwrites_a_sheet(self):
        sheet = self.tmp / "s.csv"
        self.emit(sheet)
        self.fill(sheet, self.labels())
        before = sheet.read_bytes()
        code, text = self.emit(sheet)
        self.assertEqual(code, 2)
        self.assertIn("may hold labels", text)
        self.assertEqual(sheet.read_bytes(), before)
        self.assertEqual(self.emit(self.tmp / "t.csv", reader="someone@example.com")[0], 2)

    def test_check_names_each_kind_of_problem(self):
        sheet = self.tmp / "s.csv"
        self.emit(sheet)
        self.fill(sheet, self.labels())
        with open(sheet, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        ids = [r["id"] for r in rows]
        rows[0]["groundedness"] = "maybe"
        rows[1]["row_sha"] = "0" * 12
        rows[2]["reader"] = "L1"
        rows.append(dict(rows[3]))
        rows.append({**rows[4], "id": "zz-99"})
        del rows[5]
        with open(sheet, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=bjs.SHEET_FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        code, text = self.check(sheet)
        self.assertEqual(code, 1)
        for want in (f"{ids[0]}: groundedness is 'maybe', not yes or no", f"{ids[1]}: labelled on another answer",
                     "one reader per sheet: it names ['L1', 'you']", f"{ids[3]}: on the sheet 2 times",
                     "zz-99: not a row of the frozen set", f"{ids[5]}: not on the sheet"):
            self.assertIn(want, text)

    def test_a_sheet_a_spreadsheet_saved_still_checks(self):
        sheet = self.tmp / "s.csv"
        self.emit(sheet)
        self.fill(sheet, self.labels(), bom=True, crlf=True, upper=True)
        self.assertTrue(sheet.read_bytes().startswith(b"\xef\xbb\xbf"))
        code, text = self.check(sheet)
        self.assertEqual(code, 0, text)

    def test_a_pseudonymous_reader_never_an_email(self):
        sheet = self.tmp / "s.csv"
        self.emit(sheet)
        self.fill(sheet, self.labels(), reader="someone@example.com")
        code, text = self.check(sheet)
        self.assertEqual(code, 1)
        self.assertIn("never a name or an email", text)

    def test_the_fixture_sheets_check(self):
        for name in ("labels.FX1.csv", "labels.FX2.csv"):
            code, text = self.check(FIX / name)
            self.assertEqual(code, 0, text)

    def test_a_missing_set_is_exit_2_with_where_it_comes_from(self):
        code, text = quiet(bjs.main, ["--emit", str(self.tmp / "s.csv"), "--set", str(self.tmp / "none.json")])
        self.assertEqual(code, 2)
        self.assertIn("--freeze", text)


# ----------------------------------------------------------------------------- judge_agree.py on the fixtures
class JudgeAgreeTest(Tmp):
    def agree(self, *args):
        return quiet(judge_agree.main, [*map(str, args), "--set", str(FIX / "judge_set.json")])

    def sheet_labels(self, name, rubric):
        _, labels, _ = judge_agree.read_sheet(str(FIX / name), self.frozen)
        return [labels[r["id"]][rubric] for r in self.frozen]

    def test_people_kappa_is_agreements_on_the_two_sheets(self):
        code, text = self.agree("people", FIX / "labels.FX1.csv", FIX / "labels.FX2.csv")
        self.assertEqual(code, 0, text)
        for rubric in bjs.RUBRICS:
            a, b = self.sheet_labels("labels.FX1.csv", rubric), self.sheet_labels("labels.FX2.csv", rubric)
            want = f"kappa {ag.fmt_kappa(ag.cohen_kappa(a, b))}"
            block = text.split(f"  {rubric}\n", 1)[1]
            self.assertIn(want, block.split("\n\n", 1)[0])
        self.assertIn("FX1 (", text)
        self.assertIn("(constructed)", text)

    def test_the_judge_against_a_reader_with_the_cut(self):
        code, text = self.agree("judge", FIX / "ratings.ndjson", FIX / "labels.FX1.csv")
        self.assertEqual(code, 0, text)
        lines = jsonl(FIX / "ratings.ndjson")
        people = self.sheet_labels("labels.FX1.csv", "answers_the_question")
        for cut in (4, 3):
            judged = [x["ratings"]["instruction_following"]["score"] >= cut for x in lines]
            t = ag.table(people, judged)
            code, text = self.agree("judge", FIX / "ratings.ndjson", FIX / "labels.FX1.csv", "--cut", cut)
            block = text.split("  answers_the_question", 1)[1]
            self.assertIn(f"false-pass  {judge_agree.rate(*ag.false_pass(t))}", block)
            self.assertIn(f"true-pass   {judge_agree.rate(*ag.true_pass(t))}", block)
            self.assertIn(f"a pass at {cut} or more (CUT={cut})", text)
        self.assertIn("false-pass on constructed rows", text)

    def test_the_sweep_shows_every_cut(self):
        code, text = self.agree("judge", FIX / "ratings.ndjson", FIX / "labels.FX1.csv", "--sweep")
        self.assertEqual(code, 0, text)
        self.assertEqual(len(re.findall(r"(?m)^ +[1-5] +\d+/9 ", text)), 5)
        self.assertIn("<- CUT", text)

    def test_ratings_of_another_answer_are_left_out(self):
        lines = jsonl(FIX / "ratings.ndjson")
        lines[0]["response"] += " Changed."
        path = self.tmp / "ratings.jsonl"
        path.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        code, text = self.agree("judge", path, FIX / "labels.FX1.csv")
        self.assertEqual(code, 0, text)
        self.assertIn(f"left out, rated on another answer than the frozen one: {lines[0]['id']}", text)
        self.assertIn(f"{len(lines) - 1} of the frozen rows rated", text)
        self.assertIn(f"not rated: {lines[0]['id']}", text)

    def test_an_input_that_is_missing_or_off_its_scale_is_exit_2(self):
        code, text = self.agree("people", self.tmp / "none.csv", FIX / "labels.FX2.csv")
        self.assertEqual(code, 2)
        self.assertIn("make label-sheet", text)
        code, text = self.agree("judge", self.tmp / "none.jsonl", FIX / "labels.FX1.csv")
        self.assertEqual(code, 2)
        self.assertIn("make judge-frozen", text)
        lines = jsonl(FIX / "ratings.ndjson")
        lines[0]["ratings"]["groundedness"]["score"] = 3.0
        path = self.tmp / "ratings.jsonl"
        path.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        code, text = self.agree("judge", path, FIX / "labels.FX1.csv")
        self.assertEqual(code, 2)
        self.assertIn("groundedness scores other than 0 and 1", text)
        with self.assertRaises(SystemExit) as stop, contextlib.redirect_stderr(io.StringIO()):
            self.agree("judge", FIX / "ratings.ndjson", FIX / "labels.FX1.csv", "--cut", 7)       # a cut off the 1-5 scale
        self.assertEqual(stop.exception.code, 2)


# ----------------------------------------------------------------------------- the make targets
class WiringTest(unittest.TestCase):
    def test_the_three_targets(self):
        mk = (KIT / "Makefile").read_text(encoding="utf-8")
        ev = (KIT / "mk" / "evaluation.mk").read_text(encoding="utf-8")
        readme = (KIT / "mk" / "README.md").read_text(encoding="utf-8")
        self.assertEqual(len(mk.splitlines()), 888)                     # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        for target in ("label-sheet", "judge-agree", "judge-frozen"):
            self.assertIn(target, phony)
            self.assertIn(f"`{target}`", readme)
            self.assertRegex(ev, rf"(?m)^{target}:")
        self.assertIn("\njudge-frozen: guard-project\n", ev)
        self.assertIn("evals/build_judge_set.py --emit $(or $(LABELS),evals/reports/judge_labels.csv) --reader $(or $(READER),you)", ev)
        self.assertIn("people $(or $(LABELS),evals/reports/judge_labels.csv) $(or $(AGAINST),evals/judge_labels.L1.csv)", ev)
        self.assertIn("judge $(or $(RUN),evals/judge_set.ratings.jsonl) $(or $(LABELS),evals/reports/judge_labels.csv) "
                      "--cut $(or $(CUT),4)", ev)
        # the kit's set, or a learner's own freeze in evals/reports/ while the kit has none (lesson 4.5, step 3)
        frozen = "$(firstword $(wildcard evals/judge_set.json evals/reports/judge_set.json))"
        self.assertIn('test -n "$(wildcard evals/judge_set.json evals/reports/judge_set.json)" ||', ev)
        self.assertIn(f"--reuse {frozen} --no-enrich", ev)
        self.assertIn("--save-rows $(or $(RUN),evals/reports/judge_set.ratings.jsonl)", ev)
        self.assertIn("evaluation.mk", readme)

    def test_a_learners_own_freeze_is_read_while_the_kit_has_none(self):
        # The author's set ships as evals/judge_set.json; until then a learner freezes into evals/reports/, which git
        # ignores, so a later pull of the author's set never collides with it. The kit's set wins once it is there.
        import importlib
        with tempfile.TemporaryDirectory() as d:
            evals = Path(d) / "evals"
            (evals / "reports").mkdir(parents=True)
            for name in ("build_judge_set.py", "run_eval.py"):
                shutil.copy2(KIT / "evals" / name, evals / name)
            sys.path.insert(0, str(evals))
            try:
                def resolve():
                    for mod in ("build_judge_set", "run_eval"):
                        sys.modules.pop(mod, None)
                    return importlib.import_module("build_judge_set")
                self.assertEqual(resolve().JUDGE_SET, str(evals / "judge_set.json"))     # neither: the kit's path
                (evals / "reports" / "judge_set.json").write_text("[]")
                self.assertEqual(resolve().JUDGE_SET, str(evals / "reports" / "judge_set.json"))
                (evals / "judge_set.json").write_text("[]")
                self.assertEqual(resolve().JUDGE_SET, str(evals / "judge_set.json"))     # the kit's wins
            finally:
                sys.path.remove(str(evals))
                for mod in ("build_judge_set", "run_eval"):
                    sys.modules.pop(mod, None)


if __name__ == "__main__":
    unittest.main()
