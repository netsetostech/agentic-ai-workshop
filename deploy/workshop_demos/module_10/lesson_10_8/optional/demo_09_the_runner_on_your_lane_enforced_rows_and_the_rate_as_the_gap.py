"""Lesson 10.8: The runner on your lane: enforced rows, and the rate as the gap

Optional, the author's shell: three tabs at once - the kit's MCP server in the local profile, the kit's peer against it on your own Gemini credentials, and the attack runner's peer row - so it does not run as one script. The page's recorded row shows what it does.

Run order inside this file:
1. The peer row, at a local peer (source window 53)

Prerequisites: demo_09_the_runner_on_your_lane_enforced_rows_and_the_rate_as_the_gap.
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


# Original CLI workflow for step_01_the_peer_row_at_a_local_peer.
COMMANDS_01 = """python3 -m venv ~/mcp-venv           # once: the MCP server's pins and the local store's
~/mcp-venv/bin/pip install -q -r services/mcp/requirements.txt \\
  $(grep -E '^(langchain-chroma|chromadb)==' services/chat/requirements-local.txt)
make mcp-local PY=~/mcp-venv/bin/python     # a second tab: acme's corpus, then the server on 127.0.0.1:8000
# a third tab: the kit's peer against it, in step 10's venv, Gemini through your own credentials
cd services/agent && MCP_URL=http://127.0.0.1:8000 MCP_AUTH=none SELF_URL= PORT=8080 \\
  GOOGLE_CLOUD_PROJECT="$PROJECT" GOOGLE_GENAI_USE_VERTEXAI=1 GOOGLE_CLOUD_LOCATION=global ~/pins-venv/bin/python agent.py
# back in the first tab: the peer's row, with no token and no gcloud
make attack-agents SURFACES=peer REPORT=evals/reports/attacks108_peer.json LABEL="the local peer"

"""

def step_01_the_peer_row_at_a_local_peer(session):
    """Run The peer row, at a local peer at this checkpoint.

    The peer row, at a local peer

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the author's shell (the MCP server in the local profile, the kit's peer beside it, then the peer's row: RUN_LIST.md).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/attack_peer.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_53', step_01_the_peer_row_at_a_local_peer),
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
