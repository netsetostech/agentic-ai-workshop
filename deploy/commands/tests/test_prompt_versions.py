"""Offline tests for commands/prompt_pin.py and services/rag-api/prompt_versions.json (workshop lesson 3.6).

Run from deploy/: python -m unittest discover -s commands/tests -p test_prompt_versions.py
Standard library only. generator.py, config.py and make_trainset.py are read as text and by AST, never imported. Every
changed prompt below is an edited copy in a temporary directory, made from the kit's own files with documind-rag@v3
registered to their text: the kit's files are never written, and a later version that follows the rule passes too.
"""
import ast
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

KIT = Path(__file__).resolve().parents[2]                       # deploy/
spec = importlib.util.spec_from_file_location("prompt_pin", KIT / "commands" / "prompt_pin.py")
prompt_pin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompt_pin)

GEN, CFG, REG = prompt_pin.GENERATOR, prompt_pin.CONFIG, prompt_pin.REGISTRY
# documind-rag@v3's sha256, registered on 8 October 2026. A registered version never changes its sha256: a changed
# prompt is a new version beside it, so this stays true for as long as the registry keeps v3's line.
V3 = "543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e"


def extended(sentence: str):
    """A change to SYSTEM: its last rule gains a sentence."""
    return lambda system: system.rstrip("\n") + " " + sentence + "\n"


def strings(path: Path, *names: str) -> list:
    """Module-level string constants, read by AST the way lesson B.5's build reads generator.py."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
             if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in names}
    return [found[name] for name in names]


def sha(path: Path) -> str:
    """The sha256 of SYSTEM + DATED_RULE in this generator.py, computed here rather than by prompt_pin."""
    system, dated = strings(path, "SYSTEM", "DATED_RULE")
    return hashlib.sha256((system + dated).encode("utf-8")).hexdigest()


def with_value(source: str, name: str, change) -> str:
    """source with the string assigned to `name` replaced by change(the string), written as a double-quoted literal:
    the statement is found by AST, so the edit follows the code rather than today's wording."""
    stmt = next(n for n in ast.walk(ast.parse(source)) if isinstance(n, (ast.Assign, ast.AnnAssign))
                and name in [t.id for t in (n.targets if isinstance(n, ast.Assign) else [n.target]) if isinstance(t, ast.Name)])
    old = ast.get_source_segment(source, stmt)
    new = old.replace(ast.get_source_segment(source, stmt.value), json.dumps(change(ast.literal_eval(stmt.value))), 1)
    return source.replace(old, new, 1)


BASE = sha(KIT / GEN)                                            # the kit's text, registered as v3 in every copy


class PromptVersionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="prompt_pin_")
        self.addCleanup(tmp.cleanup)
        self.tmp, self.copies = Path(tmp.name), 0

    def copy(self, system=None, dated=None, version="v3", versions=None, registry=None, gen=None, cfg=None) -> Path:
        """The three files prompt_pin reads, under a fresh temporary kit: gen and cfg an (old, new) edit of the source,
        SYSTEM and DATED_RULE changed by the given functions, prompt_version set to `version` (None: left alone), and
        the registry holding `versions` (by default v3, registered to the kit's own text) or the whole text `registry`."""
        self.copies += 1
        kit = self.tmp / f"kit{self.copies}"
        texts = {rel: (KIT / rel).read_text(encoding="utf-8") for rel in (GEN, CFG)}
        for rel, edit in ((GEN, gen), (CFG, cfg)):
            if edit:
                self.assertIn(edit[0], texts[rel])
                texts[rel] = texts[rel].replace(*edit)
        for name, change in (("SYSTEM", system), ("DATED_RULE", dated)):
            if change:
                texts[GEN] = with_value(texts[GEN], name, change)
        if version is not None:
            texts[CFG] = with_value(texts[CFG], "prompt_version", lambda _: version)
        texts[REG] = registry if registry is not None else json.dumps(
            {"versions": versions or {"documind-rag@v3": BASE}}, indent=2) + "\n"
        for rel, text in texts.items():
            (kit / rel).parent.mkdir(parents=True, exist_ok=True)
            with open(kit / rel, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        return kit

    def pin(self, kit: Path = KIT) -> tuple:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = prompt_pin.main(["--kit", str(kit)])
        return code, out.getvalue(), err.getvalue()

    def test_the_registry_matches_todays_prompt(self):
        cfg = (KIT / CFG).read_text(encoding="utf-8")
        label = "@".join(re.search(rf'^    {field}: str = (?:Field\()?"([^"]+)"', cfg, re.M).group(1)
                         for field in ("prompt_id", "prompt_version"))
        versions = json.loads((KIT / REG).read_text(encoding="utf-8"))["versions"]
        self.assertEqual(versions[label], BASE)                  # the label config.py serves under: today's text
        self.assertEqual(versions["documind-rag@v3"], V3)        # and v3's line, never rebound to another text
        code, out, err = self.pin()
        self.assertEqual((code, err), (0, ""), out)
        self.assertIn(f"prompt:   {label} ({CFG}: prompt_id@prompt_version, as /version reports it)\n", out)
        self.assertIn(f"sha256:   {BASE}\n", out)
        self.assertIn(f"registry: {label} has this sha256 ({REG}): the text is the one its version names\n", out)

    def test_a_changed_prompt_with_the_same_version_fails(self):
        for name, change in (("SYSTEM", dict(system=extended("Never paraphrase a quote."))),
                             ("DATED_RULE", dict(dated=lambda rule: rule + " Name that date."))):
            with self.subTest(name):
                kit = self.copy(**change)
                self.assertNotEqual(sha(kit / GEN), BASE)
                code, out, err = self.pin(kit)
                self.assertEqual((code, err), (1, ""), out)
                self.assertIn(f"registry: documind-rag@v3 has another sha256, {BASE}: SYSTEM or DATED_RULE changed "
                              "and prompt_version did not\n", out)
                self.assertIn(f'A changed prompt needs a new version. Set prompt_version to "v4" in {CFG}, then add\n'
                              f'    "documind-rag@v4": "{sha(kit / GEN)}"\n'
                              f'to "versions" in {REG}, keeping the lines already there.\n', out)

    def test_a_changed_prompt_with_a_new_registered_version_passes(self):
        v4_text = extended("Never paraphrase a quote.")
        kit = self.copy(system=v4_text, version="v4")                     # v4 in config.py, not yet registered
        v4 = sha(kit / GEN)
        code, out, _ = self.pin(kit)
        self.assertEqual(code, 1, out)
        self.assertIn(f'registry: documind-rag@v4 is not registered ({REG})\nRegister it: add\n'
                      f'    "documind-rag@v4": "{v4}"\n', out)
        both = {"documind-rag@v3": BASE, "documind-rag@v4": v4}
        code, out, err = self.pin(self.copy(system=v4_text, version="v4", versions=both))
        self.assertEqual((code, err), (0, ""), out)                       # registered beside v3: passes
        self.assertIn("registry: documind-rag@v4 has this sha256", out)
        code, out, _ = self.pin(self.copy(version="v4", versions=both))  # v3's text under v4's label: refused
        self.assertEqual(code, 1, out)
        self.assertIn(f'This text is registered as documind-rag@v3: set prompt_version to "v3" in {CFG}, or restore '
                      "documind-rag@v4's text.\n", out)
        code, out, _ = self.pin(self.copy(system=extended("Prefer the newest source."), versions=both))
        self.assertEqual(code, 1, out)                                    # another change under v3: the next free one
        self.assertIn('Set prompt_version to "v5"', out)
        code, out, err = self.pin(self.copy(versions=both))              # the candidate removed: v3, v4's line kept
        self.assertEqual((code, err), (0, ""), out)

    def test_a_label_the_registry_ever_held_is_never_offered_again(self):
        # Lesson 3.6's candidate (13 October 2026): v4 registered on a branch of its own, then main checked out again,
        # where the registry holds v3 alone. The candidate's rows say v4, so the next change on main is offered v5,
        # with the branch kept and once it is deleted (the reflog keeps its commit). With the reflog expired, or in a
        # copy outside git, the registry's own lines are all there is, and v4 is offered.
        if shutil.which("git") is None:
            self.skipTest("needs git")
        kit, v4_text = self.copy(), extended("Never paraphrase a quote.")
        branch = self.copy(system=v4_text, version="v4")
        both = {"documind-rag@v3": BASE, "documind-rag@v4": sha(branch / GEN)}
        branch = self.copy(system=v4_text, version="v4", versions=both)          # the branch's commit: v4 registered
        later = self.copy(system=extended("Prefer the newest source."))          # the next change, made on main
        git = ["git", "-c", "user.name=test", "-c", "user.email=test@localhost", "-c", "core.autocrlf=false",
               "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main"]

        def run(*args):
            r = subprocess.run([*git, *args], cwd=kit, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, (args, r.stderr))

        def take(src: Path):
            for rel in (GEN, CFG, REG):
                (kit / rel).write_bytes((src / rel).read_bytes())

        run("init", "-q")
        run("add", "-A")
        run("commit", "-q", "-m", "the kit: v3")
        run("switch", "-q", "-c", "prompt-v4")
        take(branch)
        run("commit", "-q", "-a", "-m", "v4: rule 4 gains a sentence")
        run("switch", "-q", "main")
        self.assertEqual(json.loads((kit / REG).read_text(encoding="utf-8"))["versions"], {"documind-rag@v3": BASE})
        self.assertEqual(prompt_pin.spent(kit, "documind-rag"), {"documind-rag@v3", "documind-rag@v4"})
        self.assertEqual(prompt_pin.next_version("documind-rag@v3", {"documind-rag@v3": BASE}, kit), "v5")
        (kit / GEN).write_bytes((later / GEN).read_bytes())
        for step in ("the branch kept", "the branch deleted"):
            if step == "the branch deleted":
                run("branch", "-D", "prompt-v4")
            with self.subTest(step):
                code, out, err = self.pin(kit)
                self.assertEqual((code, err), (1, ""), out)
                self.assertIn(f'Set prompt_version to "v5" in {CFG}, then add\n    "documind-rag@v5": ', out)
        run("reflog", "expire", "--expire=now", "--expire-unreachable=now", "--all")
        self.assertEqual(prompt_pin.spent(kit, "documind-rag"), {"documind-rag@v3"})
        code, out, _ = self.pin(kit)
        self.assertIn('Set prompt_version to "v4"', out)                      # nothing left that held v4's line
        self.assertEqual(prompt_pin.spent(later, "documind-rag"), set())      # a copy outside git
        code, out, _ = self.pin(later)
        self.assertIn('Set prompt_version to "v4"', out)

    def test_what_it_cannot_read_is_refused(self):
        twice = '{"versions": {"documind-rag@v3": "%s", "documind-rag@v3": "%s"}}' % (BASE, "0" * 64)
        version_line = re.search(r"^    prompt_version: .*\n", (KIT / CFG).read_text(encoding="utf-8"), re.M).group(0)
        cases = {
            "not JSON": (dict(registry="{"), REG, "not JSON"),
            "no versions": (dict(registry='{"note": "empty"}'), REG, 'no "versions" object'),
            "a label twice": (dict(registry=twice), REG, "documind-rag@v3 written twice"),
            "not a sha256": (dict(versions={"documind-rag@v3": "v3"}), REG, "not a sha256"),
            "SYSTEM not a literal": (dict(gen=('SYSTEM = """', 'SYSTEM = "" + """')), GEN,
                                     "SYSTEM must be set once, at module level, to a string literal"),
            "SYSTEM changed after it is set": (dict(gen=("\n\n\ndef _dated_rule(", '\nSYSTEM += "7. Be brief.\\n"\n\n\n'
                                                         "def _dated_rule(")), GEN, "SYSTEM must be set once"),
            "the join changed": (dict(gen=("{SYSTEM}{_dated_rule(packed)}", "{SYSTEM}\\n{_dated_rule(packed)}")), GEN,
                                 "no longer start the prompt with SYSTEM, then DATED_RULE"),
            "no prompt_version": (dict(cfg=(version_line, ""), version=None), CFG, "prompt_version must be declared once"),
        }
        for name, (edits, rel, why) in cases.items():
            with self.subTest(name):
                code, out, err = self.pin(self.copy(**edits))
                self.assertEqual((code, out), (2, ""), err)
                self.assertTrue(err.startswith(f"prompt_pin: {rel}: "), err)
                self.assertIn(why, err)
        kit = self.copy()
        (kit / REG).unlink()
        code, out, err = self.pin(kit)
        self.assertEqual((code, out), (2, ""), err)
        self.assertTrue(err.startswith(f"prompt_pin: {REG}: cannot read it"), err)

    def test_make_trainset_keeps_the_generators_system(self):
        # The tuning set's copy of SYSTEM is the served one, so a tuned model is served behind the prompt it was trained
        # behind (lesson 12.1). A new version that changes SYSTEM changes evals/make_trainset.py's copy with it.
        self.assertEqual(strings(KIT / "evals" / "make_trainset.py", "SYSTEM"), strings(KIT / GEN, "SYSTEM"))

    def test_the_make_target(self):
        self.assertIn("\nprompt-version:\n\t$(PY) commands/prompt_pin.py\n",
                      (KIT / "mk" / "generation.mk").read_text(encoding="utf-8"))
        makefile = (KIT / "Makefile").read_text(encoding="utf-8")
        phony = makefile[makefile.index(".PHONY:"):makefile.index("# ---------- the module files")].replace("\\", " ")
        self.assertIn("prompt-version", phony.split())
        self.assertIn("`prompt-version`", (KIT / "mk" / "README.md").read_text(encoding="utf-8"))
        # An UNOWNED.md row until a lesson page quotes the file; from then on INDEX.md names the lesson.
        unowned, index = (KIT / "UNOWNED.md").read_text(encoding="utf-8"), (KIT / "INDEX.md").read_text(encoding="utf-8")
        quoted = set(re.findall(r"^\| `([^`]+)` \| \w+ \| (?!- \|)[^|]+ \|", index, re.M))
        for f in (REG, "commands/prompt_pin.py", "commands/tests/test_prompt_versions.py", "mk/generation.mk"):
            self.assertTrue(f"`{f}`" in unowned or f in quoted, f)


if __name__ == "__main__":
    unittest.main()
