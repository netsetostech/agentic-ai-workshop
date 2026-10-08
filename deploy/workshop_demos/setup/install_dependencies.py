"""Install an explicit workstation dependency profile in the IDE interpreter.

Run once if the existing rag-shell-venv lacks the kit's operator packages. The
operator profile uses the committed API/ingest requirements rather than another
copy of their pins. The local-chat profile is separate because its Chroma/Ollama
dependencies are not required to inspect an already deployed cloud lane.
"""
from pathlib import Path
import subprocess
import sys

PROFILE = "operator"  # "operator" or "local-chat"; specialized frameworks keep their lesson venvs.


def main():
    """Install the chosen committed requirements; fail on pip's actual exit status.
    
    Example: main()
    """
    root = Path(__file__).resolve().parents[2]
    profiles = {
        "operator": ["services/rag-api/requirements.txt", "services/ingest/requirements.txt"],
        "local-chat": ["services/chat/requirements.txt", "services/chat/requirements-local.txt"],
    }
    if PROFILE not in profiles:
        raise ValueError(f"Choose one of {list(profiles)}")
    command = [sys.executable, "-m", "pip", "install"]
    for relative in profiles[PROFILE]:
        command.extend(["-r", str(root / relative)])
    if PROFILE == "operator":
        command.extend(["rank-bm25==0.2.2", "pandas"])
    print("Profile:", PROFILE, "| Python:", sys.executable, flush=True)
    subprocess.run(command, cwd=root, check=True)
    print("Dependencies installed. Return to the lesson README's first checkpoint.")


if __name__ == "__main__":
    main()
