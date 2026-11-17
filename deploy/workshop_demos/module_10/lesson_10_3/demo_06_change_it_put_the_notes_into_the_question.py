"""Lesson 10.3: Change it: put the notes into the question

Do it: the notes in the question Put it back

Run order inside this file:
1. Do it: the notes in the question (source window 25)
2. Put it back (source window 27)

Prerequisites: demo_05_verify_the_loop_the_check_and_one_reflect_call_offline.
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


# Original CLI workflow for step_01_the_notes_in_the_question.
COMMANDS_01 = """sed -i 's/asked = question  # THE QUESTION.*/asked = " ".join([question] + kept["notes"])/' commands/agent_patterns.py && git diff --stat
make agent-turn OFFLINE=1 PATTERN=verify LAUNDER=1 2>&1 | grep -vE '^(         \\[|  - |  Worked out in code:)'

"""

def step_01_the_notes_in_the_question(session):
    """Run Do it: the notes in the question at this checkpoint.

    Do it: the notes in the question

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the Change-it: the notes put into the question, then the same run).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: commands/agent_patterns.py | 2 +-
     1 file changed, 1 insertion(+), 1 deletion(-)
    agent turn: pattern verify, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      verify (lesson 10.3): check, retry or choose: the loop answers and code checks every figure in the answer against the turn's calculators, its question and its passages; a failed check gets one reflect call's note, and the loop answers again with its notes in its system prom
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_put_it_back.
COMMANDS_02 = """git checkout -q -- commands/agent_patterns.py && git diff --stat && grep -c 'asked = question  # THE QUESTION' commands/agent_patterns.py

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
        ('source_25', step_01_the_notes_in_the_question),
        ('source_27', step_02_put_it_back),
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
