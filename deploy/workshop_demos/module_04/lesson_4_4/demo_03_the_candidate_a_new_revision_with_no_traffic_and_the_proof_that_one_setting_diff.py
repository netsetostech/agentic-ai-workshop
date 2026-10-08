"""Lesson 4.4: The candidate: a new revision with no traffic, and the proof that one setting differs

Do it: the candidate The cell finds the revision serving traffic and the one tagged candidate, reads both revisions' settings, and prints every setting that differs.

Run order inside this file:
1. Do it: the candidate (source window 8)
2. Do it: prove it is one change (source window 10)

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


# Original CLI workflow for step_01_the_candidate.
COMMANDS_01 = """make candidate PROJECT="$PROJECT" GENERATOR_MODEL=gemini-3.1-flash-lite
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"

"""

def step_01_the_candidate(session):
    """Run Do it: the candidate at this checkpoint.

    Do it: the candidate

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a new revision with no traffic; nothing moves for users).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\
      --update-env-vars "^|^GENERATOR_MODEL=gemini-3.1-flash-lite|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|..." --remove-env-vars GENERATOR_LOCATION
    ...
    >> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
    >> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
    CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_prove_it_is_one_change(session):
    """Run Do it: prove it is one change at this checkpoint.

    The cell finds the revision serving traffic and the one tagged candidate, reads both revisions' settings, and prints every setting that differs.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads both revisions; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: live documind-api-000NN-xxx   candidate documind-api-000NN-yyy
      GENERATOR_MODEL        gemini-3.6-flash           -> gemini-3.1-flash-lite
    1 setting(s) differ
    """
    import json, os, subprocess
    def gcloud(*a):
        """Run this cell's gcloud command with its project/region context and decode the requested output.
        
        Example: gcloud('run', 'services', 'describe', 'documind-api')
        """
        cmd = ["gcloud", *a, "--region", os.environ["REGION"], "--project", os.environ["PROJECT"], "--format=json"]
        return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    traffic = gcloud("run", "services", "describe", "documind-api")["status"]["traffic"]
    live = max((t for t in traffic if t.get("percent")), key=lambda t: t["percent"])["revisionName"]
    cand = next(t["revisionName"] for t in traffic if t.get("tag") == "candidate")
    env = lambda rev: {e["name"]: e.get("value", "") for e in gcloud("run", "revisions", "describe", rev)["spec"]["containers"][0].get("env", [])}
    a, b = env(live), env(cand)
    print(f"live {live}   candidate {cand}")
    diff = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
    for k in diff:
        print(f"  {k:22} {a.get(k, '(unset)'):26} -> {b.get(k, '(unset)')}")
    print(f"{len(diff)} setting(s) differ" + ("" if len(diff) == 1 else " - not one controlled change yet"))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_8', step_01_the_candidate),
        ('source_10', step_02_prove_it_is_one_change),
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
