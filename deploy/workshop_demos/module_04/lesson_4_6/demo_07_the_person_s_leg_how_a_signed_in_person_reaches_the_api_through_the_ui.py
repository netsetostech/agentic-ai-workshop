"""Lesson 4.6: The person's leg: how a signed-in person reaches the API through the UI

IAP in front of the UI, the assertion forwarded beside the UI's token, and every caller the API recorded in a day. A person never calls the API directly. They sign in at IAP in front of the UI, which admits only accounts granted the sign-in role. IAP hands the UI a signed assertion with every request. When the UI calls the API, it sends two credentials, as its _headers() shows in step 5: its own token, which gets past the door, and the person's assertion, forwarded unchanged. The API's verifier sees the assertion first and takes the person's email from it. The roster check and the usage row are then about the person, which is what lesson 3.8 saw in Chat. The cell counts every caller the API recorded in the last day.

Run order inside this file:
1. The person's leg: how a signed-in person reaches the API through the UI (source window 29)

Prerequisites: demo_06_one_request_end_to_end_a_forged_header_and_the_row_that_ignores_it.
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


# Original CLI workflow for step_01_the_person_s_leg_how_a_signed_in_person_re.
COMMANDS_01 = """gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND (jsonPayload.event="query" OR jsonPayload.event="stream")' \\
  --project "$PROJECT" --freshness=1d --limit 1000 --format='value(jsonPayload.user)' | sort | uniq -c | sort -rn

"""

def step_01_the_person_s_leg_how_a_signed_in_person_re(session):
    """Run The person's leg: how a signed-in person reaches the API through the UI at this checkpoint.

    IAP in front of the UI, the assertion forwarded beside the UI's token, and every caller the API recorded in a day. A person never calls the API directly. They sign in at IAP in front of the UI, which admits only accounts granted the sign-in role. IAP hands the UI a signed assertion with every request. When the UI calls the API, it sends two credentials, as its _headers() shows in step 5: its own token, which gets past the door, and the person's assertion, forwarded unchanged. The API's verifier sees the assertion first and takes the person's email from it. The roster check and the usage row are then about the person, which is what lesson 3.8 saw in Chat. The cell counts every caller the API recorded in the last day.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every caller the API recorded in the last day).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: NN documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
          N you@example.com
    """
    manual_checkpoint("Sign in through the deployed UI as the lesson's rostered person and submit the example question. Type done before inspecting the person's assertion path.")
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_29', step_01_the_person_s_leg_how_a_signed_in_person_re),
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
