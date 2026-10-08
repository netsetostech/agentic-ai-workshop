"""Lesson 12.3: The verdict and the delta

Do it: the verdict The gates and the judge asked both revisions the same questions, so their usage rows are like for like. The cell prints make usage's model table, groups the rows by model, and prices the endpoint's rows at 1.5 times what they log.

Run order inside this file:
1. Do it: the verdict (source window 21)
2. Do it: the delta (source window 23)

Prerequisites: demo_05_the_gate_on_both_revisions.
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


# Original CLI workflow for step_01_the_verdict.
COMMANDS_01 = """make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" API_B="$CAND"

"""

def step_01_the_verdict(session):
    """Run Do it: the verdict at this checkpoint.

    Do it: the verdict

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the judge's venv from lesson 4.2: 65 answers from each revision, then Vertex AI Evaluation).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://documind-api-NUMBER.asia-south1.run.app
      65/65 answers collected from https://documind-api-NUMBER.asia-south1.run.app in ...s (model gemini-3.6-flash)
      65/65 candidate answers from https://candidate---documind-api-NUMBER.asia-south1.run.app
      context: 46/46 cited chunks read in full from the store
      trajectories: off (no --chat-url)
      pointwise: GROUNDEDNESS + INSTRUCTION_FOLLOWING  (templates cd7070; run api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070)
      judge: the service default (pass --judge-model to pin one)

      Experiments run documind-eval/api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070:
        groundedness/mean                                1.000
        groundedness/mean[isolation
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_delta.
COMMANDS_02 = """make usage PROJECT="$PROJECT" HOURS=2 | sed -n '/^by model and backend/,/^$/p'
python - <<'PY'
import os, sys
sys.path.insert(0, "evals")
from usage_rows import group, read_rows
EP, TUNED = os.environ["ENDPOINT"], 1.5      # Google's pricing page: a tuned Gemini 3 endpoint answers at 1.5 x its base
per = {g["model"]: g for g in group(read_rows(os.environ["PROJECT"], 2), ("model",))}
live, cand = per["gemini-3.6-flash"], per[EP]
a, logged = live["inr"] / live["answers"], cand["inr"] / cand["answers"]
print(f"  live       {live['answers']:4} answers  Rs {a:.4f} an answer")
print(f"  candidate  {cand['answers']:4} answers  Rs {logged:.4f} an answer as logged, Rs {logged * TUNED:.4f} as Google bills it")
d = a - logged * TUNED
print(f"the rupee delta: the tuned endpoint costs Rs {d:.4f} less an answer, Rs {d * 1000:,.0f} per 1,000 answers")
print(f"  (the usage rows alone say Rs {a - logged:.4f}: they log the endpoint at its base's rate)")
PY

"""

def step_02_the_delta(session):
    """Run Do it: the delta at this checkpoint.

    The gates and the judge asked both revisions the same questions, so their usage rows are like for like. The cell prints make usage's model table, groups the rows by model, and prices the endpoint's rows at 1.5 times what they log.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the last two hours of usage rows).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: by model and backend (what answered, through which door)
    model                 model_backend          answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ----------------------------------------------------------------------------------------------------------
    gemini-3.6-flash      vertex                     130    952849    28030    1.6395    139.36    2100   0.00
    projects/NUMBER/loca  vertex                     130    970907    17751    0.2694     22.89    1000   0.00

      live        130 answers  Rs 1.0720 an answer
      candidate   130 answers  Rs 0.1761 an answer as logged, Rs 0.2641 as Google bills it
    the rupee delta: the tuned endpoint costs Rs 0.8079 less an answer, Rs 808 per 1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_the_verdict),
        ('source_23', step_02_the_delta),
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
