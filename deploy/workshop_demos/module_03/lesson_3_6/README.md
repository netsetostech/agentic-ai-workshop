# Lesson 3.6: Check quotes and version prompts

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_offline_nine_quotes_through_both_measures_and_the_gate_s_own_lines_over_a_stand.py](demo_03_offline_nine_quotes_through_both_measures_and_the_gate_s_own_lines_over_a_stand.py) | Offline: nine quotes through both measures, and the gate's own lines over a stand-in API |
| 4 | [demo_04_your_lane_what_the_ui_shows_as_a_quote_then_a_source_s_quotes_held_against_their.py](demo_04_your_lane_what_the_ui_shows_as_a_quote_then_a_source_s_quotes_held_against_their.py) | Your lane: what the UI shows as a quote, then a source's quotes held against their passages |
| 5 | [demo_05_the_prompt_s_version_the_label_the_text_its_sha256_and_the_check.py](demo_05_the_prompt_s_version_the_label_the_text_its_sha256_and_the_check.py) | The prompt's version: the label, the text, its sha256 and the check |
| 6 | [demo_06_the_change_in_memory_rule_5_weakened_on_the_bench_and_the_sha256_it_would_regist.py](demo_06_the_change_in_memory_rule_5_weakened_on_the_bench_and_the_sha256_it_would_regist.py) | The change in memory: rule 5 weakened on the bench, and the sha256 it would register |
| 7 | [demo_07_ship_it_v4_on_a_branch_checked_built_and_answering_on_a_candidate.py](demo_07_ship_it_v4_on_a_branch_checked_built_and_answering_on_a_candidate.py) | Ship it: v4 on a branch, checked, built, and answering on a candidate |
| 8 | [demo_08_the_rows_name_the_prompt_the_candidate_taken_down_and_v4_spent.py](demo_08_the_rows_name_the_prompt_the_candidate_taken_down_and_v4_spent.py) | The rows name the prompt; the candidate taken down, and v4 spent |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads the chunk ids of acme's answers and of the passages read back beside them, so point acme at the kit's own index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads the chunk ids of acme's answers and of the passages read back beside them, so point acme at the kit's own index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads the chunk ids of acme's answers and of the passages read back beside them, so point acme at the kit's own index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_offline_nine_quotes_through_both_measures_and_the_gate_s_own_lines_over_a_stand.py

Do it: nine quotes, two measures The cell plays the API. Each row's /v1/query reply carries the row's figure and one citation, made by resolve() from a draft, so its quote reaches the gate exactly as rag-api would hand it on. Each row's /v1/passages reply is six handbook passages, the row's own clause first. Four rows are planted: lk-04 quotes its probation sentence under NP-03's number, lk-06 paraphrases, lk-08 leaves the quote empty, and lk-09's pool comes back without the passage it cites. The other six quote the first sentence of their clause.

**`step_01_nine_quotes_two_measures(session)` — Offline: nine quotes through both measures, and the gate's own lines over a stand-in API / Do it: nine quotes, two measures**

Do it: nine quotes, two measures

Operation: bash — run in the operator shell, in the kit (a Python cell; Rs 0: nothing leaves the machine).

Expected shape, not a promised result:

```text
case                                    chars  quote_check  judge_citations
the sentence, under its own passage        76  own          supported
a line break, in capitals                  69  own          supported
the same sentence, under [2]               76  elsewhere    supported
a paraphrase                               40  absent       not supported
revision 2's figure                        76  absent       not supported
an empty quote, filled in by resolve()    234  substituted  supported
_draft()'s cut of a whole section         200  own          not supported
an elision, mid-sentence                   59  absent       not supported
a passage the pool did not hold            76  unread       supported
quote_check: own 3, elsewhere 1, absent 3, substituted 1, unread 1 | judge_citations: supported 5 of 9
```

**`step_02_the_gate_s_own_lines_over_a_stand_in_api(session)` — Offline: nine quotes through both measures, and the gate's own lines over a stand-in API / Do it: the gate's own lines, over a stand-in API**

The cell plays the API. Each row's /v1/query reply carries the row's figure and one citation, made by resolve() from a draft, so its quote reaches the gate exactly as rag-api would hand it on. Each row's /v1/passages reply is six handbook passages, the row's own clause first. Four rows are planted: lk-04 quotes its probation sentence under NP-03's number, lk-06 paraphrases, lk-08 leaves the quote empty, and lk-09's pool comes back without the passage it cites. The other six quote the first sentence of their clause.

Operation: bash — run in the operator shell, in the kit (the gate against a stand-in API this cell plays; Rs 0; writes evals/reports/standin36.json).

Expected shape, not a promised result:

```text
scoped to hr_policy_2026.md: 10 row(s) cite it
  10 rows (10 answerable, 0 not) against https://stand-in.invalid

  [PASS] request_success_rate  100.0%  (threshold 100%; 10 rows)
  [PASS] answerable_rate       100.0%  (threshold 80%; 10 rows)
  [PASS] citation_rate         100.0%  (threshold 95%; 10 rows)
  [PASS] citation_valid_rate   100.0%  (threshold 100%; 10 rows)
  [PASS] must_contain_rate     100.0%  (threshold 85%; 10 rows)
  [PASS] correct_rate          100.0%  (threshold 68%; 10 rows)
  [ -- ] refusal_rate            0.0%  (threshold 90%; no rows in scope; 0 rows)
  [ -- ] media_kind_rate         0.0%  (threshold 80%; no rows in scope; 0 rows)
  [ -- ] isolation_403_rate      0.0%  (threshold 100%; no rows in scope; 0 rows)
  [info] quote_support_rate     90.0%  (quoted words found in the tenant's corpus text; not a threshold - a Doc AI extraction and a pypdf mirror hyphenate differently)
  [info] quote_passage_rate     66.7%  (6 of 9 answered rows' quotes in the passage they cite; elsewhere 1, absent 1, substituted 1, unread 1; not a threshold)
  [info] must_retrieve_recall   95.0%  (19 of 20 anchors in the pool /v1/passages returned, over 10 answerable rows; not a threshold)

  shape        rows   ok   pass
  lookup          9    9      9
  version         1    1      1
  latency ms  p50  1500  p95  1500   (round trip, 10 rows)

  report: evals/reports/standin36.json
  All thresholds met.
exit 0
```

### demo_04_your_lane_what_the_ui_shows_as_a_quote_then_a_source_s_quotes_held_against_their.py

Do it: the scoped gate, the switch on The cell reads the report the gate wrote and prints each citation's verdict, the position of the passage it names, and the quote's first words; then any row whose pool could not be read or came back without one of its anchors.

**`step_01_the_scoped_gate_the_switch_on(session)` — Your lane: what the UI shows as a quote, then a source's quotes held against their passages / Do it: the scoped gate, the switch on**

Do it: the scoped gate, the switch on

Operation: bash — run in the operator shell, in the kit (ten answers, then ten pool reads: a few rupees).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/quotes_live.txt]
```

**`step_02_every_citation_s_verdict(session)` — Your lane: what the UI shows as a quote, then a source's quotes held against their passages / Do it: every citation's verdict**

The cell reads the report the gate wrote and prints each citation's verdict, the position of the passage it names, and the quote's first words; then any row whose pool could not be read or came back without one of its anchors.

Operation: bash — run in the operator shell, in the kit (reads the report; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/quotes_live_cites.txt]
```

### demo_05_the_prompt_s_version_the_label_the_text_its_sha256_and_the_check.py

Do it: the check

**`step_01_the_check(session)` — The prompt's version: the label, the text, its sha256 and the check / Do it: the check**

Do it: the check

Operation: bash — run in the operator shell, in the kit (offline: no project, no credential, Rs 0).

Expected shape, not a promised result:

```text
python commands/prompt_pin.py
prompt:   documind-rag@v3 (services/rag-api/config.py: prompt_id@prompt_version, as /version reports it)
text:     SYSTEM + DATED_RULE, 604 characters, as generate() joins them (services/rag-api/generator.py)
sha256:   543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e
registry: documind-rag@v3 has this sha256 (services/rag-api/prompt_versions.json): the text is the one its version names
exit 0
```

### demo_06_the_change_in_memory_rule_5_weakened_on_the_bench_and_the_sha256_it_would_regist.py

Do it: the weakened rule, on the same rows

**`step_01_the_weakened_rule_on_the_same_rows(session)` — The change in memory: rule 5 weakened on the bench, and the sha256 it would register / Do it: the weakened rule, on the same rows**

Do it: the weakened rule, on the same rows

Operation: bash — run in the operator shell, in the kit (ten pool reads, then ten answers from the kit's generate() in your shell: a few rupees).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/bench_v4.txt]
```

### demo_07_ship_it_v4_on_a_branch_checked_built_and_answering_on_a_candidate.py

Do it: the branch, and rule 5 in both copies Do it: the check refuses the old label The cell sets the version and adds the line, taking the sha256 from prompt_pin's own reader of the two strings, so the registry gets exactly what the check will compute. Then the check, and the unit test the dry run runs on every push of the learner repository. Do it: commit Do it: build the image, and stage the candidate The workflow's own check, by hand: each URL's /version, with a token minted for the live URL, beside this checkout's short sha. Do it: the candidate's quotes Do it: v3 against v4, quote by quote

**`step_01_the_branch_and_rule_5_in_both_copies(session)` — Ship it: v4 on a branch, checked, built, and answering on a candidate / Do it: the branch, and rule 5 in both copies**

Do it: the branch, and rule 5 in both copies

Operation: bash — run in the operator shell, in the kit (a branch of your clone; two files edited).

Expected shape, not a promised result:

```text
Switched to a new branch 'prompt-v4'
services/rag-api/generator.py: rule 5 now reads 'A quote sums up the clause that answers - at most fifteen words, in plain language.'
evals/make_trainset.py: rule 5 now reads 'A quote sums up the clause that answers - at most fifteen words, in plain language.'
 evals/make_trainset.py        | 2 +-
 services/rag-api/generator.py | 2 +-
 2 files changed, 2 insertions(+), 2 deletions(-)
```

**`step_02_the_check_refuses_the_old_label(session)` — Ship it: v4 on a branch, checked, built, and answering on a candidate / Do it: the check refuses the old label**

Do it: the check refuses the old label

Operation: bash — run in the operator shell, in the kit (the check, which should fail).

IDE adaptation: The refusal is the observation: make prompt-version must exit 2 with the registry's own words for the edited text under the old label. Under the demo's set -e it stopped the step before the page's echo, and the kit was left on prompt-v4 with rule 5 edited (21 October 2026). Any other exit, or a 2 without those words, fails.

Expected shape, not a promised result:

```text
python commands/prompt_pin.py
prompt:   documind-rag@v3 (services/rag-api/config.py: prompt_id@prompt_version, as /version reports it)
text:     SYSTEM + DATED_RULE, 601 characters, as generate() joins them (services/rag-api/generator.py)
sha256:   269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8
registry: documind-rag@v3 has another sha256, 543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e: SYSTEM or DATED_RULE changed and prompt_version did not
A changed prompt needs a new version. Set prompt_version to "v4" in services/rag-api/config.py, then add
    "documind-rag@v4": "269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8"
to "versions" in services/rag-api/prompt_versions.json, keeping the lines already there.
make: *** [mk/generation.mk:27: prompt-version] Error 1
exit 2
```

**`step_03_name_it_v4_register_it_and_check_again(session)` — Ship it: v4 on a branch, checked, built, and answering on a candidate / Do it: name it v4, register it, and check again**

The cell sets the version and adds the line, taking the sha256 from prompt_pin's own reader of the two strings, so the registry gets exactly what the check will compute. Then the check, and the unit test the dry run runs on every push of the learner repository.

Operation: bash — run in the operator shell, in the kit (two more files edited; then the check and the unit test the dry run runs).

Expected shape, not a promised result:

```text
services/rag-api/config.py: prompt_version v4
services/rag-api/prompt_versions.json: "documind-rag@v4": "269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8"
python commands/prompt_pin.py
prompt:   documind-rag@v4 (services/rag-api/config.py: prompt_id@prompt_version, as /version reports it)
text:     SYSTEM + DATED_RULE, 601 characters, as generate() joins them (services/rag-api/generator.py)
sha256:   269dec90134e07beb3449813e1eb156c803568aa370bb52baa3a87aab8b2f6e8
registry: documind-rag@v4 has this sha256 (services/rag-api/prompt_versions.json): the text is the one its version names
exit 0
.......
----------------------------------------------------------------------
Ran 7 tests in 0.xxxs

OK
```

**`step_04_commit(session)` — Ship it: v4 on a branch, checked, built, and answering on a candidate / Do it: commit**

Do it: commit

Operation: bash — run in the operator shell, in the kit (one commit on the branch; nothing is pushed).

Expected shape, not a promised result:

```text
COMMIT Prompt v4: rule 5 asks for a summary of the clause

 evals/make_trainset.py                | 2 +-
 services/rag-api/config.py            | 2 +-
 services/rag-api/generator.py         | 2 +-
 services/rag-api/prompt_versions.json | 3 ++-
 4 files changed, 5 insertions(+), 4 deletions(-)
```

**`step_05_build_the_image_and_stage_the_candidate(session)` — Ship it: v4 on a branch, checked, built, and answering on a candidate / Do it: build the image, and stage the candidate**

Do it: build the image, and stage the candidate

Operation: bash — run in the operator shell, in the kit (one Cloud Build of the API's image, then a revision with no traffic: minutes).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ship_v4.txt]
```

**`step_06_the_label_on_both_urls(session)` — Ship it: v4 on a branch, checked, built, and answering on a candidate / Do it: the label on both URLs**

The workflow's own check, by hand: each URL's /version, with a token minted for the live URL, beside this checkout's short sha.

Operation: bash — run in the operator shell, in the kit (two GETs: the live revision and the candidate).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/version_v4.txt]
```

**`step_07_the_candidate_s_quotes(session)` — Ship it: v4 on a branch, checked, built, and answering on a candidate / Do it: the candidate's quotes**

Do it: the candidate's quotes

Operation: bash — run in the operator shell, in the kit (the same ten questions to the candidate: a few rupees).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/quotes_candidate.txt]
```

**`step_08_v3_against_v4_quote_by_quote(session)` — Ship it: v4 on a branch, checked, built, and answering on a candidate / Do it: v3 against v4, quote by quote**

Do it: v3 against v4, quote by quote

Operation: bash — run in the operator shell, in the kit (reads the two reports; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/quotes_compare.txt]
```

### demo_08_the_rows_name_the_prompt_the_candidate_taken_down_and_v4_spent.py

Do it: the rows, by revision, event and version Removing the tag ends the candidate's URL. Deleting .candidate-revision means a stray make promote stops with an error instead of moving traffic to v4. Then main again, whose four files say v3, and the check on them. The branch stays.

**`step_01_the_rows_by_revision_event_and_version(session)` — The rows name the prompt; the candidate taken down, and v4 spent / Do it: the rows, by revision, event and version**

Do it: the rows, by revision, event and version

Operation: bash — run in the operator shell (one Cloud Logging read and one describe; changes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/rows_v4.txt]
```

**`step_02_take_the_candidate_down(session)` — The rows name the prompt; the candidate taken down, and v4 spent / Do it: take the candidate down**

Removing the tag ends the candidate's URL. Deleting .candidate-revision means a stray make promote stops with an error instead of moving traffic to v4. Then main again, whose four files say v3, and the check on them. The branch stays.

Operation: bash — run in the operator shell, in the kit (the tag and its record removed, main checked out; the branch kept).

Expected shape, not a promised result:

```text
...
the candidate URL now: HTTP 404
Switched to branch 'main'
Your branch is up to date with 'origin/main'.
python commands/prompt_pin.py
prompt:   documind-rag@v3 (services/rag-api/config.py: prompt_id@prompt_version, as /version reports it)
text:     SYSTEM + DATED_RULE, 604 characters, as generate() joins them (services/rag-api/generator.py)
sha256:   543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e
registry: documind-rag@v3 has this sha256 (services/rag-api/prompt_versions.json): the text is the one its version names
exit 0
  prompt-v4
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads the chunk ids of acme's answers and of the passages read back beside them, so point acme at the kit's own index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson reads the chunk ids of acme's answers and of the passages read back beside them, so point acme at the kit's own index for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_3.6_Quote_Checks_WIX.html`. All 58 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `57e9f5eb63ef41d359c4f7a586351df4a6732eb6`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
