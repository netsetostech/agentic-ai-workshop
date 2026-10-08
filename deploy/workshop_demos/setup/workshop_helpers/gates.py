"""Observe deliberate evaluation failures without hiding unrelated command errors."""
import json
import os
from pathlib import Path


def expect_failure(session, args, *, status, messages):
    """Require both the expected exit code and the intended diagnostic in its log.
    
    Example: expect_failure(session, args, status=2, messages=["expected diagnostic"])
    """
    before = set(session.attempt.glob("command_*.log"))
    actual = session.command(args, check=False)
    logs = set(session.attempt.glob("command_*.log")) - before
    output = "\n".join(p.read_text(encoding="utf-8") for p in logs)
    if actual != status or not all(message in output for message in messages):
        raise RuntimeError(f"Expected exit {status} and diagnostics {messages!r}; got exit {actual}. Inspect the command log; this is not the intended red-gate proof.")
    print("Expected gate failure observed:", status, "|", "; ".join(messages))


def expect_guard(session, args, *, stop):
    """Run a command whose guard is meant to stop it on this lab; the stop and its message are the observation.
    
    Make exits 2 when a recipe fails. Exit 2 with the guard's own message is what the
    page shows; exit 0 means the guard let the command through, because this lab is
    not the kind it stops. Any other exit, or a 2 without the message, is an error.
    
    Example: expect_guard(session, args, stop="STOP") checks the guard text as well as exit 2
    """
    before = set(session.attempt.glob("command_*.log"))
    status = session.command(args, check=False)
    output = "\n".join(p.read_text(encoding="utf-8") for p in set(session.attempt.glob("command_*.log")) - before)
    if status == 2 and stop in output:
        print("The guard stopped the command, as the page shows:", stop)
    elif status == 0:
        print("The guard let the command through: this lab is not the kind it stops.")
    else:
        raise RuntimeError(f"Exit {status} without the guard's message {stop!r}; inspect the command log.")
    return status


def live_gate(session, *, report, source=None, expect_red=False, api=None):
    """Keep a live gate's report and status so later functions can inspect red rows.
    
    Make wraps evaluator nonzero exits as 2. A fresh structured report distinguishes
    quality failure from a failed command/token/import. HTTP/malformed failures
    cannot satisfy the deliberate handbook-revision quality-failure experiment.
    ``api`` sends the gate to another revision (a candidate's URL) instead of the API.
    
    Example: live_gate(session, report="/tmp/gate.json", api=candidate_url) retains a fresh candidate report
    """
    path = Path(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.replace(session.attempt / (path.name + ".previous"))
    args = ["make", "eval-live", f"PROJECT={session.config.project}", f"REGION={session.config.cloud_run_region}", f"REPORT={path}"]
    if source:
        args.append(f"SOURCE={source}")
    if api:
        args.append(f"API={api}")
    status = session.command(args, check=False)
    if status not in {0, 2} or not path.exists():
        raise RuntimeError(f"Gate exited {status} without a valid fresh report; inspect the command log.")
    value = json.loads(path.read_text(encoding="utf-8"))
    rows = value.get("records", [])
    if not rows:
        raise RuntimeError("The gate report has no evaluated rows.")
    print("Gate exit:", status, "| report:", path, "| failed:", value.get("failed"))
    if expect_red:
        if status != 2 or any(r.get("outcome") != "ok" for r in rows) or not any(not r["pass"] for r in rows):
            raise RuntimeError("Expected evaluated answers failing the golden assertions. An HTTP/auth/schema error or a green gate does not prove this experiment.")
        print("Revision-change red gate observed; the next step restores the original bytes.")
