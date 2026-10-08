"""Lesson 1.6: The gate goes red, and the two ways back to green

Ten questions to the API, each a generation call: a few rupees at most. The target mints two identity tokens, the UI's account as the member and the outsider's for the isolation rows, which is why it takes a moment to start. Version 1's bytes again, through the same release command. The offline gate passes, the upload lands, and the worker finds a version it has retired within the window: ingest_reactivated, nothing embedded, revision 3 retired in turn. The live gate then passes with the rows as they are.

Run order inside this file:
1. Do it: the live gate, red (source window 21)
2. The undo, then the gate, green (source window 23)

Prerequisites: demo_06_inspect_the_ledger_row_the_claims_the_vectors.
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


def step_01_the_live_gate_red(session):
    """Run Do it: the live gate, red at this checkpoint.

    Ten questions to the API, each a generation call: a few rupees at most. The target mints two identity tokens, the UI's account as the member and the outsider's for the isolation rows, which is why it takes a moment to start.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (ten questions; a few rupees).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://documind-api-NUMBER.asia-south1.run.app
    == eval gate: LIVE ==
      scoped to hr_policy_2026.md: 10 row(s) cite it
      10 rows (10 answerable, 0 not) against https://documind-api-NUMBER.asia-south1.run.app

      [PASS] request_success_rate  100.0%  (threshold 100%; 10 rows)
      [PASS] answerable_rate       100.0%  (threshold 80%; 10 rows)
      [PASS] citation_rate         100.0%  (threshold 95%; 10 rows)
      [PASS] citation_valid_rate   100.0%  (threshold 100%; 10 rows)
      [FAIL] must_contain_rate      80.0%  (threshold 85%; 10 rows)
      [PASS] correct_rate           80.0%  (threshold 68%; 10 rows)
      [ -- ] refusal_rate            0.0%  (threshold 90%; no rows in scope; 0 rows)
      ...

      shape       
    """
    from workshop_helpers.gates import live_gate
    live_gate(session, report=session.directory / "lesson42-red-gate.json", source="hr_policy_2026.md", expect_red=True)

# Original CLI workflow for step_02_the_undo_then_the_gate_green.
COMMANDS_02 = """make reindex PROJECT=$PROJECT TENANT=acme FILE=evals/corpus/acme/hr_policy_2026.md

make eval-live PROJECT=$PROJECT SOURCE=hr_policy_2026.md

"""

def step_02_the_undo_then_the_gate_green(session):
    """Run The undo, then the gate, green at this checkpoint.

    Version 1's bytes again, through the same release command. The offline gate passes, the upload lands, and the worker finds a version it has retired within the window: ingest_reactivated, nothing embedded, revision 3 retired in turn. The live gate then passes with the rows as they are.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the undo, then ten questions again).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)
    >> event doc_key chunks reused embedded retired effective_from
    >> ingest_reactivated	acme_497809ffbaa603c4...	283	283	0	283
    >> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_2026.md API=<candidate url>
    ...
      [PASS] must_contain_rate     100.0%  (threshold 85%; 10 rows)
      ...
      shape        rows   ok   pass
      lookup          9    9      9
      version         1    1      1
      All thresholds met.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_the_live_gate_red),
        ('source_23', step_02_the_undo_then_the_gate_green),
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
