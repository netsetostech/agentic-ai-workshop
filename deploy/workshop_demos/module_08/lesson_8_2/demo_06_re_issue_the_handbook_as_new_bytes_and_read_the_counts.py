"""Lesson 8.2: Re-issue the handbook as new bytes, and read the counts

make reindex is lesson 1.6's release command: the offline gate scoped to the handbook, the upload under the handbook's name, whose event reaches the worker by the push lesson 8.1 traced, and the wait for the worker's line.

Run order inside this file:
1. Do it: write the new bytes, then re-issue (source window 26)

Prerequisites: demo_05_do_it_edit_both_twins_then_build_and_deploy_a_tagged_worker.
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


# Original CLI workflow for step_01_write_the_new_bytes_then_re_issue.
COMMANDS_01 = """python - <<'PY'
import hashlib, os
v1 = open("evals/corpus/acme/hr_policy_2026.md", "rb").read()
r4 = b"<!-- r4 -->\\n" + v1                     # version 1's text behind a comment both chunkers drop: new bytes
path = os.path.expanduser("~/hr_policy_2026_r4.md")
open(path, "wb").write(r4)
print(path, "| version key acme_" + hashlib.sha256(r4).hexdigest()[:12] + "... | version 1's acme_" + hashlib.sha256(v1).hexdigest()[:12] + "...")
PY
make reindex PROJECT=$PROJECT TENANT=acme FILE=$HOME/hr_policy_2026_r4.md NAME=hr_policy_2026.md

"""

def step_01_write_the_new_bytes_then_re_issue(session):
    """Run Do it: write the new bytes, then re-issue at this checkpoint.

    make reindex is lesson 1.6's release command: the offline gate scoped to the handbook, the upload under the handbook's name, whose event reaches the worker by the push lesson 8.1 traced, and the wait for the worker's line.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (writes the new bytes to your home directory, then one re-issue).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/reindex.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_write_the_new_bytes_then_re_issue),
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
