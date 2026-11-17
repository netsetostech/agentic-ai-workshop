"""Lesson 11.8: The handover: HANDOVER.md from the checkout and the lane

Without PROJECT= every section gives the checkout's half and says the lane was not given. The canned fork is a copy of the kit, so its checkout half is the kit's: the policies, the night job, the floors, the budget and the state bucket as the Makefile and Terraform declare them, plus the canned records under Revisions. In your fork, with PROJECT and REGION. Reads only. The file lands in the fork's root; the recording is the author's lane.

Run order inside this file:
1. Do it: the handover, offline, on the canned fork (source window 37)
2. Do it: the handover of your lane (source window 39)

Prerequisites: demo_07_your_lane_read_with_the_two_tokens.
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


# Original CLI workflow for step_01_the_handover_offline_on_the_canned_fork.
COMMANDS_01 = """make handover FORK=/tmp/sahyadri && cat /tmp/sahyadri/HANDOVER.md

"""

def step_01_the_handover_offline_on_the_canned_fork(session):
    """Run Do it: the handover, offline, on the canned fork at this checkpoint.

    Without PROJECT= every section gives the checkout's half and says the lane was not given. The canned fork is a copy of the kit, so its checkout half is the kit's: the policies, the night job, the floors, the budget and the state bucket as the Makefile and Terraform declare them, plus the canned records under Revisions.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (writes HANDOVER.md into the canned fork; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> handover: /tmp/sahyadri/HANDOVER.md, from this checkout only (PROJECT= adds the lane)
    # Handover: DocuMind, this checkout

    Written by `make handover` (commands/capstone_check.py handover) at YYYY-MM-DDTHH:MM:SSZ, from this checkout; PROJECT= adds what the lane shows. It read, and changed nothing. Each section gives what the checkout states, then what the lane shows; where the two differ, the lane is what runs. make handover writes the file whole each time: notes of your own belong in RUNBOOK.md, whose template is capstone/templates/RUNBOOK.md.

    ## Alert policies

    17 policies declared in terraform/*.tf, each with what ops/runbooks.json says to do when it pages.

    | Policy | Declared in | Ap
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_handover_of_your_lane.
COMMANDS_02 = """make handover PROJECT="$PROJECT" REGION="$REGION" && cat HANDOVER.md

"""

def step_02_the_handover_of_your_lane(session):
    """Run Do it: the handover of your lane at this checkpoint.

    In your fork, with PROJECT and REGION. Reads only. The file lands in the fork's root; the recording is the author's lane.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in your fork (reads the lane, writes HANDOVER.md into the fork; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/handover.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_37', step_01_the_handover_offline_on_the_canned_fork),
        ('source_39', step_02_the_handover_of_your_lane),
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
