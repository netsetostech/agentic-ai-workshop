#!/usr/bin/env python3
"""Live smoke test for the routed DocuMind Desk (workshop lesson 10.4), then the case queue's (smoke_cases.py).

    make smoke-desk PROJECT=documind-ai-YOUR-ID          # from deploy/, after documind-chat and documind-api are deployed

Before it, once per lane, besides smoke_cases.py's own steps (its docstring):
    make roster TENANT=globex MEMBERS=documind-evalglobex-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    make roster TENANT=acme MEMBERS=documind-evalleaver-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    make roles TENANT=acme EMAIL=documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com ROLES=employee,desk_eval
    make roles TENANT=acme EMAIL=documind-evalleaver-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com ROLES=leaver,desk_eval
    make roles TENANT=globex EMAIL=documind-evalglobex-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com ROLES=employee,desk_eval
    make doc-types TENANT=acme SEED=manifest APPLY=1            # and globex: the registry coverage reads
    make route-index TENANT=acme
    make desk TENANT=acme DESK_ROUTE=on
    make desk-queues TENANT=globex FILE=evals/desk/queues.globex.json   # its Internal Committee holding ic_member roles
    make desk TENANT=globex DESK_ROUTE=single DESK_SINGLE=statute

    1. POST /v1/desk, a handbook question (route row lk-06), as      -> route handbook, an answer citing acme's own
       documind-evalacme-sa                                             objects, with the row's figure
    2. POST /v1/desk, a statute question (lk-16)                     -> route statute, cited, with the in-force lines
    3. POST /v1/desk, a POSH disclosure                              -> route case by rule, no model call, no case
                                                                        written: the POSH card, each office with its
                                                                        Local Committee contact
    4. POST /v1/desk, an invoice question (lk-10)                    -> out_of_scope by its anchor: the fixed reply,
                                                                        nothing cited, nothing retrieved
    5. POST /v1/desk, lk-06 as documind-evalleaver-sa                -> denied, zero retrieve calls
    6. POST /v1/desk, lk-28 as documind-evalglobex-sa                -> single mode: statute, method single
    7. POST /v1/route as documind-evalacme-sa, then as ui-sa         -> the decision, then 403 (no desk_eval role)
    then smoke_cases.py: the chat door, rag-api's door on /v1/stream (the same POSH words as ui-sa), the case queue.

The questions are the route set's own rows (evals/routes.jsonl), read here by id. A Desk session of its own per run
keeps each turn apart from the next run's.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import smoke_cases  # noqa: E402
from smoke_cases import CHAT_URL, POSH, PROJECT, account, call, token_as  # noqa: E402

ROUTES = HERE.parent / "evals" / "routes.jsonl"
ACME = account("DOCUMIND_REQUESTER_SA", "documind-evalacme-sa")
LEAVER = account("DOCUMIND_LEAVER_SA", "documind-evalleaver-sa")
GLOBEX = account("DOCUMIND_GLOBEX_SA", "documind-evalglobex-sa")
UI = account("DOCUMIND_IMPERSONATE_SA", "documind-ui-sa")
RUN = uuid.uuid4().hex[:10]
passed, failed = [], []


def ok(name, detail=""):
    passed.append(name); print(f"  [PASS] {name}  {detail}")


def bad(name, detail=""):
    failed.append(name); print(f"  [FAIL] {name}  {detail}")


def rows() -> dict:
    return {r["id"]: r for r in (json.loads(x) for x in ROUTES.read_text(encoding="utf-8").splitlines() if x.strip())}


def own(citations, tenant: str) -> bool:
    """Every citation names an object of `tenant` (gs://<bucket>/<tenant>/<name>)."""
    uris = [str(c.get("source_uri") or "") for c in citations or [] if isinstance(c, dict)]
    return bool(uris) and all(u.split("/")[3:4] == [tenant] for u in uris)


def ask(token, question, n, **extra):
    return call(CHAT_URL, "/v1/desk", token, {"question": question, "session_id": f"smoke-desk-{RUN}-{n}", **extra})


def desk_checks(me, leaver, globex) -> None:
    by_id = rows()
    hb, law, oos, single = by_id["lk-06"], by_id["lk-16"], by_id["lk-10"], by_id["lk-28"]

    status, b = ask(me, hb["question"], 1)
    if (status == 200 and b.get("route") == "handbook" and b.get("outcome") == "answer" and own(b.get("citations"), "acme")
            and all(w in b.get("answer", "") for w in hb["must_contain"])):
        ok("handbook", f"{len(b['citations'])} citations, method {b.get('method')}, Rs {b['limits']['cost_inr']}")
    else:
        bad("handbook", f"status={status} {str(b)[:200]} (make desk TENANT=acme DESK_ROUTE=on; make route-index)")

    status, b = ask(me, law["question"], 2)
    sections = b.get("sections") if isinstance(b, dict) else None
    if (status == 200 and b.get("route") == "statute" and own(b.get("citations"), "acme") and sections
            and sections[0].get("in_force")):
        ok("statute", f"in force: {sections[0]['in_force'][0][:70]!r}")
    else:
        bad("statute", f"status={status} {str(b)[:200]}")

    status, b = ask(me, POSH, 3)
    card = (b.get("case_offer") or {}) if isinstance(b, dict) else {}
    units = card.get("posh") or {}
    if (status == 200 and (b.get("route"), b.get("method"), b.get("model_calls")) == ("case", "rule", 0)
            and b.get("case") is None and card.get("case_type") == "posh" and units
            and all((u.get("local_committee") or {}).get("contact") for u in units.values())
            and b.get("retrieve_calls") == 0):
        ok("posh", f"no model call, no case written, offices {sorted(units)}")
    else:
        bad("posh", f"status={status} {str(b)[:200]} (make desk-queues TENANT=acme)")

    status, b = ask(me, oos["question"], 4)
    if (status == 200 and (b.get("route"), b.get("outcome"), b.get("citations"), b.get("retrieve_calls"))
            == ("out_of_scope", "oos", [], 0)):
        ok("out_of_scope", f"method {b.get('method')}: {b.get('answer', '')[:60]!r}")
    else:
        bad("out_of_scope", f"status={status} {str(b)[:200]}")

    status, b = ask(leaver, hb["question"], 5)
    if status == 200 and (b.get("route"), b.get("outcome"), b.get("retrieve_calls"), b.get("citations")) == (
            "denied", "denied", 0, []):
        ok("leaver denied", "zero retrieve calls, a case offered" if b.get("chips") else "zero retrieve calls")
    else:
        bad("leaver denied", f"status={status} {str(b)[:200]} (make roles ... ROLES=leaver,desk_eval)")

    status, b = ask(globex, single["question"], 6)
    if status == 200 and (b.get("tenant"), b.get("route"), b.get("method")) == ("globex", "statute", "single"):
        ok("globex single", f"outcome {b.get('outcome')}, model calls {b.get('model_calls')}")
    else:
        bad("globex single", f"status={status} {str(b)[:200]} (make desk TENANT=globex DESK_ROUTE=single "
                             f"DESK_SINGLE=statute)")

    status, b = call(CHAT_URL, "/v1/route", me, {"question": hb["question"]})
    (ok if status == 200 and b.get("route") == "handbook" and "answer" not in b else bad)(
        "/v1/route", f"status={status} {str(b)[:160]}")
    status, b = call(CHAT_URL, "/v1/route", token_as(UI, CHAT_URL), {"question": hb["question"]})
    (ok if status == 403 else bad)("/v1/route refuses a non-eval caller", f"status={status} {str(b)[:100]}")


def main() -> int:
    if not CHAT_URL or not PROJECT:
        print("DOCUMIND_CHAT_URL and DOCUMIND_PROJECT are not set - this is a LIVE test: make smoke-desk.")
        print(__doc__)
        return 2
    print(f"\n  DocuMind Desk - the routed Desk, live\n  chat: {CHAT_URL}\n  " + "-" * 56)
    me, leaver, globex = (token_as(sa, CHAT_URL) for sa in (ACME, LEAVER, GLOBEX))
    if not (me and leaver and globex):
        bad("tokens", "could not mint as every eval account: make desk-operators ADMIN_EMAILS=you@example.com")
    else:
        desk_checks(me, leaver, globex)
    print("  " + "-" * 56 + f"\n  {len(passed)} passed, {len(failed)} failed\n")
    cases_code = smoke_cases.main()
    return 1 if failed or cases_code else 0


if __name__ == "__main__":
    sys.exit(main())
