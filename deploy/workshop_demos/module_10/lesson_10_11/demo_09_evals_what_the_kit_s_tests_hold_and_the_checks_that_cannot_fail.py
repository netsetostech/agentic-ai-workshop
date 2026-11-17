"""Lesson 10.11: Evals: what the kit's tests hold, and the checks that cannot fail

The cell loads the kit's test module and runs its four classes that need no bash and no make, one test at a time, printing each by its name.

Run order inside this file:
1. Do it: the kit's tests, offline (source window 63)

Prerequisites: demo_08_cost_at_10_what_breaks_first_is_the_read.
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


def step_01_the_kit_s_tests_offline(session):
    """Run Do it: the kit's tests, offline at this checkpoint.

    The cell loads the kit's test module and runs its four classes that need no bash and no make, one test at a time, printing each by its name.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: the kit's tests stand gcloud in).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: PolicyTests (7)
      ok   a policy without a row or a row without a policy stops
      ok   a runbook is the policys own documentation
      ok   each rows evidence reads what its policy counts
      ok   every command the catalog names is one remediate may print
      ok   every policy the kit declares has one row
      ok   the denylist reads a commands words and flags never its values
      ok   the runbooks listing
    RuleTests (15)
      ok   a candidate is kept out of the incident
      ok   a failure no change explains is no rule
      ok   an unknown policy is no rule
      ok   documind api rolls back with make rollback
      ok   every policy named offline
      ok   held model calls names the cap
      ok   held model chooses the rollbac
    """
    import importlib.util, unittest, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    spec = importlib.util.spec_from_file_location("test_remediate", "commands/tests/test_remediate.py")
    t = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(t)
    for cls in (t.PolicyTests, t.RuleTests, t.SafetyTests, t.LiveReadTests):     # the four that need no bash and no make
        names = unittest.TestLoader().getTestCaseNames(cls)
        print(f"{cls.__name__} ({len(names)})")
        for name in names:
            result = unittest.TestResult()
            cls(name).run(result)
            print(f"  {'ok  ' if result.wasSuccessful() else 'FAIL'} {name[5:].replace('_', ' ')}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_63', step_01_the_kit_s_tests_offline),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
