"""Lesson B.2: Real embeddings: text-embedding-005 under the kit's task types

Do it: five texts, two requests, six cosines

Run order inside this file:
1. Do it: five texts, two requests, six cosines (source window 27)

Prerequisites: demo_07_cosine_similarity_in_numpy_on_vectors_you_can_read.
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


def step_01_five_texts_two_requests_six_cosines(session):
    """Run Do it: five texts, two requests, six cosines at this checkpoint.

    Do it: five texts, two requests, six cosines

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop, in ~/basics-venv, after the setup's Gemini block (a Python cell; two embedding requests, at most Rs 0.0011).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/embeddings.txt]
    """
    import os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import numpy as np
    from google import genai
    client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="us-central1")   # embeddings are regional, as in the kit
    MODEL, DIMS = "text-embedding-005", 768
    CLAUSES = {
        "IT-SEC-04": ("USB mass-storage devices are blocked on all company laptops. No exception is "
                      "granted for contractors. Data transfer uses the approved cloud bucket only."),
        "EXP-12": ("Domestic travel is reimbursed against original receipts, capped at Rs 40,000 per trip. "
                   "Anything above the cap needs written approval from the function head before travel, "
                   "not after."),
        "PR-05": ("Salary is credited on the last working day of each month. Form 16 is issued by 15 June "
                  "for the preceding financial year."),
    }
    QUESTIONS = {"lk-05": "Are USB drives allowed on a company laptop?",
                 "reworded": "Can I copy files to a pen drive at work?"}
    def embed(texts, task_type):
        """One request: DIMS numbers per text, under the task type given. Returns the response and the vectors.
        
        Example: embed(CLAUSES.values(), 'RETRIEVAL_DOCUMENT')
        """
        r = client.models.embed_content(model=MODEL, contents=list(texts),
                                        config={"output_dimensionality": DIMS, "task_type": task_type})
        return r, np.array([e.values for e in r.embeddings])
    def cosine(a, b):
        """Step 7's cosine: the dot product over the product of the lengths.
        
        Example: cosine(qv, dv)
        """
        return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
    rd, D = embed(CLAUSES.values(), "RETRIEVAL_DOCUMENT")    # the worker's task type for passages (indexer.py)
    rq, Q = embed(QUESTIONS.values(), "RETRIEVAL_QUERY")     # the API's task type for questions (retriever.py)
    print("clauses", D.shape, " questions", Q.shape, " lengths", np.linalg.norm(D, axis=1).round(4), np.linalg.norm(Q, axis=1).round(4))
    print("IT-SEC-04 begins", D[0, :4].round(4))
    print("tokens per text, as the model read them:", [getattr(e.statistics, "token_count", None) for e in [*rd.embeddings, *rq.embeddings]])
    for q, qv in zip(QUESTIONS, Q):
        print(f"{q:9}", "  ".join(f"{name} {cosine(qv, dv):.4f}" for name, dv in zip(CLAUSES, D)))
    sent = sum(len(t) for t in [*CLAUSES.values(), *QUESTIONS.values()])
    billed = [getattr(r.metadata, "billable_character_count", None) for r in (rd, rq)]
    print(f"characters sent {sent}, billable as reported {billed}: at most Rs {sent / 1000 * 0.000025 * 85:.4f}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_five_texts_two_requests_six_cosines),
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
