"""Lesson 12.4: A person accepts it: v4, and its golden row

The next version, written with who and when, the golden row pasted by lesson 4.1's method, and the files improve.py refuses to write. Read the proposal, then accept it. REVIEWER= is you: a name or an email, on one line. It is written into prompt_rules.json and your fork's history, so use the name you sign your commits with. Accept checks everything again: the proposal must be one make improve wrote, built on the latest version, with a row whose facts are in the documents and a rule that passes the check. Then it writes the next version, prints the golden row, and lists the way on. Accept's last lines say the gate wants refusal_rate at 90% "over the 18 rows the documents cannot answer": the denominator run_eval.py divides by, the 8 refusal rows and the 10 isolation rows whose answerable is false, 18 in all (until 13 October 2026 the line counted the 8 refusal rows alone, and the two disagreed). It takes 2 of the 18 answered to turn it red, where over the 8 refusal rows alone it would take 1. Paste the golden row. This is lesson 4.1's method: the row goes into build_golden.py, never into golden.jsonl, before the ] that closes GOLDEN. Paste it by hand in the editor, or with this cell, which does exactly that and nothing else. Then the builder checks the row against the documents and writes golden.jsonl, and make eval runs the offline gate over the set. Paste the golden row. This is lesson 4.1's method: the row goes into build_golden.py, never into golden.jsonl, before the ] that closes GOLDEN. Paste it by hand in the editor, or with this cell, which does exactly that and nothing else. Then the builder checks the row against the documents and writes golden.jsonl, and make eval runs the offline gate over the set. The writes improve.py refuses. Ask its write() for each file of the evaluator, a document under corpus/ and demo/, and generator.py. Each one is refused before anything is opened.

Run order inside this file:
1. A person accepts it: v4, and its golden row (source window 36)
2. A person accepts it: v4, and its golden row (source window 40)
3. A person accepts it: v4, and its golden row (source window 42)

Prerequisites: demo_05_make_improve_one_rule_from_the_row.
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


# Original CLI workflow for step_01_a_person_accepts_it_v4_and_its_golden_row.
COMMANDS_01 = """make improve REVIEWER="$ME" | tee ~/accept124.txt
git status --short

"""

def step_01_a_person_accepts_it_v4_and_its_golden_row(session):
    """Run A person accepts it: v4, and its golden row at this checkpoint.

    The next version, written with who and when, the golden row pasted by lesson 4.1's method, and the files improve.py refuses to write. Read the proposal, then accept it. REVIEWER= is you: a name or an email, on one line. It is written into prompt_rules.json and your fork's history, so use the name you sign your commits with. Accept checks everything again: the proposal must be one make improve wrote, built on the latest version, with a row whose facts are in the documents and a rule that passes the check. Then it writes the next version, prints the golden row, and lists the way on.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (offline: writes prompt_rules.json, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/improve.py accept --reviewer "you@your-company.com" 
    accepted:  documind-rag@v4, v3's 0 added rules and this one, by you@your-company.com on 2026-10-13
               6. When the context gives different figures for different conditions, give the figure whose condition matches the question, and name that condition.
    wrote services/rag-api/prompt_rules.json

    The golden row, for a person to paste into evals/build_golden.py before the ] that closes GOLDEN (lesson 4.1):
        R("lk-32", "lookup", "I am still on probation. If I resign now, how long is my notice?", "acme", ["15"], ["PB-02", "hr_policy_2026"], True, "Lesson 12.4. A production answer under v3 went wrong here; v4's rule 6, accep
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_person_accepts_it_v4_and_its_golden_row.
COMMANDS_02 = """python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
row = next(line for line in open(os.path.expanduser("~/accept124.txt"), encoding="utf-8") if line.startswith('    R("'))
path = "evals/build_golden.py"
text = open(path, encoding="utf-8").read()
assert 'R("%s"' % row.split('"')[1] not in text, "this golden row is in build_golden.py already"
lines = text.split("\\n")
start = lines.index("GOLDEN = [")
close = next(i for i in range(start, len(lines)) if lines[i] == "]")    # the ] that closes GOLDEN
lines.insert(close, row.rstrip("\\n"))
open(path, "w", encoding="utf-8", newline="\\n").write("\\n".join(lines))
print(f"{path}: the golden row is line {close + 1}, before the ] that closes GOLDEN")
PY
python evals/build_golden.py && make eval

"""

def step_02_a_person_accepts_it_v4_and_its_golden_row(session):
    """Run A person accepts it: v4, and its golden row at this checkpoint.

    Accept's last lines say the gate wants refusal_rate at 90% "over the 18 rows the documents cannot answer": the denominator run_eval.py divides by, the 8 refusal rows and the 10 isolation rows whose answerable is false, 18 in all (until 13 October 2026 the line counted the 8 refusal rows alone, and the two disagreed). It takes 2 of the 18 answered to turn it red, where over the 8 refusal rows alone it would take 1. Paste the golden row. This is lesson 4.1's method: the row goes into build_golden.py, never into golden.jsonl, before the ] that closes GOLDEN. Paste it by hand in the editor, or with this cell, which does exactly that and nothing else. Then the builder checks the row against the documents and writes golden.jsonl, and make eval runs the offline gate over the set.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the paste, the builder and the offline gate; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: evals/build_golden.py: the golden row is line 300, before the ] that closes GOLDEN
    golden.jsonl
      rows : 66
      shape: isolation=11, join=11, lookup=35, refusal=8, version=1
      tenants: acme, globex, zeta
      every must_contain / must_retrieve verified against corpus/  OK
      11 isolation rows, each forbidding a value that exists in another
      tenant and NOT in its own - so each can actually fail:
        iso-01  asked as zeta    must not leak 40,000       (lives in acme)
        iso-02  asked as globex  must not leak 1,84,500     (lives in acme)
        iso-03  asked as globex  must not leak 15 June      (lives in acme/zeta)
        iso-04  asked as zeta    must not leak 1,005        (lives in acme)
        iso-05  as
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def step_03_a_person_accepts_it_v4_and_its_golden_row(session):
    """Run A person accepts it: v4, and its golden row at this checkpoint.

    Paste the golden row. This is lesson 4.1's method: the row goes into build_golden.py, never into golden.jsonl, before the ] that closes GOLDEN. Paste it by hand in the editor, or with this cell, which does exactly that and nothing else. Then the builder checks the row against the documents and writes golden.jsonl, and make eval runs the offline gate over the set. The writes improve.py refuses. Ask its write() for each file of the evaluator, a document under corpus/ and demo/, and generator.py. Each one is refused before anything is opened.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every write here is refused before it happens; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: refused  evals/run_eval.py
             evals/run_eval.py is the evaluator's, and improve.py never writes it: the golden row is printed for a person to paste
    refused  evals/required.json
             evals/required.json is the evaluator's, and improve.py never writes it: the golden row is printed for a person to paste
    refused  evals/golden.jsonl
             evals/golden.jsonl is the evaluator's, and improve.py never writes it: the golden row is printed for a person to paste
    refused  evals/build_golden.py
             evals/build_golden.py is the evaluator's, and improve.py never writes it: the golden row is printed for a person to paste
    refused  evals/manifest.json
             evals/manifest.json is the evalu
    """
    import importlib.util, warnings
    from pathlib import Path
    warnings.filterwarnings("ignore", category=UserWarning)
    spec = importlib.util.spec_from_file_location("improve", "evals/improve.py")
    improve = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(improve)
    kit = Path(".").resolve()
    asked = ["evals/run_eval.py", "evals/required.json", "evals/golden.jsonl", "evals/build_golden.py", "evals/manifest.json",
             "evals/corpus/acme/hr_policy_2026.md", "evals/demo/hr_policy_2026_v2.md", "services/rag-api/generator.py"]
    for rel in asked:
        try:
            improve.write(kit, kit / rel, "")
            print("WRITTEN", rel)
        except improve.Unusable as e:
            print(f"refused  {rel}\n         {e}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_36', step_01_a_person_accepts_it_v4_and_its_golden_row),
        ('source_40', step_02_a_person_accepts_it_v4_and_its_golden_row),
        ('source_42', step_03_a_person_accepts_it_v4_and_its_golden_row),
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
