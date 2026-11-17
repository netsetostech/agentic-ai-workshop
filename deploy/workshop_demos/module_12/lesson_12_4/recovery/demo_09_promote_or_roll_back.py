"""Lesson 12.4: Promote, or roll back

Only when make gate was red: no promote, the commit with the new version reverted, and documind-api's template back to v3. A green gate promotes in the file before, and nothing here runs.

Run order inside this file:
1. Promote, or roll back (source window 56)

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


# Original CLI workflow for step_01_promote_or_roll_back.
COMMANDS_01 = """git -c user.name="$ME" -c user.email="$ME" revert --no-edit HEAD && git log --oneline -1   # the commit that holds $PV and its golden row
make build PROJECT="$PROJECT" REGION="$REGION" SERVICES=api 2>&1 | tail -3
make prompt-candidate PROJECT="$PROJECT" REGION="$REGION" PROMPT_VERSION=v3   # $PV off documind-api's template

"""

def step_01_promote_or_roll_back(session):
    """Run Promote, or roll back at this checkpoint.

    Green. make promote-gated runs lesson 11.2's gate-check on the record, then the unchanged make promote. That writes the revision serving now to .previous-revision, moves all the traffic to the candidate by name, and prints /version from the live URL. Ask the question on the UI again afterwards: the UI now reaches v4. The cell asks it once more from the shell. If anything looks wrong later, make rollback returns the traffic to the revision in .previous-revision, which never went away. Red. No promote. No traffic reached v4, so you can drop it without changing any version that has served. Revert the commit that holds v4 and its golden row; the next rule you accept builds on v3 again. PROMPT_VERSION=v4 is still in documind-api's template, because an update with --no-traffic still writes it. Any later candidate made from an image without v4 would carry the variable and refuse to start. So build the reverted commit and put v3 back with make prompt-candidate, which makes a new candidate with no traffic.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, only on a red gate (no traffic moves).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_56', step_01_promote_or_roll_back),
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
