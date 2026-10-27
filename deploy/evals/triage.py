#!/usr/bin/env python3
"""Read the failures first (workshop lesson 4.9): a saved live eval's failing rows as the gate saw them, then the eight
causes the kit names, then your own labels counted by cause.

    python deploy/evals/triage.py evals/reports/live.json                  # the failing rows, as the gate saw them
    python deploy/evals/triage.py evals/reports/live.json --template FILE  # a sheet to fill, one line a failing row
    python deploy/evals/triage.py evals/reports/live.json --classes        # the eight causes, and the kit's reading
    python deploy/evals/triage.py evals/reports/live.json --labels FILE    # your filled sheet, counted by cause
    make triage REPORT=evals/reports/live.json   [TEMPLATE=FILE | CLASSES=1 | LABELS=FILE]

THE INPUT is one or more run_eval.py --report files (make eval-live REPORT=...): the live revision's, a candidate's, or
both, read together, each row tagged with its report's name (the file's stem). A failing row is a record the gate did
not pass - a refusal, a missing figure, an invalid citation, a leak, a non-200 - and each line of the report's isolation
list, an outsider who was not refused (check_isolation()'s leg), is a failing row of its own. The question and what the
row expects come from golden.jsonl; what the gate saw comes from the record: its verdict (why), the answer it kept (the
first 600 characters, W2-A) and the citations, with the report's leak and stale lists, because live() writes one why a
row and a later check can overwrite an earlier one. A report written with DOCUMIND_EVAL_PASSAGES=1 carries more: the
pool's size, each must_retrieve anchor found or not in it, each quote checked against the passage it cites
(run_eval.quote_check()). Without it, retrieval and omission look the same from here.

OPEN CODING FIRST. With no flag, the failing rows are printed and nothing else: no cause, no suggestion. Write a
one-line note on ten of them before you read the causes, so the causes do not write the notes for you. --template FILE
writes the rows to a sheet (CSV: the row, the verdict, what was said, the evidence, then an empty note and an empty
class); it never overwrites a file.

THE EIGHT CAUSES (--classes), gap task S2's rag taxonomy: retrieval, version, omission, unsupported, overreach,
isolation, infra and row, each with the lever that fixes it, the workshop lessons that pull that lever, and what can
catch it - and what a report can tell. The evidence decides some causes: an outsider's 200 or another tenant's figure is
isolation, a 500 is infra, an answered unanswerable row is overreach, a retired figure is version. Retrieval and
omission it tells apart only with the pool read. Unsupported it can only hint at - a quote absent from its pool, a quote
the service substituted, an answer with no citation - and the judge or a person decides. Row it cannot see at all: a
wrong golden row reads, from its own verdict, exactly like a wrong answer, so that cause is only ever a person's label.
For each failing row --classes prints the kit's reading and its reason, or why there is none: evidence, never an answer
key.

YOUR LABELS (--labels FILE): the sheet, filled in, one cause a row from the eight, or none beside a note. An unknown
cause, a row that is not a failing row of these reports, or one row twice is refused (exit 2). It prints each cause's
count with its lever, its lessons and what can catch it, the rows noted but not classed, and where the kit had a
reading, how often yours matched it, with every difference.

Standard library only, offline, Rs 0: it reads files and asks nothing. TAXONOMIES holds the causes by name: another
lesson's classes (gap task R5's for agent hand-offs) are another entry, read through the same table.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_eval  # noqa: E402  - the golden rows, and judge_citations()'s tenant check for a citation

# The causes: (name, what it means, the lever, the workshop lessons that pull it, what can catch it, what a report can
# tell). The lessons are the manifest's; the order is the order --classes prints them in.
TAXONOMIES = {
    "rag": (
        ("retrieval", "no must_retrieve anchor reached the pool: the passage that answers was never read",
         "retrieval's depth, the hybrid leg, the reranker, the query rewrite", "2.2-2.3, 2.5",
         "must_retrieve_recall with DOCUMIND_EVAL_PASSAGES=1, an [info] line and never a threshold",
         "only with the pool read: no anchor in it"),
        ("version", "a retired version was cited, or its figure stated",
         "the ledger's versions: publish, retire, retrieve current only", "1.7",
         "the gate: a version row's must_not_contain blocks on its own, and citation_valid_rate checks the version",
         "yes: a stale figure, or a citation the ledger does not list as current"),
        ("omission", "the pool held the answer, and the reply left it out or refused",
         "packing and the prompt", "3.3-3.5",
         "the gate's must_contain and answerable_rate fail the row; only the pool tells it from retrieval",
         "only with the pool read: an anchor in it beside a refusal or a missing figure"),
        ("unsupported", "the answer says what its context does not",
         "quote checks and the judge", "3.6, 4.5",
         "the judge, which advises; quote_passage_rate, an [info] line; no gate rule reads a claim",
         "a hint only: a quote absent from its pool or substituted, or no citation"),
        ("overreach", "an answer to a row the corpus cannot answer",
         "the refusal rule", "3.5",
         "the gate: refusal_rate",
         "yes: answered, should refuse"),
        ("isolation", "another tenant's figure or passage, or a non-member who was not refused",
         "the tenant filter and the roster", "4.6-4.7",
         "the gate: isolation_403_rate, citation_valid_rate, and the must_not_contain stop",
         "yes: a leak, another tenant's citation, an outsider's non-403"),
        ("infra", "a non-200 or a malformed body: the service failed, not the answer",
         "the service's retries, timeouts and quota, and the lane's roster", "3.7",
         "the gate: request_success_rate, which must be 1.00",
         "yes: the status, or the body"),
        ("row", "the golden row or the gate's rule is wrong",
         "the golden set's own checks", "4.1",
         "only a person: make eval proves a row could fail, never that it is right",
         "no: a person's label"),
    ),
}
COLUMNS = ("report", "id", "leg", "shape", "tenant", "verdict", "said", "evidence", "note", "class")


class Refused(Exception):
    """A file this tool cannot use, or labels it will not count: exit 2."""


# ------------------------------------------------------------------ reading the reports
def load_reports(paths: list[str]) -> list[tuple[str, dict]]:
    """[(name, report)]: each a run_eval.py --report file, named by its file's stem (twice the same stem gets #2)."""
    out, names = [], set()
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            raise Refused(f"{path}: not readable as JSON ({e})")
        if not (isinstance(data, dict) and isinstance(data.get("records"), list)):
            raise Refused(f"{path}: not a run_eval.py --report file (it has no records): make eval-live REPORT=... "
                          "writes one")
        name = os.path.splitext(os.path.basename(path))[0]
        base, n = name, 2
        while name in names:
            name, n = f"{base}#{n}", n + 1
        names.add(name)
        out.append((name, data))
    return out


def _ids(lines) -> set[str]:
    """The row ids of a report's leaks, stale or isolation list: each line starts '{id}: '."""
    return {str(line).split(":", 1)[0] for line in lines or []}


def failures(reports: list[tuple[str, dict]], golden: list[dict] | None = None) -> list[dict]:
    """Every failing row of every report, in the reports' order: the records the gate did not pass, then each outsider
    who was not refused. Each carries its report's name, its leg (member or outsider), the record, the golden row (None
    when golden.jsonl no longer has it), and the report's own leak and stale verdicts for it."""
    by_id = {r["id"]: r for r in (golden if golden is not None else run_eval.load_golden())}
    out = []
    for name, rep in reports:
        leaks, stale = _ids(rep.get("leaks")), _ids(rep.get("stale"))
        for rec in rep["records"]:
            if isinstance(rec, dict) and rec.get("id") and not rec.get("pass"):
                out.append({"report": name, "id": rec["id"], "leg": "member", "record": rec,
                            "row": by_id.get(rec["id"]), "leak": rec["id"] in leaks, "stale": rec["id"] in stale})
        for line in rep.get("isolation") or []:
            rid, _, said = str(line).partition(": ")
            row = by_id.get(rid)
            out.append({"report": name, "id": rid, "leg": "outsider", "row": row, "leak": False, "stale": False,
                        "record": {"id": rid, "shape": row["shape"] if row else "isolation",
                                   "tenant": row["tenant"] if row else "?", "outcome": "ok", "why": said}})
    return out


def _flat(text, width: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= width else text[: width - 3] + "..."


def evidence(f: dict) -> str:
    """One line of what the report holds on a failing row: the status, the reply's verdict, its citations, the pool."""
    rec = f["record"]
    if f["leg"] == "outsider":
        return "asked as the outsider (check_isolation): " + rec["why"]
    parts = [f"HTTP {rec.get('status')}"]
    if rec.get("outcome") == "ok":
        parts.append(f"answerable {str(rec.get('answerable')).lower()}, confidence {rec.get('confidence')}")
        cites = rec.get("cites") or []
        if cites:
            parts.append(f"{len(cites)} citation(s): " + ", ".join(str(c.get("chunk_id")) for c in cites[:3]) +
                         (" ..." if len(cites) > 3 else ""))
        else:
            parts.append("no citation")
        if "pool" in rec:
            pool = rec.get("pool")
            anchors = rec.get("anchors") or {}
            parts.append("the pool could not be read" if pool is None else
                         f"pool {pool}" + (": " + ", ".join(f"{a} {'yes' if ok else 'no'}" for a, ok in anchors.items())
                                           if anchors else ""))
            checks = [c.get("check") for c in cites if c.get("check")]
            if checks:
                parts.append("quotes " + ", ".join(f"{k} {checks.count(k)}" for k in run_eval.QUOTE_VERDICTS
                                                   if k in checks))
    if f["leak"]:
        parts.append("in the report's leaks")
    if f["stale"]:
        parts.append("in the report's stale list")
    return "; ".join(parts)


# ------------------------------------------------------------------ the kit's reading
def reading(f: dict) -> tuple[str | None, str]:
    """(cause, reason): the cause the report's evidence decides, or (None, why it does not). Evidence, never a key."""
    rec, row = f["record"], f["row"]
    why = rec.get("why") or ""
    if f["leg"] == "outsider":
        return "isolation", "a non-member was not refused: the roster's leg of the isolation gate"
    if rec.get("outcome") in ("error", "malformed"):
        return "infra", f"the service failed: {why}"
    if rec.get("outcome") == "denied":
        return "infra", f"the eval identity itself was refused ({why}): is it on the tenant's roster (make roster)?"
    if f["stale"]:
        return "version", "a version row stated a figure only a retired version holds"
    if "a version the ledger does not list as current" in why:
        return "version", "a citation names a version the ledger does not list as current"
    if f["leak"]:
        return "isolation", "the answer held a figure that is in another tenant's corpus and not this one's"
    tenant_row = row or {"tenant": rec.get("tenant", "")}
    if rec.get("cites") and not run_eval.judge_citations(tenant_row, rec["cites"], None, {}, "")[0]:
        return "isolation", "a citation names another tenant's chunk or folder"
    if row is None:
        return None, "golden.jsonl no longer has this row"
    if not row["answerable"]:
        if why == "answered, should refuse":
            return "overreach", "the corpus cannot answer this row, and the reply answered it"
        return None, "the evidence does not decide it"
    anchors = rec.get("anchors")
    if anchors is None:
        return None, ("the pool could not be read again, so retrieval and omission look the same" if "pool" in rec else
                      "no pool was read: make eval-live with DOCUMIND_EVAL_PASSAGES=1 tells retrieval from omission")
    if not anchors:
        return None, "the row names no must_retrieve anchor to look for in the pool"
    found = [a for a, ok in anchors.items() if ok]
    if not found:
        return "retrieval", f"no must_retrieve anchor ({', '.join(anchors)}) reached the pool"
    checks = [c.get("check") for c in rec.get("cites") or [] if c.get("check")]
    if why == "refused":
        return "omission", f"{', '.join(found)} reached the pool, and the reply refused"
    if why == "answered without a citation":
        return "unsupported", "answered with no citation: nothing ties the answer to the pool (a hint: read it)"
    if why.startswith("answered without ["):
        bad = sorted({c for c in checks if c in ("absent", "substituted")})
        if bad:
            return "unsupported", (f"{', '.join(found)} reached the pool, the figure is missing and a quote is "
                                   f"{' or '.join(bad)} (a hint: read it)")
        return "omission", f"{', '.join(found)} reached the pool, and the answer left out {row.get('must_contain')}"
    return None, "the evidence does not decide it"


# ------------------------------------------------------------------ what is printed
def tag(f: dict, many: bool) -> str:
    """The row as printed: its id, after its report's name when there are several reports."""
    return (f"[{f['report']}] " if many else "") + f["id"]


def _width(fs: list[dict], many: bool) -> int:
    return max((len(tag(f, many)) for f in fs), default=0)


def _who(f: dict, many: bool, width: int) -> str:
    """The row's tag padded to `width`, then its leg: asked as the member, or as the outsider (check_isolation)."""
    return f"{tag(f, many):{width}}  {f['leg']:8}"


def show_rows(fs: list[dict], many: bool) -> list[str]:
    lines, w = [], _width(fs, many)
    for f in fs:
        rec, row = f["record"], f["row"] or {}
        lines.append(f"  {_who(f, many, w)}  {rec.get('shape', '?'):9} {rec.get('tenant', '?'):7} "
                     f"{rec.get('why') or 'failed'}")
        lines.append(f"      asked     {row.get('question', '(not in golden.jsonl)')}")
        expect = ([f"must_contain {', '.join(row['must_contain'])}"] if row.get("must_contain") else []) + \
                 ([f"must_not_contain {', '.join(row['must_not_contain'])}"] if row.get("must_not_contain") else []) + \
                 ([f"must_retrieve {', '.join(row['must_retrieve'])}"] if row.get("must_retrieve") else [])
        lines.append(f"      expected  {'an answer' if row.get('answerable') else 'a refusal'}" +
                     (f": {'; '.join(expect)}" if expect else "") if row else "      expected  -")
        if f["leg"] == "member" and rec.get("outcome") == "ok":
            said = _flat(rec.get("answer"), 220) or "(no answer kept: a report from before W2-A)"
            lines.append(f"      said      {said}")
            for n, c in enumerate(rec.get("cites") or [], 1):
                check = f"  quote {c['check']}" if c.get("check") else ""
                lines.append(f"      [{n}]       {c.get('chunk_id')}  {_flat(c.get('quote'), 90)!r}{check}")
        lines.append(f"      evidence  {evidence(f)}")
    return lines


def show_classes(fs: list[dict], taxonomy: tuple, many: bool) -> list[str]:
    lines = []
    for name, means, lever, lessons, catcher, tells in taxonomy:
        lines += [f"  {name:12} {means}", f"  {'':12} lever: {lever} ({lessons})", f"  {'':12} caught by: {catcher}",
                  f"  {'':12} from a report: {tells}", ""]
    lines.append("  the kit's reading of each failing row - evidence, never an answer key:")
    w = _width(fs, many)
    for f in fs:
        cause, reason = reading(f)
        lines.append(f"    {_who(f, many, w)}  {cause or '-':12} {reason}")
    return lines


def write_template(fs: list[dict], path: str) -> None:
    if os.path.exists(path):
        raise Refused(f"{path} exists: the template never overwrites a sheet - name another file")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for x in fs:
            rec = x["record"]
            w.writerow([x["report"], x["id"], x["leg"], rec.get("shape", ""), rec.get("tenant", ""), rec.get("why", ""),
                        _flat(rec.get("answer"), 200), evidence(x), "", ""])


def read_labels(path: str, fs: list[dict], taxonomy: tuple) -> list[tuple[dict, str, str]]:
    """[(the failing row, cause or "", note)] from a filled sheet. Refused: an unknown cause, a row that is not a
    failing row of these reports, a row twice, a sheet with no id or class column."""
    names = {c[0] for c in taxonomy}
    reports = sorted({f["report"] for f in fs})
    by_key = {(f["report"], f["id"], f["leg"]): f for f in fs}
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            sheet = list(csv.DictReader(f))
    except OSError as e:
        raise Refused(f"{path}: cannot read it ({e.strerror or e})")
    if not sheet or "id" not in sheet[0] or "class" not in sheet[0]:
        raise Refused(f"{path}: no id and class columns - --template writes the sheet to fill")
    out, seen, bad = [], set(), []
    for n, line in enumerate(sheet, 2):
        rid = (line.get("id") or "").strip()
        if not rid:
            continue
        report = (line.get("report") or "").strip() or (reports[0] if len(reports) == 1 else "")
        leg = (line.get("leg") or "").strip() or "member"
        cause = (line.get("class") or "").strip().lower()
        key = (report, rid, leg)
        if key not in by_key:
            where = f", {report}" if report else ""
            bad.append(f"line {n}: {rid} ({leg}{where}) is not a failing row of these reports")
        elif key in seen:
            bad.append(f"line {n}: {rid} ({leg}) is labelled twice")
        elif cause and cause not in names:
            bad.append(f"line {n}: {rid}: {cause!r} is not one of the causes: {', '.join(c[0] for c in taxonomy)}")
        else:
            seen.add(key)
            out.append((by_key[key], cause, (line.get("note") or "").strip()))
    if bad:
        raise Refused("; ".join(bad))
    return out


def show_counts(labels: list[tuple[dict, str, str]], fs: list[dict], taxonomy: tuple, many: bool) -> list[str]:
    classed = [(f, c) for f, c, _ in labels if c]
    noted = [f for f, c, note in labels if not c and note]
    lines = [f"  {len(fs)} failing rows; {len(classed)} classed, {len(noted)} noted only, "
             f"{len(fs) - len(classed) - len(noted)} untouched", "",
             f"  {'cause':12} {'rows':>4}  lever (lessons) - what can catch it"]
    for name, _, lever, lessons, catcher, _ in taxonomy:
        lines.append(f"  {name:12} {sum(c == name for _, c in classed):4}  {lever} ({lessons}) - {catcher}")
    if noted:
        named = [tag(f, many) + (" (outsider)" if f["leg"] == "outsider" else "") for f in noted]
        lines.append(f"\n  noted, not classed: {', '.join(named)}")
    read = [(f, c, reading(f)) for f, c in classed]
    decided = [(f, c, k) for f, c, (k, _) in read if k]
    if decided:
        same = sum(c == k for _, c, k in decided)
        lines.append(f"\n  the kit's reading, where the evidence decided one: yours matched on {same} of "
                     f"{len(decided)}")
        w = _width(fs, many)
        for f, c, (k, reason) in read:
            if k and c != k:
                lines.append(f"    {_who(f, many, w)}  yours {c:12} the kit's {k:12} {reason}")
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("reports", nargs="+", metavar="REPORT",
                    help="run_eval.py --report files (make eval-live REPORT=...)")
    act = ap.add_mutually_exclusive_group()
    act.add_argument("--template", metavar="FILE", help="write the failing rows to a sheet to fill (never overwrites)")
    act.add_argument("--classes", action="store_true",
                     help="the eight causes, and the kit's reading of each failing row")
    act.add_argument("--labels", metavar="FILE", help="a filled sheet: the causes counted, with their levers")
    ap.add_argument("--taxonomy", default="rag", choices=sorted(TAXONOMIES), help="the causes to read by (default rag)")
    a = ap.parse_args(argv)
    taxonomy = TAXONOMIES[a.taxonomy]
    try:
        reports = load_reports(a.reports)
        fs = failures(reports)
        many = len(reports) > 1
        names = ", ".join(n for n, _ in reports)
        if a.template:
            write_template(fs, a.template)
            print(f"  {len(fs)} failing rows of {names} written to {a.template}: write a one-line note on ten of them, "
                  "then read the causes (--classes) and fill the class column")
            return 0
        if a.labels:
            labels = read_labels(a.labels, fs, taxonomy)
            print(f"== triage: your labels, counted by cause ({names}) ==")
            print("\n".join(show_counts(labels, fs, taxonomy, many)))
            return 0
    except Refused as e:
        print(f"triage: {e}", file=sys.stderr)
        return 2
    if not fs:
        print(f"== triage: {names} ==\n  no failing row: every record passed and every outsider was refused")
        return 0
    if a.classes:
        print(f"== triage: the eight causes (taxonomy {a.taxonomy}), and the kit's reading of {len(fs)} "
              "failing rows ==")
        print("\n".join(show_classes(fs, taxonomy, many)))
        return 0
    print(f"== triage: {len(fs)} failing rows of {names}, as the gate saw them ==")
    print("\n".join(show_rows(fs, many)))
    print(f"\n  Before you read the causes: a one-line note on ten of these rows, in your own words. --template FILE "
          f"writes them to a sheet; --classes prints the causes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
