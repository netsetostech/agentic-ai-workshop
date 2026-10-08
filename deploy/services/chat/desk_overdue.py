#!/usr/bin/env python3
"""The case queue's hourly overdue scan (workshop lesson 5.6): the entry point of the documind-cases-overdue job.

    python desk_overdue.py --project documind-ai-YOUR-ID          # the job, on the chat image as chat-sa (terraform/desk.tf)
    make cases-overdue PROJECT=documind-ai-YOUR-ID                # the same code from deploy/, as you

Every tenant's case that is within 24 hours of its due_at and still unacknowledged (status open), and every breached
case (due_at past, still open, acknowledged or in progress), is one log line:

    {"event": "case_overdue", "case_id": "...", "queue": "grc", "due_at": "...", "state": "due" | "breached"}

The id, the queue and due_at, and nothing else: no type, no person, no summary, so the line can sit in Cloud Logging
for as long as the lane keeps logs. A posh, grievance or privacy_request case's queue is logged as "sensitive", since
ic:<unit> or privacy would say what it is about; make cases shows the operator its queue. A log-based alert on the
event is what tells a queue. It reads and writes no case.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1] if HERE.parent.name == "services" else HERE   # deploy/ from the shell; /app in the image
for p in (str(HERE), str(KIT)):                                       # (shared/ beside it there)
    if p not in sys.path:
        sys.path.insert(0, p)

from shared import cases  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)   # bare JSON -> jsonPayload
log = logging.getLogger("documind.chat.overdue")


def scan(db, now=None) -> list[dict]:
    """One line per due or breached case; returns them."""
    rows = cases.overdue(db, now)
    for r in rows:
        log.info(json.dumps({"event": "case_overdue", "case_id": r["case_id"], "queue": r["queue"],
                             "due_at": r["due_at"], "state": r["state"]}))
    log.info(json.dumps({"event": "case_overdue_scan", "due": sum(r["state"] == "due" for r in rows),
                         "breached": sum(r["state"] == "breached" for r in rows)}))
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT") or "")
    a = ap.parse_args(argv)
    if not a.project:
        ap.error("--project is required (or GOOGLE_CLOUD_PROJECT)")
    from google.cloud import firestore
    scan(firestore.Client(project=a.project))
    return 0


if __name__ == "__main__":
    sys.exit(main())
