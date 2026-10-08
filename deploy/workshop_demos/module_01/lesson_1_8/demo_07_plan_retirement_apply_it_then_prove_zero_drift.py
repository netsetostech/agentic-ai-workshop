"""Lesson 1.8: Plan retirement, apply it, then prove zero drift

Keep preview, mutation and verification as three visible operations. Keep preview, mutation and verification as three visible operations. The action must be retire for $SOURCE, with reason gone from the bucket, applied: false and drift 1. A plan is evidence, not a repair. Pause other uploads during the demonstration; the kit's apply does not execute a saved, source-scoped plan. The code that applies the plan

Run order inside this file:
1. Plan retirement, apply it, then prove zero drift (source window 16)
2. Plan retirement, apply it, then prove zero drift (source window 17)
3. The code that applies the plan (source window 20)

Prerequisites: demo_06_delete_the_cloud_file_and_show_the_stale_index.
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


# Original CLI workflow for step_01_plan_retirement_apply_it_then_prove_zero_d.
COMMANDS_01 = """ch44_plan retire

"""

def step_01_plan_retirement_apply_it_then_prove_zero_d(session):
    """Run Plan retirement, apply it, then prove zero drift at this checkpoint.

    Keep preview, mutation and verification as three visible operations.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — read-only: require exactly one repair, for this fixture.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_plan_retirement_apply_it_then_prove_zero_d.
COMMANDS_02 = """ch44_plan retire &&
  make reconcile PROJECT="$PROJECT" TENANT_ONLY=acme APPLY=1 &&
  ch44_source

"""

def step_02_plan_retirement_apply_it_then_prove_zero_d(session):
    """Run Plan retirement, apply it, then prove zero drift at this checkpoint.

    Keep preview, mutation and verification as three visible operations. The action must be retire for $SOURCE, with reason gone from the bucket, applied: false and drift 1. A plan is evidence, not a repair. Pause other uploads during the demonstration; the kit's apply does not execute a saved, source-scoped plan.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — recheck immediately before the tenant-wide apply.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_code_that_applies_the_plan.
COMMANDS_03 = """ch44_source &&
python - <<'PY'
import json, os
from pathlib import Path
r=json.loads(Path(os.environ["DEMO_DIR"], "source.json").read_text())
assert r["status"]=="retired", "Do not continue until this exact source is retired."
print("The fixture is retired.")
PY
ch44_ask absent
ch44_plan clean

"""

def step_03_the_code_that_applies_the_plan(session):
    """Run The code that applies the plan at this checkpoint.

    The code that applies the plan

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — verify retirement, citations and the next read-only plan.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_plan_retirement_apply_it_then_prove_zero_d),
        ('source_17', step_02_plan_retirement_apply_it_then_prove_zero_d),
        ('source_20', step_03_the_code_that_applies_the_plan),
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
