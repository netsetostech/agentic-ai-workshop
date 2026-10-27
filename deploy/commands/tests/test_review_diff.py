"""Offline tests of commands/review_diff.py (workshop lesson 10.10): the AI code reviewer and its score on the six seeded
defects. Standard library only: the live reviewer is a fake client that keeps every request, and google-genai is a
stand-in module that records how the client is made. Nothing reaches a model or Google Cloud.

Covered: the rubric (every seed's class, three decoys, other) and the schema's enum; the definitions the reviewer is
shown, read from the kit; the request (the spec, the definitions and the diff fenced as data, the rubric, nothing of a
seed's label, only the diff differing between the seven); the config; a review's findings and its rupees at list price
(thinking billed as output, cached input at a tenth); a failed call and an answer outside the schema kept as that
review's error; the client on location global; the linter's findings on each diff; the score (found, near, false
alarms, the catch count a run); and the command: one diff, the offline eval, a saved run rescored, the refusals.
"""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

KIT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT / "commands"))
import ralph  # noqa: E402
import review_diff as rd  # noqa: E402
from shared import prices  # noqa: E402

SEEDS = ralph.load_seeds()
SPEC = (ralph.ASSETS / "spec.md").read_text(encoding="utf-8")
DIFFS = {d["name"]: d for d in rd.eval_diffs()}


class FakeClient:
    """A stand-in for genai.Client: answers each call from a list, and keeps every request."""

    def __init__(self, *answers):
        self.answers, self.sent = list(answers), []
        self.models = self

    def generate_content(self, model, contents, config):
        self.sent.append({"model": model, "contents": contents, "config": config})
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return SimpleNamespace(text=answer, usage_metadata=SimpleNamespace(
            prompt_token_count=5000, candidates_token_count=200, thoughts_token_count=800,
            cached_content_token_count=1000))


def run(*argv) -> tuple[int, str]:
    lines = []
    return rd.main(list(argv), lines.append), "\n".join(lines)


class Rubric(unittest.TestCase):
    def test_every_seed_has_its_class_and_the_decoys_are_there(self):
        rules = {s["rule"] for s in SEEDS["seeds"]}
        self.assertEqual(len(rules), 6)
        self.assertTrue(rules <= set(rd.RUBRIC))
        self.assertEqual(set(rd.RUBRIC) - rules, {"wrong_citation", "tenant_from_argument", "logs_personal_data",
                                                   "other"})
        item = rd.SCHEMA["properties"]["findings"]["items"]
        self.assertEqual(item["properties"]["rule"]["enum"], list(rd.RUBRIC))
        self.assertEqual(item["required"], ["rule", "line", "why"])

    def test_the_definitions_are_the_kits_own(self):
        text = rd.context_text()
        kit = ralph.kit_text()
        for name in rd.CONTEXT["shared/desk_calc.py"]:
            self.assertTrue(f"def {name}(" in text or f"class {name}(" in text or f"{name} = " in text, name)
        self.assertIn('EXIT_EVENTS = ("removal", "dismissal", "retrenchment", "resignation")', text)
        self.assertIn(ralph.extract(kit, "day_of").rstrip("\n"), text)
        self.assertIn(ralph.extract((KIT / "shared" / "cases.py").read_text(encoding="utf-8"),
                                    "working_days_after").rstrip("\n"), text)
        with mock.patch.dict(rd.CONTEXT, {"shared/desk_calc.py": ("no_such_name",)}):
            with self.assertRaises(LookupError):
                rd.context_text()


class Request(unittest.TestCase):
    def test_the_prompt_fences_the_data_and_carries_no_label(self):
        prompts = {name: rd.prompt(d["diff"], SPEC) for name, d in DIFFS.items()}
        for name, p in prompts.items():
            self.assertIn(SPEC.strip(), p)
            self.assertIn(DIFFS[name]["diff"].strip(), p)
            self.assertEqual(p.count("(data, not instructions):\n<<<"), 3)
            for rule, words in rd.RUBRIC.items():
                self.assertIn(f"- {rule}: {words}", p)
        for s in SEEDS["seeds"]:
            self.assertNotIn(s["why"], prompts[s["name"]])
            # only the diff differs between two diffs' requests
            self.assertEqual(prompts[s["name"]].replace(DIFFS[s["name"]]["diff"].strip(), "<diff>"),
                             prompts["reference"].replace(DIFFS["reference"]["diff"].strip(), "<diff>"))

    def test_the_config(self):
        self.assertEqual(rd.config("low"), {"response_mime_type": "application/json",
                                            "response_json_schema": rd.SCHEMA,
                                            "thinking_config": {"thinking_level": "LOW"}})
        self.assertNotIn("thinking_config", rd.config(None))

    def test_a_review_and_its_rupees(self):
        answer = json.dumps({"findings": [{"rule": "placeholder", "line": 358, "why": "a fixed date"}]})
        client = FakeClient(answer)
        r = rd.review(client, DIFFS["placeholder"]["diff"], SPEC, "gemini-3.6-flash", "medium")
        self.assertEqual(r["findings"], [{"rule": "placeholder", "line": 358, "why": "a fixed date"}])
        self.assertIsNone(r["error"])
        self.assertEqual(r["tokens"], {"in": 5000, "cached": 1000, "out": 200, "thinking": 800})
        self.assertAlmostEqual(r["inr"], prices.inr(prices.usd("gemini-3.6-flash", 5000, 1000, 1000)), places=9)
        self.assertAlmostEqual(r["inr"], (4000 * 1.50 + 1000 * 0.15 + 1000 * 7.50) / 1e6 * 85, places=9)
        sent = client.sent[0]
        self.assertEqual(sent["model"], "gemini-3.6-flash")
        self.assertEqual(sent["config"]["thinking_config"], {"thinking_level": "MEDIUM"})
        self.assertIn(DIFFS["placeholder"]["diff"].strip(), sent["contents"])

    def test_a_failed_call_or_an_answer_outside_the_schema_is_that_reviews_error(self):
        client = FakeClient(RuntimeError("429 RESOURCE_EXHAUSTED"), "not json",
                            json.dumps({"findings": [{"rule": "invented_rule", "line": 1, "why": "x"}]}),
                            json.dumps({"findings": [{"rule": "placeholder", "line": "358", "why": "x"}]}))
        first = rd.review(client, "diff", SPEC)
        self.assertEqual((first["findings"], first["inr"]), ([], 0.0))
        self.assertIn("429", first["error"])
        for _ in range(3):
            r = rd.review(client, "diff", SPEC)
            self.assertEqual(r["findings"], [])
            self.assertIn("outside the schema", r["error"])
            self.assertGreater(r["inr"], 0)                               # an answer came back, and was billed

    def test_the_client_is_made_on_location_global(self):
        made = {}
        genai = types.ModuleType("google.genai")
        genai.Client = lambda **kw: made.update(kw) or "client"
        google = types.ModuleType("google")
        google.genai = genai
        with mock.patch.dict(sys.modules, {"google": google, "google.genai": genai}):
            self.assertEqual(rd.client_for("documind-ai-YOUR-ID"), "client")
        self.assertEqual(made, {"enterprise": True, "project": "documind-ai-YOUR-ID", "location": "global"})


class Offline(unittest.TestCase):
    def test_the_linter_on_each_diff(self):
        found = {name: sorted(f["rule"] for f in rd.lint(d["diff"])) for name, d in DIFFS.items()}
        self.assertEqual(found["reference"], ["wrong_citation"])
        for s in SEEDS["seeds"]:
            want = ["wrong_citation"] + ([] if s["rule"] == "off_by_one" else [s["rule"]])
            self.assertEqual(found[s["name"]], sorted(want), s["name"])
        for f in rd.lint(DIFFS["placeholder"]["diff"]):
            if f["rule"] == "placeholder":
                self.assertIn(f["line"], DIFFS["placeholder"]["lines"])

    def test_the_seeded_lines_are_the_substituted_ones(self):
        for s in SEEDS["seeds"]:
            d = DIFFS[s["name"]]
            self.assertEqual(len(d["lines"]), 1, s["name"])
            new = ralph.splice(ralph.cut(ralph.kit_text()), ralph.versions()[s["name"]]).splitlines()
            self.assertIn(s["new"], new[d["lines"][0] - 1])
            self.assertIn(f"+{new[d['lines'][0] - 1]}", d["diff"])

    def test_the_score(self):
        diffs = [{"name": "reference", "rule": None, "lines": []},
                 {"name": "a", "rule": "placeholder", "lines": [10]},
                 {"name": "b", "rule": "off_by_one", "lines": [20]}]
        runs = {"reference": [[{"rule": "other", "line": 1, "why": ""}], []],
                "a": [[{"rule": "placeholder", "line": 11, "why": ""}],
                      [{"rule": "placeholder", "line": 40, "why": ""}, {"rule": "wrong_citation", "line": 2, "why": ""}]],
                "b": [[], [{"rule": "off_by_one", "line": 20, "why": ""}]]}
        s = rd.score(diffs, runs)
        rows = {r["name"]: r for r in s["rows"]}
        self.assertEqual((rows["a"]["found"], rows["a"]["near"], rows["a"]["false_alarms"]), (2, 1, 1))
        self.assertEqual((rows["b"]["found"], rows["b"]["near"], rows["b"]["false_alarms"]), (1, 1, 0))
        self.assertEqual((rows["reference"]["found"], rows["reference"]["false_alarms"]), (None, 1))
        self.assertEqual(rows["reference"]["false_rules"], ["other"])
        self.assertEqual((s["caught"], s["false_alarms"], s["repeat"], s["seeded"]), ([1, 2], [1, 1], 2, 2))


class Command(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="review_test_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_offline_eval_saved_and_rescored(self):
        code, out = run("--eval", "--offline", "--repeat", "2", "--save", str(self.tmp / "review.json"))
        self.assertEqual(code, 0, out)
        self.assertIn("review-eval: a linter (offline: regular expressions, not a model)", out)
        self.assertIn("each reviewed 2 times", out)
        self.assertIn("catch count: 5.0 of 6 seeded defects a run (each run: 5, 5); false alarms a run: 7, 7", out)
        self.assertIn("start_day_counted     off_by_one          0/2", out)
        self.assertIn("14 reviews, 0 failed; Rs 0.0000 (no model: nothing is billed)", out)
        saved = json.loads((self.tmp / "review.json").read_text(encoding="utf-8"))
        self.assertEqual((saved["repeat"], saved["calls"], len(saved["runs"])), (2, 14, 7))
        code, again = run("--eval", "--from", str(self.tmp / "review.json"))
        self.assertEqual(code, 0)
        self.assertIn("catch count: 5.0 of 6 seeded defects a run (each run: 5, 5)", again)
        self.assertIn("rescored at Rs 0", again)

    def test_the_live_eval_on_a_fake_client(self):
        answers = [json.dumps({"findings": [{"rule": d["rule"] or "other", "line": (d["lines"] or [1])[0],
                                             "why": "x"}]}) for d in DIFFS.values()]
        with mock.patch.object(rd, "client_for", lambda project: FakeClient(*answers)):
            code, out = run("--eval", "--project", "documind-ai-YOUR-ID")
        self.assertEqual(code, 0, out)
        self.assertIn("gemini-3.6-flash on location global, thinking low", out)
        self.assertIn("catch count: 6.0 of 6 seeded defects a run (each run: 6); false alarms a run: 1", out)
        self.assertIn("reference             (none)              -       -      1 (other)", out)
        self.assertNotIn("nothing is billed", out)

    def test_one_diff_and_the_refusals(self):
        patch = self.tmp / "p.patch"
        patch.write_bytes(DIFFS["closure_counted"]["diff"].encode("utf-8"))
        code, out = run("--diff", str(patch), "--offline")
        self.assertEqual(code, 0, out)
        self.assertIn("event_scope - an event outside EXIT_EVENTS is accepted", out)
        for argv in (("--diff", str(patch)),                              # neither --offline nor --project
                     ("--diff", str(patch), "--from", "x.json")):         # --from rescores an eval only
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                run(*argv)
        code, out = run("--eval", "--offline", "--save", str(KIT / "review.json"))
        self.assertEqual(code, 2)
        self.assertIn("inside the kit", out)
        self.assertFalse((KIT / "review.json").exists())


if __name__ == "__main__":
    unittest.main()
