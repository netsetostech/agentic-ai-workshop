"""Lesson 3.8: The answer: asked in Chat, streamed, and the row that names you

In the browser, open Chat and ask: What colour badge do visitors wear at the Pune warehouse? The sources arrive first and the answer streams after them. The answer ends with a pill. Hover over it to see the note's clause, and open Sources under the answer. Then ask the same question from the shell and read the two newest rows:

Run order inside this file:
1. Do it: ask in the browser, ask from the shell, read both rows (source window 23)

Prerequisites: demo_04_the_upload_a_note_you_write_uploaded_in_the_browser_followed_to_the_ledger.
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


# Original CLI workflow for step_01_ask_in_the_browser_ask_from_the_shell_read.
COMMANDS_01 = """curl -s -X POST "$API/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"What colour badge do visitors wear at the Pune warehouse?","tenant_id":"acme","stream":false}' \\
  | python -c "import json,sys; raw=sys.stdin.read(); j=json.loads(raw) if raw.startswith('{') else {'answer': 'not JSON: ' + raw[:80], 'citations': []}; print('from the shell:', j.get('answer', j)[:70], '|', [c['source_uri'].split('/')[-1] for c in j.get('citations', [])[:1]])"
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND (jsonPayload.event="stream" OR jsonPayload.event="query")' \\
  --project "$PROJECT" --freshness 15m --limit 2 --format='value(timestamp,jsonPayload.event,jsonPayload.user,jsonPayload.brain,jsonPayload.tenant,jsonPayload.pool)'

"""

def step_01_ask_in_the_browser_ask_from_the_shell_read(session):
    """Run Do it: ask in the browser, ask from the shell, read both rows at this checkpoint.

    In the browser, open Chat and ask: What colour badge do visitors wear at the Pune warehouse? The sources arrive first and the answer streams after them. The answer ends with a pill. Hover over it to see the note's clause, and open Sources under the answer. Then ask the same question from the shell and read the two newest rows:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one question, a rupee; one log read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: from the shell: Every visitor to the Pune warehouse wears an amber badge, issued at gate | ['pune_visitor_rules.md']
    2026-09-2xT1x:xx:xx.xxxxxxZ	query	documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com	ui	acme	20
    2026-09-2xT1x:xx:xx.xxxxxxZ	stream	you@example.com	ui	acme	20
    """
    manual_checkpoint('In the deployed UI Chat, ask the visitor-badge question from this lesson and wait for the cited answer. Type done to compare the browser and operator API records.')
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_ask_in_the_browser_ask_from_the_shell_read),
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
