"""Turn reviewed HTML checkpoints into complete, debugger-friendly experiments.

The extraction stage still accounts for every original code window. This stage
uses explicit teaching boundaries, keeps each Python cell as a real function,
and moves lifecycle/conditional actions out of the normal demo sequence.
"""
import ast
from collections import Counter
import json
import re
import textwrap

from workshop_demo_groups import CLEANUP, EXTRAS, MANUAL, OPTIONAL_AFTER, PREREQUISITES, REQUIRED


PAUSE = ("Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). "
         "Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another "
         "adaptation here says otherwise.")


def prose_guide(builder, page, mapping):
    """Retain the page's explanatory prose, including actions outside Copy boxes."""
    page = re.sub(r"<(script|style)\b.*?</\1>", "", page, flags=re.S)
    page = re.sub(r'<div class="cw">.*?</pre></div>', "", page, flags=re.S)
    lines = [f"# Lesson {mapping['lesson']}: source reading guide", "",
             "Read this beside the section-numbered demo files. The prose below follows the main HTML;",
             "its terminal setup is replaced by the documented Python setup. Read-only code",
             "and sample output are not executable steps. Sample values are not live results.", "",
             f"Source: the lesson's main page, `{mapping.get('source_page', 'main HTML')}`, reviewed at blob `{mapping['source_sha']}`. "
             "Learners read that page on the course site; this guide keeps its prose.", ""]
    for match in re.finditer(r"<(h[2-4]|p|li)\b[^>]*>(.*?)</\1>", page, re.S):
        value = re.sub(r"<code[^>]*>(.*?)</code>", lambda m: "`" + builder.plain(m[1]) + "`", match[2], flags=re.S)
        value = builder.one_line(value)
        if value:
            prefix = "#" * int(match[1][1]) + " " if match[1].startswith("h") else "- " if match[1] == "li" else ""
            lines.extend([prefix + value, ""])
    return "\n".join(lines)


def extract_function(builder, source, record, index):
    """Keep comments and literal bytes while giving each source cell its own function."""
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "demonstrate")
    title = re.sub(r"^(?:Read it|Do it|Call it|Run it|Try it|Inspect it)\s*[:—–-]?\s*", "", record["subheading"], flags=re.I)
    if not title.strip():
        title = record["heading"]
    name = f"step_{index:02}_{builder.slug(title, 42)}"
    function = "\n".join(source.splitlines()[node.lineno - 1:node.end_lineno])
    function = function.replace("def demonstrate(session):", f"def {name}(session):", 1)
    commands = next((n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "COMMANDS" for t in n.targets)), None)
    constants = ""
    if commands:
        constant_name = f"COMMANDS_{index:02}"
        constants = "# Original CLI workflow for " + name + ".\n" + constant_name + " = " + builder.literal(ast.literal_eval(commands.value)) + "\n\n"
        function = re.sub(r"\bCOMMANDS\b", constant_name, function)
    checkpoint = MANUAL.get((record["lesson"], record.get("window")))
    if checkpoint:
        # Insert after the function docstring, before any mutation or observation.
        parsed = ast.parse(function).body[0]
        doc = parsed.body[0]
        lines = function.splitlines()
        lines.insert(doc.end_lineno, "    manual_checkpoint(" + repr(checkpoint) + ")")
        function = "\n".join(lines)
    return name, constants + function + "\n\n"


def build_file(builder, folder, mapping, filename, purpose, members, sources, category, requires):
    """Emit one complete experiment with visible ordered functions and progress guards."""
    lesson = mapping["lesson"]
    title = members[0]["heading"] if members else purpose
    live = any(not r["offline"] for r in members)
    record = {"id": filename.removesuffix(".py").replace("/", "_"), "lesson": lesson,
              "file": filename, "category": category, "requires": requires,
              "heading": title, "purpose": purpose,
              "anchor": ", ".join(dict.fromkeys(r["anchor"] for r in members)),
              "anchors": list(dict.fromkeys(r["anchor"] for r in members)),
              "section_number": int(members[0]["anchor"][1:]) if len(set(r["anchor"] for r in members)) == 1 and re.fullmatch(r"s\d+", members[0]["anchor"]) else None,
              "windows": [r["window"] for r in members if isinstance(r.get("window"), int)],
              "source": mapping.get("source", members[0]["source"] if members else ""),
              "source_lines": [r["line"] for r in members],
              "offline": not live, "live_verified": False,
              "implementation": "native_python" if all(r["implementation"] == "native_python" for r in members) else "mixed_python_and_kit_cli",
              "steps": []}
    outline = "\n".join(f"{i}. {r['subheading']} (source window {r.get('window', r['anchor'])})" for i, r in enumerate(members, 1))
    summary = (f"Lesson {lesson}: {title}\n\n{purpose}\n\n"
               f"Run order inside this file:\n{outline}\n\n"
               f"Prerequisites: {', '.join(requires) or 'workshop setup; see this lesson README'}.\n"
               "Use the existing rag-shell-venv interpreter; Run or Debug this file.\n"
               "The functions below contain the lesson examples in source order. Helpers\n"
               "supply configuration, authentication, state and CLI execution. See README.md\n"
               "for expected observations, effects and the next file; GUIDE.md retains prose.\n"
               "Example: open this file at the matching HTML heading, Run once, then inspect\n"
               "the observations below before continuing to the next numbered section.\n"
               "A successful process is not proof that a live result matched the sample.\n")
    source = builder.literal(summary) + "\nfrom workshop_helpers.session import DemoSession\nfrom workshop_helpers.steps import manual_checkpoint, run_steps\n\n"
    source += "# REPEAT replays the whole file; use only after reviewing its effects.\nREPEAT = False\n"
    source += "# A failed function may have partial effects. Inspect its saved attempt first.\nRETRY_FAILED_STEP = False\n\n\n"
    calls = []
    for index, member in enumerate(members, 1):
        name, function = extract_function(builder, sources[member["id"]], member, index)
        source += function
        step_id = "source_" + str(member.get("window", member["id"]))
        calls.append(f"        ({step_id!r}, {name}),")
        entry = {**{k: member[k] for k in ("heading", "subheading", "purpose", "label", "expected", "adaptations") if k in member},
                 "id": step_id, "function": name, "window": member.get("window"),
                 "source_line": member["line"], "manual_checkpoint": MANUAL.get((lesson, member.get("window")))}
        if entry["manual_checkpoint"]:
            entry["adaptations"] = list(entry.get("adaptations", [])) + [PAUSE]
        record["steps"].append(entry)
    source += "def demonstrate(session):\n    \"\"\"Run this section in source order, saving each function's outcome.\n\n    Example: main() opens the configured session and calls demonstrate(session).\n    A failed step stops this sequence; inspect its evidence before an explicit retry.\n    \"\"\"\n"
    source += "    run_steps(session, [\n" + "\n".join(calls) + f"\n    ], retry_failed=RETRY_FAILED_STEP, cleanup={category == 'cleanup'!r}, finalize={filename == 'setup/finish.py'!r})\n"
    source += f'\n\ndef main():\n    """Open the lesson session and run this section.\n\n    Example: use Run/Debug on this file with the rag-shell-venv interpreter.\n    Project settings and completed prerequisites come from the shared setup.\n    """\n    with DemoSession(__file__, live={live!r}, repeat=REPEAT) as session:\n        demonstrate(session)\n\n\nif __name__ == "__main__":\n    main()\n'
    ast.parse(source)
    builder.emit(folder / filename, source)
    return record


def group_lesson(builder, mapping, page=None):
    """Require an explicit, exhaustive assignment of every executable source window."""
    lesson = mapping["lesson"]
    if lesson == "1.1":
        return mapping
    folder = builder.WORKSHOP / builder.module_folder(lesson)
    original = mapping["demos"]
    sources = {r["id"]: builder.OUTPUTS.pop(folder / r["file"]) for r in original}
    if mapping["source_kind"] == "main_html":
        reviewed = json.loads((builder.ROOT / "tools/workshop_demo_reviewed.json").read_text())
        if reviewed[lesson] != mapping["source_sha"]:
            raise ValueError(f"Lesson {lesson} HTML changed. Review experiment boundaries/manual checkpoints before updating its reviewed digest.")
        by_window = {r["window"]: r for r in original}
        overrides = {w: ('required', '') for w in REQUIRED.get(lesson, [])}
        for category, name, windows, *purpose in EXTRAS.get(lesson, []):
            for window in windows:
                overrides[window] = (category, purpose[0] if purpose else '')
        cleanup = CLEANUP.get(lesson, [r['window'] for r in original if r['category'] == 'cleanup'])
        buckets = {}
        for record in original:
            if record['window'] in cleanup:
                continue
            category, note = overrides.get(record['window'], (record['category'], ''))
            buckets.setdefault((record['anchor'], category), []).append((record, note))
        definitions = []
        for (anchor, category), items in buckets.items():
            if anchor == 'setup' and category == 'required':
                filename = 'setup/prepare.py'
            else:
                prefix = f'demo_{int(anchor[1:]):02}_' if anchor != 'setup' else 'setup_'
                filename = prefix + builder.slug(items[0][0]['heading'], 80) + '.py'
                if category != 'required':
                    filename = category + '/' + filename
            purpose = ' '.join(dict.fromkeys(note or record['purpose'] for record, note in items))
            definitions.append((filename, purpose, [record['window'] for record, _ in items], category))
        cleanup_groups = {}
        for window in cleanup:
            cleanup_groups.setdefault(by_window[window]['anchor'], []).append(window)
        for anchor, windows in cleanup_groups.items():
            title = by_window[windows[0]]['heading']
            filename = 'setup/restore_settings.py' if anchor == 'setup' else f'cleanup/demo_{int(anchor[1:]):02}_{builder.slug(title,80)}.py'
            definitions.append((filename, 'At lesson end: ' + ' '.join(by_window[w]['purpose'] for w in windows), windows, 'cleanup'))
        used = [w for _, _, ws, _ in definitions for w in ws]
        if Counter(used) != Counter(by_window.keys()):
            raise ValueError(f"{lesson}: omitted {set(by_window)-set(used)}, unknown {set(used)-set(by_window)}, duplicate {[w for w,n in Counter(used).items() if n>1]}")
    else:
        # These nine lessons already have authored complete experiments, not HTML fragments.
        by_window = {r["id"]: r for r in original}

        def plan_file(r):
            if r["category"] == "cleanup":
                return "setup/finish.py"
            if r["category"] == "recovery":
                return "recovery/" + r["file"].split("_", 2)[2]      # recover_NN_name.py -> recovery/name.py
            return r["file"]
        definitions = [(plan_file(r), r["purpose"], [r["id"]], r["category"]) for r in original]
    records, required = [], []
    for filename, purpose, windows, category in definitions:
        dependencies = required[-1:] if category in {"required", "optional"} else []
        anchor = by_window[windows[0]]["anchor"] if windows and windows[0] in by_window else ""
        after = OPTIONAL_AFTER.get(lesson, {}).get(int(anchor[1:])) if category == "optional" and re.fullmatch(r"s\d+", anchor) else None
        if after == "setup":
            dependencies = [r["id"] for r in records if r["file"] == "setup/prepare.py"]
        elif after is not None:
            dependencies = [r["id"] for r in records if r["category"] == "optional" and r["section_number"] == after]
        record = build_file(builder, folder, mapping, filename, purpose, [by_window[w] for w in windows], sources, category, dependencies)
        records.append(record)
        if category == "required":
            required.append(record["id"])
    for index, record in enumerate(records):
        following = next((r["file"] for r in records[index+1:] if r["category"] == "required"), None)
        record["next"] = following or "See README: optional choices, then setup/finish.py if listed."
    if mapping['source_kind'] == 'main_html' and any(r['category'] == 'cleanup' for r in records):
        records.append(finish_dispatcher(builder, folder, lesson))
    mapping.update(schema_version=4, layout_version=3, curated=True, demos=records,
                   prerequisites=PREREQUISITES.get(lesson, "The shared workshop setup and the deployed/local inputs described in the reading guide."))
    write_documentation(builder, folder, mapping, page)
    return mapping


def finish_dispatcher(builder, folder, lesson):
    """Keep one Run button for restoration without duplicating section examples.

    Example: 1.5's section 7 cleanup runs before its unnumbered backend restore.
    """
    builder.emit(folder / 'setup/finish.py', '''"""Finish this lesson after success or failure; keep all saved evidence.

Summary: call the cleanup section files in their documented restoration order.
Example: Run this file once at lesson end, including after an earlier failure.
It attempts remaining restorations and closes the session only after success.
"""
from workshop_helpers.cleanup import finish_lesson
from workshop_helpers.session import DemoSession

REPEAT = False


def demonstrate(session):
    """Restore the mapped cleanup sections and the original lesson settings.

    Example: main() opens the saved run and passes its session here.
    """
    finish_lesson(session)


def main():
    """Open this lesson's saved state with the IDE interpreter.

    Example: Run setup/finish.py after the numbered examples, or after failure.
    """
    with DemoSession(__file__, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == '__main__':
    main()
''')
    return {'id': 'setup_finish', 'lesson': lesson, 'file': 'setup/finish.py',
            'category': 'cleanup', 'orchestrator': True, 'requires': [], 'anchor': 'finish', 'anchors': [],
            'section_number': None, 'heading': 'Finish and restore all lesson settings',
            'purpose': 'Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.',
            'windows': [], 'source_lines': [], 'steps': [], 'offline': False, 'live_verified': False,
            'implementation': 'native_python', 'next': 'Lesson finished; use start_new_session.py for a deliberate replay.'}


def write_documentation(builder, folder, mapping, page=None):
    """Write the same section/file/function index for generated and authored lessons.

    Example: lesson 1.1 uses this renderer after retaining its authored cloud checks.
    """
    lesson, records = mapping['lesson'], mapping['demos']
    if mapping['source_kind'] == 'main_html':
        mapping['source_line_basis'] = 'Teaching HTML before generated IDE-DEMO-LINKS blocks; use the section anchor in the rendered page.'
    builder.emit(folder / "lesson_map.json", json.dumps(mapping, indent=2, ensure_ascii=False))
    if page:
        builder.emit(folder / "GUIDE.md", prose_guide(builder, page, mapping))
    lines = [f"# Lesson {lesson}: {mapping['title']}", "", "## What to run", "",
             "Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.", "",
             ("The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped."
              if mapping['source_kind'] == 'main_html' else "This lesson has no authored main HTML. Its file numbers follow the explicitly listed course-plan experiments; they do not claim an HTML heading match. Run those plan steps in the order below."), "",
             "| HTML section | File | What it demonstrates |", "|---|---|---|"]
    sequence = [r for r in records if r["category"] == "required"]
    for index, record in enumerate(sequence, 1):
        label = str(record.get('section_number') or record['anchor']) if mapping['source_kind'] == 'main_html' else f'Plan step {index}'
        lines.append(f"| {label} | [{record['file']}]({record['file']}) | {record['heading'].replace('|', '/')} |")
    lines += ["", "## Before starting", "",
              "Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.", "",
              mapping["prerequisites"], "",
              "Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.", "",
              "## Resume and recovery", "",
              "Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.", "",
              "Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.", "",
              "After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.", ""]
    for category, title in (("optional", "Optional extensions"), ("recovery", "Conditional recovery"), ("cleanup", "Finish and restore")):
        chosen = [r for r in records if r["category"] == category]
        if chosen:
            lines += ["## " + title, ""] + [f"- [{r['file']}]({r['file']}) — {r['purpose']}" for r in chosen] + [""]
    lines += ["## Functions, observations and effects", "",
              "The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.", ""]
    for record in records:
        lines += [f"### {record['file']}", "", record["purpose"], ""]
        for step in record["steps"]:
            lines += [f"**`{step['function']}(session)` — {step['heading']} / {step['subheading']}**", "", step["purpose"], "",
                      "Operation: " + step["label"] + ".", ""]
            if step.get("manual_checkpoint"):
                lines += ["Manual action: " + step["manual_checkpoint"], ""]
            if step.get("adaptations"):
                lines += ["IDE adaptation: " + " ".join(step["adaptations"]), ""]
            if step["expected"]:
                lines += ["Expected shape, not a promised result:", "", "```text", step["expected"], "```", ""]
    if page:
        lines += ["## Source and coverage", "", f"[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `{mapping.get('source_page', 'main HTML')}`. All {mapping['source_window_count']} original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `{mapping['source_sha']}`.", "", "Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.", ""]
    else:
        lines += ["## Source and coverage", "", "This lesson has no authored main HTML yet. These experiments come from the course plan and actual kit entry points, not an invented HTML sequence. `lesson_map.json` records their attribution.", ""]
    builder.emit(folder / "README.md", "\n".join(lines))
    return mapping
