"""Offline tests for the answer-or-refuse eval and Jev's switch (workshop lesson 2.6): evals/decide.py and
shared/system_one.py.

Run with ``python -m unittest discover -s evals/tests -p test_decide.py`` from deploy/. Standard library only: the one
kit module here that imports a package, shared/documind_tools.py (requests, at the top; the local lane never calls
it), gets an empty stand-in for it when the package is missing. A test that could reach a network runs with
socket.socket and socket.create_connection replaced by a function that fails the test, gcloud is never run, and no
test reads a real tenant policy: each passes its own reader.
"""
import ast
import io
import importlib.util
import json
import os
import re
import socket
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

EVALS = Path(__file__).resolve().parents[1]
KIT = EVALS.parent
if str(KIT) not in sys.path:
    sys.path.insert(0, str(KIT))
try:
    import requests  # noqa: F401 - documind_tools imports it; the lanes these tests run never call it
except ImportError:
    sys.modules["requests"] = types.ModuleType("requests")


def load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_under_test", EVALS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


decide = load("decide")
from shared import system_one  # noqa: E402 - the module decide.py imported: one object, so a patch reaches both
from route_eval import wilson  # noqa: E402

AADHAAR = "2345 6789 0124"          # Verhoeff-valid (identifiers.verhoeff_digit("23456789012") is "4")
CARD = "4111 1111 1111 1111"        # Luhn-valid, a payment network's first digit
PAN = "AAAPZ1234C"                  # the corpus's synthetic invoice PAN
GSTIN = "27AAAPZ1234C1Z0"           # gstin_check_char("27AAAPZ1234C1Z") is "0"
PASSAGES = [{"n": 1, "chunk_id": "acme:inv_2026_0412#p1-0", "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/inv.md",
             "text": f"Invoice INV-2026-0412, 31.08.2024 - 01.07.2025. PAN {PAN}, GSTIN {GSTIN}. Card {CARD}."},
            {"n": 2, "chunk_id": "acme:hr_policy_2026#EXP-12", "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/hr.md",
             "text": "EXP-12 Domestic travel is reimbursed up to Rs 40,000 a trip."}]


def refuse(*args, **kwargs):
    raise AssertionError("a socket was opened")


@contextmanager
def no_network():
    with patch.object(socket, "socket", refuse), patch.object(socket, "create_connection", refuse):
        yield


@contextmanager
def jev(mode=None, recorded=None):
    """JEV_MODE set (or unset), and the recorded file pointed at `recorded` (or at a path that does not exist)."""
    env = {k: v for k, v in os.environ.items() if k != "JEV_MODE"}
    if mode is not None:
        env["JEV_MODE"] = mode
    with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, env, clear=True), \
            patch.object(system_one, "RECORDED", Path(recorded) if recorded else Path(tmp) / "absent.jsonl"):
        yield


def never(*args, **kwargs):
    raise AssertionError("called")


def a_recording(**over):
    rec = {"id": "lk-01", "tenant": "acme", "verdict": "answer", "score": 0.91, "model": "jev-test",
           "request_id": "req-0001", "recorded_at": "2026-10-27T10:00:00+05:30", "ms": 140,
           "tokens": {"input": 900, "output": 0}, "chunk_ids": [p["chunk_id"] for p in PASSAGES]}
    rec.update(over)
    return rec


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write((line if isinstance(line, str) else json.dumps(line)) + "\n")


# ===================================================================== shared/system_one.py
class SwitchTest(unittest.TestCase):
    def test_off_is_the_default_and_makes_no_call(self):
        with jev(None), no_network(), patch.object(system_one, "_request", never), \
                patch.object(system_one, "_recordings", never), patch.object(system_one.tenancy, "policy_for", never):
            res = system_one.decide("What is the per-trip cap?", PASSAGES, "lk-01", "acme")
            self.assertEqual(system_one.mode(), "off")
        self.assertEqual(tuple(res), system_one.RESULT_KEYS)
        self.assertEqual((res["verdict"], res["source"], res["reason"]), ("skipped", "off", system_one.OFF_REASON))
        self.assertIn("Jev not available", res["reason"])

    def test_an_unknown_mode_sends_nothing(self):
        with jev("liev"), no_network(), patch.object(system_one, "_request", never):
            res = system_one.decide("q", PASSAGES, "lk-01", "acme")
        self.assertEqual(res["verdict"], "skipped")
        self.assertIn("'liev'", res["reason"])

    def test_an_empty_pool_is_refused_by_code_and_jev_is_not_asked(self):
        for mode in ("recorded", "live"):
            with jev(mode), no_network(), patch.object(system_one, "_request", never), \
                    patch.object(system_one, "_recordings", never):
                res = system_one.decide("q", [], "rf-01", "acme", policy_for=never)
            self.assertEqual((res["verdict"], res["source"], res["cost_usd"]), ("refuse", "code", 0.0), mode)


class RecordedTest(unittest.TestCase):
    def test_the_file_is_absent_and_every_row_is_skipped_saying_so(self):
        with jev("recorded"), no_network(), patch.object(system_one, "_request", never):
            res = system_one.decide("q", PASSAGES, "lk-01", "acme", policy_for=never)
        self.assertEqual((res["verdict"], res["source"], res["reason"]), ("skipped", "recorded", system_one.RECORDED_ABSENT))
        self.assertIn("does not exist", res["reason"])

    def test_no_invented_recording_ships(self):
        # The kit ships without recordings. When PR 2.6-C adds them, each line must be a real one: the vendor's
        # request_id and the time it was recorded, one line per golden row.
        path = KIT / "evals" / "system_one" / "recorded.jsonl"
        self.assertEqual(system_one.RECORDED, path)
        if not path.exists():
            return
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for rec in lines:
            self.assertEqual(system_one.recording_errors(rec), [], rec.get("id"))
        self.assertEqual(len({r["id"] for r in lines}), len(lines))

    def test_a_recording_is_read_with_no_socket_and_no_policy_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "recorded.jsonl"
            write_lines(path, [a_recording()])
            with jev("recorded", path), no_network(), patch.object(system_one, "_request", never), \
                    patch.object(system_one.tenancy, "policy_for", never):
                res = system_one.decide("q", PASSAGES, "lk-01", "acme")
        self.assertEqual((res["verdict"], res["score"], res["source"], res["request_id"], res["ms"]),
                         ("answer", 0.91, "recorded", "req-0001", 140))
        self.assertAlmostEqual(res["cost_usd"], 900 * 42 / 1e9)
        self.assertEqual(res["reason"], "recorded 2026-10-27T10:00:00+05:30")

    def test_what_is_not_a_recording(self):
        cases = {"no request_id": a_recording(request_id=""), "a typed verdict": a_recording(verdict="maybe"),
                 "a score of 7": a_recording(score=7), "a date": a_recording(recorded_at="yesterday"),
                 "another tenant": a_recording(tenant="zeta")}
        for name, rec in cases.items():
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "recorded.jsonl"
                write_lines(path, [rec])
                with jev("recorded", path):
                    res = system_one.decide("q", PASSAGES, "lk-01", "acme")
            self.assertEqual(res["verdict"], "error", name)
            self.assertNotEqual(res["verdict"], "refuse", name)

    def test_a_missing_row_a_second_line_and_a_broken_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "recorded.jsonl"
            write_lines(path, [a_recording()])
            with jev("recorded", path):
                self.assertEqual(system_one.decide("q", PASSAGES, "lk-02", "acme")["verdict"], "skipped")
            write_lines(path, [a_recording(), a_recording(score=0.2)])
            with jev("recorded", path):
                self.assertEqual(system_one.decide("q", PASSAGES, "lk-01", "acme")["verdict"], "error")
            write_lines(path, [a_recording(id="lk-02"), "{not json"])
            with jev("recorded", path):
                res = system_one.decide("q", PASSAGES, "lk-02", "acme")
        self.assertEqual(res["verdict"], "error")
        self.assertIn("line 2 is not JSON", res["error"])

    def test_a_recording_made_on_another_pool_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "recorded.jsonl"
            write_lines(path, [a_recording(chunk_ids=["acme:hr_policy_2026#EXP-12"])])
            with jev("recorded", path):
                res = system_one.decide("q", PASSAGES, "lk-01", "acme")
        self.assertEqual(res["verdict"], "answer")
        self.assertIn("recorded on another pool", res["reason"])

    def test_a_recording_comes_only_from_a_live_call(self):
        live = system_one.result("refuse", score=0.12, model="jev-test", source="live", ms=90,
                                 tokens={"input": 700, "output": 0}, request_id="req-9")
        line = system_one.recording("rf-01", "acme", PASSAGES, live, now=datetime(2026, 10, 27, tzinfo=timezone.utc))
        self.assertEqual(system_one.recording_errors(line), [])
        self.assertEqual(line["chunk_ids"], [p["chunk_id"] for p in PASSAGES])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "recorded.jsonl"
            write_lines(path, [line])
            with jev("recorded", path):
                back = system_one.decide("q", PASSAGES, "rf-01", "acme")
        self.assertEqual((back["verdict"], back["score"], back["request_id"]), ("refuse", 0.12, "req-9"))
        for bad in (dict(live, source="recorded"), dict(live, verdict="error"), dict(live, request_id=None)):
            with self.assertRaises(ValueError):
                system_one.recording("rf-01", "acme", PASSAGES, bad)


class LiveTest(unittest.TestCase):
    def test_an_in_tenant_is_never_sent(self):
        readers = {"in": lambda t: "in", "unknown": lambda t: "anywhere", "missing": lambda t: None,
                   "unreadable": never}
        for name, reader in readers.items():
            with jev("live"), no_network(), patch.object(system_one, "_request", never):
                res = system_one.decide("q", PASSAGES, "iso-02", "globex", policy_for=reader)
            self.assertEqual((res["verdict"], res["source"]), ("skipped", "policy"), name)
            self.assertIn("tenant globex: data_region in - its text stays in India", res["reason"])
        # The default reader is shared/tenancy.policy_for, which fails closed itself; one that raises is `in` too.
        with jev("live"), no_network(), patch.object(system_one, "_request", never), \
                patch.object(system_one.tenancy, "policy_for", never):
            self.assertEqual(system_one.decide("q", PASSAGES, "iso-02", "globex")["source"], "policy")

    def test_until_pr_c_live_is_an_error_and_opens_nothing(self):
        with jev("live"), no_network(), patch.dict(os.environ, {"JEV_API_KEY": ""}):
            res = system_one.decide("q", PASSAGES, "lk-01", "acme", policy_for=lambda t: "any")
        self.assertEqual((res["verdict"], res["source"], res["error"]), ("error", "live", system_one.NOT_CONFIGURED))
        self.assertEqual(res["error"], "TypeSafe adapter not configured (PR 2.6-C)")
        with patch.dict(os.environ, {"JEV_API_KEY": ""}), self.assertRaises(system_one.AdapterNotConfigured) as e:
            system_one._headers()
        self.assertIn("JEV_API_KEY", str(e.exception))

    def test_identifiers_are_masked_before_the_transport(self):
        sent = []

        def transport(payload):
            sent.append(json.loads(json.dumps(payload)))
            return 200, {"stand-in": True}

        parsed = {"verdict": "answer", "score": 0.8, "model": "jev-test", "request_id": "req-1",
                  "tokens": {"input": 1200, "output": 0}}
        question = f"My Aadhaar is {AADHAAR} and my PAN {PAN}: what is the cap?"
        with jev("live"), no_network(), patch.object(system_one, "_request", transport), \
                patch.object(system_one, "_parse", lambda status, body: dict(parsed)):
            res = system_one.decide(question, PASSAGES, "lk-01", "acme", policy_for=lambda t: "any")
        self.assertEqual((res["verdict"], res["score"], res["source"], res["request_id"]), ("answer", 0.8, "live", "req-1"))
        self.assertIn("masked aadhaar, card, gstin, pan", res["reason"])
        self.assertEqual(len(sent), 1)
        payload = sent[0]
        self.assertEqual(set(payload), {"question", "passages"})
        text = json.dumps(payload)
        for raw in (AADHAAR, PAN, GSTIN, CARD, "acme", "lk-01", "chunk_id", "source_uri", "inv_2026_0412", "gs://"):
            self.assertNotIn(raw, text)
        self.assertEqual(payload["question"], "My Aadhaar is [Aadhaar] and my PAN [PAN]: what is the cap?")
        self.assertIn("PAN [PAN], GSTIN [GSTIN]. Card [card no.].", payload["passages"][0])
        self.assertIn("INV-2026-0412, 31.08.2024 - 01.07.2025", payload["passages"][0])   # not identifiers
        self.assertEqual(payload["passages"][1], PASSAGES[1]["text"])

    def test_a_failed_call_is_an_error_never_a_refusal(self):
        def timeout(payload):
            raise TimeoutError("the API did not answer")

        for name, patches in {"transport": {"_request": timeout},
                              "parse": {"_request": lambda p: (200, {}), "_parse": lambda s, b: {}["verdict"]},
                              "a score of 7": {"_request": lambda p: (200, {}),
                                               "_parse": lambda s, b: {"verdict": "answer", "score": 7}}}.items():
            with jev("live"), no_network(), patch.multiple(system_one, **patches):
                res = system_one.decide("q", PASSAGES, "lk-01", "acme", policy_for=lambda t: "any")
            self.assertEqual(res["verdict"], "error", name)
            self.assertEqual(tuple(res), system_one.RESULT_KEYS, name)

    def test_the_price_is_typesafes_and_never_flashs(self):
        self.assertAlmostEqual(system_one._price({"input": 1_000_000_000, "output": 0}), 42.0)
        self.assertAlmostEqual(system_one._price({"input": 1_000_000, "output": 0}), 0.042)   # flash: 1.50
        self.assertIsNone(system_one._price({"input": 10, "output": 5}))      # the output's price is not documented
        self.assertIsNone(system_one._price(None))
        tree = ast.parse((KIT / "shared" / "system_one.py").read_text(encoding="utf-8"))
        imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
        imported |= {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertFalse({"prices", "shared.prices", "usd"} & imported)

    def test_masking_finds_the_four_and_passes_the_rest(self):
        masked, kinds = system_one.mask_identifiers(f"{AADHAAR} / {CARD} / {PAN} / {GSTIN}")
        self.assertEqual(masked, "[Aadhaar] / [card no.] / [PAN] / [GSTIN]")
        self.assertEqual(kinds, ["aadhaar", "card", "gstin", "pan"])
        for text in ("2234 5678 9012", "invoice INV-2026-0412", "+91 93487 17536", "Rs 1,84,500", ""):
            self.assertEqual(system_one.mask_identifiers(text), (text, []), text)


# ===================================================================== evals/decide.py: the score
def rec(rid, answerable, shape="lookup", **arms):
    """One scored row; each arm a verdict, or a (verdict, extra fields) pair."""
    out = {"id": rid, "tenant": "acme", "shape": shape, "answerable": answerable, "question": rid, "pool": {},
           "arms": {}}
    for arm in decide.ARMS:
        v = arms.get(arm, "skipped")
        v, extra = (v, {}) if isinstance(v, str) else v
        res = system_one.result(v, source=extra.pop("source", "live"), **{k: x for k, x in extra.items() if k != "confidence"})
        if "confidence" in extra:
            res["confidence"] = extra["confidence"]
        out["arms"][arm] = res
    return out


FIXTURE = [
    rec("lk-01", True, rule=("answer", {"score": 0.9, "ms": 1}), generator=("answer", {"confidence": "high", "ms": 900, "cost_usd": 0.001}),
        jev=("answer", {"score": 0.95, "ms": 100, "cost_usd": 0.0000378})),
    rec("lk-02", True, rule=("answer", {"score": 0.7, "ms": 1}), generator=("refuse", {"confidence": "low", "ms": 800, "cost_usd": 0.002}),
        jev=("answer", {"score": 0.6, "ms": 120})),
    rec("jn-01", True, shape="join", rule=("refuse", {"score": 0.4, "ms": 1}), generator=("answer", {"confidence": "medium", "ms": 1000, "cost_usd": 0.003}),
        jev="error"),
    rec("lk-03", True, rule=("answer", {"score": 1.0, "ms": 2}), generator=("answer", {"confidence": "high", "ms": 700, "cost_usd": 0.001}),
        jev=("answer", {"score": 0.9, "ms": 80})),
    rec("rf-01", False, shape="refusal", rule=("answer", {"score": 0.6, "ms": 1}), generator=("refuse", {"confidence": "low", "ms": 600, "cost_usd": 0.001}),
        jev=("refuse", {"score": 0.2, "ms": 90})),
    rec("iso-02", False, shape="isolation", rule=("answer", {"score": 0.8, "ms": 1}), generator=("answer", {"confidence": "medium", "ms": 650, "cost_usd": 0.001}),
        jev=("skipped", {"source": "policy"})),
    rec("iso-04", False, shape="isolation", rule=("refuse", {"score": 0.1, "source": "code", "ms": 0}),
        generator=("refuse", {"source": "code", "ms": 0, "cost_usd": 0.0}), jev=("refuse", {"source": "code", "ms": 0})),
    rec("rf-02", False, shape="refusal", rule=("refuse", {"score": 0.3, "ms": 1}), generator="error", jev=("answer", {"score": 0.7, "ms": 110})),
]


class ScoreTest(unittest.TestCase):
    def test_the_confusion_matrix_and_the_rates_with_wilson(self):
        s = decide.summarise(FIXTURE, "rule")
        self.assertEqual((s["tp"], s["fn"], s["fp"], s["tn"], s["error"], s["skipped"], s["code"]), (3, 1, 2, 2, 0, 0, 1))
        self.assertEqual((s["answer_rate"], s["refusal_recall"], s["accuracy"]), ((3, 4), (2, 4), (5, 8)))
        lo, hi = s["wilson"]["answer_rate"]
        self.assertAlmostEqual(lo, 0.3006, places=4)     # 3 of 4: Wilson's interval, z = 1.96
        self.assertAlmostEqual(hi, 0.9544, places=4)
        self.assertEqual(s["wilson"]["accuracy"], wilson(5, 8))
        self.assertEqual(s["false_answers"], ["rf-01", "iso-02*"])          # the isolation row flagged
        self.assertTrue(s["available"])

    def test_errors_and_skips_are_not_refusals(self):
        s = decide.summarise(FIXTURE, "jev")
        self.assertEqual((s["error"], s["skipped"]), (1, 1))
        self.assertEqual(s["refusal_recall"], (2, 3))     # rf-01 and iso-04 refused, rf-02 answered; iso-02 skipped
        self.assertEqual(s["answer_rate"], (3, 3))        # jn-01's error is not counted
        self.assertEqual(s["accuracy"], (5, 6))
        g = decide.summarise(FIXTURE, "generator")
        self.assertEqual((g["error"], g["refusal_recall"], g["answer_rate"]), (1, (2, 3), (3, 4)))
        only_errors = [rec("rf-01", False, jev="error"), rec("rf-02", False, jev=("refuse", {"source": "code"}))]
        s = decide.summarise(only_errors, "jev")
        self.assertEqual((s["available"], s["failed"], s["refusal_recall"]), (False, True, (1, 1)))

    def test_kappa(self):
        a, r = "answer", "refuse"
        self.assertAlmostEqual(decide.kappa([(a, a), (a, a), (a, r), (r, r), (r, r), (r, a), (a, a), (r, r)]), 0.5)
        self.assertAlmostEqual(decide.kappa([(a, r), (r, a)]), -1.0)
        self.assertAlmostEqual(decide.kappa([(a, a), (r, r)]), 1.0)
        self.assertIsNone(decide.kappa([(a, a), (a, a)]))        # one verdict throughout: undefined, not perfect
        self.assertIsNone(decide.kappa([]))
        # rule against the generator, on the 7 rows both decided (rf-02's generator errored): they agree on 4; the
        # rule answers 5 of 7 and the generator 4 of 7, so chance agreement is 26/49 and kappa (28 - 26) / (49 - 26)
        pairs = decide.pairs_of(FIXTURE, "rule", "generator")
        self.assertEqual(len(pairs), 7)
        self.assertAlmostEqual(decide.kappa(pairs), 2 / 23)

    def test_kappa_is_lesson_4_5s(self):
        # One Cohen's kappa in the kit (13 October 2026): decide.kappa() is evals/agreement.py's cohen_kappa() over the
        # two arms' verdicts, so lesson 2.6's kappa and lesson 4.5's are one function. Every table of up to 6 rows
        # gives what the textbook formula over the share of "answer" gives, and None exactly where chance is 1.
        import itertools
        import agreement
        self.assertIs(decide.cohen_kappa, agreement.cohen_kappa)
        a, r = "answer", "refuse"
        for n in range(7):
            for verdicts in itertools.product((a, r), repeat=2 * n):
                pairs = list(zip(verdicts[::2], verdicts[1::2]))
                got = decide.kappa(pairs)
                pa = sum(x == a for x, _ in pairs) / n if n else 0.0
                pb = sum(y == a for _, y in pairs) / n if n else 0.0
                pe = pa * pb + (1 - pa) * (1 - pb)
                if not n or pe == 1:
                    self.assertIsNone(got, pairs)
                else:
                    po = sum(x == y for x, y in pairs) / n
                    self.assertAlmostEqual(got, (po - pe) / (1 - pe), places=12, msg=pairs)

    def test_brier_and_the_reliability_bins(self):
        rows = [rec("a", True, jev=("answer", {"score": 0.9})), rec("b", False, jev=("refuse", {"score": 0.1})),
                rec("c", False, jev=("answer", {"score": 0.6})), rec("d", True, jev=("answer", {"score": 1.0})),
                rec("e", True, jev="error"), rec("f", False, jev=("refuse", {"source": "code"}))]
        cal = decide.calibration(rows, "jev")
        self.assertEqual(cal["n"], 4)
        self.assertAlmostEqual(cal["brier"], (0.01 + 0.01 + 0.36 + 0.0) / 4)
        self.assertEqual([(b["n"], b["answerable"]) for b in cal["bins"]], [(1, 0), (0, 0), (0, 0), (1, 0), (2, 2)])
        self.assertAlmostEqual(cal["bins"][4]["mean"], 0.95)
        self.assertIsNone(decide.calibration(rows, "generator"))

    def test_the_generator_by_confidence(self):
        self.assertEqual(decide.by_confidence(FIXTURE), {"high": (2, 2), "medium": (1, 2), "low": (1, 2)})

    def test_latency_and_rupees_leave_out_an_empty_pools_refusal(self):
        self.assertEqual(sorted(decide.latency(FIXTURE, "generator")), [600.0, 650.0, 700.0, 800.0, 900.0, 1000.0])
        per, priced, unpriced = decide.rupees(FIXTURE, "generator")
        self.assertEqual((priced, unpriced), (6, 0))
        self.assertAlmostEqual(per, 0.009 / 6 * 85)
        per, priced, unpriced = decide.rupees(FIXTURE, "jev")
        self.assertEqual((priced, unpriced), (1, 4))

    def test_the_report_says_jev_is_not_available(self):
        rows = [rec("lk-01", True, rule=("answer", {"score": 0.9})),
                rec("rf-01", False, rule=("refuse", {"score": 0.1, "source": "code"}))]
        for r in rows:
            r["arms"]["jev"] = system_one.result("skipped", source="off", reason=system_one.OFF_REASON)
        buf = io.StringIO()
        decide.report(rows, ["pool       a fixture"], buf)
        out = buf.getvalue()
        self.assertIn("jev        not available: JEV_MODE=off: Jev not available, nothing sent", out)
        self.assertIn("refusal recall  1/1 = 100.0% [20.7%, 100.0%]", out)
        self.assertNotIn(" \n", out)


# ===================================================================== evals/decide.py: the rule arm and the runs
class RuleTest(unittest.TestCase):
    def test_the_evidence_share_and_the_rule(self):
        idf = {"cap": 3.0, "trip": 1.0}
        match = lambda w, t: t.startswith(w)  # noqa: E731
        self.assertEqual(decide.evidence_share([{"text": "The CAP on travel"}], idf, match), 0.75)
        self.assertEqual(decide.evidence_share([{"text": "trips"}, {"text": "caps"}], idf, match), 1.0)
        self.assertEqual(decide.evidence_share([], {}, match), 0.0)
        empty = decide.rule_arm([], 0.42, 0.5)
        self.assertEqual((empty["verdict"], empty["source"], empty["score"]), ("refuse", "code", 0.42))
        self.assertEqual(decide.rule_arm(PASSAGES, 0.5, 0.5)["verdict"], "answer")
        self.assertEqual(decide.rule_arm(PASSAGES, 0.49, 0.5)["verdict"], "refuse")
        self.assertEqual(decide.rule_arm(PASSAGES, 0.49, 0.5, gated=True)["verdict"], "answer")   # the lane's gate said so
        self.assertEqual(decide.rule_arm(PASSAGES, 0.9, 0.5)["cost_usd"], 0.0)


class GeneratorPriceTest(unittest.TestCase):
    """The generator arm's price: /v1/query's cost_usd when it carries one (the gateway's), else a Gemini answer's
    tokens at shared/prices.py's list price, whatever profile this shell is on. No tokens, no price: never a guess."""

    def arm(self, **fields):
        body = {"answer": "...", "citations": [], "answerable": True, "confidence": "high", "model": "gemini-3.6-flash",
                "backend": "vertex", "cost_usd": None, "tokens_in": 1000, "tokens_out": 200, "stages": {"pool": 20}}
        body.update(fields)
        return decide.generator_live("q", "acme", types.SimpleNamespace(ask=lambda question, tenant: (200, body, 900)))

    def test_a_gemini_answer_is_priced_from_its_tokens(self):
        self.assertAlmostEqual(self.arm()["cost_usd"], (1000 * 1.50 + 200 * 7.50) / 1e6)
        with patch.object(decide.prices, "PROFILE", "local"):          # the lane answered, not this shell's profile
            self.assertAlmostEqual(self.arm()["cost_usd"], 0.003)
            self.assertEqual(decide.prices.PROFILE, "local")
        self.assertEqual(self.arm(cost_usd=0.0012)["cost_usd"], 0.0012)  # the gateway's own price stands
        self.assertIsNone(self.arm(tokens_in=None)["cost_usd"])
        self.assertEqual(self.arm(tokens_in=None)["verdict"], "answer")


class FakeLane:
    """The deployed API, stood in for: a pool and a /v1/query answer per question and tenant. (An isolation row asks
    another tenant's question, so the question alone names no row; lk-06 and vr-01 are one question to one tenant,
    both answerable.)"""
    name = "lane"
    EMPTY = {"iso-04", "rf-04"}

    def __init__(self, golden, fail=()):
        self.rows = {(r["question"], r["tenant"]): r for r in golden}
        self.fail, self.asked = set(fail), []

    def pool(self, question, tenant, top_k):
        row = self.rows[(question, tenant)]
        if row["id"] in self.EMPTY:
            return {"passages": [], "answerable": False}
        return {"passages": [{"n": 1, "chunk_id": f"{tenant}:doc#1", "source_uri": f"gs://documind-ai-YOUR-ID-uploads/{tenant}/d.md",
                              "text": row["question"]}], "answerable": True}

    def ask(self, question, tenant):
        row = self.rows[(question, tenant)]
        self.asked.append(row["id"])
        if row["id"] in self.fail:
            return 500, {}, 30000
        return 200, {"answer": "...", "citations": [], "answerable": row["answerable"], "confidence": "high",
                     "model": "gemini-3.6-flash", "backend": "vertex", "cost_usd": 0.0012, "tokens_in": 800,
                     "tokens_out": 40, "stages": {"pool": 20}}, 1500


class LaneTest(unittest.TestCase):
    """decide.Lane, the deployed API's client, with gcloud, the token and both routes stood in for."""

    def test_the_api_and_the_account_come_from_the_project(self):
        number = str(10 ** 11)                     # built here: a literal would read as a real project number
        a = decide.parse_args(["--project", "documind-ai-YOUR-ID", "--region", "us-central1"])
        with patch.object(decide.subprocess, "run", lambda *args, **kw: types.SimpleNamespace(stdout=number + "\n")):
            lane = decide.Lane.from_args(a)
        self.assertEqual(lane.api_url, "https://documind-api-" + number + ".us-central1.run.app")
        self.assertEqual((lane.audience, lane.account), (lane.api_url, "documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com"))
        def no_gcloud(*args, **kw):
            raise FileNotFoundError("gcloud")

        for broken in (lambda *args, **kw: types.SimpleNamespace(stdout=""), no_gcloud):
            with patch.object(decide.subprocess, "run", broken), self.assertRaises(SystemExit):
                decide.Lane.from_args(a)

    def test_the_token_the_pool_and_the_answer(self):
        minted = []
        lane = decide.Lane("https://documind-api-NUMBER.us-central1.run.app/", "https://documind-api-NUMBER.us-central1.run.app",
                           "documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
                           minter=lambda account, audience: minted.append((account, audience)) or "token-1")
        dt = decide._tools()
        got = {}

        def retrieve(question, tenant_id, top_k, passages):
            got.update(question=question, tenant=tenant_id, top_k=top_k, passages=passages, url=dt.RAG_API_URL,
                       who=os.environ.get("DOCUMIND_IMPERSONATE_SA"))
            return {"passages": [], "answerable": False}

        env = {k: v for k, v in os.environ.items() if k not in ("DOCUMIND_ID_TOKEN", "DOCUMIND_IMPERSONATE_SA")}
        with patch.dict(os.environ, env, clear=True), no_network(), \
                patch.multiple(dt, PROFILE="local", RAG_API_URL=dt.RAG_API_URL, retrieve=retrieve, _id_token=lambda aud: "id"), \
                patch.object(decide, "ask", lambda *args: (200, {"args": args}, 5)):
            self.assertEqual(lane.pool("q", "acme", 5), {"passages": [], "answerable": False})
            self.assertEqual(got, {"question": "q", "tenant": "acme", "top_k": 5, "passages": True,
                                   "url": "https://documind-api-NUMBER.us-central1.run.app",
                                   "who": "documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com"})
            self.assertEqual(dt.PROFILE, "gcp")                    # whatever DOCUMIND_PROFILE the shell had
            status, body, ms = lane.ask("q", "acme")
            lane.ask("q2", "zeta")
        self.assertEqual(body["args"][:3], ("https://documind-api-NUMBER.us-central1.run.app", "q", "acme"))
        self.assertEqual(body["args"][4], "token-1")
        self.assertEqual(len(minted), 1)                           # one token a run, until it is 45 minutes old
        with patch.dict(os.environ, {"DOCUMIND_ID_TOKEN": "given"}):
            self.assertEqual(lane.token(), "given")

    def test_no_token_stops_the_run_and_a_bad_reply_is_an_error_row(self):
        dt = decide._tools()
        lane = decide.Lane("https://documind-api-NUMBER.us-central1.run.app", "https://documind-api-NUMBER.us-central1.run.app", None)

        def cannot(aud):
            raise RuntimeError("no credential")

        with patch.dict(os.environ, {}), no_network(), \
                patch.multiple(dt, PROFILE=dt.PROFILE, RAG_API_URL=dt.RAG_API_URL, _id_token=cannot), \
                self.assertRaises(SystemExit) as e:
            lane.pool("q", "acme", 5)
        self.assertIn("no ID token for /v1/passages", str(e.exception))

        def not_json(*args, **kw):
            raise ValueError("Expecting value")

        with patch.dict(os.environ, {}), no_network(), \
                patch.multiple(dt, PROFILE=dt.PROFILE, RAG_API_URL=dt.RAG_API_URL, _id_token=lambda aud: "id", retrieve=not_json):
            self.assertEqual(lane.pool("q", "acme", 5), {"error": "/v1/passages: ValueError: Expecting value"})


class RunTest(unittest.TestCase):
    def setUp(self):
        guard = patch.object(decide.subprocess, "run", never)      # gcloud is never run here
        guard.start()
        self.addCleanup(guard.stop)

    def run_decide(self, argv, **kw):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = decide.run(decide.parse_args(argv), out=out, **kw)
        return code, out.getvalue(), err.getvalue()

    def test_usage_errors(self):
        for argv, mode in ((["--local", "--from", "x.json"], None), (["--local", "--generator", "live"], None),
                           (["--generator", "recorded"], None), (["--local"], "sometimes")):
            with jev(mode):
                self.assertEqual(self.run_decide(argv)[0], 2, argv)
        with jev(None), patch.dict(os.environ, {"PROJECT": "", "GOOGLE_CLOUD_PROJECT": ""}):
            code, _, err = self.run_decide(["--limit", "1"])         # no lane named: no --project, no --api-url
        self.assertEqual(code, 2)
        self.assertIn("--project", err)

    def test_the_rs_0_lane_end_to_end_and_its_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = os.path.join(tmp, "run.json"), os.path.join(tmp, "again.json")
            with jev(None), no_network():
                code, out, _ = self.run_decide(["--local", "--tenant", "globex", "--save", first])
                code2, out2, _ = self.run_decide(["--from", first, "--save", second])
                code3, _, err3 = self.run_decide(["--from", first, "--generator", "live"])
            run = json.loads(Path(first).read_text(encoding="utf-8"))
            again = json.loads(Path(second).read_text(encoding="utf-8"))
        self.assertEqual((code, code2, code3), (0, 0, 2))
        self.assertIn("holds the local lane's pools", err3)       # a local pool and the lane's generator: two pools
        self.assertIn("generator  not available: the saved run is a --local run", out2)
        self.assertIn("rows       8 golden rows: 2 answerable, 6 not", out)
        self.assertIn("generator  not available: --local has no lane", out)
        self.assertIn("jev        not available: JEV_MODE=off: Jev not available, nothing sent", out)
        self.assertEqual((run["kind"], run["pool"], run["jev_mode"], len(run["rows"])), ("decide-run", "local", "off", 8))
        self.assertEqual(again["pool"], "file")
        self.assertIn(f"saved in {first}", out2)
        self.assertFalse([p for r in run["rows"] for p in r["pool"]["passages"] if "source_uri" in p])
        verdicts = lambda run: {r["id"]: r["arms"]["rule"]["verdict"] for r in run["rows"]}  # noqa: E731
        # the rule's refusals are the local lane's own: an empty pool wherever its gate refused
        self.assertEqual({k for k, v in verdicts(run).items() if v == "refuse"},
                         {r["id"] for r in run["rows"] if not r["pool"]["passages"]})
        self.assertEqual(verdicts(again), verdicts(run))

    def test_a_live_run_with_jev_live_sends_only_the_any_tenants(self):
        golden = decide.load_golden()
        lane = FakeLane(golden, fail={"lk-02"})
        sent, calls = [], []
        real_live = system_one._live

        def transport(payload):
            sent.append(payload["question"])
            return 200, {}

        def live(question, passages, tenant, policy_for=None):     # what each row's live decision sent, by tenant
            before = len(sent)
            res = real_live(question, passages, tenant, policy_for)
            calls.append((tenant, len(sent) - before, res["source"]))
            return res

        policy = {"acme": "any", "zeta": "any", "globex": "in"}
        with jev("live"), no_network(), patch.object(system_one, "_request", transport), \
                patch.object(system_one, "_live", live), \
                patch.object(system_one, "_parse", lambda s, b: {"verdict": "answer", "score": 0.7, "model": "jev-test",
                                                                 "request_id": "r", "tokens": {"input": 500, "output": 0}}):
            code, out, _ = self.run_decide(["--api-url", "https://documind-api-NUMBER.us-central1.run.app"], lane=lane,
                                           policy_for=lambda t: policy[t], idf=lambda q, t: {"word": 1.0})
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 63)                                    # 65 rows, less the 2 empty pools
        self.assertEqual({(t, n, src) for t, n, src in calls if t == "globex"}, {("globex", 0, "policy")})
        self.assertEqual({(n, src) for t, n, src in calls if t != "globex"}, {(1, "live")})
        self.assertEqual(sum(t == "globex" for t, _, _ in calls), 8)        # globex's 8 rows: none sent
        self.assertEqual(len(sent), 55)                                     # acme's and zeta's 57, less 2 empty pools
        self.assertEqual(sorted(sent), sorted(r["question"] for r in golden
                                              if r["tenant"] != "globex" and r["id"] not in FakeLane.EMPTY))
        self.assertFalse(FakeLane.EMPTY & set(lane.asked))                  # an empty pool: nobody asked
        self.assertIn("rows       65 golden rows: 47 answerable, 18 not", out)
        self.assertIn("data_region acme any, globex in, zeta any", out)
        self.assertIn("errors are not refusals: 1 left out (HTTP 500)", out)
        self.assertIn("kappa against the generator", out)

    def test_jev_live_before_pr_c_errors_on_every_row_sent_and_exits_1(self):
        golden = decide.load_golden()
        with jev("live"), no_network():
            code, out, _ = self.run_decide(["--api-url", "https://documind-api-NUMBER.us-central1.run.app", "--tenant", "zeta"],
                                           lane=FakeLane(golden), policy_for=lambda t: "any", idf=lambda q, t: {})
        self.assertEqual(code, 1)
        self.assertIn("jev        not available: TypeSafe adapter not configured (PR 2.6-C)", out)

    def test_no_key_on_the_command_line_and_the_make_target(self):
        self.assertFalse([k for k in vars(decide.parse_args([])) if "key" in k])
        mk = (KIT / "mk" / "retrieval.mk").read_text(encoding="utf-8")
        recipe = mk.split("\ndecide: guard-project\n", 1)[1].split("\n\n", 1)[0]
        self.assertEqual(recipe.strip("\n"), "\tJEV_MODE=$(JEV_MODE) $(PY) evals/decide.py --project $(PROJECT) "
                                              "--region $(REGION) $(DECIDE_ARGS)")
        self.assertIn("\nJEV_MODE ?= off\n", mk)
        makefile = (KIT / "Makefile").read_text(encoding="utf-8")
        phony = makefile[makefile.index(".PHONY:"):makefile.index("# ---------- the module files")].replace("\\", " ").split()
        self.assertIn("decide", phony)
        self.assertIn("| `retrieval.mk` | `decide` |", (KIT / "mk" / "README.md").read_text(encoding="utf-8"))

    def test_the_new_files_are_listed(self):
        # An UNOWNED.md row until a lesson page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = (KIT / "UNOWNED.md").read_text(encoding="utf-8"), (KIT / "INDEX.md").read_text(encoding="utf-8")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        for f in ("shared/system_one.py", "evals/decide.py", "evals/tests/test_decide.py", "mk/retrieval.mk",
                  "evals/system_one/recorded.jsonl"):
            self.assertTrue(f"`{f}`" in unowned or f in quoted, f)


if __name__ == "__main__":
    unittest.main()
