"""Lesson 0.5: Tenants: put people and services on the rosters

So the UI, MCP and chat accounts go on all three golden tenants (acme, zeta and globex), the A2A agent's account on acme only, and the policies become acme any, zeta any, globex in. The command writes to Firestore with your Application Default Credentials; if it fails with a permission error, run gcloud auth application-default login --no-launch-browser again (Phase 2, T2). Preview first. The dry run writes nothing: Preview first. The dry run writes nothing: Now write it. The command adds members only to the tenant named by --tenant, so put yourself on each tenant in turn. Repeating the service-account entries is harmless: each one is the same Firestore document every time. Each pass prints one ... is on <tenant> line per member and service account, then acme: data_region=any, zeta: data_region=any and globex: data_region=in. Read the rosters back from Firestore, the same documents the API checks on every request: Your email and documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com appear under every tenant; documind-agent-sa appears under acme only. To let a colleague in, they need both the door and the list: IAP access on the UI, and a place on the tenant they work in. Add several at once with a comma-separated list.

Run order inside this file:
1. Tenants: put people and services on the rosters (source window 50)
2. Tenants: put people and services on the rosters (source window 52)
3. Tenants: put people and services on the rosters (source window 53)
4. Tenants: put people and services on the rosters (source window 54)

Prerequisites: demo_09_deploy_the_seven_services_the_worker_and_the_api_the_admin_console_chat_the_ui_m.
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


# Original CLI workflow for step_01_tenants_put_people_and_services_on_the_ros.
COMMANDS_01 = """cd "${DEMO_ROOT:?Restore ~/rag-env.sh}" &&
python commands/lane.py --project "${PROJECT:?Restore ~/rag-env.sh}" roster \\
  --tenant acme --members "${OPERATOR_EMAIL:?Restore ~/rag-env.sh}" --dry-run

"""

def step_01_tenants_put_people_and_services_on_the_ros(session):
    """Run Tenants: put people and services on the rosters at this checkpoint.

    So the UI, MCP and chat accounts go on all three golden tenants (acme, zeta and globex), the A2A agent's account on acme only, and the policies become acme any, zeta any, globex in. The command writes to Firestore with your Application Default Credentials; if it fails with a permission error, run gcloud auth application-default login --no-launch-browser again (Phase 2, T2). Preview first. The dry run writes nothing:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - the roster plan, written nowhere.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: would put you@your-domain on acme
    would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
    would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
    would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
    ...
    would put documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
    would set acme: data_region=any
    would set zeta: data_region=any
    would set globex: data_region=in
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_tenants_put_people_and_services_on_the_ros.
COMMANDS_02 = """cd "${DEMO_ROOT:?Restore ~/rag-env.sh}" &&
for t in acme zeta globex; do
  python commands/lane.py --project "$PROJECT" roster --tenant "$t" --members "$OPERATOR_EMAIL" || break
done

"""

def step_02_tenants_put_people_and_services_on_the_ros(session):
    """Run Tenants: put people and services on the rosters at this checkpoint.

    Preview first. The dry run writes nothing: Now write it. The command adds members only to the tenant named by --tenant, so put yourself on each tenant in turn. Repeating the service-account entries is harmless: each one is the same Firestore document every time.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - you on all three tenants.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_tenants_put_people_and_services_on_the_ros.
COMMANDS_03 = """cd "$DEMO_ROOT" && python - <<'PY'
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from shared import tenancy
for t in ("acme", "zeta", "globex"):
    print(t, tenancy.list_members(t))
PY

"""

def step_03_tenants_put_people_and_services_on_the_ros(session):
    """Run Tenants: put people and services on the rosters at this checkpoint.

    Each pass prints one ... is on <tenant> line per member and service account, then acme: data_region=any, zeta: data_region=any and globex: data_region=in. Read the rosters back from Firestore, the same documents the API checks on every request:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - who is on each roster.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_tenants_put_people_and_services_on_the_ros.
COMMANDS_04 = """NEW_MEMBERS='colleague@your-domain'        # comma-separated for more than one
TENANT='acme'
for who in $(printf '%s' "$NEW_MEMBERS" | tr ',' ' '); do
  gcloud iap web add-iam-policy-binding --project="$PROJECT" \\
    --resource-type=cloud-run --service=documind-ui --region="$REGION" \\
    --member="user:$who" --role='roles/iap.httpsResourceAccessor' >/dev/null &&
  echo "  IAP access on documind-ui: $who" || break
done &&
python commands/lane.py --project "$PROJECT" roster --tenant "$TENANT" --members "$NEW_MEMBERS"

"""

def step_04_tenants_put_people_and_services_on_the_ros(session):
    """Run Tenants: put people and services on the rosters at this checkpoint.

    Your email and documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com appear under every tenant; documind-agent-sa appears under acme only. To let a colleague in, they need both the door and the list: IAP access on the UI, and a place on the tenant they work in. Add several at once with a comma-separated list.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - a colleague: IAP access plus one roster.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_50', step_01_tenants_put_people_and_services_on_the_ros),
        ('source_52', step_02_tenants_put_people_and_services_on_the_ros),
        ('source_53', step_03_tenants_put_people_and_services_on_the_ros),
        ('source_54', step_04_tenants_put_people_and_services_on_the_ros),
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
