"""Lesson 3.6: The change in memory: rule 5 weakened on the bench, and the sha256 it would register

Do it: the weakened rule, on the same rows

Run order inside this file:
1. Do it: the weakened rule, on the same rows (source window 34)

Prerequisites: demo_05_the_prompt_s_version_the_label_the_text_its_sha256_and_the_check.
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


# Original CLI workflow for step_01_the_weakened_rule_on_the_same_rows.
COMMANDS_01 = """make bench PROJECT="$PROJECT" BENCH_ARGS="--from-report evals/reports/quotes36.json --no-baseline --drop-rule 5 --add-rule 'A quote sums up the clause that answers - at most fifteen words, in plain language.'"

"""

def step_01_the_weakened_rule_on_the_same_rows(session):
    """Run Do it: the weakened rule, on the same rows at this checkpoint.

    Do it: the weakened rule, on the same rows

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (ten pool reads, then ten answers from the kit's generate() in your shell: a few rupees).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/bench_v4.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_the_weakened_rule_on_the_same_rows),
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
