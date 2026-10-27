# Lesson 2.5: Rewrite the query before retrieval, and measure it

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_chat_page_with_the_stage_off_the_stream_never_asks_for_a_rewrite.py](demo_03_the_chat_page_with_the_stage_off_the_stream_never_asks_for_a_rewrite.py) | The Chat page with the stage off: the stream never asks for a rewrite |
| 4 | [demo_04_the_stage_in_the_kit_the_call_the_guard_one_line_in_v1_query_and_two_lines_that.py](demo_04_the_stage_in_the_kit_the_call_the_guard_one_line_in_v1_query_and_two_lines_that.py) | The stage in the kit: the call, the guard, one line in /v1/query, and two lines that did not change |
| 5 | [demo_05_rewrite_called_directly_one_question_one_call_one_outcome.py](demo_05_rewrite_called_directly_one_question_one_call_one_outcome.py) | rewrite() called directly: one question, one call, one outcome |
| 6 | [demo_06_the_stage_on_a_candidate_query_rewrite_on_a_forced_failure_and_the_undo.py](demo_06_the_stage_on_a_candidate_query_rewrite_on_a_forced_failure_and_the_undo.py) | The stage on a candidate: QUERY_REWRITE=on, a forced failure, and the undo |
| 7 | [demo_07_the_measurement_the_rewrite_arm_against_the_lane_on_the_golden_rows_and_the_para.py](demo_07_the_measurement_the_rewrite_arm_against_the_lane_on_the_golden_rows_and_the_para.py) | The measurement: the rewrite arm against the lane, on the golden rows and the paraphrases |
| 8 | [demo_08_change_it_delete_the_prompt_s_literal_rule_and_measure_the_guard_where_the_stage.py](demo_08_change_it_delete_the_prompt_s_literal_rule_and_measure_the_guard_where_the_stage.py) | Change it: delete the prompt's literal rule and measure the guard; where the stage cannot go |

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

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The stage's two settings and the retrieval backend live in the API's environment. A name the service does not set is unset here rather than exported empty, because the kit's settings class reads an empty variable as a value, and an empty QUERY_REWRITE is a value the validator refuses. svc_env is the helper lessons 2.2 to 2.4 define; step 6 reads the template with it again. Step 7's ablation reranks through the Ranking API's client at the API's own pin; the pip line is harmless if it is already there.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

**`step_02_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

Calls from the shell impersonate documind-ui-sa, the UI's own account, which make roster put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. otok mints a token for documind-outsider-sa, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible. The stage's two settings and the retrieval backend live in the API's environment. A name the service does not set is unset here rather than exported empty, because the kit's settings class reads an empty variable as a value, and an empty QUERY_REWRITE is a value the validator refuses. svc_env is the helper lessons 2.2 to 2.4 define; step 6 reads the template with it again. Step 7's ablation reranks through the Ranking API's client at the API's own pin; the pip line is harmless if it is already there.

Operation: bash — run in the operator shell, in $DEMO_ROOT, once per shell.

IDE adaptation: Read literal environment values as JSON from the serving revision; absent keys are unset. Repeated text parsing is removed.

Expected shape, not a promised result:

```text
rewrite: off (default)  model: gemini-3.1-flash-lite (default)  backend: vector
```

### demo_03_the_chat_page_with_the_stage_off_the_stream_never_asks_for_a_rewrite.py

In the Chat page, signed in as yourself, ask: How much can I claim per trip for domestic travel? It is a paraphrase of golden row lk-01, whose answer must contain 40,000. Then read the API's log for the last ten minutes.

**`step_01_a_paraphrase_in_the_chat_page_then_the_log(session)` — The Chat page with the stage off: the stream never asks for a rewrite / Do it: a paraphrase in the Chat page, then the log**

In the Chat page, signed in as yourself, ask: How much can I claim per trip for domestic travel? It is a paraphrase of golden row lk-01, whose answer must contain 40,000. Then read the API's log for the last ten minutes.

Operation: bash — run in the operator shell, after the question in the Chat page (reads the API's log; changes nothing).

Manual action: In the deployed UI's Chat page, signed in as yourself, ask: How much can I claim per trip for domestic travel? Wait for the cited answer, then type done to read the API's log for the minutes since.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ui.txt]
```

### demo_04_the_stage_in_the_kit_the_call_the_guard_one_line_in_v1_query_and_two_lines_that.py

The cell asks the kit's guard about one question and five rewrites of it: a faithful one, the same one spelt with an en dash, the rupee sign and Devanagari digits, the amount written without its comma, the unit given another word, and the section spelt out. Nothing leaves the machine. evals/tests/test_query_rewrite.py holds 20 tests that need neither a model nor a lane: the guard on the design's examples and on the golden rows, every outcome against a fake client, the request against google-genai's own config class, the line with no question text, search_query() lifted from rewrite.py with the switch off and on, and the ablation's rewrite arm and paraphrase rows against a stand-in lane. The pipe keeps the summary and drops the timing.

**`step_01_offline_the_guard_on_the_module_s_own_exam(session)` — The stage in the kit: the call, the guard, one line in /v1/query, and two lines that did not change / Do it, offline: the guard on the module's own example**

The cell asks the kit's guard about one question and five rewrites of it: a faithful one, the same one spelt with an en dash, the rupee sign and Devanagari digits, the amount written without its comma, the unit given another word, and the section spelt out. Nothing leaves the machine.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: no call leaves the machine).

Expected shape, not a promised result:

```text
the question's literals: ['lv-07', 's.53', 'rs 52,000', '45 days']
kept    leave encashment LV-07 s.53 Rs 52,000 monthly wages 45 days
kept    lv–07 encashment, s.53, ₹५२,००० a month, 45 days
refused leave encashment LV-07 s.53 Rs 52000 45 days   (dropped rs 52,000)
refused leave encashment LV-07 s.53 Rs 52,000 45 working days   (dropped 45 days)
refused LV-07 encashment under section 53, Rs 52,000, 45 days   (dropped s.53)
```

**`step_02_offline_the_kit_s_own_tests(session)` — The stage in the kit: the call, the guard, one line in /v1/query, and two lines that did not change / Do it, offline: the kit's own tests**

evals/tests/test_query_rewrite.py holds 20 tests that need neither a model nor a lane: the guard on the design's examples and on the golden rows, every outcome against a fake client, the request against google-genai's own config class, the line with no question text, search_query() lifted from rewrite.py with the switch off and on, and the ablation's rewrite arm and paraphrase rows against a stand-in lane. The pipe keeps the summary and drops the timing.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the kit's own tests: fakes for the model and the lane; Rs 0).

Expected shape, not a promised result:

```text
Ran 20 tests
OK
```

### demo_05_rewrite_called_directly_one_question_one_call_one_outcome.py

Do it: the bench's nine questions, one call each

**`step_01_the_bench_s_nine_questions_one_call_each(session)` — rewrite() called directly: one question, one call, one outcome / Do it: the bench's nine questions, one call each**

Do it: the bench's nine questions, one call each

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; 9 gemini-3.1-flash-lite calls, a few paise).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rewrites.txt]
```

### demo_06_the_stage_on_a_candidate_query_rewrite_on_a_forced_failure_and_the_undo.py

The cell creates the revision and asks it the paraphrase from step 3. ask() prints the stage's three keys, the clocks, the answer's cost and the citations. If the first line says same, the model judged the question a good search query already; ask another of step 5's questions, such as pp-10's, the same way. QUERY_REWRITE_MODEL is a setting, so a revision whose model name is wrong is one variable away. The call fails, rewrite() catches it, and the stage searches the question: the answer still comes, with HTTP 200. Do it: the two lines the two questions wrote The variables exist only on the candidate's template, so they are removed rather than set back, and the tag is dropped. Both template lines must print empty.

**`step_01_the_stage_on_one_question(session)` — The stage on a candidate: QUERY_REWRITE=on, a forced failure, and the undo / Do it: the stage on, one question**

The cell creates the revision and asks it the paraphrase from step 3. ask() prints the stage's three keys, the clocks, the answer's cost and the citations. If the first line says same, the model judged the question a good search query already; ask another of step 5's questions, such as pp-10's, the same way.

Operation: bash — run in the operator shell (one new revision, no traffic; one question to it).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/candidate.txt]
```

**`step_02_a_model_that_does_not_exist_the_same_quest(session)` — The stage on a candidate: QUERY_REWRITE=on, a forced failure, and the undo / Do it: a model that does not exist, the same question**

QUERY_REWRITE_MODEL is a setting, so a revision whose model name is wrong is one variable away. The call fails, rewrite() catches it, and the stage searches the question: the answer still comes, with HTTP 200.

Operation: bash — run in the operator shell (one more revision, no traffic, a model that does not exist; the same question).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/candidate.txt]
```

**`step_03_the_two_lines_the_two_questions_wrote(session)` — The stage on a candidate: QUERY_REWRITE=on, a forced failure, and the undo / Do it: the two lines the two questions wrote**

Do it: the two lines the two questions wrote

Operation: bash — run in the operator shell (reads the API's log; the two lines the two questions wrote).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rewrite_rows.txt]
```

**`step_04_the_undo(session)` — The stage on a candidate: QUERY_REWRITE=on, a forced failure, and the undo / Do it: the undo**

The variables exist only on the candidate's template, so they are removed rather than set back, and the tag is dropped. Both template lines must print empty.

Operation: bash — run in the operator shell (the undo: the two variables removed, the tag dropped, the template read back).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/candidate.txt]
```

### demo_07_the_measurement_the_rewrite_arm_against_the_lane_on_the_golden_rows_and_the_para.py

The wiring check takes the first five anchored rows, two arms and five calls, and shows the lines are where they should be before the longer runs spend anything.

**`step_01_a_wiring_check_then_the_golden_rows_then_t(session)` — The measurement: the rewrite arm against the lane, on the golden rows and the paraphrases / Do it: a wiring check, then the golden rows, then the paraphrases**

The wiring check takes the first five anchored rows, two arms and five calls, and shows the lines are where they should be before the longer runs spend anything.

Operation: bash — run in the operator shell, in $DEMO_ROOT (five rows: a wiring check, about a minute).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ablate_wiring.txt]
```

**`step_02_a_wiring_check_then_the_golden_rows_then_t(session)` — The measurement: the rewrite arm against the lane, on the golden rows and the paraphrases / Do it: a wiring check, then the golden rows, then the paraphrases**

The wiring check takes the first five anchored rows, two arms and five calls, and shows the lines are where they should be before the longer runs spend anything.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the 47 anchored golden rows, two arms).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ablate_golden.txt]
```

**`step_03_a_wiring_check_then_the_golden_rows_then_t(session)` — The measurement: the rewrite arm against the lane, on the golden rows and the paraphrases / Do it: a wiring check, then the golden rows, then the paraphrases**

The wiring check takes the first five anchored rows, two arms and five calls, and shows the lines are where they should be before the longer runs spend anything.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the same rows and the 24 paraphrases: 71 rows, two arms).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ablate_paraphrases.txt]
```

### demo_08_change_it_delete_the_prompt_s_literal_rule_and_measure_the_guard_where_the_stage.py

Do it: the rows the guard can refuse, Rs 0 Do it: delete the rule Do it: the same arm, the edited prompt, those rows The edit changed the prompt and left PROMPT_VERSION as it was, so any line written with the edited prompt would name a version that does not describe it. That is a reason to restore the file rather than keep the experiment; versioning a prompt properly is lesson 3.6's subject.

**`step_01_the_rows_the_guard_can_refuse_rs_0(session)` — Change it: delete the prompt's literal rule and measure the guard; where the stage cannot go / Do it: the rows the guard can refuse, Rs 0**

Do it: the rows the guard can refuse, Rs 0

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0).

Expected shape, not a promised result:

```text
13 anchored golden rows carry a literal; the guard can refuse a rewrite of no other:
   lk-02  16
   lk-06  e3
   lk-08  rs 3,00,000
   lk-10  inv-2026-0412
   lk-11  fy2026
   jn-03  e3, 50 days
   jn-05  inv-2026-0412
   jn-06  fy2026
   lk-14  2017
   jn-08  2017
   mm-01  3, fy2025, fy2026
   mm-03  fy2026
   vr-01  e3
```

**`step_02_delete_the_rule(session)` — Change it: delete the prompt's literal rule and measure the guard; where the stage cannot go / Do it: delete the rule**

Do it: delete the rule

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; edits one kit file in your clone, never the lane).

Expected shape, not a promised result:

```text
5 rules left; the prompt version still says 2026-10-08.1
- Use the words those documents use: the formal term for an informal one, and the full name of a law or a term beside its abbreviation.
- Keep every condition the question sets: who is asking, which document, before or after, the least or the most.
- Do not answer the question, and add no fact, figure or name that is not in it.
- The question may be in English, in Hindi written in Devanagari, or in Hinglish (Hindi typed in Latin letters); write the query in English.
- One line of at most 40 words. If the question is already a good search query, return it unchanged.
```

**`step_03_the_same_arm_the_edited_prompt_those_rows(session)` — Change it: delete the prompt's literal rule and measure the guard; where the stage cannot go / Do it: the same arm, the edited prompt, those rows**

Do it: the same arm, the edited prompt, those rows

Operation: bash — run in the operator shell, in $DEMO_ROOT (the 13 rows above, two arms, the edited prompt).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/changeit.txt]
```

**`step_04_put_the_kit_back(session)` — Change it: delete the prompt's literal rule and measure the guard; where the stage cannot go / Do it: put the kit back**

The edit changed the prompt and left PROMPT_VERSION as it was, so any line written with the edited prompt would name a version that does not describe it. That is a reason to restore the file rather than keep the experiment; versioning a prompt properly is lesson 3.6's subject.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the kit file put back).

Expected shape, not a promised result:

```text
the rule is back: True
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_2.5_Query_Rewrite_WIX.html`. All 62 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `76838552527ab66dd3a37a38b8adae680c3864df`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
