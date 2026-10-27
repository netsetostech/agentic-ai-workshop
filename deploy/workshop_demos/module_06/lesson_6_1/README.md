# Lesson 6.1: Assemble the context: what rides every model call

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 5 | [demo_05_offline_one_turn_split_by_source_for_rs_0.py](demo_05_offline_one_turn_split_by_source_for_rs_0.py) | Offline: one turn split by source, for Rs 0 |
| 6 | [demo_06_on_your_lane_the_model_s_own_counter_and_the_probe.py](demo_06_on_your_lane_the_model_s_own_counter_and_the_probe.py) | On your lane: the model's own counter, and the probe |
| 7 | [demo_07_five_brains_one_question_on_your_lane.py](demo_07_five_brains_one_question_on_your_lane.py) | Five brains, one question, on your lane |
| 8 | [demo_08_change_it_top_k_and_which_part_of_the_bill_moves.py](demo_08_change_it_top_k_and_which_part_of_the_bill_moves.py) | Change it: TOP_K, and which part of the bill moves |
| 9 | [demo_09_the_thread_rides_every_call_too.py](demo_09_the_thread_rides_every_call_too.py) | The thread rides every call too |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads what a search hands the chat model, so point acme at the kit's own index for the duration, whose citations carry the kit's chunk ids and pages as the offline runs' do, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads what a search hands the chat model, so point acme at the kit's own index for the duration, whose citations carry the kit's chunk ids and pages as the offline runs' do, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads what a search hands the chat model, so point acme at the kit's own index for the duration, whose citations carry the kit's chunk ids and pages as the offline runs' do, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_05_offline_one_turn_split_by_source_for_rs_0.py

Do it

**`step_01_offline_one_turn_split_by_source_for_rs_0(session)` — Offline: one turn split by source, for Rs 0 / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (a scripted model and the kit's corpus on your machine: no network, Rs 0).

Expected shape, not a promised result:

```text
context sources: one turn on brain langgraph, tenant acme, a fresh thread; each search sends the model's top_k, or tools.py's default of 5
  OFFLINE=1: a scripted model at the google-genai boundary (the brain, its adapter, tools and limits run
  as on the lane) and the Rs 0 lane's retrieve over evals/corpus: no network, no credential, nothing
  billed. Tokens are estimated: a quarter of the characters each part carries (rag-api's estimator,
  context_budget.estimate_tokens), so the residual is 0. On your lane count_tokens counts each source.
question: After how many years of continuous service is gratuity payable?
  sent with every call: a system prompt of 426 characters, the brain's own
  and 2 tool declarations (retrieve, calculate_processing_cost), each with its parameters

model call 1 of 2 (gemini-3.6-flash): in 361, out 21: Rs 0.0594
  system prompt           106   29.4%
  tool declarations       240   66.5%
  thread so far             0  
  question                 15    4.2%
  the model's calls         0  
  tool results              0  
  residual                  0           offline the script's input is the sum of its parts
  -> retrieve(query="After how many years of continuous service is gratuity payable?")
     search: top_k 5; 5 citations back, 2,004 characters
     inside it, rag-api's own call (estimated: generator.py's prompt): system 105, 5 chunks 1,834, question 18; in 1,957, out 24: Rs 0.2648
model call 2 of 2 (gemini-3.6-flash): in 1,143, out 50: Rs 0.1776
  system prompt           106    9.3%
  tool declarations       240   21.0%
  thread so far             0  
  question                 15    1.3%
  the model's calls        21    1.8%
  tool results            761   66.6%
  residual                  0           offline the script's input is the sum of its parts
  -> no tool: the answer

the turn by source: 2 model calls; the system prompt, the declarations, the thread and the question go with every one
                       tokens        Rs
  system prompt           212    0.0270  106 in each of 2 calls
  tool declarations       480    0.0612  240 in each of 2 calls
  thread so far             0    0.0000
  question                 30    0.0038  15 in each of 2 calls
  the model's calls        21    0.0027  from call 2 on
  tool results            761    0.0970  from call 2 on
  residual                  0    0.0000
  input                 1,504    0.1918
  cached                    0    0.0000  a cached token bills at a tenth of the input price
  output                   71    0.0453  thinking included
  the model calls                0.2370  the turn's Meter (limits.py) charged Rs 0.2370 for 2 calls
  rag-api, inside                0.2648  1 answer of its own, estimated; the Meter charged Rs 0.2648
  the turn                       0.5018  at list price (shared/prices.py, USD_INR 85); offline, nothing is billed

answer: (offline, scripted) The first passage says: "Payment of Gratuity.- (1) Gratuity shall be payable to an employee on the termination of his employmen...
```

### demo_06_on_your_lane_the_model_s_own_counter_and_the_probe.py

Whether count_tokens on location global takes the declarations and the system instruction at all was not known when the kit was written. The probe settles it before any count on this page is trusted, for both forms of declaration: LangChain's parameters on the LangGraph brain, and ADK's parametersJsonSchema. The cell prints only each run's probe. Step 7 shows the whole of each run.

**`step_01_the_probe(session)` — On your lane: the model's own counter, and the probe / Do it: the probe**

Whether count_tokens on location global takes the declarations and the system instruction at all was not known when the kit was written. The probe settles it before any count on this page is trusted, for both forms of declaration: LangChain's parameters on the LangGraph brain, and ADK's parametersJsonSchema. The cell prints only each run's probe. Step 7 shows the whole of each run.

Operation: bash — run in the operator shell, in the kit (two real turns on your lane, a few rupees; only each run's probe is printed).

Expected shape, not a promised result:

```text
== BRAIN=langgraph
[awaiting the author's run: data/probe_langgraph.txt]
== BRAIN=adk
[awaiting the author's run: data/probe_adk.txt]
```

### demo_07_five_brains_one_question_on_your_lane.py

Do it

**`step_01_five_brains_one_question_on_your_lane(session)` — Five brains, one question, on your lane / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (one real turn on each brain, a few rupees each).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/lane_langchain.txt]
```

### demo_08_change_it_top_k_and_which_part_of_the_bill_moves.py

make context-sources prints its breakdown; with JSON=1 it prints the turn as one record instead, the command's --json. Write one record with TOP_K unset and one with TOP_K 3, then compare them source by source. Compare this one with step 7's langgraph output: Compare this one with step 7's langgraph output: And this one with step 7's desk output:

**`step_01_offline_the_two_records_side_by_side(session)` — Change it: TOP_K, and which part of the bill moves / Do it: offline, the two records side by side**

make context-sources prints its breakdown; with JSON=1 it prints the turn as one record instead, the command's --json. Write one record with TOP_K unset and one with TOP_K 3, then compare them source by source.

Operation: bash — run in the operator shell, in the kit (two offline turns, written as records: Rs 0).

**`step_02_offline_the_two_records_side_by_side(session)` — Change it: TOP_K, and which part of the bill moves / Do it: offline, the two records side by side**

make context-sources prints its breakdown; with JSON=1 it prints the turn as one record instead, the command's --json. Write one record with TOP_K unset and one with TOP_K 3, then compare them source by source.

Operation: bash — run in the operator shell, in the kit (reads the two records; no network).

Expected shape, not a promised result:

```text
TOP_K unset   TOP_K=3
system prompt                212       212
tool declarations            480       480
thread so far                  0         0
question                      30        30
the model's calls             21        21
tool results                 761       435   moved
rag-api, inside            1,957     1,095   moved: 5 chunks packed, then 3
the model calls, Rs       0.2370    0.1955
rag-api, Rs               0.2648    0.1549
the turn, Rs              0.5018    0.3504
```

**`step_03_on_your_lane_a_chat_brain_and_the_desk(session)` — Change it: TOP_K, and which part of the bill moves / Do it: on your lane, a chat brain and the Desk**

Compare this one with step 7's langgraph output:

Operation: bash — run in the operator shell, in the kit (one real turn, every search sent top_k 3).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/lane_langgraph_topk3.txt]
```

**`step_04_on_your_lane_a_chat_brain_and_the_desk(session)` — Change it: TOP_K, and which part of the bill moves / Do it: on your lane, a chat brain and the Desk**

Compare this one with step 7's langgraph output: And this one with step 7's desk output:

Operation: bash — run in the operator shell, in the kit (one real turn on the statute desk, top_k 3).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/lane_desk_topk3.txt]
```

### demo_09_the_thread_rides_every_call_too.py

Do it: offline Do it: on your lane

**`step_01_offline(session)` — The thread rides every call too / Do it: offline**

Do it: offline

Operation: bash — run in the operator shell, in the kit (three offline turns on one local thread: Rs 0).

Expected shape, not a promised result:

```text
context sources: one turn on brain langchain, tenant acme, turn 3 of one thread, after 2 earlier questions; each search sends the model's top_k, or tools.py's default of 5
  OFFLINE=1: a scripted model at the google-genai boundary (the brain, its adapter, tools and limits run
  as on the lane) and the Rs 0 lane's retrieve over evals/corpus: no network, no credential, nothing
  billed. Tokens are estimated: a quarter of the characters each part carries (rag-api's estimator,
  context_budget.estimate_tokens), so the residual is 0. On your lane count_tokens counts each source.
question: After how many years of continuous service is gratuity payable?
  sent with every call: a system prompt of 426 characters, the brain's own
  and 2 tool declarations (retrieve, calculate_processing_cost), each with its parameters
  the 2 earlier turns, not measured: 4 model calls and 2 searches, Rs 1.0857

model call 1 of 2 (gemini-3.6-flash): in 1,812, out 21: Rs 0.2444
  system prompt           106    5.8%
  tool declarations       240   13.2%
  thread so far         1,451   80.1%
  question                 15    0.8%
  the model's calls         0  
  tool results              0  
  residual                  0           offline the script's input is the sum of its parts
  -> retrieve(query="After how many years of continuous service is gratuity payable?")
     search: top_k 5; 5 citations back, 2,004 characters
     inside it, rag-api's own call (estimated: generator.py's prompt): system 105, 5 chunks 1,834, question 18; in 1,957, out 24: Rs 0.2648
model call 2 of 2 (gemini-3.6-flash): in 2,594, out 50: Rs 0.3626
  system prompt           106    4.1%
  tool declarations       240    9.3%
  thread so far         1,451   55.9%
  question                 15    0.6%
  the model's calls        21    0.8%
  tool results            761   29.3%
  residual                  0           offline the script's input is the sum of its parts
  -> no tool: the answer

the turn by source: 2 model calls; the system prompt, the declarations, the thread and the question go with every one
                       tokens        Rs
  system prompt           212    0.0270  106 in each of 2 calls
  tool declarations       480    0.0612  240 in each of 2 calls
  thread so far         2,902    0.3700  1,451 in each of 2 calls
  question                 30    0.0038  15 in each of 2 calls
  the model's calls        21    0.0027  from call 2 on
  tool results            761    0.0970  from call 2 on
  residual                  0    0.0000
  input                 4,406    0.5618
  cached                    0    0.0000  a cached token bills at a tenth of the input price
  output                   71    0.0453  thinking included
  the model calls                0.6070  the turn's Meter (limits.py) charged Rs 0.6070 for 2 calls
  rag-api, inside                0.2648  1 answer of its own, estimated; the Meter charged Rs 0.2648
  the turn                       0.8718  at list price (shared/prices.py, USD_INR 85); offline, nothing is billed

answer: (offline, scripted) The first passage says: "Payment of Gratuity.- (1) Gratuity shall be payable to an employee on the termination of his employmen...
```

**`step_02_on_your_lane(session)` — The thread rides every call too / Do it: on your lane**

Do it: on your lane

Operation: bash — run in the operator shell, in the kit (three real turns on one local thread, the last measured).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/lane_langchain_turns3.txt]
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads what a search hands the chat model, so point acme at the kit's own index for the duration, whose citations carry the kit's chunk ids and pages as the offline runs' do, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads what a search hands the chat model, so point acme at the kit's own index for the duration, whose citations carry the kit's chunk ids and pages as the offline runs' do, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_6.1_Context_Architecture_WIX.html`. All 49 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `272457217222d6e81f3450e0a57382c64f84b1d3`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
