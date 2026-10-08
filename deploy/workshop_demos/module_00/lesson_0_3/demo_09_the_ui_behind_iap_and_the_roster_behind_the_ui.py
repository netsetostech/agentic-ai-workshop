"""Lesson 0.3: The UI behind IAP, and the roster behind the UI

So a visitor meets up to three checks, and each kind of visitor stops at a different one: The first two rows can be checked from the shell. A request with no sign-in should come back as a redirect to Google's accounts page (the block cuts the redirect at its query string, which carries the OAuth client's id), and IAP's policy on the service should list your address with the accessor role. The first two rows can be checked from the shell. A request with no sign-in should come back as a redirect to Google's accounts page (the block cuts the redirect at its query string, which carries the OAuth client's id), and IAP's policy on the service should list your address with the accessor role. The last two rows need a browser. Open the address the first line below prints, sign in as yourself, and look at the sidebar. Then open it in a private window and sign in with a Google account that is not in ADMIN_EMAILS. make roster ran inside make up, after the indexes were ready. It puts every member of MEMBERS, which defaults to ADMIN_EMAILS, on TENANT's roster; the UI's, the MCP server's and the chat service's accounts on all three golden tenants, because each calls the API as itself; the A2A peer's on acme only; and it records where each tenant's text may be held. Lesson 1.1 reads these documents in Firestore, and lesson 4.6 follows one request through every check that reads them. Its dry run prints the plan and writes nothing, so it can be read before it is trusted. This one was computed from commands/lane.py when this page was built, with your placeholders:

Run order inside this file:
1. The UI behind IAP, and the roster behind the UI (source window 56)
2. The UI behind IAP, and the roster behind the UI (source window 59)
3. The roster make up wrote (source window 63)

Prerequisites: demo_08_seven_services_and_the_account_each_runs_as.
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


# Original CLI workflow for step_01_the_ui_behind_iap_and_the_roster_behind_th.
COMMANDS_01 = """curl -s -o /dev/null -w '%{http_code} %{redirect_url}\\n' "https://documind-ui-$NUMBER.$REGION.run.app/" | cut -d'?' -f1
gcloud iap web get-iam-policy --resource-type=cloud-run --service=documind-ui --region="$REGION" --project="$PROJECT"

"""

def step_01_the_ui_behind_iap_and_the_roster_behind_th(session):
    """Run The UI behind IAP, and the roster behind the UI at this checkpoint.

    So a visitor meets up to three checks, and each kind of visitor stops at a different one: The first two rows can be checked from the shell. A request with no sign-in should come back as a redirect to Google's accounts page (the block cuts the redirect at its query string, which carries the OAuth client's id), and IAP's policy on the service should list your address with the accessor role.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_ui_behind_iap_and_the_roster_behind_th.
COMMANDS_02 = """echo "https://documind-ui-$NUMBER.$REGION.run.app"

"""

def step_02_the_ui_behind_iap_and_the_roster_behind_th(session):
    """Run The UI behind IAP, and the roster behind the UI at this checkpoint.

    The first two rows can be checked from the shell. A request with no sign-in should come back as a redirect to Google's accounts page (the block cuts the redirect at its query string, which carries the OAuth client's id), and IAP's policy on the service should list your address with the accessor role. The last two rows need a browser. Open the address the first line below prints, sign in as yourself, and look at the sidebar. Then open it in a private window and sign in with a Google account that is not in ADMIN_EMAILS.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_roster_make_up_wrote.
COMMANDS_03 = """python commands/lane.py --project "$PROJECT" roster --tenant acme --members "$ADMIN_EMAILS" --dry-run
make roster PROJECT="$PROJECT"         # the same writes make up made; running it again changes nothing

"""

def step_03_the_roster_make_up_wrote(session):
    """Run The roster make up wrote at this checkpoint.

    make roster ran inside make up, after the indexes were ready. It puts every member of MEMBERS, which defaults to ADMIN_EMAILS, on TENANT's roster; the UI's, the MCP server's and the chat service's accounts on all three golden tenants, because each calls the API as itself; the A2A peer's on acme only; and it records where each tenant's text may be held. Lesson 1.1 reads these documents in Firestore, and lesson 4.6 follows one request through every check that reads them. Its dry run prints the plan and writes nothing, so it can be read before it is trusted. This one was computed from commands/lane.py when this page was built, with your placeholders:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
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
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_56', step_01_the_ui_behind_iap_and_the_roster_behind_th),
        ('source_59', step_02_the_ui_behind_iap_and_the_roster_behind_th),
        ('source_63', step_03_the_roster_make_up_wrote),
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
