#!/usr/bin/env python3
"""Live smoke test for the approval wired into the chat service (workshop lesson 5.8): a withdrawal paused for a second
person, the hold, the four-eyes refusal, the stranger's 404, the approval, and a rejection.

    make smoke-approval PROJECT=documind-ai-YOUR-ID          # from deploy/, after documind-chat is deployed (lesson 5.1)

Before it, once per lane (the lesson's lane steps; lesson 5.6 left the eval accounts on their rosters):
    make agent-actions TENANT=acme AGENT_ACTIONS=approval                 # the switch, for acme alone; off for every other company
    make roles TENANT=acme EMAIL=documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com ROLES=employee,doc_approver
    make desk-operators ADMIN_EMAILS=you@example.com                       # you may mint tokens as the eval accounts (5.6)

    1. POST /v1/chat as documind-ui-sa, "Withdraw DOC from search" -> 200: the LangGraph brain asked for withdraw_document and
       on the langgraph brain                                           paused; approval pending, its id, and the fixed answer
    2. POST /v1/chat, the same session, another question           -> 409: the conversation waits for a decision
    3. POST /v1/approvals/{id}/decide, approve, as documind-ui-sa  -> 403: the person who asked cannot approve their own request
    4. GET  /v1/approvals/{id} as documind-evalzeta-sa              -> 404: another company's reader cannot tell it exists
    5. GET  /v1/approvals as documind-evalacme-sa                   -> the record in the approver's pending list
    6. POST .../decide, approve, as documind-evalacme-sa            -> 200: approved; the resumed turn's answer, with
                                                                       withdraw_document among its tool calls and no refusal
    7. POST .../decide again                                        -> 409: already approved
    8. a second withdrawal, a new session, rejected with a reason   -> 200: rejected; refusals ["withdraw_document"], the
                                                                       model told why, nothing withdrawn
    9. GET  /v1/approvals as documind-ui-sa                         -> both records, mine: approved and rejected

It withdraws nothing. The approved record waits for the operator: the run ends by printing make withdraw-run APPROVAL=
for it, and the make restore SOURCE= that brings the document back afterwards. Step 1 depends on the model choosing the
tool for a question that names the file; if it answers in words instead, the smoke says so and stops.

DOCUMIND_DOC (make smoke-approval DOC=) names the document; townhall_2026_q1.md by default, a small acme document that
make restore brings back. The identities are Google ID tokens minted AS each service account for the service's own URL
(shared/iap.identity's bearer leg), as make smoke-cases mints them. The requester is documind-ui-sa (on acme's roster, as
for make smoke); the approver documind-evalacme-sa (DOCUMIND_APPROVER_SA); the stranger documind-evalzeta-sa, on zeta's.
The approval.request, approval.approve and approval.reject events stay in the audit bucket, each with the acting
account as its actor.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import uuid

CHAT_URL = os.environ.get("DOCUMIND_CHAT_URL", "").rstrip("/")
PROJECT = os.environ.get("DOCUMIND_PROJECT", "")
TENANT = os.environ.get("DOCUMIND_TENANT", "acme")
DOC = os.environ.get("DOCUMIND_DOC", "townhall_2026_q1.md")


def account(env: str, name: str) -> str:
    return os.environ.get(env) or (f"{name}@{PROJECT}.iam.gserviceaccount.com" if PROJECT else "")


REQUESTER = account("DOCUMIND_IMPERSONATE_SA", "documind-ui-sa")
APPROVER = account("DOCUMIND_APPROVER_SA", "documind-evalacme-sa")
STRANGER = account("DOCUMIND_STRANGER_SA", "documind-evalzeta-sa")
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


def call(path: str, token: str | None, body: dict | None = None, method: str | None = None, timeout: int = 300):
    """(status, json-or-text). Errors come back as data so a 409 is a result, not a crash."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{CHAT_URL}{path}", data=data, method=method or ("POST" if data else "GET"))
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


def ask(token: str, session: str, question: str):
    return call("/v1/chat", token, {"question": question, "session_id": session, "brain": "langgraph"})


def decide(token: str | None, approval_id: str, kind: str, message: str = ""):
    return call(f"/v1/approvals/{approval_id}/decide", token, {"decisions": [{"type": kind, "message": message}]})


def main() -> int:
    if not CHAT_URL or not PROJECT:
        print("DOCUMIND_CHAT_URL and DOCUMIND_PROJECT are not set - this is a LIVE test: make smoke-approval.")
        return 2
    print(f"\n  smoke-approval  {CHAT_URL}  tenant {TENANT}  document {DOC}  run {RUN}")
    me, second, stranger = token_as(REQUESTER, CHAT_URL), token_as(APPROVER, CHAT_URL), token_as(STRANGER, CHAT_URL)
    if not (me and second):
        bad("tokens", "could not mint tokens as the requester and the approver (make desk-operators ADMIN_EMAILS=you)")
        return 1

    # 1. the withdrawal pauses the turn
    session = f"smoke-approval-{RUN}"
    status, body = ask(me, session, f"Withdraw the document {DOC} from search. It is out of date.")
    rec = body.get("approval") if isinstance(body, dict) else None
    if status == 200 and rec and rec.get("status") == "pending" and "withdraw_document" in body.get("tool_calls", []):
        ok("paused", f"approval {rec['approval_id']}  waiting {[w['tool'] for w in rec['waiting']]}  expires {rec['expire_at']}")
    elif status == 200 and not rec:
        bad("paused", f"the turn did not pause: tool_calls {body.get('tool_calls')} - is acme's agent_actions approval "
                      f"(make agent-actions TENANT=acme AGENT_ACTIONS=approval)? the model answered: {str(body.get('answer'))[:160]}")
        return 1
    else:
        bad("paused", f"status={status} {str(body)[:200]}")
        return 1
    rid = rec["approval_id"]

    # 2. the hold: a paused conversation takes no new question
    status, body = ask(me, session, "What is my notice period?")
    (ok if status == 409 and rid in str(body) else bad)("held", f"status={status} {str(body.get('detail') if isinstance(body, dict) else body)[:120]}")

    # 3. four eyes: the requester's own approval
    status, body = decide(me, rid, "approve")
    (ok if status == 403 else bad)("self-approval refused", f"status={status} {str(body.get('detail') if isinstance(body, dict) else body)[:120]}")

    # 4. the stranger: another company's reader cannot tell the record exists
    if stranger:
        status, body = call(f"/v1/approvals/{rid}", stranger)
        (ok if status == 404 else bad)("stranger 404", f"status={status} {str(body)[:100]}")

    # 5. the approver's inbox
    status, body = call("/v1/approvals", second)
    pending = [r["approval_id"] for r in (body.get("pending") or [])] if isinstance(body, dict) else []
    (ok if status == 200 and rid in pending else bad)("approver inbox", f"status={status} pending {pending}")

    # 6. the second person approves: the turn resumes, the tool runs (it records; the operator withdraws)
    status, body = decide(second, rid, "approve")
    turn, rec = (body.get("turn") or {}, body.get("approval") or {}) if isinstance(body, dict) else ({}, {})
    if status == 200 and rec.get("status") == "approved" and "withdraw_document" in turn.get("tool_calls", []) and not turn.get("refusals"):
        ok("approved", f"by {rec.get('decided_by')}  model_calls {turn.get('limits', {}).get('model_calls')}  Rs {turn.get('limits', {}).get('cost_inr')}"
                       f"\n         answer: {str(turn.get('answer'))[:200]}")
    else:
        bad("approved", f"status={status} {str(body)[:240]}")

    # 7. decided once
    status, body = decide(second, rid, "approve")
    (ok if status == 409 else bad)("decided once", f"status={status} {str(body.get('detail') if isinstance(body, dict) else body)[:120]}")

    # 8. a rejection: the call errors alone, the model is told why, nothing is withdrawn
    session2 = f"smoke-reject-{RUN}"
    status, body = ask(me, session2, f"Please withdraw {DOC} from search.")
    rec2 = body.get("approval") if isinstance(body, dict) else None
    if status == 200 and rec2 and rec2.get("status") == "pending":
        status, body = decide(second, rec2["approval_id"], "reject", "That document is still in force.")
        turn, r = (body.get("turn") or {}, body.get("approval") or {}) if isinstance(body, dict) else ({}, {})
        if status == 200 and r.get("status") == "rejected" and turn.get("refusals") == ["withdraw_document"]:
            ok("rejected", f"refusals {turn.get('refusals')}\n         answer: {str(turn.get('answer'))[:200]}")
        else:
            bad("rejected", f"status={status} {str(body)[:240]}")
    else:
        bad("rejected", f"the second withdrawal did not pause: status={status} {str(body)[:200]}")

    # 9. the requester's own list
    status, body = call("/v1/approvals", me)
    mine = {r["approval_id"]: r["status"] for r in (body.get("mine") or [])} if isinstance(body, dict) else {}
    (ok if status == 200 and mine.get(rid) == "approved" else bad)("my records", f"status={status} {mine}")

    print("  " + "-" * 56 + f"\n  {len(passed)} passed, {len(failed)} failed")
    print(f"\n  Nothing was withdrawn. The operator runs the approval, then brings the document back:\n"
          f"    make withdraw-run PROJECT={PROJECT} APPROVAL={rid}\n"
          f"    make restore PROJECT={PROJECT} SOURCE={TENANT}/{DOC}\n"
          f"  and switches acme back: make agent-actions PROJECT={PROJECT} TENANT={TENANT} AGENT_ACTIONS=off\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
