"""Offline checks for make_trainset.ask_pairs() under a 429 (24 September 2026).

Run with ``python -m unittest discover -s evals/tests -p test_make_trainset_retry.py``
from deploy/. google-genai is stood in by modules that record what the kit
asks of them, so the tests need no credential, no network and no SDK; the last
test runs only where the real SDK is installed, and checks that it accepts RETRY.
"""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "make_trainset.py"
spec = importlib.util.spec_from_file_location("make_trainset_under_test", MODULE_PATH)
mt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mt)


class APIError(Exception):
    def __init__(self, code, status):
        super().__init__(f"{code} {status}")
        self.code, self.status = code, status


class Options:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def sdk(outcomes, made):
    """google, google.genai and its errors and types; each call pops the next outcome: an exception or a pair."""
    class Models:
        def generate_content(self, model, contents, config=None):
            made["configs"].append(config)
            out = outcomes.pop(0)
            if isinstance(out, Exception):
                raise out
            return types.SimpleNamespace(parsed=types.SimpleNamespace(**out))

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
    google = types.ModuleType("google")     # its own, so a real google.genai imported earlier cannot answer instead
    google.genai = genai
    return {"google": google, "google.genai": genai, "google.genai.errors": genai.errors, "google.genai.types": genai.types}


def pair(n):
    return {"question": f"q{n}", "answer": f"a{n}", "quote": f"quote {n}", "unanswerable_question": f"u{n}"}


def chunks(n):
    return [{"chunk_id": f"c{i}", "source_uri": f"gs://b/doc{i}.md", "text": f"text {i}"} for i in range(n)]


def run(outcomes, n):
    made = {"configs": []}
    out, err = io.StringIO(), io.StringIO()
    with patch.dict(sys.modules, sdk(outcomes, made)), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rows = mt.ask_pairs("p", chunks(n), refusal_every=0)
        except SystemExit as e:
            return made, None, out.getvalue(), err.getvalue(), e
    return made, rows, out.getvalue(), err.getvalue(), None


class AskPairsUnderLoad(unittest.TestCase):
    def test_the_client_carries_the_retry_options(self):
        made, rows, _, _, _ = run([pair(0)], 1)
        retry = made["client"]["http_options"].retry_options
        self.assertEqual(made["client"]["location"], "global")
        self.assertEqual((retry.attempts, retry.initial_delay, retry.max_delay), (8, 2.0, 60.0))
        self.assertEqual(retry.http_status_codes, [408, 429, 500, 502, 503, 504])
        self.assertTrue(made["configs"][0].automatic_function_calling.disable)
        self.assertEqual([r["question"] for r in rows], ["q0"])

    def test_a_chunk_that_fails_every_attempt_is_skipped_and_named(self):
        _, rows, out, err, stop = run([pair(0), APIError(429, "RESOURCE_EXHAUSTED"), pair(2)], 3)
        self.assertIsNone(stop)
        self.assertEqual([r["chunk_id"] for r in rows], ["c0", "c2"])
        self.assertIn("chunk 2/3 skipped after 8 attempts: 429 RESOURCE_EXHAUSTED", err)
        self.assertIn("1 of 3 chunks skipped after every attempt, so no row: c1", out)

    def test_three_in_a_row_stop_the_run(self):
        busy = [APIError(429, "RESOURCE_EXHAUSTED") for _ in range(3)]
        _, rows, _, _, stop = run([pair(0), APIError(503, "UNAVAILABLE"), pair(2)] + busy + [pair(6)], 7)
        self.assertIsNone(rows)
        self.assertIn("3 chunks in a row failed every attempt: stopped at chunk 6 of 7, nothing written", str(stop.code))

    def test_a_success_resets_the_count(self):
        flaky = [APIError(429, "RESOURCE_EXHAUSTED"), APIError(429, "RESOURCE_EXHAUSTED"), pair(2)] * 2
        _, rows, _, _, stop = run(flaky, 6)
        self.assertIsNone(stop)
        self.assertEqual([r["chunk_id"] for r in rows], ["c2", "c5"])

    def test_a_request_error_is_not_retried_away(self):
        with self.assertRaises(APIError):
            run([APIError(400, "INVALID_ARGUMENT"), pair(1)], 2)

    def test_the_real_sdk_accepts_retry(self):
        try:
            from google.genai import types as real
        except ImportError:
            self.skipTest("google-genai is not installed")
        self.assertEqual(real.HttpRetryOptions(**mt.RETRY).attempts, 8)


if __name__ == "__main__":
    unittest.main()
