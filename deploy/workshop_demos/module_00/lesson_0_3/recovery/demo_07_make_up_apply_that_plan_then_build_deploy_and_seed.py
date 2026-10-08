"""Lesson 0.3: make up: apply that plan, then build, deploy and seed

Now run it. It takes a long time: Cloud SQL, the GKE cluster and the deployed index each take minutes to create, and the builds run one after another. Run it inside tmux if your shell has it, so that a closed browser tab or a dropped connection does not stop an apply halfway; an interrupted apply needs a new plan. time reports how long it took. A plan refused as stale (The saved plan is stale; create a new plan, or The selected plan is missing or changed): the state, the inputs or the file changed since make plan. Run step 6 again, read the new plan, then make up. An apply that failed halfway: keep the state as it is. Terraform has recorded everything it created, so the next make plan lists only what is still missing; read it, then make up. Never delete the state or terraform/.terraform to "start clean": the next apply would try to create everything again over resources that exist. A build that stops at storage.objects.get with a 403 naming the Compute Engine default account: Cloud Build runs as that account when the kit names none, and in an organization created on or after 3 May 2024 it is created without the broad role older projects gave it. Grant it exactly what a build needs (the block below), and wait a few minutes for IAM to apply the grants. The apply had already finished by then and its plan is used up, so run make plan (it reports no changes) and make up, which applies nothing and carries on from the build. A drift line after the apply means the plan after it is not empty: a resource the provider reads back differently from how it was written. It does not stop make up, but it is a definition to fix before the next apply repeats it. A bq-views failure naming a table or a field that does not exist: the view reads the log sink's table, and the kit's own comment 

Run order inside this file:
1. make up: apply that plan, then build, deploy and seed (source window 48)

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


# Original CLI workflow for step_01_make_up_apply_that_plan_then_build_deploy.
COMMANDS_01 = """BUILDER="serviceAccount:$NUMBER-compute@developer.gserviceaccount.com"   # the account the 403 named, if it named another
gcloud storage buckets add-iam-policy-binding "gs://${PROJECT}_cloudbuild" --member="$BUILDER" --role=roles/storage.objectViewer --format=none
gcloud artifacts repositories add-iam-policy-binding documind --location="$REGION" --project="$PROJECT" --member="$BUILDER" --role=roles/artifactregistry.writer --format=none
gcloud projects add-iam-policy-binding "$PROJECT" --member="$BUILDER" --role=roles/logging.logWriter --condition=None --format=none

"""

def step_01_make_up_apply_that_plan_then_build_deploy(session):
    """Run make up: apply that plan, then build, deploy and seed at this checkpoint.

    Now run it. It takes a long time: Cloud SQL, the GKE cluster and the deployed index each take minutes to create, and the builds run one after another. Run it inside tmux if your shell has it, so that a closed browser tab or a dropped connection does not stop an apply halfway; an interrupted apply needs a new plan. time reports how long it took. A plan refused as stale (The saved plan is stale; create a new plan, or The selected plan is missing or changed): the state, the inputs or the file changed since make plan. Run step 6 again, read the new plan, then make up. An apply that failed halfway: keep the state as it is. Terraform has recorded everything it created, so the next make plan lists only what is still missing; read it, then make up. Never delete the state or terraform/.terraform to "start clean": the next apply would try to create everything again over resources that exist. A build that stops at storage.objects.get with a 403 naming the Compute Engine default account: Cloud Build runs as that account when the kit names none, and in an organization created on or after 3 May 2024 it is created without the broad role older projects gave it. Grant it exactly what a build needs (the block below), and wait a few minutes for IAM to apply the grants. The apply had already finished by then and its plan is used up, so run make plan (it reports no changes) and make up, which applies nothing and carries on from the build. A drift line after the apply means the plan after it is not empty: a resource the provider reads back differently from how it was written. It does not stop make up, but it is a definition to fix before the next apply repeats it. A bq-views failure naming a table or a field that does not exist: the view reads the log sink's table, and the kit's own comment 

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, only if the build stopped on that 403.
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
        ('source_48', step_01_make_up_apply_that_plan_then_build_deploy),
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
