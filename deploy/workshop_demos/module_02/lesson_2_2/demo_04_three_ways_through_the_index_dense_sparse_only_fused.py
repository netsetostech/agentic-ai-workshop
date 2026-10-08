"""Lesson 2.2: Three ways through the index: dense, sparse only, fused

Do it: dense, alpha 0, alpha 0.7

Run order inside this file:
1. Do it: dense, alpha 0, alpha 0.7 (source window 16)

Prerequisites: demo_03_the_lane_runs_dense_and_two_sparse_rulers_over_its_own_rows.
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


def step_01_dense_alpha_0_alpha_0_7(session):
    """Run Do it: dense, alpha 0, alpha 0.7 at this checkpoint.

    Do it: dense, alpha 0, alpha 0.7

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; one paid embedding of a few dozen characters).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: dense  first five (anchor at rank 1 of 20):
       w0         inv_2026_0412.md                     <- anchor
       p23-0      payment_of_bonus_act_1965.pdf
       ...

    sparse first five (anchor at rank None of 20):
       p28-1      industrial_relations_code_2020.pdf
       p7-0       payment_of_gratuity_act_1972.pdf
       ...

    hybrid first five (anchor at rank 1 of 20):
       w0         inv_2026_0412.md                     <- anchor
       p23-0      payment_of_bonus_act_1965.pdf
       ...

    overlap of 20: dense/hybrid 20 | dense/sparse 0
    saved /tmp/legs52.json for step 5
    """
    import os, sys, json, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = [".", "services/rag-api"]                 # shared/ for the encoder, the API's folder for hybrid.py
    from google import genai
    from google.cloud import aiplatform, firestore
    from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import Namespace
    from hybrid import hybrid_find_neighbors
    PROJECT, REGION = os.environ["PROJECT"], os.environ["REGION"]
    ENDPOINT, DEPLOYED = os.environ["VECTOR_INDEX_ENDPOINT"], os.environ["VECTOR_DEPLOYED_INDEX_ID"]
    Q = os.environ.get("Q", "What is the total payable on invoice INV-2026-0412?")
    ANCHOR = os.environ.get("ANCHOR", "inv_2026_0412")
    client = genai.Client(enterprise=True, project=PROJECT, location=REGION)          # the API embeds in its own region
    vec = list(client.models.embed_content(model="text-embedding-005", contents=[Q],
                                           config={"output_dimensionality": 768, "task_type": "RETRIEVAL_QUERY"}).embeddings[0].values)
    aiplatform.init(project=PROJECT, location=REGION)
    ep = aiplatform.MatchingEngineIndexEndpoint(ENDPOINT)
    tenant = [Namespace(name="tenant_id", allow_tokens=["acme"])]
    lists = {"dense": [n.id for n in ep.find_neighbors(deployed_index_id=DEPLOYED, queries=[vec], num_neighbors=20, filter=tenant)[0]]}
    for name, alpha in (("sparse", 0.0), ("hybrid", 0.7)):
        lists[name] = [n.id for n in hybrid_find_neighbors(ep, DEPLOYED, vec, Q, "acme", k=20, alpha=alpha, restricts=tenant)]
    db = firestore.Client(project=PROJECT)
    label = {}
    for cid in set(sum(lists.values(), [])):
        row = db.collection("chunks").document(cid).get().to_dict() or {}
        label[cid] = (row.get("locator", "?"), row.get("source_uri", "").split("/")[-1])
    hit = lambda cid: label[cid][0] == ANCHOR or label[cid][1].startswith(ANCHOR)
    for name in ("dense", "sparse", "hybrid"):
        rank = next((i + 1 for i, cid in enumerate(lists[name]) if hit(cid)), None)
        print(f"\n{name:6} first five (anchor at rank {rank} of 20):")
        for cid in lists[name][:5]:
            print(f"   {label[cid][0]:10} {label[cid][1][:34]}" + ("   <- anchor" if hit(cid) else ""))
    print("\noverlap of 20: dense/hybrid", len(set(lists["dense"]) & set(lists["hybrid"])), "| dense/sparse", len(set(lists["dense"]) & set(lists["sparse"])))
    json.dump({"question": Q, "label": label, **lists}, open("/tmp/legs52.json", "w"))
    print("saved /tmp/legs52.json for step 5")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_dense_alpha_0_alpha_0_7),
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
