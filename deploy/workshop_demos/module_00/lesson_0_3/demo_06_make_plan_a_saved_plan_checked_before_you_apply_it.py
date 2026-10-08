"""Lesson 0.3: make plan: a saved plan, checked before you apply it

The check reads Terraform's machine-readable plan, not the text you scroll through. It refuses an incomplete plan, inputs that differ from the confirmed ones, any change to the existing CI trust, and any delete: a replacement is a delete followed by a create, so it is refused too. On a blank project nothing exists to delete, and the check passes. It earns its place on every plan after this one. Run it now. Terraform prints the whole plan, one block per resource, so the block keeps a copy in ~/plan.log and then prints only the lines that summarize it. The plan file is binary; Terraform turns it into JSON on request. The cell below counts what the plan would create, by type, in the same format as the count this page made from the kit's files, so the two can be read side by side. Run it before make up: the apply consumes the selection record that names the file.

Run order inside this file:
1. make plan: a saved plan, checked before you apply it (source window 34)
2. Every resource, counted from the saved plan (source window 36)

Prerequisites: demo_03_a_blank_project_made_ready_for_a_plan.
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


# Original CLI workflow for step_01_make_plan_a_saved_plan_checked_before_you.
COMMANDS_01 = """make plan PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ADMIN_EMAILS" 2>&1 | tee "$HOME/plan.log"
grep -E '^(PASS|CI trust|STOP|Plan:)|Reviewed plan|Review the' "$HOME/plan.log"

"""

def step_01_make_plan_a_saved_plan_checked_before_you(session):
    """Run make plan: a saved plan, checked before you apply it at this checkpoint.

    The check reads Terraform's machine-readable plan, not the text you scroll through. It refuses an incomplete plan, inputs that differ from the confirmed ones, any change to the existing CI trust, and any delete: a replacement is a delete followed by a create, so it is refused too. On a blank project nothing exists to delete, and the check passes. It earns its place on every plan after this one. Run it now. Terraform prints the whole plan, one block per resource, so the block keeps a copy in ~/plan.log and then prints only the lines that summarize it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_every_resource_counted_from_the_saved_plan.
COMMANDS_02 = """PLAN="$(python -c "import json; print(json.load(open('terraform/runbook-selected-plan.json'))['plan'])")"
terraform -chdir=terraform show -json "$PLAN" > "$HOME/plan.json" && echo "saved plan: $(basename "$PLAN")"
python - <<'PY'
import json, os, warnings; warnings.filterwarnings("ignore", category=UserWarning)
from collections import Counter
plan = json.load(open(os.path.expanduser("~/plan.json"), encoding="utf-8"))
changes = [rc for rc in plan["resource_changes"] if rc["mode"] == "managed"]
print("actions:", dict(Counter("/".join(rc["change"]["actions"]) for rc in changes)))
types = Counter(rc["type"] for rc in changes if rc["change"]["actions"] != ["no-op"])
for t, n in sorted(types.items(), key=lambda x: (-x[1], x[0])):
    print(f"{n:4d}  {t}")
print(f"{sum(types.values()):4d}  in all")
PY

"""

def step_02_every_resource_counted_from_the_saved_plan(session):
    """Run Every resource, counted from the saved plan at this checkpoint.

    The plan file is binary; Terraform turns it into JSON on request. The cell below counts what the plan would create, by type, in the same format as the count this page made from the kit's files, so the two can be read side by side. Run it before make up: the apply consumes the selection record that names the file.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, after make plan and before make up.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_make_plan_a_saved_plan_checked_before_you),
        ('source_36', step_02_every_resource_counted_from_the_saved_plan),
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
