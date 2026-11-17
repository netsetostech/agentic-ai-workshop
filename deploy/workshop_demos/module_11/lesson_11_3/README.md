# Lesson 11.3: Promote, roll back and repair a controlled failure

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 5 | [demo_05_make_smoke_deployed_and_make_incident_line_by_line.py](demo_05_make_smoke_deployed_and_make_incident_line_by_line.py) | make smoke-deployed and make incident, line by line |
| 6 | [demo_06_on_your_lane_promote_break_it_roll_back.py](demo_06_on_your_lane_promote_break_it_roll_back.py) | On your lane: promote, break it, roll back |
| 7 | [demo_07_on_your_lane_the_repair_through_the_gate_and_the_proof.py](demo_07_on_your_lane_the_repair_through_the_gate_and_the_proof.py) | On your lane: the repair through the gate, and the proof |
| 8 | [demo_08_errors_by_revision_from_the_request_logs.py](demo_08_errors_by_revision_from_the_request_logs.py) | Errors by revision, from the request logs |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's two gates ask acme's golden rows, as lesson 11.2's gate did, and that gate judged its candidate with acme on the kit's own index: keep the pin for the duration, so every verdict on this page is about one lane, and put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [cleanup/demo_06_on_your_lane_promote_break_it_roll_back.py](cleanup/demo_06_on_your_lane_promote_break_it_roll_back.py) — At lesson end: time is the shell's own: when the command ends, it prints how long it took. The manifest's proof for this lesson asks for under two minutes. Between those two cells, every answer from your API is a 500. If you have to stop there, or a cell fails, run the cell below before you leave: it reads which revision serves all of documind-api's traffic and the model that revision runs, and runs make rollback only while that model is gemini-3.6-flsh. Otherwise it changes nothing and says so. The lesson's finish runs it as well. The template still names gemini-3.6-flsh until step 7's repair deploys a good revision.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's two gates ask acme's golden rows, as lesson 11.2's gate did, and that gate judged its candidate with acme on the kit's own index: keep the pin for the duration, so every verdict on this page is about one lane, and put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's two gates ask acme's golden rows, as lesson 11.2's gate did, and that gate judged its candidate with acme on the kit's own index: keep the pin for the duration, so every verdict on this page is about one lane, and put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_05_make_smoke_deployed_and_make_incident_line_by_line.py

commands/tests/test_release_repair.py runs this lesson against lesson 11.2's stand-in gcloud, extended with the template, gcloud run services update, the service and revision lists, and a stand-in make for the smokes. Where a POSIX sh is installed, as in Cloud Shell, 2 of its tests run the Makefile's own recipes: the whole controlled failure from make promote-gated back to the gated state, including that a make release-candidate after the rollback inherits the typo, and make smoke-deployed itself, with its one HTTP request caught by a local proxy. It calls nothing in Google Cloud and costs nothing; it starts a process for every stand-in call, so give it a few minutes.

**`step_01_the_kit_s_own_tests(session)` — make smoke-deployed and make incident, line by line / Do it: the kit's own tests**

commands/tests/test_release_repair.py runs this lesson against lesson 11.2's stand-in gcloud, extended with the template, gcloud run services update, the service and revision lists, and a stand-in make for the smokes. Where a POSIX sh is installed, as in Cloud Shell, 2 of its tests run the Makefile's own recipes: the whole controlled failure from make promote-gated back to the gated state, including that a make release-candidate after the rollback inherits the typo, and make smoke-deployed itself, with its one HTTP request caught by a local proxy. It calls nothing in Google Cloud and costs nothing; it starts a process for every stand-in call, so give it a few minutes.

Operation: bash — run in the operator shell, in the kit (stand-ins only: no Google call, no cost).

Expected shape, not a promised result:

```text
.......................
----------------------------------------------------------------------
Ran 23 tests in Ns

OK
```

### demo_06_on_your_lane_promote_break_it_roll_back.py

gate-check reads lesson 11.2's record, the files first and then the lane; when every check passes, make promote moves the traffic and prints what /version now says. make candidate makes a revision from the template, with every setting it passes at the Makefile's default except the one you name. It takes no traffic, gets the candidate tag and goes into .candidate-revision. The same gate as lesson 11.2's, on the revision the file now names: about ten minutes of rows, and every row that reaches the model fails. run_eval.py's lines stream between the gate's two blocks. The verdict is recorded, red, and make reports release.py's exit 1 on its last line, Error 1, before exiting 2 itself. First make promote-gated, which the red record stops at its first recipe line, line 46 of mk/release.mk, so its make promote never starts. Then plain make promote, which reads no record and moves all the traffic to the mistyped revision. Go straight on to the next cell. make smoke-deployed names the smokes it skips and runs the rest; make incident reads what the smokes logged, with the gate record and the lane. time is the shell's own: when the command ends, it prints how long it took. The manifest's proof for this lesson asks for under two minutes. Do it: the smokes and the incident, after the rollback The cell reads documind-api and its revisions from the Cloud Run Admin API's v1 resources, the same JSON gcloud run services describe --format=json prints, without release.py: each recent revision's traffic, tag, image and model, then the template's, and whether the template is what serves. Each revision's image is a digest and the template's a tag, so the cell compares the template through the revision it made last, as make incident does. Run it now, before the repair, while they differ.

**`step_01_promote_lesson_11_2_s_candidate(session)` — On your lane: promote, break it, roll back / Do it: promote lesson 11.2's candidate**

gate-check reads lesson 11.2's record, the files first and then the lane; when every check passes, make promote moves the traffic and prints what /version now says.

Operation: bash — run in the operator shell, in the kit (gate-check, then one traffic move).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/promote_gated.txt]
```

**`step_02_the_mistyped_model_as_a_candidate(session)` — On your lane: promote, break it, roll back / Do it: the mistyped model, as a candidate**

make candidate makes a revision from the template, with every setting it passes at the Makefile's default except the one you name. It takes no traffic, gets the candidate tag and goes into .candidate-revision.

Operation: bash — run in the operator shell, in the kit (a revision with no traffic and a mistyped model).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/candidate_typo.txt]
```

**`step_03_the_gate_on_it(session)` — On your lane: promote, break it, roll back / Do it: the gate on it**

The same gate as lesson 11.2's, on the revision the file now names: about ten minutes of rows, and every row that reaches the model fails. run_eval.py's lines stream between the gate's two blocks. The verdict is recorded, red, and make reports release.py's exit 1 on its last line, Error 1, before exiting 2 itself.

Operation: bash — run in the operator shell, in the kit (every golden row, about ten minutes; no model call succeeds).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/gate_typo.txt]
```

**`step_04_refused_then_forced(session)` — On your lane: promote, break it, roll back / Do it: refused, then forced**

First make promote-gated, which the red record stops at its first recipe line, line 46 of mk/release.mk, so its make promote never starts. Then plain make promote, which reads no record and moves all the traffic to the mistyped revision. Go straight on to the next cell.

Operation: bash — run in the operator shell, in the kit (the refusal, then the forced traffic move: your API answers 500 until the rollback).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/promote_refused_forced.txt]
```

**`step_05_the_smokes_and_the_incident(session)` — On your lane: promote, break it, roll back / Do it: the smokes, and the incident**

make smoke-deployed names the smokes it skips and runs the rest; make incident reads what the smokes logged, with the gate record and the lane.

Operation: bash — run in the operator shell, in the kit, straight after (the smokes, then the incident read).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke_incident_red.txt]
```

**`step_06_the_rollback_timed(session)` — On your lane: promote, break it, roll back / Do it: the rollback, timed**

time is the shell's own: when the command ends, it prints how long it took. The manifest's proof for this lesson asks for under two minutes.

Operation: bash — run in the operator shell, in the kit, straight after (one traffic move, timed).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rollback_timed.txt]
```

**`step_07_the_smokes_and_the_incident_after_the_roll(session)` — On your lane: promote, break it, roll back / Do it: the smokes and the incident, after the rollback**

Do it: the smokes and the incident, after the rollback

Operation: bash — run in the operator shell, in the kit, after the rollback (the smokes, then the incident read).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke_incident_after.txt]
```

**`step_08_the_template_from_cloud_run_s_api(session)` — On your lane: promote, break it, roll back / Read it: the template, from Cloud Run's API**

The cell reads documind-api and its revisions from the Cloud Run Admin API's v1 resources, the same JSON gcloud run services describe --format=json prints, without release.py: each recent revision's traffic, tag, image and model, then the template's, and whether the template is what serves. Each revision's image is a digest and the template's a tag, so the cell compares the template through the revision it made last, as make incident does. Run it now, before the repair, while they differ.

Operation: bash — run in the operator shell, in the kit, before the repair (two Cloud Run Admin API reads; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/template_read.txt]
```

### demo_07_on_your_lane_the_repair_through_the_gate_and_the_proof.py

Run the Repair: line your make incident printed after the rollback. On a lane whose serving revision runs the Makefile's defaults it is the first line below; if yours names more settings, use yours. Then the gate: about ten minutes and about Rs 29. Do it: promote it through the gate The smokes of your deployed services, then make incident on the lane as it is now. The proof is both: make smoke-deployed exits 0, and make incident exits 0 with the gated state.

**`step_01_the_repair_candidate_and_its_gate(session)` — On your lane: the repair through the gate, and the proof / Do it: the repair candidate, and its gate**

Run the Repair: line your make incident printed after the rollback. On a lane whose serving revision runs the Makefile's defaults it is the first line below; if yours names more settings, use yours. Then the gate: about ten minutes and about Rs 29.

Operation: bash — run in the operator shell, in the kit (the Repair line make incident printed, then every golden row).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/candidate_gate_repair.txt]
```

**`step_02_promote_it_through_the_gate(session)` — On your lane: the repair through the gate, and the proof / Do it: promote it through the gate**

Do it: promote it through the gate

Operation: bash — run in the operator shell, in the kit (gate-check, then one traffic move).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/promote_repair.txt]
```

**`step_03_the_proof(session)` — On your lane: the repair through the gate, and the proof / Do it: the proof**

The smokes of your deployed services, then make incident on the lane as it is now. The proof is both: make smoke-deployed exits 0, and make incident exits 0 with the gated state.

Operation: bash — run in the operator shell, in the kit (the proof: the smokes, then the incident read).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/smoke_incident_proof.txt]
```

### demo_08_errors_by_revision_from_the_request_logs.py

Do it: the requests, by revision

**`step_01_the_requests_by_revision(session)` — Errors by revision, from the request logs / Do it: the requests, by revision**

Do it: the requests, by revision

Operation: bash — run in the operator shell, in the kit, after the proof (Cloud Logging reads; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/errors_by_revision.txt]
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's two gates ask acme's golden rows, as lesson 11.2's gate did, and that gate judged its candidate with acme on the kit's own index: keep the pin for the duration, so every verdict on this page is about one lane, and put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's two gates ask acme's golden rows, as lesson 11.2's gate did, and that gate judged its candidate with acme on the kit's own index: keep the pin for the duration, so every verdict on this page is about one lane, and put it back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### cleanup/demo_06_on_your_lane_promote_break_it_roll_back.py

At lesson end: time is the shell's own: when the command ends, it prints how long it took. The manifest's proof for this lesson asks for under two minutes. Between those two cells, every answer from your API is a 500. If you have to stop there, or a cell fails, run the cell below before you leave: it reads which revision serves all of documind-api's traffic and the model that revision runs, and runs make rollback only while that model is gemini-3.6-flsh. Otherwise it changes nothing and says so. The lesson's finish runs it as well. The template still names gemini-3.6-flsh until step 7's repair deploys a good revision.

**`step_01_the_rollback_timed(session)` — On your lane: promote, break it, roll back / Do it: the rollback, timed**

time is the shell's own: when the command ends, it prints how long it took. The manifest's proof for this lesson asks for under two minutes. Between those two cells, every answer from your API is a 500. If you have to stop there, or a cell fails, run the cell below before you leave: it reads which revision serves all of documind-api's traffic and the model that revision runs, and runs make rollback only while that model is gemini-3.6-flsh. Otherwise it changes nothing and says so. The lesson's finish runs it as well. The template still names gemini-3.6-flsh until step 7's repair deploys a good revision.

Operation: bash — run in the operator shell, in the kit, when you finish the lesson, not now (a traffic move only while the mistyped model serves).

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs: the cell's own commands, which put back what the lesson changed.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_11.3_Promote_Rollback_WIX.html`. All 51 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `ebc973c7ecc9467df73d5fb1e4b5daf99da5814c`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
