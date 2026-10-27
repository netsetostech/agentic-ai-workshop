"""Lesson 0.5: Run Terraform: init, one saved plan, the apply, the vector index

Point Terraform at its state in your bucket. A saved plan file, after validate and an input check. Apply that exact plan, then prove nothing is left to change. Run alone, in the same terminal as T6 (the plan file name is only in that shell). Run alone, in the same terminal as T6 (the plan file name is only in that shell). Confirm nothing is left to change: The index, the endpoint and the deployed ID, still empty.

Run order inside this file:
1. T5. Initialize Terraform (source window 22)
2. T5. Initialize Terraform (source window 23)
3. T6. Plan the full infrastructure (source window 24)
4. T7. Apply (source window 25)
5. T7. Apply (source window 26)
6. T8. Verify the vector index (source window 27)

Prerequisites: demo_05_prepare_terraform_the_apis_and_the_state_bucket_its_sign_in_the_billing_account.
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


# Original CLI workflow for step_01_t5_initialize_terraform.
COMMANDS_01 = """: "${TFSTATE_BUCKET:?Restore ~/rag-env.sh}" "${TFSTATE_PREFIX:?Restore ~/rag-env.sh}" "${PROJECT:?Restore ~/rag-env.sh}" &&
cd "$DEMO_ROOT/terraform" &&
terraform init -input=false -reconfigure -backend-config="bucket=$TFSTATE_BUCKET" -backend-config="prefix=$TFSTATE_PREFIX"

"""

def step_01_t5_initialize_terraform(session):
    """Run T5. Initialize Terraform at this checkpoint.

    Point Terraform at its state in your bucket.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Init.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_t5_initialize_terraform.
COMMANDS_02 = """terraform state list

"""

def step_02_t5_initialize_terraform(session):
    """Run T5. Initialize Terraform at this checkpoint.

    Point Terraform at its state in your bucket.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - State list.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_t6_plan_the_full_infrastructure.
COMMANDS_03 = """rag_plan_infrastructure() {
  : "${PROJECT:?Restore PROJECT}" "${DEMO_ROOT:?Restore DEMO_ROOT}" || return
  : "${TF_VAR_project_id:?Restore the Terraform inputs}" || return
  : "${TF_VAR_billing_account_id:?Complete the verified billing lookup}" || return
  local inputs="$DEMO_ROOT/terraform/runbook-project.auto.tfvars.json"
  python - "$PROJECT" "$TF_VAR_project_id" "$TF_VAR_billing_account_id" "$inputs" <<'RAG_INPUTS' || return 1
import json, sys
from pathlib import Path
project, terraform_project, account, filename = sys.argv[1:]
try:
    values = json.loads(Path(filename).read_text())
except (OSError, ValueError):
    raise SystemExit("STOP: rerun the verified billing lookup to save runbook-project.auto.tfvars.json.")
if not isinstance(values, dict) or not account or terraform_project != project:
    raise SystemExit("STOP: shell project/account inputs disagree; restore the intended project.")
if values.get("project_id") != project or values.get("billing_account_id") != account:
    raise SystemExit("STOP: saved project/billing inputs disagree; rerun the verified lookup.")
print("PASS: explicit plan inputs match this project's verified billing account.")
RAG_INPUTS
  cd "$DEMO_ROOT/terraform" || return
  terraform validate || return
  RAG_PLAN="rag-$(date +%Y%m%d-%H%M%S)-$$.tfplan"
  export RAG_PLAN
  terraform plan -input=false -lock-timeout=5m -parallelism=3 \\
    -var-file="$inputs" -out="$RAG_PLAN"
}
rag_plan_infrastructure

"""

def step_03_t6_plan_the_full_infrastructure(session):
    """Run T6. Plan the full infrastructure at this checkpoint.

    A saved plan file, after validate and an input check.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Plan.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_t7_apply.
COMMANDS_04 = """cd "${DEMO_ROOT:?Restore DEMO_ROOT}/terraform" &&
terraform apply -lock-timeout=5m -parallelism=3 "${RAG_PLAN:?Run T6 in this terminal first}"

"""

def step_04_t7_apply(session):
    """Run T7. Apply at this checkpoint.

    Apply that exact plan, then prove nothing is left to change. Run alone, in the same terminal as T6 (the plan file name is only in that shell).

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Apply.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_t7_apply.
COMMANDS_05 = """cd "${DEMO_ROOT:?Restore DEMO_ROOT}/terraform" &&
terraform output &&
terraform plan -input=false -lock-timeout=5m -detailed-exitcode \\
  -var-file="$DEMO_ROOT/terraform/runbook-project.auto.tfvars.json"
echo "exit code: $?"

"""

def step_05_t7_apply(session):
    """Run T7. Apply at this checkpoint.

    Run alone, in the same terminal as T6 (the plan file name is only in that shell). Confirm nothing is left to change:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Confirm.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_t8_verify_the_vector_index.
COMMANDS_06 = """(
  set -euo pipefail
  : "${DEMO_ROOT:?Complete the shell setup first}"
  : "${PROJECT:?Set the existing project ID}"
  : "${REGION:?Set the deployment region}"
  cd "$DEMO_ROOT"
  python3 commands/verify-vector-index.py \\
    --deploy-root "$DEMO_ROOT" --project "$PROJECT" --region "$REGION"
)

"""

def step_06_t8_verify_the_vector_index(session):
    """Run T8. Verify the vector index at this checkpoint.

    The index, the endpoint and the deployed ID, still empty.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Verify.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_t5_initialize_terraform),
        ('source_23', step_02_t5_initialize_terraform),
        ('source_24', step_03_t6_plan_the_full_infrastructure),
        ('source_25', step_04_t7_apply),
        ('source_26', step_05_t7_apply),
        ('source_27', step_06_t8_verify_the_vector_index),
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
