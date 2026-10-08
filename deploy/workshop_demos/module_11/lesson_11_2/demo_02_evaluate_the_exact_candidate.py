"""Lesson 11.2: Evaluate the exact candidate

Resolve the candidate tag and require it to name the recorded revision before the live gate. Save a project/region/revision-bound gate record only after the evaluator exits successfully.

Run order inside this file:
1. Evaluate the exact candidate (source window plan-2)

Prerequisites: demo_01_create_the_recorded_candidate.
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


def step_01_evaluate_the_exact_candidate(session):
    """Run Evaluate the exact candidate at this checkpoint.

    Resolve the candidate tag and require it to name the recorded revision before the live gate. Save a project/region/revision-bound gate record only after the evaluator exits successfully.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: Course-plan experiment — live deployment.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: A successful live gate tied to the same recorded candidate revision.
    """
    import json, os, sys
    from pathlib import Path
    from workshop_helpers.auth import gcloud
    from workshop_helpers.artifacts import write_json
    expected = Path(".candidate-revision").read_text().strip()
    service = json.loads(gcloud("run", "services", "describe", "documind-api", "--project=" + session.config.project, "--region=" + session.config.cloud_run_region, "--format=json"))
    tagged = next(row for row in service["status"]["traffic"] if row.get("tag") == "candidate")
    assert tagged["revisionName"] == expected, "The candidate tag moved; evaluate the intended revision."
    report = session.attempt / "candidate_gate.json"
    session.command(["make", "eval-live", "PROJECT=" + session.config.project, "REGION=" + session.config.cloud_run_region, "API=" + tagged["url"], "REPORT=" + str(report), "PY=" + sys.executable])
    gate = {"project": session.config.project, "region": session.config.cloud_run_region, "revision": expected, "report": str(report), "passed": True}
    write_json(session.config.results_dir / "release_gate.json", gate)
    print("Gate passed for:", expected)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_demo_02_evaluate_the_exact_candidate', step_01_evaluate_the_exact_candidate),
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
