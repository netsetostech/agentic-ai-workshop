"""Lesson 3.3: One rule per row in the bench, with the refusal rows beside it

Before anything costs money, see what each edit arm will send. The cell applies each rule with the bench's own edit_system() and prints the rule count, the prompt's sha256 and the new rule 6, then checks generator.py's bytes. Do it: FIX1, the refused row Do it: FIX2, the half-answered join Do it: FIX3, the answer without its figure Each run prints its pools, its two arms with their prompts' sha256, one line per answer (the verdict, the thought and visible tokens, the rupees and the why), then a table per arm: passes out of 9 with a Wilson interval, the quote checks, and the cost. The last lines say that generator.py is unchanged on disk and SYSTEM is the kit's again. The cell below reads the three reports and puts each fix's row and guard side by side.

Run order inside this file:
1. Do it: the three rules, applied in memory first (source window 29)
2. Do it: FIX1, the refused row (source window 31)
3. Do it: FIX2, the half-answered join (source window 33)
4. Do it: FIX3, the answer without its figure (source window 35)
5. Do it: FIX3, the answer without its figure (source window 37)

Prerequisites: demo_06_the_failing_rows_read_with_their_passages_and_where_each_fix_lives.
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


def step_01_the_three_rules_applied_in_memory_first(session):
    """Run Do it: the three rules, applied in memory first at this checkpoint.

    Before anything costs money, see what each edit arm will send. The cell applies each rule with the bench's own edit_system() and prints the rule count, the prompt's sha256 and the new rule 6, then checks generator.py's bytes.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the three rules applied in memory; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: kit   5 rules, prompt sha256 543ed8060f1b177c...
    FIX1  6 rules, prompt sha256 3046edc925bd8085...
          6. If a source answers the question in other words, or states a rule that covers the case asked about, answer from it and cite it.
    FIX2  6 rules, prompt sha256 e23622bc3e66816c...
          6. If the question asks more than one thing, answer every part, each from the source that states it, and cite each source.
    FIX3  6 rules, prompt sha256 e3420a7f81105a67...
          6. Begin the answer with the figure, name or term that answers the question, written as the source writes it.
    generator.py on disk: unchanged
    """
    import ast, hashlib, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, "evals")
    import prompt_bench as bench
    
    PATH = "services/rag-api/generator.py"
    before = hashlib.sha256(open(PATH, "rb").read()).hexdigest()
    K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(open(PATH, encoding="utf-8").read()).body
         if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("SYSTEM", "DATED_RULE")}
    RULES = {"FIX1": "If a source answers the question in other words, or states a rule that covers the case asked about, answer from it and cite it.",
             "FIX2": "If the question asks more than one thing, answer every part, each from the source that states it, and cite each source.",
             "FIX3": "Begin the answer with the figure, name or term that answers the question, written as the source writes it."}
    print(f"kit   {bench.rule_count(K['SYSTEM'])}, prompt sha256 {bench.prompt_sha(K['SYSTEM'], K['DATED_RULE'])[:16]}...")
    for name, rule in RULES.items():
        edited = bench.edit_system(K["SYSTEM"], add=[rule])
        print(f"{name}  {bench.rule_count(edited)}, prompt sha256 {bench.prompt_sha(edited, K['DATED_RULE'])[:16]}...")
        print(f"      {edited.splitlines()[-1]}")
    print("generator.py on disk:", "unchanged" if hashlib.sha256(open(PATH, "rb").read()).hexdigest() == before else "CHANGED")

# Original CLI workflow for step_02_fix1_the_refused_row.
COMMANDS_02 = """make bench PROJECT="$PROJECT" BENCH_ARGS="--rows ${FIX1:?set FIX1 from the read cell} --shape refusal --report evals/reports/fix33_1.json --add-rule 'If a source answers the question in other words, or states a rule that covers the case asked about, answer from it and cite it.'"

"""

def step_02_fix1_the_refused_row(session):
    """Run Do it: FIX1, the refused row at this checkpoint.

    Do it: FIX1, the refused row

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (FIX1 from the read cell: its row and the 8 refusal rows, two arms).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/fix_1.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_fix2_the_half_answered_join.
COMMANDS_03 = """make bench PROJECT="$PROJECT" BENCH_ARGS="--rows ${FIX2:?set FIX2 from the read cell} --shape refusal --report evals/reports/fix33_2.json --add-rule 'If the question asks more than one thing, answer every part, each from the source that states it, and cite each source.'"

"""

def step_03_fix2_the_half_answered_join(session):
    """Run Do it: FIX2, the half-answered join at this checkpoint.

    Do it: FIX2, the half-answered join

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (FIX2: the same, with the second rule).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/fix_2.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_fix3_the_answer_without_its_figure.
COMMANDS_04 = """make bench PROJECT="$PROJECT" BENCH_ARGS="--rows ${FIX3:?set FIX3 from the read cell} --shape refusal --report evals/reports/fix33_3.json --add-rule 'Begin the answer with the figure, name or term that answers the question, written as the source writes it.'"

"""

def step_04_fix3_the_answer_without_its_figure(session):
    """Run Do it: FIX3, the answer without its figure at this checkpoint.

    Do it: FIX3, the answer without its figure

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (FIX3: the same, with the third rule).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/fix_3.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def step_05_fix3_the_answer_without_its_figure(session):
    """Run Do it: FIX3, the answer without its figure at this checkpoint.

    Each run prints its pools, its two arms with their prompts' sha256, one line per answer (the verdict, the thought and visible tokens, the rupees and the why), then a table per arm: passes out of 9 with a Wilson interval, the quote checks, and the cost. The last lines say that generator.py is unchanged on disk and SYSTEM is the kit's again. The cell below reads the three reports and puts each fix's row and guard side by side.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the three bench reports; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/fix_read.txt]
    """
    import json, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    
    def verdicts(answers):
        """'pass' or the why of each answer, in run order.
        
        Example: verdicts(got)
        """
        return ", ".join("pass" if a["pass"] else (a["why"] or a["outcome"]) for a in answers)
    
    
    held = 0
    for i in (1, 2, 3):
        path = f"evals/reports/fix33_{i}.json"
        if not os.path.exists(path):
            print(f"{path}: not there yet")
            continue
        b = json.load(open(path, encoding="utf-8"))
        edit = next(a for a in b["arms"] if a["name"] == "edit")
        rows = {r["id"]: r for r in b["rows"]}
        print(f"{path}: {b['model']}, {len(b['answers'])} answers, Rs {b['cost_inr']:.2f}, generator.py unchanged: {b['generator_unchanged']}")
        print(f"  {'; '.join(edit['changes'])}")
        by = {}
        for a in b["answers"]:
            by.setdefault((a["id"], a["arm"]), []).append(a)
        targets = [r for r in b["rows"] if r["shape"] != "refusal" and r["benched"]]
        fixed, kit_passed = bool(targets), bool(targets)
        for r in targets:
            kit, edited = by.get((r["id"], "kit"), []), by.get((r["id"], "edit"), [])
            for arm, got in (("kit", kit), ("edit", edited)):
                said = " ".join((got[0].get("answer") or got[0].get("error") or "").split()) if got else ""
                print(f"  {r['id']:7} {arm:4} {verdicts(got)}: {said[:110]!r}")
            kit_passed = kit_passed and all(a["pass"] for a in kit)
            fixed = fixed and not all(a["pass"] for a in kit) and all(a["pass"] for a in edited)
        guard = {}
        for arm in ("kit", "edit"):
            refusals = [a for a in b["answers"] if a["arm"] == arm and rows[a["id"]]["shape"] == "refusal"]
            guard[arm] = (sum(a["pass"] for a in refusals), len(refusals), sorted({a["id"] for a in refusals if not a["pass"]}))
        print("  refusal rows: " + "; ".join(f"{arm} {k} of {n}" + (f" (failed: {', '.join(bad)})" if bad else "")
                                           for arm, (k, n, bad) in guard.items()))
        kept = guard["edit"][0] >= guard["kit"][0]
        if fixed:
            verdict = "fixed, and the guard held" if kept else "fixed, and the guard broke"
        elif kit_passed:
            verdict = "the kit arm passed too: nothing to credit the rule with"
        else:
            verdict = "not fixed"
        print(f"  -> {verdict}")
        held += fixed and kept
    print(f"\nfixed with the guard held: {held} of 3")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_29', step_01_the_three_rules_applied_in_memory_first),
        ('source_31', step_02_fix1_the_refused_row),
        ('source_33', step_03_fix2_the_half_answered_join),
        ('source_35', step_04_fix3_the_answer_without_its_figure),
        ('source_37', step_05_fix3_the_answer_without_its_figure),
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
