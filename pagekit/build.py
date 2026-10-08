"""Build lesson pages from their sources.

    python pagekit/build.py 5.1          # one lesson
    python pagekit/build.py 4.2 4.3      # some
    python pagekit/build.py --all        # every lesson with a build.py, in manifest order

Each lesson's build.py reads its parts, the kit and the template and writes its page next to itself.
Lesson 1.1 has no build.py: its page is its own source, and every other page copies its setup section,
so rebuild the rest after editing 1.1's setup.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pagekit.pagebuild import MANIFEST, lesson_dir  # noqa: E402


def buildable() -> list[str]:
    out = []
    for module in MANIFEST["modules"].values():
        for lid, lesson in module["lessons"].items():
            if lesson.get("slug") and (lesson_dir(lid) / "build.py").exists():
                out.append(lid)
    return out


def main(argv: list[str]) -> int:
    known = buildable()
    want = known if argv == ["--all"] else argv
    if not want:
        print(__doc__)
        return 2
    unknown = [lid for lid in want if lid not in known]
    if unknown:
        print(f"no build.py for {unknown}; lessons with one: {', '.join(known)}", file=sys.stderr)
        return 2
    for lid in want:
        runpy.run_path(str(lesson_dir(lid) / "build.py"), run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
