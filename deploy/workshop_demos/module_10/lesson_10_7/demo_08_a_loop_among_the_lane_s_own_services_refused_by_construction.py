"""Lesson 10.7: A loop among the lane's own services: refused by construction

Do it This loop in lesson-12.8.sh binds who may invoke documind-chat. Add documind-agent-sa to it, as an edit meant to let the peer ask the chat something would, then run the check, then put the file back.

Run order inside this file:
1. Do it (source window 38)
2. Change it: an edge back from the peer to the chat (source window 41)

Prerequisites: demo_07_what_the_lane_logs_the_hand_off_line_beside_the_chat_row.
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


# Original CLI workflow for step_01_a_loop_among_the_lane_s_own_services_refus.
COMMANDS_01 = """make check-callers GRAPH=1

"""

def step_01_a_loop_among_the_lane_s_own_services_refus(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the caller graph; offline, no gcloud).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python commands/check_callers.py --graph
    each service, the account it runs as, and the script that deploys it and binds its invokers:
      documind-api    documind-api-sa       lesson-12.2.sh
      documind-chat   documind-chat-sa      lesson-12.8.sh
      documind-mcp    documind-mcp-sa       lesson-7.2.sh
      documind-agent  documind-agent-sa     lesson-8.4.sh
      documind-ui     documind-ui-sa        lesson-12.4.sh
      documind-gchat  documind-gchat-sa     gchat.sh

    service -> service: the caller's account holds roles/run.invoker on the callee
      documind-chat -> documind-api
      documind-chat -> documind-agent
      documind-mcp -> documind-api
      documind-agent -> documind-mcp
      documind-ui -> documind-api
      do
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_change_it_an_edge_back_from_the_peer_to_th.
COMMANDS_02 = """sed -i 's/^for who in documind-ui-sa documind-outsider-sa/for who in documind-ui-sa documind-agent-sa documind-outsider-sa/' commands/lesson-12.8.sh
git diff -U0 commands/lesson-12.8.sh | grep '^[-+]for'
python commands/check_callers.py --graph && graph=0 || graph=$?; echo "exit $graph"
git checkout -q commands/lesson-12.8.sh && python commands/check_callers.py --graph | tail -2
[ "$graph" -ne 0 ]   # the edge back must be refused: the check names the cycle and exits 1


"""

def step_02_change_it_an_edge_back_from_the_peer_to_th(session):
    """Run Change it: an edge back from the peer to the chat at this checkpoint.

    This loop in lesson-12.8.sh binds who may invoke documind-chat. Add documind-agent-sa to it, as an edit meant to let the peer ask the chat something would, then run the check, then put the file back.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Change-it: an edge back from the peer to the chat, then the kit put back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: -for who in documind-ui-sa documind-outsider-sa \\
    +for who in documind-ui-sa documind-agent-sa documind-outsider-sa \\
    each service, the account it runs as, and the script that deploys it and binds its invokers:
      documind-api    documind-api-sa       lesson-12.2.sh
      documind-chat   documind-chat-sa      lesson-12.8.sh
      documind-mcp    documind-mcp-sa       lesson-7.2.sh
      documind-agent  documind-agent-sa     lesson-8.4.sh
      documind-ui     documind-ui-sa        lesson-12.4.sh
      documind-gchat  documind-gchat-sa     gchat.sh

    service -> service: the caller's account holds roles/run.invoker on the callee
      documind-chat -> documind-api
      documind-chat -> documind-agent
      documind-mcp -> doc
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_38', step_01_a_loop_among_the_lane_s_own_services_refus),
        ('source_41', step_02_change_it_an_edge_back_from_the_peer_to_th),
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
