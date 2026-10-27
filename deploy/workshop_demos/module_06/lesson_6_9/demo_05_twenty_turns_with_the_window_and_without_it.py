"""Lesson 6.9: Twenty turns, with the window and without it

Do it: with the window Do it: without the window Give earlier turns a quarter of the room, 500 tokens, and run the same twenty turns. CHAT_HISTORY_TOKENS=500 in the environment does the same as HISTORY=500.

Run order inside this file:
1. Do it: with the window (source window 20)
2. Do it: without the window (source window 22)
3. Change it: a smaller budget (source window 24)

Prerequisites: demo_04_the_window_in_the_kit_and_one_call_opened_up.
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


# Original CLI workflow for step_01_with_the_window.
COMMANDS_01 = """make window-check            # the window in front of the kit's LangChain brain: offline, Rs 0

"""

def step_01_with_the_window(session):
    """Run Do it: with the window at this checkpoint.

    Do it: with the window

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: make window-check MODE=windowed: 20 turns of one conversation, offline, Rs 0
      the kit's LangChain brain on an InMemorySaver; a scripted model (it searches for the question, then answers from
      the first passage) and the Rs 0 lane over evals/corpus; no network, no credential
      every call is sent the window: the system prompt and the turn it answers, whole, and at most 2,000 tokens
      of earlier turns (CHAT_HISTORY_TOKENS)
      tokens are langchain-core's estimate (count_tokens_approximately), not Gemini's count

              thread           the turn's largest call     earlier turns              write rules
      turn    msgs   tokens     context   ceiling     kept whole  brought forward  cleared  mask
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_without_the_window.
COMMANDS_02 = """make window-check MODE=full  # the same twenty turns, every call sent the whole thread

"""

def step_02_without_the_window(session):
    """Run Do it: without the window at this checkpoint.

    Do it: without the window

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: make window-check MODE=full: 20 turns of one conversation, offline, Rs 0
      the kit's LangChain brain on an InMemorySaver; a scripted model (it searches for the question, then answers from
      the first passage) and the Rs 0 lane over evals/corpus; no network, no credential
      every call is sent the whole thread, as the brains do today; the ceiling is the window's (the floor plus 2,000
      tokens of earlier turns), shown for comparison
      tokens are langchain-core's estimate (count_tokens_approximately), not Gemini's count

              thread           the turn's largest call
      turn    msgs   tokens     context   ceiling     over the ceiling
         1       4      659         714     2,714            -

    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_change_it_a_smaller_budget.
COMMANDS_03 = """make window-check HISTORY=500   # a quarter of the budget for earlier turns

"""

def step_03_change_it_a_smaller_budget(session):
    """Run Change it: a smaller budget at this checkpoint.

    Give earlier turns a quarter of the room, 500 tokens, and run the same twenty turns. CHAT_HISTORY_TOKENS=500 in the environment does the same as HISTORY=500.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the Change-it).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: make window-check MODE=windowed: 20 turns of one conversation, offline, Rs 0
      the kit's LangChain brain on an InMemorySaver; a scripted model (it searches for the question, then answers from
      the first passage) and the Rs 0 lane over evals/corpus; no network, no credential
      every call is sent the window: the system prompt and the turn it answers, whole, and at most 500 tokens
      of earlier turns (CHAT_HISTORY_TOKENS)
      tokens are langchain-core's estimate (count_tokens_approximately), not Gemini's count

              thread           the turn's largest call     earlier turns              write rules
      turn    msgs   tokens     context   ceiling     kept whole  brought forward  cleared  masked
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_with_the_window),
        ('source_22', step_02_without_the_window),
        ('source_24', step_03_change_it_a_smaller_budget),
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
