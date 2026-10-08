"""Lesson 3.7: What a stream costs, what its row says, and who reads it

Do it: the day by surface, Rs 0

Run order inside this file:
1. Do it: the day by surface, Rs 0 (source window 35)

Prerequisites: demo_06_a_failure_forced_on_a_candidate_the_ranker_silent_the_stream_still_served_the_li.
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


# Original CLI workflow for step_01_the_day_by_surface_rs_0.
COMMANDS_01 = """make usage PROJECT=$PROJECT HOURS=24 | sed -n '/^by surface/,/^$/p'

"""

def step_01_the_day_by_surface_rs_0(session):
    """Run Do it: the day by surface, Rs 0 at this checkpoint.

    Do it: the day by surface, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (one log read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: by surface
    event                  answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ------------------------------------------------------------------------------------
    query                       NN     xxxxx     xxxx    0.0xxx      x.xx    4xxx   0.xx
    stream                       4      xxxx      xxx    0.0xxx      x.xx    4xxx   0.25
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_35', step_01_the_day_by_surface_rs_0),
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
