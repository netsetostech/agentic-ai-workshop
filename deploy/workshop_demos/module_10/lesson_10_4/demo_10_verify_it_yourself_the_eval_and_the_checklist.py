"""Lesson 10.4: Verify it yourself: the eval and the checklist

make route-eval posts every scored dev row to /v1/route as the row's own eval account: 187 rows, with the 20 rows of the prompt's example groups left out, since the prompt has seen them. Each handbook, statute and denial row, 173 of them, goes to /v1/desk too, for its answer and citations. The report gives each rate with its interval, the confusion matrix, whether answers cite only the desk's classes and the caller's company, the router's cost, and the p50 and p95 of the routing and of the answers. The dev gates are a route accuracy of 95% or more, each desk's recall at 90% or more, and every escalation row escalated; a FAIL line names a gate missed. If the Desk answers 429, more than 120 routes a minute from one account, the eval waits the minute out and tries again, up to three times. Do it: the test split The chat service keeps the gate lesson 5.7 set: make smoke-chat PROJECT=documind-ai-YOUR-ID, the four brains and the outsider. The routed Desk sits beside /v1/chat, not in front of it, so every brain answers as before.

Run order inside this file:
1. Do it: the router's eval, dev split (source window 79)
2. Do it: the test split (source window 81)
3. Do it: Module 5's gate (source window 83)

Prerequisites: demo_08_the_shadow_the_rows_and_the_log.
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


# Original CLI workflow for step_01_the_router_s_eval_dev_split.
COMMANDS_01 = """make route-eval PROJECT="$PROJECT" REGION="$REGION" SPLIT=dev

"""

def step_01_the_router_s_eval_dev_split(session):
    """Run Do it: the router's eval, dev split at this checkpoint.

    make route-eval posts every scored dev row to /v1/route as the row's own eval account: 187 rows, with the 20 rows of the prompt's example groups left out, since the prompt has seen them. Each handbook, statute and denial row, 173 of them, goes to /v1/desk too, for its answer and citations. The report gives each rate with its interval, the confusion matrix, whether answers cite only the desk's classes and the caller's company, the router's cost, and the p50 and p95 of the routing and of the answers. The dev gates are a route accuracy of 95% or more, each desk's recall at 90% or more, and every escalation row escalated; a FAIL line names a gate missed. If the Desk answers 429, more than 120 routes a minute from one account, the eval waits the minute out and tries again, up to three times.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every dev row through the deployed Desk, one call after another: 187 decisions and 173 paid answers; the report prints what the router cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: live: https://documind-chat-NUMBER.asia-south1.run.app, arm B (the routed Desk), split dev: 187 rows scored, 20 left out (the groups of the prompt's examples)
    arm B (the routed Desk)
    split dev
      top-1 route accuracy          N/187 = NN.N% [NN.N%, NN.N%]
        recall handbook             N/44 = NN.N% [NN.N%, NN.N%]
        recall statute              N/129 = NN.N% [NN.N%, NN.N%]
        recall case                 0/0 (no rows)
        recall clarify              0/0 (no rows)
        recall out_of_scope         N/14 = NN.N% [NN.N%, NN.N%]
      confusion (rows: expected; columns: predicted)
                           handbook      statute         case      clarify out_of_scope        other
        handbook               
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_test_split.
COMMANDS_02 = """make route-eval PROJECT="$PROJECT" REGION="$REGION" SPLIT=test

"""

def step_02_the_test_split(session):
    """Run Do it: the test split at this checkpoint.

    Do it: the test split

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the test split: it has no rows yet).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: live: https://documind-chat-NUMBER.asia-south1.run.app, arm B (the routed Desk), split test: 0 rows scored, 0 left out (the groups of the prompt's examples)
    arm B (the routed Desk)
    split test
      top-1 route accuracy          0/0 (no rows)
        recall handbook             0/0 (no rows)
        recall statute              0/0 (no rows)
        recall case                 0/0 (no rows)
        recall clarify              0/0 (no rows)
        recall out_of_scope         0/0 (no rows)
      confusion (rows: expected; columns: predicted)
                           handbook      statute         case      clarify out_of_scope        other
        handbook                  0            0            0            0            0   
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_module_5_s_gate.
COMMANDS_03 = """make smoke-chat PROJECT="$PROJECT" REGION="$REGION"   # Module 5's gate, as in lesson 5.7

"""

def step_03_module_5_s_gate(session):
    """Run Do it: Module 5's gate at this checkpoint.

    The chat service keeps the gate lesson 5.7 set: make smoke-chat PROJECT=documind-ai-YOUR-ID, the four brains and the outsider. The routed Desk sits beside /v1/chat, not in front of it, so every brain answers as before.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Module 5's gate: four brains, one question, the outsider refused).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DocuMind chat - live smoke test
      target: https://documind-chat-NUMBER.asia-south1.run.app
      --------------------------------------------------------
      [PASS] health  profile=gcp default=langchain limits=12 calls, Rs 5.0, 100.0 s
      [PASS] brain direct  NNNN ms  tools=['retrieve']  citations=N  calls=0 Rs N.NNNN  '...'
      [PASS] brain langchain  NNNN ms  tools=['retrieve']  citations=N  calls=N Rs N.NNNN  '...'
      [PASS] brain langgraph  NNNN ms  tools=['retrieve']  citations=N  calls=N Rs N.NNNN  '...'
      [PASS] brain adk  NNNN ms  tools=['retrieve']  citations=N  calls=N Rs N.NNNN  '...'
      [PASS] outsider refused  status=403 not a member of any tenant
      ----------------------------------------
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_79', step_01_the_router_s_eval_dev_split),
        ('source_81', step_02_the_test_split),
        ('source_83', step_03_module_5_s_gate),
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
