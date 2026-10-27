"""Lesson 8.3: REST: the index's own size

The index's vectors, shards and shard size, and the deployment's machine and replicas, read from the Vertex AI API. make vector-status printed the fields gcloud was asked for. The API holds more: the index's shard size, its dimensions, and the deployed index's machine and replica range. The cell reads both with two GETs, then does the one sum that matters for sizing: how much of one shard your vectors fill.

Run order inside this file:
1. REST: the index's own size (source window 24)

Prerequisites: demo_05_measure_the_corpus_with_the_kit_s_own_chunker.
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


def step_01_rest_the_index_s_own_size(session):
    """Run REST: the index's own size at this checkpoint.

    The index's vectors, shards and shard size, and the deployment's machine and replicas, read from the Vertex AI API. make vector-status printed the fields gcloud was asked for. The API holds more: the index's shard size, its dimensions, and the deployed index's machine and replica range. The cell reads both with two GETs, then does the one sum that matters for sizing: how much of one shard your vectors fill.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (two GETs on the Vertex AI API; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/index_rest.txt]
    """
    import json, os, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P, R = os.environ["PROJECT"], os.environ["REGION"]
    tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    base = f"https://{R}-aiplatform.googleapis.com/v1/projects/{P}/locations/{R}"
    get = lambda path: json.load(urllib.request.urlopen(urllib.request.Request(f"{base}/{path}", headers={"Authorization": f"Bearer {tok}"}), timeout=60))
    GIB, SHARD_GIB = 1 << 30, {"SHARD_SIZE_SMALL": 2, "SHARD_SIZE_MEDIUM": 20, "SHARD_SIZE_LARGE": 50}   # Google's shard sizes (step 8)
    for ix in get("indexes").get("indexes", []):
        cfg, st = ix["metadata"]["config"], ix.get("indexStats", {})
        n, dims, shard = int(st.get("vectorsCount", 0)), int(cfg["dimensions"]), cfg.get("shardSize", "not stated")
        print(f"index {ix['displayName']}: {n:,} vectors of {dims}, {st.get('shardsCount', 0)} shard(s), {shard}, {ix['indexUpdateMethod']}")
        if shard in SHARD_GIB:
            used = n * dims * 4 / GIB
            print(f"  dense data {used * 1024:,.1f} MiB: {100 * used / SHARD_GIB[shard]:.3f}% of one {SHARD_GIB[shard]} GiB shard; "
                  f"the shard holds {int(SHARD_GIB[shard] * GIB / (dims * 4)):,} vectors of this length")
    for ep in get("indexEndpoints").get("indexEndpoints", []):
        for d in ep.get("deployedIndexes", []):
            res = d.get("dedicatedResources", {})
            print(f"deployed {d['id']}: {res.get('machineSpec', {}).get('machineType')}, replicas {res.get('minReplicaCount')} to {res.get('maxReplicaCount')}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_24', step_01_rest_the_index_s_own_size),
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
