# Lesson 8.3: Size RAG for ten million documents

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_ui_your_corpus_counted_by_the_lane.py](demo_03_the_ui_your_corpus_counted_by_the_lane.py) | The UI: your corpus, counted by the lane |
| 5 | [demo_05_measure_the_corpus_with_the_kit_s_own_chunker.py](demo_05_measure_the_corpus_with_the_kit_s_own_chunker.py) | Measure the corpus with the kit's own chunker |
| 6 | [demo_06_rest_the_index_s_own_size.py](demo_06_rest_the_index_s_own_size.py) | REST: the index's own size |
| 7 | [demo_07_direct_reads_firestore_s_counts_and_the_worker_s_seconds.py](demo_07_direct_reads_firestore_s_counts_and_the_worker_s_seconds.py) | Direct reads: Firestore's counts and the worker's seconds |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson asks DocuMind no question: it reads counts, sizes and logs, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. If you ran it, leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson asks DocuMind no question: it reads counts, sizes and logs, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson asks DocuMind no question: it reads counts, sizes and logs, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_ui_your_corpus_counted_by_the_lane.py

The chunk counts the lane recorded, document by document, before any arithmetic. Every size on this page starts from one number: how many chunks a document becomes. Your lane has already counted them, document by document, when the worker ingested the corpus. Read those counts first, in the browser, where an operator would. The UI's address is built from your project number, as the setup block built API: The five Markdown documents went up as text, and the worker chunks text by exactly the rules the offline count uses, so their rows should match the table digit for digit. The Acts and the compliance handbook went up as PDFs: the worker sent each to Document AI, whose text is not byte for byte the pypdf text the offline count reads, so their counts can differ by a few chunks. Your table also has rows this one does not: the three figures, which the worker describes in words and embeds as one chunk each, and posh_act_2013, a scanned Act that only Document AI can read. The town hall is a text row unless you made its video in lesson 7.5; then the video takes its place. The same rows come from the shell. make sources reads the ledger in Firestore directly, as you, the operator, with your Application Default Credentials. The UI asked the API, as you, and the API first checked your email against acme's roster. One table, two callers: The same rows come from the shell. make sources reads the ledger in Firestore directly, as you, the operator, with your Application Default Credentials. The UI asked the API, as you, and the API first checked your email against acme's roster. One table, two callers: The last line is the ledger's summary for the tenant: its fingerprint and its count of current versions. Then the index itself. make vector-status asks gcloud to describe the Vector Search index and its deployment:

**`step_01_the_ui_your_corpus_counted_by_the_lane(session)` — The UI: your corpus, counted by the lane / The UI: your corpus, counted by the lane**

The chunk counts the lane recorded, document by document, before any arithmetic. Every size on this page starts from one number: how many chunks a document becomes. Your lane has already counted them, document by document, when the worker ingested the corpus. Read those counts first, in the browser, where an operator would. The UI's address is built from your project number, as the setup block built API:

Operation: bash — run in the operator shell (prints your UI's address).

Expected shape, not a promised result:

```text
https://documind-ui-NUMBER.asia-south1.run.app
```

**`step_02_the_ui_your_corpus_counted_by_the_lane(session)` — The UI: your corpus, counted by the lane / The UI: your corpus, counted by the lane**

The five Markdown documents went up as text, and the worker chunks text by exactly the rules the offline count uses, so their rows should match the table digit for digit. The Acts and the compliance handbook went up as PDFs: the worker sent each to Document AI, whose text is not byte for byte the pypdf text the offline count reads, so their counts can differ by a few chunks. Your table also has rows this one does not: the three figures, which the worker describes in words and embeds as one chunk each, and posh_act_2013, a scanned Act that only Document AI can read. The town hall is a text row unless you made its video in lesson 7.5; then the video takes its place. The same rows come from the shell. make sources reads the ledger in Firestore directly, as you, the operator, with your Application Default Credentials. The UI asked the API, as you, and the API first checked your email against acme's roster. One table, two callers:

Operation: bash — run in the operator shell, in the kit (reads the ledger; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/sources_acme.txt]
```

**`step_03_the_ui_your_corpus_counted_by_the_lane(session)` — The UI: your corpus, counted by the lane / The UI: your corpus, counted by the lane**

The same rows come from the shell. make sources reads the ledger in Firestore directly, as you, the operator, with your Application Default Credentials. The UI asked the API, as you, and the API first checked your email against acme's roster. One table, two callers: The last line is the ledger's summary for the tenant: its fingerprint and its count of current versions. Then the index itself. make vector-status asks gcloud to describe the Vector Search index and its deployment:

Operation: bash — run in the operator shell, in the kit (two gcloud describes; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/vector_status.txt]
```

### demo_05_measure_the_corpus_with_the_kit_s_own_chunker.py

The averages the arithmetic multiplies, from the kit's code on the kit's files, in a second, with no network. The cell below loads every text document of the three tenants with shared/documind_corpus.py, the loader, chunker and batcher the notebooks share. They apply the worker's two rules, 2,000 characters with 200 of overlap and a section per ## heading, and the worker's two ceilings on a request. It counts, by document type, the characters, the chunks, the characters sent and the requests, then multiplies by 10,000,000. It reads only files in your clone of the kit: nothing on the lane, nothing billed.

**`step_01_measure_the_corpus_with_the_kit_s_own_chun(session)` — Measure the corpus with the kit's own chunker / Measure the corpus with the kit's own chunker**

The averages the arithmetic multiplies, from the kit's code on the kit's files, in a second, with no network. The cell below loads every text document of the three tenants with shared/documind_corpus.py, the loader, chunker and batcher the notebooks share. They apply the worker's two rules, 2,000 characters with 200 of overlap and a section per ## heading, and the worker's two ceilings on a request. It counts, by document type, the characters, the chunks, the characters sent and the requests, then multiplies by 10,000,000. It reads only files in your clone of the kit: nothing on the lane, nothing billed.

Operation: bash — run in the operator shell, in the kit (no network: the kit's own code on the kit's own files).

Expected shape, not a promised result:

```text
doc_type   docs characters chunks       sent requests
contract      3      2,787     18      2,697        3
guidance      2    100,480    100    104,126        4
invoice       1        780      1        780        1
policy        2    320,769    566    317,383        8
report        1        707      4        689        1
statute      17  2,837,331  2,067  3,044,540       77
transcript    1      1,698      1      1,698        1
all          27  3,264,552  2,757  3,471,913       95

per document: 102.11 chunks, 128,589 characters sent, 3.52 requests
at 10,000,000 documents of this mix:
  vectors              1,021,111,111
  embedding requests   35,185,185
  dense index          2,921.4 GiB (768 numbers x 4 bytes a vector)
  embedding, once      Rs 27.33 lakh
```

### demo_06_rest_the_index_s_own_size.py

The index's vectors, shards and shard size, and the deployment's machine and replicas, read from the Vertex AI API. make vector-status printed the fields gcloud was asked for. The API holds more: the index's shard size, its dimensions, and the deployed index's machine and replica range. The cell reads both with two GETs, then does the one sum that matters for sizing: how much of one shard your vectors fill.

**`step_01_rest_the_index_s_own_size(session)` — REST: the index's own size / REST: the index's own size**

The index's vectors, shards and shard size, and the deployment's machine and replicas, read from the Vertex AI API. make vector-status printed the fields gcloud was asked for. The API holds more: the index's shard size, its dimensions, and the deployed index's machine and replica range. The cell reads both with two GETs, then does the one sum that matters for sizing: how much of one shard your vectors fill.

Operation: bash — run in the operator shell (two GETs on the Vertex AI API; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/index_rest.txt]
```

### demo_07_direct_reads_firestore_s_counts_and_the_worker_s_seconds.py

The rows the Firestore floor multiplies, and the one number no constant gives you: how long a document takes. Two reads finish the measurement. The first counts rows in Firestore without fetching them: a count() query returns one number instead of the rows it matched. chunk rows counts every version a tenant still holds: the current rows, and the rows a re-issue retired, which stay until their expire_at passes. current is what the index serves; added across the three tenants, it should match the index's vector count from steps 3 and 6. indexed sources is how many rows the fingerprint reads on every ingest to that tenant, which step 8 comes back to. Multiply your chunk rows by 59,092 bytes and you have your lane's Firestore floor for the chunks; for the 2,757 text chunks alone it is 155 MiB. At ten million documents it is 54.9 TiB. The second read is the calibration. Cloud Run logs every delivery Pub/Sub made to the worker, with its HTTP status and how long it took, so the median of those times is your lane's seconds per document. The cell saves the last month of deliveries, then counts them by status:

**`step_01_direct_reads_firestore_s_counts_and_the_wo(session)` — Direct reads: Firestore's counts and the worker's seconds / Direct reads: Firestore's counts and the worker's seconds**

The rows the Firestore floor multiplies, and the one number no constant gives you: how long a document takes. Two reads finish the measurement. The first counts rows in Firestore without fetching them: a count() query returns one number instead of the rows it matched.

Operation: bash — run in the operator shell (nine Firestore count queries; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/firestore_counts.txt]
```

**`step_02_direct_reads_firestore_s_counts_and_the_wo(session)` — Direct reads: Firestore's counts and the worker's seconds / Direct reads: Firestore's counts and the worker's seconds**

chunk rows counts every version a tenant still holds: the current rows, and the rows a re-issue retired, which stay until their expire_at passes. current is what the index serves; added across the three tenants, it should match the index's vector count from steps 3 and 6. indexed sources is how many rows the fingerprint reads on every ingest to that tenant, which step 8 comes back to. Multiply your chunk rows by 59,092 bytes and you have your lane's Firestore floor for the chunks; for the 2,757 text chunks alone it is 155 MiB. At ten million documents it is 54.9 TiB. The second read is the calibration. Cloud Run logs every delivery Pub/Sub made to the worker, with its HTTP status and how long it took, so the median of those times is your lane's seconds per document. The cell saves the last month of deliveries, then counts them by status:

Operation: bash — run in the operator shell (one Cloud Logging read; writes one file in your home directory).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ingest_latency.txt]
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson asks DocuMind no question: it reads counts, sizes and logs, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. If you ran it, leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson asks DocuMind no question: it reads counts, sizes and logs, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. If you ran it, leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_8.3_Size_Ten_Million_WIX.html`. All 37 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `1c3caa585c3e732c014c8b0ab3a1df7a2f200cb0`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
