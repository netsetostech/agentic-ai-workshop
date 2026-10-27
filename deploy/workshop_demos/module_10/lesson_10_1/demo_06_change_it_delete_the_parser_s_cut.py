"""Lesson 10.1: Change it: delete the parser's cut

Do it: first, with the cut Do it: delete the cut, and run it again Put it back

Run order inside this file:
1. Do it: first, with the cut (source window 25)
2. Do it: delete the cut, and run it again (source window 27)
3. Put it back (source window 29)

Prerequisites: demo_05_prompted_react_parsed_by_code_and_a_plan_first_offline.
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


# Original CLI workflow for step_01_first_with_the_cut.
COMMANDS_01 = """make agent-turn OFFLINE=1 PATTERN=react_text INVENT=1

"""

def step_01_first_with_the_cut(session):
    """Run Do it: first, with the cut at this checkpoint.

    Do it: first, with the cut

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: a scripted model whose stop sequence does not hold).
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

# Original CLI workflow for step_02_delete_the_cut_and_run_it_again.
COMMANDS_02 = """sed -i '/THE CUT/d' commands/agent_patterns.py && git diff --stat
make agent-turn OFFLINE=1 PATTERN=react_text INVENT=1

"""

def step_02_delete_the_cut_and_run_it_again(session):
    """Run Do it: delete the cut, and run it again at this checkpoint.

    Do it: delete the cut, and run it again

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the Change-it: delete the cut, then the same run).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: commands/agent_patterns.py | 1 -
     1 file changed, 1 deletion(-)
    agent turn: pattern react_text, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      react_text (lesson 10.1): prompted ReAct: no function declaration sent, the tools written into the prompt, the model writing Thought and Action as text and stopping at "Observation:", code reading the Action, running it through ToolNode and writing each Observation
      OFFLINE: a scripted
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_put_it_back.
COMMANDS_03 = """git checkout -q -- commands/agent_patterns.py && git diff --stat && grep -c "THE CUT" commands/agent_patterns.py

"""

def step_03_put_it_back(session):
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
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_first_with_the_cut),
        ('source_27', step_02_delete_the_cut_and_run_it_again),
        ('source_29', step_03_put_it_back),
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
