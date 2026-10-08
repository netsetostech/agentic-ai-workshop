#!/usr/bin/env python3
"""The DocuMind Desk's operator commands as direct Python calls (workshop lessons 5.6 and 10.4): what mk/agents.mk runs.

    python commands/desk_ops.py doc-types --tenant acme [--seed manifest] [--follow hr_policy_2026.md] [--dry-run]   make doc-types
                                          [--export doc_types.json]                              make doc-types EXPORT=
    python commands/desk_ops.py desk --tenant acme [--gate rules|on|off] [--max-parts 1|2]                           make desk
                                     [--route off|shadow|on|single] [--single handbook|statute] [--off statute|none]
                                     [--notes evals/desk/clause_notes.acme.json|none]                     make desk NOTES=
                                     [--gchat on|off [--confirm-residency]]
    python commands/desk_ops.py roles --tenant acme [--email E [--set R,R | --revoke R,R|all]]                        make roles
    python commands/desk_ops.py queues --tenant acme [--file evals/desk/queues.acme.json] [--dry-run]               make desk-queues
    python commands/desk_ops.py cases --tenant acme [--json]                                                           make cases
    python commands/desk_ops.py route-index --tenant acme [--dry-run]                                                  make route-index

doc-types is the registry of shared/doc_types.py: tenants/{tenant}/doc_types/{source_id}, the class an operator
gives each object and the doc_key (the pin) it was reviewed at. --seed manifest writes it from evals/manifest.json -
a text object's class and its manifest doc_key, cross-checked against the ledger on a lane that has ingested it (a
mismatch is printed, never pinned); a media object its parent's class and the ledger's doc_key, once it is ingested
(a later seed prints a replaced figure as a mismatch, the same way).
--follow re-pins one object to the version the ledger holds now, after a person has read it - a new version of a
registered name ingests as "unknown" until then - and registers a seed mismatch the same way, with its manifest
class. Every run ends with the view - one line per object: the name, the label its current rows carry, the class,
the pin and the chunk count. services/ingest/relabel.py then applies the registry to the stored rows (make doc-types
APPLY=1). --export PATH writes the registry as {tenant: {object name: class}} into PATH, the tenant's key replaced and
any other tenant's kept, so one run per tenant builds the file evals/route_eval.py --registry reads.

desk is the tenant's Desk switches in tenant_settings/{tenant}: --gate rules|on|off sets desk_gate, the hard gate that
rag-api's door (services/rag-api/desk_door.py) applies on /v1/query, /v1/stream and /v1/passages, and the chat service's
door (services/chat/desk.py) on /v1/chat - a merge write, the document's other fields (the data_region, the pins) kept,
as shared/tenancy.set_policy writes. Both services read the document once a minute per tenant, so a switch takes effect
within 60 s. Without --gate it prints the switch. rules - the rules and the masking - is what a tenant has until an
operator writes anything else (shared/desk_rules.gate_state); on adds the model check behind them
(shared/desk_recall.py: one flash-lite call for each question to the company that the rules let through, at the chat
door and on rag-api's /v1/query and /v1/stream for a body with no brain label or "ui", eval scripts included; while any
company is on, the chat door also looks up every company's caller, and the print says so beside desk_gate on); off turns
both off, and nothing but an explicit off does. The values are read exactly as this command writes them. None of the
three needs a case queue: the doors' fixed replies name the committees and the contacts the law names, and a kind of
case the company has not set up is offered as "contact the People team". --max-parts 1|2 sets desk_max_parts, how many
desks the routed Desk (workshop lesson 10.4) may run for one question, one after the other; unset, it is 1, and a second
desk is offered as a button instead.
--route sets desk_route, the routed Desk's mode: off; shadow (each /v1/chat turn is also decided by the router, and only
a desk_shadow row is written); on (POST /v1/desk answers people, and the Desk page shows Ask the Desk); single (the
same, with one answer desk and no classifier: desk_single, set with --single). on and single are refused while the
tenant's POSH queue is incomplete (queues, below), or while a unit has no Internal Committee member holding
ic_member:<unit> (roles, below) - the routed Desk answers a POSH disclosure with the card, which must name the Internal
Committee and the Local Committee and reach a member who can read it - and single while no desk_single names an answer
desk. shadow is refused while desk_gate is off (and the chat service does not shadow a tenant whose gate is off): only
while it is not off does the door answer every sensitive turn itself, so no shadow row sits beside a chat row that names
the person. --off lists the answer desks the company has switched off (desk_off: "statute", "handbook,statute", or none
to clear it); the routed Desk answers those as not covered, with no search. --notes writes clause_notes from a JSON
file, replaced whole (none clears it): {clause code: {"note": text, "basis": {instrument, section, file, lines}}}, the
company's note that the handbook desk shows beside an answer citing that clause (evals/desk/clause_notes.acme.json:
LV-01 and LV-07 against the OSH Code). The file is checked first and refused whole when anything is wrong. The chat
service reads all of these within 60 s. While desk_route is on or single, the POSH queue must stay complete and
readable: a queues file or a role change (roles, queues, below) that would break it is refused.
--gchat on|off sets desk_gchat, the Google Chat door (workshop lesson 10.4): while it is on, the chat service serves
the people of this tenant whom the Google Chat bridge names (services/chat/delegation.py). on is refused while
desk_gate is off, and unless desk_route is on or single, because the door asks the routed Desk; and for a tenant whose
data_region is "in" it also needs --confirm-residency, because the Desk's answers and their quotes then sit in the
company's Google Chat, under its Workspace settings. off is never refused. desk_gchat is printed when it is given or on.

roles is a person's roles in the tenant (shared/roles.py): tenants/{tenant}/roles/{email}. --set writes exactly the
roles given (employee, leaver, people_ops, payroll, grc_member, privacy, desk_eval, ic_member:<unit>); --revoke takes
some away, or all of them (the person is an employee again). The person must be on the tenant's roster first (make
roster). Each grant and each revoke is an audit event (role.grant, role.revoke). Without --email it lists the role
documents; with --email alone it prints that person's roles. While desk_route is on or single, a --set or --revoke
that would leave a POSH unit with no Internal Committee member holding its ic_member role is refused, and nothing is
written: give another member the role first.

queues is the tenant's case queues, tenant_settings/{tenant}.case_queues (shared/cases.py): the POSH units, each
with its Internal Committee and its district's Local Committee, the Grievance Redressal Committee, the privacy
contact, payroll, the People team and the clause-prefix map, from a JSON file (evals/desk/queues.acme.json is the
synthetic tenant's). The file is checked first and refused whole when anything is wrong; keys that start with "_"
are notes and are not written. While desk_route is on or single, a file that would leave the POSH queue incomplete,
or a unit with no member holding its ic_member role, is refused too. The case_queues field is replaced whole, the
document's other fields kept.
Without --file it prints the stored section and what it lacks. Either way it lists the people and queues no one here
could read a case for (not_readers): give them their roles with make roles.

cases is the tenant's open cases for the operator, soonest due first: the id, the type ("sensitive" for posh,
grievance and privacy_request), the queue, the status, due_at and the state (open, due within 24 hours and
unacknowledged, or breached). No person, no summary.

route-index is the routed Desk's exemplar index (workshop lesson 10.4): tenants/{tenant}/desk_exemplars/{row id},
{route, vector, row_id, group, case_type, index_version, embedding_model}, which services/chat/desk_router.py reads
once every 5 minutes per instance for its k=7 vote. The rows are evals/routes.jsonl's dev rows, never a test row,
leaving out a single-mode tenant's (labelled for its one desk) and keeping only the routes this tenant is covered
for by its doc_type registry (doc-types, above). Each question is embedded with text-embedding-005 on us-central1
(RETRIEVAL_QUERY, 768 dimensions), about 200 short questions; the new entries are written first and the
stale ones deleted after, so the index is never empty. --dry-run prints what would be written and embeds nothing.

The project is --project, else PROJECT, else GOOGLE_CLOUD_PROJECT. The person recorded as set_by is --by, else
DOCUMIND_OPERATOR, else gcloud's account. A Desk subcommand lives here and not in commands/lane.py, whose subcommand
set commands/tests/test_lane.py pins.
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # the kit: deploy/ in the learner repo
INGEST = ROOT / "services" / "ingest"


def _prepare(project: str) -> None:
    """The environment the kit's modules read, and the import paths the image lays out (commands/lane.py's rule)."""
    os.environ["GOOGLE_CLOUD_PROJECT"] = project
    os.environ.setdefault("PROJECT", project)
    os.environ.setdefault("AUDIT_BUCKET", f"{project}-audit")       # terraform/storage.tf's audit bucket: role events
    for p in (str(ROOT), str(INGEST)):
        if p not in sys.path:
            sys.path.insert(0, p)


def _operator() -> str:
    """Who is writing the registry: DOCUMIND_OPERATOR, else the gcloud account, else the login name."""
    if os.environ.get("DOCUMIND_OPERATOR"):
        return os.environ["DOCUMIND_OPERATOR"]
    try:
        r = subprocess.run(["gcloud", "config", "get-value", "account"], capture_output=True, text=True, check=True)
        if r.stdout.strip():
            return r.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    return getpass.getuser()


def object_name(tenant: str, name: str) -> str:
    """hr_policy_2026.md, acme/hr_policy_2026.md or gs://bucket/acme/hr_policy_2026.md -> acme/hr_policy_2026.md."""
    if name.startswith("gs://"):
        name = name.split("/", 3)[3] if name.count("/") >= 3 else name
    return name if name.startswith(tenant + "/") else f"{tenant}/{name}"


def _short(pin: str | None) -> str:
    """A doc_key as the view prints it: the tenant and the first twelve hex digits of the sha256."""
    if not pin:
        return "-"
    tenant, _, sha = pin.partition("_")
    return f"{tenant}_{sha[:12]}"


def ledger_of(db, tenant: str) -> dict[str, dict]:
    """sources/ rows of the tenant, by object name - the ledger the worker keeps (idempotency.record_source)."""
    return {(r.get("name") or ""): r for r in ((s.to_dict() or {}) for s in
            db.collection("sources").where("tenant_id", "==", tenant).stream())}


def view(tenant: str, registry: dict[str, dict], ledger: dict[str, dict], actions: list[dict]) -> list[dict]:
    """One row per object the registry or the ledger names: what its current rows carry against what is registered.
    actions are relabel.plan()'s, one per current version."""
    current = {a["name"]: a for a in actions}
    out = []
    for name in sorted(set(registry) | {n for n, r in ledger.items() if r.get("status") == "indexed"} | set(current)):
        entry, a = registry.get(name) or {}, current.get(name)
        if a is None:
            state = "not ingested" if entry else "no current rows"
        elif a["why"] == "pinned":
            state = "pinned" if not a["change"] else f"relabel {len(a['change'])} rows"
        elif a["why"] == "pin_miss":
            state = "pin miss: review, then FOLLOW=" + name.split("/", 1)[1]
        else:
            state = a["why"]
        label = "-" if a is None else " ".join(f"{k}" if len(a["from"]) == 1 else f"{k}:{n}"
                                                for k, n in sorted(a["from"].items()))
        out.append({"name": name, "label": label, "class": entry.get("doc_type") or "-", "pin": entry.get("pin"),
                    "chunks": a["rows"] if a else 0, "state": state, "source": entry.get("source") or "-"})
    return out


# ---------------------------------------------------------------- the subcommands
def cmd_doc_types(a) -> int:
    _prepare(a.project)
    from google.cloud import firestore
    from shared import doc_types
    import relabel
    db = firestore.Client(project=a.project)
    tenant = a.tenant
    registry, ledger = doc_types.read_registry(db, tenant), ledger_of(db, tenant)
    by = a.by or _operator()
    if a.seed:
        if a.seed != "manifest":
            print(f"--seed {a.seed!r}: the one seed is the manifest (evals/manifest.json)")
            return 2
        for act in doc_types.seed_plan(tenant, doc_types.registry_from_manifest(), ledger, registry):
            line = {"seed": act["name"], "class": act["doc_type"], "action": act["action"], "pin": _short(act["pin"])}
            if act.get("parent"):
                line["parent"] = act["parent"]
            if act["action"] == "mismatch":
                line.update({"ledger": _short(act["ledger"]),
                             **({"manifest": _short(act["manifest"])} if act.get("manifest")
                                else {"registered": _short(act.get("registered"))}),
                             "hint": "the lane holds other bytes under this name: not pinned; read them, then FOLLOW="
                                     + act["name"].split("/", 1)[1]})
            if act["action"] == "pin" and not a.dry_run:
                doc_types.set_class(db, tenant, act["name"], act["doc_type"], act["pin"], by, "manifest")
            print(json.dumps(line))
        registry = doc_types.read_registry(db, tenant)
    if a.follow:
        name = object_name(tenant, a.follow)
        entry, row = registry.get(name), ledger.get(name) or {}
        if not entry:
            # A seed mismatch registers nothing; once a person has read the lane's version, FOLLOW= registers it with
            # the manifest's class. A name the manifest does not class has no class to follow.
            m = doc_types.registry_from_manifest().get(name)
            if not m:
                print(f"{name} is not registered and evals/manifest.json gives it no class")
                return 2
            entry = {"doc_type": m["doc_type"], "pin": None}
        if row.get("status") != "indexed" or not row.get("doc_key"):
            print(f"{name}: the ledger holds no indexed version to pin (make sources TENANT_ONLY={tenant})")
            return 2
        if entry.get("pin") == row["doc_key"]:
            print(json.dumps({"follow": name, "class": entry["doc_type"], "pin": _short(row["doc_key"]), "action": "unchanged"}))
        else:
            if not a.dry_run:
                doc_types.set_class(db, tenant, name, entry["doc_type"], row["doc_key"], by, "operator")
            print(json.dumps({"follow": name, "class": entry["doc_type"], "from": _short(entry.get("pin")),
                              "pin": _short(row["doc_key"]), "action": "would re-pin" if a.dry_run else "re-pinned"}))
        registry = doc_types.read_registry(db, tenant)
    if a.export:
        path = Path(a.export)
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        data[tenant] = {name: entry["doc_type"] for name, entry in sorted(registry.items())}
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"export": str(path), "tenant": tenant, "objects": len(data[tenant])}))
    rows = view(tenant, registry, ledger, relabel.plan(relabel.read_rows(db, tenant), registry))
    if a.json:
        for r in rows:
            print(json.dumps(r))
        return 0
    print(f"{'object':48} {'label':14} {'class':10} {'pin':18} {'chunks':>6}  state")
    for r in rows:
        print(f"{r['name'][:48]:48} {r['label'][:14]:14} {r['class']:10} {_short(r['pin']):18} {r['chunks']:>6}  {r['state']}")
    return 0


DESK_SWITCHES = {"desk_gate": ("off", "rules", "on")}    # shared/desk_rules.GATE_STATES
# Printed beside desk_gate whenever it reads on - a lane that followed the lessons before the gate had three states
# wrote on, which then meant the rules alone and now adds the model check.
CHECK_NOTE = ("on runs the model check (shared/desk_recall.py): one flash-lite call for each question to this company "
              "that the rules let through, at the chat door and on rag-api's /v1/query and /v1/stream for a body with no "
              "brain label or \"ui\"; while any company is on, the chat door also looks up every company's caller. "
              "make desk TENANT={tenant} DESK_GATE=rules keeps the rules without it")
GCHAT_VALUES = ("off", "on")            # desk_gchat, the Google Chat door: printed only when given or on


def set_switch(db, tenant: str, field: str, value: str, by: str, at=None) -> dict:
    """tenant_settings/{tenant}.<field> = value, merged into the document the services read, with who set it and
    when (at: the server's timestamp unless given). Refuses a value the switch does not have: a typo must never
    read as a default."""
    value = (value or "").strip().lower()
    if value not in DESK_SWITCHES[field]:
        raise ValueError(f"{field}={value!r}: one of {'|'.join(DESK_SWITCHES[field])}")
    if at is None:
        from google.cloud import firestore
        at = firestore.SERVER_TIMESTAMP
    update = {field: value, f"{field}_set_by": by, f"{field}_set_at": at}
    db.collection("tenant_settings").document(tenant).set(update, merge=True)
    return update


def switches(db, tenant: str) -> dict:
    """The tenant's Desk switches as the services read them: desk_gate is rules unless it says off or on."""
    from shared import desk_rules
    snap = db.collection("tenant_settings").document(tenant).get()
    doc = (snap.to_dict() or {}) if snap.exists else {}
    return {"desk_gate": desk_rules.gate_state(doc)}


def stored_queues(db, tenant: str) -> dict:
    """tenant_settings/{tenant}.case_queues, or {} when the tenant has none."""
    snap = db.collection("tenant_settings").document(tenant).get()
    doc = (snap.to_dict() or {}) if snap.exists else {}
    return doc.get("case_queues") if isinstance(doc.get("case_queues"), dict) else {}


def posh_refusal(db, tenant: str, cfg: dict) -> list[str]:
    """What a POSH queue lacks for the routed Desk: its sections, then each unit no Internal Committee member can read."""
    from shared import cases
    errs = cases.posh_errors(cfg)
    if errs:
        return errs
    return [f"posh.units.{u}: no Internal Committee member holds ic_member:{u} here - make roles TENANT={tenant} "
            f"EMAIL=<member> ROLES=employee,ic_member:{u}" for u in cases.reader_gaps(db, tenant, cfg)["posh_units"]]


def route_refusal(db, tenant: str) -> list[str]:
    """Why desk_route may not be turned on or single for this tenant: what its POSH queue lacks. Empty: it may.
    desk_gate needs no queue: its replies are fixed."""
    return posh_refusal(db, tenant, stored_queues(db, tenant))


def not_readers(db, tenant: str, cfg: dict) -> list[str]:
    from shared import cases
    gaps = cases.reader_gaps(db, tenant, cfg)
    return [f"ic {e}" for e in gaps["ic"]] + [f"queue {q}: no member holds a role that reads it" for q in gaps["queues"]]


MAX_PARTS = (1, 2)


def set_max_parts(db, tenant: str, n: int, by: str, at=None) -> dict:
    """tenant_settings/{tenant}.desk_max_parts = n (1 or 2), merged, with who set it and when."""
    if n not in MAX_PARTS:
        raise ValueError(f"desk_max_parts={n!r}: one of {MAX_PARTS}")
    if at is None:
        from google.cloud import firestore
        at = firestore.SERVER_TIMESTAMP
    update = {"desk_max_parts": n, "desk_max_parts_set_by": by, "desk_max_parts_set_at": at}
    db.collection("tenant_settings").document(tenant).set(update, merge=True)
    return update


def max_parts(db, tenant: str) -> int:
    """desk_max_parts as the router reads it: 2 only when it says 2."""
    snap = db.collection("tenant_settings").document(tenant).get()
    return 2 if ((snap.to_dict() or {}) if snap.exists else {}).get("desk_max_parts") == 2 else 1


ROUTE_MODES = ("off", "shadow", "on", "single")     # services/chat/desk.py MODES
SINGLE_DESKS = ("handbook", "statute")              # the answer desks (services/chat/desk_routes.ANSWER_DESKS)


def _settings(db, tenant: str) -> dict:
    snap = db.collection("tenant_settings").document(tenant).get()
    return (snap.to_dict() or {}) if snap.exists else {}


def set_route(db, tenant: str, mode: str, by: str, single: str | None = None, at=None) -> dict:
    """tenant_settings/{tenant}.desk_route (and desk_single, when given), merged, with who set it and when. single
    needs an answer desk, given here or already stored: without one the service would read the mode as off."""
    mode, single = (mode or "").strip().lower(), (single or "").strip().lower() or None
    if mode not in ROUTE_MODES:
        raise ValueError(f"desk_route={mode!r}: one of {'|'.join(ROUTE_MODES)}")
    if single is not None and single not in SINGLE_DESKS:
        raise ValueError(f"desk_single={single!r}: one of {'|'.join(SINGLE_DESKS)}")
    if mode == "single" and (single or str(_settings(db, tenant).get("desk_single") or "").strip().lower()) \
            not in SINGLE_DESKS:
        raise ValueError("desk_route=single needs desk_single: --single handbook|statute (make desk DESK_SINGLE=)")
    if at is None:
        from google.cloud import firestore
        at = firestore.SERVER_TIMESTAMP
    update = {"desk_route": mode, "desk_route_set_by": by, "desk_route_set_at": at}
    if single is not None:
        update["desk_single"] = single
    db.collection("tenant_settings").document(tenant).set(update, merge=True)
    return update


def set_single(db, tenant: str, single: str, by: str, at=None) -> dict:
    """desk_single alone: the one answer desk single mode uses."""
    single = (single or "").strip().lower()
    if single not in SINGLE_DESKS:
        raise ValueError(f"desk_single={single!r}: one of {'|'.join(SINGLE_DESKS)}")
    if at is None:
        from google.cloud import firestore
        at = firestore.SERVER_TIMESTAMP
    update = {"desk_single": single, "desk_single_set_by": by, "desk_single_set_at": at}
    db.collection("tenant_settings").document(tenant).set(update, merge=True)
    return update


def off_names(desks: str | None) -> list[str]:
    """The answer desks a --off value names: "none" or "" is none; anything that is not an answer desk is refused."""
    names = [d.strip().lower() for d in (desks or "").replace(" ", ",").split(",") if d.strip()]
    names = [] if names == ["none"] else names
    bad = [d for d in names if d not in SINGLE_DESKS]
    if bad:
        raise ValueError(f"desk_off: {bad} are not answer desks: {'|'.join(SINGLE_DESKS)}, or none")
    return sorted(set(names))


def set_off(db, tenant: str, desks: str, by: str, at=None) -> dict:
    """desk_off: the answer desks switched off ("none" or "" clears it), merged, with who set it and when."""
    names = off_names(desks)
    if at is None:
        from google.cloud import firestore
        at = firestore.SERVER_TIMESTAMP
    update = {"desk_off": names, "desk_off_set_by": by, "desk_off_set_at": at}
    db.collection("tenant_settings").document(tenant).set(update, merge=True)
    return update


def routing(db, tenant: str) -> dict:
    """The routed Desk's settings as the chat service reads them (services/chat/desk.py desk_mode, desks_off):
    desk_route off unless it says shadow, on or single, and single only with a valid desk_single."""
    doc = _settings(db, tenant)
    mode = str(doc.get("desk_route") or "off").strip().lower()
    single = str(doc.get("desk_single") or "").strip().lower()
    if mode not in ROUTE_MODES or (mode == "single" and single not in SINGLE_DESKS):
        mode = "off"
    off = doc.get("desk_off")
    off = off.split(",") if isinstance(off, str) else off if isinstance(off, (list, tuple)) else []
    return {"desk_route": mode, "desk_single": single if single in SINGLE_DESKS else None,
            "desk_off": sorted({str(d).strip().lower() for d in off} & set(SINGLE_DESKS))}


def posh_needed(db, tenant: str) -> str | None:
    """Why the tenant's POSH queue must stay complete and readable now, or None: desk_route on or single, which
    answers a POSH disclosure with the card and its members. The gate's own reply is fixed, and needs no queue."""
    mode = routing(db, tenant)["desk_route"]
    return f"desk_route is {mode}" if mode in ("on", "single") else None


def units_left_unread(db, tenant: str, email: str, after) -> list[str]:
    """The POSH units a role change would leave with no Internal Committee member holding ic_member:<unit>: this
    person holds it now, would not after, and no other member of that unit's committee holds it."""
    from shared import roles
    cfg = stored_queues(db, tenant)
    email, after = (email or "").strip().lower(), set(after)
    now = set(roles.roles_for(db, tenant, email))
    out = []
    for unit, u in sorted((((cfg.get("posh") or {}).get("units")) or {}).items()):
        role = f"ic_member:{unit}"
        members = {str((m or {}).get("email") or "").strip().lower() for m in (u or {}).get("ic") or []}
        if (email in members and role in now and role not in after
                and not any(role in roles.roles_for(db, tenant, m) for m in members - {email})):
            out.append(unit)
    return out


NOTE_MAX = 800                                      # services/chat/desk_graph.NOTE_MAX
CLAUSE_CODE = re.compile(r"^[A-Z][A-Z0-9]{0,7}(?:-[A-Z0-9]{1,6}){1,2}$")   # services/chat/desk_graph.CLAUSE_CODE
NOTE_BASIS = ("instrument", "section", "file", "lines")


def note_errors(cfg) -> list[str]:
    """What a clause-notes file gets wrong: {clause code: {"note": text, "basis": {instrument, section, file, lines}}}."""
    if not isinstance(cfg, dict):
        return ["clause notes: a JSON object, clause code -> {note, basis}"]
    errs = []
    for code, e in sorted(cfg.items()):
        if not CLAUSE_CODE.match(str(code)):
            errs.append(f"{code}: not a handbook clause code (NP-03, LV-07)")
        elif not isinstance(e, dict) or set(e) - {"note", "basis"}:
            errs.append(f"{code}: an object with note and basis only")
        else:
            note, basis = e.get("note"), e.get("basis")
            if not isinstance(note, str) or not note.strip() or len(note) > NOTE_MAX:
                errs.append(f"{code}.note: text of 1 to {NOTE_MAX} characters")
            if basis is not None and not (isinstance(basis, dict) and set(basis) <= set(NOTE_BASIS)
                                          and all(isinstance(v, str) and v.strip() for v in basis.values())):
                errs.append(f"{code}.basis: text fields among {', '.join(NOTE_BASIS)}")
    return errs


def load_notes(spec: str) -> dict:
    """A --notes value: "none" is {}, else the JSON file without its "_" notes, checked whole (ValueError)."""
    if spec.strip().lower() == "none":
        return {}
    try:
        cfg = _notes_off(json.loads(Path(spec).read_text(encoding="utf-8")))
    except (OSError, ValueError) as e:
        raise ValueError(f"{spec}: {e}")
    errs = note_errors(cfg)
    if errs:
        raise ValueError(json.dumps({"file": spec, "refused": errs}))
    return cfg


def write_notes(db, tenant: str, notes: dict, by: str, at=None) -> dict:
    """tenant_settings/{tenant}.clause_notes = notes, replaced whole; the document's other fields kept."""
    if at is None:
        from google.cloud import firestore
        at = firestore.SERVER_TIMESTAMP
    update = {"clause_notes": notes, "clause_notes_set_by": by, "clause_notes_set_at": at}
    db.collection("tenant_settings").document(tenant).set(update, merge=list(update))
    return update


def gchat(db, tenant: str) -> str:
    """desk_gchat as the chat service reads it (services/chat/delegation.py): on only when the field says so."""
    v = _settings(db, tenant).get("desk_gchat")
    return "on" if v is True or str(v).strip().lower() == "on" else "off"


def gchat_refusal(db, tenant: str, confirm_residency: bool, gate: str | None = None,
                  route: str | None = None) -> str | None:
    """Why desk_gchat=on is refused, or None. gate and route: the values this same command is about to write."""
    from shared import tenancy
    if (gate or switches(db, tenant)["desk_gate"]) == "off":
        return f"desk_gchat stays off: the hard gate is off - make desk TENANT={tenant} DESK_GATE=rules (or on) first"
    if (route or routing(db, tenant)["desk_route"]) not in ("on", "single"):
        return (f"desk_gchat stays off: the routed Desk is not on - make desk TENANT={tenant} DESK_ROUTE=on "
                f"(or single) first")
    if tenancy.policy_of(_settings(db, tenant)) == "in" and not confirm_residency:
        return (f"desk_gchat stays off: {tenant}'s data_region is in, and the Google Chat door puts the Desk's answers "
                f"and their quotes in the company's Google Chat, under its Workspace settings - add "
                f"CONFIRM_RESIDENCY=1 once the company has agreed to that")
    return None


def set_gchat(db, tenant: str, value: str, by: str, at=None) -> dict:
    """tenant_settings/{tenant}.desk_gchat, merged, with who set it and when."""
    value = (value or "").strip().lower()
    if value not in GCHAT_VALUES:
        raise ValueError(f"desk_gchat={value!r}: one of {'|'.join(GCHAT_VALUES)}")
    if at is None:
        from google.cloud import firestore
        at = firestore.SERVER_TIMESTAMP
    update = {"desk_gchat": value, "desk_gchat_set_by": by, "desk_gchat_set_at": at}
    db.collection("tenant_settings").document(tenant).set(update, merge=True)
    return update


def cmd_desk(a) -> int:
    _prepare(a.project)
    from google.cloud import firestore
    db = firestore.Client(project=a.project)
    if a.route in ("on", "single"):
        missing = route_refusal(db, a.tenant)
        if missing:
            print(json.dumps({"tenant": a.tenant, "refused": "desk_route stays as it is: the POSH queue is incomplete",
                              "missing": missing, "fix": f"make desk-queues TENANT={a.tenant} FILE=<file>"}))
            return 2
    if a.route == "shadow" and (a.gate or switches(db, a.tenant)["desk_gate"]) == "off":
        print(json.dumps({"tenant": a.tenant, "refused": "desk_route stays as it is: shadow runs only while desk_gate "
                                                         "is not off, so the door answers every sensitive turn itself",
                          "fix": f"make desk TENANT={a.tenant} DESK_GATE=rules DESK_ROUTE=shadow"}))
        return 2
    try:                                # every value checked before anything is written
        if a.route == "single" and (a.single or routing(db, a.tenant)["desk_single"]) not in SINGLE_DESKS:
            raise ValueError("desk_route=single needs desk_single: --single handbook|statute (make desk DESK_SINGLE=)")
        if a.off is not None:
            off_names(a.off)
        notes = load_notes(a.notes) if a.notes is not None else None
    except ValueError as e:
        print(e)
        return 2
    if a.gchat == "on":
        refused = gchat_refusal(db, a.tenant, a.confirm_residency, gate=a.gate, route=a.route)
        if refused:
            print(json.dumps({"tenant": a.tenant, "refused": refused}))
            return 2
    if a.gate:
        try:
            set_switch(db, a.tenant, "desk_gate", a.gate, a.by or _operator())
        except ValueError as e:
            print(e)
            return 2
    if a.max_parts:                     # after the gate, so a refused --gate changes nothing
        set_max_parts(db, a.tenant, a.max_parts, a.by or _operator())
    if a.route:
        set_route(db, a.tenant, a.route, a.by or _operator(), single=a.single)
    elif a.single:
        set_single(db, a.tenant, a.single, a.by or _operator())
    if a.off is not None:
        set_off(db, a.tenant, a.off, a.by or _operator())
    if notes is not None:
        write_notes(db, a.tenant, notes, a.by or _operator())
    if a.gchat:
        set_gchat(db, a.tenant, a.gchat, a.by or _operator())
    door = gchat(db, a.tenant)
    gate = switches(db, a.tenant)
    print(json.dumps({"tenant": a.tenant, **gate, **({"model_check": CHECK_NOTE.format(tenant=a.tenant)}
                                                      if gate["desk_gate"] == "on" else {}),
                      "desk_max_parts": max_parts(db, a.tenant),
                      **routing(db, a.tenant), **({"clause_notes": sorted(notes)} if notes is not None else {}),
                      **({"desk_gchat": door} if a.gchat or door == "on" else {}),
                      **({"note": "rag-api and the chat service read it within 60 s"}
                         if a.gate or a.route or notes is not None or a.gchat else {})}))
    return 0


def _split(text: str | None) -> list[str]:
    return [r.strip() for r in (text or "").replace(" ", ",").split(",") if r.strip()]


def cmd_roles(a) -> int:
    _prepare(a.project)
    from google.cloud import firestore
    from shared import roles
    db = firestore.Client(project=a.project)
    if not a.email:
        if a.set is not None or a.revoke:
            print("--set and --revoke need --email")
            return 2
        for email, held in sorted(roles.list_roles(db, a.tenant).items()):
            print(json.dumps({"tenant": a.tenant, "email": email, "roles": held}))
        return 0
    if a.set is not None or a.revoke:
        why = posh_needed(db, a.tenant)
        if why:
            snap = roles.role_ref(db, a.tenant, a.email).get()
            held = ((snap.to_dict() or {}).get("roles") or []) if snap.exists else [roles.EMPLOYEE]
            if a.set is not None:
                after = _split(a.set)
            elif a.revoke.strip() == "all":
                after = []
            else:
                after = [r for r in held if r not in set(_split(a.revoke))]
            lost = units_left_unread(db, a.tenant, a.email, after or [roles.EMPLOYEE])
            if lost:
                print(json.dumps({"tenant": a.tenant, "email": a.email.lower(),
                                  "refused": f"{why}: this would leave POSH unit(s) {lost} with no Internal Committee "
                                             f"member who can read a case",
                                  "fix": f"give another member of that committee its ic_member role first: make roles "
                                         f"TENANT={a.tenant} EMAIL=<member> ROLES=employee,ic_member:<unit>"}))
                return 2
    by = a.by or _operator()
    try:
        if a.set is not None:
            out = roles.set_roles(db, a.tenant, a.email, _split(a.set), by)
        elif a.revoke:
            out = roles.revoke(db, a.tenant, a.email, "all" if a.revoke.strip() == "all" else _split(a.revoke), by)
        else:
            print(json.dumps({"tenant": a.tenant, "email": a.email.lower(), "roles": roles.roles_for(db, a.tenant, a.email)}))
            return 0
    except (ValueError, PermissionError) as e:
        print(e)
        return 2
    line = {"tenant": a.tenant, **out}
    if not {"employee", "leaver"} & set(out["after"]):
        line["note"] = ("no employee or leaver role: this person reaches no desk, the case desk included - "
                        "add employee unless that is meant")
    if out["revoked"] and posh_needed(db, a.tenant):
        gaps = route_refusal(db, a.tenant)
        if gaps:
            line["warning"] = gaps
    print(json.dumps(line))
    return 0


def _notes_off(obj):
    """The file without its notes: every key that starts with "_", at any depth."""
    if isinstance(obj, dict):
        return {k: _notes_off(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, list):
        return [_notes_off(v) for v in obj]
    return obj


def write_queues(db, tenant: str, cfg: dict, by: str, at=None) -> dict:
    """tenant_settings/{tenant}.case_queues = cfg, replaced whole; the document's other fields kept."""
    if at is None:
        from google.cloud import firestore
        at = firestore.SERVER_TIMESTAMP
    update = {"case_queues": cfg, "case_queues_set_by": by, "case_queues_set_at": at}
    db.collection("tenant_settings").document(tenant).set(update, merge=list(update))
    return update


def cmd_queues(a) -> int:
    _prepare(a.project)
    from shared import cases
    if a.file:
        try:
            cfg = _notes_off(json.loads(Path(a.file).read_text(encoding="utf-8")))
        except (OSError, ValueError) as e:
            print(f"{a.file}: {e}")
            return 2
        errs = cases.queue_errors(cfg)
        if errs:
            print(json.dumps({"tenant": a.tenant, "file": a.file, "refused": errs}))
            return 2
    from google.cloud import firestore
    db = firestore.Client(project=a.project)
    why = posh_needed(db, a.tenant) if a.file else None
    if why:
        errs = posh_refusal(db, a.tenant, cfg)
        if errs:
            print(json.dumps({"tenant": a.tenant, "file": a.file,
                              "refused": [f"{why}, so the POSH queue must stay complete and readable", *errs]}))
            return 2
    if a.file and not a.dry_run:
        write_queues(db, a.tenant, cfg, a.by or _operator())
    shown = cfg if a.file else stored_queues(db, a.tenant)
    print(json.dumps({"tenant": a.tenant, "sections": sorted(k for k in shown if k != "clause_prefixes"),
                      "posh_units": sorted(((shown.get("posh") or {}).get("units") or {})),
                      "posh_missing": cases.posh_errors(shown), "not_readers": not_readers(db, a.tenant, shown),
                      **({"action": "would write" if a.dry_run else "written"} if a.file else {})}))
    return 0


def case_rows(rows: list[dict]) -> list[dict]:
    """make cases' rows: the id, the type, the queue, the status, due_at, the state. A sensitive case's type and queue
    are both "sensitive", as cases.overdue() logs them: a queue such as ic:<unit> would say what the case is about."""
    from shared import cases
    return [{"case_id": r.get("case_id"), "type": "sensitive" if cases.sensitive(r.get("case_type")) else r.get("case_type"),
             "queue": "sensitive" if cases.sensitive(r.get("case_type")) else r.get("queue"), "status": r.get("status"),
             "due_at": cases._iso(r.get("due_at")) or "-", "state": r.get("state")} for r in rows]


def cmd_cases(a) -> int:
    _prepare(a.project)
    from google.cloud import firestore
    from shared import cases
    rows = case_rows(cases.tenant_cases(firestore.Client(project=a.project), a.tenant))
    if a.json:
        for r in rows:
            print(json.dumps(r))
        return 0
    print(f"{'case':32}  {'type':16} {'queue':16} {'status':12} {'due_at':25}  state")
    for r in rows:
        print(f"{r['case_id']:32}  {r['type']:16} {r['queue'][:16]:16} {r['status']:12} {r['due_at'][:25]:25}  {r['state']}")
    print(f"{len(rows)} open case(s): {sum(r['state'] == 'due' for r in rows)} due, "
          f"{sum(r['state'] == 'breached' for r in rows)} breached")
    return 0


# ---------------------------------------------------------------- the routed Desk's exemplar index
ROUTE_SET = ROOT / "evals" / "routes.jsonl"


def _evals():
    """evals/route_eval.py: the route set, its index rows and the router it imports."""
    if str(ROOT / "evals") not in sys.path:
        sys.path.insert(0, str(ROOT / "evals"))
    import route_eval
    return route_eval


def exemplar_rows(rows: list[dict], classes) -> list[dict]:
    """The dev rows a tenant's index holds: routed tenants' rows, on the routes the tenant's classes cover."""
    route_eval = _evals()
    _, desk_routes = route_eval.router()
    return route_eval.index_rows(rows, desk_routes.enabled_routes(classes))


def index_version(rows: list[dict], model: str) -> str:
    """A short hash of what the index was built from: the rows' ids, routes and normalised text, and the model."""
    route_eval = _evals()
    key = json.dumps([model] + sorted([r["id"], r["expected_route"], route_eval.normalise(r["question"])] for r in rows))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def write_index(db, tenant: str, rows: list[dict], vectors: list, version: str, model: str, vector=list) -> dict:
    """Write each row's entry, then delete the entries no row names any more. vector wraps a list as Firestore's
    Vector (google.cloud.firestore_v1.vector), so the field is a vector field."""
    coll = db.collection("tenants").document(tenant).collection("desk_exemplars")
    keep = []
    for r, v in zip(rows, vectors):
        coll.document(r["id"]).set({"route": r["expected_route"], "vector": vector([float(x) for x in v]),
                                    "row_id": r["id"], "group": r["group"], "case_type": r["case_type"],
                                    "index_version": version, "embedding_model": model})
        keep.append(r["id"])
    stale = sorted(s.id for s in coll.stream() if s.id not in set(keep))
    for sid in stale:
        coll.document(sid).delete()
    return {"written": len(keep), "deleted": stale}


def cmd_route_index(a) -> int:
    _prepare(a.project)
    route_eval = _evals()
    desk_router, _ = route_eval.router()
    from google.cloud import firestore
    from shared import doc_types
    db = firestore.Client(project=a.project)
    classes = {e.get("doc_type") for e in doc_types.read_registry(db, a.tenant).values()} - {doc_types.UNKNOWN, None}
    if not classes:
        print(json.dumps({"tenant": a.tenant, "refused": "the doc_type registry is empty, so no desk is covered",
                          "fix": f"make doc-types TENANT={a.tenant} SEED=manifest"}))
        return 2
    rows = exemplar_rows(route_eval.load_rows(str(ROUTE_SET)), classes)
    version = index_version(rows, desk_router.EMBED_MODEL)
    summary = {"tenant": a.tenant, "rows": len(rows), "routes": dict(sorted(Counter(r["expected_route"] for r in rows).items())),
               "index_version": version, "embedding_model": desk_router.EMBED_MODEL}
    if a.dry_run:
        print(json.dumps({**summary, "dry_run": True}))
        return 0
    from google.cloud.firestore_v1.vector import Vector
    vectors = desk_router.GeminiModels.for_project(a.project).embed_many([r["question"] for r in rows])
    print(json.dumps({**summary, **write_index(db, a.tenant, rows, vectors, version, desk_router.EMBED_MODEL, Vector),
                      "note": "the router (services/chat/desk_router.py) reads it within 5 minutes"}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n".join(__doc__.splitlines()[2:]))
    ap.add_argument("--project", default=os.environ.get("PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT") or "")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doc-types", help="the doc_type registry: seed it, re-pin one object, print the view (make doc-types)")
    d.add_argument("--tenant", default=os.environ.get("TENANT") or "acme")
    d.add_argument("--seed", help="manifest: every object of evals/manifest.json the tenant has")
    d.add_argument("--follow", help="an object name: re-pin it to the version the ledger holds now")
    d.add_argument("--by", help="who is setting the class (default: DOCUMIND_OPERATOR, else the gcloud account)")
    d.add_argument("--dry-run", action="store_true", help="print what would be written; write nothing")
    d.add_argument("--json", action="store_true", help="the view as JSON lines")
    d.add_argument("--export", help="a JSON file: the registry as {tenant: {object: class}}, for route_eval.py --registry")
    d.set_defaults(fn=cmd_doc_types)
    k = sub.add_parser("desk", help="the tenant's Desk switches in tenant_settings: --gate rules|on|off (make desk)")
    k.add_argument("--tenant", default=os.environ.get("TENANT") or "acme")
    k.add_argument("--gate", type=lambda s: s.strip().lower(), choices=DESK_SWITCHES["desk_gate"],
                   help="desk_gate: the hard gate on rag-api's question routes and the chat service's /v1/chat - rules "
                        "(the default), on (the rules and the model check) or off, any case")
    k.add_argument("--max-parts", type=int, choices=MAX_PARTS,
                   help="desk_max_parts: how many desks the routed Desk may run for one question (1 or 2)")
    k.add_argument("--route", type=lambda s: s.strip().lower(), choices=ROUTE_MODES,
                   help="desk_route: the routed Desk's mode (off, shadow, on, single)")
    k.add_argument("--single", type=lambda s: s.strip().lower(), choices=SINGLE_DESKS,
                   help="desk_single: the one answer desk of single mode (handbook or statute)")
    k.add_argument("--off", help="desk_off: the answer desks switched off, comma separated, or none")
    k.add_argument("--notes", help="clause_notes: a JSON file of the company's notes on handbook clauses, or none")
    k.add_argument("--gchat", type=lambda s: s.strip().lower(), choices=GCHAT_VALUES,
                   help="desk_gchat: the Google Chat door (on needs desk_gate not off and desk_route on or single)")
    k.add_argument("--confirm-residency", action="store_true",
                   help="with --gchat on, for a tenant whose data_region is in: the answers will sit in its Google Chat")
    k.add_argument("--by", help="who is setting it (default: DOCUMIND_OPERATOR, else the gcloud account)")
    k.set_defaults(fn=cmd_desk)
    r = sub.add_parser("roles", help="a person's roles in the tenant: list, set, revoke (make roles)")
    r.add_argument("--tenant", default=os.environ.get("TENANT") or "acme")
    r.add_argument("--email", help="the person (on the tenant's roster)")
    r.add_argument("--set", help="exactly these roles, comma separated (an empty value: back to employee)")
    r.add_argument("--revoke", help="these roles, comma separated, or all")
    r.add_argument("--by", help="who is setting them (default: DOCUMIND_OPERATOR, else the gcloud account)")
    r.set_defaults(fn=cmd_roles)
    q = sub.add_parser("queues", help="the tenant's case queues from a JSON file, checked first (make desk-queues)")
    q.add_argument("--tenant", default=os.environ.get("TENANT") or "acme")
    q.add_argument("--file", help="the queues file (evals/desk/queues.<tenant>.json); without it, print the stored ones")
    q.add_argument("--dry-run", action="store_true", help="check the file and print; write nothing")
    q.add_argument("--by", help="who is setting them (default: DOCUMIND_OPERATOR, else the gcloud account)")
    q.set_defaults(fn=cmd_queues)
    c = sub.add_parser("cases", help="the tenant's open cases: due and breached first (make cases)")
    c.add_argument("--tenant", default=os.environ.get("TENANT") or "acme")
    c.add_argument("--json", action="store_true", help="one JSON line per case")
    c.set_defaults(fn=cmd_cases)
    x = sub.add_parser("route-index", help="the routed Desk's exemplar index from the dev rows (make route-index)")
    x.add_argument("--tenant", default=os.environ.get("TENANT") or "acme")
    x.add_argument("--dry-run", action="store_true", help="print what would be written; embed and write nothing")
    x.set_defaults(fn=cmd_route_index)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    a = ap.parse_args(argv)
    if not a.project:
        ap.error("--project is required (or PROJECT in the environment)")
    return int(a.fn(a) or 0)


if __name__ == "__main__":
    sys.exit(main())
