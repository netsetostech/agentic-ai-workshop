"""Lesson 5.3: Deploy, and read it back

Only if the build stopped at storage.objects.get (the page's box): once, as a project owner, grant the project's default build account read access to its source in the PROJECT_cloudbuild bucket, push access to the documind repository and log writing. Then run the build and deploy again.

Run order inside this file:
1. Do it: build and deploy (source window 13)

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


# Original CLI workflow for step_01_build_and_deploy.
COMMANDS_01 = """BUILD_SA="$NUMBER-compute@developer.gserviceaccount.com"   # the account the 403 names
gcloud storage buckets add-iam-policy-binding "gs://${PROJECT}_cloudbuild" \\
  --member="serviceAccount:$BUILD_SA" --role=roles/storage.objectViewer --format=none
gcloud artifacts repositories add-iam-policy-binding documind --location="$REGION" --project="$PROJECT" \\
  --member="serviceAccount:$BUILD_SA" --role=roles/artifactregistry.writer --format=none
gcloud projects add-iam-policy-binding "$PROJECT" \\
  --member="serviceAccount:$BUILD_SA" --role=roles/logging.logWriter --condition=None --format=none

"""

def step_01_build_and_deploy(session):
    """Run Do it: build and deploy at this checkpoint.

    Cloud Build runs a build as the project's default build account, and the kit names no other: cloudbuild.yaml has no serviceAccount, and make build passes no --service-account. On a project made since mid-2024 that account is the Compute Engine default account, NUMBER-compute@developer.gserviceaccount.com. In an organization created on or after 3 May 2024 it is created without the Editor role Google used to give it. The build then cannot read its own source, the archive gcloud builds submit has just uploaded to the documind-ai-YOUR-ID_cloudbuild bucket, and stops at could not resolve source with a 403 naming that account. This grants that account the three things this build does, once, as a project owner: read its source in that one bucket, push the image to the documind repository, and write its log lines (cloudbuild.yaml logs to Cloud Logging only). It does not grant Editor or roles/cloudbuild.builds.builder. Granted on the project, either one can read, write and delete every object in every bucket, the uploads bucket of customer documents included, and the Compute Engine default account is also what a VM or a Cloud Run service runs as when nobody names another.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, once, as a project owner, only if the build stopped at storage.objects.get.
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
        ('source_13', step_01_build_and_deploy),
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
