# Lesson 2.2: Compare dense and hybrid retrieval

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_lane_runs_dense_and_two_sparse_rulers_over_its_own_rows.py](demo_03_the_lane_runs_dense_and_two_sparse_rulers_over_its_own_rows.py) | The lane runs dense, and two sparse rulers over its own rows |
| 4 | [demo_04_three_ways_through_the_index_dense_sparse_only_fused.py](demo_04_three_ways_through_the_index_dense_sparse_only_fused.py) | Three ways through the index: dense, sparse only, fused |
| 5 | [demo_05_rrf_by_hand_the_kit_s_rule_reproduces_the_server_s_order.py](demo_05_rrf_by_hand_the_kit_s_rule_reproduces_the_server_s_order.py) | RRF by hand: the kit's rule reproduces the server's order |
| 6 | [demo_06_the_ablation_one_knob_per_arm_no_model_in_the_loop.py](demo_06_the_ablation_one_knob_per_arm_no_model_in_the_loop.py) | The ablation: one knob per arm, no model in the loop |
| 7 | [demo_07_the_knob_hybrid_on_a_candidate_that_takes_no_traffic_compared_then_removed.py](demo_07_the_knob_hybrid_on_a_candidate_that_takes_no_traffic_compared_then_removed.py) | The knob: hybrid on a candidate that takes no traffic, compared, then removed |
| 8 | [demo_08_what_hybrid_costs_where_it_cannot_go_and_what_the_harness_does_not_measure.py](demo_08_what_hybrid_costs_where_it_cannot_go_and_what_the_harness_does_not_measure.py) | What hybrid costs, where it cannot go, and what the harness does not measure |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Loaded invoice and HR fixtures, a hybrid-capable index, and the API's actual serving configuration.

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The index endpoint, the deployed index and the retrieval settings live in the API's environment; steps 3, 4 and 7 use them. An empty value means the setting's default, which the page names where it matters; a name the service does not set is unset rather than exported empty, because the kit's settings class reads an empty variable as a value, and step 8's cell imports the kit. The ablation's sparse leg needs rank_bm25, which the kit's images do not carry because no service runs it; the pip line puts it in the venv once.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine. Temporarily disable an enabled answer cache for this retrieval/generation experiment and save its prior value. This changes the shared API; finish restores it. Cache lessons in Module 6 are unaffected.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The index endpoint, the deployed index and the retrieval settings live in the API's environment; steps 3, 4 and 7 use them. An empty value means the setting's default, which the page names where it matters; a name the service does not set is unset rather than exported empty, because the kit's settings class reads an empty variable as a value, and step 8's cell imports the kit. The ablation's sparse leg needs rank_bm25, which the kit's images do not carry because no service runs it; the pip line puts it in the venv once.

Operation: bash — run in the operator shell, once per shell.

IDE adaptation: Read literal environment values as JSON from the serving revision; absent keys are unset. Repeated text parsing is removed.

Expected shape, not a promised result:

```text
endpoint: projects/documind-ai-YOUR-ID/locations/asia-south1/indexEndpoints/9876543210987654321  deployed: documind_chunks_v1
mode: dense (default)  backend: vector
```

### demo_03_the_lane_runs_dense_and_two_sparse_rulers_over_its_own_rows.py

The cell reads the text of every current acme row, no vectors, and scores each row twice for the invoice question; then run it again for the notice-period clause. Firestore reads of this size sit inside the free quota.

**`step_01_both_rulers_over_your_rows_rs_0(session)` — The lane runs dense, and two sparse rulers over its own rows / Do it: both rulers over your rows, Rs 0**

The cell reads the text of every current acme row, no vectors, and scores each row twice for the invoice question; then run it again for the notice-period clause. Firestore reads of this size sit inside the free quota.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell, then the same cell for a second question).

Expected shape, not a promised result:

```text
N current acme rows read, text only

index leg, hashed TF by dot product: anchor inv_2026_0412 at rank 9xx of N
   p28-1      industrial_relations_code_2020.pdf     35.500
   p32-0      cgst_act_2017.pdf                      34.000
   p7-0       payment_of_gratuity_act_1972.pdf       32.000

ablation leg, BM25: anchor inv_2026_0412 at rank 1 of N
   p1-0       inv_2026_0412.md                       21.949   <- anchor
   p36-0      cgst_act_2017.pdf                      16.609
   p40-0      cgst_act_2017.pdf                      16.514
```

### demo_04_three_ways_through_the_index_dense_sparse_only_fused.py

Do it: dense, alpha 0, alpha 0.7

**`step_01_dense_alpha_0_alpha_0_7(session)` — Three ways through the index: dense, sparse only, fused / Do it: dense, alpha 0, alpha 0.7**

Do it: dense, alpha 0, alpha 0.7

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; one paid embedding of a few dozen characters).

Expected shape, not a promised result:

```text
dense  first five (anchor at rank 1 of 20):
   w0         inv_2026_0412.md                     <- anchor
   p23-0      payment_of_bonus_act_1965.pdf
   ...

sparse first five (anchor at rank None of 20):
   p28-1      industrial_relations_code_2020.pdf
   p7-0       payment_of_gratuity_act_1972.pdf
   ...

hybrid first five (anchor at rank 1 of 20):
   w0         inv_2026_0412.md                     <- anchor
   p23-0      payment_of_bonus_act_1965.pdf
   ...

overlap of 20: dense/hybrid 20 | dense/sparse 0
saved /tmp/legs52.json for step 5
```

### demo_05_rrf_by_hand_the_kit_s_rule_reproduces_the_server_s_order.py

Do it: fuse the saved lists, compare with the index's fused list

**`step_01_fuse_the_saved_lists_compare_with_the_inde(session)` — RRF by hand: the kit's rule reproduces the server's order / Do it: fuse the saved lists, compare with the index's fused list**

Do it: fuse the saved lists, compare with the index's fused list

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: the lists are on disk).

Expected shape, not a promised result:

```text
the legs differ: True | shared of 20: 0
by hand, alpha 0.7:
   w0 inv_2026_0412.md                  0.01148   dense rank  1  sparse rank  -
   p23-0 payment_of_bonus_act_1         0.01129   dense rank  2  sparse rank  -
   ...
the index's fused first five: ['w0 inv_2026_0412.md', 'p23-0 payment_of_bonus_act_1', ...]
heads agree on 5 of 5 | first is the same: True
all twenty in the index's order: True
alpha 1.0 gives the dense list back: True
alpha 0.0 gives the sparse list back: True
the bound: dense #1 0.01148, dense #20 0.00875, sparse #1 alone 0.00492
```

### demo_06_the_ablation_one_knob_per_arm_no_model_in_the_loop.py

The first run takes five rows and about a minute; the second takes acme's 40 rows and a few minutes, and appends one JSON line per arm to a ledger you keep. make ablate passes your exported REGION as the embedding region, which is where the API embeds; the direct call is the same line without make.

**`step_01_a_wiring_check_then_acme_s_rows_with_a_led(session)` — The ablation: one knob per arm, no model in the loop / Do it: a wiring check, then acme's rows with a ledger**

The first run takes five rows and about a minute; the second takes acme's 40 rows and a few minutes, and appends one JSON line per arm to a ledger you keep. make ablate passes your exported REGION as the embedding region, which is where the API embeds; the direct call is the same line without make.

Operation: bash — run in the operator shell, in $DEMO_ROOT (embeddings in paise; the Ranking API per request, a few rupees).

Expected shape, not a promised result:

```text
40 rows with anchors, NN anchors, one knob per arm (project documind-ai-YOUR-ID, embeddings in asia-south1, ranker on global)

arm                                          recall@depth  recall@5    mrr rows@1.0  p95 ms
dense 5, no reranker                                 0.9x      0.9x   0.8x       3x    xxxx
dense 20 -> rerank 5   (the lane)                    0.9x      0.9x   0.9x       3x    xxxx
       lost: lk-xx: PB-02 - ranked out (in the candidates, not the five)
dense 50 -> rerank 5                                 0.9x      0.9x   0.9x       3x    xxxx
hybrid 20 -> rerank 5  (4.5, not wired)              0.9x      0.9x   0.9x       3x    xxxx

Read it in this order: recall@depth is the reranker's ceiling - if the 20 and 50 rows agree, depth is not the knob;
recall@5 of the lane's row minus the first row is the reranker's lift, and p95 is what it costs;
the hybrid row says whether a BM25 leg is worth wiring - twenty of the anchors are clause codes, its home ground;
the rag_engine row (--arms all) is 4.3's corpus against the lane's own rows - a managed chunk that splits a clause from its code shows up as a miss.
```

### demo_07_the_knob_hybrid_on_a_candidate_that_takes_no_traffic_compared_then_removed.py

Do it: hybrid on a candidate, the same two questions to both revisions, then undo

**`step_01_hybrid_on_a_candidate_the_same_two_questio(session)` — The knob: hybrid on a candidate that takes no traffic, compared, then removed / Do it: hybrid on a candidate, the same two questions to both revisions, then undo**

Do it: hybrid on a candidate, the same two questions to both revisions, then undo

Operation: bash — run in the operator shell (one new revision, no traffic; two version reads).

Expected shape, not a promised result:

```text
documind-api-NUMBER                  mode dense | backend vector
candidate---documind-api-NUMBER      mode hybrid | backend vector
```

**`step_02_hybrid_on_a_candidate_the_same_two_questio(session)` — The knob: hybrid on a candidate that takes no traffic, compared, then removed / Do it: hybrid on a candidate, the same two questions to both revisions, then undo**

Do it: hybrid on a candidate, the same two questions to both revisions, then undo

Operation: bash — run in the operator shell (four questions, one or two rupees).

Expected shape, not a promised result:

```text
What is the total payable on invoice INV-2026-0412?
   documind-  ['  0 inv_2026_0412.md', ' 36 cgst_act_2017.pdf', ...] | retrieve_ms 6xx | pool 20 | vector_chunks 20
   candidate  ['  0 inv_2026_0412.md', ' 36 cgst_act_2017.pdf', ...] | retrieve_ms 7xx | pool 20 | vector_chunks 20
What is the notice period for a confirmed E3?
   documind-  ['  1 hr_policy_2026.md', '  4 hr_policy_2026.md', '  2 hr_policy_2026.md'] | retrieve_ms 6xx | pool 20 | vector_chunks 20
   candidate  ['  1 hr_policy_2026.md', '  4 hr_policy_2026.md', '  2 hr_policy_2026.md'] | retrieve_ms 7xx | pool 20 | vector_chunks 20
```

**`step_03_hybrid_on_a_candidate_the_same_two_questio(session)` — The knob: hybrid on a candidate that takes no traffic, compared, then removed / Do it: hybrid on a candidate, the same two questions to both revisions, then undo**

Do it: hybrid on a candidate, the same two questions to both revisions, then undo

Operation: bash — run in the operator shell (the undo: the variable removed, the tag dropped, the live mode read again).

Expected shape, not a promised result:

```text
live mode: dense
100;documind-api-00042-xyz
```

### demo_08_what_hybrid_costs_where_it_cannot_go_and_what_the_harness_does_not_measure.py

Two places, one at startup and one at runtime. A managed backend has no sparse leg to fuse and the Firestore rung's vector index takes one dense vector and nothing else, so check_retrieval_modes() refuses both pairs before the service serves; a tenant pinned to a managed store under hybrid mode is served from the deployment's backend with a retrieval_pin_ignored line instead. At runtime the chaos rung applies to hybrid as to dense: an unreachable index degrades to the Firestore rung, which is dense only, with a vector_search_fallback line and never a 500. The cell asks the validator the two questions offline.

**`step_01_where_hybrid_cannot_go(session)` — What hybrid costs, where it cannot go, and what the harness does not measure / Where hybrid cannot go**

Two places, one at startup and one at runtime. A managed backend has no sparse leg to fuse and the Firestore rung's vector index takes one dense vector and nothing else, so check_retrieval_modes() refuses both pairs before the service serves; a tenant pinned to a managed store under hybrid mode is served from the deployment's backend with a retrieval_pin_ignored line instead. At runtime the chaos rung applies to hybrid as to dense: an unreachable index degrades to the Firestore rung, which is dense only, with a vector_search_fallback line and never a 500. The cell asks the validator the two questions offline.

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: no call leaves the machine).

Expected shape, not a promised result:

```text
vector     hybrid -> allowed
firestore  hybrid -> refused: RETRIEVAL_MODE=hybrid needs RETRIEVAL_BACKEND=vector: the Firestore backend is dense-only. Set RETR...
rag_engine hybrid -> refused: RETRIEVAL_MODE=hybrid needs RETRIEVAL_BACKEND=vector: rag_engine embeds and searches on its own ...
firestore  dense  -> allowed
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_2.2_Hybrid_WIX.html`. All 40 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `e328b1eb4da48eab527de6f40bfc73967d53aefb`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
