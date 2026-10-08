"""Build IDE entry points from the main lesson HTML, preserving executable order.

Only Copy-button command windows are executable inputs. Source excerpts and
expected output remain documentation. Python heredoc cells become real functions;
CLI workflows call a shared persistent Bash bridge because Make/gcloud pipelines
are part of the kit. The explicit overrides record semantic adaptations and the
course-plan lessons whose HTML has not been authored yet.

Run from the authoring checkout: python tools/build_workshop_demos.py
Use --check to compare generated files without changing them.
"""
from __future__ import annotations
import ast
from collections import Counter
import hashlib
import html
import io
import json
from pathlib import Path
import re
import sys
import textwrap
import tokenize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pagekit.demo_links import annotate, sections, strip_links
WORKSHOP = ROOT / "deploy/workshop_demos"
# Learners have the public kit, not this authoring repository: every link in the generated files points at the
# published copy (publish_learner.py puts deploy/workshop_demos at the learner repository's workshop_demos/).
LEARNERS = "https://github.com/netsetos/agents_workshop_learner/blob/main/workshop_demos/"


def published(folder, name):
    """The learner repository's URL for a file this generator writes into ``folder``."""
    return LEARNERS + (folder / name).relative_to(WORKSHOP).as_posix()
MANIFEST = json.loads((ROOT / "course-manifest.json").read_text(encoding="utf-8"))
TAG = re.compile(r"<[^>]+>")


def module_order(key):
    """Basics ("B") first, then Modules 0-12 by number. Example: sorted(MANIFEST['modules'], key=module_order)."""
    return -1 if key == "B" else int(key)


def lesson_order(lesson):
    """Course order of a lesson id. Example: lesson_order('B.2') sorts before lesson_order('0.2')."""
    major, minor = lesson.split(".")
    return (module_order(major), int(minor))


def module_folder(lesson):
    """The lesson's demo folder under workshop_demos. Example: module_folder('1.8') is 'module_01/lesson_1_8'."""
    major = lesson.split(".")[0]
    return f"module_{major if major == 'B' else f'{int(major):02}'}/lesson_{lesson.replace('.', '_')}"


def module_title(number, module):
    """A module README's heading. Example: 'Module 1: RAG foundation - ...', or 'Basics: ...' for the pre-work."""
    return f"{module['name']}" if number == "B" else f"Module {int(number)}: {module['name']}"
OUTPUTS = {}


def plain(value):
    """Decode display text only after removing tags so escaped code operators survive."""
    return html.unescape(TAG.sub("", value)).strip()


def one_line(value):
    """Normalize prose for short file summaries without changing executable code."""
    return re.sub(r"\s+", " ", plain(value)).strip()


def slug(value, limit=48):
    """Use stable ASCII filenames that sort by the explicit HTML-step prefix."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")[:limit].rstrip("_") or "example"


def emit(path, content):
    """Accumulate deterministic output for generation or a no-write drift check."""
    if Path(path).suffix == '.py':
        from workshop_docstrings import document
        content = document(content, str(path))
    OUTPUTS[Path(path)] = content.rstrip() + "\n"


def literal(value):
    """Use readable multiline literals without altering backslashes in sample code."""
    return '"""' + value.replace('\\', '\\\\').replace('"""', '\\"\\"\\"') + '\n"""'


def page_windows(path):
    """Extract every window with its real heading, context, source position and badge."""
    page = strip_links(path.read_text(encoding="utf-8"))
    headings = [{"start": m.start(), "level": int(m[1]), "text": plain(m[2])}
                for m in re.finditer(r"<h([1-4])[^>]*>(.*?)</h\1>", page, re.S)]
    steps = sections(page)
    windows = []
    for n, match in enumerate(re.finditer(r'<div class="cw"><div class="ch-bar">(.*?)</div><pre[^>]*>(.*?)</pre>', page, re.S), 1):
        heading = next((h for h in reversed(headings) if h["start"] < match.start() and h["level"] == 3), None)
        sub = next((h for h in reversed(headings) if h["start"] < match.start() and h["level"] in {3, 4}), heading)
        section = next((s for s in reversed(steps) if s["start"] < match.start()), None)
        if section is None:
            raise ValueError(f"Code window {n} has no HTML section: {path}")
        step = section["anchor"]
        context_start = sub["start"] if sub else 0
        context = page[context_start:match.start()]
        # Excerpts/output already shown are not explanatory prose for a new call.
        context = re.sub(r'<div class="cw">.*?</pre></div>', '', context, flags=re.S)
        paragraphs = [one_line(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", context, re.S)]
        label = plain(re.search(r"<span[^>]*>(.*?)</span>", match[1], re.S)[1])
        expected_match = re.match(r'.*?<div class="cw"><div class="ch-bar"><span>(expected.*?)</span>.*?<pre[^>]*>(.*?)</pre>', page[match.end():], re.S)
        # Only attach an immediately following expected window, not a later step's.
        following = page[match.end():]
        next_window = re.search(r'<div class="cw"><div class="ch-bar"><span>(.*?)</span>.*?<pre[^>]*>(.*?)</pre>', following, re.S)
        expected = plain(next_window[2]) if next_window and plain(next_window[1]).lower().startswith("expected") and not re.search(r'<div class="step"', following[:next_window.start()]) else ""
        windows.append({"window": n, "label": label, "code": plain(match[2]), "copy": "<button" in match[1],
                        "heading": section["heading"], "section_number": section["number"],
                        "subheading": sub["text"] if sub else "Preparation", "anchor": step,
                        "purpose": " ".join(paragraphs[-2:])[:1800] or (sub["text"] if sub else label),
                        "expected": expected, "line": page[:match.start()].count("\n") + 1})
    raw = page.encode("utf-8")
    sha = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    return page, sha, headings, windows


def python_body(code):
    """Recognize a complete standalone Python cell; never strip a surrounding loop."""
    match = re.fullmatch(r"(?:#[^\n]*\n\s*)*python3?\s+-\s+<<['\"]?PY['\"]?\s*(?:#[^\n]*)?\n(.*?)\nPY\s*", code, re.S)
    return match[1] if match else None


def indent_python(code):
    """Indent a function body without changing multiline string/fixture bytes."""
    original = ast.parse(code)
    protected = set()
    for token in tokenize.generate_tokens(io.StringIO(code).readline):
        if token.type == tokenize.STRING and token.end[0] > token.start[0]:
            protected.update(range(token.start[0] + 1, token.end[0] + 1))
    result = "\n".join(("" if n in protected else "    ") + line for n, line in enumerate(code.splitlines(), 1))
    wrapped = ast.parse("def _example(session):\n" + result + "\n").body[0].body
    if ast.dump(ast.Module(body=wrapped, type_ignores=[]), include_attributes=False) != ast.dump(original, include_attributes=False):
        raise ValueError("Indenting the Python cell changed its meaning")
    return result


def dependencies(code):
    """Collect environment names needed across independent IDE processes."""
    names = set(re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)", code))
    names.update(re.findall(r"os\.environ(?:\[|\.get\()['\"]([A-Za-z_][A-Za-z0-9_]*)", code))
    names.update(re.findall(r"(?m)^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)=", code))
    names.update({"API", "API_URL", "ME", "NUMBER", "PROJECT", "REGION", "TENANT"})
    return names


def classify(lesson, window):
    """Apply explicit source-label semantics instead of executing every Copy button."""
    text = (window["label"] + " " + window["heading"]).lower()
    code = window["code"]
    if code.startswith('export DEMO_ROOT='):
        return "shared_setup"
    if lesson.startswith("B.") and window["anchor"] == "setup":   # the Basics laptop setup (pagekit/basics_setup.html)
        return "shared_setup"
    if "when you finish the lesson, not now" in text or code.startswith("# when you finish the lesson:"):
        return "cleanup"
    if "only if" in text or "optional repair" in text or (lesson == "1.8" and window["window"] in {25, 40, 42}):
        return "recovery"
    if "optional" in text or lesson == "1.8" and window["anchor"] in {"s9", "s10", "s11"}:
        return "optional"
    if lesson == "1.8" and window["anchor"] == "s12":
        return "cleanup"
    return "required"


def offline(window, body):
    """Respect the lesson's explicit no-network marker; do not equate Rs 0 with offline."""
    text = window["label"].lower()
    explicit = any(term in text for term in ("no network", "no credentials", "nothing leaves", "arithmetic only", "two files on disk", "the lists are on disk", "no google cloud"))
    if body and not re.search(r"google\.cloud|from google|gcloud|urlopen|requests\.(get|post)|os\.environ\[.(PROJECT|API)", body):
        return True
    return explicit


def make_demo(folder, record, code, body, live):
    """Write a real debugger-friendly Python cell or an explicit kit-command adapter."""
    summary = (f"Lesson {record['lesson']} / {record['anchor']}: {record['heading']}\n\n"
               f"Summary and purpose:\n{record['purpose']}\n\n"
               f"HTML instruction: {record['label']}\n"
               f"Category: {record['category']}. Read the matching README checkpoint before Run.\n"
               f"Prerequisites: {', '.join(record.get('requires', [])) or 'shared setup; see README'}\n"
               f"Expected observation: {record['expected'][:900] or 'Compare the printed observations with this heading in README.md.'}\n\n"
               "Evidence: the active lesson session records this attempt and command output.\n"
               "A completed process is not proof that every sample value matches your lane.\n"
               f"Source: {record['source']} (the main page's line {record['line']})\n")
    docs = literal(summary)
    function_doc = literal(f"Run {record['subheading']} at this checkpoint.\n\n{record['purpose']}\n\n"
                        "Args: session is the active lesson run, with validated settings and saved prerequisites.\n"
                        f"Operations: {record['label']}.\n"
                        "Returns: None; observations are printed or saved by the lesson code.\n"
                        "Failures propagate to the session; inspect its failed attempt before continuing.\n\n"
                        "Example: Run this file after its README prerequisites, or set a breakpoint in this function.\n"
                        + ("Observe: " + record['expected'][:700] if record['expected'] else "Observe the printed/saved evidence for this heading; a zero exit alone is not proof."))
    source = f'{docs}\nfrom workshop_helpers.session import DemoSession\n\n# Change only for a deliberate replay after inspecting this step\'s effects.\nREPEAT = False\n'
    # A reviewed adaptation may run Python around the page's commands (a wait before them): the commands stay a
    # visible constant, and the body calls session.shell(COMMANDS) itself.
    wraps_commands = body is not None and "session.shell(COMMANDS)" in body
    if body is None or wraps_commands:
        source += '\n# The lesson\'s actual kit commands, visible here in the same order.\nCOMMANDS = ' + literal(code) + '\n'
    source += '\n\ndef demonstrate(session):\n' + textwrap.indent(function_doc, '    ') + '\n'
    if body is not None:
        source += indent_python(body) + "\n"
        record["implementation"] = "mixed_python_and_kit_cli" if wraps_commands else "native_python"
    else:
        source += "    # Preserve the kit CLI's arguments, conditions and observation order.\n"
        source += "    session.shell(COMMANDS)\n"
        record["implementation"] = "kit_cli_workflow"
    source += f'\n\ndef main():\n    """Resume this lesson and execute only this checkpoint in the IDE interpreter."""\n    with DemoSession(__file__, live={live!r}, repeat=REPEAT) as session:\n        demonstrate(session)\n\n\nif __name__ == "__main__":\n    main()\n'
    ast.parse(source, filename=record["file"])
    emit(folder / record["file"], source)


def convert_lesson(number, module, lesson, specification):
    """Map a complete HTML page before generating its ordered executable checkpoints."""
    folder = WORKSHOP / module_folder(lesson)
    path = ROOT / "lessons" / f"{number}-{module['slug']}" / f"{lesson}-{specification['slug']}" / f"Netsetos_GCP_Capstone_{lesson}_{specification['topic_filename']}_WIX.html"
    page, sha, headings, windows = page_windows(path)
    if lesson == "1.1":
        # Curated complete experiments: do not regenerate one file per Copy box.
        from workshop_lesson31 import build_mapping
        mapping = build_mapping(sys.modules[__name__], folder, specification, path, sha, headings, windows)
        emit(path, annotate(lesson, page, mapping))
        return mapping
    from workshop_demo_additions import extra_windows, adapt_window
    original_window_count = len(windows)
    windows = extra_windows(lesson, page) + windows
    source = published(folder, "GUIDE.md")          # the page's prose, as published; the page itself is on the course site
    counts = Counter()
    demos, reading = [], []
    variables = set()
    required = []
    shared_setup = []
    for window in windows:
        if not window["copy"]:
            reading.append({key: window[key] for key in ("window", "label", "heading", "anchor", "line")})
            continue
        category = classify(lesson, window)
        if category == "shared_setup":
            shared_setup.append(window["window"])
            continue
        code = window["code"]
        variables.update(dependencies(code))
        adaptations = []
        body = python_body(code)
        step = int(re.sub(r"\D", "", window["anchor"]) or "0")
        counts[(step, category)] += 1
        prefix = "finish" if category == "cleanup" else "recover" if category == "recovery" else "demo"
        marker = "optional_" if category == "optional" else ""
        filename = f"{prefix}_{step:02}_{counts[(step, category)]:02}_{marker}{slug(window['subheading'])}.py"
        if code.startswith("# for this lesson: acme answers"):
            body = "session.pin_vector()"
            adaptations.append("Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.")
        elif code.startswith("# when you finish the lesson:"):
            body = "session.restore_backend()"
            adaptations.append("Run at lesson end despite its early HTML position, as the source label explicitly instructs.")
        # Centralize the repeated service-environment plumbing, leaving model settings visible.
        env_match = re.search(r"for N in ([A-Z0-9_ ]+); do setenv", code)
        if code.startswith("svc_env()") and env_match:
            keys = env_match[1].split()
            body = f"session.service_environment('documind-api', {keys!r})"
            pip_lines = [line for line in code.splitlines() if "pip install" in line]
            if pip_lines:
                body += "\nsession.shell(" + repr("\n".join(pip_lines)) + ")"
            variables.update(keys)
            adaptations.append("Read literal environment values as JSON from the serving revision; absent keys are unset. Repeated text parsing is removed.")
        # Avoid silently discarding learner edits while preserving the diagnostic workflow.
        if "git -C \"$DEMO_ROOT\" checkout -q -- smoke/smoke_reindex.py" in code:
            code = re.sub(r'git -C "\$DEMO_ROOT" checkout -q -- smoke/smoke_reindex.py && ', '', code)
            adaptations.append("Do not discard local smoke-script edits; a fast-forward update refuses conflicts so they can be inspected.")
        code, body, additional_changes = adapt_window(lesson, window, code, body)
        adaptations.extend(additional_changes)
        record = {**{key: window[key] for key in ("window", "label", "heading", "subheading", "anchor", "purpose", "expected", "line")},
                  "id": filename[:-3], "lesson": lesson, "file": filename, "category": category,
                  "requires": required[-1:] if category in {"required", "optional"} else [], "source": source,
                  "adaptations": adaptations, "live_verified": False}
        if category == "optional":
            previous_optional = [r["id"] for r, _, _ in demos
                                 if r["category"] == "optional" and r["anchor"] == record["anchor"]]
            if previous_optional:
                record["requires"] = previous_optional[-1:]
        record["offline"] = offline(window, body) if body not in {"session.pin_vector()", "session.restore_backend()"} else False
        if body and "session.service_environment" in body:
            record["offline"] = False
        if "offline_override" in window:
            record["offline"] = window["offline_override"]
        if category == "required":
            required.append(record["id"])
        demos.append((record, code, body))

    # All lesson code is mapped before any generated file is emitted.
    for index, (record, code, body) in enumerate(demos):
        subsequent = [r for r, _, _ in demos[index + 1:] if r["category"] == "required"]
        record["next"] = subsequent[0]["file"] if subsequent else "See README: optional extensions, then all finish_*.py files"
        make_demo(folder, record, code, body, live=not record["offline"])
    mapping = {"schema_version": 1, "lesson": lesson, "title": specification["name"],
               "source_kind": "main_html", "source": source, "source_page": path.name, "source_sha": sha,
               "shared_setup_windows": shared_setup, "source_window_count": original_window_count, "persist_variables": sorted(variables),
               "headings": [{"level": h["level"], "heading": h["text"]} for h in headings],
               "demos": [r for r, _, _ in demos], "read_only_windows": reading,
               "live_verification": "Not run by the generator; validate on the intended workstation/lane."}
    emit(folder / "lesson_map.json", json.dumps(mapping, indent=2, ensure_ascii=False))
    lines = [f"# Lesson {lesson}: {specification['name']}", "",
             f"**Summary:** {specification['proof']}. The files below follow the main HTML's runnable checkpoints and preserve its examples.", "",
             f"Source: the lesson's main page, `{path.name}`, at Git blob `{sha}`; [GUIDE.md](GUIDE.md) keeps its prose. Native Python cells can be stepped through in the IDE. Command workflows use the shared Bash/Make/gcloud helper because these are the kit's actual operations.", "",
             "## Before running", "",
             "Use `/home/user/rag-shell-venv/bin/python`, run `workshop_demos/setup/bootstrap.py`, and check `workshop_demos/setup/config/settings.local.json`. Open the learner kit root in your IDE. Each file can be Run independently; the session helper sets the working directory and carries this lesson's variables forward.", "",
             "Run the required files in the table order. A failed step does not satisfy the next file's prerequisite. Read its saved output before continuing. Optional and recovery files are explicit choices; finish files are run at the end even though some HTML pages show their commands in the setup section. Do not use Run All.", "",
             "**Execution is not live verification:** these examples have source/compile checks, not a recorded run against your GCP project. Numerical sample output is illustrative; use the checks and explanations below. Commands can change cloud resources as described by their HTML instruction.", "",
             "## Required run order", "", "| HTML | File | Instruction / purpose |", "|---|---|---|"]
    for record, _, _ in demos:
        if record["category"] == "required":
            lines.append(f"| {record['anchor']} · window {record['window']} | [{record['file']}]({record['file']}) | {record['label'].replace('|', '/')} |")
    for category, heading in (("optional", "Optional extensions"), ("recovery", "Conditional recovery"), ("cleanup", "Finish and restore settings")):
        chosen = [r for r, _, _ in demos if r["category"] == category]
        if chosen:
            lines += ["", "## " + heading, ""]
            lines += [f"- [{r['file']}]({r['file']}) — {r['label']}" for r in chosen]
    lines += ["", "## Checkpoints and explanation", ""]
    for record, code, body in demos:
        lines += [f"### {record['file']}", "", f"**HTML: {record['heading']} / {record['subheading']}**", "",
                  record["purpose"], "", f"Run instruction: {record['label']}.", "",
                  f"Implementation: {'native Python in demonstrate(session)' if record['implementation']=='native_python' else 'the existing kit command workflow through session.shell()'}. "
                  "The shared helper supplies credentials/settings, preserves this lesson's state and records failures; the file contains the actual example.", ""]
        if record["adaptations"]:
            lines += ["IDE adaptations:", ""] + ["- " + adaptation for adaptation in record["adaptations"]] + [""]
        if record["expected"]:
            lines += ["Expected shape from the HTML (actual counts/timing can differ):", "", "```text", record["expected"], "```", ""]
        lines += ["If it fails, inspect this attempt under `workshop_demos/results/`, plus any report path printed by the example. Keep the session and its fixture files for recovery. Do not rerun a cloud mutation merely to obtain another output line.", ""]
    lines += ["## Source coverage", "", f"{len(windows)} code windows mapped: {len(demos)} IDE demo files, {len(shared_setup)} shared setup blocks, {len(reading)} read-only excerpts/output blocks. `lesson_map.json` records every window and source line. Reading-only headings and UI observations remain in the source lesson; they are not turned into fake runnable examples.", "",
              "## Helper functions", "", "- `DemoSession`: resumes this lesson, checks prerequisite files and records attempts.",
              "- `session.shell(code)`: invokes the existing CLI workflow, preserving named variables and shell functions between IDE runs.",
              "- `session.service_environment(service, keys)`: reads the actual serving configuration as JSON, without saving secrets.",
              "- `session.pin_vector()` / `restore_backend()`: save and restore the prior tenant setting when the lesson has the common vector setup.",
              "- `session.command(args)`: runs a CLI argument list and retains its actual output/exit status.", ""]
    emit(folder / "README.md", "\n".join(lines))
    from group_workshop_demos import group_lesson
    mapping = group_lesson(sys.modules[__name__], mapping, page)
    emit(path, annotate(lesson, page, mapping))
    return mapping


def main():
    """Generate deterministic lesson files, then reject missing or stale coverage."""
    previous_files = set()
    for path in WORKSHOP.glob("module_*/lesson_*/lesson_map.json"):
        previous = json.loads(path.read_text(encoding="utf-8"))
        if previous["lesson"] != "1.1":
            for record in previous["demos"]:
                target = (path.parent / record["file"]).resolve()
                if not target.is_relative_to(path.parent.resolve()):
                    raise ValueError("Mapped lesson path escapes its directory")
                previous_files.add(target)
    all_lessons = []
    for number, module in sorted(MANIFEST["modules"].items(), key=lambda pair: module_order(pair[0])):
        for lesson, specification in module["lessons"].items():
            if not specification.get("slug"):
                continue  # Course-plan additions are generated by the explicit authored overrides; planned lessons have no folder yet.
            all_lessons.append(convert_lesson(number, module, lesson, specification))
    from workshop_demo_additions import generate_course_plan_lessons
    additions = generate_course_plan_lessons(sys.modules[__name__])
    from group_workshop_demos import group_lesson
    additions = [group_lesson(sys.modules[__name__], mapping) for mapping in additions]
    all_lessons.extend(additions)
    all_lessons.sort(key=lambda m: lesson_order(m["lesson"]))
    # One README per module, listing every lesson that has a folder (a module can mix written and course-plan lessons).
    for number, module in MANIFEST["modules"].items():
        listed = [m for m in all_lessons if module_folder(m["lesson"]).split("/")[0] == f"module_{number}"]
        if listed:
            emit(WORKSHOP / f"module_{number}" / "README.md", f"# {module_title(number, module)}\n\n"
                 + "Run lessons in this order, finishing/restoring each before beginning the next.\n\n"
                 + "\n".join(f"- [{item['lesson']}: {item['title']}](lesson_{item['lesson'].replace('.', '_')}/README.md)" for item in listed))
    emit(WORKSHOP / "course_map.json", json.dumps({"modules": len(MANIFEST["modules"]), "lessons_expected": len(all_lessons),
         "lessons": [{"lesson": m["lesson"], "title": m["title"], "source_sha": m["source_sha"], "source_kind": m["source_kind"], "demos": len(m["demos"])} for m in all_lessons]}, indent=2))
    emit(WORKSHOP / "COURSE.md", "# All modules and lessons\n\nThe sequence comes from each main HTML; the "
         + f"{len(additions)} lessons whose main HTML is not written yet are attributed to the course plan and kit. Lessons planned but not started have no folder yet.\n\n"
         + "\n".join(f"- [{m['lesson']}: {m['title']}]({module_folder(m['lesson'])}/README.md) — {len(m['demos'])} files; {m['source_kind']}" for m in all_lessons))
    stale = []
    # Remove only obsolete files named by the previous generated lesson map.
    # Untracked user experiments are never candidates for deletion.
    for path in sorted(previous_files - {p.resolve() for p in OUTPUTS}):
        if not path.exists():
            continue
        if "--check" in sys.argv:
            stale.append("obsolete: " + str(path.relative_to(ROOT)))
        else:
            path.unlink()
    for path, content in OUTPUTS.items():
        if "--check" in sys.argv:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    if stale:
        raise SystemExit("Generated demo files are stale:\n" + "\n".join(stale))
    print(json.dumps({"html_lessons": len(all_lessons) - len(additions), "course_plan_lessons": len(additions), "generated_files": len(OUTPUTS),
                      "demos": sum(len(m["demos"]) for m in all_lessons),
                      "native_python": sum(r["implementation"] == "native_python" for m in all_lessons for r in m["demos"]),
                      "mode": "checked" if "--check" in sys.argv else "written"}, indent=2))


if __name__ == "__main__":
    main()
