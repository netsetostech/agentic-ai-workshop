"""Lesson 0.2: Diagnose a first failure: one loosened row

The most common way an eval suite rots, made on purpose, caught, read and repaired. Picture a red live run on lk-06 the night before a release. The fastest way to green is to loosen the row: empty its must_contain, and any answer at all passes. That edit is the commonest way an eval suite rots, because the row stays in the file looking like a test. The offline gate exists to refuse it. Make the edit in your clone: Picture a red live run on lk-06 the night before a release. The fastest way to green is to loosen the row: empty its must_contain, and any answer at all passes. That edit is the commonest way an eval suite rots, because the row stays in the file looking like a test. The offline gate exists to refuse it. Make the edit in your clone: Git sees it. This is what the clone is for: every change you make to the kit is visible, and reversible, against the commit you pulled. Git sees it. This is what the clone is for: every change you make to the kit is visible, and reversible, against the commit you pulled. One line changed: the row's must_contain went from ["60"] to []. Now run the gate. Repair it

Run order inside this file:
1. Diagnose a first failure: one loosened row (source window 29)
2. Diagnose a first failure: one loosened row (source window 31)
3. Diagnose a first failure: one loosened row (source window 33)
4. Repair it (source window 36)

Prerequisites: demo_05_prove_a_first_success_make_dryrun.
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


# Original CLI workflow for step_01_diagnose_a_first_failure_one_loosened_row.
COMMANDS_01 = """cd "$DEMO_ROOT" && python - <<'PY'
import json, warnings; warnings.filterwarnings("ignore", category=UserWarning)
path = "evals/golden.jsonl"
lines = open(path, encoding="utf-8").read().split("\\n")
for i, line in enumerate(lines):
    if line.strip() and json.loads(line)["id"] == "lk-06":   # the notice-period row the lane answered
        row = json.loads(line)
        print("lk-06 must_contain before:", row["must_contain"])
        row["must_contain"] = []                              # loosened: any answer at all would now pass
        lines[i] = json.dumps(row, ensure_ascii=False)
        print("lk-06 must_contain after: ", row["must_contain"])
open(path, "w", encoding="utf-8", newline="\\n").write("\\n".join(lines))
PY

"""

def step_01_diagnose_a_first_failure_one_loosened_row(session):
    """Run Diagnose a first failure: one loosened row at this checkpoint.

    The most common way an eval suite rots, made on purpose, caught, read and repaired. Picture a red live run on lk-06 the night before a release. The fastest way to green is to loosen the row: empty its must_contain, and any answer at all passes. That edit is the commonest way an eval suite rots, because the row stays in the file looking like a test. The offline gate exists to refuse it. Make the edit in your clone:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the first terminal: loosen lk-06 in your clone (or delete the 60 by hand in an editor).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lk-06 must_contain before: ['60']
    lk-06 must_contain after:  []
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_diagnose_a_first_failure_one_loosened_row.
COMMANDS_02 = """git -C "$DEMO_ROOT" diff -U0          # what changed in your clone, with no context lines

"""

def step_02_diagnose_a_first_failure_one_loosened_row(session):
    """Run Diagnose a first failure: one loosened row at this checkpoint.

    Picture a red live run on lk-06 the night before a release. The fastest way to green is to loosen the row: empty its must_contain, and any answer at all passes. That edit is the commonest way an eval suite rots, because the row stays in the file looking like a test. The offline gate exists to refuse it. Make the edit in your clone: Git sees it. This is what the clone is for: every change you make to the kit is visible, and reversible, against the commit you pulled.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the first terminal.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: diff --git a/evals/golden.jsonl b/evals/golden.jsonl
    index 50b46d6..e2d97fb 100644
    --- a/evals/golden.jsonl
    +++ b/evals/golden.jsonl
    @@ -6 +6 @@
    -{"id": "lk-06", "shape": "lookup", "question": "What is the notice period for a confirmed E3?", "tenant": "acme", "must_contain": ["60"], "must_retrieve": ["NP-03", "hr_policy_2026"], "answerable": true}
    +{"id": "lk-06", "shape": "lookup", "question": "What is the notice period for a confirmed E3?", "tenant": "acme", "must_contain": [], "must_retrieve": ["NP-03", "hr_policy_2026"], "answerable": true}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_diagnose_a_first_failure_one_loosened_row.
COMMANDS_03 = """cd "$DEMO_ROOT" && make dryrun

"""

def step_03_diagnose_a_first_failure_one_loosened_row(session):
    """Run Diagnose a first failure: one loosened row at this checkpoint.

    Git sees it. This is what the clone is for: every change you make to the kit is visible, and reversible, against the commit you pulled. One line changed: the row's must_contain went from ["60"] to []. Now run the gate.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the first terminal.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: kit-only checkout: no curriculum notebooks under Module */ - nothing to extract or check; deploy/ here IS the extracted tree

      DocuMind AI — Tier-A offline dry run
      ------------------------------------------------------------
      [SKIP] extract       kit-only checkout (the learner repo): deploy/ is the extracted tree, nothing to compare  (Ns)
      [PASS] py_compile    125 python files parse  (Ns)
      [PASS] imports       all local imports resolve  (Ns)
      [PASS] shared-deps   every google.cloud client a shared module opens is pinned by its importers  (Ns)
      [PASS] requirements  11 files, all deps pinned  (Ns)
      [PASS] pins          30 shared packages agree across 12 files  (Ns)
      [PASS] dockerfile
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_repair_it.
COMMANDS_04 = """git -C "$DEMO_ROOT" checkout -- evals/golden.jsonl     # the committed row comes back
git -C "$DEMO_ROOT" diff --stat                         # prints nothing: the clone is clean again
cd "$DEMO_ROOT" && make dryrun

"""

def step_04_repair_it(session):
    """Run Repair it at this checkpoint.

    Repair it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the first terminal: repair, check, run again.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == eval gate: OFFLINE (no credentials, no cost) ==
      65 golden rows over 3 tenants, 27 documents

      [PASS] falsifiable
      [PASS] anchors
      [PASS] coverage

      The golden set is sound. It can go red, and it still contains the rows that would.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_29', step_01_diagnose_a_first_failure_one_loosened_row),
        ('source_31', step_02_diagnose_a_first_failure_one_loosened_row),
        ('source_33', step_03_diagnose_a_first_failure_one_loosened_row),
        ('source_36', step_04_repair_it),
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
