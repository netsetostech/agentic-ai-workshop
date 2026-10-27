"""Lesson 8.2: Do it: edit both twins, then build and deploy a tagged worker

The edit is one sed line per file. Make it in the worker alone first and run the test: this is the mistake the test exists for, and you should see what it says. Then make it in the twin and run the test again. The edit is one sed line per file. Make it in the worker alone first and run the test: this is the mistake the test exists for, and you should see what it says. Then make it in the twin and run the test again. Three tests fail, and the first message names both files and both pairs. The second says what the mistake would do to the lane: acme/cgst_act_2017.md, cut into 1,536 chunks by the worker and 390 by everything offline. The third is the pinned difference, now three windows against one. Now the twin: The worker on your lane runs the image a build pushed under a tag, and the tag is GIT_SHA: by default the checkout's commit, read with git rev-parse. Your edit did not make a commit, so a build with the default tag would push the edited worker under the commit's own tag, as if it were the kit at that commit. When that commit is the one the running worker was built from, the edit replaces the original image under its own name, and a later "redeploy the original tag" deploys the edit. The cell below therefore reads the tag the worker runs now, keeps it in ~/lesson82-orig-sha (written once, so running the cell again cannot overwrite it), and builds under that tag plus -c400. It names the service and the deploy script on purpose: without SERVICES=ingest the build is every one of the seven images, and without SCRIPTS=commands/lesson-12.5.sh the deploy is every service, all under a tag only the worker has. The build's own lines go to a log; the grep shows make's >> lines, the deploy's result and any error.

Run order inside this file:
1. Definition (source window 15)
2. Definition (source window 17)
3. The tag, and the build (source window 21)

Prerequisites: demo_04_measure_before_you_deploy_the_handbook_at_eight_sizes_rs_0.
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
COMMANDS_01 = """sed -i 's/^CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200/CHUNK_CHARS, CHUNK_OVERLAP = 400, 50/' services/ingest/main.py
grep -n "^CHUNK_CHARS" services/ingest/main.py shared/documind_corpus.py
{ python -m unittest commands/tests/test_twin_chunker.py 2>&1 || true; } | grep -E "^(FAIL:|AssertionError|Ran |OK|FAILED)" | tee /tmp/twin82.txt
grep -q "^FAILED" /tmp/twin82.txt   # one twin edited: the test must fail, naming both lines

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    The edit is one sed line per file. Make it in the worker alone first and run the test: this is the mistake the test exists for, and you should see what it says. Then make it in the twin and run the test again.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (one twin only, on purpose).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: services/ingest/main.py:105:CHUNK_CHARS, CHUNK_OVERLAP = 400, 50
    shared/documind_corpus.py:38:CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200                     # services/ingest/main.py
    FAIL: test_one_size_and_one_overlap (commands.tests.test_twin_chunker.TheTwinsAgree.test_one_size_and_one_overlap)
    AssertionError: services/ingest/main.py sets CHUNK_CHARS, CHUNK_OVERLAP = 400, 50 and shared/documind_corpus.py sets 2000, 200: a chunker change edits both lines
    FAIL: test_the_corpus_at_the_kits_pair (commands.tests.test_twin_chunker.TheTwinsAgree.test_the_corpus_at_the_kits_pair)
    AssertionError: acme/cgst_act_2017.md: 1536 chunks from services/ingest/main.py, 390 from shared/documind_corpus.py
    FAIL: t
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_definition.
COMMANDS_02 = """sed -i 's/^CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200/CHUNK_CHARS, CHUNK_OVERLAP = 400, 50/' shared/documind_corpus.py
grep -n "^CHUNK_CHARS" services/ingest/main.py shared/documind_corpus.py
python -m unittest commands/tests/test_twin_chunker.py 2>&1 | grep -E "^(FAIL:|AssertionError|Ran |OK|FAILED)"
git status --short

"""

def step_02_definition(session):
    """Run Definition at this checkpoint.

    The edit is one sed line per file. Make it in the worker alone first and run the test: this is the mistake the test exists for, and you should see what it says. Then make it in the twin and run the test again. Three tests fail, and the first message names both files and both pairs. The second says what the mistake would do to the lane: acme/cgst_act_2017.md, cut into 1,536 chunks by the worker and 390 by everything offline. The third is the pinned difference, now three windows against one. Now the twin:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the other twin).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: services/ingest/main.py:105:CHUNK_CHARS, CHUNK_OVERLAP = 400, 50
    shared/documind_corpus.py:38:CHUNK_CHARS, CHUNK_OVERLAP = 400, 50                     # services/ingest/main.py
    Ran 11 tests in ...s
    OK
     M services/ingest/main.py
     M shared/documind_corpus.py
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_tag_and_the_build.
COMMANDS_03 = """[ -s ~/lesson82-orig-sha ] || gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" \\
  --format='value(spec.template.spec.containers[0].image)' | sed 's/.*://' > ~/lesson82-orig-sha
export ORIG_SHA="$(cat ~/lesson82-orig-sha)"; echo "the worker runs ingest:$ORIG_SHA; building ingest:$ORIG_SHA-c400"
make build deploy-services PROJECT=$PROJECT SERVICES=ingest SCRIPTS=commands/lesson-12.5.sh GIT_SHA=$ORIG_SHA-c400 \\
  > ~/lesson82-build.log 2>&1
grep -E '^>> |has been deployed|^ERROR' ~/lesson82-build.log
gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" --format='value(spec.template.spec.containers[0].image,status.latestReadyRevisionName)'

"""

def step_03_the_tag_and_the_build(session):
    """Run The tag, and the build at this checkpoint.

    The worker on your lane runs the image a build pushed under a tag, and the tag is GIT_SHA: by default the checkout's commit, read with git rev-parse. Your edit did not make a commit, so a build with the default tag would push the edited worker under the commit's own tag, as if it were the kit at that commit. When that commit is the one the running worker was built from, the edit replaces the original image under its own name, and a later "redeploy the original tag" deploys the edit. The cell below therefore reads the tag the worker runs now, keeps it in ~/lesson82-orig-sha (written once, so running the cell again cannot overwrite it), and builds under that tag plus -c400. It names the service and the deploy script on purpose: without SERVICES=ingest the build is every one of the seven images, and without SCRIPTS=commands/lesson-12.5.sh the deploy is every service, all under a tag only the worker has. The build's own lines go to a log; the grep shows make's >> lines, the deploy's result and any error.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Cloud Build, then one deploy: about ten minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/build_deploy.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_15', step_01_definition),
        ('source_17', step_02_definition),
        ('source_21', step_03_the_tag_and_the_build),
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
