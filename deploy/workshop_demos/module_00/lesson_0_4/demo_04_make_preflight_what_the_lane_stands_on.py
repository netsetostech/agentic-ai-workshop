"""Lesson 0.4: make preflight: what the lane stands on

The script is short enough to read whole. It checks the tools (gcloud, terraform, make, python), that Terraform is at least 1.9, that gcloud is signed in, that the project exists and has billing, that the state bucket exists, that 22 APIs are enabled, and that the one Python package make roster needs is importable. Every check is a read, and every MISS line carries the command that fixes it. Run it with your state bucket. The script's own usage line names the bucket after the project, <project>-tfstate, and the cell uses that name unless you have already exported another. Do not leave TFSTATE_BUCKET off: the Makefile's default, documind-tfstate, is a bucket name only one project in the world can own, and it is not yours.

Run order inside this file:
1. make preflight: what the lane stands on (source window 11)

Prerequisites: demo_03_the_ui_the_smoke_s_question_asked_by_you.
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


# Original CLI workflow for step_01_make_preflight_what_the_lane_stands_on.
COMMANDS_01 = """export TFSTATE_BUCKET="${TFSTATE_BUCKET:-$PROJECT-tfstate}"   # lesson 0.3's state bucket: preflight.sh's own usage line names it <project>-tfstate
make preflight PROJECT="$PROJECT" TFSTATE_BUCKET="$TFSTATE_BUCKET" REGION="$REGION"

"""

def step_01_make_preflight_what_the_lane_stands_on(session):
    """Run make preflight: what the lane stands on at this checkpoint.

    The script is short enough to read whole. It checks the tools (gcloud, terraform, make, python), that Terraform is at least 1.9, that gcloud is signed in, that the project exists and has billing, that the state bucket exists, that 22 APIs are enabled, and that the one Python package make roster needs is importable. Every check is a read, and every MISS line carries the command that fixes it. Run it with your state bucket. The script's own usage line names the bucket after the project, <project>-tfstate, and the cell uses that name unless you have already exported another. Do not leave TFSTATE_BUCKET off: the Makefile's default, documind-tfstate, is a bucket name only one project in the world can own, and it is not yours.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (read-only; creates nothing; under a minute).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/preflight.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_make_preflight_what_the_lane_stands_on),
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
