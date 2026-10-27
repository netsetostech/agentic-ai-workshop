"""Lesson 10.2: Your lane: plan-and-execute, ReWOO and a flash-lite executor

Do it: plan-and-execute on the manager's cap Do it: ReWOO on a chained row Do it: a flash-lite executor

Run order inside this file:
1. Do it: plan-and-execute on the manager's cap (source window 45)
2. Do it: ReWOO on a chained row (source window 47)
3. Do it: a flash-lite executor (source window 49)

Prerequisites: demo_07_the_3_chained_rows_offline_and_a_cheaper_executor.
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


# Original CLI workflow for step_01_plan_and_execute_on_the_manager_s_cap.
COMMANDS_01 = """make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=plan_execute ROW=chained-exit-stated-cap

"""

def step_01_plan_and_execute_on_the_manager_s_cap(session):
    """Run Do it: plan-and-execute on the manager's cap at this checkpoint.

    Do it: plan-and-execute on the manager's cap

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one live turn, about Rs 3.64 before thinking).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/turn_plan_execute.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_rewoo_on_a_chained_row.
COMMANDS_02 = """make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=rewoo ROW=chained-exit-e3

"""

def step_02_rewoo_on_a_chained_row(session):
    """Run Do it: ReWOO on a chained row at this checkpoint.

    Do it: ReWOO on a chained row

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one live turn, about Rs 1.76 before thinking).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/turn_rewoo.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_a_flash_lite_executor.
COMMANDS_03 = """make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=plan_execute ROW=chained-exit-e3 EXEC_MODEL=gemini-3.1-flash-lite

"""

def step_03_a_flash_lite_executor(session):
    """Run Do it: a flash-lite executor at this checkpoint.

    Do it: a flash-lite executor

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one live turn, about Rs 1.51 before thinking).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/turn_lite.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_45', step_01_plan_and_execute_on_the_manager_s_cap),
        ('source_47', step_02_rewoo_on_a_chained_row),
        ('source_49', step_03_a_flash_lite_executor),
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
