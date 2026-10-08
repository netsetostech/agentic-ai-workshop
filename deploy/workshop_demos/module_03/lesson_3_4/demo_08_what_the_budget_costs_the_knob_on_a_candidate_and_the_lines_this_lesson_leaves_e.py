"""Lesson 3.4: What the budget costs, the knob on a candidate, and the lines this lesson leaves empty

max_context_tokens is a setting, so the way to see the drop on the live corpus without touching the live service is a candidate revision, as in lessons 2.2 to 2.4: a budget of 600 tokens leaves room for about three handbook sections after the fixed prompt, so the same question at top_k 5 packs three, drops two, logs the drop, and answers from what it packed. The variable is not set on the live service, so the undo removes it and the default returns.

Run order inside this file:
1. The knob: a budget too small, on a candidate that takes no traffic (source window 34)

Prerequisites: demo_07_the_answer_s_reserve_the_retry_and_the_tokens_on_the_rows.
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


# Original CLI workflow for step_01_the_knob_a_budget_too_small_on_a_candidate.
COMMANDS_01 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars MAX_CONTEXT_TOKENS=600 --quiet
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
curl -s -X POST "$CAND/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":5}' \\
  | python -c "import sys, json; j = json.load(sys.stdin); print('candidate: tokens_in', j['tokens_in'], '| citations', len(j['citations']), '| answerable', j['answerable'], '| pool', j['stages']['pool'])"
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="context_budget_drop"' \\
  --project "$PROJECT" --freshness 5m --limit 2 --format='value(timestamp,jsonPayload.packed,jsonPayload.dropped)'
gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate --remove-env-vars MAX_CONTEXT_TOKENS --quiet
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet
echo "template now: ${MAX_CONTEXT_TOKENS:-$(svc_env documind-api MAX_CONTEXT_TOKENS)}"; echo "(empty means unset: the default, 8000)"

"""

def step_01_the_knob_a_budget_too_small_on_a_candidate(session):
    """Run The knob: a budget too small, on a candidate that takes no traffic at this checkpoint.

    max_context_tokens is a setting, so the way to see the drop on the live corpus without touching the live service is a candidate revision, as in lessons 2.2 to 2.4: a budget of 600 tokens leaves room for about three handbook sections after the fixed prompt, so the same question at top_k 5 packs three, drops two, logs the drop, and answers from what it packed. The variable is not set on the live service, so the undo removes it and the default returns.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one new revision, no traffic; one question; one log read; then the undo).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: candidate: tokens_in 6xx | citations 2 | answerable True | pool 20
    2026-09-2xT1x:xx:xx.xxxxxxZ	3	2
    template now:
    (empty means unset: the default, 8000)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_the_knob_a_budget_too_small_on_a_candidate),
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
