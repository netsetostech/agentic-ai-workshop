"""Lesson 5.6: Roles and cases, in the code

No lane and no cost: five of commands/tests/test_cases.py's tests, run against its fake Firestore and fake audit bucket. Who holds what; an expired draft is 410; nobody else can tell a case exists; a POSH case holds no text, and one press opens one; and the audit actor is a case reference.

Run order inside this file:
1. Do it: five of the queue's tests (source window 40)

Prerequisites: demo_05_one_fixed_reply_at_every_door.
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


# Original CLI workflow for step_01_five_of_the_queue_s_tests.
COMMANDS_01 = """python -m unittest -v commands/tests/test_cases.py -k who_holds -k expired -k nobody_else -k posh_case_holds -k audit_actor 2>&1 | tail -n 10

"""

def step_01_five_of_the_queue_s_tests(session):
    """Run Do it: five of the queue's tests at this checkpoint.

    No lane and no cost: five of commands/tests/test_cases.py's tests, run against its fake Firestore and fake audit bucket. Who holds what; an expired draft is 410; nobody else can tell a case exists; a POSH case holds no text, and one press opens one; and the audit actor is a case reference.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (five of the case queue's offline tests; no lane, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: test_a_posh_case_holds_no_text_and_one_press_opens_one (commands.tests.test_cases.CaseTests.test_a_posh_case_holds_no_text_and_one_press_opens_one) ... ok
    test_an_expired_draft_is_410 (commands.tests.test_cases.CaseTests.test_an_expired_draft_is_410) ... ok
    test_nobody_else_can_tell_a_case_exists (commands.tests.test_cases.CaseTests.test_nobody_else_can_tell_a_case_exists) ... ok
    test_the_audit_actor_is_a_case_reference (commands.tests.test_cases.CaseTests.test_the_audit_actor_is_a_case_reference) ... ok
    test_who_holds_what (commands.tests.test_cases.RolesTests.test_who_holds_what) ... ok

    ----------------------------------------------------------------------
    Ran 5 tests in N.NNNs

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
        ('source_40', step_01_five_of_the_queue_s_tests),
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
