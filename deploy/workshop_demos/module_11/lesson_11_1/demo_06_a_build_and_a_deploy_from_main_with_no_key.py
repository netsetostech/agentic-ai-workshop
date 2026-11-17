"""Lesson 11.1: A build and a deploy from main, with no key

The cell starts the run, finds its id, prints its page, waits until release-candidate has finished, and prints the run's summary. Open the page while it waits and watch the jobs and their steps. In the browser the same start is Actions > documind-cd > Run workflow, on main, with candidate as the path. On the run's page: Review deployments, tick production, then Reject. The cell does the same through GitHub's REST API, as the reviewer: The cell reads documind-api's traffic and the candidate revision, then asks GitHub which commit the run built and how the run ended.

Run order inside this file:
1. Do it: dispatch, and wait for the build and the gate (source window 25)
2. Do it: say no at promote (source window 27)
3. Do it: what the run left on Cloud Run (source window 28)

Prerequisites: demo_05_four_variables_from_your_lane_and_a_person_in_front_of_production.
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


# Original CLI workflow for step_01_dispatch_and_wait_for_the_build_and_the_ga.
COMMANDS_01 = """gh workflow run documind-cd.yml --repo "$GH_REPO" --ref main -f path=candidate && sleep 20
export RUN="$(gh run list --repo "$GH_REPO" --workflow documind-cd.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId')"
echo "run $RUN: https://github.com/$GH_REPO/actions/runs/$RUN"
until [ "$(gh run view "$RUN" --repo "$GH_REPO" --json jobs --jq '[.jobs[] | select(.name == "release-candidate") | .status] | first')" = completed ]; do sleep 30; done
gh run view "$RUN" --repo "$GH_REPO"

"""

def step_01_dispatch_and_wait_for_the_build_and_the_ga(session):
    """Run Do it: dispatch, and wait for the build and the gate at this checkpoint.

    The cell starts the run, finds its id, prints its page, waits until release-candidate has finished, and prints the run's summary. Open the page while it waits and watch the jobs and their steps. In the browser the same start is Actions > documind-cd > Run workflow, on main, with candidate as the path.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (starts one run on your fork, then waits about fifteen minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/run_main.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_say_no_at_promote.
COMMANDS_02 = """ENV_ID="$(gh api "repos/$GH_REPO/environments/production" --jq .id)"
printf '{"environment_ids":[%s],"state":"rejected","comment":"lesson 11.2 judges this candidate first"}' "$ENV_ID" \\
  | gh api -X POST "repos/$GH_REPO/actions/runs/$RUN/pending_deployments" --input - --silent && echo "promote: rejected"

"""

def step_02_say_no_at_promote(session):
    """Run Do it: say no at promote at this checkpoint.

    On the run's page: Review deployments, tick production, then Reject. The cell does the same through GitHub's REST API, as the reviewer:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, or press Reject on the run's page (a person's no).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_what_the_run_left_on_cloud_run.
COMMANDS_03 = """python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]


def gc(*args):
    \"\"\"One gcloud read of the lane, as JSON.\"\"\"
    out = subprocess.run(["gcloud", *args, f"--project={P}", f"--region={R}", "--format=json"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


svc = gc("run", "services", "describe", "documind-api")
print("documind-api, last changed by", svc["metadata"].get("annotations", {}).get("serving.knative.dev/lastModifier", "(not recorded)"))
for t in svc["status"].get("traffic", []):
    print(f'  {t.get("percent", 0):>3}%  {t.get("revisionName")}  tag {t.get("tag", "-")}')
cand = next((t["revisionName"] for t in svc["status"].get("traffic", []) if t.get("tag") == "candidate"), None)
if cand:
    rev = gc("run", "revisions", "describe", cand)
    box = rev["spec"]["containers"][0]
    env = {e["name"]: e.get("value") for e in box.get("env", [])}
    print("candidate", cand, "made by", rev["metadata"].get("annotations", {}).get("serving.knative.dev/creator", "(not recorded)"))
    print("  image  ", box["image"])
    print("  GIT_SHA", env.get("GIT_SHA"))
PY
echo "the run built: $(gh run view "$RUN" --repo "$GH_REPO" --json headSha --jq .headSha)"
gh run view "$RUN" --repo "$GH_REPO" --json status,conclusion,jobs --jq '"run: \\(.status), \\(.conclusion)", (.jobs[] | "  \\(.name): \\(.conclusion)")'

"""

def step_03_what_the_run_left_on_cloud_run(session):
    """Run Do it: what the run left on Cloud Run at this checkpoint.

    The cell reads documind-api's traffic and the candidate revision, then asks GitHub which commit the run built and how the run ended.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two Cloud Run reads and two GitHub reads; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/candidate.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_dispatch_and_wait_for_the_build_and_the_ga),
        ('source_27', step_02_say_no_at_promote),
        ('source_28', step_03_what_the_run_left_on_cloud_run),
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
