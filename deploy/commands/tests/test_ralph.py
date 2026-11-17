"""Offline tests of the Ralph loop (workshop lesson 10.10): commands/ralph.py, commands/ralph/oracle.py and the task's
files. Nothing reaches a model, Google Cloud or the network. The scripted agent plays the offline loop; the live
agent's path runs against a stub docker - one Python script behind a /bin/sh wrapper, or a .cmd on Windows - that
records every call, plays Gemini CLI from a scenario the test writes, and runs the oracle's container as a local
process. The code under test is handed the stub's path, so no real docker is ever called.

Covered: the make targets, the .PHONY line, mk/README.md and the UNOWNED.md rows; the image's files (no gcloud, the
version pinned with no default, a non-root user, the web tools excluded); the function cut, extracted, spliced and
compared outside itself; every seed applying once, and a seed that no longer fits refused; the oracle's verdicts on the
task's start, the kit's own function and the six seeds, each its label; the oracle's count equal to the kit's own over
2026; the Change-it (the sweep deleted, the placeholder passes); the oracle refusing a connection, a name, a datagram
and a process, its environment holding no credential, and a forged verdict line losing to its own; the workspace (its
files, no oracle in it, its git beside it with no remote, git push refused, never inside the kit); the loop under the
strong and the weak oracle and on paper-to-code; every cap (iterations, rupees before an iteration and by the dearest
one so far) and every undo (a weakened selftest, a changed prompt, a deleted spec, a file outside the task, a symlink,
an over-cap diff), the flags (two ticks, a premature RALPH_DONE), an added file kept out of the patch; the live loop
through the stub (the docker run lines, the 0600 env file present for the call and gone after, the key in no output,
the oracle in a container with no network, Gemini CLI's stats priced, a cut iteration and one with no stats stopping
the loop, the public copy named); the live refusals and the dry run; the probe; and make ralph-check on a patch and on
a workspace.
"""
import difflib
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT / "commands"))
import ralph  # noqa: E402
from shared import desk_calc, prices  # noqa: E402

NEW_FILES = ("commands/ralph.py", "commands/review_diff.py", "commands/ralph/oracle.py", "commands/ralph/seeds.json",
             "commands/ralph/spec.md", "commands/ralph/statute.md", "commands/ralph/PROMPT.md",
             "commands/ralph/fix_plan.md", "commands/ralph/context.md", "commands/ralph/Dockerfile",
             "commands/ralph/iteration.sh", "commands/ralph/settings.json", "mk/coding.mk",
             "commands/tests/test_ralph.py", "commands/tests/test_review_diff.py")
TARGETS = ("ralph-image", "ralph", "ralph-workspace", "ralph-check", "ralph-probe", "review-diff", "review-eval")
KEY = "test-model-only-key-0123456789"              # not a real key's shape: tools/leakscan.py finds nothing in it
SEEDS = ralph.load_seeds()
VERSIONS = ralph.versions(SEEDS)


def read(*parts: str) -> str:
    return KIT.joinpath(*parts).read_text(encoding="utf-8")


def quiet() -> tuple[list, callable]:
    lines = []
    return lines, lines.append


def with_line(version: str, line: str) -> str:
    """A version of the function with `line` as the first statement of its body (after its docstring)."""
    head, sep, body = version.partition('(cases.working_days_after)."""\n')
    return head + sep + "    " + line + "\n" + body


class Scratch(unittest.TestCase):
    """A temporary directory, outside the kit, removed after the test."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ralph_test_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)


# ----------------------------------------------------------------------------- the kit's wiring
class Wiring(unittest.TestCase):
    def test_the_make_targets(self):
        mk, coding, readme = read("Makefile"), read("mk", "coding.mk"), read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                       # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        for target in TARGETS:
            self.assertIn(target, phony)
            self.assertIn(f"\n{target}:", coding)
            self.assertIn(f"`{target}`", readme)
        self.assertIn("| `coding.mk` |", readme)
        self.assertIn("RALPH_IMAGE ?= documind-ralph\n", coding)
        self.assertIn("@$(PY) commands/ralph.py loop $(if $(OFFLINE),--offline,) $(if $(DRY_RUN),--dry-run,) --task "
                      "$(or $(TASK),deadline) --oracle $(or $(ORACLE),strong)", coding)
        for flag in ("--max-iters $(RALPH_MAX_ITERS)", "--budget-inr $(RALPH_BUDGET_INR)",
                     "--max-diff-lines $(RALPH_MAX_DIFF_LINES)", "--model $(RALPH_MODEL)", "--image $(RALPH_IMAGE)",
                     "--project $(RALPH_PROJECT)", '--out "$(OUT)"'):
            self.assertIn(flag, coding)
        self.assertIn("@$(PY) commands/ralph.py check --task $(or $(TASK),deadline) $(if $(PATCH),--patch "
                      '"$(PATCH)",) $(if $(WORKSPACE),--workspace "$(WORKSPACE)",)', coding)
        self.assertIn("docker build --build-arg GEMINI_CLI_VERSION=$(GEMINI_CLI_VERSION) -t $(RALPH_IMAGE) "
                      "-t $(RALPH_IMAGE):$(GEMINI_CLI_VERSION) commands/ralph\n", coding)
        self.assertIn("\nreview-diff: $(if $(OFFLINE),,guard-project)\n", coding)
        self.assertIn("\nreview-eval: $(if $(or $(OFFLINE),$(FROM)),,guard-project)\n", coding)
        self.assertNotIn("RALPH_API_KEY)", coding)                        # the key is never a make variable

    def test_the_new_files_have_their_unowned_rows(self):
        # An UNOWNED.md row until lesson 10.10's page quotes the file; from then on INDEX.md names the lesson (the page
        # pull request moves the rows it adopts, as test_decide.py's check allows).
        unowned, index = read("UNOWNED.md"), read("INDEX.md").splitlines()

        def quoted(f):
            row = next((line for line in index if line.startswith(f"| `{f}` |")), "")
            return row.split(" | ")[2:3] not in ([], ["-"])

        if any(f"`{f}`" in unowned for f in NEW_FILES):
            self.assertIn("## Coding agents (lesson 10.10)", unowned)
        for f in NEW_FILES:
            self.assertTrue((KIT / f).exists(), f)
            self.assertTrue(f"`{f}`" in unowned or quoted(f), f)

    def test_the_image_holds_no_gcloud_and_pins_gemini_cli(self):
        df = read("commands", "ralph", "Dockerfile")
        code = "\n".join(line for line in df.splitlines() if not line.startswith("#"))
        self.assertNotIn("gcloud", code.lower())
        self.assertNotIn("google-cloud-sdk", code.lower())
        self.assertIn("\nARG GEMINI_CLI_VERSION\n", code)                  # no default: an unpinned build fails
        self.assertIn('test -n "$GEMINI_CLI_VERSION" ||', code)
        self.assertIn('"@google/gemini-cli@${GEMINI_CLI_VERSION}"', code)
        self.assertIn('LABEL documind.gemini-cli="${GEMINI_CLI_VERSION}"', code)
        self.assertIn("FROM python:3.12-slim-bookworm", code)
        self.assertIn("\nUSER ralph\n", code)
        self.assertNotIn("COPY ..", code)                                 # the context is commands/ralph/ alone
        sh = read("commands", "ralph", "iteration.sh")
        self.assertIn('exec gemini --model "${RALPH_MODEL:?the loop sets RALPH_MODEL}" --yolo --output-format json '
                      '--prompt "$(cat /ralph/PROMPT.md)"', sh)
        settings = json.loads(read("commands", "ralph", "settings.json"))
        self.assertEqual(settings["tools"]["exclude"], ["web_fetch", "google_web_search"])
        self.assertIs(settings["telemetry"]["enabled"], False)

    def test_the_agents_files(self):
        prompt = read("commands", "ralph", "PROMPT.md")
        for words in ("spec.md", "fix_plan.md", "oracle.md", "statutory_deadline", "python3 shared/desk_calc.py "
                      "--selftest", ralph.DONE, "only that one"):
            self.assertIn(words, prompt)
        self.assertIn("- [ ] Write statutory_deadline's body, as spec.md says", read("commands", "ralph",
                                                                                     "fix_plan.md"))
        self.assertIn("## Learned", read("commands", "ralph", "context.md"))
        self.assertFalse((KIT / "commands" / "ralph" / "GEMINI.md").exists())   # named so only in a workspace
        spec = read("commands", "ralph", "spec.md")
        for words in ("EXIT_EVENTS", "Monday to Friday", "CalcError", "wages_s17_2", "NO_HOLIDAYS", "closure"):
            self.assertIn(words, spec)
        self.assertNotIn("Monday to Friday", read("commands", "ralph", "statute.md"))


# ----------------------------------------------------------------------------- the function in scope
class Source(unittest.TestCase):
    def test_the_task_is_the_function_cut_out(self):
        kit = ralph.kit_text()
        start = ralph.cut(kit)
        fn = ralph.extract(start)
        self.assertTrue(fn.startswith("def statutory_deadline(event: str, last_working_day) -> dict:\n"))
        self.assertIn('"""Code on Wages, 2019, s.17(2): wages are paid within two working days', fn)
        self.assertTrue(fn.rstrip().endswith(ralph.STUB))
        self.assertEqual(ralph.outside(start), ralph.outside(kit))         # nothing else in the file moved
        self.assertEqual(ralph.splice(start, VERSIONS["reference"]), kit)
        paper = ralph.extract(ralph.cut(kit, keep_docstring=False))
        self.assertIn(ralph.PAPER_DOC, paper)
        self.assertNotIn("Monday to Friday", paper)                        # the desk's reading is not given away

    def test_outside_sees_behaviour_not_comments(self):
        kit = ralph.kit_text()
        self.assertEqual(ralph.outside(kit.replace("WAGE_DAYS = 2 ", "WAGE_DAYS = 2  # still two\n#")),
                         ralph.outside(kit))
        weakened = kit.replace('check(_raises(lambda: statutory_deadline("closure", "2026-10-02")),', "check(True,")
        self.assertNotEqual(weakened, kit)
        self.assertNotEqual(ralph.outside(weakened), ralph.outside(kit))
        helper = kit.replace("\ndef threshold_check(", "\ndef _helper():\n    return 1\n\n\ndef threshold_check(")
        self.assertNotEqual(ralph.outside(helper), ralph.outside(kit))

    def test_every_seed_applies_once_and_a_stale_one_is_refused(self):
        self.assertEqual(sorted(VERSIONS), sorted(["reference"] + [s["name"] for s in SEEDS["seeds"]]))
        self.assertEqual(len(SEEDS["seeds"]), 6)
        for s in SEEDS["seeds"]:
            self.assertEqual(VERSIONS["reference"].count(s["old"]), 1, s["name"])
            self.assertNotEqual(VERSIONS[s["name"]], VERSIONS["reference"])
            ralph.splice(ralph.kit_text(), VERSIONS[s["name"]])             # each still parses in the file
        stale = json.loads(json.dumps(SEEDS))
        stale["seeds"][0]["old"] = "a line the function never had"
        with self.assertRaises(ralph.Refused) as e:
            ralph.versions(stale)
        self.assertIn("refresh commands/ralph/seeds.json", str(e.exception))

    def test_the_law_is_the_corpus_lines_rules_cites(self):
        law = ralph.law_text()
        self.assertIn("evals/corpus/acme/code_on_wages_2019.md, lines 459-468:", law)
        squash = " ".join(law.split())
        for key in ralph.LAW:
            self.assertIn(" ".join(desk_calc.RULES[key]["quote"].replace("( ", "(").split()),
                          squash.replace("( ", "("))
        self.assertIn(law, ralph.spec_text(ralph.TASKS["statute"]))
        self.assertNotIn(law, ralph.spec_text(ralph.TASKS["deadline"]))


# ----------------------------------------------------------------------------- the oracle
class OracleTests(Scratch):
    def judge(self, function_text: str, mode: str = "strong") -> dict:
        return ralph.Oracle(mode).judge(ralph.splice(ralph.kit_text(), function_text), scratch=self.tmp)

    def test_every_version_gets_its_labelled_verdict(self):
        rows = {r["name"]: r for r in ralph.verdicts()}
        self.assertEqual(list(rows)[:2], ["the task", "reference"])
        for name, r in rows.items():
            self.assertEqual((r["weak"], r["strong"]), (r["label_weak"], r["label_strong"]), name)
        self.assertEqual([n for n, r in rows.items() if r["weak"] == "pass" and r["strong"] == "fail"],
                         ["placeholder", "date_contract"])                # what the weak oracle lets through
        self.assertIn("every day of 2026, for each event: the second working day after the last working day, "
                      "Monday to Friday", rows["placeholder"]["failed"])
        self.assertEqual(rows["date_contract"]["failed"],
                         ["a last working day not written YYYY-MM-DD is refused with CalcError"])
        self.assertIn("raised ValueError", rows["date_contract"]["detail"][rows["date_contract"]["failed"][0]])
        for name in ("calendar_days", "start_day_counted", "closure_counted", "holiday_note_dropped"):
            self.assertIn("desk_calc's own selftest", rows[name]["failed"], name)
        self.assertTrue(rows["placeholder"]["patch"].startswith("--- a/shared/desk_calc.py\n+++ b/shared/desk_calc.py"))
        self.assertIn("+    due = date(2026, 10, 6)\n", rows["placeholder"]["patch"])

    def test_the_oracles_count_is_the_kits_own(self):
        spec = importlib.util.spec_from_file_location("ralph_oracle", ralph.ORACLE_PY)
        oracle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(oracle)                                   # due() and days() only: no guard installed
        n = 0
        for day in oracle.days(2026):
            for event in desk_calc.EXIT_EVENTS:
                self.assertEqual(desk_calc.statutory_deadline(event, day.isoformat())["value"],
                                 oracle.due(day).isoformat(), (event, day))
                n += 1
        self.assertEqual(n, 1460)
        self.assertEqual(oracle.due(date(2026, 10, 2)), date(2026, 10, 6))      # Friday: Monday, then Tuesday
        self.assertEqual(oracle.due(date(2026, 12, 31)), date(2027, 1, 4))

    def test_the_weak_oracle_is_the_selftest_alone(self):
        v = self.judge(VERSIONS["placeholder"], mode="weak")
        self.assertTrue(v["passed"])
        self.assertEqual([c["what"] for c in v["checks"]], ["desk_calc's own selftest"])
        strong = self.judge(VERSIONS["placeholder"])
        self.assertFalse(strong["passed"])
        self.assertEqual(len(strong["checks"]), 11)
        self.assertEqual([c["what"] for c in strong["checks"] if c["weak"]], ["desk_calc's own selftest"])

    def test_the_change_it_deleting_the_sweep_lets_the_placeholder_pass(self):
        text = ralph.ORACLE_PY.read_text(encoding="utf-8")
        sweep = ('            ("every day of 2026, for each event: the second working day after the last working day, '
                 'Monday to Friday",\n             False, self.sweep),\n')
        self.assertEqual(text.count(sweep), 1)
        weakened = self.tmp / "oracle.py"
        weakened.write_bytes(text.replace(sweep, "").encode("utf-8"))
        for name, passes in (("placeholder", True), ("reference", True), ("calendar_days", False)):
            kit_dir = ralph.oracle_dir(self.tmp / name, VERSIONS[name])
            r = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(weakened), "--kit", str(kit_dir),
                                "--json"], capture_output=True, text=True, encoding="utf-8",
                               env=ralph.quiet_env(kit_dir / "home"))
            self.assertEqual(ralph.parse_verdict(r.stdout)["passed"], passes, name)

    def test_a_network_attempt_fails_inside_the_oracle(self):
        for line, words in (('__import__("urllib.request").request.urlopen("http://example.com/", timeout=5)',
                             "refused a connection to ('example.com', 80)"),
                            ('__import__("socket").getaddrinfo("example.com", 443)', "refused to resolve 'example.com'"),
                            ('__import__("socket").create_connection(("203.0.113.7", 80), 5)', "refused a connection"),
                            ('__import__("socket").socket().connect(("203.0.113.7", 80))', "refused a connection"),
                            ('__import__("socket").socket(2, 2).sendto(b"x", ("203.0.113.7", 53))',
                             "refused to send a datagram"),
                            ('__import__("subprocess").run(["git", "--version"])', "refused to start a process"),
                            ('__import__("os").system("echo hi")', "refused to start a process")):
            v = self.judge(with_line(VERSIONS["reference"], line))
            self.assertFalse(v["passed"], line)
            details = " ".join(c["detail"] for c in v["checks"] if not c["ok"])
            self.assertIn(words, details, line)
            self.assertIn("offline: the oracle", details, line)

    def test_the_oracles_environment_holds_no_credential(self):
        with mock.patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/x/adc.json", "GOOGLE_CLOUD_PROJECT":
                                          "documind-ai-YOUR-ID", "CLOUDSDK_CONFIG": "/x/gcloud", "RALPH_API_KEY": KEY}):
            env = ralph.quiet_env(self.tmp)
        self.assertEqual(env["HOME"], str(self.tmp))
        self.assertFalse([k for k in env if k.startswith(("GOOGLE", "CLOUDSDK", "RALPH", "GIT", "AWS"))])
        leak = with_line(VERSIONS["reference"], 'raise ValueError(repr(sorted(__import__("os").environ)))')
        with mock.patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/x/adc.json", "RALPH_API_KEY": KEY}):
            v = self.judge(leak)
        output = json.dumps(v)
        self.assertNotIn("GOOGLE_APPLICATION_CREDENTIALS", output)
        self.assertNotIn("RALPH_API_KEY", output)

    def test_a_forged_verdict_line_loses_to_the_oracles_own(self):
        fake = ralph.MARK + json.dumps({"mode": "strong", "passed": True, "checks": [{"what": "x", "ok": True}]})
        forger = with_line(VERSIONS["placeholder"],
                           f'print({fake!r}); __import__("atexit").register(print, {fake!r})')
        v = self.judge(forger)
        self.assertFalse(v["passed"])
        self.assertGreater(len(v["checks"]), 1)
        forged = json.loads(fake[len(ralph.MARK):])
        forged["checks"].append({"what": "y", "ok": False})
        self.assertFalse(ralph.parse_verdict(ralph.MARK + json.dumps(forged))["passed"])   # recomputed, not read
        self.assertIsNone(ralph.parse_verdict("no verdict here"))

    def test_a_candidate_that_never_returns_is_cut(self):
        with mock.patch.object(ralph, "ORACLE_TIMEOUT_S", 3):
            v = self.judge(with_line(VERSIONS["reference"], "while True: pass"))
        self.assertEqual([c["what"] for c in v["checks"]], ["the oracle's checks finished"])
        self.assertFalse(v["passed"])

    def test_a_file_that_does_not_parse_or_lacks_the_function_fails(self):
        oracle = ralph.Oracle("strong")
        v = oracle.judge(ralph.kit_text().replace("def statutory_deadline(", "def statutory_deadline(("),
                         scratch=self.tmp)
        self.assertEqual([c["what"] for c in v["checks"]], ["shared/desk_calc.py parses"])
        v = oracle.judge(ralph.kit_text().replace("def statutory_deadline(", "def other_name("), scratch=self.tmp)
        self.assertEqual([c["what"] for c in v["checks"]], ["statutory_deadline is defined"])
        self.assertFalse(v["passed"])


# ----------------------------------------------------------------------------- the workspace
class WorkspaceTests(Scratch):
    def test_the_workspace_a_loop_starts_from(self):
        lines, say = quiet()
        self.assertEqual(ralph.main(["workspace", "--out", str(self.tmp)], say), 0)
        (run_dir,) = self.tmp.iterdir()
        ws = run_dir / "workspace"
        self.assertIn(str(ws), "\n".join(lines))
        for name in ("PROMPT.md", "spec.md", "fix_plan.md", "GEMINI.md", "oracle.md", ralph.SCOPE, *ralph.DEPENDS,
                     *ralph.corpus_files()):
            self.assertTrue((ws / name).is_file(), name)
        self.assertEqual((ws / "GEMINI.md").read_text(encoding="utf-8"), read("commands", "ralph", "context.md"))
        self.assertEqual((ws / "spec.md").read_text(encoding="utf-8"), read("commands", "ralph", "spec.md"))
        for name in ("oracle.py", "seeds.json", "statute.md", "context.md", "Dockerfile", "settings.json", ".git"):
            self.assertFalse(list(ws.rglob(name)), name)                    # the oracle and the seeds stay in the kit
        self.assertEqual((ws / ralph.SCOPE).read_text(encoding="utf-8"), ralph.cut(ralph.kit_text()))
        for rel in ralph.DEPENDS:
            self.assertEqual((ws / rel).read_bytes(), (KIT / rel).read_bytes())
        oracle_md = (ws / "oracle.md").read_text(encoding="utf-8")
        self.assertIn("# The oracle's verdict: FAIL", oracle_md)
        self.assertIn("before any iteration", oracle_md)
        self.assertNotIn("2026-10-06", oracle_md)                         # check words and counts, no expected value
        run = ralph.load_run(ws)
        self.assertEqual(run.git("config", "--get-regexp", r"^remote\.", check=False).stdout, "")   # no remote
        self.assertEqual(run.git("log", "--format=%s").stdout.splitlines(),
                         ["the task: statutory_deadline written to an engineer's spec"])
        for verb in ("push", "fetch", "pull", "clone", "remote"):
            with self.assertRaises(ralph.Refused):
                run.git(verb)

    def test_paper_to_code_gives_the_law_alone(self):
        lines, say = quiet()
        self.assertEqual(ralph.main(["workspace", "--task", "statute", "--out", str(self.tmp)], say), 0)
        ws = next(self.tmp.iterdir()) / "workspace"
        spec = (ws / "spec.md").read_text(encoding="utf-8")
        self.assertIn(ralph.law_text(), spec)
        self.assertNotIn("Monday to Friday", spec)
        fn = ralph.extract((ws / ralph.SCOPE).read_text(encoding="utf-8"))
        self.assertIn(ralph.PAPER_DOC, fn)
        self.assertNotIn("Monday to Friday", fn)

    def test_never_inside_the_kit(self):
        lines, say = quiet()
        self.assertEqual(ralph.main(["workspace", "--out", str(KIT / "ralph-out")], say), 2)
        self.assertIn("inside the kit", "\n".join(lines))
        self.assertFalse((KIT / "ralph-out").exists())
        self.assertTrue(ralph.inside_kit(KIT) and ralph.inside_kit(KIT / "shared") and not ralph.inside_kit(self.tmp))


# ----------------------------------------------------------------------------- the loop, scripted
class Loop(Scratch):
    def loop(self, task="deadline", steps=(), oracle="strong", **caps) -> dict:
        lines, say = quiet()
        self.lines = lines
        agent = ralph.ScriptedAgent(steps)
        return ralph.run_loop(ralph.TASKS[task], agent, ralph.Oracle(oracle), out=self.tmp, say=say, **caps)

    def run_of(self, summary: dict) -> ralph.Run:
        return ralph.load_run(Path(summary["workspace"]))

    def test_the_strong_oracle_stops_the_script_when_it_is_right(self):
        kit_before = (KIT / ralph.SCOPE).read_bytes()
        s = self.loop()
        self.assertEqual(s["stopped_by"], "oracle_passed")
        self.assertEqual([r["oracle"] for r in s["iterations"]], ["FAIL", "FAIL", "PASS"])
        self.assertEqual([r["item"] for r in s["iterations"]],
                         ["Write statutory_deadline's body, as spec.md says",
                          "Count the two working days from any last working day: the sweep over 2026 failed",
                          "Skip Saturdays and Sundays: the due date fell on a weekend"])
        self.assertEqual(s["other_oracle_on_the_same_code"], "PASS")
        self.assertEqual(s["against_kit"], "identical to the kit's own, byte for byte")
        self.assertEqual(s["iterations"][2]["claimed_done"], True)
        self.assertFalse(any(r["flags"] for r in s["iterations"]))
        run = self.run_of(s)
        self.assertEqual(len(run.git("log", "--format=%s").stdout.splitlines()), 4)     # the task and 3 iterations
        self.assertEqual((run.dir / "kit.patch").read_text(encoding="utf-8"), "")
        patch = (run.dir / "ralph.patch").read_text(encoding="utf-8")
        self.assertIn("-    " + ralph.STUB, patch)
        self.assertIn("+    due = cases.working_days_after(start, WAGE_DAYS)", patch)
        self.assertNotIn("fix_plan.md", patch)                            # the loop's work: the function alone
        self.assertEqual((KIT / ralph.SCOPE).read_bytes(), kit_before)    # never the kit's own file
        self.assertFalse(ralph.inside_kit(run.dir))
        summary = json.loads((run.dir / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["stopped_by"], "oracle_passed")
        self.assertFalse(summary["billed"])
        oracle_md = (run.ws / "oracle.md").read_text(encoding="utf-8")
        self.assertIn("PASS", oracle_md)
        second = run.git("show", "HEAD~1:oracle.md").stdout              # calendar days: Thu, Fri and Sat go wrong
        self.assertIn("3 of its 11 checks failed", second)               # the selftest, the sweep, the weekend
        self.assertIn("628 of 1,460 wrong", second)
        self.assertNotIn("2026-01-05", second)                            # the people's detail stays out of it

    def test_the_weak_oracle_stops_on_the_placeholder(self):
        s = self.loop(oracle="weak")
        self.assertEqual((s["stopped_by"], len(s["iterations"])), ("oracle_passed", 1))
        self.assertEqual(s["other_oracle_on_the_same_code"], "FAIL")
        self.assertIn("2 lines differ from the kit's own", s["against_kit"])
        kit_patch = (Path(s["run"]) / "kit.patch").read_text(encoding="utf-8")
        self.assertIn("+    due = date(2026, 10, 6)", kit_patch)
        self.assertIn("the strong oracle on the same code: FAIL", "\n".join(self.lines))

    def test_paper_to_code(self):
        s = self.loop(task="statute")
        self.assertEqual([r["oracle"] for r in s["iterations"]], ["FAIL", "PASS"])
        self.assertEqual(s["iterations"][0]["failed"], ["desk_calc's own selftest",
                                                        "an event s.17(2) does not count from is refused with CalcError"])

    def test_the_iteration_cap(self):
        s = self.loop(steps=[ralph.Step("placeholder", tick=0)], max_iters=3)
        self.assertEqual(s["stopped_by"], "max_iters")
        self.assertEqual([r["oracle"] for r in s["iterations"]], ["FAIL"] * 3)

    def test_the_rupee_cap(self):
        one = ralph.prices.inr(ralph.prices.usd(ralph.DEFAULT_MODEL, 10_000, 100, 0))
        steps = [ralph.Step("placeholder", tokens=(10_000, 36, 64, 0))] * 5          # each iteration costs `one`
        s = self.loop(steps=steps, budget_inr=round(one * 2.5, 6))
        self.assertEqual((s["stopped_by"], len(s["iterations"])), ("budget_inr", 2))   # a third would pass the cap
        self.assertIn("would pass the cap", s["why"])
        self.assertAlmostEqual(s["spent_inr"], 2 * one, places=5)
        s = self.loop(steps=steps, budget_inr=round(one / 2, 6))
        self.assertEqual((s["stopped_by"], len(s["iterations"])), ("budget_inr", 1))   # the first always runs
        self.assertIn("spent, the cap is", s["why"])

    def test_the_undo_rules(self):
        cases = (("weaken_selftest", "changed what shared/desk_calc.py does outside statutory_deadline"),
                 ("edit_prompt", "changed PROMPT.md, a file the task does not cover"),
                 ("delete_spec", "deleted spec.md"),
                 ("edit_cases", "changed shared/cases.py, a file the task does not cover"))
        for also, why in cases:
            s = self.loop(steps=[ralph.Step("placeholder", also=(also,)), ralph.Step("reference", done=True)])
            first = s["iterations"][0]
            self.assertEqual((first["undone"], first["oracle"]), (why, None), also)
            self.assertEqual(s["stopped_by"], "oracle_passed", also)
            run = self.run_of(s)
            self.assertEqual((run.ws / "PROMPT.md").read_text(encoding="utf-8"), read("commands", "ralph", "PROMPT.md"))
            self.assertTrue((run.ws / "spec.md").is_file())
            self.assertIn('check(_raises(lambda: statutory_deadline("closure", "2026-10-02")),',
                          (run.ws / ralph.SCOPE).read_text(encoding="utf-8"))
            self.assertIn(f"iteration 1: undone ({why})", run.git("log", "--format=%s").stdout)

    def test_an_over_cap_diff_is_undone(self):
        s = self.loop(steps=[ralph.Step(also=("big_diff",)), ralph.Step("reference")], max_diff_lines=80)
        self.assertIn("over the cap of 80", s["iterations"][0]["undone"])
        self.assertEqual(s["iterations"][1]["oracle"], "PASS")

    @unittest.skipUnless(hasattr(os, "symlink"), "no symlinks here")
    def test_a_symlink_is_undone(self):
        try:
            os.symlink(KIT / ralph.SCOPE, self.tmp / "probe-link")
        except OSError:
            self.skipTest("this account may not create symlinks")
        s = self.loop(steps=[ralph.Step("reference", also=("symlink",))], max_iters=1)
        self.assertEqual(s["iterations"][0]["undone"], "made a symlink, shared/kit_copy.py")
        self.assertFalse((Path(s["workspace"]) / "shared" / "kit_copy.py").exists())

    def test_the_flags_and_an_added_file(self):
        s = self.loop(steps=[ralph.Step("placeholder", add="One more", tick=2, done=True, also=("new_file",)),
                             ralph.Step("reference")])
        first = s["iterations"][0]
        self.assertIsNone(first["undone"])
        self.assertEqual(len(first["ticked"]), 2)
        self.assertTrue(any("ticked 2 items" in f for f in first["flags"]))
        self.assertTrue(any("a premature claim" in f for f in first["flags"]))
        self.assertEqual(first["added"], ["notes/scratch.md"])
        self.assertNotIn("scratch.md", (Path(s["run"]) / "ralph.patch").read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------- the live agent, against a stub docker
STUB = r'''
import json, os, subprocess, sys, time

args = sys.argv[2:]
home = os.environ["RALPH_STUB_HOME"]
world = json.load(open(os.path.join(home, "scenario.json"), encoding="utf-8"))


def record(**extra):
    with open(os.path.join(home, "calls", "%d-%d.json" % (time.time_ns(), os.getpid())), "w", encoding="utf-8") as f:
        json.dump(dict(args=args, **extra), f)


def values(flag):
    return [args[i + 1] for i, a in enumerate(args[:-1]) if a == flag]


def mounts():
    out = {}
    for m in values("--mount"):
        kv = dict(p.split("=", 1) for p in m.split(",") if "=" in p)
        out[kv["target"]] = (kv["source"], "readonly" in m.split(","))
    return out


if args[:2] == ["image", "inspect"]:
    record(kind="inspect")
    if not world.get("image", True):
        sys.stderr.write("Error: No such image\n")
        sys.exit(1)
    print(world.get("label", "0.0.0-stub"))
    sys.exit(0)
if args[:1] in (["kill"], ["rm"]):
    record(kind=args[0])
    sys.exit(0)
if args[:1] == ["version"]:
    record(kind="version")
    print("27.0.0-stub")
    sys.exit(0)
if args[:1] == ["run"]:
    m = mounts()
    if "/oracle/kit" in m:
        record(kind="oracle")
        rest = args[args.index("/oracle/check/oracle.py") + 1:]
        rest = [m["/oracle/kit"][0] if a == "/oracle/kit" else a for a in rest]
        script = os.path.join(m["/oracle/check"][0], "oracle.py")
        r = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", script] + rest, capture_output=True, text=True,
                           encoding="utf-8")
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        sys.exit(r.returncode)
    if "/work" in m and "ralph-iteration" not in args:
        record(kind="holds")
        names = [x.split("=", 1)[0] for x in open(values("--env-file")[0], encoding="utf-8").read().splitlines() if x]
        names += [v.split("=", 1)[0] for v in values("--env")] + ["PATH"]
        print("\n".join(sorted(names)) + "\n---\n" + "\n".join(sorted(list(m) + ["/proc", "/tmp"])))
        sys.exit(0)
    if "-c" in args:
        record(kind="isolation")
        sys.stderr.write("OSError: [Errno 101] Network is unreachable\n")
        sys.exit(1)
    counter = os.path.join(home, "agent_calls")
    n = int(open(counter).read()) + 1 if os.path.exists(counter) else 1
    open(counter, "w").write(str(n))
    env_file = values("--env-file")[0]
    lines = open(env_file, encoding="utf-8").read().splitlines()
    mode = None if os.name == "nt" else oct(os.stat(env_file).st_mode & 0o777)
    record(kind="agent", n=n, env_names=[x.split("=", 1)[0] for x in lines], env_mode=mode,
           key_ok=any(x == "GOOGLE_API_KEY=" + world["key"] for x in lines), mounts=m)
    step = world["agent"][min(n, len(world["agent"])) - 1]
    time.sleep(step.get("sleep", 0))
    ws = m["/work"][0]
    if "file" in step:
        open(os.path.join(ws, "shared", "desk_calc.py"), "wb").write(step["file"].encode("utf-8"))
    if step.get("tick"):
        plan = os.path.join(ws, "fix_plan.md")
        text = open(plan, encoding="utf-8").read().replace("- [ ] ", "- [x] ", 1)
        open(plan, "wb").write(text.encode("utf-8"))
    if "stdout" in step:
        sys.stdout.write(step["stdout"])
    else:
        print(json.dumps({"response": step.get("response", "done"), "stats": world["stats"]}))
    sys.exit(step.get("exit", 0))
record(kind="unexpected")
sys.stderr.write("stub docker: unexpected call\n")
sys.exit(99)
'''
STATS = {"models": {"gemini-3.6-flash": {"api": {"totalRequests": 4, "totalErrors": 0},
                                         "tokens": {"prompt": 40000, "candidates": 900, "total": 44000,
                                                    "cached": 20000, "thoughts": 3000, "tool": 100}},
                    "gemini-3.1-flash-lite": {"api": {"totalRequests": 1},
                                              "tokens": {"prompt": 2000, "candidates": 10, "cached": 0,
                                                         "thoughts": 0, "tool": 0}}},
         "tools": {"totalCalls": 3, "byName": {"read_file": {"count": 2}, "replace": {"count": 1}}},
         "files": {"totalLinesAdded": 11, "totalLinesRemoved": 1}}


class Stubbed(Scratch):
    def setUp(self):
        super().setUp()
        self.home, self.bin = self.tmp / "stub", self.tmp / "stub" / "bin"
        for d in (self.home, self.bin, self.home / "calls"):
            d.mkdir(exist_ok=True)
        (self.home / "stub.py").write_text(STUB, encoding="utf-8")
        stub = self.home / "stub.py"
        if os.name == "nt":                                                 # text mode writes CRLF here
            self.docker = str(self.bin / "docker.cmd")
            Path(self.docker).write_text(f'@echo off\n"{sys.executable}" "{stub}" docker %*\nexit /b %errorlevel%\n',
                                         encoding="utf-8")
        else:
            self.docker = str(self.bin / "docker")
            Path(self.docker).write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(stub))} "
                                         f"docker \"$@\"\n", encoding="utf-8")
            os.chmod(self.docker, 0o755)
        self.addCleanup(lambda: os.environ.pop("RALPH_STUB_HOME", None))
        os.environ["RALPH_STUB_HOME"] = str(self.home)
        self.start = ralph.cut(ralph.kit_text())
        self.world = {"key": KEY, "stats": STATS, "agent": []}

    def scenario(self, *steps, **world) -> None:
        self.world.update(world, agent=list(steps))
        (self.home / "scenario.json").write_text(json.dumps(self.world), encoding="utf-8")

    def file_with(self, version: str) -> str:
        return ralph.splice(self.start, VERSIONS[version])

    def calls(self, kind=None) -> list:
        out = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.home / "calls").glob("*.json"))]
        return [c for c in out if kind is None or c.get("kind") == kind]

    def live(self, timeout_s=120, **caps) -> dict:
        lines, say = quiet()
        self.lines = lines
        agent = ralph.GeminiCliAgent(self.docker, "documind-ralph", "gemini-3.6-flash", KEY, None, timeout_s)
        oracle = ralph.Oracle("strong", image="documind-ralph", docker=self.docker)
        return ralph.run_loop(ralph.TASKS["deadline"], agent, oracle, out=self.tmp / "runs", say=say, **caps)


class Live(Stubbed):
    def test_the_live_loop_through_the_stub(self):
        self.scenario({"file": self.file_with("placeholder"), "tick": True},
                      {"file": self.file_with("reference"), "tick": True, "response": "Done.\n" + ralph.DONE})
        s = self.live(max_iters=5, budget_inr=100)
        self.assertEqual((s["stopped_by"], [r["oracle"] for r in s["iterations"]]), ("oracle_passed", ["FAIL", "PASS"]))
        self.assertTrue(s["billed"])
        priced = ralph.price_stats(STATS)
        self.assertEqual(s["iterations"][0]["tokens"], {k: priced[k] for k in ("in", "cached", "out", "thinking")})
        self.assertAlmostEqual(s["spent_inr"], 2 * priced["inr"], places=5)
        self.assertTrue(s["iterations"][1]["claimed_done"])
        agents = self.calls("agent")
        self.assertEqual([c["n"] for c in agents], [1, 2])
        for c in agents:
            self.assertEqual(c["env_names"], ["GOOGLE_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI"])
            self.assertTrue(c["key_ok"])
            if os.name != "nt":
                self.assertEqual(c["env_mode"], "0o600")
            self.assertEqual(c["mounts"]["/ralph/PROMPT.md"], [str(ralph.ASSETS / "PROMPT.md"), True])
            self.assertEqual(c["mounts"]["/etc/gemini-cli/settings.json"], [str(ralph.ASSETS / "settings.json"), True])
            self.assertEqual(c["mounts"]["/work"], [s["workspace"], False])
            self.assert_agent_line(c["args"])
        oracles = self.calls("oracle")
        self.assertEqual(len(oracles), 4)                                 # the start, two iterations, the record
        for c in oracles:
            a = c["args"]
            self.assertEqual(a[a.index("--network") + 1], "none")
            self.assertIn("--read-only", a)
            self.assertTrue(all(",readonly" in m for m in (a[i + 1] for i, x in enumerate(a) if x == "--mount")))
            self.assertNotIn("--env-file", a)
        self.assertFalse((Path(s["run"]) / "agent.env").exists())
        everything = "\n".join(self.lines) + json.dumps(self.calls()) + "".join(
            p.read_text(encoding="utf-8") for p in Path(s["run"]).rglob("*") if p.is_file() and p.suffix in (
                ".json", ".txt", ".patch", ".md"))
        self.assertNotIn(KEY, everything)

    def assert_agent_line(self, a: list) -> None:
        line = " ".join(a)
        self.assertEqual(a[:2], ["run", "--rm"])
        for words in ("--cap-drop ALL", "--security-opt no-new-privileges", "--read-only", "--pids-limit 256",
                      "--memory 2g", "--env RALPH_MODEL=gemini-3.6-flash", "documind-ralph ralph-iteration"):
            self.assertIn(words, line)
        for never in ("gcloud", "GOOGLE_APPLICATION_CREDENTIALS", "docker.sock", "--privileged", "--network host",
                      KEY, "application_default_credentials"):
            self.assertNotIn(never, line)
        self.assertEqual(a.count("--env-file"), 1)

    def test_a_cut_iteration_stops_the_loop(self):
        self.scenario({"sleep": 5})
        s = self.live(timeout_s=1.5, max_iters=3, budget_inr=50)
        self.assertEqual((s["stopped_by"], len(s["iterations"])), ("iteration_timeout", 1))
        self.assertIsNone(s["iterations"][0]["inr"])
        self.assertEqual({c["kind"] for c in self.calls() if c["kind"] in ("kill", "rm")}, {"kill", "rm"})
        self.assertFalse((Path(s["run"]) / "agent.env").exists())

    def test_an_iteration_with_no_stats_stops_the_loop(self):
        self.scenario({"stdout": "Error: authentication failed\n", "exit": 1})
        s = self.live(max_iters=3, budget_inr=50)
        self.assertEqual((s["stopped_by"], len(s["iterations"])), ("agent_failed", 1))
        self.assertEqual(s["iterations"][0]["error"], "exit 1")

    def test_naming_the_public_copy_undoes_the_iteration(self):
        self.scenario({"file": self.file_with("reference"),
                       "response": "I fetched https://raw.githubusercontent.com/x/y/main/commands/ralph/oracle.py"},
                      {"file": self.file_with("reference")})
        s = self.live(max_iters=3, budget_inr=50)
        self.assertIn("named githubusercontent.com", s["iterations"][0]["undone"])
        self.assertEqual(s["iterations"][1]["oracle"], "PASS")


class LiveCommand(Stubbed):
    def main(self, *argv, env=None, which=True) -> tuple[int, str]:
        """ralph.main in this process, with the stub as the only docker shutil.which can find; env values of None
        are unset for the call, and everything is put back after it."""
        lines, say = quiet()
        env = {"RALPH_API_KEY": KEY, "RALPH_BUDGET_INR": None, **(env or {})}
        with mock.patch.dict(os.environ, {k: v for k, v in env.items() if v is not None}), \
                mock.patch.object(ralph.shutil, "which", lambda name: self.docker if which else None):
            for k in [k for k, v in env.items() if v is None]:
                os.environ.pop(k, None)
            code = ralph.main(list(argv), say)
        return code, "\n".join(lines)

    def test_the_live_loop_refuses_to_start(self):
        self.scenario(image=True)
        code, out = self.main("loop", env={"RALPH_BUDGET_INR": None})
        self.assertEqual(code, 2)
        self.assertIn("no default spend", out)
        code, out = self.main("loop", "--budget-inr", "20", env={"RALPH_API_KEY": None})
        self.assertEqual(code, 2)
        self.assertIn("RALPH_API_KEY is not set", out)
        code, out = self.main("loop", "--budget-inr", "20", env={"RALPH_API_KEY": '{"type": "service_account", '
                                                                                  '"private_key": "x"}'})
        self.assertEqual(code, 2)
        self.assertIn("never a key file", out)
        code, out = self.main("loop", "--budget-inr", "20", which=False)
        self.assertEqual(code, 2)
        self.assertIn("docker is not on PATH", out)
        self.scenario(image=False)
        code, out = self.main("loop", "--budget-inr", "20")
        self.assertEqual(code, 2)
        self.assertIn("make ralph-image", out)
        self.scenario(image=True)
        code, out = self.main("loop", "--budget-inr", "20", "--model", "gemini 3; rm -rf /")
        self.assertEqual(code, 2)
        self.assertIn("is not a model name", out)
        self.assertFalse(self.calls("agent"))

    def test_the_dry_run_prints_both_lines_and_starts_nothing(self):
        code, out = self.main("loop", "--dry-run", "--project", "documind-ai-YOUR-ID")
        self.assertEqual(code, 0)
        self.assertIn("ralph-iteration", out)
        self.assertIn("--network none", out)
        self.assertIn("GOOGLE_API_KEY, GOOGLE_GENAI_USE_VERTEXAI, GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION", out)
        self.assertNotIn(KEY, out)
        self.assertNotIn("documind-ai-YOUR-ID", out)                      # the project is a value, never printed
        self.assertFalse(self.calls())

    def test_the_probe(self):
        self.scenario({"response": "OK"}, {"response": "NO-WEB-TOOL"}, image=True, label="9.9.9")
        code, out = self.main("probe")
        self.assertEqual(code, 0)
        self.assertIn("2. the ralph image's Gemini CLI: observed - version 9.9.9 (its label)", out)
        self.assertIn("refused, as it must be", out)
        self.assertIn("4. what the agent's container holds: observed - env names ['GOOGLE_API_KEY', "
                      "'GOOGLE_GENAI_USE_VERTEXAI', 'HOME', 'PATH', 'RALPH_MODEL']; mounts ['/etc/gemini-cli/settings.json',"
                      " '/proc', '/ralph/PROMPT.md', '/tmp', '/work']", out)
        self.assertIn("5. one headless call: not tested - add YES=1", out)
        self.assertFalse(self.calls("agent"))
        holds = self.calls("holds")[0]["args"]
        self.assertEqual(holds[holds.index("documind-ralph") + 1:holds.index("documind-ralph") + 3], ["sh", "-c"])
        self.assertNotIn("probe-dummy-not-a-key", out)
        code, out = self.main("probe", "--yes")
        self.assertEqual(code, 0)
        self.assertIn("5. one headless call: observed", out)
        self.assertIn("'gemini-3.1-flash-lite', 'gemini-3.6-flash'", out)
        self.assertIn("6. the web tools excluded: observed", out)
        self.assertEqual(len(self.calls("agent")), 2)
        self.assertNotIn(KEY, out)


# ----------------------------------------------------------------------------- Gemini CLI's output, priced
class Parsing(Scratch):
    def test_the_stats_are_priced_at_list_price(self):
        p = ralph.price_stats(STATS)
        flash = prices.inr(prices.usd("gemini-3.6-flash", 40100, 3900, 20000))
        lite = prices.inr(prices.usd("gemini-3.1-flash-lite", 2000, 10, 0))
        self.assertAlmostEqual(p["inr"], flash + lite, places=9)
        self.assertEqual((p["in"], p["cached"], p["out"], p["thinking"]), (42100, 20000, 910, 3000))
        self.assertEqual(p["models"]["gemini-3.6-flash"]["requests"], 4)
        self.assertAlmostEqual(flash, (20100 * 1.50 + 20000 * 0.15 + 3900 * 7.50) / 1e6 * 85, places=9)
        self.assertIsNone(ralph.price_stats(None))
        self.assertIsNone(ralph.price_stats({"models": {}}))
        self.assertIsNone(ralph.price_stats({"models": {"x": "not a dict"}}))

    def test_the_json_is_found_after_any_noise(self):
        body = json.dumps({"response": "ok\nRALPH_DONE", "stats": STATS}, indent=2)
        self.assertEqual(ralph.parse_cli_json(body)["response"], "ok\nRALPH_DONE")
        self.assertEqual(ralph.parse_cli_json("Loaded cached credentials.\n" + body)["stats"], STATS)
        self.assertIsNone(ralph.parse_cli_json("Error: no auth"))
        self.assertIsNone(ralph.parse_cli_json(""))

    def test_the_key_and_the_env_file(self):
        self.assertIsNone(ralph.key_problem(KEY))
        self.assertIn("not set", ralph.key_problem(""))
        self.assertIn("never a key file", ralph.key_problem('{"private_key": "x"}'))
        self.assertIn("space", ralph.key_problem("two words"))
        self.assertIn("names a file", ralph.key_problem(str(KIT / ralph.SCOPE)))
        path = self.tmp / "agent.env"
        ralph.write_env_file(path, {"GOOGLE_API_KEY": KEY, "GOOGLE_GENAI_USE_VERTEXAI": "true"})
        self.assertEqual(path.read_bytes(), f"GOOGLE_API_KEY={KEY}\nGOOGLE_GENAI_USE_VERTEXAI=true\n".encode())
        if os.name != "nt":
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(ralph.Refused):
            ralph.write_env_file(path, {"GOOGLE_API_KEY": "a\nb"})


# ----------------------------------------------------------------------------- make ralph-check on a change
class CheckCommand(Scratch):
    def check(self, *argv) -> tuple[int, str]:
        lines, say = quiet()
        return ralph.main(["check", *argv], say), "\n".join(lines)

    def test_the_seeds_table(self):
        code, out = self.check("--write-patches", str(self.tmp / "patches"))
        self.assertEqual(code, 0, out)
        self.assertIn("every verdict is the one commands/ralph/seeds.json labels it with", out)
        self.assertIn("the weak one passes 2: placeholder, date_contract", out)
        self.assertEqual(sorted(p.name for p in (self.tmp / "patches").iterdir()),
                         sorted(["reference.patch"] + [f"{s['name']}.patch" for s in SEEDS["seeds"]]))
        code, out = self.check("--patch", str(self.tmp / "patches" / "placeholder.patch"))
        self.assertEqual(code, 1)
        self.assertIn("applies to the task's start", out)
        self.assertIn("weak oracle (desk_calc's own selftest): PASS", out)
        self.assertIn("strong oracle: FAIL", out)
        code, out = self.check("--patch", str(self.tmp / "patches" / "reference.patch"))
        self.assertEqual(code, 0, out)

    def test_a_patch_against_the_kits_own_file_and_one_that_fits_neither(self):
        kit = ralph.kit_text()
        theirs = ralph.splice(kit, VERSIONS["calendar_days"])
        patch = "".join(difflib.unified_diff(kit.splitlines(True), theirs.splitlines(True), "a/shared/desk_calc.py",
                                             "b/shared/desk_calc.py"))
        (self.tmp / "kit.patch").write_bytes(patch.encode("utf-8"))
        code, out = self.check("--patch", str(self.tmp / "kit.patch"))
        self.assertEqual(code, 1)
        self.assertIn("applies to the kit's own file", out)
        (self.tmp / "other.patch").write_bytes(b"--- a/shared/desk_calc.py\n+++ b/shared/desk_calc.py\n@@ -1,1 +1,1 @@\n"
                                               b"-no such line\n+another\n")
        code, out = self.check("--patch", str(self.tmp / "other.patch"))
        self.assertEqual(code, 2)
        self.assertIn("applies neither", out)

    def test_a_workspace_left_by_hand(self):
        lines, say = quiet()
        self.assertEqual(ralph.main(["workspace", "--out", str(self.tmp)], say), 0)
        run_dir = next(self.tmp.iterdir())
        ws = run_dir / "workspace"
        scope = ws / ralph.SCOPE
        scope.write_bytes(ralph.splice(scope.read_text(encoding="utf-8"), VERSIONS["reference"]).encode("utf-8"))
        code, out = self.check("--workspace", str(ws))
        self.assertEqual(code, 0, out)
        self.assertIn("strong oracle: PASS", out)
        hand = (run_dir / "by-hand.patch").read_text(encoding="utf-8")
        self.assertIn("+    due = cases.working_days_after(start, WAGE_DAYS)", hand)
        scope.write_bytes(scope.read_bytes().replace(b"WAGE_DAYS = 2 ", b"WAGE_DAYS = 3 "))
        code, out = self.check("--workspace", str(ws))
        self.assertIn("NOTE: the change also alters what shared/desk_calc.py does outside statutory_deadline", out)


if __name__ == "__main__":
    unittest.main()
