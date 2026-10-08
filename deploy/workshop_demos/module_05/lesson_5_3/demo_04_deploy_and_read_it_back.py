"""Lesson 5.3: Deploy, and read it back

Do it: build and deploy Do it: read it back

Run order inside this file:
1. Do it: build and deploy (source window 11)
2. Do it: read it back (source window 14)

Prerequisites: demo_03_the_door_as_the_kit_writes_it_down.
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
COMMANDS_01 = """make build deploy-services PROJECT="$PROJECT" REGION="$REGION" SERVICES=mcp SCRIPTS=commands/lesson-7.2.sh ADMIN_EMAILS="$ME"

"""

def step_01_build_and_deploy(session):
    """Run Do it: build and deploy at this checkpoint.

    Do it: build and deploy

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (build the image, deploy it, bind its callers).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/mcp:COMMIT from services/mcp
    Creating temporary archive of ... file(s) totalling ... MiB before compression.
    ...
    DONE ... asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/mcp:COMMIT
    >> commands/lesson-7.2.sh (DEPLOY block)
    Deploying container to Cloud Run service [documind-mcp] in project [documind-ai-YOUR-ID] region [asia-south1]
    ...
    Service URL: https://documind-mcp-NUMBER.asia-south1.run.app
    Updated IAM policy for service [documind-mcp].   (three times: ui, agent, outsider)
    ...
    >> you@example.com may mint tokens as documind-ui-sa
    >> you@example.com may mint tokens as documind-outsider-sa
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_read_it_back(session):
    """Run Do it: read it back at this checkpoint.

    Do it: read it back

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the service as deployed, against the script).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: serving     documind-mcp-00004-k7w at https://documind-mcp-NUMBER.asia-south1.run.app
      runs as     documind-mcp-sa
      ingress     all
      SELF_URL    https://documind-mcp-NUMBER.asia-south1.run.app
      invokers    documind-agent-sa, documind-outsider-sa, documind-ui-sa
      the script  documind-agent-sa, documind-outsider-sa, documind-ui-sa - the same
    """
    import json, os, subprocess
    def gc(*a):
        """Run the requested gcloud inspection and return its decoded JSON for this section.
        
        Example: gc('describe')
        """
        return json.loads(subprocess.run(["gcloud", "run", "services", *a, "documind-mcp", "--region", os.environ["REGION"],
                                          "--project", os.environ["PROJECT"], "--format", "json"], capture_output=True, text=True, check=True).stdout)
    svc, policy = gc("describe"), gc("get-iam-policy")
    spec, meta = svc["spec"]["template"]["spec"], svc["spec"]["template"]["metadata"]
    env = {e["name"]: e.get("value") for e in spec["containers"][0].get("env", [])}
    print(f"  serving     {svc['status']['latestReadyRevisionName']} at {svc['status']['url']}")
    print(f"  runs as     {spec['serviceAccountName'].split('@')[0]}")
    print(f"  ingress     {svc['metadata']['annotations'].get('run.googleapis.com/ingress')}")
    print(f"  SELF_URL    {env.get('SELF_URL')}")
    invokers = sorted(m.split(":", 1)[1].split("@")[0] for b in policy.get("bindings", []) if b["role"] == "roles/run.invoker" for m in b["members"])
    print(f"  invokers    {', '.join(invokers)}")
    print(f"  the script  {', '.join(sorted(['documind-agent-sa', 'documind-outsider-sa', 'documind-ui-sa']))} - "
          + ("the same" if invokers == sorted(["documind-agent-sa", "documind-outsider-sa", "documind-ui-sa"]) else "DIFFERENT: someone bound more, or less"))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_build_and_deploy),
        ('source_14', step_02_read_it_back),
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
