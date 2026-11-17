"""Lesson 0.5: Before you run anything: open Cloud Shell and keep it alive

Open the Google Cloud console signed in as the account that owns your billing account, and click Activate Cloud Shell. Start a tmux session: builds and the Terraform apply run for a long time, and inside tmux they keep running if the browser drops.

Run order inside this file:
1. Before you run anything: open Cloud Shell and keep it alive (source window 1)

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


# Original CLI workflow for step_01_before_you_run_anything_open_cloud_shell_a.
COMMANDS_01 = """tmux new -s documind            # later, after a disconnect: tmux attach -t documind
gcloud --version | sed -n 1p
gcloud config get-value account
git --version
python3 --version

"""

def step_01_before_you_run_anything_open_cloud_shell_a(session):
    """Run Before you run anything: open Cloud Shell and keep it alive at this checkpoint.

    Open the Google Cloud console signed in as the account that owns your billing account, and click Activate Cloud Shell. Start a tmux session: builds and the Terraform apply run for a long time, and inside tmux they keep running if the browser drops.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Cloud Shell, once per session.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_1', step_01_before_you_run_anything_open_cloud_shell_a),
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
