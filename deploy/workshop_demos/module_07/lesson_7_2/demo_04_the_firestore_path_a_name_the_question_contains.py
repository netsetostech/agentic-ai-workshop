"""Lesson 7.2: The Firestore path: a name the question contains

Do it

Run order inside this file:
1. Do it (source window 11)

Prerequisites: demo_03_the_seeders_run.
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


# Original CLI workflow for step_01_the_firestore_path_a_name_the_question_con.
COMMANDS_01 = """make graph PROJECT="$PROJECT" TENANT=acme GRAPH_ARGS='--ask "Who signs off on a big purchase?"'
make graph PROJECT="$PROJECT" TENANT=acme GRAPH_ARGS='--ask "Which purchases need the CFO?"'

"""

def step_01_the_firestore_path_a_name_the_question_con(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two walks of the Firestore graph; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: cd services/ingest && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID PYTHONPATH=../.. \\
      SPANNER_INSTANCE=documind-graph SPANNER_DATABASE=documind \\
      python graph.py --project documind-ai-YOUR-ID --tenant acme --backend firestore --ask "Who signs off on a big purchase?"
    {
     "question": "Who signs off on a big purchase?",
     "backend": "firestore",
     "seeded_by": "containment",
     "seeds": [],
     "nodes": [],
     "chunk_ids": []
    }
    cd services/ingest && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID PYTHONPATH=../.. \\
      SPANNER_INSTANCE=documind-graph SPANNER_DATABASE=documind \\
      python graph.py --project documind-ai-YOUR-ID --tenant acme --backend firestore --ask "Which purchases need the CFO?"
    {
     "question": "W
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_the_firestore_path_a_name_the_question_con),
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
