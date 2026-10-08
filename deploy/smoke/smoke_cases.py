#!/usr/bin/env python3
"""Live smoke test for the DocuMind Desk's case queue and the chat door (workshop lesson 5.6).

    make smoke-cases PROJECT=documind-ai-YOUR-ID          # from deploy/, after documind-chat and documind-api are deployed

Before it, once per lane (the lesson's lane steps):
    make desk-operators ADMIN_EMAILS=you@example.com       # you may mint tokens as the eval accounts
    make roster TENANT=acme MEMBERS=documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com,documind-evalgrc-sa@...
    make roster TENANT=zeta MEMBERS=documind-evalzeta-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    make roles TENANT=acme EMAIL=documind-evalgrc-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com ROLES=grc_member
    make roles TENANT=acme EMAIL=you@example.com ROLES=employee,grc_member,ic_member:hyderabad,ic_member:pune
    make desk-queues TENANT=acme FILE=evals/desk/queues.acme.json     # your email in place of you@example.com
    make desk TENANT=acme                                            # desk_gate: rules (on, with a model_check note, if an
                                                                     # earlier lesson wrote it; off only if someone wrote off)

    1. POST /v1/chat, a POSH disclosure, as documind-evalacme-sa  -> 200 from the door: model none, cost Rs 0, no tool
                                                                     call (no brain ran)
    2. POST /v1/stream on the API, the same words, as ui-sa        -> the done event: model none, cost 0
    3. POST /v1/cases, a grievance, as documind-evalacme-sa        -> a draft in the grc queue, with its basis
    4. POST /v1/cases/{id}/confirm, twice with one token           -> open, and the same case both times
    5. GET  /v1/cases as documind-evalgrc-sa                       -> the case in the committee's inbox
    6. POST /v1/cases/{id}/status as documind-evalgrc-sa           -> acknowledged, then closed (the run tidies up)
    7. GET  /v1/cases/{id} as documind-evalzeta-sa                 -> 404: another tenant cannot tell it exists
    8. POST /v1/cases, a POSH press, twice with one token, as      -> one case, open, with no text, in ic:hyderabad;
       documind-evalacme-sa, naming DOCUMIND_IC_EMAIL                then withdrawn by the account that raised it
    9. GET  /v1/cases as the outsider                              -> 403 from the roster (optional: DOCUMIND_OUTSIDER_SA)

DOCUMIND_IC_EMAIL (make smoke-cases IC_EMAIL=) is an Internal Committee member of acme's hyderabad unit in the queues
file you loaded, holding ic_member:hyderabad (make roles TENANT=acme EMAIL=you@example.com
ROLES=employee,grc_member,ic_member:hyderabad,ic_member:pune); by default, your gcloud account.

The identities are Google ID tokens minted AS each service account, with the email inside, for the service's own URL
(shared/iap.identity's bearer leg). A person cannot be scripted that way, which is why the eval accounts exist
(terraform/desk.tf). The /v1/stream leg runs as ui-sa, on the tenant's roster as for make smoke, because the eval
accounts may invoke the chat service only. The case it opens is a grievance whose summary says it is a smoke test;
its case.open, case.update and case.close events stay in the audit bucket, each with a case reference as its actor.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))       # deploy/: the gate the services run
from shared import desk_rules  # noqa: E402

CHAT_URL = os.environ.get("DOCUMIND_CHAT_URL", "").rstrip("/")
API_URL = os.environ.get("DOCUMIND_API_URL", "").rstrip("/")
PROJECT = os.environ.get("DOCUMIND_PROJECT", "")
TENANT = os.environ.get("DOCUMIND_TENANT", "acme")


def account(env: str, name: str) -> str:
    return os.environ.get(env) or (f"{name}@{PROJECT}.iam.gserviceaccount.com" if PROJECT else "")


REQUESTER = account("DOCUMIND_REQUESTER_SA", "documind-evalacme-sa")
READER = account("DOCUMIND_READER_SA", "documind-evalgrc-sa")
STRANGER = account("DOCUMIND_STRANGER_SA", "documind-evalzeta-sa")
UI = account("DOCUMIND_IMPERSONATE_SA", "documind-ui-sa")
OUTSIDER = os.environ.get("DOCUMIND_OUTSIDER_SA", "")
IC_UNIT = os.environ.get("DOCUMIND_IC_UNIT", "hyderabad")
POSH = "My manager keeps making sexual comments about my body. What can I do?"
RUN = uuid.uuid4().hex[:12]
passed, failed = [], []


def ok(name, detail=""):
    passed.append(name); print(f"  [PASS] {name}  {detail}")


def bad(name, detail=""):
    failed.append(name); print(f"  [FAIL] {name}  {detail}")


def token_as(sa: str, audience: str) -> str | None:
    if not sa:
        return None
    try:
        out = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email",
                              f"--impersonate-service-account={sa}", f"--audiences={audience}"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception as e:  # noqa: BLE001
        print(f"  (could not mint a token as {sa}: {getattr(e, 'stderr', '') or e})".strip()[:300])
        return None


def call(base: str, path: str, token: str | None, body: dict | None = None, method: str | None = None,
         timeout: int = 120):
    """(status, json-or-text). Errors come back as data so a 404 is a result, not a crash."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{base}{path}", data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw, status = r.read().decode(), r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read().decode(), e.code
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw


def ic_email() -> str:
    """The Internal Committee member the POSH press names: DOCUMIND_IC_EMAIL, else your gcloud account."""
    if os.environ.get("DOCUMIND_IC_EMAIL"):
        return os.environ["DOCUMIND_IC_EMAIL"].strip().lower()
    try:
        out = subprocess.run(["gcloud", "config", "get-value", "account"], capture_output=True, text=True, check=True)
        return out.stdout.strip().lower()
    except Exception:  # noqa: BLE001
        return ""


def done_event(sse: str) -> dict | None:
    """The data of the stream's done event."""
    for block in str(sse).split("\n\n"):
        lines = block.strip().splitlines()
        if lines and lines[0] == "event: done" and len(lines) > 1 and lines[1].startswith("data: "):
            return json.loads(lines[1][len("data: "):])
    return None


def main() -> int:
    if not CHAT_URL or not PROJECT:
        print("DOCUMIND_CHAT_URL and DOCUMIND_PROJECT are not set - this is a LIVE test: make smoke-cases.")
        print(__doc__)
        return 2
    if desk_rules.gate(POSH) != "posh":
        print(f"the smoke's POSH question no longer hits the gate (rules {desk_rules.RULES_VERSION}): fix the smoke")
        return 2
    print(f"\n  DocuMind Desk - the case queue, live\n  chat: {CHAT_URL}\n  api:  {API_URL or '(not set)'}\n  " + "-" * 56)
    me, grc, zeta = (token_as(sa, CHAT_URL) for sa in (REQUESTER, READER, STRANGER))
    if not (me and grc and zeta):
        bad("tokens", "could not mint as every eval account: make desk-operators ADMIN_EMAILS=you@example.com")
        print("  " + "-" * 56 + f"\n  {len(passed)} passed, {len(failed)} failed\n")
        return 1

    # 1. the chat door: a POSH disclosure never reaches a brain
    status, body = call(CHAT_URL, "/v1/chat", me, {"question": POSH, "session_id": f"smoke-cases-{RUN}"})
    lim = body.get("limits") if isinstance(body, dict) else {}
    if (status == 200 and body.get("model") == "none" and body.get("brain") == "desk_gate"
            and body.get("tool_calls") == [] and (lim or {}).get("cost_inr") == 0 and body.get("answer")):
        ok("chat door", f"brain={body['brain']} model=none Rs 0  {body['answer'][:60]!r}")
    else:
        bad("chat door", f"status={status} body={str(body)[:200]} (is desk_gate off for {TENANT}? make desk prints it)")

    # 2. rag-api's door: the same words on /v1/stream
    if API_URL:
        status, raw = call(API_URL, "/v1/stream", token_as(UI, API_URL), {"query": POSH, "tenant_id": TENANT})
        done = done_event(raw) if status == 200 else None
        if done and done.get("model") == "none" and done.get("cost_usd") == 0 and done.get("backend") == "desk_gate":
            ok("api door (stream)", "model=none cost_usd=0 backend=desk_gate")
        else:
            bad("api door (stream)", f"status={status} done={done} {str(raw)[:160]}")

    # 3-4. a grievance: drafted, confirmed twice with one token - one case
    status, draft = call(CHAT_URL, "/v1/cases", me, {"case_type": "grievance",
                                                     "summary": f"smoke test {RUN}: please close this case"})
    if status == 200 and draft.get("status") == "draft" and draft.get("queue") == "grc" and draft.get("basis"):
        ok("draft", f"queue=grc expires={draft.get('expire_at')}")
    else:
        bad("draft", f"status={status} body={str(draft)[:200]} (make desk-queues TENANT={TENANT} FILE=...)")
        print("  " + "-" * 56 + f"\n  {len(passed)} passed, {len(failed)} failed\n")
        return 1
    case_id, token = draft["case_id"], f"smoke-{RUN}"
    first = call(CHAT_URL, f"/v1/cases/{case_id}/confirm", me, {"token": token})
    again = call(CHAT_URL, f"/v1/cases/{case_id}/confirm", me, {"token": token})
    if (first[0] == again[0] == 200 and first[1].get("status") == "open" and again[1].get("case_id") == case_id
            and again[1].get("opened_at") == first[1].get("opened_at")):
        ok("confirm, twice", f"one case, open, due {first[1].get('due_at')}")
    else:
        bad("confirm, twice", f"{first[0]} {str(first[1])[:120]} / {again[0]} {str(again[1])[:120]}")

    # 5-6. the committee's inbox, and the committee moves it along
    status, body = call(CHAT_URL, "/v1/cases", grc)
    inbox = [c.get("case_id") for c in body.get("inbox", [])] if isinstance(body, dict) else []
    (ok if status == 200 and case_id in inbox else bad)("inbox", f"status={status} roles={body.get('roles') if isinstance(body, dict) else body} "
                                                                 f"in inbox={case_id in inbox}")
    for step in ("acknowledged", "closed"):
        status, body = call(CHAT_URL, f"/v1/cases/{case_id}/status", grc, {"status": step})
        (ok if status == 200 and body.get("status") == step else bad)(f"status {step}", f"status={status} {str(body)[:120]}")

    # 7. another tenant cannot tell the case exists
    status, body = call(CHAT_URL, f"/v1/cases/{case_id}", zeta)
    (ok if status == 404 else bad)("another tenant", f"status={status} {str(body)[:100]}")

    # 8. POSH: no draft and no text; one token, one case; the account that raised it withdraws it
    ic = ic_email()
    press = {"case_type": "posh", "unit": IC_UNIT, "contacts": [ic], "token": f"smoke-posh-{RUN}"}
    p1, p2 = call(CHAT_URL, "/v1/cases", me, press), call(CHAT_URL, "/v1/cases", me, press)
    if (p1[0] == p2[0] == 200 and p1[1].get("status") == "open" and p1[1].get("summary") is None
            and p2[1].get("case_id") == p1[1].get("case_id") and p1[1].get("queue") == f"ic:{IC_UNIT}"):
        ok("posh, twice", f"one case, no text, Local Committee {(p1[1].get('owner') or {}).get('local_committee', {}).get('contact')}")
        status, body = call(CHAT_URL, f"/v1/cases/{p1[1]['case_id']}/cancel", me, {})
        (ok if status == 200 and body.get("status") == "withdrawn" else bad)("posh withdrawn", f"status={status} {str(body)[:100]}")
    else:
        bad("posh, twice", f"{p1[0]} {str(p1[1])[:160]} / {p2[0]} (is {ic or 'IC_EMAIL'} on the {IC_UNIT} committee in the "
                           f"queues file, with ic_member:{IC_UNIT}? make roles)")

    # 9. the outsider: invited by IAM, refused by the roster
    if OUTSIDER:
        status, body = call(CHAT_URL, "/v1/cases", token_as(OUTSIDER, CHAT_URL))
        (ok if status == 403 else bad)("outsider refused", f"status={status} {str(body)[:100]}")

    print("  " + "-" * 56 + f"\n  {len(passed)} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
