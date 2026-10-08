# Lesson 6.7: Verify restart recovery and session isolation

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_isolation_on_the_kit_s_own_app.py](demo_03_isolation_on_the_kit_s_own_app.py) | Isolation, on the kit's own app |
| 4 | [demo_04_a_conversation_across_a_redeploy.py](demo_04_a_conversation_across_a_redeploy.py) | A conversation across a redeploy |
| 5 | [demo_05_another_person_finds_nothing.py](demo_05_another_person_finds_nothing.py) | Another person finds nothing |
| 6 | [demo_06_the_rows_behind_both.py](demo_06_the_rows_behind_both.py) | The rows behind both |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The durable conversation storage from 6.6; the example redeploys the chat service.

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

### demo_03_isolation_on_the_kit_s_own_app.py

Do it: the venv Do it: eight callers

**`step_01_the_venv(session)` — Isolation, on the kit's own app / Do it: the venv**

Do it: the venv

Operation: bash — run in the operator shell, in the kit (lesson 5.4's venv, with the web layer and 6.6's connector).

Expected shape, not a promised result:

```text
graph-venv ok: fastapi 0.141.1
```

**`step_02_eight_callers(session)` — Isolation, on the kit's own app / Do it: eight callers**

Do it: eight callers

Operation: bash — run in the operator shell, in the kit (the kit's chat app on your machine; no model, no network).

Expected shape, not a promised result:

```text
alice gives the word, lesson113        200  Got it: saffron.
  alice asks for it                      200  You asked me to remember saffron.
  alice, a new session                   200  I have no word from you in this conversation.
  bob, her tenant, same session name     200  I have no word from you in this conversation.
  carol, another tenant, the same name   200  I have no word from you in this conversation.
  alice, the body naming zeta            200  You asked me to remember saffron.
  alice, a session id with a colon       422  String should match pattern '^[A-Za-z0-9_-]{1,64}$'
  the outsider                           403  not a member of any tenant
  a token that names nobody              401  the bearer token carries no verified email
  the threads the checkpointer holds:
    acme:alice@acme.example:lesson113
    acme:alice@acme.example:lesson113-b
    acme:bob@acme.example:lesson113
    zeta:carol@zeta.example:lesson113
  after a restart, alice asks again      200  I have no word from you in this conversation.
```

### demo_04_a_conversation_across_a_redeploy.py

Do it

**`step_01_a_conversation_across_a_redeploy(session)` — A conversation across a redeploy / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (a word, a redeploy, the word again).

Expected shape, not a promised result:

```text
serving documind-chat-00007-x4q
  langchain lesson113-4242-langchain  "Got it: saffron. I'll keep it for this conve"
  adk       lesson113-4242-adk        "Got it: saffron. I'll keep it for this conve"
serving documind-chat-00008-m2k, redeployed at 2026-09-23T11:20:41Z
  langchain lesson113-4242-langchain  saffron yes  'You asked me to remember "saffron"'
  adk       lesson113-4242-adk        saffron no   "I don't have a word from you in th"
```

### demo_05_another_person_finds_nothing.py

Do it

**`step_01_another_person_finds_nothing(session)` — Another person finds nothing / Do it**

Do it

Operation: bash — run in the operator shell (the address of your UI).

Expected shape, not a promised result:

```text
open https://documind-ui-NUMBER.asia-south1.run.app and sign in as you@example.com
```

### demo_06_the_rows_behind_both.py

Do it

**`step_01_the_rows_behind_both(session)` — The rows behind both / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the rows behind steps 4 and 5).

Expected shape, not a promised result:

```text
lesson113-4242-langchain: 6 checkpoints, 3 before the redeploy and 3 after
  lesson113-4242-adk: no rows - the ADK brain keeps none
  threads of you: 1; the latest is session 3f9c2a1d0b7e, 3 checkpoints
  threads of documind-ui-sa: 2; the latest is session lesson113-4242-langchain, 6 checkpoints
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_6.7_Restart_Isolation_WIX.html`. All 19 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `7220ffa4bff89e61f6a508a13b032fb08f8673ac`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
