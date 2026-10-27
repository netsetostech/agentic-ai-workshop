"""Offline checks for ADK_PLANNER, ADK's own planner on the chat's ADK brain (workshop lesson 10.2).

    python -m unittest commands/tests/test_adk_planner.py -v          # from deploy/

No network beyond 127.0.0.1, no credential. The first class needs only the standard library: the switch as brains.py
holds it (read once at import, empty by default, plan_react the one value), set on the agent after it is built and
after the hand-off's lines, and only in the ADK brain; the brain still names no thinking level (lessons 5.7 and 6.1
assert it); the final-answer join that drops thought parts; both CI lines and the UNOWNED.md row.

The second runs the kit's own ADK brain on a scripted model and a stand-in rag-api, and needs the chat image's pins
(pip install -r services/chat/requirements.txt), google-adk 2.8.0 among them. It checks what was verified offline on
that pin on 13 October 2026: LlmAgent's pydantic config is neither frozen nor validated on assignment, so the planner
set after the agent is built is the one the flow reads on every model request (the planning instruction is in the
request); a reply with a final-answer tag answers with its final text and none of its plan or reasoning; a plan beside a
tool call comes back marked thought, and the next request carries it as plain text (ADK's own
_remove_thought_from_request, so a written plan is resent on every later call); a reply that is all plan answers with
the labelled fallback, never an empty answer; with the switch unset the brain has no planner and a reply with no
thought part answers byte for byte as before; a thought part never reaches the answer, with or without the switch; an
unknown value logs a warning and sets no planner. Without the pins this class is skipped and says so; with
DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins steps set it, a missing pin is an error instead.
"""
import importlib.util
import json
import logging
import os
import re
import sys
import threading
import unittest
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[2]
ROOT = KIT.parent


def _has(module: str) -> bool:
    """find_spec, but False when a parent package is missing (find_spec raises then: CI's shared interpreter)."""
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


FRAMEWORKS = all(_has(m) for m in ("langchain", "langgraph", "google.adk"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
PLAN = "/*PLANNING*/\n1. search the handbook for the notice period\n2. answer with the figure and its source"
CI_LINE = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_adk_planner.py -v"


def read(*parts: str) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


class TheSwitchAsWritten(unittest.TestCase):
    """What needs no framework: the switch, where it is set, the join, the CI lines and the row."""

    @classmethod
    def setUpClass(cls):
        cls.src = read("services", "chat", "brains.py")
        cls.adk = cls.src.split("\nclass AdkBrain:", 1)[1].split("\nclass DirectBrain:", 1)[0]

    def test_off_unless_set_and_read_once_at_import(self):
        self.assertIn('\nADK_PLANNER = os.environ.get("ADK_PLANNER", "")\n', self.src)
        self.assertEqual(self.src.count('os.environ.get("ADK_PLANNER"'), 1)
        self.assertEqual(re.findall(r'ADK_PLANNER == "(\w+)"', self.src), ["plan_react"])     # the one value

    def test_set_after_the_agent_is_built_in_the_adk_brain_alone(self):
        self.assertEqual(self.src.count("root.planner = PlanReActPlanner()"), 1)
        self.assertEqual(self.src.count("from google.adk.planners import PlanReActPlanner"), 1)
        self.assertIn("root.planner = PlanReActPlanner()", self.adk)
        built, handoff = self.adk.index("root = LlmAgent("), self.adk.index("root.tools.append(peer.tool())")
        planner, runner = self.adk.index("root.planner = PlanReActPlanner()"), self.adk.index("self.runner = Runner(")
        self.assertLess(built, handoff)
        self.assertLess(handoff, planner)        # test_handoff.py holds the hand-off's lines under the constructor
        self.assertLess(planner, runner)
        self.assertNotIn("planner", self.adk[built:handoff])        # not a constructor argument: set afterwards
        self.assertNotIn("thinking", self.adk)          # lessons 5.7 and 6.1: the ADK brain names no thinking level

    def test_the_join_drops_thought_parts_and_never_answers_empty(self):
        self.assertIn('out["answer"] = "".join(p.text or "" for p in ev.content.parts if not p.thought)\n'
                      '                if any(p.thought for p in ev.content.parts):\n'
                      '                    plan = "".join(p.text or "" for p in ev.content.parts).strip()\n'
                      '                    out["answer"] = out["answer"].strip() or NO_FINAL_ANSWER + plan\n', self.adk)
        self.assertNotIn('out["answer"] = "".join(p.text or "" for p in ev.content.parts)\n', self.adk)

    def test_the_ci_lines_and_the_row(self):
        self.assertIn(CI_LINE, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = ROOT / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                                    # the authoring repository's own CI
            self.assertIn(CI_LINE, repo_ci.read_text(encoding="utf-8"))
        f = "commands/tests/test_adk_planner.py"
        row = next((l for l in read("INDEX.md").splitlines() if l.startswith(f"| `{f}` |")), "")   # a page quotes it
        self.assertTrue(f"| `{f}` | **10.2**" in read("UNOWNED.md") or row.split(" | ")[2:3] not in ([], ["-"]), f)


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class ThePlannerInTheBrain(unittest.TestCase):
    """The kit's ADK brain, scripted, with ADK_PLANNER set and unset."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        cls.adk_level = logging.getLogger("google_adk").level
        logging.getLogger("google_adk").setLevel(logging.ERROR)    # ADK's notes on a scripted model's missing usage
        os.environ.setdefault("CHECKPOINT_DSN", "")
        sys.path[:0] = [p for p in (str(KIT), str(KIT / "services/chat")) if p not in sys.path]
        import brains
        import shared.documind_tools as dt
        from google.adk.agents import LlmAgent
        from google.adk.models.base_llm import BaseLlm
        from google.adk.models.llm_response import LlmResponse
        from google.adk.planners import PlanReActPlanner
        from google.genai import types as gt
        cls.brains, cls.dt, cls.gt, cls.R, cls.LlmAgent, cls.PlanReActPlanner = (
            brains, dt, gt, LlmResponse, LlmAgent, PlanReActPlanner)

        class Api(BaseHTTPRequestHandler):
            """rag-api, stood in, for the turn that searches."""

            def log_message(self, *a):
                pass

            def do_POST(self):
                req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                cite = {"chunk_id": f"acme:{req['query']}#0", "source_uri": "gs://b/acme/h.pdf", "page": 4,
                        "quote": "A confirmed employee serves 60 days' notice.", "score": 0.9}
                data = json.dumps({"answer": "rag-api's answer", "answerable": True, "confidence": "high",
                                   "citations": [cite]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        cls.api = ThreadingHTTPServer(("127.0.0.1", 0), Api)
        threading.Thread(target=cls.api.serve_forever, daemon=True).start()
        cls.saved = (dt.RAG_API_URL, dt._id_token)
        dt.RAG_API_URL, dt._id_token = f"http://127.0.0.1:{cls.api.server_address[1]}", lambda aud: "TOKEN"

        class AdkScript(BaseLlm):
            model: str = "script"
            turns: list = []
            sent: list = []

            async def generate_content_async(self, llm_request, stream=False):
                self.sent.append(llm_request.model_copy(deep=True))     # as sent, before anything later changes it
                yield self.turns.pop(0)

        cls.AdkScript = AdkScript

    @classmethod
    def tearDownClass(cls):
        cls.api.shutdown()
        cls.dt.RAG_API_URL, cls.dt._id_token = cls.saved
        logging.getLogger("google_adk").setLevel(cls.adk_level)

    def reply(self, *parts):
        """One scripted model reply: text parts as strings, a tool call as a (name, args) pair."""
        gt = self.gt
        made = [gt.Part(text=p) if isinstance(p, str) else gt.Part(function_call=gt.FunctionCall(name=p[0], args=p[1]))
                for p in parts]
        return self.R(content=self.gt.Content(role="model", parts=made))

    def turn(self, replies, planner="plan_react", label="t"):
        """One turn of the kit's ADK brain, built with ADK_PLANNER=planner, on a model that gives `replies`."""
        with mock.patch.object(self.brains, "ADK_PLANNER", planner):
            brain = self.brains.AdkBrain(None)
        model = self.AdkScript(turns=list(replies), sent=[])
        brain.runner.agent.model = model
        out = brain.answer("What notice does a confirmed employee serve?",
                           config={"configurable": {"thread_id": f"acme:you:{label}"}},
                           context={"tenant_id": "acme", "user_id": "you@example.com", "assertion": ""})
        return brain, model, out

    @staticmethod
    def instruction(request) -> str:
        si = request.config.system_instruction
        return si if isinstance(si, str) else str(si)

    def test_the_config_allows_setting_the_planner_after_the_agent_is_built(self):
        cfg = self.LlmAgent.model_config
        self.assertFalse(cfg.get("frozen", False))
        self.assertFalse(cfg.get("validate_assignment", False))
        with mock.patch.object(self.brains, "ADK_PLANNER", "plan_react"):
            brain = self.brains.AdkBrain(None)
        self.assertIsInstance(brain.runner.agent.planner, self.PlanReActPlanner)
        self.assertIs(brain.runner.app.root_agent.planner, brain.runner.agent.planner)    # the agent the runner runs

    def test_a_final_answer_without_its_plan_or_reasoning(self):
        _, model, out = self.turn([self.reply(PLAN + "\n/*REASONING*/\nno search needed for this one\n"
                                              "/*FINAL_ANSWER*/\nSixty days [1].")], label="final")
        self.assertIn("/*PLANNING*/", self.instruction(model.sent[0]))       # the flow read the planner set afterwards
        self.assertIn("/*FINAL_ANSWER*/", self.instruction(model.sent[0]))
        self.assertEqual(out["answer"], "Sixty days [1].")                  # the final text alone, trimmed

    def test_a_plan_beside_a_call_is_resent_as_plain_text(self):
        brain, model, out = self.turn([
            self.reply(PLAN, ("retrieve", {"query": "notice period"})),
            self.reply("/*REASONING*/\nthe handbook says 60 days\n/*FINAL_ANSWER*/\nSixty days of notice [1]."),
        ], label="call")
        self.assertEqual(out["tool_calls"], ["retrieve"])
        self.assertEqual(out["answer"], "Sixty days of notice [1].")
        self.assertEqual([c["n"] for c in out["citations"]], [1])
        resent = [(c.role, p.thought) for c in model.sent[1].contents for p in (c.parts or [])
                  if p.text and "search the handbook" in p.text]
        self.assertEqual(resent, [("model", None)])           # the plan goes back as plain text, not as thought
        import asyncio
        sess = asyncio.run(brain.svc.get_session(app_name="documind", user_id="you@example.com",
                                                 session_id="acme:you:call"))
        stored = [p.thought for ev in sess.events if ev.content for p in (ev.content.parts or [])
                  if p.text and "search the handbook" in p.text]
        self.assertEqual(stored, [True])                      # and the session keeps it marked as thought

    def test_a_reply_that_is_all_plan_is_labelled_never_empty(self):
        _, _, out = self.turn([self.reply(PLAN)], label="plan-only")
        plan = PLAN.replace("/*PLANNING*/\n", "")                         # ADK strips the tags
        self.assertEqual(out["answer"], self.brains.NO_FINAL_ANSWER + plan)

    def test_unset_no_planner_and_a_plain_reply_as_before(self):
        brain, model, out = self.turn([self.reply("\nSixty days [1].\n")], planner="", label="unset")
        self.assertIsNone(brain.runner.agent.planner)
        self.assertNotIn("/*PLANNING*/", self.instruction(model.sent[0]))
        self.assertEqual(out["answer"], "\nSixty days [1].\n")              # no thought part: byte for byte, as before

    def test_a_thought_part_never_reaches_the_answer(self):
        gt = self.gt
        for planner in ("", "plan_react"):
            with self.subTest(planner=planner):
                thought = self.R(content=gt.Content(role="model", parts=[
                    gt.Part(text="private working the reader never sees", thought=True), gt.Part(text="Sixty days.")]))
                _, _, out = self.turn([thought], planner=planner, label=f"thought-{planner or 'unset'}")
                self.assertEqual(out["answer"], "Sixty days.")

    def test_an_unknown_value_sets_no_planner_and_says_so(self):
        with self.assertLogs("documind.chat.brains", level="WARNING") as logs, \
                mock.patch.object(self.brains, "ADK_PLANNER", "builtin"):
            brain = self.brains.AdkBrain(None)
        self.assertIsNone(brain.runner.agent.planner)
        self.assertIn("ADK_PLANNER='builtin' is not one this kit sets (plan_react)", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
