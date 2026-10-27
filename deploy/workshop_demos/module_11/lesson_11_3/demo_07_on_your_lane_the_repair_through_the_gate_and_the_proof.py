"""Lesson 11.3: On your lane: the repair through the gate, and the proof

Run the Repair: line your make incident printed after the rollback. On a lane whose serving revision runs the Makefile's defaults it is the first line below; if yours names more settings, use yours. Then the gate: about ten minutes and about Rs 29. Do it: promote it through the gate The smokes of your deployed services, then make incident on the lane as it is now. The proof is both: make smoke-deployed exits 0, and make incident exits 0 with the gated state.

Run order inside this file:
1. Do it: the repair candidate, and its gate (source window 44)
2. Do it: promote it through the gate (source window 46)
3. Do it: the proof (source window 48)

Prerequisites: demo_06_on_your_lane_promote_break_it_roll_back.
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


# Original CLI workflow for step_01_the_repair_candidate_and_its_gate.
COMMANDS_01 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
make candidate PROJECT="$PROJECT" REGION="$REGION" GENERATOR_MODEL=gemini-3.6-flash
make gate PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_01_the_repair_candidate_and_its_gate(session):
    """Run Do it: the repair candidate, and its gate at this checkpoint.

    Run the Repair: line your make incident printed after the rollback. On a lane whose serving revision runs the Makefile's defaults it is the first line below; if yours names more settings, use yours. Then the gate: about ten minutes and about Rs 29.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the Repair line make incident printed, then every golden row).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/candidate_gate_repair.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_promote_it_through_the_gate.
COMMANDS_02 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
make promote-gated PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_02_promote_it_through_the_gate(session):
    """Run Do it: promote it through the gate at this checkpoint.

    Do it: promote it through the gate

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (gate-check, then one traffic move).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/promote_repair.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_proof.
COMMANDS_03 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
make smoke-deployed PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
make incident PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_03_the_proof(session):
    """Run Do it: the proof at this checkpoint.

    The smokes of your deployed services, then make incident on the lane as it is now. The proof is both: make smoke-deployed exits 0, and make incident exits 0 with the gated state.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the proof: the smokes, then the incident read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/smoke_incident_proof.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_44', step_01_the_repair_candidate_and_its_gate),
        ('source_46', step_02_promote_it_through_the_gate),
        ('source_48', step_03_the_proof),
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
