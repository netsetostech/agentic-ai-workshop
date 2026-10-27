"""Regressions for source-section identity and faithful documentation edits."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
from pagekit.demo_links import annotate, sections, strip_links
from pagekit import pagebuild
from workshop_docstrings import document, without_docs
import ast


class LayoutTests(unittest.TestCase):
    """Use minimal pages/fixtures to verify boundaries independent of real maps."""

    def test_unnumbered_setup_is_not_previous_numbered_section(self):
        page = '<div class="step" id="s2"><div class="step-n">2</div><h3>Definitions</h3></div><h3 id="setup">Setup</h3><div class="step" id="s5"><div class="step-n">5</div><h3>Version</h3></div>'
        self.assertEqual([(s['anchor'],s['number']) for s in sections(page)], [('s2',2),('setup',None),('s5',5)])
        with self.assertRaisesRegex(ValueError, 'disagree'):
            sections(page.replace('id="s5"','id="s6"'))

    def test_link_regeneration_never_changes_source_or_uses_old_ranges(self):
        page = '<div class="step" id="s5"><div class="step-n">5</div><h3>Version</h3>\n<p>Use the same bytes.</p></div>\n'
        mapping = {'demos': [{'file':'demo_05_version.py','anchor':'s5','anchors':['s5'],'category':'required'}]}
        shown = annotate('1.1',page,mapping)
        self.assertIn('agents_workshop_learner/blob/main/', shown)
        self.assertIn('demo_05_version.py', shown)
        self.assertEqual(strip_links(shown),page)
        self.assertEqual(annotate('1.1',shown,mapping),shown)

    def test_documentation_preserves_one_line_classes_and_literal_bytes(self):
        source = 'class Store:\n    def __init__(self, name, region): self.name = name; self.region = region\n\ndef embed(text, task):\n    fixture = """first line\nsecond line"""\n    return fixture, text, task\n'
        result = document(source,'fixture')
        self.assertEqual(without_docs(ast.parse(result)),without_docs(ast.parse(source)))
        self.assertEqual(document(result,'fixture'),result)
        self.assertIn('Example:', result)

    def test_runtime_counts_exclude_teaching_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            kit=Path(directory)
            for relative in ('services/worker.py','workshop_demos/module_04/demo.py','__pycache__/cached.py'):
                path=kit/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('audit_emit("doc.upload")')
            with patch.object(pagebuild,'KIT',kit):
                self.assertEqual([p.relative_to(kit).as_posix() for p in pagebuild.kit_runtime_files('*.py')],['services/worker.py'])

    def test_lesson_15_poison_cells_are_found_by_their_code(self):
        # Window numbers went stale once and the drill ran the page's wildcard delete; the roles follow the code.
        from workshop_demo_runtime_adaptations import poison_role
        self.assertEqual(poison_role('export POISON_SINCE="$(date)"\nmake poison PROJECT=$PROJECT TENANT=acme'), "create_drill")
        self.assertEqual(poison_role('make dlq PROJECT=$PROJECT\ngcloud pubsub subscriptions pull ingest-dlq-sub --limit 1'), "inspect_dead_letter")
        self.assertEqual(poison_role('gcloud pubsub subscriptions pull ingest-dlq-sub --limit 1 --auto-ack'), "finish_drill")
        self.assertEqual(poison_role('ACK="$(gcloud pubsub subscriptions pull ingest-dlq-sub --limit 10 --format=json)"\n'
                                     'gcloud pubsub subscriptions ack ingest-dlq-sub --ack-ids="$ACK"'), "finish_drill")
        self.assertIsNone(poison_role('make smoke PROJECT=$PROJECT'))

    def test_a_status_echo_runs_with_the_pages_shell_while_its_output_awaits(self):
        # 0.4's smoke without the tenant and 11.1-11.3's refused gates stopped their demos: no recorded output to read.
        from workshop_demo_runtime_adaptations import adapt
        cell = 'make gate PROJECT="$PROJECT"; echo "exit $?"'
        awaiting = {"window": 9, "expected": "[awaiting the author's run: data/gate.txt]"}
        code, body, changes = adapt("9.9", dict(awaiting), cell, None)
        self.assertTrue(code.startswith("set +e +o pipefail") and code.rstrip().endswith("true   # the status it printed is the cell's answer: compare it with the page's prose"), code)
        self.assertEqual(len(changes), 1)
        recorded_ok = {"window": 9, "expected": "PASS: gate green\nexit 0"}            # a recorded success: as written
        self.assertEqual(adapt("9.9", dict(recorded_ok), cell, None)[0], cell)
        no_echo = adapt("9.9", dict(awaiting), 'make gate PROJECT="$PROJECT"', None)  # no status asked for: as written
        self.assertEqual(no_echo[0], 'make gate PROJECT="$PROJECT"')
        self.assertEqual(adapt("9.9", dict(awaiting), cell, "print(1)")[0], cell)   # a Python body: the shell is not used


if __name__ == '__main__':
    unittest.main()
