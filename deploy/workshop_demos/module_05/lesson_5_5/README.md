# Lesson 5.5: Diagnose tool arguments, access failures and timeouts

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_five_failures_through_the_kit_s_langchain_brain.py](demo_03_five_failures_through_the_kit_s_langchain_brain.py) | Five failures through the kit's LangChain brain |
| 4 | [demo_04_a_turn_that_will_not_stop_the_call_cap_the_rupees_and_the_deadline.py](demo_04_a_turn_that_will_not_stop_the_call_cap_the_rupees_and_the_deadline.py) | A turn that will not stop: the call cap, the rupees and the deadline |
| 5 | [demo_05_access_failures_at_the_chat_service_s_door.py](demo_05_access_failures_at_the_chat_service_s_door.py) | Access failures at the chat service's door |
| 6 | [demo_06_an_argument_the_corpus_cannot_honour.py](demo_06_an_argument_the_corpus_cannot_honour.py) | An argument the corpus cannot honour |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The deployed chat lane; the framework failure harness runs in its own lesson venv.

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

### demo_03_five_failures_through_the_kit_s_langchain_brain.py

Do it: the venv Do it: five failures

**`step_01_the_venv(session)` — Five failures through the kit's LangChain brain / Do it: the venv**

Do it: the venv

Operation: bash — run in the operator shell, in the kit (the venv from lesson 5.4, made if it is missing).

Expected shape, not a promised result:

```text
graph-venv ok: langchain 1.4.0
```

**`step_02_five_failures(session)` — Five failures through the kit's LangChain brain / Do it: five failures**

Do it: five failures

Operation: bash — run in the operator shell, in the kit (five failures through the kit's LangChain brain; no model, no network beyond your machine).

Expected shape, not a promised result:

```text
blocked   0.0 s  refusals ['delete_document']  tool_timeouts []
            result [error] {"error": "delete_document requires manual approval"}
  bad args  0.0 s  refusals ['calculate_processing_cost']  tool_timeouts []
            result [error] Error invoking tool 'calculate_processing_cost' with kwargs {'total_page
  no such   0.0 s  refusals ['summon_rain']  tool_timeouts []
            result [error] Error: summon_rain is not a valid tool, try one of [retrieve, calculate_
  timed out 0.5 s  refusals []  tool_timeouts []
            result [success] {"error": "document search is unavailable", "citations": [], "answerable
  cut       1.0 s  refusals []  tool_timeouts ['retrieve']
            result [success] {"error": "retrieve did not answer within 1s and was abandoned", "timed_
  the log lines, from the guard's timer, the adapter and the one retrieve():
    WARNING refused delete_document (blocked list)
    INFO    calculate_processing_cost took 0.00s (budget 10s)
    INFO    summon_rain took 0.00s (budget 30s)
    WARNING retrieve failed: HTTPConnectionPool(host='127.0.0.1', port=PORT): Read timed out. (
    INFO    retrieve took 0.50s
    INFO    retrieve took 0.50s
    WARNING rag-api query failed: document retrieval is unavailable
    INFO    retrieve took 0.50s (budget 25s)
    WARNING retrieve took 1.00s (budget 1s)
    INFO    retrieve took 2.00s
    INFO    retrieve took 2.00s
```

### demo_04_a_turn_that_will_not_stop_the_call_cap_the_rupees_and_the_deadline.py

Do it: a model that never stops asking Do it: every brain, offline Do it: your lane's limits Do it: a capped turn on your lane

**`step_01_a_model_that_never_stops_asking(session)` — A turn that will not stop: the call cap, the rupees and the deadline / Do it: a model that never stops asking**

Do it: a model that never stops asking

Operation: bash — run in the operator shell, in the kit (a model that never stops asking, then the next turn on its thread; offline).

Expected shape, not a promised result:

```text
turn 1  model calls 3 of 3  tool calls 3  stopped_by model_calls
          answer: I stopped this turn at one of its limits before I could finish, so this answer is incomplete. Ask again, or ask a narrower question.
  turn 2  model calls 1 of 3  tool calls 0  stopped_by None
          answer: USD 33.96 at the priority tier, about Rs 2,886.60.
  the thread: 10 messages, 3 tool calls, 0 left open
```

**`step_02_every_brain_offline(session)` — A turn that will not stop: the call cap, the rupees and the deadline / Do it: every brain, offline**

Do it: every brain, offline

Operation: bash — run in the operator shell, in the kit (every agent brain against the limits, offline).

Expected shape, not a promised result:

```text
test_a_forced_recursion_limit_leaves_a_whole_thread (commands.tests.test_chat_limits.BrainsStop.test_a_forced_recursion_limit_leaves_a_whole_thread)
The framework's backstop, tripped before the Meter: the open call is answered, the turn ends with the stop, ... ok
test_a_hung_model_call_ends_in_the_stop_not_an_exception (commands.tests.test_chat_limits.BrainsStop.test_a_hung_model_call_ends_in_the_stop_not_an_exception) ... ok
test_a_looping_model_stops_at_the_call_cap_and_the_next_turn_answers (commands.tests.test_chat_limits.BrainsStop.test_a_looping_model_stops_at_the_call_cap_and_the_next_turn_answers) ... ok
test_a_looping_model_stops_at_the_deadline (commands.tests.test_chat_limits.BrainsStop.test_a_looping_model_stops_at_the_deadline) ... ok
test_a_looping_model_stops_at_the_rupee_cap (commands.tests.test_chat_limits.BrainsStop.test_a_looping_model_stops_at_the_rupee_cap)
8,000 tokens a call is about Rs 1.05, and each search Rs 0.19: a Rs 2 cap allows two calls. ... ok
test_a_normal_turn_is_charged_and_not_stopped (commands.tests.test_chat_limits.BrainsStop.test_a_normal_turn_is_charged_and_not_stopped) ... ok
test_a_queued_tool_call_is_cancelled_not_run (commands.tests.test_chat_limits.BrainsStop.test_a_queued_tool_call_is_cancelled_not_run)
One pool thread, three calls of 1 s cut at 0.2 s: only the first ever runs. ... ok
test_a_slow_search_is_abandoned_at_its_budget_as_data (commands.tests.test_chat_limits.BrainsStop.test_a_slow_search_is_abandoned_at_its_budget_as_data)
A 3 s rag-api against a 1 s budget: the turn goes on at 1 s, the model reads a payload error, and the ... ok
test_a_turn_writes_the_same_checkpoints (commands.tests.test_chat_limits.BrainsStop.test_a_turn_writes_the_same_checkpoints)
wrap_model_call adds no graph node: +3 checkpoints a turn, +5 with a tool call (workshop lesson 6.6). ... ok
test_adks_own_cap_is_caught (commands.tests.test_chat_limits.BrainsStop.test_adks_own_cap_is_caught) ... ok
test_an_abandoned_search_adds_no_citation (commands.tests.test_chat_limits.BrainsStop.test_an_abandoned_search_adds_no_citation)
The cut search answers at 1.6 s, while the model's answer takes until 2.5 s: its thread finishes inside the ... ok
test_other_model_errors_still_fail_the_turn (commands.tests.test_chat_limits.BrainsStop.test_other_model_errors_still_fail_the_turn) ... ok
test_the_adk_declarations_are_unchanged_by_the_timer (commands.tests.test_chat_limits.BrainsStop.test_the_adk_declarations_are_unchanged_by_the_timer) ... ok
test_the_chat_service_answers_a_stopped_turn_with_200 (commands.tests.test_chat_limits.BrainsStop.test_the_chat_service_answers_a_stopped_turn_with_200)
agent.chat() with a cheap model that never stops asking: HTTP 200, the stop sentence, the row's fields. ... ok
test_the_model_reads_the_timeout_as_a_payload_error (commands.tests.test_chat_limits.BrainsStop.test_the_model_reads_the_timeout_as_a_payload_error) ... ok
test_a_turn_ends_before_anything_around_it_gives_up (commands.tests.test_chat_limits.KitAgrees.test_a_turn_ends_before_anything_around_it_gives_up)
The deadline, one retry's backoff and the last tool's floor: about 103 s, under 120 and 300. ... ok
test_the_chat_prices_are_rag_apis (commands.tests.test_chat_limits.KitAgrees.test_the_chat_prices_are_rag_apis) ... ok
test_the_chat_row_names_every_limits_field (commands.tests.test_chat_limits.KitAgrees.test_the_chat_row_names_every_limits_field)
Each field in the row literal, read the way the pages read it: a spread would hide them. ... ok
test_the_defaults (commands.tests.test_chat_limits.KitAgrees.test_the_defaults) ... ok
test_the_local_profile_costs_nothing (commands.tests.test_chat_limits.KitAgrees.test_the_local_profile_costs_nothing) ... ok
test_the_mcp_tool_keeps_its_contract (commands.tests.test_chat_limits.KitAgrees.test_the_mcp_tool_keeps_its_contract) ... ok
test_a_stop_is_sticky_and_the_first_reason_wins (commands.tests.test_chat_limits.MeterArithmetic.test_a_stop_is_sticky_and_the_first_reason_wins) ... ok
test_a_timeout_is_recognised_from_every_client (commands.tests.test_chat_limits.MeterArithmetic.test_a_timeout_is_recognised_from_every_client) ... ok
test_a_tool_gets_its_budget_or_the_time_left_never_under_a_second (commands.tests.test_chat_limits.MeterArithmetic.test_a_tool_gets_its_budget_or_the_time_left_never_under_a_second) ... ok
test_cached_tokens_are_billed_at_a_tenth (commands.tests.test_chat_limits.MeterArithmetic.test_cached_tokens_are_billed_at_a_tenth) ... ok
test_each_model_attempt_fits_in_the_time_left (commands.tests.test_chat_limits.MeterArithmetic.test_each_model_attempt_fits_in_the_time_left) ... ok
test_rag_apis_own_cost_wins_over_list_price (commands.tests.test_chat_limits.MeterArithmetic.test_rag_apis_own_cost_wins_over_list_price) ... ok
test_the_call_cap_counts_the_calls_it_allows (commands.tests.test_chat_limits.MeterArithmetic.test_the_call_cap_counts_the_calls_it_allows) ... ok
test_the_deadline_refuses_a_call_with_too_little_time_left (commands.tests.test_chat_limits.MeterArithmetic.test_the_deadline_refuses_a_call_with_too_little_time_left) ... ok
test_the_first_call_is_always_allowed (commands.tests.test_chat_limits.MeterArithmetic.test_the_first_call_is_always_allowed) ... ok
test_the_rupee_cap_stops_the_call_after_the_one_that_crossed_it (commands.tests.test_chat_limits.MeterArithmetic.test_the_rupee_cap_stops_the_call_after_the_one_that_crossed_it) ... ok
test_the_summary_and_the_row (commands.tests.test_chat_limits.MeterArithmetic.test_the_summary_and_the_row) ... ok
test_twelve_flash_calls_of_8000_tokens_cost_more_than_the_default_cap (commands.tests.test_chat_limits.MeterArithmetic.test_twelve_flash_calls_of_8000_tokens_cost_more_than_the_default_cap) ... ok
test_a_calls_fate_is_decided_once (commands.tests.test_chat_limits.TimedCalls.test_a_calls_fate_is_decided_once) ... ok
test_a_queued_call_is_cancelled_and_a_running_one_writes_nothing (commands.tests.test_chat_limits.TimedCalls.test_a_queued_call_is_cancelled_and_a_running_one_writes_nothing)
One pool thread, three calls of 1 s cut at 0.2 s: the first runs on, past all three cuts, but may ... ok
test_no_turn_context_keeps_no_meter (commands.tests.test_chat_limits.TimedCalls.test_no_turn_context_keeps_no_meter)
Outside a turn, ADK's callbacks get a fresh Meter each time: never one stored in the ContextVar's default, ... ok

----------------------------------------------------------------------
Ran 36 tests in N.NNNs

OK
```

**`step_03_your_lane_s_limits(session)` — A turn that will not stop: the call cap, the rupees and the deadline / Do it: your lane's limits**

Do it: your lane's limits

Operation: bash — run in the operator shell, in the kit (reads /health as documind-ui-sa; changes nothing).

Expected shape, not a promised result:

```text
documind-chat  https://documind-chat-NUMBER.asia-south1.run.app
  model calls a turn    12
  rupees a turn         Rs 5
  deadline              100 s; each model call min(30 s, time left / 2), none started with under 5 s left
  tool budgets          retrieve 95 s, calculate_processing_cost 10 s
documind-agent  https://documind-agent-NUMBER.asia-south1.run.app
  model calls a task    not on its /health (ADK defaults to 500)
```

**`step_04_a_capped_turn_on_your_lane(session)` — A turn that will not stop: the call cap, the rupees and the deadline / Do it: a capped turn on your lane**

Do it: a capped turn on your lane

Operation: bash — run in the operator shell, in the kit (caps the deployed chat at one model call, smokes it, and puts it back).

Expected shape, not a promised result:

```text
>> documind-chat: CHAT_MAX_MODEL_CALLS=1 (STOP=model_calls)

  DocuMind chat - live smoke test
  target: https://documind-chat-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] health  profile=gcp default=langchain limits=1 calls, Rs 5.0, 100.0 s
  [PASS] brain direct  3120 ms  tools=['retrieve']  citations=5  calls=0 Rs 0.2831  'Gratuity becomes payable after not less than five years of c'
  [PASS] brain langchain stopped  stopped_by=model_calls calls=1 Rs 0.5445  'I stopped this turn at one of its limits before I could fini'
  [PASS] brain langgraph stopped  stopped_by=model_calls calls=1 Rs 0.5445  'I stopped this turn at one of its limits before I could fini'
  [PASS] brain adk stopped  stopped_by=model_calls calls=1 Rs 0.5445  'I stopped this turn at one of its limits before I could fini'
  --------------------------------------------------------
  5 passed, 0 failed

>> restored: CHAT_MAX_MODEL_CALLS unset, the default applies
>> the same smoke with the limit restored: every brain answers

  DocuMind chat - live smoke test
  target: https://documind-chat-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] health  profile=gcp default=langchain limits=12 calls, Rs 5.0, 100.0 s
  [PASS] brain direct  3120 ms  tools=['retrieve']  citations=5  calls=0 Rs 0.2831  'Gratuity becomes payable after not less than five years of c'
  [PASS] brain langchain  11840 ms  tools=['retrieve']  citations=5  calls=2 Rs 1.1023  'Gratuity becomes payable once you have rendered at least fiv'
  [PASS] brain langgraph  9730 ms  tools=['retrieve']  citations=5  calls=2 Rs 1.1023  'Gratuity is payable after at least five years of continuous '
  [PASS] brain adk  14260 ms  tools=['retrieve']  citations=5  calls=2 Rs 1.1023  'After five years of continuous service, gratuity becomes pay'
  --------------------------------------------------------
  5 passed, 0 failed
```

### demo_05_access_failures_at_the_chat_service_s_door.py

Do it

**`step_01_access_failures_at_the_chat_service_s_door(session)` — Access failures at the chat service's door / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (three identities at the chat service's door).

Expected shape, not a promised result:

```text
403  {"detail":"not a member of any tenant"}
  401  {"detail":"the bearer token carries no verified email"}
  200  {"answer":"Gratuity becomes payable after not less than five years of continuous service [1].","tool
```

### demo_06_an_argument_the_corpus_cannot_honour.py

Do it

**`step_01_an_argument_the_corpus_cannot_honour(session)` — An argument the corpus cannot honour / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (one question with and without a doc_type filter, then rag-api's rows).

Expected shape, not a promised result:

```text
doc_type None     5 citations | answerable True | The total payable on invoice INV-2026-0412 is Rs 1,84,500 
  doc_type invoice  0 citations | answerable False | The corpus holds nothing near this question: no passage of
  pool 20  answerable True   backend vertex  Rs 0.2831
  pool  0  answerable False  backend none    Rs 0.0000
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_5.5_Tool_Failures_WIX.html`. All 29 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `780a103bb4f0ddb0633a2c104547c46fa01b58c3`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
