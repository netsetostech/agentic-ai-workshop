"""Lesson 6.7: A conversation across a redeploy

Do it

Run order inside this file:
1. Do it (source window 14)

Prerequisites: demo_03_isolation_on_the_kit_s_own_app.
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


# Original CLI workflow for step_01_a_conversation_across_a_redeploy.
COMMANDS_01 = """export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"
CHAT_TOKEN="$(tok "$CHAT")" python - <<'PY'
import json, os, subprocess, time, urllib.request
def text(answer):   # a chat service built before 24 September 2026 can send Gemini's content blocks instead of a string
    return answer if isinstance(answer, str) else "".join(p if isinstance(p, str) else p.get("text", "") for p in answer
                                                          if isinstance(p, str) or p.get("type") == "text")
P, R, CHAT = os.environ["PROJECT"], os.environ["REGION"], os.environ["CHAT"]
def gc(*a):
    return subprocess.run(["gcloud", *a, "--project", P, "--region", R, "--quiet"], capture_output=True, text=True, check=True).stdout.strip()
def serving():
    return gc("run", "services", "describe", "documind-chat", "--format", "value(status.latestReadyRevisionName)")
def ask(brain, session, question):
    req = urllib.request.Request(CHAT + "/v1/chat", method="POST",
                                 data=json.dumps({"question": question, "session_id": session, "brain": brain}).encode(),
                                 headers={"Authorization": "Bearer " + os.environ["CHAT_TOKEN"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return " ".join(text(json.loads(r.read())["answer"]).split())
state = {"session": f"lesson113-{os.getpid()}", "before": serving()}
print(f"serving {state['before']}")
for brain in ("langchain", "adk"):
    said = ask(brain, f"{state['session']}-{brain}", "Remember this word for me: saffron. Just confirm you have it.")
    print(f"  {brain:9} {state['session']}-{brain:9}  {said[:44]!r}")
state["redeployed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
gc("run", "services", "update", "documind-chat", "--update-env-vars", f"LESSON113_RESTART={int(time.time())}")   # a new revision
gc("run", "services", "update-traffic", "documind-chat", "--to-latest")
state["after"] = serving()
print(f"serving {state['after']}, redeployed at {state['redeployed_at']}Z")
for brain in ("langchain", "adk"):
    said = ask(brain, f"{state['session']}-{brain}", "Which word did I ask you to remember?")
    print(f"  {brain:9} {state['session']}-{brain:9}  saffron {'yes' if 'saffron' in said.lower() else 'no '}  {said[:34]!r}")
json.dump(state, open(os.path.expanduser("~/lesson113.json"), "w"))
PY

"""

def step_01_a_conversation_across_a_redeploy(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a word, a redeploy, the word again).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: serving documind-chat-00007-x4q
      langchain lesson113-4242-langchain  "Got it: saffron. I'll keep it for this conve"
      adk       lesson113-4242-adk        "Got it: saffron. I'll keep it for this conve"
    serving documind-chat-00008-m2k, redeployed at 2026-09-23T11:20:41Z
      langchain lesson113-4242-langchain  saffron yes  'You asked me to remember "saffron"'
      adk       lesson113-4242-adk        saffron no   "I don't have a word from you in th"
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_14', step_01_a_conversation_across_a_redeploy),
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
