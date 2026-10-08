"""A Google Chat event as one record, from either of the two shapes Chat may send (the Google Chat door, workshop lesson
10.4). Standard library only.

    add-on shape    the Workspace add-on model, the one the "HR Desk" app is configured with: the body carries a "chat"
                    key, and a person's message is chat.messagePayload.message with its sender
    classic shape   the interaction-event model: the body carries "type", "message", "user", "space" and "common"

normalise(body) returns one record of plain values; nothing in it is the event's text except "text" and "texts", which
only the gate and the masking read. A field path the read pages did not state is UNCONFIRMED: it sits in one function
below, named so, and the lane probe (the gchat_probe row, main.py) records which path held on a real event. Until the
probe has run, an event the record cannot place is "other", and the bridge answers it with nothing.

The ids the bridge derives, all pure:

    session_id(space, day)  "gc-" + sha256(space name)[:24] + "-" + YYYYMMDD in India: 36 characters, inside the Desk's
                            session pattern ([A-Za-z0-9_-]{1,64}), with no ":" (thread_config refuses it) and no "/"
                            (a space name has one). One Desk thread a day per direct message: tenant:email:desk~gc-...
    event_key(message)      sha256(message name): the duplicate claim's document id and the posted answer's id
    press_key(...)          sha256 of the pressed card's message name, the action and its parameters: a doubled press
                            is one claim
    client_id(key)          "client-" + 56 lower-case hex digits, 63 characters: spaces.messages.create's messageId,
                            so a second post of one answer is refused by Chat itself
    token(...)              the client idempotency token a case create or confirm carries, built like press_key, so a
                            retried press opens or confirms one case
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))     # India has no daylight saving: a fixed offset
SESSION = re.compile(r"^gc-[0-9a-f]{24}-\d{8}$")
QUESTION_MAX = 4000                                # the Desk's ChatRequest and DeskRequest cap
HUMAN = "HUMAN"                                    # the User resource's type for a person
# services/chat/delegation.py's PERSON, word for word (commands/tests/test_gchat.py holds the two equal): an address
# the Desk would refuse to be named for is "could not read your account" here, and never reaches the Desk, whose
# refusal would count as a refused delegation.
PERSON = re.compile(r"^[a-z0-9][a-z0-9._%+'-]{0,63}@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")


def _d(obj, *path):
    """obj[path[0]][path[1]]..., or None at the first missing step or non-dict."""
    for key in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- the paths, each one place
def addon_parts(body: dict) -> tuple[str, dict | None, dict | None]:
    """(kind, message, payload) of an add-on event. messagePayload is from the quickstart page; addedToSpacePayload
    and buttonClickedPayload are UNCONFIRMED (from memory), and so is chat.user as a press's sender (normalise): the
    probe records which key a real event carried, and whether a press carried an email."""
    chat = body.get("chat") if isinstance(body.get("chat"), dict) else {}
    if isinstance(chat.get("messagePayload"), dict):
        p = chat["messagePayload"]
        return "message", p.get("message") if isinstance(p.get("message"), dict) else None, p
    if isinstance(chat.get("buttonClickedPayload"), dict):
        p = chat["buttonClickedPayload"]
        return "press", p.get("message") if isinstance(p.get("message"), dict) else None, p
    if isinstance(chat.get("addedToSpacePayload"), dict):
        return "added", None, chat["addedToSpacePayload"]
    return "other", None, None


CLASSIC_KINDS = {"MESSAGE": "message", "CARD_CLICKED": "press", "ADDED_TO_SPACE": "added"}   # UNCONFIRMED values


def press_parameters(body: dict) -> tuple[dict, str | None]:
    """A button's parameters and where they came from. UNCONFIRMED paths: the add-on model's commonEventObject
    (the event-object page names the object, not the path), and the classic common or action; the probe records which
    one held (params_from)."""
    for where, value in (("commonEventObject.parameters", _d(body, "commonEventObject", "parameters")),
                         ("common.parameters", _d(body, "common", "parameters")),
                         ("action.parameters", _d(body, "action", "parameters"))):
        if isinstance(value, dict) and value:
            return {str(k): str(v) for k, v in value.items() if isinstance(v, (str, int))}, where
        if isinstance(value, list) and value:                 # [{"key": .., "value": ..}], the shape a card sends
            out = {str(p.get("key")): str(p.get("value")) for p in value if isinstance(p, dict) and p.get("key")}
            if out:
                return out, where
    return {}, None


def form_values(body: dict) -> tuple[dict, str | None]:
    """A press's form inputs (a selection on the card): {name: [values]}. UNCONFIRMED paths, as press_parameters."""
    for where, value in (("commonEventObject.formInputs", _d(body, "commonEventObject", "formInputs")),
                         ("common.formInputs", _d(body, "common", "formInputs"))):
        if isinstance(value, dict) and value:
            out = {}
            for name, v in value.items():
                vals = _d(v, "stringInputs", "value")
                if isinstance(vals, list):
                    out[str(name)] = [str(x) for x in vals]
            if out:
                return out, where
    return {}, None


def direct_message(space: dict | None) -> tuple[bool, str | None]:
    """(is it a direct message, the field that said so). UNCONFIRMED: the space-type field's name (spaceType,
    the older type, singleUserBotDm, all from memory). Only a field that says "direct message" counts, so an event
    whose space cannot be read is treated as a named space: the bridge then asks the person to message it directly."""
    space = space if isinstance(space, dict) else {}
    if space.get("spaceType") == "DIRECT_MESSAGE":
        return True, "spaceType"
    if space.get("type") == "DM":
        return True, "type"
    if space.get("singleUserBotDm") is True:
        return True, "singleUserBotDm"
    for field in ("spaceType", "type", "singleUserBotDm"):
        if field in space:
            return False, field
    return False, None


def user_id_token_present(body: dict) -> bool:
    """Whether the event carries the person's own Google-signed ID token (the add-on runtimes page names
    authorizationEventObject.userIdToken; UNCONFIRMED for Chat). Recorded by the probe only: nothing verifies or uses it."""
    return bool(_d(body, "authorizationEventObject", "userIdToken"))


def attachment_present(message: dict | None) -> bool:
    """UNCONFIRMED field names (attachment, attachedGifs): a message carrying either is not a typed question."""
    message = message if isinstance(message, dict) else {}
    return bool(message.get("attachment") or message.get("attachedGifs"))


TEXT_FIELDS = ("text", "argumentText", "formattedText")


def is_person(email) -> bool:
    """One lower-case person's address, as the Desk's delegation rule 3 reads it: PERSON, at most 254 characters, no
    ":", and not a service account."""
    return (isinstance(email, str) and email == email.strip().lower() and len(email) <= 254
            and bool(PERSON.match(email)) and ":" not in email and not email.endswith(".gserviceaccount.com"))


# ---------------------------------------------------------------- the record
def normalise(body) -> dict:
    """One record from either shape: shape, kind (message, press, added, other), message_name, space_name, dm and
    space_field, thread_name, sender_name, sender_type, sender_email (lower case, or None), text (the message's text)
    and texts (every text field it carries, for the gate), has_attachment, action and parameters (a press), form,
    params_from, has_user_id_token."""
    body = body if isinstance(body, dict) else {}
    rec = {"shape": None, "kind": "other", "message_name": None, "space_name": None, "dm": False, "space_field": None,
           "space_keys": [], "thread_name": None, "sender_name": None, "sender_type": None, "sender_email": None,
           "text": "", "texts": [], "has_attachment": False, "action": None, "parameters": {}, "form": {},
           "params_from": None, "form_from": None, "has_user_id_token": user_id_token_present(body)}
    if isinstance(body.get("chat"), dict):
        rec["shape"] = "addon"
        kind, message, payload = addon_parts(body)
        space = _d(payload, "space") or _d(message, "space") or _d(body, "chat", "space")
        user = _d(message, "sender") if kind == "message" else _d(body, "chat", "user")
    elif isinstance(body.get("type"), str):
        rec["shape"] = "classic"
        kind = CLASSIC_KINDS.get(body["type"], "other")
        message = body.get("message") if isinstance(body.get("message"), dict) else None
        space = body.get("space") if isinstance(body.get("space"), dict) else _d(message, "space")
        user = _d(message, "sender") if kind == "message" else body.get("user")
    else:
        return rec
    rec["kind"] = kind
    space = space if isinstance(space, dict) else {}
    rec["space_name"] = space.get("name") if isinstance(space.get("name"), str) else None
    rec["dm"], rec["space_field"] = direct_message(space)
    rec["space_keys"] = sorted(str(k) for k in space)[:12]           # field names only, for the probe
    if isinstance(message, dict):
        rec["message_name"] = message.get("name") if isinstance(message.get("name"), str) else None
        rec["thread_name"] = _d(message, "thread", "name") if isinstance(_d(message, "thread", "name"), str) else None
        rec["texts"] = [message[f] for f in TEXT_FIELDS if isinstance(message.get(f), str) and message[f].strip()]
        rec["text"] = message.get("text") if isinstance(message.get("text"), str) else \
            (rec["texts"][0] if rec["texts"] else "")
        rec["has_attachment"] = attachment_present(message)
    if isinstance(user, dict):
        rec["sender_name"] = user.get("name") if isinstance(user.get("name"), str) else None
        rec["sender_type"] = user.get("type") if isinstance(user.get("type"), str) else None
        email = user.get("email")
        rec["sender_email"] = email.strip().lower() if isinstance(email, str) and email.strip() else None
    if kind == "press":
        rec["parameters"], rec["params_from"] = press_parameters(body)
        rec["form"], rec["form_from"] = form_values(body)
        rec["action"] = rec["parameters"].get("act")
    if kind in ("message", "press") and not rec["message_name"]:
        rec["kind"] = "other"                       # no name: nothing to claim and no answer id to post under
    return rec


# ---------------------------------------------------------------- the ids
def today_ist(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).astimezone(IST).strftime("%Y%m%d")


def session_id(space_name: str, day: str) -> str:
    """The Desk session for a direct message on a day (YYYYMMDD, India)."""
    if not space_name or not re.fullmatch(r"\d{8}", day or ""):
        raise ValueError("a space name and a YYYYMMDD day")
    return f"gc-{_sha(space_name)[:24]}-{day}"


def session_of_space(sid: str, space_name: str) -> bool:
    """A session id a button carries belongs to this space (its hash part), whatever its day."""
    return bool(SESSION.match(sid or "")) and bool(space_name) and sid[3:27] == _sha(space_name)[:24]


def event_key(message_name: str) -> str:
    return _sha(message_name)


def press_key(message_name: str, action: str, parameters: dict) -> str:
    params = "&".join(f"{k}={parameters[k]}" for k in sorted(parameters))
    return _sha(f"press|{message_name}|{action}|{params}")


def client_id(key: str) -> str:
    """spaces.messages.create's messageId for an answer: 63 characters, lower-case letters, digits and hyphens."""
    if not re.fullmatch(r"[0-9a-f]{64}", key or ""):
        raise ValueError("a claim key: 64 hex digits")
    return "client-" + key[:56]


def token(message_name: str, action: str, parameters: dict) -> str:
    """The client token of a case create or confirm (cases.TOKEN: 8 to 128 of [A-Za-z0-9_-])."""
    params = "&".join(f"{k}={parameters[k]}" for k in sorted(parameters))
    return "gc" + _sha(f"token|{message_name}|{action}|{params}")[:40]
