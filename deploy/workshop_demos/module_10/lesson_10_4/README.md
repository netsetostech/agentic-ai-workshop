# Lesson 10.4: Route each question to one specialist agent

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_your_lane_the_classes_the_example_index_and_the_switches.py](demo_03_your_lane_the_classes_the_example_index_and_the_switches.py) | Your lane: the classes, the example index and the switches |
| 4 | [demo_04_the_desk_page_and_the_hr_desk_app_in_google_chat.py](demo_04_the_desk_page_and_the_hr_desk_app_in_google_chat.py) | The Desk page, and the HR Desk app in Google Chat |
| 5 | [demo_05_classes_desks_the_rules_first_and_the_google_chat_door_in_the_code.py](demo_05_classes_desks_the_rules_first_and_the_google_chat_door_in_the_code.py) | Classes, desks, the rules first and the Google Chat door, in the code |
| 6 | [demo_06_two_signals_and_one_arbiter_in_the_code.py](demo_06_two_signals_and_one_arbiter_in_the_code.py) | Two signals and one arbiter, in the code |
| 7 | [demo_07_v1_route_and_v1_desk_over_rest.py](demo_07_v1_route_and_v1_desk_over_rest.py) | /v1/route and /v1/desk, over REST |
| 8 | [demo_08_the_shadow_the_rows_and_the_log.py](demo_08_the_shadow_the_rows_and_the_log.py) | The shadow, the rows and the log |
| 10 | [demo_10_verify_it_yourself_the_eval_and_the_checklist.py](demo_10_verify_it_yourself_the_eval_and_the_checklist.py) | Verify it yourself: the eval and the checklist |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Lesson 5.6's Desk: acme's case queues, the gate's rules for acme (desk_gate unwritten), your roles, and token rights for the eval accounts. Step 3 pulls the kit, rebuilds and redeploys rag-api, the UI and the chat service, then applies its Terraform with DESK_JOB=true (optionally with GCHAT_DOOR=true too, then the door's bridge with make deploy-gchat), rosters evalglobex and evalleaver, applies the doc_type registry to acme, zeta and globex, builds acme's and zeta's example index, and switches acme's router on and globex to the statute desk alone; step 8 gives zeta its queues and turns its router to shadow, then on; zeta keeps the gate's rules.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Optional extensions

- [optional/demo_03_your_lane_the_classes_the_example_index_and_the_switches.py](optional/demo_03_your_lane_the_classes_the_example_index_and_the_switches.py) — Optional: turn the Google Chat door on. Plan with GCHAT_DOOR=true beside DESK_JOB=true and apply, deploy chat again so documind-gchat-sa may call it, then make deploy-gchat. Keep GCHAT_DOOR=true on every later make plan and make up. The Workspace part, the door's smoke and its rows need it.
- [optional/demo_04_the_desk_page_and_the_hr_desk_app_in_google_chat.py](optional/demo_04_the_desk_page_and_the_hr_desk_app_in_google_chat.py) — Optional, and only with the door on, a Business or Enterprise Google Workspace account and a Chat app you configured in the Google Cloud console: deploy the Google Chat bridge again so it admits the app's add-on agent, put your Workspace address on acme's roster, switch desk_gchat on for acme, and print the two questions to send the HR Desk app. Without Workspace, skip it: the page's expected conversation shows what it does, and make smoke-gchat proves the door's refusals with the door on.
- [optional/demo_07_v1_route_and_v1_desk_over_rest.py](optional/demo_07_v1_route_and_v1_desk_over_rest.py) — Optional, only with the door on, and no Workspace needed: make smoke-gchat's four refusals and the door's latest rows. It refuses on a lane whose last apply had the door off.
- [optional/demo_08_the_shadow_the_rows_and_the_log.py](optional/demo_08_the_shadow_the_rows_and_the_log.py) — Optional, only with the door on: the desk rows that came through the Google Chat door, then the bridge's claims in its own Firestore database; reads only.

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

### demo_03_your_lane_the_classes_the_example_index_and_the_switches.py

The routed Desk's code was already in the images lesson 5.6 deployed, switched off by desk_route. This cell makes sure your lane runs the code this page quotes: it pulls the kit, builds and redeploys rag-api, the UI and the chat service, then plans and applies the kit's Terraform. Terraform comes last because of DESK_JOB=true, which you keep as 5.6 said: it points the hourly overdue job at the chat image of the commit you pulled, chat:COMMIT, and commands/lesson-12.8.sh in the deploy is what builds that image. Without the flag the plan would remove the job, and make plan's guard would refuse it. The Google Chat door stays off: without GCHAT_DOOR=true the plan declares nothing of terraform/gchat.tf, nor the bridge's account in terraform/desk.tf, and the chat deploy says that documind-gchat-sa does not exist yet. The whole cell takes many minutes. The router is measured as the people it serves, so the kit has an eval account for each kind of caller. evalleaver is an acme leaver: its roles open the case desk and nothing else. evalglobex is a globex employee. Both go on their rosters. Then three accounts get desk_eval, the role that lets them call POST /v1/route. evalglobex also gets ic_member:head_office, because globex's queues, loaded below, name it as the Internal Committee, and a single desk, like any routed Desk, is refused while an office's POSH cases have no reader. The cell also sets CHAT and UI, notes the time in SINCE106 for step 8, and defines 5.6's two helpers again: sa names an account, and etok mints a token as one, for the chat service. make doc-types SEED=manifest writes acme's registry from evals/manifest.json. Each text object gets its class, pinned to the doc_key the manifest records for its bytes, and the kit cross-checks that against what your lane ingested. A figure takes its parent's class, pinned to the version on your lane, because make media drew it there. The town hall video is not_ingested unless you made it. Then the view: each object's current label, its class, its pin, its chunks and what the relabel would do. Last comes the relabel's plan. The registry is written now; the stored rows are not, until APPLY=1. An object an earlier lesson uploaded that the manifest does not name, such as 1.4's and 3.4's smoke notes or 3.8's visitor rules, shows unregistered and keeps unknown; which ones you have depends on the lessons you ran. APPLY=1 runs the plan on every store that filters by class: the Firestore rows, the Vector Search restricts, the Vertex AI Search documents and BigQuery's chunk_source. Then it expires the company's answer cache, so no cached answer from before survives. zeta and globex are seeded and applied in one run each. A run exits 3 when BigQuery deferred a statement because rows were still in its streaming buffer; run the same line again later. The same view again, for acme, without SEED. make route-index takes the route set's dev rows on the routes a company's registry covers, embeds each question once with text-embedding-005 on us-central1, and writes them to tenants/{tenant}/desk_exemplars. The version is a hash of the rows and the model, so the same rows give the same version on every lane. globex gets no index: a single desk asks no classifier and takes no vote. acme goes from off to on. globex gets its queues, with its eval account as the Internal Committee, then single mode with the statute desk: every globex question goes to the law, with no classifier.

**`step_01_the_kit_you_have_now_on_your_lane(session)` — Your lane: the classes, the example index and the switches / Do it: the kit you have now, on your lane**

The routed Desk's code was already in the images lesson 5.6 deployed, switched off by desk_route. This cell makes sure your lane runs the code this page quotes: it pulls the kit, builds and redeploys rag-api, the UI and the chat service, then plans and applies the kit's Terraform. Terraform comes last because of DESK_JOB=true, which you keep as 5.6 said: it points the hourly overdue job at the chat image of the commit you pulled, chat:COMMIT, and commands/lesson-12.8.sh in the deploy is what builds that image. Without the flag the plan would remove the job, and make plan's guard would refuse it. The Google Chat door stays off: without GCHAT_DOOR=true the plan declares nothing of terraform/gchat.tf, nor the bridge's account in terraform/desk.tf, and the chat deploy says that documind-gchat-sa does not exist yet. The whole cell takes many minutes.

Operation: bash — run in the operator shell, in the kit (the kit you have now, on your lane; many minutes).

Expected shape, not a promised result:

```text
...
>> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/api:COMMIT from services/rag-api
...
>> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/ui:COMMIT from services/frontend
...
>> commands/lesson-12.2.sh (DEPLOY block)
...
>> commands/lesson-12.4.sh (DEPLOY block)
...
>> commands/lesson-12.8.sh (DEPLOY block)
...
Plan: N to add, N to change, 0 to destroy.
PASS: no deletes/replacements or existing CI trust changes. Reviewed plan: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
Review the displayed changes, then run this command with 'apply' instead of 'plan'.
PASS: selected plan, confirmed inputs, backend/workspace and state agree: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
...
Apply complete! Resources: N added, N changed, 0 destroyed.
```

**`step_02_two_more_eval_accounts(session)` — Your lane: the classes, the example index and the switches / Do it: two more eval accounts**

The router is measured as the people it serves, so the kit has an eval account for each kind of caller. evalleaver is an acme leaver: its roles open the case desk and nothing else. evalglobex is a globex employee. Both go on their rosters. Then three accounts get desk_eval, the role that lets them call POST /v1/route. evalglobex also gets ic_member:head_office, because globex's queues, loaded below, name it as the Internal Committee, and a single desk, like any routed Desk, is refused while an office's POSH cases have no reader. The cell also sets CHAT and UI, notes the time in SINCE106 for step 8, and defines 5.6's two helpers again: sa names an account, and etok mints a token as one, for the chat service.

Operation: bash — run in the operator shell, in the kit (two URLs, the time, two helpers, two more eval accounts and the roles of three).

Expected shape, not a promised result:

```text
documind-evalglobex-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is on globex
...
acme: data_region=any
zeta: data_region=any
globex: data_region=in
documind-evalleaver-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is on acme
...
acme: data_region=any
zeta: data_region=any
globex: data_region=in
{"tenant": "acme",
 "email": "documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
 "before": ["employee"],
 "after": ["desk_eval", "employee"],
 "granted": ["desk_eval"],
 "revoked": []}
{"tenant": "acme",
 "email": "documind-evalleaver-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
 "before": ["employee"],
 "after": ["desk_eval", "leaver"],
 "granted": ["desk_eval", "leaver"],
 "revoked": ["employee"]}
{"tenant": "globex",
 "email": "documind-evalglobex-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
 "before": ["employee"],
 "after": ["desk_eval", "employee", "ic_member:head_office"],
 "granted": ["desk_eval", "ic_member:head_office"],
 "revoked": []}
```

**`step_03_the_classes(session)` — Your lane: the classes, the example index and the switches / Do it: the classes**

make doc-types SEED=manifest writes acme's registry from evals/manifest.json. Each text object gets its class, pinned to the doc_key the manifest records for its bytes, and the kit cross-checks that against what your lane ingested. A figure takes its parent's class, pinned to the version on your lane, because make media drew it there. The town hall video is not_ingested unless you made it. Then the view: each object's current label, its class, its pin, its chunks and what the relabel would do. Last comes the relabel's plan. The registry is written now; the stored rows are not, until APPLY=1. An object an earlier lesson uploaded that the manifest does not name, such as 1.4's and 3.4's smoke notes or 3.8's visitor rules, shows unregistered and keeps unknown; which ones you have depends on the lessons you ran.

Operation: bash — run in the operator shell, in the kit (acme's registry from the manifest, the view, and the relabel's plan).

Expected shape, not a promised result:

```text
...
{"seed": "acme/annual_report_2026_fig3.png",
 "class": "report",
 "action": "pin",
 "pin": "yours",
 "parent": "annual_report_2026"}
...
{"seed": "acme/hr_policy_2026.md", "class": "policy", "action": "pin", "pin": "acme_497809ffbaa6"}
...
{"seed": "acme/labour_codes_compliance_handbook.pdf",
 "class": "guidance",
 "action": "pin",
 "pin": "acme_bbc851624beb"}
...
{"seed": "acme/msa_acme_2026.md", "class": "contract", "action": "pin", "pin": "acme_cd56da350670"}
...
{"seed": "acme/payment_of_gratuity_act_1972.pdf",
 "class": "statute",
 "action": "pin",
 "pin": "acme_fa044c91c671"}
...
{"seed": "acme/townhall_2026_q1.mp4",
 "class": "transcript",
 "action": "not_ingested",
 "pin": "-",
 "parent": "townhall_2026_q1"}
object                                           label          class      pin                chunks  state
...
acme/annual_report_2026_fig3.png                 figure         report     yours                   N  relabel N rows
...
acme/hr_policy_2026.md                           unknown        policy     acme_497809ffbaa6       N  relabel N rows
...
acme/labour_codes_compliance_handbook.pdf        unknown        guidance   acme_bbc851624beb       N  relabel N rows
...
acme/msa_acme_2026.md                            unknown        contract   acme_cd56da350670       N  relabel N rows
...
acme/payment_of_gratuity_act_1972.pdf            unknown        statute    acme_fa044c91c671       N  relabel N rows
...
acme/pune_visitor_rules.md                       unknown        -          -                       N  unregistered
acme/smoke_note.md                               unknown        -          -                       N  unregistered
acme/smoke_note_v1.md                            unknown        -          -                       N  unregistered
...
{"relabel": "acme/hr_policy_2026.md",
 "doc_key": "acme_497809ffbaa603c49577add351033f4374ad1aefa3394f761be0c9df5e3f3173",
 "rows": N,
 "of": N,
 "from": {"unknown": N},
 "to": "policy",
 "why": "pinned"}
...
{"event": "relabel_plan",
 "tenant": "acme",
 "reset": false,
 "versions": N,
 "to_change": N,
 "rows": N,
 "history_rows": N,
 "unregistered": ["acme/pune_visitor_rules.md", "acme/smoke_note.md", "acme/smoke_note_v1.md"],
 "pin_miss": [],
 "note": "nothing is written without --apply (APPLY=1)"}
```

**`step_04_apply_for_all_three_companies(session)` — Your lane: the classes, the example index and the switches / Do it: apply, for all three companies**

APPLY=1 runs the plan on every store that filters by class: the Firestore rows, the Vector Search restricts, the Vertex AI Search documents and BigQuery's chunk_source. Then it expires the company's answer cache, so no cached answer from before survives. zeta and globex are seeded and applied in one run each. A run exits 3 when BigQuery deferred a statement because rows were still in its streaming buffer; run the same line again later.

Operation: bash — run in the operator shell, in the kit (the relabel applied for acme, then zeta and globex seeded and applied).

Expected shape, not a promised result:

```text
object                                           label          class      pin                chunks  state
...
acme/annual_report_2026_fig3.png                 figure         report     yours                   N  relabel N rows
...
acme/hr_policy_2026.md                           unknown        policy     acme_497809ffbaa6       N  relabel N rows
...
{"relabel": "acme/annual_report_2026_fig3.png",
 "doc_key": "yours",
 "rows": N,
 "of": N,
 "from": {"figure": N},
 "to": "report",
 "why": "pinned"}
...
{"relabel": "acme/hr_policy_2026.md",
 "doc_key": "acme_497809ffbaa603c49577add351033f4374ad1aefa3394f761be0c9df5e3f3173",
 "rows": N,
 "of": N,
 "from": {"unknown": N},
 "to": "policy",
 "why": "pinned"}
...
{"event": "relabel_applied",
 "tenant": "acme",
 "reset": false,
 "versions": N,
 "to_change": N,
 "rows": N,
 "history_rows": N,
 "unregistered": ["acme/pune_visitor_rules.md", "acme/smoke_note.md", "acme/smoke_note_v1.md"],
 "pin_miss": [],
 "firestore_rows": N,
 "vector_datapoints": N,
 "vector_skipped": N,
 "vector_restored": N,
 "vector_removed": N,
 "left_current": N,
 "search": {"updated": N},
 "bigquery": {"updated": N, "deferred": N, "failed": []},
 "answer_cache_expired": N,
 "failed": [],
 "vector_index": "projects/NUMBER/locations/REGION/indexes/INDEX_ID",
 "vertex_search": "checked",
 "fingerprint": "unchanged: a relabel moves no doc_key; the answer cache was expired instead"}
...
{"event": "relabel_applied", "tenant": "zeta", "versions": N, "to_change": N, "rows": N, "unregistered": [], "pin_miss": [], "failed": [], ...}
...
{"event": "relabel_applied", "tenant": "globex", "versions": N, "to_change": N, "rows": N, "unregistered": ["globex/maternity_benefit_amendment_act_2017.pdf"], "pin_miss": [], "failed": [], ...}
```

**`step_05_nothing_left_to_change(session)` — Your lane: the classes, the example index and the switches / Do it: nothing left to change**

The same view again, for acme, without SEED.

Operation: bash — run in the operator shell, in the kit (the view again: nothing left to change).

Expected shape, not a promised result:

```text
object                                           label          class      pin                chunks  state
...
acme/annual_report_2026_fig3.png                 report         report     yours                   N  pinned
...
acme/hr_policy_2026.md                           policy         policy     acme_497809ffbaa6       N  pinned
...
acme/msa_acme_2026.md                            contract       contract   acme_cd56da350670       N  pinned
...
acme/pune_visitor_rules.md                       unknown        -          -                       N  unregistered
acme/smoke_note.md                               unknown        -          -                       N  unregistered
acme/smoke_note_v1.md                            unknown        -          -                       N  unregistered
...
{"event": "relabel_plan",
 "tenant": "acme",
 "reset": false,
 "versions": N,
 "to_change": 0,
 "rows": 0,
 "history_rows": N,
 "unregistered": ["acme/pune_visitor_rules.md", "acme/smoke_note.md", "acme/smoke_note_v1.md"],
 "pin_miss": [],
 "note": "nothing is written without --apply (APPLY=1)"}
```

**`step_06_the_example_index(session)` — Your lane: the classes, the example index and the switches / Do it: the example index**

make route-index takes the route set's dev rows on the routes a company's registry covers, embeds each question once with text-embedding-005 on us-central1, and writes them to tenants/{tenant}/desk_exemplars. The version is a hash of the rows and the model, so the same rows give the same version on every lane. globex gets no index: a single desk asks no classifier and takes no vote.

Operation: bash — run in the operator shell, in the kit (the exemplar index for the two routed tenants: about 200 embeddings each).

Expected shape, not a promised result:

```text
{"tenant": "acme",
 "rows": 198,
 "routes": {"handbook": 51, "out_of_scope": 18, "statute": 129},
 "index_version": "d15e143dd357",
 "embedding_model": "text-embedding-005",
 "written": 198,
 "deleted": [],
 "note": "the router (services/chat/desk_router.py) reads it within 5 minutes"}
{"tenant": "zeta",
 "rows": 198,
 "routes": {"handbook": 51, "out_of_scope": 18, "statute": 129},
 "index_version": "d15e143dd357",
 "embedding_model": "text-embedding-005",
 "written": 198,
 "deleted": [],
 "note": "the router (services/chat/desk_router.py) reads it within 5 minutes"}
```

**`step_07_the_switches(session)` — Your lane: the classes, the example index and the switches / Do it: the switches**

acme goes from off to on. globex gets its queues, with its eval account as the Internal Committee, then single mode with the statute desk: every globex question goes to the law, with no classifier.

Operation: bash — run in the operator shell, in the kit (acme on; globex's queues, then globex in single mode).

Expected shape, not a promised result:

```text
{"tenant": "acme",
 "desk_gate": "rules",
 "desk_max_parts": 1,
 "desk_route": "on",
 "desk_single": null,
 "desk_off": [],
 "note": "rag-api and the chat service read it within 60 s"}
>> the router's three alert policies (terraform/desk_alerts.tf): make plan up DESK_ROUTER_ALERTS=true after the router has taken some turns; then keep DESK_ROUTER_ALERTS=true on every later plan
{"tenant": "globex",
 "sections": ["grc", "payroll", "people", "posh", "privacy"],
 "posh_units": ["head_office"],
 "posh_missing": [],
 "not_readers": ["queue grc: no member holds a role that reads it", "queue privacy: no member holds a role that reads it", "queue payroll: no member holds a role that reads it", "queue people: no member holds a role that reads it"],
 "action": "written"}
{"tenant": "globex",
 "desk_gate": "rules",
 "desk_max_parts": 1,
 "desk_route": "single",
 "desk_single": "statute",
 "desk_off": [],
 "note": "rag-api and the chat service read it within 60 s"}
```

### optional/demo_03_your_lane_the_classes_the_example_index_and_the_switches.py

Optional: turn the Google Chat door on. Plan with GCHAT_DOOR=true beside DESK_JOB=true and apply, deploy chat again so documind-gchat-sa may call it, then make deploy-gchat. Keep GCHAT_DOOR=true on every later make plan and make up. The Workspace part, the door's smoke and its rows need it.

**`step_01_optional_the_google_chat_door_and_its_brid(session)` — Your lane: the classes, the example index and the switches / Optional: the Google Chat door and its bridge**

The Google Chat door is a second front door onto the same POST /v1/desk. When a person messages the "HR Desk" app, Google Chat calls an HTTPS endpoint, and here that endpoint is documind-gchat, a Cloud Run service of its own: the bridge, services/gchat/. It asks the Desk on the person's behalf and posts the Desk's reply into the chat as a card. It makes no model call and calls no service but the chat service. Run this part if you will try step 4's part in Google Chat or step 7's smoke of the door; otherwise skip it, with those parts and step 8's read of the door's rows. The plan, with GCHAT_DOOR=true, adds the door's 11 resources: what terraform/gchat.tf declares, the documind-gchat Firestore database, the documind-gchat-work topic and its documind-gchat-push subscription, the documind-gchatpush-sa account and the Chat API, with their IAM bindings; and documind-gchat-sa, the account in terraform/desk.tf that the bridge runs as. Keep GCHAT_DOOR=true, beside DESK_JOB=true, on every later make plan and make up: without it the plan would delete the door, and make plan's guard would refuse it. The plan and apply are the Terraform part of make plan up GCHAT_DOOR=true, which the kit names as the step before make deploy-gchat (make up would also rebuild and redeploy every service). The chat deploy is the part of make up the door needs: it allows documind-gchat-sa, which exists now, to call documind-chat. make deploy-gchat refuses on a lane whose last apply had the door off; here it builds the bridge's image and deploys it with commands/gchat.sh. Two accounts may call the bridge: documind-gchatpush-sa, Pub/Sub's push identity, and documind-outsider-sa, which step 7's smoke sends to it. The script's last line allows a third, the Chat app's add-on agent, service-NUMBER@gcp-sa-gsui

Operation: bash — run in the operator shell, in the kit, only to turn the Google Chat door on (its Terraform with GCHAT_DOOR=true, chat again, then the bridge: its image, its service and who may call it; many minutes).

Expected shape, not a promised result:

```text
Plan: 11 to add, 0 to change, 0 to destroy.
PASS: no deletes/replacements or existing CI trust changes. Reviewed plan: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
Review the displayed changes, then run this command with 'apply' instead of 'plan'.
PASS: selected plan, confirmed inputs, backend/workspace and state agree: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
...
Apply complete! Resources: 11 added, 0 changed, 0 destroyed.
>> commands/lesson-12.8.sh (DEPLOY block)
...
>> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/gchat:COMMIT from services/gchat
...
>> commands/gchat.sh (DEPLOY block)
...
>> the Chat app's add-on agent does not exist yet: configure the app (Google Chat API, Configuration), then run make deploy-gchat again
```

### demo_04_the_desk_page_and_the_hr_desk_app_in_google_chat.py

Do it: the questions, and the page

**`step_01_the_questions_and_the_page(session)` — The Desk page, and the HR Desk app in Google Chat / Do it: the questions, and the page**

Do it: the questions, and the page

Operation: bash — run in the operator shell, in the kit (the three route-set questions to paste, and the page's address).

Expected shape, not a promised result:

```text
lk-06: What is the notice period for a confirmed E3?
lk-17: At what rate is gratuity paid for each completed year of service?
lk-10: What is the total payable on invoice INV-2026-0412?
https://documind-ui-NUMBER.asia-south1.run.app   <- open it signed in as you@example.com, then choose Desk
```

### optional/demo_04_the_desk_page_and_the_hr_desk_app_in_google_chat.py

Optional, and only with the door on, a Business or Enterprise Google Workspace account and a Chat app you configured in the Google Cloud console: deploy the Google Chat bridge again so it admits the app's add-on agent, put your Workspace address on acme's roster, switch desk_gchat on for acme, and print the two questions to send the HR Desk app. Without Workspace, skip it: the page's expected conversation shows what it does, and make smoke-gchat proves the door's refusals with the door on.

**`step_01_optional_with_google_workspace_the_hr_desk(session)` — The Desk page, and the HR Desk app in Google Chat / Optional, with Google Workspace: the HR Desk app in Google Chat**

Configure the app. In the console, on your lane's project, open the Google Chat API's Configuration page. The kit expects: Then run the cell as the operator. It deploys the bridge again, so that its last line now allows the add-on agent. It puts your Workspace address on acme's roster, where with no roles document it holds employee. Then it turns the door on for acme. make desk refuses DESK_GCHAT=on while the company's gate is off, and unless its routed Desk is on or single. For a company whose data_region is in, it also needs CONFIRM_RESIDENCY=1, because the Desk's answers and their quotes then sit in the company's Google Chat. acme's gate has run its rules since lesson 5.6 and its router is on since step 3, and its data_region is any. The chat service reads the switch within 60 seconds.

Operation: bash — run in the operator shell, in the kit, only with Google Workspace and once the app is configured (the bridge again, your address on acme's roster, the door on for acme, two questions to paste).

Manual action: Only with a Business or Enterprise Google Workspace account. First configure the Chat app in the Google Cloud console, on your lane's project (Google Chat API, Configuration), as the page's step 4 lists: the name HR Desk, the add-on model, the HTTP endpoint URL https://documind-gchat-NUMBER.REGION.run.app with no trailing slash, and the app available to your Workspace address. Set WS in this cell to that address. Type done to deploy the bridge again, roster the address on acme and switch the door on; then, in Google Chat, send HR Desk the lk-06 question and the POSH line it prints.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
>> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/gchat:COMMIT from services/gchat
...
>> commands/gchat.sh (DEPLOY block)
...
employee@example.com is on acme
...
acme: data_region=any
zeta: data_region=any
globex: data_region=in
{"tenant": "acme",
 "desk_gate": "rules",
 "desk_max_parts": 1,
 "desk_route": "on",
 "desk_single": null,
 "desk_off": [],
 "desk_gchat": "on",
 "note": "rag-api and the chat service read it within 60 s"}
lk-06: What is the notice period for a confirmed E3?
POSH:  My manager keeps making sexual comments about my body. What can I do?
```

### demo_05_classes_desks_the_rules_first_and_the_google_chat_door_in_the_code.py

No lane and no cost: the cell imports the router and runs decide() with no models, as an acme employee, on the smoke's disclosure, four questions with identifiers, and one with none.

**`step_01_the_rules_on_your_machine(session)` — Classes, desks, the rules first and the Google Chat door, in the code / Do it: the rules on your machine**

No lane and no cost: the cell imports the router and runs decide() with no models, as an acme employee, on the smoke's disclosure, four questions with identifiers, and one with none.

Operation: bash — run in the operator shell, in the kit (decide() with no models: the rules alone; no lane, no cost).

Manual action: Wait five minutes after make desk switched acme's router on: the chat service reads the switches within 60 s and the example index within 5 minutes. Then open the deployed UI in a new tab, so the Desk starts a new conversation, sign in as yourself and choose Desk. Under Ask the Desk, ask What is the notice period? first, and if the reply asks which desk you mean, press the handbook's button. Ask the lk-06 question the previous section printed: one handbook answer with its citations. Ask the lk-17 question: a statute answer with a line for each Act it cites. Ask the lk-10 question: it is turned away at once, with a Raise a case button. Type done to run the router's rules on your machine.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
gate posh  anchors []             near True  -> case         rule     
  gate None  anchors ['out_of_scope'] near False -> out_of_scope anchor   
  gate None  anchors ['handbook']   near False -> handbook     anchor   
  gate None  anchors ['statute']    near False -> statute      anchor   
  gate None  anchors ['statute']    near True  -> fallback     fallback error:RuntimeError
  gate None  anchors []             near False -> fallback     fallback error:RuntimeError
  K 7 ACCEPT_VOTES 5 CASE_VOTES 3 TAU_OOS 0.7 prompt 2026-10-01.1
```

### demo_06_two_signals_and_one_arbiter_in_the_code.py

No lane and no cost: evals/route_eval.py --local runs decide() in process on every scored dev row, with a scripted classifier and offline embeddings. For each row, it takes the row's own group out of the vote first, so a question never finds itself. make desk-check is the proof that the Desk's code holds, with no lane and no cost. It checks that the route set is the one evals/build_routes.py builds and that every row is sound, runs the self-tests and unit tests of the eval and the probe, runs the router on the dev rows as the cell above did, checks that the threshold sweep counts right, and checks that every calculator rule says what its line of the corpus says. Then it runs the chat service's tests for the case queue, the router and the desk graph, which need the chat image's libraries: the first run makes ~/graph-venv and installs services/chat/requirements.txt into it, which takes a few minutes. Every line must pass; a failing one stops the run.

**`step_01_the_router_on_every_dev_row_on_your_machin(session)` — Two signals and one arbiter, in the code / Do it: the router on every dev row, on your machine**

No lane and no cost: evals/route_eval.py --local runs decide() in process on every scored dev row, with a scripted classifier and offline embeddings. For each row, it takes the row's own group out of the vote first, so a question never finds itself.

Operation: bash — run in the operator shell, in the kit (the router on every dev row with a scripted classifier; no lane, no cost).

Expected shape, not a promised result:

```text
local: the classifier is scripted, so this measures the cascade, not a model
  187 rows scored; 20 left out (the groups of the prompt's examples); index of 198 dev rows
arm B (the routed Desk)
split dev
  top-1 route accuracy          186/187 = 99.5% [97.0%, 99.9%]
    recall handbook             43/44 = 97.7% [88.2%, 99.6%]
    recall statute              129/129 = 100.0% [97.1%, 100.0%]
    recall case                 0/0 (no rows)
    recall clarify              0/0 (no rows)
    recall out_of_scope         14/14 = 100.0% [78.5%, 100.0%]
  confusion (rows: expected; columns: predicted)
                       handbook      statute         case      clarify out_of_scope        other
    handbook                 43            0            0            1            0            0
    statute                   0          129            0            0            0            0
    case                      0            0            0            0            0            0
    clarify                   0            0            0            0            0            0
    out_of_scope              0            0            0            0           14            0
...
  route accuracy, en            186/187 = 99.5% [97.0%, 99.9%]
  escalation recall, pooled     0/0 (no rows)
  authority_rate                not measured: the run carries no citations (a /v1/route run)
  correct_rate                  not measured: the run carries no answer text (a /v1/route run)
  methods: anchor 52, arbiter 48, model 78, single 9
  acceptance rules: A 77, B 1, F 48
  accepted without L2           139/139 = 100.0% [97.3%, 100.0%]
  sent to L2                    48/187 = 25.7% [19.9%, 32.4%]
  router cost                   Rs 3.8461 in all, Rs 0.02057 a turn
the dev gates hold
```

**`step_02_the_desk_s_offline_check(session)` — Two signals and one arbiter, in the code / Do it: the Desk's offline check**

make desk-check is the proof that the Desk's code holds, with no lane and no cost. It checks that the route set is the one evals/build_routes.py builds and that every row is sound, runs the self-tests and unit tests of the eval and the probe, runs the router on the dev rows as the cell above did, checks that the threshold sweep counts right, and checks that every calculator rule says what its line of the corpus says. Then it runs the chat service's tests for the case queue, the router and the desk graph, which need the chat image's libraries: the first run makes ~/graph-venv and installs services/chat/requirements.txt into it, which takes a few minutes. Every line must pass; a failing one stops the run.

Operation: bash — run in the operator shell, in the kit (the Desk's offline check: no lane, no cost; the first run installs ~/graph-venv).

Expected shape, not a promised result:

```text
routes.jsonl: 207 derived rows (golden 65, paraphrases 42, SFT rewrites 100), 0 hand-written; checked, all 207 valid
evals/routes.jsonl: 207 rows
  route            dev  test
  handbook          51     0
  statute          138     0
  case               0     0
  clarify            0     0
  out_of_scope      18     0
  total            207     0
  Wilson: 20 of 20 -> 83.9%, 73 of 73 -> 95.0%, 75 of 75 -> 95.1%, 100 of 100 -> 96.3%
  kNN: no dev row retrieves its own id, group or text (leave-one-group-out over 207 dev rows)
no cross-split pair
route_probe selftest: the four facts read correctly from canned yes, partial, no and error responses; 5 calls per probe
----------------------------------------------------------------------
Ran N tests in N.NNNs

OK
local: the classifier is scripted, so this measures the cascade, not a model
...
the dev gates hold
route_threshold selftest: accepted accuracy, L1 errors to L2 and L2 share count right on hand-made signals; 28 candidate pairs; no recommendation when none meets the targets
ok    accrual: acme/hr_policy_2026.md:19 says it
ok    carry_forward: acme/hr_policy_2026.md:19-20 says it
...
every rule says what its corpus line says, and the figures hold
Ran N tests in N.NNNs

OK
```

### demo_07_v1_route_and_v1_desk_over_rest.py

Five questions to /v1/route as evalacme: the smoke's disclosure, an invoice, a clause code, a named Act, and lk-06 with no identifier. Then lk-06 again, as documind-ui-sa. lk-06 and lk-17 to /v1/desk, each in its own session. For each section, the cell prints the title, the objects cited, whether the answer holds the route set's expected words, and the in-force lines. lk-06 as the leaver; globex's DPDP question as evalglobex; "What is the notice period?" as evalacme. jn-03 asks for a figure: "I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?" When L1 marks a question needs_calculation, the handbook desk runs in agent mode. A small agent searches the handbook's passages, and a calculator from shared/desk_calc.py does the arithmetic. The calculator takes the balance only from the person's message and the cap only from clause LV-07 of a passage this turn read; any other number is refused, and the agent is told why. smoke/smoke_desk.py checks the routed Desk in one run, as the eval accounts, then runs 5.6's case-queue smoke. Its questions are the route set's own rows, read by id, and each run uses fresh sessions.

**`step_01_decisions(session)` — /v1/route and /v1/desk, over REST / Do it: decisions**

Five questions to /v1/route as evalacme: the smoke's disclosure, an invoice, a clause code, a named Act, and lk-06 with no identifier. Then lk-06 again, as documind-ui-sa.

Operation: bash — run in the operator shell, in the kit (five decisions from POST /v1/route as evalacme, then the same call as ui-sa).

Expected shape, not a promised result:

```text
POSH   200 route case          method rule    anchors []                 model_calls 0  Rs 0.0
  lk-10  200 route out_of_scope  method anchor  anchors ['out_of_scope']   model_calls 0  Rs 0.0
  NP-03  200 route handbook      method anchor  anchors ['handbook']       model_calls 0  Rs 0.0
  lk-18  200 route statute       method anchor  anchors ['statute']        model_calls 0  Rs 0.0
  lk-06  200 route handbook      method model   anchors []                 model_calls 1  Rs N.NNNN
         L1 handbook; the vote handbook, N of 7, nearest cosine N.NNNN; accepted by rule A
  as ui-sa 403 POST /v1/route is for the Desk's eval accounts (desk_eval)
```

**`step_02_answers(session)` — /v1/route and /v1/desk, over REST / Do it: answers**

lk-06 and lk-17 to /v1/desk, each in its own session. For each section, the cell prints the title, the objects cited, whether the answer holds the route set's expected words, and the in-force lines.

Operation: bash — run in the operator shell, in the kit (two answers from POST /v1/desk as evalacme).

Expected shape, not a promised result:

```text
lk-06 200 route handbook method model outcome answer  model_calls 1  retrieve_calls 1  Rs N.NNNN
    From the company handbook: N citations from acme/hr_policy_2026.md
    the answer says ['60']: True
    chips []
  lk-17 200 route statute method model outcome answer  model_calls 1  retrieve_calls 1  Rs N.NNNN
    What the law says: N citations from acme/code_on_social_security_2020.pdf, acme/industrial_relations_code_2020.pdf, acme/payment_of_gratuity_act_1972.pdf
    the answer says ['fifteen days']: True
    | Payment of Gratuity Act, 1972: the Code on Social Security, 2020, s.164(1) repeals it from the day the Code on Social Security, 2020 comes into force (the date is not shown here until a person has checked it against the Gazette); shown for comparison.
    | Code on Social Security, 2020: it comes into force on such date as the Central Government may, by notification, appoint, and different dates may be appointed for different provisions (s.1(3)); the date is not shown here until a person has checked it against the Gazette.
    | Industrial Relations Code, 2020: it comes into force on such date as the Central Government may, by notification, appoint, and different dates may be appointed for different provisions (s.1(3)); the date is not shown here until a person has checked it against the Gazette.
    | Legal information, not advice.
    chips []
```

**`step_03_the_leaver_the_single_desk_and_a_question(session)` — /v1/route and /v1/desk, over REST / Do it: the leaver, the single desk, and a question back**

lk-06 as the leaver; globex's DPDP question as evalglobex; "What is the notice period?" as evalacme.

Operation: bash — run in the operator shell, in the kit (the leaver, globex in single mode, and a question with no desk in it).

Expected shape, not a promised result:

```text
leaver  200 route denied outcome denied  retrieve_calls 0  model_calls 1  chips ['case']
          Your roles in this company do not include asking the company handbook, so DocuMind did not search for this. You can raise a case for a person.
  globex  200 tenant globex mode single route statute method single  model_calls 0  outcome answer
          cites ['globex/dpdp_act_2023.pdf']
  clarify 200 route clarify method arbiter: Should I answer this from the company handbook or from the law?
          chips ['Ask what the company handbook says', 'Ask what the law says']
```

**`step_04_a_figure_worked_out_in_code(session)` — /v1/route and /v1/desk, over REST / Do it: a figure, worked out in code**

jn-03 asks for a figure: "I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?" When L1 marks a question needs_calculation, the handbook desk runs in agent mode. A small agent searches the handbook's passages, and a calculator from shared/desk_calc.py does the arithmetic. The calculator takes the balance only from the person's message and the cap only from clause LV-07 of a passage this turn read; any other number is refused, and the agent is told why.

Operation: bash — run in the operator shell, in the kit (jn-03, a figure, to POST /v1/desk as evalacme: the handbook desk in agent mode).

Expected shape, not a promised result:

```text
jn-03 200 route handbook method model mode agent  tool_calls ['retrieve', 'encashable_days']
        retrieve_calls 1  model_calls N  Rs N.NNNN
        the answer says ['45', '60']: True

Of your 50 days of earned leave, 45 are encashed on exit, at basic pay [1]. A confirmed employee at grade E3 or above serves a notice period of 60 days [2].

Worked out in code:
- Earned leave encashed on exit (LV-07): min(50, 45) = 45 days. The balance from your message; the cap from LV-07 [1]. Condition: LV-07 bars encashment during probation: this figure holds only once probation is over.
```

**`step_05_the_live_smoke(session)` — /v1/route and /v1/desk, over REST / Do it: the live smoke**

smoke/smoke_desk.py checks the routed Desk in one run, as the eval accounts, then runs 5.6's case-queue smoke. Its questions are the route set's own rows, read by id, and each run uses fresh sessions.

Operation: bash — run in the operator shell, in the kit (the routed Desk's live smoke, then the case queue's).

Expected shape, not a promised result:

```text
DocuMind Desk - the routed Desk, live
  chat: https://documind-chat-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] handbook  N citations, method model, Rs N.NNNN
  [PASS] statute  in force: 'Code on Social Security, 2020: it comes into force on such date as the'
  [PASS] posh  no model call, no case written, offices ['hyderabad', 'pune']
  [PASS] out_of_scope  method anchor: "This is outside what DocuMind's desks answer: it is not in t"
  [PASS] leaver denied  zero retrieve calls, a case offered
  [PASS] globex single  outcome answer, model calls 0
  [PASS] /v1/route  status=200 {'email': 'documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com', 'tenant': 'acme', 'mode': 'on', 'arm': 'B', 'route': 'handbook', 'desk': None, 'me
  [PASS] /v1/route refuses a non-eval caller  status=403 {'detail': "POST /v1/route is for the Desk's eval accounts (desk_eval)"}
  --------------------------------------------------------
  8 passed, 0 failed


  DocuMind Desk - the case queue, live
  chat: https://documind-chat-NUMBER.asia-south1.run.app
  api:  https://documind-api-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] chat door  brain=desk_gate model=none Rs 0  'It sounds as if this may be about sexual harassment at work.'
  [PASS] api door (stream)  model=none cost_usd=0 backend=desk_gate
  [PASS] draft  queue=grc expires=YYYY-MM-DDTHH:MM:SS+00:00
  [PASS] confirm, twice  one case, open, due YYYY-MM-DDTHH:MM:SS+00:00
  [PASS] inbox  status=200 roles=['grc_member'] in inbox=True
  [PASS] status acknowledged  status=200 {'case_id': '7bdc9df68d7e04c6e9e9451bd1553f08', 'tenant': 'acme', 'requester': 'documind-evalacme-sa@documind-ai-YOUR-ID
  [PASS] status closed  status=200 {'case_id': '7bdc9df68d7e04c6e9e9451bd1553f08', 'tenant': 'acme', 'requester': 'documind-evalacme-sa@documind-ai-YOUR-ID
  [PASS] another tenant  status=404 {'detail': 'no such case'}
  [PASS] posh, twice  one case, no text, Local Committee lc.hyderabad@example.com
  [PASS] posh withdrawn  status=200 {'case_id': '630d05ead95931295611d1fef5cc4efd', 'tenant': 'acme', 'requester': 'documind-evalacme-sa
  [PASS] outsider refused  status=403 {'detail': 'not a member of any tenant'}
  --------------------------------------------------------
  11 passed, 0 failed
```

### optional/demo_07_v1_route_and_v1_desk_over_rest.py

Optional, only with the door on, and no Workspace needed: make smoke-gchat's four refusals and the door's latest rows. It refuses on a lane whose last apply had the door off.

**`step_01_optional_the_google_chat_door_s_refusals(session)` — /v1/route and /v1/desk, over REST / Optional: the Google Chat door's refusals**

This needs the door on your lane, step 3's optional part, and no Google Workspace. On a lane whose last apply had the door off, make smoke-gchat refuses and says so. smoke/smoke_gchat.py sends four requests that must be refused. Steps 1 and 2 go to the bridge as documind-outsider-sa: a Chat-shaped event to / and a push envelope to /work. The outsider is one of the bridge's invokers, so Cloud Run lets it in, and the 401, "this endpoint answers Google Chat and its own push only", comes from the bridge's own code. Steps 3 and 4 go to the chat service's POST /v1/desk as documind-evalacme-sa and as ui-sa, each naming a person in X-DocuMind-Principal, and the Desk's rule 1 refuses both: "not an allowed delegate". Then the smoke prints the latest rows of each kind from the last hour. The kit's comments call steps 3 and 4 the alert's own test: each writes a desk_delegation_refused row, which "Desk: a delegation was refused" counts, so expect it to fire and notify whatever channels your lane's alerts use. That is on purpose. No step shows the door accepting a call, because nobody may mint a token as documind-gchat-sa, by design. A person in Google Chat, as in step 4, is that proof.

Operation: bash — run in the operator shell, in the kit, only with the Google Chat door on (its refusals; no Google Workspace needed).

Expected shape, not a promised result:

```text
DocuMind Desk - the Google Chat door's refusals, live
  bridge: https://documind-gchat-NUMBER.asia-south1.run.app
  chat:   https://documind-chat-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] 1. POST / as the outsider  -> 401 'this endpoint answers Google Chat and its own push only'
  [PASS] 2. POST /work as the outsider  -> 401 'this endpoint answers Google Chat and its own push only'
  [PASS] 3. POST /v1/desk as documind-evalacme-sa, naming a person  -> 403 'not an allowed delegate'
  [PASS] 4. POST /v1/desk as documind-ui-sa, naming a person  -> 403 'not an allowed delegate'

  the latest rows (Cloud Logging, the last hour; a row can take a minute to arrive):
    jsonPayload.event="gchat"
      "(none)"
    jsonPayload.event="gchat_answer"
      "(none)"
    jsonPayload.event="gchat_verify_failed"
      {"event": "gchat_verify_failed", "path": "/work", "reason": "wrong_caller", ...}
      {"event": "gchat_verify_failed", "path": "/", "reason": "wrong_caller", ...}
    jsonPayload.event="desk" AND jsonPayload.via="gchat"
      "(none)"
    jsonPayload.event="desk_delegation_refused"
      {"event": "desk_delegation_refused", "caller": "documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com", "reason": "not an allowed delegate", "path": "/v1/desk"}
      {"event": "desk_delegation_refused", "caller": "documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com", "reason": "not an allowed delegate", "path": "/v1/desk"}
    jsonPayload.event="desk_delegation_denied"
      "(none)"

  4 passed, 0 failed
```

### demo_08_the_shadow_the_rows_and_the_log.py

zeta's router in shadow beside ordinary chat turns; a chunk, its registry entry and an exemplar in Firestore; every row the router logged; the Google Chat door's rows and claims; the Desk's day in BigQuery; then zeta on. Shadow first. A company that is not ready to route can let the router watch. With desk_route at shadow, every /v1/chat turn for that company is answered by its brain as before, and the router decides the same question beside it, with its own Meter, and logs a desk_shadow row. It answers nothing and keeps nothing. Shadow needs desk_gate not off, so the door answers every disclosure before the router could see it; zeta already has the gate's rules, because nothing has switched them off. zeta goes on to desk_route on later in this step, and the routed Desk waits for a complete POSH queue. So zeta gets its queues, with evalzeta as head office's committee, then the role, then the shadow. Three of zeta's route-set questions to /v1/chat as evalzeta, with the direct brain: a travel cap from zeta's handbook, the Code on Wages, and zeta's own contract. acme's chunk for NP-03, the handbook's registry entry, the exemplar for lk-06, and the three companies' switches, read with the Firestore client. Every desk and desk_shadow row the chat service logged since step 3. Since step 3's apply, the log sink copies the chat service's desk rows into BigQuery. make desk-views checks terraform/sql/desk_daily.sql with a dry run, then creates the view documind_observability.desk_daily: one row per India day, company, desk and kind of caller, with the turns, their outcomes, the escalations, how each turn was decided, the arbiter's share, the chip turns, the rupees and the latencies. No column names a person, a session or a question. The bq query then reads today's rows. Run it a few minutes after step 7, since the sink takes a little while to deliver rows and BigQuery types the table's columns from the rows it has seen. This is a preview; lesson 11.5 explains the sink and the views. The shadow rows are what a company reads before it switches. On the stand-in they agree with the route set's labels. Read yours first, and switch zeta on when they do.

**`step_01_the_shadow_the_rows_and_the_log(session)` — The shadow, the rows and the log / The shadow, the rows and the log**

zeta's router in shadow beside ordinary chat turns; a chunk, its registry entry and an exemplar in Firestore; every row the router logged; the Google Chat door's rows and claims; the Desk's day in BigQuery; then zeta on. Shadow first. A company that is not ready to route can let the router watch. With desk_route at shadow, every /v1/chat turn for that company is answered by its brain as before, and the router decides the same question beside it, with its own Meter, and logs a desk_shadow row. It answers nothing and keeps nothing. Shadow needs desk_gate not off, so the door answers every disclosure before the router could see it; zeta already has the gate's rules, because nothing has switched them off. zeta goes on to desk_route on later in this step, and the routed Desk waits for a complete POSH queue. So zeta gets its queues, with evalzeta as head office's committee, then the role, then the shadow.

Operation: bash — run in the operator shell, in the kit (zeta's queues with its eval account as the committee, then the router in shadow).

Expected shape, not a promised result:

```text
{"tenant": "zeta",
 "sections": ["grc", "payroll", "people", "posh", "privacy"],
 "posh_units": ["head_office"],
 "posh_missing": [],
 "not_readers": ["ic head_office: documind-evalzeta-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com", "queue grc: no member holds a role that reads it", "queue privacy: no member holds a role that reads it", "queue payroll: no member holds a role that reads it", "queue people: no member holds a role that reads it"],
 "action": "written"}
{"tenant": "zeta",
 "email": "documind-evalzeta-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
 "before": ["employee"],
 "after": ["desk_eval", "employee", "ic_member:head_office"],
 "granted": ["desk_eval", "ic_member:head_office"],
 "revoked": []}
{"tenant": "zeta",
 "desk_gate": "rules",
 "desk_max_parts": 1,
 "desk_route": "shadow",
 "desk_single": null,
 "desk_off": [],
 "note": "rag-api and the chat service read it within 60 s"}
>> the router's three alert policies (terraform/desk_alerts.tf): make plan up DESK_ROUTER_ALERTS=true after the router has taken some turns; then keep DESK_ROUTER_ALERTS=true on every later plan
```

**`step_02_three_ordinary_chat_turns(session)` — The shadow, the rows and the log / Do it: three ordinary chat turns**

Three of zeta's route-set questions to /v1/chat as evalzeta, with the direct brain: a travel cap from zeta's handbook, the Code on Wages, and zeta's own contract.

Operation: bash — run in the operator shell, in the kit (three ordinary chat turns on zeta, which the router decides beside).

Expected shape, not a promised result:

```text
iso-01 200 brain direct  citations N  model_calls 0  the answer says ['25,000']: True
  lk-21  200 brain direct  citations N  model_calls 0  the answer says ['seventh day']: True
  lk-13  200 brain direct  citations N  model_calls 0
```

**`step_03_the_rows_in_firestore(session)` — The shadow, the rows and the log / Do it: the rows in Firestore**

acme's chunk for NP-03, the handbook's registry entry, the exemplar for lk-06, and the three companies' switches, read with the Firestore client.

Operation: bash — run in the operator shell, in the kit (a chunk, its registry entry, an exemplar and the three tenants' switches, from Firestore).

Expected shape, not a promised result:

```text
chunks/acme:497809ffbaa603c49577add351033f4374ad1aefa3394f761be0c9df5e3f3173#1
    doc_type policy  kind text  current True  acme/hr_policy_2026.md
  tenants/acme/doc_types/acme~hr_policy_2026.md: policy, pin acme_497809ffbaa6..., set by you@example.com, source manifest
    the pin is the chunk's doc_key: True
  tenants/acme/desk_exemplars/lk-06: route handbook, group lk-06, 768 dimensions, text-embedding-005, index d15e143dd357
  tenant_settings/acme: desk_gate rules, desk_route on, desk_single None, data_region any
  tenant_settings/zeta: desk_gate rules, desk_route shadow, desk_single None, data_region any
  tenant_settings/globex: desk_gate rules, desk_route single, desk_single statute, data_region in
```

**`step_04_the_log(session)` — The shadow, the rows and the log / Do it: the log**

Every desk and desk_shadow row the chat service logged since step 3.

Operation: bash — run in the operator shell, in the kit (every desk and desk_shadow row since step 3; reads only).

Expected shape, not a promised result:

```text
desk        desk  acme   you                       clarify      arbiter F    calls 2  clarify
  desk        desk  acme   you                       handbook     user    None calls 0  answer
  desk        desk  acme   you                       handbook     model   A    calls 1  answer
  desk        desk  acme   you                       statute      model   A    calls 1  answer
  desk        desk  acme   you                       out_of_scope anchor  None calls 0  oos
  desk        route acme   None                      case         rule    None calls 0  
  desk        route acme   documind-evalacme-sa      out_of_scope anchor  None calls 0  
  desk        route acme   documind-evalacme-sa      handbook     anchor  None calls 0  
  desk        route acme   documind-evalacme-sa      statute      anchor  None calls 0  
  desk        route acme   documind-evalacme-sa      handbook     model   A    calls 1  
  desk        desk  acme   documind-evalacme-sa      handbook     model   A    calls 1  answer
  desk        desk  acme   documind-evalacme-sa      statute      model   A    calls 1  answer
  desk        desk  acme   documind-evalleaver-sa    denied       model   A    calls 1  denied
  desk        desk  globex documind-evalglobex-sa    statute      single  None calls 0  answer
  desk        desk  acme   documind-evalacme-sa      clarify      arbiter F    calls 2  clarify
  desk        desk  acme   documind-evalacme-sa      handbook     model   A    calls 4  answer
  desk        desk  acme   documind-evalacme-sa      handbook     model   A    calls 1  answer
  desk        desk  acme   documind-evalacme-sa      statute      model   A    calls 1  answer
  desk        desk  acme   None                      case         rule    None calls 0  case
  desk        desk  acme   documind-evalacme-sa      out_of_scope anchor  None calls 0  oos
  desk        desk  acme   documind-evalleaver-sa    denied       model   A    calls 1  denied
  desk        desk  globex documind-evalglobex-sa    statute      single  None calls 0  answer
  desk        route acme   documind-evalacme-sa      handbook     model   A    calls 1  
  desk_shadow chat  zeta   documind-evalzeta-sa      handbook     model   A    calls 1  
  desk_shadow chat  zeta   documind-evalzeta-sa      statute      anchor  None calls 0  
  desk_shadow chat  zeta   documind-evalzeta-sa      out_of_scope model   A    calls 1
```

**`step_05_the_desk_s_day_in_bigquery(session)` — The shadow, the rows and the log / Do it: the Desk's day in BigQuery**

Since step 3's apply, the log sink copies the chat service's desk rows into BigQuery. make desk-views checks terraform/sql/desk_daily.sql with a dry run, then creates the view documind_observability.desk_daily: one row per India day, company, desk and kind of caller, with the turns, their outcomes, the escalations, how each turn was decided, the arbiter's share, the chip turns, the rupees and the latencies. No column names a person, a session or a question. The bq query then reads today's rows. Run it a few minutes after step 7, since the sink takes a little while to deliver rows and BigQuery types the table's columns from the rows it has seen. This is a preview; lesson 11.5 explains the sink and the views.

Operation: bash — run in the operator shell, in the kit (the desk_daily view applied, then today's rows read with bq).

Expected shape, not a promised result:

```text
bq --project_id=documind-ai-YOUR-ID query --use_legacy_sql=false --dry_run < terraform/sql/desk_daily.sql
...
bq --project_id=documind-ai-YOUR-ID query --use_legacy_sql=false < terraform/sql/desk_daily.sql
...
>> the router's three alert policies (terraform/desk_alerts.tf) exist only on a lane planned with DESK_ROUTER_ALERTS=true: now that the router has run, make plan up DESK_ROUTER_ALERTS=true, and keep it on every later plan
+--------+--------------+------------------+-------+----------+-----------+-------------+-------+----------+
| tenant |     desk     |     callers      | turns | answered | clarified | escalations | to_l2 | cost_inr |
+--------+--------------+------------------+-------+----------+-----------+-------------+-------+----------+
| acme   | case         | people           |     N |        N |         N |           N |     N |     N.NN |
| acme   | clarify      | people           |     N |        N |         N |           N |     N |     N.NN |
| acme   | clarify      | service_accounts |     N |        N |         N |           N |     N |     N.NN |
| acme   | handbook     | people           |     N |        N |         N |           N |     N |     N.NN |
| acme   | handbook     | service_accounts |     N |        N |         N |           N |     N |     N.NN |
| acme   | out_of_scope | people           |     N |        N |         N |           N |     N |     N.NN |
| acme   | out_of_scope | service_accounts |     N |        N |         N |           N |     N |     N.NN |
| acme   | statute      | people           |     N |        N |         N |           N |     N |     N.NN |
| acme   | statute      | service_accounts |     N |        N |         N |           N |     N |     N.NN |
| globex | statute      | service_accounts |     N |        N |         N |           N |     N |     N.NN |
+--------+--------------+------------------+-------+----------+-----------+-------------+-------+----------+
```

**`step_06_zeta_on(session)` — The shadow, the rows and the log / Do it: zeta on**

The shadow rows are what a company reads before it switches. On the stand-in they agree with the route set's labels. Read yours first, and switch zeta on when they do.

Operation: bash — run in the operator shell, in the kit (zeta from shadow to on).

Expected shape, not a promised result:

```text
{"tenant": "zeta",
 "desk_gate": "rules",
 "desk_max_parts": 1,
 "desk_route": "on",
 "desk_single": null,
 "desk_off": [],
 "note": "rag-api and the chat service read it within 60 s"}
>> the router's three alert policies (terraform/desk_alerts.tf): make plan up DESK_ROUTER_ALERTS=true after the router has taken some turns; then keep DESK_ROUTER_ALERTS=true on every later plan
```

### optional/demo_08_the_shadow_the_rows_and_the_log.py

Optional, only with the door on: the desk rows that came through the Google Chat door, then the bridge's claims in its own Firestore database; reads only.

**`step_01_optional_the_google_chat_door_s_rows(session)` — The shadow, the rows and the log / Optional: the Google Chat door's rows**

This needs the door on your lane, step 3's optional part: without it there is no documind-gchat database to read. Two direct reads of what step 4's conversation left, if you had it. The desk rows with via "gchat" are the Desk's own rows for the turns the bridge asked for. The handbook turn names you and the delegate; the disclosure's names nobody, as on the Desk page. The bridge's claims are in its own Firestore database, documind-gchat, never the default one where the rosters and roles live. A claim stops a message that Chat delivers twice, or that Pub/Sub pushes twice, from being answered twice. Its id is a hash of the message's name, it holds no text and no email, and it expires 24 hours after it was made. A TTL policy then deletes it; how soon after is not confirmed.

Operation: bash — run in the operator shell, in the kit, only with the Google Chat door on (the desk rows that came through the Google Chat door since step 3, then the bridge's claims; reads only).

Expected shape, not a promised result:

```text
desk rows through the Google Chat door: 2
    via gchat  delegate gchat  user employee@example.com  route handbook  case_type None  outcome answer
    via gchat  delegate None  user None  route case  case_type sensitive  outcome case
  claims in documind-gchat's gchat_events: 1
    d4f2fa564e03b68e...  fields ['attempts', 'created_at', 'expire_at', 'kind', 'leased_at', 'state']
      kind message  state answered  attempts 1  an email in it: False  expire_at - created_at: 1 day, 0:00:00
```

### demo_10_verify_it_yourself_the_eval_and_the_checklist.py

make route-eval posts every scored dev row to /v1/route as the row's own eval account: 187 rows, with the 20 rows of the prompt's example groups left out, since the prompt has seen them. Each handbook, statute and denial row, 173 of them, goes to /v1/desk too, for its answer and citations. The report gives each rate with its interval, the confusion matrix, whether answers cite only the desk's classes and the caller's company, the router's cost, and the p50 and p95 of the routing and of the answers. The dev gates are a route accuracy of 95% or more, each desk's recall at 90% or more, and every escalation row escalated; a FAIL line names a gate missed. If the Desk answers 429, more than 120 routes a minute from one account, the eval waits the minute out and tries again, up to three times. Do it: the test split The chat service keeps the gate lesson 5.7 set: make smoke-chat PROJECT=documind-ai-YOUR-ID, the four brains and the outsider. The routed Desk sits beside /v1/chat, not in front of it, so every brain answers as before.

**`step_01_the_router_s_eval_dev_split(session)` — Verify it yourself: the eval and the checklist / Do it: the router's eval, dev split**

make route-eval posts every scored dev row to /v1/route as the row's own eval account: 187 rows, with the 20 rows of the prompt's example groups left out, since the prompt has seen them. Each handbook, statute and denial row, 173 of them, goes to /v1/desk too, for its answer and citations. The report gives each rate with its interval, the confusion matrix, whether answers cite only the desk's classes and the caller's company, the router's cost, and the p50 and p95 of the routing and of the answers. The dev gates are a route accuracy of 95% or more, each desk's recall at 90% or more, and every escalation row escalated; a FAIL line names a gate missed. If the Desk answers 429, more than 120 routes a minute from one account, the eval waits the minute out and tries again, up to three times.

Operation: bash — run in the operator shell, in the kit (every dev row through the deployed Desk, one call after another: 187 decisions and 173 paid answers; the report prints what the router cost).

Expected shape, not a promised result:

```text
live: https://documind-chat-NUMBER.asia-south1.run.app, arm B (the routed Desk), split dev: 187 rows scored, 20 left out (the groups of the prompt's examples)
arm B (the routed Desk)
split dev
  top-1 route accuracy          N/187 = NN.N% [NN.N%, NN.N%]
    recall handbook             N/44 = NN.N% [NN.N%, NN.N%]
    recall statute              N/129 = NN.N% [NN.N%, NN.N%]
    recall case                 0/0 (no rows)
    recall clarify              0/0 (no rows)
    recall out_of_scope         N/14 = NN.N% [NN.N%, NN.N%]
  confusion (rows: expected; columns: predicted)
                       handbook      statute         case      clarify out_of_scope        other
    handbook                  N            N            N            N            N            N
    statute                   N            N            N            N            N            N
    case                      0            0            0            0            0            0
    clarify                   0            0            0            0            0            0
    out_of_scope              N            N            N            N            N            N
    ...
  route accuracy, en            N/187 = NN.N% [NN.N%, NN.N%]
  escalation recall, pooled     0/0 (no rows)
  outcome accuracy              N/187 = NN.N% [NN.N%, NN.N%]
  authority_rate                N/173 = NN.N% [NN.N%, NN.N%]
    handbook                    N/44 = NN.N% [NN.N%, NN.N%]
    statute                     N/129 = NN.N% [NN.N%, NN.N%]
    no cross-tenant citation    N/173 = NN.N% [NN.N%, NN.N%]
  no citation where none is due N/14 = NN.N% [NN.N%, NN.N%]
  correct_rate (answer rows)    N/137 = NN.N% [NN.N%, NN.N%]
  no must_not_contain           N/16 = NN.N% [NN.N%, NN.N%]
  router cost                   Rs N.NNNN in all, Rs N.NNNNN a turn
  router_ms                     p50 N  p95 N  over 187 turns
  desk latency_ms               p50 N  p95 N  over 173 turns
```

**`step_02_the_test_split(session)` — Verify it yourself: the eval and the checklist / Do it: the test split**

Do it: the test split

Operation: bash — run in the operator shell, in the kit (the test split: it has no rows yet).

Expected shape, not a promised result:

```text
live: https://documind-chat-NUMBER.asia-south1.run.app, arm B (the routed Desk), split test: 0 rows scored, 0 left out (the groups of the prompt's examples)
arm B (the routed Desk)
split test
  top-1 route accuracy          0/0 (no rows)
    recall handbook             0/0 (no rows)
    recall statute              0/0 (no rows)
    recall case                 0/0 (no rows)
    recall clarify              0/0 (no rows)
    recall out_of_scope         0/0 (no rows)
  confusion (rows: expected; columns: predicted)
                       handbook      statute         case      clarify out_of_scope        other
    handbook                  0            0            0            0            0            0
    statute                   0            0            0            0            0            0
    case                      0            0            0            0            0            0
    clarify                   0            0            0            0            0            0
    out_of_scope              0            0            0            0            0            0
  escalation recall, pooled     0/0 (no rows)
  authority_rate                not measured: the run carries no citations (a /v1/route run)
  correct_rate                  not measured: the run carries no answer text (a /v1/route run)
  router cost                   Rs 0.0000 in all, Rs 0.00000 a turn
FAIL  route accuracy 0/0 (no rows) is under 95%
make: *** [mk/agents.mk:214: route-eval] Error 1
```

**`step_03_module_5_s_gate(session)` — Verify it yourself: the eval and the checklist / Do it: Module 5's gate**

The chat service keeps the gate lesson 5.7 set: make smoke-chat PROJECT=documind-ai-YOUR-ID, the four brains and the outsider. The routed Desk sits beside /v1/chat, not in front of it, so every brain answers as before.

Operation: bash — run in the operator shell, in the kit (Module 5's gate: four brains, one question, the outsider refused).

Expected shape, not a promised result:

```text
DocuMind chat - live smoke test
  target: https://documind-chat-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] health  profile=gcp default=langchain limits=12 calls, Rs 5.0, 100.0 s
  [PASS] brain direct  NNNN ms  tools=['retrieve']  citations=N  calls=0 Rs N.NNNN  '...'
  [PASS] brain langchain  NNNN ms  tools=['retrieve']  citations=N  calls=N Rs N.NNNN  '...'
  [PASS] brain langgraph  NNNN ms  tools=['retrieve']  citations=N  calls=N Rs N.NNNN  '...'
  [PASS] brain adk  NNNN ms  tools=['retrieve']  citations=N  calls=N Rs N.NNNN  '...'
  [PASS] outsider refused  status=403 not a member of any tenant
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_10.4_Desk_Router_WIX.html`. All 84 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `03242e524bd39dd3ceff5c2e0518c22d2e49a24c`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
