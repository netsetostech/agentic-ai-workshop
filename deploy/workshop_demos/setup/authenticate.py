"""Explicit, interactive ADC login. Never run automatically from a lesson."""
import json
from pathlib import Path
import shutil
import subprocess


def main():
    """Run interactive ADC login for this workstation and preserve gcloud account selection.
    
    Example: main()
    """
    executable = shutil.which("gcloud")
    if not executable:
        raise RuntimeError("gcloud is not on the IDE's PATH.")
    local = Path(__file__).resolve().parent / "config" / "settings.local.json"
    settings = json.loads(local.read_text()) if local.exists() else {}
    command = [executable, "auth", "application-default", "login", "--no-launch-browser"]
    if settings.get("project"):
        command.append("--project=" + settings["project"])
    print("Follow the browser sign-in instructions; paste its code into this Run console.", flush=True)
    subprocess.run(command, check=True)
    print("ADC refreshed. Run check_setup.py next.")


if __name__ == "__main__":
    main()
