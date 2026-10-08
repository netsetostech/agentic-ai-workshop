#!/usr/bin/env python3
"""Live smoke test for the Google Chat door's refusals (workshop lesson 10.4).

    make smoke-gchat PROJECT=documind-ai-YOUR-ID          # from deploy/, after make deploy-gchat

Before it, once per lane: make plan up GCHAT_DOOR=true (terraform/gchat.tf), make deploy-gchat, chat deployed again
with this kit (services/chat/delegation.py ships in the chat image), make operators and make desk-operators
ADMIN_EMAILS=you@example.com (you may mint tokens as the outsider, ui-sa and the eval accounts).

    1. POST /     on documind-gchat as the outsider, a Chat-shaped body   -> 401 from the bridge's code (the outsider is
                                                                             an invoker, so not the network's)
    2. POST /work on documind-gchat as the outsider, a push envelope      -> 401 from the code
    3. POST /v1/desk on documind-chat as documind-evalacme-sa, naming a   -> 403 "not an allowed delegate"
       person in X-DocuMind-Principal
    4. the same as ui-sa                                                  -> the same 403

Then it prints the latest gchat, gchat_answer, gchat_verify_failed, desk (via gchat), desk_delegation_refused and
desk_delegation_denied rows. Steps 3 and 4 each write a desk_delegation_refused row, on which the alert on that event
fires: the alert's own test. By design nothing can mint a token as documind-gchat-sa, so the accepted path is proven
by a person messaging the app in Google Chat (the lane proof). No step sends a question that the Desk's gate catches.

DOCUMIND_PERSON (default: your gcloud account) is the address steps 3 and 4 name; neither is accepted, whoever it is.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

GCHAT_URL = os.environ.get("DOCUMIND_GCHAT_URL", "").rstrip("/")
CHAT_URL = os.environ.get("DOCUMIND_CHAT_URL", "").rstrip("/")
PROJECT = os.environ.get("DOCUMIND_PROJECT", "")
OUTSIDER = os.environ.get("DOCUMIND_OUTSIDER_SA", "")
HEADER = "X-DocuMind-Principal"
NOT_A_DELEGATE = "not an allowed delegate"                  # services/chat/delegation.py
CODE_401 = "this endpoint answers Google Chat and its own push only"   # services/gchat/main.py
QUESTION = "How many days of earned leave can I carry forward?"
ROWS = ('jsonPayload.event="gchat"', 'jsonPayload.event="gchat_answer"', 'jsonPayload.event="gchat_verify_failed"',
        'jsonPayload.event="desk" AND jsonPayload.via="gchat"', 'jsonPayload.event="desk_delegation_refused"',
        'jsonPayload.event="desk_delegation_denied"')
passed, failed = [], []


def account(env: str, name: str) -> str:
    return os.environ.get(env) or (f"{name}@{PROJECT}.iam.gserviceaccount.com" if PROJECT else "")


EVAL = account("DOCUMIND_REQUESTER_SA", "documind-evalacme-sa")
UI = account("DOCUMIND_IMPERSONATE_SA", "documind-ui-sa")


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


def call(base: str, path: str, token: str | None, body: dict | None = None, headers: dict | None = None,
         timeout: int = 60):
    """(status, json-or-text). Errors come back as data so a 403 is a result, not a crash."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{base}{path}", data=data, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw, status = r.read().decode(), r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read().decode(), e.code
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw


def person() -> str:
    if os.environ.get("DOCUMIND_PERSON"):
        return os.environ["DOCUMIND_PERSON"].strip().lower()
    try:
        out = subprocess.run(["gcloud", "config", "get-value", "account"], capture_output=True, text=True, check=True)
        return out.stdout.strip().lower()
    except Exception:  # noqa: BLE001
        return ""


def rows() -> None:
    print("\n  the latest rows (Cloud Logging, the last hour; a row can take a minute to arrive):")
    for flt in ROWS:
        try:
            out = subprocess.run(["gcloud", "logging", "read", flt, f"--project={PROJECT}", "--freshness=1h",
                                  "--limit=3", "--format=json(jsonPayload)"], capture_output=True, text=True,
                                 check=True, timeout=60)
            got = [r.get("jsonPayload") for r in json.loads(out.stdout or "[]")]
        except Exception as e:  # noqa: BLE001 - printing only
            got = [f"(could not read: {type(e).__name__})"]
        print(f"    {flt}")
        for r in got or ["(none)"]:
            print(f"      {json.dumps(r)[:400]}")


def main() -> int:
    if not GCHAT_URL or not CHAT_URL or not PROJECT:
        print("DOCUMIND_GCHAT_URL, DOCUMIND_CHAT_URL and DOCUMIND_PROJECT are not set - this is a LIVE test: "
              "make smoke-gchat.")
        print(__doc__)
        return 2
    print(f"\n  DocuMind Desk - the Google Chat door's refusals, live\n  bridge: {GCHAT_URL}\n  chat:   {CHAT_URL}\n  "
          + "-" * 56)

    t = token_as(OUTSIDER, GCHAT_URL)
    if not t:
        bad("1-2. the outsider", "no token: make operators lets you mint as documind-outsider-sa")
    else:
        event = {"chat": {"messagePayload": {"message": {"name": "spaces/SMOKE/messages/SMOKE", "text": "Hello",
                                                         "sender": {"name": "users/SMOKE", "type": "HUMAN",
                                                                    "email": "employee@example.com"}},
                                             "space": {"name": "spaces/SMOKE", "spaceType": "DIRECT_MESSAGE"}}}}
        status, body = call(GCHAT_URL, "/", t, event)
        detail = body.get("detail") if isinstance(body, dict) else None
        (ok if status == 401 and detail == CODE_401 else bad)("1. POST / as the outsider", f"-> {status} {detail!r}")
        data = base64.b64encode(json.dumps({"key": "0" * 64}).encode()).decode()
        envelope = {"message": {"data": data, "messageId": "1"},
                    "subscription": f"projects/{PROJECT}/subscriptions/documind-gchat-push"}
        status, body = call(GCHAT_URL, "/work", t, envelope)
        detail = body.get("detail") if isinstance(body, dict) else None
        (ok if status == 401 and detail == CODE_401 else bad)("2. POST /work as the outsider", f"-> {status} {detail!r}")

    who = person()
    turn = {"question": QUESTION, "session_id": "smoke-gchat"}
    for step, sa in (("3", EVAL), ("4", UI)):
        t = token_as(sa, CHAT_URL)
        if not t:
            bad(f"{step}. POST /v1/desk as {sa}", "no token: make operators / make desk-operators")
            continue
        status, body = call(CHAT_URL, "/v1/desk", t, turn, headers={HEADER: who or "employee@example.com"})
        detail = body.get("detail") if isinstance(body, dict) else None
        (ok if status == 403 and detail == NOT_A_DELEGATE else bad)(
            f"{step}. POST /v1/desk as {sa.split('@')[0]}, naming a person", f"-> {status} {detail!r}")

    rows()
    print(f"\n  {len(passed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
