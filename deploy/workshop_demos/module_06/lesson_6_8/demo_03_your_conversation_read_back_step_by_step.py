"""Lesson 6.8: Your conversation, read back step by step

Do it: two questions in the UI Do it: your thread

Run order inside this file:
1. Do it: two questions in the UI (source window 9)
2. Do it: your thread (source window 11)

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


# Original CLI workflow for step_01_two_questions_in_the_ui.
COMMANDS_01 = """echo "open https://documind-ui-$NUMBER.$REGION.run.app and sign in as $ME"

"""

def step_01_two_questions_in_the_ui(session):
    """Run Do it: two questions in the UI at this checkpoint.

    Do it: two questions in the UI

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the address of your UI).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: open https://documind-ui-NUMBER.asia-south1.run.app and sign in as you@your-company.com
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_your_thread.
COMMANDS_02 = """make thread EMAIL="$ME" | tee /tmp/lesson68-threads.txt          # your threads, the latest written first
SID=$(awk '$1 == "acme" && $2 !~ /^desk~/ {print $2; exit}' /tmp/lesson68-threads.txt)   # the newest chat thread: the UI's
echo "SID=$SID"
make thread EMAIL="$ME" SESSION="$SID"                              # that thread, a row per checkpoint

"""

def step_02_your_thread(session):
    """Run Do it: your thread at this checkpoint.

    Do it: your thread

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (your threads, then the newest decoded; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ui_thread.txt]
    """
    manual_checkpoint("In the deployed UI's Chat page, signed in as yourself, set Brain to langgraph and ask: After how many years of continuous service is gratuity payable? When the answer is in, ask: Is it payable to a contract employee? Type done to read your thread back from the checkpointer: without the two questions there is no thread, and every later step of this lesson has nothing to read.")
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_two_questions_in_the_ui),
        ('source_11', step_02_your_thread),
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
