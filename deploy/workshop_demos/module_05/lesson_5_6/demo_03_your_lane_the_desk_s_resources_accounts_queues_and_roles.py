"""Lesson 5.6: Your lane: the Desk's resources, accounts, queues and roles

On a lane whose last plan predates the Desk, the plan adds 23 resources. terraform/desk.tf has 12 of them: two TTL fields (a draft's expire_at and a client token's), five indexes (one for each query the case queue makes) and five eval accounts. terraform/desk_alerts.tf has six log-based metrics and four alert policies, and terraform/storage.tf lets the chat service write the audit bucket. The one change is the log sink's filter, widened to copy the Desk's rows to BigQuery. Three switches would add more, and this lesson needs none of them: GCHAT_DOOR=true adds 11 for lesson 10.4's Google Chat door, DESK_ROUTER_ALERTS=true the router's three alert policies, and DESK_GATE_ALERTS=true the policy that pages when a company's model checks keep failing, for a lane where some company has the check on. Then come the images with the Desk's code, deployed by their own scripts. lesson-12.8.sh builds the chat image itself and lets the eval accounts invoke documind-chat. Last, make desk-job declares the hourly overdue scan on that chat image: a plan with DESK_JOB=true, which adds the job's three, then its apply. The whole cell takes many minutes. The flags are the ones you gave make up. A script cannot call the chat service as a person, so the kit has eval accounts. Each is a service account on one tenant's roster, with no project role, and make smoke-cases and this lesson's cells call as them. evalacme is an acme employee, evalgrc an acme Grievance Redressal Committee member, and evalzeta a zeta employee. make desk-operators lets you mint tokens as all five. The cell also sets CHAT and UI, notes the time in SINCE105 for step 8's log read, and defines two helpers: sa names an account, and etok mints a token as one, for the chat service. evals/desk/queues.acme.json names acme's queues: who receives each kind of case, and the company's target in days. For POSH it lists each office's Internal Committee and its district's Local Committee. The file puts you@example.com on both offices' committees, and the sed puts your own email there instead. Then make desk, with no DESK_GATE, prints acme's switches and writes nothing. evalgrc gets grc_member alone, so it can read and move grievances but cannot raise a case: the note says so. You get employee, so the Desk page shows you Tell the Desk and lets you raise cases. You also get the three roles that read: grievances, and the POSH cases of both offices.

Run order inside this file:
1. Do it: the Desk on your lane (source window 6)
2. Do it: the eval accounts (source window 8)
3. Do it: acme's queues, and its switch as it stands (source window 10)
4. Do it: the roles (source window 12)

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


# Original CLI workflow for step_01_the_desk_on_your_lane.
COMMANDS_01 = """make plan PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"   # the flags you gave make up; the plan refuses to delete
python commands/infrastructure.py apply --project "$PROJECT" --region "$REGION" --terraform-dir terraform   # make up's first line, alone
make build PROJECT="$PROJECT" REGION="$REGION" SERVICES="api ui"
make deploy-services PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME" \\
  SCRIPTS="commands/lesson-12.2.sh commands/lesson-12.4.sh commands/lesson-12.8.sh"
make desk-job PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"   # the same flags as make plan

"""

def step_01_the_desk_on_your_lane(session):
    """Run Do it: the Desk on your lane at this checkpoint.

    On a lane whose last plan predates the Desk, the plan adds 23 resources. terraform/desk.tf has 12 of them: two TTL fields (a draft's expire_at and a client token's), five indexes (one for each query the case queue makes) and five eval accounts. terraform/desk_alerts.tf has six log-based metrics and four alert policies, and terraform/storage.tf lets the chat service write the audit bucket. The one change is the log sink's filter, widened to copy the Desk's rows to BigQuery. Three switches would add more, and this lesson needs none of them: GCHAT_DOOR=true adds 11 for lesson 10.4's Google Chat door, DESK_ROUTER_ALERTS=true the router's three alert policies, and DESK_GATE_ALERTS=true the policy that pages when a company's model checks keep failing, for a lane where some company has the check on. Then come the images with the Desk's code, deployed by their own scripts. lesson-12.8.sh builds the chat image itself and lets the eval accounts invoke documind-chat. Last, make desk-job declares the hourly overdue scan on that chat image: a plan with DESK_JOB=true, which adds the job's three, then its apply. The whole cell takes many minutes. The flags are the ones you gave make up.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the Desk's Terraform, the three services rebuilt, the hourly job; many minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    Plan: 23 to add, 1 to change, 0 to destroy.
    PASS: no deletes/replacements or existing CI trust changes. Reviewed plan: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
    Review the displayed changes, then run this command with 'apply' instead of 'plan'.
    PASS: selected plan, confirmed inputs, backend/workspace and state agree: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
    ...
    Apply complete! Resources: 23 added, 1 changed, 0 destroyed.
    >> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/api:COMMIT from services/rag-api
    ...
    >> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/ui:COMMIT from services/frontend
    ...
    >> commands/lesson-12.2.sh (DEPLOY block)
    ...
    >> comma
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_eval_accounts.
COMMANDS_02 = """export CHAT="https://documind-chat-$NUMBER.$REGION.run.app" UI="https://documind-ui-$NUMBER.$REGION.run.app"
export SINCE105="$(date -u +%FT%TZ)"
sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }
etok() { gcloud auth print-identity-token --include-email --audiences="$CHAT" \\
         --impersonate-service-account="$(sa "$1")"; }
make desk-operators PROJECT="$PROJECT" ADMIN_EMAILS="$ME"
make roster PROJECT="$PROJECT" TENANT=acme MEMBERS="$(sa evalacme),$(sa evalgrc)"
make roster PROJECT="$PROJECT" TENANT=zeta MEMBERS="$(sa evalzeta)"

"""

def step_02_the_eval_accounts(session):
    """Run Do it: the eval accounts at this checkpoint.

    A script cannot call the chat service as a person, so the kit has eval accounts. Each is a service account on one tenant's roster, with no project role, and make smoke-cases and this lesson's cells call as them. evalacme is an acme employee, evalgrc an acme Grievance Redressal Committee member, and evalzeta a zeta employee. make desk-operators lets you mint tokens as all five. The cell also sets CHAT and UI, notes the time in SINCE105 for step 8's log read, and defines two helpers: sa names an account, and etok mints a token as one, for the chat service.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two URLs, two helpers, the eval accounts minted as and put on rosters).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> you@example.com may mint tokens as documind-evalacme-sa
    >> you@example.com may mint tokens as documind-evalzeta-sa
    >> you@example.com may mint tokens as documind-evalglobex-sa
    >> you@example.com may mint tokens as documind-evalleaver-sa
    >> you@example.com may mint tokens as documind-evalgrc-sa
    documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is on acme
    documind-evalgrc-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is on acme
    ...
    acme: data_region=any
    zeta: data_region=any
    globex: data_region=in
    documind-evalzeta-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is on zeta
    ...
    acme: data_region=any
    zeta: data_region=any
    globex: data_region=in
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_acme_s_queues_and_its_switch_as_it_stands.
COMMANDS_03 = """sed "s/you@example.com/$ME/g" evals/desk/queues.acme.json > "$HOME/queues.acme.json"   # you sit on both committees
make desk-queues PROJECT="$PROJECT" TENANT=acme FILE="$HOME/queues.acme.json"
make desk PROJECT="$PROJECT" TENANT=acme   # the switch as it stands: no DESK_GATE, so nothing is written

"""

def step_03_acme_s_queues_and_its_switch_as_it_stands(session):
    """Run Do it: acme's queues, and its switch as it stands at this checkpoint.

    evals/desk/queues.acme.json names acme's queues: who receives each kind of case, and the company's target in days. For POSH it lists each office's Internal Committee and its district's Local Committee. The file puts you@example.com on both offices' committees, and the sed puts your own email there instead. Then make desk, with no DESK_GATE, prints acme's switches and writes nothing.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's queues with your email in them, then acme's switches as they stand).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"tenant": "acme",
     "sections": ["grc", "payroll", "people", "posh", "privacy"],
     "posh_units": ["hyderabad", "pune"],
     "posh_missing": [],
     "not_readers": ["ic hyderabad: you@example.com", "ic hyderabad: ic.hyderabad.member@example.com", "ic pune: ic.pune.presiding@example.com", "ic pune: you@example.com", "queue grc: no member holds a role that reads it", "queue privacy: no member holds a role that reads it", "queue payroll: no member holds a role that reads it", "queue people: no member holds a role that reads it"],
     "action": "written"}
    {"tenant": "acme",
     "desk_gate": "rules",
     "desk_max_parts": 1,
     "desk_route": "off",
     "desk_single": null,
     "desk_off": []}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_the_roles.
COMMANDS_04 = """make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$(sa evalgrc)" ROLES=grc_member
make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$ME" ROLES=employee,grc_member,ic_member:hyderabad,ic_member:pune

"""

def step_04_the_roles(session):
    """Run Do it: the roles at this checkpoint.

    evalgrc gets grc_member alone, so it can read and move grievances but cannot raise a case: the note says so. You get employee, so the Desk page shows you Tell the Desk and lets you raise cases. You also get the three roles that read: grievances, and the POSH cases of both offices.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the committee's account and you get your roles).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"tenant": "acme",
     "email": "documind-evalgrc-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
     "before": ["employee"],
     "after": ["grc_member"],
     "granted": ["grc_member"],
     "revoked": ["employee"],
     "note": "no employee or leaver role: this person reaches no desk, the case desk included - add employee unless that is meant"}
    {"tenant": "acme",
     "email": "you@example.com",
     "before": ["employee"],
     "after": ["employee", "grc_member", "ic_member:hyderabad", "ic_member:pune"],
     "granted": ["grc_member", "ic_member:hyderabad", "ic_member:pune"],
     "revoked": []}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_the_desk_on_your_lane),
        ('source_8', step_02_the_eval_accounts),
        ('source_10', step_03_acme_s_queues_and_its_switch_as_it_stands),
        ('source_12', step_04_the_roles),
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
