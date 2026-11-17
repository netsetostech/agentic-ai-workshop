# Lesson 5.1: Understand tool contracts and the direct agent loop

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_chat_service_in_your_lane_s_region.py](demo_03_the_chat_service_in_your_lane_s_region.py) | The chat service, in your lane's region |
| 4 | [demo_04_the_contract_what_the_model_reads_of_each_tool.py](demo_04_the_contract_what_the_model_reads_of_each_tool.py) | The contract: what the model reads of each tool |
| 5 | [demo_05_the_one_retrieve_from_your_shell.py](demo_05_the_one_retrieve_from_your_shell.py) | The one retrieve(), from your shell |
| 6 | [demo_06_the_direct_brain_one_retrieve_no_loop.py](demo_06_the_direct_brain_one_retrieve_no_loop.py) | The direct brain: one retrieve(), no loop |
| 7 | [demo_07_the_loop_the_model_chooses_its_tools.py](demo_07_the_loop_the_model_chooses_its_tools.py) | The loop: the model chooses its tools |
| 8 | [demo_08_the_rows_what_each_brain_cost_and_which_row_records_it.py](demo_08_the_rows_what_each_brain_cost_and_which_row_records_it.py) | The rows: what each brain cost, and which row records it |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Optional extensions

- [optional/demo_07_the_loop_the_model_chooses_its_tools.py](optional/demo_07_the_loop_the_model_chooses_its_tools.py) — The scripted model always asks for both searches. Whether Gemini does is the model's choice. This cell makes the first model call of a turn by hand: the brains' own model from shared/profile.py, the kit's two tools bound to it, the system prompt, and the same two-part question. It prints the tool calls in the one message that comes back, then the tokens and the rupees. It is one call to gemini-3.6-flash on your project, under a rupee. No tool runs, and rag-api is not called.

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

### demo_03_the_chat_service_in_your_lane_s_region.py

Do it: deploy Do it: where it points, and its brains

**`step_01_deploy(session)` — The chat service, in your lane's region / Do it: deploy**

Do it: deploy

Operation: bash — run in the operator shell, in the kit (the chat service built and deployed in your region; several minutes).

Expected shape, not a promised result:

```text
>> commands/lesson-12.8.sh (DEPLOY block)
Creating temporary archive of ... file(s) totalling ... MiB before compression.
...
DONE ... asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/chat:COMMIT
Deploying container to Cloud Run service [documind-chat] in project [documind-ai-YOUR-ID] region [asia-south1]
...
Service URL: https://documind-chat-NUMBER.asia-south1.run.app
Updated IAM policy for service [documind-chat].   (seven times, one per account: documind-ui-sa, documind-outsider-sa, documind-evalacme-sa,
   documind-evalzeta-sa, documind-evalglobex-sa, documind-evalleaver-sa,
   documind-evalgrc-sa)
>> documind-gchat-sa does not exist yet (terraform/desk.tf: make plan up; documind-gchat-sa only with GCHAT_DOOR=true) - not bound
Job [documind-checkpoint-setup] has successfully been deployed.
Execution [documind-checkpoint-setup-xxxxx] has successfully completed.
...
>> you@example.com may mint tokens as documind-ui-sa
>> you@example.com may mint tokens as documind-outsider-sa
```

**`step_02_where_it_points_and_its_brains(session)` — The chat service, in your lane's region / Do it: where it points, and its brains**

Do it: where it points, and its brains

Operation: bash — run in the operator shell, in the kit (where the chat service points, and its brains).

Expected shape, not a promised result:

```text
RAG_API_URL https://documind-api-NUMBER.asia-south1.run.app | SELF_URL https://documind-chat-NUMBER.asia-south1.run.app | DOCUMIND_BRAIN langchain
{"status":"ok","profile":"gcp","brains":["langchain","langgraph","adk","direct"],"default_brain":"langchain","limits":{"max_model_calls":12,"budget_inr":5.0,"deadline_s":100.0,"model_timeout_s":30.0,"model_attempts":2,"min_model_s":5.0,"tool_budgets_s":{"retrieve":95.0,"calculate_processing_cost":10}}}
```

### demo_04_the_contract_what_the_model_reads_of_each_tool.py

Do it

**`step_01_the_contract_what_the_model_reads_of_each(session)` — The contract: what the model reads of each tool / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (what the model reads of each tool; reads the source, installs nothing).

Expected shape, not a promised result:

```text
retrieve(query: str, doc_type: str = 'all', top_k: int = 5)    hidden: runtime
      Retrieve grounded passages from DocuMind's corpus.
  calculate_processing_cost(total_pages: int, num_documents: int = 1, processing_type: str = 'standard')
      Estimate document processing cost in USD and INR.
  'express' refused: unknown tier 'express'; expected one of ['bulk', 'priority', 'standard']
```

### demo_05_the_one_retrieve_from_your_shell.py

Do it

**`step_01_the_one_retrieve_from_your_shell(session)` — The one retrieve(), from your shell / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the one retrieve(), called from your shell as a roster member).

Expected shape, not a promised result:

```text
1 citations | answerable True | confidence high | 2.7 s
  first: {'chunk_id': 'acme:aaaaaaaa#0', 'page': 3, 'score': 0.94}
  rag-api's own answer: Gratuity is payable on termination after not less than five years of continuous service [1
```

### demo_06_the_direct_brain_one_retrieve_no_loop.py

Do it

**`step_01_the_direct_brain_one_retrieve_no_loop(session)` — The direct brain: one retrieve(), no loop / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (a small chat function, and the direct brain).

Expected shape, not a promised result:

```text
direct    tool_calls ['retrieve']  refusals []  citations 1  3180 ms
      Gratuity is payable on termination after not less than five years of continuous service [1].
```

### demo_07_the_loop_the_model_chooses_its_tools.py

Do it The cell runs the kit's own LangChain brain on your machine, with a scripted model and a stand-in rag-api, so it calls nothing on your lane and costs nothing. The model asks for two searches in one message: the notice period, and the earned leave encashed on exit. The stand-in takes 1.5 seconds over the first and 1 second over the second, and both answers include LV-07, the handbook's clause on leave at exit. The cell prints when each search reached the stand-in and when it was answered, the citations each result carried, and the turn's list and citations. It runs in ~/graph-venv, lesson 5.4's venv with the chat image's pins, and the first cell makes it if it is missing.

**`step_01_the_loop_the_model_chooses_its_tools(session)` — The loop: the model chooses its tools / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the LangChain loop on the same question, then a cost question on both brains).

Expected shape, not a promised result:

```text
langchain tool_calls ['retrieve']  refusals []  citations 1 n [1]  7240 ms
      After five years of continuous service, under the Payment of Gratuity Act, 1972 [1].
  langchain tool_calls ['retrieve', 'calculate_processing_cost']  refusals []  citations 1 n [1]  11350 ms
      The handbook has 283 pages [1]. At the priority tier (USD 0.12 a page) they cost USD 33.96, abou
  direct    tool_calls ['retrieve']  refusals []  citations 1  3420 ms
      The documents give no per-page price for processing the handbook; the April invoice bills priori
```

**`step_02_two_searches_at_once_offline(session)` — The loop: the model chooses its tools / Do it: two searches at once, offline**

The cell runs the kit's own LangChain brain on your machine, with a scripted model and a stand-in rag-api, so it calls nothing on your lane and costs nothing. The model asks for two searches in one message: the notice period, and the earned leave encashed on exit. The stand-in takes 1.5 seconds over the first and 1 second over the second, and both answers include LV-07, the handbook's clause on leave at exit. The cell prints when each search reached the stand-in and when it was answered, the citations each result carried, and the turn's list and citations. It runs in ~/graph-venv, lesson 5.4's venv with the chat image's pins, and the first cell makes it if it is missing.

Operation: bash — run in the operator shell, in the kit (lesson 5.4's ~/graph-venv with the chat image's pins; a minute the first time).

Expected shape, not a promised result:

```text
graph-venv ok: langchain 1.4.0
```

**`step_03_two_searches_at_once_offline(session)` — The loop: the model chooses its tools / Do it: two searches at once, offline**

The cell runs the kit's own LangChain brain on your machine, with a scripted model and a stand-in rag-api, so it calls nothing on your lane and costs nothing. The model asks for two searches in one message: the notice period, and the earned leave encashed on exit. The stand-in takes 1.5 seconds over the first and 1 second over the second, and both answers include LV-07, the handbook's clause on leave at exit. The cell prints when each search reached the stand-in and when it was answered, the citations each result carried, and the turn's list and citations. It runs in ~/graph-venv, lesson 5.4's venv with the chat image's pins, and the first cell makes it if it is missing.

Operation: bash — run in the operator shell, in the kit (the kit's LangChain brain on your machine: a scripted model, a stand-in rag-api; no lane, no cost).

Expected shape, not a promised result:

```text
one model message asked for 2 searches; the stand-in rag-api's log:
    'notice period'                   arrived at 0.0 s, answered at 1.5 s
    'earned leave encashed on exit'   arrived at 0.0 s, answered at 1.0 s
  at once: True (both arrived before either was answered); 1.5 s for the two, where one after the other takes 2.5 s
  what the model read, one result for each call:
    'notice period'                   [3] NP-03  [4] PB-02  [1] LV-07
    'earned leave encashed on exit'   [1] LV-07  [2] LV-01
  tool_calls ['retrieve', 'retrieve']; the turn's citations: [1] LV-07, [2] LV-01, [3] NP-03, [4] PB-02
  the answer: Sixty days [3]; at most 45 days of earned leave are encashed [1].
```

### optional/demo_07_the_loop_the_model_chooses_its_tools.py

The scripted model always asks for both searches. Whether Gemini does is the model's choice. This cell makes the first model call of a turn by hand: the brains' own model from shared/profile.py, the kit's two tools bound to it, the system prompt, and the same two-part question. It prints the tool calls in the one message that comes back, then the tokens and the rupees. It is one call to gemini-3.6-flash on your project, under a rupee. No tool runs, and rag-api is not called.

**`step_01_optional_does_gemini_ask_for_two_at_once(session)` — The loop: the model chooses its tools / Optional: does Gemini ask for two at once?**

The scripted model always asks for both searches. Whether Gemini does is the model's choice. This cell makes the first model call of a turn by hand: the brains' own model from shared/profile.py, the kit's two tools bound to it, the system prompt, and the same two-part question. It prints the tool calls in the one message that comes back, then the tokens and the rupees. It is one call to gemini-3.6-flash on your project, under a rupee. No tool runs, and rag-api is not called.

Operation: bash — optional: run in the operator shell, in the kit (one Gemini call with the kit's two tools; no tool runs; under a rupee).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/parallel_live.txt]
```

### demo_08_the_rows_what_each_brain_cost_and_which_row_records_it.py

rag-api's row for every retrieve(), and the chat service's row for every turn. Each retrieve() posts to rag-api's /v1/query, and rag-api writes its usage row, now labelled with the brain that asked. The chat service writes a row of its own for each turn: the brain, the tenant, the user, the session, the time and the two lists, and the turn's own model calls, their tokens and their cost, beside what its searches billed. Lesson 5.5 shows the limits those numbers are counted against. The cell reads both kinds since step 5, the shell's own retrieval included, labelled ui because it named no brain.

**`step_01_the_rows_what_each_brain_cost_and_which_ro(session)` — The rows: what each brain cost, and which row records it / The rows: what each brain cost, and which row records it**

rag-api's row for every retrieve(), and the chat service's row for every turn. Each retrieve() posts to rag-api's /v1/query, and rag-api writes its usage row, now labelled with the brain that asked. The chat service writes a row of its own for each turn: the brain, the tenant, the user, the session, the time and the two lists, and the turn's own model calls, their tokens and their cost, beside what its searches billed. Lesson 5.5 shows the limits those numbers are counted against. The cell reads both kinds since step 5, the shell's own retrieval included, labelled ui because it named no brain.

Operation: bash — run in the operator shell, in the kit (the rows both services wrote since the retrieve cell; reads only).

Expected shape, not a promised result:

```text
rag-api, one row per retrieve():
    brain ui         in   1790  out   96  Rs 0.2894   2600 ms
    brain direct     in   1790  out   96  Rs 0.2894   2710 ms
    brain langchain  in   1812  out  101  Rs 0.2954   2840 ms
    brain langchain  in   1650  out   88  Rs 0.2665   2390 ms
    brain direct     in   1705  out   92  Rs 0.2760   2620 ms
  the chat service, one row per turn:
    brain direct     tool_calls ['retrieve']    3180 ms  (keys: brain, budget_inr, cached_tokens, cost_usd, event, latency_ms, max_model_calls, model, model_calls, rag_cost_usd, refusals, session_id, stopped_by, surface, tenant, tokens_in, tokens_out, tool_calls, tool_timeouts, user)
    brain langchain  tool_calls ['retrieve']    7240 ms  (keys: brain, budget_inr, cached_tokens, cost_usd, event, latency_ms, max_model_calls, model, model_calls, rag_cost_usd, refusals, session_id, stopped_by, surface, tenant, tokens_in, tokens_out, tool_calls, tool_timeouts, user)
    brain langchain  tool_calls ['retrieve', 'calculate_processing_cost']   11350 ms  (keys: brain, budget_inr, cached_tokens, cost_usd, event, latency_ms, max_model_calls, model, model_calls, rag_cost_usd, refusals, session_id, stopped_by, surface, tenant, tokens_in, tokens_out, tool_calls, tool_timeouts, user)
    brain direct     tool_calls ['retrieve']    3420 ms  (keys: brain, budget_inr, cached_tokens, cost_usd, event, latency_ms, max_model_calls, model, model_calls, rag_cost_usd, refusals, session_id, stopped_by, surface, tenant, tokens_in, tokens_out, tool_calls, tool_timeouts, user)
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_5.1_Agent_Loop_WIX.html`. All 33 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `9abad409dcccc34daf6650ea28d882e0b674dc4a`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
