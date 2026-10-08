"""Map 1.1's authored checks to the actual numbered HTML sections.

Example: the same-bytes experiment belongs to section 5, not to a second demo.
Function bodies remain authored Python; the common renderer supplies the index.
"""
import ast

REVIEWED_SOURCE = '77b8143fc03414b24b415247dcdb9fa88ec56b1b'   # the Cohort 2 renumbering: prose, and Module 0 in window 1's two comments


def build_mapping(builder, folder, specification, path, sha, headings, windows):
    """Map every window and mark additional proofs as prose-derived.

    Example: windows 21 and 23 map to the version functions in section 5.
    """
    if sha != REVIEWED_SOURCE:
        raise ValueError('Lesson 1.1 HTML changed; review examples and UI prerequisites.')
    from pagekit.demo_links import sections, strip_links
    page = strip_links(path.read_text(encoding='utf-8'))
    titles = {s['anchor']: s['heading'] for s in sections(page)}
    source = builder.published(folder, 'GUIDE.md')
    definitions = [('setup/prepare.py', [3], 'required', 'setup', ['demonstrate'])]
    for section, covered, functions in [
        (3, [9, 10, 12], ['establish_roster', 'compare_access', 'inspect_membership']),
        (4, [16, 18], ['trace_source']),
        (5, [21, 23], ['upload_same_bytes', 'inspect_indexed_versions']),
        (6, [26, 28], ['inspect_citations', 'inspect_locators']),
        (7, [32, 34], ['compare_filters', 'compare_tenant_chunks']),
        (8, [], ['prove_local_contract_rules']),
    ]:
        anchor = f's{section}'
        filename = f'demo_{section:02}_{builder.slug(titles[anchor],80)}.py'
        definitions.append((filename, covered, 'required', anchor, functions))
    definitions.append(('setup/finish.py', [5], 'cleanup', 'setup', ['demonstrate']))
    used, records, required = {1}, [], []
    for filename, covered, category, anchor, functions in definitions:
        used.update(covered)
        text = (folder / filename).read_text(encoding='utf-8')
        tree = ast.parse(text)
        nodes = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        source_windows = [w for w in windows if w['window'] in covered]
        purpose = ast.get_docstring(tree).split('\n\n')[1]
        steps = []
        for index, function in enumerate(functions):
            w = source_windows[min(index, len(source_windows)-1)] if source_windows else None
            steps.append({'id': 'source_' + str(w['window']) if w else 'source_prose_rules', 'function': function, 'window': w['window'] if w else None,
                'source_line': w['line'] if w else None, 'heading': titles[anchor],
                'subheading': w['subheading'] if w else 'Local proofs from the explanation and checklist',
                'purpose': ast.get_docstring(nodes[function]), 'label': w['label'] if w else 'Local Python; no network',
                'expected': w['expected'] if w else 'Rewrapping retains the chunk hash; a root object is refused.',
                'adaptations': ['Retain the authored contract assertions and exact-generation checks.'],
                'manual_checkpoint': 'Upload evals/demo/gratuity_amendment_2026.md in the ACME UI before Run. ACME_UPLOAD="operator" is an explicitly labelled alternative.' if function == 'upload_same_bytes' else None})
        record = {'id': filename.removesuffix('.py').replace('/', '_'), 'lesson': '1.1', 'file': filename,
            'windows': covered, 'category': category, 'requires': required[-1:] if category == 'required' else [],
            'anchor': anchor, 'anchors': [anchor], 'section_number': int(anchor[1:]) if anchor != 'setup' else None,
            'heading': titles[anchor], 'purpose': purpose, 'implementation': 'native_python',
            'offline': anchor == 's8', 'live_verified': False, 'source': source,
            'source_lines': [w['line'] for w in source_windows], 'steps': steps}
        records.append(record)
        if category == 'required':
            required.append(record['id'])
    for index, record in enumerate(records):
        record['next'] = records[index+1]['file'] if index+1 < len(records) else 'Lesson finished; start_new_session.py enables a deliberate replay.'
    reading = [{k: w[k] for k in ('window','label','heading','anchor','line')} for w in windows if w['window'] not in used]
    assert all(not w['copy'] for w in windows if w['window'] not in used)
    mapping = {'schema_version': 4, 'layout_version': 3, 'curated': True, 'lesson': '1.1', 'title': specification['name'],
        'source_kind': 'main_html', 'source': source, 'source_page': path.name, 'source_sha': sha,
        'shared_setup_windows': [1], 'source_window_count': len(windows),
        'persist_variables': ['API','API_URL','ME','NUMBER','PROJECT','REGION','TENANT'],
        'headings': [{'level': h['level'], 'heading': h['text']} for h in headings],
        'demos': records, 'read_only_windows': reading,
        'prerequisites': 'Module 0 deployment and seeded HR/Code on Wages documents. Section 5 requires the exact amendment uploaded in the ACME UI before Run. Later sections use those saved generations.',
        'prose_checkpoints': [
            {'anchor': 's5', 'file': records[3]['file'], 'function': 'upload_same_bytes', 'proof': 'ACME UI upload required; operator mode is a labelled alternative.'},
            {'anchor': 's6', 'file': records[4]['file'], 'function': 'inspect_citations', 'proof': 'Ask both the Markdown and PDF question.'},
            {'anchor': 's8', 'file': records[6]['file'], 'function': 'prove_local_contract_rules', 'proof': 'Local validators prove rewrapping identity and root-object rejection; this is not a live poison upload.'}],
        'live_verification': 'Offline/source checks; workstation execution is required for IAM, indexing and model results.'}
    from group_workshop_demos import write_documentation
    write_documentation(builder, folder, mapping, page)
    return mapping
