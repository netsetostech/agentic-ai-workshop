"""Lesson 4.5: The judge on the same rows: true-pass, false-pass and the cut

Do it: the judge against you, then against the author CUT=3 passes the second metric at 3 or more, and SWEEP=1 adds every cut from 1 to 5 under the two blocks, the current one marked. There is nothing to restore: a run without CUT is back at 4.

Run order inside this file:
1. Do it: the judge against you, then against the author (source window 32)
2. Change it: move the cut (source window 34)

Prerequisites: demo_04_two_people_on_the_same_rows_cohen_s_kappa.
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


# Original CLI workflow for step_01_the_judge_against_you_then_against_the_aut.
COMMANDS_01 = """if [ -f evals/judge_set.ratings.jsonl ]; then make judge-agree                                 # the judge against your sheet, cut at 4
else echo "waits for the author's judge_set.ratings.jsonl: not in your kit yet"; fi
if [ -f evals/judge_labels.L1.csv ] && [ -f evals/judge_set.ratings.jsonl ]; then make judge-agree LABELS=evals/judge_labels.L1.csv   # the judge against the author
else echo "waits for the author's judge_labels.L1.csv and judge_set.ratings.jsonl: not in your kit yet"; fi


"""

def step_01_the_judge_against_you_then_against_the_aut(session):
    """Run Do it: the judge against you, then against the author at this checkpoint.

    Do it: the judge against you, then against the author

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the judge's ratings of the same rows against one sheet).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/judge_set.json]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_change_it_move_the_cut.
COMMANDS_02 = """if [ -f evals/judge_set.ratings.jsonl ]; then make judge-agree CUT=3 SWEEP=1                   # your sheet: a looser cut, and every cut beside it
else echo "waits for the author's judge_set.ratings.jsonl: not in your kit yet"; fi
if [ -f evals/judge_labels.L1.csv ] && [ -f evals/judge_set.ratings.jsonl ]; then make judge-agree LABELS=evals/judge_labels.L1.csv CUT=3 SWEEP=1   # the author's
else echo "waits for the author's judge_labels.L1.csv and judge_set.ratings.jsonl: not in your kit yet"; fi


"""

def step_02_change_it_move_the_cut(session):
    """Run Change it: move the cut at this checkpoint.

    CUT=3 passes the second metric at 3 or more, and SWEEP=1 adds every cut from 1 to 5 under the two blocks, the current one marked. There is nothing to restore: a run without CUT is back at 4.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the Change-it; nothing to restore, because CUT is not a setting).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/judge_set.json]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_32', step_01_the_judge_against_you_then_against_the_aut),
        ('source_34', step_02_change_it_move_the_cut),
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
