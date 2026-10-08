# Lesson 5.4: Implement the main LangGraph workflow

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_graph_in_a_venv_of_its_own.py](demo_03_the_graph_in_a_venv_of_its_own.py) | The graph, in a venv of its own |
| 4 | [demo_04_the_refuse_node_forced_to_fire.py](demo_04_the_refuse_node_forced_to_fire.py) | The refuse node, forced to fire |
| 5 | [demo_05_the_graph_on_your_lane_one_thread_a_new_thread_and_a_request_to_delete.py](demo_05_the_graph_on_your_lane_one_thread_a_new_thread_and_a_request_to_delete.py) | The graph on your lane: one thread, a new thread, and a request to delete |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The deployed chat lane from 5.1; framework dependencies are installed by this lesson's preparation.

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

### demo_03_the_graph_in_a_venv_of_its_own.py

Do it: the venv Do it: the graph

**`step_01_the_venv(session)` — The graph, in a venv of its own / Do it: the venv**

Do it: the venv

Operation: bash — run in the operator shell, in the kit (a small venv with the chat image's LangChain pins; a minute or two).

Expected shape, not a promised result:

```text
graph-venv ok: langchain 1.4.0
```

**`step_02_the_graph(session)` — The graph, in a venv of its own / Do it: the graph**

Do it: the graph

Operation: bash — run in the operator shell, in the kit (the kit's graph, built and listed; no network, no model).

Expected shape, not a promised result:

```text
nodes: __start__, agent, tools, refuse, __end__
  __start__ -> agent    
      agent -> __end__    (route decides)
      agent -> refuse     (route decides)
      agent -> tools      (route decides)
     refuse -> agent    
      tools -> agent
```

### demo_04_the_refuse_node_forced_to_fire.py

Do it

**`step_01_the_refuse_node_forced_to_fire(session)` — The refuse node, forced to fire / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (three scripted turns through the kit's own graph; no network, no model).

Expected shape, not a promised result:

```text
plain    agent -> tools -> agent          tool_calls ['retrieve']  refusals []
           answer: After five years of continuous service [1].
  blocked  agent -> refuse -> agent         tool_calls ['delete_document']  refusals ['delete_document']
           error result for delete_document: {"error": "delete_document requires manual approval"}
           answer: I could not delete the invoice: deleting a document requires manual approval, so
  mixed    agent -> refuse -> agent         tool_calls ['retrieve', 'delete_document']  refusals ['retrieve', 'delete_document']
           error result for retrieve: {"error": "retrieve requires manual approval"}
           error result for delete_document: {"error": "delete_document requires manual approval"}
           answer: Nothing was done: that request needs manual approval.
```

### demo_05_the_graph_on_your_lane_one_thread_a_new_thread_and_a_request_to_delete.py

Do it

**`step_01_the_graph_on_your_lane_one_thread_a_new_th(session)` — The graph on your lane: one thread, a new thread, and a request to delete / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (four turns to the LangGraph brain on your lane).

Expected shape, not a promised result:

```text
[lesson102] tool_calls ['retrieve']  refusals []  7310 ms
      Gratuity becomes payable after not less than five years of continuous service, under the Payment of Gratuity A
  [lesson102] tool_calls ['retrieve']  refusals []  6890 ms
      Under the Code on Social Security, 2020, a fixed-term employee is paid gratuity on a pro rata basis, without t
  [lesson102-new] tool_calls []  refusals []  2140 ms
      Could you tell me what you would like to know about? For example, gratuity or leave for fixed-term employees u
  [lesson102] tool_calls []  refusals []  1980 ms
      I can't delete documents - I can only search and read them. Removing the April invoice needs someone with acce
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_5.4_LangGraph_WIX.html`. All 19 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `0f0a7699c5f7e6eb5b1785fcdc570c29b0198022`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
