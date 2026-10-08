# Lesson B.2: Turn text into tokens and embeddings

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| 3 | [demo_03_a_tokenizer_you_can_read_byte_pair_merges_on_two_handbook_clauses.py](demo_03_a_tokenizer_you_can_read_byte_pair_merges_on_two_handbook_clauses.py) | A tokenizer you can read: byte-pair merges on two handbook clauses |
| 4 | [demo_04_the_kit_s_two_estimates_against_plain_character_counts.py](demo_04_the_kit_s_two_estimates_against_plain_character_counts.py) | The kit's two estimates against plain character counts |
| 5 | [demo_05_the_rupee_line_tokens_priced_with_the_kit_s_prices.py](demo_05_the_rupee_line_tokens_priced_with_the_kit_s_prices.py) | The rupee line: tokens priced with the kit's prices |
| 6 | [demo_06_the_model_s_own_count_count_tokens_on_gemini_3_6_flash.py](demo_06_the_model_s_own_count_count_tokens_on_gemini_3_6_flash.py) | The model's own count: count_tokens on gemini-3.6-flash |
| 7 | [demo_07_cosine_similarity_in_numpy_on_vectors_you_can_read.py](demo_07_cosine_similarity_in_numpy_on_vectors_you_can_read.py) | Cosine similarity in numpy, on vectors you can read |
| 8 | [demo_08_real_embeddings_text_embedding_005_under_the_kit_s_task_types.py](demo_08_real_embeddings_text_embedding_005_under_the_kit_s_task_types.py) | Real embeddings: text-embedding-005 under the kit's task types |

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

### demo_03_a_tokenizer_you_can_read_byte_pair_merges_on_two_handbook_clauses.py

Do it: learn the merges, then cut five texts

**`step_01_learn_the_merges_then_cut_five_texts(session)` — A tokenizer you can read: byte-pair merges on two handbook clauses / Do it: learn the merges, then cut five texts**

Do it: learn the merges, then cut five texts

Operation: bash — run on your laptop, in ~/basics-venv (a Python cell; Rs 0, nothing leaves the machine).

Expected shape, not a promised result:

```text
training text: 407 characters, 39 distinct; 65 merges learned
the first ten: ['on', 'ti', 'th', 'er', 'ed', ' a', ' s', 'no', 'ce', ' p']
the last five: [' months', ' on', ' probation', 'ith', 'ten']
'What is the notice period for a confirmed E3?'   45 characters -> 23 pieces ['W', 'h', 'a', 't', ' is', ' the', ' notice', ' period', ' f', 'o', 'r', ' a', ' ', 'c', 'on', 'f', 'i', 'r', 'm', 'ed', ' E', '3', '?']
' notice'                                          7 characters ->  1 piece  [' notice']
'notice'                                           6 characters ->  2 pieces ['no', 'tice']
'Notice'                                           6 characters ->  3 pieces ['N', 'o', 'tice']
'Bengaluru'                                        9 characters ->  9 pieces ['B', 'e', 'n', 'g', 'a', 'l', 'u', 'r', 'u']
```

### demo_04_the_kit_s_two_estimates_against_plain_character_counts.py

Do it: four texts, five counts each

**`step_01_four_texts_five_counts_each(session)` — The kit's two estimates against plain character counts / Do it: four texts, five counts each**

Do it: four texts, five counts each

Operation: bash — run on your laptop, in ~/basics-venv (a Python cell; Rs 0, nothing leaves the machine).

Expected shape, not a promised result:

```text
characters  bytes  words  len // 4  len // 3
the question (golden row lk-06)          45     45      9        11        15
the same question in Hindi               48    120     10        12        16
an Indian amount (FIN-02)                62     62     11        15        20
a whole clause (NP-03)                  212    212     38        53        70
```

### demo_05_the_rupee_line_tokens_priced_with_the_kit_s_prices.py

Do it: the golden question's rupee line, Rs 0

**`step_01_the_golden_question_s_rupee_line_rs_0(session)` — The rupee line: tokens priced with the kit's prices / Do it: the golden question's rupee line, Rs 0**

Do it: the golden question's rupee line, Rs 0

Operation: bash — run on your laptop, in ~/basics-venv (a Python cell; Rs 0, arithmetic only).

Expected shape, not a promised result:

```text
'What is the notice period for a confirmed E3?': 45 characters, about 11 tokens by the estimate
as input to gemini-3.6-flash: 11 x $1.50 per 1M = $0.000017 = Rs 0.0014 at 85, 0.14 paise
the same 11 tokens as output: $0.000082 = Rs 0.0070, at 5 times the input rate
a lakh such questions as input: Rs 140.25
```

### demo_06_the_model_s_own_count_count_tokens_on_gemini_3_6_flash.py

Do it: three texts, the model's count, and the rupee line

**`step_01_three_texts_the_model_s_count_and_the_rupe(session)` — The model's own count: count_tokens on gemini-3.6-flash / Do it: three texts, the model's count, and the rupee line**

Do it: three texts, the model's count, and the rupee line

Operation: bash — run on your laptop, in ~/basics-venv, after the setup's Gemini block (a Python cell; three count_tokens calls, no charge).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/count_tokens.txt]
```

### demo_07_cosine_similarity_in_numpy_on_vectors_you_can_read.py

Do it: four cosines, then word counts against meaning

**`step_01_four_cosines_then_word_counts_against_mean(session)` — Cosine similarity in numpy, on vectors you can read / Do it: four cosines, then word counts against meaning**

Do it: four cosines, then word counts against meaning

Operation: bash — run on your laptop, in ~/basics-venv (a Python cell; Rs 0, nothing leaves the machine).

Expected shape, not a promised result:

```text
a [3. 4.]  b [4. 3.]
cosine(a, b)        0.9600
cosine(a, 10 * a)   1.0000   the length does not count, only the direction
cosine(a, [-4, 3])  0.0000   at right angles
cosine(a, -a)      -1.0000   opposite
at length 1 the dot product is the cosine: 0.9600

word-count vectors: 78 dimensions, one per distinct word
lk-05     IT-SEC-04 0.2887  EXP-12 0.0000  PR-05 0.0680   shared with IT-SEC-04: ['are', 'company', 'on', 'usb']
reworded  IT-SEC-04 0.0000  EXP-12 0.0550  PR-05 0.0000   shared with IT-SEC-04: []
```

### demo_08_real_embeddings_text_embedding_005_under_the_kit_s_task_types.py

Do it: five texts, two requests, six cosines

**`step_01_five_texts_two_requests_six_cosines(session)` — Real embeddings: text-embedding-005 under the kit's task types / Do it: five texts, two requests, six cosines**

Do it: five texts, two requests, six cosines

Operation: bash — run on your laptop, in ~/basics-venv, after the setup's Gemini block (a Python cell; two embedding requests, at most Rs 0.0011).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/embeddings.txt]
```

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_B.2_Tokens_Embeddings_WIX.html`. All 28 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `1395591d92dec2c9a56f1342d31a0d356441f8a6`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
