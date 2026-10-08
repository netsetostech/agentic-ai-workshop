"""Lesson 0.4: REST: /health, /ready and /version by hand

The three GETs the smoke and the restore both use, and what each one can and cannot prove. Call them yourself, with the setup block's token, then call /health once more with no token at all:

Run order inside this file:
1. REST: /health, /ready and /version by hand (source window 33)

Prerequisites: demo_06_break_it_once_a_tenant_nobody_lists.
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


# Original CLI workflow for step_01_rest_health_ready_and_version_by_hand.
COMMANDS_01 = """for p in health ready version; do echo "GET /$p"; curl -s -w '\\nHTTP %{http_code}\\n' "$API/$p" -H "Authorization: Bearer $(tok "$API")"; done
curl -s -o /dev/null -w 'GET /health with no token: HTTP %{http_code}\\n' "$API/health"

"""

def step_01_rest_health_ready_and_version_by_hand(session):
    """Run REST: /health, /ready and /version by hand at this checkpoint.

    The three GETs the smoke and the restore both use, and what each one can and cannot prove. Call them yourself, with the setup block's token, then call /health once more with no token at all:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (four GETs; tok is the setup block's function).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rest_reads.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_33', step_01_rest_health_ready_and_version_by_hand),
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
