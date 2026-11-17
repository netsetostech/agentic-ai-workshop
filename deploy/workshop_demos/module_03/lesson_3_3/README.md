# Lesson 3.3: Recognise prompt failure modes and fix them in the prompt

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 4 | [demo_04_the_prompt_and_the_gate_s_rule_in_the_kit_system_the_prompt_line_row_verdict_and.py](demo_04_the_prompt_and_the_gate_s_rule_in_the_kit_system_the_prompt_line_row_verdict_and.py) | The prompt and the gate's rule in the kit: SYSTEM, the prompt line, row_verdict() and the passage checks |
| 5 | [demo_05_the_live_eval_with_every_answerable_row_s_pool_read_again.py](demo_05_the_live_eval_with_every_answerable_row_s_pool_read_again.py) | The live eval, with every answerable row's pool read again |
| 6 | [demo_06_the_failing_rows_read_with_their_passages_and_where_each_fix_lives.py](demo_06_the_failing_rows_read_with_their_passages_and_where_each_fix_lives.py) | The failing rows, read with their passages, and where each fix lives |
| 7 | [demo_07_one_rule_per_row_in_the_bench_with_the_refusal_rows_beside_it.py](demo_07_one_rule_per_row_in_the_bench_with_the_refusal_rows_beside_it.py) | One rule per row in the bench, with the refusal rows beside it |
| 8 | [demo_08_why_the_fix_stays_in_memory_the_served_prompt_is_the_trained_prompt.py](demo_08_why_the_fix_stays_in_memory_the_served_prompt_is_the_trained_prompt.py) | Why the fix stays in memory: the served prompt is the trained prompt |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads each failing row's passages by the kit's own chunk ids and pages, so point acme at the kit's index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads each failing row's passages by the kit's own chunk ids and pages, so point acme at the kit's index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads each failing row's passages by the kit's own chunk ids and pages, so point acme at the kit's index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_04_the_prompt_and_the_gate_s_rule_in_the_kit_system_the_prompt_line_row_verdict_and.py

The cell reads SYSTEM and DATED_RULE from generator.py as text, with Python's own parser, and splits SYSTEM into its rules with the bench's own reader, rules_of(). It imports no Google library and calls nothing.

**`step_01_system_s_rules_as_the_bench_will_number_th(session)` — The prompt and the gate's rule in the kit: SYSTEM, the prompt line, row_verdict() and the passage checks / Do it: SYSTEM's rules, as the bench will number them**

The cell reads SYSTEM and DATED_RULE from generator.py as text, with Python's own parser, and splits SYSTEM into its rules with the bench's own reader, rules_of(). It imports no Google library and calls nothing.

Operation: bash — run in the operator shell, in the kit (reads generator.py as text; no network, Rs 0).

Expected shape, not a promised result:

```text
SYSTEM, as the bench numbers it: You are DocuMind, a retrieval-grounded assistant. / Rules:
  1. Answer ONLY from the numbered context below. Never invent sources.
  2. Cite using [N] where N is the chunk number. Multiple chunks: [1,2].
  3. If the context does not contain the answer, set answerable=false and say so.
  4. Keep answers under 300 words unless asked for more.
  5. A quote is the clause that answers - at most twenty-five words, never a whole section.
DATED_RULE, added only when a packed passage carries an effective date:
  6. Some sources carry an effective date. Where sources disagree, follow the one with the latest effective date, cite it, and say which source you followed and from when it applies.
sha256 of SYSTEM then DATED_RULE: 543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e
```

### demo_05_the_live_eval_with_every_answerable_row_s_pool_read_again.py

Do it: the eval, with the switch on

**`step_01_the_eval_with_the_switch_on(session)` — The live eval, with every answerable row's pool read again / Do it: the eval, with the switch on**

Do it: the eval, with the switch on

Operation: bash — run in the operator shell, in the kit (every golden row, each answerable pool read again: ten minutes or more).

IDE adaptation: Run the eval through live_gate with the page's switch on: the rates and the required rows decide its exit, and a red exit with a fresh report is the reading step 6 starts from, as the page says. Before lesson 7.5 builds the town hall video, mm-03 cannot cite a segment and blocks the gate on its own. A missing report or an HTTP/auth failure still fails.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/eval_live.txt]
```

### demo_06_the_failing_rows_read_with_their_passages_and_where_each_fix_lives.py

Do it: the failing rows

**`step_01_the_failing_rows(session)` — The failing rows, read with their passages, and where each fix lives / Do it: the failing rows**

Do it: the failing rows

Operation: bash — run in the operator shell, in the kit (reads the report, and each failing row's pool from /v1/passages: no model, Rs 0).

IDE adaptation: Export the cell's FIX1-FIX3 as the page asks you to paste them: the cell prints the export line, which a Python cell cannot run in your shell, so step 7's bench stopped at ${FIX1:?} (21 October 2026). The session keeps them for the next file.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/failing_rows.txt]
```

### demo_07_one_rule_per_row_in_the_bench_with_the_refusal_rows_beside_it.py

Before anything costs money, see what each edit arm will send. The cell applies each rule with the bench's own edit_system() and prints the rule count, the prompt's sha256 and the new rule 6, then checks generator.py's bytes. Do it: FIX1, the refused row Do it: FIX2, the half-answered join Do it: FIX3, the answer without its figure Each run prints its pools, its two arms with their prompts' sha256, one line per answer (the verdict, the thought and visible tokens, the rupees and the why), then a table per arm: passes out of 9 with a Wilson interval, the quote checks, and the cost. The last lines say that generator.py is unchanged on disk and SYSTEM is the kit's again. The cell below reads the three reports and puts each fix's row and guard side by side.

**`step_01_the_three_rules_applied_in_memory_first(session)` — One rule per row in the bench, with the refusal rows beside it / Do it: the three rules, applied in memory first**

Before anything costs money, see what each edit arm will send. The cell applies each rule with the bench's own edit_system() and prints the rule count, the prompt's sha256 and the new rule 6, then checks generator.py's bytes.

Operation: bash — run in the operator shell, in the kit (the three rules applied in memory; no network, Rs 0).

Expected shape, not a promised result:

```text
kit   5 rules, prompt sha256 543ed8060f1b177c...
FIX1  6 rules, prompt sha256 3046edc925bd8085...
      6. If a source answers the question in other words, or states a rule that covers the case asked about, answer from it and cite it.
FIX2  6 rules, prompt sha256 e23622bc3e66816c...
      6. If the question asks more than one thing, answer every part, each from the source that states it, and cite each source.
FIX3  6 rules, prompt sha256 e3420a7f81105a67...
      6. Begin the answer with the figure, name or term that answers the question, written as the source writes it.
generator.py on disk: unchanged
```

**`step_02_fix1_the_refused_row(session)` — One rule per row in the bench, with the refusal rows beside it / Do it: FIX1, the refused row**

Do it: FIX1, the refused row

Operation: bash — run in the operator shell, in the kit (FIX1 from the read cell: its row and the 8 refusal rows, two arms).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/fix_1.txt]
```

**`step_03_fix2_the_half_answered_join(session)` — One rule per row in the bench, with the refusal rows beside it / Do it: FIX2, the half-answered join**

Do it: FIX2, the half-answered join

Operation: bash — run in the operator shell, in the kit (FIX2: the same, with the second rule).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/fix_2.txt]
```

**`step_04_fix3_the_answer_without_its_figure(session)` — One rule per row in the bench, with the refusal rows beside it / Do it: FIX3, the answer without its figure**

Do it: FIX3, the answer without its figure

Operation: bash — run in the operator shell, in the kit (FIX3: the same, with the third rule).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/fix_3.txt]
```

**`step_05_fix3_the_answer_without_its_figure(session)` — One rule per row in the bench, with the refusal rows beside it / Do it: FIX3, the answer without its figure**

Each run prints its pools, its two arms with their prompts' sha256, one line per answer (the verdict, the thought and visible tokens, the rupees and the why), then a table per arm: passes out of 9 with a Wilson interval, the quote checks, and the cost. The last lines say that generator.py is unchanged on disk and SYSTEM is the kit's again. The cell below reads the three reports and puts each fix's row and guard side by side.

Operation: bash — run in the operator shell, in the kit (reads the three bench reports; Rs 0).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/fix_read.txt]
```

### demo_08_why_the_fix_stays_in_memory_the_served_prompt_is_the_trained_prompt.py

Do it: the two copies, and the kit's own test

**`step_01_the_two_copies_and_the_kit_s_own_test(session)` — Why the fix stays in memory: the served prompt is the trained prompt / Do it: the two copies, and the kit's own test**

Do it: the two copies, and the kit's own test

Operation: bash — run in the operator shell, in the kit (two files read as text, then the kit's own test; Rs 0).

Expected shape, not a promised result:

```text
generator.py's SYSTEM: 423 characters; make_trainset.py's: 423; byte for byte equal: True
OK
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads each failing row's passages by the kit's own chunk ids and pages, so point acme at the kit's index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads each failing row's passages by the kit's own chunk ids and pages, so point acme at the kit's index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_3.3_Prompt_Failures_WIX.html`. All 42 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `2234cf3cb8c2625c7b3c783425458e19c04d13ec`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
