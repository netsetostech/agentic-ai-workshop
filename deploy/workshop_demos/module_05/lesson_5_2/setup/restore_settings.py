"""Lesson 5.2: Before you run anything: set up the shell

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done. Step 1's panel and the last point of step 7 are about doc_type filters, and a filter finds a row by its class. On your lane every text row still carries unknown, the label the worker writes, so a class filter finds nothing (lesson 2.1). make doc-types SEED=manifest writes acme's doc_type registry from the kit's evals/manifest.json: each document's class, pinned to the version it was reviewed at. Then it prints the view, one line per document, and the relabel's plan. APPLY=1 carries out the plan. It moves the stored rows to their classes in Firestore, Vector Search, Vertex AI Search and BigQuery, and expires acme's answer cache. Nothing is uploaded again, and no row is embedded again unless its vector is not the declared model's. The relabel needs the index's name, which the first line reads off your lane. Lesson 10.4 teaches the registry and the relabel in full. If make stops with error 3, BigQuery deferred a statement for rows still in its streaming buffer. The other stores are relabelled, and the same line run again later finishes it. Lesson 5.5 expects every text row unknown again, so the last cell puts the rows back when you finish this lesson. It keeps the registry.

Run order inside this file:
1. Which store answers acme? Pin it to the kit's own index for this lesson (source window 5)
2. Which store answers acme? Pin it to the kit's own index for this lesson (source window 8)

Prerequisites: workshop setup; see this lesson README.
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


def step_01_which_store_answers_acme_pin_it_to_the_kit(session):
    """Run Which store answers acme? Pin it to the kit's own index for this lesson at this checkpoint.

    DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell when you finish the lesson, not now.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    session.restore_backend()

# Original CLI workflow for step_02_which_store_answers_acme_pin_it_to_the_kit.
COMMANDS_02 = """# when you finish the lesson: acme's rows back to what the worker wrote, as lesson 5.5 expects; the registry stays
export VECTOR_INDEX_NAME="$(gcloud ai indexes list --region="$REGION" --project="$PROJECT" \\
  --filter='displayName=documind-chunks' --format='value(name)')"
make doc-types PROJECT="$PROJECT" TENANT=acme RESET=1 APPLY=1

"""

def step_02_which_store_answers_acme_pin_it_to_the_kit(session):
    """Run Which store answers acme? Pin it to the kit's own index for this lesson at this checkpoint.

    Step 1's panel and the last point of step 7 are about doc_type filters, and a filter finds a row by its class. On your lane every text row still carries unknown, the label the worker writes, so a class filter finds nothing (lesson 2.1). make doc-types SEED=manifest writes acme's doc_type registry from the kit's evals/manifest.json: each document's class, pinned to the version it was reviewed at. Then it prints the view, one line per document, and the relabel's plan. APPLY=1 carries out the plan. It moves the stored rows to their classes in Firestore, Vector Search, Vertex AI Search and BigQuery, and expires acme's answer cache. Nothing is uploaded again, and no row is embedded again unless its vector is not the declared model's. The relabel needs the index's name, which the first line reads off your lane. Lesson 10.4 teaches the registry and the relabel in full. If make stops with error 3, BigQuery deferred a statement for rows still in its streaming buffer. The other stores are relabelled, and the same line run again later finishes it. Lesson 5.5 expects every text row unknown again, so the last cell puts the rows back when you finish this lesson. It keeps the registry.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell when you finish the lesson, not now.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/doc_types_reset.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_5', step_01_which_store_answers_acme_pin_it_to_the_kit),
        ('source_8', step_02_which_store_answers_acme_pin_it_to_the_kit),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=True, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
