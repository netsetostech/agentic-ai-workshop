"""Lesson 6.4: The curve: every candidate threshold on the labelled pairs

Do it

Run order inside this file:
1. Do it (source window 9)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_the_curve_every_candidate_threshold_on_the.
COMMANDS_01 = """python evals/cache_threshold.py --project "$PROJECT" --report ~/cache93_curve.json

"""

def step_01_the_curve_every_candidate_threshold_on_the(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (65 embeddings, about a minute; the report goes to your home folder).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 42 pairs against 23 golden questions, text-embedding-005 @ us-central1

      threshold   hit rate (same)   false-hit rate (different)
           0.85      100% (24)          83% (15)
           0.88      100% (24)          67% (12)
           0.90       96% (23)          61% (11)
           0.92       62% (15)          50% ( 9)
           0.94       46% (11)          22% ( 4)
           0.95       33% ( 8)          11% ( 2)
           0.96       25% ( 6)           6% ( 1)
           0.97       17% ( 4)           0% ( 0)
           0.98        4% ( 1)           0% ( 0)

      lowest threshold with no false hit: 0.97
      nearest false pairs: pp-25 0.962, pp-31 0.955, pp-37 0.947, pp-35 0.941, pp-42 0.931, pp-41 0.929, pp-27 0.926, pp-30 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_curve_every_candidate_threshold_on_the),
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
