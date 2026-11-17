"""Lesson 0.5: Prepare Terraform: the APIs and the state bucket, its sign-in, the billing account, the inputs

40 APIs, the service agents, the versioned state bucket. Before you start, finish Phase 1 (S1 to S6) in this terminal with the Python environment active. The API list is the block make apis runs; this step adds the service agents and the state bucket. Application Default Credentials and the quota project. Run this alone, open the URL and sign in with your operator account: The billing account Terraform's budget needs, verified and saved. Every input the kit's make plan would pass, and the CI trust, saved into the same inputs file. Inputs not listed keep their variables.tf defaults: the Google Chat door, the Desk job and GKE Autopilot stay off. The CI trust (terraform/wif.tf) lets GitHub Actions workflows from one repository, on one branch, become sa-documind-cicd in your project with no key file. That account can deploy code that runs as your services, so the repository must be one you own. It is never the repository you cloned: netsetos/agents_workshop_learner is the course author's, and trusting it would let the author's workflows deploy into your lane. On GitHub, open that repository and choose Fork; your fork is YOUR-GITHUB-USER/agents_workshop_learner. Lesson 11.1 builds and deploys through this trust. Name your fork in GH_REPO; the block looks up its numeric id, the value the trust is really keyed on, and stops on the author's repository or an empty answer.

Run order inside this file:
1. T1. Enable APIs, service agents and the state bucket (source window 17)
2. T2. Sign in Terraform and set its quota project (source window 18)
3. T2. Sign in Terraform and set its quota project (source window 19)
4. T3. Save the billing account for Terraform (source window 20)
5. T4. Set the Terraform inputs (source window 21)

Prerequisites: demo_04_prepare_python_and_the_kit_the_3_12_environment_the_clone_from_main_the_dependen.
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


# Original CLI workflow for step_01_t1_enable_apis_service_agents_and_the_stat.
COMMANDS_01 = """(
set -euo pipefail
: "${PROJECT:?Restore ~/rag-env.sh}" "${PROJECT_NUMBER:?Restore ~/rag-env.sh}" "${REGION:?Restore ~/rag-env.sh}"
: "${DEMO_ROOT:?Restore ~/rag-env.sh}" "${TFSTATE_BUCKET:?Restore ~/rag-env.sh}"
cd "$DEMO_ROOT"
# The repository's API list (40 services, two batches) from commands/lesson-12.1.sh.
api_block="$(sed -n '/^# ---- ENABLE_APIS ----/,/^# ---- APPLY ----/p' commands/lesson-12.1.sh | sed '/^# ----/d')"
[[ -n "$api_block" ]] || { echo 'STOP: ENABLE_APIS block not found in commands/lesson-12.1.sh.' >&2; exit 1; }
sh -ec "$api_block"
# Two the full Terraform also needs that are not in that list.
gcloud services enable iam.googleapis.com sts.googleapis.com --project="$PROJECT"
# Google-managed service agents Terraform grants roles to.
for svc in pubsub.googleapis.com aiplatform.googleapis.com clouddeploy.googleapis.com cloudbuild.googleapis.com; do
  gcloud beta services identity create --service="$svc" --project="$PROJECT"
done
gcloud storage service-agent --project="$PROJECT"
# off.tf reads the Compute Engine default service account; it must exist and be enabled.
gcloud iam service-accounts describe "$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \\
  --project="$PROJECT" --format='yaml(email,disabled)'
# Terraform state bucket: reuse it if it exists, create it only if it is really absent.
if out="$(gcloud storage buckets describe "gs://$TFSTATE_BUCKET" --project="$PROJECT" --format='value(name)' 2>&1)"; then
  echo "REUSE: gs://$TFSTATE_BUCKET already exists"
elif grep -qiE 'not found|404' <<<"$out"; then
  gcloud storage buckets create "gs://$TFSTATE_BUCKET" --project="$PROJECT" \\
    --location="$REGION" --uniform-bucket-level-access --public-access-prevention
else
  printf '%s\\n' "$out" >&2
  echo 'STOP: bucket lookup failed for a reason other than not-found. Fix access first.' >&2
  exit 1
fi
gcloud storage buckets update "gs://$TFSTATE_BUCKET" --versioning
echo 'PASS: APIs, service agents and state bucket ready.'
)

"""

def step_01_t1_enable_apis_service_agents_and_the_stat(session):
    """Run T1. Enable APIs, service agents and the state bucket at this checkpoint.

    40 APIs, the service agents, the versioned state bucket. Before you start, finish Phase 1 (S1 to S6) in this terminal with the Python environment active. The API list is the block make apis runs; this step adds the service agents and the state bucket.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - APIs and state bucket.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_t2_sign_in_terraform_and_set_its_quota_pro.
COMMANDS_02 = """gcloud auth application-default login --no-launch-browser

"""

def step_02_t2_sign_in_terraform_and_set_its_quota_pro(session):
    """Run T2. Sign in Terraform and set its quota project at this checkpoint.

    Application Default Credentials and the quota project. Run this alone, open the URL and sign in with your operator account:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - ADC login.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_t2_sign_in_terraform_and_set_its_quota_pro.
COMMANDS_03 = """# Use the deployment project ID, not a billing account ID or gcloud's shared project.
: "${PROJECT:?Restore the existing deployment project ID}"
export OPERATOR_EMAIL="${OPERATOR_EMAIL:-$(gcloud config get-value account 2>/dev/null)}"
[[ -n "$OPERATOR_EMAIL" ]] || { echo 'STOP: no operator account; run gcloud auth login first.' >&2; false; } &&
gcloud config set project "$PROJECT" &&
gcloud config set billing/quota_project "$PROJECT" &&
gcloud auth application-default set-quota-project "$PROJECT" &&
gcloud auth application-default print-access-token >/dev/null &&
echo "PASS: Terraform credentials ready, quota project $PROJECT"

"""

def step_03_t2_sign_in_terraform_and_set_its_quota_pro(session):
    """Run T2. Sign in Terraform and set its quota project at this checkpoint.

    Application Default Credentials and the quota project. Run this alone, open the URL and sign in with your operator account:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Quota project.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_t3_save_the_billing_account_for_terraform.
COMMANDS_04 = """rag_load_project_billing() {
  : "${PROJECT:?Restore the intended project ID}" "${DEMO_ROOT:?Restore DEMO_ROOT}" "${REGION:?Restore REGION}" || return
  unset BILLING_ACCOUNT_NAME BILLING_ACCOUNT_ID TF_VAR_billing_account_id
  BILLING_ACCOUNT_ID="$(python - "$PROJECT" "$DEMO_ROOT" "$REGION" <<'RAG_BILLING'
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

project, root, region = sys.argv[1:]
flags = [f"--project={project}", f"--billing-project={project}", "--format=json"]
def read_gcloud(args):
    try:
        return json.loads(subprocess.check_output(["gcloud", *args, *flags], text=True))
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise SystemExit(f"STOP: cannot verify project billing; no inputs were saved ({type(exc).__name__}).")
info = read_gcloud(["projects", "describe", project])
if info.get("projectId") != project or info.get("lifecycleState") != "ACTIVE":
    raise SystemExit("STOP: PROJECT must identify the intended ACTIVE project.")
billing = read_gcloud(["billing", "projects", "describe", project])
if billing.get("projectId") != project or billing.get("billingEnabled") is not True:
    raise SystemExit("STOP: billing is not enabled for the intended project.")
match = re.fullmatch(r"billingAccounts/([0-9A-Za-z]{6}-[0-9A-Za-z]{6}-[0-9A-Za-z]{6})",
                     billing.get("billingAccountName") or "")
if not match or match.group(1) == "000000-000000-000000":
    raise SystemExit("STOP: the linked billing account ID is missing or invalid.")
account = match.group(1).upper()
target = Path(root) / "terraform" / "runbook-project.auto.tfvars.json"
if not target.parent.is_dir():
    raise SystemExit("STOP: restore DEMO_ROOT to the existing deployment directory.")
try:
    values = json.loads(target.read_text()) if target.exists() else {}
except (OSError, json.JSONDecodeError):
    raise SystemExit("STOP: inspect the existing runbook-project.auto.tfvars.json; it was not replaced.")
if not isinstance(values, dict):
    raise SystemExit("STOP: runbook-project.auto.tfvars.json must contain a JSON object.")
if values.get("project_id") not in (None, "", project):
    raise SystemExit("STOP: saved inputs belong to another project; verify the state/backend before proceeding.")
if values.get("region") not in (None, "", region):
    raise SystemExit("STOP: saved inputs name another region; a region move is a separate reviewed migration.")
values.update(project_id=project, region=region, billing_account_id=account)
with tempfile.NamedTemporaryFile(mode="w", dir=target.parent, prefix=".rag-inputs-", delete=False) as f:
    json.dump(values, f, indent=2)
    f.write("\\n")
    temporary = Path(f.name)
try:
    temporary.replace(target)
finally:
    temporary.unlink(missing_ok=True)
print(account)
RAG_BILLING
)" || return
  BILLING_ACCOUNT_NAME="billingAccounts/$BILLING_ACCOUNT_ID"
  export BILLING_ACCOUNT_NAME BILLING_ACCOUNT_ID
  export TF_VAR_billing_account_id="$BILLING_ACCOUNT_ID"
  printf 'PASS: verified active project %s and linked billing account %s.\\n' "$PROJECT" "$BILLING_ACCOUNT_ID"
  printf 'Saved Terraform inputs: %s/terraform/runbook-project.auto.tfvars.json\\n' "$DEMO_ROOT"
}

rag_load_project_billing

"""

def step_04_t3_save_the_billing_account_for_terraform(session):
    """Run T3. Save the billing account for Terraform at this checkpoint.

    The billing account Terraform's budget needs, verified and saved.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Billing lookup.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_t4_set_the_terraform_inputs.
COMMANDS_05 = """export GH_REPO=YOUR-GITHUB-USER/agents_workshop_learner   # your fork: a repository you own
rag_configure_terraform_inputs() {
  [[ "${GH_REPO:-}" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ && "$GH_REPO" != YOUR-GITHUB-USER/* ]] || {
    printf 'STOP: export GH_REPO=OWNER/REPO, your fork of the kit, before this block.\\n' >&2
    return 1
  }
  [[ "${GH_REPO,,}" != "netsetos/agents_workshop_learner" ]] || {
    printf 'STOP: %s is the course author'"'"'s repository; trusting it would let its workflows deploy into your project. Fork it and name your fork.\\n' "$GH_REPO" >&2
    return 1
  }
  [[ "${GH_REPO_ID:-}" =~ ^[1-9][0-9]*$ ]] ||
    GH_REPO_ID="$(curl -s "https://api.github.com/repos/$GH_REPO" | python -c 'import json,sys; print(json.load(sys.stdin).get("id", ""))')"
  [[ "$GH_REPO_ID" =~ ^[1-9][0-9]*$ ]] || {
    printf 'STOP: GitHub returned no numeric id for %s. Check the name; for a private repository, export GH_REPO_ID from: gh api repos/%s --jq .id\\n' "$GH_REPO" "$GH_REPO" >&2
    return 1
  }
  [[ "${BILLING_ACCOUNT_ID:-}" =~ ^[0-9A-Za-z]{6}-[0-9A-Za-z]{6}-[0-9A-Za-z]{6}$ && "$BILLING_ACCOUNT_ID" != "000000-000000-000000" ]] || {
    printf 'STOP: complete the verified project-billing lookup (T3) first.\\n' >&2
    return 1
  }
  [[ -n "${OPERATOR_EMAIL:-}" && -n "${REGION:-}" && -n "${RESIDENCY:-}" && -n "${DEMO_ROOT:-}" ]] || {
    printf 'STOP: OPERATOR_EMAIL, REGION, RESIDENCY or DEMO_ROOT is empty; restore ~/rag-env.sh.\\n' >&2
    return 1
  }
  export TF_VAR_project_id="$PROJECT"
  export TF_VAR_github_repository="$GH_REPO"
  export TF_VAR_github_repository_id="$GH_REPO_ID"
  export TF_VAR_billing_account_id="$BILLING_ACCOUNT_ID"
  export TF_VAR_pagerduty_key='unset-in-dryrun'
  export TF_VAR_region="$REGION"
  export TF_VAR_india_region='asia-south1'
  export TF_VAR_residency="$RESIDENCY"
  export TF_VAR_env='dev'
  export TF_VAR_audit_lock='false'
  export TF_VAR_gemini_quota_override='false'
  export TF_VAR_budget_amount='5000'
  export TF_VAR_budget_currency=''
  export TF_VAR_budget_pubsub='false'
  export TF_VAR_alert_channels='[]'
  export TF_VAR_alert_emails="[\\"$OPERATOR_EMAIL\\"]"
  export TF_VAR_enforce_no_sa_keys='false'
  export TF_VAR_deploy_ref='refs/heads/main'
  export TF_VAR_embedding_model='text-embedding-005'
  export TF_VAR_embedding_version='1'
  export TF_VAR_retention_days='30'
  export TF_VAR_managed_search='true'
  export TF_VAR_managed_mirror='both'
  export TF_VAR_tenants='["acme","zeta"]'
  export TF_VAR_reconcile_job='false'
  export TF_VAR_batch_job='false'
  export TF_VAR_reconcile_image=''
  python - "$DEMO_ROOT/terraform/runbook-project.auto.tfvars.json" "$TF_VAR_github_repository" "$TF_VAR_github_repository_id" "$TF_VAR_deploy_ref" <<'RAG_TRUST' || return 1
import json, sys
from pathlib import Path
target, repository, repository_id, ref = sys.argv[1:]
path = Path(target)
values = json.loads(path.read_text()) if path.exists() else {}
values.update(github_repository=repository, github_repository_id=repository_id, deploy_ref=ref)
path.write_text(json.dumps(values, indent=2) + "\\n")
print("PASS: CI trust saved to", path.name)
RAG_TRUST
  printf 'Terraform project: %s\\nTerraform region: %s\\nGitHub repository: %s (%s)\\nDeploy ref: %s\\nBilling account: %s\\nManaged mirror: %s\\nAlert email: %s\\n' "$TF_VAR_project_id" "$TF_VAR_region" "$TF_VAR_github_repository" "$TF_VAR_github_repository_id" "$TF_VAR_deploy_ref" "$TF_VAR_billing_account_id" "$TF_VAR_managed_mirror" "$OPERATOR_EMAIL"
}
rag_configure_terraform_inputs &&
source "$HOME/rag-save-env.sh"

"""

def step_05_t4_set_the_terraform_inputs(session):
    """Run T4. Set the Terraform inputs at this checkpoint.

    Every input the kit's make plan would pass, and the CI trust, saved into the same inputs file. Inputs not listed keep their variables.tf defaults: the Google Chat door, the Desk job and GKE Autopilot stay off. The CI trust (terraform/wif.tf) lets GitHub Actions workflows from one repository, on one branch, become sa-documind-cicd in your project with no key file. That account can deploy code that runs as your services, so the repository must be one you own. It is never the repository you cloned: netsetos/agents_workshop_learner is the course author's, and trusting it would let the author's workflows deploy into your lane. On GitHub, open that repository and choose Fork; your fork is YOUR-GITHUB-USER/agents_workshop_learner. Lesson 11.1 builds and deploys through this trust. Name your fork in GH_REPO; the block looks up its numeric id, the value the trust is really keyed on, and stops on the author's repository or an empty answer.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Inputs (your fork, not the example's).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_t1_enable_apis_service_agents_and_the_stat),
        ('source_18', step_02_t2_sign_in_terraform_and_set_its_quota_pro),
        ('source_19', step_03_t2_sign_in_terraform_and_set_its_quota_pro),
        ('source_20', step_04_t3_save_the_billing_account_for_terraform),
        ('source_21', step_05_t4_set_the_terraform_inputs),
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
