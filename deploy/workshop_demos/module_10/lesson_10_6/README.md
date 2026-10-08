# Lesson 10.6: Trace the implemented A2A peer and its permissions

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_peer_s_permissions_as_the_kit_writes_them.py](demo_03_the_peer_s_permissions_as_the_kit_writes_them.py) | The peer's permissions, as the kit writes them |
| 4 | [demo_04_the_card_refused_without_a_token_read_with_one.py](demo_04_the_card_refused_without_a_token_read_with_one.py) | The card: refused without a token, read with one |
| 5 | [demo_05_the_gate_make_smoke_agent.py](demo_05_the_gate_make_smoke_agent.py) | The gate: make smoke-agent |
| 6 | [demo_06_one_task_traced.py](demo_06_one_task_traced.py) | One task, traced |

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_peer_s_permissions_as_the_kit_writes_them.py

Do it

**`step_01_the_peer_s_permissions_as_the_kit_writes_t(session)` — The peer's permissions, as the kit writes them / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the peer's permissions, as the kit writes them; no network).

Expected shape, not a promised result:

```text
documind-agent, as commands/lesson-8.4.sh deploys it:
  runs as documind-agent-sa  model gemini-3.6-flash  knows one URL: MCP_URL
  who may call it: documind-ui-sa, documind-chat-sa
  documind-agent-sa may call documind-mcp: True
  its project roles: aiplatform.user, logging.logWriter, cloudtrace.agent
  the rosters it is on: acme
  agent.py imports: __future__, google, logging, os, starlette, urllib, uvicorn
  the image copies: services/agent/requirements.txt, services/agent/
```

### demo_04_the_card_refused_without_a_token_read_with_one.py

Do it

**`step_01_the_card_refused_without_a_token_read_with(session)` — The card: refused without a token, read with one / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the card, without a token and with one).

Expected shape, not a promised result:

```text
the card without a token: HTTP 403
the card with a token: documind_peer, version 0.0.1
  answers at https://documind-agent-NUMBER.asia-south1.run.app over JSONRPC, A2A 1.0
  streaming False, input ['text/plain'], output ['text/plain']
  skills: model
```

### demo_05_the_gate_make_smoke_agent.py

Do it

**`step_01_the_gate_make_smoke_agent(session)` — The gate: make smoke-agent / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the module's A2A gate).

Expected shape, not a promised result:

```text
DocuMind A2A peer - live smoke test
  target: https://documind-agent-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  question: After how many years of continuous service does gratuity become payable?
  expected answer pattern: \b(?:five|5)(?:\s*\(\s*(?:five|5)\s*\))?[\s-]+years?\b
  [PASS] card refused without a token  status=403
  [PASS] agent card  name=documind_peer url=https://documind-agent-NUMBER.asia-south1.run.app skills=['documind_peer']
  [PASS] task answered  state=completed  'Gratuity is payable after not less than five years of continuous service [1]. Source: paym'
  [PASS] zeta refused by the roster  'The DocuMind server refused this: documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is not on tena'
  [PASS] outsider refused at the door  status=403
  --------------------------------------------------------
  5 passed, 0 failed
```

### demo_06_one_task_traced.py

Do it: the task Do it: what the lane saw

**`step_01_the_task(session)` — One task, traced / Do it: the task**

Do it: the task

Operation: bash — run in the operator shell, in the kit (one task, and its history).

Expected shape, not a promised result:

```text
a task, state completed, 4 messages in its history:
  user  text      'After how many years of continuous service does gratuity become pa'
  agent calls     retrieve(query='After how many years of continuous')
  agent receives  retrieve: 5 citations
  agent text      'Gratuity is payable after not less than five years of continuous s'
the answer: Gratuity is payable after not less than five years of continuous service [1]. Source
```

**`step_02_what_the_lane_saw(session)` — One task, traced / Do it: what the lane saw**

Do it: what the lane saw

Operation: bash — run in the operator shell, in the kit (who the lane saw).

Expected shape, not a promised result:

```text
documind-mcp - who asked it:
  retrieve        tenant acme   caller documind-agent-sa
documind-api - who it served:
  retrieve        tenant acme   user   documind-mcp-sa
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_10.6_A2A_Peer_WIX.html`. All 19 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `6f13d04435a34279510124166f441b32d6337022`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
