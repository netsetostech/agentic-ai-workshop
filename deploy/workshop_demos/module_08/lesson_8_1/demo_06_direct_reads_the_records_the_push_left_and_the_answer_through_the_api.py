"""Lesson 8.1: Direct reads: the records the push left, and the answer through the API

Firestore read directly with your own credentials, then the API's two doors onto the same records: the ledger it serves and the question it answers. The push ended in writes, and two keys find them all without a search, as lesson 1.4 showed. The ledger row is named after the object, sources/acme~pubsub_trace_note.md, and it names the version's key, doc_key. The cell reads the ledger row, the claim, the version's chunk rows and acme's ledger summary, and holds each generation against the object's: Three generations, one number: the object's, the ledger's and the claim's. That equality is the trace's proof that one notice, delivered and acknowledged, produced every record. The chunk rows are the three the worker's chunker cuts from the note by its two rules, a chunk for each ## section and a preamble for the text above the first heading: preamble, NG-01, NG-02. This page ran the worker's own _chunk() on the note when it was built, and it cut the same three. Last, the API's two doors onto the same records. GET /v1/sources is the ledger as the UI's Versions table draws it, asked here as the UI's service account; POST /v1/query asks step 3's question again:

Run order inside this file:
1. Direct reads: the records the push left, and the answer through the API (source window 22)
2. Direct reads: the records the push left, and the answer through the API (source window 24)

Prerequisites: demo_05_rest_the_trace_hop_by_hop_and_the_subscription_as_pub_sub_holds_it.
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


def step_01_direct_reads_the_records_the_push_left_and(session):
    """Run Direct reads: the records the push left, and the answer through the API at this checkpoint.

    Firestore read directly with your own credentials, then the API's two doors onto the same records: the ledger it serves and the question it answers. The push ended in writes, and two keys find them all without a search, as lesson 1.4 showed. The ledger row is named after the object, sources/acme~pubsub_trace_note.md, and it names the version's key, doc_key. The cell reads the ledger row, the claim, the version's chunk rows and acme's ledger summary, and holds each generation against the object's:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (Firestore reads and one Cloud Storage read; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/trace_records.txt]
    """
    import json, os, subprocess, urllib.parse, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    P, NAME = os.environ["PROJECT"], "acme/pubsub_trace_note.md"
    TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    req = urllib.request.Request(f"https://storage.googleapis.com/storage/v1/b/{P}-uploads/o/{urllib.parse.quote(NAME, safe='')}",
                                 headers={"Authorization": f"Bearer {TOKEN}"})
    gen = str(json.load(urllib.request.urlopen(req, timeout=60))["generation"])
    db = firestore.Client(project=P)
    src = db.document("sources/" + NAME.replace("/", "~")).get().to_dict() or {}
    key = src.get("doc_key") or ""
    claim = (db.document(f"documents/{key}").get().to_dict() or {}) if key else {}
    rows = (db.collection("chunks").where(filter=FieldFilter("tenant_id", "==", "acme"))
            .where(filter=FieldFilter("source_uri", "==", f"gs://{P}-uploads/{NAME}")).stream())
    mine = sorted((s for s in rows if (s.to_dict() or {}).get("doc_key") == key), key=lambda s: int(s.id.rsplit("#", 1)[1]))
    led = db.document("ledger/acme").get().to_dict() or {}
    same = lambda g: "yes" if str(g) == gen else "NO"
    print(f"the object:  generation {gen}")
    print(f"sources/{NAME.replace('/', '~')}: {src.get('status')}, generation {src.get('generation')} (the object's: "
          f"{same(src.get('generation'))}), chunks {src.get('chunks')}, reused {src.get('reused')}, embedded {src.get('embedded')}")
    print(f"documents/{key[:13]}...: {claim.get('status')}, generation {claim.get('generation')} (the object's: "
          f"{same(claim.get('generation'))}), chunks {claim.get('chunks')}")
    print(f"chunks of this version: {len(mine)}, {sum(1 for s in mine if s.to_dict().get('current'))} current, "
          f"locators {', '.join(s.to_dict().get('locator') or '?' for s in mine)}")
    print(f"ledger/acme: fingerprint {str(led.get('fingerprint'))[:8]}..., versions {led.get('versions')}, last_event {led.get('last_event')}")

# Original CLI workflow for step_02_direct_reads_the_records_the_push_left_and.
COMMANDS_02 = """TOKEN="$(tok "$API")" python - <<'PY'
import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
API, TOKEN, NAME = os.environ["API"], os.environ["TOKEN"], "acme/pubsub_trace_note.md"
QUESTION = "After 9 pm, where do couriers deliver at the Bhiwandi depot, and who signs for the parcel?"


def call(path, body=None):
    \"\"\"GET or POST one DocuMind API path as the UI's service account; returns the parsed JSON.\"\"\"
    req = urllib.request.Request(API + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))


row = next((r for r in call("/v1/sources?tenant_id=acme")["sources"] if r["name"] == NAME), {})
print(f"GET /v1/sources: {NAME} {row.get('status')}, generation {row.get('generation')}, chunks {row.get('chunks')}, "
      f"embedded {row.get('embedded')}, held in {', '.join(sorted(row.get('mirrored') or {})) or 'the kit rows only'}")
ans = call("/v1/query", {"query": QUESTION, "tenant_id": "acme", "stream": False})
print(f"POST /v1/query: {ans['answer'][:160]}")
for c in ans["citations"]:
    if c["source_uri"].endswith(NAME):
        print(f"  cites {c['chunk_id'][:17]}...#{c['chunk_id'].rsplit('#', 1)[1]}: {c['quote'][:70]}")
s = ans.get("stages") or {}
print(f"  answerable {ans['answerable']}, backend {s.get('retrieval_backend')}, pool {s.get('pool')}, from the index {s.get('vector_chunks')}")
PY

"""

def step_02_direct_reads_the_records_the_push_left_and(session):
    """Run Direct reads: the records the push left, and the answer through the API at this checkpoint.

    Three generations, one number: the object's, the ledger's and the claim's. That equality is the trace's proof that one notice, delivered and acknowledged, produced every record. The chunk rows are the three the worker's chunker cuts from the note by its two rules, a chunk for each ## section and a preamble for the text above the first heading: preamble, NG-01, NG-02. This page ran the worker's own _chunk() on the note when it was built, and it cut the same three. Last, the API's two doors onto the same records. GET /v1/sources is the ledger as the UI's Versions table draws it, asked here as the UI's service account; POST /v1/query asks step 3's question again:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the ledger, then one answer: paise).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/trace_api.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_direct_reads_the_records_the_push_left_and),
        ('source_24', step_02_direct_reads_the_records_the_push_left_and),
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
