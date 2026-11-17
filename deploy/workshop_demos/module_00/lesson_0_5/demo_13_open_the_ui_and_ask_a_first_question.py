"""Lesson 0.5: Open the UI and ask a first question

The end-to-end check a person makes. Print the UI's address and open it in a browser signed in as your operator account: A 403 after you signed in means the roster, not IAP: rerun the tenants step and read the rosters back. A first-time IAP setup on a project without an organization may also ask for the OAuth consent screen in the console (Cloud Run, the service, Security, Identity-Aware Proxy); complete it there and retry the failed command. Never switch authentication off to make the page load. That first answer is what the usage views were waiting for: the log sink has now exported the API's first rows, so BigQuery has the table the views read. Create them, from the kit root:

Run order inside this file:
1. Open the UI and ask a first question (source window 58)
2. Open the UI and ask a first question (source window 59)

Prerequisites: demo_12_verify_all_seven_services.
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


# Original CLI workflow for step_01_open_the_ui_and_ask_a_first_question.
COMMANDS_01 = """echo "${UI_URL:?Run F1 in this terminal}"

"""

def step_01_open_the_ui_and_ask_a_first_question(session):
    """Run Open the UI and ask a first question at this checkpoint.

    The end-to-end check a person makes. Print the UI's address and open it in a browser signed in as your operator account:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - the UI's address.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_open_the_ui_and_ask_a_first_question.
COMMANDS_02 = """cd "${DEMO_ROOT:?Restore ~/rag-env.sh}" &&
make bq-views PROJECT="${PROJECT:?Restore ~/rag-env.sh}"

"""

def step_02_open_the_ui_and_ask_a_first_question(session):
    """Run Open the UI and ask a first question at this checkpoint.

    A 403 after you signed in means the roster, not IAP: rerun the tenants step and read the rosters back. A first-time IAP setup on a project without an organization may also ask for the OAuth consent screen in the console (Cloud Run, the service, Security, Identity-Aware Proxy); complete it there and retry the failed command. Never switch authentication off to make the page load. That first answer is what the usage views were waiting for: the log sink has now exported the API's first rows, so BigQuery has the table the views read. Create them, from the kit root:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - the usage views, after the first answer.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_58', step_01_open_the_ui_and_ask_a_first_question),
        ('source_59', step_02_open_the_ui_and_ask_a_first_question),
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
