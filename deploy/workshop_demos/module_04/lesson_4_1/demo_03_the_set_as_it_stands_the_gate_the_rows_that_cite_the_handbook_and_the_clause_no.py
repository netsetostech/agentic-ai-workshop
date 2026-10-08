"""Lesson 4.1: The set as it stands: the gate, the rows that cite the handbook, and the clause no row asks about

The second line lists the rows that cite hr_policy_2026.md. They are the set a reindex of that one document is judged on, in lesson 4.4. The second line lists the rows that cite hr_policy_2026.md. They are the set a reindex of that one document is judged on, in lesson 4.4. Ten rows cite the handbook, by --source. Now count by clause. The cell reads the handbook's sections and lists, for each clause that is not filler, the ACME rows that anchor on it.

Run order inside this file:
1. Do it: the gate, the rows that cite the handbook, and the handbook's clauses (source window 10)
2. Do it: the gate, the rows that cite the handbook, and the handbook's clauses (source window 12)

Prerequisites: setup_prepare.
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


def step_01_the_gate_the_rows_that_cite_the_handbook_a(session):
    """Run Do it: the gate, the rows that cite the handbook, and the handbook's clauses at this checkpoint.

    The second line lists the rows that cite hr_policy_2026.md. They are the set a reindex of that one document is judged on, in lesson 4.4.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the offline gate, then the rows that cite the handbook).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/run_eval.py
    == eval gate: OFFLINE (no credentials, no cost) ==
      65 golden rows over 3 tenants, 27 documents

      [PASS] falsifiable
      [PASS] anchors
      [PASS] coverage

      The golden set is sound. It can go red, and it still contains the rows that would.
      rows citing hr_policy_2026.md: 10 - the scoped live gate judges these
        lk-01  lookup    What is the per-trip cap on domestic travel reimbursement?
        lk-02  lookup    By when is Form 16 issued?
        lk-03  lookup    How many days of earned leave can I carry forward?
        lk-04  lookup    What notice period applies during probation?
        lk-05  lookup    Are USB drives allowed on a company laptop?
        lk-06  lookup    What is the
    """
    from workshop_helpers.steps import backup_files
    backup_files(session, ["evals/build_golden.py", "evals/golden.jsonl", "evals/required.json", "evals/paraphrases.jsonl"])
    session.shell("make eval\npython evals/run_eval.py --source hr_policy_2026.md | sed -n '/rows citing/,$p'")

def step_02_the_gate_the_rows_that_cite_the_handbook_a(session):
    """Run Do it: the gate, the rows that cite the handbook, and the handbook's clauses at this checkpoint.

    The second line lists the rows that cite hr_policy_2026.md. They are the set a reindex of that one document is judged on, in lesson 4.4. Ten rows cite the handbook, by --source. Now count by clause. The cell reads the handbook's sections and lists, for each clause that is not filler, the ACME rows that anchor on it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the handbook and golden.jsonl; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: hr_policy_2026.md: 282 sections, 272 of them GEN- filler
      NP-03      Notice period            lk-06 jn-02 jn-03 vr-01
      PB-02      Probation                lk-04 jn-01
      LV-01      Earned leave             lk-03 lk-07
      LV-07      Leave on exit            jn-01 jn-02 jn-03
      EXP-12     Travel reimbursement     lk-01
      PR-05      Payroll and Form 16      lk-02
      IT-SEC-04  Removable media          lk-05 jn-07
      SEC-09     Access review            <- no golden row asks about this clause
      FIN-02     Purchase approval        lk-08
      WFH-01     Remote work              lk-09
    """
    import json, re
    text = open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()
    heads = re.findall(r"(?m)^## (\S+) \S (.+)$", text)
    rows = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
    real = [(code, name) for code, name in heads if not code.startswith("GEN-")]
    print(f"hr_policy_2026.md: {len(heads)} sections, {len(heads) - len(real)} of them GEN- filler")
    for code, name in real:
        ids = [r["id"] for r in rows if r["tenant"] == "acme" and code in r["must_retrieve"]]
        print(f"  {code:10} {name:24} {' '.join(ids) or '<- no golden row asks about this clause'}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_the_gate_the_rows_that_cite_the_handbook_a),
        ('source_12', step_02_the_gate_the_rows_that_cite_the_handbook_a),
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
