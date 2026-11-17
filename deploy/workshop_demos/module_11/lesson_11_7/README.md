# Lesson 11.7: Reproduce the agent failures production shows and no eval row does

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_registry_read_at_rs_0.py](demo_03_the_registry_read_at_rs_0.py) | The registry, read at Rs 0 |
| 4 | [demo_04_the_lines_the_two_drills_rest_on.py](demo_04_the_lines_the_two_drills_rest_on.py) | The lines the two drills rest on |
| 5 | [demo_05_every_offline_drill_on_a_stand_in_of_cloud_run.py](demo_05_every_offline_drill_on_a_stand_in_of_cloud_run.py) | Every offline drill, on a stand-in of Cloud Run |
| 6 | [demo_06_your_two_services_as_cloud_run_s_api_returns_them.py](demo_06_your_two_services_as_cloud_run_s_api_returns_them.py) | Your two services, as Cloud Run's API returns them |
| 7 | [demo_07_the_two_drills_on_your_lane.py](demo_07_the_two_drills_on_your_lane.py) | The two drills on your lane |
| 8 | [demo_08_the_detectors_what_your_lane_shows_now.py](demo_08_the_detectors_what_your_lane_shows_now.py) | The detectors: what your lane shows now |
| 9 | [demo_09_the_release_no_gate_judged_loud_against_silent_and_what_the_kit_does_not_do_yet.py](demo_09_the_release_no_gate_judged_loud_against_silent_and_what_the_kit_does_not_do_yet.py) | The release no gate judged, loud against silent, and what the kit does not do yet |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's drills change documind-chat alone, and the one answer that reads acme's rows is make smoke-chat's, which checks that each brain cites something, not which store it came from. Pin acme or not, as you prefer; if you set the pin, put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's drills change documind-chat alone, and the one answer that reads acme's rows is make smoke-chat's, which checks that each brain cites something, not which store it came from. Pin acme or not, as you prefer; if you set the pin, put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's drills change documind-chat alone, and the one answer that reads acme's rows is make smoke-chat's, which checks that each brain cites something, not which store it came from. Pin acme or not, as you prefer; if you set the pin, put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_registry_read_at_rs_0.py

Do it: the registry Do it: one entry, every field

**`step_01_the_registry(session)` — The registry, read at Rs 0 / Do it: the registry**

Do it: the registry

Operation: bash — run in the operator shell, in the kit (reads one file; no lane, no cost).

Expected shape, not a promised result:

```text
13 gotchas in ops/gotchas.json (workshop lesson 11.7). make gotchas ID=<id> shows one; make gotcha-drill runs every offline drill, Rs 0
id                              signal  drill          status   lessons            title
pinned-traffic                  silent  offline, live  open     5.5 6.7 11.3       A service pinned to one revision never serves a later change
deploy-drops-hotfix             silent  offline, live  open     0.3 2.5 5.5        A routine make deploy-services drops a setting made by hand
ungated-api-release             silent  offline        open     0.3 11.1 11.2      make deploy-services and make up put an ungated API revision live
switch-rides-into-candidate     silent  offline        open     2.5 4.4 11.2 11.6  A switch set on one candidate rides into the next
rollback-keeps-template         silent  offline        open     11.3               make rollback moves the traffic back, not the settings
tag-audience-401                loud    live           guarded  4.3 4.4 11.2       A token minted for the candidate's tag URL is refused on every row
looping-model-stopped           silent  offline, live  open     5.5 5.7            A looping model is stopped quietly, with HTTP 200
abandoned-call-bills            silent  offline        open     5.5 11.5           A search the turn abandoned still runs, and rag-api bills it
agent-spend-outside-the-month   silent  offline        open     5.5 11.5 11.6      The agents' own model calls are missing from the month's spend
vector-search-fallback          silent  live           open     2.4 11.4           Vector Search fails and Firestore answers, silently
poison-upload                   loud    live           open     1.5 11.5           A poison upload is quiet for an hour, then pages
ci-promote-loses-previous       silent  offline        open     11.1 11.3          After a CI promote, make rollback has nothing to return to
environment-without-reviewers   silent  live           open     11.1               A production environment nobody created lets promote run unapproved
```

**`step_02_one_entry_every_field(session)` — The registry, read at Rs 0 / Do it: one entry, every field**

Do it: one entry, every field

Operation: bash — run in the operator shell, in the kit (one entry, every field).

Expected shape, not a promised result:

```text
deploy-drops-hotfix: A routine make deploy-services drops a setting made by hand
  signal     silent
  status     open
  symptom    A setting put on a running service with gcloud run services update --update-env-vars (lesson 2.5's
             QUERY_REWRITE=on, a chat cap, a Change-it left in place) holds until the next routine make
             deploy-services. Each deploy script sets its service's whole environment with --set-env-vars, so a
             variable the script does not list is gone, and a switch the deploy does carry (ARMOR, ROUTING,
             GENERATOR_MODEL, ADMIN_EMAILS) goes back to the Makefile's default unless it is passed again. The service
             carries on with the default, without a word.
  no eval    The gate judged the revision that had the setting. After the deploy the default serves, the rows still
             pass, and the setting that made the difference is simply not there.
  drill      offline, Rs 0 (make gotcha-drill ID=deploy-drops-hotfix): A stand-in documind-chat:
             CHAT_MAX_MODEL_CALLS=8 set by hand, then make deploy-services SCRIPTS=commands/lesson-12.8.sh applied as
             that script's own --set-env-vars list, with CHAT_EXTRA_ENV empty as the Makefile leaves it; then the same
             deploy carrying the value in CHAT_EXTRA_ENV, as a fork that keeps the setting would. It prints
             REPRODUCED: the routine deploy dropped the hand-set CHAT_MAX_MODEL_CALLS, and /health reports the default
             again; and CLEARED: the deploy that carries CHAT_MAX_MODEL_CALLS keeps it, and the detector finds nothing
             left to drop
  on a lane  make gotcha-drill ID=deploy-drops-hotfix LIVE=1 PROJECT=documind-ai-YOUR-ID REGION=<region>
             ADMIN_EMAILS=<you>. Changes: documind-chat: CHAT_MAX_MODEL_CALLS=8, then make deploy-services
             SCRIPTS=commands/lesson-12.8.sh GIT_SHA=<the serving image's tag>, which rebuilds the chat image from
             this checkout; it refuses unless this checkout is at that commit and the deploy would change nothing
             else. Restores: the deploy removes the variable itself; after a failure a finally block removes it. Cost:
             Rs 0 in model calls; one Cloud Build of the chat image, about four minutes
  detector   make gotcha-detect ID=deploy-drops-hotfix PROJECT=documind-ai-YOUR-ID REGION=<region>. Reads gcloud run
             services describe for the seven services make deploy-services deploys, against each deploy script's
             --set-env-vars list and the Makefile's defaults; finds each variable the next make deploy-services would
             drop, and each switch it would put back to the Makefile's default unless you pass it
  lever      Carry the setting in the deploy, so that every deploy keeps it. A switch make deploy-services passes goes
             on its command line every time (make deploy-services ARMOR=on ADMIN_EMAILS=you@example.com); one it does
             not pass goes into the deploy script's --set-env-vars in your fork, reviewed like any change (for
             documind-chat, CHAT_EXTRA_ENV, which the Makefile empties). Until then, run the detector before each
             deploy and set again what it lists.
  lessons    0.3, 2.5, 5.5
  cost       Rs 0 offline; live, one chat image build
  kit        commands/lesson-12.8.sh: --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=$PROJECT|DOCUMIND_PROFILE=gcp
  kit        commands/lesson-12.8.sh: ${CHAT_EXTRA_ENV-}"
  kit        Makefile: CHAT_EXTRA_ENV=; \
  kit        commands/lesson-12.2.sh: --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=$PROJECT|RETRIEVAL_BACKEND=
  kit        services/chat/limits.py: MAX_MODEL_CALLS = int(os.environ.get("CHAT_MAX_MODEL_CALLS", "12"))
```

### demo_04_the_lines_the_two_drills_rest_on.py

The cell loads the kit's own reader of the deploy scripts, the one the drills and the detectors use, and prints what each deploy writes. It reads the scripts and the Makefile, and calls nothing.

**`step_01_what_each_routine_deploy_writes(session)` — The lines the two drills rest on / Do it: what each routine deploy writes**

The cell loads the kit's own reader of the deploy scripts, the one the drills and the detectors use, and prints what each deploy writes. It reads the scripts and the Makefile, and calls nothing.

Operation: bash — run in the operator shell, in the kit (the kit's own reader of the deploy scripts; no lane, no cost).

Expected shape, not a promised result:

```text
make deploy-services runs 7 deploy scripts, and each sets its service's whole environment:
  documind-ingest  commands/lesson-12.5.sh    --set-env-vars, 13 variables
  documind-api     commands/lesson-12.2.sh    --set-env-vars, 29 variables
  documind-admin   commands/lesson-12.3.sh    --set-env-vars, 4 variables
  documind-ui      commands/lesson-12.4.sh    --set-env-vars, 18 variables
  documind-chat    commands/lesson-12.8.sh    --set-env-vars, 10 variables
  documind-mcp     commands/lesson-7.2.sh     --set-env-vars, 6 variables
  documind-agent   commands/lesson-8.4.sh     --set-env-vars, 8 variables
documind-chat's list: AUDIT_BUCKET, DOCUMIND_BRAIN, DOCUMIND_PROFILE, GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT, GOOGLE_GENAI_USE_VERTEXAI, IAP_AUDIENCE, RAG_API_URL, RAG_TIMEOUT_S, SELF_URL
CHAT_MAX_MODEL_CALLS in it: False
the script's hook for more: CHAT_EXTRA_ENV, which make deploy-services sets to ''
the switches it passes, each back to the Makefile's default unless you pass it: ADMIN_EMAILS=admin@documind.example.com, ARMOR=off, BUDGET_USD=100, GENERATOR_MODEL=gemini-3.6-flash, GRAPH_BACKEND=firestore, MANAGED_MIRROR=both, MIN_INSTANCES=0, MODEL_BACKEND=vertex, RAG_LOCATION=us-central1, RAG_MODEL_BASE=gemini-3.6-flash, RESIDENCY=us, RETRIEVAL_CURRENT_ONLY=off, RETRIEVAL_GRAPH=off, ROUTING=off, SEMANTIC_CACHE=off, SPANNER_DATABASE=documind, SPANNER_INSTANCE=documind-graph
```

### demo_05_every_offline_drill_on_a_stand_in_of_cloud_run.py

Do it: pinned traffic Do it: a routine deploy drops a hotfix The command runs all 9 drills, and grep keeps each drill's verdict lines: its name, REPRODUCED, CLEARED where it shows its lever, and the count at the end. Run make gotcha-drill ID=<id> to read any one of them in full.

**`step_01_pinned_traffic(session)` — Every offline drill, on a stand-in of Cloud Run / Do it: pinned traffic**

Do it: pinned traffic

Operation: bash — run in the operator shell, in the kit (a stand-in of Cloud Run; no lane, Rs 0).

Expected shape, not a promised result:

```text
== pinned-traffic, offline (a stand-in, Rs 0): A service pinned to one revision never serves a later change
documind-chat: documind-chat-00001-mup takes 100% of the traffic, following the latest revision; /health: max_model_calls 12
the traffic held on that revision by name, as a rollback by traffic leaves it:
$ gcloud run services update-traffic documind-chat --to-revisions=documind-chat-00001-mup=100 --region=us-central1 --project=documind-ai-YOUR-ID --quiet
a setting changed by hand:
$ gcloud run services update documind-chat --update-env-vars=CHAT_MAX_MODEL_CALLS=3 --region=us-central1 --project=documind-ai-YOUR-ID --quiet
documind-chat-00002-zeq: made with CHAT_MAX_MODEL_CALLS=3, takes 0% of the traffic; /health: max_model_calls 12
detector: documind-chat: its traffic is held on documind-chat-00001-mup 100%, not on the latest revision: every later update and deploy lands at 0%
detector: documind-chat: its newest revision documind-chat-00002-zeq takes 0% of the traffic and carries no tag: a change no request reaches
REPRODUCED: the new revision takes 0% of the traffic, and /health still reports the old cap
the lever:
$ gcloud run services update-traffic documind-chat --to-latest --region=us-central1 --project=documind-ai-YOUR-ID --quiet
documind-chat-00002-zeq takes 100% of the traffic; /health: max_model_calls 3
CLEARED: after --to-latest the new revision takes the traffic, and /health reports the new cap
$ gcloud run services update documind-chat --remove-env-vars=CHAT_MAX_MODEL_CALLS --region=us-central1 --project=documind-ai-YOUR-ID --quiet
restored: CHAT_MAX_MODEL_CALLS unset, traffic on the latest revision; /health: max_model_calls 12
```

**`step_02_a_routine_deploy_drops_a_hotfix(session)` — Every offline drill, on a stand-in of Cloud Run / Do it: a routine deploy drops a hotfix**

Do it: a routine deploy drops a hotfix

Operation: bash — run in the operator shell, in the kit (a stand-in of Cloud Run; no lane, Rs 0).

Expected shape, not a promised result:

```text
== deploy-drops-hotfix, offline (a stand-in, Rs 0): A routine make deploy-services drops a setting made by hand
documind-chat: image tag c0ffee1, nothing the next deploy would change; /health: max_model_calls 12
a setting changed by hand:
$ gcloud run services update documind-chat --update-env-vars=CHAT_MAX_MODEL_CALLS=8 --region=us-central1 --project=documind-ai-YOUR-ID --quiet
/health: max_model_calls 8: the hand-set value answers
detector, before the deploy: CHAT_MAX_MODEL_CALLS=8: dropped, not in commands/lesson-12.8.sh's --set-env-vars; make deploy-services empties CHAT_EXTRA_ENV, the script's hook for more
the routine deploy:
$ make deploy-services SCRIPTS=commands/lesson-12.8.sh PROJECT=documind-ai-YOUR-ID REGION=us-central1 GIT_SHA=c0ffee1
documind-chat-00003-rix: CHAT_MAX_MODEL_CALLS gone; /health: max_model_calls 12
REPRODUCED: the routine deploy dropped the hand-set CHAT_MAX_MODEL_CALLS, and /health reports the default again
the lever: carry the value in the deploy. commands/lesson-12.8.sh reads CHAT_EXTRA_ENV for more variables, and make deploy-services empties it (the Makefile's CHAT_EXTRA_ENV=;), so a fork that keeps the setting sets it there: CHAT_EXTRA_ENV='|CHAT_MAX_MODEL_CALLS=8'
documind-chat-00004-lod: /health: max_model_calls 8; the detector, with that deploy: nothing to drop
CLEARED: the deploy that carries CHAT_MAX_MODEL_CALLS keeps it, and the detector finds nothing left to drop
restored: CHAT_MAX_MODEL_CALLS unset, traffic on the latest revision; /health: max_model_calls 12
```

**`step_03_every_offline_drill(session)` — Every offline drill, on a stand-in of Cloud Run / Do it: every offline drill**

The command runs all 9 drills, and grep keeps each drill's verdict lines: its name, REPRODUCED, CLEARED where it shows its lever, and the count at the end. Run make gotcha-drill ID=<id> to read any one of them in full.

Operation: bash — run in the operator shell, in the kit (every offline drill; no lane, Rs 0, a few seconds).

Expected shape, not a promised result:

```text
== pinned-traffic, offline (a stand-in, Rs 0): A service pinned to one revision never serves a later change
REPRODUCED: the new revision takes 0% of the traffic, and /health still reports the old cap
CLEARED: after --to-latest the new revision takes the traffic, and /health reports the new cap
== deploy-drops-hotfix, offline (a stand-in, Rs 0): A routine make deploy-services drops a setting made by hand
REPRODUCED: the routine deploy dropped the hand-set CHAT_MAX_MODEL_CALLS, and /health reports the default again
CLEARED: the deploy that carries CHAT_MAX_MODEL_CALLS keeps it, and the detector finds nothing left to drop
== ungated-api-release, offline (a stand-in, Rs 0): make deploy-services and make up put an ungated API revision live
REPRODUCED: make deploy-services moved documind-api's traffic to a revision no gate judged
CLEARED: make deploy-services without lesson-12.2.sh left documind-api on the gated revision
== switch-rides-into-candidate, offline (a stand-in, Rs 0): A switch set on one candidate rides into the next
REPRODUCED: the new candidate carries QUERY_REWRITE=on, which nobody set on it
CLEARED: after the undo, the next candidate differs from the serving revision in GIT_SHA alone
== rollback-keeps-template, offline (a stand-in, Rs 0): make rollback moves the traffic back, not the settings
REPRODUCED: the next candidate inherits the rolled-back revision's GENERATOR_MODEL=gemini-3.6-flsh
CLEARED: after the repair, the next candidate's GENERATOR_MODEL is the serving revision's
== looping-model-stopped, offline (a stand-in, Rs 0): A looping model is stopped quietly, with HTTP 200
REPRODUCED: the turn stopped at a limit and answered HTTP 200, and no alert policy or log metric in terraform/ reads stopped_by
== abandoned-call-bills, offline (a stand-in, Rs 0): A search the turn abandoned still runs, and rag-api bills it
REPRODUCED: a running call cut at its budget ran to its end after the turn had let it go
== agent-spend-outside-the-month, offline (a stand-in, Rs 0): The agents' own model calls are missing from the month's spend
REPRODUCED: the agent's own model calls are in none of them: tenant_daily and make usage read rag-api's rows only, and rag-api alone adds to the breaker's counter
== ci-promote-loses-previous, offline (a stand-in, Rs 0): After a CI promote, make rollback has nothing to return to
REPRODUCED: make rollback stops in this checkout: the promote recorded the previous revision on the runner
CLEARED: with the name from the promote job's log, make rollback returns the traffic to the revision before the promote
9 of 9 offline drills reproduced their gotcha
```

### demo_06_your_two_services_as_cloud_run_s_api_returns_them.py

Do it: the two services, before the drills

**`step_01_the_two_services_before_the_drills(session)` — Your two services, as Cloud Run's API returns them / Do it: the two services, before the drills**

Do it: the two services, before the drills

Operation: bash — run in the operator shell, in the kit (reads only: two services and their serving revisions).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rest_traffic.txt]
```

### demo_07_the_two_drills_on_your_lane.py

documind-chat changes for a few minutes: two new revisions, four /health reads, and no model call. Most of its time is the chat's image build, about four minutes. No model call. Do it: the chat, on every brain

**`step_01_pinned_traffic_on_your_lane(session)` — The two drills on your lane / Do it: pinned traffic, on your lane**

documind-chat changes for a few minutes: two new revisions, four /health reads, and no model call.

Operation: bash — run in the operator shell, in the kit (documind-chat for a few minutes; Rs 0).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/drill_pinned.txt]
```

**`step_02_a_routine_deploy_drops_a_hotfix_on_your_la(session)` — The two drills on your lane / Do it: a routine deploy drops a hotfix, on your lane**

Most of its time is the chat's image build, about four minutes. No model call.

Operation: bash — run in the operator shell, in the kit (documind-chat: a routine deploy of the chat alone, about four minutes; Rs 0 in model calls).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/drill_deploy_drop.txt]
```

**`step_03_the_chat_on_every_brain(session)` — The two drills on your lane / Do it: the chat, on every brain**

Do it: the chat, on every brain

Operation: bash — run in the operator shell, in the kit (4 questions, one per brain, and the outsider refused; about Rs 5).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke_chat.txt]
```

### demo_08_the_detectors_what_your_lane_shows_now.py

Do it: every detector

**`step_01_every_detector(session)` — The detectors: what your lane shows now / Do it: every detector**

Do it: every detector

Operation: bash — run in the operator shell, in the kit (reads only).

IDE adaptation: Read the detectors' exit as the page does: 1 when anything is found, which every lane shows (the admin address deploy-drops-hotfix reads), stopped the demo at its first cell (22 October 2026). The step fails if a detector's read failed with nothing found (make's Error 2) or the summary line never printed.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/detect_all.txt]
```

### demo_09_the_release_no_gate_judged_loud_against_silent_and_what_the_kit_does_not_do_yet.py

This is the hazard in step 1's red box. make up runs make deploy-services, whose default SCRIPTS include lesson-12.2.sh, the API's deploy. After it the recipe moves documind-api's traffic to the revision it just made, by name (step 4). Lesson 11.2's gate runs on a candidate, and make deploy-services makes none. Add an entry whose drill and check commands/gotchas.py does not run, and the registry refuses to load: make gotchas, every drill and every detector stop with exit 2 and name the problems. commands/tests/test_gotchas.py holds the same rule, in test_a_detector_that_does_not_exist_is_refused, one of its 50 tests. The kit's dry-run workflow runs that file on every push, so a pull request that adds such an entry goes red. The cell copies pinned-traffic as made-up-gotcha, runs the registry, and puts the file back.

**`step_01_the_release_no_gate_judged(session)` — The release no gate judged, loud against silent, and what the kit does not do yet / The release no gate judged**

This is the hazard in step 1's red box. make up runs make deploy-services, whose default SCRIPTS include lesson-12.2.sh, the API's deploy. After it the recipe moves documind-api's traffic to the revision it just made, by name (step 4). Lesson 11.2's gate runs on a candidate, and make deploy-services makes none.

Operation: bash — run in the operator shell, in the kit (a stand-in of Cloud Run; no lane, Rs 0).

Expected shape, not a promised result:

```text
== ungated-api-release, offline (a stand-in, Rs 0): make deploy-services and make up put an ungated API revision live
documind-api after make release-candidate GIT_SHA=b2c3d4e, the gate and make promote: documind-api-00002-zeq serves 100%, recorded in deploy/.candidate-revision
a routine deploy from a newer checkout:
$ make deploy-services GIT_SHA=c3d4e5f   (SCRIPTS: 7 scripts, lesson-12.2.sh among them)
documind-api: documind-api-00003-rix serves 100%, GIT_SHA c3d4e5f
detector: documind-api serves documind-api-00003-rix, which this checkout neither recorded as a candidate (documind-api-00002-zeq) nor rolled back to (documind-api-00001-mup): make deploy-services, make up or a hand update-traffic put it live, and no gate judged it
REPRODUCED: make deploy-services moved documind-api's traffic to a revision no gate judged
the lever, from the same gated state: the other services' scripts only
documind-api after make release-candidate GIT_SHA=b2c3d4e, the gate and make promote: documind-api-00002-zeq serves 100%, recorded in deploy/.candidate-revision
$ make deploy-services SCRIPTS="commands/lesson-12.5.sh commands/lesson-12.3.sh commands/lesson-12.4.sh commands/lesson-12.8.sh commands/lesson-7.2.sh commands/lesson-8.4.sh" GIT_SHA=c3d4e5f
detector: documind-api serves documind-api-00002-zeq, the candidate this checkout recorded (make candidate or make release-candidate), which the gate judged if you ran make eval-live on it
CLEARED: make deploy-services without lesson-12.2.sh left documind-api on the gated revision
```

**`step_02_change_it_a_gotcha_with_no_detector(session)` — The release no gate judged, loud against silent, and what the kit does not do yet / Change it: a gotcha with no detector**

Add an entry whose drill and check commands/gotchas.py does not run, and the registry refuses to load: make gotchas, every drill and every detector stop with exit 2 and name the problems. commands/tests/test_gotchas.py holds the same rule, in test_a_detector_that_does_not_exist_is_refused, one of its 50 tests. The kit's dry-run workflow runs that file on every push, so a pull request that adds such an entry goes red. The cell copies pinned-traffic as made-up-gotcha, runs the registry, and puts the file back.

Operation: bash — run in the operator shell, in the kit (edits ops/gotchas.json, then puts it back; no lane, no cost).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
ops/gotchas.json: 14 entries, the last one made-up-gotcha
STOP: gotchas.json breaks its rules: made-up-gotcha: drill.offline names a drill commands/gotchas.py does not run; made-up-gotcha: detector.kind is check, and commands/gotchas.py has no check for this id
exit 2
13 gotchas in ops/gotchas.json (workshop lesson 11.7). make gotchas ID=<id> shows one; make gotcha-drill runs every offline drill, Rs 0
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's drills change documind-chat alone, and the one answer that reads acme's rows is make smoke-chat's, which checks that each brain cites something, not which store it came from. Pin acme or not, as you prefer; if you set the pin, put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's drills change documind-chat alone, and the one answer that reads acme's rows is make smoke-chat's, which checks that each brain cites something, not which store it came from. Pin acme or not, as you prefer; if you set the pin, put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_11.7_Production_Gotchas_WIX.html`. All 43 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `3b7c21fe9698327c5c705df17b12bee0ccfc497a`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
