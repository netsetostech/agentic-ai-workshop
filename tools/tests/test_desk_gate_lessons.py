"""The Desk's hard gate against the lessons' own questions (the authoring repository only: the learner kit has no
lessons/). Every tenant has the gate's rules once the Desk is deployed in lesson 5.6, unless an operator writes off,
so no question a lesson sends - a build.py literal or a lane script's, on any tenant - may get the gate's fixed reply
or be masked. The kit's half, deploy/commands/tests/test_desk_rules.py, covers the smokes and the demos; this file
reuses its extractor, so a new lesson question joins the set by itself.
"""
import glob
import importlib.util
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "deploy"
if str(KIT) not in sys.path:
    sys.path.insert(0, str(KIT))

from shared import desk_rules  # noqa: E402

_spec = importlib.util.spec_from_file_location("kit_desk_rules_test", KIT / "commands" / "tests" / "test_desk_rules.py")
kit_test = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kit_test)


def lesson_questions() -> dict[str, list[str]]:
    files = sorted(glob.glob(str(ROOT / "lessons" / "*" / "*" / "build.py")) +
                   glob.glob(str(ROOT / "lessons" / "*" / "*" / "lane*.py")))
    return {os.path.relpath(f, ROOT): kit_test.questions_in_python(Path(f).read_text(encoding="utf-8")) for f in files}


class LessonQuestionsTests(unittest.TestCase):
    def test_no_lesson_question_fires_or_is_masked(self):
        found = lesson_questions()
        self.assertGreaterEqual(len(found), 60, "every lesson's build.py, and the lane scripts")
        self.assertTrue(any(k.endswith("lane181.py") for k in found))
        self.assertGreater(sum(len(v) for v in found.values()), 100)
        fired = [(f, q[:80], desk_rules.gate(q)) for f, qs in found.items() for q in qs if desk_rules.gate(q)]
        masked = [(f, q[:80], desk_rules.mask(q)[1]) for f, qs in found.items() for q in qs if desk_rules.mask(q)[1]]
        self.assertEqual(fired, [], "a lesson question would get the gate's fixed reply (every tenant has the rules)")
        self.assertEqual(masked, [], "a lesson question would be masked (every tenant has the rules)")

    def test_the_lessons_synthetic_aadhaar_numbers_fail_verhoeff(self):
        # 4.8 shows 2234 5678 9012 and 9.1 sends 2345 6789 0123 (to the gateway, not through the door); neither is
        # a valid Aadhaar, so neither is masked if it ever reaches rag-api.
        for rel, shown in (("lessons/04-evals-safety/4.8-dlp-guard-audit/build.py", "2234 5678 9012"),
                           ("lessons/09-serving/9.1-gateway-routes/build.py", "2345 6789 0123")):
            self.assertIn(shown, (ROOT / rel).read_text(encoding="utf-8"), rel)
            self.assertEqual(desk_rules.mask(f"My Aadhaar is {shown}")[1], [], shown)


if __name__ == "__main__":
    unittest.main()
