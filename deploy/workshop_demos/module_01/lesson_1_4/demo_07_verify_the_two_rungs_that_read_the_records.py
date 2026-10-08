"""Lesson 1.4: Verify: the two rungs that read the records

The first cell runs the Firestore rung's exact query with the note's own vector: itself first, at a cosine distance of zero. The second asks the API a question only the note can answer and prints which rung served it and how many of the pooled chunks came from the index. The kit ships two read-only commands for exactly this lesson. verify-vector-index.py reads Terraform's outputs and asks the API whether the index Terraform declared is the one attached to the endpoint, streaming, 768-dimensional, deployed exactly once; it needs a checkout with Terraform state, and the two gcloud reads in step 5 are the same checks by hand. check-firestore-fallback.py takes the handbook, proves the ledger row names the bytes in your checkout, and runs the Firestore rung with combined filters in both current modes; it imports the API's own modules, so it needs the API's packages in your venv. Both write their evidence under operator-evidence/. Their tests run offline in a fraction of a second.

Run order inside this file:
1. Do it: the fallback rung, then the API (source window 37)
2. The operator's checks: two commands, and their tests (source window 39)

Prerequisites: demo_06_inspect_the_mirror_and_the_audit_trail.
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


# Original CLI workflow for step_01_the_fallback_rung_then_the_api.
COMMANDS_01 = """python - <<'PY'
import os, hashlib, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
PROJECT = os.environ["PROJECT"]
db = firestore.Client(project=PROJECT)
NOTE = os.environ.get("NOTE", os.path.expanduser("~/lesson34_note.md"))    # the note you wrote in step 3
sha = hashlib.sha256(open(NOTE, "rb").read()).hexdigest()
cid = f"acme:{sha}#1"
vec = list(db.collection("chunks").document(cid).get().to_dict()["embedding"])
q = db.collection("chunks").where("tenant_id", "==", "acme").where("current", "==", True)      # the rung's predicates
hits = q.find_nearest("embedding", Vector(vec), distance_measure=DistanceMeasure.COSINE, limit=3, distance_result_field="d").get()
for h in hits:
    d = h.to_dict()
    print(f"  {h.id.split('#')[0][:18]}...#{h.id.rsplit('#', 1)[1]}  {d['locator']:9} cosine distance {d['d']:.4f}" + ("   <- itself" if h.id == cid else ""))
PY

curl -s -X POST $API/v1/query -H "Authorization: Bearer $(tok $API)" -H "Content-Type: application/json" \\
  -d '{"query":"Where is the smoke lantern kept, and how often is it checked?","tenant_id":"acme","stream":false}' \\
  | python -c "import json,sys; j=json.load(sys.stdin); print(j['answer'][:150]); print([(c['chunk_id'].split('#')[1], c['source_uri'].split('/')[-1]) for c in j['citations'][:2]]); s=j['stages']; print('backend', s['retrieval_backend'], '| pool', s['pool'], '| from the index', s['vector_chunks'])"

"""

def step_01_the_fallback_rung_then_the_api(session):
    """Run Do it: the fallback rung, then the API at this checkpoint.

    The first cell runs the Firestore rung's exact query with the note's own vector: itself first, at a cosine distance of zero. The second asks the API a question only the note can answer and prints which rung served it and how many of the pooled chunks came from the index.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme:9c41d0e2b7f5...#1  SM-01     cosine distance 0.0000   <- itself
      acme:9c41d0e2b7f5...#2  SM-02     cosine distance 0.2xxx
      acme:9c41d0e2b7f5...#0  preamble  cosine distance 0.3xxx
    The smoke lantern is kept in bay 4 of the Pune warehouse and is checked on the first Monday of every month ... [Source 1]
    [('1', 'smoke_note_v1.md'), ('2', 'smoke_note_v1.md')]
    backend vector | pool 20 | from the index 20
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_operator_s_checks_two_commands_and_the.
COMMANDS_02 = """python commands/verify-vector-index.py --deploy-root "$DEMO_ROOT" --project "$PROJECT" --region "$REGION"

GOOGLE_CLOUD_PROJECT="$PROJECT" python commands/check-firestore-fallback.py

python -m unittest discover -s commands/tests -p test_verify_vector_index.py
python -m unittest discover -s commands/tests -p test_check_firestore_fallback.py

"""

def step_02_the_operator_s_checks_two_commands_and_the(session):
    """Run The operator's checks: two commands, and their tests at this checkpoint.

    The kit ships two read-only commands for exactly this lesson. verify-vector-index.py reads Terraform's outputs and asks the API whether the index Terraform declared is the one attached to the endpoint, streaming, 768-dimensional, deployed exactly once; it needs a checkout with Terraform state, and the two gcloud reads in step 5 are the same checks by hand. check-firestore-fallback.py takes the handbook, proves the ledger row names the bytes in your checkout, and runs the Firestore rung with combined filters in both current modes; it imports the API's own modules, so it needs the API's packages in your venv. Both write their evidence under operator-evidence/. Their tests run offline in a fraction of a second.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (all read-only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Project: documind-ai-YOUR-ID (NUMBER)
    Terraform index: projects/documind-ai-YOUR-ID/locations/asia-south1/indexes/1234567890123456789
    Terraform endpoint: projects/documind-ai-YOUR-ID/locations/asia-south1/indexEndpoints/9876543210987654321
    API index: projects/NUMBER/locations/asia-south1/indexes/1234567890123456789
    API endpoint: projects/NUMBER/locations/asia-south1/indexEndpoints/9876543210987654321
    Index dimensions: 768; update method: STREAM_UPDATE
    Global vector count: 1745
    Deployment: documind_chunks_v1
    Deployment sync time: 2026-09-22T10:41:07.000Z
    PASS: the expected index is attached to the expected endpoint.
    This verifies attachment and configuration; ingestion and query checks are se
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_37', step_01_the_fallback_rung_then_the_api),
        ('source_39', step_02_the_operator_s_checks_two_commands_and_the),
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
