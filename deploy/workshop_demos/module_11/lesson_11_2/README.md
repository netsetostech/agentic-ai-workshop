# Lesson 11.2: Evaluate and gate the exact candidate revision

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_candidate_as_the_console_and_lesson_11_1_s_run_show_it.py](demo_03_the_candidate_as_the_console_and_lesson_11_1_s_run_show_it.py) | The candidate, as the console and lesson 11.1's run show it |
| 4 | [demo_04_make_gate_and_make_promote_gated_line_by_line.py](demo_04_make_gate_and_make_promote_gated_line_by_line.py) | make gate and make promote-gated, line by line |
| 5 | [demo_05_on_your_lane_the_candidate_named_the_token_s_audience_and_the_gate.py](demo_05_on_your_lane_the_candidate_named_the_token_s_audience_and_the_gate.py) | On your lane: the candidate named, the token's audience, and the gate |
| 6 | [demo_06_the_record_read_back_against_cloud_run_and_gate_check_alone.py](demo_06_the_record_read_back_against_cloud_run_and_gate_check_alone.py) | The record read back against Cloud Run, and gate-check alone |
| 7 | [demo_07_change_it_a_record_that_names_another_revision.py](demo_07_change_it_a_record_that_names_another_revision.py) | Change it: a record that names another revision |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's gate asks acme's golden rows, and lesson 11.1's dispatch judged the same candidate with acme on the kit's own index: pin it the same way for the duration, so the two verdicts are about one lane, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's gate asks acme's golden rows, and lesson 11.1's dispatch judged the same candidate with acme on the kit's own index: pin it the same way for the duration, so the two verdicts are about one lane, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's gate asks acme's golden rows, and lesson 11.1's dispatch judged the same candidate with acme on the kit's own index: pin it the same way for the duration, so the two verdicts are about one lane, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_candidate_as_the_console_and_lesson_11_1_s_run_show_it.py

If your candidate came from lesson 11.1's dispatch, read what its release-candidate job printed. The cell finds the run and the job, then keeps the lines that name the revision, compare its /version with the commit, and give the live gate's verdict, each after the name of the step that printed it.

**`step_01_the_dispatch_s_own_lines(session)` — The candidate, as the console and lesson 11.1's run show it / Do it: the dispatch's own lines**

If your candidate came from lesson 11.1's dispatch, read what its release-candidate job printed. The cell finds the run and the job, then keeps the lines that name the revision, compare its /version with the commit, and give the live gate's verdict, each after the name of the step that printed it.

Operation: bash — run in the operator shell, in the kit, if lesson 11.1's dispatch made your candidate (GitHub reads; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ci_gate.txt]
```

### demo_04_make_gate_and_make_promote_gated_line_by_line.py

commands/tests/test_release_gate.py plays every case on this page against a stand-in gcloud that keeps one lane's traffic table and revisions in a file. Where a POSIX sh is installed, as in Cloud Shell, it also runs the recipes of record-candidate, promote-gated, promote and rollback as make hands them to the shell, and shows that only the gated revision is promoted. It calls nothing in Google Cloud and costs nothing; it starts a process for every stand-in call, so give it a minute or two.

**`step_01_the_kit_s_own_tests(session)` — make gate and make promote-gated, line by line / Do it: the kit's own tests**

commands/tests/test_release_gate.py plays every case on this page against a stand-in gcloud that keeps one lane's traffic table and revisions in a file. Where a POSIX sh is installed, as in Cloud Shell, it also runs the recipes of record-candidate, promote-gated, promote and rollback as make hands them to the shell, and shows that only the gated revision is promoted. It calls nothing in Google Cloud and costs nothing; it starts a process for every stand-in call, so give it a minute or two.

Operation: bash — run in the operator shell, in the kit (stand-ins only: no Google call, no cost).

Expected shape, not a promised result:

```text
.............................
----------------------------------------------------------------------
Ran 29 tests in Ns

OK
```

### demo_05_on_your_lane_the_candidate_named_the_token_s_audience_and_the_gate.py

make record-candidate is the line make release-candidate ends with, run on its own. The cell then prints the traffic table and whether the file and the tag name one revision. The cell mints two tokens as documind-ui-sa, one for the canonical URL and one for the tag URL, and calls the tag URL twice with each: /version, which checks no token itself, and /v1/sources for acme, which goes through verify_iap and acme's roster but calls no model. About ten minutes: every golden row as the member, then the isolation rows again as the outsider. run_eval.py's own lines stream between the gate's two blocks; lesson 4.3 reads them.

**`step_01_name_the_candidate(session)` — On your lane: the candidate named, the token's audience, and the gate / Do it: name the candidate**

make record-candidate is the line make release-candidate ends with, run on its own. The cell then prints the traffic table and whether the file and the tag name one revision.

Operation: bash — run in the operator shell, in the kit (one describe; writes .candidate-revision).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/record_candidate.txt]
```

**`step_02_the_tag_url_and_the_audience(session)` — On your lane: the candidate named, the token's audience, and the gate / Do it: the tag URL and the audience**

The cell mints two tokens as documind-ui-sa, one for the canonical URL and one for the tag URL, and calls the tag URL twice with each: /version, which checks no token itself, and /v1/sources for acme, which goes through verify_iap and acme's roster but calls no model.

Operation: bash — run in the operator shell, in the kit (two tokens, four GETs, no model call).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/audience.txt]
```

**`step_03_the_gate(session)` — On your lane: the candidate named, the token's audience, and the gate / Do it: the gate**

About ten minutes: every golden row as the member, then the isolation rows again as the outsider. run_eval.py's own lines stream between the gate's two blocks; lesson 4.3 reads them.

Operation: bash — run in the operator shell, in the kit (every golden row, about ten minutes).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/gate.txt]
```

### demo_06_the_record_read_back_against_cloud_run_and_gate_check_alone.py

Do it: the record against the lane Do it: gate-check, and nothing after it

**`step_01_the_record_against_the_lane(session)` — The record read back against Cloud Run, and gate-check alone / Do it: the record against the lane**

Do it: the record against the lane

Operation: bash — run in the operator shell, in the kit (two Cloud Run Admin API reads and your files; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/record_vs_lane.txt]
```

**`step_02_gate_check_and_nothing_after_it(session)` — The record read back against Cloud Run, and gate-check alone / Do it: gate-check, and nothing after it**

Do it: gate-check, and nothing after it

Operation: bash — run in the operator shell, in the kit (the check alone: nothing moves).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/gate_check.txt]
```

### demo_07_change_it_a_record_that_names_another_revision.py

A copy of your record with one field changed, offered to make promote-gated through GATE_FILE. The cell copies your record to evals/reports/scratch-gate.json with one field changed: the revision, set to the one serving now. It offers the copy to make promote-gated through GATE_FILE, deletes it, and runs gate-check on your own record, which it never touched. The copy is green, fresh, judged by today's rules, and its report still hashes to its sha256: everything in it is true except the name.

**`step_01_change_it_a_record_that_names_another_revi(session)` — Change it: a record that names another revision / Change it: a record that names another revision**

A copy of your record with one field changed, offered to make promote-gated through GATE_FILE. The cell copies your record to evals/reports/scratch-gate.json with one field changed: the revision, set to the one serving now. It offers the copy to make promote-gated through GATE_FILE, deletes it, and runs gate-check on your own record, which it never touched. The copy is green, fresh, judged by today's rules, and its report still hashes to its sha256: everything in it is true except the name.

Operation: bash — run in the operator shell, in the kit (a copy of your record, refused; it is deleted afterwards).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
evals/reports/scratch-gate.json: your record, with documind-api-00042-xyz replaced by documind-api-00041-kel, the revision serving now
REFUSED: the gate record evals/reports/scratch-gate.json does not let make promote move traffic:
  - another revision: the record names documind-api-00041-kel, and make promote would move traffic to documind-api-00042-xyz (.candidate-revision). The gate judged documind-api-00041-kel; make gate judges documind-api-00042-xyz
make: *** [mk/release.mk:46: promote-gated] Error 1
exit 2
your record: gate-check exit 0
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's gate asks acme's golden rows, and lesson 11.1's dispatch judged the same candidate with acme on the kit's own index: pin it the same way for the duration, so the two verdicts are about one lane, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's gate asks acme's golden rows, and lesson 11.1's dispatch judged the same candidate with acme on the kit's own index: pin it the same way for the duration, so the two verdicts are about one lane, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_11.2_Gated_Candidate_WIX.html`. All 40 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `213f9987f72054b35fe7a03511bfcd6540d6f02b`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
