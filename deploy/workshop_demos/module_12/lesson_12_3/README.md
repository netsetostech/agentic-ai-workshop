# Lesson 12.3: Compare the tuned candidate with an uncontaminated baseline

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_what_the_kit_does_with_a_tuned_candidate.py](demo_03_what_the_kit_does_with_a_tuned_candidate.py) | What the kit does with a tuned candidate |
| 4 | [demo_04_the_candidate_audited.py](demo_04_the_candidate_audited.py) | The candidate, audited |
| 5 | [demo_05_the_gate_on_both_revisions.py](demo_05_the_gate_on_both_revisions.py) | The gate on both revisions |
| 6 | [demo_06_the_verdict_and_the_delta.py](demo_06_the_verdict_and_the_delta.py) | The verdict and the delta |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The tuned endpoint from 12.2, its ~/poll172.log and the uncontaminated evaluation baseline. The optional steps 7 and 8 need the v3 endpoint in ~/poll172v3.log (12.2's step 7).

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Optional extensions

- [optional/demo_07_optional_the_v3_candidate_and_the_gate_on_it.py](optional/demo_07_optional_the_v3_candidate_and_the_gate_on_it.py) — Do it Then the chapter's gate, on v3. A tidy format is worth nothing if the answers under it fail:
- [optional/demo_08_optional_one_question_two_models.py](optional/demo_08_optional_one_question_two_models.py) — Do it

## Finish and restore

- [cleanup/demo_06_the_verdict_and_the_delta.py](cleanup/demo_06_the_verdict_and_the_delta.py) — At lesson end: The decision is yours, and it reads the three results in order. The gate must pass. The judge says how often the tuned model gives the worse answer where the two differ. The delta says what that is worth at your volume. With a candidate that passes, there are three ways forward:
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

### demo_03_what_the_kit_does_with_a_tuned_candidate.py

Do it

**`step_01_what_the_kit_does_with_a_tuned_candidate(session)` — What the kit does with a tuned candidate / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the kit's own functions; no network).

Expected shape, not a promised result:

```text
an answer gemini-3.6-flash cached, looked up for the tuned endpoint: alive True
cost.py with RAG_MODEL_BASE=gemini-3.1-flash-lite  Rs 0.1764 an answer of 7,400 tokens in, 150 out
cost.py with RAG_MODEL_BASE=gemini-3.6-flash       Rs 1.0391 an answer of 7,400 tokens in, 150 out
Google, a tuned endpoint at 1.5 x its base          Rs 0.2646

make usage's model column
model                  answers    tok_in  tok_out       USD       INR  p95 ms  unans
------------------------------------------------------------------------------------
gemini-3.6-flash             1      7400      210    0.0127      1.08    2100   0.00
projects/NUMBER/loca         1      7400      150    0.0021      0.18    1000   0.00
```

### demo_04_the_candidate_audited.py

Do it: the candidate The cell makes the four checks from step 1:

**`step_01_the_candidate(session)` — The candidate, audited / Do it: the candidate**

Do it: the candidate

Operation: bash — run in the operator shell, in the kit (a revision with no traffic; nothing is billed until it answers).

Expected shape, not a promised result:

```text
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \
  --update-env-vars "^|^GENERATOR_MODEL=projects/NUMBER/locations/us/endpoints/9136961803583303949|RAG_MODEL_BASE=gemini-3.1-flash-lite|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=off|SEMANTIC_CACHE=off|RETRIEVAL_CURRENT_ONLY=off|RETRIEVAL_GRAPH=off|GRAPH_BACKEND=firestore|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
...
>> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app
```

**`step_02_the_audit(session)` — The candidate, audited / Do it: the audit**

The cell makes the four checks from step 1:

Operation: bash — run in the operator shell, in the kit (reads both revisions, ~/tune172.log, the bucket and Firestore).

Expected shape, not a promised result:

```text
1. one change: 2 settings differ between documind-api-000NN-xxx (live) and documind-api-000NN-yyy
   GENERATOR_MODEL  gemini-3.6-flash -> projects/NUMBER/locations/us/endpoints/9136961803583303949
   RAG_MODEL_BASE   gemini-3.6-flash -> gemini-3.1-flash-lite
   the model and the base it is priced at, and nothing else
2. the answer cache: off on the live revision, off on the candidate
3. the test set: the endpoint was tuned on documind_sft_v2.vertex.jsonl, 315 rows; building it dropped 15 for the golden set, and today's golden set would drop 0 more
4. the context cache: none for acme, so both revisions pay full price for their input
verdict: uncontaminated - one change, no answer cache, a training file the test set never entered, the same input price
```

### demo_05_the_gate_on_both_revisions.py

Do it

**`step_01_the_gate_on_both_revisions(session)` — The gate on both revisions / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (every golden row, on each revision: about twenty minutes).

IDE adaptation: Run both gates through live_gate: a red gate on the live revision or the tuned candidate is an observation this lesson compares, and each keeps its fresh report. The page's `| tail -3` stopped the cell under pipefail on a red baseline; here the whole gate output shows. A missing report or an HTTP/auth failure still fails.

Expected shape, not a promised result:

```text
report: /home/YOU/base173.json
  All thresholds met.
>> https://candidate---documind-api-NUMBER.asia-south1.run.app
  65 rows (47 answerable, 18 not) against https://candidate---documind-api-NUMBER.asia-south1.run.app

  [PASS] request_success_rate  100.0%  (threshold 100%; 65 rows)
  [PASS] answerable_rate        97.9%  (threshold 80%; 47 rows)
  [PASS] citation_rate         100.0%  (threshold 95%; 46 rows)
  [PASS] citation_valid_rate   100.0%  (threshold 100%; 46 rows)
  [PASS] must_contain_rate      95.7%  (threshold 85%; 46 rows)
  [PASS] correct_rate           93.6%  (threshold 68%; 47 rows)
  [PASS] refusal_rate          100.0%  (threshold 90%; 18 rows)
  [PASS] media_kind_rate       100.0%  (threshold 80%; 3 rows)
  [PASS] isolation_403_rate    100.0%  (threshold 100%; 11 rows)
  [info] quote_support_rate      ...  (quoted words found in the tenant's corpus text; not a threshold - a Doc AI extraction and a pypdf mirror hyphenate differently)

  shape        rows   ok   pass
  lookup         34   34     33
  join           11   11      9
  refusal         8    8      8
  isolation      11   11     11
  version         1    1      1
  latency ms  p50   ...  p95   ...   (round trip, 65 rows)
  retrieve_ms p50   ...  p95   ...
  rerank_ms   p50   ...  p95   ...
  generate_ms p50   ...  p95   ...
  pool        avg   ...   semantic cache hits ...

  rows that cost a point (3):
    jn-03  join      acme    answered without ['45', '60'] | '45 days of the earned leave are encashed.'
    jn-09  join      acme    answered without ['8.33', 'twenty per cent'] | 'the minimum bonus is 8.33% of the salary or wage.'
    lk-27  lookup    acme    REFUSED conf=low cites=0 | What is the maximum rate of central tax the CGST Act allows?

  report: /home/YOU/cand173.json
  All thresholds met.
```

**`step_02_the_gate_on_both_revisions(session)` — The gate on both revisions / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (reads the two reports).

Expected shape, not a promised result:

```text
live  candidate  needs
  request_success_rate   100.0%     100.0%   100%
  answerable_rate         97.9%      97.9%    80%
  citation_rate          100.0%     100.0%    95%
  citation_valid_rate    100.0%     100.0%   100%
  must_contain_rate       97.8%      95.7%    85%
  correct_rate            95.7%      93.6%    68%
  refusal_rate           100.0%     100.0%    90%
  media_kind_rate        100.0%     100.0%    80%
  isolation_403_rate     100.0%     100.0%   100%
  jn-03: pass on live, fail on the candidate (answered without ['45', '60'])
  jn-06: fail on live, pass on the candidate (ok)
  jn-09: pass on live, fail on the candidate (answered without ['8.33', 'twenty per cent'])
  3 row(s) changed verdict; median round trip ... ms live, ... ms candidate
```

### demo_06_the_verdict_and_the_delta.py

Do it: the verdict The gates and the judge asked both revisions the same questions, so their usage rows are like for like. The cell prints make usage's model table, groups the rows by model, and prices the endpoint's rows at 1.5 times what they log.

**`step_01_the_verdict(session)` — The verdict and the delta / Do it: the verdict**

Do it: the verdict

Operation: bash — run in the operator shell, in the kit (the judge's venv from lesson 4.2: 65 answers from each revision, then Vertex AI Evaluation).

Expected shape, not a promised result:

```text
>> https://documind-api-NUMBER.asia-south1.run.app
  65/65 answers collected from https://documind-api-NUMBER.asia-south1.run.app in ...s (model gemini-3.6-flash)
  65/65 candidate answers from https://candidate---documind-api-NUMBER.asia-south1.run.app
  context: 46/46 cited chunks read in full from the store
  trajectories: off (no --chat-url)
  pointwise: GROUNDEDNESS + INSTRUCTION_FOLLOWING  (templates cd7070; run api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070)
  judge: the service default (pass --judge-model to pin one)

  Experiments run documind-eval/api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070:
    groundedness/mean                                1.000
    groundedness/mean[isolation]                     1.000
    groundedness/mean[join]                          1.000
    groundedness/mean[lookup]                        1.000
    groundedness/mean[refusal]                       1.000
    groundedness/mean[version]                       1.000
    groundedness/std                                 0.000
    instruction_following/mean                       4.877
    instruction_following/std                        0.600
    pairwise_question_answering_quality/baseline_model_win_rate 0.031
    pairwise_question_answering_quality/candidate_model_win_rate 0.015
    row_count                                        65.000

  the gate (run_eval.py) still decides; this judge explains. Where they disagree, read the row.
```

**`step_02_the_delta(session)` — The verdict and the delta / Do it: the delta**

The gates and the judge asked both revisions the same questions, so their usage rows are like for like. The cell prints make usage's model table, groups the rows by model, and prices the endpoint's rows at 1.5 times what they log.

Operation: bash — run in the operator shell, in the kit (reads the last two hours of usage rows).

Expected shape, not a promised result:

```text
by model and backend (what answered, through which door)
model                 model_backend          answers    tok_in  tok_out       USD       INR  p95 ms  unans
----------------------------------------------------------------------------------------------------------
gemini-3.6-flash      vertex                     130    952849    28030    1.6395    139.36    2100   0.00
projects/NUMBER/loca  vertex                     130    970907    17751    0.2694     22.89    1000   0.00

  live        130 answers  Rs 1.0720 an answer
  candidate   130 answers  Rs 0.1761 an answer as logged, Rs 0.2641 as Google bills it
the rupee delta: the tuned endpoint costs Rs 0.8079 less an answer, Rs 808 per 1,000 answers
  (the usage rows alone say Rs 0.8959: they log the endpoint at its base's rate)
```

### optional/demo_07_optional_the_v3_candidate_and_the_gate_on_it.py

Do it Then the chapter's gate, on v3. A tidy format is worth nothing if the answers under it fail:

**`step_01_optional_the_v3_candidate_and_the_gate_on(session)` — Optional: the v3 candidate, and the gate on it / Do it**

Do it

Operation: bash — optional: run in the operator shell, in the kit (v3's endpoint behind the candidate address; still no traffic).

Expected shape, not a promised result:

```text
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \
  --update-env-vars "^|^GENERATOR_MODEL=projects/NUMBER/locations/us/endpoints/3784707595493887459|RAG_MODEL_BASE=gemini-3.1-flash-lite|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=off|SEMANTIC_CACHE=off|RETRIEVAL_CURRENT_ONLY=off|RETRIEVAL_GRAPH=off|GRAPH_BACKEND=firestore|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
...
>> candidate revision: documind-api-000NN-zzz (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app
```

**`step_02_optional_the_v3_candidate_and_the_gate_on(session)` — Optional: the v3 candidate, and the gate on it / Do it**

Then the chapter's gate, on v3. A tidy format is worth nothing if the answers under it fail:

Operation: bash — optional: run in the operator shell, in the kit (every golden row on the v3 candidate: about ten minutes).

Expected shape, not a promised result:

```text
>> https://candidate---documind-api-NUMBER.asia-south1.run.app
  65 rows (47 answerable, 18 not) against https://candidate---documind-api-NUMBER.asia-south1.run.app

  [PASS] request_success_rate  100.0%  (threshold 100%; 65 rows)
  [PASS] answerable_rate        97.9%  (threshold 80%; 47 rows)
  [PASS] citation_rate         100.0%  (threshold 95%; 46 rows)
  [PASS] citation_valid_rate   100.0%  (threshold 100%; 46 rows)
  [PASS] must_contain_rate      95.7%  (threshold 85%; 46 rows)
  [PASS] correct_rate           93.6%  (threshold 68%; 47 rows)
  [PASS] refusal_rate          100.0%  (threshold 90%; 18 rows)
  [PASS] media_kind_rate       100.0%  (threshold 80%; 3 rows)
  [PASS] isolation_403_rate    100.0%  (threshold 100%; 11 rows)
  [info] quote_support_rate      ...  (quoted words found in the tenant's corpus text; not a threshold - a Doc AI extraction and a pypdf mirror hyphenate differently)

  shape        rows   ok   pass
  lookup         34   34     33
  join           11   11      9
  refusal         8    8      8
  isolation      11   11     11
  version         1    1      1
  latency ms  p50   ...  p95   ...   (round trip, 65 rows)
  retrieve_ms p50   ...  p95   ...
  rerank_ms   p50   ...  p95   ...
  generate_ms p50   ...  p95   ...
  pool        avg   ...   semantic cache hits ...

  rows that cost a point (3):
    jn-03  join      acme    answered without ['45', '60'] | '**answer:** 45 days.\n**why:** at most 45 days of earned leave are encashed on ex'
    jn-09  join      acme    answered without ['8.33', 'twenty per cent'] | '**answer:** 8.33%.\n**why:** the minimum bonus is 8.33% of the salary or wage [1]'
    lk-27  lookup    acme    REFUSED conf=low cites=0 | What is the maximum rate of central tax the CGST Act allows?

  report: /home/YOU/cand173v3.json
  All thresholds met.
```

### optional/demo_08_optional_one_question_two_models.py

Do it

**`step_01_optional_one_question_two_models(session)` — Optional: one question, two models / Do it**

Do it

Operation: bash — optional: run in the operator shell, in the kit (three questions on each revision; ask again as often as you like).

Expected shape, not a promised result:

```text
Q: Can unused leave shorten my notice period?
  live, as the UI answers (gemini-3.6-flash): 2 citation(s), 2 [N] mark(s), 2100 ms, about Rs 1.06
    No. Unused earned leave may not be set off against the notice period [1], and leave cannot be used to shorten notice [2].
  tuned candidate (endpoint 3784707595493887459): 1 citation(s), 1 [N] mark(s), 1000 ms, about Rs 0.25
    **Answer:** No.
    **Why:** Unused earned leave may not be set off against the notice period [1].
    **Clause:** NP-03, hr_policy_2026.md

Q: Kya main apni bachi hui leave se notice period chhota kar sakta hoon?
  live, as the UI answers (gemini-3.6-flash): 2 citation(s), 2 [N] mark(s), 2100 ms, about Rs 1.06
    No. Unused earned leave may not be set off against the notice period [1], and leave cannot be used to shorten notice [2].
  tuned candidate (endpoint 3784707595493887459): 1 citation(s), 1 [N] mark(s), 1000 ms, about Rs 0.25
    **Answer:** Nahi.
    **Why:** Bachi hui earned leave ko notice period ke against set off nahi kiya ja sakta [1].
    **Clause:** NP-03, hr_policy_2026.md

Q: How much is ACME's referral bonus?
  live, as the UI answers (gemini-3.6-flash): 0 citation(s), 0 [N] mark(s), 2100 ms, about Rs 1.06
    The documents do not say. The handbook has a section headed Referral bonus, but it states no amount.
  tuned candidate (endpoint 3784707595493887459): 0 citation(s), 0 [N] mark(s), 1000 ms, about Rs 0.24
    **Answer:** Not in the documents.
    **Why:** None of the sources states this, so there is nothing to cite.

the UI's URL sends 100% of its traffic to documind-api-000NN-xxx; the candidate answers only at its own URL
```

### cleanup/demo_06_the_verdict_and_the_delta.py

At lesson end: The decision is yours, and it reads the three results in order. The gate must pass. The judge says how often the tuned model gives the worse answer where the two differ. The delta says what that is worth at your volume. With a candidate that passes, there are three ways forward:

**`step_01_the_decision_and_the_candidate_s_tag(session)` — The verdict and the delta / The decision, and the candidate's tag**

The decision is yours, and it reads the three results in order. The gate must pass. The judge says how often the tuned model gives the worse answer where the two differ. The delta says what that is worth at your volume. With a candidate that passes, there are three ways forward:

Operation: bash — run in the operator shell, in the kit (removes the candidate's address; the revision stays, with no traffic).

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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_12.3_Tuned_Candidate_WIX.html`. All 33 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `b2fefa0d8707ac518698fb9851e542583dd1762a`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
