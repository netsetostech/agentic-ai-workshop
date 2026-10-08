# Lesson 12.2: Validate sanitized datasets and run managed tuning

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_checks_that_run_before_the_spend.py](demo_03_the_checks_that_run_before_the_spend.py) | The checks that run before the spend |
| 4 | [demo_04_the_frozen_file_validated.py](demo_04_the_frozen_file_validated.py) | The frozen file, validated |
| 5 | [demo_05_the_job_submitted.py](demo_05_the_job_submitted.py) | The job, submitted |
| 6 | [demo_06_the_endpoint_and_where_it_answers.py](demo_06_the_endpoint_and_where_it_answers.py) | The endpoint, and where it answers |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The reviewed sanitized datasets from 12.1. Submission creates a billed tuning job; resume polling the saved job instead of resubmitting. The optional v3 job (step 7) needs 12.1's v3 and is a second billed job.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Optional extensions

- [optional/demo_07_optional_v3_validated_and_tuned_with_its_validation_file.py](optional/demo_07_optional_v3_validated_and_tuned_with_its_validation_file.py) — Do it Then submit the job with a name that says v3 and the validation file, and return at once: Then submit the job with a name that says v3 and the validation file, and return at once: Then wait for it. The poll only reads, so after a disconnect it is safe to run again:

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

### demo_03_the_checks_that_run_before_the_spend.py

Do it

**`step_01_the_checks_that_run_before_the_spend(session)` — The checks that run before the spend / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the two self-tests and the rules; no network).

Expected shape, not a promised result:

```text
selftest: the evidence rule dropped jn-06's chunk and kept EMEA elsewhere and lk-09's 8, the question rule dropped lk-06's twin, the PAN row dropped, two formats agree, ModelDraft parses, the batch round trip holds
selftest: the helpdesk rows mark the source they cite, carry the served prompt with SYSTEM once, drop a quote not in its chunk, keep Hinglish twins and refusals, and a PAN in a distractor drops its row
selftest: an untunable base and a rank the SDK cannot spell are refused before submission; adapter 4 is ADAPTER_SIZE_FOUR and the SDK accepts it
gemini-3.6-flash, adapter 4: refused before submission: managed SFT accepts ['gemini-3.1-flash-lite', 'gemini-3.5-flash'] as of 2026-09-04
gemini-3.1-flash-lite, adapter 3: refused before submission: the LoRA rank must be one of [1, 2, 4, 8, 16, 32]
gemini-3.1-flash-lite, adapter 32: accepted, ADAPTER_SIZE_THIRTY_TWO
make tune's defaults: {'epoch_count': 3, 'adapter_size': 'ADAPTER_SIZE_FOUR', 'tuned_model_display_name': 'documind-sft-v1'}
an endpoint whose path says us is called at: us; with GENERATOR_LOCATION=us-central1: us-central1
```

### demo_04_the_frozen_file_validated.py

Do it

**`step_01_the_frozen_file_validated(session)` — The frozen file, validated / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (reads the bucket and Firestore; one DLP scan in asia-south1).

Expected shape, not a promised result:

```text
the file make tune VERSION=v2 reads: gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_v2.vertex.jsonl
  vertex sha256 as the manifest says
  chat   sha256 as the manifest says
1. the shape: 315 of 315 rows are a system instruction, a user turn and a model turn, text only; the chat file says the same in 315; targets that parse as ModelDraft: 315
2. the test set: the golden set (65 rows) would drop 0 of 315
3. personal data, by the kit's own scan (DLP in asia-south1, LIKELY or above; findings, never the values):
   in the questions and answers, which make trainset scans: 0 rows
   in the chunks the user turns carry, which it does not: 1 row
     acme:cgst_act_2017#p1-0: EMAIL_ADDRESS
4. residency: the rows are acme's, whose data_region is any; may they be held in us-central1? True
5. the size: about 203,451 tokens an epoch by the kit's estimate (characters / 4); the longest row about 863 of the 131,072 Google allows
   3 epochs: about 610,353 training tokens, about Rs 156 at USD 3.00 a million
verdict: ready to tune: the manifest's bytes, the trainer's shape, no golden row, nothing where make trainset looks, and acme may leave India
         1 row carries a finding make trainset never looked for: read the chunks before you pay
```

### demo_05_the_job_submitted.py

Do it

**`step_01_the_job_submitted(session)` — The job, submitted / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (submits the job and returns: the billed act).

Expected shape, not a promised result:

```text
python evals/tune.py --project documind-ai-YOUR-ID --dataset gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_${VERSION:-v1}.vertex.jsonl \
  --base gemini-3.1-flash-lite --epochs 3 --adapter 4 --display-name documind-sft-v2 --no-wait
  submitted projects/NUMBER/locations/us-central1/tuningJobs/7240862654976436473 on gemini-3.1-flash-lite: 3 epochs, adapter 4, dataset gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_v2.vertex.jsonl
  poll later: python evals/tune.py --project documind-ai-YOUR-ID --poll projects/NUMBER/locations/us-central1/tuningJobs/7240862654976436473
JOB=projects/NUMBER/locations/us-central1/tuningJobs/7240862654976436473
```

### demo_06_the_endpoint_and_where_it_answers.py

The first cell polls the job once a minute until it ends. The poll only reads, so it costs nothing, and after a disconnect it is safe to run again: it takes the job from step 5's log. When the job succeeds, tune.py prints: The cell keeps the endpoint in ~/poll172.log and in ENDPOINT. The cell keeps the endpoint in ~/poll172.log and in ENDPOINT. The second cell asks the endpoint one question the way the generator would. It sends SYSTEM, one source under its header and the question, with generator._call's settings: ModelDraft's schema, 2,048 tokens and thinking at LOW. The chunk is not one the rows were written from, and the question is not a golden one. The cell asks in three places: us-central1, the job's region; global, where the served model answers; and the location the generator would use, from the path.

**`step_01_definition(session)` — The endpoint, and where it answers / Definition**

The first cell polls the job once a minute until it ends. The poll only reads, so it costs nothing, and after a disconnect it is safe to run again: it takes the job from step 5's log. When the job succeeds, tune.py prints: The cell keeps the endpoint in ~/poll172.log and in ENDPOINT.

Operation: bash — run in the operator shell, in the kit (waits for the job, a line a minute).

Expected shape, not a promised result:

```text
09:53:00 JobState.JOB_STATE_PENDING
  09:54:00 JobState.JOB_STATE_PENDING
  09:55:00 JobState.JOB_STATE_RUNNING
  ...      (a line a minute while the job runs: 33 more here)
  10:29:00 JobState.JOB_STATE_RUNNING
  JOB_STATE_SUCCEEDED
  tuned model : projects/NUMBER/locations/us/models/6156234374247085944@1
  endpoint    : projects/NUMBER/locations/us/endpoints/9136961803583303949

  serve it as a candidate revision, no traffic, and judge it:
    make candidate PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=projects/NUMBER/locations/us/endpoints/9136961803583303949 RAG_MODEL_BASE=gemini-3.1-flash-lite
    make eval-live PROJECT=documind-ai-YOUR-ID API=<the candidate url>
    make judge PROJECT=documind-ai-YOUR-ID API_B=<the candidate url>
ENDPOINT=projects/NUMBER/locations/us/endpoints/9136961803583303949
```

**`step_02_definition(session)` — The endpoint, and where it answers / Definition**

The cell keeps the endpoint in ~/poll172.log and in ENDPOINT. The second cell asks the endpoint one question the way the generator would. It sends SYSTEM, one source under its header and the question, with generator._call's settings: ModelDraft's schema, 2,048 tokens and thinking at LOW. The chunk is not one the rows were written from, and the question is not a golden one. The cell asks in three places: us-central1, the job's region; global, where the served model answers; and the location the generator would use, from the path.

Operation: bash — run in the operator shell, in the kit (one answer from the endpoint, and two calls that are not found).

Expected shape, not a promised result:

```text
the endpoint's path says us; the generator would call it at us
  us-central1  404 NOT_FOUND
  global       404 NOT_FOUND
  us           answered: 429 tokens in, 97 out; a ModelDraft, answerable True, 1 citation(s), 0 [N] marks in the answer
  the answer: No. A loss of wages from withholding an increment for a good and sufficient cause is not deemed a deduction from wages, where the employer's provisions meet the requirements the appropriate Government notifies.
  the price: Rs 0.0322 as Google bills a tuned Gemini 3 endpoint (1.5 x flash-lite); cost.py would log Rs 0.0215
```

### optional/demo_07_optional_v3_validated_and_tuned_with_its_validation_file.py

Do it Then submit the job with a name that says v3 and the validation file, and return at once: Then submit the job with a name that says v3 and the validation file, and return at once: Then wait for it. The poll only reads, so after a disconnect it is safe to run again:

**`step_01_optional_v3_validated_and_tuned_with_its_v(session)` — Optional: v3, validated and tuned with its validation file / Do it**

Do it

Operation: bash — optional: run in the operator shell, in the kit (reads the bucket and Firestore; DLP over every prompt).

Expected shape, not a promised result:

```text
the files make tune VERSION=v3 reads: documind_sft_v3.vertex.jsonl, and with --validation documind_sft_v3.validation.vertex.jsonl
  vertex     sha256 as the manifest says
  chat       sha256 as the manifest says
  validation sha256 as the manifest says
  rows       sha256 as the manifest says
1. the shape: 435 of 435 rows are one user turn that is the served prompt and one model turn, text only; the chat file says the same in 395 of 395; targets that parse as ModelDraft: 435
2. the test set: the golden set would drop 0 of 435 rows; 0 of the 598 chunks in the prompts are a golden row's evidence
3. personal data: DLP over every prompt and every answer, so over every chunk: 0 with a finding
4. residency: the rows are acme's, whose data_region is any; may they be held in us-central1? True
5. the size: about 551,632 tokens an epoch, the longest row about 1,805 of the 131,072 Google allows; the validation file about 57,521, scored and never trained on
   3 epochs: about 1,654,896 training tokens, about Rs 422 at USD 3.00 a million
verdict: ready to tune: the manifest's bytes, the served shape, no golden row or evidence in any prompt, no finding in any chunk, and acme may leave India
```

**`step_02_optional_v3_validated_and_tuned_with_its_v(session)` — Optional: v3, validated and tuned with its validation file / Do it**

Then submit the job with a name that says v3 and the validation file, and return at once:

Operation: bash — optional: run in the operator shell, in the kit (submits the v3 job and returns: a second billed act).

Expected shape, not a promised result:

```text
python evals/tune.py --project documind-ai-YOUR-ID --dataset gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_${VERSION:-v1}.vertex.jsonl \
  --base gemini-3.1-flash-lite --epochs 3 --adapter 4 --display-name documind-sft-v3 --validation gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_v3.validation.vertex.jsonl --no-wait
  submitted projects/NUMBER/locations/us-central1/tuningJobs/4763636347812545555 on gemini-3.1-flash-lite: 3 epochs, adapter 4, dataset gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_v3.vertex.jsonl
  poll later: python evals/tune.py --project documind-ai-YOUR-ID --poll projects/NUMBER/locations/us-central1/tuningJobs/4763636347812545555
JOB_V3=projects/NUMBER/locations/us-central1/tuningJobs/4763636347812545555
```

**`step_03_optional_v3_validated_and_tuned_with_its_v(session)` — Optional: v3, validated and tuned with its validation file / Do it**

Then submit the job with a name that says v3 and the validation file, and return at once: Then wait for it. The poll only reads, so after a disconnect it is safe to run again:

Operation: bash — optional: run in the operator shell, in the kit (waits for the v3 job, a line a minute).

Expected shape, not a promised result:

```text
10:03:00 JobState.JOB_STATE_PENDING
  10:04:00 JobState.JOB_STATE_PENDING
  10:05:00 JobState.JOB_STATE_RUNNING
  ...      (a line a minute while the job runs: 33 more here)
  10:39:00 JobState.JOB_STATE_RUNNING
  JOB_STATE_SUCCEEDED
  tuned model : projects/NUMBER/locations/us/models/8366872049017976783@1
  endpoint    : projects/NUMBER/locations/us/endpoints/3784707595493887459

  serve it as a candidate revision, no traffic, and judge it:
    make candidate PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=projects/NUMBER/locations/us/endpoints/3784707595493887459 RAG_MODEL_BASE=gemini-3.1-flash-lite
    make eval-live PROJECT=documind-ai-YOUR-ID API=<the candidate url>
    make judge PROJECT=documind-ai-YOUR-ID API_B=<the candidate url>
ENDPOINT_V3=projects/NUMBER/locations/us/endpoints/3784707595493887459
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_12.2_Managed_Tuning_WIX.html`. All 28 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `8d2fab91ee14935e4fdd422af3798cf76a95b6f7`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
