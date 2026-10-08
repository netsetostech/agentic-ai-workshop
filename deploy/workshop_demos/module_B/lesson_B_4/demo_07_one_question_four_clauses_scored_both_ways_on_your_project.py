"""Lesson B.4: One question, four clauses, scored both ways on your project

The embedding cell uses Vertex AI, which the setup switched on. The Ranking API is served by Discovery Engine, a separate API: switch it on once for your project. Enabling it costs nothing; the ranker bills per request. The cell is the kit's two embedding calls in miniature. It embeds the four clauses in one request under RETRIEVAL_DOCUMENT, as the worker embeds a document's chunks, and the question under RETRIEVAL_QUERY, as the API embeds a question, with the kit's model, its 768 numbers and its region. Then it scales every vector to length 1 and takes the dot products: four cosines. It saves them to ~/b4_bi.json for the comparison. The two requests carry 773 characters between them, about 0.16 paise. The kit calls the ranker through Google's Discovery Engine client library. Your Basics venv has only numpy and google-genai, and REST needs nothing more than libraries google-genai installed with it: google-auth, which turns your Application Default Credentials into an access token (through requests, another of them), and httpx, for the call itself. The path is the kit's ranking config, and the body is the kit's request (the model, the question, one record per clause with its text, and top_n) plus one flag that asks for ids and scores without the texts echoed back. The X-Goog-User-Project header is in Google's own example: with a person's sign-in rather than a service account, it names the project the call is billed to and counted against. Four records are one query, at USD 1 per 1,000 queries of up to 100 records each: Rs 0.085. The proof of the lesson: the same four pairs, scored both ways. The cell reads the two files, ranks the clauses by each score, and prints three things: each scorer's first choice, how many of the six pairs of clauses the two put in the same order, and how far each score spreads from its highest to its lowest.

Run order inside this file:
1. One more API (source window 19)
2. The bi-encoder side: text-embedding-005, a fraction of a paisa (source window 21)
3. The cross-encoder side: the Ranking API over REST, 8.5 paise (source window 23)
4. Side by side, Rs 0 (source window 25)

Prerequisites: demo_05_a_cross_encoder_one_pair_read_together_scored_once.
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


# Original CLI workflow for step_01_one_more_api.
COMMANDS_01 = """gcloud services enable discoveryengine.googleapis.com --project "$PROJECT" \\
  && echo "discoveryengine.googleapis.com is on for $PROJECT"   # the Ranking API: free to enable, billed per request

"""

def step_01_one_more_api(session):
    """Run One more API at this checkpoint.

    The embedding cell uses Vertex AI, which the setup switched on. The Ranking API is served by Discovery Engine, a separate API: switch it on once for your project. Enabling it costs nothing; the ranker bills per request.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run once, in the shell where PROJECT is set (after lesson 0.1).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: discoveryengine.googleapis.com is on for documind-ai-YOUR-ID
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_the_bi_encoder_side_text_embedding_005_a_f(session):
    """Run The bi-encoder side: text-embedding-005, a fraction of a paisa at this checkpoint.

    The cell is the kit's two embedding calls in miniature. It embeds the four clauses in one request under RETRIEVAL_DOCUMENT, as the worker embeds a document's chunks, and the question under RETRIEVAL_QUERY, as the API embeds a question, with the kit's model, its 768 numbers and its region. Then it scales every vector to length 1 and takes the dot products: four cosines. It saves them to ~/b4_bi.json for the comparison. The two requests carry 773 characters between them, about 0.16 paise.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in your venv, PROJECT set (a Python cell; two paid embedding requests).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/bi_encoder.txt]
    """
    import os, json, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import numpy as np
    from google import genai
    PROJECT = os.environ["PROJECT"]
    QUESTION = "Can I use my unused leave to shorten my notice period?"
    CLAUSES = {   # four clauses of the kit's handbook, evals/corpus/acme/hr_policy_2026.md
        "NP-03": ("A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice "
                  "runs from the date the resignation is acknowledged in writing. Unused earned leave may "
                  "not be set off against the notice period."),
        "PB-02": ("New joiners serve six months on probation at grade E2. During probation the notice "
                  "period is 15 days for either side. Probation may be extended once, by up to three "
                  "months, with written reasons."),
        "LV-01": ("Earned leave accrues at 1.75 days per completed month. A maximum of 30 days may be "
                  "carried forward into the next calendar year; anything above 30 lapses on 31 December."),
        "LV-07": ("Earned leave is encashed on exit at basic pay, capped at 45 days. Leave cannot be "
                  "encashed during probation and cannot be used to shorten notice."),
    }
    client = genai.Client(enterprise=True, project=PROJECT, location="us-central1")   # embeddings are regional, as in the kit
    def embed(texts, task):
        """Embed this text under the selected document/query task type so the lesson can compare the vectors.
        
        Example: embed(list(CLAUSES.values()), 'RETRIEVAL_DOCUMENT')
        """
        r = client.models.embed_content(model="text-embedding-005", contents=texts,
                                        config={"output_dimensionality": 768, "task_type": task})
        return np.array([e.values for e in r.embeddings])
    D = embed(list(CLAUSES.values()), "RETRIEVAL_DOCUMENT")      # the worker's side: every chunk, once, at ingest
    q = embed([QUESTION], "RETRIEVAL_QUERY")[0]                  # the API's side: once per question
    D = D / np.linalg.norm(D, axis=1, keepdims=True)             # length 1, so the dot product below is the cosine
    q = q / np.linalg.norm(q)
    scores = D @ q
    print(f"text-embedding-005 on us-central1: {len(D)} clause vectors (RETRIEVAL_DOCUMENT) and 1 question vector (RETRIEVAL_QUERY), {D.shape[1]} numbers each")
    print("the cosine of the question with each clause, highest first:")
    for name, s in sorted(zip(CLAUSES, scores), key=lambda p: -p[1]):
        print(f"  {name}  cosine {s:.4f}")
    json.dump({name: float(s) for name, s in zip(CLAUSES, scores)}, open(os.path.expanduser("~/b4_bi.json"), "w"))
    print("saved ~/b4_bi.json for the comparison")

def step_03_the_cross_encoder_side_the_ranking_api_ove(session):
    """Run The cross-encoder side: the Ranking API over REST, 8.5 paise at this checkpoint.

    The kit calls the ranker through Google's Discovery Engine client library. Your Basics venv has only numpy and google-genai, and REST needs nothing more than libraries google-genai installed with it: google-auth, which turns your Application Default Credentials into an access token (through requests, another of them), and httpx, for the call itself. The path is the kit's ranking config, and the body is the kit's request (the model, the question, one record per clause with its text, and top_n) plus one flag that asks for ids and scores without the texts echoed back. The X-Goog-User-Project header is in Google's own example: with a person's sign-in rather than a service account, it names the project the call is billed to and counted against. Four records are one query, at USD 1 per 1,000 queries of up to 100 records each: Rs 0.085.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in your venv, PROJECT set (a Python cell; one paid rank request).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/cross_encoder.txt]
    """
    import os, json, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import google.auth, httpx
    from google.auth.transport.requests import Request
    PROJECT = os.environ["PROJECT"]
    QUESTION = "Can I use my unused leave to shorten my notice period?"
    CLAUSES = {   # four clauses of the kit's handbook, evals/corpus/acme/hr_policy_2026.md
        "NP-03": ("A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice "
                  "runs from the date the resignation is acknowledged in writing. Unused earned leave may "
                  "not be set off against the notice period."),
        "PB-02": ("New joiners serve six months on probation at grade E2. During probation the notice "
                  "period is 15 days for either side. Probation may be extended once, by up to three "
                  "months, with written reasons."),
        "LV-01": ("Earned leave accrues at 1.75 days per completed month. A maximum of 30 days may be "
                  "carried forward into the next calendar year; anything above 30 lapses on 31 December."),
        "LV-07": ("Earned leave is encashed on exit at basic pay, capped at 45 days. Leave cannot be "
                  "encashed during probation and cannot be used to shorten notice."),
    }
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(Request())                                   # an access token from your Application Default Credentials
    url = (f"https://discoveryengine.googleapis.com/v1/projects/{PROJECT}/locations/global/"
           "rankingConfigs/default_ranking_config:rank")       # the kit's ranking_config_path(), as a REST path
    body = {"model": "semantic-ranker-fast-004", "query": QUESTION,
            "records": [{"id": name, "content": text} for name, text in CLAUSES.items()],
            "topN": len(CLAUSES), "ignoreRecordDetailsInResponse": True}
    r = httpx.post(url, json=body, timeout=30,
                   headers={"Authorization": f"Bearer {creds.token}", "X-Goog-User-Project": PROJECT})
    if r.status_code != 200:
        raise SystemExit(f"HTTP {r.status_code}: {r.text[:500]}")
    records = r.json()["records"]                              # highest score first
    print(f"semantic-ranker-fast-004 on global: {len(records)} records scored, highest first")
    for rec in records:
        print(f"  {rec['id']}  score {rec.get('score', 0.0):.4f}")
    json.dump({rec["id"]: rec.get("score", 0.0) for rec in records}, open(os.path.expanduser("~/b4_cross.json"), "w"))
    print("saved ~/b4_cross.json for the comparison")

def step_04_side_by_side_rs_0(session):
    """Run Side by side, Rs 0 at this checkpoint.

    The proof of the lesson: the same four pairs, scored both ways. The cell reads the two files, ranks the clauses by each score, and prints three things: each scorer's first choice, how many of the six pairs of clauses the two put in the same order, and how far each score spreads from its highest to its lowest.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in your venv after the two cells above (a Python cell; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/compare.txt]
    """
    import json, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from itertools import combinations
    bi = json.load(open(os.path.expanduser("~/b4_bi.json")))           # the first cell: the cosines
    cross = json.load(open(os.path.expanduser("~/b4_cross.json")))     # the second: the ranker's scores
    by_bi = sorted(bi, key=lambda n: -bi[n])
    by_cross = sorted(cross, key=lambda n: -cross[n])
    print(f"{'clause':8}{'bi-encoder cosine':>19}{'rank':>6}{'cross-encoder score':>21}{'rank':>6}")
    for n in by_bi:
        print(f"{n:8}{bi[n]:19.4f}{by_bi.index(n) + 1:6}{cross[n]:21.4f}{by_cross.index(n) + 1:6}")
    pairs = list(combinations(by_bi, 2))
    same = sum((bi[a] - bi[b]) * (cross[a] - cross[b]) > 0 for a, b in pairs)
    print(f"first choice: bi-encoder {by_bi[0]}, cross-encoder {by_cross[0]}")
    print(f"pairs of clauses the two put in the same order: {same} of {len(pairs)}")
    print(f"spread, highest minus lowest: bi-encoder {bi[by_bi[0]] - bi[by_bi[-1]]:.4f}, "
          f"cross-encoder {cross[by_cross[0]] - cross[by_cross[-1]]:.4f}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_one_more_api),
        ('source_21', step_02_the_bi_encoder_side_text_embedding_005_a_f),
        ('source_23', step_03_the_cross_encoder_side_the_ranking_api_ove),
        ('source_25', step_04_side_by_side_rs_0),
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
