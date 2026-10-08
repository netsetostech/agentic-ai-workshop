"""Lesson 10.4: /v1/route and /v1/desk, over REST

Optional, only with the door on, and no Workspace needed: make smoke-gchat's four refusals and the door's latest rows. It refuses on a lane whose last apply had the door off.

Run order inside this file:
1. Optional: the Google Chat door's refusals (source window 62)

Prerequisites: demo_07_v1_route_and_v1_desk_over_rest.
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


# Original CLI workflow for step_01_optional_the_google_chat_door_s_refusals.
COMMANDS_01 = """make smoke-gchat PROJECT="$PROJECT" REGION="$REGION"

"""

def step_01_optional_the_google_chat_door_s_refusals(session):
    """Run Optional: the Google Chat door's refusals at this checkpoint.

    This needs the door on your lane, step 3's optional part, and no Google Workspace. On a lane whose last apply had the door off, make smoke-gchat refuses and says so. smoke/smoke_gchat.py sends four requests that must be refused. Steps 1 and 2 go to the bridge as documind-outsider-sa: a Chat-shaped event to / and a push envelope to /work. The outsider is one of the bridge's invokers, so Cloud Run lets it in, and the 401, "this endpoint answers Google Chat and its own push only", comes from the bridge's own code. Steps 3 and 4 go to the chat service's POST /v1/desk as documind-evalacme-sa and as ui-sa, each naming a person in X-DocuMind-Principal, and the Desk's rule 1 refuses both: "not an allowed delegate". Then the smoke prints the latest rows of each kind from the last hour. The kit's comments call steps 3 and 4 the alert's own test: each writes a desk_delegation_refused row, which "Desk: a delegation was refused" counts, so expect it to fire and notify whatever channels your lane's alerts use. That is on purpose. No step shows the door accepting a call, because nobody may mint a token as documind-gchat-sa, by design. A person in Google Chat, as in step 4, is that proof.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, only with the Google Chat door on (its refusals; no Google Workspace needed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DocuMind Desk - the Google Chat door's refusals, live
      bridge: https://documind-gchat-NUMBER.asia-south1.run.app
      chat:   https://documind-chat-NUMBER.asia-south1.run.app
      --------------------------------------------------------
      [PASS] 1. POST / as the outsider  -> 401 'this endpoint answers Google Chat and its own push only'
      [PASS] 2. POST /work as the outsider  -> 401 'this endpoint answers Google Chat and its own push only'
      [PASS] 3. POST /v1/desk as documind-evalacme-sa, naming a person  -> 403 'not an allowed delegate'
      [PASS] 4. POST /v1/desk as documind-ui-sa, naming a person  -> 403 'not an allowed delegate'

      the latest rows (Cloud Logging, the last hour; a row can take a
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_62', step_01_optional_the_google_chat_door_s_refusals),
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
