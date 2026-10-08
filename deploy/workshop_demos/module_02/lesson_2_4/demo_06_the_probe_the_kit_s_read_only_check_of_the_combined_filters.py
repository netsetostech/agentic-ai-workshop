"""Lesson 2.4: The probe: the kit's read-only check of the combined filters

Do it: the probe, then its evidence

Run order inside this file:
1. Do it: the probe, then its evidence (source window 31)

Prerequisites: demo_05_the_chaos_rung_an_index_that_will_not_answer_on_a_candidate_that_takes_no_traffi.
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


# Original CLI workflow for step_01_the_probe_then_its_evidence.
COMMANDS_01 = """export GOOGLE_CLOUD_PROJECT="$PROJECT"                                    # the probe insists the two agree
python commands/check-firestore-fallback.py
python -c "import json; r = json.load(open('operator-evidence/firestore-combined-filters.json')); print('evidence:', r['filters'], '| current off:', len(r['results']['off']['ids']), 'rows | current on:', len(r['results']['on']['ids']), 'rows | doc_key', r['doc_key'][:17] + '...')"

"""

def step_01_the_probe_then_its_evidence(session):
    """Run Do it: the probe, then its evidence at this checkpoint.

    Do it: the probe, then its evidence

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (one embedding read off a row, a few dozen Firestore reads; nothing written to the cloud).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"project": "documind-ai-YOUR-ID", "collection": "chunks", "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md", "source_status": "indexed", "source_doc_key": "acme_497809ff..."}
    Verified HR source: 283 current chunks; stored doc_type='unknown'; manifest doc_type='policy'
    NOTE: stored metadata differs from the manifest. This probe tests the stored equality filters; it does not certify policy classification or repair metadata.
    PASS: combined doc_type='unknown'+kind='text', current=off, rows=5
    PASS: combined doc_type='unknown'+kind='text', current=on, rows=5
    PASS: both Firestore filter modes verified. Evidence: operator-evidence/firestore-combined-filters.json
    evidence: {'do
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_the_probe_then_its_evidence),
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
