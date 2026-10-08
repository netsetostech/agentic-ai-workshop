"""Lesson 6.5: One conversation, four brains, two sessions

Do it

Run order inside this file:
1. Do it (source window 16)

Prerequisites: demo_04_the_memory_checkpointer_and_the_line_it_logs.
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


# Original CLI workflow for step_01_one_conversation_four_brains_two_sessions.
COMMANDS_01 = """export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"
CHAT_TOKEN="$(tok "$CHAT")" python - <<'PY'
import json, os, urllib.error, urllib.request
def text(answer):   # a chat service built before 24 September 2026 can send Gemini's content blocks instead of a string
    return answer if isinstance(answer, str) else "".join(p if isinstance(p, str) else p.get("text", "") for p in answer
                                                          if isinstance(p, str) or p.get("type") == "text")
S = {"A": f"lesson111-{os.getpid()}", "B": f"lesson111-{os.getpid()}-b"}   # two fresh sessions each run
TURNS = [("langchain", "A", "Remember this word for me: tamarind. Just confirm you have it."),
         ("langgraph", "A", "Which word did I ask you to remember?"),
         ("adk", "A", "Which word did I ask you to remember?"),
         ("direct", "A", "Which word did I ask you to remember?"),
         ("langchain", "B", "Which word did I ask you to remember?"),
         ("langchain", "B", "After how many years of continuous service does gratuity become payable?")]
for brain, s, q in TURNS:
    req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", method="POST",
                                 data=json.dumps({"question": q, "session_id": S[s], "brain": brain}).encode(),
                                 headers={"Authorization": "Bearer " + os.environ["CHAT_TOKEN"], "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            b = json.loads(r.read())
        said = " ".join(text(b["answer"]).split())
        print(f"  {brain:9} session {s}  tools {str(b['tool_calls']):13} tamarind {'yes' if 'tamarind' in said.lower() else 'no '}  {said[:40]!r}")
    except urllib.error.HTTPError as e:
        print(f"  {brain:9} session {s}  HTTP {e.code}  {e.read()[:80]!r}")
PY

"""

def step_01_one_conversation_four_brains_two_sessions(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one conversation, four brains, two sessions).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: langchain session A  tools []            tamarind yes  "Got it: tamarind. I'll keep it for this "
      langgraph session A  tools []            tamarind yes  'You asked me to remember "tamarind".'
      adk       session A  tools []            tamarind no   "I don't have a word from you in this con"
      direct    session A  tools ['retrieve']  tamarind no   'The documents do not say which word you '
      langchain session B  tools []            tamarind no   "I don't have a word from you in this con"
      langchain session B  tools ['retrieve']  tamarind no   'Gratuity becomes payable after not less '
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_one_conversation_four_brains_two_sessions),
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
