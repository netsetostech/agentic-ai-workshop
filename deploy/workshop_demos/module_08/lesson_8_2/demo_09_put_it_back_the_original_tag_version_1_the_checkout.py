"""Lesson 8.2: Put it back: the original tag, version 1, the checkout

The order matters. Deploy the original tag first: from that moment every document the worker ingests is cut at 2000/200 again, and nothing else can be cut at 400/50 while you work. Then upload version 1's bytes: the worker finds a version it retired 30 days or less ago and answers with the undo, flipping version 1's 283 rows back and retiring the new version's 555. The undo cuts nothing, so it would bring back version 1's chunks under either worker; the deploy is what decides how the next upload is cut. The tag comes from the file step 5 wrote, so a new shell is no obstacle. The order matters. Deploy the original tag first: from that moment every document the worker ingests is cut at 2000/200 again, and nothing else can be cut at 400/50 while you work. Then upload version 1's bytes: the worker finds a version it retired 30 days or less ago and answers with the undo, flipping version 1's 283 rows back and retiring the new version's 555. The undo cuts nothing, so it would bring back version 1's chunks under either worker; the deploy is what decides how the next upload is cut. The tag comes from the file step 5 wrote, so a new shell is no obstacle. Expect back to ingest:COMMIT, the deploy's lines, the service's image back at ingest:COMMIT on a newer revision, and then make reindex's line: ingest_reactivated, version 1's key acme_497809ffbaa6..., 283 chunks, 283 reused, 0 embedded, 555 retired. Last, the checkout. The test runs once more so the kit you leave is the kit the course ships, and passes:

Run order inside this file:
1. Definition (source window 43)
2. Definition (source window 45)

Prerequisites: demo_08_reconcile_the_ledger_against_the_bucket_the_index_against_the_rows_the_golden_ro.
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


# Original CLI workflow for step_01_definition.
COMMANDS_01 = """export ORIG_SHA="$(cat ~/lesson82-orig-sha)"; echo "back to ingest:$ORIG_SHA"
make deploy-services PROJECT=$PROJECT SCRIPTS=commands/lesson-12.5.sh GIT_SHA=$ORIG_SHA > ~/lesson82-revert.log 2>&1
grep -E '^>> |has been deployed|^ERROR' ~/lesson82-revert.log
gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" --format='value(spec.template.spec.containers[0].image,status.latestReadyRevisionName)'
make reindex PROJECT=$PROJECT TENANT=acme FILE=evals/corpus/acme/hr_policy_2026.md

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    The order matters. Deploy the original tag first: from that moment every document the worker ingests is cut at 2000/200 again, and nothing else can be cut at 400/50 while you work. Then upload version 1's bytes: the worker finds a version it retired 30 days or less ago and answers with the undo, flipping version 1's 283 rows back and retiring the new version's 555. The undo cuts nothing, so it would bring back version 1's chunks under either worker; the deploy is what decides how the next upload is cut. The tag comes from the file step 5 wrote, so a new shell is no obstacle.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (one deploy, no build; then version 1 again).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/revert.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_definition.
COMMANDS_02 = """git checkout -- services/ingest/main.py shared/documind_corpus.py
grep -n "^CHUNK_CHARS" services/ingest/main.py shared/documind_corpus.py
python -m unittest commands/tests/test_twin_chunker.py 2>&1 | grep -E "^(FAIL:|AssertionError|Ran |OK|FAILED)"
git diff --quiet && echo "the checkout matches the kit again"

"""

def step_02_definition(session):
    """Run Definition at this checkpoint.

    The order matters. Deploy the original tag first: from that moment every document the worker ingests is cut at 2000/200 again, and nothing else can be cut at 400/50 while you work. Then upload version 1's bytes: the worker finds a version it retired 30 days or less ago and answers with the undo, flipping version 1's 283 rows back and retiring the new version's 555. The undo cuts nothing, so it would bring back version 1's chunks under either worker; the deploy is what decides how the next upload is cut. The tag comes from the file step 5 wrote, so a new shell is no obstacle. Expect back to ingest:COMMIT, the deploy's lines, the service's image back at ingest:COMMIT on a newer revision, and then make reindex's line: ingest_reactivated, version 1's key acme_497809ffbaa6..., 283 chunks, 283 reused, 0 embedded, 555 retired. Last, the checkout. The test runs once more so the kit you leave is the kit the course ships, and passes:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the checkout put back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: services/ingest/main.py:105:CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200
    shared/documind_corpus.py:38:CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200                     # services/ingest/main.py
    Ran 11 tests in ...s
    OK
    the checkout matches the kit again
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_43', step_01_definition),
        ('source_45', step_02_definition),
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
