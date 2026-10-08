"""Lesson 2.2: The knob: hybrid on a candidate that takes no traffic, compared, then removed

Do it: hybrid on a candidate, the same two questions to both revisions, then undo

Run order inside this file:
1. Do it: hybrid on a candidate, the same two questions to both revisions, then undo (source window 31)
2. Do it: hybrid on a candidate, the same two questions to both revisions, then undo (source window 33)
3. Do it: hybrid on a candidate, the same two questions to both revisions, then undo (source window 35)

Prerequisites: demo_06_the_ablation_one_knob_per_arm_no_model_in_the_loop.
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


# Original CLI workflow for step_01_hybrid_on_a_candidate_the_same_two_questio.
COMMANDS_01 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --update-env-vars RETRIEVAL_MODE=hybrid --quiet
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
for U in "$API" "$CAND"; do
  curl -s "$U/version" -H "Authorization: Bearer $(tok "$API")" \\
    | python -c "import sys, json; j = json.load(sys.stdin); print('$U'.split('//')[1].split('.')[0].ljust(36), 'mode', j['retrieval_mode'], '| backend', j['retrieval_backend'])"
done

"""

def step_01_hybrid_on_a_candidate_the_same_two_questio(session):
    """Run Do it: hybrid on a candidate, the same two questions to both revisions, then undo at this checkpoint.

    Do it: hybrid on a candidate, the same two questions to both revisions, then undo

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one new revision, no traffic; two version reads).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-api-NUMBER                  mode dense | backend vector
    candidate---documind-api-NUMBER      mode hybrid | backend vector
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_hybrid_on_a_candidate_the_same_two_questio.
COMMANDS_02 = """ask() { curl -s -X POST "$1/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d "{\\"query\\":\\"$2\\",\\"tenant_id\\":\\"acme\\",\\"stream\\":false,\\"top_k\\":3}" \\
  | python -c "import sys, json; j = json.load(sys.stdin); s = j['stages']; print('  ', '$1'.split('//')[1].split('---')[0].split('.')[0][:9].ljust(10), [c['chunk_id'].rsplit('#', 1)[1].rjust(3) + ' ' + c['source_uri'].split('/')[-1][:22] for c in j['citations']], '| retrieve_ms', s['retrieve_ms'], '| pool', s['pool'], '| vector_chunks', s['vector_chunks'])"; }
for Q in "What is the total payable on invoice INV-2026-0412?" "What is the notice period for a confirmed E3?"; do
  echo "$Q"; ask "$API" "$Q"; ask "$CAND" "$Q"
done

"""

def step_02_hybrid_on_a_candidate_the_same_two_questio(session):
    """Run Do it: hybrid on a candidate, the same two questions to both revisions, then undo at this checkpoint.

    Do it: hybrid on a candidate, the same two questions to both revisions, then undo

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (four questions, one or two rupees).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: What is the total payable on invoice INV-2026-0412?
       documind-  ['  0 inv_2026_0412.md', ' 36 cgst_act_2017.pdf', ...] | retrieve_ms 6xx | pool 20 | vector_chunks 20
       candidate  ['  0 inv_2026_0412.md', ' 36 cgst_act_2017.pdf', ...] | retrieve_ms 7xx | pool 20 | vector_chunks 20
    What is the notice period for a confirmed E3?
       documind-  ['  1 hr_policy_2026.md', '  4 hr_policy_2026.md', '  2 hr_policy_2026.md'] | retrieve_ms 6xx | pool 20 | vector_chunks 20
       candidate  ['  1 hr_policy_2026.md', '  4 hr_policy_2026.md', '  2 hr_policy_2026.md'] | retrieve_ms 7xx | pool 20 | vector_chunks 20
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_hybrid_on_a_candidate_the_same_two_questio.
COMMANDS_03 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\
  --remove-env-vars RETRIEVAL_MODE --quiet
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet
curl -s "$API/version" -H "Authorization: Bearer $(tok "$API")" | python -c "import sys, json; print('live mode:', json.load(sys.stdin)['retrieval_mode'])"
gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format='value(status.traffic[].percent,status.traffic[].revisionName)'

"""

def step_03_hybrid_on_a_candidate_the_same_two_questio(session):
    """Run Do it: hybrid on a candidate, the same two questions to both revisions, then undo at this checkpoint.

    Do it: hybrid on a candidate, the same two questions to both revisions, then undo

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the undo: the variable removed, the tag dropped, the live mode read again).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: live mode: dense
    100;documind-api-00042-xyz
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_hybrid_on_a_candidate_the_same_two_questio),
        ('source_33', step_02_hybrid_on_a_candidate_the_same_two_questio),
        ('source_35', step_03_hybrid_on_a_candidate_the_same_two_questio),
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
