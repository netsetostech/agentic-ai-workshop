"""Lesson 10.7: The hand-off over REST: the response, the smoke, and the confused deputy

Do it: the smoke Do it: a confused deputy

Run order inside this file:
1. Do it: the smoke (source window 26)
2. Do it: a confused deputy (source window 28)

Prerequisites: demo_05_the_far_side_the_peer_stops_a_task_at_12_model_calls.
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


# Original CLI workflow for step_01_the_smoke.
COMMANDS_01 = """make smoke-handoff PROJECT="$PROJECT" REGION="$REGION"

"""

def step_01_the_smoke(session):
    """Run Do it: the smoke at this checkpoint.

    Do it: the smoke

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the hand-off's smoke: two turns).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/smoke_handoff.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_confused_deputy.
COMMANDS_02 = """gcloud run services update documind-chat --region="$REGION" --project="$PROJECT" --quiet \\
  --update-env-vars="PEER_ACCOUNT=documind-ui-sa@$PROJECT.iam.gserviceaccount.com" >/dev/null 2>&1 \\
  && echo ">> documind-chat: PEER_ACCOUNT=documind-ui-sa, on three rosters, for this cell" \\
  || echo "ERROR: the env update failed; the turn below would run with PEER_ACCOUNT unchanged"
CHAT_TOKEN="$(tok "$CHAT")" python - <<'PY'
import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
body = {"question": "Ask DocuMind's A2A peer which documents the corpus holds, and how many there are.",
        "session_id": "lesson107-deputy", "brain": "adk"}
req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", data=json.dumps(body).encode(),
                             headers={"Authorization": "Bearer " + os.environ["CHAT_TOKEN"], "Content-Type": "application/json"})
r = json.load(urllib.request.urlopen(req, timeout=180))
print("tool_calls:", r.get("tool_calls"), " refusals:", r.get("refusals"))
for h in r.get("handoffs", []):
    print(f"hand-off {h['n']}: {h['outcome']}, budget {h['budget_s']}, the peer's task {h['state']}")
    print(f"  {h['reason']}")
print("answer:", str(r.get("answer"))[:160])
PY
make handoff PROJECT="$PROJECT" REGION="$REGION"   # PEER_ACCOUNT back to the account documind-agent runs as

"""

def step_02_a_confused_deputy(session):
    """Run Do it: a confused deputy at this checkpoint.

    Do it: a confused deputy

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the confused deputy, refused before anything is sent).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/deputy.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_the_smoke),
        ('source_28', step_02_a_confused_deputy),
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
