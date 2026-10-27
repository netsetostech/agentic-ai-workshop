"""Lesson 10.10: The loop offline: three runs, two caps and the guards

Do it: the strong oracle, then the weak one Do it: a rupee cap The scripted agent can also misbehave on purpose: the kit's tests use that, and so does this page. Each row below is one iteration it played under the strong oracle when this page was built, and what summary.json recorded for it. Two rules cannot show in that table here. A symlink is undone: it is the first rule of inspect(), and the kit's tests make one where the system allows it. And only live, an agent's output that names github.com, githubusercontent.com or agents_workshop_learner undoes its iteration, because the oracle is public there and work that may have been copied is not kept. Then what the loop never does. It never writes inside the kit:

Run order inside this file:
1. Do it: the strong oracle, then the weak one (source window 26)
2. Do it: the strong oracle, then the weak one (source window 28)
3. Do it: a rupee cap (source window 30)
4. The guards: undone, flagged, never (source window 35)

Prerequisites: demo_04_the_oracle_weak_and_strong.
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


# Original CLI workflow for step_01_the_strong_oracle_then_the_weak_one.
COMMANDS_01 = """make ralph OFFLINE=1 OUT=/tmp/ralph-strong

"""

def step_01_the_strong_oracle_then_the_weak_one(session):
    """Run Do it: the strong oracle, then the weak one at this checkpoint.

    Do it: the strong oracle, then the weak one

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the loop, scripted, under the strong oracle; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ralph: task deadline (statutory_deadline written to an engineer's spec), agent scripted, strong oracle
      caps: 8 iterations, no rupee cap, 80 changed lines an iteration
      the run: /tmp/ralph-strong/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX
      OFFLINE: a scripted agent (commands/ralph.py, Task.script), no model, no network; its tokens are the script's, priced at list price, and nothing is billed
    iteration 1: item "Write statutory_deadline's body, as spec.md says" | 12 lines changed | oracle FAIL (1 failed) | in 14,737 (cached 0), out 302, thinking 64 tokens, Rs 2.1123; spent Rs 2.1123
        FAIL  every day of 2026, for each event: the second working day after the last working day, Monday to Friday
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_strong_oracle_then_the_weak_one.
COMMANDS_02 = """make ralph OFFLINE=1 ORACLE=weak OUT=/tmp/ralph-weak

"""

def step_02_the_strong_oracle_then_the_weak_one(session):
    """Run Do it: the strong oracle, then the weak one at this checkpoint.

    Do it: the strong oracle, then the weak one

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same script under the weak oracle; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ralph: task deadline (statutory_deadline written to an engineer's spec), agent scripted, weak oracle
      caps: 8 iterations, no rupee cap, 80 changed lines an iteration
      the run: /tmp/ralph-weak/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX
      OFFLINE: a scripted agent (commands/ralph.py, Task.script), no model, no network; its tokens are the script's, priced at list price, and nothing is billed
    iteration 1: item "Write statutory_deadline's body, as spec.md says" | 12 lines changed | oracle PASS | in 14,398 (cached 0), out 302, thinking 64 tokens, Rs 2.0691; spent Rs 2.0691
    stopped: the weak oracle passed after 1 iteration
      spent: Rs 2.0691 at list price for the script's tokens (nothing is billed)

    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_a_rupee_cap.
COMMANDS_03 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
make ralph OFFLINE=1 RALPH_BUDGET_INR=5 OUT=/tmp/ralph-cap
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_03_a_rupee_cap(session):
    """Run Do it: a rupee cap at this checkpoint.

    Do it: a rupee cap

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same script under a rupee cap; nothing is billed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ralph: task deadline (statutory_deadline written to an engineer's spec), agent scripted, strong oracle
      caps: 8 iterations, Rs 5, 80 changed lines an iteration
      the run: /tmp/ralph-cap/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX
      OFFLINE: a scripted agent (commands/ralph.py, Task.script), no model, no network; its tokens are the script's, priced at list price, and nothing is billed
    iteration 1: item "Write statutory_deadline's body, as spec.md says" | 12 lines changed | oracle FAIL (1 failed) | in 14,737 (cached 0), out 302, thinking 64 tokens, Rs 2.1123; spent Rs 2.1123
        FAIL  every day of 2026, for each event: the second working day after the last working day, Monday to Friday (1,448 of 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_the_guards_undone_flagged_never.
COMMANDS_04 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
make ralph OFFLINE=1 OUT=.          # the kit itself, as the run's parent
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_04_the_guards_undone_flagged_never(session):
    """Run The guards: undone, flagged, never at this checkpoint.

    The scripted agent can also misbehave on purpose: the kit's tests use that, and so does this page. Each row below is one iteration it played under the strong oracle when this page was built, and what summary.json recorded for it. Two rules cannot show in that table here. A symlink is undone: it is the first rule of inspect(), and the kit's tests make one where the system allows it. And only live, an agent's output that names github.com, githubusercontent.com or agents_workshop_learner undoes its iteration, because the oracle is public there and work that may have been copied is not kept. Then what the loop never does. It never writes inside the kit:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (where the loop will not write).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ERROR: /home/you/deploy_module_rag is inside the kit: the loop never writes there. Give OUT= a directory outside it
    make: *** [mk/coding.mk:33: ralph] Error 2
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_the_strong_oracle_then_the_weak_one),
        ('source_28', step_02_the_strong_oracle_then_the_weak_one),
        ('source_30', step_03_a_rupee_cap),
        ('source_35', step_04_the_guards_undone_flagged_never),
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
