"""The Google Chat bridge's own fixed replies (the Google Chat door, workshop lesson 10.4). Standard library only.

Every reply here is the bridge's: what the HR Desk app says when it does not ask the Desk, or when the Desk refused
the person. None names a law or a committee: legal text comes only from the Desk, whose one source is
shared/desk_law.py. None echoes what the person typed.

DESK_NOT_A_MEMBER and DESK_DOOR_OFF are the Desk's own 403 details (services/chat/delegation.py), word for word, so
the bridge can tell the two denials from every other refusal; commands/tests/test_gchat.py holds them equal.
"""
from __future__ import annotations

DESK_NOT_A_MEMBER = "not a member of any tenant"
DESK_DOOR_OFF = "the Google Chat door is not switched on for your company"

WELCOME_TITLE = "HR Desk"
WELCOME = ("Ask me a question about your company's handbook or about Indian employment law, in a direct message. I "
           "answer from your company's own documents and the law DocuMind holds, with the sources, and I can hand a "
           "question to a person on the People team.")
WELCOME_PRIVACY = ("What you type here stays in your company's Google Chat under its retention settings. DocuMind "
                   "masks Aadhaar and card numbers before it reads a question.")

ACK = "Thanks. I am reading your question now: the answer follows here in a moment."
ALREADY = "I have this one already: the answer follows here."
TAKEN = "I have that one already. If you cannot see my answer above, please ask again."   # promises nothing later
NOT_ON_ROSTER = ("Your account is not on a DocuMind roster, so the HR Desk cannot answer you here. Ask your People "
                 "team to add you.")
DOOR_OFF = ("The HR Desk in Google Chat is not switched on for your company. You can still ask on the DocuMind Desk "
            "page.")
DM_ONLY = "Please message me directly: I answer in a direct message only, so nobody else reads your question."
TYPED_ONLY = "I read typed questions only. Please type your question as a message, without a file or an image."
TOO_LONG = "That question is longer than 4,000 characters. Please ask it in fewer words."
RATE_LIMITED = "That is a lot of questions in one minute. Please wait a minute and ask again."
NO_ACCOUNT = ("I could not read your account from this message, so I cannot tell which company you belong to. Please "
              "use the DocuMind Desk page.")
UNREACHABLE = "I could not reach the HR Desk just now. Please ask again in a few minutes, or use the DocuMind Desk page."
STALE = "That button belongs to an older conversation. Please ask your question again."
REFUSED = "The HR Desk could not do that: "            # followed by the Desk's own fixed reason
CANCELLED = "Cancelled. The draft is gone, and nobody was sent anything."


# The add-on model's synchronous reply wraps the message (the HTTP quickstart for Chat apps); the classic model's reply
# is the message itself, which is from memory. The lane probe records the shape a real event carried.
def wrap(message: dict, shape: str | None) -> dict:
    """The HTTP response body that posts `message` in reply, for the event's shape."""
    if shape == "addon":
        return {"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": message}}}}
    return message


def text(words: str) -> dict:
    """A message of plain text."""
    return {"text": words}


def welcome() -> dict:
    """The card an "Added to space" event gets."""
    return {"cardsV2": [{"cardId": "welcome", "card": {
        "header": {"title": WELCOME_TITLE, "subtitle": "DocuMind"},
        "sections": [{"widgets": [{"textParagraph": {"text": WELCOME}},
                                  {"textParagraph": {"text": WELCOME_PRIVACY}}]}]}}]}


def for_denial(detail) -> str | None:
    """The bridge's reply to the Desk's 403 detail, when it is one of the two denials about the person."""
    return {DESK_NOT_A_MEMBER: NOT_ON_ROSTER, DESK_DOOR_OFF: DOOR_OFF}.get(detail if isinstance(detail, str) else None)
