"""Lesson 11.1: Your fork and your project, as GitHub and the console show them

The cell reads the trust from the inputs file and exports the repository as GH_REPO, which every later cell uses. Then it asks GitHub about that repository: whether it is public and a fork, its numeric id, and the state of its workflows.

Run order inside this file:
1. Do it: what your lane trusts, and what GitHub says about it (source window 6)

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


# Original CLI workflow for step_01_what_your_lane_trusts_and_what_github_says.
COMMANDS_01 = """read -r GH_REPO TRUST_ID TRUST_REF < <(python -c 'import json; t = json.load(open("terraform/runbook-project.auto.tfvars.json")); print(t["github_repository"], t["github_repository_id"], t["deploy_ref"])')
export GH_REPO; echo "your lane trusts $GH_REPO, id $TRUST_ID, on $TRUST_REF"
gh repo view "$GH_REPO" --json nameWithOwner,visibility,isFork,parent \\
  --jq '"GitHub: \\(.nameWithOwner), \\(.visibility), " + (if .isFork then "a fork of \\(.parent.owner.login)/\\(.parent.name)" else "not a fork" end)'
gh api "repos/$GH_REPO" --jq '"its GitHub id: \\(.id)"'
gh workflow list --repo "$GH_REPO" --all --json name,state --jq '.[] | "workflow \\(.name): \\(.state)"'

"""

def step_01_what_your_lane_trusts_and_what_github_says(session):
    """Run Do it: what your lane trusts, and what GitHub says about it at this checkpoint.

    The cell reads the trust from the inputs file and exports the repository as GH_REPO, which every later cell uses. Then it asks GitHub about that repository: whether it is public and a fork, its numeric id, and the state of its workflows.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads one local file, then GitHub; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/fork_check.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_what_your_lane_trusts_and_what_github_says),
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
