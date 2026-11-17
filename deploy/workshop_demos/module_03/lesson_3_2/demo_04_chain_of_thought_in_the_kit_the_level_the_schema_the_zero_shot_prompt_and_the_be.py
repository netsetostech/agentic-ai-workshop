"""Lesson 3.2: Chain of thought in the kit: the level, the schema, the zero-shot prompt and the bench

Step 7 adds one rule. This cell builds the edit arm's SYSTEM with the bench's own edit_system(), from generator.py's text read as data, since importing generator.py builds a Gemini client for your lane. Then it hashes both prompts as the bench's header does, SYSTEM followed by DATED_RULE, the text lesson 3.6 binds to a version, and looks each hash up in the kit's registry of prompt versions. No model is called. The two test files run the bench on a scripted model and a stand-in lane, and the router's example swap on its scripted classifier. They check the level and the temperature sent, the rule edited in memory with generator.py untouched, the gate's verdict on every answer, the rupees, and the swap put back whatever happens. The pipe keeps the summary lines.

Run order inside this file:
1. Do it, offline: the edit arm's prompt, before you pay for it (source window 18)
2. Do it, offline: the bench's and the swap's own tests (source window 20)

Prerequisites: demo_03_the_chat_page_the_answer_to_a_join_and_the_thinking_it_billed.
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


def step_01_offline_the_edit_arm_s_prompt_before_you_p(session):
    """Run Do it, offline: the edit arm's prompt, before you pay for it at this checkpoint.

    Step 7 adds one rule. This cell builds the edit arm's SYSTEM with the bench's own edit_system(), from generator.py's text read as data, since importing generator.py builds a Gemini client for your lane. Then it hashes both prompts as the bench's header does, SYSTEM followed by DATED_RULE, the text lesson 3.6 binds to a version, and looks each hash up in the kit's registry of prompt versions. No model is called.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: no model is called).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: You are DocuMind, a retrieval-grounded assistant.
    Rules:
    1. Answer ONLY from the numbered context below. Never invent sources.
    2. Cite using [N] where N is the chunk number. Multiple chunks: [1,2].
    3. If the context does not contain the answer, set answerable=false and say so.
    4. Keep answers under 300 words unless asked for more.
    5. A quote is the clause that answers - at most twenty-five words, never a whole section.
    6. Show your working in the answer: name each fact the question needs and the [N] that states it, then combine them.
    kit  prompt sha256 543ed8060f1b177c...  documind-rag@v3
    edit prompt sha256 3f23ad647176d4fe...  no version names it
    """
    import ast, json, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, "evals")
    import prompt_bench
    source = open("services/rag-api/generator.py", encoding="utf-8").read()
    kit = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(source).body
           if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) in ("SYSTEM", "DATED_RULE")}
    RULE = "Show your working in the answer: name each fact the question needs and the [N] that states it, then combine them."
    edit = prompt_bench.edit_system(kit["SYSTEM"], add=[RULE])
    print(edit, end="")
    versions = json.load(open("services/rag-api/prompt_versions.json", encoding="utf-8"))["versions"]
    for arm, system in (("kit", kit["SYSTEM"]), ("edit", edit)):
        sha = prompt_bench.prompt_sha(system, kit["DATED_RULE"])
        print(f"{arm:4} prompt sha256 {sha[:16]}...  {next((v for v, s in versions.items() if s == sha), 'no version names it')}")

# Original CLI workflow for step_02_offline_the_bench_s_and_the_swap_s_own_tes.
COMMANDS_02 = """for t in test_prompt_bench.py test_route_exemplars.py; do
  python -m unittest discover -s evals/tests -p "$t" 2>&1 | grep -E "^(Ran|OK|FAILED)" | sed -E "s/ in [0-9.]+s$//"
done

"""

def step_02_offline_the_bench_s_and_the_swap_s_own_tes(session):
    """Run Do it, offline: the bench's and the swap's own tests at this checkpoint.

    The two test files run the bench on a scripted model and a stand-in lane, and the router's example swap on its scripted classifier. They check the level and the temperature sent, the rule edited in memory with generator.py untouched, the gate's verdict on every answer, the rupees, and the swap put back whatever happens. The pipe keeps the summary lines.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the kit's own tests: a scripted model and a stand-in lane; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Ran 21 tests
    OK
    Ran 9 tests
    OK
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_offline_the_edit_arm_s_prompt_before_you_p),
        ('source_20', step_02_offline_the_bench_s_and_the_swap_s_own_tes),
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
