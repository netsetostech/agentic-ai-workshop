# Lesson 3.5: Generate structured answers, citations and refusals

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_contract_offline_drafts_that_pass_drafts_that_fail_and_the_resolver_on_the_k.py](demo_03_the_contract_offline_drafts_that_pass_drafts_that_fail_and_the_resolver_on_the_k.py) | The contract offline: drafts that pass, drafts that fail, and the resolver on the kit's chunks |
| 4 | [demo_04_one_answer_from_the_lane_field_by_field_with_every_quote_checked_against_its_row.py](demo_04_one_answer_from_the_lane_field_by_field_with_every_quote_checked_against_its_row.py) | One answer from the lane, field by field, with every quote checked against its row |
| 5 | [demo_05_three_refusals_the_model_s_twice_the_api_s_once_and_how_their_envelopes_differ.py](demo_05_three_refusals_the_model_s_twice_the_api_s_once_and_how_their_envelopes_differ.py) | Three refusals: the model's twice, the API's once, and how their envelopes differ |
| 6 | [demo_06_the_model_call_by_hand_the_schema_the_thinking_the_usage_the_price.py](demo_06_the_model_call_by_hand_the_schema_the_thinking_the_usage_the_price.py) | The model call by hand: the schema, the thinking, the usage, the price |
| 7 | [demo_07_the_model_as_a_setting_the_global_client_a_tuned_endpoint_a_pin_and_a_router.py](demo_07_the_model_as_a_setting_the_global_client_a_tuned_endpoint_a_pin_and_a_router.py) | The model as a setting: the global client, a tuned endpoint, a pin and a router |
| 8 | [demo_08_what_an_answer_costs_and_the_failure_that_is_not_a_refusal.py](demo_08_what_an_answer_costs_and_the_failure_that_is_not_a_refusal.py) | What an answer costs, and the failure that is not a refusal |

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The model, its location, the tuned base, the router, the backend, the prompt version and the answer's reserve live in the API's environment, each with a default the page names; a name the service does not set is unset rather than exported empty, because steps 3 and 6 import the kit. /version says what is actually serving.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine. Temporarily disable an enabled answer cache for this retrieval/generation experiment and save its prior value. This changes the shared API; finish restores it. Cache lessons in Module 6 are unaffected.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The model, its location, the tuned base, the router, the backend, the prompt version and the answer's reserve live in the API's environment, each with a default the page names; a name the service does not set is unset rather than exported empty, because steps 3 and 6 import the kit. /version says what is actually serving.

Operation: bash — run in the operator shell, in $DEMO_ROOT, once per shell.

IDE adaptation: Read literal environment values as JSON from the serving revision; absent keys are unset. Repeated text parsing is removed.

Expected shape, not a promised result:

```text
model: gemini-3.6-flash (default)  location: from the model: global for a name  base: none, no tuned endpoint
routing: off (default)  backend: vertex (default)  prompt: v3 (default)  answer: 2,048 (default)
version: gemini-3.6-flash | documind-rag@v3 | vertex
```

### demo_03_the_contract_offline_drafts_that_pass_drafts_that_fail_and_the_resolver_on_the_k.py

Do it: six drafts, one resolution, two refusals

**`step_01_six_drafts_one_resolution_two_refusals(session)` — The contract offline: drafts that pass, drafts that fail, and the resolver on the kit's chunks / Do it: six drafts, one resolution, two refusals**

Do it: six drafts, one resolution, two refusals

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: nothing leaves the machine).

Expected shape, not a promised result:

```text
resolved: 2 of 3 citations kept: source 7 was out of range and dropped, not raised
   acme:hr_policy_2026#NP-03      page 1 score 0.0 kind text quote 'NP-03 — Notice period A confirmed employee a'
   acme:hr_policy_2026#PB-02      page 1 score 0.0 kind text quote 'PB-02 — Probation New joiners serve six mont'
RAGAnswer: {"answer": "A confirmed employee in grade E3 serves the notice period in NP-03 [1]; probation is different [2].", "citations": [{" ...
refused (source 0, [Source N] is 1-based): citations.0.source: Input should be greater than or equal to 1
refused (confidence outside high|medium|low): confidence: Input should be 'high', 'medium' or 'low'
refused (a quote over the draft's limit): citations.0.quote: String should have at most 200 characters
the model's refusal, resolved: {'answer': 'The context does not contain the answer.', 'citations': [], 'confidence': 'low', 'answerable': False}
the empty pool's, written by the API without a model: The corpus holds nothing near this question: no passage of this tenant's current documents was r ...
```

### demo_04_one_answer_from_the_lane_field_by_field_with_every_quote_checked_against_its_row.py

Do it: one question, two halves, three rows

**`step_01_one_question_two_halves_three_rows(session)` — One answer from the lane, field by field, with every quote checked against its row / Do it: one question, two halves, three rows**

Do it: one question, two halves, three rows

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; one question and three Firestore reads, a rupee).

Expected shape, not a promised result:

```text
the contract: {"answer": "A confirmed employee in grade E3 must serve a notice period of ... [1]...", "citations": "3 citations", "confidence": "high", "answerable": true}
the envelope: {'model': 'gemini-3.6-flash', 'backend': 'vertex', 'tokens_in': 1xxx, 'tokens_out': 4xx, 'cached_tokens': 0, 'cost_usd': 0.00xxxx, 'latency_ms': 2xxx, 'cache_hit': 'none'}
[N] marks in the answer: ['1', '2', '3'] | citations returned: 3
   [1] #  1 hr_policy_2026.md        page None score 0.9xxx kind text | row found True | quote in the row True | 1x words
   [2] #  4 hr_policy_2026.md        page None score 0.8xxx kind text | row found True | quote in the row True | 1x words
   [3] #  2 hr_policy_2026.md        page None score 0.6xxx kind text | row found True | quote in the row True | 1x words
```

### demo_05_three_refusals_the_model_s_twice_the_api_s_once_and_how_their_envelopes_differ.py

Do it: three questions, three envelopes, three rows

**`step_01_three_questions_three_envelopes_three_rows(session)` — Three refusals: the model's twice, the API's once, and how their envelopes differ / Do it: three questions, three envelopes, three rows**

Do it: three questions, three envelopes, three rows

Operation: bash — run in the operator shell (three questions, two of them model calls: a rupee; one log read).

Expected shape, not a promised result:

```text
answerable False | confidence low | citations 0 | backend vertex | tokens 1xxx + 1xx | cost_usd 0.00xxxx | pool 20 | The provided context does not contain information about Globex's not
answerable False | confidence low | citations 0 | backend vertex | tokens 1xxx + 1xx | cost_usd 0.00xxxx | pool 20 | The context covers FY2025 and FY2026; it does not state the revenue f
answerable False | confidence low | citations 0 | backend none | tokens 0 + 0 | cost_usd 0.0 | pool 0 | The corpus holds nothing near this question: no passage of this tena
acme	False	none	0	0.0
acme	False	vertex	1xxx	0.00xxxx
globex	False	vertex	1xxx	0.00xxxx
```

### demo_06_the_model_call_by_hand_the_schema_the_thinking_the_usage_the_price.py

Do it: the same call, from the shell

**`step_01_the_same_call_from_the_shell(session)` — The model call by hand: the schema, the thinking, the usage, the price / Do it: the same call, from the shell**

Do it: the same call, from the shell

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; one model call at the generator's rate, a few paise).

Expected shape, not a promised result:

```text
finish: STOP | the draft: {"answer": "A confirmed employee in grade E3 ... [1]", "citations": [{"source": 1, "quote": "..."}], "confidence": "high", "answerable": true} ...
resolved: [('acme:hr_policy_2026#NP-03', 1, 0.0)] | answerable True | confidence high
usage: prompt 4xx | candidates 1xx | thoughts xxx | cached 0
priced as the API would: $0.00xxxx = Rs 0.xxxx at 85.0
```

### demo_07_the_model_as_a_setting_the_global_client_a_tuned_endpoint_a_pin_and_a_router.py

Read the lane, Rs 0

**`step_01_read_the_lane_rs_0(session)` — The model as a setting: the global client, a tuned endpoint, a pin and a router / Read the lane, Rs 0**

Read the lane, Rs 0

Operation: bash — run in the operator shell, in $DEMO_ROOT (three reads).

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
acme's tenant_settings: {'generator_model': None, 'model_backend': None, 'retrieval_backend': 'vector', 'data_region': 'any'}
```

### demo_08_what_an_answer_costs_and_the_failure_that_is_not_a_refusal.py

The code

**`step_01_the_code(session)` — What an answer costs, and the failure that is not a refusal / The code**

The code

Operation: bash — run in the operator shell (one new revision, no traffic; one question that fails on purpose; one log read; the undo).

Expected shape, not a promised result:

```text
HTTP 502
{"detail":"generation produced no parseable answer (MAX_TOKENS)"}
2026-09-2xT1x:xx:xx.xxxxxxZ	generation_unparsed			MAX_TOKENS
2026-09-2xT1x:xx:xx.xxxxxxZ	generation_truncated	16	1x
template now:
(empty means unset: the default, 2048)
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_3.5_Structured_Answers_WIX.html`. All 37 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `be4ba0adff0eefafe272eebc8c9d04137e150d3b`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
