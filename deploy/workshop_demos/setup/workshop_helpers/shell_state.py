"""Capture only named, non-credential exports after a lesson command workflow.

The parent stores the result in its private ignored evidence directory. This
module is an internal subprocess entry point, not a lesson for learners to run.
"""
import json
import os
from pathlib import Path
import sys
from .session import secret_name


def main():
    """Write filtered environment data without exposing it on stdout.
    
    Example: main()
    """
    target = Path(sys.argv[1])
    values = {key: value for key, value in os.environ.items() if not secret_name(key)
              and re_allowed(key)}
    target.write_text(json.dumps(values), encoding="utf-8")
    target.chmod(0o600)


def re_allowed(name):
    """Limit capture to the reviewed names passed in this lesson's map.
    
    Example: re_allowed(key)
    """
    return name in json.loads(os.environ.get("WORKSHOP_PERSIST_VARIABLES", "[]"))


if __name__ == "__main__":
    main()
