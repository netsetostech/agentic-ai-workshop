"""Lesson 10.7: The far side: the peer stops a task at 12 model calls

Do it: the cap, published Do it: trip the cap on your lane

Run order inside this file:
1. Do it: the cap, published (source window 21)
2. Do it: trip the cap on your lane (source window 24)

Prerequisites: demo_04_the_hand_off_in_the_kit_what_crosses_and_the_gate_in_front_of_it.
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


# Original CLI workflow for step_01_the_cap_published.
COMMANDS_01 = """curl -s -H "Authorization: Bearer $(tok "$AGENT")" "$AGENT/health"; echo

"""

def step_01_the_cap_published(session):
    """Run Do it: the cap, published at this checkpoint.

    Do it: the cap, published

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the peer's /health).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"status":"ok","mcp_url":"https://documind-mcp-NUMBER.asia-south1.run.app","self_url":"https://documind-agent-NUMBER.asia-south1.run.app","model":"gemini-3.6-flash","max_llm_calls":12,"peer_chain":"off","tool_pins":"off","agent_fence":false,"kit_import":false}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_trip_the_cap_on_your_lane.
COMMANDS_02 = """make agent-drill PROJECT="$PROJECT" REGION="$REGION"   # the peer capped at 1 for a minute or two, then 12 again

"""

def step_02_trip_the_cap_on_your_lane(session):
    """Run Do it: trip the cap on your lane at this checkpoint.

    Do it: trip the cap on your lane

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the cap tripped, then put back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/agent_drill.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_the_cap_published),
        ('source_24', step_02_trip_the_cap_on_your_lane),
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
