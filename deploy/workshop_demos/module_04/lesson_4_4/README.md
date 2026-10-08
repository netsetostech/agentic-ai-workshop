# Lesson 4.4: Compare one controlled change against a baseline

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_candidate_a_new_revision_with_no_traffic_and_the_proof_that_one_setting_diff.py](demo_03_the_candidate_a_new_revision_with_no_traffic_and_the_proof_that_one_setting_diff.py) | The candidate: a new revision with no traffic, and the proof that one setting differs |
| 4 | [demo_04_the_scoped_gate_on_both_revisions_and_the_rows_that_moved.py](demo_04_the_scoped_gate_on_both_revisions_and_the_rows_that_moved.py) | The scoped gate on both revisions, and the rows that moved |
| 5 | [demo_05_the_pairwise_judge_which_answer_is_better_row_by_row.py](demo_05_the_pairwise_judge_which_answer_is_better_row_by_row.py) | The pairwise judge: which answer is better, row by row |
| 6 | [demo_06_the_rupee_delta_from_the_usage_rows.py](demo_06_the_rupee_delta_from_the_usage_rows.py) | The rupee delta, from the usage rows |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Lesson 4.2's judge environment and a single baseline revision; no other lesson should own the candidate tag.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [cleanup/demo_08_deciding_the_confounds_that_fake_a_result_and_removing_the_candidate.py](cleanup/demo_08_deciding_the_confounds_that_fake_a_result_and_removing_the_candidate.py) — At lesson end: This ends the experiment. The candidate revision stays in the service's history with no traffic and no URL. Removing the tag is not enough on its own: make promote refuses only when the tag points at another revision, and otherwise flips traffic to the revision named in .candidate-revision. Deleting that file makes make promote stop with an error instead.
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

### demo_03_the_candidate_a_new_revision_with_no_traffic_and_the_proof_that_one_setting_diff.py

Do it: the candidate The cell finds the revision serving traffic and the one tagged candidate, reads both revisions' settings, and prints every setting that differs.

**`step_01_the_candidate(session)` — The candidate: a new revision with no traffic, and the proof that one setting differs / Do it: the candidate**

Do it: the candidate

Operation: bash — run in the operator shell, in the kit (a new revision with no traffic; nothing moves for users).

Expected shape, not a promised result:

```text
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \
  --update-env-vars "^|^GENERATOR_MODEL=gemini-3.1-flash-lite|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|..." --remove-env-vars GENERATOR_LOCATION
...
>> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app
```

**`step_02_prove_it_is_one_change(session)` — The candidate: a new revision with no traffic, and the proof that one setting differs / Do it: prove it is one change**

The cell finds the revision serving traffic and the one tagged candidate, reads both revisions' settings, and prints every setting that differs.

Operation: bash — run in the operator shell, in the kit (reads both revisions; changes nothing).

Expected shape, not a promised result:

```text
live documind-api-000NN-xxx   candidate documind-api-000NN-yyy
  GENERATOR_MODEL        gemini-3.6-flash           -> gemini-3.1-flash-lite
1 setting(s) differ
```

### demo_04_the_scoped_gate_on_both_revisions_and_the_rows_that_moved.py

Do it: the gate on the live revision, then on the candidate Now set the two reports side by side: each judged threshold on both revisions, every row whose verdict changed, and the median round trip of each.

**`step_01_the_gate_on_the_live_revision_then_on_the(session)` — The scoped gate on both revisions, and the rows that moved / Do it: the gate on the live revision, then on the candidate**

Do it: the gate on the live revision, then on the candidate

Operation: bash — run in the operator shell, in the kit (the 10 rows that cite the handbook, on each revision: a few minutes).

IDE adaptation: Run both gates through live_gate: a red gate on the live revision or the candidate is an observation this lesson compares, and each keeps its fresh report. The page's `| tail -3` stopped the cell under pipefail on a red baseline; here the whole gate output shows. A missing report or an HTTP/auth failure still fails.

Expected shape, not a promised result:

```text
>> https://documind-api-NUMBER.asia-south1.run.app

  report: evals/reports/base73.json
  All thresholds met.
>> https://candidate---documind-api-NUMBER.asia-south1.run.app
== eval gate: LIVE ==
  scoped to hr_policy_2026.md: 10 row(s) cite it
  10 rows (10 answerable, 0 not) against https://candidate---documind-api-NUMBER.asia-south1.run.app

  [PASS] request_success_rate  100.0%  (threshold 100%; 10 rows)
  [PASS] answerable_rate       100.0%  (threshold 80%; 10 rows)
  [PASS] citation_rate         100.0%  (threshold 95%; 10 rows)
  [PASS] citation_valid_rate   100.0%  (threshold 100%; 10 rows)
  [PASS] must_contain_rate      90.0%  (threshold 85%; 10 rows)
  [PASS] correct_rate           90.0%  (threshold 68%; 10 rows)
  [ -- ] refusal_rate            0.0%  (threshold 90%; no rows in scope; 0 rows)
  [ -- ] media_kind_rate         0.0%  (threshold 80%; no rows in scope; 0 rows)
  [ -- ] isolation_403_rate      0.0%  (threshold 100%; no rows in scope; 0 rows)
  [info] quote_support_rate      ...  (quoted words found in the tenant's corpus text; not a threshold - a Doc AI extraction and a pypdf mirror hyphenate differently)

  shape        rows   ok   pass
  lookup          9    9      8
  version         1    1      1
  latency ms  p50   ...  p95   ...   (round trip, 10 rows)
  retrieve_ms p50   ...  p95   ...
  rerank_ms   p50   ...  p95   ...
  generate_ms p50   ...  p95   ...
  pool        avg   ...   semantic cache hits ...

  rows that cost a point (1):
    lk-04  lookup    acme    answered without ['15'] | 'the documents cover this [1].'

  report: evals/reports/cand73.json
  All thresholds met.
```

**`step_02_the_gate_on_the_live_revision_then_on_the(session)` — The scoped gate on both revisions, and the rows that moved / Do it: the gate on the live revision, then on the candidate**

Now set the two reports side by side: each judged threshold on both revisions, every row whose verdict changed, and the median round trip of each.

Operation: bash — run in the operator shell, in the kit (reads the two reports; changes nothing).

Expected shape, not a promised result:

```text
live  candidate  needs
  request_success_rate   100.0%     100.0%   100%
  answerable_rate        100.0%     100.0%    80%
  citation_rate          100.0%     100.0%    95%
  citation_valid_rate    100.0%     100.0%   100%
  must_contain_rate      100.0%      90.0%    85%
  correct_rate           100.0%      90.0%    68%
  lk-04: pass on live, fail on the candidate (answered without ['15'])
  1 row(s) changed verdict; median round trip ... ms live, ... ms candidate
```

### demo_05_the_pairwise_judge_which_answer_is_better_row_by_row.py

Do it

**`step_01_the_pairwise_judge_which_answer_is_better(session)` — The pairwise judge: which answer is better, row by row / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (twenty rows on each revision, then the Evaluation service).

Expected shape, not a promised result:

```text
>> https://documind-api-NUMBER.asia-south1.run.app
  20/20 answers collected from https://documind-api-NUMBER.asia-south1.run.app in ...s (model gemini-3.6-flash)
  20/20 candidate answers from https://candidate---documind-api-NUMBER.asia-south1.run.app
  context: .../... cited chunks read in full from the store
  trajectories: off (no --chat-url)
  pointwise: GROUNDEDNESS + INSTRUCTION_FOLLOWING  (templates cd7070; run api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070)
  judge: the service default (pass --judge-model to pin one)

  Experiments run documind-eval/api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070:
    groundedness/mean                                ...
    groundedness/mean[join]                          ...
    groundedness/mean[lookup]                        ...
    groundedness/std                                 ...
    instruction_following/mean                       ...
    instruction_following/std                        ...
    pairwise_question_answering_quality/baseline_model_win_rate ...
    pairwise_question_answering_quality/candidate_model_win_rate ...
    row_count                                        20.000

  the gate (run_eval.py) still decides; this judge explains. Where they disagree, read the row.
```

### demo_06_the_rupee_delta_from_the_usage_rows.py

Every answer of the last hour, grouped by the model that gave it, and the difference per answer. The API priced every answer on its usage row with cost.price(), at the rates of the model that answered. The gate's runs and the judge's collections asked both revisions the same questions, so the two groups are like for like. The cell groups the last hour's rows by model and divides.

**`step_01_the_rupee_delta_from_the_usage_rows(session)` — The rupee delta, from the usage rows / The rupee delta, from the usage rows**

Every answer of the last hour, grouped by the model that gave it, and the difference per answer. The API priced every answer on its usage row with cost.price(), at the rates of the model that answered. The gate's runs and the judge's collections asked both revisions the same questions, so the two groups are like for like. The cell groups the last hour's rows by model and divides.

Operation: bash — run in the operator shell, in the kit (the last hour of usage rows, by model).

Expected shape, not a promised result:

```text
gemini-3.6-flash          ... answers  Rs ...  Rs ... an answer
  gemini-3.1-flash-lite     ... answers  Rs ...  Rs ... an answer
  the candidate costs Rs ... less an answer: Rs ... per 1,000 answers
```

### cleanup/demo_08_deciding_the_confounds_that_fake_a_result_and_removing_the_candidate.py

At lesson end: This ends the experiment. The candidate revision stays in the service's history with no traffic and no URL. Removing the tag is not enough on its own: make promote refuses only when the tag points at another revision, and otherwise flips traffic to the revision named in .candidate-revision. Deleting that file makes make promote stop with an error instead.

**`step_01_remove_the_candidate_s_tag(session)` — Deciding, the confounds that fake a result, and removing the candidate / Do it: remove the candidate's tag**

This ends the experiment. The candidate revision stays in the service's history with no traffic and no URL. Removing the tag is not enough on its own: make promote refuses only when the tag points at another revision, and otherwise flips traffic to the revision named in .candidate-revision. Deleting that file makes make promote stop with an error instead.

Operation: bash — run in the operator shell, in the kit (the candidate's tag and its recorded name removed; the live revision is untouched).

Expected shape, not a promised result:

```text
...
the candidate URL now: HTTP 404
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_4.4_Controlled_Change_WIX.html`. All 27 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `97d97638098f6e3f140aba7bc44e9edda7bc2aa0`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
