"""Lesson 11.3: make smoke-deployed and make incident, line by line

commands/tests/test_release_repair.py runs this lesson against lesson 11.2's stand-in gcloud, extended with the template, gcloud run services update, the service and revision lists, and a stand-in make for the smokes. Where a POSIX sh is installed, as in Cloud Shell, 2 of its tests run the Makefile's own recipes: the whole controlled failure from make promote-gated back to the gated state, including that a make release-candidate after the rollback inherits the typo, and make smoke-deployed itself, with its one HTTP request caught by a local proxy. It calls nothing in Google Cloud and costs nothing; it starts a process for every stand-in call, so give it a few minutes.

Run order inside this file:
1. Do it: the kit's own tests (source window 19)

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


# Original CLI workflow for step_01_the_kit_s_own_tests.
COMMANDS_01 = """python commands/tests/test_release_repair.py

"""

def step_01_the_kit_s_own_tests(session):
    """Run Do it: the kit's own tests at this checkpoint.

    commands/tests/test_release_repair.py runs this lesson against lesson 11.2's stand-in gcloud, extended with the template, gcloud run services update, the service and revision lists, and a stand-in make for the smokes. Where a POSIX sh is installed, as in Cloud Shell, 2 of its tests run the Makefile's own recipes: the whole controlled failure from make promote-gated back to the gated state, including that a make release-candidate after the rollback inherits the typo, and make smoke-deployed itself, with its one HTTP request caught by a local proxy. It calls nothing in Google Cloud and costs nothing; it starts a process for every stand-in call, so give it a few minutes.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (stand-ins only: no Google call, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: .......................
    ----------------------------------------------------------------------
    Ran 23 tests in Ns

    OK
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_the_kit_s_own_tests),
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
