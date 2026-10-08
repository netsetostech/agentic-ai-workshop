"""The DocuMind Desk on the chat service (workshop lesson 5.6): the chat door and the case routes.

agent.py installs both with one line, desk.install(app, caller=..., tenant_for=..., thread_config=...), so its own
handlers stay exactly as they are.

THE CHAT DOOR. A question the law hands to a person (shared/desk_rules.py: posh, grievance, privacy_request,
exit_dues, human_requested) must not reach a brain: on POST /v1/chat a brain's own model reads the turn before it
calls rag-api, so rag-api's door (services/rag-api/desk_door.py) would stop only the search. This door stands in front
of chat() as a pure ASGI middleware, so a hit never enters the handler: no brain runs, no model is called, and nothing
is checkpointed.

    1. The body is buffered, at most 64 KiB (a 413 above that); ChatRequest caps the question at 4,000 characters, but
       pydantic reads it only after this door has read the body.
    2. A body ChatRequest would refuse (not JSON, no string question, a question over 4,000 characters, a bad
       session_id or brain) is replayed unchanged: the handler's own 422 answers it.
    3. On the local profile there is no IAP and no Firestore: the tenant is LOCAL_TENANT, nobody is verified and no
       switch is read, as chat() itself never touches Firestore there. LOCAL_TENANT has the rules, as every tenant has
       until an operator writes off: a hit gets the fixed reply below, a number is masked, and nothing else changes.
    4. No hit, no identifier and no model check to run - a question with no words, or no tenant whose desk_gate is on
       (CHECKED, shared/desk_recall.OnTenants, read once a minute): the original bytes go through untouched, and nothing
       is read or verified.
    5. Otherwise the caller is verified with the caller() install() was given, and the tenant looked up with its
       tenant_for(), before any setting is read - so this door reads no tenant's settings for a caller it does not
       know. Then tenant_settings/{tenant}.desk_gate, as gate_state() reads it: rules unless it says off or on, and a
       failed read is the last state this process read for the tenant, else rules - only an operator's "off" replays
       the body as sent.
         - A hit: their refusals (401, 403) are answered here, in FastAPI's own bytes, so a caller cannot tell a gate
           hit from a pass by the reply. Then the fixed reply of shared/desk_law.py in /v1/chat's response shape, with
           no tool calls, no refusals, no citations, model "none" and cost 0, plus case_offer: the type of case the
           person may raise for it (POST /v1/cases), so a page can offer that case without reading the reply's words.
         - No hit, and desk_gate on: the model check (shared/desk_recall.py) reads the masked question before any
           brain does. A class is answered as a hit is, with the check's model and its one call in limits; none, or a
           check that fails, goes on below. Each check logs a "desk_gate_check" row: its outcome, tokens and cost, no
           question and no person, at WARNING when the check failed. The check and the CHECKED read run on
           desk_recall's own threads (POOL, READ_POOL), with the request's context. CHECKED is lane-wide: while any
           tenant is on, every turn with words that the rules let through is looked up, because the tenant is known
           only after the caller is.
         - Aadhaar or card numbers and no hit: a refused caller's body is replayed unchanged, so the handler gives its
           own 401 or 403; for a member, unless desk_gate is off, the numbers are masked before the body is replayed,
           so neither the brain, the checkpoint nor the model sees them.
    6. A hit that is answered logs {"event": "desk_gate", "surface": "chat", ...} with the class, the rules version
       and the method (rule or model), never the question. For posh, grievance and privacy_request the row's user is
       null and its class "sensitive".
Every turn the door hands to chat() also goes to _shadow(): while the tenant's desk_route is shadow, the routed Desk's
router decides it there too and logs a row (workshop lesson 10.4), and the door's own lines did not change for it.

THE CASE ROUTES (shared/cases.py, shared/roles.py):

    POST /v1/cases                  raise a case: one of the six types the button offers. A draft comes back (posh:
                                    the case itself, with the unit, the chosen contacts and the Local Committee;
                                    posh takes a client token, so a doubled press opens one case)
    POST /v1/cases/{id}/confirm     the person's confirmed words, with a client token: the same token, the same case
    POST /v1/cases/{id}/cancel      withdraw a draft or one's own open case
    GET  /v1/cases                  the reader's inbox (the queues their roles read) and the cases they raised
    GET  /v1/cases/{id}             one case, by a point read: 404 unless the reader may read it
    POST /v1/cases/{id}/status      the queue moves a case along
    GET  /v1/cases/offer            what the person may raise here: the Desk's switches, the case types whose queue is
                                    configured, and the POSH card's offices, members and Local Committee contacts

Every one takes the person from _principal(request, caller), and only from there: caller(request), unless the Google
Chat bridge names a person (services/chat/delegation.py). {id} matches a case id only (32 hex digits), so a later
route such as /v1/cases/offer is never taken for a case. The tenant is the roster's (tenant_for), never a request
field. The records live in Firestore, so on the local profile these routes answer 501. tenant_settings is read
through settings(), once a minute per tenant.

THE ROUTED DESK (workshop lesson 10.4: services/chat/desk_router.py decides a turn, desk_graph.py answers it):

    POST /v1/desk     one turn for a person. The handler makes the Meter, then runs decide() before any graph runs; the
                      thread's previous turn and the chips it offered are read back with graph.get_state(). A gate hit
                      or any case, denied, not_covered or out_of_scope turn is answered by code and never enters the
                      graph, so nothing is checkpointed; only answer, clarify and fallback turns invoke it, with the
                      decision in its state. A chip asks the thread's own last question of a desk the last kept reply
                      offered (409 otherwise); draft_id names the draft the page shows, read back as the person's
                      own. A POSH reply carries the card GET /v1/cases/offer shows (cases.posh_offer). Served while
                      desk_route is on or single; a desk_eval account may call it in any mode, and only it may send
                      arm. An unknown field (a tenant, prev_question) is a 422. One "desk" row a turn.
    POST /v1/route    the decision alone, for the Desk's eval accounts (desk_eval): no answer, no checkpoint, at most
                      ROUTE_RATE calls a minute per account in each worker process. prev_question and prev_route stand
                      in for the thread a follow-up row needs; a prev_question the gate takes is refused, so no model
                      reads it. Its "desk" row says surface "route".
    GET /v1/desk/check  who the request serves and their tenant, refused as POST /v1/desk refuses its caller, with no
                      text: the Google Chat bridge asks it before it queues a question, so a person on no roster, or a
                      company with the door or the routed Desk off, hears so at once.
    shadow            while desk_route is shadow and desk_gate is not off (the door then answers every sensitive turn
                      itself), _shadow() decides each /v1/chat turn too, inside the request and beside the brain (the
                      chat service's CPU is throttled between requests, so a background task could stall), with its own
                      Meter, and logs a "desk_shadow" row. It never answers, drafts or checkpoints. The request waits
                      SHADOW_TIMEOUT_S for it; a decide still running then writes its row when it ends. Nothing runs
                      while no tenant is in shadow (shadow_tenants(), read once a minute). At most SHADOW_DECIDES
                      decides run at once, on threads and a model pool of their own, so they never hold up a lookup or
                      an answered turn's classifier; past that a turn is skipped, with a "desk_shadow_skipped" line. A
                      posh, grievance or privacy_request gate hit that still reaches it writes no row, only a skipped
                      line with no tenant.

Each Desk row names every field in its literal (_desk_row, _shadow_row) and carries no question; for posh, grievance
and privacy_request (a turn on an open draft of one of them included) its user is null and its case_type
"sensitive". desk_route is off, shadow, on or single
(desk_single names the one answer desk; single without a valid one is off); desk_off lists the answer desks the
company has switched off; clause_notes holds the company's notes a handbook answer shows beside the clauses it cites
(desk_graph.noted). Gemini generation runs on location global and the query embedding on us-central1
(desk_router.GeminiModels). Like the case routes, these answer 501 on the local profile.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from functools import lru_cache
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.convertors import Convertor, register_url_convertor
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException as RefusedHTTP

import delegation
import desk_router
import desk_routes
import limits
from shared import cases, desk_law, desk_recall, desk_rules, roles
from shared.profile import PROFILE

log = logging.getLogger("documind.chat.desk")

PATH = "/v1/chat"
MAX_BODY = 64 * 1024
QUESTION_MAX = 4000                     # ChatRequest.question's max_length (agent.py)
SESSION = re.compile(r"[A-Za-z0-9_-]{1,64}")    # ChatRequest.session_id's pattern
BRAIN_NAMES = ("langchain", "langgraph", "adk", "direct")
NOT_A_MEMBER = "not a member of any tenant"     # chat()'s own 403, word for word
SETTINGS_TTL_S = 60
_hooks: dict = {}


# ---------------------------------------------------------------- tenant_settings, once a minute per tenant
@lru_cache(maxsize=1)
def _client():
    from google.cloud import firestore
    return firestore.Client()


_SETTINGS: dict[str, tuple[float, dict]] = {}


def settings(tenant: str) -> dict:
    """tenant_settings/{tenant}, read at most once a minute per tenant per instance. A failed read raises: the door
    keeps the last desk_gate state it read for the tenant, else rules (gate_state()); a case route answers 503; the
    shadow stops."""
    hit = _SETTINGS.get(tenant)
    if hit and time.monotonic() - hit[0] < SETTINGS_TTL_S:
        return hit[1]
    snap = _client().collection("tenant_settings").document(tenant).get()
    doc = (snap.to_dict() or {}) if snap.exists else {}
    _SETTINGS[tenant] = (time.monotonic(), doc)
    return doc


_GATE_SEEN: dict[str, str] = {}         # the last desk_gate state this process read, per tenant


def gate_state(tenant: str) -> str:
    """tenant_settings/{tenant}.desk_gate as the door applies it (shared/desk_rules.gate_state): off, rules or on. A
    failed read is the last state this process read for the tenant, else rules: never off for want of a read."""
    try:
        state = desk_rules.gate_state(settings(tenant))
    except Exception as e:  # noqa: BLE001 - the rules hold while the switch cannot be read
        log.warning(json.dumps({"event": "desk_gate_unread", "surface": "chat", "tenant": tenant,
                                "error": type(e).__name__}))
        return _GATE_SEEN.get(tenant, "rules")
    _GATE_SEEN[tenant] = state
    return state


# The tenants whose desk_gate is on: the door looks a caller up for the model check only while there is one.
CHECKED = desk_recall.OnTenants(lambda: desk_recall.read_on_tenants(_client()), log, "chat")


def _check(question: str) -> dict:
    """The model check (shared/desk_recall.py) on the masked question, with the routed Desk's own Gemini client. No
    client is no check (desk_recall.unavailable()); the door logs the result's row."""
    models = _models()
    return desk_recall.check(models.gen, question) if models is not None else desk_recall.unavailable()


# ---------------------------------------------------------------- the chat door
def _read(question: str):
    """The gate's class and the masked question, in one call: the door runs it off the event loop."""
    return desk_rules.gate(question), desk_rules.mask(question)


def _turn(payload) -> str | None:
    """The question of a body ChatRequest would accept, else None (the handler's 422 answers it)."""
    if not isinstance(payload, dict):
        return None
    q, sid, brain = payload.get("question"), payload.get("session_id", "default"), payload.get("brain")
    if not isinstance(q, str) or not 1 <= len(q) <= QUESTION_MAX:
        return None
    if not isinstance(sid, str) or not SESSION.fullmatch(sid) or (brain is not None and brain not in BRAIN_NAMES):
        return None
    return q


def _bytes(obj) -> bytes:
    """Starlette's JSONResponse rendering, byte for byte, so the door's replies read like the handler's."""
    return json.dumps(obj, ensure_ascii=False, allow_nan=False, indent=None, separators=(",", ":")).encode("utf-8")


async def _reply(send, status: int, obj, headers=None) -> None:
    """A JSON reply with JSONResponse's headers, in its order: an error's own headers, then the length and the type."""
    body = _bytes(obj)
    hs = [(str(k).lower().encode("latin-1"), str(v).encode("latin-1")) for k, v in (headers or {}).items()]
    hs += [(b"content-length", str(len(body)).encode()), (b"content-type", b"application/json")]
    await send({"type": "http.response.start", "status": status, "headers": hs})
    await send({"type": "http.response.body", "body": body})


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


async def _shadow(scope, question: str, tenant: str | None) -> None:
    """The routed Desk's shadow mode (workshop lesson 10.4) runs here, beside the brain and inside the request, and
    writes its own row, never the answer, while the tenant's desk_route is shadow. The door calls it on every turn
    it hands to chat(), with the question chat() will see, and the tenant when the door looked it up (else None)."""
    return await _shadow_turn(scope, question, tenant)


async def _quietly(aw) -> None:
    try:
        await aw
    except Exception as e:  # noqa: BLE001 - the shadow never fails the turn
        log.warning(json.dumps({"event": "desk_shadow_failed", "error": type(e).__name__}))


class ChatDoor:
    def __init__(self, app):
        self.app = app

    async def _checking(self) -> bool:
        """True while some tenant's desk_gate is on: only then is a turn with no hit looked up for the model check."""
        return bool(await CHECKED.tenants())       # on the loop: only the turn that claims the read waits for it

    async def _pass(self, scope, receive, send, body: bytes, question: str, tenant: str | None):
        """chat() gets the turn, with the body as sent or its masked copy; the shadow hook runs beside it, in a task
        of its own, and the request ends when both have."""
        shadow = asyncio.create_task(_quietly(_shadow(scope, question, tenant)))
        try:
            await self.app(scope, _replay(body, receive), send)
        finally:
            await shadow

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or scope.get("method") != "POST" or scope.get("path") != PATH:
            return await self.app(scope, receive, send)
        t0 = time.monotonic()
        too_big = {"detail": f"request body over {MAX_BODY} bytes"}
        declared = Headers(scope=scope).get("content-length")
        if declared and declared.strip().isdigit() and int(declared) > MAX_BODY:
            return await _reply(send, 413, too_big)
        chunks, size = [], 0
        while True:
            msg = await receive()
            if msg["type"] == "http.disconnect":
                return None
            part = msg.get("body", b"")
            size += len(part)
            if size > MAX_BODY:
                return await _reply(send, 413, too_big)
            chunks.append(part)
            if not msg.get("more_body"):
                break
        body = b"".join(chunks)
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            payload = None
        question = _turn(payload)
        if question is None:
            return await self.app(scope, _replay(body, receive), send)
        cls, (masked, kinds) = await asyncio.to_thread(_read, question)
        local = PROFILE == "local"                 # no IAP, no Firestore: LOCAL_TENANT, the rules and no switch to read
        checked = not local and cls is None and question.strip() != "" and await self._checking()   # no words: no check
        if cls is None and not kinds and not checked:
            return await self._pass(scope, receive, send, body, question,
                                    os.environ.get("LOCAL_TENANT", "acme") if local else None)
        if local:
            user, tenant, state = {"email": None}, os.environ.get("LOCAL_TENANT", "acme"), "rules"
        else:
            try:
                user = await asyncio.to_thread(_hooks["caller"], Request(scope))
                tenant = await asyncio.to_thread(_hooks["tenant_for"], user["email"])
            except RefusedHTTP as e:
                if cls is None:                    # nothing to mask or check for a caller the handler refuses
                    return await self._pass(scope, receive, send, body, question, None)
                return await _reply(send, e.status_code, {"detail": e.detail}, getattr(e, "headers", None))
            if tenant is None:
                if cls is None:
                    return await self._pass(scope, receive, send, body, question, None)
                return await _reply(send, 403, {"detail": NOT_A_MEMBER})
            state = await asyncio.to_thread(gate_state, tenant)
        if state == "off":                         # an operator's explicit off: the body as it was sent
            return await self._pass(scope, receive, send, body, question, tenant)
        method, meter = "rule", limits.Meter(model="none")
        if cls is None and checked and state == "on":
            got = await desk_recall.run(desk_recall.POOL, _check, masked)
            (log.warning if got["outcome"] == "error" else log.info)(json.dumps(desk_recall.row("chat", tenant, got)))
            if got["case"] is not None:
                cls, method, meter = got["case"], "model", limits.Meter(model=got["model"])
                meter.allow_model_call()
                meter.charge_model(got["tokens_in"], got["tokens_out"], got["cached_tokens"])
        if cls is None:
            if kinds:
                payload["question"] = masked
                body = json.dumps(payload).encode()     # ASCII escapes: a lone surrogate reaches the handler's 422
                return await self._pass(_with_length(scope, len(body)), receive, send, body, masked, tenant)
            return await self._pass(scope, receive, send, body, question, tenant)
        sensitive = cls in desk_rules.SENSITIVE
        log.info(json.dumps({"event": "desk_gate", "surface": "chat", "tenant": tenant,
                             "user": None if sensitive else user["email"],
                             "class": "sensitive" if sensitive else cls, "rules_version": desk_rules.RULES_VERSION,
                             "method": method}))
        return await _reply(send, 200, {"answer": desk_law.template(cls), "tool_calls": [], "refusals": [],
                                        "citations": [], "brain": "desk_gate", "model": meter.model,
                                        "session_id": payload.get("session_id", "default"),
                                        "latency_ms": int((time.monotonic() - t0) * 1000),
                                        "limits": meter.summary(),
                                        "case_offer": {"case_type": cls}})


# ---------------------------------------------------------------- the case routes
class CaseId(Convertor):
    """A path segment that is a case id (shared/cases.ID): anything else is not this route's."""
    regex = "[0-9a-f]{32}"

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: str) -> str:
        return str(value)


register_url_convertor("case_id", CaseId())
router = APIRouter()
TOKEN = r"^[A-Za-z0-9_-]{8,128}$"


class CaseCreate(BaseModel):
    """What the "Raise a case" button sends. The source is always "button"; the tenant and the person are never
    fields. posh takes the unit and the contacts and no text; the others an optional first summary."""

    case_type: Literal["posh", "grievance", "privacy_request", "exit_dues", "people_query", "human_requested"]
    summary: Optional[str] = Field(default=None, max_length=cases.SUMMARY_MAX)
    unit: Optional[str] = Field(default=None, pattern=r"^[a-z0-9_-]{1,40}$")
    contacts: list[str] = Field(default_factory=list, max_length=20)
    token: Optional[str] = Field(default=None, pattern=TOKEN)
    last_working_day: Optional[date] = None
    people_ops_opt_in: bool = False


class CaseConfirm(BaseModel):
    token: str = Field(pattern=TOKEN)
    summary: Optional[str] = Field(default=None, max_length=cases.SUMMARY_MAX)
    people_ops_opt_in: Optional[bool] = None


class CaseStatus(BaseModel):
    status: Literal["acknowledged", "in_progress", "resolved", "closed"]


def _principal(request: Request, caller) -> dict:
    """Who is asking, for every Desk and case route. The chat door calls caller() itself."""
    return delegation.principal(request, caller, _hooks["tenant_for"], settings)


def _who(request: Request) -> dict:
    """The verified person, the door they came through ("direct" for the kit's own surfaces) and their tenant."""
    p = dict(_principal(request, _hooks["caller"]))
    p.setdefault("via", "direct")
    p["email"] = str(p.get("email") or "").lower()
    tenant = os.environ.get("LOCAL_TENANT", "acme") if PROFILE == "local" else _hooks["tenant_for"](p["email"])
    if tenant is None:
        raise HTTPException(403, NOT_A_MEMBER)
    return {**p, "tenant": tenant}


def _db():
    if PROFILE == "local":
        raise HTTPException(501, "the case queue keeps its records in Firestore: run the chat service on the gcp profile")
    return _client()


def _queues(tenant: str) -> dict:
    try:
        return (settings(tenant) or {}).get("case_queues") or {}
    except Exception:  # noqa: BLE001 - a case shows its queue and clock, so it waits for a readable configuration
        raise HTTPException(503, "the company's case queues could not be read: try again in a minute")


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except cases.CaseError as e:
        raise HTTPException(e.status, e.detail)


def _raiser(db, who: dict) -> list[str]:
    held = roles.roles_for(db, who["tenant"], who["email"])
    if "case" not in roles.desks(held):
        raise HTTPException(403, "your roles in this company do not include raising a case")
    return held


@router.post("/v1/cases")
def create_case(body: CaseCreate, request: Request) -> dict:
    who = _who(request)
    db = _db()
    _raiser(db, who)
    queues = _queues(who["tenant"])
    if body.case_type == "posh":
        if body.summary:
            raise HTTPException(422, "a POSH case holds no text: choose the unit and whom to contact")
        if not body.token:
            raise HTTPException(422, "a POSH case takes a client token, so a doubled press opens one case")
        rec = _call(cases.open_posh, db, who["tenant"], who["email"], body.unit or "", body.contacts, queues,
                    token=body.token, via=who["via"])
    else:
        rec = _call(cases.draft, db, who["tenant"], who["email"], body.case_type, queues, summary=body.summary,
                    via=who["via"], last_working_day=body.last_working_day, people_ops_opt_in=body.people_ops_opt_in)
    return cases.view(rec, queues)


@router.post("/v1/cases/{case_id:case_id}/confirm")
def confirm_case(case_id: str, body: CaseConfirm, request: Request) -> dict:
    who = _who(request)
    db = _db()
    _raiser(db, who)
    queues = _queues(who["tenant"])
    rec = _call(cases.confirm, db, case_id, who["tenant"], who["email"], body.token, queues, summary=body.summary,
                people_ops_opt_in=body.people_ops_opt_in)
    return cases.view(rec, queues)


@router.post("/v1/cases/{case_id:case_id}/cancel")
def cancel_case(case_id: str, request: Request) -> dict:
    who = _who(request)
    db = _db()
    queues = _queues(who["tenant"])            # before the change: a failed read must not hide a change made
    rec = _call(cases.cancel, db, case_id, who["tenant"], who["email"])
    return cases.view(rec, queues)


@router.get("/v1/cases")
def list_cases(request: Request) -> dict:
    who = _who(request)
    db = _db()
    held = roles.roles_for(db, who["tenant"], who["email"])
    queues = _queues(who["tenant"])
    got = cases.list_for(db, who["tenant"], who["email"], held)
    return {"email": who["email"], "tenant": who["tenant"], "roles": held,
            "inbox": [cases.view(r, queues) for r in got["inbox"]], "mine": [cases.view(r, queues) for r in got["mine"]],
            "more": got["more"]}


@router.get("/v1/cases/offer")
def case_offer(request: Request) -> dict:
    """What the person may raise in their company, from the settings the doors read (once a minute): the Desk's
    switches, the case types whose queue is configured, and, when the POSH section is complete, each office's Internal
    Committee members and Local Committee contact - the POSH card. No case is read and no text is taken."""
    who = _who(request)
    db = _db()
    held = _raiser(db, who)
    try:
        doc = settings(who["tenant"]) or {}
    except Exception:  # noqa: BLE001 - the card waits for a readable configuration
        raise HTTPException(503, "the company's case queues could not be read: try again in a minute")
    queues = doc.get("case_queues") or {}
    types = [t for t in desk_law.CASE_TYPES if (t == "posh" and not cases.posh_errors(queues))
             or (t != "posh" and cases.queue_for(t, queues) is not None)]
    posh = cases.posh_offer(queues)
    return {"email": who["email"], "tenant": who["tenant"], "roles": held,
            "desk_gate": desk_rules.gate_state(doc), "desk_route": desk_mode(doc)[0],
            "types": types, "posh": posh or None}


@router.get("/v1/cases/{case_id:case_id}")
def get_case(case_id: str, request: Request) -> dict:
    who = _who(request)
    db = _db()
    held = roles.roles_for(db, who["tenant"], who["email"])
    rec = _call(cases.read, db, case_id, who["tenant"], who["email"], held)
    return cases.view(rec, _queues(who["tenant"]))


@router.post("/v1/cases/{case_id:case_id}/status")
def set_case_status(case_id: str, body: CaseStatus, request: Request) -> dict:
    who = _who(request)
    db = _db()
    held = roles.roles_for(db, who["tenant"], who["email"])
    queues = _queues(who["tenant"])            # before the change: a failed read must not hide a change made
    rec = _call(cases.set_status, db, case_id, who["tenant"], who["email"], held, body.status)
    return cases.view(rec, queues)


# ---------------------------------------------------------------- the routed Desk (workshop lesson 10.4)
MODES = ("off", "shadow", "on", "single")
SERVED = ("on", "single")                   # the modes in which /v1/desk answers a person
EVAL_ROLE = "desk_eval"                     # shared/roles.py: the Desk's eval accounts
ARMS = ("B", "C", "Astar")                  # B the routed Desk; C code only; Astar one agent (desk_router's arms)
ROUTE_RATE = 120                            # /v1/route calls a minute per eval account, in each worker process
SHADOW_TIMEOUT_S = 10.0                     # the router's own 8 s budget, and a little
COVERAGE_TTL_S = 300                        # a tenant's doc_type registry, read at most once every 5 minutes
SHADOW_TENANTS_TTL_S = 60                   # which tenants are in shadow, read at most once a minute per process
SHADOW_THREADS = max(2, int(os.environ.get("DESK_SHADOW_THREADS", "8")))
SHADOW_DECIDES = SHADOW_THREADS // 2        # decides at once: the other threads are left for the lookups
SHADOW_POOL = ThreadPoolExecutor(max_workers=SHADOW_THREADS, thread_name_prefix="documind-desk-shadow")
SHADOW_ROUTER_POOL = ThreadPoolExecutor(max_workers=2 * SHADOW_DECIDES,       # L1 and the vote; never desk_router.POOL
                                        thread_name_prefix="documind-desk-shadow-router")
_SHADOW_SLOTS = threading.BoundedSemaphore(SHADOW_DECIDES)
_RATE: dict[str, list[float]] = {}
_RATE_LOCK = threading.Lock()
_COVERAGE: dict[str, tuple[float, dict]] = {}
_GRAPH_LOCK = threading.Lock()


def desk_mode(doc) -> tuple[str, str | None]:
    """(mode, single desk) from tenant_settings: desk_route off, shadow, on or single, and for single the one answer
    desk desk_single names. Anything else - a missing field, a typo, single without a valid desk_single - is off."""
    doc = doc if isinstance(doc, dict) else {}
    mode = str(doc.get("desk_route") or "off").strip().lower()
    single = str(doc.get("desk_single") or "").strip().lower()
    if mode not in MODES or (mode == "single" and single not in desk_routes.ANSWER_DESKS):
        return "off", None
    return mode, (single if mode == "single" else None)


def desks_off(doc) -> list[str]:
    """The answer desks the company has switched off (desk_off): each is not_covered, with no search and no model."""
    v = (doc or {}).get("desk_off") if isinstance(doc, dict) else None
    v = v.split(",") if isinstance(v, str) else v if isinstance(v, (list, tuple)) else []
    return sorted({str(d).strip().lower() for d in v} & set(desk_routes.ANSWER_DESKS))


def _coverage(db, tenant: str) -> dict:
    """{answer desk: covered} from the tenant's doc_type registry (shared/doc_types.py), read at most once every 5
    minutes per instance. A failed or empty read is {}, every desk covered, and is not kept: coverage spares a
    search that would find nothing; rag-api's tenant filter is what keeps a search in its tenant."""
    hit = _COVERAGE.get(tenant)
    if hit and time.monotonic() - hit[0] < COVERAGE_TTL_S:
        return dict(hit[1])
    try:
        from shared import doc_types
        classes = {e.get("doc_type") for e in doc_types.read_registry(db, tenant).values() if isinstance(e, dict)}
    except Exception as e:  # noqa: BLE001 - the router's coverage check is one check of several
        log.warning(json.dumps({"event": "desk_coverage_unread", "tenant": tenant, "error": type(e).__name__}))
        return {}
    if not classes:
        return {}
    cov = desk_routes.coverage(classes)
    _COVERAGE[tenant] = (time.monotonic(), cov)
    return dict(cov)


@lru_cache(maxsize=1)
def _gemini():
    return desk_router.GeminiModels.for_project(os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT", ""))


def _models():
    """The live classifier, arbiter and query embedding (desk_router.GeminiModels), built once per process. None when
    they cannot be built: decide() then takes its fallback, never a 500."""
    try:
        return _gemini()
    except Exception as e:  # noqa: BLE001 - the router's failure path answers the turn
        log.warning(json.dumps({"event": "desk_models_unbuilt", "error": type(e).__name__}))
        return None


def _desk_graph():
    import desk_graph       # LangGraph: loaded on the first routed turn, not when the door loads
    return desk_graph


def _graph(app):
    """The desk graph, compiled once per process on the service's own checkpointer (agent.py's lifespan)."""
    saver = app.state.checkpointer
    g = getattr(app.state, "desk_graph", None)
    if g is None or g.checkpointer is not saver:
        with _GRAPH_LOCK:
            g = getattr(app.state, "desk_graph", None)
            if g is None or g.checkpointer is not saver:
                g = app.state.desk_graph = _desk_graph().build(saver)
    return g


def _desk_settings(tenant: str) -> dict:
    try:
        return settings(tenant) or {}
    except Exception:  # noqa: BLE001 - the mode, the queues and the off list come from here: no guess
        raise HTTPException(503, "the company's Desk settings could not be read: try again in a minute")


def _route_ctx(db, tenant: str, held: list, doc: dict, meter, arm: str | None = None) -> dict:
    """decide()'s ctx from what this service reads: the roles, the mode, coverage (a switched-off desk is not
    covered), the clause-prefix map, the exemplar index (not read for single mode or arms C and Astar, which use
    none), the parts allowed. The thread's previous turn is added by the caller."""
    _, single = desk_mode(doc)
    queues = (doc or {}).get("case_queues") or {}
    cov = {**_coverage(db, tenant), **{d: False for d in desks_off(doc)}}
    index = [] if single or arm in ("C", "Astar") else desk_router.load_index(db, tenant)
    return {"tenant": tenant, "roles": list(held), "meter": meter, "single": single, "coverage": cov,
            "clause_prefixes": sorted(queues.get("clause_prefixes") or {}), "index": index,
            "max_parts": 2 if (doc or {}).get("desk_max_parts") == 2 else 1, "arm": arm, "now": time.time()}


def _within_rate(email: str) -> bool:
    now = time.monotonic()
    with _RATE_LOCK:
        recent = [t for t in _RATE.get(email, ()) if now - t < 60.0]
        ok = len(recent) < ROUTE_RATE
        if ok:
            recent.append(now)
        _RATE[email] = recent
        return ok


def _last_question(values: dict) -> str | None:
    """The thread's last question, as it was checkpointed (masked)."""
    for m in reversed(values.get("messages") or []):
        if getattr(m, "type", None) == "human" and isinstance(m.content, str) and m.content.strip():
            return m.content
    return None


def _open_draft(db, who: dict, held: list, draft_id: str | None) -> tuple[str | None, str | None]:
    """(id, case type) of the draft the page shows, when it is this person's own, still a draft and unexpired; else
    (None, None). The type goes on the turn, so a grievance or privacy draft's turn is logged as sensitive."""
    if not draft_id:
        return None, None
    try:
        rec = cases.read(db, draft_id, who["tenant"], who["email"], held)
    except Exception:  # noqa: BLE001 - not theirs, gone or unreadable: no draft is open
        return None, None
    exp = rec.get("expire_at")
    live = hasattr(exp, "timestamp") and exp.timestamp() > time.time()
    if rec.get("status") == "draft" and rec.get("requester") == who["email"] and live:
        return draft_id, rec.get("case_type")
    return None, None


class DeskRequest(BaseModel):
    """One turn of the routed Desk: a question, or a chip the thread's last reply offered. The tenant, the person
    and the thread's previous turn are never fields; any other field is a 422."""

    model_config = {"extra": "forbid"}
    question: Optional[str] = Field(default=None, min_length=1, max_length=QUESTION_MAX)
    session_id: str = Field(default="default", pattern=r"^[A-Za-z0-9_-]{1,64}$")
    chip: Optional[Literal["handbook", "statute", "case"]] = None
    draft_id: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{32}$")
    arm: Optional[Literal[ARMS]] = None


class RouteRequest(BaseModel):
    """The decision for one route-set row. prev_question and prev_route stand in for a follow-up row's thread."""

    model_config = {"extra": "forbid"}
    question: str = Field(min_length=1, max_length=QUESTION_MAX)
    prev_question: Optional[str] = Field(default=None, min_length=1, max_length=QUESTION_MAX)
    prev_route: Optional[Literal[desk_routes.ROUTES]] = None
    arm: Optional[Literal[ARMS]] = None


def _desk_row(surface: str, who: dict, session_id: str | None, mode: str, arm: str | None, chip: str | None,
              decision: dict, meter, outcome: str | None, retrieve_calls: int, citations: int, latency_ms: int,
              tool_calls=(), refusals=()) -> dict:
    """One "desk" row: every field named here, no question, and for a sensitive case no person and no session."""
    rec = desk_router.record(decision)
    sensitive = rec["sensitivity_tier"] == "sensitive"
    used = meter.row()
    # via stays "gchat" on a sensitive row: the bridge names a person only on a turn this reply showed is no sensitive
    # case, or one the Desk never decided (services/gchat/main.py row()), whatever rules the bridge's image gates by.
    return {"event": "desk", "surface": surface, "tenant": who["tenant"],
            "user": None if sensitive else who["email"], "session_id": None if sensitive else session_id,
            "via": who.get("via") or "direct", "delegate": None if sensitive else who.get("delegate"),
            "mode": mode, "arm": arm or "B", "chip": chip, "route": rec["route"], "method": rec["method"],
            "confidence": rec["confidence"], "desk": rec["desk"], "accepted_by": rec["accepted_by"],
            "gate": rec["gate"], "anchors": rec["anchors"], "case_type": rec["case_type"], "outcome": outcome,
            "parts": rec["parts"], "chips": rec["chips"], "second_route": rec["second_route"],
            "knn_route": rec["knn_route"], "knn_share": rec["knn_share"], "knn_sim": rec["knn_sim"],
            "l1_error": rec["l1_error"], "l2": rec["l2"], "l2_error": rec["l2_error"],
            "fallback_reason": rec["fallback_reason"], "denied_reason": rec["denied_reason"],
            "covered": rec["covered"], "committed": rec["committed"], "masked": rec["masked"],
            "router_ms": rec["router_ms"], "router_calls": rec["router_calls"], "model_calls": used["model_calls"],
            "retrieve_calls": retrieve_calls, "citations": citations, "latency_ms": latency_ms,
            "tool_calls": list(tool_calls), "refusals": list(refusals),
            "model": used["model"], "tokens_in": used["tokens_in"], "tokens_out": used["tokens_out"],
            "cached_tokens": used["cached_tokens"], "cost_usd": used["cost_usd"],
            "rag_cost_usd": used["rag_cost_usd"], "stopped_by": used["stopped_by"],
            "prompt_version": rec["prompt_version"], "rules_version": rec["rules_version"]}


def _shadow_row(tenant: str, email: str, decision: dict, meter, shadow_ms: int) -> dict:
    """One "desk_shadow" row: what the routed Desk would have done with a /v1/chat turn. Every field named here, no
    question, and for a sensitive case no person."""
    rec = desk_router.record(decision)
    sensitive = rec["sensitivity_tier"] == "sensitive"
    used = meter.row()
    return {"event": "desk_shadow", "surface": "chat", "tenant": tenant, "user": None if sensitive else email,
            "mode": "shadow", "route": rec["route"], "method": rec["method"], "confidence": rec["confidence"],
            "desk": rec["desk"], "accepted_by": rec["accepted_by"], "gate": rec["gate"], "anchors": rec["anchors"],
            "case_type": rec["case_type"], "parts": rec["parts"], "chips": rec["chips"],
            "second_route": rec["second_route"], "knn_route": rec["knn_route"], "knn_share": rec["knn_share"],
            "knn_sim": rec["knn_sim"], "l1_error": rec["l1_error"], "l2": rec["l2"], "l2_error": rec["l2_error"],
            "fallback_reason": rec["fallback_reason"], "denied_reason": rec["denied_reason"],
            "covered": rec["covered"], "committed": rec["committed"], "masked": rec["masked"],
            "router_ms": rec["router_ms"], "router_calls": rec["router_calls"], "model_calls": used["model_calls"],
            "shadow_ms": shadow_ms, "model": used["model"], "tokens_in": used["tokens_in"],
            "tokens_out": used["tokens_out"], "cached_tokens": used["cached_tokens"], "cost_usd": used["cost_usd"],
            "stopped_by": used["stopped_by"], "prompt_version": rec["prompt_version"],
            "rules_version": rec["rules_version"]}


@router.post("/v1/desk")
def desk_turn(body: DeskRequest, request: Request) -> dict:
    t0 = time.monotonic()
    who = _who(request)
    if (body.question is None) == (body.chip is None):
        raise HTTPException(422, "send a question or a chip, one of the two")
    db = _db()
    held = roles.roles_for(db, who["tenant"], who["email"])
    evaluator = EVAL_ROLE in held
    if body.arm is not None and not evaluator:
        raise HTTPException(403, "arm is for the Desk's eval accounts (desk_eval)")
    doc = _desk_settings(who["tenant"])
    mode, _ = desk_mode(doc)
    if mode not in SERVED and not evaluator:
        raise HTTPException(403, "the routed Desk is not switched on for your company")
    dg = _desk_graph()
    meter = limits.Meter(model=desk_router.L1_MODEL)
    graph = _graph(request.app)
    config = dg.thread(_hooks["thread_config"], who["tenant"], who["email"], body.session_id)
    question, route_tried, partial = body.question, None, None
    if body.chip is not None:                  # the thread's own last question, to a desk its last reply offered
        values = graph.get_state(config).values or {}
        offered = {c.get("desk") for c in values.get("offered_chips") or () if isinstance(c, dict)}
        question = _last_question(values)
        if body.chip not in offered or not question:
            raise HTTPException(409, "that choice is not on offer in this conversation: ask the question again")
        if body.chip == "case":
            route_tried = values.get("last_route")
            partial = [c["chunk_id"] for s in values.get("sections") or () for c in s.get("citations") or ()
                       if isinstance(c, dict) and c.get("chunk_id")]
    ctx = _route_ctx(db, who["tenant"], held, doc, meter, arm=body.arm)
    draft_id, draft_type = _open_draft(db, who, held, body.draft_id)
    ctx.update(dg.previous(graph, config), chip=body.chip, draft_open=draft_id, draft_case_type=draft_type)
    decision = desk_router.decide(question, ctx, _models())
    queues = doc.get("case_queues") or {}
    turn = {"tenant": who["tenant"], "email": who["email"], "roles": held, "db": db, "queues": queues,
            "meter": meter, "via": who.get("via") or "direct", "assertion": who.get("assertion") or None,
            "draft_open": ctx["draft_open"], "desks_off": desks_off(doc), "route_tried": route_tried,
            "partial_answer_citations": partial, "clause_notes": doc.get("clause_notes"),
            "clause": desk_router.clause_of(decision.get("question") or "", ctx["clause_prefixes"])}
    out = dg.run_turn(graph, decision, turn, config)
    ct = decision.get("case_type")
    case, offer = out["case"], None
    offered = decision["route"] == "case" and decision["method"] != "draft"     # a draft turn points to the draft
    if offered and ct == "posh":                         # the POSH card: cases.posh_offer(), as /v1/cases/offer
        case, offer = None, out["case"]
    elif offered and ct:
        offer = {"case_type": ct}
    latency_ms = int((time.monotonic() - t0) * 1000)
    log.info(json.dumps(_desk_row("desk", who, body.session_id, mode, body.arm, body.chip, decision, meter,
                                  out["outcome"], out["retrieve_calls"], len(out["citations"]), latency_ms,
                                  out["tool_calls"], out["refusals"])))
    return {"email": who["email"], "tenant": who["tenant"], "session_id": body.session_id, "mode": mode,
            "arm": body.arm or "B", "route": decision["route"], "method": decision["method"],
            "outcome": out["outcome"], "answer": out["answer"], "note": out["note"], "sections": out["sections"],
            "citations": out["citations"], "chips": out["chips"], "case": case, "case_offer": offer,
            "tool_calls": out["tool_calls"], "retrieve_calls": out["retrieve_calls"],
            "model_calls": meter.model_calls,
            "decision": out["route"], "latency_ms": latency_ms, "limits": meter.summary()}


@router.post("/v1/route")
def route_turn(body: RouteRequest, request: Request) -> dict:
    t0 = time.monotonic()
    who = _who(request)
    if not _within_rate(who["email"]):
        raise HTTPException(429, f"more than {ROUTE_RATE} routes a minute from this account: wait a minute",
                            headers={"Retry-After": "60"})
    db = _db()
    held = roles.roles_for(db, who["tenant"], who["email"])
    if EVAL_ROLE not in held:
        raise HTTPException(403, "POST /v1/route is for the Desk's eval accounts (desk_eval)")
    if (body.prev_question is None) != (body.prev_route is None):
        raise HTTPException(422, "prev_question and prev_route go together")
    prev = None
    if body.prev_question is not None:
        if desk_rules.gate(body.prev_question):       # it would reach the prompt: the gate's words reach no model
            raise HTTPException(422, "prev_question is one the gate hands to a person: send it as a question")
        prev = desk_rules.mask(body.prev_question)[0][:desk_router.PREV_CHARS]
    doc = _desk_settings(who["tenant"])
    mode, _ = desk_mode(doc)
    meter = limits.Meter(model=desk_router.L1_MODEL)
    ctx = _route_ctx(db, who["tenant"], held, doc, meter, arm=body.arm)
    if prev is not None:                       # as evals/route_eval.py's route_run sets a follow-up row
        ctx.update(prev_route=body.prev_route, prev_question=prev, prev_at=ctx["now"] - 60,
                   prev_clarified=body.prev_route == "clarify")
    decision = desk_router.decide(body.question, ctx, _models())
    latency_ms = int((time.monotonic() - t0) * 1000)
    log.info(json.dumps(_desk_row("route", who, None, mode, body.arm, None, decision, meter, None, 0, 0, latency_ms)))
    return {"email": who["email"], "tenant": who["tenant"], "mode": mode, "arm": body.arm or "B",
            "route": decision["route"], "desk": decision["desk"], "method": decision["method"],
            "case_type": decision["case_type"], "decision": desk_router.record(decision),
            "model_calls": meter.model_calls, "router_ms": decision["router_ms"],
            "cost_inr": round(meter.spent_inr(), 6), "latency_ms": latency_ms}


@router.get("/v1/desk/check")
def desk_check(request: Request) -> dict:
    """Who this request serves, and their tenant, refused as POST /v1/desk refuses a caller before any turn (the
    principal, the roster, the local profile, the routed Desk's mode): a 403 names why not. Reads no case, takes no
    text."""
    who = _who(request)
    db = _db()
    mode, _ = desk_mode(_desk_settings(who["tenant"]))
    if mode not in SERVED and EVAL_ROLE not in roles.roles_for(db, who["tenant"], who["email"]):
        raise HTTPException(403, "the routed Desk is not switched on for your company")
    return {"email": who["email"], "tenant": who["tenant"], "via": who["via"]}


# ---------------------------------------------------------------- shadow mode
def _read_shadow_tenants(db) -> frozenset:
    """The tenants whose desk_route is exactly "shadow" (as make desk writes it), by one query: one attempt, at most
    desk_recall.READ_TIMEOUT_S (Firestore's default retries for about 300 s)."""
    from google.cloud.firestore_v1.base_query import FieldFilter
    q = db.collection("tenant_settings").where(filter=FieldFilter("desk_route", "==", "shadow"))
    return frozenset(s.id for s in q.stream(retry=None, timeout=desk_recall.READ_TIMEOUT_S))


def _shadowing():
    """The shadow's tenants as CHECKED reads the door's: desk_recall.OnTenants, at most once every SHADOW_TENANTS_TTL_S
    per process, by one thread at a time, so a turn waits at most READ_TIMEOUT_S for it, once a minute. A failed read
    keeps the last set (none before the first read works): the set only says which turns to look at, and each one's
    own tenant_settings still decides. Its line is desk_shadow_tenants_unread, not the gate's paged one."""
    return desk_recall.OnTenants(lambda: _read_shadow_tenants(_client()), log, "chat", ttl_s=SHADOW_TENANTS_TTL_S,
                                 event="desk_shadow_tenants_unread")


SHADOWING = _shadowing()


def shadow_tenants() -> frozenset:
    """The tenants in shadow (SHADOWING): the last set while it is fresh, else one bounded read."""
    return SHADOWING.get()


def _skipped(tenant: str | None, reason: str) -> None:
    log.info(json.dumps({"event": "desk_shadow_skipped", "surface": "chat", "tenant": tenant, "reason": reason}))
    return None


def _shadow_work(scope, question: str, tenant: str | None, t0: float) -> dict | None:
    """The caller, the tenant and its mode, then decide() with its own Meter, and the "desk_shadow" row logged here,
    so a decide that outlives the request's wait still writes its row. None and no row when the tenant is not in
    shadow mode, its desk_gate is off (or unread), or chat() refuses the caller itself. None with a
    "desk_shadow_skipped" line, and no model call, when SHADOW_DECIDES decides are running already ("busy") or
    SHADOW_TIMEOUT_S has passed before decide() starts ("late"). A turn the gate hands to a person as posh, grievance
    or privacy_request writes no row, only a "desk_shadow_skipped" line with no tenant ("withheld"): the turn's own
    chat row names the person, so even a row with no user could be matched to it by time."""
    if time.monotonic() - t0 >= SHADOW_TIMEOUT_S:
        return _skipped(tenant, "late")
    request, user = Request(scope), None
    if tenant is None:                         # the door did not look the tenant up for this turn
        try:
            user = _hooks["caller"](request)
        except RefusedHTTP:
            return None
        tenant = _hooks["tenant_for"](str(user.get("email") or "").lower())
        if tenant is None:
            return None
    try:
        doc = settings(tenant)
    except Exception:  # noqa: BLE001 - no shadow without the mode: the shadow is a measurement, so it does not guess
        return None
    if desk_mode(doc)[0] != "shadow":
        return None
    if desk_rules.gate_state(doc) == "off":   # the door answers every sensitive turn itself unless it is off
        return None
    if user is None:
        try:
            user = _hooks["caller"](request)
        except RefusedHTTP:
            return None
    email = str(user.get("email") or "").lower()
    if not _SHADOW_SLOTS.acquire(blocking=False):
        return _skipped(tenant, "busy")
    try:
        db = _client()
        held = roles.roles_for(db, tenant, email)
        meter = limits.Meter(model=desk_router.L1_MODEL)
        ctx = _route_ctx(db, tenant, held, doc, meter)
        if time.monotonic() - t0 >= SHADOW_TIMEOUT_S:
            return _skipped(tenant, "late")
        decision = desk_router.decide(question, {**ctx, "pool": SHADOW_ROUTER_POOL}, _models())
    finally:
        _SHADOW_SLOTS.release()
    if decision.get("gate") in desk_rules.SENSITIVE:     # the chat row beside it names the person: no row at all
        return _skipped(None, "withheld")
    row = _shadow_row(tenant, email, decision, meter, int((time.monotonic() - t0) * 1000))
    log.info(json.dumps(row))
    return row


def _shadow_decide(scope, question: str, tenant: str | None, t0: float) -> dict | None:
    """In SHADOW_POOL: _shadow_work(), with an error logged here, since the request may have stopped waiting."""
    try:
        return _shadow_work(scope, question, tenant, t0)
    except Exception as e:  # noqa: BLE001 - the shadow never fails anything
        log.warning(json.dumps({"event": "desk_shadow_failed", "error": type(e).__name__}))
        return None


async def _shadow_turn(scope, question: str, tenant: str | None) -> None:
    """The shadow hook's body. Nothing on the local profile (no settings to read), nothing while no tenant is in
    shadow (shadow_tenants()), and nothing for a tenant the door looked up that is not in shadow. Otherwise
    _shadow_decide() in SHADOW_POOL, and the request waits up to SHADOW_TIMEOUT_S for it: a decide not started by
    then is cancelled, and one still running writes its own row when it ends ("desk_shadow_late" says so)."""
    if PROFILE == "local":
        return None
    shadowing = SHADOWING.fresh()
    if shadowing is None:
        shadowing = await asyncio.to_thread(shadow_tenants)
    if not shadowing or (tenant is not None and tenant not in shadowing):
        return None
    t0 = time.monotonic()
    work = SHADOW_POOL.submit(_shadow_decide, scope, question, tenant, t0)
    try:
        await asyncio.wait_for(asyncio.wrap_future(work), SHADOW_TIMEOUT_S)
    except asyncio.TimeoutError:
        log.info(json.dumps({"event": "desk_shadow_late", "surface": "chat", "tenant": tenant,
                             "waited_ms": int((time.monotonic() - t0) * 1000)}))
    return None


def install(app, caller, tenant_for, thread_config) -> None:
    """Mount the case routes and put the chat door in front of POST /v1/chat. caller(request) is agent.py's identity
    (401 when it cannot say who), tenant_for(email) the roster's answer (None is a 403), and thread_config the
    checkpointer's thread id, kept for the routed Desk. Starlette makes the middleware added last the outermost, so a
    line added after this one wraps the door."""
    _hooks.update(caller=caller, tenant_for=tenant_for, thread_config=thread_config)
    app.include_router(router)
    app.add_middleware(ChatDoor)
