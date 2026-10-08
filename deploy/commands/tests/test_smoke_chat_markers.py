"""Offline checks for make smoke-chat's citation gate (workshop lesson 5.7).

An agent brain numbers its citations 1..k for the turn, so every [n] in its answer must name one of them. The direct
brain passes rag-api's answer through: its [N] is a place in rag-api's packed context, and its citations are only the
sources the model quoted, so a correct direct answer can cite [3] beside one citation. No network: smoke_chat.call is
replaced by a stand-in that answers as the chat service would. Every turn reports its limits (workshop lesson 5.5):
the gate wants them present, not stopped and within the cap, and an agent brain's turn priced above Rs 0; the drill
(make limits-drill) wants each agent brain stopped by the limit it set.
"""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[2] / "smoke" / "smoke_chat.py"
spec = importlib.util.spec_from_file_location("smoke_chat_under_test", SOURCE)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)

LIMITS = {"stopped_by": None, "model_calls": 2, "max_model_calls": 12, "cost_inr": 0.87, "budget_inr": 5.0,
          "deadline_s": 100.0, "tool_timeouts": []}
AGENT_OK = {"answer": "Gratuity is payable after five years of continuous service [1].",
            "tool_calls": ["retrieve"], "refusals": [],
            "citations": [{"n": 1, "chunk_id": "acme:gratuity#3"}, {"n": 2, "chunk_id": "acme:gratuity#4"}],
            "limits": LIMITS}
# rag-api's model cited the third packed chunk and quoted only that one: one citation, marker [3]
DIRECT_OK = {"answer": "Gratuity is payable after five years of continuous service [3].",
             "tool_calls": ["retrieve"], "refusals": [], "citations": [{"chunk_id": "acme:gratuity#3", "page": 3}],
             "limits": dict(LIMITS, model_calls=0, cost_inr=0.37)}      # no model call of its own; rag-api's answer
STOPPED = dict(AGENT_OK, answer="I stopped this turn at one of its limits before I could finish.", citations=[],
               limits=dict(LIMITS, stopped_by="model_calls", model_calls=1, max_model_calls=1))


def run(bodies: dict, expect_stop: str = "") -> tuple[int, list, list]:
    """smoke_chat.main() against a stand-in chat service: (exit code, passed, failed)."""
    def call(path, token, body=None, timeout=180):
        if path == "/health":
            return 200, {"brains": list(smoke.BRAINS), "profile": "gcp", "default_brain": "langchain",
                         "limits": {"max_model_calls": 12, "budget_inr": 5.0, "deadline_s": 100.0}}
        reply = dict(bodies[body["brain"]])
        reply.update(brain=body["brain"], session_id=body["session_id"], latency_ms=1)
        return 200, reply
    smoke.passed.clear()
    smoke.failed.clear()
    with patch.object(smoke, "CHAT_URL", "http://stand-in"), patch.object(smoke, "OUTSIDER", ""), \
            patch.object(smoke, "IMPERSONATE", ""), patch.object(smoke, "call", call), \
            patch.object(smoke, "EXPECT_STOP", expect_stop), \
            contextlib.redirect_stdout(io.StringIO()):
        code = smoke.main()
    return code, list(smoke.passed), list(smoke.failed)


class SmokeChatMarkerTests(unittest.TestCase):
    def bodies(self, **over) -> dict:
        out = {b: AGENT_OK for b in smoke.BRAINS if b != "direct"}
        out["direct"] = DIRECT_OK
        out.update(over)
        return out

    def test_a_direct_answer_citing_rag_apis_packed_context_passes(self):
        code, passed, failed = run(self.bodies())
        self.assertEqual((code, failed), (0, []))
        self.assertEqual(passed, ["health"] + [f"brain {b}" for b in smoke.BRAINS])

    def test_an_agent_marker_past_its_last_citation_fails(self):
        past = dict(AGENT_OK, answer="Five years [3].")
        code, _, failed = run(self.bodies(langgraph=past))
        self.assertEqual((code, failed), (1, ["brain langgraph"]))

    def test_agent_citations_must_be_numbered_from_one(self):
        skipped = dict(AGENT_OK, answer="Five years [2].", citations=[{"n": 2, "chunk_id": "acme:gratuity#4"}])
        unnumbered = dict(AGENT_OK, citations=[{"chunk_id": "acme:gratuity#3"}])
        code, _, failed = run(self.bodies(langchain=skipped, adk=unnumbered))
        self.assertEqual((code, failed), (1, ["brain langchain", "brain adk"]))

    def test_every_brain_must_return_citations(self):
        code, _, failed = run(self.bodies(direct=dict(DIRECT_OK, citations=[]), adk=dict(AGENT_OK, citations=[])))
        self.assertEqual((code, failed), (1, ["brain direct", "brain adk"]))

    def test_every_turn_must_report_its_limits_unstopped_and_priced(self):
        code, _, failed = run(self.bodies(langchain={k: v for k, v in AGENT_OK.items() if k != "limits"},
                                          langgraph=STOPPED, adk=dict(AGENT_OK, limits=dict(LIMITS, cost_inr=0.0))))
        self.assertEqual((code, failed), (1, ["brain langchain", "brain langgraph", "brain adk"]))

    def test_the_drill_wants_every_agent_brain_stopped_by_its_limit(self):
        stopped = {b: STOPPED for b in smoke.BRAINS if b != "direct"}
        code, passed, failed = run(self.bodies(**stopped), expect_stop="model_calls")
        self.assertEqual((code, failed), (0, []))
        self.assertEqual(passed, ["health", "brain direct"] + [f"brain {b} stopped" for b in smoke.BRAINS if b != "direct"])
        code, _, failed = run(self.bodies(), expect_stop="model_calls")      # a limit that never tripped fails the drill
        self.assertEqual((code, failed), (1, [f"brain {b} stopped" for b in smoke.BRAINS if b != "direct"]))


if __name__ == "__main__":
    unittest.main()
