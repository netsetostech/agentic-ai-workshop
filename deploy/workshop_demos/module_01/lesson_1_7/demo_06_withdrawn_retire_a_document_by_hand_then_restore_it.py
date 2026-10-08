"""Lesson 1.7: Withdrawn: retire a document by hand, then restore it

The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

Run order inside this file:
1. Do it: withdraw the note, test the tombstone, restore it (source window 25)
2. Do it: withdraw the note, test the tombstone, restore it (source window 29)
3. Do it: withdraw the note, test the tombstone, restore it (source window 31)
4. Do it: withdraw the note, test the tombstone, restore it (source window 33)

Prerequisites: demo_05_stale_the_generation_guard_and_three_replayed_events.
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


# Original CLI workflow for step_01_withdraw_the_note_test_the_tombstone_resto.
COMMANDS_01 = """gcloud storage cp "gs://$PROJECT-uploads/acme/smoke_note_v1.md" "$HOME/lesson34_note.md" 2>/dev/null \\
  || { GEN="$(gcloud storage ls -a "gs://$PROJECT-uploads/acme/smoke_note_v1.md" | sed -n 's/.*#//p' | sort -n | tail -1)"; \\
       gcloud storage cp "gs://$PROJECT-uploads/acme/smoke_note_v1.md#$GEN" "$HOME/lesson34_note.md"; }
python - <<'PY'
import os, hashlib, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
db = firestore.Client(project=os.environ["PROJECT"])
want = (db.collection("sources").document("acme~smoke_note_v1.md").get().to_dict() or {}).get("sha256")
have = hashlib.sha256(open(os.path.expanduser("~/lesson34_note.md"), "rb").read()).hexdigest() if os.path.exists(os.path.expanduser("~/lesson34_note.md")) else "no file"
print("ledger", (want or "no ledger row: run lesson 1.4 step 3 first")[:16], "| file", have[:16], "|", "the same bytes" if want == have else "DIFFERENT: run the rebuild block")
PY

"""

def step_01_withdraw_the_note_test_the_tombstone_resto(session):
    """Run Do it: withdraw the note, test the tombstone, restore it at this checkpoint.

    The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the object, or its last generation; then the hash against the ledger).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ledger abcdef0123456789 | file abcdef0123456789 | the same bytes
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_withdraw_the_note_test_the_tombstone_resto.
COMMANDS_02 = """make retire PROJECT=$PROJECT SOURCE=acme/smoke_note_v1.md

curl -s "$API/v1/sources?tenant_id=acme" -H "Authorization: Bearer $(tok "$API")" \\
  | python -c "import json,sys; j=json.load(sys.stdin); [print(r['name'], r['status'], 'chunks', r['chunks']) for r in j['sources'] if 'smoke_note' in r['name']]; print('fingerprint', j['fingerprint'], '| last event', j['last_event'])"

python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
PROJECT = os.environ["PROJECT"]
db = firestore.Client(project=PROJECT)
rows = [r.to_dict() for r in db.collection("chunks").where("tenant_id", "==", "acme").where("source_uri", "==", f"gs://{PROJECT}-uploads/acme/smoke_note_v1.md").stream()]
print(len(rows), "rows | current:", sum(bool(r.get("current")) for r in rows), "| with expire_at:", sum(r.get("expire_at") is not None for r in rows), "| superseded_by:", {str(r.get("superseded_by")) for r in rows})
PY

"""

def step_02_withdraw_the_note_test_the_tombstone_resto(session):
    """Run Do it: withdraw the note, test the tombstone, restore it at this checkpoint.

    The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the withdrawal, then two reads).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"event": "reconcile_withdrawn", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/smoke_note_v1.md", "fingerprint": "7c2e91a4d05b3f68", "retired_doc_keys": ["acme_9c41d0e2b7f5..."], "retired_ids": ["acme:9c41d0e2b7f5...#0", "acme:9c41d0e2b7f5...#1", "acme:9c41d0e2b7f5...#2"], "retired_chunks": 3, "note": "a tombstone: the object is kept and nothing automatic re-ingests it; make restore SOURCE= does"}
    acme/smoke_note_v1.md withdrawn chunks 3
    fingerprint 7c2e91a4d05b3f68 | last event reconcile_withdrawn
    3 rows | current: 0 | with expire_at: 3 | superseded_by: {'None'}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_withdraw_the_note_test_the_tombstone_resto.
COMMANDS_03 = """curl -s -X POST $API/v1/query -H "Authorization: Bearer $(tok $API)" -H "Content-Type: application/json" \\
  -d '{"query":"Where is the smoke lantern kept?","tenant_id":"acme","stream":false}' \\
  | python -c "import json,sys; j=json.load(sys.stdin); print('answerable', j['answerable'], '| citations', len(j['citations']), '|', j['answer'][:90])"

"""

def step_03_withdraw_the_note_test_the_tombstone_resto(session):
    """Run Do it: withdraw the note, test the tombstone, restore it at this checkpoint.

    The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one question; paise).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: answerable False | citations 0 | The corpus holds nothing near this question: no passage of this tenant's current documents
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_withdraw_the_note_test_the_tombstone_resto.
COMMANDS_04 = """SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
gcloud storage cp "$HOME/lesson34_note.md" "gs://$PROJECT-uploads/acme/smoke_note_v1.md"
sleep 25
gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND jsonPayload.event=\\"ingest_withdrawn\\" AND timestamp>=\\"$SINCE\\"" \\
  --project "$PROJECT" --limit 1 --format='value(jsonPayload.event,jsonPayload.doc_key,jsonPayload.hint)'

SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
make restore PROJECT=$PROJECT SOURCE=acme/smoke_note_v1.md
for i in $(seq 1 30); do sleep 10
  LINE="$(gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND (jsonPayload.event=\\"ingest_reactivated\\" OR jsonPayload.event=\\"ingest_ok\\") AND jsonPayload.tenant=\\"acme\\" AND timestamp>=\\"$SINCE\\"" \\
    --project "$PROJECT" --limit 1 --format='value(jsonPayload.event,jsonPayload.chunks,jsonPayload.reused,jsonPayload.embedded)')"
  [ -n "$LINE" ] && { echo ">> event chunks reused embedded: $LINE"; break; }
done
curl -s "$API/v1/sources?tenant_id=acme" -H "Authorization: Bearer $(tok "$API")" \\
  | python -c "import json,sys; [print(r['name'], r['status'], 'reused', r['reused'], 'embedded', r['embedded']) for r in json.load(sys.stdin)['sources'] if 'smoke_note' in r['name']]"
curl -s -X POST $API/v1/query -H "Authorization: Bearer $(tok $API)" -H "Content-Type: application/json" \\
  -d '{"query":"Where is the smoke lantern kept?","tenant_id":"acme","stream":false}' \\
  | python -c "import json,sys; j=json.load(sys.stdin); print('answerable', j['answerable'], '|', j['answer'][:90])"

"""

def step_04_withdraw_the_note_test_the_tombstone_resto(session):
    """Run Do it: withdraw the note, test the tombstone, restore it at this checkpoint.

    The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the same bytes again: refused; then the restore).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ingest_withdrawn	acme_9c41d0e2b7f5...	make restore SOURCE= clears the tombstone
    {"event": "reconcile_restored", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/smoke_note_v1.md", "generation": "1758555302345678", "next": "ingest_reactivated inside the undo window, ingest_ok (a fresh version) after it"}
    >> event chunks reused embedded: ingest_reactivated	3	3	0
    acme/smoke_note_v1.md indexed reused 3 embedded 0
    answerable True | The smoke lantern is kept in bay 4 of the Pune warehouse ... [Source 1]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_withdraw_the_note_test_the_tombstone_resto),
        ('source_29', step_02_withdraw_the_note_test_the_tombstone_resto),
        ('source_31', step_03_withdraw_the_note_test_the_tombstone_resto),
        ('source_33', step_04_withdraw_the_note_test_the_tombstone_resto),
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
