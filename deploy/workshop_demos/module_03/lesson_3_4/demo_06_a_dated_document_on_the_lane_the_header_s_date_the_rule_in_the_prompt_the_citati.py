"""Lesson 3.4: A dated document on the lane: the header's date, the rule in the prompt, the citation event

Do it: the dated revision in, the stream read, revision 1 back

Run order inside this file:
1. Do it: the dated revision in, the stream read, revision 1 back (source window 27)

Prerequisites: demo_05_one_answer_s_tokens_the_packed_set_s_estimate_the_model_s_count_and_the_price.
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


# Original CLI workflow for step_01_the_dated_revision_in_the_stream_read_revi.
COMMANDS_01 = """worker_line() { for i in $(seq 1 30); do sleep 10
  LINE="$(gcloud logging read "resource.type=\\"cloud_run_revision\\" AND resource.labels.service_name=\\"documind-ingest\\" AND (jsonPayload.event=\\"ingest_ok\\" OR jsonPayload.event=\\"ingest_reactivated\\") AND (jsonPayload.tenant=\\"acme\\" OR jsonPayload.doc_key:\\"acme_\\") AND timestamp>=\\"$1\\"" \\
    --project "$PROJECT" --limit 1 --format='value(jsonPayload.event,jsonPayload.chunks,jsonPayload.embedded,jsonPayload.effective_from)')"
  [ -n "$LINE" ] && { echo ">> event chunks embedded effective_from: $LINE"; return; }; done; echo ">> no worker line in five minutes"; }
SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; gcloud storage cp evals/demo/smoke_note_v2.md "gs://$PROJECT-uploads/acme/smoke_note.md"; worker_line "$SINCE"
curl -N -s -X POST "$API/v1/stream" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"Where is the smoke lantern kept, and from when?","tenant_id":"acme"}' \\
  | python -c "
import sys, json
ev, text = None, []
for line in sys.stdin:
    line = line.strip()
    if line.startswith('event: '): ev = line[7:]
    elif line.startswith('data: ') and ev == 'citation':
        d = json.loads(line[6:]); print('citation', d['n'], d['source'].split('/')[-1], '| effective_from', d.get('effective_from'), '| quote', repr(d['quote'][:50]))
    elif line.startswith('data: ') and ev == 'token': text.append(json.loads(line[6:])['t'])
    elif line.startswith('data: ') and ev == 'done':
        d = json.loads(line[6:]); print('done: tokens_in', d.get('tokens_in'), '| tokens_out', d.get('tokens_out'), '| latency_ms', d.get('latency_ms'), '| the price is on the row, not in the event')
print('answer:', ''.join(text)[:160])"
SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; gcloud storage cp evals/demo/smoke_note_v1.md "gs://$PROJECT-uploads/acme/smoke_note.md"; worker_line "$SINCE"

"""

def step_01_the_dated_revision_in_the_stream_read_revi(session):
    """Run Do it: the dated revision in, the stream read, revision 1 back at this checkpoint.

    Do it: the dated revision in, the stream read, revision 1 back

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (one upload, one streamed question, one upload; paise).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> event chunks embedded effective_from: ingest_reactivated	3	0	2026-10-01
    citation 1 smoke_note.md | effective_from 2026-10-01 | quote 'The smoke lantern is kept in bay 7 of the Pune wa'
    done: tokens_in 1xxx | tokens_out 3xx | latency_ms 2xxx | the price is on the row, not in the event
    answer: The smoke lantern is kept in bay 7 of the Pune warehouse [1], effective from 1 October 2026 ...
    >> event chunks embedded effective_from: ingest_reactivated	3	0	None
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_the_dated_revision_in_the_stream_read_revi),
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
