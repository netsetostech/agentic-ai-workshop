"""Run once with the SAME Python interpreter that will run the lesson files."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

INSTALL_LIVE_DEPENDENCIES = True  # False installs only the helpers for offline examples.


def main():
    """Install editable helpers using this interpreter and preserve existing settings.
    
    Example: main()
    """
    setup = Path(__file__).resolve().parent
    local = setup / "config" / "settings.local.json"
    print("Installing for:", sys.executable, flush=True)
    if not local.exists():
        settings = json.loads((setup / "config" / "settings.example.json").read_text())
        command = shutil.which("gcloud")
        if command:
            result = subprocess.run([command, "config", "get-value", "project"],
                                    text=True, capture_output=True, timeout=30)
            project = result.stdout.strip()
            if result.returncode == 0 and project and project != "(unset)":
                settings["project"] = project
        local.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        print("Created:", local)
    else:
        print("Keeping your existing settings:", local)
    target = str(setup) + ("[live]" if INSTALL_LIVE_DEPENDENCIES else "")
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", target], check=True)
    print("Setup installed. Check project and region in settings.local.json.")
    print("Read workshop_demos/README.md, then the chosen lesson's README for its file order.")
    print("Specialized dependencies and separate judge/agent/gateway venvs are described at their lesson checkpoints.")
    print("In every IDE run configuration, keep this interpreter:", sys.executable)


if __name__ == "__main__":
    main()
