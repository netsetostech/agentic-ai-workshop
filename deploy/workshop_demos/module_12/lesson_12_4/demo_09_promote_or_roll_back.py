"""Lesson 12.4: Promote, or roll back

A green record moves the traffic to the candidate. A red one moves nothing, and the version goes back with git. Green. make promote-gated runs lesson 11.2's gate-check on the record, then the unchanged make promote. That writes the revision serving now to .previous-revision, moves all the traffic to the candidate by name, and prints /version from the live URL. Ask the question on the UI again afterwards: the UI now reaches v4. The cell asks it once more from the shell. If anything looks wrong later, make rollback returns the traffic to the revision in .previous-revision, which never went away.

Run order inside this file:
1. Promote, or roll back (source window 54)

Prerequisites: demo_08_before_and_after_the_live_url_and_the_tag_url.
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
COMMANDS_01 = """make promote-gated PROJECT="$PROJECT" REGION="$REGION"
curl -s -X POST "$API/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d "$(python -c 'import json, os; print(json.dumps({"query": os.environ["Q"], "tenant_id": os.environ["TENANT"], "stream": False}))')" \\
  | python -c 'import json, sys; a = json.load(sys.stdin); print("live now, answerable:", a["answerable"], "| answer:", a["answer"])'

"""

def step_01_promote_or_roll_back(session):
    """Run Promote, or roll back at this checkpoint.

    A green record moves the traffic to the candidate. A red one moves nothing, and the version goes back with git. Green. make promote-gated runs lesson 11.2's gate-check on the record, then the unchanged make promote. That writes the revision serving now to .previous-revision, moves all the traffic to the candidate by name, and prints /version from the live URL. Ask the question on the UI again afterwards: the UI now reaches v4. The cell asks it once more from the shell. If anything looks wrong later, make rollback returns the traffic to the revision in .previous-revision, which never went away.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, only on a green record (traffic moves; one answer after it).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/outcome.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_54', step_01_promote_or_roll_back),
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
