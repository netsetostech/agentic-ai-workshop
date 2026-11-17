"""Lesson 2.5: The measurement: the rewrite arm against the lane, on the golden rows and the paraphrases

The wiring check takes the first five anchored rows, two arms and five calls, and shows the lines are where they should be before the longer runs spend anything.

Run order inside this file:
1. Do it: a wiring check, then the golden rows, then the paraphrases (source window 46)
2. Do it: a wiring check, then the golden rows, then the paraphrases (source window 48)
3. Do it: a wiring check, then the golden rows, then the paraphrases (source window 50)

Prerequisites: demo_06_the_stage_on_a_candidate_query_rewrite_on_a_forced_failure_and_the_undo.
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


# Original CLI workflow for step_01_a_wiring_check_then_the_golden_rows_then_t.
COMMANDS_01 = """make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite --limit 5"
# the same without make: python evals/ablate.py --project $PROJECT --region $REGION --arms dense20 --rewrite --limit 5

"""

def step_01_a_wiring_check_then_the_golden_rows_then_t(session):
    """Run Do it: a wiring check, then the golden rows, then the paraphrases at this checkpoint.

    The wiring check takes the first five anchored rows, two arms and five calls, and shows the lines are where they should be before the longer runs spend anything.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (five rows: a wiring check, about a minute).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ablate_wiring.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_wiring_check_then_the_golden_rows_then_t.
COMMANDS_02 = """make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite"

"""

def step_02_a_wiring_check_then_the_golden_rows_then_t(session):
    """Run Do it: a wiring check, then the golden rows, then the paraphrases at this checkpoint.

    The wiring check takes the first five anchored rows, two arms and five calls, and shows the lines are where they should be before the longer runs spend anything.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the 47 anchored golden rows, two arms).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ablate_golden.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_a_wiring_check_then_the_golden_rows_then_t.
COMMANDS_03 = """make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite --paraphrases evals/paraphrases.jsonl"

"""

def step_03_a_wiring_check_then_the_golden_rows_then_t(session):
    """Run Do it: a wiring check, then the golden rows, then the paraphrases at this checkpoint.

    The wiring check takes the first five anchored rows, two arms and five calls, and shows the lines are where they should be before the longer runs spend anything.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the same rows and the 24 paraphrases: 71 rows, two arms).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ablate_paraphrases.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_46', step_01_a_wiring_check_then_the_golden_rows_then_t),
        ('source_48', step_02_a_wiring_check_then_the_golden_rows_then_t),
        ('source_50', step_03_a_wiring_check_then_the_golden_rows_then_t),
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
