"""Lesson 2.3: The Ranking API by hand: the API's pool, the API's request, the API's order

Do it: embed, pool, rank, compare

Run order inside this file:
1. Do it: embed, pool, rank, compare (source window 13)

Prerequisites: demo_03_one_answer_read_end_to_end_the_citations_their_scores_the_stages.
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


def step_01_embed_pool_rank_compare(session):
    """Run Do it: embed, pool, rank, compare at this checkpoint.

    Do it: embed, pool, rank, compare

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; one paid embedding and one rank request, well under a rupee).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: pool: 20 current ids from the index in 9xx ms, every one found_by vector
    ranker: 20 of 20 back in 2xx ms, 20 records sent, model semantic-ranker-fast-004
       rank 1  score 0.9xxx  pool # 1  NP-03     hr_policy_2026.md
       rank 2  score 0.xxxx  pool # x  ...       hr_policy_2026.md
       ...
    the API's cited ids, by score: ['#1', '#4', '#2'] | by hand, first 5: ['#1', '#4', '#2', '#7', '#3']
    every citation is in the by-hand top 5: True | in the same relative order: True
    saved /tmp/pool53.json for steps 5, 7 and 8
    """
    import os, json, time, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google import genai
    from google.cloud import aiplatform, firestore
    from google.cloud import discoveryengine_v1 as discoveryengine
    from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import Namespace
    PROJECT, REGION = os.environ["PROJECT"], os.environ["REGION"]
    ENDPOINT, DEPLOYED = os.environ["VECTOR_INDEX_ENDPOINT"], os.environ["VECTOR_DEPLOYED_INDEX_ID"]
    Q = os.environ.get("Q", "What is the notice period for a confirmed E3?")
    client = genai.Client(enterprise=True, project=PROJECT, location=REGION)              # the API embeds in its own region
    t = time.perf_counter()
    vec = list(client.models.embed_content(model="text-embedding-005", contents=[Q],
                                           config={"output_dimensionality": 768, "task_type": "RETRIEVAL_QUERY"}).embeddings[0].values)
    aiplatform.init(project=PROJECT, location=REGION)
    hits = aiplatform.MatchingEngineIndexEndpoint(ENDPOINT).find_neighbors(deployed_index_id=DEPLOYED, queries=[vec], num_neighbors=20,
                                                                          filter=[Namespace(name="tenant_id", allow_tokens=["acme"])])[0]
    db = firestore.Client(project=PROJECT)
    pool = []                                                        # _hydrate(): the payloads in the index's order, score = the distance
    for n in hits:
        row = db.collection("chunks").document(n.id).get().to_dict() or {}
        if row.get("current") is False:
            continue                                                 # prefer_current(): a retired row never reaches the ranker
        pool.append({"id": n.id, "score": n.distance, "text": row.get("text", ""), "locator": row.get("locator", "?"),
                     "source": row.get("source_uri", "").split("/")[-1], "found_by": "vector"})
    print(f"pool: {len(pool)} current ids from the index in {int((time.perf_counter() - t) * 1000)} ms, every one found_by vector")
    ranker = discoveryengine.RankServiceClient()                                          # retriever._ranker()
    config = ranker.ranking_config_path(project=PROJECT, location="global", ranking_config="default_ranking_config")
    records = [discoveryengine.RankingRecord(id=str(i), content=c["text"]) for i, c in enumerate(pool[:200])]
    t = time.perf_counter()
    resp = ranker.rank(request=discoveryengine.RankRequest(ranking_config=config, model="semantic-ranker-fast-004",
                                                            top_n=len(pool), query=Q, records=records), timeout=5.0)
    print(f"ranker: {len(resp.records)} of {len(pool)} back in {int((time.perf_counter() - t) * 1000)} ms, {len(records)} records sent, model semantic-ranker-fast-004")
    ranked = [(int(r.id), r.score) for r in resp.records]
    for rank, (i, score) in enumerate(ranked[:5], 1):
        print(f"   rank {rank}  score {score:.4f}  pool #{i + 1:>2}  {pool[i]['locator']:9} {pool[i]['source'][:28]}")
    try:
        ans = json.load(open("/tmp/ans53_5.json"))
        cited = [c["chunk_id"] for c in sorted(ans["citations"], key=lambda c: -c["score"])]
        hand = [pool[i]["id"] for i, _ in ranked[:5]]
        print("the API's cited ids, by score:", [f"#{c.rsplit('#', 1)[1]}" for c in cited], "| by hand, first 5:", [f"#{c.rsplit('#', 1)[1]}" for c in hand])
        print("every citation is in the by-hand top 5:", all(c in hand for c in cited), "| in the same relative order:", [c for c in hand if c in cited] == cited)
    except FileNotFoundError:
        print("run step 3 first to compare with the API's citations")
    json.dump({"question": Q, "pool": pool, "ranked": ranked}, open("/tmp/pool53.json", "w"))
    print("saved /tmp/pool53.json for steps 5, 7 and 8")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_embed_pool_rank_compare),
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
