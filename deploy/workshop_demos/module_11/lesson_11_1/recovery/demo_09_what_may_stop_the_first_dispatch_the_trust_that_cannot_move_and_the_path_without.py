"""Lesson 11.1: What may stop the first dispatch, the trust that cannot move, and the path without GitHub

The workflow's two release steps are make targets, and you can run them from the operator shell as yourself: the same image built by Cloud Build, the same revision with no traffic and the tag candidate. It proves the build and the deploy, not the keyless identity, because your own sign-in makes both calls. It also moves the candidate tag to the revision it makes, so run it only if step 6 could not run.

Run order inside this file:
1. Without GitHub: the local operator path (source window 44)

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


# Original CLI workflow for step_01_without_github_the_local_operator_path.
COMMANDS_01 = """export GIT_SHA="$(git rev-parse HEAD)"     # the kit commit your checkout holds
make build PROJECT="$PROJECT" REGION="$REGION" SERVICES=api GIT_SHA="$GIT_SHA"
make release-candidate PROJECT="$PROJECT" REGION="$REGION" GIT_SHA="$GIT_SHA"

"""

def step_01_without_github_the_local_operator_path(session):
    """Run Without GitHub: the local operator path at this checkpoint.

    The workflow's two release steps are make targets, and you can run them from the operator shell as yourself: the same image built by Cloud Build, the same revision with no traffic and the tag candidate. It proves the build and the deploy, not the keyless identity, because your own sign-in makes both calls. It also moves the candidate tag to the revision it makes, so run it only if step 6 could not run.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, only if you could not dispatch (a build, and a candidate as you).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/api:COMMIT from services/rag-api
    ...
    gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --image asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/api:COMMIT --no-traffic --tag candidate --update-env-vars GIT_SHA=COMMIT --quiet
    ...
    >> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
    >> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app  (make eval-live API=that, then make promote)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_44', step_01_without_github_the_local_operator_path),
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
