"""Lesson 10.9: Deploy, and ask through the query API

Do it: deploy Do it: ask, three ways

Run order inside this file:
1. Do it: deploy (source window 27)
2. Do it: ask, three ways (source window 29)
3. Do it: ask, three ways (source window 31)
4. Do it: ask, three ways (source window 33)

Prerequisites: demo_04_every_call_through_one_seam_the_dry_run.
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


# Original CLI workflow for step_01_deploy.
COMMANDS_01 = """make managed-peer-up PROJECT="$PROJECT" REGION="$REGION"   # 10 to 20 minutes, most of it the image's build

"""

def step_01_deploy(session):
    """Run Do it: deploy at this checkpoint.

    Do it: deploy

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the managed peer deployed: it bills until step 10).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/up.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_ask_three_ways.
COMMANDS_02 = """make managed-peer-ask PROJECT="$PROJECT" REGION="$REGION"

"""

def step_02_ask_three_ways(session):
    """Run Do it: ask, three ways at this checkpoint.

    Do it: ask, three ways

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's question, through the query API).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ask_acme.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_ask_three_ways.
COMMANDS_03 = """make managed-peer-ask PROJECT="$PROJECT" REGION="$REGION" TENANT=zeta

"""

def step_03_ask_three_ways(session):
    """Run Do it: ask, three ways at this checkpoint.

    Do it: ask, three ways

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same question, naming zeta).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ask_zeta.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_ask_three_ways.
COMMANDS_04 = """make managed-peer-ask PROJECT="$PROJECT" REGION="$REGION" HOST=cloudrun

"""

def step_04_ask_three_ways(session):
    """Run Do it: ask, three ways at this checkpoint.

    Do it: ask, three ways

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same question to the Cloud Run peer, over A2A).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ask_cloudrun.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_deploy),
        ('source_29', step_02_ask_three_ways),
        ('source_31', step_03_ask_three_ways),
        ('source_33', step_04_ask_three_ways),
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
