"""Lesson 2.3: The fallback: the pool by retrieval score, flagged on the row, forced on a candidate

Do it, offline: the kit's fallback on the pool you saved Do it, on a candidate: a deadline no call can meet

Run order inside this file:
1. Do it, offline: the kit's fallback on the pool you saved (source window 17)
2. Do it, on a candidate: a deadline no call can meet (source window 19)
3. Do it, on a candidate: a deadline no call can meet (source window 21)

Prerequisites: demo_04_the_ranking_api_by_hand_the_api_s_pool_the_api_s_request_the_api_s_order.
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


def step_01_offline_the_kit_s_fallback_on_the_pool_you(session):
    """Run Do it, offline: the kit's fallback on the pool you saved at this checkpoint.

    Do it, offline: the kit's fallback on the pool you saved

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: nothing leaves the machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: rerank_fell_back: True | every chunk marked: True
    the pool by retrieval score, what the caller gets while the ranker is down:
       score 0.7xxx  pool # 1  NP-03     hr_policy_2026.md
       score 0.7xxx  pool # 2  ...       hr_policy_2026.md
       ...
    the ranker's five (step 4): ['NP-03', '...', '...', '...', '...']
    kept by the fallback: x of 5 | first is the same: True
    """
    import os, sys, json, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = [".", "services/rag-api"]
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.environ["PROJECT"])
    for k in ("RETRIEVAL_MODE", "RETRIEVAL_BACKEND", "RETRIEVAL_CURRENT_ONLY", "TOP_K_RETRIEVE", "RERANK_TIMEOUT_S", "SEMANTIC_CACHE"):
        if os.environ.get(k) == "":
            del os.environ[k]                                                # an empty export from an earlier names box means the default
    from retriever import _by_retrieval_score, rerank_fell_back              # the kit's own fallback, in this process
    d = json.load(open("/tmp/pool53.json"))
    pool, ranked = d["pool"], [i for i, _ in d["ranked"]]
    pos = {c["id"]: i + 1 for i, c in enumerate(pool)}
    stood_in = _by_retrieval_score([dict(c) for c in pool], 5)
    print("rerank_fell_back:", rerank_fell_back(stood_in), "| every chunk marked:", all(c.get("rerank_fallback") for c in stood_in))
    print("the pool by retrieval score, what the caller gets while the ranker is down:")
    for c in stood_in:
        print(f"   score {c['score']:.4f}  pool #{pos[c['id']]:>2}  {c['locator']:9} {c['source'][:28]}")
    print("the ranker's five (step 4):", [pool[i]["locator"] for i in ranked[:5]])
    print("kept by the fallback:", sum(1 for c in stood_in if c["id"] in {pool[i]["id"] for i in ranked[:5]}), "of 5 | first is the same:", stood_in[0]["id"] == pool[ranked[0]]["id"])

# Original CLI workflow for step_02_on_a_candidate_a_deadline_no_call_can_meet.
COMMANDS_02 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars RERANK_TIMEOUT_S=0.001 --quiet
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
curl -s -X POST "$CAND/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":5}' \\
  | python -c "import sys, json; j = json.load(sys.stdin); s = j['stages']; print('candidate: rerank_fallback', s.get('rerank_fallback', 0), '| rerank_ms', s['rerank_ms'], '| pool', s['pool'], '| answerable', j['answerable']); [print('   score %.4f  #%s  %s' % (c['score'], c['chunk_id'].rsplit('#', 1)[1], c['source_uri'].split('/')[-1][:26])) for c in j['citations']]"
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="rerank_fallback"' \\
  --project "$PROJECT" --freshness 10m --limit 3 --format='value(timestamp,jsonPayload.tenant,jsonPayload.error)'

"""

def step_02_on_a_candidate_a_deadline_no_call_can_meet(session):
    """Run Do it, on a candidate: a deadline no call can meet at this checkpoint.

    Do it, on a candidate: a deadline no call can meet

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one new revision, no traffic; one question to it; one log read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: candidate: rerank_fallback 1 | rerank_ms 1x | pool 20 | answerable True
       score 0.7xxx  #1  hr_policy_2026.md
       score 0.7xxx  #4  hr_policy_2026.md
       score 0.6xxx  #2  hr_policy_2026.md
    2026-09-2xT1x:xx:xx.xxxxxxZ	acme	DeadlineExceeded
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_on_a_candidate_a_deadline_no_call_can_meet.
COMMANDS_03 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --remove-env-vars RERANK_TIMEOUT_S --quiet
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet
curl -s -X POST "$API/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":3}' \\
  | python -c "import sys, json; j = json.load(sys.stdin); s = j['stages']; print('live: rerank_fallback', s.get('rerank_fallback', 0), '| rerank_ms', s['rerank_ms'], '| first score', round(j['citations'][0]['score'], 4))"
gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format='value(status.traffic[].percent,status.traffic[].revisionName)'

"""

def step_03_on_a_candidate_a_deadline_no_call_can_meet(session):
    """Run Do it, on a candidate: a deadline no call can meet at this checkpoint.

    Do it, on a candidate: a deadline no call can meet

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the undo: the variable removed, the tag dropped, the live service asked once).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: live: rerank_fallback 0 | rerank_ms 3xx | first score 0.9xxx
    100;documind-api-00044-xyz
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_offline_the_kit_s_fallback_on_the_pool_you),
        ('source_19', step_02_on_a_candidate_a_deadline_no_call_can_meet),
        ('source_21', step_03_on_a_candidate_a_deadline_no_call_can_meet),
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
