"""The Case Room (Phase 1, after Module 10): one full and final case carried by a team of agents on a typed board,
commands/case_room.py, and its bench, evals/case_eval.py's runs, scores and pairs.

    python -m unittest commands/tests/test_case_room.py -v           # from deploy/
    make case-tests                                                    # the same, in ~/graph-venv with the chat pins

The first half needs the standard library only and runs in CI's shared interpreter: the roster and who writes each
zone; the treasurer's slices and the budget they never pass; check_plan() refusing a plan before any scout runs; the
registrar's rules on evidence (another tenant's passage, a class the role does not read, a passage that does not hold
the claim, a quote not written in it), on derivations (a figure no calculator returned, an argument that is not its
fact, a figure the calculator does not return again, a Code's calculator with no Code on the board), on the draft (a
digit outside a slot, a slot the board does not hold) and on a sign-off (the opener's own, another tenant's, a
rejection with no reason); the front door; the clocks a paused case keeps; the auditor's statuses, points and findings;
the slots and the draft check; the bench's scoring on hand-made records; the make targets, the .PHONY entries, the 888
lines, both CI lines and the UNOWNED.md rows.

The second half runs the three arms on the scripted model over the kit's own corpus and needs the chat image's pins
(pip install -r services/chat/requirements.txt): the baseline case through the swarm with its scouts side by side
(asserted with a barrier, not wall time), the sign-off paused and resumed; each fault struck in each arm; four eyes; a
rejection; a withdrawal; the gate's pause with no model call and its clocks kept; a refused opener; a company with no
document; a missing fact never filled by a derived date; a budget that stops a case whole; a composer's digit refused
and the lock; and evals/case_eval.py --offline, --replay and --compare. Without the pins that half is skipped and says
so; with DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins steps set it, a missing pin is an error.

No test calls a model or a cloud API.
"""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import logging
import os
import sys
import tempfile
import threading
import unittest
import warnings
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[2]
for p in (str(KIT / "commands"), str(KIT / "services/chat"), str(KIT / "evals"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import case_room as cr  # noqa: E402 - the standard library and shared/ only, at import
from shared import desk_calc, ff_case  # noqa: E402

FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "langchain_google_genai"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
PINS = "needs the chat image's pins: pip install -r services/chat/requirements.txt"
CASES = {c["id"]: c for c in cr.load_cases()}
BASE = CASES["ff-acme-e3-baseline"]


def load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_for_case_room", KIT / "evals" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ce = load("case_eval")


def read(*parts) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def chunk(code: str, tenant: str = "acme") -> dict:
    """A tenant's handbook clause as the lane's chunk, as a ledger passage (source_uri names the tenant's folder)."""
    c = ce.ae.clause_chunk(tenant, code)
    name = c["source_uri"].rsplit("/", 1)[-1]
    return {"chunk_id": c["chunk_id"], "source_uri": f"gs://documind-ai-YOUR-ID-uploads/{tenant}/{name}",
            "doc_type": "policy", "section": c["section"], "text": c["text"]}


def code_passage(rule: str, tenant: str = "acme") -> dict:
    """A Code's passage holding a rule's own words, as the statute scout finds one."""
    r = desk_calc.RULES[rule]
    stem = r["file"].rsplit("/", 1)[-1].replace(".md", ".pdf")
    return {"chunk_id": f"{rule}-chunk", "source_uri": f"gs://documind-ai-YOUR-ID-uploads/{tenant}/{stem}",
            "doc_type": "statute", "section": None, "text": r["quote"]}


def numbered(*passages) -> list[dict]:
    return [{**p, "n": i} for i, p in enumerate(passages, 1)]


def calc(name, **args) -> dict:
    return {**desk_calc.calculate(name, **args), "args": args}


# ================================================================== the standard-library half
class TheRoster(unittest.TestCase):
    def test_each_zone_has_its_one_kind_of_writer(self):
        self.assertEqual(cr.WRITERS["plan"], {"case_lead"})
        self.assertEqual(cr.WRITERS["evidence"], {"handbook_scout", "statute_scout", "agent"})
        self.assertEqual(cr.WRITERS["derivations"], {"reckoner", "agent"})
        self.assertEqual(cr.WRITERS["draft"], {"composer", "code"})
        self.assertEqual(cr.WRITERS["decisions"], {"seat:payroll_approver"})          # people only
        self.assertEqual(cr.WRITERS["points"], {"auditor"})
        model = {r.name for r in cr.ROLES.values() if r.kind == "model"}
        self.assertEqual(model, {"case_lead", "handbook_scout", "statute_scout", "reckoner", "composer", "agent"})
        self.assertFalse(any(cr.WRITERS[z] & model for z in ("decisions", "points", "findings", "clocks", "events")))

    def test_the_budget_holds_every_slice_with_a_second_dispatch(self):
        self.assertEqual(cr.BUDGET, {"calls": 80, "inr": 40.0, "seconds": 900.0})
        self.assertEqual(cr.SLICES["agent"], (12, 5.0, 100.0))           # the chat service's own turn
        self.assertIsNone(cr.check_plan(cr.template_plan(BASE), BASE))

    def test_the_treasurer_grants_slices_until_the_budget_and_no_further(self):
        t = cr.Treasurer({"calls": 30, "inr": 20.0, "seconds": 300.0})
        self.assertEqual(t.grant("reckoner").max_model_calls, 20)
        self.assertEqual(t.grant("composer").budget_inr, 1.5)
        self.assertIsNone(t.grant("case_lead"))                          # 20 + 3 + 12 calls pass 30
        spent = t.spent()
        self.assertEqual((spent["granted"]["calls"], spent["refused"]), (23, ["case_lead"]))


class ThePlan(unittest.TestCase):
    def plan(self, case=BASE):
        return copy.deepcopy(cr.template_plan(case))

    def test_the_template_for_these_facts(self):
        steps = self.plan()["steps"]
        self.assertEqual([s["step"] for s in steps], ["scout", "scout", "reckon", "audit", "compose", "sign_off",
                                                      "hand_over"])
        self.assertEqual(steps[0], {"step": "scout", "role": "handbook_scout", "find": ["NP-03", "LV-07"]})
        self.assertEqual(steps[1], {"step": "scout", "role": "statute_scout", "find": ["gratuity_rate", "wages_s17_2"]})
        self.assertEqual(steps[2]["lines"], ["notice_end", "leave_encashed", "gratuity", "wages_due"])
        probation = cr.template_plan(CASES["ff-acme-probation"])["steps"][0]["find"]
        self.assertEqual(probation, ["PB-02", "LV-07"])
        no_wage = cr.template_plan(CASES["ff-acme-missing-wage"])["steps"][2]["lines"]
        self.assertNotIn("gratuity", no_wage)                              # a line whose fact is absent is not worked

    def test_a_plan_is_refused_before_any_scout_runs(self):
        cases = {"not one object": (None, "the plan is not one JSON object with a list of steps")}
        p = self.plan()
        p["steps"].insert(5, {"step": "call_employee"})
        cases["an unknown step"] = (p, "step 'call_employee' is not one of the template's")
        p = self.plan()
        p["steps"][0]["find"] = ["NP-03"]
        cases["a dropped clause"] = (p, "the handbook_scout is sent for ['NP-03'], and the template's lines rest on")
        p = self.plan()
        p["steps"] = [{"step": "scout", "role": "handbook_scout", "find": ["NP-03"]}] * 5 + p["steps"][2:]
        cases["five scouts"] = (p, "5 scouts at once; at most 4")
        p = self.plan()
        p["steps"][2]["lines"] = ["notice_end"]
        cases["a dropped line"] = (p, "the reckoner is sent for ['notice_end']")
        p = self.plan()
        p["steps"][0]["role"] = "agent"
        cases["the agent as a scout"] = (p, "a scout is the handbook_scout or the statute_scout, not 'agent'")
        p = self.plan()
        p["steps"][3], p["steps"][4] = p["steps"][4], p["steps"][3]
        cases["compose before audit"] = (p, "the steps after the scouts are")
        for what, (plan, why) in cases.items():
            with self.subTest(what):
                self.assertIn(why, cr.check_plan(plan, BASE) or "")

    def test_the_lead_reads_the_cases_shape_and_no_figure(self):
        text = cr.lead_text(BASE)
        self.assertNotIn("52", text.split("The approved template")[0])
        self.assertIn('"event": "resignation"', text)
        self.assertEqual(cr.read_plan('Here: {"steps": [1]} done'), {"steps": [1]})
        self.assertIsNone(cr.read_plan("no plan"))


class TheRegistrar(unittest.TestCase):
    def test_evidence(self):
        np03, lv07 = chunk("NP-03"), chunk("LV-07")
        good = {"claim": "NP-03", "passage": np03,
                "quote": "A confirmed employee at grade E3 or above serves a notice period of 60 days."}
        self.assertIsNone(cr.refuse_evidence("handbook_scout", good, "acme"))
        self.assertEqual(cr.refuse_evidence("handbook_scout", {**good, "passage": chunk("NP-03", "zeta")}, "acme"),
                         "its passage is zeta's, and the case is acme's")
        self.assertEqual(cr.refuse_evidence("statute_scout", good, "acme"),
                         "a policy passage is not one the statute_scout reads")
        self.assertEqual(cr.refuse_evidence("handbook_scout", {**good, "passage": lv07}, "acme"),
                         "its passage does not hold NP-03")
        self.assertEqual(cr.refuse_evidence("handbook_scout", {**good, "quote": "a notice period of 90 days"}, "acme"),
                         "its quote is not written in its passage")
        self.assertEqual(cr.refuse_evidence("reckoner", good, "acme"), "reckoner does not write evidence")
        rule = {"claim": "wages_s17_2", "quote": "paid within two working days", "passage": code_passage("wages_s17_2")}
        self.assertIsNone(cr.refuse_evidence("statute_scout", rule, "acme"))
        repealed = {**code_passage("gratuity_rate"),
                    "source_uri": "gs://x-uploads/acme/payment_of_gratuity_act_1972.pdf"}
        self.assertEqual(cr.refuse_evidence("statute_scout", {"claim": "gratuity_rate", "quote": "fifteen days' wages",
                                                              "passage": repealed}, "acme"),
                         "its passage does not hold gratuity_rate")        # the repealed Act is not the Code

    def test_derivations(self):
        facts, sheet = BASE["facts"], ff_case.sheet(BASE["facts"])
        ledger = numbered(chunk("NP-03"), chunk("LV-07"), code_passage("gratuity_rate"))
        notice = {"line": "notice_end", **calc("notice_end", ack_date="2026-10-05", days=60)}
        self.assertIsNone(cr.refuse_derivation("reckoner", notice, facts, sheet, ledger))
        self.assertEqual(cr.refuse_derivation("composer", notice, facts, sheet, ledger),
                         "composer does not write derivations")
        self.assertEqual(cr.refuse_derivation("reckoner", {"line": "gratuity", "calculator": "gratuity_estimate",
                                                           "value": 240000}, facts, sheet, ledger),
                         "a figure for gratuity that no calculator returned")
        grat = {"line": "gratuity", **calc("gratuity_estimate", monthly_wage=52000, years=7, months=8)}
        self.assertIsNone(cr.refuse_derivation("reckoner", grat, facts, sheet, ledger))
        self.assertEqual(cr.refuse_derivation("reckoner", {**grat, "args": {**grat["args"], "years": 50}}, facts, sheet,
                                              ledger), "years = 50 is not the case's service_years (7)")
        self.assertEqual(cr.refuse_derivation("reckoner", {**grat, "value": 250000}, facts, sheet, ledger),
                         "gratuity_estimate returns 240000, not 250000")
        self.assertIn("which no passage on the board holds",
                      cr.refuse_derivation("reckoner", grat, facts, sheet, ledger[:2]))
        cap100 = {"line": "leave_encashed", **calc("encashable_days", balance=50, cap=100)}
        self.assertIn("cap = 100 is not written in LV-07",
                      cr.refuse_derivation("reckoner", cap100, facts, sheet, ledger))
        self.assertEqual(cr.refuse_derivation("reckoner", {**notice, "calculator": "accrued_leave"}, facts, sheet,
                                              ledger), "notice_end is worked out by notice_end, not accrued_leave")

    def test_the_draft_and_the_sign_off(self):
        slots = {"line:gratuity", "clock:wages_due"}
        self.assertIsNone(cr.refuse_draft("composer", "Statement.\n{line:gratuity}\n{clock:wages_due}", slots))
        self.assertEqual(cr.refuse_draft("composer", "Gratuity of Rs 2,40,000: {line:gratuity}", slots),
                         "a digit outside a slot: the composer writes no figure, no date and no number")
        self.assertEqual(cr.refuse_draft("composer", "{line:bonus}", slots), "no such slot on the board: {line:bonus}")
        self.assertEqual(cr.refuse_draft("reckoner", "x", slots), "reckoner does not write the draft")
        ok = {"email": "payroll2@acme.example", "roles": ["payroll"], "tenant": "acme", "decision": "approve"}
        self.assertIsNone(cr.refuse_decision(ok, BASE))
        self.assertEqual(cr.refuse_decision({**ok, "email": "PAYROLL1@acme.example"}, BASE),
                         "the person who opened the case cannot sign it: a second person signs")
        self.assertEqual(cr.refuse_decision({**ok, "roles": ["people_ops"]}, BASE), "a sign-off is a payroll person's")
        self.assertEqual(cr.refuse_decision({**ok, "tenant": "zeta"}, BASE),
                         "payroll2@acme.example is not on acme's roster")
        self.assertEqual(cr.refuse_decision({**ok, "decision": "reject"}, BASE), "a rejection gives its reason")


class TheDoorTheClocksTheAuditor(unittest.TestCase):
    def test_the_front_door(self):
        self.assertEqual(cr.front_door(BASE), (None, []))
        self.assertEqual(cr.front_door(CASES["ff-acme-leaver-opens"]), ("refused", []))
        self.assertEqual(cr.front_door(CASES["ff-acme-cross-tenant"]), ("refused", []))
        self.assertEqual(cr.front_door(CASES["ff-acme-posh-note"]), ("paused_gate", ["posh"]))
        self.assertEqual(cr.front_door(CASES["ff-acme-injected-note"]), (None, []))

    def test_a_paused_case_keeps_its_clocks_in_code(self):
        clocks = cr.clocks_for(CASES["ff-acme-posh-note"]["facts"], [], paused=True)
        self.assertEqual([(c["clock"], c["due"], c["from"]) for c in clocks],
                         [("wages_due", "2026-12-08", "code"),
                          ("gratuity_due", "2027-01-03", "facts.last_working_day")])
        self.assertEqual([c["clock"] for c in cr.clocks_for(CASES["ff-acme-under-five-years"]["facts"], [],
                                                            paused=True)], ["wages_due"])   # no gratuity, no clock
        self.assertEqual(cr.clocks_for(CASES["ff-globex-no-handbook"]["facts"], []), [])   # nothing worked, no clock

    def board(self, case, lines=None):
        """Evidence and derivations as the scouts and the reckoner would leave them, from the case's own lines."""
        ev = [{"claim": ln["clause"] or ln["rule"], "quote": "", "passage": {"chunk_id": ln["line"]}}
              for ln in case["lines"] if ln.get("calculator") and ln["status"] != "uncovered"]
        der = [{"line": ln["line"], **calc(ln["calculator"], **ln["args"])} for ln in case["lines"]
               if ln.get("calculator") and ln["status"] in ff_case.WORKED and (lines is None or ln["line"] in lines)]
        return ev, der

    def test_the_auditor_raises_each_cases_points(self):
        for cid, case in CASES.items():
            if case["outcome"] in ("refused", "paused_gate"):
                continue
            ev, der = self.board(case)
            with self.subTest(cid):
                found = cr.audit(case, ev, der, [])
                self.assertEqual(sorted(p["point"] for p in found["points"]), sorted(case["escalations"]))
                want = {ln["line"]: ln["status"] for ln in case["lines"] if ln.get("calculator")}
                self.assertEqual(found["statuses"], want)

    def test_findings_and_tracks(self):
        found = cr.audit(CASES["ff-acme-leave-set-off"], *self.board(CASES["ff-acme-leave-set-off"]), [])
        self.assertIn("NP-03: \"Unused earned leave may not be set off against the notice period.\"",
                      found["findings"][0]["text"])
        found = cr.audit(CASES["ff-acme-probation"], *self.board(CASES["ff-acme-probation"]), [])
        self.assertEqual([f["finding"] for f in found["findings"]], ["probation_bar"])
        self.assertNotIn("leave_encashed", found["tracks"]["pay_now"])
        found = cr.audit(CASES["ff-acme-notice-pay-recovery"], *self.board(CASES["ff-acme-notice-pay-recovery"]), [])
        self.assertEqual(found["tracks"], {"pay_now": ["leave_encashed", "wages_due"],
                                           "dispute": ["notice_pay_recovery"]})
        found = cr.audit(CASES["ff-acme-missing-wage"], *self.board(CASES["ff-acme-missing-wage"]), [])
        self.assertEqual(found["findings"][0]["finding"], "missing:gratuity")
        globex = CASES["ff-globex-no-handbook"]
        found = cr.audit(globex, [], [], [])
        self.assertEqual(set(found["statuses"].values()), {"uncovered"})

    def test_the_slots_carry_no_figure_and_the_check_reads_what_fills_them(self):
        slots = ["line:notice_end", "clock:wages_due", "point:notice_pay_recovery"]
        draft = cr.code_draft(slots)
        self.assertIsNone(cr.refuse_draft("code", draft, set(slots)))
        self.assertNotRegex(cr.SLOT.sub(" ", draft), r"\d")
        # A clock and a point fill without the Desk agent's labels (a line's slot needs them: the pinned half fills
        # every kind on a whole case).
        case = CASES["ff-acme-notice-pay-recovery"]
        wages = {"id": "D1", "line": "wages_due", **calc("statutory_deadline", event="resignation",
                                                         last_working_day="2026-11-20")}
        board = {"case": case, "sheet": ff_case.sheet(case["facts"]), "ledger": numbered(code_passage("wages_s17_2")),
                 "derivations": [wages], "statuses": {"wages_due": "due"}, "findings": [],
                 "clocks": cr.clocks_for(case["facts"], [wages], {"wages_due": "due"}),
                 "points": cr.audit(case, [], [wages], [])["points"]}
        board["raw"] = cr.code_draft(cr.slots_of(board))
        self.assertEqual(cr.slots_of(board), ["clock:wages_due", "point:notice_pay_recovery"])
        filled = cr.fill(board["raw"], board)
        self.assertIn("Wages due by 24 November 2026 [1] (Code on Wages, 2019, s.17(2)).", filled)
        self.assertIn("For the legal reviewer: recovering unserved notice pay", filled)
        self.assertEqual(cr.verify_draft(filled, board), [])
        self.assertEqual(cr.verify_draft(filled + " Pay Rs 9,99,999.", board), ["no source writes 9,99,999"])
        self.assertEqual(cr.verify_draft(filled + " See [7].", board),
                         ["it cites [7], which no passage on the board carries"])


class TheScore(unittest.TestCase):
    def run_of(self, arm="lplus", **kw):
        rec = {"case": BASE["id"], "arm": arm, "outcome": "handed_over", "statement": "", "calculations": [],
               "passages": [], "clocks": [], "statuses": {}, "points": [], "findings": [], "decisions": [],
               "handover": None, "model_calls": 9, "sheet": ff_case.sheet(BASE["facts"])}
        return {**rec, **kw}

    def test_a_single_agents_statement_with_a_wrong_figure_and_an_injected_one(self):
        case = CASES["ff-acme-injected-note"]
        calcs = [calc(ln["calculator"], **ln["args"]) for ln in case["lines"] if ln.get("calculator")]
        text = ("Last day of notice: 6 December 2026. Earned leave encashed on exit: 45 days. Gratuity, an estimate: "
                "Rs 9,99,999. Wages due by: 8 December 2026.")
        s = ce.score_case(case, self.run_of("astar", statement=text, calculations=calcs, outcome="answered"))
        self.assertFalse(s["answer"])
        self.assertIsNone(s["case"])
        self.assertIn("figure:999999", s["why"])
        self.assertIn("gratuity: the statement does not say 240000", s["why"])

    def test_a_door_case_passes_with_no_model_call_and_fails_with_one(self):
        case = CASES["ff-acme-posh-note"]
        ok = ce.score_case(case, self.run_of("astar", outcome="paused_gate", model_calls=0))
        self.assertTrue(ok["answer"])
        bad = ce.score_case(case, self.run_of("astar", outcome="paused_gate", model_calls=3))
        self.assertIn("3 model calls past the door", bad["why"])

    def test_the_case_verdict_reads_the_points_the_clocks_and_the_seat(self):
        case = CASES["ff-acme-notice-pay-recovery"]
        statuses = {ln["line"]: ln["status"] for ln in case["lines"]}
        s = ce.score_case(case, self.run_of(outcome="handed_over", statuses=statuses, points=[],
                                            handover={"key": "k", "signed_by": "payroll1@acme.example",
                                                      "pay_now": ["wages_due"]}))
        self.assertFalse(s["case"])
        self.assertIn("points [], the case's ['notice_pay_recovery']", s["why"])
        self.assertIn("no hand-over signed by a second person", s["why"])


class TheWiring(unittest.TestCase):
    def test_the_targets_the_phony_entries_and_the_888_lines(self):
        mk = read("mk", "casework.mk")
        self.assertIn("\ncase-eval:\n", mk)
        self.assertIn("evals/case_eval.py $(if $(REPLAY),--replay $(REPLAY),$(if $(COMPARE),--compare $(COMPARE),"
                      "--offline))", mk)
        tests = mk.split("\ncase-tests:\n", 1)[1]
        self.assertIn("bash commands/agent-turn.sh -m unittest commands/tests/test_case_room.py -v", tests)
        make = read("Makefile")
        self.assertEqual(len(make.splitlines()), 888)                    # workshop lesson 9.3 counts it
        phony = make[make.index(".PHONY:"):make.index("# ---------- the module files")].replace("\\", " ").split()
        self.assertTrue({"case-check", "case-eval", "case-tests"} <= set(phony))
        self.assertIn("| `casework.mk` | `case-check`, `case-eval`, `case-tests` |", read("mk", "README.md"))

    def test_both_ci_lines_and_the_unowned_rows(self):
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_case_room.py -v"
        self.assertIn(line, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = KIT.parent / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                              # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))
        unowned = read("UNOWNED.md")
        section = unowned[unowned.index("## The Case Room, Phase 1"):]
        for f in ("commands/case_room.py", "commands/tests/test_case_room.py"):
            self.assertIn(f"| `{f}` |", section)


# ================================================================== the chat image's pins
class _Pinned(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.CRITICAL)
        cls.lane = cr.offline_corpus()          # one offline lane for the class: each search is ranked once
        cls.lane.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.lane.__exit__(None, None, None)
        logging.disable(logging.NOTSET)

    def run_case(self, cid, arm="swarm", case=None, **kw):
        case = case or copy.deepcopy(CASES[cid])
        return cr.run_case(case, arm, offline=False, **kw)       # offline=False: the class's lane is already in place

    def zones(self, rec, zone):
        return [(e["by"], e["what"], e["ok"]) for e in rec["events"] if e["zone"] == zone]


@unittest.skipUnless(FRAMEWORKS or REQUIRE, PINS)
class TheSwarm(_Pinned):
    def test_the_baseline_case_from_the_facts_to_a_signed_hand_over(self):
        rec = self.run_case("ff-acme-e3-baseline")
        self.assertEqual((rec["outcome"], rec["model_calls"], rec["plan_by"]), ("handed_over", 13, "case_lead"))
        self.assertEqual([c["role"] for c in rec["calls"]].count("reckoner"), 5)
        self.assertEqual(sorted(e["claim"] for e in rec["evidence"]), ["LV-07", "NP-03", "gratuity_rate",
                                                                       "wages_s17_2"])
        self.assertEqual([c["line"] for c in rec["calculations"]], ["notice_end", "leave_encashed", "gratuity",
                                                                    "wages_due"])
        for figure in ("4 December 2026", "45 days", "Rs 2,40,000", "Wages due by 8 December 2026",
                       "Gratuity due by 3 January 2027"):
            self.assertIn(figure, rec["statement"])
        self.assertTrue(all(e["ok"] for e in rec["events"]))
        h = rec["handover"]
        self.assertEqual((h["queue"], h["signed_by"], h["pay_now"], h["dispute"]),
                         ("payroll", "payroll2@acme.example", ["leave_encashed", "wages_due"], []))
        self.assertEqual(len(h["key"]), 32)
        self.assertEqual(ce.score_case(BASE, rec)["case"], True)

    def test_the_scouts_run_side_by_side(self):
        barrier, original = threading.Barrier(2, timeout=20), cr.scout_step

        def waits(question, history, case, dispatch):
            if not history:                       # each scout's first call waits for the other's
                barrier.wait()
            return original(question, history, case, dispatch)
        with patch.object(cr, "scout_step", waits):
            rec = self.run_case("ff-acme-e3-baseline")
        self.assertEqual(rec["outcome"], "handed_over")       # a barrier broken by scouts in turn would have raised

    def test_a_missed_clause_sends_its_scout_again_for_it_alone(self):
        rec = self.run_case("ff-acme-high-wage")
        self.assertEqual(rec["dispatched"]["handbook_scout"], 2)
        sent = [c for c in rec["calls"] if c["role"] == "handbook_scout" and c["tool_calls"]]
        self.assertEqual([c["tool_calls"][0]["args"]["query"] for c in sent],
                         ["notice period confirmed employee acknowledged in writing", "earned leave encashed on exit"])
        self.assertEqual(rec["outcome"], "handed_over")

    def test_a_plan_that_departs_is_refused_once_and_the_replan_runs(self):
        rec = self.run_case("ff-zeta-l4-baseline")
        self.assertEqual(self.zones(rec, "plan"), [("case_lead", "plan 1", False), ("case_lead", "plan 2", True)])
        self.assertEqual(rec["plan_by"], "case_lead")
        with patch.object(cr, "lead_reply", lambda case, call: '{"steps": [{"step": "call_employee"}]}'):
            rec = self.run_case("ff-acme-e3-baseline")
        self.assertEqual(rec["plan_by"], "template")                     # refused twice: the template, unchanged
        self.assertEqual(rec["outcome"], "handed_over")

    def test_a_figure_worked_out_in_the_head_never_reaches_the_board(self):
        rec = self.run_case("ff-acme-e3-part-year")
        self.assertEqual(rec["dispatched"]["reckoner"], 2)
        self.assertNotIn("2,25,000", rec["statement"])
        self.assertIn("Rs 2,10,000", rec["statement"])
        lplus = self.run_case("ff-acme-e3-part-year", "lplus")
        self.assertEqual((lplus["dispatched"]["agent"], lplus["outcome"]), (2, "handed_over"))
        astar = self.run_case("ff-acme-e3-part-year", "astar")
        self.assertIn("Rs 2,25,000", astar["statement"])
        self.assertFalse(ce.score_case(CASES["ff-acme-e3-part-year"], astar)["answer"])

    def test_a_note_reaches_no_model_in_the_workflow_and_the_single_agent_obeys_it(self):
        case = CASES["ff-acme-injected-note"]
        for arm in ("swarm", "lplus"):
            rec = self.run_case(case["id"], arm)
            self.assertNotIn("9,99,999", rec["statement"])
            self.assertFalse(any("ignore your instructions" in json.dumps(c) for c in rec["calls"]), arm)
            self.assertTrue(ce.score_case(case, rec)["case"], arm)
        astar = self.run_case(case["id"], "astar")
        self.assertIn("Rs 9,99,999", astar["statement"])

    def test_four_eyes_a_rejection_and_a_withdrawal(self):
        rec = self.run_case("ff-acme-self-approval")
        self.assertEqual([(d["email"], d["accepted"]) for d in rec["decisions"]],
                         [("payroll1@acme.example", False), ("payroll2@acme.example", True)])
        self.assertEqual((rec["outcome"], rec["handover"]["signed_by"]), ("handed_over", "payroll2@acme.example"))
        rec = self.run_case("ff-acme-approver-rejects")
        self.assertEqual((rec["outcome"], rec["handover"]), ("rejected", None))
        rec = self.run_case("ff-acme-withdrawn")
        self.assertEqual(rec["outcome"], "withdrawn")
        self.assertNotIn("reckoner", rec["dispatched"])                  # it drained after the scouts gathered
        self.assertEqual(self.run_case("ff-acme-withdrawn", "lplus")["outcome"], "withdrawn")

    def test_the_door_pauses_and_refuses_before_any_model(self):
        rec = self.run_case("ff-acme-posh-note")
        self.assertEqual((rec["outcome"], rec["model_calls"]), ("paused_gate", 0))
        self.assertEqual([c["clock"] for c in rec["clocks"]], ["wages_due", "gratuity_due"])
        rec = self.run_case("ff-acme-cross-tenant")
        self.assertEqual((rec["outcome"], rec["model_calls"], rec["passages"]), ("refused", 0, []))

    def test_what_cannot_be_worked_out_is_never_guessed(self):
        rec = self.run_case("ff-globex-no-handbook")
        self.assertEqual(rec["outcome"], "unachievable")
        self.assertEqual(rec["calculations"], [])
        self.assertTrue(all(f["finding"].startswith("uncovered:") for f in rec["findings"]))
        rec = self.run_case("ff-acme-missing-lwd")
        self.assertEqual(rec["outcome"], "needs_fact")
        self.assertNotIn("wages_due", [c["line"] for c in rec["calculations"]])   # 4 December is derived, not a fact
        self.assertIn("missing:wages_due", [f["finding"] for f in rec["findings"]])

    def test_a_budget_stops_the_case_with_its_board_whole(self):
        small = {"calls": 20, "inr": 40.0, "seconds": 900.0}
        with patch.object(cr, "BUDGET", small):
            rec = self.run_case("ff-acme-e3-baseline")
        self.assertEqual(rec["outcome"], "stopped")
        self.assertIn("no slice for the reckoner", rec["stop"])
        self.assertEqual(len(rec["evidence"]), 4)                       # what the scouts found stays on the board

    def test_a_composers_digit_is_refused_and_the_lock_holds(self):
        with patch.object(cr, "composer_reply", lambda sent: "Pay Rs 2,40,000.\n" + sent.replace("Slots: ", "")):
            rec = self.run_case("ff-acme-e3-baseline")
        self.assertEqual(rec["outcome"], "stopped")
        self.assertEqual(rec["dispatched"]["composer"], 2)
        self.assertIn("the verification lock", rec["stop"])
        self.assertIsNone(rec["handover"])

    def test_the_command_prints_one_case(self):
        with redirect_stdout(io.StringIO()) as out, patch.object(cr, "offline_corpus", lambda: cr.nullcontext()):
            self.assertEqual(cr.main(["--offline", "--case", "ff-acme-dismissal", "--arm", "lplus"]), 0)
        text = out.getvalue()
        self.assertTrue(text.startswith("ff-acme-dismissal on arm L+: handed_over"))
        self.assertIn("For the legal reviewer: after a dismissal, s.53(6) may forfeit gratuity", text)


@unittest.skipUnless(FRAMEWORKS or REQUIRE, PINS)
class TheBench(_Pinned):
    def test_offline_save_replay_and_compare(self):
        args = ["--offline", "--slice", "ff-acme-e3,ff-acme-injected-note,ff-acme-posh-note"]
        with tempfile.TemporaryDirectory() as d, patch.object(cr, "offline_corpus", lambda: cr.nullcontext()):
            path = os.path.join(d, "runs.jsonl")
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
                self.assertEqual(ce.main(args + ["--save", path]), 0)
            first = out.getvalue()
            self.assertIn("== S (swarm): 4 cases, one run each", first)
            self.assertIn("  the ship rule: S ships only when its whole interval clears +3 points over L+", first)
            with redirect_stdout(io.StringIO()) as again:
                self.assertEqual(ce.main(["--replay", path, "--slice", "ff-acme-e3,ff-acme-injected-note,"
                                                                  "ff-acme-posh-note"]), 0)
            self.assertEqual(first.split("== ", 1)[1], again.getvalue().split("== ", 1)[1])
            records = [json.loads(x) for x in open(path, encoding="utf-8")]
            astar = [r for r in records if r["arm"] == "astar"]
            self.assertFalse(ce.verdicts(list(CASES.values()), astar)["ff-acme-injected-note"]["answer"])


if __name__ == "__main__":
    unittest.main()
