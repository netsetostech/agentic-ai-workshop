"""Lesson 0.4: Save the session: the state, the inputs, the keys

infrastructure.py writes the six values it confirmed (project_id, region, billing_account_id, github_repository, github_repository_id, deploy_ref) to the inputs file, and every later plan, check and apply reads them back. A different project or region in the same checkout is refused, never migrated. The selected-plan record is the other file, and it does not outlive the apply: So after make up there is no saved plan waiting to be applied again; the next change to the lane starts with a new make plan, which is the point. Read both: If ~/rag-source-session.env does not exist, the save stops with STOP: Missing rag-source-session.env; restore the original source setup. The kit's commands/git-source.sh writes that file for a source repository that keeps the kit under deploy/; your clone keeps it at the root, so if the save stops on it, write the file once yourself, in the same format, from your clone's current commit: Then save. The cell exports the two names the helper saves that the setup block calls something else: PROJECT_NUMBER (the setup's NUMBER) and OPERATOR_EMAIL (its ME). TFSTATE_BUCKET is already exported, from step 4.

Run order inside this file:
1. The saved inputs, beside the Terraform (source window 41)
2. The session keys, in your home directory (source window 48)

Prerequisites: demo_07_rest_health_ready_and_version_by_hand.
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


# Original CLI workflow for step_01_the_saved_inputs_beside_the_terraform.
COMMANDS_01 = """gcloud storage ls -l "gs://$TFSTATE_BUCKET/**/default.tfstate"      # the state make up wrote
python -c 'import json; print(sorted(json.load(open("terraform/runbook-project.auto.tfvars.json"))))'   # the inputs' names, not their values

"""

def step_01_the_saved_inputs_beside_the_terraform(session):
    """Run The saved inputs, beside the Terraform at this checkpoint.

    infrastructure.py writes the six values it confirmed (project_id, region, billing_account_id, github_repository, github_repository_id, deploy_ref) to the inputs file, and every later plan, check and apply reads them back. A different project or region in the same checkout is refused, never migrated. The selected-plan record is the other file, and it does not outlive the apply: So after make up there is no saved plan waiting to be applied again; the next change to the lane starts with a new make plan, which is the point. Read both:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads one object's listing and one local file).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/state_inputs.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_session_keys_in_your_home_directory.
COMMANDS_02 = """source commands/session-restart.sh                     # defines the helper's functions; runs nothing
export PROJECT_NUMBER="$NUMBER" OPERATOR_EMAIL="$ME"   # two names it saves that the setup block calls NUMBER and ME
rag_save_session
sed 's/=.*//' ~/rag-resume.env; stat -c '%a %n' ~/rag-resume.env   # the names saved, never the values; the file's mode

"""

def step_02_the_session_keys_in_your_home_directory(session):
    """Run The session keys, in your home directory at this checkpoint.

    If ~/rag-source-session.env does not exist, the save stops with STOP: Missing rag-source-session.env; restore the original source setup. The kit's commands/git-source.sh writes that file for a source repository that keeps the kit under deploy/; your clone keeps it at the root, so if the save stops on it, write the file once yourself, in the same format, from your clone's current commit: Then save. The cell exports the two names the helper saves that the setup block calls something else: PROJECT_NUMBER (the setup's NUMBER) and OPERATOR_EMAIL (its ME). TFSTATE_BUCKET is already exported, from step 4.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, at the end of every session.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/save_session.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_41', step_01_the_saved_inputs_beside_the_terraform),
        ('source_48', step_02_the_session_keys_in_your_home_directory),
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
