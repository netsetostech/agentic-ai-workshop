"""Lesson 4.7: The kit's own tests of the same refusals

The smoke test's check 3b, and the chat service's check 4. The kit asserts these refusals itself, so a deploy that opened a door would fail its own smoke test. smoke/smoke.py sends its question again with no token and passes only on 401 or 403. smoke/smoke_chat.py asks the chat service as the outsider and passes only on a 403 from the roster, not a 401 from the verifier. The MCP server's smoke test does the same. The cell runs the API's smoke test and keeps two of its lines.

Run order inside this file:
1. The kit's own tests of the same refusals (source window 23)

Prerequisites: demo_06_the_policy_against_a_pin_a_tenant_kept_in_india_pinned_to_a_store_outside_it.
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


# Original CLI workflow for step_01_the_kit_s_own_tests_of_the_same_refusals.
COMMANDS_01 = """set +o pipefail   # as the page runs it: make smoke's own status does not stop this filtered read
DOCUMIND_API_URL="$API" DOCUMIND_PROJECT="$PROJECT" DOCUMIND_TENANT=acme make smoke | grep -E "no token|pass ·"

"""

def step_01_the_kit_s_own_tests_of_the_same_refusals(session):
    """Run The kit's own tests of the same refusals at this checkpoint.

    The smoke test's check 3b, and the chat service's check 4. The kit asserts these refusals itself, so a deploy that opened a door would fail its own smoke test. smoke/smoke.py sends its question again with no token and passes only on 401 or 403. smoke/smoke_chat.py asks the chat service as the outsider and passes only on a 403 from the roster, not a 401 from the verifier. The MCP server's smoke test does the same. The cell runs the API's smoke test and keeps two of its lines.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's smoke test, two of its lines).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [PASS] no token refused  status=403
      N pass · 0 fail
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_the_kit_s_own_tests_of_the_same_refusals),
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
