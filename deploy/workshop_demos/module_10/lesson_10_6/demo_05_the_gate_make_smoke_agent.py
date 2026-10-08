"""Lesson 10.6: The gate: make smoke-agent

Do it

Run order inside this file:
1. Do it (source window 14)

Prerequisites: demo_04_the_card_refused_without_a_token_read_with_one.
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


# Original CLI workflow for step_01_the_gate_make_smoke_agent.
COMMANDS_01 = """make smoke-agent PROJECT="$PROJECT" REGION="$REGION"   # the module's A2A gate: five checks

"""

def step_01_the_gate_make_smoke_agent(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the module's A2A gate).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DocuMind A2A peer - live smoke test
      target: https://documind-agent-NUMBER.asia-south1.run.app
      --------------------------------------------------------
      question: After how many years of continuous service does gratuity become payable?
      expected answer pattern: \\b(?:five|5)(?:\\s*\\(\\s*(?:five|5)\\s*\\))?[\\s-]+years?\\b
      [PASS] card refused without a token  status=403
      [PASS] agent card  name=documind_peer url=https://documind-agent-NUMBER.asia-south1.run.app skills=['documind_peer']
      [PASS] task answered  state=completed  'Gratuity is payable after not less than five years of continuous service [1]. Source: paym'
      [PASS] zeta refused by the roster  'The DocuMind server refused this: doc
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_14', step_01_the_gate_make_smoke_agent),
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
