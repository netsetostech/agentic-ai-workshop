# Lesson 1.6: Reindex a changed section and measure embedding reuse

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_gate_the_golden_set_scoped_to_one_document.py](demo_03_the_gate_the_golden_set_scoped_to_one_document.py) | The gate: the golden set, scoped to one document |
| 4 | [demo_04_measure_reuse_six_kinds_of_edit_rs_0.py](demo_04_measure_reuse_six_kinds_of_edit_rs_0.py) | Measure reuse: six kinds of edit, Rs 0 |
| 5 | [demo_05_do_it_revision_3_of_the_handbook_on_the_lane.py](demo_05_do_it_revision_3_of_the_handbook_on_the_lane.py) | Do it: revision 3 of the handbook, on the lane |
| 6 | [demo_06_inspect_the_ledger_row_the_claims_the_vectors.py](demo_06_inspect_the_ledger_row_the_claims_the_vectors.py) | Inspect: the ledger row, the claims, the vectors |
| 7 | [demo_07_the_gate_goes_red_and_the_two_ways_back_to_green.py](demo_07_the_gate_goes_red_and_the_two_ways_back_to_green.py) | The gate goes red, and the two ways back to green |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The original handbook and unchanged golden set; the live gate deliberately fails for revision 3.

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

### demo_03_the_gate_the_golden_set_scoped_to_one_document.py

Do it: the offline gate, scoped to the handbook, Rs 0

**`step_01_the_offline_gate_scoped_to_the_handbook_rs(session)` — The gate: the golden set, scoped to one document / Do it: the offline gate, scoped to the handbook, Rs 0**

Do it: the offline gate, scoped to the handbook, Rs 0

Operation: bash — run in the operator shell, in $DEMO_ROOT (no credentials, no cost).

Expected shape, not a promised result:

```text
== eval gate: OFFLINE (no credentials, no cost) ==
  65 golden rows over 3 tenants, 27 documents

  [PASS] falsifiable
  [PASS] anchors
  [PASS] coverage

  The golden set is sound. It can go red, and it still contains the rows that would.

  rows citing hr_policy_2026.md: 10 - the scoped live gate judges these
    lk-01  lookup    What is the per-trip cap on domestic travel reimbursement?
    lk-02  lookup    By when is Form 16 issued?
    lk-03  lookup    How many days of earned leave can I carry forward?
    lk-04  lookup    What notice period applies during probation?
    lk-05  lookup    Are USB drives allowed on a company laptop?
    lk-06  lookup    What is the notice period for a confirmed E3?
    lk-07  lookup    At what rate does earned leave accrue?
    lk-08  lookup    Who approves a purchase of Rs 3,00,000?
    lk-09  lookup    How many days a month can I work remotely?
    vr-01  version   What is the notice period for a confirmed E3?
```

### demo_04_measure_reuse_six_kinds_of_edit_rs_0.py

Do it: the six edits through the worker's planner

**`step_01_the_six_edits_through_the_worker_s_planner(session)` — Measure reuse: six kinds of edit, Rs 0 / Do it: the six edits through the worker's planner**

Do it: the six edits through the worker's planner

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
a figure in NP-03 (60 to 90)         chunks 283 -> 283  reused 282  embedded  1    234 chars  ['NP-03']
a figure in PB-02 (15 to 20)         chunks 283 -> 283  reused 282  embedded  1    212 chars  ['PB-02']
NP-03 re-wrapped (whitespace only)   chunks 283 -> 283  reused 283  embedded  0      0 chars  []
NP-03's heading renamed              chunks 283 -> 283  reused 282  embedded  1    250 chars  ['NP-03']
a clause inserted before PB-02       chunks 283 -> 284  reused 283  embedded  1     84 chars  ['NP-04']
NP-03 and PB-02 swapped              chunks 283 -> 283  reused 283  embedded  0      0 chars  []
wages: a sentence added on page 2    chunks  65 ->  65  reused  63  embedded  2   3261 chars  ['p2-0', 'p2-1']
```

### demo_05_do_it_revision_3_of_the_handbook_on_the_lane.py

Do it

**`step_01_do_it_revision_3_of_the_handbook_on_the_la(session)` — Do it: revision 3 of the handbook, on the lane / Do it**

Do it

Operation: bash — run in the operator shell, in $DEMO_ROOT (writes the revision to your home directory, then one re-issue).

Expected shape, not a promised result:

```text
/home/you/hr_policy_2026_rev3.md | version key acme_54337b4ba3f0...
>> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)
>> event doc_key chunks reused embedded retired effective_from
>> ingest_ok	acme_54337b4ba3f0109a...	283	281	2	283	2026-11-01
>> retired (doc_keys, chunks, expire days): [u'acme_497809ffbaa603c4...']	283	30
>> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_2026.md API=<candidate url>
```

### demo_06_inspect_the_ledger_row_the_claims_the_vectors.py

Read the three

**`step_01_read_the_three(session)` — Inspect: the ledger row, the claims, the vectors / Read the three**

Read the three

Operation: bash — run in the operator shell (the ledger row from the API, then the claims and the vectors from Firestore).

Expected shape, not a promised result:

```text
acme/hr_policy_2026.md chunks 283 reused 281 embedded 2 retired 283 effective 2026-11-01 text-embedding-005@1
3 claims (versions) for hr_policy_2026.md, oldest first
  acme_497809ff...  superseded chunks 283  reused 0  embedded 283  superseded_by acme_54337b4b...  reactivated once
  acme_55603088...  superseded chunks 283  reused 281  embedded 2  superseded_by acme_497809ff...
  acme_54337b4b...  indexed    chunks 283  reused 281  embedded 2
rows: 849 | current: 283 | retired: 566
  LV-01  current hash ff463cede286  version 1's hash ff463cede286  same vector: True
  NP-03  current hash 876232171dec  version 1's hash f4512754ae41  same vector: False
```

### demo_07_the_gate_goes_red_and_the_two_ways_back_to_green.py

Ten questions to the API, each a generation call: a few rupees at most. The target mints two identity tokens, the UI's account as the member and the outsider's for the isolation rows, which is why it takes a moment to start. Version 1's bytes again, through the same release command. The offline gate passes, the upload lands, and the worker finds a version it has retired within the window: ingest_reactivated, nothing embedded, revision 3 retired in turn. The live gate then passes with the rows as they are.

**`step_01_the_live_gate_red(session)` — The gate goes red, and the two ways back to green / Do it: the live gate, red**

Ten questions to the API, each a generation call: a few rupees at most. The target mints two identity tokens, the UI's account as the member and the outsider's for the isolation rows, which is why it takes a moment to start.

Operation: bash — run in the operator shell, in $DEMO_ROOT (ten questions; a few rupees).

IDE adaptation: Require a fresh report with evaluated answers that fail assertions; preserve the expected nonzero exit without treating authentication or command failure as the lesson's proof.

Expected shape, not a promised result:

```text
>> https://documind-api-NUMBER.asia-south1.run.app
== eval gate: LIVE ==
  scoped to hr_policy_2026.md: 10 row(s) cite it
  10 rows (10 answerable, 0 not) against https://documind-api-NUMBER.asia-south1.run.app

  [PASS] request_success_rate  100.0%  (threshold 100%; 10 rows)
  [PASS] answerable_rate       100.0%  (threshold 80%; 10 rows)
  [PASS] citation_rate         100.0%  (threshold 95%; 10 rows)
  [PASS] citation_valid_rate   100.0%  (threshold 100%; 10 rows)
  [FAIL] must_contain_rate      80.0%  (threshold 85%; 10 rows)
  [PASS] correct_rate           80.0%  (threshold 68%; 10 rows)
  [ -- ] refusal_rate            0.0%  (threshold 90%; no rows in scope; 0 rows)
  ...

  shape        rows   ok   pass
  lookup          9    9      8
  version         1    1      0
  latency ms  p50  2410  p95  3980   (round trip, 10 rows)

  rows that cost a point (2):
    lk-06  lookup    acme    missing '60' | What is the notice period for a confirmed E3?
    vr-01  version   acme    missing '60' | What is the notice period for a confirmed E3?

  required rows that did not pass (1) - each one blocks on its own:
    vr-01: missing '60'

  Blocked: must_contain_rate: 80% < 85%; required: 1 mandatory row(s) did not pass
```

**`step_02_the_undo_then_the_gate_green(session)` — The gate goes red, and the two ways back to green / The undo, then the gate, green**

Version 1's bytes again, through the same release command. The offline gate passes, the upload lands, and the worker finds a version it has retired within the window: ingest_reactivated, nothing embedded, revision 3 retired in turn. The live gate then passes with the rows as they are.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the undo, then ten questions again).

Expected shape, not a promised result:

```text
>> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)
>> event doc_key chunks reused embedded retired effective_from
>> ingest_reactivated	acme_497809ffbaa603c4...	283	283	0	283
>> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_2026.md API=<candidate url>
...
  [PASS] must_contain_rate     100.0%  (threshold 85%; 10 rows)
  ...
  shape        rows   ok   pass
  lookup          9    9      9
  version         1    1      1
  All thresholds met.
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_1.6_Reindex_WIX.html`. All 26 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `a687d81609b23483c7d84b8575ae6615b57d9f0c`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
