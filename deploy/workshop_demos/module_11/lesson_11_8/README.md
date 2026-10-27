# Lesson 11.8: Complete the independent capstone and operational handover

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 4 | [demo_04_the_lines_the_check_rests_on.py](demo_04_the_lines_the_check_rests_on.py) | The lines the check rests on |
| 5 | [demo_05_the_check_offline_the_kit_as_it_ships_a_canned_capstone_your_fork.py](demo_05_the_check_offline_the_kit_as_it_ships_a_canned_capstone_your_fork.py) | The check, offline: the kit as it ships, a canned capstone, your fork |
| 6 | [demo_06_change_it_one_command_deleted_one_component_fails.py](demo_06_change_it_one_command_deleted_one_component_fails.py) | Change it: one command deleted, one component fails |
| 7 | [demo_07_your_lane_read_with_the_two_tokens.py](demo_07_your_lane_read_with_the_two_tokens.py) | Your lane, read with the two tokens |
| 8 | [demo_08_the_handover_handover_md_from_the_checkout_and_the_lane.py](demo_08_the_handover_handover_md_from_the_checkout_and_the_lane.py) | The handover: HANDOVER.md from the checkout and the lane |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads your fork and your lane and changes neither, so the pin does not matter here: leave acme wherever it is. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads your fork and your lane and changes neither, so the pin does not matter here: leave acme wherever it is. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads your fork and your lane and changes neither, so the pin does not matter here: leave acme wherever it is. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_04_the_lines_the_check_rests_on.py

The selftest runs every rule on documents, records and PDFs it makes up, with no fork and no lane: the rejected options as a list, a table and sub-sections, the cost model's volumes and date, every way a FAILURE-MODES command resolves or does not, pages from text and from a PDF's page tree, plain and packed, a rollback told from a promote, and the outsider's 403. commands/tests/test_capstone_check.py holds 31 more tests, on the canned fork and on a stand-in lane, and commands/tests/test_capstone_templates.py 13 on the templates of step 5.

**`step_01_the_rules_on_hand_made_input(session)` — The lines the check rests on / Do it: the rules on hand-made input**

The selftest runs every rule on documents, records and PDFs it makes up, with no fork and no lane: the rejected options as a list, a table and sub-sections, the cost model's volumes and date, every way a FAILURE-MODES command resolves or does not, pages from text and from a PDF's page tree, plain and packed, a rollback told from a promote, and the outsider's 403. commands/tests/test_capstone_check.py holds 31 more tests, on the canned fork and on a stand-in lane, and commands/tests/test_capstone_templates.py 13 on the templates of step 5.

Operation: bash — run in the operator shell, in the kit (the rules on hand-made input; no fork, no lane, Rs 0).

Expected shape, not a promised result:

```text
capstone_check selftest: ARCHITECTURE.md's rejected options (list, table, sub-section; a bare name is not argued), COST-MODEL.md's volumes, amounts, date and rate, FAILURE-MODES.md's entries and every way a command resolves or does not, pages from text and from a PDF's page tree (plain and packed), a rollback told from a promote, the lane smokes and the outsider's 403, each on hand-made input
```

### demo_05_the_check_offline_the_kit_as_it_ships_a_canned_capstone_your_fork.py

Run it in your kit checkout. If your checkout holds lesson 11.3's records, components 1, 4 and 8 read them and your output differs from the one below, which was run on a copy of the kit with no records at all. commands/tests/capstone_fork/ is Sahyadri Freight, a made-up logistics company whose corpus is a fleet safety manual and a driver handbook, 32 pages between them, with the four documents and the records lesson 11.3's controlled failure leaves: a mistyped model promoted by force, rolled back and repaired, with a smoke run around each step and the repair's gate report. The kit's tests lay it over a copy of the kit, so you do the same: a local clone of your checkout, the canned files over it, its two golden rows appended, then the check. The clone holds none of your records, so the output is the canned fork's alone. The check's rules are functions you can call. The cell loads the module, points a Fork at the canned fork and prints what the rules see: the smoke runs in order, the rollback they show, each report with its isolation rows, the tenant's pages, and how each FAILURE-MODES command resolves. Your four documents start from the kit's templates in capstone/templates/. Each is the canned fork's document emptied: the same headings, a {{...}} placeholder in every slot, 66 across the four, and a comment at the top saying what the check reads in it and what the defence reads. In your fork you copy them to its root, cp capstone/templates/*.md ., and replace every placeholder, braces included. Here the cell lays them as they ship over the canned fork's four, runs the check, counts the lines that still hold a placeholder, and puts the canned four back. In the fork you will defend, offline. The recording is the author's reference fork, built the way yours will be: a tenant of its own, make ingest-corpus, make roster, golden rows, make gate, lesson 11.3's rollback with a smoke run before and after, and the four documents, written from the templates.

**`step_01_the_kit_as_it_ships(session)` — The check, offline: the kit as it ships, a canned capstone, your fork / Do it: the kit as it ships**

Run it in your kit checkout. If your checkout holds lesson 11.3's records, components 1, 4 and 8 read them and your output differs from the one below, which was run on a copy of the kit with no records at all.

Operation: bash — run in the operator shell, in the kit (reads your checkout and runs make eval, a few seconds; no lane, Rs 0).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
>> capstone-check: the fork at /home/you/deploy_module_rag, offline: its files and records, and make eval. PROJECT=
   adds the lane's reads
   1  FAIL  A live URL behind IAP
            the fork deploys documind-ui behind IAP: --iap and --no-allow-unauthenticated (commands/lesson-12.4.sh)
          - no make smoke-deployed run in evals/reports/smoke-deployed.jsonl: make smoke-deployed PROJECT=<id> (lesson
            11.3) records one
          - no live eval report in evals/reports/ asked the isolation rows: make gate (lesson 11.2) writes one, as
            make eval-live REPORT=<file> does
   2  FAIL  Your own corpus, 30 pages or more, ingested
          - evals/corpus/ holds no tenant of your own, only the kit's (acme, globex, zeta): your corpus goes in
            evals/corpus/<your tenant>/, which make ingest-corpus uploads under that tenant
   3  PASS  An eval suite, 30 golden rows or more, with tenant isolation
            evals/golden.jsonl: 65 golden rows, 11 of them isolation rows
            make eval: evals/run_eval.py offline exits 0 (the golden set can go red, and still holds the rows that
            would)
   4  FAIL  One lane on top of the core: chat, media, SLM or graph
          - no make smoke-deployed run in evals/reports/smoke-deployed.jsonl: make smoke-deployed PROJECT=<id> (lesson
            11.3) records one
   5  FAIL  ARCHITECTURE.md, with the alternatives you rejected
          - ARCHITECTURE.md is missing from the fork's root: copy capstone/templates/ARCHITECTURE.md there from the
            kit, and replace each {{...}} placeholder in it
   6  FAIL  COST-MODEL.md at 1k, 10k and 100k queries a month
          - COST-MODEL.md is missing from the fork's root: copy capstone/templates/COST-MODEL.md there from the kit,
            and replace each {{...}} placeholder in it
   7  FAIL  FAILURE-MODES.md, four entries, each proved by a script
          - FAILURE-MODES.md is missing from the fork's root: copy capstone/templates/FAILURE-MODES.md there from the
            kit, and replace each {{...}} placeholder in it
   8  FAIL  RUNBOOK.md and one recorded rollback
          - RUNBOOK.md is missing from the fork's root: copy capstone/templates/RUNBOOK.md there from the kit, and
            replace each {{...}} placeholder in it
          - no make smoke-deployed run in evals/reports/smoke-deployed.jsonl: make smoke-deployed PROJECT=<id> (lesson
            11.3) records one
>> incomplete: components 1, 2, 4, 5, 6, 7 and 8 FAIL. A missing component is an incomplete submission, and the
   defence does not run
```

**`step_02_a_canned_capstone_that_passes(session)` — The check, offline: the kit as it ships, a canned capstone, your fork / Do it: a canned capstone that passes**

commands/tests/capstone_fork/ is Sahyadri Freight, a made-up logistics company whose corpus is a fleet safety manual and a driver handbook, 32 pages between them, with the four documents and the records lesson 11.3's controlled failure leaves: a mistyped model promoted by force, rolled back and repaired, with a smoke run around each step and the repair's gate report. The kit's tests lay it over a copy of the kit, so you do the same: a local clone of your checkout, the canned files over it, its two golden rows appended, then the check. The clone holds none of your records, so the output is the canned fork's alone.

Operation: bash — run in the operator shell, in the kit (a copy of the kit with the canned fork over it, then the check; Rs 0).

Expected shape, not a promised result:

```text
>> capstone-check: the fork at /tmp/sahyadri, offline: its files and records, and make eval. PROJECT= adds the lane's
   reads
   1  PASS  A live URL behind IAP
            the fork deploys documind-ui behind IAP: --iap and --no-allow-unauthenticated (commands/lesson-12.4.sh)
            a member was answered: GET /version said git_sha abc1234, gemini-3.6-flash, documind-rag@v3 (make
            smoke-deployed, 2026-11-17T10:30:00Z)
            a non-member was refused: every isolation row (11) answered 403 to the outsider
            (evals/reports/gate-documind-api-00043-fix.json)
   2  PASS  Your own corpus, 30 pages or more, ingested
            sahyadri's corpus: 2 documents, 32 pages as the ingest worker counts them
            a query cites one: sh-01 cited fleet_safety_manual_2026.md and passed
            (evals/reports/gate-documind-api-00043-fix.json)
   3  PASS  An eval suite, 30 golden rows or more, with tenant isolation
            evals/golden.jsonl: 67 golden rows, 11 of them isolation rows
            make eval: evals/run_eval.py offline exits 0 (the golden set can go red, and still holds the rows that
            would)
   4  PASS  One lane on top of the core: chat, media, SLM or graph
            chat: make smoke-chat passed in the last make smoke-deployed run (2026-11-17T10:30:00Z)
            media: make smoke-media passed in the last make smoke-deployed run (2026-11-17T10:30:00Z)
   5  PASS  ARCHITECTURE.md, with the alternatives you rejected
            ARCHITECTURE.md names 3 rejected options with a reason: GKE Autopilot for the API; A second vector
            database (Pinecone); Fine-tuning before prompting
   6  PASS  COST-MODEL.md at 1k, 10k and 100k queries a month
            COST-MODEL.md names the three volumes, 1k, 10k and 100k queries a month
            dual-priced: 10 amounts in rupees, 12 amounts in dollars
            dated 2026-11-18
            at 85 rupees to the dollar
   7  PASS  FAILURE-MODES.md, four entries, each proved by a script
            4 entries proved by a command the fork runs:
            "Pinned traffic hides a change": make gotcha-drill ID=pinned-traffic
            "A rollback keeps the bad template": make gotcha-drill ID=rollback-keeps-template
            "A poison upload pages an hour later": make poison TENANT=sahyadri PROJECT=documind-ai-YOUR-ID
            "A mistyped model answers 500": FAULT=model HOLD=1 PROJECT=documind-ai-YOUR-ID bash
            commands/incident-drill.sh
   8  PASS  RUNBOOK.md and one recorded rollback
            RUNBOOK.md says how to roll back
            a recorded rollback, the traffic left the revision the candidate tag names: documind-api-00042-typ ->
            documind-api-00041-kel, between the make smoke-deployed runs of 2026-11-17T09:20:00Z and
            2026-11-17T09:35:00Z; /version before: git_sha abc1234, gemini-3.6-flsh, documind-rag@v3; after: git_sha
            abc1234, gemini-3.6-flash, documind-rag@v3
>> complete: every one of the eight components PASSes. Nothing here is scored: the defence scores the five dimensions
```

**`step_03_the_records_with_the_kit_s_own_rules(session)` — The check, offline: the kit as it ships, a canned capstone, your fork / Do it: the records, with the kit's own rules**

The check's rules are functions you can call. The cell loads the module, points a Fork at the canned fork and prints what the rules see: the smoke runs in order, the rollback they show, each report with its isolation rows, the tenant's pages, and how each FAILURE-MODES command resolves.

Operation: bash — run in the operator shell, in the kit (the kit's own rules on the canned fork's records; Rs 0).

Expected shape, not a promised result:

```text
4 make smoke-deployed runs in evals/reports/smoke-deployed.jsonl, oldest first:
  2026-11-17T08:10:00Z  serving documind-api-00041-kel  candidate documind-api-00041-kel  PASS  /version: git_sha abc1234, gemini-3.6-flash, documind-rag@v3
  2026-11-17T09:20:00Z  serving documind-api-00042-typ  candidate documind-api-00042-typ  FAIL  /version: git_sha abc1234, gemini-3.6-flsh, documind-rag@v3
  2026-11-17T09:35:00Z  serving documind-api-00041-kel  candidate documind-api-00042-typ  PASS  /version: git_sha abc1234, gemini-3.6-flash, documind-rag@v3
  2026-11-17T10:30:00Z  serving documind-api-00043-fix  candidate documind-api-00043-fix  PASS  /version: git_sha abc1234, gemini-3.6-flash, documind-rag@v3
the rollback the check finds: documind-api-00042-typ -> documind-api-00041-kel, the traffic left the revision the candidate tag names
evals/reports/gate-documind-api-00043-fix.json: 67 rows, 11 isolation rows asked, every one refused: True
your own tenant: sahyadri; driver_handbook_2026.md 8 pages, fleet_safety_manual_2026.md 24 pages; 32 in all
FAILURE-MODES.md: 'Pinned traffic hides a change': Symptom yes; `make gotcha-drill ID=pinned-traffic` runs in the fork
FAILURE-MODES.md: 'A rollback keeps the bad template': Symptom yes; `make gotcha-drill ID=rollback-keeps-template` runs in the fork
FAILURE-MODES.md: 'A poison upload pages an hour later': Symptom yes; `make poison TENANT=sahyadri PROJECT=documind-ai-YOUR-ID` runs in the fork
FAILURE-MODES.md: 'A mistyped model answers 500': Symptom yes; `FAULT=model HOLD=1 PROJECT=documind-ai-YOUR-ID bash commands/incident-drill.sh` runs in the fork
```

**`step_04_your_four_documents_from_the_templates(session)` — The check, offline: the kit as it ships, a canned capstone, your fork / Do it: your four documents, from the templates**

Your four documents start from the kit's templates in capstone/templates/. Each is the canned fork's document emptied: the same headings, a {{...}} placeholder in every slot, 66 across the four, and a comment at the top saying what the check reads in it and what the defence reads. In your fork you copy them to its root, cp capstone/templates/*.md ., and replace every placeholder, braces included. Here the cell lays them as they ship over the canned fork's four, runs the check, counts the lines that still hold a placeholder, and puts the canned four back.

Operation: bash — run in the operator shell, in the kit (the templates over the canned fork's copy, then its four back; Rs 0).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
>> capstone-check: the fork at /tmp/sahyadri, offline: its files and records, and make eval. PROJECT= adds the lane's
   reads
   1  PASS  A live URL behind IAP
            the fork deploys documind-ui behind IAP: --iap and --no-allow-unauthenticated (commands/lesson-12.4.sh)
            a member was answered: GET /version said git_sha abc1234, gemini-3.6-flash, documind-rag@v3 (make
            smoke-deployed, 2026-11-17T10:30:00Z)
            a non-member was refused: every isolation row (11) answered 403 to the outsider
            (evals/reports/gate-documind-api-00043-fix.json)
   2  PASS  Your own corpus, 30 pages or more, ingested
            sahyadri's corpus: 2 documents, 32 pages as the ingest worker counts them
            a query cites one: sh-01 cited fleet_safety_manual_2026.md and passed
            (evals/reports/gate-documind-api-00043-fix.json)
   3  PASS  An eval suite, 30 golden rows or more, with tenant isolation
            evals/golden.jsonl: 67 golden rows, 11 of them isolation rows
            make eval: evals/run_eval.py offline exits 0 (the golden set can go red, and still holds the rows that
            would)
   4  PASS  One lane on top of the core: chat, media, SLM or graph
            chat: make smoke-chat passed in the last make smoke-deployed run (2026-11-17T10:30:00Z)
            media: make smoke-media passed in the last make smoke-deployed run (2026-11-17T10:30:00Z)
   5  FAIL  ARCHITECTURE.md, with the alternatives you rejected
          - ARCHITECTURE.md names 0 rejected options with a reason (and 3 without one: {{OPTION 1}}; {{OPTION 2}};
            {{OPTION 3}}): 3 or more, each with why (6 words or more)
   6  FAIL  COST-MODEL.md at 1k, 10k and 100k queries a month
            COST-MODEL.md names the three volumes, 1k, 10k and 100k queries a month
            at 85 rupees to the dollar
          - COST-MODEL.md gives 0 amounts in rupees (Rs, INR or ₹ and a figure) and 0 amounts in dollars ($ or USD and
            a figure): 3 or more of each, a pair for each volume
          - COST-MODEL.md carries no date (2026-11-20, or 20 Nov 2026): prices move
   7  FAIL  FAILURE-MODES.md, four entries, each proved by a script
          - 0 entries proved, 4 or more: an entry is a heading with a Symptom: line and a command in backticks that
            the fork can run
          - "{{FAILURE 1}}": `make gotcha-drill ID={{GOTCHA-ID}}`: ID={{GOTCHA-ID}} is not in ops/gotchas.json, lesson
            11.7's registry
          - "{{FAILURE 2}}": `make gotcha-drill ID={{GOTCHA-ID}} LIVE=1`: ID={{GOTCHA-ID}} is not in ops/gotchas.json,
            lesson 11.7's registry
          - "{{FAILURE 3}}": `make {{TARGET}}`: the fork's Makefile and mk/*.mk define no {{TARGET}} target
          - "{{FAILURE 4}}": `bash commands/{{SCRIPT}}.sh`: the fork holds no commands/{{SCRIPT}}.sh
   8  FAIL  RUNBOOK.md and one recorded rollback
            a recorded rollback, the traffic left the revision the candidate tag names: documind-api-00042-typ ->
            documind-api-00041-kel, between the make smoke-deployed runs of 2026-11-17T09:20:00Z and
            2026-11-17T09:35:00Z; /version before: git_sha abc1234, gemini-3.6-flsh, documind-rag@v3; after: git_sha
            abc1234, gemini-3.6-flash, documind-rag@v3
          - RUNBOOK.md does not say how to roll back: make rollback (lesson 11.3), or gcloud run services
            update-traffic
>> incomplete: components 5, 6, 7 and 8 FAIL. A missing component is an incomplete submission, and the defence does
   not run
exit 1
/tmp/sahyadri/ARCHITECTURE.md:8
/tmp/sahyadri/COST-MODEL.md:7
/tmp/sahyadri/FAILURE-MODES.md:18
/tmp/sahyadri/RUNBOOK.md:5
exit 0
```

**`step_05_your_fork(session)` — The check, offline: the kit as it ships, a canned capstone, your fork / Do it: your fork**

In the fork you will defend, offline. The recording is the author's reference fork, built the way yours will be: a tenant of its own, make ingest-corpus, make roster, golden rows, make gate, lesson 11.3's rollback with a smoke run before and after, and the four documents, written from the templates.

Operation: bash — run in the operator shell, in your fork (offline; Rs 0).

IDE adaptation: Read the check's verdict as the cell's answer: incomplete (exit 1) is work on your fork, and on a checkout that is still the kit it is what the check says, which stopped the demo before the lane's reads and the handover (22 October 2026). The step fails if the check stopped (make's Error 2) or printed no verdict.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/capstone_check.txt]
```

### demo_06_change_it_one_command_deleted_one_component_fails.py

An entry of FAILURE-MODES.md without a command is a symptom nobody can reproduce. The canned fork's first entry, "Pinned traffic hides a change", is proved by make gotcha-drill ID=pinned-traffic, lesson 11.7's offline drill. The cell deletes that one line with sed, runs the check, then copies the kit's canned file back and runs it once more, printing only the exit code.

**`step_01_definition(session)` — Change it: one command deleted, one component fails / Definition**

An entry of FAILURE-MODES.md without a command is a symptom nobody can reproduce. The canned fork's first entry, "Pinned traffic hides a change", is proved by make gotcha-drill ID=pinned-traffic, lesson 11.7's offline drill. The cell deletes that one line with sed, runs the check, then copies the kit's canned file back and runs it once more, printing only the exit code.

Operation: bash — run in the operator shell, in the kit (edits the canned fork's copy, then puts it back; Rs 0).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
>> capstone-check: the fork at /tmp/sahyadri, offline: its files and records, and make eval. PROJECT= adds the lane's
   reads
   1  PASS  A live URL behind IAP
            the fork deploys documind-ui behind IAP: --iap and --no-allow-unauthenticated (commands/lesson-12.4.sh)
            a member was answered: GET /version said git_sha abc1234, gemini-3.6-flash, documind-rag@v3 (make
            smoke-deployed, 2026-11-17T10:30:00Z)
            a non-member was refused: every isolation row (11) answered 403 to the outsider
            (evals/reports/gate-documind-api-00043-fix.json)
   2  PASS  Your own corpus, 30 pages or more, ingested
            sahyadri's corpus: 2 documents, 32 pages as the ingest worker counts them
            a query cites one: sh-01 cited fleet_safety_manual_2026.md and passed
            (evals/reports/gate-documind-api-00043-fix.json)
   3  PASS  An eval suite, 30 golden rows or more, with tenant isolation
            evals/golden.jsonl: 67 golden rows, 11 of them isolation rows
            make eval: evals/run_eval.py offline exits 0 (the golden set can go red, and still holds the rows that
            would)
   4  PASS  One lane on top of the core: chat, media, SLM or graph
            chat: make smoke-chat passed in the last make smoke-deployed run (2026-11-17T10:30:00Z)
            media: make smoke-media passed in the last make smoke-deployed run (2026-11-17T10:30:00Z)
   5  PASS  ARCHITECTURE.md, with the alternatives you rejected
            ARCHITECTURE.md names 3 rejected options with a reason: GKE Autopilot for the API; A second vector
            database (Pinecone); Fine-tuning before prompting
   6  PASS  COST-MODEL.md at 1k, 10k and 100k queries a month
            COST-MODEL.md names the three volumes, 1k, 10k and 100k queries a month
            dual-priced: 10 amounts in rupees, 12 amounts in dollars
            dated 2026-11-18
            at 85 rupees to the dollar
   7  FAIL  FAILURE-MODES.md, four entries, each proved by a script
            "A rollback keeps the bad template": make gotcha-drill ID=rollback-keeps-template
            "A poison upload pages an hour later": make poison TENANT=sahyadri PROJECT=documind-ai-YOUR-ID
            "A mistyped model answers 500": FAULT=model HOLD=1 PROJECT=documind-ai-YOUR-ID bash
            commands/incident-drill.sh
          - 3 entries proved, 4 or more: an entry is a heading with a Symptom: line and a command in backticks that
            the fork can run
          - "Pinned traffic hides a change": no command in backticks (make ..., python ..., bash ...)
   8  PASS  RUNBOOK.md and one recorded rollback
            RUNBOOK.md says how to roll back
            a recorded rollback, the traffic left the revision the candidate tag names: documind-api-00042-typ ->
            documind-api-00041-kel, between the make smoke-deployed runs of 2026-11-17T09:20:00Z and
            2026-11-17T09:35:00Z; /version before: git_sha abc1234, gemini-3.6-flsh, documind-rag@v3; after: git_sha
            abc1234, gemini-3.6-flash, documind-rag@v3
>> incomplete: component 7 FAILs. A missing component is an incomplete submission, and the defence does not run
exit 1
exit 0
```

### demo_07_your_lane_read_with_the_two_tokens.py

Three GETs and one describe, as you. The last line greps documind-ui's description for its IAP annotation; step 9 says why it is greped rather than named. Every offline line again, and a lane: line under components 1, 2, 4 and 8. Reads only; Rs 0.

**`step_01_the_reads_by_hand(session)` — Your lane, read with the two tokens / Do it: the reads by hand**

Three GETs and one describe, as you. The last line greps documind-ui's description for its IAP annotation; step 9 says why it is greped rather than named.

Operation: bash — run in the operator shell, in the kit (three GETs with the two tokens, one describe; Rs 0).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rest_reads.txt]
```

**`step_02_the_check_with_your_lane(session)` — Your lane, read with the two tokens / Do it: the check with your lane**

Every offline line again, and a lane: line under components 1, 2, 4 and 8. Reads only; Rs 0.

Operation: bash — run in the operator shell, in your fork (gcloud reads from an allow-list of 11, two tokens, three GETs; Rs 0).

IDE adaptation: Read the check's verdict as the cell's answer: incomplete (exit 1) is work on your fork, and on a checkout that is still the kit it is what the check says, which stopped the demo before the lane's reads and the handover (22 October 2026). The step fails if the check stopped (make's Error 2) or printed no verdict.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/capstone_live.txt]
```

### demo_08_the_handover_handover_md_from_the_checkout_and_the_lane.py

Without PROJECT= every section gives the checkout's half and says the lane was not given. The canned fork is a copy of the kit, so its checkout half is the kit's: the policies, the night job, the floors, the budget and the state bucket as the Makefile and Terraform declare them, plus the canned records under Revisions. In your fork, with PROJECT and REGION. Reads only. The file lands in the fork's root; the recording is the author's lane.

**`step_01_the_handover_offline_on_the_canned_fork(session)` — The handover: HANDOVER.md from the checkout and the lane / Do it: the handover, offline, on the canned fork**

Without PROJECT= every section gives the checkout's half and says the lane was not given. The canned fork is a copy of the kit, so its checkout half is the kit's: the policies, the night job, the floors, the budget and the state bucket as the Makefile and Terraform declare them, plus the canned records under Revisions.

Operation: bash — run in the operator shell, in the kit (writes HANDOVER.md into the canned fork; Rs 0).

Expected shape, not a promised result:

```text
>> handover: /tmp/sahyadri/HANDOVER.md, from this checkout only (PROJECT= adds the lane)
# Handover: DocuMind, this checkout

Written by `make handover` (commands/capstone_check.py handover) at YYYY-MM-DDTHH:MM:SSZ, from this checkout; PROJECT= adds what the lane shows. It read, and changed nothing. Each section gives what the checkout states, then what the lane shows; where the two differ, the lane is what runs. make handover writes the file whole each time: notes of your own belong in RUNBOOK.md, whose template is capstone/templates/RUNBOOK.md.

## Alert policies

17 policies declared in terraform/*.tf, each with what ops/runbooks.json says to do when it pages.

| Policy | Declared in | Applied | When it pages | On the lane |
|---|---|---|---|---|
| API p95 latency > 3s | alerts.tf | always | make remediate proposes a rollback | - |
| Unanswerable rate > 20% for a tenant | alerts.tf | always | make remediate proposes a rollback | - |
| documind-slm left warm: instances > 0 for 2 hours | alerts.tf | always | a person: the runbook's own step, make off, is for when no session is running, which only a person knows | - |
| documind-vllm left warm: instances > 0 for 2 hours | alerts.tf | always | a person: the runbook's own step, make off, is for when no session is running, which only a person knows | - |
| Ingest failed | alerts.tf | always | make remediate proposes a rollback | - |
| Ledger drift above zero for two nights | alerts.tf | when RECONCILE_JOB=true | a person: the ledger against the uploads bucket, not a revision: make reconcile prints the plan, and a person applies it | - |
| Nightly reconcile failed | alerts.tf | when RECONCILE_JOB=true | a person: a job's run, not a service's revision: a person reads the execution's logs and runs it again | - |
| Ingest dead-letter queue holds messages | alerts.tf | always | a person: an upload the worker refused twelve times: a person reads it, fixes or removes the object, then acknowledges it | - |
| Ingest subscription backlog: oldest message over 30 minutes | alerts.tf | always | a person: a queue, not a revision: a person reads what the worker logs and whether it answers, and a busy worker drains on its own | - |
| Desk router: fallback share above 1% for a tenant | desk_alerts.tf | when DESK_ROUTER_ALERTS=true | make remediate proposes a rollback | - |
| Desk router: L2 share above its 15% cap for a tenant | desk_alerts.tf | when DESK_ROUTER_ALERTS=true | a person: the router's thresholds decide it, and a change to TAU_OOS or ACCEPT_VOTES is a reviewed commit | - |
| Desk router: clarify or out_of_scope up more than 5 points week on week | desk_alerts.tf | when DESK_ROUTER_ALERTS=true | a person: a change in what people ask, over two weeks: the router's examples or a desk's switches, a person's call | - |
| Desk case queue: a case due within 24 hours and unacknowledged, or breached | desk_alerts.tf | always | a person: a case is its queue's people's to act on, and a sensitive queue's committee or contact's alone | - |
| A registered document arrived at a version nobody reviewed | desk_alerts.tf | always | a person: a person reads the new version before the pin follows it | - |
| Desk: a delegation was refused | desk_alerts.tf | always | a person: a refused caller is a security question for the operator: who can mint tokens as it | - |
| Desk gate check: failed share above 20% for a tenant | desk_alerts.tf | when DESK_GATE_ALERTS=true | make remediate proposes a rollback | - |
| Desk gate check: a door could not read which tenants are on | desk_alerts.tf | always | a person: Firestore, or the service account's access to it: a person reads the error | - |

## The night job

terraform/off.tf declares the Cloud Scheduler job `documind-off-nightly`: `0 23 * * *` in Asia/Kolkata, 23:00 IST, every night. It runs the Cloud Run job documind-off, which floors documind-slm, documind-vllm, documind-gateway, documind-ui to min-instances 0 where they are deployed; make off-now runs the same job on demand.

## Floors

The checkout: `MIN_INSTANCES ?= 0` in the Makefile, the UI's floor when make deploy-services deploys it (1 on a session day, 0 after), and the night job floors the GPU services, the gateway and the UI to 0 every night. A floor above 0 bills its instances while they idle.

## Revisions

- `.candidate-revision`: none in this checkout
- `.previous-revision`: none in this checkout
- the gate record (`evals/reports/gate.json`): documind-api-00043-fix, PASS, finished 2026-11-17T10:12:00Z; make promote-gated holds it for 24 hours
- the last make smoke-deployed run: 2026-11-17T10:30:00Z, serving documind-api-00043-fix, PASS

## CI trust

No confirmed inputs in this checkout (terraform/runbook-project.auto.tfvars.json, gitignored, is what make plan saves).

## Budget

The checkout: budget.tf's `DocuMind monthly budget`, `BUDGET_AMOUNT ?= 5000` in the Makefile (whole units of the billing account's currency; make up passes it), alerting at 50%, 80%, 100%, 120% forecast of it. A billing budget alerts and stops nothing.

## State bucket

Terraform keeps the lane's state in `gs://<project>-tfstate/documind/<project>/default.tfstate` (the Makefile's TFSTATE_BUCKET and TFSTATE_PREFIX defaults). make plan, make up and make down read it; without it, Terraform no longer knows what it made.

## Not read

- the lane: no PROJECT was given
```

**`step_02_the_handover_of_your_lane(session)` — The handover: HANDOVER.md from the checkout and the lane / Do it: the handover of your lane**

In your fork, with PROJECT and REGION. Reads only. The file lands in the fork's root; the recording is the author's lane.

Operation: bash — run in the operator shell, in your fork (reads the lane, writes HANDOVER.md into the fork; Rs 0).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/handover.txt]
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads your fork and your lane and changes neither, so the pin does not matter here: leave acme wherever it is. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads your fork and your lane and changes neither, so the pin does not matter here: leave acme wherever it is. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_11.8_Capstone_Handover_WIX.html`. All 41 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `755bf433e9168d8a73ccf0f5d43bcd6c529eb3a6`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
