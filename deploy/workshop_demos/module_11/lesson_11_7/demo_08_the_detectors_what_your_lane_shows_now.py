"""Lesson 11.7: The detectors: what your lane shows now

Do it: every detector

Run order inside this file:
1. Do it: every detector (source window 37)

Prerequisites: demo_07_the_two_drills_on_your_lane.
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


# Original CLI workflow for step_01_every_detector.
COMMANDS_01 = """make gotcha-detect PROJECT="$PROJECT" REGION="$REGION" 2>&1 | tee /tmp/gotcha-detect.out && status=0 || status=$?
grep -qE '^[0-9]+ detectors: [0-9]+ found, [0-9]+ could not read$' /tmp/gotcha-detect.out   # every detector ran
[ "$status" -eq 0 ] || grep -q 'gotcha-detect\\] Error 1$' /tmp/gotcha-detect.out   # Error 1: something found, as the page expects


"""

def step_01_every_detector(session):
    """Run Do it: every detector at this checkpoint.

    Do it: every detector

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/detect_all.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_37', step_01_every_detector),
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
