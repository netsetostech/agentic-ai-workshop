"""Lesson 4.4: The pairwise judge: which answer is better, row by row

Do it

Run order inside this file:
1. Do it (source window 21)

Prerequisites: demo_04_the_scoped_gate_on_both_revisions_and_the_rows_that_moved.
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


# Original CLI workflow for step_01_the_pairwise_judge_which_answer_is_better.
COMMANDS_01 = """make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" API_B="$CAND" JUDGE_ARGS="--rows 20"

"""

def step_01_the_pairwise_judge_which_answer_is_better(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (twenty rows on each revision, then the Evaluation service).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://documind-api-NUMBER.asia-south1.run.app
      20/20 answers collected from https://documind-api-NUMBER.asia-south1.run.app in ...s (model gemini-3.6-flash)
      20/20 candidate answers from https://candidate---documind-api-NUMBER.asia-south1.run.app
      context: .../... cited chunks read in full from the store
      trajectories: off (no --chat-url)
      pointwise: GROUNDEDNESS + INSTRUCTION_FOLLOWING  (templates cd7070; run api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070)
      judge: the service default (pass --judge-model to pin one)

      Experiments run documind-eval/api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070:
        groundedness/mean                                ...
        groundedness/mean[join]    
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_the_pairwise_judge_which_answer_is_better),
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
