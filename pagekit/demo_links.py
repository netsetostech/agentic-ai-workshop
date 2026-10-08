"""Connect each HTML heading to its published IDE examples without changing cells.

Example: ``annotate('2.2', page)`` inserts public learner links under the actual
section headings. ``strip_links(page)`` recovers the reviewed teaching source,
so regenerating links cannot invalidate its digest or renumber its code windows.
"""
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r'<!-- IDE-DEMO-LINKS -->.*?<!-- /IDE-DEMO-LINKS -->\n?', re.S)
PUBLIC = 'https://github.com/netsetos/agents_workshop_learner/blob/main/'


def strip_links(page):
    """Remove only this module's generated blocks; e.g. before hashing the source."""
    return BLOCK.sub('', page)


def sections(page):
    """Read visible section numbers and headings, including unnumbered setup.

    Example: section ``s5`` returns number 5; ``setup`` returns None. Reject a
    disagreement between the displayed number and anchor instead of guessing.
    """
    page = strip_links(page)
    markers = list(re.finditer(r'<div class="step" id="([^"]+)"|<h3 id="(setup)">', page))
    result = []
    for marker in markers:
        anchor = marker[1] or marker[2]
        heading = re.search(r'<h3\b[^>]*>(.*?)</h3>', page[marker.start():], re.S)
        if not heading:
            raise ValueError(f'Missing heading for {anchor}')
        number = None
        if anchor != 'setup':
            badge = re.search(r'<div class="step-n">(\d+)</div>', page[marker.start():marker.start()+heading.start()])
            if not badge or anchor != 's' + badge[1]:
                raise ValueError(f'Anchor and visible section number disagree: {anchor}')
            number = int(badge[1])
        result.append({'anchor': anchor, 'number': number, 'start': marker.start(),
                       'heading_end': marker.start()+heading.end(),
                       'heading': html.unescape(re.sub(r'<[^>]+>', '', heading[1])).strip()})
    return result


def annotate(lesson, page, mapping=None):
    """Render the matching files under every heading, never inside a code window.

    Example: a conditional repair in section 4 is labelled 'Recovery only'; it
    is not presented as the next required example. Links point at public files.
    """
    page = strip_links(page)
    major = lesson.split('.')[0]
    folder = f'workshop_demos/module_{major if major == "B" else f"{int(major):02}"}/lesson_{lesson.replace(".", "_")}'
    if mapping is None:
        path = ROOT / 'deploy' / folder / 'lesson_map.json'
        if not path.exists():
            return page
        mapping = json.loads(path.read_text(encoding='utf-8'))
    by_anchor = {}
    for record in mapping['demos']:
        for anchor in record.get('anchors', [record['anchor']]):
            by_anchor.setdefault(anchor, []).append(record)
    inserts = []
    for section in sections(page):
        records = by_anchor.get(section['anchor'], [])
        items = []
        if section['anchor'] == 'setup' or (lesson == '1.8' and section['anchor'] == 's3'):
            items.append('<li>First-time IDE setup: <a href="' + PUBLIC + 'workshop_demos/setup/README.md" target="_blank" rel="noopener">interpreter, configuration and authentication</a>.</li>')
        for record in records:
            label = {'required': 'Run here', 'cleanup': 'At lesson end', 'recovery': 'Recovery only', 'optional': 'Optional'}[record['category']]
            items.append('<li>' + label + ': <a href="' + PUBLIC + folder + '/' + record['file'] + '" target="_blank" rel="noopener"><code>' + html.escape(record['file']) + '</code></a>.</li>')
        if any(r['category'] == 'cleanup' for r in records) and any(r.get('orchestrator') for r in mapping['demos']):
            items.append('<li>At lesson end, run <a href="' + PUBLIC + folder + '/setup/finish.py" target="_blank" rel="noopener"><code>setup/finish.py</code></a> to execute all remaining restoration steps.</li>')
        if not items:
            continue
        block = '<!-- IDE-DEMO-LINKS --><div class="box" style="overflow-wrap:anywhere"><p><b>Run in your IDE</b> · The filename number is this HTML section number. Run the functions in their listed order; do not repeat the terminal cells as well.</p><ul>' + ''.join(items) + '</ul></div><!-- /IDE-DEMO-LINKS -->\n'
        inserts.append((section['heading_end'], block))
    for position, block in reversed(inserts):
        page = page[:position] + block + page[position:]
    return page
