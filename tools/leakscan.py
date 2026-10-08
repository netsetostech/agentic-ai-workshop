"""What must never leave this repository, as one list.

tools/publish_learner.py holds the kit to it before a publish (the learner repo is public), and
pagekit/check_lesson.py holds every page to it (the pages are pasted into a public website).

Built in: key material, tokens, a real DocuMind project id or project number, a personal mailbox, and the
file kinds that belong to the authoring side only. Add your own lane's identifiers without committing
them: PUBLISH_DENY="id-one,id-two" in the environment, or one string per line in .publish-deny at the
repository root (gitignored).
"""
from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATTERNS = [
    ("a private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("a Google API key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("an OAuth access token", re.compile(r"\bya29\.[0-9A-Za-z_\-]{20,}")),
    ("a GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b")),
    ("a service-account key file", re.compile(r'"private_key_id"\s*:')),
    # documind-ai-YOUR-ID is the placeholder; documind-ai-live-NNNN are the kit's sample project names (README)
    ("a real DocuMind project id", re.compile(r"\bdocumind-ai-(?!YOUR-ID\b|live-)[a-z0-9][a-z0-9-]*")),
    ("a project number in a resource path", re.compile(r"\bprojects/\d{6,}/")),
    ("a project number in a Cloud Run URL", re.compile(r"-\d{9,}\.[a-z0-9-]+\.run\.app")),
    ("a personal mailbox", re.compile(r"[A-Za-z0-9._%+-]+@(?:gmail|googlemail|yahoo|hotmail|outlook|live|icloud|proton|protonmail|rediffmail)\.[a-z.]+", re.I)),
]

# file kinds that never belong in the learner repo
REFUSED_NAMES = ["*_WIX.html", "*.ipynb", ".env", ".env.*", "*.tfstate", "*.tfstate.*", "*.pem", "*.key",
                 "credentials.json", "service-account*.json", "*-sa-key*.json", "*-credentials*.json", ".publish-deny"]
ALLOWED_NAMES = [".env.example"]


def deny_strings() -> list[str]:
    out = [s.strip() for s in os.environ.get("PUBLISH_DENY", "").split(",") if s.strip()]
    f = ROOT / ".publish-deny"
    if f.exists():
        out += [line.strip() for line in f.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    return out


def scan_text(text: str, deny: list[str] | None = None) -> list[tuple[str, str]]:
    """(what, the matched text) for every finding in one text."""
    found = []
    for what, rx in PATTERNS:
        for m in rx.finditer(text):
            found.append((what, m.group(0)[:80]))
    for s in deny if deny is not None else deny_strings():
        if s in text:
            found.append(("a denied string", s[:3] + "..."))    # never echo the denied value itself
    return found


def refused_name(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    if any(fnmatch.fnmatch(name, p) for p in ALLOWED_NAMES):
        return False
    return any(fnmatch.fnmatch(name, p) for p in REFUSED_NAMES)
