"""Who a Desk route serves when the Google Chat bridge asks on someone's behalf (the DocuMind Desk, workshop lesson 10.4).

The chat service takes identity from one place, agent.py's caller(): the person's IAP assertion, or the caller's own
Google ID token for SELF_URL (shared/iap.py). Neither can name an employee who messaged the "HR Desk" app in Google
Chat: Chat calls the bridge (services/gchat/) as Google's own agent, and no service account can mint an assertion or an
ID token in a person's name. So the Desk trusts one named delegate, the bridge's account, to name the person in the
header X-DocuMind-Principal, under rules that live here, in the Desk, and not in the bridge.

principal(request, caller, tenant_for, settings) is services/chat/desk.py's _principal() for every Desk and case route:

    no header     caller(request), unchanged, with via "direct": the Desk page, the eval accounts, make smoke-desk and
                  every other caller are served exactly as before. The bridge's own account is on no roster, so a
                  bridge call without the header is refused by the roster, as the outsider is.
    the header    caller(request) first, so an unverified request is still a 401. Then a 403 with a fixed reason
                  unless every rule holds, checked in this order:
                    1. the verified caller is a delegate: DELEGATES, documind-gchat-sa in this service's own project
                       (GOOGLE_CLOUD_PROJECT). A person's IAP assertion names the person, so no person passes, whichever
                       leg caller() used;
                    2. the route is delegable (DELEGABLE): POST /v1/desk, GET /v1/desk/check, POST /v1/cases, a case's
                       confirm and cancel, GET /v1/cases/offer. Never /v1/route, the inbox, one case's read or a
                       status change; /v1/chat never reads the header, because its door and handler call caller();
                    3. the named principal is one lower-case address of a person: the PERSON pattern, no ":" (which
                       thread_config refuses), never a *.gserviceaccount.com account (chat-sa sits on every golden
                       roster, and the eval accounts hold desk_eval), and the header sent once;
                    4. the body carries no arm and no prev_* field, whatever the person's roles;
                    5. the profile is not local: there is no bridge on a laptop;
                    6. tenant_for(principal) finds a tenant;
                    7. that tenant's desk_gchat is on, read through settings() (the Desk's 60-second cache); a failed
                       read is off.
                  Rules 1 to 5 refuse the caller: a desk_delegation_refused row {caller, reason, path}, with no
                  principal, which an alert counts. They are checked before 6 and 7, so a request they refuse reads no
                  roster and no setting, and a caller that is not the delegate learns nothing about either. Rules 6
                  and 7 are an ordinary answer about a person (not on a roster, or the door is off for the company): a
                  desk_delegation_denied row {reason, path}, with no principal and no alert.
                  Passed: {"email": principal, "assertion": None, "via": "gchat", "delegate": "gchat"}. From there
                  roles, coverage and the gate treat the person like anyone else; a leaver is still denied the answer
                  desks.

rag-api never sees the header. retrieve() sends the chat service's own ID token and the person's assertion only when
there is one, and a delegated principal carries none, so a delegated turn reaches rag-api as documind-chat-sa, as make
smoke-chat does: chat-sa must be on the tenant's roster (make roster puts it on the golden three).

Whoever can mint a token as documind-gchat-sa, act as it, or publish to its work topic can speak for every rostered
person of every tenant with desk_gchat on. tools/check_authz.py holds the kit to: nobody mints as it, nobody but the
bridge publishes to the topic, and Pub/Sub's push identity is a separate account that is not a delegate.

This module imports nothing from desk.py or agent.py: desk.py passes in caller, the tenant_for install() received and
its own settings reader.
"""
from __future__ import annotations

import json
import logging
import os
import re

from fastapi import HTTPException

from shared.profile import PROFILE

log = logging.getLogger("documind.chat.delegation")

HEADER = "x-documind-principal"
DELEGATES = {"documind-gchat-sa": "gchat"}      # account id -> delegate name; the address is in this project only
CASE = "[0-9a-f]{32}"                           # services/chat/desk.py CaseId
DELEGABLE = (("POST", "/v1/desk"), ("GET", "/v1/desk/check"), ("POST", "/v1/cases"),
             ("POST", "/v1/cases/{id}/confirm"), ("POST", "/v1/cases/{id}/cancel"), ("GET", "/v1/cases/offer"))
_DELEGABLE = tuple((m, re.compile("^" + re.escape(p).replace(re.escape("{id}"), CASE) + "$")) for m, p in DELEGABLE)
PERSON = re.compile(r"^[a-z0-9][a-z0-9._%+'-]{0,63}@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")
SERVICE_ACCOUNTS = ".gserviceaccount.com"
SWITCH = "desk_gchat"

# The 403 details. The bridge turns the two denials into its own fixed replies (services/gchat/replies.py holds the
# same words, and commands/tests/test_gchat.py holds the two equal).
NOT_A_DELEGATE = "not an allowed delegate"
NOT_DELEGABLE = "this route cannot be called on someone's behalf"
NOT_A_PERSON = "the named principal is not one person's address"
NOT_IN_BODY = "a delegated request carries no arm and no prev_* field"
NOT_LOCAL = "there is no delegation on the local profile"
NOT_A_MEMBER = "not a member of any tenant"                     # chat()'s own 403, word for word
DOOR_OFF = "the Google Chat door is not switched on for your company"


def delegate_of(email: str) -> str | None:
    """The delegate an account is, or None: one of DELEGATES, at this service's own project."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip().lower()
    if not project:
        return None
    local, _, domain = (email or "").lower().partition("@")
    return DELEGATES.get(local) if domain == f"{project}.iam.gserviceaccount.com" else None


def _route(request) -> tuple[str | None, str]:
    """(the DELEGABLE path the request matches, or None; the path as logged, with a case id as {id})."""
    path, method = request.scope.get("path") or "", request.scope.get("method") or ""
    shown = re.sub(r"/" + CASE + r"(?=/|$)", "/{id}", path)
    for (m, rx), (_, name) in zip(_DELEGABLE, DELEGABLE):
        if m == method and rx.match(path):
            return name, shown
    return None, shown


def _body_fields(request) -> set[str] | None:
    """The top-level fields of the JSON body FastAPI read for the handler (Starlette keeps it on the request as
    _body), or None when no body was read; set() for a body that is not a JSON object (the handler's 422 answers it)."""
    raw = getattr(request, "_body", None)
    if raw is None:
        return None
    try:
        obj = json.loads(raw or b"null")
    except (ValueError, UnicodeDecodeError):
        return set()
    return set(obj) if isinstance(obj, dict) else set()


def _refuse(caller_email: str, reason: str, path: str):
    log.warning(json.dumps({"event": "desk_delegation_refused", "caller": caller_email, "reason": reason,
                            "path": path}))
    raise HTTPException(403, reason)


def _deny(reason: str, path: str):
    log.info(json.dumps({"event": "desk_delegation_denied", "reason": reason, "path": path}))
    raise HTTPException(403, reason)


def principal(request, caller, tenant_for, settings) -> dict:
    """The person a Desk or case route serves: caller(request) without the header; with it, the named person under
    the rules above, or a 403. caller(request) raises its own 401 first in both cases."""
    named = request.headers.getlist(HEADER)
    who = caller(request)
    if not named:
        return {**who, "via": "direct"}
    email = str(who.get("email") or "").lower()
    route, path = _route(request)
    name = delegate_of(email)
    if name is None:                                                    # 1
        _refuse(email, NOT_A_DELEGATE, path)
    if route is None:                                                   # 2
        _refuse(email, NOT_DELEGABLE, path)
    person = named[0]
    if len(named) != 1 or person != person.strip().lower() or len(person) > 254 or not PERSON.match(person) \
            or ":" in person or person.endswith(SERVICE_ACCOUNTS):      # 3
        _refuse(email, NOT_A_PERSON, path)
    fields = _body_fields(request)
    if (fields is None and request.scope.get("method") == "POST" and route != "/v1/cases/{id}/cancel") or \
            any(f == "arm" or str(f).startswith("prev_") for f in fields or ()):   # 4: a POST body unread is no proof
        _refuse(email, NOT_IN_BODY, path)
    if PROFILE == "local":                                              # 5
        _refuse(email, NOT_LOCAL, path)
    tenant = tenant_for(person)
    if tenant is None:                                                  # 6
        _deny(NOT_A_MEMBER, path)
    try:
        on = _switch_on((settings(tenant) or {}).get(SWITCH))
    except Exception:  # noqa: BLE001 - a failed read is off: the door stays shut (desk_gate alone falls back to rules)
        on = False
    if not on:                                                          # 7
        _deny(DOOR_OFF, path)
    return {"email": person, "assertion": None, "via": name, "delegate": name}


def _switch_on(v) -> bool:
    """desk_gchat's rule: on only when the setting is True or says on (any case); anything else is off."""
    return v is True or (isinstance(v, str) and v.strip().lower() == "on")
