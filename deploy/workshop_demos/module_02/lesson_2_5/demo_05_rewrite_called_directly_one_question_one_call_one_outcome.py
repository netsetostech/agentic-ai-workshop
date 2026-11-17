"""Lesson 2.5: rewrite() called directly: one question, one call, one outcome

Do it: the bench's nine questions, one call each

Run order inside this file:
1. Do it: the bench's nine questions, one call each (source window 27)

Prerequisites: demo_04_the_stage_in_the_kit_the_call_the_guard_one_line_in_v1_query_and_two_lines_that.
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


def step_01_the_bench_s_nine_questions_one_call_each(session):
    """Run Do it: the bench's nine questions, one call each at this checkpoint.

    Do it: the bench's nine questions, one call each

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; 9 gemini-3.1-flash-lite calls, a few paise).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rewrites.txt]
    """
    import os, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, ".")
    from google import genai
    from shared import prices, query_rewrite
    client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")   # Gemini 3.x is served from global only
    ROWS = [
        ("pp-01", "How much can I claim per trip for domestic travel?"),
        ("pp-10", "How many remote-work days am I allowed per month?"),
        ("jn-07", "A contractor wants to copy data to a USB drive and says their SOW allows it. What applies?"),
        ("lk-06", "What is the notice period for a confirmed E3?"),
        ("pp-07", "Notice period for confirmed E3 employees?"),
        ("pp-09", "Whose approval is needed for a Rs 3 lakh purchase?"),
        ("jn-03", "I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?"),
        ("pp-16", "What is the minimum bonus payable under the Bonus Act?"),
        ("lk-03", "How many days of earned leave can I carry forward?"),
    ]
    tokens_in = tokens_out = 0
    usd = 0.0
    for rid, question in ROWS:
        got = query_rewrite.rewrite(client, question)
        tokens_in, tokens_out, usd = tokens_in + got["tokens_in"], tokens_out + got["tokens_out"], usd + got["cost_usd"]
        detail = {"rewritten": got["query"], "same": "given back as asked - the question is searched",
                  "rejected": "dropped " + ", ".join(got["dropped"]) + " - the question is searched",
                  "fallback": f"{got['error']} - the question is searched"}[got["outcome"]]
        print(f"{rid:6} {got['outcome']:9} {got['ms']:5} ms  {detail}")
    print(f"{len(ROWS)} calls to {query_rewrite.MODEL}, prompt {query_rewrite.PROMPT_VERSION}: {tokens_in:,} tokens in, {tokens_out:,} out, "
          f"Rs {prices.inr(usd):.2f} at list price")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_the_bench_s_nine_questions_one_call_each),
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
