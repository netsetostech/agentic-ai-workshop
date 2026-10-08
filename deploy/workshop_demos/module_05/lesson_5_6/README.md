# Lesson 5.6: Hand a question to the person the law names

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_your_lane_the_desk_s_resources_accounts_queues_and_roles.py](demo_03_your_lane_the_desk_s_resources_accounts_queues_and_roles.py) | Your lane: the Desk's resources, accounts, queues and roles |
| 4 | [demo_04_the_desk_page_tell_raise_read.py](demo_04_the_desk_page_tell_raise_read.py) | The Desk page: tell, raise, read |
| 5 | [demo_05_one_fixed_reply_at_every_door.py](demo_05_one_fixed_reply_at_every_door.py) | One fixed reply at every door |
| 6 | [demo_06_roles_and_cases_in_the_code.py](demo_06_roles_and_cases_in_the_code.py) | Roles and cases, in the code |
| 7 | [demo_07_the_case_routes_over_rest.py](demo_07_the_case_routes_over_rest.py) | The case routes, over REST |
| 8 | [demo_08_the_records_the_audit_events_and_the_log_rows.py](demo_08_the_records_the_audit_events_and_the_log_rows.py) | The records, the audit events and the log rows |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

Module 5's deployed chat lane and lesson 1.1's roster. Step 3 applies the Desk's Terraform, redeploys rag-api, the UI and the chat service, declares the hourly overdue job, and loads acme's queues and roles, leaving desk_gate unwritten so acme has the gate's rules and no model check; keep DESK_JOB=true on every later plan, and on make reconcile-job and make batch-job.

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

### demo_03_your_lane_the_desk_s_resources_accounts_queues_and_roles.py

On a lane whose last plan predates the Desk, the plan adds 23 resources. terraform/desk.tf has 12 of them: two TTL fields (a draft's expire_at and a client token's), five indexes (one for each query the case queue makes) and five eval accounts. terraform/desk_alerts.tf has six log-based metrics and four alert policies, and terraform/storage.tf lets the chat service write the audit bucket. The one change is the log sink's filter, widened to copy the Desk's rows to BigQuery. Three switches would add more, and this lesson needs none of them: GCHAT_DOOR=true adds 11 for lesson 10.4's Google Chat door, DESK_ROUTER_ALERTS=true the router's three alert policies, and DESK_GATE_ALERTS=true the policy that pages when a company's model checks keep failing, for a lane where some company has the check on. Then come the images with the Desk's code, deployed by their own scripts. lesson-12.8.sh builds the chat image itself and lets the eval accounts invoke documind-chat. Last, make desk-job declares the hourly overdue scan on that chat image: a plan with DESK_JOB=true, which adds the job's three, then its apply. The whole cell takes many minutes. The flags are the ones you gave make up. A script cannot call the chat service as a person, so the kit has eval accounts. Each is a service account on one tenant's roster, with no project role, and make smoke-cases and this lesson's cells call as them. evalacme is an acme employee, evalgrc an acme Grievance Redressal Committee member, and evalzeta a zeta employee. make desk-operators lets you mint tokens as all five. The cell also sets CHAT and UI, notes the time in SINCE105 for step 8's log read, and defines two helpers: sa names an account, and etok mints a token as one, for the chat service. evals/desk/queues.acme.json names acme's queues: who receives each kind of case, and the company's target in days. For POSH it lists each office's Internal Committee and its district's Local Committee. The file puts you@example.com on both offices' committees, and the sed puts your own email there instead. Then make desk, with no DESK_GATE, prints acme's switches and writes nothing. evalgrc gets grc_member alone, so it can read and move grievances but cannot raise a case: the note says so. You get employee, so the Desk page shows you Tell the Desk and lets you raise cases. You also get the three roles that read: grievances, and the POSH cases of both offices.

**`step_01_the_desk_on_your_lane(session)` — Your lane: the Desk's resources, accounts, queues and roles / Do it: the Desk on your lane**

On a lane whose last plan predates the Desk, the plan adds 23 resources. terraform/desk.tf has 12 of them: two TTL fields (a draft's expire_at and a client token's), five indexes (one for each query the case queue makes) and five eval accounts. terraform/desk_alerts.tf has six log-based metrics and four alert policies, and terraform/storage.tf lets the chat service write the audit bucket. The one change is the log sink's filter, widened to copy the Desk's rows to BigQuery. Three switches would add more, and this lesson needs none of them: GCHAT_DOOR=true adds 11 for lesson 10.4's Google Chat door, DESK_ROUTER_ALERTS=true the router's three alert policies, and DESK_GATE_ALERTS=true the policy that pages when a company's model checks keep failing, for a lane where some company has the check on. Then come the images with the Desk's code, deployed by their own scripts. lesson-12.8.sh builds the chat image itself and lets the eval accounts invoke documind-chat. Last, make desk-job declares the hourly overdue scan on that chat image: a plan with DESK_JOB=true, which adds the job's three, then its apply. The whole cell takes many minutes. The flags are the ones you gave make up.

Operation: bash — run in the operator shell, in the kit (the Desk's Terraform, the three services rebuilt, the hourly job; many minutes).

Expected shape, not a promised result:

```text
...
Plan: 23 to add, 1 to change, 0 to destroy.
PASS: no deletes/replacements or existing CI trust changes. Reviewed plan: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
Review the displayed changes, then run this command with 'apply' instead of 'plan'.
PASS: selected plan, confirmed inputs, backend/workspace and state agree: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
...
Apply complete! Resources: 23 added, 1 changed, 0 destroyed.
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
...
Plan: 3 to add, 0 to change, 0 to destroy.
PASS: no deletes/replacements or existing CI trust changes. Reviewed plan: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
Review the displayed changes, then run this command with 'apply' instead of 'plan'.
PASS: selected plan, confirmed inputs, backend/workspace and state agree: .../terraform/rag-YYYYMMDDTHHMMSSZ-...tfplan
...
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.
>> documind-cases-overdue declared on asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/chat:COMMIT and scheduled hourly (desk.tf); make cases-overdue runs the same scan now
>> keep DESK_JOB=true on every later make plan, make up, make reconcile-job and make batch-job: without it their plan would delete the job, and the guard refuses it
```

**`step_02_the_eval_accounts(session)` — Your lane: the Desk's resources, accounts, queues and roles / Do it: the eval accounts**

A script cannot call the chat service as a person, so the kit has eval accounts. Each is a service account on one tenant's roster, with no project role, and make smoke-cases and this lesson's cells call as them. evalacme is an acme employee, evalgrc an acme Grievance Redressal Committee member, and evalzeta a zeta employee. make desk-operators lets you mint tokens as all five. The cell also sets CHAT and UI, notes the time in SINCE105 for step 8's log read, and defines two helpers: sa names an account, and etok mints a token as one, for the chat service.

Operation: bash — run in the operator shell, in the kit (two URLs, two helpers, the eval accounts minted as and put on rosters).

Expected shape, not a promised result:

```text
>> you@example.com may mint tokens as documind-evalacme-sa
>> you@example.com may mint tokens as documind-evalzeta-sa
>> you@example.com may mint tokens as documind-evalglobex-sa
>> you@example.com may mint tokens as documind-evalleaver-sa
>> you@example.com may mint tokens as documind-evalgrc-sa
documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is on acme
documind-evalgrc-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is on acme
...
acme: data_region=any
zeta: data_region=any
globex: data_region=in
documind-evalzeta-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com is on zeta
...
acme: data_region=any
zeta: data_region=any
globex: data_region=in
```

**`step_03_acme_s_queues_and_its_switch_as_it_stands(session)` — Your lane: the Desk's resources, accounts, queues and roles / Do it: acme's queues, and its switch as it stands**

evals/desk/queues.acme.json names acme's queues: who receives each kind of case, and the company's target in days. For POSH it lists each office's Internal Committee and its district's Local Committee. The file puts you@example.com on both offices' committees, and the sed puts your own email there instead. Then make desk, with no DESK_GATE, prints acme's switches and writes nothing.

Operation: bash — run in the operator shell, in the kit (acme's queues with your email in them, then acme's switches as they stand).

Expected shape, not a promised result:

```text
{"tenant": "acme",
 "sections": ["grc", "payroll", "people", "posh", "privacy"],
 "posh_units": ["hyderabad", "pune"],
 "posh_missing": [],
 "not_readers": ["ic hyderabad: you@example.com", "ic hyderabad: ic.hyderabad.member@example.com", "ic pune: ic.pune.presiding@example.com", "ic pune: you@example.com", "queue grc: no member holds a role that reads it", "queue privacy: no member holds a role that reads it", "queue payroll: no member holds a role that reads it", "queue people: no member holds a role that reads it"],
 "action": "written"}
{"tenant": "acme",
 "desk_gate": "rules",
 "desk_max_parts": 1,
 "desk_route": "off",
 "desk_single": null,
 "desk_off": []}
```

**`step_04_the_roles(session)` — Your lane: the Desk's resources, accounts, queues and roles / Do it: the roles**

evalgrc gets grc_member alone, so it can read and move grievances but cannot raise a case: the note says so. You get employee, so the Desk page shows you Tell the Desk and lets you raise cases. You also get the three roles that read: grievances, and the POSH cases of both offices.

Operation: bash — run in the operator shell, in the kit (the committee's account and you get your roles).

Expected shape, not a promised result:

```text
{"tenant": "acme",
 "email": "documind-evalgrc-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
 "before": ["employee"],
 "after": ["grc_member"],
 "granted": ["grc_member"],
 "revoked": ["employee"],
 "note": "no employee or leaver role: this person reaches no desk, the case desk included - add employee unless that is meant"}
{"tenant": "acme",
 "email": "you@example.com",
 "before": ["employee"],
 "after": ["employee", "grc_member", "ic_member:hyderabad", "ic_member:pune"],
 "granted": ["grc_member", "ic_member:hyderabad", "ic_member:pune"],
 "revoked": []}
```

### demo_04_the_desk_page_tell_raise_read.py

Do it: the words, and the page

**`step_01_the_words_and_the_page(session)` — The Desk page: tell, raise, read / Do it: the words, and the page**

Do it: the words, and the page

Operation: bash — run in the operator shell, in the kit (the words to paste, and the page's address).

Expected shape, not a promised result:

```text
My manager keeps making sexual comments about my body. What can I do?
https://documind-ui-NUMBER.asia-south1.run.app   <- open it signed in as you@example.com, then choose Desk
```

### demo_05_one_fixed_reply_at_every_door.py

No lane and no cost: the cell imports the kit's rules and runs them on the smoke's disclosure, a near miss, a plain question and two numbers. The disclosure to /v1/stream and /v1/query as acme, with tok's token for documind-ui-sa, the account make smoke calls as. The cell takes the words from the smoke's own file. The same words to the chat service as evalacme, asking for the langchain brain, which would send them to Gemini first. The cell also prints case_offer, the field the Desk page reads.

**`step_01_the_gate_on_your_machine(session)` — One fixed reply at every door / Do it: the gate on your machine**

No lane and no cost: the cell imports the kit's rules and runs them on the smoke's disclosure, a near miss, a plain question and two numbers.

Operation: bash — run in the operator shell, in the kit (gate() and mask() on your machine; no lane, no cost).

Manual action: In the deployed UI, signed in as yourself, choose Desk: acme has the gate's rules with nothing switched on, and your roles are read on every request, so there is nothing to wait for. Paste the sentence the previous section printed into Tell the Desk and Send: the fixed reply comes back and the POSH card opens under Raise a case. Choose Hyderabad and yourself, and Create a confidential record; then, under What is it about?, raise a grievance, check it and Send; in Your inbox, change the grievance to Acknowledged and Update. Type done to run the gate on your machine and through both doors.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
gate posh   mask []        My manager keeps making sexual comments about my body. What can I do?
  gate None   mask []        Can I file a POSH complaint after three months?
  gate None   mask []        Can I carry forward my earned leave?
  gate None   mask ['card']  Please refund the hotel booking to my card [card no.].
  gate None   mask []        My Aadhaar 2234 5678 9012 is on the travel form.
  rules 2026-10-01.4
```

**`step_02_rag_api_s_door(session)` — One fixed reply at every door / Do it: rag-api's door**

The disclosure to /v1/stream and /v1/query as acme, with tok's token for documind-ui-sa, the account make smoke calls as. The cell takes the words from the smoke's own file.

Operation: bash — run in the operator shell, in the kit (the disclosure to rag-api's /v1/stream and /v1/query, as documind-ui-sa).

Expected shape, not a promised result:

```text
/v1/stream text/event-stream; charset=utf-8 | event: token then event: done
    token: It sounds as if this may be about sexual harassment at work. (530 characters in all)
    done:  {'model': 'none', 'backend': 'desk_gate', 'cost_usd': 0.0, 'tokens_in': 0, 'tokens_out': 0, 'cache_hit': 'none'}
  /v1/query  application/json | {'model': 'none', 'backend': 'desk_gate', 'cost_usd': 0.0, 'answerable': False, 'confidence': 'low', 'citations': []}
```

**`step_03_the_chat_door(session)` — One fixed reply at every door / Do it: the chat door**

The same words to the chat service as evalacme, asking for the langchain brain, which would send them to Gemini first. The cell also prints case_offer, the field the Desk page reads.

Operation: bash — run in the operator shell, in the kit (the same words to the chat service, as an acme employee, asking for an agent brain).

Expected shape, not a promised result:

```text
brain desk_gate  model none  tool_calls []  citations []  model_calls 0  Rs 0.0
  case_offer {'case_type': 'posh'}
  It sounds as if this may be about sexual harassment at work. DocuMind does not answer this itself: it did not search its documents for this or write an answer to it.
  Under the Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013, your employer's Internal Committee receives complaints. Each district also has a Local Committee, which receives complaints in the cases the Act names. You choose what to share with them.
  If the Act does not cover you, your company's own policy may still apply.
```

### demo_06_roles_and_cases_in_the_code.py

No lane and no cost: five of commands/tests/test_cases.py's tests, run against its fake Firestore and fake audit bucket. Who holds what; an expired draft is 410; nobody else can tell a case exists; a POSH case holds no text, and one press opens one; and the audit actor is a case reference.

**`step_01_five_of_the_queue_s_tests(session)` — Roles and cases, in the code / Do it: five of the queue's tests**

No lane and no cost: five of commands/tests/test_cases.py's tests, run against its fake Firestore and fake audit bucket. Who holds what; an expired draft is 410; nobody else can tell a case exists; a POSH case holds no text, and one press opens one; and the audit actor is a case reference.

Operation: bash — run in the operator shell, in the kit (five of the case queue's offline tests; no lane, no cost).

Expected shape, not a promised result:

```text
test_a_posh_case_holds_no_text_and_one_press_opens_one (commands.tests.test_cases.CaseTests.test_a_posh_case_holds_no_text_and_one_press_opens_one) ... ok
test_an_expired_draft_is_410 (commands.tests.test_cases.CaseTests.test_an_expired_draft_is_410) ... ok
test_nobody_else_can_tell_a_case_exists (commands.tests.test_cases.CaseTests.test_nobody_else_can_tell_a_case_exists) ... ok
test_the_audit_actor_is_a_case_reference (commands.tests.test_cases.CaseTests.test_the_audit_actor_is_a_case_reference) ... ok
test_who_holds_what (commands.tests.test_cases.RolesTests.test_who_holds_what) ... ok

----------------------------------------------------------------------
Ran 5 tests in N.NNNs

OK
```

### demo_07_the_case_routes_over_rest.py

The cell first asks what evalacme may raise. It raises a grievance as evalacme and sends it twice with one token. Then it tries a second token. evalgrc reads its inbox, then asks for the offer. evalzeta and the outsider ask for the case. The raiser tries to close it, and the committee acknowledges and closes it. It keeps the id in ~/lesson105_case.txt for step 8. smoke/smoke_cases.py checks the whole queue in one run, as the eval accounts, with your email as the Internal Committee member its POSH press names. It closes and withdraws what it opens. make cases lists a tenant's open cases, soonest due first, for you to chase. A sensitive case's type and queue both show as "sensitive", since a queue such as ic:hyderabad would give the type away, and no person is named. make cases-overdue runs the hourly job's scan once, as you.

**`step_01_a_case_end_to_end(session)` — The case routes, over REST / Do it: a case, end to end**

The cell first asks what evalacme may raise. It raises a grievance as evalacme and sends it twice with one token. Then it tries a second token. evalgrc reads its inbox, then asks for the offer. evalzeta and the outsider ask for the case. The raiser tries to close it, and the committee acknowledges and closes it. It keeps the id in ~/lesson105_case.txt for step 8.

Operation: bash — run in the operator shell, in the kit (the offer, then a case raised, confirmed twice, read by the committee, refused to others, closed).

Expected shape, not a promised result:

```text
offer      200  acme, desk_gate rules, POSH offices ['hyderabad', 'pune']
             types posh, grievance, privacy_request, exit_dues, people_query, human_requested
  draft      200  draft in grc (Grievance Redressal Committee), expires 0:30:00 after it was made
             basis Industrial Relations Code, 2020: s.4(1), s.4(5), s.4(6)
  confirm x2 200 open, 200 open: same case True, opened once True
             due 15 days, 0:00:00 after it opened: the company's own target: 15 days (case_queues.grc.sla_days)
  new token  409  this case is already open
  inbox      200  seen as documind-evalgrc-sa in acme, roles ['grc_member'], the case in it: True
  grc offer  403  your roles in this company do not include raising a case
  zeta       404  no such case
  out        403  not a member of any tenant
  raiser     403  only the case's queue changes its status
  committee  200  acknowledged
  committee  200  closed
```

**`step_02_the_live_smoke(session)` — The case routes, over REST / Do it: the live smoke**

smoke/smoke_cases.py checks the whole queue in one run, as the eval accounts, with your email as the Internal Committee member its POSH press names. It closes and withdraws what it opens.

Operation: bash — run in the operator shell, in the kit (the case queue's live smoke).

Expected shape, not a promised result:

```text
DocuMind Desk - the case queue, live
  chat: https://documind-chat-NUMBER.asia-south1.run.app
  api:  https://documind-api-NUMBER.asia-south1.run.app
  --------------------------------------------------------
  [PASS] chat door  brain=desk_gate model=none Rs 0  'It sounds as if this may be about sexual harassment at work.'
  [PASS] api door (stream)  model=none cost_usd=0 backend=desk_gate
  [PASS] draft  queue=grc expires=YYYY-MM-DDTHH:MM:SS+00:00
  [PASS] confirm, twice  one case, open, due YYYY-MM-DDTHH:MM:SS+00:00
  [PASS] inbox  status=200 roles=['grc_member'] in inbox=True
  [PASS] status acknowledged  status=200 {'case_id': 'f61615ef83f1165722a5ee805065654b', 'tenant': 'acme', 'requester': 'documind-evalacme-sa@documind-ai-YOUR-ID
  [PASS] status closed  status=200 {'case_id': 'f61615ef83f1165722a5ee805065654b', 'tenant': 'acme', 'requester': 'documind-evalacme-sa@documind-ai-YOUR-ID
  [PASS] another tenant  status=404 {'detail': 'no such case'}
  [PASS] posh, twice  one case, no text, Local Committee lc.hyderabad@example.com
  [PASS] posh withdrawn  status=200 {'case_id': '721aa2320010d00117794591262ca9bb', 'tenant': 'acme', 'requester': 'documind-evalacme-sa
  [PASS] outsider refused  status=403 {'detail': 'not a member of any tenant'}
  --------------------------------------------------------
  11 passed, 0 failed
```

**`step_03_the_operator_s_view(session)` — The case routes, over REST / Do it: the operator's view**

make cases lists a tenant's open cases, soonest due first, for you to chase. A sensitive case's type and queue both show as "sensitive", since a queue such as ic:hyderabad would give the type away, and no person is named. make cases-overdue runs the hourly job's scan once, as you.

Operation: bash — run in the operator shell, in the kit (acme's open cases, and the overdue scan the hourly job runs).

Expected shape, not a promised result:

```text
case                              type             queue            status       due_at                     state
677ddf02cb3576d1097b86284682ad71  sensitive        sensitive        open         YYYY-MM-DDTHH:MM:SS+00:00  open
b41155df5b60dd3efdb1f1a0afcd94c9  sensitive        sensitive        acknowledged YYYY-MM-DDTHH:MM:SS+00:00  open
2 open case(s): 0 due, 0 breached
{"event": "case_overdue_scan", "due": 0, "breached": 0}
```

### demo_08_the_records_the_audit_events_and_the_log_rows.py

The case from step 7, the smoke's POSH record, and two role documents, read with the Firestore client. Today's case and role events in the audit bucket, the newest six, then the latest case.open and role.grant in full. Every desk_gate row since step 3, from both services.

**`step_01_the_records(session)` — The records, the audit events and the log rows / Do it: the records**

The case from step 7, the smoke's POSH record, and two role documents, read with the Firestore client.

Operation: bash — run in the operator shell, in the kit (the case, the smoke's POSH case and two role documents, read from Firestore).

Expected shape, not a promised result:

```text
cases/70356c174ba69ae3100d3d830531f27e
    grievance closed in grc, tenant acme, source button, via direct
    summary 'Lesson 5.6 test case: please close it.'  expire_at gone  audit_pending []  token_sha256 64 hex digits
  the smoke's posh case: withdrawn in ic:hyderabad, unit hyderabad, contacts ['you@example.com'], summary None, question_sha256 None
  tenants/acme/roles/you@...: ['employee', 'grc_member', 'ic_member:hyderabad', 'ic_member:pune'], set by you@example.com
  tenants/acme/roles/documind-evalgrc-sa@...: ['grc_member'], set by you@example.com
```

**`step_02_the_audit_events(session)` — The records, the audit events and the log rows / Do it: the audit events**

Today's case and role events in the audit bucket, the newest six, then the latest case.open and role.grant in full.

Operation: bash — run in the operator shell, in the kit (today's case and role events in the audit bucket).

Expected shape, not a promised result:

```text
14 case and role events today; the last six:
    case.close-04b5496c-0c9a-4c8e-8eb8-8a93b0cb9d4d.json
    case.open-62b1d84e-eb7f-4f4d-815a-2cc512343c7a.json
    case.update-4251c1f7-5d9a-4f35-a81a-95bfa63619dd.json
    case.close-09c060c0-272f-4987-b4a7-cbfb9cae321c.json
    case.open-57204f61-542c-4dd8-83b7-279e956f644e.json
    case.close-08415b1b-e70e-463d-95d9-8c6746037e67.json
  case.open: actor {'tenant_id': 'acme', 'case_ref': 'case:721aa2320010d00117794591262ca9bb'}  target {'case_id': '721aa2320010d00117794591262ca9bb', 'case_type': 'sensitive'}  meta {'status': 'open', 'source': 'button', 'via': 'direct'}
  role.grant: actor {'tenant_id': 'acme', 'email': 'you@example.com'}  target {'email': 'you@example.com', 'roles': ['grc_member', 'ic_member:hyderabad', 'ic_member:pune']}  meta {}
```

**`step_03_the_log_rows(session)` — The records, the audit events and the log rows / Do it: the log rows**

Every desk_gate row since step 3, from both services.

Operation: bash — run in the operator shell, in the kit (the desk_gate rows since step 3; reads only).

Expected shape, not a promised result:

```text
documind-chat surface chat    tenant acme  user None  class sensitive  rules 2026-10-01.4
  documind-api  surface stream  tenant acme  user None  class sensitive  rules 2026-10-01.4
  documind-api  surface query   tenant acme  user None  class sensitive  rules 2026-10-01.4
  documind-chat surface chat    tenant acme  user None  class sensitive  rules 2026-10-01.4
  documind-chat surface chat    tenant acme  user None  class sensitive  rules 2026-10-01.4
  documind-api  surface stream  tenant acme  user None  class sensitive  rules 2026-10-01.4
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_5.6_Case_Desk_WIX.html`. All 54 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `ffa6d70e006958e3f835fa26f78e425518dd3f27`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
