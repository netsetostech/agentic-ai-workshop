"""Lesson 5.8: The pause, in the kit: approval.py

make approval-check is commands/approval-check.sh. It makes ~/graph-venv if it is missing (lesson 5.4 made it), installs the chat image's pins and the SQLite checkpointer, langgraph-checkpoint-sqlite 3.1.1, the version services/chat/requirements-local.txt pins, and runs commands/tests/test_approvals.py. CI's chat-pins step runs the same file. It needs no credential, no network after the install, and costs nothing.

Run order inside this file:
1. Do it: the kit's own tests (source window 23)

Prerequisites: demo_03_your_lane_the_people_team_s_reader_and_a_request_for_a_person_on_the_desk_page.
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
COMMANDS_01 = """make approval-check

"""

def step_01_the_kit_s_own_tests(session):
    """Run Do it: the kit's own tests at this checkpoint.

    make approval-check is commands/approval-check.sh. It makes ~/graph-venv if it is missing (lesson 5.4 made it), installs the chat image's pins and the SQLite checkpointer, langgraph-checkpoint-sqlite 3.1.1, the version services/chat/requirements-local.txt pins, and runs commands/tests/test_approvals.py. CI's chat-pins step runs the same file. It needs no credential, no network after the install, and costs nothing.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's own tests, offline; the first run makes or completes ~/graph-venv).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: test_a_rejection_errors_that_call_only (commands.tests.test_approvals.Approvals.test_a_rejection_errors_that_call_only) ... ok
    test_a_second_process_resumes_the_turn_from_the_sqlite_file (commands.tests.test_approvals.Approvals.test_a_second_process_resumes_the_turn_from_the_sqlite_file) ... ok
    test_a_turn_with_nothing_to_approve_does_not_pause (commands.tests.test_approvals.Approvals.test_a_turn_with_nothing_to_approve_does_not_pause) ... ok
    test_ask_user_is_answered_by_the_person_who_asked (commands.tests.test_approvals.Approvals.test_ask_user_is_answered_by_the_person_who_asked) ... ok
    test_offer_case_writes_nothing (commands.tests.test_approvals.Approvals.test_offer_case_writes_nothing) 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_the_kit_s_own_tests),
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
