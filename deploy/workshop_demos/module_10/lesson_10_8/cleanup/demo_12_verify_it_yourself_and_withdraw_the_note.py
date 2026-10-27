"""Lesson 10.8: Verify it yourself, and withdraw the note

At lesson end: make retire flags every current chunk of the note with an expiry and writes WITHDRAWN on its ledger row: a tombstone the nightly reconcile honours, so the same bytes uploaded again are acknowledged and never reactivated. The object stays in the bucket, and make restore is the way back. Then the chat switches come off, if step 9 did not already remove them.

Run order inside this file:
1. Clean up: the note withdrawn, the switches off (source window 83)

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


# Original CLI workflow for step_01_clean_up_the_note_withdrawn_the_switches_o.
COMMANDS_01 = """make retire PROJECT="$PROJECT" SOURCE=acme/vendor_note_acme.md
make sources PROJECT="$PROJECT" TENANT_ONLY=acme | grep -i vendor_note
gcloud run services update documind-chat --region "$REGION" --project "$PROJECT" --quiet \\
  --remove-env-vars AGENT_FENCE,AGENT_SCRUB

"""

def step_01_clean_up_the_note_withdrawn_the_switches_o(session):
    """Run Clean up: the note withdrawn, the switches off at this checkpoint.

    make retire flags every current chunk of the note with an expiry and writes WITHDRAWN on its ledger row: a tombstone the nightly reconcile honours, so the same bytes uploaded again are acknowledged and never reactivated. The object stays in the bucket, and make restore is the way back. Then the chat switches come off, if step 9 did not already remove them.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the note withdrawn, the ledger row, the switches off).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/retire.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_83', step_01_clean_up_the_note_withdrawn_the_switches_o),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=True, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
