"""Lesson 11.7: Every offline drill, on a stand-in of Cloud Run

Do it: pinned traffic Do it: a routine deploy drops a hotfix The command runs all 9 drills, and grep keeps each drill's verdict lines: its name, REPRODUCED, CLEARED where it shows its lever, and the count at the end. Run make gotcha-drill ID=<id> to read any one of them in full.

Run order inside this file:
1. Do it: pinned traffic (source window 21)
2. Do it: a routine deploy drops a hotfix (source window 23)
3. Do it: every offline drill (source window 25)

Prerequisites: demo_04_the_lines_the_two_drills_rest_on.
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


# Original CLI workflow for step_01_pinned_traffic.
COMMANDS_01 = """make gotcha-drill ID=pinned-traffic

"""

def step_01_pinned_traffic(session):
    """Run Do it: pinned traffic at this checkpoint.

    Do it: pinned traffic

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a stand-in of Cloud Run; no lane, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == pinned-traffic, offline (a stand-in, Rs 0): A service pinned to one revision never serves a later change
    documind-chat: documind-chat-00001-mup takes 100% of the traffic, following the latest revision; /health: max_model_calls 12
    the traffic held on that revision by name, as a rollback by traffic leaves it:
    $ gcloud run services update-traffic documind-chat --to-revisions=documind-chat-00001-mup=100 --region=us-central1 --project=documind-ai-YOUR-ID --quiet
    a setting changed by hand:
    $ gcloud run services update documind-chat --update-env-vars=CHAT_MAX_MODEL_CALLS=3 --region=us-central1 --project=documind-ai-YOUR-ID --quiet
    documind-chat-00002-zeq: made with CHAT_MAX_MODEL_CALLS=3, takes 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_a_routine_deploy_drops_a_hotfix.
COMMANDS_02 = """make gotcha-drill ID=deploy-drops-hotfix

"""

def step_02_a_routine_deploy_drops_a_hotfix(session):
    """Run Do it: a routine deploy drops a hotfix at this checkpoint.

    Do it: a routine deploy drops a hotfix

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a stand-in of Cloud Run; no lane, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == deploy-drops-hotfix, offline (a stand-in, Rs 0): A routine make deploy-services drops a setting made by hand
    documind-chat: image tag c0ffee1, nothing the next deploy would change; /health: max_model_calls 12
    a setting changed by hand:
    $ gcloud run services update documind-chat --update-env-vars=CHAT_MAX_MODEL_CALLS=8 --region=us-central1 --project=documind-ai-YOUR-ID --quiet
    /health: max_model_calls 8: the hand-set value answers
    detector, before the deploy: CHAT_MAX_MODEL_CALLS=8: dropped, not in commands/lesson-12.8.sh's --set-env-vars; make deploy-services empties CHAT_EXTRA_ENV, the script's hook for more
    the routine deploy:
    $ make deploy-services SCRIPTS=commands/lesson-12.8.sh PROJE
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_every_offline_drill.
COMMANDS_03 = """make gotcha-drill | grep -E '^(==|REPRODUCED|CLEARED|NOT|[0-9]+ of)'   # every offline drill, its verdict lines

"""

def step_03_every_offline_drill(session):
    """Run Do it: every offline drill at this checkpoint.

    The command runs all 9 drills, and grep keeps each drill's verdict lines: its name, REPRODUCED, CLEARED where it shows its lever, and the count at the end. Run make gotcha-drill ID=<id> to read any one of them in full.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every offline drill; no lane, Rs 0, a few seconds).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == pinned-traffic, offline (a stand-in, Rs 0): A service pinned to one revision never serves a later change
    REPRODUCED: the new revision takes 0% of the traffic, and /health still reports the old cap
    CLEARED: after --to-latest the new revision takes the traffic, and /health reports the new cap
    == deploy-drops-hotfix, offline (a stand-in, Rs 0): A routine make deploy-services drops a setting made by hand
    REPRODUCED: the routine deploy dropped the hand-set CHAT_MAX_MODEL_CALLS, and /health reports the default again
    CLEARED: the deploy that carries CHAT_MAX_MODEL_CALLS keeps it, and the detector finds nothing left to drop
    == ungated-api-release, offline (a stand-in, Rs 0): make deploy-services 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_pinned_traffic),
        ('source_23', step_02_a_routine_deploy_drops_a_hotfix),
        ('source_25', step_03_every_offline_drill),
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
