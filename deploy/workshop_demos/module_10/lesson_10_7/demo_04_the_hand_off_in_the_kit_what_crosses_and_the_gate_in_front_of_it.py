"""Lesson 10.7: The hand-off in the kit: what crosses, and the gate in front of it

No network and no model: the cell imports peer.py, asks its gate about four askers, then asks how long a hand-off may wait with 100 s, 30 s and half a second left in the turn.

Run order inside this file:
1. Do it: the gate and the wait, on the kit's own code (source window 16)

Prerequisites: demo_03_switch_the_hand_off_on_and_ask_the_adk_brain.
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


def step_01_the_gate_and_the_wait_on_the_kit_s_own_cod(session):
    """Run Do it: the gate and the wait, on the kit's own code at this checkpoint.

    No network and no model: the cell imports peer.py, asks its gate about four askers, then asks how long a hand-off may wait with 100 s, 30 s and half a second left in the turn.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (peer.py's gate and wait, on the kit's own code; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: HANDOFF_MAX_PER_TURN 2, PEER_TIMEOUT_S 75 s, the turn's deadline 100 s
    an acme member: sent
    an acme member, 2 already sent this turn: refused, this turn has already handed 2 questions to the peer, the most one turn may (HANDOFF_MAX_PER_TURN)
    a zeta member: refused, the peer reads the corpus as an account that is not on this tenant's roster alone, so its answer could come from another tenant's documents; it was not asked (a confused deputy)
    an acme member, the peer's account on 3 rosters: refused, the peer reads the corpus as an account that is not on this tenant's roster alone, so its answer could come from another tenant's documents; it was not asked (a confused deputy)
    100 s left in the tu
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = [".", "services/chat"]
    import limits, peer
    print(f"HANDOFF_MAX_PER_TURN {peer.HANDOFF_MAX_PER_TURN}, PEER_TIMEOUT_S {peer.PEER_TIMEOUT_S:g} s, the turn's deadline {limits.TURN_DEADLINE_S:g} s")
    for who, tenant, rosters, sent in (("an acme member", "acme", ["acme"], 0),
                                       ("an acme member, 2 already sent this turn", "acme", ["acme"], 2),
                                       ("a zeta member", "zeta", ["acme"], 0),
                                       ("an acme member, the peer's account on 3 rosters", "acme", ["acme", "globex", "zeta"], 0)):
        why = peer.gate(tenant, rosters, sent)
        print(f"{who}: " + ("sent" if why is None else "refused, " + why))
    for left in (100, 30, 0.5):
        meter = limits.Meter()
        meter.started -= meter.deadline_s - left            # a turn with this much time left
        print(f"{left:g} s left in the turn: the hand-off waits at most {peer.budget_s(meter):.0f} s")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_the_gate_and_the_wait_on_the_kit_s_own_cod),
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
