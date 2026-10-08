"""Lesson 5.4: The graph on your lane: one thread, a new thread, and a request to delete

Do it

Run order inside this file:
1. Do it (source window 17)

Prerequisites: demo_04_the_refuse_node_forced_to_fire.
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


# Original CLI workflow for step_01_the_graph_on_your_lane_one_thread_a_new_th.
COMMANDS_01 = """export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"
ask102() {   # one turn to the LangGraph brain as documind-ui-sa: $1 = the session, $2 = the question
TOKEN="$(tok "$CHAT")" S="$1" Q="$2" python - <<'PY'
import json, os, urllib.error, urllib.request
def text(answer):   # a chat service built before 24 September 2026 can send Gemini's content blocks instead of a string
    return answer if isinstance(answer, str) else "".join(p if isinstance(p, str) else p.get("text", "") for p in answer
                                                          if isinstance(p, str) or p.get("type") == "text")
body = json.dumps({"question": os.environ["Q"], "session_id": os.environ["S"], "brain": "langgraph"}).encode()
req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", data=body, method="POST",
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
try:
    a = json.load(urllib.request.urlopen(req, timeout=300))
    print(f"  [{a['session_id']}] tool_calls {a['tool_calls']}  refusals {a['refusals']}  {a['latency_ms']} ms")
    print(f"      {text(a['answer'])[:110]}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}  {e.read().decode(errors='replace')[:100]}")
PY
}
ask102 lesson102 "After how many years of continuous service does gratuity become payable?"
ask102 lesson102 "And how is it paid to a fixed-term employee under the Code on Social Security?"          # the same thread: "it" is gratuity
ask102 lesson102-new "And how is it paid to a fixed-term employee under the Code on Social Security?"      # a new thread: "it" is nothing
ask102 lesson102 "Delete the April invoice from ACME's documents."

"""

def step_01_the_graph_on_your_lane_one_thread_a_new_th(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (four turns to the LangGraph brain on your lane).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [lesson102] tool_calls ['retrieve']  refusals []  7310 ms
          Gratuity becomes payable after not less than five years of continuous service, under the Payment of Gratuity A
      [lesson102] tool_calls ['retrieve']  refusals []  6890 ms
          Under the Code on Social Security, 2020, a fixed-term employee is paid gratuity on a pro rata basis, without t
      [lesson102-new] tool_calls []  refusals []  2140 ms
          Could you tell me what you would like to know about? For example, gratuity or leave for fixed-term employees u
      [lesson102] tool_calls []  refusals []  1980 ms
          I can't delete documents - I can only search and read them. Removing the April invoice needs someone with acce
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_the_graph_on_your_lane_one_thread_a_new_th),
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
