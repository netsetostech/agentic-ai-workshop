"""Lesson B.1: Files and JSON: pathlib, json and a JSONL file

The cell below takes four rows of the kit's evals/golden.jsonl (a lookup, a join, a refusal and an isolation row), writes them to ~/basics-b1/golden_sample.jsonl the way the kit writes the real file, and reads them back the way the eval gate does. Then it deletes one comma from a copy of line 1, to show what json.loads says about a broken line.

Run order inside this file:
1. Write four golden rows, read them back (source window 13)

Prerequisites: demo_03_the_venv_what_the_setup_block_built_and_why_the_kit_pins.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


def step_01_write_four_golden_rows_read_them_back(session):
    """Run Write four golden rows, read them back at this checkpoint.

    The cell below takes four rows of the kit's evals/golden.jsonl (a lookup, a join, a refusal and an isolation row), writes them to ~/basics-b1/golden_sample.jsonl the way the kit writes the real file, and reads them back the way the eval gate does. Then it deletes one comma from a copy of line 1, to show what json.loads says about a broken line.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop: writes ~/basics-b1/golden_sample.jsonl.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: wrote ~/basics-b1/golden_sample.jsonl: 875 bytes, 4 lines
    read back: 4 rows, equal to what was written: True
    line 1 on disk: {"id": "lk-01", "shape": "lookup", "question": "What is the per-trip cap on domestic travel reimbursement?", "tenant": "acme", "must_contain": ["40,000"], "must_retrieve": ["EXP-12", "hr_policy_2026"], "answerable": true}
    lk-01: answerable True is a bool, must_contain ['40,000'] is a list
    iso-01 asks zeta what lk-01 asks acme: it must contain ['25,000'], never ['40,000']
    answerable: 3 of 4 | shapes: lookup, join, refusal, isolation
    the line with one comma lost: Expecting ',' delimiter (line 1, column 35)
    """
    import json, warnings
    from pathlib import Path
    warnings.filterwarnings("ignore", category=UserWarning)
    
    ROWS = [   # four rows of the kit's evals/golden.jsonl: a lookup, a join, a refusal and an isolation row (iso-01 without its note)
        {"id": "lk-01", "shape": "lookup", "question": "What is the per-trip cap on domestic travel reimbursement?",
         "tenant": "acme", "must_contain": ["40,000"], "must_retrieve": ["EXP-12", "hr_policy_2026"], "answerable": True},
        {"id": "jn-01", "shape": "join", "question": "If I resign during probation, what notice applies and can I encash leave?",
         "tenant": "acme", "must_contain": ["15", "cannot"], "must_retrieve": ["PB-02", "LV-07"], "answerable": True},
        {"id": "rf-02", "shape": "refusal", "question": "How many casual leave days do I get?",
         "tenant": "acme", "must_contain": [], "must_retrieve": [], "answerable": False},
        {"id": "iso-01", "shape": "isolation", "question": "What is the per-trip cap on travel reimbursement?",
         "tenant": "zeta", "must_contain": ["25,000"], "must_retrieve": ["EXP-12", "hr_policy_zeta_2026"], "answerable": True, "must_not_contain": ["40,000"]},
    ]
    folder = Path.home() / "basics-b1"                         # / joins the parts, on every operating system
    folder.mkdir(exist_ok=True)
    path = folder / "golden_sample.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as f:  # newline="\n": the same bytes on Windows
        for row in ROWS:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")   # one object, one line: the kit's writer
    print(f"wrote ~/{folder.name}/{path.name}: {path.stat().st_size} bytes, {len(ROWS)} lines")
    
    with path.open(encoding="utf-8") as f:
        back = [json.loads(line) for line in f if line.strip()]   # the kit's reader, line for line
    print("read back:", len(back), "rows, equal to what was written:", back == ROWS)
    first = path.read_text(encoding="utf-8").splitlines()[0]
    print("line 1 on disk:", first)
    row = back[0]
    print(f"{row['id']}: answerable {row['answerable']!r} is a {type(row['answerable']).__name__}, "
          f"must_contain {row['must_contain']!r} is a {type(row['must_contain']).__name__}")
    by_id = {r["id"]: r for r in back}
    iso, lk = by_id["iso-01"], by_id["lk-01"]
    print(f"iso-01 asks {iso['tenant']} what lk-01 asks {lk['tenant']}: it must contain {iso['must_contain']}, never {iso['must_not_contain']}")
    print("answerable:", sum(r["answerable"] for r in back), "of", len(back), "| shapes:", ", ".join(r["shape"] for r in back))
    broken = first.replace('"lookup", ', '"lookup" ', 1)        # the same line with one comma lost
    try:
        json.loads(broken)
    except json.JSONDecodeError as e:
        print(f"the line with one comma lost: {e.msg} (line {e.lineno}, column {e.colno})")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_write_four_golden_rows_read_them_back),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
