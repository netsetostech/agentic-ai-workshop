"""Offline tests for evals/triage.py (workshop lesson 4.9): a live eval's failing rows read before their causes, the
eight causes with the kit's reading of each row, and a filled sheet counted by cause.

Run with ``python -m unittest discover -s evals/tests -p test_triage.py`` from deploy/. Stdlib only. The reports are
real: run_eval.live() is run over a stub of the API, as tests/test_eval_rows.py runs it, with DOCUMIND_EVAL_PASSAGES=1
and the passages cut by the kit's own chunker - so triage reads the file make eval-live REPORT= writes, nothing made up
to look like one.
"""
from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

EVALS = Path(__file__).resolve().parents[1]
KIT = EVALS.parent
MANIFEST = KIT.parent / "course-manifest.json"     # the authoring repository's; a learner's clone has none


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tri = load(EVALS / "triage.py", "triage_under_test")
rv = tri.run_eval
chunker = load(KIT / "shared" / "documind_corpus.py", "documind_corpus_for_triage")

GOLDEN = {r["id"]: r for r in rv.load_golden()}
CHUNKS = {c["chunk_id"]: c for t, slugs in (("acme", ("hr_policy_2026", "msa_acme_2026")), ("zeta", ("hr_policy_zeta_2026",)),
                                            ("globex", ("msa_globex_2026",)))
          for d in chunker.load_documents(t, str(EVALS), "documind-ai-YOUR-ID") if d["slug"] in slugs
          for c in chunker.chunk_document(d, t)}
OUTSIDER = "outsider@not-a-tenant.invalid"
ENV_KEYS = ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "DOCUMIND_USER_EMAIL", "DOCUMIND_OUTSIDER_EMAIL",
            "DOCUMIND_EVAL_PASSAGES")
CAUSES = [c[0] for c in tri.TAXONOMIES["rag"]]


def passage(cid: str) -> dict:
    c = CHUNKS[cid]
    return {"chunk_id": cid, "source_uri": c["source_uri"], "page": 1, "kind": "text", "text": c["text"]}


def cite(cid: str, quote: str | None = None) -> dict:
    """A citation of one chunk; its quote the chunk's own words unless given."""
    return {"chunk_id": cid, "source_uri": CHUNKS[cid]["source_uri"], "page": 1, "kind": "text", "score": 0.9,
            "quote": quote or re.sub(r"\s+", " ", CHUNKS[cid]["text"]).strip()[20:120]}


def reply(answer: str, cites: list, answerable: bool = True) -> tuple[int, dict]:
    return 200, {"answer": answer, "citations": cites, "answerable": answerable,
                 "confidence": "high" if answerable else "low", "model": "stub", "backend": "vertex", "cache_hit": "none",
                 "stages": {"retrieve_ms": 3, "rerank_ms": 2, "generate_ms": 9, "pool": 6}}


REFUSED = reply("The documents do not say.", [], False)
# row id -> (the member's reply, the pool /v1/passages returns, the outsider's status), and the cause each one is
PLAN = {
    "lk-01": (reply("The cap is Rs 40,000 a trip [1].", [cite("acme:hr_policy_2026#EXP-12")]),
              ["acme:hr_policy_2026#EXP-12"], None),                                           # passes
    "lk-02": ((403, {}), None, None),                                                          # infra: the member refused
    "lk-04": (REFUSED, ["acme:msa_acme_2026#MSA-04", "acme:msa_acme_2026#MSA-07"], None),       # retrieval
    "lk-06": (REFUSED, ["acme:hr_policy_2026#NP-03", "acme:hr_policy_2026#LV-07"], None),       # omission
    "lk-12": (reply("Thirty days [1].", [cite("acme:msa_acme_2026#MSA-04", "words this passage never holds")]),
              ["acme:msa_acme_2026#MSA-04"], None),                                            # unsupported: an absent quote
    "jn-01": (reply("Fifteen days [1].", [cite("globex:msa_globex_2026#MSA-04")]),
              ["acme:hr_policy_2026#PB-02", "acme:hr_policy_2026#LV-07"], None),               # isolation, under a later why
    "jn-02": (reply("Unused leave cannot shorten the notice period.", []),
              ["acme:hr_policy_2026#NP-03", "acme:hr_policy_2026#LV-07"], None),               # unsupported: no citation
    "jn-03": (reply("You serve 60 days [1].", [cite("acme:hr_policy_2026#NP-03")]),
              ["acme:hr_policy_2026#NP-03", "acme:hr_policy_2026#LV-07"], None),               # omission: 45 left out
    "rf-02": (reply("You get twelve days a year [1].", [cite("acme:hr_policy_2026#LV-01")]), None, None),   # overreach
    "rf-05": ((500, {}), None, None),                                                          # infra
    "iso-01": (reply("The cap is Rs 25,000 a trip [1].", [cite("zeta:hr_policy_zeta_2026#EXP-12")]),
               ["zeta:hr_policy_zeta_2026#EXP-12"], 200),                     # passes; its outsider is not refused
    "iso-02": (reply("The total is Rs 1,84,500 [1].", [cite("globex:msa_globex_2026#MSA-07")]), None, 403),  # isolation: a leak
    "vr-01": (reply("The notice period is 90 days [1].", [cite("acme:hr_policy_2026#NP-03")]),
              ["acme:hr_policy_2026#NP-03", "acme:hr_policy_2026#LV-07"], None),               # version: a stale figure
}
READING = {("lk-02", "member"): "infra", ("lk-04", "member"): "retrieval", ("lk-06", "member"): "omission",
           ("lk-12", "member"): "unsupported", ("jn-01", "member"): "isolation", ("jn-02", "member"): "unsupported",
           ("jn-03", "member"): "omission", ("rf-02", "member"): "overreach", ("rf-05", "member"): "infra",
           ("iso-02", "member"): "isolation", ("vr-01", "member"): "version", ("iso-01", "outsider"): "isolation"}


def write_report(path: str, passages_on: bool = True, plan: dict = PLAN) -> str:
    """run_eval.live() over the stub, PLAN's rows in golden order, its report written to `path`. live() asks every row
    in order, then the isolation rows as the outsider; lk-06 and vr-01 ask the same question, so replies go by order.
    The pools go by question, and the two share theirs."""
    rows = [r for r in rv.load_golden() if r["id"] in plan]
    order = iter(rows)
    by_q = {(r["question"], r["tenant"]): r["id"] for r in rows}
    isolation = {(r["question"], r["tenant"]): r["id"] for r in rows if r["shape"] == "isolation"}

    def ask(api_url, question, tenant, email, token, retries=1):
        if email == OUTSIDER:
            return (plan[isolation[(question, tenant)]][2] or 403), {}, 4
        row = next(order)
        assert (row["question"], row["tenant"]) == (question, tenant), row["id"]
        status, body = plan[row["id"]][0]
        return status, json.loads(json.dumps(body)), 11

    def passages(api_url, question, tenant, email, token, top_k=6, retries=1):
        ids = plan[by_q[(question, tenant)]][1]
        return None if ids is None else [passage(c) for c in ids]

    env = {"DOCUMIND_EVAL_PASSAGES": "1"} if passages_on else {}
    with patch.dict(os.environ):
        for k in ENV_KEYS:
            os.environ.pop(k, None)
        os.environ.update(env)
        with patch.object(rv, "ask", ask), patch.object(rv, "passages", passages), \
                patch.object(rv, "fetch_current_shas", lambda api_url, tenant, token: None), \
                contextlib.redirect_stdout(io.StringIO()):
            rv.live("http://stub.invalid", report=path, golden=rows)
    return path


def run(*argv) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = tri.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


class TriageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.live = write_report(os.path.join(cls.tmp.name, "live.json"))
        cls.nopool = write_report(os.path.join(cls.tmp.name, "nopool.json"), passages_on=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def failing(self, *paths):
        return tri.failures(tri.load_reports(list(paths)))

    def test_the_report_is_run_evals(self):
        data = json.loads(Path(self.live).read_text(encoding="utf-8"))
        self.assertIn("passage_checks", data)
        self.assertEqual({r["id"]: r["pass"] for r in data["records"]}["lk-01"], True)
        self.assertEqual(data["isolation"], ["iso-01: a non-member asking zeta got 200, expected 403"])
        self.assertEqual([line.split(":")[0] for line in data["leaks"]], ["iso-02"])
        self.assertEqual([line.split(":")[0] for line in data["stale"]], ["vr-01"])

    def test_the_failing_rows_exactly(self):
        fs = self.failing(self.live)
        self.assertEqual({(f["id"], f["leg"]) for f in fs}, set(READING))
        self.assertNotIn(("lk-01", "member"), {(f["id"], f["leg"]) for f in fs})
        self.assertNotIn(("iso-01", "member"), {(f["id"], f["leg"]) for f in fs})

    def test_the_kits_reading(self):
        got = {(f["id"], f["leg"]): tri.reading(f) for f in self.failing(self.live)}
        self.assertEqual({k: v[0] for k, v in got.items()}, READING)
        self.assertIn("PB-02, hr_policy_2026", got[("lk-04", "member")][1])
        self.assertIn("NP-03, hr_policy_2026 reached the pool, and the reply refused", got[("lk-06", "member")][1])
        self.assertIn("a quote is absent", got[("lk-12", "member")][1])
        self.assertIn("another tenant's chunk", got[("jn-01", "member")][1])     # under "answered without [...]"
        self.assertEqual(self.failing(self.live)[[f["id"] for f in self.failing(self.live)].index("jn-01")]["record"]["why"],
                         "answered without ['15', 'cannot']")
        self.assertNotIn("row", set(READING.values()))                          # a person's label, never the kit's

    def test_without_the_pool_retrieval_and_omission_are_not_read(self):
        got = {(f["id"], f["leg"]): tri.reading(f) for f in self.failing(self.nopool)}
        for key in (("lk-04", "member"), ("lk-06", "member"), ("jn-03", "member"), ("lk-12", "member")):
            self.assertIsNone(got[key][0], key)
            self.assertIn("DOCUMIND_EVAL_PASSAGES=1", got[key][1])
        self.assertEqual(got[("rf-02", "member")][0], "overreach")
        self.assertEqual(got[("vr-01", "member")][0], "version")

    def test_open_coding_names_no_cause(self):
        rc, out, _ = run(self.live)
        self.assertEqual(rc, 0)
        self.assertIn("12 failing rows of live, as the gate saw them", out)
        self.assertIn("What is the notice period for a confirmed E3?", out)        # lk-06's question, from golden.jsonl
        self.assertIn("pool 2: NP-03 yes, hr_policy_2026 yes", out)
        self.assertRegex(out, r"iso-01 +outsider +isolation +zeta +a non-member asking zeta got 200, expected 403")
        self.assertRegex(out, r"lk-06 +member +lookup +acme +refused")
        self.assertIn("quote absent", out)
        for word in ("retrieval", "omission", "unsupported", "overreach", "infra", "lever", "caught by"):
            self.assertNotIn(word, out)                                          # no cause before the notes
        self.assertIn("Before you read the causes", out)

    def test_the_template(self):
        path = os.path.join(self.tmp.name, "sheet.csv")
        rc, out, _ = run(self.live, "--template", path)
        self.assertEqual(rc, 0, out)
        with open(path, encoding="utf-8", newline="") as f:
            sheet = list(csv.DictReader(f))
        self.assertEqual(list(sheet[0]), list(tri.COLUMNS))
        self.assertEqual({(r["id"], r["leg"]) for r in sheet}, set(READING))
        self.assertTrue(all(r["note"] == "" and r["class"] == "" and r["report"] == "live" for r in sheet))
        before = Path(path).read_bytes()
        rc, _, err = run(self.live, "--template", path)
        self.assertEqual(rc, 2)
        self.assertIn("never overwrites", err)
        self.assertEqual(Path(path).read_bytes(), before)
        os.unlink(path)

    def test_the_classes(self):
        rc, out, _ = run(self.live, "--classes")
        self.assertEqual(rc, 0)
        for name, means, lever, lessons, catcher, tells in tri.TAXONOMIES["rag"]:
            self.assertIn(f"  {name:12} {means}", out)
            self.assertIn(f"lever: {lever} ({lessons})", out)
            self.assertIn(f"caught by: {catcher}", out)
            self.assertIn(f"from a report: {tells}", out)
        self.assertRegex(out, r"lk-04 +member +retrieval +no must_retrieve anchor \(PB-02, hr_policy_2026\) reached the pool")
        self.assertRegex(out, r"iso-01 +outsider +isolation +a non-member was not refused")

    def sheet(self, classes: dict, notes: dict | None = None, extra: list | None = None) -> str:
        fs = self.failing(self.live)
        path = os.path.join(self.tmp.name, f"filled{len(os.listdir(self.tmp.name))}.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(tri.COLUMNS)
            for x in fs:
                key = (x["id"], x["leg"])
                note, cause = (notes or {}).get(key, ""), classes.get(key, "")
                w.writerow([x["report"], x["id"], x["leg"], "", "", "", "", "", note, cause])
            for line in extra or []:
                w.writerow(line)
        return path

    def test_labels_counted(self):
        mine = dict(READING)
        mine[("lk-12", "member")] = "row"                       # a person may decide the row itself is wrong
        mine[("jn-03", "member")] = "Retrieval"                 # case does not matter
        del mine[("rf-05", "member")]
        rc, out, err = run(self.live, "--labels", self.sheet(mine, {("rf-05", "member"): "a 500, twice?"}))
        self.assertEqual(rc, 0, err)
        self.assertIn("12 failing rows; 11 classed, 1 noted only, 0 untouched", out)
        counts = dict(re.findall(r"(?m)^  (\w+) +(\d+)  ", out))
        self.assertEqual({k: int(v) for k, v in counts.items() if k in CAUSES},
                         {"retrieval": 2, "version": 1, "omission": 1, "unsupported": 1, "overreach": 1, "isolation": 3,
                          "infra": 1, "row": 1})
        self.assertIn("noted, not classed: rf-05", out)
        self.assertIn("yours matched on 9 of 11", out)
        self.assertRegex(out, r"jn-03 +member +yours retrieval +the kit's omission")
        self.assertRegex(out, r"lk-12 +member +yours row +the kit's unsupported")

    def test_labels_refused(self):
        cases = {"an unknown cause": (self.sheet({("lk-06", "member"): "bad luck"}), "'bad luck' is not one of the causes"),
                 "a passing row": (self.sheet({}, extra=[["live", "lk-01", "member", "", "", "", "", "", "", "omission"]]),
                                   "lk-01 (member, live) is not a failing row"),
                 "a row twice": (self.sheet({}, extra=[["live", "lk-06", "member", "", "", "", "", "", "", "omission"]] * 2),
                                 "lk-06 (member) is labelled twice")}
        for name, (path, says) in cases.items():
            with self.subTest(name):
                rc, _, err = run(self.live, "--labels", path)
                self.assertEqual(rc, 2)
                self.assertIn(says, err)
        bare = os.path.join(self.tmp.name, "bare.csv")
        Path(bare).write_text("id,note\nlk-06,x\n", encoding="utf-8")
        rc, _, err = run(self.live, "--labels", bare)
        self.assertEqual((rc, "no id and class columns" in err), (2, True))

    def test_two_reports(self):
        rc, out, _ = run(self.live, self.nopool)
        self.assertEqual(rc, 0)
        self.assertIn("24 failing rows of live, nopool", out)
        self.assertIn("[live] lk-06", out)
        self.assertIn("[nopool] lk-06", out)
        fs = self.failing(self.live, self.nopool)
        path = os.path.join(self.tmp.name, "two.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "class"])                         # no report column, with two reports: whose row?
            w.writerow(["lk-06", "omission"])
        rc, _, err = run(self.live, self.nopool, "--labels", path)
        self.assertEqual(rc, 2)
        self.assertIn("is not a failing row", err)
        self.assertEqual(len(fs), 24)

    def test_inputs_refused(self):
        bad = os.path.join(self.tmp.name, "bad.json")
        Path(bad).write_text(json.dumps({"rows": 3}), encoding="utf-8")
        rc, _, err = run(bad)
        self.assertEqual(rc, 2)
        self.assertIn("not a run_eval.py --report file", err)
        rc, _, err = run(os.path.join(self.tmp.name, "missing.json"))
        self.assertEqual(rc, 2)
        with self.assertRaises(SystemExit):
            run()                                               # make triage with no REPORT=

    def test_nothing_failed(self):
        plan = {"lk-01": PLAN["lk-01"]}
        path = write_report(os.path.join(self.tmp.name, "green.json"), plan=plan)
        rc, out, _ = run(path)
        self.assertEqual(rc, 0)
        self.assertIn("no failing row", out)

    def test_the_lessons_the_causes_name_exist(self):
        if not MANIFEST.exists():
            self.skipTest("course-manifest.json is the authoring repository's")
        lessons = {k for m in json.loads(MANIFEST.read_text(encoding="utf-8"))["modules"].values() for k in m["lessons"]}
        for name, _, _, numbers, _, _ in tri.TAXONOMIES["rag"]:
            for part in numbers.split(", "):
                ends = part.split("-")
                for n in ends:
                    self.assertIn(n, lessons, name)
                if len(ends) == 2:                              # 2.2-2.3: a range inside one module
                    self.assertEqual(ends[0].split(".")[0], ends[1].split(".")[0], name)


if __name__ == "__main__":
    unittest.main()
