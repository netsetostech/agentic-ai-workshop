# Lesson 0.3: Understand the project, identities and resource map, and deploy the lane

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| 3 | [demo_03_a_blank_project_made_ready_for_a_plan.py](demo_03_a_blank_project_made_ready_for_a_plan.py) | A blank project, made ready for a plan |
| 6 | [demo_06_make_plan_a_saved_plan_checked_before_you_apply_it.py](demo_06_make_plan_a_saved_plan_checked_before_you_apply_it.py) | make plan: a saved plan, checked before you apply it |
| 7 | [demo_07_make_up_apply_that_plan_then_build_deploy_and_seed.py](demo_07_make_up_apply_that_plan_then_build_deploy_and_seed.py) | make up: apply that plan, then build, deploy and seed |
| 8 | [demo_08_seven_services_and_the_account_each_runs_as.py](demo_08_seven_services_and_the_account_each_runs_as.py) | Seven services, and the account each runs as |
| 9 | [demo_09_the_ui_behind_iap_and_the_roster_behind_the_ui.py](demo_09_the_ui_behind_iap_and_the_roster_behind_the_ui.py) | The UI behind IAP, and the roster behind the UI |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Conditional recovery

- [recovery/demo_07_make_up_apply_that_plan_then_build_deploy_and_seed.py](recovery/demo_07_make_up_apply_that_plan_then_build_deploy_and_seed.py) — Now run it. It takes a long time: Cloud SQL, the GKE cluster and the deployed index each take minutes to create, and the builds run one after another. Run it inside tmux if your shell has it, so that a closed browser tab or a dropped connection does not stop an apply halfway; an interrupted apply needs a new plan. time reports how long it took. A plan refused as stale (The saved plan is stale; create a new plan, or The selected plan is missing or changed): the state, the inputs or the file changed since make plan. Run step 6 again, read the new plan, then make up. An apply that failed halfway: keep the state as it is. Terraform has recorded everything it created, so the next make plan lists only what is still missing; read it, then make up. Never delete the state or terraform/.terraform to "start clean": the next apply would try to create everything again over resources that exist. A build that stops at storage.objects.get with a 403 naming the Compute Engine default account: Cloud Build runs as that account when the kit names none, and in an organization created on or after 3 May 2024 it is created without the broad role older projects gave it. Grant it exactly what a build needs (the block below), and wait a few minutes for IAM to apply the grants. The apply had already finished by then and its plan is used up, so run make plan (it reports no changes) and make up, which applies nothing and carries on from the build. A drift line after the apply means the plan after it is not empty: a resource the provider reads back differently from how it was written. It does not stop make up, but it is a definition to fix before the next apply repeats it. A bq-views failure naming a table or a field that does not exist: the view reads the log sink's table, and the kit's own comment 

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### demo_03_a_blank_project_made_ready_for_a_plan.py

A Google Cloud API is off until a project turns it on, and Terraform cannot create a resource whose API is off. make apis turns on the 40 the lane uses, in two calls, because the Service Usage API takes at most twenty at a time. It is safe to run again; an API already on stays on. Terraform keeps its record of what it built, the state, in a bucket, so that the next plan in any shell compares the files with what exists instead of trying to create everything again. Bucket names are global: the first person in the world to create a name owns it. The Makefile's default, documind-tfstate, is one name for the whole world and can serve only one lane, so the setup block named yours after your project, the form the kit's own smoke/preflight.sh uses in its example. It exported TFSTATE_BUCKET and TFSTATE_PREFIX too, so the targets that connect to the state later (make tf-backend, make down) find this one. Versioning keeps every earlier copy of the state file, which is how a damaged state is recovered. The kit includes a keyless pipeline: terraform/wif.tf declares a workload identity pool that lets GitHub Actions workflows from one repository, on one branch, become sa-documind-cicd, the pipeline's account, with no key file anywhere. That account may act as 8 accounts (step 4), which makes this one of the most powerful settings in your project: whoever controls that repository's workflows can deploy code that runs as your services. Lesson 11.1 builds and deploys through this trust. A new project has to name it now, and the kit refuses to guess. Name a repository you own, for instance your fork of netsetos/agents_workshop_learner. Its numeric id is what the trust is really keyed on, because a repository's name can be released and claimed by someone else and its id cannot. prepare then reads your project and its billing account, checks that the project has no GitHub provider the state does not know about, and saves the three values with your project, region and billing account in terraform/runbook-project.auto.tfvars.json, a local file Git ignores. Every later plan reads them from there. IAP signs people in with Google's OAuth, and an OAuth sign-in needs a consent screen with a name on it. Configure it once in the console, under Google Auth Platform > Branding: an app name such as DocuMind and your address as the support e-mail. The kit cannot check this for you, and its preflight says so on its last line. Whether you need more depends on where your project lives: IAP signs people in with Google's OAuth, and an OAuth sign-in needs a consent screen with a name on it. Configure it once in the console, under Google Auth Platform > Branding: an app name such as DocuMind and your address as the support e-mail. The kit cannot check this for you, and its preflight says so on its last line. Whether you need more depends on where your project lives: If it prints organization and the people you will let in belong to that organization, IAP's Google-managed sign-in is enough. If it prints nothing, which is the usual case for a project made with a personal account, Google's IAP guide says you must bring your own OAuth client: IAP's managed client serves only people inside an organization, and a project outside any organization has none. In the console, create one under Google Auth Platform > Clients (or APIs & Services > Credentials), type Web application; once it exists, add the redirect URI https://iap.googleapis.com/v1/oauth/clientIds/CLIENT_ID:handleRedirect with its own client id in place of CLIENT_ID. Set the consent screen's audience to External; while it is in testing, list each address in ADMIN_EMAILS as a test user. Then hand the client to IAP for the whole project: make preflight reads, and creates nothing: the four tools on PATH and Terraform's version, your sign-in, the project and its billing, the state bucket, 22 of the APIs, and the one Python package make roster needs. A line that starts with MISS carries the command that fixes it.

**`step_01_1_the_apis(session)` — A blank project, made ready for a plan / 1. The APIs**

A Google Cloud API is off until a project turns it on, and Terraform cannot create a resource whose API is off. make apis turns on the 40 the lane uses, in two calls, because the Service Usage API takes at most twenty at a time. It is safe to run again; an API already on stays on.

Operation: bash — run in the operator shell, once per project.

**`step_02_2_a_state_bucket_of_your_own(session)` — A blank project, made ready for a plan / 2. A state bucket of your own**

Terraform keeps its record of what it built, the state, in a bucket, so that the next plan in any shell compares the files with what exists instead of trying to create everything again. Bucket names are global: the first person in the world to create a name owns it. The Makefile's default, documind-tfstate, is one name for the whole world and can serve only one lane, so the setup block named yours after your project, the form the kit's own smoke/preflight.sh uses in its example. It exported TFSTATE_BUCKET and TFSTATE_PREFIX too, so the targets that connect to the state later (make tf-backend, make down) find this one. Versioning keeps every earlier copy of the state file, which is how a damaged state is recovered.

Operation: bash — run in the operator shell, once per project.

**`step_03_3_the_one_repository_you_trust_to_deploy(session)` — A blank project, made ready for a plan / 3. The one repository you trust to deploy**

The kit includes a keyless pipeline: terraform/wif.tf declares a workload identity pool that lets GitHub Actions workflows from one repository, on one branch, become sa-documind-cicd, the pipeline's account, with no key file anywhere. That account may act as 8 accounts (step 4), which makes this one of the most powerful settings in your project: whoever controls that repository's workflows can deploy code that runs as your services. Lesson 11.1 builds and deploys through this trust. A new project has to name it now, and the kit refuses to guess. Name a repository you own, for instance your fork of netsetos/agents_workshop_learner. Its numeric id is what the trust is really keyed on, because a repository's name can be released and claimed by someone else and its id cannot. prepare then reads your project and its billing account, checks that the project has no GitHub provider the state does not know about, and saves the three values with your project, region and billing account in terraform/runbook-project.auto.tfvars.json, a local file Git ignores. Every later plan reads them from there.

Operation: bash — run in the operator shell, once per project (your repository, not the example's).

Expected shape, not a promised result:

```text
PASS: saved confirmed inputs to /home/you/deploy_module_rag/terraform/runbook-project.auto.tfvars.json
CI trust: YOUR-GITHUB-USER/YOUR-REPO (ID NUMBER) / refs/heads/main
```

**`step_04_4_the_sign_in_screen_iap_will_show(session)` — A blank project, made ready for a plan / 4. The sign-in screen IAP will show**

IAP signs people in with Google's OAuth, and an OAuth sign-in needs a consent screen with a name on it. Configure it once in the console, under Google Auth Platform > Branding: an app name such as DocuMind and your address as the support e-mail. The kit cannot check this for you, and its preflight says so on its last line. Whether you need more depends on where your project lives:

Operation: bash — run in the operator shell: is your project inside an organization?.

**`step_05_4_the_sign_in_screen_iap_will_show(session)` — A blank project, made ready for a plan / 4. The sign-in screen IAP will show**

IAP signs people in with Google's OAuth, and an OAuth sign-in needs a consent screen with a name on it. Configure it once in the console, under Google Auth Platform > Branding: an app name such as DocuMind and your address as the support e-mail. The kit cannot check this for you, and its preflight says so on its last line. Whether you need more depends on where your project lives: If it prints organization and the people you will let in belong to that organization, IAP's Google-managed sign-in is enough. If it prints nothing, which is the usual case for a project made with a personal account, Google's IAP guide says you must bring your own OAuth client: IAP's managed client serves only people inside an organization, and a project outside any organization has none. In the console, create one under Google Auth Platform > Clients (or APIs & Services > Credentials), type Web application; once it exists, add the redirect URI https://iap.googleapis.com/v1/oauth/clientIds/CLIENT_ID:handleRedirect with its own client id in place of CLIENT_ID. Set the consent screen's audience to External; while it is in testing, list each address in ADMIN_EMAILS as a test user. Then hand the client to IAP for the whole project:

Operation: bash — run in the operator shell, only for a project with no organization.

**`step_06_5_ask_the_kit_whether_the_project_is_ready(session)` — A blank project, made ready for a plan / 5. Ask the kit whether the project is ready**

make preflight reads, and creates nothing: the four tools on PATH and Terraform's version, your sign-in, the project and its billing, the state bucket, 22 of the APIs, and the one Python package make roster needs. A line that starts with MISS carries the command that fixes it.

Operation: bash — run in the operator shell.

Expected shape, not a promised result:

```text
ok    gcloud on PATH
  ok    terraform on PATH
  ok    make on PATH
  ok    python on PATH
  ok    terraform VERSION (backend.tf wants >= 1.9)
  ok    signed in as you@example.com
  ok    project documind-ai-YOUR-ID exists
  ok    billing linked
  ok    state bucket gs://documind-ai-YOUR-ID-tfstate
  ok    APIs enabled
  ok    google-cloud-firestore for make roster

preflight clean - next: make plan, then make up
not checkable from here: the OAuth consent screen (Google Auth Platform > Branding) - IAP needs it
```

### demo_06_make_plan_a_saved_plan_checked_before_you_apply_it.py

The check reads Terraform's machine-readable plan, not the text you scroll through. It refuses an incomplete plan, inputs that differ from the confirmed ones, any change to the existing CI trust, and any delete: a replacement is a delete followed by a create, so it is refused too. On a blank project nothing exists to delete, and the check passes. It earns its place on every plan after this one. Run it now. Terraform prints the whole plan, one block per resource, so the block keeps a copy in ~/plan.log and then prints only the lines that summarize it. The plan file is binary; Terraform turns it into JSON on request. The cell below counts what the plan would create, by type, in the same format as the count this page made from the kit's files, so the two can be read side by side. Run it before make up: the apply consumes the selection record that names the file.

**`step_01_make_plan_a_saved_plan_checked_before_you(session)` — make plan: a saved plan, checked before you apply it / make plan: a saved plan, checked before you apply it**

The check reads Terraform's machine-readable plan, not the text you scroll through. It refuses an incomplete plan, inputs that differ from the confirmed ones, any change to the existing CI trust, and any delete: a replacement is a delete followed by a create, so it is refused too. On a blank project nothing exists to delete, and the check passes. It earns its place on every plan after this one. Run it now. Terraform prints the whole plan, one block per resource, so the block keeps a copy in ~/plan.log and then prints only the lines that summarize it.

Operation: bash — run in the operator shell.

**`step_02_every_resource_counted_from_the_saved_plan(session)` — make plan: a saved plan, checked before you apply it / Every resource, counted from the saved plan**

The plan file is binary; Terraform turns it into JSON on request. The cell below counts what the plan would create, by type, in the same format as the count this page made from the kit's files, so the two can be read side by side. Run it before make up: the apply consumes the selection record that names the file.

Operation: bash — run in the operator shell, after make plan and before make up.

### demo_07_make_up_apply_that_plan_then_build_deploy_and_seed.py

The deploy step is the reason the kit has no second copy of its deploy flags: it cuts the block between # ---- DEPLOY ---- and the next marker out of each script and runs it as it is, in the order the services must come up. The worker comes first, because the push subscription Terraform made already points at its address. Now run it. It takes a long time: Cloud SQL, the GKE cluster and the deployed index each take minutes to create, and the builds run one after another. Run it inside tmux if your shell has it, so that a closed browser tab or a dropped connection does not stop an apply halfway; an interrupted apply needs a new plan. time reports how long it took.

**`step_01_make_up_apply_that_plan_then_build_deploy(session)` — make up: apply that plan, then build, deploy and seed / make up: apply that plan, then build, deploy and seed**

The deploy step is the reason the kit has no second copy of its deploy flags: it cuts the block between # ---- DEPLOY ---- and the next marker out of each script and runs it as it is, in the order the services must come up. The worker comes first, because the push subscription Terraform made already points at its address. Now run it. It takes a long time: Cloud SQL, the GKE cluster and the deployed index each take minutes to create, and the builds run one after another. Run it inside tmux if your shell has it, so that a closed browser tab or a dropped connection does not stop an apply halfway; an interrupted apply needs a new plan. time reports how long it took.

Operation: bash — run in the operator shell.

### recovery/demo_07_make_up_apply_that_plan_then_build_deploy_and_seed.py

Now run it. It takes a long time: Cloud SQL, the GKE cluster and the deployed index each take minutes to create, and the builds run one after another. Run it inside tmux if your shell has it, so that a closed browser tab or a dropped connection does not stop an apply halfway; an interrupted apply needs a new plan. time reports how long it took. A plan refused as stale (The saved plan is stale; create a new plan, or The selected plan is missing or changed): the state, the inputs or the file changed since make plan. Run step 6 again, read the new plan, then make up. An apply that failed halfway: keep the state as it is. Terraform has recorded everything it created, so the next make plan lists only what is still missing; read it, then make up. Never delete the state or terraform/.terraform to "start clean": the next apply would try to create everything again over resources that exist. A build that stops at storage.objects.get with a 403 naming the Compute Engine default account: Cloud Build runs as that account when the kit names none, and in an organization created on or after 3 May 2024 it is created without the broad role older projects gave it. Grant it exactly what a build needs (the block below), and wait a few minutes for IAM to apply the grants. The apply had already finished by then and its plan is used up, so run make plan (it reports no changes) and make up, which applies nothing and carries on from the build. A drift line after the apply means the plan after it is not empty: a resource the provider reads back differently from how it was written. It does not stop make up, but it is a definition to fix before the next apply repeats it. A bq-views failure naming a table or a field that does not exist: the view reads the log sink's table, and the kit's own comment 

**`step_01_make_up_apply_that_plan_then_build_deploy(session)` — make up: apply that plan, then build, deploy and seed / make up: apply that plan, then build, deploy and seed**

Now run it. It takes a long time: Cloud SQL, the GKE cluster and the deployed index each take minutes to create, and the builds run one after another. Run it inside tmux if your shell has it, so that a closed browser tab or a dropped connection does not stop an apply halfway; an interrupted apply needs a new plan. time reports how long it took. A plan refused as stale (The saved plan is stale; create a new plan, or The selected plan is missing or changed): the state, the inputs or the file changed since make plan. Run step 6 again, read the new plan, then make up. An apply that failed halfway: keep the state as it is. Terraform has recorded everything it created, so the next make plan lists only what is still missing; read it, then make up. Never delete the state or terraform/.terraform to "start clean": the next apply would try to create everything again over resources that exist. A build that stops at storage.objects.get with a 403 naming the Compute Engine default account: Cloud Build runs as that account when the kit names none, and in an organization created on or after 3 May 2024 it is created without the broad role older projects gave it. Grant it exactly what a build needs (the block below), and wait a few minutes for IAM to apply the grants. The apply had already finished by then and its plan is used up, so run make plan (it reports no changes) and make up, which applies nothing and carries on from the build. A drift line after the apply means the plan after it is not empty: a resource the provider reads back differently from how it was written. It does not stop make up, but it is a definition to fix before the next apply repeats it. A bq-views failure naming a table or a field that does not exist: the view reads the log sink's table, and the kit's own comment 

Operation: bash — run in the operator shell, only if the build stopped on that 403.

### demo_08_seven_services_and_the_account_each_runs_as.py

The first proof: the services are up, and each runs as the account step 4 said it would. Cloud Run keeps the account a service runs as on the service itself. Listing the services with that one field beside the name is the whole check: 7 rows, each with its own account, matching the table in step 4. Step 5 left one fact open: the deployed index's machine follows the index's shard size, and the kit lets the service choose it. Read both from the live lane; step 10 prices the row that matches.

**`step_01_seven_services_and_the_account_each_runs_a(session)` — Seven services, and the account each runs as / Seven services, and the account each runs as**

The first proof: the services are up, and each runs as the account step 4 said it would. Cloud Run keeps the account a service runs as on the service itself. Listing the services with that one field beside the name is the whole check: 7 rows, each with its own account, matching the table in step 4.

Operation: bash — run in the operator shell.

**`step_02_the_shard_size_the_service_chose(session)` — Seven services, and the account each runs as / The shard size the service chose**

Step 5 left one fact open: the deployed index's machine follows the index's shard size, and the kit lets the service choose it. Read both from the live lane; step 10 prices the row that matches.

Operation: bash — run in the operator shell.

### demo_09_the_ui_behind_iap_and_the_roster_behind_the_ui.py

So a visitor meets up to three checks, and each kind of visitor stops at a different one: The first two rows can be checked from the shell. A request with no sign-in should come back as a redirect to Google's accounts page (the block cuts the redirect at its query string, which carries the OAuth client's id), and IAP's policy on the service should list your address with the accessor role. The first two rows can be checked from the shell. A request with no sign-in should come back as a redirect to Google's accounts page (the block cuts the redirect at its query string, which carries the OAuth client's id), and IAP's policy on the service should list your address with the accessor role. The last two rows need a browser. Open the address the first line below prints, sign in as yourself, and look at the sidebar. Then open it in a private window and sign in with a Google account that is not in ADMIN_EMAILS. make roster ran inside make up, after the indexes were ready. It puts every member of MEMBERS, which defaults to ADMIN_EMAILS, on TENANT's roster; the UI's, the MCP server's and the chat service's accounts on all three golden tenants, because each calls the API as itself; the A2A peer's on acme only; and it records where each tenant's text may be held. Lesson 1.1 reads these documents in Firestore, and lesson 4.6 follows one request through every check that reads them. Its dry run prints the plan and writes nothing, so it can be read before it is trusted. This one was computed from commands/lane.py when this page was built, with your placeholders:

**`step_01_the_ui_behind_iap_and_the_roster_behind_th(session)` — The UI behind IAP, and the roster behind the UI / The UI behind IAP, and the roster behind the UI**

So a visitor meets up to three checks, and each kind of visitor stops at a different one: The first two rows can be checked from the shell. A request with no sign-in should come back as a redirect to Google's accounts page (the block cuts the redirect at its query string, which carries the OAuth client's id), and IAP's policy on the service should list your address with the accessor role.

Operation: bash — run in the operator shell.

**`step_02_the_ui_behind_iap_and_the_roster_behind_th(session)` — The UI behind IAP, and the roster behind the UI / The UI behind IAP, and the roster behind the UI**

The first two rows can be checked from the shell. A request with no sign-in should come back as a redirect to Google's accounts page (the block cuts the redirect at its query string, which carries the OAuth client's id), and IAP's policy on the service should list your address with the accessor role. The last two rows need a browser. Open the address the first line below prints, sign in as yourself, and look at the sidebar. Then open it in a private window and sign in with a Google account that is not in ADMIN_EMAILS.

Operation: bash — run in the operator shell.

**`step_03_the_roster_make_up_wrote(session)` — The UI behind IAP, and the roster behind the UI / The roster make up wrote**

make roster ran inside make up, after the indexes were ready. It puts every member of MEMBERS, which defaults to ADMIN_EMAILS, on TENANT's roster; the UI's, the MCP server's and the chat service's accounts on all three golden tenants, because each calls the API as itself; the A2A peer's on acme only; and it records where each tenant's text may be held. Lesson 1.1 reads these documents in Firestore, and lesson 4.6 follows one request through every check that reads them. Its dry run prints the plan and writes nothing, so it can be read before it is trusted. This one was computed from commands/lane.py when this page was built, with your placeholders:

Operation: bash — run in the operator shell.

Expected shape, not a promised result:

```text
would put you@example.com on acme
would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
would put documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
would put documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
would put documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
would put documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
would set acme: data_region=any
would set zeta: data_region=any
would set globex: data_region=in
```

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_0.3_Deploy_Lane_WIX.html`. All 71 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `840ab0010164fb7bf8900b43fb668aa2e80d08fb`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
