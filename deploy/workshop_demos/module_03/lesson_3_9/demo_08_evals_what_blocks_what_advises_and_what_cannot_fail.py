"""Lesson 3.9: Evals: what blocks, what advises, and what cannot fail

Do it: the gate offline, and the rows that cannot fail

Run order inside this file:
1. Do it: the gate offline, and the rows that cannot fail (source window 47)

Prerequisites: demo_07_cost_at_10_the_limits_the_kit_declares_and_the_one_it_does_not.
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


# Original CLI workflow for step_01_the_gate_offline_and_the_rows_that_cannot.
COMMANDS_01 = """python evals/run_eval.py
python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["evals"]
from run_eval import THRESHOLDS, load_golden, load_required
golden, required = load_golden(), set(load_required())
print(f"what blocks a release: {len(THRESHOLDS)} thresholds and {len(required)} required rows over {len(golden)} rows, scored by code")
never = [r for r in golden if r.get("must_not_contain")]
print(f"must_not_contain on {len(never)} rows: " + ", ".join(f"{sum(r['shape'] == s for r in never)} {s}" for s in sorted({r['shape'] for r in never})))
for r in never:
    if r["shape"] != "isolation":
        print(f"  {r['id']} ({r['shape']}): {r['must_not_contain']} lives only in a revision under evals/demo; a version the ledger failed to retire can say it, so it can fail")
iso = [r for r in never if r["shape"] == "isolation"]
print(f"  the {len(iso)} isolation rows: the retriever filters by tenant before the generator reads, so they fail only on an invented figure")
print(f"  what replaced them: isolation_403_rate at {THRESHOLDS['isolation_403_rate']:.2f}, asked by an account on no tenant's roster")
PY

"""

def step_01_the_gate_offline_and_the_rows_that_cannot(session):
    """Run Do it: the gate offline, and the rows that cannot fail at this checkpoint.

    Do it: the gate offline, and the rows that cannot fail

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the offline gate, then a Python cell; Rs 0: no credential, no call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == eval gate: OFFLINE (no credentials, no cost) ==
      65 golden rows over 3 tenants, 27 documents

      [PASS] falsifiable
      [PASS] anchors
      [PASS] coverage

      The golden set is sound. It can go red, and it still contains the rows that would.
    what blocks a release: 9 thresholds and 15 required rows over 65 rows, scored by code
    must_not_contain on 12 rows: 11 isolation, 1 version
      vr-01 (version): ['90 days'] lives only in a revision under evals/demo; a version the ledger failed to retire can say it, so it can fail
      the 11 isolation rows: the retriever filters by tenant before the generator reads, so they fail only on an invented figure
      what replaced them: isolation_403_rate at 1.00, asked b
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_47', step_01_the_gate_offline_and_the_rows_that_cannot),
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
