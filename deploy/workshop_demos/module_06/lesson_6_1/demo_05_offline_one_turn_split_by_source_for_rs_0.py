"""Lesson 6.1: Offline: one turn split by source, for Rs 0

Do it

Run order inside this file:
1. Do it (source window 20)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_offline_one_turn_split_by_source_for_rs_0.
COMMANDS_01 = """make context-sources OFFLINE=1 BRAIN=langgraph

"""

def step_01_offline_one_turn_split_by_source_for_rs_0(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a scripted model and the kit's corpus on your machine: no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: context sources: one turn on brain langgraph, tenant acme, a fresh thread; each search sends the model's top_k, or tools.py's default of 5
      OFFLINE=1: a scripted model at the google-genai boundary (the brain, its adapter, tools and limits run
      as on the lane) and the Rs 0 lane's retrieve over evals/corpus: no network, no credential, nothing
      billed. Tokens are estimated: a quarter of the characters each part carries (rag-api's estimator,
      context_budget.estimate_tokens), so the residual is 0. On your lane count_tokens counts each source.
    question: After how many years of continuous service is gratuity payable?
      sent with every call: a system prompt of 426 characters, the brain's own
      a
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_offline_one_turn_split_by_source_for_rs_0),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
