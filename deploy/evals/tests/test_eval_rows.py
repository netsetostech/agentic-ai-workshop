"""Offline tests for run_eval.py's row helpers (W2-A): row_verdict() against live()'s own inline rule, quote_check()'s
five verdicts and the generator's "..." repair, anchors_found(), the request passages() sends, and the
DOCUMIND_EVAL_PASSAGES switch - off, nothing printed changes; on, two [info] lines and each row's checks.

Run with ``python -m unittest discover -s evals/tests -p test_eval_rows.py`` from deploy/. Stdlib only: CI runs
evals/tests without rag-api's pins. Nothing reaches a network - a stub stands in for the API, as lesson 4.2's build
does, and urlopen is replaced where passages() is called itself. The passages are the kit's corpus cut by the kit's
own chunker (shared/documind_corpus.py), with ids minted the way the ingest worker mints them.
"""
from __future__ import annotations

import contextlib
import copy
import functools
import gc
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch
import warnings

EVALS = Path(__file__).resolve().parents[1]
KIT = EVALS.parent


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rv = load(EVALS / "run_eval.py", "run_eval_under_test")
chunker = load(KIT / "shared" / "documind_corpus.py", "documind_corpus_under_test")

GOLDEN = rv.load_golden()
BY_ID = {r["id"]: r for r in GOLDEN}
CORPUS = rv.load_corpus()
REAL = {s["slug"] for s in json.loads((EVALS / "real_sources.json").read_text(encoding="utf-8"))}
# The synthetic documents alone: the Acts are most of the corpus's 3 MB, and live() collapses the whitespace of all of it
# on every run. The rule does not care how big the corpus is; quote support still goes both ways over these.
SYNTHETIC = {t: {name: text for name, text in docs.items() if name.rsplit(".", 1)[0] not in REAL} for t, docs in CORPUS.items()}
MANIFEST = rv.load_manifest_objects()
API, MEMBER, OUTSIDER = "http://stub.invalid", "eval@documind.in", "outsider@not-a-tenant.invalid"
CUR, OLD = "c" * 64, "d" * 64          # a version the ledger lists as current, and one it has retired
ENV_KEYS = ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "DOCUMIND_USER_EMAIL", "DOCUMIND_OUTSIDER_EMAIL",
            "DOCUMIND_EVAL_PASSAGES")
CITE_FIELDS = ("chunk_id", "source_uri", "page", "kind", "quote", "score")     # what a record keeps of a citation
INDEXED = {}                           # every media file make ingest-corpus uploads, by kind: the lane after lesson 7.5
for _t, _names in MANIFEST.items():
    for _n in _names:
        _kind = rv.MEDIA_KINDS.get(os.path.splitext(_n)[1].lower())
        if _kind:
            INDEXED.setdefault(_t, {}).setdefault(_kind, set()).add(_n.rsplit("/", 1)[-1])


@functools.lru_cache(maxsize=None)
def text_of(full: bool) -> dict:
    """live()'s text_of for a corpus: each tenant's haystack() with its whitespace collapsed, for quote support."""
    corpus = CORPUS if full else SYNTHETIC
    return {t: re.sub(r"\s+", " ", rv.haystack(corpus, t)) for t in corpus}


def normal(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def handbook_pool() -> list[dict]:
    """acme's handbook as /v1/passages would return it: cut by the kit's chunker (the worker's two rules), each passage
    in the route's shape, ids as the worker mints them - {tenant}:{sha256}#{i}, which carry no slug and no clause id."""
    raw = (EVALS / "corpus" / "acme" / "hr_policy_2026.md").read_bytes()
    doc = {"slug": "hr_policy_2026", "doc_type": "policy", "text": raw.decode("utf-8"),
           "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"}
    sha = hashlib.sha256(raw).hexdigest()
    return [{"n": i, "chunk_id": f"acme:{sha}#{i}", "source_uri": c["source_uri"], "page": c["page_start"],
             "doc_type": c["doc_type"], "kind": c["kind"], "section": c.get("section"), "text": c["text"]}
            for i, c in enumerate(chunker.chunk_document(doc, "acme"))]


HANDBOOK = handbook_pool()


def chunk(code: str) -> dict:
    """The handbook's passage for one clause: its section title starts with the code."""
    return next(p for p in HANDBOOK if (p["section"] or "").startswith(code))


def repaired(said: str, limit: int = 200) -> str:
    """generator._draft()'s repair of an over-long quote, as written there (pinned in KitAssumptionsTest)."""
    return said[: limit - 3].rstrip() + "..." if len(said) > limit else said


def resolved(model_quote: str, passage: dict) -> str:
    """The quote resolve() hands on (pinned in KitAssumptionsTest): the model's, else the chunk's first 500 characters."""
    return (model_quote or passage.get("text", ""))[:500]


@contextlib.contextmanager
def environ(**values):
    """The run's environment: no token, no switch, nothing from the shell running the tests, then `values`."""
    with patch.dict(os.environ):
        for k in ENV_KEYS:
            os.environ.pop(k, None)
        os.environ.update(values)
        yield


# ------------------------------------------------------------------ a stub API: each row answered the way an outcome says
ANSWERABLE = ("ok", "refused", "nofig", "badcite", "badfolder", "retired", "unlisted", "nocite", "unsupported", "multi",
              "kind", "leak", "stale", "long")
UNANSWERABLE = ("ok", "answered", "leak", "leakrefusal")
FAILED = ("err", "transport", "denied", "bad", "malcite")
OUTCOMES = tuple(dict.fromkeys(ANSWERABLE + UNANSWERABLE + FAILED))


def reply(row: dict, outcome: str) -> tuple[int, dict]:
    """(status, body) for one row. An outcome that does not apply to the row - a leak on a row with no
    must_not_contain, a refusal on an unanswerable row - is answered as "ok"."""
    t, mc, mnc = row["tenant"], row.get("must_contain", []), row.get("must_not_contain", [])
    other = "globex" if t != "globex" else "acme"
    fig = " and ".join(mc)
    obj = sorted(MANIFEST[t])[0].split("/", 1)[1]

    def cite(quote=None, tenant=t, folder=t, sha=CUR, name=obj, kind=row.get("must_cite_kind") or "text"):
        c = {"chunk_id": f"{tenant}:{sha}#3", "source_uri": f"gs://documind-ai-YOUR-ID-uploads/{folder}/{name}", "page": 2,
             "quote": quote or (mc[0] if mc else "the documents"), "score": 0.8, "kind": kind}
        if kind != "text":
            c["media_url"] = "https://storage.googleapis.com/signed-and-expiring"
        return c

    def body(answer, cites, answerable):
        return 200, {"answer": answer, "citations": cites, "answerable": answerable,
                     "confidence": "high" if answerable else "low", "model": "stub", "backend": "vertex", "cache_hit": "none",
                     "stages": {"retrieve_ms": 3, "rerank_ms": 2, "generate_ms": 9, "pool": 6}}

    if outcome == "err":
        return 500, {}
    if outcome == "transport":
        return 0, {"error": "TimeoutError"}
    if outcome == "denied":
        return 403, {}
    if outcome == "bad":
        return 200, {}
    if outcome == "malcite":
        return body(f"{fig} [1].", [{"chunk_id": f"{t}:{CUR}#3", "source_uri": "", "quote": "x"}], True)
    if row["answerable"]:
        table = {"ok": (f"{fig} [1].", [cite()], True),
                 "refused": ("The documents do not say.", [], False),
                 "nofig": ("The documents cover this [1].", [cite()], True),
                 "badcite": (f"{fig} [1].", [cite(tenant=other)], True),
                 "badfolder": (f"{fig} [1].", [cite(folder=other)], True),
                 "retired": (f"{fig} [1].", [cite(sha=OLD)], True),
                 "unlisted": (f"{fig} [1].", [cite(name="not_in_the_manifest.md")], True),
                 "nocite": (f"{fig}.", [], True),
                 "unsupported": (f"{fig} [1].", [cite(quote="words no document of this tenant holds")], True),
                 "multi": (f"{fig} [1] [2].", [cite(), cite(tenant=other)], True),
                 "long": (f"{fig} [1]. " + "The clause says more, and the answer says it at length. " * 15, [cite()], True)}
        if row.get("must_cite_kind"):
            table["kind"] = (f"{fig} [1].", [cite(kind="text")], True)
        if mnc:
            table["leak"] = (f"{fig}, and {mnc[0]} [1].", [cite()], True)
            table["stale"] = (f"{mnc[0]} [1].", [cite()], True)
    else:
        table = {"ok": ("The documents do not say.", [], False),
                 "answered": ("Here is what the documents say [1].", [cite()], True)}
        if mnc:
            table["leak"] = (f"{mnc[0]} [1].", [cite()], True)
            table["leakrefusal"] = (f"The documents do not say whether it is {mnc[0]}.", [], False)
    return body(*table.get(outcome, table["ok"]))


def forbid(*a, **k):
    raise AssertionError("passages() was called with DOCUMIND_EVAL_PASSAGES off")


def run_live(pick, current=lambda tenant: {CUR}, passages=forbid, report=None, full=False,
             media=lambda tenant: INDEXED.get(tenant, {}), **env):
    """live() over the stub, every golden row. pick(i, row) names the outcome; current(tenant) is what the ledger
    answers (a set of shas, or None when GET /v1/sources is down); media(tenant) the media files it lists as indexed,
    by kind. Returns (rc, stdout, report, [(row, status, body)])."""
    sent = []

    def ask(api_url, question, tenant, email, token, retries=1):
        if email == OUTSIDER:
            return 403, {}, 4                       # check_isolation(): every non-member is refused
        row = GOLDEN[len(sent)]
        assert (row["question"], row["tenant"]) == (question, tenant), (row["id"], question)
        status, body = reply(row, pick(len(sent), row))
        sent.append((row, status, copy.deepcopy(body)))
        return status, body, 11

    corpus = CORPUS if full else SYNTHETIC
    with tempfile.TemporaryDirectory() as tmp:
        path = report or os.path.join(tmp, "report.json")
        out = io.StringIO()
        with environ(**env), patch.object(rv, "ask", ask), patch.object(rv, "load_corpus", lambda: corpus), \
                patch.object(rv, "fetch_current_shas", lambda api_url, tenant, token: current(tenant)), \
                patch.object(rv, "fetch_media_names", lambda api_url, tenant, token: media(tenant)), \
                patch.object(rv, "passages", passages), contextlib.redirect_stdout(out):
            rc = rv.live(API, report=path, golden=GOLDEN)
        with open(path, encoding="utf-8") as f:
            return rc, out.getvalue(), json.load(f), sent


# ------------------------------------------------------------------ row_verdict(): live()'s rule, one row at a time
REASONS = {        # every reason live() can give a row, and how to recognise it
    "a failed request": lambda w: w.startswith("HTTP "),
    "a malformed body": lambda w: w.startswith("answer missing"),
    "a malformed citation": lambda w: w.startswith("citation 0 lacks"),
    "a refusal": lambda w: w == "refused",
    "no citation": lambda w: w == "answered without a citation",
    "no figure cited": lambda w: w == "cited no figure",
    "no segment cited": lambda w: w == "cited no segment",
    "no figure said": lambda w: w.startswith("answered without ["),
    "another tenant's chunk": lambda w: w.startswith("chunk ") and " is not " in w,
    "another tenant's folder": lambda w: " is not under " in w,
    "a retired version": lambda w: "a version the ledger does not list as current" in w,
    "a leak or a stale figure": lambda w: w.startswith("answer contained "),
    "an answer to refuse": lambda w: w == "answered, should refuse",
    "a pass": lambda w: w == "",
}


class RowVerdictTest(unittest.TestCase):
    """row_verdict() is live()'s per-row judgment pulled out as a function. live() keeps its inline copy, because lessons
    quote it, so the two are held equal here: every golden row, every kind of reply the gate distinguishes."""

    def scenarios(self):
        """(name, pick, ledger down too, the whole corpus): every row ok; each outcome on every row it applies to; two
        mixtures, one of them against the whole corpus, Acts included."""
        yield "every row ok", lambda i, row: "ok", True, False
        for outcome in OUTCOMES[1:]:
            yield outcome, (lambda o: lambda i, row: o)(outcome), outcome == "retired", False
        yield "mixed", lambda i, row: OUTCOMES[i % len(OUTCOMES)], True, False
        yield "mixed, the whole corpus", lambda i, row: OUTCOMES[(7 * i + 3) % len(OUTCOMES)], False, True

    def assert_equal_to_live(self, name, pick, current, full):
        rc, out, report, sent = run_live(pick, current, full=full)
        self.assertEqual(len(report["records"]), len(GOLDEN), name)
        verdicts = []
        for (row, status, body), rec in zip(sent, report["records"]):
            v = rv.row_verdict(row, status, body, current(row["tenant"]), MANIFEST, text_of(full).get(row["tenant"], ""))
            self.assertEqual((v["outcome"], v["pass"], v["why"]), (rec["outcome"], rec["pass"], rec["why"]), f"{name}: {row['id']}")
            verdicts.append(v)
        # Everything live() counts, counted again from the verdicts alone: the rates (isolation is check_isolation()'s,
        # not a row's), quote support, the leak and stale lines, and the required rows that did not pass.
        n = sum(r["answerable"] for r in GOLDEN)
        answered = sum(v["answered"] for v in verdicts)
        cited = sum(v["cited"] for v in verdicts)
        kinds = [v["kind_ok"] for v in verdicts if v["kind_ok"] is not None]
        want = {"request_success_rate": sum(v["outcome"] == "ok" for v in verdicts) / len(GOLDEN),
                "answerable_rate": answered / n,
                "citation_rate": cited / max(answered, 1),
                "citation_valid_rate": sum(bool(v["cited"] and v["valid"]) for v in verdicts) / max(cited, 1),
                "must_contain_rate": sum(v["contained"] is True for v in verdicts) / max(answered, 1),
                "correct_rate": sum(bool(v["answered"] and v["pass"]) for v in verdicts) / n,
                "refusal_rate": sum(v["refused"] for v in verdicts) / (len(GOLDEN) - n),
                "media_kind_rate": sum(kinds) / max(len(kinds), 1),
                "isolation_403_rate": report["scores"]["isolation_403_rate"]}
        self.assertEqual(want, report["scores"], name)
        supported = [v["supported"] for v in verdicts if v["cited"]]
        self.assertEqual(report["quote_support_rate"], sum(supported) / len(supported) if supported else None, name)
        self.assertEqual(report["leaks"], [line for v in verdicts for line in v["leaks"]], name)
        self.assertEqual(report["stale"], [line for v in verdicts for line in v["stale"]], name)
        required = set(rv.load_required())
        self.assertEqual(report["required_failed"], [f"{r['id']}: {v['why'] or 'failed'}" for r, v in zip(GOLDEN, verdicts)
                                                     if r["id"] in required and not v["pass"]], name)
        return rc, verdicts

    def test_equal_to_live_over_every_golden_row_and_every_reply(self):
        whys, supported = [], set()
        for name, pick, ledger_down_too, full in self.scenarios():
            ledgers = [("ledger up", lambda tenant: {CUR})] + ([("ledger down", lambda tenant: None)] if ledger_down_too else [])
            for ledger, current in ledgers:
                with self.subTest(scenario=name, ledger=ledger):
                    rc, verdicts = self.assert_equal_to_live(f"{name}, {ledger}", pick, current, full)
                    if name == "every row ok":
                        self.assertEqual(rc, 0)                      # the stub's right answers clear every threshold
                        self.assertTrue(all(v["pass"] for v in verdicts))
                    whys += [v["why"] for v in verdicts]
                    supported |= {v["supported"] for v in verdicts}
        reached = {label for label, seen in REASONS.items() if any(seen(w) for w in whys)}
        self.assertEqual(reached, set(REASONS))                     # every branch of the rule was taken at least once
        self.assertEqual(supported, {True, False, None})            # and quote support went both ways

    def test_failed_requests_and_the_benchs_call(self):
        row = BY_ID["lk-06"]
        self.assertEqual(rv.row_verdict(row, 503, {})["why"], "HTTP 503")
        self.assertEqual(rv.row_verdict(row, 401, {})["outcome"], "denied")
        self.assertEqual(rv.row_verdict(row, 0, {"error": "URLError"})["why"], "HTTP 0 URLError")
        self.assertEqual(rv.row_verdict(row, 200, {"answer": "x"})["outcome"], "malformed")
        # the prompt bench's call: an answer it generated itself, no ledger to ask and no manifest
        status, body = reply(row, "ok")
        v = rv.row_verdict(row, status, body)
        self.assertEqual((v["pass"], v["why"], v["answered"], v["cited"], v["valid"], v["contained"], v["kind_ok"]),
                         (True, "", True, True, True, True, None))
        status, body = reply(row, "nofig")
        self.assertEqual(rv.row_verdict(row, status, body)["why"], "answered without ['60']")


# ------------------------------------------------------------------ a media row asks for its kind once the media is indexed
class MediaAsIndexedTest(unittest.TestCase):
    """mm-03 asks for a segment of townhall_2026_q1.mp4, which lesson 7.5 builds. Before then every full live gate
    failed on a required row no answer could pass (22 October 2026). Now a media row asks for its figure or segment
    only while the tenant's ledger lists a current file of that kind named after the row's document; until then it is
    judged as the text lookup it also is, and the gate says so on an [info] line."""
    FIGURES = {"figure": INDEXED["acme"]["figure"]}           # the lane before lesson 7.5: the pictures, no video

    def test_a_row_without_its_media_is_judged_on_its_words(self):
        mm03 = BY_ID["mm-03"]
        got = rv.as_media_stands(mm03, self.FIGURES)
        self.assertNotIn("must_cite_kind", got)
        self.assertEqual(got["media_absent"], "segment")
        self.assertEqual({k: v for k, v in got.items() if k != "media_absent"},
                         {k: v for k, v in mm03.items() if k != "must_cite_kind"})
        self.assertEqual(mm03["must_cite_kind"], "segment", "the golden row itself is not changed")
        for row in (BY_ID["mm-01"], BY_ID["mm-02"], BY_ID["lk-06"]):
            self.assertIs(rv.as_media_stands(row, self.FIGURES), row)       # a figure that is there; no media asked
        self.assertIs(rv.as_media_stands(mm03, INDEXED["acme"]), mm03)       # the video indexed: the segment is asked
        self.assertIs(rv.as_media_stands(mm03, None), mm03)                  # the ledger unread: asked, as before
        self.assertIn("media_absent", rv.as_media_stands(mm03, {"segment": {"standup_2026_q2.mp4"}}),
                      "another document's video is not the town hall's")

    def test_the_ledger_read_for_current_media(self):
        rows = {"sources": [{"name": "acme/townhall_2026_q1.mp4", "status": "indexed"},
                            {"name": "acme/annual_report_2026_fig3.png", "status": "superseded"},
                            {"name": "acme/whiteboard_arch.PNG", "status": "indexed"},
                            {"name": "acme/hr_policy_2026.md", "status": "indexed"},
                            {"name": "acme/payment_of_bonus_act_1965_p30.png", "status": "failed"}]}
        seen = []

        def urlopen(req, timeout=None):
            seen.append((req.full_url, req.get_header("Authorization")))
            return FakeResponse(rows)
        with patch.object(rv.urllib.request, "urlopen", urlopen):
            got = rv.fetch_media_names(API + "/", "acme", "tok")
        self.assertEqual(got, {"segment": {"townhall_2026_q1.mp4"}, "figure": {"whiteboard_arch.PNG"}})
        self.assertEqual(seen, [(f"{API}/v1/sources?tenant_id=acme", "Bearer tok")])

        def down(req, timeout=None):
            raise urllib.error.URLError("no route")
        with patch.object(rv.urllib.request, "urlopen", down):
            self.assertIsNone(rv.fetch_media_names(API, "acme", None))

    def test_the_gate_before_and_after_the_video(self):
        pick = lambda i, row: "kind" if row["id"] == "mm-03" else "ok"     # a text citation: there is no segment to cite
        rc, out, report, sent = run_live(pick, media=lambda tenant: self.FIGURES if tenant == "acme" else {})
        self.assertEqual((rc, report["required_failed"]), (0, []), out)
        self.assertIn("[info] mm-03: no segment file of townhall_2026_q1 indexed for acme yet", out)
        self.assertEqual(out.count("[info] mm-0"), 1, "the figures are there, so mm-01 and mm-02 still ask for theirs")
        self.assertEqual(report["scores"]["media_kind_rate"], 1.0)           # two figure rows, both cited a figure
        for row, status, body in sent:
            v = rv.row_verdict(rv.as_media_stands(row, self.FIGURES if row["tenant"] == "acme" else {}), status, body,
                               {CUR}, MANIFEST, text_of(False).get(row["tenant"], ""))
            self.assertTrue(v["pass"], (row["id"], v["why"]))
        # The video indexed and the same text citation: the row is asked for its segment and holds the gate red.
        rc, out, report, _ = run_live(pick)
        self.assertNotEqual(rc, 0)
        self.assertEqual(report["required_failed"], ["mm-03: cited no segment"])
        self.assertNotIn("[info] mm-03", out)


# ------------------------------------------------------------------ quote_check(): one verdict per citation
class QuoteCheckTest(unittest.TestCase):
    NP03 = "A confirmed employee at grade E3 or above serves a notice period of 60 days."

    def setUp(self):
        self.pool = [chunk("NP-03"), chunk("PB-02"), chunk("GEN-000"), chunk("GEN-001")]

    def check(self, code, quote, pool="setup"):
        return rv.quote_check({"chunk_id": chunk(code)["chunk_id"], "quote": quote}, self.pool if pool == "setup" else pool)

    def test_own_with_the_whitespace_collapsed_and_the_case_folded(self):
        self.assertEqual(self.check("NP-03", self.NP03), "own")
        self.assertIn("Notice runs\nfrom the date", chunk("NP-03")["text"])        # the source breaks the line here
        self.assertEqual(self.check("NP-03", "NOTICE RUNS from the date the resignation is acknowledged in writing."), "own")

    def test_own_wins_when_the_words_are_in_more_than_one_passage(self):
        boiler = "It applies to all employees and to contractors working on ACME premises or systems."
        self.assertIn(normal(boiler), normal(chunk("GEN-000")["text"]))
        self.assertEqual(self.check("GEN-001", boiler), "own")

    def test_elsewhere_is_real_words_under_the_wrong_source(self):
        self.assertEqual(self.check("PB-02", self.NP03), "elsewhere")

    def test_absent_is_words_no_passage_holds(self):
        self.assertEqual(self.check("NP-03", self.NP03.replace("60 days", "90 days")), "absent")   # revision 2's figure
        # strict, as judge_citations is: only the generator's trailing dots are dropped, never a model's own elision
        self.assertEqual(self.check("NP-03", "A confirmed employee ... serves a notice period of 60 days."), "absent")
        self.assertEqual(self.check("NP-03", "..."), "absent")

    def test_substituted_is_resolve_filling_in_for_a_missing_quote(self):
        for code, length in (("GEN-000", 500), ("NP-03", len(chunk("NP-03")["text"]))):   # 593 characters cut at 500; 234 whole
            quote = resolved("", chunk(code))
            self.assertEqual(len(quote), length)
            self.assertIn(normal(quote), normal(chunk(code)["text"]))       # the words ARE in the passage ...
            self.assertEqual(self.check(code, quote), "substituted")       # ... but the model quoted nothing
        self.assertEqual(self.check("NP-03", resolved(self.NP03, chunk("NP-03"))), "own")   # a quote it gave is its own

    def test_unread_is_a_passage_not_read_back(self):
        self.assertEqual(self.check("EXP-12", self.NP03), "unread")          # the words are in the pool, the cited chunk is not
        self.assertEqual(self.check("NP-03", self.NP03, pool=None), "unread")
        self.assertEqual(self.check("NP-03", self.NP03, pool=[]), "unread")
        self.assertEqual(rv.quote_check({"quote": self.NP03}, self.pool), "unread")

    def test_the_generators_repair_is_dropped_before_matching(self):
        said = ("This section restates ACME's standing position on attendance and shift rosters. It applies to all "
                "employees and to contractors working on ACME premises or systems. Where this section conflicts with a "
                "signed statement of work, the statement of work governs for that engagement only and this handbook "
                "governs everywhere else.")
        self.assertIn(normal(said), normal(chunk("GEN-000")["text"]))
        quote = repaired(said)
        self.assertTrue(len(said) > 200 and quote.endswith("...") and len(quote) <= 200)
        self.assertNotIn(normal(quote), normal(chunk("GEN-000")["text"]))  # with the dots, not the document's words
        self.assertEqual(self.check("GEN-000", quote), "own")
        self.assertEqual(self.check("GEN-001", quote), "elsewhere")         # attendance, not grievance: GEN-000's alone
        self.assertEqual(self.check("NP-03", "Notice runs from the date the resignation is acknowledged..."), "own")

    def test_one_verdict_each(self):
        quotes = (self.NP03, "Probation may be extended once", "words in no passage", resolved("", chunk("PB-02")), "")
        seen = {self.check(code, q, pool) for code in ("NP-03", "PB-02", "EXP-12") for q in quotes for pool in ("setup", None)}
        self.assertEqual(seen, set(rv.QUOTE_VERDICTS))
        self.assertEqual(len(rv.QUOTE_VERDICTS), 5)


# ------------------------------------------------------------------ anchors_found(): must_retrieve against the pool
class AnchorsFoundTest(unittest.TestCase):
    def test_the_slug_is_in_the_source_and_the_clause_in_the_text(self):
        row = BY_ID["lk-06"]
        self.assertEqual(row["must_retrieve"], ["NP-03", "hr_policy_2026"])
        np03 = chunk("NP-03")
        self.assertNotIn("NP-03", np03["chunk_id"])                         # the worker's id carries neither
        self.assertNotIn("hr_policy_2026", np03["chunk_id"])
        self.assertEqual(rv.anchors_found(row, [np03]), {"NP-03": True, "hr_policy_2026": True})
        self.assertEqual(rv.anchors_found(row, [chunk("EXP-12"), chunk("PB-02")]), {"NP-03": False, "hr_policy_2026": True})
        moved = dict(np03, source_uri="gs://documind-ai-YOUR-ID-uploads/acme/somewhere_else.md")
        self.assertEqual(rv.anchors_found(row, [moved]), {"NP-03": True, "hr_policy_2026": False})

    def test_an_empty_pool_finds_nothing_and_an_unread_one_is_not_judged(self):
        row = BY_ID["lk-06"]
        self.assertEqual(rv.anchors_found(row, []), {"NP-03": False, "hr_policy_2026": False})
        self.assertIsNone(rv.anchors_found(row, None))
        self.assertEqual(rv.anchors_found(BY_ID["rf-01"], [chunk("NP-03")]), {})       # a refusal row names no anchor

    def test_the_whole_corpus_as_the_pool_finds_every_anchor_the_offline_check_finds(self):
        # check_anchors() passes on the committed corpus (the offline gate says so: SwitchTest runs it); the live rule,
        # handed every document of a tenant as its pool, must find every anchor that tenant's rows name
        for tenant, docs in CORPUS.items():
            pool = [{"chunk_id": f"{tenant}:{CUR}#{i}", "source_uri": f"gs://documind-ai-YOUR-ID-uploads/{tenant}/{name}",
                     "text": text} for i, (name, text) in enumerate(docs.items())]
            every = {"must_retrieve": sorted({a for r in GOLDEN if r["tenant"] == tenant for a in r.get("must_retrieve", [])})}
            found = rv.anchors_found(every, pool)
            self.assertEqual(sorted(a for a, hit in found.items() if not hit), [], tenant)


# ------------------------------------------------------------------ passages(): the route documind_tools calls
class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.payload if isinstance(self.payload, bytes) else json.dumps(self.payload).encode()


class PassagesTest(unittest.TestCase):
    QUESTION = "What is the notice period for a confirmed E3?"

    def call(self, *replies, token="tok", url=API):
        """passages() against a urlopen that plays `replies` in turn: a payload, or an exception to raise."""
        seen = []

        def urlopen(req, timeout=None):
            seen.append((req, timeout))
            r = replies[len(seen) - 1]
            if isinstance(r, Exception):
                raise r
            return FakeResponse(r)

        with patch.object(rv.urllib.request, "urlopen", urlopen), patch.object(rv.time, "sleep") as sleep:
            got = rv.passages(url, self.QUESTION, "acme", MEMBER, token)
        for r in replies:
            if isinstance(r, urllib.error.HTTPError):
                r.close()
        return got, seen, sleep

    def http(self, code):
        return urllib.error.HTTPError(API + "/v1/passages", code, "stub", {}, io.BytesIO(b""))

    def test_the_request_is_asks_body_on_the_passages_route(self):
        pool = [chunk("NP-03"), chunk("PB-02")]
        got, seen, _ = self.call({"passages": pool, "answerable": True, "usage": {}})
        self.assertEqual(got, pool)
        (req, timeout), = seen
        self.assertEqual((req.full_url, req.get_method(), timeout), (API + "/v1/passages", "POST", 90))
        self.assertEqual(json.loads(req.data), {"query": self.QUESTION, "tenant_id": "acme", "top_k": 6})
        self.assertEqual((req.get_header("Content-type"), req.get_header("X-user-email"), req.get_header("Authorization")),
                         ("application/json", MEMBER, "Bearer tok"))
        # byte for byte the body ask() sends to /v1/query: the same retrieval and rerank, so the same pool
        asked = []
        with patch.object(rv.urllib.request, "urlopen", lambda r, timeout=None: asked.append(r) or FakeResponse({})):
            rv._ask_once(API, self.QUESTION, "acme", MEMBER, "tok")
        self.assertEqual((asked[0].full_url, asked[0].data), (API + "/v1/query", req.data))

    def test_no_token_no_bearer_and_one_slash(self):
        _, seen, _ = self.call({"passages": []}, token=None, url=API + "/")
        self.assertIsNone(seen[0][0].get_header("Authorization"))
        self.assertEqual(seen[0][0].full_url, API + "/v1/passages")

    def test_what_comes_back(self):
        self.assertEqual(self.call({"passages": [], "answerable": False})[0], [])            # an empty pool is a pool
        self.assertEqual(self.call({"passages": [chunk("NP-03"), "junk"]})[0], [chunk("NP-03")])
        self.assertIsNone(self.call({"passages": [], "answer": "A person will take this up.", "answerable": False})[0])
        self.assertIsNone(self.call(["not", "an", "object"])[0])
        self.assertIsNone(self.call({"answer": "no passages key"})[0])

    def test_a_4xx_is_an_answer_and_a_5xx_is_asked_once_more(self):
        got, seen, sleep = self.call(self.http(403))
        self.assertEqual((got, len(seen), sleep.call_count), (None, 1, 0))
        got, seen, sleep = self.call(self.http(503), {"passages": [chunk("NP-03")]})
        self.assertEqual((got, len(seen)), ([chunk("NP-03")], 2))
        sleep.assert_called_once_with(2)
        got, seen, _ = self.call(self.http(500), self.http(500))
        self.assertEqual((got, len(seen)), (None, 2))
        got, seen, _ = self.call(TimeoutError(), b"not json")
        self.assertEqual((got, len(seen)), (None, 2))


# ------------------------------------------------------------------ DOCUMIND_EVAL_PASSAGES: off, nothing printed changes
SPECIAL = {"lk-01": "the cited chunk is not in the pool", "lk-02": "no pool", "lk-03": "elsewhere", "lk-04": "absent",
           "lk-05": "substituted", "lk-07": "an anchor missing"}
PICK = {"lk-27": "refused", "jn-06": "nofig", "jn-01": "long"}


def pick_switch(i: int, row: dict) -> str:
    return PICK.get(row["id"], "ok")


def pool_for(row: dict) -> list[dict] | None:
    """The stub pool for one row: the cited chunk holds the quote and the anchors, except on the SPECIAL rows."""
    _, body = reply(row, pick_switch(0, row))
    cite = body["citations"][0] if body["citations"] else {"chunk_id": f"{row['tenant']}:{CUR}#3", "quote": ""}
    cid, quote, anchors = cite["chunk_id"], cite["quote"], " ".join(row.get("must_retrieve", []))
    src = f"gs://documind-ai-YOUR-ID-uploads/{row['tenant']}/a.md"
    case = SPECIAL.get(row["id"])
    if case == "no pool":
        return None
    if case == "the cited chunk is not in the pool":
        return [{"chunk_id": f"{row['tenant']}:{CUR}#9", "source_uri": src, "text": f"{anchors}: {quote}"}]
    if case == "elsewhere":
        return [{"chunk_id": cid, "source_uri": src, "text": anchors}, {"chunk_id": "x#9", "source_uri": src, "text": f"so {quote}."}]
    if case == "absent":
        return [{"chunk_id": cid, "source_uri": src, "text": anchors}]
    if case == "substituted":
        return [{"chunk_id": cid, "source_uri": src, "text": quote}, {"chunk_id": "x#9", "source_uri": src, "text": anchors}]
    if case == "an anchor missing":
        return [{"chunk_id": cid, "source_uri": src, "text": f"{row['must_retrieve'][0]}: {quote}"}]
    return [{"chunk_id": cid, "source_uri": src, "text": f"{anchors}: {quote}"}]


HAYSTACKS = {t: rv.haystack(CORPUS, t) for t in CORPUS}
DEMO_TEXT = rv.load_demo()


def offline(*args, **env) -> tuple[int, str]:
    """main() with no --api-url, as `python evals/run_eval.py` runs it in CI. The corpus, its haystacks and the retired
    versions are read once for the module - the same strings, without rebuilding three tenants' text for every row."""
    real = rv.haystack
    out = io.StringIO()
    with environ(**env), patch.object(sys, "argv", ["run_eval.py", *args]), patch.object(rv, "load_corpus", lambda: CORPUS), \
            patch.object(rv, "haystack", lambda corpus, tenant: HAYSTACKS[tenant] if corpus is CORPUS else real(corpus, tenant)), \
            patch.object(rv, "load_demo", lambda: DEMO_TEXT), contextlib.redirect_stdout(out):
        rc = rv.main()
    return rc, out.getvalue()


class SwitchTest(unittest.TestCase):
    def setUp(self):
        for rid in list(SPECIAL) + list(PICK):
            self.assertTrue(BY_ID[rid]["answerable"], rid)
        self.calls = []
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.report = os.path.join(tmp.name, "report.json")          # one path, so the "report:" line matches too

    def stub_passages(self, api_url, question, tenant, email, token):
        row = next(r for r in GOLDEN if r["answerable"] and r["id"] not in self.calls
                   and (r["question"], r["tenant"]) == (question, tenant))
        self.assertEqual((api_url, email, token), (API, MEMBER, None))
        self.calls.append(row["id"])
        return pool_for(row)

    def test_offline_prints_the_same_whatever_the_switch(self):
        for args in ((), ("--source", "hr_policy_2026.md")):
            rc, out = offline(*args)
            self.assertEqual(rc, 0, out[-400:])
            self.assertTrue(out.startswith("== eval gate: OFFLINE (no credentials, no cost) =="))
            self.assertIn("The golden set is sound.", out)
            self.assertNotIn("quote_passage_rate", out)
            self.assertEqual(offline(*args, DOCUMIND_EVAL_PASSAGES="1"), (rc, out), args)
            self.assertEqual(offline(*args, DOCUMIND_EVAL_PASSAGES="0"), (rc, out), args)

    def test_live_with_the_switch_off_asks_nothing_more_and_prints_nothing_more(self):
        rc, off, report, sent = run_live(pick_switch, report=self.report)          # passages() raises if it is called
        self.assertEqual(run_live(pick_switch, report=self.report, DOCUMIND_EVAL_PASSAGES="0")[:2], (rc, off))
        self.assertNotIn("passage_checks", report)
        self.assertNotIn("quote_passage_rate", off)
        for (row, status, body), rec in zip(sent, report["records"]):
            self.assertFalse({"pool", "anchors"} & set(rec), row["id"])
            self.assertEqual(rec["answer"], body["answer"][:600])
            self.assertEqual(rec["citations"], len(body["citations"]))       # the count, as it always was
            self.assertEqual(rec["cites"], [{k: c.get(k) for k in CITE_FIELDS} for c in body["citations"]])
        recs = {r["id"]: r for r in report["records"]}
        self.assertEqual(len(recs["jn-01"]["answer"]), 600)
        self.assertEqual(recs["mm-01"]["cites"][0]["kind"], "figure")
        self.assertNotIn("media_url", recs["mm-01"]["cites"][0])             # a signed link that expires stays out

    def test_live_with_the_switch_on_reads_the_pools_and_adds_two_lines(self):
        _, off, report_off, _ = run_live(pick_switch, report=self.report)
        _, on, report, _ = run_live(pick_switch, passages=self.stub_passages, report=self.report, DOCUMIND_EVAL_PASSAGES="1")
        answerable = [r["id"] for r in GOLDEN if r["answerable"]]
        self.assertEqual(self.calls, answerable)           # every answerable row once, refused lk-27 included; no other

        answered = len(answerable) - 1                     # lk-27 refused; every other answerable row cites once
        read = answered - 2                                # lk-01's cited chunk is not in its pool; lk-02 has no pool
        own = read - 3                                     # lk-03 elsewhere, lk-04 absent, lk-05 substituted
        asked = sum(len(BY_ID[r]["must_retrieve"]) for r in answerable) - len(BY_ID["lk-02"]["must_retrieve"])
        found = asked - 1                                  # lk-07's second anchor
        self.assertEqual(report["passage_checks"], {
            "rows": len(answerable), "unread_rows": 1,
            "quotes": {"own": own, "elsewhere": 1, "absent": 1, "substituted": 1, "unread": 2},
            "quote_passage_rate": own / read, "anchors_found": found, "anchors": asked, "must_retrieve_recall": found / asked})

        lines = [f"  [info] {'quote_passage_rate':21} {own / read:6.1%}  ({own} of {read} answered rows' quotes in the passage "
                 f"they cite; elsewhere 1, absent 1, substituted 1, unread 2; not a threshold)",
                 f"  [info] {'must_retrieve_recall':21} {found / asked:6.1%}  ({found} of {asked} anchors in the pool "
                 f"/v1/passages returned, over {len(answerable) - 1} answerable rows; 1 pool(s) could not be read; "
                 f"not a threshold)"]
        off_lines = off.splitlines()
        at = next(i for i, line in enumerate(off_lines) if line.startswith("  [info] quote_support_rate")) + 1
        self.assertEqual(on.splitlines(), off_lines[:at] + lines + off_lines[at:])

        recs = {r["id"]: r for r in report["records"]}
        self.assertEqual({rid: [c["check"] for c in recs[rid]["cites"]] for rid in SPECIAL},
                         {"lk-01": ["unread"], "lk-02": ["unread"], "lk-03": ["elsewhere"], "lk-04": ["absent"],
                          "lk-05": ["substituted"], "lk-07": ["own"]})
        self.assertEqual((recs["lk-02"]["pool"], recs["lk-02"]["anchors"]), (None, None))
        self.assertEqual(recs["lk-07"]["anchors"], {"LV-01": True, "hr_policy_2026": False})
        self.assertEqual((recs["lk-27"]["cites"], recs["lk-27"]["pool"]), ([], 1))
        self.assertTrue(all(recs["lk-27"]["anchors"].values()))
        for rid, rec in recs.items():
            if not BY_ID[rid]["answerable"]:
                self.assertFalse({"pool", "anchors"} & set(rec), rid)
        # the verdicts, the rates and every other field are what they were with the switch off
        for rec in report["records"]:
            rec.pop("pool", None)
            rec.pop("anchors", None)
            for c in rec.get("cites", []):
                c.pop("check")
        report.pop("passage_checks")
        self.assertEqual(report, report_off)


# ------------------------------------------------------------------ what the helpers rely on in other files
class KitAssumptionsTest(unittest.TestCase):
    """quote_check() drops the generator's repair and recognises resolve()'s substitution; passages() posts to the route
    main.py serves and documind_tools calls. Checked as text, so this file needs nothing but the standard library."""

    def read(self, rel):
        return (KIT / rel).read_text(encoding="utf-8")

    def test_the_repair_the_contract_and_the_substitution(self):
        gen, schemas = self.read("services/rag-api/generator.py"), self.read("shared/documind_schemas.py")
        self.assertIn('c["quote"] = c["quote"][: limit - 3].rstrip() + "..."', gen)      # what repaired() reproduces
        self.assertIn('quote: str = Field(max_length=200, description="Exact words from that source")', schemas)
        self.assertIn('quote=(quote or c.get("text", ""))[:500],', schemas)              # what resolved() reproduces
        self.assertIn('cite(n, "")', schemas)                         # a source cited only in the prose: substituted too
        self.assertIn("ans = resolve(draft, packed)", gen)

    def test_the_route_and_its_reply(self):
        main, tools = self.read("services/rag-api/main.py"), self.read("shared/documind_tools.py")
        door = self.read("services/rag-api/desk_door.py")
        self.assertIn('@app.post("/v1/passages")\ndef passages(req: QueryRequest, user=Depends(verify_iap)):', main)
        self.assertIn('out = [{"n": i, "chunk_id": c.get("id"), "source_uri": c.get("source_uri") or "", '
                      '"page": c.get("page_start"),', main)
        self.assertIn('"text": c.get("text") or ""}', main)
        self.assertIn('resp = requests.post(f"{RAG_API_URL}/v1/passages", json=payload, headers=headers, '
                      'timeout=RAG_TIMEOUT_S)', tools)
        self.assertIn('return await _json(send, 200, {"passages": [], "answer": text, "answerable": False, '
                      '"usage": usage})', door)


# ------------------------------------------------------------------ the corpus files, read and closed
class CorpusFilesTest(unittest.TestCase):
    def test_the_corpus_and_the_demo_are_read_with_every_file_closed(self):
        """13 October 2026: load_corpus() and load_demo() left each file they read to the garbage collector, a
        ResourceWarning per file; lesson 3.1's test cell ran with -W ignore::ResourceWarning to hide them."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            corpus, demo = rv.load_corpus(), rv.load_demo()
            gc.collect()
        self.assertEqual([str(w.message) for w in caught if issubclass(w.category, ResourceWarning)], [])
        self.assertEqual(corpus, CORPUS)                                   # the same texts, read the same way
        self.assertIn("gratuity", demo)


class AskRetries(unittest.TestCase):
    """ask(): one retry for a 5xx (two seconds) and for a 429 (the API's Retry-After); no other 4xx is retried."""

    def run_ask(self, answers):
        calls, slept = iter(answers), []
        with patch.object(rv, "_ask_once", lambda *a, **k: next(calls)), patch.object(rv.time, "sleep", slept.append):
            return rv.ask("https://api.invalid", "q", "acme", "e@x", None), slept

    def test_a_429_is_asked_again_after_the_retry_after(self):
        (status, body, _), slept = self.run_ask([(429, {}, 5), (200, {"answer": "ok"}, 7)])
        self.assertEqual((status, body, slept), (200, {"answer": "ok"}, [rv.RETRY_AFTER_429_S]))

    def test_a_second_429_is_counted(self):
        (status, _, _), slept = self.run_ask([(429, {}, 5), (429, {}, 6)])
        self.assertEqual((status, slept), (429, [rv.RETRY_AFTER_429_S]))

    def test_any_other_4xx_is_not_retried_and_a_5xx_waits_two_seconds(self):
        self.assertEqual(self.run_ask([(404, {}, 3)])[1], [])
        self.assertEqual(self.run_ask([(503, {}, 1), (200, {}, 2)])[1], [2])


if __name__ == "__main__":
    unittest.main()
