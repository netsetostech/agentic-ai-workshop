"""Lesson 5.5: Access failures at the chat service's door

Do it

Run order inside this file:
1. Do it (source window 26)

Prerequisites: demo_04_a_turn_that_will_not_stop_the_call_cap_the_rupees_and_the_deadline.
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


# Original CLI workflow for step_01_access_failures_at_the_chat_service_s_door.
COMMANDS_01 = """export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"
chatas() {   # one /v1/chat turn with the token in $1: the status, then the start of the body
  code=$(curl -s -o /tmp/chat103.json -w "%{http_code}" -X POST "$CHAT/v1/chat" -H "Authorization: Bearer $1" \\
    -H "Content-Type: application/json" -d '{"question": "After how many years of continuous service does gratuity become payable?", "session_id": "lesson103"}')
  echo "  $code  $(head -c 100 /tmp/chat103.json)"
}
chatas "$(gcloud auth print-identity-token --include-email --audiences="$CHAT" \\
    --impersonate-service-account="documind-outsider-sa@$PROJECT.iam.gserviceaccount.com" 2>/dev/null)"   # admitted by IAM, on no roster
chatas "$(gcloud auth print-identity-token --audiences="$CHAT" \\
    --impersonate-service-account="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" 2>/dev/null)"          # no --include-email
chatas "$(tok "$CHAT")"                                                                                  # a roster member

"""

def step_01_access_failures_at_the_chat_service_s_door(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (three identities at the chat service's door).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 403  {"detail":"not a member of any tenant"}
      401  {"detail":"the bearer token carries no verified email"}
      200  {"answer":"Gratuity becomes payable after not less than five years of continuous service [1].","tool
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_access_failures_at_the_chat_service_s_door),
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
