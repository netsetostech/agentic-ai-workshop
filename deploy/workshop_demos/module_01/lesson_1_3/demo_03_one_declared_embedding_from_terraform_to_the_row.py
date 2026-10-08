"""Lesson 1.3: One declared embedding, from Terraform to the row

All read-only. The first prints the worker's environment, the second asks the API what it is serving, the third reads the pair off the ledger rows the Versions table renders.

Run order inside this file:
1. Call it: three reads of one pair (source window 11)

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


# Original CLI workflow for step_01_three_reads_of_one_pair.
COMMANDS_01 = """gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" \\
  --format='value(spec.template.spec.containers[0].env)' | tr ';' '\\n' | grep -E 'EMBEDDING_MODEL|EMBEDDING_VERSION'

curl -s "$API/version" -H "Authorization: Bearer $(tok "$API")" \\
  | python -c "import json,sys; j=json.load(sys.stdin); print('api serves embedding', j['embedding'], '| generator', j['generator_model'], '| retrieval', j['retrieval_mode'], j['retrieval_backend'])"

curl -s "$API/v1/sources?tenant_id=acme" -H "Authorization: Bearer $(tok "$API")" \\
  | python -c "import json,sys; [print(f\\"{r['name']:44} chunks {r['chunks']:>4}  reused {r['reused']:>4}  embedded {r['embedded']:>4}  {r['embedding']}\\") for r in json.load(sys.stdin)['sources']]"

"""

def step_01_three_reads_of_one_pair(session):
    """Run Call it: three reads of one pair at this checkpoint.

    All read-only. The first prints the worker's environment, the second asks the API what it is serving, the third reads the pair off the ledger rows the Versions table renders.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {'name': 'EMBEDDING_MODEL', 'value': 'text-embedding-005'}
    {'name': 'EMBEDDING_VERSION', 'value': '1'}
    api serves embedding text-embedding-005@1 | generator gemini-3.6-flash | retrieval hybrid vector
    acme/code_on_wages_2019.pdf                  chunks   67  reused    0  embedded   67  text-embedding-005@1
    acme/dpdp_act_2023.pdf                       chunks   44  reused    0  embedded   44  text-embedding-005@1
    acme/hr_policy_2026.md                       chunks  283  reused    0  embedded  283  text-embedding-005@1
    ...
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_three_reads_of_one_pair),
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
