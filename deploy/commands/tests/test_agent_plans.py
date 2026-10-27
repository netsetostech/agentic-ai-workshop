"""Lesson 10.2's two patterns on the agent bench (commands/agent_patterns.py): plan_execute, a plan carried out a step
at a time with one replan after a refused or failed step, and rewoo, a plan written once and run in waves.

    python -m unittest commands/tests/test_agent_plans.py -v         # from deploy/
    make agent-tests                                                  # the same, in ~/graph-venv with the chat pins

The first half needs the standard library only and runs in CI's shared interpreter: read_plan() and read_rewoo() on
the forms a plan takes; check_rewoo() refusing a plan before any tool runs; needs() and next_wave() (the steps that
wait on nothing together, a refused value stopping what takes it and nothing else); resolve(); read_figure() checking
an extract worker's quote; the prompts' lines and the readers the scripted model reads them back with; the registry and
the executor models; the CI lines, make's lines and the UNOWNED.md row. The second half runs both patterns on
ScriptedPlanModel over the kit's own corpus and needs the chat image's pins (pip install -r services/chat/
requirements.txt): the plan parsed and run in order, through ToolNode with the timed wrapper; one replan after a
refusal and never a second; a plan with no step; the call cap; placeholders filled; the waves, their calls running side
by side (asserted with a barrier, not wall time); a forward placeholder and an invented literal refused; a refused
extract; each call priced at its own model's rates, the executor's flash-lite at 0.25/1.50; thinking on every call;
agent_turn.py and agent_eval.py with both, beside the loop; and the loop, react_text and plan_first as they were.
Without the pins that half is skipped and says so; with DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins steps set it, a
missing pin is an error instead.

No test calls a model or a cloud API.
"""
from __future__ import annotations

import importlib.util
import io
import json
import logging
import os
import re
import sys
import threading
import unittest
import warnings
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

KIT = Path(__file__).resolve().parents[2]
for p in (str(KIT / "commands"), str(KIT / "services/chat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import agent_patterns as ap  # noqa: E402 - the standard library and shared/ only, at import
from shared import desk_calc, prices  # noqa: E402

FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "langchain_google_genai"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
PINS = "needs the chat image's pins: pip install -r services/chat/requirements.txt"
LITE = "gemini-3.1-flash-lite"
NOTICE, ENCASH = "notice period confirmed employee acknowledged in writing", "earned leave encashed on exit"
GRATUITY = "gratuity fifteen days wages for every completed year of service"
# rewoo's plan for chained-exit-e3, as the scripted planner writes it: three searches, two reads, three calculators.
CHAINED_PLAN = "\n".join([
    'Plan: Search for the passage each figure rests on.',
    f'#E1 = retrieve[{{"query": "{NOTICE}"}}]', f'#E2 = retrieve[{{"query": "{ENCASH}"}}]',
    f'#E3 = retrieve[{{"query": "{GRATUITY}"}}]',
    '#E4 = extract[{"what": "the days NP-03 states", "from": "#E1"}]',
    '#E5 = extract[{"what": "the cap LV-07 states", "from": "#E2"}]',
    '#E6 = notice_end[{"ack_date": "2026-10-05", "days": "#E4"}]', '#E7 = encashable_days[{"balance": 50, "cap": "#E5"}]',
    '#E8 = gratuity_estimate[{"monthly_wage": 52000, "years": 7, "months": 8}]'])
TOOLS = ("retrieve", "accrued_leave", "carry_forward", "encashable_days", "notice_end", "gratuity_estimate",
         "statutory_deadline", "threshold_check")


def read(*parts) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def ok(**extra) -> dict:
    return {"state": "ok", **extra}


# ================================================================== the standard-library half
class Plans(unittest.TestCase):
    def test_how_a_call_ended_is_kept_when_it_was_not_a_stop(self):
        from types import SimpleNamespace as Reply
        self.assertEqual(ap.finish_of(Reply(response_metadata={"finish_reason": "UNEXPECTED_TOOL_CALL"})), "UNEXPECTED_TOOL_CALL")
        self.assertEqual(ap.finish_of(Reply(response_metadata={"finish_reason": "FinishReason.MALFORMED_FUNCTION_CALL"})),
                         "MALFORMED_FUNCTION_CALL")
        for metadata in ({"finish_reason": "STOP"}, {}, None):
            self.assertIsNone(ap.finish_of(Reply(response_metadata=metadata)))

    def test_a_numbered_plan(self):
        text = ("Here is the plan.\n1. Search for NP-03: retrieve {\"query\": \"notice\"}\n2) Work out the date\n"
                "   (it needs step 1)\n**3.** Answer from them\n- 4. Last\nThe 60 days. Done.")
        self.assertEqual(ap.read_plan(text), ['Search for NP-03: retrieve {"query": "notice"}', "Work out the date",
                                              "Answer from them", "Last"])
        self.assertEqual((ap.read_plan(""), ap.read_plan("I would search, then calculate.")), ([], []))

    def test_a_plan_written_once(self):
        steps = ap.read_rewoo("Plan: search first\n#E1 = retrieve[{\"query\": \"a [b]\"}]\nnoise\n"
                              "#E2 = extract[{\"what\": \"the days NP-03 states\", \"from\": \"#E1\"}]\n"
                              "**#E3** = notice_end[{\"ack_date\": \"2026-10-05\", \"days\": \"#E2\"}]\n"
                              "#E4 = retrieve[notice period]\n#E5 = retrieve[[1, 2]]")
        self.assertEqual([(s["id"], s["tool"]) for s in steps],
                         [("#E1", "retrieve"), ("#E2", "extract"), ("#E3", "notice_end"), ("#E4", "retrieve"),
                          ("#E5", "retrieve")])
        self.assertEqual((steps[0]["args"], steps[0]["why"], steps[1]["why"]), ({"query": "a [b]"}, "search first", ""))
        self.assertTrue(steps[3]["error"].startswith("its arguments are not one JSON object"))
        self.assertEqual(steps[4]["error"], "its arguments are a JSON list, not an object")
        self.assertNotIn("error", steps[2])

    def check(self, text, cap=12) -> str | None:
        return ap.check_rewoo(ap.read_rewoo(text), TOOLS, cap)

    def test_a_plan_is_refused_before_any_tool_runs(self):
        self.assertIsNone(self.check(CHAINED_PLAN))
        cases = {"no step": "no step is written as #E<n>",
                 "\n".join(f'#E{i} = retrieve[{{"query": "q{i}"}}]' for i in range(1, 14)):
                     "it has 13 steps, and a turn runs at most 12",
                 '#E1 = retrieve[{"query": "a"}]\n#E1 = retrieve[{"query": "b"}]': "#E1 is written twice",
                 "#E1 = retrieve[gratuity]": "#E1: its arguments are not one JSON object",
                 '#E1 = shell[{"cmd": "ls"}]': "#E1 calls shell, which is not one of this desk's tools",
                 '#E1 = notice_end[{"ack_date": "2026-10-05", "days": "#E2"}]\n'
                 '#E2 = retrieve[{"query": "notice"}]': "#E1 uses #E2 before #E2 runs: a step may use only the steps "
                                                        "written above it",
                 '#E1 = notice_end[{"ack_date": "2026-10-05", "days": "#E9"}]': "#E1 uses #E9, which the plan does "
                                                                                 "not write",
                 '#E1 = retrieve[{"query": "a"}]\n#E2 = extract[{"what": "x", "from": "the passages"}]':
                     "#E2 must read from the placeholder of one search written above it",
                 '#E1 = retrieve[{"query": "a"}]\n#E2 = extract[{"what": "x", "from": "#E1"}]\n'
                 '#E3 = extract[{"what": "y", "from": "#E2"}]': "#E3 must read from the placeholder of one search",
                 '#E1 = retrieve[{"query": "a"}]\n#E2 = extract[{"what": " ", "from": "#E1"}]':
                     "#E2 does not say what figure to read",
                 '#E1 = retrieve[{"query": "a"}]\n#E2 = encashable_days[{"balance": 50, "cap": "#E1"}]':
                     "#E2 gives cap the passages of #E1: a search returns passages, not a figure"}
        for plan, why in cases.items():
            self.assertTrue((self.check(plan) or "").startswith(why), (plan, self.check(plan)))
        self.assertIsNone(self.check(CHAINED_PLAN, cap=9))
        self.assertTrue(self.check(CHAINED_PLAN, cap=7).startswith("it has 8 steps, and a turn runs at most 7"))

    def test_what_each_step_waits_for(self):
        steps = ap.read_rewoo(CHAINED_PLAN)
        wants = ap.needs(steps)
        self.assertEqual(wants["#E1"], ([], []))
        self.assertEqual(wants["#E4"], (["#E1"], []))                           # an extract: its search, nothing more
        self.assertEqual(wants["#E6"], (["#E4"], ["#E1", "#E2", "#E3"]))        # a calculator: and every search above
        self.assertEqual(wants["#E8"], ([], ["#E1", "#E2", "#E3"]))

    def test_the_waves(self):
        """The steps that wait on nothing run together; each later wave is every step whose needs have run."""
        steps, outcome, waves = ap.read_rewoo(CHAINED_PLAN), {}, []
        while len(outcome) < len(steps):
            ready, never = ap.next_wave(steps, outcome)
            self.assertEqual(never, {})
            waves.append(ready)
            outcome.update({sid: ok(value=1) for sid in ready})
        self.assertEqual(waves, [["#E1", "#E2", "#E3"], ["#E4", "#E5", "#E8"], ["#E6", "#E7"]])

    def test_a_refused_value_stops_what_takes_it_and_nothing_else(self):
        steps = ap.read_rewoo(CHAINED_PLAN)
        outcome = {"#E1": ok(), "#E2": {"state": "failed"}, "#E3": ok()}
        ready, never = ap.next_wave(steps, outcome)
        self.assertEqual((ready, never), (["#E4", "#E8"], {"#E5": "#E2 was failed"}))   # #E8 runs: a search ran
        outcome.update({"#E4": {"state": "refused"}, "#E5": {"state": "skipped"}, "#E8": ok(value=240000)})
        self.assertEqual(ap.next_wave(steps, outcome), ([], {"#E6": "#E4 was refused", "#E7": "#E5 was not run"}))
        pending = {"#E1": ok()}                                                 # a search still to run holds a calculator
        self.assertEqual(ap.next_wave(steps, pending)[0], ["#E2", "#E3", "#E4"])

    def test_placeholders_filled(self):
        values = {"#E4": 60, "#E5": 45.5, "#E9": "2026-12-04"}
        self.assertEqual(ap.resolve({"ack_date": "2026-10-05", "days": " #E4 ", "cap": "#E5", "nested": ["#E9"]}, values),
                         {"ack_date": "2026-10-05", "days": 60, "cap": 45.5, "nested": ["2026-12-04"]})
        self.assertEqual(ap.resolve({"query": "wages due after #E9 and #E7"}, values),
                         {"query": "wages due after 2026-12-04 and #E7"})
        self.assertEqual(ap.placeholders({"a": "#E2 and #E1", "b": ["#E2", 3]}), ["#E2", "#E1"])

    def test_an_extract_workers_reply_is_checked(self):
        np03 = [{"n": 1, "text": "NP-03 — Notice period\nA confirmed employee at grade E3 or above serves a notice\n"
                                 "period of 60 days. Notice runs from the date of acknowledgement."}]
        quote = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
        self.assertEqual(ap.read_figure(json.dumps({"value": 60, "quote": quote}), np03), (60, quote, None))
        fenced = "```json\n" + json.dumps({"value": "60", "quote": quote}) + "\n```"
        self.assertEqual(ap.read_figure(fenced, np03)[0], 60)
        cases = {json.dumps({"value": 60, "quote": "Notice is 60 days."}): "its quote is not written in the passages it "
                                                                            "was given",
                 json.dumps({"value": 45, "quote": quote}): "its quote does not write 45",
                 json.dumps({"value": None, "quote": ""}): "the worker found no such figure in the passages",
                 "sixty days": "the worker's reply is not one JSON object with a value and a quote",
                 json.dumps({"value": "sixty", "quote": quote}): "sixty is neither a number nor a date",
                 json.dumps({"value": "2026-12-04", "quote": quote}): "its quote does not write 2026-12-04"}
        for reply, why in cases.items():
            value, _, got = ap.read_figure(reply, np03)
            self.assertEqual((value, got), (None, why), reply)
        lakh = [{"text": "Purchases up to Rs 2,00,000 are approved by the function head."}]
        self.assertEqual(ap.read_figure(json.dumps({"value": "2,00,000", "quote": "Purchases up to Rs 2,00,000 are "
                                                    "approved by the function head."}), lakh)[0], 200000)

    def test_the_executor_reads_a_codes_passages_by_name(self):
        found = {"passages": [{"n": 1, "source": "hr_policy_2026.md", "doc_type": "policy", "section": "NP-03",
                               "text": "60 days."},
                              {"n": 2, "source": "osh_code_2020.pdf", "doc_type": "statute", "section": None,
                               "text": "Every establishment..."}], "answerable": True}
        self.assertEqual(json.loads(ap.by_name(json.dumps(found))), {"passages": [
            found["passages"][0], {"n": 2, "source": "osh_code_2020.pdf", "doc_type": "statute", "section": None}],
            "answerable": True})
        self.assertEqual(ap.by_name("refused: no"), "refused: no")
        done = [{"n": 1, "text": "Search", "tools": [{"name": "retrieve", "args": {"query": "q"}, "said": "returned",
                                                       "content": json.dumps(found)}]}]
        self.assertIn("Every establishment", "\n".join(ap.done_lines(done)))                 # the solver's: whole
        self.assertNotIn("Every establishment", ap.ask_step("Q?", ["Search", "Next"], done, 2))
        self.assertNotIn("Every establishment", ap.ask_replan("Q?", done, "Step 1 was refused: no", []))
        self.assertIn("60 days.", ap.ask_step("Q?", ["Search", "Next"], done, 2))

    def test_a_tool_result_in_the_prompts_words(self):
        self.assertEqual(ap.said_of("error", "refused: cap = 100"), "refused")
        self.assertEqual(ap.said_of("success", json.dumps({"error": "retrieve did not answer", "timed_out": True})),
                         "failed")
        self.assertEqual(ap.said_of("success", json.dumps({"value": 45})), "returned")
        self.assertEqual(ap.said_line("refused", "refused: cap = 100\nis not written"), "cap = 100 is not written")
        self.assertEqual(ap.said_line("returned", '{"value": 45}'), '{"value": 45}')

    def test_the_prompts_read_back(self):
        """What the planning prompts write, the scripted model reads back as the loop's history (sent_history())."""
        found = json.dumps({"passages": [{"n": 1, "doc_type": "policy", "text": "60 days."}]})   # a handbook's: whole
        done = [{"n": 1, "text": "Search", "tools": [{"name": "retrieve", "args": {"query": "q"}, "said": "returned",
                                                       "content": found}]},
                {"n": 2, "text": "Encash", "tools": [{"name": "encashable_days", "args": {"balance": 80, "cap": 100},
                                                       "said": "refused", "content": "refused: cap = 100 is not here"}]},
                {"n": 3, "text": "Answer", "tools": [], "wrote": "I  have\nit"}]
        lines = ap.done_lines(done)
        self.assertEqual(lines[3:], ["2. Encash", '   call: encashable_days {"balance": 80, "cap": 100}',
                                     "   refused: cap = 100 is not here", "3. Answer",
                                     "   no tool call; the executor wrote: I have it"])
        step = ap.ask_step("Q?", ["Search", "Encash", "Answer", "More"], done, 4)
        self.assertTrue(step.startswith("Question: Q?\n\nThe plan:\n1. Search\n"))
        self.assertTrue(step.endswith("\n\nCarry out step 4: More"))
        self.assertEqual(ap.sent_history(step), [
            {"role": "ai", "tools": ["retrieve"]},
            {"role": "tool", "name": "retrieve", "content": found, "status": "success"},
            {"role": "ai", "tools": ["encashable_days"]},
            {"role": "tool", "name": "encashable_days", "content": "cap = 100 is not here", "status": "error"}])
        replan = ap.ask_replan("Q?", done[:2], "Step 2 was refused: cap = 100 is not here", ["Answer"])
        self.assertIn("\n\nStep 2 was refused: cap = 100 is not here\nSteps not yet run:\n3. Answer\n\nWrite the plan",
                      replan)
        self.assertTrue(ap.ask_solve("Q?", []).endswith("Done for this turn:\nNo step ran."))
        steps = ap.read_rewoo('#E1 = retrieve[{"query": "q"}]\n#E2 = extract[{"what": "x", "from": "#E1"}]\n'
                              '#E3 = encashable_days[{"balance": 50, "cap": "#E2"}]')
        outcome = {"#E1": ok(said="returned", content='{"passages": []}', call={"args": {"query": "q"}}),
                   "#E2": ok(value=45, quote="capped at 45 days."),
                   "#E3": {"state": "refused", "said": "refused", "content": "refused: no", "call": {
                       "args": {"balance": 50, "cap": 45}}}}
        self.assertEqual(ap.evidence_lines(steps, outcome)[3:], [
            '#E2 = extract[{"what": "x", "from": "#E1"}]', '   read: 45, quoting "capped at 45 days."',
            '#E3 = encashable_days[{"balance": 50, "cap": "#E2"}]', '   call: encashable_days {"balance": 50, "cap": 45}',
            "   refused: no"])
        self.assertEqual(ap.evidence_lines(steps[:1], {}), ['#E1 = retrieve[{"query": "q"}]',
                                                            "   not run: the turn stopped first"])
        sent = ap.ask_extract("the cap LV-07 states", "#E1", [{"n": 6, "source": "hr_policy_2026.md",
                                                               "section": "LV-07 — Leave on exit",
                                                               "text": "LV-07 — Leave on exit\nCapped at 45 days."}])
        self.assertEqual(ap.sent_passages(sent), [{"n": 6, "source": "hr_policy_2026.md",
                                                   "section": "LV-07 — Leave on exit",
                                                   "text": "LV-07 — Leave on exit\nCapped at 45 days."}])
        self.assertIn("The plan was refused before any tool ran: no step.", ap.ask_rewoo_solve("Q?", [], {}, "no step"))


class Registry(unittest.TestCase):
    def test_both_patterns_are_built(self):
        for name in ("plan_execute", "rewoo"):
            p = ap.PATTERNS[name]
            self.assertEqual((p.name, p.lessons, p.executor, p.text), (name, "10.2", True, False))
            self.assertNotIn(name, ap.PLANNED)
        self.assertFalse(any(ap.PATTERNS[n].executor for n in ("loop", "react_text", "plan_first")))
        self.assertEqual(ap.MAX_REPLANS, 1)
        self.assertEqual(ap.ROLES, ("plan", "act", "extract", "replan", "solve"))

    def test_an_executor_is_a_model_the_kit_prices(self):
        self.assertIn(LITE, ap.EXEC_MODELS)
        self.assertIn("gemini-3.6-flash", ap.EXEC_MODELS)
        self.assertTrue(all(m in prices.PRICES for m in ap.EXEC_MODELS))
        self.assertEqual(prices.PRICES[LITE], (0.25, 1.50))
        with self.assertRaisesRegex(ValueError, "an executor model is one of"):
            ap.scripted("q", pattern="plan_execute", model="gpt-5")
        with self.assertRaisesRegex(ValueError, "model is for the executor of plan_execute, rewoo"):
            ap.scripted("q", pattern="loop", model=LITE)

    def test_ci_make_and_unowned(self):
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_agent_plans.py -v"
        self.assertIn(line, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = KIT.parent / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                                    # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))
        agents = read("mk", "agents.mk")
        recipe = agents.split("\nagent-tests:\n", 1)[1].split("\n\n", 1)[0]
        self.assertIn("bash commands/agent-turn.sh -m unittest commands/tests/test_agent_plans.py -v", recipe)
        turn = agents.split("\nagent-turn: ", 1)[1].split("\n\n", 1)[0]
        self.assertIn(' Q="$(Q)" ROW=$(ROW) EXEC_MODEL=$(EXEC_MODEL) OFFLINE=$(OFFLINE) ', turn)
        evaluate = agents.split("\nagent-eval: ", 1)[1].split("\n\n", 1)[0]
        self.assertIn("$(if $(EXEC_MODEL),--exec-model $(EXEC_MODEL),)", evaluate)
        lines = agents.splitlines()                                             # lesson 10.4's build reads route-eval
        self.assertEqual(lines.index("route-eval: guard-project") + 2, 214)
        sh = read("commands", "agent-turn.sh")
        self.assertIn('if [ -n "${EXEC_MODEL:-}" ]; then ARGS+=(--exec-model "$EXEC_MODEL"); fi', sh)
        self.assertIn('if [ -n "${ROW:-}" ]; then ARGS+=(--row "$ROW"); fi', sh)
        unowned = read("UNOWNED.md")
        # its row, until a page quotes the file; then INDEX.md names that page (the page PR moves the row)
        row = next((l for l in read("INDEX.md").splitlines() if l.startswith("| `commands/tests/test_agent_plans.py` |")), "")
        self.assertTrue("| `commands/tests/test_agent_plans.py` | **10.2** |" in unowned
                        or row.split(" | ")[2:3] not in ([], ["-"]))
        if "| `commands/agent_patterns.py` |" in unowned:                       # the registry's row names the pattern,
            self.assertIn("`plan_execute` (10.2)", unowned)
        else:                                                                   # until lesson 10.2's page quotes the file
            registry = next(l for l in read("INDEX.md").splitlines() if l.startswith("| `commands/agent_patterns.py` |"))
            self.assertIn("10.2", registry.split(" | ")[2].split(", "))


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

    def model(self, replies=None, model=None, **kw):
        return ap._scripted_plan_class()(model=model or self.da.AGENT_MODEL, thinking_level=self.da.THINKING_LEVEL,
                                         replies=replies, **kw)

    def turn(self, name="plan_execute", row="chained-exit-e3", llm=None, executor=None, question=None, **kw):
        r = self.rows.get(row) or {}
        question = question or r["question"]
        llm = llm or ap.scripted(question, r.get("tenant", "acme"), task=r or None, pattern=name)
        return ap.run(name, question, llm=llm, executor=executor, **kw), llm

    def score(self, row: str, turn: dict) -> dict:
        spec = importlib.util.spec_from_file_location("agent_eval_for_plans_score", KIT / "evals" / "agent_eval.py")
        ae = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ae)
        return ae.score(self.rows[row], turn)

    def flagged(self, turn: dict) -> list[str]:
        return desk_calc.unsupported(turn["answer"], turn["calculations"], turn["question"],
                                     *[p.get("text") or "" for p in turn["passages"]])


@unittest.skipUnless(FRAMEWORKS or REQUIRE, PINS)
class PlanExecute(_Pinned):
    def test_the_plan_is_written_and_run_in_order(self):
        turn, llm = self.turn()
        plan = turn["plan"]
        self.assertEqual(len(plan["plans"]), 1)
        steps = plan["plans"][0]
        self.assertEqual(len(steps), 6)
        self.assertEqual([re.search(r"(\w+) \{", s).group(1) for s in steps], [
            "retrieve", "notice_end", "retrieve", "encashable_days", "retrieve", "gratuity_estimate"])
        self.assertEqual(turn["tool_calls"], [re.search(r"(\w+) \{", s).group(1) for s in steps])   # the plan's order
        self.assertEqual([e["text"] for e in plan["log"] if e["event"] == "step"], steps)
        self.assertEqual(llm.roles, ["plan"] + ["act"] * 6 + ["solve"])
        self.assertEqual([c["role"] for c in turn["calls"]], ["plan"] + ["act"] * 6 + ["solve"])
        self.assertEqual((turn["model_calls"], turn["refusals"], turn["stopped_by"], plan["replans"]), (8, [], None, 0))
        self.assertEqual([c["value"] for c in turn["calculations"]], ["2026-12-04", 45, 240000])
        self.assertEqual(turn["answer"], "Last day of notice: 4 December 2026 [1]. Earned leave encashed on exit: "
                                         "45 days [6]. Gratuity, an estimate: Rs 2,40,000 [12].")
        self.assertEqual(self.flagged(turn), [])
        self.assertEqual({k: self.score("chained-exit-e3", turn)[k] for k in ("correct", "provenance")},
                         {"correct": True, "provenance": True})
        self.assertEqual(llm.tools, [[]] + [list(TOOLS)] * 6 + [[]])    # only the executor's calls bind the tools
        self.assertIn("Carry out step 2: Last day of notice: notice_end", llm.sent[2])
        self.assertIn('   call: retrieve {"query": "notice period confirmed', llm.sent[2])    # step 1's result, read

    def test_each_step_runs_through_toolnode_with_the_timed_wrapper(self):
        from langgraph import prebuilt
        built, timed = [], []
        real_node, real_timed = prebuilt.ToolNode, self.limits.timed_tool_call

        def node(tools, **kw):
            built.append((tools, kw))
            return real_node(tools, **kw)

        def spy(request, handler):
            timed.append(request.tool_call["name"])
            return real_timed(request, handler)

        with patch.object(prebuilt, "ToolNode", node), patch.object(self.limits, "timed_tool_call", spy):
            turn, _ = self.turn()
        self.assertEqual(built, [(self.da.TOOLSETS["astar"], {"wrap_tool_call": spy})])
        self.assertEqual(timed, turn["tool_calls"])

    def test_a_refusal_is_replanned_once(self):
        turn, llm = self.turn(row="chained-exit-stated-cap")
        plan = turn["plan"]
        first, second = plan["plans"]
        self.assertIn('encashable_days {"balance": 80, "cap": 100}', first[2])                  # the question's cap
        self.assertEqual(second[:2], [f'Search for LV-07: retrieve {{"query": "{ENCASH}"}}',
                                      'Earned leave encashed on exit: encashable_days {"balance": 80, "cap": '
                                      '"<the cap LV-07 states>"}'])
        self.assertEqual(second[2:], first[3:])                                 # the steps not yet run, as they were
        self.assertEqual(llm.roles, ["plan", "act", "act", "act", "replan", "act", "act", "act", "act", "solve"])
        self.assertEqual((turn["refusals"], plan["replans"], turn["model_calls"]), (["encashable_days"], 1, 10))
        step3 = next(e for e in plan["log"] if e["event"] == "step" and e["n"] == 3)
        self.assertEqual(step3["status"], "refused")
        self.assertTrue(step3["tools"][0]["result"]["error"].startswith("refused: cap = 100 is not written in LV-07"))
        why = next(e for e in plan["log"] if e["event"] == "replan")["why"]
        self.assertTrue(why.startswith("Step 3 was refused: cap = 100 is not written in LV-07"), why)
        self.assertIn(why, llm.sent[4])                                         # what the replanner read
        self.assertEqual([c["value"] for c in turn["calculations"]], ["2026-12-04", 45, 240000])
        self.assertTrue(self.score("chained-exit-stated-cap", turn)["correct"])

    def test_never_a_second_replan(self):
        wage = {"calls": [{"name": "gratuity_estimate", "args": {"monthly_wage": 60000, "years": 7, "months": 8}}]}
        llm = self.model(["1. Gratuity: gratuity_estimate {}\n2. Again\n3. Again", wage, "1. Try again\n2. And again",
                          wage, wage, "I could not work it out."])
        turn, _ = self.turn(row="calc-gratuity-7y8m", llm=llm)
        self.assertEqual(llm.roles, ["plan", "act", "replan", "act", "act", "solve"])
        self.assertEqual((turn["plan"]["replans"], turn["refusals"]), (1, ["gratuity_estimate"] * 3))
        self.assertEqual([e["status"] for e in turn["plan"]["log"] if e["event"] == "step"], ["refused"] * 3)
        self.assertEqual((turn["answer"], turn["stopped_by"]), ("I could not work it out.", None))

    def test_a_plan_with_no_step_is_a_failure_replanned_once(self):
        llm = self.model(["I will search and then calculate.", "No steps from me either.", "Nothing to say."])
        turn, _ = self.turn(row="calc-gratuity-7y8m", llm=llm)
        self.assertEqual(llm.roles, ["plan", "replan", "solve"])
        self.assertIn("The plan could not be read: it has no numbered step.", llm.sent[1])
        self.assertEqual((turn["plan"]["plans"], turn["tool_calls"], turn["answer"]), ([[], []], [], "Nothing to say."))

    def test_an_empty_reply_to_a_planning_call_is_asked_once_more(self):
        # Gemini 3 sometimes calls a tool the planner's prompt lists as text: the reply holds nothing (finish
        # UNEXPECTED_TOOL_CALL), as every first plan of the live bench did on 22 October 2026. Asked again, it plans.
        llm = self.model(["", "No steps here.", "No steps either.", "Nothing to say."])
        turn, _ = self.turn(row="calc-gratuity-7y8m", llm=llm)
        self.assertEqual(llm.roles, ["plan", "plan", "replan", "solve"])
        self.assertNotIn(ap.NO_TOOL_HERE, llm.sent[0])
        self.assertIn(ap.NO_TOOL_HERE, llm.sent[1])
        self.assertEqual([c["role"] for c in turn["calls"]], ["plan", "plan", "replan", "solve"])
        self.assertEqual(turn["plan"]["plans"], [[], []])                     # the second plan's reply had no step either

    def test_the_call_cap_stops_a_long_plan(self):
        search = {"calls": [{"name": "retrieve", "args": {"query": GRATUITY}}]}
        llm = self.model(["\n".join(f"{i}. Search again" for i in range(1, 16)), search])
        meter = self.limits.Meter(max_model_calls=4, model=self.da.AGENT_MODEL)
        turn, _ = self.turn(row="calc-gratuity-7y8m", llm=llm, meter=meter)
        self.assertEqual((turn["stopped_by"], turn["answer"], turn["model_calls"]),
                         ("model_calls", self.limits.STOP_ANSWER, 4))
        self.assertEqual(len(llm.sent), 4)                                      # the refused call never reached it
        self.assertEqual(turn["plan"]["log"][-1], {"event": "stop", "before": "step 4"})
        self.assertFalse(turn["answerable"])

    def test_each_call_at_its_own_models_rates(self):
        """A flash-lite executor: its act calls are priced at USD 0.25/1.50 per 1M tokens, the planner's at flash's
        1.50/7.50, and the turn's Meter charges each call as the recorder prices it."""
        row = self.rows["chained-exit-e3"]
        meter = self.limits.Meter(model=self.da.AGENT_MODEL)
        executor = ap.scripted(row["question"], task=row, pattern="plan_execute", model=LITE)
        turn, _ = self.turn(executor=executor, meter=meter)
        for c in turn["calls"]:
            model = LITE if c["role"] == "act" else self.da.AGENT_MODEL
            self.assertEqual(c["model"], model)
            self.assertEqual(c["inr"], round(prices.inr(prices.usd(model, c["tokens_in"], c["tokens_out"],
                                                                   c["cached_tokens"])), 6))
        act = next(c for c in turn["calls"] if c["role"] == "act")
        self.assertAlmostEqual(act["inr"], prices.inr((act["tokens_in"] * 0.25 + act["tokens_out"] * 1.50) / 1e6),
                               places=6)
        self.assertAlmostEqual(prices.inr(meter.cost_usd), turn["inr"], places=5)
        self.assertEqual(meter.model_calls, turn["model_calls"])
        self.assertEqual({r: (v["model"], v["calls"]) for r, v in turn["roles"].items()},
                         {"plan": (self.da.AGENT_MODEL, 1), "act": (LITE, 6), "solve": (self.da.AGENT_MODEL, 1)})
        self.assertAlmostEqual(sum(v["inr"] for v in turn["roles"].values()), turn["inr"], places=5)
        self.assertEqual((turn["plan"]["planner"], turn["plan"]["executor"]), (self.da.AGENT_MODEL, LITE))
        same, _ = self.turn()
        self.assertGreater(same["roles"]["act"]["inr"], turn["roles"]["act"]["inr"])            # flash's act calls
        self.assertEqual(same["answer"], turn["answer"])

    def test_thinking_goes_with_every_call(self):
        row = self.rows["chained-exit-e3"]
        executor = ap.scripted(row["question"], task=row, pattern="plan_execute", model=LITE)
        turn, llm = self.turn(executor=executor, thinking="high")
        self.assertEqual((set(llm.seen), set(executor.seen)), ({"high"}, {"high"}))
        self.assertEqual({(c["thinking_level"], c["thinking_tokens"]) for c in turn["calls"]}, {("high", 1024)})

    def test_one_model_patterns_take_no_executor(self):
        with self.assertRaisesRegex(ValueError, "an executor model is for plan_execute, rewoo: the loop pattern"):
            self.turn(name="loop", executor=self.model())


@unittest.skipUnless(FRAMEWORKS or REQUIRE, PINS)
class Rewoo(_Pinned):
    def test_placeholders_filled_and_the_waves(self):
        turn, llm = self.turn("rewoo")
        plan = turn["plan"]
        self.assertEqual(plan["waves"], [["#E1", "#E2", "#E3"], ["#E4", "#E5", "#E8"], ["#E6", "#E7"]])
        self.assertIsNone(plan["refused"])
        self.assertEqual(llm.roles, ["plan_once", "extract", "extract", "solve"])  # planner, workers, solver
        self.assertEqual([c["role"] for c in turn["calls"]], ["plan", "extract", "extract", "solve"])
        self.assertEqual(turn["model_calls"], 1 + 2 + 1)
        waves = [e for e in plan["log"] if e["event"] == "wave"]
        reads = {s["id"]: (s["value"], s["quote"]) for s in waves[1]["steps"] if s["tool"] == "extract"}
        self.assertEqual(reads, {"#E4": (60, "A confirmed employee at grade E3 or above serves a notice period of 60 "
                                              "days."),
                                 "#E5": (45, "Earned leave is encashed on exit at basic pay, capped at 45 days.")})
        run = {s["id"]: s for w in waves for s in w["steps"] if s["tool"] != "extract"}
        self.assertEqual((run["#E6"]["written"], run["#E6"]["args"]),
                         ({"ack_date": "2026-10-05", "days": "#E4"}, {"ack_date": "2026-10-05", "days": 60}))
        self.assertEqual(run["#E7"]["args"], {"balance": 50, "cap": 45})
        ai = [m for m in turn["trace"] if [t["name"] for t in m["tools"]]]
        self.assertEqual([[t["name"] for t in m["tools"]] for m in ai],
                         [["retrieve"] * 3, ["gratuity_estimate"], ["notice_end", "encashable_days"]])
        self.assertTrue(all(m["call"] is None for m in ai))                     # built by code, never sent
        self.assertEqual(sorted(c["value"] for c in turn["calculations"] if c["unit"] != "date"), [45, 240000])
        self.assertEqual({k: self.score("chained-exit-e3", turn)[k] for k in ("correct", "provenance")},
                         {"correct": True, "provenance": True})
        self.assertEqual(self.flagged(turn), [])

    def test_a_waves_calls_run_side_by_side(self):
        """Overlap is asserted, not wall time: each search waits at a barrier the three must reach together. The loop
        ranks the three searches first, so the lane's own CPU-bound ranking (which threads share) costs nothing here."""
        from shared import documind_tools
        self.turn("loop")
        barrier, started, ended = threading.Barrier(3, timeout=20), [], []
        row = self.rows["chained-exit-e3"]
        llm = ap.scripted(row["question"], task=row, pattern="rewoo")
        with ap.offline():
            lane = documind_tools.retrieve

            def retrieve(*args, **kw):
                started.append(kw.get("tenant_id") or args[1])
                barrier.wait()                                  # BrokenBarrierError if they ran one after another
                try:
                    return lane(*args, **kw)
                finally:
                    ended.append(1)

            with patch.object(documind_tools, "retrieve", retrieve):
                turn = ap.run("rewoo", row["question"], llm=llm)
        self.assertEqual((len(started), len(ended), turn["retrieve_calls"]), (3, 3, 3))
        self.assertFalse(barrier.broken)
        self.assertEqual(turn["plan"]["waves"][0], ["#E1", "#E2", "#E3"])

    def test_a_forward_placeholder_is_refused_before_any_tool_runs(self):
        llm = self.model(['#E1 = notice_end[{"ack_date": "2026-10-05", "days": "#E2"}]\n'
                          '#E2 = retrieve[{"query": "notice period"}]', "I could not plan this."])
        turn, _ = self.turn("rewoo", row="calc-notice-e3", llm=llm)
        self.assertTrue(turn["plan"]["refused"].startswith("#E1 uses #E2 before #E2 runs"))
        self.assertEqual((turn["tool_calls"], turn["plan"]["waves"], turn["model_calls"]), ([], [], 2))
        self.assertEqual(llm.roles, ["plan_once", "solve"])
        self.assertIn("The plan was refused before any tool ran: #E1 uses #E2 before #E2 runs", llm.sent[1])

    def test_an_invented_literal_is_refused_and_nothing_replans(self):
        turn, llm = self.turn("rewoo", row="chained-exit-stated-cap")
        self.assertNotIn("replan", llm.roles)
        self.assertEqual(turn["refusals"], ["encashable_days"])
        e5 = next(s for e in turn["plan"]["log"] if e["event"] == "wave" for s in e["steps"] if s["id"] == "#E5")
        self.assertEqual((e5["args"], e5["state"]), ({"balance": 80, "cap": 100}, "refused"))
        self.assertTrue(e5["result"]["error"].startswith("refused: cap = 100 is not written in LV-07"))
        self.assertIn("Earned leave encashed on exit: not worked out, as encashable_days refused what it was given",
                      turn["answer"])
        got = self.score("chained-exit-stated-cap", turn)
        self.assertEqual((got["correct"], got["provenance"]), (False, False))
        self.assertIn("encashable_days: the figure is not stated", got["why"])
        self.assertEqual(self.flagged(turn), [])                                # no figure of its own, all the same

    def test_a_refused_extract_stops_its_calculator(self):
        plan = ('#E1 = retrieve[{"query": "notice period confirmed employee acknowledged in writing"}]\n'
                '#E2 = extract[{"what": "the days NP-03 states", "from": "#E1"}]\n'
                '#E3 = notice_end[{"ack_date": "2026-10-05", "days": "#E2"}]')
        llm = self.model([plan, json.dumps({"value": 60, "quote": "Notice is sixty days."}), "Not worked out."])
        turn, _ = self.turn("rewoo", row="calc-notice-e3", llm=llm)
        outcome = [e for e in turn["plan"]["log"] if e["event"] in ("wave", "skip")]
        self.assertEqual(outcome[1]["steps"][0]["why"], "its quote is not written in the passages it was given")
        self.assertEqual(outcome[2], {"event": "skip", "id": "#E3", "why": "#E2 was refused"})
        self.assertEqual((turn["tool_calls"], turn["calculations"]), (["retrieve"], []))
        self.assertIn("   not run: #E2 was refused", llm.sent[2])

    def test_each_call_at_its_own_models_rates(self):
        row = self.rows["chained-exit-e3"]
        meter = self.limits.Meter(model=self.da.AGENT_MODEL)
        executor = ap.scripted(row["question"], task=row, pattern="rewoo", model=LITE)
        turn, llm = self.turn("rewoo", executor=executor, meter=meter)
        self.assertEqual((llm.roles, executor.roles), (["plan_once", "solve"], ["extract", "extract"]))
        for c in turn["calls"]:
            model = LITE if c["role"] == "extract" else self.da.AGENT_MODEL
            self.assertEqual((c["model"], c["inr"]), (model, round(prices.inr(prices.usd(
                model, c["tokens_in"], c["tokens_out"], c["cached_tokens"])), 6)))
        self.assertAlmostEqual(prices.inr(meter.cost_usd), turn["inr"], places=5)

    def test_the_call_cap(self):
        """A plan of more steps than the turn's calls is refused before any tool runs, so its tools stay bounded; its
        workers count against the cap, and the call past it stops the turn."""
        many = "\n".join(f'#E{i} = retrieve[{{"query": "q{i}"}}]' for i in range(1, 14))
        turn, _ = self.turn("rewoo", row="calc-notice-e3", llm=self.model([many, "No."]))
        self.assertTrue(turn["plan"]["refused"].startswith("it has 13 steps, and a turn runs at most 12"))
        self.assertEqual((turn["tool_calls"], turn["model_calls"]), ([], 2))
        reads = "\n".join([f'#E1 = retrieve[{{"query": "{NOTICE}"}}]']
                          + [f'#E{i} = extract[{{"what": "the days NP-03 states", "from": "#E1"}}]' for i in (2, 3, 4)])
        quote = json.dumps({"value": 60, "quote": "A confirmed employee at grade E3 or above serves a notice period of "
                                                  "60 days."})
        meter = self.limits.Meter(max_model_calls=4, model=self.da.AGENT_MODEL)
        turn, llm = self.turn("rewoo", row="calc-notice-e3", llm=self.model([reads, quote]), meter=meter)
        self.assertEqual((turn["stopped_by"], turn["answer"], turn["model_calls"]),
                         ("model_calls", self.limits.STOP_ANSWER, 4))
        self.assertEqual(llm.roles, ["plan_once", "extract", "extract", "extract"])
        self.assertEqual(turn["plan"]["log"][-1], {"event": "stop", "before": "solve"})

    def test_thinking_goes_with_every_call(self):
        turn, llm = self.turn("rewoo", thinking="minimal")
        self.assertEqual(llm.seen, ["minimal"] * 4)
        self.assertEqual({(c["thinking_level"], c["thinking_tokens"]) for c in turn["calls"]}, {("minimal", 0)})


@unittest.skipUnless(FRAMEWORKS or REQUIRE, PINS)
class Beside(_Pinned):
    """The 10.1 patterns as they were, and the loop on a chained row."""
    KEYS = {"answer", "passages", "calculations", "tool_calls", "refusals", "retrieve_calls", "answerable", "stopped_by",
            "pattern", "desk", "tenant", "question", "thinking", "composed", "calls", "trace", "model_calls",
            "tokens_in", "cached_tokens", "thinking_tokens", "visible_tokens", "tokens_out", "inr", "rag_inr"}

    def test_the_10_1_patterns_keep_their_record(self):
        for name in ("loop", "react_text", "plan_first"):
            turn, _ = self.turn(name, row="calc-gratuity-7y8m")
            self.assertEqual(set(turn), self.KEYS, name)
            self.assertFalse(any("role" in c for c in turn["calls"]), name)
            self.assertEqual((turn["model_calls"], turn["answer"]), (3, "Gratuity, an estimate: Rs 2,40,000 [2]."))
        self.assertEqual(set(self.turn("rewoo", row="calc-gratuity-7y8m")[0]), self.KEYS | {"plan", "roles"})

    def test_the_loop_on_a_chained_row(self):
        turn, llm = self.turn("loop")
        self.assertEqual(turn["tool_calls"], ["retrieve", "notice_end", "retrieve", "encashable_days", "retrieve",
                                              "gratuity_estimate"])
        self.assertEqual((turn["model_calls"], llm.slip), (7, False))
        self.assertTrue(self.score("chained-exit-e3", turn)["correct"])
        stated, _ = self.turn("loop", row="chained-exit-stated-cap")        # it reads LV-07 before its calculator
        self.assertEqual((stated["refusals"], [c["value"] for c in stated["calculations"]]),
                         ([], ["2026-12-04", 45, 240000]))
        text, _ = self.turn("react_text", row="chained-exit-saturday")
        self.assertEqual([c["value"] for c in text["calculations"]], ["2026-12-05", 45, 210000])
        self.assertIn("1. Search for the passage NP-03 is in. 2. Call notice_end", self.turn("plan_first")[0]["calls"][0]
                      ["text"])

    def test_agent_turn_prints_both(self):
        import agent_turn
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agent_turn.main(["--offline", "--pattern", "plan_execute", "--row",
                                              "chained-exit-stated-cap", "--exec-model", LITE]), 0)
        text = out.getvalue()
        for line in ("agent turn: pattern plan_execute, desk astar, tenant acme",
                     f"  the planner: gemini-3.6-flash (plan, replan and solve); the executor: {LITE} (act; "
                     "EXEC_MODEL= names another)",
                     "  the plan:", "    3. Earned leave encashed on exit: encashable_days {\"balance\": 80, \"cap\": 100}",
                     "step 3: Earned leave encashed on exit", f"  model call 4 (act, {LITE}, thinking low): in ",
                     "  the step was refused", "model call 5 (replan, gemini-3.6-flash, thinking low): in ",
                     "  the plan for the work still to do:", "plans: 2 written, 1 replan (at most 1 a turn)",
                     f"by role: plan 1 call, Rs ", f"act 7 calls, Rs ", f"({LITE}); replan 1 call",
                     "  -> no tool: the answer, from the steps' results",
                     "10 model calls (12 at most), 3 searches, 3 calculations, 1 refused or failed tool call; stopped "
                     "by nothing", "figure check: every figure in the model's text is a calculator's"):
            self.assertIn(line, text)
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agent_turn.main(["--offline", "--pattern", "rewoo", "--row", "chained-exit-e3"]), 0)
        text = out.getvalue()
        for line in ("  the plan, written once:", '    #E4 = extract[{"what": "the days NP-03 states", "from": "#E1"}]',
                     "wave 1: #E1, #E2, #E3, together", '  #E4 = extract(what="the days NP-03 states", from="#E1")',
                     '       = 60, quoting "A confirmed employee at grade E3 or above serves a notice period of 60 days."',
                     '  #E6 = notice_end(ack_date="2026-10-05", days="#E4"), run as notice_end(ack_date="2026-10-05", '
                     "days=60)", "waves: 3 (#E1, #E2, #E3 | #E4, #E5, #E8 | #E6, #E7)",
                     "4 model calls (12 at most), 3 searches, 3 calculations"):
            self.assertIn(line, text)
        for argv, why in ((["--offline", "--exec-model", LITE], "--exec-model is for plan_execute, rewoo: the loop"),
                          (["--offline", "--row", "chained-exit-nine"], "--row names one row of evals/agent_tasks.jsonl"),
                          (["--offline", "--row", "chained-exit-e3", "--question", "q?"], "in place of --question")):
            with redirect_stderr(io.StringIO()) as err:
                self.assertEqual(agent_turn.main(argv), 2)
            self.assertIn(why, err.getvalue())

    def test_agent_eval_scores_both_beside_the_loop(self):
        spec = importlib.util.spec_from_file_location("agent_eval_for_plans", KIT / "evals" / "agent_eval.py")
        ae = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ae)
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            self.assertEqual(ae.main(["--offline", "--patterns", "loop,plan_execute,rewoo", "--slice", "chained"]), 0)
        text = out.getvalue()
        for arm in ("loop", "plan_execute", "rewoo"):
            self.assertIn(f"== {arm}, thinking default (low), desk astar: 3 rows x 1 run", text)
        self.assertEqual(len(re.findall(r"chained-exit-stated-cap +chained +yes +yes ", text)), 2)   # loop, plan_execute
        self.assertRegex(text, r"chained-exit-stated-cap +chained +no +no +3\.0 .*no encashable_days call returned it")
        self.assertIn("  the plans: replanned in 1 of 3 runs", text)
        self.assertIn("  the plans: refused before any tool ran in 0 of 3 runs, 3.0 waves a run", text)
        self.assertIn("  by role, a run: plan 1.0 calls, Rs ", text)
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            self.assertEqual(ae.main(["--offline", "--patterns", "plan_execute", "--slice", "chained",
                                      "--exec-model", f"default,{LITE}"]), 0)
        text = out.getvalue()
        self.assertIn(f"; an executor on {LITE} | 3 rows, 2 arms", text)
        self.assertIn(f"== plan_execute, thinking default (low), desk astar, executor {LITE}: 3 rows x 1 run", text)
        self.assertIn(f"act 6.3 calls, Rs 0.2136 ({LITE})", text)                # 6, 6, and 7 with its replan
        self.assertIn(f"paired (correct), 3 rows: both 3, default only 0, {LITE} only 0, neither 0", text)
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(ae.main(["--offline", "--patterns", "loop", "--exec-model", LITE]), 2)
        self.assertIn("--exec-model is for plan_execute, rewoo, and --patterns names neither", err.getvalue())


if __name__ == "__main__":
    unittest.main()
