"""The page checker: every authored lesson's page against the manifest, the kit and the page rules.

    python pagekit/check_lesson.py             # every lesson with a page
    python pagekit/check_lesson.py 5.1 4.4     # some

A line starting with '!' is a failure, and the exit code is 1 if any page has one. What a page is held to:
  - the title, the hero crumb and the footer name the lesson the manifest names
  - no "Check yourself" quizzes and no exercise cards
  - every substantive line in a window labelled with a kit file is in deploy/ verbatim, so a kit change that
    alters a quoted line fails here until the page is rebuilt (python pagekit/build.py <lesson>)
  - every make target in a code block is a target of deploy/Makefile or deploy/mk/*.mk
  - the template's head and height script are present, the divs balance, table cells carry data-label
  - nothing private: no real project id or number, no key, no personal mailbox (tools/leakscan.py)
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pagekit.pagebuild import KIT, MANIFEST, module_key, page_path  # noqa: E402
from pagekit.demo_links import annotate, strip_links
from tools.leakscan import deny_strings, scan_text  # noqa: E402

MAKEFILE = (KIT / "Makefile").read_text(encoding="utf-8") + "".join(
    "\n" + p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
MAKE_TARGETS = set(re.findall(r"^([a-z][A-Za-z0-9_./-]*):", MAKEFILE, re.M))

# every line of every kit source, whitespace-collapsed, for the verbatim check
KIT_LINES = set()
for pattern in ("*.py", "*.tf", "*.sh", "*.yaml", "*.yml", "*.mk", "*.sql", "Makefile"):
    for p in KIT.rglob(pattern):
        if "__pycache__" in p.parts:
            continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            KIT_LINES.add(" ".join(line.split()))

TAG = re.compile(r"</?(?:span|pre|code|br|b|strong|em)\b[^>]*>", re.I)
KIT_LABEL = re.compile(r"(\.py|\.tf|\.sh|\.yaml|\.yml|\.mk|\.sql|Makefile)", re.I)
NOT_EXCERPTS = ("bash", "shell", "python", "text", "log", "json", "output", "expected", "gcloud", "make")
MIN_KB = 60  # a floor that catches a near-empty page; teaching content has no upper limit (26 September 2026)
MAX_IDE_LINK_KB = 10  # Generated navigation has a separate bound.


def windows(page: str):
    rx = r'<div class="cw"><div class="ch-bar"><span>(.*?)</span>.*?<pre[^>]*>(.*?)</pre>'
    for m in re.finditer(rx, page, re.S):
        yield html.unescape(TAG.sub("", m.group(1))), html.unescape(TAG.sub("", m.group(2)))


def verbatim(page: str):
    """(lines checked, misses) over the windows labelled with a kit file."""
    checked, misses = 0, []
    for label, code in windows(page):
        head = label.strip()
        if head.lower().startswith(NOT_EXCERPTS):
            continue        # commands, learner code, sample output: not excerpts
        if not KIT_LABEL.search(head):
            continue
        for line in code.splitlines():
            s = " ".join(line.split())
            if len(s) < 25 or s.startswith(("#", "...", ">>>", "$")):
                continue
            checked += 1
            if s not in KIT_LINES:
                misses.append(f"{head[:60]}: {s[:90]}")
    return checked, misses


LESSON_IDS = {lid for m in MANIFEST["modules"].values() for lid in m["lessons"]}
MODULE_NUMBERS = {int(k) for k in MANIFEST["modules"] if k != "B"}
NOT_PROSE = re.compile(r"<pre\b.*?</pre>|<code\b.*?</code>|<script\b.*?</script>|<style\b.*?</style>", re.S | re.I)
LID = r"(?:B|\d{1,2})\.\d{1,2}"


def references(page: str) -> list:
    """Lessons and modules the page's prose names that the manifest does not have. Since the Cohort 2 renumbering a
    stale number would silently point at another lesson, so every 'Lesson N.M' and 'Module N' must exist."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", NOT_PROSE.sub(" ", page)))
    bad = set()
    for m in re.finditer(r"\b[Ll]essons?\s+(" + LID + r"(?:\s*(?:,|and|or|to|–|-)\s*" + LID + r")*)", text):
        bad.update(f"lesson {lid}" for lid in re.findall(LID, m.group(1)) if lid not in LESSON_IDS)
    for m in re.finditer(r"\bModules?\s+(\d{1,2})\b(?!\.\d)", text):
        if int(m.group(1)) not in MODULE_NUMBERS:
            bad.add(f"Module {m.group(1)}")
    return sorted(bad)


COMMAND_WINDOWS = ("bash", "shell", "make", "gcloud")


def make_targets(page: str) -> set:
    """make targets a learner is told to run: inline <code>, and the command windows (labelled bash, shell, make,
    gcloud), one element at a time with shell comments cut. Kit excerpts are not scanned: their prose ("would make
    an old version current") is checked verbatim against the kit instead."""
    texts = [html.unescape(TAG.sub("", c)) for c in re.findall(r"<code[^>]*>(.*?)</code>", page, re.S)]
    texts += [code for label, code in windows(page) if label.strip().lower().startswith(COMMAND_WINDOWS)]
    found = set()
    for text in texts:
        for line in text.splitlines():
            line = re.sub(r"(^|\s)#.*$", "", line)
            found.update(re.findall(r"\bmake[ \t]+([a-z][a-z0-9_-]*)", line))
    return found


def check(lid: str) -> list:
    module = MANIFEST["modules"][module_key(lid)]
    lesson = module["lessons"][lid]
    path = page_path(lid)
    out = [f"== {lid} {lesson['name']}"]
    if not path.exists():
        return out + [f"  ! missing {path.relative_to(ROOT).as_posix()}"]
    page = path.read_text(encoding="utf-8")
    kb = path.stat().st_size / 1024
    teaching_kb = len(strip_links(page).encode('utf-8')) / 1024
    navigation_kb = kb - teaching_kb
    title_m = re.search(r"<title>(.*?)</title>", page, re.S)
    title = html.unescape(title_m.group(1).strip()) if title_m else ""
    steps = page.count('class="step"')
    quizzes, cards = page.count('class="quiz"'), page.count('class="exercise-card"')
    out.append(f"  {path.name}: {kb:.0f} KB, {steps} steps")
    if not title.startswith(f"Lesson {lid} ") or "| Netsetos" not in title or lesson["name"] not in title:
        out.append(f"  ! title {title[:90]!r} (want: Lesson {lid} {lesson['name']} ... | Netsetos)")
    if quizzes or cards:
        out.append(f"  ! {quizzes} quizzes and {cards} exercise cards: the page has neither")
    word = module["name"].split(" - ")[0].strip()
    crumb = (f"Basics &middot; Lesson {lid}" if module_key(lid) == "B"
             else f"Module {int(lid.split('.')[0])} &middot; {word} &middot; Lesson {lid}")
    if crumb not in page:
        out.append(f"  ! hero crumb (want {crumb})")
    if f"Lesson {lid}" not in page.split('class="footer"')[-1][:400]:
        out.append("  ! the footer does not name the lesson")
    for ref in references(page):
        out.append(f"  ! names {ref}, which the manifest does not have")
    if teaching_kb < MIN_KB:
        out.append(f"  ! teaching content {teaching_kb:.1f} KB, under the {MIN_KB} KB floor")
    if navigation_kb > MAX_IDE_LINK_KB or page != annotate(lid, page):
        out.append(f"  ! IDE navigation must match the generated links and fit {MAX_IDE_LINK_KB} KB (actual {navigation_kb:.1f})")
    rows = re.findall(r"<tr>(.*?)</tr>", page, re.S)
    bare = sum(1 for r in rows if r.count("<td") > 1 and r.count("data-label") < r.count("<td") - 1)
    if bare:
        out.append(f"  ! {bare} table rows without data-label (the phone layout needs it)")
    if "COLAB-LINK" in page:
        out.append("  ! Colab markers present")
    if "family=DM+Sans" not in page or "<style>" not in page:
        out.append("  ! the template head is missing")
    if "netsetos-embed-height" not in page:
        out.append("  ! the template's height script is missing")
    bad = sorted(t for t in make_targets(page) if t not in MAKE_TARGETS)
    if bad:
        out.append(f"  ! make targets not in deploy/Makefile or deploy/mk/*.mk: {bad}")
    checked, misses = verbatim(page)
    out.append(f"  kit excerpts: {checked - len(misses)} of {checked} lines verbatim")
    for m in misses[:8]:
        out.append(f"  ! not in the kit: {m}")
    for what, text in scan_text(page, DENY):
        out.append(f"  ! {what}: {text}")
    if page.count("<div") != page.count("</div>"):
        out.append(f"  ! div balance {page.count('<div')} open, {page.count('</div>')} closed")
    awaiting = page.count("[awaiting the author&#x27;s run:") + page.count("[awaiting the author's run:")
    if awaiting:   # a note, not a finding: pagebuild.recorded() fills these from the lesson's data/ once the run is in
        out.append(f"  note: {awaiting} output(s) awaiting the author's run")
    return out


def authored() -> list:
    return [lid for m in MANIFEST["modules"].values() for lid, les in m["lessons"].items()
            if les.get("slug") and les.get("topic_filename") and page_path(lid).exists()]


DENY = deny_strings()


def main(argv: list) -> int:
    failed = 0
    for lid in argv or authored():
        lines = check(lid)
        bad = any(line.lstrip().startswith("!") for line in lines)
        failed += bad
        print("\n".join(lines) + ("" if bad else "\n  ok"))
    print(f"\n{failed} page(s) with findings" if failed else "\nevery page ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
