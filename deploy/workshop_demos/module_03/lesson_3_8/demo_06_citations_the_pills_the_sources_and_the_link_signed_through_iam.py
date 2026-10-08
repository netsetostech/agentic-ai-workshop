"""Lesson 3.8: Citations: the pills, the sources, and the link signed through IAM

In the browser, under the answer from step 5, open Sources and click Open source on the note. A new tab shows the note's text from the bucket, through a link that stops working in 15 minutes. Then capture the same answer as a transcript and paste it into the renderer in step 1:

Run order inside this file:
1. Do it: open the source, then render your own transcript (source window 28)

Prerequisites: demo_05_the_answer_asked_in_chat_streamed_and_the_row_that_names_you.
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


# Original CLI workflow for step_01_open_the_source_then_render_your_own_trans.
COMMANDS_01 = """curl -N -s -X POST "$API/v1/stream" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"What colour badge do visitors wear at the Pune warehouse?","tenant_id":"acme","top_k":5}' > /tmp/stream64.txt
echo "citation events: $(grep -c '^event: citation' /tmp/stream64.txt) | tokens: $(grep -c '^event: token' /tmp/stream64.txt) | done: $(grep -c '^event: done' /tmp/stream64.txt)"
grep -m1 '^data: {"n": 1' /tmp/stream64.txt | cut -c7- \\
  | python -c "import json,sys; d=json.load(sys.stdin); print('first citation:', d['source'].split('/')[-1], '| kind', d['kind'], '| page', d['page'], '| quote', repr(d['quote'][:48]))"
cat /tmp/stream64.txt

"""

def step_01_open_the_source_then_render_your_own_trans(session):
    """Run Do it: open the source, then render your own transcript at this checkpoint.

    In the browser, under the answer from step 5, open Sources and click Open source on the note. A new tab shows the note's text from the bucket, through a link that stops working in 15 minutes. Then capture the same answer as a transcript and paste it into the renderer in step 1:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one stream, a rupee).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: citation events: 5 | tokens: NN | done: 1
    first citation: pune_visitor_rules.md | kind text | page None | quote 'VR-01 - Badges\\nEvery visitor to the Pune warehou'
    ...
    """
    manual_checkpoint("Open the answer's citation/source in the UI and inspect the signed link. Type done to render and inspect the transcript from Python.")
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_28', step_01_open_the_source_then_render_your_own_trans),
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
