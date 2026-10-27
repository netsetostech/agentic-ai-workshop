"""The approval wired into the chat service (workshop lesson 5.8), behind a company switch that is off until an
operator sets it: tenant_settings/{tenant}.agent_actions = approval (make agent-actions).

Off, or for any brain but langgraph, nothing here runs: agent.chat()'s one call, wired(), gives back the brain it was
given, and the LangGraph brain is what lessons 5.4, 5.5 and 5.7 show, refuse node and all. On, for that company:

    the brain      services/chat/approval.build_approval_graph() on the service's own checkpointer and model, in the
                   LangGraph brain's place: agent -> approve -> the pause. The turn's answer says that it waits, and
                   the response carries `approval`, the record (shared/approvals.py), whose id names the pause.
    the hold       a conversation that waits takes no new question: 409 with the record's id, because a new message
                   on a paused thread would drop the pause. Once the record has expired, the hold ends the pause as
                   the person who asked would, a reject with the reason through decide(): the approve node writes
                   each waiting call's error result, the model answers that turn, and the new question runs.
    the routes     GET  /v1/approvals                what the person asked for; for a doc_approver, the company's
                                                     pending withdrawals as well
                   GET  /v1/approvals/{id}           one record: 404 unless the reader may read it
                   POST /v1/approvals/{id}/decide    {"decisions": [one per waiting call, in order]}. 404; 410 when
                                                     the record expired; 409 when it is already decided, or the turn
                                                     no longer waits; 403 for the person who asked approving their
                                                     own request, and for a second person not on this company's
                                                     roster or without doc_approver (approval.roster_rule); 422 for
                                                     the wrong kind or count of decision. Then approval.decide()
                                                     resumes the turn for the person who asked, with its own Meter,
                                                     and the record says what became of it.

Every route takes the person from delegation.principal(), as the case routes do, and the tenant from the roster. The
records live in Firestore, so on the local profile the routes answer 501 and the switch is never read. An approved
withdrawal withdraws nothing here: the record carries it, and the operator runs make withdraw-run. The resumed turn
logs a chat row of agent.chat()'s shape, surface "approval", naming the record and who decided.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.convertors import Convertor, register_url_convertor

import approval
import brains
import delegation
import desk
import limits
from shared import approvals, roles
from shared.profile import LOCAL_MODEL, PROFILE

log = logging.getLogger("documind.chat.approval_routes")

SWITCH, ON = "agent_actions", "approval"           # tenant_settings/{tenant}.agent_actions: approval, else off
WIRED_BRAIN = "langgraph"                           # the one brain the switch changes
_hooks: dict = {}


class ApprovalId(Convertor):
    regex = "[0-9a-f]{32}"

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: str) -> str:
        return value


register_url_convertor("approval_id", ApprovalId())
router = APIRouter()


# ---------------------------------------------------------------- the switch, the brain, the hold
def switched_on(tenant: str) -> bool:
    """tenant_settings/{tenant}.agent_actions == approval, read as the Desk reads its switches (desk.settings, once a
    minute per tenant). Never on the local profile, and a read that fails counts as off, with a warning row."""
    if PROFILE == "local":
        return False
    try:
        return (desk.settings(tenant) or {}).get(SWITCH) == ON
    except Exception as e:  # noqa: BLE001 - off for want of a read: the brain the company had
        log.warning(json.dumps({"event": "agent_actions_unread", "surface": "chat", "tenant": tenant,
                                "error": type(e).__name__}))
        return False


def _db():
    """The Desk's one Firestore client (desk.py), so what stands it in for a test stands this in too."""
    if PROFILE == "local":
        raise HTTPException(501, "approval records live in Firestore: run the chat service on the gcp profile")
    return desk._client()


class ApprovalBrain:
    """The LangGraph brain with approval.py's approve node in the refuse node's place, on the service's checkpointer:
    the same answer shape as brains.LangGraphBrain, plus `paused` when the turn stopped for a person."""

    name = WIRED_BRAIN

    def __init__(self, checkpointer, llm=None):
        self.graph = approval.build_approval_graph(llm, checkpointer)

    def answer(self, question: str, *, config: dict, context: dict) -> dict:
        from langgraph.errors import GraphRecursionError

        turn, state, ctx = brains._turn(question, context)
        try:
            out = self.graph.invoke(state, config={**config, "recursion_limit": limits.recursion_limit()}, context=ctx)
        except GraphRecursionError:         # the backstop tripped before the Meter: end the turn whole
            limits.meter_of(ctx).stop("recursion_limit")
            limits.repair_thread(self.graph, config, as_node="agent")
            out = self.graph.get_state(config).values
        return {**brains._summary(out["messages"], turn, ctx["cited"]), "paused": "__interrupt__" in out}


def _brain(app) -> ApprovalBrain:
    """Built once per process, on first use, as brain_for() builds the four brains."""
    b = getattr(app.state, "approval_brain", None)
    if b is None:
        try:
            b = ApprovalBrain(app.state.checkpointer)
        except ImportError as exc:
            raise HTTPException(501, f"the approval graph is not installed in this image: {exc.name}")
        app.state.approval_brain = b
    return b


def _record(graph, db, config: dict, tenant: str, email: str, session_id: str) -> dict:
    """The pause's record, opened or found: its id is the thread and the checkpoint the pause is kept in."""
    snap = graph.get_state(config)
    waiting = approval.paused(graph, config)
    rid = approvals.approval_id(config["configurable"]["thread_id"], str(snap.config["configurable"].get("checkpoint_id")))
    return approvals.open_request(db, rid, tenant, email, session_id, config["configurable"]["thread_id"], WIRED_BRAIN, waiting)


def _context(db, tenant: str, approval_id: str | None = None) -> dict:
    """A resumed turn's context: its own Meter, the person tools' needs, and the executor when a record may be approved.
    The thread's tenant and person are decide()'s to set."""
    return {"assertion": "", "brain": WIRED_BRAIN, "meter": limits.Meter(model=LOCAL_MODEL if PROFILE == "local" else brains.MODEL),
            "cited": [], "db": db, "case_queues": _queues(tenant), "offers": [],
            "withdraw": approvals.executor(db, approval_id) if approval_id else None}


def _summary(out: dict, ctx: dict) -> dict:
    """The resumed turn's answer, tool calls, refusals and citations: the turn is the thread's last question."""
    from langchain_core.messages import HumanMessage
    msgs = out["messages"]
    turn = next((m.id for m in reversed(msgs) if isinstance(m, HumanMessage)), None)
    return brains._summary(msgs, turn, ctx["cited"])


def _row(rec: dict, by: str, status: str, summary: dict, meter, latency_ms: int) -> None:
    """The resumed turn's row, in agent.chat()'s shape (workshop lessons 5.1, 5.5, 5.7 and 11.5 parse that one), with
    surface "approval": the person is the one who asked, and the record, who decided and the outcome are named beside."""
    used = meter.row()
    log.info(json.dumps({"event": "chat", "surface": "approval", "brain": WIRED_BRAIN,
                         "tenant": rec["tenant"], "user": rec["requester"],
                         "session_id": rec["session_id"], "latency_ms": latency_ms,
                         "tool_calls": summary["tool_calls"], "refusals": summary["refusals"],
                         "model": used["model"], "model_calls": used["model_calls"],
                         "tokens_in": used["tokens_in"], "tokens_out": used["tokens_out"],
                         "cached_tokens": used["cached_tokens"], "cost_usd": used["cost_usd"],
                         "rag_cost_usd": used["rag_cost_usd"], "stopped_by": used["stopped_by"],
                         "tool_timeouts": used["tool_timeouts"], "max_model_calls": used["max_model_calls"],
                         "budget_inr": used["budget_inr"], "approval": rec["approval_id"], "decided_by": by,
                         "status": status}))


def _end_pause(graph, config: dict, rec: dict, db, why: str) -> None:
    """A pause nobody can decide any more is ended as the person who asked would end it: a reject with the reason
    (an answer saying so, for a question), through decide(). The approve node writes each waiting call's error
    result itself, the model answers that turn, and the thread is whole for the next question. Nothing here writes
    the thread's state from outside the graph: limits.repair_thread is the kit's one such writer (workshop lesson 6.8)."""
    decisions = [{"type": "respond", "message": f"(no answer: {why})"} if w["tool"] in approval.NEEDS_ANSWER
                 else {"type": "reject", "message": why} for w in rec.get("waiting") or []]
    ctx = _context(db, rec["tenant"])
    t0 = time.monotonic()
    out = approval.decide(graph, config, decisions, by=rec["requester"], context=ctx)
    _row(rec, rec["requester"], rec["status"], _summary(out, ctx), ctx["meter"], int((time.monotonic() - t0) * 1000))


class Wired:
    """The approval brain for one company's turn: the context the person tools read, the record when the turn pauses,
    and case_offer when the model offered a case (offer_case writes nothing; the person raises it, as after the
    chat door's own offer)."""

    name = WIRED_BRAIN

    def __init__(self, brain: ApprovalBrain, db, tenant: str, email: str, session_id: str):
        self.brain, self.db, self.tenant, self.email, self.session_id = brain, db, tenant, email, session_id

    def answer(self, question: str, *, config: dict, context: dict) -> dict:
        ctx = {**context, "db": self.db, "case_queues": _queues(self.tenant), "offers": []}
        out = self.brain.answer(question, config=config, context=ctx)
        if out.pop("paused", False):
            rec = _record(self.brain.graph, self.db, config, self.tenant, self.email, self.session_id)
            out["approval"] = approvals.view(rec)
            out["answer"] = waiting_text(out["approval"])
        if ctx["offers"]:
            out["case_offer"] = ctx["offers"][0]
        return out


def waiting_text(view: dict) -> str:
    """The fixed answer of a turn that waits, from the record's view: what waits, who decides, and the id; never the
    model's words."""
    tools_ = ", ".join(w["tool"] for w in view["waiting"])
    if view["kind"] == "answer":
        q = next((w["args"].get("question", "") for w in view["waiting"] if w["tool"] == "ask_user"), "")
        return (f"DocuMind needs one fact from you before it can answer: {q} This conversation waits for your reply "
                f"(approval {view['approval_id']}, a respond decision at {view['decide']}) until {view['expire_at']}.")
    return (f"This conversation is waiting for a second person: {tools_} needs the approval of someone in your company "
            f"who holds {approvals.APPROVER}, and you cannot approve your own request. Approval {view['approval_id']} "
            f"({view['decide']}) waits until {view['expire_at']}; nothing has been withdrawn, and this conversation "
            "takes no new question until it is decided.")


def wired(app, name: str, brain, tenant: str, email: str, session_id: str):
    """agent.chat()'s one call. The brain it was given, unless this company's agent_actions is approval and the
    turn asked for the LangGraph brain: then the approval brain, after the hold - 409 while the conversation waits
    for a decision that can still be made."""
    if name != WIRED_BRAIN or not switched_on(tenant):
        return brain
    db, ab = _db(), _brain(app)
    config = _hooks["thread_config"](tenant, email, session_id)
    if approval.paused(ab.graph, config):
        rec = _record(ab.graph, db, config, tenant, email, session_id)
        if rec["status"] == "pending" and not approvals.expired(rec):
            raise HTTPException(409, f"this conversation is waiting for a decision on approval {rec['approval_id']} "
                                     f"({', '.join(w['tool'] for w in rec['waiting'])}): {approvals.who_decides(rec)}, "
                                     f"at POST /v1/approvals/{rec['approval_id']}/decide. GET /v1/approvals lists it. A new "
                                     "question would drop the pause, so none is taken until then.")
        rec = approvals.expire(db, rec)                  # pending and past expire_at: marked, as the decision route marks it
        _end_pause(ab.graph, config, rec, db, f"the approval expired before a decision came (approval {rec['approval_id']} "
                                              f"is {rec['status']}), so nothing was done")
    return Wired(ab, db, tenant, email, session_id)


# ---------------------------------------------------------------- the routes
class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["approve", "reject", "respond"]
    message: str = Field(default="", max_length=approval.ANSWER_MAX)


class Decisions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decisions: list[Decision] = Field(min_length=1, max_length=8)


def _who(request: Request) -> dict:
    """The verified person and their tenant, as the case routes read them (delegation.principal)."""
    p = dict(delegation.principal(request, _hooks["caller"], _hooks["tenant_for"], desk.settings))
    p["email"] = str(p.get("email") or "").lower()
    tenant = os.environ.get("LOCAL_TENANT", "acme") if PROFILE == "local" else _hooks["tenant_for"](p["email"])
    if tenant is None:
        raise HTTPException(403, desk.NOT_A_MEMBER)
    return {**p, "tenant": tenant}


def _queues(tenant: str) -> dict:
    try:
        return (desk.settings(tenant) or {}).get("case_queues") or {}
    except Exception:  # noqa: BLE001 - offer_case then finds no queue and says who to contact instead
        return {}


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except approvals.ApprovalError as e:
        raise HTTPException(e.status, e.detail)


def _reader(db, who: dict) -> tuple[dict, bool]:
    """The record the person may read, and whether they read as a doc_approver."""
    held = roles.roles_for(db, who["tenant"], who["email"])
    return held, approvals.APPROVER in held


@router.get("/v1/approvals")
def list_approvals(request: Request) -> dict:
    who = _who(request)
    db = _db()
    _, approver = _reader(db, who)
    return approvals.list_for(db, who["tenant"], who["email"], approver=approver)


@router.get("/v1/approvals/{approval_id:approval_id}")
def get_approval(approval_id: str, request: Request) -> dict:
    who = _who(request)
    db = _db()
    _, approver = _reader(db, who)
    rec = _call(approvals.read, db, approval_id, who["tenant"], who["email"], approver=approver)
    return approvals.view(approvals.expire(db, rec))


@router.post("/v1/approvals/{approval_id:approval_id}/decide")
def decide_approval(approval_id: str, body: Decisions, request: Request) -> dict:
    from langchain_core.messages import ToolMessage
    from langgraph.errors import GraphRecursionError

    who = _who(request)
    db = _db()
    _, approver = _reader(db, who)
    rec = _call(approvals.read, db, approval_id, who["tenant"], who["email"], approver=approver)
    rec = _call(approvals.decidable, db, rec)
    ab = _brain(request.app)
    config = _hooks["thread_config"](rec["tenant"], rec["requester"], rec["session_id"])
    # The resumed turn runs for the person who asked (decide() sets the thread's tenant and user in the context),
    # under its own limits, with the person tools' context and the executor that records an approved withdrawal.
    ctx = _context(db, rec["tenant"], approval_id)
    meter = ctx["meter"]
    decisions = [d.model_dump() for d in body.decisions]
    t0 = time.monotonic()
    try:
        out = approval.decide(ab.graph, config, decisions, by=who["email"], context=ctx,
                              may_approve=approval.roster_rule(db, approvals.APPROVER))
    except LookupError as e:                 # the turn no longer waits: the record says lost
        approvals.lost(db, rec)
        raise HTTPException(409, f"approval {approval_id} cannot be decided: {e} (its record is now lost)")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    except GraphRecursionError:              # the backstop tripped before the Meter: end the turn whole
        meter.stop("recursion_limit")
        limits.repair_thread(ab.graph, config, as_node="agent")
        out = ab.graph.get_state(config).values
    summary = _summary(out, ctx)
    answered = {m.tool_call_id: m for m in out["messages"] if isinstance(m, ToolMessage)}
    results = [{"call_id": w["call_id"], "tool": w["tool"],
                "status": getattr(answered.get(w["call_id"]), "status", None),
                "content": str(getattr(answered.get(w["call_id"]), "content", ""))[:2000]} for w in rec["waiting"]]
    rec = approvals.settle(db, rec, decisions, who["email"], results,
                           {k: summary[k] for k in ("answer", "tool_calls", "refusals")})
    latency_ms = int((time.monotonic() - t0) * 1000)
    _row(rec, who["email"], rec["status"], summary, meter, latency_ms)
    turn_out = {**summary, "brain": WIRED_BRAIN, "session_id": rec["session_id"], "latency_ms": latency_ms,
                "limits": meter.summary()}
    if ctx["offers"]:
        turn_out["case_offer"] = ctx["offers"][0]
    return {"approval": approvals.view(rec), "turn": turn_out}


def install(app, caller, tenant_for, thread_config) -> None:
    """Mount the approval routes. caller(request) is agent.py's identity (401 when it cannot say who), tenant_for(email)
    the roster's answer (None is a 403), thread_config the checkpointer's thread id, which the hold and a decision
    build for the person who asked. The chat door (desk.install) stays in front of POST /v1/chat; these routes are
    not behind it."""
    _hooks.update(caller=caller, tenant_for=tenant_for, thread_config=thread_config)
    app.include_router(router)
