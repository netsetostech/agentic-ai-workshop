"""Lesson 11.1: Grant the build account what a build needs

Only if the build stopped at storage.objects.get: 'could not resolve source' and a 403 naming the Compute Engine default account. The kit names no account for Cloud Build, so a build runs as the project's default build account, and in an organization created on or after 3 May 2024 that account is created without the Editor role. Run once, as a project owner: read access to its source in the PROJECT_cloudbuild bucket only, push access to the documind repository, and log writing. Not Editor or roles/cloudbuild.builds.builder: granted on the project, either one can read, write and delete every object in every bucket, the uploads bucket included. IAM applies a grant in about two minutes, sometimes seven or more; then run the build again.

Run order inside this file:
1. Grant the build account what a build needs (source window plan-3)

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


def step_01_grant_the_build_account_what_a_build_needs(session):
    """Run Grant the build account what a build needs at this checkpoint.

    Only if the build stopped at storage.objects.get: 'could not resolve source' and a 403 naming the Compute Engine default account. The kit names no account for Cloud Build, so a build runs as the project's default build account, and in an organization created on or after 3 May 2024 that account is created without the Editor role. Run once, as a project owner: read access to its source in the PROJECT_cloudbuild bucket only, push access to the documind repository, and log writing. Not Editor or roles/cloudbuild.builds.builder: granted on the project, either one can read, write and delete every object in every bucket, the uploads bucket included. IAM applies a grant in about two minutes, sometimes seven or more; then run the build again.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: Course-plan experiment — live deployment.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Three bindings added for the account the 403 named; the next build reads its source.
    """
    import os
    p, r = session.config.project, session.config.cloud_run_region
    member = "serviceAccount:" + os.environ["NUMBER"] + "-compute@developer.gserviceaccount.com"   # the account the 403 names; use yours if it names another
    session.command(["gcloud", "storage", "buckets", "add-iam-policy-binding", "gs://" + p + "_cloudbuild",
                     "--member=" + member, "--role=roles/storage.objectViewer", "--format=none"])
    session.command(["gcloud", "artifacts", "repositories", "add-iam-policy-binding", "documind", "--location=" + r,
                     "--project=" + p, "--member=" + member, "--role=roles/artifactregistry.writer", "--format=none"])
    session.command(["gcloud", "projects", "add-iam-policy-binding", p, "--member=" + member,
                     "--role=roles/logging.logWriter", "--condition=None", "--format=none"])
    print("Granted. IAM applies a grant in about two minutes, sometimes seven or more; then run the build again.")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_recover_03_grant_the_build_account_what_a_build_needs', step_01_grant_the_build_account_what_a_build_needs),
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
