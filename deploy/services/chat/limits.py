"""DocuMind chat service - the limits of one turn: model calls, rupees and time (workshop lessons 5.5 and 5.7).

Before these limits, a turn stopped when the model stopped asking for tools. LangChain's create_agent binds a
recursion limit of 9,999 and LangGraph's default is 10,007, so a model that kept asking for the same search ran about
5,000 calls until Cloud Run's 300 s cut the request. ADK's cap of 12 calls ended in an exception and a 500. The tool
budgets in tools.TIMEOUTS were read after the call returned, to pick a log level, and never cut a call short.

Now every turn carries one Meter, made by agent.chat() for the turn and handed to the brain in its context:

    model calls   CHAT_MAX_MODEL_CALLS   12     checked before each model call; the first call is always allowed
    rupees        CHAT_TURN_BUDGET_INR   5      this turn's model calls and rag-api answers, at list price
    time          CHAT_TURN_DEADLINE_S   100    no model call starts with under CHAT_MIN_MODEL_S (5) left; each call
                                                gets min(CHAT_MODEL_TIMEOUT_S, time left / CHAT_MODEL_ATTEMPTS)

A tripped limit ends the turn with HTTP 200, STOP_ANSWER as the answer and limits.stopped_by naming the limit; the
thread stays whole, so the next turn on it answers. Each tool call is cut at the smaller of its own budget and the
time the turn has left (never under TOOL_FLOOR_S), and a cut call is a payload error the model reads, not a refusal;
a cut call still queued never runs, and one already running adds no citation to the turn.
The worst case is the deadline, plus one retry's backoff (about 2 s), plus the tool floor: about 103 s, under the UI's
120 s, gunicorn's 120 s worker timeout and Cloud Run's 300 s (commands/tests/test_chat_limits.py checks the sum).

Each brain checks the Meter at its own seam: LangChain through TurnLimitsMiddleware (wrap_model_call only, so a turn
still writes the same checkpoints), the hand-built LangGraph node itself, ADK through its model callbacks beside
RunConfig.max_llm_calls. The frameworks' own limits stay as backstops. The rupees are a turn's own; the month's
counter and the tenant_daily view still count rag-api's rows only.

This module imports only the standard library and shared/prices.py at the top; LangChain, tools.py and ADK's types
are imported where they are used, so its arithmetic can be tested without the chat image's pins.
"""
from __future__ import annotations

import asyncio
import contextvars
import functools
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field

from shared import prices

try:                                                     # the chat image has it; the stdlib tests do not need it
    from langchain.agents.middleware import AgentMiddleware
except ImportError:                                      # pragma: no cover - only without the chat pins
    AgentMiddleware = object

logger = logging.getLogger("documind.chat.limits")

PROFILE = os.environ.get("DOCUMIND_PROFILE", "gcp")      # the same switch shared/profile.py reads
MAX_MODEL_CALLS = int(os.environ.get("CHAT_MAX_MODEL_CALLS", "12"))
TURN_BUDGET_INR = float(os.environ.get("CHAT_TURN_BUDGET_INR", "5"))
TURN_DEADLINE_S = float(os.environ.get("CHAT_TURN_DEADLINE_S", "100"))
MODEL_TIMEOUT_S = float(os.environ.get("CHAT_MODEL_TIMEOUT_S", "30"))
MODEL_ATTEMPTS = int(os.environ.get("CHAT_MODEL_ATTEMPTS", "2"))
MIN_MODEL_S = float(os.environ.get("CHAT_MIN_MODEL_S", "5"))
TOOL_FLOOR_S = 1.0               # a tool call always gets at least this long
RETRY_BACKOFF_S = 2.0            # google-genai waits about 1 s plus up to 1 s of jitter before its retry

STOP_ANSWER = ("I stopped this turn at one of its limits before I could finish, so this answer is incomplete. "
               "Ask again, or ask a narrower question.")
STOPS = ("model_calls", "turn_budget", "turn_deadline", "recursion_limit")

# The pool timed tool calls run in. Its own, never asyncio.to_thread: asyncio.run() waits for the default executor's
# threads before it returns, so an abandoned call would hold the turn to the end anyway. Every turn in the process
# shares it, and a call waiting for a free thread spends its own budget waiting, so the pool is sized above what one
# process can ask for at once: Cloud Run sends up to 20 requests to the container (--concurrency=20, commands/
# lesson-12.8.sh), a turn can run a few calls side by side, and an abandoned call keeps its thread to RAG_TIMEOUT_S.
TOOL_THREADS = int(os.environ.get("CHAT_TOOL_THREADS", "64"))
TOOL_POOL = ThreadPoolExecutor(max_workers=TOOL_THREADS, thread_name_prefix="documind-tool")


def _timeouts() -> dict:
    from tools import TIMEOUTS          # services/chat/tools.py, imported here so this module loads without LangChain
    return TIMEOUTS


def _request():
    """The ADK brain's turn context (tools.REQUEST), or None outside a turn. Never the ContextVar's shared default
    dict: a Meter stored there would carry one count across every later call in the process."""
    from tools import REQUEST
    return REQUEST.get(None)


@dataclass
class Meter:
    """One turn's counter. agent.chat() makes it after the brain is built, so a cold import is not the turn's time."""

    max_model_calls: int = MAX_MODEL_CALLS
    budget_inr: float = TURN_BUDGET_INR
    deadline_s: float = TURN_DEADLINE_S
    model: str = ""
    started: float = field(default_factory=time.monotonic)
    model_calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cached_tokens: int = 0
    cost_usd: float = 0.0           # this turn's own model calls
    rag_cost_usd: float = 0.0       # what rag-api billed for this turn's searches
    stopped_by: str | None = None
    tool_timeouts: list = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def left(self) -> float:
        return self.deadline_s - (time.monotonic() - self.started)

    def spent_inr(self) -> float:
        return prices.inr(self.cost_usd + self.rag_cost_usd)

    def allow_model_call(self) -> bool:
        """True, and counted, when the turn may call the model once more; False, with stopped_by set, when not."""
        with self._lock:
            if self.stopped_by is None and self.model_calls:            # the first call is always allowed
                if self.model_calls >= self.max_model_calls:
                    self.stopped_by = "model_calls"
                elif self.spent_inr() >= self.budget_inr:
                    self.stopped_by = "turn_budget"
                elif self.left() < MIN_MODEL_S:
                    self.stopped_by = "turn_deadline"
            if self.stopped_by is not None:
                return False
            self.model_calls += 1
            return True

    def stop(self, reason: str) -> None:
        with self._lock:
            self.stopped_by = self.stopped_by or reason

    def charge_model(self, tokens_in: int, tokens_out: int, cached_tokens: int = 0, model: str | None = None) -> None:
        """One model call's tokens, priced at list price (shared/prices.py)."""
        tokens_in, tokens_out, cached_tokens = int(tokens_in or 0), int(tokens_out or 0), int(cached_tokens or 0)
        with self._lock:
            self.tokens_in += tokens_in
            self.tokens_out += tokens_out
            self.cached_tokens += cached_tokens
            self.cost_usd += prices.usd(model or self.model, tokens_in, tokens_out, cached_tokens)

    def charge_rag(self, usage: dict | None) -> None:
        """One rag-api answer. Its own cost (the gateway's price, or 0 for a cache hit) wins over list price."""
        if not usage:
            return
        usd = usage.get("cost_usd")
        if usd is None:
            usd = prices.usd(usage.get("model"), int(usage.get("tokens_in") or 0), int(usage.get("tokens_out") or 0),
                             int(usage.get("cached_tokens") or 0))
        with self._lock:
            self.rag_cost_usd += float(usd)

    def model_timeout_s(self) -> float:
        """Each attempt's timeout: the attempts together fit in the time left, and no attempt runs past 30 s."""
        return max(TOOL_FLOOR_S, min(MODEL_TIMEOUT_S, self.left() / MODEL_ATTEMPTS))

    def tool_budget_s(self, name: str) -> float:
        """The smaller of the tool's own budget and the turn's time left, never under the floor."""
        return max(TOOL_FLOOR_S, min(float(_timeouts().get(name, 30)), self.left()))

    def tool_timed_out(self, name: str) -> None:
        with self._lock:
            self.tool_timeouts.append(name)

    def summary(self) -> dict:
        """The response's `limits`: what the turn used against what it was allowed."""
        return {"stopped_by": self.stopped_by, "model_calls": self.model_calls, "max_model_calls": self.max_model_calls,
                "cost_inr": round(self.spent_inr(), 4), "budget_inr": self.budget_inr,
                "deadline_s": self.deadline_s, "tool_timeouts": list(self.tool_timeouts)}

    def row(self) -> dict:
        """The chat row's fields, which agent.chat() names one by one in its log line."""
        return {"model": self.model, "model_calls": self.model_calls, "tokens_in": self.tokens_in,
                "tokens_out": self.tokens_out, "cached_tokens": self.cached_tokens,
                "cost_usd": round(self.cost_usd, 6), "rag_cost_usd": round(self.rag_cost_usd, 6),
                "stopped_by": self.stopped_by, "tool_timeouts": list(self.tool_timeouts),
                "max_model_calls": self.max_model_calls, "budget_inr": self.budget_inr}


def meter_of(context) -> Meter:
    """The turn's Meter from a runtime context. A context dict with none (a notebook, a test) gets one at the defaults,
    kept in that dict for the rest of its turn; no context at all gets a fresh one each time, kept nowhere."""
    meter = context.get("meter") if isinstance(context, dict) else getattr(context, "meter", None)
    if meter is None:
        meter = Meter()
        if isinstance(context, dict):
            context["meter"] = meter
    return meter


def published() -> dict:
    """What /health publishes, and `make limits` prints."""
    return {"max_model_calls": MAX_MODEL_CALLS, "budget_inr": TURN_BUDGET_INR, "deadline_s": TURN_DEADLINE_S,
            "model_timeout_s": MODEL_TIMEOUT_S, "model_attempts": MODEL_ATTEMPTS, "min_model_s": MIN_MODEL_S,
            "tool_budgets_s": dict(_timeouts())}


def recursion_limit() -> int:
    """The framework backstop: two graph steps per model call and its tools, doubled, plus room for the guard."""
    return 4 * MAX_MODEL_CALLS + 10


def is_timeout(exc: BaseException) -> bool:
    """A transport timeout from any client the brains use: httpx (google-genai), requests, asyncio, the builtin."""
    names = {c.__name__ for c in type(exc).__mro__}
    return bool(names & {"TimeoutError", "TimeoutException", "Timeout", "ReadTimeout", "ServerTimeoutError"})


def usage_of(message) -> tuple:
    """(tokens_in, tokens_out, cached) from a LangChain AIMessage: output counts thinking, cache_read is in input."""
    u = getattr(message, "usage_metadata", None) or {}
    cached = (u.get("input_token_details") or {}).get("cache_read") or 0
    return u.get("input_tokens") or 0, u.get("output_tokens") or 0, cached


def stop_message():
    from langchain_core.messages import AIMessage
    return AIMessage(content=STOP_ANSWER)


def call_settings(meter: Meter) -> dict:
    """The per-call timeout and attempts for Gemini (langchain-google-genai reads both per call). The gcp profile only:
    whether ChatOllama takes them is not checked."""
    if PROFILE != "gcp":
        return {}
    return {"timeout": meter.model_timeout_s(), "max_retries": MODEL_ATTEMPTS}


# ----------------------------------------------------------------------------- tools, every brain
def _payload_error(name: str, budget: float) -> dict:
    """What the model reads when a tool is cut: data, like a failed search, never an error status. It is never only
    an "error" key, which ADK's own argument check answers and the ADK brain marks as a refusal."""
    return {"error": f"{name} did not answer within {budget:g}s and was abandoned", "timed_out": True,
            "citations": [], "answerable": False, "confidence": "low"}


class _Ticket:
    """One timed call's fate, decided once: delivered to the model, or abandoned at its budget. The tool claims it
    (may_commit) before it writes into the turn - the Meter's rag cost and the ledger that numbers the citations - so
    an abandoned call, whose thread runs on, never adds a cost or a source the model was not shown."""

    def __init__(self):
        self._lock = threading.Lock()
        self.state = None

    def _decide(self, state: str) -> bool:
        with self._lock:
            self.state = self.state or state
            return self.state == state

    def commit(self) -> bool:
        return self._decide("delivered")

    def abandon(self) -> bool:
        return self._decide("abandoned")


_TICKET: contextvars.ContextVar = contextvars.ContextVar("documind_tool_ticket", default=None)


def may_commit() -> bool:
    """True when this tool call's result will reach the model, so it may write into the turn; False once the call was
    abandoned. A call outside a timed wrapper (the direct brain, a notebook) is always delivered."""
    ticket = _TICKET.get()
    return ticket is None or ticket.commit()


def _ticketed():
    """A copy of the caller's context with a fresh ticket in it: the context the pool thread runs the call in."""
    ticket, ctx = _Ticket(), contextvars.copy_context()
    ctx.run(_TICKET.set, ticket)
    return ticket, ctx


def _log_time(name: str, started: float, budget: float) -> None:
    elapsed = time.monotonic() - started
    (logger.warning if elapsed > budget else logger.info)("%s took %.2fs (budget %ss)", name, elapsed, f"{budget:g}")


def timed_tool_call(request, handler):
    """LangChain's and LangGraph's tool wrapper: run the call in TOOL_POOL and wait for it no longer than its budget.

    A call past its budget is abandoned and the model reads a payload error. One still queued for a thread is
    cancelled; one already running goes on until RAG_TIMEOUT_S, and rag-api still bills it on its own row, but it
    writes nothing into the turn, neither cost nor citation (may_commit). Anything the tool raises is raised here, so
    a token mint that fails still fails the turn."""
    from langchain_core.messages import ToolMessage

    name = request.tool_call["name"]
    meter = meter_of(getattr(request.runtime, "context", None))
    budget = meter.tool_budget_s(name)
    started = time.monotonic()
    ticket, ctx = _ticketed()
    future = TOOL_POOL.submit(ctx.run, handler, request)
    try:
        return future.result(timeout=budget)
    except FutureTimeout:
        future.cancel()                        # still queued: it never runs
        if not ticket.abandon():               # it had already written its result into the turn: deliver it
            return future.result()
        meter.tool_timed_out(name)
        return ToolMessage(content=json.dumps(_payload_error(name, budget)), name=name,
                           tool_call_id=request.tool_call["id"])
    finally:
        _log_time(name, started, budget)


async def timed_async(name: str, fn, /, **kwargs):
    """ADK's twin of timed_tool_call: the plain function runs in TOOL_POOL; the turn waits no longer than its budget."""
    meter = meter_of(_request())
    budget = meter.tool_budget_s(name)
    started = time.monotonic()
    ticket, ctx = _ticketed()
    future = TOOL_POOL.submit(ctx.run, functools.partial(fn, **kwargs))
    try:
        return await asyncio.wait_for(asyncio.wrap_future(future), budget)    # a queued call is cancelled with it
    except (TimeoutError, asyncio.TimeoutError):  # one class from Python 3.11; two on 3.10
        if not ticket.abandon():               # it had already written its result into the turn: deliver it
            return await asyncio.wrap_future(future)
        meter.tool_timed_out(name)
        return _payload_error(name, budget)
    finally:
        _log_time(name, started, budget)


def timed_adk(fn):
    """One of tools.for_adk()'s functions as the coroutine ADK awaits. functools.wraps keeps the name, the docstring
    and the signature, so FunctionTool declares exactly what it declared before."""
    @functools.wraps(fn)
    async def call(**kwargs):
        return await timed_async(fn.__name__, fn, **kwargs)
    return call


# ----------------------------------------------------------------------------- 1. langchain
class TurnLimitsMiddleware(AgentMiddleware):
    """The Meter at LangChain's model seam. wrap_model_call only: a before_model or after_model hook would add graph
    nodes, and every turn would write more checkpoints (workshop lesson 6.6 counts them)."""

    def _before(self, request):
        meter = meter_of(request.runtime.context)
        if not meter.allow_model_call():
            return meter, None
        return meter, request.override(model_settings={**request.model_settings, **call_settings(meter)})

    @staticmethod
    def _after(meter, response):
        inner = getattr(response, "model_response", response)          # an ExtendedModelResponse wraps one
        for m in getattr(inner, "result", None) or [inner]:
            if getattr(m, "usage_metadata", None):
                meter.charge_model(*usage_of(m))
        return response

    def wrap_model_call(self, request, handler):
        meter, request = self._before(request)
        if request is None:
            return stop_message()
        try:
            return self._after(meter, handler(request))
        except Exception as exc:                       # noqa: BLE001 - only a timeout is caught; the rest raises
            if not is_timeout(exc):
                raise
            meter.stop("turn_deadline")
            return stop_message()

    async def awrap_model_call(self, request, handler):
        meter, request = self._before(request)
        if request is None:
            return stop_message()
        try:
            return self._after(meter, await handler(request))
        except Exception as exc:                       # noqa: BLE001
            if not is_timeout(exc):
                raise
            meter.stop("turn_deadline")
            return stop_message()


def repair_thread(graph, config: dict, as_node: str) -> None:
    """After a recursion error: answer every call the last model message left open, then end the turn with
    STOP_ANSWER, so the thread is whole and its next turn starts clean."""
    from langchain_core.messages import ToolMessage

    msgs = graph.get_state(config).values.get("messages", [])
    answered = {m.tool_call_id for m in msgs if isinstance(m, ToolMessage)}
    open_calls = [c for m in msgs for c in (getattr(m, "tool_calls", None) or []) if c["id"] not in answered]
    patch = [ToolMessage(content=json.dumps({"error": "the turn stopped before this call ran"}), name=c["name"],
                         tool_call_id=c["id"]) for c in open_calls]
    graph.update_state(config, {"messages": patch + [stop_message()]}, as_node=as_node)


# ----------------------------------------------------------------------------- 3. adk
def _adk_stop():
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types as gt
    return LlmResponse(content=gt.Content(role="model", parts=[gt.Part(text=STOP_ANSWER)]))


def adk_before_model(callback_context, llm_request):
    """Before ADK counts the call: refuse it with STOP_ANSWER, or give it this turn's timeout (in milliseconds)."""
    meter = meter_of(_request())
    if not meter.allow_model_call():
        return _adk_stop()
    if PROFILE == "gcp":
        from google.genai import types as gt
        llm_request.config = llm_request.config or gt.GenerateContentConfig()
        opts = llm_request.config.http_options or gt.HttpOptions()
        opts.timeout = int(meter.model_timeout_s() * 1000)
        llm_request.config.http_options = opts
    return None


def adk_after_model(callback_context, llm_response):
    """The call's tokens onto the Meter. Gemini counts thinking apart from the answer; both are billed as output."""
    u = getattr(llm_response, "usage_metadata", None)
    if u is not None:
        meter_of(_request()).charge_model(
            u.prompt_token_count or 0, (u.candidates_token_count or 0) + (u.thoughts_token_count or 0),
            u.cached_content_token_count or 0)
    return None


def adk_model_error(callback_context, llm_request, error):
    """A timed-out call ends the turn with STOP_ANSWER; any other error is ADK's to raise."""
    if not is_timeout(error):
        return None
    meter_of(_request()).stop("turn_deadline")
    return _adk_stop()
