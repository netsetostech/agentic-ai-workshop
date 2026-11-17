"""Lesson 5.8: Your lane: the People team's reader, and a request for a person on the Desk page

A request for a person goes to acme's people queue, the People team's. A case there is read by whoever holds people_ops, and nobody on your lane holds it yet: lesson 5.6 gave you the roles that read grievances and POSH cases. So far a request for a person would reach no one. The cell sets the names the later steps use, notes the time in SINCE108 for step 7's log read, and gives you people_ops beside the four roles you have. ROLES= sets exactly the roles it lists, so it names all five.

Run order inside this file:
1. Do it: the People team's reader (source window 6)

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


# Original CLI workflow for step_01_the_people_team_s_reader.
COMMANDS_01 = """export CHAT="https://documind-chat-$NUMBER.$REGION.run.app" SINCE108="$(date -u +%FT%TZ)"
sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }
etok() { gcloud auth print-identity-token --include-email --audiences="$CHAT" \\
         --impersonate-service-account="$(sa "$1")"; }
make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$ME" ROLES=employee,grc_member,ic_member:hyderabad,ic_member:pune,people_ops

"""

def step_01_the_people_team_s_reader(session):
    """Run Do it: the People team's reader at this checkpoint.

    A request for a person goes to acme's people queue, the People team's. A case there is read by whoever holds people_ops, and nobody on your lane holds it yet: lesson 5.6 gave you the roles that read grievances and POSH cases. So far a request for a person would reach no one. The cell sets the names the later steps use, notes the time in SINCE108 for step 7's log read, and gives you people_ops beside the four roles you have. ROLES= sets exactly the roles it lists, so it names all five.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the names the lane steps use, then people_ops beside your four roles).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/roles.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_the_people_team_s_reader),
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
