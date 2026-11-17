"""Lesson 2.6: The rule and the generator on your lane's pools

Do it: zeta's rows on your lane

Run order inside this file:
1. Do it: zeta's rows on your lane (source window 35)

Prerequisites: demo_05_the_decision_eval_for_rs_0_a_higher_floor_and_jev_s_switch.
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


# Original CLI workflow for step_01_zeta_s_rows_on_your_lane.
COMMANDS_01 = """make decide PROJECT="$PROJECT" REGION="$REGION" DECIDE_ARGS="--tenant zeta --save evals/reports/decide-zeta.json"

"""

def step_01_zeta_s_rows_on_your_lane(session):
    """Run Do it: zeta's rows on your lane at this checkpoint.

    Do it: zeta's rows on your lane

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (zeta's 10 rows: 10 passages calls at Rs 0 and 10 generator calls, about Rs 2.75 of input and at most Rs 15.80 in all).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/decide_learner.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_35', step_01_zeta_s_rows_on_your_lane),
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
