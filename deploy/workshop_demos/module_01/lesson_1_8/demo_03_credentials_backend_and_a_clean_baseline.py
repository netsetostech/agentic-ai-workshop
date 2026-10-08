"""Lesson 1.8: Credentials, backend and a clean baseline

Do this before presenting. Stop at an error; do not paste the next stage until its checkpoint passes. Use the same operator shell and virtual environment throughout. Create a chapter directory before changing the backend, save its original pin, and run the offline planner check. These files are local demo state; keep them out of commits.

Run order inside this file:
1. Credentials, backend and a clean baseline (source window 10)

Prerequisites: demo_02_how_reconciliation_decides.
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


def step_01_credentials_backend_and_a_clean_baseline(session):
    """Run Credentials, backend and a clean baseline at this checkpoint.

    Do this before presenting. Stop at an error; do not paste the next stage until its checkpoint passes. Use the same operator shell and virtual environment throughout. Create a chapter directory before changing the backend, save its original pin, and run the offline planner check. These files are local demo state; keep them out of commits.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT; prepare once per demonstration.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    session.state["backend_restore_required"] = True
    session.save()
    session.shell(': "${PROJECT:?run the shell setup first}"\n: "${API:?run the shell setup first}"\nexport RUN_ID="$(python -c \'import uuid; print(uuid.uuid4().hex[:10])\')"\nexport DEMO_DIR="$PWD/.lesson44/$RUN_ID"\nmkdir -p "$DEMO_DIR"\n\nch44_prepare() {\n  GOOGLE_CLOUD_PROJECT="$PROJECT" python - <<\'PY\' > "$DEMO_DIR/backend-before.txt"\nimport warnings\nwarnings.filterwarnings("ignore", category=UserWarning)\nfrom shared.tenancy import backend_for\nprint(backend_for("acme") or "default")\nPY\n  [ "$?" -eq 0 ] && [ -s "$DEMO_DIR/backend-before.txt" ] || return 1\n  make tenant-backend PROJECT="$PROJECT" TENANT=acme RETRIEVAL_BACKEND=vector || return\n  python services/ingest/reconcile.py --selftest || return\n  make reconcile PROJECT="$PROJECT" TENANT_ONLY=acme\n}\nch44_prepare')

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_credentials_backend_and_a_clean_baseline),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
