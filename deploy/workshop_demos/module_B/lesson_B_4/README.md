# Lesson B.4: Encode with BERT-style models: embeddings and rankers

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| 3 | [demo_03_the_masked_language_idea_fill_the_blank_from_both_sides.py](demo_03_the_masked_language_idea_fill_the_blank_from_both_sides.py) | The masked-language idea: fill the blank from both sides |
| 4 | [demo_04_a_bi_encoder_two_texts_encoded_apart_compared_by_cosine.py](demo_04_a_bi_encoder_two_texts_encoded_apart_compared_by_cosine.py) | A bi-encoder: two texts, encoded apart, compared by cosine |
| 5 | [demo_05_a_cross_encoder_one_pair_read_together_scored_once.py](demo_05_a_cross_encoder_one_pair_read_together_scored_once.py) | A cross-encoder: one pair, read together, scored once |
| 7 | [demo_07_one_question_four_clauses_scored_both_ways_on_your_project.py](demo_07_one_question_four_clauses_scored_both_ways_on_your_project.py) | One question, four clauses, scored both ways on your project |

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

### demo_03_the_masked_language_idea_fill_the_blank_from_both_sides.py

Do it: hide three words and ask the text for them, Rs 0

**`step_01_hide_three_words_and_ask_the_text_for_them(session)` — The masked-language idea: fill the blank from both sides / Do it: hide three words and ask the text for them, Rs 0**

Do it: hide three words and ask the text for them, Rs 0

Operation: bash — run in your venv (a Python cell; no network, Rs 0).

Expected shape, not a promised result:

```text
the text: 4 clauses, 11 sentences, 128 words

NP-03, sentence 1: a confirmed employee at grade e3 or above serves a [MASK] period of 60 days
  left only   (a _): confirmed 1, maximum 1  -> a tie: confirmed, maximum; the hidden word is not among them
  both sides  (a _ period): notice 2, confirmed 1, maximum 1  -> notice, the hidden word

PB-02, sentence 2: during probation the notice period is [MASK] days for either side
  left only   (is _): acknowledged 1, encashed 1  -> a tie: acknowledged, encashed; the hidden word is not among them
  both sides  (is _ days): acknowledged 1, encashed 1, 60 1, 1.75 1, 30 1, 45 1  -> a tie: acknowledged, encashed, 60, 1.75, 30, 45; the hidden word is not among them

NP-03, sentence 3: unused earned [MASK] may not be set off against the notice period
  left only   (earned _): leave 2  -> leave, the hidden word
  both sides  (earned _ may): leave 2, probation 1, days 1  -> leave, the hidden word
```

### demo_04_a_bi_encoder_two_texts_encoded_apart_compared_by_cosine.py

Do it: a five-axis bi-encoder on the four clauses, Rs 0

**`step_01_a_five_axis_bi_encoder_on_the_four_clauses(session)` — A bi-encoder: two texts, encoded apart, compared by cosine / Do it: a five-axis bi-encoder on the four clauses, Rs 0**

Do it: a five-axis bi-encoder on the four clauses, Rs 0

Operation: bash — run in your venv (a Python cell; no network, Rs 0).

Expected shape, not a promised result:

```text
the toy: 23 words on 5 axes; the store: 4 clause vectors of 5 numbers
  NP-03  [leave 0.416, exit 0.885, pay 0.000, probation 0.000, reduce 0.208]
  PB-02  [leave 0.000, exit 0.356, pay 0.000, probation 0.934, reduce 0.000]
  LV-01  [leave 1.000, exit 0.000, pay 0.000, probation 0.000, reduce 0.000]
  LV-07  [leave 0.552, exit 0.375, pay 0.690, probation 0.197, reduce 0.197]
the question: Can I use my unused leave to shorten my notice period?
  words it knows: unused, leave, shorten, notice, period
  its vector: [leave 0.647, exit 0.647, pay 0.000, probation 0.000, reduce 0.404]
the cosine with each stored vector, highest first (for vectors of length 1 the dot product is the cosine):
  NP-03  0.926
  LV-07  0.679
  LV-01  0.647
  PB-02  0.230
the same question in other words: Will my holidays cut my notice short?
  NP-03 0.876   LV-07 0.638   LV-01 0.537   PB-02 0.212
```

### demo_05_a_cross_encoder_one_pair_read_together_scored_once.py

Do it: the same pairs, read together, Rs 0

**`step_01_the_same_pairs_read_together_rs_0(session)` — A cross-encoder: one pair, read together, scored once / Do it: the same pairs, read together, Rs 0**

Do it: the same pairs, read together, Rs 0

Operation: bash — run in your venv (a Python cell; no network, Rs 0).

Expected shape, not a promised result:

```text
the question's ideas, in order: leave > reduce > exit
clause    bi-encoder  cross-encoder
NP-03          0.926           1.00
        lined up best: Unused earned leave may not be set off against the notice period.
LV-07          0.679           1.00
        lined up best: Leave cannot be encashed during probation and cannot be used to shorten notice.
LV-01          0.647           0.33
        lined up best: Earned leave accrues at 1.75 days per completed month.
PB-02          0.230           0.33
        lined up best: During probation the notice period is 15 days for either side.
the same words, swapped:
  Leave cannot be used to shorten notice.    0.980           1.00
  Notice cannot be used to shorten leave.    0.980           0.33
the two vectors are identical: True
```

### demo_07_one_question_four_clauses_scored_both_ways_on_your_project.py

The embedding cell uses Vertex AI, which the setup switched on. The Ranking API is served by Discovery Engine, a separate API: switch it on once for your project. Enabling it costs nothing; the ranker bills per request. The cell is the kit's two embedding calls in miniature. It embeds the four clauses in one request under RETRIEVAL_DOCUMENT, as the worker embeds a document's chunks, and the question under RETRIEVAL_QUERY, as the API embeds a question, with the kit's model, its 768 numbers and its region. Then it scales every vector to length 1 and takes the dot products: four cosines. It saves them to ~/b4_bi.json for the comparison. The two requests carry 773 characters between them, about 0.16 paise. The kit calls the ranker through Google's Discovery Engine client library. Your Basics venv has only numpy and google-genai, and REST needs nothing more than libraries google-genai installed with it: google-auth, which turns your Application Default Credentials into an access token (through requests, another of them), and httpx, for the call itself. The path is the kit's ranking config, and the body is the kit's request (the model, the question, one record per clause with its text, and top_n) plus one flag that asks for ids and scores without the texts echoed back. The X-Goog-User-Project header is in Google's own example: with a person's sign-in rather than a service account, it names the project the call is billed to and counted against. Four records are one query, at USD 1 per 1,000 queries of up to 100 records each: Rs 0.085. The proof of the lesson: the same four pairs, scored both ways. The cell reads the two files, ranks the clauses by each score, and prints three things: each scorer's first choice, how many of the six pairs of clauses the two put in the same order, and how far each score spreads from its highest to its lowest.

**`step_01_one_more_api(session)` — One question, four clauses, scored both ways on your project / One more API**

The embedding cell uses Vertex AI, which the setup switched on. The Ranking API is served by Discovery Engine, a separate API: switch it on once for your project. Enabling it costs nothing; the ranker bills per request.

Operation: bash — run once, in the shell where PROJECT is set (after lesson 0.1).

Expected shape, not a promised result:

```text
discoveryengine.googleapis.com is on for documind-ai-YOUR-ID
```

**`step_02_the_bi_encoder_side_text_embedding_005_a_f(session)` — One question, four clauses, scored both ways on your project / The bi-encoder side: text-embedding-005, a fraction of a paisa**

The cell is the kit's two embedding calls in miniature. It embeds the four clauses in one request under RETRIEVAL_DOCUMENT, as the worker embeds a document's chunks, and the question under RETRIEVAL_QUERY, as the API embeds a question, with the kit's model, its 768 numbers and its region. Then it scales every vector to length 1 and takes the dot products: four cosines. It saves them to ~/b4_bi.json for the comparison. The two requests carry 773 characters between them, about 0.16 paise.

Operation: bash — run in your venv, PROJECT set (a Python cell; two paid embedding requests).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/bi_encoder.txt]
```

**`step_03_the_cross_encoder_side_the_ranking_api_ove(session)` — One question, four clauses, scored both ways on your project / The cross-encoder side: the Ranking API over REST, 8.5 paise**

The kit calls the ranker through Google's Discovery Engine client library. Your Basics venv has only numpy and google-genai, and REST needs nothing more than libraries google-genai installed with it: google-auth, which turns your Application Default Credentials into an access token (through requests, another of them), and httpx, for the call itself. The path is the kit's ranking config, and the body is the kit's request (the model, the question, one record per clause with its text, and top_n) plus one flag that asks for ids and scores without the texts echoed back. The X-Goog-User-Project header is in Google's own example: with a person's sign-in rather than a service account, it names the project the call is billed to and counted against. Four records are one query, at USD 1 per 1,000 queries of up to 100 records each: Rs 0.085.

Operation: bash — run in your venv, PROJECT set (a Python cell; one paid rank request).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/cross_encoder.txt]
```

**`step_04_side_by_side_rs_0(session)` — One question, four clauses, scored both ways on your project / Side by side, Rs 0**

The proof of the lesson: the same four pairs, scored both ways. The cell reads the two files, ranks the clauses by each score, and prints three things: each scorer's first choice, how many of the six pairs of clauses the two put in the same order, and how far each score spreads from its highest to its lowest.

Operation: bash — run in your venv after the two cells above (a Python cell; no network, Rs 0).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/compare.txt]
```

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_B.4_Encoder_Models_WIX.html`. All 26 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `c5e0d3ccaccb4143687b69cae20a2d562c329369`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
