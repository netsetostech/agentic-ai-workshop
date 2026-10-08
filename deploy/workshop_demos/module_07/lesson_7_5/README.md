# Lesson 7.5: Query a video clip and validate media citations

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_from_a_segment_to_a_pill_run.py](demo_03_from_a_segment_to_a_pill_run.py) | From a segment to a pill, run |
| 4 | [demo_04_the_clip_built_the_transcript_withdrawn_the_video_heard.py](demo_04_the_clip_built_the_transcript_withdrawn_the_video_heard.py) | The clip built, the transcript withdrawn, the video heard |
| 5 | [demo_05_the_clip_at_its_second.py](demo_05_the_clip_at_its_second.py) | The clip at its second |
| 6 | [demo_06_make_smoke_media_green.py](demo_06_make_smoke_media_green.py) | make smoke-media, green |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Configured media ingestion services; this lesson builds its own synthetic video with make media before indexing it.

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

### demo_03_from_a_segment_to_a_pill_run.py

Do it

**`step_01_from_a_segment_to_a_pill_run(session)` — From a segment to a pill, run / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the contract and the UI's pill, run; no network).

Expected shape, not a promised result:

```text
1. resolve(): 2 draft citations in, 1 out ([Source 7] was not in the context):
   {'chunk_id': 'acme:77e0...#1', 'source_uri': 'gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.mp4', 'page': None, 'score': 0.88, 'kind': 'segment', 'media_url': 'gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.mp4', 'start': 200.7, 'end': 238.0}
2. the answer as the UI draws it: Revenue in EMEA fell 5.2 per cent, from 96 crore to 91 crore [Clip 3, 03:20].
   under Sources: the video from second 200, captioned 03:20 – 03:58 of townhall_2026_q1.mp4
3. the pills for the three sources: [1] [Fig 2] [Clip 3, 03:20] | a segment with no start: [Clip 3, ?]
4. the usage row's modality: video | the same answer from the table and the figure: image
5. mm-03, citing [Source 3]: kinds ['segment'] -> counts
5. mm-03, citing [Source 1]: kinds ['text'] -> cited no segment
```

### demo_04_the_clip_built_the_transcript_withdrawn_the_video_heard.py

make media MEDIA_ARGS=--video runs evals/build_media.py: Next, the transcript goes. upload.sh keeps a transcript home once its video exists, as it keeps a PDF's text mirror home, but it removes nothing already sent: make retire withdraws it as lesson 7.4 showed. The rows are retired, acme's two managed stores delete their copies, and the ledger row becomes a tombstone. The object stays in the bucket, and make restore would bring it back. make retire withdraws it as lesson 7.4 showed. The rows are retired, acme's two managed stores delete their copies, and the ledger row becomes a tombstone. The object stays in the bucket, and make restore would bring it back. Then the video goes up as a new document. make reindex copies it into acme's uploads and waits for the worker's line. The worker's media branch describes it in one Gemini call: Then the video goes up as a new document. make reindex copies it into acme's uploads and waits for the worker's line. The worker's media branch describes it in one Gemini call: Last, read the video's rows from acme's index, and hold them against the ground truth:

**`step_01_definition(session)` — The clip built, the transcript withdrawn, the video heard / Definition**

make media MEDIA_ARGS=--video runs evals/build_media.py:

Operation: bash — run in the operator shell, in the kit (the town hall synthesised: a minute or two).

Expected shape, not a promised result:

```text
python evals/build_media.py --video
  keep annual_report_2026_fig3.png (43 KB) - exists; --force re-renders
  keep inv_2026_0412.png (123 KB) - exists; --force re-renders
  keep payment_of_bonus_act_1965_p30.png (151 KB) - exists; --force re-renders
  voices: {'Meera': 'en-IN-Chirp3-HD-Aoede', 'Arjun': 'en-IN-Chirp3-HD-Charon'}
  Meera    0.0-  21.5s  Good morning, everyone, and welcome to the FY2026 town hall....
  Arjun   22.2-  57.7s  Thanks, Meera. Let me start with the table you all have on s...
  Meera   58.4-  69.6s  On people, headcount closed at 4,180, up from 3,742, and att...
  Arjun   70.3-  93.1s  On capital expenditure we invested 78 crore during the year....
  Meera   93.8- 104.8s  Thank you, Arjun. Questions are open on the portal until Fri...
  corpus/acme/townhall_2026_q1.mp4: 1.5 MB, 106 s, 5 utterances; ground truth beside it in townhall_2026_q1.segments.json
```

**`step_02_definition(session)` — The clip built, the transcript withdrawn, the video heard / Definition**

Next, the transcript goes. upload.sh keeps a transcript home once its video exists, as it keeps a PDF's text mirror home, but it removes nothing already sent: make retire withdraws it as lesson 7.4 showed. The rows are retired, acme's two managed stores delete their copies, and the ledger row becomes a tombstone. The object stays in the bucket, and make restore would bring it back.

Operation: bash — run in the operator shell, in the kit (the transcript withdrawn from acme).

Expected shape, not a promised result:

```text
{"event": "reconcile_withdrawn", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.md", "fingerprint": "1a19e8a7d490616d", "retired_doc_keys": ["acme_b0d7702de2bf5a7d0770de433916af821b4a83f13ca321e074293ef99f4d75c1"], "retired_ids": ["acme:b0d7702de2bf5a7d0770de433916af821b4a83f13ca321e074293ef99f4d75c1#0"], "retired_chunks": 1, "note": "a tombstone: the object is kept and nothing automatic re-ingests it; make restore SOURCE= does"}
```

**`step_03_definition(session)` — The clip built, the transcript withdrawn, the video heard / Definition**

make retire withdraws it as lesson 7.4 showed. The rows are retired, acme's two managed stores delete their copies, and the ledger row becomes a tombstone. The object stays in the bucket, and make restore would bring it back. Then the video goes up as a new document. make reindex copies it into acme's uploads and waits for the worker's line. The worker's media branch describes it in one Gemini call:

Operation: bash — run in the operator shell, in the kit (the video uploaded; waits for the worker).

Expected shape, not a promised result:

```text
...
>> gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.mp4 - waiting for the worker (up to 5 min)
>> event doc_key chunks reused embedded retired effective_from
>> ingest_ok	acme_a85a89590f9a2b8b7ffc8588e11578297c5bc1fe5181482b0ef75d22d00881d3	5	0	5	0	
>> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=townhall_2026_q1.mp4 API=<candidate url>
```

**`step_04_definition(session)` — The clip built, the transcript withdrawn, the video heard / Definition**

Then the video goes up as a new document. make reindex copies it into acme's uploads and waits for the worker's line. The worker's media branch describes it in one Gemini call: Last, read the video's rows from acme's index, and hold them against the ground truth:

Operation: bash — run in the operator shell, in the kit (reads only).

Expected shape, not a promised result:

```text
5 segments of townhall_2026_q1.mp4 in acme's index, against the ground truth's 5 turns:
  segment t0-22     00:00-00:22   22 s  over Meera 00:00
      Meera, the CEO, opens the FY2026 town hall over a first slide saying the video is synthetic, welcoming s...
  segment t22-58    00:22-00:58   36 s  over Arjun 00:22
      Arjun, the CFO, walks through the revenue table on slide two: India grew from 412 to 508 crore, up 23.3 ...
  segment t58-70    00:58-01:10   12 s  over Meera 00:58
      Meera says headcount closed at 4,180, up from 3,742, and attrition came down to 11.4 per cent from 14.9 ...
  segment t70-93    01:10-01:33   23 s  over Arjun 01:10
      Arjun says capital expenditure was 78 crore for the year: 31 crore went into the Hyderabad plant expansi...
  segment t93-105   01:33-01:45   12 s  over Meera 01:33
      Meera thanks Arjun and says questions are open on the portal until Friday, over a closing slide. The rec...
checks: longest 36 s (the prompt asks for at most 60) -> PASS; start before end in every row -> PASS; last end 01:45 against the speech's end 01:44
the EMEA line: Arjun says '5.2 per cent' in the turn at 00:22-00:57; the segment that quotes it: t22-58
```

### demo_05_the_clip_at_its_second.py

Do it

**`step_01_the_clip_at_its_second(session)` — The clip at its second / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (golden row mm-03's question, as the UI asks it).

Expected shape, not a promised result:

```text
5 sources packed: [1] segment [2] figure [3] text [4] segment [5] text
the UI shows: The CFO said EMEA was the one region that shrank: revenue fell 5.2 per cent, from 96 crore to 91 crore, because two large renewals in Germany slipped into the first quarter of FY2027 [Clip 4, 00:22].
run_eval's rule for mm-03: cited kinds ['segment'], a segment asked for -> PASS
the ground truth: Arjun says '5.2 per cent' in the turn 00:22-00:57
[Clip 4]: the player opens townhall_2026_q1.mp4 at 00:22, the clip runs to 00:58; it holds the turn -> PASS
  open it at that second, for 15 minutes, as documind-ui-sa:
  https://storage.googleapis.com/documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.mp4?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=documind-ui-sa%40documind-ai-YOUR-ID.iam.gserviceaccount.com%2F20260924%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260924T083000Z&X-Goog-Expires=900&X-Goog-SignedHeaders=host&X-Goog-Signature=...#t=22
```

### demo_06_make_smoke_media_green.py

Do it

**`step_01_make_smoke_media_green(session)` — make smoke-media, green / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the gate: a minute or two).

Expected shape, not a promised result:

```text
DocuMind Module 9 - live smoke test
  api: https://documind-api-NUMBER.asia-south1.run.app
  mcp: https://documind-mcp-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] generate  blob=acme/gen/cd18d3eb6f6dd202ce999de17eb66160.png cached=False
  [PASS] outsider refused  status=403
  [PASS] figure citation  kinds=['figure'] media_url=gs://documind-ai-YOUR-ID-uploads/acme/annual_report_2026_fig  "EMEA's revenue declined, from Rs 96 crore in FY2025 to Rs 91"
  [PASS] media documents  4 of 21 indexed documents are media: ['annual_report_2026_fig3.png', 'inv_2026_0412.png', 'payment_of_bonus_act_1965_p30.png', 'townhall_2026_q1.mp4']
  [PASS] signed PUT  gs://documind-ai-YOUR-ID-uploads/acme/smoke_media_probe.png
  [PASS] worker indexed the PUT  chunks=1 at 2026-09-24T08:14:00.300000+00:00
  --------------------------------------------------------
  6 passed, 0 failed
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_7.5_Video_Clip_WIX.html`. All 26 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `139fc0392978c735a000f0aed33bb4a541f5ad5a`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
