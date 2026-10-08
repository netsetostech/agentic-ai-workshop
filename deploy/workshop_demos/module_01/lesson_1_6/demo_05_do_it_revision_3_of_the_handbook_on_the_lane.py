"""Lesson 1.6: Do it: revision 3 of the handbook, on the lane

Do it

Run order inside this file:
1. Do it (source window 15)

Prerequisites: demo_04_measure_reuse_six_kinds_of_edit_rs_0.
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


# Original CLI workflow for step_01_do_it_revision_3_of_the_handbook_on_the_la.
COMMANDS_01 = """python - <<'PY'
import os, hashlib
v1 = open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()
r3 = v1.replace("# ACME Employee Handbook 2026\\n", "# ACME Employee Handbook 2026 (revision 3)\\n\\nEffective from: 2026-11-01. Revision 3 changes NP-03: the notice period for a confirmed E3 becomes 90 days.\\n", 1)
r3 = r3.replace("serves a notice period of 60 days", "serves a notice period of 90 days", 1)
path = os.path.expanduser("~/hr_policy_2026_rev3.md")
open(path, "w", encoding="utf-8", newline="\\n").write(r3)
print(path, "| version key acme_" + hashlib.sha256(r3.encode("utf-8")).hexdigest()[:12] + "...")
PY

make reindex PROJECT=$PROJECT TENANT=acme FILE=$HOME/hr_policy_2026_rev3.md NAME=hr_policy_2026.md

"""

def step_01_do_it_revision_3_of_the_handbook_on_the_la(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (writes the revision to your home directory, then one re-issue).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: /home/you/hr_policy_2026_rev3.md | version key acme_54337b4ba3f0...
    >> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)
    >> event doc_key chunks reused embedded retired effective_from
    >> ingest_ok	acme_54337b4ba3f0109a...	283	281	2	283	2026-11-01
    >> retired (doc_keys, chunks, expire days): [u'acme_497809ffbaa603c4...']	283	30
    >> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_2026.md API=<candidate url>
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_15', step_01_do_it_revision_3_of_the_handbook_on_the_la),
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
