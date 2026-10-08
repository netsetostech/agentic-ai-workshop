# Lesson 6.4: Measure latency, avoided calls and false cache hits

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_curve_every_candidate_threshold_on_the_labelled_pairs.py](demo_03_the_curve_every_candidate_threshold_on_the_labelled_pairs.py) | The curve: every candidate threshold on the labelled pairs |
| 4 | [demo_04_the_replay_the_same_pairs_asked_live_at_0_95.py](demo_04_the_replay_the_same_pairs_asked_live_at_0_95.py) | The replay: the same pairs, asked live at 0.95 |
| 5 | [demo_05_avoided_calls_in_rupees_and_the_latency_of_a_hit.py](demo_05_avoided_calls_in_rupees_and_the_latency_of_a_hit.py) | Avoided calls in rupees, and the latency of a hit |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Conditional recovery

- [recovery/demo_04_the_replay_the_same_pairs_asked_live_at_0_95.py](recovery/demo_04_the_replay_the_same_pairs_asked_live_at_0_95.py) — Each question gets a second try, two seconds after a 5xx or a timeout, as the kit's own run_eval.py gives it: one retry separates a blip from an outage. A blip, such as the first request to a fresh revision failing once, shows as a line saying how many questions were answered on a second try. A question that fails twice is listed with its HTTP status, and the replay carries on without it. The status is all the client sees. The reason is in the API's own log, and this reads the last three tracebacks, with the revision that threw each one:

## Finish and restore

- [cleanup/demo_06_choosing_the_threshold_and_the_clean_up.py](cleanup/demo_06_choosing_the_threshold_and_the_clean_up.py) — At lesson end: What the numbers allow, where the threshold lives, and the candidate put away. The kit's rule is the lowest candidate with no false hit on the set, and your curve names it. Before moving the switch, weigh three things. First, the rule of three: 18 different pairs with no false hit still allow a true rate of about 17%. The honest next step is more different pairs, written from real questions one word away, not a lower threshold. Second, the saving at that threshold: if it hits only a few same-fact pairs, the exact rung (the same words, no threshold at all) may be most of what the cache is worth. Third, the replay's hit from lines, which the curve cannot see. The threshold is an environment variable, SEMANTIC_CACHE_THRESHOLD, read once when a revision starts. No make target passes it, so trying 0.97 on a candidate takes gcloud run services update documind-api --no-traffic --tag candidate --update-env-vars SEMANTIC_CACHE_THRESHOLD=0.97, with your region and project, and then the replay again.
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

### demo_03_the_curve_every_candidate_threshold_on_the_labelled_pairs.py

Do it

**`step_01_the_curve_every_candidate_threshold_on_the(session)` — The curve: every candidate threshold on the labelled pairs / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (65 embeddings, about a minute; the report goes to your home folder).

Expected shape, not a promised result:

```text
42 pairs against 23 golden questions, text-embedding-005 @ us-central1

  threshold   hit rate (same)   false-hit rate (different)
       0.85      100% (24)          83% (15)
       0.88      100% (24)          67% (12)
       0.90       96% (23)          61% (11)
       0.92       62% (15)          50% ( 9)
       0.94       46% (11)          22% ( 4)
       0.95       33% ( 8)          11% ( 2)
       0.96       25% ( 6)           6% ( 1)
       0.97       17% ( 4)           0% ( 0)
       0.98        4% ( 1)           0% ( 0)

  lowest threshold with no false hit: 0.97
  nearest false pairs: pp-25 0.962, pp-31 0.955, pp-37 0.947, pp-35 0.941, pp-42 0.931, pp-41 0.929, pp-27 0.926, pp-30 0.926, pp-33 0.923, pp-40 0.914, pp-26 0.908, pp-36 0.885, pp-38 0.864, pp-39 0.858, pp-34 0.852, pp-29
  report: /home/you/cache93_curve.json
```

### demo_04_the_replay_the_same_pairs_asked_live_at_0_95.py

Do it: the candidate Do it: the replay

**`step_01_the_candidate(session)` — The replay: the same pairs, asked live at 0.95 / Do it: the candidate**

Do it: the candidate

Operation: bash — run in the operator shell, in the kit (a revision with SEMANTIC_CACHE=on at the kit's 0.95, and a start time).

Expected shape, not a promised result:

```text
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \
  --update-env-vars "^|^GENERATOR_MODEL=gemini-3.6-flash|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=off|SEMANTIC_CACHE=on|..."
...
>> candidate revision: documind-api-00046-wpk (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app
```

**`step_02_the_replay(session)` — The replay: the same pairs, asked live at 0.95 / Do it: the replay**

Do it: the replay

Operation: bash — run in the operator shell, in the kit (the 23 golden questions, then the 42 pairs, to the candidate; a few minutes).

Expected shape, not a promised result:

```text
pp-01 same right hit      211 ms  How much can I claim per trip for domestic travel?
  pp-15 same right hit      188 ms  Gratuity is paid at what rate per completed year?
  pp-16 same right hit      221 ms  What is the minimum bonus payable under the Bonus Ac
  pp-17 same right hit      209 ms  Under the Code on Wages, what is the rate for overti
  pp-18 same right hit      208 ms  Under the Code on Wages, what is the deadline for pa
  pp-19 same right hit      217 ms  The standing orders chapter of the IR Code applies f
  pp-20 same right hit      194 ms  Under the OSH Code, how many days of work earn a day
  pp-21 same right hit      153 ms  Under the DPDP Act, what is a Consent Manager?
  pp-25 diff FALSE HIT      230 ms  What is the notice period for a confirmed E2?
  pp-31 diff FALSE HIT      236 ms  Who approves a purchase of Rs 30,000?
  same-fact pairs served from the cache: 8 of 24
  different pairs served from the cache: 2 of 18
```

### recovery/demo_04_the_replay_the_same_pairs_asked_live_at_0_95.py

Each question gets a second try, two seconds after a 5xx or a timeout, as the kit's own run_eval.py gives it: one retry separates a blip from an outage. A blip, such as the first request to a fresh revision failing once, shows as a line saying how many questions were answered on a second try. A question that fails twice is listed with its HTTP status, and the replay carries on without it. The status is all the client sees. The reason is in the API's own log, and this reads the last three tracebacks, with the revision that threw each one:

**`step_01_the_replay(session)` — The replay: the same pairs, asked live at 0.95 / Do it: the replay**

Each question gets a second try, two seconds after a 5xx or a timeout, as the kit's own run_eval.py gives it: one retry separates a blip from an outage. A blip, such as the first request to a fresh revision failing once, shows as a line saying how many questions were answered on a second try. A question that fails twice is listed with its HTTP status, and the replay carries on without it. The status is all the client sees. The reason is in the API's own log, and this reads the last three tracebacks, with the revision that threw each one:

Operation: bash — run in the operator shell, only if the replay listed questions with no answer (the API's last three tracebacks).

### demo_05_avoided_calls_in_rupees_and_the_latency_of_a_hit.py

Do it: the candidate's rows Do it: the kit's table

**`step_01_the_candidate_s_rows(session)` — Avoided calls in rupees, and the latency of a hit / Do it: the candidate's rows**

Do it: the candidate's rows

Operation: bash — run in the operator shell, in the kit (the candidate's rows since the start: hits, p95, rupees; reads only).

Expected shape, not a promised result:

```text
65 answers on the candidate: 10 from the answer cache, 55 from the model
  p95 latency: 236 ms for a hit, 3187 ms for a model answer
  a model answer cost Rs 0.4673 on average: the hits avoided 10 calls, about Rs 4.67
  of those hits, 2 served a wrong answer: pp-25, pp-31
```

**`step_02_the_kit_s_table(session)` — Avoided calls in rupees, and the latency of a hit / Do it: the kit's table**

Do it: the kit's table

Operation: bash — run in the operator shell, in the kit (the kit's own table of the last hour, by model and backend).

Expected shape, not a promised result:

```text
by model and backend (what answered, through which door)
model                 model_backend          answers    tok_in  tok_out       USD       INR  p95 ms  unans
----------------------------------------------------------------------------------------------------------
gemini-3.6-flash      vertex                      55     97661    20783    0.3024     25.70    3187   0.00
gemini-3.6-flash      cache                       10         0        0    0.0000      0.00     236   0.00
```

### cleanup/demo_06_choosing_the_threshold_and_the_clean_up.py

At lesson end: What the numbers allow, where the threshold lives, and the candidate put away. The kit's rule is the lowest candidate with no false hit on the set, and your curve names it. Before moving the switch, weigh three things. First, the rule of three: 18 different pairs with no false hit still allow a true rate of about 17%. The honest next step is more different pairs, written from real questions one word away, not a lower threshold. Second, the saving at that threshold: if it hits only a few same-fact pairs, the exact rung (the same words, no threshold at all) may be most of what the cache is worth. Third, the replay's hit from lines, which the curve cannot see. The threshold is an environment variable, SEMANTIC_CACHE_THRESHOLD, read once when a revision starts. No make target passes it, so trying 0.97 on a candidate takes gcloud run services update documind-api --no-traffic --tag candidate --update-env-vars SEMANTIC_CACHE_THRESHOLD=0.97, with your region and project, and then the replay again.

**`step_01_choosing_the_threshold_and_the_clean_up(session)` — Choosing the threshold, and the clean-up / Choosing the threshold, and the clean-up**

What the numbers allow, where the threshold lives, and the candidate put away. The kit's rule is the lowest candidate with no false hit on the set, and your curve names it. Before moving the switch, weigh three things. First, the rule of three: 18 different pairs with no false hit still allow a true rate of about 17%. The honest next step is more different pairs, written from real questions one word away, not a lower threshold. Second, the saving at that threshold: if it hits only a few same-fact pairs, the exact rung (the same words, no threshold at all) may be most of what the cache is worth. Third, the replay's hit from lines, which the curve cannot see. The threshold is an environment variable, SEMANTIC_CACHE_THRESHOLD, read once when a revision starts. No make target passes it, so trying 0.97 on a candidate takes gcloud run services update documind-api --no-traffic --tag candidate --update-env-vars SEMANTIC_CACHE_THRESHOLD=0.97, with your region and project, and then the replay again.

Operation: bash — run in the operator shell, in the kit (the candidate's tag and recorded name removed).

Expected shape, not a promised result:

```text
Updating traffic...done.
Done.
URL: https://documind-api-...run.app
Traffic:
  100% documind-api-000MM-xxx      (the live revision, as before; no candidate tag)
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_6.4_Cache_Measure_WIX.html`. All 23 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `afcbff09c9738c4e6b84e3080c2c49c6941152f9`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
