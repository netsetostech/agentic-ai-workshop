"""Lesson 7.4: Six arms, one golden set: is a store as good?

Do it

Run order inside this file:
1. Do it (source window 11)

Prerequisites: demo_03_the_four_events_through_the_kit_s_mirror_run.
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


# Original CLI workflow for step_01_six_arms_one_golden_set_is_a_store_as_good.
COMMANDS_01 = """python -m pip install -q rank-bm25==0.2.2      # the hybrid arm's BM25 (lesson 2.2 installed it; safe to repeat)
make ablate PROJECT="$PROJECT" ABLATE_ARGS="--arms all"

"""

def step_01_six_arms_one_golden_set_is_a_store_as_good(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (retrieval only, no model: a few minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/ablate.py --project documind-ai-YOUR-ID --region asia-south1 --arms all
    47 rows with anchors, 66 anchors, one knob per arm (project documind-ai-YOUR-ID, embeddings in asia-south1, ranker on global)

    arm                                          recall@depth  recall@5    mrr rows@1.0  p95 ms
    dense 5, no reranker                                 0.94      0.94   0.81       44     ...
           lost: lk-19: payment_of_bonus_act_1965 - not retrieved at depth 5
           lost: lk-21: code_on_wages_2019 - not retrieved at depth 5
           lost: jn-11: labour_codes_compliance_handbook - not retrieved at depth 5
    dense 20 -> rerank 5   (the lane)                    1.00      0.94   0.81       44  
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_six_arms_one_golden_set_is_a_store_as_good),
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
