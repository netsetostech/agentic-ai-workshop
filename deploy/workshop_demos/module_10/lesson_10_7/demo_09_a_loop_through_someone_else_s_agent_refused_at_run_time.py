"""Lesson 10.7: A loop through someone else's agent: refused at run time

The first cell deploys the peer again with the switch on; lesson-8.4.sh builds the image first, so it takes a few minutes. The second reads the peer's /health, stops if the switch is still off, and sends two tasks whose chains the peer must refuse.

Run order inside this file:
1. Do it: switch it on, then send two chained tasks (source window 47)
2. Do it: switch it on, then send two chained tasks (source window 48)

Prerequisites: demo_08_a_loop_among_the_lane_s_own_services_refused_by_construction.
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


# Original CLI workflow for step_01_switch_it_on_then_send_two_chained_tasks.
COMMANDS_01 = """make deploy-services SCRIPTS=commands/lesson-8.4.sh PEER_CHAIN=on PROJECT="$PROJECT" REGION="$REGION"   # rebuilds the peer's image, then deploys it
# later, to switch it off: the same line without PEER_CHAIN=on

"""

def step_01_switch_it_on_then_send_two_chained_tasks(session):
    """Run Do it: switch it on, then send two chained tasks at this checkpoint.

    The first cell deploys the peer again with the switch on; lesson-8.4.sh builds the image first, so it takes a few minutes. The second reads the peer's /health, stops if the switch is still off, and sends two tasks whose chains the peer must refuse.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the peer deployed with PEER_CHAIN=on; no model call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_switch_it_on_then_send_two_chained_tasks.
COMMANDS_02 = """AGENT_TOKEN="$(tok "$AGENT")" python - <<'PY'
import json, os, urllib.request, uuid, warnings
warnings.filterwarnings("ignore", category=UserWarning)
H = {"Authorization": "Bearer " + os.environ["AGENT_TOKEN"], "Content-Type": "application/json"}
health = json.load(urllib.request.urlopen(urllib.request.Request(os.environ["AGENT"] + "/health", headers=H)))
print(f"the peer's /health: peer_chain {health.get('peer_chain')}, max_llm_calls {health.get('max_llm_calls')}")
if health.get("peer_chain") != "on":        # None: an image from before this lesson's kit, which names no switch at all
    raise SystemExit("PEER_CHAIN is not on at this peer: deploy it with PEER_CHAIN=on first, or these two tasks reach the model")
def ask(chain):
    \"\"\"One task for the peer, its request carrying this delegation chain; the task that comes back.\"\"\"
    body = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "message/send", "params": {
        "message": {"role": "user", "kind": "message", "messageId": str(uuid.uuid4()),
                    "parts": [{"kind": "text", "text": "Which documents does the corpus hold?"}]},
        "metadata": {"documind_chain": chain, "documind_handoff_id": "lesson107-" + str(len(chain))}}}
    req = urllib.request.Request(os.environ["AGENT"] + "/", data=json.dumps(body).encode(), headers=H)
    return json.load(urllib.request.urlopen(req, timeout=120))["result"]
for chain in (["partner_agent", "documind_peer"], ["documind_adk", "partner_agent", "vendor_agent"]):
    task = ask(chain)
    said = " ".join(p.get("text", "") for p in task["status"].get("message", {}).get("parts", []))
    print(f"{' -> '.join(chain)}: {task['status']['state']}, history {[m['role'] for m in task.get('history', [])]}")
    print(f"  {said}")
PY

"""

def step_02_switch_it_on_then_send_two_chained_tasks(session):
    """Run Do it: switch it on, then send two chained tasks at this checkpoint.

    The first cell deploys the peer again with the switch on; lesson-8.4.sh builds the image first, so it takes a few minutes. The second reads the peer's /health, stops if the switch is still off, and sends two tasks whose chains the peer must refuse.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two chained tasks for the peer, each refused before a model call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/chain_reject.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_47', step_01_switch_it_on_then_send_two_chained_tasks),
        ('source_48', step_02_switch_it_on_then_send_two_chained_tasks),
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
