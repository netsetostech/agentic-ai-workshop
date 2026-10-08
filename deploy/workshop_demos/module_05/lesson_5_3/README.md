# Lesson 5.3: Deploy MCP and verify authorized access

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_door_as_the_kit_writes_it_down.py](demo_03_the_door_as_the_kit_writes_it_down.py) | The door, as the kit writes it down |
| 4 | [demo_04_deploy_and_read_it_back.py](demo_04_deploy_and_read_it_back.py) | Deploy, and read it back |
| 5 | [demo_05_the_gate_make_smoke_mcp.py](demo_05_the_gate_make_smoke_mcp.py) | The gate: make smoke-mcp |
| 6 | [demo_06_one_call_at_each_door_and_both_sides_of_the_answer.py](demo_06_one_call_at_each_door_and_both_sides_of_the_answer.py) | One call at each door, and both sides of the answer |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Conditional recovery

- [recovery/demo_04_deploy_and_read_it_back.py](recovery/demo_04_deploy_and_read_it_back.py) — Only if the build stopped at storage.objects.get (the page's box): once, as a project owner, grant the project's default build account read access to its source in the PROJECT_cloudbuild bucket, push access to the documind repository and log writing. Then run the build and deploy again.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_door_as_the_kit_writes_it_down.py

Do it

**`step_01_the_door_as_the_kit_writes_it_down(session)` — The door, as the kit writes it down / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the door as the kit writes it down; no network).

Expected shape, not a promised result:

```text
documind-mcp, as commands/lesson-7.2.sh deploys it:
  --no-allow-unauthenticated  --ingress=all  --min-instances=${MIN_INSTANCES:-0}  --service-account=documind-mcp-sa
  SELF_URL=https://documind-mcp-$PROJECT_NUMBER.${REGION:-us-central1}.run.app
  RAG_API_URL=https://documind-api-$PROJECT_NUMBER.${REGION:-us-central1}.run.app
  FASTMCP_STATELESS_HTTP=true
  RAG_TIMEOUT_S=90
who may call it (roles/run.invoker): documind-ui-sa, documind-agent-sa, documind-outsider-sa
the tenants each caller may read through it (lane.py's roster_plan):
  documind-ui-sa         acme, zeta, globex
  documind-agent-sa      acme
  documind-outsider-sa   none
the account rag-api sees for every MCP retrieval: documind-mcp-sa, on acme, zeta, globex
```

### demo_04_deploy_and_read_it_back.py

Do it: build and deploy Do it: read it back

**`step_01_build_and_deploy(session)` — Deploy, and read it back / Do it: build and deploy**

Do it: build and deploy

Operation: bash — run in the operator shell, in the kit (build the image, deploy it, bind its callers).

Expected shape, not a promised result:

```text
>> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/mcp:COMMIT from services/mcp
Creating temporary archive of ... file(s) totalling ... MiB before compression.
...
DONE ... asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/mcp:COMMIT
>> commands/lesson-7.2.sh (DEPLOY block)
Deploying container to Cloud Run service [documind-mcp] in project [documind-ai-YOUR-ID] region [asia-south1]
...
Service URL: https://documind-mcp-NUMBER.asia-south1.run.app
Updated IAM policy for service [documind-mcp].   (three times: ui, agent, outsider)
...
>> you@example.com may mint tokens as documind-ui-sa
>> you@example.com may mint tokens as documind-outsider-sa
```

**`step_02_read_it_back(session)` — Deploy, and read it back / Do it: read it back**

Do it: read it back

Operation: bash — run in the operator shell, in the kit (the service as deployed, against the script).

Expected shape, not a promised result:

```text
serving     documind-mcp-00004-k7w at https://documind-mcp-NUMBER.asia-south1.run.app
  runs as     documind-mcp-sa
  ingress     all
  SELF_URL    https://documind-mcp-NUMBER.asia-south1.run.app
  invokers    documind-agent-sa, documind-outsider-sa, documind-ui-sa
  the script  documind-agent-sa, documind-outsider-sa, documind-ui-sa - the same
```

### recovery/demo_04_deploy_and_read_it_back.py

Only if the build stopped at storage.objects.get (the page's box): once, as a project owner, grant the project's default build account read access to its source in the PROJECT_cloudbuild bucket, push access to the documind repository and log writing. Then run the build and deploy again.

**`step_01_build_and_deploy(session)` — Deploy, and read it back / Do it: build and deploy**

Cloud Build runs a build as the project's default build account, and the kit names no other: cloudbuild.yaml has no serviceAccount, and make build passes no --service-account. On a project made since mid-2024 that account is the Compute Engine default account, NUMBER-compute@developer.gserviceaccount.com. In an organization created on or after 3 May 2024 it is created without the Editor role Google used to give it. The build then cannot read its own source, the archive gcloud builds submit has just uploaded to the documind-ai-YOUR-ID_cloudbuild bucket, and stops at could not resolve source with a 403 naming that account. This grants that account the three things this build does, once, as a project owner: read its source in that one bucket, push the image to the documind repository, and write its log lines (cloudbuild.yaml logs to Cloud Logging only). It does not grant Editor or roles/cloudbuild.builds.builder. Granted on the project, either one can read, write and delete every object in every bucket, the uploads bucket of customer documents included, and the Compute Engine default account is also what a VM or a Cloud Run service runs as when nobody names another.

Operation: bash — run in the operator shell, once, as a project owner, only if the build stopped at storage.objects.get.

### demo_05_the_gate_make_smoke_mcp.py

Do it

**`step_01_the_gate_make_smoke_mcp(session)` — The gate: make smoke-mcp / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the module's gate).

Expected shape, not a promised result:

```text
DocuMind MCP - live smoke test
  target: https://documind-mcp-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] health  {"status":"ok","profile":"gcp","self_url":"https://documind-mcp-NUMBER.asia-south1.run.app"}
  [PASS] tools/list  ['calculate_processing_cost', 'corpus_stats', 'list_documents', 'retrieve']
  [PASS] retrieve  answerable=True citations=5  'Five years of continuous service [1].'
  [PASS] outsider refused  documind-outsider-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is not on tenant 'acme''s roster
  --------------------------------------------------------
  4 passed, 0 failed
```

### demo_06_one_call_at_each_door_and_both_sides_of_the_answer.py

Do it: every door Do it: both sides

**`step_01_every_door(session)` — One call at each door, and both sides of the answer / Do it: every door**

Do it: every door

Operation: bash — run in the operator shell, in the kit (one call at each door).

Expected shape, not a promised result:

```text
no token                              HTTP 403 - Cloud Run, before the server ran
  ui-sa, a token for rag-api's address  HTTP 401 - Cloud Run, before the server ran
  ui-sa, no email in the token          tool error - not authenticated: the bearer token carries no verified email
  the outsider, naming acme             tool error - documind-outsider-sa is not on tenant 'acme''s roster
  ui-sa, naming zeta                    answered - answerable True, 5 citations
```

**`step_02_both_sides(session)` — One call at each door, and both sides of the answer / Do it: both sides**

Do it: both sides

Operation: bash — run in the operator shell, in the kit (both sides of the answered calls).

Expected shape, not a promised result:

```text
documind-mcp, a line per answered call - who asked:
  retrieve  tenant acme   caller documind-ui-sa
  retrieve  tenant zeta   caller documind-ui-sa
documind-api, a row per retrieval it served for the MCP server - who it served:
  retrieve  tenant acme   user   documind-mcp-sa
  retrieve  tenant zeta   user   documind-mcp-sa
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_5.3_MCP_Deploy_WIX.html`. All 22 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `84a7e098461d32a587731e9d8ffc358d0dd77573`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
