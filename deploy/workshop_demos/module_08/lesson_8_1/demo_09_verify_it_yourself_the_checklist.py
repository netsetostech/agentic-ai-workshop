"""Lesson 8.1: Verify it yourself: the checklist

Eight checks, each one step above, each with what a pass looks like on your lane; then the one command that puts the note away. When the checks are done, withdraw the note. make retire flags its rows as retired, with an expire_at 30 days out, marks its ledger row withdrawn, removes it from the managed stores, takes its ids out of the Vector Search index (since 13 October 2026) and moves acme's fingerprint. The object stays in the bucket, and make restore would bring it back (lesson 1.7):

Run order inside this file:
1. Verify it yourself: the checklist (source window 41)

Prerequisites: demo_07_the_burst_thirty_one_objects_against_five_instances.
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


# Original CLI workflow for step_01_verify_it_yourself_the_checklist.
COMMANDS_01 = """make retire PROJECT=$PROJECT SOURCE=acme/pubsub_trace_note.md

"""

def step_01_verify_it_yourself_the_checklist(session):
    """Run Verify it yourself: the checklist at this checkpoint.

    Eight checks, each one step above, each with what a pass looks like on your lane; then the one command that puts the note away. When the checks are done, withdraw the note. make retire flags its rows as retired, with an expire_at 30 days out, marks its ledger row withdrawn, removes it from the managed stores, takes its ids out of the Vector Search index (since 13 October 2026) and moves acme's fingerprint. The object stays in the bucket, and make restore would bring it back (lesson 1.7):

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, when the lesson is done (withdraws the note; reversible with make restore).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/trace_retire.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_41', step_01_verify_it_yourself_the_checklist),
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
