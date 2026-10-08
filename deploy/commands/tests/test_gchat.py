"""The Google Chat door (workshop lesson 10.4): the bridge, services/gchat/, and the Desk's side of it,
services/chat/delegation.py.

    python -m unittest commands/tests/test_gchat.py          (from deploy/)

The first half needs the standard library only and runs in CI's shared interpreter: both event shapes from
placeholder fixtures, the session id rule, the claim keys and the client- message id, render() for every Desk
outcome (under 30,000 bytes, the question never echoed, no gs:// URI or signed URL, every button calling SELF_URL with
no text), and the fixed replies. The second half needs the chat image's pins (FastAPI, google-auth): the bridge's
handlers with the token check, the queue, the claims and the Desk replaced by fakes, and delegation.principal() on
agent.py's real app. CI's chat-pins step runs it with DOCUMIND_REQUIRE_LIBS=1, so a missing pin fails rather than
skips. No test calls Google Chat, Pub/Sub, Firestore, a model or a network.

The fixtures are placeholders until the lane probe records real events; then they are rewritten from those, with every
email employee@example.com, every users/ and spaces/ id and message name a fixed placeholder, and the project number
NUMBER. A test fails on any email outside example.com and on any run of ten or more digits in them.
"""
from __future__ import annotations

import ast
import base64
import copy
import importlib.util
import json
import logging
import os
import re
import sys
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[2]
for p in (str(KIT / "services/gchat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import cards  # noqa: E402
import claims  # noqa: E402
import events  # noqa: E402
import post  # noqa: E402
import replies  # noqa: E402
from shared import cases, desk_law, desk_rules  # noqa: E402

FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("fastapi", "google.auth", "langgraph", "httpx"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
SELF_URL = "https://documind-gchat-NUMBER.us-central1.run.app"
PROJECT = "documind-ai-YOUR-ID"
CALLER = "service-NUMBER@gcp-sa-gsuiteaddons.iam.gserviceaccount.com"
PUSH = f"documind-gchatpush-sa@{PROJECT}.iam.gserviceaccount.com"
BRIDGE = f"documind-gchat-sa@{PROJECT}.iam.gserviceaccount.com"
EMPLOYEE = "employee@example.com"
POSH = "My manager keeps making sexual comments about my body. What can I do?"     # test_desk.py's, which fires posh
MISSED = "A senior colleague keeps standing too close and texting me late at night about my looks."   # the gate misses it
LEAVE = "How many days of earned leave can I carry forward?"
AADHAAR = "2345 6789 0124"
SPACE, THREAD, MESSAGE = "spaces/DMSPACE", "spaces/DMSPACE/threads/THREADA", "spaces/DMSPACE/messages/MESSAGEA"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


desk_ops = _load("desk_ops_for_gchat", KIT / "commands" / "desk_ops.py")
_TD = []


def test_desk():
    """commands/tests/test_desk.py's stand-ins (FakeDB, the service harness), loaded once under another name, so its
    own tests are not collected here."""
    if not _TD:
        _TD.append(_load("test_desk_for_gchat", KIT / "commands" / "tests" / "test_desk.py"))
    return _TD[0]


# ------------------------------------------------------------------ the fixtures (placeholders until the probe)
def addon_message(text=LEAVE, space=SPACE, space_type="DIRECT_MESSAGE", email=EMPLOYEE, sender_type="HUMAN",
                  attachment=False, name=MESSAGE) -> dict:
    message = {"name": name, "text": text, "argumentText": text, "thread": {"name": THREAD},
               "sender": {"name": "users/EMPLOYEE", "type": sender_type, **({"email": email} if email else {})}}
    if attachment:
        message["attachment"] = [{"name": f"{name}/attachments/ATTACHMENTA", "contentType": "image/png"}]
    return {"chat": {"user": {"name": "users/EMPLOYEE", "type": sender_type, **({"email": email} if email else {})},
                     "messagePayload": {"message": message, "space": {"name": space, "spaceType": space_type}}}}


def classic_message(text=LEAVE) -> dict:
    return {"type": "MESSAGE", "space": {"name": SPACE, "type": "DM"},
            "user": {"name": "users/EMPLOYEE", "type": "HUMAN", "email": EMPLOYEE},
            "message": {"name": MESSAGE, "text": text, "thread": {"name": THREAD},
                        "sender": {"name": "users/EMPLOYEE", "type": "HUMAN", "email": EMPLOYEE}},
            "common": {}}


def addon_press(params: dict, name="spaces/DMSPACE/messages/CARDA") -> dict:
    return {"commonEventObject": {"parameters": params},
            "chat": {"user": {"name": "users/EMPLOYEE", "type": "HUMAN", "email": EMPLOYEE},
                     "buttonClickedPayload": {"message": {"name": name, "thread": {"name": THREAD}},
                                              "space": {"name": SPACE, "spaceType": "DIRECT_MESSAGE"}}}}


def classic_press(params: dict) -> dict:
    return {"type": "CARD_CLICKED", "space": {"name": SPACE, "type": "DM"},
            "user": {"name": "users/EMPLOYEE", "type": "HUMAN", "email": EMPLOYEE},
            "message": {"name": "spaces/DMSPACE/messages/CARDA", "thread": {"name": THREAD}},
            "common": {"parameters": params}}


ADDED = {"chat": {"user": {"name": "users/EMPLOYEE", "type": "HUMAN", "email": EMPLOYEE},
                  "addedToSpacePayload": {"space": {"name": SPACE, "spaceType": "DIRECT_MESSAGE"}}}}
FIXTURES = [addon_message(), classic_message(), addon_press({"act": "chip", "chip": "statute", "sid": "x"}),
            classic_press({"act": "cancel"}), ADDED, addon_message(attachment=True)]


def sid(day="20261001") -> str:
    return events.session_id(SPACE, day)


# ------------------------------------------------------------------ the Desk's replies, one per outcome
def _cite(n, name="hr_policy_2026.md", quote="Up to 30 days of earned leave may be carried forward."):
    return {"n": n, "chunk_id": f"{name}-{n}", "source_uri": f"gs://documind-ai-YOUR-ID-uploads/acme/{name}",
            "page": n, "quote": quote, "score": 0.9}


def _section(desk, answer, cites, answerable=True, in_force=()):
    titles = {"handbook": "From the company handbook", "statute": "What the law says",
              "fallback": "From the documents you can read"}
    text = answer + ("\n\n" + "\n".join(in_force) if in_force else "")
    return {"desk": desk, "title": titles[desk], "answer": text, "answerable": answerable, "confidence": "high",
            "citations": cites, "in_force": list(in_force), "error": False}


def _reply(route, answer, sections=(), chips=(), case=None, offer=None, outcome="answer"):
    cites = [c for s in sections for c in s["citations"]]
    return {"email": EMPLOYEE, "tenant": "acme", "session_id": sid(), "mode": "on", "arm": "B", "route": route,
            "method": "model", "outcome": outcome, "answer": answer, "note": "", "sections": list(sections),
            "citations": cites, "chips": [{"desk": d, "label": label} for d, label in chips], "case": case,
            "case_offer": offer, "tool_calls": [], "retrieve_calls": len(sections), "model_calls": 1,
            "decision": {}, "latency_ms": 900, "limits": {}}


CHIPS = (("statute", "Ask what the law says"), ("case", "Raise a case"))
IN_FORCE = desk_law.in_force_lines(["code_on_wages_2019.md"])


def outcomes() -> dict:
    hb = _section("handbook", "Up to 30 days [1].", [_cite(1)])
    st = _section("statute", "Within two working days [1].", [_cite(1, "code_on_wages_2019.md", "paid within two working days")],
                  in_force=IN_FORCE)
    refusal = _section("handbook", "The documents this desk reads do not answer this.", [], answerable=False)
    fb = _section("fallback", "From the documents: 30 days [1].", [_cite(1)])
    queues = desk_ops._notes_off(json.loads((KIT / "evals" / "desk" / "queues.acme.json").read_text(encoding="utf-8")))
    posh = {"case_type": "posh", "configured": True, "posh": cases.posh_offer(queues), "clock": [desk_law.CLOCKS["posh"]],
            "basis": desk_law.basis_for("posh")}
    draft = {"case_id": "a" * 32, "case_type": "exit_dues", "status": "draft", "summary": "masked question here",
             "owner": {"queue_name": "Payroll", "contact": "payroll@example.com"}, "clock": ["two working days"],
             "basis": desk_law.basis_for("exit_dues"), "sensitive": False}
    return {
        "handbook": _reply("handbook", hb["answer"], [hb], CHIPS),
        "statute": _reply("statute", st["answer"], [st], (("case", "Raise a case"),)),
        "clarify": _reply("clarify", "Should I answer this from the company handbook or from the law?", (),
                          (("handbook", "Ask what the company handbook says"), ("statute", "Ask what the law says")),
                          outcome="clarify"),
        "out_of_scope": _reply("out_of_scope", "DocuMind cannot do things in other systems.", (),
                               (("case", "Raise a case"),), outcome="oos"),
        "not_covered": _reply("not_covered", "This company has no documents for the law yet.", (),
                              (("case", "Raise a case"),), outcome="not_covered"),
        "denied": _reply("denied", "Your roles in this company do not include asking the law.", (),
                         (("case", "Raise a case"),), outcome="denied"),
        "grounded_refusal": _reply("handbook", refusal["answer"], [refusal], CHIPS, outcome="grounded_refusal"),
        "case_draft": _reply("case", desk_law.template("exit_dues"), (), (), case=draft, offer={"case_type": "exit_dues"},
                             outcome="case"),
        "posh": _reply("case", desk_law.template("posh"), (), (), case=None, offer=posh, outcome="case"),
        "fallback": _reply("fallback", fb["answer"], [fb], CHIPS),
        "draft_open": _reply("case", "You have a case draft open.", (), (), case={"draft_open": "b" * 32}, outcome="case"),
    }


def huge() -> dict:
    cites = [_cite(i, quote="q" * 5000 + " gs://bucket/secret.pdf") for i in range(1, 60)]
    sec = _section("statute", "word " * 8000 + "https://storage.googleapis.com/b/o?X-Goog-Signature=abc", cites,
                   in_force=IN_FORCE)
    return _reply("statute", sec["answer"], [sec], CHIPS)


def buttons(obj) -> list:
    out = []
    if isinstance(obj, dict):
        if "onClick" in obj:
            out.append(obj)
        for v in obj.values():
            out += buttons(v)
    elif isinstance(obj, list):
        for v in obj:
            out += buttons(v)
    return out


PARAM_KEYS = {"act", "chip", "sid", "case", "unit", "cls", "m"}


# ================================================================== the standard-library half
class FixtureTests(unittest.TestCase):
    def test_the_bridge_and_the_desk_read_one_address_alike(self):
        src = (KIT / "services" / "chat" / "delegation.py").read_text(encoding="utf-8")
        (pattern,) = re.findall(r'^PERSON = re\.compile\(r"(.*)"\)$', src, re.M)
        self.assertEqual(events.PERSON.pattern, pattern)
        for email, ok in (("you@example.com", True), ("o'neil@example.com", True), ("You@example.com", False),
                          ("a@b", False), ("you@example.com:x", False), ("x@p.iam.gserviceaccount.com", False)):
            self.assertEqual(events.is_person(email), ok, email)

    def test_the_fixtures_hold_only_placeholders(self):
        text = json.dumps(FIXTURES)
        for email in re.findall(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+)", text):
            self.assertEqual(email, "example.com")
        self.assertIsNone(re.search(r"\d{10,}", text))


class EventTests(unittest.TestCase):
    def test_both_shapes_read_the_same(self):
        a, c = events.normalise(addon_message()), events.normalise(classic_message())
        for ev, shape, field in ((a, "addon", "spaceType"), (c, "classic", "type")):
            self.assertEqual((ev["shape"], ev["kind"], ev["message_name"], ev["space_name"], ev["dm"], ev["space_field"],
                              ev["thread_name"], ev["sender_type"], ev["sender_email"], ev["text"], ev["has_attachment"]),
                             (shape, "message", MESSAGE, SPACE, True, field, THREAD, "HUMAN", EMPLOYEE, LEAVE, False))

    def test_presses_added_and_others(self):
        for body, src in ((addon_press({"act": "chip", "chip": "statute", "sid": sid()}), "commonEventObject.parameters"),
                          (classic_press({"act": "chip", "chip": "statute", "sid": sid()}), "common.parameters")):
            ev = events.normalise(body)
            self.assertEqual((ev["kind"], ev["action"], ev["parameters"]["chip"], ev["params_from"], ev["dm"]),
                             ("press", "chip", "statute", src, True))
        listed = events.normalise({**addon_press({}),
                                   "commonEventObject": {"parameters": [{"key": "act", "value": "cancel"}]}})
        self.assertEqual(listed["action"], "cancel")
        self.assertEqual(events.normalise(ADDED)["kind"], "added")
        for other in ({}, {"type": "REMOVED_FROM_SPACE"}, {"chat": {}}, [], "x", {"type": "MESSAGE", "message": {}}):
            self.assertEqual(events.normalise(other)["kind"], "other", other)

    def test_a_space_that_does_not_say_direct_message_is_a_named_space(self):
        self.assertFalse(events.normalise(addon_message(space_type="SPACE"))["dm"])
        body = addon_message()
        del body["chat"]["messagePayload"]["space"]["spaceType"]
        self.assertEqual((events.normalise(body)["dm"], events.normalise(body)["space_field"]), (False, None))
        self.assertTrue(events.normalise(addon_message(attachment=True))["has_attachment"])
        self.assertIsNone(events.normalise(addon_message(email=None))["sender_email"])
        self.assertEqual(events.normalise(addon_message(email="Employee@Example.com"))["sender_email"], EMPLOYEE)

    def test_the_session_id(self):
        s = sid()
        self.assertEqual(len(s), 36)
        self.assertRegex(s, r"^[A-Za-z0-9_-]{1,64}$")
        self.assertNotIn(":", s)
        self.assertNotIn("/", s)
        self.assertNotEqual(s, sid("20261002"))
        self.assertNotEqual(s, events.session_id("spaces/OTHER", "20261001"))
        self.assertTrue(events.session_of_space(s, SPACE))
        self.assertTrue(events.session_of_space(sid("20260101"), SPACE))
        self.assertFalse(events.session_of_space(events.session_id("spaces/OTHER", "20261001"), SPACE))
        self.assertFalse(events.session_of_space("gc-x", SPACE))
        from datetime import datetime, timezone
        self.assertEqual(events.today_ist(datetime(2026, 9, 30, 19, 0, tzinfo=timezone.utc)), "20261001")  # 00:30 IST
        with self.assertRaises(ValueError):
            events.session_id("", "20261001")

    def test_the_keys_and_the_client_id(self):
        key = events.event_key(MESSAGE)
        self.assertRegex(key, r"^[0-9a-f]{64}$")
        cid = events.client_id(key)
        self.assertEqual(len(cid), 63)
        self.assertRegex(cid, r"^client-[0-9a-f]{56}$")
        self.assertEqual(cid, events.client_id(events.event_key(MESSAGE)))         # one question, one id
        self.assertNotEqual(cid, events.client_id(events.event_key(MESSAGE + "B")))
        p1 = events.press_key("m", "confirm", {"case": "a" * 32, "sid": "s"})
        self.assertEqual(p1, events.press_key("m", "confirm", {"sid": "s", "case": "a" * 32}))
        self.assertNotEqual(p1, events.press_key("m", "cancel", {"case": "a" * 32, "sid": "s"}))
        self.assertNotEqual(p1, key)
        tok = events.token("m", "confirm", {"case": "a" * 32})
        self.assertRegex(tok, r"^[A-Za-z0-9_-]{8,128}$")
        self.assertTrue(cases.TOKEN.match(tok))
        with self.assertRaises(ValueError):
            events.client_id("not a key")


class CardTests(unittest.TestCase):
    def check(self, name, msg, question=None):
        raw = json.dumps(msg, ensure_ascii=False)
        self.assertLess(len(raw.encode("utf-8")), cards.LIMIT_BYTES, name)
        self.assertNotIn("gs://", raw, name)
        self.assertNotIn("X-Goog-Signature", raw, name)
        if question:
            self.assertNotIn(question, raw, name)
        for b in buttons(msg):
            action = b["onClick"]["action"]
            self.assertEqual(action["function"], SELF_URL, name)
            for p in action["parameters"]:
                self.assertIn(p["key"], PARAM_KEYS, name)
                self.assertRegex(p["value"], r"^[A-Za-z0-9_-]{1,64}$", name)

    def test_every_outcome(self):
        for name, reply in outcomes().items():
            msg = cards.render(reply, SELF_URL, sid())
            self.check(name, msg, question="masked question here")
            self.assertIn("cardsV2", msg, name)

    def test_what_each_card_says(self):
        got = {k: cards.render(v, SELF_URL, sid()) for k, v in outcomes().items()}
        head = {k: m["cardsV2"][0]["card"]["header"] for k, m in got.items()}
        self.assertEqual(head["handbook"], {"title": "HR Desk", "subtitle": "From your company handbook"})
        self.assertEqual(head["statute"], {"title": "HR Desk", "subtitle": "What the law says"})
        self.assertEqual(head["case_draft"]["title"], "Handed to a person")
        raw = json.dumps(got["statute"])
        for line in IN_FORCE:                                     # the in-force line, whole, in its own paragraph
            self.assertIn(json.dumps({"textParagraph": {"text": line}}), raw)
        acts = lambda m: [(p["key"], p["value"]) for b in buttons(m) for p in b["onClick"]["action"]["parameters"]]
        self.assertEqual([v for k, v in acts(got["handbook"]) if k == "chip"], ["statute", "case"])   # the case desk last
        self.assertEqual([v for k, v in acts(got["clarify"]) if k == "chip"], ["handbook", "statute"])
        self.assertEqual([v for k, v in acts(got["case_draft"]) if k == "act"], ["confirm", "cancel"])
        self.assertIn(cards.EDIT_ON_PAGE, json.dumps(got["case_draft"]))
        posh = json.dumps(got["posh"])
        self.assertIn(json.dumps(cards.POSH_PRIVACY)[1:-1], posh)
        offices = [x for x in got["posh"]["cardsV2"][0]["card"]["sections"] if x.get("header")]
        self.assertEqual(len(offices), len(outcomes()["posh"]["case_offer"]["posh"]))
        for office in offices:                  # before the press: it sends the case to every member listed above
            *_, line, press = office["widgets"]
            self.assertEqual((line, press["buttonList"]["buttons"][0]["text"]),
                             ({"textParagraph": {"text": cards.esc(cards.POSH_MEMBERS)}}, cards.POSH_BUTTON))
        self.assertEqual(posh.count(json.dumps(cards.POSH_MEMBERS)[1:-1]), len(offices))
        self.assertIn("every Internal Committee member listed above", cards.POSH_MEMBERS)
        self.assertIn("Desk page", cards.POSH_MEMBERS)
        self.assertEqual(sorted(v for k, v in acts(got["posh"]) if k == "unit"),
                         sorted(outcomes()["posh"]["case_offer"]["posh"]))       # one press per office
        self.assertEqual({v for k, v in acts(got["posh"]) if k == "act"}, {"posh"})
        units = outcomes()["posh"]["case_offer"]["posh"]
        for b in buttons(got["posh"]):                  # each press carries the digest of the members its card listed
            p = {x["key"]: x["value"] for x in b["onClick"]["action"]["parameters"]}
            self.assertEqual(p["m"], cards.members_digest(m["email"] for m in units[p["unit"]]["members"]))
        for para in desk_law.template("posh").split("\n\n"):     # the Desk's template, word for word
            self.assertIn(json.dumps({"textParagraph": {"text": cards.esc(para)}}), posh)
        self.assertEqual(buttons(got["draft_open"]), [])

    def test_the_cap_and_the_links(self):
        msg = cards.render(huge(), SELF_URL, sid())
        self.check("huge", msg)
        raw = json.dumps(msg)
        for line in IN_FORCE:
            self.assertIn(line, raw)
        self.assertLessEqual(raw.count("decoratedText"), cards.CITES_MAX)
        self.assertEqual(cards.sanitise("see gs://b/o.pdf and https://storage.googleapis.com/b/o and "
                                        "https://example.com/x?sig=1 and https://example.com/page"),
                         "see [document] and [link removed] and [link removed] and https://example.com/page")
        self.assertEqual(cards.esc("<b>&"), "&lt;b&gt;&amp;")
        unconfigured = dict(outcomes()["posh"], case_offer={"case_type": "posh", "configured": False, "posh": None})
        msg = cards.render(unconfigured, SELF_URL, sid())
        self.assertEqual(buttons(msg), [])
        self.assertIn(json.dumps(cards.POSH_PRIVACY)[1:-1], json.dumps(msg))
        many = copy.deepcopy(outcomes()["posh"])
        unit = next(iter(many["case_offer"]["posh"].values()))
        many["case_offer"]["posh"] = {f"office{i}": unit for i in range(400)}
        msg = cards.render(many, SELF_URL, sid())
        self.check("many offices", msg)
        self.assertIn(json.dumps(cards.POSH_TOO_MANY)[1:-1], json.dumps(msg))

    def test_the_fixed_card_and_the_fifth_attempt(self):
        msg = cards.fixed_card(desk_law.template("posh"), SELF_URL, sid(), "posh")
        self.check("fixed", msg)
        (b,) = buttons(msg)
        self.assertEqual((b["text"], {p["key"]: p["value"] for p in b["onClick"]["action"]["parameters"]}),
                         (cards.SHOW_OPTIONS, {"act": "options", "cls": "posh", "sid": sid()}))
        self.assertEqual(buttons(cards.fixed_card(desk_law.template("posh"), SELF_URL, None, None, replies.DM_ONLY)), [])
        self.assertEqual(replies.text(replies.UNREACHABLE), {"text": replies.UNREACHABLE})
        self.assertIn("could not reach the HR Desk", replies.UNREACHABLE)


class ReplyTests(unittest.TestCase):
    def test_the_desk_denials_are_the_desks_words(self):
        src = (KIT / "services" / "chat" / "delegation.py").read_text(encoding="utf-8")
        consts = {n.targets[0].id: n.value.value for n in ast.parse(src).body
                  if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.targets[0], ast.Name)}
        self.assertEqual(replies.DESK_NOT_A_MEMBER, consts["NOT_A_MEMBER"])
        self.assertEqual(replies.DESK_DOOR_OFF, consts["DOOR_OFF"])
        desk_src = (KIT / "services" / "chat" / "desk.py").read_text(encoding="utf-8")
        desk_consts = {n.targets[0].id: n.value.value for n in ast.parse(desk_src).body
                       if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
                       and isinstance(n.targets[0], ast.Name)}
        self.assertEqual(desk_consts["NOT_A_MEMBER"], consts["NOT_A_MEMBER"])     # the roster's 403, from either side
        self.assertEqual(replies.for_denial(consts["NOT_A_MEMBER"]), replies.NOT_ON_ROSTER)
        self.assertEqual(replies.for_denial(consts["DOOR_OFF"]), replies.DOOR_OFF)
        self.assertIsNone(replies.for_denial("anything else"))

    def test_the_wrapper(self):
        m = replies.text("x")
        self.assertEqual(replies.wrap(m, "addon"),
                         {"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": m}}}})
        self.assertEqual(replies.wrap(m, "classic"), m)
        self.assertEqual(replies.welcome()["cardsV2"][0]["card"]["header"]["title"], "HR Desk")

    def test_no_fixed_reply_writes_law(self):
        for name in ("ACK", "NOT_ON_ROSTER", "DOOR_OFF", "DM_ONLY", "TYPED_ONLY", "TOO_LONG", "RATE_LIMITED",
                     "NO_ACCOUNT", "UNREACHABLE", "WELCOME"):
            text = getattr(replies, name)
            self.assertNotRegex(text, r"(?i)\bAct\b|section \d|Internal Committee|Code on")


class PostTests(unittest.TestCase):
    """post.py with a stand-in session: the request it makes, never a network."""

    class Session:
        def __init__(self, *statuses):
            self.statuses, self.calls = list(statuses), []

        def post(self, url, params=None, json=None, timeout=None):
            self.calls.append({"url": url, "params": params, "json": json})
            status = self.statuses.pop(0)
            return type("R", (), {"status_code": status, "json": lambda self: {"messageIds": ["1"]}})()

    def test_create_and_publish(self):
        s = self.Session(200)
        key = events.event_key(MESSAGE)
        got = post.create(SPACE, THREAD, events.client_id(key), {"text": "x"}, session_for=lambda scopes: s)
        self.assertEqual(got, "posted")
        (call,) = s.calls
        self.assertEqual(call["url"], f"https://chat.googleapis.com/v1/{SPACE}/messages")
        self.assertEqual(call["params"], {"messageId": events.client_id(key),
                                          "messageReplyOption": "REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"})
        self.assertEqual(call["json"], {"text": "x", "thread": {"name": THREAD}})
        self.assertEqual(post.create(SPACE, None, events.client_id(key), {"text": "x"},
                                     session_for=lambda scopes: self.Session(post.DUPLICATE_STATUS)), "duplicate")
        for status, retry in ((429, True), (503, True), (400, False)):
            with self.assertRaises(post.PostError) as e:
                post.create(SPACE, THREAD, events.client_id(key), {"text": "x"}, session_for=lambda scopes: self.Session(status))
            self.assertEqual((e.exception.status, e.exception.retry), (status, retry))
        with self.assertRaises(post.PostError):
            post.create("spaces/A/../B", THREAD, events.client_id(key), {}, session_for=lambda scopes: s)
        p, lane = self.Session(200), PROJECT.lower()               # a project id is lower-case
        post.publish(lane, {"key": key, "question": "x"}, session=p)
        self.assertEqual(p.calls[0]["url"], f"https://pubsub.googleapis.com/v1/projects/{lane}/topics/documind-gchat-work:publish")
        data = json.loads(base64.b64decode(p.calls[0]["json"]["messages"][0]["data"]))
        self.assertEqual(data, {"key": key, "question": "x"})
        with self.assertRaises(post.PostError):
            post.publish(lane, {}, session=self.Session(403))
        with self.assertRaises(post.PostError):
            post.publish(PROJECT, {}, session=p)                    # not a project id: nothing is sent
        self.assertEqual(len(p.calls), 1)

    def test_no_way_to_post_is_not_retried(self):
        key = events.event_key(MESSAGE)

        class RefreshError(Exception):                      # google.auth.exceptions.RefreshError, by its name
            pass

        def refused(scopes):
            return self.Session(403)

        def no_token(scopes):
            raise RefreshError("no token")

        def no_account(scopes):
            raise post.PostError(0, False)                   # _self() with no service account to impersonate

        def no_answer(scopes):
            raise ConnectionError("reset")

        for adc, own, want in ((refused, no_token, (403, False, True)), (refused, refused, (403, False, True)),
                               (no_token, no_account, (403, False, True)), (refused, no_answer, (403, True, False)),
                               (no_answer, no_token, (0, True, False))):
            with patch.object(post, "_adc", adc), patch.object(post, "_self", own), \
                    patch.dict(post.AUTH_USED, {"how": None}):
                with self.assertRaises(post.PostError) as e:
                    post.create(SPACE, THREAD, events.client_id(key), {"text": "x"})
                self.assertEqual((e.exception.status, e.exception.retry, e.exception.auth), want,
                                 (adc.__name__, own.__name__))
                self.assertEqual(post.AUTH_USED["how"], "failed")


class FakeFirestore:
    """The calls claims.py makes and no more: collection().document() refs, get(transaction=) snapshots, set through
    a transaction, update and delete. update on a missing document raises, as Firestore's NotFound does. Paired with
    claims._transactional replaced by run_once: one attempt, no contention."""

    class Ref:
        def __init__(self, db, path):
            self.db, self.path = db, path

        def get(self, transaction=None):
            data = self.db.docs.get(self.path)
            return type("Snap", (), {"exists": data is not None, "to_dict": lambda _s: dict(data or {})})()

        def update(self, fields):
            if self.path not in self.db.docs:
                raise KeyError(f"no document {self.path}")
            self.db.docs[self.path] = {**self.db.docs[self.path], **fields}

        def delete(self):
            self.db.docs.pop(self.path, None)

    def __init__(self):
        self.docs = {}

    def collection(self, name):
        db = self
        return type("Col", (), {"document": lambda _c, key: FakeFirestore.Ref(db, f"{name}/{key}")})()

    def transaction(self):
        db = self
        return type("Tx", (), {"set": lambda _t, ref, data: db.docs.__setitem__(ref.path, dict(data))})()


def run_once(fn):
    return lambda tx: fn(tx)


class ClaimsTests(unittest.TestCase):
    """claims.py itself, the replay defence: take, queued, drop, lease, release and answered on a stand-in store."""

    FIELDS = {"kind", "state", "attempts", "created_at", "leased_at", "expire_at"}

    def setUp(self):
        from datetime import datetime, timedelta, timezone
        self.td = timedelta
        self.t = [datetime(2026, 10, 1, 4, 30, tzinfo=timezone.utc)]
        self.db = FakeFirestore()
        for p in (patch.object(claims, "_now", lambda: self.t[0]), patch.object(claims, "_transactional", run_once),
                  patch.object(claims, "_client", self.db)):
            p.start()
            self.addCleanup(p.stop)

    def later(self, seconds):
        self.t[0] = self.t[0] + self.td(seconds=seconds)

    def doc(self, key):
        return self.db.docs[f"{claims.COLLECTION}/{key}"]

    def test_take_retakes_only_a_stale_received_claim(self):
        k, t0 = "a" * 64, self.t[0]
        self.assertTrue(claims.take(k, "message"))
        self.assertEqual(self.doc(k), {"kind": "message", "state": "received", "attempts": 0, "created_at": t0,
                                       "leased_at": None, "expire_at": t0 + claims.TTL})
        self.later(claims.RETAKE_S - 1)
        self.assertFalse(claims.take(k, "message"))           # a delivery while the first is still working
        self.later(2)
        self.assertTrue(claims.take(k, "message"))            # the request that wrote it died: taken back
        self.assertEqual(self.doc(k)["created_at"], self.t[0])
        claims.queued(k)
        self.later(3600)
        self.assertFalse(claims.take(k, "message"))           # a queued claim is never taken back
        claims.drop(k)
        self.assertTrue(claims.take(k, "message"))

    def test_lease_counts_attempts_across_release_and_takes_back_a_stale_lease(self):
        k, t0 = "b" * 64, self.t[0]
        claims.take(k, "press")
        claims.queued(k)
        self.assertEqual(claims.lease(k), ("working", 1))
        self.later(10)
        self.assertEqual(claims.lease(k), ("busy", 1))        # another delivery holds it
        claims.release(k)
        self.assertEqual((self.doc(k)["state"], self.doc(k)["attempts"], self.doc(k)["leased_at"]), ("queued", 1, None))
        self.assertEqual(claims.lease(k), ("working", 2))
        self.later(claims.LEASE_S + 1)
        self.assertEqual(claims.lease(k), ("working", 3))     # the worker that leased it died: taken back, counted
        claims.answered(k)
        self.later(60)
        self.assertEqual(claims.lease(k), ("answered", 3))
        d = self.doc(k)
        self.assertEqual((d["kind"], d["created_at"], d["expire_at"]), ("press", t0, t0 + claims.TTL))
        self.assertEqual(claims.lease("c" * 64), ("working", 1))      # a push whose claim expired: a new one
        self.assertEqual(self.doc("c" * 64)["expire_at"], self.t[0] + claims.TTL)
        for doc in self.db.docs.values():
            self.assertEqual(set(doc), self.FIELDS)

    def test_the_database_is_the_bridges_own(self):
        self.assertEqual((claims.DATABASE, claims.COLLECTION), ("documind-gchat", "gchat_events"))


class WiringTests(unittest.TestCase):
    def read(self, *parts) -> str:
        return (KIT.joinpath(*parts)).read_text(encoding="utf-8")

    def test_ci_and_make_run_these_tests(self):
        self.assertIn("commands/tests/test_gchat.py", self.read("commands", "desk-check.sh"))
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_gchat.py -v"
        self.assertIn(line, self.read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = KIT.parent / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                            # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))
        mk, agents = self.read("Makefile"), self.read("mk", "agents.mk")
        phony = mk[mk.index(".PHONY:"):].split("\n\n", 1)[0]
        for target in ("deploy-gchat", "smoke-gchat"):                  # each refuses on a lane without the door
            self.assertIn(f" {target}", phony)
            self.assertIn(f"\n{target}: guard-project tf-backend\n\t@$(GCHAT_DOOR_ON)\n", agents)
        self.assertIn('GCHAT_DOOR_ON = [ "$$(cd $(TF_DIR) && terraform output -raw gchat_door 2>/dev/null)" = true ] ||', agents)
        self.assertIn("GCHAT_DOOR ?= false\nTF_EXTRA_VARS += -var gchat_door=$(GCHAT_DOOR)\n", agents)
        self.assertIn("$(MAKE) build deploy-services SERVICES=gchat SCRIPTS=commands/gchat.sh", agents)
        self.assertIn("$(if $(DESK_GCHAT),--gchat $(DESK_GCHAT),) $(if $(CONFIRM_RESIDENCY),--confirm-residency,)", agents)
        smoke_all = mk.split("\nsmoke-all:", 1)[1].split("\n\n", 1)[0]
        self.assertNotIn("gchat", smoke_all)                              # a default lane has no bridge
        self.assertIn("documind-gchat", re.search(r"^DOWN_SERVICES\s*=(.*)$", mk, re.M).group(1))

    def test_the_bridge_pins_are_the_chat_services(self):
        def pins(path):
            return dict(ln.split("==", 1) for ln in self.read(*path).splitlines() if "==" in ln and not ln.startswith("#"))
        bridge, chat = pins(("services", "gchat", "requirements.txt")), pins(("services", "chat", "requirements.txt"))
        self.assertEqual(set(bridge), {"fastapi", "uvicorn", "gunicorn", "pydantic", "requests", "google-auth",
                                       "google-cloud-firestore"})
        self.assertEqual({k: chat[k] for k in bridge}, bridge)

    def test_the_bridge_imports_only_what_it_needs(self):
        src = "".join(self.read("services", "gchat", f) for f in ("main.py", "events.py", "cards.py", "replies.py",
                                                                  "claims.py", "post.py"))
        shared = set(re.findall(r"^from shared import (.+)$", src, re.M))
        self.assertEqual(shared, {"desk_law, desk_rules, iap"})
        for banned in ("documind_tools", "tenancy", "genai", "psycopg", "iap.identity(", "RAG_API_URL"):
            self.assertNotIn(banned, src)


# ================================================================== the library half
class _Log:
    def __init__(self):
        self.raw, self.rows = [], []

    def _keep(self, msg, *a, **k):
        self.raw.append(str(msg))
        try:
            self.rows.append(json.loads(msg))
        except ValueError:
            pass

    info = warning = error = _keep


class FakeClaims:
    def __init__(self):
        self.docs = {}

    def take(self, key, kind):
        if key in self.docs:
            return False
        self.docs[key] = {"kind": kind, "state": "received", "attempts": 0}
        return True

    def queued(self, key):
        self.docs[key]["state"] = "queued"

    def drop(self, key):
        self.docs.pop(key, None)

    def lease(self, key, kind="message"):
        rec = self.docs.setdefault(key, {"kind": kind, "state": "queued", "attempts": 0})
        if rec["state"] == "answered":
            return "answered", rec["attempts"]
        rec["attempts"] += 1
        rec["state"] = "working"
        return "working", rec["attempts"]

    def answered(self, key):
        self.docs.setdefault(key, {"attempts": 0})["state"] = "answered"

    def release(self, key):
        self.docs[key]["state"] = "queued"


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class BridgeTests(unittest.TestCase):
    """services/gchat/main.py's handlers, with the token check, the queue, the claims and the Desk replaced."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        env = {"SELF_URL": SELF_URL, "CHAT_URL": "https://documind-chat-NUMBER.us-central1.run.app",
               "GCHAT_CALLER": CALLER, "GOOGLE_CLOUD_PROJECT": PROJECT}
        with patch.dict(os.environ, env):
            cls.main = _load("gchat_main_under_test", KIT / "services" / "gchat" / "main.py")

    def setUp(self):
        m = self.main
        self.claims, self.published, self.posts, self.calls, self.log = FakeClaims(), [], [], [], _Log()
        self.answers = {}                   # (method, path) -> a reply, or a DeskError to raise

        def desk(method, path, email, body=None, timeout=0):
            self.calls.append({"method": method, "path": path, "email": email, "body": body, "timeout": timeout})
            got = self.answers.get((method, path.split("?")[0]))
            if isinstance(got, Exception):
                raise got
            if got is None:
                return {"email": email, "tenant": "acme", "via": "gchat"}
            return copy.deepcopy(got)

        def bearer_email(headers, audience):
            self.assertEqual(audience, SELF_URL)
            auth = headers.get("authorization") or ""
            if not auth.startswith("Bearer id:"):
                raise m.iap.IapError("invalid bearer token: ValueError")
            return auth[len("Bearer id:"):].lower()                      # as shared/iap.bearer_email returns it

        def publish(project, payload):
            self.published.append(payload)
            return "1"

        def create(space, thread, message_id, message):
            self.posts.append({"space": space, "thread": thread, "id": message_id, "message": message})
            return "posted"

        for p in (patch.object(m, "desk", desk), patch.object(m.iap, "bearer_email", bearer_email),
                  patch.object(m, "claims", self.claims), patch.object(m.post, "publish", publish),
                  patch.object(m.post, "create", create), patch.object(m, "log", self.log),
                  patch.object(m, "_PROBED", set()), patch.object(m, "_RATE", {})):
            p.start()
            self.addCleanup(p.stop)

    def event(self, body, caller=CALLER):
        r = self.main.handle_event({"authorization": f"Bearer id:{caller}"} if caller else {}, json.dumps(body).encode())
        return r.status_code, json.loads(r.body or b"{}")

    def work(self, payload, caller=PUSH, subscription=f"projects/{PROJECT}/subscriptions/documind-gchat-push"):
        env = {"message": {"data": base64.b64encode(json.dumps(payload).encode()).decode(), "messageId": "1"},
               "subscription": subscription}
        r = self.main.handle_work({"authorization": f"Bearer id:{caller}"}, json.dumps(env).encode())
        return r.status_code

    def message_of(self, body) -> dict:
        return body["hostAppDataAction"]["chatDataAction"]["createMessageAction"]["message"]

    def rows(self, event="gchat"):
        return [r for r in self.log.rows if r.get("event") == event]

    def no_text_logged(self, *texts):
        for t in texts:
            self.assertFalse(any(t in raw for raw in self.log.raw), t[:40])

    def posh_answer(self):
        return outcomes()["posh"]

    # -------------------------------------------------------------- the token, first
    def test_only_the_right_caller_reaches_each_path(self):
        for caller in (None, PUSH, BRIDGE, "documind-outsider-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
                       "chat@system.gserviceaccount.com"):
            status, body = self.event(addon_message(POSH), caller=caller)
            self.assertEqual(status, 401, caller)
        for caller in (CALLER, BRIDGE, "documind-outsider-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com"):
            self.assertEqual(self.work({"key": "0" * 64}, caller=caller), 401, caller)
        self.assertEqual((self.calls, self.published, self.posts), ([], [], []))
        failed = self.rows("gchat_verify_failed")
        self.assertEqual(len(failed), 8)
        self.assertEqual({r["reason"] for r in failed}, {"no_token", "wrong_caller"})
        self.assertTrue(all(set(r) == {"event", "path", "reason", "aud_is_self_url", "aud_has_trailing_slash",
                                       "email_is_gchat_caller", "email_is_chat_system", "iss_is_google"} for r in failed))
        self.no_text_logged("id:", POSH)

    def test_a_refused_token_row_reads_the_claims_and_never_logs_the_token(self):
        claims_ = base64.urlsafe_b64encode(json.dumps({"aud": SELF_URL + "/", "email": "chat@system.gserviceaccount.com",
                                                        "iss": "https://accounts.google.com"}).encode()).decode().rstrip("=")
        tok = f"e30.{claims_}.c2ln"
        r = self.main.handle_event({"authorization": f"Bearer {tok}"}, b"{}")
        self.assertEqual(r.status_code, 401)
        (row,) = self.rows("gchat_verify_failed")
        self.assertEqual((row["reason"], row["aud_is_self_url"], row["aud_has_trailing_slash"], row["email_is_chat_system"],
                          row["iss_is_google"], row["email_is_gchat_caller"]), ("invalid_token", False, True, True, True, False))
        self.no_text_logged(tok, claims_)

    # -------------------------------------------------------------- the gate, before everything
    def test_a_posh_disclosure_is_answered_now_and_never_queued(self):
        self.answers[("POST", "/v1/desk")] = self.posh_answer()
        status, body = self.event(addon_message(POSH))
        self.assertEqual(status, 200)
        (call,) = self.calls
        self.assertEqual((call["method"], call["path"], call["email"], call["body"], call["timeout"]),
                         ("POST", "/v1/desk", EMPLOYEE, {"question": POSH, "session_id": sid_today(self.main)},
                          self.main.GATE_BUDGET_S))
        self.assertEqual((self.published, self.claims.docs, self.posts), ([], {}, []))
        self.assertIn(json.dumps(cards.POSH_PRIVACY)[1:-1], json.dumps(self.message_of(body)))
        (row,) = self.rows()
        self.assertEqual((row["user"], row["class"], row["queued"], row["outcome"]), (None, "sensitive", False, "gate"))
        self.no_text_logged(POSH, "sexual")

    def test_the_gate_holds_whatever_the_space_attachment_length_or_rate(self):
        self.answers[("POST", "/v1/desk")] = self.posh_answer()
        _, body = self.event(addon_message(POSH, attachment=True))
        self.assertIn("posh", json.dumps(self.message_of(body)))
        for i in range(self.main.RATE_PER_MIN):                 # the sender's minute is used up by other questions
            self.event(addon_message(f"{LEAVE} {i}", name=f"{MESSAGE}{i}"))
        self.assertEqual(self.event(addon_message(LEAVE, name=MESSAGE + "X"))[1], self.main.replies.wrap(
            replies.text(replies.RATE_LIMITED), "addon"))
        n_pub, n_calls = len(self.published), len(self.calls)
        _, body = self.event(addon_message(POSH, name=MESSAGE + "P"))
        self.assertEqual(len(self.published), n_pub)
        self.assertEqual(self.calls[-1]["path"], "/v1/desk")
        _, body = self.event(addon_message(POSH, space="spaces/NAMED", space_type="SPACE"))      # a named space
        msg = json.dumps(self.message_of(body))
        self.assertIn(json.dumps(replies.DM_ONLY)[1:-1], msg)
        self.assertEqual(buttons(self.message_of(body)), [])
        _, body = self.event(addon_message(POSH + " " + "x" * 4000))                           # over the cap
        (b,) = buttons(self.message_of(body))
        self.assertEqual(b["text"], cards.SHOW_OPTIONS)
        _, body = self.event(addon_message(POSH, email=None))                                  # no email
        self.assertEqual(buttons(self.message_of(body)), [])
        self.assertEqual(len(self.calls), n_calls + 1)            # the space, the cap and the missing email: no Desk call
        self.assertEqual(len(self.published), n_pub)
        self.assertTrue(all(r["user"] is None and r["class"] == "sensitive" for r in self.rows() if r["class"]))
        self.no_text_logged(POSH, "sexual")

    def test_a_slow_desk_still_gets_the_fixed_text(self):
        self.answers[("POST", "/v1/desk")] = self.main.DeskError(0)
        _, body = self.event(addon_message(POSH))
        msg = self.message_of(body)
        for para in desk_law.template("posh").split("\n\n"):
            self.assertIn(cards.esc(para), json.dumps(msg, ensure_ascii=False))
        (b,) = buttons(msg)
        self.assertEqual({p["key"]: p["value"] for p in b["onClick"]["action"]["parameters"]},
                         {"act": "options", "cls": "posh", "sid": sid_today(self.main)})
        self.answers[("POST", "/v1/desk")] = self.main.DeskError(403, replies.DESK_NOT_A_MEMBER)
        _, body = self.event(addon_message(POSH, name=MESSAGE + "2"))
        self.assertIn(json.dumps(replies.NOT_ON_ROSTER)[1:-1], json.dumps(self.message_of(body)))
        self.assertEqual(buttons(self.message_of(body)), [])
        self.assertEqual(self.published, [])

    # -------------------------------------------------------------- a question, queued
    def test_a_question_is_claimed_checked_masked_queued_and_acknowledged(self):
        status, body = self.event(addon_message(f"My Aadhaar is {AADHAAR}. {LEAVE}"))
        self.assertEqual((status, body), (200, replies.wrap(replies.text(replies.ACK), "addon")))
        self.assertEqual([(c["method"], c["path"], c["email"]) for c in self.calls], [("GET", "/v1/desk/check", EMPLOYEE)])
        (p,) = self.published
        self.assertEqual((p["key"], p["kind"], p["email"], p["session_id"], p["space"], p["thread"]),
                         (events.event_key(MESSAGE), "message", EMPLOYEE, sid_today(self.main), SPACE, THREAD))
        self.assertNotIn(AADHAAR, p["question"])
        self.assertIn("[Aadhaar]", p["question"])
        self.assertEqual(self.claims.docs[events.event_key(MESSAGE)]["state"], "queued")
        self.assertEqual(self.event(addon_message(f"My Aadhaar is {AADHAAR}. {LEAVE}"))[1], body)      # a retry
        self.assertEqual(len(self.published), 1)
        (row, dup) = self.rows()
        self.assertEqual((row["outcome"], row["tenant"], row["user"], row["queued"]), ("queued", "acme", None, True))
        self.assertEqual((dup["outcome"], dup["user"]), ("duplicate", None))     # the class is not known yet
        self.no_text_logged(AADHAAR, LEAVE)
        _, body = self.event(classic_message(LEAVE + " again"))        # the classic shape, the same message: no wrapper
        self.assertEqual(body, replies.text(replies.ACK))

    def test_direct_typed_short_questions_only(self):
        for body, reply in ((addon_message(space="spaces/NAMED", space_type="SPACE"), replies.DM_ONLY),
                            (addon_message(attachment=True), replies.TYPED_ONLY),
                            (addon_message("x" * 4001), replies.TOO_LONG),
                            (addon_message(email=None), replies.NO_ACCOUNT),
                            (addon_message(sender_type="BOT"), replies.NO_ACCOUNT)):
            _, got = self.event(body)
            self.assertEqual(self.message_of(got), replies.text(reply))
        self.assertEqual((self.published, self.calls, self.claims.docs), ([], [], {}))
        self.assertEqual(len(self.rows("gchat_no_email")), 2)
        self.assertEqual(self.event(ADDED)[1], replies.wrap(replies.welcome(), "addon"))
        self.assertEqual(self.event({"chat": {"somethingElse": {}}})[1], {})

    def test_a_refusal_from_the_check_is_the_fixed_reply_and_frees_the_claim(self):
        for detail, reply in ((replies.DESK_NOT_A_MEMBER, replies.NOT_ON_ROSTER), (replies.DESK_DOOR_OFF, replies.DOOR_OFF)):
            self.answers[("GET", "/v1/desk/check")] = self.main.DeskError(403, detail)
            _, got = self.event(addon_message(LEAVE, name=MESSAGE + detail[:5].replace(" ", "")))
            self.assertEqual(self.message_of(got), replies.text(reply))
        self.assertEqual((self.published, self.claims.docs), ([], {}))
        self.answers[("GET", "/v1/desk/check")] = self.main.DeskError(0)      # too slow: the question goes on
        self.event(addon_message(LEAVE))
        self.assertEqual(len(self.published), 1)

    def test_a_failed_publish_frees_the_claim_and_an_unreadable_event_gets_nothing(self):
        order = []
        self.claims.queued = lambda key: (order.append("queued"), FakeClaims.queued(self.claims, key))

        def publish(project, payload):
            order.append("publish")
            raise self.main.post.PostError(503, True)

        with patch.object(self.main.post, "publish", publish):
            _, got = self.event(addon_message(LEAVE))
        self.assertEqual(self.message_of(got), replies.text(replies.UNREACHABLE))
        self.assertEqual((order, self.claims.docs), (["queued", "publish"], {}))      # queued first, then freed
        self.assertIsNone(self.rows()[-1]["user"])                  # a publish that timed out may still be delivered
        with patch.object(self.main.events, "normalise", side_effect=TypeError(LEAVE)):
            self.assertEqual(self.event(addon_message(LEAVE)), (200, {}))
        self.assertEqual(self.rows("gchat_error")[-1], {"event": "gchat_error", "where": "normalise", "error": "TypeError"})
        self.no_text_logged(LEAVE)

    def test_sync_only_mode_asks_no_check_and_promises_no_later_answer(self):
        self.answers[("POST", "/v1/desk")] = outcomes()["handbook"]
        s = sid_today(self.main)
        sent = []
        with patch.object(self.main, "GCHAT_ASYNC", False):
            _, body = self.event(addon_message(LEAVE))
            self.assertEqual([(c["path"], c["timeout"]) for c in self.calls], [("/v1/desk", self.main.SYNC_ONLY_BUDGET_S)])
            self.assertEqual(self.claims.docs[events.event_key(MESSAGE)]["state"], "answered")
            sent.append(self.message_of(body))
            _, body = self.event(addon_message(LEAVE))                       # Chat's retry of the same message
            self.assertEqual(self.message_of(body), replies.text(replies.TAKEN))
            sent.append(self.message_of(body))
            for _ in range(2):                                               # a chip, pressed twice
                _, body = self.event(addon_press({"act": "chip", "chip": "statute", "sid": s}))
                sent.append(self.message_of(body))
            self.assertEqual(sent[-1], replies.text(replies.TAKEN))
            self.answers[("POST", "/v1/desk")] = self.main.DeskError(403, replies.DESK_DOOR_OFF)
            _, body = self.event(addon_message(LEAVE, name=MESSAGE + "B"))   # the Desk call refuses as the check would
            self.assertEqual(self.message_of(body), replies.text(replies.DOOR_OFF))
            sent.append(self.message_of(body))
        self.assertNotIn("/v1/desk/check", [c["path"] for c in self.calls])
        self.assertEqual(self.published, [])
        for msg in sent:
            self.assertNotIn(msg, (replies.text(replies.ACK), replies.text(replies.ALREADY)))

    def test_the_token_is_checked_before_the_body_is_read(self):
        import asyncio
        read, sent = [], []

        async def receive():
            read.append(1)
            return {"type": "http.request", "body": json.dumps(addon_message(POSH)).encode(), "more_body": False}

        async def send(message):
            sent.append(message)

        for path in ("/", "/work"):
            scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "POST",
                     "scheme": "https", "path": path, "raw_path": path.encode(), "root_path": "", "query_string": b"",
                     "headers": [(b"authorization", b"Bearer forged")], "server": ("bridge", 443),
                     "client": ("caller", 1)}
            asyncio.run(self.main.app(scope, receive, send))
        self.assertEqual([m["status"] for m in sent if m["type"] == "http.response.start"], [401, 401])
        self.assertEqual((read, self.calls, self.published), ([], [], []))

    def test_a_token_whose_payload_is_not_an_object_is_a_401(self):
        payload = base64.urlsafe_b64encode(b"[1]").decode().rstrip("=")
        for path, handle in (("/", self.main.handle_event), ("/work", self.main.handle_work)):
            r = handle({"authorization": f"Bearer e30.{payload}.c2ln"}, b"{}")
            self.assertEqual(r.status_code, 401, path)
        self.assertEqual([r["reason"] for r in self.rows("gchat_verify_failed")], ["invalid_token", "invalid_token"])

    def test_an_address_the_desk_would_refuse_never_reaches_it(self):
        _, body = self.event(addon_message(email="a@b"))
        self.assertEqual(self.message_of(body), replies.text(replies.NO_ACCOUNT))
        _, body = self.event(addon_message(POSH, email="a@b"))                 # a gate hit: the fixed text alone
        self.assertEqual(buttons(self.message_of(body)), [])
        self.assertEqual(self.calls, [])
        (row,) = self.rows("gchat_no_email")
        self.assertEqual((row["has_sender_email"], row["email_is_person"]), (True, False))
        self.event(addon_message(email="o'neil@example.com", name=MESSAGE + "O"))
        self.assertEqual([(c["path"], c["email"]) for c in self.calls], [("/v1/desk/check", "o'neil@example.com")])

    def test_a_post_no_credential_may_make_is_acknowledged_and_the_desk_not_asked_again(self):
        self.answers[("POST", "/v1/desk")] = outcomes()["handbook"]
        tries = []

        def create(space, thread, message_id, message):
            tries.append(message)
            raise self.main.post.PostError(403, False, auth=True)

        with patch.object(self.main.post, "create", create):
            self.assertEqual(self.work(self.payload()), 204)
            self.assertEqual(self.work(self.payload()), 204)                     # a redelivery
        self.assertEqual(len(tries), 1)                       # no "could not reach" post: it would be refused alike
        self.assertEqual([c["path"] for c in self.calls], ["/v1/desk"])
        self.assertEqual(self.claims.docs[events.event_key(MESSAGE)]["state"], "answered")
        (row,) = self.rows("gchat_answer")
        self.assertEqual((row["attempts"], row["outcome"]), (1, "post_refused"))

    def test_the_real_claims_keep_no_text_and_no_email(self):
        store = FakeFirestore()
        self.answers[("POST", "/v1/desk")] = outcomes()["handbook"]
        s = sid_today(self.main)
        with patch.object(self.main, "claims", claims), patch.object(claims, "_client", store), \
                patch.object(claims, "_transactional", run_once):
            self.event(addon_message(f"My Aadhaar is {AADHAAR}. {LEAVE}"))
            self.assertEqual(self.event(addon_message(LEAVE))[1], replies.wrap(replies.text(replies.ACK), "addon"))
            self.event(addon_press({"act": "chip", "chip": "statute", "sid": s}))
            (p,) = [x for x in self.published if x["kind"] == "message"]
            self.assertEqual(self.work(p), 204)
            self.assertEqual(self.work(p), 204)                                  # a redelivery: answered
        self.assertEqual(len(self.published), 2)
        self.assertEqual([c["path"] for c in self.calls].count("/v1/desk"), 1)
        self.assertEqual(len(store.docs), 2)
        self.assertEqual(store.docs[f"gchat_events/{events.event_key(MESSAGE)}"]["state"], "answered")
        for doc in store.docs.values():
            self.assertEqual(set(doc), ClaimsTests.FIELDS)
            flat = json.dumps(doc, default=str)
            for word in ("@", AADHAAR, LEAVE, "Aadhaar", "statute", SPACE, "users/"):
                self.assertNotIn(word, flat)

    # -------------------------------------------------------------- whom a row names
    def test_no_row_of_a_turn_the_gate_missed_and_the_desk_found_sensitive_names_the_person(self):
        """The Desk logs its own row of such a turn, sensitive and via "gchat", seconds after the bridge's: a bridge row
        that named the person would pair with it by time and tenant. Queued, a duplicate, the worker, sync-only."""
        self.assertIsNone(desk_rules.gate(MISSED))
        self.answers[("POST", "/v1/desk")] = self.posh_answer()
        s = sid_today(self.main)
        self.event(addon_message(MISSED))
        self.event(addon_message(MISSED))                                        # Chat's retry
        self.event(addon_press({"act": "chip", "chip": "case", "sid": s}))       # a chip goes the same way
        self.assertEqual(len(self.published), 2)
        for p in self.published:
            self.assertEqual(self.work(p), 204)                  # the POSH card posted, the push acknowledged
        self.assertIn(json.dumps(cards.POSH_PRIVACY)[1:-1], json.dumps(self.posts[0]["message"]))
        with patch.object(self.main, "GCHAT_ASYNC", False):
            self.event(addon_message(MISSED, name=MESSAGE + "S"))                # answered in the response
            self.answers[("POST", "/v1/desk")] = outcomes()["case_draft"] | {
                "case": None, "case_offer": {"case_type": "grievance"}}
            self.event(addon_message(MISSED, name=MESSAGE + "G"))
            self.answers[("POST", "/v1/desk")] = self.main.DeskError(0)           # the Desk may have had it all the same
            self.event(addon_message(MISSED, name=MESSAGE + "T"))
        self.assertEqual([(r["kind"], r["outcome"], r["class"], r["user"]) for r in self.rows()], [
            ("message", "queued", None, None), ("message", "duplicate", None, None), ("press", "queued", None, None),
            ("message", "answered", "sensitive", None), ("message", "answered", "sensitive", None),
            ("message", "unreachable", None, None)])
        self.assertEqual([r["outcome"] for r in self.rows("gchat_answer")], ["case", "case"])
        self.assertFalse(any(EMPLOYEE in raw for raw in self.log.raw))          # no row of any kind names the person
        self.no_text_logged(MISSED)

    def test_a_row_names_the_person_when_the_class_is_known_and_plain_or_the_desk_never_had_the_words(self):
        with patch.object(self.main, "GCHAT_ASYNC", False):
            for name, reply in (("A", "handbook"), ("B", "case_draft"), ("C", "draft_open")):
                self.answers[("POST", "/v1/desk")] = outcomes()[reply]
                self.event(addon_message(LEAVE, name=MESSAGE + name))
        self.answers[("GET", "/v1/desk/check")] = self.main.DeskError(403, replies.DESK_NOT_A_MEMBER)
        self.event(addon_message(LEAVE, name=MESSAGE + "D"))                    # refused before any Desk call
        self.event(addon_message("x" * 4001, name=MESSAGE + "E"))
        self.event(ADDED)
        self.answers[("POST", "/v1/desk")] = outcomes()["case_draft"]
        self.event(addon_message("My F&F settlement is overdue by three weeks.", name=MESSAGE + "F"))   # a gate hit
        self.assertEqual([(r["outcome"], r["class"], r["user"]) for r in self.rows()], [
            ("answered", None, EMPLOYEE), ("answered", "exit_dues", EMPLOYEE),
            ("answered", None, None),                                           # a case whose type the reply does not say
            ("refused", None, EMPLOYEE), ("too_long", None, EMPLOYEE), ("welcome", None, EMPLOYEE),
            ("gate", "exit_dues", EMPLOYEE)])

    def test_a_gate_hit_names_nobody_when_the_desks_newer_rules_find_it_sensitive(self):
        """The bridge's image may gate by older rules than the Desk's (mk/agents.mk): its own class is plain while the
        Desk logs the turn sensitive and via "gchat". A call that failed may have been classified all the same."""
        self.answers[("POST", "/v1/desk")] = self.posh_answer()
        with patch.object(self.main.desk_rules, "gate", lambda text: "human_requested"):
            self.event(addon_message(LEAVE, name=MESSAGE + "A"))
            self.answers[("POST", "/v1/desk")] = self.main.DeskError(0)
            self.event(addon_message(LEAVE, name=MESSAGE + "B"))
            self.answers[("POST", "/v1/desk")] = self.main.DeskError(403, replies.DESK_NOT_A_MEMBER)
            self.event(addon_message(LEAVE, name=MESSAGE + "C"))                 # refused before the Desk decides
        self.assertEqual([(r["outcome"], r["class"], r["user"]) for r in self.rows()], [
            ("gate", "sensitive", None), ("gate_fixed", "human_requested", None),
            ("gate_fixed", "human_requested", EMPLOYEE)])

    def test_a_gate_hit_names_the_person_when_the_desks_rules_find_no_case(self):
        """The mirror case: the bridge's rules fire sensitive while the Desk routes the turn plain and names the person
        on its own row. The bridge row must not mark that person's turn sensitive, so it follows the Desk. A failed
        call may have been logged by name all the same, so its row names neither the person nor the class."""
        self.answers[("POST", "/v1/desk")] = outcomes()["handbook"]
        with patch.object(self.main.desk_rules, "gate", lambda text: "posh"):
            self.event(addon_message(LEAVE, name=MESSAGE + "A"))
            self.answers[("POST", "/v1/desk")] = self.main.DeskError(0)
            self.event(addon_message(LEAVE, name=MESSAGE + "B"))
        self.assertEqual([(r["outcome"], r["class"], r["user"]) for r in self.rows()], [
            ("gate", None, EMPLOYEE), ("gate_fixed", None, None)])

    # -------------------------------------------------------------- the presses
    def test_the_presses(self):
        s = sid_today(self.main)
        _, got = self.event(addon_press({"act": "chip", "chip": "statute", "sid": s}))
        self.assertEqual(self.message_of(got), replies.text(replies.ACK))
        self.assertEqual((self.published[-1]["chip"], self.published[-1]["kind"], self.published[-1].get("question")),
                         ("statute", "press", None))
        _, got = self.event(addon_press({"act": "chip", "chip": "statute", "sid": s}))       # doubled
        self.assertEqual(self.message_of(got), replies.text(replies.ALREADY))
        _, got = self.event(addon_press({"act": "chip", "chip": "statute",
                                         "sid": events.session_id("spaces/OTHER", "20261001")}, name="spaces/DMSPACE/messages/C2"))
        self.assertEqual(self.message_of(got), replies.text(replies.STALE))
        self.answers[("POST", "/v1/cases/" + "a" * 32 + "/confirm")] = {
            "case_id": "a" * 32, "case_type": "grievance", "tenant": "acme",
            "owner": {"queue_name": "Grievance Redressal Committee"}, "clock": ["30 days"]}
        _, got = self.event(addon_press({"act": "confirm", "case": "a" * 32, "sid": s}, name="spaces/DMSPACE/messages/C3"))
        call = self.calls[-1]
        self.assertEqual((call["path"], set(call["body"])), ("/v1/cases/" + "a" * 32 + "/confirm", {"token"}))
        self.assertTrue(cases.TOKEN.match(call["body"]["token"]))
        self.assertIn("Your case is open", json.dumps(self.message_of(got)))
        self.assertEqual(self.rows()[-1]["user"], None)                               # a grievance: sensitive
        offer = self.posh_answer()["case_offer"]["posh"]
        unit = sorted(offer)[0]
        self.answers[("GET", "/v1/cases/offer")] = {"tenant": "acme", "posh": offer}
        self.answers[("POST", "/v1/cases")] = {"case_id": "c" * 32, "case_type": "posh", "tenant": "acme"}
        digest = cards.members_digest(m["email"] for m in offer[unit]["members"])
        _, got = self.event(addon_press({"act": "posh", "unit": unit, "m": digest, "sid": s},
                                        name="spaces/DMSPACE/messages/C4"))
        call = self.calls[-1]
        self.assertEqual((call["body"]["case_type"], call["body"]["unit"], sorted(call["body"]["contacts"])),
                         ("posh", unit, sorted(m["email"] for m in offer[unit]["members"])))
        self.assertNotIn("summary", call["body"])
        self.assertIn("Recorded", json.dumps(self.message_of(got)))
        _, got = self.event(addon_press({"act": "options", "cls": "posh", "sid": s}, name="spaces/DMSPACE/messages/C5"))
        self.assertEqual({p["value"] for b in buttons(self.message_of(got)) for p in b["onClick"]["action"]["parameters"]
                          if p["key"] == "unit"}, set(offer))
        self.answers[("POST", "/v1/cases")] = {"case_id": "d" * 32, "case_type": "grievance", "tenant": "acme",
                                               "summary": "", "owner": {"queue_name": "GRC"}, "clock": [], "basis": []}
        _, got = self.event(addon_press({"act": "options", "cls": "grievance", "sid": s}, name="spaces/DMSPACE/messages/C6"))
        self.assertEqual(self.calls[-1]["body"], {"case_type": "grievance"})
        self.assertEqual([p["value"] for b in buttons(self.message_of(got)) for p in b["onClick"]["action"]["parameters"]
                          if p["key"] == "act"], ["confirm", "cancel"])
        self.answers[("POST", "/v1/cases/" + "a" * 32 + "/cancel")] = self.main.DeskError(409, "this case is closed")
        _, got = self.event(addon_press({"act": "cancel", "case": "a" * 32, "sid": s}, name="spaces/DMSPACE/messages/C7"))
        self.assertEqual(self.message_of(got), replies.text(replies.REFUSED + "this case is closed"))
        named = addon_press({"act": "chip", "chip": "statute", "sid": s}, name="spaces/NAMED/messages/C8")
        named["chat"]["buttonClickedPayload"]["space"] = {"name": "spaces/NAMED", "spaceType": "SPACE"}
        _, got = self.event(named)
        self.assertEqual(self.message_of(got), replies.text(replies.DM_ONLY))

    def test_a_committee_press_sends_only_to_the_members_its_card_listed(self):
        s, offer = sid_today(self.main), copy.deepcopy(self.posh_answer()["case_offer"]["posh"])
        unit = sorted(offer)[0]
        self.answers[("GET", "/v1/cases/offer")] = {"tenant": "acme", "posh": offer}
        _, got = self.event(addon_press({"act": "options", "cls": "posh", "sid": s}, name="spaces/DMSPACE/messages/O1"))
        presses = [{p["key"]: p["value"] for p in b["onClick"]["action"]["parameters"]}
                   for b in buttons(self.message_of(got))]
        (press,) = [p for p in presses if p.get("unit") == unit]
        offer[unit]["members"].append({"name": "Member (placeholder)", "email": "ic.new.member@example.com"})
        _, got = self.event(addon_press(press, name="spaces/DMSPACE/messages/O1"))     # the committee changed since
        self.assertEqual(self.message_of(got), replies.text(cards.POSH_CHANGED))
        self.assertNotIn(("POST", "/v1/cases"), [(c["method"], c["path"]) for c in self.calls])
        self.assertEqual(self.rows()[-1]["outcome"], "stale")
        offer[unit]["members"] = [{"name": f"Member Number {i} (placeholder)", "email": f"ic.member.{i}@example.com"}
                                  for i in range(30)]                             # more names than the card shows
        _, got = self.event(addon_press({"act": "options", "cls": "posh", "sid": s}, name="spaces/DMSPACE/messages/O2"))
        msg = self.message_of(got)
        self.assertEqual({p["value"] for b in buttons(msg) for p in b["onClick"]["action"]["parameters"]
                          if p["key"] == "unit"}, set(offer) - {unit})
        self.assertEqual(json.dumps(msg).count(json.dumps(cards.POSH_TOO_LONG)[1:-1]), 1)
        self.assertNotIn("ic.member.29@example.com", json.dumps(msg))

    # -------------------------------------------------------------- the worker
    def payload(self, **kw):
        return {"key": events.event_key(MESSAGE), "kind": "message", "email": EMPLOYEE, "session_id": sid(),
                "space": SPACE, "thread": THREAD, "question": LEAVE, **kw}

    def test_the_worker_answers_once_under_the_client_id(self):
        self.answers[("POST", "/v1/desk")] = outcomes()["handbook"]
        self.assertEqual(self.work(self.payload()), 204)
        (post_,) = self.posts
        self.assertEqual((post_["space"], post_["thread"], post_["id"]),
                         (SPACE, THREAD, events.client_id(events.event_key(MESSAGE))))
        self.assertEqual(self.calls[-1]["body"], {"session_id": sid(), "question": LEAVE})
        self.assertEqual(self.calls[-1]["timeout"], self.main.WORK_TIMEOUT_S)
        self.assertEqual(self.work(self.payload()), 204)                       # a redelivery: answered, nothing more
        self.assertEqual(len(self.posts), 1)
        (row,) = self.rows("gchat_answer")
        self.assertEqual((row["attempts"], row["outcome"]), (1, "answer"))
        self.no_text_logged(LEAVE)

    def test_the_worker_retries_then_says_so_on_the_fifth_attempt(self):
        self.answers[("POST", "/v1/desk")] = self.main.DeskError(503)
        for attempt in range(1, self.main.MAX_ATTEMPTS):
            self.assertEqual(self.work(self.payload()), 503, attempt)
            self.assertEqual(self.claims.docs[events.event_key(MESSAGE)]["state"], "queued")
        self.assertEqual(self.posts, [])
        self.assertEqual(self.work(self.payload()), 204)
        (post_,) = self.posts
        self.assertEqual(post_["message"], replies.text(replies.UNREACHABLE))
        self.assertEqual(self.claims.docs[events.event_key(MESSAGE)]["state"], "answered")
        self.answers[("POST", "/v1/desk")] = self.main.DeskError(403, replies.DESK_DOOR_OFF)     # a refusal: said at once
        self.assertEqual(self.work(self.payload(key=events.event_key(MESSAGE + "2"))), 204)
        self.assertEqual(self.posts[-1]["message"], replies.text(replies.DOOR_OFF))

    def test_the_worker_refuses_another_subscription_and_a_payload_it_did_not_write(self):
        self.assertEqual(self.work(self.payload(), subscription=f"projects/{PROJECT}/subscriptions/another"), 401)
        self.assertEqual(self.work(self.payload(), subscription="projects/other-project/subscriptions/documind-gchat-push"), 401)
        for bad in (self.payload(key="x"), self.payload(email="nobody"), self.payload(session_id="a:b"),
                    self.payload(question="x" * 4001), self.payload(chip="statute"), self.payload(space="spaces/A/B")):
            self.assertEqual(self.work(bad), 204)
        self.assertEqual((self.calls, self.posts), ([], []))
        self.assertEqual(self.work(self.payload(question=None, chip="statute", kind="press")), 204)
        self.assertEqual(self.calls[-1]["body"], {"session_id": sid(), "chip": "statute"})


def sid_today(main) -> str:
    return events.session_id(SPACE, events.today_ist())


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class DelegationTests(unittest.TestCase):
    """delegation.principal() on agent.py's real app, through test_desk.py's stand-ins: identity from an x-test-email
    header, Firestore a dictionary, the models scripted, rag-api a table."""

    @classmethod
    def setUpClass(cls):
        cls.td = test_desk()
        cls.base = cls.td.ServiceTests
        cls.base.setUpClass()
        import delegation
        cls.delegation = delegation

    @classmethod
    def tearDownClass(cls):
        cls.base.tearDownClass()

    def setUp(self):
        td = self.td
        self.h = self.base("test_a_handbook_turn_answers_cites_and_logs_one_row")
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.h.flags["acme"]["desk_gchat"] = "on"
        self.h.flags["acme"]["desk_gate"] = "on"
        self.dlog = _Log()
        for p in (patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": PROJECT}), patch.object(self.delegation, "log", self.dlog)):
            p.start()
            self.addCleanup(p.stop)
        self.ME, self.LEAVE = td.ME, td.LEAVE

    def ask(self, c, who, path="/v1/desk", body=None, person=None, method="POST", headers=None):
        hdrs = {"x-test-email": who} if who else {}
        if person is not None:
            hdrs["X-DocuMind-Principal"] = person
        hdrs.update(headers or {})
        if method == "GET":
            return c.get(path, headers=hdrs)
        return c.post(path, json=body, headers=hdrs)

    def refused(self):
        return [r for r in self.dlog.rows if r.get("event") == "desk_delegation_refused"]

    def denied(self):
        return [r for r in self.dlog.rows if r.get("event") == "desk_delegation_denied"]

    def test_the_delegate_is_served_as_the_person_it_names(self):
        with self.h.client() as c:
            r = self.ask(c, BRIDGE, body={"question": self.LEAVE, "session_id": sid()}, person=self.ME)
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual((r.json()["email"], r.json()["tenant"], r.json()["route"]), (self.ME, "acme", "handbook"))
            r = self.ask(c, BRIDGE, "/v1/desk/check", person=self.ME, method="GET")
            self.assertEqual(r.json(), {"email": self.ME, "tenant": "acme", "via": "gchat"})
            r = self.ask(c, BRIDGE, "/v1/cases", body={"case_type": "grievance"}, person=self.ME)
            self.assertEqual(r.status_code, 200, r.text)
            (rec,) = self.h.db.cases().values()
            self.assertEqual((rec["via"], rec["requester"]), ("gchat", self.ME))
            r = self.ask(c, self.ME, "/v1/desk/check", method="GET")                       # no header: as before
            self.assertEqual(r.json()["via"], "direct")
        (row,) = [x for x in self.h.log.rows if x.get("event") == "desk"]
        self.assertEqual((row["user"], row["via"], row["delegate"]), (self.ME, "gchat", "gchat"))
        self.assertEqual((self.refused(), self.denied()), ([], []))

    def test_a_delegated_sensitive_turn_names_nobody_and_the_check_refuses_as_the_desk_does(self):
        routed_off = "the routed Desk is not switched on for your company"
        with self.h.client() as c:
            r = self.ask(c, BRIDGE, body={"question": self.td.POSH, "session_id": sid()}, person=self.ME)
            self.assertEqual((r.status_code, r.json()["tenant"], r.json()["model_calls"]), (200, "acme", 0), r.text)
            draft = self.ask(c, BRIDGE, "/v1/cases", body={"case_type": "grievance"}, person=self.ME).json()["case_id"]
            r = self.ask(c, BRIDGE, body={"question": self.LEAVE, "session_id": sid(), "draft_id": draft}, person=self.ME)
            self.assertEqual((r.status_code, r.json()["method"]), (200, "draft"), r.text)
            self.h.flags["acme"]["desk_route"] = "off"                  # the check refuses whom POST /v1/desk refuses
            for path, method, body in (("/v1/desk/check", "GET", None),
                                       ("/v1/desk", "POST", {"question": self.LEAVE, "session_id": sid()})):
                r = self.ask(c, BRIDGE, path, body=body, person=self.ME, method=method)
                self.assertEqual((r.status_code, r.json()["detail"]), (403, routed_off), path)
                r = self.ask(c, self.ME, path, body=body, method=method)
                self.assertEqual((r.status_code, r.json()["detail"]), (403, routed_off), path)
            r = self.ask(c, self.td.EVAL, "/v1/desk/check", method="GET")    # the eval accounts, in any mode, as /v1/desk
            self.assertEqual((r.status_code, r.json()["via"]), (200, "direct"))
        posh, on_draft = [x for x in self.h.log.rows if x.get("event") == "desk"]
        for row in (posh, on_draft):
            self.assertEqual((row["user"], row["delegate"], row["session_id"], row["via"], row["case_type"]),
                             (None, None, None, "gchat", "sensitive"))
        self.assertNotIn("comments", json.dumps(self.h.log.rows))
        self.assertEqual((self.refused(), self.denied()), ([], []))

    def test_the_posh_privacy_line_is_what_the_desk_and_the_queue_do(self):
        """cards.POSH_PRIVACY, clause by clause, for a disclosure the gate catches and one only the classifier finds:
        read to decide the reply and kept by no case, no checkpoint and no row; a message that waited in the work
        queue is gone once acknowledged, and an unacknowledged one after an hour."""
        line = cards.POSH_PRIVACY
        self.assertIn("not saved with a case, in the Desk's history or in its logs", line)
        self.assertIn("removed from the queue once answered, within an hour at most", line)
        tf = (KIT / "terraform" / "gchat.tf").read_text(encoding="utf-8")
        topic = tf.split('resource "google_pubsub_topic" "gchat_work" {')[1].split("\n}\n")[0]
        sub = tf.split('resource "google_pubsub_subscription" "gchat_push" {')[1].split("\n}\n")[0]
        self.assertIn('message_retention_duration = "3600s"', sub)
        for kept in ("retain_acked_messages", "dead_letter_policy"):
            self.assertNotIn(kept, sub)
        self.assertNotIn("message_retention_duration", topic)
        self.assertNotIn("case", self.h.g.GRAPH_ROUTES)                     # a case turn writes no checkpoint
        self.assertIsNone(desk_rules.gate(MISSED))
        self.h.models = self.td.Models(self.td.l1("case", ct="posh"))
        with self.h.client() as c:
            for text, session in ((POSH, "gate-hit"), (MISSED, "gate-miss")):
                r = self.ask(c, BRIDGE, body={"question": text, "session_id": session}, person=self.ME)
                self.assertEqual((r.status_code, r.json()["route"], r.json()["case_offer"]["case_type"]),
                                 (200, "case", "posh"), r.text)
                self.assertIn(json.dumps(line)[1:-1], json.dumps(cards.render(r.json(), SELF_URL, session)))
                self.assertFalse(self.h.kept(c, self.ME, session))
        self.assertEqual(len(self.h.models.prompts), 1)                     # the miss, read by the classifier
        self.assertEqual(self.h.db.cases(), {})
        rows = [x for x in self.h.log.rows if x.get("event") == "desk"]
        self.assertEqual([(x["user"], x["via"], x["case_type"]) for x in rows], [(None, "gchat", "sensitive")] * 2)
        for text in (POSH, MISSED):
            self.assertNotIn(text, json.dumps(self.h.log.rows + self.dlog.rows))

    def test_rule_one_refuses_every_caller_but_the_delegate(self):
        ui = f"documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"
        other_project = "documind-gchat-sa@another-project.iam.gserviceaccount.com"
        with self.h.client() as c:
            for who in (self.td.EVAL, ui, self.ME, other_project, PUSH):
                r = self.ask(c, who, body={"question": self.LEAVE, "session_id": "s1"}, person=self.ME)
                self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.NOT_A_DELEGATE), who)
            self.assertEqual(self.ask(c, None, body={"question": self.LEAVE}, person=self.ME).status_code, 401)
        self.assertEqual([r["caller"] for r in self.refused()],
                         [w.lower() for w in (self.td.EVAL, ui, self.ME, other_project, PUSH)])
        self.assertTrue(all(set(r) == {"event", "caller", "reason", "path"} for r in self.refused()))
        self.assertEqual(self.h.log.rows, [])

    def test_the_named_principal_must_be_one_person(self):
        with self.h.client() as c:
            r = self.ask(c, BRIDGE, body={"question": self.LEAVE, "session_id": "s1"}, person="o'neil@example.com")
            self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.NOT_A_MEMBER))   # a person
            for person in ("documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com", "You@example.com",
                           "you@example.com:x", "not an address", "", "a@b"):
                r = self.ask(c, BRIDGE, body={"question": self.LEAVE, "session_id": "s1"}, person=person)
                self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.NOT_A_PERSON), person)
            r = c.post("/v1/desk", json={"question": self.LEAVE, "session_id": "s1"},
                       headers=[("x-test-email", BRIDGE), ("X-DocuMind-Principal", self.ME),
                                ("X-DocuMind-Principal", "colleague@example.com")])
            self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.NOT_A_PERSON))

    def test_only_the_delegable_routes_and_no_eval_fields(self):
        with self.h.client() as c:
            for method, path, body in (("POST", "/v1/route", {"question": self.LEAVE}), ("GET", "/v1/cases", None),
                                       ("GET", "/v1/cases/" + "a" * 32, None),
                                       ("POST", "/v1/cases/" + "a" * 32 + "/status", {"status": "closed"})):
                r = self.ask(c, BRIDGE, path, body=body, person=self.ME, method=method)
                self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.NOT_DELEGABLE), path)
            r = self.ask(c, BRIDGE, body={"question": self.LEAVE, "session_id": "s1", "arm": "C"}, person=self.ME)
            self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.NOT_IN_BODY))
            r = self.ask(c, BRIDGE, "/v1/cases", body={"case_type": "grievance", "prev_route": "handbook"}, person=self.ME)
            self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.NOT_IN_BODY))
        self.assertEqual({r["path"] for r in self.refused()},
                         {"/v1/route", "/v1/cases", "/v1/cases/{id}", "/v1/cases/{id}/status", "/v1/desk"})
        self.assertEqual(self.h.db.cases(), {})

    def test_the_roster_and_the_flag_deny_without_an_alert(self):
        with self.h.client() as c:
            r = self.ask(c, BRIDGE, body={"question": self.LEAVE, "session_id": "s1"}, person="stranger@example.com")
            self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.NOT_A_MEMBER))
            r = self.ask(c, BRIDGE, body={"question": self.LEAVE, "session_id": "s1"}, person=self.td.GLOBEX_ME)
            self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.DOOR_OFF))     # globex: off
            self.h.flags["acme"]["desk_gchat"] = "off"
            r = self.ask(c, BRIDGE, body={"question": self.LEAVE, "session_id": "s1"}, person=self.ME)
            self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.DOOR_OFF))
            self.h.flags["acme"]["desk_gchat"] = "on"

            def broken(tenant):
                raise RuntimeError("firestore unwell")

            with patch.object(self.td_desk(), "settings", broken):
                r = self.ask(c, BRIDGE, body={"question": self.LEAVE, "session_id": "s1"}, person=self.ME)
                self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.DOOR_OFF))
            r = self.ask(c, BRIDGE, "/v1/desk/check", method="GET")              # the delegate itself: no roster
            self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.NOT_A_MEMBER))
        self.assertEqual(self.refused(), [])
        self.assertEqual([r["reason"] for r in self.denied()], [self.delegation.NOT_A_MEMBER, self.delegation.DOOR_OFF,
                                                                self.delegation.DOOR_OFF, self.delegation.DOOR_OFF])
        self.assertTrue(all(set(r) == {"event", "reason", "path"} for r in self.denied()))

    def test_the_local_profile_refuses_the_header(self):
        with self.h.client() as c, patch.object(self.delegation, "PROFILE", "local"):
            r = self.ask(c, BRIDGE, body={"question": self.LEAVE, "session_id": "s1"}, person=self.ME)
            self.assertEqual((r.status_code, r.json()["detail"]), (403, self.delegation.NOT_LOCAL))
        self.assertEqual([r["reason"] for r in self.refused()], [self.delegation.NOT_LOCAL])

    def td_desk(self):
        return self.base.desk


class DeskSwitchTests(unittest.TestCase):
    """make desk DESK_GCHAT=on|off: refused until the gate and the routed Desk are on, and for a tenant whose data
    stays in India until the residency is confirmed; printed only when given or on."""

    def run_ops(self, db, *args):
        import io
        import types
        from contextlib import redirect_stdout
        fs = types.SimpleNamespace(Client=lambda project=None: db, SERVER_TIMESTAMP="SERVER_TIMESTAMP")
        google, cloud = types.ModuleType("google"), types.ModuleType("google.cloud")
        google.__path__, cloud.__path__, google.cloud, cloud.firestore = [], [], cloud, fs
        mods = {"google": google, "google.cloud": cloud, "google.cloud.firestore": fs}
        with patch.dict(sys.modules, mods), patch.dict(os.environ, {"DOCUMIND_OPERATOR": EMPLOYEE}), \
                redirect_stdout(io.StringIO()) as out:
            code = desk_ops.main(["--project", "documind-ai-YOUR-ID", "desk", "--tenant", "globex", *args])
        return code, out.getvalue()

    def test_the_door_switch(self):
        db = test_desk().FakeDB()
        db.docs["tenant_settings/globex"] = {"data_region": "in", "desk_gate": "off"}
        code, out = self.run_ops(db, "--gchat", "on")
        self.assertEqual(code, 2)
        self.assertIn("the hard gate is off", out)
        del db.docs["tenant_settings/globex"]["desk_gate"]                      # nothing set: the rules, enough here
        self.assertIn("the routed Desk is not on", self.run_ops(db, "--gchat", "on")[1])
        db.docs["tenant_settings/globex"].update({"desk_gate": "on"})
        self.assertIn("the routed Desk is not on", self.run_ops(db, "--gchat", "on")[1])
        db.docs["tenant_settings/globex"].update({"desk_route": "single", "desk_single": "statute"})
        code, out = self.run_ops(db, "--gchat", "on")
        self.assertEqual(code, 2)
        self.assertIn("CONFIRM_RESIDENCY=1", out)
        self.assertNotIn("desk_gchat", db.docs["tenant_settings/globex"])
        code, out = self.run_ops(db, "--gchat", "on", "--confirm-residency")
        self.assertEqual(code, 0, out)
        doc = db.docs["tenant_settings/globex"]
        self.assertEqual((doc["desk_gchat"], doc["desk_gchat_set_by"], doc["data_region"]), ("on", EMPLOYEE, "in"))
        self.assertEqual(json.loads(out)["desk_gchat"], "on")
        self.assertEqual(json.loads(self.run_ops(db)[1])["desk_gchat"], "on")          # on: printed
        code, out = self.run_ops(db, "--gchat", "off")                                  # off is never refused
        self.assertEqual((code, db.docs["tenant_settings/globex"]["desk_gchat"]), (0, "off"))
        self.assertNotIn("desk_gchat", json.loads(self.run_ops(db)[1]))                 # off and not given: as before
        db.docs["tenant_settings/zeta"] = {"data_region": "any", "desk_gate": "on", "desk_route": "on"}
        self.assertEqual(desk_ops.gchat_refusal(db, "zeta", False), None)


if __name__ == "__main__":
    unittest.main()
