"""Lesson 2.2: The ablation: one knob per arm, no model in the loop

The first run takes five rows and about a minute; the second takes acme's 40 rows and a few minutes, and appends one JSON line per arm to a ledger you keep. make ablate passes your exported REGION as the embedding region, which is where the API embeds; the direct call is the same line without make.

Run order inside this file:
1. Do it: a wiring check, then acme's rows with a ledger (source window 26)

Prerequisites: demo_05_rrf_by_hand_the_kit_s_rule_reproduces_the_server_s_order.
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


# Original CLI workflow for step_01_a_wiring_check_then_acme_s_rows_with_a_led.
COMMANDS_01 = """make ablate PROJECT=$PROJECT ABLATE_ARGS="--tenant acme --limit 5"
# the same without make: python evals/ablate.py --project $PROJECT --region $REGION --tenant acme --limit 5

make ablate PROJECT=$PROJECT ABLATE_ARGS="--tenant acme --ledger ~/ablate.jsonl"
tail -n 4 ~/ablate.jsonl | python -c "import sys, json; [print(j['arm'][:32].ljust(34), 'recall@5', j['recall_at_5'], 'mrr', j['mrr'], 'p95', j['p95_ms'], 'ms') for j in map(json.loads, sys.stdin)]"

"""

def step_01_a_wiring_check_then_acme_s_rows_with_a_led(session):
    """Run Do it: a wiring check, then acme's rows with a ledger at this checkpoint.

    The first run takes five rows and about a minute; the second takes acme's 40 rows and a few minutes, and appends one JSON line per arm to a ledger you keep. make ablate passes your exported REGION as the embedding region, which is where the API embeds; the direct call is the same line without make.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (embeddings in paise; the Ranking API per request, a few rupees).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 40 rows with anchors, NN anchors, one knob per arm (project documind-ai-YOUR-ID, embeddings in asia-south1, ranker on global)

    arm                                          recall@depth  recall@5    mrr rows@1.0  p95 ms
    dense 5, no reranker                                 0.9x      0.9x   0.8x       3x    xxxx
    dense 20 -> rerank 5   (the lane)                    0.9x      0.9x   0.9x       3x    xxxx
           lost: lk-xx: PB-02 - ranked out (in the candidates, not the five)
    dense 50 -> rerank 5                                 0.9x      0.9x   0.9x       3x    xxxx
    hybrid 20 -> rerank 5  (4.5, not wired)              0.9x      0.9x   0.9x       3x    xxxx

    Read it in this order: recall@depth is 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_a_wiring_check_then_acme_s_rows_with_a_led),
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
