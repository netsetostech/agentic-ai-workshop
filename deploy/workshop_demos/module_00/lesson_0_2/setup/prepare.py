"""Lesson 0.2: Before you run anything: install the tools, clone the kit, make the venv

Install what is missing, open a new terminal so its PATH is fresh, and check. Each tool should print a path; the versions below the paths are the second check, against the table.

Run order inside this file:
1. The tools, and why the kit needs each (source window 1)

Prerequisites: workshop setup; see this lesson README.
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


# Original CLI workflow for step_01_the_tools_and_why_the_kit_needs_each.
COMMANDS_01 = """for t in git curl python3.12 terraform gcloud docker ollama make; do    # each prints a path, or MISSING
  printf '%-10s %s\\n' "$t" "$(command -v "$t" || echo MISSING)"
done
python3.12 --version; terraform version | head -1; gcloud --version | head -1
docker --version; ollama --version

"""

def step_01_the_tools_and_why_the_kit_needs_each(session):
    """Run The tools, and why the kit needs each at this checkpoint.

    Install what is missing, open a new terminal so its PATH is fresh, and check. Each tool should print a path; the versions below the paths are the second check, against the table.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in a terminal on your laptop, after installing the tools.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/tool_checks.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_1', step_01_the_tools_and_why_the_kit_needs_each),
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
