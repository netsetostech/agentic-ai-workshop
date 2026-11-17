"""Lesson 5.1: The loop: the model chooses its tools

The scripted model always asks for both searches. Whether Gemini does is the model's choice. This cell makes the first model call of a turn by hand: the brains' own model from shared/profile.py, the kit's two tools bound to it, the system prompt, and the same two-part question. It prints the tool calls in the one message that comes back, then the tokens and the rupees. It is one call to gemini-3.6-flash on your project, under a rupee. No tool runs, and rag-api is not called.

Run order inside this file:
1. Optional: does Gemini ask for two at once? (source window 30)

Prerequisites: demo_07_the_loop_the_model_chooses_its_tools.
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


# Original CLI workflow for step_01_optional_does_gemini_ask_for_two_at_once.
COMMANDS_01 = """GOOGLE_CLOUD_PROJECT="$PROJECT" ~/graph-venv/bin/python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
from langchain_core.messages import HumanMessage, SystemMessage
import brains, limits, tools
from shared import prices
from shared.profile import build_llm
llm = build_llm().bind_tools(tools.TOOLS)         # the brains' model, gemini-3.6-flash on global, with the kit's two tools
msg = llm.invoke([SystemMessage(content=brains.SYSTEM),
                  HumanMessage(content="How long is my notice period, and how much earned leave is encashed when I leave?")])
print(f"  {brains.MODEL}'s first message: {len(msg.tool_calls)} tool call(s)")
for c in msg.tool_calls:
    print(f"    {c['name']}(" + ", ".join(f"{k}={v!r}" for k, v in c["args"].items()) + ")")
tin, tout, _ = limits.usage_of(msg)               # output counts the thinking tokens
print(f"  {tin} tokens in, {tout} out: Rs {prices.inr(prices.usd(brains.MODEL, tin, tout)):.2f}")
PY

"""

def step_01_optional_does_gemini_ask_for_two_at_once(session):
    """Run Optional: does Gemini ask for two at once? at this checkpoint.

    The scripted model always asks for both searches. Whether Gemini does is the model's choice. This cell makes the first model call of a turn by hand: the brains' own model from shared/profile.py, the kit's two tools bound to it, the system prompt, and the same two-part question. It prints the tool calls in the one message that comes back, then the tokens and the rupees. It is one call to gemini-3.6-flash on your project, under a rupee. No tool runs, and rag-api is not called.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit (one Gemini call with the kit's two tools; no tool runs; under a rupee).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/parallel_live.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_30', step_01_optional_does_gemini_ask_for_two_at_once),
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
