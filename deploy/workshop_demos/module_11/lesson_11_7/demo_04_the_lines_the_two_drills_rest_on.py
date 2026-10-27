"""Lesson 11.7: The lines the two drills rest on

The cell loads the kit's own reader of the deploy scripts, the one the drills and the detectors use, and prints what each deploy writes. It reads the scripts and the Makefile, and calls nothing.

Run order inside this file:
1. Do it: what each routine deploy writes (source window 18)

Prerequisites: demo_03_the_registry_read_at_rs_0.
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


def step_01_what_each_routine_deploy_writes(session):
    """Run Do it: what each routine deploy writes at this checkpoint.

    The cell loads the kit's own reader of the deploy scripts, the one the drills and the detectors use, and prints what each deploy writes. It reads the scripts and the Makefile, and calls nothing.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's own reader of the deploy scripts; no lane, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: make deploy-services runs 7 deploy scripts, and each sets its service's whole environment:
      documind-ingest  commands/lesson-12.5.sh    --set-env-vars, 13 variables
      documind-api     commands/lesson-12.2.sh    --set-env-vars, 29 variables
      documind-admin   commands/lesson-12.3.sh    --set-env-vars, 4 variables
      documind-ui      commands/lesson-12.4.sh    --set-env-vars, 18 variables
      documind-chat    commands/lesson-12.8.sh    --set-env-vars, 10 variables
      documind-mcp     commands/lesson-7.2.sh     --set-env-vars, 6 variables
      documind-agent   commands/lesson-8.4.sh     --set-env-vars, 8 variables
    documind-chat's list: AUDIT_BUCKET, DOCUMIND_BRAIN, DOCUMIND_PROFILE, GOOGLE_CLOUD_LOCA
    """
    import importlib.util, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    spec = importlib.util.spec_from_file_location("gotchas", "commands/gotchas.py")
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)                          # the kit's own reader of the deploy scripts: no lane, no network
    mk = g.makefile()
    specs, passes = g.deploy_specs(), g.deploy_passes(mk)
    print(f"make deploy-services runs {len(g.default_scripts(mk))} deploy scripts, and each sets its service's whole environment:")
    for name, s in specs.items():
        print(f"  {name:16} {s.script:26} --set-env-vars, {len(s.writes())} variables")
    chat = specs["documind-chat"]
    print("documind-chat's list: " + ", ".join(sorted(chat.writes())))
    print("CHAT_MAX_MODEL_CALLS in it:", "CHAT_MAX_MODEL_CALLS" in chat.writes())
    print(f"the script's hook for more: {', '.join(chat.hooks)}, which make deploy-services sets to {passes['CHAT_EXTRA_ENV'][1]!r}")
    made = sorted(f"{n}={v}" for n, (how, v) in passes.items() if how == "make" and v)
    print("the switches it passes, each back to the Makefile's default unless you pass it: " + ", ".join(made))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_what_each_routine_deploy_writes),
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
