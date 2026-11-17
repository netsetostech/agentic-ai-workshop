"""Lesson 3.3: The live eval, with every answerable row's pool read again

Do it: the eval, with the switch on

Run order inside this file:
1. Do it: the eval, with the switch on (source window 19)

Prerequisites: demo_04_the_prompt_and_the_gate_s_rule_in_the_kit_system_the_prompt_line_row_verdict_and.
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


def step_01_the_eval_with_the_switch_on(session):
    """Run Do it: the eval, with the switch on at this checkpoint.

    Do it: the eval, with the switch on

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every golden row, each answerable pool read again: ten minutes or more).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_live.txt]
    """
    import os
    from workshop_helpers.gates import live_gate
    os.environ["DOCUMIND_EVAL_PASSAGES"] = "1"
    try:
        live_gate(session, report="evals/reports/lesson33.json")
    finally:
        os.environ.pop("DOCUMIND_EVAL_PASSAGES", None)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_the_eval_with_the_switch_on),
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
