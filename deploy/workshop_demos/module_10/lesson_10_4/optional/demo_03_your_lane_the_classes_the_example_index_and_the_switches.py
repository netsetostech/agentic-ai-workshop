"""Lesson 10.4: Your lane: the classes, the example index and the switches

Optional: turn the Google Chat door on. Plan with GCHAT_DOOR=true beside DESK_JOB=true and apply, deploy chat again so documind-gchat-sa may call it, then make deploy-gchat. Keep GCHAT_DOOR=true on every later make plan and make up. The Workspace part, the door's smoke and its rows need it.

Run order inside this file:
1. Optional: the Google Chat door and its bridge (source window 8)

Prerequisites: demo_03_your_lane_the_classes_the_example_index_and_the_switches.
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


# Original CLI workflow for step_01_optional_the_google_chat_door_and_its_brid.
COMMANDS_01 = """# the Terraform part of make plan up, with the door: keep GCHAT_DOOR=true on every later make plan and make up
make plan PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME" DESK_JOB=true GCHAT_DOOR=true
python commands/infrastructure.py apply --project "$PROJECT" --region "$REGION" --terraform-dir terraform
# chat again, as make up would: its deploy lets documind-gchat-sa, which exists now, call documind-chat
make deploy-services PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME" SCRIPTS=commands/lesson-12.8.sh
make deploy-gchat PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"

"""

def step_01_optional_the_google_chat_door_and_its_brid(session):
    """Run Optional: the Google Chat door and its bridge at this checkpoint.

    The Google Chat door is a second front door onto the same POST /v1/desk. When a person messages the "HR Desk" app, Google Chat calls an HTTPS endpoint, and here that endpoint is documind-gchat, a Cloud Run service of its own: the bridge, services/gchat/. It asks the Desk on the person's behalf and posts the Desk's reply into the chat as a card. It makes no model call and calls no service but the chat service. Run this part if you will try step 4's part in Google Chat or step 7's smoke of the door; otherwise skip it, with those parts and step 8's read of the door's rows. The plan, with GCHAT_DOOR=true, adds the door's 11 resources: what terraform/gchat.tf declares, the documind-gchat Firestore database, the documind-gchat-work topic and its documind-gchat-push subscription, the documind-gchatpush-sa account and the Chat API, with their IAM bindings; and documind-gchat-sa, the account in terraform/desk.tf that the bridge runs as. Keep GCHAT_DOOR=true, beside DESK_JOB=true, on every later make plan and make up: without it the plan would delete the door, and make plan's guard would refuse it. The plan and apply are the Terraform part of make plan up GCHAT_DOOR=true, which the kit names as the step before make deploy-gchat (make up would also rebuild and redeploy every service). The chat deploy is the part of make up the door needs: it allows documind-gchat-sa, which exists now, to call documind-chat. make deploy-gchat refuses on a lane whose last apply had the door off; here it builds the bridge's image and deploys it with commands/gchat.sh. Two accounts may call the bridge: documind-gchatpush-sa, Pub/Sub's push identity, and documind-outsider-sa, which step 7's smoke sends to it. The script's last line allows a third, the Chat app's add-on agent, service-NUMBER@gcp-sa-gsui

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, only to turn the Google Chat door on (its Terraform with GCHAT_DOOR=true, chat again, then the bridge: its image, its service and who may call it; many minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Plan: 11 to add, 0 to change, 0 to destroy.
    PASS: no deletes/replacements or existing CI trust changes. Reviewed plan: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
    Review the displayed changes, then run this command with 'apply' instead of 'plan'.
    PASS: selected plan, confirmed inputs, backend/workspace and state agree: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
    ...
    Apply complete! Resources: 11 added, 0 changed, 0 destroyed.
    >> commands/lesson-12.8.sh (DEPLOY block)
    ...
    >> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/gchat:COMMIT from services/gchat
    ...
    >> commands/gchat.sh (DEPLOY block)
    ...
    >> the Chat app's add-on agent does not exist yet: configure the app (Google 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_8', step_01_optional_the_google_chat_door_and_its_brid),
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
