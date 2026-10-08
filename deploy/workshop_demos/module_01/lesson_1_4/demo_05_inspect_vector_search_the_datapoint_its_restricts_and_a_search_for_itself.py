"""Lesson 1.4: Inspect Vector Search: the datapoint, its restricts, and a search for itself

Three things exist: the index, the endpoint, and the deployed index that joins them and is the one that costs money per hour. The kit's make vector-status runs commands/vector-status.sh, which takes the two names from the shell (the variables you exported above) or, failing that, from Terraform's outputs; the two commands below are the same reads by hand. Read one datapoint back, then search for it

Run order inside this file:
1. The index and its deployment, as gcloud sees them (source window 24)
2. Read one datapoint back, then search for it (source window 27)

Prerequisites: demo_04_inspect_firestore_the_claim_the_rows_the_ledger_row_the_fingerprint.
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


# Original CLI workflow for step_01_the_index_and_its_deployment_as_gcloud_see.
COMMANDS_01 = """gcloud ai indexes describe "$(basename "$VECTOR_INDEX_NAME")" --region="$REGION" --project="$PROJECT" \\
  --format='yaml(displayName,indexStats.vectorsCount,indexStats.shardsCount,indexUpdateMethod,metadata.config.dimensions,metadata.config.distanceMeasureType)'
gcloud ai index-endpoints describe "$(basename "$VECTOR_INDEX_ENDPOINT")" --region="$REGION" --project="$PROJECT" \\
  --format='yaml(displayName,deployedIndexes[].id,deployedIndexes[].indexSyncTime,deployedIndexes[].dedicatedResources.machineSpec.machineType)'

"""

def step_01_the_index_and_its_deployment_as_gcloud_see(session):
    """Run The index and its deployment, as gcloud sees them at this checkpoint.

    Three things exist: the index, the endpoint, and the deployed index that joins them and is the one that costs money per hour. The kit's make vector-status runs commands/vector-status.sh, which takes the two names from the shell (the variables you exported above) or, failing that, from Terraform's outputs; the two commands below are the same reads by hand.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: displayName: documind-chunks
    indexStats:
      shardsCount: 1
      vectorsCount: '1745'
    indexUpdateMethod: STREAM_UPDATE
    metadata:
      config:
        dimensions: 768
        distanceMeasureType: DOT_PRODUCT_DISTANCE
    displayName: documind-endpoint
    deployedIndexes:
    - dedicatedResources:
        machineSpec:
          machineType: e2-standard-2
      id: documind_chunks_v1
      indexSyncTime: '2026-09-22T10:41:07.000Z'
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_read_one_datapoint_back_then_search_for_it(session):
    """Run Read one datapoint back, then search for it at this checkpoint.

    Read one datapoint back, then search for it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: datapoint acme:9c41d0e2b7f5...#1: 768 numbers | same as the row's vector: True
    restricts: [('tenant_id', ['acme']), ('kind', ['text']), ('doc_type', ['unknown']), ('current', ['true'])]
    sparse dimensions: 24
      acme:9c41d0e2b7f5...#1  distance 1.0000   <- itself
      acme:9c41d0e2b7f5...#2  distance 0.7xxx
      acme:9c41d0e2b7f5...#0  distance 0.6xxx
    """
    import os, hashlib, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import aiplatform, firestore
    from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import Namespace
    PROJECT, REGION = os.environ["PROJECT"], os.environ["REGION"]
    ENDPOINT, DEPLOYED = os.environ["VECTOR_INDEX_ENDPOINT"], os.environ["VECTOR_DEPLOYED_INDEX_ID"]
    db = firestore.Client(project=PROJECT)
    NOTE = os.environ.get("NOTE", os.path.expanduser("~/lesson34_note.md"))    # the note you wrote in step 3
    sha = hashlib.sha256(open(NOTE, "rb").read()).hexdigest()
    cid = f"acme:{sha}#1"                                                  # SM-01, the smoke lantern
    vec = list(db.collection("chunks").document(cid).get().to_dict()["embedding"])
    aiplatform.init(project=PROJECT, location=REGION)
    ep = aiplatform.MatchingEngineIndexEndpoint(ENDPOINT)
    dp = ep.read_index_datapoints(deployed_index_id=DEPLOYED, ids=[cid])[0]
    same = len(dp.feature_vector) == len(vec) and all(abs(a - b) < 1e-6 for a, b in zip(dp.feature_vector, vec))
    print(f"datapoint {dp.datapoint_id.split('#')[0][:18]}...#1: {len(dp.feature_vector)} numbers | same as the row's vector: {same}")
    print("restricts:", [(r.namespace, list(r.allow_list)) for r in dp.restricts])
    print("sparse dimensions:", len(dp.sparse_embedding.dimensions))
    hits = ep.find_neighbors(deployed_index_id=DEPLOYED, queries=[vec], num_neighbors=3,
                             filter=[Namespace(name="tenant_id", allow_tokens=["acme"]), Namespace(name="current", allow_tokens=["true"])])[0]
    for n in hits:
        print(f"  {n.id.split('#')[0][:18]}...#{n.id.rsplit('#', 1)[1]}  distance {n.distance:.4f}" + ("   <- itself" if n.id == cid else ""))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_24', step_01_the_index_and_its_deployment_as_gcloud_see),
        ('source_27', step_02_read_one_datapoint_back_then_search_for_it),
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
