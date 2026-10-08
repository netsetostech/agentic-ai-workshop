"""Lesson 2.1: Filters: two keys, a 400 for everything else

Do it: four filters, four verdicts

Run order inside this file:
1. Do it: four filters, four verdicts (source window 16)

Prerequisites: demo_04_authorized_the_tenant_comes_from_identity_and_one_index_serves_three.
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


# Original CLI workflow for step_01_four_filters_four_verdicts.
COMMANDS_01 = """ask() { curl -s -w "\\nHTTP %{http_code}" -X POST $API/v1/query -H "Authorization: Bearer $(tok $API)" -H "Content-Type: application/json" \\
  -d "{\\"query\\":\\"What is the notice period for a confirmed E3?\\",\\"tenant_id\\":\\"acme\\",\\"stream\\":false,\\"filters\\":$1}" \\
  | python -c "import sys,json; raw=sys.stdin.read(); body,code=raw.rsplit('HTTP ',1); j=json.loads(body); print(code.strip(), '|', (j.get('detail') or f\\"answerable {j['answerable']} pool {j['stages']['pool']} | {j['answer'][:60]}\\"))"; }
ask '{"tenant_id":"zeta"}'
ask '{"doc_type":3}'
ask '{"doc_type":"policy"}'
ask '{"kind":"text"}'

"""

def step_01_four_filters_four_verdicts(session):
    """Run Do it: four filters, four verdicts at this checkpoint.

    Do it: four filters, four verdicts

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (two 400s cost nothing; two questions, paise).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 400 | unknown filter key(s) tenant_id; allowed: doc_type, kind
    400 | filter doc_type must be a non-empty string or a list of 1 to 5 of them
    200 | answerable False pool 0 | The corpus holds nothing near this question: no passage of this
    200 | answerable True pool 20 | A confirmed employee at grade E3 or above serves a notice period
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_four_filters_four_verdicts),
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
