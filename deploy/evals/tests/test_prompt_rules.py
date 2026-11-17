"""Offline tests for services/rag-api/prompt_rules.py and prompt_rules.json, and generator.py's last two lines (workshop
lesson 12.4): the default prompt unchanged, the checks on a rule, append-only, which versions serve, and SYSTEM rebound
where every reader still sees what it saw.

Run from deploy/: python -m unittest discover -s evals/tests -p test_prompt_rules.py
Standard library only. prompt_rules.py is loaded by path; generator.py, config.py, cache_admin.py and
evals/make_trainset.py are read as text and by AST, never imported (generator.py builds a Gemini client at import).
Every changed rules file is a copy in a temporary directory: the kit's files are never written.
"""
import ast
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

KIT = Path(__file__).resolve().parents[2]                       # deploy/
API = KIT / "services" / "rag-api"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pr = load(API / "prompt_rules.py", "prompt_rules_under_test")
GEN_SRC = (API / "generator.py").read_text(encoding="utf-8")
GEN_TREE = ast.parse(GEN_SRC)


def strings(src: str, *names: str) -> list:
    """Module-level string constants, read by AST the way lesson B.5's build reads generator.py."""
    found = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(src).body
             if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in names}
    return [found[name] for name in names]


SYSTEM, DATED_RULE = strings(GEN_SRC, "SYSTEM", "DATED_RULE")
LINES = ('from prompt_rules import with_rules  # noqa: E402',
         'globals()["SYSTEM"] = with_rules(SYSTEM, settings.prompt_id, settings.prompt_version)')
GOOD = "When the question names a grade, give the figure for that grade and say which grade it is."
OTHER = "If two sources give different figures for the same thing, give both and cite each."


def rules_file(directory: str, versions: dict, name: str = "prompt_rules.json") -> Path:
    path = Path(directory) / name
    path.write_text(json.dumps({"versions": versions}), encoding="utf-8")
    return path


def registry_file(directory: str, labels) -> Path:
    path = Path(directory) / "prompt_versions.json"
    path.write_text(json.dumps({"versions": {label: "0" * 64 for label in labels}}), encoding="utf-8")
    return path


class TheDefaultChangesNothing(unittest.TestCase):
    """PROMPT_VERSION unset: config.py's v3, which adds no rules, so the prompt is the one served before."""

    def test_the_kit_lists_v3_and_its_default_version_adds_no_rules(self):
        doc = pr.load()
        self.assertEqual(doc["versions"]["v3"]["rules"], [])
        cfg = (API / "config.py").read_text(encoding="utf-8")
        default = re.search(r'^    prompt_version: str = "(v[0-9]+)"$', cfg, re.M).group(1)
        prompt_id = re.search(r'^    prompt_id: str = "([^"]+)"$', cfg, re.M).group(1)
        # So the text make prompt-version hashes (SYSTEM + DATED_RULE) is the text config.py's default serves.
        self.assertEqual(default, "v3")
        self.assertEqual(pr.rules_for(prompt_id, default), [])

    def test_the_default_prompt_is_the_tuning_sets_system_byte_for_byte(self):
        served = pr.with_rules(SYSTEM, "documind-rag", "v3")
        self.assertIs(served, SYSTEM)                                   # not rebuilt: the literal itself
        trainset, = strings((KIT / "evals" / "make_trainset.py").read_text(encoding="utf-8"), "SYSTEM")
        self.assertEqual(served, trainset)                             # lessons 12.1-12.3 trained behind it

    def test_the_kits_file_is_in_the_format_improve_writes(self):
        self.assertEqual(pr.dumps(pr.load()), pr.RULES.read_text(encoding="utf-8"))


class GeneratorsLastLines(unittest.TestCase):
    """The two lines generator.py ends with: SYSTEM rebound to the version's text, its literal left alone."""

    def test_two_lines_at_the_end_after_every_function(self):
        imp, assign = GEN_TREE.body[-2:]
        self.assertIsInstance(imp, ast.ImportFrom)
        self.assertIsInstance(assign, ast.Assign)
        self.assertEqual((ast.get_source_segment(GEN_SRC, imp) + "  # noqa: E402", ast.get_source_segment(GEN_SRC, assign)),
                         LINES)
        self.assertTrue(GEN_SRC.endswith("\n" + LINES[0] + "\n" + LINES[1] + "\n"))
        defs = [n for n in GEN_TREE.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        self.assertLess(max(n.end_lineno for n in defs), imp.lineno)   # outside every function a page quotes

    def test_SYSTEM_keeps_its_one_assignment(self):
        # make prompt-version, the page builds that read SYSTEM by AST (B.5, 2.3, 2.6, 3.4, 3.5, 3.9) and the lifters in
        # tools/check_retrieval.py and evals/tests/test_prompt_bench.py take the one module-level SYSTEM = <literal>;
        # the rebinding is written through globals(), a subscript, which none of them reads.
        named = [n for n in GEN_TREE.body if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign))
                 and any(isinstance(t, ast.Name) and t.id == "SYSTEM"
                         for t in (n.targets if isinstance(n, ast.Assign) else [n.target]))]
        self.assertEqual(len(named), 1)
        target = GEN_TREE.body[-1].targets[0]
        self.assertIsInstance(target, ast.Subscript)
        self.assertEqual(ast.unparse(target), "globals()['SYSTEM']")
        pin = load(KIT / "commands" / "prompt_pin.py", "prompt_pin_for_rules")
        self.assertEqual(pin.prompt_text(GEN_SRC), SYSTEM + DATED_RULE)

    def test_the_lines_run_as_the_service_runs_them(self):
        statements = ast.Module(body=GEN_TREE.body[-2:], type_ignores=[])
        code = compile(statements, str(API / "generator.py"), "exec")
        saved = sys.modules.get("prompt_rules"), pr.RULES
        sys.modules["prompt_rules"] = pr                                # what the service imports from /app
        try:
            with tempfile.TemporaryDirectory() as d:
                pr.RULES = rules_file(d, {"v3": {"rules": []}, "v4": {"rules": [GOOD]}})
                runs = {}
                for version in ("v3", "v4"):
                    ns = {"SYSTEM": SYSTEM, "settings": SimpleNamespace(prompt_id="documind-rag", prompt_version=version)}
                    exec(code, ns)
                    runs[version] = ns["SYSTEM"]
                self.assertIs(runs["v3"], SYSTEM)
                self.assertEqual(runs["v4"], SYSTEM + f"6. {GOOD}\n")
                ns = {"SYSTEM": SYSTEM, "settings": SimpleNamespace(prompt_id="documind-rag", prompt_version="v9")}
                with self.assertRaises(pr.RulesError):                  # the revision does not start
                    exec(code, ns)
        finally:
            pr.RULES = saved[1]
            if saved[0] is None:
                sys.modules.pop("prompt_rules", None)
            else:
                sys.modules["prompt_rules"] = saved[0]

    def test_every_reader_of_SYSTEM_reads_it_when_it_runs(self):
        # Each reads the module's SYSTEM inside a function body, after the import that rebinds it: none holds the
        # literal in a default, a decorator or a module-level copy.
        readers, elsewhere = set(), []
        for node in GEN_TREE.body[:-1]:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inside = {id(n) for stmt in node.body for n in ast.walk(stmt)}
                for n in ast.walk(node):
                    if isinstance(n, ast.Name) and n.id == "SYSTEM":
                        (readers.add(node.name) if id(n) in inside else elsewhere.append(node.name))
            else:
                elsewhere += [type(node).__name__ for n in ast.walk(node) if isinstance(n, ast.Name) and n.id == "SYSTEM"
                              and isinstance(n.ctx, ast.Load)]
        self.assertEqual(elsewhere, [])
        self.assertTrue({"generate", "generate_stream", "_budget", "_gateway_messages"} <= readers, readers)
        admin = ast.parse((API / "cache_admin.py").read_text(encoding="utf-8"))
        top = [n for n in admin.body if isinstance(n, ast.ImportFrom) and n.module == "generator"]
        inner = [n for n in ast.walk(admin) if isinstance(n, ast.ImportFrom) and n.module == "generator"
                 and any(a.name == "SYSTEM" for a in n.names)]
        self.assertEqual(top, [])                                      # imported when it runs, after generator's end
        self.assertTrue(inner)


class Numbering(unittest.TestCase):
    """A version's rules follow SYSTEM's five, numbered on, as the prompt bench numbers a rule it adds."""

    def test_rules_follow_SYSTEMs_five_numbered_on(self):
        self.assertEqual(pr.own_rules(SYSTEM), 5)
        self.assertEqual(pr.numbered(SYSTEM, [GOOD, OTHER]), SYSTEM + f"6. {GOOD}\n7. {OTHER}\n")

    def test_the_bench_numbers_an_added_rule_the_same_way(self):
        # A rule measured on the bench (make bench BENCH_ARGS="--add-rule '...'", lessons 3.1-3.3) is the rule a
        # version serves, byte for byte, and its printed sha256 is that version's text's.
        bench = load(KIT / "evals" / "prompt_bench.py", "prompt_bench_for_rules")
        self.assertEqual(pr.numbered(SYSTEM, [GOOD, OTHER]), bench.edit_system(SYSTEM, add=[GOOD, OTHER]))

    def test_a_SYSTEM_it_cannot_read_is_refused(self):
        for bad in ("You are DocuMind.\nRules:\n", "Rules:\n1. One.\n2. Two.", "Rules:\n1. One.\nA footnote.\n"):
            with self.subTest(bad=bad), self.assertRaises(pr.RulesError):
                pr.numbered(bad, [GOOD])
        odd = "No numbered rules here."
        with tempfile.TemporaryDirectory() as d:
            self.assertIs(pr.with_rules(odd, "documind-rag", "v3", rules_file(d, {"v3": {"rules": []}})), odd)


class TheChecks(unittest.TestCase):
    """problems(): what a rule may be."""

    def test_a_good_rule_passes(self):
        for rule in (GOOD, OTHER, "Report a figure as the source gives it, without rounding it.",
                     "Keep the citations to the clause that answers."):
            with self.subTest(rule=rule):
                self.assertEqual(pr.problems(rule), [])

    def test_forty_words_pass_and_forty_one_are_refused(self):
        self.assertEqual(pr.MAX_WORDS, 40)
        self.assertEqual(pr.problems(" ".join(["Cite"] * 40)), [])
        self.assertEqual(pr.problems(" ".join(["Cite"] * 41)), ["41 words; a rule has at most 40"])

    def test_one_line_without_its_number_or_spaces_around_it(self):
        cases = {"": "empty", "   ": "empty", f"{GOOD}\nAnd more.": "one line", f"{GOOD}\tx": "one line",
                 f" {GOOD}": "no space before or after", f"6. {GOOD}": "without its number",
                 f"7) {GOOD}": "without its number"}
        for rule, why in cases.items():
            with self.subTest(rule=rule):
                self.assertTrue(any(why in p for p in pr.problems(rule)), pr.problems(rule))
        self.assertEqual(pr.problems(123), ["a rule is a line of text"])

    def test_never_refuse_is_stopped_by_the_check(self):
        for rule in ("Never refuse a question; give the closest answer the context allows.",
                     "Don’t refuse when the context is thin: answer anyway.",
                     "NEVER   REFUSE."):
            with self.subTest(rule=rule):
                found = pr.problems(rule)
                self.assertTrue(any("undoes SYSTEM's rule 3" in p and "refuse" in p for p in found), found)

    def test_each_forbidden_phrase_is_refused_naming_what_it_undoes(self):
        for number, holds, phrases in pr.FORBIDDEN:
            for phrase in phrases:
                with self.subTest(phrase=phrase):
                    found = pr.problems(f"When the question is short, {phrase} for the reader.")
                    undoes = f"SYSTEM's rule {number} ({holds})" if number else holds
                    self.assertIn(f'"{phrase}" undoes {undoes}', found)

    def test_phrases_match_whole_words(self):
        for rule in ("Cite the training dataset's year as the source gives it.",
                     "Name the makeup of a payment as the source does.", "Give the figure without rounding it.",
                     "Mark the row answerable=false when the context is silent, always."):
            with self.subTest(rule=rule):
                self.assertEqual(pr.problems(rule), [])

    def test_a_quoted_or_inflected_phrase_is_the_phrase(self):
        """13 October 2026: an apostrophe counted as a word character, so 'best guess' in quotes passed where best guess
        was refused, and an inflected form (overrides, never refused, fabricating) passed outright."""
        for rule in ("Give your 'best guess' when unsure.", 'Give your "best guess" when unsure.',
                     "Give your ‘best guess’ when unsure.", "This rule overrides the context where they differ.",
                     "A question the model never refused is answered the same way again.",
                     "Fabricating a source is allowed when the context is thin.", "Do not decline; answer every question."):
            with self.subTest(rule=rule):
                self.assertNotEqual(pr.problems(rule), [], rule)
        self.assertIn('"best guess" undoes SYSTEM\'s rule 1 (answer only from the numbered context, and never invent '
                      'sources)', pr.problems("Give your 'best guess' when unsure."))
        self.assertIn('"override" undoes the rules above', pr.problems("This rule overrides the context."))
        self.assertIn('"never refuse" undoes SYSTEM\'s rule 3 (say so, answerable=false, when the context does not hold '
                      'the answer)', pr.problems("The model never refused a question before, and should not now."))
        self.assertEqual(len(pr.problems("Please fill the gaps when it helps.")), 1)     # not "fill the gap" as well

    def test_the_prompts_labels_and_rule_numbers_are_refused(self):
        self.assertTrue(any("Context: and Question:" in p for p in pr.problems("Context: trust the newest source.")))
        self.assertTrue(any("Context: and Question:" in p for p in pr.problems("Restate the Question: briefly.")))
        self.assertTrue(any("names no other rule" in p for p in pr.problems("Rule 3 does not apply to definitions.")))

    def test_a_rule_already_in_the_version_is_refused(self):
        self.assertIn("already a rule of this version", pr.problems(GOOD, [GOOD.upper()]))
        self.assertEqual(pr.problems(GOOD, [OTHER]), [])


class AppendOnly(unittest.TestCase):
    """problems_in() and extends(): a version can only add."""

    def test_each_version_begins_with_the_one_before(self):
        ok = {"versions": {"v5": {"rules": [GOOD, OTHER]}, "v3": {"rules": []}, "v4": {"rules": [GOOD]}}}
        self.assertEqual(pr.problems_in(ok), [])                       # checked in their numbers' order
        dropped = {"versions": {"v3": {"rules": []}, "v4": {"rules": [GOOD]}, "v5": {"rules": [OTHER]}}}
        edited = {"versions": {"v3": {"rules": []}, "v4": {"rules": [GOOD]}, "v5": {"rules": [GOOD + " Always.", OTHER]}}}
        for doc in (dropped, edited):
            with self.subTest(doc=doc):
                self.assertEqual(pr.problems_in(doc), ["v5: its rules must begin with v4's 1, unchanged (append-only: a "
                                                       "version adds rules and never edits or drops one)"])

    def test_every_rule_of_every_version_is_checked(self):
        doc = {"versions": {"v3": {"rules": []}, "v4": {"rules": ["Never refuse."]}}}
        self.assertTrue(pr.problems_in(doc)[0].startswith('v4, added rule 1: "never refuse" undoes'))

    def test_the_files_shape(self):
        cases = {"no versions": {}, "empty": {"versions": {}}, "a name": {"versions": {"V4": {"rules": []}}},
                 "a leading zero": {"versions": {"v04": {"rules": []}}}, "no list": {"versions": {"v3": {"rules": "x"}}},
                 "not text": {"versions": {"v3": {"rules": [3]}}}, "no object": {"versions": {"v3": []}}}
        for name, doc in cases.items():
            with self.subTest(name):
                self.assertTrue(pr.problems_in(doc))
        with tempfile.TemporaryDirectory() as d:
            twice = Path(d) / "prompt_rules.json"
            twice.write_text('{"versions": {"v3": {"rules": []}, "v3": {"rules": ["x"]}}}', encoding="utf-8")
            with self.assertRaisesRegex(pr.RulesError, "v3 written twice"):
                pr.load(twice)
            garbage = Path(d) / "garbage.json"
            garbage.write_text("{not json", encoding="utf-8")
            with self.assertRaisesRegex(pr.RulesError, "^garbage.json: not JSON"):
                pr.load(garbage)
            bad = rules_file(d, {"v3": {"rules": []}, "v4": {"rules": ["Never refuse."]}})
            with self.assertRaisesRegex(pr.RulesError, r"^prompt_rules\.json: v4, added rule 1"):
                pr.load(bad)

    def test_extends_refuses_a_dropped_or_edited_version(self):
        old = {"versions": {"v3": {"rules": []}, "v4": {"rules": [GOOD], "reviewer": "you@example.com"}}}
        self.assertEqual(pr.extends(old, {"versions": {**old["versions"], "v5": {"rules": [GOOD, OTHER]}}}), [])
        self.assertEqual(pr.extends(old, {"versions": {"v3": {"rules": []}}}),
                         ["v4: dropped; a version stays once it is written"])
        edited = {"versions": {"v3": {"rules": []}, "v4": {"rules": [GOOD], "reviewer": "someone@example.com"}}}
        self.assertEqual(pr.extends(old, edited),
                         ["v4: changed; a version is never edited, and a new rule is a new version"])


class WhichVersionsServe(unittest.TestCase):
    """rules_for(): a listed version's rules, none for one lesson 3.6 registered, and a refusal for any other."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.rules = rules_file(self.dir.name, {"v3": {"rules": []}, "v4": {"rules": [GOOD]}})

    def test_a_listed_version_serves_its_rules(self):
        self.assertEqual(pr.rules_for("documind-rag", "v4", self.rules), [GOOD])
        self.assertEqual(pr.with_rules(SYSTEM, "documind-rag", "v4", self.rules), SYSTEM + f"6. {GOOD}\n")

    def test_a_version_lesson_36_registered_adds_nothing(self):
        # Lesson 3.6's v4 edits SYSTEM itself and registers its text's sha256; prompt_rules.json need not list it.
        rules = rules_file(self.dir.name, {"v3": {"rules": []}}, "only_v3.json")
        registry = registry_file(self.dir.name, ["documind-rag@v3", "documind-rag@v4"])
        edited = SYSTEM.replace("never a whole section.", "never a whole clause.")
        self.assertIs(pr.with_rules(edited, "documind-rag", "v4", rules, registry), edited)

    def test_any_other_version_is_refused(self):
        registry = registry_file(self.dir.name, ["documind-rag@v3", "other-prompt@v7"])
        for version in ("v7", "v44", "4"):
            with self.subTest(version=version), self.assertRaises(pr.RulesError) as caught:
                pr.with_rules(SYSTEM, "documind-rag", version, self.rules, registry)
            message = str(caught.exception)
            for needle in (f"PROMPT_VERSION={version!r}", "prompt_rules.json lists v3, v4", "prompt_versions.json",
                           f"documind-rag@{version}", "would answer with SYSTEM alone"):
                self.assertIn(needle, message)

    def test_the_registry_is_read_only_for_a_version_not_listed(self):
        missing = Path(self.dir.name) / "absent.json"
        self.assertEqual(pr.rules_for("documind-rag", "v3", self.rules, missing), [])
        with self.assertRaisesRegex(pr.RulesError, r"PROMPT_VERSION='v5': prompt_rules\.json does not list it, and "
                                                   r"absent\.json: cannot read it"):
            pr.rules_for("documind-rag", "v5", self.rules, missing)

    def test_the_kits_registry_holds_v3(self):
        self.assertIn("documind-rag@v3", pr.registered())


class TheImage(unittest.TestCase):
    """The rules travel in the rag-api image, beside generator.py, and need nothing the image lacks."""

    def test_the_image_copies_the_rules_beside_the_generator(self):
        dockerfile = (API / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY --chown=app:app services/rag-api/ ./", dockerfile)
        for name in ("prompt_rules.py", "prompt_rules.json", "prompt_versions.json", "generator.py"):
            self.assertTrue((API / name).is_file(), name)

    def test_prompt_rules_imports_the_standard_library_only(self):
        tree = ast.parse((API / "prompt_rules.py").read_text(encoding="utf-8"))
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(imported, {"__future__", "json", "re", "pathlib"})


if __name__ == "__main__":
    unittest.main()
