"""Lesson 5.8: The rows, the case and your role, read directly

The chat service's chat and desk_gate rows since step 3, from Cloud Logging. The cell names each account by the part of its email before the @. make cases lists acme's open cases, soonest due first. Then the cell reads step 6's case and your role document from Firestore.

Run order inside this file:
1. Do it: the log rows (source window 39)
2. Do it: the case and your role (source window 41)

Prerequisites: demo_06_escalate_and_clarify_over_rest_on_your_lane.
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


def step_01_the_log_rows(session):
    """Run Do it: the log rows at this checkpoint.

    The chat service's chat and desk_gate rows since step 3, from Cloud Logging. The cell names each account by the part of its email before the @.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the chat service's chat and desk_gate rows since step 3; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rows.txt]
    """
    import json, os, subprocess, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND '
         f'(jsonPayload.event="chat" OR jsonPayload.event="desk_gate") AND timestamp>="{os.environ["SINCE108"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    for e in json.loads(out or "[]"):
        j = e["jsonPayload"]
        who = str(j.get("user")).split("@")[0]
        if j["event"] == "desk_gate":
            print(f"  desk_gate  user {who:22} class {j['class']}  method {j['method']}  rules {j['rules_version']}")
        else:
            print(f"  chat       user {who:22} brain {j['brain']}  session {j['session_id']}  tool_calls {j['tool_calls']}"
                  f"  model_calls {j['model_calls']}  tokens {j['tokens_in']}/{j['tokens_out']}  cost_usd {j['cost_usd']}")

# Original CLI workflow for step_02_the_case_and_your_role.
COMMANDS_02 = """make cases PROJECT="$PROJECT" TENANT=acme
python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
db = firestore.Client(project=os.environ["PROJECT"])
cid = open(os.path.expanduser("~/lesson108_case.txt")).read().strip()
c = db.collection("cases").document(cid).get().to_dict()
print(f"  cases/{cid}")
print(f"    {c['case_type']} {c['status']} in {c['queue']}, source {c['source']}, via {c['via']}, opened {c['opened_at'] is not None}")
print(f"    summary {c['summary']!r}  audit_pending {c['audit_pending']}  token_sha256 {len(c['token_sha256'])} hex digits")
me = os.environ["ME"].lower()
r = db.collection("tenants").document("acme").collection("roles").document(me).get().to_dict()
print(f"  tenants/acme/roles/{me.split('@')[0]}@...: {r['roles']}, set by {r['set_by'].split('@')[0]}@...")
PY

"""

def step_02_the_case_and_your_role(session):
    """Run Do it: the case and your role at this checkpoint.

    make cases lists acme's open cases, soonest due first. Then the cell reads step 6's case and your role document from Firestore.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's open cases, then step 6's case and your role document, from Firestore).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/records.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_39', step_01_the_log_rows),
        ('source_41', step_02_the_case_and_your_role),
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
