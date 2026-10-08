"""Lesson 4.2: The judge: the lane's own answers, read with the context they cite

Do it: the judge's venv and its self-test --reuse keeps the collected answers in a file. If the Evaluation step stops, the rerun judges the same answers without asking the lane again.

Run order inside this file:
1. Do it: the judge's venv and its self-test (source window 31)
2. Do it: the judge on your lane (source window 33)

Prerequisites: demo_04_the_live_half_every_row_two_identities_nine_rates_three_exit_codes.
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


# Original CLI workflow for step_01_the_judge_s_venv_and_its_self_test.
COMMANDS_01 = """python -m venv "$HOME/judge-venv"            # its own venv: the SDK is a major version ahead of the kit's
"$HOME/judge-venv/bin/python" -m pip install -q "google-cloud-aiplatform[evaluation]==2.1.0" pandas google-cloud-firestore
"$HOME/judge-venv/bin/python" evals/judge.py --selftest

"""

def step_01_the_judge_s_venv_and_its_self_test(session):
    """Run Do it: the judge's venv and its self-test at this checkpoint.

    Do it: the judge's venv and its self-test

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a second venv for the judge, then its offline self-test).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: selftest: the cited chunk's text replaces its quote as the context and a miss keeps the quote; the prompt the judge reads carries the context then the question; the frame carries the six judge columns plus the baseline; the trajectory maths is right on the three cases
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_judge_on_your_lane.
COMMANDS_02 = """mkdir -p evals/reports
make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" JUDGE_ARGS="--reuse evals/reports/judge72.json"

"""

def step_02_the_judge_on_your_lane(session):
    """Run Do it: the judge on your lane at this checkpoint.

    --reuse keeps the collected answers in a file. If the Evaluation step stops, the rerun judges the same answers without asking the lane again.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the lane answers every row again, then Vertex AI Evaluation reads them).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://documind-api-NUMBER.asia-south1.run.app
      65/65 answers collected from https://documind-api-NUMBER.asia-south1.run.app in ...s (model gemini-3.6-flash)
      context: .../... cited chunks read in full from the store
      trajectories: off (no --chat-url)
      pointwise: GROUNDEDNESS + INSTRUCTION_FOLLOWING  (templates cd7070; run api-GITSHA-YYYYMMDD-HHMM-tcd7070)
      pairwise: off (no --api-b)
      judge: the service default (pass --judge-model to pin one)

      Experiments run documind-eval/api-GITSHA-YYYYMMDD-HHMM-tcd7070:
        groundedness/mean                                ...
        groundedness/mean[isolation]                     ...
        groundedness/mean[join]                          ...
        g
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_the_judge_s_venv_and_its_self_test),
        ('source_33', step_02_the_judge_on_your_lane),
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
