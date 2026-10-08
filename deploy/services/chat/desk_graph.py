"""The DocuMind Desk's graph (workshop lesson 10.4): the desks a decided turn runs, as a LangGraph StateGraph.

    dispatch    reads the decision the handler passes in (services/chat/desk_router.decide()), calls no model, and
                goes to the turn's first desk with Command(goto=...)
    handbook    one rag-api answer over [policy]: documind_tools.retrieve(..., doc_type=["policy"], brain="desk"),
                and the company's note on each clause it cites that has one (tenant_settings clause_notes)
    statute     one rag-api answer over [statute, guidance], and the in-force note of shared/desk_law.py for every
                instrument it cites, closing with "Legal information, not advice."
    fallback    the router failed: one answer over every doc type the person may read (with the in-force note when it
                cites the law)
    astar       the eval's arm A* (a desk_eval caller's arm "Astar" only): one agent over the doc types the person may
                read, with every calculator (desk_agent.py)
    clarify     one question back, with a button for each of the two likeliest desks
    case, oos   the case desk and out_of_scope, by code (case_reply, oos_reply below)
    next_part   pops the turn's fixed list of parts: the next desk, or END. A second part starts only while the turn
                has PART_MIN_S left; otherwise it is offered as a chip. Parts run one after the other, never as
                Command(goto=[a, b]), which would run both in one superstep

The parts list is fixed by the router and only popped here: no tool names a desk, none can hand the turn to another.
A direct desk has no tool and no loop. When the router says a figure is asked (decision needs_calculation), the
handbook or statute desk runs in agent mode instead (desk_agent.py): a create_agent loop over a passages-backed
retrieve held to the desk's doc types and the desk's calculators (shared/desk_calc.py), under the turn's limits - the
same Meter, its model-call and rupee caps and its deadline. A desk that cannot answer (a grounded refusal) is not
re-routed: its section carries a chip to the other desk - a new turn the person chooses - and a case offer.

Code numbers the turn's citations across its sections (n = 1, 2, ...). Each section keeps rag-api's own answer text;
the [N] markers inside it are rag-api's numbers for that section's own context, which a citation does not carry, so
they are left as written: in a two-part turn the second section's [1] sits beside the citation numbered after the
first section's. A page shows citations by section. desk_max_parts is 1 unless an operator sets 2.

CHECKPOINTS. The thread is tenant:user:desk~<session>, through agent.py's thread_config rule (thread() below), in the
service's own checkpointer. "~" is a character /v1/chat's session_id pattern refuses, so no chat session can name a
Desk thread, and thread_config still refuses ":". Only answer, clarify and fallback turns invoke the graph (run_turn),
so only they write a checkpoint: a gate hit, a case, an out_of_scope, a denied or a not_covered turn is answered by
code and never checkpointed. The state keeps the masked question, never the person's own text: decide() masks before
anything else, and a gate hit keeps no text at all. The decision is checkpointed with L1's sensitive case_type
scrubbed as record() scrubs it. previous() reads the last turn back for the router's sticky and clarify checks.

THE CASE DESK opens a case only through shared/cases.py: draft() for every type with a draft, its source (rule,
model, desk), route_trace (desk_router.record(), with no question and a sensitive type shown as "sensitive"),
route_tried and partial_answer_citations; and for POSH no write at all - the reply is the fixed text and the card the
person presses (POST /v1/cases with the unit, the members chosen and a client token, which calls open_posh()). A
grievance or privacy draft starts with an empty summary; the others start with the masked question, for the person to
edit (a gate hit's start empty: the gate keeps no text). Only a person whose roles open the case desk gets a draft.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.errors import GraphBubbleUp
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.runtime import Runtime
from langgraph.types import Command

import desk_agent
import desk_router
import limits
from desk_routes import ANSWER_DESKS, DESKS, doc_types, fallback_doc_types
from shared import cases, desk_law, desk_rules, documind_tools, roles

log = logging.getLogger("documind.chat.desk_graph")

GRAPH_ROUTES = ("handbook", "statute", "clarify", "fallback")      # the turns that invoke the graph
PART_MIN_S = 30.0       # starting value: rag-api's p95 plus one model call, until the lane measures them
TITLES = {"handbook": "From the company handbook", "statute": "What the law says",
          "fallback": "From the documents you can read", "astar": "From the documents you can read"}
SOURCES = {"rule": "rule", "model": "model", "arbiter": "model", "user": "desk"}     # cases.SOURCES, by method
STARTS_WITH_QUESTION = ("exit_dues", "people_query", "human_requested")
CASE_TEXT = ("This needs a person. DocuMind has drafted a case for the People team: read it, edit it, and confirm "
             "it or cancel it.")
NO_DRAFT = {"roles": "This needs a person. Your roles in this company do not include raising a case, so DocuMind has "
                     "not drafted one.",
            "error": "This needs a person, but DocuMind could not draft the case just now. You can raise one under "
                     "Raise a case."}
DRAFT_OPEN = "You have a case draft open. Confirm it or cancel it first; DocuMind has not read this question further."
OOS = {
    "action": "DocuMind cannot do things in other systems, such as applying for leave or approving a claim: do it in "
              "the company's HR system.",
    "own_record": "DocuMind cannot see your own HR record, such as your leave balance or payslip: look in the "
                  "company's HR system.",
    None: "This is outside what DocuMind's desks answer: it is not in the company handbook or in the law DocuMind "
          "holds.",
}
MASKED = {"aadhaar": "an Aadhaar number", "card": "a card number"}
CLAUSE_CODE = re.compile(r"^[A-Z][A-Z0-9]{0,7}(?:-[A-Z0-9]{1,6}){1,2}$")   # a handbook section's code: NP-03, IT-SEC-04
NOTE_MAX = 800


class DeskState(TypedDict, total=False):
    messages: Annotated[list, add_messages]     # the masked question and the reply
    decision: dict                              # this turn's, from the handler
    parts: list                                 # the desks still to run this turn
    sections: list
    offered_chips: list
    last_route: str | None
    last_question: str | None                   # masked, 300 characters at most
    last_at: float | None
    clarified: bool                             # the last turn was a clarify (the router's cap)
    case_draft_id: str | None                   # the open draft, when the handler records one


SESSION_PREFIX = "desk~"     # "~" is outside /v1/chat's session_id pattern ([A-Za-z0-9_-]), so the two never collide


def thread(thread_config, tenant: str, user: str, session: str) -> dict:
    """The Desk's checkpoint thread, tenant:user:desk~<session>, by agent.py's thread_config rule."""
    return thread_config(tenant, user, SESSION_PREFIX + session)


def previous(graph, config: dict) -> dict:
    """The thread's last turn, for decide()'s ctx: prev_route, prev_question (masked), prev_at, prev_clarified."""
    values = graph.get_state(config).values or {}
    return {"prev_route": values.get("last_route"), "prev_question": values.get("last_question"),
            "prev_at": values.get("last_at"), "prev_clarified": bool(values.get("clarified"))}


def chip(desk: str) -> dict:
    return {"desk": desk, "label": DESKS[desk]["chip"]}


def _mask_note(decision: dict) -> str:
    kinds = [MASKED[k] for k in decision.get("masked") or () if k in MASKED]
    return f"I removed {' and '.join(kinds)} from your question before reading it.\n\n" if kinds else ""


# --------------------------------------------------------------------- the answer desks
def _section(desk: str, r: dict, before: list, decision: dict) -> tuple[dict, list]:
    """One labelled section with its citations numbered after the turn's earlier ones, and the chips a refusal
    offers: the other desk, then a case."""
    n = sum(len(s["citations"]) for s in before)
    cites = [] if "error" in r else r.get("citations") or []
    numbered = [{**c, "n": n + i} for i, c in enumerate(cites, 1)]
    if "error" in r:
        text = r["error"]
    elif r.get("answer"):
        text = r["answer"]
    elif cites:                                  # the local lane: no generator behind retrieve()
        text = "From the documents:\n" + "\n".join(f"[{c['n']}] {c.get('quote', '')}" for c in numbered)
    else:
        text = "The documents this desk reads do not answer this."
    in_force = []
    names = [c.get("source_uri") or c.get("source") for c in cites]
    if "error" not in r and (desk == "statute" or any(desk_law.statute_of(x) for x in names)):
        in_force = desk_law.in_force_lines(names)          # the fallback too, when it cites the law
    if in_force:
        text += "\n\n" + "\n".join(in_force)
    answered = bool(r.get("answerable")) and "error" not in r
    chips = []
    if not answered:
        permitted = set(decision.get("permitted") or ())
        chips = [chip(d) for d in ANSWER_DESKS if d != desk and d in permitted and desk not in ("fallback", "astar")
                 and decision.get("method") != "single"]          # single mode has one answer desk
        if "case" in permitted:
            chips.append(chip("case"))
    return ({"desk": desk, "title": TITLES[desk], "answer": text, "answerable": answered,
             "confidence": r.get("confidence", "low"), "citations": numbered, "in_force": in_force, "notes": [],
             "error": "error" in r}, chips)


# --------------------------------------------------------------------- the company's clause notes
def notes_of(raw) -> dict:
    """tenant_settings/{tenant}.clause_notes as the handbook desk reads it: {clause code: {"note", "basis"}}. An entry
    that is not a clause code with a note is left out (commands/desk_ops.py refuses it before it is written)."""
    out = {}
    for code, e in (raw.items() if isinstance(raw, dict) else ()):
        code = str(code).strip().upper()
        if CLAUSE_CODE.match(code) and isinstance(e, dict) and isinstance(e.get("note"), str) and e["note"].strip():
            out[code] = {"note": e["note"].strip()[:NOTE_MAX],
                         "basis": dict(e["basis"]) if isinstance(e.get("basis"), dict) else None}
    return out


def cited_clauses(citations: list, ctx: dict, codes) -> list[str]:
    """The codes among `codes` that the citations come from. A notebook's or the local lane's chunk id names its
    section (acme:hr_policy_2026#LV-07); a lane's (acme:<sha256>#3) does not, so the chunk rows' locators are read in
    one call, and a row counts only when it is this tenant's. A long section's later windows count too (LV-07-1)."""
    tenant, codes = ctx["tenant"], list(codes)

    def code_of(loc: str):
        return next((c for c in codes if loc == c or loc.startswith(c + "-")), None)

    found, ids = [], []
    for c in citations:
        cid = str(c.get("chunk_id") or "")
        loc = cid.rpartition("#")[2] if cid.startswith(f"{tenant}:") and "#" in cid else ""
        if loc.isdigit():
            ids.append(cid)
        elif loc:
            found.append(code_of(loc))
    if ids and ctx.get("db") is not None:
        db = ctx["db"]
        for snap in db.get_all([db.collection("chunks").document(i) for i in dict.fromkeys(ids)],
                               field_paths=["tenant_id", "locator"]):
            row = (snap.to_dict() or {}) if snap.exists else {}
            if row.get("tenant_id") == tenant:
                found.append(code_of(str(row.get("locator") or "")))
    return sorted({c for c in found if c})


def noted(section: dict, ctx: dict) -> dict:
    """A handbook answer with the company's note on each clause it cites that has one, after the answer and in
    "notes". A read that fails shows the answer alone."""
    notes = notes_of(ctx.get("clause_notes"))
    if not notes or not section.get("answerable"):
        return section
    try:
        codes = cited_clauses(section["citations"], ctx, notes)
    except Exception as e:  # noqa: BLE001 - the handbook's answer stands without its notes
        log.warning(json.dumps({"event": "desk_clause_notes_unread", "error": type(e).__name__}))
        return section
    shown = [{"clause": c, "note": notes[c]["note"], "basis": notes[c]["basis"]} for c in codes]
    if not shown:
        return section
    text = section["answer"] + "\n\n" + "\n".join(f"Note on {n['clause']}: {n['note']}" for n in shown)
    return {**section, "answer": text, "notes": shown}


def _answer(desk: str, state: DeskState, runtime: Runtime) -> dict:
    ctx = runtime.context
    decision = state["decision"]
    question = decision["question"]
    if desk in ANSWER_DESKS and len(decision.get("parts") or ()) > 1:   # a focus line by code, never a rewrite
        question = f"{question}\n\n(This part: what {DESKS[desk]['label']} says.)"
    filt = fallback_doc_types(decision["parts"]) if desk in ("fallback", "astar") else doc_types(desk)
    if desk == "astar" or (decision.get("needs_calculation") and DESKS.get(desk, {}).get("agent_model")):
        return _agent_answer(desk, question, filt, state, ctx)
    return _direct(desk, question, filt, state, ctx)


def _direct(desk: str, question: str, filt: list, state: DeskState, ctx: dict, agent_error: str | None = None) -> dict:
    """A direct section: rag-api's own cited answer from one retrieve. After an agent's model failed (agent_error),
    the same answer only while the turn's Meter has its budget and its time left; otherwise its stop answer."""
    meter = limits.meter_of(ctx)
    if agent_error and meter.stopped_by is None:
        if meter.spent_inr() >= meter.budget_inr:
            meter.stop("turn_budget")
        elif meter.left() < limits.MIN_MODEL_S:
            meter.stop("turn_deadline")
    if agent_error and meter.stopped_by is not None:
        r, calls = {"citations": [], "answerable": False, "confidence": "low", "answer": limits.STOP_ANSWER}, 0
    else:
        r = documind_tools.retrieve(question, tenant_id=ctx["tenant"], top_k=5, doc_type=filt,
                                    assertion=ctx.get("assertion") or None, brain="desk")
        meter.charge_rag(r.get("usage"))
        calls = 1
    section, chips = _section(desk, r, state.get("sections") or [], state["decision"])
    if desk == "handbook":
        section = noted(section, ctx)
    extra = {"agent_error": agent_error, "stopped_by": meter.stopped_by} if agent_error else {}
    return _with_section(state, {**section, "mode": "direct", "retrieve_calls": calls, "tool_calls": [],
                                 "refusals": [], **extra}, chips)


def _with_section(state: DeskState, section: dict, chips: list) -> dict:
    offered = list(state.get("offered_chips") or [])
    offered += [c for c in chips if c not in offered]
    return {"sections": (state.get("sections") or []) + [section], "offered_chips": offered}


def _agent_answer(desk: str, question: str, filt: list, state: DeskState, ctx: dict) -> dict:
    """Agent mode (desk_agent.py): the section is the agent's answer, its calculations written by code, and the
    passages it read as the citations. Only an answer turn reaches here: a gate hit never enters the graph. A model
    error (a 429, a 5xx) is not the turn's: the section is the direct answer instead (_direct), under the same Meter."""
    decision = state["decision"]
    if decision.get("gate") or decision.get("route") not in ("handbook", "statute", "fallback"):
        raise ValueError("only an answer turn reaches a desk's agent")
    try:
        got = desk_agent.run(desk, question, filt, ctx)
    except GraphBubbleUp:                             # LangGraph's own control flow is not an error
        raise
    except Exception as exc:                          # noqa: BLE001 - logged by type, never by its text
        log.warning(json.dumps({"event": "desk_agent_failed", "desk": desk, "error": type(exc).__name__}))
        return _direct(desk, question, filt, state, ctx, agent_error=type(exc).__name__)
    r = {"citations": [desk_agent.citation(p) for p in got["passages"]], "answerable": got["answerable"],
         "confidence": "medium" if got["answerable"] else "low", "answer": desk_agent.compose(got)}
    section, chips = _section(desk, r, state.get("sections") or [], decision)
    if desk == "handbook":
        section = noted(section, ctx)
    return _with_section(state, {**section, "mode": "agent", "calculations": got["calculations"],
                                 "retrieve_calls": got["retrieve_calls"], "tool_calls": got["tool_calls"],
                                 "refusals": got["refusals"], "stopped_by": got["stopped_by"]}, chips)


def handbook(state: DeskState, runtime: Runtime) -> dict:
    return _answer("handbook", state, runtime)


def statute(state: DeskState, runtime: Runtime) -> dict:
    return _answer("statute", state, runtime)


def fallback(state: DeskState, runtime: Runtime) -> dict:
    return _answer("fallback", state, runtime)


def astar(state: DeskState, runtime: Runtime) -> dict:
    return _answer("astar", state, runtime)


# --------------------------------------------------------------------- the code desks
def posh_card(queues: dict) -> dict:
    """What the POSH reply offers: the card GET /v1/cases/offer shows (shared/cases.posh_offer: each office, its
    Internal Committee members and its Local Committee), the clock and the basis. Nothing is written: the person
    chooses the office and the members and presses."""
    card = cases.posh_offer(queues)
    if card is None:
        return {"case_type": "posh", "configured": False, "posh": None}
    return {"case_type": "posh", "configured": True, "posh": card,
            "clock": [desk_law.CLOCKS["posh"]], "basis": desk_law.basis_for("posh"),
            "open": "POST /v1/cases with case_type posh, the unit, the members chosen and a client token"}


def case_reply(decision: dict, ctx: dict) -> dict:
    """The case desk's reply. A draft through cases.draft() for a person whose roles open the case desk; for POSH,
    the card and no write; while a draft is open, a pointer to it."""
    ct = decision.get("case_type") or "people_query"
    if decision.get("method") == "draft":
        return {"answer": DRAFT_OPEN, "case": {"draft_open": ctx.get("draft_open")}, "chips": []}
    gate = decision.get("gate")
    fixed = desk_law.template(gate or ct) if (gate or ct) in desk_law.TEMPLATES else None   # says nothing of a draft
    text = fixed or CASE_TEXT
    queues = ctx.get("queues") or {}
    if ct == "posh":
        return {"answer": text, "case": posh_card(queues), "chips": []}
    if "case" not in roles.desks(ctx.get("roles") or ()):
        return {"answer": fixed or NO_DRAFT["roles"], "case": None, "chips": []}
    sensitive = ct in desk_law.SENSITIVE_CASES
    question = decision.get("question")
    summary = (question or "")[:cases.SUMMARY_MAX] if ct in STARTS_WITH_QUESTION else ""
    try:
        rec = cases.draft(ctx["db"], ctx["tenant"], ctx["email"], ct, queues, summary=summary,
                          source=SOURCES.get(decision.get("method"), "model"), via=ctx.get("via") or "direct",
                          clause=ctx.get("clause"), route_trace=desk_router.record(decision),
                          route_tried=ctx.get("route_tried"),
                          partial_answer_citations=ctx.get("partial_answer_citations"),
                          question_sha256=None if sensitive or not question else desk_router.question_sha256(question))
    except cases.CaseError as e:
        return {"answer": fixed or NO_DRAFT["error"], "case": {"error": e.status, "detail": e.detail}, "chips": []}
    except Exception as e:  # noqa: BLE001 - a store that failed is a reply, never a 500
        log.warning(json.dumps({"event": "desk_case_draft_failed", "error": type(e).__name__}))
        return {"answer": fixed or NO_DRAFT["error"], "case": {"error": 503, "detail": "the case could not be drafted"},
                "chips": []}
    return {"answer": text, "case": cases.view(rec, queues), "chips": []}


def oos_reply(decision: dict, ctx: dict) -> dict:
    kind = desk_rules.action(decision.get("question") or "")
    permitted = set(decision.get("permitted") or ())
    return {"answer": _mask_note(decision) + OOS[kind], "case": None,
            "chips": [chip("case")] if "case" in permitted else []}


def refusal_reply(decision: dict, ctx: dict) -> dict:
    """denied and not_covered: no retrieval, no model, a case offer."""
    desk = decision.get("desk")
    name = DESKS[desk]["label"] if desk in DESKS else "an answer"
    if decision["route"] == "not_covered" and desk in (ctx.get("desks_off") or ()):
        text = (f"The company has switched off the desk for {name} for now, so DocuMind did not search for this. "
                f"You can raise a case for the People team.")
    elif decision["route"] == "denied":
        text = (f"Your roles in this company do not include asking {name}, so DocuMind did not search for this. "
                f"You can raise a case for a person.")
    else:
        text = (f"This company has no documents for {name} yet, so DocuMind did not search for this. "
                f"You can raise a case for the People team.")
    permitted = set(decision.get("permitted") or ())
    return {"answer": text, "case": None, "chips": [chip("case")] if "case" in permitted else []}


def case_node(state: DeskState, runtime: Runtime) -> dict:
    out = case_reply(state["decision"], runtime.context)
    return {"messages": [AIMessage(content=out["answer"])], "offered_chips": out["chips"]}


def oos(state: DeskState, runtime: Runtime) -> dict:
    out = oos_reply(state["decision"], runtime.context)
    return {"messages": [AIMessage(content=out["answer"])], "offered_chips": out["chips"]}


def clarify(state: DeskState, runtime: Runtime) -> dict:
    decision = state["decision"]
    desks = [d for d in decision.get("chips") or () if d in ANSWER_DESKS][:2]
    if len(desks) == 2:
        text = f"Should I answer this from {DESKS[desks[0]]['label']} or from {DESKS[desks[1]]['label']}?"
    else:
        text = "Could you say a little more about what you want to know?"
    return {"messages": [AIMessage(content=_mask_note(decision) + text)], "offered_chips": [chip(d) for d in desks],
            "last_route": "clarify", "last_question": (decision.get("question") or "")[:desk_router.PREV_CHARS],
            "last_at": time.time(), "clarified": True}


# --------------------------------------------------------------------- dispatch and the parts
def dispatch(state: DeskState, runtime: Runtime) -> Command[Literal["handbook", "statute", "case", "clarify", "oos",
                                                                    "fallback", "astar"]]:
    d = state["decision"]
    route = d["route"]
    first = {"case": "case", "out_of_scope": "oos", "clarify": "clarify", "fallback": "fallback"}.get(route)
    if route == "fallback" and d.get("arm") == "Astar":            # set by decide() for a desk_eval caller's arm only
        first = "astar"
    rest: list = []
    if route in ANSWER_DESKS:
        first, rest = d["parts"][0], list(d["parts"][1:])
    if first is None:
        raise ValueError(f"route {route!r} is answered by code and never enters the graph")
    return Command(goto=first, update={"parts": rest, "sections": [], "offered_chips": [],
                                       "messages": [HumanMessage(content=d.get("question") or "")]})


def head(decision: dict) -> str:
    """What an answer says before its sections: the numbers masked out of the question, and the desk a second clarify
    committed to."""
    out = _mask_note(decision)
    if decision.get("committed") and decision["route"] in DESKS:
        out += f"Taking this as a question about {DESKS[decision['route']]['label']}.\n\n"
    return out


def _compose(state: DeskState, skipped: list) -> str:
    decision = state["decision"]
    sections = state.get("sections") or []
    head_ = head(decision)
    if len(sections) == 1:
        body = sections[0]["answer"]
    else:
        body = "\n\n".join(f"{s['title']}\n{s['answer']}" for s in sections)
    return head_ + body


def next_part(state: DeskState, runtime: Runtime) -> Command[Literal["handbook", "statute", "__end__"]]:
    parts = list(state.get("parts") or [])
    if parts and limits.meter_of(runtime.context).left() >= PART_MIN_S:
        return Command(goto=parts[0], update={"parts": parts[1:]})
    offered = list(state.get("offered_chips") or [])
    decision = state["decision"]
    offered += [chip(p) for p in parts if chip(p) not in offered]          # a part with no time left: a chip
    offered += [chip(c) for c in decision.get("chips") or () if c in DESKS and DESKS[c]["chip"]
                and chip(c) not in offered]
    return Command(goto=END, update={
        "parts": [], "offered_chips": offered,
        "messages": [AIMessage(content=_compose(state, parts))],
        "last_route": decision["route"], "last_question": (decision.get("question") or "")[:desk_router.PREV_CHARS],
        "last_at": time.time(), "clarified": False})


def build(checkpointer=None):
    """The compiled graph, on the service's checkpointer."""
    g = StateGraph(DeskState, context_schema=dict)
    for name, fn in (("dispatch", dispatch), ("handbook", handbook), ("statute", statute), ("case", case_node),
                     ("clarify", clarify), ("oos", oos), ("fallback", fallback), ("astar", astar),
                     ("next_part", next_part)):
        g.add_node(name, fn)
    g.add_edge(START, "dispatch")
    for desk in ("handbook", "statute", "fallback", "astar"):
        g.add_edge(desk, "next_part")
    for desk in ("case", "clarify", "oos"):
        g.add_edge(desk, END)
    return g.compile(checkpointer=checkpointer)


# --------------------------------------------------------------------- one turn
OUTCOMES = {"case": "case", "out_of_scope": "oos", "clarify": "clarify", "denied": "denied",
            "not_covered": "not_covered"}       # evals/route_eval.py's outcomes; an answer desk's is answered or not


def outcome(decision: dict, sections: list) -> str:
    """The turn's outcome as the route eval scores it: an answer desk's is "answer" when a section answered, else
    "grounded_refusal"; every other route's is fixed by the route."""
    if decision["route"] in OUTCOMES:
        return OUTCOMES[decision["route"]]
    return "answer" if any(s.get("answerable") for s in sections) else "grounded_refusal"


def run_turn(graph, decision: dict, ctx: dict, config: dict | None = None) -> dict:
    """The reply to one decided turn: {answer, note (head() of an answer turn), sections, citations, chips, case,
    outcome, retrieve_calls (one per direct section, each search an agent made), tool_calls and refusals (an agent's,
    by name), route (the loggable record)}. Only answer, clarify and fallback turns invoke the graph, so only they are
    checkpointed."""
    route = decision["route"]
    out: dict
    if route in GRAPH_ROUTES:
        kept = {**decision, "l1": desk_router.record(decision)["l1"]}      # L1's sensitive guess is not checkpointed
        state = graph.invoke({"decision": kept}, config=config, context=ctx)
        sections = state.get("sections") or []
        out = {"answer": state["messages"][-1].content, "sections": sections,
               "citations": [c for s in sections for c in s["citations"]], "chips": state.get("offered_chips") or [],
               "case": None, "note": head(kept) if sections else ""}
    else:
        if route == "case":
            got = case_reply(decision, ctx)
        elif route == "out_of_scope":
            got = oos_reply(decision, ctx)
        else:
            got = refusal_reply(decision, ctx)
        out = {"answer": got["answer"], "sections": [], "citations": [], "chips": got["chips"], "case": got["case"],
               "note": ""}
    out["outcome"] = outcome(decision, out["sections"])
    out["retrieve_calls"] = sum(int(s.get("retrieve_calls", 1)) for s in out["sections"])
    out["tool_calls"] = [t for s in out["sections"] for t in s.get("tool_calls") or ()]
    out["refusals"] = [t for s in out["sections"] for t in s.get("refusals") or ()]
    out["route"] = desk_router.record(decision)
    return out
