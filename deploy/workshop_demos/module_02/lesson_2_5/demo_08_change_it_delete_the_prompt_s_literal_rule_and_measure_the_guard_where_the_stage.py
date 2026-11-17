"""Lesson 2.5: Change it: delete the prompt's literal rule and measure the guard; where the stage cannot go

Do it: the rows the guard can refuse, Rs 0 Do it: delete the rule Do it: the same arm, the edited prompt, those rows The edit changed the prompt and left PROMPT_VERSION as it was, so any line written with the edited prompt would name a version that does not describe it. That is a reason to restore the file rather than keep the experiment; versioning a prompt properly is lesson 3.6's subject.

Run order inside this file:
1. Do it: the rows the guard can refuse, Rs 0 (source window 55)
2. Do it: delete the rule (source window 57)
3. Do it: the same arm, the edited prompt, those rows (source window 59)
4. Do it: put the kit back (source window 61)

Prerequisites: demo_07_the_measurement_the_rewrite_arm_against_the_lane_on_the_golden_rows_and_the_para.
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


def step_01_the_rows_the_guard_can_refuse_rs_0(session):
    """Run Do it: the rows the guard can refuse, Rs 0 at this checkpoint.

    Do it: the rows the guard can refuse, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 13 anchored golden rows carry a literal; the guard can refuse a rewrite of no other:
       lk-02  16
       lk-06  e3
       lk-08  rs 3,00,000
       lk-10  inv-2026-0412
       lk-11  fy2026
       jn-03  e3, 50 days
       jn-05  inv-2026-0412
       jn-06  fy2026
       lk-14  2017
       jn-08  2017
       mm-01  3, fy2025, fy2026
       mm-03  fy2026
       vr-01  e3
    """
    import json, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, ".")
    from shared.query_rewrite import literals
    rows = [r for r in (json.loads(line) for line in open("evals/golden.jsonl", encoding="utf-8") if line.strip())
            if r.get("must_retrieve") and literals(r["question"])]
    with open("/tmp/literal_rows.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    print(len(rows), "anchored golden rows carry a literal; the guard can refuse a rewrite of no other:")
    for r in rows:
        print(f"   {r['id']:6} {', '.join(literals(r['question']))}")

def step_02_delete_the_rule(session):
    """Run Do it: delete the rule at this checkpoint.

    Do it: delete the rule

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; edits one kit file in your clone, never the lane).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 5 rules left; the prompt version still says 2026-10-08.1
    - Use the words those documents use: the formal term for an informal one, and the full name of a law or a term beside its abbreviation.
    - Keep every condition the question sets: who is asking, which document, before or after, the least or the most.
    - Do not answer the question, and add no fact, figure or name that is not in it.
    - The question may be in English, in Hindi written in Devanagari, or in Hinglish (Hindi typed in Latin letters); write the query in English.
    - One line of at most 40 words. If the question is already a good search query, return it unchanged.
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    path = "shared/query_rewrite.py"
    src = open(path, encoding="utf-8").read()
    rule = ('        "- Copy every code, grade, section, number, amount, date and unit exactly as written: QX-12, G7, s.99, "\n'
            '        "Rs 12,345 and 21 days stay QX-12, G7, s.99, Rs 12,345 and 21 days.",\n')
    assert src.count(rule) == 1, "the rule is not where this page expects it: git checkout -- shared/query_rewrite.py, then pull the kit"
    open(path, "w", encoding="utf-8").write(src.replace(rule, ""))
    sys.path.insert(0, ".")
    from shared import query_rewrite as qr
    rules = [line for line in qr.prompt("QUESTION").splitlines() if line.startswith("- ")]
    print(len(rules), "rules left; the prompt version still says", qr.PROMPT_VERSION)
    print("\n".join(rules))

# Original CLI workflow for step_03_the_same_arm_the_edited_prompt_those_rows.
COMMANDS_03 = """make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite --golden /tmp/literal_rows.jsonl"

"""

def step_03_the_same_arm_the_edited_prompt_those_rows(session):
    """Run Do it: the same arm, the edited prompt, those rows at this checkpoint.

    Do it: the same arm, the edited prompt, those rows

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the 13 rows above, two arms, the edited prompt).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/changeit.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_put_the_kit_back.
COMMANDS_04 = """git checkout -q -- shared/query_rewrite.py
git status --short -- shared/
python -c "import sys; sys.path.insert(0, '.'); from shared import query_rewrite as qr; print('the rule is back:', any(l.startswith('- Copy every code') for l in qr.prompt('q').splitlines()))"

"""

def step_04_put_the_kit_back(session):
    """Run Do it: put the kit back at this checkpoint.

    The edit changed the prompt and left PROMPT_VERSION as it was, so any line written with the edited prompt would name a version that does not describe it. That is a reason to restore the file rather than keep the experiment; versioning a prompt properly is lesson 3.6's subject.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the kit file put back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the rule is back: True
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_55', step_01_the_rows_the_guard_can_refuse_rs_0),
        ('source_57', step_02_delete_the_rule),
        ('source_59', step_03_the_same_arm_the_edited_prompt_those_rows),
        ('source_61', step_04_put_the_kit_back),
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
