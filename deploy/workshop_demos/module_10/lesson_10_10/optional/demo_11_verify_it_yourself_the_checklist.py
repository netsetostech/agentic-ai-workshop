"""Lesson 10.10: Verify it yourself: the checklist

Fifteen checks, each one step above, each with the value that proves it. Nothing on your lane is configured. The offline runs wrote run directories under /tmp, and the last cell below removes them. Your only spend was the reviewer's calls on gemini-3.6-flash, seven for each repeat, billed to your lane as any model call you make. The human step left your clone as it was. The live loop is the author's: its model-only key was created for the run and deleted after it, so no credential of the loop's exists on any lane. Lesson 10.11 designs an agent that acts on the running lane itself.

Run order inside this file:
1. Verify it yourself: the checklist (source window 82)

Prerequisites: demo_09_direct_reads_and_the_human_step.
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


# Original CLI workflow for step_01_verify_it_yourself_the_checklist.
COMMANDS_01 = """rm -rf /tmp/ralph-hand /tmp/ralph-strong /tmp/ralph-weak /tmp/ralph-cap /tmp/ralph-statute /tmp/change-it-*

"""

def step_01_verify_it_yourself_the_checklist(session):
    """Run Verify it yourself: the checklist at this checkpoint.

    Fifteen checks, each one step above, each with the value that proves it. Nothing on your lane is configured. The offline runs wrote run directories under /tmp, and the last cell below removes them. Your only spend was the reviewer's calls on gemini-3.6-flash, seven for each repeat, billed to your lane as any model call you make. The human step left your clone as it was. The live loop is the author's: its model-only key was created for the run and deleted after it, so no credential of the loop's exists on any lane. Lesson 10.11 designs an agent that acts on the running lane itself.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (optional: the run directories this page made).
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
        ('source_82', step_01_verify_it_yourself_the_checklist),
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
