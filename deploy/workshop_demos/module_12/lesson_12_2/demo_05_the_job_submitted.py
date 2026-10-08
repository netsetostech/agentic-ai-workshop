"""Lesson 12.2: The job, submitted

Do it

Run order inside this file:
1. Do it (source window 16)

Prerequisites: demo_04_the_frozen_file_validated.
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


# Original CLI workflow for step_01_the_job_submitted.
COMMANDS_01 = """make tune PROJECT="$PROJECT" VERSION=v2 TUNE_ARGS="--display-name documind-sft-v2 --no-wait" | tee ~/tune172.log
export JOB="$(grep -o 'projects/[^ ]*/tuningJobs/[0-9]*' ~/tune172.log | head -1)"; echo "JOB=$JOB"

"""

def step_01_the_job_submitted(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (submits the job and returns: the billed act).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/tune.py --project documind-ai-YOUR-ID --dataset gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_${VERSION:-v1}.vertex.jsonl \\
      --base gemini-3.1-flash-lite --epochs 3 --adapter 4 --display-name documind-sft-v2 --no-wait
      submitted projects/NUMBER/locations/us-central1/tuningJobs/7240862654976436473 on gemini-3.1-flash-lite: 3 epochs, adapter 4, dataset gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_v2.vertex.jsonl
      poll later: python evals/tune.py --project documind-ai-YOUR-ID --poll projects/NUMBER/locations/us-central1/tuningJobs/7240862654976436473
    JOB=projects/NUMBER/locations/us-central1/tuningJobs/7240862654976436473
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_the_job_submitted),
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
