"""Check every lesson mapping, import, native cell and CLI syntax without cloud calls.

This verifies coverage and executable structure, not IAM, model responses, live
latency, paid operations or the truth of illustrative expected-output numbers.
"""
import ast
import importlib.util
import json
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pagekit.demo_links import annotate, sections, strip_links
from pagekit.pagebuild import page_path
from build_workshop_demos import page_windows, slug

ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT / "deploy/workshop_demos"
PRIVATE = "github.com/netsetos/agents_workshop/"          # the authoring repository: learners get a 404
PUBLIC = "https://github.com/netsetos/agents_workshop_learner/blob/main/workshop_demos/"


def check_links():
    """Learners have the public kit only. No file may link into the authoring repository, and every learner-repo
    link, and every relative link in a Markdown file, must name something published with it."""
    problems, checked = [], 0
    for path in sorted(WORKSHOP.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".json", ".py"} or "results" in path.relative_to(WORKSHOP).parts:
            continue
        text = path.read_text(encoding="utf-8")
        where = path.relative_to(ROOT).as_posix()
        if PRIVATE in text:
            problems.append(f"{where}: links into the private authoring repository")
        for url in re.findall(re.escape(PUBLIC) + r"[^\s)\"'#]+", text):
            checked += 1
            if not (WORKSHOP / url[len(PUBLIC):]).is_file():
                problems.append(f"{where}: {url} is not a file the kit publishes")
        if path.suffix == ".md":
            for link in re.findall(r"\]\(([^)\s]+)\)", text):
                target = link.split("#")[0]
                if target and "://" not in target and not target.startswith("mailto:"):
                    checked += 1
                    if not (path.parent / target).exists():
                        problems.append(f"{where}: relative link {link} does not resolve")
    return problems, checked


def main():
    """Fail on omitted source windows, invalid dependencies or malformed commands."""
    manifest = json.loads((ROOT / "course-manifest.json").read_text())
    # Every written lesson has a folder, and so does every course-plan lesson; a lesson planned but not started has none.
    from workshop_demo_additions import course_plan_recipes
    expected = {lesson for module in manifest["modules"].values() for lesson, spec in module["lessons"].items()
                if spec.get("slug")} | set(course_plan_recipes())
    maps = sorted(WORKSHOP.glob("module_*/lesson_*/lesson_map.json"))
    seen, native, commands, windows = set(), 0, 0, 0
    raw_commands, raw_python, inline_python, documented = 0, 0, 0, 0
    syntax_errors = []
    bash = shutil.which("bash")
    if not bash and sys.platform == "win32":
        candidate = Path("C:/Program Files/Git/bin/bash.exe")
        bash = str(candidate) if candidate.exists() else None
    assert bash, "Install bash to check the kit CLI workflows."
    for path in maps:
        mapping = json.loads(path.read_text(encoding="utf-8"))
        assert mapping["lesson"] not in seen
        seen.add(mapping["lesson"])
        teaching = [r for r in mapping["demos"] if r["category"] == "required" and r["file"].startswith("demo_")]
        assert teaching, (path, "Missing teaching examples")
        if mapping['source_kind'] == 'main_html':
            page = page_path(mapping['lesson']).read_text(encoding='utf-8')
            assert page == annotate(mapping['lesson'], page, mapping), (path, 'Missing/stale HTML run links')
            section_map = {s['anchor']: s for s in sections(page)}
            _, _, _, source_windows = page_windows(page_path(mapping['lesson']))
            source_by_number = {w['window']: w for w in source_windows}
            for window in source_windows:
                if not window['copy']:
                    continue
                result = subprocess.run([bash, '-n'], input=window['code'], text=True, encoding='utf-8', capture_output=True)
                assert not result.returncode, (path, window['window'], 'HTML Bash syntax', result.stderr)
                raw_commands += 1
                for cell in re.finditer(r'python3?\s+-\s+<<[\'\"]?(PY\w*)[\'\"]?[^\n]*\n(.*?)\n\1\b', window['code'], re.S):
                    ast.parse(cell[2], filename=f"HTML {mapping['lesson']} window {window['window']}")
                    raw_python += 1
                for cell in re.finditer(r'''\bpython3?\s+-c\s+("(?:[^"\\]|\\.)*"|'[^']*')''', window['code']):
                    code = shlex.split(cell[1])[0]
                    ast.parse(code, filename=f"HTML {mapping['lesson']} window {window['window']} inline Python")
                    inline_python += 1
            numbered = []
            for record in mapping['demos']:
                if record['file'].startswith('setup/'):
                    continue
                assert len(record['anchors']) == 1, (path, 'One numbered section per file', record)
                section = section_map[record['anchor']]
                number = section['number']
                assert Path(record['file']).name.startswith(f'demo_{number:02}_') if number else 'setup_' in record['file'], (path, record)
                assert record['heading'] == section['heading'], (path, 'Heading mismatch', record)
                assert Path(record['file']).stem.endswith(slug(section['heading'],80)), (path, 'Filename/heading mismatch', record)
                assert all(source_by_number[w]['anchor'] == record['anchor'] for w in record.get('windows', [])), (path, 'Window in wrong section', record)
                assert record.get('windows',[]) == sorted(record.get('windows',[])), (path, 'Window order', record)
                if record['category'] == 'required' and number:
                    numbered.append(number)
            assert numbered == sorted(set(numbered)), (path, 'Required section order', numbered)
        ids = set()
        covered = list(mapping.get("shared_setup_windows", [])) + [r["window"] for r in mapping.get("read_only_windows", [])]
        for demo in mapping["demos"]:
            assert demo["id"] not in ids, (path, demo["id"])
            assert set(demo["requires"]).issubset(ids), (path, demo["requires"])
            ids.add(demo["id"])
            if isinstance(demo.get("window"), int):
                covered.append(demo["window"])
            covered.extend(demo.get("windows", []))
            script = path.parent / demo["file"]
            tree = ast.parse(script.read_text(encoding="utf-8"))
            assert ast.get_docstring(tree), script
            names = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
            assert {"main", "demonstrate"}.issubset(names), script
            assert ast.get_docstring(names["main"]) and ast.get_docstring(names["demonstrate"]), script
            for step in demo.get("steps", []):
                assert step["function"] in names and ast.get_docstring(names[step["function"]]), (script, step)
            if demo.get('steps') and not any(s['function'] == 'demonstrate' for s in demo['steps']):
                runner = next(n for n in ast.walk(names['demonstrate']) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'run_steps')
                actual_order = []
                for pair in runner.args[1].elts:
                    callback = pair.elts[1]
                    function = callback.id if isinstance(callback, ast.Name) else callback.args[0].id
                    actual_order.append((ast.literal_eval(pair.elts[0]), function))
                assert actual_order == [(s['id'], s['function']) for s in demo['steps']], (script, 'Function call order differs from the lesson map')
            # Importing a demo must only define its constants/functions, never call cloud APIs.
            spec = importlib.util.spec_from_file_location("_demo_check_" + mapping["lesson"].replace('.', '_') + '_' + demo["id"], script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            native += demo["implementation"] == "native_python"
            pieces = []
            for name, value in vars(module).items():
                if name == "COMMANDS" or name.startswith("COMMANDS_"):
                    assert isinstance(value, str), (script, name)
                    pieces.append(value)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "shell" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    pieces.append(node.args[0].value)
            for code in pieces:
                result = subprocess.run([bash, "-n"], input=code, text=True, encoding="utf-8", capture_output=True)
                if result.returncode:
                    syntax_errors.append(f"{script}: {result.stderr}")
                commands += 1
        if mapping["source_kind"] == "main_html":
            assert sorted(covered) == list(range(1, mapping["source_window_count"] + 1)), (path, covered)
            windows += len(covered)
        if mapping.get("curated"):
            actual = {p.relative_to(path.parent).as_posix() for p in path.parent.rglob("*.py")}
            assert actual == {r["file"] for r in mapping["demos"]}, (path, "Unmapped/obsolete lesson files", actual)
        readme = (path.parent / "README.md").read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", readme):
            if "://" not in link:
                assert (path.parent / link.split('#')[0]).is_file(), (path, link)
    assert not syntax_errors, "\n".join(syntax_errors)
    assert seen == expected, {"missing": sorted(expected - seen), "extra": sorted(seen - expected)}
    for script in WORKSHOP.rglob('*.py'):
        if 'tests' in script.relative_to(WORKSHOP).parts or 'results' in script.relative_to(WORKSHOP).parts:
            continue
        for node in ast.walk(ast.parse(script.read_text(encoding='utf-8'))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node)
                assert doc and 'Example:' in doc, (script, node.name, 'Missing summary/usage example')
                documented += 1
    link_problems, links = check_links()
    assert not link_problems, "\n".join(link_problems)
    print(json.dumps({"modules": len(manifest["modules"]), "lessons": len(seen),
                      "native_python_demos": native, "bash_workflows_syntax_checked": commands,
                      "all_html_code_windows_accounted_for": windows, "links_checked": links, "cloud_calls": 0}, indent=2))
    print(json.dumps({'html_bash_windows_syntax_checked': raw_commands, 'html_python_cells_compiled': raw_python,
                      'html_inline_python_compiled': inline_python, 'documented_functions_and_classes': documented}, indent=2))


if __name__ == "__main__":
    main()
