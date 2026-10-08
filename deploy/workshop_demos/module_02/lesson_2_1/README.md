# Lesson 2.1: Apply query embeddings and authorized filters

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_question_s_vector_direct_candidates_and_api_citations.py](demo_03_the_question_s_vector_direct_candidates_and_api_citations.py) | The question's vector: direct candidates and API citations |
| 4 | [demo_04_authorized_the_tenant_comes_from_identity_and_one_index_serves_three.py](demo_04_authorized_the_tenant_comes_from_identity_and_one_index_serves_three.py) | Authorized: the tenant comes from identity, and one index serves three |
| 5 | [demo_05_filters_two_keys_a_400_for_everything_else.py](demo_05_filters_two_keys_a_400_for_everything_else.py) | Filters: two keys, a 400 for everything else |
| 6 | [demo_06_the_restricts_the_per_request_backend_and_the_stages_block.py](demo_06_the_restricts_the_per_request_backend_and_the_stages_block.py) | The restricts, the per-request backend, and the stages block |
| 7 | [demo_07_current_is_the_ledger_s_filter_never_the_caller_s.py](demo_07_current_is_the_ledger_s_filter_never_the_caller_s.py) | Current is the ledger's filter, never the caller's |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The intended Terraform state/index deployment; preflight rejects empty or mismatched endpoint IDs.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Conditional recovery

- [recovery/setup_before_you_run_anything_set_up_the_shell.py](recovery/setup_before_you_run_anything_set_up_the_shell.py) — Continue only after PASS. Keep Acme on vector through steps 3–9. The API environment's RETRIEVAL_BACKEND is a default; the tenant pin overrides it. If step 3 still reports the old backend, wait for that one-minute cache to expire, then retry. This is a configuration repair for an existing index, not an index-creation step. Read the ID from the intended Terraform state and prove that it is deployed on the same endpoint. The following block refuses an endpoint mismatch or missing deployment. It creates a corrected API revision and routes 100% of the demo service's traffic to it. Other environment variables are retained; do not rerun the full infrastructure deployment to fix this one setting.

## Finish and restore

- [cleanup/demo_09_verify_it_yourself_the_checklist.py](cleanup/demo_09_verify_it_yourself_the_checklist.py) — At lesson end: Run only after steps 3–9. Restore the value saved before the demo, which may be rag_engine, another backend or default. The last option removes the explicit pin. Do not assume every lane originally used RAG Engine, and do not place this command beside the setup command.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

Run in $DEMO_ROOT. This reads the single revision receiving traffic, checks that its deployed ID exists, saves only the relevant settings under operator-evidence/lesson51/, and then selects vector for Acme. Empty optional settings take their code defaults. It stops before any embedding or tenant change if the deployment is invalid. A split-traffic service needs a chosen revision before this single-revision demonstration can proceed.

**`step_01_run_first_check_the_serving_revision_and_s(session)` — Before you run anything: set up the shell / Run first: check the serving revision and save the original pin**

Run in $DEMO_ROOT. This reads the single revision receiving traffic, checks that its deployed ID exists, saves only the relevant settings under operator-evidence/lesson51/, and then selects vector for Acme. Empty optional settings take their code defaults. It stops before any embedding or tenant change if the deployment is invalid. A split-traffic service needs a chosen revision before this single-revision demonstration can proceed.

Operation: bash — run before step 3; reads configuration and saves/sets the Acme pin.

### recovery/setup_before_you_run_anything_set_up_the_shell.py

Continue only after PASS. Keep Acme on vector through steps 3–9. The API environment's RETRIEVAL_BACKEND is a default; the tenant pin overrides it. If step 3 still reports the old backend, wait for that one-minute cache to expire, then retry. This is a configuration repair for an existing index, not an index-creation step. Read the ID from the intended Terraform state and prove that it is deployed on the same endpoint. The following block refuses an endpoint mismatch or missing deployment. It creates a corrected API revision and routes 100% of the demo service's traffic to it. Other environment variables are retained; do not rerun the full infrastructure deployment to fix this one setting.

**`step_01_run_first_check_the_serving_revision_and_s(session)` — Before you run anything: set up the shell / Run first: check the serving revision and save the original pin**

Continue only after PASS. Keep Acme on vector through steps 3–9. The API environment's RETRIEVAL_BACKEND is a default; the tenant pin overrides it. If step 3 still reports the old backend, wait for that one-minute cache to expire, then retry. This is a configuration repair for an existing index, not an index-creation step. Read the ID from the intended Terraform state and prove that it is deployed on the same endpoint. The following block refuses an endpoint mismatch or missing deployment. It creates a corrected API revision and routes 100% of the demo service's traffic to it. Other environment variables are retained; do not rerun the full infrastructure deployment to fix this one setting.

Operation: bash — optional repair; updates the API revision and its traffic.

### demo_03_the_question_s_vector_direct_candidates_and_api_citations.py

Run the preflight first. This cell uses its verified settings, checks the endpoint and Acme pin again before paying for an embedding, searches with the same tenant/current restricts, then compares candidate IDs with the API citations. Overlap and first-citation order are observations, not pass/fail assertions. Hybrid retrieval, graph candidates, current-version checks and reranking can change the final selection.

**`step_01_embed_search_compare(session)` — The question's vector: direct candidates and API citations / Do it: embed, search, compare**

Run the preflight first. This cell uses its verified settings, checks the endpoint and Acme pin again before paying for an embedding, searches with the same tenant/current restricts, then compares candidate IDs with the API citations. Overlap and first-citation order are observations, not pass/fail assertions. Hybrid retrieval, graph candidates, current-version checks and reranking can change the final selection.

Operation: bash — run in the operator shell (a Python cell, then one question; a paid embedding of a few hundred characters).

Expected shape, not a promised result:

```text
Actual deployed ID: the ID verified during preflight
Direct dense candidates: non-empty for the loaded handbook
stages.retrieval_backend: vector
vector_chunks: greater than 0
PASS: the direct search worked and Vector Search contributed to the API pool.
```

### demo_04_authorized_the_tenant_comes_from_identity_and_one_index_serves_three.py

The UI's service account, which your tok() impersonates, sits on all three rosters. The first two calls send it the same question against acme and zeta; the third sends the outsider's token; the fourth sends the UI's token with a header that claims to be someone else. Each line shows the HTTP status. A request turned away for a reason that passes, a model quota hit, a Cloud Run scale-up or a dropped connection, is asked once more after five seconds; anything else prints the reason the service gave instead of a traceback.

**`step_01_one_identity_two_tenants_one_outsider(session)` — Authorized: the tenant comes from identity, and one index serves three / Do it: one identity, two tenants, one outsider**

The UI's service account, which your tok() impersonates, sits on all three rosters. The first two calls send it the same question against acme and zeta; the third sends the outsider's token; the fourth sends the UI's token with a header that claims to be someone else. Each line shows the HTTP status. A request turned away for a reason that passes, a model quota hit, a Cloud Run scale-up or a dropped connection, is asked once more after five seconds; anything else prints the reason the service gave instead of a traceback.

Operation: bash — run in the operator shell (a Python cell; two answered questions, two refusals; paise).

Expected shape, not a promised result:

```text
acme: HTTP 200 | The per-trip cap on domestic travel reimbursement is Rs 40,000. | ['hr_policy_2026.md']
zeta: HTTP 200 | The per-trip cap on domestic travel reimbursement is Rs 25,000 against | ['hr_policy_zeta_2026.md']
outsider on acme: HTTP 403 | not a member of this tenant
ui-sa with a false header on zeta: HTTP 200 | The per-trip cap on domestic travel reimbursement | the header changed nothing
```

### demo_05_filters_two_keys_a_400_for_everything_else.py

Do it: four filters, four verdicts

**`step_01_four_filters_four_verdicts(session)` — Filters: two keys, a 400 for everything else / Do it: four filters, four verdicts**

Do it: four filters, four verdicts

Operation: bash — run in the operator shell (two 400s cost nothing; two questions, paise).

Expected shape, not a promised result:

```text
400 | unknown filter key(s) tenant_id; allowed: doc_type, kind
400 | filter doc_type must be a non-empty string or a list of 1 to 5 of them
200 | answerable False pool 0 | The corpus holds nothing near this question: no passage of this
200 | answerable True pool 20 | A confirmed employee at grade E3 or above serves a notice period
```

### demo_06_the_restricts_the_per_request_backend_and_the_stages_block.py

Do it: the tenant's pin and policy, then a full stages block, Rs 0 plus one question

**`step_01_the_tenant_s_pin_and_policy_then_a_full_st(session)` — The restricts, the per-request backend, and the stages block / Do it: the tenant's pin and policy, then a full stages block, Rs 0 plus one question**

Do it: the tenant's pin and policy, then a full stages block, Rs 0 plus one question

Operation: bash — run in the operator shell, in $DEMO_ROOT (two reads, one question).

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
acme: data_region=any
{
 "policy_fallback": 0,
 "retrieval_backend": "vector",
 "retrieve_ms": 612,
 "pool": 20,
 "graph_chunks": 0,
 "managed_chunks": 0,
 "vector_chunks": 20,
 "rerank_ms": 388,
 "generate_ms": 1742
}
citations 3 | cache_hit none | latency_ms 2760
```

### demo_07_current_is_the_ledger_s_filter_never_the_caller_s.py

Do it: the question the revisions answered differently

**`step_01_the_question_the_revisions_answered_differ(session)` — Current is the ledger's filter, never the caller's / Do it: the question the revisions answered differently**

Do it: the question the revisions answered differently

Operation: bash — run in the operator shell (one question, then the cited row read off Firestore).

Expected shape, not a promised result:

```text
A confirmed employee at grade E3 or above serves a notice period of 60 days ... [Source 1]
cited acme:497809ffbaa6...#1
the cited row: NP-03 | current: True | doc_key: acme_497809ff... | text starts: NP-03 — Notice period A confirmed employee at grade E3 or above
NP-03 rows on the lane: 3 | current: 1 | saying 90 days: 2 (retired, never cited)
```

### cleanup/demo_09_verify_it_yourself_the_checklist.py

At lesson end: Run only after steps 3–9. Restore the value saved before the demo, which may be rag_engine, another backend or default. The last option removes the explicit pin. Do not assume every lane originally used RAG Engine, and do not place this command beside the setup command.

**`step_01_finish_restore_the_saved_tenant_pin(session)` — Verify it yourself: the checklist / Finish: restore the saved tenant pin**

Run only after steps 3–9. Restore the value saved before the demo, which may be rag_engine, another backend or default. The last option removes the explicit pin. Do not assume every lane originally used RAG Engine, and do not place this command beside the setup command.

Operation: bash — end of lesson only; restore the original Acme pin.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_2.1_Query_Filters_WIX.html`. All 29 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `eec99fabc474ce0ab221815772043a8d9d45a33f`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
