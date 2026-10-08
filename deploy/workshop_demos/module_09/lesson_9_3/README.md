# Lesson 9.3: Inspect the vLLM service and the GKE alternative

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_vllm_service_read.py](demo_03_the_vllm_service_read.py) | The vLLM service, read |
| 4 | [demo_04_the_manifest_read.py](demo_04_the_manifest_read.py) | The manifest, read |
| 5 | [demo_05_the_lane_s_cluster_inspected.py](demo_05_the_lane_s_cluster_inspected.py) | The lane's cluster, inspected |
| 6 | [demo_06_the_duty_cycle_sum.py](demo_06_the_duty_cycle_sum.py) | The duty-cycle sum |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Read the vLLM/GKE definitions even if the optional GKE cluster has not been deployed; absence is not a serving comparison.

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

### demo_03_the_vllm_service_read.py

Do it

**`step_01_the_vllm_service_read(session)` — The vLLM service, read / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (reads the service's files; no network).

Expected shape, not a promised result:

```text
the image: FROM vllm/vllm-openai:v0.28.0, then python -m uvicorn main:app --host 0.0.0.0 --port 8080 --workers 1 --timeout-keep-alive 120
  weights in the image: none - no step fetches them, and the HF_TOKEN build-arg cloudbuild.yaml passes has no ARG to land in
  so the engine downloads google/gemma-3-4b-it when it starts, from Hugging Face
  the environment make deploy-vllm gives it: GOOGLE_CLOUD_PROJECT - no Hugging Face token
the service: 1 nvidia-l4, 8 vCPU, 32Gi; 0 to 1 instance; 32 requests at a time; startup probe 120 s + 5 x 30 s = 270 s
its door: every chat completion needs an X-API-Key header, hashed and looked up in Firestore (api_keys then tenants)
  what the gateway's token proxy sends: its own ID token as Authorization, and no X-API-Key
  code elsewhere in the kit that writes an api_keys document: none
  roles Terraform grants documind-vllm-sa, the account it runs as: none
its request log: BigQuery table 'project.dataset.inference_logs'
the gateway's route to it: documind-inference, http://127.0.0.1:8090/vllm/v1, falling back to documind-slm, documind-general
```

### demo_04_the_manifest_read.py

Do it

**`step_01_the_manifest_read(session)` — The manifest, read / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (reads the manifest and the image it runs; no network).

Expected shape, not a promised result:

```text
Deployment documind-vllm: 1 replica, and no autoscaler
  its node: nodeSelector cloud.google.com/gke-accelerator=nvidia-l4, so Autopilot provisions an L4 node for the pod
  image: ${IMAGE}, which make gke-up fills in: asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/gemma-vllm:latest
  limits: 1 GPU, 6 vCPU, 24Gi (requests default to the limits)
  env: HF_HUB_OFFLINE=1
  startup probe: GET /health every 10 s, 60 failures allowed: 600 s to load
  args: --model=google/gemma-3-4b-it --dtype=bfloat16 --gpu-memory-utilization=0.90 --max-model-len=4096 --port=8080
Service documind-vllm: ClusterIP (no type named, so the default), port 80 to 8080: no address outside the cluster
the image it runs: ENTRYPOINT [], CMD python -m uvicorn main:app --host 0.0.0.0 --port 8080 --workers 1 --timeout-keep-alive 120
  the manifest sets args and no command, and the ENTRYPOINT is empty: the container runs '--model=google/gemma-3-4b-it' as its program
  main.py takes its model from the environment (MODEL_NAME), and reads none of those args
  the image holds no weights (step 3), and HF_HUB_OFFLINE=1 forbids the download
verdict: as written, this pod cannot start
```

### demo_05_the_lane_s_cluster_inspected.py

Do it

**`step_01_the_lane_s_cluster_inspected(session)` — The lane's cluster, inspected / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (read-only: describes the lane's cluster, looks for the vLLM service and image).

Expected shape, not a promised result:

```text
documind-autopilot: STANDARD, a regional control plane in asia-south1, on documind-vpc, RUNNING
  node pool documind-lab: 1 x e2-standard-2 in asia-south1-a, 30 GB pd-standard, GPU: none
  what it bills while it exists: $0.10 an hour for the control plane (the free tier covers only zonal and Autopilot clusters) + $0.0805 for the node = $0.1805 an hour, Rs 15.34; Rs 11,199 for a 730-hour month, plus the disk
documind-vllm on Cloud Run (us-central1): not deployed
the gemma-vllm image in asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind: not built
```

**`step_02_the_lane_s_cluster_inspected(session)` — The lane's cluster, inspected / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (it stops before changing anything on a Standard lab).

IDE adaptation: The page runs make gke-up to watch its guard stop on the Standard CPU lab (exit 2 with STOP). Accept that stop as the observation, and exit 0 where the lab is Autopilot; any other exit is still an error.

Expected shape, not a promised result:

```text
STOP: the Standard CPU lab cannot run the L4 GPU lesson. Set gke_autopilot=true in Terraform, review cluster replacement and quota, and apply before make gke-up.
make: *** [Makefile:711: gke-up] Error 1
```

### demo_06_the_duty_cycle_sum.py

Do it

**`step_01_the_duty_cycle_sum(session)` — The duty-cycle sum / Do it**

Do it

Operation: bash — run in the operator shell (arithmetic only; no network).

Expected shape, not a promised result:

```text
your pattern: 8 bursts a day of 30 minutes, on 22 days a month
Cloud Run, on demand: each burst, then up to 10 idle minutes - an instance lives 320 minutes a day
  the duty-cycle sum: 320 min x 22 days = 117.3 hours of 730 (16.1%) x $1.4209 = $166.72, Rs 14,171 a month
GKE Autopilot, always on, for all 730 hours:
  us-central1  $0.9558 an hour (node 0.8536 + L4 0.0670 + 8 vCPU 0.0240 + 32 GiB 0.0112): Rs 59,309; with the $0.10 cluster fee, Rs 65,514
               cheaper than Cloud Run above 67.3% of the month (74.3% with the fee)
  asia-south1  $1.0113 an hour (node 0.8886 + L4 0.0805 + 8 vCPU 0.0288 + 32 GiB 0.0134): Rs 62,753; with the $0.10 cluster fee, Rs 68,958
               cheaper than Cloud Run above 71.2% of the month (78.2% with the fee)
at 16.1%: Cloud Run is cheaper - Rs 14,171 against Rs 59,309 for the cheapest GKE line
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_9.3_VLLM_GKE_WIX.html`. All 23 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `383d76df919ed8e9e3c09d023f05584889c7ce6d`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
