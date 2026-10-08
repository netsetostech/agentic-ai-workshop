"""Lesson 1.7: The three states side by side

Read the ledger as the operator does, Rs 0

Run order inside this file:
1. Read the ledger as the operator does, Rs 0 (source window 36)

Prerequisites: demo_06_withdrawn_retire_a_document_by_hand_then_restore_it.
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


# Original CLI workflow for step_01_read_the_ledger_as_the_operator_does_rs_0.
COMMANDS_01 = """make sources PROJECT=$PROJECT TENANT_ONLY=acme

"""

def step_01_read_the_ledger_as_the_operator_does_rs_0(session):
    """Run Read the ledger as the operator does, Rs 0 at this checkpoint.

    Read the ledger as the operator does, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: source                                       status            gen chunks reused embed retired effective  embedding              indexed_at
    acme/code_on_wages_2019.pdf                  indexed    ...2671234567     67      0    67       0 -          text-embedding-005@1   2026-09-20T09:14:02
    acme/hr_policy_2026.md                       indexed    ...4107123456    283    283     0     283 -          text-embedding-005@1   2026-09-22T13:41:55
    acme/smoke_note_v1.md                        indexed    ...5302345678      3      3     0       0 -          text-embedding-005@1   2026-09-22T15:21:40
    ...
    {"ledger": "acme", "fingerprint": "3a9f0c17e5d2b846", "versions": 9, "last_event": "ingest_reactivat
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_36', step_01_read_the_ledger_as_the_operator_does_rs_0),
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
