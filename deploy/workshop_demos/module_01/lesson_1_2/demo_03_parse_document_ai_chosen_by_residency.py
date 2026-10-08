"""Lesson 1.2: Parse: Document AI, chosen by residency

Two read-only calls. The first prints the worker's environment, where the residency and the processor id live. The second asks the Document AI API to list the processors in each of the two possible locations; exactly one location will list documind-parser.

Run order inside this file:
1. Call it: which reader does your lane have? (source window 9)

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


# Original CLI workflow for step_01_which_reader_does_your_lane_have.
COMMANDS_01 = """gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" \\
  --format='value(spec.template.spec.containers[0].env)' | tr ';' '\\n' | grep -E 'RESIDENCY|DOCAI_PROCESSOR_ID'

for LOC in us asia-south1; do
  echo "== $LOC =="
  curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \\
    "https://$LOC-documentai.googleapis.com/v1/projects/$NUMBER/locations/$LOC/processors" \\
    | python -c "import json,sys; j=json.load(sys.stdin); [print(p['displayName'], p['type'], p['state']) for p in j.get('processors', [])] or print('(none)')"
done

"""

def step_01_which_reader_does_your_lane_have(session):
    """Run Call it: which reader does your lane have? at this checkpoint.

    Two read-only calls. The first prints the worker's environment, where the residency and the processor id live. The second asks the Document AI API to list the processors in each of the two possible locations; exactly one location will list documind-parser.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {'name': 'RESIDENCY', 'value': 'us'}
    {'name': 'DOCAI_PROCESSOR_ID', 'value': 'a1b2c3d4e5f6a7b8'}
    == us ==
    documind-parser LAYOUT_PARSER_PROCESSOR ENABLED
    == asia-south1 ==
    (none)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_which_reader_does_your_lane_have),
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
