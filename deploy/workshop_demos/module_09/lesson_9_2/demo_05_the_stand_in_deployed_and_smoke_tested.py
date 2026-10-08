"""Lesson 9.2: The stand-in, deployed and smoke-tested

Do it

Run order inside this file:
1. Do it (source window 17)
2. Do it (source window 19)

Prerequisites: demo_04_the_waits_and_the_bill_from_the_kit.
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


# Original CLI workflow for step_01_the_stand_in_deployed_and_smoke_tested.
COMMANDS_01 = """make deploy-slm PROJECT="$PROJECT" SLM_STOCK=gemma3:4b      # the first build pulls 3.3 GB into the image: minutes

"""

def step_01_the_stand_in_deployed_and_smoke_tested(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a GPU service: it bills while an instance lives).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> stand-in: gemma3:4b will be served as documind-slm
    gcloud run deploy documind-slm \\
      --source services/slm --region us-central1 --project documind-ai-YOUR-ID \\
      --gpu 1 --gpu-type nvidia-l4 --no-gpu-zonal-redundancy \\
      --cpu 8 --memory 32Gi \\
      --max-instances 1 --min-instances 0 --timeout 600 --concurrency 4 \\
      --no-allow-unauthenticated --labels slm-source=stock \\
      --startup-probe httpGet.path=/api/tags,httpGet.port=8080,initialDelaySeconds=10,periodSeconds=5,failureThreshold=30 --quiet
    ...
    >> slm: https://documind-slm-NUMBER.us-central1.run.app (min-instances 0; make slm-off after every session anyway)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_stand_in_deployed_and_smoke_tested.
COMMANDS_02 = """make smoke-slm PROJECT="$PROJECT"

"""

def step_02_the_stand_in_deployed_and_smoke_tested(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, right after the deploy.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DocuMind SLM - live smoke test
      target: https://documind-slm-NUMBER.us-central1.run.app
      --------------------------------------------------------
      [PASS] /api/tags lists documind-slm  HTTP 200 in 0.1s (cold start included): ['documind-slm:latest']
      [PASS] /api/generate answers  'OK' in 12.0s
      [PASS] /v1/chat/completions answers (the OpenAI-compatible door)  'OK' in 0.6s
      [PASS] through the gateway's documind-slm route  HTTP 200, served by 'ollama_chat/documind-slm' in 0.6s
      [PASS] what the service serves  stock	us-central1-docker.pkg.dev/documind-ai-YOUR-ID/cloud-run-source-deploy/documind-slm@sha256:DIGEST
      --------------------------------------------------------
      5 passed, 0 faile
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_the_stand_in_deployed_and_smoke_tested),
        ('source_19', step_02_the_stand_in_deployed_and_smoke_tested),
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
