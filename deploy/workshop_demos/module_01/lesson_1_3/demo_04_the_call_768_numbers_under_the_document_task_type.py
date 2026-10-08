"""Lesson 1.3: The call: 768 numbers under the document task type

This cell costs money, a very small amount: two calls on a 234-character clause, about a tenth of a paisa. It reads NP-03's text and stored vector off the lane, embeds the same text under the document profile with the worker's exact settings, and compares by cosine. Then it embeds the same text under the query profile and compares again.

Run order inside this file:
1. Do it: embed one clause yourself, both ways (source window 14)

Prerequisites: demo_03_one_declared_embedding_from_terraform_to_the_row.
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


def step_01_embed_one_clause_yourself_both_ways(session):
    """Run Do it: embed one clause yourself, both ways at this checkpoint.

    This cell costs money, a very small amount: two calls on a 234-character clause, about a tenth of a paisa. It reads NP-03's text and stored vector off the lane, embeds the same text under the document profile with the worker's exact settings, and compares by cosine. Then it embeds the same text under the query profile and compares again.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash; two paid calls).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lane vector: 768 numbers; first three [0.0213, -0.0117, 0.0388]
    same text, RETRIEVAL_DOCUMENT: cosine to the lane's vector 1.0
    same text, RETRIEVAL_QUERY:    cosine to the lane's vector 0.9xxx
    """
    import os, math, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    from google import genai
    PROJECT = os.environ["PROJECT"]
    db = firestore.Client(project=PROJECT)
    row = next(db.collection("chunks").where("tenant_id", "==", "acme")
                 .where("source_uri", "==", f"gs://{PROJECT}-uploads/acme/hr_policy_2026.md")
                 .where("current", "==", True).where("locator", "==", "NP-03").stream()).to_dict()
    lane = list(row["embedding"])
    client = genai.Client(enterprise=True, project=PROJECT, location="us-central1")   # embeddings are regional
    def embed(text, task):
        """Embed this text under the selected document/query task type so the lesson can compare the vectors.
        
        Example: embed(row['text'], 'RETRIEVAL_DOCUMENT')
        """
        r = client.models.embed_content(model="text-embedding-005", contents=[text],
                                        config={"output_dimensionality": 768, "task_type": task})
        return list(r.embeddings[0].values)
    def cosine(a, b):
        """Compute the cosine between two vectors to compare direction independently of their lengths.
        
        Example: cosine(doc, lane)
        """
        return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))
    doc, qry = embed(row["text"], "RETRIEVAL_DOCUMENT"), embed(row["text"], "RETRIEVAL_QUERY")
    print("lane vector:", len(lane), "numbers; first three", [round(v, 4) for v in lane[:3]])
    print("same text, RETRIEVAL_DOCUMENT: cosine to the lane's vector", round(cosine(doc, lane), 4))
    print("same text, RETRIEVAL_QUERY:    cosine to the lane's vector", round(cosine(qry, lane), 4))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_14', step_01_embed_one_clause_yourself_both_ways),
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
