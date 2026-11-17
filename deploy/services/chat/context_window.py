"""DocuMind chat service - the window: what one model call is sent of a conversation (workshop lesson 6.9).

NOTHING IN THE SERVICE IMPORTS THIS MODULE. Every brain still sends its model the whole thread on every call - the
LangGraph brain's node sends [SystemMessage(SYSTEM)] + state["messages"] (brains.py), create_agent sends its system
prompt and the state's messages - so a conversation's calls grow with every turn, and so does each call's bill. This is
the window a later change would put in front of the model, behind a switch that defaults to full (uplift H3); until
then the lesson's cells and make window-check (commands/window_check.py) run it, offline or with Gemini on your own
machine.

THE RECORD AND THE CALL. The checkpointer keeps every message of a thread (workshop lessons 6.5-6.8). The window decides
what one call is sent, from a copy, and writes nothing back: the thread, its checkpoints and the turn id
brains._summary() finds a turn by are untouched, so make thread still lists every message, and a turn writes the
checkpoints it wrote before (lesson 6.6's +3 and +5).

THE RULE, at every model call, over the messages the brain would send (its system prompt, then the thread):

    the floor        the system prompt and the newest turn - the person's latest message, and every call and result
                     since - are always sent, whole. A turn is never cut, so no call goes out without the results it
                     asked for.
    earlier turns    newest first, each is kept whole while the earlier turns fit in the history budget,
                     CHAT_HISTORY_TOKENS (2,000 by default: the history line of rag-api's TokenBudget, lesson 3.4). Each
                     is COMPACTED: a result whose status is not error becomes CLEARED, and its call stays, so the pair
                     is whole; a search is cheap to run again, and SYSTEM already asks for one on a follow-up. A
                     refusal stays as it is.
    brought forward  the earlier turns that do not fit leave the call. One line brings them forward, inside the same
                     budget, at the top of the first message kept after the system prompt: which turns, and the
                     questions asked in them - the newest that fit, oldest first, each with its turn's number. Code
                     writes it, not a model, so it costs nothing and invents nothing. It rides in a person's message,
                     never in the system prompt: the questions are the person's words, and the call never carries two
                     of the person's messages in a row, which no turn of the kit sends.
    write rules      what is carried from an earlier turn keeps to the Desk's rules for a person's words (workshop
                     lessons 5.6 and 10.4). Every earlier question, kept or brought forward, is masked (desk_rules.mask:
                     checked Aadhaar and card numbers) and cut to 300 characters (desk_router.PREV_CHARS, the previous
                     question the Desk keeps); the model's earlier answers are masked too. The newest question is masked
                     and sent whole (ChatRequest caps it at 4,000 characters). The newest turn's model messages and
                     results go as they are: Gemini 3 needs the thought signatures of the turn in progress
                     (langchain-google-genai 4.4.0, chat_models.py:1591).

So a call's context is at most its floor plus the budget - its CEILING - however long the thread grows, and the newest
turn and the system prompt are always in it. A turn is a person's message and everything after it, up to the next one.
A tool call and its result always share a turn (a result whose call sits in an earlier turn joins the turns between into
one), so keeping or dropping whole turns never splits a pair: no call is sent without the result the thread holds for
it, and no result without the call that asked for it. A call the thread itself left open - a turn cut off mid-flight -
is sent as it is and counted as unanswered in the report: closing it is limits.repair_thread()'s job, not the window's
(what Gemini answers to an open call is lesson 6.8's to show).

TOKENS are langchain-core's count_tokens_approximately: four characters a token and three a message, rounded up per
message, the counter trim_messages and the context-editing middleware default to. It is an estimate, not Gemini's
count, and the tool declarations every call also carries are outside it (lesson 6.1 measures them); make window-check
LIVE=1 prints Gemini's own input tokens beside it. Masking never lengthens a text (desk_rules.MASK_TEXT), so a masked
message is never bigger than the one stored.

THREE FORMS, one rule:

    window(messages)    the rule itself: (what the call is sent, a report). full(messages) changes nothing and
                        reports the same sizes: today's behaviour, measured
    windowed(llm)       a chat model with the window in front of it, for brains.LangChainBrain(saver, llm=...) or
                        LangGraphBrain's: the brain, its graph, its middleware and its checkpointer stay the kit's own.
                        make window-check builds its brains this way; each call's report lands in .calls
    middleware()        the window as create_agent middleware, the last in the list: wrap_model_call and
                        awrap_model_call only, on a copy of the request, so the agent's graph and its checkpoints are
                        the ones it had

plan() is the rule's arithmetic alone, on token counts; the page's interactive is a port of it.

NOT USED, AND WHY. langchain 1.4.0's ContextEditingMiddleware (agents/middleware/context_editing.py:187) does the
clearing alone: past its trigger (100,000 tokens by default) ClearToolUsesEdit (:58) puts "[cleared]" in all but the
newest three tool results, in wrap_model_call on a deep copy (:270), as this window does; it keeps every turn, so a call
still grows with the thread. SummarizationMiddleware is rejected: its before_model hook (summarization.py:398) replaces
the state's messages with a model-written summary (RemoveMessage(id=REMOVE_ALL_MESSAGES), :432), so the checkpoint
would lose the record, and the hook is a graph node of its own, one more checkpoint every model call. ADK has its own
compaction, App(events_compaction_config=EventsCompactionConfig(...)), marked @experimental in google-adk 2.8.0
(apps/_configs.py:49) and written by a model; the ADK brain keeps its own sessions, so this window does not reach it.
Desk threads (desk~ sessions, desk_graph.py) are not windowed: the Desk sends its models the turn's masked question,
never the thread (desk_agent.run(); the router's prompt holds the previous question, cut to 300 characters).

It lives beside the brains, not in shared/: its three forms are LangChain's (the messages, the token counter, a chat
model, create_agent middleware), it windows the chat brains' threads alone, and the Desk's 300 characters are read from
services/chat/desk_router.py, which shared/ cannot import. This module imports the standard library and the Desk's rules
(shared/desk_rules.py, desk_router.PREV_CHARS) at the top; LangChain is imported where it is used, so plan(), turns()
and carried() run without the chat image's pins. Verified offline on 12 October 2026 against langchain 1.4.0,
langchain-core 1.6.2 and langgraph 1.2.12 (commands/tests/test_context_window.py).
"""
from __future__ import annotations

import json
import math
import os
from typing import Any

from desk_router import PREV_CHARS            # services/chat/desk_router.py: the previous question the Desk keeps, 300
from shared import desk_rules, identifiers

MODES = ("full", "windowed")
HISTORY_TOKENS = int(os.environ.get("CHAT_HISTORY_TOKENS", "2000"))
CLEARED = json.dumps({"cleared": True, "reason": "evidence from an earlier turn: search again if you need it"})
# The line that brings the dropped turns forward. Each question carries its turn's number, so the model can tell the
# first question from the first one listed. window() reserves room for the longest form of the line, every number at
# its widest, so the line sent is never bigger than the room plan() gave it.
LINE_HEAD = "[Earlier in this conversation, not shown here: {turns}."
LINE_ALL = " The person asked:"
LINE_SOME = " The person asked, in {turns}:"
LINE_TAIL = " Search again for anything you need from them.]"


# ----------------------------------------------------------------------------- the arithmetic
def plan(earlier: list[int], questions: list[list[int]], budget: int, head: int) -> tuple[int, int, bool]:
    """(how many earlier turns are kept whole - the newest, how many questions the line lists - the newest of the
    dropped turns', whether the line is sent). earlier[i] is turn i's tokens as the window sends it, oldest first;
    questions[i] what each of its questions adds to the line; head the line's tokens with no question in it. Every
    count is an integer, and nothing else is read: this is the whole rule's arithmetic."""
    if sum(earlier) <= budget:
        return len(earlier), 0, False          # everything earlier fits: nothing is dropped, so there is no line
    line = head <= budget                      # a budget too small for the line drops the turns without one
    room, kept = budget - (head if line else 0), 0
    for size in reversed(earlier):             # newest first, whole turns only, and none once one does not fit
        if size > room:
            break
        room -= size
        kept += 1
    if not line:
        return kept, 0, False
    listed = 0
    for size in reversed([q for qs in questions[:len(earlier) - kept] for q in qs]):
        if size > room:
            break
        room -= size
        listed += 1
    return kept, listed, True


# ----------------------------------------------------------------------------- the messages
def text_of(content) -> str:
    """A message's text: Gemini 3 can send a list of blocks where older models sent a string (as brains._summary)."""
    if isinstance(content, str):
        return content
    return "".join(b if isinstance(b, str) else b.get("text", "") for b in content or []
                   if isinstance(b, str) or (isinstance(b, dict) and b.get("type") == "text"))


def _kind(m) -> str:
    return getattr(m, "type", "")


def turns(thread: list) -> list[list]:
    """The thread's turns, oldest first: a person's message and every message after it up to the next one; messages
    before the first person's message are a turn of their own. A result whose call sits in an earlier turn joins the
    turns between into one, so a call and its result are never in two turns."""
    if not thread:
        return []
    starts = [i for i, m in enumerate(thread) if _kind(m) == "human"]
    if not starts or starts[0] != 0:
        starts = [0] + starts
    spans: list[list[int]] = []
    asked: dict = {}                                  # call id -> the index of the message that asked it
    for a, b in zip(starts, starts[1:] + [len(thread)]):
        spans.append([a, b])
        for i in range(a, b):
            m = thread[i]
            for c in getattr(m, "tool_calls", None) or []:
                if c.get("id"):
                    asked[c["id"]] = i
            at = asked.get(getattr(m, "tool_call_id", None)) if _kind(m) == "tool" else None
            while at is not None and spans[-1][0] > at:      # the call is in an earlier turn: join them
                last = spans.pop()
                spans[-1][1] = last[1]
    return [thread[a:b] for a, b in spans]


def _mask(text: str) -> tuple[str, int]:
    """(the text with every checked Aadhaar and card number masked, how many). desk_rules.mask() does the masking."""
    found = len(identifiers.find_numbers(text))
    return (desk_rules.mask(text)[0], found) if found else (text, 0)


def _masked(content) -> tuple[Any, int]:
    """A message's content masked, block by block; other blocks (a thought signature, an image) as they are."""
    if isinstance(content, str):
        return _mask(content)
    out, n = [], 0
    for b in content or []:
        if isinstance(b, str):
            b, k = _mask(b)
        elif isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str):
            text, k = _mask(b["text"])
            b = {**b, "text": text} if k else b
        else:
            k = 0
        out.append(b)
        n += k
    return (out, n) if n else (content, 0)


def carried(question: str) -> tuple[str, int, bool]:
    """An earlier question as the window carries it, the Desk's way: masked, then cut to PREV_CHARS (desk.py's
    prev_question). Returns (the text, how many numbers were masked, whether it was cut)."""
    masked, n = _mask(question)
    return masked[:PREV_CHARS], n, len(masked) > PREV_CHARS


def _copy(m, content):
    return m if content is m.content else m.model_copy(update={"content": content})


def _masked_calls(m) -> tuple[list, int]:
    """A model message's tool calls with every checked number in their string arguments masked (13 October 2026: a card
    number a person wrote came back whole in the search query the model built from it). (the calls, how many)."""
    calls, masked = [], 0
    for c in getattr(m, "tool_calls", None) or []:
        args = {}
        for key, value in (c.get("args") or {}).items():
            value, n = _mask(value) if isinstance(value, str) else (value, 0)
            args[key] = value
            masked += n
        calls.append({**c, "args": args})
    return calls, masked


def _compact(unit: list) -> dict:
    """An earlier turn as the window would keep it: its results cleared, its questions carried, its answers masked."""
    out, questions, masked, cut, cleared = [], [], 0, 0, 0
    for m in unit:
        kind = _kind(m)
        if kind == "human":
            q, n, was_cut = carried(text_of(m.content))
            questions.append((q, n, was_cut))
            masked, cut = masked + n, cut + was_cut
            out.append(m if q == m.content else m.model_copy(update={"content": q}))
        elif kind == "tool" and getattr(m, "status", "success") != "error":
            out.append(m.model_copy(update={"content": CLEARED, "artifact": None}))
            cleared += 1
        elif kind in ("ai", "tool"):                        # an answer, a call's words and arguments, a refusal: masked
            content, n = _masked(m.content)
            calls, k = _masked_calls(m)
            masked += n + k
            out.append(_copy(m, content) if not k else m.model_copy(update={"content": content, "tool_calls": calls}))
        else:
            out.append(m)
    return {"messages": out, "questions": questions, "masked": masked, "cut": cut, "cleared": cleared}


def _newest(unit: list) -> tuple[list, int, int]:
    """The newest turn as it is sent: its question masked and whole; any earlier question a join pulled in is carried;
    the model's messages and the results as they are. Returns (the messages, numbers masked, questions cut)."""
    last = max((i for i, m in enumerate(unit) if _kind(m) == "human"), default=None)
    out, masked, cut = [], 0, 0
    for i, m in enumerate(unit):
        if _kind(m) != "human":
            out.append(m)
        elif i == last:
            content, n = _masked(m.content)
            masked += n
            out.append(_copy(m, content))
        else:
            q, n, was_cut = carried(text_of(m.content))
            masked, cut = masked + n, cut + was_cut
            out.append(m if q == m.content else m.model_copy(update={"content": q}))
    return out, masked, cut


def _turns(first: int, last: int) -> str:
    return f"turn {first}" if first == last else f"turns {first} to {last}"


def _line(dropped: int, shown: list[tuple], asked: int) -> str:
    """The line that brings turns 1 to dropped forward: shown is (turn, question) for each question it lists, oldest
    first, of the asked questions those turns hold."""
    out = LINE_HEAD.format(turns=_turns(1, dropped))
    if shown:
        out += LINE_ALL if len(shown) == asked else LINE_SOME.format(turns=_turns(shown[0][0], shown[-1][0]))
        out += "".join(_item(t, q) for t, q in shown)
    return out + LINE_TAIL


def _widest_line(widest: int) -> str:
    """The line's longest form with no question in it, every number as wide as the thread's turn count: the reserve."""
    return (LINE_HEAD.format(turns=f"turns 1 to {widest}") + LINE_SOME.format(turns=f"turns {widest} to {widest}")
            + LINE_TAIL)


def _item(turn: int, question: str) -> str:
    return f" ({turn}) {json.dumps(question, ensure_ascii=False)}"


def _prefix(m, line: str):
    """The line at the top of the first message kept after the system prompt, a paragraph of its own."""
    if isinstance(m.content, str):
        return m.model_copy(update={"content": f"{line}\n\n{m.content}"})
    return m.model_copy(update={"content": [{"type": "text", "text": line}] + list(m.content or [])})


def _open_calls(messages: list) -> int:
    """Calls in these messages with no result among them: a turn the thread itself left open."""
    answered = {getattr(m, "tool_call_id", None) for m in messages if _kind(m) == "tool"}
    return sum(1 for m in messages for c in getattr(m, "tool_calls", None) or [] if c.get("id") not in answered)


def _counter(count):
    if count is not None:
        return count
    from langchain_core.messages.utils import count_tokens_approximately
    return count_tokens_approximately


def _tokens(messages: list, count) -> int:
    return sum(count([m]) for m in messages)


def tokens(messages, count=None) -> int:
    """The window's estimate of these messages' tokens: each message counted on its own, and the counts added."""
    return _tokens(list(messages), _counter(count))


def _split(messages) -> tuple[list, list]:
    """(the system prompt - the leading system messages, the thread)."""
    msgs = list(messages)
    lead = 0
    while lead < len(msgs) and _kind(msgs[lead]) == "system":
        lead += 1
    return msgs[:lead], msgs[lead:]


def _budget(history_tokens) -> int:
    return max(0, int(HISTORY_TOKENS if history_tokens is None else history_tokens))


# ----------------------------------------------------------------------------- 1. the rule
def window(messages, *, history_tokens: int | None = None, count=None) -> tuple[list, dict]:
    """(what one model call is sent, the report): the system prompt and the newest turn whole, the earlier turns that
    fit in the history budget compacted, the rest brought forward in one line, every earlier question masked and cut to
    300 characters. messages is what the brain would send, its system prompt first. Nothing given is changed: every
    message that differs is a copy."""
    from langchain_core.messages import HumanMessage

    count, budget = _counter(count), _budget(history_tokens)
    system, thread = _split(messages)
    units = turns(thread)
    newest, masked, cut = _newest(units[-1]) if units else ([], 0, 0)
    comp = [_compact(u) for u in units[:-1]]
    widest = max(len(units), 1)                  # no turn number in the line is wider than the thread's turn count
    head = count([HumanMessage(content=_widest_line(widest))])
    sizes = [_tokens(c["messages"], count) for c in comp]
    items = [[math.ceil(len(_item(widest, q)) / 4) for q, _, _ in c["questions"]] for c in comp]
    kept, listed, has_line = plan(sizes, items, budget, head)

    dropped, keep = comp[:len(comp) - kept], comp[len(comp) - kept:]
    body = [m for c in keep for m in c["messages"]] + newest
    for c in keep:
        masked, cut = masked + c["masked"], cut + c["cut"]
    line = None
    if has_line:
        questions = [(t, q, n, was_cut) for t, c in enumerate(dropped, 1) for q, n, was_cut in c["questions"]]
        shown = questions[len(questions) - listed:] if listed else []
        for _, _, n, was_cut in shown:
            masked, cut = masked + n, cut + was_cut
        line = _line(len(dropped), [(t, q) for t, q, _, _ in shown], len(questions))
        if body and _kind(body[0]) == "human":
            body[0] = _prefix(body[0], line)
        else:                                     # not reached from a kit thread: a dropped turn means a person's
            body.insert(0, HumanMessage(content=line))       # message opens what is kept
    sent = system + body
    floor = _tokens(system, count) + _tokens(newest, count)
    context = _tokens(sent, count)
    return sent, {"mode": "windowed", "budget": budget, "system_tokens": _tokens(system, count),
                  "floor_tokens": floor, "ceiling": floor + budget, "context_tokens": context,
                  "earlier_tokens": context - floor, "context_messages": len(sent),
                  "thread_messages": len(thread), "thread_tokens": _tokens(thread, count), "turns": len(units),
                  "kept": kept, "brought_forward": len(dropped), "listed": listed, "line": line,
                  "cleared": sum(c["cleared"] for c in keep), "masked": masked, "cut": cut,
                  "unanswered": _open_calls(body)}


def full(messages, *, history_tokens: int | None = None, count=None) -> tuple[list, dict]:
    """What the brains send today, unchanged - the same list, the same messages - with the window's report of its sizes:
    the same floor and ceiling, every earlier turn kept as it is, nothing cleared, masked or cut."""
    count, budget = _counter(count), _budget(history_tokens)
    msgs = messages if isinstance(messages, list) else list(messages)
    system, thread = _split(msgs)
    units = turns(thread)
    floor = _tokens(system, count) + (_tokens(units[-1], count) if units else 0)
    context = _tokens(msgs, count)
    return msgs, {"mode": "full", "budget": budget, "system_tokens": _tokens(system, count),
                      "floor_tokens": floor, "ceiling": floor + budget, "context_tokens": context,
                      "earlier_tokens": context - floor, "context_messages": len(msgs),
                      "thread_messages": len(thread), "thread_tokens": _tokens(thread, count), "turns": len(units),
                      "kept": max(len(units) - 1, 0), "brought_forward": 0, "listed": 0, "line": None,
                      "cleared": 0, "masked": 0, "cut": 0, "unanswered": _open_calls(thread)}


def _apply(mode: str):
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, not {mode!r}")
    return window if mode == "windowed" else full


# ----------------------------------------------------------------------------- 2. in front of a brain's model
def windowed(llm, mode: str = "windowed", *, history_tokens: int | None = None, count=None, calls: list | None = None):
    """llm with the window in front of it: the model a brain is built with - brains.LangChainBrain(saver,
    llm=windowed(llm)), or LangGraphBrain's - so the brain, its graph, its middleware and its checkpointer stay the
    kit's own, and only what each call is sent changes. mode full sends what the brain sends, untouched, and still
    reports it. Each call's report is appended to .calls (the list given, or a new one), which the copies bind_tools
    makes share."""
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.outputs import ChatGeneration, ChatResult

    apply = _apply(mode)

    class Windowed(BaseChatModel):
        inner: Any
        calls: Any = None                       # Any, not list: pydantic would copy a list, and the copies share it

        @property
        def _llm_type(self) -> str:
            return "documind-context-window"

        def bind_tools(self, tools, **kwargs):
            return self.model_copy(update={"inner": self.inner.bind_tools(tools, **kwargs)})

        def _send(self, messages):
            sent, report = apply(messages, history_tokens=history_tokens, count=count)
            self.calls.append(report)
            return sent

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            msg = self.inner.invoke(self._send(messages), stop=stop, **kwargs)
            return ChatResult(generations=[ChatGeneration(message=msg)])

        async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
            msg = await self.inner.ainvoke(self._send(messages), stop=stop, **kwargs)
            return ChatResult(generations=[ChatGeneration(message=msg)])

    return Windowed(inner=llm, calls=calls if calls is not None else [])


# ----------------------------------------------------------------------------- 3. create_agent middleware
def middleware(mode: str = "windowed", *, history_tokens: int | None = None, count=None, calls: list | None = None):
    """The window as create_agent middleware, to go last in the list (brains.LangChainBrain's would then be
    [limits.TurnLimitsMiddleware(), the guard, this]): the turn's limits are checked, and its tokens charged, around the
    call it wraps. wrap_model_call and awrap_model_call only, on request.override(messages=...): a before_model or
    after_model hook would be a graph node, and every turn would write more checkpoints (limits.TurnLimitsMiddleware
    says the same). Each call's report is appended to .calls."""
    from langchain.agents.middleware import AgentMiddleware

    apply = _apply(mode)
    reports = calls if calls is not None else []

    class ContextWindowMiddleware(AgentMiddleware):
        def __init__(self):
            super().__init__()
            self.calls = reports

        def _request(self, request):
            head = [request.system_message] if request.system_message is not None else []
            sent, report = apply(head + list(request.messages), history_tokens=history_tokens, count=count)
            reports.append(report)
            return request.override(messages=list(sent[len(head):]))

        def wrap_model_call(self, request, handler):
            return handler(self._request(request))

        async def awrap_model_call(self, request, handler):
            return await handler(self._request(request))

    return ContextWindowMiddleware()
