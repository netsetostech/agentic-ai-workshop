"""Build lesson 5.6 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Some questions are not DocuMind's to answer. A disclosure of sexual harassment at work, a grievance about how a person
is treated, a request about one's own personal data, wages unpaid after leaving, and "let me talk to a person" go to
the people the law or the company names. The kit finds them by rule (shared/desk_rules.gate()), answers them by code
with one fixed text per class (shared/desk_law.py), at two doors - rag-api's (services/rag-api/desk_door.py) and the
chat service's (services/chat/desk.py) - and lets the person raise a case that only the right people can read
(shared/roles.py, shared/cases.py). The lane walk: the Desk's Terraform, code and accounts; the queues file and the
gate as it stands (rules, with nothing set), the roles; the Desk page; the disclosure through every door; the case
routes as the eval accounts; make smoke-cases; the records, the audit events and the log rows. acme stays on rules:
the model check (desk_gate on) is explained and not switched on, so no later lesson pays for it.

Build-time proof. The widget's rows are the kit's own: the smoke's disclosure and examples and near misses from
commands/tests/test_desk_rules.py, so this file holds no question that fires the gate; every verdict the widget shows
is gate() run here, and each explanation is checked against _fires(). The expected outputs are the kit's own code
run against stand-ins: commands/desk_ops.py against the fake Firestore of commands/tests/test_cases.py; rag-api's
DeskDoor and the chat service's ChatDoor and case routes (fastapi, starlette) behind a local HTTP bridge, with a
stand-in identity and roster; the lane's cells and smoke/smoke_cases.py run against that bridge; the Firestore,
audit-bucket and log cells against the same fake records. Ids, times and tokens are made deterministic, and every
timestamp is shown as a placeholder.
"""
import ast
import contextlib
import hashlib
import html
import importlib.util
import io
import itertools
import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import types
import uuid
import warnings
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "5.6"
title = ("<title>Lesson 5.6 Hand a question to the person the law names - the hard gate, one fixed reply at every "
         "door, and a case only the right people can read | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
LANE_ID = PROJ.lower()                 # the stand-ins run on a real-looking (lower-case) id; every output shows PROJ
ME = "you@example.com"
warnings.filterwarnings("ignore")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:1fr;gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:8px 0 4px;}
.pc-box p{margin:4px 0;}
.gt-words{font-size:14px;color:var(--navy);background:#f1f5f9;border-radius:8px;padding:8px 10px;margin:6px 0;}
.gt-verdict{font-family:var(--mono);font-size:13px;padding:5px 10px;border-radius:8px;display:inline-block;margin:4px 0;}
.gt-verdict.hit{background:#fee2e2;color:#7f1d1d;}.gt-verdict.miss{background:#dcfce7;color:#14532d;}
.gt-src{font-size:12px;color:var(--slate);margin:0 0 6px;}
.gt-why{margin:6px 0 0;padding-left:20px;font-size:13.5px;}
.gt-why li{margin:3px 0;}
.gt-why li.yes{color:#7c2d12;}.gt-why li.no{color:#475569;}
.gt-reply{white-space:pre-wrap;border-left:3px solid var(--teal);padding:4px 10px;margin:4px 0;color:var(--navy);}
.gt-law{margin:4px 0;padding-left:18px;font-size:12.5px;}
.gt-law li{margin:4px 0;}
.gt-ref{font-family:var(--mono);font-size:11.5px;color:#0e7490;}
.gt-line{display:block;font-style:italic;color:#334155;margin-top:2px;}
"""

setup = setup_section()


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, KIT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod                        # pydantic resolves the routes' models by their module
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ verbatim excerpts
DR, DL, DD, CD, FD = ("shared/desk_rules.py", "shared/desk_law.py", "services/rag-api/desk_door.py",
                      "services/chat/desk.py", "services/frontend/desk.py")
RO, CA, TF, OV = "shared/roles.py", "shared/cases.py", "terraform/desk.tf", "services/chat/desk_overdue.py"
EXCERPTS = {
    "gate": ("shared/desk_rules.py - gate() and _fires(): a first person, then each class in order, most protective first",
             block(DR, "def _fires(cls: str, t: str) -> bool:", end="# A member of the committee, or of HR") + "\n...\n"
             + block(DR, "def gate(question: str) -> str | None:", end="# ------------------------------------------------------------"
                     "---- the out_of_scope candidates")),
    "mask": ("shared/desk_rules.py - mask(): checked Aadhaar and card numbers out, each kind named",
             block(DR, 'MASK_TEXT = {"aadhaar": "[Aadhaar]", "card": "[card no.]"}', n=1) + "\n\n\n"
             + block(DR, "def mask(question: str) -> tuple[str, list[str]]:")),
    "law": ("shared/desk_law.py - one fixed reply per class, the same at every door",
            block(DL, "NOWHERE = ", n=1) + "\n\n" + block(DL, "TEMPLATES: dict[str, str] = {", n=8) + "\n    ...\n}\n\n\n"
            + block(DL, "def template(cls: str) -> str:", n=3)),
    "apidoor": ("services/rag-api/desk_door.py - DeskDoor.__call__(): verify, check the roster, read the switch, then the reply",
                block(DD, '        tenant = payload.get("tenant_id")')),
    "chatdoor": ("services/chat/desk.py - ChatDoor.__call__(): the same order in front of POST /v1/chat, before any brain",
                 block(CD, "        cls, (masked, kinds) = await asyncio.to_thread(_read, question)",
                       end="# ---------------------------------------------------------------- the case routes")),
    "installs": ("services/rag-api/main.py and services/chat/agent.py - each door is one install call (rag-api's with the model check)",
                 block("services/rag-api/main.py", "from shared import desk_recall  # noqa: E402", n=5) + "\n...\n"
                 + block("services/chat/agent.py", "import desk  # noqa: E402", n=2)),
    "page": ("services/frontend/desk.py - what the Desk page reads, and its four sections",
             block(FD, "    What it reads   GET /v1/cases/offer:", n=24)),
    "roles": ("shared/roles.py - the desks each role opens, and roles_for(), the one reader",
              block(RO, 'EMPLOYEE, LEAVER = "employee", "leaver"', n=7) + "\n...\n"
              + block(RO, "def roles_for(db, tenant: str, email: str) -> list[str]:")),
    "raiser": ("services/chat/desk.py - who may raise a case, and the route that raises one",
               block(CD, "def _raiser(db, who: dict) -> list[str]:", n=5) + "\n\n\n"
               + block(CD, '@router.post("/v1/cases")', n=17)),
    "offer": ("services/chat/desk.py - case_offer(): what a person may raise, from the settings the doors read",
              block(CD, '@router.get("/v1/cases/offer")', end='@router.get("/v1/cases/{case_id:case_id}")')),
    "routes": ("services/chat/desk.py - the case routes, as the module's docstring lists them",
               block(CD, "    POST /v1/cases                  raise a case:", n=10)),
    "consts": ("shared/cases.py - the queue's numbers",
               block(CA, "DRAFT_TTL = timedelta(minutes=30)", n=7)),
    "new": ("shared/cases.py - _new(): an id that says nothing, and every field a case can carry",
            block(CA, "def _new(tenant: str, requester: str, case_type: str, queue: str, source: str, via: str, now: datetime) -> dict:")),
    "confirm": ("shared/cases.py - confirm(): one transaction, one token, one case; the expiry checked in code",
                block(CA, "def confirm(db, case_id: str, tenant: str, requester: str, token: str, queues: dict, *,")),
    "posh": ("shared/cases.py - open_posh(): no text, a member who can read it, and the token claimed once",
             block(CA, "    held = [roles_mod.roles_for(db, tenant, c) for c in chosen]", n=27)),
    "access": ("shared/cases.py - access(): who reads a case, and who moves it",
               block(CA, "def access(rec: dict, email: str, roles) -> tuple[bool, bool]:")),
    "actor": ("shared/cases.py - the audit event's target and actor: a case reference, never an email",
              block(CA, "def _target(rec: dict) -> dict:", n=8)),
    "tf": ("terraform/desk.tf - the expiry is cleaned up by a TTL, and each query the queue makes has its index",
           block(TF, 'resource "google_firestore_field" "cases_expire_at" {', n=8) + "\n...\n"
           + block(TF, "locals {", n=9)),
    "overdue": ("services/chat/desk_overdue.py - scan(): the hourly job writes ids, queues and dates, nothing else",
                block(OV, "def scan(db, now=None) -> list[dict]:", n=10)),
}
assert EXCERPTS["gate"][1].rstrip().endswith("return None") and "if not (_HUMAN_IMPERATIVE.search(t) or _first_person(t)):" in EXCERPTS["gate"][1]
assert EXCERPTS["mask"][1].rstrip().endswith('return "".join(out), sorted({k for _, _, k in found})')
assert EXCERPTS["law"][1].rstrip().endswith("return TEMPLATES[cls]") and '"posh": (' in EXCERPTS["law"][1]
assert EXCERPTS["apidoor"][1].rstrip().endswith('**usage, "latency_ms": latency, "stages": {}, "cache_hit": "none"})')
assert 'usage = {"tokens_in": 0, "tokens_out": 0, "cached_tokens": 0, "cost_usd": 0.0, "model": "none", "backend": "desk_gate"}' in EXCERPTS["apidoor"][1]
assert EXCERPTS["chatdoor"][1].rstrip().endswith('"case_offer": {"case_type": cls}})')
assert ("install_desk_door(app, settings=lambda t: tenant_settings(t), verify=verify_iap, member=enforce_membership,\n"
        "                  checked=_desk_checked, check=lambda q: desk_recall.check(_gen_client, q))") in EXCERPTS["installs"][1]
assert EXCERPTS["installs"][1].startswith("from shared import desk_recall  # noqa: E402\n_desk_checked = desk_recall.OnTenants(")
assert "desk.install(app, caller=caller, tenant_for=tenant_for, thread_config=thread_config)" in EXCERPTS["installs"][1]
assert EXCERPTS["page"][1].rstrip().endswith("shared/desk_law.QUEUES), so it never shows another queue's case or who raised it.")
assert EXCERPTS["page"][1].startswith("    What it reads   GET /v1/cases/offer:") and "    Tell the Desk   Only for an employee" in EXCERPTS["page"][1]
assert EXCERPTS["offer"][1].startswith('@router.get("/v1/cases/offer")') and EXCERPTS["offer"][1].rstrip().endswith('"types": types, "posh": posh or None}')
assert EXCERPTS["routes"][1].rstrip().endswith("configured, and the POSH card's offices, members and Local Committee contacts")
N_ROUTES = sum(line.lstrip().startswith(("GET ", "POST ")) for line in EXCERPTS["routes"][1].splitlines())
assert N_ROUTES == 7
assert EXCERPTS["roles"][1].rstrip().endswith('return [r for r in ((snap.to_dict() or {}).get("roles") or []) if isinstance(r, str) and valid(r)]')
assert EXCERPTS["raiser"][1].rstrip().endswith("return cases.view(rec, queues)")
assert EXCERPTS["consts"][1].rstrip().endswith("AUDIT_LEASE = timedelta(minutes=2)")
assert '"case_id": secrets.token_hex(16)' in EXCERPTS["new"][1] and '"summary": None' in EXCERPTS["new"][1]
assert EXCERPTS["confirm"][1].startswith("def confirm(") and EXCERPTS["confirm"][1].rstrip().endswith("return _flush(db, case_id)")
assert 'raise CaseError(410, "this draft expired after 30 minutes: raise the case again")' in EXCERPTS["confirm"][1]
assert EXCERPTS["posh"][1].rstrip().endswith("return _flush(db, _tx(db.transaction()))") and "chosen_contacts" in EXCERPTS["posh"][1]
assert EXCERPTS["access"][1].rstrip().endswith("return reads or mine, moves")
assert EXCERPTS["actor"][1].rstrip().endswith('return {"tenant_id": rec["tenant"], "case_ref": "case:" + rec["case_id"]}')
assert "ttl_config {}" in EXCERPTS["tf"][1] and EXCERPTS["tf"][1].rstrip().endswith("}") and "inbox_ic" in EXCERPTS["tf"][1]
assert EXCERPTS["overdue"][1].rstrip().endswith("return rows")
def kit_window(label: str, code: str) -> str:
    """pagebuild.window(); the Desk page's docstring is prose inside a string, so it is coloured as one string."""
    if label not in (EXCERPTS["page"][0], EXCERPTS["routes"][0]):
        return window(label, code)
    empty = window(label, "")
    assert empty.count('<pre tabindex="0"></pre>') == 1
    return empty.replace('<pre tabindex="0"></pre>', '<pre tabindex="0"><span class="st">' + html.escape(code, quote=False) + "</span></pre>")


fill = filler(EXCERPTS, kit_window)


def fd_const(name: str):
    """A constant of the Desk page's own code (services/frontend/desk.py), read without importing Streamlit."""
    for node in ast.parse((KIT / FD).read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(isinstance(x, ast.Name) and x.id == name for x in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


START = fd_const("START")                 # the button under a fixed reply that starts the case it offers

# ------------------------------------------------------------------ the kit's modules and its facts
for p in (str(KIT / "services/chat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from shared import cases, desk_law, desk_recall, desk_rules, identifiers, roles  # noqa: E402

logging.getLogger().addHandler(logging.NullHandler())   # desk_overdue's basicConfig must not print the build's rows
kt = load("kit_desk_rules_105", "commands/tests/test_desk_rules.py")
tc = load("kit_test_cases_105", "commands/tests/test_cases.py")
smoke0 = load("smoke_cases_105", "smoke/smoke_cases.py")
lane = load("lane_105", "commands/lane.py")
door_mod = load("desk_door_105", DD)
chat_desk = load("chat_desk_105", CD)
POSH = smoke0.POSH
assert desk_rules.gate(POSH) == "posh"

assert door_mod.MAX_BODY == chat_desk.MAX_BODY == 64 * 1024 and door_mod.QUERY_MAX == chat_desk.QUESTION_MAX
assert cases.DRAFT_TTL == timedelta(minutes=30) and cases.TOKEN_TTL == timedelta(days=1) and cases.DUE_SOON == timedelta(hours=24)
assert chat_desk.SETTINGS_TTL_S == 60 and chat_desk.CaseId.regex == "[0-9a-f]{32}"
assert desk_recall.ON_TENANTS_TTL_S == 60 and desk_recall.READ_TIMEOUT_S == 2.0   # the page: once a minute, at most 2 s
tf_src = (KIT / TF).read_text(encoding="utf-8")
mk_src = (KIT / "mk/agents.mk").read_text(encoding="utf-8")
EVAL_SAS = re.search(r"^DESK_EVAL_SAS = (.+)$", mk_src, re.M).group(1).split()
assert EVAL_SAS == [f"documind-{k}-sa" for k in re.findall(r"^    (eval\w+)\s+= \"", tf_src, re.M)], EVAL_SAS
N_INDEXES = len(re.findall(r"^    (?:inbox|inbox_ic|mine|overdue|tenant)\s+= \[", tf_src, re.M))
assert N_INDEXES == 5 and 'schedule    = "0 * * * *"' in tf_src and 'time_zone   = "Asia/Kolkata"' in tf_src
assert tf_src.count('resource "google_firestore_field"') == 2 and tf_src.count('resource "google_service_account"') == 2


def planned(rel: str, on: frozenset = frozenset()) -> dict:
    """{type.name: instances} of every resource in deploy/<rel> a plan declares with the switches in `on` true and every
    other at its default, false: `count = var.X ? 1 : 0` or `local.X ? 1 : 0` (X a switch), `for_each` over a local
    map (its keys counted), else one. Any other count or for_each stops the build."""
    src = (KIT / rel).read_text(encoding="utf-8")
    out = {}
    for kind, name, body in re.findall(r'^resource "(\w+)" "(\w+)" \{\n(.*?)^\}', src, re.M | re.S):
        count, each = re.search(r"^  count\s+= (.+)$", body, re.M), re.search(r"^  for_each\s+= (.+)$", body, re.M)
        if count:
            sw = re.fullmatch(r"(?:var|local)\.(\w+) \? 1 : 0", count.group(1))
            assert sw, (rel, name, count.group(1))
            out[f"{kind}.{name}"] = int(sw.group(1) in on)
        elif each:
            m = re.fullmatch(r"local\.(\w+)", each.group(1))
            keys = re.search(r"^  " + m.group(1) + r" = \{\n(.*?)^  \}", src, re.M | re.S) if m else None
            assert keys, (rel, name, each.group(1))
            out[f"{kind}.{name}"] = len(re.findall(r"^    \w+\s+=", keys.group(1), re.M))
        else:
            out[f"{kind}.{name}"] = 1
    return out


# What a default plan adds for the Desk on a lane last planned before it (make plan with no switch on), counted from the
# kit's own .tf files: desk.tf, desk_alerts.tf and the chat service's grant on the audit bucket in storage.tf; and the
# one change, the log sink's filter widened for the Desk's rows. GCHAT_DOOR=true, DESK_ROUTER_ALERTS=true and
# DESK_GATE_ALERTS=true each add their own on top, and DESK_JOB=true (make desk-job, below) the job's.
DESK_TF = planned(TF)
ALERTS_TF = planned("terraform/desk_alerts.tf")
CHAT_AUDIT = planned("terraform/storage.tf")["google_storage_bucket_iam_member.chat_audit"]
assert 'member = "serviceAccount:${google_service_account.chat.email}"' in block("terraform/storage.tf", '"chat_audit"', n=5)
assert 'jsonPayload.event = "desk" OR jsonPayload.event = "passages" OR' in (KIT / "terraform/sink.tf").read_text(encoding="utf-8")
N_TF_ADD = sum(DESK_TF.values())
assert N_TF_ADD == 2 + N_INDEXES + len(EVAL_SAS)        # two TTL fields, the indexes, the eval accounts
N_METRICS = sum(v for k, v in ALERTS_TF.items() if k.startswith("google_logging_metric."))
N_POLICIES = sum(v for k, v in ALERTS_TF.items() if k.startswith("google_monitoring_alert_policy."))
N_PLAN_ADD = N_TF_ADD + N_METRICS + N_POLICIES + CHAT_AUDIT
assert N_METRICS + N_POLICIES == sum(ALERTS_TF.values())
N_GCHAT = (sum(planned("terraform/gchat.tf", frozenset({"gchat_door"})).values()) - sum(planned("terraform/gchat.tf").values())
           + sum(planned(TF, frozenset({"gchat_door"})).values()) - N_TF_ADD)
N_ROUTER_ALERTS = sum(planned("terraform/desk_alerts.tf", frozenset({"desk_router_alerts"})).values()) - sum(ALERTS_TF.values())
N_GATE_ALERTS = sum(planned("terraform/desk_alerts.tf", frozenset({"desk_gate_alerts"})).values()) - sum(ALERTS_TF.values())
assert sum(planned("terraform/gchat.tf").values()) == 0 and N_GCHAT >= 10 and N_ROUTER_ALERTS == 3
assert N_GATE_ALERTS == 1                          # the page says "the policy": the model check's failed share
QUEUES_ACME = tc.queues_file("acme")
SLA = {k: QUEUES_ACME[k]["sla_days"] for k in ("posh", "grc", "privacy", "payroll", "people")}
assert QUEUES_ACME["grc"]["accepts_desk_case"] is False
N_EXISTING = sum(len(v) for v in kt.existing_questions().values())
N_EXAMPLES = sum(len(v) for v in kt.EXAMPLES.values())
N_NEAR = len(kt.NEAR_MISSES)
WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}

# ------------------------------------------------------------------ Level 0: the widget's rows, verdicts and reasons
LANG = {"en": "English", "hi": "Hindi", "hinglish": "Hinglish"}


def ex(cls: str, part: str):
    found = [(lang, q) for lang, q in kt.EXAMPLES[cls] if part in q]
    assert len(found) == 1, (cls, part, found)
    return found[0]


def nm(part: str) -> str:
    found = [q for q in kt.NEAR_MISSES if part in q]
    assert len(found) == 1, (part, found)
    return found[0]


CARD_ROW = "Please refund the hotel booking to my card 4111 1111 1111 1111."
AADHAAR_ROW = "My Aadhaar 2234 5678 9012 is on the travel form."
ROWS = [  # (group, language, the words, where they come from)
    ("fires", "en", POSH, "smoke/smoke_cases.py: the disclosure make smoke-cases sends"),
    ("fires", *ex("posh", "POSH complaint against my manager"), "an example in commands/tests/test_desk_rules.py"),
    ("fires", *ex("posh", "senior chhed"), "an example in commands/tests/test_desk_rules.py"),
    ("fires", *ex("grievance", "shouts at me"), "an example in commands/tests/test_desk_rules.py"),
    ("fires", *ex("grievance", "सबके सामने"), "an example in commands/tests/test_desk_rules.py"),
    ("fires", *ex("privacy_request", "a copy of all my personal data"), "an example in commands/tests/test_desk_rules.py"),
    ("fires", *ex("exit_dues", "last working day was"), "an example in commands/tests/test_desk_rules.py"),
    ("fires", *ex("human_requested", "HR se baat"), "an example in commands/tests/test_desk_rules.py"),
    ("near", "en", nm("POSH complaint after three months"), "a near miss in commands/tests/test_desk_rules.py"),
    ("near", "en", nm("where do I file a complaint of sexual harassment"), "a near miss in commands/tests/test_desk_rules.py"),
    ("near", "en", nm("How do I raise a grievance under the IR Code"), "a near miss in commands/tests/test_desk_rules.py"),
    ("near", "en", nm("full and final settlement after my last day"), "a near miss in commands/tests/test_desk_rules.py"),
    ("near", "en", nm("carry forward my earned leave"), "a near miss in commands/tests/test_desk_rules.py"),
    ("near", "en", nm("touched my laptop"), "a near miss in commands/tests/test_desk_rules.py"),
    ("numbers", "en", CARD_ROW, "the Visa test number, which passes the Luhn check"),
    ("numbers", "en", AADHAAR_ROW, "lesson 4.8's synthetic Aadhaar, which fails the Verhoeff check"),
]
R = desk_rules


def frame(t: str) -> str:
    m = R.INFO.search(R._HELP.sub(" ", t))
    return m.group(0).strip() if m else ""


def why(words: str) -> dict:
    """gate()'s steps on one question, from the kit's own patterns: the class, and one line per check."""
    t, cls = R.normalise(words), R.gate(words)
    person = bool(R._HUMAN_IMPERATIVE.search(t) or R._first_person(t))
    steps = [["yes" if person else "no", "a first-person marker, or a request for a person" if person else
              "no first-person marker: it is about a rule or someone else, so gate() stops at its first check"]]
    focus = cls
    if person and cls is None:   # the class whose topic the words touch, if any
        focus = next((c for c in R.CLASSES if (R.DISCLOSE.get(c) and R.DISCLOSE[c].search(t))
                      or (R.PROCESS.get(c) is not None and R.PROCESS[c].search(t))), None)
        if focus is None and (R._EXIT_MONEY.search(t) or R._NOT_PAID.search(t)):
            focus = "exit_dues"
    if person and focus == "exit_dues":
        money, unpaid = bool(R._EXIT_MONEY.search(t) or R._GENERIC_MONEY.search(t)), bool(R._NOT_PAID.search(t))
        future = bool(R._EXIT_IF.search(t) and not R._EXIT_DONE.search(t))
        steps.append(["yes" if money else "no", "money a leaver is owed: salary, full and final, gratuity, dues"])
        steps.append(["yes" if unpaid else "no", "words that it has not been paid" if unpaid else "nothing says it has not been paid"])
        if future:
            steps.append(["no", "the leaving has not happened yet: a question about how the rule works"])
    elif person and focus == "human_requested":
        steps.append(["yes", "asks for a person now, not whether or when to ask for one"])
    elif person and focus:
        d = R.DISCLOSE[focus].search(t) if R.DISCLOSE.get(focus) else None
        p = R.PROCESS[focus].search(t) if R.PROCESS.get(focus) is not None else None
        steps.append(["yes" if d else "no", f"a {focus} DISCLOSE pattern: it happened to the person, or names who did it"
                      if d else f"no {focus} DISCLOSE pattern: nothing says it happened to the person"])
        if not d:
            steps.append(["yes" if p else "no", f"a {focus} PROCESS pattern: a step such as filing or raising one"])
            if p:
                req, fr = bool(R.REQUEST.search(t)), frame(t)
                if req:
                    steps.append(["yes", "a plain request for the step itself, so the frame does not matter"])
                else:
                    steps.append(["no" if fr else "yes", f'an information frame ("{fr}"): it asks how the law or the process works'
                                  if fr else "no information frame around it"])
    elif person:
        steps.append(["no", "no class's topic: an ordinary question for the documents"])
    fired = next((c for c in R.CLASSES if R._fires(c, t)), None) if person else None
    assert fired == cls, (words, fired, cls)            # the steps shown are the ones gate() took
    return {"cls": cls, "steps": steps}


TODAY = datetime(2026, 10, 1, 5, 30, tzinfo=timezone.utc)


def case_side(cls: str) -> dict:
    """What a case of this class shows on acme, from the kit's case table and acme's queues file."""
    spec = desk_law.CASE_TYPES[cls]
    queue = cases.queue_for(cls, QUEUES_ACME, unit="hyderabad")
    due_at, basis = cases._due(cls, queue, QUEUES_ACME, TODAY)
    rec = {"case_type": cls, "queue": queue, "sla_basis": basis, "statutory_flags": []}
    if queue.startswith(desk_law.IC_QUEUE):
        who = ("It waits in the queue of the office the person chooses (ic:hyderabad or ic:pune on acme). Only the members the "
               "person picks, and who hold ic_member for that office, see it in their Desk inbox. The card always shows the "
               "district's Local Committee")
    else:
        q = desk_law.QUEUES[queue]
        who = (f"It waits in the {queue} queue ({q['name']}): a holder of " + " or ".join(q["read"]) + " sees it in their Desk inbox"
               + (f", and a holder of {' or '.join(q['opt_in'])} only when the person chooses to share it" if q["opt_in"] else ""))
    law = []
    for b in desk_law.basis_for(cls):
        line = ""
        if b["lines"]:
            a, z = (int(x) for x in b["lines"].split("-"))
            src = (KIT / "evals/corpus/acme" / b["file"]).read_text(encoding="utf-8").split("\n")   # the kit counts "\n" only
            line = re.sub(r"\s+", " ", " ".join(s.strip() for s in src[a - 1:z])).strip()
            line += "" if line.endswith((".", ";", ":")) else " ..."     # the kit's lines end mid-sentence
            ref = f"evals/corpus/acme/{b['file']}:{b['lines']}"
        else:
            ref = f"{b['file']}: a scan with no text layer in the corpus, so named with no section"
        law.append({"name": b["instrument"] + (", " + b["section"] if b["section"] else ""), "says": b["says"], "ref": ref, "line": line})
    assert (cls == "posh") == (cls not in START)          # POSH opens its card at once; every other class has a button
    assert due_at is not None and basis.startswith("the company's own target")      # acme's file sets every queue's days
    return {"template": desk_law.template(cls), "sensitive": cls in R.SENSITIVE, "who": who, "days": (due_at - TODAY).days,
            "clock": cases.clock(rec, QUEUES_ACME), "law": law, "draft": spec["draft"], "start": START.get(cls)}


WIDGET_ROWS = []
for group, lang, words, src in ROWS:
    w = why(words)
    masked, kinds = R.mask(words)
    WIDGET_ROWS.append({"group": group, "lang": LANG[lang], "words": words, "src": src, "cls": w["cls"], "steps": w["steps"],
                        "masked": masked if kinds else "", "kinds": kinds})
VERDICTS = [r["cls"] for r in WIDGET_ROWS]
assert VERDICTS == [R.gate(w) for _, _, w, _ in ROWS]                                  # the widget shows gate() itself
assert [r["cls"] for r in WIDGET_ROWS if r["group"] == "fires"] == ["posh", "posh", "posh", "grievance", "grievance",
                                                                       "privacy_request", "exit_dues", "human_requested"]
assert all(r["cls"] is None for r in WIDGET_ROWS if r["group"] != "fires")
assert [r["kinds"] for r in WIDGET_ROWS if r["group"] == "numbers"] == [["card"], []]
assert not any(R.mask(w)[1] for g, _, w, _ in ROWS if g != "numbers")
assert identifiers.luhn_valid("4111111111111111") and not identifiers.verhoeff_valid("223456789012")
CLASS_SIDE = {c: case_side(c) for c in R.CLASSES}
# what step 9 says the kit does not do yet, checked here so the page changes when the kit does
ROUTE_ROWS = [json.loads(x) for x in (KIT / "evals/routes.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
assert ROUTE_ROWS and not any(r.get("must_escalate") for r in ROUTE_ROWS)          # no people-written escalation rows yet
assert set(desk_law.IN_FORCE.values()) == {None}                                     # no in-force date entered
assert desk_law.BASIS["posh_act"]["lines"] is None and desk_law.BASIS["posh_act"]["section"] is None
assert "no holiday calendar is loaded" in cases.working_days_after.__doc__
OVERDUE_TF = sorted(f.name for f in (KIT / "terraform").glob("*.tf") if "case_overdue" in f.read_text(encoding="utf-8"))
DESK_ALERTS = (KIT / "terraform/desk_alerts.tf").read_text(encoding="utf-8")
OVERDUE_METRIC = DESK_ALERTS.split('resource "google_logging_metric" "case_overdue" {', 1)[1].split("\n}\n", 1)[0]
OVERDUE_POLICY = DESK_ALERTS.split('resource "google_monitoring_alert_policy" "case_overdue" {', 1)[1].split("\n}\n", 1)[0]
assert OVERDUE_TF == ["desk_alerts.tf"]                # the alert on the job's lines, and nothing else reads them
assert sorted(re.findall(r"^    (\w+) += \"EXTRACT", OVERDUE_METRIC, re.M)) == ["queue", "state"]      # no tenant, no case id
assert "notification_channels = local.alert_channel_ids" in OVERDUE_POLICY and not re.search(r"^  count +=", OVERDUE_POLICY, re.M)
assert '"tenant"' not in EXCERPTS["overdue"][1]              # the line names no company, so the incident cannot
assert "with desk_route off or\nshadow, the page is the case half alone." in (KIT / FD).read_text(encoding="utf-8")
assert 'if desk_mode(doc)[0] != "shadow":\n        return None' in (KIT / CD).read_text(encoding="utf-8")


def imported(rel: str) -> set:
    """Every module a kit file imports, as dotted names (from a import b: a.b)."""
    names = set()
    for node in ast.walk(ast.parse((KIT / rel).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            names |= {f"{node.module}.{a.name}" if node.module else a.name for a in node.names}
    return names


CASE_IMPORTS = imported(CA) | imported(CD) | imported(OV)      # no delivery: nothing in the case path mails, pages or posts
assert not {n.split(".")[0] for n in CASE_IMPORTS} & {"smtplib", "email", "requests", "urllib", "http", "httpx", "twilio",
                                                       "sendgrid", "googleapiclient", "slack_sdk"}, CASE_IMPORTS
assert not any("pubsub" in n or "tasks" in n for n in CASE_IMPORTS), CASE_IMPORTS
# every label step 4 quotes from the Desk page, as the page's code draws it
FD_SRC = (KIT / FD).read_text(encoding="utf-8")
UI_LABELS = ['st.subheader("Tell the Desk")', 'st.text_area("What do you need help with?"', 'st.form_submit_button("Send")',
             'st.caption(f"This is a fixed reply. {used} To reach a person, raise the case below. "',
             'if r.get("checked") else "No AI model was used.")',
             '"A case does not include what you typed here."', 'st.subheader("Raise a case")', '"posh": "Sexual harassment at work (POSH)"',
             'st.selectbox("Your office"', 'st.multiselect("Internal Committee members to contact"',
             'st.form_submit_button("Create a confidential record"', 'st.success(f"Recorded. Your case reference is {_ref(done[\'view\'])}.")',
             'st.button("Record another"', 'st.markdown(f"**Target date:** {_when(case[\'due_at\'])}")',
             '"grievance": "A complaint about how I am treated at work"', 'st.form_submit_button("Next: check it before sending")',
             'st.form_submit_button("Send", type="primary")', '"Sent. Your case reference is {_ref(out)}. You can follow it under Your cases."',
             'st.subheader("Your cases")', 'st.subheader("Your inbox")', '"acknowledged": "Acknowledged (we have seen it)"',
             'st.selectbox("Change the status to"', 'st.form_submit_button("Update")', 'f"Updated: {MOVE.get(to, to)}."',
             'return str(case.get("case_id") or "")[:8].upper()', 'if employee and offer.get("desk_gate") in ("rules", "on"):',
             'st.warning(SIGN_IN)', '"The case desk needs your company\'s sign-in (IAP)', '"Raise a grievance"',
             'ss["desk_kind"] = "posh"             # the POSH card at once', '"members see it in their inbox."',
             '"The record keeps your name, your office and the members you chose, and none of your words. Only those "',
             '"Seen by the team"', '"grievance": "Grievance"', 'st.selectbox("What is it about?"', '"posh": "POSH complaint"',
             '"open": "Sent"', 'st.markdown("**The law it rests on:**  \\n"',
             'with st.expander(f"{name}. Status: {state}"):']
assert all(label in FD_SRC for label in UI_LABELS), [label for label in UI_LABELS if label not in FD_SRC]
assert "A fluent Hindi and Hinglish speaker has not reviewed them" in (KIT / "commands/tests/test_desk_rules.py").read_text(encoding="utf-8")
assert CLASS_SIDE["grievance"]["days"] == SLA["grc"] and desk_law.CLOCKS["company_target"] in CLASS_SIDE["grievance"]["clock"]
assert "The date shown is the company's own target." in CLASS_SIDE["privacy_request"]["clock"][0]
assert CLASS_SIDE["posh"]["law"][0]["line"] == "" and all(l["line"] for c in ("grievance", "exit_dues", "privacy_request") for l in CLASS_SIDE[c]["law"])

# ------------------------------------------------------------------ the stand-ins: one fake Firestore, one fake audit bucket
db = tc.FakeDB()
_hex = (hashlib.sha256(f"lesson 10.5, stand-in {i}".encode()).hexdigest() for i in itertools.count())
_tick = itertools.count()


def tick() -> datetime:
    return TODAY + timedelta(seconds=next(_tick))


class FakeDT(datetime):
    @classmethod
    def now(cls, tz=None):
        return tick()


class Blob:
    def __init__(self, bucket, name):
        self.bucket, self.name, self.data, self.time_created = bucket, name, "", None

    def upload_from_string(self, data, content_type=None):
        self.data, self.time_created = data, tick()
        self.bucket.blobs.append(self)

    def download_as_text(self):
        return self.data


class Bucket:
    def __init__(self, name):
        self.name, self.blobs = name, []

    def blob(self, name):
        return Blob(self, name)

    def list_blobs(self, prefix=""):
        tail = prefix.split("/", 3)[-1]                    # the day is the stand-in's own; the tenant is what is asked
        return [b for b in self.blobs if b.name.split("/", 3)[-1].startswith(tail)]


AUDIT = Bucket(f"{LANE_ID}-audit")
fake_storage = types.ModuleType("google.cloud.storage")
fake_storage.Client = lambda *a, **k: types.SimpleNamespace(bucket=lambda name: AUDIT, get_bucket=lambda name: AUDIT)
audit_log = tc.audit_log
STACK = contextlib.ExitStack()
for p in (patch.object(cases, "_fs", lambda: tc.FS), patch.object(cases, "_now", tick),
          patch.object(cases, "secrets", types.SimpleNamespace(token_hex=lambda n=16: next(_hex)[:2 * n])),
          patch.object(audit_log, "storage", fake_storage), patch.object(audit_log, "_bucket", None),
          patch.object(audit_log, "datetime", FakeDT),
          patch.object(audit_log, "uuid", types.SimpleNamespace(uuid4=lambda: uuid.UUID(hex=next(_hex)[:32], version=4))),
          patch.dict(os.environ, {"AUDIT_BUCKET": f"{LANE_ID}-audit"})):
    STACK.enter_context(p)


def sa(name: str) -> str:
    return f"documind-{name}-sa@{LANE_ID}.iam.gserviceaccount.com"


# the roster as make roster leaves it (3.1 put you on acme; this lesson adds the eval accounts)
ROSTER_PLAN = {}
for t, e in (lane.roster_plan(LANE_ID, "acme", [ME])[0] + lane.roster_plan(LANE_ID, "acme", [sa("evalacme"), sa("evalgrc")])[0]
             + lane.roster_plan(LANE_ID, "zeta", [sa("evalzeta")])[0]):
    ROSTER_PLAN.setdefault(e.lower(), [])
    if t not in ROSTER_PLAN[e.lower()]:
        ROSTER_PLAN[e.lower()].append(t)
        db.collection("tenants").document(t).collection("members").document(e.lower()).set({"email": e.lower()})
assert ROSTER_PLAN[sa("ui")][0] == "acme" and ROSTER_PLAN[sa("evalzeta")] == ["zeta"] and sa("outsider") not in ROSTER_PLAN
db.collection("tenant_settings").document("acme").set({"data_region": "any"})


def ops(*args) -> str:
    """commands/desk_ops.py, as make runs it, against the fake Firestore."""
    fs = types.SimpleNamespace(Client=lambda project=None: db, SERVER_TIMESTAMP="SERVER_TIMESTAMP")
    with tc.cloud_modules(firestore=fs), patch.dict(os.environ, {"DOCUMIND_OPERATOR": ME}), redirect_stdout(io.StringIO()) as out:
        desk_ops_main = tc.desk_ops.main
        code = desk_ops_main(["--project", LANE_ID, *args])
    return out.getvalue(), code


T = Path(tempfile.mkdtemp(prefix="lesson105-"))
qfile = T / "queues.acme.json"
qfile.write_text((KIT / "evals/desk/queues.acme.json").read_text(encoding="utf-8").replace("you@example.com", ME), encoding="utf-8")
OUT = {}
o1, c1 = ops("queues", "--tenant", "acme", "--file", str(qfile))
o2, c2 = ops("desk", "--tenant", "acme")                                          # the switch as it stands: nothing set
assert (c1, c2) == (0, 0) and json.loads(o2)["desk_gate"] == "rules" and "desk_gate" not in db.docs["tenant_settings/acme"]
assert "ic hyderabad: " in o1 and "ic pune: " in o1                               # nobody reads POSH cases yet
OUT["queues"] = o1 + o2
o3, c3 = ops("roles", "--tenant", "acme", "--email", sa("evalgrc"), "--set", "grc_member")
o4, c4 = ops("roles", "--tenant", "acme", "--email", ME, "--set", "employee,grc_member,ic_member:hyderabad,ic_member:pune")
assert (c3, c4) == (0, 0) and "no employee or leaver role" in o3
assert {"ic_member:hyderabad", "ic_member:pune"} <= set(json.loads(o4)["after"])
OUT["roles"] = o3 + o4
ROLE_EVENTS = [json.loads(b.data) for b in AUDIT.blobs]
assert [e["action"] for e in ROLE_EVENTS] == ["role.grant", "role.revoke", "role.grant"] and ROLE_EVENTS[0]["actor"]["email"] == ME
assert roles.desks(roles.roles_for(db, "acme", sa("evalgrc"))) == set()            # grc_member alone raises no case

# ------------------------------------------------------------------ the two doors and the case routes, behind a local bridge
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

BEARER = {"ui": sa("ui"), "evalacme": sa("evalacme"), "evalgrc": sa("evalgrc"), "evalzeta": sa("evalzeta"),
          "outsider": sa("outsider"), "me": ME}


def bearer_email(headers) -> str:
    auth = headers.get("authorization") or ""
    who = BEARER.get(auth[7:]) if auth.startswith("Bearer ") else None
    if not who:
        raise HTTPException(401, "no identity")
    return who


def settings(tenant):
    return dict(db.docs.get(f"tenant_settings/{tenant}") or {})


ROWS_LOGGED = []


class Rows(logging.Handler):
    def __init__(self, service):
        super().__init__(logging.INFO)
        self.service = service

    def emit(self, record):
        ROWS_LOGGED.append((self.service, json.loads(record.getMessage())))


for name, svc in (("documind-api", "documind-api"), ("documind.chat.desk", "documind-chat")):
    lg = logging.getLogger(name)
    lg.addHandler(Rows(svc))
    lg.setLevel(logging.INFO)
    lg.propagate = False


async def handler_app(scope, receive, send):           # rag-api's handlers: a question the gate does not take
    await receive()
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": b'{"handler":true}'})


def member(email, tenant):
    if tenant not in ROSTER_PLAN.get(email.lower(), []):
        raise HTTPException(403, f"{email} is not a member of {tenant}")


api_app = door_mod.DeskDoor(handler_app, settings=settings, verify=lambda c: {"email": bearer_email(c.headers)}, member=member)
chat_app = FastAPI()
STACK.enter_context(patch.object(chat_desk, "PROFILE", "gcp"))
STACK.enter_context(patch.object(chat_desk, "settings", settings))
STACK.enter_context(patch.object(chat_desk, "_client", lambda: db))
# the door's own tenants read, over the stand-in: no company on this lane switches the model check on (acme stays on
# rules), so the list is empty
assert desk_recall.read_on_tenants(db) == frozenset()
STACK.enter_context(patch.object(chat_desk, "CHECKED",
                                 desk_recall.OnTenants(lambda: desk_recall.read_on_tenants(db), chat_desk.log, "chat")))
assert chat_desk.CHECKED.get() == frozenset()   # the door's read, run once here: every chat turn below is a gate hit
chat_desk.install(chat_app, caller=lambda request: {"email": bearer_email(request.headers), "assertion": None},
                  tenant_for=lambda e: (ROSTER_PLAN.get(e.lower()) or [None])[0], thread_config=lambda *a: None)
LOCK = threading.Lock()


def bridge(app):
    client = TestClient(app, raise_server_exceptions=True)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _go(self):
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n) if n else None
            with LOCK:
                r = client.request(self.command, self.path, content=body,
                                   headers={k: v for k, v in self.headers.items() if k.lower() not in ("host", "content-length")})
            data = r.content
            self.send_response(r.status_code)
            for k, v in r.headers.items():
                if k.lower() not in ("content-length", "transfer-encoding", "connection", "date", "server"):
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = _go

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


api_srv, API_LOCAL = bridge(api_app)
chat_srv, CHAT_LOCAL = bridge(chat_app)
chat_client = TestClient(chat_app)


def as_who(who, method, path, body=None):
    r = chat_client.request(method, path, json=body, headers={"Authorization": f"Bearer {who}"})
    return r.status_code, r.json()


# the Desk page, as you (step 4): Tell the Desk, the POSH card, a grievance drafted and sent, acknowledged in your inbox
s, told = as_who("me", "POST", "/v1/chat", {"question": POSH, "session_id": "deskpage1", "brain": "direct"})
assert (s, told["brain"], told["model"]) == (200, "desk_gate", "none") and told["answer"] == desk_law.template("posh")
assert told["case_offer"] == {"case_type": "posh"}                                  # the POSH card opens at once
s, ui_offer = as_who("me", "GET", "/v1/cases/offer")
assert s == 200 and (ui_offer["email"], ui_offer["tenant"], ui_offer["desk_gate"], ui_offer["desk_route"]) == (ME, "acme", "rules", "off")
assert "employee" in ui_offer["roles"] and sorted(ui_offer["posh"]) == ["hyderabad", "pune"]
assert {"name": "Presiding Officer (placeholder)", "email": ME} in ui_offer["posh"]["hyderabad"]["members"]
OFFER_TYPES = ui_offer["types"]
assert OFFER_TYPES == list(desk_law.CASE_TYPES), OFFER_TYPES                        # acme's file sets up every kind
s, ui_posh = as_who("me", "POST", "/v1/cases", {"case_type": "posh", "unit": "hyderabad", "contacts": [ME], "token": "uipress-" + "a" * 16})
assert s == 200 and ui_posh["summary"] is None and ui_posh["queue"] == "ic:hyderabad", ui_posh
s, ui_draft = as_who("me", "POST", "/v1/cases", {"case_type": "grievance", "summary": "My words, as I would tell the committee."})
s, ui_open = as_who("me", "POST", f"/v1/cases/{ui_draft['case_id']}/confirm", {"token": "uidraft-" + "b" * 16})
assert s == 200 and ui_open["status"] == "open"
s, ui_inbox = as_who("me", "GET", "/v1/cases")
assert {c["case_id"] for c in ui_inbox["inbox"]} == {ui_posh["case_id"], ui_open["case_id"]}, ui_inbox
assert (ui_inbox["email"], ui_inbox["tenant"]) == (ME, "acme")                       # the page draws them: it is you
s, ui_ack = as_who("me", "POST", f"/v1/cases/{ui_open['case_id']}/status", {"status": "acknowledged"})
assert (s, ui_ack["status"]) == (200, "acknowledged")
UI_VIEW = ui_open

# ------------------------------------------------------------------ the cells
OFFLINE_PY = """import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from shared import desk_rules
from smoke.smoke_cases import POSH                  # the disclosure make smoke-cases sends
for words in (POSH, "Can I file a POSH complaint after three months?", "Can I carry forward my earned leave?",
              "Please refund the hotel booking to my card 4111 1111 1111 1111.", "My Aadhaar 2234 5678 9012 is on the travel form."):
    masked, kinds = desk_rules.mask(words)
    print(f"  gate {str(desk_rules.gate(words)):5}  mask {str(kinds):9} {masked}")
print("  rules", desk_rules.RULES_VERSION)"""

DOORS_PY = """import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from smoke.smoke_cases import POSH                  # the disclosure make smoke-cases sends
def post(path):
    req = urllib.request.Request(os.environ["API"] + path, data=json.dumps({"query": POSH, "tenant_id": "acme"}).encode(),
                                 method="POST", headers={"Content-Type": "application/json",
                                                         "Authorization": "Bearer " + os.environ["TOKEN"]})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.headers.get("Content-Type"), r.read().decode()
kind, sse = post("/v1/stream")
events = [b.split("\\n") for b in sse.strip().split("\\n\\n")]
done = json.loads(events[-1][1][len("data: "):])
print("  /v1/stream", kind, "|", " then ".join(e[0] for e in events))
text = json.loads(events[0][1][len("data: "):])["t"]
print("    token:", text.split(". ")[0] + ".", f"({len(text)} characters in all)")
print("    done: ", {k: done[k] for k in ("model", "backend", "cost_usd", "tokens_in", "tokens_out", "cache_hit")})
kind, raw = post("/v1/query")
r = json.loads(raw)
print("  /v1/query ", kind, "|", {k: r[k] for k in ("model", "backend", "cost_usd", "answerable", "confidence", "citations")})"""

CHATDOOR_PY = """import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from smoke.smoke_cases import POSH
body = json.dumps({"question": POSH, "session_id": "lesson105", "brain": "langchain"}).encode()
req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", data=body, method="POST",
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
a = json.load(urllib.request.urlopen(req, timeout=60))
print(f"  brain {a['brain']}  model {a['model']}  tool_calls {a['tool_calls']}  citations {a['citations']}"
      f"  model_calls {a['limits']['model_calls']}  Rs {a['limits']['cost_inr']}")
print(f"  case_offer {a['case_offer']}")
print("  " + a["answer"].replace("\\n\\n", "\\n  "))"""

CASES_PY = """import json, os, urllib.error, urllib.request, uuid, warnings
from datetime import datetime
warnings.filterwarnings("ignore", category=UserWarning)
def call(who, path, body=None):
    req = urllib.request.Request(os.environ["CHAT"] + path, method="GET" if body is None else "POST",
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["T_" + who]})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
def span(a, b):
    return str(datetime.fromisoformat(b) - datetime.fromisoformat(a))
s, o = call("ACME", "/v1/cases/offer")
print(f"  offer      {s}  {o['tenant']}, desk_gate {o['desk_gate']}, POSH offices {sorted(o['posh'] or {})}")
print(f"             types {', '.join(o['types'])}")
s, d = call("ACME", "/v1/cases", {"case_type": "grievance", "summary": "Lesson 5.6 test case: please close it."})
cid = d["case_id"]
print(f"  draft      {s}  {d['status']} in {d['queue']} ({d['owner']['queue_name']}), expires {span(d['created_at'], d['expire_at'])} after it was made")
print(f"             basis {d['basis'][0]['instrument']}: {', '.join(b['section'] for b in d['basis'])}")
token = "lesson105-" + uuid.uuid4().hex[:12]                      # the page's own token, as the Desk page makes one
one, two = (call("ACME", f"/v1/cases/{cid}/confirm", {"token": token}) for _ in range(2))
print(f"  confirm x2 {one[0]} {one[1]['status']}, {two[0]} {two[1]['status']}: same case {two[1]['case_id'] == cid},"
      f" opened once {two[1]['opened_at'] == one[1]['opened_at']}")
print(f"             due {span(one[1]['opened_at'], one[1]['due_at'])} after it opened: {one[1]['sla_basis']}")
s, b = call("ACME", f"/v1/cases/{cid}/confirm", {"token": token + "-again"})
print(f"  new token  {s}  {b['detail']}")
s, box = call("GRC", "/v1/cases")
print(f"  inbox      {s}  seen as {box['email'].split('@')[0]} in {box['tenant']}, roles {box['roles']},"
      f" the case in it: {cid in [c['case_id'] for c in box['inbox']]}")
s, b = call("GRC", "/v1/cases/offer")
print(f"  grc offer  {s}  {b['detail']}")
for who in ("ZETA", "OUT"):
    s, b = call(who, f"/v1/cases/{cid}")
    print(f"  {who.lower():10} {s}  {b['detail']}")
s, b = call("ACME", f"/v1/cases/{cid}/status", {"status": "closed"})
print(f"  raiser     {s}  {b['detail']}")
for step in ("acknowledged", "closed"):
    s, b = call("GRC", f"/v1/cases/{cid}/status", {"status": step})
    print(f"  committee  {s}  {b['status']}")
open(os.path.expanduser("~/lesson105_case.txt"), "w").write(cid)"""

RECORDS_PY = """import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
p = os.environ["PROJECT"]
db = firestore.Client(project=p)
cid = open(os.path.expanduser("~/lesson105_case.txt")).read().strip()
c = db.collection("cases").document(cid).get().to_dict()
print(f"  cases/{cid}")
print(f"    {c['case_type']} {c['status']} in {c['queue']}, tenant {c['tenant']}, source {c['source']}, via {c['via']}")
print(f"    summary {c['summary']!r}  expire_at {c.get('expire_at', 'gone')}  audit_pending {c['audit_pending']}"
      f"  token_sha256 {len(c['token_sha256'])} hex digits")
evalacme = f"documind-evalacme-sa@{p}.iam.gserviceaccount.com"
mine = (db.collection("cases").where("tenant", "==", "acme").where("requester", "==", evalacme)
        .order_by("created_at", direction=firestore.Query.DESCENDING).limit(10).stream())
posh = next(s.to_dict() for s in mine if s.to_dict()["case_type"] == "posh")
print(f"  the smoke's posh case: {posh['status']} in {posh['queue']}, unit {posh['unit']}, contacts {posh['chosen_contacts']},"
      f" summary {posh['summary']!r}, question_sha256 {posh['question_sha256']!r}")
for who in (os.environ["ME"], f"documind-evalgrc-sa@{p}.iam.gserviceaccount.com"):
    r = db.collection("tenants").document("acme").collection("roles").document(who.lower()).get()
    print(f"  tenants/acme/roles/{who.split('@')[0]}@...: {r.to_dict()['roles']}, set by {r.to_dict()['set_by']}")"""

AUDIT_PY = """import datetime, json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import storage
p = os.environ["PROJECT"]
bucket = storage.Client(project=p).bucket(f"{p}-audit")
day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m/%d")
desk = sorted((b for b in bucket.list_blobs(prefix=f"{day}/acme/") if "/case." in b.name or "/role." in b.name),
              key=lambda b: b.time_created)
print(f"  {len(desk)} case and role events today; the last six:")
for b in desk[-6:]:
    print("   ", b.name.split("/")[-1])
for action in ("case.open", "role.grant"):
    e = json.loads(next(b for b in reversed(desk) if f"/{action}-" in b.name).download_as_text())
    print(f"  {action}: actor {e['actor']}  target {e['target']}  meta {e['meta']}")"""

LOGS_PY = """import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
f = f'resource.type="cloud_run_revision" AND jsonPayload.event="desk_gate" AND timestamp>="{os.environ["SINCE105"]}"'
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                      "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j = e["jsonPayload"]
    print(f"  {e['resource']['labels']['service_name']:13} surface {j['surface']:7} tenant {j['tenant']}  user {j['user']}"
          f"  class {j['class']}  rules {j['rules_version']}")"""


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


SA_FN = 'sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }'
ETOK_FN = ('etok() { gcloud auth print-identity-token --include-email --audiences="$CHAT" \\\n'
           '         --impersonate-service-account="$(sa "$1")"; }')
CELLS = {
    "infra": ('make plan PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"   # the flags you gave make up; the plan refuses to delete\n'
              'python commands/infrastructure.py apply --project "$PROJECT" --region "$REGION" --terraform-dir terraform   # make up\'s first line, alone\n'
              'make build PROJECT="$PROJECT" REGION="$REGION" SERVICES="api ui"\n'
              'make deploy-services PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME" \\\n'
              '  SCRIPTS="commands/lesson-12.2.sh commands/lesson-12.4.sh commands/lesson-12.8.sh"\n'
              'make desk-job PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"   # the same flags as make plan'),
    "ids": ('export CHAT="https://documind-chat-$NUMBER.$REGION.run.app" UI="https://documind-ui-$NUMBER.$REGION.run.app"\n'
            'export SINCE105="$(date -u +%FT%TZ)"\n'
            + SA_FN + "\n" + ETOK_FN + "\n"
            'make desk-operators PROJECT="$PROJECT" ADMIN_EMAILS="$ME"\n'
            'make roster PROJECT="$PROJECT" TENANT=acme MEMBERS="$(sa evalacme),$(sa evalgrc)"\n'
            'make roster PROJECT="$PROJECT" TENANT=zeta MEMBERS="$(sa evalzeta)"'),
    "queues": ('sed "s/you@example.com/$ME/g" evals/desk/queues.acme.json > "$HOME/queues.acme.json"   # you sit on both committees\n'
               'make desk-queues PROJECT="$PROJECT" TENANT=acme FILE="$HOME/queues.acme.json"\n'
               'make desk PROJECT="$PROJECT" TENANT=acme   # the switch as it stands: no DESK_GATE, so nothing is written'),
    "roles": ('make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$(sa evalgrc)" ROLES=grc_member\n'
              'make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$ME" ROLES=employee,grc_member,ic_member:hyderabad,ic_member:pune'),
    "page": ('python -c "from smoke.smoke_cases import POSH; print(POSH)"     # the words to paste into Tell the Desk\n'
             'echo "$UI   <- open it signed in as $ME, then choose Desk"'),
    "offline": heredoc(OFFLINE_PY),
    "doors": heredoc(DOORS_PY, 'TOKEN="$(tok "$API")" '),
    "chatdoor": heredoc(CHATDOOR_PY, 'TOKEN="$(etok evalacme)" '),
    "tests": "python -m unittest -v commands/tests/test_cases.py -k who_holds -k expired -k nobody_else -k posh_case_holds -k audit_actor 2>&1 | tail -n 10",
    "cases": heredoc(CASES_PY, 'T_ACME="$(etok evalacme)" T_GRC="$(etok evalgrc)" T_ZETA="$(etok evalzeta)" T_OUT="$(etok outsider)" '),
    "smoke": 'make smoke-cases PROJECT="$PROJECT" REGION="$REGION" IC_EMAIL="$ME"',
    "ops": 'make cases PROJECT="$PROJECT" TENANT=acme\nmake cases-overdue PROJECT="$PROJECT"',
    "records": heredoc(RECORDS_PY),
    "audit": heredoc(AUDIT_PY),
    "logs": heredoc(LOGS_PY),
}
assert "POSH" not in CELLS["page"].split("print(")[0] or "import POSH" in CELLS["page"]

# ------------------------------------------------------------------ run the cells against the stand-ins
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": LANE_ID, "ME": ME,
       "HOME": str(T), "USERPROFILE": str(T), "API": API_LOCAL, "CHAT": CHAT_LOCAL, "TOKEN": "ui", "T_ACME": "evalacme", "T_GRC": "evalgrc",
       "T_ZETA": "evalzeta", "T_OUT": "outsider", "SINCE105": "YYYY-MM-DDTHH:MM:SSZ"}
ISO = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?\+00:00")


def run_cell(body: str, env: dict | None = None, argv: list | None = None) -> str:
    r = subprocess.run([sys.executable] + (argv or ["-"]), input=body if not argv else None, cwd=str(KIT), capture_output=True,
                       text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-1500:]
    return r.stdout


def norm(text: str) -> str:
    return (ISO.sub("YYYY-MM-DDTHH:MM:SS+00:00", text).replace(CHAT_LOCAL, "https://documind-chat-NUMBER.asia-south1.run.app")
            .replace(API_LOCAL, "https://documind-api-NUMBER.asia-south1.run.app"))


OUT["page"] = run_cell("", argv=["-c", "from smoke.smoke_cases import POSH; print(POSH)"]) + \
    "https://documind-ui-NUMBER.asia-south1.run.app   <- open it signed in as you@example.com, then choose Desk\n"
OUT["offline"] = run_cell(OFFLINE_PY)
assert OUT["offline"].count("gate posh") == 1 and OUT["offline"].count("gate None") == 4 and "[card no.]" in OUT["offline"]
n_rows = len(ROWS_LOGGED)
OUT["doors"] = run_cell(DOORS_PY)
assert "event: token then event: done" in OUT["doors"] and "'model': 'none'" in OUT["doors"] and "'cost_usd': 0.0" in OUT["doors"]
assert [r[1]["surface"] for r in ROWS_LOGGED[n_rows:]] == ["stream", "query"]
OUT["chatdoor"] = run_cell(CHATDOOR_PY, env={"TOKEN": "evalacme"})
assert "brain desk_gate  model none  tool_calls []" in OUT["chatdoor"] and "Rs 0" in OUT["chatdoor"]
assert "  case_offer {'case_type': 'posh'}" in OUT["chatdoor"]
OUT["cases"] = norm(run_cell(CASES_PY))
assert "confirm x2 200 open, 200 open: same case True, opened once True" in OUT["cases"] and "expires 0:30:00 after" in OUT["cases"]
assert "zeta       404  no such case" in OUT["cases"] and "out        403  not a member of any tenant" in OUT["cases"]
assert "raiser     403  only the case's queue changes its status" in OUT["cases"] and f"due {SLA['grc']} days, 0:00:00" in OUT["cases"]
assert "offer      200  acme, desk_gate rules, POSH offices ['hyderabad', 'pune']" in OUT["cases"] and "seen as documind-evalgrc-sa in acme" in OUT["cases"]
assert "grc offer  403  your roles in this company do not include raising a case" in OUT["cases"]
CASE_ID = (T / "lesson105_case.txt").read_text().strip()

# the offline tests: the kit's own, run on the kit here
t = subprocess.run([sys.executable, "-m", "unittest", "-v", "commands/tests/test_cases.py", "-k", "who_holds", "-k", "expired",
                    "-k", "nobody_else", "-k", "posh_case_holds", "-k", "audit_actor"], cwd=str(KIT), capture_output=True,
                   text=True, env={**ENV, "PYTHONPATH": ""})
assert t.returncode == 0, t.stderr[-1500:]
TEST_LINES = (t.stdout + t.stderr).rstrip("\n").splitlines()[-10:]
assert sum(" ... ok" in line for line in TEST_LINES) == 5 and TEST_LINES[-1] == "OK", TEST_LINES
OUT["tests"] = "\n".join(re.sub(r"Ran (\d+) tests in [\d.]+s", r"Ran \1 tests in N.NNNs", line) for line in TEST_LINES)

# make smoke-cases: the kit's smoke, against the bridge (it reads DOCUMIND_IC_EMAIL when it runs)
SMOKE_ENV = {"DOCUMIND_CHAT_URL": CHAT_LOCAL, "DOCUMIND_API_URL": API_LOCAL, "DOCUMIND_PROJECT": LANE_ID,
             "DOCUMIND_OUTSIDER_SA": sa("outsider"), "DOCUMIND_IC_EMAIL": ME, "DOCUMIND_TENANT": "acme"}
token_for = {v: k for k, v in BEARER.items()}
with patch.dict(os.environ, SMOKE_ENV):
    smoke = load("smoke_cases_105_run", "smoke/smoke_cases.py")
    with patch.object(smoke, "token_as", lambda acct, audience: token_for.get(acct)), redirect_stdout(io.StringIO()) as so:
        rc = smoke.main()
SMOKE = so.getvalue()
assert rc == 0 and "0 failed" in SMOKE, SMOKE
N_SMOKE = SMOKE.count("[PASS]")
OUT["smoke"] = norm(SMOKE).strip("\n") + "\n"

# make cases, make cases-overdue
OUT["ops"], _ = ops("cases", "--tenant", "acme")
ov = []
h = logging.Handler()
h.emit = lambda r: ov.append(r.getMessage())
olg = logging.getLogger("documind.chat.overdue")
olg.addHandler(h)
olg.setLevel(logging.INFO)
olg.propagate = False
tc.desk_overdue.scan(db, now=TODAY + timedelta(hours=1))
OUT["ops"] = norm(OUT["ops"]) + "\n".join(ov) + "\n"
assert "2 open case(s): 0 due, 0 breached" in OUT["ops"] and '"due": 0, "breached": 0' in OUT["ops"]


def run_here(code: str, mods: dict) -> str:
    """A cell that reads Google Cloud, run in this process with stand-ins for the clients it imports."""
    with tc.cloud_modules(**mods), patch.dict(os.environ, {"HOME": str(T), "USERPROFILE": str(T), "PROJECT": LANE_ID, "ME": ME, "SINCE105": "-"}), \
            redirect_stdout(io.StringIO()) as out:
        exec(compile(code, "<cell>", "exec"), {"__name__": "__cell__"})
    return out.getvalue()


fake_fs = types.SimpleNamespace(Client=lambda project=None: db, Query=types.SimpleNamespace(DESCENDING="DESCENDING"))
OUT["records"] = norm(run_here(RECORDS_PY, {"firestore": fake_fs}))
assert "summary None" in OUT["records"] and "expire_at gone" in OUT["records"] and "audit_pending []" in OUT["records"]
OUT["audit"] = run_here(AUDIT_PY, {"storage": fake_storage})
assert "case.open: actor {'tenant_id': 'acme', 'case_ref': 'case:" in OUT["audit"] and "@" not in OUT["audit"].split("case.open:")[1].split("role.grant:")[0]
LOG_ROWS = [{"jsonPayload": j, "resource": {"labels": {"service_name": svc}}} for svc, j in ROWS_LOGGED if j.get("event") == "desk_gate"]
assert not [j for _, j in ROWS_LOGGED if j.get("event") == "desk_check_tenants_unread"], "a tenants read failed while the build ran the chat door"
fake_sub = types.ModuleType("subprocess")
fake_sub.run = lambda cmd, **kw: types.SimpleNamespace(stdout=json.dumps(LOG_ROWS), stderr="", returncode=0)
with patch.dict(sys.modules, {"subprocess": fake_sub}):
    OUT["logs"] = run_here(LOGS_PY, {})
assert OUT["logs"].count("user None") == len(LOG_ROWS) and "class sensitive" in OUT["logs"]

# the shapes of what the lane prints for the commands that run Terraform, builds and gcloud
mk_rec = mk_src[mk_src.index("desk-job: guard-project"):]
JOB_ECHO = re.findall(r'@echo ">> (.+)"', mk_rec)[:2]
assert len(JOB_ECHO) == 2 and JOB_ECHO[0].startswith("documind-cases-overdue declared on $(CHAT_IMAGE)")
# make desk-job is make plan with DESK_JOB=true, then make up's apply: the same guard, the same lines
assert mk_rec.startswith("desk-job: guard-project tf-backend\n\t$(INFRA) plan $(INFRA_FLAGS) $(INFRA_VARS)\n\t$(INFRA) apply $(INFRA_FLAGS)\n")
CHAT_IMAGE = f"asia-south1-docker.pkg.dev/{PROJ}/documind/chat:COMMIT"
N_JOB = len(re.findall(r"^  count\s+= local\.desk_job \? 1 : 0$", tf_src, re.M))
assert N_JOB == 3                                  # the job, its invoker binding, the hourly schedule
mkfile = (KIT / "Makefile").read_text(encoding="utf-8")
assert 'echo ">> $$f (DEPLOY block)"' in mkfile and 'echo ">> building $(IMAGE_REPO)/$$svc:$(GIT_SHA) from services/$$dir"' in mkfile
infra_src = (KIT / "commands/infrastructure.py").read_text(encoding="utf-8")
PASS_LINES = [re.search(r'print\(f?"(PASS: no deletes[^"]*)', infra_src).group(1).replace("{path}", ".../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan"),
              re.search(r'print\(f?"(Review the displayed changes[^"]*)', infra_src).group(1),
              re.search(r'print\(f?"(PASS: selected plan[^"]*)', infra_src).group(1).replace("{path}", ".../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan")]
REPO = f"asia-south1-docker.pkg.dev/{PROJ}/documind"
PLANNED = PASS_LINES[0] + "\n" + PASS_LINES[1] + "\n" + PASS_LINES[2] + "\n...\n"
OUT["infra"] = (f"...\nPlan: {N_PLAN_ADD} to add, 1 to change, 0 to destroy.\n" + PLANNED
                + f"Apply complete! Resources: {N_PLAN_ADD} added, 1 changed, 0 destroyed.\n"
                + f">> building {REPO}/api:COMMIT from services/rag-api\n...\n>> building {REPO}/ui:COMMIT from services/frontend\n...\n"
                + "".join(f">> commands/lesson-12.{n}.sh (DEPLOY block)\n...\n" for n in (2, 4, 8))
                + f"...\nPlan: {N_JOB} to add, 0 to change, 0 to destroy.\n" + PLANNED
                + f"Apply complete! Resources: {N_JOB} added, 0 changed, 0 destroyed.\n"
                + "\n".join(">> " + e.replace("$(CHAT_IMAGE)", CHAT_IMAGE) for e in JOB_ECHO) + "\n")
ROSTER_A, POLICIES = lane.roster_plan(LANE_ID, "acme", [sa("evalacme"), sa("evalgrc")])
ROSTER_Z, _ = lane.roster_plan(LANE_ID, "zeta", [sa("evalzeta")])
assert 'echo ">> $$who may mint tokens as $$sa"; done; done' in mk_src
assert POLICIES == [("acme", "any"), ("zeta", "any"), ("globex", "in")]
pol = "".join(f"{t}: data_region={r}\n" for t, r in POLICIES)
OUT["ids"] = ("".join(f">> {ME} may mint tokens as {a}\n" for a in EVAL_SAS)
              + "".join(f"{e.lower()} is on {t}\n" for t, e in ROSTER_A[:2]) + "...\n" + pol
              + "".join(f"{e.lower()} is on {t}\n" for t, e in ROSTER_Z[:1]) + "...\n" + pol)
OUT["queues"] = OUT["queues"].replace(str(qfile), "/home/you/queues.acme.json")
OUT["roles"] = OUT["roles"]

STACK.close()
api_srv.shutdown()
chat_srv.shutdown()
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


def pretty_json_lines(text: str) -> str:
    """desk_ops prints one JSON object a line; shown with a break after each top-level key, as it would wrap anyway."""
    out = []
    for line in text.splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            out.append(line)
            continue
        out.append("{" + ",\n ".join(json.dumps(k) + ": " + json.dumps(v, ensure_ascii=False) for k, v in obj.items()) + "}")
    return "\n".join(out) + "\n"


OUT["queues"] = pretty_json_lines(OUT["queues"])
OUT["roles"] = pretty_json_lines(OUT["roles"])
OUT = {k: v.replace(LANE_ID, PROJ) for k, v in OUT.items()}
assert not any(LANE_ID in v for v in OUT.values())
CELL_LABELS = {
    "infra": "run in the operator shell, in the kit (the Desk's Terraform, the three services rebuilt, the hourly job; many minutes)",
    "ids": "run in the operator shell, in the kit (two URLs, two helpers, the eval accounts minted as and put on rosters)",
    "queues": "run in the operator shell, in the kit (acme's queues with your email in them, then acme's switches as they stand)",
    "roles": "run in the operator shell, in the kit (the committee's account and you get your roles)",
    "page": "run in the operator shell, in the kit (the words to paste, and the page's address)",
    "offline": "run in the operator shell, in the kit (gate() and mask() on your machine; no lane, no cost)",
    "doors": "run in the operator shell, in the kit (the disclosure to rag-api's /v1/stream and /v1/query, as documind-ui-sa)",
    "chatdoor": "run in the operator shell, in the kit (the same words to the chat service, as an acme employee, asking for an agent brain)",
    "tests": "run in the operator shell, in the kit (five of the case queue's offline tests; no lane, no cost)",
    "cases": "run in the operator shell, in the kit (the offer, then a case raised, confirmed twice, read by the committee, refused to others, closed)",
    "smoke": "run in the operator shell, in the kit (the case queue's live smoke)",
    "ops": "run in the operator shell, in the kit (acme's open cases, and the overdue scan the hourly job runs)",
    "records": "run in the operator shell, in the kit (the case, the smoke's POSH case and two role documents, read from Firestore)",
    "audit": "run in the operator shell, in the kit (today's case and role events in the audit bucket)",
    "logs": "run in the operator shell, in the kit (the desk_gate rows since step 3; reads only)",
}
OUT_LABELS = {
    "infra": ("shape (Terraform's, Cloud Build's and gcloud's own lines are cut down; the first plan's counts are a lane's "
              "whose last plan predates the Desk, and a lane planned with this kit already has nothing of the Desk's to add)"),
    "ids": "shape (make roster also puts the services' own accounts on their rosters, as it always has)",
    "queues": "(commands/desk_ops.py run on the kit's own queues file against a stand-in Firestore)",
    "roles": "(commands/desk_ops.py against the same stand-in)",
    "page": "(the first line is the smoke's own sentence)",
    "offline": "(this cell run on the kit)",
    "doors": "(the cell run against the kit's DeskDoor behind a local stand-in; on your lane the same keys and values)",
    "chatdoor": "(the cell run against the kit's ChatDoor behind a local stand-in)",
    "tests": "(run on the kit; your Python may print the test names a little differently)",
    "cases": "(the cell run against the kit's case routes and shared/cases.py behind a local stand-in)",
    "smoke": "(smoke/smoke_cases.py run against the same stand-in; your ids and dates differ)",
    "ops": "(commands/desk_ops.py and desk_overdue.scan() on the stand-in's records: the two cases you raised on the Desk page)",
    "records": "(the cell against the stand-in's records; your ids differ)",
    "audit": "(the cell against a stand-in bucket holding the events the kit wrote; your names and ids differ)",
    "logs": "(the stand-in's rows: what the two doors logged on the local stand-ins while this page was built)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
assert set(CELLS) == set(OUT), set(CELLS) ^ set(OUT)

# ------------------------------------------------------------------ the widget
DATA = {"rows": WIDGET_ROWS, "classes": CLASS_SIDE}
UI_JS = r"""var root = document.getElementById('gt'); if (!root) return;
  var D = %s, $ = function(id){ return document.getElementById(id); };
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  var GROUPS = {fires: 'Questions the gate takes', near: 'Near misses: the documents answer them', numbers: 'Numbers in a question'};
  var sel = $('gt-q');
  Object.keys(GROUPS).forEach(function(g){
    var og = document.createElement('optgroup'); og.label = GROUPS[g];
    D.rows.forEach(function(r, i){ if (r.group !== g) return;
      var o = document.createElement('option'); o.value = i; o.textContent = r.words.length > 70 ? r.words.slice(0, 68) + '...' : r.words; og.appendChild(o); });
    sel.appendChild(og); });
  function render(){
    var r = D.rows[+sel.value], c = r.cls ? D.classes[r.cls] : null, h = '';
    $('gt-words').textContent = r.words;
    $('gt-src').textContent = r.lang + ', ' + r.src;
    var v = $('gt-verdict'); v.className = 'gt-verdict ' + (c ? 'hit' : 'miss');
    v.textContent = 'gate() returns ' + (c ? '"' + r.cls + '"' : 'None');
    $('gt-why').innerHTML = r.steps.map(function(s){ return '<li class="' + s[0] + '">' + (s[0] === 'yes' ? '&#10003; ' : '&#10007; ') + esc(s[1]) + '</li>'; }).join('');
    if (!c) {
      h += '<b class="h">No class: the question goes on</b><p>To retrieval and the model, exactly as before the Desk.</p>';
      if (r.kinds.length) h += '<b class="h">But first, unless desk_gate is off</b><p>For a caller on the roster, the door replaces the ' + esc(r.kinds.join(' and ')) + ' number before any handler reads the question:</p><p class="gt-reply">' + esc(r.masked) + '</p>';
      else if (r.group === 'numbers') h += '<b class="h">The number stays</b><p>2234 5678 9012 fails the Verhoeff check, so it is not an Aadhaar number, and the question passes as typed.</p>';
    } else {
      h += '<b class="h">Unless desk_gate is off, the door answers</b><p class="gt-reply">' + esc(c.template) + '</p>';
      h += '<p>Model none, Rs 0: nothing is searched, generated or cached. The log row names the class' + (c.sensitive ? ' as "sensitive", with user null.' : ' and the person.') + '</p>';
      h += '<b class="h">The case the reply offers</b><p>The chat door\'s reply carries case_offer, naming ' + esc(r.cls) + '. ' + (c.start ? 'Under the reply, the Desk page shows a button, "' + esc(c.start) + '", that starts this kind of case with an empty form.' : 'The Desk page opens the POSH card at once.') + ' Nothing typed in the box goes into the case.</p>';
      h += '<b class="h">If the person raises it</b><p>' + esc(c.who) + '.</p><p>' + (c.draft ? 'A draft first, which the person reads and sends. Once it is sent, the Desk page' : 'No draft and no text: the case opens at once with the office and the members chosen, and the Desk page') + ' shows its "Target date:", ' + c.days + ' days on, with the clock lines below it.</p>';
      h += '<b class="h">The clock shown with the case</b>';
      c.clock.forEach(function(k){ h += '<p>' + esc(k) + '</p>'; });
      h += '<b class="h">The law it rests on</b>';
      if (!c.law.length) h += '<p>No statute: the company\'s own People team.</p>';
      else h += '<ul class="gt-law">' + c.law.map(function(l){ return '<li><strong>' + esc(l.name) + '</strong>: ' + esc(l.says) + ' <span class="gt-ref">' + esc(l.ref) + '</span>' + (l.line ? '<span class="gt-line">' + esc(l.line) + '</span>' : '') + '</li>'; }).join('') + '</ul>';
    }
    $('gt-out').innerHTML = h;
  }
  sel.addEventListener('change', render);
  sel.value = 0; render();""" % json.dumps(DATA, ensure_ascii=False)

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

GRC_VIEW = {k: UI_VIEW[k] for k in ("queue", "sla_basis")}
STATS = {
    "N_CLASSES": WORDS[len(R.CLASSES)], "N_TYPES": WORDS[len(desk_law.CASE_TYPES)], "N_ROUTES": WORDS[N_ROUTES], "RULES_VERSION": R.RULES_VERSION,
    "MAX_KIB": str(door_mod.MAX_BODY // 1024), "MAX_BYTES": f"{door_mod.MAX_BODY:,}", "QMAX": f"{door_mod.QUERY_MAX:,}",
    "SUMMARY_MAX": f"{cases.SUMMARY_MAX:,}", "DRAFT_MIN": str(int(cases.DRAFT_TTL.total_seconds() // 60)),
    "TOKEN_H": str(int(cases.TOKEN_TTL.total_seconds() // 3600)), "LIMIT": str(cases.LIMIT), "ACTIVE_LIMIT": str(cases.ACTIVE_LIMIT),
    "DUE_SOON_H": str(int(cases.DUE_SOON.total_seconds() // 3600)), "SETTINGS_S": str(chat_desk.SETTINGS_TTL_S),
    "RECALL_MODEL": desk_recall.MODEL,
    "N_EXISTING": str(N_EXISTING), "N_EXAMPLES": str(N_EXAMPLES), "N_NEAR": str(N_NEAR), "N_EVAL": WORDS[len(EVAL_SAS)],
    "N_INDEXES": WORDS[N_INDEXES], "N_TF_ADD": str(N_TF_ADD), "N_SMOKE": str(N_SMOKE), "N_ROWS": str(len(ROWS)),
    "N_PLAN_ADD": str(N_PLAN_ADD), "N_METRICS": WORDS[N_METRICS], "N_POLICIES": WORDS[N_POLICIES], "N_GCHAT": str(N_GCHAT),
    "N_ROUTER_ALERTS": WORDS[N_ROUTER_ALERTS], "N_JOB": WORDS[N_JOB],
    "N_KIT_ROWS": str(sum(g != "numbers" for g, _, _, _ in ROWS)), "N_PAGE_ROWS": WORDS[sum(g == "numbers" for g, _, _, _ in ROWS)],
    "SIGN_IN": html.escape(fd_const("SIGN_IN"), quote=False),
    "SLA_GRC": str(SLA["grc"]), "SLA_POSH": str(SLA["posh"]), "SLA_PRIVACY": str(SLA["privacy"]), "SLA_PAYROLL": str(SLA["payroll"]),
    "SLA_PEOPLE": str(SLA["people"]), "N_LOG_ROWS": WORDS[len(LOG_ROWS)], "AUDIT_LEASE_MIN": str(int(cases.AUDIT_LEASE.total_seconds() // 60)),
    "POSH_WORDS": html.escape(POSH),
}
assert GRC_VIEW == {"queue": "grc", "sla_basis": f"the company's own target: {SLA['grc']} days (case_queues.grc.sla_days)"}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    for r in WIDGET_ROWS:
        print(f"----- {r['cls']}  {r['words']}\n" + "\n".join(f"   {a:3} {b}" for a, b in r["steps"]))
    print(json.dumps(CLASS_SIDE, indent=1, ensure_ascii=False))
    print(STATS)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: gate() on {len(ROWS)} of the kit's own rows, each step checked against _fires() | desk_ops, both doors, the case "
      f"routes and the smoke run on stand-ins ({N_SMOKE} PASS) | the cells' outputs from the kit's own code")
