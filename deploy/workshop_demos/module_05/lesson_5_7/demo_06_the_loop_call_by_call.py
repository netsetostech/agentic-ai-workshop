"""Lesson 5.7: The loop, call by call

Do it

Run order inside this file:
1. Do it (source window 22)

Prerequisites: demo_05_four_cost_lines_from_rag_api_s_rows_and_the_chat_rows.
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


# Original CLI workflow for step_01_the_loop_call_by_call.
COMMANDS_01 = """GOOGLE_CLOUD_PROJECT="$PROJECT" RAG_API_URL="$API" RAG_TIMEOUT_S=90 \\
DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com" ~/graph-venv/bin/python - <<'PY'
import asyncio, json, logging, os, sys, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
sys.path[:0] = [".", "services/chat"]
from langgraph.checkpoint.memory import InMemorySaver
import brains, limits
from shared import prices                          # the chat service's prices: cost.py's, gemini-3.6-flash at 1.50 and 7.50 per 1M
Q = "After how many years of continuous service does gratuity become payable?"
for name in ("langchain", "langgraph", "adk"):
    b, meter = brains.build(name, InMemorySaver()), limits.Meter(model=brains.MODEL)
    cfg = {"configurable": {"thread_id": f"acme:lesson104:{name}"}}
    b.answer(Q, config=cfg, context={"tenant_id": "acme", "user_id": "lesson104", "assertion": "", "brain": name, "meter": meter})
    if name == "adk":                              # ADK keeps each model call's usage on the session's events
        s = asyncio.run(b.svc.get_session(app_name="documind", user_id="lesson104", session_id=cfg["configurable"]["thread_id"]))
        calls = [(u.prompt_token_count or 0, (u.candidates_token_count or 0) + (u.thoughts_token_count or 0), u.thoughts_token_count or 0)
                 for u in (e.usage_metadata for e in s.events) if u]
    else:                                          # LangChain keeps it on each AIMessage; output_tokens already counts thinking
        g = b.agent if name == "langchain" else b.graph
        calls = [(u["input_tokens"], u["output_tokens"], u.get("output_token_details", {}).get("reasoning", 0))
                 for u in (getattr(m, "usage_metadata", None) for m in g.get_state(cfg).values["messages"]) if u]
    print(f"  {name:9} " + "   ".join(f"call {k}: in {i:>5,} out {o:>4,}" for k, (i, o, t) in enumerate(calls, 1))
          + f"   (thinking {sum(c[2] for c in calls):,})")
    print(f"            the Meter, as the chat row keeps it: {meter.model_calls} model calls, in {meter.tokens_in:,},"
          f" out {meter.tokens_out:,}, Rs {prices.inr(meter.cost_usd):.4f}")
PY

"""

def step_01_the_loop_call_by_call(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's three agent brains on your machine, each model call counted).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: langchain call 1: in   401 out   31   call 2: in   931 out   20   (thinking 0)
                the Meter, as the chat row keeps it: 2 model calls, in 1,332, out 51, Rs 0.2023
      langgraph call 1: in   401 out   31   call 2: in   931 out   20   (thinking 0)
                the Meter, as the chat row keeps it: 2 model calls, in 1,332, out 51, Rs 0.2023
      adk       call 1: in   501 out   21   call 2: in 1,058 out   20   (thinking 0)
                the Meter, as the chat row keeps it: 2 model calls, in 1,559, out 41, Rs 0.2249
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_the_loop_call_by_call),
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
