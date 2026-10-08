# Lesson 6.5: Distinguish agent state, conversation history and knowledge

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_one_turn_taken_apart.py](demo_03_one_turn_taken_apart.py) | One turn, taken apart |
| 4 | [demo_04_the_memory_checkpointer_and_the_line_it_logs.py](demo_04_the_memory_checkpointer_and_the_line_it_logs.py) | The memory checkpointer, and the line it logs |
| 5 | [demo_05_one_conversation_four_brains_two_sessions.py](demo_05_one_conversation_four_brains_two_sessions.py) | One conversation, four brains, two sessions |
| 6 | [demo_06_which_checkpointer_your_lane_runs.py](demo_06_which_checkpointer_your_lane_runs.py) | Which checkpointer your lane runs |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Module 5's deployed chat lane and the framework venv created during preparation.

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

### demo_03_one_turn_taken_apart.py

Do it: the venv Do it: one turn

**`step_01_the_venv(session)` — One turn, taken apart / Do it: the venv**

Do it: the venv

Operation: bash — run in the operator shell, in the kit (lesson 5.4's venv, with the web layer and the SQLite checkpointer added).

Expected shape, not a promised result:

```text
graph-venv ok: fastapi 0.141.1
```

**`step_02_one_turn(session)` — One turn, taken apart / Do it: one turn**

Do it: one turn

Operation: bash — run in the operator shell, in the kit (one turn taken apart; no model, no network beyond your machine).

Expected shape, not a promised result:

```text
1. turn 1, the LangChain brain, thread acme:you@example.com:lesson111
   kept  HumanMessage What is the notice period?
   kept  AIMessage    retrieve(...)
   kept  ToolMessage  {"citations": [{"chunk_id": "acme:hr_policy_2026#NP-03", "quote"
   kept  AIMessage    Sixty days [1].
   the system prompt among them: False; checkpoints written: 5
2. turn 2, the LangGraph brain, the same thread: 6 messages, turn 1's among them
   the history still quotes: The notice period is 60 days.
   the corpus now says:      The notice period is 90 days.
3. a new session, the same person: 0 messages
```

### demo_04_the_memory_checkpointer_and_the_line_it_logs.py

Do it

**`step_01_the_memory_checkpointer_and_the_line_it_lo(session)` — The memory checkpointer, and the line it logs / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the chat service's checkpointer with CHECKPOINT_DSN=memory, then a restart).

Expected shape, not a promised result:

```text
1. the chat service's own checkpointer, with CHECKPOINT_DSN=memory
WARNING documind.chat.agent: CHECKPOINT_DSN=memory: conversations die with the instance (8.5). Tests only - never a deployment.
   InMemorySaver: 2 messages in acme:you@example.com:lesson111
WARNING documind.chat.agent: CHECKPOINT_DSN=memory: conversations die with the instance (8.5). Tests only - never a deployment.
   after a restart: 0 messages
2. the laptop lane's SqliteSaver, a file (agent.py's DOCUMIND_PROFILE=local branch)
   after a restart: 2 messages
```

### demo_05_one_conversation_four_brains_two_sessions.py

Do it

**`step_01_one_conversation_four_brains_two_sessions(session)` — One conversation, four brains, two sessions / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (one conversation, four brains, two sessions).

Expected shape, not a promised result:

```text
langchain session A  tools []            tamarind yes  "Got it: tamarind. I'll keep it for this "
  langgraph session A  tools []            tamarind yes  'You asked me to remember "tamarind".'
  adk       session A  tools []            tamarind no   "I don't have a word from you in this con"
  direct    session A  tools ['retrieve']  tamarind no   'The documents do not say which word you '
  langchain session B  tools []            tamarind no   "I don't have a word from you in this con"
  langchain session B  tools ['retrieve']  tamarind no   'Gratuity becomes payable after not less '
```

### demo_06_which_checkpointer_your_lane_runs.py

Do it

**`step_01_which_checkpointer_your_lane_runs(session)` — Which checkpointer your lane runs / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the checkpointer your chat service is configured with).

Expected shape, not a promised result:

```text
CHECKPOINT_DSN  from the secret documind-checkpoint-dsn, version latest
  Cloud SQL       documind-ai-YOUR-ID:asia-south1:documind-checkpoint
  the memory warning in 30 days of the service's log: none
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_6.5_State_History_WIX.html`. All 19 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `a4df41e28a582704ba318ce387bc1df09b3dfddb`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
