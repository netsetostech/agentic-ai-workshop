"""Lesson 4.5: Your lane's judge on the frozen rows: the ratings step 5 reads until the author's ship

Do it

Run order inside this file:
1. Do it (source window 38)

Prerequisites: demo_05_the_judge_on_the_same_rows_true_pass_false_pass_and_the_cut.
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


# Original CLI workflow for step_01_your_lane_s_judge_on_the_frozen_rows_the_r.
COMMANDS_01 = """make judge-frozen PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python"
make judge-agree RUN=evals/reports/judge_set.ratings.jsonl      # your lane's judge against your sheet

"""

def step_01_your_lane_s_judge_on_the_frozen_rows_the_r(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (while the kit has no author's ratings: 40 Vertex AI Evaluation requests, two a row; nothing asked of the API).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/judge_frozen.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_38', step_01_your_lane_s_judge_on_the_frozen_rows_the_r),
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
