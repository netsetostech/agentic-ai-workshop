# Lesson 8.2: Change a chunker, re-embed and reconcile

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_the_kit_s_code_two_lines_one_rule_and_the_test_that_holds_them.py](demo_03_the_kit_s_code_two_lines_one_rule_and_the_test_that_holds_them.py) | The kit's code: two lines, one rule, and the test that holds them |
| 4 | [demo_04_measure_before_you_deploy_the_handbook_at_eight_sizes_rs_0.py](demo_04_measure_before_you_deploy_the_handbook_at_eight_sizes_rs_0.py) | Measure before you deploy: the handbook at eight sizes, Rs 0 |
| 5 | [demo_05_do_it_edit_both_twins_then_build_and_deploy_a_tagged_worker.py](demo_05_do_it_edit_both_twins_then_build_and_deploy_a_tagged_worker.py) | Do it: edit both twins, then build and deploy a tagged worker |
| 6 | [demo_06_re_issue_the_handbook_as_new_bytes_and_read_the_counts.py](demo_06_re_issue_the_handbook_as_new_bytes_and_read_the_counts.py) | Re-issue the handbook as new bytes, and read the counts |
| 7 | [demo_07_rest_which_image_serves_and_how_many_tokens_a_new_chunk_is.py](demo_07_rest_which_image_serves_and_how_many_tokens_a_new_chunk_is.py) | REST: which image serves, and how many tokens a new chunk is |
| 8 | [demo_08_reconcile_the_ledger_against_the_bucket_the_index_against_the_rows_the_golden_ro.py](demo_08_reconcile_the_ledger_against_the_bucket_the_index_against_the_rows_the_golden_ro.py) | Reconcile: the ledger against the bucket, the index against the rows, the golden rows |
| 9 | [demo_09_put_it_back_the_original_tag_version_1_the_checkout.py](demo_09_put_it_back_the_original_tag_version_1_the_checkout.py) | Put it back: the original tag, version 1, the checkout |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson re-cuts the handbook in the kit's own rows; acme's managed stores cut the same text by rules of their own, so point acme at the kit's rows for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson re-cuts the handbook in the kit's own rows; acme's managed stores cut the same text by rules of their own, so point acme at the kit's rows for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson re-cuts the handbook in the kit's own rows; acme's managed stores cut the same text by rules of their own, so point acme at the kit's rows for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_the_kit_s_code_two_lines_one_rule_and_the_test_that_holds_them.py

From the kit, with nothing changed. The grep keeps the lines that matter: each failure's name and message, the count and the verdict.

**`step_01_the_twin_test_on_the_kit_as_it_is_rs_0(session)` — The kit's code: two lines, one rule, and the test that holds them / Do it: the twin test on the kit as it is, Rs 0**

From the kit, with nothing changed. The grep keeps the lines that matter: each failure's name and message, the count and the verdict.

Operation: bash — run in the operator shell, in $DEMO_ROOT (no credentials, no cost).

Expected shape, not a promised result:

```text
Ran 11 tests in ...s
OK
```

### demo_04_measure_before_you_deploy_the_handbook_at_eight_sizes_rs_0.py

Do it: the handbook through the kit's chunker

**`step_01_the_handbook_through_the_kit_s_chunker(session)` — Measure before you deploy: the handbook at eight sizes, Rs 0 / Do it: the handbook through the kit's chunker**

Do it: the handbook through the kit's chunker

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; the kit's own chunker, Rs 0).

Expected shape, not a promised result:

```text
pair      chunks reused embedded characters requests  rupees largest
2000/200     283    283        0          0        0    0.00     599
1000/100     283    283        0          0        0    0.00     599
 600/100     283    283        0          0        0    0.00     599
 599/50      283    283        0          0        0    0.00     599
 598/50      298    268       30       9735        1    0.02     593
 500/50      555     11      544     170348        4    0.36     443
 400/50      555     11      544     170348        4    0.36     368
 300/50      827     11      816     183948        5    0.39     285
left whole at 400/50, so reused: preamble, NP-03, PB-02, LV-01, LV-07, EXP-12, PR-05, IT-SEC-04, SEC-09, FIN-02, WFH-01
cut at 400/50: 272 sections of 563 to 599 characters, into 544 windows
the longest section: 599 characters (15 of them), so no size from 599 up cuts anything
```

### demo_05_do_it_edit_both_twins_then_build_and_deploy_a_tagged_worker.py

The edit is one sed line per file. Make it in the worker alone first and run the test: this is the mistake the test exists for, and you should see what it says. Then make it in the twin and run the test again. The edit is one sed line per file. Make it in the worker alone first and run the test: this is the mistake the test exists for, and you should see what it says. Then make it in the twin and run the test again. Three tests fail, and the first message names both files and both pairs. The second says what the mistake would do to the lane: acme/cgst_act_2017.md, cut into 1,536 chunks by the worker and 390 by everything offline. The third is the pinned difference, now three windows against one. Now the twin: The worker on your lane runs the image a build pushed under a tag, and the tag is GIT_SHA: by default the checkout's commit, read with git rev-parse. Your edit did not make a commit, so a build with the default tag would push the edited worker under the commit's own tag, as if it were the kit at that commit. When that commit is the one the running worker was built from, the edit replaces the original image under its own name, and a later "redeploy the original tag" deploys the edit. The cell below therefore reads the tag the worker runs now, keeps it in ~/lesson82-orig-sha (written once, so running the cell again cannot overwrite it), and builds under that tag plus -c400. It names the service and the deploy script on purpose: without SERVICES=ingest the build is every one of the seven images, and without SCRIPTS=commands/lesson-12.5.sh the deploy is every service, all under a tag only the worker has. The build's own lines go to a log; the grep shows make's >> lines, the deploy's result and any error.

**`step_01_definition(session)` — Do it: edit both twins, then build and deploy a tagged worker / Definition**

The edit is one sed line per file. Make it in the worker alone first and run the test: this is the mistake the test exists for, and you should see what it says. Then make it in the twin and run the test again.

Operation: bash — run in the operator shell, in $DEMO_ROOT (one twin only, on purpose).

IDE adaptation: Read the twin test's red as the cell's answer: with the worker alone edited it must fail, and its exit 1 under pipefail stopped the demo with services/ingest/main.py edited and the put-back step never run (22 October 2026). The step now fails only if the test passes.

Expected shape, not a promised result:

```text
services/ingest/main.py:105:CHUNK_CHARS, CHUNK_OVERLAP = 400, 50
shared/documind_corpus.py:38:CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200                     # services/ingest/main.py
FAIL: test_one_size_and_one_overlap (commands.tests.test_twin_chunker.TheTwinsAgree.test_one_size_and_one_overlap)
AssertionError: services/ingest/main.py sets CHUNK_CHARS, CHUNK_OVERLAP = 400, 50 and shared/documind_corpus.py sets 2000, 200: a chunker change edits both lines
FAIL: test_the_corpus_at_the_kits_pair (commands.tests.test_twin_chunker.TheTwinsAgree.test_the_corpus_at_the_kits_pair)
AssertionError: acme/cgst_act_2017.md: 1536 chunks from services/ingest/main.py, 390 from shared/documind_corpus.py
FAIL: test_the_two_differences_the_kit_keeps (commands.tests.test_twin_chunker.TheTwinsAgree.test_the_two_differences_the_kit_keeps)
AssertionError: the invoice: services/ingest/main.py gives [('w0', None), ('w1', None), ('w2', None)], shared/documind_corpus.py [('p1-0', 1)]; the kit keeps w<k> with no page against p1-<k> on page 1
Ran 11 tests in ...s
FAILED (failures=3)
```

**`step_02_definition(session)` — Do it: edit both twins, then build and deploy a tagged worker / Definition**

The edit is one sed line per file. Make it in the worker alone first and run the test: this is the mistake the test exists for, and you should see what it says. Then make it in the twin and run the test again. Three tests fail, and the first message names both files and both pairs. The second says what the mistake would do to the lane: acme/cgst_act_2017.md, cut into 1,536 chunks by the worker and 390 by everything offline. The third is the pinned difference, now three windows against one. Now the twin:

Operation: bash — run in the operator shell, in $DEMO_ROOT (the other twin).

Expected shape, not a promised result:

```text
services/ingest/main.py:105:CHUNK_CHARS, CHUNK_OVERLAP = 400, 50
shared/documind_corpus.py:38:CHUNK_CHARS, CHUNK_OVERLAP = 400, 50                     # services/ingest/main.py
Ran 11 tests in ...s
OK
 M services/ingest/main.py
 M shared/documind_corpus.py
```

**`step_03_the_tag_and_the_build(session)` — Do it: edit both twins, then build and deploy a tagged worker / The tag, and the build**

The worker on your lane runs the image a build pushed under a tag, and the tag is GIT_SHA: by default the checkout's commit, read with git rev-parse. Your edit did not make a commit, so a build with the default tag would push the edited worker under the commit's own tag, as if it were the kit at that commit. When that commit is the one the running worker was built from, the edit replaces the original image under its own name, and a later "redeploy the original tag" deploys the edit. The cell below therefore reads the tag the worker runs now, keeps it in ~/lesson82-orig-sha (written once, so running the cell again cannot overwrite it), and builds under that tag plus -c400. It names the service and the deploy script on purpose: without SERVICES=ingest the build is every one of the seven images, and without SCRIPTS=commands/lesson-12.5.sh the deploy is every service, all under a tag only the worker has. The build's own lines go to a log; the grep shows make's >> lines, the deploy's result and any error.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Cloud Build, then one deploy: about ten minutes).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/build_deploy.txt]
```

### demo_06_re_issue_the_handbook_as_new_bytes_and_read_the_counts.py

make reindex is lesson 1.6's release command: the offline gate scoped to the handbook, the upload under the handbook's name, whose event reaches the worker by the push lesson 8.1 traced, and the wait for the worker's line.

**`step_01_write_the_new_bytes_then_re_issue(session)` — Re-issue the handbook as new bytes, and read the counts / Do it: write the new bytes, then re-issue**

make reindex is lesson 1.6's release command: the offline gate scoped to the handbook, the upload under the handbook's name, whose event reaches the worker by the push lesson 8.1 traced, and the wait for the worker's line.

Operation: bash — run in the operator shell, in $DEMO_ROOT (writes the new bytes to your home directory, then one re-issue).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/reindex.txt]
```

### demo_07_rest_which_image_serves_and_how_many_tokens_a_new_chunk_is.py

gcloud run services describe printed one line in step 5. Underneath it is the Cloud Run Admin API, and its service resource says more: the image in the service's template, the newest revision that is ready, where the traffic goes, and, one call further, every revision the service has kept with the image each one runs. Step 9's revert deploys one of those images again, so read them now, while the edited worker serves. The kit counts characters: the window is 400 characters, and the batcher estimates tokens as characters divided by 3. The embedding model counts tokens, and reads at most 2,048 of one text, cutting the rest unless told not to (lesson B.2 read that on Google's page on 7 October 2026). The largest chunk at 400/50 is GEN-003's first window, 368 characters. The cell cuts the handbook at 400/50 in memory, finds that window, and sends it to text-embedding-005's REST endpoint in us-central1, as the worker's client would, under the worker's task type. The response carries the model's own count beside the vector.

**`step_01_definition(session)` — REST: which image serves, and how many tokens a new chunk is / Definition**

gcloud run services describe printed one line in step 5. Underneath it is the Cloud Run Admin API, and its service resource says more: the image in the service's template, the newest revision that is ready, where the traffic goes, and, one call further, every revision the service has kept with the image each one runs. Step 9's revert deploys one of those images again, so read them now, while the edited worker serves.

Operation: bash — run in the operator shell (a Python cell: two GETs on the Cloud Run Admin API).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rest_revisions.txt]
```

**`step_02_the_tokens_in_the_largest_new_chunk(session)` — REST: which image serves, and how many tokens a new chunk is / The tokens in the largest new chunk**

The kit counts characters: the window is 400 characters, and the batcher estimates tokens as characters divided by 3. The embedding model counts tokens, and reads at most 2,048 of one text, cutting the rest unless told not to (lesson B.2 read that on Google's page on 7 October 2026). The largest chunk at 400/50 is GEN-003's first window, 368 characters. The cell cuts the handbook at 400/50 in memory, finds that window, and sends it to text-embedding-005's REST endpoint in us-central1, as the worker's client would, under the worker's task type. The response carries the model's own count beside the vector.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell: one embedding, a fraction of a paisa).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/token_check.txt]
```

### demo_08_reconcile_the_ledger_against_the_bucket_the_index_against_the_rows_the_golden_ro.py

Lesson 1.8 ran the nightly walk: every object in the bucket against its ledger row in sources/. For each object, a generation the ledger already holds is ok; any other generation has its bytes hashed, and the hash decides. The bytes the ledger already names are a touch (record the generation, index nothing); bytes a claim indexed that the ledger never recorded are a backfill; bytes no claim holds are a reingest, which rewrites the object onto itself so the worker's own path runs again. Drift counts the sources the ledger had wrong. Nothing in either function reads the chunker. The walk compares names, generations and hashes of bytes, so it proves the ledger names what the bucket holds; it cannot prove which rule cut the rows. Run the kit's own planner over a stand-in lane, four nights in this lesson's life: Nothing in either function reads the chunker. The walk compares names, generations and hashes of bytes, so it proves the ledger names what the bucket holds; it cannot prove which rule cut the rows. Run the kit's own planner over a stand-in lane, four nights in this lesson's life: The second night is the case the walk exists for: had the re-issue's push been lost, the ledger would still name version 1 at generation 2, the walk would hash generation 3, find bytes no claim holds, and rewrite the object so the worker indexes it, cut by whatever pair the worker runs that night. The same bytes can be cut two ways depending on when they arrive. Now the real walk, the plan only, and the versions view after it: The ledger row is a summary. The rows are the evidence: the cell counts the handbook's rows by version and state, finds the longest current row, and checks whether two current rows hold version 1's vectors: NP-03, which the new rule left whole, and GEN-003, which it cut. Then it counts every tenant's current rows in Firestore and reads the Vector Search index's own count. The re-cut changed 544 vectors in the same index the questions search, so lesson 1.6's live gate, scoped to the handbook, is the check that matters. Every one of the ten rows asks about a real clause, and every real clause kept its text and its vector: what moved is the 544 windows of generated text beside them, now shorter and more numerous. The gate says whether the clauses still win.

**`step_01_definition(session)` — Reconcile: the ledger against the bucket, the index against the rows, the golden rows / Definition**

Lesson 1.8 ran the nightly walk: every object in the bucket against its ledger row in sources/. For each object, a generation the ledger already holds is ok; any other generation has its bytes hashed, and the hash decides. The bytes the ledger already names are a touch (record the generation, index nothing); bytes a claim indexed that the ledger never recorded are a backfill; bytes no claim holds are a reingest, which rewrites the object onto itself so the worker's own path runs again. Drift counts the sources the ledger had wrong. Nothing in either function reads the chunker. The walk compares names, generations and hashes of bytes, so it proves the ledger names what the bucket holds; it cannot prove which rule cut the rows. Run the kit's own planner over a stand-in lane, four nights in this lesson's life:

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; the kit's planner on a stand-in, Rs 0).

Expected shape, not a promised result:

```text
the re-issue landed: bucket and ledger at generation 3   ok        drift 0
its push was lost: the ledger still names generation 2   reingest  drift 1
the same bytes written again (generation 4)              touch     drift 0
after the revert: version 1 again, at generation 5       ok        drift 0
```

**`step_02_definition(session)` — Reconcile: the ledger against the bucket, the index against the rows, the golden rows / Definition**

Nothing in either function reads the chunker. The walk compares names, generations and hashes of bytes, so it proves the ledger names what the bucket holds; it cannot prove which rule cut the rows. Run the kit's own planner over a stand-in lane, four nights in this lesson's life: The second night is the case the walk exists for: had the re-issue's push been lost, the ledger would still name version 1 at generation 2, the walk would hash generation 3, find bytes no claim holds, and rewrite the object so the worker indexes it, cut by whatever pair the worker runs that night. The same bytes can be cut two ways depending on when they arrive. Now the real walk, the plan only, and the versions view after it:

Operation: bash — run in the operator shell, in $DEMO_ROOT (the plan only: nothing is applied).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/reconcile.txt]
```

**`step_03_the_rows_and_the_index_read_directly(session)` — Reconcile: the ledger against the bucket, the index against the rows, the golden rows / The rows and the index, read directly**

The ledger row is a summary. The rows are the evidence: the cell counts the handbook's rows by version and state, finds the longest current row, and checks whether two current rows hold version 1's vectors: NP-03, which the new rule left whole, and GEN-003, which it cut. Then it counts every tenant's current rows in Firestore and reads the Vector Search index's own count.

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell: Firestore reads, one count, one GET).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/index_vs_ledger.txt]
```

**`step_04_the_gate_the_handbook_s_golden_rows_asked(session)` — Reconcile: the ledger against the bucket, the index against the rows, the golden rows / The gate: the handbook's golden rows, asked again**

The re-cut changed 544 vectors in the same index the questions search, so lesson 1.6's live gate, scoped to the handbook, is the check that matters. Every one of the ten rows asks about a real clause, and every real clause kept its text and its vector: what moved is the 544 windows of generated text beside them, now shorter and more numerous. The gate says whether the clauses still win.

Operation: bash — run in the operator shell, in $DEMO_ROOT (ten questions; a few rupees).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/eval_live.txt]
```

### demo_09_put_it_back_the_original_tag_version_1_the_checkout.py

The order matters. Deploy the original tag first: from that moment every document the worker ingests is cut at 2000/200 again, and nothing else can be cut at 400/50 while you work. Then upload version 1's bytes: the worker finds a version it retired 30 days or less ago and answers with the undo, flipping version 1's 283 rows back and retiring the new version's 555. The undo cuts nothing, so it would bring back version 1's chunks under either worker; the deploy is what decides how the next upload is cut. The tag comes from the file step 5 wrote, so a new shell is no obstacle. The order matters. Deploy the original tag first: from that moment every document the worker ingests is cut at 2000/200 again, and nothing else can be cut at 400/50 while you work. Then upload version 1's bytes: the worker finds a version it retired 30 days or less ago and answers with the undo, flipping version 1's 283 rows back and retiring the new version's 555. The undo cuts nothing, so it would bring back version 1's chunks under either worker; the deploy is what decides how the next upload is cut. The tag comes from the file step 5 wrote, so a new shell is no obstacle. Expect back to ingest:COMMIT, the deploy's lines, the service's image back at ingest:COMMIT on a newer revision, and then make reindex's line: ingest_reactivated, version 1's key acme_497809ffbaa6..., 283 chunks, 283 reused, 0 embedded, 555 retired. Last, the checkout. The test runs once more so the kit you leave is the kit the course ships, and passes:

**`step_01_definition(session)` — Put it back: the original tag, version 1, the checkout / Definition**

The order matters. Deploy the original tag first: from that moment every document the worker ingests is cut at 2000/200 again, and nothing else can be cut at 400/50 while you work. Then upload version 1's bytes: the worker finds a version it retired 30 days or less ago and answers with the undo, flipping version 1's 283 rows back and retiring the new version's 555. The undo cuts nothing, so it would bring back version 1's chunks under either worker; the deploy is what decides how the next upload is cut. The tag comes from the file step 5 wrote, so a new shell is no obstacle.

Operation: bash — run in the operator shell, in $DEMO_ROOT (one deploy, no build; then version 1 again).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/revert.txt]
```

**`step_02_definition(session)` — Put it back: the original tag, version 1, the checkout / Definition**

The order matters. Deploy the original tag first: from that moment every document the worker ingests is cut at 2000/200 again, and nothing else can be cut at 400/50 while you work. Then upload version 1's bytes: the worker finds a version it retired 30 days or less ago and answers with the undo, flipping version 1's 283 rows back and retiring the new version's 555. The undo cuts nothing, so it would bring back version 1's chunks under either worker; the deploy is what decides how the next upload is cut. The tag comes from the file step 5 wrote, so a new shell is no obstacle. Expect back to ingest:COMMIT, the deploy's lines, the service's image back at ingest:COMMIT on a newer revision, and then make reindex's line: ingest_reactivated, version 1's key acme_497809ffbaa6..., 283 chunks, 283 reused, 0 embedded, 555 retired. Last, the checkout. The test runs once more so the kit you leave is the kit the course ships, and passes:

Operation: bash — run in the operator shell, in $DEMO_ROOT (the checkout put back).

Expected shape, not a promised result:

```text
services/ingest/main.py:105:CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200
shared/documind_corpus.py:38:CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200                     # services/ingest/main.py
Ran 11 tests in ...s
OK
the checkout matches the kit again
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson re-cuts the handbook in the kit's own rows; acme's managed stores cut the same text by rules of their own, so point acme at the kit's rows for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson re-cuts the handbook in the kit's own rows; acme's managed stores cut the same text by rules of their own, so point acme at the kit's rows for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_8.2_Rechunk_Reembed_WIX.html`. All 46 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `5111868eecf916b3400fd9d5899661c81313622a`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
