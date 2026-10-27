"""Lesson 11.1: Four variables from your lane, and a person in front of production

Do it: the first make ci-vars The cell creates production through GitHub's REST API with you as its one required reviewer (in the browser: Settings > Environments > New environment, then Required reviewers). It runs make ci-vars again, pipes the four lines it printed into the shell, and reads back what the repository now holds. A shell that never exported REGION sends the Makefile's default. The kit refuses it before any tool runs:

Run order inside this file:
1. Do it: the first make ci-vars (source window 19)
2. Do it: a reviewer, then the variables (source window 21)
3. Change it: the Makefile's region (source window 23)

Prerequisites: demo_03_your_fork_and_your_project_as_github_and_the_console_show_them.
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


# Original CLI workflow for step_01_the_first_make_ci_vars.
COMMANDS_01 = """make ci-vars PROJECT="$PROJECT" REGION="$REGION"

"""

def step_01_the_first_make_ci_vars(session):
    """Run Do it: the first make ci-vars at this checkpoint.

    Do it: the first make ci-vars

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (terraform output and one GitHub read; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: # documind-cd.yml reads 4 repository variables. Set them on YOUR-GITHUB-USER/YOUR-REPO, the repository wif.tf trusts:
    gh variable set GCP_PROJECT --repo YOUR-GITHUB-USER/YOUR-REPO --body documind-ai-YOUR-ID
    gh variable set GCP_REGION --repo YOUR-GITHUB-USER/YOUR-REPO --body asia-south1
    gh variable set WIF_PROVIDER --repo YOUR-GITHUB-USER/YOUR-REPO --body projects/NUMBER/locations/global/workloadIdentityPools/documind-github/providers/github-oidc
    gh variable set CICD_SERVICE_ACCOUNT --repo YOUR-GITHUB-USER/YOUR-REPO --body sa-documind-cicd@documind-ai-YOUR-ID.iam.gserviceaccount.com
    # The trust (wif.tf): YOUR-GITHUB-USER/YOUR-REPO, id REPO_ID, ref refs/heads/main. A run from any other ref is 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_reviewer_then_the_variables.
COMMANDS_02 = """printf '{"reviewers":[{"type":"User","id":%s}]}' "$(gh api user --jq .id)" \\
  | gh api -X PUT "repos/$GH_REPO/environments/production" --input - --jq '"environment \\(.name): " + ([.protection_rules[].type] | join(", "))'
make ci-vars PROJECT="$PROJECT" REGION="$REGION" | tee "$HOME/ci-vars.txt"
grep '^gh variable set ' "$HOME/ci-vars.txt" | bash
gh variable list --repo "$GH_REPO"
echo "repository secrets: $(gh secret list --repo "$GH_REPO" | wc -l)"

"""

def step_02_a_reviewer_then_the_variables(session):
    """Run Do it: a reviewer, then the variables at this checkpoint.

    The cell creates production through GitHub's REST API with you as its one required reviewer (in the browser: Settings > Environments > New environment, then Required reviewers). It runs make ci-vars again, pipes the four lines it printed into the shell, and reads back what the repository now holds.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (writes to your fork: one environment, four variables).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/gh_setup.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_change_it_the_makefile_s_region.
COMMANDS_03 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
make ci-vars PROJECT="$PROJECT" REGION=us-central1     # what a shell left on the Makefile's default would send
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_03_change_it_the_makefile_s_region(session):
    """Run Change it: the Makefile's region at this checkpoint.

    A shell that never exported REGION sends the Makefile's default. The kit refuses it before any tool runs:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, if you want to see the refusal (nothing runs).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: STOP: REGION is us-central1, but lane documind-ai-YOUR-ID was planned in asia-south1 (runbook-project.auto.tfvars.json), where its image repository and services are: make ci-vars PROJECT=documind-ai-YOUR-ID REGION=asia-south1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_the_first_make_ci_vars),
        ('source_21', step_02_a_reviewer_then_the_variables),
        ('source_23', step_03_change_it_the_makefile_s_region),
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
