# Lesson 2.6: Decide answer-or-refuse with a System One model (Jev)

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_a_refusal_in_the_ui_and_what_it_paid_for.py](demo_03_a_refusal_in_the_ui_and_what_it_paid_for.py) | A refusal in the UI, and what it paid for |
| 4 | [demo_04_the_kit_s_code_two_refusals_in_the_handler_and_the_evidence_rule.py](demo_04_the_kit_s_code_two_refusals_in_the_handler_and_the_evidence_rule.py) | The kit's code: two refusals in the handler, and the evidence rule |
| 5 | [demo_05_the_decision_eval_for_rs_0_a_higher_floor_and_jev_s_switch.py](demo_05_the_decision_eval_for_rs_0_a_higher_floor_and_jev_s_switch.py) | The decision eval for Rs 0, a higher floor, and Jev's switch |
| 6 | [demo_06_the_rule_and_the_generator_on_your_lane_s_pools.py](demo_06_the_rule_and_the_generator_on_your_lane_s_pools.py) | The rule and the generator on your lane's pools |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Optional extensions

- [optional/demo_07_against_the_gate_refusal_recall_false_answers_calibration_latency_and_rupees.py](optional/demo_07_against_the_gate_refusal_recall_false_answers_calibration_latency_and_rupees.py) — All 65 rows on the author's lane, each arm held against the gate's 0.90, the false answers by id, what refusing first would save and lose, and where Jev could sit after the cohort. The author ran all 65 rows on the author's lane and saved the run. Its report is below. Every figure in this step's tables that is not the Rs 0 lane's is computed from that saved file, when this page is built, by decide.py's own summarise(), calibration(), by_confidence() and latency(). The same command runs on your lane if you want your own.

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

### demo_03_a_refusal_in_the_ui_and_what_it_paid_for.py

First the row's truth, from the file every eval reads: First the row's truth, from the file every eval reads: Then the question as documind-ui-sa, through /v1/query, which generates, and /v1/passages, which stops at the reranker:

**`step_01_the_golden_row_and_the_same_question_from(session)` — A refusal in the UI, and what it paid for / Do it: the golden row, and the same question from the shell**

First the row's truth, from the file every eval reads:

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: one line of the golden set).

Expected shape, not a promised result:

```text
{
 "id": "rf-01",
 "shape": "refusal",
 "question": "What is ACME's sabbatical policy?",
 "tenant": "acme",
 "must_contain": [],
 "must_retrieve": [],
 "answerable": false,
 "note": "Was 'parental leave' until the real Maternity Benefit Acts joined ACME's corpus, which made twenty-six weeks a defensible answer. A refusal row has to ask for something the corpus really does not hold."
}
```

**`step_02_the_golden_row_and_the_same_question_from(session)` — A refusal in the UI, and what it paid for / Do it: the golden row, and the same question from the shell**

First the row's truth, from the file every eval reads: Then the question as documind-ui-sa, through /v1/query, which generates, and /v1/passages, which stops at the reranker:

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell: one generator call, about Rs 0.23 of input by the kit's own count and at most Rs 1.31 of output; the passages call costs nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/ui_refusal.txt]
```

### demo_04_the_kit_s_code_two_refusals_in_the_handler_and_the_evidence_rule.py

Do it: the rule's arithmetic on three rows

**`step_01_the_rule_s_arithmetic_on_three_rows(session)` — The kit's code: two refusals in the handler, and the evidence rule / Do it: the rule's arithmetic on three rows**

Do it: the rule's arithmetic on three rows

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: nothing leaves the machine).

Expected shape, not a promised result:

```text
rf-01 (acme, refusal, answerable False): What is ACME's sabbatical policy?
   sabbatical     idf  8.09   not in the pool
   policy         idf  4.20   in the pool
   acme           idf  1.77   not in the pool
   share 0.30 against EVIDENCE_FLOOR 0.5: the rule says refuse
rf-02 (acme, refusal, answerable False): How many casual leave days do I get?
   casual         idf  3.98   in the pool
   leave          idf  3.49   in the pool
   days           idf  1.19   in the pool
   share 1.00 against EVIDENCE_FLOOR 0.5: the rule says answer
lk-01 (acme, lookup, answerable True): What is the per-trip cap on domestic travel reimbursement?
   trip           idf  6.99   in the pool
   domestic       idf  5.14   in the pool
   reimbursement  idf  4.48   in the pool
   travel         idf  4.24   in the pool
   cap            idf  2.89   in the pool
   share 1.00 against EVIDENCE_FLOOR 0.5: the rule says answer
```

### demo_05_the_decision_eval_for_rs_0_a_higher_floor_and_jev_s_switch.py

Do it: all 65 rows, Rs 0 Raise the floor and the rule buys refusals with answers. The same run at 0.70: shared/system_one.py is the only door to Jev, and decide() its only entry point. It never raises: every outcome is a result with a verdict of answer, refuse, skipped or error, and only the first two are decisions. The mode is read at call time, and off returns at once. An empty pool is refused in code, as rag-api refuses it, before any mode could ask Jev. Recorded mode reads the recorded file and nothing else. Live mode checks the tenant's data_region first, failing closed to in, then builds the payload from the question and the passages' text with identifiers masked, and only then reaches the adapter seam: _headers(), _request() and _parse(), which PR 2.6-C fills once TypeSafe documents its API. Until then _request() raises before any key is read or any socket opens, and decide() turns that into an error row, which no rate counts as a refusal. Run the Rs 0 eval with JEV_MODE=recorded on zeta's 10 rows, then call decide() in each mode, with the data regions make roster writes standing in for the Firestore read:

**`step_01_all_65_rows_rs_0(session)` — The decision eval for Rs 0, a higher floor, and Jev's switch / Do it: all 65 rows, Rs 0**

Do it: all 65 rows, Rs 0

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: no lane and no model; a few minutes, because it ranks the tenant's whole corpus for every row).

Expected shape, not a promised result:

```text
... 10/65 rows
  ... 20/65 rows
  ... 30/65 rows
  ... 40/65 rows
  ... 50/65 rows
  ... 60/65 rows
== answer or refuse: the decision eval (lesson 2.6) ==
  rows       65 golden rows: 47 answerable, 18 not
  pool       the Rs 0 lane, top 5: documind_tools.retrieve(passages=True) on the local profile over the kit's
             corpus (2757 chunks), its gate the evidence rule at 0.50
  rule       an empty pool, or evidence under 0.50 of the question's information, is refused (Rs 0)
  generator  --local has no lane: the generator needs one (replay a saved run: --from FILE)
  jev        JEV_MODE=off: Jev not available, nothing sent

  rule       65 decided (5 by code: an empty pool), 0 errors, 0 skipped
             answer rate     47/47 = 100.0% [92.4%, 100.0%]    of the answerable rows, answered
             refusal recall  5/18 = 27.8% [12.5%, 50.9%]       of the unanswerable rows, refused
             accuracy        52/65 = 80.0% [68.7%, 87.9%]      of the rows decided
             confusion       answerable: 47 answered, 0 refused | unanswerable: 13 answered, 5 refused
             false answers   13, * an isolation row:
                             rf-02 rf-03 iso-03* iso-05* rf-06 iso-06* iso-07* rf-07 iso-08* iso-09*
                             iso-10* mm-04* mm-05
  generator  not available: --local has no lane: the generator needs one (replay a saved run: --from FILE)
  jev        not available: JEV_MODE=off: Jev not available, nothing sent

  per shape    rows  rule        generator   jev         (right decisions / decided)
  lookup         34  34/34       -           -
  join           11  11/11       -           -
  refusal         8  3/8         -           -
  isolation      11  3/11        -           -
  version         1  1/1         -           -

  kappa against the generator: - (the generator did not run)
  rows where the arms disagree: - (one arm decided)

  calibration (Brier: 0 is perfect; always 0.5 scores 0.25)
    rule (the evidence share, not a probability): Brier 0.182 over 65 rows
      score      rows  mean score  answerable
      0.0-0.2       1        0.18     0/1
      0.2-0.4       3        0.35     0/3
      0.4-0.6       3        0.54     2/3
      0.6-0.8      11        0.69     6/11
      0.8-1.0      47        0.99    39/47
    jev        no scores

  latency per decision, ms      p50       p95   decisions (an empty pool's refusal took none)
    rule (in process)            0.0x      0.0x          60
    generator (/v1/query)           -         -           0
    jev                             -         -           0
  rupees per decision (USD x 85)
    rule       Rs 0 a decision, over 60 (code, no model)
    generator  -
    jev        -
```

**`step_02_change_it_a_higher_floor(session)` — The decision eval for Rs 0, a higher floor, and Jev's switch / Change it: a higher floor**

Raise the floor and the rule buys refusals with answers. The same run at 0.70:

Operation: bash — run in the operator shell, in $DEMO_ROOT (the Change-it: the same Rs 0 run with a higher floor).

Expected shape, not a promised result:

```text
... 10/65 rows
  ... 20/65 rows
  ... 30/65 rows
  ... 40/65 rows
  ... 50/65 rows
  ... 60/65 rows
== answer or refuse: the decision eval (lesson 2.6) ==
  rows       65 golden rows: 47 answerable, 18 not
  pool       the Rs 0 lane, top 5: documind_tools.retrieve(passages=True) on the local profile over the kit's
             corpus (2757 chunks), its gate the evidence rule at 0.70
  rule       an empty pool, or evidence under 0.70 of the question's information, is refused (Rs 0)
  generator  --local has no lane: the generator needs one (replay a saved run: --from FILE)
  jev        JEV_MODE=off: Jev not available, nothing sent

  rule       65 decided (14 by code: an empty pool), 0 errors, 0 skipped
             answer rate     42/47 = 89.4% [77.4%, 95.4%]      of the answerable rows, answered
             refusal recall  9/18 = 50.0% [29.0%, 71.0%]       of the unanswerable rows, refused
             accuracy        51/65 = 78.5% [67.0%, 86.7%]      of the rows decided
             confusion       answerable: 42 answered, 5 refused | unanswerable: 9 answered, 9 refused
             false answers   9, * an isolation row:
                             rf-02 rf-03 iso-03* iso-05* iso-06* rf-07 iso-08* iso-09* mm-05
  generator  not available: --local has no lane: the generator needs one (replay a saved run: --from FILE)
  jev        not available: JEV_MODE=off: Jev not available, nothing sent

  per shape    rows  rule        generator   jev         (right decisions / decided)
  lookup         34  32/34       -           -
  join           11  8/11        -           -
  refusal         8  4/8         -           -
  isolation      11  6/11        -           -
  version         1  1/1         -           -

  kappa against the generator: - (the generator did not run)
  rows where the arms disagree: - (one arm decided)

  calibration (Brier: 0 is perfect; always 0.5 scores 0.25)
    rule (the evidence share, not a probability): Brier 0.182 over 65 rows
      score      rows  mean score  answerable
      0.0-0.2       1        0.18     0/1
      0.2-0.4       3        0.35     0/3
      0.4-0.6       3        0.54     2/3
      0.6-0.8      11        0.69     6/11
      0.8-1.0      47        0.99    39/47
    jev        no scores

  latency per decision, ms      p50       p95   decisions (an empty pool's refusal took none)
    rule (in process)            0.0x      0.0x          51
    generator (/v1/query)           -         -           0
    jev                             -         -           0
  rupees per decision (USD x 85)
    rule       Rs 0 a decision, over 51 (code, no model)
    generator  -
    jev        -
```

**`step_03_jev_s_switch_called_by_hand(session)` — The decision eval for Rs 0, a higher floor, and Jev's switch / Jev's switch, called by hand**

shared/system_one.py is the only door to Jev, and decide() its only entry point. It never raises: every outcome is a result with a verdict of answer, refuse, skipped or error, and only the first two are decisions. The mode is read at call time, and off returns at once. An empty pool is refused in code, as rag-api refuses it, before any mode could ask Jev. Recorded mode reads the recorded file and nothing else. Live mode checks the tenant's data_region first, failing closed to in, then builds the payload from the question and the passages' text with identifiers masked, and only then reaches the adapter seam: _headers(), _request() and _parse(), which PR 2.6-C fills once TypeSafe documents its API. Until then _request() raises before any key is read or any socket opens, and decide() turns that into an error row, which no rate counts as a refusal. Run the Rs 0 eval with JEV_MODE=recorded on zeta's 10 rows, then call decide() in each mode, with the data regions make roster writes standing in for the Firestore read:

Operation: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: Jev's recorded mode, on zeta's ten rows).

Expected shape, not a promised result:

```text
== answer or refuse: the decision eval (lesson 2.6) ==
  rows       10 golden rows: 5 answerable, 5 not
  pool       the Rs 0 lane, top 5: documind_tools.retrieve(passages=True) on the local profile over the kit's
             corpus (1002 chunks), its gate the evidence rule at 0.50
  rule       an empty pool, or evidence under 0.50 of the question's information, is refused (Rs 0)
  generator  --local has no lane: the generator needs one (replay a saved run: --from FILE)
  jev        JEV_MODE=recorded: no recordings: evals/system_one/recorded.jsonl does not exist - none ship until decisions are recorded against TypeSafe's API (PR 2.6-C), and none are written by hand

  rule       10 decided (1 by code: an empty pool), 0 errors, 0 skipped
             answer rate     5/5 = 100.0% [56.6%, 100.0%]      of the answerable rows, answered
             refusal recall  1/5 = 20.0% [3.6%, 62.4%]         of the unanswerable rows, refused
             accuracy        6/10 = 60.0% [31.3%, 83.2%]       of the rows decided
             confusion       answerable: 5 answered, 0 refused | unanswerable: 4 answered, 1 refused
             false answers   4, * an isolation row:
                             iso-05* iso-08* iso-09* mm-04*
  generator  not available: --local has no lane: the generator needs one (replay a saved run: --from FILE)
  jev        not available: no recordings: evals/system_one/recorded.jsonl does not exist - none ship until decisions are recorded against TypeSafe's API (PR 2.6-C), and none are written by hand (1 empty pools refused by code)

  per shape    rows  rule        generator   jev         (right decisions / decided)
  lookup          4  4/4         -           -
  isolation       6  2/6         -           -

  kappa against the generator: - (the generator did not run)
  rows where the arms disagree: - (one arm decided)

  calibration (Brier: 0 is perfect; always 0.5 scores 0.25)
    rule (the evidence share, not a probability): Brier 0.382 over 10 rows
      score      rows  mean score  answerable
      0.0-0.2       0           -     0/0
      0.2-0.4       0           -     0/0
      0.4-0.6       2        0.52     1/2
      0.6-0.8       1        0.61     0/1
      0.8-1.0       7        1.00     4/7
    jev        no scores

  latency per decision, ms      p50       p95   decisions (an empty pool's refusal took none)
    rule (in process)            0.0x      0.0x           9
    generator (/v1/query)           -         -           0
    jev                             -         -           0
  rupees per decision (USD x 85)
    rule       Rs 0 a decision, over 9 (code, no model)
    generator  -
    jev        -
```

**`step_04_jev_s_switch_called_by_hand(session)` — The decision eval for Rs 0, a higher floor, and Jev's switch / Jev's switch, called by hand**

shared/system_one.py is the only door to Jev, and decide() its only entry point. It never raises: every outcome is a result with a verdict of answer, refuse, skipped or error, and only the first two are decisions. The mode is read at call time, and off returns at once. An empty pool is refused in code, as rag-api refuses it, before any mode could ask Jev. Recorded mode reads the recorded file and nothing else. Live mode checks the tenant's data_region first, failing closed to in, then builds the payload from the question and the passages' text with identifiers masked, and only then reaches the adapter seam: _headers(), _request() and _parse(), which PR 2.6-C fills once TypeSafe documents its API. Until then _request() raises before any key is read or any socket opens, and decide() turns that into an error row, which no rate counts as a refusal. Run the Rs 0 eval with JEV_MODE=recorded on zeta's 10 rows, then call decide() in each mode, with the data regions make roster writes standing in for the Firestore read:

Operation: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: no socket opens in any mode).

Expected shape, not a promised result:

```text
off      acme    skipped  source off       JEV_MODE=off: Jev not available, nothing sent
recorded acme    skipped  source recorded  no recordings: evals/system_one/recorded.jsonl does not exist - none ship until decisions are recorded against TypeSafe's API (PR 2.6-C), and none are written by hand
live     globex  skipped  source policy    tenant globex: data_region in - its text stays in India and Jev's region is undocumented: not sent
live     acme    error    source live      the question and 1 passages were ready to send; masked pan | error: TypeSafe adapter not configured (PR 2.6-C)

what live mode would send: ['passages', 'question'] | masked: pan
   PAN: [PAN]
   GSTIN: 27AAAPZ1234C1ZV
   Contact / संपर्क: +919876543210
   Email: accounts@acme-demo.invalid
```

### demo_06_the_rule_and_the_generator_on_your_lane_s_pools.py

Do it: zeta's rows on your lane

**`step_01_zeta_s_rows_on_your_lane(session)` — The rule and the generator on your lane's pools / Do it: zeta's rows on your lane**

Do it: zeta's rows on your lane

Operation: bash — run in the operator shell, in $DEMO_ROOT (zeta's 10 rows: 10 passages calls at Rs 0 and 10 generator calls, about Rs 2.75 of input and at most Rs 15.80 in all).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/decide_learner.txt]
```

### optional/demo_07_against_the_gate_refusal_recall_false_answers_calibration_latency_and_rupees.py

All 65 rows on the author's lane, each arm held against the gate's 0.90, the false answers by id, what refusing first would save and lose, and where Jev could sit after the cohort. The author ran all 65 rows on the author's lane and saved the run. Its report is below. Every figure in this step's tables that is not the Rs 0 lane's is computed from that saved file, when this page is built, by decide.py's own summarise(), calibration(), by_confidence() and latency(). The same command runs on your lane if you want your own.

**`step_01_against_the_gate_refusal_recall_false_answ(session)` — Against the gate: refusal recall, false answers, calibration, latency and rupees / Against the gate: refusal recall, false answers, calibration, latency and rupees**

All 65 rows on the author's lane, each arm held against the gate's 0.90, the false answers by id, what refusing first would save and lose, and where Jev could sit after the cohort. The author ran all 65 rows on the author's lane and saved the run. Its report is below. Every figure in this step's tables that is not the Rs 0 lane's is computed from that saved file, when this page is built, by decide.py's own summarise(), calibration(), by_confidence() and latency(). The same command runs on your lane if you want your own.

Operation: bash — run in the operator shell, in $DEMO_ROOT (optional: all 65 rows, about Rs 17.57 of input and at most Rs 102.43 in all).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/decide_live.txt]
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

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_2.6_System_One_WIX.html`. All 40 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `2c5ffaf4fdf36c282a1fd6ba68ee3e9c5728f9c4`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
