"""Lesson 11.8: Write an evidence handover

Summarize actual lesson attempts and retain the exact candidate gate, failures and evidence locations. This is an evidence index for a human capstone review, not an automatic rubric score.

Run order inside this file:
1. Write an evidence handover (source window plan-2)

Prerequisites: demo_01_run_the_operational_gate.
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


def step_01_write_an_evidence_handover(session):
    """Run Write an evidence handover at this checkpoint.

    Summarize actual lesson attempts and retain the exact candidate gate, failures and evidence locations. This is an evidence index for a human capstone review, not an automatic rubric score.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: Course-plan experiment — local Python/kit inspection.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    import json
    from workshop_helpers.artifacts import write_json
    records = []
    for path in sorted(session.config.results_dir.glob("module_*/lesson_*/*/session.json")):
        state = json.loads(path.read_text(encoding="utf-8"))
        records.append({"lesson": state["lesson"], "project": state["identity"]["project"], "evidence": str(path),
                        "completed": state["completed"], "failed_attempts": [a for a in state["attempts"] if a["status"] == "failed"],
                        "backend_restore_required": state.get("backend_restore_required", False)})
    write_json(session.attempt / "handover.json", records)
    print("Evidence index:", session.attempt / "handover.json")
    print("Review the capstone rubric against the actual artifacts; no score was invented.")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_demo_02_write_an_evidence_handover', step_01_write_an_evidence_handover),
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
