"""Lesson 2.4: The chaos rung: an index that will not answer, on a candidate that takes no traffic

Do it: a candidate that cannot reach the index

Run order inside this file:
1. Do it: a candidate that cannot reach the index (source window 25)
2. Do it: a candidate that cannot reach the index (source window 27)

Prerequisites: demo_04_moving_one_tenant_beneath_the_index_by_hand_and_back.
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


# Original CLI workflow for step_01_a_candidate_that_cannot_reach_the_index.
COMMANDS_01 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars VECTOR_DEPLOYED_INDEX_ID=documind_chunks_nonesuch --quiet
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
curl -s -X POST "$CAND/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":3}' \\
  | python -c "
import sys, json
j = json.load(sys.stdin); s = j['stages']
print('candidate: backend', s['retrieval_backend'], '| vector_chunks', s['vector_chunks'], '| pool', s['pool'], '| answerable', j['answerable'], '| citations', len(j['citations']))
ok = s['retrieval_backend'] != 'vector' or s.get('vector_chunks', 0) > 0                   # smoke.py check 3a, by hand
print('the smoke would say:', '[PASS] vector tier' if ok else '[FAIL] vector tier  RETRIEVAL_BACKEND=vector and no chunk came from the index - the Firestore rung answered. make vector-status; make backfill-vectors APPLY=1')"
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="vector_search_fallback"' \\
  --project "$PROJECT" --freshness 10m --limit 2 --format='value(timestamp,jsonPayload.tenant,jsonPayload.error)'

"""

def step_01_a_candidate_that_cannot_reach_the_index(session):
    """Run Do it: a candidate that cannot reach the index at this checkpoint.

    Do it: a candidate that cannot reach the index

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one new revision, no traffic; one question to it; one log read; ask() from step 4).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: candidate: backend vector | vector_chunks 0 | pool 20 | answerable True | citations 3
    the smoke would say: [FAIL] vector tier  RETRIEVAL_BACKEND=vector and no chunk came from the index - the Firestore rung answered. make vector-status; make backfill-vectors APPLY=1
    2026-09-2xT1x:xx:xx.xxxxxxZ	acme	... documind_chunks_nonesuch ...
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_candidate_that_cannot_reach_the_index.
COMMANDS_02 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars VECTOR_DEPLOYED_INDEX_ID="$VECTOR_DEPLOYED_INDEX_ID" --quiet
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet
echo "template now: $(svc_env documind-api VECTOR_DEPLOYED_INDEX_ID)"
ask '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":3}'
gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format='value(status.traffic[].percent,status.traffic[].revisionName)'

"""

def step_02_a_candidate_that_cannot_reach_the_index(session):
    """Run Do it: a candidate that cannot reach the index at this checkpoint.

    Do it: a candidate that cannot reach the index

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the undo: the real name back on the template, the tag dropped, the live service asked once).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: template now: documind_chunks_v1
    backend vector | vector_chunks 20 | pool 20 | retrieve_ms 6xx | answerable True | first 1 hr_policy_2026.md | A confirmed employee in grade E3 ...
    100;documind-api-00048-xyz
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_a_candidate_that_cannot_reach_the_index),
        ('source_27', step_02_a_candidate_that_cannot_reach_the_index),
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
