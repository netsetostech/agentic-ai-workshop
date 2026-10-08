# Lesson 1.7: Publish versions, retire documents and reject stale events

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_publish_the_swap_and_the_reader_s_guard.py](demo_03_publish_the_swap_and_the_reader_s_guard.py) | Publish: the swap, and the reader's guard |
| 4 | [demo_04_superseded_the_retired_rows_bookkeeping_and_the_clock_that_removes_them.py](demo_04_superseded_the_retired_rows_bookkeeping_and_the_clock_that_removes_them.py) | Superseded: the retired rows' bookkeeping, and the clock that removes them |
| 5 | [demo_05_stale_the_generation_guard_and_three_replayed_events.py](demo_05_stale_the_generation_guard_and_three_replayed_events.py) | Stale: the generation guard, and three replayed events |
| 6 | [demo_06_withdrawn_retire_a_document_by_hand_then_restore_it.py](demo_06_withdrawn_retire_a_document_by_hand_then_restore_it.py) | Withdrawn: retire a document by hand, then restore it |
| 7 | [demo_07_the_three_states_side_by_side.py](demo_07_the_three_states_side_by_side.py) | The three states side by side |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The handbook history from 1.6 and the smoke note from 1.4. Use the conditional repair only if the note is absent.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Conditional recovery

- [recovery/demo_06_withdrawn_retire_a_document_by_hand_then_restore_it.py](recovery/demo_06_withdrawn_retire_a_document_by_hand_then_restore_it.py) — The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

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

### demo_03_publish_the_swap_and_the_reader_s_guard.py

Read the handbook's versions, Rs 0

**`step_01_read_the_handbook_s_versions_rs_0(session)` — Publish: the swap, and the reader's guard / Read the handbook's versions, Rs 0**

Read the handbook's versions, Rs 0

Operation: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).

Expected shape, not a promised result:

```text
acme_497809ff...  rows 283  current 283  retired   0
acme_55603088...  rows 283  current   0  retired 283  superseded_by acme_497809ff...  expire_at 2026-10-22  effective_to None
acme_54337b4b...  rows 283  current   0  retired 283  superseded_by acme_497809ff...  expire_at 2026-10-22  effective_to None
current versions: 1 | staged rows: 0
```

### demo_04_superseded_the_retired_rows_bookkeeping_and_the_clock_that_removes_them.py

Do it: the purge plan, Rs 0

**`step_01_the_purge_plan_rs_0(session)` — Superseded: the retired rows' bookkeeping, and the clock that removes them / Do it: the purge plan, Rs 0**

Do it: the purge plan, Rs 0

Operation: bash — run in the operator shell, in $DEMO_ROOT (read-only without APPLY=1).

Expected shape, not a promised result:

```text
{"event": "reconcile_purge_plan", "expired": 0, "retired": 566, "applied": false, "note": "the TTL policy on chunks.expire_at (firestore_indexes.tf) deletes these on its own within a day; this is the manual twin for a lane that has not applied it"}
```

### demo_05_stale_the_generation_guard_and_three_replayed_events.py

The block reads the handbook's generation off the ledger, then publishes three records into the ingest topic exactly as Cloud Storage would, with the generation before the ledger's, the ledger's own, and one after it. The push subscription delivers them to the worker, and the worker's three lines say what it did with each. Nothing on the lane changes.

**`step_01_three_events_three_verdicts_rs_0(session)` — Stale: the generation guard, and three replayed events / Do it: three events, three verdicts, Rs 0**

The block reads the handbook's generation off the ledger, then publishes three records into the ingest topic exactly as Cloud Storage would, with the generation before the ledger's, the ledger's own, and one after it. The push subscription delivers them to the worker, and the worker's three lines say what it did with each. Nothing on the lane changes.

Operation: bash — run in the operator shell, in $DEMO_ROOT (three messages; nothing is indexed).

Expected shape, not a promised result:

```text
the ledger's generation for the handbook: 1758554107123456
TIMESTAMP                 EVENT               GENERATION        LEDGER_GENERATION  REASON
2026-09-22T15:02:31.512Z  ingest_stale_event  1758554107123457                     generation gone: the object was overwritten
2026-09-22T15:02:30.907Z  ingest_duplicate
2026-09-22T15:02:30.211Z  ingest_stale_event  1758554107123455  1758554107123456   older than the ledger
```

### demo_06_withdrawn_retire_a_document_by_hand_then_restore_it.py

The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

**`step_01_withdraw_the_note_test_the_tombstone_resto(session)` — Withdrawn: retire a document by hand, then restore it / Do it: withdraw the note, test the tombstone, restore it**

The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the object, or its last generation; then the hash against the ledger).

Expected shape, not a promised result:

```text
ledger abcdef0123456789 | file abcdef0123456789 | the same bytes
```

**`step_02_withdraw_the_note_test_the_tombstone_resto(session)` — Withdrawn: retire a document by hand, then restore it / Do it: withdraw the note, test the tombstone, restore it**

The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the withdrawal, then two reads).

Expected shape, not a promised result:

```text
{"event": "reconcile_withdrawn", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/smoke_note_v1.md", "fingerprint": "7c2e91a4d05b3f68", "retired_doc_keys": ["acme_9c41d0e2b7f5..."], "retired_ids": ["acme:9c41d0e2b7f5...#0", "acme:9c41d0e2b7f5...#1", "acme:9c41d0e2b7f5...#2"], "retired_chunks": 3, "note": "a tombstone: the object is kept and nothing automatic re-ingests it; make restore SOURCE= does"}
acme/smoke_note_v1.md withdrawn chunks 3
fingerprint 7c2e91a4d05b3f68 | last event reconcile_withdrawn
3 rows | current: 0 | with expire_at: 3 | superseded_by: {'None'}
```

**`step_03_withdraw_the_note_test_the_tombstone_resto(session)` — Withdrawn: retire a document by hand, then restore it / Do it: withdraw the note, test the tombstone, restore it**

The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

Operation: bash — run in the operator shell (one question; paise).

Expected shape, not a promised result:

```text
answerable False | citations 0 | The corpus holds nothing near this question: no passage of this tenant's current documents
```

**`step_04_withdraw_the_note_test_the_tombstone_resto(session)` — Withdrawn: retire a document by hand, then restore it / Do it: withdraw the note, test the tombstone, restore it**

The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

Operation: bash — run in the operator shell (the same bytes again: refused; then the restore).

Expected shape, not a promised result:

```text
ingest_withdrawn	acme_9c41d0e2b7f5...	make restore SOURCE= clears the tombstone
{"event": "reconcile_restored", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/smoke_note_v1.md", "generation": "1758555302345678", "next": "ingest_reactivated inside the undo window, ingest_ok (a fresh version) after it"}
>> event chunks reused embedded: ingest_reactivated	3	3	0
acme/smoke_note_v1.md indexed reused 3 embedded 0
answerable True | The smoke lantern is kept in bay 4 of the Pune warehouse ... [Source 1]
```

### recovery/demo_06_withdrawn_retire_a_document_by_hand_then_restore_it.py

The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

**`step_01_withdraw_the_note_test_the_tombstone_resto(session)` — Withdrawn: retire a document by hand, then restore it / Do it: withdraw the note, test the tombstone, restore it**

The document is the note lesson 1.4 indexed, three chunks under acme/smoke_note_v1.md, with its bytes still at ~/lesson34_note.md; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs. Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read ingest_ok with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

Operation: bash — only if the check said DIFFERENT or the bucket had nothing (rebuilds the note from the kit's fixture and the ledger's hash).

Expected shape, not a promised result:

```text
rebuilt, dated 2026-09-DD
```

### demo_07_the_three_states_side_by_side.py

Read the ledger as the operator does, Rs 0

**`step_01_read_the_ledger_as_the_operator_does_rs_0(session)` — The three states side by side / Read the ledger as the operator does, Rs 0**

Read the ledger as the operator does, Rs 0

Operation: bash — run in the operator shell, in $DEMO_ROOT.

Expected shape, not a promised result:

```text
source                                       status            gen chunks reused embed retired effective  embedding              indexed_at
acme/code_on_wages_2019.pdf                  indexed    ...2671234567     67      0    67       0 -          text-embedding-005@1   2026-09-20T09:14:02
acme/hr_policy_2026.md                       indexed    ...4107123456    283    283     0     283 -          text-embedding-005@1   2026-09-22T13:41:55
acme/smoke_note_v1.md                        indexed    ...5302345678      3      3     0       0 -          text-embedding-005@1   2026-09-22T15:21:40
...
{"ledger": "acme", "fingerprint": "3a9f0c17e5d2b846", "versions": 9, "last_event": "ingest_reactivated"}
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_1.7_Versions_WIX.html`. All 38 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `3fc7051907aad57df30bf22596ebd56a662a00ac`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
