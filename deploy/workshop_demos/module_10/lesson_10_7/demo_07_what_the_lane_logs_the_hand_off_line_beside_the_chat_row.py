"""Lesson 10.7: What the lane logs: the hand-off line beside the chat row

Do it Then switch the hand-off off

Run order inside this file:
1. Do it (source window 31)
2. Then switch the hand-off off (source window 33)

Prerequisites: demo_06_the_hand_off_over_rest_the_response_the_smoke_and_the_confused_deputy.
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


# Original CLI workflow for step_01_what_the_lane_logs_the_hand_off_line_besid.
COMMANDS_01 = """sleep 20   # Cloud Logging needs a moment to show the lines
python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
def rows(flt):
    \"\"\"documind-chat's log lines since SINCE107 that match flt, oldest first, as their jsonPayload.\"\"\"
    f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND {flt} '
         f'AND timestamp>="{os.environ["SINCE107"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc",
                          "--limit", "50", "--format", "json"], capture_output=True, text=True, check=True).stdout
    return [e["jsonPayload"] for e in json.loads(out or "[]")]
print("the hand-off lines:")
for j in rows('jsonPayload.event="handoff"'):
    print(f"  {j['outcome']:9} n {j['n']}  tenant {j['tenant']}  rosters {j['peer_rosters']}  {j['seconds']} s of "
          f"{j['budget_s']}  the question: {j['request_chars']} characters  id {(j['handoff_id'] or '')[:8]}")
print("the ADK brain's chat rows:")
for j in rows('jsonPayload.event="chat" AND jsonPayload.brain="adk"'):
    print(f"  tools {j['tool_calls']}  refusals {j['refusals']}  model calls {j['model_calls']}  "
          f"handoffs key: {'handoffs' in j}")
PY

"""

def step_01_what_the_lane_logs_the_hand_off_line_besid(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the hand-off lines and the chat rows since step 3).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/logs.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_then_switch_the_hand_off_off.
COMMANDS_02 = """make handoff OFF=1 PROJECT="$PROJECT" REGION="$REGION"

"""

def step_02_then_switch_the_hand_off_off(session):
    """Run Then switch the hand-off off at this checkpoint.

    Then switch the hand-off off

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the hand-off off again).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> documind-chat: the hand-off is off (PEER_URL and PEER_ACCOUNT removed); every brain answers alone
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_what_the_lane_logs_the_hand_off_line_besid),
        ('source_33', step_02_then_switch_the_hand_off_off),
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
