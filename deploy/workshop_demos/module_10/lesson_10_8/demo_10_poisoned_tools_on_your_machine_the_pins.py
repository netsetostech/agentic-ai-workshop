"""Lesson 10.8: Poisoned tools, on your machine: the pins

Listing the kit's server in process imports it, so the venv takes the server's requirements (fastmcp 3.4.7 and the mcp client) and the peer's (google-adk 2.8.0), which pin the same side of the mcp 1.x line. make pin-tools rewrites tool_pins.json byte for byte when nothing changed; CHECK=1 says so and exits 0. Do it: the poisoned server, and the pins against it Do it: the rug pull Edit the kit's own server as a well-meaning teammate might: one more sentence on retrieve's docstring, which is its description. The pins see a tool that changed since a person reviewed it, and CHECK=1 fails. Reviewing it is make pin-tools without CHECK, and the diff is exactly the description and the fingerprint. The last line puts the kit back.

Run order inside this file:
1. Do it: a venv with both services' pins, then the pins against the kit's own server (source window 63)
2. Do it: a venv with both services' pins, then the pins against the kit's own server (source window 64)
3. Do it: the poisoned server, and the pins against it (source window 66)
4. Do it: the poisoned server, and the pins against it (source window 70)
5. Do it: the rug pull (source window 72)
6. Change it: one description, edited (source window 77)

Prerequisites: demo_09_the_runner_on_your_lane_enforced_rows_and_the_rate_as_the_gap.
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


# Original CLI workflow for step_01_a_venv_with_both_services_pins_then_the_pi.
COMMANDS_01 = """python3 -m venv ~/pins-venv
~/pins-venv/bin/pip install -q -r services/mcp/requirements.txt -r services/agent/requirements.txt
export PY=~/pins-venv/bin/python     # make's $(PY): the recipes below run in this venv

"""

def step_01_a_venv_with_both_services_pins_then_the_pi(session):
    """Run Do it: a venv with both services' pins, then the pins against the kit's own server at this checkpoint.

    Listing the kit's server in process imports it, so the venv takes the server's requirements (fastmcp 3.4.7 and the mcp client) and the peer's (google-adk 2.8.0), which pin the same side of the mcp 1.x line. make pin-tools rewrites tool_pins.json byte for byte when nothing changed; CHECK=1 says so and exits 0.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run once, in the kit (the server's and the peer's pins in one venv: fastmcp 3.4.7, the mcp client, google-adk 2.8.0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_venv_with_both_services_pins_then_the_pi.
COMMANDS_02 = """make pin-tools PY="$PY"
make pin-tools PY="$PY" CHECK=1

"""

def step_02_a_venv_with_both_services_pins_then_the_pi(session):
    """Run Do it: a venv with both services' pins, then the pins against the kit's own server at this checkpoint.

    Listing the kit's server in process imports it, so the venv takes the server's requirements (fastmcp 3.4.7 and the mcp client) and the peer's (google-adk 2.8.0), which pin the same side of the mcp 1.x line. make pin-tools rewrites tool_pins.json byte for byte when nothing changed; CHECK=1 says so and exits 0.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's own server listed in process: offline, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: /home/you/pins-venv/bin/python commands/pin_tools.py --server-local
    pinned 4 tools to /home/you/deploy_module_rag/services/agent/tool_pins.json: calculate_processing_cost, corpus_stats, list_documents, retrieve
    /home/you/pins-venv/bin/python commands/pin_tools.py --check --server-local
    tool pins are current: 4 tools, all pinned and unchanged.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_poisoned_server_and_the_pins_against_i.
COMMANDS_03 = """(make evil-mcp PY="$PY" > /tmp/evil-mcp.log 2>&1 &)   # the second tab: the poisoned server, in the background here
for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:8900/mcp && break; sleep 1; done
head -n 1 /tmp/evil-mcp.log


"""

def step_03_the_poisoned_server_and_the_pins_against_i(session):
    """Run Do it: the poisoned server, and the pins against it at this checkpoint.

    Do it: the poisoned server, and the pins against it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in a second shell tab, in the kit (the poisoned server on 127.0.0.1:8900, its default shape).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: evil MCP (a fixture) on http://127.0.0.1:8900/mcp - an extra unpinned tool, summarise_inbox; every host it names is .invalid
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_the_poisoned_server_and_the_pins_against_i.
COMMANDS_04 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
make pin-tools PY="$PY" CHECK=1 URL=http://127.0.0.1:8900/mcp; echo "exit status: $?"
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_04_the_poisoned_server_and_the_pins_against_i(session):
    """Run Do it: the poisoned server, and the pins against it at this checkpoint.

    Do it: the poisoned server, and the pins against it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the first tab, in the kit (the pins against the poisoned server, over the wire).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: /home/you/pins-venv/bin/python commands/pin_tools.py --check --url http://127.0.0.1:8900/mcp
    tool pins are out of date (1):
      - added, never pinned: summarise_inbox
    review the change, then re-pin with make pin-tools (no CHECK).
    make: *** [mk/agents.mk:368: pin-tools] Error 1
    exit status: 1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_the_rug_pull.
COMMANDS_05 = """set +e +o pipefail   # as the page runs it: the check is meant to fail on the rug pull
pkill -f "evals/adversarial/evil_mcp.py"; sleep 1                # Ctrl-C on the first shape
(make evil-mcp PY="$PY" RUG=1 > /tmp/evil-mcp.log 2>&1 &)        # the second tab again, the rug pull
for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:8900/mcp && break; sleep 1; done
head -n 1 /tmp/evil-mcp.log
make pin-tools PY="$PY" CHECK=1 URL=http://127.0.0.1:8900/mcp; echo "exit status: $?"
pkill -f "evals/adversarial/evil_mcp.py"   # the server stopped: nothing after this cell needs it
true


"""

def step_05_the_rug_pull(session):
    """Run Do it: the rug pull at this checkpoint.

    Do it: the rug pull

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the second tab, then the first (the rug pull: the same four names, one changed description).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: evil MCP (a fixture) on http://127.0.0.1:8900/mcp - RUG (retrieve's description poisoned); every host it names is .invalid
    /home/you/pins-venv/bin/python commands/pin_tools.py --check --url http://127.0.0.1:8900/mcp
    tool pins are out of date (1):
      - changed since it was pinned: retrieve
    review the change, then re-pin with make pin-tools (no CHECK).
    make: *** [mk/agents.mk:368: pin-tools] Error 1
    exit status: 1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_change_it_one_description_edited.
COMMANDS_06 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
sed -i "s/with the lane's own cited answer\\./& Up to twenty passages./" services/mcp/server.py
make pin-tools PY="$PY" CHECK=1; echo "exit status: $?"
make pin-tools PY="$PY"
git diff --unified=1 services/agent/tool_pins.json
git checkout -- services/mcp/server.py services/agent/tool_pins.json    # the kit as it was
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_06_change_it_one_description_edited(session):
    """Run Change it: one description, edited at this checkpoint.

    Edit the kit's own server as a well-meaning teammate might: one more sentence on retrieve's docstring, which is its description. The pins see a tool that changed since a person reviewed it, and CHECK=1 fails. Reviewing it is make pin-tools without CHECK, and the diff is exactly the description and the fingerprint. The last line puts the kit back.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one description edited, the check failing, the re-pin, and the kit restored).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: /home/you/pins-venv/bin/python commands/pin_tools.py --check --server-local
    tool pins are out of date (1):
      - changed since it was pinned: retrieve
    review the change, then re-pin with make pin-tools (no CHECK).
    make: *** [mk/agents.mk:368: pin-tools] Error 1
    exit status: 1
    /home/you/pins-venv/bin/python commands/pin_tools.py --server-local
    pinned 4 tools to /home/you/deploy_module_rag/services/agent/tool_pins.json: calculate_processing_cost, corpus_stats, list_documents, retrieve
    --- a/services/agent/tool_pins.json
    +++ b/services/agent/tool_pins.json
    @@ -81,4 +81,4 @@
         "retrieve": {
    -      "fingerprint": "933d0e30aff203558aabf34b814410a33af606044a91b759aa7dbb1dc86ce11f",
    -      "descrip
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_63', step_01_a_venv_with_both_services_pins_then_the_pi),
        ('source_64', step_02_a_venv_with_both_services_pins_then_the_pi),
        ('source_66', step_03_the_poisoned_server_and_the_pins_against_i),
        ('source_70', step_04_the_poisoned_server_and_the_pins_against_i),
        ('source_72', step_05_the_rug_pull),
        ('source_77', step_06_change_it_one_description_edited),
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
