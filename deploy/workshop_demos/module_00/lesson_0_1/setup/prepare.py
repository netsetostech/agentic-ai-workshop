"""Lesson 0.1: Before you run anything: open Cloud Shell

This lesson needs a Google account, a browser, and a shell where the gcloud CLI acts as you. Cloud Shell is the simplest: a terminal in the browser, on a Debian machine Google provisions for you, with the gcloud CLI already installed and 5 GB of free persistent disk as your home directory. Open the Google Cloud console at console.cloud.google.com, sign in with the Google account you will use for the whole course, and click Activate Cloud Shell, the terminal icon at the top right. A laptop works too, if the gcloud CLI is installed and signed in; lesson 0.2 sets a laptop up properly. Nothing on this page needs the kit: there is no clone yet, no Python environment and no lane, and every command here costs Rs 0. Run the block below once per session. It prints gcloud's version, the account it acts as, and its default project, which stays empty until step 4 sets it.

Run order inside this file:
1. Before you run anything: open Cloud Shell (source window 1)

Prerequisites: workshop setup; see this lesson README.
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


# Original CLI workflow for step_01_before_you_run_anything_open_cloud_shell.
COMMANDS_01 = """gcloud --version | head -n 1
gcloud config get-value account
gcloud config get-value project

"""

def step_01_before_you_run_anything_open_cloud_shell(session):
    """Run Before you run anything: open Cloud Shell at this checkpoint.

    This lesson needs a Google account, a browser, and a shell where the gcloud CLI acts as you. Cloud Shell is the simplest: a terminal in the browser, on a Debian machine Google provisions for you, with the gcloud CLI already installed and 5 GB of free persistent disk as your home directory. Open the Google Cloud console at console.cloud.google.com, sign in with the Google account you will use for the whole course, and click Activate Cloud Shell, the terminal icon at the top right. A laptop works too, if the gcloud CLI is installed and signed in; lesson 0.2 sets a laptop up properly. Nothing on this page needs the kit: there is no clone yet, no Python environment and no lane, and every command here costs Rs 0. Run the block below once per session. It prints gcloud's version, the account it acts as, and its default project, which stays empty until step 4 sets it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in Cloud Shell, once per session (or in a terminal where gcloud is signed in).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/setup_check.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_1', step_01_before_you_run_anything_open_cloud_shell),
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
