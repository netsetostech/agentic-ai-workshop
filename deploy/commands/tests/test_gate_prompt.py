"""Offline tests of make gate's GATE_PROMPT=1 (lessons 3.6 and 11.2): commands/release.py's prompt_reasons(),
prompt_gate() and the switch in live_gate(). Nothing reaches Google Cloud.

    python -m unittest discover -s commands/tests -p test_gate_prompt.py      # from deploy/

Standard library and git. Each case is a commit in a throwaway git repository holding the four files the check reads
(services/rag-api/generator.py, config.py, prompt_versions.json and prompt_rules.json), copied from the kit and edited:
the kit as it ships, its text changed under the same label, lesson 3.6's v4 registered beside v3, a label set on a
revision whose text is another version's, lesson 12.4's rules version on the registered SYSTEM, and the commits and
files the check cannot read. GET /version and the rows are stood in: get_version() returns what a candidate would
answer, and evals/run_eval.py is never started. Without GATE_PROMPT=1, live_gate() reads no /version and runs the rows
as before. Without git the tests skip.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load("release_under_prompt_test", KIT / "commands" / "release.py")
pin = load("prompt_pin_under_gate_test", KIT / "commands" / "prompt_pin.py")
GEN, CFG, REG, RULES = pin.GENERATOR, pin.CONFIG, pin.REGISTRY, release.PROMPT_RULES
RULE4 = "4. Keep answers under 300 words unless asked for more."
VERSION_LINE = '    prompt_version: str = "v3"\n'
NEW_RULE = "Name the policy section each figure comes from."
GIT = ["git", "-c", "user.name=test", "-c", "user.email=test@localhost", "-c", "core.autocrlf=false",
       "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main"]
REAL_RUN = subprocess.run


def sha_of(generator: str) -> str:
    """The sha256 make prompt-version computes for this generator.py's SYSTEM + DATED_RULE."""
    return hashlib.sha256(pin.prompt_text(generator).encode("utf-8")).hexdigest()


@unittest.skipIf(shutil.which("git") is None, "needs git")
class PromptGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="gate_prompt_")
        cls.repo = Path(cls.tmp.name) / "kit"
        cls.src = {rel: (KIT / rel).read_text(encoding="utf-8") for rel in (GEN, CFG, REG, RULES)}
        assert cls.src[GEN].count(RULE4) == 1 and cls.src[CFG].count(VERSION_LINE) == 1, "the kit moved: update the edits"
        cls.v3 = json.loads(cls.src[REG])["versions"]["documind-rag@v3"]
        cls.v4_gen = cls.src[GEN].replace(RULE4, RULE4.replace("300", "200"))
        cls.v4 = sha_of(cls.v4_gen)
        cls.git("init", "-q")
        cls.commits = {
            "shipped": cls.commit({}),
            "text changed, v3 kept": cls.commit({GEN: cls.v4_gen}),
            "v4 registered": cls.commit({GEN: cls.v4_gen, CFG: cls.src[CFG].replace(VERSION_LINE, VERSION_LINE.replace("v3", "v4")),
                                         REG: cls.registry(v4=cls.v4)}),
            "v4's line merged, v3's text": cls.commit({REG: cls.registry(v4=cls.v4)}),
            "12.4's v4": cls.commit({RULES: cls.rules_with_v4()}),
            "12.4's v4, text changed": cls.commit({GEN: cls.v4_gen, RULES: cls.rules_with_v4()}),
            "12.4's v4, registered too": cls.commit({RULES: cls.rules_with_v4(), REG: cls.registry(v4=cls.v4)}),
            "no rules file": cls.commit({RULES: None}),
            "no registry": cls.commit({REG: None}),
        }

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @classmethod
    def git(cls, *args: str) -> str:
        cls.repo.mkdir(parents=True, exist_ok=True)
        r = REAL_RUN([*GIT, *args], cwd=cls.repo, capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, (args, r.stderr)
        return r.stdout.strip()

    @classmethod
    def registry(cls, **more: str) -> str:
        versions = {"documind-rag@v3": cls.v3, **{f"documind-rag@{k}": v for k, v in more.items()}}
        return json.dumps({"versions": versions}, indent=2) + "\n"

    @classmethod
    def rules_with_v4(cls) -> str:
        doc = json.loads(cls.src[RULES])
        doc["versions"]["v4"] = {"rules": [NEW_RULE]}
        return json.dumps(doc, indent=2) + "\n"

    @classmethod
    def commit(cls, changes: dict) -> str:
        """The kit's four files with `changes` (rel -> text, None: absent), committed; the commit's short sha."""
        for rel, text in {**cls.src, **changes}.items():
            path = cls.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if text is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(text, encoding="utf-8", newline="\n")
        cls.git("add", "-A")
        cls.git("commit", "-q", "--allow-empty", "-m", ", ".join(changes) or "the kit")
        return cls.git("rev-parse", "--short=7", "HEAD")

    def reasons(self, case: str, served: str) -> list:
        return release.prompt_reasons(self.commits[case], served, self.repo)

    def test_a_registered_version_passes(self):
        self.assertEqual(self.reasons("shipped", "documind-rag@v3"), [])          # the kit as it ships
        self.assertEqual(self.reasons("v4 registered", "documind-rag@v4"), [])    # lesson 3.6's v4, registered beside v3
        self.assertEqual(self.reasons("12.4's v4", "documind-rag@v4"), [])        # lesson 12.4: v3's SYSTEM and one rule
        self.assertEqual(self.reasons("no rules file", "documind-rag@v3"), [])    # a commit from before lesson 12.4
        self.assertEqual(self.reasons("v4's line merged, v3's text", "documind-rag@v3"), [])

    def test_a_text_its_label_is_not_registered_to_is_refused(self):
        why = self.reasons("text changed, v3 kept", "documind-rag@v3")
        self.assertEqual(why, [f"documind-rag@v3 is registered to sha256 {self.v3[:12]}..., and SYSTEM + DATED_RULE hash "
                               f"to {self.v4[:12]}...: the text changed and the version did not"])
        # PROMPT_VERSION=v3 on an image whose text is v4's; PROMPT_VERSION=v4 on one whose text is still v3's
        self.assertIn("the text changed and the version did not", self.reasons("v4 registered", "documind-rag@v3")[0])
        self.assertIn(f"documind-rag@v4 is registered to sha256 {self.v4[:12]}",
                      self.reasons("v4's line merged, v3's text", "documind-rag@v4")[0])
        self.assertEqual(self.reasons("shipped", "documind-rag@v9"),
                         [f"documind-rag@v9 is not registered in {REG}, and SYSTEM + DATED_RULE hash to {self.v3[:12]}...: "
                          "register the label, or answer under the one that text is registered to"])

    def test_a_rules_version_needs_the_registered_system_and_one_label(self):
        why = self.reasons("12.4's v4, text changed", "documind-rag@v4")
        self.assertEqual(why, [f"documind-rag@v4 serves SYSTEM and 1 rule of {RULES}, and SYSTEM + DATED_RULE (sha256 "
                               f"{self.v4[:12]}...) is not the text documind-rag@v3 is registered to: make prompt-version at "
                               "that commit says why"])
        self.assertEqual(self.reasons("12.4's v4, registered too", "documind-rag@v4"),
                         [f"documind-rag@v4 is a rules version in {RULES} and registered in {REG} as well: one label, two texts"])

    def test_what_it_cannot_read_is_a_reason(self):
        self.assertEqual(release.prompt_reasons("dev", "documind-rag@v3", self.repo), ["GIT_SHA 'dev' names no commit"])
        self.assertEqual(release.prompt_reasons("0123abc", "documind-rag@v3", self.repo),
                         ["this checkout holds no commit 0123abc: fetch it, or gate from the clone that built the image"])
        self.assertEqual(self.reasons("no registry", "documind-rag@v3"), [f"commit {self.commits['no registry']} has no {REG}"])
        self.assertEqual(self.reasons("shipped", ""), ["GET /version names no prompt"])

    def live_gate(self, answers: dict | None, switch: str | None) -> tuple:
        """live_gate() with GATE_PROMPT set to `switch` (None: not set), and GET /version and evals/run_eval.py stood in:
        (its result or the Stop, what it printed, the commands it ran other than git)."""
        ran = []

        def run(argv, *a, **k):
            if argv[0] == "git":
                return REAL_RUN(argv, *a, **k)
            ran.append(argv)
            return subprocess.CompletedProcess(argv, 0)

        def get_version(url, token):
            if answers is None:
                raise AssertionError("GET /version was asked without GATE_PROMPT=1")
            return answers

        env = {k: v for k, v in os.environ.items() if k != "GATE_PROMPT"}
        out = io.StringIO()
        with mock.patch.dict(os.environ, {**env, **({"GATE_PROMPT": switch} if switch is not None else {})}, clear=True), \
                mock.patch.object(release.subprocess, "run", run), mock.patch.object(release, "get_version", get_version), \
                mock.patch.object(release, "KIT", self.repo), contextlib.redirect_stdout(out):
            try:
                result = release.live_gate("https://candidate---documind-api-NUMBER.REGION.run.app",
                                           Path(self.tmp.name) / "gate-report.json", "MEMBER", "OUTSIDER")
            except release.Stop as e:
                result = e
        return result, out.getvalue(), ran

    def test_without_the_switch_live_gate_is_unchanged(self):
        for switch in (None, "", "0", "yes"):                                  # GATE_PROMPT=1 alone turns it on
            with self.subTest(GATE_PROMPT=switch):
                result, out, ran = self.live_gate(None, switch)
                self.assertEqual((result, out), (0, ""))
                self.assertEqual(len(ran), 1)
                self.assertTrue(ran[0][1].endswith(os.path.join("evals", "run_eval.py")) and ran[0][2:4] == [
                                "--api-url", "https://candidate---documind-api-NUMBER.REGION.run.app"], ran)

    def test_with_the_switch_a_bad_prompt_stops_before_any_row(self):
        sha = self.commits["text changed, v3 kept"]
        result, out, ran = self.live_gate({"git_sha": sha, "prompt": "documind-rag@v3"}, "1")
        self.assertIsInstance(result, release.Stop)
        self.assertTrue(str(result).startswith(f"GATE_PROMPT=1: the candidate answers as documind-rag@v3 at GIT_SHA {sha}, "
                                               "which is not a registered prompt version: documind-rag@v3 is registered "
                                               "to sha256 "), result)
        self.assertIn("No row was asked and there is no gate record", str(result))
        self.assertEqual((out, ran), ("", []))                                  # evals/run_eval.py never started

    def test_with_the_switch_a_registered_prompt_runs_the_rows(self):
        sha = self.commits["v4 registered"]
        result, out, ran = self.live_gate({"git_sha": sha, "prompt": "documind-rag@v4"}, "1")
        self.assertEqual(result, 0)
        self.assertEqual(out, f">> prompt: documind-rag@v4 at GIT_SHA {sha} is a registered version (GATE_PROMPT=1, "
                              f"{REG} at that commit)\n")
        self.assertEqual(len(ran), 1)

    def test_the_switch_is_documented(self):
        # make gate ... GATE_PROMPT=1: make exports a variable set on its command line to the recipe, so
        # mk/release.mk's gate recipe, which lesson 11.2 quotes, needs no change for it
        self.assertIn("GATE_PROMPT=1 (off by default: it can refuse a release)", release.__doc__)
        self.assertIn("GATE_PROMPT=1", release.live_gate.__doc__)


if __name__ == "__main__":
    unittest.main()
