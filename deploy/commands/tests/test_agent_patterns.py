"""Lesson 10.1's two patterns on the agent bench (commands/agent_patterns.py): react_text, prompted ReAct that code
parses, and plan_first, the loop with a plan-first instruction.

    python -m unittest commands/tests/test_agent_patterns.py -v      # from deploy/
    make agent-tests                                                  # the same, in ~/graph-venv with the chat pins

The first half needs the standard library only and runs in CI's shared interpreter: read_step(), the parser, on every
form a reply takes; the cut, one marked line; the registry; the CI lines, make agent-tests and the UNOWNED.md row. The
second half runs the patterns on scripted models over the kit's own corpus and needs the chat image's pins (pip install
-r services/chat/requirements.txt). react_text: the gap plan's P1 cases (a scripted Action runs gratuity_estimate
through ToolNode and its value is the next Observation; an invented wage comes back as an Observation carrying
check_args' refusal; a malformed Action gets a format Observation and the corrected Action runs; a model-written
"Observation: Rs 2,50,000" is cut and never reaches the answer; a looping script ends with stopped_by model_calls, or,
on the turn's own limits, a search loop resending every Observation reaches the rupees first; no request carries a
function declaration), the ToolNode and its timed wrapper, the loop's own wrappers at the model call, the stop sequence
sent and honoured, the Change-it (the cut deleted: the invented figure is the answer and desk_calc.unsupported() flags
it), and thinking on every call. plan_first: the instruction leads the desk's prompt, the loop's middleware, tools and
graph are its own, the plan is written and the loop still decides. Then agent_turn.py and agent_eval.py with both.
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
GRATUITY = "I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?"
SEARCH = ('Thought: I search.\n'
          'Action: retrieve[{"query": "gratuity fifteen days wages for every completed year of service"}]')
GRATUITY_ACTION = 'Thought: I call it.\nAction: gratuity_estimate[{"monthly_wage": 52000, "years": 7, "months": 8}]'
ANSWER = "Thought: I have it.\nFinal Answer: Gratuity, an estimate: Rs 2,40,000 [2]."


def read(*parts) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def flagged(turn: dict) -> list[str]:
    return desk_calc.unsupported(turn["answer"], turn["calculations"], turn["question"],
                                 *[p.get("text") or "" for p in turn["passages"]])


# ================================================================== the standard-library half
class Parser(unittest.TestCase):
    def test_an_action(self):
        text = 'Thought: I need the passage.\nAction: retrieve[{"query": "gratuity [s.53]"}]'
        got = ap.read_step(text + "\n")
        self.assertEqual(got, {"read": text, "action": {"name": "retrieve", "args": {"query": "gratuity [s.53]"}}})

    def test_a_final_answer_ends_the_turn(self):
        got = ap.read_step("Thought: I have it.\nFinal Answer: Gratuity, an estimate: Rs 2,40,000 [2].")
        self.assertEqual(got["final"], "Gratuity, an estimate: Rs 2,40,000 [2].")
        self.assertNotIn("action", got)
        got = ap.read_step('Action: retrieve[{"query": "q"}]\nFinal Answer: done')     # no Observation between them
        self.assertEqual((got.get("final"), got.get("action")), ("done", None))

    def test_a_label_may_carry_emphasis(self):
        got = ap.read_step('**Thought:** I search.\n**Action:** retrieve[{"query": "q"}]')
        self.assertEqual(got["action"], {"name": "retrieve", "args": {"query": "q"}})

    def test_a_format_error_names_the_fix(self):
        cases = {"Thought: I will think about it.": "no Action and no Final Answer. Write one Action, as Action: <tool>[",
                 "": "no Action and no Final Answer",
                 'Action: retrieve[{"query": "a"}]\nAction: retrieve[{"query": "b"}]': "2 Actions in one reply. Write",
                 'Action: retrieve\nAction Input: {"query": "gratuity"}':                # LangChain's older protocol
                     "the Action is not written as <tool>[<its arguments, as one JSON object>]",
                 "Action: gratuity_estimate[monthly_wage=52000, years=7]":
                     "the arguments of gratuity_estimate are not one JSON object in brackets (Expecting value)",
                 'Action: retrieve["gratuity"]': "(a JSON str, not an object)",
                 'Action: retrieve[{"query": "q"}': "(no ] after the object)"}
        for text, why in cases.items():
            got = ap.read_step(text)
            self.assertTrue(got["error"].startswith(ap.FORMAT), text)
            self.assertIn(why, got["error"], text)
            self.assertNotIn("action", got, text)
            self.assertNotIn("final", got, text)

    def test_the_cut(self):
        wrote = (GRATUITY_ACTION + "\nObservation: Rs 2,50,000\nThought: The calculator returned it.\n"
                 "Final Answer: Gratuity, an estimate: Rs 2,50,000.")
        got = ap.read_step(wrote)
        self.assertEqual(got, {"read": GRATUITY_ACTION, "action": {"name": "gratuity_estimate", "args": {
            "monthly_wage": 52000, "years": 7, "months": 8}}})
        self.assertEqual(ap.STOP, "Observation:")

    def test_the_cut_is_one_marked_line(self):
        """Lesson 10.1's Change-it deletes one line: the only one marked THE CUT, the only split at the stop."""
        lines = read("commands", "agent_patterns.py").splitlines()
        marked = [line.strip() for line in lines if "THE CUT" in line]
        self.assertEqual(len(marked), 1)
        self.assertTrue(marked[0].startswith("text = text.split(STOP, 1)[0]"))
        self.assertEqual(sum("split(STOP" in line for line in lines), 1)


class Registry(unittest.TestCase):
    def test_both_patterns_are_built(self):
        """10.1's two after the loop; the later lessons' patterns follow them (test_agent_plans.py has 10.2's)."""
        self.assertEqual(list(ap.PATTERNS)[:3], ["loop", "react_text", "plan_first"])
        self.assertFalse({"react_text", "plan_first"} & set(ap.PLANNED))
        self.assertEqual({n: (p.lessons, p.text) for n, p in list(ap.PATTERNS.items())[:3]},
                         {"loop": ("10.1-10.3, 10.5", False), "react_text": ("10.1", True),
                          "plan_first": ("10.1", False)})
        self.assertTrue(ap.PLAN_FIRST.startswith("Plan first. Before your first tool call, write your plan"))

    def test_ci_and_make_run_it(self):
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_agent_patterns.py -v"
        self.assertIn(line, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = KIT.parent / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                                    # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))
        agents = read("mk", "agents.mk")                    # make agent-tests runs it, in its own recipe
        recipe = agents.split("\nagent-tests:\n", 1)[1].split("\n\n", 1)[0]
        self.assertIn("bash commands/agent-turn.sh -m unittest commands/tests/test_agent_patterns.py -v", recipe)
        self.assertIn("| `commands/tests/test_agent_patterns.py` | **10.1** |", read("UNOWNED.md"))


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

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def text_model(self, **kw):
        return ap._scripted_text_class()(model=self.da.AGENT_MODEL, thinking_level=self.da.THINKING_LEVEL, **kw)

    def turn(self, name="react_text", llm=None, question=GRATUITY, mod=ap, **kw):
        llm = llm or mod.scripted(question, pattern=name)
        with mod.offline():
            return mod.run(name, question, llm=llm, **kw), llm


@unittest.skipUnless(FRAMEWORKS or REQUIRE, PINS)
class ReactText(_Pinned):
    def test_a_scripted_action_runs_and_its_value_is_the_next_observation(self):
        turn, llm = self.turn()
        self.assertEqual((turn["tool_calls"], turn["refusals"], turn["stopped_by"], turn["model_calls"]),
                         (["retrieve", "gratuity_estimate"], [], None, 3))
        self.assertEqual([c["value"] for c in turn["calculations"]], [240000])
        self.assertEqual(turn["answer"], "Gratuity, an estimate: Rs 2,40,000 [2].")
        self.assertEqual(turn["trace"][1]["react"]["action"],
                         {"name": "gratuity_estimate", "args": {"monthly_wage": 52000, "years": 7, "months": 8}})
        label, observation = ap._blocks(llm.sent[2])[-1]                      # the last thing call 3 read
        self.assertEqual(label, "Observation")
        self.assertEqual((json.loads(observation)["calculator"], json.loads(observation)["value"]),
                         ("gratuity_estimate", 240000))
        self.assertEqual([s["call"] for s in turn["trace"]], [1, 2, 3])
        self.assertEqual(flagged(turn), [])
        loop, _ = self.turn("loop")                                             # the loop, on the same script
        for key in ("answer", "tool_calls", "calculations", "passages", "refusals"):
            self.assertEqual(turn[key], loop[key], key)

    def test_the_action_runs_through_toolnode_with_the_timed_wrapper(self):
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
            self.turn()
        self.assertEqual(built, [(self.da.TOOLSETS["astar"], {"wrap_tool_call": spy})])
        self.assertEqual(timed, ["retrieve", "gratuity_estimate"])
        self.assertIn("ToolNode(TOOLS, wrap_tool_call=limits.timed_tool_call)", read("services", "chat", "brains.py"))

    def test_every_call_goes_through_the_loops_wrappers(self):
        """DeskTurnLimits around the recorder: the Meter counts every call and prices it as the agent's model, whatever
        the Meter's own model, and the recorder's rupees are the Meter's."""
        meter = self.limits.Meter(model="gemini-3.1-flash-lite")
        turn, _ = self.turn(meter=meter)
        self.assertEqual(meter.model_calls, turn["model_calls"])
        self.assertAlmostEqual(prices.inr(meter.cost_usd), turn["inr"], places=5)
        self.assertEqual({c["model"] for c in turn["calls"]}, {self.da.AGENT_MODEL})

    def test_an_invented_wage_comes_back_as_an_observation(self):
        wage = 'Thought: I call it.\nAction: gratuity_estimate[{"monthly_wage": 60000, "years": 7, "months": 8}]'
        turn, llm = self.turn(llm=self.text_model(replies=[SEARCH, wage, GRATUITY_ACTION, ANSWER]))
        self.assertEqual((turn["refusals"], turn["model_calls"]), (["gratuity_estimate"], 4))
        label, observation = ap._blocks(llm.sent[2])[-1]
        self.assertEqual(label, "Observation")
        self.assertTrue(observation.startswith("refused: monthly_wage = 60000 is a fact about the person that their "
                                               "message does not state: ask them for it"), observation)
        self.assertEqual(turn["trace"][1]["tools"][0]["status"], "error")
        self.assertEqual([c["value"] for c in turn["calculations"]], [240000])
        self.assertEqual(turn["answer"], "Gratuity, an estimate: Rs 2,40,000 [2].")

    def test_a_malformed_action_gets_a_format_observation_and_the_corrected_action_runs(self):
        malformed = "Thought: I call it.\nAction: gratuity_estimate[monthly_wage=52000, years=7, months=8]"
        turn, llm = self.turn(llm=self.text_model(replies=[SEARCH, malformed, GRATUITY_ACTION, ANSWER]))
        self.assertEqual((turn["tool_calls"], turn["refusals"], turn["model_calls"]),
                         (["retrieve", "gratuity_estimate"], [], 4))
        label, observation = ap._blocks(llm.sent[2])[-1]
        self.assertEqual(label, "Observation")
        self.assertTrue(observation.startswith(ap.FORMAT + "the arguments of gratuity_estimate are not one JSON "
                                                           "object"), observation)
        self.assertEqual((turn["trace"][1]["tools"], turn["trace"][1]["react"]["error"]), ([], observation))
        self.assertEqual([c["value"] for c in turn["calculations"]], [240000])

    def test_the_stop_sequence_cuts_an_invented_observation(self):
        row = self.rows["calc-gratuity-7y8m"]
        held = self.text_model(task=row, invents="Rs 2,50,000")                # honours its stop, as Gemini does
        turn, _ = self.turn(llm=held)
        self.assertEqual(held.stops, [[ap.STOP]] * 3)
        self.assertFalse(any(ap.STOP in c["text"] for c in turn["calls"]))     # no reply holds one
        self.assertEqual(turn["answer"], "Gratuity, an estimate: Rs 2,40,000 [2].")
        loose = ap.scripted(GRATUITY, pattern="react_text", invents="Rs 2,50,000")
        self.assertFalse(loose.honours_stop)                                    # a stop that does not hold
        turn, _ = self.turn(llm=loose)
        self.assertIn("\nObservation: Rs 2,50,000\n", turn["calls"][1]["text"])
        self.assertTrue(turn["trace"][1]["react"]["cut"].startswith("Observation: Rs 2,50,000\n"))
        self.assertEqual((turn["answer"], [c["value"] for c in turn["calculations"]]),
                         ("Gratuity, an estimate: Rs 2,40,000 [2].", [240000]))
        self.assertNotIn("2,50,000", turn["composed"])
        self.assertEqual(flagged(turn), [])

    def without_the_cut(self):
        """agent_patterns.py with the line marked THE CUT deleted, as lesson 10.1's Change-it deletes it, loaded in
        memory under its own path; the file on disk is not touched."""
        path = KIT / "commands" / "agent_patterns.py"
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        marked = [i for i, line in enumerate(lines) if "THE CUT" in line]
        self.assertEqual(len(marked), 1)
        name = "agent_patterns_without_the_cut"
        mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None, origin=str(path)))
        mod.__file__ = str(path)
        sys.modules[name] = mod
        self.addCleanup(sys.modules.pop, name, None)
        exec(compile("".join(line for i, line in enumerate(lines) if i not in marked), str(path), "exec"), mod.__dict__)
        return mod

    def test_without_the_cut_the_invention_is_the_answer_and_unsupported_flags_it(self):
        changed = self.without_the_cut()
        turn, _ = self.turn(llm=changed.scripted(GRATUITY, pattern="react_text", invents="Rs 2,50,000"), mod=changed)
        self.assertEqual(turn["answer"], "Gratuity, an estimate: Rs 2,50,000 [2].")
        self.assertEqual((turn["tool_calls"], turn["calculations"], turn["model_calls"]), (["retrieve"], [], 2))
        self.assertIn("Observation: Rs 2,50,000", turn["trace"][1]["react"]["read"])
        self.assertEqual(flagged(turn), ["2,50,000"])
        turn, _ = self.turn(llm=changed.scripted(GRATUITY, pattern="react_text"), mod=changed)
        self.assertEqual((turn["answer"], flagged(turn)), ("Gratuity, an estimate: Rs 2,40,000 [2].", []))

    def test_the_call_cap_stops_a_loop(self):
        again = 'Thought: I search again.\nAction: retrieve[{"query": "gratuity"}]'
        for reply, cap in ((again, 3), ("Thought: I will think about it some more.", self.limits.MAX_MODEL_CALLS)):
            llm = self.text_model(replies=[reply])                              # a search loop, then a format loop
            turn, _ = self.turn(llm=llm, meter=self.limits.Meter(max_model_calls=cap, model=self.da.AGENT_MODEL))
            self.assertEqual((turn["stopped_by"], turn["answer"], turn["model_calls"]),
                             ("model_calls", self.limits.STOP_ANSWER, cap))
            self.assertEqual(len(llm.sent), cap)                                # the refused call never reached it
            self.assertIsNone(turn["trace"][-1]["call"])
            self.assertFalse(turn["answerable"])
        turn, _ = self.turn(llm=self.text_model(replies=[again]))              # every Observation resent each call:
        self.assertEqual(turn["stopped_by"], "turn_budget")                     # the rupees run out before the calls
        self.assertLess(turn["model_calls"], self.limits.MAX_MODEL_CALLS)
        self.assertGreaterEqual(turn["inr"], self.limits.TURN_BUDGET_INR)

    def test_no_request_carries_a_function_declaration(self):
        from langchain_core.utils.function_calling import convert_to_openai_tool
        turn, llm = self.turn()
        for settings in llm.settings:
            self.assertFalse({"tools", "functions", "tool_choice", "tool_config"} & set(settings), settings)
        with self.assertRaises(NotImplementedError):                           # a model with no function calling
            llm.bind_tools(self.da.TOOLSETS["astar"])
        system = llm.system[0]
        self.assertEqual(set(llm.system), {system})
        self.assertEqual(system, ap.react_prompt("astar"))
        self.assertTrue(system.startswith(self.da.system_prompt("astar") + "\n\n" + ap.REACT_PROTOCOL))
        for tool, line in zip(self.da.TOOLSETS["astar"], system.splitlines()[-len(self.da.TOOLSETS["astar"]):]):
            declared = convert_to_openai_tool(tool)["function"]
            self.assertEqual(json.loads(line), {**declared, "description": " ".join(declared["description"].split())})

    def test_thinking_goes_with_every_call(self):
        turn, llm = self.turn(thinking="high")
        self.assertEqual(llm.seen, ["high"] * 3)
        self.assertEqual({(c["thinking_level"], c["thinking_tokens"]) for c in turn["calls"]}, {("high", 1024)})
        turn, llm = self.turn()
        self.assertEqual(llm.seen, [None] * 3)                                  # unset: the model's own level
        self.assertEqual({c["thinking_level"] for c in turn["calls"]}, {self.da.THINKING_LEVEL})


@unittest.skipUnless(FRAMEWORKS or REQUIRE, PINS)
class PlanFirst(_Pinned):
    def test_the_instruction_leads_the_desks_prompt_and_the_loop_is_its_own(self):
        from langchain.agents import create_agent
        built = []

        def capture(**kw):
            built.append(kw)
            return create_agent(**kw)

        with patch("langchain.agents.create_agent", capture):
            self.turn("plan_first")
            self.turn("loop")
        plan, loop = built
        self.assertEqual(plan["system_prompt"], ap.PLAN_FIRST + "\n\n" + self.da.system_prompt("astar"))
        self.assertEqual(loop["system_prompt"], self.da.system_prompt("astar"))
        self.assertEqual([type(m).__name__ for m in plan["middleware"]], ["DeskTurnLimits", "Recorder", "DeskGuard"])
        self.assertEqual((plan["tools"], plan["checkpointer"]), (loop["tools"], False))
        self.assertEqual(sorted(create_agent(**plan).get_graph().nodes), sorted(create_agent(**loop).get_graph().nodes))

    def test_the_plan_is_written_and_the_loop_still_decides(self):
        turn, _ = self.turn("plan_first")
        loop, _ = self.turn("loop")
        self.assertTrue(turn["trace"][0]["text"].startswith(
            "Plan: 1. Search for the passage the figure rests on. 2. Call gratuity_estimate with numbers the question"))
        for key in ("answer", "tool_calls", "calculations", "refusals"):
            self.assertEqual(turn[key], loop[key], key)
        self.assertGreater(turn["calls"][0]["visible_tokens"], loop["calls"][0]["visible_tokens"])   # written once
        self.assertGreater(turn["calls"][2]["tokens_in"], loop["calls"][2]["tokens_in"])             # read back
        row = self.rows["calc-gratuity-7y8m"]
        left = ap._scripted_class()(model=self.da.AGENT_MODEL, thinking_level="low", task=row, slip=True)
        turn, _ = self.turn("plan_first", llm=left)         # it plans the calculator, then writes the figure itself
        self.assertIn("2. Call gratuity_estimate", turn["trace"][0]["text"])
        self.assertEqual((turn["tool_calls"], turn["calculations"]), (["retrieve"], []))
        self.assertEqual(flagged(turn), ["2,40,000"])

    def test_thinking_goes_with_every_call(self):
        turn, llm = self.turn("plan_first", thinking="minimal")
        self.assertEqual(llm.seen, ["minimal"] * 3)
        self.assertEqual({(c["thinking_level"], c["thinking_tokens"]) for c in turn["calls"]}, {("minimal", 0)})


@unittest.skipUnless(FRAMEWORKS or REQUIRE, PINS)
class Commands(_Pinned):
    def test_agent_turn_prints_both(self):
        import agent_turn
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agent_turn.main(["--offline", "--pattern", "react_text"]), 0)
        text = out.getvalue()
        for line in ("agent turn: pattern react_text, desk astar, tenant acme",
                     "  react_text (lesson 10.1): prompted ReAct: no function declaration sent",
                     "  Thought: I need the passage this rests on, so I search for it.",
                     '  Action: retrieve[{"query": "gratuity fifteen days wages for every completed year of service"}]',
                     "  -> code runs gratuity_estimate(monthly_wage=52000, years=7, months=8); the Observation it "
                     "writes:",
                     "  Final Answer: Gratuity, an estimate: Rs 2,40,000 [2].",
                     "1 calculation, 0 refused or failed tool calls, 0 format errors; stopped by nothing",
                     "figure check: every figure in the model's text is a calculator's"):
            self.assertIn(line, text)
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agent_turn.main(["--offline", "--pattern", "react_text", "--invent"]), 0)
        text = out.getvalue()
        self.assertIn('  cut by the parser, which reads nothing from the first "Observation:" on:\n'
                      "    | Observation: Rs 2,50,000\n", text)
        self.assertIn("figure check: every figure in the model's text is a calculator's", text)
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agent_turn.main(["--offline", "--pattern", "plan_first", "--thinking", "high"]), 0)
        self.assertIn("  the model wrote: Plan: 1. Search for the passage the figure rests on.", out.getvalue())
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(agent_turn.main(["--offline", "--invent"]), 2)
        self.assertIn("--invent is for --offline --pattern react_text", err.getvalue())

    def test_agent_eval_scores_both_beside_the_loop(self):
        spec = importlib.util.spec_from_file_location("agent_eval_for_patterns", KIT / "evals" / "agent_eval.py")
        ae = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ae)
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            self.assertEqual(ae.main(["--offline", "--patterns", "loop,react_text,plan_first",
                                      "--slice", "calc-gratuity-7y6m,trap,refuse"]), 0)
        text = out.getvalue()
        for arm in ("loop", "react_text", "plan_first"):
            self.assertIn(f"== {arm}, thinking default (low), desk astar: 3 rows x 1 run", text)
        self.assertEqual(len(re.findall(r"trap-encash-cap +trap +yes +no ", text)), 3)     # each copies the cap
        self.assertEqual(len(re.findall(r"refuse-gratuity-years +refuse +yes +yes ", text)), 3)
        self.assertEqual(text.count("first runs: correct    3/3 = 100.0%"), 3)


if __name__ == "__main__":
    unittest.main()
