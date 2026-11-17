"""Lesson 3.2: The Chat page: the answer to a join, and the thinking it billed

In the Chat page, signed in as yourself, ask exactly: I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve? Read the answer: the eval gate would want 45 and 60 in it. Then read the API's log for the last ten minutes.

Run order inside this file:
1. Do it: jn-03 in the Chat page, then its row (source window 6)

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


# Original CLI workflow for step_01_jn_03_in_the_chat_page_then_its_row.
COMMANDS_01 = """gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="stream"' \\
  --project "$PROJECT" --freshness 10m --limit 1 --format=json | python -c "
import sys, json
for e in json.load(sys.stdin):
    r = e['jsonPayload']
    print('stream | brain', r.get('brain'), '| tenant', r.get('tenant'), '| model', r.get('model'), '| pool', r.get('pool'),
          '| tokens_in', r.get('tokens_in'), '| tokens_out', r.get('tokens_out'), '| generate_ms', r.get('generate_ms'),
          '| Rs %.4f' % (85 * (r.get('cost_usd') or 0)))"

"""

def step_01_jn_03_in_the_chat_page_then_its_row(session):
    """Run Do it: jn-03 in the Chat page, then its row at this checkpoint.

    In the Chat page, signed in as yourself, ask exactly: I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve? Read the answer: the eval gate would want 45 and 60 in it. Then read the API's log for the last ten minutes.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, after the question in the Chat page (reads the API's log; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ui_stream.txt]
    """
    manual_checkpoint("In the deployed UI's Chat page, signed in as yourself, ask exactly: I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve? Wait for the cited answer, then type done to read its stream row from the API's log.")
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_jn_03_in_the_chat_page_then_its_row),
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
