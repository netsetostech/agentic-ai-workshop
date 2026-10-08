"""Lesson 5.2: Invoke: retrieve from a local client

At lesson end: Do it: stop the server

Run order inside this file:
1. Do it: stop the server (source window 19)

Prerequisites: workshop setup; see this lesson README.
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


def step_01_stop_the_server(session):
    """Run Do it: stop the server at this checkpoint.

    Do it: stop the server

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (stop the server, read what it logged).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: mcp_call retrieve  tenant acme  caller documind-ui-sa  via iam  {'answerable': True, 'citations': 5, 'error': None}
    """
    owned = session.state.get("local_service")
    session.stop_local_service()
    if owned:
        import json
        for line in open(owned["log"], encoding="utf-8"):
            if line.startswith('{"event": "mcp_call"'):
                e = json.loads(line)
                rest = {k: v for k, v in e.items() if k not in ("event", "tool", "tenant", "caller", "via", "query_sha")}
                print(f"  mcp_call {e['tool']}  tenant {e['tenant']}  caller {e['caller'].split('@')[0]}  via {e['via']}  {rest}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_stop_the_server),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=True, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
