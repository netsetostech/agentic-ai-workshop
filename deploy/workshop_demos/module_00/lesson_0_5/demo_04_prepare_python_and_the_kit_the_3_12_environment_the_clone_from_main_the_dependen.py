"""Lesson 0.5: Prepare Python and the kit: the 3.12 environment, the clone from main, the dependencies

Python 3.12 in ~/rag-shell-venv, outside the source tree. The environment lives at $HOME/rag-shell-venv; project files stay in $HOME/deploy_module_rag. Clones main into $DEMO_ROOT the first time and fast-forwards to the latest main afterwards. Once you have built images in Build and deploy, they are tied to the commit saved in GIT_SHA. Pulling newer code afterwards does not change the running services; the pin block in Phase 3 will notice the difference and tell you to either go back to the saved commit or rebuild every image. The operator's Python packages, checked against the kit's pins. Needed for the build gate, ingestion, evaluation and smoke tests. Terraform does not need it. Restores your saved settings in a new terminal. To also pull the latest code, rerun S6.

Run order inside this file:
1. S5. Create the Python 3.12 environment (source window 12)
2. S5. Create the Python 3.12 environment (source window 13)
3. S6. Get all files from the latest main (source window 14)
4. S7. Install Python dependencies (source window 15)
5. Reopening a terminal later (source window 16)

Prerequisites: demo_03_prepare_the_project_and_the_shell_the_project_the_sign_in_the_variables_the_tool.
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


# Original CLI workflow for step_01_s5_create_the_python_3_12_environment.
COMMANDS_01 = """(
  set -eu
  RAG_UV_BIN_DIR="$HOME/rag-tools-bin"
  RAG_VENV_PATH="$HOME/rag-shell-venv"
  mkdir -p "$RAG_UV_BIN_DIR"
  if [ ! -x "$RAG_UV_BIN_DIR/uv" ]; then
    RAG_UV_INSTALLER="$(mktemp /tmp/documind-uv-install.XXXXXXXX)"
    trap 'rm -f "$RAG_UV_INSTALLER"' EXIT
    curl --fail --silent --show-error --location \\
      https://astral.sh/uv/install.sh --output "$RAG_UV_INSTALLER"
    UV_INSTALL_DIR="$RAG_UV_BIN_DIR" UV_NO_MODIFY_PATH=1 \\
      sh "$RAG_UV_INSTALLER"
  fi
  "$RAG_UV_BIN_DIR/uv" python install 3.12
  if [ -e "$RAG_VENV_PATH" ] || [ -L "$RAG_VENV_PATH" ]; then
    if [ ! -f "$RAG_VENV_PATH/bin/activate" ] || [ ! -x "$RAG_VENV_PATH/bin/python3.12" ]; then
      printf '%s\\n' 'STOP: existing environment is incomplete or uses another Python. Inspect it before replacing it.' >&2
      exit 1
    fi
    "$RAG_VENV_PATH/bin/python3.12" - <<'PY'
import os, sys
from pathlib import Path
expected = Path(os.environ["HOME"]) / "rag-shell-venv"
if sys.version_info[:2] != (3, 12) or sys.prefix == sys.base_prefix or Path(sys.prefix).resolve() != expected.resolve():
    raise SystemExit("STOP: existing environment is not the required Python 3.12 venv.")
print("Reusing:", sys.prefix)
PY
    "$RAG_VENV_PATH/bin/python3.12" -m pip --version || {
      printf '%s\\n' 'STOP: existing environment has no working pip.' >&2
      exit 1
    }
  else
    "$RAG_UV_BIN_DIR/uv" venv --python 3.12 --seed "$RAG_VENV_PATH"
  fi
)

"""

def step_01_s5_create_the_python_3_12_environment(session):
    """Run S5. Create the Python 3.12 environment at this checkpoint.

    Python 3.12 in ~/rag-shell-venv, outside the source tree. The environment lives at $HOME/rag-shell-venv; project files stay in $HOME/deploy_module_rag.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Install uv and Python 3.12.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_s5_create_the_python_3_12_environment.
COMMANDS_02 = """source "$HOME/rag-shell-venv/bin/activate" &&
hash -r &&
which python &&
python --version &&
python -m pip --version &&
python - <<'PY'
import os, sys
from pathlib import Path
expected = Path(os.environ["HOME"]) / "rag-shell-venv"
assert sys.version_info[:2] == (3, 12), "STOP: Python must be 3.12."
assert sys.prefix != sys.base_prefix, "STOP: system Python is still selected."
assert Path(sys.prefix).resolve() == expected.resolve(), "STOP: a different environment is selected."
print("PASS: Python 3.12 environment active:", sys.prefix)
PY

"""

def step_02_s5_create_the_python_3_12_environment(session):
    """Run S5. Create the Python 3.12 environment at this checkpoint.

    Python 3.12 in ~/rag-shell-venv, outside the source tree. The environment lives at $HOME/rag-shell-venv; project files stay in $HOME/deploy_module_rag.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Activate and verify.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_s6_get_all_files_from_the_latest_main.
COMMANDS_03 = """# Always the latest main of netsetos/agents_workshop_learner.
export RAG_REPO_URL='https://github.com/netsetos/agents_workshop_learner.git'
export DEMO_ROOT="${DEMO_ROOT:-$HOME/deploy_module_rag}"
(
  set -euo pipefail
  if [ -d "$DEMO_ROOT/.git" ]; then
    case "$(git -C "$DEMO_ROOT" remote get-url origin)" in
      "$RAG_REPO_URL"|https://github.com/netsetos/agents_workshop_learner|git@github.com:netsetos/agents_workshop_learner.git) ;;
      *) echo "STOP: $DEMO_ROOT is a clone of a different repository. Move it aside first." >&2; exit 1 ;;
    esac
    git -C "$DEMO_ROOT" fetch origin main
    git -C "$DEMO_ROOT" checkout main
    git -C "$DEMO_ROOT" merge --ff-only origin/main
  elif [ -e "$DEMO_ROOT" ] && [ -n "$(ls -A "$DEMO_ROOT")" ]; then
    echo "STOP: $DEMO_ROOT already has files but is not a Git clone. Move it aside, then rerun." >&2; exit 1
  else
    git clone --branch main "$RAG_REPO_URL" "$DEMO_ROOT"
  fi
  git -C "$DEMO_ROOT" log -1 --format='PASS: up to date with origin/main (%h, %cr): %s'
  printf 'Commit: %s\\nFiles: %s\\n' "$(git -C "$DEMO_ROOT" rev-parse HEAD)" "$(git -C "$DEMO_ROOT" ls-files | wc -l)"
  if [ -n "${GIT_SHA:-}" ] && [ "$GIT_SHA" != "$(git -C "$DEMO_ROOT" rev-parse HEAD)" ]; then
    echo "NOTE: your images were built from $GIT_SHA, which is not this commit. See the pin block in Phase 3."
  fi
) && cd "$DEMO_ROOT"

"""

def step_03_s6_get_all_files_from_the_latest_main(session):
    """Run S6. Get all files from the latest main at this checkpoint.

    Clones main into $DEMO_ROOT the first time and fast-forwards to the latest main afterwards. Once you have built images in Build and deploy, they are tied to the commit saved in GIT_SHA. Pulling newer code afterwards does not change the running services; the pin block in Phase 3 will notice the difference and tell you to either go back to the saved commit or rebuild every image.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Clone or update.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_s7_install_python_dependencies.
COMMANDS_04 = """: "${PROJECT:?Restore your existing project ID}" "${DEMO_ROOT:?Restore DEMO_ROOT}" &&
export PROJECT DEMO_ROOT &&
source "$HOME/rag-shell-venv/bin/activate" &&
source "$DEMO_ROOT/commands/session-restart.sh" &&
rag_install_python_dependencies &&
(
  set -euo pipefail
  : "${PROJECT:?Restore your existing project ID}" "${DEMO_ROOT:?Restore DEMO_ROOT}"
  cd "$DEMO_ROOT"
  "$HOME/rag-shell-venv/bin/python" - <<'RAG_ENV_RECORD'
import hashlib, importlib.metadata, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
root = Path(os.environ['DEMO_ROOT'])
files = ('shared/requirements.txt', 'services/ingest/requirements.txt',
         'services/rag-api/requirements.txt', 'services/mcp/requirements.txt')
record = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'project_setting': os.environ['PROJECT'],
    'python': sys.executable,
    'python_version': sys.version,
    'requirements_sha256': {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in files},
    'installed_packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions() if d.metadata.get('Name')},
    'scope': 'local package versions, imports and pip check; no cloud readiness claim',
}
out = root / 'operator-evidence/python-dependencies.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(record, indent=2, sort_keys=True) + '\\n')
print('PASS: dependency evidence saved to', out)
RAG_ENV_RECORD
) &&
export GOOGLE_CLOUD_PROJECT="${PROJECT:?Restore PROJECT}" &&
export PYTHONPATH="${DEMO_ROOT:?Restore DEMO_ROOT}"

"""

def step_04_s7_install_python_dependencies(session):
    """Run S7. Install Python dependencies at this checkpoint.

    The operator's Python packages, checked against the kit's pins. Needed for the build gate, ingestion, evaluation and smoke tests. Terraform does not need it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Install.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_reopening_a_terminal_later.
COMMANDS_05 = """source "$HOME/rag-shell-venv/bin/activate" &&
source "$HOME/rag-env.sh" &&
export PROJECT_ID="$PROJECT" GOOGLE_CLOUD_PROJECT="$PROJECT" GOOGLE_CLOUD_QUOTA_PROJECT="$PROJECT" \\
       CLOUDSDK_CORE_PROJECT="$PROJECT" CLOUDSDK_BILLING_QUOTA_PROJECT="$PROJECT" \\
       DEPLOY_ROOT="$DEMO_ROOT" PYTHONPATH="$DEMO_ROOT" &&
gcloud config set project "$PROJECT" &&
source "$DEMO_ROOT/commands/session-restart.sh" &&
rag_require_terraform &&
cd "$DEMO_ROOT" &&
echo "GIT_SHA=[${GIT_SHA:-not pinned yet}]"

"""

def step_05_reopening_a_terminal_later(session):
    """Run Reopening a terminal later at this checkpoint.

    Restores your saved settings in a new terminal. To also pull the latest code, rerun S6.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - a new terminal: restore your settings.
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
        ('source_12', step_01_s5_create_the_python_3_12_environment),
        ('source_13', step_02_s5_create_the_python_3_12_environment),
        ('source_14', step_03_s6_get_all_files_from_the_latest_main),
        ('source_15', step_04_s7_install_python_dependencies),
        ('source_16', step_05_reopening_a_terminal_later),
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
