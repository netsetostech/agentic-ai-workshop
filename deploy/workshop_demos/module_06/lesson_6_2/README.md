# Lesson 6.2: Compare context caching and answer caching

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_context_cache_a_pack_a_cache_and_the_next_answer.py](demo_03_the_context_cache_a_pack_a_cache_and_the_next_answer.py) | The context cache: a pack, a cache, and the next answer |
| 4 | [demo_04_the_rows_what_the_context_cache_did_to_the_bill.py](demo_04_the_rows_what_the_context_cache_did_to_the_bill.py) | The rows: what the context cache did to the bill |
| 5 | [demo_05_the_answer_cache_a_candidate_that_remembers_answers.py](demo_05_the_answer_cache_a_candidate_that_remembers_answers.py) | The answer cache: a candidate that remembers answers |
| 6 | [demo_06_four_asks_a_miss_two_hits_and_a_paraphrase.py](demo_06_four_asks_a_miss_two_hits_and_a_paraphrase.py) | Four asks: a miss, two hits and a paraphrase |
| 7 | [demo_07_what_each_cache_is_holding_and_the_clean_up.py](demo_07_what_each_cache_is_holding_and_the_clean_up.py) | What each cache is holding, and the clean-up |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [cleanup/demo_07_what_each_cache_is_holding_and_the_clean_up.py](cleanup/demo_07_what_each_cache_is_holding_and_the_clean_up.py) — At lesson end: The cell prints tenant_caches/acme, then the answer-cache entry for the question's words. It uses the kit's own qhash, imported from services/rag-api, so the key is computed exactly as the API computes it. The two records show where each cache keeps its weight. For the context cache, Firestore holds only a pointer and a few facts, and the pack's forty-odd thousand tokens sit on Google's side, billed by the hour until they expire or are deleted. For the answer cache, Firestore holds everything: the answer, its citations and the question's 768-number embedding. That costs Firestore storage and reads, for 24 hours. The clean-up removes the candidate's tag and recorded name, and deletes the context cache. The next acme question to the live API finds no record and runs uncached at once.
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

### demo_03_the_context_cache_a_pack_a_cache_and_the_next_answer.py

Do it: the question, uncached Do it: the cache Do it: the same question, with the cache

**`step_01_the_question_uncached(session)` — The context cache: a pack, a cache, and the next answer / Do it: the question, uncached**

Do it: the question, uncached

Operation: bash — run in the operator shell, in the kit (a small ask function, a start time for the rows, and one question to the live API).

Expected shape, not a promised result:

```text
backend vertex cache_hit none     tokens_in   1812  cached_tokens      0   2410 ms  | Employees may work remotely up to eight days
```

**`step_02_the_cache(session)` — The context cache: a pack, a cache, and the next answer / Do it: the cache**

Do it: the cache

Operation: bash — run in the operator shell, in the kit (acme's context cache: its pack, on Gemini, for an hour).

Expected shape, not a promised result:

```text
cd services/rag-api && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=gemini-3.6-flash \
  python cache_admin.py ${CACHE_OP:-create} --project documind-ai-YOUR-ID --tenant acme
  cache projects/NUMBER/locations/global/cachedContents/CACHE_ID
  location global (global or regional: the answer to CLAUDE.md's question)
  model gemini-3.6-flash | tokens 41259 | expires YYYY-MM-DD HH:MM:SS.ssssss+00:00 | corpus 75b21a03f12f | ledger fingerprint FINGERPRINT
  the next /v1/query for acme carries cached_content; read cached_tokens in its usage row
```

**`step_03_the_same_question_with_the_cache(session)` — The context cache: a pack, a cache, and the next answer / Do it: the same question, with the cache**

Do it: the same question, with the cache

Operation: bash — run in the operator shell, in the kit (the same question again, to the live API).

Expected shape, not a promised result:

```text
backend vertex cache_hit none     tokens_in  43071  cached_tokens  41259   2650 ms  | Employees may work remotely up to eight days
```

### demo_04_the_rows_what_the_context_cache_did_to_the_bill.py

Do it

**`step_01_the_rows_what_the_context_cache_did_to_the(session)` — The rows: what the context cache did to the bill / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (every acme usage row since the first ask; reads only).

Expected shape, not a promised result:

```text
00041-kqz  vertex  in   1812  cached      0  Rs 0.4937   2410 ms
  00041-kqz  vertex  in  43071  cached  41259  Rs 1.0197   2650 ms
```

### demo_05_the_answer_cache_a_candidate_that_remembers_answers.py

Do it

**`step_01_the_answer_cache_a_candidate_that_remember(session)` — The answer cache: a candidate that remembers answers / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (a revision with SEMANTIC_CACHE=on and no traffic).

Expected shape, not a promised result:

```text
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \
  --update-env-vars "^|^GENERATOR_MODEL=gemini-3.6-flash|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=off|SEMANTIC_CACHE=on|..."
...
>> candidate revision: documind-api-00044-rtv (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app
```

### demo_06_four_asks_a_miss_two_hits_and_a_paraphrase.py

One question four ways, then the rows. The first ask is a miss: the candidate has never seen the question, so it retrieves, calls the model and stores the answer. The second is the same words, for the exact rung. The third is the same words in lower case without the question mark, which qhash treats as identical. The fourth says the same thing in other words. It is a hit only if its embedding lands within 0.95 of the first question's; otherwise it is a miss, and its own answer is stored beside the first.

**`step_01_four_asks_a_miss_two_hits_and_a_paraphrase(session)` — Four asks: a miss, two hits and a paraphrase / Four asks: a miss, two hits and a paraphrase**

One question four ways, then the rows. The first ask is a miss: the candidate has never seen the question, so it retrieves, calls the model and stores the answer. The second is the same words, for the exact rung. The third is the same words in lower case without the question mark, which qhash treats as identical. The fourth says the same thing in other words. It is a hit only if its embedding lands within 0.95 of the first question's; otherwise it is a miss, and its own answer is stored beside the first.

Operation: bash — run in the operator shell, in the kit (four asks to the candidate).

Expected shape, not a promised result:

```text
backend vertex cache_hit none     tokens_in  43071  cached_tokens  41259   2590 ms  | Employees may work remotely up to eight days
  backend cache  cache_hit semantic tokens_in      0  cached_tokens      0    182 ms  | Employees may work remotely up to eight days
  backend cache  cache_hit semantic tokens_in      0  cached_tokens      0    176 ms  | Employees may work remotely up to eight days
  backend vertex cache_hit none     tokens_in  43053  cached_tokens  41259   2720 ms  | Employees may work remotely up to eight days
```

**`step_02_four_asks_a_miss_two_hits_and_a_paraphrase(session)` — Four asks: a miss, two hits and a paraphrase / Four asks: a miss, two hits and a paraphrase**

One question four ways, then the rows. The first ask is a miss: the candidate has never seen the question, so it retrieves, calls the model and stores the answer. The second is the same words, for the exact rung. The third is the same words in lower case without the question mark, which qhash treats as identical. The fourth says the same thing in other words. It is a hit only if its embedding lands within 0.95 of the first question's; otherwise it is a miss, and its own answer is stored beside the first.

Operation: bash — run in the operator shell, in the kit (the same rows cell, now with the candidate's).

Expected shape, not a promised result:

```text
00041-kqz  vertex  in   1812  cached      0  Rs 0.4937   2410 ms
  00041-kqz  vertex  in  43071  cached  41259  Rs 1.0197   2650 ms
  00044-rtv  vertex  in  43071  cached  41259  Rs 1.0197   2590 ms
  00044-rtv  cache   in      0  cached      0  Rs 0.0000    182 ms
  00044-rtv  cache   in      0  cached      0  Rs 0.0000    176 ms
  00044-rtv  vertex  in  43053  cached  41259  Rs 1.0085   2720 ms
```

### demo_07_what_each_cache_is_holding_and_the_clean_up.py

The record behind the context cache, the entry behind the hit, and both caches put away. The cell prints tenant_caches/acme, then the answer-cache entry for the question's words. It uses the kit's own qhash, imported from services/rag-api, so the key is computed exactly as the API computes it.

**`step_01_what_each_cache_is_holding_and_the_clean_u(session)` — What each cache is holding, and the clean-up / What each cache is holding, and the clean-up**

The record behind the context cache, the entry behind the hit, and both caches put away. The cell prints tenant_caches/acme, then the answer-cache entry for the question's words. It uses the kit's own qhash, imported from services/rag-api, so the key is computed exactly as the API computes it.

Operation: bash — run in the operator shell, in the kit (what each cache is holding; reads only).

Expected shape, not a promised result:

```text
context cache  (Firestore holds a pointer; the pack itself is on Google's side)
    cache_name: projects/NUMBER/locations/global/cachedContents/CACHE_ID
    location: global
    model: gemini-3.6-flash
    tokens: 41259
    expire_time: YYYY-MM-DD HH:MM:SS.ssssss+00:00
    corpus_fingerprint: FINGERPRINT
answer cache  (2 acme entries; 1 for this question's words)
    question: How many days a month can I work remotely?
    qhash: 79ae9ca70e9e21c4c23aca5b  scope: 7a0875abc72b0f7b  fingerprint: FINGERPRINT_
    model: gemini-3.6-flash  expire_at: YYYY-MM-DD HH:MM:SS+00:00  embedding: 768 numbers
    answer: Employees may work remotely up to eight days per month with   citations: 1
```

### cleanup/demo_07_what_each_cache_is_holding_and_the_clean_up.py

At lesson end: The cell prints tenant_caches/acme, then the answer-cache entry for the question's words. It uses the kit's own qhash, imported from services/rag-api, so the key is computed exactly as the API computes it. The two records show where each cache keeps its weight. For the context cache, Firestore holds only a pointer and a few facts, and the pack's forty-odd thousand tokens sit on Google's side, billed by the hour until they expire or are deleted. For the answer cache, Firestore holds everything: the answer, its citations and the question's 768-number embedding. That costs Firestore storage and reads, for 24 hours. The clean-up removes the candidate's tag and recorded name, and deletes the context cache. The next acme question to the live API finds no record and runs uncached at once.

**`step_01_what_each_cache_is_holding_and_the_clean_u(session)` — What each cache is holding, and the clean-up / What each cache is holding, and the clean-up**

The cell prints tenant_caches/acme, then the answer-cache entry for the question's words. It uses the kit's own qhash, imported from services/rag-api, so the key is computed exactly as the API computes it. The two records show where each cache keeps its weight. For the context cache, Firestore holds only a pointer and a few facts, and the pack's forty-odd thousand tokens sit on Google's side, billed by the hour until they expire or are deleted. For the answer cache, Firestore holds everything: the answer, its citations and the question's 768-number embedding. That costs Firestore storage and reads, for 24 hours. The clean-up removes the candidate's tag and recorded name, and deletes the context cache. The next acme question to the live API finds no record and runs uncached at once.

Operation: bash — run in the operator shell, in the kit (the candidate's tag and recorded name removed, the context cache deleted).

Expected shape, not a promised result:

```text
Updating traffic...done.
Done.
URL: https://documind-api-...run.app
Traffic:
  100% documind-api-00041-kqz      (the live revision, as before; no candidate tag)
cd services/rag-api && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=gemini-3.6-flash \
  python cache_admin.py ${CACHE_OP:-create} --project documind-ai-YOUR-ID --tenant acme
  deleted acme's cache
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_6.2_Cache_Compare_WIX.html`. All 32 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `9863ad496e4fb405ef06d3ff2257a01666b35f6a`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
