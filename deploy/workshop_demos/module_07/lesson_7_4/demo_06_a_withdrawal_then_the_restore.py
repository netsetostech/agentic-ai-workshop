"""Lesson 7.4: A withdrawal, then the restore

Do it Then the restore:

Run order inside this file:
1. Do it (source window 20)
2. Do it (source window 22)

Prerequisites: demo_05_a_new_version_then_the_undo.
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


# Original CLI workflow for step_01_a_withdrawal_then_the_restore.
COMMANDS_01 = """export SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
make retire PROJECT="$PROJECT" SOURCE=zeta/hr_policy_zeta_2026.md
fresh154 withdrawn

"""

def step_01_a_withdrawal_then_the_restore(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the handbook withdrawn by hand, then the check).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"event": "reconcile_withdrawn", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/zeta/hr_policy_zeta_2026.md", "fingerprint": "756528d4215dfc80", "retired_doc_keys": ["zeta_e920a147e36b71710f6ba542f63694634bb3755a581d443c2603d899f125256a"], "retired_ids": ["zeta:e920a147e36b71710f6ba542f63694634bb3755a581d443c2603d899f125256a#0", "...", "zeta:e920a147e36b71710f6ba542f63694634bb3755a581d443c2603d899f125256a#99"], "retired_chunks": 283, "note": "a tombstone: the object is kept and nothing automatic re-ingests it; make restore SOURCE= does"}
    the mirror's doc.mirror events for zeta since 2026-09-24T08:20:00Z (the audit bucket):
      08:20:24  delete:withdrawn  rag_engine    us-central1 zeta_e920a147..
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_withdrawal_then_the_restore.
COMMANDS_02 = """export SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
make restore PROJECT="$PROJECT" SOURCE=zeta/hr_policy_zeta_2026.md
fresh154 indexed

"""

def step_02_a_withdrawal_then_the_restore(session):
    """Run Do it at this checkpoint.

    Then the restore:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the handbook brought back, then the check).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"event": "reconcile_restored", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/zeta/hr_policy_zeta_2026.md", "generation": "1758000000021000", "next": "ingest_reactivated inside the undo window, ingest_ok (a fresh version) after it"}
    the mirror's doc.mirror events for zeta since 2026-09-24T08:30:00Z (the audit bucket):
      08:30:39  upsert            rag_engine    us-central1 zeta_e920a147...
      08:30:39  upsert            vertex_search global      zeta_e920a147...
    make managed-status TENANT_ONLY=zeta, until the stores match the ledger (the handbook indexed):
      0:00  handbook indexed; rag_engine in sync; vertex_search drift, missing zeta_e920a147...
      0:20  handbook indexed; rag_engine in sync; v
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_a_withdrawal_then_the_restore),
        ('source_22', step_02_a_withdrawal_then_the_restore),
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
