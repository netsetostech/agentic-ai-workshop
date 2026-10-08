# Lesson 3.4: Pack evidence within the context budget

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_budget_s_lines_and_the_packer_offline_on_the_kit_s_own_documents.py](demo_03_the_budget_s_lines_and_the_packer_offline_on_the_kit_s_own_documents.py) | The budget's lines and the packer, offline on the kit's own documents |
| 4 | [demo_04_the_model_s_counter_beside_the_estimate_english_hindi_and_a_pool_trimmed_by_the.py](demo_04_the_model_s_counter_beside_the_estimate_english_hindi_and_a_pool_trimmed_by_the.py) | The model's counter beside the estimate: English, Hindi, and a pool trimmed by the exact count |
| 5 | [demo_05_one_answer_s_tokens_the_packed_set_s_estimate_the_model_s_count_and_the_price.py](demo_05_one_answer_s_tokens_the_packed_set_s_estimate_the_model_s_count_and_the_price.py) | One answer's tokens: the packed set's estimate, the model's count, and the price |
| 6 | [demo_06_a_dated_document_on_the_lane_the_header_s_date_the_rule_in_the_prompt_the_citati.py](demo_06_a_dated_document_on_the_lane_the_header_s_date_the_rule_in_the_prompt_the_citati.py) | A dated document on the lane: the header's date, the rule in the prompt, the citation event |
| 7 | [demo_07_the_answer_s_reserve_the_retry_and_the_tokens_on_the_rows.py](demo_07_the_answer_s_reserve_the_retry_and_the_tokens_on_the_rows.py) | The answer's reserve, the retry, and the tokens on the rows |
| 8 | [demo_08_what_the_budget_costs_the_knob_on_a_candidate_and_the_lines_this_lesson_leaves_e.py](demo_08_what_the_budget_costs_the_knob_on_a_candidate_and_the_lines_this_lesson_leaves_e.py) | What the budget costs, the knob on a candidate, and the lines this lesson leaves empty |

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The budget's total, the answer's reserve, the model and the rupee rate live in the API's environment, each with a default the page names; a name the service does not set is unset rather than exported empty, because steps 4 and 5 import the kit and its settings class reads an empty variable as a value.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine. Temporarily disable an enabled answer cache for this retrieval/generation experiment and save its prior value. This changes the shared API; finish restores it. Cache lessons in Module 6 are unaffected.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The budget's total, the answer's reserve, the model and the rupee rate live in the API's environment, each with a default the page names; a name the service does not set is unset rather than exported empty, because steps 4 and 5 import the kit and its settings class reads an empty variable as a value.

Operation: bash — run in the operator shell, in $DEMO_ROOT, once per shell.

IDE adaptation: Read literal environment values as JSON from the serving revision; absent keys are unset. Repeated text parsing is removed.

Expected shape, not a promised result:

```text
context: 8000 (default)  answer: 2048 (default)  model: gemini-3.6-flash (default)  prompt: v3 (default)  usd_inr: 85 (default)
```

### demo_03_the_budget_s_lines_and_the_packer_offline_on_the_kit_s_own_documents.py

Do it: the lines, then two pools twice, then a counter

**`step_01_the_lines_then_two_pools_twice_then_a_coun(session)` — The budget's lines and the packer, offline on the kit's own documents / Do it: the lines, then two pools twice, then a counter**

Do it: the lines, then two pools twice, then a counter

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: nothing leaves the machine).

Expected shape, not a promised result:

```text
4.5's teaching split: system 1500 | tenant_pack 40000 | chunks 6000 | history 2000 | answer 2000 | input_total 49500
the API's, this question: system 168 (the fixed prompt, 672 characters) | chunks 7832 | tenant_pack 0 | history 0 | answer 2048 | input_total 8000

handbook sections, top_k 5: packed 5, dropped 0, context 301 tokens | the dated rule is added
   [Source 1] hr_policy_2026.md, p.1, NP-03 — Notice period  (72 tokens)
   [Source 2] smoke_note.md, p.1, effective from 2026-10-01  (66 tokens)
   [Source 3] hr_policy_2026.md, p.1  (32 tokens)

handbook sections, top_k 20: packed 20, dropped 0, context 2009 tokens | the dated rule is added
   [Source 1] hr_policy_2026.md, p.1, NP-03 — Notice period  (72 tokens)
   [Source 2] smoke_note.md, p.1, effective from 2026-10-01  (66 tokens)
   [Source 3] hr_policy_2026.md, p.1  (32 tokens)

full Act pages, top_k 5: packed 5, dropped 0, context 1667 tokens | the dated rule is added
   [Source 1] hr_policy_2026.md, p.1, NP-03 — Notice period  (72 tokens)
   [Source 2] smoke_note.md, p.1, effective from 2026-10-01  (66 tokens)
   [Source 3] cgst_act_2017.md, p.116  (508 tokens)

full Act pages, top_k 20: packed 17, dropped 3, context 7774 tokens | log: context_budget_drop packed=17 dropped=3 | the dated rule is added
   [Source 1] hr_policy_2026.md, p.1, NP-03 — Notice period  (72 tokens)
   [Source 2] smoke_note.md, p.1, effective from 2026-10-01  (66 tokens)
   [Source 3] cgst_act_2017.md, p.116  (508 tokens)

full Act pages, top_k 20, with a counter injected that reads 60 percent more: packed 11, dropped 9, trimmed from the tail after the estimate had packed them
```

### demo_04_the_model_s_counter_beside_the_estimate_english_hindi_and_a_pool_trimmed_by_the.py

Do it: three texts, two counters, one pool twice

**`step_01_three_texts_two_counters_one_pool_twice(session)` — The model's counter beside the estimate: English, Hindi, and a pool trimmed by the exact count / Do it: three texts, two counters, one pool twice**

Do it: three texts, two counters, one pool twice

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; a handful of count_tokens calls).

Expected shape, not a promised result:

```text
NP-03, English     chars   234  estimate  58  counted  1xx  ratio x.xx  (near one)
a clause in Hindi  chars    72  estimate   18  counted   xx  ratio x.xx  (well above one)
one Act page       chars  2000  estimate  500  counted  4xx  ratio x.xx  (near one)
twenty Act pages under the estimate     : packed 15, dropped 5, context 7633 tokens by that counter
twenty Act pages under the model's count: packed 1x, dropped x, context 7xxx tokens by that counter
```

### demo_05_one_answer_s_tokens_the_packed_set_s_estimate_the_model_s_count_and_the_price.py

Do it: one question, its tokens, its price, and the estimate beside it

**`step_01_one_question_its_tokens_its_price_and_the(session)` — One answer's tokens: the packed set's estimate, the model's count, and the price / Do it: one question, its tokens, its price, and the estimate beside it**

Do it: one question, its tokens, its price, and the estimate beside it

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; one question, a rupee).

Expected shape, not a promised result:

```text
the answer: tokens_in 1xxx | cached_tokens 0 | tokens_out 4xx | cost_usd 0.00xxxx | citations 3 | model gemini-3.6-flash
cost.price(): $0.00xxxx = Rs 0.xxxx at 85.0 | in 1xxx out 4xx cached 0
the estimate for the same packed set: fixed 168 + context 8xx = 1xxx | the model counted 1xxx | ratio 0.9x
```

### demo_06_a_dated_document_on_the_lane_the_header_s_date_the_rule_in_the_prompt_the_citati.py

Do it: the dated revision in, the stream read, revision 1 back

**`step_01_the_dated_revision_in_the_stream_read_revi(session)` — A dated document on the lane: the header's date, the rule in the prompt, the citation event / Do it: the dated revision in, the stream read, revision 1 back**

Do it: the dated revision in, the stream read, revision 1 back

Operation: bash — run in the operator shell, in $DEMO_ROOT (one upload, one streamed question, one upload; paise).

Expected shape, not a promised result:

```text
>> event chunks embedded effective_from: ingest_reactivated	3	0	2026-10-01
citation 1 smoke_note.md | effective_from 2026-10-01 | quote 'The smoke lantern is kept in bay 7 of the Pune wa'
done: tokens_in 1xxx | tokens_out 3xx | latency_ms 2xxx | the price is on the row, not in the event
answer: The smoke lantern is kept in bay 7 of the Pune warehouse [1], effective from 1 October 2026 ...
>> event chunks embedded effective_from: ingest_reactivated	3	0	None
```

### demo_07_the_answer_s_reserve_the_retry_and_the_tokens_on_the_rows.py

Do it: the day's tokens, and the retries there were not

**`step_01_the_day_s_tokens_and_the_retries_there_wer(session)` — The answer's reserve, the retry, and the tokens on the rows / Do it: the day's tokens, and the retries there were not**

Do it: the day's tokens, and the retries there were not

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: two log reads).

Expected shape, not a promised result:

```text
by tenant
tenant                 answers    tok_in  tok_out       USD       INR  p95 ms  unans
------------------------------------------------------------------------------------
acme                        NN     xxxxx     xxxx    0.0xxx      x.xx    4xxx   0.0x
2026-09-2xT1x:xx:xx.xxxxxxZ	context_budget_drop		1x	x
```

### demo_08_what_the_budget_costs_the_knob_on_a_candidate_and_the_lines_this_lesson_leaves_e.py

max_context_tokens is a setting, so the way to see the drop on the live corpus without touching the live service is a candidate revision, as in lessons 2.2 to 2.4: a budget of 600 tokens leaves room for about three handbook sections after the fixed prompt, so the same question at top_k 5 packs three, drops two, logs the drop, and answers from what it packed. The variable is not set on the live service, so the undo removes it and the default returns.

**`step_01_the_knob_a_budget_too_small_on_a_candidate(session)` — What the budget costs, the knob on a candidate, and the lines this lesson leaves empty / The knob: a budget too small, on a candidate that takes no traffic**

max_context_tokens is a setting, so the way to see the drop on the live corpus without touching the live service is a candidate revision, as in lessons 2.2 to 2.4: a budget of 600 tokens leaves room for about three handbook sections after the fixed prompt, so the same question at top_k 5 packs three, drops two, logs the drop, and answers from what it packed. The variable is not set on the live service, so the undo removes it and the default returns.

Operation: bash — run in the operator shell (one new revision, no traffic; one question; one log read; then the undo).

Expected shape, not a promised result:

```text
candidate: tokens_in 6xx | citations 2 | answerable True | pool 20
2026-09-2xT1x:xx:xx.xxxxxxZ	3	2
template now:
(empty means unset: the default, 8000)
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_3.4_Context_Budget_WIX.html`. All 35 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `451850344630a66cad10a9fdc60c7712b39b2c4f`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
