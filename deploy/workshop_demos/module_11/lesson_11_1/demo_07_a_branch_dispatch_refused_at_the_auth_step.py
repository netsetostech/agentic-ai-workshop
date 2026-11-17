"""Lesson 11.1: A branch dispatch, refused at the auth step

The cell makes a branch at main's commit through GitHub's REST API, dispatches the workflow on it, waits for the run to finish, prints its summary and the error lines of the failed step, and deletes the branch. In the browser: the branch menu on your fork's code page, then Run workflow with that branch chosen.

Run order inside this file:
1. Do it: a branch, a run, a refusal (source window 31)

Prerequisites: demo_06_a_build_and_a_deploy_from_main_with_no_key.
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


# Original CLI workflow for step_01_a_branch_a_run_a_refusal.
COMMANDS_01 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
gh api -X POST "repos/$GH_REPO/git/refs" -f ref=refs/heads/try-a-branch \\
  -f sha="$(gh api "repos/$GH_REPO/commits/main" --jq .sha)" --jq '"branch \\(.ref) at \\(.object.sha[0:7])"'
gh workflow run documind-cd.yml --repo "$GH_REPO" --ref try-a-branch -f path=candidate && sleep 20
BR="$(gh run list --repo "$GH_REPO" --workflow documind-cd.yml --branch try-a-branch --limit 1 --json databaseId --jq '.[0].databaseId')"
gh run watch "$BR" --repo "$GH_REPO" --exit-status > /dev/null; echo "gh run watch $BR: exit $?"
gh run view "$BR" --repo "$GH_REPO"
gh run view "$BR" --repo "$GH_REPO" --log-failed | grep -iE "error|attribute condition" | head -n 5
gh api -X DELETE "repos/$GH_REPO/git/refs/heads/try-a-branch" && echo "branch try-a-branch deleted"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_01_a_branch_a_run_a_refusal(session):
    """Run Do it: a branch, a run, a refusal at this checkpoint.

    The cell makes a branch at main's commit through GitHub's REST API, dispatches the workflow on it, waits for the run to finish, prints its summary and the error lines of the failed step, and deletes the branch. In the browser: the branch menu on your fork's code page, then Run workflow with that branch chosen.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a branch, a run that fails on purpose, the branch deleted).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/run_branch.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_a_branch_a_run_a_refusal),
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
