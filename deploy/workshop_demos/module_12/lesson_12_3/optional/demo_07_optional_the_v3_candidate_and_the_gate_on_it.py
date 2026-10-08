"""Lesson 12.3: Optional: the v3 candidate, and the gate on it

Do it Then the chapter's gate, on v3. A tidy format is worth nothing if the answers under it fail:

Run order inside this file:
1. Do it (source window 28)
2. Do it (source window 30)

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


# Original CLI workflow for step_01_optional_the_v3_candidate_and_the_gate_on.
COMMANDS_01 = """export ENDPOINT_V3="${ENDPOINT_V3:-$(grep -o 'projects/[^ ]*/endpoints/[0-9]*' ~/poll172v3.log | head -1)}"     # lesson 12.2's step 7
make candidate PROJECT="$PROJECT" GENERATOR_MODEL="$ENDPOINT_V3" RAG_MODEL_BASE=gemini-3.1-flash-lite
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"

"""

def step_01_optional_the_v3_candidate_and_the_gate_on(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit (v3's endpoint behind the candidate address; still no traffic).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\
      --update-env-vars "^|^GENERATOR_MODEL=projects/NUMBER/locations/us/endpoints/3784707595493887459|RAG_MODEL_BASE=gemini-3.1-flash-lite|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=off|SEMANTIC_CACHE=off|RETRIEVAL_CURRENT_ONLY=off|RETRIEVAL_GRAPH=off|GRAPH_BACKEND=firestore|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
    ...
    >> candidate revision: documind-api-000NN-zzz (deploy/.candidate-revision - make promote moves traffic to it by name)
    >> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remo
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_optional_the_v3_candidate_and_the_gate_on.
COMMANDS_02 = """make eval-live PROJECT="$PROJECT" API="$CAND" REPORT="$HOME/cand173v3.json"

"""

def step_02_optional_the_v3_candidate_and_the_gate_on(session):
    """Run Do it at this checkpoint.

    Then the chapter's gate, on v3. A tidy format is worth nothing if the answers under it fail:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit (every golden row on the v3 candidate: about ten minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://candidate---documind-api-NUMBER.asia-south1.run.app
      65 rows (47 answerable, 18 not) against https://candidate---documind-api-NUMBER.asia-south1.run.app

      [PASS] request_success_rate  100.0%  (threshold 100%; 65 rows)
      [PASS] answerable_rate        97.9%  (threshold 80%; 47 rows)
      [PASS] citation_rate         100.0%  (threshold 95%; 46 rows)
      [PASS] citation_valid_rate   100.0%  (threshold 100%; 46 rows)
      [PASS] must_contain_rate      95.7%  (threshold 85%; 46 rows)
      [PASS] correct_rate           93.6%  (threshold 68%; 47 rows)
      [PASS] refusal_rate          100.0%  (threshold 90%; 18 rows)
      [PASS] media_kind_rate       100.0%  (threshold 80%; 3 rows)
      [PASS] isolation_40
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_28', step_01_optional_the_v3_candidate_and_the_gate_on),
        ('source_30', step_02_optional_the_v3_candidate_and_the_gate_on),
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
