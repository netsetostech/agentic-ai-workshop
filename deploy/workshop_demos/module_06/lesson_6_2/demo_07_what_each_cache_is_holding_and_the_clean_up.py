"""Lesson 6.2: What each cache is holding, and the clean-up

The record behind the context cache, the entry behind the hit, and both caches put away. The cell prints tenant_caches/acme, then the answer-cache entry for the question's words. It uses the kit's own qhash, imported from services/rag-api, so the key is computed exactly as the API computes it.

Run order inside this file:
1. What each cache is holding, and the clean-up (source window 29)

Prerequisites: demo_06_four_asks_a_miss_two_hits_and_a_paraphrase.
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


def step_01_what_each_cache_is_holding_and_the_clean_u(session):
    """Run What each cache is holding, and the clean-up at this checkpoint.

    The record behind the context cache, the entry behind the hit, and both caches put away. The cell prints tenant_caches/acme, then the answer-cache entry for the question's words. It uses the kit's own qhash, imported from services/rag-api, so the key is computed exactly as the API computes it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (what each cache is holding; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: context cache  (Firestore holds a pointer; the pack itself is on Google's side)
        cache_name: projects/NUMBER/locations/global/cachedContents/CACHE_ID
        location: global
        model: gemini-3.6-flash
        tokens: 41259
        expire_time: YYYY-MM-DD HH:MM:SS.ssssss+00:00
        corpus_fingerprint: FINGERPRINT
    answer cache  (2 acme entries; 1 for this question's words)
        question: How many days a month can I work remotely?
        qhash: 79ae9ca70e9e21c4c23aca5b  scope: 7a0875abc72b0f7b  fingerprint: FINGERPRINT_
        model: gemini-3.6-flash  expire_at: YYYY-MM-DD HH:MM:SS+00:00  embedding: 768 numbers
        answer: Employees may work remotely up to eight days per month with   citations: 1
    """
    import os, sys
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    sys.path.insert(0, "services/rag-api")
    from semantic_cache import qhash
    db = firestore.Client(project=os.environ["PROJECT"])
    c = db.collection("tenant_caches").document("acme").get().to_dict() or {}
    print("context cache  (Firestore holds a pointer; the pack itself is on Google's side)")
    for k in ("cache_name", "location", "model", "tokens", "expire_time", "corpus_fingerprint"):
        print(f"    {k}: {c.get(k)}")
    rows = [d.to_dict() for d in db.collection("answer_cache").where(filter=FieldFilter("tenant_id", "==", "acme")).stream()]
    mine = [r for r in rows if r.get("qhash") == qhash(os.environ["Q91"])]
    print(f"answer cache  ({len(rows)} acme entries; {len(mine)} for this question's words)")
    for r in mine[:1]:
        print(f"    question: {r['question']}\n    qhash: {r['qhash']}  scope: {r['scope']}  fingerprint: {r['fingerprint'][:12]}")
        print(f"    model: {r['model']}  expire_at: {r['expire_at']}  embedding: {len(r['embedding'])} numbers")
        print(f"    answer: {r['answer']['answer'][:60]}  citations: {len(r['answer']['citations'])}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_29', step_01_what_each_cache_is_holding_and_the_clean_u),
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
