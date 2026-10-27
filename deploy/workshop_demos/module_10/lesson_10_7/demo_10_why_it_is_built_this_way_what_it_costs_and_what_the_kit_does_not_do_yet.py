"""Lesson 10.7: Why it is built this way, what it costs, and what the kit does not do yet

Every guard above sits on the lane. One more loop needs neither a hand-off nor a second service: two agents that may each hand the turn to the other, where neither owns the answer. In ADK it is one setting away. An agent under a parent is offered transfer_to_agent, whose agent_name is an enum of the agents it may reach: its parent, and its peers unless disallow_transfer_to_peers is set. commands/agent_shapes.py builds two such desks under a root, scripts each to want the other desk to answer, and puts one plugin on the run, TransferCap. It counts the agents a turn starts in a temp: key, which ADK keeps for one turn and never stores, and once 3 transfers have been made it answers in place of the next agent, before that agent's model is called. Run it offline, at Rs 0. It runs the same turn twice, with the peer edges and without them:

Run order inside this file:
1. A ping-pong, and the cap that ends it (source window 52)

Prerequisites: demo_09_a_loop_through_someone_else_s_agent_refused_at_run_time.
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


# Original CLI workflow for step_01_a_ping_pong_and_the_cap_that_ends_it.
COMMANDS_01 = """make agent-shapes OFFLINE=1

"""

def step_01_a_ping_pong_and_the_cap_that_ends_it(session):
    """Run A ping-pong, and the cap that ends it at this checkpoint.

    Every guard above sits on the lane. One more loop needs neither a hand-off nor a second service: two agents that may each hand the turn to the other, where neither owns the answer. In ADK it is one setting away. An agent under a parent is offered transfer_to_agent, whose agent_name is an enum of the agents it may reach: its parent, and its peers unless disallow_transfer_to_peers is set. commands/agent_shapes.py builds two such desks under a root, scripts each to want the other desk to answer, and puts one plugin on the run, TransferCap. It counts the agents a turn starts in a temp: key, which ADK keeps for one turn and never stores, and once 3 transfers have been made it answers in place of the next agent, before that agent's model is called. Run it offline, at Rs 0. It runs the same turn twice, with the peer edges and without them:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two ADK desks in a ping-pong, and the cap that ends it; offline, Rs 0; the first run builds ~/graph-venv).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: swarm_adk, offline: scripted models, no credential, Rs 0. TransferCap ends a turn after 3 transfers.
    Q: What notice period does a confirmed E3 employee at ACME serve?

    == transfers between the desks allowed (ADK's default)
    who each agent may transfer to (transfer_to_agent's enum, as its model was offered it):
      desk_root      handbook_desk, statute_desk
      handbook_desk  desk_root, statute_desk
      statute_desk   desk_root, handbook_desk
    transfer 1: desk_root -> handbook_desk
    transfer 2: handbook_desk -> statute_desk
    transfer 3: statute_desk -> handbook_desk
    transfer 4: handbook_desk -> statute_desk   refused: TransferCap answered before statute_desk ran
    answer, written by TransferCap, in statu
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_52', step_01_a_ping_pong_and_the_cap_that_ends_it),
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
