"""Lesson 8.2: Reconcile: the ledger against the bucket, the index against the rows, the golden rows

Lesson 1.8 ran the nightly walk: every object in the bucket against its ledger row in sources/. For each object, a generation the ledger already holds is ok; any other generation has its bytes hashed, and the hash decides. The bytes the ledger already names are a touch (record the generation, index nothing); bytes a claim indexed that the ledger never recorded are a backfill; bytes no claim holds are a reingest, which rewrites the object onto itself so the worker's own path runs again. Drift counts the sources the ledger had wrong. Nothing in either function reads the chunker. The walk compares names, generations and hashes of bytes, so it proves the ledger names what the bucket holds; it cannot prove which rule cut the rows. Run the kit's own planner over a stand-in lane, four nights in this lesson's life: Nothing in either function reads the chunker. The walk compares names, generations and hashes of bytes, so it proves the ledger names what the bucket holds; it cannot prove which rule cut the rows. Run the kit's own planner over a stand-in lane, four nights in this lesson's life: The second night is the case the walk exists for: had the re-issue's push been lost, the ledger would still name version 1 at generation 2, the walk would hash generation 3, find bytes no claim holds, and rewrite the object so the worker indexes it, cut by whatever pair the worker runs that night. The same bytes can be cut two ways depending on when they arrive. Now the real walk, the plan only, and the versions view after it: The ledger row is a summary. The rows are the evidence: the cell counts the handbook's rows by version and state, finds the longest current row, and checks whether two current rows hold version 1's vectors: NP-03, which the new rule left whole, and GEN-003, which it cut. Then it counts every tenant's current rows in Firestore and reads the Vector Search index's own count. The re-cut changed 544 vectors in the same index the questions search, so lesson 1.6's live gate, scoped to the handbook, is the check that matters. Every one of the ten rows asks about a real clause, and every real clause kept its text and its vector: what moved is the 544 windows of generated text beside them, now shorter and more numerous. The gate says whether the clauses still win.

Run order inside this file:
1. Definition (source window 34)
2. Definition (source window 36)
3. The rows and the index, read directly (source window 38)
4. The gate: the handbook's golden rows, asked again (source window 41)

Prerequisites: demo_07_rest_which_image_serves_and_how_many_tokens_a_new_chunk_is.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


def step_01_definition(session):
    """Run Definition at this checkpoint.

    Lesson 1.8 ran the nightly walk: every object in the bucket against its ledger row in sources/. For each object, a generation the ledger already holds is ok; any other generation has its bytes hashed, and the hash decides. The bytes the ledger already names are a touch (record the generation, index nothing); bytes a claim indexed that the ledger never recorded are a backfill; bytes no claim holds are a reingest, which rewrites the object onto itself so the worker's own path runs again. Drift counts the sources the ledger had wrong. Nothing in either function reads the chunker. The walk compares names, generations and hashes of bytes, so it proves the ledger names what the bucket holds; it cannot prove which rule cut the rows. Run the kit's own planner over a stand-in lane, four nights in this lesson's life:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; the kit's planner on a stand-in, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the re-issue landed: bucket and ledger at generation 3   ok        drift 0
    its push was lost: the ledger still names generation 2   reingest  drift 1
    the same bytes written again (generation 4)              touch     drift 0
    after the revert: version 1 again, at generation 5       ok        drift 0
    """
    import hashlib, sys
    sys.path.insert(0, "services/ingest")
    from reconcile import plan, decide_bytes, drift_of
    v1 = open("evals/corpus/acme/hr_policy_2026.md", "rb").read()
    sha = {"v1": hashlib.sha256(v1).hexdigest(), "r4": hashlib.sha256(b"<!-- r4 -->\n" + v1).hexdigest()}
    NAME, SID = "acme/hr_policy_2026.md", "acme~hr_policy_2026.md"
    def night(what, bucket_gen, bucket_bytes, ledger_gen, ledger_bytes, claimed):
        """One walk over a stand-in lane: the handbook's object against its ledger row, decided by the kit's own planner.
        
        Example: night('the re-issue landed: bucket and ledger at generation 3', '3', 'r4', '3', 'r4', ['v1', 'r4'])
        """
        row = {"gcs_uri": "gs://uploads/" + NAME, "generation": ledger_gen, "sha256": sha[ledger_bytes],
               "doc_key": "acme_" + sha[ledger_bytes], "status": "indexed"}
        claims = {"acme_" + sha[v]: {"status": "indexed"} for v in claimed}
        act = plan([{"name": NAME, "generation": bucket_gen, "tenant_id": "acme"}], {SID: row}, claims)[0]["action"]
        if act == "check_bytes":                          # the walk hashes the object only when the generations differ
            act = decide_bytes(sha[bucket_bytes], "acme", row, claims)
        print(f"{what:56} {act:9} drift {drift_of({act: 1})}")
    night("the re-issue landed: bucket and ledger at generation 3", "3", "r4", "3", "r4", ["v1", "r4"])
    night("its push was lost: the ledger still names generation 2", "3", "r4", "2", "v1", ["v1"])
    night("the same bytes written again (generation 4)", "4", "r4", "3", "r4", ["v1", "r4"])
    night("after the revert: version 1 again, at generation 5", "5", "v1", "5", "v1", ["v1", "r4"])

# Original CLI workflow for step_02_definition.
COMMANDS_02 = """make reconcile PROJECT=$PROJECT TENANT_ONLY=acme
make sources PROJECT=$PROJECT TENANT_ONLY=acme

"""

def step_02_definition(session):
    """Run Definition at this checkpoint.

    Nothing in either function reads the chunker. The walk compares names, generations and hashes of bytes, so it proves the ledger names what the bucket holds; it cannot prove which rule cut the rows. Run the kit's own planner over a stand-in lane, four nights in this lesson's life: The second night is the case the walk exists for: had the re-issue's push been lost, the ledger would still name version 1 at generation 2, the walk would hash generation 3, find bytes no claim holds, and rewrite the object so the worker indexes it, cut by whatever pair the worker runs that night. The same bytes can be cut two ways depending on when they arrive. Now the real walk, the plan only, and the versions view after it:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the plan only: nothing is applied).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/reconcile.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def step_03_the_rows_and_the_index_read_directly(session):
    """Run The rows and the index, read directly at this checkpoint.

    The ledger row is a summary. The rows are the evidence: the cell counts the handbook's rows by version and state, finds the longest current row, and checks whether two current rows hold version 1's vectors: NP-03, which the new rule left whole, and GEN-003, which it cut. Then it counts every tenant's current rows in Firestore and reads the Vector Search index's own count.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell: Firestore reads, one count, one GET).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/index_vs_ledger.txt]
    """
    import collections, hashlib, json, os, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    P, R = os.environ["PROJECT"], os.environ["REGION"]
    db = firestore.Client(project=P)
    eq = lambda q, field, value: q.where(filter=FieldFilter(field, "==", value))
    uri = f"gs://{P}-uploads/acme/hr_policy_2026.md"
    v1 = "acme_" + hashlib.sha256(open("evals/corpus/acme/hr_policy_2026.md", "rb").read()).hexdigest()
    rows = [s.to_dict() for s in eq(eq(db.collection("chunks"), "tenant_id", "acme"), "source_uri", uri).stream()]
    for (key, current), n in sorted(collections.Counter((r.get("doc_key", "?"), bool(r.get("current"))) for r in rows).items()):
        print(f"  {key[:13]}...  {'current' if current else 'retired':8} {n:>4} rows{'  (version 1)' if key == v1 else ''}")
    now = {r["locator"]: r for r in rows if r.get("current")}
    old = {r["locator"]: r for r in rows if r.get("doc_key") == v1}
    print(f"current: {len(now)} rows, the longest {max(len(r['text']) for r in now.values())} characters")
    for loc in ("NP-03", "GEN-003"):
        print(f"  {loc:8} current hash {now[loc]['chunk_hash'][:12]}  version 1's {old[loc]['chunk_hash'][:12]}  "
              f"same vector: {list(now[loc]['embedding']) == list(old[loc]['embedding'])}")
    current = int(eq(db.collection("chunks"), "current", True).count().get()[0][0].value)
    tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    url = f"https://{R}-aiplatform.googleapis.com/v1/projects/{P}/locations/{R}/indexes"
    for ix in json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"}), timeout=60)).get("indexes", []):
        print(f"index {ix['displayName']}: {int(ix.get('indexStats', {}).get('vectorsCount', 0)):,} vectors; Firestore: {current:,} current rows, all tenants")

# Original CLI workflow for step_04_the_gate_the_handbook_s_golden_rows_asked.
COMMANDS_04 = """make eval-live PROJECT=$PROJECT SOURCE=hr_policy_2026.md

"""

def step_04_the_gate_the_handbook_s_golden_rows_asked(session):
    """Run The gate: the handbook's golden rows, asked again at this checkpoint.

    The re-cut changed 544 vectors in the same index the questions search, so lesson 1.6's live gate, scoped to the handbook, is the check that matters. Every one of the ten rows asks about a real clause, and every real clause kept its text and its vector: what moved is the 544 windows of generated text beside them, now shorter and more numerous. The gate says whether the clauses still win.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (ten questions; a few rupees).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_live.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_definition),
        ('source_36', step_02_definition),
        ('source_38', step_03_the_rows_and_the_index_read_directly),
        ('source_41', step_04_the_gate_the_handbook_s_golden_rows_asked),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
