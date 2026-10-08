"""Lesson 0.3: Seven services, and the account each runs as

The first proof: the services are up, and each runs as the account step 4 said it would. Cloud Run keeps the account a service runs as on the service itself. Listing the services with that one field beside the name is the whole check: 7 rows, each with its own account, matching the table in step 4. Step 5 left one fact open: the deployed index's machine follows the index's shard size, and the kit lets the service choose it. Read both from the live lane; step 10 prices the row that matches.

Run order inside this file:
1. Seven services, and the account each runs as (source window 49)
2. The shard size the service chose (source window 51)

Prerequisites: demo_07_make_up_apply_that_plan_then_build_deploy_and_seed.
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


# Original CLI workflow for step_01_seven_services_and_the_account_each_runs_a.
COMMANDS_01 = """gcloud run services list --project "$PROJECT" --region "$REGION" \\
  --format='table(metadata.name:label=SERVICE, spec.template.spec.serviceAccountName:label=RUNS_AS)'
gcloud run services list --project "$PROJECT" --region "$REGION" --format='value(metadata.name)' | wc -l

"""

def step_01_seven_services_and_the_account_each_runs_a(session):
    """Run Seven services, and the account each runs as at this checkpoint.

    The first proof: the services are up, and each runs as the account step 4 said it would. Cloud Run keeps the account a service runs as on the service itself. Listing the services with that one field beside the name is the whole check: 7 rows, each with its own account, matching the table in step 4.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_shard_size_the_service_chose.
COMMANDS_02 = """IDX=$(terraform -chdir=terraform output -raw vector_index_name); EP=$(terraform -chdir=terraform output -raw vector_index_endpoint)
gcloud ai indexes describe "$(basename "$IDX")" --region="$REGION" --project="$PROJECT" --format='value(metadata.config.shardSize)'
gcloud ai index-endpoints describe "$(basename "$EP")" --region="$REGION" --project="$PROJECT" \\
  --format='value(deployedIndexes[0].dedicatedResources.machineSpec.machineType,deployedIndexes[0].dedicatedResources.minReplicaCount)'

"""

def step_02_the_shard_size_the_service_chose(session):
    """Run The shard size the service chose at this checkpoint.

    Step 5 left one fact open: the deployed index's machine follows the index's shard size, and the kit lets the service choose it. Read both from the live lane; step 10 prices the row that matches.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_49', step_01_seven_services_and_the_account_each_runs_a),
        ('source_51', step_02_the_shard_size_the_service_chose),
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
