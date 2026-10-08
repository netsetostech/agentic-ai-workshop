# Lesson 1.4: Write, inspect and verify indexed records

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_write_the_order_the_worker_keeps_and_a_fresh_document_to_watch.py](demo_03_write_the_order_the_worker_keeps_and_a_fresh_document_to_watch.py) | Write: the order the worker keeps, and a fresh document to watch |
| 4 | [demo_04_inspect_firestore_the_claim_the_rows_the_ledger_row_the_fingerprint.py](demo_04_inspect_firestore_the_claim_the_rows_the_ledger_row_the_fingerprint.py) | Inspect Firestore: the claim, the rows, the ledger row, the fingerprint |
| 5 | [demo_05_inspect_vector_search_the_datapoint_its_restricts_and_a_search_for_itself.py](demo_05_inspect_vector_search_the_datapoint_its_restricts_and_a_search_for_itself.py) | Inspect Vector Search: the datapoint, its restricts, and a search for itself |
| 6 | [demo_06_inspect_the_mirror_and_the_audit_trail.py](demo_06_inspect_the_mirror_and_the_audit_trail.py) | Inspect the mirror and the audit trail |
| 7 | [demo_07_verify_the_two_rungs_that_read_the_records.py](demo_07_verify_the_two_rungs_that_read_the_records.py) | Verify: the two rungs that read the records |
| 8 | [demo_08_repair_expire_and_what_the_records_cost.py](demo_08_repair_expire_and_what_the_records_cost.py) | Repair, expire, and what the records cost |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Module 0's deployed Vector Search index, Firestore indexes and audit/mirror configuration.

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The index, the endpoint, the BigQuery table and the audit bucket are named in the environment of the two services that use them. Read them once into the shell; every cell below uses these variables. Both reads are read-only.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The index, the endpoint, the BigQuery table and the audit bucket are named in the environment of the two services that use them. Read them once into the shell; every cell below uses these variables. Both reads are read-only.

Operation: bash — run in the operator shell, once per shell.

Expected shape, not a promised result:

```text
index:    projects/documind-ai-YOUR-ID/locations/asia-south1/indexes/1234567890123456789
endpoint: projects/documind-ai-YOUR-ID/locations/asia-south1/indexEndpoints/9876543210987654321  deployed: documind_chunks_v1
mirror:   documind-ai-YOUR-ID.rag_data.chunk_source  audit: documind-ai-YOUR-ID-audit
```

### demo_03_write_the_order_the_worker_keeps_and_a_fresh_document_to_watch.py

The note is the kit's three-clause warehouse memo with one line added: your account and today's date. The line matters. A version is its bytes, and the kit's reindex smoke from Module 0 uploads the unchanged file under another name; if it ever ran on your lane, those bytes are already claimed, and the worker acks the same bytes again as a duplicate and writes nothing. One line of your own makes a new version key. The note is a Markdown file of about 500 characters with no PII: no Document AI, three embeddings, about a hundredth of a paisa. The block reads the index's datapoint count, writes and uploads the note, waits for the worker's line, then waits for the count to move. The index's statistics refresh on their own schedule, so the last wait can take a few minutes. The note is the kit's three-clause warehouse memo with one line added: your account and today's date. The line matters. A version is its bytes, and the kit's reindex smoke from Module 0 uploads the unchanged file under another name; if it ever ran on your lane, those bytes are already claimed, and the worker acks the same bytes again as a duplicate and writes nothing. One line of your own makes a new version key. The note is a Markdown file of about 500 characters with no PII: no Document AI, three embeddings, about a hundredth of a paisa. The block reads the index's datapoint count, writes and uploads the note, waits for the worker's line, then waits for the count to move. The index's statistics refresh on their own schedule, so the last wait can take a few minutes. Two reads tell you what the worker did with an upload. The first lists every ingest event of the last twenty minutes with its verdict: ingest_duplicate means the bytes were already claimed on this lane, ingest_failed carries the error, and no line at all means the event never reached the worker. The second reads the claim for the unchanged demo bytes; its gcs_uri names the object that holds them, which on a lane where the smoke has run is acme/smoke_note.md. The claim is per version, not per name: that is the record this whole step is about.

**`step_01_index_a_note_and_count_the_datapoints_befo(session)` — Write: the order the worker keeps, and a fresh document to watch / Do it: index a note, and count the datapoints before and after**

The note is the kit's three-clause warehouse memo with one line added: your account and today's date. The line matters. A version is its bytes, and the kit's reindex smoke from Module 0 uploads the unchanged file under another name; if it ever ran on your lane, those bytes are already claimed, and the worker acks the same bytes again as a duplicate and writes nothing. One line of your own makes a new version key. The note is a Markdown file of about 500 characters with no PII: no Document AI, three embeddings, about a hundredth of a paisa. The block reads the index's datapoint count, writes and uploads the note, waits for the worker's line, then waits for the count to move. The index's statistics refresh on their own schedule, so the last wait can take a few minutes.

Operation: bash — run in the operator shell, in $DEMO_ROOT (one small ingest).

Expected shape, not a promised result:

```text
datapoints before: N
>> event doc_key chunks pages embedded: ingest_ok  acme_9c41d0e2b7f5a1...  3  1  3
datapoints now: N+3
```

**`step_02_index_a_note_and_count_the_datapoints_befo(session)` — Write: the order the worker keeps, and a fresh document to watch / Do it: index a note, and count the datapoints before and after**

The note is the kit's three-clause warehouse memo with one line added: your account and today's date. The line matters. A version is its bytes, and the kit's reindex smoke from Module 0 uploads the unchanged file under another name; if it ever ran on your lane, those bytes are already claimed, and the worker acks the same bytes again as a duplicate and writes nothing. One line of your own makes a new version key. The note is a Markdown file of about 500 characters with no PII: no Document AI, three embeddings, about a hundredth of a paisa. The block reads the index's datapoint count, writes and uploads the note, waits for the worker's line, then waits for the count to move. The index's statistics refresh on their own schedule, so the last wait can take a few minutes. Two reads tell you what the worker did with an upload. The first lists every ingest event of the last twenty minutes with its verdict: ingest_duplicate means the bytes were already claimed on this lane, ingest_failed carries the error, and no line at all means the event never reached the worker. The second reads the claim for the unchanged demo bytes; its gcs_uri names the object that holds them, which on a lane where the smoke has run is acme/smoke_note.md. The claim is per version, not per name: that is the record this whole step is about.

Operation: bash — run in the operator shell (both read-only).

Expected shape, not a promised result:

```text
2026-09-22T11:58:07.412Z  ingest_duplicate  acme_111510fcf0a6ce7c...
the demo bytes' claim, acme_111510fcf0a6...: {'status': 'indexed', 'gcs_uri': 'gs://documind-ai-YOUR-ID-uploads/acme/smoke_note.md', 'chunks': 3, 'generation': '1758...'}
```

### demo_04_inspect_firestore_the_claim_the_rows_the_ledger_row_the_fingerprint.py

Read all four, Rs 0

**`step_01_read_all_four_rs_0(session)` — Inspect Firestore: the claim, the rows, the ledger row, the fingerprint / Read all four, Rs 0**

Read all four, Rs 0

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
doc_key from the note's bytes: acme_9c41d0e2b7f5a1...
documents/: {'status': 'indexed', 'chunks': 3, 'reused': 0, 'embedded': 3, 'generation': '1758542671234567', 'tenant_id': 'acme'}
chunks/: 3 rows | current: 3 | staged: 0 | with expire_at: 0
  acme:9c41d0e2b7f5...#0  preamble  section=None hash=70501fc5957f vector=768 doc_type=unknown
  acme:9c41d0e2b7f5...#1  SM-01     section='SM-01 - The smoke lantern' hash=14adcf0a776b vector=768 doc_type=unknown
  acme:9c41d0e2b7f5...#2  SM-02     section='SM-02 - The ladder' hash=(yours) vector=768 doc_type=unknown
sources/acme~smoke_note_v1.md: {'status': 'indexed', 'chunks': 3, 'reused': 0, 'embedded': 3, 'retired': 0, 'effective_from': None} | doc_key matches: True | sha256 matches: True
ledger/acme: {'fingerprint': '9b1d5e7a3c2f4680', 'versions': N, 'last_event': 'ingest_ok'}
```

### demo_05_inspect_vector_search_the_datapoint_its_restricts_and_a_search_for_itself.py

Three things exist: the index, the endpoint, and the deployed index that joins them and is the one that costs money per hour. The kit's make vector-status runs commands/vector-status.sh, which takes the two names from the shell (the variables you exported above) or, failing that, from Terraform's outputs; the two commands below are the same reads by hand. Read one datapoint back, then search for it

**`step_01_the_index_and_its_deployment_as_gcloud_see(session)` — Inspect Vector Search: the datapoint, its restricts, and a search for itself / The index and its deployment, as gcloud sees them**

Three things exist: the index, the endpoint, and the deployed index that joins them and is the one that costs money per hour. The kit's make vector-status runs commands/vector-status.sh, which takes the two names from the shell (the variables you exported above) or, failing that, from Terraform's outputs; the two commands below are the same reads by hand.

Operation: bash — run in the operator shell.

Expected shape, not a promised result:

```text
displayName: documind-chunks
indexStats:
  shardsCount: 1
  vectorsCount: '1745'
indexUpdateMethod: STREAM_UPDATE
metadata:
  config:
    dimensions: 768
    distanceMeasureType: DOT_PRODUCT_DISTANCE
displayName: documind-endpoint
deployedIndexes:
- dedicatedResources:
    machineSpec:
      machineType: e2-standard-2
  id: documind_chunks_v1
  indexSyncTime: '2026-09-22T10:41:07.000Z'
```

**`step_02_read_one_datapoint_back_then_search_for_it(session)` — Inspect Vector Search: the datapoint, its restricts, and a search for itself / Read one datapoint back, then search for it**

Read one datapoint back, then search for it

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
datapoint acme:9c41d0e2b7f5...#1: 768 numbers | same as the row's vector: True
restricts: [('tenant_id', ['acme']), ('kind', ['text']), ('doc_type', ['unknown']), ('current', ['true'])]
sparse dimensions: 24
  acme:9c41d0e2b7f5...#1  distance 1.0000   <- itself
  acme:9c41d0e2b7f5...#2  distance 0.7xxx
  acme:9c41d0e2b7f5...#0  distance 0.6xxx
```

### demo_06_inspect_the_mirror_and_the_audit_trail.py

Read the mirror rows, then the audit event

**`step_01_read_the_mirror_rows_then_the_audit_event(session)` — Inspect the mirror and the audit trail / Read the mirror rows, then the audit event**

Read the mirror rows, then the audit event

Operation: bash — run in the operator shell (two BigQuery queries, then one read from the audit bucket).

Expected shape, not a promised result:

```text
+--------------------------------------------------+---------------------------+------+----------+----------+----------+
|                     chunk_id                     |       heading_path        | kind | doc_type | pii_flag |    at    |
+--------------------------------------------------+---------------------------+------+----------+----------+----------+
| acme:9c41d0e2b7f5...#0                           | NULL                      | text | unknown  |    false | 10:39:52 |
| acme:9c41d0e2b7f5...#1                           | SM-01 - The smoke lantern | text | unknown  |    false | 10:39:52 |
| acme:9c41d0e2b7f5...#2                           | SM-02 - The ladder        | text | unknown  |    false | 10:39:52 |
+--------------------------------------------------+---------------------------+------+----------+----------+----------+
+-----------+-----------+
| rows_ever | documents |
+-----------+-----------+
|      2031 |         9 |
+-----------+-----------+
{
 "id": "3d6d8a5e-...",
 "ts": "2026-09-22T10:39:53.412Z",
 "action": "doc.upload",
 "actor": {"tenant_id": "acme", "email": "system:ingest"},
 "target": {"type": "document", "id": "acme_9c41d0e2b7f5...", "tenant_id": "acme"},
 "meta": {"gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/smoke_note_v1.md", "pages": 1, "chunks": 3, "pii": false, "kinds": ["text"], "reused": 0, "embedded": 3, "retired": 0}
}
```

### demo_07_verify_the_two_rungs_that_read_the_records.py

The first cell runs the Firestore rung's exact query with the note's own vector: itself first, at a cosine distance of zero. The second asks the API a question only the note can answer and prints which rung served it and how many of the pooled chunks came from the index. The kit ships two read-only commands for exactly this lesson. verify-vector-index.py reads Terraform's outputs and asks the API whether the index Terraform declared is the one attached to the endpoint, streaming, 768-dimensional, deployed exactly once; it needs a checkout with Terraform state, and the two gcloud reads in step 5 are the same checks by hand. check-firestore-fallback.py takes the handbook, proves the ledger row names the bytes in your checkout, and runs the Firestore rung with combined filters in both current modes; it imports the API's own modules, so it needs the API's packages in your venv. Both write their evidence under operator-evidence/. Their tests run offline in a fraction of a second.

**`step_01_the_fallback_rung_then_the_api(session)` — Verify: the two rungs that read the records / Do it: the fallback rung, then the API**

The first cell runs the Firestore rung's exact query with the note's own vector: itself first, at a cosine distance of zero. The second asks the API a question only the note can answer and prints which rung served it and how many of the pooled chunks came from the index.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
acme:9c41d0e2b7f5...#1  SM-01     cosine distance 0.0000   <- itself
  acme:9c41d0e2b7f5...#2  SM-02     cosine distance 0.2xxx
  acme:9c41d0e2b7f5...#0  preamble  cosine distance 0.3xxx
The smoke lantern is kept in bay 4 of the Pune warehouse and is checked on the first Monday of every month ... [Source 1]
[('1', 'smoke_note_v1.md'), ('2', 'smoke_note_v1.md')]
backend vector | pool 20 | from the index 20
```

**`step_02_the_operator_s_checks_two_commands_and_the(session)` — Verify: the two rungs that read the records / The operator's checks: two commands, and their tests**

The kit ships two read-only commands for exactly this lesson. verify-vector-index.py reads Terraform's outputs and asks the API whether the index Terraform declared is the one attached to the endpoint, streaming, 768-dimensional, deployed exactly once; it needs a checkout with Terraform state, and the two gcloud reads in step 5 are the same checks by hand. check-firestore-fallback.py takes the handbook, proves the ledger row names the bytes in your checkout, and runs the Firestore rung with combined filters in both current modes; it imports the API's own modules, so it needs the API's packages in your venv. Both write their evidence under operator-evidence/. Their tests run offline in a fraction of a second.

Operation: bash — run in the operator shell, in $DEMO_ROOT (all read-only).

Expected shape, not a promised result:

```text
Project: documind-ai-YOUR-ID (NUMBER)
Terraform index: projects/documind-ai-YOUR-ID/locations/asia-south1/indexes/1234567890123456789
Terraform endpoint: projects/documind-ai-YOUR-ID/locations/asia-south1/indexEndpoints/9876543210987654321
API index: projects/NUMBER/locations/asia-south1/indexes/1234567890123456789
API endpoint: projects/NUMBER/locations/asia-south1/indexEndpoints/9876543210987654321
Index dimensions: 768; update method: STREAM_UPDATE
Global vector count: 1745
Deployment: documind_chunks_v1
Deployment sync time: 2026-09-22T10:41:07.000Z
PASS: the expected index is attached to the expected endpoint.
This verifies attachment and configuration; ingestion and query checks are separate.
{"project": "documind-ai-YOUR-ID", "collection": "chunks", "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md", "source_status": "indexed", "source_doc_key": "acme_..."}
Verified HR source: 283 current chunks; stored doc_type='unknown'; manifest doc_type='policy'
NOTE: stored metadata differs from the manifest. This probe tests the stored equality filters; it does not certify policy classification or repair metadata.
PASS: combined doc_type='unknown'+kind='text', current=off, rows=5
PASS: combined doc_type='unknown'+kind='text', current=on, rows=5
PASS: both Firestore filter modes verified. Evidence: operator-evidence/firestore-combined-filters.json
Ran 8 tests in 0.005s
OK
Ran 11 tests in 0.006s
OK
```

### demo_08_repair_expire_and_what_the_records_cost.py

Firestore holds everything the index holds and more: the text, the vector, the stamps and the flags. So when the index and the rows disagree, the index is rebuilt from the rows, and nothing in the rows is ever derived from the index. backfill() reads every current row (of one tenant, or all), rebuilds each datapoint with the row's own vector, re-embeds only a row whose stamp fails the check from lesson 1.3, and checkpoints the repaired vector back on the row with optimistic concurrency so that a concurrent writer is never overwritten. Its plan is the count you saw in 1.3; APPLY=1 is the repair, and the two states it exists for are a worker deployed before the index existed and an apply that lost its index and succeeded on the second run.

**`step_01_the_rows_rebuild_the_tier(session)` — Repair, expire, and what the records cost / The rows rebuild the tier**

Firestore holds everything the index holds and more: the text, the vector, the stamps and the flags. So when the index and the rows disagree, the index is rebuilt from the rows, and nothing in the rows is ever derived from the index. backfill() reads every current row (of one tenant, or all), rebuilds each datapoint with the row's own vector, re-embeds only a row whose stamp fails the check from lesson 1.3, and checkpoints the repaired vector back on the row with optimistic concurrency so that a concurrent writer is never overwritten. Its plan is the count you saw in 1.3; APPLY=1 is the repair, and the two states it exists for are a worker deployed before the index existed and an apply that lost its index and succeeded on the second run.

Operation: bash — the plan (read-only) and the repair (writes to the tier; run it only when the plan is not zero).

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_1.4_Indexed_Records_WIX.html`. All 46 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `25ca420f96d82cacd1aeaffd37bdfde92039ecbe`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
