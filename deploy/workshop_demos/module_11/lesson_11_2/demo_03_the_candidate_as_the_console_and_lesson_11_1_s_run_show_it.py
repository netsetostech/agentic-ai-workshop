"""Lesson 11.2: The candidate, as the console and lesson 11.1's run show it

If your candidate came from lesson 11.1's dispatch, read what its release-candidate job printed. The cell finds the run and the job, then keeps the lines that name the revision, compare its /version with the commit, and give the live gate's verdict, each after the name of the step that printed it.

Run order inside this file:
1. Do it: the dispatch's own lines (source window 6)

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


# Original CLI workflow for step_01_the_dispatch_s_own_lines.
COMMANDS_01 = """GH_REPO="$(python -c 'import json; print(json.load(open("terraform/runbook-project.auto.tfvars.json"))["github_repository"])')"
RUN="$(gh run list --repo "$GH_REPO" --workflow documind-cd.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId')"
JOB="$(gh run view "$RUN" --repo "$GH_REPO" --json jobs --jq '.jobs[] | select(.name == "release-candidate") | .databaseId')"
echo "run $RUN, job release-candidate $JOB"
gh run view --job "$JOB" --repo "$GH_REPO" --log \\
  | grep -E '>> candidate revision: |candidate /version git_sha=[^$]|== eval gate: LIVE ==| rows \\(|\\[(PASS|FAIL)\\]|All thresholds met|Blocked:' \\
  | sed -E 's/^[^\\t]*\\t([^\\t]*)\\t[^ ]* /\\1: /'

"""

def step_01_the_dispatch_s_own_lines(session):
    """Run Do it: the dispatch's own lines at this checkpoint.

    If your candidate came from lesson 11.1's dispatch, read what its release-candidate job printed. The cell finds the run and the job, then keeps the lines that name the revision, compare its /version with the commit, and give the live gate's verdict, each after the name of the step that printed it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, if lesson 11.1's dispatch made your candidate (GitHub reads; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ci_gate.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_the_dispatch_s_own_lines),
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
