"""Lesson 10.4: Your lane: the classes, the example index and the switches

The routed Desk's code was already in the images lesson 5.6 deployed, switched off by desk_route. This cell makes sure your lane runs the code this page quotes: it pulls the kit, builds and redeploys rag-api, the UI and the chat service, then plans and applies the kit's Terraform. Terraform comes last because of DESK_JOB=true, which you keep as 5.6 said: it points the hourly overdue job at the chat image of the commit you pulled, chat:COMMIT, and commands/lesson-12.8.sh in the deploy is what builds that image. Without the flag the plan would remove the job, and make plan's guard would refuse it. The Google Chat door stays off: without GCHAT_DOOR=true the plan declares nothing of terraform/gchat.tf, nor the bridge's account in terraform/desk.tf, and the chat deploy says that documind-gchat-sa does not exist yet. The whole cell takes many minutes. The router is measured as the people it serves, so the kit has an eval account for each kind of caller. evalleaver is an acme leaver: its roles open the case desk and nothing else. evalglobex is a globex employee. Both go on their rosters. Then three accounts get desk_eval, the role that lets them call POST /v1/route. evalglobex also gets ic_member:head_office, because globex's queues, loaded below, name it as the Internal Committee, and a single desk, like any routed Desk, is refused while an office's POSH cases have no reader. The cell also sets CHAT and UI, notes the time in SINCE106 for step 8, and defines 5.6's two helpers again: sa names an account, and etok mints a token as one, for the chat service. make doc-types SEED=manifest writes acme's registry from evals/manifest.json. Each text object gets its class, pinned to the doc_key the manifest records for its bytes, and the kit cross-checks that against what your lane ingested. A figure takes its parent's class, pinned to the version on your lane, because make media drew it there. The town hall video is not_ingested unless you made it. Then the view: each object's current label, its class, its pin, its chunks and what the relabel would do. Last comes the relabel's plan. The registry is written now; the stored rows are not, until APPLY=1. An object an earlier lesson uploaded that the manifest does not name, such as 1.4's and 3.4's smoke notes or 3.8's visitor rules, shows unregistered and keeps unknown; which ones you have depends on the lessons you ran. APPLY=1 runs the plan on every store that filters by class: the Firestore rows, the Vector Search restricts, the Vertex AI Search documents and BigQuery's chunk_source. Then it expires the company's answer cache, so no cached answer from before survives. zeta and globex are seeded and applied in one run each. A run exits 3 when BigQuery deferred a statement because rows were still in its streaming buffer; run the same line again later. The same view again, for acme, without SEED. make route-index takes the route set's dev rows on the routes a company's registry covers, embeds each question once with text-embedding-005 on us-central1, and writes them to tenants/{tenant}/desk_exemplars. The version is a hash of the rows and the model, so the same rows give the same version on every lane. globex gets no index: a single desk asks no classifier and takes no vote. acme goes from off to on. globex gets its queues, with its eval account as the Internal Committee, then single mode with the statute desk: every globex question goes to the law, with no classifier.

Run order inside this file:
1. Do it: the kit you have now, on your lane (source window 6)
2. Do it: two more eval accounts (source window 10)
3. Do it: the classes (source window 12)
4. Do it: apply, for all three companies (source window 14)
5. Do it: nothing left to change (source window 16)
6. Do it: the example index (source window 18)
7. Do it: the switches (source window 20)

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


# Original CLI workflow for step_01_the_kit_you_have_now_on_your_lane.
COMMANDS_01 = """git pull   # the kit you deploy is the kit this page quotes
make build PROJECT="$PROJECT" REGION="$REGION" SERVICES="api ui"
make deploy-services PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME" \\
  SCRIPTS="commands/lesson-12.2.sh commands/lesson-12.4.sh commands/lesson-12.8.sh"
# then Terraform, now that the chat image this commit names exists: the flags you gave make up
make plan PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME" DESK_JOB=true
python commands/infrastructure.py apply --project "$PROJECT" --region "$REGION" --terraform-dir terraform

"""

def step_01_the_kit_you_have_now_on_your_lane(session):
    """Run Do it: the kit you have now, on your lane at this checkpoint.

    The routed Desk's code was already in the images lesson 5.6 deployed, switched off by desk_route. This cell makes sure your lane runs the code this page quotes: it pulls the kit, builds and redeploys rag-api, the UI and the chat service, then plans and applies the kit's Terraform. Terraform comes last because of DESK_JOB=true, which you keep as 5.6 said: it points the hourly overdue job at the chat image of the commit you pulled, chat:COMMIT, and commands/lesson-12.8.sh in the deploy is what builds that image. Without the flag the plan would remove the job, and make plan's guard would refuse it. The Google Chat door stays off: without GCHAT_DOOR=true the plan declares nothing of terraform/gchat.tf, nor the bridge's account in terraform/desk.tf, and the chat deploy says that documind-gchat-sa does not exist yet. The whole cell takes many minutes.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit you have now, on your lane; many minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    >> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/api:COMMIT from services/rag-api
    ...
    >> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/ui:COMMIT from services/frontend
    ...
    >> commands/lesson-12.2.sh (DEPLOY block)
    ...
    >> commands/lesson-12.4.sh (DEPLOY block)
    ...
    >> commands/lesson-12.8.sh (DEPLOY block)
    ...
    Plan: N to add, N to change, 0 to destroy.
    PASS: no deletes/replacements or existing CI trust changes. Reviewed plan: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
    Review the displayed changes, then run this command with 'apply' instead of 'plan'.
    PASS: selected plan, confirmed inputs, backend/workspace and state agree: .../terraform/rag-YYYYMMDDT
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_two_more_eval_accounts.
COMMANDS_02 = """export CHAT="https://documind-chat-$NUMBER.$REGION.run.app" UI="https://documind-ui-$NUMBER.$REGION.run.app"
export SINCE106="$(date -u +%FT%TZ)"
sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }
etok() { gcloud auth print-identity-token --include-email --audiences="$CHAT" \\
         --impersonate-service-account="$(sa "$1")"; }
make roster PROJECT="$PROJECT" TENANT=globex MEMBERS="$(sa evalglobex)"
make roster PROJECT="$PROJECT" TENANT=acme MEMBERS="$(sa evalleaver)"
make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$(sa evalacme)" ROLES=employee,desk_eval
make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$(sa evalleaver)" ROLES=leaver,desk_eval
make roles PROJECT="$PROJECT" TENANT=globex EMAIL="$(sa evalglobex)" ROLES=employee,desk_eval,ic_member:head_office

"""

def step_02_two_more_eval_accounts(session):
    """Run Do it: two more eval accounts at this checkpoint.

    The router is measured as the people it serves, so the kit has an eval account for each kind of caller. evalleaver is an acme leaver: its roles open the case desk and nothing else. evalglobex is a globex employee. Both go on their rosters. Then three accounts get desk_eval, the role that lets them call POST /v1/route. evalglobex also gets ic_member:head_office, because globex's queues, loaded below, name it as the Internal Committee, and a single desk, like any routed Desk, is refused while an office's POSH cases have no reader. The cell also sets CHAT and UI, notes the time in SINCE106 for step 8, and defines 5.6's two helpers again: sa names an account, and etok mints a token as one, for the chat service.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two URLs, the time, two helpers, two more eval accounts and the roles of three).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-evalglobex-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is on globex
    ...
    acme: data_region=any
    zeta: data_region=any
    globex: data_region=in
    documind-evalleaver-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is on acme
    ...
    acme: data_region=any
    zeta: data_region=any
    globex: data_region=in
    {"tenant": "acme",
     "email": "documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
     "before": ["employee"],
     "after": ["desk_eval", "employee"],
     "granted": ["desk_eval"],
     "revoked": []}
    {"tenant": "acme",
     "email": "documind-evalleaver-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
     "before": ["employee"],
     "after": ["desk_eval", "leaver"],
     "granted": ["desk_eval", "leaver"],
     "
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_classes.
COMMANDS_03 = """make doc-types PROJECT="$PROJECT" TENANT=acme SEED=manifest

"""

def step_03_the_classes(session):
    """Run Do it: the classes at this checkpoint.

    make doc-types SEED=manifest writes acme's registry from evals/manifest.json. Each text object gets its class, pinned to the doc_key the manifest records for its bytes, and the kit cross-checks that against what your lane ingested. A figure takes its parent's class, pinned to the version on your lane, because make media drew it there. The town hall video is not_ingested unless you made it. Then the view: each object's current label, its class, its pin, its chunks and what the relabel would do. Last comes the relabel's plan. The registry is written now; the stored rows are not, until APPLY=1. An object an earlier lesson uploaded that the manifest does not name, such as 1.4's and 3.4's smoke notes or 3.8's visitor rules, shows unregistered and keeps unknown; which ones you have depends on the lessons you ran.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's registry from the manifest, the view, and the relabel's plan).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    {"seed": "acme/annual_report_2026_fig3.png",
     "class": "report",
     "action": "pin",
     "pin": "yours",
     "parent": "annual_report_2026"}
    ...
    {"seed": "acme/hr_policy_2026.md", "class": "policy", "action": "pin", "pin": "acme_497809ffbaa6"}
    ...
    {"seed": "acme/labour_codes_compliance_handbook.pdf",
     "class": "guidance",
     "action": "pin",
     "pin": "acme_bbc851624beb"}
    ...
    {"seed": "acme/msa_acme_2026.md", "class": "contract", "action": "pin", "pin": "acme_cd56da350670"}
    ...
    {"seed": "acme/payment_of_gratuity_act_1972.pdf",
     "class": "statute",
     "action": "pin",
     "pin": "acme_fa044c91c671"}
    ...
    {"seed": "acme/townhall_2026_q1.mp4",
     "class": "transcript",
     "action": "not_ingested",
     "pin": "-",
 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_apply_for_all_three_companies.
COMMANDS_04 = """make doc-types PROJECT="$PROJECT" TENANT=acme APPLY=1
make doc-types PROJECT="$PROJECT" TENANT=zeta SEED=manifest APPLY=1
make doc-types PROJECT="$PROJECT" TENANT=globex SEED=manifest APPLY=1

"""

def step_04_apply_for_all_three_companies(session):
    """Run Do it: apply, for all three companies at this checkpoint.

    APPLY=1 runs the plan on every store that filters by class: the Firestore rows, the Vector Search restricts, the Vertex AI Search documents and BigQuery's chunk_source. Then it expires the company's answer cache, so no cached answer from before survives. zeta and globex are seeded and applied in one run each. A run exits 3 when BigQuery deferred a statement because rows were still in its streaming buffer; run the same line again later.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the relabel applied for acme, then zeta and globex seeded and applied).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: object                                           label          class      pin                chunks  state
    ...
    acme/annual_report_2026_fig3.png                 figure         report     yours                   N  relabel N rows
    ...
    acme/hr_policy_2026.md                           unknown        policy     acme_497809ffbaa6       N  relabel N rows
    ...
    {"relabel": "acme/annual_report_2026_fig3.png",
     "doc_key": "yours",
     "rows": N,
     "of": N,
     "from": {"figure": N},
     "to": "report",
     "why": "pinned"}
    ...
    {"relabel": "acme/hr_policy_2026.md",
     "doc_key": "acme_497809ffbaa603c49577add351033f4374ad1aefa3394f761be0c9df5e3f3173",
     "rows": N,
     "of": N,
     "from": {"unknown": N},
     "to": "policy",
     "why
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_nothing_left_to_change.
COMMANDS_05 = """make doc-types PROJECT="$PROJECT" TENANT=acme

"""

def step_05_nothing_left_to_change(session):
    """Run Do it: nothing left to change at this checkpoint.

    The same view again, for acme, without SEED.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the view again: nothing left to change).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: object                                           label          class      pin                chunks  state
    ...
    acme/annual_report_2026_fig3.png                 report         report     yours                   N  pinned
    ...
    acme/hr_policy_2026.md                           policy         policy     acme_497809ffbaa6       N  pinned
    ...
    acme/msa_acme_2026.md                            contract       contract   acme_cd56da350670       N  pinned
    ...
    acme/pune_visitor_rules.md                       unknown        -          -                       N  unregistered
    acme/smoke_note.md                               unknown        -          -                       N  unregistered
    acme/smoke_note_v1.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_the_example_index.
COMMANDS_06 = """make route-index PROJECT="$PROJECT" TENANT=acme
make route-index PROJECT="$PROJECT" TENANT=zeta

"""

def step_06_the_example_index(session):
    """Run Do it: the example index at this checkpoint.

    make route-index takes the route set's dev rows on the routes a company's registry covers, embeds each question once with text-embedding-005 on us-central1, and writes them to tenants/{tenant}/desk_exemplars. The version is a hash of the rows and the model, so the same rows give the same version on every lane. globex gets no index: a single desk asks no classifier and takes no vote.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the exemplar index for the two routed tenants: about 200 embeddings each).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"tenant": "acme",
     "rows": 198,
     "routes": {"handbook": 51, "out_of_scope": 18, "statute": 129},
     "index_version": "d15e143dd357",
     "embedding_model": "text-embedding-005",
     "written": 198,
     "deleted": [],
     "note": "the router (services/chat/desk_router.py) reads it within 5 minutes"}
    {"tenant": "zeta",
     "rows": 198,
     "routes": {"handbook": 51, "out_of_scope": 18, "statute": 129},
     "index_version": "d15e143dd357",
     "embedding_model": "text-embedding-005",
     "written": 198,
     "deleted": [],
     "note": "the router (services/chat/desk_router.py) reads it within 5 minutes"}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

# Original CLI workflow for step_07_the_switches.
COMMANDS_07 = """make desk PROJECT="$PROJECT" TENANT=acme DESK_ROUTE=on
sed "s/you@example.com/$(sa evalglobex)/g" evals/desk/queues.globex.json > "$HOME/queues.globex.json"
make desk-queues PROJECT="$PROJECT" TENANT=globex FILE="$HOME/queues.globex.json"
make desk PROJECT="$PROJECT" TENANT=globex DESK_ROUTE=single DESK_SINGLE=statute

"""

def step_07_the_switches(session):
    """Run Do it: the switches at this checkpoint.

    acme goes from off to on. globex gets its queues, with its eval account as the Internal Committee, then single mode with the statute desk: every globex question goes to the law, with no classifier.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme on; globex's queues, then globex in single mode).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"tenant": "acme",
     "desk_gate": "rules",
     "desk_max_parts": 1,
     "desk_route": "on",
     "desk_single": null,
     "desk_off": [],
     "note": "rag-api and the chat service read it within 60 s"}
    >> the router's three alert policies (terraform/desk_alerts.tf): make plan up DESK_ROUTER_ALERTS=true after the router has taken some turns; then keep DESK_ROUTER_ALERTS=true on every later plan
    {"tenant": "globex",
     "sections": ["grc", "payroll", "people", "posh", "privacy"],
     "posh_units": ["head_office"],
     "posh_missing": [],
     "not_readers": ["queue grc: no member holds a role that reads it", "queue privacy: no member holds a role that reads it", "queue payroll: no member holds a role that reads it", "queue
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_07)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_the_kit_you_have_now_on_your_lane),
        ('source_10', step_02_two_more_eval_accounts),
        ('source_12', step_03_the_classes),
        ('source_14', step_04_apply_for_all_three_companies),
        ('source_16', step_05_nothing_left_to_change),
        ('source_18', step_06_the_example_index),
        ('source_20', step_07_the_switches),
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
