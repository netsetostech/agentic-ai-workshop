# Lesson 5.7: Compare the LangChain and ADK adapters

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_two_adapters_over_one_tool_side_by_side.py](demo_03_two_adapters_over_one_tool_side_by_side.py) | Two adapters over one tool, side by side |
| 4 | [demo_04_four_brains_on_health_and_the_module_s_gate.py](demo_04_four_brains_on_health_and_the_module_s_gate.py) | Four brains on /health, and the module's gate |
| 5 | [demo_05_four_cost_lines_from_rag_api_s_rows_and_the_chat_rows.py](demo_05_four_cost_lines_from_rag_api_s_rows_and_the_chat_rows.py) | Four cost lines, from rag-api's rows and the chat rows |
| 6 | [demo_06_the_loop_call_by_call.py](demo_06_the_loop_call_by_call.py) | The loop, call by call |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The deployed chat lane and access to the example models; adapters use a separate framework venv.

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

### demo_03_two_adapters_over_one_tool_side_by_side.py

Do it: the venv Do it: side by side

**`step_01_the_venv(session)` — Two adapters over one tool, side by side / Do it: the venv**

Do it: the venv

Operation: bash — run in the operator shell, in the kit (lesson 5.4's venv, with google-adk added).

Expected shape, not a promised result:

```text
graph-venv ok: google-adk 2.8.0 langchain 1.4.0
```

**`step_02_side_by_side(session)` — Two adapters over one tool, side by side / Do it: side by side**

Do it: side by side

Operation: bash — run in the operator shell, in the kit (the two adapters side by side; no model, no network beyond your machine).

Expected shape, not a promised result:

```text
1. what each model is shown for retrieve (* = required); raw = FunctionTool over the shared retrieve(), unadapted
   langchain query*, doc_type, top_k                                          481 characters
   adk       query*, doc_type, top_k                                          635 characters
   raw       query*, tenant_id*, top_k, doc_type, assertion, brain, passages  3,420 characters
   langchain tools: retrieve, calculate_processing_cost
   adk tools:       retrieve, calculate_processing_cost   (tools.for_adk())
2. one retrieve(); the ADK model writes tenant_id "globex" and assertion "anything"
   langchain rag-api got tenant acme, brain langchain, assertion header None
             the model read: citations, answerable, confidence; citations numbered [1]
   adk       rag-api got tenant acme, brain adk, assertion header None
             the model read: citations, answerable, confidence; citations numbered [1]
3. four calls that go wrong
   delete_document(doc="x")
     langchain [error] {"error": "delete_document requires manual approval"}
               refusals ['delete_document']
     adk       [error] {"error": "delete_document requires manual approval", "status":
               "error"}
               refusals ['delete_document']
   calculate_processing_cost(total_pages="many")
     langchain [error] Error invoking tool 'calculate_processing_cost' with kwargs
               {'total_pages': 'many'} with error: total_pages: Input should be a valid
               [...]
               refusals ['calculate_processing_cost']
     adk       [error] {"error": "1 validation error for
               calculate_processing_cost\ntotal_pages\n Input should be a valid integer,
               unable to parse string as an [...]
               refusals ['calculate_processing_cost']
   calculate_processing_cost(total_pages=10, processing_type="express")
     langchain [error] unknown tier 'express'; expected one of ['bulk', 'priority',
               'standard']
               refusals ['calculate_processing_cost']
     adk       [error] {"error": "unknown tier 'express'; expected one of ['bulk',
               'priority', 'standard']", "status": "error"}
               refusals ['calculate_processing_cost']
   calculate_processing_cost()
     langchain [error] Error invoking tool 'calculate_processing_cost' with kwargs {} with
               error: total_pages: Field required Please fix the error and try again.
               refusals ['calculate_processing_cost']
     adk       [error] {"error": "Invoking `calculate_processing_cost()` failed as the
               following mandatory input parameters are not present:\ntotal_pages\nYou
               [...]
               refusals ['calculate_processing_cost']
4. ADK's sessions with no CHECKPOINT_DSN: InMemorySessionService, at most 12 model calls a turn
5. the turn's limits, wired three ways: a model that asks for a tool on every call, at a cap of 2
   langchain  nodes model, tools; TurnLimitsMiddleware wraps the model call
              stopped_by model_calls after 2 model calls: I stopped this turn at one of its limits bef...
   langgraph  nodes agent, tools, refuse; the agent node checks the Meter itself
              stopped_by model_calls after 2 model calls: I stopped this turn at one of its limits bef...
   adk        adk_before_model, adk_after_model, adk_model_error; RunConfig max_llm_calls 12
              stopped_by model_calls after 2 model calls: I stopped this turn at one of its limits bef...
   the kit's middleware:      nodes model, tools; a turn with one tool call writes 5 checkpoints
   ModelCallLimitMiddleware:  nodes model, tools, ModelCallLimitMiddleware.before_model, ModelCallLimitMiddleware.after_model; a turn with one tool call writes 9 checkpoints
```

### demo_04_four_brains_on_health_and_the_module_s_gate.py

Do it

**`step_01_four_brains_on_health_and_the_module_s_gat(session)` — Four brains on /health, and the module's gate / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (/health, then the module's gate).

Expected shape, not a promised result:

```text
{"status":"ok","profile":"gcp","brains":["langchain","langgraph","adk","direct"],"default_brain":"langchain","limits":{"max_model_calls":12,"budget_inr":5.0,"deadline_s":100.0,"model_timeout_s":30.0,"model_attempts":2,"min_model_s":5.0,"tool_budgets_s":{"retrieve":95.0,"calculate_processing_cost":10}}}
  DocuMind chat - live smoke test
  target: https://documind-chat-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] health  profile=gcp default=langchain limits=12 calls, Rs 5.0, 100.0 s
  [PASS] brain direct  3120 ms  tools=['retrieve']  citations=5  calls=0 Rs 0.3699  'Gratuity becomes payable after not less than five years of c'
  [PASS] brain langchain  11840 ms  tools=['retrieve']  citations=5  calls=2 Rs 0.8738  'Gratuity becomes payable once you have rendered at least fiv'
  [PASS] brain langgraph  9730 ms  tools=['retrieve']  citations=5  calls=2 Rs 0.8777  'Gratuity is payable after at least five years of continuous '
  [PASS] brain adk  14260 ms  tools=['retrieve']  citations=5  calls=2 Rs 1.0024  'After five years of continuous service, gratuity becomes pay'
  [PASS] outsider refused  status=403 not a member of any tenant
  --------------------------------------------------------
  6 passed, 0 failed
```

### demo_05_four_cost_lines_from_rag_api_s_rows_and_the_chat_rows.py

Do it

**`step_01_four_cost_lines_from_rag_api_s_rows_and_th(session)` — Four cost lines, from rag-api's rows and the chat rows / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (rag-api's rows and the chat rows since step 4, one line per brain).

Expected shape, not a promised result:

```text
rag-api's rows        the chat rows             whole
  direct    1 retrieve()  Rs 0.3699   0 model calls  Rs 0.0000   Rs 0.3699
  langchain 1 retrieve()  Rs 0.3593   2 model calls  Rs 0.5144   Rs 0.8737
  langgraph 1 retrieve()  Rs 0.3613   2 model calls  Rs 0.5164   Rs 0.8777
  adk       1 retrieve()  Rs 0.3687   2 model calls  Rs 0.6337   Rs 1.0024
```

### demo_06_the_loop_call_by_call.py

Do it

**`step_01_the_loop_call_by_call(session)` — The loop, call by call / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the kit's three agent brains on your machine, each model call counted).

Expected shape, not a promised result:

```text
langchain call 1: in   401 out   31   call 2: in   931 out   20   (thinking 0)
            the Meter, as the chat row keeps it: 2 model calls, in 1,332, out 51, Rs 0.2023
  langgraph call 1: in   401 out   31   call 2: in   931 out   20   (thinking 0)
            the Meter, as the chat row keeps it: 2 model calls, in 1,332, out 51, Rs 0.2023
  adk       call 1: in   501 out   21   call 2: in 1,058 out   20   (thinking 0)
            the Meter, as the chat row keeps it: 2 model calls, in 1,559, out 41, Rs 0.2249
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_5.7_Adapters_WIX.html`. All 23 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `38fb9d89de6f76a3929d154aa4d2e3b39a759159`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
