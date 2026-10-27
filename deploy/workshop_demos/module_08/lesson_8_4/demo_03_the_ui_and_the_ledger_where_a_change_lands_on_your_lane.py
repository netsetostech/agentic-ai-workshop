"""Lesson 8.4: The UI and the ledger: where a change lands on your lane

The Documents page as yourself, the same ledger through the API as the UI's account, then the three records the caches compare. A change ends in the ledger, so read the ledger first, where an operator would. The UI's address is built from your project number, as the setup block built API: Open it signed in to Google as yourself and choose Documents. The Versions table is the ledger: one row per source, with its status, its chunks, what its last change cost (reused, embedded, retired), the embedding it was made with, when it landed and where it is held. The caption above it prints the count of current versions, the corpus fingerprint, the last change and the tenant's data_region. Your email maps to acme, so these are acme's rows. The same rows come from the API. GET /v1/sources is the versions view main.py serves. The shell calls it as documind-ui-sa, the UI's own account, which make roster put on all three tenants, so the call could name any of them. The UI asked as you, and only acme was yours. One ledger, two callers: The same rows come from the API. GET /v1/sources is the versions view main.py serves. The shell calls it as documind-ui-sa, the UI's own account, which make roster put on all three tenants, so the call could name any of them. The UI asked as you, and only acme was yours. One ledger, two callers: any is acme's data_region, set by make roster, and it is why the managed stores hold acme's copies. The handbook row's last three counts are what its last change cost: an undo shows 283 reused and 0 embedded, and a re-issue like revision 2 shows 281 and 2. Then the three records that decide whether a cache may be used. Firestore holds them, and the cell reads each one directly:

Run order inside this file:
1. The UI and the ledger: where a change lands on your lane (source window 6)
2. The UI and the ledger: where a change lands on your lane (source window 8)
3. The UI and the ledger: where a change lands on your lane (source window 10)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_the_ui_and_the_ledger_where_a_change_lands.
COMMANDS_01 = """echo "https://documind-ui-$NUMBER.$REGION.run.app"

"""

def step_01_the_ui_and_the_ledger_where_a_change_lands(session):
    """Run The UI and the ledger: where a change lands on your lane at this checkpoint.

    The Documents page as yourself, the same ledger through the API as the UI's account, then the three records the caches compare. A change ends in the ledger, so read the ledger first, where an operator would. The UI's address is built from your project number, as the setup block built API:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (prints your UI's address).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: https://documind-ui-NUMBER.asia-south1.run.app
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_ui_and_the_ledger_where_a_change_lands.
COMMANDS_02 = """curl -s "$API/v1/sources?tenant_id=acme" -H "Authorization: Bearer $(tok "$API")" \\
  | python -c 'import json, sys; d = json.load(sys.stdin); print("acme:", d["data_region"], "|", d["versions"], "current versions | fingerprint", d["fingerprint"], "| last", d["last_event"]); [print(" ", s["name"], s["status"], s["chunks"], "chunks, reused", s["reused"], "embedded", s["embedded"], "retired", s["retired"], s["embedding"]) for s in d["sources"] if s["name"].endswith("hr_policy_2026.md")]'

"""

def step_02_the_ui_and_the_ledger_where_a_change_lands(session):
    """Run The UI and the ledger: where a change lands on your lane at this checkpoint.

    Open it signed in to Google as yourself and choose Documents. The Versions table is the ledger: one row per source, with its status, its chunks, what its last change cost (reused, embedded, retired), the embedding it was made with, when it landed and where it is held. The caption above it prints the count of current versions, the corpus fingerprint, the last change and the tenant's data_region. Your email maps to acme, so these are acme's rows. The same rows come from the API. GET /v1/sources is the versions view main.py serves. The shell calls it as documind-ui-sa, the UI's own account, which make roster put on all three tenants, so the call could name any of them. The UI asked as you, and only acme was yours. One ledger, two callers:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one GET as the UI's account; reads the ledger, writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme: any | NUMBER current versions | fingerprint ... | last ingest_...
      acme/hr_policy_2026.md indexed 283 chunks, reused N embedded N retired N text-embedding-005@1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def step_03_the_ui_and_the_ledger_where_a_change_lands(session):
    """Run The UI and the ledger: where a change lands on your lane at this checkpoint.

    The same rows come from the API. GET /v1/sources is the versions view main.py serves. The shell calls it as documind-ui-sa, the UI's own account, which make roster put on all three tenants, so the call could name any of them. The UI asked as you, and only acme was yours. One ledger, two callers: any is acme's data_region, set by make roster, and it is why the managed stores hold acme's copies. The handbook row's last three counts are what its last change cost: an undo shows 283 reused and 0 embedded, and a re-issue like revision 2 shows 281 and 2. Then the three records that decide whether a cache may be used. Firestore holds them, and the cell reads each one directly:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (three Firestore reads; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ledger/acme: fingerprint ..., NUMBER versions, last event ...
    tenant_caches/acme: none  (or: packed under ...: current | STALE)
    answer_cache, acme: N entries, N under the current fingerprint
    """
    import os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    db = firestore.Client(project=os.environ["PROJECT"])
    led = (db.document("ledger/acme").get().to_dict() or {})
    print(f"ledger/acme: fingerprint {led.get('fingerprint')}, {led.get('versions')} versions, last event {led.get('last_event')}")
    cache = db.document("tenant_caches/acme").get()
    packed = (cache.to_dict() or {}).get("corpus_fingerprint") if cache.exists else None
    print("tenant_caches/acme: " + ("none" if not cache.exists else f"packed under {packed}: "
                                    + ("current" if packed == led.get("fingerprint") else "STALE")))
    fps = [s.to_dict().get("fingerprint") for s in db.collection("answer_cache").where("tenant_id", "==", "acme").select(["fingerprint"]).stream()]
    print(f"answer_cache, acme: {len(fps)} entries, {sum(f == led.get('fingerprint') for f in fps)} under the current fingerprint")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_the_ui_and_the_ledger_where_a_change_lands),
        ('source_8', step_02_the_ui_and_the_ledger_where_a_change_lands),
        ('source_10', step_03_the_ui_and_the_ledger_where_a_change_lands),
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
