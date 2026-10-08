"""Lesson 4.1: A lookup row: written into build_golden.py, built, and judged

The cell removes any earlier lk-32 line and inserts the row before the bracket that closes GOLDEN, so running it twice is harmless. The builder prints its first five lines and its last. make eval runs exactly the gate's line; calling it directly puts the exit code on a line of its own. The next cell judges six versions of the row in memory, with the gate's own two functions. It writes nothing.

Run order inside this file:
1. Do it: add the row, build, gate (source window 16)
2. What the gate catches, and the one mistake it cannot see (source window 18)

Prerequisites: demo_03_the_set_as_it_stands_the_gate_the_rows_that_cite_the_handbook_and_the_clause_no.
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


# Original CLI workflow for step_01_add_the_row_build_gate.
COMMANDS_01 = """python - <<'PY'
from pathlib import Path
p = Path("evals/build_golden.py")
row = '    R("lk-32", "lookup", "How long can an account go unused before it is disabled?", "acme", ["45 days"], ["SEC-09", "hr_policy_2026"], True, "Lesson 4.1. SEC-09 was the one clause of the handbook no row asked about. Zeta holds the same clause, so the row is a lookup and never an isolation row."),'
lines = [l for l in p.read_text(encoding="utf-8").split("\\n") if not l.startswith('    R("lk-32",')]
lines.insert(lines.index("]", lines.index("GOLDEN = [")), row)            # before the bracket that closes GOLDEN
p.write_text("\\n".join(lines), encoding="utf-8", newline="\\n")
print(sum(l.startswith('    R("') for l in lines), "rows in GOLDEN; the last is lk-32")
PY
python evals/build_golden.py | sed -n '1,5p;$p'
python evals/run_eval.py; echo "exit code $?"

"""

def step_01_add_the_row_build_gate(session):
    """Run Do it: add the row, build, gate at this checkpoint.

    The cell removes any earlier lk-32 line and inserts the row before the bracket that closes GOLDEN, so running it twice is harmless. The builder prints its first five lines and its last. make eval runs exactly the gate's line; calling it directly puts the exit code on a line of its own.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one line into evals/build_golden.py, then the build and the gate).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 66 rows in GOLDEN; the last is lk-32
    golden.jsonl
      rows : 66
      shape: isolation=11, join=11, lookup=35, refusal=8, version=1
      tenants: acme, globex, zeta
      every must_contain / must_retrieve verified against corpus/  OK
    wrote 66 rows -> /home/you/deploy_module_rag/evals/golden.jsonl
    == eval gate: OFFLINE (no credentials, no cost) ==
      66 golden rows over 3 tenants, 27 documents

      [PASS] falsifiable
      [PASS] anchors
      [PASS] coverage

      The golden set is sound. It can go red, and it still contains the rows that would.
    exit code 0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_what_the_gate_catches_and_the_one_mistake(session):
    """Run What the gate catches, and the one mistake it cannot see at this checkpoint.

    The next cell judges six versions of the row in memory, with the gate's own two functions. It writes nothing.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (six versions of the row, judged in memory; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: as written                               accepted
    a figure the clause never gives          REFUSED
        lk-32: must_contain '45 working days' is not in acme's corpus - the row can only fail
    words the file breaks across two lines   REFUSED
        lk-32: must_contain 'disabled automatically' is not in acme's corpus - the row can only fail
    a clause code with a typo                REFUSED
        lk-32: anchor 'SEC-9' matches nothing in acme's corpus (slug? clause id? typo?)
    nothing the answer must contain          REFUSED
        lk-32: an answerable row with no must_contain accepts any answer at all
    another clause's figure                  accepted
    """
    import sys; sys.path.insert(0, "evals")
    from run_eval import load_corpus, check_falsifiable, check_anchors
    corpus = load_corpus()
    row = {"id": "lk-32", "shape": "lookup", "tenant": "acme", "must_contain": ["45 days"],
           "must_retrieve": ["SEC-09", "hr_policy_2026"], "answerable": True}
    for name, change in [("as written", {}),
                         ("a figure the clause never gives", {"must_contain": ["45 working days"]}),
                         ("words the file breaks across two lines", {"must_contain": ["disabled automatically"]}),
                         ("a clause code with a typo", {"must_retrieve": ["SEC-9", "hr_policy_2026"]}),
                         ("nothing the answer must contain", {"must_contain": []}),
                         ("another clause's figure", {"must_contain": ["60 days"]})]:
        found = check_falsifiable([{**row, **change}], corpus) + check_anchors([{**row, **change}], corpus)
        print(f"{name:40} {'REFUSED' if found else 'accepted'}")
        for f in found:
            print("   ", f)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_add_the_row_build_gate),
        ('source_18', step_02_what_the_gate_catches_and_the_one_mistake),
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
