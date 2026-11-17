# Lesson 8.4: System design: a self-updating documentation platform

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_ui_and_the_ledger_where_a_change_lands_on_your_lane.py](demo_03_the_ui_and_the_ledger_where_a_change_lands_on_your_lane.py) | The UI and the ledger: where a change lands on your lane |
| 4 | [demo_04_architecture_the_path_a_change_takes_station_by_station.py](demo_04_architecture_the_path_a_change_takes_station_by_station.py) | Architecture: the path a change takes, station by station |
| 5 | [demo_05_architecture_three_designs_the_kit_rejected_and_the_number_that_would_change_eac.py](demo_05_architecture_three_designs_the_kit_rejected_and_the_number_that_would_change_eac.py) | Architecture: three designs the kit rejected, and the number that would change each |
| 6 | [demo_06_failure_modes_what_pages_what_does_not_and_what_the_design_does_about_it.py](demo_06_failure_modes_what_pages_what_does_not_and_what_the_design_does_about_it.py) | Failure modes: what pages, what does not, and what the design does about it |
| 7 | [demo_07_cost_standing_still_staying_fresh_and_one_change_at_1k_100k_and_10m_documents.py](demo_07_cost_standing_still_staying_fresh_and_one_change_at_1k_100k_and_10m_documents.py) | Cost: standing still, staying fresh, and one change, at 1k, 100k and 10M documents |
| 9 | [demo_09_evals_a_change_is_a_release_and_the_check_that_cannot_fail.py](demo_09_evals_a_change_is_a_release_and_the_check_that_cannot_fail.py) | Evals: a change is a release, and the check that cannot fail |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson asks DocuMind no question: it reads the ledger, the caches' records and the alert policies, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. If you ran it, leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson asks DocuMind no question: it reads the ledger, the caches' records and the alert policies, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson asks DocuMind no question: it reads the ledger, the caches' records and the alert policies, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_ui_and_the_ledger_where_a_change_lands_on_your_lane.py

The Documents page as yourself, the same ledger through the API as the UI's account, then the three records the caches compare. A change ends in the ledger, so read the ledger first, where an operator would. The UI's address is built from your project number, as the setup block built API: Open it signed in to Google as yourself and choose Documents. The Versions table is the ledger: one row per source, with its status, its chunks, what its last change cost (reused, embedded, retired), the embedding it was made with, when it landed and where it is held. The caption above it prints the count of current versions, the corpus fingerprint, the last change and the tenant's data_region. Your email maps to acme, so these are acme's rows. The same rows come from the API. GET /v1/sources is the versions view main.py serves. The shell calls it as documind-ui-sa, the UI's own account, which make roster put on all three tenants, so the call could name any of them. The UI asked as you, and only acme was yours. One ledger, two callers: The same rows come from the API. GET /v1/sources is the versions view main.py serves. The shell calls it as documind-ui-sa, the UI's own account, which make roster put on all three tenants, so the call could name any of them. The UI asked as you, and only acme was yours. One ledger, two callers: any is acme's data_region, set by make roster, and it is why the managed stores hold acme's copies. The handbook row's last three counts are what its last change cost: an undo shows 283 reused and 0 embedded, and a re-issue like revision 2 shows 281 and 2. Then the three records that decide whether a cache may be used. Firestore holds them, and the cell reads each one directly:

**`step_01_the_ui_and_the_ledger_where_a_change_lands(session)` — The UI and the ledger: where a change lands on your lane / The UI and the ledger: where a change lands on your lane**

The Documents page as yourself, the same ledger through the API as the UI's account, then the three records the caches compare. A change ends in the ledger, so read the ledger first, where an operator would. The UI's address is built from your project number, as the setup block built API:

Operation: bash — run in the operator shell (prints your UI's address).

Expected shape, not a promised result:

```text
https://documind-ui-NUMBER.asia-south1.run.app
```

**`step_02_the_ui_and_the_ledger_where_a_change_lands(session)` — The UI and the ledger: where a change lands on your lane / The UI and the ledger: where a change lands on your lane**

Open it signed in to Google as yourself and choose Documents. The Versions table is the ledger: one row per source, with its status, its chunks, what its last change cost (reused, embedded, retired), the embedding it was made with, when it landed and where it is held. The caption above it prints the count of current versions, the corpus fingerprint, the last change and the tenant's data_region. Your email maps to acme, so these are acme's rows. The same rows come from the API. GET /v1/sources is the versions view main.py serves. The shell calls it as documind-ui-sa, the UI's own account, which make roster put on all three tenants, so the call could name any of them. The UI asked as you, and only acme was yours. One ledger, two callers:

Operation: bash — run in the operator shell (one GET as the UI's account; reads the ledger, writes nothing).

Expected shape, not a promised result:

```text
acme: any | NUMBER current versions | fingerprint ... | last ingest_...
  acme/hr_policy_2026.md indexed 283 chunks, reused N embedded N retired N text-embedding-005@1
```

**`step_03_the_ui_and_the_ledger_where_a_change_lands(session)` — The UI and the ledger: where a change lands on your lane / The UI and the ledger: where a change lands on your lane**

The same rows come from the API. GET /v1/sources is the versions view main.py serves. The shell calls it as documind-ui-sa, the UI's own account, which make roster put on all three tenants, so the call could name any of them. The UI asked as you, and only acme was yours. One ledger, two callers: any is acme's data_region, set by make roster, and it is why the managed stores hold acme's copies. The handbook row's last three counts are what its last change cost: an undo shows 283 reused and 0 embedded, and a re-issue like revision 2 shows 281 and 2. Then the three records that decide whether a cache may be used. Firestore holds them, and the cell reads each one directly:

Operation: bash — run in the operator shell (three Firestore reads; writes nothing).

Expected shape, not a promised result:

```text
ledger/acme: fingerprint ..., NUMBER versions, last event ...
tenant_caches/acme: none  (or: packed under ...: current | STALE)
answer_cache, acme: N entries, N under the current fingerprint
```

### demo_04_architecture_the_path_a_change_takes_station_by_station.py

The cell cuts version 1 and revision 2 of the handbook with shared/documind_corpus.py, the notebooks' twin of the worker's chunker, which mints the same chunk texts and hashes. It applies the carry-over's rule: a chunk is reused when its hash is held. Then it cuts the same two texts as whole-document windows, the way the worker cut a handbook before 12 September 2026.

**`step_01_the_re_issue_offline(session)` — Architecture: the path a change takes, station by station / Do it: the re-issue, offline**

The cell cuts version 1 and revision 2 of the handbook with shared/documind_corpus.py, the notebooks' twin of the worker's chunker, which mints the same chunk texts and hashes. It applies the carry-over's rule: a chunk is reused when its hash is held. Then it cuts the same two texts as whole-document windows, the way the worker cut a handbook before 12 September 2026.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
by section: 283 chunks, 281 reused, 2 embedded (preamble, NP-03), 453 characters sent
by whole-document windows: 92 chunks, 0 reused, 92 embedded, 178,706 characters sent
revision 2's first lines: '# ACME Employee Handbook 2026 (revision 2)', then 'Effective from: 2026-10-01. Revision 2 changes NP-03: the no'
```

### demo_05_architecture_three_designs_the_kit_rejected_and_the_number_that_would_change_eac.py

The cell prices the same edit cut both ways at lesson 8.3's embedding price, reads the retention window and its floor from the Makefile and variables.tf, and reads the push lane's limits from eventarc.tf and the worker's deploy script to compute the rewrite bound.

**`step_01_the_three_thresholds_from_the_kit_s_files(session)` — Architecture: three designs the kit rejected, and the number that would change each / Do it: the three thresholds, from the kit's files**

The cell prices the same edit cut both ways at lesson 8.3's embedding price, reads the retention window and its floor from the Makefile and variables.tf, and reads the push lane's limits from eventarc.tf and the worker's deploy script to compute the rewrite bound.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
1. one clause edited: Rs 0.0010 to embed by section, Rs 0.38 by whole-document windows (394 times as much)
2. retired rows live 30 days (RETENTION_DAYS); the window can be set from 1 to 3650 days, never to zero
3. rewrites at once that the push lane clears inside 6,600 s of backoff, at 1 s a document: 198,000
3. rewrites at once that the push lane clears inside 6,600 s of backoff, at 10 s a document: 19,800
```

### demo_06_failure_modes_what_pages_what_does_not_and_what_the_design_does_about_it.py

The cell reads every Terraform file, lists the alert policies that watch the document lifecycle with what each one reads and when it exists, and counts the policies that read the main subscription, its oldest unacknowledged age, and cache_stale. The walk's planner is pure Python. The cell hands it three objects nobody indexed: one whose claim was cut off in processing, one zero-byte object, and one PDF the worker queued for the batch lane. Then it asks the claim's lease what the night's rewrite of the first will find. The same list from the Monitoring API: every policy on your lane by name, and whether any of them reads the main subscription or the dead-letter one.

**`step_01_the_policies_the_kit_declares_read_from_it(session)` — Failure modes: what pages, what does not, and what the design does about it / Do it: the policies the kit declares, read from its files**

The cell reads every Terraform file, lists the alert policies that watch the document lifecycle with what each one reads and when it exists, and counts the policies that read the main subscription, its oldest unacknowledged age, and cache_stale.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
ingest_failed      reads ingest_events
reconcile_drift    reads reconcile_drift - declared only when reconcile_job is true
reconcile_failed   reads completed_task_attempt_count on documind-reconcile - declared only when reconcile_job is true
dlq_depth          reads num_undelivered_messages on ingest-dlq-sub
ingest_backlog     reads oldest_unacked_message_age on documind-ingest-push
doc_type_pin_miss  reads doc_type_pin_miss
policies that read documind-ingest-push: 1; that read oldest_unacked_message_age: 1; that count cache_stale: 0
the walk: RECONCILE_JOB   ?= false | the batch job: BATCH_JOB       ?= false
```

**`step_02_the_walk_on_three_stuck_states(session)` — Failure modes: what pages, what does not, and what the design does about it / Do it: the walk on three stuck states**

The walk's planner is pure Python. The cell hands it three objects nobody indexed: one whose claim was cut off in processing, one zero-byte object, and one PDF the worker queued for the batch lane. Then it asks the claim's lease what the night's rewrite of the first will find.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
acme/cut_off.md    reingest  (not in the ledger)
acme/poison.pdf    reingest  (not in the ledger)
acme/big.pdf       queued    (handed to the batch lane; the batch job indexes it, the claim says queued)
drift 2 of 3 objects
acme/cut_off.md's claim at the walk: 23,100 s old, its lease 660 s, so the rewrite's delivery takes the claim back and indexes the bytes
```

**`step_03_on_your_lane_the_policies_that_exist(session)` — Failure modes: what pages, what does not, and what the design does about it / Read it on your lane: the policies that exist**

The same list from the Monitoring API: every policy on your lane by name, and whether any of them reads the main subscription or the dead-letter one.

Operation: bash — run in the operator shell (one GET on the Monitoring API; changes nothing).

Expected shape, not a promised result:

```text
11 alert policies on the lane
  A registered document arrived at a version nobody reviewed
  API p95 latency > 3s
  Desk case queue: a case due within 24 hours and unacknowledged, or breached
  Desk gate check: a door could not read which tenants are on
  Desk: a delegation was refused
  Ingest dead-letter queue holds messages
  Ingest failed
  Ingest subscription backlog: oldest message over 30 minutes
  Unanswerable rate > 20% for a tenant
  documind-slm left warm: instances > 0 for 2 hours
  documind-vllm left warm: instances > 0 for 2 hours
reads documind-ingest-push: True | reads the dead-letter subscription: True

13 alert policies on the lane
  A registered document arrived at a version nobody reviewed
  API p95 latency > 3s
  Desk case queue: a case due within 24 hours and unacknowledged, or breached
  Desk gate check: a door could not read which tenants are on
  Desk: a delegation was refused
  Ingest dead-letter queue holds messages
  Ingest failed
  Ingest subscription backlog: oldest message over 30 minutes
  Ledger drift above zero for two nights
  Nightly reconcile failed
  Unanswerable rate > 20% for a tenant
  documind-slm left warm: instances > 0 for 2 hours
  documind-vllm left warm: instances > 0 for 2 hours
reads documind-ingest-push: True | reads the dead-letter subscription: True
```

### demo_07_cost_standing_still_staying_fresh_and_one_change_at_1k_100k_and_10m_documents.py

This is component 6's COST-MODEL.md as something a reviewer can rerun. It measures the kit's corpus with the kit's own chunker, carries lesson 8.3's prices as dated constants, and uses the edit's counts from this page: its characters, its datapoints, and the Firestore writes and reads the kit's functions made.

**`step_01_the_cost_model_as_a_script(session)` — Cost: standing still, staying fresh, and one change, at 1k, 100k and 10M documents / Do it: the cost model as a script**

This is component 6's COST-MODEL.md as something a reviewer can rerun. It measures the kit's corpus with the kit's own chunker, carries lesson 8.3's prices as dated constants, and uses the edit's counts from this page: its characters, its datapoints, and the Firestore writes and reads the kit's functions made.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
the kit's corpus: 27 documents, 102.11 chunks and 128,589 characters each; one edit like the handbook's Rs 0.14 before the fingerprint
     1,000 documents: Rs 7,488 a month standing, Rs 273 to embed once, Rs 0.17 an edit; 43,769 edits a month cost as much as standing still
   100,000 documents: Rs 1.25 lakh a month standing, Rs 27,325 to embed once, Rs 3.12 an edit; 40,150 edits a month cost as much as standing still
10,000,000 documents: Rs 94.18 lakh a month standing, Rs 27.33 lakh to embed once, Rs 297.64 an edit; 31,643 edits a month cost as much as standing still
```

### demo_09_evals_a_change_is_a_release_and_the_check_that_cannot_fail.py

Do it: the gate offline, and what moves with a document

**`step_01_the_gate_offline_and_what_moves_with_a_doc(session)` — Evals: a change is a release, and the check that cannot fail / Do it: the gate offline, and what moves with a document**

Do it: the gate offline, and what moves with a document

Operation: bash — run in the operator shell, in $DEMO_ROOT (the offline gate, then a Python cell; Rs 0: no credential, no call).

Expected shape, not a promised result:

```text
== eval gate: OFFLINE (no credentials, no cost) ==
  65 golden rows over 3 tenants, 27 documents

  [PASS] falsifiable
  [PASS] anchors
  [PASS] coverage

  The golden set is sound. It can go red, and it still contains the rows that would.
make eval-live SOURCE=hr_policy_2026.md sends 10 of 65 rows: lk-01, lk-02, lk-03, lk-04, lk-05, lk-06, lk-07, lk-08, lk-09, vr-01
vr-01 (required): must not say ['90 days'], which only revision 2 holds (True); re-issue the handbook and this row moves with it, in one commit
anchors over whole documents: 0 problems - it reads files and never a chunk, so no chunker change and no carry-over bug can turn it red
what blocks live: 9 thresholds and 15 required rows; must_retrieve recall is printed as [info]
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson asks DocuMind no question: it reads the ledger, the caches' records and the alert policies, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. If you ran it, leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson asks DocuMind no question: it reads the ledger, the caches' records and the alert policies, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. If you ran it, leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_8.4_Design_Self_Updating_Docs_WIX.html`. All 54 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `84d0e937ed8f263a6f0838649ecb9372dcec6dd5`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
