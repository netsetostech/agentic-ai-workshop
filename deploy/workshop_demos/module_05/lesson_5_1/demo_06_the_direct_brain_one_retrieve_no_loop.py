"""Lesson 5.1: The direct brain: one retrieve(), no loop

Do it

Run order inside this file:
1. Do it (source window 19)

Prerequisites: demo_05_the_one_retrieve_from_your_shell.
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


# Original CLI workflow for step_01_the_direct_brain_one_retrieve_no_loop.
COMMANDS_01 = """chat10() {   # one /v1/chat turn as documind-ui-sa: $1 = the brain, $2 = the question
TOKEN="$(tok "$CHAT")" B="$1" Q="$2" python - <<'PY'
import json, os, urllib.error, urllib.request
def text(answer):   # a chat service built before 24 September 2026 can send Gemini's content blocks instead of a string
    return answer if isinstance(answer, str) else "".join(p if isinstance(p, str) else p.get("text", "") for p in answer
                                                          if isinstance(p, str) or p.get("type") == "text")
body = json.dumps({"question": os.environ["Q"], "session_id": "lesson101-" + os.environ["B"], "brain": os.environ["B"]}).encode()
req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", data=body, method="POST",
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
try:
    a = json.load(urllib.request.urlopen(req, timeout=300))
    n = [c["n"] for c in a.get("citations", []) if "n" in c]   # an agent brain numbers this turn's citations from 1
    print(f"  {a['brain']:9} tool_calls {a['tool_calls']}  refusals {a['refusals']}  citations {len(a.get('citations', []))}"
          + (f" n {n}" if n else "") + f"  {a['latency_ms']} ms")
    print(f"      {text(a['answer'])[:96]}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}  {e.read().decode(errors='replace')[:100]}")
PY
}
chat10 direct "After how many years of continuous service does gratuity become payable?"

"""

def step_01_the_direct_brain_one_retrieve_no_loop(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a small chat function, and the direct brain).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: direct    tool_calls ['retrieve']  refusals []  citations 5  3180 ms
          Gratuity is payable on termination after not less than five years of continuous service [1].
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_the_direct_brain_one_retrieve_no_loop),
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
