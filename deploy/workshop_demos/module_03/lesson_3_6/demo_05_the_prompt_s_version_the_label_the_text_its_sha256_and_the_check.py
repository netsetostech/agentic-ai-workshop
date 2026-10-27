"""Lesson 3.6: The prompt's version: the label, the text, its sha256 and the check

Do it: the check

Run order inside this file:
1. Do it: the check (source window 31)

Prerequisites: demo_04_your_lane_what_the_ui_shows_as_a_quote_then_a_source_s_quotes_held_against_their.
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


# Original CLI workflow for step_01_the_check.
COMMANDS_01 = """make prompt-version; echo "exit $?"

"""

def step_01_the_check(session):
    """Run Do it: the check at this checkpoint.

    Do it: the check

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (offline: no project, no credential, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python commands/prompt_pin.py
    prompt:   documind-rag@v3 (services/rag-api/config.py: prompt_id@prompt_version, as /version reports it)
    text:     SYSTEM + DATED_RULE, 604 characters, as generate() joins them (services/rag-api/generator.py)
    sha256:   543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e
    registry: documind-rag@v3 has this sha256 (services/rag-api/prompt_versions.json): the text is the one its version names
    exit 0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_the_check),
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
