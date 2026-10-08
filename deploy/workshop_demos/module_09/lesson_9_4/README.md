# Lesson 9.4: Compare actual backends and verify shutdown behavior

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_table_s_maths_read.py](demo_03_the_table_s_maths_read.py) | The table's maths, read |
| 4 | [demo_04_the_comparison_with_the_actual_backends.py](demo_04_the_comparison_with_the_actual_backends.py) | The comparison, with the actual backends |
| 5 | [demo_05_everything_off.py](demo_05_everything_off.py) | Everything off |
| 6 | [demo_06_zero_gpu_instances.py](demo_06_zero_gpu_instances.py) | Zero GPU instances |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Actual configured comparison backends and monitoring read access; shutdown does not instantly imply zero instances.

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

### demo_03_the_table_s_maths_read.py

Do it

**`step_01_the_table_s_maths_read(session)` — The table's maths, read / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the script's own check of its maths; no network).

Expected shape, not a promised result:

```text
backend            rows  groundedness  cite-precision   p95 ms  Rs/1k queries
------------------------------------------------------------------------------
documind-general      3         0.500           0.667     1200          42.00
documind-slm          3         1.000           0.500     3100        1951.33

selftest OK - groundedness excludes refusal rows, precision is per cited chunk, p95 is the 95th latency, Rs/1k is mean cost x 1000
```

**`step_02_the_table_s_maths_read(session)` — The table's maths, read / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (reads the script, the tools module and config.yaml; no network).

Expected shape, not a promised result:

```text
a row asks the gateway for a route by name: documind-general, documind-slm (make compare's default)
  its context: the citations' quotes of the API's own answer - retrieve() posts to /v1/query
  if that answer takes more than 20 s, the row's context is empty, and only the log says so
from the gateway's reply a row keeps the answer and the token counts, and reads neither the model that answered nor x-litellm-response-cost
its price is the script's own, by the route asked (USD a million tokens, in / out):
  documind-general    table  1.50 /  7.50   config.yaml  1.50 /  7.50
  documind-reasoning  table  1.50 /  7.50   config.yaml  2.00 / 12.00  <- no entry: documind-general's
  documind-slm        table 20.50 / 20.50   config.yaml 20.50 / 20.50
  documind-sensitive  table  1.50 /  7.50   config.yaml 20.50 / 20.50  <- no entry: documind-general's
  documind-inference  table  1.50 /  7.50   config.yaml  6.80 /  6.80  <- no entry: documind-general's
  documind-gke        table 20.50 / 20.50   config.yaml 20.50 / 20.50
p95 on 20 rows is sorted row 19 of 20: the slowest row never shows
```

### demo_04_the_comparison_with_the_actual_backends.py

Do it

**`step_01_the_comparison_with_the_actual_backends(session)` — The comparison, with the actual backends / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (20 questions to the API, then to three routes; the GPU wakes; about five minutes).

Expected shape, not a promised result:

```text
backend            rows  groundedness  cite-precision   p95 ms  Rs/1k queries
------------------------------------------------------------------------------
documind-general     20         1.000           1.000     1500          38.69
documind-slm         20         0.850           1.000     3100         262.77
documind-inference   20         0.850           1.000     3400          38.50

what answered each route - the gateway's reply, which the table does not keep:
  documind-general    gemini-3.6-flash            20 rows
  documind-slm        ollama_chat/documind-slm    20 rows
  documind-inference  ollama_chat/documind-slm    20 rows
the rupees for these rows, the gateway's price against the table's:
  documind-general    Rs   0.77   Rs   0.77
  documind-slm        Rs   5.26   Rs   5.26
  documind-inference  Rs   5.26   Rs   0.77
the slowest documind-slm row: 55.7 s; the p95 the table prints is row 19 of 20, 3.1 s
```

### demo_05_everything_off.py

Do it

**`step_01_everything_off(session)` — Everything off / Do it**

Do it

Operation: bash — run in the operator shell, in the kit, when the comparison is done.

Expected shape, not a promised result:

```text
...
documind-slm scaled to zero
...
documind-gateway scaled to zero
...
vLLM workload removed; the cluster and any Standard lab node remain (gke.tf) - make down removes them
documind-slm: min-instances 0
documind-vllm: min-instances absent
documind-gateway: min-instances 0
documind-ui: min-instances 0
```

### demo_06_zero_gpu_instances.py

Do it

**`step_01_zero_gpu_instances(session)` — Zero GPU instances / Do it**

Do it

Operation: bash — run in the operator shell, at least 10 minutes after make off (reads Cloud Monitoring; changes nothing).

Manual action: The next read is Cloud Monitoring at least ten minutes after make off. Stop and rerun this demo later if you like; completed comparison/shutdown steps are retained. After done, it waits only for whatever is left of the ten minutes.

IDE adaptation: The page reads Cloud Monitoring at least ten minutes after make off. Wait for whatever is left of those ten minutes after the manual pause, so an early 'done' cannot read the instance count too soon. Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
instance_count per service, 09:40 to 10:25 UTC, one point a minute (Cloud Monitoring):
  documind-slm      last instance at 10:13 UTC    a GPU service
  documind-vllm     no instance in the window     a GPU service
  documind-gateway  last instance at 10:09 UTC
  documind-ui       no instance in the window
GPU services with an instance in the last 3 minutes: none - zero GPU instances
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_9.4_Compare_Shutdown_WIX.html`. All 21 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `6279d8ef22f2b880414191dd9de3f5b9b4db124f`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
