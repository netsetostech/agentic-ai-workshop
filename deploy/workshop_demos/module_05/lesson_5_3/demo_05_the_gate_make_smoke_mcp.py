"""Lesson 5.3: The gate: make smoke-mcp

Do it

Run order inside this file:
1. Do it (source window 16)

Prerequisites: demo_04_deploy_and_read_it_back.
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


# Original CLI workflow for step_01_the_gate_make_smoke_mcp.
COMMANDS_01 = """export MCP="https://documind-mcp-$NUMBER.$REGION.run.app" SINCE122="$(date -u +%FT%TZ)"
make smoke-mcp PROJECT="$PROJECT" REGION="$REGION"   # the module's gate: health, tools/list, retrieve, the outsider refused

"""

def step_01_the_gate_make_smoke_mcp(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the module's gate).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DocuMind MCP - live smoke test
      target: https://documind-mcp-NUMBER.asia-south1.run.app
      --------------------------------------------------------
      [PASS] health  {"status":"ok","profile":"gcp","self_url":"https://documind-mcp-NUMBER.asia-south1.run.app"}
      [PASS] tools/list  ['calculate_processing_cost', 'corpus_stats', 'list_documents', 'retrieve']
      [PASS] retrieve  answerable=True citations=5  'Five years of continuous service [1].'
      [PASS] outsider refused  documind-outsider-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is not on tenant 'acme''s roster
      --------------------------------------------------------
      4 passed, 0 failed
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_the_gate_make_smoke_mcp),
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
