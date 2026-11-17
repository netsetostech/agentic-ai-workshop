"""Lesson 3.3: Why the fix stays in memory: the served prompt is the trained prompt

Do it: the two copies, and the kit's own test

Run order inside this file:
1. Do it: the two copies, and the kit's own test (source window 41)

Prerequisites: demo_07_one_rule_per_row_in_the_bench_with_the_refusal_rows_beside_it.
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


# Original CLI workflow for step_01_the_two_copies_and_the_kit_s_own_test.
COMMANDS_01 = """python - <<'PY'
import ast, warnings
warnings.filterwarnings("ignore", category=UserWarning)


def system_of(path):
    \"\"\"The SYSTEM string a file sets at module level, read by AST: neither file is imported.\"\"\"
    for node in ast.parse(open(path, encoding="utf-8").read()).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "SYSTEM":
            return ast.literal_eval(node.value)


served, trained = system_of("services/rag-api/generator.py"), system_of("evals/make_trainset.py")
print(f"generator.py's SYSTEM: {len(served)} characters; make_trainset.py's: {len(trained)}; byte for byte equal: {served == trained}")
PY
python -m unittest discover -s commands/tests -p test_prompt_versions.py -k make_trainset 2>&1 | tail -1

"""

def step_01_the_two_copies_and_the_kit_s_own_test(session):
    """Run Do it: the two copies, and the kit's own test at this checkpoint.

    Do it: the two copies, and the kit's own test

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two files read as text, then the kit's own test; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: generator.py's SYSTEM: 423 characters; make_trainset.py's: 423; byte for byte equal: True
    OK
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_41', step_01_the_two_copies_and_the_kit_s_own_test),
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
