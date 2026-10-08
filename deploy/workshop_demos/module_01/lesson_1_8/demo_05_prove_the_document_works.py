"""Lesson 1.8: Prove the document works

Show the source ledger in the UI and the same source's evidence from the API. On the Documents page, use Refresh indexing status and find the exact lesson44_<run-id>.md row. The first upload may need time for the worker and retrieval tier to catch up. The pin is cached for about a minute; the answer's stages prove which backend actually served it. On the Documents page, use Refresh indexing status and find the exact lesson44_<run-id>.md row. The first upload may need time for the worker and retrieval tier to catch up. The pin is cached for about a minute; the answer's stages prove which backend actually served it. Checkpoint: source indexed at this upload's generation, a cited answer naming locker Q7 in Jaipur, and no pending repair. If the source is indexed but the query has not caught up, repeat ch44_ask present and inspect its evidence; do not upload again merely to wait.

Run order inside this file:
1. Prove the document works (source window 13)
2. Prove the document works (source window 14)

Prerequisites: demo_04_create_this_chapter_s_note_and_the_checks.
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


# Original CLI workflow for step_01_prove_the_document_works.
COMMANDS_01 = """ch44_upload && ch44_ask present && ch44_plan clean

"""

def step_01_prove_the_document_works(session):
    """Run Prove the document works at this checkpoint.

    Show the source ledger in the UI and the same source's evidence from the API. On the Documents page, use Refresh indexing status and find the exact lesson44_<run-id>.md row. The first upload may need time for the worker and retrieval tier to catch up. The pin is cached for about a minute; the answer's stages prove which backend actually served it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — upload, wait for this generation, then ask and record N.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_prove_the_document_works(session):
    """Run Prove the document works at this checkpoint.

    On the Documents page, use Refresh indexing status and find the exact lesson44_<run-id>.md row. The first upload may need time for the worker and retrieval tier to catch up. The pin is cached for about a minute; the answer's stages prove which backend actually served it. Checkpoint: source indexed at this upload's generation, a cited answer naming locker Q7 in Jaipur, and no pending repair. If the source is indexed but the query has not caught up, repeat ch44_ask present and inspect its evidence; do not upload again merely to wait.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — after the checkpoint passes, save the observed chunk count.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    import json, os
    from pathlib import Path
    d=Path(os.environ["DEMO_DIR"])
    r=json.loads((d/"source.json").read_text())
    assert r["status"]=="indexed" and r["doc_key"]==os.environ["DOC_KEY"]
    assert str(r["generation"])==os.environ["CH44_GENERATION"]
    assert int(r["chunks"])>0
    (d/"initial-chunks.txt").write_text(str(r["chunks"]), encoding="utf-8")
    print("N =", r["chunks"])

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_prove_the_document_works),
        ('source_14', step_02_prove_the_document_works),
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
