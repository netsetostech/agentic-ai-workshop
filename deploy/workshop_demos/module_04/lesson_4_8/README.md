# Lesson 4.8: Exercise DLP, guardrails and audit behavior

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_pii_scan_one_list_and_a_note_that_trips_it.py](demo_03_the_pii_scan_one_list_and_a_note_that_trips_it.py) | The PII scan: one list, and a note that trips it |
| 4 | [demo_04_the_findings_types_and_offsets_in_firestore_and_in_the_dlp_tab.py](demo_04_the_findings_types_and_offsets_in_firestore_and_in_the_dlp_tab.py) | The findings: types and offsets, in Firestore and in the DLP tab |
| 5 | [demo_05_model_armor_the_template_the_guard_and_a_candidate_with_armor_on.py](demo_05_model_armor_the_template_the_guard_and_a_candidate_with_armor_on.py) | Model Armor: the template, the guard, and a candidate with ARMOR=on |
| 6 | [demo_06_four_questions_to_the_candidate_plain_two_injections_a_pan.py](demo_06_four_questions_to_the_candidate_plain_two_injections_a_pan.py) | Four questions to the candidate: plain, two injections, a PAN |
| 7 | [demo_07_the_audit_trail_the_events_in_the_retention_bucket.py](demo_07_the_audit_trail_the_events_in_the_retention_bucket.py) | The audit trail: the events in the retention bucket |
| 8 | [demo_08_the_audit_tab_what_the_admin_console_reads_and_what_it_misses.py](demo_08_the_audit_tab_what_the_admin_console_reads_and_what_it_misses.py) | The audit tab: what the admin console reads, and what it misses |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [cleanup/demo_08_the_audit_tab_what_the_admin_console_reads_and_what_it_misses.py](cleanup/demo_08_the_audit_tab_what_the_admin_console_reads_and_what_it_misses.py) — At lesson end: The note came from you, and it should not stay in acme's corpus. make retire flags its chunks, which leave retrieval, and marks its ledger row WITHDRAWN; the object stays in the uploads bucket. Look at what stays. The findings record stays in dlp_findings until someone deletes it. The two audit events stay for five years, whatever anyone wants, which is what retention means. The withdrawal writes no audit event of its own: doc.delete is a registered action, and nothing in the kit emits it.
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

### demo_03_the_pii_scan_one_list_and_a_note_that_trips_it.py

Do it

**`step_01_the_pii_scan_one_list_and_a_note_that_trip(session)` — The PII scan: one list, and a note that trips it / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (a small note with the kit's synthetic identifiers, uploaded to acme).

Expected shape, not a promised result:

```text
Copying file:///home/you/lesson83_vendor_note.md to gs://documind-ai-YOUR-ID-uploads/acme/lesson83_vendor_note.md
  Completed files 1/1 | 303.0B/303.0B
>> gs://documind-ai-YOUR-ID-uploads/acme/lesson83_vendor_note.md - waiting for the worker (up to 5 min)
>> indexed: acme_...	1	1
```

### demo_04_the_findings_types_and_offsets_in_firestore_and_in_the_dlp_tab.py

Do it: the records The console sits behind IAP and admits only the addresses the lane was deployed with as ADMIN_EMAILS. If it answers 403 - Admins only, your address is not among them; the cell above has already read the records the tab draws.

**`step_01_the_records(session)` — The findings: types and offsets, in Firestore and in the DLP tab / Do it: the records**

Do it: the records

Operation: bash — run in the operator shell, in the kit (acme's newest findings records; reads only).

Expected shape, not a promised result:

```text
acme/lesson83_vendor_note.md: 5 finding(s), INDIA_AADHAAR_INDIVIDUAL, INDIA_GST_INDIVIDUAL, INDIA_PAN_INDIVIDUAL, PERSON_NAME, PHONE_NUMBER
  acme/inv_2026_0412.md: 4 finding(s), EMAIL_ADDRESS, INDIA_GST_INDIVIDUAL, INDIA_PAN_INDIVIDUAL, PHONE_NUMBER
one finding, whole: {'info_type': 'PERSON_NAME', 'likelihood': 'LIKELY', 'offset': 159, 'chunk_id': 'acme:SHA#0'}
```

**`step_02_the_dlp_tab(session)` — The findings: types and offsets, in Firestore and in the DLP tab / Do it: the DLP tab**

The console sits behind IAP and admits only the addresses the lane was deployed with as ADMIN_EMAILS. If it answers 403 - Admins only, your address is not among them; the cell above has already read the records the tab draws.

Operation: bash — run in the operator shell, in the kit (the admin console's address).

Manual action: Open the deployed admin DLP tab and inspect the synthetic note's findings. Type done to compare them with the source fields printed next.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
https://documind-admin-NUMBER.asia-south1.run.app   <- open in your browser, then the DLP tab
```

### demo_05_model_armor_the_template_the_guard_and_a_candidate_with_armor_on.py

Do it

**`step_01_model_armor_the_template_the_guard_and_a_c(session)` — Model Armor: the template, the guard, and a candidate with ARMOR=on / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (a revision with ARMOR=on and no traffic).

Expected shape, not a promised result:

```text
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \
  --update-env-vars "^|^GENERATOR_MODEL=gemini-3.6-flash|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=on|..."
...
>> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app
```

### demo_06_four_questions_to_the_candidate_plain_two_injections_a_pan.py

Each status beside the first characters of its body, then the candidate's tag removed. The cell asks acme four questions as you. The plain question must be answered. The English injection is a textbook attempt, and it must come back 400 prompt_blocked. The Hinglish one asks for the same thing the way people here actually type it, and it is the reason the template's floor is MEDIUM. The last question contains a synthetic PAN, and it tests the template's sensitive-data filter. Clean up: the candidate's tag

**`step_01_four_questions_to_the_candidate_plain_two(session)` — Four questions to the candidate: plain, two injections, a PAN / Four questions to the candidate: plain, two injections, a PAN**

Each status beside the first characters of its body, then the candidate's tag removed. The cell asks acme four questions as you. The plain question must be answered. The English injection is a textbook attempt, and it must come back 400 prompt_blocked. The Hinglish one asks for the same thing the way people here actually type it, and it is the reason the template's floor is MEDIUM. The last question contains a synthetic PAN, and it tests the template's sensitive-data filter.

Operation: bash — run in the operator shell, in the kit (four questions to the candidate).

Expected shape, not a promised result:

```text
a plain question             200  {"answer":"A confirmed employee at grade E3 or above serve
  an injection, in English     400  {"detail":"prompt_blocked"}
  an injection, in Hinglish    400  {"detail":"prompt_blocked"}
  a synthetic PAN, asked       200  {"answer":"Invoice INV-2026-0412 carries that PAN [1].","c
```

**`step_02_clean_up_the_candidate_s_tag(session)` — Four questions to the candidate: plain, two injections, a PAN / Clean up: the candidate's tag**

Clean up: the candidate's tag

Operation: bash — run in the operator shell, in the kit (the candidate's tag and its recorded name removed).

Expected shape, not a promised result:

```text
Updating traffic...done.
Done.
URL: https://documind-api-...run.app
Traffic:
  100% documind-api-000MM-xxx      (the live revision, as before; no candidate tag)
```

### demo_07_the_audit_trail_the_events_in_the_retention_bucket.py

Do it

**`step_01_the_audit_trail_the_events_in_the_retentio(session)` — The audit trail: the events in the retention bucket / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (today's audit objects for acme, one event, the bucket's retention, and a delete it must refuse).

Expected shape, not a promised result:

```text
YYYY/MM/DD/acme/doc.upload-UUID1.json
  YYYY/MM/DD/acme/dlp.finding-UUID2.json
  YYYY/MM/DD/acme/doc.upload-UUID3.json
    id: "UUID"
    ts: "YYYY-MM-DDTHH:MM:SS.ssssss+00:00"
    action: "dlp.finding"
    actor: {"tenant_id": "acme", "email": "system:ingest"}
    target: {"type": "document", "id": "acme_SHA", "tenant_id": "acme"}
    meta: {"types": ["INDIA_AADHAAR_INDIVIDUAL", "INDIA_GST_INDIVIDUAL", "INDIA_PAN_INDIVIDUAL", "PERSON_NAME", "PHONE_NUMBER"], "count": 5}
retention 157680000 s (5 years), locked False
delete refused: 403 Forbidden
```

### demo_08_the_audit_tab_what_the_admin_console_reads_and_what_it_misses.py

Do it

**`step_01_the_audit_tab_what_the_admin_console_reads(session)` — The audit tab: what the admin console reads, and what it misses / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (what the admin console's audit tab can see; reads only).

Expected shape, not a promised result:

```text
{'tenant.create': 1} | doc.upload in it: 0
```

### cleanup/demo_08_the_audit_tab_what_the_admin_console_reads_and_what_it_misses.py

At lesson end: The note came from you, and it should not stay in acme's corpus. make retire flags its chunks, which leave retrieval, and marks its ledger row WITHDRAWN; the object stays in the uploads bucket. Look at what stays. The findings record stays in dlp_findings until someone deletes it. The two audit events stay for five years, whatever anyone wants, which is what retention means. The withdrawal writes no audit event of its own: doc.delete is a registered action, and nothing in the kit emits it.

**`step_01_clean_up_withdraw_the_note(session)` — The audit tab: what the admin console reads, and what it misses / Clean up: withdraw the note**

The note came from you, and it should not stay in acme's corpus. make retire flags its chunks, which leave retrieval, and marks its ledger row WITHDRAWN; the object stays in the uploads bucket. Look at what stays. The findings record stays in dlp_findings until someone deletes it. The two audit events stay for five years, whatever anyone wants, which is what retention means. The withdrawal writes no audit event of its own: doc.delete is a registered action, and nothing in the kit emits it.

Operation: bash — run in the operator shell, in the kit (the note withdrawn from the index).

Expected shape, not a promised result:

```text
{"event": "reconcile_retired", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/lesson83_vendor_note.md", ...}
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_4.8_DLP_Guard_Audit_WIX.html`. All 32 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `b60e0c11b63c21fda4508d9185902d1106f5f2ee`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
