"""Lesson 10.3: Before you run anything: set up the shell

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The shell, in the kit, with PROJECT, REGION, NUMBER, API and tok from the block above. Steps 4 to 7 run offline at Rs 0 and need no project. Their Python cells need only the shell's own Python; the first make agent-turn or make agent-eval builds ~/graph-venv with the chat image's pins (lessons 5.4, 10.1 and 10.2 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call gemini-3.6-flash on location global, and rag-api's /v1/passages as documind-ui-sa. The bench's desk searches by class and drops every passage that has none (services/chat/desk_agent.py, _search()). Lesson 10.1's setup line gave acme's and zeta's stored rows their classes. If you have not run it, run this now: the 12 rows are acme's but one, zeta's carry-forward. A second run finds nothing to change. An exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later.

Run order inside this file:
1. Which store answers acme? Pin it to the kit's own index for this lesson (source window 3)
2. Which store answers acme? Pin it to the kit's own index for this lesson (source window 6)

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

    DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell now, before the lesson's first step.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme: retrieval_backend=vector
    """
    session.pin_vector()

# Original CLI workflow for step_02_which_store_answers_acme_pin_it_to_the_kit.
COMMANDS_02 = """for t in acme zeta; do make doc-types PROJECT="$PROJECT" TENANT=$t SEED=manifest APPLY=1; done

"""

def step_02_which_store_answers_acme_pin_it_to_the_kit(session):
    """Run Which store answers acme? Pin it to the kit's own index for this lesson at this checkpoint.

    The shell, in the kit, with PROJECT, REGION, NUMBER, API and tok from the block above. Steps 4 to 7 run offline at Rs 0 and need no project. Their Python cells need only the shell's own Python; the first make agent-turn or make agent-eval builds ~/graph-venv with the chat image's pins (lessons 5.4, 10.1 and 10.2 may have made it already), which takes a few minutes once. Step 3 uses the chat service on your lane; steps 8 and 9 call gemini-3.6-flash on location global, and rag-api's /v1/passages as documind-ui-sa. The bench's desk searches by class and drops every passage that has none (services/chat/desk_agent.py, _search()). Lesson 10.1's setup line gave acme's and zeta's stored rows their classes. If you have not run it, run this now: the 12 rows are acme's but one, zeta's carry-forward. A second run finds nothing to change. An exit status of 3 means BigQuery deferred a statement, and its last line says to run it again later.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (once, if lesson 10.1's setup line has not run: acme's and zeta's stored rows get their classes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_3', step_01_which_store_answers_acme_pin_it_to_the_kit),
        ('source_6', step_02_which_store_answers_acme_pin_it_to_the_kit),
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
