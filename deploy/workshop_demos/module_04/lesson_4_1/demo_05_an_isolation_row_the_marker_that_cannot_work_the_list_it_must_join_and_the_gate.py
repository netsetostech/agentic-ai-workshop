"""Lesson 4.1: An isolation row: the marker that cannot work, the list it must join, and the gate green again

The first try: the obvious marker The second try: ACME's phrase The third try: listed, and the gate green

Run order inside this file:
1. The first try: the obvious marker (source window 23)
2. The second try: ACME's phrase (source window 25)
3. The third try: listed, and the gate green (source window 27)

Prerequisites: demo_04_a_lookup_row_written_into_build_golden_py_built_and_judged.
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


def step_01_the_first_try_the_obvious_marker(session):
    """Run The first try: the obvious marker at this checkpoint.

    The first try: the obvious marker

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the isolation row, with the obvious marker).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 67 rows in GOLDEN; the last is iso-11
    golden.jsonl
      rows : 67
      shape: isolation=12, join=11, lookup=35, refusal=8, version=1
      tenants: acme, globex, zeta

      ASSERTIONS THAT DO NOT MATCH THE CORPUS:
       ! iso-11: must_not_contain '45 days' is in zeta's OWN corpus - answering it correctly would fail the row
    exit code 1
    66
    """
    from pathlib import Path
    p = Path("evals/build_golden.py")
    row = '    R("iso-11", "isolation", "How many days of earned leave are encashed on exit?", "zeta", ["20 days"], ["LV-07", "hr_policy_zeta_2026"], True, "Lesson 4.1. The same question, a different answer per tenant: ACME caps encashment at 45 days.", ["45 days"]),'
    lines = [l for l in p.read_text(encoding="utf-8").split("\n") if not l.startswith('    R("iso-11",')]
    lines.insert(lines.index("]", lines.index("GOLDEN = [")), row)            # before the bracket that closes GOLDEN
    p.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(sum(l.startswith('    R("') for l in lines), "rows in GOLDEN; the last is iso-11")
    import sys
    from workshop_helpers.gates import expect_failure
    expect_failure(session, [sys.executable, "evals/build_golden.py"], status=1, messages=["iso-11:", "OWN corpus"])
    print("Unchanged golden row count:", len(Path("evals/golden.jsonl").read_text().splitlines()))

def step_02_the_second_try_acme_s_phrase(session):
    """Run The second try: ACME's phrase at this checkpoint.

    The second try: ACME's phrase

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same row with ACME's phrase as the marker, then the build and the gate).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 67 rows in GOLDEN; the last is iso-11
    golden.jsonl
      rows : 67
      shape: isolation=12, join=11, lookup=35, refusal=8, version=1
      tenants: acme, globex, zeta
      every must_contain / must_retrieve verified against corpus/  OK
    wrote 67 rows -> /home/you/deploy_module_rag/evals/golden.jsonl
    == eval gate: OFFLINE (no credentials, no cost) ==
      67 golden rows over 3 tenants, 27 documents

      [PASS] falsifiable
      [PASS] anchors
      [FAIL] coverage
             iso-11: a isolation row that required.json does not list

      1 problem(s). The golden set cannot judge the model until it judges itself.
    exit code 1
    """
    from pathlib import Path
    p = Path("evals/build_golden.py")
    row = '    R("iso-11", "isolation", "How many days of earned leave are encashed on exit?", "zeta", ["20 days"], ["LV-07", "hr_policy_zeta_2026"], True, "Lesson 4.1. ACME caps encashment at 45 days, and 45 days is also in SEC-09 of this handbook, so the marker is the phrase only ACME holds.", ["capped at 45 days"]),'
    lines = [l for l in p.read_text(encoding="utf-8").split("\n") if not l.startswith('    R("iso-11",')]
    lines.insert(lines.index("]", lines.index("GOLDEN = [")), row)            # before the bracket that closes GOLDEN
    p.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(sum(l.startswith('    R("') for l in lines), "rows in GOLDEN; the last is iso-11")
    import sys
    from workshop_helpers.gates import expect_failure
    session.command([sys.executable, "evals/build_golden.py"])
    expect_failure(session, [sys.executable, "evals/run_eval.py"], status=1, messages=["iso-11:", "required.json does not list"])

# Original CLI workflow for step_03_the_third_try_listed_and_the_gate_green.
COMMANDS_03 = """python - <<'PY'
import json
from pathlib import Path
p = Path("evals/required.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["ids"] = sorted(set(d["ids"]) | {"iso-11"})
p.write_text(json.dumps(d, indent=1), encoding="utf-8", newline="\\n")
print(len(d["ids"]), "required ids:", " ".join(d["ids"]))
PY
make eval; echo "exit code $?"

"""

def step_03_the_third_try_listed_and_the_gate_green(session):
    """Run The third try: listed, and the gate green at this checkpoint.

    The third try: listed, and the gate green

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (iso-11 listed in evals/required.json, then make eval).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 16 required ids: iso-01 iso-02 iso-03 iso-04 iso-05 iso-06 iso-07 iso-08 iso-09 iso-10 iso-11 mm-01 mm-02 mm-03 mm-04 vr-01
    python evals/run_eval.py
    == eval gate: OFFLINE (no credentials, no cost) ==
      67 golden rows over 3 tenants, 27 documents

      [PASS] falsifiable
      [PASS] anchors
      [PASS] coverage

      The golden set is sound. It can go red, and it still contains the rows that would.
    exit code 0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_the_first_try_the_obvious_marker),
        ('source_25', step_02_the_second_try_acme_s_phrase),
        ('source_27', step_03_the_third_try_listed_and_the_gate_green),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
