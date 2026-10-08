"""Offline checks for the limits of one chat turn: model calls, rupees and time (workshop lessons 5.5 and 5.7).

    python -m unittest commands/tests/test_chat_limits.py -v          # from deploy/
    make limits-check                                                 # the same, in ~/graph-venv with the chat pins

The first classes need only the standard library: services/chat/limits.py's Meter, its prices held equal to
rag-api's cost.py, the worst case of a turn held under the UI's and the servers' timeouts, and the chat row's fields
named in agent.py's log line; a cut call that never runs when queued and writes nothing when it runs. The second
runs the kit's own three agent brains against scripted models and a stand-in rag-api, and needs the chat image's
pins (pip install -r services/chat/requirements.txt): a looping model stopped by the call cap, the rupee cap and the
deadline, with the next turn on the thread answering; a slow search abandoned at its budget as data, not a refusal,
and adding no citation when it finishes; a queued call cut before it ran; a hung model call ending in the stop, not
an exception; a forced recursion limit leaving a whole thread; ADK's own cap caught; the checkpoints a turn writes
unchanged; and the chat service answering a stopped turn with HTTP 200. Without the pins it is skipped and says so;
with DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins step sets it, a missing pin is an error instead.
"""
import ast
import asyncio
from concurrent.futures import ThreadPoolExecutor
import contextvars
import importlib.util
import json
import logging
import os
from pathlib import Path
import re
import sys
import threading
import time
import types
import unittest
from unittest.mock import patch
import uuid
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KIT = Path(__file__).resolve().parents[2]
for p in (str(KIT / "services/chat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import limits                                  # noqa: E402 - stdlib and shared/prices.py only, at import
from shared import desk_recall, prices         # noqa: E402

FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "google.adk", "fastapi"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
AGENTS = ("langchain", "langgraph", "adk")
ROW_FIELDS = ("model", "model_calls", "tokens_in", "tokens_out", "cached_tokens", "cost_usd", "rag_cost_usd",
              "stopped_by", "tool_timeouts", "max_model_calls", "budget_inr")


def fake_tools(**timeouts):
    """The two names limits.py reads from tools.py, for a test with no LangChain."""
    return patch.dict(sys.modules, {"tools": types.SimpleNamespace(
        TIMEOUTS=timeouts or {"retrieve": 95}, REQUEST=contextvars.ContextVar("documind_request", default={}))})


class MeterArithmetic(unittest.TestCase):
    """The Meter alone: what it allows, what it charges, what it gives a model call and a tool call."""

    def test_the_call_cap_counts_the_calls_it_allows(self):
        m = limits.Meter(max_model_calls=3)
        self.assertEqual([m.allow_model_call() for _ in range(5)], [True, True, True, False, False])
        self.assertEqual((m.model_calls, m.stopped_by), (3, "model_calls"))

    def test_the_first_call_is_always_allowed(self):
        m = limits.Meter(max_model_calls=0, budget_inr=0, deadline_s=0)
        self.assertTrue(m.allow_model_call())
        self.assertFalse(m.allow_model_call())
        self.assertEqual(m.model_calls, 1)

    def test_the_rupee_cap_stops_the_call_after_the_one_that_crossed_it(self):
        m = limits.Meter(budget_inr=2, model="gemini-3.6-flash")
        self.assertTrue(m.allow_model_call())
        m.charge_model(200_000, 50)                  # one long call: (200,000 x 1.50 + 50 x 7.50) / 1M x 85
        self.assertEqual(round(m.spent_inr(), 2), 25.53)
        self.assertFalse(m.allow_model_call())
        self.assertEqual((m.stopped_by, m.model_calls), ("turn_budget", 1))

    def test_twelve_flash_calls_of_8000_tokens_cost_more_than_the_default_cap(self):
        m = limits.Meter(model="gemini-3.6-flash", budget_inr=1e9)
        for _ in range(12):
            m.charge_model(8000, 0)
        self.assertEqual(round(m.spent_inr(), 2), 12.24)
        self.assertGreater(m.spent_inr(), limits.TURN_BUDGET_INR)

    def test_the_deadline_refuses_a_call_with_too_little_time_left(self):
        m = limits.Meter(deadline_s=limits.MIN_MODEL_S + 60)
        self.assertTrue(m.allow_model_call())
        m.started -= 61                              # 61 s later: under MIN_MODEL_S left
        self.assertFalse(m.allow_model_call())
        self.assertEqual(m.stopped_by, "turn_deadline")

    def test_a_stop_is_sticky_and_the_first_reason_wins(self):
        m = limits.Meter()
        m.allow_model_call()
        m.stop("turn_deadline")
        m.stop("model_calls")
        self.assertFalse(m.allow_model_call())
        self.assertEqual(m.stopped_by, "turn_deadline")

    def test_cached_tokens_are_billed_at_a_tenth(self):
        m = limits.Meter(model="gemini-3.6-flash")
        m.charge_model(10_000, 1_000, cached_tokens=8_000)
        self.assertAlmostEqual(m.cost_usd, (2_000 * 1.50 + 8_000 * 0.15 + 1_000 * 7.50) / 1e6)
        self.assertEqual((m.tokens_in, m.tokens_out, m.cached_tokens), (10_000, 1_000, 8_000))

    def test_rag_apis_own_cost_wins_over_list_price(self):
        m = limits.Meter()
        m.charge_rag({"model": "gemini-3.6-flash", "tokens_in": 1000, "tokens_out": 100, "cost_usd": 0.0})   # a cache hit
        m.charge_rag({"model": "documind-general", "tokens_in": 1000, "tokens_out": 100, "cost_usd": 0.004})  # the gateway's
        m.charge_rag({"model": "gemini-3.1-flash-lite", "tokens_in": 1000, "tokens_out": 100, "cost_usd": None})
        m.charge_rag(None)                                                                                     # a failed search
        self.assertAlmostEqual(m.rag_cost_usd, 0.004 + (1000 * 0.25 + 100 * 1.50) / 1e6)
        self.assertEqual(m.cost_usd, 0.0)

    def test_each_model_attempt_fits_in_the_time_left(self):
        m = limits.Meter(deadline_s=100)
        self.assertEqual(m.model_timeout_s(), limits.MODEL_TIMEOUT_S)          # 30: the attempts take 60 of 100 s
        m.started -= 60                                                          # 40 s left: 20 s an attempt
        self.assertAlmostEqual(m.model_timeout_s(), 40 / limits.MODEL_ATTEMPTS, delta=0.05)
        m.started -= 39.5
        self.assertEqual(m.model_timeout_s(), limits.TOOL_FLOOR_S)              # never a zero, which means none

    def test_a_tool_gets_its_budget_or_the_time_left_never_under_a_second(self):
        with fake_tools(retrieve=95, calculate_processing_cost=10):
            m = limits.Meter(deadline_s=100)
            self.assertEqual(m.tool_budget_s("retrieve"), 95)
            self.assertEqual(m.tool_budget_s("calculate_processing_cost"), 10)
            self.assertEqual(m.tool_budget_s("summon_rain"), 30)                 # an undeclared name: the old default
            m.started -= 60
            self.assertAlmostEqual(m.tool_budget_s("retrieve"), 40, delta=0.05)
            m.started -= 45
            self.assertEqual(m.tool_budget_s("retrieve"), limits.TOOL_FLOOR_S)

    def test_the_summary_and_the_row(self):
        m = limits.Meter(model="gemini-3.6-flash")
        m.allow_model_call()
        m.charge_model(1000, 100)
        m.tool_timed_out("retrieve")
        self.assertEqual(sorted(m.row()), sorted(ROW_FIELDS))
        s = m.summary()
        self.assertEqual((s["stopped_by"], s["model_calls"], s["tool_timeouts"]), (None, 1, ["retrieve"]))
        self.assertEqual(s["cost_inr"], round((1000 * 1.50 + 100 * 7.50) / 1e6 * 85, 4))
        json.dumps(m.row()), json.dumps(s)                                       # both go out as JSON

    def test_a_timeout_is_recognised_from_every_client(self):
        class ReadTimeout(Exception):                                            # httpx's, by name
            pass
        self.assertTrue(limits.is_timeout(TimeoutError()))
        self.assertTrue(limits.is_timeout(ReadTimeout()))
        self.assertFalse(limits.is_timeout(ValueError("bad")))
        self.assertFalse(limits.is_timeout(RuntimeError("could not mint an ID token")))


class TimedCalls(unittest.TestCase):
    """What a cut tool call may still do: a queued one never runs, a running one writes nothing into the turn."""

    def test_a_calls_fate_is_decided_once(self):
        t = limits._Ticket()
        self.assertTrue(t.commit())
        self.assertFalse(t.abandon())                       # delivered first: the caller hands the model its result
        t = limits._Ticket()
        self.assertTrue(t.abandon())
        self.assertFalse(t.commit())                        # abandoned first: the tool writes nothing
        self.assertTrue(limits.may_commit())                # outside a timed wrapper a call is always delivered

    def test_a_queued_call_is_cancelled_and_a_running_one_writes_nothing(self):
        """One pool thread, three calls of 1 s cut at 0.2 s: the first runs on, past all three cuts, but may
        not commit; the queued two never start."""
        ran, committed = [], []

        def tool(n):
            ran.append(n)
            time.sleep(1.0)
            committed.append((n, limits.may_commit()))
            return {"citations": [n]}

        async def turn():
            return [await limits.timed_async("retrieve", tool, n=n) for n in range(3)]

        with fake_tools(retrieve=0), patch.object(limits, "TOOL_FLOOR_S", 0.2), \
                patch.object(limits, "_log_time", lambda *a: None), \
                patch.object(limits, "TOOL_POOL", ThreadPoolExecutor(max_workers=1)) as pool:
            out = asyncio.run(turn())
            pool.shutdown(wait=True)
        self.assertEqual([o["timed_out"] for o in out], [True] * 3)
        self.assertEqual((ran, committed), ([0], [(0, False)]))

    def test_no_turn_context_keeps_no_meter(self):
        """Outside a turn, ADK's callbacks get a fresh Meter each time: never one stored in the ContextVar's default,
        which every later caller in the process would share."""
        with fake_tools():
            self.assertIsNone(limits._request())
            first, second = limits.meter_of(limits._request()), limits.meter_of(limits._request())
            self.assertIsNot(first, second)
            self.assertEqual(sys.modules["tools"].REQUEST.get(), {})


class KitAgrees(unittest.TestCase):
    """The limits against the rest of the kit: rag-api's prices, the timeouts around a turn, the row agent.py logs."""

    def test_the_chat_prices_are_rag_apis(self):
        tree = ast.parse((KIT / "services/rag-api/cost.py").read_text(encoding="utf-8"))
        fallback = next(n.value for n in tree.body if isinstance(n, ast.Assign) and n.targets[0].id == "FALLBACK")
        self.assertEqual(ast.literal_eval(fallback), prices.PRICES)
        self.assertEqual(len(prices.PRICES), 8)
        self.assertEqual(prices.USD_INR, 85)
        self.assertIn('USD_INR = float(os.environ.get("USD_INR_RATE", "85"))',
                      (KIT / "services/rag-api/cost.py").read_text(encoding="utf-8"))

    def test_the_local_profile_costs_nothing(self):
        with patch.object(prices, "PROFILE", "local"):
            self.assertEqual(prices.usd("gemini-3.6-flash", 10_000, 1_000), 0.0)

    def test_a_turn_ends_before_anything_around_it_gives_up(self):
        """The deadline, one retry's backoff and the last tool's floor: about 103 s, under 120 and 300."""
        worst = limits.TURN_DEADLINE_S + limits.RETRY_BACKOFF_S * (limits.MODEL_ATTEMPTS - 1) + limits.TOOL_FLOOR_S
        self.assertEqual(worst, 103)
        ui = (KIT / "services/frontend/chat.py").read_text(encoding="utf-8")
        ui_timeout = int(re.search(r'requests\.post\(f"\{CHAT_URL\}/v1/chat",.*?timeout=(\d+)\)', ui, re.S).group(1))
        worker = int(re.search(r'"-t", "(\d+)"', (KIT / "services/chat/Dockerfile").read_text(encoding="utf-8")).group(1))
        deploy = (KIT / "commands/lesson-12.8.sh").read_text(encoding="utf-8")
        run = int(re.search(r"gcloud run deploy documind-chat.*?--timeout=(\d+)", deploy, re.S).group(1))
        self.assertLess(worst, ui_timeout)
        self.assertLess(worst, worker)
        self.assertLess(ui_timeout, run)
        # the chat door's model check (shared/desk_recall.py) runs before chat() starts the turn's clock: the tenants
        # read, once a minute, and an "on" tenant's check fit with the turn under the same two timeouts
        door = desk_recall.READ_TIMEOUT_S + desk_recall.CHECK_TIMEOUT_S
        self.assertEqual(worst + door, 108)
        self.assertLess(worst + door, ui_timeout)
        self.assertLess(worst + door, worker)
        self.assertEqual((ui_timeout, worker, run), (120, 120, 300))
        # retrieve's budget on the lane is RAG_TIMEOUT_S + 5, under the deadline, so one slow search cannot use it up
        lane_rag = float(re.search(r"RAG_TIMEOUT_S=(\d+)", deploy).group(1))
        self.assertIn('TIMEOUTS = {"retrieve": documind_tools.RAG_TIMEOUT_S + 5, "calculate_processing_cost": 10}',
                      (KIT / "services/chat/tools.py").read_text(encoding="utf-8"))
        self.assertLess(lane_rag + 5, limits.TURN_DEADLINE_S)

    def test_the_defaults(self):
        self.assertEqual((limits.MAX_MODEL_CALLS, limits.TURN_BUDGET_INR, limits.TURN_DEADLINE_S, limits.MODEL_TIMEOUT_S,
                          limits.MODEL_ATTEMPTS, limits.MIN_MODEL_S), (12, 5, 100, 30, 2, 5))
        self.assertEqual(limits.recursion_limit(), 4 * 12 + 10)

    def test_the_chat_row_names_every_limits_field(self):
        """Each field in the row literal, read the way the pages read it: a spread would hide them."""
        src = (KIT / "services/chat/agent.py").read_text(encoding="utf-8")
        row = re.search(r'logger\.info\(json\.dumps\(\{"event": "chat",(.*?)\}\)\)', src, re.S).group(1)
        self.assertNotIn("**", row)
        for name in ROW_FIELDS:
            self.assertIn(f'"{name}": used["{name}"]', row, name)

    def test_the_mcp_tool_keeps_its_contract(self):
        src = (KIT / "services/mcp/server.py").read_text(encoding="utf-8")
        self.assertIn('    out.pop("usage", None)', src)
        self.assertLess(src.index('    out.pop("usage", None)'), src.index("    return out                       # the citations"))


# ----------------------------------------------------------------------------- the library half
@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class BrainsStop(unittest.TestCase):
    """The kit's langchain, langgraph and adk brains under one Meter each turn, with scripted models."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.CRITICAL)
        os.environ.setdefault("CHECKPOINT_DSN", "")
        import shared.documind_tools as dt
        import brains
        import tools
        cls.dt, cls.brains, cls.tools = dt, brains, tools
        cls.state = state = {"sleep": 0.0}

        class Api(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                time.sleep(state["sleep"])
                body = {"answer": "rag-api's own answer", "answerable": True, "confidence": "high",
                        "citations": [{"chunk_id": f"acme:{req['query']}#0", "source_uri": "gs://b/acme/x.pdf",
                                       "page": 1, "quote": "q", "score": 0.9}],
                        "model": "gemini-3.6-flash", "tokens_in": 1000, "tokens_out": 100, "cached_tokens": 0,
                        "cost_usd": None}
                data = json.dumps(body).encode()
                try:
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except OSError:                       # the caller abandoned it
                    pass

        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Api)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.saved = (dt.RAG_API_URL, dt._id_token)
        dt.RAG_API_URL, dt._id_token = f"http://127.0.0.1:{cls.srv.server_address[1]}", lambda aud: "TOKEN"

        import httpx
        from google.adk.models.base_llm import BaseLlm
        from google.adk.models.llm_response import LlmResponse
        from google.genai import types as gt
        from langchain_core.language_models.chat_models import BaseChatModel
        from langchain_core.messages import AIMessage
        from langchain_core.outputs import ChatGeneration, ChatResult
        from pydantic import Field

        class Model(BaseChatModel):
            """Each call takes the next step: "tool" asks for a search, "text" answers, "hang" waits past its
            timeout as an unanswered request does. With no steps left: "tool" if it loops, else "text"."""
            steps: list = Field(default_factory=list)
            loop: bool = False
            seen: list = Field(default_factory=list)
            tokens_in: int = 8000                     # about Rs 1.05 a call at flash's list price

            @property
            def _llm_type(self):
                return "script"

            def bind_tools(self, tools, **kw):
                return self.bind(**kw)

            def _generate(self, messages, stop=None, run_manager=None, **kw):
                self.seen.append(kw)
                step = self.steps.pop(0) if self.steps else ("tool" if self.loop else "text")
                if step == "hang":
                    time.sleep(min(kw.get("timeout") or 1, 1))
                    raise httpx.ReadTimeout("the model did not answer")
                if step == "slow":                    # an answer that takes 1.5 s
                    time.sleep(1.5)
                    step = "text"
                calls = [{"name": "retrieve", "args": {"query": "gratuity"}, "id": uuid.uuid4().hex}] if step == "tool" else []
                msg = AIMessage("" if calls else "done [1]", tool_calls=calls, usage_metadata={
                    "input_tokens": self.tokens_in, "output_tokens": 50, "total_tokens": self.tokens_in + 50})
                return ChatResult(generations=[ChatGeneration(message=msg)])

        class AdkModel(BaseLlm):
            model: str = "script"
            steps: list = Field(default_factory=list)
            loop: bool = False
            seen: list = Field(default_factory=list)

            async def generate_content_async(self, llm_request, stream=False):
                cfg = llm_request.config
                self.seen.append(cfg.http_options.timeout if cfg and cfg.http_options else None)
                step = self.steps.pop(0) if self.steps else ("tool" if self.loop else "text")
                if step == "hang":
                    raise httpx.ReadTimeout("the model did not answer")
                if step == "slow":
                    await asyncio.sleep(1.5)
                    step = "text"
                part = (gt.Part(function_call=gt.FunctionCall(name="retrieve", args={"query": "gratuity"}))
                        if step == "tool" else gt.Part(text="done [1]"))
                yield LlmResponse(content=gt.Content(role="model", parts=[part]),
                                  usage_metadata=gt.GenerateContentResponseUsageMetadata(
                                      prompt_token_count=8000, candidates_token_count=50))

        cls.Model, cls.AdkModel = Model, AdkModel

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.dt.RAG_API_URL, cls.dt._id_token = cls.saved
        logging.disable(logging.NOTSET)

    def setUp(self):
        self.state["sleep"] = 0.0

    def brain(self, name, **model):
        """One brain of the kit's, with a scripted model of its framework's kind."""
        from langgraph.checkpoint.memory import InMemorySaver
        if name == "adk":
            b = self.brains.AdkBrain(None)
            b.runner.agent.model = m = self.AdkModel(**model)
            return b, m
        m = self.Model(**model)
        return self.brains.build(name, InMemorySaver(), llm=m), m

    def turn(self, b, thread, meter=None):
        cfg = {"configurable": {"thread_id": f"acme:you:{thread}"}}
        meter = meter or limits.Meter(model="gemini-3.6-flash")
        out = b.answer("How long until gratuity is payable?", config=cfg,
                       context={"tenant_id": "acme", "user_id": "you", "assertion": "", "brain": b.name, "meter": meter})
        return out, meter

    def then_answers(self, b, m, thread):
        """The next turn on the same thread, with a model that answers: it is not stopped."""
        m.steps[:], m.loop = ["tool", "text"], False
        out, meter = self.turn(b, thread)
        self.assertIsNone(meter.stopped_by, b.name)
        self.assertEqual((out["answer"], out["tool_calls"]), ("done [1]", ["retrieve"]), b.name)

    def test_a_looping_model_stops_at_the_call_cap_and_the_next_turn_answers(self):
        for name in AGENTS:
            b, m = self.brain(name, loop=True)
            out, meter = self.turn(b, "cap-" + name, limits.Meter(max_model_calls=3, model="gemini-3.6-flash"))
            self.assertEqual((meter.stopped_by, meter.model_calls), ("model_calls", 3), name)
            self.assertEqual((out["answer"], out["tool_calls"], out["refusals"]),
                             (limits.STOP_ANSWER, ["retrieve"] * 3, []), name)
            self.then_answers(b, m, "cap-" + name)

    def test_a_looping_model_stops_at_the_rupee_cap(self):
        """8,000 tokens a call is about Rs 1.05, and each search Rs 0.19: a Rs 2 cap allows two calls."""
        for name in AGENTS:
            b, m = self.brain(name, loop=True)
            out, meter = self.turn(b, "budget-" + name, limits.Meter(budget_inr=2, model="gemini-3.6-flash"))
            self.assertEqual((meter.stopped_by, meter.model_calls), ("turn_budget", 2), name)
            self.assertEqual((meter.tokens_in, meter.tokens_out), (16_000, 100), name)
            self.assertAlmostEqual(meter.cost_usd, 2 * (8000 * 1.50 + 50 * 7.50) / 1e6, msg=name)
            self.assertAlmostEqual(meter.rag_cost_usd, 2 * (1000 * 1.50 + 100 * 7.50) / 1e6, msg=name)
            self.assertEqual(out["answer"], limits.STOP_ANSWER, name)
            self.then_answers(b, m, "budget-" + name)

    def test_a_looping_model_stops_at_the_deadline(self):
        for name in AGENTS:
            b, m = self.brain(name, loop=True)
            self.state["sleep"] = 0.2                                   # each search takes 0.2 s
            with patch.object(limits, "MIN_MODEL_S", 0.5):
                t = time.monotonic()
                out, meter = self.turn(b, "deadline-" + name, limits.Meter(deadline_s=1.2, model="gemini-3.6-flash"))
            self.assertEqual(meter.stopped_by, "turn_deadline", name)
            self.assertLess(time.monotonic() - t, 1.2, name)
            self.assertEqual(out["answer"], limits.STOP_ANSWER, name)
            self.state["sleep"] = 0.0
            self.then_answers(b, m, "deadline-" + name)

    def test_a_slow_search_is_abandoned_at_its_budget_as_data(self):
        """A 3 s rag-api against a 1 s budget: the turn goes on at 1 s, the model reads a payload error, and the
        call is in tool_timeouts, not in refusals."""
        self.state["sleep"] = 3.0
        with patch.dict(self.tools.TIMEOUTS, {"retrieve": 1}):
            for name in AGENTS:
                b, m = self.brain(name, steps=["tool", "text"])
                t = time.monotonic()
                out, meter = self.turn(b, "slow-" + name)
                took = time.monotonic() - t
                self.assertLess(took, 1 + 0.3, name)                    # the stand-in is still asleep
                self.assertEqual((out["tool_calls"], out["refusals"], out["citations"]), (["retrieve"], [], []), name)
                self.assertEqual((meter.tool_timeouts, meter.stopped_by), (["retrieve"], None), name)
                self.assertEqual(out["answer"], "done [1]", name)

    def test_an_abandoned_search_adds_no_citation(self):
        """The cut search answers at 1.6 s, while the model's answer takes until 2.5 s: its thread finishes inside the
        turn, and still writes nothing into it: no citation numbered, no cost on the turn's Meter."""
        self.state["sleep"] = 1.6
        with patch.dict(self.tools.TIMEOUTS, {"retrieve": 1}):
            for name in AGENTS:
                b, m = self.brain(name, steps=["tool", "slow"])
                out, meter = self.turn(b, "late-" + name)
                self.assertEqual((meter.tool_timeouts, out["citations"]), (["retrieve"], []), name)
                self.assertEqual(meter.rag_cost_usd, 0, name)         # on rag-api's row only

    def test_a_queued_tool_call_is_cancelled_not_run(self):
        """One pool thread, three calls of 1 s cut at 0.2 s: only the first ever runs."""
        from langchain_core.messages import ToolMessage
        ran = []

        def handler(request):
            ran.append(request.tool_call["id"])
            time.sleep(1.0)
            return ToolMessage(content="{}", tool_call_id=request.tool_call["id"])

        ctx = {"meter": limits.Meter()}
        with patch.dict(self.tools.TIMEOUTS, {"retrieve": 0}), patch.object(limits, "TOOL_FLOOR_S", 0.2), \
                patch.object(limits, "TOOL_POOL", ThreadPoolExecutor(max_workers=1)) as pool:
            for i in range(3):
                req = types.SimpleNamespace(tool_call={"name": "retrieve", "id": f"c{i}"},
                                            runtime=types.SimpleNamespace(context=ctx))
                self.assertTrue(json.loads(limits.timed_tool_call(req, handler).content)["timed_out"])
            pool.shutdown(wait=True)
        self.assertEqual((ran, ctx["meter"].tool_timeouts), (["c0"], ["retrieve"] * 3))

    def test_the_model_reads_the_timeout_as_a_payload_error(self):
        self.state["sleep"] = 3.0
        with patch.dict(self.tools.TIMEOUTS, {"retrieve": 0.5}):          # under the floor: cut at 1 s
            b, m = self.brain("langchain", steps=["tool", "text"])
            self.turn(b, "read-timeout")
            msgs = b.agent.get_state({"configurable": {"thread_id": "acme:you:read-timeout"}}).values["messages"]
            res = [x for x in msgs if type(x).__name__ == "ToolMessage"][0]
            self.assertEqual(res.status, "success")
            body = json.loads(res.content)
            self.assertTrue(body["timed_out"])
            self.assertEqual(body["error"], "retrieve did not answer within 1s and was abandoned")

            b, m = self.brain("adk", steps=["tool", "text"])
            self.turn(b, "read-timeout-adk")
            sess = self.brains.asyncio.run(b.svc.get_session(app_name="documind", user_id="you",
                                                             session_id="acme:you:read-timeout-adk"))
            got = [p.function_response.response for e in sess.events for p in (e.content.parts if e.content else [])
                   if p.function_response]
            self.assertTrue(got[0]["timed_out"])
            self.assertNotIn("status", got[0])                           # not an error result: no refusal

    def test_a_hung_model_call_ends_in_the_stop_not_an_exception(self):
        for name in AGENTS:
            b, m = self.brain(name, steps=["hang"])
            out, meter = self.turn(b, "hung-" + name)
            self.assertEqual((out["answer"], meter.stopped_by), (limits.STOP_ANSWER, "turn_deadline"), name)
            sent = m.seen[0]
            if name == "adk":
                self.assertEqual(sent, int(limits.MODEL_TIMEOUT_S * 1000), name)    # milliseconds, on the request
            else:
                self.assertEqual((sent["timeout"], sent["max_retries"]), (limits.MODEL_TIMEOUT_S, limits.MODEL_ATTEMPTS))
            self.then_answers(b, m, "hung-" + name)

    def test_other_model_errors_still_fail_the_turn(self):
        for name in ("langchain", "langgraph"):
            b, m = self.brain(name)
            with patch.object(type(m), "_generate", side_effect=RuntimeError("quota")):
                with self.assertRaises(RuntimeError, msg=name):
                    self.turn(b, "err-" + name)

    def test_a_forced_recursion_limit_leaves_a_whole_thread(self):
        """The framework's backstop, tripped before the Meter: the open call is answered, the turn ends with the stop,
        and the next turn answers on the same thread."""
        for name in ("langchain", "langgraph"):
            b, m = self.brain(name, loop=True)
            with patch.object(limits, "recursion_limit", return_value=3):
                out, meter = self.turn(b, "recursion-" + name, limits.Meter(max_model_calls=50))
            self.assertEqual((out["answer"], meter.stopped_by), (limits.STOP_ANSWER, "recursion_limit"), name)
            graph = b.agent if name == "langchain" else b.graph
            msgs = graph.get_state({"configurable": {"thread_id": f"acme:you:recursion-{name}"}}).values["messages"]
            asked = {c["id"] for x in msgs for c in (getattr(x, "tool_calls", None) or [])}
            answered = {x.tool_call_id for x in msgs if type(x).__name__ == "ToolMessage"}
            self.assertEqual(asked, answered, name)
            self.then_answers(b, m, "recursion-" + name)

    def test_adks_own_cap_is_caught(self):
        from google.adk.agents.run_config import RunConfig
        b, m = self.brain("adk", loop=True)
        b.run_config = RunConfig(max_llm_calls=2)
        out, meter = self.turn(b, "adk-cap", limits.Meter(max_model_calls=50))
        self.assertEqual((out["answer"], meter.stopped_by), (limits.STOP_ANSWER, "model_calls"), "adk")
        self.assertEqual((out["tool_calls"], out["refusals"]), (["retrieve", "retrieve"], []))     # kept, not dropped
        self.then_answers(b, m, "adk-cap")

    def test_a_normal_turn_is_charged_and_not_stopped(self):
        for name in AGENTS:
            b, m = self.brain(name, steps=["tool", "text"])
            out, meter = self.turn(b, "normal-" + name)
            self.assertEqual((meter.stopped_by, meter.model_calls, meter.tool_timeouts), (None, 2, []), name)
            self.assertAlmostEqual(meter.cost_usd, 2 * (8000 * 1.50 + 50 * 7.50) / 1e6, msg=name)
            self.assertAlmostEqual(meter.rag_cost_usd, (1000 * 1.50 + 100 * 7.50) / 1e6, msg=name)
            self.assertGreater(meter.summary()["cost_inr"], 0, name)

    def test_the_adk_declarations_are_unchanged_by_the_timer(self):
        from google.adk.tools import FunctionTool
        for f in self.tools.for_adk():
            plain = FunctionTool(f)._get_declaration().model_dump(mode="json", exclude_none=True)
            timed = FunctionTool(limits.timed_adk(f))._get_declaration().model_dump(mode="json", exclude_none=True)
            self.assertEqual(plain, timed, f.__name__)

    def test_a_turn_writes_the_same_checkpoints(self):
        """wrap_model_call adds no graph node: +3 checkpoints a turn, +5 with a tool call (workshop lesson 6.6)."""
        from langgraph.checkpoint.memory import InMemorySaver
        saver = InMemorySaver()
        m = self.Model(steps=["text", "tool", "text"])
        b = self.brains.build("langchain", saver, llm=m)
        cfg = {"configurable": {"thread_id": "acme:you:checkpoints"}}
        counts = []
        for _ in range(2):
            self.turn(b, "checkpoints")
            counts.append(len(list(saver.list(cfg))))
        self.assertEqual(counts, [3, 8])

    def test_the_chat_service_answers_a_stopped_turn_with_200(self):
        """agent.chat() with a cheap model that never stops asking: HTTP 200, the stop sentence, the row's fields."""
        from fastapi.testclient import TestClient
        with patch.dict(os.environ, {"CHECKPOINT_DSN": "memory"}):
            sys.modules.pop("agent", None)
            import agent
        import desk
        agent.app.dependency_overrides[agent.caller] = lambda: {"email": "you@acme.example", "assertion": None}
        rows = []
        no_check = desk.desk_recall.OnTenants(frozenset, desk.log, "test")     # no tenant's desk_gate is on here
        with patch.object(agent, "tenant_for", return_value="acme"), patch.object(desk, "CHECKED", no_check), \
                patch.object(desk, "SHADOWING", desk.desk_recall.OnTenants(frozenset, desk.log, "test")), \
                patch.object(agent.logger, "info", side_effect=lambda line: rows.append(json.loads(line))), \
                TestClient(agent.app) as client:
            client.app.state.brains["langchain"] = self.brains.build(
                "langchain", client.app.state.checkpointer, llm=self.Model(loop=True, tokens_in=100))
            health = client.get("/health").json()
            r = client.post("/v1/chat", json={"question": "gratuity?", "session_id": "s1", "brain": "langchain"})
        self.assertEqual(health["limits"]["max_model_calls"], limits.MAX_MODEL_CALLS)
        self.assertEqual(health["limits"]["tool_budgets_s"]["retrieve"], self.dt.RAG_TIMEOUT_S + 5)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual((body["answer"], body["limits"]["stopped_by"]), (limits.STOP_ANSWER, "model_calls"))
        self.assertEqual(body["limits"]["model_calls"], limits.MAX_MODEL_CALLS)
        row = rows[-1]
        self.assertEqual(row["event"], "chat")
        self.assertTrue(set(ROW_FIELDS) <= set(row), sorted(set(ROW_FIELDS) - set(row)))
        self.assertEqual((row["stopped_by"], row["model_calls"], row["model"]),
                         ("model_calls", limits.MAX_MODEL_CALLS, "gemini-3.6-flash"))
        self.assertGreater(row["cost_usd"], 0)
        self.assertGreater(row["rag_cost_usd"], 0)


if __name__ == "__main__":
    unittest.main()
