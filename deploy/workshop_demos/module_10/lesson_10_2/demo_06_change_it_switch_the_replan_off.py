"""Lesson 10.2: Change it: switch the replan off

Do it: no replan Put it back

Run order inside this file:
1. Do it: no replan (source window 27)
2. Put it back (source window 29)

Prerequisites: demo_05_rewoo_one_plan_with_placeholders_checked_and_run_in_waves_offline.
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


# Original CLI workflow for step_01_no_replan.
COMMANDS_01 = """sed -i 's/^MAX_REPLANS = 1 /MAX_REPLANS = 0 /' commands/agent_patterns.py && git diff --stat
make agent-turn OFFLINE=1 PATTERN=plan_execute ROW=chained-exit-stated-cap 2>&1 | grep -vE '^(         \\[|  - |  Worked out in code:)'

"""

def step_01_no_replan(session):
    """Run Do it: no replan at this checkpoint.

    Do it: no replan

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the Change-it: no replan, then the same turn).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: commands/agent_patterns.py | 2 +-
     1 file changed, 1 insertion(+), 1 deletion(-)
    agent turn: pattern plan_execute, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      plan_execute (lesson 10.2): plan-and-execute: a planner call writes a numbered plan, an executor carries it out a step at a time with the desk's tools through ToolNode, a refused or failed step sends the rest back to the planner once, and a last call writes the answer
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_put_it_back.
COMMANDS_02 = """git checkout -q -- commands/agent_patterns.py && git diff --stat && grep -c '^MAX_REPLANS = 1 ' commands/agent_patterns.py

"""

def step_02_put_it_back(session):
    """Run Put it back at this checkpoint.

    Put it back

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (put the line back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_no_replan),
        ('source_29', step_02_put_it_back),
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
