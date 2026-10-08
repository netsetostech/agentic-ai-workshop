"""setup/update_kit.py against real Git repositories: an origin, a learner's clone, and a new kit commit to pull.

The learner opens the kit in PyCharm, which writes .idea/ into it; that folder, like any untracked file, must not
block an update (git pull refuses before it would overwrite one), while an edit to a tracked file still must.
"""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SETUP = Path(__file__).resolve().parents[1] / "setup"
KIT = Path(__file__).resolve().parents[2]
LEARNER = "https://github.com/netsetos/agents_workshop_learner.git"


def load_updater():
    spec = importlib.util.spec_from_file_location("update_kit_under_test", SETUP / "update_kit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-C", str(cwd), *args],
                          check=True, capture_output=True, text=True).stdout.strip()


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class UpdateKitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        origin, author = self.tmp / "origin.git", self.tmp / "author"
        git(self.tmp, "init", "-q", "--bare", "-b", "main", str(origin))
        git(self.tmp, "clone", "-q", str(origin), str(author))
        (author / "README.md").write_text("kit v1\n")
        git(author, "add", "README.md")
        git(author, "commit", "-q", "-m", "v1")
        git(author, "push", "-q", "origin", "HEAD:main")
        self.kit = self.tmp / "kit"
        git(self.tmp, "clone", "-q", "-b", "main", str(origin), str(self.kit))
        (author / "README.md").write_text("kit v2\n")
        git(author, "commit", "-q", "-am", "v2")
        git(author, "push", "-q", "origin", "HEAD:main")
        self.new_head = git(author, "rev-parse", "HEAD")
        self.updater = load_updater()

    def update(self):
        real = subprocess.run

        def run(args, **kwargs):          # the clone's origin is a local path; answer as the learner repo
            if list(args[-3:]) == ["remote", "get-url", "origin"]:
                return SimpleNamespace(stdout=LEARNER + "\n")
            return real(args, **kwargs)

        with patch.object(self.updater, "load_config", return_value=SimpleNamespace(kit_root=self.kit)), \
                patch.object(self.updater.subprocess, "run", side_effect=run):
            self.updater.main()

    def test_the_ides_folder_and_other_untracked_files_do_not_block(self):
        (self.kit / ".idea").mkdir()
        (self.kit / ".idea" / "workspace.xml").write_text("<project/>")
        (self.kit / "my_notes.md").write_text("mine\n")
        self.update()
        self.assertEqual(git(self.kit, "rev-parse", "HEAD"), self.new_head)
        self.assertEqual((self.kit / "my_notes.md").read_text(), "mine\n")

    def test_an_edited_tracked_file_still_blocks(self):
        (self.kit / "README.md").write_text("my edit\n")
        with self.assertRaisesRegex(RuntimeError, "local changes"):
            self.update()
        self.assertNotEqual(git(self.kit, "rev-parse", "HEAD"), self.new_head)
        self.assertEqual((self.kit / "README.md").read_text(), "my edit\n")

    def test_the_kit_ignores_the_ide_folders(self):
        ignored = (KIT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".idea/", ignored)
        self.assertIn(".vscode/", ignored)


if __name__ == "__main__":
    unittest.main()
