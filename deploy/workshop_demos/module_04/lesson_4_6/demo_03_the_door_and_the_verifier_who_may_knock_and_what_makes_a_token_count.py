"""Lesson 4.6: The door and the verifier: who may knock, and what makes a token count

Do it: the API's audiences, and who may invoke it The cell mints two tokens for the API as documind-ui-sa: one the way tok does, and one without --include-email. It reads their claims without verifying them; the API does the verifying. Nothing is sent.

Run order inside this file:
1. Do it: the API's audiences, and who may invoke it (source window 10)
2. Do it: what your token says about itself (source window 12)

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


def step_01_the_api_s_audiences_and_who_may_invoke_it(session):
    """Run Do it: the API's audiences, and who may invoke it at this checkpoint.

    Do it: the API's audiences, and who may invoke it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the API's two audiences and who may invoke it; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: IAP_AUDIENCE  /projects/NUMBER/locations/asia-south1/services/documind-ui
                  /projects/NUMBER/locations/asia-south1/services/documind-chat
    SELF_URL      https://documind-api-NUMBER.asia-south1.run.app
    run.invoker   serviceAccount:documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
                  serviceAccount:documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
                  serviceAccount:documind-outsider-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
                  serviceAccount:documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    """
    import json, os, subprocess
    def gcloud(*a):
        """Run this cell's gcloud command with its project/region context and decode the requested output.
        
        Example: gcloud('run', 'services', 'get-iam-policy', 'documind-api')
        """
        cmd = ["gcloud", *a, "--region", os.environ["REGION"], "--project", os.environ["PROJECT"], "--format=json"]
        return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    env = {e["name"]: e.get("value", "") for e in gcloud("run", "services", "describe", "documind-api")["spec"]["template"]["spec"]["containers"][0].get("env", [])}
    for k in ("IAP_AUDIENCE", "SELF_URL"):
        print(f"{k:13}", "\n              ".join(env.get(k, "(unset)").split(",")))
    for b in gcloud("run", "services", "get-iam-policy", "documind-api").get("bindings", []):
        if b["role"] == "roles/run.invoker":
            print("run.invoker  ", "\n              ".join(sorted(b["members"])))

# Original CLI workflow for step_02_what_your_token_says_about_itself.
COMMANDS_02 = """TOKEN="$(tok "$API")" BARE="$(gcloud auth print-identity-token --audiences="$API" \\
  --impersonate-service-account="documind-ui-sa@$PROJECT.iam.gserviceaccount.com")" python - <<'PY'
import base64, json, os, time
for name in ("TOKEN", "BARE"):
    part = os.environ[name].split(".")[1]
    c = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))      # read, not verified: the API verifies
    print(f"{name}: aud {c.get('aud')}")
    print(f"       email {c.get('email', '(none)')}, email_verified {c.get('email_verified', '(none)')}, "
          f"iss {c.get('iss')}, {int((c['exp'] - time.time()) / 60)} minutes left")
PY

"""

def step_02_what_your_token_says_about_itself(session):
    """Run Do it: what your token says about itself at this checkpoint.

    The cell mints two tokens for the API as documind-ui-sa: one the way tok does, and one without --include-email. It reads their claims without verifying them; the API does the verifying. Nothing is sent.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two tokens for the API, one with the email and one without; decoded, not sent).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: TOKEN: aud https://documind-api-NUMBER.asia-south1.run.app
           email documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com, email_verified True, iss https://accounts.google.com, 59 minutes left
    BARE: aud https://documind-api-NUMBER.asia-south1.run.app
           email (none), email_verified (none), iss https://accounts.google.com, 59 minutes left
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_the_api_s_audiences_and_who_may_invoke_it),
        ('source_12', step_02_what_your_token_says_about_itself),
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
