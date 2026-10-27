# Lesson 5.8: Pause, approve, clarify and escalate: human in the loop

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_your_lane_the_people_team_s_reader_and_a_request_for_a_person_on_the_desk_page.py](demo_03_your_lane_the_people_team_s_reader_and_a_request_for_a_person_on_the_desk_page.py) | Your lane: the People team's reader, and a request for a person on the Desk page |
| 4 | [demo_04_the_pause_in_the_kit_approval_py.py](demo_04_the_pause_in_the_kit_approval_py.py) | The pause, in the kit: approval.py |
| 5 | [demo_05_pause_refuse_approve_and_resume_on_your_machine.py](demo_05_pause_refuse_approve_and_resume_on_your_machine.py) | Pause, refuse, approve and resume on your machine |
| 6 | [demo_06_escalate_and_clarify_over_rest_on_your_lane.py](demo_06_escalate_and_clarify_over_rest_on_your_lane.py) | Escalate and clarify over REST, on your lane |
| 7 | [demo_07_the_rows_the_case_and_your_role_read_directly.py](demo_07_the_rows_the_case_and_your_role_read_directly.py) | The rows, the case and your role, read directly |
| 8 | [demo_08_the_approval_wired_in_a_withdrawal_paused_on_your_lane_decided_over_rest_run_by.py](demo_08_the_approval_wired_in_a_withdrawal_paused_on_your_lane_decided_over_rest_run_by.py) | The approval wired in: a withdrawal paused on your lane, decided over REST, run by you |

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

### demo_03_your_lane_the_people_team_s_reader_and_a_request_for_a_person_on_the_desk_page.py

A request for a person goes to acme's people queue, the People team's. A case there is read by whoever holds people_ops, and nobody on your lane holds it yet: lesson 5.6 gave you the roles that read grievances and POSH cases. So far a request for a person would reach no one. The cell sets the names the later steps use, notes the time in SINCE108 for step 7's log read, and gives you people_ops beside the four roles you have. ROLES= sets exactly the roles it lists, so it names all five.

**`step_01_the_people_team_s_reader(session)` — Your lane: the People team's reader, and a request for a person on the Desk page / Do it: the People team's reader**

A request for a person goes to acme's people queue, the People team's. A case there is read by whoever holds people_ops, and nobody on your lane holds it yet: lesson 5.6 gave you the roles that read grievances and POSH cases. So far a request for a person would reach no one. The cell sets the names the later steps use, notes the time in SINCE108 for step 7's log read, and gives you people_ops beside the four roles you have. ROLES= sets exactly the roles it lists, so it names all five.

Operation: bash — run in the operator shell, in the kit (the names the lane steps use, then people_ops beside your four roles).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/roles.txt]
```

### demo_04_the_pause_in_the_kit_approval_py.py

make approval-check is commands/approval-check.sh. It makes ~/graph-venv if it is missing (lesson 5.4 made it), installs the chat image's pins and the SQLite checkpointer, langgraph-checkpoint-sqlite 3.1.1, the version services/chat/requirements-local.txt pins, and runs commands/tests/test_approvals.py. CI's chat-pins step runs the same file. It needs no credential, no network after the install, and costs nothing.

**`step_01_the_kit_s_own_tests(session)` — The pause, in the kit: approval.py / Do it: the kit's own tests**

make approval-check is commands/approval-check.sh. It makes ~/graph-venv if it is missing (lesson 5.4 made it), installs the chat image's pins and the SQLite checkpointer, langgraph-checkpoint-sqlite 3.1.1, the version services/chat/requirements-local.txt pins, and runs commands/tests/test_approvals.py. CI's chat-pins step runs the same file. It needs no credential, no network after the install, and costs nothing.

Operation: bash — run in the operator shell, in the kit (the kit's own tests, offline; the first run makes or completes ~/graph-venv).

Expected shape, not a promised result:

```text
test_a_rejection_errors_that_call_only (commands.tests.test_approvals.Approvals.test_a_rejection_errors_that_call_only) ... ok
test_a_second_process_resumes_the_turn_from_the_sqlite_file (commands.tests.test_approvals.Approvals.test_a_second_process_resumes_the_turn_from_the_sqlite_file) ... ok
test_a_turn_with_nothing_to_approve_does_not_pause (commands.tests.test_approvals.Approvals.test_a_turn_with_nothing_to_approve_does_not_pause) ... ok
test_ask_user_is_answered_by_the_person_who_asked (commands.tests.test_approvals.Approvals.test_ask_user_is_answered_by_the_person_who_asked) ... ok
test_offer_case_writes_nothing (commands.tests.test_approvals.Approvals.test_offer_case_writes_nothing) ... ok
test_the_approval_line_above_interrupt_is_written_twice (commands.tests.test_approvals.Approvals.test_the_approval_line_above_interrupt_is_written_twice)
The page's Change-it: the kit writes "approval asked" below interrupt(), once. Moved above it, a resume ... ok
test_the_graph_pauses_for_a_second_person_and_resumes_on_approval (commands.tests.test_approvals.Approvals.test_the_graph_pauses_for_a_second_person_and_resumes_on_approval) ... ok
test_the_middleware_form_adds_a_node_and_pauses_alike (commands.tests.test_approvals.Approvals.test_the_middleware_form_adds_a_node_and_pauses_alike) ... ok
test_the_requesters_own_approval_is_refused (commands.tests.test_approvals.Approvals.test_the_requesters_own_approval_is_refused) ... ok
test_who_may_approve_is_read_from_the_tenants_roster (commands.tests.test_approvals.Approvals.test_who_may_approve_is_read_from_the_tenants_roster) ... ok
test_withdraw_document_never_runs_without_a_second_persons_approval (commands.tests.test_approvals.Approvals.test_withdraw_document_never_runs_without_a_second_persons_approval) ... ok
test_it_writes_no_audit_event (commands.tests.test_approvals.Wiring.test_it_writes_no_audit_event)
Workshop lesson 4.8 lists every audit action the kit writes, from the emit literals in its runtime files ... ok
test_make_its_script_and_ci_run_this_file (commands.tests.test_approvals.Wiring.test_make_its_script_and_ci_run_this_file) ... ok
test_one_module_in_the_service_imports_it_behind_the_switch (commands.tests.test_approvals.Wiring.test_one_module_in_the_service_imports_it_behind_the_switch)
Since 13 October 2026 (workshop lesson 5.8's wired approval) approval_routes.py imports the module, and ... ok
test_the_versions_it_was_verified_against_are_the_pins (commands.tests.test_approvals.Wiring.test_the_versions_it_was_verified_against_are_the_pins) ... ok

----------------------------------------------------------------------
Ran 15 tests in N.NNNs

OK
```

### demo_05_pause_refuse_approve_and_resume_on_your_machine.py

The cell builds the kit's approval graph on a scripted model that asks for withdraw_document, with an in-memory checkpointer and an executor that only prints. It streams the turn to its pause and lists what waits. Then it tries Asha's own approval, and Ravi's. The pause is data in the checkpointer, not a request waiting in memory. The first process pauses the turn into a SQLite file, ~/lesson108_threads.db, through SqliteSaver, the local lane's checkpointer, and ends. The second process is a new interpreter: it builds a new graph on the same file, finds the waiting call, and resumes it with Ravi's approval. The same graph, now with a scripted model that asks Asha which rule applies to her. The handbook's NP-03 gives a confirmed employee at grade E3 or above 60 days' notice, and its PB-02 gives 15 days during probation. Ravi tries to answer for her, Asha tries to approve, then Asha answers. A resumed node runs again from its first line. The kit writes its "approval asked" line below interrupt(), so it is written once, at the resume. The first cell defines twice108, which pauses one withdrawal, approves it, and counts that line at each point. The second cell moves the line above interrupt(), from line 364 to line 361, and runs twice108 again. Then it puts the kit's file back with git, so the setup section's git pull next time is not refused.

**`step_01_a_withdrawal_paused_and_approved(session)` — Pause, refuse, approve and resume on your machine / Do it: a withdrawal, paused and approved**

The cell builds the kit's approval graph on a scripted model that asks for withdraw_document, with an in-memory checkpointer and an executor that only prints. It streams the turn to its pause and lists what waits. Then it tries Asha's own approval, and Ravi's.

Operation: bash — run in the operator shell, in the kit (a withdrawal paused, refused to its requester, approved by a second person; no network, no model).

Expected shape, not a promised result:

```text
ran: agent
  ran: __interrupt__
  waiting: withdraw_document {'name': 'hr_policy_2026.md'} call c0, takes ['approve', 'reject'], asked by asha@example.com
  asha approves: PermissionError - the person who asked cannot approve their own request: a second person must
  still waiting: ['withdraw_document']
  log: approval asked: withdraw_document
  withdraw() called with {'tenant': 'acme', 'name': 'hr_policy_2026.md', 'requested_by': 'asha@example.com', 'approved_by': 'ravi@example.com'}
  ravi approves: withdraw_document success {"status": "withdrawal_started", "document": "acme/hr_policy_2026.md", "undo": "make restore SOURCE=acme/hr_policy_2026.md"}
  path: __start__ -> agent -> approve -> tools -> agent -> END
  waiting now: []
```

**`step_02_a_second_process_resumes_it(session)` — Pause, refuse, approve and resume on your machine / Do it: a second process resumes it**

The pause is data in the checkpointer, not a request waiting in memory. The first process pauses the turn into a SQLite file, ~/lesson108_threads.db, through SqliteSaver, the local lane's checkpointer, and ends. The second process is a new interpreter: it builds a new graph on the same file, finds the waiting call, and resumes it with Ravi's approval.

Operation: bash — run in the operator shell, in the kit (one process pauses the turn into a file, a second process resumes it).

Expected shape, not a promised result:

```text
process 1: paused before ('approve',) | waiting: ['withdraw_document']
process 1: ends; the paused turn is in the file
process 2: a new graph on the same file finds: ['withdraw_document']
process 2: log: approval asked: withdraw_document
process 2: withdraw() called with {'tenant': 'acme', 'name': 'hr_policy_2026.md', 'requested_by': 'asha@example.com', 'approved_by': 'ravi@example.com'}
process 2: answer: Withdrawn, from the second process. | waiting now: []
```

**`step_03_a_question_only_the_asker_answers(session)` — Pause, refuse, approve and resume on your machine / Do it: a question only the asker answers**

The same graph, now with a scripted model that asks Asha which rule applies to her. The handbook's NP-03 gives a confirmed employee at grade E3 or above 60 days' notice, and its PB-02 gives 15 days during probation. Ravi tries to answer for her, Asha tries to approve, then Asha answers.

Operation: bash — run in the operator shell, in the kit (a clarifying question, answered only by the person who asked).

Expected shape, not a promised result:

```text
waiting: ask_user takes ['respond'], for asha@example.com: Are you a confirmed employee at grade E3 or above, or still on probation?
  ravi sends respond: PermissionError - only the person who asked may answer their own question
  asha sends approve: ValueError - ask_user takes respond, not 'approve'
  asha answers: the model reads ask_user's result 'I am still on probation.' (success)
  path: __start__ -> agent -> approve -> agent -> END
```

**`step_04_change_it_the_approval_line_above_interrup(session)` — Pause, refuse, approve and resume on your machine / Change it: the approval line above interrupt()**

A resumed node runs again from its first line. The kit writes its "approval asked" line below interrupt(), so it is written once, at the resume. The first cell defines twice108, which pauses one withdrawal, approves it, and counts that line at each point. The second cell moves the line above interrupt(), from line 364 to line 361, and runs twice108 again. Then it puts the kit's file back with git, so the setup section's git pull next time is not refused.

Operation: bash — run in the operator shell, in the kit (defines twice108, then runs it on the kit as it is).

Expected shape, not a promised result:

```text
at the pause:      0 approval line(s)
  after the resume:  1 approval line(s), 1 withdrawal(s)
```

**`step_05_change_it_the_approval_line_above_interrup(session)` — Pause, refuse, approve and resume on your machine / Change it: the approval line above interrupt()**

A resumed node runs again from its first line. The kit writes its "approval asked" line below interrupt(), so it is written once, at the resume. The first cell defines twice108, which pauses one withdrawal, approves it, and counts that line at each point. The second cell moves the line above interrupt(), from line 364 to line 361, and runs twice108 again. Then it puts the kit's file back with git, so the setup section's git pull next time is not refused.

Operation: bash — run in the operator shell, in the kit (the Change-it: one line moved, twice108 again, then the kit restored).

Expected shape, not a promised result:

```text
moved line 364 up to line 361, just above: answer = interrupt(request)
  at the pause:      1 approval line(s)
  after the resume:  2 approval line(s), 1 withdrawal(s)
approval.py is the kit's again
```

### demo_06_escalate_and_clarify_over_rest_on_your_lane.py

The cell sends the gate's own request for a person on one session, then one of its near misses, "How do I contact HR about payroll?", which gate() reads as a question about a process and lets through. Then it raises the case the first reply offered and sends it with a token. Last, it withdraws the case as the person who raised it. It keeps the case's id in ~/lesson108_case.txt for step 7. Three turns. The handbook answers "What is my notice period?" two ways: 60 days for a confirmed employee at grade E3 or above (NP-03), and 15 days during probation (PB-02). The second turn gives, on the same session, the fact the first lacked. The third sends the same reply in a new session.

**`step_01_escalate(session)` — Escalate and clarify over REST, on your lane / Do it: escalate**

The cell sends the gate's own request for a person on one session, then one of its near misses, "How do I contact HR about payroll?", which gate() reads as a question about a process and lets through. Then it raises the case the first reply offered and sends it with a token. Last, it withdraws the case as the person who raised it. It keeps the case's id in ~/lesson108_case.txt for step 7.

Operation: bash — run in the operator shell, in the kit (a request for a person and a near miss, as documind-evalacme-sa; then the case).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/escalate.txt]
```

**`step_02_clarify(session)` — Escalate and clarify over REST, on your lane / Do it: clarify**

Three turns. The handbook answers "What is my notice period?" two ways: 60 days for a confirmed employee at grade E3 or above (NP-03), and 15 days during probation (PB-02). The second turn gives, on the same session, the fact the first lacked. The third sends the same reply in a new session.

Operation: bash — run in the operator shell, in the kit (a question, the reply on the same session, the reply in a new session).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/clarify.txt]
```

### demo_07_the_rows_the_case_and_your_role_read_directly.py

The chat service's chat and desk_gate rows since step 3, from Cloud Logging. The cell names each account by the part of its email before the @. make cases lists acme's open cases, soonest due first. Then the cell reads step 6's case and your role document from Firestore.

**`step_01_the_log_rows(session)` — The rows, the case and your role, read directly / Do it: the log rows**

The chat service's chat and desk_gate rows since step 3, from Cloud Logging. The cell names each account by the part of its email before the @.

Operation: bash — run in the operator shell, in the kit (the chat service's chat and desk_gate rows since step 3; reads only).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rows.txt]
```

**`step_02_the_case_and_your_role(session)` — The rows, the case and your role, read directly / Do it: the case and your role**

make cases lists acme's open cases, soonest due first. Then the cell reads step 6's case and your role document from Firestore.

Operation: bash — run in the operator shell, in the kit (acme's open cases, then step 6's case and your role document, from Firestore).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/records.txt]
```

### demo_08_the_approval_wired_in_a_withdrawal_paused_on_your_lane_decided_over_rest_run_by.py

The whole flow runs on the kit's own chat service with a fake Firestore and a scripted model, at Rs 0: the switch off, then on; the pause and its record; the hold; the requester's own approval refused; another company's approver and a colleague without the role seeing nothing; the second person's approval; a rejection beside a search; a question only the asker answers; an expired record, and the hold ending its pause; a lost pause; and --approved on the record. 18 tests, in ~/graph-venv from step 4. make agent-actions writes agent_actions into acme's tenant_settings, beside the Desk's switches, and prints them; the chat service reads it within a minute. make roles gives documind-evalacme-sa the doc_approver role beside employee: the eval account stands in for a colleague who may approve, as it stood in for an acme employee in lesson 5.6. The requester will be documind-ui-sa, on acme's roster since lesson 5.1's smoke. make smoke-approval runs the flow once against your chat service, printing each step. As documind-ui-sa it asks the LangGraph brain to withdraw townhall_2026_q1.md, a small acme document: the turn pauses, and the reply carries the record. The same session's next question is held. The requester's own approval is refused. documind-evalzeta-sa, on zeta's roster, cannot tell the record exists. The approver's list shows it. documind-evalacme-sa approves it, and the turn resumes: the tool runs, records the approved withdrawal, and the model answers that the operator will run it. A second decision is refused. Then a second withdrawal on a new session, which the approver rejects with a reason: the call errors alone and the model says nothing was withdrawn. The smoke withdraws nothing; it ends by printing your next two commands. The approval queued the work; you run it. The cell reads the approved record's id as the requester, runs make withdraw-run for it, and lists acme's sources, where the document's ledger row now says withdrawn. Acme's approval records from Firestore, oldest first, and today's approval events in the audit bucket, read without the chat service. make restore lifts the tombstone, as lesson 1.7 showed, and the worker returns the document. Then make agent-actions writes off, and acme's LangGraph brain is again the one lessons 5.4, 5.5 and 5.7 show, within a minute.

**`step_01_the_kit_s_own_tests_offline(session)` — The approval wired in: a withdrawal paused on your lane, decided over REST, run by you / Do it: the kit's own tests, offline**

The whole flow runs on the kit's own chat service with a fake Firestore and a scripted model, at Rs 0: the switch off, then on; the pause and its record; the hold; the requester's own approval refused; another company's approver and a colleague without the role seeing nothing; the second person's approval; a rejection beside a search; a question only the asker answers; an expired record, and the hold ending its pause; a lost pause; and --approved on the record. 18 tests, in ~/graph-venv from step 4.

Operation: bash — run in the operator shell, in the kit (the wired approval's own tests, offline, in ~/graph-venv from step 4).

Expected shape, not a promised result:

```text
test_an_event_the_bucket_refused_waits_on_the_record (commands.tests.test_approval_wired.Records.test_an_event_the_bucket_refused_waits_on_the_record) ... ok
test_expired_is_410_and_decided_is_409_checked_in_code (commands.tests.test_approval_wired.Records.test_expired_is_410_and_decided_is_409_checked_in_code) ... ok
test_one_pause_is_one_record_with_one_event (commands.tests.test_approval_wired.Records.test_one_pause_is_one_record_with_one_event) ... ok
test_recheck_refuses_before_the_tombstone (commands.tests.test_approval_wired.Records.test_recheck_refuses_before_the_tombstone) ... ok
test_the_executor_records_and_withdraws_nothing (commands.tests.test_approval_wired.Records.test_the_executor_records_and_withdraws_nothing) ... ok
test_what_a_decision_amounts_to (commands.tests.test_approval_wired.Records.test_what_a_decision_amounts_to) ... ok
test_who_may_read (commands.tests.test_approval_wired.Records.test_who_may_read) ... ok
test_a_pause_that_is_gone_is_lost (commands.tests.test_approval_wired.WiredService.test_a_pause_that_is_gone_is_lost) ... ok
test_a_question_is_the_requesters_alone (commands.tests.test_approval_wired.WiredService.test_a_question_is_the_requesters_alone) ... ok
test_a_rejection_errors_that_call_alone_and_the_requester_may_cancel (commands.tests.test_approval_wired.WiredService.test_a_rejection_errors_that_call_alone_and_the_requester_may_cancel) ... ok
test_a_withdrawal_pauses_is_held_refused_to_its_requester_and_approved_by_a_second_person (commands.tests.test_approval_wired.WiredService.test_a_withdrawal_pauses_is_held_refused_to_its_requester_and_approved_by_a_second_person) ... ok
test_an_expired_record_is_410_and_the_hold_then_lets_the_next_question_through (commands.tests.test_approval_wired.WiredService.test_an_expired_record_is_410_and_the_hold_then_lets_the_next_question_through) ... ok
test_offer_case_reaches_the_response_and_writes_nothing (commands.tests.test_approval_wired.WiredService.test_offer_case_reaches_the_response_and_writes_nothing) ... ok
test_reconcile_approved_runs_on_the_record (commands.tests.test_approval_wired.WiredService.test_reconcile_approved_runs_on_the_record) ... ok
test_switch_off_is_the_brain_lessons_5_4_and_5_7_show (commands.tests.test_approval_wired.WiredService.test_switch_off_is_the_brain_lessons_5_4_and_5_7_show) ... ok
test_one_call_in_chat_and_one_install_line_reach_the_switch (commands.tests.test_approval_wired.Wiring.test_one_call_in_chat_and_one_install_line_reach_the_switch) ... ok
test_reconcile_approved_rechecks_then_reenters_the_retire_branch (commands.tests.test_approval_wired.Wiring.test_reconcile_approved_rechecks_then_reenters_the_retire_branch) ... ok
test_the_role_the_actions_and_the_targets (commands.tests.test_approval_wired.Wiring.test_the_role_the_actions_and_the_targets) ... ok

----------------------------------------------------------------------
Ran 18 tests in N.NNNs

OK
```

**`step_02_switch_acme_on_and_name_the_second_person(session)` — The approval wired in: a withdrawal paused on your lane, decided over REST, run by you / Do it: switch acme on, and name the second person**

make agent-actions writes agent_actions into acme's tenant_settings, beside the Desk's switches, and prints them; the chat service reads it within a minute. make roles gives documind-evalacme-sa the doc_approver role beside employee: the eval account stands in for a colleague who may approve, as it stood in for an acme employee in lesson 5.6. The requester will be documind-ui-sa, on acme's roster since lesson 5.1's smoke.

Operation: bash — run in the operator shell, in the kit (acme's agent_actions to approval; doc_approver for documind-evalacme-sa).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/switch.txt]
```

**`step_03_the_flow_live(session)` — The approval wired in: a withdrawal paused on your lane, decided over REST, run by you / Do it: the flow, live**

make smoke-approval runs the flow once against your chat service, printing each step. As documind-ui-sa it asks the LangGraph brain to withdraw townhall_2026_q1.md, a small acme document: the turn pauses, and the reply carries the record. The same session's next question is held. The requester's own approval is refused. documind-evalzeta-sa, on zeta's roster, cannot tell the record exists. The approver's list shows it. documind-evalacme-sa approves it, and the turn resumes: the tool runs, records the approved withdrawal, and the model answers that the operator will run it. A second decision is refused. Then a second withdrawal on a new session, which the approver rejects with a reason: the call errors alone and the model says nothing was withdrawn. The smoke withdraws nothing; it ends by printing your next two commands.

Operation: bash — run in the operator shell, in the kit (the whole flow once, against your chat service; about Rs 10-15).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke_approval.txt]
```

**`step_04_run_the_approved_withdrawal(session)` — The approval wired in: a withdrawal paused on your lane, decided over REST, run by you / Do it: run the approved withdrawal**

The approval queued the work; you run it. The cell reads the approved record's id as the requester, runs make withdraw-run for it, and lists acme's sources, where the document's ledger row now says withdrawn.

Operation: bash — run in the operator shell, in the kit (the approved record's id, your run of it, and acme's sources).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/withdraw.txt]
```

**`step_05_the_records_and_the_events_read_directly(session)` — The approval wired in: a withdrawal paused on your lane, decided over REST, run by you / Do it: the records and the events, read directly**

Acme's approval records from Firestore, oldest first, and today's approval events in the audit bucket, read without the chat service.

Operation: bash — run in the operator shell, in the kit (acme's approval records and today's approval events, from Firestore and the bucket).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/approvals.txt]
```

**`step_06_bring_the_document_back_and_switch_acme_of(session)` — The approval wired in: a withdrawal paused on your lane, decided over REST, run by you / Do it: bring the document back, and switch acme off**

make restore lifts the tombstone, as lesson 1.7 showed, and the worker returns the document. Then make agent-actions writes off, and acme's LangGraph brain is again the one lessons 5.4, 5.5 and 5.7 show, within a minute.

Operation: bash — run in the operator shell, in the kit (the document back, and acme's switch off).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/restore.txt]
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_5.8_Human_In_Loop_WIX.html`. All 62 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `e4f5251946e9173b1c0555451a11ffdeaa9dec61`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
