"""Lesson 3.5: Three refusals: the model's twice, the API's once, and how their envelopes differ

Do it: three questions, three envelopes, three rows

Run order inside this file:
1. Do it: three questions, three envelopes, three rows (source window 21)

Prerequisites: demo_04_one_answer_from_the_lane_field_by_field_with_every_quote_checked_against_its_row.
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


# Original CLI workflow for step_01_three_questions_three_envelopes_three_rows.
COMMANDS_01 = """ask() { curl -s -X POST "$API/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" -d "$1" \\
  | python -c "import sys, json; j = json.load(sys.stdin); print('answerable', j['answerable'], '| confidence', j['confidence'], '| citations', len(j['citations']), '| backend', j['backend'], '| tokens', j['tokens_in'], '+', j['tokens_out'], '| cost_usd', j['cost_usd'], '| pool', j['stages']['pool'], '|', j['answer'][:64])"; }
ask '{"query":"What is the notice period at Globex for a confirmed employee?","tenant_id":"globex","stream":false,"top_k":3}'
ask '{"query":"What was ACME\\u0027s revenue in FY2024?","tenant_id":"acme","stream":false,"top_k":3}'
ask '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":3,"filters":{"doc_type":"policy"}}'
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" AND jsonPayload.unanswerable_flag=1' \\
  --project "$PROJECT" --freshness 5m --limit 3 --format='value(jsonPayload.tenant,jsonPayload.answerable,jsonPayload.model_backend,jsonPayload.tokens_in,jsonPayload.cost_usd)'

"""

def step_01_three_questions_three_envelopes_three_rows(session):
    """Run Do it: three questions, three envelopes, three rows at this checkpoint.

    Do it: three questions, three envelopes, three rows

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (three questions, two of them model calls: a rupee; one log read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: answerable False | confidence low | citations 0 | backend vertex | tokens 1xxx + 1xx | cost_usd 0.00xxxx | pool 20 | The provided context does not contain information about Globex's not
    answerable False | confidence low | citations 0 | backend vertex | tokens 1xxx + 1xx | cost_usd 0.00xxxx | pool 20 | The context covers FY2025 and FY2026; it does not state the revenue f
    answerable False | confidence low | citations 0 | backend none | tokens 0 + 0 | cost_usd 0.0 | pool 0 | The corpus holds nothing near this question: no passage of this tena
    acme	False	none	0	0.0
    acme	False	vertex	1xxx	0.00xxxx
    globex	False	vertex	1xxx	0.00xxxx
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_three_questions_three_envelopes_three_rows),
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
