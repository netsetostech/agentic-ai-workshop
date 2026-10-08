# pagekit - how a lesson page is made

| File | What it does |
|---|---|
| `template_head.html`, `template_tail.html` | the page shell every lesson shares: the fonts, the teal CSS, the footer, the auto-height script for the Wix embed |
| `pagebuild.py` | the shared half of every build: paths from the manifest, `block()` (verbatim kit lines), the highlighter, `window()`, `filler()`, the assembly, `finish()` |
| `basics_setup.html` | the laptop setup every Basics page carries in place of the lane's shell setup (there is no lane yet): Python 3.12 in `~/basics-venv`, numpy and the kit's google-genai pin, then the project from lesson 0.1 for the cells that call Gemini |
| `build.py` | the runner: `python pagekit/build.py 5.1`, or `--all` |
| `check_lesson.py` | the page checker: the manifest's names, the page rules, every excerpt verbatim, real make targets, nothing private |
| `audit_responsive.py` | the responsive auditor (40 gates, run per document including every srcdoc) |
| `audit_pages.py` | the auditor over every page, failing on any FAIL except the listed known exceptions |

## A lesson's build

`lessons/NN-module/N.M-slug/build.py` holds only what is the lesson's own:

- `title` and `EXTRA_CSS` (the scrollbar rule, the read-only badge, the lesson's widget styles);
- `EXCERPTS = {name: (label, block("path/in/deploy", "first line", end=... | n=...))}`: each becomes a read-only window
  wherever a part says `@@name@@`;
- numbers computed from the kit at build time, dropped into the parts where they say `%%NAME%%`;
- `JS`, the widget script, placed before `</body>`;
- the order of the parts: `a`, then 1.1's setup section (`setup_section()`; a Basics page takes `basics_setup_section()`),
  then `b` and `c`;
- outputs only a live run can print: `recorded(lesson, name)` reads them from the lesson's `data/<name>`, recorded once from
  the author's run. Until then the page shows a marked stand-in, `finish()` names every one still awaited, and
  `check_lesson.py` notes the count. The lesson's `RUN_LIST.md` says which command records each file.

`finish()` refuses a page with an unfilled `@@name@@` or `%%NAME%%` and writes the page next to `build.py`. The build is
deterministic: rebuilding an unchanged lesson reproduces its page byte for byte, so `git diff` after a rebuild shows
exactly what a kit or part change did to the page.
