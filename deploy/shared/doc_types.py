"""The doc_type registry (workshop lesson 10.4): which class each object is, said by an operator, never by the uploader.

Every text chunk the worker ingests from the uploads bucket carried doc_type "unknown" (DocumentContract's default,
services/ingest/contracts.py), and the bytes cannot bring a class with them: doc_key is the tenant plus the sha256,
so the same bytes uploaded again are acked as a duplicate. So the class lives beside the ledger, keyed the way the
ledger keys an object - tenants/{tenant}/doc_types/{source_id}, the source_id idempotency.source_id_for mints from
the object name - as {name, doc_type, pin, set_by, set_at, source}. The pin is the doc_key a person reviewed, and
the worker gives a version its class only when its doc_key is the pin (assign). A new version of a registered name -
a re-issue, or an overwrite by any member, since the uploads bucket lets the UI's account write it - ingests as
"unknown" and logs doc_type_pin_miss, until an operator re-pins it after review (make doc-types FOLLOW=<name>).
services/ingest/relabel.py applies the registry to the rows already stored. The undo (the same bytes as a retired
version uploaded again) does not pass this hook: it flips the old rows current with the label they hold, so the relabel
keeps the retired rows' labels by the same rule - the class on the pin's rows, "unknown" on every other version's.

The seed is evals/manifest.json. A text object takes its manifest class; a figure, video or image (the manifest's
media values, never classes) takes its parent's class through the longest same-tenant slug prefix
(annual_report_2026_fig3.png -> annual_report_2026 -> report); whiteboard_arch.png has no parent and stays
unregistered, a `figure` in no desk's scope. The database client is passed in and nothing here imports a cloud
library, so the worker, the operator's commands and the offline tests share one copy.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("documind.doc_types")

CLASSES = ("policy", "statute", "guidance", "report", "transcript", "contract", "invoice")
UNKNOWN = "unknown"
SOURCES = ("manifest", "operator")          # who set an entry: the seed from evals/manifest.json, or a person
MANIFEST = Path(__file__).resolve().parents[1] / "evals" / "manifest.json"


def source_id_for(name: str) -> str:
    """idempotency.source_id_for, repeated so this module needs no cloud client: Firestore ids cannot hold '/'."""
    return name.replace("/", "~")


def entry_ref(db, tenant_id: str, name: str):
    return db.collection("tenants").document(tenant_id).collection("doc_types").document(source_id_for(name))


def media_parent(slug: str, parents: dict[str, str]) -> str | None:
    """The parent of a media object: the longest slug of the same tenant's text objects that is the media slug
    itself or a prefix of it ending at an underscore (inv_2026_0412 for inv_2026_0412.png, payment_of_bonus_act_1965
    for payment_of_bonus_act_1965_p30.png). None when no text object names it."""
    hits = [p for p in parents if slug == p or slug.startswith(p + "_")]
    return max(hits, key=len) if hits else None


def registry_from_manifest(manifest: list[dict] | None = None) -> dict[str, dict]:
    """Object name (tenant/basename, as evals/upload.sh puts it in the bucket) -> {tenant_id, name, doc_type, sha256,
    parent}. Text objects carry their manifest class and sha256; media carry their parent's class and no sha256 - a
    media pin can only come from the lane's ledger, after ingest. An object with no class is left out."""
    if manifest is None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    text: dict[str, dict[str, str]] = {}
    for m in manifest:
        if m.get("doc_type") in CLASSES:
            text.setdefault(m["tenant_id"], {})[m.get("slug") or Path(m["file"]).stem] = m["doc_type"]
    for m in manifest:
        tenant, base = m["tenant_id"], Path(m["file"]).name
        name = f"{tenant}/{base}"
        if m.get("doc_type") in CLASSES:
            out[name] = {"tenant_id": tenant, "name": name, "doc_type": m["doc_type"], "sha256": m.get("sha256"),
                         "parent": None}
            continue
        parents = text.get(tenant, {})
        parent = media_parent(m.get("slug") or Path(m["file"]).stem, parents)
        if parent:
            out[name] = {"tenant_id": tenant, "name": name, "doc_type": parents[parent], "sha256": None,
                         "parent": parent}
    return out


def read_entry(db, tenant_id: str, name: str) -> dict | None:
    snap = entry_ref(db, tenant_id, name).get()
    return (snap.to_dict() or {}) if snap.exists else None


def read_registry(db, tenant_id: str) -> dict[str, dict]:
    """Every entry of the tenant, by object name."""
    out = {}
    for snap in db.collection("tenants").document(tenant_id).collection("doc_types").stream():
        row = snap.to_dict() or {}
        out[row.get("name") or snap.id.replace("~", "/")] = row
    return out


def assign(db, doc, name: str):
    """The worker's hook (services/ingest/main.py, index_document, both lanes): `doc` with its registered class when
    the entry's pin is this version's doc_key, and "unknown" otherwise. A registered name arriving with another
    doc_key is a doc_type_pin_miss line - the version is unreviewed text, and the desks that filter on a class do
    not see it until an operator re-pins it. Never raises: the hook runs before index_document's try, so a failed
    read is one doc_type_lookup_failed line and "unknown" (make doc-types APPLY=1 relabels the version once the pin
    is readable), never a claim left processing. A PDF the push lane hands to the batch lane passes the hook on both,
    so one unreviewed version can log two pin-miss lines: count distinct doc_key values."""
    cls = UNKNOWN
    try:
        entry = read_entry(db, doc.tenant_id, name)
    except Exception as e:  # noqa: BLE001 - a class is never worth a lost document
        entry = None
        log.warning(json.dumps({"event": "doc_type_lookup_failed", "tenant": doc.tenant_id, "name": name,
                                "error": f"{type(e).__name__}: {e}"[:200]}))
    if entry and entry.get("doc_type") in CLASSES:
        if entry.get("pin") and entry.get("pin") == doc.doc_key:
            cls = entry["doc_type"]
        else:
            log.warning(json.dumps({"event": "doc_type_pin_miss", "tenant": doc.tenant_id, "name": name,
                                    "doc_key": doc.doc_key, "pin": entry.get("pin"),
                                    "hint": "review it, then make doc-types FOLLOW=<name> APPLY=1"}))
    return doc.model_copy(update={"doc_type": cls})


def set_class(db, tenant_id: str, name: str, doc_type: str, pin: str | None, set_by: str, source: str) -> dict:
    """The operator's write, and the only one: {name, doc_type, pin, set_by, set_at, source}. No service calls it."""
    if doc_type not in CLASSES:
        raise ValueError(f"doc_type {doc_type!r}: one of {', '.join(CLASSES)}")
    if source not in SOURCES:
        raise ValueError(f"source {source!r}: one of {', '.join(SOURCES)}")
    if not name.startswith(tenant_id + "/"):
        raise ValueError(f"{name!r} is not under the tenant prefix {tenant_id}/")
    if pin is not None and not pin.startswith(tenant_id + "_"):
        raise ValueError(f"pin {pin!r} is not a doc_key of {tenant_id}")
    row = {"name": name, "doc_type": doc_type, "pin": pin, "set_by": set_by,
           "set_at": datetime.now(timezone.utc), "source": source}
    entry_ref(db, tenant_id, name).set(row)
    return row


def seed_plan(tenant_id: str, seed: dict[str, dict], ledger: dict[str, dict], registry: dict[str, dict]) -> list[dict]:
    """What SEED=manifest writes for one tenant, as data. seed: registry_from_manifest(); ledger: object name ->
    its sources/ row; registry: read_registry(). One action per manifest object of the tenant:

    pin         a text object takes the doc_key the ledger holds when it is the manifest's own (tenant_sha256), or
                the manifest's doc_key on a lane that has not ingested it - so the worker classes it at ingest; a
                media object takes the ledger's doc_key the first time it is seeded
    mismatch    the ledger's current version is not the manifest's bytes, or a seeded media object's pin: printed,
                never pinned - a new version is a person's to review (FOLLOW=), and a re-run of the seed must not
                accept a figure someone replaced
    not_ingested  a media object the ledger does not hold yet: nothing to pin until it is ingested
    unchanged   the entry already says this class and this pin
    operator    an entry a person set (FOLLOW=): the seed leaves it alone"""
    out = []
    for name, m in sorted(seed.items()):
        if m["tenant_id"] != tenant_id:
            continue
        row = ledger.get(name) or {}
        held = row.get("doc_key") if row.get("status", "indexed") == "indexed" else None
        have = registry.get(name)
        act = {"name": name, "doc_type": m["doc_type"], "parent": m.get("parent"), "ledger": held}
        if have and have.get("source") == "operator":
            out.append({**act, "action": "operator", "pin": have.get("pin")})
            continue
        if m.get("sha256"):
            want = f"{tenant_id}_{m['sha256']}"
            if held and held != want:
                out.append({**act, "action": "mismatch", "pin": None, "manifest": want})
                continue
            pin = want
        elif held:
            if have and have.get("pin") and have["pin"] != held:
                out.append({**act, "action": "mismatch", "pin": None, "registered": have["pin"]})
                continue
            pin = held
        else:
            out.append({**act, "action": "not_ingested", "pin": None})
            continue
        if have and have.get("doc_type") == m["doc_type"] and have.get("pin") == pin:
            out.append({**act, "action": "unchanged", "pin": pin})
        else:
            out.append({**act, "action": "pin", "pin": pin})
    return out
