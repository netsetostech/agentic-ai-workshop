# Lesson 3.2: Prompt with chain of thought and few-shot exemplars

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_chat_page_the_answer_to_a_join_and_the_thinking_it_billed.py](demo_03_the_chat_page_the_answer_to_a_join_and_the_thinking_it_billed.py) | The Chat page: the answer to a join, and the thinking it billed |
| 4 | [demo_04_chain_of_thought_in_the_kit_the_level_the_schema_the_zero_shot_prompt_and_the_be.py](demo_04_chain_of_thought_in_the_kit_the_level_the_schema_the_zero_shot_prompt_and_the_be.py) | Chain of thought in the kit: the level, the schema, the zero-shot prompt and the bench |
| 5 | [demo_05_the_pool_the_bench_holds_fixed_v1_passages_for_jn_03.py](demo_05_the_pool_the_bench_holds_fixed_v1_passages_for_jn_03.py) | The pool the bench holds fixed: /v1/passages for jn-03 |
| 6 | [demo_06_chain_of_thought_measured_the_join_rows_at_low_medium_and_high.py](demo_06_chain_of_thought_measured_the_join_rows_at_low_medium_and_high.py) | Chain of thought, measured: the join rows at LOW, MEDIUM and HIGH |
| 7 | [demo_07_change_it_one_prompted_reasoning_rule_against_native_thinking.py](demo_07_change_it_one_prompted_reasoning_rule_against_native_thinking.py) | Change it: one prompted-reasoning rule against native thinking |
| 8 | [demo_08_few_shot_in_the_kit_the_examples_the_swap_and_the_offline_arms.py](demo_08_few_shot_in_the_kit_the_examples_the_swap_and_the_offline_arms.py) | Few-shot in the kit: the examples, the swap and the offline arms |
| 9 | [demo_09_few_shot_measured_the_examples_taken_out_and_put_back_on_your_lane.py](demo_09_few_shot_measured_the_examples_taken_out_and_put_back_on_your_lane.py) | Few-shot, measured: the examples taken out and put back on your lane |
| 10 | [demo_10_direct_reads_the_two_reports_turn_by_turn.py](demo_10_direct_reads_the_two_reports_turn_by_turn.py) | Direct reads: the two reports, turn by turn |

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

### demo_03_the_chat_page_the_answer_to_a_join_and_the_thinking_it_billed.py

In the Chat page, signed in as yourself, ask exactly: I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve? Read the answer: the eval gate would want 45 and 60 in it. Then read the API's log for the last ten minutes.

**`step_01_jn_03_in_the_chat_page_then_its_row(session)` — The Chat page: the answer to a join, and the thinking it billed / Do it: jn-03 in the Chat page, then its row**

In the Chat page, signed in as yourself, ask exactly: I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve? Read the answer: the eval gate would want 45 and 60 in it. Then read the API's log for the last ten minutes.

Operation: bash — run in the operator shell, after the question in the Chat page (reads the API's log; changes nothing).

Manual action: In the deployed UI's Chat page, signed in as yourself, ask exactly: I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve? Wait for the cited answer, then type done to read its stream row from the API's log.

IDE adaptation: Pause before this cell for the page's manual step, a browser action or a wait (the README's Manual action). Type done to continue, or stop and rerun later. The cell then runs as the page gives it, unless another adaptation here says otherwise.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ui_stream.txt]
```

### demo_04_chain_of_thought_in_the_kit_the_level_the_schema_the_zero_shot_prompt_and_the_be.py

Step 7 adds one rule. This cell builds the edit arm's SYSTEM with the bench's own edit_system(), from generator.py's text read as data, since importing generator.py builds a Gemini client for your lane. Then it hashes both prompts as the bench's header does, SYSTEM followed by DATED_RULE, the text lesson 3.6 binds to a version, and looks each hash up in the kit's registry of prompt versions. No model is called. The two test files run the bench on a scripted model and a stand-in lane, and the router's example swap on its scripted classifier. They check the level and the temperature sent, the rule edited in memory with generator.py untouched, the gate's verdict on every answer, the rupees, and the swap put back whatever happens. The pipe keeps the summary lines.

**`step_01_offline_the_edit_arm_s_prompt_before_you_p(session)` — Chain of thought in the kit: the level, the schema, the zero-shot prompt and the bench / Do it, offline: the edit arm's prompt, before you pay for it**

Step 7 adds one rule. This cell builds the edit arm's SYSTEM with the bench's own edit_system(), from generator.py's text read as data, since importing generator.py builds a Gemini client for your lane. Then it hashes both prompts as the bench's header does, SYSTEM followed by DATED_RULE, the text lesson 3.6 binds to a version, and looks each hash up in the kit's registry of prompt versions. No model is called.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: no model is called).

Expected shape, not a promised result:

```text
You are DocuMind, a retrieval-grounded assistant.
Rules:
1. Answer ONLY from the numbered context below. Never invent sources.
2. Cite using [N] where N is the chunk number. Multiple chunks: [1,2].
3. If the context does not contain the answer, set answerable=false and say so.
4. Keep answers under 300 words unless asked for more.
5. A quote is the clause that answers - at most twenty-five words, never a whole section.
6. Show your working in the answer: name each fact the question needs and the [N] that states it, then combine them.
kit  prompt sha256 543ed8060f1b177c...  documind-rag@v3
edit prompt sha256 3f23ad647176d4fe...  no version names it
```

**`step_02_offline_the_bench_s_and_the_swap_s_own_tes(session)` — Chain of thought in the kit: the level, the schema, the zero-shot prompt and the bench / Do it, offline: the bench's and the swap's own tests**

The two test files run the bench on a scripted model and a stand-in lane, and the router's example swap on its scripted classifier. They check the level and the temperature sent, the rule edited in memory with generator.py untouched, the gate's verdict on every answer, the rupees, and the swap put back whatever happens. The pipe keeps the summary lines.

Operation: bash — run in the operator shell, in $DEMO_ROOT (the kit's own tests: a scripted model and a stand-in lane; Rs 0).

Expected shape, not a promised result:

```text
Ran 21 tests
OK
Ran 9 tests
OK
```

### demo_05_the_pool_the_bench_holds_fixed_v1_passages_for_jn_03.py

The curl saves the route's reply. The Python cell lists the passages and checks them with run_eval's own rules: which passage holds each figure the gate wants (contains()), and whether each anchor the row names is in the pool (anchors_found(), the rule DOCUMIND_EVAL_PASSAGES=1 uses).

**`step_01_jn_03_s_pool_and_where_its_two_facts_sit(session)` — The pool the bench holds fixed: /v1/passages for jn-03 / Do it: jn-03's pool, and where its two facts sit**

The curl saves the route's reply. The Python cell lists the passages and checks them with run_eval's own rules: which passage holds each figure the gate wants (contains()), and whether each anchor the row names is in the pool (anchors_found(), the rule DOCUMIND_EVAL_PASSAGES=1 uses).

Operation: bash — run in the operator shell, in $DEMO_ROOT (one /v1/passages call, then a Python cell; no model call).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/passages_jn03.txt]
```

### demo_06_chain_of_thought_measured_the_join_rows_at_low_medium_and_high.py

Do it: the join rows at three levels

**`step_01_the_join_rows_at_three_levels(session)` — Chain of thought, measured: the join rows at LOW, MEDIUM and HIGH / Do it: the join rows at three levels**

Do it: the join rows at three levels

Operation: bash — run in the operator shell, in $DEMO_ROOT (11 pools, then 33 answers on your lane).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/join_levels.txt]
```

### demo_07_change_it_one_prompted_reasoning_rule_against_native_thinking.py

Do it: both arms, with every answer kept in a report The report keeps each answer's first 600 characters, its calls and its quote checks. The cell prints jn-03's answer from each arm, so you can see where the working went.

**`step_01_both_arms_with_every_answer_kept_in_a_repo(session)` — Change it: one prompted-reasoning rule against native thinking / Do it: both arms, with every answer kept in a report**

Do it: both arms, with every answer kept in a report

Operation: bash — run in the operator shell, in $DEMO_ROOT (11 pools, then 22 answers at LOW, two arms).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/cot_rule.txt]
```

**`step_02_jn_03_s_two_answers_from_the_report(session)` — Change it: one prompted-reasoning rule against native thinking / Do it: jn-03's two answers, from the report**

The report keeps each answer's first 600 characters, its calls and its quote checks. The cell prints jn-03's answer from each arm, so you can see where the working went.

Operation: bash — run in the operator shell (a Python cell; reads the report, Rs 0).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/cot_answers.txt]
```

### demo_08_few_shot_in_the_kit_the_examples_the_swap_and_the_offline_arms.py

Do it, offline: the swap, and the rows it scores LOCAL=1 runs the same eval with route_eval.py's scripted classifier and offline embeddings: no project and no cost. The scripted L1 gives each row its own label, deliberately wrong on about one row in eight, and reads no example. So offline the two arms must agree on every route. What differs is the prompt's length, and so the router's cost.

**`step_01_offline_the_swap_and_the_rows_it_scores(session)` — Few-shot in the kit: the examples, the swap and the offline arms / Do it, offline: the swap, and the rows it scores**

Do it, offline: the swap, and the rows it scores

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0).

Expected shape, not a promised result:

```text
with the examples: 2,121 characters, 8 example lines
inside the swap:   1,576 characters, 0 example lines
every other line unchanged: True
after the swap, the kit's tuple again: True
207 dev rows: 20 in the examples' 8 groups, out of every arm's score; 187 scored
```

**`step_02_offline_both_arms_on_the_scripted_classifi(session)` — Few-shot in the kit: the examples, the swap and the offline arms / Do it, offline: both arms on the scripted classifier**

LOCAL=1 runs the same eval with route_eval.py's scripted classifier and offline embeddings: no project and no cost. The scripted L1 gives each row its own label, deliberately wrong on about one row in eight, and reads no example. So offline the two arms must agree on every route. What differs is the prompt's length, and so the router's cost.

Operation: bash — run in the operator shell, in $DEMO_ROOT (offline: no project, Rs 0).

Expected shape, not a promised result:

```text
python evals/route_eval.py --local --exemplars kit
local: the classifier is scripted, so this measures the cascade, not a model
  187 rows scored; 20 left out (the groups of the prompt's examples); index of 198 dev rows
  exemplars: the kit's own, desk_routes.PROMPT_EXEMPLARS - 8 in the L1 prompt; the rows of the kit's 8 stay out of the score in every arm
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
    handbook -> statute: 0/44 = 0.0% [0.0%, 8.0%]
    handbook -> case: 0/44 = 0.0% [0.0%, 8.0%]
    handbook -> clarify: 1/44 = 2.3% [0.4%, 11.8%]
    handbook -> out_of_scope: 0/44 = 0.0% [0.0%, 8.0%]
    handbook -> other: 0/44 = 0.0% [0.0%, 8.0%]
    statute -> handbook: 0/129 = 0.0% [0.0%, 2.9%]
    statute -> case: 0/129 = 0.0% [0.0%, 2.9%]
    statute -> clarify: 0/129 = 0.0% [0.0%, 2.9%]
    statute -> out_of_scope: 0/129 = 0.0% [0.0%, 2.9%]
    statute -> other: 0/129 = 0.0% [0.0%, 2.9%]
    out_of_scope -> handbook: 0/14 = 0.0% [0.0%, 21.5%]
    out_of_scope -> statute: 0/14 = 0.0% [0.0%, 21.5%]
    out_of_scope -> case: 0/14 = 0.0% [0.0%, 21.5%]
    out_of_scope -> clarify: 0/14 = 0.0% [0.0%, 21.5%]
    out_of_scope -> other: 0/14 = 0.0% [0.0%, 21.5%]
  route accuracy, en            186/187 = 99.5% [97.0%, 99.9%]
  escalation recall, pooled     0/0 (no rows)
  authority_rate                not measured: the run carries no citations (a /v1/route run)
  correct_rate                  not measured: the run carries no answer text (a /v1/route run)
  methods: anchor 52, arbiter 48, model 78, single 9
  acceptance rules: A 76, B 1, C 1, F 48
  accepted without L2           139/139 = 100.0% [97.3%, 100.0%]
  sent to L2                    48/187 = 25.7% [19.9%, 32.4%]
  router cost                   Rs 3.8411 in all, Rs 0.02054 a turn
  L1 alone                      106/126 = 84.1% [76.8%, 89.5%]  (L1's own route, before the vote and the arbiter, on the turns it was asked; 0 failed)
the dev gates hold
```

**`step_03_offline_both_arms_on_the_scripted_classifi(session)` — Few-shot in the kit: the examples, the swap and the offline arms / Do it, offline: both arms on the scripted classifier**

LOCAL=1 runs the same eval with route_eval.py's scripted classifier and offline embeddings: no project and no cost. The scripted L1 gives each row its own label, deliberately wrong on about one row in eight, and reads no example. So offline the two arms must agree on every route. What differs is the prompt's length, and so the router's cost.

Operation: bash — run in the operator shell, in $DEMO_ROOT (offline, the examples out: Rs 0).

Expected shape, not a promised result:

```text
python evals/route_eval.py --local --exemplars none
...
  exemplars: none - 0 in the L1 prompt; the rows of the kit's 8 stay out of the score in every arm
...
  router cost                   Rs 3.4761 in all, Rs 0.01859 a turn
```

### demo_09_few_shot_measured_the_examples_taken_out_and_put_back_on_your_lane.py

Do it: with the kit's examples, then with none

**`step_01_with_the_kit_s_examples_then_with_none(session)` — Few-shot, measured: the examples taken out and put back on your lane / Do it: with the kit's examples, then with none**

Do it: with the kit's examples, then with none

Operation: bash — run in the operator shell, in $DEMO_ROOT (the kit's examples: 126 gemini-3.1-flash-lite calls, the arbiter's, and embeddings).

IDE adaptation: Run the arm through route_gate: the dev gates' FAIL lines and exit 1 are a reading this lesson compares, as the page says, so the next arm still runs; a run that writes no fresh report with its decisions still fails.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/exemplars_kit.txt]
```

**`step_02_with_the_kit_s_examples_then_with_none(session)` — Few-shot, measured: the examples taken out and put back on your lane / Do it: with the kit's examples, then with none**

Do it: with the kit's examples, then with none

Operation: bash — run in the operator shell, in $DEMO_ROOT (the same rows, no example).

IDE adaptation: Run the arm through route_gate: the dev gates' FAIL lines and exit 1 are a reading this lesson compares, as the page says, so the next arm still runs; a run that writes no fresh report with its decisions still fails.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/exemplars_none.txt]
```

### demo_10_direct_reads_the_two_reports_turn_by_turn.py

Do it: the paired read, and the turns that flipped

**`step_01_the_paired_read_and_the_turns_that_flipped(session)` — Direct reads: the two reports, turn by turn / Do it: the paired read, and the turns that flipped**

Do it: the paired read, and the turns that flipped

Operation: bash — run in the operator shell (a Python cell; reads the two reports, Rs 0).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/exemplar_flips.txt]
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_3.2_CoT_Few_Shot_WIX.html`. All 52 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `9d08b333f5364f71179e7d150f0b9463217dd55e`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
