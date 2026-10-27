"""Lesson 4.9: Ten rows in your own words, before any cause

Do it: the failing rows, as the gate saw them Do it: the sheet

Run order inside this file:
1. Do it: the failing rows, as the gate saw them (source window 19)
2. Do it: the sheet (source window 21)

Prerequisites: demo_03_two_reports_to_read_the_live_revision_and_a_candidate_that_fails_more.
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


# Original CLI workflow for step_01_the_failing_rows_as_the_gate_saw_them.
COMMANDS_01 = """make triage REPORT="evals/reports/live49.json evals/reports/cand49.json"

"""

def step_01_the_failing_rows_as_the_gate_saw_them(session):
    """Run Do it: the failing rows, as the gate saw them at this checkpoint.

    Do it: the failing rows, as the gate saw them

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the two reports; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/triage_rows.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_sheet.
COMMANDS_02 = """make triage REPORT="evals/reports/live49.json evals/reports/cand49.json" TEMPLATE=evals/reports/triage49.csv

"""

def step_02_the_sheet(session):
    """Run Do it: the sheet at this checkpoint.

    Do it: the sheet

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (writes the sheet; never over a file).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/triage.py evals/reports/live49.json evals/reports/cand49.json --template evals/reports/triage49.csv
      N failing rows of live49, cand49 written to evals/reports/triage49.csv: write a one-line note on ten of them, then read the causes (--classes) and fill the class column
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_the_failing_rows_as_the_gate_saw_them),
        ('source_21', step_02_the_sheet),
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
