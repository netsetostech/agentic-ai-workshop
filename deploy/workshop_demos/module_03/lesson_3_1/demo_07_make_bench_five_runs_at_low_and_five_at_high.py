"""Lesson 3.1: make bench: five runs at LOW and five at HIGH

The bench on your lane: jn-03's pool read once from your /v1/passages, then generate() five times at LOW and five at HIGH, interleaved, each answer judged and priced. --show adds the pool and each level's distinct answers, the most frequent first. --report keeps every answer, the config it was sent with, its usage and its verdict in evals/reports/bench-levels.json, which the kit's .gitignore keeps out of git. The bench imports generator.py in your shell: Module 0 installed rag-api's pins in your venv, and if this shell lacks one the bench names it and stops before any call.

Run order inside this file:
1. Definition (source window 28)

Prerequisites: demo_06_five_calls_to_v1_query_judged_by_the_gate_s_rule.
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


# Original CLI workflow for step_01_definition.
COMMANDS_01 = """make bench PROJECT="$PROJECT" REGION="$REGION" BENCH_ARGS="--rows jn-03 --runs 5 --levels LOW,HIGH --show --report evals/reports/bench-levels.json"

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    The bench on your lane: jn-03's pool read once from your /v1/passages, then generate() five times at LOW and five at HIGH, interleaved, each answer judged and priced. --show adds the pool and each level's distinct answers, the most frequent first. --report keeps every answer, the config it was sent with, its usage and its verdict in evals/reports/bench-levels.json, which the kit's .gitignore keeps out of git. The bench imports generator.py in your shell: Module 0 installed rag-api's pins in your venv, and if this shell lacks one the bench names it and stops before any call.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (ten answers, five at LOW and five at HIGH: about Rs 2.02 of input, at most Rs 15.08 at the cap; a cut-off answer asked again adds up to Rs 3.92).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/bench_levels.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_28', step_01_definition),
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
