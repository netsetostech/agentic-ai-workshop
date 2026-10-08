"""The responsive audit over every authored page: fail on any FAIL gate except the known exceptions below.

    python pagekit/audit_pages.py            # every lesson with a page
    python pagekit/audit_pages.py 5.1 4.4    # some

The gates are audit_responsive.py's (the phone widths, the embed with no scrollport, touch sizes, the srcdoc
documents). A WARN is printed, never fatal. An exception is listed here with its reason, so it is a decision
someone can read and reverse, not a silenced gate.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pagekit.pagebuild import MANIFEST, page_path  # noqa: E402

KNOWN = {
    "R39": "code-window labels read 'bash &mdash; run in the operator shell'; the em dash is the pages' house style for labels",
}


def authored() -> list:
    return [lid for m in MANIFEST["modules"].values() for lid, les in m["lessons"].items()
            if les.get("slug") and les.get("topic_filename") and page_path(lid).exists()]


def main(argv: list) -> int:
    lids = argv or authored()
    bad = 0
    for lid in lids:
        page = page_path(lid)
        r = subprocess.run([sys.executable, str(ROOT / "pagekit" / "audit_responsive.py"), "--json", str(page)],
                           capture_output=True, text=True, encoding="utf-8")
        try:
            results = next(iter(json.loads(r.stdout).values()))
        except (ValueError, StopIteration):
            print(f"{lid}: the auditor gave no JSON")
            print(r.stderr[-400:])
            bad += 1
            continue
        fails = [x for x in results if x["severity"] == "FAIL"]
        warns = [x for x in results if x["severity"] == "WARN"]
        real = [x for x in fails if x["gate"] not in KNOWN]
        known = sorted({x["gate"] for x in fails if x["gate"] in KNOWN})
        passes = sum(1 for x in results if x["severity"] == "PASS")
        status = "FAIL" if real else "ok"
        extra = f", known: {', '.join(known)}" if known else ""
        print(f"{lid}: {status}  {passes} pass, {len(warns)} warn{extra}")
        for x in real + warns:
            print(f"   [{x['severity']}] {x['gate']} ({x['doc']}) line {x.get('line')}: {x['message']}")
        bad += bool(real)
    for gate, why in KNOWN.items():
        print(f"known exception {gate}: {why}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
