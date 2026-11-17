"""Lesson 3.2: Few-shot, measured: the examples taken out and put back on your lane

Do it: with the kit's examples, then with none

Run order inside this file:
1. Do it: with the kit's examples, then with none (source window 46)
2. Do it: with the kit's examples, then with none (source window 48)

Prerequisites: demo_08_few_shot_in_the_kit_the_examples_the_swap_and_the_offline_arms.
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


def step_01_with_the_kit_s_examples_then_with_none(session):
    """Run Do it: with the kit's examples, then with none at this checkpoint.

    Do it: with the kit's examples, then with none

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the kit's examples: 126 gemini-3.1-flash-lite calls, the arbiter's, and embeddings).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/exemplars_kit.txt]
    """
    from pathlib import Path
    from workshop_helpers.gates import route_gate
    route_gate(session, exemplars="kit", report=Path.home() / "exemplars_kit.json")

def step_02_with_the_kit_s_examples_then_with_none(session):
    """Run Do it: with the kit's examples, then with none at this checkpoint.

    Do it: with the kit's examples, then with none

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the same rows, no example).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/exemplars_none.txt]
    """
    from pathlib import Path
    from workshop_helpers.gates import route_gate
    route_gate(session, exemplars="none", report=Path.home() / "exemplars_none.json")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_46', step_01_with_the_kit_s_examples_then_with_none),
        ('source_48', step_02_with_the_kit_s_examples_then_with_none),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
