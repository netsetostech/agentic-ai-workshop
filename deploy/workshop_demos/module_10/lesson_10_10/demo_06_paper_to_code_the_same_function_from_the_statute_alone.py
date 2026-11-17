"""Lesson 10.10: Paper-to-code: the same function from the statute alone

Do it

Run order inside this file:
1. Do it (source window 42)

Prerequisites: demo_05_the_loop_offline_three_runs_two_caps_and_the_guards.
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


# Original CLI workflow for step_01_paper_to_code_the_same_function_from_the_s.
COMMANDS_01 = """make ralph OFFLINE=1 TASK=statute OUT=/tmp/ralph-statute

"""

def step_01_paper_to_code_the_same_function_from_the_s(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (paper-to-code, scripted; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ralph: task statute (statutory_deadline from the statute alone (paper-to-code)), agent scripted, strong oracle
      caps: 8 iterations, no rupee cap, 80 changed lines an iteration
      the run: /tmp/ralph-statute/ralph-statute-YYYYMMDD-HHMMSS-XXXXXXXX
      OFFLINE: a scripted agent (commands/ralph.py, Task.script), no model, no network; its tokens are the script's, priced at list price, and nothing is billed
    iteration 1: item "Write statutory_deadline's body, as spec.md says" | 16 lines changed | oracle FAIL (2 failed) | in 14,496 (cached 0), out 312, thinking 64 tokens, Rs 2.0879; spent Rs 2.0879
        FAIL  desk_calc's own selftest (1 of 79 lines failed)
        FAIL  an event s.17(2) does not count from
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_42', step_01_paper_to_code_the_same_function_from_the_s),
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
