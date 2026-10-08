"""Lesson 10.6: The card: refused without a token, read with one

Do it

Run order inside this file:
1. Do it (source window 12)

Prerequisites: demo_03_the_peer_s_permissions_as_the_kit_writes_them.
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


# Original CLI workflow for step_01_the_card_refused_without_a_token_read_with.
COMMANDS_01 = """export AGENT="https://documind-agent-$NUMBER.$REGION.run.app" SINCE123="$(date -u +%FT%TZ)"
curl -s -o /dev/null -w "the card without a token: HTTP %{http_code}\\n" "$AGENT/.well-known/agent-card.json"
curl -s -H "Authorization: Bearer $(tok "$AGENT")" "$AGENT/.well-known/agent-card.json" > /tmp/card123.json
python - <<'PY'
import json
card = json.load(open("/tmp/card123.json"))
iface = (card.get("supportedInterfaces") or [{}])[0]
print(f"the card with a token: {card['name']}, version {card['version']}")
print(f"  answers at {iface.get('url')} over {iface.get('protocolBinding')}, A2A {iface.get('protocolVersion')}")
print(f"  streaming {card['capabilities'].get('streaming')}, input {card['defaultInputModes']}, output {card['defaultOutputModes']}")
print("  skills:", ", ".join(s["name"] for s in card["skills"]))
PY

"""

def step_01_the_card_refused_without_a_token_read_with(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the card, without a token and with one).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the card without a token: HTTP 403
    the card with a token: documind_peer, version 0.0.1
      answers at https://documind-agent-NUMBER.asia-south1.run.app over JSONRPC, A2A 1.0
      streaming False, input ['text/plain'], output ['text/plain']
      skills: model
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_12', step_01_the_card_refused_without_a_token_read_with),
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
