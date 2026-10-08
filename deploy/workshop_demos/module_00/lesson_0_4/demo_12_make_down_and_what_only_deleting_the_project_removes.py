"""Lesson 0.4: make down, and what only deleting the project removes

MANAGED_SEARCH is true by default, so the state holds two Vertex AI Search data stores, one for acme and one for zeta, each with prevent_destroy. Terraform rejects any plan that would destroy such a resource, and a destroy plan destroys everything, so this one destroys nothing: the six lines of step 10 keep billing after make down, still Rs 2,666 a day with a MEDIUM index. The list the recipe prints afterwards does not name the data stores; the kit's README does. Lesson 7.3 meets the same guard from the stores' side. The recipe's last line is the one that ends the bill: delete the throwaway project. Shutting a project down stops all of its billing; for 30 days the project can still be restored, and then it and everything in it are deleted. The same page adds two cautions: charges already run up can still arrive until the current billing cycle ends, and it advises disabling billing on the project before you shut it down. One switch would block the deletion itself: AUDIT_LOCK=true locks the audit bucket's five-year retention and liens the project, which is why it is false for a lab.

Run order inside this file:
1. make down, and what only deleting the project removes (source window 75)

Prerequisites: demo_11_next_session_a_restored_shell.
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


# Original CLI workflow for step_01_make_down_and_what_only_deleting_the_proje.
COMMANDS_01 = """make down PROJECT="$PROJECT" REGION="$REGION"

"""

def step_01_make_down_and_what_only_deleting_the_proje(session):
    """Run make down, and what only deleting the project removes at this checkpoint.

    MANAGED_SEARCH is true by default, so the state holds two Vertex AI Search data stores, one for acme and one for zeta, each with prevent_destroy. Terraform rejects any plan that would destroy such a resource, and a destroy plan destroys everything, so this one destroys nothing: the six lines of step 10 keep billing after make down, still Rs 2,666 a day with a MEDIUM index. The list the recipe prints afterwards does not name the data stores; the kit's README does. Lesson 7.3 meets the same guard from the stores' side. The recipe's last line is the one that ends the bill: delete the throwaway project. Shutting a project down stops all of its billing; for 30 days the project can still be restored, and then it and everything in it are deleted. The same page adds two cautions: charges already run up can still arrive until the current billing cycle ends, and it advises disabling billing on the project before you shut it down. One switch would block the deletion itself: AUDIT_LOCK=true locks the audit bucket's five-year retention and liens the project, which is why it is false for a lab.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, when you are finished with the lane - not now: Module 1 starts on this lane.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/down.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_75', step_01_make_down_and_what_only_deleting_the_proje),
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
