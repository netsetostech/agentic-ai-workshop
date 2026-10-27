"""Lesson 10.11: On your lane: hold a fault, read the plan, run it by hand

At lesson end: RESTORE=1 runs the plan's restore for the drill: the variable put back as .fault-hold recorded it, which makes a new revision, then the traffic sent to the latest revision. It checks that the latest revision takes all the traffic, and removes .fault-hold. Then the plan's last step: the smoke, and remediate, which should read no_failure. RESTORE=1 runs the plan's restore for the drill: the variable put back as .fault-hold recorded it, which makes a new revision, then the traffic sent to the latest revision. It checks that the latest revision takes all the traffic, and removes .fault-hold. Then the plan's last step: the smoke, and remediate, which should read no_failure.

Run order inside this file:
1. Restore, and verify again (source window 19)
2. Restore, and verify again (source window 21)

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


# Original CLI workflow for step_01_restore_and_verify_again.
COMMANDS_01 = """if [ -s .fault-hold ]; then make incident-drill PROJECT=$PROJECT RESTORE=1
else echo "no fault is held in this checkout (.fault-hold): nothing to restore"; fi


"""

def step_01_restore_and_verify_again(session):
    """Run Restore, and verify again at this checkpoint.

    RESTORE=1 runs the plan's restore for the drill: the variable put back as .fault-hold recorded it, which makes a new revision, then the traffic sent to the latest revision. It checks that the latest revision takes all the traffic, and removes .fault-hold. Then the plan's last step: the smoke, and remediate, which should read no_failure.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the plan's restore, as the drill recorded it).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/restore.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_restore_and_verify_again.
COMMANDS_02 = """make smoke-chat PROJECT=$PROJECT
make remediate PROJECT=$PROJECT SAVE=evals/reports/remediate_restored.json

"""

def step_02_restore_and_verify_again(session):
    """Run Restore, and verify again at this checkpoint.

    RESTORE=1 runs the plan's restore for the drill: the variable put back as .fault-hold recorded it, which makes a new revision, then the traffic sent to the latest revision. It checks that the latest revision takes all the traffic, and removes .fault-hold. Then the plan's last step: the smoke, and remediate, which should read no_failure.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the plan's verify again).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/smoke_restored.txt]

    [awaiting the author's run: data/plan_restored.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_restore_and_verify_again),
        ('source_21', step_02_restore_and_verify_again),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=True, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
