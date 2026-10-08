"""Lesson 4.2: The offline half: on every push, and CI's verdict on the commit you run

Do it: the gate as CI runs it, and CI's result on your commit The next cell asks GitHub's public API which commits the dry run has judged, and marks the one your clone is at.

Run order inside this file:
1. Do it: the gate as CI runs it, and CI's result on your commit (source window 8)
2. Do it: the gate as CI runs it, and CI's result on your commit (source window 10)

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


# Original CLI workflow for step_01_the_gate_as_ci_runs_it_and_ci_s_result_on.
COMMANDS_01 = """make eval

"""

def step_01_the_gate_as_ci_runs_it_and_ci_s_result_on(session):
    """Run Do it: the gate as CI runs it, and CI's result on your commit at this checkpoint.

    Do it: the gate as CI runs it, and CI's result on your commit

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the offline half, as CI runs it).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/run_eval.py
    == eval gate: OFFLINE (no credentials, no cost) ==
      65 golden rows over 3 tenants, 27 documents

      [PASS] falsifiable
      [PASS] anchors
      [PASS] coverage

      The golden set is sound. It can go red, and it still contains the rows that would.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_the_gate_as_ci_runs_it_and_ci_s_result_on(session):
    """Run Do it: the gate as CI runs it, and CI's result on your commit at this checkpoint.

    The next cell asks GitHub's public API which commits the dry run has judged, and marks the one your clone is at.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one unauthenticated call to GitHub's public API).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: your kit is at b89bbd8
      b89bbd8  push  success  2026-09-23  <- the commit you run
      6999d24  push  success  2026-09-22
    """
    import json, subprocess, urllib.request
    url = "https://api.github.com/repos/netsetos/agents_workshop_learner/actions/workflows/documind-dryrun.yml/runs?per_page=3"
    runs = json.load(urllib.request.urlopen(url, timeout=30))["workflow_runs"]
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    print("your kit is at", head[:7])
    for r in runs:
        mark = "  <- the commit you run" if r["head_sha"] == head else ""
        print(f"  {r['head_sha'][:7]}  {r['event']:5} {r['conclusion'] or r['status']:8} {r['created_at'][:10]}{mark}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_8', step_01_the_gate_as_ci_runs_it_and_ci_s_result_on),
        ('source_10', step_02_the_gate_as_ci_runs_it_and_ci_s_result_on),
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
