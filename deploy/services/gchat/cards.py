"""The Desk's reply as one Google Chat message in the Cards v2 shape (the Google Chat door, workshop lesson 10.4).
Standard library only.

render(desk, self_url, session_id) takes the JSON POST /v1/desk returned and returns one message: cardsV2[].card with
a header and sections of textParagraph, decoratedText and buttonList widgets, as the Chat API's page on creating
messages shows them. By the Desk's outcome:

    handbook answer     "HR Desk", "From your company handbook": the answer, then Sources (one decoratedText per
                        citation: the document and page, then the quote), then the Desk's chips
    statute answer      "What the law says": the answer, each in-force line whole in its own paragraph, the sources
    clarify             the one question back and a button for each desk the Desk offered
    oos, not_covered,   the Desk's fixed text, then its chips ("Raise a case" when the Desk offers the case desk)
    denied, refusal
    case draft          "Handed to a person": the Desk's text, the queue, the clock and the basis as the Desk sends
                        them, whether the draft has a summary, then Confirm and Cancel; editing stays on the Desk page
    posh                the Desk's fixed template; each office with its Internal Committee members and the district's
                        Local Committee contact as plain text, then the line that its button sends the case to every
                        member listed (the Desk page can leave someone out) and a "Create a confidential record"
                        button that carries a digest of those members, so a press after the committee changed sends
                        nothing; an office whose members do not fit gets the Desk page instead of the button; and the
                        privacy line
    fallback            the answer and the chips, as the Desk sends them

What a card never holds: the person's question (a case draft's summary starts as the masked question, so the card
says whether there is one and does not show it), a gs:// URI or a signed URL (Chat keeps history, and a signed URL
there is a bearer link: sanitise() removes both from every string), legal text of the bridge's own (every template is
the Desk's), or HTML the Desk did not mean (every string is escaped).

Every button calls the bridge back: in the add-on model a button's action.function names the HTTPS endpoint Chat
calls (from memory, UNCONFIRMED: action() is the one place), so it is exactly SELF_URL, the only audience the bridge
verifies, and what the press means is in its parameters: act, the session id, and a chip id, a case id or an office
and its members' digest. Never text. Whether a cardId is required is UNCONFIRMED; each card carries one.

The size: a Chat message is at most 32,000 bytes. The answer is capped at ANSWER_MAX characters, at most CITES_MAX
citations are shown, each quote is capped at QUOTE_MAX characters, an in-force line is never cut, and fit() steps down
until the serialised message is under LIMIT_BYTES.
"""
from __future__ import annotations

import hashlib
import html
import json
import re

ANSWER_MAX = 3000
CITES_MAX = 5
QUOTE_MAX = 300
MEMBERS_MAX = 800
LIMIT_BYTES = 30000
TITLE = "HR Desk"
SUBTITLES = {"handbook": "From your company handbook", "statute": "What the law says"}
HANDED = "Handed to a person"
POSH_MEMBERS = ("This button sends your case to every Internal Committee member listed above. To leave someone out, "
                "use the Desk page instead.")
# What is kept of the message that brought up the card (commands/tests/test_gchat.py holds the line to it): no case (a
# POSH case opens with no text), no Desk checkpoint (a case turn never enters the graph), no row and no claim; a gate
# miss waits in the work queue until the worker acknowledges it, and the subscription drops it unacknowledged at an hour.
POSH_PRIVACY = ("DocuMind keeps no copy of the message that brought up these options: it was read only to decide the "
                "reply, and it is not saved with a case, in the Desk's history or in its logs. If it waited in the "
                "Desk's queue, it was removed from the queue once answered, within an hour at most. This chat stays in "
                "your company's Google Chat under its retention settings.")
POSH_BUTTON = "Create a confidential record"
POSH_TOO_LONG = ("This office's Internal Committee has more members than fit here: see them all, and choose whom to "
                 "send your case to, on the Desk page.")
POSH_CHANGED = ("This office's Internal Committee has changed since these options were shown, so your case was not "
                "sent. Please ask again to see its members now, or use the Desk page.")
EDIT_ON_PAGE = "Editing stays on the Desk page."
POSH_TOO_MANY = "Your company has more offices than fit in one message: choose yours, and its members, on the Desk page."
CHIP_IDS = ("handbook", "statute", "case")
SHOW_OPTIONS = "Show my options"

_GS = re.compile(r"gs://[^\s)\]>\"']+", re.I)
_URL = re.compile(r"https?://[^\s)\]>\"']+", re.I)
_SIGNED = re.compile(r"[?&](?:x-goog-signature|x-goog-credential|signature|x-amz-signature|sig|googleaccessid)=", re.I)
_STORAGE = re.compile(r"^https?://(?:[a-z0-9.-]+\.)?storage\.(?:googleapis|cloud\.google)\.com/", re.I)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitise(s) -> str:
    """The string with every gs:// URI and every signed or Cloud Storage URL removed, and control characters gone."""
    s = _CONTROL.sub("", "" if s is None else str(s))
    s = _GS.sub("[document]", s)
    return _URL.sub(lambda m: "[link removed]" if _SIGNED.search(m.group(0)) or _STORAGE.match(m.group(0))
                    else m.group(0), s)


def esc(s) -> str:
    """Sanitised and escaped for a text field that reads formatting."""
    return html.escape(sanitise(s), quote=False)


def cut(s: str, n: int) -> str:
    return s if len(s) <= n else s[: max(0, n - 3)].rstrip() + "..."


def members_digest(emails) -> str:
    """The POSH button's m: which members its card listed, so a press sends the case to no one the person did not see."""
    return hashlib.sha256("\n".join(sorted(str(e).lower() for e in emails)).encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------- widgets
def paragraph(s) -> dict:
    return {"textParagraph": {"text": esc(s)}}


def action(self_url: str, params: dict) -> dict:
    """A button's onClick: the bridge's own URL as the function, and the press's meaning as parameters."""
    return {"action": {"function": self_url, "parameters": [{"key": k, "value": str(v)} for k, v in params.items()]}}


def button(label: str, self_url: str, **params) -> dict:
    return {"text": sanitise(label)[:80], "onClick": action(self_url, params)}


def buttons(items: list) -> dict:
    return {"buttonList": {"buttons": items}}


def card(card_id: str, header: dict, sections: list) -> dict:
    return {"cardsV2": [{"cardId": card_id, "card": {"header": header, "sections": [s for s in sections if s["widgets"]]}}]}


def header(title: str, subtitle: str | None = None) -> dict:
    return {"title": title, **({"subtitle": subtitle} if subtitle else {})}


def chip_buttons(chips, self_url: str, session_id: str) -> list:
    """The Desk's chips as buttons, the case desk last: each carries its chip id and the session, never text."""
    seen, out = [], []
    for c in chips or ():
        d = c.get("desk") if isinstance(c, dict) else None
        if d in CHIP_IDS and d not in seen:
            seen.append(d)
    for d in sorted(seen, key=lambda x: x == "case"):
        label = next((c.get("label") for c in chips if isinstance(c, dict) and c.get("desk") == d), None) or d
        out.append(button(label, self_url, act="chip", chip=d, sid=session_id))
    return out


def _doc_name(c: dict) -> str:
    src = str(c.get("source_uri") or c.get("source") or "")
    name = src.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1] or "a document"
    page = c.get("page")
    return sanitise(name) + (f", page {page}" if isinstance(page, int) and not isinstance(page, bool) else "")


def _section_text(s: dict) -> tuple[str, list]:
    """A section's answer without its in-force lines, and the lines (the Desk appends them as its last paragraph)."""
    answer = str(s.get("answer") or "")
    lines = [str(x) for x in s.get("in_force") or () if isinstance(x, str)]
    tail = "\n\n" + "\n".join(lines)
    if lines and answer.endswith(tail):
        answer = answer[: -len(tail)]
    return answer, lines


# ---------------------------------------------------------------- the outcomes
def answer_card(desk: dict, self_url: str, session_id: str, answer_max: int = ANSWER_MAX,
                cites_max: int = CITES_MAX, quote_max: int = QUOTE_MAX) -> dict:
    sections = [s for s in desk.get("sections") or () if isinstance(s, dict)]
    first = sections[0].get("desk") if sections else desk.get("route")
    out, budget = [], answer_max
    note = str(desk.get("note") or "").strip()
    if note:
        out.append({"widgets": [paragraph(cut(note, 500))]})
    for s in sections:
        body, lines = _section_text(s)
        body = cut(body.strip(), max(0, budget))
        budget -= len(body)
        widgets = [paragraph(p) for p in body.split("\n\n") if p.strip()]
        widgets += [paragraph(line) for line in lines]                 # the in-force lines, whole
        out.append({"header": esc(s.get("title")) if len(sections) > 1 else None, "widgets": widgets})
    cites = [c for c in desk.get("citations") or () if isinstance(c, dict)][:cites_max]
    if cites:
        out.append({"header": "Sources", "widgets": [
            {"decoratedText": {"topLabel": esc(cut(_doc_name(c), 120)),
                               "text": esc(cut(str(c.get("quote") or ""), quote_max)), "wrapText": True}}
            for c in cites]})
    chips = chip_buttons(desk.get("chips"), self_url, session_id)
    if chips:
        out.append({"widgets": [buttons(chips)]})
    for s in out:
        if s.get("header") is None:
            s.pop("header", None)
    return card("answer", header(TITLE, SUBTITLES.get(first)), out)


def text_card(desk: dict, self_url: str, session_id: str, answer_max: int = ANSWER_MAX) -> dict:
    """clarify, out_of_scope, not_covered, denied, a draft already open, a case the Desk could not draft."""
    words = cut(str(desk.get("answer") or "").strip(), answer_max)
    widgets = [paragraph(p) for p in words.split("\n\n") if p.strip()]
    chips = chip_buttons(desk.get("chips"), self_url, session_id)
    return card("reply", header(TITLE), [{"widgets": widgets}, {"widgets": [buttons(chips)] if chips else []}])


def draft_card(answer: str, case: dict, self_url: str, session_id: str) -> dict:
    """A case the Desk drafted for the person: what it is, who would have it, the clock and the basis, and the two
    presses. The draft's summary is not shown (it starts as the masked question)."""
    owner = case.get("owner") if isinstance(case.get("owner"), dict) else {}
    facts = []
    if owner.get("queue_name"):
        facts.append({"decoratedText": {"topLabel": "Who would have it", "text": esc(owner["queue_name"]),
                                        "wrapText": True}})
    for c in case.get("clock") or ():
        facts.append({"decoratedText": {"topLabel": "The clock", "text": esc(cut(str(c), 600)), "wrapText": True}})
    for b in case.get("basis") or ():
        if isinstance(b, dict):
            label = " ".join(str(x) for x in (b.get("instrument"), b.get("section")) if x)
            facts.append({"decoratedText": {"topLabel": esc(cut(label, 150)), "text": esc(cut(str(b.get("says") or ""), 600)),
                                            "wrapText": True}})
    summary = ("The draft holds your question as its first summary. " if str(case.get("summary") or "").strip()
               else "The draft has no summary yet. ")
    cid = str(case.get("case_id") or "")
    presses = [button("Confirm", self_url, act="confirm", case=cid, sid=session_id),
               button("Cancel", self_url, act="cancel", case=cid, sid=session_id)] if re.fullmatch(r"[0-9a-f]{32}", cid) else []
    return card("case", header(HANDED), [
        {"widgets": [paragraph(p) for p in cut(str(answer or ""), ANSWER_MAX).split("\n\n") if p.strip()]},
        {"widgets": facts},
        {"widgets": [paragraph(summary + EDIT_ON_PAGE)] + ([buttons(presses)] if presses else [])}])


def posh_card(answer: str, offer: dict | None, self_url: str, session_id: str, too_many: bool = False) -> dict:
    """The POSH reply: the Desk's fixed template, each office, and a press per office. offer is the Desk's posh card
    (desk_graph.posh_card), or None when the company's POSH section is incomplete: then the template alone. too_many:
    the offices do not fit in one message, so the card points to the Desk page for them."""
    sections = [{"widgets": [paragraph(p) for p in cut(str(answer or ""), ANSWER_MAX).split("\n\n") if p.strip()]}]
    if too_many:
        sections.append({"widgets": [paragraph(POSH_TOO_MANY)]})
    units = (offer or {}).get("posh") if (offer or {}).get("configured") else None
    if isinstance(units, dict) and units:
        for unit, spec in sorted(units.items()):
            if not isinstance(spec, dict) or not re.fullmatch(r"[a-z0-9_-]{1,40}", str(unit)):
                continue
            members = [m for m in spec.get("members") or () if isinstance(m, dict) and m.get("email")]
            names = [f"{m.get('name') or m.get('email')} ({m.get('email')})" for m in members]
            listed = "; ".join(names)
            lc = spec.get("local_committee") if isinstance(spec.get("local_committee"), dict) else {}
            widgets = [{"decoratedText": {"topLabel": "Internal Committee", "text": esc(cut(listed, MEMBERS_MAX)),
                                          "wrapText": True}},
                       {"decoratedText": {"topLabel": "Local Committee",
                                          "text": esc(cut(", ".join(str(x) for x in (lc.get("name"), lc.get("contact")) if x), 400)),
                                          "wrapText": True}}]
            if len(listed) > MEMBERS_MAX:               # a member the card cut off would get the case unseen
                widgets.append(paragraph(POSH_TOO_LONG))
            elif names:                                 # the press sends the case to every member listed: say so first
                digest = members_digest(m["email"] for m in members)
                widgets += [paragraph(POSH_MEMBERS),
                            buttons([button(POSH_BUTTON, self_url, act="posh", unit=unit, m=digest, sid=session_id)])]
            sections.append({"header": esc(cut(str(spec.get("name") or unit), 120)), "widgets": widgets})
    sections.append({"widgets": [paragraph(POSH_PRIVACY)]})
    return card("posh", header(TITLE), sections)


def fixed_card(words: str, self_url: str, session_id: str | None, cls: str | None, extra: str | None = None) -> dict:
    """A gate hit the bridge answers itself (the Desk was slow, or the question too long): the Desk's own fixed text
    from shared/desk_law.py, and a "Show my options" press when there is a session to press it in. extra: one more
    line of the bridge's (message me directly)."""
    widgets = [paragraph(p) for p in str(words or "").split("\n\n") if p.strip()]
    if extra:
        widgets.append(paragraph(extra))
    presses = [button(SHOW_OPTIONS, self_url, act="options", cls=cls, sid=session_id)] if session_id and cls else []
    return card("fixed", header(TITLE), [{"widgets": widgets}, {"widgets": [buttons(presses)] if presses else []}])


def result_card(title: str, lines: list) -> dict:
    """The answer to a press: a case recorded, opened or cancelled."""
    return card("result", header(title), [{"widgets": [paragraph(cut(str(x), 1200)) for x in lines if x]}])


# ---------------------------------------------------------------- one message
def render(desk: dict, self_url: str, session_id: str) -> dict:
    """One message for one POST /v1/desk reply, under LIMIT_BYTES."""
    desk = desk if isinstance(desk, dict) else {}
    offer = desk.get("case_offer") if isinstance(desk.get("case_offer"), dict) else None
    case = desk.get("case") if isinstance(desk.get("case"), dict) else None
    if desk.get("route") == "case" and offer and offer.get("case_type") == "posh":
        message = posh_card(desk.get("answer"), offer, self_url, session_id)
        return message if size(message) < LIMIT_BYTES else posh_card(desk.get("answer"), None, self_url, session_id,
                                                                     too_many=True)
    if desk.get("route") == "case" and case and case.get("case_id"):
        return fit(draft_card(desk.get("answer"), case, self_url, session_id), desk, self_url, session_id)
    if desk.get("sections"):
        return fit(answer_card(desk, self_url, session_id), desk, self_url, session_id)
    return fit(text_card(desk, self_url, session_id), desk, self_url, session_id)


def size(message: dict) -> int:
    return len(json.dumps(message, ensure_ascii=False).encode("utf-8"))


def fit(message: dict, desk: dict, self_url: str, session_id: str) -> dict:
    """The message, or a smaller one: fewer sources and shorter quotes, then a shorter answer, then the text alone."""
    if size(message) < LIMIT_BYTES:
        return message
    if desk.get("sections"):
        for answer_max, cites_max, quote_max in ((ANSWER_MAX, 3, 150), (1500, 0, 0)):
            smaller = answer_card(desk, self_url, session_id, answer_max, cites_max, quote_max)
            if size(smaller) < LIMIT_BYTES:
                return smaller
    smaller = text_card(desk, self_url, session_id, 1500)
    if size(smaller) < LIMIT_BYTES:
        return smaller
    return {"text": cut(sanitise(desk.get("answer") or ""), 1500)}
