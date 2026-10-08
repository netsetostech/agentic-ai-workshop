"""The relabel (workshop lesson 10.4): the doc_type registry applied to the rows already stored, one tenant at a time.

    PYTHONPATH=.:services/ingest python services/ingest/relabel.py --project P --tenant acme           # the plan
    PYTHONPATH=.:services/ingest python services/ingest/relabel.py --project P --tenant acme --apply   # steps 1 to 7
    PYTHONPATH=.:services/ingest python services/ingest/relabel.py --project P --tenant acme --reset [--apply]
    python services/ingest/relabel.py --selftest                                                       # the planner, offline

make doc-types runs it after the registry (commands/desk_ops.py doc-types), the way make backfill-vectors runs
reconcile.py. Uploading the same bytes again cannot relabel anything: doc_key is the tenant plus the sha256, and the
worker acks a repeat as a duplicate. So this works on stored data. For each current version of the tenant, the class
is the registry's when the entry's pin is the version's doc_key (shared/doc_types.py), and then:

  1. its Firestore chunk rows get the class, in batches under Firestore's 500-write limit - the managed backends read
     doc_type from these rows at query time (rag-api retriever.py, _version_row);
  2. its Vector Search datapoints are re-upserted from the rows' own vectors through indexer._repair_snapshots, whose
     restrict carries the row's doc_type. Only current rows are passed - it raises on any other - and the upsert goes
     BEFORE the rows are written, so a failed upsert leaves rows the next run plans again. _repair_snapshots asks for
     an ingestion maintenance window, because a swap can retire a row between the read and the upsert and the upsert
     would put the retired datapoint back; so the rows are read again after it, and any id a swap retired meanwhile
     is removed from the tier and left unwritten;
  3. its Vertex AI Search document gets a structData-only update of doc_type, written here and not through the
     managed mirror: the mirror's upsert writes the text to the audit bucket again, whose retention policy refuses
     deletes, and workshop lesson 7.3 holds that only the worker calls it. For a tenant whose data_region lets the
     store hold its text (acme and zeta), when MANAGED_MIRROR names the store and the store exists;
  4. BigQuery's chunk_source (BQ_CHUNK_TABLE) gets a DML UPDATE per label on tenant, source and version (the chunk_id
     before its '#': the table keeps every version's rows, and each takes its own label). Rows still in the streaming
     buffer are refused by BigQuery and retried on the next run: steps 3 and 4 check every labelled version on every
     run, not only the versions step 1 changes, and a run with a deferred statement says so and exits 3;
  5. a version that is not its entry's pin goes back to "unknown" - a figure or a segment to its media type, what the
     worker writes for a media upload no pin covers. The retired versions of a registered name follow the same rule
     on their Firestore rows (and in BigQuery), the pin's rows taking the class: the undo flips a retired version
     current with the label its rows hold, without passing the worker's hook, so a class left on a version nobody
     pinned would come back with it. They are off the tier, so they never go to _repair_snapshots;
  6. the tenant's answer_cache entries are expired, on every --apply that has a registered version (or --reset): the
     corpus fingerprint hashes doc_keys only (idempotency.corpus_fingerprint), so a relabel does not move it, and a
     cached answer is scoped by its filters. The TTL policy deletes them, as it deletes every entry;
  7. nothing is re-uploaded, and nothing is re-embedded unless a row's embedding is not the declared one -
     _repair_snapshots' own rule.

A version whose step 1 or 2 fails is reported and the run goes on to the next version and to steps 3, 4 and 6; the
run exits 1, and the next plan lists the version again. A failure once the upsert has started (a later group's upsert
included) first puts the tier back to the labels the rows hold, so the datapoints never run ahead of rows a later plan
(--reset, a re-pin) would leave alone.

--apply refuses an empty VECTOR_INDEX_NAME (make doc-types reads it from Terraform's output): rows relabelled without
their datapoints would leave the old label on the restricts where no later plan can see it. --no-index is for a
deployment with no Vector Search tier at all.

--reset plans every row of the tenant, current and retired, back to "unknown" (a media row to its media type) by the
same steps and leaves the registry in place: the state workshop lessons 2.1 and 5.5 teach, for rehearsing them on a
relabelled lane. Without --reset an unregistered source is never touched.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_KIT = Path(__file__).resolve().parents[2]          # deploy/ in the repository; in the image shared/ sits beside this file
if (_KIT / "shared").is_dir() and str(_KIT) not in sys.path:
    sys.path.append(str(_KIT))

from shared.doc_types import CLASSES, UNKNOWN  # noqa: E402

BATCH = 400                      # a Firestore batch holds 500 writes; commit early (idempotency.BATCH)
FIELDS = ["tenant_id", "source_uri", "doc_key", "doc_type", "kind", "current", "staged"]


def _name_of(gcs_uri: str) -> str:
    """gs://bucket/acme/x.md -> acme/x.md (idempotency._name_of, repeated so the planner needs no cloud client)."""
    return gcs_uri.split("/", 3)[3] if gcs_uri.startswith("gs://") and gcs_uri.count("/") >= 3 else gcs_uri


def _doc_key_of(row: dict) -> str:
    """idempotency._doc_key_of over a row dict: a row written before the ledger has no doc_key; its id is <tenant>:<sha256>#<i>."""
    return row.get("doc_key") or row["id"].split("#")[0].replace(":", "_", 1)


def unlabelled(kind: str | None) -> str:
    """What a row carries when no pin covers it: "unknown" for text, the media type for a figure or a segment - the
    worker's own fallback for a media upload (services/ingest/main.py, MEDIA_TYPES)."""
    return UNKNOWN if (kind or "text") == "text" else kind


def plan(rows: list[dict], registry: dict[str, dict], reset: bool = False) -> list[dict]:
    """Pure: one action per current version of the tenant.

    rows: the tenant's chunk rows as dicts with their id ({id, source_uri, doc_key, doc_type, kind, current, staged});
    a row that is not current, or is staged, is never planned. registry: object name -> entry (doc_types.read_registry).
    Each action names the version, why it gets its label (pinned | pin_miss | unregistered | reset), the label each
    row should carry (targets; empty for an unregistered source) and the rows whose label changes (change)."""
    versions: dict[tuple, list[dict]] = {}
    for r in rows:
        if r.get("current") is not True or r.get("staged"):
            continue
        versions.setdefault((r.get("source_uri") or "", _doc_key_of(r)), []).append(r)
    out = []
    for (uri, doc_key), vrows in sorted(versions.items()):
        name = _name_of(uri)
        entry = registry.get(name) or {}
        cls = None
        if reset:
            why = "reset"
        elif entry.get("doc_type") not in CLASSES:
            why = "unregistered"
        elif entry.get("pin") and entry.get("pin") == doc_key:
            why, cls = "pinned", entry["doc_type"]
        else:
            why = "pin_miss"
        targets = {} if why == "unregistered" else {r["id"]: cls or unlabelled(r.get("kind")) for r in vrows}
        change = sorted(r["id"] for r in vrows if r["id"] in targets and r.get("doc_type") != targets[r["id"]])
        out.append({"name": name, "source_uri": uri, "doc_key": doc_key, "why": why, "class": cls,
                    "rows": len(vrows), "from": dict(Counter(r.get("doc_type") or "-" for r in vrows)),
                    "to": "/".join(sorted(set(targets.values()))) or None,
                    "kinds": sorted({r.get("kind") or "text" for r in vrows}),
                    "targets": targets, "change": change})
    return out


def plan_history(rows: list[dict], registry: dict[str, dict], reset: bool = False) -> list[dict]:
    """Pure: one action per retired version of a registered name (every retired version with --reset), Firestore rows
    only - step 5's rule for history: the pin's rows keep the class, every other version's rows are unlabelled, so
    an undo (which flips the rows current as they are) brings back no class a person did not pin. rows: the tenant's
    rows with current False ({id, source_uri, doc_key, doc_type, kind, current, staged}); a staged row is not history."""
    versions: dict[tuple, list[dict]] = {}
    for r in rows:
        if r.get("current") is not False or r.get("staged"):
            continue
        versions.setdefault((r.get("source_uri") or "", _doc_key_of(r)), []).append(r)
    out = []
    for (uri, doc_key), vrows in sorted(versions.items()):
        name = _name_of(uri)
        entry = registry.get(name) or {}
        cls = None
        if reset:
            why = "reset"
        elif entry.get("doc_type") not in CLASSES:
            continue
        elif entry.get("pin") and entry.get("pin") == doc_key:
            why, cls = "pinned", entry["doc_type"]
        else:
            why = "pin_miss"
        targets = {r["id"]: cls or unlabelled(r.get("kind")) for r in vrows}
        change = sorted(r["id"] for r in vrows if r.get("doc_type") != targets[r["id"]])
        out.append({"name": name, "source_uri": uri, "doc_key": doc_key, "why": why, "class": cls, "history": True,
                    "rows": len(vrows), "from": dict(Counter(r.get("doc_type") or "-" for r in vrows)),
                    "to": "/".join(sorted(set(targets.values()))),
                    "kinds": sorted({r.get("kind") or "text" for r in vrows}),
                    "targets": targets, "change": change})
    return out


def summary(actions: list[dict], tenant_id: str, reset: bool, history: list[dict] = ()) -> dict:
    return {"tenant": tenant_id, "reset": reset, "versions": len(actions),
            "to_change": sum(1 for a in actions if a["change"]),
            "rows": sum(len(a["change"]) for a in actions),
            "history_rows": sum(len(h["change"]) for h in history),
            "unregistered": sorted(a["name"] for a in actions if a["why"] == "unregistered"),
            "pin_miss": sorted(a["name"] for a in actions if a["why"] == "pin_miss")}


def plan_lines(actions: list[dict]) -> list[dict]:
    """One line per version whose label changes (a retired one marked history): a second plan after an --apply prints none."""
    return [{"relabel": a["name"], "doc_key": a["doc_key"], "rows": len(a["change"]), "of": a["rows"],
             "from": a["from"], "to": a["to"], "why": a["why"], **({"history": True} if a.get("history") else {})}
            for a in actions if a["change"]]


def read_rows(db, tenant_id: str, current: bool = True) -> list[dict]:
    """The tenant's current chunk rows (current=False: its retired and staged rows), the planner's fields only (no
    vectors): two equality filters, no composite index."""
    q = (db.collection("chunks").where("tenant_id", "==", tenant_id).where("current", "==", current).select(FIELDS))
    return [{"id": s.id, **(s.to_dict() or {})} for s in q.stream()]


class _Relabelled:
    """A chunk snapshot as _repair_snapshots reads it - id, reference, update_time, to_dict() - with the new label on
    the row, so the datapoint goes up with its class before the row itself is written."""

    def __init__(self, snap, doc_type: str):
        self._snap, self._doc_type = snap, doc_type

    @property
    def id(self):
        return self._snap.id

    @property
    def reference(self):
        return self._snap.reference

    @property
    def update_time(self):
        return self._snap.update_time

    def to_dict(self) -> dict:
        return {**(self._snap.to_dict() or {}), "doc_type": self._doc_type}


def _repairable(row: dict) -> bool:
    """What _repair_snapshots accepts without raising (indexer.py): current, not staged, a tenant and a text."""
    return row.get("current") is True and not row.get("staged") and bool(row.get("tenant_id")) and bool(row.get("text"))


def bq_statements(table: str, tenant_id: str, actions: list[dict]) -> list[tuple[str, dict]]:
    """Step 4 as data: one UPDATE per label, (sql, {param: value}) - a version whose rows go back to unlabelled takes
    "unknown" for text and its kind for media, as step 5 does on Firestore. chunk_source keeps a row per chunk of
    every version (indexer.mirror_to_bigquery, chunk_id the Firestore row's id), so each statement names its versions
    - the chunk_id before its '#' - as well as their sources: a re-pin labels the pinned version, not the source's
    history."""
    by_label: dict[str | None, tuple[set, set]] = {}
    for a in actions:
        if a["why"] != "unregistered" and a["source_uri"] and a["targets"]:
            uris, versions = by_label.setdefault(a["class"], (set(), set()))
            uris.add(a["source_uri"])
            versions.update(i.split("#")[0] for i in a["targets"])
    out = []
    for label, (uris, versions) in sorted(by_label.items(), key=lambda kv: kv[0] or ""):
        value = "@label" if label else "IF(IFNULL(kind, 'text') = 'text', 'unknown', kind)"
        sql = (f"UPDATE `{table}` SET doc_type = {value} WHERE tenant_id = @tenant AND source_uri IN UNNEST(@uris) "
               f"AND SPLIT(chunk_id, '#')[SAFE_OFFSET(0)] IN UNNEST(@versions) AND doc_type IS DISTINCT FROM {value}")
        params = {"tenant": tenant_id, "uris": sorted(uris), "versions": sorted(versions)}
        if label:
            params["label"] = label
        out.append((sql, params))
    return out


def run_bq(bq, statements: list[tuple[str, dict]]) -> dict:
    """Step 4 on a client: the rows each statement changed, or the statements BigQuery refused because the rows are
    still in the streaming buffer (deferred: the next run retries them)."""
    from google.cloud import bigquery
    done = {"updated": 0, "deferred": 0, "failed": []}
    for sql, params in statements:
        qp = [bigquery.ScalarQueryParameter("tenant", "STRING", params["tenant"]),
              bigquery.ArrayQueryParameter("uris", "STRING", params["uris"]),
              bigquery.ArrayQueryParameter("versions", "STRING", params["versions"])]
        if "label" in params:
            qp.append(bigquery.ScalarQueryParameter("label", "STRING", params["label"]))
        try:
            job = bq.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=qp))
            job.result()
            done["updated"] += int(job.num_dml_affected_rows or 0)
        except Exception as e:  # noqa: BLE001 - reported per statement; the run goes on to the next step
            if "streaming buffer" in str(e).lower():
                done["deferred"] += 1
            else:
                done["failed"].append(f"{type(e).__name__}: {e}"[:300])
    return done


class SearchLabels:
    """Step 3: a Vertex AI Search document's structData doc_type, and nothing else (update_mask struct_data). The
    store is managed.VertexSearchStore; the document id is the doc_key, as the mirror writes it."""

    def __init__(self, store):
        self.store = store

    def __call__(self, tenant_id: str, doc_key: str, doc_type: str) -> str:
        from google.api_core.exceptions import NotFound
        from managed import NoStore
        c = self.store.clients()
        try:
            self.store.ensure(tenant_id)                  # found once per tenant, as the mirror finds it
        except NoStore:
            return "no store"
        name = f"{self.store.branch(tenant_id)}/documents/{doc_key}"
        try:
            doc = c.docs.get_document(name=name)
        except NotFound:
            return "not held"
        struct = c.de.Document.to_dict(doc).get("struct_data") or {}
        if struct.get("doc_type") == doc_type:
            return "unchanged"
        c.docs.update_document(request=c.de.UpdateDocumentRequest(
            document=c.de.Document(name=name, id=doc_key, struct_data={**struct, "doc_type": doc_type}),
            update_mask={"paths": ["struct_data"]}))
        return "updated"


def _live(row: dict | None) -> bool:
    return bool(row) and row.get("current") is True and not row.get("staged")


def _write_labels(db, snaps, targets: dict) -> int:
    """The rows' doc_type, in batches under Firestore's 500-write limit."""
    batch, pending, n = db.batch(), 0, 0
    for s in snaps:
        batch.update(s.reference, {"doc_type": targets[s.id]})
        pending += 1
        n += 1
        if pending == BATCH:
            batch.commit()
            batch, pending = db.batch(), 0
    if pending:
        batch.commit()
    return n


def _apply_version(db, a: dict, out: dict, index_name: str, repair, remove) -> None:
    """Steps 2, then 1 or 5, for one current version."""
    chunks = db.collection("chunks")
    live = []
    for s in db.get_all([chunks.document(i) for i in a["change"]]):   # read again: a swap since the plan made history
        if not s.exists:
            continue
        if _live(s.to_dict()):
            live.append(s)
        else:
            out["left_current"] += 1
    # 2. the tier first, from the rows' own vectors, current rows only
    if index_name and repair is not None:
        ok = [_Relabelled(s, a["targets"][s.id]) for s in live if _repairable(s.to_dict() or {})]
        out["vector_skipped"] += len(live) - len(ok)
        if ok:
            try:
                # repair upserts in groups and can fail after an earlier group landed (a later upsert, or a
                # re-embed commit after its upsert), so a failure anywhere from here on puts the tier back.
                out["vector_datapoints"] += repair(index_name, db, ok)
                # A swap between the read above and the upsert retired some of these ids and took them off the tier
                # first; the upsert put them back. Read once more: what is history now leaves the tier, unwritten.
                gone = sorted(s.id for s in db.get_all([s.reference for s in ok]) if not _live(s.to_dict()))
                if gone:
                    if remove is not None:
                        remove(index_name, gone)
                    out["vector_removed"] += len(gone)
                    out["left_current"] += len(gone)
                    live = [s for s in live if s.id not in set(gone)]
                # 1 and 5. then the rows: the class, or back to unlabelled
                out["firestore_rows"] += _write_labels(db, live, a["targets"])
            except Exception:
                # Some datapoints may already carry the new label and their rows do not. A plan reads the rows only,
                # so a later run whose target is the rows' label (--reset, a re-pin) would never upsert them again.
                _restore_tier(db, a, [s.reference for s in ok], out, index_name, repair, remove)
                raise
            return
    # 1 and 5. then the rows: the class, or back to unlabelled
    out["firestore_rows"] += _write_labels(db, live, a["targets"])


def _restore_tier(db, a: dict, refs: list, out: dict, index_name: str, repair, remove) -> None:
    """After a failure past the upsert: the tier back to the labels the rows hold now, from the rows themselves, and
    an id a swap retired meanwhile off it. If that fails too, a second line in failed says what is left to do."""
    try:
        snaps = db.get_all(refs)
        back = [s for s in snaps if s.exists and _repairable(s.to_dict() or {})]
        gone = sorted(s.id for s in snaps if not (s.exists and _live(s.to_dict())))
        if back:
            out["vector_restored"] += repair(index_name, db, back)
        if gone:
            if remove is not None:
                remove(index_name, gone)
            out["vector_removed"] += len(gone)
    except Exception as e:  # noqa: BLE001
        out["failed"].append(f"tier {a['doc_key']}: not put back after the failure ({type(e).__name__}: {e}); its "
                             f"datapoints may carry {a['to']!r} - apply this plan again before any other"[:300])


def _apply_history(db, h: dict, out: dict) -> None:
    """Step 5 on a retired version: its Firestore rows only - they are off the tier and out of the managed stores."""
    chunks = db.collection("chunks")
    snaps = [s for s in db.get_all([chunks.document(i) for i in h["change"]])
             if s.exists and (s.to_dict() or {}).get("current") is False and not (s.to_dict() or {}).get("staged")]
    out["history_rows"] += _write_labels(db, snaps, h["targets"])


def apply(db, tenant_id: str, actions: list[dict], index_name: str = "", repair=None, search=None,
          bq=None, bq_table: str = "", now: datetime | None = None, remove=None, history: list[dict] = ()) -> dict:
    """Steps 1 to 7 for one tenant's plan. repair is indexer._repair_snapshots and remove indexer.remove_datapoints
    (None, or no index_name: the deployment has no Vector Search tier and the step is skipped, as the worker skips
    it); search is a SearchLabels or None; bq a BigQuery client or None; history is plan_history()'s. Returns the
    counts each step reports; a version that fails is one line in failed, and the other versions and steps still run."""
    now = now or datetime.now(timezone.utc)
    out = {"tenant": tenant_id, "firestore_rows": 0, "history_rows": 0, "vector_datapoints": 0, "vector_skipped": 0,
           "vector_restored": 0, "vector_removed": 0, "left_current": 0, "search": {}, "bigquery": None,
           "answer_cache_expired": 0, "failed": []}
    for a in actions:
        if a["change"]:
            try:
                _apply_version(db, a, out, index_name, repair, remove)
            except Exception as e:  # noqa: BLE001 - one line; the next plan lists the version again
                out["failed"].append(f"version {a['doc_key']}: {type(e).__name__}: {e}"[:300])
    for h in history:
        if h["change"]:
            try:
                _apply_history(db, h, out)
            except Exception as e:  # noqa: BLE001
                out["failed"].append(f"history {h['doc_key']}: {type(e).__name__}: {e}"[:300])
    # 3. the Vertex AI Search copies of text versions: every labelled current version, every run
    if search is not None:
        counts: Counter = Counter()
        for a in actions:
            if a["why"] == "unregistered" or "text" not in a["kinds"]:
                continue
            try:
                counts[search(tenant_id, a["doc_key"], a["class"] or UNKNOWN)] += 1
            except Exception as e:  # noqa: BLE001 - one line, and the other steps still run
                out["failed"].append(f"vertex_search {a['doc_key']}: {type(e).__name__}: {e}"[:300])
        out["search"] = dict(counts)
    # 4. BigQuery's chunk_source, current and retired versions
    if bq is not None and bq_table:
        out["bigquery"] = run_bq(bq, bq_statements(bq_table, tenant_id, [*actions, *history]))
        out["failed"] += [f"bigquery: {e}" for e in out["bigquery"]["failed"]]
    # 6. the answer cache: expired, not deleted - the TTL policy is the only deleter (semantic_cache.py). On every run
    # with a registered version, not only one that wrote rows: a run that died after its writes leaves none to write.
    if any(a["why"] != "unregistered" for a in [*actions, *history]):
        try:
            batch, pending = db.batch(), 0
            for s in db.collection("answer_cache").where("tenant_id", "==", tenant_id).select(["expire_at"]).stream():
                batch.update(s.reference, {"expire_at": now})
                pending += 1
                out["answer_cache_expired"] += 1
                if pending == BATCH:
                    batch.commit()
                    batch, pending = db.batch(), 0
            if pending:
                batch.commit()
        except Exception as e:  # noqa: BLE001
            out["failed"].append(f"answer_cache: {type(e).__name__}: {e}"[:300])
    return out


def selftest() -> int:
    reg = {"acme/hr_policy_2026.md": {"doc_type": "policy", "pin": "acme_h1"},
           "acme/posh_act_2013.pdf": {"doc_type": "statute", "pin": "acme_p1"},
           "acme/msa_acme_2026.md": {"doc_type": "contract", "pin": "acme_m1"},
           "acme/annual_report_2026_fig3.png": {"doc_type": "report", "pin": "acme_f1"}}
    u = "gs://b/acme/"
    rows = [{"id": "acme:h1#0", "source_uri": u + "hr_policy_2026.md", "doc_type": "unknown", "kind": "text", "current": True},
            {"id": "acme:h1#1", "source_uri": u + "hr_policy_2026.md", "doc_type": "unknown", "kind": "text", "current": True},
            {"id": "acme:h0#0", "source_uri": u + "hr_policy_2026.md", "doc_type": "unknown", "kind": "text", "current": False},
            {"id": "acme:posh_act_2013#s1", "doc_key": "acme_p1", "source_uri": u + "posh_act_2013.pdf",
             "doc_type": "statute", "kind": "text", "current": True},                 # seeded by a notebook: labelled
            {"id": "acme:m2#0", "source_uri": u + "msa_acme_2026.md", "doc_type": "contract", "kind": "text", "current": True},
            {"id": "acme:f1#0", "source_uri": u + "annual_report_2026_fig3.png", "doc_type": "figure", "kind": "figure",
             "current": True},
            {"id": "acme:w1#0", "source_uri": u + "whiteboard_arch.png", "doc_type": "figure", "kind": "figure", "current": True}]
    first = plan(rows, reg)
    by = {a["name"]: a for a in first}
    assert by["acme/hr_policy_2026.md"]["change"] == ["acme:h1#0", "acme:h1#1"], "the retired row is never planned"
    assert by["acme/hr_policy_2026.md"]["to"] == "policy" and by["acme/posh_act_2013.pdf"]["change"] == []
    assert by["acme/msa_acme_2026.md"]["why"] == "pin_miss" and by["acme/msa_acme_2026.md"]["to"] == "unknown"
    assert by["acme/annual_report_2026_fig3.png"]["to"] == "report"
    assert by["acme/whiteboard_arch.png"]["why"] == "unregistered" and not by["acme/whiteboard_arch.png"]["change"]

    def applied(rows, actions):
        t = {i: a["targets"][i] for a in actions for i in a["change"]}
        return [{**r, "doc_type": t.get(r["id"], r["doc_type"])} for r in rows]

    after = applied(rows, first)
    assert not plan_lines(plan(after, reg)), "a second plan lists no change"
    back = plan(after, reg, reset=True)
    assert {a["name"]: a["to"] for a in back}["acme/annual_report_2026_fig3.png"] == "figure", "a figure resets to its media type"
    # the round trip on a lane the worker ingested (every text row unknown, every figure a figure): --reset, then the
    # relabel plans exactly what the first relabel planned
    worker = [{**r, "doc_type": unlabelled(r["kind"])} for r in rows]
    once = plan(worker, reg)
    again = plan(applied(applied(worker, once), plan(applied(worker, once), reg, reset=True)), reg)
    assert [(a["name"], a["change"], a["to"]) for a in again] == [(a["name"], a["change"], a["to"]) for a in once]
    # history: a retired version keeps a class only when it is the pin - the undo flips it back as it is
    retired = [{"id": "acme:h0#0", "source_uri": u + "hr_policy_2026.md", "doc_type": "unknown", "kind": "text", "current": False},
               {"id": "acme:m1#0", "source_uri": u + "msa_acme_2026.md", "doc_type": "contract", "kind": "text", "current": False},
               {"id": "acme:w0#0", "source_uri": u + "whiteboard_arch.png", "doc_type": "figure", "kind": "figure", "current": False}]
    hist = plan_history(retired, {**reg, "acme/msa_acme_2026.md": {"doc_type": "contract", "pin": "acme_m2"}})
    assert [(h["name"], h["change"], h["to"]) for h in hist] == [("acme/hr_policy_2026.md", [], "unknown"),
                                                                 ("acme/msa_acme_2026.md", ["acme:m1#0"], "unknown")], hist
    sql = bq_statements("p.rag_data.chunk_source", "acme", first)
    assert len(sql) == 4 and all("tenant_id = @tenant" in s and "@versions" in s for s, _ in sql), sql
    print(f"selftest OK: {len(first)} current versions, {summary(first, 'acme', False)['rows']} rows to relabel "
          "(a pinned handbook, a pinned figure, a pin miss back to unknown); a seeded statute and an unregistered "
          "whiteboard unchanged; the retired row never planned as current; a second plan lists no change; --reset "
          "then a relabel plans the same; a retired version that is not the pin back to unknown; "
          f"{len(sql)} BigQuery statements, one per label, scoped to their versions")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    ap.add_argument("--tenant", help="one tenant; the registry is tenants/{tenant}/doc_types")
    ap.add_argument("--apply", action="store_true", help="act; the default prints the plan")
    ap.add_argument("--reset", action="store_true",
                    help="every row of the tenant, current and retired, back to unknown (media: its media type); "
                         "the registry is kept")
    ap.add_argument("--no-index", action="store_true",
                    help="--apply on a deployment with no Vector Search tier: VECTOR_INDEX_NAME may be empty")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.project or not a.tenant:
        ap.error("--project and --tenant are required")
    # The cloud clients and the worker's modules are imported here, not at the top: the selftest runs the planner
    # on a machine with neither.
    from google.cloud import firestore
    from shared.doc_types import read_registry
    db = firestore.Client(project=a.project)
    registry = read_registry(db, a.tenant)
    actions = plan(read_rows(db, a.tenant), registry, a.reset)
    history = plan_history(read_rows(db, a.tenant, current=False), registry, a.reset)
    for line in plan_lines([*actions, *history]):
        print(json.dumps(line))
    head = summary(actions, a.tenant, a.reset, history)
    if not a.apply:
        print(json.dumps({"event": "relabel_plan", **head, "note": "nothing is written without --apply (APPLY=1)"}))
        return 0
    os.environ["GOOGLE_CLOUD_PROJECT"] = a.project
    index_name, repair, remove = os.environ.get("VECTOR_INDEX_NAME", ""), None, None
    if not index_name and not a.no_index:
        # Refused, not skipped: rows relabelled without their datapoints would leave the restricts on the old label,
        # and no later plan could see it - the plan reads the rows.
        print("VECTOR_INDEX_NAME is empty: the Vector Search restricts would keep the old label. Set it "
              "(terraform -chdir=terraform output -raw vector_index_name), or pass --no-index on a deployment without the tier")
        return 2
    if index_name:
        from indexer import _repair_snapshots as repair    # VECTOR_DRY_RUN=1 makes it refuse: the tier needs a real write
        from indexer import remove_datapoints as remove
    search = None
    if os.environ.get("MANAGED_MIRROR", "off") in ("vertex_search", "both"):
        from managed import VertexSearchStore
        from shared.tenancy import permits, policy_for
        store = VertexSearchStore(a.project, os.environ.get("SEARCH_LOCATION", "global"))
        if permits(policy_for(a.tenant, db), store.region):
            search = SearchLabels(store)
    bq_table = os.environ.get("BQ_CHUNK_TABLE", "")
    bq = None
    if bq_table:
        from google.cloud import bigquery
        bq = bigquery.Client(project=a.project)
    done = apply(db, a.tenant, actions, index_name=index_name, repair=repair, search=search, bq=bq, bq_table=bq_table,
                 remove=remove, history=history)
    print(json.dumps({"event": "relabel_applied", **head, **done,
                      "vector_index": index_name or "none (--no-index: no tier to relabel)",
                      "vertex_search": "checked" if search else "not this tenant's (MANAGED_MIRROR, or its data_region)",
                      "fingerprint": "unchanged: a relabel moves no doc_key; the answer cache was expired instead"},
                     default=str))
    if done["failed"]:
        return 1
    deferred = (done["bigquery"] or {}).get("deferred", 0)
    if deferred:
        # Not done: the second plan reads Firestore and cannot see chunk_source, so the exit code says it.
        print(f"BigQuery deferred {deferred} statement(s): rows still in the streaming buffer. Run make doc-types "
              f"TENANT={a.tenant} APPLY=1 again once BigQuery has flushed it; the run retries them.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
