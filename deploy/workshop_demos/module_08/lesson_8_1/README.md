# Lesson 8.1: Run the ingest events through Pub/Sub, mapped to Kafka

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_ui_one_note_in_its_row_and_an_answer_that_cites_it.py](demo_03_the_ui_one_note_in_its_row_and_an_answer_that_cites_it.py) | The UI: one note in, its row, and an answer that cites it |
| 5 | [demo_05_rest_the_trace_hop_by_hop_and_the_subscription_as_pub_sub_holds_it.py](demo_05_rest_the_trace_hop_by_hop_and_the_subscription_as_pub_sub_holds_it.py) | REST: the trace hop by hop, and the subscription as Pub/Sub holds it |
| 6 | [demo_06_direct_reads_the_records_the_push_left_and_the_answer_through_the_api.py](demo_06_direct_reads_the_records_the_push_left_and_the_answer_through_the_api.py) | Direct reads: the records the push left, and the answer through the API |
| 7 | [demo_07_the_burst_thirty_one_objects_against_five_instances.py](demo_07_the_burst_thirty_one_objects_against_five_instances.py) | The burst: thirty-one objects against five instances |
| 9 | [demo_09_verify_it_yourself_the_checklist.py](demo_09_verify_it_yourself_the_checklist.py) | Verify it yourself: the checklist |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's answers, in steps 3 and 6, must come from the kit's own rows, where the worker writes the note it traces, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's answers, in steps 3 and 6, must come from the kit's own rows, where the worker writes the note it traces, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's answers, in steps 3 and 6, must come from the kit's own rows, where the worker writes the note it traces, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_ui_one_note_in_its_row_and_an_answer_that_cites_it.py

The upload this page traces, made once, then seen the way a user sees it: a row under Versions, and an answer with a citation. The trace needs an upload nobody else could have made, so the cell below writes a short note of your own: a title line, the time you made it, and two invented sections. The time makes its bytes, and so its content hash, new to your lane. Then make ingest-one copies it under acme's prefix and waits for the worker's ingest_ok line. That is the kit's own drill:

**`step_01_the_ui_one_note_in_its_row_and_an_answer_t(session)` — The UI: one note in, its row, and an answer that cites it / The UI: one note in, its row, and an answer that cites it**

The upload this page traces, made once, then seen the way a user sees it: a row under Versions, and an answer with a citation. The trace needs an upload nobody else could have made, so the cell below writes a short note of your own: a title line, the time you made it, and two invented sections. The time makes its bytes, and so its content hash, new to your lane. Then make ingest-one copies it under acme's prefix and waits for the worker's ingest_ok line. That is the kit's own drill:

Operation: bash — run in the operator shell, in the kit (one small upload; paise of embedding).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/trace_upload.txt]
```

### demo_05_rest_the_trace_hop_by_hop_and_the_subscription_as_pub_sub_holds_it.py

Three Google APIs, read with your operator token: Cloud Storage for the object, Cloud Logging for the push and the worker's lines, Pub/Sub for the subscription and its topic. The first cell asks Cloud Storage's JSON API for the note's metadata, which is the record the notice carried. Then it asks Cloud Logging for everything documind-ingest logged in the ten minutes after the object was created: the request log entry Cloud Run writes for each POST it receives, and the worker's own JSON lines for this version. It prints them as one timeline, in seconds from the object's creation: Step 4 read what Terraform declared. The platform holds more: every field Google filled in with a default. The cell reads the subscription and its topic from the Pub/Sub API, then reads terraform/eventarc.tf in your clone of the kit and marks each field with who set it:

**`step_01_rest_the_trace_hop_by_hop_and_the_subscrip(session)` — REST: the trace hop by hop, and the subscription as Pub/Sub holds it / REST: the trace hop by hop, and the subscription as Pub/Sub holds it**

Three Google APIs, read with your operator token: Cloud Storage for the object, Cloud Logging for the push and the worker's lines, Pub/Sub for the subscription and its topic. The first cell asks Cloud Storage's JSON API for the note's metadata, which is the record the notice carried. Then it asks Cloud Logging for everything documind-ingest logged in the ten minutes after the object was created: the request log entry Cloud Run writes for each POST it receives, and the worker's own JSON lines for this version. It prints them as one timeline, in seconds from the object's creation:

Operation: bash — run in the operator shell, a minute after the upload (one Cloud Storage read, one Cloud Logging read).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/trace_timeline.txt]
```

**`step_02_the_subscription_as_pub_sub_holds_it(session)` — REST: the trace hop by hop, and the subscription as Pub/Sub holds it / The subscription, as Pub/Sub holds it**

Step 4 read what Terraform declared. The platform holds more: every field Google filled in with a default. The cell reads the subscription and its topic from the Pub/Sub API, then reads terraform/eventarc.tf in your clone of the kit and marks each field with who set it:

Operation: bash — run in the operator shell, in the kit (two Pub/Sub reads and your clone's eventarc.tf; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/subscription_rest.txt]
```

### demo_06_direct_reads_the_records_the_push_left_and_the_answer_through_the_api.py

Firestore read directly with your own credentials, then the API's two doors onto the same records: the ledger it serves and the question it answers. The push ended in writes, and two keys find them all without a search, as lesson 1.4 showed. The ledger row is named after the object, sources/acme~pubsub_trace_note.md, and it names the version's key, doc_key. The cell reads the ledger row, the claim, the version's chunk rows and acme's ledger summary, and holds each generation against the object's: Three generations, one number: the object's, the ledger's and the claim's. That equality is the trace's proof that one notice, delivered and acknowledged, produced every record. The chunk rows are the three the worker's chunker cuts from the note by its two rules, a chunk for each ## section and a preamble for the text above the first heading: preamble, NG-01, NG-02. This page ran the worker's own _chunk() on the note when it was built, and it cut the same three. Last, the API's two doors onto the same records. GET /v1/sources is the ledger as the UI's Versions table draws it, asked here as the UI's service account; POST /v1/query asks step 3's question again:

**`step_01_direct_reads_the_records_the_push_left_and(session)` — Direct reads: the records the push left, and the answer through the API / Direct reads: the records the push left, and the answer through the API**

Firestore read directly with your own credentials, then the API's two doors onto the same records: the ledger it serves and the question it answers. The push ended in writes, and two keys find them all without a search, as lesson 1.4 showed. The ledger row is named after the object, sources/acme~pubsub_trace_note.md, and it names the version's key, doc_key. The cell reads the ledger row, the claim, the version's chunk rows and acme's ledger summary, and holds each generation against the object's:

Operation: bash — run in the operator shell (Firestore reads and one Cloud Storage read; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/trace_records.txt]
```

**`step_02_direct_reads_the_records_the_push_left_and(session)` — Direct reads: the records the push left, and the answer through the API / Direct reads: the records the push left, and the answer through the API**

Three generations, one number: the object's, the ledger's and the claim's. That equality is the trace's proof that one notice, delivered and acknowledged, produced every record. The chunk rows are the three the worker's chunker cuts from the note by its two rules, a chunk for each ## section and a preamble for the text above the first heading: preamble, NG-01, NG-02. This page ran the worker's own _chunk() on the note when it was built, and it cut the same three. Last, the API's two doors onto the same records. GET /v1/sources is the ledger as the UI's Versions table draws it, asked here as the UI's service account; POST /v1/query asks step 3's question again:

Operation: bash — run in the operator shell (the ledger, then one answer: paise).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/trace_api.txt]
```

### demo_07_the_burst_thirty_one_objects_against_five_instances.py

Why squeeze. A bus that pushes has to learn how fast its reader can go, and it learns only from the answers. Pub/Sub starts a subscription's push window small, widens it with each success and narrows it with each failure (Google's push page). Cloud Run holds a request that finds no free instance in its pending queue and then refuses it with a 429. The subscription counts each refusal as a failed delivery, retries it after the backoff, and charges it against the 12 attempts; the comment in step 4's subscription is the kit's record of a first live load that learned this the hard way. At 30 in flight, 31 messages are 2 rounds of work; at 5 they are at least 7, and they have to queue. Squeezing the ceiling makes the reader the bottleneck, so you can watch the bus adapt to it. Why the corpus. make ingest-corpus uploads the kit's corpus again: by upload.sh's rule, 21 objects for acme, 3 for globex and 7 for zeta, 31 in all. Each upload is a new generation, so each fires a notice, and each notice is pushed until the worker takes it. But the bytes are the ones your lane indexed when it was built, so every claim is already taken: the worker downloads the generation, hashes it, finds the claim and answers 200 duplicate. Nothing is parsed, nothing is embedded and no model is called. The burst costs deliveries and nothing else, as long as that "every" holds, and the first cell checks it before anything moves: The ceiling is a setting of the worker's revision: the same --max-instances flag lesson-12.5.sh deploys with. Changing it deploys a new revision with the same image and the same environment. Google recommends a service-level maximum for most uses, which needs no new revision (its maximum-instances page); the revision's flag is used here so that the restore at the end puts back exactly what the kit deployed. The ceiling is a setting of the worker's revision: the same --max-instances flag lesson-12.5.sh deploys with. Changing it deploys a new revision with the same image and the same environment. Google recommends a service-level maximum for most uses, which needs no new revision (its maximum-instances page); the revision's flag is used here so that the restore at the end puts back exactly what the kit deployed. Now note the time and upload the corpus. Keep this shell open: the next three cells read BURST_SINCE. If the shell does close, export it again with the time this cell printed. Give it two minutes, then read every request Cloud Run received for the worker since BURST_SINCE, by status and by ten-second slice, with the worker's verdicts for the same window: Pub/Sub keeps its own counts for each subscription: the backlog (messages not yet acknowledged), the age of the oldest of them, and every push it made, by how the push ended. Cloud Run counts its instances the same way. These metrics are sampled every 60 seconds and can take up to 120 seconds to appear (Google's list of metrics), so run this cell at least three minutes after the upload: Put the ceiling back

**`step_01_the_burst_thirty_one_objects_against_five(session)` — The burst: thirty-one objects against five instances / The burst: thirty-one objects against five instances**

Why squeeze. A bus that pushes has to learn how fast its reader can go, and it learns only from the answers. Pub/Sub starts a subscription's push window small, widens it with each success and narrows it with each failure (Google's push page). Cloud Run holds a request that finds no free instance in its pending queue and then refuses it with a 429. The subscription counts each refusal as a failed delivery, retries it after the backoff, and charges it against the 12 attempts; the comment in step 4's subscription is the kit's record of a first live load that learned this the hard way. At 30 in flight, 31 messages are 2 rounds of work; at 5 they are at least 7, and they have to queue. Squeezing the ceiling makes the reader the bottleneck, so you can watch the bus adapt to it. Why the corpus. make ingest-corpus uploads the kit's corpus again: by upload.sh's rule, 21 objects for acme, 3 for globex and 7 for zeta, 31 in all. Each upload is a new generation, so each fires a notice, and each notice is pushed until the worker takes it. But the bytes are the ones your lane indexed when it was built, so every claim is already taken: the worker downloads the generation, hashes it, finds the claim and answers 200 duplicate. Nothing is parsed, nothing is embedded and no model is called. The burst costs deliveries and nothing else, as long as that "every" holds, and the first cell checks it before anything moves:

Operation: bash — run in the operator shell, in the kit (hashes your clone's corpus against the ledger; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/burst_precheck.txt]
```

**`step_02_squeeze_then_upload(session)` — The burst: thirty-one objects against five instances / Squeeze, then upload**

The ceiling is a setting of the worker's revision: the same --max-instances flag lesson-12.5.sh deploys with. Changing it deploys a new revision with the same image and the same environment. Google recommends a service-level maximum for most uses, which needs no new revision (its maximum-instances page); the revision's flag is used here so that the restore at the end puts back exactly what the kit deployed.

Operation: bash — run in the operator shell (a new revision of the worker, the same image; a minute).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/burst_squeeze.txt]
```

**`step_03_squeeze_then_upload(session)` — The burst: thirty-one objects against five instances / Squeeze, then upload**

The ceiling is a setting of the worker's revision: the same --max-instances flag lesson-12.5.sh deploys with. Changing it deploys a new revision with the same image and the same environment. Google recommends a service-level maximum for most uses, which needs no new revision (its maximum-instances page); the revision's flag is used here so that the restore at the end puts back exactly what the kit deployed. Now note the time and upload the corpus. Keep this shell open: the next three cells read BURST_SINCE. If the shell does close, export it again with the time this cell printed.

Operation: bash — run in the operator shell, in the kit (31 uploads, every one already indexed).

Expected shape, not a promised result:

```text
BURST_SINCE=YYYY-MM-DDTHH:MM:SSZ
PROJECT_ID=documind-ai-YOUR-ID bash evals/upload.sh
project : documind-ai-YOUR-ID
bucket  : gs://documind-ai-YOUR-ID-uploads

==> acme (21 files) -> gs://documind-ai-YOUR-ID-uploads/acme/
    annual_report_2026.md
    annual_report_2026_fig3.png
    cgst_act_2017.pdf
    code_on_social_security_2020.pdf
    code_on_wages_2019.pdf
    dpdp_act_2023.pdf
    hr_policy_2026.md
    industrial_relations_code_2020.pdf
    inv_2026_0412.md
    inv_2026_0412.png
    it_act_2000.pdf
    labour_codes_compliance_handbook.pdf
    maternity_benefit_act_1961.pdf
    maternity_benefit_amendment_act_2017.pdf
    msa_acme_2026.md
    osh_code_2020.pdf
    payment_of_bonus_act_1965.pdf
    payment_of_bonus_act_1965_p30.png
    payment_of_gratuity_act_1972.pdf
    posh_act_2013.pdf
    townhall_2026_q1.md
...
==> globex (3 files) -> gs://documind-ai-YOUR-ID-uploads/globex/
    dpdp_act_2023.pdf
    it_act_2000.pdf
    msa_globex_2026.md
...
==> zeta (7 files) -> gs://documind-ai-YOUR-ID-uploads/zeta/
    code_on_social_security_2020.pdf
    code_on_wages_2019.pdf
    hr_policy_zeta_2026.md
    industrial_relations_code_2020.pdf
    labour_codes_compliance_handbook.pdf
    msa_zeta_2026.md
    osh_code_2020.pdf
...

Uploaded. Eventarc should now be enqueuing one ingest job per object;
watch the DLQ if nothing lands:
  gcloud pubsub subscriptions pull ingest-dlq-sub --auto-ack --limit=10

The two binary assets are NOT here - manifest.json lists what to supply:
  - About three minutes: two synthetic voices reading townhall_2026_q1.md over four slides. `make media --video` builds it (the Text-to-Speech API and ffmpeg: apt-get it in Cloud Shell, or pip install imageio-ffmpeg). Or record a real product walkthrough of the same length - no real faces or voices.
  - Photograph of a hand-drawn architecture sketch, for the 9.x image-caption path. Draw it, photograph it, check no colleague is in frame.
```

**`step_04_what_the_worker_saw(session)` — The burst: thirty-one objects against five instances / What the worker saw**

Give it two minutes, then read every request Cloud Run received for the worker since BURST_SINCE, by status and by ten-second slice, with the worker's verdicts for the same window:

Operation: bash — run in the operator shell, two minutes after the upload (Cloud Logging reads; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/burst_requests.txt]
```

**`step_05_what_pub_sub_saw(session)` — The burst: thirty-one objects against five instances / What Pub/Sub saw**

Pub/Sub keeps its own counts for each subscription: the backlog (messages not yet acknowledged), the age of the oldest of them, and every push it made, by how the push ended. Cloud Run counts its instances the same way. These metrics are sampled every 60 seconds and can take up to 120 seconds to appear (Google's list of metrics), so run this cell at least three minutes after the upload:

Operation: bash — run in the operator shell, at least three minutes after the upload (Cloud Monitoring reads; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/burst_metrics.txt]
```

**`step_06_put_the_ceiling_back(session)` — The burst: thirty-one objects against five instances / Put the ceiling back**

Put the ceiling back

Operation: bash — run in the operator shell, before you leave this step (the ceiling back to the kit's; a minute).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/burst_restore.txt]
```

### demo_09_verify_it_yourself_the_checklist.py

Eight checks, each one step above, each with what a pass looks like on your lane; then the one command that puts the note away. When the checks are done, withdraw the note. make retire flags its rows as retired, with an expire_at 30 days out, marks its ledger row withdrawn, removes it from the managed stores, takes its ids out of the Vector Search index (since 13 October 2026) and moves acme's fingerprint. The object stays in the bucket, and make restore would bring it back (lesson 1.7):

**`step_01_verify_it_yourself_the_checklist(session)` — Verify it yourself: the checklist / Verify it yourself: the checklist**

Eight checks, each one step above, each with what a pass looks like on your lane; then the one command that puts the note away. When the checks are done, withdraw the note. make retire flags its rows as retired, with an expire_at 30 days out, marks its ledger row withdrawn, removes it from the managed stores, takes its ids out of the Vector Search index (since 13 October 2026) and moves acme's fingerprint. The object stays in the bucket, and make restore would bring it back (lesson 1.7):

Operation: bash — run in the operator shell, in the kit, when the lesson is done (withdraws the note; reversible with make restore).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/trace_retire.txt]
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's answers, in steps 3 and 6, must come from the kit's own rows, where the worker writes the note it traces, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's answers, in steps 3 and 6, must come from the kit's own rows, where the worker writes the note it traces, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_8.1_PubSub_Kafka_WIX.html`. All 42 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `1e9a96b64334dbc3d0d7d57f73ef634d3ecaaa83`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
