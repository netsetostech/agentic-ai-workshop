"""Lesson 3.2: Change it: one prompted-reasoning rule against native thinking

Do it: both arms, with every answer kept in a report The report keeps each answer's first 600 characters, its calls and its quote checks. The cell prints jn-03's answer from each arm, so you can see where the working went.

Run order inside this file:
1. Do it: both arms, with every answer kept in a report (source window 26)
2. Do it: jn-03's two answers, from the report (source window 28)

Prerequisites: demo_06_chain_of_thought_measured_the_join_rows_at_low_medium_and_high.
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


# Original CLI workflow for step_01_both_arms_with_every_answer_kept_in_a_repo.
COMMANDS_01 = """make bench PROJECT=$PROJECT BENCH_ARGS="--shape join --levels LOW --add-rule 'Show your working in the answer: name each fact the question needs and the [N] that states it, then combine them.' --report $HOME/cot_rule.json"

"""

def step_01_both_arms_with_every_answer_kept_in_a_repo(session):
    """Run Do it: both arms, with every answer kept in a report at this checkpoint.

    Do it: both arms, with every answer kept in a report

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (11 pools, then 22 answers at LOW, two arms).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/cot_rule.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_jn_03_s_two_answers_from_the_report(session):
    """Run Do it: jn-03's two answers, from the report at this checkpoint.

    The report keeps each answer's first 600 characters, its calls and its quote checks. The cell prints jn-03's answer from each arm, so you can see where the working went.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell; reads the report, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/cot_answers.txt]
    """
    import json, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    report = json.load(open(os.path.expanduser("~/cot_rule.json"), encoding="utf-8"))
    for a in (a for a in report["answers"] if a["id"] == "jn-03"):
        thought = sum(c.get("thought", 0) for c in a["calls"])
        visible = sum(c.get("visible", 0) for c in a["calls"])
        print(f"== {a['arm']} {a['level']}: {'pass' if a['pass'] else 'did not pass: ' + a['why']} | thought {thought} | visible {visible} "
              f"| Rs {a['cost_inr']:.4f}")
        print(a.get("answer") or a.get("error"))
        for c in a.get("cites", []):
            print(f"   quote, {c['check']}: {c['quote'][:90]}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_both_arms_with_every_answer_kept_in_a_repo),
        ('source_28', step_02_jn_03_s_two_answers_from_the_report),
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
