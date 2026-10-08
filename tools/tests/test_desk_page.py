"""The Desk page's case half (deploy/services/frontend/desk.py, workshop lesson 5.6), offline, with Streamlit stubbed.

In the style of tools/check_authz.py's documents-page check: the page's source is run with its imports replaced by
fakes at the seam - a Streamlit that records what is drawn and answers widgets from a table (a button is pressed by
its form or key and its label, so two "Send" buttons are two buttons), and an HTTP client that plays the chat
service's case offer, case routes and chat door (its case views built by the kit's own shared/cases.view, its offer
by the route's own rules). No network, no Streamlit, no credential.

    - the page draws no case data unless the service saw the signed-in person, in their company;
    - the inbox lists only the reader's queue, sent cases only, and shows who raised a case to that queue alone;
      what a person wrote cannot become an image or a link there;
    - the POSH card always shows the Local Committee contact, keeps the committee's contacts on screen when the
      service cannot open the case (409, 503), records once per press, and shows the record for its office only;
    - a person with no queue role sees no inbox; a failed role read shows the case form only;
    - a gate hit gets the chat door's fixed reply with no other call, and the case it offers: the POSH card at once,
      another kind behind a button; the typed words are never shown back, kept, or put in a case;
    - only an employee gets the box; the routed half stays hidden while desk_route is off or absent, and while it is on
      or single it takes the box's place: the reply shown as the desks answered it, the POSH card at once, a drafted
      case under Raise a case, chips that ask another desk or start a case, only for the signed-in person, and the
      question never shown back or kept;
    - a draft is edited, sent with one token however often it is pressed, or cancelled; an expired one gives the
      person's words and kind back;
    - a call that does not work is told in a plain sentence, never in words that repeat what was typed;
    - the page's copies of the kit's tables are the kit's, it copies none of shared/desk_law.py's wording, and the
      fakes answer with the routes' own fields.
"""
import ast
import json
import re
import secrets
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "deploy"
PAGE = KIT / "services" / "frontend" / "desk.py"
APP = KIT / "services" / "frontend" / "app.py"
ROUTES = KIT / "services" / "chat" / "desk.py"
if str(KIT) not in sys.path:
    sys.path.insert(0, str(KIT))

from shared import cases, desk_law, desk_rules, roles  # noqa: E402

CHAT = "https://documind-chat-NUMBER.us-central1.run.app"
ME = "you@example.com"
DISCLOSURE = "My manager keeps making sexual comments about my body. What can I do?"


def _queues(name):
    doc = json.loads((KIT / "evals" / "desk" / f"queues.{name}.json").read_text(encoding="utf-8"))
    return {k: v for k, v in doc.items() if not k.startswith("_")}


QCFG, ZCFG = _queues("acme"), _queues("zeta")
NOW = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
SEND = ("desk_draft", "Send")


# ---------------------------------------------------------------- the fakes at the seam
class Stop(Exception):
    pass


class Rerun(Exception):
    pass


class State(dict):
    """st.session_state: attribute or item access. As in Streamlit, the page may set a widget's key only before the
    widget is drawn in that run (`drawn` holds the keys drawn so far while a run is on)."""
    drawn = None

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k) from None

    def __setattr__(self, k, v):
        self[k] = v

    def __setitem__(self, k, v):
        if State.drawn is not None and k in State.drawn:
            raise AssertionError(f"StreamlitAPIException: st.session_state.{k} cannot be modified after the widget "
                                 f"with key {k} is instantiated")
        super().__setitem__(k, v)


class Block:
    def __init__(self, st, kind, label=""):
        self.st, self.kind, self.label = st, kind, label

    def __enter__(self):
        self.st.out.append((self.kind, str(self.label)))
        if self.kind == "form":
            self.st.forms.append(self.label)
        return self

    def __exit__(self, *a):
        if self.kind == "form":
            self.st.forms.pop()
        return False


def _draw(kind):
    def draw(self, body="", *a, **k):
        self.out.append((kind, str(body)))
    return draw


class FakeSt:
    """What the page draws, in order, as (kind, text). A widget answers from `answers` by label, else from the session
    under its key, else its default (kept in `values`). A button is pressed when (its form, or its key; its label) is
    in `pressed`."""

    def __init__(self, answers=None, pressed=()):
        self.session_state, self.answers, self.pressed = State(), dict(answers or {}), set(pressed)
        self.out, self.seen, self.options, self.values, self.forms = [], [], {}, {}, []

    title, subheader, caption, markdown = _draw("title"), _draw("subheader"), _draw("caption"), _draw("markdown")
    info, warning, error, success = _draw("info"), _draw("warning"), _draw("error"), _draw("success")

    def container(self, **k):
        return Block(self, "container")

    def expander(self, label, **k):
        return Block(self, "expander", label)

    def form(self, key, **k):
        return Block(self, "form", key)

    def _widget(self, label, default, key=None):
        """The person's answer for this label; else, as Streamlit does, what the session holds under the widget's key;
        else its default. A keyed widget's value is kept under its key."""
        self.out.append(("widget", label))
        self.values[label] = default
        value = self.answers.get(label, self.session_state.get(key, default) if key else default)
        if key:
            dict.__setitem__(self.session_state, key, value)
            if State.drawn is not None:
                State.drawn.add(key)
        return value

    def text_area(self, label, value="", key=None, **k):
        return self._widget(label, value, key)

    def selectbox(self, label, options, index=0, format_func=str, key=None, **k):
        opts = list(options)
        self.options[label] = [format_func(o) for o in opts]
        return self._widget(label, opts[index] if index is not None and opts else None, key)

    def multiselect(self, label, options, default=None, format_func=str, key=None, **k):
        self.options[label] = [format_func(o) for o in options]
        return self._widget(label, list(default or []), key)

    def checkbox(self, label, value=False, key=None, **k):
        return self._widget(label, value, key)

    def date_input(self, label, value=None, key=None, **k):
        return self._widget(label, value, key)

    def form_submit_button(self, label, **k):
        self.out.append(("button", label))
        return (self.forms[-1], label) in self.pressed

    def button(self, label, key=None, **k):
        assert not self.forms, "st.button inside a form"
        self.out.append(("button", label))
        return (key, label) in self.pressed

    def rerun(self):
        raise Rerun()

    def stop(self):
        raise Stop()

    # what a test reads
    def text(self, everything=False) -> str:
        rows = self.seen + self.out if everything else self.out
        return re.sub(r"\\(.)", r"\1", "\n".join(t for _, t in rows))     # the page's Markdown escapes, undone

    def kinds(self, kind) -> list[str]:
        return [t for k, t in self.out if k == kind]


class Resp:
    def __init__(self, status, body):
        self.status_code, self._body = status, body

    def json(self):
        if self._body is None:
            raise ValueError("no JSON")
        return self._body


class Http:
    def __init__(self, service):
        self.service, self.calls = service, []

    def request(self, method, url, json=None, headers=None, timeout=None):
        assert url.startswith(CHAT + "/"), url
        self.calls.append((method, url[len(CHAT):], json, headers))
        status, body = self.service(method, url[len(CHAT):], json)
        if status == 0:
            raise ConnectionError("the chat service is not there")
        return Resp(status, body)


def record(case_type, queue, requester, status="open", queues=QCFG, **kw) -> dict:
    """A case as the routes return it: the kit's own shared/cases.view of a record."""
    rec = {"case_id": secrets.token_hex(16), "tenant": "acme", "requester": requester, "case_type": case_type,
           "queue": queue, "unit": None, "chosen_contacts": [], "status": status, "source": "button", "via": "direct",
           "created_at": NOW, "opened_at": None if status == "draft" else NOW, "status_at": NOW, "due_at": None,
           "sla_basis": None, "summary": None, "statutory_flags": [], "people_ops_opt_in": False}
    rec.update(kw)
    if status == "draft":
        rec["expire_at"] = NOW + cases.DRAFT_TTL
    elif rec["due_at"] is None:
        rec["due_at"], rec["sla_basis"] = cases._due(case_type, queue, queues, NOW)
    return cases.view(rec, queues)


def posh_refusal(body, held) -> tuple[int, dict]:
    """(status, body) of shared/cases.open_posh's refusal when every chosen member holds `held`, as the route sends it."""
    with mock.patch.object(cases.roles_mod, "roles_for", lambda db, tenant, email: list(held)):
        try:
            cases.open_posh(None, "acme", ME, body["unit"], body["contacts"], QCFG, token=body["token"])
        except cases.CaseError as e:
            return e.status, {"detail": e.detail}
    raise AssertionError("open_posh went on to write a case")


class Service:
    """The chat service as the page sees it: GET /v1/cases/offer, GET /v1/cases, POST /v1/cases and its confirm,
    cancel and status, and POST /v1/chat behind the chat door. It answers as `seen_as`, in `tenant`."""

    def __init__(self, roles=("employee",), inbox=(), mine=(), list_status=200, offer_status=200, gate=None,
                 more=False, tenant="acme", queues=QCFG, desk_gate="on", desk_route="off", seen_as=ME, gate_model="none"):
        self.roles, self.inbox, self.mine, self.gate, self.more = list(roles), list(inbox), list(mine), gate, more
        self.gate_model = gate_model            # "none" for a rule's reply; the model check's model when it found it
        self.list_status, self.offer_status, self.tenant, self.queues = list_status, offer_status, tenant, queues
        self.desk_gate, self.desk_route, self.seen_as = desk_gate, desk_route, seen_as
        self.drafts, self.confirm_status, self.move_status, self.posh_status = {}, [], [], []
        self.opened_by_then, self.ic_roles, self.chat_reply = False, None, None
        self.desk_replies = []

    def desk_answer(self, body, **kw) -> dict:
        """services/chat/desk.desk_turn's answer, in its fields: by default a handbook section with one citation."""
        cite = {"n": 1, "quote": "NP-03", "source_uri": "gs://b/acme/hr_policy_2026.md", "page": 1}
        out = {"email": self.seen_as, "tenant": self.tenant, "session_id": body.get("session_id"),
               "mode": self.desk_route, "arm": "B", "route": "handbook", "method": "model", "outcome": "answer",
               "answer": "Sixty days <b>[1]</b>.", "note": "",
               "sections": [{"desk": "handbook", "title": "From the company handbook", "answer": "Sixty days <b>[1]</b>.",
                             "answerable": True, "confidence": "high", "citations": [cite], "in_force": [], "error": False}],
               "citations": [cite], "chips": [], "case": None, "case_offer": None, "tool_calls": [], "retrieve_calls": 1,
               "model_calls": 1, "decision": {"route": "handbook"}, "latency_ms": 900, "limits": {"cost_inr": 0.1}}
        out.update(kw)
        return out

    def offer(self) -> dict:
        """services/chat/desk.case_offer's answer, by its own rules."""
        q = self.queues or {}
        types = [t for t in desk_law.CASE_TYPES if (t == "posh" and not cases.posh_errors(q))
                 or (t != "posh" and cases.queue_for(t, q) is not None)]
        units = ((q.get("posh") or {}).get("units") or {}) if "posh" in types else {}
        posh = {u: {"name": s.get("name") or u,
                    "members": [{"name": m.get("name"), "email": str(m.get("email") or "").lower()} for m in s.get("ic") or []],
                    "local_committee": s.get("local_committee")} for u, s in sorted(units.items())}
        return {"email": self.seen_as, "tenant": self.tenant, "roles": self.roles, "desk_gate": self.desk_gate,
                "desk_route": self.desk_route, "types": types, "posh": posh or None}

    def __call__(self, method, path, body):
        if (method, path) == ("GET", "/v1/cases/offer"):
            if self.offer_status != 200:
                return self.offer_status, ({"detail": "the company's case queues could not be read: try again in a minute"}
                                           if self.offer_status else None)
            if "case" not in roles.desks(self.roles):
                return 403, {"detail": "your roles in this company do not include raising a case"}
            return 200, self.offer()
        if (method, path) == ("GET", "/v1/cases"):
            if self.list_status != 200:
                return self.list_status, ({"detail": "the company's case queues could not be read"} if self.list_status else None)
            return 200, {"email": self.seen_as, "tenant": self.tenant, "roles": self.roles, "inbox": self.inbox,
                         "mine": self.mine, "more": self.more}
        if (method, path) == ("POST", "/v1/chat"):
            if self.chat_reply:
                return self.chat_reply
            if self.gate:
                return 200, {"answer": desk_law.template(self.gate), "tool_calls": [], "refusals": [], "citations": [],
                             "brain": "desk_gate", "model": self.gate_model, "session_id": body["session_id"],
                             "latency_ms": 2, "limits": {"cost_inr": 0 if self.gate_model == "none" else 0.02},
                             "case_offer": {"case_type": self.gate}}
            return 200, {"answer": "Sixty days <b>[1]</b>.", "tool_calls": ["search"], "refusals": [], "brain": "direct",
                         "model": "gemini-3.6-flash", "session_id": body["session_id"], "latency_ms": 900,
                         "citations": [{"quote": "NP-03", "source_uri": "gs://b/acme/hr_policy_2026.md", "page": 1}]}
        if (method, path) == ("POST", "/v1/cases"):
            if body["case_type"] == "posh":
                if not body.get("token"):
                    return 422, {"detail": "a POSH case takes a client token, so a doubled press opens one case"}
                if self.posh_status:
                    status = self.posh_status.pop(0)
                    if status != 200:
                        return status, None
                if self.ic_roles is not None:          # the kit's own refusal, from the roles the members hold
                    return posh_refusal(body, self.ic_roles)
                return 200, record("posh", desk_law.IC_QUEUE + body["unit"], ME, unit=body["unit"],
                                   chosen_contacts=sorted(body["contacts"]), queues=self.queues)
            view = record(body["case_type"], "grc" if body["case_type"] == "grievance" else "people", ME,
                          status="draft", summary=body.get("summary") or "",
                          people_ops_opt_in=bool(body.get("people_ops_opt_in")),
                          last_working_day=body.get("last_working_day"))
            self.drafts[view["case_id"]] = view
            return 200, view
        m = re.fullmatch(r"/v1/cases/([0-9a-f]{32})/(confirm|cancel|status)", path)
        if m and m.group(2) == "confirm":
            status = self.confirm_status.pop(0) if self.confirm_status else 200
            if status != 200:
                return status, {"detail": {410: "this draft expired after 30 minutes: raise the case again",
                                           409: "this case is already open"}.get(status, "boom")}
            d = self.drafts[m.group(1)]
            return 200, record(d["case_type"], d["queue"], ME, summary=body.get("summary"), case_id=d["case_id"])
        if m and m.group(2) == "cancel":           # a draft is deleted: a second cancel finds nothing
            gone = self.drafts.pop(m.group(1), None)
            if gone is None:
                return 404, {"detail": "no such case"}
            return 200, {**gone, "status": "withdrawn", "opened_at": self.opened_by_then and NOW.isoformat()}
        if m and m.group(2) == "status":
            status = self.move_status.pop(0) if self.move_status else 200
            if status != 200:
                return status, {"detail": {403: "only the case's queue changes its status",
                                           409: "a closed case cannot become acknowledged"}.get(status, "boom")}
            return 200, {"case_id": m.group(1), "status": body["status"]}
        if (method, path) == ("POST", "/v1/desk"):
            return self.desk_replies.pop(0) if self.desk_replies else (200, self.desk_answer(body))
        return 404, {"detail": "Not Found"}


def load(st, http, tenant="acme", chat_url=CHAT, render=None) -> dict:
    """The page's module, its imports replaced: streamlit, requests, auth's tenant_for, chat.py's URL, headers and
    citation shape, citations.py's renderer."""
    tree = ast.parse(PAGE.read_text(encoding="utf-8"))
    local = {"auth", "chat", "citations"}
    body = [n for n in tree.body
            if not (isinstance(n, ast.ImportFrom) and n.module in local)
            and not (isinstance(n, ast.Import) and {a.name for a in n.names} & {"streamlit", "requests"})]
    audiences = []
    ns = {"__name__": "desk_page_under_test", "st": st, "requests": http,
          "tenant_for": tenant if callable(tenant) else (lambda e: tenant), "CHAT_URL": chat_url,
          "_headers": lambda aud: audiences.append(aud) or {"Authorization": "Bearer ui-sa", "x-goog-iap-jwt-assertion": "person"},
          "_as_source": lambda c: {"text": c.get("quote", ""), "source_uri": c.get("source_uri", "")},
          "render_with_citations": render or (lambda answer, sources: st.out.append(("cited", answer)))}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(PAGE), "exec"), ns)
    ns["_audiences"] = audiences
    return ns


def run(ns, st, email=ME) -> str:
    """One page view, rerun as Streamlit reruns it (a button is pressed once)."""
    try:
        for _ in range(4):
            st.out, st.forms, State.drawn = [], [], set()
            try:
                ns["desk_page"]({"email": email})
                st.pressed = set()
                return "drawn"
            except Rerun:
                st.seen += st.out
                st.pressed = set()
            except Stop:
                return "stopped"
        raise AssertionError("the page reran more than three times")
    finally:
        State.drawn = None


def page(service, answers=None, pressed=(), **kw):
    st, http = FakeSt(answers, pressed), Http(service)
    ns = load(st, http, **kw)
    outcome = run(ns, st)
    return st, http, ns, outcome


def posts(http, path="/v1/cases"):
    return [c for c in http.calls if c[:2] == ("POST", path)]


def case_rows(st):
    return [k for k in st.kinds("form") if k.startswith(("desk_new_", "desk_posh", "desk_draft", "desk_move_"))]


# ---------------------------------------------------------------- the tests
class CopiesOfTheKit(unittest.TestCase):
    """The page cannot import shared/ (its image builds from services/frontend alone), so it carries copies."""

    def setUp(self):
        self.ns = load(FakeSt(), Http(Service()))

    def test_none_of_desk_laws_wording(self):
        """The fixed replies, the clocks and the law a case rests on come from the service, read from desk_law when it
        runs: a copy here would go stale when that wording changes."""
        # every string in the page, the pieces Python joins (adjacent literals, f-strings' text) joined, spaces folded
        source = re.sub(r"\s+", " ", "\n".join(n.value for n in ast.walk(ast.parse(PAGE.read_text(encoding="utf-8")))
                                               if isinstance(n, ast.Constant) and isinstance(n.value, str)))

        def texts(v):
            if isinstance(v, str):
                yield v
            elif isinstance(v, dict):
                for x in v.values():
                    yield from texts(x)
            elif isinstance(v, (list, tuple, set, frozenset)):
                for x in v:
                    yield from texts(x)

        sentences = {p.strip() for name in ("TEMPLATES", "CLOCKS", "BASIS", "NOWHERE")
                     for t in texts(getattr(desk_law, name)) for p in re.split(r"(?<=[.:])\s+|\n+", t)
                     if len(p.strip()) >= 30}
        self.assertGreater(len(sentences), 30)
        for sentence in sentences:
            self.assertNotIn(sentence, source)
        for name in ("GATE_OPENINGS", "gate_class", "TEMPLATES", "CLOCKS", "company_settings", "_roster_db"):
            self.assertNotIn(name, self.ns)
        for read in ("tenant_settings", ".collection(", "_roster_db"):
            self.assertNotIn(read, PAGE.read_text(encoding="utf-8"), "the page reads Firestore itself")

    def test_the_queues_and_case_types(self):
        self.assertEqual(self.ns["QUEUES"], {q: {k: tuple(spec[k]) for k in ("read", "status", "opt_in")}
                                             for q, spec in desk_law.QUEUES.items()})
        self.assertEqual(list(self.ns["CASE_TYPES"]), list(desk_law.CASE_TYPES))
        self.assertEqual(list(self.ns["CASE_NAMES"]), list(desk_law.CASE_TYPES))
        self.assertEqual(set(self.ns["START"]), set(desk_law.CASE_TYPES) - {"posh"}, "a button for every other kind")
        self.assertLessEqual(set(desk_rules.CLASSES), set(desk_law.CASE_TYPES), "every gate class is a kind of case")
        self.assertEqual(self.ns["NEXT"], cases.NEXT)
        self.assertEqual(set(self.ns["STATUS"]), set(cases.STATUSES))
        self.assertEqual(set(self.ns["MOVE"]), {s for nxt in cases.NEXT.values() for s in nxt})
        self.assertEqual((self.ns["IC_QUEUE"], self.ns["UNREAD"], self.ns["EMPLOYEE"], self.ns["SUMMARY_MAX"]),
                         (desk_law.IC_QUEUE, roles.UNREAD, roles.EMPLOYEE, cases.SUMMARY_MAX))
        self.assertTrue(roles.IC_ROLE.match(self.ns["IC_ROLE"] + "hyderabad"))
        door = ROUTES.read_text(encoding="utf-8")
        self.assertIn(f"QUESTION_MAX = {self.ns['QUESTION_MAX']}", door)
        self.assertIn('"brain": "desk_gate", "model": meter.model', door, "the reply the page recognises as the door's")
        self.assertIn('method, meter = "rule", limits.Meter(model="none")', door, "a rule's reply says model none")
        self.assertIn('"case_offer": {"case_type": cls}', door, "the case a fixed reply offers")

    def test_the_fake_answers_with_the_routes_fields(self):
        tree = ast.parse(ROUTES.read_text(encoding="utf-8"))

        def returned(fn):
            node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == fn)
            ret = [n for n in ast.walk(node) if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict)][-1]
            return [k.value for k in ret.value.keys]

        svc = Service()
        self.assertEqual(returned("case_offer"), list(svc.offer()))
        self.assertEqual(returned("list_cases"), list(svc("GET", "/v1/cases", None)[1]))
        self.assertEqual(svc.offer()["posh"]["pune"]["local_committee"]["contact"], "lc.pune@example.com")


class Identity(unittest.TestCase):
    def test_nothing_for_someone_the_service_saw_instead(self):
        inbox = [record("grievance", "grc", "alice@example.com", summary="Shouted at in the review.")]
        mine = [record("grievance", "grc", "ui-sa@example.com")]
        for svc in (Service(roles=["employee", "grc_member"], inbox=inbox, mine=mine, seen_as="ui-sa@example.com"),
                    Service(roles=["employee", "grc_member"], inbox=inbox, mine=mine, seen_as=None),
                    Service(roles=["employee", "grc_member"], inbox=inbox, mine=mine, offer_status=503,
                            seen_as="ui-sa@example.com"),
                    Service(roles=["employee", "grc_member"], inbox=inbox, mine=mine, list_status=503,
                            seen_as="ui-sa@example.com")):
            st, http, _, outcome = page(svc, answers={"What is it about?": "grievance"})
            self.assertEqual(outcome, "drawn")
            self.assertEqual(len(st.kinds("warning")), 1)
            self.assertIn("sign-in (IAP)", st.kinds("warning")[0])
            self.assertEqual(st.kinds("subheader"), [], "no section is drawn")
            self.assertEqual(case_rows(st) + st.kinds("expander") + st.kinds("widget"), [])
            for seen in ("alice@", "Shouted at", "ui-sa@"):
                self.assertNotIn(seen, st.text())
            self.assertEqual([c[:2] for c in http.calls if c[0] == "POST"], [])

    def test_the_offer_is_read_for_the_persons_company(self):
        zeta = ZCFG["posh"]["units"]["head_office"]["local_committee"]["contact"]
        st, http, *_ = page(Service(tenant="zeta", queues=ZCFG), answers={"What is it about?": "posh"}, tenant="zeta")
        self.assertIn(zeta, st.text())
        self.assertEqual(st.options["Your office"], [ZCFG["posh"]["units"]["head_office"]["name"]])
        for acme in ("lc.hyderabad@", "lc.pune@", "Hyderabad"):
            self.assertNotIn(acme, st.text())
        self.assertEqual([c[:2] for c in http.calls], [("GET", "/v1/cases/offer"), ("GET", "/v1/cases")])
        # the service answered for another company than the roster gave this person: nothing is drawn
        st, *_ = page(Service(tenant="acme"), answers={"What is it about?": "posh"}, tenant="zeta")
        self.assertIn("sign-in (IAP)", st.kinds("warning")[0])
        self.assertNotIn("lc.hyderabad@", st.text())


class Inbox(unittest.TestCase):
    def test_lists_only_the_readers_queue(self):
        inbox = [record("grievance", "grc", "alice@example.com", summary="Shouted at in the review."),
                 record("exit_dues", "payroll", "bob@example.com"),
                 record("posh", "ic:hyderabad", "carol@example.com", unit="hyderabad",
                        chosen_contacts=["ic.hyderabad.member@example.com"]),
                 record("people_query", "people", "dave@example.com"),
                 record("grievance", "grc", "erin@example.com", status="draft"),
                 record("grievance", "grc", "fatima@example.com", opened_at=None)]
        st, http, ns, _ = page(Service(roles=["employee", "grc_member"], inbox=inbox))
        text = st.text()
        self.assertIn("Your inbox", st.kinds("subheader"))
        self.assertIn("alice@example.com", text)
        self.assertIn("Shouted at in the review.", text)
        for other in ("bob@", "carol@", "dave@", "erin@", "fatima@"):
            self.assertNotIn(other, text, "another queue's case, or one never sent, was shown")
        self.assertEqual([k for k in st.kinds("form") if k.startswith("desk_move_")], [f"desk_move_{inbox[0]['case_id']}"])
        self.assertNotIn("Only the latest cases are shown here. Some older ones are not.", st.kinds("caption"))

    def test_people_ops_reads_a_grievance_only_when_shared(self):
        inbox = [record("grievance", "grc", "frank@example.com"),
                 record("grievance", "grc", "gita@example.com", people_ops_opt_in=True),
                 record("exit_dues", "payroll", "hari@example.com"),
                 record("human_requested", "people", "indu@example.com")]
        st, *_ = page(Service(roles=["employee", "people_ops"], inbox=inbox))
        text = st.text()
        self.assertNotIn("frank@", text)
        for shown in ("gita@", "hari@", "indu@"):
            self.assertIn(shown, text)
        moves = [k for k in st.kinds("form") if k.startswith("desk_move_")]
        self.assertEqual(moves, [f"desk_move_{inbox[3]['case_id']}"], "people_ops moves the people queue's cases only")

    def test_a_posh_case_only_for_the_members_chosen(self):
        inbox = [record("posh", "ic:hyderabad", "jaya@example.com", unit="hyderabad", chosen_contacts=[ME]),
                 record("posh", "ic:hyderabad", "kiran@example.com", unit="hyderabad",
                        chosen_contacts=["ic.hyderabad.member@example.com"]),
                 record("posh", "ic:pune", "lata@example.com", unit="pune", chosen_contacts=[ME])]
        st, *_ = page(Service(roles=["employee", "ic_member:hyderabad"], inbox=inbox))
        text = st.text()
        self.assertIn("jaya@", text)
        self.assertNotIn("kiran@", text)
        self.assertNotIn("lata@", text)

    def test_no_queue_role_no_inbox(self):
        stray = [record("grievance", "grc", "mona@example.com")]
        for held in (["employee"], ["leaver"], ["employee", "desk_eval"]):
            st, *_ = page(Service(roles=held, inbox=stray))
            self.assertNotIn("Your inbox", st.kinds("subheader"), held)
            self.assertNotIn("mona@", st.text(), held)
            self.assertIn("Raise a case", st.kinds("subheader"), held)

    def test_says_when_a_list_was_cut(self):
        st, *_ = page(Service(roles=["employee"], mine=[record("grievance", "grc", ME)], more=True))
        self.assertIn("Only the latest cases are shown here. Some older ones are not.", st.kinds("caption"))

    def test_what_a_person_wrote_stays_text(self):
        trap = "![x](https://tracker.example/p.png?who=me) [click here](https://evil.example) # heading <b>bold</b>"
        inbox = [record("grievance", "grc", "olga@example.com", summary=trap)]
        st, *_ = page(Service(roles=["employee", "grc_member"], inbox=inbox))
        raw = "\n".join(st.kinds("markdown"))
        self.assertNotIn("![", raw)
        self.assertNotIn("](", raw)
        self.assertNotIn("<b>", raw)
        self.assertIsNone(re.search(r"(?<!\\)[\[\]()!<>#]", next(t for t in st.kinds("markdown") if "tracker" in t)
                                    .split("**In their words:**", 1)[1]), "every special character escaped")
        self.assertIn(trap, st.text(), "and shown as the person wrote it")


class Moves(unittest.TestCase):
    def test_a_status_move(self):
        case = record("grievance", "grc", "pia@example.com")
        form = f"desk_move_{case['case_id']}"
        for status, said in ((200, ("success", "Updated: Acknowledged (we have seen it).")),
                             (403, ("error", "Only the team this case was sent to can change its status.")),
                             (409, ("error", "This case cannot move to that status now. Please reload the page to see "
                                             "where it is."))):
            svc = Service(roles=["employee", "grc_member"], inbox=[case])
            svc.move_status = [status]
            st, http, *_ = page(svc, answers={"Change the status to": "acknowledged"}, pressed={(form, "Update")})
            moved = posts(http, f"/v1/cases/{case['case_id']}/status")
            self.assertEqual([c[2] for c in moved], [{"status": "acknowledged"}], status)
            self.assertIn(said[1], st.kinds(said[0]), status)
            self.assertNotIn("cannot become", st.text(everything=True), "the service's own words")
            self.assertNotIn("only the case's queue", st.text(everything=True))

    def test_the_draft_send_is_not_the_tell_send(self):
        """Two buttons are labelled Send: the one in the box and the one under a draft. Each is its own."""
        svc = Service(roles=["employee"])
        st, http = FakeSt({"What is it about?": "grievance"}, {("desk_new_grievance", "Next: check it before sending")}), Http(svc)
        ns = load(st, http)
        run(ns, st)
        self.assertIn("desk_draft", st.kinds("form"))
        self.assertIn("desk_tell", st.kinds("form"))
        st.answers["What do you need help with?"] = "notice period?"
        st.pressed = {("desk_tell", "Send")}
        run(ns, st)
        self.assertEqual(len(posts(http, "/v1/chat")), 1)
        self.assertFalse([c for c in http.calls if c[1].endswith("/confirm")], "the draft was sent with the box")
        st.pressed = {SEND}
        run(ns, st)
        self.assertEqual(len(posts(http, "/v1/chat")), 1, "the box was sent with the draft")
        self.assertEqual(len([c for c in http.calls if c[1].endswith("/confirm")]), 1)


class RoleReadFails(unittest.TestCase):
    def test_the_case_form_only(self):
        mine = [record("grievance", "grc", ME)]
        for svc in (Service(list_status=503), Service(list_status=0),
                    Service(roles=[roles.UNREAD], inbox=[record("grievance", "grc", "nina@example.com")], mine=mine,
                            desk_route="on")):
            st, http, ns, outcome = page(svc, answers={"What is it about?": "grievance"})
            self.assertEqual(outcome, "drawn")
            self.assertEqual(st.kinds("subheader"), ["Raise a case"])
            self.assertIn(("widget", "What is it about?"), st.out)
            self.assertIn("desk_new_grievance", st.kinds("form"), "the case form is there")
            self.assertNotIn("desk_tell", st.kinds("form"))
            self.assertNotIn("nina@", st.text())
            self.assertEqual([c[:2] for c in http.calls], [("GET", "/v1/cases/offer"), ("GET", "/v1/cases")])

    def test_nothing_answers(self):
        st, http, _, outcome = page(Service(offer_status=0, list_status=0))
        self.assertEqual((outcome, st.kinds("subheader")), ("drawn", ["Raise a case"]))
        self.assertEqual(st.kinds("info"), ["The Desk could not be reached just now. Please try again in a minute."])
        self.assertEqual(st.kinds("widget"), [])

    def test_the_offer_refused(self):
        inbox = [record("grievance", "grc", "quinn@example.com")]
        st, *_ = page(Service(roles=["grc_member"], inbox=inbox))       # a queue role alone raises no case
        self.assertIn("Your account cannot raise a case here. If you think it should, please ask the People team.",
                      st.kinds("info"))
        self.assertNotIn(("widget", "What is it about?"), st.out)
        self.assertIn("quinn@", st.text(), "the inbox is still there")
        st, *_ = page(Service(offer_status=503))
        self.assertIn("The Desk is not available just now. Please try again in a minute.", st.kinds("info"))
        self.assertNotIn("could not be read", st.text())


class PoshCard(unittest.TestCase):
    def test_always_shows_the_local_committee(self):
        for unit in ("hyderabad", "pune"):
            lc = QCFG["posh"]["units"][unit]["local_committee"]["contact"]
            for chosen in ([], [ME]):
                st, http, ns, _ = page(Service(), answers={"What is it about?": "posh", "Your office": unit,
                                                           "Internal Committee members to contact": chosen},
                                       pressed={("desk_posh", "Create a confidential record")})
                self.assertIn(lc, st.text(), (unit, chosen))
                made = posts(http)
                if not chosen:
                    self.assertEqual(made, [], "a record with nobody to contact was sent")
                    self.assertIn("Choose at least one member to contact.", st.kinds("error"))
                    self.assertIn(ns["POSH_KEEPS"], st.kinds("caption"))
                    continue
                self.assertEqual(len(made), 1)
                self.assertEqual(set(made[0][2]), {"case_type", "unit", "contacts", "token"}, "a POSH record holds no text")
                self.assertEqual((made[0][2]["unit"], made[0][2]["contacts"]), (unit, [ME]))
                self.assertIn("Recorded. Your case reference is", st.text())
                self.assertNotIn("desk_posh", st.kinds("form"), "the panel takes the form's place")
                after = [t for k, t in st.out if k == "markdown" and "Local Committee" in t]
                self.assertGreaterEqual(len(after), 2, "the card and the record both name the Local Committee")

    def test_the_keeps_line(self):
        self.assertEqual(load(FakeSt(), Http(Service()))["POSH_KEEPS"],
                         "The record keeps your name, your office and the members you chose, and none of your words. "
                         "Only those members see it in their inbox.")

    def test_a_press_whose_reply_was_lost_is_pressed_with_the_same_token(self):
        svc = Service()
        svc.posh_status = [0, 503]
        answers = {"What is it about?": "posh", "Your office": "hyderabad", "Internal Committee members to contact": [ME]}
        st, http = FakeSt(answers, {("desk_posh", "Create a confidential record")}), Http(svc)
        ns = load(st, http)
        for _ in range(3):
            st.pressed = {("desk_posh", "Create a confidential record")}
            run(ns, st)
        tokens = [c[2]["token"] for c in posts(http)]
        self.assertEqual(len(tokens), 3)
        self.assertEqual(len(set(tokens)), 1)
        self.assertTrue(cases.TOKEN.match(tokens[0]), "a token the case route takes")
        self.assertIn("Recorded. Your case reference is", st.text())

    def test_the_record_for_its_office_and_record_another(self):
        answers = {"What is it about?": "posh", "Your office": "hyderabad", "Internal Committee members to contact": [ME]}
        st, http = FakeSt(answers, {("desk_posh", "Create a confidential record")}), Http(Service())
        ns = load(st, http)
        run(ns, st)
        self.assertIn("Recorded. Your case reference is", st.text())
        st.answers["Your office"] = "pune"
        run(ns, st)
        self.assertNotIn("Recorded.", st.text(), "the record is shown for its own office only")
        self.assertIn("desk_posh", st.kinds("form"))
        st.answers["Your office"] = "hyderabad"
        run(ns, st)
        self.assertIn("Recorded.", st.text())
        self.assertIn("Record another", st.kinds("button"))
        st.pressed = {("desk_posh_another", "Record another")}
        run(ns, st)
        self.assertNotIn("Recorded.", st.text())
        self.assertIn("desk_posh", st.kinds("form"))
        st.pressed = {("desk_posh", "Create a confidential record")}
        run(ns, st)
        tokens = [c[2]["token"] for c in posts(http)]
        self.assertEqual(len(tokens), 2)
        self.assertNotEqual(tokens[0], tokens[1], "another record is another case")

    def test_a_refusal_keeps_the_contacts_on_the_card(self):
        unit = QCFG["posh"]["units"]["pune"]
        for held, status in (([], 409), (["employee"], 409), ([roles.UNREAD], 503)):
            svc = Service()
            svc.ic_roles = held
            st, http, *_ = page(svc, answers={"What is it about?": "posh", "Your office": "pune",
                                              "Internal Committee members to contact": [ME]},
                                pressed={("desk_posh", "Create a confidential record")})
            status_got, body = posh_refusal(http.calls[-1][2], held)
            self.assertEqual(status_got, status)
            detail = body["detail"]
            self.assertEqual(st.kinds("error"), [detail[:1].upper() + detail[1:]], held)
            self.assertFalse(st.kinds("success"))
            text = st.text()
            for m in unit["ic"]:
                self.assertIn(f"{m['name']} ({m['email']})", text, "the members' contacts stay on the card")
            self.assertIn(unit["local_committee"]["contact"], text, "the Local Committee stays on the card")
            errors = [i for i, row in enumerate(st.out) if row[0] == "error"]
            lc = [i for i, row in enumerate(st.out)
                  if unit["local_committee"]["contact"] in re.sub(r"\\(.)", r"\1", row[1])]
            self.assertLess(lc[0], errors[0], "the contacts are above the refusal")
        self.assertIn("contact them, or the Local Committee, directly", posh_refusal(
            {"unit": "pune", "contacts": [ME], "token": "t" * 16}, ["employee"])[1]["detail"])

    def test_another_refusal_is_told_plainly(self):
        svc = Service()
        svc.posh_status = [403]
        st, *_ = page(svc, answers={"What is it about?": "posh", "Your office": "pune",
                                    "Internal Committee members to contact": [ME]},
                      pressed={("desk_posh", "Create a confidential record")})
        self.assertEqual(st.kinds("error"), ["Your account cannot do this here. If you think it should, please ask the "
                                             "People team."])

    def test_no_posh_section(self):
        bare = {k: v for k, v in QCFG.items() if k != "posh"}
        st, http, *_ = page(Service(queues=bare, gate="posh"), answers={"What do you need help with?": DISCLOSURE},
                            pressed={("desk_tell", "Send")})
        self.assertNotIn(load(FakeSt(), Http(Service()))["CASE_TYPES"]["posh"], st.options["What is it about?"])
        self.assertNotIn("Your office", st.kinds("widget"))
        self.assertIn("Your company has not set up this kind of case here yet. Please contact the People team directly.",
                      st.kinds("caption"))
        self.assertIn(desk_law.TEMPLATES["posh"].split("\n\n")[1], st.text(), "the fixed reply names the committees")

    def test_no_units_in_the_offer(self):
        st = FakeSt()
        ns = load(st, Http(Service()))
        ns["posh_card"]({})
        self.assertTrue(st.kinds("warning"))
        self.assertIn("Local Committee of your district", st.kinds("warning")[0])
        self.assertNotIn("Your office", st.kinds("widget"))


class TellTheDesk(unittest.TestCase):
    def test_a_posh_gate_hit_opens_the_card_at_once(self):
        self.assertEqual(desk_rules.gate(DISCLOSURE), "posh")
        st, http = FakeSt({"What do you need help with?": DISCLOSURE}, {("desk_tell", "Send")}), Http(Service(gate="posh"))
        ns = load(st, http)
        run(ns, st)
        self.assertEqual([c[:2] for c in http.calls], [("GET", "/v1/cases/offer"), ("GET", "/v1/cases"), ("POST", "/v1/chat")])
        sent = http.calls[2][2]
        self.assertEqual((sent["question"], sent["brain"]), (DISCLOSURE, "direct"))
        self.assertEqual(ns["_audiences"], [CHAT] * 3, "every call carries chat.py's two credentials for the chat service")
        for para in desk_law.TEMPLATES["posh"].split("\n\n"):
            self.assertIn(para, st.text(), "the door's reply, as it came")
        self.assertIn("This is a fixed reply. No AI model was used. To reach a person, raise the case below. A case "
                      "does not include what you typed here.", st.kinds("caption"))
        self.assertIn("Your office", st.kinds("widget"), "the POSH card, at once")
        self.assertIn(QCFG["posh"]["units"]["hyderabad"]["local_committee"]["contact"], st.text())
        self.assertEqual(posts(http), [], "no case is opened by itself")
        # the next view still shows the reply and the card; recording it carries no words
        st.answers["Internal Committee members to contact"] = [ME]
        st.pressed = {("desk_posh", "Create a confidential record")}
        run(ns, st)
        self.assertEqual(set(posts(http)[0][2]), {"case_type", "unit", "contacts", "token"})
        self.assertNotIn(DISCLOSURE, st.text(everything=True), "the disclosure was shown back")
        self.assertNotIn("sexual comments", repr(dict(st.session_state)), "the disclosure was kept in the session")
        self.assertNotIn("sexual comments", json.dumps([c[2] for c in http.calls[3:]]), "the disclosure reached a case")

    def test_each_other_class_offers_its_case(self):
        for cls in sorted(set(desk_rules.CLASSES) - {"posh"}):
            words = f"words about {cls} I typed"
            st, http = FakeSt({"What do you need help with?": words}, {("desk_tell", "Send")}), Http(Service(gate=cls))
            ns = load(st, http)
            run(ns, st)
            self.assertIn(desk_law.TEMPLATES[cls].split("\n\n")[-1], st.text(), cls)
            self.assertIn(ns["START"][cls], st.kinds("button"), cls)
            self.assertFalse([k for k in st.kinds("form") if k.startswith("desk_new_")], "nothing starts by itself")
            st.pressed = {("desk_start", ns["START"][cls])}
            run(ns, st)
            self.assertIn(f"desk_new_{cls}", st.kinds("form"), cls)
            self.assertEqual(st.values["In your own words (you can change this before sending)"], "",
                             "the typed words are not put in the case")
            self.assertEqual([c[:2] for c in http.calls if c[0] == "POST"], [("POST", "/v1/chat")], cls)
            self.assertNotIn(words, st.text(everything=True))

    def test_another_answer_is_shown_as_the_chat_page_shows_it(self):
        st, *_ = page(Service(), answers={"What do you need help with?": "notice period?"}, pressed={("desk_tell", "Send")})
        self.assertEqual([t for k, t in st.out if k == "cited"], ["Sixty days &lt;b&gt;[1]&lt;/b&gt;."])
        self.assertNotIn("Your office", st.kinds("widget"))

    def test_a_renderer_that_fails_shows_the_answer_plainly(self):
        def broken(answer, sources):
            raise KeyError("page")
        st, *_ = page(Service(), answers={"What do you need help with?": "notice period?"},
                      pressed={("desk_tell", "Send")}, render=broken)
        self.assertIn("Sixty days <b>[1]</b>.", st.kinds("markdown"))

    def test_a_hit_the_model_check_found_says_a_model_read_it(self):
        st, http = (FakeSt({"What do you need help with?": "words the rules let through"}, {("desk_tell", "Send")}),
                    Http(Service(gate="grievance", gate_model="gemini-3.1-flash-lite")))
        ns = load(st, http)
        run(ns, st)
        self.assertIn(desk_law.TEMPLATES["grievance"].split("\n\n")[-1], st.text())
        self.assertIn("This is a fixed reply. An AI model read your message only to decide that it should go to a person; "
                      "it wrote nothing. To reach a person, raise the case below. A case does not include what you "
                      "typed here.", st.kinds("caption"))
        self.assertNotIn("No AI model was used.", " ".join(st.kinds("caption")))
        self.assertIn(ns["START"]["grievance"], st.kinds("button"), "the case it offers, as for a rule's reply")

    def test_the_box_with_the_rules_alone(self):
        st, http, *_ = page(Service(desk_gate="rules"), answers={"What do you need help with?": DISCLOSURE},
                            pressed={("desk_tell", "Send")})
        self.assertIn("desk_tell", st.kinds("form"))
        self.assertEqual(len(posts(http, "/v1/chat")), 1)

    def test_no_box_while_the_gate_is_off(self):
        for svc in (Service(desk_gate="off"), Service(offer_status=503)):
            st, http, *_ = page(svc, answers={"What do you need help with?": DISCLOSURE}, pressed={("desk_tell", "Send")})
            self.assertNotIn("desk_tell", st.kinds("form"))
            self.assertEqual(posts(http, "/v1/chat"), [])
            self.assertIn("Raise a case", st.kinds("subheader"))

    def test_only_an_employee_gets_the_box(self):
        for held, box in ((["employee"], True), (["employee", "grc_member"], True), (["leaver"], False),
                          ([roles.UNREAD], False)):
            st, *_ = page(Service(roles=held), answers={"What is it about?": "grievance"})
            self.assertEqual("desk_tell" in st.kinds("form"), box, held)
            self.assertIn("desk_new_grievance", st.kinds("form"), "every one of them can raise a case")

    def test_a_refusal_never_repeats_the_question(self):
        question = "My Aadhaar is 2345 6789 0123 and my manager shouts"
        for reply in ((422, {"detail": [{"type": "string_too_long", "loc": ["body", "question"], "msg": "too long",
                                         "input": question}]}),
                      (422, {"detail": f"question: {question!r} is not allowed"}),
                      (403, {"detail": f"not a member: {question}"}),
                      (500, {"detail": question})):
            svc = Service()
            svc.chat_reply = reply
            st, *_ = page(svc, answers={"What do you need help with?": question}, pressed={("desk_tell", "Send")})
            self.assertEqual(len(st.kinds("error")), 1, reply)
            self.assertNotIn("2345", st.text(everything=True), reply)
            self.assertNotIn("shouts", st.text(everything=True), reply)


class RoutedHalf(unittest.TestCase):
    def test_hidden_while_desk_route_is_off_or_absent(self):
        for svc, shown in ((Service(), False), (Service(desk_route="shadow"), False),
                           (Service(offer_status=503, desk_route="on"), False),
                           (Service(roles=["leaver"], desk_route="on"), False),
                           (Service(desk_route="on"), True), (Service(desk_route="single"), True)):
            st, http = FakeSt(), Http(svc)
            ns = load(st, http)
            called = []
            ns["routed_half"] = lambda tenant, offer: called.append(tenant)
            run(ns, st)
            self.assertEqual(called, ["acme"] if shown else [], svc.desk_route)
        st = FakeSt()
        ns = load(st, Http(Service()))
        ns["routed_half"]("acme", {"desk_route": "on"})
        self.assertEqual(st.out, [], "the routed half draws nothing without an employee's offer")

    def test_ask_the_desk_in_place_of_tell_the_desk(self):
        asked = "What is the notice period for a confirmed E3?"
        st, http, ns, _ = page(Service(desk_route="on"), answers={"Your question": asked}, pressed={("desk_ask", "Ask")})
        self.assertEqual(st.kinds("subheader")[:2], ["Ask the Desk", "Raise a case"])
        self.assertNotIn("desk_tell", st.kinds("form"), "one box, not two")
        self.assertEqual(posts(http, "/v1/chat"), [])
        (sent,) = [c[2] for c in posts(http, "/v1/desk")]
        self.assertEqual(sent, {"question": asked, "session_id": st.session_state["desk_session"]})
        self.assertEqual([t for k, t in st.out if k == "cited"], ["Sixty days &lt;b&gt;[1]&lt;/b&gt;."])
        self.assertNotIn(asked, st.text(everything=True), "the question was shown back")
        self.assertNotIn("confirmed E3", repr(dict(st.session_state)), "the question was kept in the session")
        self.assertEqual(ns["_audiences"], [CHAT] * 3)
        for svc in (Service(desk_route="off"), Service(desk_route="shadow"), Service(roles=["leaver"], desk_route="on")):
            st, http, *_ = page(svc, answers={"Your question": asked}, pressed={("desk_ask", "Ask")})
            self.assertNotIn("Ask the Desk", st.kinds("subheader"), svc.desk_route)
            self.assertEqual(posts(http, "/v1/desk"), [])

    def test_a_posh_reply_opens_the_card_at_once(self):
        svc = Service(desk_route="on")
        svc.desk_replies = [(200, svc.desk_answer({}, route="case", method="rule", outcome="case", sections=[],
                                                  citations=[], answer=desk_law.template("posh"), model_calls=0,
                                                  case_offer={"case_type": "posh", "configured": True,
                                                              "posh": svc.offer()["posh"]}))]
        st, http, *_ = page(svc, answers={"Your question": DISCLOSURE}, pressed={("desk_ask", "Ask")})
        for para in desk_law.TEMPLATES["posh"].split("\n\n"):
            self.assertIn(para, st.text())
        self.assertIn("Your office", st.kinds("widget"), "the POSH card, at once")
        self.assertIn(QCFG["posh"]["units"]["hyderabad"]["local_committee"]["contact"], st.text())
        self.assertEqual(posts(http), [], "no case is opened by itself")
        self.assertNotIn(DISCLOSURE, st.text(everything=True))
        self.assertNotIn("sexual comments", repr(dict(st.session_state)))

    def test_a_drafted_case_waits_under_raise_a_case(self):
        svc = Service(desk_route="on")
        draft = record("people_query", "people", ME, status="draft", summary="Who decides my notice exception?")
        svc.desk_replies = [(200, svc.desk_answer({}, route="case", method="model", outcome="case", sections=[],
                                                  citations=[], answer="This needs a person.", case=draft,
                                                  case_offer={"case_type": "people_query"}))]
        st, http, ns, _ = page(svc, answers={"Your question": "Who decides my notice exception?"},
                               pressed={("desk_ask", "Ask")})
        self.assertIn("desk_draft", st.kinds("form"))
        self.assertNotIn(ns["START"]["people_query"], st.kinds("button"), "drafted already: no second start")
        st.answers["Your question"], st.pressed = "And my leave?", {("desk_ask", "Ask")}
        run(ns, st)
        self.assertEqual(posts(http, "/v1/desk")[-1][2]["draft_id"], draft["case_id"], "the draft the page shows")

    def test_the_chips_ask_another_desk_or_start_a_case(self):
        svc = Service(desk_route="on")
        chips = [{"desk": "statute", "label": "x"}, {"desk": "case", "label": "y"}, {"desk": "tools", "label": "z"}]
        svc.desk_replies = [(200, svc.desk_answer({}, chips=chips))]
        st, http, ns, _ = page(svc, answers={"Your question": "notice?"}, pressed={("desk_ask", "Ask")})
        self.assertEqual([b for b in st.kinds("button") if b in ns["ROUTED_CHIPS"].values()],
                         ["Ask what the law says", "Raise a case"])
        st.pressed = {("desk_chip_statute", "Ask what the law says")}
        run(ns, st)
        self.assertEqual(posts(http, "/v1/desk")[-1][2], {"chip": "statute", "session_id": st.session_state["desk_session"]})
        # a reply DocuMind did not keep (out of scope): its case chip starts the case here, with nothing typed in it
        svc.desk_replies = [(200, svc.desk_answer({}, route="out_of_scope", outcome="oos", sections=[], citations=[],
                                                  answer="Outside what the desks answer.",
                                                  chips=[{"desk": "case", "label": "Raise a case"}]))]
        st.answers["Your question"], st.pressed = "Please apply my leave", {("desk_ask", "Ask")}
        run(ns, st)
        before = len(posts(http, "/v1/desk"))
        st.pressed = {("desk_chip_case", "Raise a case")}
        run(ns, st)
        self.assertEqual(len(posts(http, "/v1/desk")), before)
        self.assertIn("desk_new_people_query", st.kinds("form"))
        self.assertEqual(st.values["In your own words (you can change this before sending)"], "")

    def test_a_reply_for_someone_else_is_not_shown(self):
        svc = Service(desk_route="on")
        svc.desk_replies = [(200, svc.desk_answer({}, email="ui-sa@example.com"))]
        st, *_ = page(svc, answers={"Your question": "notice?"}, pressed={("desk_ask", "Ask")})
        self.assertIn("sign-in (IAP)", st.kinds("warning")[0])
        self.assertNotIn("Sixty days", st.text())
        self.assertNotIn("desk_routed", st.session_state)

    def test_a_refusal_is_told_plainly(self):
        question = "My Aadhaar is 2345 6789 0123 and my manager shouts"
        for reply, said in (((409, {"detail": "that choice is not on offer"}), "That choice is no longer on offer."),
                            ((422, {"detail": [{"input": question}]}), "Please check what you entered"),
                            ((403, {"detail": f"no: {question}"}), "Your account cannot do this here."), ((0, None), "")):
            svc = Service(desk_route="on")
            svc.desk_replies = [reply]
            st, *_ = page(svc, answers={"Your question": question}, pressed={("desk_ask", "Ask")})
            self.assertEqual(len(st.kinds("error")), 1, reply)
            self.assertIn(said, st.kinds("error")[0])
            self.assertNotIn("2345", st.text(everything=True), reply)

    def test_odd_desk_answers_never_raise(self):
        svc = Service(desk_route="single")
        svc.desk_replies = [(200, svc.desk_answer({}, sections=["x", {"title": 5, "answer": None, "citations": "y"}],
                                                  chips=5, case_offer=[], case="draft", note=None, route=["case"]))]
        st, _, _, outcome = page(svc, answers={"Your question": "notice?"}, pressed={("desk_ask", "Ask")})
        self.assertEqual(outcome, "drawn")
        self.assertIn("Raise a case", st.kinds("subheader"))

    def test_the_chip_labels_and_the_fakes_fields_are_the_services(self):
        sys.path.insert(0, str(KIT / "services" / "chat"))
        try:
            import desk_routes
        finally:
            sys.path.remove(str(KIT / "services" / "chat"))
        ns = load(FakeSt(), Http(Service()))
        self.assertEqual(ns["ROUTED_CHIPS"], {d: desk_routes.DESKS[d]["chip"] for d in ("handbook", "statute", "case")})
        tree = ast.parse(ROUTES.read_text(encoding="utf-8"))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "desk_turn")
        ret = [n for n in ast.walk(node) if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict)][-1]
        self.assertEqual([k.value for k in ret.value.keys], list(Service().desk_answer({})))


class Drafts(unittest.TestCase):
    def test_edit_send_and_one_token(self):
        svc = Service(roles=["employee"])
        st, http = FakeSt({"What is it about?": "grievance", "In your own words (you can change this before sending)":
                           "First words.", "Also share this with the HR team": True},
                          {("desk_new_grievance", "Next: check it before sending")}), Http(svc)
        ns = load(st, http)
        run(ns, st)
        made = [c[2] for c in posts(http)]
        self.assertEqual(made, [{"case_type": "grievance", "summary": "First words.", "people_ops_opt_in": True}])
        self.assertIn("desk_draft", st.kinds("form"))
        self.assertIn("Grievance Redressal Committee", st.text(), "who it goes to")
        self.assertIn(desk_law.BASIS["ir_s4_1"]["says"], st.text(), "the law it rests on")
        svc.confirm_status = [503]
        st.answers["In your own words (you can change this)"] = "Edited words."
        st.pressed = {SEND}
        run(ns, st)
        self.assertIn("desk_draft", st.kinds("form"), "a failed send keeps the draft")
        self.assertIn("The Desk is not available just now. Please try again in a minute.", st.kinds("error"))
        st.pressed = {SEND}
        run(ns, st)
        sends = [c for c in http.calls if c[1].endswith("/confirm")]
        self.assertEqual(len(sends), 2)
        self.assertEqual(sends[0][2]["token"], sends[1][2]["token"], "the same draft is sent with one token")
        self.assertTrue(cases.TOKEN.match(sends[0][2]["token"]), "a token the confirm route takes")
        self.assertEqual(sends[1][2]["summary"], "Edited words.")
        self.assertNotIn("desk_draft", st.kinds("form"))
        self.assertTrue(any(t.startswith("Sent. Your case reference is") for t in st.kinds("success")))

    def test_the_target_date_and_its_clock(self):
        mine = [record("grievance", "grc", ME)]
        self.assertTrue(mine[0]["due_at"] and mine[0]["clock"])
        st, *_ = page(Service(mine=mine))
        rows = st.out
        i = next(n for n, (k, t) in enumerate(rows) if k == "markdown" and t.startswith("**Target date:**"))
        self.assertEqual([re.sub(r"\\(.)", r"\1", t) for k, t in rows[i + 1:i + 1 + len(mine[0]["clock"])]],
                         mine[0]["clock"], "the clock lines, beneath the date")
        self.assertNotIn("Reply expected by", st.text())

    def test_cancel(self):
        svc = Service(roles=["employee"])
        nxt = ("desk_new_human_requested", "Next: check it before sending")
        st, http = FakeSt({"What is it about?": "human_requested"}, {nxt}), Http(svc)
        ns = load(st, http)
        run(ns, st)
        st.pressed = {("desk_draft", "Cancel this request")}
        run(ns, st)
        self.assertTrue(any(c[1].endswith("/cancel") for c in http.calls))
        self.assertIn("Cancelled. Nothing was sent.", st.kinds("success"))
        self.assertNotIn("desk_draft", st.kinds("form"))
        self.assertEqual(svc.drafts, {}, "the draft is deleted")
        # a draft already gone (cancelled in another tab, or expired) is a 404: the page lets it go the same way
        st.pressed = {nxt}
        run(ns, st)
        svc.drafts.clear()
        st.pressed = {("desk_draft", "Cancel this request")}
        run(ns, st)
        self.assertIn("Cancelled. Nothing was sent.", st.kinds("success"))
        self.assertNotIn("desk_draft", st.kinds("form"))
        # a Send whose reply never arrived opened the case after all: Cancel then withdraws it, and says so
        st.pressed = {nxt}
        run(ns, st)
        svc.opened_by_then = True
        st.pressed = {("desk_draft", "Cancel this request")}
        run(ns, st)
        self.assertIn("Withdrawn. The team sees that you withdrew it.", st.kinds("success"))

    def test_an_expired_draft_gives_the_words_back(self):
        for status, said in ((410, "a request is kept for 30 minutes only"), (404, "it could not be found any more")):
            svc = Service(roles=["employee"])
            nxt = ("desk_new_grievance", "Next: check it before sending")
            st, http = FakeSt({"What is it about?": "grievance", "In your own words (you can change this before "
                               "sending)": "First words.", "Also share this with the HR team": True}, {nxt}), Http(svc)
            ns = load(st, http)
            run(ns, st)
            # while the draft waits, the person looks at another kind and rewrites the words in the draft
            st.answers = {"In your own words (you can change this)": "Edited words, written over ten minutes."}
            st.session_state["desk_kind"] = "people_query"
            svc.confirm_status = [status]
            st.pressed = {SEND}
            run(ns, st)
            self.assertTrue(any(said in t for t in st.kinds("error")), status)
            self.assertNotIn("desk_draft", st.kinds("form"))
            self.assertIn("desk_new_grievance", st.kinds("form"), "the same kind, ready again")
            self.assertEqual(st.values["In your own words (you can change this before sending)"],
                             "Edited words, written over ten minutes.", "never an empty form")
            self.assertIs(st.values["Also share this with the HR team"], True)
            st.pressed = {nxt}
            run(ns, st)
            self.assertEqual(posts(http)[-1][2], {"case_type": "grievance", "people_ops_opt_in": True,
                                                  "summary": "Edited words, written over ten minutes."})
            self.assertIn("desk_draft", st.kinds("form"))
            self.assertNotIn("desk_refill", st.session_state, "the words are let go once they are a draft again")

    def test_an_expired_exit_dues_draft_keeps_its_date(self):
        svc = Service(roles=["employee"])
        st, http = FakeSt({"Your last working day": date(2026, 9, 25)},
                          {("desk_new_exit_dues", "Next: check it before sending")}), Http(svc)
        st.session_state["desk_kind"] = "exit_dues"
        ns = load(st, http)
        run(ns, st)
        del st.answers["Your last working day"]
        svc.confirm_status = [410]
        st.pressed = {SEND}
        run(ns, st)
        self.assertEqual(st.values["Your last working day"], date(2026, 9, 25))

    def test_a_draft_sent_elsewhere(self):
        svc = Service(roles=["employee"])
        st, http = FakeSt({"What is it about?": "people_query"},
                          {("desk_new_people_query", "Next: check it before sending")}), Http(svc)
        ns = load(st, http)
        run(ns, st)
        svc.confirm_status = [409]
        st.pressed = {SEND}
        run(ns, st)
        self.assertEqual(st.kinds("error"), ["This request was already sent or cancelled. Look for it under Your cases."])
        self.assertNotIn("already open", st.text())


class ThePage(unittest.TestCase):
    def test_a_person_on_no_roster(self):
        st, http = FakeSt(), Http(Service())
        ns = load(st, http, tenant=None)
        self.assertEqual(run(ns, st), "stopped")
        self.assertEqual(http.calls, [])
        self.assertIn("not a member", st.kinds("error")[0])

    def test_the_roster_cannot_be_read(self):
        def unwell(email):
            raise RuntimeError("Firestore is unwell")
        st, http = FakeSt(), Http(Service())
        ns = load(st, http, tenant=unwell)
        self.assertEqual(run(ns, st), "stopped")
        self.assertEqual(st.kinds("error"), ["Your account could not be checked just now. Please try again in a minute."])
        self.assertEqual(http.calls, [])

    def test_plain_words_for_each_status(self):
        ns = load(FakeSt(), Http(Service()))
        for status in (0, 401, 403, 404, 409, 413, 422, 501, 503, 500):
            said = ns["_problem"](status)
            self.assertTrue(said.endswith(".") and "detail" not in said, status)
        self.assertEqual(ns["_posh_problem"](409, {"detail": "none of the members you chose can receive a case"}),
                         "None of the members you chose can receive a case")
        self.assertEqual(ns["_posh_problem"](422, {"detail": "not on the pune Internal Committee: ['x']"}),
                         ns["_problem"](422))

    def test_odd_answers_never_raise(self):
        odd = {"case_id": ["x"], "case_type": ["grievance"], "status": {"a": 1}, "queue": "grc", "opened_at": "soon",
               "due_at": "9999-12-31T23:59:00+00:00", "clock": "one line", "basis": ["not a dict"], "owner": "nobody",
               "summary": 7, "requester": None}
        svc = Service(roles=["employee", "grc_member"], inbox=[odd, "row"], mine=[odd, None])
        svc.offer = lambda: {"email": ME, "tenant": "acme", "roles": ["employee"], "desk_gate": "on",
                             "desk_route": ["on"], "types": [["posh"], "grievance", None], "posh": ["not", "a", "map"]}
        st, http, _, outcome = page(svc, answers={"What is it about?": "grievance"})
        self.assertEqual(outcome, "drawn")
        self.assertEqual(st.options["What is it about?"], [load(FakeSt(), Http(Service()))["CASE_TYPES"]["grievance"]])
        self.assertIn("Your cases", st.kinds("subheader"))
        self.assertFalse([c for c in st.kinds("caption") if len(c) <= 2], "a clock that is not a list, drawn by letter")
        odd.update({"chosen_contacts": 5, "basis": 5, "clock": 5, "owner": {"members": 5}, "queue": "ic:pune"})
        svc = Service(roles=["employee", "ic_member:pune"], inbox=[odd], mine=[odd])
        svc.offer = lambda: {"email": ME, "tenant": "acme", "roles": 5, "desk_gate": "on", "desk_route": "off",
                             "types": ["posh"], "posh": {"pune": {"name": "Pune", "members": 5, "local_committee": 5}}}
        st, *_ = page(svc, answers={"What is it about?": "posh"})
        self.assertIn("not added yet. Please ask the People team.", st.text())
        svc = Service()
        svc.offer = lambda: {"email": ME, "tenant": "acme", "roles": 5, "types": 5, "posh": 5}
        svc.mine = svc.inbox = 5
        st, _, _, outcome = page(svc)
        self.assertEqual(outcome, "drawn")
        self.assertIn("Your company has not set up any kind of case here yet. Please contact the People team directly.",
                      st.kinds("info"))

    def test_no_chat_service(self):
        st, http = FakeSt(), Http(Service())
        ns = load(st, http, chat_url="")
        run(ns, st)
        self.assertEqual(st.kinds("subheader"), ["Raise a case"])
        self.assertEqual(http.calls, [])

    def test_app_wiring(self):
        app = APP.read_text(encoding="utf-8")
        self.assertIn("from desk import desk_page\n", app)
        self.assertIn('pages = ["Chat", "Documents", "Studio", "Admin"] if is_admin(user) else ["Chat", "Documents", "Studio"]\n'
                      'pages.insert(1, "Desk")', app)
        self.assertIn('elif page == "Desk":\n    desk_page(user)\n', app)
        self.assertIn('pages = ["Chat", "Documents", "Studio", "Admin"]', app, "lesson 7.6's build asserts this")


if __name__ == "__main__":
    unittest.main()
