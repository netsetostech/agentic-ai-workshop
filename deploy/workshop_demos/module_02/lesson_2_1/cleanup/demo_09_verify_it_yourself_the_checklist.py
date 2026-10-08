"""Lesson 2.1: Verify it yourself: the checklist

At lesson end: Run only after steps 3–9. Restore the value saved before the demo, which may be rag_engine, another backend or default. The last option removes the explicit pin. Do not assume every lane originally used RAG Engine, and do not place this command beside the setup command.

Run order inside this file:
1. Finish: restore the saved tenant pin (source window 29)

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


def step_01_finish_restore_the_saved_tenant_pin(session):
    """Run Finish: restore the saved tenant pin at this checkpoint.

    Run only after steps 3–9. Restore the value saved before the demo, which may be rag_engine, another backend or default. The last option removes the explicit pin. Do not assume every lane originally used RAG Engine, and do not place this command beside the setup command.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — end of lesson only; restore the original Acme pin.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    import json, os, warnings
    from pathlib import Path
    warnings.filterwarnings("ignore", category=UserWarning)
    from shared.tenancy import backend_for, set_backend
    project = os.environ["PROJECT"]
    os.environ["GOOGLE_CLOUD_PROJECT"] = project
    path = Path("operator-evidence/lesson51/pin-before.json")
    if not path.exists():
        raise SystemExit("STOP: no saved pin; inspect the current tenant setting before changing it.")
    before = json.loads(path.read_text())
    if before["project"] != project:
        raise SystemExit("STOP: saved pin belongs to another project.")
    current = backend_for("acme") or "default"
    if current not in ("vector", before["backend"]):
        raise SystemExit("STOP: the pin changed independently; do not overwrite it.")
    print("Acme restored:", set_backend("acme", before["backend"]))
    print("Allow up to 60 seconds for the API's tenant-setting cache.")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_29', step_01_finish_restore_the_saved_tenant_pin),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=True, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
