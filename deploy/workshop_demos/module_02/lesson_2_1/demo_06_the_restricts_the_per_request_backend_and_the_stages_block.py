"""Lesson 2.1: The restricts, the per-request backend, and the stages block

Do it: the tenant's pin and policy, then a full stages block, Rs 0 plus one question

Run order inside this file:
1. Do it: the tenant's pin and policy, then a full stages block, Rs 0 plus one question (source window 21)

Prerequisites: demo_05_filters_two_keys_a_400_for_everything_else.
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


# Original CLI workflow for step_01_the_tenant_s_pin_and_policy_then_a_full_st.
COMMANDS_01 = """python commands/lane.py tenant-backend acme
python commands/lane.py tenant-policy acme

curl -s -X POST $API/v1/query -H "Authorization: Bearer $(tok $API)" -H "Content-Type: application/json" \\
  -d '{"query":"How many days of earned leave can I carry forward?","tenant_id":"acme","stream":false,"top_k":3}' \\
  | python -c "import json,sys; j=json.load(sys.stdin); print(json.dumps(j['stages'], indent=1)); print('citations', len(j['citations']), '| cache_hit', j.get('cache_hit'), '| latency_ms', j['latency_ms'])"

"""

def step_01_the_tenant_s_pin_and_policy_then_a_full_st(session):
    """Run Do it: the tenant's pin and policy, then a full stages block, Rs 0 plus one question at this checkpoint.

    Do it: the tenant's pin and policy, then a full stages block, Rs 0 plus one question

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (two reads, one question).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme: retrieval_backend=vector
    acme: data_region=any
    {
     "policy_fallback": 0,
     "retrieval_backend": "vector",
     "retrieve_ms": 612,
     "pool": 20,
     "graph_chunks": 0,
     "managed_chunks": 0,
     "vector_chunks": 20,
     "rerank_ms": 388,
     "generate_ms": 1742
    }
    citations 3 | cache_hit none | latency_ms 2760
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_the_tenant_s_pin_and_policy_then_a_full_st),
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
