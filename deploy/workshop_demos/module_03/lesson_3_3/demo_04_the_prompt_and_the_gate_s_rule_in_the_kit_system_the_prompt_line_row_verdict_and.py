"""Lesson 3.3: The prompt and the gate's rule in the kit: SYSTEM, the prompt line, row_verdict() and the passage checks

The cell reads SYSTEM and DATED_RULE from generator.py as text, with Python's own parser, and splits SYSTEM into its rules with the bench's own reader, rules_of(). It imports no Google library and calls nothing.

Run order inside this file:
1. Do it: SYSTEM's rules, as the bench will number them (source window 16)

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


def step_01_system_s_rules_as_the_bench_will_number_th(session):
    """Run Do it: SYSTEM's rules, as the bench will number them at this checkpoint.

    The cell reads SYSTEM and DATED_RULE from generator.py as text, with Python's own parser, and splits SYSTEM into its rules with the bench's own reader, rules_of(). It imports no Google library and calls nothing.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads generator.py as text; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: SYSTEM, as the bench numbers it: You are DocuMind, a retrieval-grounded assistant. / Rules:
      1. Answer ONLY from the numbered context below. Never invent sources.
      2. Cite using [N] where N is the chunk number. Multiple chunks: [1,2].
      3. If the context does not contain the answer, set answerable=false and say so.
      4. Keep answers under 300 words unless asked for more.
      5. A quote is the clause that answers - at most twenty-five words, never a whole section.
    DATED_RULE, added only when a packed passage carries an effective date:
      6. Some sources carry an effective date. Where sources disagree, follow the one with the latest effective date, cite it, and say which source you followed and
    """
    import ast, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, "evals")
    import prompt_bench as bench            # the bench's own reader of SYSTEM: the standard library, no Google client
    
    PATH = "services/rag-api/generator.py"   # read as text, never imported
    K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(open(PATH, encoding="utf-8").read()).body
         if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("SYSTEM", "DATED_RULE")}
    head, rules = bench.rules_of(K["SYSTEM"])
    print("SYSTEM, as the bench numbers it:", " / ".join(head))
    for n, rule in enumerate(rules, 1):
        print(f"  {n}. {rule}")
    print("DATED_RULE, added only when a packed passage carries an effective date:")
    print("  " + K["DATED_RULE"].strip())
    print("sha256 of SYSTEM then DATED_RULE:", bench.prompt_sha(K["SYSTEM"], K["DATED_RULE"]))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_system_s_rules_as_the_bench_will_number_th),
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
