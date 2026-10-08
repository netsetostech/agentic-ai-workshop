"""Lesson 2.1: The question's vector: direct candidates and API citations

Run the preflight first. This cell uses its verified settings, checks the endpoint and Acme pin again before paying for an embedding, searches with the same tenant/current restricts, then compares candidate IDs with the API citations. Overlap and first-citation order are observations, not pass/fail assertions. Hybrid retrieval, graph candidates, current-version checks and reranking can change the final selection.

Run order inside this file:
1. Do it: embed, search, compare (source window 8)

Prerequisites: setup_prepare.
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


def step_01_embed_search_compare(session):
    """Run Do it: embed, search, compare at this checkpoint.

    Run the preflight first. This cell uses its verified settings, checks the endpoint and Acme pin again before paying for an embedding, searches with the same tenant/current restricts, then compares candidate IDs with the API citations. Overlap and first-citation order are observations, not pass/fail assertions. Hybrid retrieval, graph candidates, current-version checks and reranking can change the final selection.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, then one question; a paid embedding of a few hundred characters).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Actual deployed ID: the ID verified during preflight
    Direct dense candidates: non-empty for the loaded handbook
    stages.retrieval_backend: vector
    vector_chunks: greater than 0
    PASS: the direct search worked and Vector Search contributed to the API pool.
    """
    import os, json, warnings, subprocess
    from pathlib import Path
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    warnings.filterwarnings("ignore", category=UserWarning)
    from google import genai
    from google.cloud import aiplatform, firestore
    from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import Namespace
    
    PROJECT, REGION, API = os.environ["PROJECT"], os.environ["REGION"], os.environ["API"]
    settings_file = Path("operator-evidence/lesson51/settings.json")
    if not settings_file.exists():
        raise SystemExit("STOP: run this lesson's preflight first.")
    cfg = json.loads(settings_file.read_text())
    if cfg["project"] != PROJECT or cfg["api"].rstrip("/") != API.rstrip("/"):
        raise SystemExit("STOP: saved settings belong to another project or API; rerun preflight.")
    db = firestore.Client(project=PROJECT)
    pin = (db.collection("tenant_settings").document("acme").get().to_dict() or {}).get("retrieval_backend")
    if pin != "vector":
        raise SystemExit("STOP: Acme is not pinned to vector. Run preflight; restore only after the lesson.")
    aiplatform.init(project=PROJECT, location=REGION)
    ep = aiplatform.MatchingEngineIndexEndpoint(cfg["endpoint"])
    if cfg["deployed_id"] not in [d.id for d in ep.deployed_indexes]:
        raise SystemExit("STOP: deployed ID is absent; use the repair note and rerun preflight.")
    restricts = [Namespace(name="tenant_id", allow_tokens=["acme"])]
    if cfg["current_only"] == "on":
        restricts.append(Namespace(name="current", allow_tokens=["true"]))
    print("Direct dense search:", cfg["deployed_id"], "| current_only:", cfg["current_only"],
          "| requested candidates:", cfg["top_k"], "| API mode:", cfg["mode"], "| graph:", cfg["graph"])
    Q = "What is the notice period for a confirmed E3?"
    client = genai.Client(enterprise=True, project=PROJECT, location="us-central1")
    vec = list(client.models.embed_content(model=cfg["embed_model"], contents=[Q],
        config={"output_dimensionality": 768, "task_type": "RETRIEVAL_QUERY"}).embeddings[0].values)
    result = ep.find_neighbors(deployed_index_id=cfg["deployed_id"], queries=[vec],
                              num_neighbors=cfg["top_k"], filter=restricts)
    hits = result[0] if result else []
    pool = [n.id for n in hits]
    print("Direct dense candidates, first five:")
    for n in hits[:5]:
        row = db.collection("chunks").document(n.id).get().to_dict() or {}
        print(n.id, "|", row.get("locator", "?"), "|", row.get("source_uri", ""),
              "| current:", row.get("current"), "| score:", round(n.distance, 4))
    if not hits:
        raise SystemExit("STOP: the valid deployment returned no matching candidates; check ingestion and restricts.")
    tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
        f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"],
        check=True, capture_output=True, text=True).stdout.strip()
    if not tok:
        raise SystemExit("STOP: no identity token returned.")
    body = json.dumps({"query": Q, "tenant_id": "acme", "stream": False}).encode()
    request = Request(f"{API}/v1/query", data=body, method="POST",
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=180) as response:
            ans = json.load(response)
    except HTTPError as exc:
        raise SystemExit(f"API HTTP {exc.code}: {exc.read().decode()}")
    cited = [c["chunk_id"] for c in ans.get("citations", [])]
    stages = ans.get("stages") or {}
    print("API answerable:", ans.get("answerable"), "|", ans.get("answer", "")[:100])
    print("Citation overlap:", sum(c in pool for c in cited), "of", len(cited),
          "| first matches direct first:", bool(cited) and cited[0] == pool[0])
    print("stages.retrieval_backend:", stages.get("retrieval_backend"), "| pool:", stages.get("pool"),
          "| vector_chunks:", stages.get("vector_chunks"), "| cache_hit:", ans.get("cache_hit"))
    if stages.get("retrieval_backend") != "vector":
        raise SystemExit("STOP: API used another backend. Allow its one-minute pin cache to expire; rerun preflight if it persists.")
    if (stages.get("vector_chunks") or 0) == 0:
        raise SystemExit("STOP: no Vector Search chunks reached the API pool; inspect vector_search_fallback logs and current rows.")
    print("PASS: the direct search worked and Vector Search contributed to the API pool.")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_8', step_01_embed_search_compare),
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
