"""Lesson 11.7: The registry, read at Rs 0

Do it: the registry Do it: one entry, every field

Run order inside this file:
1. Do it: the registry (source window 7)
2. Do it: one entry, every field (source window 9)

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


# Original CLI workflow for step_01_the_registry.
COMMANDS_01 = """make gotchas

"""

def step_01_the_registry(session):
    """Run Do it: the registry at this checkpoint.

    Do it: the registry

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads one file; no lane, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 13 gotchas in ops/gotchas.json (workshop lesson 11.7). make gotchas ID=<id> shows one; make gotcha-drill runs every offline drill, Rs 0
    id                              signal  drill          status   lessons            title
    pinned-traffic                  silent  offline, live  open     5.5 6.7 11.3       A service pinned to one revision never serves a later change
    deploy-drops-hotfix             silent  offline, live  open     0.3 2.5 5.5        A routine make deploy-services drops a setting made by hand
    ungated-api-release             silent  offline        open     0.3 11.1 11.2      make deploy-services and make up put an ungated API revision live
    switch-rides-into-candidate     silent 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_one_entry_every_field.
COMMANDS_02 = """make gotchas ID=deploy-drops-hotfix

"""

def step_02_one_entry_every_field(session):
    """Run Do it: one entry, every field at this checkpoint.

    Do it: one entry, every field

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one entry, every field).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: deploy-drops-hotfix: A routine make deploy-services drops a setting made by hand
      signal     silent
      status     open
      symptom    A setting put on a running service with gcloud run services update --update-env-vars (lesson 2.5's
                 QUERY_REWRITE=on, a chat cap, a Change-it left in place) holds until the next routine make
                 deploy-services. Each deploy script sets its service's whole environment with --set-env-vars, so a
                 variable the script does not list is gone, and a switch the deploy does carry (ARMOR, ROUTING,
                 GENERATOR_MODEL, ADMIN_EMAILS) goes back to the Makefile's default unless it is passed again. The service
                 carries on wi
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_the_registry),
        ('source_9', step_02_one_entry_every_field),
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
