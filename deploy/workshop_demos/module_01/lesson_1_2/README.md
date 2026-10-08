# Lesson 1.2: Parse documents and compare chunk boundaries

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_parse_document_ai_chosen_by_residency.py](demo_03_parse_document_ai_chosen_by_residency.py) | Parse: Document AI, chosen by residency |
| 4 | [demo_04_count_pages_first_slices_and_the_250_page_line.py](demo_04_count_pages_first_slices_and_the_250_page_line.py) | Count pages first: slices, and the 250-page line |
| 5 | [demo_05_chunk_by_section_the_handbook_becomes_283_clauses.py](demo_05_chunk_by_section_the_handbook_becomes_283_clauses.py) | Chunk by section: the handbook becomes 283 clauses |
| 6 | [demo_06_chunk_by_window_an_act_becomes_page_windows.py](demo_06_chunk_by_window_an_act_becomes_page_windows.py) | Chunk by window: an Act becomes page windows |
| 7 | [demo_07_compare_the_boundaries_two_parsers_one_document.py](demo_07_compare_the_boundaries_two_parsers_one_document.py) | Compare the boundaries: two parsers, one document |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Module 0 deployment and the seeded HR handbook/Code on Wages corpus.

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

### demo_03_parse_document_ai_chosen_by_residency.py

Two read-only calls. The first prints the worker's environment, where the residency and the processor id live. The second asks the Document AI API to list the processors in each of the two possible locations; exactly one location will list documind-parser.

**`step_01_which_reader_does_your_lane_have(session)` — Parse: Document AI, chosen by residency / Call it: which reader does your lane have?**

Two read-only calls. The first prints the worker's environment, where the residency and the processor id live. The second asks the Document AI API to list the processors in each of the two possible locations; exactly one location will list documind-parser.

Operation: bash — run in the operator shell.

Expected shape, not a promised result:

```text
{'name': 'RESIDENCY', 'value': 'us'}
{'name': 'DOCAI_PROCESSOR_ID', 'value': 'a1b2c3d4e5f6a7b8'}
== us ==
documind-parser LAYOUT_PARSER_PROCESSOR ENABLED
== asia-south1 ==
(none)
```

### demo_04_count_pages_first_slices_and_the_250_page_line.py

The same count, on the PDFs in your kit folder, with the same library. The cell prints pages and slices per PDF, then the totals and what one parse of the whole corpus would cost at each processor's list price - the rates as the course reads them on the pricing page, to re-verify before quoting. The amendment Act is four pages and globex does not hold it, so ingesting it there is a fresh source, one Document AI request, and a few paise. Then read the worker's line for it, which carries the page count as pages.

**`step_01_count_the_corpus_rs_0(session)` — Count pages first: slices, and the 250-page line / Do it: count the corpus, Rs 0**

The same count, on the PDFs in your kit folder, with the same library. The cell prints pages and slices per PDF, then the totals and what one parse of the whole corpus would cost at each processor's list price - the rates as the course reads them on the pricing page, to re-verify before quoting.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
acme/cgst_act_2017.pdf                           pages= 236 slices= 16 inline
acme/code_on_social_security_2020.pdf            pages= 116 slices=  8 inline
acme/code_on_wages_2019.pdf                      pages=  29 slices=  2 inline
acme/maternity_benefit_amendment_act_2017.pdf    pages=   4 slices=  1 inline
acme/posh_act_2013.pdf                           pages=  13 slices=  1 inline
...
zeta/osh_code_2020.pdf                           pages=  86 slices=  6 inline

1065 pages in 79 Document AI requests
one full parse: OCR Rs 136   Layout Parser Rs 905
```

**`step_02_prove_it_on_the_lane_one_small_pdf_four_pa(session)` — Count pages first: slices, and the 250-page line / Prove it on the lane: one small PDF, four pages**

The amendment Act is four pages and globex does not hold it, so ingesting it there is a fresh source, one Document AI request, and a few paise. Then read the worker's line for it, which carries the page count as pages.

Operation: bash — run in the operator shell, in $DEMO_ROOT (costs about four pages of Document AI).

Expected shape, not a promised result:

```text
globex_e7a1c0...    4    5    5
```

### demo_05_chunk_by_section_the_handbook_becomes_283_clauses.py

Do it: cut the handbook, Rs 0 The worker cut the same file with the same rule when the corpus was loaded. Its rows for the handbook should be the same 283 locators in the same order.

**`step_01_cut_the_handbook_rs_0(session)` — Chunk by section: the handbook becomes 283 clauses / Do it: cut the handbook, Rs 0**

Do it: cut the handbook, Rs 0

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
283 chunks from 282 headings
  preamble   section=None                               chars=   97  hash=903e2b39ee92
  NP-03      section=NP-03 — Notice period              chars=  234  hash=f4512754ae41
  PB-02      section=PB-02 — Probation                  chars=  212  hash=bb65ccc2494c
  LV-01      section=LV-01 — Earned leave               chars=  189  hash=ff463cede286
  LV-07      section=LV-07 — Leave on exit              chars=  167  hash=7b5538b88f78
sections windowed within themselves: []
```

**`step_02_on_the_lane(session)` — Chunk by section: the handbook becomes 283 clauses / Read it on the lane**

The worker cut the same file with the same rule when the corpus was loaded. Its rows for the handbook should be the same 283 locators in the same order.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
lane: 283 local: 283 same locators in the same order: True
same hashes: True
```

### demo_06_chunk_by_window_an_act_becomes_page_windows.py

Your kit has a text mirror of every Act, made by pypdf when the corpus was fetched, with a form feed between pages. Cut the mirror of the Code on Wages and look at one seam. Read it on the lane, and ask a question that lands on a page

**`step_01_cut_the_code_on_wages_rs_0(session)` — Chunk by window: an Act becomes page windows / Do it: cut the Code on Wages, Rs 0**

Your kit has a text mirror of every Act, made by pypdf when the corpus was fetched, with a form feed between pages. Cut the mirror of the Code on Wages and look at one seam.

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
pages in the mirror: 29
65 windows; the first six locators: ['p1-0', 'p2-0', 'p2-1', 'p3-0', 'p3-1', 'p4-0']
p2-0 is 2000 chars; p2-1 is 1201 chars
end of p2-0 -> 'th or without the knowledge of the\nprincipal employer and includ'
start of p2-1 -> 'in or\nin connection with the work of an establishment when he'
the overlap: the last 200 characters of p2-0 reappear at the start of p2-1 -> True
```

**`step_02_on_the_lane_and_ask_a_question_that_lands(session)` — Chunk by window: an Act becomes page windows / Read it on the lane, and ask a question that lands on a page**

Read it on the lane, and ask a question that lands on a page

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

**`step_03_on_the_lane_and_ask_a_question_that_lands(session)` — Chunk by window: an Act becomes page windows / Read it on the lane, and ask a question that lands on a page**

Read it on the lane, and ask a question that lands on a page

Operation: bash — run in the operator shell (acme pinned to vector, see the setup).

Expected shape, not a promised result:

```text
67 windows on the lane; first six: ['p1-0', 'p2-0', 'p2-1', 'p3-0', 'p3-1', 'p4-0']
pages seen: [1, 2, 3, 4, 5] ... 29
Under the Code on Wages, wages must be paid within seven days after the end of the wage period ... [Source 1]
19 code_on_wages_2019.pdf page 9 | (iv) monthly basis, before the expiry of the seventh day of the succ
20 code_on_wages_2019.pdf page 9 | ...
```

### demo_07_compare_the_boundaries_two_parsers_one_document.py

See it, page by page

**`step_01_see_it_page_by_page(session)` — Compare the boundaries: two parsers, one document / See it, page by page**

See it, page by page

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
lane 67 windows, mirror 65 windows
pages with a different number of windows: [(7, 3, 2), (23, 3, 2)]
p2-0 on the lane: 2000 chars, hash 4c19e0b7a2d8
p2-0 in the mirror: 2000 chars, hash 6a3f7e9c01b5
lane text starts: 'THE CODE ON WAGES, 2019\nCHAPTER I\nPRELIMINARY\n1. (1) This Code may be called ...'
mirror text starts: 'THE CODE ON WAGES, 2019 CHAPTER I PRELIMINARY 1. (1) This Code may be called ...'
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_1.2_Parse_Chunk_WIX.html`. All 29 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `b099dbefa1a1ac6ed8c033e6e86ca49edce9f313`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
