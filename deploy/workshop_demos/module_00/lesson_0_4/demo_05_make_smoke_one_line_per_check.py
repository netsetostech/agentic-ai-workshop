"""Lesson 0.4: make smoke: one line per check

No guard-project, and no variables passed: smoke.py reads everything from its environment. These are the names it reads, and what it does when one is missing: Three of them decide who is asking and about what. DOCUMIND_PROJECT gives the identity: without DOCUMIND_IMPERSONATE_SA, the script impersonates documind-ui-sa in that project. DOCUMIND_TENANT gives the tenant, and its default is tenant-smoke. Hold on to that default; step 6 is about it. Run the script with no URL at all and it refuses, then prints its own checklist. This costs nothing and touches nothing: main() returns before it mints a token or opens a connection. The last required check asks the same question with no token at all. A service that answers everybody would pass every check above it, so this one asserts a refusal: 401 or 403, and anything else is a failure. Run it with the three variables, the tenant included. API, PROJECT and TENANT come from the setup block; TENANT is acme.

Run order inside this file:
1. make smoke: one line per check (source window 15)
2. make smoke: one line per check (source window 21)

Prerequisites: demo_04_make_preflight_what_the_lane_stands_on.
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


# Original CLI workflow for step_01_make_smoke_one_line_per_check.
COMMANDS_01 = """env -u DOCUMIND_API_URL python smoke/smoke.py; echo "exit $?"     # no URL: it refuses, and says what it checks

"""

def step_01_make_smoke_one_line_per_check(session):
    """Run make smoke: one line per check at this checkpoint.

    No guard-project, and no variables passed: smoke.py reads everything from its environment. These are the names it reads, and what it does when one is missing: Three of them decide who is asking and about what. DOCUMIND_PROJECT gives the identity: without DOCUMIND_IMPERSONATE_SA, the script impersonates documind-ui-sa in that project. DOCUMIND_TENANT gives the tenant, and its default is tenant-smoke. Hold on to that default; step 6 is about it. Run the script with no URL at all and it refuses, then prints its own checklist. This costs nothing and touches nothing: main() returns before it mints a token or opens a connection.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (no network: smoke.py stops before its first call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DOCUMIND_API_URL is not set — this is a LIVE test, run it after `make up`.

    DocuMind AI — live smoke test (Tier B).

    Run this AFTER `make up` against a real deployment to prove the RAG API is
    alive end-to-end. Uses only the Python standard library + the `gcloud` CLI
    (for the identity token), so it runs anywhere gcloud is authenticated.

    It is NOT part of the offline dry run — offline, validate.py only syntax-checks
    this file. On live day:

        export DOCUMIND_API_URL=https://documind-api-xxx.run.app
        export DOCUMIND_PROJECT=documind-ai-live-0901
        python deploy/smoke/smoke.py

    Checks:
        1. GET  /health                -> 200 {"status":"ok"}
        2. GET  /ready                 -> 200 (to
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_make_smoke_one_line_per_check.
COMMANDS_02 = """make smoke DOCUMIND_API_URL="$API" DOCUMIND_PROJECT="$PROJECT" DOCUMIND_TENANT="$TENANT"

"""

def step_02_make_smoke_one_line_per_check(session):
    """Run make smoke: one line per check at this checkpoint.

    The last required check asks the same question with no token at all. A service that answers everybody would pass every check above it, so this one asserts a refusal: 401 or 403, and anything else is a failure. Run it with the three variables, the tenant included. API, PROJECT and TENANT come from the setup block; TENANT is acme.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one question answered, one refused; about a minute).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/smoke_green.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_15', step_01_make_smoke_one_line_per_check),
        ('source_21', step_02_make_smoke_one_line_per_check),
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
