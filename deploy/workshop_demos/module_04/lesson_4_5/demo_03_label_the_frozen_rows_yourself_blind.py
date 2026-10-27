"""Lesson 4.5: Label the frozen rows yourself, blind

While your kit has no evals/judge_set.json, freeze your own. make judge with --save-rows rates lesson 4.2's saved answers, evals/reports/judge72.json, and writes every rated row beside its question, context and answer. If that file is gone, --reuse collects the answers afresh, 65 questions to your API, about Rs 29.01. Each row gets two Evaluation requests either way. --freeze then picks 20 of the rated rows by the rules in step 8 and writes them to evals/reports/judge_set.json. Git ignores that folder, so the author's set can arrive later without a clash. The kit's targets read your set while the kit has none, and the author's once it ships. Skip the block if the first line says a set is there. Do it: your sheet Open evals/reports/judge_labels.csv in a spreadsheet or a text editor. For each row, read the context first, then the answer, then the question again, and write yes or no under both label columns. Write a note on any row you hesitate over, now: step 4 prints it beside the other reader's. Here is one filled row of the kit's fixture, as a sheet holds it: The answer refuses, so it claims nothing: grounded, yes. But the context holds the cap, so a refusal does not answer the question: no. The reader's note says why: "the cap is in the context". Save the sheet as CSV with every column kept and in the same order. A spreadsheet may add a byte-order mark, Windows line endings or a capitalised YES; the check reads all three. Then check it:

Run order inside this file:
1. Do it first: a frozen set, your own while the kit has none (source window 11)
2. Do it: your sheet (source window 12)
3. Do it: your sheet (source window 14)

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


# Original CLI workflow for step_01_first_a_frozen_set_your_own_while_the_kit.
COMMANDS_01 = """test -f evals/judge_set.json -o -f evals/reports/judge_set.json && echo "a frozen set is in your kit: skip this block" || {
make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" \\
  JUDGE_ARGS="--reuse evals/reports/judge72.json --save-rows evals/reports/judge45_rows.jsonl" &&
python evals/build_judge_set.py --freeze evals/reports/judge45_rows.jsonl --set evals/reports/judge_set.json
}

"""

def step_01_first_a_frozen_set_your_own_while_the_kit(session):
    """Run Do it first: a frozen set, your own while the kit has none at this checkpoint.

    While your kit has no evals/judge_set.json, freeze your own. make judge with --save-rows rates lesson 4.2's saved answers, evals/reports/judge72.json, and writes every rated row beside its question, context and answer. If that file is gone, --reuse collects the answers afresh, 65 questions to your API, about Rs 29.01. Each row gets two Evaluation requests either way. --freeze then picks 20 of the rated rows by the rules in step 8 and writes them to evals/reports/judge_set.json. Git ignores that folder, so the author's set can arrive later without a clash. The kit's targets read your set while the kit has none, and the author's once it ships. Skip the block if the first line says a set is there.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, in lesson 4.2's judge venv (only while there is no frozen set: 130 Evaluation requests over lesson 4.2's saved answers, or 65 fresh answers first if they are gone).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_your_sheet.
COMMANDS_02 = """make label-sheet

"""

def step_02_your_sheet(session):
    """Run Do it: your sheet at this checkpoint.

    Do it: your sheet

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: a blank sheet of the frozen rows for you; it never overwrites one).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/judge_set.json]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_your_sheet.
COMMANDS_03 = """python evals/build_judge_set.py --check evals/reports/judge_labels.csv
if [ -f evals/judge_labels.L1.csv ]; then python evals/build_judge_set.py --check evals/judge_labels.L1.csv      # the author's sheet, shipped with the kit
else echo "waits for the author's judge_labels.L1.csv: not in your kit yet"; fi


"""

def step_03_your_sheet(session):
    """Run Do it: your sheet at this checkpoint.

    Open evals/reports/judge_labels.csv in a spreadsheet or a text editor. For each row, read the context first, then the answer, then the question again, and write yes or no under both label columns. Write a note on any row you hesitate over, now: step 4 prints it beside the other reader's. Here is one filled row of the kit's fixture, as a sheet holds it: The answer refuses, so it claims nothing: grounded, yes. But the context holds the cap, so a refusal does not answer the question: no. The reader's note says why: "the cap is in the context". Save the sheet as CSV with every column kept and in the same order. A spreadsheet may add a byte-order mark, Windows line endings or a capitalised YES; the check reads all three. Then check it:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: holds a filled sheet to the frozen set).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/judge_set.json]
    """
    manual_checkpoint("Open evals/reports/judge_labels.csv in a spreadsheet or editor. For every row read the context, then the answer, then the question, and write yes or no under both groundedness and answers_the_question, blind: before reading any other reader's labels. Save it as CSV with every column kept. Type done to check it against the frozen set.")
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_first_a_frozen_set_your_own_while_the_kit),
        ('source_12', step_02_your_sheet),
        ('source_14', step_03_your_sheet),
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
