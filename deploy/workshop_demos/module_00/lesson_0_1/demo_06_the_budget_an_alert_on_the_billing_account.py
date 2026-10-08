"""Lesson 0.1: The budget: an alert on the billing account

The Budget API answers for the same budget. --billing-project makes the call count against your project, where step 5 enabled the Budget API (the kit's helper names a quota project for its own gcloud calls in the same way); the filter picks yours out of any others on the account, and the format keeps the fields the console asked about.

Run order inside this file:
1. Read it back with gcloud (source window 13)

Prerequisites: demo_05_the_apis_40_services_in_two_calls.
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


# Original CLI workflow for step_01_back_with_gcloud.
COMMANDS_01 = """gcloud billing budgets list --billing-account="$BILLING" --billing-project="$PROJECT" \\
  --filter='displayName="Billing account guard"' \\
  --format='yaml(displayName,amount,thresholdRules,budgetFilter.calendarPeriod,budgetFilter.creditTypesTreatment,budgetFilter.creditTypes)'

"""

def step_01_back_with_gcloud(session):
    """Run Read it back with gcloud at this checkpoint.

    The Budget API answers for the same budget. --billing-project makes the call count against your project, where step 5 enabled the Budget API (the kit's helper names a quota project for its own gcloud calls in the same way); the filter picks yours out of any others on the account, and the format keeps the fields the console asked about.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in Cloud Shell after the console steps (read-only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/budgets_list.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_back_with_gcloud),
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
