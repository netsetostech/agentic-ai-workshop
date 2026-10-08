"""Lesson 2.4: What the rung costs, where it cannot go, and the policy that sends a tenant home

A tenant's data_region says where its text may be held: any lets the managed mirror copy its current versions abroad, in keeps it on the kit's rows in India, and a missing or unknown value is in, because an unreadable policy is the strict one. retrieval_backend_for() holds every request's backend against it: a managed pin for an in tenant is served from the kit's own rung instead, the deployment's if that is vector or firestore, otherwise Firestore, with policy_fallback 1 on the row, which the warehouse sums into a column. The cell runs the two pure functions behind that decision offline; nothing leaves the machine.

Run order inside this file:
1. The policy that sends a tenant home (source window 42)

Prerequisites: demo_07_the_tier_from_the_rows_vector_status_backfill_vectors_and_the_rows_that_count_th.
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


def step_01_the_policy_that_sends_a_tenant_home(session):
    """Run The policy that sends a tenant home at this checkpoint.

    A tenant's data_region says where its text may be held: any lets the managed mirror copy its current versions abroad, in keeps it on the kit's rows in India, and a missing or unknown value is in, because an unreadable policy is the strict one. retrieval_backend_for() holds every request's backend against it: a managed pin for an in tenant is served from the kit's own rung instead, the deployment's if that is vector or firestore, otherwise Firestore, with policy_fallback 1 on the row, which the warehouse sums into a column. The cell runs the two pure functions behind that decision offline; nothing leaves the machine.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {}                       -> policy in
    {'data_region': 'any'}   -> policy any
    {'data_region': 'in'}    -> policy in
    {'data_region': 'eu'}    -> policy in
    in   tenant, a store in asia-south1  -> may hold it
    in   tenant, a store in us-central1  -> may not
    in   tenant, a store in global       -> may not
    any  tenant, a store in us-central1  -> may hold it
    """
    import sys
    sys.path.insert(0, ".")
    from shared.tenancy import policy_of, permits
    for doc in ({}, {"data_region": "any"}, {"data_region": "in"}, {"data_region": "eu"}):
        print(f"{str(doc):24} -> policy {policy_of(doc)}")
    for policy, region in (("in", "asia-south1"), ("in", "us-central1"), ("in", "global"), ("any", "us-central1")):
        print(f"{policy:4} tenant, a store in {region:12} -> {'may hold it' if permits(policy, region) else 'may not'}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_42', step_01_the_policy_that_sends_a_tenant_home),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
