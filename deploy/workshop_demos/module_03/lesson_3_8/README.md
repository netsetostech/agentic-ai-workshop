# Lesson 3.8: Complete the Streamlit upload-to-answer journey

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_front_door_iap_the_ui_s_settings_and_who_may_sign_in.py](demo_03_the_front_door_iap_the_ui_s_settings_and_who_may_sign_in.py) | The front door: IAP, the UI's settings, and who may sign in |
| 4 | [demo_04_the_upload_a_note_you_write_uploaded_in_the_browser_followed_to_the_ledger.py](demo_04_the_upload_a_note_you_write_uploaded_in_the_browser_followed_to_the_ledger.py) | The upload: a note you write, uploaded in the browser, followed to the ledger |
| 5 | [demo_05_the_answer_asked_in_chat_streamed_and_the_row_that_names_you.py](demo_05_the_answer_asked_in_chat_streamed_and_the_row_that_names_you.py) | The answer: asked in Chat, streamed, and the row that names you |
| 6 | [demo_06_citations_the_pills_the_sources_and_the_link_signed_through_iam.py](demo_06_citations_the_pills_the_sources_and_the_link_signed_through_iam.py) | Citations: the pills, the sources, and the link signed through IAM |
| 7 | [demo_07_the_ui_s_account_what_it_may_do_and_the_checks_the_page_makes_first.py](demo_07_the_ui_s_account_what_it_may_do_and_the_checks_the_page_makes_first.py) | The UI's account: what it may do, and the checks the page makes first |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

An ACME browser login through IAP and a deployed Streamlit UI, API and ingest lane.

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The UI's own environment says how it signs people in, where it uploads and which API it calls. The block prints the five names that matter and exports the UI's address for the steps below. An empty CHAT_URL means the chat service is not deployed on this lane, and then Chat has no brain picker. The page streams from the API directly, which is the journey this lesson follows.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The UI's own environment says how it signs people in, where it uploads and which API it calls. The block prints the five names that matter and exports the UI's address for the steps below. An empty CHAT_URL means the chat service is not deployed on this lane, and then Chat has no brain picker. The page streams from the API directly, which is the journey this lesson follows.

Operation: bash — run in the operator shell, once per shell.

Expected shape, not a promised result:

```text
AUTH_MODE      iap
RAG_API_URL    https://documind-api-NUMBER.asia-south1.run.app
UPLOAD_BUCKET  documind-ai-YOUR-ID-uploads
IAP_AUDIENCE   /projects/NUMBER/locations/asia-south1/services/documind-ui
CHAT_URL       https://documind-chat-NUMBER.asia-south1.run.app
UI=https://documind-ui-NUMBER.asia-south1.run.app
```

### demo_03_the_front_door_iap_the_ui_s_settings_and_who_may_sign_in.py

Do it: the service's account, IAP's flag, who may sign in, and a request without one

**`step_01_the_service_s_account_iap_s_flag_who_may_s(session)` — The front door: IAP, the UI's settings, and who may sign in / Do it: the service's account, IAP's flag, who may sign in, and a request without one**

Do it: the service's account, IAP's flag, who may sign in, and a request without one

Operation: bash — run in the operator shell (four reads).

IDE adaptation: Run with the page's shell semantics: every line is a read. If the UI is not behind IAP, grep prints nothing and the IAP policy and the unsigned request after it show why, instead of the cell stopping at grep.

Expected shape, not a promised result:

```text
documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    run.googleapis.com/iap-enabled: 'true'
roles/iap.httpsResourceAccessor	user:you@example.com
without a sign-in: HTTP 302 -> https://accounts.google.com/o/oauth2/v2/auth?client_id=...
```

### demo_04_the_upload_a_note_you_write_uploaded_in_the_browser_followed_to_the_ledger.py

First write the note on the operator machine. The page's file picker opens the computer your browser runs on, so the note has to get there. In a Cloud Workstation or the Cloud Shell editor, right-click the file in the explorer and choose Download. In a plain terminal, paste the printed text into a new file with any editor. A pasted copy can differ in its line endings, and then its hash differs from the one printed here. That is the version contract from lesson 1.1 at work, not a fault. First write the note on the operator machine. The page's file picker opens the computer your browser runs on, so the note has to get there. In a Cloud Workstation or the Cloud Shell editor, right-click the file in the explorer and choose Download. In a plain terminal, paste the printed text into a new file with any editor. A pasted copy can differ in its line endings, and then its hash differs from the one printed here. That is the version contract from lesson 1.1 at work, not a fault. In the browser, open Documents, choose the file, and click Index documents. The page reports the object it wrote and its generation, then says the upload is complete and indexing is still in progress. Wait half a minute and click Refresh indexing status until the note appears in Versions. Then follow it from the shell:

**`step_01_write_the_note_upload_it_in_the_browser_fo(session)` — The upload: a note you write, uploaded in the browser, followed to the ledger / Do it: write the note, upload it in the browser, follow it**

First write the note on the operator machine. The page's file picker opens the computer your browser runs on, so the note has to get there. In a Cloud Workstation or the Cloud Shell editor, right-click the file in the explorer and choose Download. In a plain terminal, paste the printed text into a new file with any editor. A pasted copy can differ in its line endings, and then its hash differs from the one printed here. That is the version contract from lesson 1.1 at work, not a fault.

Operation: bash — run in the operator shell (writes one small file in your home directory).

**`step_02_write_the_note_upload_it_in_the_browser_fo(session)` — The upload: a note you write, uploaded in the browser, followed to the ledger / Do it: write the note, upload it in the browser, follow it**

First write the note on the operator machine. The page's file picker opens the computer your browser runs on, so the note has to get there. In a Cloud Workstation or the Cloud Shell editor, right-click the file in the explorer and choose Download. In a plain terminal, paste the printed text into a new file with any editor. A pasted copy can differ in its line endings, and then its hash differs from the one printed here. That is the version contract from lesson 1.1 at work, not a fault. In the browser, open Documents, choose the file, and click Index documents. The page reports the object it wrote and its generation, then says the upload is complete and indexing is still in progress. Wait half a minute and click Refresh indexing status until the note appears in Versions. Then follow it from the shell:

Operation: bash — run in the operator shell (the object, the worker's line, your hash, the ledger row).

Manual action: In the ACME UI, Documents -> Upload: choose the exact ~/pune_visitor_rules.md created in the previous step, then Index documents. Refresh until indexed. If your browser runs elsewhere, download this exact file from the workstation first. Type done after the UI checkpoint.

IDE adaptation: Verify the exact UI-uploaded bytes, source generation, claim and current chunks; an unrelated latest ingest_ok event cannot satisfy this checkpoint. Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
text/plain	4xx	17586xxxxxxxxxxx
2026-09-2xT1x:xx:xx.xxxxxxZ	acme_3f9c2b7e1a04...	3	0	3
your file's hash begins: 3f9c2b7e1a04
acme/pune_visitor_rules.md indexed chunks 3 reused 0 embedded 3
versions NN | last event ingest_ok
```

### demo_05_the_answer_asked_in_chat_streamed_and_the_row_that_names_you.py

In the browser, open Chat and ask: What colour badge do visitors wear at the Pune warehouse? The sources arrive first and the answer streams after them. The answer ends with a pill. Hover over it to see the note's clause, and open Sources under the answer. Then ask the same question from the shell and read the two newest rows:

**`step_01_ask_in_the_browser_ask_from_the_shell_read(session)` — The answer: asked in Chat, streamed, and the row that names you / Do it: ask in the browser, ask from the shell, read both rows**

In the browser, open Chat and ask: What colour badge do visitors wear at the Pune warehouse? The sources arrive first and the answer streams after them. The answer ends with a pill. Hover over it to see the note's clause, and open Sources under the answer. Then ask the same question from the shell and read the two newest rows:

Operation: bash — run in the operator shell (one question, a rupee; one log read).

Manual action: In the deployed UI Chat, ask the visitor-badge question from this lesson and wait for the cited answer. Type done to compare the browser and operator API records.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
from the shell: Every visitor to the Pune warehouse wears an amber badge, issued at gate | ['pune_visitor_rules.md']
2026-09-2xT1x:xx:xx.xxxxxxZ	query	documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com	ui	acme	20
2026-09-2xT1x:xx:xx.xxxxxxZ	stream	you@example.com	ui	acme	20
```

### demo_06_citations_the_pills_the_sources_and_the_link_signed_through_iam.py

In the browser, under the answer from step 5, open Sources and click Open source on the note. A new tab shows the note's text from the bucket, through a link that stops working in 15 minutes. Then capture the same answer as a transcript and paste it into the renderer in step 1:

**`step_01_open_the_source_then_render_your_own_trans(session)` — Citations: the pills, the sources, and the link signed through IAM / Do it: open the source, then render your own transcript**

In the browser, under the answer from step 5, open Sources and click Open source on the note. A new tab shows the note's text from the bucket, through a link that stops working in 15 minutes. Then capture the same answer as a transcript and paste it into the renderer in step 1:

Operation: bash — run in the operator shell (one stream, a rupee).

Manual action: Open the answer's citation/source in the UI and inspect the signed link. Type done to render and inspect the transcript from Python.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
citation events: 5 | tokens: NN | done: 1
first citation: pune_visitor_rules.md | kind text | page None | quote 'VR-01 - Badges\nEvery visitor to the Pune warehou'
...
```

### demo_07_the_ui_s_account_what_it_may_do_and_the_checks_the_page_makes_first.py

Do it: read the account's grants, Rs 0

**`step_01_read_the_account_s_grants_rs_0(session)` — The UI's account: what it may do, and the checks the page makes first / Do it: read the account's grants, Rs 0**

Do it: read the account's grants, Rs 0

Operation: bash — run in the operator shell (reads only).

Expected shape, not a promised result:

```text
project roles:
roles/aiplatform.user
roles/datastore.user
roles/documentai.apiUser
roles/secretmanager.secretAccessor
roles/speech.editor
uploads bucket: ['roles/storage.objectAdmin']
may invoke documind-api: ['roles/run.invoker']
may invoke documind-chat: ['roles/run.invoker']
may invoke documind-ingest: none
on itself: ['roles/iam.serviceAccountTokenCreator']
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_3.8_UI_Journey_WIX.html`. All 35 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `f27f9d0481047e5469cc8e52c3997f8bea47a544`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
