# Lesson 1.3: Create and validate compatible embeddings

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_one_declared_embedding_from_terraform_to_the_row.py](demo_03_one_declared_embedding_from_terraform_to_the_row.py) | One declared embedding, from Terraform to the row |
| 4 | [demo_04_the_call_768_numbers_under_the_document_task_type.py](demo_04_the_call_768_numbers_under_the_document_task_type.py) | The call: 768 numbers under the document task type |
| 5 | [demo_05_batches_250_texts_and_15_000_tokens_per_request.py](demo_05_batches_250_texts_and_15_000_tokens_per_request.py) | Batches: 250 texts and 15,000 tokens per request |
| 6 | [demo_06_validate_the_stamp_and_the_function_that_reads_it.py](demo_06_validate_the_stamp_and_the_function_that_reads_it.py) | Validate: the stamp, and the function that reads it |
| 7 | [demo_07_carry_over_re_issue_the_handbook_embed_only_what_changed.py](demo_07_carry_over_re_issue_the_handbook_embed_only_what_changed.py) | Carry-over: re-issue the handbook, embed only what changed |
| 8 | [demo_08_the_sparse_twin_the_notebook_twin_and_what_embedding_bills.py](demo_08_the_sparse_twin_the_notebook_twin_and_what_embedding_bills.py) | The sparse twin, the notebook twin, and what embedding bills |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The seeded original handbook and live ingest worker; this lesson temporarily reissues it.

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. Steps 6 and 7 import the worker's own indexer.py, which imports the Vector Search and Gemini SDKs at the top. The setup block installed only the Firestore client; add the other two once. Nothing in this lesson writes to Vector Search.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. Steps 6 and 7 import the worker's own indexer.py, which imports the Vector Search and Gemini SDKs at the top. The setup block installed only the Firestore client; add the other two once. Nothing in this lesson writes to Vector Search.

Operation: bash — run in the operator shell, once.

### demo_03_one_declared_embedding_from_terraform_to_the_row.py

All read-only. The first prints the worker's environment, the second asks the API what it is serving, the third reads the pair off the ledger rows the Versions table renders.

**`step_01_three_reads_of_one_pair(session)` — One declared embedding, from Terraform to the row / Call it: three reads of one pair**

All read-only. The first prints the worker's environment, the second asks the API what it is serving, the third reads the pair off the ledger rows the Versions table renders.

Operation: bash — run in the operator shell.

Expected shape, not a promised result:

```text
{'name': 'EMBEDDING_MODEL', 'value': 'text-embedding-005'}
{'name': 'EMBEDDING_VERSION', 'value': '1'}
api serves embedding text-embedding-005@1 | generator gemini-3.6-flash | retrieval hybrid vector
acme/code_on_wages_2019.pdf                  chunks   67  reused    0  embedded   67  text-embedding-005@1
acme/dpdp_act_2023.pdf                       chunks   44  reused    0  embedded   44  text-embedding-005@1
acme/hr_policy_2026.md                       chunks  283  reused    0  embedded  283  text-embedding-005@1
...
```

### demo_04_the_call_768_numbers_under_the_document_task_type.py

This cell costs money, a very small amount: two calls on a 234-character clause, about a tenth of a paisa. It reads NP-03's text and stored vector off the lane, embeds the same text under the document profile with the worker's exact settings, and compares by cosine. Then it embeds the same text under the query profile and compares again.

**`step_01_embed_one_clause_yourself_both_ways(session)` — The call: 768 numbers under the document task type / Do it: embed one clause yourself, both ways**

This cell costs money, a very small amount: two calls on a 234-character clause, about a tenth of a paisa. It reads NP-03's text and stored vector off the lane, embeds the same text under the document profile with the worker's exact settings, and compares by cosine. Then it embeds the same text under the query profile and compares again.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash; two paid calls).

Expected shape, not a promised result:

```text
lane vector: 768 numbers; first three [0.0213, -0.0117, 0.0388]
same text, RETRIEVAL_DOCUMENT: cosine to the lane's vector 1.0
same text, RETRIEVAL_QUERY:    cosine to the lane's vector 0.9xxx
```

### demo_05_batches_250_texts_and_15_000_tokens_per_request.py

The loader's copy of the rule, on the chunks you cut in lesson 1.2. No call is made; a plan is printed.

**`step_01_plan_the_handbook_rs_0(session)` — Batches: 250 texts and 15,000 tokens per request / Do it: plan the handbook, Rs 0**

The loader's copy of the rule, on the chunks you cut in lesson 1.2. No call is made; a plan is printed.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
handbook: 283 chunks, 158,692 chars -> 4 requests of [85, 78, 78, 42] texts, est tokens [14833, 14949, 14944, 8057]
wages mirror: 65 chunks, 102,444 chars -> 3 requests of [28, 28, 9] texts, est tokens [...]
the handbook in one request would carry about 52,783 estimated tokens: over 20,000, refused whole
```

### demo_06_validate_the_stamp_and_the_function_that_reads_it.py

Read the stamp off one row, Rs 0 This cell imports the worker's indexer.py as deployed and runs its test over every current acme row. The import builds the worker's embedding client (which is why the project must be in the environment) but nothing is embedded. The backfill target prints a plan when APPLY=1 is absent: it reads every current row and counts the ones that fail the same function. On a healthy lane the count is zero, and the target is how you would find out otherwise. It needs the index name from Terraform's outputs; if your checkout has no Terraform state, the second form takes the name from the API instead. The unit tests run the worker's file against doubled SDKs, offline, in a fraction of a second.

**`step_01_read_the_stamp_off_one_row_rs_0(session)` — Validate: the stamp, and the function that reads it / Read the stamp off one row, Rs 0**

Read the stamp off one row, Rs 0

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
row id: acme:9f3c...#1
  locator                  'NP-03'
  chunk_hash               'f4512754ae41...'
  embedding_model          'text-embedding-005'
  embedding_version        '1'
  embedding_task_type      'RETRIEVAL_DOCUMENT'
  sparse_encoder_version   'blake2b-tf-v1'
  schema_version           2
  kind                     'text'
  doc_type                 'unknown'
  embedding                768 numbers, first three [0.0213, -0.0117, 0.0388]
```

**`step_02_validate_every_current_row_of_a_tenant_wit(session)` — Validate: the stamp, and the function that reads it / Validate every current row of a tenant, with the worker's own function**

This cell imports the worker's indexer.py as deployed and runs its test over every current acme row. The import builds the worker's embedding client (which is why the project must be in the environment) but nothing is embedded.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
acme current rows: N  compatible: N  incompatible: 0
   N rows stamped ('text-embedding-005', '1', 'RETRIEVAL_DOCUMENT', 768)
the worker expects: ('text-embedding-005', '1', 'RETRIEVAL_DOCUMENT', 768)
```

**`step_03_the_same_check_as_an_operator_runs_it_and(session)` — Validate: the stamp, and the function that reads it / The same check as an operator runs it, and as the tests run it**

The backfill target prints a plan when APPLY=1 is absent: it reads every current row and counts the ones that fail the same function. On a healthy lane the count is zero, and the target is how you would find out otherwise. It needs the index name from Terraform's outputs; if your checkout has no Terraform state, the second form takes the name from the API instead. The unit tests run the worker's file against doubled SDKs, offline, in a fraction of a second.

Operation: bash — run in the operator shell (both read-only).

Expected shape, not a promised result:

```text
{"event": "backfill_vectors_plan", "index": "projects/NUMBER/locations/asia-south1/indexes/1234567890123456789", "tenant": "acme", "current_chunks": N, "needs_document_embedding": 0, "invalid_chunks": 0, "embedding_task_type": "RETRIEVAL_DOCUMENT", "note": "Pause uploads/undo/batch writers; keep answer caches off during repair and validation."}
............
----------------------------------------------------------------------
Ran 12 tests in 0.014s

OK
```

### demo_07_carry_over_re_issue_the_handbook_embed_only_what_changed.py

The worker's planner on the two versions of the handbook, with a stand-in for what held_vectors() would lend: one vector per version-1 hash. The upload must keep the object name, acme/hr_policy_2026.md, or it is a new source and nothing is held. The loop then waits for the worker's ingest_ok line and prints its counts. Cost: two clauses, 453 characters, about a hundredth of a paisa; a Markdown file pays no Document AI. Refresh Documents. The handbook's row in the Versions table now reads reused 281, embedded 2, retired 283, with an effective date of 1 October 2026 that the revision declares in its first lines. The first call below is the same row from the API; the second reads the rows themselves and checks the thing the counts claim: an unchanged clause's new row carries the same numbers as its retired predecessor, and a changed clause's does not. The third asks the question the revision changed the answer to. Upload version 1 again under the same name. Its doc_key is the one the lane retired a minute ago, so the worker does not parse, chunk or embed anything: it flips the retired rows back to current, retires revision 2, and logs ingest_reactivated with embedded 0. This is the undo from lesson 1.1, seen from the embedding side: nothing was ever deleted, so nothing has to be made again.

**`step_01_plan_it_locally_rs_0(session)` — Carry-over: re-issue the handbook, embed only what changed / Plan it locally, Rs 0**

The worker's planner on the two versions of the handbook, with a stand-in for what held_vectors() would lend: one vector per version-1 hash.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
v2: 283 chunks, reused 281, to embed 2: ['preamble', 'NP-03']
  preamble: hash 903e2b39ee92 -> b4736d2f3e52
  NP-03: hash f4512754ae41 -> 876232171dec
```

**`step_02_on_the_lane_revision_2_over_the_same_name(session)` — Carry-over: re-issue the handbook, embed only what changed / Do it on the lane: revision 2 over the same name**

The upload must keep the object name, acme/hr_policy_2026.md, or it is a new source and nothing is held. The loop then waits for the worker's ingest_ok line and prints its counts. Cost: two clauses, 453 characters, about a hundredth of a paisa; a Markdown file pays no Document AI.

Operation: bash — run in the operator shell, in $DEMO_ROOT (one re-issue; the worker takes under a minute).

Expected shape, not a promised result:

```text
>> chunks reused embedded retired effective_from: 283	281	2	283	2026-10-01
```

**`step_03_see_it_in_the_ui_then_read_it_three_more_w(session)` — Carry-over: re-issue the handbook, embed only what changed / See it in the UI, then read it three more ways**

Refresh Documents. The handbook's row in the Versions table now reads reused 281, embedded 2, retired 283, with an effective date of 1 October 2026 that the revision declares in its first lines. The first call below is the same row from the API; the second reads the rows themselves and checks the thing the counts claim: an unchanged clause's new row carries the same numbers as its retired predecessor, and a changed clause's does not. The third asks the question the revision changed the answer to.

Operation: bash — run in the operator shell.

Expected shape, not a promised result:

```text
acme/hr_policy_2026.md chunks 283 reused 281 embedded 2 retired 283 effective 2026-10-01 text-embedding-005@1
rows for the source: 566 | current: 283 | retired: 283
  LV-01     hash ff463cede286 -> ff463cede286   same vector: True
  NP-03     hash f4512754ae41 -> 876232171dec   same vector: False
  preamble  hash 903e2b39ee92 -> b4736d2f3e52   same vector: False
A confirmed employee at grade E3 or above serves a notice period of 90 days ... [Source 1]
[('1', 'hr_policy_2026.md'), ('2', 'hr_policy_2026.md')] vector
```

**`step_04_undo_it_the_same_bytes_again_and_nothing_i(session)` — Carry-over: re-issue the handbook, embed only what changed / Undo it: the same bytes again, and nothing is embedded**

Upload version 1 again under the same name. Its doc_key is the one the lane retired a minute ago, so the worker does not parse, chunk or embed anything: it flips the retired rows back to current, retires revision 2, and logs ingest_reactivated with embedded 0. This is the undo from lesson 1.1, seen from the embedding side: nothing was ever deleted, so nothing has to be made again.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the undo; no model call).

Expected shape, not a promised result:

```text
>> reactivated: chunks reused embedded retired: 283	283	0	283
A confirmed employee at grade E3 or above serves a notice period of 60 days ... [Source 1]
```

### demo_08_the_sparse_twin_the_notebook_twin_and_what_embedding_bills.py

Run it on the lane's text, Rs 0

**`step_01_on_the_lane_s_text_rs_0(session)` — The sparse twin, the notebook twin, and what embedding bills / Run it on the lane's text, Rs 0**

Run it on the lane's text, Rs 0

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
row stamp: blake2b-tf-v1 | encoder here: blake2b-tf-v1
NP-03: 41 words, 33 distinct -> 33 sparse dimensions, max weight 2.5
the question: 13 dimensions, 9 shared with NP-03: ['a', 'at', 'confirmed', 'days', 'e3', 'employee', 'grade', 'notice', 'of']
same text twice, same dimensions: True
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_1.3_Embeddings_WIX.html`. All 48 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `56ae46416219aee8c45075960c9f86bab98015ac`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
