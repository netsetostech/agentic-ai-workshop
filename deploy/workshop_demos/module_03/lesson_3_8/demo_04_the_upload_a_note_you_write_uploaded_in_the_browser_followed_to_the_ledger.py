"""Lesson 3.8: The upload: a note you write, uploaded in the browser, followed to the ledger

First write the note on the operator machine. The page's file picker opens the computer your browser runs on, so the note has to get there. In a Cloud Workstation or the Cloud Shell editor, right-click the file in the explorer and choose Download. In a plain terminal, paste the printed text into a new file with any editor. A pasted copy can differ in its line endings, and then its hash differs from the one printed here. That is the version contract from lesson 1.1 at work, not a fault. First write the note on the operator machine. The page's file picker opens the computer your browser runs on, so the note has to get there. In a Cloud Workstation or the Cloud Shell editor, right-click the file in the explorer and choose Download. In a plain terminal, paste the printed text into a new file with any editor. A pasted copy can differ in its line endings, and then its hash differs from the one printed here. That is the version contract from lesson 1.1 at work, not a fault. In the browser, open Documents, choose the file, and click Index documents. The page reports the object it wrote and its generation, then says the upload is complete and indexing is still in progress. Wait half a minute and click Refresh indexing status until the note appears in Versions. Then follow it from the shell:

Run order inside this file:
1. Do it: write the note, upload it in the browser, follow it (source window 16)
2. Do it: write the note, upload it in the browser, follow it (source window 17)

Prerequisites: demo_03_the_front_door_iap_the_ui_s_settings_and_who_may_sign_in.
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


# Original CLI workflow for step_01_write_the_note_upload_it_in_the_browser_fo.
COMMANDS_01 = """cat > "$HOME/pune_visitor_rules.md" <<EOF
# Pune warehouse visitor rules

Synthetic note for lesson 3.8, uploaded through the DocuMind UI. Every fact is invented.

## VR-01 - Badges

Every visitor to the Pune warehouse wears an amber badge, issued at gate 2 against a photo identity card and returned at the same gate.

## VR-02 - Escorts

A visitor is escorted at all times by the host who signed them in, and visitors do not enter the loading dock.

Uploaded through the UI for lesson 3.8 by $ME on $(date -u +%F).
EOF
sha256sum "$HOME/pune_visitor_rules.md" | cut -c1-12; cat "$HOME/pune_visitor_rules.md"

"""

def step_01_write_the_note_upload_it_in_the_browser_fo(session):
    """Run Do it: write the note, upload it in the browser, follow it at this checkpoint.

    First write the note on the operator machine. The page's file picker opens the computer your browser runs on, so the note has to get there. In a Cloud Workstation or the Cloud Shell editor, right-click the file in the explorer and choose Download. In a plain terminal, paste the printed text into a new file with any editor. A pasted copy can differ in its line endings, and then its hash differs from the one printed here. That is the version contract from lesson 1.1 at work, not a fault.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (writes one small file in your home directory).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_write_the_note_upload_it_in_the_browser_fo(session):
    """Run Do it: write the note, upload it in the browser, follow it at this checkpoint.

    First write the note on the operator machine. The page's file picker opens the computer your browser runs on, so the note has to get there. In a Cloud Workstation or the Cloud Shell editor, right-click the file in the explorer and choose Download. In a plain terminal, paste the printed text into a new file with any editor. A pasted copy can differ in its line endings, and then its hash differs from the one printed here. That is the version contract from lesson 1.1 at work, not a fault. In the browser, open Documents, choose the file, and click Index documents. The page reports the object it wrote and its generation, then says the upload is complete and indexing is still in progress. Wait half a minute and click Refresh indexing status until the note appears in Versions. Then follow it from the shell:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the object, the worker's line, your hash, the ledger row).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: text/plain	4xx	17586xxxxxxxxxxx
    2026-09-2xT1x:xx:xx.xxxxxxZ	acme_3f9c2b7e1a04...	3	0	3
    your file's hash begins: 3f9c2b7e1a04
    acme/pune_visitor_rules.md indexed chunks 3 reused 0 embedded 3
    versions NN | last event ingest_ok
    """
    manual_checkpoint('In the ACME UI, Documents -> Upload: choose the exact ~/pune_visitor_rules.md created in the previous step, then Index documents. Refresh until indexed. If your browser runs elsewhere, download this exact file from the workstation first. Type done after the UI checkpoint.')
    from pathlib import Path
    from workshop_helpers.lesson31 import LessonCloud
    cloud = LessonCloud(session)
    data = (Path.home() / "pune_visitor_rules.md").read_bytes()
    expected = cloud.fixture("acme", "pune_visitor_rules.md", data, upload=False)
    observed = cloud.wait_indexed(expected)
    print("Exact UI upload:", expected, "|", observed["summary"])
    cloud.worker_logs(expected)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_write_the_note_upload_it_in_the_browser_fo),
        ('source_17', step_02_write_the_note_upload_it_in_the_browser_fo),
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
