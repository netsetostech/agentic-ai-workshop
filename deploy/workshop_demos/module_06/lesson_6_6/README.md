# Lesson 6.6: Configure and inspect durable conversation storage

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_what_a_turn_writes.py](demo_03_what_a_turn_writes.py) | What a turn writes |
| 4 | [demo_04_what_your_lane_runs.py](demo_04_what_your_lane_runs.py) | What your lane runs |
| 5 | [demo_05_the_tables_and_one_row_per_thread.py](demo_05_the_tables_and_one_row_per_thread.py) | The tables, and one row per thread |
| 6 | [demo_06_one_thread_step_by_step.py](demo_06_one_thread_step_by_step.py) | One thread, step by step |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

A lane with the durable conversation store configured; read configuration before inspecting SQL.

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

### demo_03_what_a_turn_writes.py

Do it: the venv Do it: two turns

**`step_01_the_venv(session)` — What a turn writes / Do it: the venv**

Do it: the venv

Operation: bash — run in the operator shell, in the kit (lesson 5.4's venv, with the Cloud SQL connector added).

Expected shape, not a promised result:

```text
graph-venv ok: connector 1.22.0
```

**`step_02_two_turns(session)` — What a turn writes / Do it: two turns**

Do it: two turns

Operation: bash — run in the operator shell, in the kit (two turns, their checkpoints and versions counted; no model, no network).

Expected shape, not a promised result:

```text
a turn with no tool   +3 checkpoints, +2 versions of messages
a turn with retrieve  +5 checkpoints, +4 versions of messages
the messages channel, every version kept:
   version 1  1 message      211 bytes
   version 2  2 messages     472 bytes
   version 3  3 messages     687 bytes
   version 4  4 messages   1,001 bytes
   version 5  5 messages   2,760 bytes
   version 6  6 messages   3,021 bytes
   8,152 bytes kept, for a conversation whose latest version is 3,021 bytes
the ADK brain, given the lane's DSN, with google-adk and no SQLAlchemy - as the chat image has them:
WARNING documind.chat.brains: ADK DatabaseSessionService unavailable (The 'sqlalchemy' package is required to use this feature. Please install it by running: pip install google-adk[db]); using memory
   it keeps its sessions in InMemorySessionService
```

### demo_04_what_your_lane_runs.py

Do it

**`step_01_what_your_lane_runs(session)` — What your lane runs / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (what holds the conversations on your lane).

Expected shape, not a promised result:

```text
instance      documind-checkpoint: POSTGRES_16, db-f1-micro, zonal, 10 GB
  backups       off
  network       public IP on, 0 authorized networks
  databases     postgres, documind
  users         chat, postgres
  the DSN       secret documind-checkpoint-dsn, 1 version(s), the latest enabled
  setup job     last run 2026-09-12T10:41, succeeded 1
  images        job chat:3f9c2a1d0b7e, service chat:8e41d7c2f5a9 - DIFFERENT
  ADK sessions  in memory: ADK DatabaseSessionService unavailable (The 'sqlalchemy' packa
```

### demo_05_the_tables_and_one_row_per_thread.py

Do it

**`step_01_the_tables_and_one_row_per_thread(session)` — The tables, and one row per thread / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the tables, their rows, and one row per thread).

Expected shape, not a promised result:

```text
documind-ai-YOUR-ID:asia-south1:documind-checkpoint, database documind, as chat: 4 tables
  checkpoint_blobs           35 rows
  checkpoint_migrations      10 rows
  checkpoint_writes          37 rows
  checkpoints                29 rows
setup() has applied migrations 0 to 9
one row per thread, the latest first:
  acme  documind-ui-sa  lesson111-4242-b     8 checkpoints  step  6  2026-09-23T10:03
  acme  documind-ui-sa  lesson111-4242       6 checkpoints  step  4  2026-09-23T10:02
  acme  documind-ui-sa  smoke-langgraph      5 checkpoints  step  3  2026-09-23T09:16
  acme  documind-ui-sa  smoke-langchain      5 checkpoints  step  3  2026-09-23T09:15
  acme  documind-ui-sa  lesson103            5 checkpoints  step  3  2026-09-23T08:41
no ADK tables: the ADK brain's sessions are not in this database
```

### demo_06_one_thread_step_by_step.py

Do it

**`step_01_one_thread_step_by_step(session)` — One thread, step by step / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the latest thread, step by step).

Expected shape, not a promised result:

```text
the latest thread, session lesson111-4242-b: its checkpoints in order
  step -1  input  messages unchanged
  step  0  loop   messages, version 1:    175 bytes
  step  1  loop   messages, version 2:    412 bytes
  step  2  input  messages unchanged
  step  3  loop   messages, version 3:    586 bytes
  step  4  loop   messages, version 4:    866 bytes
  step  5  loop   messages, version 5:  2,325 bytes
  step  6  loop   messages, version 6:  2,562 bytes
every version kept: 6,926 bytes; the latest alone: 2,562 bytes
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_6.6_Durable_Storage_WIX.html`. All 19 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `3f82eb1abf6a809f82f7d6b46288248b73c26c3e`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
