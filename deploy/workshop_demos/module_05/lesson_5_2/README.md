# Lesson 5.2: Expose, discover and invoke MCP tools

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_expose_what_the_server_declares.py](demo_03_expose_what_the_server_declares.py) | Expose: what the server declares |
| 4 | [demo_04_start_the_server_on_your_machine.py](demo_04_start_the_server_on_your_machine.py) | Start the server on your machine |
| 5 | [demo_05_discover_tools_list_on_the_wire.py](demo_05_discover_tools_list_on_the_wire.py) | Discover: tools/list on the wire |
| 6 | [demo_06_invoke_retrieve_from_a_local_client.py](demo_06_invoke_retrieve_from_a_local_client.py) | Invoke: retrieve from a local client |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The deployed retrieval API for local MCP calls; preparation installs fastmcp in the selected interpreter.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [cleanup/demo_06_invoke_retrieve_from_a_local_client.py](cleanup/demo_06_invoke_retrieve_from_a_local_client.py) — At lesson end: Do it: stop the server
- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done. Step 1's panel and the last point of step 7 are about doc_type filters, and a filter finds a row by its class. On your lane every text row still carries unknown, the label the worker writes, so a class filter finds nothing (lesson 2.1). make doc-types SEED=manifest writes acme's doc_type registry from the kit's evals/manifest.json: each document's class, pinned to the version it was reviewed at. Then it prints the view, one line per document, and the relabel's plan. APPLY=1 carries out the plan. It moves the stored rows to their classes in Firestore, Vector Search, Vertex AI Search and BigQuery, and expires acme's answer cache. Nothing is uploaded again, and no row is embedded again unless its vector is not the declared model's. The relabel needs the index's name, which the first line reads off your lane. Lesson 10.4 teaches the registry and the relabel in full. If make stops with error 3, BigQuery deferred a statement for rows still in its streaming buffer. The other stores are relabelled, and the same line run again later finishes it. Lesson 5.5 expects every text row unknown again, so the last cell puts the rows back when you finish this lesson. It keeps the registry.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The shell, in the kit's folder, with PROJECT, REGION, API and tok. You need fastmcp 3.4.7 in the operator venv, and the first cell installs it. Step 4 starts the kit's server on port 8121 of your machine, as a background process that uses your credentials. It reads the roster from Firestore and asks rag-api as documind-ui-sa. Step 6 stops it. The box below gives acme's stored rows their classes for this lesson, and its last cell, when you finish, puts them back; nothing else on your lane changes. Step 1's panel and the last point of step 7 are about doc_type filters, and a filter finds a row by its class. On your lane every text row still carries unknown, the label the worker writes, so a class filter finds nothing (lesson 2.1). make doc-types SEED=manifest writes acme's doc_type registry from the kit's evals/manifest.json: each document's class, pinned to the version it was reviewed at. Then it prints the view, one line per document, and the relabel's plan. APPLY=1 carries out the plan. It moves the stored rows to their classes in Firestore, Vector Search, Vertex AI Search and BigQuery, and expires acme's answer cache. Nothing is uploaded again, and no row is embedded again unless its vector is not the declared model's. The relabel needs the index's name, which the first line reads off your lane. Lesson 10.4 teaches the registry and the relabel in full.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

The shell, in the kit's folder, with PROJECT, REGION, API and tok. You need fastmcp 3.4.7 in the operator venv, and the first cell installs it. Step 4 starts the kit's server on port 8121 of your machine, as a background process that uses your credentials. It reads the roster from Firestore and asks rag-api as documind-ui-sa. Step 6 stops it. The box below gives acme's stored rows their classes for this lesson, and its last cell, when you finish, puts them back; nothing else on your lane changes. Step 1's panel and the last point of step 7 are about doc_type filters, and a filter finds a row by its class. On your lane every text row still carries unknown, the label the worker writes, so a class filter finds nothing (lesson 2.1). make doc-types SEED=manifest writes acme's doc_type registry from the kit's evals/manifest.json: each document's class, pinned to the version it was reviewed at. Then it prints the view, one line per document, and the relabel's plan. APPLY=1 carries out the plan. It moves the stored rows to their classes in Firestore, Vector Search, Vertex AI Search and BigQuery, and expires acme's answer cache. Nothing is uploaded again, and no row is embedded again unless its vector is not the declared model's. The relabel needs the index's name, which the first line reads off your lane. Lesson 10.4 teaches the registry and the relabel in full.

Operation: bash — run in the operator shell, in the kit (acme's registry from the manifest, then its stored rows relabelled: a few minutes).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/doc_types.txt]
```

### demo_03_expose_what_the_server_declares.py

Do it: fastmcp Do it: what the server declares

**`step_01_fastmcp(session)` — Expose: what the server declares / Do it: fastmcp**

Do it: fastmcp

Operation: bash — run in the operator shell, in the kit (fastmcp in the operator venv).

Expected shape, not a promised result:

```text
fastmcp 3.4.7
```

**`step_02_what_the_server_declares(session)` — Expose: what the server declares / Do it: what the server declares**

Do it: what the server declares

Operation: bash — run in the operator shell, in the kit (the server imported and listed in memory; no network).

Expected shape, not a promised result:

```text
server DocuMind, protocol 2025-11-25
instructions: DocuMind answers questions about a tenant's documents with citations. Use `ret...
retrieve: Retrieve grounded passages from DocuMind's corpus, with the...
   query            string          required            The question, in natural...
   doc_type         string          default 'all'       policy, contract, invoice,...
   top_k            integer         default 5           How many passages to return...
   tenant           string or null  default None        Only if you belong to several...
list_documents: What is in the caller's corpus: one row per uploaded document,...
   status           string          default 'indexed'   indexed, processing, failed,...
   tenant           string or null  default None        Only if you belong to several...
corpus_stats: Chunks and documents in the caller's corpus, by document type...
   tenant           string or null  default None        Only if you belong to several...
calculate_processing_cost: Estimate document processing cost in USD and INR.
   total_pages      integer         required            Total page count across all...
   num_documents    integer         default 1           How many documents those...
   processing_type  string          default 'standard'  Service tier - standard,...
```

### demo_04_start_the_server_on_your_machine.py

Do it

**`step_01_start_the_server_on_your_machine(session)` — Start the server on your machine / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the kit's server on your machine, in the background).

IDE adaptation: Start an owned server with a bounded health check and saved PID/log, instead of an unbounded shell loop. Tokens are minted in each calling demo, never stored between runs.

Expected shape, not a promised result:

```text
{"status":"ok","profile":"gcp","self_url":"http://localhost:8121"}
```

### demo_05_discover_tools_list_on_the_wire.py

Do it

**`step_01_discover_tools_list_on_the_wire(session)` — Discover: tools/list on the wire / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (tools/list, raw).

IDE adaptation: Mint fresh local-server audience tokens in this process; secret tokens are intentionally excluded from persisted session state.

Expected shape, not a promised result:

```text
HTTP 200, text/event-stream, first line: event: message
tools/list: 4 tools
  retrieve                   needs query        may take doc_type, top_k, tenant
  list_documents             needs nothing      may take status, tenant
  corpus_stats               needs nothing      may take tenant
  calculate_processing_cost  needs total_pages  may take num_documents, processing_type
```

### demo_06_invoke_retrieve_from_a_local_client.py

Do it

**`step_01_invoke_retrieve_from_a_local_client(session)` — Invoke: retrieve from a local client / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (tools/call from fastmcp's client).

IDE adaptation: Mint fresh local-server audience tokens in this process; secret tokens are intentionally excluded from persisted session state.

Expected shape, not a promised result:

```text
retrieve: answerable True, 5 citations, confidence high
  'Gratuity becomes payable after not less than five years of continuous serv'
  [1] payment_of_gratuity_act_1972.pdf p.2  'rendered continuous service for not '
  [2] payment_of_gratuity_act_1972.pdf p.2  'the completion of continuous service'
  [3] payment_of_gratuity_act_1972.pdf p.2  'for every completed year of service '
an argument it refuses: doc_type must be one of ('policy', 'contract', 'invoice',
    'report', 'statute', 'guidance', 'form', 'research_paper') or all, not 'memo'
a tenant not on your roster: documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    is not on tenant 'initech''s roster
a token without an email lists 4 tools, and calls:
  not authenticated: the bearer token carries no verified email
```

### cleanup/demo_06_invoke_retrieve_from_a_local_client.py

At lesson end: Do it: stop the server

**`step_01_stop_the_server(session)` — Invoke: retrieve from a local client / Do it: stop the server**

Do it: stop the server

Operation: bash — run in the operator shell, in the kit (stop the server, read what it logged).

IDE adaptation: Stop only this session's verified process group and inspect its saved log; never kill an unverified saved shell PID.

Expected shape, not a promised result:

```text
mcp_call retrieve  tenant acme  caller documind-ui-sa  via iam  {'answerable': True, 'citations': 5, 'error': None}
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done. Step 1's panel and the last point of step 7 are about doc_type filters, and a filter finds a row by its class. On your lane every text row still carries unknown, the label the worker writes, so a class filter finds nothing (lesson 2.1). make doc-types SEED=manifest writes acme's doc_type registry from the kit's evals/manifest.json: each document's class, pinned to the version it was reviewed at. Then it prints the view, one line per document, and the relabel's plan. APPLY=1 carries out the plan. It moves the stored rows to their classes in Firestore, Vector Search, Vertex AI Search and BigQuery, and expires acme's answer cache. Nothing is uploaded again, and no row is embedded again unless its vector is not the declared model's. The relabel needs the index's name, which the first line reads off your lane. Lesson 10.4 teaches the registry and the relabel in full. If make stops with error 3, BigQuery deferred a statement for rows still in its streaming buffer. The other stores are relabelled, and the same line run again later finishes it. Lesson 5.5 expects every text row unknown again, so the last cell puts the rows back when you finish this lesson. It keeps the registry.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Step 1's panel and the last point of step 7 are about doc_type filters, and a filter finds a row by its class. On your lane every text row still carries unknown, the label the worker writes, so a class filter finds nothing (lesson 2.1). make doc-types SEED=manifest writes acme's doc_type registry from the kit's evals/manifest.json: each document's class, pinned to the version it was reviewed at. Then it prints the view, one line per document, and the relabel's plan. APPLY=1 carries out the plan. It moves the stored rows to their classes in Firestore, Vector Search, Vertex AI Search and BigQuery, and expires acme's answer cache. Nothing is uploaded again, and no row is embedded again unless its vector is not the declared model's. The relabel needs the index's name, which the first line reads off your lane. Lesson 10.4 teaches the registry and the relabel in full. If make stops with error 3, BigQuery deferred a statement for rows still in its streaming buffer. The other stores are relabelled, and the same line run again later finishes it. Lesson 5.5 expects every text row unknown again, so the last cell puts the rows back when you finish this lesson. It keeps the registry.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs: the cell's own commands, which put back what the lesson changed.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/doc_types_reset.txt]
```

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_5.2_MCP_Tools_WIX.html`. All 24 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `c8d94db34e2bd24045e0c60768c637d37f426c68`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
