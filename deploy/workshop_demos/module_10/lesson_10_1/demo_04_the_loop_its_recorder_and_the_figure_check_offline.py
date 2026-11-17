"""Lesson 10.1: The loop, its recorder and the figure check, offline

With OFFLINE=1, make agent-turn runs the bench on a scripted model and the kit's own corpus: no project, no credential, no network. The question is the gratuity row of the task set. Do it: the same turn at four thinking levels

Run order inside this file:
1. Do it: one turn (source window 12)
2. Do it: the same turn at four thinking levels (source window 14)

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


# Original CLI workflow for step_01_one_turn.
COMMANDS_01 = """make agent-turn OFFLINE=1

"""

def step_01_one_turn(session):
    """Run Do it: one turn at this checkpoint.

    With OFFLINE=1, make agent-turn runs the bench on a scripted model and the kit's own corpus: no project, no credential, no network. The question is the gratuity row of the task set.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: a scripted model and the kit's corpus; the first run builds ~/graph-venv).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: agent turn: pattern loop, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      OFFLINE: a scripted model and the kit's own corpus, no credential, no cost. Every count below is the script's: 4 characters a token, 64 thinking tokens a call at low
    question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

    model call 1 (thinking low): in 267, thinking 64, visible 21 tokens, Rs 0.0882
      -> retrieve(query=
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_same_turn_at_four_thinking_levels.
COMMANDS_02 = """for t in minimal low medium high; do make agent-turn OFFLINE=1 THINKING=$t 2>&1 | grep -E '^(  thinking:|model call|tokens:|figure check|the turn failed|make: )'; done

"""

def step_02_the_same_turn_at_four_thinking_levels(session):
    """Run Do it: the same turn at four thinking levels at this checkpoint.

    Do it: the same turn at four thinking levels

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the same turn at the four levels, the per-call lines only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: thinking: minimal, sent with every call
    model call 1 (thinking minimal): in 267, thinking 0, visible 21 tokens, Rs 0.0474
    model call 2 (thinking minimal): in 2,329, thinking 0, visible 17 tokens, Rs 0.3078
    model call 3 (thinking minimal): in 2,840, thinking 0, visible 10 tokens, Rs 0.3685
    tokens: in 5,436, thinking 0, visible 48; Rs 0.7237 for the model calls at list price, Rs 0.0000 for rag-api (the script's tokens: nothing is billed)
    figure check: every figure in the model's text is a calculator's, the question's or a passage's (desk_calc.unsupported: none)
      thinking: low, sent with every call
    model call 1 (thinking low): in 267, thinking 64, visible 21 tokens, Rs 0.0882
    model call 2 (thi
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_12', step_01_one_turn),
        ('source_14', step_02_the_same_turn_at_four_thinking_levels),
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
