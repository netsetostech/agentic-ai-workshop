"""Lesson 10.8: Poisoned tools, on your machine: the pins

Optional, the author's shell: the kit's peer on your machine against the poisoned server, in three tabs, with TOOL_PINS off and then on. The pin checks before it prove the same refusal without a model call.

Run order inside this file:
1. Do it: the peer against the poisoned server (source window 75)

Prerequisites: demo_10_poisoned_tools_on_your_machine_the_pins.
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


# Original CLI workflow for step_01_the_peer_against_the_poisoned_server.
COMMANDS_01 = """cd services/agent
MCP_URL=http://127.0.0.1:8900 MCP_AUTH=none SELF_URL= PORT=8080 TOOL_PINS=off \\
  GOOGLE_CLOUD_PROJECT="$PROJECT" GOOGLE_GENAI_USE_VERTEXAI=1 GOOGLE_CLOUD_LOCATION=global "$PY" agent.py
# a third tab: one inventory question to the local peer, as the runner would send it
curl -s -X POST http://127.0.0.1:8080/ -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"message": {"role": "user", "kind": "message", "messageId": "pins-1", "parts": [{"kind": "text", "text": "Which documents are in the corpus?"}]}}}'
# then Ctrl-C the peer and start it again with TOOL_PINS=on, and once more against make evil-mcp RUG=1

"""

def step_01_the_peer_against_the_poisoned_server(session):
    """Run Do it: the peer against the poisoned server at this checkpoint.

    The kit's own peer, on your machine, pointed at the fixture with MCP_AUTH=none, so no token is minted and no account impersonated; SELF_URL empty, so its card says localhost. Gemini answers, through your own credentials, so each task costs a few model calls. Ask one inventory question three times: pins off against the default shape, pins on against the same, and pins on against RUG=1. With the pins off, summarise_inbox and its sentence are in the model's hands; with them on, the peer's log says tool_unpinned and the model never sees that tool; against the rug pull, the honest retrieve is the one dropped, because its fingerprint moved.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the author's shell (the kit's peer on your machine against the poisoned server: Gemini answers, so a few rupees).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/pins_peer.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_75', step_01_the_peer_against_the_poisoned_server),
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
