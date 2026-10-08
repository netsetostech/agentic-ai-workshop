# Lesson 7.6: Exercise implemented Studio and voice features

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_studio_s_and_the_voice_s_rules_run.py](demo_03_the_studio_s_and_the_voice_s_rules_run.py) | The Studio's and the voice's rules, run |
| 4 | [demo_04_a_generated_image_and_its_usage_row.py](demo_04_a_generated_image_and_its_usage_row.py) | A generated image, and its usage row |
| 5 | [demo_05_the_upload_door.py](demo_05_the_upload_door.py) | The upload door |
| 6 | [demo_06_an_answer_read_aloud_and_a_question_nobody_hears.py](demo_06_an_answer_read_aloud_and_a_question_nobody_hears.py) | An answer read aloud, and a question nobody hears |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The deployed Studio/voice capabilities described on the page; browser/microphone permissions remain user actions.

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

### demo_03_the_studio_s_and_the_voice_s_rules_run.py

Do it

**`step_01_the_studio_s_and_the_voice_s_rules_run(session)` — The Studio's and the voice's rules, run / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the rules, run; no network).

Expected shape, not a promised result:

```text
1. a generation: {'event': 'media', 'modality': 'image', 'model': 'gemini-3.1-flash-image', 'tokens_in': 0, 'cost_usd': 0.039, 'cached': False}
1. a DEMO_MODE hit: {'event': 'media', 'modality': 'image', 'model': 'gemini-3.1-flash-image', 'tokens_in': 0, 'cost_usd': 0.0, 'cached': True}
2. event=chat        copied       by the sink, never read by tenant_daily
2. event=desk        copied       by the sink, never read by tenant_daily
2. event=desk_gate   copied       by the sink, never read by tenant_daily
2. event=desk_shadow copied       by the sink, never read by tenant_daily
2. event=media       never copied by the sink, read by tenant_daily
2. event=passages    copied       by the sink, never read by tenant_daily
2. event=query       copied       by the sink, read by tenant_daily
2. event=stream      copied       by the sink, read by tenant_daily
3. read aloud 1, en-IN-Chirp3-HD-Kore: synthesised, then cached (1 object in the bucket)
3. read aloud 2, en-IN-Chirp3-HD-Kore: read back from the cache (1 object in the bucket)
3. read aloud 3, hi-IN-Chirp3-HD-Kore: synthesised, then cached (2 objects in the bucket)
   the first object: tts/171aae62fa1f4b3a....ogg, the SHA-256 of 'en-IN-Chirp3-HD-Kore|1.0|ogg|' and the text
```

### demo_04_a_generated_image_and_its_usage_row.py

Do it

**`step_01_a_generated_image_and_its_usage_row(session)` — A generated image, and its usage row / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (one image, then a DEMO_MODE hit).

Expected shape, not a promised result:

```text
generate 1: {'blob': 'acme/gen/9b79e5785c446f20e956772bbe9e2781.png', 'bucket': 'documind-ai-YOUR-ID-media', 'cached': False}
generate 2: {'blob': 'acme/gen/9b79e5785c446f20e956772bbe9e2781.png', 'bucket': 'documind-ai-YOUR-ID-media', 'cached': True}
the usage rows since 2026-09-24T08:10:00Z (Cloud Logging, oldest first):
  tenant acme, modality image, model gemini-3.1-flash-image, cost_usd 0.039, cached False, user documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
  tenant acme, modality image, model gemini-3.1-flash-image, cost_usd 0.0, cached True, user documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
the audit events since then, in documind-ai-YOUR-ID-audit (kept five years): 1
  media.generate by documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com: acme/gen/9b79e5785c446f20e956772bbe9e2781.png, meta {'model': 'gemini-3.1-flash-image', 'synthid': True, 'prompt_sha': '9b79e5785c446f20e956772bbe9e2781'}
the image, for 15 minutes, as documind-ui-sa (the Studio's own signer):
  https://storage.googleapis.com/documind-ai-YOUR-ID-media/acme/gen/9b79e5785c446f20e956772bbe9e2781.png?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=documind-ui-sa%40documind-ai-YOUR-ID.iam.gserviceaccount.com%2F20260924%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260924T083000Z&X-Goog-Expires=900&X-Goog-SignedHeaders=host&X-Goog-Signature=...
```

### demo_05_the_upload_door.py

Do it

**`step_01_the_upload_door(session)` — The upload door / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (two refusals, then lesson 7.5's video through the door).

Expected shape, not a promised result:

```text
upload-url townhall.zip as application/zip: (400, "content_type must be one of ['application/pdf', 'audio/mpeg', 'image/jpeg', 'image/png', 'text/markdown', 'text/plain', 'video/mp4']")
upload-url ../globex/townhall_2026_q1.mp4 as video/mp4: (400, 'filename must be a bare name')
upload-url townhall_2026_q1.mp4 as video/mp4: 200, a PUT into gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.mp4, signed for 15 minutes
PUT 1,474,032 bytes straight to the bucket: HTTP 200
the worker: {"event": "ingest_duplicate", "doc_key": "acme_2b7f0b3acad009d5e38d869a87861150807d598e862de6d72a5349bafaee97d8"}
```

### demo_06_an_answer_read_aloud_and_a_question_nobody_hears.py

The first cell asks the town hall question as documind-ui-sa. It reads the answer aloud with the UI's own cached_tts, twice, and saves the audio as ~/answer.ogg. The text is the answer's first 1,500 characters, as the chat's toggle reads it. Play it: in Cloud Shell, cloudshell download ~/answer.ogg hands the file to your browser. That is the second proof: an answer read aloud. The second cell gives that audio to the UI's own transcribe, first where the UI runs it, then in eu. eu is a location Google lists chirp_3 in, for Hindi and English (India). The audio leaves India for that one call: a synthetic voice reading an answer about acme, whose policy is any (lesson 7.3). This is the function:

**`step_01_definition(session)` — An answer read aloud, and a question nobody hears / Definition**

The first cell asks the town hall question as documind-ui-sa. It reads the answer aloud with the UI's own cached_tts, twice, and saves the audio as ~/answer.ogg. The text is the answer's first 1,500 characters, as the chat's toggle reads it.

Operation: bash — run in the operator shell, in the kit (one answer, read aloud twice).

Expected shape, not a promised result:

```text
the answer: The CFO said EMEA was the one region that shrank: revenue fell 5.2 per cent, from 96 crore to 91 crore, because two large renewals in Germany slipped into the first quarter of FY2027 [3].
read aloud 1: a miss, synthesised by Chirp 3 HD and written to gs://documind-ai-YOUR-ID-tts-cache/tts/d28fac84987c....ogg (36,799 bytes of Ogg Opus)
read aloud 2: a hit, read back from gs://documind-ai-YOUR-ID-tts-cache/tts/d28fac84987c....ogg (36,799 bytes of Ogg Opus)
saved ~/answer.ogg: in Cloud Shell, cloudshell download ~/answer.ogg hands it to your browser to play
```

**`step_02_definition(session)` — An answer read aloud, and a question nobody hears / Definition**

Play it: in Cloud Shell, cloudshell download ~/answer.ogg hands the file to your browser. That is the second proof: an answer read aloud. The second cell gives that audio to the UI's own transcribe, first where the UI runs it, then in eu. eu is a location Google lists chirp_3 in, for Hindi and English (India). The audio leaves India for that one call: a synthetic voice reading an answer about acme, whose policy is any (lesson 7.3). This is the function:

Operation: bash — run in the operator shell, in the kit (the answer's audio, transcribed twice).

Expected shape, not a promised result:

```text
transcribe() where the UI runs it, asia-south1: ''
transcribe() in eu: 'The CFO said EMEA was the one region that shrank: revenue fell 5.2 per cent, from 96 crore to 91 crore, because two large renewals in Germany slipped into the first quarter of FY2027.'
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_7.6_Studio_Voice_WIX.html`. All 22 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `fbbf9c146875e365f93128d312d1b7bed2f13340`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
