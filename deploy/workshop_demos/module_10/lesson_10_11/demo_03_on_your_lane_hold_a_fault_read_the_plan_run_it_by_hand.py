"""Lesson 10.11: On your lane: hold a fault, read the plan, run it by hand

make remediate OFFLINE=1 reads the kit's own recording of this drill, ops/incidents/held_model.json. It needs no PROJECT and no credential, and it prints the plan you should get on the lane, with your lane's revision names in place of these. HOLD=1 writes deploy/.fault-hold first, with the variable as it was and the revision serving, so that RESTORE=1 always has a record. Then it sets the fault, and the new revision takes the traffic. It runs the smoke once, so that the lane holds the fault's own turns for remediate to read, and it leaves the fault in place. remediate reads the lane three times and prints the plan. SAVE= keeps what it read, with the project id and number replaced, so the incident can be replayed later. Expect bad_revision, the change CHAT_MODEL: unset -> "gemini-3.6-flsh", and a rollback to the revision HOLD=1 recorded as serving before the fault. Paste step 1's command as your plan printed it, or set PREV to the revision it names. It moves traffic only: the fault's revision stays, at 0%. The plan's step 2. Every brain should answer, because the traffic is on the revision before the fault. Expect rolled_back. The plan starts again from the verify, and does not print the rollback a second time: its step 1 says the rollback is done.

Run order inside this file:
1. First, offline: the plan the drill should produce (source window 6)
2. Hold the fault (source window 8)
3. Read the plan (source window 11)
4. Run the rollback it printed (source window 13)
5. Verify (source window 15)
6. Read the lane again (source window 17)

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


# Original CLI workflow for step_01_first_offline_the_plan_the_drill_should_pr.
COMMANDS_01 = """make remediate OFFLINE=1

"""

def step_01_first_offline_the_plan_the_drill_should_pr(session):
    """Run First, offline: the plan the drill should produce at this checkpoint.

    make remediate OFFLINE=1 reads the kit's own recording of this drill, ops/incidents/held_model.json. It needs no PROJECT and no credential, and it prints the plan you should get on the lane, with your lane's revision names in place of these.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: remediate: documind-chat on documind-ai-YOUR-ID (us-central1), the 60 minutes to 2026-10-12 10:00 UTC (15:30 IST)
    rules only: no model is called, and nothing on the lane is changed.
    read from a recorded state: held_model.json (make incident-drill FAULT=model HOLD=1 and its smoke: CHAT_MODEL=gemini-3.6-flsh, a mistyped model, fails every agent turn with a 500)

    What the lane shows
      traffic     100% documind-chat-00042-tvd (following the latest revision)
      revision    documind-chat-00042-tvd  created 2026-10-12 09:41 UTC (15:11 IST), inside the window  [serving]
      revision    documind-chat-00041-kpw  created 2026-10-09 06:12 UTC (11:42 IST)  [the revision before it]
      the change  CHAT_MODEL: 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_hold_the_fault.
COMMANDS_02 = """make incident-drill PROJECT=$PROJECT HOLD=1

"""

def step_02_hold_the_fault(session):
    """Run Hold the fault at this checkpoint.

    HOLD=1 writes deploy/.fault-hold first, with the variable as it was and the revision serving, so that RESTORE=1 always has a record. Then it sets the fault, and the new revision takes the traffic. It runs the smoke once, so that the lane holds the fault's own turns for remediate to read, and it leaves the fault in place.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (one revision of documind-chat, and the smoke once on the fault).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/hold.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_read_the_plan.
COMMANDS_03 = """make remediate PROJECT=$PROJECT SAVE=evals/reports/remediate_held.json

"""

def step_03_read_the_plan(session):
    """Run Read the plan at this checkpoint.

    remediate reads the lane three times and prints the plan. SAVE= keeps what it read, with the project id and number replaced, so the incident can be replayed later. Expect bad_revision, the change CHAT_MODEL: unset -> "gemini-3.6-flsh", and a rollback to the revision HOLD=1 recorded as serving before the fault.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: three reads, nothing changed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/plan_held.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_run_the_rollback_it_printed.
COMMANDS_04 = """PREV="$(make -s remediate OFFLINE=1 FIXTURE=evals/reports/remediate_held.json | grep -o -- '--to-revisions [a-z0-9-]*=100' | head -n 1 | sed 's/^--to-revisions //; s/=100$//')"   # the revision your plan's step 1 names, as it printed it
echo "rolling back to: $PREV"
gcloud run services update-traffic documind-chat --region "$REGION" --project "$PROJECT" --to-revisions "$PREV=100"

"""

def step_04_run_the_rollback_it_printed(session):
    """Run Run the rollback it printed at this checkpoint.

    Paste step 1's command as your plan printed it, or set PREV to the revision it names. It moves traffic only: the fault's revision stays, at 0%.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the rollback your plan printed: traffic to the revision before, by name).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rollback.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_verify.
COMMANDS_05 = """make smoke-chat PROJECT=$PROJECT

"""

def step_05_verify(session):
    """Run Verify at this checkpoint.

    The plan's step 2. Every brain should answer, because the traffic is on the revision before the fault.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the plan's verify: four brains, one question).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/smoke_rolled_back.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_read_the_lane_again.
COMMANDS_06 = """make remediate PROJECT=$PROJECT SAVE=evals/reports/remediate_rolled_back.json

"""

def step_06_read_the_lane_again(session):
    """Run Read the lane again at this checkpoint.

    Expect rolled_back. The plan starts again from the verify, and does not print the rollback a second time: its step 1 says the rollback is done.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: three reads, nothing changed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/plan_rolled_back.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_first_offline_the_plan_the_drill_should_pr),
        ('source_8', step_02_hold_the_fault),
        ('source_11', step_03_read_the_plan),
        ('source_13', step_04_run_the_rollback_it_printed),
        ('source_15', step_05_verify),
        ('source_17', step_06_read_the_lane_again),
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
