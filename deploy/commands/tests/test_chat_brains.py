"""Offline checks for the chat service's agent brains (workshop lessons 5.1, 5.4, 5.5 and 5.7).

Each turn reports its own tool calls, refusals and numbered citations; the three agent brains bind one tool list,
and no declaration a model reads names the tenant, the assertion or the brain; one error contract holds in all three
(an unknown or blocked name, a bad, wrong-typed or missing argument and an unknown tier are error results and count
as refusals, a failed search is data, anything else fails the turn); the UI draws an agent's citations and escapes
its text.

    python -m unittest commands/tests/test_chat_brains.py -v          # from deploy/

The first class needs only the standard library: it runs _summary() out of brains.py, and the UI's _as_source() and
citations.py's renderer, on stand-ins. The second runs the kit's own brains against scripted models and a stand-in
rag-api, and needs the chat image's pins (pip install -r services/chat/requirements.txt). Without them it is skipped
and says so; with DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins step sets it, a missing pin is an error instead.
"""
import ast
import html
import importlib.util
import inspect
import json
import logging
import os
from pathlib import Path
import sys
import threading
import types
import unittest
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KIT = Path(__file__).resolve().parents[2]
BRAINS_SRC = (KIT / "services/chat/brains.py").read_text(encoding="utf-8")
UI_SRC = (KIT / "services/frontend/chat.py").read_text(encoding="utf-8")
CITES_SRC = (KIT / "services/frontend/citations.py").read_text(encoding="utf-8")
FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "google.adk"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"
AGENTS = ("langchain", "langgraph", "adk")


def defs(src: str, *names: str) -> str:
    """The source of the named top-level functions and assignments, to exec without importing the module."""
    nodes = [n for n in ast.parse(src).body
             if (isinstance(n, ast.FunctionDef) and n.name in names)
             or (isinstance(n, ast.Assign) and any(getattr(t, "id", "") in names for t in n.targets))]
    assert len(nodes) == len(names), (names, [getattr(n, "name", None) for n in nodes])
    return "\n\n".join(ast.get_source_segment(src, n) for n in nodes)


class ToolMessage:                          # all _summary() asks of a tool message: name, status, id
    def __init__(self, name, status="success", id=None):
        self.name, self.status, self.id, self.content = name, status, id, ""


class Msg:
    def __init__(self, content="", tool_calls=None, id=None):
        self.content, self.tool_calls, self.id = content, tool_calls or [], id


def summary_fn():
    ns = {"ToolMessage": ToolMessage}
    exec(defs(BRAINS_SRC, "_summary"), ns)
    return ns["_summary"]


class SummaryIsPerTurn(unittest.TestCase):
    """A checkpointed thread hands back the whole conversation; the four keys describe this turn only."""

    def thread(self):
        out = []
        for t in range(3):
            out += [Msg(f"question {t}", id=f"turn{t}"),
                    Msg(tool_calls=[{"name": "retrieve", "args": {}, "id": f"c{t}"}]),
                    ToolMessage("retrieve", "error" if t == 0 else "success"),
                    Msg(f"answer {t} [1]")]
        return out

    def test_each_turn_counts_its_own_calls(self):
        s = summary_fn()
        for t in range(3):
            got = s(self.thread()[: 4 * (t + 1)], f"turn{t}")
            self.assertEqual(got["tool_calls"], ["retrieve"])
            self.assertEqual(got["refusals"], ["retrieve"] if t == 0 else [])
            self.assertEqual(got["answer"], f"answer {t} [1]")
            self.assertEqual(sorted(got), ["answer", "citations", "refusals", "tool_calls"])

    def test_citations_are_ordered_by_the_number_the_answer_cites(self):
        got = summary_fn()(self.thread(), "turn2", [{"n": 2, "chunk_id": "b"}, {"n": 1, "chunk_id": "a"}])
        self.assertEqual([c["n"] for c in got["citations"]], [1, 2])

    def test_a_turn_that_is_not_in_the_thread_is_an_error_not_the_whole_thread(self):
        with self.assertRaises(ValueError):
            summary_fn()(self.thread(), "turn9")

    def test_the_ui_draws_an_agent_answer_with_pills_and_escapes_it(self):
        """_as_source() maps the chat service's citations to citations.py's shape, and the answer is escaped
        before render_with_citations(), which draws with unsafe_allow_html."""
        calls = [n for n in ast.walk(ast.parse(UI_SRC)) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", "") == "render_with_citations"]
        self.assertIn("render_with_citations(html.escape(answer, quote=False), cited)",
                      [ast.get_source_segment(UI_SRC, c) for c in calls])
        drawn = []

        class Expander:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        st = types.SimpleNamespace(markdown=lambda text, **kw: drawn.append((text, kw)), expander=lambda *a: Expander(),
                                   caption=lambda *a, **k: None, image=lambda *a, **k: None, video=lambda *a, **k: None,
                                   link_button=lambda *a, **k: None)
        ns = {"re": __import__("re"), "st": st, "signed_url": lambda uri, page=None: "https://signed.invalid/x"}
        exec(defs(CITES_SRC, "_CITE", "_mmss", "_label", "render_with_citations"), ns)
        exec(defs(UI_SRC, "_as_source"), ns)
        reply = [{"n": 1, "chunk_id": "acme:gratuity#4", "source_uri": "gs://b/acme/gratuity.pdf", "page": 3,
                  "quote": 'not less than "five" years', "score": 0.9},
                 {"n": 2, "chunk_id": "acme:gratuity#9", "source_uri": "gs://b/acme/fig.pdf", "page": 7, "quote": "a figure",
                  "score": 0.8, "kind": "figure", "media_url": "gs://b/acme/fig.png"}]
        cited = [ns["_as_source"](c) for c in reply]
        self.assertEqual(cited[0], {"text": 'not less than "five" years', "source_uri": "gs://b/acme/gratuity.pdf",
                                    "page_start": 3, "kind": "text", "media_url": None, "start": None, "end": None})
        self.assertEqual((cited[1]["kind"], cited[1]["media_url"]), ("figure", "gs://b/acme/fig.png"))
        ns["render_with_citations"](html.escape("Five years [1], see [2]. <img src=x onerror=alert(1)>", quote=False), cited)
        text, kw = drawn[0]
        self.assertTrue(kw.get("unsafe_allow_html"))
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", text)
        self.assertNotIn("<img", text)
        self.assertIn('title="not less than &quot;five&quot; years..."', text)       # pill 1 is the first citation
        self.assertIn(">[Fig 2, p.7]</span>", text)                                    # pill 2 is the figure


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class BrainsAgree(unittest.TestCase):
    """The kit's langchain, langgraph and adk brains, with scripted models: the same keys, tools and failures."""

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.CRITICAL)
        os.environ.setdefault("CHECKPOINT_DSN", "")
        sys.path[:0] = [str(KIT), str(KIT / "services/chat")]
        import shared.documind_tools as dt
        import brains
        import tools
        cls.dt, cls.brains, cls.tools = dt, brains, tools
        cls.seen = seen = []
        cls.down = down = []                    # non-empty: the stand-in rag-api answers 500

        class Api(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                seen.append((req["tenant_id"], req.get("brain"), self.headers.get(dt.ASSERTION_HEADER)))
                q = req["query"]
                body = {"answer": "rag-api's own answer", "answerable": True, "confidence": "high",
                        "citations": [{"chunk_id": f"acme:{q}#{k}", "source_uri": "gs://b/acme/x.pdf", "page": k + 1,
                                       "quote": f"{q} {k}", "score": 0.9} for k in range(2)]
                        + [{"chunk_id": "acme:shared#0", "source_uri": "gs://b/acme/s.pdf", "page": 1,
                            "quote": "shared", "score": 0.5}]}
                data = json.dumps({"detail": "down"} if down else body).encode()
                self.send_response(500 if down else 200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Api)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.saved = (dt.RAG_API_URL, dt._id_token)
        dt.RAG_API_URL, dt._id_token = f"http://127.0.0.1:{cls.srv.server_address[1]}", lambda aud: "TOKEN"

        from google.adk.models.base_llm import BaseLlm
        from google.adk.models.llm_response import LlmResponse
        from google.genai import types as gt
        from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
        from langchain_core.messages import AIMessage

        class Script(FakeMessagesListChatModel):
            def bind_tools(self, tools, **kw):
                return self

        class AdkScript(BaseLlm):
            model: str = "script"
            turns: list = []
            sent: list = []

            async def generate_content_async(self, llm_request, stream=False):
                self.sent.append(llm_request)
                yield self.turns.pop(0)

        def lc_turn(calls, text="done [1]"):
            return [AIMessage("", tool_calls=[{"name": n, "args": a, "id": f"c{i}"} for i, (n, a) in enumerate(calls)]),
                    AIMessage(text)]

        def adk_turn(calls, text="done [1]"):
            parts = [gt.Part(function_call=gt.FunctionCall(name=n, args=a)) for n, a in calls]
            return [LlmResponse(content=gt.Content(role="model", parts=parts)),
                    LlmResponse(content=gt.Content(role="model", parts=[gt.Part(text=text)]))]

        cls.Script, cls.AdkScript = Script, AdkScript
        cls.lc_turn, cls.adk_turn = staticmethod(lc_turn), staticmethod(adk_turn)
        cls.ctx = {"tenant_id": "acme", "user_id": "you", "assertion": ""}

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.dt.RAG_API_URL, cls.dt._id_token = cls.saved
        logging.disable(logging.NOTSET)         # the suites after this one in the same run log again

    def run_turns(self, name, turns, thread, adk_model=None, ctx=None):
        """Each item of `turns` is one user turn: the (tool, args) calls the model asks for, in one model message."""
        from langgraph.checkpoint.memory import InMemorySaver
        cfg = {"configurable": {"thread_id": f"acme:you:{thread}"}}
        context = {**(ctx or self.ctx), "brain": name}
        outs = []
        if name == "adk":
            b = self.brains.AdkBrain(None)
            for calls in turns:
                b.runner.agent.model = adk_model or self.AdkScript(turns=self.adk_turn(calls), sent=[])
                outs.append(b.answer("q", config=cfg, context=context))
            return outs
        script = [m for calls in turns for m in self.lc_turn(calls)]
        b = self.brains.build(name, InMemorySaver(), llm=self.Script(responses=script))
        for _ in turns:
            outs.append(b.answer("q", config=cfg, context=context))
        return outs

    def test_tool_calls_are_this_turns_on_a_long_thread(self):
        for name in AGENTS:
            outs = self.run_turns(name, [[("retrieve", {"query": f"q{t}"})] for t in range(3)], "long-" + name)
            self.assertEqual([o["tool_calls"] for o in outs], [["retrieve"]] * 3, name)      # the old code: 1, 2, 3
            self.assertEqual([o["refusals"] for o in outs], [[]] * 3, name)
            self.assertTrue(all(sorted(o) == ["answer", "citations", "refusals", "tool_calls"] for o in outs), name)

    def test_every_agent_brain_returns_numbered_citations(self):
        two = [[("retrieve", {"query": "alpha"}), ("retrieve", {"query": "beta"})]]
        for name in AGENTS:
            (out,) = self.run_turns(name, two, "cite-" + name)
            self.assertEqual([c["n"] for c in out["citations"]], list(range(1, 6)), name)    # two searches, one ledger
            self.assertEqual(sum(c["chunk_id"] == "acme:shared#0" for c in out["citations"]), 1, name)

    def test_turn_two_is_numbered_from_one(self):
        for name in AGENTS:
            first, second = self.run_turns(name, [[("retrieve", {"query": "alpha"})], [("retrieve", {"query": "beta"})]],
                                           "again-" + name)
            self.assertEqual([c["n"] for c in second["citations"]], [1, 2, 3], name)
            self.assertEqual([c["chunk_id"] for c in second["citations"]],
                             ["acme:beta#0", "acme:beta#1", "acme:shared#0"], name)            # this turn's, not turn 1's

    def test_one_tool_list_one_declaration(self):
        from google.adk.tools import FunctionTool
        from langchain_core.utils.function_calling import convert_to_openai_tool
        adk = [FunctionTool(f) for f in self.tools.for_adk()]
        self.assertEqual([t.name for t in self.tools.TOOLS], ["retrieve", "calculate_processing_cost"])
        self.assertEqual([t.name for t in self.tools.TOOLS], [t.name for t in adk])
        for lc, ak in zip(self.tools.TOOLS, adk):
            lcd = convert_to_openai_tool(lc)["function"]
            akd = ak._get_declaration().model_dump(mode="json", exclude_none=True)
            aks = akd.get("parameters") or akd["parameters_json_schema"]
            self.assertEqual(list(lcd["parameters"]["properties"]), list(aks["properties"]), lc.name)
            self.assertEqual(lcd["parameters"].get("required"), aks.get("required"), lc.name)
            self.assertEqual(inspect.cleandoc(lcd["description"]), inspect.cleandoc(akd["description"]), lc.name)
            for hidden in ("tenant_id", "assertion", "brain", "runtime", "cited"):
                self.assertNotIn(hidden, aks["properties"], lc.name)
                self.assertNotIn(hidden, lcd["parameters"]["properties"], lc.name)

    def test_the_model_cannot_choose_the_tenant_or_the_assertion(self):
        """What the model writes goes nowhere; what agent.py put in the context, the person's assertion included, arrives."""
        ctx = {"tenant_id": "initech", "user_id": "you", "assertion": "PERSON-ASSERTION"}
        for name in AGENTS:
            self.run_turns(name, [[("retrieve", {"query": "g", "tenant_id": "globex", "assertion": "anything"})]],
                           "tenant-" + name, ctx=ctx)
            self.assertEqual(self.seen[-1], ("initech", name, "PERSON-ASSERTION"), name)

    def test_failures_are_equal_error_results_in_every_brain(self):
        cases = {"blocked": ("delete_document", {"doc": "x"}, True),
                 "unknown": ("summon_rain", {}, True),
                 "wrong type": ("calculate_processing_cost", {"total_pages": "many"}, True),
                 "tier": ("calculate_processing_cost", {"total_pages": 10, "processing_type": "express"}, True),
                 "fraction": ("calculate_processing_cost", {"total_pages": 10.5}, True),
                 "query list": ("retrieve", {"query": ["a", "b"]}, True),          # one schema checks ADK's arguments too
                 "top_k float": ("retrieve", {"query": "g", "top_k": 2.5}, True),
                 "coerced": ("calculate_processing_cost", {"total_pages": "10"}, False),
                 "ok": ("calculate_processing_cost", {"total_pages": 10, "processing_type": "priority"}, False)}
        for key, (tool, args, refused) in cases.items():
            for name in AGENTS:
                (out,) = self.run_turns(name, [[(tool, args)]], f"fail-{key.replace(' ', '')}-{name}")
                self.assertEqual(out["refusals"], [tool] if refused else [], (key, name))
                self.assertEqual(out["tool_calls"], [tool], (key, name))

    def test_a_missing_argument_is_an_error_result_in_every_brain(self):
        for tool in ("calculate_processing_cost", "retrieve"):
            for name in AGENTS:
                (out,) = self.run_turns(name, [[(tool, {})]], f"missing-{tool}-{name}")
                self.assertEqual(out["refusals"], [tool], (tool, name))

    def test_a_failed_search_is_data_and_a_failed_mint_fails_the_turn(self):
        self.down.append(True)
        try:
            for name in AGENTS:
                (out,) = self.run_turns(name, [[("retrieve", {"query": "g"})]], "down-" + name)
                self.assertEqual((out["tool_calls"], out["refusals"], out["citations"]), (["retrieve"], [], []), name)
        finally:
            self.down.clear()

        from google.auth.exceptions import MalformedError
        for exc in (RuntimeError("could not mint an ID token"),
                    MalformedError("not in the expected format")):      # google-auth's errors are ValueErrors too
            def mint(audience):
                raise exc
            saved, self.dt._id_token = self.dt._id_token, mint
            try:
                for name in AGENTS:
                    with self.assertRaises(type(exc), msg=name):
                        self.run_turns(name, [[("retrieve", {"query": "g"})]], f"mint-{type(exc).__name__}-{name}")
            finally:
                self.dt._id_token = saved

    def test_the_adk_model_reads_what_the_langchain_model_reads(self):
        m = self.AdkScript(turns=self.adk_turn([("retrieve", {"query": "alpha"})]), sent=[])
        self.run_turns("adk", [[]], "read", adk_model=m)
        read = [p.function_response.response for c in m.sent[-1].contents for p in c.parts or [] if p.function_response]
        self.assertEqual(sorted(read[0]), ["answerable", "citations", "confidence"])          # no rag-api answer
        self.assertEqual([c["n"] for c in read[0]["citations"]], [1, 2, 3])                   # the n to cite by


if __name__ == "__main__":
    unittest.main()
