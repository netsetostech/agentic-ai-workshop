"""Lesson 0.4: What still bills when nothing runs

The table prices the lane where it runs. Its services, index, databases and cluster are in Mumbai, asia-south1 (Spanner's configuration is regional-asia-south1 on every lane), and each unit price is Mumbai's list price as Google's pages gave it on 7 October 2026, before tax. Prices change, and an Indian billing account is charged at Google's own rupee prices rather than at Rs 85 to the dollar. The number that counts is your bill: in the console, Billing, then Reports, filtered to your project and grouped by SKU, on a day the lane sat idle. What the table leaves out bills by size or by use rather than by the hour: Firestore, the buckets, the container images, the two RAG Engine corpora and the two data stores, the nightly job's minute, the BigQuery tables' few rows. At the corpus's size these are small next to the six lines, and the bill shows them as well. Now read the six lines on your own lane: the machine behind the deployed index and the shard size the API picked, Spanner's edition and units, the databases' tier, the cluster's location and node, the connector's machines.

Run order inside this file:
1. The arithmetic (source window 64)

Prerequisites: demo_09_make_off_and_zero_instances.
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


# Original CLI workflow for step_01_the_arithmetic.
COMMANDS_01 = """gcloud ai index-endpoints list --region="$REGION" --project="$PROJECT" \\
  --format="table(displayName,deployedIndexes[0].dedicatedResources.machineSpec.machineType,deployedIndexes[0].dedicatedResources.minReplicaCount)"
gcloud ai indexes list --region="$REGION" --project="$PROJECT" --format="table(displayName,metadata.config.shardSize)"
gcloud spanner instances list --project="$PROJECT" --format="table(name.basename(),config.basename(),edition,processingUnits)"
gcloud sql instances list --project="$PROJECT" --format="table(name,settings.tier,region,state)"
gcloud container clusters list --project="$PROJECT" --format="table(name,location,autopilot.enabled,currentNodeCount)"
gcloud container node-pools list --cluster=documind-autopilot --region="$REGION" --project="$PROJECT" \\
  --format="table(name,config.machineType,config.diskType,config.diskSizeGb,locations.list())"
gcloud compute networks vpc-access connectors describe documind-vpc --region="$REGION" --project="$PROJECT" \\
  --format="table(name.basename(),machineType,minInstances,maxInstances)"

"""

def step_01_the_arithmetic(session):
    """Run The arithmetic at this checkpoint.

    The table prices the lane where it runs. Its services, index, databases and cluster are in Mumbai, asia-south1 (Spanner's configuration is regional-asia-south1 on every lane), and each unit price is Mumbai's list price as Google's pages gave it on 7 October 2026, before tax. Prices change, and an Indian billing account is charged at Google's own rupee prices rather than at Rs 85 to the dollar. The number that counts is your bill: in the console, Billing, then Reports, filtered to your project and grouped by SKU, on a day the lane sat idle. What the table leaves out bills by size or by use rather than by the hour: Firestore, the buckets, the container images, the two RAG Engine corpora and the two data stores, the nightly job's minute, the BigQuery tables' few rows. At the corpus's size these are small next to the six lines, and the bill shows them as well. Now read the six lines on your own lane: the machine behind the deployed index and the shard size the API picked, Spanner's edition and units, the databases' tier, the cluster's location and node, the connector's machines.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (read-only: seven listings of what bills by the hour).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/standing_resources.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_64', step_01_the_arithmetic),
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
