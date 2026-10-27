"""Lesson 11.8: The lines the check rests on

The selftest runs every rule on documents, records and PDFs it makes up, with no fork and no lane: the rejected options as a list, a table and sub-sections, the cost model's volumes and date, every way a FAILURE-MODES command resolves or does not, pages from text and from a PDF's page tree, plain and packed, a rollback told from a promote, and the outsider's 403. commands/tests/test_capstone_check.py holds 31 more tests, on the canned fork and on a stand-in lane, and commands/tests/test_capstone_templates.py 13 on the templates of step 5.

Run order inside this file:
1. Do it: the rules on hand-made input (source window 16)

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


# Original CLI workflow for step_01_the_rules_on_hand_made_input.
COMMANDS_01 = """python commands/capstone_check.py --selftest

"""

def step_01_the_rules_on_hand_made_input(session):
    """Run Do it: the rules on hand-made input at this checkpoint.

    The selftest runs every rule on documents, records and PDFs it makes up, with no fork and no lane: the rejected options as a list, a table and sub-sections, the cost model's volumes and date, every way a FAILURE-MODES command resolves or does not, pages from text and from a PDF's page tree, plain and packed, a rollback told from a promote, and the outsider's 403. commands/tests/test_capstone_check.py holds 31 more tests, on the canned fork and on a stand-in lane, and commands/tests/test_capstone_templates.py 13 on the templates of step 5.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the rules on hand-made input; no fork, no lane, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: capstone_check selftest: ARCHITECTURE.md's rejected options (list, table, sub-section; a bare name is not argued), COST-MODEL.md's volumes, amounts, date and rate, FAILURE-MODES.md's entries and every way a command resolves or does not, pages from text and from a PDF's page tree (plain and packed), a rollback told from a promote, the lane smokes and the outsider's 403, each on hand-made input
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_the_rules_on_hand_made_input),
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
