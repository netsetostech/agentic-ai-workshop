# Lesson 0.4: Prove the lane, break it once, and switch it off

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_ui_the_smoke_s_question_asked_by_you.py](demo_03_the_ui_the_smoke_s_question_asked_by_you.py) | The UI: the smoke's question, asked by you |
| 4 | [demo_04_make_preflight_what_the_lane_stands_on.py](demo_04_make_preflight_what_the_lane_stands_on.py) | make preflight: what the lane stands on |
| 5 | [demo_05_make_smoke_one_line_per_check.py](demo_05_make_smoke_one_line_per_check.py) | make smoke: one line per check |
| 6 | [demo_06_break_it_once_a_tenant_nobody_lists.py](demo_06_break_it_once_a_tenant_nobody_lists.py) | Break it once: a tenant nobody lists |
| 7 | [demo_07_rest_health_ready_and_version_by_hand.py](demo_07_rest_health_ready_and_version_by_hand.py) | REST: /health, /ready and /version by hand |
| 8 | [demo_08_save_the_session_the_state_the_inputs_the_keys.py](demo_08_save_the_session_the_state_the_inputs_the_keys.py) | Save the session: the state, the inputs, the keys |
| 9 | [demo_09_make_off_and_zero_instances.py](demo_09_make_off_and_zero_instances.py) | make off, and zero instances |
| 10 | [demo_10_what_still_bills_when_nothing_runs.py](demo_10_what_still_bills_when_nothing_runs.py) | What still bills when nothing runs |
| 11 | [demo_11_next_session_a_restored_shell.py](demo_11_next_session_a_restored_shell.py) | Next session: a restored shell |
| 12 | [demo_12_make_down_and_what_only_deleting_the_project_removes.py](demo_12_make_down_and_what_only_deleting_the_project_removes.py) | make down, and what only deleting the project removes |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Conditional recovery

- [recovery/demo_08_save_the_session_the_state_the_inputs_the_keys.py](recovery/demo_08_save_the_session_the_state_the_inputs_the_keys.py) — It refuses to save without PROJECT, REGION and DEMO_ROOT, which the setup block sets. Then it checks the source session, the record of which commit of the kit the lane was deployed from, and the resume checks it again: If ~/rag-source-session.env does not exist, the save stops with STOP: Missing rag-source-session.env; restore the original source setup. The kit's commands/git-source.sh writes that file for a source repository that keeps the kit under deploy/; your clone keeps it at the root, so if the save stops on it, write the file once yourself, in the same format, from your clone's current commit:

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's smoke checks the kit's own index only when a request ran on it, so point acme at it for the duration and put the pin back before you switch off, in step 9. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until step 9, just before make off.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's smoke checks the kit's own index only when a request ran on it, so point acme at it for the duration and put the pin back before you switch off, in step 9. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's smoke checks the kit's own index only when a request ran on it, so point acme at it for the duration and put the pin back before you switch off, in step 9. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_ui_the_smoke_s_question_asked_by_you.py

Before any command, use the lane the way a person does, and notice which identity is asking. The smoke test in step 5 asks one question. Ask it yourself first, in the browser, so that you know what a working answer looks like before a script judges one. The UI's address is built from your project number and region, the same way the setup block built API:

**`step_01_the_ui_the_smoke_s_question_asked_by_you(session)` — The UI: the smoke's question, asked by you / The UI: the smoke's question, asked by you**

Before any command, use the lane the way a person does, and notice which identity is asking. The smoke test in step 5 asks one question. Ask it yourself first, in the browser, so that you know what a working answer looks like before a script judges one. The UI's address is built from your project number and region, the same way the setup block built API:

Operation: bash — run in the operator shell (prints your UI's address).

Expected shape, not a promised result:

```text
https://documind-ui-NUMBER.asia-south1.run.app
```

### demo_04_make_preflight_what_the_lane_stands_on.py

The script is short enough to read whole. It checks the tools (gcloud, terraform, make, python), that Terraform is at least 1.9, that gcloud is signed in, that the project exists and has billing, that the state bucket exists, that 22 APIs are enabled, and that the one Python package make roster needs is importable. Every check is a read, and every MISS line carries the command that fixes it. Run it with your state bucket. The script's own usage line names the bucket after the project, <project>-tfstate, and the cell uses that name unless you have already exported another. Do not leave TFSTATE_BUCKET off: the Makefile's default, documind-tfstate, is a bucket name only one project in the world can own, and it is not yours.

**`step_01_make_preflight_what_the_lane_stands_on(session)` — make preflight: what the lane stands on / make preflight: what the lane stands on**

The script is short enough to read whole. It checks the tools (gcloud, terraform, make, python), that Terraform is at least 1.9, that gcloud is signed in, that the project exists and has billing, that the state bucket exists, that 22 APIs are enabled, and that the one Python package make roster needs is importable. Every check is a read, and every MISS line carries the command that fixes it. Run it with your state bucket. The script's own usage line names the bucket after the project, <project>-tfstate, and the cell uses that name unless you have already exported another. Do not leave TFSTATE_BUCKET off: the Makefile's default, documind-tfstate, is a bucket name only one project in the world can own, and it is not yours.

Operation: bash — run in the operator shell, in the kit (read-only; creates nothing; under a minute).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/preflight.txt]
```

### demo_05_make_smoke_one_line_per_check.py

No guard-project, and no variables passed: smoke.py reads everything from its environment. These are the names it reads, and what it does when one is missing: Three of them decide who is asking and about what. DOCUMIND_PROJECT gives the identity: without DOCUMIND_IMPERSONATE_SA, the script impersonates documind-ui-sa in that project. DOCUMIND_TENANT gives the tenant, and its default is tenant-smoke. Hold on to that default; step 6 is about it. Run the script with no URL at all and it refuses, then prints its own checklist. This costs nothing and touches nothing: main() returns before it mints a token or opens a connection. The last required check asks the same question with no token at all. A service that answers everybody would pass every check above it, so this one asserts a refusal: 401 or 403, and anything else is a failure. Run it with the three variables, the tenant included. API, PROJECT and TENANT come from the setup block; TENANT is acme.

**`step_01_make_smoke_one_line_per_check(session)` — make smoke: one line per check / make smoke: one line per check**

No guard-project, and no variables passed: smoke.py reads everything from its environment. These are the names it reads, and what it does when one is missing: Three of them decide who is asking and about what. DOCUMIND_PROJECT gives the identity: without DOCUMIND_IMPERSONATE_SA, the script impersonates documind-ui-sa in that project. DOCUMIND_TENANT gives the tenant, and its default is tenant-smoke. Hold on to that default; step 6 is about it. Run the script with no URL at all and it refuses, then prints its own checklist. This costs nothing and touches nothing: main() returns before it mints a token or opens a connection.

Operation: bash — run in the operator shell, in the kit (no network: smoke.py stops before its first call).

Expected shape, not a promised result:

```text
DOCUMIND_API_URL is not set — this is a LIVE test, run it after `make up`.

DocuMind AI — live smoke test (Tier B).

Run this AFTER `make up` against a real deployment to prove the RAG API is
alive end-to-end. Uses only the Python standard library + the `gcloud` CLI
(for the identity token), so it runs anywhere gcloud is authenticated.

It is NOT part of the offline dry run — offline, validate.py only syntax-checks
this file. On live day:

    export DOCUMIND_API_URL=https://documind-api-xxx.run.app
    export DOCUMIND_PROJECT=documind-ai-live-0901
    python deploy/smoke/smoke.py

Checks:
    1. GET  /health                -> 200 {"status":"ok"}
    2. GET  /ready                 -> 200 (tolerates 404 if not implemented)
    3. POST /v1/query              -> 200 with answer + citations + answerable
    3b. the same question with no token -> 401/403 (the door refuses before the roster is asked)
    3c. (SEMANTIC_CACHE=on only) the same question again -> a hit: cache_hit=semantic, backend=cache,
        the same citations. Off, the line says so and asserts nothing.
    4. (optional) BigQuery query-log row for today (informational)
    5. (optional) documind-chat remembers across two requests - 8.5's gate, the checkpointer.
       Needs DOCUMIND_CHAT_URL and DOCUMIND_CHAT_TOKEN (an ID token IAP accepts for the chat
       surface, e.g. `gcloud auth print-identity-token --audiences=<IAP client id>`).

Identity: the ID token IS who you are (12.8, shared/iap.py's bearer leg). rag-api verifies it
and checks the impersonated account against the tenant roster - so DOCUMIND_IMPERSONATE_SA
must be a member of DOCUMIND_TENANT, or check 3 is a 403. No x-user-email / x-tenant-id
headers are sent: nothing reads them outside AUTH_MODE=dev, and this is a live test.

Exit code is non-zero if any required check fails.
exit 2
```

**`step_02_make_smoke_one_line_per_check(session)` — make smoke: one line per check / make smoke: one line per check**

The last required check asks the same question with no token at all. A service that answers everybody would pass every check above it, so this one asserts a refusal: 401 or 403, and anything else is a failure. Run it with the three variables, the tenant included. API, PROJECT and TENANT come from the setup block; TENANT is acme.

Operation: bash — run in the operator shell, in the kit (one question answered, one refused; about a minute).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke_green.txt]
```

### demo_06_break_it_once_a_tenant_nobody_lists.py

The same smoke without DOCUMIND_TENANT: one check fails, and you follow it to the code that printed it and the code that refused. Run the smoke again without the tenant, which the Makefile's header example leaves out too. Keep the URL and the project, so the smoke still has an identity to ask with. env -u makes sure no DOCUMIND_TENANT survives from an earlier shell, and the last command prints make's own exit status. Find why. The question named a tenant because smoke.py always sends one: DOCUMIND_TENANT, and without it, tenant-smoke. Its own docstring predicted this failure: Check the roster. Which tenants is documind-ui-sa on? make roster decides, through one function in commands/lane.py, and its dry run prints the plan without touching Firestore: Check the roster. Which tenants is documind-ui-sa on? make roster decides, through one function in commands/lane.py, and its dry run prints the plan without touching Firestore: The UI's account is on acme, zeta and globex, and no line names tenant-smoke. The plan is what make roster wrote in lesson 0.3. To see the rosters as they are now, read them from Firestore with the kit's own module:

**`step_01_break_it_once_a_tenant_nobody_lists(session)` — Break it once: a tenant nobody lists / Break it once: a tenant nobody lists**

The same smoke without DOCUMIND_TENANT: one check fails, and you follow it to the code that printed it and the code that refused. Run the smoke again without the tenant, which the Makefile's header example leaves out too. Keep the URL and the project, so the smoke still has an identity to ask with. env -u makes sure no DOCUMIND_TENANT survives from an earlier shell, and the last command prints make's own exit status.

Operation: bash — run in the operator shell, in the kit (the same smoke without a tenant: one check fails, on purpose).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke_broken.txt]
```

**`step_02_break_it_once_a_tenant_nobody_lists(session)` — Break it once: a tenant nobody lists / Break it once: a tenant nobody lists**

Find why. The question named a tenant because smoke.py always sends one: DOCUMIND_TENANT, and without it, tenant-smoke. Its own docstring predicted this failure: Check the roster. Which tenants is documind-ui-sa on? make roster decides, through one function in commands/lane.py, and its dry run prints the plan without touching Firestore:

Operation: bash — run in the operator shell, in the kit (no network: the dry run prints and returns).

Expected shape, not a promised result:

```text
would put you@your-company.com on acme
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

**`step_03_break_it_once_a_tenant_nobody_lists(session)` — Break it once: a tenant nobody lists / Break it once: a tenant nobody lists**

Check the roster. Which tenants is documind-ui-sa on? make roster decides, through one function in commands/lane.py, and its dry run prints the plan without touching Firestore: The UI's account is on acme, zeta and globex, and no line names tenant-smoke. The plan is what make roster wrote in lesson 0.3. To see the rosters as they are now, read them from Firestore with the kit's own module:

Operation: bash — run in the operator shell, in the kit (two Firestore reads; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/roster_read.txt]
```

### demo_07_rest_health_ready_and_version_by_hand.py

The three GETs the smoke and the restore both use, and what each one can and cannot prove. Call them yourself, with the setup block's token, then call /health once more with no token at all:

**`step_01_rest_health_ready_and_version_by_hand(session)` — REST: /health, /ready and /version by hand / REST: /health, /ready and /version by hand**

The three GETs the smoke and the restore both use, and what each one can and cannot prove. Call them yourself, with the setup block's token, then call /health once more with no token at all:

Operation: bash — run in the operator shell (four GETs; tok is the setup block's function).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rest_reads.txt]
```

### demo_08_save_the_session_the_state_the_inputs_the_keys.py

infrastructure.py writes the six values it confirmed (project_id, region, billing_account_id, github_repository, github_repository_id, deploy_ref) to the inputs file, and every later plan, check and apply reads them back. A different project or region in the same checkout is refused, never migrated. The selected-plan record is the other file, and it does not outlive the apply: So after make up there is no saved plan waiting to be applied again; the next change to the lane starts with a new make plan, which is the point. Read both: If ~/rag-source-session.env does not exist, the save stops with STOP: Missing rag-source-session.env; restore the original source setup. The kit's commands/git-source.sh writes that file for a source repository that keeps the kit under deploy/; your clone keeps it at the root, so if the save stops on it, write the file once yourself, in the same format, from your clone's current commit: Then save. The cell exports the two names the helper saves that the setup block calls something else: PROJECT_NUMBER (the setup's NUMBER) and OPERATOR_EMAIL (its ME). TFSTATE_BUCKET is already exported, from step 4.

**`step_01_the_saved_inputs_beside_the_terraform(session)` — Save the session: the state, the inputs, the keys / The saved inputs, beside the Terraform**

infrastructure.py writes the six values it confirmed (project_id, region, billing_account_id, github_repository, github_repository_id, deploy_ref) to the inputs file, and every later plan, check and apply reads them back. A different project or region in the same checkout is refused, never migrated. The selected-plan record is the other file, and it does not outlive the apply: So after make up there is no saved plan waiting to be applied again; the next change to the lane starts with a new make plan, which is the point. Read both:

Operation: bash — run in the operator shell, in the kit (reads one object's listing and one local file).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/state_inputs.txt]
```

**`step_02_the_session_keys_in_your_home_directory(session)` — Save the session: the state, the inputs, the keys / The session keys, in your home directory**

If ~/rag-source-session.env does not exist, the save stops with STOP: Missing rag-source-session.env; restore the original source setup. The kit's commands/git-source.sh writes that file for a source repository that keeps the kit under deploy/; your clone keeps it at the root, so if the save stops on it, write the file once yourself, in the same format, from your clone's current commit: Then save. The cell exports the two names the helper saves that the setup block calls something else: PROJECT_NUMBER (the setup's NUMBER) and OPERATOR_EMAIL (its ME). TFSTATE_BUCKET is already exported, from step 4.

Operation: bash — run in the operator shell, in the kit, at the end of every session.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/save_session.txt]
```

### recovery/demo_08_save_the_session_the_state_the_inputs_the_keys.py

It refuses to save without PROJECT, REGION and DEMO_ROOT, which the setup block sets. Then it checks the source session, the record of which commit of the kit the lane was deployed from, and the resume checks it again: If ~/rag-source-session.env does not exist, the save stops with STOP: Missing rag-source-session.env; restore the original source setup. The kit's commands/git-source.sh writes that file for a source repository that keeps the kit under deploy/; your clone keeps it at the root, so if the save stops on it, write the file once yourself, in the same format, from your clone's current commit:

**`step_01_the_session_keys_in_your_home_directory(session)` — Save the session: the state, the inputs, the keys / The session keys, in your home directory**

It refuses to save without PROJECT, REGION and DEMO_ROOT, which the setup block sets. Then it checks the source session, the record of which commit of the kit the lane was deployed from, and the resume checks it again: If ~/rag-source-session.env does not exist, the save stops with STOP: Missing rag-source-session.env; restore the original source setup. The kit's commands/git-source.sh writes that file for a source repository that keeps the kit under deploy/; your clone keeps it at the root, so if the save stops on it, write the file once yourself, in the same format, from your clone's current commit:

Operation: bash — run in the operator shell, in the kit, once per machine and only if the save below stops on it.

### demo_09_make_off_and_zero_instances.py

Four switches and a check. Each switch is a make target of its own, and each line starts with -, which tells make to carry on when the line fails. That matters on your lane. make up deploys seven services, and of the four make off floors, only documind-ui is among them: the small model, the vLLM engine and the gateway arrive in Module 9. Their switches fail on a service that does not exist, make notes each error as ignored, and the loop prints absent for them. gke-down removes the vLLM workload from the GKE cluster, which has none yet, and leaves the cluster and its node standing, as its own message says. The loop at the end reads each floor back from the service's template. The same four floors are lowered every night at 23:00 IST by the documind-off job, so a floor you forget costs an evening; make off-now runs that job by hand. Now run the target: One thing make off does not cover is worth knowing before you ever raise a floor: MIN_INSTANCES reaches three deploy scripts, the UI's, the MCP server's and the A2A peer's, and make off floors only the UI. Deploy with MIN_INSTANCES=1 for a session day, and the read below will show documind-mcp and documind-agent still holding an instance after make off. The cell waits out the idle window, then reads instance_count for every Cloud Run service in the project, one point a minute over the last half hour:

**`step_01_make_off_and_zero_instances(session)` — make off, and zero instances / make off, and zero instances**

Four switches and a check. Each switch is a make target of its own, and each line starts with -, which tells make to carry on when the line fails. That matters on your lane. make up deploys seven services, and of the four make off floors, only documind-ui is among them: the small model, the vLLM engine and the gateway arrive in Module 9. Their switches fail on a service that does not exist, make notes each error as ignored, and the loop prints absent for them. gke-down removes the vLLM workload from the GKE cluster, which has none yet, and leaves the cluster and its node standing, as its own message says. The loop at the end reads each floor back from the service's template. The same four floors are lowered every night at 23:00 IST by the documind-off job, so a floor you forget costs an evening; make off-now runs that job by hand. Now run the target:

Operation: bash — run in the operator shell, in the kit, after the setup section's pin-back window.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/off.txt]
```

**`step_02_make_off_and_zero_instances(session)` — make off, and zero instances / make off, and zero instances**

One thing make off does not cover is worth knowing before you ever raise a floor: MIN_INSTANCES reaches three deploy scripts, the UI's, the MCP server's and the A2A peer's, and make off floors only the UI. Deploy with MIN_INSTANCES=1 for a session day, and the read below will show documind-mcp and documind-agent still holding an instance after make off. The cell waits out the idle window, then reads instance_count for every Cloud Run service in the project, one point a minute over the last half hour:

Operation: bash — run in the operator shell after make off, with no request to the lane in between (reads Cloud Monitoring; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/zero_instances.txt]
```

### demo_10_what_still_bills_when_nothing_runs.py

The table prices the lane where it runs. Its services, index, databases and cluster are in Mumbai, asia-south1 (Spanner's configuration is regional-asia-south1 on every lane), and each unit price is Mumbai's list price as Google's pages gave it on 7 October 2026, before tax. Prices change, and an Indian billing account is charged at Google's own rupee prices rather than at Rs 85 to the dollar. The number that counts is your bill: in the console, Billing, then Reports, filtered to your project and grouped by SKU, on a day the lane sat idle. What the table leaves out bills by size or by use rather than by the hour: Firestore, the buckets, the container images, the two RAG Engine corpora and the two data stores, the nightly job's minute, the BigQuery tables' few rows. At the corpus's size these are small next to the six lines, and the bill shows them as well. Now read the six lines on your own lane: the machine behind the deployed index and the shard size the API picked, Spanner's edition and units, the databases' tier, the cluster's location and node, the connector's machines.

**`step_01_the_arithmetic(session)` — What still bills when nothing runs / The arithmetic**

The table prices the lane where it runs. Its services, index, databases and cluster are in Mumbai, asia-south1 (Spanner's configuration is regional-asia-south1 on every lane), and each unit price is Mumbai's list price as Google's pages gave it on 7 October 2026, before tax. Prices change, and an Indian billing account is charged at Google's own rupee prices rather than at Rs 85 to the dollar. The number that counts is your bill: in the console, Billing, then Reports, filtered to your project and grouped by SKU, on a day the lane sat idle. What the table leaves out bills by size or by use rather than by the hour: Firestore, the buckets, the container images, the two RAG Engine corpora and the two data stores, the nightly job's minute, the BigQuery tables' few rows. At the corpus's size these are small next to the six lines, and the bill shows them as well. Now read the six lines on your own lane: the machine behind the deployed index and the shard size the API picked, Spanner's edition and units, the databases' tier, the cluster's location and node, the connector's machines.

Operation: bash — run in the operator shell (read-only: seven listings of what bills by the hour).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/standing_resources.txt]
```

### demo_11_next_session_a_restored_shell.py

A new shell, one function, and proof that it found the same project and region, and an API that answers. Next weekend, the shell you saved from is gone. Open a new one and restore it:

**`step_01_next_session_a_restored_shell(session)` — Next session: a restored shell / Next session: a restored shell**

A new shell, one function, and proof that it found the same project and region, and an API that answers. Next weekend, the shell you saved from is gone. Open a new one and restore it:

Operation: bash — run in a new shell at the start of your next session.

### demo_12_make_down_and_what_only_deleting_the_project_removes.py

MANAGED_SEARCH is true by default, so the state holds two Vertex AI Search data stores, one for acme and one for zeta, each with prevent_destroy. Terraform rejects any plan that would destroy such a resource, and a destroy plan destroys everything, so this one destroys nothing: the six lines of step 10 keep billing after make down, still Rs 2,666 a day with a MEDIUM index. The list the recipe prints afterwards does not name the data stores; the kit's README does. Lesson 7.3 meets the same guard from the stores' side. The recipe's last line is the one that ends the bill: delete the throwaway project. Shutting a project down stops all of its billing; for 30 days the project can still be restored, and then it and everything in it are deleted. The same page adds two cautions: charges already run up can still arrive until the current billing cycle ends, and it advises disabling billing on the project before you shut it down. One switch would block the deletion itself: AUDIT_LOCK=true locks the audit bucket's five-year retention and liens the project, which is why it is false for a lab.

**`step_01_make_down_and_what_only_deleting_the_proje(session)` — make down, and what only deleting the project removes / make down, and what only deleting the project removes**

MANAGED_SEARCH is true by default, so the state holds two Vertex AI Search data stores, one for acme and one for zeta, each with prevent_destroy. Terraform rejects any plan that would destroy such a resource, and a destroy plan destroys everything, so this one destroys nothing: the six lines of step 10 keep billing after make down, still Rs 2,666 a day with a MEDIUM index. The list the recipe prints afterwards does not name the data stores; the kit's README does. Lesson 7.3 meets the same guard from the stores' side. The recipe's last line is the one that ends the bill: delete the throwaway project. Shutting a project down stops all of its billing; for 30 days the project can still be restored, and then it and everything in it are deleted. The same page adds two cautions: charges already run up can still arrive until the current billing cycle ends, and it advises disabling billing on the project before you shut it down. One switch would block the deletion itself: AUDIT_LOCK=true locks the audit bucket's five-year retention and liens the project, which is why it is false for a lab.

Operation: bash — run in the operator shell, in the kit, when you are finished with the lane - not now: Module 1 starts on this lane.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/down.txt]
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's smoke checks the kit's own index only when a request ran on it, so point acme at it for the duration and put the pin back before you switch off, in step 9. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until step 9, just before make off.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's smoke checks the kit's own index only when a request ran on it, so point acme at it for the duration and put the pin back before you switch off, in step 9. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until step 9, just before make off.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_0.4_Prove_Switch_Off_WIX.html`. All 76 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `227e9752d5a191e48fe77a44ab7d3f59135b88bd`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
