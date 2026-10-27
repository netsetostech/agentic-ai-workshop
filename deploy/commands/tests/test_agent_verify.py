"""Lesson 10.3's pattern on the agent bench (commands/agent_patterns.py): verify, check, retry or choose, with code as
the critic. The loop answers; figure_check() reads the answer; a failed check gets one reflect call's note and the loop
answers again, its notes in its system prompt and never its question, at most three attempts.

    python -m unittest commands/tests/test_agent_verify.py -v        # from deploy/
    make agent-tests                                                  # the same, in ~/graph-venv with the chat pins

The first half needs the standard library only and runs in CI's shared interpreter: figure_check() gives one answer
one verdict every time, fails an unsupported figure, a cited passage never read and a stop, and never takes a figure
from a note; said_check(), cut_note(), did_lines() and the scripted note keep figures out of what a note is written
from; the registry, PLANNED empty, the one line marked THE QUESTION; the CI lines, make's lines, line 214 and the
UNOWNED.md row. The second half runs verify on ScriptedCheckModel over the kit's own corpus and needs the chat image's
pins (pip install -r services/chat/requirements.txt): attempt 1 is the loop's own turn; a first attempt that fails the
check and a second, after a note, that passes; Rs 2,50,000 corrected in one round; a note that carries a figure, which
check_args refuses as an argument and the check flags in every later answer, up to the cap; each attempt a turn of its
own, its reflect call counted on its own Meter; the rupees; thinking on every call; the Change-it (the note put into
the question, in memory), which launders the figure; agent_turn.py and agent_eval.py with verify. Without the pins that
half is skipped and says so; with DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins steps set it, a missing pin is an error.

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
import unittest
import warnings
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
for p in (str(KIT / "commands"), str(KIT / "services/chat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import agent_patterns as ap  # noqa: E402 - the standard library and shared/ only, at import
from shared import desk_calc, prices  # noqa: E402

FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "langchain_google_genai"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
PINS = "needs the chat image's pins: pip install -r services/chat/requirements.txt"
GRATUITY = "I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?"
SEARCH = {"calls": [{"name": "retrieve", "args": {"query": "gratuity fifteen days wages for every completed year of "
                                                           "service"}}]}
S53 = {"n": 1, "source": "code_on_social_security_2020.pdf", "doc_type": "statute", "section": None,
       "text": "the fifteen days' wages shall be calculated by dividing the monthly rate of wages last drawn by him by "
               "twenty-six and multiplying the quotient by fifteen."}


def read(*parts) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def gratuity():
    return {**desk_calc.gratuity_estimate(52000, 7, 8), "args": {"monthly_wage": 52000, "years": 7, "months": 8}}


def load_eval(name: str):
    spec = importlib.util.spec_from_file_location(name, KIT / "evals" / "agent_eval.py")
    ae = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ae)
    return ae


# ================================================================== the standard-library half
class Check(unittest.TestCase):
    def test_one_answer_one_verdict_every_time(self):
        """Code, never a model: the same answer, calculations, question and passages give the same verdict, and the
        check changes none of them."""
        args = ("Gratuity, an estimate: Rs 2,40,000 [1].", [gratuity()], GRATUITY, [S53])
        kept = copy.deepcopy(args)
        verdicts = [ap.figure_check(*copy.deepcopy(args)) for _ in range(5)]
        self.assertEqual(verdicts, [{"passed": True, "unsupported": [], "uncited": [], "stopped_by": None}] * 5)
        self.assertEqual(ap.figure_check(*args), verdicts[0])
        self.assertEqual(args, kept)

    def test_what_fails_it(self):
        head = ap.figure_check("Gratuity, an estimate: Rs 2,40,000 [1].", [], GRATUITY, [S53])
        self.assertEqual((head["passed"], head["unsupported"]), (False, ["2,40,000"]))
        far = ap.figure_check("Rs 2,40,000 [1, 3].", [gratuity()], GRATUITY, [S53, dict(S53, n=2)])
        self.assertEqual((far["passed"], far["unsupported"], far["uncited"]), (False, [], [3]))
        none = ap.figure_check("Rs 2,40,000 [2].", [gratuity()], GRATUITY, [])        # no passage read at all
        self.assertEqual(none["uncited"], [2])
        stop = ap.figure_check("I stopped this turn at one of its limits.", [], GRATUITY, [], "model_calls")
        self.assertEqual((stop["passed"], stop["unsupported"], stop["stopped_by"]), (False, [], "model_calls"))
        self.assertEqual(ap.said_check(head), "failed: no calculator, question or passage of the turn wrote 2,40,000")
        self.assertEqual(ap.said_check(far), "failed: it cites [3], which no passage the turn read carries")
        self.assertEqual(ap.said_check(stop), "failed: the turn stopped at its model_calls limit")

    def test_what_passes_it(self):
        lv07 = {"n": 4, "doc_type": "policy", "text": "LV-07 Leave on exit\nEarned leave is encashed on exit at basic "
                                                      "pay, capped at 45 days."}
        self.assertTrue(ap.figure_check("LV-07 caps it at 45 days [4].", [], "How many days?", [lv07])["passed"])
        self.assertTrue(ap.figure_check("On your Rs 52,000 a month, see [1].", [], GRATUITY, [S53])["passed"])
        notice = {**desk_calc.notice_end("2026-10-05", 60), "args": {}}
        self.assertTrue(ap.figure_check("Notice ends on 4 December 2026 [1][2-3].", [notice], "",
                                        [dict(S53, n=i) for i in (1, 2, 3)])["passed"])
        self.assertEqual(ap.cited("[1], [2-3] and [1, 4]; s.53(1) and LV-07 are no marks"), [1, 2, 3, 4])
        self.assertEqual(ap.said_check(ap.figure_check("No figure, no passage.", [], "", [])),
                         "passed: every figure is a calculator's, the question's or a passage's, and every [n] a "
                         "passage read")

    def test_a_note_is_never_a_source(self):
        """A figure only a note writes is unsupported: the check reads the turn's calculations, its question and its
        passages, and a note is none of them. Put the note into the question (lesson 10.3's Change-it) and the same
        figure passes: notes are memory, not evidence."""
        note = "My answer stated a figure no calculator returned. The figure is Rs 2,40,000."
        answer = "Gratuity, an estimate: Rs 2,40,000 [1]."
        self.assertEqual(ap.figure_check(answer, [], GRATUITY, [S53])["unsupported"], ["2,40,000"])
        self.assertTrue(ap.figure_check(answer, [], GRATUITY + "\n\n" + note, [S53])["passed"])    # laundered
        self.assertEqual(desk_calc.unsupported(note), ["2,40,000"])                     # what the record keeps
        refused, _ = desk_calc.check_args("gratuity_estimate", {"monthly_wage": 60000, "years": 7, "months": 8}, [],
                                          GRATUITY)
        self.assertTrue(refused[0].startswith("monthly_wage = 60000 is a fact about the person that their message "
                                              "does not state"))
        self.assertEqual(desk_calc.check_args("gratuity_estimate", {"monthly_wage": 60000, "years": 7, "months": 8},
                                              [], GRATUITY + " The wage is Rs 60,000.")[0], [])


class Notes(unittest.TestCase):
    def test_a_note_is_cut_to_300_characters_on_one_line(self):
        note = ap.cut_note("Use the `calculator`.\n\n  Then cite it.  " + "x" * 400)
        self.assertEqual(len(note), ap.NOTE_CHARS)
        self.assertNotIn("`", note)
        self.assertNotIn("\n", note)
        self.assertTrue(note.startswith("Use the 'calculator'. Then cite it. xxx"))
        self.assertEqual((ap.cut_note(""), ap.cut_note(None), ap.cut_note(" short ")), ("", "", "short"))

    def test_what_the_reflect_call_reads(self):
        """The question, the answer, what the attempt did (a calculator's result only as "a figure") and the verdict:
        no figure a calculator returned reaches the reflect call from code."""
        steps = [{"tools": [{"name": "retrieve", "args": {"query": "gratuity"}, "status": "success",
                             "result": {"passages": [{"n": 1, "source": "code_on_social_security_2020.pdf",
                                                      "section": None}, {"n": 2, "source": "hr_policy_2026.md",
                                                                         "section": "LV-07 Leave on exit"}]}},
                            {"name": "gratuity_estimate", "args": {"monthly_wage": 52000, "years": 7, "months": 8},
                             "status": "success", "result": {"value": 240000, "formula": "Rs 2,40,000"}},
                            {"name": "gratuity_estimate", "args": {"monthly_wage": 60000, "years": 7, "months": 8},
                             "status": "error", "result": {"error": "refused: monthly_wage = 60000 is a fact about the "
                                                                    "person that their message does not state"}},
                            {"name": "retrieve", "args": {"query": "q"}, "status": "success",
                             "result": {"passages": [], "error": "document search is unavailable"}}]}]
        lines = ap.did_lines(steps)
        self.assertEqual(lines, [
            '   call: retrieve {"query": "gratuity"}',
            "   returned: [1] code_on_social_security_2020.pdf; [2] hr_policy_2026.md, LV-07 Leave on exit",
            '   call: gratuity_estimate {"monthly_wage": 52000, "years": 7, "months": 8}', "   returned: a figure",
            '   call: gratuity_estimate {"monthly_wage": 60000, "years": 7, "months": 8}',
            "   refused: monthly_wage = 60000 is a fact about the person that their message does not state",
            '   call: retrieve {"query": "q"}', "   failed: document search is unavailable"])
        self.assertEqual(ap.did_lines([{"tools": []}]), ["   no tool call"])
        check = ap.figure_check("Rs 2,50,000 [1].", [], GRATUITY, [S53])
        sent = ap.ask_reflect(GRATUITY, "Rs  2,50,000\n[1].", steps, check)
        self.assertTrue(sent.startswith(f"Question: {GRATUITY}\n\nYour answer: Rs 2,50,000 [1].\n\nWhat you did:\n"))
        self.assertTrue(sent.endswith("\n\nThe figure check failed: no calculator, question or passage of the turn "
                                      "wrote 2,50,000"))
        self.assertNotIn("2,40,000", sent)
        self.assertNotIn("240000", sent)

    def test_the_scripted_note(self):
        rows = {r["id"]: r for r in ap.tasks()}
        sent = "Question: q\n\nThe figure check failed: no calculator, question or passage of the turn wrote 2,40,000"
        note = ap.reflect_note(sent, rows["calc-gratuity-7y8m"])
        self.assertTrue(note.startswith("My answer stated a figure that no calculator of that turn returned. Next "
                                        "time: search first, call gratuity_estimate"))
        self.assertEqual(desk_calc.unsupported(note), [])                       # no figure: what failed, not a fix
        self.assertLessEqual(len(note), ap.NOTE_CHARS)
        carried = ap.reflect_note(sent, rows["calc-gratuity-7y8m"], launders="Rs 2,40,000")
        self.assertTrue(carried.endswith(" The figure is Rs 2,40,000."))
        self.assertEqual((desk_calc.unsupported(carried), ap.cut_note(carried)), (["2,40,000"], carried))
        self.assertIn("call notice_end and encashable_days and gratuity_estimate",
                      ap.reflect_note(sent, rows["chained-exit-e3"]))
        self.assertTrue(ap.reflect_note("The figure check failed: it cites [9], which no passage the turn read carries",
                                        None).startswith("My answer cited a passage the turn never read. Next time: "
                                                         "state only figures"))


class Registry(unittest.TestCase):
    def test_verify_is_built_and_nothing_is_planned(self):
        p = ap.PATTERNS["verify"]
        self.assertEqual((p.name, p.lessons, p.checked, p.text, p.executor), ("verify", "10.3", True, False, False))
        self.assertEqual(list(ap.PATTERNS), ["loop", "react_text", "plan_first", "plan_execute", "rewoo", "verify"])
        self.assertFalse(any(ap.PATTERNS[n].checked for n in ap.PATTERNS if n != "verify"))
        self.assertEqual(ap.PLANNED, {})
        self.assertEqual((ap.MAX_ATTEMPTS, ap.NOTE_CHARS, ap.CHECK_ROLES), (3, 300, ("answer", "reflect")))
        with self.assertRaises(ValueError) as e:
            ap.pattern("critic")
        self.assertEqual(str(e.exception), "no pattern 'critic': built loop, react_text, plan_first, plan_execute, "
                                           "rewoo, verify")
        with self.assertRaisesRegex(ValueError, "launders is for verify: the loop pattern writes no note"):
            ap.scripted("q", pattern="loop", launders="Rs 1")
        with self.assertRaisesRegex(ValueError, "invents is for react_text and verify"):
            ap.scripted("q", pattern="plan_first", invents="Rs 1")

    def test_the_question_is_one_marked_line(self):
        """Lesson 10.3's Change-it edits one line: the only one marked THE QUESTION, which sets what an attempt asks
        and check_args and the figure check read; the notes reach the attempt through noted() alone."""
        lines = read("commands", "agent_patterns.py").splitlines()
        marked = [line.strip() for line in lines if "THE QUESTION" in line]
        self.assertEqual(len(marked), 1)
        self.assertTrue(marked[0].startswith("asked = question  # THE QUESTION:"))
        at = next(i for i, line in enumerate(lines) if "THE QUESTION" in line)
        self.assertEqual(lines[at + 1].strip(), 'actx["desk_message"] = asked')
        self.assertIn("prompt=noted(desk, kept[\"notes\"])", lines[at + 2])

    def test_ci_make_and_unowned(self):
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_agent_verify.py -v"
        self.assertIn(line, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = KIT.parent / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                                    # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))
        agents = read("mk", "agents.mk")
        recipe = agents.split("\nagent-tests:\n", 1)[1].split("\n\n", 1)[0]
        self.assertIn("bash commands/agent-turn.sh -m unittest commands/tests/test_agent_verify.py -v", recipe)
        evaluate = agents.split("\nagent-eval: ", 1)[1].split("\n\n", 1)[0]
        self.assertIn('$(if $(REPLAY),--replay $(foreach f,$(REPLAY),"$(f)"),', evaluate)
        lines = agents.splitlines()                                             # lesson 10.4's build reads route-eval
        self.assertEqual(lines.index("route-eval: guard-project") + 2, 214)
        unowned = read("UNOWNED.md")
        # its row, until a page quotes the file; then INDEX.md names that page (the page PR moves the row)
        row = next((l for l in read("INDEX.md").splitlines() if l.startswith("| `commands/tests/test_agent_verify.py` |")), "")
        self.assertTrue("| `commands/tests/test_agent_verify.py` | **10.3** |" in unowned
                        or row.split(" | ")[2:3] not in ([], ["-"]))
        if "| `commands/agent_patterns.py` |" in unowned:                       # the registry's row names the pattern,
            self.assertIn("`verify` (10.3): each attempt is the loop as a turn of its own", unowned)
        else:                                                                   # until lesson 10.3's page quotes the file
            registry = next(l for l in read("INDEX.md").splitlines() if l.startswith("| `commands/agent_patterns.py` |"))
            self.assertIn("10.3", registry.split(" | ")[2].split(", "))


# ================================================================== the chat image's pins
class _Pinned(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.CRITICAL)
        import desk_agent
        import limits
        cls.da, cls.limits = desk_agent, limits
        cls.rows = {r["id"]: r for r in ap.tasks()}
        cls.lane = ap.offline()             # one offline lane for the class: each search is ranked once, not each turn
        cls.lane.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.lane.__exit__(None, None, None)
        logging.disable(logging.NOTSET)

    def model(self, mod=ap, **kw):
        return mod._scripted_check_class()(model=self.da.AGENT_MODEL, thinking_level=self.da.THINKING_LEVEL, **kw)

    def turn(self, llm=None, row="calc-gratuity-7y8m", mod=ap, **kw):
        r = self.rows[row]
        llm = llm or self.model(mod, task=r)
        return mod.run("verify", r["question"], llm=llm, **kw), llm

    def score(self, row: str, turn: dict) -> dict:
        return load_eval("agent_eval_for_verify_score").score(self.rows[row], turn)


@unittest.skipUnless(FRAMEWORKS or REQUIRE, PINS)
class Verify(_Pinned):
    def test_attempt_one_is_the_loops_own_turn(self):
        """An answer the check passes ships at once: verify's record is the loop's on the same script, its calls
        tagged with their attempt and role."""
        turn, llm = self.turn()
        loop = ap.run("loop", GRATUITY, llm=ap.scripted(GRATUITY))
        for key in ("answer", "passages", "calculations", "tool_calls", "refusals", "retrieve_calls", "answerable",
                    "stopped_by", "composed", "model_calls", "inr", "tokens_in"):
            self.assertEqual(turn[key], loop[key], key)
        self.assertEqual((turn["shipped"], len(turn["attempts"]), turn["notes"], turn["check"]["passed"]),
                         (1, 1, [], True))
        self.assertEqual({(c["role"], c["attempt"]) for c in turn["calls"]}, {("answer", 1)})
        self.assertEqual(llm.roles, ["answer"] * 3)
        self.assertEqual(set(turn["roles"]), {"answer"})
        self.assertEqual(turn["attempts"][0]["note"], None)

    def test_a_failed_check_a_note_then_a_pass(self):
        """Attempt 1 writes the figure itself (a slip): the check fails it; one reflect call writes a note, which goes
        into attempt 2's system prompt and never its question; attempt 2 calls the calculator and ships."""
        turn, llm = self.turn(self.model(task=self.rows["calc-gratuity-7y8m"], slip=True))
        first, second = turn["attempts"]
        self.assertEqual((first["answer"], first["calculations"], first["check"]["unsupported"]),
                         ("Gratuity, an estimate: Rs 2,40,000 [2].", [], ["2,40,000"]))
        self.assertEqual(llm.roles, ["answer", "answer", "reflect", "answer", "answer", "answer"])
        self.assertEqual([(c["role"], c["attempt"]) for c in turn["calls"]],
                         [("answer", 1), ("answer", 1), ("reflect", 2), ("answer", 2), ("answer", 2), ("answer", 2)])
        note = second["note"]
        self.assertEqual(turn["notes"], [note])
        self.assertEqual(desk_calc.unsupported(note), [])
        self.assertEqual(second["note_figures"], [])
        self.assertTrue(llm.sent[2].endswith("The figure check failed: no calculator, question or passage of the turn "
                                             "wrote 2,40,000"))
        for i, role in enumerate(llm.roles):
            if role == "answer":
                self.assertEqual(llm.sent[i], GRATUITY)                         # the question, never a note
                self.assertEqual(note in llm.system[i], i > 2)                  # the note: attempt 2's system prompt
        self.assertEqual(llm.system[3], ap.noted("astar", [note]))
        self.assertTrue(llm.system[3].startswith(self.da.system_prompt("astar") + "\n\n" + ap.NOTES + "\n```\n1. "))
        self.assertEqual((turn["shipped"], turn["check"]["passed"], [c["value"] for c in turn["calculations"]]),
                         (2, True, [240000]))
        self.assertEqual((turn["answer"], turn["question"], second["question"]),
                         ("Gratuity, an estimate: Rs 2,40,000 [2].", GRATUITY, GRATUITY))
        got = self.score("calc-gratuity-7y8m", turn)
        self.assertEqual((got["correct"], got["provenance"]), (True, True))
        self.assertEqual(self.score("calc-gratuity-7y8m", dict(turn, **{k: first[k] for k in (
            "answer", "calculations", "passages")}))["provenance"], False)       # attempt 1 alone: no calculator

    def test_an_invented_figure_corrected_in_one_round(self):
        turn, llm = self.turn(self.model(task=self.rows["calc-gratuity-7y8m"], invents="Rs 2,50,000"))
        first, second = turn["attempts"]
        self.assertEqual((first["answer"], first["check"]["unsupported"]),
                         ("Gratuity, an estimate: Rs 2,50,000 [2].", ["2,50,000"]))
        self.assertEqual((second["answer"], second["check"]["passed"], turn["shipped"]),
                         ("Gratuity, an estimate: Rs 2,40,000 [2].", True, 2))
        reflect = llm.sent[llm.roles.index("reflect")]
        self.assertIn("wrote 2,50,000", reflect)
        self.assertNotIn("2,40,000", reflect)                                   # the right figure never reaches it

    def test_a_note_cannot_launder_a_number(self):
        """Every note carries Rs 2,40,000 - the right figure - and each later attempt writes it as its own, with no
        calculator: the check fails each, since a note is never a source, and the run stops at three attempts."""
        turn, llm = self.turn(ap.scripted(GRATUITY, pattern="verify", launders="Rs 2,40,000"))
        self.assertTrue(llm.slip)                                               # so that a note is written at all
        self.assertEqual(len(turn["attempts"]), ap.MAX_ATTEMPTS)
        self.assertEqual(llm.roles, ["answer", "answer", "reflect", "answer", "answer", "reflect", "answer", "answer"])
        for a in turn["attempts"]:
            self.assertEqual((a["answer"], a["calculations"], a["check"]["unsupported"]),
                             ("Gratuity, an estimate: Rs 2,40,000 [2].", [], ["2,40,000"]))
        self.assertEqual([a["note_figures"] for a in turn["attempts"]], [[], ["2,40,000"], ["2,40,000"]])
        self.assertTrue(all(n.endswith("The figure is Rs 2,40,000.") for n in turn["notes"]))
        self.assertEqual((turn["shipped"], turn["check"]["passed"], turn["calculations"]), (3, False, []))
        got = self.score("calc-gratuity-7y8m", turn)
        self.assertEqual((got["correct"], got["provenance"], got["unsupported"]), (True, False, ["2,40,000"]))

    def test_a_notes_figure_is_refused_as_an_argument(self):
        """A note that supplies a wage: attempt 2 gives it to the calculator, and check_args refuses it, since the
        question it reads is the person's own."""
        wage = {"calls": [{"name": "gratuity_estimate", "args": {"monthly_wage": 60000, "years": 7, "months": 8}}]}
        llm = self.model(replies=[SEARCH, "Gratuity, an estimate: Rs 2,76,923 [2].",
                                  "The wage is Rs 60,000: give the calculator monthly_wage 60000.", SEARCH, wage,
                                  "I could not work the gratuity out: the calculator refused the wage."])
        turn, _ = self.turn(llm)
        first, second = turn["attempts"]
        self.assertEqual(first["check"]["unsupported"], ["2,76,923"])
        self.assertEqual(second["note_figures"], ["60,000", "60000"])
        self.assertEqual((second["refusals"], second["calculations"]), (["gratuity_estimate"], []))
        refused = next(t for s in second["trace"] for t in s["tools"] if t["status"] == "error")
        self.assertTrue(refused["result"]["error"].startswith("refused: monthly_wage = 60000 is a fact about the "
                                                              "person that their message does not state"))
        self.assertEqual((turn["shipped"], turn["check"]["passed"]), (2, True))    # no figure: the check passes it
        self.assertFalse(self.score("calc-gratuity-7y8m", turn)["correct"])          # and the scorer does not

    def test_the_retry_cap(self):
        llm = self.model(replies=["Rs 9,99,999."])                              # never a calculator, every reply
        turn, _ = self.turn(llm)
        self.assertEqual((len(turn["attempts"]), turn["shipped"], turn["model_calls"]), (3, 3, 5))
        self.assertEqual(llm.roles, ["answer", "reflect", "answer", "reflect", "answer"])
        self.assertEqual(sum(c["role"] == "reflect" for c in turn["calls"]), ap.MAX_ATTEMPTS - 1)
        self.assertEqual([a["check"]["unsupported"] for a in turn["attempts"]], [["9,99,999"]] * 3)

    def test_each_attempt_is_a_turn_of_its_own(self):
        """A fresh Meter at the turn's limits for each attempt, the reflect call counted on its retry's: the Meter
        given is the first attempt's alone."""
        meter = self.limits.Meter(max_model_calls=2, model=self.da.AGENT_MODEL)
        llm = self.model(replies=[SEARCH])                                      # searches until a limit stops it
        turn, _ = self.turn(llm, meter=meter)
        self.assertEqual([a["stopped_by"] for a in turn["attempts"]], ["model_calls"] * 3)
        self.assertEqual([a["model_calls"] for a in turn["attempts"]], [2, 2, 2])
        self.assertEqual([[c["role"] for c in turn["calls"] if c["attempt"] == n] for n in (1, 2, 3)],
                         [["answer", "answer"], ["reflect", "answer"], ["reflect", "answer"]])
        self.assertEqual((meter.model_calls, turn["model_calls"], turn["stopped_by"]), (2, 6, "model_calls"))
        self.assertEqual(turn["attempts"][0]["check"]["stopped_by"], "model_calls")
        self.assertEqual(turn["notes"], [])                                     # a reply of tool calls writes no note
        self.assertEqual([a["passages"] for a in turn["attempts"][1:]], [turn["attempts"][0]["passages"]] * 2)

    def test_the_rupees(self):
        """Each call priced as the agent's model; the first attempt's Meter charges its calls as the recorder prices
        them, and the record's rupees are every attempt's."""
        meter = self.limits.Meter(model=self.da.AGENT_MODEL)
        turn, _ = self.turn(self.model(task=self.rows["calc-gratuity-7y8m"], invents="Rs 2,50,000"), meter=meter)
        for c in turn["calls"]:
            self.assertEqual(c["inr"], round(prices.inr(prices.usd(self.da.AGENT_MODEL, c["tokens_in"], c["tokens_out"],
                                                                   c["cached_tokens"])), 6))
        self.assertAlmostEqual(prices.inr(meter.cost_usd), turn["attempts"][0]["inr"], places=5)
        self.assertAlmostEqual(sum(a["inr"] for a in turn["attempts"]), turn["inr"], places=5)
        self.assertAlmostEqual(sum(r["inr"] for r in turn["roles"].values()), turn["inr"], places=5)
        self.assertEqual({r: v["calls"] for r, v in turn["roles"].items()}, {"answer": 5, "reflect": 1})

    def test_thinking_goes_with_every_call(self):
        turn, llm = self.turn(self.model(task=self.rows["calc-gratuity-7y8m"], slip=True), thinking="high")
        self.assertEqual(llm.seen, ["high"] * 6)
        self.assertEqual({(c["thinking_level"], c["thinking_tokens"]) for c in turn["calls"]}, {("high", 1024)})

    def with_the_note_in_the_question(self):
        """agent_patterns.py with the line marked THE QUESTION changed, as lesson 10.3's Change-it changes it: each
        attempt asks the question with every note after it. Loaded in memory under its own name; the file on disk is
        not touched."""
        path = KIT / "commands" / "agent_patterns.py"
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        (at,) = [i for i, line in enumerate(lines) if "THE QUESTION" in line]
        indent = lines[at][:len(lines[at]) - len(lines[at].lstrip())]
        lines[at] = indent + 'asked = question + "".join(f"\\n\\nA note: {n}" for n in kept["notes"])\n'
        name = "agent_patterns_note_in_the_question"
        mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None, origin=str(path)))
        mod.__file__ = str(path)
        sys.modules[name] = mod
        self.addCleanup(sys.modules.pop, name, None)
        exec(compile("".join(lines), str(path), "exec"), mod.__dict__)
        return mod

    def test_the_change_it_launders_the_number(self):
        """With the note in the question, a figure only the note writes is a source to the figure check and to
        check_args: the laundered Rs 2,40,000 ships on attempt 2, and a wage the note supplies is taken."""
        changed = self.with_the_note_in_the_question()
        turn, _ = self.turn(changed.scripted(GRATUITY, pattern="verify", launders="Rs 2,40,000"), mod=changed)
        self.assertEqual((turn["shipped"], turn["check"]["passed"], turn["calculations"]), (2, True, []))
        self.assertIn("A note: My answer stated a figure", turn["question"])
        self.assertEqual(self.score("calc-gratuity-7y8m", turn)["provenance"], False)   # the scorer still sees it
        wage = {"calls": [{"name": "gratuity_estimate", "args": {"monthly_wage": 60000, "years": 7, "months": 8}}]}
        llm = self.model(changed, replies=[SEARCH, "Gratuity, an estimate: Rs 2,76,923 [2].",
                                           "The wage is Rs 60,000: give the calculator monthly_wage 60000.", SEARCH,
                                           wage, "Gratuity, an estimate: Rs 2,76,923 [2]."])
        turn, _ = self.turn(llm, mod=changed)
        self.assertEqual((turn["refusals"], [c["value"] for c in turn["calculations"]]), ([], [276923]))
        self.assertEqual((turn["shipped"], turn["check"]["passed"]), (2, True))       # a wrong figure, checked
        self.assertFalse(self.score("calc-gratuity-7y8m", turn)["correct"])
        unchanged, _ = self.turn(self.model(replies=llm.replies))
        self.assertEqual(unchanged["attempts"][1]["refusals"], ["gratuity_estimate"])


@unittest.skipUnless(FRAMEWORKS or REQUIRE, PINS)
class Commands(_Pinned):
    def test_agent_turn_prints_each_attempt(self):
        import agent_turn
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agent_turn.main(["--offline", "--pattern", "verify", "--invent"]), 0)
        text = out.getvalue()
        for line in ("agent turn: pattern verify, desk astar, tenant acme",
                     "  verify (lesson 10.3): check, retry or choose: the loop answers and code checks every figure",
                     "  --invent: the scripted model's first attempt writes Rs 2,50,000 in place of its calculator's "
                     "figure", "attempt 1: the loop, a turn of its own\n",
                     "  the attempt's answer: Gratuity, an estimate: Rs 2,50,000 [2].",
                     "  the figure check, code and no model: failed: no calculator, question or passage of the turn "
                     "wrote 2,50,000", "attempt 2: the loop, a turn of its own, after a note",
                     "model call 3 (reflect, gemini-3.6-flash, thinking low): in ",
                     "  the note, cut to 300 characters by code, into this attempt's system prompt, never its "
                     "question: My answer stated a figure",
                     "  -> gratuity_estimate(monthly_wage=52000, years=7, months=8)",
                     "the answer that ships: attempt 2's, the first the figure check passed",
                     "6 model calls in 2 attempts and 1 reflect call (12 at most an attempt); the answer that ships: 1 "
                     "search, 1 calculation, 0 refused or failed tool calls; stopped by nothing",
                     "by role: answer 5 calls, Rs ", "; reflect 1 call, Rs ",
                     "figure check: every figure in the model's text is a calculator's"):
            self.assertIn(line, text)
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agent_turn.main(["--offline", "--pattern", "verify", "--launder"]), 0)
        text = out.getvalue()
        for line in ("  the note writes 2,40,000: a note is never a source, so check_args refuses it as an argument "
                     "and the figure check flags it in an answer", "attempt 3: the loop, a turn of its own, after a note",
                     "the answer that ships: attempt 3's, the last of 3: the figure check passed none",
                     "8 model calls in 3 attempts and 2 reflect calls",
                     "figure check: no calculator, question or passage wrote 2,40,000 (desk_calc.unsupported)"):
            self.assertIn(line, text)
        for argv, why in ((["--offline", "--launder"], "--launder is for --offline --pattern verify"),
                          (["--offline", "--pattern", "rewoo", "--invent"], "--invent is for --offline --pattern "
                                                                            "react_text"),
                          (["--live", "--pattern", "verify", "--invent"], "--invent is for --offline")):
            with redirect_stderr(io.StringIO()) as err:
                self.assertEqual(agent_turn.main(argv), 2)
            self.assertIn(why, err.getvalue())
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agent_turn.main(["--offline", "--pattern", "verify", "--json"]), 0)
        record = json.loads(out.getvalue())
        self.assertEqual((record["pattern"], record["shipped"], len(record["attempts"])), ("verify", 1, 1))
        self.assertIn("trace", record["attempts"][0])

    def test_a_refusal_prints_its_word_once(self):
        """13 October 2026: check_args' refusal reaches the record as "refused: ...", and _result() wrote "refused: "
        in front of it again (lesson 10.2's page read "refused: refused: cap = 100 ...")."""
        import agent_turn
        tool = {"name": "calculate", "status": "error",
                "result": {"error": "refused: cap = 100 is not written in LV-07 of a handbook passage this turn read"}}
        self.assertEqual(agent_turn._result(tool),
                         ["refused: cap = 100 is not written in LV-07 of a handbook passage this turn read"])
        self.assertEqual(agent_turn._result({"name": "calculate", "status": "error", "result": {"error": "boom"}}),
                         ["refused: boom"])

    def test_agent_eval_side_by_side_saved_and_replayed(self):
        """PATTERNS=loop,verify, three runs, best-of-3: the three ways side by side with calls and rupees, then the
        same from the saves replayed at Rs 0, loop's and verify's in two files."""
        ae = load_eval("agent_eval_for_verify")
        fd, saved = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        self.addCleanup(os.remove, saved)
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            self.assertEqual(ae.main(["--offline", "--patterns", "loop,verify", "--slice",
                                      "calc-gratuity-7y8m,calc-grc-threshold,trap", "--runs", "3", "--best-of", "3",
                                      "--save", saved]), 0)
        text = out.getvalue()
        block = text[text.index("== check, retry or choose (lesson 10.3)"):]
        for line in ("== check, retry or choose (lesson 10.3): loop against verify, on the 3 rows both ran",
                     "  pass@1, loop's first run: correct 3/3 = 100.0% [43.8%, 100.0%], verified 0/3 = 0.0%",
                     "  pass@3 re-rolls, any of its first 3 runs (the ceiling a perfect chooser reaches): correct 3/3 "
                     "= 100.0% [43.8%, 100.0%], verified 3/3 = 100.0%",
                     "  best-of-3, the run the figure check chooses (code, no model): correct 3/3 = 100.0% [43.8%, "
                     "100.0%], verified 3/3 = 100.0%",
                     "  pass@3 with notes, verify's answer that ships (up to 3 attempts, a note before each retry): "
                     "correct 3/3 = 100.0% [43.8%, 100.0%], verified 1/3 = 33.3%",
                     "  the figure check's precision: of the 8 of loop's 9 runs it passes, 8 correct (100%) and 6 "
                     "verified; of the 3 of verify's 4 attempts it passes, 3 correct (100%) and 1 verified"):
            self.assertIn(line, block)
        self.assertRegex(block, r"pass@1, loop's first run: .*; 2\.0 calls and Rs \d+\.\d{4} a row")
        self.assertRegex(block, r"best-of-3, .*; 8\.0 calls and Rs \d+\.\d{4} a row")
        self.assertIn("  with notes: the figure check passed on attempt 1 in 8, on attempt 2 in 1, on attempt 3 in 0 "
                      "and on none in 0 of 9 runs (at most 3 attempts a run)", text)
        records = [json.loads(line) for line in Path(saved).read_text(encoding="utf-8").splitlines()]
        self.assertNotIn("gs://", Path(saved).read_text(encoding="utf-8"))
        checked = [r for r in records if r["arm"]["pattern"] == "verify"]
        self.assertTrue(checked and all("trace" not in a for r in checked for a in r["attempts"]))
        files = []
        for pattern, keep in (("loop", lambda r: True), ("verify", lambda r: r["run"] == 0)):
            fd, path = tempfile.mkstemp(suffix=".jsonl")
            os.close(fd)
            self.addCleanup(os.remove, path)
            ae.save([r for r in records if r["arm"]["pattern"] == pattern and keep(r)], path)
            files.append(path)
        with redirect_stdout(io.StringIO()) as again:
            self.assertEqual(ae.main(["--replay", *files, "--best-of", "3"]), 0)
        replayed = again.getvalue()
        self.assertIn(f"replayed 12 saved runs of {files[0]}, {files[1]}: rescored at Rs 0", replayed)
        self.assertIn("  best-of-3: not for this arm, which has 1 run a row", replayed)
        self.assertEqual(replayed[replayed.index("== check, retry or choose"):].splitlines()[:6],
                         [line for line in block.splitlines()[:6]])


if __name__ == "__main__":
    unittest.main()
