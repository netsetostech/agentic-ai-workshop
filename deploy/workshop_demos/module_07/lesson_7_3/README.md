# Lesson 7.3: Configure and query managed retrieval mirrors

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_mirror_s_rules_run.py](demo_03_the_mirror_s_rules_run.py) | The mirror's rules, run |
| 4 | [demo_04_the_policies_the_pins_and_the_stores.py](demo_04_the_policies_the_pins_and_the_stores.py) | The policies, the pins and the stores |
| 5 | [demo_05_ask_the_stores_and_find_who_found_the_cited_chunk.py](demo_05_ask_the_stores_and_find_who_found_the_cited_chunk.py) | Ask the stores, and find who found the cited chunk |
| 6 | [demo_06_globex_stays_home_the_skip_the_ledger_row_and_a_pin_the_policy_overrides.py](demo_06_globex_stays_home_the_skip_the_ledger_row_and_a_pin_the_policy_overrides.py) | globex stays home: the skip, the ledger row, and a pin the policy overrides |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Configured RAG Engine/Vertex AI Search mirrors and tenant residency policies that permit those regions.

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

### demo_03_the_mirror_s_rules_run.py

Do it

**`step_01_the_mirror_s_rules_run(session)` — The mirror's rules, run / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (the mirror's rules, run; no store, no network).

Expected shape, not a promised result:

```text
policy_of: {'None': 'in', 'any': 'any', 'ANY ': 'any', 'us': 'in'}
permits: {'any -> us-central1': True, 'any -> global': True, 'any -> asia-south1': True, 'in -> us-central1': False, 'in -> global': False, 'in -> asia-south1': True}
1. acme (any) makes version v1 current:
     mirror_ok              rag_engine    upsert            acme_v1 uploaded
     mirror_ok              vertex_search upsert            acme_v1 uploaded
   held {'rag_engine': 'us-central1', 'vertex_search': 'global'}
2. globex (in) adds a note:
     mirror_policy_skipped  rag_engine    upsert            in
     mirror_policy_skipped  vertex_search upsert            in
   held {}
3. globex adds a second note:
   held {}
4. acme's policy is turned to in, and version v2 becomes current:
     mirror_policy_skipped  rag_engine    upsert            in
     mirror_policy_skipped  vertex_search upsert            in
   held {}
   the stores still hold {'rag_engine': ['acme_v1'], 'vertex_search': ['acme_v1']}
5. v1 is retired:
     mirror_ok              rag_engine    delete:superseded 1
     mirror_ok              vertex_search delete:superseded 1
   the stores hold {'rag_engine': [], 'vertex_search': []}
the audit trail:
   doc.mirror upsert rag_engine acme_v1
   doc.mirror upsert vertex_search acme_v1
   doc.mirror delete:superseded rag_engine acme_v1
   doc.mirror delete:superseded vertex_search acme_v1
```

### demo_04_the_policies_the_pins_and_the_stores.py

Do it

**`step_01_the_policies_the_pins_and_the_stores(session)` — The policies, the pins and the stores / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (reads only).

Expected shape, not a promised result:

```text
acme: data_region=any
acme: retrieval_backend=vector
zeta: data_region=any
zeta: retrieval_backend=vertex_search
globex: data_region=in
globex: retrieval_backend=default (the deployment RETRIEVAL_BACKEND)
cd services/ingest && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID RAG_LOCATION=us-central1 AUDIT_BUCKET=documind-ai-YOUR-ID-audit \
  python managed.py --project documind-ai-YOUR-ID --status --mode both
{"tenant": "acme", "store": "rag_engine", "ledger_current": 21, "held": 18, "missing": 3, "orphans": 0, "status": "drift", "missing_doc_keys": ["acme_0994e77d201672aa703e6d5a9a00590d117ad98239b319e900a0d6a787ede170", "acme_80403acbbf9b2ada3bb37bfa6983bd864696ed45ca459a5ad7cf0296596ca987", "acme_ef63c85dc631e96e6c46364c3188f3f7a9a9283ad2e88074494d378399e1a71b"], "orphan_doc_keys": []}
{"tenant": "acme", "store": "vertex_search", "ledger_current": 21, "held": 18, "missing": 3, "orphans": 0, "status": "drift", "missing_doc_keys": ["acme_0994e77d201672aa703e6d5a9a00590d117ad98239b319e900a0d6a787ede170", "acme_80403acbbf9b2ada3bb37bfa6983bd864696ed45ca459a5ad7cf0296596ca987", "acme_ef63c85dc631e96e6c46364c3188f3f7a9a9283ad2e88074494d378399e1a71b"], "orphan_doc_keys": []}
{"tenant": "globex", "store": "rag_engine", "ledger_current": 3, "status": "no store", "hint": "no RAG Engine corpus 'documind-globex' in us-central1: make rag-corpus TENANT=globex"}
{"tenant": "globex", "store": "vertex_search", "ledger_current": 3, "status": "no store", "hint": "no Vertex AI Search data store 'documind-globex' in global: MANAGED_SEARCH=true make plan / make up declares one per tenant (managed.tf)"}
{"tenant": "zeta", "store": "rag_engine", "ledger_current": 7, "held": 7, "missing": 0, "orphans": 0, "status": "in sync", "missing_doc_keys": [], "orphan_doc_keys": []}
{"tenant": "zeta", "store": "vertex_search", "ledger_current": 7, "held": 7, "missing": 0, "orphans": 0, "status": "in sync", "missing_doc_keys": [], "orphan_doc_keys": []}
```

### demo_05_ask_the_stores_and_find_who_found_the_cited_chunk.py

Do it The answer's citation carries no found_by, because the kit's Citation has no such field. The stamp is on the chunk in the pool. This cell asks the API again, then runs the kit's own retrieve() in your shell with backend rag_engine, the call the API made, and looks for the cited chunk in that pool.

**`step_01_ask_the_stores_and_find_who_found_the_cite(session)` — Ask the stores, and find who found the cited chunk / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (acme's pin back to RAG Engine, then one question for each tenant).

Expected shape, not a promised result:

```text
acme: retrieval_backend=rag_engine
acme: retrieval_backend rag_engine, policy_fallback 0; pool 17, 14 from a managed store
  A: A confirmed employee at grade E3 or above serves a notice period of 60 days [2].
  cites acme:acme_497809ff...#rag-c31c1f459b60 (hr_policy_2026.md)
zeta: retrieval_backend vertex_search, policy_fallback 0; pool 12, 12 from a managed store
  A: A confirmed employee at grade L4 or above serves a notice period of 30 days [1].
  cites zeta:zeta_e920a147...#vs-9b9cb379153b (hr_policy_zeta_2026.md)
globex: retrieval_backend vector, policy_fallback 0; pool 20, 0 from a managed store
  A: Either party may terminate the agreement for convenience on 120 days' written notice [1].
  cites globex:a0d13745...#2 (msa_globex_2026.md)
```

**`step_02_ask_the_stores_and_find_who_found_the_cite(session)` — Ask the stores, and find who found the cited chunk / Do it**

The answer's citation carries no found_by, because the kit's Citation has no such field. The stamp is on the chunk in the pool. This cell asks the API again, then runs the kit's own retrieve() in your shell with backend rag_engine, the call the API made, and looks for the cited chunk in that pool.

Operation: bash — run in the operator shell, in the kit (the same question to the API, then through the kit's own retrieve()).

Expected shape, not a promised result:

```text
the API: retrieval_backend rag_engine, 14 of the pool's 17 chunks from the store
the same question through the kit's retrieve(), backend rag_engine: 17 chunks
  found_by rag_engine    14   for example acme:acme_497809ff...#rag-c31c1f459b60
  found_by (none)         3   for example acme:0994e77d...#0
the chunk the answer cites: acme:acme_497809ff...#rag-c31c1f459b60
  found_by rag_engine, score 0.706 (1 minus its distance), from hr_policy_2026.md
```

### demo_06_globex_stays_home_the_skip_the_ledger_row_and_a_pin_the_policy_overrides.py

Do it Then read what the worker's mirror said about the note, and the ledger row it stamped: If your lines are missing, the worker instance that took the note had already said it: the skip is said once per tenant and store per instance. The cell then prints the last week's lines instead, and the empty mirrored on the row is the record for this document. Last, try to move globex's text with a pin:

**`step_01_globex_stays_home_the_skip_the_ledger_row(session)` — globex stays home: the skip, the ledger row, and a pin the policy overrides / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (a note to globex, whose text may not leave India).

Expected shape, not a promised result:

```text
...
>> gs://documind-ai-YOUR-ID-uploads/globex/globex_visitor_note_2026.md - waiting for the worker (up to 5 min)
>> event doc_key chunks reused embedded retired effective_from
>> ingest_ok	globex_e1d732be92b3b1a9bf473b161aa5dc24da5a560289c49e4a5991032067516da9	1	0	1	0	
>> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=globex_visitor_note_2026.md API=<candidate url>
```

**`step_02_globex_stays_home_the_skip_the_ledger_row(session)` — globex stays home: the skip, the ledger row, and a pin the policy overrides / Do it**

Then read what the worker's mirror said about the note, and the ledger row it stamped:

Operation: bash — run in the operator shell, in the kit (reads only).

Expected shape, not a promised result:

```text
the worker's mirror lines for globex since 2026-09-24T07:30:00Z:
  07:30:09 mirror_policy_skipped  store rag_engine    region us-central1 data_region in
  07:30:10 mirror_policy_skipped  store vertex_search region global      data_region in
the ledger row for globex/globex_visitor_note_2026.md: status indexed, mirrored {}
globex's data_region, as GET /v1/sources reports it: in
```

**`step_03_globex_stays_home_the_skip_the_ledger_row(session)` — globex stays home: the skip, the ledger row, and a pin the policy overrides / Do it**

If your lines are missing, the worker instance that took the note had already said it: the skip is said once per tenant and store per instance. The cell then prints the last week's lines instead, and the empty mirrored on the row is the record for this document. Last, try to move globex's text with a pin:

Operation: bash — run in the operator shell, in the kit (globex pinned to a store for one question, then unpinned).

Expected shape, not a promised result:

```text
globex: retrieval_backend=rag_engine
globex: retrieval_backend vector, policy_fallback 1; pool 20, 0 from a managed store
  A: Either party may terminate the agreement for convenience on 120 days' written notice [1].
  cites globex:a0d13745...#2 (msa_globex_2026.md)
globex: retrieval_backend=default
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_7.3_Managed_Mirrors_WIX.html`. All 26 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `5d2f8eed1c871bf3e8af3c1094e90280a07c7795`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
