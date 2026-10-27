"""Lesson 11.3: On your lane: promote, break it, roll back

At lesson end: time is the shell's own: when the command ends, it prints how long it took. The manifest's proof for this lesson asks for under two minutes. Between those two cells, every answer from your API is a 500. If you have to stop there, or a cell fails, run the cell below before you leave: it reads which revision serves all of documind-api's traffic and the model that revision runs, and runs make rollback only while that model is gemini-3.6-flsh. Otherwise it changes nothing and says so. The lesson's finish runs it as well. The template still names gemini-3.6-flsh until step 7's repair deploys a good revision.

Run order inside this file:
1. Do it: the rollback, timed (source window 38)

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


# Original CLI workflow for step_01_the_rollback_timed.
COMMANDS_01 = """# when you finish the lesson: documind-api back on the revision before the forced promote, only while it serves gemini-3.6-flsh
SERVING="$(gcloud run services describe documind-api --region="$REGION" --project="$PROJECT" --format=json |
  python -c 'import json,sys; print(next((t.get("revisionName", "") for t in json.load(sys.stdin)["status"]["traffic"] if t.get("percent") == 100), ""))')"
MODEL="$(gcloud run revisions describe "$SERVING" --region="$REGION" --project="$PROJECT" --format=json |
  python -c 'import json,sys; print({e["name"]: e.get("value", "") for c in json.load(sys.stdin)["spec"]["containers"] for e in c.get("env", [])}.get("GENERATOR_MODEL", ""))')"
if [ "$MODEL" = "gemini-3.6-flsh" ]; then make rollback PROJECT="$PROJECT" REGION="$REGION"; else echo "documind-api serves $SERVING ($MODEL): nothing to put back"; fi

"""

def step_01_the_rollback_timed(session):
    """Run Do it: the rollback, timed at this checkpoint.

    time is the shell's own: when the command ends, it prints how long it took. The manifest's proof for this lesson asks for under two minutes. Between those two cells, every answer from your API is a 500. If you have to stop there, or a cell fails, run the cell below before you leave: it reads which revision serves all of documind-api's traffic and the model that revision runs, and runs make rollback only while that model is gemini-3.6-flsh. Otherwise it changes nothing and says so. The lesson's finish runs it as well. The template still names gemini-3.6-flsh until step 7's repair deploys a good revision.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, when you finish the lesson, not now (a traffic move only while the mistyped model serves).
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
        ('source_38', step_01_the_rollback_timed),
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
