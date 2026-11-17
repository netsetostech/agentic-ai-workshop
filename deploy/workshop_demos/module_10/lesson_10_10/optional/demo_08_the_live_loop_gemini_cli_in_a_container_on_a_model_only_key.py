"""Lesson 10.10: The live loop: Gemini CLI in a container, on a model-only key

Optional, the author's run: the live loop on a model-only Gemini API key the author creates for the run and deletes after it, typed at the prompt and never echoed, under a rupee cap from the batch-1 dry run; then the reviewer on its patch. It bills that key's project. Without such a key, skip it: the page's recorded run shows what it does, and the required steps before it prove the loop refuses to start without one.

Run order inside this file:
1. The author's run (source window 70)
2. The author's run (source window 72)

Prerequisites: demo_08_the_live_loop_gemini_cli_in_a_container_on_a_model_only_key.
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


# Original CLI workflow for step_01_the_author_s_run.
COMMANDS_01 = """make ralph-image                                   # Gemini CLI at the kit's pin; once a session
read -rs RALPH_API_KEY && export RALPH_API_KEY     # the model-only key, typed: never echoed, never in history
make ralph RALPH_MAX_ITERS=8 RALPH_BUDGET_INR=CAP OUT="$HOME/ralph-live"   # CAP: from the batch-1 dry run

"""

def step_01_the_author_s_run(session):
    """Run The author's run at this checkpoint.

    The author ran the loop in Cloud Shell, which has Docker, with the image built in the same session (Cloud Shell's Docker storage does not outlive it). The cap came from a one-iteration dry run in batch 1. If the probe finds the key needs a project, RALPH_PROJECT adds GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION=global to the agent's environment.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the author's run, on the author's lane, in Cloud Shell (batch 4): yours refuses, as above.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ralph_loop.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_author_s_run.
COMMANDS_02 = """export RUN="$(ls -dt "$HOME"/ralph-live/ralph-* | head -n 1)"
make review-diff PROJECT="$PROJECT" DIFF="$RUN/ralph.patch"

"""

def step_02_the_author_s_run(session):
    """Run The author's run at this checkpoint.

    The author ran the loop in Cloud Shell, which has Docker, with the image built in the same session (Cloud Shell's Docker storage does not outlive it). The cap came from a one-iteration dry run in batch 1. If the probe finds the key needs a project, RALPH_PROJECT adds GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION=global to the agent's environment. Then the reviewer, on the loop's own work:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the author's run (batch 4): the reviewer on the live loop's work.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/review_diff.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_70', step_01_the_author_s_run),
        ('source_72', step_02_the_author_s_run),
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
