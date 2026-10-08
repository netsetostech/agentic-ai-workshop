# Lesson B.5: Generate with GPT-style models: decoding and run-to-run variance

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| 3 | [demo_03_from_scores_to_one_token_greedy_and_sampling.py](demo_03_from_scores_to_one_token_greedy_and_sampling.py) | From scores to one token: greedy and sampling |
| 4 | [demo_04_reshape_the_odds_temperature_top_k_and_top_p.py](demo_04_reshape_the_odds_temperature_top_k_and_top_p.py) | Reshape the odds: temperature, top-k and top-p |
| 5 | [demo_05_the_loop_and_five_runs_of_one_prompt_counted.py](demo_05_the_loop_and_five_runs_of_one_prompt_counted.py) | The loop, and five runs of one prompt counted |
| 7 | [demo_07_gemini_five_times_count_the_distinct_answers.py](demo_07_gemini_five_times_count_the_distinct_answers.py) | Gemini, five times: count the distinct answers |
| 8 | [demo_08_two_thinking_levels_thought_tokens_and_rupees.py](demo_08_two_thinking_levels_thought_tokens_and_rupees.py) | Two thinking levels: thought tokens and rupees |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### demo_03_from_scores_to_one_token_greedy_and_sampling.py

Do it: one turn of the loop, Rs 0

**`step_01_one_turn_of_the_loop_rs_0(session)` — From scores to one token: greedy and sampling / Do it: one turn of the loop, Rs 0**

Do it: one turn of the loop, Rs 0

Operation: bash — run on your laptop, in the Basics venv (numpy only, no network).

Expected shape, not a promised result:

```text
60  logit +4.0  probability 0.750
 sixty  logit +2.6  probability 0.185
    15  logit +0.6  probability 0.025
    90  logit +0.2  probability 0.017
    45  logit -0.2  probability 0.011
    30  logit -0.6  probability 0.008
ninety  logit -1.0  probability 0.005
total 1.000 | 60 or sixty 0.934, another figure 0.066 | greedy picks '60'
seed 1, ten draws: 60 60 60 60 60 sixty 90 60 60 60
seed 2, ten draws: 60 60 60 60 60 60 60 60 60 60
seed 1, ten draws: 60 60 60 60 60 sixty 90 60 60 60
seed 7, 10,000 draws: 60 0.747, sixty 0.190, 15 0.024, 90 0.015, 45 0.011, 30 0.007, ninety 0.006
```

### demo_04_reshape_the_odds_temperature_top_k_and_top_p.py

Do it: eight settings on one turn, Rs 0

**`step_01_eight_settings_on_one_turn_rs_0(session)` — Reshape the odds: temperature, top-k and top-p / Do it: eight settings on one turn, Rs 0**

Do it: eight settings on one turn, Rs 0

Operation: bash — run on your laptop, in the Basics venv (numpy only, no network).

Expected shape, not a promised result:

```text
setting             P(60) P(sixty) P(another figure) left
T=0 (greedy)        1.000    0.000             0.000    1
T=0.5               0.941    0.057             0.002    7
T=1.0               0.750    0.185             0.066    7
T=1.5               0.582    0.229             0.190    7
T=2.0               0.469    0.233             0.299    7
T=1.0, top-k 2      0.802    0.198             0.000    2
T=1.0, top-p 0.90   0.802    0.198             0.000    2
T=1.0, top-p 0.95   0.781    0.193             0.026    3
```

### demo_05_the_loop_and_five_runs_of_one_prompt_counted.py

Do it: thirty runs and one cut short, Rs 0

**`step_01_thirty_runs_and_one_cut_short_rs_0(session)` — The loop, and five runs of one prompt counted / Do it: thirty runs and one cut short, Rs 0**

Do it: thirty runs and one cut short, Rs 0

Operation: bash — run on your laptop, in the Basics venv (numpy only, no network).

Expected shape, not a promised result:

```text
greedy (T=0)    distinct 1 of 5, another figure in 0 of 5
                60 days . | 60 days . | 60 days . | 60 days . | 60 days .
T=0.5           distinct 2 of 5, another figure in 0 of 5
                60 days . | 60 days . | 60 days . | 60 days . | 60 days from acknowledgement .
T=1.0           distinct 3 of 5, another figure in 0 of 5
                60 days . | 60 days . | sixty days . | 60 days . | 60 days from acknowledgement .
T=1.5           distinct 4 of 5, another figure in 1 of 5
                sixty days . | sixty days . | 45 days . | 60 days . | 60 calendar days .
T=2.0           distinct 5 of 5, another figure in 2 of 5
                sixty days from acknowledgement . | 15 days . | 30 days . | 60 days . | 60 calendar days .
T=2.0, top-k 2  distinct 4 of 5, another figure in 0 of 5
                60 days from acknowledgement . | sixty days . | sixty days . | 60 days . | 60 calendar days .
greedy, capped at 2 tokens: ('60 days', 'MAX_TOKENS')
```

### demo_07_gemini_five_times_count_the_distinct_answers.py

This is the lesson's proof, on the real model. The prompt is the one generate() builds when retrieval hands it a single clause: the rules from step 6, the handbook's clause NP-03 as [Source 1], and the question of golden row lk-06, whose check is that the answer states 60. The config is _call()'s, setting for setting. The cell asks five times, prints each answer, and counts two things: distinct answers (the exact text, with runs of spaces collapsed), and answers that state 60 by the boundary rule run_eval.py uses, where the figure must stand on its own, so "160" does not count (unlike run_eval.py, the cell does not read "sixty" as 60). The prompt is about 195 tokens by the kit's own estimate (four characters a token); the cell prints what the five calls cost, and they cannot cost more than Rs 6.53 in output even if every call ran to the cap. This cell and the one in step 8 call Gemini on your own Google Cloud project, so they need lesson 0.1's project and the setup's second block (the sign-in and PROJECT). If you have not made the project yet, read the author's recorded output below, go on to lesson 0.1, and come back: the cells will wait.

**`step_01_definition(session)` — Gemini, five times: count the distinct answers / Definition**

This is the lesson's proof, on the real model. The prompt is the one generate() builds when retrieval hands it a single clause: the rules from step 6, the handbook's clause NP-03 as [Source 1], and the question of golden row lk-06, whose check is that the answer states 60. The config is _call()'s, setting for setting. The cell asks five times, prints each answer, and counts two things: distinct answers (the exact text, with runs of spaces collapsed), and answers that state 60 by the boundary rule run_eval.py uses, where the figure must stand on its own, so "160" does not count (unlike run_eval.py, the cell does not read "sixty" as 60). The prompt is about 195 tokens by the kit's own estimate (four characters a token); the cell prints what the five calls cost, and they cannot cost more than Rs 6.53 in output even if every call ran to the cap. This cell and the one in step 8 call Gemini on your own Google Cloud project, so they need lesson 0.1's project and the setup's second block (the sign-in and PROJECT). If you have not made the project yet, read the author's recorded output below, go on to lesson 0.1, and come back: the cells will wait.

Operation: bash — run on your laptop after lesson 0.1, in the Basics venv (five calls to gemini-3.6-flash, at most Rs 6.53 in output).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/five_runs.txt]
```

### demo_08_two_thinking_levels_thought_tokens_and_rupees.py

Golden row jn-01 joins two clauses: probation's notice (PB-02) and leave on exit (LV-07), and its check is that the answer says 15 days and that leave cannot be encashed. The prompt is again generate()'s, with both clauses packed, about 252 tokens by the kit's estimate. The cell sends it at LOW, the kit's level, and at HIGH, and gives both the 6,144-token room that generate() gives its one retry, so that a long think at HIGH is not cut off. For each level it prints the thought tokens, the answer tokens, the prompt tokens, the finish reason, the cost at the kit's prices and the answer. Two calls: at most Rs 7.83 in output, even if both ran to the cap.

**`step_01_definition(session)` — Two thinking levels: thought tokens and rupees / Definition**

Golden row jn-01 joins two clauses: probation's notice (PB-02) and leave on exit (LV-07), and its check is that the answer says 15 days and that leave cannot be encashed. The prompt is again generate()'s, with both clauses packed, about 252 tokens by the kit's estimate. The cell sends it at LOW, the kit's level, and at HIGH, and gives both the 6,144-token room that generate() gives its one retry, so that a long think at HIGH is not cut off. For each level it prints the thought tokens, the answer tokens, the prompt tokens, the finish reason, the cost at the kit's prices and the answer. Two calls: at most Rs 7.83 in output, even if both ran to the cap.

Operation: bash — run on your laptop after lesson 0.1, in the Basics venv (two calls to gemini-3.6-flash, at most Rs 7.83 in output).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/thinking_levels.txt]
```

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_B.5_Decoder_Models_WIX.html`. All 26 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `456244a622c02be64d37a8550d556e129277b6ae`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
