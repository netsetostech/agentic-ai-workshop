"""Lesson 4.8: The audit tab: what the admin console reads, and what it misses

At lesson end: The note came from you, and it should not stay in acme's corpus. make retire flags its chunks, which leave retrieval, and marks its ledger row WITHDRAWN; the object stays in the uploads bucket. Look at what stays. The findings record stays in dlp_findings until someone deletes it. The two audit events stay for five years, whatever anyone wants, which is what retention means. The withdrawal writes no audit event of its own: doc.delete is a registered action, and nothing in the kit emits it.

Run order inside this file:
1. Clean up: withdraw the note (source window 31)

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


# Original CLI workflow for step_01_clean_up_withdraw_the_note.
COMMANDS_01 = """make retire PROJECT="$PROJECT" SOURCE=acme/lesson83_vendor_note.md

"""

def step_01_clean_up_withdraw_the_note(session):
    """Run Clean up: withdraw the note at this checkpoint.

    The note came from you, and it should not stay in acme's corpus. make retire flags its chunks, which leave retrieval, and marks its ledger row WITHDRAWN; the object stays in the uploads bucket. Look at what stays. The findings record stays in dlp_findings until someone deletes it. The two audit events stay for five years, whatever anyone wants, which is what retention means. The withdrawal writes no audit event of its own: doc.delete is a registered action, and nothing in the kit emits it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the note withdrawn from the index).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"event": "reconcile_retired", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/lesson83_vendor_note.md", ...}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_clean_up_withdraw_the_note),
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
