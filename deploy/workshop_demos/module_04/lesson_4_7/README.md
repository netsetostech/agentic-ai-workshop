# Lesson 4.7: Test valid access, denied access and cross-tenant requests

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_refusal_ladder_the_door_a_401_and_a_403_side_by_side.py](demo_03_the_refusal_ladder_the_door_a_401_and_a_403_side_by_side.py) | The refusal ladder: the door, a 401 and a 403 side by side |
| 4 | [demo_04_cross_tenant_every_isolation_row_as_the_outsider_and_as_a_member.py](demo_04_cross_tenant_every_isolation_row_as_the_outsider_and_as_a_member.py) | Cross-tenant: every isolation row, as the outsider and as a member |
| 5 | [demo_05_residency_each_tenant_s_data_region_and_the_rule_that_applies_it.py](demo_05_residency_each_tenant_s_data_region_and_the_rule_that_applies_it.py) | Residency: each tenant's data_region, and the rule that applies it |
| 6 | [demo_06_the_policy_against_a_pin_a_tenant_kept_in_india_pinned_to_a_store_outside_it.py](demo_06_the_policy_against_a_pin_a_tenant_kept_in_india_pinned_to_a_store_outside_it.py) | The policy against a pin: a tenant kept in India, pinned to a store outside it |
| 7 | [demo_07_the_kit_s_own_tests_of_the_same_refusals.py](demo_07_the_kit_s_own_tests_of_the_same_refusals.py) | The kit's own tests of the same refusals |

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_refusal_ladder_the_door_a_401_and_a_403_side_by_side.py

Do it

**`step_01_the_refusal_ladder_the_door_a_401_and_a_40(session)` — The refusal ladder: the door, a 401 and a 403 side by side / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (four requests to /v1/query; one is answered).

Expected shape, not a promised result:

```text
no token                   403  (Cloud Run's own page: the request never reached the API)
  a token without its email  401  {"detail":"the bearer token carries no verified email"}
  the outsider's token       403  {"detail":"not a member of this tenant"}
  documind-ui-sa's token     200  {"answer":"A confirmed employee at grade E3 or above serves a noti
```

### demo_04_cross_tenant_every_isolation_row_as_the_outsider_and_as_a_member.py

Do it

**`step_01_cross_tenant_every_isolation_row_as_the_ou(session)` — Cross-tenant: every isolation row, as the outsider and as a member / Do it**

Do it

Operation: bash — run in the operator shell, in the kit (11 outsider requests, then 11 member questions).

Expected shape, not a promised result:

```text
the outsider, on 11 isolation rows: 403 on 100%
  iso-01 as zeta   HTTP 200  answerable True   no '40,000'
  iso-02 as globex HTTP 200  answerable False  no '1,84,500'
  iso-03 as globex HTTP 200  answerable False  no '15 June'
  iso-04 as zeta   HTTP 200  answerable False  no '1,005'
  iso-05 as zeta   HTTP 200  answerable False  no 'AAAPZ1234C'
  iso-06 as globex HTTP 200  answerable False  no 'twenty-six weeks'
  iso-07 as globex HTTP 200  answerable False  no "fifteen days' wages"
  iso-08 as zeta   HTTP 200  answerable False  no 'recommendations of the Council'
  iso-09 as zeta   HTTP 200  answerable False  no 'single point of contact'
  iso-10 as globex HTTP 200  answerable False  no 'twice the rate of wages'
  mm-04  as zeta   HTTP 200  answerable False  no '5.2 per cent'
```

### demo_05_residency_each_tenant_s_data_region_and_the_rule_that_applies_it.py

Do it: the three policies

**`step_01_the_three_policies(session)` — Residency: each tenant's data_region, and the rule that applies it / Do it: the three policies**

Do it: the three policies

Operation: bash — run in the operator shell, in the kit (each tenant's data_region; reads only).

Expected shape, not a promised result:

```text
acme: data_region=any
zeta: data_region=any
globex: data_region=in
```

### demo_06_the_policy_against_a_pin_a_tenant_kept_in_india_pinned_to_a_store_outside_it.py

A pin set, a minute's wait, one question, its usage row, and the pin cleared. The cell pins globex to rag_engine, a managed store in us-central1, then waits a minute, because the API reads each tenant's settings once a minute. It asks one of globex's own questions and reads the question's usage row: which backend served, and policy_fallback. Then it clears the pin. RETRIEVAL_BACKEND is given on each make line on purpose, because a value exported in your shell would otherwise win.

**`step_01_the_policy_against_a_pin_a_tenant_kept_in(session)` — The policy against a pin: a tenant kept in India, pinned to a store outside it / The policy against a pin: a tenant kept in India, pinned to a store outside it**

A pin set, a minute's wait, one question, its usage row, and the pin cleared. The cell pins globex to rag_engine, a managed store in us-central1, then waits a minute, because the API reads each tenant's settings once a minute. It asks one of globex's own questions and reads the question's usage row: which backend served, and policy_fallback. Then it clears the pin. RETRIEVAL_BACKEND is given on each make line on purpose, because a value exported in your shell would otherwise win.

Operation: bash — run in the operator shell, in the kit (a pin set, one question, its usage row, the pin cleared).

Expected shape, not a promised result:

```text
globex: retrieval_backend=rag_engine
globex asked: HTTP 200, answerable True
vector	1
globex: retrieval_backend=default
```

### demo_07_the_kit_s_own_tests_of_the_same_refusals.py

The smoke test's check 3b, and the chat service's check 4. The kit asserts these refusals itself, so a deploy that opened a door would fail its own smoke test. smoke/smoke.py sends its question again with no token and passes only on 401 or 403. smoke/smoke_chat.py asks the chat service as the outsider and passes only on a 403 from the roster, not a 401 from the verifier. The MCP server's smoke test does the same. The cell runs the API's smoke test and keeps two of its lines.

**`step_01_the_kit_s_own_tests_of_the_same_refusals(session)` — The kit's own tests of the same refusals / The kit's own tests of the same refusals**

The smoke test's check 3b, and the chat service's check 4. The kit asserts these refusals itself, so a deploy that opened a door would fail its own smoke test. smoke/smoke.py sends its question again with no token and passes only on 401 or 403. smoke/smoke_chat.py asks the chat service as the outsider and passes only on a 403 from the roster, not a 401 from the verifier. The MCP server's smoke test does the same. The cell runs the API's smoke test and keeps two of its lines.

Operation: bash — run in the operator shell, in the kit (the kit's smoke test, two of its lines).

IDE adaptation: Run with the page's pipeline status (no pipefail). The cell filters make smoke for the lines this lesson reads; a check failing elsewhere in the smoke shows in those lines instead of stopping the cell before its later lines.

Expected shape, not a promised result:

```text
[PASS] no token refused  status=403
  N pass · 0 fail
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_4.7_Access_Tests_WIX.html`. All 24 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `af7968ba7b37b06283c139e316adcd2049e9156c`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
