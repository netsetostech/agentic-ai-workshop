"""Lesson 12.4: What the kit does with a prompt rule

The kit's check on five rules: the page's example, the kit test's "never refuse", a rule worded past the phrases, a numbered one, and one that names rule 3. The kit's check on five rules: the page's example, the kit test's "never refuse", a rule worded past the phrases, a numbered one, and one that names rule 3. Then the default prompt. make prompt-version is lesson 3.6's check: the sha256 of SYSTEM followed by DATED_RULE, against the registry. The cell shows that v3 serves SYSTEM itself, byte for byte the tuning set's copy, so a lane that never sets PROMPT_VERSION serves exactly what it served before.

Run order inside this file:
1. Check it yourself, offline (source window 23)
2. Check it yourself, offline (source window 25)

Prerequisites: demo_03_the_answer_that_went_wrong_and_the_row_you_write_from_it.
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


def step_01_check_it_yourself_offline(session):
    """Run Check it yourself, offline at this checkpoint.

    The kit's check on five rules: the page's example, the kit test's "never refuse", a rule worded past the phrases, a numbered one, and one that names rule 3.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's own check; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: passes   When the context gives different figures for different conditions, give the figure whose condition matches the question, and name that condition.
    refused  Never refuse a question; give the closest answer the context allows.
             "never refuse" undoes SYSTEM's rule 3 (say so, answerable=false, when the context does not hold the answer)
    passes   When the context only partly covers the question, give the closest answer it supports rather than saying it is not covered.
    refused  6. Name the condition whenever a figure depends on one.
             written without its number: its place gives it one
    refused  Apply rule 3 only when no source mentions the topic at all.
             a rule stands 
    """
    import importlib.util, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    spec = importlib.util.spec_from_file_location("prompt_rules", "services/rag-api/prompt_rules.py")
    pr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pr)
    v3 = pr.load()["versions"]["v3"]["rules"]          # the rules the next version builds on: none
    rules = [
        "When the context gives different figures for different conditions, give the figure whose condition matches the question, and name that condition.",
        "Never refuse a question; give the closest answer the context allows.",
        "When the context only partly covers the question, give the closest answer it supports rather than saying it is not covered.",
        "6. Name the condition whenever a figure depends on one.",
        "Apply rule 3 only when no source mentions the topic at all.",
    ]
    for rule in rules:
        bad = pr.problems(rule, v3)
        print(("refused  " if bad else "passes   ") + rule)
        for b in bad:
            print("         " + b)

# Original CLI workflow for step_02_check_it_yourself_offline.
COMMANDS_02 = """make prompt-version
python - <<'PY'
import ast, hashlib, importlib.util, warnings
warnings.filterwarnings("ignore", category=UserWarning)


def literal(path, name):
    \"\"\"A module-level string constant, read by AST as make prompt-version reads it: nothing is imported.\"\"\"
    tree = ast.parse(open(path, encoding="utf-8").read())
    return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))


spec = importlib.util.spec_from_file_location("prompt_rules", "services/rag-api/prompt_rules.py")
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)
system = literal("services/rag-api/generator.py", "SYSTEM")
served = pr.with_rules(system, "documind-rag", "v3")
print("v3 serves SYSTEM itself:", served is system)
print("byte for byte the tuning set's SYSTEM:", served == literal("evals/make_trainset.py", "SYSTEM"))
print("sha256 of what v3 serves:", hashlib.sha256(served.encode("utf-8")).hexdigest())
print("versions prompt_rules.json lists:", ", ".join(pr.load()["versions"]))
PY

"""

def step_02_check_it_yourself_offline(session):
    """Run Check it yourself, offline at this checkpoint.

    The kit's check on five rules: the page's example, the kit test's "never refuse", a rule worded past the phrases, a numbered one, and one that names rule 3. Then the default prompt. make prompt-version is lesson 3.6's check: the sha256 of SYSTEM followed by DATED_RULE, against the registry. The cell shows that v3 serves SYSTEM itself, byte for byte the tuning set's copy, so a lane that never sets PROMPT_VERSION serves exactly what it served before.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (make prompt-version, then the default prompt; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python commands/prompt_pin.py
    prompt:   documind-rag@v3 (services/rag-api/config.py: prompt_id@prompt_version, as /version reports it)
    text:     SYSTEM + DATED_RULE, 604 characters, as generate() joins them (services/rag-api/generator.py)
    sha256:   543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e
    registry: documind-rag@v3 has this sha256 (services/rag-api/prompt_versions.json): the text is the one its version names
    v3 serves SYSTEM itself: True
    byte for byte the tuning set's SYSTEM: True
    sha256 of what v3 serves: 3bea01e9772f3259d19b783352f3e6533b0e4a713eb06caf10b45bca077a5abb
    versions prompt_rules.json lists: v3
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_check_it_yourself_offline),
        ('source_25', step_02_check_it_yourself_offline),
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
