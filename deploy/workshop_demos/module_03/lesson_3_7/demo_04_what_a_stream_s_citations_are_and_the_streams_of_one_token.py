"""Lesson 3.7: What a stream's citations are, and the streams of one token

Do it: the empty pool as one token, then the stream rows

Run order inside this file:
1. Do it: the empty pool as one token, then the stream rows (source window 16)

Prerequisites: demo_03_a_stream_in_curl_the_raw_events_their_order_and_a_clock_on_each.
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


# Original CLI workflow for step_01_the_empty_pool_as_one_token_then_the_strea.
COMMANDS_01 = """curl -N -s -X POST "$API/v1/stream" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","filters":{"doc_type":"policy"}}' \\
  | python -c "
import sys, json
ev, n = None, {}
for line in sys.stdin:
    line = line.strip()
    if line.startswith('event: '): ev = line[7:]; n[ev] = n.get(ev, 0) + 1
    elif line.startswith('data: ') and ev == 'token': print('the one token:', json.loads(line[6:])['t'][:88], '...')
    elif line.startswith('data: ') and ev == 'done': d = json.loads(line[6:]); print('done: backend', d['backend'], '| tokens_in', d['tokens_in'], '| pool', d['stages']['pool'], '| rerank_ms', d['stages']['rerank_ms'], '| generate_ms', d['stages']['generate_ms'])
print('events:', n)"
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="stream"' \\
  --project "$PROJECT" --freshness 15m --limit 3 --format='value(jsonPayload.answerable,jsonPayload.model_backend,jsonPayload.tokens_in,jsonPayload.tokens_out,jsonPayload.pool,jsonPayload.guard,jsonPayload.brain)'

"""

def step_01_the_empty_pool_as_one_token_then_the_strea(session):
    """Run Do it: the empty pool as one token, then the stream rows at this checkpoint.

    Do it: the empty pool as one token, then the stream rows

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one stream that costs nothing; one log read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the one token: The corpus holds nothing near this question: no passage of this tenant's current documents was ...
    done: backend none | tokens_in 0 | pool 0 | rerank_ms 0 | generate_ms 0
    events: {'token': 1, 'done': 1}
    False	none	0	0	0	off	ui
    True	vertex	1xxx	4xx	20	off	ui
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_the_empty_pool_as_one_token_then_the_strea),
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
