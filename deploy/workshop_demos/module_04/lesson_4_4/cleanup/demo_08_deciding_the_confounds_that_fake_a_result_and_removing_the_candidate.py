"""Lesson 4.4: Deciding, the confounds that fake a result, and removing the candidate

At lesson end: This ends the experiment. The candidate revision stays in the service's history with no traffic and no URL. Removing the tag is not enough on its own: make promote refuses only when the tag points at another revision, and otherwise flips traffic to the revision named in .candidate-revision. Deleting that file makes make promote stop with an error instead.

Run order inside this file:
1. Do it: remove the candidate's tag (source window 26)

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


# Original CLI workflow for step_01_remove_the_candidate_s_tag.
COMMANDS_01 = """gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate
rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag
curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"

"""

def step_01_remove_the_candidate_s_tag(session):
    """Run Do it: remove the candidate's tag at this checkpoint.

    This ends the experiment. The candidate revision stays in the service's history with no traffic and no URL. Removing the tag is not enough on its own: make promote refuses only when the tag points at another revision, and otherwise flips traffic to the revision named in .candidate-revision. Deleting that file makes make promote stop with an error instead.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the candidate's tag and its recorded name removed; the live revision is untouched).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    the candidate URL now: HTTP 404
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_remove_the_candidate_s_tag),
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
