#!/usr/bin/env python3
"""What rides each model call of one turn, by source, with its tokens and rupees (workshop lesson 6.1).

    python commands/context_sources.py --offline [--brain B] [--desk D] [--turns N] [--top-k K] [--question Q] [--json]
    python commands/context_sources.py [--brain B] ...    # your lane: GOOGLE_CLOUD_PROJECT, RAG_API_URL and
                                                          # DOCUMIND_IMPERSONATE_SA set, as make context-sources sets them
    make context-sources [BRAIN=] [DESK=] [TURNS=] [TOP_K=] [Q=] [OFFLINE=1]   # the same, in ~/graph-venv (mk/memory.mk)

A brain sends its model far more than the question, and sends most of it again with every call of the turn:

    system prompt       the instructions: brains.SYSTEM for langchain and langgraph; for adk the agent's instruction,
                        brains.SYSTEM, after which ADK adds a line of its own naming the agent (google-adk 2.8.0,
                        flows/llm_flows/identity.py); desk_agent.system_prompt() for a desk
    tool declarations   every tool the model may call, as its adapter serialises it. langchain-google-genai converts the
                        bound tools with convert_to_genai_function_declarations (_function_utils.py:219): parameters as a
                        Gemini Schema. ADK's FunctionTool declares parametersJsonSchema, with titles and defaults
    thread so far       the earlier turns of the conversation: their questions, the model's calls, the results, answers
    question            this turn's question
    the model's calls   the function calls the model made earlier in this turn, sent back with every later call
    tool results        what those calls returned: a search's citations (a desk's search: each passage's full text)

HOW IT READS A CALL. Every brain's model call goes through google-genai: LangChain's ChatGoogleGenerativeAI calls
Models.generate_content (langchain-google-genai 4.4.0, chat_models.py:4177) and ADK's Gemini AsyncModels.
generate_content (google-adk 2.8.0, models/google_llm.py:322). For the run the command wraps both, so it reads what
each adapter handed the SDK - the system instruction, the declarations, the contents - and what came back. A request's
contents split at the turn's question: the last user content whose text is the question (or failing that the last
user content with text and no function response, which is how langchain-google-genai finds a turn's start,
chat_models.py:1597-1616). Before it is the thread; after it, a model content is the model's calls and a function
response a tool result. Anything else is "other": none of these brains sends any.

BRAIN: langchain (the default), langgraph, adk, direct or desk, as services/chat builds them (brains.build(); for desk,
desk_agent.run() on DESK=statute, handbook or astar, with no router in front: the desk is chosen, not routed, and the
router's own call is not measured). The chat brains keep their thread in a local InMemorySaver (ADK in its in-memory
session service), so a lane's threads are never read or written. TURNS=2 or 3 asks one or two earlier questions on the
same thread first (EARLIER), so the thread rides too; direct keeps no thread and a desk agent runs with none
(checkpointer=False), so both take one turn only. TOP_K=K sends top_k K with every search of the run, whatever the
model asked (tools.py declares top_k with a default of 5; the declaration is unchanged): lesson 6.1's Change-it.

WHAT A SEARCH RETURNS DIFFERS BY LANE, and with it what TOP_K moves. On your lane a chat brain's search is rag-api's
/v1/query, which answers with its own model call (generator.py) and returns the citations that answer chose
(shared/documind_schemas.resolve: a quote each, at most twenty-five words by rule 5 of generator.SYSTEM); the model's
tool result is those quotes, and TOP_K moves rag-api's own prompt, the chunks it packs, more than it moves them. A
desk's search is /v1/passages: every passage's full text and no model call, so TOP_K moves its results directly. The
direct brain makes no model call of its own on the lane: rag-api's answer is the turn, and its cost is the turn's.

OFFLINE=1 makes no network connection (a socket that would leave the machine is refused; loopback stays, asyncio's
own pipe on Windows uses it), mints no token, sets the placeholder project and counts nothing on the lane. The model
is a script answering at the google-genai boundary: search for the question, then answer from the first passage
found, "(offline, scripted)". So the brain, its adapter, its tools and its limits run as on the lane, and only the
reply is the script's. A search is the Rs 0 lane's: documind_tools.retrieve on the local profile, its BM25 ranking and
evidence gate, over the tenant's chunks of evals/corpus held in memory (agent_patterns.offline()). It returns every
one of the top_k passages, each quote cut to the sentences that carry the question (at most 500 characters), as if
rag-api's answer had cited every chunk it packed; the answer and the usage rag-api would add are estimated from
generator.py's own prompt - its SYSTEM, the chunks context_budget.pack_chunks fits in what generator._budget leaves of
config.py's max_context_tokens, the question - read from rag-api's source (literals only). Every count offline is an
estimate: a quarter of the characters each part carries, at least 1 (rag-api's own estimator,
context_budget.estimate_tokens; nothing for an empty part), over a text part's text, a call's name and JSON
arguments, a result's name and JSON response, a declaration's JSON as the SDK serialises it. The script's input is
the sum of those parts, so the residual is 0 offline. The rupees are list price on the estimate; nothing is billed.

ON YOUR LANE the turn is real: Gemini through the brain's own model (location global), each search on your lane's
rag-api as documind-ui-sa, under the chat service's limits (12 calls, Rs 5, 100 s). Each call's input, cached,
output and thinking tokens are its usage_metadata's, and its rupees are those at list price (shared/prices.py, as the
turn's limits.Meter charges them). Then each source is counted by the model's own count_tokens on location global,
which is not billed: the question alone, then with the thread before it, with the system instruction, with the
declarations (CountTokensConfig's system_instruction and tools, google-genai 2.22.0 types.py:11617), then with each
content after the question in turn. Each source's tokens are what adding it adds, so they sum to the request's own
count, and the residual is what the call billed less what was counted. A field count_tokens refuses, or counts as
nothing, is estimated instead, marked ~, and named in the probe; a content it refuses ends the counting of contents,
and it and those after it are estimated. Workshop lesson 6.1's batch 1 probe is this run: whether count_tokens with
tools and a system instruction is honoured on location global, and how far its count is from what the call billed.

--json prints the record (every call, its sources, the searches, the totals, the probe) as one JSON object.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import importlib.util
import json
import os
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
for _p in (str(HERE), str(KIT / "services" / "chat"), str(KIT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared import prices  # noqa: E402 - the standard library only

PLACEHOLDER = "documind-ai-YOUR-ID"
BRAINS = ("langchain", "langgraph", "adk", "direct", "desk")
DESKS = ("statute", "handbook", "astar")
QUESTION = "After how many years of continuous service is gratuity payable?"
# TURNS=2 or 3 asks these first, on the same thread: a handbook question and a follow-up on gratuity, both answered
# from acme's corpus offline.
EARLIER = ("How many days of earned leave can I carry forward?", "Is gratuity payable to a contract employee?")
SOURCES = ("system", "tools", "thread", "question", "calls", "results", "other")
LABELS = {"system": "system prompt", "tools": "tool declarations", "thread": "thread so far", "question": "question",
          "calls": "the model's calls", "results": "tool results", "other": "other"}
LIVE_ENV = ("GOOGLE_CLOUD_PROJECT", "RAG_API_URL", "DOCUMIND_IMPERSONATE_SA")
RAG_API = KIT / "services" / "rag-api"
TOP_K_MAX = 20                  # rag-api's QueryRequest.top_k (le=20); documind_tools.retrieve clamps to it


class Refused(Exception):
    """A run this command turns down, with the reason to print."""


# ----------------------------------------------------------------------------- the offline estimator
_RAG: dict = {}


def context_budget():
    """services/rag-api/context_budget.py, loaded by its path: the standard library only, and the module rag-api packs
    its own prompt with."""
    if "cb" not in _RAG:
        name = "documind_rag_context_budget"
        spec = importlib.util.spec_from_file_location(name, RAG_API / "context_budget.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod                    # its dataclass looks its annotations up through sys.modules
        spec.loader.exec_module(mod)
        _RAG["cb"] = mod
    return _RAG["cb"]


def tokens(text: str) -> int:
    """OFFLINE=1's count of one part: rag-api's own estimator (a quarter of the characters, at least 1), and nothing
    for an empty part."""
    return context_budget().estimate_tokens(text) if text else 0


def part_text(part: dict) -> str:
    """The characters one part carries, as the estimate reads it: a text part's text, a call's name and its JSON
    arguments, a result's name and its JSON response."""
    if "function_call" in part:
        call = part["function_call"]
        return (call.get("name") or "") + json.dumps(call.get("args") or {}, ensure_ascii=False)
    if "function_response" in part:
        res = part["function_response"]
        return (res.get("name") or "") + json.dumps(res.get("response") or {}, ensure_ascii=False)
    return part.get("text") or ""


def declaration_text(decl: dict) -> str:
    return json.dumps(decl, ensure_ascii=False)


def content_tokens(content: dict) -> int:
    return sum(tokens(part_text(p)) for p in content["parts"])


def request_tokens(req: dict) -> int:
    """A whole request, estimated part by part: what OFFLINE=1's script reports it was sent."""
    return (tokens(req["system"]) + sum(tokens(declaration_text(d)) for d in req["tools"])
            + sum(content_tokens(c) for c in req["contents"]))


# ----------------------------------------------------------------------------- one request, as plain data
def system_text(si) -> str:
    """A system instruction's text, in whichever form the SDK takes it: a string (ADK's), a Content (LangChain's), a
    Part or a list of them."""
    if si is None:
        return ""
    if isinstance(si, str):
        return si
    if isinstance(si, (list, tuple)):
        return "".join(system_text(x) for x in si)
    parts = getattr(si, "parts", None)
    if parts is not None:
        return "".join(p.text or "" for p in parts)
    return getattr(si, "text", None) or ""


def plain_part(p) -> dict:
    """One google-genai Part as JSON-ready data. A thought signature is noted, never copied: it is opaque bytes."""
    out: dict = {}
    if p.function_call is not None:
        out["function_call"] = {"name": p.function_call.name, "args": copy.deepcopy(p.function_call.args or {})}
    elif p.function_response is not None:
        out["function_response"] = {"name": p.function_response.name,
                                    "response": copy.deepcopy(p.function_response.response or {})}
    elif p.text is not None:
        out["text"] = p.text
    else:
        out["other"] = sorted(k for k, v in p.model_dump(exclude_none=True).items() if v not in (None, b"", ""))
    if p.thought_signature:
        out["signed"] = True
    if p.thought:
        out["thought"] = True
    return out


def plain_request(model: str, contents: list, system, tools) -> dict:
    """What one generate_content call was handed, as data: the model, the system instruction's text, each function
    declaration as the SDK serialises it (camelCase, empty fields left out), and the contents."""
    decls = []
    for tool in tools or []:
        for d in getattr(tool, "function_declarations", None) or []:
            decls.append(d.model_dump(mode="json", exclude_none=True, by_alias=True))
    return {"model": model, "system": system_text(system), "tools": decls,
            "contents": [{"role": c.role, "parts": [plain_part(p) for p in c.parts or []]} for c in contents]}


# ----------------------------------------------------------------------------- the sources of one request
def _text_of(content: dict) -> str:
    return "".join(p.get("text") or "" for p in content["parts"] if "text" in p)


def _asks(content: dict) -> bool:
    parts = content["parts"]
    return (content["role"] == "user" and any("text" in p for p in parts)
            and not any("function_response" in p for p in parts))


def question_index(contents: list[dict], question: str | None = None) -> int:
    """The turn's question: the last user content whose text is the question; failing that, the last user content with
    text and no function response."""
    if question is not None:
        hit = [i for i, c in enumerate(contents) if _asks(c) and _text_of(c) == question]
        if hit:
            return hit[-1]
    hit = [i for i, c in enumerate(contents) if _asks(c)]
    if not hit:
        raise ValueError("no user content asks anything: a request with no question")
    return hit[-1]


def label(contents: list[dict], question: str | None = None) -> list[str]:
    """Each content's source, one label a content: thread before the question, the question, then the model's calls,
    tool results, or other."""
    qi = question_index(contents, question)
    out = []
    for i, c in enumerate(contents):
        if i < qi:
            out.append("thread")
        elif i == qi:
            out.append("question")
        elif c["role"] == "model":
            out.append("calls")
        elif any("function_response" in p for p in c["parts"]):
            out.append("results")
        else:
            out.append("other")
    return out


def estimated_sources(req: dict, labels: list[str]) -> dict:
    """{source: tokens} for one request, each part estimated once and counted under its content's source."""
    out = dict.fromkeys(SOURCES, 0)
    out["system"] = tokens(req["system"])
    out["tools"] = sum(tokens(declaration_text(d)) for d in req["tools"])
    for content, where in zip(req["contents"], labels):
        out[where] += content_tokens(content)
    return out


# ----------------------------------------------------------------------------- counting on the lane
def describe(err: BaseException) -> str:
    """An error in one line: google-genai's APIError as its code, status and message."""
    code, status = getattr(err, "code", None), getattr(err, "status", None)
    said = getattr(err, "message", None) or str(err)
    head = " ".join(str(x) for x in (code, status) if x) or type(err).__name__
    return " ".join(f"{head}: {said}".split())[:240]


class Counter:
    """count(contents, system, tools) -> tokens, each distinct request asked once (a turn's calls share their
    prefixes). The memo is keyed by the plain contents, so a refusal is asked once and raised again from memory."""

    def __init__(self, count):
        self.count, self.memo, self.asked = count, {}, 0

    def __call__(self, raw: list, plain: list, system=None, tools=None) -> int:
        key = (json.dumps(plain, sort_keys=True, default=str), system is not None, bool(tools))
        if key not in self.memo:
            self.asked += 1
            try:
                got = self.count(raw, system, tools)
                if got is None:
                    raise ValueError("count_tokens answered with no total")
                self.memo[key] = int(got)
            except Exception as exc:              # noqa: BLE001 - a refusal is the probe's answer, never the turn's
                self.memo[key] = exc
        hit = self.memo[key]
        if isinstance(hit, Exception):
            raise hit
        return hit


def counted_pieces(raw: dict, req: dict, labels: list[str], counter: Counter) -> tuple[list, dict]:
    """One request's sources counted in context: [(source, tokens, counted?, content index or None)] in the order they
    were added - the question alone, then the thread before it, the system instruction, the declarations, then each
    content after the question - and the probe: what count_tokens did with the system instruction and the
    declarations. A piece's tokens are what adding it added, so the pieces sum to the request's count."""
    contents, plain = raw["contents"], req["contents"]
    qi = labels.index("question")
    probe = {"system": None, "tools": None, "contents": None}
    est_s = tokens(req["system"])
    est_t = sum(tokens(declaration_text(d)) for d in req["tools"])

    def ask(idx: list, system=None, tools=None):
        try:
            return counter([contents[i] for i in idx], [plain[i] for i in idx], system, tools), None
        except Exception as exc:                  # noqa: BLE001
            return None, exc

    got, err = ask([qi])
    if err is not None:                           # the contents themselves refused: every source estimated
        probe["contents"] = probe["system"] = probe["tools"] = f"refused: {describe(err)}"
        pieces = [(labels[i], content_tokens(plain[i]), False, i) for i in range(len(plain))]
        return pieces + [("system", est_s, False, None), ("tools", est_t, False, None)], probe
    pieces, at, kept, contents_ok = [("question", got, True, qi)], got, [qi], True
    if qi:
        got, err = ask(list(range(qi + 1)))
        if err is None:
            pieces.append(("thread", got - at, True, None))
            at, kept = got, list(range(qi + 1))
        else:
            contents_ok = False
            probe["contents"] = f"refused the thread: {describe(err)}"
            pieces += [("thread", content_tokens(plain[i]), False, i) for i in range(qi)]
    system, tools = raw["system"], raw["tools"]
    if system is not None and req["system"]:
        got, err = ask(kept, system)
        if err is None and got > at:
            probe["system"] = f"honoured: +{got - at:,}"
            pieces.append(("system", got - at, True, None))
            at = got
        else:
            probe["system"] = f"refused: {describe(err)}" if err is not None else "accepted, but counted as nothing"
            pieces.append(("system", est_s, False, None))
            system = None
    if tools and req["tools"]:
        got, err = ask(kept, system, tools)
        if err is None and got > at:
            probe["tools"] = f"honoured: +{got - at:,}"
            pieces.append(("tools", got - at, True, None))
            at = got
        else:
            probe["tools"] = f"refused: {describe(err)}" if err is not None else "accepted, but counted as nothing"
            pieces.append(("tools", est_t, False, None))
            tools = None
    for i in range(qi + 1, len(plain)):
        if contents_ok:
            got, err = ask(kept + [i], system, tools)
            if err is None:
                pieces.append((labels[i], got - at, True, i))
                at, kept = got, kept + [i]
                continue
            contents_ok = False
            probe["contents"] = f"refused a content after the question: {describe(err)}"
        pieces.append((labels[i], content_tokens(plain[i]), False, i))
    return pieces, probe


def count_tokens_on(client, model: str):
    """The live count: the model's own count_tokens, with the system instruction and the declarations in its config."""
    from google.genai import types

    def count(contents: list, system=None, tools=None) -> int:
        config = types.CountTokensConfig(system_instruction=system, tools=tools) if (system is not None or tools) else None
        return client.models.count_tokens(model=model, contents=contents, config=config).total_tokens
    return count


# ----------------------------------------------------------------------------- the capture, at the google-genai boundary
def reply_of(response) -> dict:
    """What a call answered: its text (thoughts left out) and the function calls it asked for."""
    cands = getattr(response, "candidates", None) or []
    parts = (cands[0].content.parts if cands and cands[0].content else None) or []
    return {"text": "".join(p.text for p in parts if p.text and not p.thought),
            "calls": [{"name": p.function_call.name, "args": dict(p.function_call.args or {})}
                      for p in parts if p.function_call is not None]}


class Calls:
    """Every generate_content call made while installed, as the SDK was handed it (copied at the call) and what came
    back. With a script, the script answers in the model's place (OFFLINE=1); without one the real call is made."""

    def __init__(self, script=None):
        self.script, self.made, self.turn = script, [], 0

    def _record(self, model, contents, config) -> dict:
        from google.genai import _transformers as t
        from google.genai import types
        if not (isinstance(contents, list) and all(isinstance(c, types.Content) for c in contents)):
            contents = t.t_contents(contents)
        system = getattr(config, "system_instruction", None)
        tools = getattr(config, "tools", None)
        raw = {"model": model, "contents": copy.deepcopy(list(contents)), "system": copy.deepcopy(system),
               "tools": copy.deepcopy(list(tools)) if tools else None}
        entry = {"n": len(self.made) + 1, "turn": self.turn, "model": model, "raw": raw,
                 "request": plain_request(model, raw["contents"], system, tools)}
        self.made.append(entry)
        return entry

    @staticmethod
    def _answered(entry: dict, response):
        u = getattr(response, "usage_metadata", None)

        def n(key):
            return int(getattr(u, key, None) or 0)
        entry["usage"] = {"input": n("prompt_token_count"), "cached": n("cached_content_token_count"),
                          "visible": n("candidates_token_count"), "thinking": n("thoughts_token_count")}
        entry["reply"] = reply_of(response)
        return response

    @contextlib.contextmanager
    def installed(self):
        from google.genai import models as gm
        real_sync, real_async = gm.Models.generate_content, gm.AsyncModels.generate_content
        calls = self

        def generate_content(self_, *, model, contents, config=None):
            entry = calls._record(model, contents, config)
            try:
                got = calls.script(entry["request"]) if calls.script else real_sync(self_, model=model, contents=contents,
                                                                                   config=config)
            except Exception as exc:              # noqa: BLE001 - noted on the call, then raised as it was
                entry["error"] = describe(exc)
                raise
            return calls._answered(entry, got)

        async def agenerate_content(self_, *, model, contents, config=None):
            entry = calls._record(model, contents, config)
            try:
                got = (calls.script(entry["request"]) if calls.script else
                       await real_async(self_, model=model, contents=contents, config=config))
            except Exception as exc:              # noqa: BLE001
                entry["error"] = describe(exc)
                raise
            return calls._answered(entry, got)

        gm.Models.generate_content, gm.AsyncModels.generate_content = generate_content, agenerate_content
        try:
            yield self
        finally:
            gm.Models.generate_content, gm.AsyncModels.generate_content = real_sync, real_async


# ----------------------------------------------------------------------------- offline: the script and the Rs 0 lane
def script_step(req: dict) -> dict:
    """OFFLINE=1's model: search for the turn's question until a search has answered, then answer from the first
    passage it returned. {"text", "calls": [{name, args}]}."""
    contents = req["contents"]
    qi = question_index(contents)
    found = [p["function_response"].get("response") or {} for c in contents[qi + 1:] for p in c["parts"]
             if "function_response" in p]
    if not found:
        return {"text": "", "calls": [{"name": "retrieve", "args": {"query": _text_of(contents[qi])}}]}
    hits = found[-1].get("citations") or found[-1].get("passages") or []
    if not hits:
        return {"text": "(offline, scripted) The search found nothing to cite, so the documents give no answer.",
                "calls": []}
    said = " ".join(str(hits[0].get("quote") or hits[0].get("text") or "").split())
    said = said if len(said) <= 150 else said[:147].rstrip() + "..."
    return {"text": f'(offline, scripted) The first passage says: "{said}" [{hits[0].get("n") or 1}]', "calls": []}


def scripted(req: dict):
    """script_step() as the GenerateContentResponse Gemini would send: the reply's parts, and usage_metadata whose
    prompt_token_count is the request's estimate and whose candidates_token_count is the reply's. No thinking."""
    from google.genai import types
    step = script_step(req)
    parts = ([types.Part(text=step["text"])] if step["text"] else []) + [
        types.Part(function_call=types.FunctionCall(name=c["name"], args=c["args"])) for c in step["calls"]]
    sent = request_tokens(req)
    written = tokens(step["text"]) + sum(tokens(part_text({"function_call": c})) for c in step["calls"])
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=parts),
                                    finish_reason=types.FinishReason.STOP)],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=sent, candidates_token_count=written, total_token_count=sent + written))


@contextlib.contextmanager
def offline_lane():
    """OFFLINE=1's process: the placeholder project and no checkpoint DSN, no network but loopback, no identity token,
    count_tokens refused (offline counts are the estimator's), and the Rs 0 lane's retrieve over evals/corpus held in
    memory. Everything it changes is put back on the way out."""
    import agent_patterns as ap
    import thread_replay as rp
    from google.genai import models as gm
    from shared import documind_tools as dt

    def no_token(audience):
        raise OSError("offline: no identity token is minted")

    def no_count(self_, **kwargs):
        raise OSError("offline: count_tokens is your lane's; OFFLINE=1 estimates")

    env = {k: os.environ.get(k) for k in ("GOOGLE_CLOUD_PROJECT", "CHECKPOINT_DSN")}
    saved = (dt._id_token, gm.Models.count_tokens, gm.AsyncModels.count_tokens)
    os.environ["GOOGLE_CLOUD_PROJECT"] = PLACEHOLDER
    os.environ.pop("CHECKPOINT_DSN", None)        # the ADK brain would keep its sessions on that database
    dt._id_token, gm.Models.count_tokens, gm.AsyncModels.count_tokens = no_token, no_count, no_count
    try:
        with rp.no_network(), ap.offline():
            yield
    finally:
        dt._id_token, gm.Models.count_tokens, gm.AsyncModels.count_tokens = saved
        for k, v in env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@contextlib.contextmanager
def live_lane():
    """A lane run's process: no checkpoint DSN, so the ADK brain keeps its sessions in memory and no lane database is
    written. Put back on the way out."""
    dsn = os.environ.pop("CHECKPOINT_DSN", None)
    try:
        yield
    finally:
        if dsn is not None:
            os.environ["CHECKPOINT_DSN"] = dsn


# ----------------------------------------------------------------------------- rag-api's own prompt, inside a search
def rag_constants() -> dict:
    """generator.py's SYSTEM and DATED_RULE, and config.py's max_context_tokens and max_answer_tokens, read from
    rag-api's source as literals: rag-api's own pins are not this venv's, and nothing of it is imported or run."""
    if "constants" not in _RAG:
        out = {}
        for node in ast.parse((RAG_API / "generator.py").read_text(encoding="utf-8")).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and getattr(node.targets[0], "id", None) in ("SYSTEM", "DATED_RULE"):
                out[node.targets[0].id] = ast.literal_eval(node.value)
        for node in ast.walk(ast.parse((RAG_API / "config.py").read_text(encoding="utf-8"))):
            if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) in ("max_context_tokens",
                                                                                      "max_answer_tokens"):
                out[node.target.id] = ast.literal_eval(node.value)
        missing = {"SYSTEM", "DATED_RULE", "max_context_tokens", "max_answer_tokens"} - set(out)
        if missing:
            raise Refused(f"rag-api's source no longer holds {', '.join(sorted(missing))} as a literal")
        _RAG["constants"] = out
    return _RAG["constants"]


def rag_prompt(query: str, chunks: list[dict]) -> dict:
    """rag-api's own prompt for a search over these chunks (each with its text, source_uri and page or page_start), as
    generator.generate() builds it: SYSTEM (and the dated rule when a packed chunk carries a date), the chunks
    pack_chunks fits in what _budget() leaves of max_context_tokens, the question. Each part estimated as rag-api
    estimates it; tokens_in is their sum."""
    cb, k = context_budget(), rag_constants()
    fixed = f"{k['SYSTEM']}{k['DATED_RULE']}\n\nContext:\n\n\nQuestion: {query}"
    room = cb.TokenBudget.fit(k["max_context_tokens"], fixed, cb.estimate_tokens, answer=k["max_answer_tokens"]).chunks
    context, packed, dropped = cb.pack_chunks(list(chunks), room, cb.estimate_tokens)
    rule = k["DATED_RULE"] if any(c.get("effective_from") for c in packed) else ""
    split = {"system": tokens(k["SYSTEM"] + rule), "chunks": tokens(f"\n\nContext:\n{context}"),
             "question": tokens(f"\n\nQuestion: {query}")}
    return {**split, "tokens_in": sum(split.values()), "packed": len(packed), "dropped": len(dropped)}


class Searches:
    """documind_tools.retrieve, wrapped for the run: TOP_K sent with every search, each search noted (the call that
    asked it, the top_k asked and sent, what came back and rag-api's own usage), and offline, rag-api's answer and
    usage added to a /v1/query-shaped result, estimated from its own prompt."""

    def __init__(self, calls: Calls, top_k: int | None = None, offline: bool = False):
        self.calls, self.top_k, self.offline, self.made, self.inner = calls, top_k, offline, [], None

    @contextlib.contextmanager
    def installed(self):
        from shared import documind_tools as dt
        self.inner = dt.retrieve
        dt.retrieve = self
        try:
            yield self
        finally:
            dt.retrieve = self.inner

    def __call__(self, query, tenant_id="", top_k=5, doc_type=None, assertion=None, brain=None, passages=False):
        sent = self.top_k or top_k
        r = self.inner(query, tenant_id=tenant_id, top_k=sent, doc_type=doc_type, assertion=assertion, brain=brain,
                       passages=passages)
        found = r.get("passages" if passages else "citations") or []
        entry = {"turn": self.calls.turn, "after_call": self.calls.made[-1]["n"] if self.calls.made else 0,
                 "query": query, "doc_type": doc_type, "top_k": top_k, "sent": sent, "passages": passages,
                 "found": len(found), "chars": sum(len(str(x.get("text" if passages else "quote") or "")) for x in found)}
        if "error" in r:
            entry["error"] = r["error"]
        if not passages and self.offline and "error" not in r:
            # The chunks the citations came from, whole, as rag-api would pack them: the Rs 0 lane returns every one of
            # the top_k it ranked, so they are the same set in the same order.
            import agent_patterns as ap
            whole = {c["chunk_id"]: c for c in ap.CorpusStore.chunks(tenant_id)}
            prompt = rag_prompt(query, [whole[c["chunk_id"]] for c in found if c.get("chunk_id") in whole])
            answer = ("(offline, scripted) rag-api's own answer is not generated offline; its prompt would pack "
                      f"{prompt['packed']} chunk{'' if prompt['packed'] == 1 else 's'}.")
            usage = {"model": prices.DEFAULT_MODEL, "tokens_in": prompt["tokens_in"], "tokens_out": tokens(answer),
                     "cached_tokens": 0, "cost_usd": None}
            r = {**r, "answer": answer, "usage": usage}
            entry["rag"] = {**usage, "estimated": True, "prompt": prompt}
        elif not passages and "error" not in r:
            usage = r.get("usage") or {}
            entry["rag"] = {k: usage.get(k) for k in ("model", "tokens_in", "tokens_out", "cached_tokens", "cost_usd")}
        self.made.append(entry)
        return r


# ----------------------------------------------------------------------------- one turn on a brain
def own_prompt(brain: str, desk: str) -> str:
    """The system prompt the brain itself was given, to tell it apart from what its framework adds."""
    if brain == "desk":
        import desk_agent
        return desk_agent.system_prompt(desk)
    import brains
    return brains.SYSTEM


def run_turns(brain: str, questions: list[str], tenant: str, desk: str, calls: Calls) -> list[dict]:
    """Each question a turn on one thread, the last the measured one. [{meter, answer}] a turn."""
    import limits
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or PLACEHOLDER
    user = f"documind-ui-sa@{project}.iam.gserviceaccount.com"
    if brain == "desk":
        import agent_patterns as ap
        import desk_agent as da
        calls.turn = 1
        meter = limits.Meter(model=da.AGENT_MODEL)
        saved = (dict(da._AGENTS), dict(da._MODEL))
        da._AGENTS.clear()
        da._MODEL.clear()
        da._MODEL["llm"] = da.chat_model()       # this run's model; the process's own agents are put back after
        try:
            got = da.run(desk, questions[-1], ap.classes_for(desk), {"tenant": tenant, "assertion": None, "meter": meter})
        finally:
            da._AGENTS.clear()
            da._AGENTS.update(saved[0])
            da._MODEL.clear()
            da._MODEL.update(saved[1])
        return [{"meter": meter, "answer": got["answer"]}]
    import brains
    from langgraph.checkpoint.memory import InMemorySaver
    b = brains.build(brain, InMemorySaver())
    config = {"configurable": {"thread_id": f"{tenant}:{user}:context-sources"}}
    out = []
    for i, question in enumerate(questions, 1):
        calls.turn = i
        meter = limits.Meter(model=brains.MODEL)
        got = b.answer(question, config=config, context={"tenant_id": tenant, "user_id": user, "assertion": "",
                                                          "brain": brain, "meter": meter})
        out.append({"meter": meter, "answer": got["answer"]})
    return out


def inr_in(model: str, n: int) -> float:
    """n input tokens at the model's list price, in rupees."""
    return prices.inr(prices.usd(model, n, 0, 0))


def run(brain: str = "langchain", *, question: str = QUESTION, turns: int = 1, tenant: str = "acme",
        desk: str = "statute", top_k: int | None = None, offline: bool = True) -> tuple:
    """The turns themselves, every model call and search captured: (Calls, Searches, [{meter, answer}] a turn)."""
    questions = list(EARLIER[:turns - 1]) + [question]
    calls = Calls(script=scripted if offline else None)
    searches = Searches(calls, top_k=top_k, offline=offline)
    with (offline_lane() if offline else live_lane()), calls.installed(), searches.installed():
        done = run_turns(brain, questions, tenant, desk, calls)
    return calls, searches, done


def measure(brain: str = "langchain", *, question: str = QUESTION, turns: int = 1, tenant: str = "acme",
            desk: str = "statute", top_k: int | None = None, offline: bool = True, count=None) -> dict:
    """One measured turn (after turns - 1 earlier ones) on a brain, as a record. Offline the sources are estimated;
    count(contents, system, tools) counts them instead when given, and on the lane it defaults to the model's own
    count_tokens on location global."""
    calls, searches, done = run(brain, question=question, turns=turns, tenant=tenant, desk=desk, top_k=top_k,
                                offline=offline)
    if count is None and not offline and calls.made:
        from google import genai
        client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location="global")
        count = count_tokens_on(client, calls.made[-1]["model"])
    counter = Counter(count) if count is not None else None
    return record(brain, desk, tenant, question, turns, top_k, offline, calls, searches, done, counter)


# ----------------------------------------------------------------------------- the record
def _call_inr(c: dict) -> float:
    u = c.get("usage") or {}
    return prices.inr(prices.usd(c["model"], u.get("input", 0), u.get("visible", 0) + u.get("thinking", 0),
                                 u.get("cached", 0)))


def record(brain, desk, tenant, question, turns, top_k, offline, calls, searches, done, counter) -> dict:
    """The measured turn as one JSON-ready record: each call's sources and tokens, its rupees, the searches, the turn's
    totals, the earlier turns' cost and, when counted, the probe."""
    measured = [c for c in calls.made if c["turn"] == turns]
    rows, probe = [], None
    for k, c in enumerate(measured, 1):
        req, usage = c["request"], c.get("usage") or {}
        labels = label(req["contents"], question)
        if counter is None:
            sources, approx = estimated_sources(req, labels), []
        else:
            pieces, call_probe = counted_pieces(c["raw"], req, labels, counter)
            sources = dict.fromkeys(SOURCES, 0)
            for s, n, _, _ in pieces:
                sources[s] += n
            approx = sorted({s for s, _, exact, _ in pieces if not exact})
            probe = probe or call_probe
        model, counted = c["model"], sum(sources.values())
        billed, cached = usage.get("input", 0), usage.get("cached", 0)
        output = usage.get("visible", 0) + usage.get("thinking", 0)
        residual = None if c.get("error") else billed - counted        # a failed call billed nothing to compare
        rows.append({
            "n": k, "model": model, "error": c.get("error"), "usage": {**usage, "output": output},
            "sources": sources, "estimated": approx, "counted": counted, "residual": residual,
            "asked": (c.get("reply") or {}).get("calls", []), "said": (c.get("reply") or {}).get("text", ""),
            "inr": {"sources": {s: inr_in(model, n) for s, n in sources.items()},
                    "residual": inr_in(model, residual or 0),
                    "cached": -prices.inr(prices.usd(model, cached, 0, 0) - prices.usd(model, cached, 0, cached)),
                    "output": prices.inr(prices.usd(model, 0, output, 0)),
                    "call": _call_inr(c)}})
    if probe is not None and rows:
        probe = {**probe, "counted": rows[0]["counted"], "billed": rows[0]["usage"].get("input", 0),
                 "residual": rows[0]["residual"], "count_requests": counter.asked}
    by_n = {c["n"]: k for k, c in enumerate(measured, 1)}
    found = [{**s, "call": by_n.get(s["after_call"], 0)} for s in searches.made if s["turn"] == turns]
    earlier_calls = [c for c in calls.made if c["turn"] != turns]
    earlier_searches = [s for s in searches.made if s["turn"] != turns]
    meter, answer = done[-1]["meter"], done[-1]["answer"]
    model_inr = sum(r["inr"]["call"] for r in rows)
    rag_inr = sum(prices.inr(_rag_usd(s.get("rag"))) for s in found)
    head = measured[0]["request"] if measured else None
    mine = own_prompt(brain, desk) if head else ""
    return {
        "brain": brain, "desk": desk if brain == "desk" else None, "tenant": tenant, "question": question,
        "turns": turns, "top_k": top_k, "offline": offline, "counter": "estimate" if counter is None else "count_tokens",
        "system": None if head is None else {"characters": len(head["system"]), "own": mine,
                                             "added": _added(head["system"], mine)},
        "declarations": [] if head is None else [d.get("name") for d in head["tools"]],
        "parameters_key": None if head is None else next(
            (k for d in head["tools"] for k in d if k.startswith("parameters")), None),
        "calls": rows, "searches": found,
        "totals": {"tokens": {s: sum(r["sources"][s] for r in rows) for s in SOURCES},
                   "residual": sum(r["residual"] or 0 for r in rows),
                   "input": sum(r["usage"].get("input", 0) for r in rows),
                   "cached": sum(r["usage"].get("cached", 0) for r in rows),
                   "output": sum(r["usage"]["output"] for r in rows),
                   "thinking": sum(r["usage"].get("thinking", 0) for r in rows),
                   "inr": {s: sum(r["inr"]["sources"][s] for r in rows) for s in SOURCES},
                   "residual_inr": sum(r["inr"]["residual"] for r in rows),
                   "cached_inr": sum(r["inr"]["cached"] for r in rows),
                   "output_inr": sum(r["inr"]["output"] for r in rows),
                   "model_inr": model_inr, "rag_inr": rag_inr, "turn_inr": model_inr + rag_inr},
        "meter": {"model_calls": meter.model_calls, "model_inr": prices.inr(meter.cost_usd),
                  "rag_inr": prices.inr(meter.rag_cost_usd), "stopped_by": meter.stopped_by},
        "earlier": {"turns": turns - 1, "model_calls": len(earlier_calls), "searches": len(earlier_searches),
                    "inr": sum(_call_inr(c) for c in earlier_calls)
                    + sum(prices.inr(_rag_usd(s.get("rag"))) for s in earlier_searches)},
        "answer": answer, "probe": probe,
    }


def _rag_usd(rag: dict | None) -> float:
    """What one rag-api answer cost: its own cost_usd when it carries one (the gateway's, or 0 for a cache hit), else
    its tokens at list price, as limits.Meter.charge_rag prices it."""
    if not rag:
        return 0.0
    if rag.get("cost_usd") is not None:
        return float(rag["cost_usd"])
    return prices.usd(rag.get("model"), int(rag.get("tokens_in") or 0), int(rag.get("tokens_out") or 0),
                      int(rag.get("cached_tokens") or 0))


def _added(sent: str, mine: str) -> str | None:
    """What the framework put into the system instruction beside the brain's own prompt, if anything."""
    if not mine or sent == mine or mine not in sent:
        return None
    return " ".join(sent.replace(mine, "", 1).split()) or None


# ----------------------------------------------------------------------------- the printout
def _short(text: str, width: int = 96) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= width else text[:width - 3].rstrip() + "..."


def _rs(x: float) -> str:
    return f"{x:,.4f}"


def _args(args: dict) -> str:
    return ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in (args or {}).items())


def _header(rec: dict) -> list[str]:
    who = f"brain {rec['brain']}" + (f", desk {rec['desk']}" if rec["desk"] else "")
    thread = ("a fresh thread" if rec["turns"] == 1 else
              f"turn {rec['turns']} of one thread, after {rec['turns'] - 1} earlier "
              f"question{'s' if rec['turns'] > 2 else ''}")
    if rec["top_k"]:
        top = f"every search sends top_k {rec['top_k']} (TOP_K), whatever was asked"
    elif rec["brain"] == "desk":
        top = "each search sends desk_agent.TOP_K, 5"
    elif rec["brain"] == "direct":
        top = "its one search sends top_k 5 (brains.DirectBrain)"
    else:
        top = "each search sends the model's top_k, or tools.py's default of 5"
    out = [f"context sources: one turn on {who}, tenant {rec['tenant']}, {thread}; {top}"]
    if rec["offline"]:
        out += ["  OFFLINE=1: a scripted model at the google-genai boundary (the brain, its adapter, tools and limits run",
                "  as on the lane) and the Rs 0 lane's retrieve over evals/corpus: no network, no credential, nothing",
                "  billed. Tokens are estimated: a quarter of the characters each part carries (rag-api's estimator,"]
        out.append("  context_budget.estimate_tokens), so the residual is 0. On your lane count_tokens counts each source."
                   if rec["counter"] == "estimate" else
                   "  context_budget.estimate_tokens); each source is counted in context by the count given.")
    else:
        out += ["  on your lane: Gemini on location global, each search on your rag-api as documind-ui-sa. Each call's",
                "  tokens are its usage_metadata's; each source is counted in context by count_tokens on location global",
                "  (not billed), ~ where it was estimated instead. The residual is what a call billed less what was counted."]
    out.append(f"question: {rec['question']}")
    if rec["system"]:
        added = rec["system"]["added"]
        out.append(f"  sent with every call: a system prompt of {rec['system']['characters']:,} characters, "
                   + (f"the brain's own and then the framework's {_short(added, 64)!r}" if added else "the brain's own"))
        n = len(rec["declarations"])
        out.append(f"  and {n} tool declaration{'s' if n != 1 else ''} ({', '.join(rec['declarations'])}), each with "
                   f"its {rec['parameters_key'] or 'parameters'}")
    if rec["earlier"]["turns"]:
        e = rec["earlier"]
        out.append(f"  the {e['turns']} earlier turn{'s' if e['turns'] != 1 else ''}, not measured: {e['model_calls']} "
                   f"model calls and {e['searches']} searches, Rs {_rs(e['inr'])}")
    return out


def _call_lines(r: dict, rec: dict) -> list[str]:
    u, offline = r["usage"], rec["offline"]
    out = [f"model call {r['n']} of {len(rec['calls'])} ({r['model']}): in {u.get('input', 0):,}"
           + (f" ({u['cached']:,} cached)" if u.get("cached") else "")
           + f", out {u['output']:,}" + (f" ({u['thinking']:,} thinking)" if u.get("thinking") else "")
           + f": Rs {_rs(r['inr']['call'])}" + (f"   FAILED: {r['error']}" if r.get("error") else "")]
    billed = u.get("input", 0) or 1
    for s in SOURCES:
        n = r["sources"][s]
        if s == "other" and not n:
            continue
        mark = "~" if s in r["estimated"] else " "
        out.append(f"  {LABELS[s]:18} {mark}{n:>7,}  " + (f"{100 * n / billed:5.1f}%" if n else ""))
    if r["residual"] is None:
        out.append(f"  {'residual':18}  {'-':>7}   the call failed: nothing billed to compare")
    else:
        out.append(f"  {'residual':18}  {r['residual']:>7,}  " + (f"{100 * r['residual'] / billed:5.1f}%" if r["residual"] else "      ")
                   + ("   offline the script's input is the sum of its parts" if offline and rec["counter"] == "estimate"
                      else f"   billed {u.get('input', 0):,}, counted {r['counted']:,}"))
    for a in r["asked"]:
        out.append(f"  -> {a['name']}({_args(a['args'])})")
        for s in rec["searches"]:
            if s["call"] == r["n"]:
                out += _search_lines(s)
    if not r["asked"] and not r.get("error"):
        out.append("  -> no tool: the answer")
    return out


def _turn_lines(rec: dict) -> list[str]:
    rows, t, m = rec["calls"], rec["totals"], rec["meter"]
    out = []
    if rows:
        out += [f"the turn by source: {len(rows)} model call{'s' if len(rows) != 1 else ''}; the system prompt, the "
                "declarations, the thread and the question go with every one",
                f"  {'':18}  {'tokens':>7}  {'Rs':>8}"]
        for s in SOURCES:
            per = [r["sources"][s] for r in rows]
            if s == "other" and not any(per):
                continue
            if not any(per):
                note = ""
            elif s in ("calls", "results"):
                note = f"from call {next(i for i, x in enumerate(per, 1) if x)} on"
            elif len(per) > 1 and len(set(per)) == 1:
                note = f"{per[0]:,} in each of {len(per)} calls"
            else:
                note = " + ".join(f"{x:,}" for x in per) if len(per) > 1 else ""
            out.append(f"  {LABELS[s]:18}  {t['tokens'][s]:>7,}  {_rs(t['inr'][s]):>8}  {note}".rstrip())
        out += [f"  {'residual':18}  {t['residual']:>7,}  {_rs(t['residual_inr']):>8}",
                f"  {'input':18}  {t['input']:>7,}  {_rs(sum(t['inr'].values()) + t['residual_inr']):>8}",
                f"  {'cached':18}  {t['cached']:>7,}  {_rs(t['cached_inr']):>8}  a cached token bills at a tenth of "
                "the input price",
                f"  {'output':18}  {t['output']:>7,}  {_rs(t['output_inr']):>8}  thinking included",
                f"  {'the model calls':18}  {'':>7}  {_rs(t['model_inr']):>8}  the turn's Meter (limits.py) charged "
                f"Rs {_rs(m['model_inr'])} for {m['model_calls']} call{'s' if m['model_calls'] != 1 else ''}"]
    else:
        out.append("the turn: no model call of the chat's own")
    n_rag = sum(1 for s in rec["searches"] if s.get("rag"))
    out += [f"  {'rag-api, inside':18}  {'':>7}  {_rs(t['rag_inr']):>8}  {n_rag} answer{'s' if n_rag != 1 else ''} of "
            "its own" + (", estimated" if rec["offline"] and n_rag else "") + f"; the Meter charged Rs {_rs(m['rag_inr'])}",
            f"  {'the turn':18}  {'':>7}  {_rs(t['turn_inr']):>8}  at list price (shared/prices.py, USD_INR "
            f"{prices.USD_INR})" + ("; offline, nothing is billed" if rec["offline"] else "")]
    if m["stopped_by"]:
        out.append(f"  the turn's limits stopped it: {m['stopped_by']}")
    return out


def render(rec: dict) -> str:
    out = _header(rec) + [""]
    if not rec["calls"]:
        out.append("no model call of the chat's own: one retrieve, and rag-api's grounded answer comes back with it "
                   "(brains.DirectBrain).")
        out.append("What rides rag-api's own call is its system prompt, the chunks it packed and the question:")
        for s in rec["searches"]:
            out += _search_lines(s)
    for r in rec["calls"]:
        out += _call_lines(r, rec)
    out += [""] + _turn_lines(rec) + ["", f"answer: {_short(rec['answer'], 150)}"]
    p = rec["probe"]
    if p:
        out += ["", f"probe (workshop lesson 6.1, batch 1): count_tokens on location global, {rec['calls'][0]['model']}",
                f"  system_instruction: {p['system'] or 'not sent'}",
                f"  tools:              {p['tools'] or 'not sent'}",
                f"  contents:           {p['contents'] or 'counted'}",
                f"  call 1's request:   counted {p['counted']:,}, billed {p['billed']:,} (prompt_token_count), residual "
                + ("-" if p["residual"] is None else f"{p['residual']:,}")
                + f"; {p['count_requests']} count_tokens request{'s' if p['count_requests'] != 1 else ''}, none billed"]
    return "\n".join(out)


def _search_lines(s: dict) -> list[str]:
    """One search: the top_k it sent, what came back, and rag-api's own call inside it."""
    kind = "passages" if s["passages"] else "citations"
    sent = (f"top_k {s['sent']}" + (f" (TOP_K; {s['top_k']} asked)" if s["sent"] != s["top_k"] else ""))
    lines = [f"     search: {sent}; {s['found']} {kind} back, {s['chars']:,} characters"
             + (f"; {s['error']}" if s.get("error") else "")]
    rag = s.get("rag")
    if rag and rag.get("estimated"):
        p = rag["prompt"]
        lines.append(f"     inside it, rag-api's own call (estimated: generator.py's prompt): system {p['system']:,}, "
                     f"{p['packed']} chunk{'' if p['packed'] == 1 else 's'} {p['chunks']:,}, question {p['question']:,}; "
                     f"in {rag['tokens_in']:,}, out {rag['tokens_out']:,}: Rs {_rs(prices.inr(_rag_usd(rag)))}")
    elif rag:
        lines.append(f"     inside it, rag-api's own call (its usage): in {int(rag.get('tokens_in') or 0):,}"
                     + (f" ({int(rag['cached_tokens']):,} cached)" if rag.get("cached_tokens") else "")
                     + f", out {int(rag.get('tokens_out') or 0):,}: Rs {_rs(prices.inr(_rag_usd(rag)))}")
    elif s["passages"]:
        lines.append("     /v1/passages: no model call inside the search")
    return lines


# ----------------------------------------------------------------------------- the command
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--offline", action="store_true", help="a scripted model and the Rs 0 lane: no network, Rs 0")
    ap.add_argument("--brain", default="langchain", choices=BRAINS)
    ap.add_argument("--desk", choices=DESKS, help="with --brain desk: statute (the default), handbook or astar")
    ap.add_argument("--turns", type=int, default=1, help=f"1 to {len(EARLIER) + 1}: earlier questions asked first")
    ap.add_argument("--top-k", type=int, help=f"1 to {TOP_K_MAX}: sent with every search (the Change-it)")
    ap.add_argument("--question", default=QUESTION)
    ap.add_argument("--tenant", default="acme")
    ap.add_argument("--json", action="store_true", help="the record as one JSON object")
    a = ap.parse_args(argv)
    # pydantic warns when it serialises a tool call whose runtime context (a dict holding the turn's Meter) is not its
    # schema's None, and google-adk marks its experimental pieces: notices, not output, as in every lesson cell.
    warnings.filterwarnings("ignore", category=UserWarning)
    try:
        if a.desk and a.brain != "desk":
            raise Refused("DESK= is for BRAIN=desk")
        if not 1 <= a.turns <= len(EARLIER) + 1:
            raise Refused(f"TURNS is 1 to {len(EARLIER) + 1}")
        if a.turns > 1 and a.brain in ("direct", "desk"):
            raise Refused(f"{a.brain} keeps no thread (" + ("brains.DirectBrain answers one retrieve" if a.brain == "direct"
                          else "desk_agent: checkpointer=False") + "), so its turns are all first turns: leave TURNS out")
        if a.top_k is not None and not 1 <= a.top_k <= TOP_K_MAX:
            raise Refused(f"TOP_K is 1 to {TOP_K_MAX}, rag-api's limit")
        if os.environ.get("DOCUMIND_PROFILE", "gcp") != "gcp":
            raise Refused("DOCUMIND_PROFILE is not gcp: this measures the gcp lane's calls; OFFLINE=1 needs no profile")
        if not a.offline:
            need = [k for k in LIVE_ENV if not os.environ.get(k)]
            if need:
                raise Refused(f"a turn on your lane needs {', '.join(need)}: make context-sources PROJECT=<id> sets them, "
                              "or OFFLINE=1 for the scripted turn")
        rec = measure(a.brain, question=a.question, turns=a.turns, tenant=a.tenant, desk=a.desk or "statute",
                      top_k=a.top_k, offline=a.offline)
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:                      # noqa: BLE001 - the turn failed: say how, exit 1
        print(f"the turn failed: {type(exc).__name__}: {_short(str(exc), 300)}", file=sys.stderr)
        return 1
    print(json.dumps(rec, ensure_ascii=False, indent=1, default=str) if a.json else render(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
