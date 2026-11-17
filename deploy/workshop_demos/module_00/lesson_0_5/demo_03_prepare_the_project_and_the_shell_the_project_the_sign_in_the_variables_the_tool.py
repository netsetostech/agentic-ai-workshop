"""Lesson 0.5: Prepare the project and the shell: the project, the sign-in, the variables, the tools

The account every later command runs as. One set of variables, checked, then saved for new terminals. Change PROJECT to your project ID. The block stops at the first failed check. Ends with PASS: project <id> (<number>) is active, billed, operator <email>. Write the helper that saves your settings for new terminals, then save. It now also keeps GIT_SHA, the source snapshot your images are built from (pinned in Phase 3). Terraform 1.9 or newer, git, jq, make and file. Terraform v1.9.0 or newer and no MISSING lines: skip to S5. Otherwise run the matching install below. Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository: Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository: The fingerprint identifies HashiCorp's package-signing key. Do not continue if the download or conversion failed. The last command prints Terraform v1.9.0 or newer. Only if terraform still isn't found, or an older binary shadows it: Packages installed outside your home directory may need reinstalling after a Cloud Shell VM reset. Never loosen required_version or provider constraints, and never use insecure TLS or unsigned-package flags. Install git, jq, make or file (only if one is missing):

Run order inside this file:
1. S2. Sign in the gcloud CLI (source window 2)
2. S3. Set the project and session variables (source window 3)
3. S3. Set the project and session variables (source window 4)
4. S4. Check Terraform and command-line tools (source window 5)
5. S4. Check Terraform and command-line tools (source window 6)
6. S4. Check Terraform and command-line tools (source window 7)
7. S4. Check Terraform and command-line tools (source window 8)
8. S4. Check Terraform and command-line tools (source window 9)
9. S4. Check Terraform and command-line tools (source window 10)
10. S4. Check Terraform and command-line tools (source window 11)

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


# Original CLI workflow for step_01_s2_sign_in_the_gcloud_cli.
COMMANDS_01 = """gcloud auth list --filter=status:ACTIVE --format='value(account)'

"""

def step_01_s2_sign_in_the_gcloud_cli(session):
    """Run S2. Sign in the gcloud CLI at this checkpoint.

    The account every later command runs as.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Check sign-in.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_s3_set_the_project_and_session_variables.
COMMANDS_02 = """# Deployment project; change only when starting a separate deployment.
export PROJECT='documind-ai-YOUR-ID'
export REGION='asia-south1'
export RESIDENCY='india'
export GOOGLE_CLOUD_PROJECT="$PROJECT"
export PROJECT_ID="$PROJECT"
export TF_VAR_project_id="$PROJECT"
export GOOGLE_CLOUD_QUOTA_PROJECT="$PROJECT"
export CLOUDSDK_CORE_PROJECT="$PROJECT"
export CLOUDSDK_BILLING_QUOTA_PROJECT="$PROJECT"
export DEMO_ROOT="$HOME/deploy_module_rag"
export DEPLOY_ROOT="$DEMO_ROOT"
export PYTHONPATH="$DEMO_ROOT"
export TFSTATE_BUCKET="${PROJECT}-tfstate"
export TFSTATE_PREFIX="documind/${PROJECT}"
export BUILD_SOURCE_BUCKET="${PROJECT}-rag-build-source"
gcloud config set project "$PROJECT" &&
gcloud config set billing/quota_project "$PROJECT" &&
gcloud projects describe "$PROJECT" --format='yaml(projectId,projectNumber,lifecycleState)' &&
test "$(gcloud projects describe "$PROJECT" --format='value(lifecycleState)')" = 'ACTIVE' &&
OPERATOR_EMAIL="$(gcloud config get-value account 2>/dev/null)" &&
[[ -n "$OPERATOR_EMAIL" ]] &&
export OPERATOR_EMAIL &&
gcloud services enable cloudbilling.googleapis.com cloudresourcemanager.googleapis.com --project="$PROJECT" &&
gcloud billing projects describe "$PROJECT" --format='yaml(projectId,billingEnabled,billingAccountName)' &&
test "$(gcloud billing projects describe "$PROJECT" --format='value(billingEnabled)')" = 'True' &&
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')" &&
export PROJECT_NUMBER &&
echo "PASS: project $PROJECT ($PROJECT_NUMBER) is active, billed, operator $OPERATOR_EMAIL"

"""

def step_02_s3_set_the_project_and_session_variables(session):
    """Run S3. Set the project and session variables at this checkpoint.

    One set of variables, checked, then saved for new terminals. Change PROJECT to your project ID. The block stops at the first failed check.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Project and variables.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_s3_set_the_project_and_session_variables.
COMMANDS_03 = """# Writes ~/rag-save-env.sh, which saves your settings for new terminals.
cat > "$HOME/rag-save-env.sh" <<'RAG_SAVE'
(
  umask 077
  for v in PROJECT REGION RESIDENCY OPERATOR_EMAIL PROJECT_NUMBER DEMO_ROOT \\
           TFSTATE_BUCKET TFSTATE_PREFIX BUILD_SOURCE_BUCKET BILLING_ACCOUNT_ID BILLING_ACCOUNT_NAME \\
           GIT_SHA ADMIN_EMAILS \\
           $(compgen -v TF_VAR_); do
    if [ -n "${!v+x}" ]; then printf 'export %s=%q\\n' "$v" "${!v}"; fi
  done > "$HOME/rag-env.sh"
  echo "PASS: settings saved to $HOME/rag-env.sh"
)
RAG_SAVE
if [[ -n "${PROJECT_NUMBER:-}" && -n "${OPERATOR_EMAIL:-}" ]]; then
  source "$HOME/rag-save-env.sh"
else
  echo 'STOP: the project block above did not pass; fix it before saving.' >&2
fi

"""

def step_03_s3_set_the_project_and_session_variables(session):
    """Run S3. Set the project and session variables at this checkpoint.

    Ends with PASS: project <id> (<number>) is active, billed, operator <email>. Write the helper that saves your settings for new terminals, then save. It now also keeps GIT_SHA, the source snapshot your images are built from (pinned in Phase 3).

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Save settings.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_s4_check_terraform_and_command_line_tools.
COMMANDS_04 = """if command -v terraform >/dev/null; then terraform version | sed -n 1p; else echo "MISSING: terraform"; fi
for t in git jq file make; do command -v "$t" >/dev/null || echo "MISSING: $t"; done

"""

def step_04_s4_check_terraform_and_command_line_tools(session):
    """Run S4. Check Terraform and command-line tools at this checkpoint.

    Terraform 1.9 or newer, git, jq, make and file.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Check tools.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_s4_check_terraform_and_command_line_tools.
COMMANDS_05 = """sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

"""

def step_05_s4_check_terraform_and_command_line_tools(session):
    """Run S4. Check Terraform and command-line tools at this checkpoint.

    Terraform v1.9.0 or newer and no MISSING lines: skip to S5. Otherwise run the matching install below. Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Prerequisites.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_s4_check_terraform_and_command_line_tools.
COMMANDS_06 = """(
  set -euo pipefail
  curl --fail --silent --show-error --location https://apt.releases.hashicorp.com/gpg \\
    | gpg --dearmor \\
    | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null
)
gpg --no-default-keyring --keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg --fingerprint

"""

def step_06_s4_check_terraform_and_command_line_tools(session):
    """Run S4. Check Terraform and command-line tools at this checkpoint.

    Terraform v1.9.0 or newer and no MISSING lines: skip to S5. Otherwise run the matching install below. Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Signing key.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

# Original CLI workflow for step_07_s4_check_terraform_and_command_line_tools.
COMMANDS_07 = """export RAG_APT_CODENAME="$(. /etc/os-release; printf '%s' "${UBUNTU_CODENAME:-$VERSION_CODENAME}")"
printf 'deb [arch=%s signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com %s main\\n' "$(dpkg --print-architecture)" "$RAG_APT_CODENAME" | sudo tee /etc/apt/sources.list.d/hashicorp.list

"""

def step_07_s4_check_terraform_and_command_line_tools(session):
    """Run S4. Check Terraform and command-line tools at this checkpoint.

    Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository: The fingerprint identifies HashiCorp's package-signing key. Do not continue if the download or conversion failed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Repository.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_07)

# Original CLI workflow for step_08_s4_check_terraform_and_command_line_tools.
COMMANDS_08 = """(
  set -euo pipefail
  sudo apt-get update
  sudo apt-get install -y terraform
  /usr/bin/terraform version
  # Keep the verified package binary in the persistent home directory too.
  mkdir -p "$HOME/.local/bin"
  install -m 0755 /usr/bin/terraform "$HOME/.local/bin/terraform"
  "$HOME/.local/bin/terraform" version
)

"""

def step_08_s4_check_terraform_and_command_line_tools(session):
    """Run S4. Check Terraform and command-line tools at this checkpoint.

    Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository: The fingerprint identifies HashiCorp's package-signing key. Do not continue if the download or conversion failed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Install Terraform.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_08)

# Original CLI workflow for step_09_s4_check_terraform_and_command_line_tools.
COMMANDS_09 = """# Append lookup locations so the active Python environment keeps precedence.
export PATH="$PATH:$HOME/.local/bin:/usr/local/bin:/usr/bin"
hash -r
type -a terraform
terraform version

"""

def step_09_s4_check_terraform_and_command_line_tools(session):
    """Run S4. Check Terraform and command-line tools at this checkpoint.

    The last command prints Terraform v1.9.0 or newer. Only if terraform still isn't found, or an older binary shadows it:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Fix PATH.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_09)

# Original CLI workflow for step_10_s4_check_terraform_and_command_line_tools.
COMMANDS_10 = """if ! command -v jq >/dev/null || ! command -v file >/dev/null || ! command -v git >/dev/null || ! command -v make >/dev/null; then
  sudo apt-get update
  sudo apt-get install -y jq file git make
fi
jq --version
git --version
command -v file sha256sum cmp mktemp make

"""

def step_10_s4_check_terraform_and_command_line_tools(session):
    """Run S4. Check Terraform and command-line tools at this checkpoint.

    Packages installed outside your home directory may need reinstalling after a Cloud Shell VM reset. Never loosen required_version or provider constraints, and never use insecure TLS or unsigned-package flags. Install git, jq, make or file (only if one is missing):

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Install utilities.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_10)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_2', step_01_s2_sign_in_the_gcloud_cli),
        ('source_3', step_02_s3_set_the_project_and_session_variables),
        ('source_4', step_03_s3_set_the_project_and_session_variables),
        ('source_5', step_04_s4_check_terraform_and_command_line_tools),
        ('source_6', step_05_s4_check_terraform_and_command_line_tools),
        ('source_7', step_06_s4_check_terraform_and_command_line_tools),
        ('source_8', step_07_s4_check_terraform_and_command_line_tools),
        ('source_9', step_08_s4_check_terraform_and_command_line_tools),
        ('source_10', step_09_s4_check_terraform_and_command_line_tools),
        ('source_11', step_10_s4_check_terraform_and_command_line_tools),
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
