"""Lesson 3.4: The answer's reserve, the retry, and the tokens on the rows

Do it: the day's tokens, and the retries there were not

Run order inside this file:
1. Do it: the day's tokens, and the retries there were not (source window 32)

Prerequisites: demo_06_a_dated_document_on_the_lane_the_header_s_date_the_rule_in_the_prompt_the_citati.
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


# Original CLI workflow for step_01_the_day_s_tokens_and_the_retries_there_wer.
COMMANDS_01 = """make usage PROJECT=$PROJECT HOURS=24 | sed -n '/^by tenant/,/^$/p'
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND (jsonPayload.event="generation_truncated" OR jsonPayload.event="context_budget_drop")' \\
  --project "$PROJECT" --freshness 24h --limit 5 --format='value(timestamp,jsonPayload.event,jsonPayload.tokens_out,jsonPayload.packed,jsonPayload.dropped)'

"""

def step_01_the_day_s_tokens_and_the_retries_there_wer(session):
    """Run Do it: the day's tokens, and the retries there were not at this checkpoint.

    Do it: the day's tokens, and the retries there were not

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: two log reads).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: by tenant
    tenant                 answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ------------------------------------------------------------------------------------
    acme                        NN     xxxxx     xxxx    0.0xxx      x.xx    4xxx   0.0x
    2026-09-2xT1x:xx:xx.xxxxxxZ	context_budget_drop		1x	x
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_32', step_01_the_day_s_tokens_and_the_retries_there_wer),
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
