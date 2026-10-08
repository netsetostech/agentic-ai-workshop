"""Lesson 1.8: Restore the exact bytes and prove reuse

A new upload generation, the same content hash, and the worker's verified reactivation. The checksum must still match. Changing the memo, adding today's date, or replacing it with a base smoke fixture creates different bytes and does not demonstrate the same-version undo. Keep the same object name too.

Run order inside this file:
1. Restore the exact bytes and prove reuse (source window 21)
2. Restore the exact bytes and prove reuse (source window 22)

Prerequisites: demo_07_plan_retirement_apply_it_then_prove_zero_drift.
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


# Original CLI workflow for step_01_restore_the_exact_bytes_and_prove_reuse.
COMMANDS_01 = """ch44_upload &&
python - <<'PY'
import json, os
from pathlib import Path
d=Path(os.environ["DEMO_DIR"])
r=json.loads((d/"source.json").read_text())
n=int((d/"initial-chunks.txt").read_text())
assert r["status"]=="indexed" and r["doc_key"]==os.environ["DOC_KEY"]
assert str(r["generation"])==os.environ["CH44_GENERATION"]
assert r["chunks"]==n and r["reused"]==n and r["embedded"]==0, \\
    "This was not a complete reuse. Inspect this version's worker events."
print("Restored:", n, "chunks reused; 0 embedded")
PY

"""

def step_01_restore_the_exact_bytes_and_prove_reuse(session):
    """Run Restore the exact bytes and prove reuse at this checkpoint.

    A new upload generation, the same content hash, and the worker's verified reactivation. The checksum must still match. Changing the memo, adding today's date, or replacing it with a base smoke fixture creates different bytes and does not demonstrate the same-version undo. Keep the same object name too.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — upload only if the original checksum still passes; wait for the new generation.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_restore_the_exact_bytes_and_prove_reuse.
COMMANDS_02 = """ch44_logs
ch44_ask present
ch44_plan clean

"""

def step_02_restore_the_exact_bytes_and_prove_reuse(session):
    """Run Restore the exact bytes and prove reuse at this checkpoint.

    A new upload generation, the same content hash, and the worker's verified reactivation. The checksum must still match. Changing the memo, adding today's date, or replacing it with a base smoke fixture creates different bytes and does not demonstrate the same-version undo. Keep the same object name too.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — show this upload's event, restored citation and clean plan.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_restore_the_exact_bytes_and_prove_reuse),
        ('source_22', step_02_restore_the_exact_bytes_and_prove_reuse),
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
