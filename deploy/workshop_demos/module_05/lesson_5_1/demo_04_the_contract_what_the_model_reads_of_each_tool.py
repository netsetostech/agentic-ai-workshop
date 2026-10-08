"""Lesson 5.1: The contract: what the model reads of each tool

Do it

Run order inside this file:
1. Do it (source window 12)

Prerequisites: demo_03_the_chat_service_in_your_lane_s_region.
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


def step_01_the_contract_what_the_model_reads_of_each(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (what the model reads of each tool; reads the source, installs nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: retrieve(query: str, doc_type: str = 'all', top_k: int = 5)    hidden: runtime
          Retrieve grounded passages from DocuMind's corpus.
      calculate_processing_cost(total_pages: int, num_documents: int = 1, processing_type: str = 'standard')
          Estimate document processing cost in USD and INR.
      'express' refused: unknown tier 'express'; expected one of ['bulk', 'priority', 'standard']
    """
    import ast
    src = open("services/chat/tools.py", encoding="utf-8").read()
    for fn in ast.parse(src).body:
        if isinstance(fn, ast.FunctionDef) and any(getattr(d, "id", "") == "tool" for d in fn.decorator_list):
            a = fn.args.args
            dflt = [None] * (len(a) - len(fn.args.defaults)) + fn.args.defaults
            shown = [f"{x.arg}: {ast.unparse(x.annotation)}" + (f" = {ast.unparse(v)}" if v is not None else "") for x, v in zip(a, dflt) if x.arg != "runtime"]
            hidden = [x.arg for x in a if x.arg == "runtime"]
            print(f"  {fn.name}({', '.join(shown)})" + (f"    hidden: {hidden[0]}" if hidden else ""))
            print(f"      {ast.get_docstring(fn).splitlines()[0]}")
    from shared.documind_tools import calculate_processing_cost   # the function the chat's cost tool hands its arguments to
    try:
        calculate_processing_cost(283, processing_type="express")
    except ValueError as exc:
        print(f"  'express' refused: {exc}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_12', step_01_the_contract_what_the_model_reads_of_each),
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
