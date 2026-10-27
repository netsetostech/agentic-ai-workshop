"""Lesson 0.5: Restore the shell, pin GIT_SHA, export the runtime settings and prepare the secrets

Settings back, Python checked, and the commit every image is built from. Run this first in every new terminal. It restores the settings saved in Phases 1 and 2, activates Python 3.12, loads the repository helpers from commands/session-restart.sh and checks Terraform and the Python dependencies. It changes nothing in the cloud. Ends with PASS: shell restored. A Python STOP means rerun S7; a sign-in error means gcloud auth login, and for Terraform also T2. Now pin GIT_SHA: the exact commit every image is built from and every service is deployed with. The first time, it records the commit you have checked out. After that, it checks the checkout still matches. Its form is the short hash, the one the kit's own make build tags images with (GIT_SHA ?= git rev-parse --short HEAD in the Makefile), so a later make deploy-services or make promote finds these images. Never set GIT_SHA by hand to a value that was not built. If you see the “not the checked-out commit” STOP, choose one of the two options it prints; do not mix images from different commits. Check Python syntax in the build inputs: The runtime settings every deploy reads, from Terraform's outputs. Run only after the full reviewed Terraform plan has been applied. A missing or empty output is a stop condition. This block must run in your main shell (not a subshell) because it exports variables for every later step. Rerun it after any restart. The UI's cookie secret and the chat checkpoint DSN. Terraform creates cookie-secret as an empty holder. The UI and admin services mount :latest, so it needs one enabled version. A permission error must be fixed; it is not evidence that no version exists.

Run order inside this file:
1. Restore the shell and pin GIT_SHA (source window 28)
2. Restore the shell and pin GIT_SHA (source window 29)
3. Restore the shell and pin GIT_SHA (source window 30)
4. F1. Export runtime settings from Terraform state (source window 31)
5. F1. Export runtime settings from Terraform state (source window 32)
6. F2. Prepare cookie-secret and the checkpoint DSN (source window 33)

Prerequisites: demo_06_run_terraform_init_one_saved_plan_the_apply_the_vector_index.
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


# Original CLI workflow for step_01_restore_the_shell_and_pin_git_sha.
COMMANDS_01 = """source "$HOME/rag-shell-venv/bin/activate" &&
hash -r &&
source "$HOME/rag-env.sh" &&
export PROJECT_ID="$PROJECT" GOOGLE_CLOUD_PROJECT="$PROJECT" GOOGLE_CLOUD_QUOTA_PROJECT="$PROJECT" \\
       CLOUDSDK_CORE_PROJECT="$PROJECT" CLOUDSDK_BILLING_QUOTA_PROJECT="$PROJECT" \\
       DEPLOY_ROOT="$DEMO_ROOT" PYTHONPATH="$DEMO_ROOT" &&
gcloud config set project "$PROJECT" &&
source "$DEMO_ROOT/commands/session-restart.sh" &&
rag_require_terraform &&
rag_check_python_dependencies &&
gcloud auth print-access-token >/dev/null &&
cd "$DEMO_ROOT" &&
echo "PASS: shell restored for $PROJECT in $REGION; GIT_SHA=[${GIT_SHA:-not pinned yet}]"

"""

def step_01_restore_the_shell_and_pin_git_sha(session):
    """Run Restore the shell and pin GIT_SHA at this checkpoint.

    Settings back, Python checked, and the commit every image is built from. Run this first in every new terminal. It restores the settings saved in Phases 1 and 2, activates Python 3.12, loads the repository helpers from commands/session-restart.sh and checks Terraform and the Python dependencies. It changes nothing in the cloud.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Restore.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_restore_the_shell_and_pin_git_sha.
COMMANDS_02 = """rag_pin_snapshot() {
  : "${DEMO_ROOT:?Run the restore block first}"
  grep -q 'GIT_SHA' "$HOME/rag-save-env.sh" 2>/dev/null || {
    echo 'STOP: ~/rag-save-env.sh does not save GIT_SHA. Rerun the "Save settings" block from S3, then rerun this block.' >&2
    return 1
  }
  local head dirty
  head="$(git -C "$DEMO_ROOT" rev-parse --short --verify 'HEAD^{commit}')" || return
  dirty="$(git -C "$DEMO_ROOT" status --porcelain -- shared services cloudbuild.yaml)" || return
  if [[ -n "$dirty" ]]; then
    printf 'STOP: build inputs have local changes, so images would not match any commit:\\n%s\\n' "$dirty" >&2
    return 1
  fi
  if [[ -z "${GIT_SHA:-}" ]]; then
    export GIT_SHA="$head"
    echo "PINNED: GIT_SHA set to the checked-out commit (its short hash, the form make build tags with)."
  elif [[ "$GIT_SHA" != "$head" ]]; then
    printf 'STOP: saved GIT_SHA %s is not the checked-out commit %s.\\n' "$GIT_SHA" "$head" >&2
    printf 'Choose one: keep the built images (git -C "$DEMO_ROOT" checkout --detach "$GIT_SHA"), or adopt the new code (unset GIT_SHA, rerun this block, then rebuild every image in F3).\\n' >&2
    return 1
  else
    echo "PASS: GIT_SHA matches the checked-out commit."
  fi
  git -C "$DEMO_ROOT" log -1 --format='Snapshot: %H (%cd) %s' "$GIT_SHA" &&
  source "$HOME/rag-save-env.sh"
}
rag_pin_snapshot

"""

def step_02_restore_the_shell_and_pin_git_sha(session):
    """Run Restore the shell and pin GIT_SHA at this checkpoint.

    Ends with PASS: shell restored. A Python STOP means rerun S7; a sign-in error means gcloud auth login, and for Terraform also T2. Now pin GIT_SHA: the exact commit every image is built from and every service is deployed with. The first time, it records the commit you have checked out. After that, it checks the checkout still matches. Its form is the short hash, the one the kit's own make build tags images with (GIT_SHA ?= git rev-parse --short HEAD in the Makefile), so a later make deploy-services or make promote finds these images.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Pin GIT_SHA.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_restore_the_shell_and_pin_git_sha.
COMMANDS_03 = """(
  set -euo pipefail
  cd "${DEMO_ROOT:?Restore DEMO_ROOT}"
  "$HOME/rag-shell-venv/bin/python" -m compileall -q shared services/rag-api services/ingest
  echo 'PASS: Python syntax'
)

"""

def step_03_restore_the_shell_and_pin_git_sha(session):
    """Run Restore the shell and pin GIT_SHA at this checkpoint.

    Never set GIT_SHA by hand to a value that was not built. If you see the “not the checked-out commit” STOP, choose one of the two options it prints; do not mix images from different commits. Check Python syntax in the build inputs:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Syntax check.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_f1_export_runtime_settings_from_terraform.
COMMANDS_04 = """rag_export_full_runtime_settings() {
  : "${DEMO_ROOT:?Restore DEMO_ROOT}" "${PROJECT:?Restore PROJECT}" "${REGION:?Restore REGION}" "${OPERATOR_EMAIL:?Restore OPERATOR_EMAIL}"
  cd "$DEMO_ROOT" || return
  export PATH="$PATH:$HOME/.local/bin:/usr/local/bin:/usr/bin"
  hash -r
  command -v terraform >/dev/null || { printf '%s\\n' 'STOP: install Terraform using S4, then rerun F1.' >&2; return 127; }
  local rag_project_number rag_output rag_value
  local -A rag_outputs=()
  rag_project_number="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')" || return
  [[ "$rag_project_number" =~ ^[0-9]+$ ]] || { printf '%s\\n' 'STOP: project number was not returned.' >&2; return 1; }
  for rag_output in docai_processor_id docai_location vector_index_endpoint vector_deployed_index_id vector_index_name checkpoint_instance retention_days embedding_model embedding_version spanner_instance spanner_database; do
    rag_value="$(terraform -chdir=terraform output -raw "$rag_output")" || { printf 'STOP: cannot read Terraform output %s.\\n' "$rag_output" >&2; return 1; }
    [[ -n "${rag_value//[[:space:]]/}" ]] || { printf 'STOP: Terraform output %s is empty.\\n' "$rag_output" >&2; return 1; }
    rag_outputs[$rag_output]="$rag_value"
  done
  export PROJECT_NUMBER="$rag_project_number"
  export IMAGE_REPO="$REGION-docker.pkg.dev/$PROJECT/documind"
  export BUILD_SA="sa-documind-cicd@$PROJECT.iam.gserviceaccount.com"
  export DOCAI_PROCESSOR_ID="${rag_outputs[docai_processor_id]}"
  export DOCAI_LOCATION="${rag_outputs[docai_location]}"
  export VECTOR_INDEX_ENDPOINT="${rag_outputs[vector_index_endpoint]}"
  export VECTOR_DEPLOYED_INDEX_ID="${rag_outputs[vector_deployed_index_id]}"
  export VECTOR_INDEX_NAME="${rag_outputs[vector_index_name]}"
  export CHECKPOINT_INSTANCE="${rag_outputs[checkpoint_instance]}"
  export RETENTION_DAYS="${rag_outputs[retention_days]}"
  export EMBEDDING_MODEL="${rag_outputs[embedding_model]}"
  export EMBEDDING_VERSION="${rag_outputs[embedding_version]}"
  export BQ_CHUNK_TABLE="$PROJECT.rag_data.chunk_source"
  export RETRIEVAL_BACKEND='vector'
  export RETRIEVAL_CURRENT_ONLY='on'
  export RETRIEVAL_GRAPH='off'
  export GRAPH_BACKEND='firestore'
  export SPANNER_INSTANCE="${rag_outputs[spanner_instance]}"
  export SPANNER_DATABASE="${rag_outputs[spanner_database]}"
  export BATCH_JOB_NAME=''
  export MANAGED_MIRROR='both'
  export RAG_LOCATION='us-central1'
  export SEARCH_LOCATION='global'
  export AUDIT_BUCKET="$PROJECT-audit"
  export GENERATOR_MODEL='gemini-3.6-flash'
  export RAG_MODEL_BASE="$GENERATOR_MODEL"
  export MODEL_BACKEND='vertex'
  export ROUTING='off'
  export ARMOR='off'
  export SEMANTIC_CACHE='off'
  export DEMO_MODE='1'
  export BUDGET_USD='100'
  export MIN_INSTANCES='0'
  export ADMIN_EMAILS="${ADMIN_EMAILS:-$OPERATOR_EMAIL}"
  export ADMIN_DOMAINS="${ADMIN_DOMAINS:-}"
  export API_URL="https://documind-api-$PROJECT_NUMBER.$REGION.run.app"
  export CHAT_URL="https://documind-chat-$PROJECT_NUMBER.$REGION.run.app"
  export UI_URL="https://documind-ui-$PROJECT_NUMBER.$REGION.run.app"
  export ADMIN_URL="https://documind-admin-$PROJECT_NUMBER.$REGION.run.app"
  export MCP_URL="https://documind-mcp-$PROJECT_NUMBER.$REGION.run.app"
  export AGENT_URL="https://documind-agent-$PROJECT_NUMBER.$REGION.run.app"
  printf '%s\\n' 'PASS: runtime settings exported from successful, nonempty Terraform outputs.'
}
rag_export_full_runtime_settings

"""

def step_04_f1_export_runtime_settings_from_terraform(session):
    """Run F1. Export runtime settings from Terraform state at this checkpoint.

    The runtime settings every deploy reads, from Terraform's outputs. Run only after the full reviewed Terraform plan has been applied. A missing or empty output is a stop condition. This block must run in your main shell (not a subshell) because it exports variables for every later step. Rerun it after any restart.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - F1.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_f1_export_runtime_settings_from_terraform.
COMMANDS_05 = """: "${PROJECT:?Set the existing project ID}"
: "${GIT_SHA:?Set the pinned source commit}"
: "${PROJECT_NUMBER:?Project lookup failed}"
: "${IMAGE_REPO:?F1 did not complete}"
: "${RESIDENCY:?Restore ~/rag-env.sh}"
: "${DOCAI_PROCESSOR_ID:?Document AI output is missing}"
: "${VECTOR_INDEX_ENDPOINT:?Vector endpoint output is missing}"
: "${VECTOR_DEPLOYED_INDEX_ID:?Deployed index output is missing}"
: "${VECTOR_INDEX_NAME:?Vector index output is missing}"
: "${CHECKPOINT_INSTANCE:?Cloud SQL output is missing}"
: "${SPANNER_INSTANCE:?Spanner instance output is missing}"
: "${SPANNER_DATABASE:?Spanner database output is missing}"
printf 'API: %s\\nVector endpoint: %s\\nVector index: %s\\nCloud SQL: %s\\nBigQuery mirror: %s\\nImage tag: %s\\n' \\
  "$API_URL" "$VECTOR_INDEX_ENDPOINT" "$VECTOR_INDEX_NAME" "$CHECKPOINT_INSTANCE" "$BQ_CHUNK_TABLE" "$GIT_SHA"

"""

def step_05_f1_export_runtime_settings_from_terraform(session):
    """Run F1. Export runtime settings from Terraform state at this checkpoint.

    The runtime settings every deploy reads, from Terraform's outputs. Run only after the full reviewed Terraform plan has been applied. A missing or empty output is a stop condition. This block must run in your main shell (not a subshell) because it exports variables for every later step. Rerun it after any restart.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - F1 guard.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_f2_prepare_cookie_secret_and_the_checkpoin.
COMMANDS_06 = """(
set -euo pipefail
: "${PROJECT:?Run F1 first}"
gcloud secrets describe cookie-secret --project="$PROJECT" --format='value(name)'
enabled="$(gcloud secrets versions list cookie-secret --project="$PROJECT" \\
  --filter='state=enabled' --format='value(name)')"
if [[ -z "$enabled" ]]; then
  echo 'No enabled cookie-secret version; adding one (value not printed).'
  python -c 'import secrets; print(secrets.token_hex(32))' |
    gcloud secrets versions add cookie-secret --project="$PROJECT" --data-file=-
else
  echo "cookie-secret already has an enabled version; reusing it."
fi
gcloud secrets add-iam-policy-binding cookie-secret --project="$PROJECT" \\
  --member="serviceAccount:documind-admin-sa@$PROJECT.iam.gserviceaccount.com" \\
  --role='roles/secretmanager.secretAccessor' --condition=None >/dev/null
dsn="$(gcloud secrets versions list documind-checkpoint-dsn --project="$PROJECT" \\
  --filter='state=enabled' --format='value(name)')"
[[ -n "$dsn" ]] || { echo 'STOP: documind-checkpoint-dsn has no enabled version. Check the Terraform apply (cloudsql.tf); do not create one by hand.' >&2; exit 1; }
echo 'PASS: cookie-secret and checkpoint DSN ready.'
)

"""

def step_06_f2_prepare_cookie_secret_and_the_checkpoin(session):
    """Run F2. Prepare cookie-secret and the checkpoint DSN at this checkpoint.

    The UI's cookie secret and the chat checkpoint DSN. Terraform creates cookie-secret as an empty holder. The UI and admin services mount :latest, so it needs one enabled version. A permission error must be fixed; it is not evidence that no version exists.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - F2.
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
        ('source_28', step_01_restore_the_shell_and_pin_git_sha),
        ('source_29', step_02_restore_the_shell_and_pin_git_sha),
        ('source_30', step_03_restore_the_shell_and_pin_git_sha),
        ('source_31', step_04_f1_export_runtime_settings_from_terraform),
        ('source_32', step_05_f1_export_runtime_settings_from_terraform),
        ('source_33', step_06_f2_prepare_cookie_secret_and_the_checkpoin),
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
