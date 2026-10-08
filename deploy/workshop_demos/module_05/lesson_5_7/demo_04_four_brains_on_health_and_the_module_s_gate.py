"""Lesson 5.7: Four brains on /health, and the module's gate

Do it

Run order inside this file:
1. Do it (source window 18)

Prerequisites: demo_03_two_adapters_over_one_tool_side_by_side.
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


# Original CLI workflow for step_01_four_brains_on_health_and_the_module_s_gat.
COMMANDS_01 = """export CHAT="https://documind-chat-$NUMBER.$REGION.run.app" SINCE104="$(date -u +%FT%TZ)"
curl -s -H "Authorization: Bearer $(tok "$CHAT")" "$CHAT/health"; echo
make smoke-chat PROJECT="$PROJECT" REGION="$REGION"   # the module's gate: four brains, one question, the outsider refused

"""

def step_01_four_brains_on_health_and_the_module_s_gat(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (/health, then the module's gate).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"status":"ok","profile":"gcp","brains":["langchain","langgraph","adk","direct"],"default_brain":"langchain","limits":{"max_model_calls":12,"budget_inr":5.0,"deadline_s":100.0,"model_timeout_s":30.0,"model_attempts":2,"min_model_s":5.0,"tool_budgets_s":{"retrieve":95.0,"calculate_processing_cost":10}}}
      DocuMind chat - live smoke test
      target: https://documind-chat-NUMBER.asia-south1.run.app
      --------------------------------------------------------
      [PASS] health  profile=gcp default=langchain limits=12 calls, Rs 5.0, 100.0 s
      [PASS] brain direct  3120 ms  tools=['retrieve']  citations=5  calls=0 Rs 0.3699  'Gratuity becomes payable after not less than five years of c'
      [PASS] brain la
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_four_brains_on_health_and_the_module_s_gat),
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
