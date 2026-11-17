# Lesson 10.11: System design: incident auto-remediation

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_on_your_lane_hold_a_fault_read_the_plan_run_it_by_hand.py](demo_03_on_your_lane_hold_a_fault_read_the_plan_run_it_by_hand.py) | On your lane: hold a fault, read the plan, run it by hand |
| 4 | [demo_04_architecture_the_path_an_incident_takes_read_by_read_and_rule_by_rule.py](demo_04_architecture_the_path_an_incident_takes_read_by_read_and_rule_by_rule.py) | Architecture: the path an incident takes, read by read and rule by rule |
| 5 | [demo_05_architecture_why_rules_and_not_a_model_and_two_more_designs_rejected.py](demo_05_architecture_why_rules_and_not_a_model_and_two_more_designs_rejected.py) | Architecture: why rules and not a model, and two more designs rejected |
| 6 | [demo_06_failure_modes_four_the_kit_reproduces_and_what_pages_for_them.py](demo_06_failure_modes_four_the_kit_reproduces_and_what_pages_for_them.py) | Failure modes: four the kit reproduces, and what pages for them |
| 7 | [demo_07_cost_an_incident_priced_and_a_model_priced_at_three_scales.py](demo_07_cost_an_incident_priced_and_a_model_priced_at_three_scales.py) | Cost: an incident priced, and a model priced at three scales |
| 8 | [demo_08_cost_at_10_what_breaks_first_is_the_read.py](demo_08_cost_at_10_what_breaks_first_is_the_read.py) | Cost at 10×: what breaks first is the read |
| 9 | [demo_09_evals_what_the_kit_s_tests_hold_and_the_checks_that_cannot_fail.py](demo_09_evals_what_the_kit_s_tests_hold_and_the_checks_that_cannot_fail.py) | Evals: what the kit's tests hold, and the checks that cannot fail |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [cleanup/demo_03_on_your_lane_hold_a_fault_read_the_plan_run_it_by_hand.py](cleanup/demo_03_on_your_lane_hold_a_fault_read_the_plan_run_it_by_hand.py) — At lesson end: RESTORE=1 runs the plan's restore for the drill: the variable put back as .fault-hold recorded it, which makes a new revision, then the traffic sent to the latest revision. It checks that the latest revision takes all the traffic, and removes .fault-hold. Then the plan's last step: the smoke, and remediate, which should read no_failure. RESTORE=1 runs the plan's restore for the drill: the variable put back as .fault-hold recorded it, which makes a new revision, then the traffic sent to the latest revision. It checks that the latest revision takes all the traffic, and removes .fault-hold. Then the plan's last step: the smoke, and remediate, which should read no_failure.
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

### demo_03_on_your_lane_hold_a_fault_read_the_plan_run_it_by_hand.py

make remediate OFFLINE=1 reads the kit's own recording of this drill, ops/incidents/held_model.json. It needs no PROJECT and no credential, and it prints the plan you should get on the lane, with your lane's revision names in place of these. HOLD=1 writes deploy/.fault-hold first, with the variable as it was and the revision serving, so that RESTORE=1 always has a record. Then it sets the fault, and the new revision takes the traffic. It runs the smoke once, so that the lane holds the fault's own turns for remediate to read, and it leaves the fault in place. remediate reads the lane three times and prints the plan. SAVE= keeps what it read, with the project id and number replaced, so the incident can be replayed later. Expect bad_revision, the change CHAT_MODEL: unset -> "gemini-3.6-flsh", and a rollback to the revision HOLD=1 recorded as serving before the fault. Paste step 1's command as your plan printed it, or set PREV to the revision it names. It moves traffic only: the fault's revision stays, at 0%. The plan's step 2. Every brain should answer, because the traffic is on the revision before the fault. Expect rolled_back. The plan starts again from the verify, and does not print the rollback a second time: its step 1 says the rollback is done.

**`step_01_first_offline_the_plan_the_drill_should_pr(session)` — On your lane: hold a fault, read the plan, run it by hand / First, offline: the plan the drill should produce**

make remediate OFFLINE=1 reads the kit's own recording of this drill, ops/incidents/held_model.json. It needs no PROJECT and no credential, and it prints the plan you should get on the lane, with your lane's revision names in place of these.

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
remediate: documind-chat on documind-ai-YOUR-ID (us-central1), the 60 minutes to 2026-10-12 10:00 UTC (15:30 IST)
rules only: no model is called, and nothing on the lane is changed.
read from a recorded state: held_model.json (make incident-drill FAULT=model HOLD=1 and its smoke: CHAT_MODEL=gemini-3.6-flsh, a mistyped model, fails every agent turn with a 500)

What the lane shows
  traffic     100% documind-chat-00042-tvd (following the latest revision)
  revision    documind-chat-00042-tvd  created 2026-10-12 09:41 UTC (15:11 IST), inside the window  [serving]
  revision    documind-chat-00041-kpw  created 2026-10-09 06:12 UTC (11:42 IST)  [the revision before it]
  the change  CHAT_MODEL: unset -> "gemini-3.6-flsh"
  answers     documind-chat-00042-tvd: 5 requests, 3 answered 5xx (60%); 1 chat turn, 0 stopped by a limit
  answers     documind-chat-00041-kpw: nothing in the window
  signal      5xx answers, silent: no alert policy the kit declares counts a service's 5xx answers

Diagnosis - rule bad_revision
  documind-chat-00042-tvd was created inside the window and fails (5xx answers); documind-chat-00041-kpw, the revision
  before it, answered nothing in the window, so it shows no failure. Between the two, only CHAT_MODEL changed.

The plan. remediate runs none of it: you do, in this order.
  1. Roll back: all traffic to documind-chat-00041-kpw, which never went away (documind-chat-00042-tvd stays, at 0%).
       gcloud run services update-traffic documind-chat --region us-central1 --project documind-ai-YOUR-ID --to-revisions documind-chat-00041-kpw=100
  2. Verify: every brain answers.
       make smoke-chat PROJECT=documind-ai-YOUR-ID REGION=us-central1
  3. Restore. The rollback moved traffic only: the template still carries the change, and a service whose traffic is
     pinned to a revision by name leaves every later revision at 0%. Undo the change, then send the traffic to the
     latest revision, in that order (the other order sends it back to documind-chat-00042-tvd).
       gcloud run services update documind-chat --region us-central1 --project documind-ai-YOUR-ID --remove-env-vars=CHAT_MODEL --quiet
       gcloud run services update-traffic documind-chat --region us-central1 --project documind-ai-YOUR-ID --to-latest
     This checkout holds the drill's fault (deploy/.fault-hold): make incident-drill RESTORE=1
     PROJECT=documind-ai-YOUR-ID runs both.
  4. Verify again: make smoke-chat PROJECT=documind-ai-YOUR-ID REGION=us-central1, then make remediate
     PROJECT=documind-ai-YOUR-ID SERVICE=documind-chat: it reads no failure.

0 model calls. Nothing on the lane was changed.
```

**`step_02_hold_the_fault(session)` — On your lane: hold a fault, read the plan, run it by hand / Hold the fault**

HOLD=1 writes deploy/.fault-hold first, with the variable as it was and the revision serving, so that RESTORE=1 always has a record. Then it sets the fault, and the new revision takes the traffic. It runs the smoke once, so that the lane holds the fault's own turns for remediate to read, and it leaves the fault in place.

Operation: bash — run in the operator shell, in $DEMO_ROOT (one revision of documind-chat, and the smoke once on the fault).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/hold.txt]
```

**`step_03_read_the_plan(session)` — On your lane: hold a fault, read the plan, run it by hand / Read the plan**

remediate reads the lane three times and prints the plan. SAVE= keeps what it read, with the project id and number replaced, so the incident can be replayed later. Expect bad_revision, the change CHAT_MODEL: unset -> "gemini-3.6-flsh", and a rollback to the revision HOLD=1 recorded as serving before the fault.

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: three reads, nothing changed).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/plan_held.txt]
```

**`step_04_run_the_rollback_it_printed(session)` — On your lane: hold a fault, read the plan, run it by hand / Run the rollback it printed**

Paste step 1's command as your plan printed it, or set PREV to the revision it names. It moves traffic only: the fault's revision stays, at 0%.

Operation: bash — run in the operator shell (the rollback your plan printed: traffic to the revision before, by name).

IDE adaptation: Fill in the page's placeholder from the plan itself: the saved plan replays offline at Rs 0, and its step 1 names the revision to roll back to. The literal REVISION was sent to gcloud, which refused it, and the fault stayed on the lane (22 October 2026).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rollback.txt]
```

**`step_05_verify(session)` — On your lane: hold a fault, read the plan, run it by hand / Verify**

The plan's step 2. Every brain should answer, because the traffic is on the revision before the fault.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the plan's verify: four brains, one question).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke_rolled_back.txt]
```

**`step_06_read_the_lane_again(session)` — On your lane: hold a fault, read the plan, run it by hand / Read the lane again**

Expect rolled_back. The plan starts again from the verify, and does not print the rollback a second time: its step 1 says the rollback is done.

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: three reads, nothing changed).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/plan_rolled_back.txt]
```

### demo_04_architecture_the_path_an_incident_takes_read_by_read_and_rule_by_rule.py

The loop runs make remediate OFFLINE=1 on each of the kit's seven recordings and prints, for each, the rule that decided, how many commands the plan printed, and its last line. The cell loads remediate.py, prints the only commands it may run, the events it reads on each service, the exact filter of its one logging read for the drill's window, and holds five commands against the denylist. RUNBOOKS=1 lists every policy the kit declares with its runbook and what remediate may do. Its first line, and the two signals no policy watches: One GET on the Monitoring API lists every alert policy on your lane by its display name, and the cell holds each against ops/runbooks.json. On a lane deployed with the defaults, expect eleven: three that remediate may roll back for and eight that are a person's, with the other six behind their switches. A no row line would be a policy that pages with no runbook remediate knows.

**`step_01_every_recording_offline(session)` — Architecture: the path an incident takes, read by read and rule by rule / Do it: every recording, offline**

The loop runs make remediate OFFLINE=1 on each of the kit's seven recordings and prints, for each, the rule that decided, how many commands the plan printed, and its last line.

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
held_model        bad_revision    4 printed, 0 model calls
held_model_calls  bad_revision    4 printed, 0 model calls
rolled_back       rolled_back     3 printed, 0 model calls
restored          no_failure      0 printed, 0 model calls
old_revision      no_change       0 printed, 0 model calls
person_only       person_only     0 printed, 0 model calls
unknown_policy    unknown_policy  0 printed, 0 model calls
```

**`step_02_the_reads_and_the_denylist(session)` — Architecture: the path an incident takes, read by read and rule by rule / Do it: the reads, and the denylist**

The cell loads remediate.py, prints the only commands it may run, the events it reads on each service, the exact filter of its one logging read for the drill's window, and holds five commands against the denylist.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
the only commands it runs: gcloud run services describe; gcloud run revisions list; gcloud logging read
documind-chat: the request log, and the events chat, desk, desk_shadow, desk_delegation_refused, desk_gate_check, desk_check_tenants_unread
documind-api: the request log, and the events query, stream, desk_gate_check, desk_check_tenants_unread
resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND timestamp>="2026-10-12T09:00:00Z" AND (logName="projects/documind-ai-YOUR-ID/logs/run.googleapis.com%2Frequests" OR jsonPayload.event="chat" OR jsonPayload.event="desk" OR jsonPayload.event="desk_shadow" OR jsonPayload.event="desk_delegation_refused" OR jsonPayload.event="desk_gate_check" OR jsonPayload.event="desk_check_tenants_unread")
the newest 2000 lines of a window of 1h (SINCE=, 168h at most)
may be printed         gcloud run services update-traffic documind-chat --to-revisions documind-chat-00041-kpw=100
refused: 'delete'      gcloud run services delete documind-chat --quiet
refused: 'deploy'      gcloud run deploy documind-chat --image chat:fix
refused: '-iam-policy' gcloud run services add-iam-policy-binding documind-chat --member=allUsers
refused: 'make down'   make down PROJECT=documind-ai-YOUR-ID
```

**`step_03_the_catalog(session)` — Architecture: the path an incident takes, read by read and rule by rule / Do it: the catalog**

RUNBOOKS=1 lists every policy the kit declares with its runbook and what remediate may do. Its first line, and the two signals no policy watches:

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
17 alert policies the kit declares (terraform/alerts.tf: 9, terraform/desk_alerts.tf: 8); 6 behind a switch. remediate may propose a rollback for 5; the rest are a person's.
Silent: what remediate reads that no policy watches
  5xx answers: requests a service answered with a 5xx status, from Cloud Run's request log. no alert policy the kit
  declares counts a service's 5xx answers.
  chat turns stopped by a limit: documind-chat turns ended by one of their limits (limits.stopped_by on the chat row,
  workshop lesson 5.5). every chat row carries stopped_by and no policy counts it yet: an agent alert policy is
  designed for after 6 December.
```

**`step_04_on_your_lane_the_policies_your_lane_holds(session)` — Architecture: the path an incident takes, read by read and rule by rule / Read it on your lane: the policies your lane holds**

One GET on the Monitoring API lists every alert policy on your lane by its display name, and the cell holds each against ops/runbooks.json. On a lane deployed with the defaults, expect eleven: three that remediate may roll back for and eight that are a person's, with the other six behind their switches. A no row line would be a policy that pages with no runbook remediate knows.

Operation: bash — run in the operator shell, in $DEMO_ROOT (one GET on the Monitoring API; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/lane_policies.txt]
```

### demo_05_architecture_why_rules_and_not_a_model_and_two_more_designs_rejected.py

The cell does what the kit's test does: it plants the instruction in every line of the drill's recording, in three fields no rule counts and in three a line keeps, then prints both plans' rules and commands and looks for the planted words in the printout.

**`step_01_plant_an_instruction(session)` — Architecture: why rules and not a model, and two more designs rejected / Do it: plant an instruction**

The cell does what the kit's test does: it plants the instruction in every line of the drill's recording, in three fields no rule counts and in three a line keeps, then prints both plans' rules and commands and looks for the planted words in the printout.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
clean    Diagnosis - rule bad_revision, 4 commands
planted  Diagnosis - rule bad_revision, 4 commands
the same commands: True | 'delete' printed: False | 'SYSTEM' printed: False
answers     documind-chat-00042-tvd: 5 requests, 3 answered 5xx (60%); 1 chat turn, 1 stopped by a limit (another limit 1)
```

### demo_06_failure_modes_four_the_kit_reproduces_and_what_pages_for_them.py

The cell prints the catalog's two silent signals, then gives remediate's rules six states: the kit's recordings of the first three failures, the pinned lane two ways, built as the kit's test builds them, and the rolled-back lane with the failing revision's lines gone from the window. Last, the good revision carries a value with a denied word in it.

**`step_01_the_failure_modes_offline(session)` — Failure modes: four the kit reproduces, and what pages for them / Do it: the failure modes, offline**

The cell prints the catalog's two silent signals, then gives remediate's rules six states: the kit's recordings of the first three failures, the pinned lane two ways, built as the kit's test builds them, and the rolled-back lane with the failing revision's lines gone from the window. Last, the good revision carries a value with a denied word in it.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
silent: 5xx answers: no alert policy the kit declares counts a service's 5xx answers
silent: chat turns stopped by a limit: every chat row carries stopped_by and no policy counts it yet: an agent alert policy is designed for after 6 December
a mistyped model                       bad_revision, on 5xx answers
a call cap                             bad_revision, on chat turns stopped by a limit
a failure no change explains           no_change, on 5xx answers
pinned, the change undone              pinned_clean
pinned, a newer revision that differs  pinned_new
rolled back, the window gone by        pinned_new
a denied word in a value: printed; the denylist read gcloud run services update documind-chat --region --project --update-env-vars --remove-env-vars --quiet
```

### demo_07_cost_an_incident_priced_and_a_model_priced_at_three_scales.py

Component 6's COST-MODEL.md starts from this. The cell reads the rates and the rupee rate from the kit, builds a model's prompt from the kit's own catalog and docstring, prints the plan remediate gives the drill's recording as the model's answer, and fills an hour's window with the recording's own lines at each scale.

**`step_01_the_cost_model_as_a_script(session)` — Cost: an incident priced, and a model priced at three scales / Do it: the cost model as a script**

Component 6's COST-MODEL.md starts from this. The cell reads the rates and the rupee rate from the kit, builds a model's prompt from the kit's own catalog and docstring, prints the plan remediate gives the drill's recording as the model's answer, and fills an hour's window with the recording's own lines at each scale.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
the rules: 3 reads at Rs 0 and 0 model calls, at every scale
a model: 3,241 tokens of rules and runbooks, then the lines; 614 tokens of plan out
    1,000 turns a month:     3 lines an hour,     3 read |  4,016 tokens in | flash Rs  0.90 ($0.0106), flash-lite Rs 0.16 ($0.0019) an incident
   10,000 turns a month:    28 lines an hour,    28 read |  4,564 tokens in | flash Rs  0.97 ($0.0115), flash-lite Rs 0.18 ($0.0021) an incident
  100,000 turns a month:   274 lines an hour,   274 read |  9,945 tokens in | flash Rs  1.66 ($0.0195), flash-lite Rs 0.29 ($0.0034) an incident
1,000,000 turns a month: 2,740 lines an hour, 2,000 read | 47,701 tokens in | flash Rs  6.47 ($0.0762), flash-lite Rs 1.09 ($0.0128) an incident
```

### demo_08_cost_at_10_what_breaks_first_is_the_read.py

Do it: the limits from the kit's files

**`step_01_the_limits_from_the_kit_s_files(session)` — Cost at 10×: what breaks first is the read / Do it: the limits from the kit's files**

Do it: the limits from the kit's files

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).

Expected shape, not a promised result:

```text
the read: the newest 2000 lines, 1000 turns at 2 lines a turn | a failure: 2 bad lines and a share | the window: 1h
    1,000 turns a month:     1.4 turns an hour | the read covers 60.0 of its 60 minutes | under the router's 100-turn floor
   10,000 turns a month:    13.7 turns an hour | the read covers 60.0 of its 60 minutes | under the router's 100-turn floor
  100,000 turns a month:   137.0 turns an hour | the read covers 60.0 of its 60 minutes | reaches the router's 100-turn floor
1,000,000 turns a month:  1369.9 turns an hour | the read covers 43.8 of its 60 minutes | reaches the router's 100-turn floor
the read stops covering an average hour at 730,000 turns a month; the router's floor is reached at 73,000, and the gate check's 20 in 30 minutes at 29,200 checks a month
```

### demo_09_evals_what_the_kit_s_tests_hold_and_the_checks_that_cannot_fail.py

The cell loads the kit's test module and runs its four classes that need no bash and no make, one test at a time, printing each by its name.

**`step_01_the_kit_s_tests_offline(session)` — Evals: what the kit's tests hold, and the checks that cannot fail / Do it: the kit's tests, offline**

The cell loads the kit's test module and runs its four classes that need no bash and no make, one test at a time, printing each by its name.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: the kit's tests stand gcloud in).

Expected shape, not a promised result:

```text
PolicyTests (7)
  ok   a policy without a row or a row without a policy stops
  ok   a runbook is the policys own documentation
  ok   each rows evidence reads what its policy counts
  ok   every command the catalog names is one remediate may print
  ok   every policy the kit declares has one row
  ok   the denylist reads a commands words and flags never its values
  ok   the runbooks listing
RuleTests (15)
  ok   a candidate is kept out of the incident
  ok   a failure no change explains is no rule
  ok   an unknown policy is no rule
  ok   documind api rolls back with make rollback
  ok   every policy named offline
  ok   held model calls names the cap
  ok   held model chooses the rollback
  ok   person only prints the policys runbook
  ok   pinned states after the rollback
  ok   restored reads no failure
  ok   rolled back prints the verify and the restore not another rollback
  ok   split traffic is no rule
  ok   the latency and people only signals
  ok   the restore quotes values and keeps secrets
  ok   the thresholds a failure needs
SafetyTests (8)
  ok   a line keeps no person
  ok   a planted instruction changes nothing
  ok   every command it runs is one of three reads
  ok   gcloud json refuses anything but a read
  ok   no model client and no connection of its own
  ok   no printed command could delete deploy or grant
  ok   the fixtures carry placeholders only
  ok   the live path reads three times and runs none of the plan
LiveReadTests (9)
  ok   a plan that stops saves nothing
  ok   a service named by the policy
  ok   save finds the number in the services urls without a namespace
  ok   save makes the reports folder a fresh clone lacks
  ok   save refuses an identifier it cannot replace
  ok   save then offline prints the same plan
  ok   the inputs it refuses
  ok   the log filter reads the requests and the policies events
  ok   the reads shape the state a fixture holds
```

### cleanup/demo_03_on_your_lane_hold_a_fault_read_the_plan_run_it_by_hand.py

At lesson end: RESTORE=1 runs the plan's restore for the drill: the variable put back as .fault-hold recorded it, which makes a new revision, then the traffic sent to the latest revision. It checks that the latest revision takes all the traffic, and removes .fault-hold. Then the plan's last step: the smoke, and remediate, which should read no_failure. RESTORE=1 runs the plan's restore for the drill: the variable put back as .fault-hold recorded it, which makes a new revision, then the traffic sent to the latest revision. It checks that the latest revision takes all the traffic, and removes .fault-hold. Then the plan's last step: the smoke, and remediate, which should read no_failure.

**`step_01_restore_and_verify_again(session)` — On your lane: hold a fault, read the plan, run it by hand / Restore, and verify again**

RESTORE=1 runs the plan's restore for the drill: the variable put back as .fault-hold recorded it, which makes a new revision, then the traffic sent to the latest revision. It checks that the latest revision takes all the traffic, and removes .fault-hold. Then the plan's last step: the smoke, and remediate, which should read no_failure.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the plan's restore, as the drill recorded it).

IDE adaptation: Restore only a fault this checkout holds: the restore is the lesson's cleanup, run after a failure too, and a run that stopped before the hold has nothing to put back.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/restore.txt]
```

**`step_02_restore_and_verify_again(session)` — On your lane: hold a fault, read the plan, run it by hand / Restore, and verify again**

RESTORE=1 runs the plan's restore for the drill: the variable put back as .fault-hold recorded it, which makes a new revision, then the traffic sent to the latest revision. It checks that the latest revision takes all the traffic, and removes .fault-hold. Then the plan's last step: the smoke, and remediate, which should read no_failure.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the plan's verify again).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke_restored.txt]

[awaiting the author's run: data/plan_restored.txt]
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_10.11_Incident_Remediation_WIX.html`. All 64 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `05a7640fa25b236c78e6696879fc67de8b6e8121`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
