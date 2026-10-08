"""Lesson 10.4: The Desk page, and the HR Desk app in Google Chat

Optional, and only with the door on, a Business or Enterprise Google Workspace account and a Chat app you configured in the Google Cloud console: deploy the Google Chat bridge again so it admits the app's add-on agent, put your Workspace address on acme's roster, switch desk_gchat on for acme, and print the two questions to send the HR Desk app. Without Workspace, skip it: the page's expected conversation shows what it does, and make smoke-gchat proves the door's refusals with the door on.

Run order inside this file:
1. Optional, with Google Workspace: the HR Desk app in Google Chat (source window 25)

Prerequisites: demo_04_the_desk_page_and_the_hr_desk_app_in_google_chat.
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


# Original CLI workflow for step_01_optional_with_google_workspace_the_hr_desk.
COMMANDS_01 = """WS="employee@example.com"   # yours: the Google Workspace address you will message the app from
make deploy-gchat PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"   # again, now that the app exists
make roster PROJECT="$PROJECT" TENANT=acme MEMBERS="$WS"
make desk PROJECT="$PROJECT" TENANT=acme DESK_GCHAT=on
python - <<'PY'
import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from smoke.smoke_cases import POSH
rows = {r["id"]: r for r in (json.loads(x) for x in open("evals/routes.jsonl", encoding="utf-8") if x.strip())}
print(f"lk-06: {rows['lk-06']['question']}")
print(f"POSH:  {POSH}")
PY

"""

def step_01_optional_with_google_workspace_the_hr_desk(session):
    """Run Optional, with Google Workspace: the HR Desk app in Google Chat at this checkpoint.

    Configure the app. In the console, on your lane's project, open the Google Chat API's Configuration page. The kit expects: Then run the cell as the operator. It deploys the bridge again, so that its last line now allows the add-on agent. It puts your Workspace address on acme's roster, where with no roles document it holds employee. Then it turns the door on for acme. make desk refuses DESK_GCHAT=on while the company's gate is off, and unless its routed Desk is on or single. For a company whose data_region is in, it also needs CONFIRM_RESIDENCY=1, because the Desk's answers and their quotes then sit in the company's Google Chat. acme's gate has run its rules since lesson 5.6 and its router is on since step 3, and its data_region is any. The chat service reads the switch within 60 seconds.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, only with Google Workspace and once the app is configured (the bridge again, your address on acme's roster, the door on for acme, two questions to paste).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/gchat:COMMIT from services/gchat
    ...
    >> commands/gchat.sh (DEPLOY block)
    ...
    employee@example.com is on acme
    ...
    acme: data_region=any
    zeta: data_region=any
    globex: data_region=in
    {"tenant": "acme",
     "desk_gate": "rules",
     "desk_max_parts": 1,
     "desk_route": "on",
     "desk_single": null,
     "desk_off": [],
     "desk_gchat": "on",
     "note": "rag-api and the chat service read it within 60 s"}
    lk-06: What is the notice period for a confirmed E3?
    POSH:  My manager keeps making sexual comments about my body. What can I do?
    """
    manual_checkpoint("Only with a Business or Enterprise Google Workspace account. First configure the Chat app in the Google Cloud console, on your lane's project (Google Chat API, Configuration), as the page's step 4 lists: the name HR Desk, the add-on model, the HTTP endpoint URL https://documind-gchat-NUMBER.REGION.run.app with no trailing slash, and the app available to your Workspace address. Set WS in this cell to that address. Type done to deploy the bridge again, roster the address on acme and switch the door on; then, in Google Chat, send HR Desk the lk-06 question and the POSH line it prints.")
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_optional_with_google_workspace_the_hr_desk),
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
