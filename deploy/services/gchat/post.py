"""The Google Chat bridge's two writes (the Google Chat door, workshop lesson 10.4): an answer posted into the
person's direct message as the app, and a question published to the work topic. No key file: the service's own
credentials, through google-auth, imported inside the functions that use them (as shared/iap.py imports it), so the
module imports without a cloud SDK.

create(space, thread, message_id, message) is spaces.messages.create, called over REST:

    POST https://chat.googleapis.com/v1/{space}/messages?messageId=client-...&messageReplyOption=...

with the body the message itself and thread.name set to the event's thread, and the option
REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD, as the Chat API's page on creating messages names them. The messageId
("client-" and 56 hex digits, events.client_id) is unique within the space, so a second create of one answer is
refused by Chat; that the refusal is a 409 is UNCONFIRMED (DUPLICATE_STATUS), and the worker treats it as posted.
A 429 (1 write a second per space, 3,000 a minute per project) and a 5xx are retried by Pub/Sub. When every way of
posting is refused (401 or 403) or has no token, the error is not retried: the worker acknowledges the message
rather than ask the Desk the same question again on every redelivery.

App authentication is the chat.bot scope. That the service's own credentials can take it is UNCONFIRMED, and so is
whether an add-on-model app posts through this API at all: auth_order() is the one place. Application Default
Credentials first; then the account impersonating itself, which works only with the self-grant terraform/gchat.tf
does not make until the lane probe asks for it. Whichever answered first is kept, and the probe row records it
(AUTH_USED: adc, self_impersonation or failed). If neither works, main.py's GCHAT_ASYNC = False answers every
question in the HTTP response instead, with no Chat API write.

publish(project, payload) is Pub/Sub's topics.publish over REST: the payload as one message's base64 data. Only this
account may publish to the topic (terraform/gchat.tf, tools/check_authz.py).

These requests go through requests and google-auth, both pinned by the chat service already; the Pub/Sub and Chat
client libraries are not used, so the bridge adds no pin of its own.
"""
from __future__ import annotations

import base64
import json
import os
import re

CHAT_API = "https://chat.googleapis.com/v1"
PUBSUB_API = "https://pubsub.googleapis.com/v1"
CHAT_SCOPE = "https://www.googleapis.com/auth/chat.bot"
PUBSUB_SCOPE = "https://www.googleapis.com/auth/pubsub"
TOPIC = "documind-gchat-work"
REPLY_OPTION = "REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
DUPLICATE_STATUS = 409          # UNCONFIRMED: what Chat returns for a messageId the space already holds
POST_TIMEOUT_S = 20
PUBLISH_TIMEOUT_S = 5
SPACE = re.compile(r"^spaces/[A-Za-z0-9_-]{1,128}$")
THREAD = re.compile(r"^spaces/[A-Za-z0-9_-]{1,128}/threads/[A-Za-z0-9_.-]{1,128}$")
MESSAGE_ID = re.compile(r"^client-[0-9a-f]{56}$")

AUTH_USED: dict = {"how": None}         # adc | self_impersonation | failed, for the probe row


class PostError(Exception):
    """A write that failed. retry: Pub/Sub should try the message again; status: the HTTP status, or 0. auth: no way
    of posting as the app was allowed (every one answered 401 or 403, or could not get a token), so no retry and no
    second post can do better."""

    def __init__(self, status: int, retry: bool, auth: bool = False):
        super().__init__(f"status {status}")
        self.status, self.retry, self.auth = status, retry, auth


NO_TOKEN = ("RefreshError", "DefaultCredentialsError")     # google.auth.exceptions: no credential could be had


def _no_token(e: Exception) -> bool:
    """A credential that could not be had, as opposed to a request that got no answer (which a retry may fix)."""
    return isinstance(e, PostError) or any(c.__name__ in NO_TOKEN for c in type(e).__mro__)


def _adc(scopes: list):
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    creds, _ = google.auth.default(scopes=scopes)
    return AuthorizedSession(creds)


def _self(scopes: list):
    """The service's account impersonating itself for `scopes`: needs roles/iam.serviceAccountTokenCreator on itself."""
    import google.auth
    from google.auth import impersonated_credentials
    from google.auth.transport.requests import AuthorizedSession, Request
    source, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    source.refresh(Request())
    me = getattr(source, "service_account_email", "") or ""
    if "@" not in me:
        raise PostError(0, False)
    target = impersonated_credentials.Credentials(source_credentials=source, target_principal=me,
                                                  target_scopes=scopes)
    return AuthorizedSession(target)


def auth_order() -> list:
    """The ways to post as the app, in the order tried (UNCONFIRMED which works: the lane probe records it)."""
    if AUTH_USED["how"] == "self_impersonation":
        return [("self_impersonation", _self)]
    return [("adc", _adc), ("self_impersonation", _self)]


def create(space: str, thread: str | None, message_id: str, message: dict, session_for=None) -> str:
    """Post `message` as the app. Returns "posted" or "duplicate"; raises PostError."""
    if not SPACE.match(space or "") or not MESSAGE_ID.match(message_id or ""):
        raise PostError(0, False)
    params = {"messageId": message_id}
    body = dict(message)
    if thread and THREAD.match(thread) and thread.startswith(space + "/"):
        params["messageReplyOption"] = REPLY_OPTION
        body["thread"] = {"name": thread}
    last, unanswered = 0, False
    for how, make in ([("given", session_for)] if session_for else auth_order()):
        try:
            session = make([CHAT_SCOPE])
            resp = session.post(f"{CHAT_API}/{space}/messages", params=params, json=body, timeout=POST_TIMEOUT_S)
        except Exception as e:  # noqa: BLE001 - no credential of this kind, or no answer: try the next way
            unanswered = unanswered or not _no_token(e)
            continue
        last = resp.status_code
        if resp.status_code in (401, 403):
            continue                                    # this way cannot post as the app: try the next
        if how != "given":
            AUTH_USED["how"] = how
        if 200 <= resp.status_code < 300:
            return "posted"
        if resp.status_code == DUPLICATE_STATUS:
            return "duplicate"
        raise PostError(resp.status_code, resp.status_code == 429 or resp.status_code >= 500)
    if not session_for:
        AUTH_USED["how"] = "failed" if AUTH_USED["how"] is None else AUTH_USED["how"]
    if not unanswered:              # every way was refused or had no token: a retry would rerun the Desk for nothing
        raise PostError(403, False, auth=True)
    raise PostError(last, True)


def publish(project: str, payload: dict, session=None) -> str:
    """Publish one work message; returns its message id. Raises PostError."""
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project or ""):
        raise PostError(0, False)
    data = base64.b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
    try:
        session = session or _adc([PUBSUB_SCOPE])
        resp = session.post(f"{PUBSUB_API}/projects/{project}/topics/{TOPIC}:publish",
                            json={"messages": [{"data": data}]}, timeout=PUBLISH_TIMEOUT_S)
    except Exception:  # noqa: BLE001 - not published: the handler releases the claim and answers
        raise PostError(0, True)
    if not 200 <= resp.status_code < 300:
        raise PostError(resp.status_code, True)
    try:
        return str((resp.json().get("messageIds") or [""])[0])
    except Exception:  # noqa: BLE001 - published; the id is only for the log
        return ""


def project() -> str:
    return os.environ.get("GOOGLE_CLOUD_PROJECT", "")
