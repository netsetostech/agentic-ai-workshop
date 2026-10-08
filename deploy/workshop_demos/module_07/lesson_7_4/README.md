# Lesson 7.4: Compare quality and test update/withdrawal freshness

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_four_events_through_the_kit_s_mirror_run.py](demo_03_the_four_events_through_the_kit_s_mirror_run.py) | The four events through the kit's mirror, run |
| 4 | [demo_04_six_arms_one_golden_set_is_a_store_as_good.py](demo_04_six_arms_one_golden_set_is_a_store_as_good.py) | Six arms, one golden set: is a store as good? |
| 5 | [demo_05_a_new_version_then_the_undo.py](demo_05_a_new_version_then_the_undo.py) | A new version, then the undo |
| 6 | [demo_06_a_withdrawal_then_the_restore.py](demo_06_a_withdrawal_then_the_restore.py) | A withdrawal, then the restore |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The managed mirrors from 7.3 and the original Zeta handbook; update and withdrawal are intentional.

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

### demo_03_the_four_events_through_the_kit_s_mirror_run.py

Do it

**`step_01_the_four_events_through_the_kit_s_mirror_r(session)` — The four events through the kit's mirror, run / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the kit's mirror through the four events; no store, no network).

Expected shape, not a promised result:

```text
1. v1 is ingested: the worker's swap, then after_swap()
     mirror_ok     rag_engine    upsert            v1 uploaded, 73 characters
     mirror_ok     vertex_search upsert            v1 uploaded, 73 characters
   make managed-status: rag_engine    in sync
   make managed-status: vertex_search in sync
2. v2 replaces it: after_swap(), with v1 in the swap's retired_doc_keys
     mirror_ok     rag_engine    upsert            v2 uploaded, 73 characters
     mirror_ok     vertex_search upsert            v2 uploaded, 73 characters
     mirror_ok     rag_engine    delete:superseded 1
     mirror_ok     vertex_search delete:superseded 1
   make managed-status: rag_engine    in sync
   make managed-status: vertex_search in sync
3. the undo, v1's bytes again: the worker flips the rows back, then after_undo(), which is given no text
     mirror_ok     rag_engine    upsert            v1 uploaded, 73 characters
     mirror_ok     vertex_search upsert            v1 uploaded, 73 characters
     mirror_ok     rag_engine    delete:superseded 1
     mirror_ok     vertex_search delete:superseded 1
   the stores now hold for v1: {'rag_engine': '...a notice period of 30 days.', 'vertex_search': '...a notice period of 30 days.'}
   make managed-status: rag_engine    in sync
   make managed-status: vertex_search in sync
4. make retire: the rows retired, the ledger row withdrawn, then retired(..., 'withdrawn')
     mirror_ok     rag_engine    delete:withdrawn  1
     mirror_ok     vertex_search delete:withdrawn  1
   make managed-status: rag_engine    in sync
   make managed-status: vertex_search in sync
5. make restore, while Vertex AI Search refuses one import: the worker's reactivation, then after_undo()
     mirror_ok     rag_engine    upsert            v1 uploaded, 73 characters
     mirror_failed vertex_search upsert            TimeoutError: the import did not finish
   make managed-status: rag_engine    in sync
   make managed-status: vertex_search drift, missing ['v1']
```

### demo_04_six_arms_one_golden_set_is_a_store_as_good.py

Do it

**`step_01_six_arms_one_golden_set_is_a_store_as_good(session)` — Six arms, one golden set: is a store as good? / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (retrieval only, no model: a few minutes).

Expected shape, not a promised result:

```text
python evals/ablate.py --project documind-ai-YOUR-ID --region asia-south1 --arms all
47 rows with anchors, 66 anchors, one knob per arm (project documind-ai-YOUR-ID, embeddings in asia-south1, ranker on global)

arm                                          recall@depth  recall@5    mrr rows@1.0  p95 ms
dense 5, no reranker                                 0.94      0.94   0.81       44     ...
       lost: lk-19: payment_of_bonus_act_1965 - not retrieved at depth 5
       lost: lk-21: code_on_wages_2019 - not retrieved at depth 5
       lost: jn-11: labour_codes_compliance_handbook - not retrieved at depth 5
dense 20 -> rerank 5   (the lane)                    1.00      0.94   0.81       44     ...
       lost: lk-19: payment_of_bonus_act_1965 - ranked out (in the candidates, not the five)
       lost: lk-21: code_on_wages_2019 - ranked out (in the candidates, not the five)
       lost: jn-11: labour_codes_compliance_handbook - ranked out (in the candidates, not the five)
dense 50 -> rerank 5                                 1.00      0.94   0.81       44     ...
       lost: lk-19: payment_of_bonus_act_1965 - ranked out (in the candidates, not the five)
       lost: lk-21: code_on_wages_2019 - ranked out (in the candidates, not the five)
       lost: jn-11: labour_codes_compliance_handbook - ranked out (in the candidates, not the five)
hybrid 20 -> rerank 5  (4.5, not wired)              1.00      0.94   0.81       44     ...
       lost: lk-19: payment_of_bonus_act_1965 - ranked out (in the candidates, not the five)
       lost: lk-21: code_on_wages_2019 - ranked out (in the candidates, not the five)
       lost: jn-11: labour_codes_compliance_handbook - ranked out (in the candidates, not the five)
rag_engine 20 -> rerank 5  (4.3's corpus, P9.4)         0.96      0.91   0.76       41     ...   (2 rows failed)
       jn-04: RuntimeError: no RAG Engine corpus 'documind-globex': make rag-corpus TENANT=globex, then MANAGED_MIRROR=rag_engine
       lk-28: RuntimeError: no RAG Engine corpus 'documind-globex': make rag-corpus TENANT=globex, then MANAGED_MIRROR=rag_engine
       lost: lk-02: PR-05, hr_policy_2026 - ranked out (in the candidates, not the five)
       lost: lk-05: IT-SEC-04, hr_policy_2026 - not retrieved at depth 1
       lost: jn-07: IT-SEC-04 - not retrieved at depth 2
       lost: jn-11: labour_codes_compliance_handbook - ranked out (in the candidates, not the five)
vertex_search 20 -> rerank 5  (4.4's data store, R4)         0.88      0.71   0.61       30     ...   (2 rows failed)
       jn-04: NotFound: 404 DataStore documind-globex not found
       lk-28: NotFound: 404 DataStore documind-globex not found
       lost: lk-05: IT-SEC-04, hr_policy_2026 - not retrieved at depth 0
       lost: lk-08: FIN-02 - ranked out (in the candidates, not the five)
       lost: lk-09: WFH-01 - not retrieved at depth 6
       lost: lk-13: MSA-09 - not retrieved at depth 3
       lost: jn-01: LV-07 - not retrieved at depth 12
       lost: jn-02: NP-03, LV-07 - not retrieved at depth 15
       lost: jn-03: LV-07, NP-03 - not retrieved at depth 18
       lost: jn-07: IT-SEC-04 - not retrieved at depth 5
       lost: lk-15: maternity_benefit_amendment_act_2017 - ranked out (in the candidates, not the five)
       lost: lk-24: osh_code_2020 - ranked out (in the candidates, not the five)
       lost: lk-25: osh_code_2020 - ranked out (in the candidates, not the five)
       lost: lk-26: dpdp_act_2023 - ranked out (in the candidates, not the five)
       lost: lk-29: osh_code_2020 - ranked out (in the candidates, not the five)
       lost: lk-30: dpdp_act_2023 - ranked out (in the candidates, not the five)
       lost: lk-31: code_on_social_security_2020 - ranked out (in the candidates, not the five)

Read it in this order: recall@depth is the reranker's ceiling - if the 20 and 50 rows agree, depth is not the knob;
recall@5 of the lane's row minus the first row is the reranker's lift, and p95 is what it costs;
the hybrid row says whether a BM25 leg is worth wiring - twenty of the anchors are clause codes, its home ground;
the rag_engine row (--arms all) is 4.3's corpus against the lane's own rows - a managed chunk that splits a clause from its code shows up as a miss.
```

### demo_05_a_new_version_then_the_undo.py

Do it Now the undo: the same name, with the first version's bytes, straight from the kit's corpus. This is the worker's branch for a version it has seen before:

**`step_01_a_new_version_then_the_undo(session)` — A new version, then the undo / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (a second version of zeta's handbook, then the check).

Expected shape, not a promised result:

```text
...
>> gs://documind-ai-YOUR-ID-uploads/zeta/hr_policy_zeta_2026.md - waiting for the worker (up to 5 min)
>> event doc_key chunks reused embedded retired effective_from
>> ingest_ok	zeta_025c4143c0a1115dda29f3556faff8cbe552249f4576c78036ea07a80f9be422	283	282	1	283	
>> retired (doc_keys, chunks, expire days): zeta_e920a147e36b71710f6ba542f63694634bb3755a581d443c2603d899f125256a	283	30
>> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_zeta_2026.md API=<candidate url>
the mirror's doc.mirror events for zeta since 2026-09-24T08:00:00Z (the audit bucket):
  08:00:48  upsert            rag_engine    us-central1 zeta_025c4143...
  08:00:48  upsert            vertex_search global      zeta_025c4143...
  08:00:49  delete:superseded rag_engine    us-central1 zeta_e920a147...
  08:00:49  delete:superseded vertex_search global      zeta_e920a147...
make managed-status TENANT_ONLY=zeta, until the stores match the ledger (the handbook indexed):
  0:00  handbook indexed; rag_engine in sync; vertex_search drift, missing zeta_025c4143...
  0:20  handbook indexed; rag_engine in sync; vertex_search in sync
{"tenant": "zeta", "store": "rag_engine", "ledger_current": 7, "held": 7, "missing": 0, "orphans": 0, "status": "in sync", "missing_doc_keys": [], "orphan_doc_keys": []}
{"tenant": "zeta", "store": "vertex_search", "ledger_current": 7, "held": 7, "missing": 0, "orphans": 0, "status": "in sync", "missing_doc_keys": [], "orphan_doc_keys": []}
zeta, answered from vertex_search: A confirmed employee at grade L4 or above serves a notice period of 45 days [1].
  cites zeta:zeta_025c4143...#vs-f44cd45f3eb8
```

**`step_02_a_new_version_then_the_undo(session)` — A new version, then the undo / Do it**

Now the undo: the same name, with the first version's bytes, straight from the kit's corpus. This is the worker's branch for a version it has seen before:

Operation: bash — run in the operator shell, in the kit (the first version's bytes again, then the check).

Expected shape, not a promised result:

```text
...
>> gs://documind-ai-YOUR-ID-uploads/zeta/hr_policy_zeta_2026.md - waiting for the worker (up to 5 min)
>> event doc_key chunks reused embedded retired effective_from
>> ingest_reactivated	zeta_e920a147e36b71710f6ba542f63694634bb3755a581d443c2603d899f125256a	283	283	0	283	
>> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_zeta_2026.md API=<candidate url>
the mirror's doc.mirror events for zeta since 2026-09-24T08:10:00Z (the audit bucket):
  08:10:48  upsert            rag_engine    us-central1 zeta_e920a147...
  08:10:48  upsert            vertex_search global      zeta_e920a147...
  08:10:49  delete:superseded rag_engine    us-central1 zeta_025c4143...
  08:10:49  delete:superseded vertex_search global      zeta_025c4143...
make managed-status TENANT_ONLY=zeta, until the stores match the ledger (the handbook indexed):
  0:00  handbook indexed; rag_engine in sync; vertex_search drift, missing zeta_e920a147...
  0:20  handbook indexed; rag_engine in sync; vertex_search in sync
{"tenant": "zeta", "store": "rag_engine", "ledger_current": 7, "held": 7, "missing": 0, "orphans": 0, "status": "in sync", "missing_doc_keys": [], "orphan_doc_keys": []}
{"tenant": "zeta", "store": "vertex_search", "ledger_current": 7, "held": 7, "missing": 0, "orphans": 0, "status": "in sync", "missing_doc_keys": [], "orphan_doc_keys": []}
zeta, answered from vertex_search: A confirmed employee at grade L4 or above serves a notice period of 30 days [1].
  cites zeta:zeta_e920a147...#vs-e9fd5992049d
```

### demo_06_a_withdrawal_then_the_restore.py

Do it Then the restore:

**`step_01_a_withdrawal_then_the_restore(session)` — A withdrawal, then the restore / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the handbook withdrawn by hand, then the check).

Expected shape, not a promised result:

```text
{"event": "reconcile_withdrawn", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/zeta/hr_policy_zeta_2026.md", "fingerprint": "756528d4215dfc80", "retired_doc_keys": ["zeta_e920a147e36b71710f6ba542f63694634bb3755a581d443c2603d899f125256a"], "retired_ids": ["zeta:e920a147e36b71710f6ba542f63694634bb3755a581d443c2603d899f125256a#0", "...", "zeta:e920a147e36b71710f6ba542f63694634bb3755a581d443c2603d899f125256a#99"], "retired_chunks": 283, "note": "a tombstone: the object is kept and nothing automatic re-ingests it; make restore SOURCE= does"}
the mirror's doc.mirror events for zeta since 2026-09-24T08:20:00Z (the audit bucket):
  08:20:24  delete:withdrawn  rag_engine    us-central1 zeta_e920a147...
  08:20:24  delete:withdrawn  vertex_search global      zeta_e920a147...
make managed-status TENANT_ONLY=zeta, until the stores match the ledger (the handbook withdrawn):
  0:00  handbook withdrawn; rag_engine in sync; vertex_search in sync
{"tenant": "zeta", "store": "rag_engine", "ledger_current": 6, "held": 6, "missing": 0, "orphans": 0, "status": "in sync", "missing_doc_keys": [], "orphan_doc_keys": []}
{"tenant": "zeta", "store": "vertex_search", "ledger_current": 6, "held": 6, "missing": 0, "orphans": 0, "status": "in sync", "missing_doc_keys": [], "orphan_doc_keys": []}
zeta, answered from vertex_search: The context does not say.
```

**`step_02_a_withdrawal_then_the_restore(session)` — A withdrawal, then the restore / Do it**

Then the restore:

Operation: bash — run in the operator shell, in the kit (the handbook brought back, then the check).

Expected shape, not a promised result:

```text
{"event": "reconcile_restored", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/zeta/hr_policy_zeta_2026.md", "generation": "1758000000021000", "next": "ingest_reactivated inside the undo window, ingest_ok (a fresh version) after it"}
the mirror's doc.mirror events for zeta since 2026-09-24T08:30:00Z (the audit bucket):
  08:30:39  upsert            rag_engine    us-central1 zeta_e920a147...
  08:30:39  upsert            vertex_search global      zeta_e920a147...
make managed-status TENANT_ONLY=zeta, until the stores match the ledger (the handbook indexed):
  0:00  handbook indexed; rag_engine in sync; vertex_search drift, missing zeta_e920a147...
  0:20  handbook indexed; rag_engine in sync; vertex_search in sync
{"tenant": "zeta", "store": "rag_engine", "ledger_current": 7, "held": 7, "missing": 0, "orphans": 0, "status": "in sync", "missing_doc_keys": [], "orphan_doc_keys": []}
{"tenant": "zeta", "store": "vertex_search", "ledger_current": 7, "held": 7, "missing": 0, "orphans": 0, "status": "in sync", "missing_doc_keys": [], "orphan_doc_keys": []}
zeta, answered from vertex_search: A confirmed employee at grade L4 or above serves a notice period of 30 days [1].
  cites zeta:zeta_e920a147...#vs-e9fd5992049d
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_7.4_Mirror_Freshness_WIX.html`. All 23 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `52a2208d70780892bee65299e6a93e78318165ff`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
