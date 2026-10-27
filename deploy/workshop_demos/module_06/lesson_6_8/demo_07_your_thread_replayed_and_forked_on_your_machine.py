"""Lesson 6.8: Your thread replayed and forked on your machine

Do it The system prompt tells the model to search for every document question, "a follow-up too". Take that clause out of your clone's brains.py and replay the same turn: the replay asks your follow-up again with the edited prompt and the same history. The lane's prompt does not change, since the replay runs the brain from your clone, on your machine.

Run order inside this file:
1. Do it (source window 35)
2. Change it: the prompt's rule for follow-ups (source window 37)
3. Change it: the prompt's rule for follow-ups (source window 39)
4. Change it: the prompt's rule for follow-ups (source window 41)

Prerequisites: demo_06_one_step_read_back_and_the_thread_exported.
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


# Original CLI workflow for step_01_your_thread_replayed_and_forked_on_your_ma.
COMMANDS_01 = """make replay FILE="$HOME/lesson68.json" FORK="Is it payable to an apprentice?"

"""

def step_01_your_thread_replayed_and_forked_on_your_ma(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (your thread replayed and forked on your machine; a few model calls).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/replay_fork.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_change_it_the_prompt_s_rule_for_follow_ups.
COMMANDS_02 = """sed -i 's/document question, a follow-up too, and cite/document question, and cite/' services/chat/brains.py
grep -c "a follow-up too" services/chat/brains.py || true         # 0: the clause is gone from your clone, and never was on the lane

"""

def step_02_change_it_the_prompt_s_rule_for_follow_ups(session):
    """Run Change it: the prompt's rule for follow-ups at this checkpoint.

    The system prompt tells the model to search for every document question, "a follow-up too". Take that clause out of your clone's brains.py and replay the same turn: the replay asks your follow-up again with the edited prompt and the same history. The lane's prompt does not change, since the replay runs the brain from your clone, on your machine.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (edits one line of your clone's brains.py).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_change_it_the_prompt_s_rule_for_follow_ups.
COMMANDS_03 = """make replay FILE="$HOME/lesson68.json" FORK="Is it payable to an apprentice?"

"""

def step_03_change_it_the_prompt_s_rule_for_follow_ups(session):
    """Run Change it: the prompt's rule for follow-ups at this checkpoint.

    The system prompt tells the model to search for every document question, "a follow-up too". Take that clause out of your clone's brains.py and replay the same turn: the replay asks your follow-up again with the edited prompt and the same history. The lane's prompt does not change, since the replay runs the brain from your clone, on your machine.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same replay, with the edited prompt).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/changeit.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_change_it_the_prompt_s_rule_for_follow_ups.
COMMANDS_04 = """git checkout -q -- services/chat/brains.py                # the kit's prompt back
grep -c "a follow-up too" services/chat/brains.py

"""

def step_04_change_it_the_prompt_s_rule_for_follow_ups(session):
    """Run Change it: the prompt's rule for follow-ups at this checkpoint.

    The system prompt tells the model to search for every document question, "a follow-up too". Take that clause out of your clone's brains.py and replay the same turn: the replay asks your follow-up again with the edited prompt and the same history. The lane's prompt does not change, since the replay runs the brain from your clone, on your machine.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's prompt back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_35', step_01_your_thread_replayed_and_forked_on_your_ma),
        ('source_37', step_02_change_it_the_prompt_s_rule_for_follow_ups),
        ('source_39', step_03_change_it_the_prompt_s_rule_for_follow_ups),
        ('source_41', step_04_change_it_the_prompt_s_rule_for_follow_ups),
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
