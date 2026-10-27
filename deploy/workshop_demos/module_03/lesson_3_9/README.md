# Lesson 3.9: System design: a fact-checking system built from DocuMind's parts

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_architecture_the_path_a_claim_takes_station_by_station.py](demo_03_architecture_the_path_a_claim_takes_station_by_station.py) | Architecture: the path a claim takes, station by station |
| 4 | [demo_04_architecture_three_designs_rejected_and_the_number_that_would_change_each.py](demo_04_architecture_three_designs_rejected_and_the_number_that_would_change_each.py) | Architecture: three designs rejected, and the number that would change each |
| 5 | [demo_05_failure_modes_four_the_kit_reproduces_and_which_ones_the_alerts_see.py](demo_05_failure_modes_four_the_kit_reproduces_and_which_ones_the_alerts_see.py) | Failure modes: four the kit reproduces, and which ones the alerts see |
| 6 | [demo_06_cost_a_claim_a_month_and_a_floor_at_1k_10k_and_100k_claims.py](demo_06_cost_a_claim_a_month_and_a_floor_at_1k_10k_and_100k_claims.py) | Cost: a claim, a month and a floor, at 1k, 10k and 100k claims |
| 7 | [demo_07_cost_at_10_the_limits_the_kit_declares_and_the_one_it_does_not.py](demo_07_cost_at_10_the_limits_the_kit_declares_and_the_one_it_does_not.py) | Cost at 10×: the limits the kit declares, and the one it does not |
| 8 | [demo_08_evals_what_blocks_what_advises_and_what_cannot_fail.py](demo_08_evals_what_blocks_what_advises_and_what_cannot_fail.py) | Evals: what blocks, what advises, and what cannot fail |

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_architecture_the_path_a_claim_takes_station_by_station.py

The cell cuts the handbook with the kit's chunker, takes NP-03, the notice-period clause, and holds six quotes against it with quote_holds(): the sentence as written, a sentence that crosses a line break, the same sentence with revision 2's figure, a paraphrase, the whole clause, and the whole clause as _draft() trims an over-long quote. Each line prints both halves of the rule and the kit's verdict.

**`step_01_the_quote_check_on_the_handbook_offline(session)` — Architecture: the path a claim takes, station by station / Do it: the quote check on the handbook, offline**

The cell cuts the handbook with the kit's chunker, takes NP-03, the notice-period clause, and holds six quotes against it with quote_holds(): the sentence as written, a sentence that crosses a line break, the same sentence with revision 2's figure, a paraphrase, the whole clause, and the whole clause as _draft() trims an over-long quote. Each line prints both halves of the rule and the kit's verdict.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
NP-03: 212 characters, 38 words under its heading
the sentence as written         15 words | in the passage True  | 25 words at most True  | quote_holds True
across a line break             11 words | in the passage True  | 25 words at most True  | quote_holds True
revision 2's figure             15 words | in the passage False | 25 words at most True  | quote_holds False
a paraphrase                     9 words | in the passage False | 25 words at most True  | quote_holds False
the whole clause                38 words | in the passage True  | 25 words at most False | quote_holds False
the clause as _draft() trims it 36 words | in the passage False | 25 words at most False | quote_holds False
```

### demo_04_architecture_three_designs_rejected_and_the_number_that_would_change_each.py

The cell rebuilds a claim's budget with the kit's own function, reads the cache's floor and its read rate from the kit, measures each tenant's corpus with the kit's estimate, reads the policies make roster writes, and prices the judge on every claim. Four prices come from Google's pages, dated in the cell: the cache's storage, the embedding, the ranking query and the judge's default autorater.

**`step_01_the_three_thresholds_from_the_kit_s_files(session)` — Architecture: three designs rejected, and the number that would change each / Do it: the three thresholds, from the kit's files**

The cell rebuilds a claim's budget with the kit's own function, reads the cache's floor and its read rate from the kit, measures each tenant's corpus with the kit's estimate, reads the policies make roster writes, and prices the judge on every claim. Four prices come from Google's pages, dated in the cell: the cache's storage, the embedding, the ranking query and the judge's default autorater.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
a cache would replace $0.01284 a claim: 7,825 chunk tokens at the ceiling, one embedding, one ranking query
  1,000 claims a month: a cached corpus is cheaper below 14,588 tokens; no cache exists below 4,096
 10,000 claims a month: a cached corpus is cheaper below 57,567 tokens; no cache exists below 4,096
100,000 claims a month: a cached corpus is cheaper below 81,612 tokens; no cache exists below 4,096
acme    485,430 tokens: Rs 30,121 a month to keep it cached, Rs 6.19 a claim to read it
globex   43,184 tokens: Rs  2,680 a month to keep it cached, Rs 0.55 a claim to read it
zeta    287,517 tokens: Rs 17,840 a month to keep it cached, Rs 3.67 a claim to read it
acme    data_region any: a web search only once the tenant has agreed to it
zeta    data_region any: a web search only once the tenant has agreed to it
globex  data_region in : its text stays on the kit's own rows: a web search is refused
a judge on every claim: Rs 0.47 a claim, Rs 46,512 a month at 100k; one in twenty, Rs 2,326
```

### demo_05_failure_modes_four_the_kit_reproduces_and_which_ones_the_alerts_see.py

The cell reads every Terraform file in the kit, lists the alert policies each declares, holds quota.tf's named alerts against them, and prints what the unanswerable rate's denominator counts.

**`step_01_the_alerts_the_kit_declares_against_the_on(session)` — Failure modes: four the kit reproduces, and which ones the alerts see / Do it: the alerts the kit declares, against the ones it names**

The cell reads every Terraform file in the kit, lists the alert policies each declares, holds quota.tf's named alerts against them, and prints what the unanswerable rate's denominator counts.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
alerts.tf declares api_latency, unanswerable_rate, gpu_left_warm, ingest_failed, reconcile_drift, reconcile_failed, dlq_depth, ingest_backlog
desk_alerts.tf declares desk_fallback_share, desk_l2_share, desk_clarify_oos_trend, case_overdue, doc_type_pin_miss, desk_delegation_refused, desk_gate_error_share, desk_check_tenants_unread
quota.tf names unanswerable_rate declared in alerts.tf
quota.tf names dlq_depth         declared in alerts.tf
quota.tf names guardrail_blocks  declared by nothing
quota.tf names cache_hit_low     declared by nothing
quota.tf names burn_rate         declared by nothing
the unanswerable rate counts: resource.type="cloud_run_revision" resource.labels.service_name="documind-api" (jsonPayload.event="query" OR jsonPayload.event="stream")
rows it never counts: passages, desk_gate
```

### demo_06_cost_a_claim_a_month_and_a_floor_at_1k_10k_and_100k_claims.py

This is the table as a script you can keep: component 6's COST-MODEL.md starts from its output. It reads the rates and the rupee rate from the kit, rebuilds a claim's budget with the kit's own function, and carries the three prices the kit does not hold, the embedding, the ranking query and the judge's autorater, as constants with their date. The ceiling is what no claim may exceed; the average is what claims cost. make usage reads the last day's usage rows, and its table by model and backend carries each model's answers and tokens; the second line divides them. Your average depends on what was asked on your lane, so it is yours, not the author's.

**`step_01_the_cost_model_as_a_script(session)` — Cost: a claim, a month and a floor, at 1k, 10k and 100k claims / Do it: the cost model as a script**

This is the table as a script you can keep: component 6's COST-MODEL.md starts from its output. It reads the rates and the rupee rate from the kit, rebuilds a claim's budget with the kit's own function, and carries the three prices the kit does not hold, the embedding, the ranking query and the judge's autorater, as constants with their date.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
a claim at the ceiling, 8,000 tokens in and 2,048 out: model $0.02736, retrieval $0.00110, judge $0.000274
  1,000 claims, SMALL : model Rs 2,326 + retrieval Rs 94 + judge Rs 23 + floor Rs 32,157 = Rs 34,600 ($407), Rs 34.60 a claim
  1,000 claims, MEDIUM: model Rs 2,326 + retrieval Rs 94 + judge Rs 23 + floor Rs 81,100 = Rs 83,543 ($983), Rs 83.54 a claim
 10,000 claims, SMALL : model Rs 23,256 + retrieval Rs 935 + judge Rs 233 + floor Rs 32,157 = Rs 56,581 ($666), Rs 5.66 a claim
 10,000 claims, MEDIUM: model Rs 23,256 + retrieval Rs 935 + judge Rs 233 + floor Rs 81,100 = Rs 1,05,524 ($1,241), Rs 10.55 a claim
100,000 claims, SMALL : model Rs 2,32,560 + retrieval Rs 9,350 + judge Rs 2,326 + floor Rs 32,157 = Rs 2,76,393 ($3,252), Rs 2.76 a claim
100,000 claims, MEDIUM: model Rs 2,32,560 + retrieval Rs 9,350 + judge Rs 2,326 + floor Rs 81,100 = Rs 3,25,336 ($3,827), Rs 3.25 a claim
```

**`step_02_your_lane_s_tokens_a_claim_from_the_rows(session)` — Cost: a claim, a month and a floor, at 1k, 10k and 100k claims / Do it: your lane's tokens a claim, from the rows**

The ceiling is what no claim may exceed; the average is what claims cost. make usage reads the last day's usage rows, and its table by model and backend carries each model's answers and tokens; the second line divides them. Your average depends on what was asked on your lane, so it is yours, not the author's.

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: one read of the last day's usage rows).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/usage_tokens.txt]
```

### demo_07_cost_at_10_the_limits_the_kit_declares_and_the_one_it_does_not.py

The first cell reads the four ceilings from the kit's files and does the arithmetic for 1k, 10k, 100k and a million claims a month. The second block reads the same values from your lane: the API's scale and concurrency, the deployed index's machine and replicas, and whether quota.tf's override is in your Terraform state.

**`step_01_the_ceilings_from_the_kit_s_files_then_you(session)` — Cost at 10×: the limits the kit declares, and the one it does not / Do it: the ceilings from the kit's files, then your lane's**

The first cell reads the four ceilings from the kit's files and does the arithmetic for 1k, 10k, 100k and a million claims a month. The second block reads the same values from your lane: the API's scale and concurrency, the deployed index's machine and replicas, and whether quota.tf's override is in your Terraform state.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
documind-api: 40 at a time x 20 instances = 800 claims in flight; 0 kept warm; cut at 120 s
Vector Search: min 1 and max 1 replica: one node answers every claim's search
quota.tf: 600 generate_content requests a minute for the whole project; GEMINI_QUOTA_OVERRIDE ?= false
800 slots turn over 16,000 claims a minute at the 3 s SLO and 400 at the 120 s cut; they bind before the quota once a claim takes 80 s
    1,000 a month:  0.023 a minute, one every 2,628.0 s | the quota binds at a busiest minute 26,280.0 x the average; the slots, at 120 s a claim, at 17,520.0 x
   10,000 a month:  0.228 a minute, one every   262.8 s | the quota binds at a busiest minute  2,628.0 x the average; the slots, at 120 s a claim, at  1,752.0 x
  100,000 a month:  2.283 a minute, one every    26.3 s | the quota binds at a busiest minute    262.8 x the average; the slots, at 120 s a claim, at    175.2 x
1,000,000 a month: 22.831 a minute, one every     2.6 s | the quota binds at a busiest minute     26.3 x the average; the slots, at 120 s a claim, at     17.5 x
```

**`step_02_the_ceilings_from_the_kit_s_files_then_you(session)` — Cost at 10×: the limits the kit declares, and the one it does not / Do it: the ceilings from the kit's files, then your lane's**

The first cell reads the four ceilings from the kit's files and does the arithmetic for 1k, 10k, 100k and a million claims a month. The second block reads the same values from your lane: the API's scale and concurrency, the deployed index's machine and replicas, and whether quota.tf's override is in your Terraform state.

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: reads only, nothing changed).

IDE adaptation: Run with the page's shell semantics: every line is a read. grep -c prints 0 and exits 1 on a lane without quota.tf's override, and that 0 is the answer the page reads, not a failure; the cell ends on true so its last line's status is not taken for one.

Expected shape, not a promised result:

```text
autoscaling.knative.dev/maxScale: '20'
      containerConcurrency: 40
      timeoutSeconds: 120
e2-standard-2	1	1
0
```

### demo_08_evals_what_blocks_what_advises_and_what_cannot_fail.py

Do it: the gate offline, and the rows that cannot fail

**`step_01_the_gate_offline_and_the_rows_that_cannot(session)` — Evals: what blocks, what advises, and what cannot fail / Do it: the gate offline, and the rows that cannot fail**

Do it: the gate offline, and the rows that cannot fail

Operation: bash — run in the operator shell, in $DEMO_ROOT (the offline gate, then a Python cell; Rs 0: no credential, no call).

Expected shape, not a promised result:

```text
== eval gate: OFFLINE (no credentials, no cost) ==
  65 golden rows over 3 tenants, 27 documents

  [PASS] falsifiable
  [PASS] anchors
  [PASS] coverage

  The golden set is sound. It can go red, and it still contains the rows that would.
what blocks a release: 9 thresholds and 15 required rows over 65 rows, scored by code
must_not_contain on 12 rows: 11 isolation, 1 version
  vr-01 (version): ['90 days'] lives only in a revision under evals/demo; a version the ledger failed to retire can say it, so it can fail
  the 11 isolation rows: the retriever filters by tenant before the generator reads, so they fail only on an invented figure
  what replaced them: isolation_403_rate at 1.00, asked by an account on no tenant's roster
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_3.9_Design_Fact_Checking_WIX.html`. All 48 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `af82fe1d1e35eabd754b6aec0d095c10bf085032`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
