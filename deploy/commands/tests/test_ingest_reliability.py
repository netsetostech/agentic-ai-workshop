"""Offline checks for the ingest path's reliability fixes of 13 October 2026, from workshop lesson 8.4's review.

Run: python -m unittest discover -s commands/tests -p test_ingest_reliability.py      (from deploy/)

Covered: the claim's lease (services/ingest/idempotency.py: LEASE_SECONDS, BATCH_LEASE_SECONDS, retake_expired()) -
a claim inside its lease is held, one past it is taken back once and restamped, a batch job's claim holds for the
job's timeout, a claim that moved on is left alone - and push() in services/ingest/main.py on it: a redelivery inside
the lease is nacked with a 409 and indexes nothing, one after it takes the cut-off claim back and indexes, a batch
claim is acked, and a finished or queued claim is acked as before. The walk's plan for a cut-off claim (a reingest,
which the lease now lets through). The retired ids leaving the Vector Search index (reconcile.py remove_vectors(),
on the walk's retire and on --retire, over a stubbed index), with VECTOR_INDEX_NAME from mk/lifecycle.mk and
terraform/reconcile.tf; nothing touched without an index. The lifecycle metric (terraform/alerts.tf ingest_events)
counting every verdict the worker logs but a refused delivery, and the queued line's hint naming make batch-job first.

Standard library, with a Firestore small enough to read: no cloud client is built and nothing reaches Google Cloud.
main.py builds its clients when imported, so push() is taken out of it whole and run on the real idempotency.py over
that Firestore; it needs pydantic for the worker's contracts (CI installs it) and is skipped without it, and
DOCUMIND_REQUIRE_LIBS=1 turns that skip into a failure.
"""
import ast
import asyncio
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
import logging
import os
import re
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[2]
INGEST = KIT / "services" / "ingest"
NOW = datetime(2026, 10, 13, 9, 30, tzinfo=timezone.utc)
TS, DEL = object(), object()                                  # firestore.SERVER_TIMESTAMP, firestore.DELETE_FIELD


# ------------------------------------------------------------------ a Firestore small enough to read

class Store:
    """Documents by path. A SERVER_TIMESTAMP write stamps the store's clock; a transaction is the plain calls."""

    def __init__(self):
        self.docs, self.clock = {}, NOW

    def put(self, path: tuple, data: dict, merge: bool):
        cur = dict(self.docs.get(path) or {}) if merge else {}
        for k, v in data.items():
            if v is DEL:
                cur.pop(k, None)
            else:
                cur[k] = self.clock if v is TS else v
        self.docs[path] = cur

    def collection(self, name):
        return Coll(self, (name,))

    def batch(self):
        return Batch()

    def transaction(self):
        return types.SimpleNamespace(set=lambda ref, data, merge=False: ref.set(data, merge=merge))


class Snap:
    def __init__(self, ref, d):
        self.reference, self.id, self._d, self.exists = ref, ref.path[-1], d, d is not None

    def to_dict(self):
        return dict(self._d) if self._d is not None else None

    def get(self, field):
        return (self._d or {}).get(field)


class Ref:
    def __init__(self, st, path):
        self.st, self.path = st, path

    @property
    def id(self):
        return self.path[-1]

    def get(self, transaction=None):
        return Snap(self, self.st.docs.get(self.path))

    def set(self, data, merge=False):
        self.st.put(self.path, data, merge)

    def update(self, data):
        self.st.put(self.path, data, True)


class Coll:
    def __init__(self, st, path, filters=()):
        self.st, self.path, self.filters = st, path, tuple(filters)

    def document(self, key):
        return Ref(self.st, self.path + (key,))

    def where(self, field, op, value):
        assert op == "==", op
        return Coll(self.st, self.path, self.filters + ((field, value),))

    def stream(self):
        return iter([Snap(Ref(self.st, p), d) for p, d in list(self.st.docs.items())
                     if len(p) == len(self.path) + 1 and p[:-1] == self.path
                     and all(d.get(f) == v for f, v in self.filters)])


class Batch:
    def __init__(self):
        self.ops = []

    def update(self, ref, data, option=None):
        self.ops.append((ref, data))

    def set(self, ref, data, merge=False):
        self.ops.append((ref, data))

    def commit(self):
        for ref, data in self.ops:
            ref.update(data)
        self.ops = []


FIRESTORE = types.SimpleNamespace(SERVER_TIMESTAMP=TS, DELETE_FIELD=DEL, Client=object, Transaction=object,
                                  transactional=lambda f: f)


def cloud_modules(db=None, gcs=None) -> dict:
    """google.cloud's firestore and storage as stand-ins, so `from google.cloud import firestore` never finds the real one."""
    fs = types.ModuleType("google.cloud.firestore")
    fs.__dict__.update(vars(FIRESTORE))
    fs.Client = lambda project=None: db
    storage = types.ModuleType("google.cloud.storage")
    storage.Client = lambda project=None: gcs
    cloud = types.ModuleType("google.cloud")
    cloud.firestore, cloud.storage = fs, storage
    google = types.ModuleType("google")
    google.cloud = cloud
    return {"google": google, "google.cloud": cloud, "google.cloud.firestore": fs, "google.cloud.storage": storage}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, cloud_modules()):
        spec.loader.exec_module(mod)
    return mod


idem = load("idempotency_kf1", INGEST / "idempotency.py")
reconcile = load("reconcile_kf1", INGEST / "reconcile.py")


def read(*parts) -> str:
    return (KIT.joinpath(*parts)).read_text(encoding="utf-8")


class Lines(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


@contextlib.contextmanager
def worker_log():
    """The worker's logger ("documind.ingest", which claim() writes too), captured and kept off the console."""
    logger, grab = logging.getLogger("documind.ingest"), Lines()
    saved = (logger.level, logger.propagate)
    logger.addHandler(grab)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        yield grab.lines
    finally:
        logger.removeHandler(grab)
        logger.setLevel(saved[0])
        logger.propagate = saved[1]


def events(lines: list) -> list:
    return [json.loads(line).get("event") for line in lines if line.startswith("{")]


# ------------------------------------------------------------------ the lease, on its own

class LeaseTests(unittest.TestCase):
    KEY, URI = "acme_s1", "gs://lab-uploads/acme/policy.md"

    def claim_row(self, age_s, **extra):
        db = Store()
        db.docs[("documents", self.KEY)] = {"gcs_uri": self.URI, "tenant_id": "acme", "status": "processing",
                                            "claimed_at": NOW - timedelta(seconds=age_s), **extra}
        return db

    def test_the_lease_is_the_ack_deadline_and_the_batch_jobs_timeout_with_a_minute(self):
        sub = read("terraform", "eventarc.tf").split('resource "google_pubsub_subscription" "ingest_push" {', 1)[1]
        ack = int(re.search(r"(?m)^  ack_deadline_seconds = (\d+)$", sub).group(1))
        timeout = int(re.search(r"--timeout=(\d+)", read("commands", "lesson-12.5.sh")).group(1))
        job = int(re.search(r'(?m)^      timeout\s+= "(\d+)s"', read("terraform", "batch.tf")).group(1))
        self.assertEqual((ack, timeout), (600, 600))
        self.assertEqual(idem.LEASE_SECONDS, ack + 60)
        self.assertEqual(idem.BATCH_LEASE_SECONDS, job + 60)
        self.assertEqual(idem.lease_of({}), idem.LEASE_SECONDS)
        self.assertEqual(idem.lease_of({"lane": "batch"}), idem.BATCH_LEASE_SECONDS)

    def test_inside_its_lease_a_claim_is_held_and_nothing_is_written(self):
        db = self.claim_row(300)
        before = dict(db.docs[("documents", self.KEY)])
        got = idem.retake_expired(db, self.KEY, self.URI, "acme", now=NOW)
        self.assertEqual(got, {"verdict": "held", "lane": "push", "status": "processing", "age_s": 300,
                               "lease_s": idem.LEASE_SECONDS})
        self.assertEqual(db.docs[("documents", self.KEY)], before)

    def test_past_its_lease_a_claim_is_taken_back_once(self):
        db = self.claim_row(idem.LEASE_SECONDS + 1, error="kept")
        old = db.docs[("documents", self.KEY)]["claimed_at"]
        db.clock = NOW + timedelta(seconds=1)
        got = idem.retake_expired(db, self.KEY, self.URI, "acme", now=NOW)
        self.assertEqual((got["verdict"], got["age_s"]), ("retaken", idem.LEASE_SECONDS + 1))
        row = db.docs[("documents", self.KEY)]
        self.assertEqual((row["status"], row["claimed_at"], row["retaken_from"]), ("processing", db.clock, old))
        self.assertEqual((row["gcs_uri"], row["tenant_id"], row["error"]), (self.URI, "acme", "kept"))
        # the second delivery reads the restamped claim: a live lease again, so exactly one of the two indexes
        again = idem.retake_expired(db, self.KEY, self.URI, "acme", now=NOW + timedelta(seconds=2))
        self.assertEqual(again["verdict"], "held")

    def test_the_lease_runs_out_at_its_last_second(self):
        held = idem.retake_expired(self.claim_row(idem.LEASE_SECONDS - 1), self.KEY, self.URI, "acme", now=NOW)
        gone = idem.retake_expired(self.claim_row(idem.LEASE_SECONDS), self.KEY, self.URI, "acme", now=NOW)
        self.assertEqual((held["verdict"], gone["verdict"]), ("held", "retaken"))

    def test_a_batch_jobs_claim_holds_for_the_jobs_timeout(self):
        db = self.claim_row(idem.LEASE_SECONDS * 3, lane="batch")
        got = idem.retake_expired(db, self.KEY, self.URI, "acme", now=NOW)
        self.assertEqual((got["verdict"], got["lane"], got["lease_s"]), ("held", "batch", idem.BATCH_LEASE_SECONDS))
        db = self.claim_row(idem.BATCH_LEASE_SECONDS + 5, lane="batch")
        got = idem.retake_expired(db, self.KEY, self.URI, "acme", now=NOW)
        self.assertEqual((got["verdict"], got["lane"]), ("retaken", "batch"))
        self.assertNotIn("lane", db.docs[("documents", self.KEY)])       # the push lane holds it now

    def test_a_claim_that_moved_on_is_left_alone(self):
        for status in ("indexed", "failed", "queued", "superseded"):
            db = self.claim_row(idem.LEASE_SECONDS * 2)
            db.docs[("documents", self.KEY)]["status"] = status
            before = dict(db.docs[("documents", self.KEY)])
            got = idem.retake_expired(db, self.KEY, self.URI, "acme", now=NOW)
            self.assertEqual((got["verdict"], got["status"]), ("moved", status))
            self.assertEqual(db.docs[("documents", self.KEY)], before)
        got = idem.retake_expired(Store(), self.KEY, self.URI, "acme", now=NOW)
        self.assertEqual((got["verdict"], got["status"]), ("moved", None))

    def test_a_claim_with_no_clock_has_no_lease(self):
        db = self.claim_row(0)
        del db.docs[("documents", self.KEY)]["claimed_at"]
        got = idem.retake_expired(db, self.KEY, self.URI, "acme", now=NOW)
        self.assertEqual((got["verdict"], got["age_s"]), ("retaken", None))

    def test_claim_still_refuses_a_processing_claim(self):
        # claim() is unchanged: the lease is asked for by push() after a refusal, never by claim() itself
        with worker_log() as lines:
            self.assertFalse(idem.claim(self.claim_row(idem.LEASE_SECONDS * 2), self.KEY, self.URI, "acme"))
        self.assertEqual(events(lines), ["ingest_duplicate"])

    def test_the_walk_plans_a_reingest_for_a_cut_off_claim(self):
        # The walk's rewrite is the delivery that, long after the lease, now takes the claim back.
        self.assertEqual(reconcile.decide_bytes("s1", "acme", None, {self.KEY: {"status": "processing"}}), "reingest")


# ------------------------------------------------------------------ push(), taken out of main.py whole

class HTTPException(Exception):
    def __init__(self, status_code, detail=None):
        super().__init__(status_code, detail)
        self.status_code, self.detail = status_code, detail


class Request:
    def __init__(self, envelope):
        self._envelope = envelope

    async def json(self):
        return self._envelope


class Blob:
    def __init__(self, content):
        self.content = content

    def download_as_bytes(self):
        return self.content


def contracts_or_skip(test):
    try:
        sys.path.insert(0, str(INGEST))
        import contracts                                   # noqa: F401  pydantic
        import pydantic
        return contracts, pydantic
    except ImportError:
        if os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1":
            raise
        test.skipTest("pydantic is not installed")
    finally:
        sys.path.remove(str(INGEST))


class PushLeaseTests(unittest.TestCase):
    CONTENT = b"# Policy\n\nNP-01 Notice is thirty days.\n"
    NAME = "acme/policy.md"

    def setUp(self):
        contracts, pydantic = contracts_or_skip(self)
        self.db, self.indexed = Store(), []
        src = read("services", "ingest", "main.py")
        node = next(n for n in ast.parse(src).body if isinstance(n, ast.AsyncFunctionDef) and n.name == "push")
        ns = {"base64": base64, "json": json, "Request": object, "HTTPException": HTTPException,
              "ValidationError": pydantic.ValidationError, "IngestMessage": contracts.IngestMessage,
              "DocumentContract": contracts.DocumentContract, "sha256_of": contracts.sha256_of,
              "effective_from_of": contracts.effective_from_of, "NotFound": type("NotFound", (Exception,), {}),
              "log": logging.getLogger("documind.ingest"), "_db": self.db,
              "_gcs": types.SimpleNamespace(bucket=lambda b: types.SimpleNamespace(
                  blob=lambda name, generation=None: Blob(self.CONTENT))),
              "INDEX_NAME": "", "_mirror": types.SimpleNamespace(active=False), "EMBEDDING_MODEL": "text-embedding-005",
              "EMBEDDING_VERSION": "1", "RETENTION_DAYS": 30, "_expire_at": lambda days: NOW + timedelta(days=days),
              "IngestFailed": type("IngestFailed", (Exception,), {}),
              "index_document": lambda doc, msg, content: self.indexed.append(doc.doc_key) or {"status": "indexed"}}
        for name in ("claim", "current_chunks", "finish", "reactivate", "record_source", "refresh_fingerprint",
                     "retake_expired", "retire_previous", "source_id_for", "stale_generation", "status_of", "withdrawn"):
            ns[name] = getattr(idem, name)
        exec(compile(ast.get_source_segment(src, node), "services/ingest/main.py", "exec"), ns)
        self.push = ns["push"]
        self.key = "acme_" + hashlib.sha256(self.CONTENT).hexdigest()

    def deliver(self):
        record = {"bucket": "lab-uploads", "name": self.NAME, "size": str(len(self.CONTENT)),
                  "contentType": "text/markdown", "generation": "1760000000000001"}
        envelope = {"message": {"data": base64.b64encode(json.dumps(record).encode()).decode()}}
        with worker_log() as lines:
            try:
                return asyncio.run(self.push(Request(envelope))), lines
            except HTTPException as e:
                return e, lines

    def claimed(self, age_s, **extra):
        self.db.docs[("documents", self.key)] = {"gcs_uri": f"gs://lab-uploads/{self.NAME}", "tenant_id": "acme",
                                                 "status": "processing",
                                                 "claimed_at": datetime.now(timezone.utc) - timedelta(seconds=age_s),
                                                 **extra}

    def test_a_first_delivery_claims_and_indexes(self):
        got, lines = self.deliver()
        self.assertEqual(got, {"status": "indexed"})
        self.assertEqual((self.indexed, self.db.docs[("documents", self.key)]["status"]), ([self.key], "processing"))

    def test_a_redelivery_inside_the_lease_is_nacked_and_indexes_nothing(self):
        self.claimed(120)
        before = dict(self.db.docs[("documents", self.key)])
        got, lines = self.deliver()
        self.assertIsInstance(got, HTTPException)
        self.assertEqual(got.status_code, 409)                 # any non-2xx is a nack on a push subscription
        self.assertEqual((self.indexed, self.db.docs[("documents", self.key)]), ([], before))
        self.assertEqual(events(lines), ["ingest_duplicate", "ingest_claim_held"])
        held = json.loads(lines[-1])
        self.assertEqual((held["tenant"], held["lane"], held["lease_s"]), ("acme", "push", idem.LEASE_SECONDS))
        self.assertGreaterEqual(held["age_s"], 120)

    def test_a_redelivery_after_the_lease_takes_the_cut_off_claim_back_and_indexes(self):
        self.claimed(idem.LEASE_SECONDS + 30)
        old = self.db.docs[("documents", self.key)]["claimed_at"]
        got, lines = self.deliver()
        self.assertEqual((got, self.indexed), ({"status": "indexed"}, [self.key]))
        row = self.db.docs[("documents", self.key)]
        self.assertEqual((row["status"], row["retaken_from"], row["claimed_at"]), ("processing", old, NOW))
        self.assertEqual(events(lines), ["ingest_duplicate", "ingest_claim_retaken"])

    def test_a_claim_the_batch_job_holds_is_acked(self):
        self.claimed(idem.LEASE_SECONDS * 2, lane="batch")
        got, lines = self.deliver()
        self.assertEqual((got, self.indexed), ({"status": "batch_processing", "doc_key": self.key}, []))
        self.assertEqual(events(lines), ["ingest_duplicate", "ingest_claim_held"])

    def test_finished_and_queued_claims_are_acked_as_before(self):
        for status, want in (("indexed", "duplicate"), ("queued", "queued_batch")):
            self.db.docs[("documents", self.key)] = {"status": status, "claimed_at": NOW - timedelta(days=1)}
            got, lines = self.deliver()
            self.assertEqual((got, self.indexed), ({"status": want, "doc_key": self.key}, []), status)
            self.assertEqual(events(lines), ["ingest_duplicate"], status)


# ------------------------------------------------------------------ the walk and --retire take the ids out of the index

class Bucket:
    def __init__(self, names):
        self.names = names

    def list_blobs(self, prefix=None):
        return [types.SimpleNamespace(name=n, generation=g) for n, g in self.names.items()
                if not prefix or n.startswith(prefix)]

    def get_blob(self, name):
        return types.SimpleNamespace(name=name, generation=self.names[name]) if name in self.names else None


class RetireTests(unittest.TestCase):
    URI = "gs://lab-uploads/acme/old.md"

    def lane(self):
        db = Store()
        for i in range(3):
            db.docs[("chunks", f"acme:s3#{i}")] = {"tenant_id": "acme", "source_uri": self.URI, "doc_key": "acme_s3",
                                                  "current": True}
        db.docs[("chunks", "acme:s1#0")] = {"tenant_id": "acme", "source_uri": "gs://lab-uploads/acme/kept.md",
                                           "doc_key": "acme_s1", "current": True}
        db.docs[("sources", "acme~old.md")] = {"tenant_id": "acme", "name": "acme/old.md", "gcs_uri": self.URI,
                                               "doc_key": "acme_s3", "generation": "4", "sha256": "s3",
                                               "status": "indexed"}
        db.docs[("sources", "acme~kept.md")] = {"tenant_id": "acme", "name": "acme/kept.md",
                                                "gcs_uri": "gs://lab-uploads/acme/kept.md", "doc_key": "acme_s1",
                                                "generation": "2", "sha256": "s1", "status": "indexed"}
        return db

    def run_reconcile(self, db, objects, argv, index=None):
        removed, mirrored = [], []
        indexer = types.ModuleType("indexer")
        indexer.remove_datapoints = lambda name, ids: removed.append((name, list(ids)))
        managed = types.ModuleType("managed")
        managed.Mirror = types.SimpleNamespace(from_env=lambda db_, mode: types.SimpleNamespace(
            retired=lambda tenant, keys, why: mirrored.append((tenant, keys, why))))
        contracts = types.ModuleType("contracts")
        contracts.sha256_of = lambda b: hashlib.sha256(b).hexdigest()
        gcs = types.SimpleNamespace(bucket=lambda name: Bucket(objects))
        mods = {**cloud_modules(db, gcs), "idempotency": idem, "indexer": indexer, "managed": managed,
                "contracts": contracts}
        env = {"VECTOR_INDEX_NAME": index} if index else {}
        out = io.StringIO()
        with patch.dict(sys.modules, mods), patch.dict(os.environ, env), \
                patch.object(sys, "argv", ["reconcile.py", "--project", "lab", *argv]), \
                contextlib.redirect_stdout(out), worker_log():
            if not index:
                os.environ.pop("VECTOR_INDEX_NAME", None)
            rc = reconcile.main()
        return rc, [json.loads(line) for line in out.getvalue().splitlines() if line.startswith("{")], removed, mirrored

    def test_remove_vectors_over_a_stubbed_index(self):
        calls = []
        gone = {"retired_ids": ["acme:s3#0", "acme:s3#1"]}
        self.assertEqual(reconcile.remove_vectors("projects/p/locations/r/indexes/9", gone,
                                                  remove=lambda name, ids: calls.append((name, ids))), 2)
        self.assertEqual(calls, [("projects/p/locations/r/indexes/9", ["acme:s3#0", "acme:s3#1"])])
        self.assertEqual(gone["datapoints_removed"], 2)
        nothing = {"retired_ids": []}
        self.assertEqual(reconcile.remove_vectors("idx", nothing, remove=lambda *a: calls.append(a)), 0)
        self.assertEqual((len(calls), nothing["datapoints_removed"]), (1, 0))
        no_index = {"retired_ids": ["acme:s3#0"]}
        self.assertEqual(reconcile.remove_vectors("", no_index, remove=lambda *a: calls.append(a)), 0)
        self.assertEqual((len(calls), "datapoints_removed" in no_index), (1, False))

    def test_retire_by_hand_removes_the_withdrawn_sources_datapoints(self):
        db = self.lane()
        rc, lines, removed, mirrored = self.run_reconcile(
            db, {"acme/old.md": "4", "acme/kept.md": "2"}, ["--retire", "acme/old.md", "--apply"], index="idx-9")
        self.assertEqual(rc, 0)
        self.assertEqual(removed, [("idx-9", ["acme:s3#0", "acme:s3#1", "acme:s3#2"])])
        line = next(x for x in lines if x.get("event") == "reconcile_withdrawn")
        self.assertEqual((line["retired_chunks"], line["datapoints_removed"]), (3, 3))
        self.assertEqual(db.docs[("sources", "acme~old.md")]["status"], "withdrawn")
        self.assertEqual(mirrored, [("acme", ["acme_s3"], "withdrawn")])
        self.assertTrue(db.docs[("chunks", "acme:s1#0")]["current"])          # the other source keeps its rows

    def test_the_walk_removes_the_datapoints_of_a_source_gone_from_the_bucket(self):
        db = self.lane()
        rc, lines, removed, mirrored = self.run_reconcile(db, {"acme/kept.md": "2"}, ["--apply"], index="idx-9")
        self.assertEqual(rc, 0)
        self.assertEqual(removed, [("idx-9", ["acme:s3#0", "acme:s3#1", "acme:s3#2"])])
        line = next(x for x in lines if x.get("event") == "reconcile_retired")
        self.assertEqual(line["datapoints_removed"], 3)
        self.assertEqual(db.docs[("sources", "acme~old.md")]["status"], "retired")
        self.assertEqual(lines[-1]["event"], "reconcile_done")

    def test_without_an_index_the_rows_are_retired_and_the_index_is_not_touched(self):
        db = self.lane()
        rc, lines, removed, mirrored = self.run_reconcile(db, {"acme/kept.md": "2"}, ["--apply"])
        line = next(x for x in lines if x.get("event") == "reconcile_retired")
        self.assertEqual((rc, removed, line["retired_chunks"], "datapoints_removed" in line), (0, [], 3, False))

    def test_the_index_reaches_the_walk_and_make_retire(self):
        job = read("terraform", "reconcile.tf")
        self.assertRegex(job, r'name  = "VECTOR_INDEX_NAME"[^\n]*\n\s+value = google_vertex_ai_index\.documind\.id\n')
        mk = read("mk", "lifecycle.mk")
        for target in ("retire", "reconcile"):
            recipe = re.search(rf"(?ms)^{target}: guard-project\n(.*?)\n\n", mk).group(1)
            self.assertIn("VECTOR_INDEX_NAME=$${VECTOR_INDEX_NAME:-$$(cd $(TF_DIR) && terraform output -raw "
                          "vector_index_name 2>/dev/null)}", recipe, target)
            self.assertIn("services/ingest/reconcile.py", recipe, target)


# ------------------------------------------------------------------ what the lifecycle metric counts, and the queue's hint

class LifecycleLineTests(unittest.TestCase):
    def test_the_metric_counts_every_verdict_but_a_refused_delivery(self):
        alerts = read("terraform", "alerts.tf")
        metric = alerts.split('resource "google_logging_metric" "ingest_events" {', 1)[1].split("\n}\n", 1)[0]
        counted = re.search(r'jsonPayload\.event=~"\^ingest_\(([a-z_|]+)\)\$"', metric).group(1).split("|")
        main, idm = read("services", "ingest", "main.py"), read("services", "ingest", "idempotency.py")
        logged = {e for e in re.findall(r'"event": ?"ingest_([a-z_]+)"', main + idm) if not e.endswith("_")}
        self.assertIn('"event": "ingest_claim_" + lease["verdict"]', main)        # one line per lease verdict
        logged |= {"claim_" + v for v in re.findall(r'\{"verdict": "(\w+)"', idm)}
        self.assertEqual(len(counted), len(set(counted)))
        self.assertEqual(set(counted), logged - {"duplicate", "claim_held", "claim_moved"})
        described = re.search(r'key         = "event"\n.*?description = "([^"]+)"', metric, re.S).group(1)
        self.assertEqual(described.split(" | "), ["ingest_" + e for e in counted])

    def test_the_queued_line_names_the_job_before_make_batch(self):
        hint = re.search(r'consumer = "no job declared \(BATCH_JOB unset\): ([^"]+)"', read("services", "ingest", "main.py"))
        self.assertLess(hint.group(1).index("make batch-job"), hint.group(1).index("make batch runs"))
        mk = read("mk", "lifecycle.mk")
        self.assertIn("batch: guard-project\n\tgcloud run jobs execute documind-ingest-batch", mk)  # the job must exist


if __name__ == "__main__":
    unittest.main()
