"""Lesson 5.1: The loop: the model chooses its tools

Do it

Run order inside this file:
1. Do it (source window 22)

Prerequisites: demo_06_the_direct_brain_one_retrieve_no_loop.
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


# Original CLI workflow for step_01_the_loop_the_model_chooses_its_tools.
COMMANDS_01 = """chat10 langchain "After how many years of continuous service does gratuity become payable?"
chat10 langchain "The ACME handbook has 283 pages. What would processing it cost at the priority tier?"
chat10 direct "The ACME handbook has 283 pages. What would processing it cost at the priority tier?"

"""

def step_01_the_loop_the_model_chooses_its_tools(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the LangChain loop on the same question, then a cost question on both brains).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: langchain tool_calls ['retrieve']  refusals []  citations 5 n [1, 2, 3, 4, 5]  7240 ms
          After five years of continuous service, under the Payment of Gratuity Act, 1972 [1].
      langchain tool_calls ['retrieve', 'calculate_processing_cost']  refusals []  citations 3 n [1, 2, 3]  11350 ms
          The handbook has 283 pages [1]. At the priority tier (USD 0.12 a page) they cost USD 33.96, abou
      direct    tool_calls ['retrieve']  refusals []  citations 3  3420 ms
          The documents give no per-page price for processing the handbook; the April invoice bills priori
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_the_loop_the_model_chooses_its_tools),
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
