"""The ADK brain hands one question to DocuMind's A2A peer, as one more tool (workshop lesson 10.7).

Off unless PEER_URL is set on the chat service. commands/handoff.sh sets it, with PEER_ACCOUNT, the account
documind-agent runs as (read from Cloud Run); the next make deploy-services removes both. Unset, brains.py adds no
tool and every brain answers exactly as before. The ADK brain alone hands off; the other three never see the tool.

What crosses the hop is one question, as an A2A message: not the tenant, not the person, not the thread. A2A carries
no identity of its own (lesson 10.6), so the chat calls the peer as its own account, documind-chat-sa, and the peer
reads the corpus as ITS account, documind-agent-sa, which sits on acme's roster alone. That is a confused deputy
waiting to happen: a zeta member asks the chat, the chat asks the peer, and the peer answers from acme's corpus. The
gate refuses it before anything is sent: a hand-off goes ahead only when the peer's account sits on exactly one
roster, and it is the asker's (shared/tenancy.tenants_of, read as each hand-off starts, so a roster change counts at
once). The refusal names no other tenant: the asker learns only that the peer's corpus is not theirs.

Beside the question, in the request's metadata, go the delegation chain, ["documind_adk"], and a random hand-off id
(workshop lesson 10.7, 13 October 2026). With PEER_CHAIN=on the peer refuses a request whose chain already names it or
holds three agents, before any model call (services/agent/chain.py), and its log line carries the same id as this
side's. With the switch off nothing on the peer acts on either.

Three limits, each a constant here or on the peer:
  HANDOFF_MAX_PER_TURN  2. A third hand-off in one turn is refused before it is sent, parallel calls included.
  PEER_TIMEOUT_S        75. The longest one hand-off waits, and never past the turn's own deadline (limits.Meter,
                        100 s); the UI waits 120 s for the whole turn. A cut hand-off is a payload error, as a cut
                        retrieve() is, and tool_timeouts names it. The peer may work on; nothing it says after the
                        cut reaches the turn.
  the peer's own cap    12 model calls a task (services/agent/agent.py): a looping peer ends its task `failed`.

Every hand-off of the turn, sent or refused, is recorded in the turn's context (tools.REQUEST's "handoffs"), which
AdkBrain.answer() returns as the response's `handoffs`, and in one log line, {"event": "handoff", ...}, which joins the
chat row by tenant, user and time. The chat row keeps its keys: lesson 11.5 reads them. The line logs the question's
length, never its words, as the chat row logs tool names and never their arguments. The gcp profile only: the roster
and the peer are on Google Cloud.

The A2A client is a2a-sdk's own (services/chat/requirements.txt pins the version the peer's image runs, with no
extra), imported when a hand-off is sent: an image without it still starts, and only a hand-off fails.
"""
from __future__ import annotations

import asyncio
import functools
import json
import logging
import os
import time
import uuid

import limits
from shared import documind_tools, tenancy

logger = logging.getLogger("documind.chat.peer")

PEER_URL = os.environ.get("PEER_URL", "").rstrip("/")              # https://documind-agent-NUMBER.REGION.run.app
PEER_ACCOUNT = os.environ.get("PEER_ACCOUNT", "").strip().lower()  # documind-agent-sa@PROJECT.iam.gserviceaccount.com
PEER_TIMEOUT_S = float(os.environ.get("PEER_TIMEOUT_S", "75"))
HANDOFF_MAX_PER_TURN = 2
NAME = "documind_peer"
# The request's metadata (workshop lesson 10.7): the chain the question has come along, which starts at the one brain
# that hands off (brains.py's AdkBrain, its root agent named documind_adk), and the hand-off's id. The keys are the
# ones services/agent/chain.py reads; the peer imports nothing from the kit, so each side names them.
CHAIN_KEY, HANDOFF_KEY, ASKER = "documind_chain", "documind_handoff_id", "documind_adk"
# What the chat's model reads to choose the tool. The peer holds the MCP server's inventory tools, which the chat's
# own two (retrieve, calculate_processing_cost) do not; widen this and more questions cross the hop.
DESCRIPTION = ("Hand one question to DocuMind's A2A peer, an agent that reads this corpus through the DocuMind MCP "
               "server: which documents the corpus holds, how many there are, and the corpus's counts. Send the "
               "question in words, complete in itself; the answer comes back in words, with no passages to cite. "
               "For what a document says, search instead.")


def gate(tenant: str, peer_tenants: list, sent: int) -> str | None:
    """Why a hand-off may not be sent, or None. `sent` is how many this turn has already sent (or is sending), and
    `peer_tenants` the rosters the peer's account sits on. The words go to the model and the asker: no tenant named."""
    if sent >= HANDOFF_MAX_PER_TURN:
        return f"this turn has already handed {sent} questions to the peer, the most one turn may (HANDOFF_MAX_PER_TURN)"
    if list(peer_tenants) != [tenant]:
        return ("the peer reads the corpus as an account that is not on this tenant's roster alone, so its answer "
                "could come from another tenant's documents; it was not asked (a confused deputy)")
    return None


def budget_s(meter: limits.Meter) -> float:
    """How long a hand-off may wait: PEER_TIMEOUT_S, or the turn's time left when that is less, and never under the
    floor every tool call gets (limits.TOOL_FLOOR_S)."""
    return max(limits.TOOL_FLOOR_S, min(PEER_TIMEOUT_S, meter.left()))


async def _blocking(fn, *args):
    """A blocking call - the roster query, the token mint - in limits.TOOL_POOL, never asyncio.to_thread: asyncio.run()
    waits for that pool's threads before it returns (limits.py)."""
    return await asyncio.get_running_loop().run_in_executor(limits.TOOL_POOL, functools.partial(fn, *args))


async def _send(question: str, token: str, wait_s: float, handoff_id: str) -> dict:
    """One A2A message to the peer, with the chat's own ID token; the state the peer's task ended in, and its words.
    The card comes first, from PEER_URL/.well-known/agent-card.json, and names the JSON-RPC address to post to. The
    request's metadata holds the chain, this brain alone, and the hand-off's id; nothing personal."""
    import httpx
    from a2a.client import ClientConfig, create_client
    from a2a.types import Message, Part, Role, SendMessageRequest, TaskState

    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}, timeout=wait_s) as http:
        client = await create_client(PEER_URL, client_config=ClientConfig(httpx_client=http, streaming=False))
        message = Message(role=Role.ROLE_USER, message_id=str(uuid.uuid4()), parts=[Part(text=question)])
        request = SendMessageRequest(message=message, metadata={CHAIN_KEY: [ASKER], HANDOFF_KEY: handoff_id})
        items = [item async for item in client.send_message(request)]
    last = items[-1] if items else None
    if last is None or not last.HasField("task"):           # a bare message, which ADK's to_a2a does not send
        said = last.message.parts if last is not None and last.HasField("message") else []
        return {"state": "completed" if said else "unknown", "task_id": None, "text": " ".join(p.text for p in said)}
    task = last.task
    state = TaskState.Name(task.status.state).removeprefix("TASK_STATE_").lower()
    answer = "\n".join(p.text for a in task.artifacts for p in a.parts if p.text)
    status = " ".join(p.text for p in task.status.message.parts if p.text)
    return {"state": state, "task_id": task.id, "text": answer if state == "completed" else status or answer}


async def documind_peer(request: str) -> dict:
    from tools import REQUEST          # services/chat/tools.py, imported here so this module loads without LangChain

    ctx = REQUEST.get(None)
    if ctx is None:                                 # outside an ADK brain's turn: a ledger for this call alone
        ctx = {}
    records = ctx.setdefault("handoffs", [])
    # Counted and recorded before the first await, so calls the model makes side by side count each other.
    sent = sum(1 for r in records if r["outcome"] != "refused")
    record = {"n": len(records) + 1, "request": request, "outcome": "pending", "reason": None, "state": None,
              "task_id": None, "seconds": 0.0, "budget_s": None, "handoff_id": uuid.uuid4().hex}
    records.append(record)
    started, rosters = time.monotonic(), None
    try:
        peer_tenants = await _blocking(tenancy.tenants_of, PEER_ACCOUNT) if PEER_ACCOUNT else []
        rosters = len(peer_tenants)
        reason = gate(ctx.get("tenant_id", ""), peer_tenants, sent)
        if reason:
            record.update(outcome="refused", reason=reason)
            return {"error": reason, "status": "error"}       # a refusal, as a blocked tool's is: refusals names it
        meter = limits.meter_of(ctx)
        wait_s = budget_s(meter)
        token = await _blocking(documind_tools._id_token, PEER_URL)   # a mint that fails fails the turn (lesson 5.5)
        record.update(outcome="sent", budget_s=round(wait_s, 1))
        try:
            task = await asyncio.wait_for(_send(request, token, wait_s, record["handoff_id"]), wait_s)
        except Exception as exc:  # noqa: BLE001 - the peer's failure is data for the model, as a failed search is
            if isinstance(exc, TimeoutError) or limits.is_timeout(exc) or "Timeout" in type(exc).__name__:
                meter.tool_timed_out(NAME)
                record["outcome"] = "timed_out"
                return limits._payload_error(NAME, wait_s)
            record.update(outcome="error", reason=f"{type(exc).__name__}: {exc}"[:300])
            return {"error": f"the peer could not be asked ({type(exc).__name__})", "answerable": False}
        record.update(outcome="answered" if task["state"] == "completed" else "failed", state=task["state"],
                      task_id=task["task_id"])
        if task["state"] != "completed":
            return {"error": f"the peer's task ended {task['state']}: {task['text']}", "state": task["state"]}
        return {"answer": task["text"], "state": task["state"]}
    finally:
        record["seconds"] = round(time.monotonic() - started, 2)
        logger.info(json.dumps({"event": "handoff", "surface": "chat", "peer": NAME, "tenant": ctx.get("tenant_id"),
                                "user": ctx.get("user_id"), "brain": ctx.get("brain"), "n": record["n"],
                                "outcome": record["outcome"], "reason": record["reason"], "state": record["state"],
                                "task_id": record["task_id"], "seconds": record["seconds"],
                                "budget_s": record["budget_s"], "request_chars": len(request or ""),
                                "peer_account": PEER_ACCOUNT or None, "peer_rosters": rosters,
                                "handoff_id": record["handoff_id"]}))


documind_peer.__doc__ = DESCRIPTION


def tool():
    """The hand-off as an ADK tool. FunctionTool declares its name and its one argument, `request`, and reads its
    description from DESCRIPTION. It times itself (budget_s), so brains.py adds it without limits.timed_adk."""
    from google.adk.tools import FunctionTool
    return FunctionTool(documind_peer)
