"""Lesson 11.8: Your lane, read with the two tokens

Three GETs and one describe, as you. The last line greps documind-ui's description for its IAP annotation; step 9 says why it is greped rather than named. Every offline line again, and a lane: line under components 1, 2, 4 and 8. Reads only; Rs 0.

Run order inside this file:
1. Do it: the reads by hand (source window 30)
2. Do it: the check with your lane (source window 32)

Prerequisites: demo_06_change_it_one_command_deleted_one_component_fails.
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


# Original CLI workflow for step_01_the_reads_by_hand.
COMMANDS_01 = """curl -s -o /dev/null -w "GET /version as documind-ui-sa: %{http_code}\\n" "$API/version" -H "Authorization: Bearer $(tok "$API")"
curl -s "$API/version" -H "Authorization: Bearer $(tok "$API")"; echo
curl -s -o /dev/null -w "GET /v1/sources?tenant_id=$TENANT as documind-outsider-sa: %{http_code}\\n" \\
  "$API/v1/sources?tenant_id=$TENANT" -H "Authorization: Bearer $(otok)"
gcloud run services describe documind-ui --region "$REGION" --project "$PROJECT" --format=json | grep -i iap || echo "no iap annotation: see step 9"

"""

def step_01_the_reads_by_hand(session):
    """Run Do it: the reads by hand at this checkpoint.

    Three GETs and one describe, as you. The last line greps documind-ui's description for its IAP annotation; step 9 says why it is greped rather than named.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (three GETs with the two tokens, one describe; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rest_reads.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_check_with_your_lane.
COMMANDS_02 = """make capstone-check PROJECT="$PROJECT" REGION="$REGION" 2>&1 | tee /tmp/capstone-check.out && status=0 || status=$?
grep -qE '^>> (complete|incomplete): ' /tmp/capstone-check.out   # the check gave its verdict
[ "$status" -eq 0 ] || grep -q 'capstone-check\\] Error 1$' /tmp/capstone-check.out   # Error 1: incomplete, work on the fork


"""

def step_02_the_check_with_your_lane(session):
    """Run Do it: the check with your lane at this checkpoint.

    Every offline line again, and a lane: line under components 1, 2, 4 and 8. Reads only; Rs 0.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in your fork (gcloud reads from an allow-list of 11, two tokens, three GETs; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/capstone_live.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_30', step_01_the_reads_by_hand),
        ('source_32', step_02_the_check_with_your_lane),
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
