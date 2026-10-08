"""Lesson 12.1: Your training file, as v2

Do it

Run order inside this file:
1. Do it (source window 18)

Prerequisites: demo_04_the_evidence_and_the_verdict.
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


# Original CLI workflow for step_01_your_training_file_as_v2.
COMMANDS_01 = """python -m pip install -q google-genai==2.22.0 google-cloud-dlp==3.39.0   # the ingest image's pins: the model that writes the rows, the PII scan
make trainset PROJECT="$PROJECT" TRAINSET_ARGS="--version v2"     # v1 is the kit's own file: yours is v2

"""

def step_01_your_training_file_as_v2(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (about twenty minutes: one flash call a chunk).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/make_trainset.py --project documind-ai-YOUR-ID --tenant acme --rows ${ROWS:-300} \\
      --upload gs://documind-ai-YOUR-ID-datasets/sft/ --version v2
      300 chunks sampled from acme's corpus mirrors
      315 rows (30 refusals) from 12 documents; dropped 15 for golden overlap ['jn-10', 'jn-11', 'lk-14', 'lk-17', 'lk-18', 'lk-23', 'lk-24', 'lk-26', 'lk-28'] and 0 by the PII scan
      wrote /home/YOU/deploy_module_rag/evals/sft/documind_sft_v2.{vertex,chat}.jsonl + .manifest.json (sha ac73343d2550)
      uploaded gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_v2.chat.jsonl
      uploaded gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_v2.manifest.json
      uploaded gs://documind-ai-YOUR-ID-datase
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_your_training_file_as_v2),
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
