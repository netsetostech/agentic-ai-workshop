"""The agent bench (workshop lessons 10.1-10.3 and 10.5): commands/agent_patterns.py, agent_turn.py and agent-turn.sh,
evals/agent_eval.py's runs, and their wiring.

    python -m unittest commands/tests/test_agent_bench.py -v          # from deploy/
    make agent-tests                                                   # the same, in ~/graph-venv with the chat pins

The first half needs the standard library only and runs in CI's shared interpreter: the make targets, appended below
every Desk target; the script; the CI lines and the UNOWNED.md rows; desk_calc's selftest lines that lesson 10.4
prints; the recorder's arithmetic, the scripted token counts and the slip schedule; the corpus store. The second half
runs the Desk agent's loop on a scripted model over the kit's own corpus and needs the chat image's pins (pip install -r
services/chat/requirements.txt): the turn held equal to desk_agent.run()'s, the context run() builds, the recorder
inside the turn's limits adding no graph node, thinking sent on every call, the call cap, an invented cap refused, the
offline corpus with no network, and agent_turn.py and agent_eval.py end to end. Without the pins that half is skipped
and says so; with DOCUMIND_REQUIRE_LIBS=1, as CI's chat-pins steps set it, a missing pin is an error instead.

No test calls a model or a cloud API.
"""
from __future__ import annotations

import importlib.util
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
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
TARGETS = ("agent-turn", "agent-eval", "agent-tests")
GRATUITY = "I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?"
NEW_FILES = ("commands/agent_patterns.py", "commands/agent_turn.py", "commands/agent-turn.sh", "evals/agent_tasks.jsonl",
             "evals/agent_eval.py", "evals/paired.py", "commands/tests/test_agent_bench.py",
             "evals/tests/test_paired.py", "evals/tests/test_agent_eval.py")


def read(*parts) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


# ================================================================== the standard-library half
class Wiring(unittest.TestCase):
    def test_the_targets(self):
        mk, agents, readme = read("Makefile"), read("mk", "agents.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                             # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        for target in TARGETS:
            self.assertIn(target, phony)
            self.assertIn(f"`{target}`", readme)
            self.assertIn(f"\n{target}:", agents)
        self.assertIn("\nagent-turn: $(if $(OFFLINE),,guard-project)\n", agents)
        self.assertIn("\nagent-eval: $(if $(or $(OFFLINE),$(CHECK),$(REPLAY),$(COMPARE)),,guard-project)\n", agents)
        self.assertIn("`agent-turn.sh`", readme)

    def test_appended_below_every_desk_target(self):
        """Lesson 10.4's build reads route-eval's recipe by its line number: the bench's targets come after the last
        Desk recipe, so no line above them moves."""
        agents = read("mk", "agents.mk")
        lines = agents.splitlines()
        last_desk = agents.index("\ndesk-operators: guard-project\n")
        self.assertTrue(all(agents.index(f"\n{t}:") > last_desk for t in TARGETS))
        at = lines.index("route-eval: guard-project") + 2                      # 10.4's own derivation
        self.assertIn("evals/route_eval.py --live", lines[at + 1])
        self.assertEqual(at, 214)

    def test_the_script(self):
        sh, limits_sh = read("commands", "agent-turn.sh"), read("commands", "limits-check.sh")
        for line in ('VENV="${GRAPH_VENV:-$HOME/graph-venv}"', '[ -x "$VENV/bin/python" ] || "${PY:-python3}" -m venv "$VENV"',
                     '"$VENV/bin/pip" install -q -r services/chat/requirements.txt'):
            self.assertIn(line, sh)
            self.assertIn(line, limits_sh)
        self.assertIn('export DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com"', sh)
        self.assertIn('RAG_API_URL="https://documind-api-$NUMBER.$REGION.run.app"', sh)
        self.assertLess(sh.index('if [ "${OFFLINE:-}" = 1 ]; then'), sh.index("gcloud projects describe"))   # OFFLINE: no gcloud
        self.assertIn('exec "$VENV/bin/python" commands/agent_turn.py "$MODE" "${ARGS[@]}"', sh)
        self.assertIn("set -euo pipefail", sh)

    def test_invent_and_launder_are_make_variables(self):
        """13 October 2026: make agent-turn passed neither of agent_turn.py's offline flags, so lessons 10.1 and 10.3 ran
        the script through agent-turn.sh by hand. INVENT and LAUNDER: 1 for the flag's own figure, else the figure."""
        agents, sh = read("mk", "agents.mk"), read("commands", "agent-turn.sh")
        recipe = agents.split("\nagent-turn: $(if $(OFFLINE),,guard-project)\n", 1)[1].split("\n", 1)[0]
        self.assertIn(' INVENT="$(INVENT)" LAUNDER="$(LAUNDER)" ', recipe)
        for flag in ("INVENT", "LAUNDER"):
            self.assertIn(f'if [ -n "${{{flag}:-}}" ]; then ARGS+=(--{flag.lower()}); [ "${flag}" = 1 ] || '
                          f'ARGS+=("${flag}"); fi', sh)

    @unittest.skipIf(sys.platform == "win32" or not shutil.which("bash"), "a POSIX bash")
    def test_agent_turn_sh_hands_them_to_agent_turn_py(self):
        with tempfile.TemporaryDirectory() as venv:
            (Path(venv) / "bin").mkdir()
            for tool, body in (("pip", "exit 0"), ("python", 'printf "%s\\n" "$@"')):     # python prints its argv
                (Path(venv) / "bin" / tool).write_text(f"#!/usr/bin/env bash\n{body}\n", encoding="utf-8")
                (Path(venv) / "bin" / tool).chmod(0o755)

            def argv(**env):
                keep = {k: v for k, v in os.environ.items() if k not in ("INVENT", "LAUNDER", "PATTERN", "TENANT", "DESK")}
                r = subprocess.run(["bash", "commands/agent-turn.sh"], cwd=str(KIT), capture_output=True, text=True,
                                   timeout=60, env={**keep, "GRAPH_VENV": venv, "OFFLINE": "1", **env})
                self.assertEqual(r.returncode, 0, r.stderr)
                return r.stdout.splitlines()

            head = ["commands/agent_turn.py", "--offline", "--pattern", "react_text", "--desk", "astar", "--tenant", "acme"]
            self.assertEqual(argv(PATTERN="react_text"), head)
            self.assertEqual(argv(PATTERN="react_text", INVENT="1"), head + ["--invent"])
            self.assertEqual(argv(PATTERN="react_text", INVENT="Rs 3,00,000", LAUNDER="1"),
                             head + ["--invent", "Rs 3,00,000", "--launder"])

    @unittest.skipUnless(shutil.which("make"), "no make here")
    def test_make_agent_turn_passes_them_to_the_script(self):
        r = subprocess.run(["make", "-n", "--no-print-directory", "-C", str(KIT), "agent-turn", "OFFLINE=1", "PATTERN=verify",
                            "LAUNDER=Rs 2,40,000"], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(' OFFLINE=1 INVENT="" LAUNDER="Rs 2,40,000" PY=', r.stdout)

    def test_ci_runs_the_chat_pins_half(self):
        line = "DOCUMIND_REQUIRE_LIBS=1 /tmp/chat-venv/bin/python -m unittest commands/tests/test_agent_bench.py -v"
        self.assertIn(line, read(".github", "workflows", "documind-dryrun.yml"))
        repo_ci = KIT.parent / ".github" / "workflows" / "checks.yml"
        if repo_ci.exists():                                                    # the authoring repository's own CI
            self.assertIn(line, repo_ci.read_text(encoding="utf-8"))

    def test_the_new_files_are_listed(self):
        unowned = read("UNOWNED.md")
        for f in NEW_FILES:
            self.assertTrue((KIT / f).exists(), f)
            self.assertIn(f"`{f}`", unowned, f)

    def test_desk_calc_keeps_the_lines_lesson_10_4_prints(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(desk_calc.selftest(), 0)
        lines = out.getvalue().rstrip("\n").splitlines()
        self.assertEqual(lines[:2], ["ok    accrual: acme/hr_policy_2026.md:19 says it",
                                     "ok    carry_forward: acme/hr_policy_2026.md:19-20 says it"])
        self.assertEqual(lines[-1], "every rule says what its corpus line says, and the figures hold")
        self.assertIn("ok    the same figure with no calculator call", lines)


class Records(unittest.TestCase):
    def test_a_call_with_thinking(self):
        usage = {"input_tokens": 3000, "output_tokens": 450, "total_tokens": 3450,
                 "input_token_details": {"cache_read": 1000}, "output_token_details": {"reasoning": 400}}
        c = ap.call_record(2, usage, "high", "gemini-3.6-flash", [{"name": "retrieve", "args": {"query": "q"}, "id": "x"}],
                           "text", "m-2")
        self.assertEqual((c["tokens_in"], c["cached_tokens"], c["thinking_tokens"], c["visible_tokens"], c["tokens_out"]),
                         (3000, 1000, 400, 50, 450))
        self.assertEqual(c["inr"], round(prices.inr((2000 * 1.50 + 1000 * 0.15 + 450 * 7.50) / 1e6), 6))
        self.assertEqual((c["n"], c["id"], c["thinking_level"], c["tool_calls"]),
                         (2, "m-2", "high", [{"name": "retrieve", "args": {"query": "q"}}]))

    def test_a_call_with_no_thinking_reported(self):
        c = ap.call_record(1, {"input_tokens": 100, "output_tokens": 20}, "minimal", "gemini-3.6-flash")
        self.assertEqual((c["thinking_tokens"], c["visible_tokens"]), (0, 20))
        self.assertEqual(ap.call_record(1, None, "low", "gemini-3.6-flash")["inr"], 0.0)

    def test_the_scripts_counts(self):
        u = ap.scripted_usage(401, "abcd" * 10, [{"name": "retrieve", "args": {"query": "q"}}], "low")
        self.assertEqual(u["input_tokens"], 101)                                # four characters a token, rounded up
        self.assertEqual(u["output_token_details"], {"reasoning": 64})
        self.assertEqual(u["output_tokens"], 64 + -(-(40 + len("retrieve") + len('{"query": "q"}')) // 4))
        self.assertNotIn("output_token_details", ap.scripted_usage(10, "x", [], "minimal"))
        self.assertEqual(ap.SCRIPTED_THINKING, {"minimal": 0, "low": 64, "medium": 256, "high": 1024})

    def test_the_slip_schedule(self):
        rows = {r["id"]: r for r in ap.tasks()}
        self.assertEqual([ap.slips(rows["trap-encash-cap"], r) for r in range(3)], [True, False, False])
        for kind in ("lookup", "refuse"):
            self.assertFalse(any(ap.slips(r, n) for r in rows.values() if r["kind"] == kind for n in range(20)))
        calc = [ap.slips(r, n) for r in rows.values() if r["kind"] == "calc" for n in range(40)]
        self.assertTrue(0.1 < sum(calc) / len(calc) < 0.3)                      # about one run in five

    def test_the_planned_patterns_are_errors_that_say_so(self):
        """A pattern still to come is an error naming its lesson until its pull request moves it into PATTERNS (10.1's
        in test_agent_patterns.py, 10.2's in test_agent_plans.py)."""
        self.assertEqual(list(ap.PATTERNS)[0], "loop")
        self.assertFalse(set(ap.PATTERNS) & set(ap.PLANNED))
        for name, lesson in ap.PLANNED.items():
            with self.assertRaisesRegex(ValueError, f"planned for lesson {re.escape(lesson)}'s pull request"):
                ap.pattern(name)
        with self.assertRaisesRegex(ValueError, "no pattern 'chain'"):
            ap.pattern("chain")

    def test_the_corpus_store_holds_a_tenant_and_its_classes(self):
        store = ap.CorpusStore()
        policy = store.get(where={"$and": [{"tenant_id": "zeta"}, {"doc_type": "policy"}]})
        self.assertTrue(policy["documents"])
        self.assertEqual({m["tenant_id"] for m in policy["metadatas"]}, {"zeta"})
        self.assertEqual({m["doc_type"] for m in policy["metadatas"]}, {"policy"})
        both = store.get(where={"$and": [{"tenant_id": "zeta"}, {"doc_type": {"$in": ["policy", "guidance"]}}]})
        self.assertEqual({m["doc_type"] for m in both["metadatas"]}, {"policy", "guidance"})
        self.assertTrue(all(m["source_uri"].startswith("gs://documind-ai-YOUR-ID-uploads/zeta/") for m in both["metadatas"]))
        self.assertEqual(store.get(where={"doc_type": "policy"}), {"documents": [], "metadatas": []})   # no tenant, nothing


# ================================================================== the chat image's pins
@unittest.skipUnless(FRAMEWORKS or REQUIRE, "needs the chat image's pins: pip install -r services/chat/requirements.txt")
class Loop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore")
        logging.disable(logging.CRITICAL)
        import desk_agent
        import limits
        from langchain_core.language_models.chat_models import BaseChatModel
        from langchain_core.messages import AIMessage
        from langchain_core.outputs import ChatGeneration, ChatResult
        cls.da, cls.limits = desk_agent, limits
        cls.rows = {r["id"]: r for r in ap.tasks()}

        class Looping(BaseChatModel):
            """Asks for a search on every call: only the turn's limits stop it."""

            @property
            def _llm_type(self):
                return "looping"

            def bind_tools(self, tools, tool_choice=None, **kw):
                return self.bind(**kw)

            def _generate(self, messages, stop=None, run_manager=None, **kw):
                n = sum(m.type == "ai" for m in messages)
                msg = AIMessage("", tool_calls=[{"name": "retrieve", "args": {"query": f"earned leave {n}"},
                                                 "id": f"loop-{n}", "type": "tool_call"}],
                                usage_metadata={"input_tokens": 1000, "output_tokens": 50, "total_tokens": 1050})
                return ChatResult(generations=[ChatGeneration(message=msg)])

        cls.Looping = Looping

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def turn(self, question=GRATUITY, **kw):
        llm = kw.pop("llm", None) or ap.scripted(question, kw.get("tenant", "acme"))
        with ap.offline():
            return ap.run("loop", question, llm=llm, **kw), llm

    def test_the_loop_works_the_gratuity_out_with_its_calculator(self):
        turn, llm = self.turn()
        self.assertEqual((turn["tool_calls"], turn["refusals"], turn["retrieve_calls"], turn["stopped_by"]),
                         (["retrieve", "gratuity_estimate"], [], 1, None))
        (calc,) = turn["calculations"]
        self.assertEqual((calc["value"], calc["estimate"]), (240000, True))
        self.assertEqual({k: calc["args"][k] for k in ("monthly_wage", "years", "months")},
                         {"monthly_wage": 52000, "years": 7, "months": 8})
        self.assertEqual(turn["answer"], "Gratuity, an estimate: Rs 2,40,000 [2].")
        self.assertIn("Worked out in code:\n- Gratuity, an estimate (Code on Social Security, 2020, s.53(1)", turn["composed"])
        self.assertEqual([p["source"] for p in turn["passages"]][:2],
                         ["payment_of_gratuity_act_1972.pdf", "code_on_social_security_2020.pdf"])
        self.assertFalse(any("gs://" in json.dumps(p) for p in turn["passages"]))          # file names, never a URI
        self.assertEqual(desk_calc.unsupported(turn["answer"], turn["calculations"], GRATUITY,
                                               *[p["text"] for p in turn["passages"]]), [])
        self.assertEqual(turn["model_calls"], 3)
        self.assertEqual([c["n"] for c in turn["calls"]], [1, 2, 3])
        self.assertEqual(turn["inr"], round(sum(c["inr"] for c in turn["calls"]), 6))
        self.assertEqual([s["call"] for s in turn["trace"]], [1, 2, 3])
        self.assertEqual(turn["trace"][1]["tools"][0]["result"]["value"], 240000)

    def test_the_turn_is_desk_agent_runs(self):
        """desk_agent.run() on the same script and corpus, through the Desk's own agent(): the same answer, passages,
        calculations, tool calls, refusals, searches, answerable and stop."""
        q = self.rows["calc-encash-invented-cap"]["question"]
        theirs_llm = ap.scripted(q)
        with ap.offline(), patch.dict(self.da._AGENTS, clear=True), patch.dict(self.da._MODEL, {"llm": theirs_llm}):
            meter = self.limits.Meter(model=self.da.AGENT_MODEL)
            theirs = self.da.run("astar", q, ap.classes_for("astar"), {"tenant": "acme", "assertion": None, "meter": meter})
        ours, _ = self.turn(q)
        for key in ("answer", "calculations", "tool_calls", "refusals", "retrieve_calls", "answerable", "stopped_by"):
            self.assertEqual(ours[key], theirs[key], key)
        self.assertEqual([(p["chunk_id"], p["text"]) for p in ours["passages"]],
                         [(p["chunk_id"], p["text"]) for p in theirs["passages"]])
        self.assertEqual(meter.model_calls, ours["model_calls"])

    def test_the_context_is_the_one_run_builds(self):
        seen = {}

        class Agent:
            def invoke(self, state, config=None, context=None):
                seen.update(context)
                from langchain_core.messages import AIMessage
                return {"messages": [AIMessage("done")]}

        meter = self.limits.Meter()
        with patch.object(self.da, "agent", lambda kind: Agent()):
            self.da.run("handbook", "q?", ["policy"], {"tenant": "zeta", "assertion": "A", "meter": meter})
        ours = ap.context("handbook", "q?", tenant="zeta", meter=meter, assertion="A")
        self.assertEqual(ours.pop("bench_calls"), [])
        self.assertEqual(ours, seen)
        self.assertEqual(ap.classes_for("handbook"), ["policy"])
        self.assertEqual(ap.classes_for("statute"), ["statute", "guidance"])
        self.assertEqual(ap.classes_for("astar"), ["policy", "statute", "guidance"])

    def test_the_recorder_adds_no_node_and_sits_inside_the_limits(self):
        from langchain.agents import create_agent
        built = []

        def capture(**kw):
            built.append(kw)
            return create_agent(**kw)

        with patch("langchain.agents.create_agent", capture):
            self.turn()
        (kw,) = built
        self.assertEqual([type(m).__name__ for m in kw["middleware"]], ["DeskTurnLimits", "Recorder", "DeskGuard"])
        self.assertEqual((kw["tools"], kw["system_prompt"], kw["checkpointer"]),
                         (self.da.TOOLSETS["astar"], self.da.system_prompt("astar"), False))
        plain = create_agent(model=kw["model"], tools=kw["tools"], middleware=[kw["middleware"][0], kw["middleware"][2]])
        self.assertEqual(sorted(create_agent(**kw).get_graph().nodes), sorted(plain.get_graph().nodes))
        recorder = type(kw["middleware"][1])
        self.assertEqual({n for n in vars(recorder) if not n.startswith("_")}, {"wrap_model_call", "awrap_model_call"})

    def test_thinking_goes_with_every_call(self):
        turn, llm = self.turn(thinking="high")
        self.assertEqual(llm.seen, ["high"] * 3)
        self.assertEqual({(c["thinking_level"], c["thinking_tokens"]) for c in turn["calls"]}, {("high", 1024)})
        turn, llm = self.turn()
        self.assertEqual(llm.seen, [None] * 3)                                  # unset: the model's own level
        self.assertEqual({c["thinking_level"] for c in turn["calls"]}, {self.da.THINKING_LEVEL})
        with self.assertRaisesRegex(ValueError, "thinking is one of minimal, low, medium, high"):
            self.turn(thinking="max")

    def test_the_recorders_rupees_are_the_meters(self):
        meter = self.limits.Meter(model=self.da.AGENT_MODEL)
        turn, _ = self.turn(meter=meter)
        self.assertAlmostEqual(prices.inr(meter.cost_usd), turn["inr"], places=5)
        self.assertEqual(meter.model_calls, turn["model_calls"])

    def test_the_turns_limits_stop_the_loop(self):
        meter = self.limits.Meter(max_model_calls=3, model=self.da.AGENT_MODEL)
        turn, _ = self.turn(llm=self.Looping(), meter=meter)
        self.assertEqual((turn["stopped_by"], turn["answer"], turn["model_calls"]),
                         ("model_calls", self.limits.STOP_ANSWER, 3))          # the refused fourth call: not a call
        self.assertIsNone(turn["trace"][-1]["call"])
        self.assertFalse(turn["answerable"])

    def test_an_invented_cap_is_refused(self):
        row = json.loads(json.dumps(self.rows["calc-encash-invented-cap"]))
        row["calcs"][0]["args"]["cap"] = 100                                    # the manager's figure
        llm = ap._scripted_class()(model=self.da.AGENT_MODEL, thinking_level="low", task=row)
        turn, _ = self.turn(row["question"], llm=llm)
        self.assertEqual((turn["refusals"], turn["calculations"]), (["encashable_days"], []))
        refused = turn["trace"][1]["tools"][0]["result"]["error"]
        self.assertIn("refused: cap = 100 is not written in LV-07 of a handbook passage", refused)

    def test_the_offline_corpus_needs_no_network(self):
        from shared import documind_tools
        before = (documind_tools.PROFILE, documind_tools.retrieve)

        def no_token(audience):
            raise AssertionError("an ID token was minted offline")

        with patch.object(documind_tools, "_id_token", no_token), ap.offline():
            got = documind_tools.retrieve("earned leave encashed on exit", "acme", doc_type=["policy"], passages=True)
            again = documind_tools.retrieve("earned leave encashed on exit", "acme", doc_type=["policy"], passages=True)
            zeta = documind_tools.retrieve("earned leave carried forward", "zeta", doc_type=["policy"], passages=True)
        self.assertTrue(got["answerable"])
        self.assertTrue(got["passages"][0]["section"].startswith("LV-07"))
        self.assertIn("capped at 45 days", got["passages"][0]["text"])
        self.assertEqual(got, again)
        self.assertTrue(all(p["chunk_id"].startswith("zeta:") for p in zeta["passages"]))
        self.assertIn("A maximum of 18 days", zeta["passages"][0]["text"])
        self.assertEqual((documind_tools.PROFILE, documind_tools.retrieve), before)    # put back

    def test_a_single_turn_never_slips(self):
        row = self.rows["calc-gratuity-7y8m"]
        self.assertTrue(ap.slips(row, 0))
        self.assertFalse(ap.scripted(GRATUITY).slip)
        self.assertTrue(ap.scripted(GRATUITY, task=row, run=0, slips_on=True).slip)

    def test_agent_turn_prints_the_turn(self):
        import agent_turn
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agent_turn.main(["--offline"]), 0)
        text = out.getvalue()
        for line in ("agent turn: pattern loop, desk astar, tenant acme", f"question: {GRATUITY}",
                     "model call 1 (thinking low): in ", '  -> retrieve(query="gratuity fifteen days wages for every '
                     'completed year of service")', "  -> gratuity_estimate(monthly_wage=52000, years=7, months=8)",
                     "= Rs 2,40,000: 7 years 8 months counts as 8 years", "  -> no tool: the answer",
                     "  Gratuity, an estimate: Rs 2,40,000 [2].", "  Worked out in code:",
                     "3 model calls (12 at most), 1 search, 1 calculation, 0 refused or failed tool calls; stopped by "
                     "nothing", "figure check: every figure in the model's text is a calculator's"):
            self.assertIn(line, text)
        self.assertRegex(text, r"Rs \d+\.\d{4} for the model calls at list price, Rs 0\.0000 for rag-api")
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(agent_turn.main(["--offline", "--json", "--thinking", "medium", "--desk", "statute"]), 0)
        record = json.loads(out.getvalue())
        self.assertEqual((record["desk"], record["thinking"], record["calculations"][0]["value"]), ("statute", "medium", 240000))
        with patch.dict(os.environ, {"RAG_API_URL": ""}), redirect_stderr(io.StringIO()) as err:
            self.assertEqual(agent_turn.main(["--live"]), 2)
        self.assertIn("--live needs", err.getvalue())
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(agent_turn.main(["--offline", "--pattern", "chain"]), 2)
        self.assertIn("no pattern 'chain'", err.getvalue())

    def test_agent_eval_offline_end_to_end(self):
        spec = importlib.util.spec_from_file_location("agent_eval_for_bench", KIT / "evals" / "agent_eval.py")
        ae = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ae)
        fd, saved = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        self.addCleanup(os.remove, saved)
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            self.assertEqual(ae.main(["--offline", "--slice", "trap,calc-gratuity-7y8m,refuse", "--runs", "2",
                                      "--best-of", "2", "--save", saved]), 0)
        text = out.getvalue()
        self.assertIn("== loop, thinking default (low), desk astar: 3 rows x 2 runs", text)
        self.assertRegex(text, r"trap-encash-cap +trap +2/2 +1/2 ")          # the first run copies the cap
        self.assertIn("no encashable_days call returned it", text)
        self.assertIn("best-of-2, chosen by the figure check alone: correct 3/3 = 100.0% [43.8%, 100.0%], verified 3/3",
                      text)
        self.assertIn("verified pass@2 1.000, pass^2 0.333", text)
        self.assertIn("(the script's tokens at list price: nothing is billed)", text)
        records = [json.loads(line) for line in Path(saved).read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(records), 6)
        self.assertNotIn("gs://", Path(saved).read_text(encoding="utf-8"))
        with redirect_stdout(io.StringIO()) as again:
            self.assertEqual(ae.main(["--replay", saved, "--best-of", "2"]), 0)
        table = (lambda t: [line for line in t.splitlines() if re.match(r"  (calc|trap|refuse)-", line)])
        self.assertEqual(table(again.getvalue()), table(text))                 # the same scores at Rs 0


if __name__ == "__main__":
    unittest.main()
