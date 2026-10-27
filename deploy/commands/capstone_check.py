#!/usr/bin/env python3
"""The capstone's eight components checked, and the lane's handover written (the v5 course's Module 11, lesson 11.8).

    python commands/capstone_check.py check [--fork <dir>]                         make capstone-check [FORK=<dir>]
    python commands/capstone_check.py check --project <id> --region <region>       make capstone-check PROJECT=<id>
    python commands/capstone_check.py handover [--project <id> --region <region>]  make handover [PROJECT=<id>]
    python commands/capstone_check.py --selftest

check prints, for each of the capstone rubric's eight components, PASS or FAIL with the evidence or with what is
missing: whether the component exists in the fork and a stranger can verify it, never how good it is. It scores
nothing. The five dimensions are the defence's, scored by two assessors, and a component that fails makes an incomplete
submission, for which the defence does not run. The fork is a directory (--fork; by default the kit this file is in,
and make passes FORK, . unless given). Offline, the default, check reads the fork's files at Rs 0 with no credential:
the four documents, the corpus and golden rows, and the records make leaves in evals/reports/ (gitignored, so the
checkout that ran make holds them); and it runs the fork's own evals/run_eval.py offline, as make eval runs it. With
--project it also reads the lane and changes nothing: gcloud's describe and list calls (gcloud_json() refuses any other
command), ID tokens minted as make eval-live mints them, and GETs on documind-api, none of which calls a model. The
records it reads are then that lane's only. The four documents have templates in capstone/templates/, which a missing
document's line names; copied as it ships, a template still fails its component until its {{...}} placeholders are
replaced.

  1  A live URL behind IAP. commands/lesson-12.4.sh deploys documind-ui with --iap and --no-allow-unauthenticated; the
     last make smoke-deployed run (lesson 11.3) recorded GET /version answering a member; the newest live eval report
     that asked the isolation rows (make gate's, lesson 11.2, or make eval-live REPORT='s) has every one refused to
     the outsider with a 403. The lane: GET /version as documind-ui-sa answers 200, GET /v1/sources as
     documind-outsider-sa, who is on no roster, answers 403, and documind-ui has IAP on.
  2  Your own corpus, 30 pages or more, ingested. A tenant of your own under evals/corpus/, not one of the kit's three:
     its documents as make ingest-corpus uploads them (evals/upload.sh leaves a .md beside its .pdf at home), with
     their pages counted as the ingest worker counts them (a PDF's page tree, or its mirror's pages: line; a text
     file's form feeds plus one; a picture or a recording, one), 30 or more; and the newest live eval report that
     asked that tenant has a row of it passed citing one of them. The lane: GET /v1/sources, the Documents page's
     read, lists each of them indexed.
  3  An eval suite, 30 golden rows or more, with tenant isolation. evals/golden.jsonl holds 30 rows or more, 5 or more
     of them isolation rows, and the fork's evals/run_eval.py exits 0 offline (make eval). Nothing on the lane.
  4  One lane on top of the core. The last make smoke-deployed run passed a lane's smoke: smoke-chat (chat),
     smoke-media (media), smoke-slm (SLM), or the API's smoke while /version said retrieval_graph on or auto (graph).
     The lane: that lane's services are deployed now.
  5  ARCHITECTURE.md, with the alternatives you rejected. A section whose heading says rejected or alternatives names
     three or more, each a list item, a table row or a sub-heading, with its reason: six words or more.
  6  COST-MODEL.md at 1k, 10k and 100k queries a month. It names the three volumes, gives three or more amounts in
     rupees and three or more in dollars, carries a date, and states the rate: 85 rupees to the dollar (USD_INR = 85).
  7  FAILURE-MODES.md, four entries, each proved by a script. Four headed sections or more, each with a Symptom: line
     and a command in backticks the fork can run: a make target its Makefile or mk/*.mk defines, or a script it holds
     (python, bash, sh or ./, then the path). Of lesson 11.7's registry, make gotcha-drill with an ID= that
     ops/gotchas.json gives an offline drill (a live one with LIVE=) reproduces a gotcha; make gotchas and make
     gotcha-detect show and detect one, and prove nothing. The commands are resolved, never run.
  8  RUNBOOK.md and one recorded rollback. RUNBOOK.md says how to roll back (make rollback, or update-traffic), and two
     successive make smoke-deployed runs of one lane show a rollback with /version answered before and after: the
     traffic left the revision the candidate tag still names, or went back to an older revision. The lane: both are
     documind-api's revisions.

handover writes HANDOVER.md into the fork (--out for elsewhere), whole: the alert policies, the night job, the floors,
the revisions, the CI trust, the budget and the state bucket, each as this checkout states it and, with --project, as
the lane shows it. On the lane it only reads: gcloud_json()'s READS, as check's (the scheduler job, the workload
identity provider, the project's billing account and its budgets, the state bucket and its object among them), and
the Monitoring API's alert policies (a GET, with gcloud's access token). A lane read that fails is listed under Not
read, and the rest is written.

--selftest runs the rules on hand-made documents, records and PDFs, with no fork and no lane.

Exit codes: check: 0 every component PASS, 1 a component FAILs; handover: 0 written, 1 written with a lane read that
failed; both: 2 stopped, and the message says why.
"""
from __future__ import annotations

import argparse
import functools
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent                                   # the kit: deploy/ here, the repository root in the learner repo


def _sibling(name: str):
    """A command beside this one, loaded by its path, as release.py loads infrastructure.py."""
    spec = importlib.util.spec_from_file_location(f"capstone_{name}", HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# release.py owns the lane's names and the records make leaves (the gate's two accounts, the smoke log's format, how a
# /version answer reads) and its one way to run gcloud; remediate.py owns the alert policies as the Terraform declares
# them, joined to ops/runbooks.json. This reads the same records by the same rules rather than a second copy of them.
release = _sibling("release")
remediate = _sibling("remediate")


class Stop(RuntimeError):
    """A precondition or a read failed. The message says which, and the command exits 2."""


STOPS = (Stop, release.Stop, release.infra.Stop, remediate.Stop)
INCOMPLETE, STOPPED = 1, 2

# The rubric's eight components, in its order and with its numbers.
COMPONENTS = {1: "A live URL behind IAP",
              2: "Your own corpus, 30 pages or more, ingested",
              3: "An eval suite, 30 golden rows or more, with tenant isolation",
              4: "One lane on top of the core: chat, media, SLM or graph",
              5: "ARCHITECTURE.md, with the alternatives you rejected",
              6: "COST-MODEL.md at 1k, 10k and 100k queries a month",
              7: "FAILURE-MODES.md, four entries, each proved by a script",
              8: "RUNBOOK.md and one recorded rollback"}
GOLDEN_MIN, ISOLATION_MIN, PAGES_MIN = 30, 5, 30    # components 2 and 3, as the rubric states them
REJECTED_MIN, ENTRIES_MIN, USD_INR = 3, 4, 85       # components 5, 7 and 6
REASON_WORDS = 6                                    # fewer, and a rejected option is named, not argued
AMOUNTS_MIN = 3                                     # a rupee and a dollar figure for each of the three volumes
KIT_TENANTS = ("acme", "globex", "zeta")            # the kit's own corpus (commands/lane.py's GOLDEN_TENANTS), not yours

UI_SCRIPT = "commands/lesson-12.4.sh"               # make deploy-services deploys documind-ui from it
IAP_FLAGS = ("--iap", "--no-allow-unauthenticated")
REPORTS = "evals/reports"                           # make gate's and make eval-live REPORT='s reports, the smoke log
SMOKE_LOG = f"{REPORTS}/smoke-deployed.jsonl"
REGISTRY = "ops/gotchas.json"
LANES = (("chat", "smoke-chat"), ("media", "smoke-media"), ("SLM", "smoke-slm"))  # graph is the API's smoke, below
GRAPH_ON = ("on", "auto")                           # /version's retrieval_graph when the graph answers (off | on | auto)
ONE_PAGE = (".png", ".jpg", ".jpeg", ".mp4", ".mp3")  # the worker's media: a page each (ingest main.py, MEDIA_TYPES)
GOTCHA_TARGETS = ("gotcha-drill", "gotcha-detect", "gotchas")
TEMPLATES = "capstone/templates"                    # the four documents' templates (13 October 2026)


def plural(n: int, one: str, many: str = "") -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def pct(value) -> str:
    return f"{value:.0%}" if isinstance(value, (int, float)) else "?"


# ---------------------------------------------------------------- the rules, each on text or records alone

def shell_command(text: str, start: str) -> str:
    """The command of a shell script that begins with start, its continuation lines joined; '' when there is none."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(start):
            parts = [line.strip()]
            while parts[-1].endswith("\\") and i + 1 < len(lines):
                parts[-1] = parts[-1][:-1]
                i += 1
                parts.append(lines[i].strip())
            return " ".join(parts)
    return ""


def answered(version) -> bool:
    """Whether a recorded GET /version answered (release.py records {"error": ...} when it could not)."""
    return isinstance(version, dict) and bool(version) and "error" not in version


def text_pages(text: str) -> int:
    """A text upload's pages as the ingest worker counts them (main.py's _parse): its form feeds plus one."""
    return max(1, text.count("\f") + 1)


def declared_pages(text: str) -> int | None:
    """The pages: line of a mirror's provenance header (evals/fetch_real.py writes it beside each real PDF)."""
    head = re.match(r"\s*<!--(.*?)-->", text, re.S)
    found = re.search(r"^pages:\s*(\d+)\s*$", head.group(1), re.M) if head else None
    return int(found.group(1)) if found else None


def _dictionary(data: bytes, at: int) -> bytes:
    """The PDF dictionary (<< ... >>) that holds the byte at `at`, nested dictionaries counted; b'' when unbalanced."""
    depth, i = 0, at
    while i > 0:
        i -= 1
        if data[i:i + 2] == b">>":
            depth += 1
        elif data[i:i + 2] == b"<<":
            if depth == 0:
                break
            depth -= 1
    start, depth, j = i, 0, i
    while j < len(data) - 1:
        if data[j:j + 2] == b"<<":
            depth, j = depth + 1, j + 2
        elif data[j:j + 2] == b">>":
            depth, j = depth - 1, j + 2
            if depth == 0:
                return data[start:j]
        else:
            j += 1
    return b""


def pdf_pages(data: bytes) -> int | None:
    """A PDF's page count off its page tree, with the standard library, as the worker reads it with pypdf: the largest
    /Count of a /Type /Pages dictionary (the root's), in the file or in its Flate streams (PDF 1.5 packs objects into
    them); failing that, its /Type /Page leaves counted. None when it has neither."""
    texts = [data]
    for stream in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        try:
            texts.append(zlib.decompressobj().decompress(stream.group(1)))
        except zlib.error:
            continue
    counts, leaves = [], 0
    for text in texts:
        for tree in re.finditer(rb"/Type\s*/Pages\b", text):
            found = re.search(rb"/Count\s+(\d+)", _dictionary(text, tree.start()))
            if found:
                counts.append(int(found.group(1)))
        leaves += len(re.findall(rb"/Type\s*/Page(?![A-Za-z])", text))
    return max(counts) if counts else (leaves or None)


def pages_of(path: Path) -> int | None:
    """A document's pages as the ingest worker counts them; None where that cannot be told offline (a .docx is
    Document AI's to count)."""
    suffix = path.suffix.lower()
    if suffix in (".md", ".txt"):
        return text_pages(path.read_text(encoding="utf-8", errors="replace"))
    if suffix == ".pdf":
        mirror = path.with_suffix(".md")
        declared = declared_pages(mirror.read_text(encoding="utf-8", errors="replace")) if mirror.is_file() else None
        return declared or pdf_pages(path.read_bytes())
    return 1 if suffix in ONE_PAGE else None


def documents(folder: Path) -> list[tuple[str, int | None]]:
    """A tenant folder's documents as make ingest-corpus uploads them (evals/upload.sh: a .md beside its .pdf or .mp4
    twin stays home, a .segments.json is no document), each with its pages."""
    out = []
    for path in sorted(folder.iterdir()):
        name = path.name.lower()
        if not path.is_file() or name.endswith(".segments.json"):
            continue
        if name.endswith(".md") and (path.with_suffix(".pdf").is_file() or path.with_suffix(".mp4").is_file()):
            continue
        out.append((path.name, pages_of(path)))
    return out


def stem(name: str) -> str:
    return name.rsplit("/", 1)[-1].rsplit(".", 1)[0]


def is_report(data) -> bool:
    """Whether a JSON file is a live eval report: what evals/run_eval.py --report writes."""
    return isinstance(data, dict) and all(k in data for k in ("rows", "scores", "thresholds", "failed", "judged"))


def isolation_asked(report: dict) -> int:
    """How many isolation rows a live eval report asked the outsider, 0 when its run judged none (a scoped run)."""
    if "isolation_403_rate" not in (report.get("judged") or []):
        return 0
    return sum(1 for r in report.get("records") or [] if isinstance(r, dict) and r.get("shape") == "isolation")


def outsider_refused(report: dict) -> bool:
    """Every isolation row refused to the outsider with a 403 (run_eval.py's check_isolation: a rate of 100%)."""
    return bool(isolation_asked(report)) and (report.get("scores") or {}).get("isolation_403_rate") == 1 \
        and not report.get("isolation")


def cited(records: list, tenant: str, stems: set) -> str:
    """The first row of the tenant's that passed citing one of its documents, as '<row> cited <file>'; ''."""
    for r in records:
        if not isinstance(r, dict) or r.get("tenant") != tenant or r.get("pass") is not True:
            continue
        for c in r.get("cites") or []:
            uri = str((c or {}).get("source_uri") or "") if isinstance(c, dict) else ""
            obj = uri.split("/", 3)[-1] if uri.startswith("gs://") else uri
            if obj.split("/", 1)[0] == tenant and stem(obj) in stems:
                return f"{r.get('id')} cited {obj.rsplit('/', 1)[-1]}"
    return ""


def revision_number(name) -> int | None:
    """Cloud Run's number for a revision it named itself (documind-api-00042-typ: 42): a service's revisions in order."""
    m = re.fullmatch(r"documind-api-(\d{5})-[a-z0-9]{3}", str(name or ""))
    return int(m.group(1)) if m else None


def rollback(runs: list) -> tuple[dict, dict] | None:
    """The latest rollback two successive make smoke-deployed runs of one lane show, as (the run before, the run after):
    the revision serving changed, from the one the candidate tag still names after it (make rollback moves the traffic
    and leaves the tag where it was) or to an older one, and both runs recorded a /version answer. A run whose traffic
    moved during its smokes (serving_after) is evidence of neither end."""
    found, last = None, {}
    for run in runs:
        lane = (run.get("project"), run.get("region"))
        before, last[lane] = last.get(lane), run
        if not before or before.get("serving_after") or run.get("serving_after"):
            continue
        was, now = before.get("serving"), run.get("serving")
        if not was or not now or was == now:
            continue
        a, b = revision_number(was), revision_number(now)
        if ((run.get("candidate") == was or (a is not None and b is not None and b < a))
                and answered(before.get("version")) and answered(run.get("version"))):
            found = (before, run)
    return found


def lane_smokes(run: dict) -> list[tuple[str, str]]:
    """(lane, its smoke) for each lane a make smoke-deployed run passed: chat, media and SLM by their own smokes, graph
    by the API's smoke while /version said retrieval_graph on or auto."""
    ran = run.get("ran") if isinstance(run.get("ran"), dict) else {}
    passed = [(name, smoke) for name, smoke in LANES if ran.get(smoke) == 0]
    version = run.get("version") if isinstance(run.get("version"), dict) else {}
    if ran.get("smoke") == 0 and version.get("retrieval_graph") in GRAPH_ON:
        passed.append(("graph", "smoke"))
    return passed


# Markdown, as far as the three documents need it.
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
ITEM = re.compile(r"^ ?(?:[-*+]|\d{1,3}[.)])\s+(.*)$")           # a top-level item: one nested under it is indented
TABLE_RULE = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?$")
REJECTED = re.compile(r"reject|alternative", re.I)


def sections(text: str) -> list[tuple[int, str, list]]:
    """A Markdown text's headed sections in order: (level, heading, its lines up to the next heading of any level). A
    line inside a fenced code block is never a heading."""
    out, fenced = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
        heading = None if fenced else HEADING.match(line)
        if heading and not FENCE.match(line):
            out.append((len(heading.group(1)), heading.group(2), []))
        elif out:
            out[-1][2].append(line)
    return out


def listed(lines: list) -> list[str]:
    """The entries of a section's own lines: each top-level list item with its continuation lines (the lines after it
    up to a blank one, and indented ones, nested items among them), and each body row of a table, its cells joined by
    ' | ' (the row above a |---| rule is the header). Fenced code is skipped."""
    out, fenced, table, open_item = [], False, [], False

    def close_table():
        if table:
            body = table[2:] if len(table) > 1 and TABLE_RULE.match(table[1]) else table
            out.extend(" | ".join(c.strip() for c in row.strip().strip("|").split("|")) for row in body)
            table.clear()

    for line in lines:
        if FENCE.match(line):
            fenced, open_item = not fenced, False
            continue
        if fenced:
            continue
        stripped = line.strip()
        if stripped.startswith("|"):
            table.append(stripped)
            open_item = False
            continue
        close_table()
        item = ITEM.match(line)
        if item:
            out.append(item.group(1).strip())
            open_item = True
        elif not stripped:
            open_item = False
        elif open_item or (out and line.startswith("  ")):
            out[-1] += " " + stripped
    close_table()
    return out


def name_of(option: str) -> str:
    """A rejected option's name: its text up to the first ': ', ' | ' or ' - ', six words at most."""
    head = re.split(r":\s| \| | - | – | — ", option, maxsplit=1)[0].split()
    return " ".join(head[:6]) + (" ..." if len(head) > 6 else "")


def rejected_options(text: str) -> list[str] | None:
    """Each option a section on the alternatives you rejected names (a heading that says rejected or alternatives):
    its list items, its table's rows and its sub-sections, each as one text. None when there is no such section."""
    secs, found, i = sections(text), None, 0
    while i < len(secs):
        level, title, body = secs[i]
        i += 1
        if not REJECTED.search(title):
            continue
        found = (found or []) + listed(body)
        while i < len(secs) and secs[i][0] > level:                     # its sub-sections: an option each
            found.append(f"{secs[i][1]}: " + " ".join(line.strip() for line in secs[i][2] if line.strip()))
            i += 1
    return found


def words(text: str) -> int:
    return len(re.findall(r"\w+", text))


VOLUMES = (("1k", re.compile(r"\b1\s?k\b|\b1,000\b|\b1000\b|\bone thousand\b", re.I)),
           ("10k", re.compile(r"\b10\s?k\b|\b10,000\b|\b10000\b|\bten thousand\b", re.I)),
           ("100k", re.compile(r"\b100\s?k\b|\b100,000\b|\b1,00,000\b|\b100000\b|\b(?:one|1|a) lakh\b", re.I)))
RUPEES = re.compile(r"(?:₹|\bRs\.?|\bINR)\s?\d|\d[\d,]*(?:\.\d+)?\s?(?:INR|rupees?)\b", re.I)
DOLLARS = re.compile(r"(?:\$|\bUSD)\s?\d|\d[\d,]*(?:\.\d+)?\s?(?:USD|dollars?)\b", re.I)
DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b|\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* 20\d\d\b"
                  r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? 20\d\d\b")


def cost_model(text: str) -> tuple[list, list]:
    """(what COST-MODEL.md holds, what it lacks) of the three volumes, the amounts in each currency, a date and the rate."""
    held, missing = [], []
    named = [v for v, pattern in VOLUMES if pattern.search(text)]
    lacks = [v for v, _ in VOLUMES if v not in named]
    if lacks:
        missing.append(f"COST-MODEL.md does not name {' or '.join(lacks)} queries a month (1k, 10k and 100k, as 10k, "
                       "10,000 or 1 lakh)")
    else:
        held.append("COST-MODEL.md names the three volumes, 1k, 10k and 100k queries a month")
    rupees, dollars = len(RUPEES.findall(text)), len(DOLLARS.findall(text))
    if rupees >= AMOUNTS_MIN and dollars >= AMOUNTS_MIN:
        held.append(f"dual-priced: {plural(rupees, 'amount')} in rupees, {plural(dollars, 'amount')} in dollars")
    else:
        missing.append(f"COST-MODEL.md gives {plural(rupees, 'amount')} in rupees (Rs, INR or ₹ and a figure) and "
                       f"{plural(dollars, 'amount')} in dollars ($ or USD and a figure): {AMOUNTS_MIN} or more of each, "
                       "a pair for each volume")
    date = DATE.search(text)
    (held if date else missing).append(f"dated {date.group(0)}" if date else
                                       "COST-MODEL.md carries no date (2026-11-20, or 20 Nov 2026): prices move")
    rate = any(re.search(rf"\b{USD_INR}\b", line) and re.search(r"INR|\bRs\b|₹|rupee", line, re.I)
               and re.search(r"USD|\$|dollar", line, re.I) for line in text.splitlines())
    (held if rate else missing).append(f"at {USD_INR} rupees to the dollar" if rate else
                                       f"COST-MODEL.md does not state its rate, USD_INR = {USD_INR}, on one line")
    return held, missing


SYMPTOM = re.compile(r"^\s*(?:[-+]\s+)?symptoms?\s*[:\-–—]\s*\S", re.I)
CODE_SPAN = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
RUNNERS = ("make", "python", "python3", "bash", "sh")


def command_words(command: str) -> list[str] | None:
    """A command's words with any leading VAR=value assignments dropped; None when it does not parse."""
    try:
        found = shlex.split(command)
    except ValueError:
        return None
    while found and ASSIGNMENT.match(found[0]):
        found.pop(0)
    return found


def is_command(text: str) -> bool:
    found = command_words(text)
    return bool(found) and (found[0] in RUNNERS or found[0].startswith("./"))


def failure_modes(text: str) -> list[tuple[str, bool, list]]:
    """FAILURE-MODES.md's entries, each a headed section below the title with something in it: (its heading, whether
    it has a Symptom: line, the commands it gives in backticks or a fenced block that start with make, python,
    python3, bash, sh or ./, VAR=value assignments first allowed)."""
    out = []
    for level, title, body in sections(text):
        if level < 2 or not any(line.strip() for line in body):
            continue
        symptom = any(SYMPTOM.match(re.sub(r"[*_`]", "", line)) for line in body)
        commands, fenced = [], False
        for line in body:
            if FENCE.match(line):
                fenced = not fenced
                continue
            for candidate in ([line.strip().removeprefix("$ ")] if fenced else CODE_SPAN.findall(line)):
                if is_command(candidate):
                    commands.append(candidate.strip())
        out.append((title, symptom, commands))
    return out


def unresolved(command: str, targets: set, has_file, registry: dict) -> str:
    """Why a FAILURE-MODES command would not run in the fork, '' when it would: a make target the fork defines (make
    gotcha-drill with an ID= the registry gives the drill for: offline, or live with LIVE=), or a script the fork holds.
    has_file(path) says whether the fork holds a file at a path relative to its root."""
    found = command_words(command)
    if not found:
        return "it is not a command"
    runner, rest = found[0], found[1:]
    if runner == "make":
        settings = dict(w.split("=", 1) for w in rest if ASSIGNMENT.match(w))
        names, skip = [], False
        for word in rest:
            if skip:
                skip = False
            elif word in ("-C", "-f", "--directory", "--file"):
                skip = True
            elif not word.startswith("-") and not ASSIGNMENT.match(word):
                names.append(word)
        if not names:
            return "make with no target runs the default goal (dryrun), not this failure"
        target = names[0]
        if target not in targets:
            return f"the fork's Makefile and mk/*.mk define no {target} target"
        if target in GOTCHA_TARGETS:
            if target != "gotcha-drill":
                return f"make {target} {'shows' if target == 'gotchas' else 'detects'} a gotcha, it does not reproduce " \
                       "one: make gotcha-drill ID=<id> does"
            gotcha = settings.get("ID", "")
            if not gotcha:
                return "make gotcha-drill with no ID= runs every drill, not this failure's"
            entry = registry.get(gotcha)
            if entry is None:
                return f"ID={gotcha} is not in ops/gotchas.json, lesson 11.7's registry"
            drill = entry.get("drill") if isinstance(entry.get("drill"), dict) else {}
            mode = "live" if settings.get("LIVE") else "offline"
            if not drill.get(mode):
                return f"{gotcha} has no {mode} drill in ops/gotchas.json" + (
                    ": its live drill runs with LIVE=1" if mode == "offline" and drill.get("live") else "")
        return ""
    if runner in ("python", "python3"):
        skip, path = False, ""
        for i, word in enumerate(rest):
            if skip:
                skip = False
            elif word in ("-X", "-W"):
                skip = True
            elif word == "-c":
                return "python -c runs inline code, not a script the fork holds"
            elif word == "-m":
                module = rest[i + 1].replace(".", "/") if i + 1 < len(rest) else ""
                path = next((p for p in (f"{module}.py", f"{module}/__main__.py") if module and has_file(p)), "")
                return "" if path else f"python -m {rest[i + 1] if i + 1 < len(rest) else ''}: no such module in the fork"
            elif not word.startswith("-"):
                path = word
                break
    elif runner in ("bash", "sh"):
        path = next((w for w in rest if not w.startswith("-")), "")
    else:
        path = runner
    if not path:
        return f"{runner} names no script"
    return "" if has_file(path) else f"the fork holds no {path.removeprefix('./')}"


def rule_targets(text: str) -> set:
    """The targets a makefile's rules define: a line not indented that names them before a ':' (not := or ::=)."""
    names = set()
    for line in text.splitlines():
        rule = re.match(r"([^\s:#=][^:#=]*?)\s*:(?![:=])", line)
        if rule:
            names.update(t for t in rule.group(1).split() if not t.startswith(".") and not set("%$") & set(t))
    return names


# ---------------------------------------------------------------- the fork, as its files and records say

class Fork:
    """The fork's files, read and never changed; with a lane, only that lane's records count."""

    def __init__(self, root: Path, project: str = "", region: str = "", number: str = ""):
        self.root, self.project, self.region, self.number = root, project, region, number

    def text(self, rel: str) -> str | None:
        try:
            return (self.root / rel).read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return None
        except OSError as e:
            raise Stop(f"cannot read {rel} in the fork: {e}") from e

    def has_file(self, rel: str) -> bool:
        path = (self.root / rel.removeprefix("./")).resolve()
        return path.is_file() and self.root.resolve() in path.parents

    def json(self, rel: str):
        text = self.text(rel)
        try:
            return json.loads(text) if text is not None else None
        except ValueError:
            return None

    @functools.cached_property
    def runs(self) -> list:
        """The make smoke-deployed runs evals/reports/smoke-deployed.jsonl holds, in the order they were logged."""
        out = []
        for line in filter(str.strip, (self.text(SMOKE_LOG) or "").splitlines()):
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if not (isinstance(entry, dict) and entry.get("format") == release.SMOKE_FORMAT
                    and release.read_stamp(entry.get("finished"))):
                continue
            if self.project and (entry.get("project"), entry.get("region")) != (self.project, self.region):
                continue
            out.append(entry)
        return out

    @functools.cached_property
    def reports(self) -> list:
        """(path, report) for each live eval report in evals/reports/, the newest file first: make gate's
        gate-<revision>.json, make eval-live REPORT='s. With a lane, the reports of its documind-api only."""
        folder, found = self.root / REPORTS, []
        for path in (folder.glob("*.json") if folder.is_dir() else []):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not is_report(data):
                continue
            if self.number and f"{release.SERVICE}-{self.number}.{self.region}.run.app" not in str(data.get("api_url")):
                continue
            found.append((path.stat().st_mtime, path.name, data))
        found.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return [(f"{REPORTS}/{name}", data) for _, name, data in found]

    @functools.cached_property
    def targets(self) -> set:
        mk = self.root / "mk"
        files = ["Makefile", *(f"mk/{p.name}" for p in sorted(mk.glob("*.mk")))] if mk.is_dir() else ["Makefile"]
        return set().union(*(rule_targets(self.text(rel) or "") for rel in files))

    @functools.cached_property
    def registry(self) -> dict:
        data = self.json(REGISTRY)
        entries = data.get("gotchas") if isinstance(data, dict) else None
        return {g["id"]: g for g in entries or [] if isinstance(g, dict) and isinstance(g.get("id"), str)}

    @functools.cached_property
    def corpus(self) -> dict:
        """{tenant: its documents and their pages} for each folder under evals/corpus/ that is not one of the kit's."""
        folder = self.root / "evals" / "corpus"
        if not folder.is_dir():
            return {}
        return {p.name: documents(p) for p in sorted(folder.iterdir()) if p.is_dir() and p.name not in KIT_TENANTS}

    @property
    def own_tenant(self) -> str:
        """The tenant of your own with the most pages ('' when there is none)."""
        totals = {t: sum(n or 0 for _, n in docs) for t, docs in self.corpus.items()}
        return max(sorted(totals), key=lambda t: totals[t], default="")

    def where(self) -> str:
        return f" of {self.project} in {self.region}" if self.project else ""


# ---------------------------------------------------------------- the lane, read and never changed

# The only gcloud commands this runs. gcloud_json() refuses any other before it runs, so neither check nor handover can
# change the lane; the two tokens are minted by release.identity_token(), as make eval-live mints them.
READS = (("gcloud", "projects", "describe"), ("gcloud", "run", "services", "describe"),
         ("gcloud", "run", "services", "list"), ("gcloud", "run", "revisions", "list"),
         ("gcloud", "scheduler", "jobs", "describe"),
         ("gcloud", "iam", "workload-identity-pools", "providers", "describe"),
         ("gcloud", "billing", "projects", "describe"), ("gcloud", "billing", "budgets", "list"),
         ("gcloud", "storage", "buckets", "describe"), ("gcloud", "storage", "objects", "describe"),
         ("gcloud", "auth", "print-access-token"))
IN_SLM_REGION = ("documind-slm", "documind-vllm")   # the Makefile's DOWN_SERVICES_GPU, deployed in SLM_REGION
MONITORING = "https://monitoring.googleapis.com/v3/projects/{project}/alertPolicies?pageSize=500"


def is_read(argv: list) -> bool:
    return any(tuple(argv[:len(r)]) == r for r in READS)


def gcloud_json(argv: list):
    """One of READS, its output as JSON. Any other command is refused before it runs."""
    if not is_read(argv):
        raise Stop(f"capstone_check only reads, and {' '.join(argv[:5])} is not one of its reads")
    r = release.run(argv)
    what = " ".join(w for w in argv[:5] if not w.startswith("-"))
    if r.returncode:
        raise Stop(f"{what} failed (exit {r.returncode}): {release.cause(r.stderr)}")
    try:
        return json.loads(r.stdout or "null")
    except ValueError:
        raise Stop(f"{what} did not return JSON") from None


def access_token() -> str:
    """gcloud's own access token, for the one read gcloud has no GA command for (the alert policies). Never printed."""
    argv = ["gcloud", "auth", "print-access-token"]
    assert is_read(argv)
    r = release.run(argv)
    token = (r.stdout or "").strip()
    if r.returncode or not token or any(ch.isspace() for ch in token):
        raise Stop(f"gcloud auth print-access-token failed (exit {r.returncode}): {release.cause(r.stderr)}")
    return token


def http_json(url: str, token: str) -> tuple:
    """GET url with the token: (HTTP status, the JSON body or None, what went wrong or ''). Two attempts on a
    connection failure or a 5xx, as release.get_version makes them: a revision scaled to zero waits for an instance.
    A 4xx is an answer, returned as it is."""
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    last = ""
    for _ in range(2):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                status, raw = response.status, response.read()
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return e.code, None, f"HTTP {e.code}"
            last = f"HTTP {e.code}"
            continue
        except (urllib.error.URLError, OSError) as e:
            last = str(getattr(e, "reason", e))
            continue
        try:
            return status, json.loads(raw.decode("utf-8")), ""
        except ValueError:
            return status, None, "the body is not JSON"
    return 0, None, last


def said(status: int, error: str) -> str:
    return error or f"HTTP {status}"


class Lane:
    """The lane, read and never changed: READS through gcloud_json(), the tokens as make eval-live mints them, and
    GETs on documind-api's canonical URL, the audience either token is minted for (F42)."""

    def __init__(self, project: str, region: str, slm_region: str):
        self.project, self.region, self.slm_region = project, region, slm_region
        self._services = {}

    @functools.cached_property
    def number(self) -> str:
        info = gcloud_json(["gcloud", "projects", "describe", self.project, "--format=json"])
        number = str(info.get("projectNumber") or "") if isinstance(info, dict) else ""
        if not number.isdigit():
            raise Stop(f"gcloud projects describe {self.project} returned no project number")
        return number

    @property
    def url(self) -> str:
        return f"https://{release.SERVICE}-{self.number}.{self.region}.run.app"

    @functools.cached_property
    def member(self) -> str:
        return os.environ.get("DOCUMIND_ID_TOKEN") or release.identity_token(self.project, release.MEMBER_SA, self.url)

    @functools.cached_property
    def outsider(self) -> str:
        return os.environ.get("DOCUMIND_OUTSIDER_TOKEN") or release.identity_token(
            self.project, release.OUTSIDER_SA, self.url)

    @functools.cached_property
    def version(self) -> tuple:
        return http_json(f"{self.url}/version", self.member)

    def sources(self, tenant: str, token: str) -> tuple:
        return http_json(f"{self.url}/v1/sources?tenant_id={urllib.parse.quote(tenant)}", token)

    def services(self, region: str) -> list:
        if region not in self._services:
            data = gcloud_json(["gcloud", "run", "services", "list", f"--region={region}", f"--project={self.project}",
                                "--format=json"])
            if not isinstance(data, list):
                raise Stop(f"gcloud run services list in {region} did not return a list")
            self._services[region] = [s for s in data if isinstance(s, dict)]
        return self._services[region]

    def deployed_items(self) -> list:
        """(name, region, the service) for each Cloud Run service of the lane: every one in REGION, and the GPU
        services in SLM_REGION, where make deploy-slm and make deploy-vllm put them."""
        out = []
        for where in dict.fromkeys((self.region, self.slm_region)):
            for service in self.services(where):
                name = str((service.get("metadata") or {}).get("name") or "")
                if name and where == (self.slm_region if name in IN_SLM_REGION else self.region):
                    out.append((name, where, service))
        return out

    @functools.cached_property
    def deployed(self) -> set:
        return {name for name, _, _ in self.deployed_items()}

    def describe(self, service: str) -> dict:
        data = gcloud_json(["gcloud", "run", "services", "describe", service, f"--region={self.region}",
                            f"--project={self.project}", "--format=json"])
        if not isinstance(data, dict):
            raise Stop(f"gcloud run services describe {service} did not return a service")
        return data

    @functools.cached_property
    def revisions(self) -> list:
        data = gcloud_json(["gcloud", "run", "revisions", "list", f"--service={release.SERVICE}",
                            f"--region={self.region}", f"--project={self.project}", "--format=json"])
        if not isinstance(data, list):
            raise Stop("gcloud run revisions list did not return a list")
        return [r for r in data if isinstance(r, dict) and release.REVISION.fullmatch(
            str((r.get("metadata") or {}).get("name") or ""))]

    def policies(self) -> list:
        """Every alert policy on the lane (the Monitoring API's alertPolicies.list, page by page)."""
        token, out, page = access_token(), [], ""
        while True:
            url = MONITORING.format(project=self.project) + (f"&pageToken={urllib.parse.quote(page)}" if page else "")
            status, body, error = http_json(url, token)
            if status != 200 or not isinstance(body, dict):
                raise Stop(f"GET the Monitoring API's alertPolicies answered {said(status, error)}")
            out += [p for p in body.get("alertPolicies") or [] if isinstance(p, dict)]
            page = str(body.get("nextPageToken") or "")
            if not page:
                return out


def iap_on(service: dict) -> bool:
    """Whether a Cloud Run service has IAP on: --iap sets the run.googleapis.com/iap-enabled annotation."""
    annotations = (service.get("metadata") or {}).get("annotations") or {}
    return str(annotations.get("run.googleapis.com/iap-enabled", "")).lower() == "true" or service.get("iapEnabled") is True


# ---------------------------------------------------------------- the eight components

def no_runs(fork: Fork) -> str:
    return (f"no make smoke-deployed run{fork.where()} in {SMOKE_LOG}: make smoke-deployed PROJECT=<id> (lesson 11.3) "
            "records one")


def no_document(name: str) -> str:
    """A document missing from the fork's root, and its template: copied as it ships, the template still fails the
    component, until its {{...}} placeholders are replaced."""
    return (f"{name} is missing from the fork's root: copy {TEMPLATES}/{name} there from the kit, and replace each "
            "{{...}} placeholder in it")


def component_1(fork: Fork, lane: Lane | None) -> tuple[list, list]:
    held, missing = [], []
    script = fork.text(UI_SCRIPT)
    deploy = shell_command(script or "", "gcloud run deploy documind-ui")
    lacks = [flag for flag in IAP_FLAGS if not re.search(rf"(?<!\S){re.escape(flag)}(?!\S)", deploy)]
    if not deploy:
        missing.append(f"{UI_SCRIPT} " + ("is missing from the fork" if script is None else
                                          "has no gcloud run deploy documind-ui") +
                       ": the UI is the live URL, and make deploy-services deploys it from that script")
    elif lacks:
        missing.append(f"{UI_SCRIPT} deploys documind-ui without {' and '.join(lacks)}: the live URL is not behind IAP")
    else:
        held.append(f"the fork deploys documind-ui behind IAP: {' and '.join(IAP_FLAGS)} ({UI_SCRIPT})")
    run = fork.runs[-1] if fork.runs else None
    if run is None:
        missing.append(no_runs(fork))
    elif not answered(run.get("version")):
        missing.append(f"the last make smoke-deployed run ({run['finished']}) recorded no /version answer: "
                       f"{release.answered(run.get('version'))}")
    else:
        held.append(f"a member was answered: GET /version said {release.answered(run['version'])} (make smoke-deployed, "
                    f"{run['finished']})")
    asked = [(rel, report) for rel, report in fork.reports if isolation_asked(report)]
    if not asked:
        missing.append(f"no live eval report{fork.where()} in {REPORTS}/ asked the isolation rows: make gate (lesson "
                       "11.2) writes one, as make eval-live REPORT=<file> does")
    elif outsider_refused(asked[0][1]):
        held.append(f"a non-member was refused: every isolation row ({isolation_asked(asked[0][1])}) answered 403 to the "
                    f"outsider ({asked[0][0]})")
    else:
        rel, report = asked[0]
        missing.append(f"in the newest live eval report that asked the isolation rows ({rel}) the outsider was not always "
                       f"refused: isolation_403_rate {pct((report.get('scores') or {}).get('isolation_403_rate'))}"
                       + (f"; {report['isolation'][0]}" if report.get("isolation") else ""))
    if lane:
        status, body, error = lane.version
        if status == 200 and answered(body):
            held.append(f"lane: GET /version as {release.MEMBER_SA}: 200, {release.answered(body)}")
        else:
            missing.append(f"lane: GET /version as {release.MEMBER_SA} answered {said(status, error)}, not 200")
        tenant = fork.own_tenant or KIT_TENANTS[0]
        status, _, error = lane.sources(tenant, lane.outsider)
        if status == 403:
            held.append(f"lane: GET /v1/sources?tenant_id={tenant} as {release.OUTSIDER_SA}, on no roster: 403")
        else:
            missing.append(f"lane: GET /v1/sources?tenant_id={tenant} as {release.OUTSIDER_SA}, on no roster, answered "
                           f"{said(status, error)}, not 403: the roster no longer decides")
        if "documind-ui" not in lane.deployed:
            missing.append(f"lane: documind-ui is not deployed in {lane.region}: make deploy-services deploys it")
        elif iap_on(lane.describe("documind-ui")):
            held.append("lane: documind-ui has IAP on (run.googleapis.com/iap-enabled)")
        else:
            missing.append("lane: documind-ui does not have IAP on: make deploy-services SCRIPTS=commands/lesson-12.4.sh "
                           "deploys it with --iap")
    return held, missing


def component_2(fork: Fork, lane: Lane | None) -> tuple[list, list]:
    held, missing = [], []
    tenant = fork.own_tenant
    if not tenant:
        return held, [f"evals/corpus/ holds no tenant of your own, only the kit's ({', '.join(KIT_TENANTS)}): your corpus "
                      "goes in evals/corpus/<your tenant>/, which make ingest-corpus uploads under that tenant"]
    docs = fork.corpus[tenant]
    pages = sum(n or 0 for _, n in docs)
    unknown = [name for name, n in docs if n is None]
    line = (f"{tenant}'s corpus: {plural(len(docs), 'document')}, {plural(pages, 'page')} as the ingest worker counts "
            "them" + (f" (pages not counted offline: {', '.join(unknown)})" if unknown else ""))
    if pages >= PAGES_MIN:
        held.append(line)
    else:
        missing.append(f"{line}: {PAGES_MIN} or more")
    stems = {stem(name) for name, _ in docs}
    asked = next(((rel, [r for r in report.get("records") or [] if isinstance(r, dict) and r.get("tenant") == tenant])
                  for rel, report in fork.reports
                  if any(isinstance(r, dict) and r.get("tenant") == tenant for r in report.get("records") or [])), None)
    if asked is None:
        missing.append(f"no live eval report{fork.where()} in {REPORTS}/ asked a question of {tenant}'s: golden rows "
                       f"for {tenant} (lesson 4.1), then make gate")
    elif cited(asked[1], tenant, stems):
        held.append(f"a query cites one: {cited(asked[1], tenant, stems)} and passed ({asked[0]})")
    else:
        missing.append(f"in {asked[0]}, no row of {tenant}'s passed citing one of its documents")
    if lane:
        status, body, error = lane.sources(tenant, lane.member)
        if status == 403:
            missing.append(f"lane: GET /v1/sources?tenant_id={tenant} as {release.MEMBER_SA}: 403, it is on no roster of "
                           f"{tenant}'s: make roster TENANT={tenant} MEMBERS={release.MEMBER_SA}@{lane.project}"
                           ".iam.gserviceaccount.com")
        elif status != 200 or not isinstance(body, dict):
            missing.append(f"lane: GET /v1/sources?tenant_id={tenant} answered {said(status, error)}")
        else:
            indexed = {stem(str(s.get("name") or "")) for s in body.get("sources") or []
                       if isinstance(s, dict) and s.get("status") == "indexed"}
            absent = [name for name, _ in docs if stem(name) not in indexed]
            if absent:
                missing.append(f"lane: GET /v1/sources?tenant_id={tenant} does not list these as indexed: "
                               f"{', '.join(absent)} (make ingest-corpus PROJECT={lane.project} uploads them)")
            else:
                held.append(f"lane: GET /v1/sources?tenant_id={tenant}, the Documents page's read, lists all "
                            f"{plural(len(docs), 'document')} indexed")
    return held, missing


def run_eval_offline(fork: Fork) -> tuple[int, str]:
    """make eval in the fork: its own evals/run_eval.py, offline (no --api-url: no credential, no network). (exit code,
    the lines that say what failed, or its last line)."""
    if not fork.has_file("evals/run_eval.py"):
        return STOPPED, "evals/run_eval.py is missing"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    try:
        r = subprocess.run([sys.executable, "evals/run_eval.py"], cwd=fork.root, env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    except (OSError, subprocess.TimeoutExpired) as e:
        return STOPPED, f"evals/run_eval.py could not run: {e}"
    lines = [line.strip() for line in (r.stdout + "\n" + r.stderr).splitlines() if line.strip()]
    failing = [line for i, line in enumerate(lines) if i and lines[i - 1].startswith("[FAIL]")]
    return r.returncode, "; ".join(failing[:2]) or (lines[-1] if lines else "no output")


def component_3(fork: Fork, lane: Lane | None) -> tuple[list, list]:
    held, missing = [], []
    text = fork.text("evals/golden.jsonl")
    try:
        rows = [json.loads(line) for line in (text or "").splitlines() if line.strip()] if text is not None else None
    except ValueError as e:
        rows, missing = None, [f"evals/golden.jsonl does not parse as JSON lines: {e}"]
    if text is None:
        missing.append("evals/golden.jsonl is missing")
    elif rows is not None:
        isolation = sum(1 for r in rows if isinstance(r, dict) and r.get("shape") == "isolation")
        line = f"evals/golden.jsonl: {plural(len(rows), 'golden row')}, {isolation} of them isolation rows"
        if len(rows) >= GOLDEN_MIN and isolation >= ISOLATION_MIN:
            held.append(line)
        else:
            missing.append(f"{line}: {GOLDEN_MIN} or more, {ISOLATION_MIN} or more of them isolation rows")
    code, said_ = run_eval_offline(fork)
    if code == 0:
        held.append("make eval: evals/run_eval.py offline exits 0 (the golden set can go red, and still holds the rows "
                    "that would)")
    else:
        missing.append(f"make eval: evals/run_eval.py offline exits {code}: {said_}")
    return held, missing


def component_4(fork: Fork, lane: Lane | None) -> tuple[list, list]:
    run = fork.runs[-1] if fork.runs else None
    if run is None:
        return [], [no_runs(fork)]
    passed = lane_smokes(run)
    if not passed:
        ran = run.get("ran") if isinstance(run.get("ran"), dict) else {}
        return [], [f"the last make smoke-deployed run ({run['finished']}) passed no lane's smoke: smoke-chat (chat), "
                    "smoke-media (media), smoke-slm (SLM), or the API's smoke with /version's retrieval_graph on or "
                    f"auto (graph); it ran {', '.join(f'{t} (exit {c})' for t, c in ran.items()) or 'none'}"
                    + (f"; skipped, a service not deployed: {', '.join(run['skipped'])}" if run.get("skipped") else "")]
    held = [f"{name}: make {smoke} passed in the last make smoke-deployed run ({run['finished']})"
            for name, smoke in passed]
    if not lane:
        return held, []
    needs, up = dict(release.SMOKES), []
    for name, smoke in passed:
        absent = [s for s in needs.get(smoke, ()) if s not in lane.deployed]
        status, body, _ = lane.version if name == "graph" else (200, {}, "")
        graph_off = name == "graph" and not (isinstance(body, dict) and body.get("retrieval_graph") in GRAPH_ON)
        if not absent and not graph_off:
            up.append(name)
            held.append(f"lane: {name}'s services are deployed: {', '.join(needs.get(smoke, ()))}"
                        + (f", and /version says retrieval_graph {body['retrieval_graph']}" if name == "graph" else ""))
    if up:
        return held, []
    return held, ["lane: none of those lanes is deployed now (gcloud run services list"
                  + (", and /version's retrieval_graph" if any(n == "graph" for n, _ in passed) else "") + ")"]


def component_5(fork: Fork, lane: Lane | None) -> tuple[list, list]:
    text = fork.text("ARCHITECTURE.md")
    if text is None:
        return [], [no_document("ARCHITECTURE.md")]
    options = rejected_options(text)
    if options is None:
        return [], ["ARCHITECTURE.md has no section on the alternatives you rejected: a heading that says Rejected (or "
                    f"Alternatives), with {REJECTED_MIN} or more under it, each with why"]
    argued = [o for o in options if words(o) >= REASON_WORDS]
    short = [o for o in options if words(o) < REASON_WORDS]
    line = (f"ARCHITECTURE.md names {plural(len(argued), 'rejected option')} with a reason"
            + (f" (and {len(short)} without one: {'; '.join(name_of(o) for o in short)})" if short else ""))
    if len(argued) >= REJECTED_MIN:
        return [f"{line}: {'; '.join(name_of(o) for o in argued)}"], []
    return [], [f"{line}: {REJECTED_MIN} or more, each with why ({REASON_WORDS} words or more)"]


def component_6(fork: Fork, lane: Lane | None) -> tuple[list, list]:
    text = fork.text("COST-MODEL.md")
    if text is None:
        return [], [no_document("COST-MODEL.md")]
    return cost_model(text)


def component_7(fork: Fork, lane: Lane | None) -> tuple[list, list]:
    text = fork.text("FAILURE-MODES.md")
    if text is None:
        return [], [no_document("FAILURE-MODES.md")]
    held, missing, proved = [], [], 0
    for title, symptom, commands in failure_modes(text):
        why = {c: unresolved(c, fork.targets, fork.has_file, fork.registry) for c in commands}
        runs = next((c for c in commands if not why[c]), "")
        if symptom and runs:
            proved += 1
            held.append(f'"{title}": {runs}')
            continue
        lacks = [] if symptom else ["no Symptom: line"]
        if not commands:
            lacks.append("no command in backticks (make ..., python ..., bash ...)")
        elif not runs:
            lacks += [f"`{c}`: {why[c]}" for c in commands]
        missing.append(f'"{title}": {"; ".join(lacks)}')
    if proved >= ENTRIES_MIN:
        return [f"{plural(proved, 'entry', 'entries')} proved by a command the fork runs:", *held], []
    return held, [f"{plural(proved, 'entry', 'entries')} proved, {ENTRIES_MIN} or more: an entry is a heading with a "
                  "Symptom: line and a command in backticks that the fork can run", *missing]


def component_8(fork: Fork, lane: Lane | None) -> tuple[list, list]:
    held, missing = [], []
    text = fork.text("RUNBOOK.md")
    if text is None:
        missing.append(no_document("RUNBOOK.md"))
    elif re.search(r"\bmake rollback\b|\bupdate-traffic\b", text):
        held.append("RUNBOOK.md says how to roll back")
    else:
        missing.append("RUNBOOK.md does not say how to roll back: make rollback (lesson 11.3), or gcloud run services "
                       "update-traffic")
    found = rollback(fork.runs)
    if found is None:
        missing.append(no_runs(fork) if not fork.runs else
                       f"no two successive make smoke-deployed runs{fork.where()} show a rollback: make smoke-deployed "
                       "before and after make rollback records one (lesson 11.3)")
    else:
        before, after = found
        how = ("the traffic left the revision the candidate tag names" if after.get("candidate") == before["serving"]
               else "back to an older revision")
        held.append(f"a recorded rollback, {how}: {before['serving']} -> {after['serving']}, between the make "
                    f"smoke-deployed runs of {before['finished']} and {after['finished']}; /version before: "
                    f"{release.answered(before['version'])}; after: {release.answered(after['version'])}")
        if lane:
            names = {str((r.get("metadata") or {}).get("name")) for r in lane.revisions}
            absent = [n for n in (before["serving"], after["serving"]) if n not in names]
            if absent:
                missing.append(f"lane: {release.SERVICE} has no {' or '.join(absent)}: the recorded rollback is another "
                               "lane's")
            else:
                held.append(f"lane: both are {release.SERVICE} revisions on {lane.project}")
    return held, missing


CHECKS = ((1, component_1), (2, component_2), (3, component_3), (4, component_4), (5, component_5), (6, component_6),
          (7, component_7), (8, component_8))


def fork_root(text: str) -> Path:
    root = Path(text or KIT).expanduser().resolve()
    if not root.is_dir():
        raise Stop(f"the fork {text} is not a directory: --fork (FORK=) names the checkout of your fork")
    return root


def lane_of(a) -> Lane | None:
    if not a.project:
        return None
    if not release.PROJECT_ID.fullmatch(a.project):
        raise Stop("pass --project with the lane's project id (PROJECT)")
    slm_region = a.slm_region or release.SLM_REGION_DEFAULT
    if not release.REGION_NAME.fullmatch(a.region or ""):
        raise Stop("pass --region with the region documind-api runs in (REGION)")
    if not release.REGION_NAME.fullmatch(slm_region):
        raise Stop("pass --slm-region with the region of the GPU services (SLM_REGION)")
    return Lane(a.project, a.region, slm_region)


def say(prefix: str, text: str) -> None:
    print(textwrap.fill(text, width=118, initial_indent=prefix, subsequent_indent=" " * len(prefix),
                        break_long_words=False, break_on_hyphens=False))


def cmd_check(a) -> int:
    root, lane = fork_root(a.fork), lane_of(a)
    if lane and release.SERVICE not in lane.deployed:
        raise Stop(f"{release.SERVICE} is not deployed in {lane.region} ({lane.project}), so there is no lane to read "
                   "there: REGION is the region the lane runs in, and the Makefile's default is us-central1")
    fork = Fork(root, *((lane.project, lane.region, lane.number) if lane else ()))
    say(">> ", f"capstone-check: the fork at {root}" + (
        f", and the lane {lane.project} in {lane.region}, read only" if lane else
        ", offline: its files and records, and make eval. PROJECT= adds the lane's reads"))
    failed = []
    for n, check in CHECKS:
        held, missing = check(fork, lane)
        print(f"   {n}  {'FAIL' if missing else 'PASS'}  {COMPONENTS[n]}")
        for line in held:
            say("            ", line)
        for line in missing:
            say("          - ", line)
        if missing:
            failed.append(n)
    if not failed:
        say(">> ", "complete: every one of the eight components PASSes. Nothing here is scored: the defence scores the "
                   "five dimensions")
        return 0
    names = " and ".join(", ".join(map(str, failed)).rsplit(", ", 1))
    say(">> ", f"incomplete: component{'s' if len(failed) > 1 else ''} {names} FAIL{'' if len(failed) > 1 else 's'}. "
               "A missing component is an incomplete submission, and the defence does not run")
    return INCOMPLETE


# ---------------------------------------------------------------- the handover

def make_default(text: str, name: str) -> str | None:
    found = re.search(rf"^{re.escape(name)}[ \t]*\?=[ \t]*(.*?)[ \t]*$", text, re.M)
    return found.group(1) if found else None


def tf_block(text: str, kind: str, name: str) -> str:
    """A Terraform resource block, from its first line to its closing brace; '' when the file declares none."""
    found = re.search(rf'^resource "{re.escape(kind)}" "{re.escape(name)}" \{{\n', text, re.M)
    if not found:
        return ""
    end = text.find("\n}\n", found.start())
    return text[found.start():end + 2 if end >= 0 else len(text)]


def tf_string(block: str, key: str) -> str:
    found = re.search(rf'^\s*{re.escape(key)}\s*=\s*"([^"]*)"', block, re.M)
    return found.group(1) if found else ""


def cron_time(schedule: str, zone: str) -> str:
    """'0 23 * * *' in Asia/Kolkata as 23:00 IST; '' for a schedule that is not one time every day."""
    parts = schedule.split()
    if len(parts) != 5 or not (parts[0].isdigit() and parts[1].isdigit()) or parts[2:] != ["*", "*", "*"]:
        return ""
    return f"{int(parts[1]):02d}:{int(parts[0]):02d} " + ("IST" if zone == "Asia/Kolkata" else zone)


def cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


class Handover:
    """HANDOVER.md's sections, each the checkout's statement and, with a lane, the lane's reading of it. A lane read
    that fails goes to unread, and the section says so."""

    def __init__(self, fork: Fork, lane: Lane | None):
        self.fork, self.lane, self.unread = fork, lane, []

    def read(self, what: str, fn):
        try:
            return fn()
        except STOPS as e:
            self.unread.append(f"{what}: {e}")
            return None

    def policies(self) -> list:
        out = ["## Alert policies", ""]
        try:
            rows = remediate.runbooks(self.fork.root / "terraform",
                                      remediate.load_catalog(self.fork.root / "ops" / "runbooks.json"))
        except STOPS as e:
            rows = None
            out += [f"The checkout's policies could not be read: {e}", ""]
        live = self.read("the alert policies (the Monitoring API's alertPolicies)", self.lane.policies) \
            if self.lane else None
        on = {str(p.get("displayName")): p for p in live or []}
        if rows is not None:
            out += [f"{plural(len(rows), 'policy', 'policies')} declared in terraform/*.tf, each with what "
                    "ops/runbooks.json says to do when it pages" + (f"; {sum(r['policy'] in on for r in rows)} of them on "
                                                                   "the lane." if live is not None else "."), ""]
            out += ["| Policy | Declared in | Applied | When it pages | On the lane |", "|---|---|---|---|---|"]
            for r in rows:
                act = ("make remediate proposes a rollback" if r.get("action") == "rollback" else
                       f"a person: {r.get('person') or 'see its documentation'}")
                there = on.get(r["policy"])
                lane_cell = ("not read" if live is None else "not on the lane" if there is None else
                             ("enabled" if there.get("enabled", True) else "disabled") + ", " + (
                                 plural(len(there.get("notificationChannels") or []), "channel")
                                 if there.get("notificationChannels") else "no channel: it notifies nobody"))
                out.append(f"| {cell(r['policy'])} | {r['resource'].split(' ', 1)[0].removeprefix('terraform/')} | "
                           f"{'when ' + r['gate'].upper() + '=true' if r.get('gate') else 'always'} | {cell(act)} | "
                           f"{lane_cell if self.lane else '-'} |")
            extra = sorted(set(on) - {r["policy"] for r in rows})
            if extra:
                out += ["", f"On the lane and declared by no .tf file in this checkout: {'; '.join(extra)}."]
        return out + [""]

    def night_job(self) -> list:
        out = ["## The night job", ""]
        off = self.fork.text("terraform/off.tf") or ""
        block = tf_block(off, "google_cloud_scheduler_job", "off")
        name, schedule, zone = (tf_string(block, k) for k in ("name", "schedule", "time_zone"))
        floored = re.findall(r"(documind-[a-z0-9-]+):\$(?:SLM_REGION|REGION)\b", off)
        if block:
            out.append(f"terraform/off.tf declares the Cloud Scheduler job `{name}`: `{schedule}` in {zone}"
                       + (f", {cron_time(schedule, zone)}" if cron_time(schedule, zone) else "")
                       + f", every night. It runs the Cloud Run job documind-off, which floors {', '.join(floored)} "
                       "to min-instances 0 where they are deployed; make off-now runs the same job on demand.")
        else:
            out.append("terraform/off.tf declares no nightly job in this checkout.")
        if self.lane and block:
            job = self.read(f"the night job (gcloud scheduler jobs describe {name})", lambda: gcloud_json(
                ["gcloud", "scheduler", "jobs", "describe", name, f"--location={self.lane.region}",
                 f"--project={self.lane.project}", "--format=json"]))
            if isinstance(job, dict):
                status = job.get("status") if isinstance(job.get("status"), dict) else {}
                out += ["", f"On the lane: {job.get('state', '?')}, `{job.get('schedule', '?')}` in "
                        f"{job.get('timeZone', '?')}; last attempt {job.get('lastAttemptTime') or 'none yet'}"
                        + (f", which failed: {status.get('message') or status.get('code')}" if status.get("code") else "")
                        + "."]
        return out + [""]

    def floors(self) -> list:
        out = ["## Floors", ""]
        mk = self.fork.text("Makefile") or ""
        out.append(f"The checkout: `MIN_INSTANCES ?= {make_default(mk, 'MIN_INSTANCES') or '?'}` in the Makefile, the UI's "
                   "floor when make deploy-services deploys it (1 on a session day, 0 after), and the night job floors "
                   "the GPU services, the gateway and the UI to 0 every night. A floor above 0 bills its instances "
                   "while they idle.")
        if self.lane:
            items = self.read("the floors (gcloud run services list)", self.lane.deployed_items)
            if items is not None:
                out += ["", "| Service | Region | min-instances | max-instances |", "|---|---|---|---|"]
                for name, where, service in sorted(items, key=lambda t: t[0]):
                    notes = ((service.get("spec") or {}).get("template") or {}).get("metadata") or {}
                    notes = notes.get("annotations") or {}
                    out.append(f"| {name} | {where} | {notes.get('autoscaling.knative.dev/minScale', '0')} | "
                               f"{notes.get('autoscaling.knative.dev/maxScale', '-')} |")
        return out + [""]

    def revisions(self) -> list:
        out = ["## Revisions", ""]
        for label, meaning in ((".candidate-revision", "make promote moves the traffic to it"),
                               (".previous-revision", "make rollback returns the traffic to it")):
            name = (self.fork.text(label) or "").strip()
            out.append(f"- `{label}`: {name or 'none in this checkout'}" + (f" ({meaning})" if name else ""))
        record = self.fork.json(f"{REPORTS}/gate.json")
        if isinstance(record, dict) and record.get("format") == release.GATE_FORMAT:
            out.append(f"- the gate record (`{REPORTS}/gate.json`): {record.get('revision')}, "
                       f"{str(record.get('verdict')).upper()}, finished {record.get('finished')}; make promote-gated "
                       f"holds it for {release.MAX_AGE_HOURS:g} hours")
        else:
            out.append(f"- the gate record (`{REPORTS}/gate.json`): none in this checkout (make gate writes it)")
        run = self.fork.runs[-1] if self.fork.runs else None
        out.append(f"- the last make smoke-deployed run: {run['finished']}, serving {run.get('serving')}, "
                   f"{str(run.get('verdict')).upper()}" if run else "- the last make smoke-deployed run: none in this "
                   "checkout")
        if self.lane:
            api = self.read(f"{release.SERVICE}'s traffic (gcloud run services describe)",
                            lambda: self.lane.describe(release.SERVICE))
            revisions = self.read(f"{release.SERVICE}'s revisions (gcloud run revisions list)",
                                  lambda: self.lane.revisions)
            if isinstance(api, dict):
                traffic = [t for t in (api.get("status") or {}).get("traffic") or [] if isinstance(t, dict)]
                out += ["", "On the lane, documind-api's traffic table:", "",
                        "| Revision | Percent | Tag |", "|---|---|---|"]
                out += [f"| {t.get('revisionName') or '(latest)'} | {t.get('percent') or 0} | {t.get('tag') or ''} |"
                        for t in traffic]
            if revisions is not None:
                envs = {str((r.get("metadata") or {}).get("name")): release.container_of(r.get("spec"))[1]
                        for r in revisions}
                serving = release.traffic_of(api)[0] if isinstance(api, dict) and (api.get("status") or {}).get(
                    "traffic") else ""
                env = envs.get(serving, {})
                out += ["", f"{plural(len(revisions), 'revision')} of documind-api on the lane (Cloud Run keeps every "
                        "one, so a rollback is a traffic move)" + (
                            f"; the serving one, {serving}, runs GIT_SHA {env.get('GIT_SHA', '(unset)')} and "
                            f"GENERATOR_MODEL {env.get('GENERATOR_MODEL', '(unset)')}" if serving in envs else "") + "."]
        return out + [""]

    def trust(self) -> list:
        out = ["## CI trust", ""]
        inputs = self.fork.json(f"terraform/{release.infra.INPUT_FILE}")
        said_ = {k: (inputs or {}).get(k) for k in release.infra.TRUST} if isinstance(inputs, dict) else None
        if said_ and all(said_.values()):
            out.append(f"The checkout's confirmed inputs (terraform/{release.infra.INPUT_FILE}, which make plan saved): "
                       f"{said_['github_repository']} (repository ID {said_['github_repository_id']}), "
                       f"{said_['deploy_ref']}. wif.tf trusts that repository, by its immutable ID, on that branch "
                       "alone; no key exists for the pipeline (make keys-check lists any user-managed key).")
        else:
            out.append(f"No confirmed inputs in this checkout (terraform/{release.infra.INPUT_FILE}, gitignored, is "
                       "what make plan saves).")
        if self.lane:
            provider = self.read("the CI trust (gcloud iam workload-identity-pools providers describe github-oidc)",
                                 lambda: gcloud_json(["gcloud", "iam", "workload-identity-pools", "providers",
                                                      "describe", "github-oidc", "--workload-identity-pool=documind-github",
                                                      "--location=global", f"--project={self.lane.project}",
                                                      "--format=json"]))
            if isinstance(provider, dict):
                try:
                    lane_trust = release.infra.parse_trust(provider.get("attributeCondition"))
                except release.infra.Stop as e:
                    out += ["", f"On the lane: the provider's condition is not wif.tf's three gates ({e})."]
                else:
                    agree = "the same as the checkout's" if said_ and lane_trust == said_ else \
                        "not what this checkout states" if said_ else "nothing in this checkout to compare"
                    out += ["", f"On the lane, the workload identity provider's condition: "
                            f"{lane_trust['github_repository']} (repository ID {lane_trust['github_repository_id']}), "
                            f"{lane_trust['deploy_ref']}: {agree}."]
        return out + [""]

    def budget(self) -> list:
        out = ["## Budget", ""]
        tf = self.fork.text("terraform/budget.tf") or ""
        name = tf_string(tf_block(tf, "google_billing_budget", "documind"), "display_name")
        rules = re.findall(r'threshold_percent\s*=\s*([0-9.]+)(?:\s*\n\s*spend_basis\s*=\s*"(\w+)")?', tf)
        mk = self.fork.text("Makefile") or ""
        out.append(f"The checkout: budget.tf's `{name or '?'}`, `BUDGET_AMOUNT ?= {make_default(mk, 'BUDGET_AMOUNT') or '?'}`"
                   " in the Makefile (whole units of the billing account's currency; make up passes it), alerting at "
                   + ", ".join(f"{float(p):.0%}" + (" forecast" if basis == "FORECASTED_SPEND" else "")
                               for p, basis in rules) + " of it. A billing budget alerts and stops nothing.")
        if self.lane:
            billing = self.read("the billing account (gcloud billing projects describe)", lambda: gcloud_json(
                ["gcloud", "billing", "projects", "describe", self.lane.project, "--format=json"]))
            account = str((billing or {}).get("billingAccountName") or "").removeprefix("billingAccounts/") \
                if isinstance(billing, dict) else ""
            budgets = self.read("the budget (gcloud billing budgets list)", lambda: gcloud_json(
                ["gcloud", "billing", "budgets", "list", f"--billing-account={account}", "--format=json"])) \
                if account else None
            if billing is not None and not account:
                out += ["", "On the lane: the project has no billing account linked."]
            mine = next((b for b in budgets or [] if isinstance(b, dict) and b.get("displayName") == name), None)
            if mine:
                amount = ((mine.get("amount") or {}).get("specifiedAmount") or {})
                found = [r.get("thresholdPercent") for r in mine.get("thresholdRules") or [] if isinstance(r, dict)]
                out += ["", f"On the lane: {amount.get('units', '?')} {amount.get('currencyCode', '')}".rstrip()
                        + f" a month, alerting at {', '.join(pct(p) for p in found) or 'no threshold'}."]
            elif budgets is not None:
                out += ["", f"On the lane: the billing account holds no budget named `{name}`."]
        return out + [""]

    def state(self) -> list:
        out = ["## State bucket", ""]
        backend = self.fork.json("terraform/.terraform/terraform.tfstate")
        config = ((backend or {}).get("backend") or {}).get("config") or {} if isinstance(backend, dict) else {}
        mk = self.fork.text("Makefile") or ""
        project = self.lane.project if self.lane else "<project>"
        bucket = config.get("bucket") or (make_default(mk, "TFSTATE_BUCKET") or "").replace("$(PROJECT)", project)
        prefix = config.get("prefix") or (make_default(mk, "TFSTATE_PREFIX") or "").replace("$(PROJECT)", project)
        source = ("terraform/.terraform/terraform.tfstate, the backend make plan initialised" if config.get("bucket")
                  else "the Makefile's TFSTATE_BUCKET and TFSTATE_PREFIX defaults")
        out.append(f"Terraform keeps the lane's state in `gs://{bucket}/{prefix}/default.tfstate` ({source}). make plan, "
                   "make up and make down read it; without it, Terraform no longer knows what it made.")
        if self.lane and bucket and prefix:
            info = self.read(f"the state bucket (gcloud storage buckets describe gs://{bucket})", lambda: gcloud_json(
                ["gcloud", "storage", "buckets", "describe", f"gs://{bucket}", "--format=json"]))
            obj = self.read("the state object (gcloud storage objects describe)", lambda: gcloud_json(
                ["gcloud", "storage", "objects", "describe", f"gs://{bucket}/{prefix}/default.tfstate", "--format=json"]))
            if isinstance(info, dict):
                soft = info.get("soft_delete_policy") if isinstance(info.get("soft_delete_policy"), dict) else {}
                out += ["", f"On the lane: the bucket is in {info.get('location', '?')}, versioning "
                        f"{'on' if info.get('versioning_enabled') else 'off'}, public access prevention "
                        f"{info.get('public_access_prevention', '?')}, uniform access "
                        f"{'on' if info.get('uniform_bucket_level_access') else 'off'}"
                        + (f", soft delete {int(soft['retentionDurationSeconds']) // 86400} days"
                           if str(soft.get("retentionDurationSeconds", "")).isdigit() else "") + "."]
            if isinstance(obj, dict):
                out.append(f"The state object: {obj.get('size', '?')} bytes, updated {obj.get('update_time', '?')}.")
        return out + [""]

    def text(self, written: str) -> str:
        lane = self.lane
        body = [self.policies(), self.night_job(), self.floors(), self.revisions(), self.trust(), self.budget(),
                self.state()]
        head = [f"# Handover: DocuMind on {lane.project}" if lane else "# Handover: DocuMind, this checkout", "",
                f"Written by `make handover` (commands/capstone_check.py handover) at {written}, from this checkout"
                + (f" and the lane `{lane.project}` in {lane.region} (the GPU services in {lane.slm_region})" if lane
                   else "; PROJECT= adds what the lane shows") + ". It read, and changed nothing. Each section gives "
                "what the checkout states, then what the lane shows; where the two differ, the lane is what runs. "
                "make handover writes the file whole each time: notes of your own belong in RUNBOOK.md, whose "
                f"template is {TEMPLATES}/RUNBOOK.md.", ""]
        tail = ["## Not read", ""] + ([f"- {line}" for line in self.unread] or
                                      ["- nothing" if lane else "- the lane: no PROJECT was given"])
        return "\n".join(head + [line for section in body for line in section] + tail) + "\n"


def cmd_handover(a) -> int:
    root, lane = fork_root(a.fork), lane_of(a)
    fork = Fork(root, *((lane.project, lane.region, lane.number) if lane else ()))
    out = Path(a.out).expanduser().resolve() if a.out else root / "HANDOVER.md"
    handover = Handover(fork, lane)
    text = handover.text(release.stamp(release.now()))
    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_name(out.name + ".part")
    with open(part, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(part, out)
    print(f">> handover: {out}" + (f", from this checkout and the lane {lane.project}" if lane else
                                   ", from this checkout only (PROJECT= adds the lane)"))
    if handover.unread:
        print(f">> {plural(len(handover.unread), 'lane read')} failed, each listed under Not read:")
        for line in handover.unread:
            say("   - ", line)
        return INCOMPLETE
    return 0


# ---------------------------------------------------------------- the selftest

def _pdf(pages: int, packed: bool) -> bytes:
    """A PDF's skeleton with a page tree of `pages` leaves; packed puts the tree in a Flate object stream, as PDF 1.5
    writers do. Enough for pdf_pages(), not for a reader."""
    tree = (f"<< /Type /Pages /Kids [{' '.join(f'{3 + i} 0 R' for i in range(pages))}] /Count {pages} "
            "/Resources << /Font << >> >> >>").encode()
    leaves = b"".join(b"<< /Type /Page /Parent 2 0 R >>\n" for _ in range(pages))
    if not packed:
        return b"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n2 0 obj " + tree + b" endobj\n" + leaves
    body = zlib.compress(tree + b"\n" + leaves)
    return (b"%PDF-1.5\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n9 0 obj << /Type /ObjStm /Filter "
            b"/FlateDecode /Length " + str(len(body)).encode() + b" >>\nstream\n" + body + b"\nendstream\nendobj\n")


def selftest() -> int:
    """The rules on hand-made documents, records and PDFs: no fork, no lane."""
    arch = ("# Architecture\n\n## What we rejected\n\n- GKE Autopilot: our duty cycle is 4%, and Cloud Run bills only the\n"
            "  requests; above 74% we would move.\n- Pinecone\n\n| Option | Why not |\n|---|---|\n| BigQuery vector "
            "search | its p95 missed our 3 s promise at 10x |\n\n### Fine-tuning first\nThe golden set did not show a "
            "gap that prompts could not close.\n\n## Request path\n- browser to documind-ui\n")
    options = rejected_options(arch)
    assert len(options) == 4 and [words(o) >= REASON_WORDS for o in options] == [True, False, True, True], options
    assert rejected_options("# A\n\n## Choices\n- one\n") is None
    cost = ("Dated 2026-11-20, at USD_INR = 85.\n\n| Queries a month | Rupees | Dollars |\n|---|---|---|\n"
            "| 1k | Rs 450 | $5.29 |\n| 10k | Rs 4,500 | $52.94 |\n| 1 lakh | Rs 45,000 | $529.41 |\n")
    assert cost_model(cost)[1] == [], cost_model(cost)
    lacks = cost_model(cost.replace("Dated 2026-11-20, ", "").replace("| 10k", "| ten"))[1]
    assert len(lacks) == 2 and lacks[0].startswith("COST-MODEL.md does not name 10k ") and "no date" in lacks[1], lacks
    assert [name_of(o) for o in options] == ["GKE Autopilot", "Pinecone", "BigQuery vector search",
                                             "Fine-tuning first"], options
    modes = ("# Failure modes\n\n## Pinned traffic\nSymptom: the change never serves.\n`make gotcha-drill "
             "ID=pinned-traffic`\n\n## Poison upload\n**Symptom:** the queue pages an hour later.\n```bash\n$ make "
             "gotcha-drill ID=poison-upload LIVE=1\n```\n\n## A held fault\n- Symptom - every turn answers 500\n"
             "`FAULT=model HOLD=1 bash commands/incident-drill.sh`\n\n## Untested\nSymptom: something.\n")
    entries = failure_modes(modes)
    assert [(t, s, len(c)) for t, s, c in entries] == [("Pinned traffic", True, 1), ("Poison upload", True, 1),
                                                       ("A held fault", True, 1), ("Untested", True, 0)], entries
    targets, files = {"gotcha-drill", "gotchas", "poison"}, {"commands/incident-drill.sh"}
    registry = {"pinned-traffic": {"drill": {"offline": {"marker": "m"}, "live": None}},
                "poison-upload": {"drill": {"offline": None, "live": {"run": "make poison"}}}}

    def why(command: str) -> str:
        return unresolved(command, targets, files.__contains__, registry)
    assert [why(c) for _, _, cs in entries for c in cs] == ["", "", ""]
    assert "no offline drill" in why("make gotcha-drill ID=poison-upload") and "LIVE=1" in why(
        "make gotcha-drill ID=poison-upload")
    assert "no live drill" in why("make gotcha-drill ID=pinned-traffic LIVE=1")
    assert "not in ops/gotchas.json" in why("make gotcha-drill ID=nope") and "no ID=" in why("make gotcha-drill")
    assert "does not reproduce" in why("make gotchas ID=pinned-traffic") and "no flood" in why("make flood")
    assert why("PROJECT=x make poison") == "" and "holds no commands/x.sh" in why("bash commands/x.sh")
    assert rule_targets("A ?= 1\nB := 2\n.PHONY: x\nx: y\n\t@echo a: b\ny z:\n# c: d\n") == {"x", "y", "z"}
    assert text_pages("one\ftwo\fthree") == 3 and text_pages("") == 1
    assert declared_pages("<!--\nsource: x\npages: 29\n-->\n# T\f") == 29 and declared_pages("# T") is None
    assert pdf_pages(_pdf(3, False)) == 3 and pdf_pages(_pdf(31, True)) == 31 and pdf_pages(b"not a pdf") is None
    assert "--iap" in shell_command("x\ngcloud run deploy documind-ui \\\n  --region=r \\\n  --iap \\\n  --cpu=2\ny",
                                    "gcloud run deploy documind-ui").split()

    def run(serving: str, candidate: str, version=None, **extra) -> dict:
        return {"project": "p", "region": "r", "serving": serving, "candidate": candidate,
                "version": {"git_sha": "abc1234"} if version is None else version, "finished": "t", **extra}
    good, bad, fix = "documind-api-00041-kel", "documind-api-00042-typ", "documind-api-00043-fix"
    promote, back = [run(good, bad), run(bad, bad)], [run(bad, bad), run(good, bad)]
    assert rollback(promote) is None and rollback(back) == (back[0], back[1])
    assert rollback([run(fix, ""), run(good, "")]) is not None                  # older, with the tag removed
    assert rollback([run(bad, bad), run(good, bad, version={"error": "HTTP 403"})]) is None
    assert rollback([run(bad, bad, serving_after=good), run(good, bad)]) is None
    assert lane_smokes({"ran": {"smoke": 0, "smoke-chat": 0, "smoke-media": 1}, "version": {}}) == [("chat",
                                                                                                    "smoke-chat")]
    assert lane_smokes({"ran": {"smoke": 0}, "version": {"retrieval_graph": "auto"}}) == [("graph", "smoke")]
    report = {"rows": 65, "scores": {"isolation_403_rate": 1.0}, "thresholds": {}, "failed": [],
              "judged": ["isolation_403_rate"], "isolation": [],
              "records": [{"shape": "isolation"}] * 2 + [{"id": "own-01", "tenant": "t", "pass": True,
                                                          "cites": [{"source_uri": "gs://b-uploads/t/manual.md"}]}]}
    assert is_report(report) and isolation_asked(report) == 2 and outsider_refused(report)
    assert not outsider_refused(dict(report, scores={"isolation_403_rate": 0.5}, isolation=["iso-01: got 200"]))
    assert cited(report["records"], "t", {"manual"}) == "own-01 cited manual.md" and not cited(report["records"], "u",
                                                                                                {"manual"})
    print(f"capstone_check selftest: ARCHITECTURE.md's rejected options (list, table, sub-section; a bare name is not "
          f"argued), COST-MODEL.md's volumes, amounts, date and rate, FAILURE-MODES.md's entries and every way a "
          f"command resolves or does not, pages from text and from a PDF's page tree (plain and packed), a rollback "
          f"told from a promote, the lane smokes and the outsider's 403, each on hand-made input")
    return 0


# ---------------------------------------------------------------- the command line

def build_parser() -> argparse.ArgumentParser:
    lines = __doc__.splitlines()
    ap = argparse.ArgumentParser(prog="capstone_check.py", description=lines[0], epilog="\n".join(lines[2:]),
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="the rules on hand-made input, no fork and no lane")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--fork", default="", help="the fork's checkout (default: the kit this file is in; make: FORK, .)")
    # The lane only when asked for: every lesson's shell exports PROJECT, and on 22 October 2026 that turned the offline
    # check of the canned fork into a read of the lane, which failed components 1, 2, 4 and 8.
    common.add_argument("--project", default="",
                        help="the lane's project id (make: PROJECT= on its command line): adds the lane's reads; none, "
                             "the fork alone, whatever PROJECT the shell exports")
    common.add_argument("--region", default=os.environ.get("REGION") or "", help="the region documind-api runs in")
    common.add_argument("--slm-region", default=os.environ.get("SLM_REGION") or "",
                        help=f"the region of the GPU services (SLM_REGION; default {release.SLM_REGION_DEFAULT})")
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("check", parents=[common], help="PASS or FAIL for each of the eight components (make capstone-check)")
    c.set_defaults(fn=cmd_check)
    h = sub.add_parser("handover", parents=[common], help="HANDOVER.md, from the checkout and the lane (make handover)")
    h.add_argument("--out", default="", help="where to write it (default: HANDOVER.md in the fork)")
    h.set_defaults(fn=cmd_handover)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.cmd:
        ap.error("name check or handover, or pass --selftest")
    try:
        return int(a.fn(a) or 0)
    except STOPS as e:
        sys.stdout.flush()
        print(f"STOP: {e}", file=sys.stderr)
        return STOPPED


if __name__ == "__main__":
    sys.exit(main())
