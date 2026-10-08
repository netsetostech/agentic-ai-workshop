"""Lesson 0.2: Prove a first success: make dryrun

Run it

Run order inside this file:
1. Run it (source window 25)

Prerequisites: demo_04_the_rs_0_lane_the_notice_period_question_with_citations.
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


# Original CLI workflow for step_01_prove_a_first_success_make_dryrun.
COMMANDS_01 = """cd "$DEMO_ROOT" && source "$HOME/rag-shell-venv/bin/activate"
make dryrun          # or, without make: python extract_documind.py --check && python validate.py && python evals/run_eval.py

"""

def step_01_prove_a_first_success_make_dryrun(session):
    """Run Run it at this checkpoint.

    Run it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the first terminal, in the operator venv.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: kit-only checkout: no curriculum notebooks under Module */ - nothing to extract or check; deploy/ here IS the extracted tree

      DocuMind AI — Tier-A offline dry run
      ------------------------------------------------------------
      [SKIP] extract       kit-only checkout (the learner repo): deploy/ is the extracted tree, nothing to compare  (Ns)
      [PASS] py_compile    125 python files parse  (Ns)
      [PASS] imports       all local imports resolve  (Ns)
      [PASS] shared-deps   every google.cloud client a shared module opens is pinned by its importers  (Ns)
      [PASS] requirements  11 files, all deps pinned  (Ns)
      [PASS] pins          30 shared packages agree across 12 files  (Ns)
      [PASS] dockerfile
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_prove_a_first_success_make_dryrun),
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
