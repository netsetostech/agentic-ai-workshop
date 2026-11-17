"""Lesson 4.5: Two people on the same rows: Cohen's kappa

Do it: the worked table, and the kit's own tests Do it: you against the author, then the author against the peer Until the author's sheet ships, kappa needs a second person. Make a colleague a sheet of the same rows under their own pseudonym. They label it blind, from the guide alone, without seeing yours. Then check their sheet and count your agreement with it. The author-against-peer line above waits for the recorded pair.

Run order inside this file:
1. Do it: the worked table, and the kit's own tests (source window 20)
2. Do it: you against the author, then the author against the peer (source window 22)
3. Do it, while the kit has no author's sheet: a colleague as your second reader (source window 24)
4. Do it, while the kit has no author's sheet: a colleague as your second reader (source window 25)

Prerequisites: demo_03_label_the_frozen_rows_yourself_blind.
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


# Original CLI workflow for step_01_the_worked_table_and_the_kit_s_own_tests.
COMMANDS_01 = """python evals/agreement.py --selftest
python -m unittest discover -s evals/tests -p test_agreement.py 2>&1 | tail -3

"""

def step_01_the_worked_table_and_the_kit_s_own_tests(session):
    """Run Do it: the worked table, and the kit's own tests at this checkpoint.

    Do it: the worked table, and the kit's own tests

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the worked table, then the kit's own tests of the arithmetic).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: selftest: the worked table of 50 rows (20 both yes, 5 and 10 split, 15 both no) agrees on 35/50 = 70.0% [56.2%, 80.9%], 0.50 by chance, kappa 0.40; identical labels 1.00; one label throughout undefined; a reader with one label against one with two 0.00
    Ran 18 tests in ...s

    OK
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_you_against_the_author_then_the_author_aga.
COMMANDS_02 = """if [ -f evals/judge_labels.L1.csv ]; then make judge-agree PEOPLE=1                       # your sheet against the author's
else echo "waits for the author's judge_labels.L1.csv: not in your kit yet"; fi
if [ -f evals/judge_labels.L1.csv ] && [ -f evals/judge_labels.L2.csv ]; then make judge-agree PEOPLE=1 LABELS=evals/judge_labels.L1.csv AGAINST=evals/judge_labels.L2.csv   # the author against the peer
else echo "waits for the author's judge_labels.L1.csv and judge_labels.L2.csv: not in your kit yet"; fi


"""

def step_02_you_against_the_author_then_the_author_aga(session):
    """Run Do it: you against the author, then the author against the peer at this checkpoint.

    Do it: you against the author, then the author against the peer

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: two sheets, kappa per rubric).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/judge_set.json]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_while_the_kit_has_no_author_s_sheet_a_coll.
COMMANDS_03 = """make label-sheet LABELS=evals/reports/judge_labels.peer.csv READER=peer

"""

def step_03_while_the_kit_has_no_author_s_sheet_a_coll(session):
    """Run Do it, while the kit has no author's sheet: a colleague as your second reader at this checkpoint.

    Until the author's sheet ships, kappa needs a second person. Make a colleague a sheet of the same rows under their own pseudonym. They label it blind, from the guide alone, without seeing yours. Then check their sheet and count your agreement with it. The author-against-peer line above waits for the recorded pair.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: only while the kit has no author's sheet; a blank sheet for your colleague).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_while_the_kit_has_no_author_s_sheet_a_coll.
COMMANDS_04 = """python evals/build_judge_set.py --check evals/reports/judge_labels.peer.csv
make judge-agree PEOPLE=1 AGAINST=evals/reports/judge_labels.peer.csv   # your sheet against your colleague's

"""

def step_04_while_the_kit_has_no_author_s_sheet_a_coll(session):
    """Run Do it, while the kit has no author's sheet: a colleague as your second reader at this checkpoint.

    Until the author's sheet ships, kappa needs a second person. Make a colleague a sheet of the same rows under their own pseudonym. They label it blind, from the guide alone, without seeing yours. Then check their sheet and count your agreement with it. The author-against-peer line above waits for the recorded pair.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: once your colleague has filled their sheet, blind).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    manual_checkpoint("Only while the kit has no author's sheet: your colleague fills evals/reports/judge_labels.peer.csv the same way, blind, from the guide alone and without seeing yours. Type done to check their sheet and count your agreement with it.")
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_the_worked_table_and_the_kit_s_own_tests),
        ('source_22', step_02_you_against_the_author_then_the_author_aga),
        ('source_24', step_03_while_the_kit_has_no_author_s_sheet_a_coll),
        ('source_25', step_04_while_the_kit_has_no_author_s_sheet_a_coll),
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
