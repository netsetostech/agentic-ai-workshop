# Lesson 2.4: Test fallback without losing tenant or metadata filters

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_firestore_rung_by_hand_the_api_s_three_predicates_on_firestore_s_own_vector.py](demo_03_the_firestore_rung_by_hand_the_api_s_three_predicates_on_firestore_s_own_vector.py) | The Firestore rung by hand: the API's three predicates on Firestore's own vector index |
| 4 | [demo_04_moving_one_tenant_beneath_the_index_by_hand_and_back.py](demo_04_moving_one_tenant_beneath_the_index_by_hand_and_back.py) | Moving one tenant beneath the index by hand, and back |
| 5 | [demo_05_the_chaos_rung_an_index_that_will_not_answer_on_a_candidate_that_takes_no_traffi.py](demo_05_the_chaos_rung_an_index_that_will_not_answer_on_a_candidate_that_takes_no_traffi.py) | The chaos rung: an index that will not answer, on a candidate that takes no traffic |
| 6 | [demo_06_the_probe_the_kit_s_read_only_check_of_the_combined_filters.py](demo_06_the_probe_the_kit_s_read_only_check_of_the_combined_filters.py) | The probe: the kit's read-only check of the combined filters |
| 7 | [demo_07_the_tier_from_the_rows_vector_status_backfill_vectors_and_the_rows_that_count_th.py](demo_07_the_tier_from_the_rows_vector_status_backfill_vectors_and_the_rows_that_count_th.py) | The tier from the rows: vector-status, backfill-vectors, and the rows that count the rung |
| 8 | [demo_08_what_the_rung_costs_where_it_cannot_go_and_the_policy_that_sends_a_tenant_home.py](demo_08_what_the_rung_costs_where_it_cannot_go_and_the_policy_that_sends_a_tenant_home.py) | What the rung costs, where it cannot go, and the policy that sends a tenant home |

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The index names and the retrieval settings live in the API's environment; a name the service does not set is unset rather than exported empty, because the kit's settings class reads an empty variable as a value, and steps 5 and 6 import the kit. The pins live in Firestore, one document per tenant, and the lane helper prints them.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine. Temporarily disable an enabled answer cache for this retrieval/generation experiment and save its prior value. This changes the shared API; finish restores it. Cache lessons in Module 6 are unaffected.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The index names and the retrieval settings live in the API's environment; a name the service does not set is unset rather than exported empty, because the kit's settings class reads an empty variable as a value, and steps 5 and 6 import the kit. The pins live in Firestore, one document per tenant, and the lane helper prints them.

Operation: bash — run in the operator shell, in $DEMO_ROOT, once per shell.

IDE adaptation: Read literal environment values as JSON from the serving revision; absent keys are unset. Repeated text parsing is removed.

Expected shape, not a promised result:

```text
endpoint: projects/documind-ai-YOUR-ID/locations/asia-south1/indexEndpoints/9876543210987654321  deployed: documind_chunks_v1
backend: vector  mode: dense (default)  current_only: off (default)  top_k_retrieve: 20 (default)
acme: retrieval_backend=vector
zeta: retrieval_backend=default (the deployment RETRIEVAL_BACKEND)
acme: data_region=any
```

### demo_03_the_firestore_rung_by_hand_the_api_s_three_predicates_on_firestore_s_own_vector.py

Run the cell as it is, then twice more with a filter in front of its first line: F='{"doc_type":"policy"}' python - <<'PY' and F='{"kind":"text"}' python - <<'PY', the rest unchanged. The worker stamped the lane's uploads doc_type: unknown, so the first filter empties the pool on this rung exactly as it did on the index in lesson 2.1, and the second keeps it whole.

**`step_01_the_rung_under_three_predicate_sets(session)` — The Firestore rung by hand: the API's three predicates on Firestore's own vector index / Do it: the rung under three predicate sets**

Run the cell as it is, then twice more with a filter in front of its first line: F='{"doc_type":"policy"}' python - <<'PY' and F='{"kind":"text"}' python - <<'PY', the rest unchanged. The worker stamped the lane's uploads doc_type: unknown, so the first filter empties the pool on this rung exactly as it did on the index in lesson 2.1, and the second keeps it whole.

Operation: bash — run in the operator shell (a Python cell; one embedding, a few dozen Firestore reads).

Expected shape, not a promised result:

```text
predicates: tenant_id -> 20 rows, every one found_by firestore
   NP-03     hr_policy_2026.md          doc_type unknown  kind text   current True  score 0.7xxx
   ...
index needed: (tenant_id, embedding) | reads billed, at most: 1x for 1xxx index entries + 20 documents

predicates: tenant_id, doc_type (doc_type=policy) -> 0 rows, every one found_by firestore
index needed: (tenant_id, doc_type, embedding) | reads billed, at most: 1x for 1xxx index entries + 0 documents

predicates: tenant_id, kind (kind=text) -> 20 rows, every one found_by firestore
   NP-03     hr_policy_2026.md          doc_type unknown  kind text   current True  score 0.7xxx
   ...
index needed: (tenant_id, kind, embedding) | reads billed, at most: 1x for 1xxx index entries + 20 documents
```

### demo_04_moving_one_tenant_beneath_the_index_by_hand_and_back.py

Do it: pin acme beneath the index, and wait for the API to notice Do it: the same predicates on the chosen rung, and two tenants that do not cross Do it: the smoke's line for a chosen rung, then the pin back

**`step_01_pin_acme_beneath_the_index_and_wait_for_th(session)` — Moving one tenant beneath the index by hand, and back / Do it: pin acme beneath the index, and wait for the API to notice**

Do it: pin acme beneath the index, and wait for the API to notice

Operation: bash — run in the operator shell, in $DEMO_ROOT (one field written; up to nine questions while the minute passes).

Expected shape, not a promised result:

```text
acme: retrieval_backend=firestore
backend vector | vector_chunks 20 | pool 20 | retrieve_ms 6xx | answerable True | first 1 hr_policy_2026.md | A confirmed employee in grade E3 ...
backend firestore | vector_chunks 0 | pool 20 | retrieve_ms 5xx | answerable True | first 1 hr_policy_2026.md | A confirmed employee in grade E3 ...
```

**`step_02_the_same_predicates_on_the_chosen_rung_and(session)` — Moving one tenant beneath the index by hand, and back / Do it: the same predicates on the chosen rung, and two tenants that do not cross**

Do it: the same predicates on the chosen rung, and two tenants that do not cross

Operation: bash — run in the operator shell (four questions, a few rupees).

Expected shape, not a promised result:

```text
backend firestore | vector_chunks 0 | pool 0 | retrieve_ms 4xx | answerable False | first - | The corpus holds nothing near this question: no passage of this
backend firestore | vector_chunks 0 | pool 20 | retrieve_ms 5xx | answerable True | first 1 hr_policy_2026.md | A confirmed employee in grade E3 ...
backend firestore | vector_chunks 0 | pool 20 | retrieve_ms 5xx | answerable True | first x hr_policy_2026.md | ... Rs 40,000 ...
backend vector | vector_chunks 20 | pool 20 | retrieve_ms 6xx | answerable True | first x hr_policy_zeta_2026.md | ... Rs 25,000 ...
```

**`step_03_the_smoke_s_line_for_a_chosen_rung_then_th(session)` — Moving one tenant beneath the index by hand, and back / Do it: the smoke's line for a chosen rung, then the pin back**

Do it: the smoke's line for a chosen rung, then the pin back

Operation: bash — run in the operator shell, in $DEMO_ROOT (two smokes, a rupee each; one field written).

IDE adaptation: Run with the page's pipeline status (no pipefail). The cell filters make smoke for the lines this lesson reads; a check failing elsewhere in the smoke shows in those lines instead of stopping the cell before its later lines.

Expected shape, not a promised result:

```text
[ -- ] vector tier  this request ran on firestore — skipped
acme: retrieval_backend=vector
backend vector | vector_chunks 20 | pool 20 | retrieve_ms 6xx | answerable True | first 1 hr_policy_2026.md | A confirmed employee in grade E3 ...
  [PASS] vector tier  20 of 20 chunks came from the index
```

### demo_05_the_chaos_rung_an_index_that_will_not_answer_on_a_candidate_that_takes_no_traffi.py

Do it: a candidate that cannot reach the index

**`step_01_a_candidate_that_cannot_reach_the_index(session)` — The chaos rung: an index that will not answer, on a candidate that takes no traffic / Do it: a candidate that cannot reach the index**

Do it: a candidate that cannot reach the index

Operation: bash — run in the operator shell (one new revision, no traffic; one question to it; one log read; ask() from step 4).

Expected shape, not a promised result:

```text
candidate: backend vector | vector_chunks 0 | pool 20 | answerable True | citations 3
the smoke would say: [FAIL] vector tier  RETRIEVAL_BACKEND=vector and no chunk came from the index - the Firestore rung answered. make vector-status; make backfill-vectors APPLY=1
2026-09-2xT1x:xx:xx.xxxxxxZ	acme	... documind_chunks_nonesuch ...
```

**`step_02_a_candidate_that_cannot_reach_the_index(session)` — The chaos rung: an index that will not answer, on a candidate that takes no traffic / Do it: a candidate that cannot reach the index**

Do it: a candidate that cannot reach the index

Operation: bash — run in the operator shell (the undo: the real name back on the template, the tag dropped, the live service asked once).

Expected shape, not a promised result:

```text
template now: documind_chunks_v1
backend vector | vector_chunks 20 | pool 20 | retrieve_ms 6xx | answerable True | first 1 hr_policy_2026.md | A confirmed employee in grade E3 ...
100;documind-api-00048-xyz
```

### demo_06_the_probe_the_kit_s_read_only_check_of_the_combined_filters.py

Do it: the probe, then its evidence

**`step_01_the_probe_then_its_evidence(session)` — The probe: the kit's read-only check of the combined filters / Do it: the probe, then its evidence**

Do it: the probe, then its evidence

Operation: bash — run in the operator shell, in $DEMO_ROOT (one embedding read off a row, a few dozen Firestore reads; nothing written to the cloud).

Expected shape, not a promised result:

```text
{"project": "documind-ai-YOUR-ID", "collection": "chunks", "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md", "source_status": "indexed", "source_doc_key": "acme_497809ff..."}
Verified HR source: 283 current chunks; stored doc_type='unknown'; manifest doc_type='policy'
NOTE: stored metadata differs from the manifest. This probe tests the stored equality filters; it does not certify policy classification or repair metadata.
PASS: combined doc_type='unknown'+kind='text', current=off, rows=5
PASS: combined doc_type='unknown'+kind='text', current=on, rows=5
PASS: both Firestore filter modes verified. Evidence: operator-evidence/firestore-combined-filters.json
evidence: {'doc_type': 'unknown', 'kind': 'text'} | current off: 5 rows | current on: 5 rows | doc_key acme_497809ff...
```

### demo_07_the_tier_from_the_rows_vector_status_backfill_vectors_and_the_rows_that_count_th.py

Do it: count the tier, plan its refill, read the rows by rung, Rs 0

**`step_01_count_the_tier_plan_its_refill_read_the_ro(session)` — The tier from the rows: vector-status, backfill-vectors, and the rows that count the rung / Do it: count the tier, plan its refill, read the rows by rung, Rs 0**

Do it: count the tier, plan its refill, read the rows by rung, Rs 0

Operation: bash — run in the operator shell, in $DEMO_ROOT (read-only: the plan writes nothing without --apply).

Expected shape, not a promised result:

```text
index: documind-chunks  datapoints: 4xxx  shards: 1  update: STREAM_UPDATE
endpoint: documind-endpoint  deployed: documind_chunks_v1  synced: 2026-09-2xT1x:xx:xx.xxxxxxZ
{"event": "backfill_vectors_plan", "index": "projects/NUMBER/locations/asia-south1/indexes/1234567890123456789", "tenant": "acme", "current_chunks": 1xxx, "needs_document_embedding": 0, "invalid_chunks": 0, "embedding_task_type": "RETRIEVAL_DOCUMENT", "note": "Pause uploads/undo/batch writers; keep answer caches off during repair and validation."}

by retrieval backend (which store served the pool; 13 September 2026)
retrieval_backend      answers    tok_in  tok_out       USD       INR  p95 ms  unans
------------------------------------------------------------------------------------
firestore                    5      xxxx      xxx    0.0xxx      x.xx    2xxx   0.20
vector                       6      xxxx      xxx    0.0xxx      x.xx    2xxx   0.00
```

### demo_08_what_the_rung_costs_where_it_cannot_go_and_the_policy_that_sends_a_tenant_home.py

A tenant's data_region says where its text may be held: any lets the managed mirror copy its current versions abroad, in keeps it on the kit's rows in India, and a missing or unknown value is in, because an unreadable policy is the strict one. retrieval_backend_for() holds every request's backend against it: a managed pin for an in tenant is served from the kit's own rung instead, the deployment's if that is vector or firestore, otherwise Firestore, with policy_fallback 1 on the row, which the warehouse sums into a column. The cell runs the two pure functions behind that decision offline; nothing leaves the machine.

**`step_01_the_policy_that_sends_a_tenant_home(session)` — What the rung costs, where it cannot go, and the policy that sends a tenant home / The policy that sends a tenant home**

A tenant's data_region says where its text may be held: any lets the managed mirror copy its current versions abroad, in keeps it on the kit's rows in India, and a missing or unknown value is in, because an unreadable policy is the strict one. retrieval_backend_for() holds every request's backend against it: a managed pin for an in tenant is served from the kit's own rung instead, the deployment's if that is vector or firestore, otherwise Firestore, with policy_fallback 1 on the row, which the warehouse sums into a column. The cell runs the two pure functions behind that decision offline; nothing leaves the machine.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0).

Expected shape, not a promised result:

```text
{}                       -> policy in
{'data_region': 'any'}   -> policy any
{'data_region': 'in'}    -> policy in
{'data_region': 'eu'}    -> policy in
in   tenant, a store in asia-south1  -> may hold it
in   tenant, a store in us-central1  -> may not
in   tenant, a store in global       -> may not
any  tenant, a store in us-central1  -> may hold it
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs. Restore the saved answer-cache value and tenant backend, including after a failed experiment.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_2.4_Fallback_WIX.html`. All 43 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `fc9115e7693b7a3af4ab9f5c5711b8b67aea351b`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
