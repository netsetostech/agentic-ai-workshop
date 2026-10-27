"""Lesson 10.3: verify: the loop, the check and one reflect call, offline

Do it: as the prompt stands Do it: a figure of its own, corrected in one round Do it: notes that carry a figure

Run order inside this file:
1. Do it: as the prompt stands (source window 18)
2. Do it: a figure of its own, corrected in one round (source window 20)
3. Do it: notes that carry a figure (source window 22)

Prerequisites: demo_04_the_figure_check_on_its_own_at_rs_0.
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


# Original CLI workflow for step_01_as_the_prompt_stands.
COMMANDS_01 = """make agent-turn OFFLINE=1 PATTERN=verify 2>&1 | grep -vE '^(         \\[|  - |  Worked out in code:)'

"""

def step_01_as_the_prompt_stands(session):
    """Run Do it: as the prompt stands at this checkpoint.

    Do it: as the prompt stands

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: verify on the gratuity row as the prompt stands; the first run builds ~/graph-venv).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: agent turn: pattern verify, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      verify (lesson 10.3): check, retry or choose: the loop answers and code checks every figure in the answer against the turn's calculators, its question and its passages; a failed check gets one reflect call's note, and the loop answers again with its notes in its system prompt, never its question, at most three attempts; the first answer the check passes
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_figure_of_its_own_corrected_in_one_round.
COMMANDS_02 = """make agent-turn OFFLINE=1 PATTERN=verify INVENT=1 2>&1 | grep -vE '^(         \\[|  - |  Worked out in code:)'

"""

def step_02_a_figure_of_its_own_corrected_in_one_round(session):
    """Run Do it: a figure of its own, corrected in one round at this checkpoint.

    Do it: a figure of its own, corrected in one round

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: a first attempt that writes a figure of its own).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: agent turn: pattern verify, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      verify (lesson 10.3): check, retry or choose: the loop answers and code checks every figure in the answer against the turn's calculators, its question and its passages; a failed check gets one reflect call's note, and the loop answers again with its notes in its system prompt, never its question, at most three attempts; the first answer the check passes
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_notes_that_carry_a_figure.
COMMANDS_03 = """make agent-turn OFFLINE=1 PATTERN=verify LAUNDER=1 2>&1 | grep -vE '^(         \\[|  - |  Worked out in code:)'

"""

def step_03_notes_that_carry_a_figure(session):
    """Run Do it: notes that carry a figure at this checkpoint.

    Do it: notes that carry a figure

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: notes that carry a figure).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: agent turn: pattern verify, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      verify (lesson 10.3): check, retry or choose: the loop answers and code checks every figure in the answer against the turn's calculators, its question and its passages; a failed check gets one reflect call's note, and the loop answers again with its notes in its system prompt, never its question, at most three attempts; the first answer the check passes
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_as_the_prompt_stands),
        ('source_20', step_02_a_figure_of_its_own_corrected_in_one_round),
        ('source_22', step_03_notes_that_carry_a_figure),
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
