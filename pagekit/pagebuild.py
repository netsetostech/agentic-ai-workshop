"""The shared half of every lesson's build.py: paths from the manifest, the template, the 1.1 setup
section, verbatim kit excerpts with their highlighting, and the page assembly.

A lesson's build.py keeps only what is its own: the title, its extra CSS, its excerpts, the numbers it
computes from the kit, its widget script and the order of its parts. Run one with
    python pagekit/build.py 5.1          (or --all)
The page is written next to its build.py, under the name the manifest gives it.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "deploy"                  # the DocuMind kit: published as-is to the learner repo
PLAN = ROOT / "plan"
PAGEKIT = ROOT / "pagekit"
MANIFEST = json.loads((ROOT / "course-manifest.json").read_text(encoding="utf-8"))
HEAD = (PAGEKIT / "template_head.html").read_text(encoding="utf-8").splitlines(keepends=True)
TAIL = (PAGEKIT / "template_tail.html").read_text(encoding="utf-8").splitlines(keepends=True)

# the shell setup every page repeats: lesson 1.1's section, from its heading to the step-3 marker
SETUP_FROM = "1.1"
SETUP_START = '<h3 id="setup">'
SETUP_END = '<!-- ============================ STEP 3 ============================ -->'


# ------------------------------------------------------------------ where a lesson lives
def module_key(lid: str) -> str:
    """The manifest key of a lesson's module: 'B' for Basics, otherwise the number padded to two digits ('0.2' -> '00')."""
    major = lid.split(".")[0]
    return major if major == "B" else major.zfill(2)


def lesson_meta(lid: str) -> tuple:
    module = MANIFEST["modules"][module_key(lid)]
    return module, module["lessons"][lid]


def lesson_dir(lid: str) -> Path:
    module, lesson = lesson_meta(lid)
    return ROOT / "lessons" / f"{module_key(lid)}-{module['slug']}" / f"{lid}-{lesson['slug']}"


def page_path(lid: str) -> Path:
    _, lesson = lesson_meta(lid)
    return lesson_dir(lid) / f"Netsetos_GCP_Capstone_{lid}_{lesson['topic_filename']}_WIX.html"


def part(lid: str, name: str) -> str:
    """One of the lesson's prose parts: lessons/.../parts/<name>.html."""
    return (lesson_dir(lid) / "parts" / f"{name}.html").read_text(encoding="utf-8")


def data(lid: str, name: str) -> Path:
    """A file the lesson captured once and builds from: lessons/.../data/<name>."""
    return lesson_dir(lid) / "data" / name


AWAITING = []   # the recorded outputs a build asked for that no live run has recorded yet; finish() names them


def recorded(lid: str, name: str) -> str:
    """What a live run printed, recorded once in the lesson's data/<name>. Until the author's run is recorded, a
    marked stand-in takes its place, and finish() names every one still awaited (the lesson's run list says how)."""
    path = data(lid, name)
    if path.exists():
        return path.read_text(encoding="utf-8").rstrip("\n")
    AWAITING.append(name)
    return f"[awaiting the author's run: data/{name}]"


def kit_runtime_files(pattern: str):
    """Read deployed kit sources without counting teaching copies as implementations.

    Example: kit_runtime_files('*.py') lets an audit identify actual event emitters;
    workshop_demos may quote those same calls but does not deploy another service.
    """
    return (path for path in KIT.rglob(pattern) if path.is_file()
            and not {'workshop_demos', '__pycache__', '.terraform', '.git'}.intersection(path.relative_to(KIT).parts))


def setup_section() -> str:
    from pagekit.demo_links import strip_links
    page = page_path(SETUP_FROM).read_text(encoding="utf-8")
    page = strip_links(page)  # The importing lesson gets its own IDE links at finish().
    return page[page.index(SETUP_START):page.index(SETUP_END)]


def basics_setup_section() -> str:
    """The laptop setup every Basics page repeats, in place of the lane's shell setup (there is no lane yet):
    Python 3.12 in ~/basics-venv with numpy and the kit's google-genai pin, then the project from lesson 0.1 and
    Application Default Credentials for the cells that call Gemini."""
    return (PAGEKIT / "basics_setup.html").read_text(encoding="utf-8")


# ------------------------------------------------------------------ verbatim excerpts, highlighted
KW = re.compile(r"\b(def|return|for|if|elif|else|while|in|and|or|not|import|from|class|None|True|False|raise|with|as|lambda|yield|try|except|finally|pass|break|continue|is|global|async|await)\b")
TOKEN = re.compile(r'(#.*$)|("""[\s\S]*?"""|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(\b\d+(?:_\d+)*(?:\.\d+)?\b)', re.M)


def hl_plain(text: str) -> str:
    esc = html.escape(text)
    esc = KW.sub(lambda m: '<span class="kw">' + m.group(1) + "</span>", esc)
    # the name after def, wrapped AFTER the keyword pass so the span's own "class" is not taken for a keyword
    esc = re.sub(r'<span class="kw">def</span> (\w+)', r'<span class="kw">def</span> <span class="fn">\1</span>', esc)
    return esc


def hl(code: str) -> str:
    """Escape, then colour comments, strings and numbers; keywords and def names in the rest."""
    out, pos = [], 0
    for m in TOKEN.finditer(code):
        out.append(hl_plain(code[pos:m.start()]))
        if m.group(1):
            out.append('<span class="cm">' + html.escape(m.group(1)) + "</span>")
        elif m.group(2):
            out.append('<span class="st">' + html.escape(m.group(2)) + "</span>")
        else:
            out.append('<span class="nu">' + html.escape(m.group(3)) + "</span>")
        pos = m.end()
    out.append(hl_plain(code[pos:]))
    return "".join(out)


def block(rel: str, start: str, end: str | None = None, n: int | None = None, nth: int = 1) -> str:
    """Lines of deploy/<rel>, verbatim: from the nth line containing `start`, for `n` lines, or up to the line
    containing `end`, or up to the next top-level def/class. Trailing blank lines are dropped."""
    lines = (KIT / rel).read_text(encoding="utf-8").splitlines()
    hits = [k for k, line in enumerate(lines) if start in line]
    i = hits[nth - 1]
    if n is not None:
        j = i + n
    elif end is not None:
        j = next(k for k in range(i + 1, len(lines)) if end in lines[k])
    else:
        j = next((k for k in range(i + 1, len(lines)) if lines[k].startswith(("def ", "class "))), len(lines))
    chunk = lines[i:j]
    while chunk and not chunk[-1].strip():
        chunk.pop()
    return "\n".join(chunk)


def window(label: str, code: str) -> str:
    """A read-only code window: the label names the kit file, the badge says it is to read, not to paste."""
    return ('<div class="cw"><div class="ch-bar"><span>' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + hl(code) + "</pre></div>\n")


def filler(excerpts: dict, win=None):
    """fill(part): every @@name@@ in a part becomes the read-only window of excerpts[name] = (label, code)."""
    win = win or window

    def fill(text: str) -> str:
        def rep(m):
            label, code = excerpts[m.group(1)]
            return win(label, code)
        return re.sub(r"@@(\w+)@@", rep, text)
    return fill


# ------------------------------------------------------------------ the page
def assemble(title: str, extra_css: str, body: str, js: str = "") -> str:
    """The template's head with this page's <title> and extra CSS, the body, then the template's tail with the
    page's script before </body>. The tail's first line (the template's own footer) is dropped: every page's
    last part carries its footer."""
    tail_txt = "".join(TAIL[1:])
    assert tail_txt.count("</body>") == 1
    tail_txt = tail_txt.replace("</body>", js + "</body>")
    return "".join(HEAD[:6]) + title + "".join(HEAD[7:213]).replace("</style>", extra_css + "</style>") + "\n" + body + tail_txt


def finish(lid: str, title: str, extra_css: str, body: str, js: str = "") -> Path:
    left = re.findall(r"@@\w+@@|%%\w+%%", body)
    assert not left, f"unfilled tokens: {left}"
    page = assemble(title, extra_css, body, js)
    from pagekit.demo_links import annotate
    page = annotate(lid, page)
    out = page_path(lid)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8", newline="\n")
    steps, quizzes = page.count('class="step"'), page.count('class="quiz"')
    opens, closes = page.count("<div"), page.count("</div>")
    print(f"wrote {out.relative_to(ROOT).as_posix()}: {len(page)} bytes | steps {steps} | quizzes {quizzes} | div {opens}/{closes}")
    if AWAITING:
        print(f"awaiting the author's run ({len(AWAITING)}): {', '.join(AWAITING)}")
    return out
