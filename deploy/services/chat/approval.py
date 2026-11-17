"""DocuMind chat service - a person in the loop: pause, approve, clarify, offer a case (workshop lesson 5.8).

THE SERVICE REACHES THIS MODULE THROUGH ONE SWITCH, OFF UNTIL AN OPERATOR SETS IT. approval_routes.py imports it: for a
company whose tenant_settings.agent_actions is approval (make agent-actions), the LangGraph brain is
build_approval_graph() below, the pause is a record (shared/approvals.py) and the /v1/approvals routes end it. For
every other company, and for the other brains, the chat service is what it was: tools.BLOCKED and the LangGraph
brain's refuse node stay as workshop lessons 5.4, 5.5 and 5.7 show them. Offline it runs on scripted models
(commands/tests/test_approvals.py, make approval-check). Three tools bring a person into a turn:

    withdraw_document   an action with a side effect. The turn waits for a SECOND person in the company to approve
                        it, and the person who asked cannot approve their own request (four eyes). Withdrawn is not
                        deleted: make restore brings the document back. What withdraws is injected, the turn
                        context's "withdraw", so the tests withdraw nothing.
    ask_user            a clarifying question. The turn waits for the person who asked; their answer comes back as
                        the tool's result (a "respond" decision, LangChain's RespondDecision).
    offer_case          the case desk's hand-off (workshop lesson 5.6), offered by the model when a question belongs
                        to a person. It checks the person's roles and the type's queue, and writes nothing: the
                        person raises the case with the button, as after the chat door's own case_offer.

The pause, in two forms that take one decision format, {"decisions": [one per waiting call, in order]}:

    build_approval_graph()  the LangGraph brain's graph with an approve node in refuse's place: agent -> approve, where
                            interrupt() stops the turn and the checkpointer keeps it; a decision resumes it, approve ->
                            tools -> agent. A rejected call gets an error result and nothing else is held back: a
                            search asked for beside it still runs.
    hitl_middleware()       LangChain's HumanInTheLoopMiddleware for create_agent, configured the same. Its after_model
                            hook is a graph node of its own, so each model call writes one more checkpoint (why
                            limits.TurnLimitsMiddleware wraps the model call instead).

paused() reads what a paused turn waits for, in one shape from both forms. decide() is how a decision comes back: it
checks who may decide before anything runs, then resumes the turn with Command(resume=...). Its rules, which the
approve node and withdraw_document check again:

    approve   a second person, never the person who asked; when may_approve is given, it says who else may.
              roster_rule(db, role) is the kit's: on the roster of the conversation's own tenant, holding the role
    reject    the person who asked (their cancel), or a second person who may approve
    respond   the person who asked, and no one else

The person who asked is read from the thread id, tenant:user:session, which agent.thread_config() builds from the
verified caller: never from the model, a request body or the context a resume brings.

A resumed node runs again from its first line, so nothing above interrupt() may have a side effect. The approve
node's "approval asked" line sits below it and is written once; above it, it is written at the pause and again at
the resume (workshop lesson 5.8's Change-it), as an email or a ticket sent there would go out twice.

Verified offline on 8 October 2026 against langchain 1.4.0, langgraph 1.2.12 and langgraph-checkpoint-sqlite 3.1.1
(the local lane's pin, services/chat/requirements-local.txt): a second process sharing a SqliteSaver file resumes a
paused turn. Wired into the service behind the switch on 13 October 2026 (approval_routes.py, shared/approvals.py).
"""
from __future__ import annotations

import json
import logging
from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import ToolException, tool
from langgraph.types import Command, Send, interrupt

try:
    from langchain.tools import ToolRuntime          # langchain 1.x re-exports langgraph's
except ImportError:                                   # a bare langgraph install
    from langgraph.prebuilt.tool_node import ToolRuntime

from shared import cases, desk_law, roles

import limits                                         # services/chat/limits.py: the turn's Meter and its timed calls
from tools import TOOLS, _ctx                         # the kit's tools, and its one reader of a ToolRuntime's context

logger = logging.getLogger("documind.chat.approval")

NEEDS_APPROVAL = frozenset({"withdraw_document"})     # a second person in the company approves these
NEEDS_ANSWER = frozenset({"ask_user"})                 # the person who asked answers these
DECISIONS = {**{n: ("approve", "reject") for n in NEEDS_APPROVAL}, **{n: ("respond",) for n in NEEDS_ANSWER}}
NAME_MAX, REASON_MAX, ANSWER_MAX = 200, 200, 4000
CaseType = Literal["posh", "grievance", "privacy_request", "exit_dues", "people_query", "human_requested"]


def _key(email) -> str:
    return str(email or "").strip().lower()


def owner(config) -> tuple[str, str]:
    """The tenant and the person whose conversation this is, from its thread id, tenant:user:session: agent.py's
    thread_config() builds it from the verified caller, and a resume cannot change it."""
    thread = str(((config or {}).get("configurable") or {}).get("thread_id") or "")
    parts = thread.split(":")
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"{thread!r} is not a conversation's thread id (tenant:user:session)")
    return parts[0], _key(parts[1])


def normalize_name(name: str, tenant: str) -> str:
    """The document's bare name in this tenant, from a bare name, tenant/name or the upload URI gs://bucket/tenant/name.
    Another tenant's document, a '/', a backslash, '..' and a name over NAME_MAX characters are refused (ValueError)."""
    raw = str(name or "").strip()
    if raw.startswith("gs://"):
        raw = raw[len("gs://"):].partition("/")[2]
    if "/" in raw:
        head, _, raw = raw.partition("/")
        if head != tenant:
            raise ValueError(f"{name!r} is not one of {tenant}'s documents")
    if not raw or len(raw) > NAME_MAX or any(bad in raw for bad in ("/", "\\", "..")):
        raise ValueError(f"{name!r} is not a document's name: a file name of at most {NAME_MAX} characters")
    return raw


# ----------------------------------------------------------------------------- the three tools
@tool
def withdraw_document(name: str, runtime: ToolRuntime = None) -> dict:
    """Withdraw one of the company's documents from search, so that no answer cites it. A second person in the
    company must approve it first, and the turn waits for them: until this tool returns, say the withdrawal is
    waiting for approval, never that it is done. Nothing is deleted; the document can be brought back.

    Args:
        name: The document's file name, as its citations show it (for example hr_policy_2026.md)
    """
    # The last lock (uplift D1): this call runs only with a second person's approval of THIS call, which decide()
    # carries in the resumed turn's context. The tenant and the person who asked are the thread's, never the model's.
    try:
        tenant, asker = owner(getattr(runtime, "config", None))
        doc = normalize_name(name, tenant)
    except ValueError as exc:
        raise ToolException(str(exc)) from None
    approver = _key((_ctx(runtime, "approvals", None) or {}).get(getattr(runtime, "tool_call_id", None)))
    if not approver or approver == asker:
        raise ToolException("withdraw_document runs only after a second person in the company approves this call")
    withdraw = _ctx(runtime, "withdraw", None)
    if withdraw is None:
        raise ToolException("nothing here can withdraw a document, so nothing was withdrawn")
    done = withdraw(tenant=tenant, name=doc, requested_by=asker, approved_by=approver)
    return {**(done or {}), "document": f"{tenant}/{doc}", "undo": f"make restore SOURCE={tenant}/{doc}"}


@tool
def ask_user(question: str) -> str:
    """Ask the person one short question when their request cannot be answered without it: which document, which
    office, which month. Their reply comes back as this tool's result. Never use it to ask for an approval.

    Args:
        question: The one question, in the person's own language
    """
    # The person answers in this call's place (a respond decision), so this body runs only where nobody was asked.
    raise ToolException("nobody was asked: put the question in your answer instead")


@tool
def offer_case(case_type: CaseType, runtime: ToolRuntime = None) -> dict:
    """Offer the person a case that a person handles, for a question no document should answer: harassment at work
    (posh), a complaint about how they are treated (grievance), a request about their own personal data
    (privacy_request), dues unpaid after they left (exit_dues), a question for the People team (people_query), or a
    request to talk to a person (human_requested). Nothing is raised until the person presses the button and
    confirms, so never say that a case was opened.

    Args:
        case_type: The kind of case to offer
    """
    # Writes nothing (uplift D8). The person's roles must open the case desk (shared/roles.desks; a failed read is the
    # case desk only), and the type's queue must be configured, as GET /v1/cases/offer decides it (services/chat/
    # desk.py). There is no reason argument: what a person disclosed never reaches a case, a row or this result.
    try:
        tenant, person = owner(getattr(runtime, "config", None))
    except ValueError as exc:
        raise ToolException(str(exc)) from None
    if "case" not in roles.desks(roles.roles_for(_ctx(runtime, "db", None), tenant, person)):
        raise ToolException("this person's roles do not include raising a case: say who to contact instead")
    queues = _ctx(runtime, "case_queues", None) or {}
    queue = None if case_type == "posh" else cases.queue_for(case_type, queues)
    if cases.posh_errors(queues) if case_type == "posh" else queue is None:
        raise ToolException(f"this company has no queue for a {case_type} case: say who to contact instead")
    offer = {"case_type": case_type}                  # the chat door's case_offer: the same key and shape
    offers = _ctx(runtime, "offers", None)
    if isinstance(offers, list):
        offers.append(offer)
    return {"case_offer": offer,
            "handled_by": "the Internal Committee" if case_type == "posh" else desk_law.QUEUES[queue]["name"],
            "note": "Nothing is raised until the person presses Raise a case and confirms."}


for _t in (withdraw_document, ask_user, offer_case):
    _t.handle_tool_error = True                       # a ToolException is an error result the model reads
PERSON_TOOLS = [withdraw_document, ask_user, offer_case]


# ----------------------------------------------------------------------------- the pause, and who may end it
def _describe(call: dict, state=None, runtime=None) -> str:
    """What the person deciding reads (HumanInTheLoopMiddleware calls it with the state and runtime as well)."""
    if call["name"] in NEEDS_ANSWER:
        return str(call["args"].get("question", ""))
    return (f"{call['name']} {json.dumps(call['args'], ensure_ascii=False)}, asked for in this conversation. A second "
            "person in the company must approve it; make restore undoes a withdrawal.")


def _pending(messages) -> list[dict]:
    """The last model message's calls that have no result yet."""
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], AIMessage):
            done = {m.tool_call_id for m in messages[i + 1:] if isinstance(m, ToolMessage)}
            return [c for c in messages[i].tool_calls if c["id"] not in done]
    return []


def _request(calls: list[dict]) -> dict:
    """The pause's payload in HumanInTheLoopMiddleware's own shape (its HITLRequest), so both forms ask alike."""
    return {"action_requests": [{"name": c["name"], "args": c["args"], "description": _describe(c)} for c in calls],
            "review_configs": [{"action_name": c["name"], "allowed_decisions": list(DECISIONS[c["name"]])}
                               for c in calls]}


def _asks(calls: list[dict], request: dict, config) -> list[dict]:
    """paused()'s items: each waiting call beside what the pause asked about it."""
    tenant, asker = owner(config)
    return [{"tool": c["name"], "args": c["args"], "call_id": c["id"],
             "allowed_decisions": list(r["allowed_decisions"]), "description": a.get("description", ""),
             "tenant": tenant, "requester": asker}
            for c, a, r in zip(calls, request["action_requests"], request["review_configs"])]


def _check(ask: dict, decision, by, may_approve=None) -> tuple[type, str] | None:
    """Why this person may not make this decision on this call, as (the exception decide() raises, the reason); None
    when they may."""
    kind = decision.get("type") if isinstance(decision, dict) else None
    if kind not in ask["allowed_decisions"]:
        return ValueError, f"{ask['tool']} takes {' or '.join(ask['allowed_decisions'])}, not {kind!r}"
    text, most = decision.get("message", ""), ANSWER_MAX if kind == "respond" else REASON_MAX
    if not isinstance(text, str) or len(text) > most or (kind == "respond" and not text.strip()):
        return ValueError, f"a {kind} message is text of at most {most} characters, and an answer is not empty"
    who, asker = _key(by), ask["requester"]
    if not who:
        return PermissionError, "a decision names the verified person who makes it"
    if kind == "respond":
        return None if who == asker else (PermissionError, "only the person who asked may answer their own question")
    if kind == "approve" and who == asker:
        return PermissionError, "the person who asked cannot approve their own request: a second person must"
    if who != asker and may_approve is not None and not may_approve(ask["tenant"], who):
        return PermissionError, f"{who} may not decide {ask['tool']} requests in this company"
    return None


def _refusals(asks: list[dict], answer) -> list[str]:
    """The approve node's own check of a resume value, by decide()'s rules but without may_approve (a node does not
    look roles up). Empty when every decision stands."""
    decisions = answer.get("decisions") if isinstance(answer, dict) else None
    if not isinstance(decisions, list) or len(decisions) != len(asks):
        return [f"{len(asks)} decision(s) are needed, one for each waiting call, in order"]
    return [refused[1] for ask, d in zip(asks, decisions) if (refused := _check(ask, d, answer.get("by")))]


def roster_rule(db, role: str):
    """A may_approve for decide(), read from the tenant's roster (13 October 2026): who besides the person who asked may
    approve or reject a call. They must be on the roster of the conversation's own tenant, the same company (a person
    on another tenant's roster, or on none, is refused), and hold `role` there, a role make roles grants
    (shared/roles.valid(), read by roles_for(), the one reader). Each refusal raises PermissionError with its reason, so
    decide() refuses before anything runs and the turn stays paused. A roster that cannot be read refuses everyone.

        decide(agent, config, decisions, by=caller_email, may_approve=roster_rule(db, "people_ops"))

    The service's routes pass roster_rule(db, "doc_approver"), the role shared/roles.py holds for it (approval_routes.py,
    13 October 2026); a caller may name any role make roles grants, and "employee" lets every member without a role
    document decide."""
    if not isinstance(role, str) or not roles.valid(role):
        raise ValueError(f"{role!r} is not a role make roles grants: one of {list(roles.ROLES + roles.RESERVED)} or "
                         "ic_member:<unit>")

    def may_approve(tenant: str, email: str) -> bool:
        held = roles.roles_for(db, tenant, email)
        if roles.UNREAD in held:
            raise PermissionError(f"{tenant}'s roster could not be read, so no decision can be checked: try again")
        if not held:
            raise PermissionError(f"{email} is not on {tenant}'s roster: only a person in this company may decide its "
                                  "requests")
        if role not in held:
            raise PermissionError(f"{email} does not hold {role} in {tenant}, the role that may approve or reject these "
                                  "requests (make roles grants it)")
        return True
    return may_approve


def paused(agent, config: dict) -> list[dict]:
    """What a paused turn waits for, one item per call: the tool, its arguments and call id, the decisions it takes,
    what the person deciding reads, the tenant and who asked. [] when the turn is not paused. One shape from
    build_approval_graph() and from an agent built with hitl_middleware()."""
    snap = agent.get_state(config)
    if not snap.interrupts:
        return []
    request = snap.interrupts[0].value
    calls = [c for c in _pending(snap.values.get("messages", [])) if c["name"] in DECISIONS]
    if [c["name"] for c in calls] != [a["name"] for a in request.get("action_requests", [])]:
        raise RuntimeError("this pause does not match the conversation's waiting calls")
    return _asks(calls, request, config)


def decide(agent, config: dict, decisions: list[dict], *, by: str, context: dict | None = None,
           may_approve=None) -> dict:
    """Resume a paused turn with one decision per waiting call, in paused()'s order: {"type": "approve"},
    {"type": "reject", "message": a reason} or {"type": "respond", "message": the answer}. `by` is the verified person
    deciding (a route reads it from caller(), never from the body). Refused before anything runs, so the turn stays
    paused: no pause (LookupError, a route's 409), a wrong count or kind of decision (ValueError, 422), a person the
    rules do not allow (PermissionError, 403). The resumed turn runs for the person who asked: its context's
    tenant_id and user_id are the thread's, and its approvals name who approved each call."""
    asks = paused(agent, config)
    if not asks:
        raise LookupError("this conversation is not waiting for anyone")
    if not isinstance(decisions, list) or len(decisions) != len(asks):
        raise ValueError(f"{len(asks)} decision(s) are needed, one for each waiting call, in order")
    for ask, decision in zip(asks, decisions):
        refused = _check(ask, decision, by, may_approve)
        if refused:
            raise refused[0](refused[1])
    tenant, asker = owner(config)
    approvals = {a["call_id"]: _key(by) for a, d in zip(asks, decisions) if d["type"] == "approve"}
    ctx = {**(context or {}), "tenant_id": tenant, "user_id": asker, "approvals": approvals}
    return agent.invoke(Command(resume={"decisions": decisions, "by": _key(by)}),
                        config={**config, "recursion_limit": limits.recursion_limit()}, context=ctx)


# ----------------------------------------------------------------------------- the two forms
def build_approval_graph(llm=None, checkpointer=None, *, system: str | None = None):
    """The LangGraph brain's graph (services/chat/brains.py), with an approve node where its refuse node is:

        agent -> approve -> the pause (__interrupt__); then, on a decision: approve -> tools -> agent

    A turn with nothing to pause for runs as the brain's does, agent -> tools -> agent. The model is bound to the
    kit's TOOLS and PERSON_TOOLS, and each call runs within its budget (limits.timed_tool_call)."""
    from langgraph.graph import END, START, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode

    if system is None:
        from brains import SYSTEM as system          # imported here, so that brains.py may import this module
    if llm is None:
        from shared.profile import build_llm
        llm = build_llm()
    model = llm.bind_tools(TOOLS + PERSON_TOOLS)

    def agent(state, runtime):
        # The brain's own agent node: the Meter before the call, the call's timeout, a timed-out call as the stop.
        meter = limits.meter_of(runtime.context)
        if not meter.allow_model_call():
            return {"messages": [limits.stop_message()]}
        try:
            msg = model.invoke([SystemMessage(content=system)] + state["messages"], **limits.call_settings(meter))
        except Exception as exc:                       # noqa: BLE001 - only a timeout is caught
            if not limits.is_timeout(exc):
                raise
            meter.stop("turn_deadline")
            return {"messages": [limits.stop_message()]}
        meter.charge_model(*limits.usage_of(msg))
        return {"messages": [msg]}

    def route(state):
        calls = _pending(state["messages"])
        if not calls:
            return END
        return "approve" if any(c["name"] in DECISIONS for c in calls) else "tools"

    def approve(state, config):
        """Pause for the person each waiting call needs, then hand on only what they let through."""
        calls = [c for c in _pending(state["messages"]) if c["name"] in DECISIONS]
        request = {**_request(calls), "call_ids": [c["id"] for c in calls], "requester": owner(config)[1]}
        asks = _asks(calls, request, config)
        answer = interrupt(request)                   # the turn stops here; a resume runs this node again from the top
        while refused := _refusals(asks, answer):     # the node's own lock: decide() has checked the same rules
            answer = interrupt({**request, "refused": refused})
        logger.info("approval asked: %s", ", ".join(a["name"] for a in request["action_requests"]))
        out = []
        for call, decision in zip(calls, answer["decisions"]):
            if decision["type"] == "reject":
                who = ("cancelled by the person who asked for it" if _key(answer["by"]) == request["requester"]
                       else "rejected by a second person")
                out.append(ToolMessage(content=json.dumps({"error": f"{call['name']} was {who}, so nothing was done",
                                                           "their_reason": decision.get("message", "")}),
                                       name=call["name"], tool_call_id=call["id"], status="error"))
            elif decision["type"] == "respond":
                out.append(ToolMessage(content=decision["message"], name=call["name"], tool_call_id=call["id"]))
        return {"messages": out}

    def onward(state):
        calls = _pending(state["messages"])           # the approved calls, and any asked for beside them
        return [Send("tools", [c]) for c in calls] if calls else "agent"

    g = StateGraph(MessagesState, context_schema=dict)
    g.add_node("agent", agent)
    g.add_node("approve", approve)
    g.add_node("tools", ToolNode(TOOLS + PERSON_TOOLS, wrap_tool_call=limits.timed_tool_call))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route, ["approve", "tools", END])
    g.add_conditional_edges("approve", onward, ["tools", "agent"])
    g.add_edge("tools", "agent")
    return g.compile(checkpointer=checkpointer)


def hitl_middleware():
    """The same pause for create_agent: HumanInTheLoopMiddleware (langchain 1.4.0) with DECISIONS' tools and what
    _describe says. Bind TOOLS + PERSON_TOOLS beside it, and put it first in the list (uplift D1); the call cap and
    the guard keep their own order after it. Its after_model hook is a node, so an agent built with it writes one
    more checkpoint for each model call than the LangChain brain does."""
    from langchain.agents.middleware import HumanInTheLoopMiddleware

    return HumanInTheLoopMiddleware(interrupt_on={name: {"allowed_decisions": list(allowed), "description": _describe}
                                                  for name, allowed in DECISIONS.items()})
