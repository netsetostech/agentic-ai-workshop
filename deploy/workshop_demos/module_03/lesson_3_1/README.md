# Lesson 3.1: See run-to-run variance and thinking levels in the same prompt

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_one_question_five_times_in_the_chat_page.py](demo_03_one_question_five_times_in_the_chat_page.py) | One question, five times, in the Chat page |
| 5 | [demo_05_the_bench_for_rs_0_its_tests_and_a_scripted_model.py](demo_05_the_bench_for_rs_0_its_tests_and_a_scripted_model.py) | The bench for Rs 0: its tests, and a scripted model |
| 6 | [demo_06_five_calls_to_v1_query_judged_by_the_gate_s_rule.py](demo_06_five_calls_to_v1_query_judged_by_the_gate_s_rule.py) | Five calls to /v1/query, judged by the gate's rule |
| 7 | [demo_07_make_bench_five_runs_at_low_and_five_at_high.py](demo_07_make_bench_five_runs_at_low_and_five_at_high.py) | make bench: five runs at LOW and five at HIGH |
| 8 | [demo_08_change_it_send_a_temperature_of_2_0_and_read_what_went_out.py](demo_08_change_it_send_a_temperature_of_2_0_and_read_what_went_out.py) | Change it: send a temperature of 2.0, and read what went out |
| 9 | [demo_09_what_your_lane_logged_and_what_the_bench_did_not.py](demo_09_what_your_lane_logged_and_what_the_bench_did_not.py) | What your lane logged, and what the bench did not |

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

### demo_03_one_question_five_times_in_the_chat_page.py

Golden row jn-03 asked five times as yourself: what moves between the answers, what stays, and what the page sends. Start in the product, where a user meets variance. The Chat page streams each answer from /v1/stream and sends only the question: rag-api keeps no history, so five turns are five independent answers to one prompt. Before you ask, note the time in the operator shell. Step 9 reads the usage rows written since then.

**`step_01_one_question_five_times_in_the_chat_page(session)` — One question, five times, in the Chat page / One question, five times, in the Chat page**

Golden row jn-03 asked five times as yourself: what moves between the answers, what stays, and what the page sends. Start in the product, where a user meets variance. The Chat page streams each answer from /v1/stream and sends only the question: rag-api keeps no history, so five turns are five independent answers to one prompt. Before you ask, note the time in the operator shell. Step 9 reads the usage rows written since then.

Operation: bash — run in the operator shell, in $DEMO_ROOT, before you ask in the UI (Rs 0: it notes the time).

Expected shape, not a promised result:

```text
lesson 3.1 from YYYY-MM-DDTHH:MM:SSZ (UTC): step 9 reads the usage rows written since then
```

### demo_05_the_bench_for_rs_0_its_tests_and_a_scripted_model.py

Before you spend a rupee, run the bench where nothing can be billed. First its tests, 21 of them in evals/tests/test_prompt_bench.py. They answer with the kit's own generate() over a scripted model and stand-ins for the lane, and they check what step 4 claimed: each row's pool is read once and held fixed, the level and the temperature are sent and nothing else changes, generator.py is never written, every answer is judged by the gate's rule, and the rupees are list price. The one test that runs the recorder on google-genai's own types needs that library, which Module 0 installed in your venv. Before you spend a rupee, run the bench where nothing can be billed. First its tests, 21 of them in evals/tests/test_prompt_bench.py. They answer with the kit's own generate() over a scripted model and stand-ins for the lane, and they check what step 4 claimed: each row's pool is read once and held fixed, the level and the temperature are sent and nothing else changes, generator.py is never written, every answer is judged by the gate's rule, and the rupees are list price. The one test that runs the recorder on google-genai's own types needs that library, which Module 0 installed in your venv. Then the bench itself. The cell below runs prompt_bench.main(), the function make bench runs, over generator.py imported in your shell, with two things stood in. /v1/passages returns the handbook's first six clauses, cut by the kit's own chunker as the kit's tests cut them, so NP-03 is [Source 1] and LV-07 is [Source 4]. The model is a script behind generator._client. It writes five wordings of an answer to jn-03 in turn, the same five at every level and temperature, and "thinks" 120 tokens at LOW and 900 at HIGH, the numbers the kit's tests script. Its fifth wording has all 50 days encashed, so that you can see a failure printed. It also counts the thinking level and the temperature each call was sent with. The cell runs the bench twice: the two levels with --show, then a temperature of 2.0.

**`step_01_definition(session)` — The bench for Rs 0: its tests, and a scripted model / Definition**

Before you spend a rupee, run the bench where nothing can be billed. First its tests, 21 of them in evals/tests/test_prompt_bench.py. They answer with the kit's own generate() over a scripted model and stand-ins for the lane, and they check what step 4 claimed: each row's pool is read once and held fixed, the level and the temperature are sent and nothing else changes, generator.py is never written, every answer is judged by the gate's rule, and the rupees are list price. The one test that runs the recorder on google-genai's own types needs that library, which Module 0 installed in your venv.

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: the kit's tests of the bench, no network).

Expected shape, not a promised result:

```text
test_bench_redact_0_prints_them_as_they_are (test_prompt_bench.IdentifierTests.test_bench_redact_0_prints_them_as_they_are) ... ok
test_the_lanes_project_id_and_number_are_printed_and_reported_as_the_pages_print_them (test_prompt_bench.IdentifierTests.test_the_lanes_project_id_and_number_are_printed_and_reported_as_the_pages_print_them) ... ok
test_what_the_redactor_replaces (test_prompt_bench.IdentifierTests.test_what_the_redactor_replaces) ... ok
test_the_level_and_the_temperature_are_sent_and_nothing_else_changes (test_prompt_bench.RecorderTests.test_the_level_and_the_temperature_are_sent_and_nothing_else_changes) ... ok
test_the_recorder_on_google_genais_own_types (test_prompt_bench.RecorderTests.test_the_recorder_on_google_genais_own_types) ... ok
test_a_row_with_no_pool_is_not_benched (test_prompt_bench.RetrievalTests.test_a_row_with_no_pool_is_not_benched) ... ok
test_each_rows_pool_is_read_once_before_anything_is_asked_and_held_fixed (test_prompt_bench.RetrievalTests.test_each_rows_pool_is_read_once_before_anything_is_asked_and_held_fixed) ... ok
test_the_prompt_is_what_generate_builds_from_the_pool (test_prompt_bench.RetrievalTests.test_the_prompt_is_what_generate_builds_from_the_pool) ... ok
test_failing_picks_a_reports_failing_rows (test_prompt_bench.RowTests.test_failing_picks_a_reports_failing_rows) ... ok
test_rows_are_refused_when_they_cannot_be_read (test_prompt_bench.RowTests.test_rows_are_refused_when_they_cannot_be_read) ... ok
test_the_generator_needs_the_lanes_project (test_prompt_bench.RowTests.test_the_generator_needs_the_lanes_project) ... ok
test_a_429_on_the_model_asked_falls_back_to_the_default_and_says_so (test_prompt_bench.ScoringTests.test_a_429_on_the_model_asked_falls_back_to_the_default_and_says_so) ... ok
test_a_wrong_answer_a_breach_and_a_stale_version_fail_as_the_gate_fails_them (test_prompt_bench.ScoringTests.test_a_wrong_answer_a_breach_and_a_stale_version_fail_as_the_gate_fails_them) ... ok
test_an_answer_cut_off_twice_is_an_error_with_both_calls_billed (test_prompt_bench.ScoringTests.test_an_answer_cut_off_twice_is_an_error_with_both_calls_billed) ... ok
test_every_answer_is_judged_by_the_gates_rule (test_prompt_bench.ScoringTests.test_every_answer_is_judged_by_the_gates_rule) ... ok
test_distinct_answers_and_citation_sets_per_row_across_runs (test_prompt_bench.SummaryTests.test_distinct_answers_and_citation_sets_per_row_across_runs) ... ok
test_the_rupees_are_list_price (test_prompt_bench.SummaryTests.test_the_rupees_are_list_price) ... ok
test_edit_system (test_prompt_bench.SystemTests.test_edit_system) ... ok
test_rules_edited_in_memory_and_generator_py_untouched (test_prompt_bench.SystemTests.test_rules_edited_in_memory_and_generator_py_untouched) ... ok
test_the_kit_system_and_client_come_back_whatever_happens (test_prompt_bench.SystemTests.test_the_kit_system_and_client_come_back_whatever_happens) ... ok
test_the_make_target_and_its_listings (test_prompt_bench.WiringTests.test_the_make_target_and_its_listings) ... ok

----------------------------------------------------------------------
Ran 21 tests in N.NNNs

OK
```

**`step_02_definition(session)` — The bench for Rs 0: its tests, and a scripted model / Definition**

Before you spend a rupee, run the bench where nothing can be billed. First its tests, 21 of them in evals/tests/test_prompt_bench.py. They answer with the kit's own generate() over a scripted model and stand-ins for the lane, and they check what step 4 claimed: each row's pool is read once and held fixed, the level and the temperature are sent and nothing else changes, generator.py is never written, every answer is judged by the gate's rule, and the rupees are list price. The one test that runs the recorder on google-genai's own types needs that library, which Module 0 installed in your venv. Then the bench itself. The cell below runs prompt_bench.main(), the function make bench runs, over generator.py imported in your shell, with two things stood in. /v1/passages returns the handbook's first six clauses, cut by the kit's own chunker as the kit's tests cut them, so NP-03 is [Source 1] and LV-07 is [Source 4]. The model is a script behind generator._client. It writes five wordings of an answer to jn-03 in turn, the same five at every level and temperature, and "thinks" 120 tokens at LOW and 900 at HIGH, the numbers the kit's tests script. Its fifth wording has all 50 days encashed, so that you can see a failure printed. It also counts the thinking level and the temperature each call was sent with. The cell runs the bench twice: the two levels with --show, then a temperature of 2.0.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: the kit's generate() over a scripted model, nothing leaves the machine).

Expected shape, not a promised result:

```text
== prompt bench: gemini-3.6-flash, against http://stand-in.invalid ==
  1 row(s) x 1 arm(s) x 2 level(s) x 5 run(s): up to 10 answers, one generate() each
  pools: POST /v1/passages once a row (top_k 6), held fixed for every arm, level and run
    jn-03   join      acme    6 passages: hr_policy_2026.md x6
  arms (prompt sha256: SYSTEM followed by DATED_RULE, the text every prompt starts with)
    kit   generator.py's SYSTEM - 5 rules; no temperature
          prompt sha256 543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e
    (the kit arm at LOW is the API's own request: generator.py's SYSTEM, thinking_level LOW, no temperature)

  answers
    jn-03   kit   LOW     run 1  pass  thought    120  visible    69  Rs 0.1863
    jn-03   kit   HIGH    run 1  pass  thought    900  visible    69  Rs 0.6835
    jn-03   kit   LOW     run 2  pass  thought    120  visible    74  Rs 0.1895
    jn-03   kit   HIGH    run 2  pass  thought    900  visible    74  Rs 0.6867
    jn-03   kit   LOW     run 3  pass  thought    120  visible    62  Rs 0.1818
    jn-03   kit   HIGH    run 3  pass  thought    900  visible    62  Rs 0.6791
    jn-03   kit   LOW     run 4  pass  thought    120  visible    69  Rs 0.1863
    jn-03   kit   HIGH    run 4  pass  thought    900  visible    69  Rs 0.6835
    jn-03   kit   LOW     run 5  FAIL  thought    120  visible    68  Rs 0.1856  answered without ['45', '60']
    jn-03   kit   HIGH    run 5  FAIL  thought    900  visible    68  Rs 0.6829  answered without ['45', '60']

  arm   level   pass                              distinct  cite sets  thought  visible  Rs/answer
  kit   LOW     4/5 = 80.0% [37.6%, 96.4%]          4 of 5     1 of 5      120       68     0.1859
  kit   HIGH    4/5 = 80.0% [37.6%, 96.4%]          4 of 5     1 of 5      900       68     0.6831
  distinct: answer texts that differ within a row across its runs, summed over the rows; cite sets: the same for the passages cited; thought and visible: output tokens an answer, every call of it counted
  quotes kit LOW: 10 of 10 in the passage they cite
  quotes kit HIGH: 10 of 10 in the passage they cite

  jn-03 (join, acme): I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?
    [1] hr_policy_2026.md p.1: 'NP-03 — Notice period A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice runs'
    [2] hr_policy_2026.md p.1: 'PB-02 — Probation New joiners serve six months on probation at grade E2. During probation the notice period is'
    [3] hr_policy_2026.md p.1: 'LV-01 — Earned leave Earned leave accrues at 1.75 days per completed month. A maximum of 30 days may be carrie'
    [4] hr_policy_2026.md p.1: 'LV-07 — Leave on exit Earned leave is encashed on exit at basic pay, capped at 45 days. Leave cannot be encash'
    [5] hr_policy_2026.md p.1: 'EXP-12 — Travel reimbursement Domestic travel is reimbursed against original receipts, capped at Rs 40,000 per'
    [6] hr_policy_2026.md p.1: 'PR-05 — Payroll and Form 16 Salary is credited on the last working day of each month. Form 16 is issued by 15 '
    kit LOW: 4 distinct of 5
      2x  'You can encash 45 of your 50 days, the cap on exit, and you serve a notice period of 60 days [4, 1].'
      1x  "Encashment is capped at 45 days, so 45 days are paid at basic pay [4]. As a confirmed E3 you serve 60 days' notice [1]."
      1x  'Forty-five days are encashed and the notice period is sixty days [4, 1].'
      1x  'All 50 days of earned leave are encashed at basic pay, and the notice period is 60 days [4, 1].'
    kit HIGH: 4 distinct of 5
      2x  'You can encash 45 of your 50 days, the cap on exit, and you serve a notice period of 60 days [4, 1].'
      1x  "Encashment is capped at 45 days, so 45 days are paid at basic pay [4]. As a confirmed E3 you serve 60 days' notice [1]."
      1x  'Forty-five days are encashed and the notice period is sixty days [4, 1].'
      1x  'All 50 days of earned leave are encashed at basic pay, and the notice period is 60 days [4, 1].'

  Rs 4.3452 in all: 10 answers, 10 model calls on gemini-3.6-flash, priced at list (shared/prices.py)
  generator.py unchanged on disk; SYSTEM is the kit's again
  the script was sent: thinking_level HIGH, temperature None: 5 calls; thinking_level LOW, temperature None: 5 calls

== prompt bench: gemini-3.6-flash, against http://stand-in.invalid ==
  1 row(s) x 2 arm(s) x 1 level(s) x 5 run(s): up to 10 answers, one generate() each
  pools: POST /v1/passages once a row (top_k 6), held fixed for every arm, level and run
    jn-03   join      acme    6 passages: hr_policy_2026.md x6
  arms (prompt sha256: SYSTEM followed by DATED_RULE, the text every prompt starts with)
    kit   generator.py's SYSTEM - 5 rules; no temperature
          prompt sha256 543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e
    edit  generator.py's SYSTEM - 5 rules; temperature 2
          prompt sha256 543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e
    (the kit arm at LOW is the API's own request: generator.py's SYSTEM, thinking_level LOW, no temperature)

  answers
    jn-03   kit   LOW     run 1  pass  thought    120  visible    69  Rs 0.1863
    jn-03   edit  LOW     run 1  pass  thought    120  visible    69  Rs 0.1863
    jn-03   kit   LOW     run 2  pass  thought    120  visible    74  Rs 0.1895
    jn-03   edit  LOW     run 2  pass  thought    120  visible    74  Rs 0.1895
    jn-03   kit   LOW     run 3  pass  thought    120  visible    62  Rs 0.1818
    jn-03   edit  LOW     run 3  pass  thought    120  visible    62  Rs 0.1818
    jn-03   kit   LOW     run 4  pass  thought    120  visible    69  Rs 0.1863
    jn-03   edit  LOW     run 4  pass  thought    120  visible    69  Rs 0.1863
    jn-03   kit   LOW     run 5  FAIL  thought    120  visible    68  Rs 0.1856  answered without ['45', '60']
    jn-03   edit  LOW     run 5  FAIL  thought    120  visible    68  Rs 0.1856  answered without ['45', '60']

  arm   level   pass                              distinct  cite sets  thought  visible  Rs/answer
  kit   LOW     4/5 = 80.0% [37.6%, 96.4%]          4 of 5     1 of 5      120       68     0.1859
  edit  LOW     4/5 = 80.0% [37.6%, 96.4%]          4 of 5     1 of 5      120       68     0.1859
  distinct: answer texts that differ within a row across its runs, summed over the rows; cite sets: the same for the passages cited; thought and visible: output tokens an answer, every call of it counted
  quotes kit LOW: 10 of 10 in the passage they cite
  quotes edit LOW: 10 of 10 in the passage they cite

  Rs 1.8589 in all: 10 answers, 10 model calls on gemini-3.6-flash, priced at list (shared/prices.py)
  generator.py unchanged on disk; SYSTEM is the kit's again
  the script was sent: thinking_level LOW, temperature 2.0: 5 calls; thinking_level LOW, temperature None: 5 calls
```

### demo_06_five_calls_to_v1_query_judged_by_the_gate_s_rule.py

Now the real model, through the API. /v1/query is the request make eval-live sends for every golden row, and the bench's kit arm at LOW reproduces it, so these five answers are five more draws from what step 7 measures. The cell asks the way the gate asks, run_eval.ask() with top_k 6 as documind-ui-sa, and judges each reply with row_verdict() after reading the ledger's current versions from GET /v1/sources, as the gate does. It starts with /version, which names the model, the prompt version and the answer cache. The cache is off unless a deploy turned it on (SEMANTIC_CACHE, lesson 6.2); with it on, a repeated question can come back from the cache with no model call, and the five would not be five draws.

**`step_01_definition(session)` — Five calls to /v1/query, judged by the gate's rule / Definition**

Now the real model, through the API. /v1/query is the request make eval-live sends for every golden row, and the bench's kit arm at LOW reproduces it, so these five answers are five more draws from what step 7 measures. The cell asks the way the gate asks, run_eval.ask() with top_k 6 as documind-ui-sa, and judges each reply with row_verdict() after reading the ledger's current versions from GET /v1/sources, as the gate does. It starts with /version, which names the model, the prompt version and the answer cache. The cache is off unless a deploy turned it on (SEMANTIC_CACHE, lesson 6.2); with it on, a repeated question can come back from the cache with no model call, and the five would not be five draws.

Operation: bash — run in the operator shell, in $DEMO_ROOT (five /v1/query answers at LOW: about Rs 1.01 of input by the kit's count, at most Rs 7.54 with every answer at the 2,048-token cap).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rest_five.txt]
```

### demo_07_make_bench_five_runs_at_low_and_five_at_high.py

The bench on your lane: jn-03's pool read once from your /v1/passages, then generate() five times at LOW and five at HIGH, interleaved, each answer judged and priced. --show adds the pool and each level's distinct answers, the most frequent first. --report keeps every answer, the config it was sent with, its usage and its verdict in evals/reports/bench-levels.json, which the kit's .gitignore keeps out of git. The bench imports generator.py in your shell: Module 0 installed rag-api's pins in your venv, and if this shell lacks one the bench names it and stops before any call.

**`step_01_definition(session)` — make bench: five runs at LOW and five at HIGH / Definition**

The bench on your lane: jn-03's pool read once from your /v1/passages, then generate() five times at LOW and five at HIGH, interleaved, each answer judged and priced. --show adds the pool and each level's distinct answers, the most frequent first. --report keeps every answer, the config it was sent with, its usage and its verdict in evals/reports/bench-levels.json, which the kit's .gitignore keeps out of git. The bench imports generator.py in your shell: Module 0 installed rag-api's pins in your venv, and if this shell lacks one the bench names it and stops before any call.

Operation: bash — run in the operator shell, in $DEMO_ROOT (ten answers, five at LOW and five at HIGH: about Rs 2.02 of input, at most Rs 15.08 at the cap; a cut-off answer asked again adds up to Rs 3.92).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/bench_levels.txt]
```

### demo_08_change_it_send_a_temperature_of_2_0_and_read_what_went_out.py

generator.py sends no temperature; the bench can. --temperature 2.0 adds a second arm, edit: the kit's prompt, the kit's level and a temperature of 2.0 on every call. The kit arm runs beside it, interleaved, so the two share the lane's conditions, and both print one prompt sha256, because the text is the same: the only difference the run can show is the knob. Without --levels the bench runs at LOW, so this run's kit arm is a third sample of the request steps 6 and 7 already asked. The table cannot prove that 2.0 was sent: it prints each arm's settings, not its requests. The recorder's log can. Every call in the report carries its config as sent (the thinking level, the temperature, None when none was sent, and the cap) and what came back.

**`step_01_definition(session)` — Change it: send a temperature of 2.0, and read what went out / Definition**

generator.py sends no temperature; the bench can. --temperature 2.0 adds a second arm, edit: the kit's prompt, the kit's level and a temperature of 2.0 on every call. The kit arm runs beside it, interleaved, so the two share the lane's conditions, and both print one prompt sha256, because the text is the same: the only difference the run can show is the knob. Without --levels the bench runs at LOW, so this run's kit arm is a third sample of the request steps 6 and 7 already asked.

Operation: bash — run in the operator shell, in $DEMO_ROOT (ten answers at LOW, five with a temperature of 2.0: about Rs 2.02 of input, at most Rs 15.08 at the cap).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/bench_temperature.txt]
```

**`step_02_read_what_went_out(session)` — Change it: send a temperature of 2.0, and read what went out / Read what went out**

The table cannot prove that 2.0 was sent: it prints each arm's settings, not its requests. The recorder's log can. Every call in the report carries its config as sent (the thinking level, the temperature, None when none was sent, and the cap) and what came back.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the report step 8's run wrote).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/bench_temperature.json]
```

### demo_09_what_your_lane_logged_and_what_the_bench_did_not.py

rag-api writes one usage row for every /v1/query, /v1/stream and /v1/passages request, in the one shape main.py's usage_row() builds, to Cloud Logging. make usage and the BigQuery view tenant_daily read those rows, and as each one is written its cost is added to the month's spend counter, which the router's breaker reads before it picks a model. The cell reads the rows written since T0, the time you noted in step 3, oldest first, with each row's tokens and the price cost.py gave it. Wait a minute after step 8, because a row can take a little while to reach the log, and if this is a new shell, set T0 again to a time before step 3.

**`step_01_definition(session)` — What your lane logged, and what the bench did not / Definition**

rag-api writes one usage row for every /v1/query, /v1/stream and /v1/passages request, in the one shape main.py's usage_row() builds, to Cloud Logging. make usage and the BigQuery view tenant_daily read those rows, and as each one is written its cost is added to the month's spend counter, which the router's breaker reads before it picks a model. The cell reads the rows written since T0, the time you noted in step 3, oldest first, with each row's tokens and the price cost.py gave it. Wait a minute after step 8, because a row can take a little while to reach the log, and if this is a new shell, set T0 again to a time before step 3.

Operation: bash — run in the operator shell, in $DEMO_ROOT, a minute after step 8 (a Python cell; Rs 0: one Cloud Logging read).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/usage_rows.txt]
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_3.1_Stochastic_WIX.html`. All 35 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `a05b177935767e6d4412a41782001c53c305ff58`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
