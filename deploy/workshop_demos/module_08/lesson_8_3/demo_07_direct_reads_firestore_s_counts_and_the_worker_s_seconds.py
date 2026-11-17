"""Lesson 8.3: Direct reads: Firestore's counts and the worker's seconds

The rows the Firestore floor multiplies, and the one number no constant gives you: how long a document takes. Two reads finish the measurement. The first counts rows in Firestore without fetching them: a count() query returns one number instead of the rows it matched. chunk rows counts every version a tenant still holds: the current rows, and the rows a re-issue retired, which stay until their expire_at passes. current is what the index serves; added across the three tenants, it should match the index's vector count from steps 3 and 6. indexed sources is how many rows the fingerprint reads on every ingest to that tenant, which step 8 comes back to. Multiply your chunk rows by 59,092 bytes and you have your lane's Firestore floor for the chunks; for the 2,757 text chunks alone it is 155 MiB. At ten million documents it is 54.9 TiB. The second read is the calibration. Cloud Run logs every delivery Pub/Sub made to the worker, with its HTTP status and how long it took, so the median of those times is your lane's seconds per document. The cell saves the last month of deliveries, then counts them by status:

Run order inside this file:
1. Direct reads: Firestore's counts and the worker's seconds (source window 26)
2. Direct reads: Firestore's counts and the worker's seconds (source window 28)

Prerequisites: demo_06_rest_the_index_s_own_size.
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


def step_01_direct_reads_firestore_s_counts_and_the_wo(session):
    """Run Direct reads: Firestore's counts and the worker's seconds at this checkpoint.

    The rows the Firestore floor multiplies, and the one number no constant gives you: how long a document takes. Two reads finish the measurement. The first counts rows in Firestore without fetching them: a count() query returns one number instead of the rows it matched.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (nine Firestore count queries; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/firestore_counts.txt]
    """
    import os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    db = firestore.Client(project=os.environ["PROJECT"])
    count = lambda q: int(q.count().get()[0][0].value)          # one aggregation: billed by the index entries it reads, not by rows
    eq = lambda q, field, value: q.where(filter=FieldFilter(field, "==", value))
    print(f"{'tenant':7} {'chunk rows':>10} {'current':>8} {'indexed sources':>15}")
    for t in ("acme", "globex", "zeta"):
        rows = eq(db.collection("chunks"), "tenant_id", t)
        print(f"{t:7} {count(rows):>10,} {count(eq(rows, 'current', True)):>8,} "
              f"{count(eq(eq(db.collection('sources'), 'tenant_id', t), 'status', 'indexed')):>15,}")

# Original CLI workflow for step_02_direct_reads_firestore_s_counts_and_the_wo.
COMMANDS_02 = """gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" AND httpRequest.requestMethod="POST"' \\
  --project="$PROJECT" --freshness=30d --limit=1000 --format=json > ~/ingest-requests.json
python - <<'PY'
import json, os, statistics, warnings
warnings.filterwarnings("ignore", category=UserWarning)
by = {}
for e in json.load(open(os.path.expanduser("~/ingest-requests.json"))):
    h = e.get("httpRequest", {})
    by.setdefault(int(h.get("status", 0)), []).append(float(str(h.get("latency", "0s")).rstrip("s") or 0))
for status, secs in sorted(by.items()):
    secs.sort()
    print(f"HTTP {status}: {len(secs):>4} deliveries, median {statistics.median(secs):.1f} s, slowest {secs[-1]:.1f} s")
taken = sorted(s for status, secs in by.items() if 200 <= status < 300 for s in secs)
if taken:
    m = statistics.median(taken)
    print(f"at 10,000,000 documents, 30 at a time, {m:.1f} s each: {10000000 * m / 30 / 86400:,.1f} days")
PY

"""

def step_02_direct_reads_firestore_s_counts_and_the_wo(session):
    """Run Direct reads: Firestore's counts and the worker's seconds at this checkpoint.

    chunk rows counts every version a tenant still holds: the current rows, and the rows a re-issue retired, which stay until their expire_at passes. current is what the index serves; added across the three tenants, it should match the index's vector count from steps 3 and 6. indexed sources is how many rows the fingerprint reads on every ingest to that tenant, which step 8 comes back to. Multiply your chunk rows by 59,092 bytes and you have your lane's Firestore floor for the chunks; for the 2,757 text chunks alone it is 155 MiB. At ten million documents it is 54.9 TiB. The second read is the calibration. Cloud Run logs every delivery Pub/Sub made to the worker, with its HTTP status and how long it took, so the median of those times is your lane's seconds per document. The cell saves the last month of deliveries, then counts them by status:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one Cloud Logging read; writes one file in your home directory).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ingest_latency.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_direct_reads_firestore_s_counts_and_the_wo),
        ('source_28', step_02_direct_reads_firestore_s_counts_and_the_wo),
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
