"""Lesson 10.1: Prompted ReAct, parsed by code; and a plan first, offline

Do it: prompted ReAct Do it: a plan first

Run order inside this file:
1. Do it: prompted ReAct (source window 20)
2. Do it: a plan first (source window 22)

Prerequisites: demo_04_the_loop_its_recorder_and_the_figure_check_offline.
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


# Original CLI workflow for step_01_prompted_react.
COMMANDS_01 = """make agent-turn OFFLINE=1 PATTERN=react_text

"""

def step_01_prompted_react(session):
    """Run Do it: prompted ReAct at this checkpoint.

    Do it: prompted ReAct

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: prompted ReAct on the same question).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: agent turn: pattern react_text, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      react_text (lesson 10.1): prompted ReAct: no function declaration sent, the tools written into the prompt, the model writing Thought and Action as text and stopping at "Observation:", code reading the Action, running it through ToolNode and writing each Observation
      OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every c
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_plan_first.
COMMANDS_02 = """make agent-turn OFFLINE=1 PATTERN=plan_first

"""

def step_02_a_plan_first(session):
    """Run Do it: a plan first at this checkpoint.

    Do it: a plan first

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the plan-first prompt on the same question).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: agent turn: pattern plan_first, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      plan_first (lesson 10.1): the loop, its prompt led by an instruction to write a plan first: nothing runs the plan, and the loop still decides every call
      OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
    question: I earn Rs 52,000 a m
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_prompted_react),
        ('source_22', step_02_a_plan_first),
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
