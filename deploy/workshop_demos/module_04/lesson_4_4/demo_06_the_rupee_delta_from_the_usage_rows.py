"""Lesson 4.4: The rupee delta, from the usage rows

Every answer of the last hour, grouped by the model that gave it, and the difference per answer. The API priced every answer on its usage row with cost.price(), at the rates of the model that answered. The gate's runs and the judge's collections asked both revisions the same questions, so the two groups are like for like. The cell groups the last hour's rows by model and divides.

Run order inside this file:
1. The rupee delta, from the usage rows (source window 24)

Prerequisites: demo_05_the_pairwise_judge_which_answer_is_better_row_by_row.
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


def step_01_the_rupee_delta_from_the_usage_rows(session):
    """Run The rupee delta, from the usage rows at this checkpoint.

    Every answer of the last hour, grouped by the model that gave it, and the difference per answer. The API priced every answer on its usage row with cost.price(), at the rates of the model that answered. The gate's runs and the judge's collections asked both revisions the same questions, so the two groups are like for like. The cell groups the last hour's rows by model and divides.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the last hour of usage rows, by model).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gemini-3.6-flash          ... answers  Rs ...  Rs ... an answer
      gemini-3.1-flash-lite     ... answers  Rs ...  Rs ... an answer
      the candidate costs Rs ... less an answer: Rs ... per 1,000 answers
    """
    import os, sys; sys.path.insert(0, "evals")
    from usage_rows import read_rows, group
    per = {g["model"]: g for g in group(read_rows(os.environ["PROJECT"], 1), ("model",))}
    for m, g in per.items():
        print(f"  {m:24} {g['answers']:4} answers  Rs {g['inr']:7.2f}  Rs {g['inr'] / g['answers']:.4f} an answer")
    live, cand = per.get("gemini-3.6-flash"), per.get("gemini-3.1-flash-lite")
    if live and cand:
        d = live["inr"] / live["answers"] - cand["inr"] / cand["answers"]
        print(f"  the candidate costs Rs {d:.4f} less an answer: Rs {d * 1000:,.0f} per 1,000 answers")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_24', step_01_the_rupee_delta_from_the_usage_rows),
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
