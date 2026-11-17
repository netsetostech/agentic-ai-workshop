"""Lesson 12.3: The verdict and the delta

At lesson end: Then the gate on it, and the three reports side by side: each judged rate, the rows passed, the generation time at p50 and p95 as the gate measures it, the model that answered each, and the rows each change moved. Remove the untuned revision's address when you are done with it. The revision stays in the service's list, with no traffic, as the candidate's does after the next block. The decision is yours, and it reads the three results in order. The gate must pass. The judge says how often the tuned model gives the worse answer where the two differ. The delta says what that is worth at your volume. With a candidate that passes, there are three ways forward:

Run order inside this file:
1. Compare the models: the untuned base (source window 31)
2. The decision, and the candidate's tag (source window 34)

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


# Original CLI workflow for step_01_compare_the_models_the_untuned_base.
COMMANDS_01 = """gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags untuned
curl -s -o /dev/null -w "the untuned URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$UNTUNED/health"

"""

def step_01_compare_the_models_the_untuned_base(session):
    """Run Compare the models: the untuned base at this checkpoint.

    Then the gate on it, and the three reports side by side: each judged rate, the rows passed, the generation time at p50 and p95 as the gate measures it, the model that answered each, and the rows each change moved. Remove the untuned revision's address when you are done with it. The revision stays in the service's list, with no traffic, as the candidate's does after the next block.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (removes the untuned revision's address; the revision stays, with no traffic).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    the untuned URL now: HTTP 404
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_decision_and_the_candidate_s_tag.
COMMANDS_02 = """gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate
rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag
curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"
python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]
def describe(*what):
    out = subprocess.run(["gcloud", "run", *what, "--region", R, "--project", P, "--format=json"], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)
def runs(rev):                        # a revision's image (the digest it holds) and its literal settings
    c = describe("revisions", "describe", rev)["spec"]["containers"][0]
    return c["image"], {e["name"]: e.get("value", "") for e in c.get("env") or [] if "valueFrom" not in e}
svc = describe("services", "describe", "documind-api")
serving = next(t["revisionName"] for t in svc["status"]["traffic"] if t.get("percent") == 100)
image, want = runs(serving)
made, have = runs(svc["status"]["latestCreatedRevisionName"])      # the revision the template last made
put, drop = {k: v for k, v in want.items() if have.get(k) != v}, sorted(set(have) - set(want))
print(f"the template against {serving}: image {'the same' if made == image else 'another'}; put back {sorted(put)}; remove {drop}")
if put or drop or made != image:
    cmd = ["gcloud", "run", "services", "update", "documind-api", "--region", R, "--project", P, "--no-traffic", "--quiet", "--image", image]
    cmd += ["--update-env-vars", "^|^" + "|".join(f"{k}={v}" for k, v in put.items())] if put else []
    cmd += ["--remove-env-vars", ",".join(drop)] if drop else []
    subprocess.run(cmd, check=True, capture_output=True)
PY
make gotcha-detect ID=rollback-keeps-template PROJECT="$PROJECT" REGION="$REGION" | tail -3

"""

def step_02_the_decision_and_the_candidate_s_tag(session):
    """Run The decision, and the candidate's tag at this checkpoint.

    The decision is yours, and it reads the three results in order. The gate must pass. The judge says how often the tuned model gives the worse answer where the two differ. The delta says what that is worth at your volume. With a candidate that passes, there are three ways forward:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (removes the candidate's address; the revision stays, with no traffic).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    the candidate URL now: HTTP 404
    the template against documind-api-000NN-xxx: image another; put back ['GENERATOR_MODEL', 'GIT_SHA', 'RAG_MODEL_BASE']; remove []
    documind-api's template is what its serving revision documind-api-000NN-xxx was made from
    nothing found
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_compare_the_models_the_untuned_base),
        ('source_34', step_02_the_decision_and_the_candidate_s_tag),
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
