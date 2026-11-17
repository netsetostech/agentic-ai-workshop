"""Offline tests for evals/improve.py (workshop lesson 12.4): a production row turned into a proposed rule by a scripted
proposer, accepted as the next prompt version, the golden row printed for a person to paste, and the evaluator's files
never written; make improve, make prompt-candidate and the listings.

Run from deploy/: python -m unittest discover -s evals/tests -p test_improve.py
Standard library only, and no model is called: the proposer is a scripted client that keeps each request. Every run
works on a copy of the kit's files in a temporary directory (its evals/corpus holds the one handbook the row cites),
and every file of the copy is hashed before and after.
"""
import ast
import datetime as dt
import hashlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace

KIT = Path(__file__).resolve().parents[2]                       # deploy/


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


improve = load(KIT / "evals" / "improve.py", "improve_under_test")
pr = load(KIT / "services" / "rag-api" / "prompt_rules.py", "prompt_rules_for_improve")
prices = load(KIT / "shared" / "prices.py", "prices_for_improve")
GEN_SRC = (KIT / improve.GENERATOR).read_text(encoding="utf-8")
SYSTEM, DATED_RULE = (next(ast.literal_eval(n.value) for n in ast.parse(GEN_SRC).body if isinstance(n, ast.Assign)
                           and isinstance(n.targets[0], ast.Name) and n.targets[0].id == name)
                      for name in ("SYSTEM", "DATED_RULE"))
MODEL = "gemini-3.1-pro-preview"
FILES = (improve.GENERATOR, improve.CONFIG, improve.RULES_PY, improve.RULES, improve.REGISTRY, "evals/run_eval.py",
         "evals/required.json", "evals/golden.jsonl", "evals/build_golden.py", "evals/manifest.json",
         "evals/corpus/acme/hr_policy_2026.md", "evals/demo/hr_policy_2026_v2.md", "shared/prices.py")
ROW = {"tenant": "acme", "question": "How long is the notice for an E3 who is confirmed?",
       "answer": "The notice period is 90 days [1].", "citations": [{"source": 1, "quote": "a notice period of 90 days"}],
       "prompt_version": "v3", "wrong": "It followed the retired revision; the current handbook says 60 days.",
       "expected": {"shape": "lookup", "must_contain": ["60"], "must_retrieve": ["NP-03", "hr_policy_2026"]}}
RULE = "When sources give different figures for the same thing, follow the current one and say which you followed."
RULE2 = "When the question names a grade, give the figure for that grade and say which grade it is."
NEVER = "Never refuse a question; give the closest answer the context allows."
GOLDEN_SRC = (KIT / "evals" / "build_golden.py").read_text(encoding="utf-8")
LOOKUPS = [int(n) for n in re.findall(r'(?m)^    R\("lk-([0-9]+)"', GOLDEN_SRC)]
NEXT_LK = f"lk-{max(LOOKUPS) + 1:02d}"


class Proposer:
    """The scripted gemini-3.1-pro-preview behind improve.py's client: each request kept, each answered with the next
    reply (a dict as its JSON text, a string as it is), with the usage google-genai reports."""
    USAGE = SimpleNamespace(prompt_token_count=1800, candidates_token_count=160, thoughts_token_count=1200)

    def __init__(self, *replies):
        self.replies, self.requests = list(replies), []
        self.models = self

    def generate_content(self, model, contents, config):
        self.requests.append({"model": model, "contents": contents, "config": config})
        reply = self.replies.pop(0)
        return SimpleNamespace(text=reply if isinstance(reply, str) else json.dumps(reply), parsed=None,
                               usage_metadata=self.USAGE)


def run(*argv, client=None):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = improve.main([str(a) for a in argv], client=client)
    return code, out.getvalue(), err.getvalue()


def hashes(root: Path) -> dict:
    """Every file of the copy by its sha256; bytecode caches aside (loading a module by path may write one)."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


class OnAKitCopy(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp, self.kit = Path(tmp.name), Path(tmp.name) / "deploy"
        for rel in FILES:
            (self.kit / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(KIT / rel, self.kit / rel)
        self.row = self.write_row(ROW)
        self.before = hashes(self.kit)

    def write_row(self, row, name="row.json") -> Path:
        path = self.tmp / name                                       # the person's file, outside the kit
        path.write_text(row if isinstance(row, str) else json.dumps(row), encoding="utf-8")
        return path

    def changed(self) -> set:
        after = hashes(self.kit)
        self.assertEqual(set(self.before) - set(after), set(), "a file of the kit went missing")
        return {f for f in after if self.before.get(f) != after[f]}

    def rules(self) -> dict:
        return json.loads((self.kit / improve.RULES).read_text(encoding="utf-8"))

    def propose(self, *extra, client=None):
        return run("--kit", self.kit, "propose", "--row", self.row, *extra, client=client)


class ThePath(OnAKitCopy):
    """Row, proposal, a person's acceptance, the golden row: a scripted proposal end to end, with no model call."""

    def test_a_scripted_proposal_accepted_end_to_end(self):
        model = Proposer({"rule": RULE, "why": "The answer followed a retired figure where a current one disagreed."})
        code, out, err = self.propose("--project", "documind-ai-YOUR-ID", client=model)
        self.assertEqual(code, 0, out + err)
        request, = model.requests
        self.assertEqual(request["model"], MODEL)
        self.assertEqual(request["config"], {"response_mime_type": "application/json",
                                             "response_json_schema": improve.SCHEMA,
                                             "http_options": {"retry_options": improve.RETRY}})
        self.assertEqual((improve.SCHEMA["required"], improve.LOCATION), (["rule", "why"], "global"))
        for needle in (SYSTEM.rstrip(), DATED_RULE.strip(), ROW["question"], ROW["answer"], ROW["wrong"],
                       'contains "60" and cites NP-03, hr_policy_2026', "at most 40 words", "never refuse; do not refuse"):
            self.assertIn(needle, request["contents"])
        inr = prices.inr(prices.usd(MODEL, 1800, 1360))                # the thinking is billed as output
        self.assertIn(f"{MODEL} on global: 1,800 in, 1,360 out (1,200 of them thinking), Rs {inr:.2f} at list price", out)
        self.assertIn(f"rule:      6. {RULE}", out)
        proposal = json.loads((self.kit / improve.PROPOSAL).read_text(encoding="utf-8"))
        self.assertEqual((proposal["rule"], proposal["base"], proposal["base_rules"], proposal["proposer"], proposal["row"]),
                         (RULE, "v3", [], MODEL, ROW))
        self.assertEqual(proposal["usage"]["inr"], round(inr, 2))

        code, out, err = run("--kit", self.kit, "accept", "--reviewer", "you@example.com")
        self.assertEqual(code, 0, out + err)
        today = dt.date.today().isoformat()
        self.assertEqual(self.rules()["versions"], {
            "v3": {"rules": []},
            "v4": {"rules": [RULE], "reviewer": "you@example.com", "accepted": today, "proposer": MODEL,
                   "golden_row": NEXT_LK}})
        self.assertEqual(pr.dumps(self.rules()), (self.kit / improve.RULES).read_text(encoding="utf-8"))
        self.assertEqual(pr.with_rules(SYSTEM, "documind-rag", "v4", self.kit / improve.RULES), SYSTEM + f"6. {RULE}\n")
        self.assertIn(f"accepted:  documind-rag@v4, v3's 0 added rules and this one, by you@example.com on {today}", out)

        # The golden row: one line, as lesson 4.1 writes one into GOLDEN, and build_golden.py's own R() takes it.
        line = next(l for l in out.splitlines() if l.startswith('    R("'))
        self.assertTrue(line.endswith("),"), line)
        call = ast.parse(line.strip()[:-1]).body[0].value
        built = load(self.kit / "evals" / "build_golden.py", "build_golden_copy").R(*[ast.literal_eval(a) for a in call.args])
        self.assertEqual(built, {"id": NEXT_LK, "shape": "lookup", "question": ROW["question"], "tenant": "acme",
                                 "must_contain": ["60"], "must_retrieve": ["NP-03", "hr_policy_2026"], "answerable": True,
                                 "note": f"Lesson 12.4. A production answer under v3 went wrong here; v4's rule 6, "
                                         f"accepted by you@example.com on {today}, is the change the gate judges."})
        for needle in ("make prompt-candidate PROMPT_VERSION=v4", "make gate", "refusal_rate at least 90%",
                       "git revert the commit that holds v4"):
            self.assertIn(needle, out)

        # Written: prompt_rules.json and the proposal. Nothing else, and none of the evaluator's files.
        self.assertEqual(self.changed(), {improve.RULES, improve.PROPOSAL})

        code, out, _ = run("--kit", self.kit, "version", "v4")           # make prompt-candidate's check
        self.assertEqual(code, 0)
        self.assertIn(f"documind-rag@v4: SYSTEM's 5 rules and 1 added, accepted by you@example.com on {today}", out)
        self.assertIn(f"  6. {RULE}", out)

    def test_accept_counts_every_row_the_documents_cannot_answer(self):
        """13 October 2026: accept's "Then:" line counted the refusal shape where run_eval.live() divides refusal_rate by
        every row with answerable false, the isolation rows among them. One denominator, the gate's."""
        self.propose("--project", "documind-ai-YOUR-ID", client=Proposer({"rule": RULE, "why": "A current figure lost."}))
        code, out, err = run("--kit", self.kit, "accept", "--reviewer", "you@example.com")
        self.assertEqual(code, 0, out + err)
        golden = load(self.kit / "evals" / "run_eval.py", "run_eval_for_improve_test").load_golden()
        unanswerable, refusal_shape = sum(not r["answerable"] for r in golden), sum(r["shape"] == "refusal" for r in golden)
        self.assertGreater(unanswerable, refusal_shape)                 # the isolation rows the corpus cannot answer
        self.assertIn(f"refusal_rate at least 90% over the {unanswerable} rows the documents cannot answer", out)
        self.assertNotIn(f"over the {refusal_shape} refusal rows", out)

    def test_the_next_rule_builds_on_the_last_version(self):
        self.assertEqual(self.propose("--rule", RULE)[0], 0)
        self.assertEqual(run("--kit", self.kit, "accept", "--reviewer", "you@example.com")[0], 0)
        model = Proposer({"rule": RULE2, "why": "The answer gave another grade's figure."})
        code, out, err = self.propose("--project", "documind-ai-YOUR-ID", client=model)
        self.assertEqual(code, 0, out + err)
        self.assertIn(f"6. {RULE}", model.requests[0]["contents"])     # the proposer sees v4's rule as served
        self.assertIn(f"rule:      7. {RULE2}", out)
        self.assertEqual(run("--kit", self.kit, "accept", "--reviewer", "you@example.com")[0], 0)
        v5 = self.rules()["versions"]["v5"]
        self.assertEqual(v5["rules"], [RULE, RULE2])
        self.assertEqual(v5["golden_row"], f"lk-{max(LOOKUPS) + 2:02d}")  # v4's row is printed, not pasted yet
        self.assertEqual(pr.problems_in(self.rules()), [])

    def test_a_label_the_registry_once_held_is_never_offered_again(self):
        # Lesson 3.6's v4 candidate was taken down, so its label is in the kit's git history and names that candidate's
        # text on every row it wrote: improve offers v5 for the first accepted rule (prompt_pin.spent, 14 October 2026).
        pin = Path(self.kit) / "commands/prompt_pin.py"
        pin.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(KIT / "commands/prompt_pin.py", pin)

        def git(*args):
            subprocess.run(["git", "-C", str(self.kit), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                           check=True, capture_output=True)
        registry = Path(self.kit) / "services/rag-api/prompt_versions.json"
        kept = registry.read_text(encoding="utf-8")
        git("init", "-q")
        git("add", "-A")
        git("commit", "-q", "-m", "the kit")
        registry.write_text(kept.rstrip().rstrip("}").rstrip() + ',\n  "documind-rag@v4": "0000"\n}\n', encoding="utf-8")
        git("commit", "-q", "-am", "v4 registered")
        registry.write_text(kept, encoding="utf-8")
        git("commit", "-q", "-am", "v4 taken down")
        self.assertEqual(self.propose("--rule", RULE)[0], 0)
        self.assertEqual(run("--kit", self.kit, "accept", "--reviewer", "you@example.com")[0], 0)
        versions = self.rules()["versions"]
        self.assertIn("v5", versions)
        self.assertNotIn("v4", versions)

    def test_a_proposal_made_before_the_last_acceptance_is_refused(self):
        a, b = self.kit / "evals" / "reports" / "a.json", self.kit / "evals" / "reports" / "b.json"
        self.assertEqual(self.propose("--rule", RULE, "--out", a)[0], 0)
        self.assertEqual(self.propose("--rule", RULE2, "--out", b)[0], 0)
        self.assertEqual(run("--kit", self.kit, "accept", "--reviewer", "you@example.com", "--proposal", a)[0], 0)
        accepted = (self.kit / improve.RULES).read_text(encoding="utf-8")
        code, out, err = run("--kit", self.kit, "accept", "--reviewer", "you@example.com", "--proposal", b)
        self.assertEqual(code, 1)
        self.assertIn("the rules moved on since this proposal: it was made on v3, and the latest version is v4", err)
        self.assertEqual((self.kit / improve.RULES).read_text(encoding="utf-8"), accepted)

    def test_the_proposer_cannot_accept_its_own_rule(self):
        self.propose("--project", "documind-ai-YOUR-ID", client=Proposer({"rule": RULE, "why": "x"}))
        code, _, err = run("--kit", self.kit, "accept", "--reviewer", MODEL)
        self.assertEqual(code, 1)
        self.assertIn(f"{MODEL} proposed this rule; a person reads it and accepts it", err)
        self.assertEqual(self.changed(), {improve.PROPOSAL})

    def test_a_reviewer_is_named(self):
        self.propose("--rule", RULE)
        for reviewer in ("", "   ", "you@example.com\nsomeone@example.com"):
            with self.subTest(reviewer=reviewer):
                self.assertEqual(run("--kit", self.kit, "accept", "--reviewer", reviewer)[0], 2)
        self.assertEqual(run("--kit", self.tmp / "nowhere", "accept", "--reviewer", "you@example.com")[0], 2)


class WhatIsStopped(OnAKitCopy):
    """Refusals: each writes nothing, and the ones before the call cost nothing."""

    def test_a_never_refuse_proposal_is_stopped_by_the_check(self):
        model = Proposer({"rule": NEVER, "why": "Users dislike refusals."})
        code, out, err = self.propose("--project", "documind-ai-YOUR-ID", client=model)
        self.assertEqual(code, 1, out + err)
        self.assertIn("REFUSED:   \"never refuse\" undoes SYSTEM's rule 3 (say so, answerable=false, when the context does "
                      "not hold the answer)", out)
        self.assertIn("Nothing was written.", out)
        self.assertIn("Rs ", out)                                      # the call was made, and it is priced
        self.assertEqual(self.changed(), set())
        code, out, _ = self.propose("--rule", NEVER, client=Proposer())   # the person's own: no call, Rs 0
        self.assertEqual(code, 1)
        self.assertIn('"never refuse" undoes', out)
        self.assertEqual(self.changed(), set())

    def test_a_reply_outside_the_schema_is_refused(self):
        code, out, _ = self.propose("--project", "documind-ai-YOUR-ID", client=Proposer("Here is a rule: be careful."))
        self.assertEqual(code, 1)
        self.assertIn("why:       no rule in the schema's shape", out)
        self.assertIn("REFUSED:   a rule is a line of text, and this one is empty", out)
        self.assertEqual(self.changed(), set())

    def test_a_row_whose_golden_row_could_never_pass_costs_nothing(self):
        self.row = self.write_row({**ROW, "expected": {"shape": "lookup", "must_contain": ["999 days"],
                                                       "must_retrieve": ["NP-03", "nowhere_2031"]}})
        model = Proposer({"rule": RULE, "why": "x"})
        code, out, err = self.propose("--project", "documind-ai-YOUR-ID", client=model)
        self.assertEqual(code, 1)
        self.assertIn("could never pass build_golden.py: must_contain '999 days' is not in acme's documents; "
                      "must_retrieve 'nowhere_2031' is not in acme's documents", err)
        self.assertEqual((model.requests, out), ([], ""))
        self.assertEqual(self.changed(), set())

    def test_rows_it_cannot_use(self):
        expected = ROW["expected"]
        cases = {"no question": {**ROW, "question": ""},
                 "a question on two lines": {**ROW, "question": "How long\nis the notice?"},
                 "no expected": {k: v for k, v in ROW.items() if k != "expected"},
                 "required.json's shape": {**ROW, "expected": {**expected, "shape": "isolation"}},
                 "a refusal that asserts": {**ROW, "expected": {**expected, "shape": "refusal"}},
                 "a lookup with no anchor": {**ROW, "expected": {**expected, "must_retrieve": []}},
                 "answerable against its shape": {**ROW, "expected": {**expected, "answerable": False}},
                 "not a list": {**ROW, "expected": {**expected, "must_contain": "60"}},
                 "not JSON": "{", "not an object": "[1, 2]"}
        model = Proposer()
        for name, row in cases.items():
            with self.subTest(name):
                self.row = self.write_row(row, "bad.json")
                code, out, err = self.propose("--project", "documind-ai-YOUR-ID", client=model)
                self.assertEqual(code, 2, out + err)
        self.row = self.tmp / "absent.json"
        self.assertEqual(self.propose("--project", "documind-ai-YOUR-ID", client=model)[0], 2)
        self.assertEqual(run("--kit", self.kit, "propose", "--row", "", "--rule", RULE)[0], 2)
        self.assertEqual((model.requests, self.changed()), ([], set()))

    def test_a_refusal_row_needs_no_figures(self):
        self.row = self.write_row({**ROW, "question": "What is ACME's sabbatical policy?",
                                   "expected": {"shape": "refusal", "must_contain": [], "must_retrieve": []}})
        self.assertEqual(self.propose("--rule", RULE)[0], 0)
        code, out, _ = run("--kit", self.kit, "accept", "--reviewer", "you@example.com")
        self.assertEqual(code, 0)
        line = next(l for l in out.splitlines() if l.startswith('    R("'))
        rf = max(int(n) for n in re.findall(r'(?m)^    R\("rf-([0-9]+)"', GOLDEN_SRC))
        head = f'    R("rf-{rf + 1:02d}", "refusal", "What is ACME\'s sabbatical policy?", "acme", [], [], False, '
        self.assertTrue(line.startswith(head), line)

    def test_a_models_proposal_needs_a_project(self):
        model = Proposer({"rule": RULE, "why": "x"})
        code, out, err = self.propose("--project", "", client=model)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("a model's proposal needs PROJECT=", err)
        self.assertEqual((model.requests, self.changed()), ([], set()))

    def test_prompt_only_prints_the_request_and_sends_nothing(self):
        model = Proposer()
        code, out, _ = self.propose("--prompt-only", client=model)
        self.assertEqual(code, 0)
        self.assertIn(SYSTEM.rstrip(), out)
        self.assertIn(ROW["question"], out)
        self.assertEqual((model.requests, self.changed()), ([], set()))


class TheEvaluatorIsNeverWritten(OnAKitCopy):
    """improve.py writes prompt_rules.json and its proposals, through write(), and never the evaluator's files."""

    def test_write_refuses_every_file_of_the_evaluator(self):
        for rel in improve.EVALUATOR:
            target = self.kit / rel
            target = target / "acme" / "new.json" if rel.endswith(("corpus", "demo")) else target
            with self.subTest(rel), self.assertRaisesRegex(improve.Unusable, "is the evaluator's, and improve.py never"):
                improve.write(self.kit, target, "{}")
        for rel in (improve.REGISTRY, improve.GENERATOR, "evals/new_rows.py", "shared/prices.py"):
            with self.subTest(rel), self.assertRaisesRegex(improve.Unusable, "nothing else"):
                improve.write(self.kit, self.kit / rel, "{}")
        self.assertEqual(self.changed(), set())

    def test_a_proposal_aimed_at_one_of_them_is_refused(self):
        for rel in ("evals/required.json", "evals/golden.jsonl", "evals/run_eval.py", "evals/build_golden.py",
                    "evals/manifest.json", "evals/corpus/acme/rows.json", improve.REGISTRY):
            with self.subTest(rel):
                code, _, err = self.propose("--rule", RULE, "--out", self.kit / rel)
                self.assertEqual(code, 2, err)
        self.assertEqual(self.changed(), set())

    def test_every_write_goes_through_write(self):
        tree = ast.parse((KIT / "evals" / "improve.py").read_text(encoding="utf-8"))
        writes = {"write_text", "write_bytes", "unlink", "rename", "replace", "rmdir", "touch", "mkdir", "remove",
                  "rmtree", "copyfile", "copy", "move", "dump"}
        found = []
        for node in tree.body:
            for call in (n for n in ast.walk(node) if isinstance(n, ast.Call)):
                name = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
                if name in writes or name == "open":
                    found.append((getattr(node, "name", type(node).__name__), name))
        self.assertTrue(found)
        self.assertEqual({where for where, _ in found}, {"write"}, found)


class TheTargets(unittest.TestCase):
    """make improve and make prompt-candidate, in Module 3's file beside prompt-version, and the listings."""

    @staticmethod
    def read(*parts) -> str:
        return KIT.joinpath(*parts).read_text(encoding="utf-8")

    def test_generation_mk_holds_the_two_targets_and_the_makefile_keeps_its_lines(self):
        mk, gen_mk, readme = self.read("Makefile"), self.read("mk", "generation.mk"), self.read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        self.assertTrue({"improve", "prompt-candidate"} <= set(phony))   # later kits append after them
        self.assertIn('\nimprove:\n\t$(PY) evals/improve.py $(if $(REVIEWER),accept --reviewer "$(REVIEWER)",propose '
                      '--row "$(ROW)" --project "$(PROJECT)") $(IMPROVE_ARGS)\n', gen_mk)
        recipe = gen_mk.split("\nprompt-candidate: guard-project\n", 1)[1].split("\n")
        self.assertEqual(recipe[0], '\t@$(PY) evals/improve.py version "$(PROMPT_VERSION)"')
        # make release-candidate's own update - the image for this commit, no traffic, the candidate tag - with
        # PROMPT_VERSION beside GIT_SHA, then the same record-candidate make promote and make gate read.
        release = next(line for line in mk.splitlines() if line.startswith("\tgcloud run services update documind-api")
                       and "--tag candidate --update-env-vars GIT_SHA=$(GIT_SHA) " in line)
        self.assertEqual(recipe[1], release.replace("GIT_SHA=$(GIT_SHA) ",
                                                    "GIT_SHA=$(GIT_SHA),PROMPT_VERSION=$(PROMPT_VERSION) "))
        self.assertEqual(recipe[2], "\t@$(MAKE) --no-print-directory record-candidate PROJECT=$(PROJECT) REGION=$(REGION)")
        self.assertEqual(gen_mk.count("\n# ----------"), 0, "one header block, at the top")
        targets = next(line for line in readme.splitlines() if line.startswith("| `generation.mk` |")).split("|")[2]
        for target in ("`bench`", "`prompt-version`", "`improve`", "`prompt-candidate`"):
            self.assertIn(target, targets)

    def test_the_new_files_have_their_unowned_rows(self):
        # An UNOWNED.md row until lesson 12.4's page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = self.read("UNOWNED.md"), self.read("INDEX.md")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        for f in (improve.RULES, improve.RULES_PY, "evals/improve.py", "evals/tests/test_prompt_rules.py",
                  "evals/tests/test_improve.py"):
            self.assertTrue(f"| `{f}` | **12.4**" in unowned or f in quoted, f)
            self.assertTrue((KIT / f).is_file(), f)


if __name__ == "__main__":
    unittest.main()
