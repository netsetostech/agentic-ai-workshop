"""Lesson 3.7: A failure forced on a candidate: the ranker silent, the stream still served, the line in the log

Do it: the ranker silent for one revision, the stream read, the line read, the undo

Run order inside this file:
1. Do it: the ranker silent for one revision, the stream read, the line read, the undo (source window 27)

Prerequisites: demo_05_the_guard_a_prompt_refused_before_the_stream_an_answer_held_until_it_is_screened.
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


# Original CLI workflow for step_01_the_ranker_silent_for_one_revision_the_str.
COMMANDS_01 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars RERANK_TIMEOUT_S=0.001 --quiet
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
curl -N -s -X POST "$CAND/v1/stream" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","top_k":3}' \\
  | python -c "
import sys, json
ev, n, text = None, {}, []
for line in sys.stdin:
    line = line.strip()
    if line.startswith('event: '): ev = line[7:]; n[ev] = n.get(ev, 0) + 1
    elif line.startswith('data: ') and ev == 'token': text.append(json.loads(line[6:])['t'])
    elif line.startswith('data: ') and ev == 'done': s = json.loads(line[6:])['stages']; print('done.stages: rerank_fallback', s.get('rerank_fallback', 0), '| rerank_ms', s['rerank_ms'], '| pool', s['pool'], '| vector_chunks', s['vector_chunks'])
print('events:', n, '| the answer:', ' '.join(''.join(text).split())[:70], '...')"
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="rerank_fallback"' \\
  --project "$PROJECT" --freshness 10m --limit 2 --format='value(timestamp,jsonPayload.tenant,jsonPayload.error)'
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="telemetry_not_instrumented"' \\
  --project "$PROJECT" --freshness 7d --limit 1 --format='value(timestamp,jsonPayload.error)'
gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate --remove-env-vars RERANK_TIMEOUT_S --quiet
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet

"""

def step_01_the_ranker_silent_for_one_revision_the_str(session):
    """Run Do it: the ranker silent for one revision, the stream read, the line read, the undo at this checkpoint.

    Do it: the ranker silent for one revision, the stream read, the line read, the undo

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one new revision, no traffic; one stream to it; two log reads; the undo).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: done.stages: rerank_fallback 1 | rerank_ms 1x | pool 20 | vector_chunks 20
    events: {'citation': 3, 'token': 3x, 'done': 1} | the answer: A confirmed employee in grade E3 must serve a notice period of ...
    2026-09-2xT1x:xx:xx.xxxxxxZ	acme	DeadlineExceeded
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_the_ranker_silent_for_one_revision_the_str),
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
