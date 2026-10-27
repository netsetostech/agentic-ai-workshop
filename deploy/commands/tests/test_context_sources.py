"""Offline checks for one turn's context by source (workshop lesson 6.1).

    python -m unittest commands/tests/test_context_sources.py -v          # from deploy/

No network, no credential, no cost. The first class needs only the standard library: mk/memory.mk's target, the
Makefile's .PHONY line and its 888 lines, the CI lines that run this file and the new files' UNOWNED.md rows; the
estimator, which is rag-api's own; a hand-made request split into its sources, each part counted once; the counting
chain on fake count_tokens functions - additive, refusing the declarations, ignoring the system instruction, refusing
the contents, refusing a later content - and the probe it reports; rag-api's prompt read from its source; a call's
rupees, cached and residual tokens included, adding up to its price; the command's refusals.

The second runs the kit's own brains and needs the chat image's pins (pip install -r services/chat/requirements.txt):
every brain, offline, its model calls read where they meet google-genai. Each call's sources sum to what the call was
sent, and each content has one source; the declarations are what binding sends (and ADK's FunctionTool declares); the
system prompt is the brain's own, with ADK's line after it; no connection leaves the machine, no token is minted,
count_tokens and the real generate_content are never called, and the placeholder project is put back. TOP_K=3 moves
the tool results and nothing else; a third turn carries the thread; the direct brain's turn is rag-api's answer; the
rupees are the turn's limits.Meter's; the counting chain runs on the captured google-genai requests. Without the pins
that class is skipped and says so; with DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins steps set it, a missing pin is an
error instead.
"""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch
import warnings

KIT = Path(__file__).resolve().parents[2]
ROOT = KIT.parent
for p in (str(KIT / "commands"), str(KIT / "services/chat"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import context_sources as cs                   # noqa: E402 - the standard library at import
from shared import prices                      # noqa: E402

FRAMEWORKS = all(importlib.util.find_spec(m) for m in ("langchain", "langgraph", "langchain_google_genai", "google.adk"))
REQUIRE = os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1"


def read(*parts) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def text(t, role="user"):
    return {"role": role, "parts": [{"text": t}]}


def call(name, args):
    return {"role": "model", "parts": [{"function_call": {"name": name, "args": args}}]}


def result(name, response):
    return {"role": "user", "parts": [{"function_response": {"name": name, "response": response}}]}


QUESTION = "After how many years is gratuity payable?"
DECLS = [{"name": "retrieve", "description": "Retrieve grounded passages.",
          "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}}},
         {"name": "calculate_processing_cost", "description": "Estimate a processing cost.",
          "parameters": {"type": "OBJECT", "properties": {"total_pages": {"type": "INTEGER"}}}}]
SYSTEM = "You are DocuMind AI. Search for every document question, a follow-up too."


def request():
    """A request a chat brain sends on its second turn's second call: the first turn whole, the question, the model's
    call and its result."""
    contents = [text("How many days of leave carry forward?"), call("retrieve", {"query": "leave carry forward"}),
                result("retrieve", {"citations": [{"n": 1, "quote": "Up to 15 days may be carried forward."}]}),
                text("Up to 15 days [1].", role="model"),
                text(QUESTION), call("retrieve", {"query": QUESTION}),
                result("retrieve", {"citations": [{"n": 1, "quote": "after five years of continuous service"}]})]
    return {"model": "gemini-3.6-flash", "system": SYSTEM, "tools": DECLS, "contents": contents}


def additive(contents, system=None, tools=None):
    """A count_tokens that is the estimator: the parts' estimates summed, the system and declarations included."""
    return (cs.tokens(cs.system_text(system)) + sum(cs.tokens(cs.declaration_text(d)) for d in tools or [])
            + sum(cs.content_tokens(c) for c in contents))


class Refusal(Exception):
    code, status, message = 400, "INVALID_ARGUMENT", "a field this endpoint does not take"


class TheSourcesAlone(unittest.TestCase):
    """What needs no LangChain: the wiring, the estimator, the split, the counting chain, rag-api's prompt, the rupees."""

    def test_the_target_its_phony_name_and_its_readme_row(self):
        mk, memory, readme = read("Makefile"), read("mk", "memory.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                     # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")]
        self.assertIn("context-sources", phony.split())                 # later kits append after it
        self.assertRegex(memory, r"(?m)^context-sources: \$\(if \$\(OFFLINE\),,guard-project\)$")   # OFFLINE=1: no project
        recipe = memory[memory.index("context-sources:"):]
        for flag in ("commands/graph-venv.sh commands/context_sources.py", "$(if $(OFFLINE),--offline,)",
                     '--brain "$(BRAIN)"', '--desk "$(DESK)"', '--turns "$(TURNS)"', '--top-k "$(TOP_K)"',
                     '$${Q:+--question "$$Q"}', '--tenant "$(TENANT)"', "$(if $(JSON),--json,)",
                     "DOCUMIND_IMPERSONATE_SA=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com",
                     "RAG_API_URL=https://documind-api-$$NUMBER.$(REGION).run.app"):
            self.assertIn(flag, recipe, flag)
        self.assertIn('Q="$(Q)";', recipe)                              # set before ${Q:+...} expands, comma and all
        self.assertIn("`context-sources`", readme)
        self.assertIn("`commands/context_sources.py`", readme)

    @unittest.skipUnless(shutil.which("make"), "no make here")
    def test_json_1_prints_the_record_through_make(self):
        """13 October 2026: the target had no JSON=, so lesson 6.1's cells ran the command through graph-venv.sh by hand
        to write a turn's record; JSON=1 is --json."""
        def dry(*args):
            r = subprocess.run(["make", "-n", "--no-print-directory", "-C", str(KIT), "context-sources", *args],
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            return r.stdout
        self.assertIn('--tenant "acme" --json', dry("OFFLINE=1", "BRAIN=langgraph", "TOP_K=3", "TENANT=acme", "JSON=1"))
        self.assertNotIn("--json", dry("OFFLINE=1", "BRAIN=langgraph"))

    def test_both_chat_pin_steps_run_this_file(self):
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_context_sources.py -v"
        self.assertIn(line, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = ROOT / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                            # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))

    def test_the_new_files_have_their_unowned_rows(self):
        # An UNOWNED.md row until lesson 6.1's page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = read("UNOWNED.md"), read("INDEX.md")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        self.assertIn("## Context sources (lesson 6.1)", unowned)
        for f in ("commands/context_sources.py", "commands/tests/test_context_sources.py"):
            self.assertTrue(f"| `{f}` | **6.1**" in unowned or f in quoted, f)
            self.assertTrue((KIT / f).exists(), f)
        mk_row = next((l for l in index.splitlines() if l.startswith("| `mk/memory.mk` |")), "| `x` | code | - | - |")
        self.assertTrue("| `mk/memory.mk` `context-sources` | **6.1**" in unowned       # the target's row, until lesson
                        or "6.1" in mk_row.split(" | ")[2].split(", "))                  # 6.1's page quotes it

    def test_the_estimator_is_rag_apis_own(self):
        cb = cs.context_budget()
        for sample in ("a", "abcd", "abcde", "x" * 403, "गोपनीयता नीति"):
            self.assertEqual(cs.tokens(sample), cb.estimate_tokens(sample))
        self.assertEqual(cs.tokens(""), 0)                              # an empty part counts nothing
        self.assertEqual(cs.part_text({"function_call": {"name": "retrieve", "args": {"query": "q"}}}),
                         'retrieve{"query": "q"}')
        self.assertEqual(cs.part_text({"function_response": {"name": "retrieve", "response": {"n": 1}}}),
                         'retrieve{"n": 1}')
        self.assertEqual(cs.part_text({"text": "hello", "signed": True}), "hello")    # a signature is never counted

    def test_a_request_splits_into_its_sources_each_part_once(self):
        req = request()
        labels = cs.label(req["contents"], QUESTION)
        self.assertEqual(labels, ["thread"] * 4 + ["question", "calls", "results"])
        got = cs.estimated_sources(req, labels)
        self.assertEqual(sum(got.values()), cs.request_tokens(req))     # every part, once
        self.assertEqual(got["system"], cs.tokens(SYSTEM))
        self.assertEqual(got["tools"], sum(cs.tokens(json.dumps(d)) for d in DECLS))
        self.assertEqual(got["question"], cs.tokens(QUESTION))
        self.assertEqual(got["thread"], sum(cs.content_tokens(c) for c in req["contents"][:4]))
        self.assertEqual(got["calls"], cs.content_tokens(req["contents"][5]))
        self.assertEqual(got["results"], cs.content_tokens(req["contents"][6]))
        self.assertEqual(got["other"], 0)

    def test_the_question_is_found_by_its_text_and_anything_else_is_other(self):
        contents = [text(QUESTION), text("Five years.", role="model"), text(QUESTION),
                    text("Continue processing previous requests as instructed.")]
        self.assertEqual(cs.label(contents, QUESTION), ["thread", "thread", "question", "other"])   # asked twice: the last
        self.assertEqual(cs.question_index(contents), 3)                # without its text: the last user text
        with self.assertRaises(ValueError):
            cs.question_index([call("retrieve", {}), result("retrieve", {})])

    def chain(self, count):
        req = request()
        raw = {"contents": req["contents"], "system": req["system"], "tools": req["tools"]}
        counter = cs.Counter(count)
        pieces, probe = cs.counted_pieces(raw, req, cs.label(req["contents"], QUESTION), counter)
        return req, pieces, probe, counter

    def test_the_counting_chain_on_an_additive_count(self):
        req, pieces, probe, counter = self.chain(additive)
        self.assertTrue(all(exact for _, _, exact, _ in pieces))
        self.assertEqual(sum(n for _, n, _, _ in pieces), cs.request_tokens(req))
        got = {s: sum(n for src, n, _, _ in pieces if src == s) for s in cs.SOURCES}
        self.assertEqual(got, cs.estimated_sources(req, cs.label(req["contents"], QUESTION)))
        self.assertEqual([s for s, _, _, _ in pieces], ["question", "thread", "system", "tools", "calls", "results"])
        self.assertEqual(probe, {"system": f"honoured: +{cs.tokens(SYSTEM):,}",
                                 "tools": f"honoured: +{got['tools']:,}", "contents": None})
        self.assertEqual(counter.asked, 6)                              # the question, the thread, two fields, two contents

    def test_refused_declarations_are_estimated_and_left_out_after(self):
        seen = []

        def count(contents, system=None, tools=None):
            seen.append(bool(tools))
            if tools:
                raise Refusal("refused")
            return additive(contents, system, None) + 2                 # two tokens of framing a request
        req, pieces, probe, _ = self.chain(count)
        self.assertEqual(probe["tools"], "refused: 400 INVALID_ARGUMENT: a field this endpoint does not take")
        self.assertTrue(probe["system"].startswith("honoured"))
        tools = [p for p in pieces if p[0] == "tools"]
        self.assertEqual(tools, [("tools", sum(cs.tokens(json.dumps(d)) for d in DECLS), False, None)])
        self.assertEqual(seen.count(True), 1)                           # asked once, never sent again
        self.assertTrue(all(exact for s, _, exact, _ in pieces if s != "tools"))
        self.assertEqual(sum(n for _, n, _, _ in pieces), cs.request_tokens(req) + 2)

    def test_a_system_instruction_counted_as_nothing_is_estimated(self):
        def count(contents, system=None, tools=None):
            return additive(contents, None, tools)                      # the field accepted and ignored
        _, pieces, probe, _ = self.chain(count)
        self.assertEqual(probe["system"], "accepted, but counted as nothing")
        self.assertIn(("system", cs.tokens(SYSTEM), False, None), pieces)

    def test_contents_refused_leave_every_source_estimated(self):
        def count(contents, system=None, tools=None):
            raise Refusal("refused")
        req, pieces, probe, _ = self.chain(count)
        self.assertTrue(probe["contents"].startswith("refused: 400 INVALID_ARGUMENT"))
        self.assertFalse(any(exact for _, _, exact, _ in pieces))
        self.assertEqual(sum(n for _, n, _, _ in pieces), cs.request_tokens(req))

    def test_a_later_content_refused_ends_the_counting_of_contents(self):
        def count(contents, system=None, tools=None):
            if any("function_response" in p for c in contents[5:] for p in c["parts"]):
                raise Refusal("refused")
            return additive(contents, system, tools)
        _, pieces, probe, _ = self.chain(count)
        self.assertTrue(probe["contents"].startswith("refused a content after the question"))
        self.assertEqual([(s, exact) for s, _, exact, _ in pieces][-2:], [("calls", True), ("results", False)])

    def test_rag_apis_prompt_is_read_from_its_source(self):
        k = cs.rag_constants()
        self.assertTrue(k["SYSTEM"].startswith("You are DocuMind, a retrieval-grounded assistant."))
        self.assertIn("effective date", k["DATED_RULE"])
        config = read("services", "rag-api", "config.py")
        for name in ("max_context_tokens", "max_answer_tokens"):
            self.assertEqual(k[name], int(re.search(rf"(?m)^\s+{name}: int = (\d+)$", config).group(1)))
        passages = [{"text": f"Clause {i}. " + "gratuity is payable " * 30, "source_uri": "gs://b/acme/act.md",
                     "page": i} for i in range(1, 4)]
        got = cs.rag_prompt("When is gratuity payable?", passages)
        self.assertEqual((got["packed"], got["dropped"]), (3, 0))
        self.assertEqual(got["tokens_in"], got["system"] + got["chunks"] + got["question"])
        self.assertEqual(got["system"], cs.tokens(k["SYSTEM"]))         # no chunk carries a date: no dated rule
        self.assertEqual(cs.rag_prompt("q", [])["packed"], 0)

    def test_a_calls_rupees_add_up_to_its_price(self):
        import limits
        req = request()
        entry = {"n": 1, "turn": 1, "model": "gemini-3.6-flash", "request": req, "raw": None,
                 "usage": {"input": cs.request_tokens(req) + 40, "cached": 120, "visible": 50, "thinking": 30},
                 "reply": {"text": "Five years [1].", "calls": []}}
        calls = cs.Calls()
        calls.made.append(entry)
        searches = cs.Searches(calls)
        meter = limits.Meter(model="gemini-3.6-flash")
        meter.charge_model(entry["usage"]["input"], 80, 120)
        with patch.object(cs, "own_prompt", return_value=SYSTEM):
            rec = cs.record("langgraph", "statute", "acme", QUESTION, 1, None, True, calls, searches,
                            [{"meter": meter, "answer": "Five years [1]."}], None)
        row = rec["calls"][0]
        self.assertEqual(row["residual"], 40)
        parts = sum(row["inr"]["sources"].values()) + row["inr"]["residual"] + row["inr"]["cached"] + row["inr"]["output"]
        self.assertAlmostEqual(parts, row["inr"]["call"], places=12)
        self.assertAlmostEqual(row["inr"]["call"], prices.inr(prices.usd("gemini-3.6-flash", row["usage"]["input"], 80, 120)),
                               places=12)
        self.assertAlmostEqual(rec["totals"]["model_inr"], rec["meter"]["model_inr"], places=12)
        self.assertLess(row["inr"]["cached"], 0)                        # a cached token bills at a tenth
        out = cs.render(rec)
        self.assertRegex(out, r"(?m)^  residual +40 ")
        self.assertIn("(120 cached), out 80 (30 thinking)", out)

    def test_the_commands_refusals(self):
        def refused(*argv, env=None):
            err = io.StringIO()
            with patch.dict(os.environ, env or {}), contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = cs.main(list(argv))
            return code, err.getvalue()
        self.assertEqual(refused("--offline", "--brain", "direct", "--turns", "2")[0], 2)
        code, err = refused("--offline", "--brain", "desk", "--turns", "3")
        self.assertEqual(code, 2)
        self.assertIn("checkpointer=False", err)
        self.assertIn("DESK= is for BRAIN=desk", refused("--offline", "--desk", "handbook")[1])
        self.assertIn("TURNS is 1 to 3", refused("--offline", "--turns", "4")[1])
        self.assertIn("TOP_K is 1 to 20", refused("--offline", "--top-k", "21")[1])
        self.assertIn("TOP_K is 1 to 20", refused("--offline", "--top-k", "0")[1])
        self.assertIn("DOCUMIND_PROFILE is not gcp", refused("--offline", env={"DOCUMIND_PROFILE": "local"})[1])
        lane = {k: "" for k in cs.LIVE_ENV}
        code, err = refused("--brain", "langgraph", env=lane)
        self.assertEqual(code, 2)
        self.assertIn("needs GOOGLE_CLOUD_PROJECT, RAG_API_URL, DOCUMIND_IMPERSONATE_SA", err)


@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class EveryBrainOffline(unittest.TestCase):
    """The kit's own brains, offline, their model calls read where they meet google-genai."""

    RUNS = {"langchain": {}, "langgraph": {}, "adk": {}, "direct": {}, "desk": {},
            "langgraph-k3": {"brain": "langgraph", "top_k": 3}, "desk-k3": {"brain": "desk", "top_k": 3},
            "langchain-t3": {"brain": "langchain", "turns": 3}, "adk-t2": {"brain": "adk", "turns": 2}}

    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        # The Rs 0 lane ranks every chunk of the tenant in pure Python, a few seconds a search, and these runs ask the
        # same few searches again and again. The ranking is deterministic, so each is ranked once and handed out as a
        # copy, as agent_patterns.offline() hands out its own: the tools number citations in place.
        from shared import documind_tools as dt
        ranked, real = {}, dt._retrieve_local

        def remembered(*args):
            key = json.dumps(args, default=str)
            if key not in ranked:
                ranked[key] = real(*args)
            return copy.deepcopy(ranked[key])
        rank = patch.object(dt, "_retrieve_local", remembered)
        rank.start()
        cls.addClassCleanup(rank.stop)
        cls.runs, cls.recs = {}, {}
        for name, kw in cls.RUNS.items():
            brain = kw.get("brain", name)
            opts = {k: v for k, v in kw.items() if k != "brain"}
            cls.runs[name] = cs.run(brain, **opts)
            cls.recs[name] = cs.record(brain, "statute", "acme", cs.QUESTION, opts.get("turns", 1), opts.get("top_k"),
                                       True, *cls.runs[name], None)

    def test_each_calls_sources_sum_to_what_it_was_sent(self):
        for name, (calls, _, _) in self.runs.items():
            rec = self.recs[name]
            measured = [c for c in calls.made if c["turn"] == rec["turns"]]
            self.assertEqual(len(measured), len(rec["calls"]), name)
            for c, row in zip(measured, rec["calls"]):
                labels = cs.label(c["request"]["contents"], cs.QUESTION)
                self.assertEqual(len(labels), len(c["request"]["contents"]), name)    # each content, one source
                self.assertEqual(sum(row["sources"].values()), c["usage"]["input"], name)
                self.assertEqual(c["usage"]["input"], cs.request_tokens(c["request"]), name)
                self.assertEqual(row["residual"], 0, name)
                self.assertEqual(row["sources"]["other"], 0, name)
            if rec["calls"]:
                self.assertEqual(rec["calls"][0]["asked"], [{"name": "retrieve", "args": {"query": cs.QUESTION}}], name)
                self.assertEqual(rec["calls"][-1]["asked"], [], name)
                first, last = rec["calls"][0]["sources"], rec["calls"][-1]["sources"]
                self.assertEqual((first["calls"], first["results"]), (0, 0), name)      # nothing returned yet
                self.assertGreater(last["results"], 0, name)

    def test_the_declarations_and_the_system_prompt_are_what_the_brain_sends(self):
        import brains
        import desk_agent
        import limits
        import tools
        from shared.profile import build_llm
        with patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": cs.PLACEHOLDER}):
            llm = build_llm()
            bound = llm.bind_tools(tools.TOOLS)
            chat = [d.model_dump(mode="json", exclude_none=True, by_alias=True)
                    for t in llm._format_tools(bound.kwargs["tools"]) for d in t.function_declarations]
            desk_bound = llm.bind_tools(desk_agent.TOOLSETS["statute"])
            desk = [d.model_dump(mode="json", exclude_none=True, by_alias=True)
                    for t in llm._format_tools(desk_bound.kwargs["tools"]) for d in t.function_declarations]
        from google.adk.tools import FunctionTool
        adk = [FunctionTool(limits.timed_adk(f))._get_declaration().model_dump(mode="json", exclude_none=True, by_alias=True)
               for f in tools.for_adk()]
        for name, decls, system in (("langchain", chat, brains.SYSTEM), ("langgraph", chat, brains.SYSTEM),
                                    ("desk", desk, desk_agent.system_prompt("statute"))):
            for c in self.runs[name][0].made:
                self.assertEqual(c["request"]["tools"], decls, name)
                self.assertEqual(c["request"]["system"], system, name)
            self.assertIsNone(self.recs[name]["system"]["added"], name)
            self.assertEqual(self.recs[name]["parameters_key"], "parameters", name)
        for c in self.runs["adk"][0].made:
            self.assertEqual(c["request"]["tools"], adk)
            self.assertTrue(c["request"]["system"].startswith(brains.SYSTEM))
        self.assertEqual(self.recs["adk"]["system"]["added"], 'You are an agent. Your internal name is "documind_adk".')
        self.assertEqual(self.recs["adk"]["parameters_key"], "parametersJsonSchema")
        self.assertEqual(self.recs["desk"]["declarations"],
                         ["retrieve", "gratuity_estimate", "statutory_deadline", "threshold_check"])

    def test_offline_makes_no_call(self):
        from google.auth import default as _  # noqa: F401 - imported, so the patch below has its target
        from google.genai import models as gm
        attempts = []

        def trap(what):
            def refuse(*args, **kwargs):
                attempts.append(what)
                raise AssertionError(f"offline reached {what}")
            return refuse
        real_connect = socket.socket.connect

        def connect(sock, address):
            if not (isinstance(address, tuple) and str(address[0]) in ("127.0.0.1", "::1", "localhost")):
                attempts.append(f"connect {address!r}")
            return real_connect(sock, address)
        before = os.environ.get("GOOGLE_CLOUD_PROJECT")
        with patch.object(gm.Models, "generate_content", trap("generate_content")), \
                patch.object(gm.AsyncModels, "generate_content", trap("async generate_content")), \
                patch.object(gm.Models, "count_tokens", trap("count_tokens")), \
                patch("google.auth.default", trap("google.auth.default")), \
                patch.object(socket.socket, "connect", connect):
            env = {k: v for k, v in os.environ.items() if k not in ("GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS")}
            with patch.dict(os.environ, env, clear=True):
                for brain in ("langgraph", "adk", "desk", "direct"):
                    rec = cs.measure(brain)
                    self.assertGreater(rec["totals"]["turn_inr"], 0, brain)
                self.assertNotIn("GOOGLE_CLOUD_PROJECT", os.environ)        # the placeholder was put back
        self.assertEqual(attempts, [])
        self.assertEqual(os.environ.get("GOOGLE_CLOUD_PROJECT"), before)

    def test_top_k_moves_the_tool_results_and_nothing_else(self):
        for base, changed in (("langgraph", "langgraph-k3"), ("desk", "desk-k3")):
            a, b = self.recs[base], self.recs[changed]
            self.assertEqual(len(a["calls"]), len(b["calls"]), base)
            for x, y in zip(a["calls"], b["calls"]):
                for s in cs.SOURCES:
                    if s != "results":
                        self.assertEqual(x["sources"][s], y["sources"][s], (base, s))
            self.assertLess(b["totals"]["tokens"]["results"], a["totals"]["tokens"]["results"], base)
            self.assertEqual([(s["top_k"], s["sent"], s["found"]) for s in b["searches"]], [(5, 3, 3)], base)
            self.assertEqual([(s["top_k"], s["sent"], s["found"]) for s in a["searches"]], [(5, 5, 5)], base)
        k3 = self.recs["langgraph-k3"]["searches"][0]["rag"]["prompt"]
        k5 = self.recs["langgraph"]["searches"][0]["rag"]["prompt"]
        self.assertEqual((k5["packed"], k3["packed"]), (5, 3))              # rag-api's own prompt moves too
        self.assertLess(k3["chunks"], k5["chunks"])
        self.assertEqual(k3["system"], k5["system"])

    def test_a_third_turn_carries_the_thread(self):
        rec = self.recs["langchain-t3"]
        calls = self.runs["langchain-t3"][0]
        self.assertEqual(rec["earlier"]["turns"], 2)
        self.assertEqual(rec["earlier"]["model_calls"], 4)
        self.assertEqual(rec["earlier"]["searches"], 2)
        threads = [r["sources"]["thread"] for r in rec["calls"]]
        self.assertEqual(len(set(threads)), 1)                              # the same thread rides every call
        earlier = [c for c in calls.made if c["turn"] == 3][0]["request"]["contents"]
        qi = cs.question_index(earlier, cs.QUESTION)
        self.assertEqual(threads[0], sum(cs.content_tokens(c) for c in earlier[:qi]))
        asked = [c["parts"][0]["text"] for c in earlier[:qi] if c["role"] == "user" and "text" in c["parts"][0]]
        self.assertEqual(asked, list(cs.EARLIER))
        fresh = self.recs["langchain"]
        for s in ("system", "tools", "question", "calls", "results"):
            self.assertEqual(rec["totals"]["tokens"][s], fresh["totals"]["tokens"][s], s)
        self.assertEqual(fresh["totals"]["tokens"]["thread"], 0)
        self.assertGreater(self.recs["adk-t2"]["calls"][0]["sources"]["thread"], 0)    # ADK's own session carries it

    def test_the_direct_brains_turn_is_rag_apis_answer(self):
        rec = self.recs["direct"]
        self.assertEqual(rec["calls"], [])
        (search,) = rec["searches"]
        self.assertTrue(search["rag"]["estimated"])
        self.assertEqual(search["rag"]["tokens_in"], search["rag"]["prompt"]["tokens_in"])
        self.assertAlmostEqual(rec["totals"]["turn_inr"], rec["meter"]["rag_inr"], places=12)
        self.assertEqual(rec["meter"]["model_calls"], 0)
        self.assertTrue(rec["answer"].startswith("(offline, scripted) rag-api's own answer"))
        self.assertIn("no model call of the chat's own", cs.render(rec))

    def test_the_rupees_are_the_turns_meters(self):
        for name, rec in self.recs.items():
            self.assertEqual(rec["meter"]["model_calls"], len(rec["calls"]), name)
            self.assertAlmostEqual(rec["totals"]["model_inr"], rec["meter"]["model_inr"], places=12, msg=name)
            self.assertAlmostEqual(rec["totals"]["rag_inr"], rec["meter"]["rag_inr"], places=12, msg=name)
            for row in rec["calls"]:
                parts = (sum(row["inr"]["sources"].values()) + row["inr"]["residual"] + row["inr"]["cached"]
                         + row["inr"]["output"])
                self.assertAlmostEqual(parts, row["inr"]["call"], places=12, msg=name)
        self.assertEqual(self.recs["desk"]["totals"]["rag_inr"], 0)        # /v1/passages: no model call inside

    def test_the_counting_chain_on_the_captured_requests(self):
        def count(contents, system=None, tools=None):
            return cs.request_tokens(cs.plain_request("m", contents, system, tools))
        rec = cs.record("adk", "statute", "acme", cs.QUESTION, 2, None, True, *self.runs["adk-t2"], cs.Counter(count))
        same = self.recs["adk-t2"]
        for x, y in zip(rec["calls"], same["calls"]):
            self.assertEqual(x["sources"], y["sources"])
            self.assertEqual((x["estimated"], x["residual"]), ([], 0))
        self.assertTrue(rec["probe"]["tools"].startswith("honoured"))

        def refusing(contents, system=None, tools=None):
            if tools:
                raise Refusal("refused")
            return count(contents, system, None)
        rec = cs.record("langgraph", "statute", "acme", cs.QUESTION, 1, None, True, *self.runs["langgraph"],
                        cs.Counter(refusing))
        self.assertTrue(rec["probe"]["tools"].startswith("refused: 400"))
        self.assertTrue(all(r["estimated"] == ["tools"] for r in rec["calls"]))
        out = cs.render(rec)
        self.assertRegex(out, r"(?m)^  tool declarations +~ *\d")
        self.assertIn("probe (workshop lesson 6.1, batch 1)", out)

    def test_on_a_lane_each_call_goes_to_the_sdk_as_it_was_made(self):
        # Without a script the capture hands each call to google-genai's own method, unchanged, and records its usage.
        # A stand-in takes that method's place here, sync for LangGraph's model and async for ADK's.
        from google.genai import models as gm
        made = []

        def answer(model, contents, config):
            made.append((model, len(contents), type(config).__name__))
            from google.genai import _transformers as t
            return cs.scripted(cs.plain_request(model, t.t_contents(contents), config.system_instruction, config.tools))

        def real(self_, *, model, contents, config=None):
            return answer(model, contents, config)

        async def areal(self_, *, model, contents, config=None):
            return answer(model, contents, config)
        for brain in ("langgraph", "adk"):
            made.clear()
            calls = cs.Calls()
            searches = cs.Searches(calls)
            with patch.object(gm.Models, "generate_content", real), patch.object(gm.AsyncModels, "generate_content", areal):
                with cs.offline_lane(), calls.installed(), searches.installed():
                    done = cs.run_turns(brain, [cs.QUESTION], "acme", "statute", calls)
            self.assertEqual([m for m, _, _ in made], ["gemini-3.6-flash"] * 2, brain)
            self.assertEqual([n for _, n, _ in made], [1, 3], brain)
            self.assertEqual({k for _, _, k in made}, {"GenerateContentConfig"}, brain)
            self.assertEqual([c["usage"]["input"] for c in calls.made],
                             [cs.request_tokens(c["request"]) for c in calls.made], brain)
            self.assertEqual(done[-1]["meter"].model_calls, 2, brain)
            self.assertTrue(done[-1]["answer"].startswith("(offline, scripted)"), brain)

    def test_the_command_prints_the_turn_and_its_json(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cs.main(["--offline", "--brain", "desk", "--top-k", "3", "--json"]), 0)
        rec = json.loads(out.getvalue())
        self.assertEqual((rec["brain"], rec["desk"], rec["counter"], rec["top_k"]), ("desk", "statute", "estimate", 3))
        self.assertEqual([r["sources"] for r in rec["calls"]], [r["sources"] for r in self.recs["desk-k3"]["calls"]])
        text_ = cs.render(rec)
        self.assertIn("every search sends top_k 3 (TOP_K), whatever was asked", text_)
        self.assertIn("search: top_k 3 (TOP_K; 5 asked); 3 passages back", text_)
        self.assertIn("/v1/passages: no model call inside the search", text_)
        self.assertIn("the turn's Meter (limits.py) charged", text_)
        self.assertNotRegex(out.getvalue() + text_, r"documind-ai-(?!YOUR-ID)")


if __name__ == "__main__":
    unittest.main()
