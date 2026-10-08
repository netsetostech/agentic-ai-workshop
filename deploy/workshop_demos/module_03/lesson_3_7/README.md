# Lesson 3.7: Stream answers and handle failures

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_a_stream_in_curl_the_raw_events_their_order_and_a_clock_on_each.py](demo_03_a_stream_in_curl_the_raw_events_their_order_and_a_clock_on_each.py) | A stream in curl: the raw events, their order, and a clock on each |
| 4 | [demo_04_what_a_stream_s_citations_are_and_the_streams_of_one_token.py](demo_04_what_a_stream_s_citations_are_and_the_streams_of_one_token.py) | What a stream's citations are, and the streams of one token |
| 5 | [demo_05_the_guard_a_prompt_refused_before_the_stream_an_answer_held_until_it_is_screened.py](demo_05_the_guard_a_prompt_refused_before_the_stream_an_answer_held_until_it_is_screened.py) | The guard: a prompt refused before the stream, an answer held until it is screened |
| 6 | [demo_06_a_failure_forced_on_a_candidate_the_ranker_silent_the_stream_still_served_the_li.py](demo_06_a_failure_forced_on_a_candidate_the_ranker_silent_the_stream_still_served_the_li.py) | A failure forced on a candidate: the ranker silent, the stream still served, the line in the log |
| 8 | [demo_08_what_a_stream_costs_what_its_row_says_and_who_reads_it.py](demo_08_what_a_stream_costs_what_its_row_says_and_who_reads_it.py) | What a stream costs, what its row says, and who reads it |

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The guard, the answer cache, the router and the ranker's deadline live in the API's environment, each with a default the page names; a name the service does not set is unset rather than exported empty. /version reports the cache and the model.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine. Temporarily disable an enabled answer cache for this retrieval/generation experiment and save its prior value. This changes the shared API; finish restores it. Cache lessons in Module 6 are unaffected.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The guard, the answer cache, the router and the ranker's deadline live in the API's environment, each with a default the page names; a name the service does not set is unset rather than exported empty. /version reports the cache and the model.

Operation: bash — run in the operator shell, in $DEMO_ROOT, once per shell.

IDE adaptation: Read literal environment values as JSON from the serving revision; absent keys are unset. Repeated text parsing is removed.

Expected shape, not a promised result:

```text
guard: off (default)  template: documind-guard (default)  cache: off (default)  routing: off (default)  rerank timeout: 5.0 (default)
version: gemini-3.6-flash | documind-rag@v3 | semantic_cache off
```

### demo_03_a_stream_in_curl_the_raw_events_their_order_and_a_clock_on_each.py

Do it: one stream, timed, then the query's citations beside it

**`step_01_one_stream_timed_then_the_query_s_citation(session)` — A stream in curl: the raw events, their order, and a clock on each / Do it: one stream, timed, then the query's citations beside it**

Do it: one stream, timed, then the query's citations beside it

Operation: bash — run in the operator shell (a Python cell; one stream and one query, two rupees).

Expected shape, not a promised result:

```text
first citation at 1xxx ms | first token at 2xxx ms | done at 4xxx ms | the API's own latency_ms 4xxx
5 citation events, then 3x token events, then done
   citation 1 #  1 hr_policy_2026.md      kind text effective_from None quote 'NP-03 — Notice period\nA confirmed em'
   citation 2 #  4 hr_policy_2026.md      kind text effective_from None quote '...'
   ...
the answer: A confirmed employee in grade E3 must serve a notice period of ... [1] ...
done: {'tokens_in': 1xxx, 'tokens_out': 4xx, 'cached_tokens': 0, 'model': 'gemini-3.6-flash', 'backend': 'vertex', 'cache_hit': 'none', 'prompt': 'documind-rag@v3'}
stages: {'policy_fallback': 0, 'retrieval_backend': 'vector', 'retrieve_ms': 6xx, 'pool': 20, 'graph_chunks': 0, 'managed_chunks': 0, 'vector_chunks': 20, 'rerank_ms': 3xx, 'generate_ms': 2xxx}
the query's answer to the same question: 3 citations, the ones the model used; the stream's 5 were the packed set
saved /tmp/stream63.txt: paste it into the reader in step 1
```

### demo_04_what_a_stream_s_citations_are_and_the_streams_of_one_token.py

Do it: the empty pool as one token, then the stream rows

**`step_01_the_empty_pool_as_one_token_then_the_strea(session)` — What a stream's citations are, and the streams of one token / Do it: the empty pool as one token, then the stream rows**

Do it: the empty pool as one token, then the stream rows

Operation: bash — run in the operator shell (one stream that costs nothing; one log read).

Expected shape, not a promised result:

```text
the one token: The corpus holds nothing near this question: no passage of this tenant's current documents was ...
done: backend none | tokens_in 0 | pool 0 | rerank_ms 0 | generate_ms 0
events: {'token': 1, 'done': 1}
False	none	0	0	0	off	ui
True	vertex	1xxx	4xx	20	off	ui
```

### demo_05_the_guard_a_prompt_refused_before_the_stream_an_answer_held_until_it_is_screened.py

Read the lane, Rs 0

**`step_01_read_the_lane_rs_0(session)` — The guard: a prompt refused before the stream, an answer held until it is screened / Read the lane, Rs 0**

Read the lane, Rs 0

Operation: bash — run in the operator shell (two log reads).

Expected shape, not a promised result:

```text
NN off
```

### demo_06_a_failure_forced_on_a_candidate_the_ranker_silent_the_stream_still_served_the_li.py

Do it: the ranker silent for one revision, the stream read, the line read, the undo

**`step_01_the_ranker_silent_for_one_revision_the_str(session)` — A failure forced on a candidate: the ranker silent, the stream still served, the line in the log / Do it: the ranker silent for one revision, the stream read, the line read, the undo**

Do it: the ranker silent for one revision, the stream read, the line read, the undo

Operation: bash — run in the operator shell (one new revision, no traffic; one stream to it; two log reads; the undo).

Expected shape, not a promised result:

```text
done.stages: rerank_fallback 1 | rerank_ms 1x | pool 20 | vector_chunks 20
events: {'citation': 3, 'token': 3x, 'done': 1} | the answer: A confirmed employee in grade E3 must serve a notice period of ...
2026-09-2xT1x:xx:xx.xxxxxxZ	acme	DeadlineExceeded
```

### demo_08_what_a_stream_costs_what_its_row_says_and_who_reads_it.py

Do it: the day by surface, Rs 0

**`step_01_the_day_by_surface_rs_0(session)` — What a stream costs, what its row says, and who reads it / Do it: the day by surface, Rs 0**

Do it: the day by surface, Rs 0

Operation: bash — run in the operator shell, in $DEMO_ROOT (one log read).

Expected shape, not a promised result:

```text
by surface
event                  answers    tok_in  tok_out       USD       INR  p95 ms  unans
------------------------------------------------------------------------------------
query                       NN     xxxxx     xxxx    0.0xxx      x.xx    4xxx   0.xx
stream                       4      xxxx      xxx    0.0xxx      x.xx    4xxx   0.25
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs. Restore the saved answer-cache value and tenant backend, including after a failed experiment.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_3.7_Streaming_WIX.html`. All 36 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `9ff597141a0ff947d0c0cf9acf42158424a2f234`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
