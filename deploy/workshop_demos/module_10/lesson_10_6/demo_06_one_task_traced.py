"""Lesson 10.6: One task, traced

Do it: the task Do it: what the lane saw

Run order inside this file:
1. Do it: the task (source window 16)
2. Do it: what the lane saw (source window 18)

Prerequisites: demo_05_the_gate_make_smoke_agent.
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


# Original CLI workflow for step_01_the_task.
COMMANDS_01 = """AGENT_TOKEN="$(tok "$AGENT")" python - <<'PY'
import json, os, urllib.request, uuid
body = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "message/send", "params": {"message": {
    "role": "user", "kind": "message", "messageId": str(uuid.uuid4()),
    "parts": [{"kind": "text", "text": "After how many years of continuous service does gratuity become payable?"}]}}}
req = urllib.request.Request(os.environ["AGENT"] + "/", data=json.dumps(body).encode(),
                             headers={"Authorization": "Bearer " + os.environ["AGENT_TOKEN"], "Content-Type": "application/json"})
task = json.loads(urllib.request.urlopen(req, timeout=180).read())["result"]
print(f"a {task['kind']}, state {task['status']['state']}, {len(task['history'])} messages in its history:")
for m in task["history"]:
    for p in m["parts"]:
        if p["kind"] == "text":
            print(f"  {m['role']:5} text      {p['text'][:66]!r}")
        elif p["metadata"].get("adk_type") == "function_call":
            print(f"  {m['role']:5} calls     {p['data']['name']}({', '.join(f'{k}={str(v)[:34]!r}' for k, v in p['data']['args'].items())})")
        else:
            r = p["data"]["response"]
            got = "an error" if r.get("isError") else f"{len(r.get('structuredContent', {}).get('citations', []))} citations"
            print(f"  {m['role']:5} receives  {p['data']['name']}: {got}")
print("the answer:", " ".join(p["text"] for a in task["artifacts"] for p in a["parts"] if p["kind"] == "text")[:84])
PY

"""

def step_01_the_task(session):
    """Run Do it: the task at this checkpoint.

    Do it: the task

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one task, and its history).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: a task, state completed, 4 messages in its history:
      user  text      'After how many years of continuous service does gratuity become pa'
      agent calls     retrieve(query='After how many years of continuous')
      agent receives  retrieve: 5 citations
      agent text      'Gratuity is payable after not less than five years of continuous s'
    the answer: Gratuity is payable after not less than five years of continuous service [1]. Source
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_what_the_lane_saw.
COMMANDS_02 = """sleep 20   # Cloud Logging needs a moment to show the lines
python - <<'PY'
import json, os, subprocess
def rows(service, flt):
    f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}" AND {flt} '
         f'AND timestamp>="{os.environ["SINCE123"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    return [e["jsonPayload"] for e in json.loads(out or "[]")]
print("documind-mcp - who asked it:")
for j in rows("documind-mcp", 'jsonPayload.event="mcp_call"'):
    print(f"  {j['tool']:15} tenant {j['tenant']:6} caller {j['caller'].split('@')[0]}")
print("documind-api - who it served:")
for j in rows("documind-api", 'jsonPayload.brain="mcp"'):
    print(f"  retrieve        tenant {j['tenant']:6} user   {j['user'].split('@')[0]}")
PY

"""

def step_02_what_the_lane_saw(session):
    """Run Do it: what the lane saw at this checkpoint.

    Do it: what the lane saw

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (who the lane saw).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-mcp - who asked it:
      retrieve        tenant acme   caller documind-agent-sa
    documind-api - who it served:
      retrieve        tenant acme   user   documind-mcp-sa
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_the_task),
        ('source_18', step_02_what_the_lane_saw),
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
