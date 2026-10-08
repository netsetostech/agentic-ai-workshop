"""Lesson 1.6: The gate: the golden set, scoped to one document

Do it: the offline gate, scoped to the handbook, Rs 0

Run order inside this file:
1. Do it: the offline gate, scoped to the handbook, Rs 0 (source window 9)

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


# Original CLI workflow for step_01_the_offline_gate_scoped_to_the_handbook_rs.
COMMANDS_01 = """python evals/run_eval.py --source hr_policy_2026.md

"""

def step_01_the_offline_gate_scoped_to_the_handbook_rs(session):
    """Run Do it: the offline gate, scoped to the handbook, Rs 0 at this checkpoint.

    Do it: the offline gate, scoped to the handbook, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (no credentials, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == eval gate: OFFLINE (no credentials, no cost) ==
      65 golden rows over 3 tenants, 27 documents

      [PASS] falsifiable
      [PASS] anchors
      [PASS] coverage

      The golden set is sound. It can go red, and it still contains the rows that would.

      rows citing hr_policy_2026.md: 10 - the scoped live gate judges these
        lk-01  lookup    What is the per-trip cap on domestic travel reimbursement?
        lk-02  lookup    By when is Form 16 issued?
        lk-03  lookup    How many days of earned leave can I carry forward?
        lk-04  lookup    What notice period applies during probation?
        lk-05  lookup    Are USB drives allowed on a company laptop?
        lk-06  lookup    What is the notice period for a con
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_offline_gate_scoped_to_the_handbook_rs),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
