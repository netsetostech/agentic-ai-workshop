"""Add reviewed explanations to the small functions embedded in lesson cells.

Example: document(source, '2.2') describes index_leg's sparse dot product without
changing its statements. A docstring-stripped AST comparison guards every edit.
"""
import ast
import copy
import re

# These explanations are about the actual nested lesson implementations, not
# replacement implementations. The call example is taken from the same source.
NESTED = {
    # B.1's cells
    'Api': 'A stand-in API on 127.0.0.1 with JSON routes, so an HTTP call can be made with no account and no network.',
    'reply': "Send this status and JSON body as the response, and note the request in the server's own log.",
    'do_GET': "Answer a GET on this stand-in server the way the lesson's scenario needs: an answer, a delay or a failure.",
    'do_POST': 'Answer a POST: read the body, refuse a missing bearer token with 401, echo the JSON it received with 200.',
    'log_message': "Silence the standard library server's per-request log lines, which would otherwise go to stderr.",
    'Slow': 'A stand-in server whose every answer takes the same fixed wait, to show calls overlapping or queueing.',
    'fetch': 'Make one blocking HTTP call to the stand-in server and return the name it answers with.',
    'fetch_in_async_def': 'The blocking call inside async def: it still blocks the event loop, which the timing shows.',
    'gather_blocking': 'Await two blocking calls with asyncio.gather; they run one after the other, each blocking the loop.',
    'gather_threads': 'Await two calls with asyncio.gather, each in its own thread through asyncio.to_thread, so they overlap.',
    'timed': 'Run one way of making the two calls and print how many fixed waits it took and whether they overlapped.',
    'Unreliable': 'A stand-in server that fails the three ways real services do: a 503 blip, a hang and an empty 200.',
    'get': 'Make one GET with a timeout and return (status, body); a timeout or a refused connection gives status 0.',
    'well_formed': "Check that an answer has the four fields of the kit's answer shape, each with the right type.",
    'send_json': 'Send this status with a JSON body and its length.',
    'embed': 'Embed this text under the selected document/query task type so the lesson can compare the vectors.',
    'cosine': 'Compute the cosine between two vectors to compare direction independently of their lengths.',
    # B.3's cells
    'softmax': "Turn each row of scores into probabilities that add up to 1 (the row's largest taken off first, against overflow).",
    'head': 'One attention head: scaled dot products of queries and keys, an optional causal mask, softmax, then the weighted sum of values.',
    'attention': "Run the lesson's two heads side by side, join their outputs and mix them through W_O.",
    'cos': 'Cosine per word between two matrices: 1 is the same direction, 0 unrelated.',
    'gaps': 'Distances between every pair of word vectors: return the closest two and the farthest two, rounded.',
    'layer_norm': 'Layer normalization per word: subtract the mean, divide by the standard deviation, then scale and shift when given.',
    'feed_forward': "The block's feed-forward part, each word alone: widen, ReLU, narrow back.",
    'block': "One transformer block in the 2017 paper's order: attention, add, norm; then feed-forward, add, norm.",
    'block_norm_first': "One transformer block in GPT-2's order: norm first inside each part, then add the residual.",
    'pairs': 'How many token pairs one attention head scores in one layer for n tokens: n times n.',
    'cut': 'Parse and chunk the supplied handbook input with the kit parser; retain its real section identities.',
    'measure': 'Compare old/new chunks through the kit reuse planner and print the changed-versus-reused counts.',
    # B.4's cells
    'sentences': 'Split a text into sentences at full stops, semicolons, question marks and exclamation marks.',
    'words': 'Lower-case a sentence and return its words and numbers, decimals kept whole.',
    'fill': "Hide one word of a clause's sentence and count which words the rest of the text puts in that gap.",
    'verdict': 'Name the candidate the counts favour, a tie, or that nothing in the text fits.',
    'known': 'Return the words of a text that the toy vocabulary knows, in order.',
    'encode': 'The toy bi-encoder: one text in, one vector out, from the axes of the words it knows; no other text is seen.',
    'ideas': 'The axes of the words a text knows, in order, with repeats merged.',
    'aligned': "Count how many of the question's ideas a sentence holds in the same order, gaps allowed.",
    'cross': "The toy cross-encoder: read question and passage together and score the passage's best-aligned sentence.",
    'tok': 'Mint a fresh identity token for this service account and the API audience; never save the credential.',
    'index_leg': 'Encode the chunk text sparsely and sum query-weight times chunk-weight for shared hashed dimensions.',
    'ask': 'Send this example request to the selected API and return its response for the following comparison.',
    'run': 'Run the specified CLI argument list and return its output; propagate command failures.',
    'output': 'Read the named Terraform output used to identify the actual deployed vector resources.',
    'read_run': 'Read the requested Cloud Run resource as JSON to inspect its deployed configuration.',
    'chunks_of': 'Parse and chunk this corpus file into the payloads consumed by the context packer.',
    'gcloud': 'Run this cell\'s gcloud command with its project/region context and decode the requested output.',
    'gc': 'Run the requested gcloud inspection and return its decoded JSON for this section.',
    'rows': 'Read usage log rows for the specified service and event so the brain costs can be compared.',
    'main': 'Run this cell\'s asynchronous MCP operation and print its returned tool declarations or evidence.',
    'client': 'Create the MCP client with the current bearer token for this local transport call.',
    'mint': 'Mint a token for the requested account/audience; varying its email claim tests an admission boundary.',
    'call': 'Perform the current transport request and expose its actual response for the lesson comparison.',
    'api': 'Read the specified authenticated API path as JSON while tracing the current source version.',
    'cause': 'Classify the observed version/retrieval markers into the kit\'s wrong-answer cause.',
    'between': 'Select the source excerpt between two markers so the inspection uses the current kit code.',
    'Brief': 'Collect a concise trace of mirror decisions in this offline simulation; this does not write a cloud audit record.',
    'Store': 'Simulate a named regional managed store for the real mirror policy functions without making network calls.',
    'Table': 'Provide the Firestore-like query surface used by the offline propagation example.',
    'emit': 'Print the simulated audit event so the policy decision is visible beside the store operations.',
    'upsert': 'Record/print the simulated tenant document upsert; no managed GCP store is modified.',
    'delete': 'Record/print the simulated tenant document deletion for the mirror lifecycle comparison.',
    'listing': 'Return the simulated store records belonging to this tenant for the freshness check.',
    'where': 'Return a query with the additional equality filter used by this offline Firestore-shaped stub.',
    'stream': 'Yield simulated document snapshots that satisfy this table\'s accumulated filters.',
    'current': 'Construct the current source-ledger fact used by the simulated mirror event.',
    'doc': 'Construct the document/chunk fact corresponding to this version key in the offline scenario.',
    'check': 'Run the actual freshness check against the current simulated ledger and store contents.',
    'logs': 'Read the scoped log events for this mirror/policy observation with the requested result limit.',
    'show': 'Print the selected event fields that explain the mirror decision.',
    'Blob': 'Simulate the Storage blob operations used to test the media contract offline.',
    'Voice': 'Simulate streaming speech responses so voice event handling can be checked without a model call.',
    'exists': 'Report whether the simulated blob exists for this branch of the media example.',
    'download_as_bytes': 'Return the simulated blob bytes to the kit media path under test.',
    'upload_from_string': 'Capture the generated media bytes in the local stub instead of uploading to Storage.',
    'streaming_synthesize': 'Yield the fixture speech responses for the supplied request stream.',
    'door': 'Try the upload contract with this filename and content type and print admission or refusal.',
    'logged': 'Read the specified training/evaluation log event so the dataset verdict uses recorded evidence.',
    'recorded': 'Wrap the existing HTTP request to retain the actual backend response used by the comparison.',
    'read': 'Read the exact source ledger, content claim and current chunks for the saved object generation.',
    # B.5's cells
    'draws': 'Yield the seeded draws in [0, 1) the toy decoder picks with, so one seed gives the same picks on every laptop.',
    'shaped': "Apply temperature, top-k and top-p to one step's logits and return the probabilities the pick draws from.",
    'sample': 'Pick the first candidate whose running total of probability passes the draw u.',
    'generate': 'Run the toy decode loop (score, shape, pick, append) from one seed until the end token or the cap.',
}
CLASS_SUMMARIES = {
    'ApiClient': 'Call the deployed lesson API with audience-bound authentication and explicit project configuration.',
    'ArtifactStore': 'Keep a separate evidence directory and outcome manifest for one local demonstration.',
    'BoundedRequest': 'Bound ADC refresh HTTP waits so expired workstation credentials fail with an actionable message.',
    'DemoConfig': 'Hold validated kit paths, project, region, service names and local result locations for every lesson.',
    'DemoContext': 'Provide a scoped preflight with lazy clients, actual kit functions and retained evidence.',
    'ServingConfig': 'Describe the inspected traffic-serving revision and its permitted literal environment values.',
    'KitAdapter': 'Load the installed kit\'s reconciliation functions directly instead of maintaining a teaching copy.',
}
EXAMPLES = {
    'ApiClient': 'client = ApiClient(config); response = client.request("/health")',
    'ArtifactStore': 'store = ArtifactStore(config, "planner"); store.save("plan", report)',
    'BoundedRequest': 'credentials.refresh(BoundedRequest()) inside checked_credentials()',
    'DemoConfig': 'config = load_config(); print(config.kit_root, config.project)',
    'DemoContext': 'with DemoContext("preflight", live=False) as context: print(context.kit)',
    'ServingConfig': 'serving = read_serving(config, config.api_service); print(serving.revision)',
    'KitAdapter': 'kit = KitAdapter(config.kit_root); report = evaluate_widget(kit, rows)',
    'LessonCloud': 'cloud = LessonCloud(session); rows = cloud.chunks("acme", "hr_policy_2026.md")',
    'DemoSession': 'with DemoSession(__file__, live=False) as session: demonstrate(session)',
    'ManualCheckpoint': 'manual_checkpoint("Upload the exact fixture in the UI") pauses until the learner types done',
    'secret_name': 'secret_name("AUTHORIZATION") is True; secret_name("TOP_K_RETRIEVE") is False',
    'utc_now': 'session.state["observed_at"] = utc_now()',
    'json_default': 'json.dumps({"path": Path("report.json")}, default=json_default)',
    'write_json': 'write_json(session.directory / "report.json", report)',
    'gcloud': 'gcloud("config", "get-value", "project")',
    'checked_credentials': 'credentials = checked_credentials() before constructing a live SDK client',
    'identity_token': 'token = identity_token(config, config.api_base_url) in an authenticated request',
    'load_config': 'config = load_config() reads settings.local.json and retains its explicit project',
    'select_revision': 'revision = select_revision(service_json) rejects ambiguous split traffic',
    'read_serving': 'serving = read_serving(config, "documind-api")',
    'expect_failure': 'expect_failure(session, args, status=2, messages=["expected diagnostic"])',
    'expect_guard': 'expect_guard(session, args, stop="STOP") checks the guard text as well as exit 2',
    'live_gate': 'live_gate(session, report="/tmp/gate.json", api=candidate_url) retains a fresh candidate report',
    'require': 'require(bool(answer.get("citations")), "No cited answer")',
    'require_fresh_vector': 'require_fresh_vector(answer) rejects a cached answer as retrieval proof',
    'version_ready': 'version_ready(expected, source, claim, chunks) checks the saved generation',
    'poll_until': 'poll_until(read_state, is_ready, seconds=60, interval=2)',
    'prepare_cache': 'prepare_cache(session, disable=True) saves the previous setting before an update',
    'restore_cache': 'restore_cache(session) restores the value saved during preparation',
    'create_drill': 'create_drill(session) saves this run\'s unique zero-byte PDF identity',
    'matches': 'matches(payload, saved) refuses another object generation',
    'inspect_dead_letter': 'inspect_dead_letter(session, acknowledge=False) observes only this drill',
    'finish_drill': 'finish_drill(session) removes only this run\'s owned fixture',
    'evaluate_widget': 'report = evaluate_widget(kit, rows) uses the HTML widget\'s five simulated documents',
    'evaluate': 'report = evaluate(kit, objects, ledger, documents, sha_for)',
    'print_plan': 'print_plan(report) prints each decision and the resulting drift count',
    'manual_checkpoint': 'manual_checkpoint("Upload the exact visitor note, then refresh until indexed")',
    'native_context': 'with native_context(session): step(session) isolates the cell\'s import changes',
    'run_steps': 'run_steps(session, [("read", inspect_rows), ("compare", compare_rows)])',
    'backup_files': 'backup_files(session, ["evals/golden.jsonl"]) saves exact existing bytes',
    'restore_files': 'restore_files(session) restores those saved bytes and retains the lesson edits',
}


def without_docs(tree):
    """Normalize docstrings only; e.g. compare this dump before and after documentation."""
    tree = copy.deepcopy(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
    return ast.dump(tree, include_attributes=False)


def document(source, context):
    """Supply summary/usage examples to every definition, preserving executable AST.

    Example: document(source, 'lesson 7.4') documents local stub classes too.
    Existing substantive documentation is retained, not replaced by a template.
    """
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    starts, count = [], 0
    for line in lines:
        starts.append(count)
        count += len(line)
    def offset(line, column):
        """Translate an AST UTF-8 column; e.g. retain Unicode text before a docstring."""
        return starts[line-1] + len(lines[line-1].encode('utf-8')[:column].decode('utf-8'))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    changes = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        old = ast.get_docstring(node)
        if old and 'Example:' in old:
            continue
        name = node.name
        if not old:
            old = CLASS_SUMMARIES.get(name) or NESTED.get(name)
            if name == '__init__':
                old = 'Initialize this local simulation from the supplied fixture values; no cloud client is created.'
            if not old:
                raise ValueError(f'{context}: write a specific summary for {name} before generating it')
        matched = next((c for c in calls if (isinstance(c.func, ast.Name) and c.func.id == name or isinstance(c.func, ast.Attribute) and c.func.attr == name)), None)
        if matched:
            example = ast.unparse(matched)
            if len(example) > 220:
                example = None
        else:
            example = None
        if not example:
            example = EXAMPLES.get(name)
        if not example:
            if name in {'__enter__', '__exit__'}:
                example = 'Use the owning class with a with statement; context entry/exit invokes this method.'
            elif name == '__init__':
                example = 'Construct the owning class with the arguments shown above; subsequent methods reuse these settings.'
            elif name == 'main':
                example = 'Run this file in the configured IDE interpreter; its __main__ guard calls main().'
            elif isinstance(node, ast.ClassDef):
                example = 'See the instance constructed in this lesson step and inspect its state in the debugger.'
            else:
                args = [a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs if a.arg not in {'self','cls'}]
                example = ('self.' if node.args.args and node.args.args[0].arg == 'self' else '') + name + '(' + ', '.join(args) + ') in the owning lesson/helper context'
        doc = old + '\n\nExample: ' + example + '\n'
        indent = ' ' * (node.col_offset + 4)
        quoted = '"""' + doc.replace('\\', '\\\\').replace('"""', '\\"\\"\\"').replace('\n', '\n' + indent) + '"""'
        first = node.body[0]
        start = offset(first.lineno, first.col_offset)
        if ast.get_docstring(node) is not None:
            end = offset(first.end_lineno, first.end_col_offset)
            changes.append((start, end, quoted))
        else:
            # A one-line function needs a real indented body before its existing
            # statement. Multi-line bodies keep comments and statement bytes.
            prefix = '\n' + indent if first.lineno == node.lineno else ''
            changes.append((start, start, prefix + quoted + '\n' + indent))
    for start, end, replacement in sorted(changes, reverse=True):
        source = source[:start] + replacement + source[end:]
    assert without_docs(tree) == without_docs(ast.parse(source)), context
    return source
