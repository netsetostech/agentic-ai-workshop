"""Lesson 10.7: Switch the hand-off on, and ask the ADK brain

Do it

Run order inside this file:
1. Do it (source window 7)

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


# Original CLI workflow for step_01_switch_the_hand_off_on_and_ask_the_adk_bra.
COMMANDS_01 = """export SINCE107="$(date -u +%FT%TZ)" CHAT="https://documind-chat-$NUMBER.$REGION.run.app" AGENT="https://documind-agent-$NUMBER.$REGION.run.app"
make handoff PROJECT="$PROJECT" REGION="$REGION"

"""

def step_01_switch_the_hand_off_on_and_ask_the_adk_bra(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the hand-off on: one env update on documind-chat, no model call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> documind-chat: PEER_URL=https://documind-agent-NUMBER.asia-south1.run.app
    >> documind-chat: PEER_ACCOUNT=documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
       the ADK brain may hand a question to the peer; make smoke-handoff checks it, make handoff OFF=1 ends it
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_switch_the_hand_off_on_and_ask_the_adk_bra),
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
