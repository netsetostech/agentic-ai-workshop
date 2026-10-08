"""Offline session regressions; no test here can create cloud resources."""
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from workshop_helpers.artifacts import write_json
from workshop_helpers.config import load_config
from workshop_helpers.session import DemoSession, secret_name
from workshop_helpers.kit import KitAdapter
from workshop_helpers.reconciliation import evaluate, evaluate_widget


class SessionTests(unittest.TestCase):
    """Verify state survives processes without credential leaks or silent replay."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = replace(load_config(), results_dir=self.root / "results", project="test-project")
        self.lesson = self.root / "lesson"
        self.lesson.mkdir()
        self.mapping = {"lesson": "4.4", "source_sha": "source", "persist_variables": ["Q", "VALUE", "SECRET_TOKEN", "MAX_CONTEXT_TOKENS"],
                        "demos": [{"file": "one.py", "id": "one", "heading": "One", "purpose": "Set state", "category": "required", "requires": []},
                                  {"file": "two.py", "id": "two", "heading": "Two", "purpose": "Read state", "category": "required", "requires": ["one"]},
                                  {"file": "finish.py", "id": "finish", "heading": "Finish", "purpose": "Restore", "category": "cleanup", "requires": []}]}
        write_json(self.lesson / "lesson_map.json", self.mapping)
        for name in ("one.py", "two.py", "finish.py"):
            (self.lesson / name).write_text("# test checkpoint\n")

    def open(self, name, **kwargs):
        """Use a real session with temporary evidence and no cloud initialization."""
        return DemoSession(self.lesson / name, live=False, config=self.config, **kwargs)

    def test_basics_and_module_0_lessons_have_their_own_folders(self):
        from workshop_helpers.artifacts import ArtifactStore
        from workshop_helpers.config import lesson_folder
        self.assertEqual(lesson_folder("B.1"), "module_B/lesson_B_1")
        self.assertEqual(lesson_folder("0.2"), "module_00/lesson_0_2")
        self.assertEqual(lesson_folder("12.3"), "module_12/lesson_12_3")
        with self.assertRaises(ValueError):
            lesson_folder("X.1")
        write_json(self.lesson / "lesson_map.json", dict(self.mapping, lesson="B.1"))
        with self.open("one.py") as session:
            self.assertEqual(session.base, self.config.results_dir / "module_B" / "lesson_B_1")
        store = ArtifactStore(self.config, "00", module="B", lesson="B.1")
        self.assertEqual(store.directory.parent.parent, self.config.results_dir / "module_B" / "lesson_B_1")

    def test_state_and_selected_interpreter_survive_new_instances(self):
        old_cwd = Path.cwd()
        with self.open("one.py") as first:
            first.set_environment(Q="same question", SECRET_TOKEN="do-not-persist", MAX_CONTEXT_TOKENS="600")
            self.assertEqual(Path.cwd(), self.config.kit_root)
            self.assertEqual(os.environ["WORKSHOP_PYTHON"], sys.executable)
            directory = first.directory
        self.assertEqual(Path.cwd(), old_cwd)
        state = json.loads((directory / "session.json").read_text())
        self.assertNotIn("do-not-persist", json.dumps(state))
        with self.open("two.py") as second:
            self.assertEqual(second.directory, directory)
            self.assertEqual(os.environ["Q"], "same question")
            self.assertEqual(os.environ["MAX_CONTEXT_TOKENS"], "600")

    def test_wrong_order_and_replay_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "prerequisite"):
            with self.open("two.py"):
                pass
        with self.open("one.py"):
            pass
        with self.assertRaisesRegex(RuntimeError, "already completed"):
            with self.open("one.py"):
                pass
        with self.open("one.py", repeat=True):
            pass

    def test_failure_remains_failed_and_cleanup_still_runs(self):
        with self.assertRaisesRegex(ValueError, "failed observation"):
            with self.open("one.py") as session:
                session.set_environment(Q="recover this run")
                raise ValueError("failed observation")
        with self.assertRaisesRegex(RuntimeError, "prerequisite"):
            with self.open("two.py"):
                pass
        with self.open("finish.py") as session:
            self.assertEqual(session.state["attempts"][0]["status"], "failed")
            self.assertEqual(os.environ["Q"], "recover this run")

    def test_second_process_cannot_share_a_locked_session(self):
        with self.open("one.py"):
            with self.assertRaisesRegex(RuntimeError, "holds"):
                with self.open("finish.py"):
                    pass

    def test_project_change_does_not_reuse_a_fixture(self):
        with self.open("one.py"):
            pass
        other = replace(self.config, project="other-project")
        with self.assertRaisesRegex(RuntimeError, "different project"):
            with DemoSession(self.lesson / "finish.py", live=False, config=other):
                pass

    def test_command_failure_and_timeout_are_visible(self):
        with self.open("one.py") as session:
            with self.assertRaises(subprocess.CalledProcessError):
                session.command([sys.executable, "-c", "print('observed failure'); raise SystemExit(7)"])
            with self.assertRaises(subprocess.TimeoutExpired):
                session.command([sys.executable, "-c", "import time; time.sleep(30)"], timeout=0.2)
            self.assertIn("observed failure", (session.attempt / "command_01.log").read_text())

    @unittest.skipUnless(os.name == "posix" or os.environ.get("WORKSHOP_TEST_BASH"), "Bash integration runs in Linux CI")
    def test_bash_variables_functions_and_failure_are_retained(self):
        with self.open("one.py") as session:
            session.shell("export Q='kept across processes'\nVALUE=7\nshow_value() { echo \"$VALUE\"; }\nexport SECRET_TOKEN=not-saved")
            self.assertNotIn("not-saved", (session.directory / "shell_state.sh").read_text())
        with self.open("two.py") as session:
            self.assertEqual(os.environ["Q"], "kept across processes")
            session.shell("test \"$(show_value)\" = 7\nexport Q='changed'\nprintf '%s\\n' \"$Q\"")
            with self.assertRaises(subprocess.CalledProcessError):
                session.shell("export Q='saved despite failure'\nfalse\necho should-not-run")
            self.assertEqual(os.environ["Q"], "saved despite failure")


class PlannerTests(unittest.TestCase):
    """Keep the offline teaching examples bound to the installed kit's decisions."""

    def test_actual_widget_default_and_variations(self):
        kit = KitAdapter(load_config().kit_root)
        rows = [dict(name="acme/hr_policy_2026.md", bucket="same", ledger="indexed", bytes="same", queued=False),
                dict(name="acme/smoke_note_v1.md", bucket="absent", ledger="indexed", bytes="same", queued=False),
                dict(name="acme/dpdp_act_2023.pdf", bucket="newer", ledger="indexed", bytes="same", queued=False),
                dict(name="acme/new_circular.md", bucket="same", ledger="none", bytes="new", queued=False),
                dict(name="acme/old_policy.md", bucket="same", ledger="withdrawn", bytes="same", queued=False)]
        report = evaluate_widget(kit, rows)
        self.assertEqual(report["summary"]["drift"], 2)
        for name in ("ok", "retire", "touch", "reingest", "withdrawn"):
            self.assertEqual(report["summary"][name], 1)
        rows[3]["bytes"] = "known"
        self.assertEqual(evaluate_widget(kit, rows)["summary"]["backfill"], 1)
        rows[3]["queued"] = True
        self.assertEqual(evaluate_widget(kit, rows)["summary"]["queued"], 1)

    def test_old_queued_generation_does_not_hide_new_upload(self):
        planner = KitAdapter(load_config().kit_root).planner
        objects = [{"name": "acme/cgst_it_bundle.pdf", "generation": "5", "tenant_id": "acme"}]
        claims = {"key": {"status": "queued", "gcs_uri": "gs://b/acme/cgst_it_bundle.pdf", "generation": "4"}}
        self.assertEqual(planner.plan(objects, {}, claims)[0]["action"], "check_bytes")
        objects[0]["generation"] = "4"
        self.assertEqual(planner.plan(objects, {}, claims)[0]["action"], "queued")

    def test_token_budget_is_not_mistaken_for_a_credential(self):
        self.assertTrue(secret_name("IAP_TOKEN"))
        self.assertTrue(secret_name("CHECKPOINT_DSN"))
        self.assertFalse(secret_name("MAX_CONTEXT_TOKENS"))


if __name__ == "__main__":
    unittest.main()
