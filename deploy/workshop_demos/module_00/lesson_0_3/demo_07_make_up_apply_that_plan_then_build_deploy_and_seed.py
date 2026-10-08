"""Lesson 0.3: make up: apply that plan, then build, deploy and seed

The deploy step is the reason the kit has no second copy of its deploy flags: it cuts the block between # ---- DEPLOY ---- and the next marker out of each script and runs it as it is, in the order the services must come up. The worker comes first, because the push subscription Terraform made already points at its address. Now run it. It takes a long time: Cloud SQL, the GKE cluster and the deployed index each take minutes to create, and the builds run one after another. Run it inside tmux if your shell has it, so that a closed browser tab or a dropped connection does not stop an apply halfway; an interrupted apply needs a new plan. time reports how long it took.

Run order inside this file:
1. make up: apply that plan, then build, deploy and seed (source window 45)

Prerequisites: demo_06_make_plan_a_saved_plan_checked_before_you_apply_it.
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


# Original CLI workflow for step_01_make_up_apply_that_plan_then_build_deploy.
COMMANDS_01 = """tmux new -s up        # optional: reattach with tmux attach -t up; the variables below are still exported inside it
time make up PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ADMIN_EMAILS" 2>&1 | tee "$HOME/up.log"
tail -n 25 "$HOME/up.log"

"""

def step_01_make_up_apply_that_plan_then_build_deploy(session):
    """Run make up: apply that plan, then build, deploy and seed at this checkpoint.

    The deploy step is the reason the kit has no second copy of its deploy flags: it cuts the block between # ---- DEPLOY ---- and the next marker out of each script and runs it as it is, in the order the services must come up. The worker comes first, because the push subscription Terraform made already points at its address. Now run it. It takes a long time: Cloud SQL, the GKE cluster and the deployed index each take minutes to create, and the builds run one after another. Run it inside tmux if your shell has it, so that a closed browser tab or a dropped connection does not stop an apply halfway; an interrupted apply needs a new plan. time reports how long it took.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
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
        ('source_45', step_01_make_up_apply_that_plan_then_build_deploy),
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
