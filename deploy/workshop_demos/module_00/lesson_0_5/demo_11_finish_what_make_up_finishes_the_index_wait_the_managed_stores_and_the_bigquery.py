"""Lesson 0.5: Finish what make up finishes: the index wait, the managed stores and the BigQuery views

The kit's own make up does not stop at the deploy. Its recipe names what follows, and this runbook has done most of it by hand: the drift check in T7, the cookie secret in F2, the builds in F3, the deploys in F4 to F8 and the roster in the step before this one: Four remain, and they are the kit's targets, run as they are. wait-index blocks until Firestore's composite indexes leave CREATING. managed-stores switches RAG Engine on once for the project, makes a corpus for each tenant whose text may travel (acme and zeta) and pins acme to rag_engine and zeta to vertex_search, so one deployment answers from all three stores; the data stores themselves were declared by Terraform (managed_search=true). bq-views-when-ready creates the usage views the admin console reads, once the table they read exists: the log sink's table appears only after the API has answered a first request, so on a new lane it prints that the views are deferred and you create them after the first answer (step 13). vector-status prints the index's own vector count, 0 until the first document is ingested. These targets read the state Phase 2 wrote, because the bucket and prefix are the kit's.

Run order inside this file:
1. Finish what make up finishes: the index wait, the managed stores and the BigQuery views (source window 56)

Prerequisites: demo_10_tenants_put_people_and_services_on_the_rosters.
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


# Original CLI workflow for step_01_finish_what_make_up_finishes_the_index_wai.
COMMANDS_01 = """cd "${DEMO_ROOT:?Restore ~/rag-env.sh}" &&
make wait-index managed-stores bq-views-when-ready vector-status \\
  PROJECT="${PROJECT:?Restore ~/rag-env.sh}" REGION="${REGION:?Restore ~/rag-env.sh}"

"""

def step_01_finish_what_make_up_finishes_the_index_wai(session):
    """Run Finish what make up finishes: the index wait, the managed stores and the BigQuery views at this checkpoint.

    The kit's own make up does not stop at the deploy. Its recipe names what follows, and this runbook has done most of it by hand: the drift check in T7, the cookie secret in F2, the builds in F3, the deploys in F4 to F8 and the roster in the step before this one: Four remain, and they are the kit's targets, run as they are. wait-index blocks until Firestore's composite indexes leave CREATING. managed-stores switches RAG Engine on once for the project, makes a corpus for each tenant whose text may travel (acme and zeta) and pins acme to rag_engine and zeta to vertex_search, so one deployment answers from all three stores; the data stores themselves were declared by Terraform (managed_search=true). bq-views-when-ready creates the usage views the admin console reads, once the table they read exists: the log sink's table appears only after the API has answered a first request, so on a new lane it prints that the views are deferred and you create them after the first answer (step 13). vector-status prints the index's own vector count, 0 until the first document is ingested. These targets read the state Phase 2 wrote, because the bucket and prefix are the kit's.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - the four closing targets, from the kit root.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_56', step_01_finish_what_make_up_finishes_the_index_wai),
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
