"""Lesson 9.1: The gateway, deployed and smoke-tested

Do it

Run order inside this file:
1. Do it (source window 17)
2. Do it (source window 19)

Prerequisites: demo_04_the_token_the_proxy_sends.
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


# Original CLI workflow for step_01_the_gateway_deployed_and_smoke_tested.
COMMANDS_01 = """make deploy-gateway PROJECT="$PROJECT"            # builds the image from services/litellm: the first build takes a while

"""

def step_01_the_gateway_deployed_and_smoke_tested(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit where make up ran (it reads the database URL from Terraform's state).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    >> gateway: https://documind-gateway-NUMBER.asia-south1.run.app (the API and the UI's account may call it)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_gateway_deployed_and_smoke_tested.
COMMANDS_02 = """make smoke-gateway PROJECT="$PROJECT"

"""

def step_02_the_gateway_deployed_and_smoke_tested(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DocuMind gateway - live smoke test
      target: https://documind-gateway-NUMBER.asia-south1.run.app
      --------------------------------------------------------
      [PASS] no token is refused at the door  HTTP 403
      [PASS] liveliness as the member's account  HTTP 200 in ...s
      [PASS] documind-general answers JSON  '{"ok": true}' in ...s, model gemini-3.6-flash
      [PASS] the cost header rag-api prices from  x-litellm-response-cost=3.45e-05
      [PASS] a PAN is routed by the guardrail  served by 'gemini-3.6-flash' in ...s (the sensitive route is the self-hosted model, no fallback)
      [PASS] documind-slm answers, or its fallback does  model 'gemini-3.6-flash' in ...s, cost 1.8e-05
      -----------------------
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_the_gateway_deployed_and_smoke_tested),
        ('source_19', step_02_the_gateway_deployed_and_smoke_tested),
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
