"""Lesson 3.5: What an answer costs, and the failure that is not a refusal

The code

Run order inside this file:
1. The code (source window 36)

Prerequisites: demo_07_the_model_as_a_setting_the_global_client_a_tuned_endpoint_a_pin_and_a_router.
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


# Original CLI workflow for step_01_the_code.
COMMANDS_01 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars MAX_ANSWER_TOKENS=16 --quiet
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
curl -s -o /tmp/cand62.json -w "HTTP %{http_code}\\n" -X POST "$CAND/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":3}'; cat /tmp/cand62.json; echo
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND (jsonPayload.event="generation_truncated" OR jsonPayload.event="generation_unparsed")' \\
  --project "$PROJECT" --freshness 5m --limit 4 --format='value(timestamp,jsonPayload.event,jsonPayload.max_output_tokens,jsonPayload.tokens_out,jsonPayload.finish_reason)'
gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate --remove-env-vars MAX_ANSWER_TOKENS --quiet
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet
echo "template now: $(svc_env documind-api MAX_ANSWER_TOKENS)"; echo "(empty means unset: the default, 2048)"

"""

def step_01_the_code(session):
    """Run The code at this checkpoint.

    The code

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one new revision, no traffic; one question that fails on purpose; one log read; the undo).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: HTTP 502
    {"detail":"generation produced no parseable answer (MAX_TOKENS)"}
    2026-09-2xT1x:xx:xx.xxxxxxZ	generation_unparsed			MAX_TOKENS
    2026-09-2xT1x:xx:xx.xxxxxxZ	generation_truncated	16	1x
    template now:
    (empty means unset: the default, 2048)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_36', step_01_the_code),
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
