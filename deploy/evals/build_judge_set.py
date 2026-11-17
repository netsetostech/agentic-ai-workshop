#!/usr/bin/env python3
"""The judge set (workshop lesson 4.5): about twenty answers frozen from a judge capture, and the label sheets people
fill on them. Standard library only, Rs 0.

    python evals/build_judge_set.py --freeze evals/reports/judge45_rows.jsonl [flash-lite=evals/reports/cand_rows.jsonl]
                                    [--rows 20] [--set evals/judge_set.json] [--force]
    python evals/build_judge_set.py --emit evals/reports/judge_labels.csv [--reader you]     # make label-sheet
    python evals/build_judge_set.py --check evals/reports/judge_labels.csv

A CAPTURE is what judge.py --save-rows writes: one line per row the judge rated, the row as judge.py holds it (the
golden row, the answer, whether the API said it could answer, and the context the judge read: the cited chunks in
full), with its ratings. ARM=FILE names the revision that answered, for a capture of a candidate; a bare FILE is the
live revision's ("live").

--freeze picks --rows rows, one per question, and writes them to --set (evals/judge_set.json) in judge.py's collection
shape, so judge.py --reuse evals/judge_set.json --no-enrich (make judge-frozen) rates exactly these rows. It keeps no
judge score, and it picks without one: rows chosen by the judge's own verdict would bias every rate measured against
it. The rules are the gap plan's (S1), scaled to twenty:

  - A third of the rows should fail. The kit's computed check finds the natural failures: the gate's figure and
    refusal rules on the frozen answer (run_eval.contains), without the citation checks, which need the lane - an
    answerable row refused, answered without its figure, an unanswerable row answered, or a figure that must not
    appear. Up to a third are picked, one shape after another.
  - A refusal claims nothing, so it is grounded, and a missing figure is a short answer rather than an unsupported
    one: natural failures seldom fail groundedness. So groundedness's third is made up with constructed rows. Each
    is a copy of an answer that passed, with one sentence its context does not support, cited as if it did. It keeps
    the question's id, says constructed: true and records the sentence (added), so natural and constructed rows are
    counted apart. The sheet a person labels does not say which is which.
  - The rest are answers that passed, one shape after another, so refusals and isolation rows are in the set too.
  - Within a shape the order is a hash of the arm and the id, so the same capture always freezes to the same set.
  - Nothing that names a lane is frozen (a project number or id, a personal mailbox), and a tuned endpoint's path is
    written as "an endpoint": the set ships in a public kit.

--emit writes a blank label sheet (CSV) for one reader: id, reader, groundedness, answers_the_question and note, then
the question, the answer and the context to read by, and row_sha (a hash of the three). Fill yes or no in both label
columns on every row; note is optional. It never overwrites a file: a sheet that exists may hold someone's labels.
--check holds a filled sheet to the frozen set: every row once and no other, labelled on the same answer (row_sha),
yes or no in both columns, one pseudonymous reader id. Exit 1 lists what is wrong; exit 2 is a file that is missing.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_eval import contains  # noqa: E402  - the gate's own matcher: a figure on its own boundaries

KIT_SET = os.path.join(HERE, "judge_set.json")              # the author's frozen set, once it ships with the kit
OWN_SET = os.path.join(HERE, "reports", "judge_set.json")    # a learner's own freeze (lesson 4.5, step 3): git ignores it,
# so a later git pull that brings the author's set never collides with it. The kit's set wins once it is there.
JUDGE_SET = OWN_SET if os.path.isfile(OWN_SET) and not os.path.isfile(KIT_SET) else KIT_SET
ROWS = 20
RUBRICS = ("groundedness", "answers_the_question")
SHEET_FIELDS = ("id", "reader", "groundedness", "answers_the_question", "note", "question", "answer", "context", "row_sha")
LABELS = ("yes", "no")
READER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,15}$")         # a pseudonymous id (you, L1, L2), never a name or an email
SHAPES = ("lookup", "join", "refusal", "isolation", "version")
REFUSED, SHOULD_REFUSE = "refused", "answered, should refuse"   # live()'s words for the two refusal failures
# A frozen row: judge.py's collection shape (status, response, context, cited, model, answerable_said) plus the set's
# own fields (language, arm, computed, constructed, added). No rating: the judge's verdicts live in its own file.
FROZEN = ("id", "shape", "tenant", "language", "arm", "question", "context", "response", "must_contain", "must_not_contain",
          "answerable", "answerable_said", "status", "cited", "model", "computed", "constructed", "added")

GUIDE = (
    "groundedness: yes when every claim in the answer is supported by the context on its row. Read the context, not "
    "what you know: a true sentence the context does not hold is unsupported. A refusal claims nothing, so it is "
    "grounded. One unsupported sentence makes the row a no.",
    "answers_the_question: yes when the answer gives what the question asks for. When the context does not hold the "
    "answer, saying so is a yes and a guess is a no; when it does hold it, a refusal or half an answer is a no.",
    "note: optional - one line on why, written before you compare with anyone.",
)

# Constructed rows: one sentence that no answer's context supports, and the phrase that must be absent from that row's
# context and answer before the sentence is used (run_eval.contains, so "seven working days" counts as present).
ADDED = (
    ("Requests under this clause are decided within 7 working days of receipt", "7 working days"),
    ("The rule was last revised on 14 February 2025", "14 February 2025"),
    ("It applies equally to contract staff from 1 January 2027", "1 January 2027"),
    ("A copy must also be filed with the regional office within 45 days", "45 days"),
    ("Approval from two senior managers is needed in every case", "two senior managers"),
)
CITE = re.compile(r"\[\d+(?:\s*,\s*\d+)*\]")
SENTENCE_END = re.compile(r"\.(?=\s|$)")
MODEL = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
LANE_MARKS = (   # tools/leakscan.py's, for what a capture can hold: the set ships in the learner kit
    ("a project number in a resource path", re.compile(r"\bprojects/\d{6,}/")),
    ("a project number in a Cloud Run URL", re.compile(r"-\d{9,}\.[a-z0-9-]+\.run\.app")),
    ("a project id", re.compile(r"\bdocumind-ai-(?!YOUR-ID\b|live-)[a-z0-9][a-z0-9-]*")),
    ("a personal mailbox", re.compile(r"[A-Za-z0-9._%+-]+@(?:gmail|googlemail|yahoo|hotmail|outlook|live|icloud|proton|"
                                      r"protonmail|rediffmail)\.[a-z.]+", re.I)),
)


def shown(path: str) -> str:
    try:
        return os.path.relpath(path)
    except ValueError:             # another drive (Windows)
        return path


def row_sha(row: dict) -> str:
    """Twelve hex digits of the question, the context and the answer: a label belongs to the answer it was given on."""
    text = json.dumps([row.get("question") or "", row.get("context") or "", row.get("response") or ""], ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


# ----------------------------------------------------------------------------- freeze
def computed(row: dict) -> str:
    """The gate's figure and refusal rules on one answer, in live()'s words: "pass", or why not. live() also checks
    each citation against the lane's ledger, which a frozen row cannot."""
    text = row.get("response") or ""
    why = ""
    for never in row.get("must_not_contain") or []:
        if contains(text, never):
            why = f"answer contained {never!r}"
    said = bool(row.get("answerable_said"))
    if not row.get("answerable"):
        return SHOULD_REFUSE if said else (why or "pass")
    if not said:
        return REFUSED
    want = row.get("must_contain") or []
    if not all(contains(text, w) for w in want):
        return f"answered without {want}"
    return why or "pass"


def rank(row: dict) -> str:
    return hashlib.sha256(f"{row['arm']}:{row['id']}".encode("utf-8")).hexdigest()


def spread(rows: list[dict], k: int, taken: set[str]) -> list[dict]:
    """Up to k rows, one shape after another (SHAPES' order), each shape's rows in rank order, and one row per
    question: an id in `taken` is skipped, and each row picked joins it."""
    groups: dict[str, list[dict]] = {}
    for r in sorted(rows, key=rank):
        groups.setdefault(r.get("shape") or "", []).append(r)
    order = [s for s in SHAPES if s in groups] + sorted(s for s in groups if s not in SHAPES)
    out: list[dict] = []
    while len(out) < k and any(groups[s] for s in order):
        for s in order:
            while groups[s] and groups[s][0]["id"] in taken:
                groups[s].pop(0)
            if groups[s] and len(out) < k:
                r = groups[s].pop(0)
                out.append(r)
                taken.add(r["id"])
    return out


def add_sentence(response: str, sentence: str) -> tuple[str, str]:
    """(the answer with one sentence added, what was added). It goes after the first sentence that cites and carries
    that citation, so the claim reads as sourced; an answer that cites nothing gets it at the end, uncited."""
    m = CITE.search(response)
    if not m:
        return response.rstrip() + f" {sentence}.", f"{sentence}."
    end = SENTENCE_END.search(response, m.end())
    cut = end.end() if end else len(response.rstrip())
    added = f"{sentence} {m.group(0)}."
    return response[:cut] + " " + added + response[cut:], added


def construct(row: dict, i: int) -> dict | None:
    """A copy of a passing answer with one unsupported sentence, the i-th constructed row (the sentences take turns);
    None when every sentence's phrase is already in the row's context or answer."""
    text = f"{row.get('context') or ''}\n{row.get('response') or ''}"
    for k in range(len(ADDED)):
        sentence, phrase = ADDED[(i + k) % len(ADDED)]
        if contains(text, phrase):
            continue
        new = dict(row)
        new["response"], new["added"] = add_sentence(row["response"], sentence)
        new["constructed"] = True
        new["computed"] = computed(new)
        return new
    return None


def frozen_row(row: dict) -> dict:
    """One row in FROZEN's order, with the lists and texts judge.py's to_frame() reads never null; `added` only on a
    constructed row."""
    out = {k: row.get(k) for k in FROZEN}
    for k in ("must_contain", "must_not_contain", "cited"):
        out[k] = list(out[k] or [])
    for k in ("question", "context", "response"):
        out[k] = out[k] or ""
    if not out["constructed"]:
        del out["added"]
    return out


def lane_marks(row: dict) -> list[str]:
    text = "\n".join(str(row.get(k) or "") for k in ("question", "context", "response", "added", "model"))
    return [what for what, rx in LANE_MARKS if rx.search(text)]


def read_capture(path: str) -> list[dict]:
    """The lines of a judge.py --save-rows file. A --reuse collection (one JSON list, the quotes rather than the
    context the judge read) is refused, with the file to use instead."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if text.lstrip().startswith("["):
        raise ValueError(f"{shown(path)} is a --reuse collection, which holds the quotes, not the context the judge read: "
                         "freeze from the --save-rows file of the same run")
    lines = [json.loads(x) for x in text.splitlines() if x.strip()]
    need = ("id", "question", "response", "answerable", "answerable_said", "ratings")
    bad = [i for i, x in enumerate(lines, 1) if not isinstance(x, dict) or any(k not in x for k in need)]
    if bad:
        raise ValueError(f"{shown(path)}: line {bad[0]} is not a judge.py --save-rows line of a collected row "
                         f"({', '.join(need)})")
    if any(x.get("constructed") for x in lines):
        raise ValueError(f"{shown(path)} rates a frozen set, constructed rows and all: freeze from a capture of the "
                         "lane's own answers, or a constructed row would come back as a natural one")
    return lines


def capture_arg(spec: str) -> tuple[str, str]:
    """ARM=FILE, or FILE for the live revision's capture."""
    arm, sep, path = spec.partition("=")
    if sep and re.match(r"^[a-z][a-z0-9.-]*$", arm) and not os.path.exists(spec):
        return arm, path
    return "live", spec


def freeze(captures: list[tuple[str, list[dict]]], n: int = ROWS) -> tuple[list[dict], dict]:
    """(the frozen rows, sorted by id; what was picked and why). See the module's docstring for the rules."""
    pool, seen = [], set()
    for arm, lines in captures:
        for line in lines:
            if line.get("status", 200) != 200 or not (line.get("response") or "").strip() or (arm, line["id"]) in seen:
                continue
            seen.add((arm, line["id"]))
            row = {k: line[k] for k in FROZEN if k in line}
            row.update(arm=arm, language=line.get("language") or "en", status=200, constructed=False)
            model = str(line.get("model") or "")
            row["model"] = model if MODEL.match(model) else ("an endpoint" if model else None)
            row["computed"] = computed(row)
            pool.append(row)
    want = math.ceil(n / 3)
    taken: set[str] = set()
    natural = spread([r for r in pool if r["computed"] != "pass"], want, taken)
    unsupported = sum(r["computed"] == SHOULD_REFUSE for r in natural)      # an answer to what the corpus cannot answer
    need = max(0, want - unsupported)
    built: list[dict] = []
    sources = [r for r in pool if r["computed"] == "pass" and r.get("answerable") and r.get("answerable_said")]
    for r in spread(sources, len(sources), set(taken)):
        if len(built) >= need:
            break
        c = construct(r, len(built))
        if c:
            built.append(c)
            taken.add(r["id"])
    passing = spread([r for r in pool if r["computed"] == "pass"], n - len(natural) - len(built), taken)
    rows = [frozen_row(r) for r in sorted(natural + built + passing, key=lambda r: r["id"])]
    marks = [f"{r['id']}: {what}" for r in rows for what in lane_marks(r)]
    if marks:
        raise ValueError("refused: the frozen set ships in a public kit, and these rows name a lane - " + "; ".join(marks))
    why = Counter("answered without a figure" if r["computed"].startswith("answered without") else
                  "said what it must not" if r["computed"].startswith("answer contained") else
                  "answered what it should refuse" if r["computed"] == SHOULD_REFUSE else r["computed"] for r in natural)
    return rows, {"pool": len(pool), "want": want, "natural": why, "unsupported": unsupported, "need": need,
                  "built": built, "passing": len(passing), "shapes": Counter(r["shape"] for r in rows)}


def write_set(rows: list[dict], path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
        f.write("\n")


def load_set(path: str = JUDGE_SET) -> list[dict]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{shown(path)}: not found. It is frozen from a judge capture: freeze your own with "
                                "--freeze CAPTURE --set evals/reports/judge_set.json (lesson 4.5, step 3); the "
                                "author's evals/judge_set.json ships with the kit once recorded")
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) and r.get("id") for r in rows):
        raise ValueError(f"{shown(path)} is not a frozen set (a JSON list of rows, each with an id)")
    return rows


# ----------------------------------------------------------------------------- label sheets
def emit(rows: list[dict], path: str, reader: str) -> int:
    if not READER.match(reader):
        print(f"--reader {reader!r}: a pseudonymous id of letters, digits, - and _ (at most 16), never a name or an email")
        return 2
    if os.path.exists(path):
        print(f"{shown(path)} exists and may hold labels: nothing written. Name a new file, or delete this one to start again.")
        return 2
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(SHEET_FIELDS)
        for r in rows:
            w.writerow([r["id"], reader, "", "", "", r.get("question") or "", r.get("response") or "", r.get("context") or "",
                        row_sha(r)])
    print(f"{shown(path)}: {len(rows)} rows for {reader}. On every row write yes or no under groundedness and under "
          "answers_the_question, reading the question, the answer and the context on that row:")
    for line in GUIDE:
        print(f"  {line}")
    print(f"Then: python evals/build_judge_set.py --check {shown(path)}")
    return 0


def load_sheet(path: str) -> tuple[list[str], list[dict]]:
    """(header, rows) of a CSV sheet, with or without a byte-order mark, LF or CRLF. A sheet a spreadsheet saved in its
    own code page is read as cp1252: only the id, reader, label and row_sha columns are checked, and they are ASCII."""
    with open(path, "rb") as f:
        raw = f.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = list(reader)
    return [h.strip() for h in (reader.fieldnames or [])], [{(k or "").strip(): v for k, v in r.items()} for r in rows]


def sheet_errors(header: list[str], sheet: list[dict], frozen: list[dict]) -> list[str]:
    """What keeps a filled sheet from counting: empty when it is complete and labels the frozen rows."""
    missing = [f for f in ("id", "reader", *RUBRICS, "row_sha") if f not in header]
    if missing:
        return [f"the header has no {', '.join(missing)}: not a label sheet (make label-sheet writes one)"]
    by_id = {r["id"]: r for r in frozen}
    ids = Counter((r.get("id") or "").strip() for r in sheet)
    why = [f"{i}: on the sheet {k} times" for i, k in ids.items() if k > 1]
    why += [f"{i}: not on the sheet" for i in by_id if i not in ids]
    readers = sorted({(r.get("reader") or "").strip() for r in sheet})
    if len(readers) > 1:
        why.append(f"one reader per sheet: it names {readers}")
    elif readers and not READER.match(readers[0]):
        why.append(f"reader {readers[0]!r}: a pseudonymous id of letters, digits, - and _ (at most 16), never a name or an email")
    for r in sheet:
        rid = (r.get("id") or "").strip()
        if rid not in by_id:
            why.append(f"{rid or '(no id)'}: not a row of the frozen set")
            continue
        if (r.get("row_sha") or "").strip() != row_sha(by_id[rid]):
            why.append(f"{rid}: labelled on another answer (row_sha {(r.get('row_sha') or '').strip() or '-'}, the frozen "
                       f"row's {row_sha(by_id[rid])}): the sheet was made from another freeze")
        for k in RUBRICS:
            v = (r.get(k) or "").strip()
            if v.lower() not in LABELS:
                why.append(f"{rid}: {k} is {repr(v) if v else 'blank'}, not yes or no")
    return why


def labels_of(sheet: list[dict]) -> dict[str, dict[str, bool]]:
    """{id: {rubric: True for yes}} of a sheet that passes sheet_errors()."""
    return {r["id"].strip(): {k: r[k].strip().lower() == "yes" for k in RUBRICS} for r in sheet}


def check(path: str, frozen: list[dict]) -> int:
    header, sheet = load_sheet(path)
    why = sheet_errors(header, sheet, frozen)
    if why:
        print(f"{shown(path)}: {len(why)} problem(s) against the frozen set's {len(frozen)} rows")
        for w in why[:20]:
            print(f"  {w}")
        if len(why) > 20:
            print(f"  ... and {len(why) - 20} more")
        return 1
    labels = labels_of(sheet)
    counts = "; ".join(f"{k} {sum(v[k] for v in labels.values())} yes, {sum(not v[k] for v in labels.values())} no" for k in RUBRICS)
    notes = sum(bool((r.get("note") or "").strip()) for r in sheet)
    print(f"{shown(path)}: {len(sheet)} rows labelled by {sheet[0]['reader'].strip()} - {counts}; {notes} with a note. "
          "Ready for judge_agree.py.")
    return 0


# ----------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--freeze", nargs="+", metavar="[ARM=]CAPTURE", help="judge.py --save-rows files to pick from")
    g.add_argument("--emit", metavar="SHEET", help="write a blank label sheet (CSV) for one reader")
    g.add_argument("--check", metavar="SHEET", help="hold a filled sheet to the frozen set")
    ap.add_argument("--set", default=JUDGE_SET, help="the frozen rows: what --freeze writes, --emit and --check read")
    ap.add_argument("--rows", type=int, default=ROWS, help=f"--freeze: how many rows (default {ROWS})")
    ap.add_argument("--reader", default="you", help="--emit: the reader's pseudonymous id (default you)")
    ap.add_argument("--force", action="store_true", help="--freeze: replace a frozen set; every sheet labelled on it goes stale")
    a = ap.parse_args(argv)
    try:
        if a.freeze:
            if a.rows < 3:
                print(f"--rows {a.rows}: a set needs at least 3 rows, a third of them failing")
                return 2
            if os.path.exists(a.set) and not a.force:
                print(f"{shown(a.set)} exists: every label sheet and rating on it belongs to its answers. Nothing written; "
                      "--force replaces it, and then every sheet must be labelled again.")
                return 2
            captures = []
            for spec in a.freeze:
                arm, path = capture_arg(spec)
                lines = read_capture(path)
                runs = sorted({str(x.get("run") or "?") for x in lines})
                print(f"  {shown(path)} ({arm}): {len(lines)} rows rated, run {', '.join(runs)}")
                captures.append((arm, lines))
            rows, why = freeze(captures, a.rows)
            write_set(rows, a.set)
            nat = sum(why["natural"].values())
            print(f"  picked {len(rows)} of {why['pool']} answers, one per question, without the judge's ratings:")
            print(f"    {nat} fail the computed check" + (f" ({', '.join(f'{k} {v}' for k, v in sorted(why['natural'].items()))})" if nat else ""))
            print(f"    {len(why['built'])} constructed: one unsupported sentence added to an answer that passed, so "
                  f"groundedness has {len(why['built']) + why['unsupported']} rows expected to fail")
            print(f"    {why['passing']} passing; by shape: " + ", ".join(f"{s} {k}" for s, k in sorted(why["shapes"].items())))
            if nat < why["want"]:
                print(f"  fewer than a third ({why['want']}) fail the computed check: the capture had {nat}. A capture of a "
                      "cheaper candidate (ARM=FILE) adds natural failures.")
            if len(why["built"]) < why["need"]:
                print(f"  only {len(why['built'])} of {why['need']} constructed: too few answers passed, or each already "
                      "holds every sentence's phrase.")
            if len(rows) < a.rows:
                print(f"  only {len(rows)} rows: the captures hold {why['pool']} answers.")
            print(f"  wrote {shown(a.set)}: {len(rows)} rows, no judge score. Read every row before you commit it, the "
                  "constructed ones above all; the labels come after:")
            for r in why["built"]:
                print(f"    {r['id']:8} + {r['added']!r}")
            return 0
        rows = load_set(a.set)
        if a.emit:
            return emit(rows, a.emit, a.reader)
        return check(a.check, rows)
    except (OSError, ValueError) as e:
        print(e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
