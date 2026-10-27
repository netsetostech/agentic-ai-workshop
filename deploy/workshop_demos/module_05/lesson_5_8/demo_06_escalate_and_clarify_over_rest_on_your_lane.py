"""Lesson 5.8: Escalate and clarify over REST, on your lane

The cell sends the gate's own request for a person on one session, then one of its near misses, "How do I contact HR about payroll?", which gate() reads as a question about a process and lets through. Then it raises the case the first reply offered and sends it with a token. Last, it withdraws the case as the person who raised it. It keeps the case's id in ~/lesson108_case.txt for step 7. Three turns. The handbook answers "What is my notice period?" two ways: 60 days for a confirmed employee at grade E3 or above (NP-03), and 15 days during probation (PB-02). The second turn gives, on the same session, the fact the first lacked. The third sends the same reply in a new session.

Run order inside this file:
1. Do it: escalate (source window 35)
2. Do it: clarify (source window 37)

Prerequisites: demo_05_pause_refuse_approve_and_resume_on_your_machine.
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


# Original CLI workflow for step_01_escalate.
COMMANDS_01 = """TOKEN="$(etok evalacme)" python - <<'PY'
import json, os, textwrap, urllib.error, urllib.request, uuid, warnings
from datetime import datetime
warnings.filterwarnings("ignore", category=UserWarning)
def call(path, body=None):
    \"\"\"One call to the chat service as documind-evalacme-sa: the status and the JSON it answers.\"\"\"
    req = urllib.request.Request(os.environ["CHAT"] + path, method="GET" if body is None else "POST",
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
def show(text):
    \"\"\"An answer on indented lines of at most 100 characters.\"\"\"
    print(textwrap.fill(" ".join(str(text).split()), 100, initial_indent="    ", subsequent_indent="    "))
def span(a, b):
    \"\"\"The time from one ISO timestamp to another.\"\"\"
    return str(datetime.fromisoformat(b) - datetime.fromisoformat(a))
offer = None
for q in ("Escalate this to a human please", "How do I contact HR about payroll?"):
    s, a = call("/v1/chat", {"question": q, "session_id": "lesson108-esc", "brain": "langgraph"})
    print(f"  {q}")
    print(f"    {s}  brain {a['brain']}  tool_calls {a['tool_calls']}  model_calls {a['limits']['model_calls']}"
          f"  Rs {a['limits']['cost_inr']}  case_offer {a.get('case_offer')}")
    show(a["answer"])
    offer = offer or a.get("case_offer")
s, d = call("/v1/cases", {"case_type": offer["case_type"], "summary": "Lesson 5.8 test: please call me about my notice period."})
print(f"  draft    {s}  {d['status']} in {d['queue']} ({d['owner']['queue_name']}),"
      f" expires {span(d['created_at'], d['expire_at'])} after it was made")
s, c = call(f"/v1/cases/{d['case_id']}/confirm", {"token": "lesson108-" + uuid.uuid4().hex[:12]})
print(f"  confirm  {s}  {c['status']}, due {span(c['opened_at'], c['due_at'])} after it opened: {c['sla_basis']}")
s, w = call(f"/v1/cases/{d['case_id']}/cancel", {})
print(f"  cancel   {s}  {w['status']}, by the person who raised it")
open(os.path.expanduser("~/lesson108_case.txt"), "w").write(d["case_id"])
PY

"""

def step_01_escalate(session):
    """Run Do it: escalate at this checkpoint.

    The cell sends the gate's own request for a person on one session, then one of its near misses, "How do I contact HR about payroll?", which gate() reads as a question about a process and lets through. Then it raises the case the first reply offered and sends it with a token. Last, it withdraws the case as the person who raised it. It keeps the case's id in ~/lesson108_case.txt for step 7.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a request for a person and a near miss, as documind-evalacme-sa; then the case).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/escalate.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_clarify.
COMMANDS_02 = """TOKEN="$(etok evalacme)" python - <<'PY'
import json, os, textwrap, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
def call(path, body=None):
    \"\"\"One call to the chat service as documind-evalacme-sa: the status and the JSON it answers.\"\"\"
    req = urllib.request.Request(os.environ["CHAT"] + path, method="GET" if body is None else "POST",
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
def show(text):
    \"\"\"An answer on indented lines of at most 100 characters.\"\"\"
    print(textwrap.fill(" ".join(str(text).split()), 100, initial_indent="    ", subsequent_indent="    "))
for session, q in (("lesson108", "What is my notice period?"), ("lesson108", "I am still on probation."), ("lesson108-new", "I am still on probation.")):
    s, a = call("/v1/chat", {"question": q, "session_id": session, "brain": "langgraph"})
    print(f"  [{session}] {q}")
    print(f"    {s}  tool_calls {a['tool_calls']}  model_calls {a['limits']['model_calls']}  Rs {a['limits']['cost_inr']}"
          f"  citations {[c['n'] for c in a['citations']]}")
    show(a["answer"])
PY

"""

def step_02_clarify(session):
    """Run Do it: clarify at this checkpoint.

    Three turns. The handbook answers "What is my notice period?" two ways: 60 days for a confirmed employee at grade E3 or above (NP-03), and 15 days during probation (PB-02). The second turn gives, on the same session, the fact the first lacked. The third sends the same reply in a new session.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a question, the reply on the same session, the reply in a new session).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/clarify.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_35', step_01_escalate),
        ('source_37', step_02_clarify),
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
