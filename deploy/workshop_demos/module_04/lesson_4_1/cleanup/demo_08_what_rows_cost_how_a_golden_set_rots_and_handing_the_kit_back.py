"""Lesson 4.1: What rows cost, how a golden set rots, and handing the kit back

At lesson end: Your clone now differs from the kit in four files. Lesson 4.2 runs the kit's own set, 65 rows and 15 required ids. The setup block's git pull --ff-only also refuses to run over local edits to a file the kit has changed. So keep your rows as a patch and restore the four files. git -C "$DEMO_ROOT" apply "$HOME/lesson71_rows.patch" brings them back whenever you want them.

Run order inside this file:
1. Keep your rows, and give the kit its files back (source window 44)

Prerequisites: workshop setup; see this lesson README.
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


def step_01_keep_your_rows_and_give_the_kit_its_files(session):
    """Run Keep your rows, and give the kit its files back at this checkpoint.

    Your clone now differs from the kit in four files. Lesson 4.2 runs the kit's own set, 65 rows and 15 required ids. The setup block's git pull --ff-only also refuses to run over local edits to a file the kit has changed. So keep your rows as a patch and restore the four files. git -C "$DEMO_ROOT" apply "$HOME/lesson71_rows.patch" brings them back whenever you want them.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (your rows kept as a patch, the four files given back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: evals/build_golden.py   | 2 ++
     evals/golden.jsonl      | 2 ++
     evals/paraphrases.jsonl | 2 ++
     evals/required.json     | 1 +
     4 files changed, 7 insertions(+)
    the four files match the kit again
    65
    7
    """
    from workshop_helpers.steps import restore_files
    restore_files(session)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_44', step_01_keep_your_rows_and_give_the_kit_its_files),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=True, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
