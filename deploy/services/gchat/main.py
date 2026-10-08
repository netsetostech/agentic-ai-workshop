"""documind-gchat: the Google Chat door onto the DocuMind Desk (workshop lesson 10.4).

An employee messages the "HR Desk" app in Google Chat, in a direct message, and gets the Desk the Desk page gives: a
cited handbook or statute answer as a card, a question back with two buttons, a case to confirm, or the POSH template
with no model call. This service makes no model call, opens no Postgres, reads nothing in the default Firestore
database and calls no service but the chat service. The one thing it can do is ask the Desk on someone's behalf: it
names the person in X-DocuMind-Principal, and the Desk decides whether to believe it (services/chat/delegation.py).

    POST /        Chat's events. Cloud Run's IAM admits three invokers; the code then verifies the Google ID token
                  for SELF_URL (shared/iap.bearer_email) and admits only GCHAT_CALLER, the Workspace add-on agent of
                  this project's app. Everything else is a 401 and a gchat_verify_failed row, before anything else.
    POST /work    Pub/Sub's push of one queued question: only documind-gchatpush-sa, and only from the
                  documind-gchat-push subscription. The answer is posted into the direct message as the app.
    GET /health

A PERSON'S MESSAGE, in order (POST /):
    1. the token, as above
    2. normalise the event, from either shape (events.py). "Added to space" gets the welcome card; anything that is
       not a person's message or a button press gets no reply
    3. the gate, before every other check: shared/desk_rules.gate() on every text field. A hit is answered now, every
       time, whatever its space, attachment, length or rate, and is never claimed or queued: a synchronous delegated
       POST /v1/desk with a GATE_BUDGET_S budget, the Desk's own card as the reply. Slower than that, or over 4,000
       characters: the Desk's fixed text (shared/desk_law.py) and a "Show my options" button. With no sender email,
       or in a named space: the fixed text only, no button, and in a space "message me directly"
    4. the sender: type HUMAN and an email, lower-cased, in a shape the Desk takes as one person's address
       (events.is_person); else "could not read your account" and a gchat_no_email row
    5. direct messages only; typed text only; 4,000 characters at most
    6. the duplicate claim (claims.py)
    7. RATE_PER_MIN questions a minute per sender in each instance
    8. a delegated GET /v1/desk/check, CHECK_BUDGET_S: a 403 is the matching fixed reply (not on a roster, door
       off); a timeout lets the question go on, and the worker shows any refusal. Not in sync-only mode, where the
       Desk call itself refuses the same way and the two together could outlast Chat's 30 s
    9. mask the question (desk_rules.mask), mark the claim queued, publish {key, kind, email, session_id, space,
       thread, question} to documind-gchat-work, and acknowledge in the HTTP response, which costs no Chat API write

A BUTTON PRESS carries an action and its parameters, never text (cards.py): a chip goes through the queue as a
question does; Confirm, Cancel, "Create a confidential record" and "Show my options" are answered now, each through a
delegable Desk route with a client token built from the pressed message, so a doubled press opens one case.

THE WORKER (POST /work): lease the claim and count the attempt; a delegated POST /v1/desk with WORK_TIMEOUT_S; render
the card and post it with spaces.messages.create under the client- id; mark it answered. An error releases the claim
and answers 503, so Pub/Sub retries; the MAX_ATTEMPTS-th attempt posts "could not reach the HR Desk" and acknowledges.
A post that no credential may make (post.PostError.auth) is acknowledged at once: a retry would only ask the Desk the
same question again. No dead-letter topic holds question text. The worst case of one push, WORK_TIMEOUT_S for the Desk
and four posts of post.POST_TIMEOUT_S, stays under the subscription's 300 s ack deadline and the service's timeout.

GCHAT_ASYNC = False is the fallback if this app cannot post through the Chat API (post.py): every question is then
answered in the HTTP response, with SYNC_ONLY_BUDGET_S and no /v1/desk/check, and needs no Chat API credential. No
reply in that mode promises a later answer: a duplicate gets replies.TAKEN, never the acknowledgement.

THE ROWS. None carries question text, a token, or an error's message.
    gchat                 {kind, outcome, tenant, user, class, queued, latency_ms}: one per event. class is "sensitive"
                          for posh, grievance and privacy_request, as on the Desk's own row; a gate hit the Desk
                          answered carries the Desk's class unless the bridge's own is sensitive. user is the sender
                          only when the row's class is known and not sensitive, or the Desk never had the turn's words
                          (the bridge answered before any Desk call or publish); else null, so a row written before the
                          Desk classified a turn (queued, duplicate, a failed call) cannot be paired by its time with
                          the Desk's sensitive row of that turn
    gchat_answer          {attempts, outcome, desk_ms, post_ms}: one per answer the worker posts
    gchat_verify_failed   {path, reason, aud_is_self_url, aud_has_trailing_slash, email_is_gchat_caller,
                          email_is_chat_system, iss_is_google}: booleans from the refused token's unverified claims
    gchat_no_email        {sender_is_human, has_sender_email, email_is_person, has_user_id_token}
    gchat_probe           booleans and enums, on the first event, the first press and the first post of an instance
"""
from __future__ import annotations

import base64
import binascii
import json
import logging
import os
import re
import sys
import threading
import time

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response

import cards
import claims
import events
import post
import replies
from shared import desk_law, desk_rules, iap

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)  # bare JSON -> Cloud Run jsonPayload
log = logging.getLogger("documind.gchat")

SELF_URL = os.environ.get("SELF_URL", "").rstrip("/")
CHAT_URL = os.environ.get("CHAT_URL", "").rstrip("/")
GCHAT_CALLER = os.environ.get("GCHAT_CALLER", "").strip().lower()
PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()

GCHAT_ASYNC = True              # False: answer every question in the HTTP response (post.py says when)
PUSH_ACCOUNT = "documind-gchatpush-sa"
BRIDGE_ACCOUNT = "documind-gchat-sa"
SUBSCRIPTION = "documind-gchat-push"
CHAT_SYSTEM = "chat@system.gserviceaccount.com"     # the classic model's caller, named only in the refused-token row
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
PRINCIPAL_HEADER = "X-DocuMind-Principal"
GATE_BUDGET_S = 15
CHECK_BUDGET_S = 5
PRESS_BUDGET_S = 10
SYNC_ONLY_BUDGET_S = 25
# One push, at worst: the Desk (WORK_TIMEOUT_S) and four posts (the card and "could not reach", each trying two
# credentials for post.POST_TIMEOUT_S): 180 + 4 x 20 = 260 s, under the push subscription's 300 s ack deadline and
# the service's --timeout=300 (terraform/gchat.tf, commands/gchat.sh), with the claim's writes in the rest.
WORK_TIMEOUT_S = 180
RATE_PER_MIN = 6
MAX_ATTEMPTS = 5
BODY_MAX = 1_000_000
ACTS = ("chip", "confirm", "cancel", "posh", "options")
CASE_ID = re.compile(r"^[0-9a-f]{32}$")
UNIT = re.compile(r"^[a-z0-9_-]{1,40}$")
SEEN_DENIALS = (401, 403, 404, 409, 410, 422)       # the Desk refused: a reply, never a retry

app = FastAPI(title="documind-gchat")


class DeskError(Exception):
    """The Desk did not answer 2xx. status 0: no answer at all (a timeout or no connection). detail: the Desk's own
    string reason, or None."""

    def __init__(self, status: int, detail: str | None = None):
        super().__init__(f"status {status}")
        self.status, self.detail = status, detail


# ---------------------------------------------------------------- the Desk, on someone's behalf
def desk(method: str, path: str, email: str, body: dict | None = None, timeout: float = CHECK_BUDGET_S) -> dict:
    """One delegated Desk call: the bridge's own ID token for CHAT_URL, minted per call, and the person named in
    X-DocuMind-Principal. Raises DeskError."""
    import requests
    from google.auth.transport.requests import Request as AuthRequest
    from google.oauth2 import id_token

    if not CHAT_URL:
        raise DeskError(0)
    try:
        token = id_token.fetch_id_token(AuthRequest(), CHAT_URL)
        resp = requests.request(method, CHAT_URL + path, json=body, timeout=timeout,
                                headers={"Authorization": f"Bearer {token}", PRINCIPAL_HEADER: email})
    except Exception:  # noqa: BLE001 - no token, no connection or too slow: no answer
        raise DeskError(0)
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail")
        except Exception:  # noqa: BLE001 - not JSON: no reason to show
            detail = None
        raise DeskError(resp.status_code, detail if isinstance(detail, str) else None)
    try:
        got = resp.json()
    except Exception:  # noqa: BLE001 - not the Desk's JSON: no answer
        raise DeskError(0)
    if not isinstance(got, dict):
        raise DeskError(0)
    return got


# ---------------------------------------------------------------- the token check
def _unverified(token: str) -> dict:
    """The claims of a token that failed verification, for the booleans of its row only."""
    try:
        part = token.split(".")[1]
        got = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    except (IndexError, ValueError, binascii.Error, UnicodeDecodeError):
        return {}
    return got if isinstance(got, dict) else {}                # a payload that is not an object: no claims


def _refuse(headers, path: str, reason: str) -> JSONResponse:
    auth = headers.get("authorization") or ""
    claims_ = _unverified(auth[7:].strip()) if auth.lower().startswith("bearer ") else {}
    aud, email = str(claims_.get("aud") or ""), str(claims_.get("email") or "").lower()
    log.warning(json.dumps({"event": "gchat_verify_failed", "path": path, "reason": reason,
                            "aud_is_self_url": bool(SELF_URL) and aud == SELF_URL,
                            "aud_has_trailing_slash": aud.endswith("/"),
                            "email_is_gchat_caller": bool(GCHAT_CALLER) and email == GCHAT_CALLER,
                            "email_is_chat_system": email == CHAT_SYSTEM,
                            "iss_is_google": claims_.get("iss") in GOOGLE_ISSUERS}))
    return JSONResponse({"detail": "this endpoint answers Google Chat and its own push only"}, status_code=401)


def expected_caller(path: str) -> str | None:
    """Who may call `path`: Chat's add-on agent on /, the push account on /work. Never the bridge's own account."""
    if path == "/":
        bad = (not GCHAT_CALLER or GCHAT_CALLER.endswith(f"@{PROJECT}.iam.gserviceaccount.com".lower())
               and GCHAT_CALLER.split("@")[0] in (PUSH_ACCOUNT, BRIDGE_ACCOUNT))
        return None if bad else GCHAT_CALLER
    return f"{PUSH_ACCOUNT}@{PROJECT}.iam.gserviceaccount.com".lower() if PROJECT else None


def verify(headers, path: str) -> JSONResponse | None:
    """None when the request carries a Google ID token for SELF_URL from the one caller `path` admits; else the 401."""
    want = expected_caller(path)
    if not want:
        return _refuse(headers, path, "not_configured")
    try:
        email = iap.bearer_email(headers, SELF_URL)
    except iap.IapError:
        return _refuse(headers, path, "invalid_token" if (headers.get("authorization") or "") else "no_token")
    if email != want:
        return _refuse(headers, path, "wrong_caller")
    return None


# ---------------------------------------------------------------- rows
_PROBED: set = set()
_PROBE_LOCK = threading.Lock()


def probe(what: str, **fields) -> None:
    """One gchat_probe row per kind per instance: booleans and enums only."""
    with _PROBE_LOCK:
        if what in _PROBED:
            return
        _PROBED.add(what)
    log.info(json.dumps({"event": "gchat_probe", "what": what, **fields}))


def row(kind: str, outcome: str, t0: float, *, tenant: str | None = None, user: str | None = None,
        cls: str | None = None, queued: bool = False, no_case: bool = False, unsent: bool = False) -> None:
    """One gchat row. user is written only when the class is known and not sensitive (cls, or no_case: the Desk's
    reply says the turn is no case), or when unsent: the Desk never had the turn's words. Otherwise it is null."""
    sensitive = cls in desk_rules.SENSITIVE
    named = not sensitive and (cls is not None or no_case or unsent)
    log.info(json.dumps({"event": "gchat", "kind": kind, "outcome": outcome, "tenant": tenant,
                         "user": user if named else None, "class": "sensitive" if sensitive else cls,
                         "queued": queued, "latency_ms": int((time.monotonic() - t0) * 1000)}))


def case_type(out: dict) -> str | None:
    """The type of the case a POST /v1/desk reply offered or drafted, or None."""
    for d in (out.get("case_offer"), out.get("case")):
        if isinstance(d, dict) and isinstance(d.get("case_type"), str):
            return d["case_type"]
    return None


def say(ev: dict, message: dict) -> JSONResponse:
    return JSONResponse(replies.wrap(message, ev.get("shape")))


def quiet() -> JSONResponse:
    return JSONResponse({})


# ---------------------------------------------------------------- the rate, per sender, per instance
_RATE: dict = {}
_RATE_LOCK = threading.Lock()


def within_rate(email: str) -> bool:
    now = time.monotonic()
    with _RATE_LOCK:
        recent = [t for t in _RATE.get(email, ()) if now - t < 60.0]
        ok = len(recent) < RATE_PER_MIN
        if ok:
            recent.append(now)
        _RATE[email] = recent
        return ok


# ---------------------------------------------------------------- POST /
def person(ev: dict) -> str | None:
    """The sender's email when the sender is a person whose email the event carried, in a shape the Desk accepts as
    one person's address (events.is_person): any other is "could not read your account", with no Desk call."""
    email = ev.get("sender_email")
    return email if ev.get("sender_type") == events.HUMAN and email and events.is_person(email) else None


def gate_reply(ev: dict, cls: str, text: str, t0: float) -> JSONResponse:
    """A gate hit: answered now, every time, and never claimed or queued."""
    email, fixed = person(ev), desk_law.template(cls)
    if not ev["dm"] or not email or not ev["space_name"]:
        row("message", "gate_fixed", t0, user=email, cls=cls)
        return say(ev, cards.fixed_card(fixed, SELF_URL, None, None, None if ev["dm"] else replies.DM_ONLY))
    sid = events.session_id(ev["space_name"], events.today_ist())
    if len(text) > events.QUESTION_MAX:
        row("message", "gate_fixed", t0, user=email, cls=cls)
        return say(ev, cards.fixed_card(fixed, SELF_URL, sid, cls))
    try:
        out = desk("POST", "/v1/desk", email, {"question": text, "session_id": sid}, timeout=GATE_BUDGET_S)
    except DeskError as e:
        denial = replies.for_denial(e.detail) if e.status == 403 else None
        # a 403 is refused before the Desk decides anything; any other failure may have been classified and logged
        row("message", "gate_fixed", t0, user=email if e.status == 403 else None,
            cls=cls if e.status == 403 or cls not in desk_rules.SENSITIVE else None)
        if denial:
            return say(ev, cards.fixed_card(fixed, SELF_URL, None, None, denial))
        return say(ev, cards.fixed_card(fixed, SELF_URL, sid, cls))
    # The Desk's verdict, not this image's: the two may gate by different rules (mk/agents.mk), and the row names
    # the person exactly when the Desk's own row for the turn does
    routed_case = out.get("route") == "case"
    seen = case_type(out) if routed_case else None if cls in desk_rules.SENSITIVE else cls
    row("message", "gate", t0, tenant=out.get("tenant"), user=email, cls=seen, no_case=not routed_case)
    return say(ev, cards.render(out, SELF_URL, sid))


def check(email: str) -> tuple[str | None, str | None]:
    """(the tenant, or None when the Desk did not answer in time; a reply for a refusal, or None)."""
    try:
        got = desk("GET", "/v1/desk/check", email, timeout=CHECK_BUDGET_S)
    except DeskError as e:
        if e.status == 403:
            return None, replies.for_denial(e.detail) or replies.REFUSED + (e.detail or "this is not allowed")
        if e.status in SEEN_DENIALS:
            return None, replies.UNREACHABLE
        return None, None                       # no answer in time: the question goes on, the worker shows a refusal
    return got.get("tenant"), None


def queue_turn(ev: dict, kind: str, key: str, email: str, sid: str, t0: float, *, question: str | None = None,
               chip: str | None = None) -> JSONResponse:
    """Steps 7 to 9 for a question or a chip: the rate, the check, then the queue (or, sync-only, the Desk now)."""
    if not within_rate(email):
        claims.drop(key)
        row(kind, "rate_limited", t0, user=email, unsent=True)
        return say(ev, replies.text(replies.RATE_LIMITED))
    tenant, refusal = check(email) if GCHAT_ASYNC else (None, None)     # sync-only: the Desk call refuses alike
    if refusal:
        claims.drop(key)
        row(kind, "refused", t0, tenant=tenant, user=email, unsent=True)     # the check carries no text
        return say(ev, replies.text(refusal))
    turn = {"session_id": sid, **({"question": question} if question is not None else {"chip": chip})}
    if not GCHAT_ASYNC:
        try:
            out = desk("POST", "/v1/desk", email, turn, timeout=SYNC_ONLY_BUDGET_S)
        except DeskError as e:
            claims.drop(key)
            row(kind, "unreachable" if e.status not in SEEN_DENIALS else "refused", t0, tenant=tenant, user=email)
            return say(ev, replies.text(_refusal_text(e)))
        claims.answered(key)
        row(kind, "answered", t0, tenant=out.get("tenant"), user=email, cls=case_type(out),
            no_case=out.get("route") != "case")
        return say(ev, cards.render(out, SELF_URL, sid))
    payload = {"key": key, "kind": kind, "email": email, "space": ev["space_name"], "thread": ev["thread_name"], **turn}
    claims.queued(key)                  # before the publish, so it never overwrites the worker's lease
    try:
        post.publish(PROJECT, payload)
    except post.PostError:
        claims.drop(key)
        row(kind, "unreachable", t0, tenant=tenant, user=email)     # a publish that timed out may still be answered
        return say(ev, replies.text(replies.UNREACHABLE))
    row(kind, "queued", t0, tenant=tenant, user=email, queued=True)
    return say(ev, replies.text(replies.ACK))


def on_message(ev: dict, t0: float) -> JSONResponse:
    for text in ev["texts"]:                                    # 3. the gate, before every other check
        cls = desk_rules.gate(text)
        if cls:
            return gate_reply(ev, cls, text, t0)
    email = person(ev)                                          # 4. the sender
    if not email:
        log.info(json.dumps({"event": "gchat_no_email", "sender_is_human": ev.get("sender_type") == events.HUMAN,
                             "has_sender_email": bool(ev.get("sender_email")),
                             "email_is_person": bool(ev.get("sender_email")) and events.is_person(ev["sender_email"]),
                             "has_user_id_token": bool(ev.get("has_user_id_token"))}))
        row("message", "no_account", t0)
        return say(ev, replies.text(replies.NO_ACCOUNT))
    if not ev["dm"] or not ev["space_name"]:                    # 5. direct messages, typed text, the cap
        row("message", "not_direct", t0, user=email, unsent=True)
        return say(ev, replies.text(replies.DM_ONLY))
    text = (ev["text"] or "").strip()
    if ev["has_attachment"] or not text:
        row("message", "not_typed", t0, user=email, unsent=True)
        return say(ev, replies.text(replies.TYPED_ONLY))
    if len(text) > events.QUESTION_MAX:
        row("message", "too_long", t0, user=email, unsent=True)
        return say(ev, replies.text(replies.TOO_LONG))
    key = events.event_key(ev["message_name"])                   # 6. the claim
    if not claims.take(key, "message"):
        row("message", "duplicate", t0, user=email)
        return say(ev, replies.text(replies.ACK if GCHAT_ASYNC else replies.TAKEN))
    masked, _ = desk_rules.mask(text)                           # 9. never the person's numbers in the queue
    sid = events.session_id(ev["space_name"], events.today_ist())
    return queue_turn(ev, "message", key, email, sid, t0, question=masked)


def _refusal_text(e: DeskError) -> str:
    if e.status == 403 and replies.for_denial(e.detail):
        return replies.for_denial(e.detail)
    if e.status in SEEN_DENIALS and e.detail:
        return replies.REFUSED + e.detail
    return replies.UNREACHABLE


def _press_case(ev: dict, email: str, act: str, params: dict, sid: str) -> tuple[dict, str, str | None, str | None]:
    """Confirm, Cancel, a confidential record and "Show my options", answered now: (message, outcome, class, tenant).
    Raises DeskError."""
    name = ev["message_name"]
    if act in ("confirm", "cancel"):
        case_id = params.get("case") or ""
        if not CASE_ID.match(case_id):
            return replies.text(replies.STALE), "stale", None, None
        if act == "cancel":
            got = desk("POST", f"/v1/cases/{case_id}/cancel", email, timeout=PRESS_BUDGET_S)
            return replies.text(replies.CANCELLED), "cancelled", got.get("case_type"), got.get("tenant")
        got = desk("POST", f"/v1/cases/{case_id}/confirm", email, {"token": events.token(name, act, params)},
                   timeout=PRESS_BUDGET_S)
        owner = got.get("owner") if isinstance(got.get("owner"), dict) else {}
        lines = [f"Your case is open. Its reference is {got.get('case_id')}.",
                 f"{owner['queue_name']} has it." if owner.get("queue_name") else None, *(got.get("clock") or [])]
        return cards.result_card("Handed to a person", lines), "confirmed", got.get("case_type"), got.get("tenant")
    if act == "posh":
        unit = params.get("unit") or ""
        offer = desk("GET", "/v1/cases/offer", email, timeout=PRESS_BUDGET_S)
        spec = ((offer.get("posh") or {}).get(unit) or {}) if UNIT.match(unit) else {}
        contacts = [m.get("email") for m in spec.get("members") or () if isinstance(m, dict) and m.get("email")]
        if not contacts:
            return replies.text(replies.STALE), "stale", "posh", offer.get("tenant")
        if params.get("m") != cards.members_digest(contacts):     # not the members the card listed
            return replies.text(cards.POSH_CHANGED), "stale", "posh", offer.get("tenant")
        got = desk("POST", "/v1/cases", email, {"case_type": "posh", "unit": unit, "contacts": contacts,
                                                "token": events.token(name, act, params)}, timeout=PRESS_BUDGET_S)
        says = [b.get("says") for b in desk_law.basis_for("posh") if isinstance(b, dict) and b.get("says")]
        lines = [f"Recorded. Your case reference is {got.get('case_id')}.",
                 f"The {spec.get('name') or unit} Internal Committee has it.", *says, cards.POSH_PRIVACY]
        return cards.result_card("HR Desk", lines), "recorded", "posh", offer.get("tenant")
    cls = params.get("cls") or ""                                     # options
    if cls not in desk_rules.CLASSES:
        return replies.text(replies.STALE), "stale", None, None
    if cls == "posh":
        offer = desk("GET", "/v1/cases/offer", email, timeout=PRESS_BUDGET_S)
        card = {"case_type": "posh", "configured": bool(offer.get("posh")), "posh": offer.get("posh")}
        return cards.posh_card(desk_law.template("posh"), card, SELF_URL, sid), "options", cls, offer.get("tenant")
    got = desk("POST", "/v1/cases", email, {"case_type": cls}, timeout=PRESS_BUDGET_S)
    return cards.draft_card(desk_law.template(cls), got, SELF_URL, sid), "options", cls, got.get("tenant")


def on_press(ev: dict, t0: float) -> JSONResponse:
    probe("press", params_from=ev.get("params_from"), form_from=ev.get("form_from"),
          has_parameters=bool(ev.get("parameters")), has_message_name=bool(ev.get("message_name")),
          has_sender_email=bool(ev.get("sender_email")), sender_is_human=ev.get("sender_type") == events.HUMAN)
    email = person(ev)
    if not email:
        row("press", "no_account", t0)
        return say(ev, replies.text(replies.NO_ACCOUNT))
    if not ev["dm"] or not ev["space_name"]:
        row("press", "not_direct", t0, user=email, unsent=True)
        return say(ev, replies.text(replies.DM_ONLY))
    params, act = ev["parameters"], ev["action"]
    if act not in ACTS:
        row("press", "ignored", t0, user=email, unsent=True)
        return quiet()
    sid = params.get("sid") or ""
    if not events.session_of_space(sid, ev["space_name"]):     # a press from another conversation
        row("press", "stale", t0, user=email, unsent=True)
        return say(ev, replies.text(replies.STALE))
    key = events.press_key(ev["message_name"], act, params)
    if not claims.take(key, "press"):
        row("press", "duplicate", t0, user=email)
        queued = act == "chip" and GCHAT_ASYNC                 # only a queued chip has an answer still to come
        return say(ev, replies.text(replies.ALREADY if queued else replies.TAKEN))
    if act == "chip":
        chip = params.get("chip")
        if chip not in cards.CHIP_IDS:
            claims.drop(key)
            row("press", "stale", t0, user=email, unsent=True)
            return say(ev, replies.text(replies.STALE))
        return queue_turn(ev, "press", key, email, sid, t0, chip=chip)
    try:
        message, outcome, cls, tenant = _press_case(ev, email, act, params, sid)
    except DeskError as e:
        if e.status in SEEN_DENIALS:
            claims.answered(key)
        else:
            claims.drop(key)                     # no answer: the next press may try again
        row("press", "refused" if e.status in SEEN_DENIALS else "unreachable", t0, user=email,
            cls="posh" if act == "posh" else (params.get("cls") if act == "options" else None))
        return say(ev, replies.text(_refusal_text(e)))
    claims.answered(key)
    row("press", outcome, t0, tenant=tenant, user=email, cls=cls)
    return say(ev, message)


def handle_event(headers, raw: bytes, verified: bool = False) -> Response:
    """verified: the route checked the token before it read the body."""
    t0 = time.monotonic()
    refused = None if verified else verify(headers, "/")       # 1. before anything else
    if refused:
        return refused
    if len(raw) > BODY_MAX:
        return JSONResponse({"detail": "event too large"}, status_code=413)
    try:
        body = json.loads(raw or b"{}")
    except (ValueError, UnicodeDecodeError):
        body = {}
    try:
        ev = events.normalise(body)                             # 2.
    except Exception as e:  # noqa: BLE001 - an event it cannot read gets no reply, and no trace of its words
        log.warning(json.dumps({"event": "gchat_error", "where": "normalise", "error": type(e).__name__}))
        return quiet()
    probe("event", shape=ev["shape"], kind=ev["kind"], caller_matched=True,
          has_sender_email=bool(ev["sender_email"]), sender_is_human=ev["sender_type"] == events.HUMAN,
          has_user_id_token=bool(ev["has_user_id_token"]), space_field=ev["space_field"], is_dm=bool(ev["dm"]),
          has_space_name=bool(ev["space_name"]), has_thread_name=bool(ev["thread_name"]),
          has_message_name=bool(ev["message_name"]), text_fields=len(ev["texts"]))
    try:
        if ev["kind"] == "added":
            row("added", "welcome", t0, user=person(ev), unsent=True)
            return say(ev, replies.welcome())
        if ev["kind"] == "message":
            return on_message(ev, t0)
        if ev["kind"] == "press":
            return on_press(ev, t0)
    except Exception as e:  # noqa: BLE001 - a reply, never a trace with the person's words in it
        log.warning(json.dumps({"event": "gchat_error", "where": ev["kind"], "error": type(e).__name__}))
        row(ev["kind"], "error", t0)
        return say(ev, replies.text(replies.UNREACHABLE))
    row(ev["kind"], "ignored", t0)
    return quiet()


@app.post("/")
async def chat_event(request: Request) -> Response:
    refused = await run_in_threadpool(verify, request.headers, "/")     # the token, before the body is read
    if refused:
        return refused
    raw = await request.body()
    return await run_in_threadpool(handle_event, request.headers, raw, True)


# ---------------------------------------------------------------- POST /work
def work_payload(envelope) -> dict | None:
    """The queued turn in a push envelope, checked field by field; None when it is not one this bridge published."""
    data = ((envelope or {}).get("message") or {}).get("data") if isinstance(envelope, dict) else None
    try:
        p = json.loads(base64.b64decode(data or "", validate=True))
    except (ValueError, binascii.Error, UnicodeDecodeError, TypeError):
        return None
    if not isinstance(p, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(p.get("key"))):
        return None
    ok = (p.get("kind") in ("message", "press") and isinstance(p.get("email"), str) and "@" in p["email"]
          and events.SESSION.match(str(p.get("session_id"))) and post.SPACE.match(str(p.get("space")))
          and (p.get("thread") is None or isinstance(p.get("thread"), str))
          and ((isinstance(p.get("question"), str) and 0 < len(p["question"]) <= events.QUESTION_MAX
                and p.get("chip") is None)
               or (p.get("question") is None and p.get("chip") in cards.CHIP_IDS)))
    return p if ok else None


def _post(p: dict, message: dict) -> str:
    status = "failed"
    try:
        status = post.create(p["space"], p.get("thread"), events.client_id(p["key"]), message)
        return status
    finally:
        probe("post", auth=post.AUTH_USED["how"], outcome=status)


def handle_work(headers, raw: bytes, verified: bool = False) -> Response:
    """verified: the route checked the token before it read the body."""
    refused = None if verified else verify(headers, "/work")
    if refused:
        return refused
    try:
        envelope = json.loads(raw or b"{}")
    except (ValueError, UnicodeDecodeError):
        envelope = None
    if not isinstance(envelope, dict) or envelope.get("subscription") != f"projects/{PROJECT}/subscriptions/{SUBSCRIPTION}":
        return _refuse(headers, "/work", "wrong_subscription")
    p = work_payload(envelope)
    if p is None:
        log.warning(json.dumps({"event": "gchat_answer", "attempts": 0, "outcome": "bad_message", "desk_ms": 0,
                                "post_ms": 0}))
        return Response(status_code=204)                       # never retried: it is not ours to answer
    state, attempts = claims.lease(p["key"], p["kind"])
    if state == "answered" or attempts > MAX_ATTEMPTS:
        return Response(status_code=204)
    if state == "busy":
        return Response(status_code=503)
    try:
        return answer(p, attempts)
    except Exception as e:  # noqa: BLE001 - an error of the bridge's own: retried, and on the last attempt said so
        log.warning(json.dumps({"event": "gchat_error", "where": "work", "error": type(e).__name__}))
        if attempts < MAX_ATTEMPTS:
            claims.release(p["key"])
            return Response(status_code=503)
        try:
            _post(p, replies.text(replies.UNREACHABLE))
        except post.PostError:
            pass
        claims.answered(p["key"])
        return Response(status_code=204)


def answer(p: dict, attempts: int) -> Response:
    """One leased turn: the Desk, the card, the post, the claim answered."""
    t0 = time.monotonic()
    turn = {"session_id": p["session_id"], **({"question": p["question"]} if p.get("question") else {"chip": p["chip"]})}
    try:
        out = desk("POST", "/v1/desk", p["email"], turn, timeout=WORK_TIMEOUT_S)
        message, outcome = cards.render(out, SELF_URL, p["session_id"]), str(out.get("outcome") or "answered")
    except DeskError as e:
        if e.status not in SEEN_DENIALS and attempts < MAX_ATTEMPTS:
            claims.release(p["key"])
            return Response(status_code=503)
        message = replies.text(_refusal_text(e))
        outcome = "refused" if e.status in SEEN_DENIALS else "unreachable"
    desk_ms = int((time.monotonic() - t0) * 1000)
    t1 = time.monotonic()
    try:
        _post(p, message)
    except post.PostError as e:
        if attempts < MAX_ATTEMPTS and e.retry:
            claims.release(p["key"])
            return Response(status_code=503)
        if not e.auth:                                          # the card itself was refused, or the last attempt
            try:
                _post(p, replies.text(replies.UNREACHABLE))
            except post.PostError:
                pass
        outcome = "post_refused" if e.auth else "post_failed"   # acknowledged: a redelivery reruns no Desk turn
    claims.answered(p["key"])
    log.info(json.dumps({"event": "gchat_answer", "attempts": attempts, "outcome": outcome, "desk_ms": desk_ms,
                         "post_ms": int((time.monotonic() - t1) * 1000)}))
    return Response(status_code=204)


@app.post("/work")
async def work(request: Request) -> Response:
    try:
        refused = await run_in_threadpool(verify, request.headers, "/work")    # the token, before the body is read
        if refused:
            return refused
        raw = await request.body()
        return await run_in_threadpool(handle_work, request.headers, raw, True)
    except Exception as e:  # noqa: BLE001 - Pub/Sub retries a 5xx; the trace would carry nothing useful
        log.warning(json.dumps({"event": "gchat_error", "where": "work", "error": type(e).__name__}))
        return Response(status_code=503)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "async": GCHAT_ASYNC}
