"""Lesson 6.1: On your lane: the model's own counter, and the probe

Whether count_tokens on location global takes the declarations and the system instruction at all was not known when the kit was written. The probe settles it before any count on this page is trusted, for both forms of declaration: LangChain's parameters on the LangGraph brain, and ADK's parametersJsonSchema. The cell prints only each run's probe. Step 7 shows the whole of each run.

Run order inside this file:
1. Do it: the probe (source window 25)

Prerequisites: demo_05_offline_one_turn_split_by_source_for_rs_0.
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


# Original CLI workflow for step_01_the_probe.
COMMANDS_01 = """for b in langgraph adk; do
  echo "== BRAIN=$b"; make context-sources PROJECT=$PROJECT BRAIN=$b | sed -n '/^probe (/,$p'
done

"""

def step_01_the_probe(session):
    """Run Do it: the probe at this checkpoint.

    Whether count_tokens on location global takes the declarations and the system instruction at all was not known when the kit was written. The probe settles it before any count on this page is trusted, for both forms of declaration: LangChain's parameters on the LangGraph brain, and ADK's parametersJsonSchema. The cell prints only each run's probe. Step 7 shows the whole of each run.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two real turns on your lane, a few rupees; only each run's probe is printed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == BRAIN=langgraph
    [awaiting the author's run: data/probe_langgraph.txt]
    == BRAIN=adk
    [awaiting the author's run: data/probe_adk.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_the_probe),
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
