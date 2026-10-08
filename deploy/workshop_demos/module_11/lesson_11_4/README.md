# Lesson 11.4: Debug a wrong answer through the complete pipeline

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_trail_as_the_kit_writes_it_down.py](demo_03_the_trail_as_the_kit_writes_it_down.py) | The trail, as the kit writes it down |
| 4 | [demo_04_a_right_answer_and_its_trail.py](demo_04_a_right_answer_and_its_trail.py) | A right answer, and its trail |
| 5 | [demo_05_break_it_a_version_reaches_the_lane.py](demo_05_break_it_a_version_reaches_the_lane.py) | Break it: a version reaches the lane |
| 6 | [demo_06_trace_it_name_the_cause_put_it_back.py](demo_06_trace_it_name_the_cause_put_it_back.py) | Trace it, name the cause, put it back |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The original HR fixture; the controlled version change is undone before completion.

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

### demo_03_the_trail_as_the_kit_writes_it_down.py

Do it

**`step_01_the_trail_as_the_kit_writes_it_down(session)` — The trail, as the kit writes it down / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the trail as the kit writes it down; no network).

Expected shape, not a promised result:

```text
the envelope on every answer, beyond the contract (schemas.py, RAGResponse):
  model, backend, cost_usd, tokens_in, tokens_out, cached_tokens, latency_ms, stages, cache_hit
stages, as query() fills them (main.py):
  generate_ms, graph_chunks, managed_chunks, policy_fallback, pool, rerank_fallback, rerank_ms, retrieval_backend, retrieve_ms, vector_chunks
found_by, the rung that put a chunk in the pool (retriever.py):
  firestore, graph, rag_engine, vector, vertex_search
GET /version, what is serving (main.py):
  model_backend, generator_model, prompt, retrieval_mode, retrieval_backend, retrieval_graph, graph_backend, embedding, retrieval_current_only, semantic_cache, git_sha
the events a degraded answer leaves in documind-api's log:
  routing_fallback         main.py:101
  retrieval_pin_ignored    main.py:140
  rag_engine_fallback      retriever.py:207
  rag_engine_fallback      retriever.py:219
  vertex_search_fallback   retriever.py:311
  vector_search_fallback   retriever.py:391
  rerank_fallback          retriever.py:512
  tier_exhausted           generator.py:304
  generation_truncated     generator.py:402
  tier_exhausted           generator.py:493
  cache_stale              cache_manager.py:119
```

### demo_04_a_right_answer_and_its_trail.py

Do it

**`step_01_a_right_answer_and_its_trail(session)` — A right answer, and its trail / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the question, the answer and its trail).

Expected shape, not a promised result:

```text
A confirmed employee at grade E3 or above serves a notice period of 60 days [1].
  [1] hr_policy_2026.md  version 497809ffbaa6  chunk 1  'serves a notice period of 60 days'
  cache_hit none | backend vertex | answerable True
  store vector | vector_chunks 20 | pool 20 | rerank_fallback 0 | policy_fallback 0
  kept in ~/ask131-before.json
```

### demo_05_break_it_a_version_reaches_the_lane.py

Do it

**`step_01_break_it_a_version_reaches_the_lane(session)` — Break it: a version reaches the lane / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (revision 2 re-issued, then the same question).

Expected shape, not a promised result:

```text
>> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)
>> event doc_key chunks reused embedded retired effective_from
>> ingest_reactivated	acme_5560308823a62dc8...	283	283	0	283
>> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_2026.md API=<candidate url>
From 1 October 2026, a confirmed employee at grade E3 or above serves a notice period of 90 days [1].
  [1] hr_policy_2026.md  version 5560308823a6  chunk 1  'serves a notice period of 90 days'
  cache_hit none | backend vertex | answerable True
  store vector | vector_chunks 20 | pool 20 | rerank_fallback 0 | policy_fallback 0
  kept in ~/ask131-after.json
```

### demo_06_trace_it_name_the_cause_put_it_back.py

Do it: the trace Do it: the versions view and the two probes Do it: put version 1 back

**`step_01_the_trace(session)` — Trace it, name the cause, put it back / Do it: the trace**

Do it: the trace

Operation: bash — run in the operator shell, in the kit (the trace: reads only).

Expected shape, not a promised result:

```text
serving: COMMIT, gemini-3.6-flash via vertex, prompt documind-rag@v3, text-embedding-005@1, current-only off, answer cache off
events since the break: none
the trail of ~/ask131-after.json, in the order the answer was made:
  1 the answer cache         clean  cache_hit none: retrieval ran
  2 the store and its rungs  clean  vector: 20 of the pool's 20 from its own index; no fallback event
  3 the pool                 clean  20 of the 20 the ablation decided
  4 the reranker             clean  the Ranking API ordered the pool
  5 the version              OFF    acme/hr_policy_2026.md: the ledger's current since 2026-09-23T10:41 is 5560308823a6, not the golden set's 497809ffbaa6; it declares effective_from 2026-10-01
  6 the model                clean  answered from 1 citation; groundedness is make judge's
CAUSE: a version (link 5) - every link before it is clean
```

**`step_02_the_versions_view_and_the_two_probes(session)` — Trace it, name the cause, put it back / Do it: the versions view and the two probes**

Do it: the versions view and the two probes

Operation: bash — run in the operator shell, in $DEMO_ROOT (the versions view and the two probes; reads only).

Expected shape, not a promised result:

```text
source                                       status                  gen chunks reused embed retired effective  embedding              indexed_at
acme/hr_policy_2026.md                       indexed    1758624067215604    283    283     0     283 -          text-embedding-005@1   2026-09-23T10:41:07
Project: documind-ai-YOUR-ID (NUMBER)
Terraform index: projects/documind-ai-YOUR-ID/locations/asia-south1/indexes/1234567890123456789
Terraform endpoint: projects/documind-ai-YOUR-ID/locations/asia-south1/indexEndpoints/9876543210987654321
API index: projects/NUMBER/locations/asia-south1/indexes/1234567890123456789
API endpoint: projects/NUMBER/locations/asia-south1/indexEndpoints/9876543210987654321
Index dimensions: 768; update method: STREAM_UPDATE
Global vector count: 1745
Deployment: documind_chunks_v1
Deployment sync time: 2026-09-23T10:42:18.000Z
PASS: the expected index is attached to the expected endpoint.
This verifies attachment and configuration; ingestion and query checks are separate.
{"project": "documind-ai-YOUR-ID", "collection": "chunks", "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md", "source_status": "indexed", "source_doc_key": "acme_5560308823a62dc812a39ca44b777bd73ccd12146b02f1f9506a3d15ed208c71"}
STOP: HR source ledger does not match the selected local HR file; review the source version.
```

**`step_03_put_version_1_back(session)` — Trace it, name the cause, put it back / Do it: put version 1 back**

Do it: put version 1 back

Operation: bash — run in the operator shell, in the kit (version 1 back, the question again, the probe again).

Expected shape, not a promised result:

```text
>> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)
>> event doc_key chunks reused embedded retired effective_from
>> ingest_reactivated	acme_497809ffbaa603c4...	283	283	0	283
>> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_2026.md API=<candidate url>
A confirmed employee at grade E3 or above serves a notice period of 60 days [1].
  [1] hr_policy_2026.md  version 497809ffbaa6  chunk 1  'serves a notice period of 60 days'
  cache_hit none | backend vertex | answerable True
  store vector | vector_chunks 20 | pool 20 | rerank_fallback 0 | policy_fallback 0
  kept in ~/ask131-restored.json
PASS: both Firestore filter modes verified. Evidence: operator-evidence/firestore-combined-filters.json
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_11.4_Debug_Wrong_Answer_WIX.html`. All 21 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `7449ad397b6297eacbbdc4e2f9efd8e24b0f6a5d`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
