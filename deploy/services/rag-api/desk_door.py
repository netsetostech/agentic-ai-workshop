"""The DocuMind Desk's door on rag-api: the hard gate before any handler runs (workshop lesson 5.6).

A question the law hands to a person (shared/desk_rules.py: posh, grievance, privacy_request, exit_dues,
human_requested) must never reach retrieval or a model, on any path into rag-api - the Chat page's direct brain
streams here, and the MCP server and the A2A peer call /v1/query themselves. So the gate sits in front of the three
routes that take a question, POST /v1/query, /v1/stream and /v1/passages, as a pure ASGI middleware: the handlers
stay exactly as they are, and a hit never enters them. The chat service's langchain, langgraph and adk brains reach
rag-api through a tool their own model chose to call: on those paths the person's words have already reached that
model, and this door sees only the search words the model wrote. It stops the search when those words hit the gate,
which they need not, and the brain's model then writes the reply itself. The chat service's own door
(services/chat/desk.py) keeps those turns from every model: it gates POST /v1/chat before any brain runs, with the
same rules and the same desk_gate switch.

    1. The body is buffered, at most 64 KiB (a 413 above that). QueryRequest caps the question at 4,000 characters,
       but pydantic reads it only after this door has read the body, so that cap does not bound the read.
    2. A body that is not JSON, has no string `query`, a query over QueryRequest's 4,000 characters, or one with no
       words, is replayed unchanged: the handler answers it. The gate and the masking run off the event loop, the
       model check and its tenants read on desk_recall's own threads (POOL, READ_POOL), with the request's context.
    3. No hit, no identifier and no model check to run: the original bytes go through untouched, and nothing is read
       or verified. The model check runs only on /v1/query and /v1/stream, only for a question a person sent (brain
       unset, or "ui" - the Chat page; a chat brain, the Desk and the MCP server label their own calls, whose words
       the chat service's door or a model has had already), and only for a tenant whose desk_gate is on, which
       checked (shared/desk_recall.OnTenants, read once a minute) lists.
    4. Otherwise the caller is verified and the roster checked first, with the functions install() was given
       (auth.py's verify_iap and enforce_membership), so this file calls no verifier of its own and reads no
       tenant's settings for a caller who is not on its roster. Then tenant_settings/{tenant}.desk_gate
       (shared/desk_rules.gate_state): rules unless it says off or on, and a failed read is rules - main.py's
       tenant_settings() reads a failure as an empty document - so only an operator's "off" replays the body as sent.
         - A hit: their HTTP errors are answered here - an HTTPException raised in a middleware, outside the app's
           exception handling, would be a 500. Then the fixed reply of shared/desk_law.py - a RAGResponse on
           /v1/query, a token event then done on /v1/stream - with model "none", backend "desk_gate", no citations,
           cost 0 and 0 tokens. Nothing is retrieved, generated or cached.
         - No hit, and desk_gate on: the model check (shared/desk_recall.py) reads the masked question. A class is
           answered as a hit is, with the check's model, tokens and cost; none, or a check that fails, goes on below.
           Each check logs a "desk_gate_check" row: its outcome, tokens and cost, no question and no person; a check
           that failed logs it at WARNING, so a tenant losing its check shows in the log's severity.
         - Aadhaar or card numbers and no hit (checked by Verhoeff and Luhn, shared/identifiers.py): a refused
           caller's body is replayed unchanged, so the handler gives its own 401 or 403; for a member, unless the
           tenant's desk_gate is off, the numbers are masked before the body is replayed, so neither retrieval nor
           the model sees them. PAN and GSTIN pass. No row is logged for a mask.
    5. A hit that is answered logs {"event": "desk_gate", ...} with the class, the rules version and the method (rule
       or model), never the question. For posh, grievance and privacy_request the row's user is null and its class
       "sensitive".

Its own replies are rendered the way FastAPI renders JSON (compact, UTF-8), so a refused caller gets the same bytes
whether or not the question hit the gate. main.py installs it before CORSMiddleware, so CORS wraps it and its replies
carry the same CORS headers as the handlers'. It imports nothing from fastapi or starlette, so its test runs in plain
asyncio with a fake app and fake auth.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time

from shared import desk_law, desk_recall, desk_rules

PATHS = {"/v1/query": "query", "/v1/stream": "stream", "/v1/passages": "passages"}
MAX_BODY = 64 * 1024
QUERY_MAX = 4000        # QueryRequest.query's max_length (schemas.py): a route that takes a longer question raises both
CHECKED = ("query", "stream")           # the surfaces the model check reads; /v1/passages is the Desk's agent mode
PEOPLE = (None, "ui")                   # the brain labels of a question a person sent: none, or the Chat page's


def _read(question: str):
    """The gate's class and the masked question, in one call: the door runs it off the event loop."""
    return desk_rules.gate(question), desk_rules.mask(question)

log = logging.getLogger("documind-api")


class _Headers:
    """The request's headers as verify_iap and shared/iap.py read them: .get(name), case-insensitive."""

    def __init__(self, raw):
        self._h: dict[str, str] = {}
        for k, v in raw or ():
            self._h.setdefault(k.decode("latin-1").lower(), v.decode("latin-1"))

    def get(self, name: str, default=None):
        return self._h.get(name.lower(), default)

    def __getitem__(self, name: str) -> str:
        return self._h[name.lower()]

    def __contains__(self, name) -> bool:
        return isinstance(name, str) and name.lower() in self._h


class _Caller:
    """What verify() is handed in place of a framework request: the headers, which is all it reads."""

    def __init__(self, scope):
        self.scope = scope
        self.headers = _Headers(scope.get("headers"))


async def _respond(send, status: int, body: bytes, content_type: bytes, headers=None) -> None:
    hs = [(b"content-type", content_type), (b"content-length", str(len(body)).encode())]
    for k, v in (headers or {}).items():
        hs.append((str(k).lower().encode("latin-1"), str(v).encode("latin-1")))
    await send({"type": "http.response.start", "status": status, "headers": hs})
    await send({"type": "http.response.body", "body": body})


def _dumps(obj) -> bytes:
    """JSON as FastAPI's JSONResponse renders it: no spaces, UTF-8 as it is, no NaN."""
    return json.dumps(obj, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


async def _json(send, status: int, obj, headers=None) -> None:
    await _respond(send, status, _dumps(obj), b"application/json", headers)


def _replay(body: bytes, receive):
    """A receive() that hands the app the buffered body once, then whatever the server sends next (a disconnect)."""
    sent = False

    async def receive_again():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return await receive()
    return receive_again


def _with_length(scope, n: int):
    hs = [(k, v) for k, v in scope.get("headers") or () if k.lower() != b"content-length"]
    return {**scope, "headers": hs + [(b"content-length", str(n).encode())]}


class DeskDoor:
    def __init__(self, app, settings, verify, member, checked=None, check=None):
        self.app, self.settings, self.verify, self.member = app, settings, verify, member
        self.checked, self.check = checked, check

    async def _state(self, tenant: str) -> str:
        try:
            return desk_rules.gate_state(await asyncio.to_thread(self.settings, tenant))
        except Exception:  # noqa: BLE001 - a failed read is the rules, never off
            return "rules"

    async def _checked(self) -> frozenset:
        """The tenants the model check runs for: none without a check to run."""
        if self.checked is None or self.check is None:
            return frozenset()
        return await self.checked.tenants()        # on the loop: only the turn that claims the read waits for it

    async def __call__(self, scope, receive, send):
        surface = PATHS.get(scope.get("path")) if scope.get("type") == "http" and scope.get("method") == "POST" else None
        if surface is None:
            return await self.app(scope, receive, send)
        t0 = time.time()
        too_big = {"detail": f"request body over {MAX_BODY} bytes"}
        declared = _Headers(scope.get("headers")).get("content-length")
        if declared and declared.strip().isdigit() and int(declared) > MAX_BODY:
            return await _json(send, 413, too_big)
        chunks, size = [], 0
        while True:
            msg = await receive()
            if msg["type"] == "http.disconnect":
                return None
            part = msg.get("body", b"")
            size += len(part)
            if size > MAX_BODY:
                return await _json(send, 413, too_big)
            chunks.append(part)
            if not msg.get("more_body"):
                break
        body = b"".join(chunks)
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            payload = None
        question = payload.get("query") if isinstance(payload, dict) else None
        if not isinstance(question, str):
            return await self.app(scope, _replay(body, receive), send)
        if len(question) > QUERY_MAX or not question.strip():   # the handler's own answer: nothing to gate or check
            return await self.app(scope, _replay(body, receive), send)
        tenant = payload.get("tenant_id")
        cls, (masked, kinds) = await asyncio.to_thread(_read, question)
        checked = (cls is None and surface in CHECKED and payload.get("brain") in PEOPLE and isinstance(tenant, str)
                   and tenant in await self._checked())
        if not isinstance(tenant, str) or not tenant or (cls is None and not kinds and not checked):
            return await self.app(scope, _replay(body, receive), send)
        try:
            user = await asyncio.to_thread(self.verify, _Caller(scope))
            await asyncio.to_thread(self.member, user["email"], tenant)
        except Exception as e:  # noqa: BLE001 - an HTTP error is answered here; anything else is the server's 500
            status = getattr(e, "status_code", None)
            if not isinstance(status, int):
                raise
            if cls is None:                         # nothing to mask or check for a caller the handler refuses
                return await self.app(scope, _replay(body, receive), send)
            return await _json(send, status, {"detail": getattr(e, "detail", str(e))}, getattr(e, "headers", None))
        state = await self._state(tenant)
        if state == "off":                          # an operator's explicit off: the body as it was sent
            return await self.app(scope, _replay(body, receive), send)
        method = "rule"
        usage = {"tokens_in": 0, "tokens_out": 0, "cached_tokens": 0, "cost_usd": 0.0, "model": "none", "backend": "desk_gate"}
        if cls is None and checked and state == "on":
            got = await desk_recall.run(desk_recall.POOL, self.check, masked)
            (log.warning if got["outcome"] == "error" else log.info)(json.dumps(desk_recall.row(surface, tenant, got)))
            if got["case"] is not None:
                cls, method, usage = got["case"], "model", desk_recall.usage(got)
        if cls is None:
            if not kinds:
                return await self.app(scope, _replay(body, receive), send)
            payload["query"] = masked
            body = json.dumps(payload).encode()
            return await self.app(_with_length(scope, len(body)), _replay(body, receive), send)
        sensitive = cls in desk_rules.SENSITIVE
        log.info(json.dumps({"event": "desk_gate", "surface": surface, "tenant": tenant,
                             "user": None if sensitive else user["email"],
                             "class": "sensitive" if sensitive else cls, "rules_version": desk_rules.RULES_VERSION,
                             "method": method}))
        text = desk_law.template(cls)
        latency = int((time.time() - t0) * 1000)
        if surface == "stream":
            done = {**usage, "latency_ms": latency, "stages": {}, "cache_hit": "none"}
            sse = (f"event: token\ndata: {json.dumps({'t': text})}\n\n"
                   f"event: done\ndata: {json.dumps(done)}\n\n").encode()
            return await _respond(send, 200, sse, b"text/event-stream; charset=utf-8")
        if surface == "passages":
            return await _json(send, 200, {"passages": [], "answer": text, "answerable": False, "usage": usage})
        return await _json(send, 200, {"answer": text, "citations": [], "confidence": "low", "answerable": False,
                                       **usage, "latency_ms": latency, "stages": {}, "cache_hit": "none"})


def install(app, settings, verify, member, checked=None, check=None) -> None:
    """Put the door in front of the app. settings(tenant) returns tenant_settings/{tenant}; verify(request) returns
    {"email": ...} or raises 401; member(email, tenant) raises 403. checked is the tenants whose desk_gate is on
    (shared/desk_recall.OnTenants: its tenants()) and check(masked question) the model check's result
    (desk_recall.check); without both, no model check runs. Starlette makes the middleware added last the outermost,
    so a line added after this one - main.py's CORSMiddleware - wraps the door."""
    app.add_middleware(DeskDoor, settings=settings, verify=verify, member=member, checked=checked, check=check)
