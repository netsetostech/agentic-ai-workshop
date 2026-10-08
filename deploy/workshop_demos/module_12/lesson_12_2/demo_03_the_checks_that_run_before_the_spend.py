"""Lesson 12.2: The checks that run before the spend

Do it

Run order inside this file:
1. Do it (source window 9)

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


# Original CLI workflow for step_01_the_checks_that_run_before_the_spend.
COMMANDS_01 = """python evals/make_trainset.py --selftest
python evals/tune.py --selftest
python - <<'PY'
import ast, re, sys, types
sys.path[:0] = ["evals"]
import tune                                          # stdlib only when imported: no SDK, no project, no network
for base, adapter in (("gemini-3.6-flash", 4), ("gemini-3.1-flash-lite", 3), ("gemini-3.1-flash-lite", 32)):
    try:
        print(f"{base}, adapter {adapter}: accepted, {tune.config_for(base, 3, adapter, 'documind-sft-v2')['adapter_size']}")
    except SystemExit as e:
        print(f"{base}, adapter {adapter}: refused before submission: {str(e).split(': ', 1)[1].split('. ', 1)[0]}")
print(f"make tune's defaults: {tune.config_for('gemini-3.1-flash-lite', 3, 4, 'documind-sft-v1')}")
fn = next(n for n in ast.parse(open("services/rag-api/generator.py", encoding="utf-8").read()).body
          if isinstance(n, ast.FunctionDef) and n.name == "_endpoint_location")


def location(model, override="", region="asia-south1"):     # generator.py builds its clients when imported: the rule is lifted out
    ns = {"re": re, "settings": types.SimpleNamespace(generator_location=override, region=region)}
    exec(compile(ast.Module([fn], []), "generator.py", "exec"), ns)
    return ns["_endpoint_location"](model)


EP = "projects/NUMBER/locations/us/endpoints/ENDPOINT_ID"
print(f"an endpoint whose path says us is called at: {location(EP)}; with GENERATOR_LOCATION=us-central1: {location(EP, 'us-central1')}")
PY

"""

def step_01_the_checks_that_run_before_the_spend(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the two self-tests and the rules; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: selftest: the evidence rule dropped jn-06's chunk and kept EMEA elsewhere and lk-09's 8, the question rule dropped lk-06's twin, the PAN row dropped, two formats agree, ModelDraft parses, the batch round trip holds
    selftest: the helpdesk rows mark the source they cite, carry the served prompt with SYSTEM once, drop a quote not in its chunk, keep Hinglish twins and refusals, and a PAN in a distractor drops its row
    selftest: an untunable base and a rank the SDK cannot spell are refused before submission; adapter 4 is ADAPTER_SIZE_FOUR and the SDK accepts it
    gemini-3.6-flash, adapter 4: refused before submission: managed SFT accepts ['gemini-3.1-flash-lite', 'gemini-3.5-flash'] as of 2026-09-04
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_checks_that_run_before_the_spend),
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
