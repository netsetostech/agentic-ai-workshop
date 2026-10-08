"""Offline checks for make_trainset.py --style helpdesk, lesson 12.1's v3 (27 September 2026).

Run with ``python -m unittest discover -s evals/tests -p test_make_trainset_helpdesk.py`` from deploy/. The teacher,
Cloud Storage and DLP are stood in by modules that record what the kit asks of them; the chunks are the kit's own
corpus mirrors, the golden set is the kit's, and the served prompt is checked against generator.py's own line. No
credential, no network, no SDK.
"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "make_trainset.py"
spec = importlib.util.spec_from_file_location("make_trainset_helpdesk_under_test", MODULE_PATH)
mt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mt)
DEPLOY = MODULE_PATH.parents[1]
GENERATOR = (DEPLOY / "services" / "rag-api" / "generator.py").read_text(encoding="utf-8")
GOLDEN = [json.loads(line) for line in (DEPLOY / "evals" / "golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
EVERYTHING = mt.load_chunks("acme")
POOL, FILLER = mt.helpdesk_pool(EVERYTHING, GOLDEN)


class APIError(Exception):
    def __init__(self, code, status):
        super().__init__(f"{code} {status}")
        self.code, self.status = code, status


class Options:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def teacher(contents):
    """A teacher that answers from the passage: its first eighteen words, quoted exactly, and a Hinglish twin."""
    words = re.sub(r"\s+", " ", contents.split("\n\nPassage:\n", 1)[1]).strip().split()[:18]
    said = " ".join(words)
    return {"question": "What does this passage say?", "verdict": "See the clause", "why": said, "clause": "", "quote": said,
            "unanswerable_question": "Does it set a retirement age?", "question_hinglish": "Is passage mein kya likha hai?",
            "verdict_hinglish": "Clause dekhiye", "why_hinglish": "Isme likha hai: " + said,
            "unanswerable_question_hinglish": "Kya isme retirement age di gayi hai?"}


def modules(made, outcomes=None):
    """google, google.genai (its errors and types), google.cloud.storage and shared.pii, each recording its calls."""
    class Models:
        def generate_content(self, model, contents, config=None):
            made["calls"].append({"model": model, "contents": contents, "config": config})
            out = outcomes.pop(0) if outcomes else None
            if isinstance(out, Exception):
                raise out
            return types.SimpleNamespace(parsed=types.SimpleNamespace(**teacher(contents)))

    class Client:
        def __init__(self, **kw):
            made["client"] = kw
            self.models = Models()

    genai = types.ModuleType("google.genai")
    genai.Client = Client
    genai.errors = types.ModuleType("google.genai.errors")
    genai.errors.APIError = APIError
    genai.types = types.ModuleType("google.genai.types")
    for name in ("HttpOptions", "HttpRetryOptions", "GenerateContentConfig", "ThinkingConfig", "AutomaticFunctionCallingConfig"):
        setattr(genai.types, name, Options)

    class Blob:
        def __init__(self, name):
            self.name = name

        def upload_from_filename(self, path):
            made["uploads"].append(self.name)

    storage = types.ModuleType("google.cloud.storage")
    storage.Client = lambda *a, **kw: types.SimpleNamespace(bucket=lambda b: types.SimpleNamespace(blob=Blob))
    cloud = types.ModuleType("google.cloud")
    cloud.storage = storage
    google = types.ModuleType("google")
    google.genai, google.cloud = genai, cloud
    pii = types.ModuleType("shared.pii")
    pii.inspect_many = lambda texts: [([{"info_type": "INDIA_PAN_INDIVIDUAL"}] if re.search(r"\b[A-Z]{3}P[A-Z][0-9]{4}[A-Z]\b", t) else [])
                                      for t in texts]
    return {"google": google, "google.genai": genai, "google.genai.errors": genai.errors, "google.genai.types": genai.types,
            "google.cloud": cloud, "google.cloud.storage": storage, "shared.pii": pii}


def rows_for(n=12, **kw):
    chunks = mt.sample([c for c in EVERYTHING if c["chunk_id"] not in FILLER], n)
    return mt.helpdesk_rows([(c, teacher(mt.HELPDESK_ASK + c["text"][:2400])) for c in chunks], POOL, **kw)


class TheTeacher(unittest.TestCase):
    def test_it_is_asked_once_a_chunk_for_the_pair_and_its_hinglish_twin(self):
        made = {"calls": []}
        with patch.dict(sys.modules, modules(made)):
            pairs = mt.ask_helpdesk("p", EVERYTHING[:2])
        self.assertEqual(made["client"]["location"], "global")
        self.assertEqual(made["client"]["http_options"].retry_options.attempts, 8)
        self.assertEqual([c["model"] for c in made["calls"]], [mt.HELPDESK_TEACHER] * 2)
        self.assertIn("again in Hinglish", made["calls"][0]["contents"])
        fields = set(made["calls"][0]["config"].response_schema.model_fields)
        self.assertTrue({"verdict", "why", "clause", "quote", "question_hinglish", "why_hinglish"} <= fields, fields)
        self.assertEqual(len(pairs), 2)

    def test_a_chunk_that_fails_every_attempt_is_skipped_and_named(self):
        made, out, err = {"calls": []}, io.StringIO(), io.StringIO()
        with patch.dict(sys.modules, modules(made, [None, APIError(429, "RESOURCE_EXHAUSTED"), None])), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            pairs = mt.ask_helpdesk("p", EVERYTHING[:3])
        self.assertEqual([c["chunk_id"] for c, _ in pairs], [EVERYTHING[0]["chunk_id"], EVERYTHING[2]["chunk_id"]])
        self.assertIn("chunk 2/3 skipped after 8 attempts: 429 RESOURCE_EXHAUSTED", err.getvalue())


class TheRows(unittest.TestCase):
    def test_every_prompt_is_the_one_generator_py_sends(self):
        line = re.search(r'^    prompt = (f"\{SYSTEM\}\{_dated_rule\(packed\)\}.*")$', GENERATOR, re.M).group(1)
        system = re.search(r'^SYSTEM = """(.*?)"""', GENERATOR, re.M | re.S).group(1)
        self.assertEqual(system, mt.SYSTEM)
        sys.path.append(str(DEPLOY / "services" / "rag-api"))
        from context_budget import pack_chunks
        by_id = {c["chunk_id"]: c for c in EVERYTHING}
        rows, _ = rows_for()
        for r in rows:
            context, _, _ = pack_chunks([mt.served_chunk(by_id[i]) for i in r["context_ids"]], 10 ** 9)
            served = eval(line, {"SYSTEM": system, "_dated_rule": lambda packed: "", "packed": [], "context": context, "query": r["question"]})
            self.assertEqual(r["prompt"], served)
            self.assertEqual(r["prompt"].count("[Source "), 1 + mt.DISTRACTORS)

    def test_distractors_are_never_golden_evidence_or_filler(self):
        pooled = {c["chunk_id"] for c in POOL}
        evidence = {d["chunk_id"] for d in mt.exclude_golden([{**c, "question": ""} for c in EVERYTHING], GOLDEN)[1]}
        self.assertTrue(evidence and FILLER)
        self.assertFalse(pooled & (evidence | FILLER))
        for r in rows_for()[0]:
            self.assertEqual(r["context_ids"][r["position"] - 1], r["chunk_id"])
            self.assertTrue(set(r["context_ids"]) - {r["chunk_id"]} <= pooled)

    def test_answers_mark_the_source_they_cite_and_refusals_cite_none(self):
        from shared.documind_schemas import ModelDraft
        rows, dropped = rows_for(n=20)
        self.assertEqual(dropped, {"quote": 0, "incomplete": 0, "hinglish": 0})
        self.assertTrue(any(not r["answerable"] for r in rows) and any(r["lang"] == "hinglish" for r in rows))
        for r in rows:
            draft = ModelDraft.model_validate_json(r["target"])
            self.assertTrue(draft.answer.startswith("**Answer:** "))
            if r["answerable"]:
                self.assertEqual([c.source for c in draft.citations], [r["position"]])
                self.assertIn(f" [{r['position']}].\n**Clause:** ", draft.answer)
                self.assertTrue(mt.quote_holds(draft.citations[0].quote, r["text"]))
            else:
                self.assertEqual((draft.citations, draft.confidence), ([], "low"))

    def test_a_pair_with_no_verdict_is_counted_apart(self):
        c = EVERYTHING[0]
        rows, dropped = mt.helpdesk_rows([(c, dict(teacher(mt.HELPDESK_ASK + c["text"]), verdict=" "))], POOL)
        self.assertEqual((rows, dropped["incomplete"], dropped["quote"]), ([], 1, 0))

    def test_a_quote_not_in_its_chunk_drops_the_pair(self):
        c = EVERYTHING[0]
        bad = dict(teacher(mt.HELPDESK_ASK + c["text"]), quote="words this passage never printed")
        long = dict(teacher(mt.HELPDESK_ASK + c["text"]), quote=" ".join(c["text"].split()[:30]))
        rows, dropped = mt.helpdesk_rows([(c, bad), (c, long)], POOL)
        self.assertEqual((rows, dropped["quote"]), ([], 2))

    def test_hinglish_twins_share_their_pairs_split(self):
        rows, _ = rows_for(n=60, validation_every=10)
        held = {r["chunk_id"] for r in rows if r["split"] == "validation"}
        self.assertTrue(held)
        for r in rows:
            self.assertEqual(r["split"] == "validation", r["chunk_id"] in held)
        twins = [r for r in rows if r["lang"] == "hinglish" and r["answerable"]]
        self.assertEqual(len(twins), 30)                                         # every second chunk
        self.assertTrue(all(mt.is_hinglish(r["question"]) for r in twins))

    def test_a_twin_goes_with_the_pair_the_question_rule_dropped(self):
        rows, _ = rows_for(n=12)
        pair = next(r for r in rows if r["lang"] == "hinglish" and r["answerable"])
        english = next(r for r in rows if r["chunk_id"] == pair["chunk_id"] and r["lang"] == "en")
        dropped = [{**english, "overlaps": "lk-99", "rule": "question"}]
        kept, dropped = mt.drop_orphan_twins([r for r in rows if r is not english], dropped)
        self.assertNotIn(pair, kept)
        self.assertEqual([(d["lang"], d["overlaps"], d["rule"]) for d in dropped], [("en", "lk-99", "question"), ("hinglish", "lk-99", "question")])
        refusals = [r for r in rows if r["chunk_id"] == pair["chunk_id"] and not r["answerable"]]
        self.assertTrue(all(r in kept for r in refusals))                        # a refusal is another question, and stays

    def test_the_scan_reads_every_chunk_a_prompt_carries(self):
        rows, _ = rows_for()
        inspect = lambda texts: [([{"info_type": "PHONE_NUMBER"}] if t == rows[0]["context_texts"][-1] else []) for t in texts]  # noqa: E731
        kept, dropped = mt.redact_served(rows, inspect)
        self.assertGreaterEqual(dropped, 1)
        self.assertNotIn(rows[0], kept)


class TheBuild(unittest.TestCase):
    def test_main_writes_four_files_and_a_manifest_and_uploads_them(self):
        made = {"calls": [], "uploads": []}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, modules(made)), contextlib.redirect_stdout(io.StringIO()) as out, \
                patch.object(sys, "argv", ["make_trainset.py", "--project", "p", "--rows", "20", "--out", tmp, "--version", "vt",
                                           "--style", "helpdesk", "--upload", "gs://p-datasets/sft/"]):
            self.assertEqual(mt.main(), 0)
            m = json.loads((Path(tmp) / "documind_sft_vt.manifest.json").read_text(encoding="utf-8"))
            vertex = [json.loads(line) for line in (Path(tmp) / "documind_sft_vt.vertex.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual((m["style"], m["teacher"], m["distractors"]), ("helpdesk", mt.HELPDESK_TEACHER, mt.DISTRACTORS))
        self.assertEqual(sorted(m["files"]), ["chat", "rows", "validation", "vertex"])
        self.assertEqual(len(vertex), m["rows"])
        self.assertTrue(all("systemInstruction" not in v for v in vertex))
        self.assertEqual(sorted(made["uploads"]), sorted(f"sft/documind_sft_vt.{x}" for x in
                                                         ("chat.jsonl", "manifest.json", "rows.jsonl", "validation.vertex.jsonl", "vertex.jsonl")))
        self.assertIn("generated GEN- sections left out", out.getvalue())
        self.assertFalse(any("#GEN-" in c["contents"] for c in made["calls"]))

    def test_the_batch_lane_is_refused(self):
        with patch.object(sys, "argv", ["make_trainset.py", "--project", "p", "--style", "helpdesk", "--batch", "gs://p/b/"]), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(mt.main(), 2)
        self.assertIn("the batch lane writes the plain style", err.getvalue())


if __name__ == "__main__":
    unittest.main()
