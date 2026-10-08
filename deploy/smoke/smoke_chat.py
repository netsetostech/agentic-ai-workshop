#!/usr/bin/env python3
"""Live smoke test for the chat service (lessons 8.7 and 12.8) - four brains over one tool.

    make smoke-chat PROJECT=...                     # from deploy/, after documind-chat is deployed
    DOCUMIND_CHAT_URL=https://documind-chat-NUMBER.us-central1.run.app \\
      DOCUMIND_IMPERSONATE_SA=documind-ui-sa@PROJECT.iam.gserviceaccount.com python smoke/smoke_chat.py

    1. GET /health                    -> 200, the four brain names and the turn limits
    2. POST /v1/chat, brain=direct    -> an answer with citations, as a roster member, in a session new to this run
    3. POST /v1/chat x langchain, langgraph, adk -> retrieve() among the tool calls, citations n = 1..k, [n] in range,
                                         and limits: not stopped, within the call cap, a cost above Rs 0
                                         (workshop lesson 5.5)
       DOCUMIND_EXPECT_STOP=model_calls|turn_budget (make limits-drill): each agent brain answers 200, stopped by it
    4. POST /v1/chat as the outsider  -> 403 from the roster, not 401 from the verifier
                                         (optional: DOCUMIND_OUTSIDER_SA, the eval gate's identity)

The identity is a Google ID token minted AS a service account with the email inside, the
audience being THIS service's URL (shared/iap.identity's bearer leg, 12.8). The chat service
looks the tenant up from the roster - there is no tenant field to send, which is the point.
Each agent brain is a cold import the first time (langchain, langgraph, google-adk), so the
timeout is generous and the first call is the slow one.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import uuid

CHAT_URL = os.environ.get("DOCUMIND_CHAT_URL", "").rstrip("/")
IMPERSONATE = os.environ.get("DOCUMIND_IMPERSONATE_SA", "")
OUTSIDER = os.environ.get("DOCUMIND_OUTSIDER_SA", "")
QUESTION = os.environ.get("DOCUMIND_SMOKE_QUESTION",
                          "After how many years of continuous service does gratuity become payable?")
BRAINS = ("direct", "langchain", "langgraph", "adk")
# A conversation of its own per run (workshop lesson 5.7): a fixed session made every run one turn longer
# on the agent brains' threads, so the second run was graded on a conversation, not a question.
RUN = uuid.uuid4().hex[:8]
MARKER = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")      # citations.py's pill pattern: [1] or [1, 3]
# make limits-drill sets it, with the chat service capped: every agent brain must stop by that limit, with a 200.
EXPECT_STOP = os.environ.get("DOCUMIND_EXPECT_STOP", "")
passed, failed = [], []


def ok(name, detail=""):
    passed.append(name); print(f"  [PASS] {name}  {detail}")


def bad(name, detail=""):
    failed.append(name); print(f"  [FAIL] {name}  {detail}")


def token_as(sa: str) -> str | None:
    if not sa:
        return None
    try:
        out = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email",
                              f"--impersonate-service-account={sa}", f"--audiences={CHAT_URL}"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception as e:  # noqa: BLE001
        print(f"  (could not mint a token as {sa}: {getattr(e, 'stderr', '') or e})".strip()[:300])
        return None


def call(path: str, token: str | None, body: dict | None = None, timeout: int = 180):
    """(status, json-or-text). Errors come back as data so a 403 is a result, not a crash."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{CHAT_URL}{path}", data=data, method="POST" if data else "GET")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            status = r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read().decode(), e.code
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw[:300]


def main() -> int:
    if not CHAT_URL:
        print("DOCUMIND_CHAT_URL is not set - this is a LIVE test, run it after documind-chat is deployed.")
        print(__doc__)
        return 2
    print(f"\n  DocuMind chat - live smoke test\n  target: {CHAT_URL}\n  " + "-" * 56)
    member = token_as(IMPERSONATE)
    if IMPERSONATE and not member:
        print("  (proceeding unauthenticated - expect refusals on a private service)")

    # 1. health: the brains the image can build
    status, body = call("/health", member)
    if status == 200 and isinstance(body, dict) and set(BRAINS) <= set(body.get("brains", [])) \
            and isinstance(body.get("limits"), dict):
        lim = body["limits"]
        ok("health", f"profile={body.get('profile')} default={body.get('default_brain')} "
                     f"limits={lim.get('max_model_calls')} calls, Rs {lim.get('budget_inr')}, {lim.get('deadline_s')} s")
    else:
        bad("health", f"status={status} body={str(body)[:120]}")

    # 2-3. one question, four brains. retrieve() must be among the tool calls of every brain:
    # an agent that answered without it answered from memory (7.3's gate, live).
    for brain in BRAINS:
        status, body = call("/v1/chat", member, {"question": QUESTION, "session_id": f"smoke-{brain}-{RUN}", "brain": brain})
        if status != 200 or not isinstance(body, dict):
            bad(f"brain {brain}", f"status={status} body={str(body)[:160]}")
            continue
        answer, tools = str(body.get("answer") or ""), body.get("tool_calls") or []
        lim = body.get("limits") or {}
        if EXPECT_STOP and brain != "direct":
            # The drill: the limit trips, the turn still answers 200, and the row names the limit.
            stopped = lim.get("stopped_by") == EXPECT_STOP and bool(answer)
            (ok if stopped else bad)(f"brain {brain} stopped", f"stopped_by={lim.get('stopped_by')} "
                                     f"calls={lim.get('model_calls')} Rs {lim.get('cost_inr')}  {answer[:60]!r}")
            continue
        # Every turn reports its limits: not stopped, within its call cap, and - for an agent brain, which pays
        # for its own model calls - a cost above Rs 0 (workshop lesson 5.5).
        limited = (bool(lim) and lim.get("stopped_by") is None
                   and (lim.get("model_calls") or 0) <= (lim.get("max_model_calls") or 0)
                   and (brain == "direct" or (lim.get("cost_inr") or 0) > 0))
        retrieved = any("retrieve" in t for t in tools)
        # The first live run passed on an answer that SAID retrieval was unavailable: the tool was
        # called and the model apologised. A smoke that cannot tell that from a cited answer is not
        # one. Every brain returns the lane's citations - require them; every brain's answer
        # must not carry the tool layer's own failure text.
        cites = body.get("citations") or []
        grounded = "unavailable" not in answer.lower() and bool(cites)
        # An agent brain numbers its citations 1..k for the turn and cites by those numbers, so a marker
        # past the last one cites nothing. The direct brain's [N] is a place in rag-api's packed context,
        # and its citations are only the sources the model quoted: [3] beside one citation is correct.
        marks = {int(n) for group in MARKER.findall(answer) for n in group.split(",")}
        numbered, k = True, list(range(1, len(cites) + 1))   # True: the direct brain numbers as rag-api does
        if brain != "direct":
            numbered = marks <= set(k) and [c.get("n") for c in cites] == k
        if answer and retrieved and grounded and numbered and limited and body.get("brain") == brain:
            ok(f"brain {brain}", f"{body.get('latency_ms')} ms  tools={tools}  citations={len(cites)}  "
                                 f"calls={lim.get('model_calls')} Rs {lim.get('cost_inr')}  {answer[:60]!r}")
        else:
            bad(f"brain {brain}", f"grounded={grounded} numbered={numbered} limited={limited} answer={answer[:70]!r}"
                                  f" tools={tools} citations={[c.get('n') for c in cites]} marks={sorted(marks)}"
                                  f" brain={body.get('brain')} limits={lim}")

    # 4. the outsider: invited by IAM, refused by the roster - 403, and not 401
    if OUTSIDER:
        outsider = token_as(OUTSIDER)
        status, body = call("/v1/chat", outsider, {"question": QUESTION, "session_id": "smoke-outsider"})
        detail = str(body.get("detail") if isinstance(body, dict) else body)[:100]
        (ok if status == 403 else bad)("outsider refused", f"status={status} {detail}")

    print("  " + "-" * 56 + f"\n  {len(passed)} passed, {len(failed)} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
