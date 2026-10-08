# Lesson 11.6: Exercise model routing, budgets and shutdown controls

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_controls_as_the_kit_writes_them_down.py](demo_03_the_controls_as_the_kit_writes_them_down.py) | The controls, as the kit writes them down |
| 4 | [demo_04_the_month_so_far.py](demo_04_the_month_so_far.py) | The month so far |
| 5 | [demo_05_the_tier_at_85_percent.py](demo_05_the_tier_at_85_percent.py) | The tier at 85 percent |
| 6 | [demo_06_off_at_night_and_the_ceiling_under_it.py](demo_06_off_at_night_and_the_ceiling_under_it.py) | Off at night, and the ceiling under it |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

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

### demo_03_the_controls_as_the_kit_writes_them_down.py

Do it

**`step_01_the_controls_as_the_kit_writes_them_down(session)` — The controls, as the kit writes them down / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the controls as the kit writes them down; no network).

Expected shape, not a promised result:

```text
per answer: ROUTING=off on the lane (lesson-12.2.sh). With it on, gemini-3.1-flash-lite labels each question SIMPLE, MEDIUM, COMPLEX, and breakers.choose_model() picks the model:
  spend   SIMPLE                  MEDIUM                  COMPLEX
  0%      gemini-3.1-flash-lite   gemini-3.6-flash        gemini-3.1-pro-preview
  79.9%   gemini-3.1-flash-lite   gemini-3.6-flash        gemini-3.1-pro-preview
  80%     gemini-3.1-flash-lite   gemini-3.1-flash-lite   gemini-3.6-flash
  85%     gemini-3.1-flash-lite   gemini-3.1-flash-lite   gemini-3.6-flash
  100%    gemini-3.1-flash-lite   gemini-3.1-flash-lite   gemini-3.6-flash
  120%    gemini-3.1-flash-lite   gemini-3.1-flash-lite   gemini-3.6-flash
  the spend: Firestore budget/<month, UTC>, USD added by every answer, over BUDGET_USD (100 on the lane); SPEND_PCT replaces it
  BUDGET_FLOOR_PCT = 100 (the comment's min-instances 0): read by nothing
per month: DocuMind monthly budget, BUDGET_AMOUNT 5000 in the billing account's currency; it emails at 50%, 80%, 100% and at a 120% forecast
per hour: documind-off runs 0 23 * * * Asia/Kolkata and floors documind-slm, documind-vllm, documind-gateway, documind-ui to min-instances 0; make off does the same by hand
  make gpu-cap: the GPU quota in us-central1 capped at 1; alerts.tf's gpu_left_warm pages when one stays up two hours
```

### demo_04_the_month_so_far.py

Do it

**`step_01_the_month_so_far(session)` — The month so far / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (reads only).

Expected shape, not a promised result:

```text
documind-api: ROUTING=off, BUDGET_USD=100, SPEND_PCT=unset
the counter, budget/2026-09: USD 7.8412 of 100 = 7.84% - the breaker would read 'normal'
the billing budget: 5000 INR a month on the whole project; emails at 50%, 80%, 100%, 120% forecast
python services/slm/gpu_quota.py --project documind-ai-YOUR-ID --region us-central1

Total NVIDIA L4 GPU allocation without zonal redundancy
  run.googleapis.com/nvidia_l4_gpu_allocation_no_zonal_redundancy
  1/{project}/{region}         us-central1  effective 3 (default 3)
```

### demo_05_the_tier_at_85_percent.py

Do it: routing on, the month as it is Do it: the same three at 85 percent Do it: undo the candidate

**`step_01_routing_on_the_month_as_it_is(session)` — The tier at 85 percent / Do it: routing on, the month as it is**

Do it: routing on, the month as it is

Operation: bash — run in the operator shell, in the kit (a candidate revision, no traffic, ROUTING on; three questions).

Expected shape, not a promised result:

```text
gemini-3.1-flash-lite    What is the notice period for a confirmed E3?
                           A confirmed employee at grade E3 or above serves a notice period of 60 days [1].
  gemini-3.6-flash         Explain what happens when a trip costs more than the per-trip travel cap.
                           Travel is capped at Rs 40,000 per trip [1]; a trip above the cap needs the function head's written approval before travel [1].
  gemini-3.1-pro-preview   Work out, step by step, the total reimbursed for three domestic trips costing Rs 38,000, Rs 45,000 and Rs 22,000.
                           Each trip is reimbursed up to the cap of Rs 40,000 [1]: Rs 38,000 + Rs 40,000 + Rs 22,000 = Rs 1,00,000; the Rs 5,000 above the cap ...
```

**`step_02_the_same_three_at_85_percent(session)` — The tier at 85 percent / Do it: the same three at 85 percent**

Do it: the same three at 85 percent

Operation: bash — run in the operator shell, in the kit (the same candidate at 85 percent; the same three questions).

Expected shape, not a promised result:

```text
gemini-3.1-flash-lite    What is the notice period for a confirmed E3?
                           A confirmed employee at grade E3 or above serves a notice period of 60 days [1].
  gemini-3.1-flash-lite    Explain what happens when a trip costs more than the per-trip travel cap.
                           Travel is capped at Rs 40,000 per trip [1]; a trip above the cap needs the function head's written approval before travel [1].
  gemini-3.6-flash         Work out, step by step, the total reimbursed for three domestic trips costing Rs 38,000, Rs 45,000 and Rs 22,000.
                           Each trip is reimbursed up to the cap of Rs 40,000 [1]: Rs 38,000 + Rs 40,000 + Rs 22,000 = Rs 1,00,000; the Rs 5,000 above the cap ...
```

**`step_03_undo_the_candidate(session)` — The tier at 85 percent / Do it: undo the candidate**

Do it: undo the candidate

Operation: bash — run in the operator shell, in the kit (the variables off the template, the tag dropped).

Expected shape, not a promised result:

```text
100	documind-api-00031-kez
```

### demo_06_off_at_night_and_the_ceiling_under_it.py

Do it: the floor, then the switch A floor of zero lets the service scale to zero, but an idle instance can stay up for up to fifteen minutes after its last request. The cell waits, then reads the UI's instance count from Cloud Monitoring for the last half hour, a sample a minute. make gpu-cap writes a consumer quota override on the L4 quotas in us-central1, capping them at one card. --max-instances belongs to one service. The quota belongs to the project, so a second GPU service, a GPU candidate or a typo cannot allocate a second card. Lowering a quota needs no approval; raising it again does.

**`step_01_the_floor_then_the_switch(session)` — Off at night, and the ceiling under it / Do it: the floor, then the switch**

Do it: the floor, then the switch

Operation: bash — run in the operator shell, in the kit (a floor, then the switch, then the nightly job's entry).

Expected shape, not a promised result:

```text
gcloud run services update documind-slm --region us-central1 --project documind-ai-YOUR-ID --min-instances 0 --quiet
ERROR: (gcloud.run.services.update) Service [documind-slm] could not be found.
make[1]: [Makefile:659: slm-off] Error 1 (ignored)
...
gcloud run services update documind-ui --region asia-south1 --project documind-ai-YOUR-ID --min-instances 0 --quiet
Deploying...
...
Done.
...
documind-slm: min-instances absent
documind-vllm: min-instances absent
documind-gateway: min-instances absent
documind-ui: min-instances 0
0 23 * * *	Asia/Kolkata	ENABLED	2026-09-23T17:30:03.184Z
```

**`step_02_the_instances_after_fifteen_minutes(session)` — Off at night, and the ceiling under it / Do it: the instances, after fifteen minutes**

A floor of zero lets the service scale to zero, but an idle instance can stay up for up to fifteen minutes after its last request. The cell waits, then reads the UI's instance count from Cloud Monitoring for the last half hour, a sample a minute.

Operation: bash — run in the operator shell, in the kit (after 15 minutes; reads only).

Manual action: The next read is Cloud Monitoring fifteen minutes after make off. Stop and rerun this demo later if you like; completed shutdown steps will not run again. After done, it waits only for whatever is left of the fifteen minutes.

IDE adaptation: Replace the page's sleep 900 with a wait for whatever is left of those fifteen minutes since make off completed. The manual pause before it lets you stop and come back; the pause and the sleep no longer add up to thirty minutes. Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
documind-ui, container instances (active and idle), a sample a minute, last 30 minutes:
  11:52 1  11:53 1  11:54 1  11:55 1  11:56 1  11:57 1  11:58 1  11:59 1  12:00 1  12:01 1
  12:02 1  12:03 1  12:04 1  12:05 1  12:06 1  12:07 1  12:08 1  12:09 0  12:10 0  12:11 0
  12:12 0  12:13 0  12:14 0  12:15 0  12:16 0  12:17 0  12:18 0  12:19 0  12:20 0  12:21 0
zero instances since 12:09 IST
```

**`step_03_the_ceiling(session)` — Off at night, and the ceiling under it / Do it: the ceiling**

make gpu-cap writes a consumer quota override on the L4 quotas in us-central1, capping them at one card. --max-instances belongs to one service. The quota belongs to the project, so a second GPU service, a GPU candidate or a typo cannot allocate a second card. Lowering a quota needs no approval; raising it again does.

Operation: bash — run in the operator shell, in the kit (lowers one quota; make gpu-cap-off takes it back).

Expected shape, not a promised result:

```text
python services/slm/gpu_quota.py --project documind-ai-YOUR-ID --region us-central1 --cap 1

Total NVIDIA L4 GPU allocation without zonal redundancy
  run.googleapis.com/nvidia_l4_gpu_allocation_no_zonal_redundancy
  1/{project}/{region}         us-central1  effective 3 (default 3)
                               -> capped at 1

1 override(s) written. Read back:
  Total NVIDIA L4 GPU allocation without zonal red 1/{project}/{region}       effective 1 (default 3, override 1)
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_11.6_Cost_Controls_WIX.html`. All 25 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `7d2d39676abfdd32aca8e43689880c544e1b0219`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
