"""DocuMind chat service - the tool layer.

One definition of each tool, imported by the agent and by nothing else. Lessons 6.1 to 6.4 all
teach against these signatures; keeping them here means a lesson and the deployed service cannot
disagree about what `calculate_processing_cost` means, which is exactly the drift Module 6 opened
with (the same tool carried three different shapes across three lessons).

Two things differ from the notebook versions, and both are about identity rather than logic:

  - `retrieve` ADAPTS shared/documind_tools.retrieve - binding the tenant, renaming the
    filter and reshaping the response - instead of returning a mock dict. It does not talk to
    rag-api itself; there is exactly one function in this repo that does (lesson 8.7).
  - it reads the tenant (and the person's IAP assertion) from the ToolRuntime the framework
    injects, never from an argument the model fills.

HOW THE TENANT REACHES A TOOL, precisely, because the first version got it wrong. `tenant_id`
was declared `Annotated[str, InjectedToolArg]`, which HIDES an argument from the schema the
model reads - and does nothing else. langgraph's ToolNode fills `InjectedState`, `InjectedStore`
and `ToolRuntime`; a bare `InjectedToolArg` is never filled, so the tool ran with tenant_id=""
and rag-api answered 403 for a tenant that does not exist. Hidden from the model AND delivered
is `runtime: ToolRuntime`, whose `.context` is the dict agent.py passes to
`agent.invoke(..., context=...)`. Proven offline on 2026-09-05 (gap G4): the runtime parameter
is absent from `tool_call_schema`, and the context arrives.

`calculate_processing_cost` delegates to the shared one. Before workshop lesson 5.5's fix it was a copy
with its own rates that priced an unknown tier at the standard rate, while the shared one refused
it; one function cannot disagree with itself. `get_usage_stats` is gone: it was a stub that always
answered `value: None`, and wiring it would have given the chat service every tenant's usage rows.

ONE TOOL LIST (workshop lesson 5.7). `TOOLS` is what LangChain and LangGraph bind;
`for_adk()` is the same two tools for ADK, as plain functions with the same docstrings, whose
request arrives through `REQUEST` rather than a ToolRuntime and whose arguments are checked
against the same schemas. Both end in `search()`, so the two adapters can differ only in how the
request reaches them, and no schema a model reads names the tenant, the assertion or the brain.

Verified 2026-09-04 against langchain 1.4.0 / langchain-google-genai 4.4.0; the ToolRuntime
wiring against langgraph 1.2.11 / langchain-core 1.5.6 on 2026-09-05.
"""
from __future__ import annotations

import contextvars
import logging
import threading
import time

from langchain_core.tools import ToolException, tool

try:
    from langchain.tools import ToolRuntime          # langchain 1.x re-exports langgraph's
except ImportError:                                   # a bare langgraph install
    from langgraph.prebuilt.tool_node import ToolRuntime

# The shared tool layer. The image must be built with `deploy/` as its context so that
# shared/ lands beside this service - see the Dockerfile. Lesson 8.7 is the argument for why
# this import exists at all: one retrieval implementation, adapted per brain, never re-written.
from shared import documind_tools

import limits                                         # services/chat/limits.py: the turn's Meter and its timed calls

logger = logging.getLogger("documind.chat.tools")

# Tools that must never be reachable from a model turn. GuardMiddleware in agent.py imports this
# set and refuses these names before dispatch; keeping it beside the tools makes an omission
# visible in review rather than at 2am.
BLOCKED = {"delete_document", "send_email", "modify_access"}
# Each tool's budget in seconds, ENFORCED by limits.timed_tool_call since workshop lesson 5.5: a call is cut at the
# smaller of its budget and the turn's time left. retrieve waits for rag-api up to RAG_TIMEOUT_S, so its budget is that
# plus 5 s for the token mint and the connection: 95 on the lane, where commands/lesson-12.8.sh sets RAG_TIMEOUT_S=90.
TIMEOUTS = {"retrieve": documind_tools.RAG_TIMEOUT_S + 5, "calculate_processing_cost": 10}


def _ctx(runtime: ToolRuntime, key: str, default: str = "") -> str:
    """One value out of the runtime context agent.py set - a dict, or an object with attributes."""
    ctx = getattr(runtime, "context", None)
    if isinstance(ctx, dict):
        return ctx.get(key, default)
    return getattr(ctx, key, default) if ctx is not None else default


# The request, for a framework with no runtime to carry it: brains.AdkBrain sets it for the turn. A
# ContextVar, not a global: the sync endpoint runs in a thread pool, and asyncio.run() and ADK's tool
# threads copy the context into each call, so two concurrent requests cannot see each other's tenant.
REQUEST: contextvars.ContextVar[dict] = contextvars.ContextVar("documind_request", default={})
_LEDGER = threading.Lock()      # ToolNode runs one model message's calls in parallel threads


def _number(citations: list, ledger: list) -> None:
    """Give each citation the n the answer cites it by: its place in this turn's ledger, and the same
    n when a second search in the same turn finds the same chunk again (workshop lesson 5.1)."""
    with _LEDGER:
        for c in citations:
            key = c.get("chunk_id") or c.get("quote")
            known = next((x for x in ledger if (x.get("chunk_id") or x.get("quote")) == key), None)
            if known is None:
                known = {**c, "n": len(ledger) + 1}
                ledger.append(known)
            c["n"] = known["n"]


@tool
def retrieve(query: str, doc_type: str = "all", top_k: int = 5,
             runtime: ToolRuntime = None) -> dict:
    """Retrieve grounded passages from DocuMind's corpus.

    Args:
        query: The question, in natural language
        doc_type: Filter by type (policy, contract, invoice, form, research_paper, all)
        top_k: How many passages to return
    """
    # runtime is INJECTED by the framework and absent from the schema the model reads (see the
    # module docstring). Its context carries the tenant, looked up from the roster by agent.py,
    # and the IAP assertion of the person this turn is for. Declare either as an ordinary
    # parameter and the model chooses the tenant - a cross-tenant read that no docstring can
    # prevent. Both are absent from the Args block on purpose: that block is model-facing.
    tenant_id = _ctx(runtime, "tenant_id")
    assertion = _ctx(runtime, "assertion")
    brain = _ctx(runtime, "brain")          # which harness is asking - rag-api's usage row records it (8.7)
    return search(query, doc_type, top_k, tenant_id=tenant_id, assertion=assertion, brain=brain,
                  cited=_ctx(runtime, "cited", None), meter=_ctx(runtime, "meter", None))


def search(query: str, doc_type: str = "all", top_k: int = 5, *, tenant_id: str = "",
           assertion: str = "", brain: str = "", cited: list | None = None, meter=None) -> dict:
    """The adapter itself, with no framework in it. LangChain's `retrieve` above and ADK's in for_adk()
    both end here (workshop lesson 5.7). `cited` is the turn's ledger: each citation gets its n. `meter`
    is the turn's limits.Meter: what rag-api billed for this search is charged to it (workshop lesson 5.5)."""
    # ADAPTER, NOT IMPLEMENTATION (lesson 8.7). This function binds the tenant, renames the
    # filter and reshapes the response for the chat API's contract. What it does NOT do is talk
    # to rag-api itself - that is documind_tools.retrieve's job, and there is exactly one of it
    # (and it is also where DOCUMIND_PROFILE=local turns into a Chroma read, gap G3).
    started = time.monotonic()
    try:
        answer = documind_tools.retrieve(
            query, tenant_id=tenant_id, top_k=top_k,
            doc_type=None if doc_type == "all" else doc_type,
            assertion=assertion or None, brain=brain or None)
    finally:
        logger.info("retrieve took %.2fs", time.monotonic() - started)
    # A call cut at its budget (limits.timed_tool_call) runs on in its thread, and rag-api still bills it on its own
    # row. It writes nothing into the turn: no cost on this turn's bill and no citation numbered into the ledger, or
    # the answer would list a source the model never read (workshop lesson 5.5).
    delivered = limits.may_commit()
    if meter is not None and delivered:
        meter.charge_rag(answer.get("usage"))       # rag-api's own cost line, on this turn's bill

    if "error" in answer:
        # Returned as data, not raised. The model reads the failure and says so, which is the
        # rule lesson 6.2 set: an exception kills the turn, a payload lets the agent explain.
        logger.warning("rag-api query failed: %s", answer["error"])
        return {"error": "document search is unavailable",
                "citations": [], "answerable": False, "confidence": "low"}

    citations = answer.get("citations", [])
    out = {
        "citations": [
            # Widened for lesson 9.6. A projection is a SILENT filter: name five
            # keys here and a media citation arrives as plain text with no
            # thumbnail and no timestamp, with nothing raised and nothing logged.
            {k: c[k] for k in ("chunk_id", "source_uri", "page", "quote", "score",
                               "kind", "media_url", "start", "end") if k in c}
            for c in citations
        ],
        "answerable": answer.get("answerable", False),
        "confidence": answer.get("confidence", "low"),
    }
    if cited is not None and delivered:
        _number(out["citations"], cited)
    return out


@tool
def calculate_processing_cost(total_pages: int, num_documents: int = 1,
                              processing_type: str = "standard") -> dict:
    """Estimate document processing cost in USD and INR.

    Args:
        total_pages: Total page count across all documents
        num_documents: How many documents those pages are spread across
        processing_type: Service tier - standard, priority, or bulk
    """
    # The shared function, not a copy (workshop lesson 5.5). It refuses an unknown tier with a
    # ValueError; re-raised as a ToolException, LangChain hands the model an error result, as it does
    # for an argument of the wrong type, and the turn goes on.
    try:
        return documind_tools.calculate_processing_cost(total_pages, num_documents, processing_type)
    except ValueError as exc:
        raise ToolException(str(exc)) from None


calculate_processing_cost.handle_tool_error = True
TOOLS = [retrieve, calculate_processing_cost]


def _checked(twin, **args) -> dict:
    """The model's arguments, checked against the @tool twin's own schema as LangChain checks them before a call:
    a value LangChain refuses is a ToolException here too, never a value passed on to rag-api (workshop
    lesson 5.7)."""
    from pydantic import ValidationError
    try:
        valid = twin.tool_call_schema.model_validate(args)
    except ValidationError as exc:
        raise ToolException(str(exc)) from None
    return {k: getattr(valid, k) for k in args}


def for_adk() -> list:
    """The same two tools for ADK, as plain functions (workshop lesson 5.7). FunctionTool declares a
    function's own signature, so these name only what the model may choose; the tenant, the assertion,
    the brain and the ledger arrive through REQUEST, and an argument the model invents is dropped."""
    def retrieve(query: str, doc_type: str = "all", top_k: int = 5) -> dict:
        ctx = REQUEST.get()
        return search(**_checked(TOOLS[0], query=query, doc_type=doc_type, top_k=top_k),
                      tenant_id=ctx.get("tenant_id", ""), assertion=ctx.get("assertion", ""),
                      brain=ctx.get("brain", ""), cited=ctx.get("cited"), meter=ctx.get("meter"))

    def calculate_processing_cost(total_pages: int, num_documents: int = 1,
                                  processing_type: str = "standard") -> dict:
        return TOOLS[1].func(**_checked(TOOLS[1], total_pages=total_pages, num_documents=num_documents,
                                        processing_type=processing_type))

    fns = [retrieve, calculate_processing_cost]
    for fn, twin in zip(fns, TOOLS):
        fn.__doc__ = twin.func.__doc__          # one docstring per tool, whichever framework reads it
    return fns
