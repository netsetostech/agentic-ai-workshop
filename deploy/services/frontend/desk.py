"""The Desk page, its case half (workshop lesson 5.6): a person is one press away.

    What it reads   GET /v1/cases/offer: the person as the chat service saw them, their roles, the Desk's switches as
                    the doors read them (desk_gate, desk_route), the kinds of case set up in their company, and the
                    POSH card (each office's Internal Committee members and its Local Committee contact).
                    GET /v1/cases: the cases they raised and, for a queue role, their inbox. Both answers name the
                    email and the company the service saw, and the page draws no case data unless they are the
                    signed-in person's: a UI running without IAP calls as its own account.
    Tell the Desk   Only for an employee (a leaver has the case desk alone, shared/roles.py), and only while desk_gate
                    is not off, because with it off the door lets every turn through to a model. The words go to POST
                    /v1/chat, through the chat door in front of it (services/chat/desk.py). A gate hit gets the door's
                    fixed reply - no model call, or with desk_gate on, the one check that found it - and the case it
                    offers (case_offer): the POSH card opens at once; another kind gets a button that starts it. Other
                    words get the chat service's direct answer, shown as the Chat page shows it. What was typed goes to
                    /v1/chat and nowhere else: never shown back, never kept (the form clears on Send), never in a case.
    Raise a case    Always shown, with the kinds the offer lists. POSH opens at once from its card and holds no text:
                    one token per office and choice of members, a "Recorded" panel for the office it was recorded for,
                    and "Record another" to start again. When the service cannot open it (409: none of the chosen
                    members can receive a case yet; 503: their roles could not be read), its words are shown under
                    the contacts. The other kinds come back as a draft the person edits, then sends with a token of
                    the page's own (the same press twice is one case) or cancels, which deletes it. A draft not sent
                    within 30 minutes expires: the person's words and kind come back in the form.
    Your cases      The cases this person raised and sent.
    Your inbox      Only for a person with a queue role, and only the cases of the queues those roles read, open ones
                    first. The page holds the service's list to the same rule (QUEUES, a copy of
                    shared/desk_law.QUEUES), so it never shows another queue's case or who raised it.

When the roles cannot be read (GET /v1/cases fails, or roles_for's "unread"), the page shows Raise a case and nothing
else: shared/roles.py allows only the case desk then. The routed Desk's answers (workshop lesson 10.4) are
routed_half(), which desk_page() reaches only for an employee while desk_route is on or single; with desk_route off or
shadow, the page is the case half alone.

Every call goes to the chat service with chat.py's _headers(CHAT_URL): the UI's own ID token for Cloud Run, and the
person's IAP assertion forwarded, so the service decides who is asking and for which company, never this page. The page
holds none of shared/desk_law.py's wording: the fixed replies, the clocks and the law a case rests on are shown as the
service sends them. A call that does not work is told in a plain sentence of the page's own, by its status; only the
POSH card's 409 and 503, written for the person, are shown in the service's words. No call can show a traceback.

routed_half(): while desk_route is on or single, an employee gets Ask the Desk in place of Tell the Desk: the question
goes to POST /v1/desk with the page's Desk session (and the draft it shows, if any), and the reply comes back as the
desks answered it - each desk's section through the Chat page's renderer with its citations, the statute desk's
in-force lines inside its text, a clarify's two buttons, the chips a reply offers (ask another desk, or raise a case),
the out_of_scope reply and the case it points to: the POSH card opens at once, and a drafted case waits under Raise a
case to be checked and sent. The reply is shown only when it names the signed-in person and their company; the question
is never shown back or kept, and a 409 (a chip no longer on offer) has its own plain sentence.
"""
from __future__ import annotations

import html
import re
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone

import requests
import streamlit as st

from auth import tenant_for
from chat import CHAT_URL, _as_source, _headers
from citations import render_with_citations

CASE_TIMEOUT_S = 30
CHAT_TIMEOUT_S = 120           # chat.py's: above the chat service's own bound on a turn
QUESTION_MAX = 4000            # ChatRequest.question's max_length (services/chat/agent.py)
SUMMARY_MAX = 1000             # shared/cases.SUMMARY_MAX: the longest summary the case routes take
IST = timezone(timedelta(hours=5, minutes=30))
CASE_ID = re.compile(r"^[0-9a-f]{32}$")
LAW_URL = re.compile(r"^https://[^\s()<>\[\]]+$")    # a law link, with nothing that could break out of it

# The six kinds of case the button offers (shared/desk_law.CASE_TYPES), in plain words: as the person chooses one, and
# as a list names it.
CASE_TYPES = {
    "posh": "Sexual harassment at work (POSH)",
    "grievance": "A complaint about how I am treated at work",
    "privacy_request": "My personal data: see it, correct it or delete it",
    "exit_dues": "Money owed to me after leaving: salary, leave or gratuity",
    "people_query": "A question for the HR team",
    "human_requested": "I want to talk to a person",
}
CASE_NAMES = {"posh": "POSH complaint", "grievance": "Grievance", "privacy_request": "Personal data request",
              "exit_dues": "Dues after leaving", "people_query": "Question for HR",
              "human_requested": "Asked for a person"}
# The button under a fixed reply that starts the case it offers (POSH needs none: its card opens at once).
START = {"grievance": "Raise a grievance", "privacy_request": "Make a personal data request",
         "exit_dues": "Ask about money owed after leaving", "people_query": "Ask the HR team",
         "human_requested": "Ask for a person"}
STATUS = {"draft": "Not sent yet", "open": "Sent", "acknowledged": "Seen by the team", "in_progress": "Being worked on",
          "resolved": "Resolved", "closed": "Closed", "withdrawn": "Withdrawn"}
MOVE = {"acknowledged": "Acknowledged (we have seen it)", "in_progress": "In progress", "resolved": "Resolved",
        "closed": "Closed"}
# shared/cases.NEXT: the moves a queue may make from each status.
NEXT = {"open": ("acknowledged", "in_progress", "resolved", "closed"),
        "acknowledged": ("in_progress", "resolved", "closed"),
        "in_progress": ("resolved", "closed"),
        "resolved": ("in_progress", "closed")}
# shared/desk_law.QUEUES: the roles that read a queue's cases ("read"), move them along ("status"), and read one only
# when the person who raised it chose to share it ("opt_in"). ic:<unit> is a POSH queue: only the Internal Committee
# members of that unit (ic_member:<unit>) whom the person chose.
QUEUES = {
    "grc": {"read": ("grc_member",), "status": ("grc_member",), "opt_in": ("people_ops",)},
    "privacy": {"read": ("privacy",), "status": ("privacy",), "opt_in": ()},
    "payroll": {"read": ("payroll", "people_ops"), "status": ("payroll",), "opt_in": ()},
    "people": {"read": ("people_ops",), "status": ("people_ops",), "opt_in": ()},
}
IC_QUEUE, IC_ROLE = "ic:", "ic_member:"
EMPLOYEE = "employee"          # shared/roles.EMPLOYEE: the one role with the answer desks, so the one with the box
UNREAD = "unread"              # shared/roles.UNREAD: what a failed role read gives
ROUTED_MODES = ("on", "single")
# The buttons under a routed reply (services/chat/desk_routes.DESKS' chip labels): ask another desk, or a person.
ROUTED_CHIPS = {"handbook": "Ask what the company handbook says", "statute": "Ask what the law says",
                "case": "Raise a case"}

SIGN_IN = ("The case desk needs your company's sign-in (IAP), and it could not confirm that you are the person signed "
           "in here, so nothing is shown. Please ask your administrator to check the sign-in.")
POSH_KEEPS = ("The record keeps your name, your office and the members you chose, and none of your words. Only those "
              "members see it in their inbox.")
# What the person is told when a call does not work: the sentence for that place first, then the one for the status.
# Never the service's own words, which are written for an engineer and can repeat what was sent.
PLAIN = {
    0: "The Desk could not be reached just now. Please try again in a minute.",
    401: "The Desk could not confirm who you are. Please reload the page, or sign in again.",
    403: "Your account cannot do this here. If you think it should, please ask the People team.",
    404: "This case could not be found. It may have been withdrawn.",
    409: "This case has changed since the page was loaded. Please reload the page.",
    413: "That is too long. Please shorten it and try again.",
    422: "Please check what you entered and try again.",
    501: "Cases are not available in this version of DocuMind. Please contact the People team directly.",
    503: "The Desk is not available just now. Please try again in a minute.",
}
IN_PLACE = {
    ("offer", 403): "Your account cannot raise a case here. If you think it should, please ask the People team.",
    ("draft", 409): "Your company has not set up this kind of case here yet. Please contact the People team directly.",
    ("send", 409): "This request was already sent or cancelled. Look for it under Your cases.",
    ("cancel", 409): "This case is closed, so it cannot be withdrawn.",
    ("move", 403): "Only the team this case was sent to can change its status.",
    ("move", 409): "This case cannot move to that status now. Please reload the page to see where it is.",
}
ASK_PROBLEM = {409: "That choice is no longer on offer. Please ask your question again."}
GONE = {404: "This request was not sent: it could not be found any more.",
        410: "This request was not sent: a request is kept for 30 minutes only."}


# ---------------------------------------------------------------- the calls
def _api(method: str, path: str, body: dict | None = None, timeout: int = CASE_TIMEOUT_S):
    """(status, JSON body or None) from the chat service, as the person. A call that does not arrive is (0, None)."""
    try:
        r = requests.request(method, f"{CHAT_URL}{path}", json=body, headers=_headers(CHAT_URL), timeout=timeout)
    except Exception:  # noqa: BLE001 - the page says the Desk could not be reached; it never shows a traceback
        return 0, None
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, None


def _problem(status: int, place: str = "") -> str:
    return (IN_PLACE.get((place, status)) or PLAIN.get(status)
            or f"The Desk could not do this just now (error {status}). Please try again in a minute.")


def _posh_problem(status: int, body) -> str:
    """The POSH card's 409 (whom to contact instead) and 503 (try again) are written for the person: those are shown
    in the service's words. Anything else gets the page's plain sentence."""
    detail = body.get("detail") if isinstance(body, dict) else None
    if status in (409, 503) and isinstance(detail, str) and detail.strip():
        text = detail.strip()[:300]
        return text[:1].upper() + text[1:]
    return _problem(status)


def _case_path(case_id, action: str = "") -> str | None:
    cid = str(case_id or "")
    return f"/v1/cases/{cid}{action}" if CASE_ID.match(cid) else None


def _seen_as(body: dict, email: str, tenant_id: str) -> bool:
    """Whether the service saw the signed-in person, in their company, and not someone else (the UI's own account)."""
    seen = str(body.get("email") or "").strip().lower()
    return bool(seen) and seen == email and body.get("tenant") == tenant_id


def _roles(body) -> list[str]:
    return [r for r in _list((body or {}).get("roles")) if isinstance(r, str)]


def offered_types(offer) -> list[str]:
    return [t for t in _list((offer or {}).get("types")) if _word(t) in CASE_TYPES]


def posh_units(offer) -> dict:
    posh = (offer or {}).get("posh")
    return {str(u): v for u, v in posh.items() if isinstance(v, dict)} if isinstance(posh, dict) else {}


# ---------------------------------------------------------------- who reads what
def has_queue_role(roles) -> bool:
    held = set(roles or ())
    queue_roles = {r for spec in QUEUES.values() for k in ("read", "status", "opt_in") for r in spec[k]}
    return bool(held & queue_roles) or any(str(r).startswith(IC_ROLE) for r in held)


def _on_ic(case: dict, email: str, held: set) -> bool:
    q = str(case.get("queue") or "")
    return (IC_ROLE + q[len(IC_QUEUE):] in held
            and email in [str(c).lower() for c in _list(case.get("chosen_contacts"))])


def in_my_queue(case: dict, email: str, roles) -> bool:
    """shared/cases.access's rule for a queue's reader: a POSH case only for the chosen Internal Committee members of
    its unit; any other case for its queue's roles, or for an opt_in role when the person chose to share it. A draft,
    or any case that was never opened, is in nobody's inbox."""
    if case.get("status") == "draft" or not case.get("opened_at"):
        return False
    held, email, q = set(roles or ()), (email or "").lower(), str(case.get("queue") or "")
    if q.startswith(IC_QUEUE):
        return _on_ic(case, email, held)
    spec = QUEUES.get(q)
    if not spec:
        return False
    return bool(held & set(spec["read"] + spec["status"])) or (
        bool(held & set(spec["opt_in"])) and case.get("people_ops_opt_in") is True)


def can_move(case: dict, email: str, roles) -> bool:
    """Whether the reader may change the case's status (the service answers 403 otherwise)."""
    held, email, q = set(roles or ()), (email or "").lower(), str(case.get("queue") or "")
    if q.startswith(IC_QUEUE):
        return _on_ic(case, email, held)
    return bool(held & set((QUEUES.get(q) or {}).get("status", ())))


# ---------------------------------------------------------------- showing things
_MD_SPECIAL = set("\\`*_{}[]()<>#+-.!|~$&:")


def _md(text) -> str:
    """Text shown as itself: Markdown's special characters escaped, so a summary or a contact cannot become a link, an
    image, a heading or a formula. Line breaks are kept."""
    return "".join("\\" + ch if ch in _MD_SPECIAL else ch for ch in str(text or "")).replace("\n", "  \n")


def _list(value) -> list:
    """A list from the service, or an empty one when it sent something else."""
    return value if isinstance(value, list) else []


def _word(value) -> str | None:
    """A value from the service used to look something up: a string, or nothing (never a list or a dict)."""
    return value if isinstance(value, str) else None


def _when(value) -> str:
    try:
        d = datetime.fromisoformat(str(value))
        d = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        return d.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")
    except (ValueError, OverflowError):
        return ""


def _day(value) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _ref(case: dict) -> str:
    return str(case.get("case_id") or "")[:8].upper()


def _owner_lines(case: dict) -> list[str]:
    """Who has the case, as the person who raised it sees it."""
    owner = case.get("owner") if isinstance(case.get("owner"), dict) else {}
    if str(case.get("queue") or "").startswith(IC_QUEUE):
        names = ", ".join(str(m.get("name") or m.get("email") or "") for m in _list(owner.get("members"))
                          if isinstance(m, dict))
        lc = owner.get("local_committee") if isinstance(owner.get("local_committee"), dict) else {}
        return [f"**Goes to:** the Internal Committee members you chose: {_md(names)}",
                f"**Local Committee:** {_md(lc.get('name'))}, {_md(lc.get('contact'))}" if lc.get("contact")
                else "**Local Committee:** not added yet. Please ask the People team."]
    contact = f" ({_md(owner.get('contact'))})" if owner.get("contact") else ""
    return [f"**Goes to:** {_md(owner.get('queue_name') or 'the team your company names')}{contact}"]


def _target(case: dict) -> None:
    """The target date, and beneath it the clock lines: whose date it is, and what the law says."""
    if case.get("due_at"):
        st.markdown(f"**Target date:** {_when(case['due_at'])}")
    for line in _list(case.get("clock")):
        st.caption(_md(line))


def _person_view(case: dict) -> None:
    """A case as the person who raised it reads it: who has it, the target date and its clock, and the law."""
    for line in _owner_lines(case):
        st.markdown(line)
    _target(case)
    basis = [b for b in _list(case.get("basis")) if isinstance(b, dict)]
    if basis:
        st.markdown("**The law it rests on:**  \n" + "  \n".join(
            _md(b.get("instrument")) + (", " + _md(b.get("section")) if b.get("section") else "")
            + ": " + _md(b.get("says"))
            + (f" [Read it]({b['url']})" if LAW_URL.match(str(b.get("url") or "")) else "") for b in basis))


# ---------------------------------------------------------------- Tell the Desk
def tell_section(types: list[str]) -> None:
    st.subheader("Tell the Desk")
    with st.form("desk_tell", clear_on_submit=True):
        text = st.text_area("What do you need help with?", max_chars=QUESTION_MAX, height=100,
                            placeholder="For example: I want to talk to someone in HR.")
        sent = st.form_submit_button("Send")
    if sent and text and text.strip():
        _tell(text, types)


def _tell(text: str, types: list[str]) -> None:
    ss = st.session_state
    ss.pop("desk_reply", None)
    status, body = _api("POST", "/v1/chat", {"question": text, "session_id": ss.desk_session, "brain": "direct"},
                        timeout=CHAT_TIMEOUT_S)
    if status != 200 or not isinstance(body, dict):
        st.error(_problem(status))           # never the service's words: a 422 can repeat what was typed
        return
    gate = body.get("brain") == "desk_gate"   # model "none" for a rule, the check's model when the check found it
    offer = body.get("case_offer") if gate and isinstance(body.get("case_offer"), dict) else {}
    cites = body.get("citations")
    ss.desk_reply = {"gate": gate, "checked": gate and body.get("model") != "none",
                     "answer": str(body.get("answer") or ""),
                     "citations": [c for c in cites if isinstance(c, dict)] if isinstance(cites, list) and not gate
                     else [],
                     "offered": offer.get("case_type") if _word(offer.get("case_type")) in CASE_TYPES else None}
    if ss.desk_reply["offered"] == "posh" and "posh" in types:
        ss["desk_kind"] = "posh"             # the POSH card at once: Raise a case below draws its chooser after this


def reply_section(types: list[str]) -> None:
    ss = st.session_state
    r = ss.get("desk_reply")
    if not r:
        return
    with st.container(border=True):
        if r["gate"]:
            st.markdown(_md(r["answer"]))     # the chat door's fixed reply, as it came
            used = ("An AI model read your message only to decide that it should go to a person; it wrote nothing."
                    if r.get("checked") else "No AI model was used.")
            st.caption(f"This is a fixed reply. {used} To reach a person, raise the case below. "
                       "A case does not include what you typed here.")
            kind = r.get("offered")
            if kind in START and kind in types:
                if st.button(START[kind], key="desk_start"):
                    ss["desk_kind"] = kind   # before Raise a case draws its chooser
            elif kind and kind not in types:
                st.caption("Your company has not set up this kind of case here yet. Please contact the People team "
                           "directly.")
            return
        try:
            cited = [_as_source(c) for c in r["citations"]]
        except Exception:  # noqa: BLE001 - a citation the page cannot read is left out, never shown as a traceback
            cited = []
        shown = False
        if cited:                            # as the Chat page shows a reply from the chat service
            try:
                render_with_citations(html.escape(r["answer"], quote=False), cited)
                shown = True
            except Exception:  # noqa: BLE001 - shown plainly instead
                shown = False
        if not shown:
            st.markdown(r["answer"])
        st.caption("DocuMind's answer from your company's documents. If you need a person, raise a case below.")


# ---------------------------------------------------------------- Raise a case
def raise_section(offer, problem: str = "") -> None:
    """The kinds the offer lists, a draft waiting to be sent, and the form or card for the kind chosen. Without an
    offer, one plain line says why."""
    ss = st.session_state
    st.subheader("Raise a case")
    if offer is None:
        st.info(problem)
        return
    st.caption("A case goes to the people your company or the law names to handle it.")
    draft = ss.get("desk_draft")
    if draft:
        draft_view(draft)
    types = offered_types(offer)
    if not types:
        st.info("Your company has not set up any kind of case here yet. Please contact the People team directly.")
        return
    if ss.get("desk_kind") not in (None, *types):
        ss.pop("desk_kind", None)            # a kind no longer offered: the chooser starts empty
    kind = st.selectbox("What is it about?", types, index=None, format_func=CASE_TYPES.get, placeholder="Choose one",
                        key="desk_kind")
    if kind == "posh":
        posh_card(posh_units(offer))
    elif kind and draft:
        st.caption("Send or cancel the request above before you start another.")
    elif kind:
        new_case_form(kind)


def posh_card(units: dict) -> None:
    """The office, its Internal Committee members and their contacts, and the Local Committee, always shown. The record
    holds the person, the office and the chosen members; nothing typed on this page reaches it."""
    ss = st.session_state
    with st.container(border=True):
        st.markdown("**Sexual harassment at work**")
        st.markdown("Choose your office and the Internal Committee members you want to contact. You decide what to "
                    "tell them.")
        if not units:
            st.warning("Your company's committee contacts could not be shown just now. Please ask the People team "
                       "how to reach your Internal Committee, or contact the Local Committee of your district.")
            return
        if ss.get("desk_posh_unit") not in (None, *units):
            ss.pop("desk_posh_unit", None)
        unit = st.selectbox("Your office", list(units), format_func=lambda u: str(units[u].get("name") or u),
                            key="desk_posh_unit")
        members = [m for m in _list(units[unit].get("members")) if isinstance(m, dict) and m.get("email")]
        names = {str(m["email"]).lower(): f"{m.get('name') or m['email']} ({m['email']})" for m in members}
        st.markdown("**Internal Committee for this office:**  \n" + ("  \n".join(_md(n) for n in names.values())
                                                                   or "not added yet. Please ask the People team."))
        lc = units[unit].get("local_committee") if isinstance(units[unit].get("local_committee"), dict) else {}
        if lc.get("contact"):
            st.markdown(f"**Local Committee:** {_md(lc.get('name'))}  \n**Contact:** {_md(lc['contact'])}")
        else:
            st.markdown("**Local Committee:** not added yet. Please ask the People team.")
        done = ss.get("desk_posh_done")
        if isinstance(done, dict) and done.get("unit") == unit:
            st.success(f"Recorded. Your case reference is {_ref(done['view'])}.")
            _person_view(done["view"])
            if st.button("Record another", key="desk_posh_another"):
                ss.pop("desk_posh_done", None)
                ss.pop("desk_posh_tokens", None)
                st.rerun()
            return
        with st.form("desk_posh"):
            chosen = st.multiselect("Internal Committee members to contact", list(names), format_func=names.get,
                                    placeholder="Choose one or more", key=f"desk_posh_members_{unit}")
            st.caption(POSH_KEEPS)
            go = st.form_submit_button("Create a confidential record", type="primary")
        if go:
            _record_posh(unit, chosen)


def _record_posh(unit: str, chosen) -> None:
    ss = st.session_state
    chosen = sorted(str(c) for c in chosen or [])
    if not chosen:
        st.error("Choose at least one member to contact.")
        return
    # One token per office and choice of members until "Record another": the same press twice opens one case.
    tokens = ss.setdefault("desk_posh_tokens", {})
    token = tokens.setdefault(f"{unit}|{','.join(chosen)}", secrets.token_urlsafe(16))
    status, body = _api("POST", "/v1/cases", {"case_type": "posh", "unit": unit, "contacts": chosen, "token": token})
    if status == 200 and isinstance(body, dict) and _case_path(body.get("case_id")):
        ss.desk_posh_done = {"unit": unit, "view": body}
        st.rerun()
    else:
        st.error(_posh_problem(status, body))


def new_case_form(kind: str) -> None:
    refill = st.session_state.get("desk_refill")
    refill = refill if isinstance(refill, dict) and refill.get("kind") == kind else {}
    with st.form(f"desk_new_{kind}"):
        summary = st.text_area("In your own words (you can change this before sending)",
                               value=str(refill.get("summary") or ""), max_chars=SUMMARY_MAX, height=120)
        last_day = (st.date_input("Your last working day", value=_day(refill.get("last_working_day")),
                                  format="DD/MM/YYYY") if kind == "exit_dues" else None)
        share = (st.checkbox("Also share this with the HR team", value=bool(refill.get("share")))
                 if kind == "grievance" else False)
        go = st.form_submit_button("Next: check it before sending")
    if go:
        _draft(kind, summary, last_day, share)


def _draft(kind: str, summary, last_day, share) -> None:
    ss = st.session_state
    body = {"case_type": kind}
    if summary and summary.strip():
        body["summary"] = summary.strip()
    if last_day:
        body["last_working_day"] = last_day.isoformat()
    if share:
        body["people_ops_opt_in"] = True
    status, out = _api("POST", "/v1/cases", body)
    if status == 200 and isinstance(out, dict) and out.get("status") == "draft" and _case_path(out.get("case_id")):
        ss.pop("desk_refill", None)
        ss.desk_draft = {"view": out, "token": secrets.token_urlsafe(16)}
        st.rerun()
    else:
        st.error(_problem(status, "draft"))


def draft_view(draft: dict) -> None:
    v = draft["view"]
    with st.container(border=True):
        st.markdown(f"**{_md(CASE_NAMES.get(_word(v.get('case_type')), 'Your request'))}**: not sent yet")
        _person_view(v)
        with st.form("desk_draft"):
            summary = st.text_area("In your own words (you can change this)", value=str(v.get("summary") or ""),
                                   max_chars=SUMMARY_MAX, height=140)
            share = (st.checkbox("Also share this with the HR team", value=bool(v.get("people_ops_opt_in")))
                     if v.get("case_type") == "grievance" else None)
            send = st.form_submit_button("Send", type="primary")
            cancel = st.form_submit_button("Cancel this request")
        until = _when(v.get("expire_at"))
        st.caption("Nothing is sent until you press Send. This draft is kept for 30 minutes"
                   + (f", until {until}." if until else "."))
    if send:
        _confirm(draft, summary, share)
    elif cancel:
        _cancel(draft)


def _confirm(draft: dict, summary, share) -> None:
    ss = st.session_state
    v = draft["view"]
    body = {"token": draft["token"], "summary": str(summary or "").strip()}
    if share is not None:
        body["people_ops_opt_in"] = bool(share)
    status, out = _api("POST", _case_path(v["case_id"], "/confirm"), body)
    if status == 200 and isinstance(out, dict) and out.get("status") not in (None, "draft"):
        ss.pop("desk_draft", None)
        ss.desk_flash = ("ok", f"Sent. Your case reference is {_ref(out)}. You can follow it under Your cases.")
        st.rerun()
    elif status in GONE:                     # expired, or gone: the person's words and kind come back in the form
        ss.pop("desk_draft", None)
        ss.desk_refill = {"kind": v.get("case_type"), "summary": str(summary or ""), "share": bool(share),
                          "last_working_day": v.get("last_working_day")}
        ss["desk_kind"] = v.get("case_type")  # Raise a case draws its chooser after the draft
        ss.desk_flash = ("error", GONE[status] + " Your words are below: check them and press Next to send them again.")
        st.rerun()
    else:
        st.error(_problem(status, "send"))


def _cancel(draft: dict) -> None:
    ss = st.session_state
    status, out = _api("POST", _case_path(draft["view"]["case_id"], "/cancel"))
    if status in (200, 404):
        ss.pop("desk_draft", None)
        opened = isinstance(out, dict) and out.get("opened_at")     # sent after all (a reply that never arrived)
        ss.desk_flash = ("ok", "Withdrawn. The team sees that you withdrew it." if opened
                         else "Cancelled. Nothing was sent.")
        st.rerun()
    else:
        st.error(_problem(status, "cancel"))


# ---------------------------------------------------------------- your cases, your inbox
def mine_section(rows) -> None:
    rows = [c for c in _list(rows) if isinstance(c, dict)]
    if not rows:
        return
    st.subheader("Your cases")
    for c in rows:
        name, state = CASE_NAMES.get(_word(c.get("case_type")), "Case"), STATUS.get(_word(c.get("status")), "Sent")
        with st.expander(f"{name}. Status: {state}"):
            st.caption(f"Reference {_ref(c)}, sent {_when(c.get('opened_at') or c.get('created_at'))}")
            _person_view(c)


def inbox_section(rows, email: str, roles) -> None:
    """Only the cases of the queues the reader's roles read, open ones first as the service lists them; who raised
    each is shown to that queue alone."""
    rows = [c for c in _list(rows) if isinstance(c, dict) and in_my_queue(c, email, roles)]
    st.subheader("Your inbox")
    st.caption("Cases sent to a team you are on. Open cases come first.")
    if not rows:
        st.info("Nothing is waiting for you.")
        return
    for c in rows:
        with st.container(border=True):
            st.markdown(f"**{_md(CASE_NAMES.get(_word(c.get('case_type')), 'Case'))}**  \nStatus: "
                        f"{STATUS.get(_word(c.get('status')), '')}. Reference {_ref(c)}.")
            lines = [f"**Raised by:** {_md(c.get('requester'))}",
                     f"**Sent:** {_when(c.get('opened_at') or c.get('created_at'))}"]
            if str(c.get("queue") or "").startswith(IC_QUEUE):
                owner = c.get("owner") if isinstance(c.get("owner"), dict) else {}
                lines.append(f"**Office:** {_md(c.get('unit'))}")
                lines.append("**Members chosen:** " + _md(", ".join(str(m.get("name") or m.get("email") or "")
                                                                  for m in _list(owner.get("members"))
                                                                  if isinstance(m, dict))))
            if c.get("case_type") == "grievance" and c.get("people_ops_opt_in") is True:
                lines.append("**Shared with the HR team:** yes")
            if c.get("last_working_day"):
                lines.append(f"**Last working day:** {_md(c['last_working_day'])}")
            st.markdown("  \n".join(lines))
            _target(c)
            if c.get("summary"):
                st.markdown("**In their words:**  \n" + _md(c["summary"]))
            nxt = NEXT.get(_word(c.get("status")))
            path = _case_path(c.get("case_id"), "/status")
            if nxt and path and can_move(c, email, roles):
                with st.form(f"desk_move_{c['case_id']}"):
                    to = st.selectbox("Change the status to", list(nxt), format_func=MOVE.get,
                                      key=f"desk_to_{c['case_id']}")
                    go = st.form_submit_button("Update")
                if go:
                    _move(path, to)


def _move(path: str, to: str) -> None:
    status, out = _api("POST", path, {"status": to})
    if status == 200:
        st.session_state.desk_flash = ("ok", f"Updated: {MOVE.get(to, to)}.")
        st.rerun()
    else:
        st.error(_problem(status, "move"))


def routed_half(tenant_id: str, offer: dict) -> None:
    """The routed Desk (workshop lesson 10.4), for an employee while the tenant's desk_route is on or single, in place
    of Tell the Desk. desk_page() draws it before Raise a case, so a reply can open the POSH card or show its draft
    there."""
    if (not isinstance(offer, dict) or EMPLOYEE not in _roles(offer) or _word(offer.get("desk_route"))
            not in ROUTED_MODES):
        return
    ss = st.session_state
    st.subheader("Ask the Desk")
    st.caption("DocuMind sends your question to the desk that answers it: your company's handbook, the law, or a "
               "person.")
    with st.form("desk_ask", clear_on_submit=True):
        text = st.text_area("Your question", max_chars=QUESTION_MAX, height=100,
                            placeholder="For example: How many days of notice do I give when I resign?")
        sent = st.form_submit_button("Ask")
    if sent and text and text.strip():
        _ask({"question": text}, offer, tenant_id)
    r = ss.get("desk_routed")
    if isinstance(r, dict):
        routed_reply(r, offer, tenant_id)


def _ask(body: dict, offer: dict, tenant_id: str) -> bool:
    """One turn: POST /v1/desk with the page's Desk session and the draft it shows. Only the reply is kept. False,
    with a plain line drawn, when there is no reply to show."""
    ss = st.session_state
    ss.pop("desk_routed", None)
    session = ss.get("desk_session") or uuid.uuid4().hex[:12]
    ss.desk_session = session
    body = {**body, "session_id": session}
    draft = ss.get("desk_draft")
    view = draft.get("view") if isinstance(draft, dict) and isinstance(draft.get("view"), dict) else {}
    if _case_path(view.get("case_id")):
        body["draft_id"] = view["case_id"]
    status, out = _api("POST", "/v1/desk", body, timeout=CHAT_TIMEOUT_S)
    if status != 200 or not isinstance(out, dict):
        st.error(ASK_PROBLEM.get(status) or _problem(status))   # never the service's words: a 422 can repeat the question
        return False
    if not _seen_as(out, str(offer.get("email") or "").strip().lower(), tenant_id):
        st.warning(SIGN_IN)                  # the service answered for someone else: nothing of it is shown
        return False
    sections = []
    for s in _list(out.get("sections")):
        if isinstance(s, dict):
            sections.append({"title": str(s.get("title") or ""), "answer": str(s.get("answer") or ""),
                             "citations": [c for c in _list(s.get("citations")) if isinstance(c, dict)]})
    chips = []
    for c in _list(out.get("chips")):
        desk = _word(c.get("desk")) if isinstance(c, dict) else None
        if desk in ROUTED_CHIPS and desk not in chips:
            chips.append(desk)
    offered = out.get("case_offer") if isinstance(out.get("case_offer"), dict) else {}
    kind = _word(offered.get("case_type"))
    case = out.get("case") if isinstance(out.get("case"), dict) else {}
    ss.desk_routed = {"route": _word(out.get("route")), "answer": str(out.get("answer") or ""),
                      "note": str(out.get("note") or ""), "sections": sections, "chips": chips,
                      "kind": kind if kind in CASE_TYPES else None,
                      "drafted": case.get("status") == "draft" and bool(_case_path(case.get("case_id")))}
    if kind == "posh" and "posh" in offered_types(offer):
        ss["desk_kind"] = "posh"             # the POSH card at once: Raise a case draws its chooser after this
    elif ss.desk_routed["drafted"]:
        ss.desk_draft = {"view": case, "token": secrets.token_urlsafe(16)}
    return True


def _section(s: dict) -> None:
    """A desk's answer, as the Chat page shows a reply with citations; plainly when they cannot be drawn."""
    try:
        cited = [_as_source(c) for c in s["citations"]]
    except Exception:  # noqa: BLE001 - a citation the page cannot read is left out, never shown as a traceback
        cited = []
    if cited:
        try:
            render_with_citations(html.escape(s["answer"], quote=False), cited)
            return
        except Exception:  # noqa: BLE001 - shown plainly instead
            pass
    st.markdown(_md(s["answer"]))


def routed_reply(r: dict, offer: dict, tenant_id: str) -> None:
    """The last reply: the note, each desk's section (its citations, and the statute desk's in-force lines inside its
    text), or the code's own reply; then the chips it offers and the case it points to."""
    ss = st.session_state
    with st.container(border=True):
        if r.get("note"):
            st.caption(_md(r["note"]))
        sections = r.get("sections") or []
        for s in sections:
            if len(sections) > 1:
                st.markdown(f"**{_md(s['title'])}**")
            _section(s)
        if not sections:
            st.markdown(_md(r.get("answer")))
        if sections:
            st.caption("DocuMind's answer from your company's documents and the law it holds. If you need a person, "
                       "raise a case.")
        kind, types = r.get("kind"), offered_types(offer)
        if r.get("route") == "case" and kind and kind not in types:
            st.caption("Your company has not set up this kind of case here yet. Please contact the People team "
                       "directly.")
        elif r.get("route") == "case" and kind in START and not r.get("drafted"):
            if st.button(START[kind], key="desk_routed_start"):
                ss["desk_kind"] = kind       # before Raise a case draws its chooser
        for desk in r.get("chips") or []:
            if st.button(ROUTED_CHIPS[desk], key=f"desk_chip_{desk}"):
                if desk == "case" and not sections:
                    # a reply DocuMind did not keep (no search ran): the case starts here, with nothing typed in it
                    if "people_query" in types:
                        ss["desk_kind"] = "people_query"
                elif _ask({"chip": desk}, offer, tenant_id):
                    st.rerun()


# ---------------------------------------------------------------- the page
def desk_page(user):
    email = str(user.get("email") or "").strip().lower()
    try:
        tenant_id, checked = tenant_for(user["email"]), True
    except Exception:  # noqa: BLE001 - the roster could not be read: a plain line, never a traceback
        tenant_id, checked = None, False
    if not tenant_id:
        st.error("Your account is not a member of any DocuMind tenant. Ask an administrator to add you." if checked
                 else "Your account could not be checked just now. Please try again in a minute.")
        st.stop()
    ss = st.session_state
    if "desk_session" not in ss:
        ss.desk_session = uuid.uuid4().hex[:12]  # the Desk's own conversation, apart from the Chat page's
    st.title("DocuMind Desk")
    st.caption("Get help from a person at your company: the team your company or the law names for it.")
    flash = ss.pop("desk_flash", None)
    if flash:
        (st.success if flash[0] == "ok" else st.error)(flash[1])
    if not CHAT_URL:
        st.subheader("Raise a case")
        st.info("Raising a case needs the DocuMind chat service, and it is not set up here. "
                "Please contact the People team directly.")
        return
    s_offer, offer = _api("GET", "/v1/cases/offer")
    s_cases, got = _api("GET", "/v1/cases")
    offer = offer if s_offer == 200 and isinstance(offer, dict) else None
    got = got if s_cases == 200 and isinstance(got, dict) else None
    answered = [b for b in (offer, got) if b is not None]
    if any(not _seen_as(b, email, tenant_id) for b in answered):
        st.warning(SIGN_IN)                  # the service saw someone else: no case of theirs is drawn here
        return
    why = _problem(503 if s_offer == 200 else s_offer, "offer")   # why there is no offer (a 200 it could not read)
    if not answered:
        st.subheader("Raise a case")
        st.info(why)
        return
    if got is None or UNREAD in _roles(got) or UNREAD in _roles(offer):
        raise_section(offer, why)            # the roles could not be read: the case desk only (shared/roles.py)
        st.caption("Your cases could not be loaded just now. Please try again in a minute.")
        return
    roles, types = _roles(got), offered_types(offer)
    employee = offer is not None and EMPLOYEE in _roles(offer)
    if employee and offer.get("desk_route") in ROUTED_MODES:
        routed_half(tenant_id, offer)        # in place of Tell the Desk, and before Raise a case (workshop lesson 10.4)
    elif employee and offer.get("desk_gate") in ("rules", "on"):
        tell_section(types)
        reply_section(types)
    raise_section(offer, why)
    mine_section(got.get("mine"))
    if has_queue_role(roles):
        inbox_section(got.get("inbox"), email, roles)
    if got.get("more") is True:
        st.caption("Only the latest cases are shown here. Some older ones are not.")
