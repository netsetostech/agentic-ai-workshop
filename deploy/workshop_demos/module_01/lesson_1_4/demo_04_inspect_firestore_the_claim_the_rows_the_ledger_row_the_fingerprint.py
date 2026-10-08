"""Lesson 1.4: Inspect Firestore: the claim, the rows, the ledger row, the fingerprint

Read all four, Rs 0

Run order inside this file:
1. Read all four, Rs 0 (source window 20)

Prerequisites: demo_03_write_the_order_the_worker_keeps_and_a_fresh_document_to_watch.
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


def step_01_read_all_four_rs_0(session):
    """Run Read all four, Rs 0 at this checkpoint.

    Read all four, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: doc_key from the note's bytes: acme_9c41d0e2b7f5a1...
    documents/: {'status': 'indexed', 'chunks': 3, 'reused': 0, 'embedded': 3, 'generation': '1758542671234567', 'tenant_id': 'acme'}
    chunks/: 3 rows | current: 3 | staged: 0 | with expire_at: 0
      acme:9c41d0e2b7f5...#0  preamble  section=None hash=70501fc5957f vector=768 doc_type=unknown
      acme:9c41d0e2b7f5...#1  SM-01     section='SM-01 - The smoke lantern' hash=14adcf0a776b vector=768 doc_type=unknown
      acme:9c41d0e2b7f5...#2  SM-02     section='SM-02 - The ladder' hash=(yours) vector=768 doc_type=unknown
    sources/acme~smoke_note_v1.md: {'status': 'indexed', 'chunks': 3, 'reused': 0, 'embedded': 3, 'retired': 0, 'effective_from': None} | do
    """
    import os, hashlib, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    PROJECT = os.environ["PROJECT"]
    db = firestore.Client(project=PROJECT)
    NOTE = os.environ.get("NOTE", os.path.expanduser("~/lesson34_note.md"))    # the note you wrote in step 3
    sha = hashlib.sha256(open(NOTE, "rb").read()).hexdigest()
    key = f"acme_{sha}"
    print("doc_key from the note's bytes:", key[:20] + "...")
    claim = db.collection("documents").document(key).get().to_dict() or {}
    print("documents/:", {k: claim.get(k) for k in ("status", "chunks", "reused", "embedded", "generation", "tenant_id")})
    rows = sorted(((s.id, s.to_dict()) for s in db.collection("chunks").where("tenant_id", "==", "acme").where("doc_key", "==", key).stream()),
                  key=lambda r: int(r[0].rsplit("#", 1)[1]))
    print("chunks/:", len(rows), "rows | current:", sum(d.get("current") is True for _, d in rows),
          "| staged:", sum(bool(d.get("staged")) for _, d in rows), "| with expire_at:", sum(d.get("expire_at") is not None for _, d in rows))
    for cid, d in rows:
        print(f"  {cid.split('#')[0][:18]}...#{cid.rsplit('#', 1)[1]}  {d['locator']:9} section={d.get('section')!r} hash={d['chunk_hash'][:12]} vector={len(d['embedding'])} doc_type={d.get('doc_type')}")
    src = db.collection("sources").document("acme~smoke_note_v1.md").get().to_dict() or {}
    print("sources/acme~smoke_note_v1.md:", {k: src.get(k) for k in ("status", "chunks", "reused", "embedded", "retired", "effective_from")},
          "| doc_key matches:", src.get("doc_key") == key, "| sha256 matches:", src.get("sha256") == sha)
    led = db.collection("ledger").document("acme").get().to_dict() or {}
    print("ledger/acme:", {k: led.get(k) for k in ("fingerprint", "versions", "last_event")})

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_read_all_four_rs_0),
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
