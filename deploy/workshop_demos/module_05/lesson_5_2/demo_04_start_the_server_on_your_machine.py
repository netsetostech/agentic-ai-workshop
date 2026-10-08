"""Lesson 5.2: Start the server on your machine

Do it

Run order inside this file:
1. Do it (source window 13)

Prerequisites: demo_03_expose_what_the_server_declares.
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


def step_01_start_the_server_on_your_machine(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's server on your machine, in the background).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"status":"ok","profile":"gcp","self_url":"http://localhost:8121"}
    """
    import os, sys
    session.set_environment(SELF_URL="http://localhost:8121", RAG_API_URL=os.environ["API"],
                            GOOGLE_CLOUD_PROJECT=session.config.project,
                            DOCUMIND_IMPERSONATE_SA=session.config.ui_service_account)
    session.start_local_service([sys.executable, "-m", "uvicorn", "services.mcp.server:app", "--port", "8121"],
                                "http://localhost:8121/health", expected_health={"status": "ok", "self_url": "http://localhost:8121"})
    print("Owned MCP server log:", session.state["local_service"]["log"])

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_start_the_server_on_your_machine),
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
