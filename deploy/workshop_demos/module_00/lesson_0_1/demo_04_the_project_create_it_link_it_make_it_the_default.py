"""Lesson 0.1: The project: create it, link it, make it the default

Put your account ID from step 3 and your project ID in the first two lines, then paste the block. --set-as-default makes the new project gcloud's default, so every later command in this session finds it without being told, and so do the Basics pages, which read it with gcloud config get-value project.

Run order inside this file:
1. With gcloud (source window 6)

Prerequisites: demo_03_the_billing_account_free_trial_or_paid.
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


# Original CLI workflow for step_01_with_gcloud.
COMMANDS_01 = """export BILLING=XXXXXX-XXXXXX-XXXXXX     # yours: the ACCOUNT_ID of the OPEN account in the list above
export PROJECT=documind-ai-YOUR-ID      # yours: 6 to 30 characters, lower case, digits and hyphens, a letter first
gcloud projects create "$PROJECT" --name="DocuMind lane" --set-as-default
gcloud billing projects link "$PROJECT" --billing-account="$BILLING"

"""

def step_01_with_gcloud(session):
    """Run With gcloud at this checkpoint.

    Put your account ID from step 3 and your project ID in the first two lines, then paste the block. --set-as-default makes the new project gcloud's default, so every later command in this session finds it without being told, and so do the Basics pages, which read it with gcloud config get-value project.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in Cloud Shell, once (put your own account id and project id in the first two lines).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/project_link.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_with_gcloud),
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
