"""Lesson 4.8: The PII scan: one list, and a note that trips it

Do it

Run order inside this file:
1. Do it (source window 8)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_the_pii_scan_one_list_and_a_note_that_trip.
COMMANDS_01 = """cat > "$HOME/lesson83_vendor_note.md" <<EOF
# Vendor onboarding note

Synthetic note for lesson 4.8. Every identifier below is the kit's invented, format-valid sample (evals/README.md).

Vendor contact: Asha Verma, mobile +919876543210.
PAN AAAPZ1234C, GSTIN 27AAAPZ1234C1ZV, Aadhaar 2234 5678 9012.

Written for lesson 4.8 at $(date -u +%FT%TZ).
EOF
make ingest-one PROJECT="$PROJECT" TENANT=acme FILE="$HOME/lesson83_vendor_note.md"

"""

def step_01_the_pii_scan_one_list_and_a_note_that_trip(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a small note with the kit's synthetic identifiers, uploaded to acme).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Copying file:///home/you/lesson83_vendor_note.md to gs://documind-ai-YOUR-ID-uploads/acme/lesson83_vendor_note.md
      Completed files 1/1 | 303.0B/303.0B
    >> gs://documind-ai-YOUR-ID-uploads/acme/lesson83_vendor_note.md - waiting for the worker (up to 5 min)
    >> indexed: acme_...	1	1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_8', step_01_the_pii_scan_one_list_and_a_note_that_trip),
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
