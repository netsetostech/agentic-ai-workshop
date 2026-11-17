#!/usr/bin/env python3
"""Live smoke test for the chat's hand-off to the A2A peer (workshop lesson 10.7) - two turns, two checks.

    make smoke-handoff PROJECT=...                  # from deploy/, after make handoff switched the hand-off on
    DOCUMIND_CHAT_URL=https://documind-chat-NUMBER.REGION.run.app \\
      DOCUMIND_IMPERSONATE_SA=documind-ui-sa@PROJECT.iam.gserviceaccount.com python smoke/smoke_handoff.py

    1. POST /v1/chat, brain=adk, a question about what the corpus holds -> 200, documind_peer among the tool calls,
       and the response's `handoffs`: one hand-off answered, the peer's task completed, within its budget
    2. POST /v1/chat, brain=langchain, the same question -> 200 and no `handoffs` key: the ADK brain alone hands off

The identity, the token and the call are smoke_chat.py's own (token_as, call): a roster member, minted for the chat's
url. The peer's answer comes from acme's corpus, the one roster its account sits on, so the member must resolve to
acme, as documind-ui-sa does on the kit's rosters; a member of another tenant gets the gate's refusal, and check 1
says so. DOCUMIND_HANDOFF_QUESTION replaces the question. Each turn is a session new to this run.
"""
from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smoke_chat as sc  # noqa: E402

QUESTION = os.environ.get("DOCUMIND_HANDOFF_QUESTION",
                          "Ask DocuMind's A2A peer which documents the corpus holds, and how many there are.")
RUN = uuid.uuid4().hex[:8]


def handed_off(status: int, body) -> tuple[bool, str]:
    """Check 1: the ADK turn handed its question to the peer, and the peer's task completed within its budget."""
    if status != 200 or not isinstance(body, dict):
        return False, f"status={status} body={str(body)[:160]}"
    if "handoffs" not in body:
        return False, "no `handoffs` in the response: the hand-off is off (make handoff PROJECT=... switches it on)"
    tools, records = body.get("tool_calls") or [], body.get("handoffs") or []
    sent = [r for r in records if r.get("outcome") != "refused"]
    first = sent[0] if sent else (records[0] if records else {})
    good = ("documind_peer" in tools and bool(sent) and first.get("outcome") == "answered"
            and first.get("state") == "completed" and (first.get("seconds") or 0) <= (first.get("budget_s") or 0)
            and bool(str(body.get("answer") or "").strip()))
    detail = (f"tools={tools} handoffs={[(r.get('outcome'), r.get('state'), r.get('seconds')) for r in records]}"
              f" {str(body.get('answer') or '')[:70]!r}")
    if records and not sent:
        detail += f"  - refused: {records[0].get('reason')}"
    return good, detail


def main() -> int:
    if not sc.CHAT_URL:
        print("DOCUMIND_CHAT_URL is not set - this is a LIVE test, run it after make handoff switched the hand-off on.")
        print(__doc__)
        return 2
    print(f"\n  DocuMind chat - the hand-off to the A2A peer, live\n  target: {sc.CHAT_URL}\n  " + "-" * 56)
    member = sc.token_as(sc.IMPERSONATE)
    status, body = sc.call("/v1/chat", member, {"question": QUESTION, "session_id": f"handoff-adk-{RUN}", "brain": "adk"})
    good, detail = handed_off(status, body)
    (sc.ok if good else sc.bad)("adk hands off", detail)
    status, body = sc.call("/v1/chat", member,
                           {"question": QUESTION, "session_id": f"handoff-langchain-{RUN}", "brain": "langchain"})
    alone = status == 200 and isinstance(body, dict) and "handoffs" not in body
    tools = body.get("tool_calls") if isinstance(body, dict) else str(body)[:120]
    (sc.ok if alone else sc.bad)("langchain answers alone", f"status={status} tools={tools}")
    print("  " + "-" * 56 + f"\n  {len(sc.passed)} passed, {len(sc.failed)} failed\n")
    return 1 if sc.failed else 0


if __name__ == "__main__":
    sys.exit(main())
