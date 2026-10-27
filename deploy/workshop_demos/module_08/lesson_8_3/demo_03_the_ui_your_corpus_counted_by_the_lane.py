"""Lesson 8.3: The UI: your corpus, counted by the lane

The chunk counts the lane recorded, document by document, before any arithmetic. Every size on this page starts from one number: how many chunks a document becomes. Your lane has already counted them, document by document, when the worker ingested the corpus. Read those counts first, in the browser, where an operator would. The UI's address is built from your project number, as the setup block built API: The five Markdown documents went up as text, and the worker chunks text by exactly the rules the offline count uses, so their rows should match the table digit for digit. The Acts and the compliance handbook went up as PDFs: the worker sent each to Document AI, whose text is not byte for byte the pypdf text the offline count reads, so their counts can differ by a few chunks. Your table also has rows this one does not: the three figures, which the worker describes in words and embeds as one chunk each, and posh_act_2013, a scanned Act that only Document AI can read. The town hall is a text row unless you made its video in lesson 7.5; then the video takes its place. The same rows come from the shell. make sources reads the ledger in Firestore directly, as you, the operator, with your Application Default Credentials. The UI asked the API, as you, and the API first checked your email against acme's roster. One table, two callers: The same rows come from the shell. make sources reads the ledger in Firestore directly, as you, the operator, with your Application Default Credentials. The UI asked the API, as you, and the API first checked your email against acme's roster. One table, two callers: The last line is the ledger's summary for the tenant: its fingerprint and its count of current versions. Then the index itself. make vector-status asks gcloud to describe the Vector Search index and its deployment:

Run order inside this file:
1. The UI: your corpus, counted by the lane (source window 6)
2. The UI: your corpus, counted by the lane (source window 8)
3. The UI: your corpus, counted by the lane (source window 10)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_the_ui_your_corpus_counted_by_the_lane.
COMMANDS_01 = """echo "https://documind-ui-$NUMBER.$REGION.run.app"     # open it signed in as yourself, then Documents

"""

def step_01_the_ui_your_corpus_counted_by_the_lane(session):
    """Run The UI: your corpus, counted by the lane at this checkpoint.

    The chunk counts the lane recorded, document by document, before any arithmetic. Every size on this page starts from one number: how many chunks a document becomes. Your lane has already counted them, document by document, when the worker ingested the corpus. Read those counts first, in the browser, where an operator would. The UI's address is built from your project number, as the setup block built API:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (prints your UI's address).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: https://documind-ui-NUMBER.asia-south1.run.app
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_ui_your_corpus_counted_by_the_lane.
COMMANDS_02 = """make sources PROJECT="$PROJECT" TENANT_ONLY=acme

"""

def step_02_the_ui_your_corpus_counted_by_the_lane(session):
    """Run The UI: your corpus, counted by the lane at this checkpoint.

    The five Markdown documents went up as text, and the worker chunks text by exactly the rules the offline count uses, so their rows should match the table digit for digit. The Acts and the compliance handbook went up as PDFs: the worker sent each to Document AI, whose text is not byte for byte the pypdf text the offline count reads, so their counts can differ by a few chunks. Your table also has rows this one does not: the three figures, which the worker describes in words and embeds as one chunk each, and posh_act_2013, a scanned Act that only Document AI can read. The town hall is a text row unless you made its video in lesson 7.5; then the video takes its place. The same rows come from the shell. make sources reads the ledger in Firestore directly, as you, the operator, with your Application Default Credentials. The UI asked the API, as you, and the API first checked your email against acme's roster. One table, two callers:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the ledger; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/sources_acme.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_ui_your_corpus_counted_by_the_lane.
COMMANDS_03 = """make vector-status PROJECT="$PROJECT" REGION="$REGION"

"""

def step_03_the_ui_your_corpus_counted_by_the_lane(session):
    """Run The UI: your corpus, counted by the lane at this checkpoint.

    The same rows come from the shell. make sources reads the ledger in Firestore directly, as you, the operator, with your Application Default Credentials. The UI asked the API, as you, and the API first checked your email against acme's roster. One table, two callers: The last line is the ledger's summary for the tenant: its fingerprint and its count of current versions. Then the index itself. make vector-status asks gcloud to describe the Vector Search index and its deployment:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two gcloud describes; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/vector_status.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_the_ui_your_corpus_counted_by_the_lane),
        ('source_8', step_02_the_ui_your_corpus_counted_by_the_lane),
        ('source_10', step_03_the_ui_your_corpus_counted_by_the_lane),
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
