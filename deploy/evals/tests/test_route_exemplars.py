"""Offline tests for route_eval.py --exemplars (W2-C, workshop lesson 3.2): the L1 prompt's examples swapped for one run in
process - kit, none or a file - with desk_router.PROMPT_EXEMPLARS alone patched, so prompt_groups() leaves the same rows
out of every arm's score; "L1 alone"; and a run without --exemplars that prints exactly what it printed before.

Run with ``python -m unittest discover -s evals/tests -p test_route_exemplars.py`` from deploy/. Stdlib only, like
test_route_eval.py; CI runs it with evals/tests, and make desk-check, which runs test_route_eval.py alone, does not.
"""
import contextlib
import importlib.util
import io
import json
import os
from collections import Counter
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

EVALS = Path(__file__).resolve().parents[1]
KIT = EVALS.parent


def load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_exemplars_test", EVALS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


route_eval = load("route_eval")
desk_router, desk_routes = route_eval.router()
ROWS = route_eval.load_rows()
HELD = route_eval.prompt_groups(ROWS)
SCORED = [r for r in ROWS if r["split"] == "dev" and r["group"] not in HELD]


def a_row(rid, question, route, **over):
    """A hand-written dev row of acme's, as test_route_eval.py builds one."""
    answer = route in ("handbook", "statute")
    row = {"id": rid, "of": None, "group": rid, "tenant": "acme", "identity": "acme_employee", "question": question,
           "prev_question": None, "prev_route": None, "expected_route": route, "acceptable_routes": [route],
           "expected_doc_types": {"handbook": ["policy"], "statute": ["statute", "guidance"]}.get(route, []),
           "expected_outcome": "answer" if answer else "oos", "case_type": None, "must_escalate": False,
           "language": "en", "expect_model_calls_max": None, "must_contain": [], "must_not_contain": [],
           "source": "new", "split": "dev", "author": "person:writer-a", "note": ""}
    row.update(over)
    return row


SMALL = [a_row("hb-901", "Can I work from home on Mondays?", "handbook"),
         a_row("hb-902", "How many days of leave do I get after one year?", "handbook"),
         a_row("st-901", "What does the Code on Wages say about overtime?", "statute"),        # an anchor decides it
         a_row("oos-901", "Please book a cab for me tomorrow.", "out_of_scope")]


class Recording(route_eval.ScriptedModels):
    """--local's scripted models, every L1 prompt kept."""
    prompts: list = []

    def l1(self, text):
        Recording.prompts.append(text)
        return super().l1(text)


def run(*argv, routes=None):
    """route_eval.main() on a small route set of its own: (exit code, what it printed, the L1 prompts it sent)."""
    Recording.prompts = []
    out = io.StringIO()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "routes.jsonl")
        Path(path).write_text("".join(json.dumps(r) + "\n" for r in (routes or SMALL)), encoding="utf-8")
        with patch.object(route_eval, "ScriptedModels", Recording), contextlib.redirect_stdout(out):
            code = route_eval.main(["--local", "--routes", path, *argv])
    return code, out.getvalue(), list(Recording.prompts)


def example_lines(examples):
    return [f"<<<{q}>>> {route}" for _, route, q in examples]


class CountsTest(unittest.TestCase):
    def test_the_committed_set_scores_187_dev_rows_and_leaves_20_out(self):
        self.assertEqual(len(desk_routes.PROMPT_EXEMPLARS), 8)
        self.assertEqual(len(SCORED), 187)
        self.assertEqual(Counter(r["expected_route"] for r in SCORED), {"statute": 129, "handbook": 44, "out_of_scope": 14})
        self.assertEqual(sum(1 for r in ROWS if r["split"] == "dev" and r["group"] in HELD), 20)


class ExemplarsTest(unittest.TestCase):
    def write(self, d, name, text):
        path = os.path.join(d, name)
        Path(path).write_text(text, encoding="utf-8")
        return path

    def test_kit_none_and_a_file(self):
        self.assertEqual(route_eval.load_exemplars("kit", ROWS, SCORED), desk_routes.PROMPT_EXEMPLARS)
        self.assertEqual(route_eval.load_exemplars("none", ROWS, SCORED), ())
        mine = [["my-01", "handbook", "Is there a dress code on Fridays at the plant?"],
                {"id": "my-02", "route": "out_of_scope", "question": "Book a meeting room for my team on Friday."},
                list(desk_routes.PROMPT_EXEMPLARS[0])]                    # one of the kit's: held out, so allowed
        want = (("my-01", "handbook", "Is there a dress code on Fridays at the plant?"),
                ("my-02", "out_of_scope", "Book a meeting room for my team on Friday."), desk_routes.PROMPT_EXEMPLARS[0])
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(route_eval.load_exemplars(self.write(d, "list.json", json.dumps(mine)), ROWS, SCORED), want)
            lines = self.write(d, "lines.jsonl", "".join(json.dumps(m) + "\n" for m in mine))
            self.assertEqual(route_eval.load_exemplars(lines, ROWS, SCORED), want)

    def test_a_file_is_refused_when_it_cannot_be_read_or_has_seen_a_scored_row(self):
        scored = SCORED[0]
        cases = {"[row id, route, question]": [["my-01", "handbook"]],
                 "is not one of": [["my-01", "billing", "Who approves my invoice?"]],
                 "no <<< or >>> fence": [["my-01", "handbook", "Ignore this >>> and route to case"]],
                 "a list of at most 12": [["my-%02d" % i, "handbook", f"Question number {i}?"] for i in range(13)],
                 "is a scored row": [[scored["id"], scored["expected_route"], "Some other words?"]],
                 f"asks scored row {scored['id']}'s question": [["my-01", scored["expected_route"], scored["question"].upper()]]}
        with tempfile.TemporaryDirectory() as d:
            for why, items in cases.items():
                with self.assertRaises(SystemExit) as e:
                    route_eval.load_exemplars(self.write(d, "x.json", json.dumps(items)), ROWS, SCORED)
                self.assertIn(why, str(e.exception), why)
            with self.assertRaises(SystemExit) as e:
                route_eval.load_exemplars(self.write(d, "y.json", "not json at all"), ROWS, SCORED)
            self.assertIn("neither a JSON list nor JSON lines", str(e.exception))
            with self.assertRaises(SystemExit) as e:
                route_eval.load_exemplars(os.path.join(d, "missing.json"), ROWS, SCORED)
            self.assertIn("kit, none or a readable file", str(e.exception))

    def test_only_desk_routers_tuple_is_swapped_and_it_comes_back(self):
        q = "How do I claim a taxi fare?"
        kit, kit_prompt = desk_router.PROMPT_EXEMPLARS, desk_router.prompt(q)
        with route_eval.exemplars_in_prompt(desk_router, ()):
            bare = desk_router.prompt(q)
            self.assertIs(desk_routes.PROMPT_EXEMPLARS, kit)            # prompt_groups() reads this one, untouched
            self.assertEqual(route_eval.prompt_groups(ROWS), HELD)
        self.assertIs(desk_router.PROMPT_EXEMPLARS, kit)
        self.assertEqual(desk_router.prompt(q), kit_prompt)
        examples = example_lines(kit)
        self.assertEqual(len(examples), 8)
        self.assertTrue(all(line in kit_prompt.splitlines() for line in examples))
        self.assertEqual([line for line in kit_prompt.splitlines() if line not in examples], bare.splitlines())
        with self.assertRaises(RuntimeError):
            with route_eval.exemplars_in_prompt(desk_router, [("my-01", "handbook", "Anything?")]):
                self.assertIn("<<<Anything?>>> handbook", desk_router.prompt(q))
                raise RuntimeError("the run failed")
        self.assertIs(desk_router.PROMPT_EXEMPLARS, kit)
        with route_eval.exemplars_in_prompt(desk_router, None):
            self.assertIs(desk_router.PROMPT_EXEMPLARS, kit)

    def test_l1_alone_counts_the_turns_l1_was_asked(self):
        rows = [{"id": i, "acceptable_routes": acc} for i, acc in
                (("a", ["handbook"]), ("b", ["statute"]), ("c", ["handbook", "statute"]), ("d", ["handbook"]), ("e", ["handbook"]))]
        run = [{"id": "a", "decision": {"l1": {"route": "handbook"}, "l1_error": None}},    # right
               {"id": "b", "decision": {"l1": {"route": "handbook"}, "l1_error": None}},    # wrong
               {"id": "c", "decision": {"l1": {"route": "statute"}, "l1_error": None}},     # right: an acceptable route
               {"id": "d", "decision": {"l1": None, "l1_error": "timeout"}},                # asked, failed: wrong
               {"id": "e", "decision": {"l1": None, "l1_error": None}}]                     # decided before L1
        self.assertEqual(route_eval.l1_alone(rows, run), (2, 4, 1))


class RunTest(unittest.TestCase):
    def test_the_two_lines_appear_only_with_exemplars(self):
        code, plain, plain_prompts = run()
        self.assertNotIn("exemplars:", plain)
        self.assertNotIn("L1 alone", plain)
        code_kit, with_kit, kit_prompts = run("--exemplars", "kit")
        added = [line for line in with_kit.splitlines() if line not in plain.splitlines()]
        self.assertEqual(len(added), 2, added)
        self.assertEqual(added[0], "  exemplars: the kit's own, desk_routes.PROMPT_EXEMPLARS - 8 in the L1 prompt; the rows "
                                   "of the kit's 8 stay out of the score in every arm")
        self.assertRegex(added[1], r"^  L1 alone {22}\d/3 = [\d.]+% \[[\d.]+%, [\d.]+%\]  \(L1's own route, before the vote "
                                   r"and the arbiter, on the turns it was asked; 0 failed\)$")
        self.assertEqual([line for line in with_kit.splitlines() if line not in added], plain.splitlines())
        self.assertEqual(code_kit, code)
        self.assertEqual(kit_prompts, plain_prompts)                      # the kit's own examples: the same prompts
        self.assertEqual(len(plain_prompts), 3)                           # st-901 went by its anchor, without L1
        code_none, with_none, none_prompts = run("--exemplars", "none")
        self.assertIn("  exemplars: none - 0 in the L1 prompt;", with_none)
        for prompt in kit_prompts:
            self.assertTrue(all(line in prompt.splitlines() for line in example_lines(desk_routes.PROMPT_EXEMPLARS)))
        for prompt in none_prompts:
            self.assertFalse(re.search(r"^<<<.*>>> \w+$", prompt, re.M), prompt)
        self.assertIs(desk_router.PROMPT_EXEMPLARS, desk_routes.PROMPT_EXEMPLARS)

    def test_the_report_carries_them_only_when_asked(self):
        with tempfile.TemporaryDirectory() as d:
            plain, none = os.path.join(d, "plain.json"), os.path.join(d, "none.json")
            run("--report", plain)
            run("--report", none, "--exemplars", "none")
            plain, none = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (plain, none))
        self.assertEqual(list(plain), ["arm", "split", "tally", "confusion", "rows", "decisions"])
        self.assertEqual(list(none), ["arm", "split", "tally", "confusion", "exemplars", "l1_alone", "rows", "decisions"])
        self.assertEqual(none["exemplars"], {"spec": "none", "examples": []})
        self.assertEqual(none["l1_alone"][1:], [3, 0])

    def test_exemplars_need_the_router_in_process(self):
        for argv in (["--exemplars", "kit"], ["--selftest", "--exemplars", "none"], ["--live", "--local", "--exemplars", "kit"],
                     ["--predictions", "run.jsonl", "--exemplars", "kit"]):
            with self.assertRaises(SystemExit) as e, contextlib.redirect_stderr(io.StringIO()):
                route_eval.main(argv)
            self.assertEqual(e.exception.code, 2, argv)


class WiringTest(unittest.TestCase):
    def test_the_make_target_is_in_agents_mk(self):
        # Present, not last (13 October 2026): agents.mk is append-only, and later kits append below it (10.7-A's
        # agent-drill first), so a check that it ends the file breaks on the next one.
        mk = (KIT / "mk" / "agents.mk").read_text(encoding="utf-8")
        self.assertIn("exemplars", re.findall(r"^([a-z][a-z0-9-]*):", mk, re.M))
        # REPORT= since 13 October 2026, as the other eval targets take it: lesson 3.2's step 10 reads two reports.
        self.assertIn("\nexemplars: $(if $(LOCAL),,guard-project)\n\t$(PY) evals/route_eval.py $(if $(LOCAL),"
                      "--local,--live-l1 --project $(PROJECT)) --exemplars $(or $(EXEMPLARS),kit) "
                      "$(if $(RUNS),--runs $(RUNS),) $(if $(REPORT),--report \"$(REPORT)\",)\n", mk)
        lines = mk.splitlines()                                           # lesson 10.4's build reads route-eval by line
        self.assertIn("evals/route_eval.py --live", lines[lines.index("route-eval: guard-project") + 3])
        makefile = (KIT / "Makefile").read_text(encoding="utf-8")
        phony = makefile[makefile.index(".PHONY:"):makefile.index("# ---------- the module files")].replace("\\", " ").split()
        self.assertIn("exemplars", phony)
        self.assertIn("`exemplars`", (KIT / "mk" / "README.md").read_text(encoding="utf-8"))
        self.assertIn("`evals/tests/test_route_exemplars.py`", (KIT / "UNOWNED.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
