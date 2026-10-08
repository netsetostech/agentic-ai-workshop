#!/usr/bin/env python3
"""Offline checks for the ingestion lifecycle's P3 fixes (course-bibles/rag-production-execution-plan-2026-09-12.md,
tasks 3.1-3.5: the R05 findings of the review). 12 September 2026.

    python tools/check_lifecycle.py

Everything here runs with no credential and no network: idempotency.py against the fake Firestore
tools/check_auth_wiring.py already runs it against (plus a transaction, so claim() runs), the worker's and the
indexer's functions lifted with `ast` (both need cloud clients at import time), reconcile.py's pure planner
imported as it is. Each check names the code change that would turn it red:

  idempotency.claim()        writes tenant_id on documents/{doc_key}; refuses a `superseded` claim unless
                             retake=True, and a `queued` one always.
  retire_previous / swap     stamp retired_at on the superseded version's claim - the undo window's clock.
  idempotency.reactivate()   refuses a withdrawn source (sources/ says so) and flips nothing; refuses a shortfall
                             (the claim says 5 chunks, 3 rows are here) and a stamp older than RETENTION_DAYS,
                             flipping nothing and logging reactivate_incomplete with both numbers; returns the rows
                             flipped otherwise, with the claim's stamps cleared.
  ingest/main.py             push() asks withdrawn() before the undo and acks ingest_withdrawn; re-upserts the
                             reactivated ids before it retires the newer version; takes the claim back
                             (retake=True) and re-ingests when the undo is refused; counts a PDF's pages before Doc
                             AI; _enqueue_batch() leaves the claim `queued` with the object, its generation and its
                             type, starts the batch job by name when one is declared (BATCH_JOB) and says which on
                             the line; a start that fails is one warning and the queue stands (13 September 2026).
  idempotency.take_batch()   the batch job's take: queued -> processing in a transaction, False for anything else,
                             the claim's fields kept.
  ingest/batch.py            queued() lists the queue oldest first; run_one() takes the claim, fetches the bytes
                             BY GENERATION, refuses bytes that hash to another document, runs the worker's own
                             index_document() with lane="batch", records the result; a gone generation is released
                             and recorded gone; a failed pipeline leaves the claim released and the record failed.
  reconcile.plan()           a withdrawn source with its object present yields no reingest ("withdrawn, object
                             kept"); with the object gone, no retire; a queued generation is skipped, not hashed;
                             neither is drift; --retire writes `withdrawn`; --restore exists; the selftest passes.
  indexer.to_datapoints()    every datapoint carries the doc_type restrict beside tenant_id, kind and current;
                             reupsert() rebuilds the same restricts from the rows and upserts the current ones.
  Makefile, INDEXING.md      `restore:` exists and runs --restore; the page names withdrawn, queued, make restore,
                             reactivate_incomplete and the batch job that consumes the queue, and no longer
                             presents deleting the object and make retire as one thing.
"""
from __future__ import annotations

import ast
import importlib.util
import io
import json
import logging
import math
import os
import re
import subprocess
import sys
import types
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INGEST = os.path.join(ROOT, "deploy", "services", "ingest")
PASSED = []
DEL = "<delete>"
TS = "<ts>"


def ok(msg):
    PASSED.append(msg)
    print(f"  ok   {msg}")


def read(rel: str) -> str:
    return open(os.path.join(ROOT, rel), encoding="utf-8").read()


def kit_makefile(*parts: str) -> str:
    """The kit's Makefile and mk/*.mk as one text (22 September 2026): the targets of a lane live in mk/<lane>.mk."""
    import glob as _glob
    base = read(*parts) if len(parts) > 1 else read(parts[0])
    root = os.path.join(ROOT, "deploy", "mk")
    return base + "".join("\n" + open(p, encoding="utf-8").read() for p in sorted(_glob.glob(os.path.join(root, "*.mk"))))


def lift(path: str, names: list[str], **consts):
    """Exec only the named top-level defs/assignments of a module, with the constants given (check_media_contract's)."""
    src = read(path)
    pieces = []
    for node in ast.parse(src).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            pieces.append(ast.get_source_segment(src, node))
        elif isinstance(node, ast.Assign):
            targets = []
            for t in node.targets:
                targets += [e.id for e in t.elts if isinstance(e, ast.Name)] if isinstance(t, ast.Tuple) \
                    else ([t.id] if isinstance(t, ast.Name) else [])
            if set(targets) & set(names):
                pieces.append(ast.get_source_segment(src, node))
    ns = dict(consts)
    ns["__builtins__"] = __builtins__
    exec("\n\n".join(pieces), ns)
    return ns


# ---------------------------------------------------------------- the fake Firestore (check_auth_wiring's, plus a transaction)
class _Ref:
    def __init__(self, store, coll, key): self.store, self.coll, self.key = store, coll, key

    def get(self, transaction=None):
        d = self.store.setdefault(self.coll, {}).get(self.key)
        return types.SimpleNamespace(exists=d is not None, id=self.key, reference=self,
                                     to_dict=lambda: dict(d) if d else None, get=lambda f: (d or {}).get(f))

    def set(self, data, merge=False):
        cur = self.store.setdefault(self.coll, {}).get(self.key) or {}
        new = {**cur, **data} if merge else dict(data)
        self.store[self.coll][self.key] = {k: v for k, v in new.items() if not (isinstance(v, str) and v == DEL)}

    def update(self, data):
        self.set(data, merge=True)


class _Query:
    def __init__(self, store, coll, filters=()): self.store, self.coll, self.filters = store, coll, list(filters)

    def where(self, f, op, v): return _Query(self.store, self.coll, self.filters + [(f, v)])

    def stream(self):
        for key, d in list(self.store.setdefault(self.coll, {}).items()):
            if all(d.get(f) == v for f, v in self.filters):
                yield _Ref(self.store, self.coll, key).get()


class _Coll(_Query):
    def document(self, key): return _Ref(self.store, self.coll, key)


class _DB:
    def __init__(self): self.store = {}

    def collection(self, name): return _Coll(self.store, name)

    def batch(self):
        ops = []
        return types.SimpleNamespace(update=lambda ref, data: ops.append((ref, data, True)),
                                     set=lambda ref, data, merge=False: ops.append((ref, data, merge)),
                                     commit=lambda: [ref.set(data, merge=m) for ref, data, m in ops] and ops.clear())

    def transaction(self):
        return types.SimpleNamespace(set=lambda ref, data: ref.set(data))


class _Lines(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


def load_idempotency():
    """idempotency.py with google.cloud.firestore stubbed: SERVER_TIMESTAMP and DELETE_FIELD are markers and the
    transaction decorator is the identity, so claim() runs its transaction body against the fake above."""
    stub = types.SimpleNamespace(SERVER_TIMESTAMP=TS, DELETE_FIELD=DEL, Client=object, Transaction=object,
                                 transactional=lambda f: f)
    try:
        import google.cloud.firestore  # noqa: F401
    except ImportError:
        mod = types.ModuleType("google.cloud.firestore")
        for k, v in vars(stub).items():
            setattr(mod, k, v)
        g = sys.modules.get("google") or types.ModuleType("google")
        gc = sys.modules.get("google.cloud") or types.ModuleType("google.cloud")
        gc.firestore, g.cloud = mod, gc
        sys.modules.setdefault("google", g)
        sys.modules.setdefault("google.cloud", gc)
        sys.modules["google.cloud.firestore"] = mod
    spec = importlib.util.spec_from_file_location("idempotency_lifecycle", os.path.join(INGEST, "idempotency.py"))
    idem = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(idem)
    idem.firestore = stub            # the real package, when it is installed, would want a real transaction
    return idem


def _rows(db, doc_key: str, uri: str, n: int, current: bool, **extra) -> None:
    sha = doc_key.split("_", 1)[1]
    for i in range(n):
        db.collection("chunks").document(f"acme:{sha}#{i}").set(
            {"tenant_id": "acme", "source_uri": uri, "doc_key": doc_key, "current": current, "text": f"{sha} {i}", **extra})


def main() -> int:
    idem = load_idempotency()
    lines = _Lines()
    logging.getLogger("documind.ingest").addHandler(lines)
    logging.getLogger("documind.ingest").setLevel(logging.INFO)
    U = "gs://b/acme/hr_policy_2026.md"
    SID = "acme~hr_policy_2026.md"

    # ------------------------------------------------------------------ 3.4: claim() writes tenant_id; retake
    db = _DB()
    assert idem.claim(db, "acme_s1", U, "acme") is True
    row = db.store["documents"]["acme_s1"]
    assert row.get("tenant_id") == "acme", f"claim() must write tenant_id on the claim (2.4's filter): {row}"
    assert row["status"] == "processing" and row["gcs_uri"] == U, row
    assert idem.claim(db, "acme_s1", U, "acme") is False, "a second delivery must be refused"
    db.collection("documents").document("acme_s1").set({"status": "superseded"}, merge=True)
    assert idem.claim(db, "acme_s1", U, "acme") is False, "a superseded claim is the undo's, not a fresh claim's"
    assert idem.claim(db, "acme_s1", U, "acme", retake=True) is True and db.store["documents"]["acme_s1"]["status"] == "processing", \
        "retake=True takes a superseded claim back after a refused undo"
    assert db.store["documents"]["acme_s1"]["tenant_id"] == "acme"
    db.collection("documents").document("acme_q").set({"status": "queued", "gcs_uri": U})
    assert idem.claim(db, "acme_q", U, "acme", retake=True) is False, "a queued claim belongs to the batch lane"
    db.collection("documents").document("acme_f").set({"status": "failed"})
    assert idem.claim(db, "acme_f", U, "acme") is True, "a failed claim is claimable, as before"
    ok("claim(): documents/{doc_key} carries tenant_id (2.4's filter); a superseded claim is refused unless retake=True; "
       "a queued one is never retaken; a failed one is claimable")

    # ------------------------------------------------------------------ the other lane's version (13 September 2026)
    db = _DB()
    embedding_stamp = {"embedding_model": "text-embedding-005", "embedding_version": "1",
                       "embedding_task_type": "RETRIEVAL_DOCUMENT"}
    _rows(db, "acme_s1", U, 3, True, **embedding_stamp)   # a notebook's compatible seed
    _rows(db, "acme_s0", U, 2, False, **embedding_stamp)  # its retired predecessor
    _rows(db, "acme_legacy", U, 1, True, embedding_model="text-embedding-005", embedding_version="1")
    _rows(db, "acme_query", U, 1, True, **{**embedding_stamp, "embedding_task_type": "RETRIEVAL_QUERY"})
    assert idem.current_chunks(db, "acme", U, "acme_s1", "text-embedding-005", "1") == 3, "the version the notebook seeded is current"
    assert idem.current_chunks(db, "acme", U, "acme_s0", "text-embedding-005", "1") == 0, "a retired version counts for nothing"
    assert idem.current_chunks(db, "acme", U, "acme_s1", "text-embedding-006", "1") == 0, "another embedding cannot serve this worker"
    assert idem.current_chunks(db, "acme", U, "acme_legacy", "text-embedding-005", "1") == 0, "unstamped legacy embeddings need repair"
    assert idem.current_chunks(db, "acme", U, "acme_query", "text-embedding-005", "1") == 0, "query embeddings cannot stand in for document embeddings"
    assert idem.current_chunks(db, "acme", U, "acme_s1") == 3, "no embedding named: the rows count as they are"
    assert idem.current_chunks(db, "acme", "gs://b/acme/other.md", "acme_s1") == 0, "one source, never another's rows"
    ok("current_chunks(): a version the notebook lane seeded - same doc_key, rows current, no claim - is found by the worker, "
       "per source and per embedding task; a retired version, another embedding or a missing document stamp is not")

    # ------------------------------------------------------------------ retired_at on the superseded claim, both retire paths
    db = _DB()
    _rows(db, "acme_s1", U, 3, True)
    db.collection("documents").document("acme_s1").set({"status": "indexed", "chunks": 3, "gcs_uri": U})
    _rows(db, "acme_s2", U, 2, False, staged=True)
    sw = idem.swap_versions(db, "acme", U, "acme_s2", expire_at="<exp>")
    assert sw["activated"] == 2 and sw["retired_doc_keys"] == ["acme_s1"], sw
    assert db.store["documents"]["acme_s1"]["status"] == "superseded" and db.store["documents"]["acme_s1"].get("retired_at") == TS, \
        "swap_versions stamps retired_at on the superseded claim"
    db2 = _DB()
    _rows(db2, "acme_s3", U, 2, True)
    db2.collection("documents").document("acme_s3").set({"status": "indexed", "chunks": 2})
    idem.retire_previous(db2, "acme", U, None, expire_at="<exp>")
    assert db2.store["documents"]["acme_s3"]["status"] == "superseded" and db2.store["documents"]["acme_s3"].get("retired_at") == TS, \
        "retire_previous stamps retired_at on the retired claim"
    ok("retire_previous() and swap_versions() stamp retired_at on the superseded claim: the undo window's clock")

    # ------------------------------------------------------------------ 3.2: the undo verifies
    # every row here, the claim counts 3, stamped just now -> 3 flipped, the stamps cleared
    back = idem.reactivate(db, "acme", U, "acme_s1")
    assert back == 3 and all(db.store["chunks"][f"acme:s1#{i}"]["current"] is True for i in range(3)), back
    assert db.store["documents"]["acme_s1"]["status"] == "indexed" and "retired_at" not in db.store["documents"]["acme_s1"], \
        "a verified undo clears the claim's stamp"
    # a shortfall: the claim says 5 chunks, 3 rows are here -> refused, nothing flipped, both numbers logged
    db = _DB()
    _rows(db, "acme_s1", U, 3, False, superseded_by="acme_s2", expire_at="<exp>")
    _rows(db, "acme_s2", U, 5, True)
    db.collection("documents").document("acme_s1").set({"status": "superseded", "chunks": 5, "retired_at": TS, "gcs_uri": U})
    lines.lines.clear()
    assert idem.reactivate(db, "acme", U, "acme_s1") is None, "the defect: 3 of 5 rows flipped and reported as the undo"
    assert all(db.store["chunks"][f"acme:s1#{i}"]["current"] is False and db.store["chunks"][f"acme:s1#{i}"]["expire_at"] == "<exp>"
               for i in range(3)), "a refused undo flips nothing and clears no stamp"
    assert db.store["documents"]["acme_s1"]["status"] == "superseded"
    ev = [json.loads(l) for l in lines.lines if "reactivate_incomplete" in l]
    assert ev and ev[0]["rows"] == 3 and ev[0]["chunks"] == 5, ev
    # the window: every row here, but retired 31 days ago against RETENTION_DAYS=30 -> refused
    db.collection("documents").document("acme_s1").set(
        {"chunks": 3, "retired_at": datetime.now(timezone.utc) - timedelta(days=31)}, merge=True)
    lines.lines.clear()
    assert idem.reactivate(db, "acme", U, "acme_s1", retention_days=30) is None, "an undo past the window must be refused"
    ev = [json.loads(l) for l in lines.lines if "reactivate_incomplete" in l]
    assert ev and ev[0]["age_days"] == 31 and ev[0]["retention_days"] == 30 and ev[0]["rows"] == 3 and ev[0]["chunks"] == 3, ev
    assert all(db.store["chunks"][f"acme:s1#{i}"]["current"] is False for i in range(3))
    assert idem.RETENTION_DAYS == int(os.environ.get("RETENTION_DAYS", "30")), "read the way the worker reads it"
    # inside the window -> the count comes back
    db.collection("documents").document("acme_s1").set(
        {"retired_at": datetime.now(timezone.utc) - timedelta(days=29)}, merge=True)
    assert idem.reactivate(db, "acme", U, "acme_s1", retention_days=30) == 3
    assert all(db.store["chunks"][f"acme:s1#{i}"]["current"] is True and "expire_at" not in db.store["chunks"][f"acme:s1#{i}"]
               for i in range(3))
    # a claim from before the stamp (no chunks, no retired_at): the undo runs as it always did
    db = _DB()
    _rows(db, "acme_s1", U, 2, False)
    db.collection("documents").document("acme_s1").set({"status": "superseded"})
    assert idem.reactivate(db, "acme", U, "acme_s1") == 2, "no count and no clock on the claim: nothing to refuse on"
    ok("reactivate() verifies before it flips: a shortfall (5 counted, 3 here) and a stamp past RETENTION_DAYS are "
       "reactivate_incomplete with both numbers and nothing flipped; inside the window the count comes back and the "
       "stamps clear; a pre-stamp claim is flipped as before")

    # ------------------------------------------------------------------ 3.1: the tombstone
    db = _DB()
    _rows(db, "acme_s1", U, 3, False, superseded_by=None, expire_at="<exp>")
    db.collection("documents").document("acme_s1").set({"status": "superseded", "chunks": 3, "retired_at": TS})
    db.collection("sources").document(SID).set({"tenant_id": "acme", "name": "acme/hr_policy_2026.md", "doc_key": "acme_s1",
                                                "status": "withdrawn", "withdrawn_at": TS})
    assert idem.withdrawn(db, "acme", U) is True and idem.withdrawn(db, "acme", "gs://b/acme/other.md") is False
    lines.lines.clear()
    assert idem.reactivate(db, "acme", U, "acme_s1") is None, "the defect: a withdrawn source reactivated"
    assert all(db.store["chunks"][f"acme:s1#{i}"]["current"] is False for i in range(3)), "nothing flipped on a withdrawn source"
    assert any("reactivate_withdrawn" in l for l in lines.lines), lines.lines
    assert idem.corpus_fingerprint(db, "acme")[1] == 0, "a withdrawn source is not a current version"
    db.collection("sources").document(SID).set({"status": "retired"}, merge=True)          # what --restore writes first
    assert idem.withdrawn(db, "acme", U) is False and idem.reactivate(db, "acme", U, "acme_s1") == 3, "the tombstone cleared, the undo runs"
    ok("the tombstone: withdrawn() reads sources/{tenant~name}; reactivate() refuses a withdrawn source and flips nothing "
       "(reactivate_withdrawn); cleared to retired, the same undo runs")

    # ------------------------------------------------------------------ the worker: push() and the batch hand-off
    worker_src = read("deploy/services/ingest/main.py")
    wfns = {n.name: n for n in ast.parse(worker_src).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    body = ast.unparse(wfns["push"]) + "\n" + ast.unparse(wfns["index_document"])   # the handler, then the pipeline both lanes run (13 September 2026)
    assert "claim(_db, doc.doc_key, doc.gcs_uri, doc.tenant_id)" in body, "the claim is given the tenant"
    for needle in ("status_of(_db, doc.doc_key) == 'superseded'", "withdrawn(_db, doc.tenant_id, doc.gcs_uri)", "reactivate(",
                   "reupsert(", "retire_previous(", "retake=True", "if back is not None:", "'ingest_withdrawn'", "'withdrawn'",
                   "status_of(_db, doc.doc_key) == 'queued'", "'queued_batch'", "_pdf_pages(content)",
                   "_parse(content, msg.content_type)", "_enqueue_batch(doc, msg)"):
        assert needle in body, f"push() lost {needle}"
    u = body.index("status_of(_db, doc.doc_key) == 'superseded'")
    assert (u < body.index("withdrawn(_db, doc.tenant_id, doc.gcs_uri)", u) < body.index("reactivate(", u) < body.index("reupsert(", u)
            < body.index("retire_previous(", u) < body.index("retake=True", u)), \
        "withdrawn before the undo; the re-upsert before the newer version is retired; the claim retaken after a refused undo"
    assert body.index("if back is not None:") < body.index("retire_previous(", u), \
        "the undo's result decides whether the newer version is retired"
    assert body.index("_pdf_pages(content)") < body.index("_parse(content, msg.content_type)"), "the page count before Doc AI"
    for needle in ("ingest_withdrawn", "ingest_queued_batch", '"consumer": consumer', "batch_job_start_failed", "from pypdf import PdfReader"):
        assert needle in worker_src, needle
    assert "pypdf" in read("deploy/services/ingest/requirements.txt")
    fake_db, logged = _DB(), []

    def _not_declared():
        raise AssertionError("no job is declared: nothing must be started")
    ns = lift("deploy/services/ingest/main.py", ["_enqueue_batch", "_pdf_pages"], _db=fake_db, json=json, io=io,
              firestore=types.SimpleNamespace(SERVER_TIMESTAMP=TS), log=types.SimpleNamespace(warning=lambda m: logged.append(m)),
              DocumentContract=object, PdfReader=lambda buf: types.SimpleNamespace(pages=[None] * 300),
              BATCH_JOB="", _run_batch_job=_not_declared)
    doc = types.SimpleNamespace(tenant_id="acme", gcs_uri="gs://b/acme/big.pdf", pages=300, doc_key="acme_big")
    msg = types.SimpleNamespace(bucket="b", name="acme/big.pdf", content_type="application/pdf", size=123456, generation="7")
    ns["_enqueue_batch"](doc, msg)
    rec = fake_db.store["ingest_batch"]["acme_big"]
    assert rec["status"] == "queued" and rec["generation"] == "7" and rec["bucket"] == "b" and rec["name"] == "acme/big.pdf" \
        and rec["content_type"] == "application/pdf" and rec["size"] == 123456 and rec["pages"] == 300, rec
    claim_row = fake_db.store.get("documents", {}).get("acme_big") or {}
    assert claim_row.get("status") == "queued" and claim_row.get("generation") == "7", \
        f"the claim must say queued, or the document is a duplicate for ever: {claim_row}"
    line = json.loads(logged[0])
    assert line["event"] == "ingest_queued_batch" and "no job declared" in line["consumer"] and "make batch" in line["consumer"], line
    # the job declared: started by name as the document is queued, and the line says so; a start that fails is one
    # warning, the record and the claim stand queued for the schedule
    started = []
    ns["BATCH_JOB"], ns["_run_batch_job"] = "documind-ingest-batch", lambda: started.append(1) or "operations/op-1"
    logged.clear(); ns["_enqueue_batch"](doc, msg)
    line = json.loads(logged[-1])
    assert started == [1] and line["event"] == "ingest_queued_batch" and "documind-ingest-batch started (operations/op-1)" in line["consumer"], line

    def _refused():
        raise RuntimeError("403: run.jobs.run denied")
    ns["_run_batch_job"] = _refused
    logged.clear(); ns["_enqueue_batch"](doc, msg)
    events = [json.loads(m)["event"] for m in logged]
    assert events == ["batch_job_start_failed", "ingest_queued_batch"] and "could not be started (RuntimeError)" in json.loads(logged[-1])["consumer"], logged
    assert "run.jobs.run denied" in json.loads(logged[0])["error"] and fake_db.store["ingest_batch"]["acme_big"]["status"] == "queued"
    assert ns["_pdf_pages"](b"%PDF-1.7") == 300

    def _bad(buf):
        raise ValueError("not a pdf")
    ns["PdfReader"] = _bad
    assert ns["_pdf_pages"](b"nope") is None, "an unreadable file is Doc AI's to judge"
    ok("the worker: withdrawn() before the undo (ingest_withdrawn), reupsert() before the newer version is retired, "
       "retake=True and a fresh ingest after a refused undo; a PDF counted by pypdf before Doc AI; _enqueue_batch() leaves "
       "the claim queued with the object, its generation and its type, starts the declared job and says which - or says "
       "make batch, or logs the refused start and keeps the queue; a queued redelivery is queued_batch")

    # ------------------------------------------------------------------ the batch lane's consumer (13 September 2026)
    # take_batch(): queued -> processing in a transaction, the fields kept; anything else is False
    db.collection("documents").document("acme_big").set({"status": "queued", "gcs_uri": "gs://b/acme/big.pdf", "generation": "7",
                                                          "pages": 300, "tenant_id": "acme"})
    assert idem.take_batch(db, "acme_big") is True
    taken = db.store["documents"]["acme_big"]
    assert taken["status"] == "processing" and taken["lane"] == "batch" and taken["pages"] == 300 and taken["generation"] == "7" and taken["claimed_at"] == TS, taken
    assert db.store["ingest_batch"]["acme_big"]["status"] == "processing"
    assert idem.take_batch(db, "acme_big") is False, "a second run never takes a claim that is processing"
    db.collection("documents").document("acme_f").set({"status": "failed", "error": "x"})
    assert idem.take_batch(db, "acme_f") is False and idem.take_batch(db, "acme_none") is False, "failed, indexed or absent: not the job's to take"
    ok("take_batch(): a queued claim becomes processing (lane batch, its fields kept) exactly once; failed, indexed or absent claims are refused")

    # batch.py on the fake: queued() oldest first; run_one() through a stand-in worker
    if "google" not in sys.modules or not hasattr(sys.modules["google"], "api_core"):
        api_core = sys.modules.get("google.api_core") or types.ModuleType("google.api_core")
        exc = types.ModuleType("google.api_core.exceptions")

        class NotFound(Exception):
            pass
        exc.NotFound = NotFound
        api_core.exceptions = exc
        g = sys.modules.get("google") or types.ModuleType("google")
        g.api_core = api_core
        sys.modules.setdefault("google", g)
        sys.modules["google.api_core"], sys.modules["google.api_core.exceptions"] = api_core, exc
    from google.api_core.exceptions import NotFound as _NotFound
    sys.path.insert(0, INGEST)
    sys.modules["idempotency"] = idem                        # run_one() imports release and take_batch from it
    spec = importlib.util.spec_from_file_location("batch_lifecycle", os.path.join(INGEST, "batch.py"))
    batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(batch)
    import contracts as _con
    big = b"%PDF-1.7 " + b"x" * 500
    key = _con.DocumentContract(tenant_id="acme", sha256=_con.sha256_of(big), gcs_uri="gs://b/acme/big.pdf", pages=300).doc_key
    bdb = _DB()
    for k, rec in ((key, {"status": "queued", "queued_at": "2026-09-13T10:00:00", "tenant_id": "acme", "gcs_uri": "gs://b/acme/big.pdf",
                          "bucket": "b", "name": "acme/big.pdf", "content_type": "application/pdf", "size": len(big), "pages": 300, "generation": "7"}),
                   ("acme_older", {"status": "queued", "queued_at": "2026-09-13T09:00:00", "tenant_id": "acme", "gcs_uri": "gs://b/acme/old.pdf",
                                   "bucket": "b", "name": "acme/old.pdf", "content_type": "application/pdf", "size": 9, "pages": 260, "generation": "3"}),
                   ("acme_done", {"status": "indexed", "queued_at": "2026-09-13T08:00:00", "gcs_uri": "gs://b/acme/done.pdf", "generation": "1"})):
        bdb.collection("ingest_batch").document(k).set(rec)
        bdb.collection("documents").document(k).set({"status": rec["status"], "gcs_uri": rec["gcs_uri"], "generation": rec["generation"]})
    q = batch.queued(bdb)
    assert [r["doc_key"] for r in q] == ["acme_older", key], "the queue is every queued record, oldest first"
    assert [r["doc_key"] for r in batch.queued(bdb, limit=1)] == ["acme_older"]

    class _Blob:
        def __init__(self, data, generation): self.data, self.generation = data, generation
        def download_as_bytes(self):
            if self.data is None:
                raise _NotFound(f"generation {self.generation} is gone")
            return self.data

    class _Bucket:
        def __init__(self, blobs): self.blobs, self.asked = blobs, []
        def blob(self, name, generation=None):
            self.asked.append((name, generation))
            return _Blob(self.blobs.get(name), generation)
    bucket = _Bucket({"acme/big.pdf": big, "acme/old.pdf": None})
    gcs = types.SimpleNamespace(bucket=lambda name: bucket)
    ran = []

    class _Worker:
        class IngestFailed(Exception):
            pass

        @staticmethod
        def index_document(doc, msg, content, lane="push"):
            ran.append((doc.doc_key, msg.generation, msg.content_type, msg.tenant_id, lane, len(content)))
            if doc.gcs_uri.endswith("boom.pdf"):
                raise _Worker.IngestFailed("ValueError: Doc AI refused the file")
            return {"status": "indexed", "chunks": 412, "reused": 400, "embedded": 12}
    assert batch.run_one(bdb, gcs, q[1], _Worker) == "indexed"
    assert ran == [(key, "7", "application/pdf", "acme", "batch", len(big))], ran
    assert bucket.asked[-1] == ("acme/big.pdf", 7), "the bytes are fetched BY GENERATION, never whatever the object holds now"
    rec = bdb.store["ingest_batch"][key]
    assert rec["status"] == "indexed" and rec["chunks"] == 412 and rec["reused"] == 400 and rec["embedded"] == 12
    assert bdb.store["documents"][key]["status"] == "processing" and bdb.store["documents"][key]["lane"] == "batch", "the take happened; the worker's finish() writes indexed"
    assert batch.run_one(bdb, gcs, q[1], _Worker) == "skipped" and len(ran) == 1, "a claim that is not queued any more is skipped, never re-indexed"
    assert batch.run_one(bdb, gcs, q[0], _Worker) == "gone" and len(ran) == 1
    assert bdb.store["ingest_batch"]["acme_older"]["status"] == "gone" and bdb.store["documents"]["acme_older"]["status"] == "failed" \
        and "generation gone" in bdb.store["documents"]["acme_older"]["error"], "a gone generation is released and recorded, so the successor's own event indexes what is there"
    other = b"%PDF-1.7 other bytes"
    okey = _con.DocumentContract(tenant_id="acme", sha256=_con.sha256_of(other), gcs_uri="gs://b/acme/boom.pdf", pages=300).doc_key
    bucket.blobs["acme/boom.pdf"] = other
    bdb.collection("ingest_batch").document(okey).set({"status": "queued", "queued_at": "2026-09-13T11:00:00", "tenant_id": "acme", "gcs_uri": "gs://b/acme/boom.pdf",
                                                        "bucket": "b", "name": "acme/boom.pdf", "content_type": "application/pdf", "size": len(other), "pages": 300, "generation": "2"})
    bdb.collection("documents").document(okey).set({"status": "queued", "gcs_uri": "gs://b/acme/boom.pdf", "generation": "2"})
    assert batch.run_one(bdb, gcs, batch.queued(bdb)[0], _Worker) == "failed" and ran[-1][0] == okey and ran[-1][4] == "batch"
    assert bdb.store["ingest_batch"][okey]["status"] == "failed" and "Doc AI refused" in bdb.store["ingest_batch"][okey]["error"], "the pipeline's failure is on the record"
    bucket.blobs["acme/boom.pdf"] = b"%PDF-1.7 swapped"
    bdb.collection("ingest_batch").document(okey).set({"status": "queued"}, merge=True)
    bdb.collection("documents").document(okey).set({"status": "queued"}, merge=True)
    assert batch.run_one(bdb, gcs, batch.queued(bdb)[0], _Worker) == "failed" and ran[-1][0] == okey, "bytes that hash to another document never index under this claim"
    assert "does not match the claim" in bdb.store["ingest_batch"][okey]["error"] and "hash to" in bdb.store["documents"][okey]["error"]
    ok("batch.py: queued() lists the queue oldest first; run_one() takes the claim, fetches the bytes by generation, hands them to the worker's "
       "index_document() with lane=batch and records chunks / reused / embedded; a taken claim is skipped, a gone generation is released and "
       "recorded gone, a failed pipeline and a hash that is not the claim's leave the record failed with the reason")

    # ------------------------------------------------------------------ the managed mirror (P9.2, 13 September 2026)
    sys.path.insert(0, os.path.normpath(os.path.join(INGEST, os.pardir, os.pardir)))   # deploy/: the mirror imports shared.tenancy the way the image lays it out
    spec = importlib.util.spec_from_file_location("managed_lifecycle", os.path.join(INGEST, "managed.py"))
    managed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(managed)
    assert managed.check_mode("off") == "off" and managed.check_mode("both") == "both" and managed.check_mode(None) == "off" and managed.check_mode(" Rag_Engine ") == "rag_engine"
    assert managed.check_mode.__code__.co_varnames[:managed.check_mode.__code__.co_argcount] == ("mode",), \
        "the mode is the deployment's capability list and nothing else; where a tenant's text may go is its data_region (13 September 2026, evening)"
    try:
        managed.check_mode("yes")
        raise AssertionError("an unknown MANAGED_MIRROR was accepted")
    except ValueError as e:
        assert "off|rag_engine|vertex_search|both" in str(e)
    assert managed.RagEngineStore("p").region == "us-central1" and managed.RagEngineStore("p", "asia-south1").region == "asia-south1" \
        and managed.VertexSearchStore("p").region == "global", "a store declares where it holds the text"
    assert managed.store_id("Acme Corp") == "documind-acme-corp" and managed.store_id("zeta") == "documind-zeta"
    mdb = _DB()
    for cid, row in (("acme:s2#1", {"tenant_id": "acme", "doc_key": "acme_s2", "text": "second", "current": True, "doc_type": "policy", "effective_from": "2026-04-01"}),
                     ("acme:s2#0", {"tenant_id": "acme", "doc_key": "acme_s2", "text": "first", "current": True, "doc_type": "policy"}),
                     ("acme:s2#2", {"tenant_id": "acme", "doc_key": "acme_s2", "text": "retired words", "current": False}),
                     ("acme:s2#3", {"tenant_id": "acme", "doc_key": "acme_s2", "text": "a figure", "current": True, "kind": "figure"}),
                     ("acme:s1#0", {"tenant_id": "acme", "doc_key": "acme_s1", "text": "another version", "current": True})):
        mdb.collection("chunks").document(cid).set(row)
    text, meta = managed.version_rows(mdb, "acme", "acme_s2")
    assert text == "first\n\nsecond" and meta == {"doc_type": "policy", "effective_from": "2026-04-01"}, (text, meta)
    assert managed.version_rows(mdb, "acme", "acme_none") == ("", {})
    ok("managed.py: MANAGED_MIRROR is refused for an unknown value and judged by nothing else (a store declares its region: us-central1, "
       "global); store ids; version_rows() joins a version's current text chunks in minted order, skipping retired rows and media, with "
       "the rows' doc_type and effective_from")

    class _Store:
        def __init__(self, name, fail=False, missing=(), region="us-central1"):
            self.name, self.fail, self.missing, self.calls, self.region = name, fail, set(missing), [], region

        def upsert(self, tenant_id, doc_key, source_uri, text, meta):
            if tenant_id in self.missing:
                raise managed.NoStore(f"no {self.name} store for {tenant_id}")
            if self.fail:
                raise RuntimeError("503 the store is down")
            self.calls.append(("upsert", tenant_id, doc_key, source_uri, text, dict(meta)))
            return f"{self.name}/{doc_key}"

        def delete(self, tenant_id, doc_key):
            if tenant_id in self.missing:
                raise managed.NoStore(f"no {self.name} store for {tenant_id}")
            if self.fail:
                raise RuntimeError("503 the store is down")
            self.calls.append(("delete", tenant_id, doc_key))
            return 1

        def listing(self, tenant_id):
            return {}
    mlog, audits = [], []
    managed.log = types.SimpleNamespace(info=lambda m: mlog.append(json.loads(m)), warning=lambda m: mlog.append(json.loads(m)))
    good, down, none = _Store("rag_engine"), _Store("vertex_search", fail=True, region="global"), _Store("vertex_search", missing={"zeta"}, region="global")
    mirror = managed.Mirror(mdb, [good, down, none], "both", policy_for=lambda t: "any",
                            audit=lambda action, actor, target, meta: audits.append((action, actor, target, meta)))
    mdoc = types.SimpleNamespace(tenant_id="acme", doc_key="acme_s2", gcs_uri="gs://b/acme/h.md", doc_type="policy", effective_from="2026-04-01")
    mirror.after_swap(mdoc, "first\n\nsecond", {"retired_doc_keys": ["acme_s1", "acme_s2"]}, {"generation": "9", "name": "acme/h.md"})
    assert good.calls == [("upsert", "acme", "acme_s2", "gs://b/acme/h.md", "first\n\nsecond",
                           {"doc_type": "policy", "effective_from": "2026-04-01", "generation": "9", "name": "acme/h.md"}),
                          ("delete", "acme", "acme_s1")], good.calls
    events = [(m["event"], m.get("store"), m.get("op")) for m in mlog]
    assert ("mirror_ok", "rag_engine", "upsert") in events and ("mirror_ok", "rag_engine", "delete:superseded") in events, events
    assert ("mirror_failed", "vertex_search", "upsert") in events and ("mirror_failed", "vertex_search", "delete:superseded") in events, events
    assert all(m["error"].startswith("RuntimeError: 503") for m in mlog if m["event"] == "mirror_failed")
    # every confirmation is a doc.mirror audit event (the store, its region, the op); a failure is not one
    assert [(a, actor["tenant_id"], actor["email"], t["id"], m["store"], m["region"], m["op"]) for a, actor, t, m in audits] == [
        ("doc.mirror", "acme", "system:ingest", "acme_s2", "rag_engine", "us-central1", "upsert"),
        ("doc.mirror", "acme", "system:ingest", "acme_s2", "vertex_search", "global", "upsert"),
        ("doc.mirror", "acme", "system:ingest", "acme_s1", "rag_engine", "us-central1", "delete:superseded"),
        ("doc.mirror", "acme", "system:ingest", "acme_s1", "vertex_search", "global", "delete:superseded")], audits
    assert all(t == {"type": "document", "id": t["id"], "tenant_id": "acme"} and m["result"] for _, _, t, m in audits)
    # and the ledger row says where the version is held: the stores that confirmed, the policy it was judged under
    stamp = mdb.store["sources"]["acme~h.md"]
    assert stamp["mirrored"] == {"rag_engine": "us-central1", "vertex_search": "global"} and stamp["data_region"] == "any" and "mirrored_at" in stamp, stamp
    mlog.clear(); good.calls.clear(); audits.clear()
    mirror.after_undo("acme", "gs://b/acme/h.md", "acme_s2", {"retired_doc_keys": ["acme_s3"]}, {"generation": "10"})
    assert good.calls == [("upsert", "acme", "acme_s2", "gs://b/acme/h.md", "first\n\nsecond",
                           {"doc_type": "policy", "effective_from": "2026-04-01", "generation": "10"}), ("delete", "acme", "acme_s3")], good.calls
    assert [m["op"] for _, _, _, m in audits] == ["upsert", "upsert", "delete:superseded", "delete:superseded"] and "sources" in mdb.store and len(mdb.store["sources"]) == 1, "no name, no stamp"
    mlog.clear()
    mirror.retired("zeta", ["zeta_a", "zeta_b"], "withdrawn")
    assert [m["event"] for m in mlog if m.get("store") == "vertex_search" and m["event"] == "mirror_no_store"] == ["mirror_no_store"], "a missing store is said once per tenant"
    assert [c for c in good.calls if c[0] == "delete"][-2:] == [("delete", "zeta", "zeta_a"), ("delete", "zeta", "zeta_b")]
    mlog.clear()
    mirror.upsert("acme", "acme_m", "gs://b/acme/f.png", "", {})
    assert mlog == [{"event": "mirror_skipped", "tenant": "acme", "doc_key": "acme_m", "why": "no text: a media version stays on the kit's own index"}], mlog
    off = managed.Mirror.from_env(mdb, "off")
    assert off.active is False and off.stores == [] and off.mode == "off"
    off.after_swap(mdoc, "text", {"retired_doc_keys": ["x"]}); off.after_undo("acme", "u", "k", {}); off.retired("acme", ["k"])
    ok("Mirror: after the swap the new version is upserted with the rows' and the message's metadata and the retired versions deleted; after "
       "the undo the reactivated version's text comes off its rows; a store that raises is one mirror_failed line per call and nothing is "
       "raised; a tenant with no store is mirror_no_store once; a media version is mirror_skipped; off constructs no store and does nothing; "
       "every confirmation is a doc.mirror audit event and the ledger row is stamped with the stores that hold the version")

    # ---- the data-region policy (13 September 2026, evening): the mirror obeys it per document
    policies = {"acme": "any", "globex": "in"}
    plog, paud = [], []
    managed.log = types.SimpleNamespace(info=lambda m: plog.append(json.loads(m)), warning=lambda m: plog.append(json.loads(m)))
    pus, pin = _Store("rag_engine"), _Store("vertex_search", region="asia-south1")      # one outside India, one inside
    pm = managed.Mirror(mdb, [pus, pin], "both", policy_for=lambda t: policies.get(t, "in"),
                        audit=lambda action, actor, target, meta: paud.append((action, actor["tenant_id"], target["id"], meta["store"], meta["region"], meta["op"])))
    gdoc = types.SimpleNamespace(tenant_id="globex", doc_key="globex_g1", gcs_uri="gs://b/globex/g.md", doc_type="policy", effective_from=None)
    pm.after_swap(gdoc, "globex words", {"retired_doc_keys": ["globex_g0"]}, {"generation": "3", "name": "globex/g.md"})
    pm.after_swap(gdoc, "globex words", {"retired_doc_keys": []}, {"generation": "4", "name": "globex/g.md"})
    assert [c for c in pus.calls if c[0] == "upsert"] == [], "a store outside India received an in-tenant's text"
    assert [c for c in pus.calls if c[0] == "delete"] == [("delete", "globex", "globex_g0")], "a delete is never refused: it is the direction the policy wants"
    assert [c[:3] for c in pin.calls if c[0] == "upsert"] == [("upsert", "globex", "globex_g1")] * 2, "a store inside India is permitted under `in`"
    skipped = [m for m in plog if m["event"] == "mirror_policy_skipped"]
    assert len(skipped) == 1 and (skipped[0]["store"], skipped[0]["region"], skipped[0]["tenant"], skipped[0]["data_region"], skipped[0]["op"]) == \
        ("rag_engine", "us-central1", "globex", "in", "upsert"), "a forbidden store is said once per tenant and store, with the policy that forbade it"
    assert paud == [("doc.mirror", "globex", "globex_g1", "vertex_search", "asia-south1", "upsert"),
                    ("doc.mirror", "globex", "globex_g0", "rag_engine", "us-central1", "delete:superseded"),
                    ("doc.mirror", "globex", "globex_g0", "vertex_search", "asia-south1", "delete:superseded"),
                    ("doc.mirror", "globex", "globex_g1", "vertex_search", "asia-south1", "upsert")], paud
    gstamp = mdb.store["sources"]["globex~g.md"]
    assert gstamp["mirrored"] == {"vertex_search": "asia-south1"} and gstamp["data_region"] == "in", gstamp
    assert pm.upsert("acme", "acme_a1", "gs://b/acme/a.md", "acme words", {}) == {"rag_engine": "us-central1", "vertex_search": "asia-south1"}, "any permits every store"
    assert pm.policy("nobody") == "in" and pm.upsert("nobody", "nobody_n1", "gs://b/nobody/n.md", "words", {}) == {"vertex_search": "asia-south1"}, "absent is in: fail closed"
    assert [c for c in pus.calls if c[0] == "upsert"] == [("upsert", "acme", "acme_a1", "gs://b/acme/a.md", "acme words", {})], pus.calls
    assert managed.Mirror(mdb, [pus], "rag_engine").policy("acme") == "in", "a mirror handed no policy reader permits nothing"
    plog.clear()
    broken = managed.Mirror(mdb, [pus], "rag_engine", policy_for=lambda t: 1 / 0, audit=lambda *a, **k: 1 / 0)
    assert broken.upsert("acme", "acme_a2", "gs://b/acme/a2.md", "words", {}) == {} and [m["event"] for m in plog] == ["mirror_policy_unreadable", "mirror_policy_skipped"], plog
    plog.clear()
    noisy = managed.Mirror(mdb, [pus], "rag_engine", policy_for=lambda t: "any", audit=lambda *a, **k: 1 / 0)
    assert noisy.upsert("acme", "acme_a2", "gs://b/acme/a2.md", "words", {}) == {"rag_engine": "us-central1"} and [m["event"] for m in plog] == ["mirror_ok", "mirror_audit_failed"], plog
    ok("the policy: a store the tenant's data_region forbids is skipped once and said so (mirror_policy_skipped, with the policy), a store inside "
       "India is permitted under `in`, `any` permits every store, an absent or unreadable policy is `in`, a delete is never refused, every "
       "copy in or out is a doc.mirror audit event, the ledger row is stamped with the stores that hold the version and the policy; a failed "
       "audit emit is one line, never a failed ingest")

    # RagEngineStore over a stand-in vertexai.rag: one corpus per tenant by name, one file per doc_key, 4.3's chunking
    rag_state = {"corpora": [], "files": {}, "calls": []}

    def _create_corpus(**kw):
        rag_state["calls"].append(("create_corpus", kw))
        c = types.SimpleNamespace(name=f"projects/p/locations/us-central1/ragCorpora/{len(rag_state['corpora']) + 1}", display_name=kw["display_name"])
        rag_state["corpora"].append(c)
        return c

    def _upload_file(corpus_name, path, display_name=None, description=None, transformation_config=None, timeout=600):
        body = open(path, encoding="utf-8").read()
        rag_state["calls"].append(("upload_file", display_name, description, body, transformation_config))
        f = types.SimpleNamespace(name=f"{corpus_name}/ragFiles/{len(rag_state['calls'])}", display_name=display_name, description=description)
        rag_state["files"].setdefault(corpus_name, []).append(f)
        return f

    def _delete_file(name, corpus_name=None):
        rag_state["calls"].append(("delete_file", name))
        rag_state["files"][corpus_name] = [f for f in rag_state["files"].get(corpus_name, []) if f.name != name]
    fake_rag = types.SimpleNamespace(
        RagEmbeddingModelConfig=lambda **kw: ("emb", kw), VertexPredictionEndpoint=lambda **kw: ("ep", kw),
        RagVectorDbConfig=lambda **kw: ("vdb", kw), TransformationConfig=lambda **kw: ("tc", kw), ChunkingConfig=lambda **kw: ("cc", kw),
        list_corpora=lambda: list(rag_state["corpora"]), create_corpus=_create_corpus,
        list_files=lambda corpus_name: list(rag_state["files"].get(corpus_name, [])), delete_file=_delete_file, upload_file=_upload_file)
    rs = managed.RagEngineStore("p", "us-central1", "text-embedding-005", rag=fake_rag)
    try:
        rs.upsert("acme", "acme_s2", "gs://b/acme/h.md", "text", {})
        raise AssertionError("a tenant without a corpus was mirrored")
    except managed.NoStore as e:
        assert "make rag-corpus TENANT=acme" in str(e)
    cname = rs.create("acme")
    assert rs.create("acme") == cname and len([c for c in rag_state["calls"] if c[0] == "create_corpus"]) == 1, "one corpus per tenant, by name"
    kw = rag_state["calls"][0][1]
    assert kw["display_name"] == "documind-acme" and kw["backend_config"] == ("vdb", {"rag_embedding_model_config": ("emb", {"vertex_prediction_endpoint": ("ep", {"publisher_model": "publishers/google/models/text-embedding-005"})})}), kw
    rs.upsert("acme", "acme_s2", "gs://b/acme/h.md", "first\n\nsecond", {"doc_type": "policy"})
    up = [c for c in rag_state["calls"] if c[0] == "upload_file"]
    assert up[-1][1:] == ("acme_s2", "gs://b/acme/h.md", "first\n\nsecond", ("tc", {"chunking_config": ("cc", {"chunk_size": 512, "chunk_overlap": 100})})), up[-1]
    rs.upsert("acme", "acme_s2", "gs://b/acme/h.md", "first\n\nsecond, amended", {})
    assert len(rag_state["files"][cname]) == 1 and [c[0] for c in rag_state["calls"][-2:]] == ["delete_file", "upload_file"], "the same doc_key again replaces its one file"
    assert rs.listing("acme") == {"acme_s2": {"name": rag_state["files"][cname][0].name, "source_uri": "gs://b/acme/h.md"}}
    assert rs.delete("acme", "acme_s2") == 1 and rs.listing("acme") == {} and rs.delete("acme", "acme_s2") == 0
    ok("RagEngineStore: a corpus per tenant found or created once by display name with the kit's embedding model; a version is one RagFile "
       "named by its doc_key, its text uploaded with 4.3's 512 / 100 chunking, replaced on a second upsert, deleted by name; no corpus is NoStore")

    # VertexSearchStore over stand-in Discovery Engine and Storage clients: a Document per doc_key, the schema's fields, INCREMENTAL
    class _Content:
        def __init__(self, uri=None, mime_type=None): self.uri, self.mime_type = uri, mime_type

    class _Document:
        Content = _Content

        def __init__(self, id=None, struct_data=None, content=None, name=None):
            self.id, self.struct_data, self.content, self.name = id, dict(struct_data or {}), content, name or f"docs/{id}"

        @classmethod
        def to_dict(cls, d):
            return {"id": d.id, "struct_data": dict(d.struct_data)}

    class _InlineSource:
        def __init__(self, documents): self.documents = list(documents)

    class _ImportReq:
        InlineSource = _InlineSource
        ReconciliationMode = types.SimpleNamespace(INCREMENTAL="INCREMENTAL", FULL="FULL")

        def __init__(self, parent, inline_source, reconciliation_mode): self.parent, self.inline_source, self.reconciliation_mode = parent, inline_source, reconciliation_mode
    vs_state = {"docs": {}, "imports": [], "objects": {}, "deleted": []}

    class _Docs:
        def import_documents(self, request):
            vs_state["imports"].append(request)
            for d in request.inline_source.documents:
                vs_state["docs"][d.id] = d
            return types.SimpleNamespace(operation=types.SimpleNamespace(name="operations/import-7"))

        def delete_document(self, name):
            key = name.rsplit("/", 1)[-1]
            if key not in vs_state["docs"]:
                raise _NotFound(name)
            del vs_state["docs"][key]

        def list_documents(self, parent):
            return list(vs_state["docs"].values())

    class _DS:
        def get_data_store(self, name):
            if not name.endswith("/dataStores/documind-acme"):
                raise _NotFound(name)
            return types.SimpleNamespace(name=name)

    class _Blob:
        def __init__(self, n): self.n = n

        def upload_from_string(self, data, content_type=None): vs_state["objects"][self.n] = (data, content_type)

        def delete(self):
            if self.n not in vs_state["objects"]:
                raise _NotFound(self.n)
            del vs_state["objects"][self.n]; vs_state["deleted"].append(self.n)
    fake_gcs = types.SimpleNamespace(bucket=lambda b: types.SimpleNamespace(blob=lambda n: _Blob(f"{b}/{n}")))
    vs = managed.VertexSearchStore("p", "global", "p-audit", clients=types.SimpleNamespace(
        de=types.SimpleNamespace(Document=_Document, ImportDocumentsRequest=_ImportReq), docs=_Docs(), ds=_DS(), gcs=fake_gcs))
    try:
        vs.upsert("zeta", "zeta_a", "gs://b/zeta/a.md", "text", {})
        raise AssertionError("a tenant without a data store was mirrored")
    except managed.NoStore as e:
        assert "MANAGED_SEARCH=true" in str(e)
    op = vs.upsert("acme", "acme_s2", "gs://b/acme/h.md", "first\n\nsecond", {"doc_type": "policy", "generation": "9", "name": "acme/h.md", "kind_extra": "dropped", "effective_from": None})
    assert op == "operations/import-7" and vs_state["objects"] == {"p-audit/search/acme/acme_s2.txt": ("first\n\nsecond", "text/plain; charset=utf-8")}
    req = vs_state["imports"][-1]
    assert req.parent == "projects/p/locations/global/collections/default_collection/dataStores/documind-acme/branches/default_branch" and req.reconciliation_mode == "INCREMENTAL"
    d = req.inline_source.documents[0]
    assert d.id == "acme_s2" and d.content.uri == "gs://p-audit/search/acme/acme_s2.txt" and d.content.mime_type == "text/plain"
    assert d.struct_data == {"tenant_id": "acme", "doc_key": "acme_s2", "source_uri": "gs://b/acme/h.md", "kind": "text", "title": "h.md",
                             "doc_type": "policy", "generation": "9", "name": "acme/h.md"}, d.struct_data
    assert vs.listing("acme") == {"acme_s2": {"name": "docs/acme_s2", "source_uri": "gs://b/acme/h.md"}}
    assert vs.delete("acme", "acme_s2") == 1 and vs_state["deleted"] == ["p-audit/search/acme/acme_s2.txt"] and vs.listing("acme") == {}
    assert vs.delete("acme", "acme_s2") == 0, "a document already gone is not an error"
    ok("VertexSearchStore: the version's text as an object in the audit bucket and one inline Document per doc_key - the schema's fields only, "
       "INCREMENTAL - into the tenant's own data store; delete removes the document and the object, twice is fine; no data store is NoStore")

    # status(): each tenant the ledger knows, each store, held against the ledger's current versions
    sdb = _DB()
    for sid, row in (("acme~h.md", {"tenant_id": "acme", "status": "indexed", "doc_key": "acme_s2"}),
                     ("acme~old.md", {"tenant_id": "acme", "status": "retired", "doc_key": "acme_s0"}),
                     ("zeta~a.md", {"tenant_id": "zeta", "status": "indexed", "doc_key": "zeta_a"})):
        sdb.collection("sources").document(sid).set(row)

    class _Listing:
        name = "vertex_search"

        def listing(self, tenant_id):
            if tenant_id == "zeta":
                raise managed.NoStore("no store")
            return {"acme_s2": {}, "acme_x": {}}
    lines = managed.status(sdb, [_Listing()])
    assert [(l["tenant"], l["status"]) for l in lines] == [("acme", "drift"), ("zeta", "no store")], lines
    assert lines[0]["ledger_current"] == 1 and lines[0]["held"] == 2 and lines[0]["missing"] == 0 and lines[0]["orphan_doc_keys"] == ["acme_x"]
    assert managed.status(sdb, [_Listing()], "acme")[0]["tenant"] == "acme" and len(managed.status(sdb, [_Listing()], "acme")) == 1
    ok("status(): per tenant per store, the ledger's current versions against what the store holds - in sync, drift with the missing and orphan keys, or no store")

    # ------------------------------------------------------------------ reconcile: the plan, --retire, --restore, the selftest
    spec = importlib.util.spec_from_file_location("reconcile_lifecycle", os.path.join(INGEST, "reconcile.py"))
    rec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rec)
    ledger = {"acme~kept.md": {"gcs_uri": "gs://b/acme/kept.md", "doc_key": "acme_k1", "generation": "4", "sha256": "k1",
                               "status": "withdrawn", "name": "acme/kept.md", "tenant_id": "acme"},
              "acme~gone.md": {"gcs_uri": "gs://b/acme/gone.md", "doc_key": "acme_g1", "generation": "1", "sha256": "g1",
                               "status": "withdrawn", "name": "acme/gone.md", "tenant_id": "acme"},
              "acme~back.md": {"gcs_uri": "gs://b/acme/back.md", "doc_key": "acme_b1", "generation": "2", "sha256": "b1",
                               "status": "retired", "name": "acme/back.md", "tenant_id": "acme"}}
    objs = [{"name": "acme/kept.md", "generation": "4", "tenant_id": "acme"},
            {"name": "acme/back.md", "generation": "5", "tenant_id": "acme"},
            {"name": "acme/big.pdf", "generation": "2", "tenant_id": "acme"}]
    docs = {"acme_s7": {"status": "queued", "gcs_uri": "gs://b/acme/big.pdf", "generation": "2"}}
    acts = rec.plan(objs, ledger, docs)
    by = {(a["action"], a["name"]): a for a in acts}
    assert ("reingest", "acme/kept.md") not in by, "the defect: a withdrawn source re-ingested by the nightly walk"
    assert ("withdrawn", "acme/kept.md") in by and by[("withdrawn", "acme/kept.md")]["why"] == "withdrawn, object kept", acts
    assert ("reingest", "acme/back.md") in by, "a retired source whose object is back is still re-ingested"
    assert ("retire", "acme/gone.md") not in by and ("withdrawn", "acme/gone.md") in by, "a withdrawn source is not retired again when its object leaves"
    assert ("queued", "acme/big.pdf") in by and ("check_bytes", "acme/big.pdf") not in by, "a queued document is skipped, not hashed"
    assert rec.plan([{"name": "acme/big.pdf", "generation": "3", "tenant_id": "acme"}], {}, docs)[0]["action"] == "check_bytes", \
        "a later generation of a queued name is a new version"
    moved = rec.plan([{"name": "acme/kept.md", "generation": "9", "tenant_id": "acme"}], ledger, {})[0]
    assert moved["action"] == "withdrawn" and "generation 4 -> 9" in moved["why"], moved
    assert rec.decide_bytes("s7", "acme", None, docs) == "queued" and rec.decide_bytes("s8", "acme", None, docs) == "reingest"
    assert rec.drift_of({"retire": 1, "reingest": 1, "withdrawn": 5, "queued": 2}) == 2, "a withdrawn source and a queued document are not drift"
    rsrc = read("deploy/services/ingest/reconcile.py")
    retire_block = rsrc[rsrc.index("if a.retire:"): rsrc.index("if a.restore:")]
    assert '"status": "withdrawn"' in retire_block and "reconcile_withdrawn" in retire_block and '"status": "retired"' not in retire_block, \
        "--retire must write withdrawn, not retired"
    restore_block = rsrc[rsrc.index("if a.restore:"): rsrc.index("if a.backfill:")]
    for needle in ("reconcile_restored", ".rewrite(", '"status": "retired"', "reconcile_restore_refused", "withdrawn"):
        assert needle in restore_block, needle
    assert '"withdrawn": 0, "queued": 0' in rsrc, "the summary counts both beside the drift"
    r = subprocess.run([sys.executable, os.path.join(INGEST, "reconcile.py"), "--selftest"], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "selftest OK" in r.stdout and "withdrawn" in r.stdout, r.stdout + r.stderr
    ok("reconcile: plan() reports a withdrawn source as 'withdrawn, object kept' and never a reingest, no retire when its "
       "object is gone, a retired source still re-ingested; a queued generation skipped, its successor planned; neither "
       "is drift; --retire writes withdrawn, --restore clears it to retired and rewrites; the selftest covers it")

    # ------------------------------------------------------------------ 3.5: the doc_type restrict, and the re-upsert
    class FakeDP:
        class Restriction:
            def __init__(self, namespace, allow_list): self.namespace, self.allow_list = namespace, list(allow_list)

        class SparseEmbedding:
            def __init__(self, values, dimensions): self.values, self.dimensions = list(values), list(dimensions)

        def __init__(self, datapoint_id, feature_vector, restricts, sparse_embedding):
            self.datapoint_id, self.feature_vector, self.restricts = datapoint_id, feature_vector, restricts
            self.sparse_embedding = sparse_embedding

    upserts = []
    from shared.sparse_encoder import sparse_encode

    def unexpected_embed(texts):
        raise AssertionError("Compatible stored document vectors must be reused without embedding")

    ns = lift("deploy/services/ingest/indexer.py",
              ["_restricts", "_sparse", "_datapoint", "to_datapoints", "reupsert", "_repair_snapshots",
               "document_embedding_matches", "valid_vector", "EMBEDDING_TASK_TYPE", "EMBEDDING_DIMENSIONS"],
              IndexDatapoint=FakeDP, math=math, DRY_RUN=False, EMBEDDING_MODEL="text-embedding-005", EMBEDDING_VERSION="1",
              embed_all=unexpected_embed, sparse_encode=sparse_encode,
              upsert=lambda name, pts: upserts.append((name, pts)) if pts else None, firestore=types.SimpleNamespace(Client=object))
    doc = types.SimpleNamespace(tenant_id="acme", doc_type="policy", chunk_id=lambda i: f"acme:s1#{i}")
    pts = ns["to_datapoints"](doc, [{"text": "a", "kind": "text"}, {"text": "b", "kind": "figure"}], [[0.1], [0.2]])
    expected_values, expected_dimensions = sparse_encode("a")
    assert pts[0].sparse_embedding.values == expected_values
    assert pts[0].sparse_embedding.dimensions == expected_dimensions
    r0 = {r.namespace: r.allow_list for r in pts[0].restricts}
    assert r0 == {"tenant_id": ["acme"], "kind": ["text"], "doc_type": ["policy"], "current": ["true"]}, \
        f"a datapoint must carry the doc_type restrict the API's filters name: {r0}"
    assert {r.namespace: r.allow_list for r in pts[1].restricts}["kind"] == ["figure"] and pts[1].datapoint_id == "acme:s1#1"
    db = _DB()
    stored_vector = [0.1, 0.2, 0.3] * 256
    _rows(db, "acme_s1", U, 3, True, embedding=stored_vector, doc_type="policy", kind="text", **embedding_stamp)
    _rows(db, "acme_s2", U, 2, True, embedding=[0.4], doc_type="policy", kind="text")           # another version's rows
    db.collection("chunks").document("acme:s1#9").set({"tenant_id": "acme", "source_uri": U, "doc_key": "acme_s1",
                                                       "current": False, "embedding": [0.9]})   # a retired row
    n = ns["reupsert"]("idx", db, "acme", U, "acme_s1")
    assert n == 3 and len(upserts) == 1 and upserts[0][0] == "idx", (n, upserts)
    sent = upserts[0][1]
    assert sorted(p.datapoint_id for p in sent) == ["acme:s1#0", "acme:s1#1", "acme:s1#2"], "the current rows of the version, no other"
    assert all(p.feature_vector == stored_vector for p in sent), "the vector is the row's own"
    assert all({r.namespace: r.allow_list for r in p.restricts} == r0 for p in sent), "the same four restricts as a fresh upsert"
    assert ns["reupsert"]("idx", db, "acme", "gs://b/acme/none.md", "acme_s1") == 0 and len(upserts) == 1, "nothing to send, no call"
    ok("indexer: to_datapoints() writes tenant_id / kind / doc_type / current on every datapoint; reupsert() rebuilds the "
       "same restricts from the rows' own vectors for the current rows of one version and upserts them once")

    # ------------------------------------------------------------------ the Makefile and the page
    mk = kit_makefile("deploy/Makefile")
    assert re.search(r"^restore: guard-project", mk, re.M), "make restore is missing"
    restore_target = mk[mk.index("\nrestore: guard-project"):][:600]
    assert "--restore" in restore_target and '"$(SOURCE)"' in restore_target and "--apply" in restore_target
    assert re.search(r"^retire: guard-project", mk, re.M) and "--retire" in mk
    phony = mk[mk.index(".PHONY:"): mk.index("# ---------- Tier A")].replace("\\", " ").split()
    assert "restore" in phony and "retire" in phony, ".PHONY must list restore"
    page = read("deploy/INDEXING.md")
    for needle in ("`withdrawn`", "make restore", "`queued`", "reactivate_incomplete", "retired_at", "`tenant_id`", "consumer",
                   "withdrawn, object kept", "ingest_withdrawn", "ingest_queued_batch", "doc_type"):
        assert needle in page, f"INDEXING.md does not name {needle}"
    assert "delete the object, or `make retire" not in page, \
        "the playbook must not present deleting the object and make retire as the same thing"
    ok("Makefile: retire and restore targets, restore in .PHONY; INDEXING.md names the withdrawn state, make restore, the "
       "queued claim and the batch job that consumes it, reactivate_incomplete, retired_at, tenant_id - and keeps "
       "storage absence apart from a withdrawal")

    print(f"\n{len(PASSED)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
