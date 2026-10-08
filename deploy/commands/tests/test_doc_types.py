"""Offline checks for the doc_type registry (shared/doc_types.py), the worker's hook and the relabel of stored rows
(services/ingest/relabel.py, commands/desk_ops.py doc-types) - workshop lesson 10.4.

Run: python -m unittest discover -s commands/tests -p test_doc_types.py
Stdlib only, with a fake Firestore: nothing here imports a cloud client. The one case that builds the worker's own
DocumentContract runs when pydantic is installed (CI installs it) and is skipped otherwise; DOCUMIND_REQUIRE_LIBS=1
turns that skip into a failure.
"""
import importlib.util
import io
import json
import os
import re
import sys
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import doc_types  # noqa: E402


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


relabel = _load("relabel", ROOT / "services" / "ingest" / "relabel.py")
desk_ops = _load("desk_ops", ROOT / "commands" / "desk_ops.py")
MANIFEST = json.loads((ROOT / "evals" / "manifest.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ a Firestore small enough to read
class Snap:
    def __init__(self, db, path):
        self._db, self.path, self.id = db, path, path[-1]
        data = db.docs.get(path)
        self.exists = data is not None
        self._data = None if data is None else json.loads(json.dumps(data, default=str))
        self.reference = Ref(db, path)
        self.update_time = db.times.get(path)

    def to_dict(self):
        return None if self._data is None else dict(self._data)


class Ref:
    def __init__(self, db, path):
        self._db, self.path, self.id = db, tuple(path), path[-1]

    def get(self):
        if self._db.fail_reads:
            raise RuntimeError("firestore unavailable")
        return Snap(self._db, self.path)

    def set(self, data, merge=False):
        self._db.write(self.path, data, merge)

    def update(self, fields):
        assert self.path in self._db.docs, f"update of a missing document {self.path}"
        self._db.write(self.path, fields, True)

    def collection(self, name):
        return Query(self._db, self.path + (name,))


class Query:
    def __init__(self, db, path, filters=()):
        self._db, self.path, self.filters = db, tuple(path), tuple(filters)

    def document(self, doc_id):
        return Ref(self._db, self.path + (doc_id,))

    def where(self, field, op, value):
        assert op == "=="
        return Query(self._db, self.path, self.filters + ((field, value),))

    def select(self, fields):
        return self

    def stream(self):
        for path in sorted(p for p in self._db.docs if p[:-1] == self.path):
            row = self._db.docs[path]
            if all(row.get(f) == v for f, v in self.filters):
                yield Snap(self._db, path)


class Batch:
    def __init__(self, db):
        self._db, self.ops = db, []

    def update(self, ref, fields):
        self.ops.append((ref, fields))

    def set(self, ref, data):
        self.ops.append((ref, data))

    def commit(self):
        assert len(self.ops) <= 500, "a Firestore batch holds 500 writes"
        self._db.commits.append(len(self.ops))
        for ref, fields in self.ops:
            ref.update(fields)


class FakeDB:
    def __init__(self):
        self.docs, self.times, self.commits, self.fail_reads, self._clock = {}, {}, [], False, 0

    def write(self, path, data, merge):
        self._clock += 1
        self.docs[path] = {**(self.docs.get(path, {}) if merge else {}), **data}
        self.times[path] = self._clock

    def collection(self, name):
        return Query(self, (name,))

    def batch(self):
        return Batch(self)

    def get_all(self, refs):
        return [Snap(self, r.path) for r in refs]


class Doc:
    """The worker's DocumentContract as assign() reads it: tenant_id, doc_key, doc_type and model_copy."""

    def __init__(self, tenant_id, sha256, doc_type="unknown"):
        self.tenant_id, self.sha256, self.doc_type = tenant_id, sha256, doc_type

    @property
    def doc_key(self):
        return f"{self.tenant_id}_{self.sha256}"

    def model_copy(self, update):
        return Doc(self.tenant_id, self.sha256, update.get("doc_type", self.doc_type))


U = "gs://documind-ai-YOUR-ID-uploads/"


def chunk(db, row_id, name, doc_key, doc_type, kind="text", current=True, **extra):
    db.write(("chunks", row_id), {"tenant_id": doc_key.split("_", 1)[0], "source_uri": U + name, "doc_key": doc_key,
                                 "doc_type": doc_type, "kind": kind, "current": current, "text": f"text of {row_id}",
                                 "embedding": [0.0] * 3, **extra}, False)


def lane(db, labelled=False, seeded=True):
    """acme as make ingest-corpus leaves it - every text row unknown, the figure a figure - with a registry seeded:
    the handbook (two current rows and a retired version), a statute, a figure, and the unregistered whiteboard.
    seeded: the statute's row came from a notebook (shared/documind_corpus.py), which writes the manifest's class."""
    reg = doc_types.registry_from_manifest()
    for name in ("acme/hr_policy_2026.md", "acme/posh_act_2013.pdf", "acme/annual_report_2026_fig3.png"):
        pin = f"acme_{reg[name]['sha256']}" if reg[name]["sha256"] else "acme_fig3"
        doc_types.set_class(db, "acme", name, reg[name]["doc_type"], pin, "operator@example.com", "manifest")
    hb = f"acme_{reg['acme/hr_policy_2026.md']['sha256']}"
    posh = f"acme_{reg['acme/posh_act_2013.pdf']['sha256']}"
    for i in range(2):
        chunk(db, f"acme:{hb[5:]}#{i}", "acme/hr_policy_2026.md", hb, "policy" if labelled else "unknown")
    chunk(db, "acme:old#0", "acme/hr_policy_2026.md", "acme_old", "unknown", current=False)       # the retired version
    chunk(db, "acme:posh_act_2013#s1", "acme/posh_act_2013.pdf", posh, "statute" if seeded or labelled else "unknown")
    chunk(db, "acme:fig3#0", "acme/annual_report_2026_fig3.png", "acme_fig3", "report" if labelled else "figure", "figure")
    chunk(db, "acme:wb#0", "acme/whiteboard_arch.png", "acme_wb", "figure", "figure")
    db.write(("answer_cache", "q1"), {"tenant_id": "acme", "expire_at": "2099-01-01"}, False)
    db.write(("answer_cache", "q2"), {"tenant_id": "zeta", "expire_at": "2099-01-01"}, False)
    return hb


def repair_stub(calls):
    """indexer._repair_snapshots' contract: it raises on a row that is not current, staged, or without text."""
    def repair(index_name, db, snaps):
        for s in snaps:
            row = s.to_dict()
            if not row.get("current") or row.get("staged") or not row.get("tenant_id") or not row.get("text"):
                raise ValueError(f"Refusing invalid current chunk: {s.id}")
            calls.append((s.id, row["doc_type"], db.docs[("chunks", s.id)]["doc_type"]))
        return len(snaps)
    return repair


def changes(actions):
    return [(a["name"], a["change"], a["to"]) for a in actions]


class RegistryTests(unittest.TestCase):
    def test_the_media_parent_map(self):
        reg = doc_types.registry_from_manifest()
        got = {n: (reg[n]["parent"], reg[n]["doc_type"]) for n in reg if reg[n]["parent"]}
        self.assertEqual(got, {"acme/annual_report_2026_fig3.png": ("annual_report_2026", "report"),
                               "acme/inv_2026_0412.png": ("inv_2026_0412", "invoice"),
                               "acme/payment_of_bonus_act_1965_p30.png": ("payment_of_bonus_act_1965", "statute"),
                               "acme/townhall_2026_q1.mp4": ("townhall_2026_q1", "transcript")})
        self.assertEqual(reg["acme/townhall_2026_q1.md"]["doc_type"], "transcript")   # registered under both names

    def test_whiteboard_stays_unregistered(self):
        reg = doc_types.registry_from_manifest()
        self.assertNotIn("acme/whiteboard_arch.png", reg)
        self.assertIsNone(doc_types.media_parent("whiteboard_arch", {"annual_report_2026": "report"}))
        self.assertIsNone(doc_types.media_parent("inv_2026_04", {"inv_2026_0412": "invoice"}))   # a prefix ends at "_"

    def test_every_manifest_object_but_the_whiteboard_maps_to_a_class(self):
        reg = doc_types.registry_from_manifest()
        names = {f"{m['tenant_id']}/{Path(m['file']).name}" for m in MANIFEST}
        self.assertEqual(set(reg), names - {"acme/whiteboard_arch.png"})
        self.assertEqual(len(reg), len(MANIFEST) - 1)
        self.assertTrue(all(r["doc_type"] in doc_types.CLASSES for r in reg.values()))
        media = {m["doc_type"] for m in MANIFEST if m["sha256"] is None}
        self.assertEqual(media, {"figure", "video", "image"})
        self.assertFalse(media & set(doc_types.CLASSES))

    def test_set_class_refuses_what_is_not_a_class_or_not_the_tenants(self):
        db = FakeDB()
        with self.assertRaises(ValueError):
            doc_types.set_class(db, "acme", "acme/x.md", "figure", "acme_1", "op", "manifest")
        with self.assertRaises(ValueError):
            doc_types.set_class(db, "acme", "zeta/x.md", "policy", "acme_1", "op", "manifest")
        with self.assertRaises(ValueError):
            doc_types.set_class(db, "acme", "acme/x.md", "policy", "zeta_1", "op", "manifest")
        with self.assertRaises(ValueError):
            doc_types.set_class(db, "acme", "acme/x.md", "policy", "acme_1", "op", "uploader")
        row = doc_types.set_class(db, "acme", "acme/x.md", "policy", "acme_1", "op", "operator")
        self.assertEqual(set(row), {"name", "doc_type", "pin", "set_by", "set_at", "source"})
        self.assertIn(("tenants", "acme", "doc_types", "acme~x.md"), db.docs)

    def test_seed_pins_from_the_manifest_then_cross_checks_the_ledger(self):
        seed = doc_types.registry_from_manifest()
        fresh = {a["name"]: a for a in doc_types.seed_plan("acme", seed, {}, {})}
        hb = f"acme_{seed['acme/hr_policy_2026.md']['sha256']}"
        self.assertEqual((fresh["acme/hr_policy_2026.md"]["action"], fresh["acme/hr_policy_2026.md"]["pin"]), ("pin", hb))
        self.assertEqual(fresh["acme/annual_report_2026_fig3.png"]["action"], "not_ingested")
        self.assertFalse(any(n.startswith(("zeta/", "globex/")) for n in fresh))
        ledger = {"acme/hr_policy_2026.md": {"doc_key": "acme_other", "status": "indexed"},
                  "acme/annual_report_2026_fig3.png": {"doc_key": "acme_fig3", "status": "indexed"},
                  "acme/posh_act_2013.pdf": {"doc_key": f"acme_{seed['acme/posh_act_2013.pdf']['sha256']}", "status": "indexed"}}
        registry = {"acme/posh_act_2013.pdf": {"doc_type": "statute", "pin": ledger["acme/posh_act_2013.pdf"]["doc_key"]},
                    "acme/msa_acme_2026.md": {"doc_type": "contract", "pin": "acme_reviewed", "source": "operator"}}
        lane_plan = {a["name"]: a for a in doc_types.seed_plan("acme", seed, ledger, registry)}
        self.assertEqual(lane_plan["acme/hr_policy_2026.md"]["action"], "mismatch")      # printed, never pinned
        self.assertIsNone(lane_plan["acme/hr_policy_2026.md"]["pin"])
        self.assertEqual((lane_plan["acme/annual_report_2026_fig3.png"]["action"],
                          lane_plan["acme/annual_report_2026_fig3.png"]["pin"]), ("pin", "acme_fig3"))
        self.assertEqual(lane_plan["acme/posh_act_2013.pdf"]["action"], "unchanged")
        self.assertEqual(lane_plan["acme/msa_acme_2026.md"]["action"], "operator")       # FOLLOW= is not undone

    def test_a_second_seed_does_not_accept_a_replaced_figure(self):
        seed = doc_types.registry_from_manifest()
        name = "acme/annual_report_2026_fig3.png"
        ledger = {name: {"doc_key": "acme_overwrite", "status": "indexed"}}
        registry = {name: {"doc_type": "report", "pin": "acme_reviewed", "source": "manifest"}}
        act = {a["name"]: a for a in doc_types.seed_plan("acme", seed, ledger, registry)}[name]
        self.assertEqual((act["action"], act["pin"], act["registered"]), ("mismatch", None, "acme_reviewed"))
        registry[name]["pin"] = "acme_overwrite"
        act = {a["name"]: a for a in doc_types.seed_plan("acme", seed, ledger, registry)}[name]
        self.assertEqual(act["action"], "unchanged")


class HookTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDB()
        doc_types.set_class(self.db, "acme", "acme/hr_policy_2026.md", "policy", "acme_v1", "op", "manifest")

    def test_a_pinned_version_takes_its_class(self):
        self.assertEqual(doc_types.assign(self.db, Doc("acme", "v1"), "acme/hr_policy_2026.md").doc_type, "policy")

    def test_a_pin_mismatch_gives_unknown_and_says_so(self):
        with self.assertLogs("documind.doc_types", "WARNING") as logs:
            out = doc_types.assign(self.db, Doc("acme", "v2", doc_type="policy"), "acme/hr_policy_2026.md")
        self.assertEqual(out.doc_type, "unknown")
        line = json.loads(logs.records[0].getMessage())
        self.assertEqual((line["event"], line["tenant"], line["name"]), ("doc_type_pin_miss", "acme", "acme/hr_policy_2026.md"))

    def test_an_unregistered_name_and_another_tenant_stay_unknown(self):
        self.assertEqual(doc_types.assign(self.db, Doc("acme", "w1"), "acme/whiteboard_arch.png").doc_type, "unknown")
        self.assertEqual(doc_types.assign(self.db, Doc("zeta", "v1"), "zeta/hr_policy_2026.md").doc_type, "unknown")

    def test_a_failed_read_is_unknown_never_an_exception(self):
        self.db.fail_reads = True
        with self.assertLogs("documind.doc_types", "WARNING") as logs:
            out = doc_types.assign(self.db, Doc("acme", "v1"), "acme/hr_policy_2026.md")
        self.assertEqual(out.doc_type, "unknown")
        self.assertIn('"doc_type_lookup_failed"', logs.output[0])

    def test_the_worker_contract(self):
        try:
            sys.path.insert(0, str(ROOT / "services" / "ingest"))
            from contracts import DocumentContract
        except ImportError:
            if os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1":
                raise
            self.skipTest("pydantic is not installed")
        finally:
            sys.path.remove(str(ROOT / "services" / "ingest"))
        doc = DocumentContract(tenant_id="acme", sha256="v1", gcs_uri=U + "acme/hr_policy_2026.md", pages=0)
        self.assertEqual(doc_types.assign(self.db, doc, "acme/hr_policy_2026.md").doc_type, "policy")

    def test_the_hook_and_what_the_pages_assert(self):
        src = (ROOT / "services" / "ingest" / "main.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("from shared import doc_types\n"), 1)
        body = src.split("def index_document(", 1)[1]
        hook = "    doc = doc_types.assign(_db, doc, msg.name)"
        self.assertIn(hook, body)
        self.assertLess(body.index(hook), body.index("    try:\n"))                   # before the try, both lanes
        self.assertIn('"doc_type": doc.doc_type if doc.doc_type != "unknown"\n'
                      '                                        else MEDIA_TYPES[msg.content_type],', body)
        self.assertIn('MEDIA_TYPES = {"image/png": "figure", "image/jpeg": "figure",\n'
                      '               "video/mp4": "segment", "audio/mpeg": "segment"}', src)           # workshop lessons 1.2, 7.3 and 7.5
        self.assertIn("text = None                                          # a media document has none", src)  # workshop lesson 7.3
        callers = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "services").rglob("*.py")
                         if re.search(r"_mirror\.after_(swap|undo)\(|mirror\.upsert\(", p.read_text(encoding="utf-8")))
        self.assertEqual(callers, ["services/ingest/main.py"])                  # workshop lesson 7.3's upsert-caller assert


class RelabelTests(unittest.TestCase):
    def test_rows_already_carrying_their_class_plan_no_change(self):
        db = FakeDB()
        lane(db, labelled=True)
        actions = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))
        self.assertEqual(relabel.plan_lines(actions), [])
        self.assertEqual({a["name"]: a["why"] for a in actions}["acme/whiteboard_arch.png"], "unregistered")

    def test_a_second_relabel_plans_no_change(self):
        db = FakeDB()
        hb = lane(db)
        first = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))
        self.assertEqual(changes([a for a in first if a["change"]]),
                         [("acme/annual_report_2026_fig3.png", ["acme:fig3#0"], "report"),
                          ("acme/hr_policy_2026.md", [f"acme:{hb[5:]}#0", f"acme:{hb[5:]}#1"], "policy")])
        calls = []
        done = relabel.apply(db, "acme", first, index_name="idx", repair=repair_stub(calls))
        self.assertEqual((done["firestore_rows"], done["vector_datapoints"], done["failed"]), (3, 3, []))
        # the tier goes up with the new label while the row still holds the old one: a failed upsert changes no row
        self.assertEqual(sorted(calls), sorted([("acme:fig3#0", "report", "figure"),
                                                (f"acme:{hb[5:]}#0", "policy", "unknown"), (f"acme:{hb[5:]}#1", "policy", "unknown")]))
        self.assertEqual(db.docs[("chunks", "acme:old#0")]["doc_type"], "unknown")       # history keeps its label
        self.assertEqual(db.docs[("chunks", "acme:wb#0")]["doc_type"], "figure")
        self.assertEqual(done["answer_cache_expired"], 1)                                 # acme's entry, not zeta's
        self.assertNotEqual(db.docs[("answer_cache", "q1")]["expire_at"], "2099-01-01")
        self.assertEqual(db.docs[("answer_cache", "q2")]["expire_at"], "2099-01-01")
        again = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))
        self.assertEqual(relabel.plan_lines(again), [])
        second = relabel.apply(db, "acme", again, index_name="idx", repair=repair_stub(calls))
        self.assertEqual((second["firestore_rows"], second["answer_cache_expired"]), (0, 1))   # expired on every --apply

    def test_reset_then_a_relabel_returns_to_the_same_plan(self):
        db = FakeDB()
        lane(db, seeded=False)                                                               # every row as the worker wrote it
        reg = doc_types.read_registry(db, "acme")
        first = relabel.plan(relabel.read_rows(db, "acme"), reg)
        relabel.apply(db, "acme", first, index_name="idx", repair=repair_stub([]))
        back = relabel.plan(relabel.read_rows(db, "acme"), reg, reset=True)
        self.assertEqual({a["name"]: a["to"] for a in back if a["change"]},
                         {"acme/hr_policy_2026.md": "unknown", "acme/annual_report_2026_fig3.png": "figure",
                          "acme/posh_act_2013.pdf": "unknown"})
        relabel.apply(db, "acme", back, index_name="idx", repair=repair_stub([]))
        self.assertEqual(len(doc_types.read_registry(db, "acme")), 3)                        # the registry stays
        again = relabel.plan(relabel.read_rows(db, "acme"), reg)
        self.assertEqual(changes(again), changes(first))
        self.assertEqual(len([c for c in changes(first) if c[1]]), 3)

    def test_non_current_rows_never_reach_repair_snapshots(self):
        db = FakeDB()
        hb = lane(db)
        actions = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))
        planned = {i for a in actions for i in a["change"]}
        self.assertNotIn("acme:old#0", planned)                                            # history is never planned
        db.write(("chunks", f"acme:{hb[5:]}#1"), {"current": False, "superseded_by": "acme_newer"}, True)   # a swap since
        db.write(("chunks", "acme:staged#0"), {"tenant_id": "acme", "source_uri": U + "acme/hr_policy_2026.md",
                                               "doc_key": hb, "doc_type": "unknown", "current": False, "staged": True,
                                               "text": "t"}, False)
        calls = []
        done = relabel.apply(db, "acme", actions, index_name="idx", repair=repair_stub(calls))   # it would raise on #1
        self.assertEqual(sorted(c[0] for c in calls), sorted(["acme:fig3#0", f"acme:{hb[5:]}#0"]))
        self.assertEqual(done["left_current"], 1)
        self.assertEqual(db.docs[("chunks", f"acme:{hb[5:]}#1")]["doc_type"], "unknown")   # not relabelled either

    def test_a_pin_miss_goes_back_to_unknown_and_media_to_its_type(self):
        db = FakeDB()
        lane(db, labelled=True)
        doc_types.set_class(db, "acme", "acme/hr_policy_2026.md", "policy", "acme_reviewed", "op", "operator")
        doc_types.set_class(db, "acme", "acme/annual_report_2026_fig3.png", "report", "acme_other", "op", "operator")
        actions = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))
        got = {a["name"]: (a["why"], a["to"]) for a in actions if a["change"]}
        self.assertEqual(got, {"acme/hr_policy_2026.md": ("pin_miss", "unknown"),
                               "acme/annual_report_2026_fig3.png": ("pin_miss", "figure")})

    def test_the_writes_stay_under_the_batch_limit(self):
        db = FakeDB()
        doc_types.set_class(db, "acme", "acme/big.md", "policy", "acme_big", "op", "operator")
        for i in range(950):
            chunk(db, f"acme:big#{i}", "acme/big.md", "acme_big", "unknown")
        actions = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))
        relabel.apply(db, "acme", actions)                                                   # no index: rows only
        self.assertEqual(db.commits, [400, 400, 150])

    def test_bigquery_one_update_per_label(self):
        db = FakeDB()
        hb = lane(db)
        actions = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))
        sql = relabel.bq_statements("documind-ai-YOUR-ID.rag_data.chunk_source", "acme", actions)
        self.assertEqual([p.get("label") for _, p in sql], ["policy", "report", "statute"])   # the whiteboard is not touched
        self.assertTrue(all("WHERE tenant_id = @tenant AND source_uri IN UNNEST(@uris)" in s for s, _ in sql))
        self.assertTrue(all("SPLIT(chunk_id, '#')[SAFE_OFFSET(0)] IN UNNEST(@versions)" in s for s, _ in sql))
        self.assertEqual({p["label"]: p["versions"] for _, p in sql},              # the version, not the source
                         {"policy": [f"acme:{hb[5:]}"], "report": ["acme:fig3"], "statute": ["acme:posh_act_2013"]})
        reset = relabel.bq_statements("t", "acme", relabel.plan(relabel.read_rows(db, "acme"), {}, reset=True))
        self.assertEqual(len(reset), 1)
        self.assertIn("IF(IFNULL(kind, 'text') = 'text', 'unknown', kind)", reset[0][0])
        self.assertEqual(len(reset[0][1]["uris"]), 4)

    def test_vertex_search_gets_text_versions_only(self):
        db = FakeDB()
        lane(db)
        actions = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))
        seen = []
        relabel.apply(db, "acme", actions, search=lambda t, k, c: seen.append((k, c)) or "updated")
        self.assertEqual(sorted(c for _, c in seen), ["policy", "statute"])

    def test_a_retired_version_keeps_a_class_only_when_it_is_the_pin(self):
        """The undo flips a retired version current with the label its rows hold, without passing the hook: after a
        FOLLOW= the reviewed old version must not keep its class, or re-uploading its bytes brings it back classed."""
        db = FakeDB()
        doc_types.set_class(db, "acme", "acme/hr_policy_2026.md", "policy", "acme_v1", "op", "manifest")
        chunk(db, "acme:v1#0", "acme/hr_policy_2026.md", "acme_v1", "policy", current=False, superseded_by="acme_v2")
        chunk(db, "acme:v2#0", "acme/hr_policy_2026.md", "acme_v2", "unknown")
        chunk(db, "acme:v0#0", "acme/hr_policy_2026.md", "acme_v0", "unknown", current=False)
        chunk(db, "acme:wb0#0", "acme/whiteboard_arch.png", "acme_wb0", "figure", "figure", current=False)
        chunk(db, "acme:v3#0", "acme/hr_policy_2026.md", "acme_v3", "unknown", current=False, staged=True)
        doc_types.set_class(db, "acme", "acme/hr_policy_2026.md", "policy", "acme_v2", "op", "operator")   # FOLLOW=
        reg = doc_types.read_registry(db, "acme")
        actions = relabel.plan(relabel.read_rows(db, "acme"), reg)
        history = relabel.plan_history(relabel.read_rows(db, "acme", current=False), reg)
        self.assertEqual([(h["doc_key"], h["change"], h["to"]) for h in history],
                         [("acme_v0", [], "unknown"), ("acme_v1", ["acme:v1#0"], "unknown")])   # no staged, no whiteboard
        self.assertEqual(relabel.plan_lines(history)[0]["history"], True)
        calls = []
        done = relabel.apply(db, "acme", actions, index_name="idx", repair=repair_stub(calls), history=history)
        self.assertEqual(([c[0] for c in calls], done["history_rows"], done["failed"]), (["acme:v2#0"], 1, []))
        self.assertEqual(db.docs[("chunks", "acme:v1#0")]["doc_type"], "unknown")
        self.assertEqual(db.docs[("chunks", "acme:v3#0")]["doc_type"], "unknown")
        db.write(("chunks", "acme:v1#0"), {"current": True}, True)                       # the undo: as the rows are
        self.assertEqual(db.docs[("chunks", "acme:v1#0")]["doc_type"], "unknown")
        # and back: once v1 is the pin again, its retired rows take the class, so an undo to the pin is classed
        doc_types.set_class(db, "acme", "acme/hr_policy_2026.md", "policy", "acme_v0", "op", "operator")
        again = relabel.plan_history(relabel.read_rows(db, "acme", current=False), doc_types.read_registry(db, "acme"))
        self.assertEqual([(h["doc_key"], h["why"], h["to"]) for h in again], [("acme_v0", "pinned", "policy")])
        sql = relabel.bq_statements("t", "acme", [*actions, *history])
        self.assertEqual({p.get("label"): p["versions"] for _, p in sql},
                         {"policy": ["acme:v2"], None: ["acme:v0", "acme:v1"]})

    def test_reset_takes_the_retired_rows_back_too(self):
        db = FakeDB()
        lane(db)
        chunk(db, "acme:fig0#0", "acme/annual_report_2026_fig3.png", "acme_fig0", "report", "figure", current=False)
        history = relabel.plan_history(relabel.read_rows(db, "acme", current=False), {}, reset=True)
        self.assertEqual({h["doc_key"]: (h["why"], h["change"], h["to"]) for h in history},
                         {"acme_fig0": ("reset", ["acme:fig0#0"], "figure"), "acme_old": ("reset", [], "unknown")})

    def test_a_failed_version_does_not_stop_the_others_or_the_cache(self):
        db = FakeDB()
        hb = lane(db)
        actions = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))

        def repair(index_name, db_, snaps):
            if any(s.id.startswith("acme:fig3") for s in snaps):
                raise RuntimeError("429 Vector Search quota")
            return len(snaps)
        done = relabel.apply(db, "acme", actions, index_name="idx", repair=repair)
        # the tier it could not put back (the quota refuses that upsert too), then the version's failure
        self.assertEqual([f.split(":")[0] for f in done["failed"]], ["tier acme_fig3", "version acme_fig3"])
        self.assertEqual(db.docs[("chunks", "acme:fig3#0")]["doc_type"], "figure")           # unchanged: planned again
        self.assertEqual(db.docs[("chunks", f"acme:{hb[5:]}#0")]["doc_type"], "policy")
        self.assertEqual(done["answer_cache_expired"], 1)
        again = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))
        self.assertEqual([line["relabel"] for line in relabel.plan_lines(again)], ["acme/annual_report_2026_fig3.png"])

    def test_a_swap_during_the_upsert_takes_the_datapoint_back_off(self):
        db = FakeDB()
        hb = lane(db)
        actions = relabel.plan(relabel.read_rows(db, "acme"), doc_types.read_registry(db, "acme"))
        swapped = f"acme:{hb[5:]}#1"

        def repair(index_name, db_, snaps):                      # the worker's swap lands while the upsert runs
            if any(s.id == swapped for s in snaps):
                db.write(("chunks", swapped), {"current": False, "superseded_by": "acme_newer"}, True)
            return len(snaps)
        removed = []
        done = relabel.apply(db, "acme", actions, index_name="idx", repair=repair,
                             remove=lambda idx, ids: removed.extend(ids))
        self.assertEqual((removed, done["vector_removed"], done["left_current"]), ([swapped], 1, 1))
        self.assertEqual(db.docs[("chunks", swapped)]["doc_type"], "unknown")                 # history: not written
        self.assertEqual(db.docs[("chunks", f"acme:{hb[5:]}#0")]["doc_type"], "policy")

    def test_a_failed_row_write_puts_the_tier_back(self):
        """The upsert goes first; a row write that fails after it must not leave the datapoints on the new label, or a
        later --reset (whose target is the rows' old label) would plan no change and never upsert them again."""
        db = FakeDB()
        hb = lane(db)
        tier = {}

        def repair(index_name, db_, snaps):                      # what each datapoint's restrict carries
            tier.update({s.id: s.to_dict()["doc_type"] for s in snaps})
            return len(snaps)

        def rows():
            return {i: db.docs[("chunks", i)]["doc_type"] for i in tier}

        class Down(Batch):
            def commit(self):
                raise RuntimeError("firestore 503")
        reg = doc_types.read_registry(db, "acme")
        with patch.object(db, "batch", lambda: Down(db)):
            done = relabel.apply(db, "acme", relabel.plan(relabel.read_rows(db, "acme"), reg),
                                 index_name="idx", repair=repair)
        self.assertEqual(sorted(f.split(":")[0] for f in done["failed"]),
                         sorted(["answer_cache", "version acme_fig3", f"version {hb}"]))   # the cache too
        self.assertEqual(done["vector_restored"], 3)
        self.assertEqual(tier, rows())                                     # back to 'figure' and 'unknown'
        self.assertEqual(tier[f"acme:{hb[5:]}#0"], "unknown")
        back = relabel.plan(relabel.read_rows(db, "acme"), reg, reset=True)
        relabel.apply(db, "acme", back, index_name="idx", repair=repair)
        self.assertEqual(tier, rows())
        # and if putting the tier back fails too, a second line per version says what is left to do
        def up_only(index_name, db_, snaps):
            if not isinstance(snaps[0], relabel._Relabelled):
                raise RuntimeError("429 Vector Search quota")
            return len(snaps)
        with patch.object(db, "batch", lambda: Down(db)):
            done = relabel.apply(db, "acme", relabel.plan(relabel.read_rows(db, "acme"), reg),
                                 index_name="idx", repair=up_only)
        tiers = [f for f in done["failed"] if f.startswith("tier ")]
        self.assertEqual((len([f for f in done["failed"] if f.startswith("version ")]), len(tiers)), (3, 3))
        self.assertTrue(all("apply this plan again" in f for f in tiers))

    def test_a_repair_that_fails_after_its_first_group_puts_the_tier_back(self):
        """_repair_snapshots upserts 100 at a time: a later group can fail after the first landed."""
        db = FakeDB()
        hb = lane(db)
        for i in range(2, 150):                                  # the handbook: 150 rows to relabel
            chunk(db, f"acme:{hb[5:]}#{i}", "acme/hr_policy_2026.md", hb, "unknown")
        tier, calls = {}, []

        def repair(index_name, db_, snaps):                      # groups of 100; the second relabel group fails
            calls.append(len(snaps))
            groups = [snaps[i:i + 100] for i in range(0, len(snaps), 100)]
            for n, group in enumerate(groups):
                if n == 1 and isinstance(group[0], relabel._Relabelled):
                    raise RuntimeError("503 upsert_datapoints: quota")
                tier.update({s.id: s.to_dict()["doc_type"] for s in group})
            return len(snaps)
        reg = doc_types.read_registry(db, "acme")
        done = relabel.apply(db, "acme", relabel.plan(relabel.read_rows(db, "acme"), reg), index_name="idx",
                             repair=repair)
        self.assertIn(f"version {hb}", [f.split(":")[0] for f in done["failed"]])
        self.assertFalse([f for f in done["failed"] if f.startswith("tier ")])
        self.assertEqual(done["vector_restored"], 150)
        rows = {i: db.docs[("chunks", i)]["doc_type"] for i in tier if i.startswith(f"acme:{hb[5:]}#")}
        self.assertEqual(set(rows.values()), {"unknown"})        # the rows were never written
        self.assertEqual({i: tier[i] for i in rows}, rows)       # and no datapoint runs ahead of them

    def test_a_deferred_bigquery_statement_is_not_a_clean_exit(self):
        db = FakeDB()
        lane(db)

        class Param:
            def __init__(self, *a):
                self.a = a

        class Client:
            def __init__(self, project=None):
                pass

            def query(self, sql, job_config=None):
                raise RuntimeError("400 UPDATE or DELETE statement over table t would affect rows in the streaming buffer")
        bq = types.SimpleNamespace(Client=Client, ScalarQueryParameter=Param, ArrayQueryParameter=Param,
                                   QueryJobConfig=lambda query_parameters=None: None)
        fs = types.SimpleNamespace(Client=lambda project=None: db)
        cloud = types.ModuleType("google.cloud")
        cloud.firestore, cloud.bigquery = fs, bq
        mods = {"google": types.ModuleType("google"), "google.cloud": cloud, "google.cloud.firestore": fs,
                "google.cloud.bigquery": bq}
        env = {"BQ_CHUNK_TABLE": "documind-ai-YOUR-ID.rag_data.chunk_source", "VECTOR_INDEX_NAME": "",
               "MANAGED_MIRROR": "off"}
        with patch.dict(sys.modules, mods), patch.dict(os.environ, env), redirect_stdout(io.StringIO()) as out:
            code = relabel.main(["--project", "documind-ai-YOUR-ID", "--tenant", "acme", "--apply", "--no-index"])
        self.assertEqual(code, 3)
        self.assertIn("BigQuery deferred 4 statement(s)", out.getvalue())

    def test_bigquery_counts_the_rows_each_statement_changed(self):
        class Param:
            def __init__(self, *a):
                self.a = a
        seen = []

        class Job:
            num_dml_affected_rows = 7

            def result(self):
                return []

        class Client:
            def query(self, sql, job_config=None):
                seen.append((sql, [p.a[0] for p in job_config.query_parameters]))
                return Job()
        bq = types.SimpleNamespace(ScalarQueryParameter=Param, ArrayQueryParameter=Param,
                                   QueryJobConfig=lambda query_parameters=None: types.SimpleNamespace(
                                       query_parameters=query_parameters))
        cloud = types.ModuleType("google.cloud")
        cloud.bigquery = bq
        mods = {"google": types.ModuleType("google"), "google.cloud": cloud, "google.cloud.bigquery": bq}
        statements = [("UPDATE t SET doc_type = @label", {"tenant": "acme", "uris": ["u"], "versions": ["v"],
                                                          "label": "policy"}),
                      ("UPDATE t SET doc_type = 'unknown'", {"tenant": "acme", "uris": ["u"], "versions": ["w"]})]
        with patch.dict(sys.modules, mods):
            done = relabel.run_bq(Client(), statements)
        self.assertEqual(done, {"updated": 14, "deferred": 0, "failed": []})
        self.assertEqual([names for _, names in seen], [["tenant", "uris", "versions", "label"],
                                                        ["tenant", "uris", "versions"]])

    def test_vertex_search_updates_struct_data_only(self):
        """SearchLabels against stand-ins shaped as discoveryengine_v1's: get, then an update masked to
        struct_data that keeps the other structData fields; unchanged, not held and no store say so."""
        class NotFound(Exception):
            pass

        class NoStore(Exception):
            pass
        held = {"b/documents/acme_hb": {"struct_data": {"doc_type": "unknown", "title": "Handbook"}},
                "b/documents/acme_st": {"struct_data": {"doc_type": "statute"}}}
        updates = []

        def get_document(name):
            if name not in held:
                raise NotFound(name)
            return held[name]
        de = types.SimpleNamespace(Document=type("Document", (), {"__init__": lambda self, **kw: self.__dict__.update(kw),
                                                                  "to_dict": staticmethod(lambda d: d)}),
                                   UpdateDocumentRequest=lambda **kw: kw)
        docs = types.SimpleNamespace(get_document=get_document, update_document=lambda request: updates.append(request))

        class Store:
            def clients(self):
                return types.SimpleNamespace(docs=docs, de=de)

            def ensure(self, tenant_id):
                if tenant_id == "globex":
                    raise NoStore(tenant_id)

            def branch(self, tenant_id):
                return "b"
        exc = types.ModuleType("google.api_core.exceptions")
        exc.NotFound = NotFound
        managed = types.ModuleType("managed")
        managed.NoStore = NoStore
        mods = {"google": types.ModuleType("google"), "google.api_core": types.ModuleType("google.api_core"),
                "google.api_core.exceptions": exc, "managed": managed}
        label = relabel.SearchLabels(Store())
        with patch.dict(sys.modules, mods):
            got = [label("acme", "acme_hb", "policy"), label("acme", "acme_st", "statute"),
                   label("acme", "acme_gone", "policy"), label("globex", "globex_x", "statute")]
        self.assertEqual(got, ["updated", "unchanged", "not held", "no store"])
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]["update_mask"], {"paths": ["struct_data"]})
        self.assertEqual((updates[0]["document"].name, updates[0]["document"].id), ("b/documents/acme_hb", "acme_hb"))
        self.assertEqual(updates[0]["document"].struct_data, {"doc_type": "policy", "title": "Handbook"})

    def test_the_selftest(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(relabel.selftest(), 0)
        self.assertIn("selftest OK", out.getvalue())


class DeskOpsTests(unittest.TestCase):
    def test_the_doc_types_subcommand(self):
        ap = desk_ops.build_parser()
        sub = next(a for a in ap._actions if a.dest == "cmd")
        self.assertIn("doc-types", sub.choices)
        a = ap.parse_args(["--project", "p", "doc-types", "--tenant", "zeta", "--seed", "manifest", "--follow", "x.md"])
        self.assertEqual((a.tenant, a.seed, a.follow), ("zeta", "manifest", "x.md"))

    def test_object_names(self):
        for given in ("hr_policy_2026.md", "acme/hr_policy_2026.md", "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"):
            self.assertEqual(desk_ops.object_name("acme", given), "acme/hr_policy_2026.md")

    def test_the_view(self):
        db = FakeDB()
        lane(db)
        reg = doc_types.read_registry(db, "acme")
        rows = {r["name"]: r for r in desk_ops.view("acme", reg, {}, relabel.plan(relabel.read_rows(db, "acme"), reg))}
        hb = rows["acme/hr_policy_2026.md"]
        self.assertEqual((hb["label"], hb["class"], hb["chunks"], hb["state"]), ("unknown", "policy", 2, "relabel 2 rows"))
        self.assertEqual((rows["acme/posh_act_2013.pdf"]["state"], rows["acme/whiteboard_arch.png"]["class"]), ("pinned", "-"))

    def run_cmd(self, db, *args):
        """desk_ops.main over the fake: a stand-in google.cloud.firestore whose Client is the fake database."""
        fs = types.SimpleNamespace(Client=lambda project=None: db)
        mods = {"google": types.ModuleType("google"), "google.cloud": types.ModuleType("google.cloud"), "google.cloud.firestore": fs}
        mods["google.cloud"].firestore = fs
        with patch.dict(sys.modules, mods), patch.dict(os.environ, {"DOCUMIND_OPERATOR": "operator@example.com"}), \
                redirect_stdout(io.StringIO()) as out:
            code = desk_ops.main(["--project", "documind-ai-YOUR-ID", "doc-types", "--tenant", "acme", *args])
        return code, out.getvalue()

    def test_seed_then_follow_on_an_ingested_lane(self):
        db = FakeDB()
        seed = doc_types.registry_from_manifest()
        hb = f"acme_{seed['acme/hr_policy_2026.md']['sha256']}"
        for name, key in (("acme/hr_policy_2026.md", hb), ("acme/msa_acme_2026.md", "acme_other"),
                          ("acme/annual_report_2026_fig3.png", "acme_fig3")):
            db.write(("sources", name.replace("/", "~")), {"tenant_id": "acme", "name": name, "doc_key": key,
                                                         "status": "indexed"}, False)
        chunk(db, f"acme:{hb[5:]}#0", "acme/hr_policy_2026.md", hb, "unknown")
        code, out = self.run_cmd(db, "--seed", "manifest", "--dry-run")
        self.assertEqual((code, doc_types.read_registry(db, "acme")), (0, {}))           # a dry run writes nothing
        code, out = self.run_cmd(db, "--seed", "manifest")
        reg = doc_types.read_registry(db, "acme")
        self.assertEqual(code, 0)
        self.assertEqual((reg["acme/hr_policy_2026.md"]["pin"], reg["acme/hr_policy_2026.md"]["set_by"]), (hb, "operator@example.com"))
        self.assertEqual(reg["acme/annual_report_2026_fig3.png"]["pin"], "acme_fig3")
        self.assertNotIn("acme/msa_acme_2026.md", reg)                                       # the mismatch is printed
        self.assertIn('"action": "mismatch"', out)
        self.assertIn("relabel 1 rows", out)                                                 # the view, after the seed
        code, out = self.run_cmd(db, "--follow", "msa_acme_2026.md")
        msa = doc_types.read_registry(db, "acme")["acme/msa_acme_2026.md"]
        self.assertEqual((code, msa["doc_type"], msa["pin"], msa["source"]), (0, "contract", "acme_other", "operator"))
        code, out = self.run_cmd(db, "--seed", "manifest")
        self.assertEqual(doc_types.read_registry(db, "acme")["acme/msa_acme_2026.md"]["pin"], "acme_other")   # kept
        code, out = self.run_cmd(db, "--follow", "whiteboard_arch.png")
        self.assertEqual(code, 2)
        db.write(("sources", "acme~annual_report_2026_fig3.png"), {"doc_key": "acme_replaced"}, True)   # a member's overwrite
        code, out = self.run_cmd(db, "--seed", "manifest")
        self.assertEqual(doc_types.read_registry(db, "acme")["acme/annual_report_2026_fig3.png"]["pin"], "acme_fig3")
        line = next(json.loads(x) for x in out.splitlines() if x.startswith('{"seed": "acme/annual_report_2026_fig3.png"'))
        self.assertEqual((line["action"], line["registered"]), ("mismatch", "acme_fig3"))

    def test_the_export_is_what_route_eval_reads(self):
        """--export writes the registry in the shape route_eval.py --registry reads; a second tenant's run adds to it."""
        import tempfile
        route_eval = _load("route_eval_for_export", ROOT / "evals" / "route_eval.py")
        db = FakeDB()
        lane(db)
        doc_types.set_class(db, "zeta", "zeta/hr_policy_zeta_2026.md", "policy", "zeta_x", "operator@example.com",
                            "manifest")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "doc_types.json")
            code, out = self.run_cmd(db, "--export", path, "--json")
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out.splitlines()[0]), {"export": path, "tenant": "acme", "objects": 3})
            fs = types.SimpleNamespace(Client=lambda project=None: db)
            cloud = types.ModuleType("google.cloud")
            cloud.firestore = fs
            with patch.dict(sys.modules, {"google": types.ModuleType("google"), "google.cloud": cloud,
                                          "google.cloud.firestore": fs}), redirect_stdout(io.StringIO()):
                desk_ops.main(["--project", "documind-ai-YOUR-ID", "doc-types", "--tenant", "zeta", "--export", path])
            classes = route_eval.classes_from_registry(path)
        self.assertEqual(classes, {("acme", "hr_policy_2026.md"): "policy", ("acme", "posh_act_2013.pdf"): "statute",
                                   ("acme", "annual_report_2026_fig3.png"): "report",
                                   ("zeta", "hr_policy_zeta_2026.md"): "policy"})

    def test_the_make_target(self):
        mk = (ROOT / "mk" / "agents.mk").read_text(encoding="utf-8")
        self.assertIn("commands/desk_ops.py --project $(PROJECT) doc-types --tenant $(TENANT)", mk)
        self.assertIn("services/ingest/relabel.py --project $(PROJECT) --tenant $(TENANT) $(if $(APPLY),--apply,) $(if $(RESET),--reset,)", mk)
        phony = (ROOT / "Makefile").read_text(encoding="utf-8").split(".PHONY:", 1)[1].split("\n\n", 1)[0]
        self.assertIn("doc-types", phony.split())


if __name__ == "__main__":
    unittest.main()
