"""Lesson 10.2: Plan-and-execute: a plan, an executor, one replan, offline

For comparison, the loop on the row with the manager's cap. The filter keeps each model call, the tool it asked for, each calculator's result or refusal, and the totals. Do it: plan-and-execute on the same row

Run order inside this file:
1. Do it: the loop on the same row, first (source window 13)
2. Do it: plan-and-execute on the same row (source window 15)

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


# Original CLI workflow for step_01_the_loop_on_the_same_row_first.
COMMANDS_01 = """make agent-turn OFFLINE=1 ROW=chained-exit-stated-cap 2>&1 | grep -E '^(model call|  -> |       (=|refused)|[0-9]+ model calls|the turn failed|make: )'

"""

def step_01_the_loop_on_the_same_row_first(session):
    """Run Do it: the loop on the same row, first at this checkpoint.

    For comparison, the loop on the row with the manager's cap. The filter keeps each model call, the tool it asked for, each calculator's result or refusal, and the totals.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the loop on the stated-cap row, its calls only; the first run builds ~/graph-venv).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: model call 1 (thinking low): in 333, thinking 64, visible 20 tokens, Rs 0.0960
      -> retrieve(query="notice period confirmed employee acknowledged in writing")
    model call 2 (thinking low): in 2,426, thinking 64, visible 12 tokens, Rs 0.3578
      -> notice_end(ack_date="2026-10-05", days=60)
           = 2026-12-04: 2026-10-05 + 60 days = 2026-12-04 (Friday)
    model call 3 (thinking low): in 2,567, thinking 64, visible 13 tokens, Rs 0.3764
      -> retrieve(query="earned leave encashed on exit")
    model call 4 (thinking low): in 4,053, thinking 64, visible 11 tokens, Rs 0.5646
      -> encashable_days(balance=80, cap=45)
           = 45 days: min(80, 45) = 45 days
    model call 5 (thinking low): in 4,168, thinking 64, 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_plan_and_execute_on_the_same_row.
COMMANDS_02 = """make agent-turn OFFLINE=1 PATTERN=plan_execute ROW=chained-exit-stated-cap

"""

def step_02_plan_and_execute_on_the_same_row(session):
    """Run Do it: plan-and-execute on the same row at this checkpoint.

    Do it: plan-and-execute on the same row

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: plan_execute on the same row).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: agent turn: pattern plan_execute, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      plan_execute (lesson 10.2): plan-and-execute: a planner call writes a numbered plan, an executor carries it out a step at a time with the desk's tools through ToolNode, a refused or failed step sends the rest back to the planner once, and a last call writes the answer from the steps' results
      the planner: gemini-3.6-flash (plan, replan and solve)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_the_loop_on_the_same_row_first),
        ('source_15', step_02_plan_and_execute_on_the_same_row),
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
