"""Lesson 11.7: The two drills on your lane

documind-chat changes for a few minutes: two new revisions, four /health reads, and no model call. Most of its time is the chat's image build, about four minutes. No model call. Do it: the chat, on every brain

Run order inside this file:
1. Do it: pinned traffic, on your lane (source window 30)
2. Do it: a routine deploy drops a hotfix, on your lane (source window 33)
3. Do it: the chat, on every brain (source window 35)

Prerequisites: demo_06_your_two_services_as_cloud_run_s_api_returns_them.
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


# Original CLI workflow for step_01_pinned_traffic_on_your_lane.
COMMANDS_01 = """make gotcha-drill ID=pinned-traffic LIVE=1 PROJECT="$PROJECT" REGION="$REGION"

"""

def step_01_pinned_traffic_on_your_lane(session):
    """Run Do it: pinned traffic, on your lane at this checkpoint.

    documind-chat changes for a few minutes: two new revisions, four /health reads, and no model call.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (documind-chat for a few minutes; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/drill_pinned.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_routine_deploy_drops_a_hotfix_on_your_la.
COMMANDS_02 = """make gotcha-drill ID=deploy-drops-hotfix LIVE=1 PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"

"""

def step_02_a_routine_deploy_drops_a_hotfix_on_your_la(session):
    """Run Do it: a routine deploy drops a hotfix, on your lane at this checkpoint.

    Most of its time is the chat's image build, about four minutes. No model call.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (documind-chat: a routine deploy of the chat alone, about four minutes; Rs 0 in model calls).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/drill_deploy_drop.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_chat_on_every_brain.
COMMANDS_03 = """make smoke-chat PROJECT="$PROJECT" REGION="$REGION"

"""

def step_03_the_chat_on_every_brain(session):
    """Run Do it: the chat, on every brain at this checkpoint.

    Do it: the chat, on every brain

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (4 questions, one per brain, and the outsider refused; about Rs 5).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/smoke_chat.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_30', step_01_pinned_traffic_on_your_lane),
        ('source_33', step_02_a_routine_deploy_drops_a_hotfix_on_your_la),
        ('source_35', step_03_the_chat_on_every_brain),
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
