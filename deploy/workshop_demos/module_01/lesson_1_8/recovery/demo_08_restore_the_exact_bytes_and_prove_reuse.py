"""Lesson 1.8: Restore the exact bytes and prove reuse

You have shown a working document, a stale index, a planned repair, consistent absence, and a verified return. Steps 9 to 11 are separate extensions. Finish with step 12 even if you skip them: it restores the backend pin saved before the demonstration. Load this run's saved session variables first. Recover the exact generation named in its source ledger, then verify the content hash before writing the local file. Do not invent replacement text and expect a same-version reactivation. If the recorded generation is no longer retained, stop and inspect version recovery options; this path cannot reconstruct deleted bytes.

Run order inside this file:
1. Why the undo counts first (source window 25)

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


def step_01_why_the_undo_counts_first(session):
    """Run Why the undo counts first at this checkpoint.

    You have shown a working document, a stale index, a planned repair, consistent absence, and a verified return. Steps 9 to 11 are separate extensions. Finish with step 12 even if you skip them: it restores the backend pin saved before the demonstration. Load this run's saved session variables first. Recover the exact generation named in its source ledger, then verify the content hash before writing the local file. Do not invent replacement text and expect a same-version reactivation. If the recorded generation is no longer retained, stop and inspect version recovery options; this path cannot reconstruct deleted bytes.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — read the retained version; this writes only the verified local backup.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    import hashlib, os, subprocess, warnings
    from pathlib import Path
    from google.cloud import firestore
    warnings.filterwarnings("ignore", category=UserWarning)
    db=firestore.Client(project=os.environ["PROJECT"])
    row=db.collection("sources").document(os.environ["SOURCE"].replace("/", "~")).get().to_dict()
    assert row, "No source ledger entry for this fixture."
    generation=str(row.get("generation") or "")
    assert generation.isdigit(), "No recoverable generation in this ledger entry."
    data=subprocess.check_output(["gcloud", "storage", "cat",
        os.environ["OBJECT"]+"#"+generation])
    sha=hashlib.sha256(data).hexdigest()
    assert sha==row.get("sha256"), "Recovered bytes do not match the ledger."
    assert "acme_"+sha==os.environ["DOC_KEY"], "These are not this run's original bytes."
    note=Path(os.environ["NOTE"])
    if note.exists():
        assert note.read_bytes()==data, "A different local file exists; inspect it before replacing."
    else:
        note.write_bytes(data)
    print("Recovered and verified:", note)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_why_the_undo_counts_first),
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
