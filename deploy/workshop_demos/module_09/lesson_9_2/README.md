# Lesson 9.2: Serve a supplied or stock model using Ollama

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_a_modelfile_from_the_tokenizer.py](demo_03_a_modelfile_from_the_tokenizer.py) | A Modelfile from the tokenizer |
| 4 | [demo_04_the_waits_and_the_bill_from_the_kit.py](demo_04_the_waits_and_the_bill_from_the_kit.py) | The waits and the bill, from the kit |
| 5 | [demo_05_the_stand_in_deployed_and_smoke_tested.py](demo_05_the_stand_in_deployed_and_smoke_tested.py) | The stand-in, deployed and smoke-tested |
| 6 | [demo_06_the_cold_start_timed.py](demo_06_the_cold_start_timed.py) | The cold start, timed |
| 7 | [demo_07_the_small_model_behind_the_gateway_and_the_api.py](demo_07_the_small_model_behind_the_gateway_and_the_api.py) | The small model behind the gateway and the API |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The supplied model/tokenizer when using that path, or the page's stock-model alternative; GPU deployment is billed.

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

### demo_03_a_modelfile_from_the_tokenizer.py

Do it

**`step_01_a_modelfile_from_the_tokenizer(session)` — A Modelfile from the tokenizer / Do it**

Do it

Operation: bash — run in the operator shell (once: a venv with a transformers that can read the tokenizer).

**`step_02_a_modelfile_from_the_tokenizer(session)` — A Modelfile from the tokenizer / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (downloads the tokenizer's files, about 31 MB; no GPU, no Google Cloud).

Expected shape, not a promised result:

```text
[transformers] PyTorch was not found. Models won't be available and only tokenizers, configuration and file/data utilities can be used.
# GENERATED by make_modelfile.py from the tokenizer. Do not hand-edit.
# Regenerate whenever the checkpoint changes - the template belongs to the
# weights, not to the project.

FROM ./documind-slm.gguf

TEMPLATE """<bos><|turn>user
{{ .Prompt }}<turn|>
<|turn>model
"""

PARAMETER stop "<turn|>"

PARAMETER num_ctx 4096
```

### demo_04_the_waits_and_the_bill_from_the_kit.py

Do it

**`step_01_the_waits_and_the_bill_from_the_kit(session)` — The waits and the bill, from the kit / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (reads the kit's files; no network).

Expected shape, not a promised result:

```text
the SLM: 1 nvidia-l4, 8 vCPU, 32Gi; 0 to 1 instance; 4 requests at a time; 600 s a request
its startup probe: /api/tags after 10 s, every 5 s, 30 failures allowed: 160 s for Ollama to list the model
make smoke-slm waits 240 s a call
a gate row: run_eval waits 90 s for the API, and asks once more two seconds after a timeout
the API waits 90 s for the gateway (GATEWAY_TIMEOUT_S)
the gateway waits 110 s for documind-slm, then falls back to documind-general
the gateway waits 110 s for documind-sensitive, then stops: it has no fallback
the bill, by the instance: (0.0001867 + 8 x 0.000018 + 32 x 0.000002) USD a second = 1.4209 USD an hour = Rs 120.78
  up to 10 idle minutes after the last request: Rs 20.13; min-instances 1 for a 720-hour month: Rs 86,960
  the kit's own figure: Rs 86,904/month, at $1.42 an hour
```

### demo_05_the_stand_in_deployed_and_smoke_tested.py

Do it

**`step_01_the_stand_in_deployed_and_smoke_tested(session)` — The stand-in, deployed and smoke-tested / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (a GPU service: it bills while an instance lives).

Expected shape, not a promised result:

```text
>> stand-in: gemma3:4b will be served as documind-slm
gcloud run deploy documind-slm \
  --source services/slm --region us-central1 --project documind-ai-YOUR-ID \
  --gpu 1 --gpu-type nvidia-l4 --no-gpu-zonal-redundancy \
  --cpu 8 --memory 32Gi \
  --max-instances 1 --min-instances 0 --timeout 600 --concurrency 4 \
  --no-allow-unauthenticated --labels slm-source=stock \
  --startup-probe httpGet.path=/api/tags,httpGet.port=8080,initialDelaySeconds=10,periodSeconds=5,failureThreshold=30 --quiet
...
>> slm: https://documind-slm-NUMBER.us-central1.run.app (min-instances 0; make slm-off after every session anyway)
```

**`step_02_the_stand_in_deployed_and_smoke_tested(session)` — The stand-in, deployed and smoke-tested / Do it**

Do it

Operation: bash — run in the operator shell, in the kit, right after the deploy.

Expected shape, not a promised result:

```text
DocuMind SLM - live smoke test
  target: https://documind-slm-NUMBER.us-central1.run.app
  --------------------------------------------------------
  [PASS] /api/tags lists documind-slm  HTTP 200 in 0.1s (cold start included): ['documind-slm:latest']
  [PASS] /api/generate answers  'OK' in 12.0s
  [PASS] /v1/chat/completions answers (the OpenAI-compatible door)  'OK' in 0.6s
  [PASS] through the gateway's documind-slm route  HTTP 200, served by 'ollama_chat/documind-slm' in 0.6s
  [PASS] what the service serves  stock	us-central1-docker.pkg.dev/documind-ai-YOUR-ID/cloud-run-source-deploy/documind-slm@sha256:DIGEST
  --------------------------------------------------------
  5 passed, 0 failed
```

### demo_06_the_cold_start_timed.py

Do it

**`step_01_the_cold_start_timed(session)` — The cold start, timed / Do it**

Do it

Operation: bash — run in the operator shell, after documind-slm has been idle for more than 10 minutes.

Expected shape, not a promised result:

```text
/api/tags              41.4 s   documind-slm:latest (4.3B, Q4_K_M)
/api/generate, first   12.0 s   'OK'
/api/generate, again    0.6 s   'OK'
a cold start: 53.4 s to the first answer - 41.4 s for an instance, then 11.4 s to load the model into the GPU
```

### demo_07_the_small_model_behind_the_gateway_and_the_api.py

Do it

**`step_01_the_small_model_behind_the_gateway_and_the(session)` — The small model behind the gateway and the API / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (lesson 9.1's three requests, through the gateway).

Expected shape, not a promised result:

```text
USD a million tokens, in and out (config.yaml): documind-general 1.50 and 7.50, documind-sensitive 20.50 and 20.50
  no personal data  HTTP 200  answered by gemini-3.6-flash; 11 tokens in, 1 out; x-litellm-response-cost 2.4e-05
  a bare PAN        HTTP 200  answered by gemini-3.6-flash; 16 tokens in, 1 out; x-litellm-response-cost 3.15e-05
  a PAN and a date  HTTP 200  answered by ollama_chat/documind-slm; 19 tokens in, 30 out; x-litellm-response-cost 0.0010045
                    Your notice period depends on your grade and confirmation status; the documents you shared do not say which applies to you.
```

**`step_02_the_small_model_behind_the_gateway_and_the(session)` — The small model behind the gateway and the API / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (a no-traffic revision; the live one keeps its settings).

Expected shape, not a promised result:

```text
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \
  --update-env-vars "^|^GENERATOR_MODEL=documind-slm|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|MODEL_BACKEND=gateway|ARMOR=off|SEMANTIC_CACHE=off|RETRIEVAL_CURRENT_ONLY=off|RETRIEVAL_GRAPH=off|GRAPH_BACKEND=firestore|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
...
>> candidate revision: documind-api-000NN-xxx (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app
```

**`step_03_the_small_model_behind_the_gateway_and_the(session)` — The small model behind the gateway and the API / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (one golden question through the candidate).

Expected shape, not a promised result:

```text
lk-06: What is the notice period for a confirmed E3?
answer: A confirmed E3 serves a notice period of 60 days [1].
  cites acme:lk-06#0
model documind-slm, backend gateway: the route the API asked for, whoever answered
cost 0.03977 USD for 1900 tokens in and 40 out: documind-slm's rate, so the small model answered
```

**`step_04_the_small_model_behind_the_gateway_and_the(session)` — The small model behind the gateway and the API / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the gate, scoped to the HR policy's rows).

Expected shape, not a promised result:

```text
>> https://candidate---documind-api-NUMBER.asia-south1.run.app
== eval gate: LIVE ==
  scoped to hr_policy_2026.md: 10 row(s) cite it
  10 rows (10 answerable, 0 not) against https://candidate---documind-api-NUMBER.asia-south1.run.app

  [PASS] request_success_rate  100.0%  (threshold 100%; 10 rows)
  [PASS] answerable_rate        90.0%  (threshold 80%; 10 rows)
  [PASS] citation_rate         100.0%  (threshold 95%; 9 rows)
  [PASS] citation_valid_rate   100.0%  (threshold 100%; 9 rows)
  [PASS] must_contain_rate      88.9%  (threshold 85%; 9 rows)
  [PASS] correct_rate           80.0%  (threshold 68%; 10 rows)
  [ -- ] refusal_rate            0.0%  (threshold 90%; no rows in scope; 0 rows)
  [ -- ] media_kind_rate         0.0%  (threshold 80%; no rows in scope; 0 rows)
  [ -- ] isolation_403_rate      0.0%  (threshold 100%; no rows in scope; 0 rows)
  [info] quote_support_rate      ...  (quoted words found in the tenant's corpus text; not a threshold - a Doc AI extraction and a pypdf mirror hyphenate differently)

  shape        rows   ok   pass
  lookup          9    9      7
  version         1    1      1
  latency ms  p50   ...  p95   ...   (round trip, 10 rows)
  retrieve_ms p50   ...  p95   ...
  rerank_ms   p50   ...  p95   ...
  generate_ms p50   ...  p95   ...
  pool        avg   ...   semantic cache hits 0

  rows that cost a point (2):
    lk-02  lookup    acme    answered without ['15 June'] | 'form 16 is issued every june [1].'
    lk-08  lookup    acme    REFUSED conf=low cites=0 | Who approves a purchase of Rs 3,00,000?

  report: /home/YOU/slm182.json
  All thresholds met.
```

**`step_05_the_small_model_behind_the_gateway_and_the(session)` — The small model behind the gateway and the API / Do it**

Do it

Operation: bash — run in the operator shell (reads the gate's report).

Expected shape, not a promised result:

```text
lk-06: pass, 1 citation(s); the route it asked for: documind-slm, through the gateway
8 of 10 rows passed; all thresholds met
```

**`step_06_the_small_model_behind_the_gateway_and_the(session)` — The small model behind the gateway and the API / Do it**

Do it

Operation: bash — run in the operator shell, in the kit, when you are done.

Expected shape, not a promised result:

```text
...
gcloud run services update documind-slm --region us-central1 --project documind-ai-YOUR-ID --min-instances 0 --quiet
...
documind-slm scaled to zero
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_9.2_Ollama_SLM_WIX.html`. All 36 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `ef4d07a96774afec01f7a333d643d470b90ee1c3`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
