# Lesson 4.3: Place evals in the pipeline: CI, the candidate gate and live traffic

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_ci_the_offline_gate_on_every_push_and_the_job_every_release_needs_first.py](demo_03_ci_the_offline_gate_on_every_push_and_the_job_every_release_needs_first.py) | CI: the offline gate on every push, and the job every release needs first |
| 4 | [demo_04_the_candidate_gate_a_revision_with_no_traffic_judged_before_any_user_meets_it.py](demo_04_the_candidate_gate_a_revision_with_no_traffic_judged_before_any_user_meets_it.py) | The candidate gate: a revision with no traffic, judged before any user meets it |
| 5 | [demo_05_live_traffic_the_usage_rows_and_the_gate_s_rows_among_them.py](demo_05_live_traffic_the_usage_rows_and_the_gate_s_rows_among_them.py) | Live traffic: the usage rows, and the gate's rows among them |
| 6 | [demo_06_the_stream_s_row_answerable_unless_the_pool_was_empty.py](demo_06_the_stream_s_row_answerable_unless_the_pool_was_empty.py) | The stream's row: answerable, unless the pool was empty |
| 7 | [demo_07_the_alert_s_own_inputs_two_log_metrics_two_policies_and_the_windows_they_saw.py](demo_07_the_alert_s_own_inputs_two_log_metrics_two_policies_and_the_windows_they_saw.py) | The alert's own inputs: two log metrics, two policies, and the windows they saw |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's step 6 needs acme's questions answered from the kit's own index, so point acme at it for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's step 6 needs acme's questions answered from the kit's own index, so point acme at it for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's step 6 needs acme's questions answered from the kit's own index, so point acme at it for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_ci_the_offline_gate_on_every_push_and_the_job_every_release_needs_first.py

The cell reads both workflow files with the standard library and prints each job: what it needs, whether it signs in to Google, who approves it, and every line that runs an eval. A red row has two honest fixes: correct the system that answered, or correct the row against its clause. The quick, dishonest one is to edit the row until the build is green, and this check exists for that edit. The cell moves lk-06's figure from 60 to 120 days, a figure no acme document holds, then runs the line CI runs. A red row has two honest fixes: correct the system that answered, or correct the row against its clause. The quick, dishonest one is to edit the row until the build is green, and this check exists for that edit. The cell moves lk-06's figure from 60 to 120 days, a figure no acme document holds, then runs the line CI runs. Give the kit its file back:

**`step_01_the_pipeline_read_from_its_two_files(session)` — CI: the offline gate on every push, and the job every release needs first / Do it: the pipeline, read from its two files**

The cell reads both workflow files with the standard library and prints each job: what it needs, whether it signs in to Google, who approves it, and every line that runs an eval.

Operation: bash — run in the operator shell, in the kit (reads the two workflow files; no network).

Expected shape, not a promised result:

```text
documind-dryrun.yml: on push, pull_request, workflow_dispatch
  tier-a              needs -                  signs in to Google: no
      runs python evals/run_eval.py
documind-cd.yml: on workflow_dispatch
  eval-gate           needs -                  signs in to Google: no
      runs python evals/run_eval.py
  release-candidate   needs eval-gate          signs in to Google: yes, only if inputs.path == 'candidate'
      runs make eval-live PROJECT="$PROJECT" REGION="$REGION" API="https://candidate---documind-api-$NUMBER.$REGION.run.app"
  promote             needs release-candidate  signs in to Google: yes, then a person (production reviewers)
  release-clouddeploy needs eval-gate          signs in to Google: yes, only if inputs.path == 'clouddeploy'
      runs python evals/run_eval.py --api-url "$URL"
```

**`step_02_break_a_row_the_way_a_hand_edit_would(session)` — CI: the offline gate on every push, and the job every release needs first / Do it: break a row the way a hand edit would**

A red row has two honest fixes: correct the system that answered, or correct the row against its clause. The quick, dishonest one is to edit the row until the build is green, and this check exists for that edit. The cell moves lk-06's figure from 60 to 120 days, a figure no acme document holds, then runs the line CI runs.

Operation: bash — run in the operator shell, in the kit (edits one line of your clone on purpose, then runs what CI runs).

IDE adaptation: The refusal is the observation: the offline gate must exit 1 with its own words for the broken lk-06. Under the demo's set -e the exit stopped the step before the page's echo, step 3's git checkout never ran, and the lane's golden set stayed broken for the next lesson (21 October 2026). Any other exit, or a 1 without those words, fails.

Expected shape, not a promised result:

```text
lk-06 now asks for ['120 days']
 evals/golden.jsonl | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
== eval gate: OFFLINE (no credentials, no cost) ==
  65 golden rows over 3 tenants, 27 documents

  [FAIL] falsifiable
         lk-06: must_contain '120 days' is not in acme's corpus - the row can only fail
  [PASS] anchors
  [PASS] coverage

  1 problem(s). The golden set cannot judge the model until it judges itself.
exit 1
```

**`step_03_break_a_row_the_way_a_hand_edit_would(session)` — CI: the offline gate on every push, and the job every release needs first / Do it: break a row the way a hand edit would**

A red row has two honest fixes: correct the system that answered, or correct the row against its clause. The quick, dishonest one is to edit the row until the build is green, and this check exists for that edit. The cell moves lk-06's figure from 60 to 120 days, a figure no acme document holds, then runs the line CI runs. Give the kit its file back:

Operation: bash — run in the operator shell, in the kit (the kit's file back).

Expected shape, not a promised result:

```text
Updated 1 path from the index
  The golden set is sound. It can go red, and it still contains the rows that would.
```

### demo_04_the_candidate_gate_a_revision_with_no_traffic_judged_before_any_user_meets_it.py

Do it: the candidate This is the workflow's check, by hand: /version on the live URL and on the tag URL, both with a token minted for the live one. Do it: the gate on the candidate Now read the report as a release decision: how many thresholds were judged, what the outsider got, and each required row. The candidate has done its job. Removing its tag ends its URL. Deleting .candidate-revision means a stray make promote stops with an error instead of moving traffic to it; lesson 4.4 explains why both are needed.

**`step_01_the_candidate(session)` — The candidate gate: a revision with no traffic, judged before any user meets it / Do it: the candidate**

Do it: the candidate

Operation: bash — run in the operator shell, in the kit (a new revision with no traffic; nothing moves for users).

Expected shape, not a promised result:

```text
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \
  --update-env-vars "^|^GENERATOR_MODEL=gemini-3.6-flash|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=off|SEMANTIC_CACHE=off|RETRIEVAL_CURRENT_ONLY=off|RETRIEVAL_GRAPH=off|GRAPH_BACKEND=firestore|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
...
>> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app
```

**`step_02_does_the_candidate_answer_as_the_same_buil(session)` — The candidate gate: a revision with no traffic, judged before any user meets it / Do it: does the candidate answer as the same build?**

This is the workflow's check, by hand: /version on the live URL and on the tag URL, both with a token minted for the live one.

Operation: bash — run in the operator shell (two GETs: the live revision and the candidate).

Expected shape, not a promised result:

```text
https://documind-api-NUMBER.asia-south1.run.app/version
  git_sha COMMIT | generator gemini-3.6-flash | prompt documind-rag@v3
https://candidate---documind-api-NUMBER.asia-south1.run.app/version
  git_sha COMMIT | generator gemini-3.6-flash | prompt documind-rag@v3
```

**`step_03_the_gate_on_the_candidate(session)` — The candidate gate: a revision with no traffic, judged before any user meets it / Do it: the gate on the candidate**

Do it: the gate on the candidate

Operation: bash — run in the operator shell, in the kit (every row as the member, every isolation row as the outsider: about ten minutes).

IDE adaptation: Run the candidate's gate through live_gate: its exit is the release decision the page reads, 0 or a red 2, and the demo must go on to the next step and the cleanup that removes the candidate's tag. Before lesson 7.5's video, mm-03 keeps a full gate red (21 October 2026 the tag was left behind). A missing report or an HTTP/auth failure still fails.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/candidate_gate.txt]
```

**`step_04_the_gate_on_the_candidate(session)` — The candidate gate: a revision with no traffic, judged before any user meets it / Do it: the gate on the candidate**

Now read the report as a release decision: how many thresholds were judged, what the outsider got, and each required row.

Operation: bash — run in the operator shell, in the kit (reads the report; changes nothing).

Expected shape, not a promised result:

```text
https://candidate---documind-api-NUMBER.asia-south1.run.app
  thresholds judged: 9 of 9; failed: none
  the outsider: isolation_403_rate 100%; let in on: no row
  required rows: 15 of 15 passed
    iso-01  isolation  zeta    pass
    iso-02  isolation  globex  pass
    iso-03  isolation  globex  pass
    iso-04  isolation  zeta    pass
    iso-05  isolation  zeta    pass
    iso-06  isolation  globex  pass
    iso-07  isolation  globex  pass
    iso-08  isolation  zeta    pass
    iso-09  isolation  zeta    pass
    iso-10  isolation  globex  pass
    mm-01   lookup     acme    pass
    mm-02   lookup     acme    pass
    mm-03   lookup     acme    pass
    mm-04   isolation  zeta    pass
    vr-01   version    acme    pass
  leaks 0, stale 0: the gate's exit was 0
```

**`step_05_remove_the_candidate(session)` — The candidate gate: a revision with no traffic, judged before any user meets it / Do it: remove the candidate**

The candidate has done its job. Removing its tag ends its URL. Deleting .candidate-revision means a stray make promote stops with an error instead of moving traffic to it; lesson 4.4 explains why both are needed.

Operation: bash — run in the operator shell, in the kit (the candidate's tag and its recorded name removed; the live revision is untouched).

Expected shape, not a promised result:

```text
...
the candidate URL now: HTTP 404
```

### demo_05_live_traffic_the_usage_rows_and_the_gate_s_rows_among_them.py

The cell reads the last day's query and stream rows with the label make usage drops, the revision, and marks the revision that serves traffic now. Then it counts the rows by caller, and checks the eval identity's rows on a revision with no traffic against golden.jsonl. Do it: the same rows, as make usage groups them

**`step_01_the_rows_split_by_revision_and_by_caller(session)` — Live traffic: the usage rows, and the gate's rows among them / Do it: the rows, split by revision and by caller**

The cell reads the last day's query and stream rows with the label make usage drops, the revision, and marks the revision that serves traffic now. Then it counts the rows by caller, and checks the eval identity's rows on a revision with no traffic against golden.jsonl.

Operation: bash — run in the operator shell, in the kit (one Cloud Logging read and one describe; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rows_by_revision.txt]
```

**`step_02_the_same_rows_as_make_usage_groups_them(session)` — Live traffic: the usage rows, and the gate's rows among them / Do it: the same rows, as make usage groups them**

Do it: the same rows, as make usage groups them

Operation: bash — run in the operator shell, in the kit (the same rows, as make usage groups them).

Expected shape, not a promised result:

```text
python evals/usage_rows.py --project documind-ai-YOUR-ID --hours ${HOURS:-24}
NN answers from documind-api in the last 24 h; USD_INR=85

by tenant
tenant                 answers    tok_in  tok_out       USD       INR  p95 ms  unans
------------------------------------------------------------------------------------
...

by model and backend (what answered, through which door)
model                 model_backend          answers    tok_in  tok_out       USD       INR  p95 ms  unans
----------------------------------------------------------------------------------------------------------
...

by brain (8.7's question, from the row)
brain                  answers    tok_in  tok_out       USD       INR  p95 ms  unans
------------------------------------------------------------------------------------
...

by surface
event                  answers    tok_in  tok_out       USD       INR  p95 ms  unans
------------------------------------------------------------------------------------
...

by retrieval backend (which store served the pool; 13 September 2026)
retrieval_backend      answers    tok_in  tok_out       USD       INR  p95 ms  unans
------------------------------------------------------------------------------------
...

where the time went (p95 per stage, by tenant)
tenant                 answers  p95 ms  retrieve  rerank  generate   pool
-------------------------------------------------------------------------
...
```

### demo_06_the_stream_s_row_answerable_unless_the_pool_was_empty.py

The cell streams rf-01's question for acme as the eval identity, prints what the stream said, then waits for the row in Cloud Logging and prints its verdict. If you asked the same question in the UI in step 5, it prints your row too, without your email.

**`step_01_one_refusal_through_the_stream_and_its_row(session)` — The stream's row: answerable, unless the pool was empty / Do it: one refusal through the stream, and its row**

The cell streams rf-01's question for acme as the eval identity, prints what the stream said, then waits for the row in Cloud Logging and prints its verdict. If you asked the same question in the UI in step 5, it prints your row too, without your email.

Operation: bash — run in the operator shell, in the kit (one streamed answer, then its row from Cloud Logging).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/stream_refusal.txt]
```

### demo_07_the_alert_s_own_inputs_two_log_metrics_two_policies_and_the_windows_they_saw.py

The cell reads each metric's filter from Cloud Logging, both policies from Cloud Monitoring, and each metric's counts per tenant over the last six hours, aligned the way the policy aligns them. Then it divides, window by window.

**`step_01_the_metrics_the_policies_and_the_windows(session)` — The alert's own inputs: two log metrics, two policies, and the windows they saw / Do it: the metrics, the policies, and the windows**

The cell reads each metric's filter from Cloud Logging, both policies from Cloud Monitoring, and each metric's counts per tenant over the last six hours, aligned the way the policy aligns them. Then it divides, window by window.

Operation: bash — run in the operator shell (two Cloud Logging reads and three Cloud Monitoring reads; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/alert_series.txt]
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's step 6 needs acme's questions answered from the kit's own index, so point acme at it for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's step 6 needs acme's questions answered from the kit's own index, so point acme at it for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_4.3_Placing_Evals_WIX.html`. All 45 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `67bf859b284dfdb4ca8a5cfa8db03e338447995e`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
