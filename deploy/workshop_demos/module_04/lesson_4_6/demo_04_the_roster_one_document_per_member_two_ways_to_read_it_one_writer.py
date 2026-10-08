"""Lesson 4.6: The roster: one document per member, two ways to read it, one writer

Do it: the three rosters, as Firestore holds them make roster runs this command without --dry-run. The dry run prints the memberships and the data-region policies it would set, and writes nothing.

Run order inside this file:
1. Do it: the three rosters, as Firestore holds them (source window 17)
2. Do it: the plan make roster would write for you (source window 19)

Prerequisites: demo_03_the_door_and_the_verifier_who_may_knock_and_what_makes_a_token_count.
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


def step_01_the_three_rosters_as_firestore_holds_them(session):
    """Run Do it: the three rosters, as Firestore holds them at this checkpoint.

    Do it: the three rosters, as Firestore holds them

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the three rosters in Firestore; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme    5 member(s)
        documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
        documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
        documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
        documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
        you@example.com
    zeta    3 member(s)
        documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
        documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
        documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    globex  3 member(s)
        documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
        documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
        documind-ui-sa@documind-ai-YOUR-ID.ia
    """
    import os
    from google.cloud import firestore
    db = firestore.Client(project=os.environ["PROJECT"])
    for t in ("acme", "zeta", "globex"):
        members = sorted(d.id for d in db.collection("tenants").document(t).collection("members").stream())
        print(f"{t:7} {len(members)} member(s)")
        for m in members:
            print("   ", m)

# Original CLI workflow for step_02_the_plan_make_roster_would_write_for_you.
COMMANDS_02 = """python commands/lane.py --project "$PROJECT" roster --tenant acme --members "$ME" --dry-run

"""

def step_02_the_plan_make_roster_would_write_for_you(session):
    """Run Do it: the plan make roster would write for you at this checkpoint.

    make roster runs this command without --dry-run. The dry run prints the memberships and the data-region policies it would set, and writes nothing.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (make roster's plan; --dry-run writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: would put you@example.com on acme
    would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
    would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
    would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
    would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
    would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
    would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
    would put documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
    would put documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
    would put documind-chat-sa@documind-ai-
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_the_three_rosters_as_firestore_holds_them),
        ('source_19', step_02_the_plan_make_roster_would_write_for_you),
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
