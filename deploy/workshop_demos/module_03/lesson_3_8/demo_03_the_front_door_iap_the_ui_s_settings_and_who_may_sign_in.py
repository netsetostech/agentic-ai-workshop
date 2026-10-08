"""Lesson 3.8: The front door: IAP, the UI's settings, and who may sign in

Do it: the service's account, IAP's flag, who may sign in, and a request without one

Run order inside this file:
1. Do it: the service's account, IAP's flag, who may sign in, and a request without one (source window 11)

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


# Original CLI workflow for step_01_the_service_s_account_iap_s_flag_who_may_s.
COMMANDS_01 = """set +e +o pipefail   # as the page runs it: every line is a read, and grep finding nothing is an answer
gcloud run services describe documind-ui --region "$REGION" --project "$PROJECT" --format='value(spec.template.spec.serviceAccountName)'
gcloud run services describe documind-ui --region "$REGION" --project "$PROJECT" --format=yaml | grep -i "iap-enabled"
gcloud iap web get-iam-policy --resource-type=cloud-run --service=documind-ui --region "$REGION" --project "$PROJECT" \\
  --flatten=bindings --format='value(bindings.role,bindings.members)'
curl -s -o /dev/null -w "without a sign-in: HTTP %{http_code} -> %{redirect_url}\\n" "$UI/"

"""

def step_01_the_service_s_account_iap_s_flag_who_may_s(session):
    """Run Do it: the service's account, IAP's flag, who may sign in, and a request without one at this checkpoint.

    Do it: the service's account, IAP's flag, who may sign in, and a request without one

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (four reads).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
        run.googleapis.com/iap-enabled: 'true'
    roles/iap.httpsResourceAccessor	user:you@example.com
    without a sign-in: HTTP 302 -> https://accounts.google.com/o/oauth2/v2/auth?client_id=...
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_the_service_s_account_iap_s_flag_who_may_s),
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
