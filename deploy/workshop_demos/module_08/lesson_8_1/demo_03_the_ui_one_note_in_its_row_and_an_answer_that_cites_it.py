"""Lesson 8.1: The UI: one note in, its row, and an answer that cites it

The upload this page traces, made once, then seen the way a user sees it: a row under Versions, and an answer with a citation. The trace needs an upload nobody else could have made, so the cell below writes a short note of your own: a title line, the time you made it, and two invented sections. The time makes its bytes, and so its content hash, new to your lane. Then make ingest-one copies it under acme's prefix and waits for the worker's ingest_ok line. That is the kit's own drill:

Run order inside this file:
1. The UI: one note in, its row, and an answer that cites it (source window 7)

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


# Original CLI workflow for step_01_the_ui_one_note_in_its_row_and_an_answer_t.
COMMANDS_01 = """cat > /tmp/pubsub_trace_note.md <<EOF
# Night gate note

A note for lesson 8.1's trace, uploaded at $(date -u +%Y-%m-%dT%H:%M:%SZ). Every fact in it is invented.

## NG-01 - The night gate

After 9 pm, couriers deliver to gate 3 of the Bhiwandi depot. The parcel is signed for at the security desk, and
the duty officer enters it in the green register before the gate is closed.

## NG-02 - A refused parcel

A parcel refused at gate 3 goes back to the hub and comes again the next evening, at most three times. After the
third refusal it waits at the hub for the sender to collect.
EOF
make ingest-one PROJECT=$PROJECT TENANT=acme FILE=/tmp/pubsub_trace_note.md

"""

def step_01_the_ui_one_note_in_its_row_and_an_answer_t(session):
    """Run The UI: one note in, its row, and an answer that cites it at this checkpoint.

    The upload this page traces, made once, then seen the way a user sees it: a row under Versions, and an answer with a citation. The trace needs an upload nobody else could have made, so the cell below writes a short note of your own: a title line, the time you made it, and two invented sections. The time makes its bytes, and so its content hash, new to your lane. Then make ingest-one copies it under acme's prefix and waits for the worker's ingest_ok line. That is the kit's own drill:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one small upload; paise of embedding).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/trace_upload.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_the_ui_one_note_in_its_row_and_an_answer_t),
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
