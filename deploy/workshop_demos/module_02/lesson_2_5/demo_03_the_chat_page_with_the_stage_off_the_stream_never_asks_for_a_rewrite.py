"""Lesson 2.5: The Chat page with the stage off: the stream never asks for a rewrite

In the Chat page, signed in as yourself, ask: How much can I claim per trip for domestic travel? It is a paraphrase of golden row lk-01, whose answer must contain 40,000. Then read the API's log for the last ten minutes.

Run order inside this file:
1. Do it: a paraphrase in the Chat page, then the log (source window 10)

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


# Original CLI workflow for step_01_a_paraphrase_in_the_chat_page_then_the_log.
COMMANDS_01 = """gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND (jsonPayload.event="stream" OR jsonPayload.event="query_rewrite")' \\
  --project "$PROJECT" --freshness 10m --limit 5 --format=json | python -c "
import sys, json
rows = [e['jsonPayload'] for e in json.load(sys.stdin)]
for r in rows:
    if r['event'] == 'stream':
        print('stream | brain', r.get('brain'), '| tenant', r.get('tenant'), '| pool', r.get('pool'), '| retrieve_ms', r.get('retrieve_ms'),
              '| answerable', r.get('answerable'), '| Rs %.2f' % (85 * (r.get('cost_usd') or 0)))
print('query_rewrite lines in the last 10 minutes:', sum(1 for r in rows if r['event'] == 'query_rewrite'))"

"""

def step_01_a_paraphrase_in_the_chat_page_then_the_log(session):
    """Run Do it: a paraphrase in the Chat page, then the log at this checkpoint.

    In the Chat page, signed in as yourself, ask: How much can I claim per trip for domestic travel? It is a paraphrase of golden row lk-01, whose answer must contain 40,000. Then read the API's log for the last ten minutes.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, after the question in the Chat page (reads the API's log; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ui.txt]
    """
    manual_checkpoint("In the deployed UI's Chat page, signed in as yourself, ask: How much can I claim per trip for domestic travel? Wait for the cited answer, then type done to read the API's log for the minutes since.")
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_a_paraphrase_in_the_chat_page_then_the_log),
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
