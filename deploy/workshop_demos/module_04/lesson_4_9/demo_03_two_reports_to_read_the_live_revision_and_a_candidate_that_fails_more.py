"""Lesson 4.9: Two reports to read: the live revision, and a candidate that fails more

Do it: the live revision, with its pools Do it: a candidate on the cheap model, the same rows, and the tag removed

Run order inside this file:
1. Do it: the live revision, with its pools (source window 8)
2. Do it: a candidate on the cheap model, the same rows, and the tag removed (source window 10)
3. Do it: a candidate on the cheap model, the same rows, and the tag removed (source window 12)
4. Do it: a candidate on the cheap model, the same rows, and the tag removed (source window 14)

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


def step_01_the_live_revision_with_its_pools(session):
    """Run Do it: the live revision, with its pools at this checkpoint.

    Do it: the live revision, with its pools

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every golden row to the live revision, each pool read again: about ten minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_live.txt]
    """
    import os
    from workshop_helpers.gates import live_gate
    os.environ["DOCUMIND_EVAL_PASSAGES"] = "1"
    try:
        live_gate(session, report="evals/reports/live49.json")
    finally:
        os.environ.pop("DOCUMIND_EVAL_PASSAGES", None)

# Original CLI workflow for step_02_a_candidate_on_the_cheap_model_the_same_ro.
COMMANDS_02 = """make candidate PROJECT="$PROJECT" GENERATOR_MODEL=gemini-3.1-flash-lite RAG_MODEL_BASE=gemini-3.1-flash-lite
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"

"""

def step_02_a_candidate_on_the_cheap_model_the_same_ro(session):
    """Run Do it: a candidate on the cheap model, the same rows, and the tag removed at this checkpoint.

    Do it: a candidate on the cheap model, the same rows, and the tag removed

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a revision on the cheap model, with no traffic).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\
      --update-env-vars "^|^GENERATOR_MODEL=gemini-3.1-flash-lite|RAG_MODEL_BASE=gemini-3.1-flash-lite|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=off|SEMANTIC_CACHE=off|RETRIEVAL_CURRENT_ONLY=off|RETRIEVAL_GRAPH=off|GRAPH_BACKEND=firestore|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
    ...
    >> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
    >> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-tr
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def step_03_a_candidate_on_the_cheap_model_the_same_ro(session):
    """Run Do it: a candidate on the cheap model, the same rows, and the tag removed at this checkpoint.

    Do it: a candidate on the cheap model, the same rows, and the tag removed

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same rows to the candidate).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_cand.txt]
    """
    import os
    from workshop_helpers.gates import live_gate
    os.environ["DOCUMIND_EVAL_PASSAGES"] = "1"
    try:
        live_gate(session, report="evals/reports/cand49.json", api=os.environ["CAND"])
    finally:
        os.environ.pop("DOCUMIND_EVAL_PASSAGES", None)

# Original CLI workflow for step_04_a_candidate_on_the_cheap_model_the_same_ro.
COMMANDS_04 = """gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate
rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag (lesson 4.4)
curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"

"""

def step_04_a_candidate_on_the_cheap_model_the_same_ro(session):
    """Run Do it: a candidate on the cheap model, the same rows, and the tag removed at this checkpoint.

    Do it: a candidate on the cheap model, the same rows, and the tag removed

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the candidate's tag and its recorded name removed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    the candidate URL now: HTTP 404
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_8', step_01_the_live_revision_with_its_pools),
        ('source_10', step_02_a_candidate_on_the_cheap_model_the_same_ro),
        ('source_12', step_03_a_candidate_on_the_cheap_model_the_same_ro),
        ('source_14', step_04_a_candidate_on_the_cheap_model_the_same_ro),
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
