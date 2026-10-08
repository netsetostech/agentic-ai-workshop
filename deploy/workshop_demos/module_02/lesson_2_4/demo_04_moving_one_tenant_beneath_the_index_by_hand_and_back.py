"""Lesson 2.4: Moving one tenant beneath the index by hand, and back

Do it: pin acme beneath the index, and wait for the API to notice Do it: the same predicates on the chosen rung, and two tenants that do not cross Do it: the smoke's line for a chosen rung, then the pin back

Run order inside this file:
1. Do it: pin acme beneath the index, and wait for the API to notice (source window 16)
2. Do it: the same predicates on the chosen rung, and two tenants that do not cross (source window 18)
3. Do it: the smoke's line for a chosen rung, then the pin back (source window 20)

Prerequisites: demo_03_the_firestore_rung_by_hand_the_api_s_three_predicates_on_firestore_s_own_vector.
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


# Original CLI workflow for step_01_pin_acme_beneath_the_index_and_wait_for_th.
COMMANDS_01 = """python commands/lane.py tenant-backend acme firestore          # the same as: make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=firestore
ask() { curl -s -X POST "$API/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" -d "$1" \\
  | python -c "import sys, json; j = json.load(sys.stdin); s = j.get('stages', {}); c = j.get('citations') or []; print('backend', s.get('retrieval_backend'), '| vector_chunks', s.get('vector_chunks'), '| pool', s.get('pool'), '| retrieve_ms', s.get('retrieve_ms'), '| answerable', j.get('answerable'), '| first', (c[0]['chunk_id'].rsplit('#', 1)[1] + ' ' + c[0]['source_uri'].split('/')[-1][:22]) if c else '-', '|', j.get('answer', '')[:60])"; }
for i in $(seq 1 9); do
  OUT="$(ask '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":3}')"; echo "$OUT"
  case "$OUT" in *"backend firestore"*) break;; esac; sleep 10                     # the pin is read once a minute
done

"""

def step_01_pin_acme_beneath_the_index_and_wait_for_th(session):
    """Run Do it: pin acme beneath the index, and wait for the API to notice at this checkpoint.

    Do it: pin acme beneath the index, and wait for the API to notice

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (one field written; up to nine questions while the minute passes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme: retrieval_backend=firestore
    backend vector | vector_chunks 20 | pool 20 | retrieve_ms 6xx | answerable True | first 1 hr_policy_2026.md | A confirmed employee in grade E3 ...
    backend firestore | vector_chunks 0 | pool 20 | retrieve_ms 5xx | answerable True | first 1 hr_policy_2026.md | A confirmed employee in grade E3 ...
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_same_predicates_on_the_chosen_rung_and.
COMMANDS_02 = """ask '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":3,"filters":{"doc_type":"policy"}}'
ask '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":3,"filters":{"kind":"text"}}'
ask '{"query":"What is the per-trip cap on domestic travel reimbursement?","tenant_id":"acme","stream":false,"top_k":3}'
ask '{"query":"What is the per-trip cap on travel reimbursement?","tenant_id":"zeta","stream":false,"top_k":3}'

"""

def step_02_the_same_predicates_on_the_chosen_rung_and(session):
    """Run Do it: the same predicates on the chosen rung, and two tenants that do not cross at this checkpoint.

    Do it: the same predicates on the chosen rung, and two tenants that do not cross

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (four questions, a few rupees).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: backend firestore | vector_chunks 0 | pool 0 | retrieve_ms 4xx | answerable False | first - | The corpus holds nothing near this question: no passage of this
    backend firestore | vector_chunks 0 | pool 20 | retrieve_ms 5xx | answerable True | first 1 hr_policy_2026.md | A confirmed employee in grade E3 ...
    backend firestore | vector_chunks 0 | pool 20 | retrieve_ms 5xx | answerable True | first x hr_policy_2026.md | ... Rs 40,000 ...
    backend vector | vector_chunks 20 | pool 20 | retrieve_ms 6xx | answerable True | first x hr_policy_zeta_2026.md | ... Rs 25,000 ...
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_smoke_s_line_for_a_chosen_rung_then_th.
COMMANDS_03 = """set +o pipefail   # as the page runs it: make smoke's own status does not stop this filtered read
DOCUMIND_PROJECT=$PROJECT DOCUMIND_API_URL=$API DOCUMIND_TENANT=acme DOCUMIND_IMPERSONATE_SA=documind-ui-sa@$PROJECT.iam.gserviceaccount.com make smoke 2>&1 | grep "vector tier"
python commands/lane.py tenant-backend acme vector
for i in $(seq 1 9); do OUT="$(ask '{"query":"What is the notice period for a confirmed E3?","tenant_id":"acme","stream":false,"top_k":3}')"; case "$OUT" in *"backend vector"*) echo "$OUT"; break;; esac; sleep 10; done
DOCUMIND_PROJECT=$PROJECT DOCUMIND_API_URL=$API DOCUMIND_TENANT=acme DOCUMIND_IMPERSONATE_SA=documind-ui-sa@$PROJECT.iam.gserviceaccount.com make smoke 2>&1 | grep "vector tier"

"""

def step_03_the_smoke_s_line_for_a_chosen_rung_then_th(session):
    """Run Do it: the smoke's line for a chosen rung, then the pin back at this checkpoint.

    Do it: the smoke's line for a chosen rung, then the pin back

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (two smokes, a rupee each; one field written).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [ -- ] vector tier  this request ran on firestore — skipped
    acme: retrieval_backend=vector
    backend vector | vector_chunks 20 | pool 20 | retrieve_ms 6xx | answerable True | first 1 hr_policy_2026.md | A confirmed employee in grade E3 ...
      [PASS] vector tier  20 of 20 chunks came from the index
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_pin_acme_beneath_the_index_and_wait_for_th),
        ('source_18', step_02_the_same_predicates_on_the_chosen_rung_and),
        ('source_20', step_03_the_smoke_s_line_for_a_chosen_rung_then_th),
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
