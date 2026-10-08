# Lesson B.3: Read a transformer block, with layer normalization

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| 3 | [demo_03_six_words_eight_numbers_each.py](demo_03_six_words_eight_numbers_each.py) | Six words, eight numbers each |
| 4 | [demo_04_one_head_queries_keys_values_and_the_weights.py](demo_04_one_head_queries_keys_values_and_the_weights.py) | One head: queries, keys, values and the weights |
| 5 | [demo_05_two_heads_joined_and_what_a_head_may_see.py](demo_05_two_heads_joined_and_what_a_head_may_see.py) | Two heads, joined, and what a head may see |
| 6 | [demo_06_the_residual_path_add_the_input_back.py](demo_06_the_residual_path_add_the_input_back.py) | The residual path: add the input back |
| 7 | [demo_07_layer_normalization_mean_0_variance_1_then_a_scale_and_a_shift.py](demo_07_layer_normalization_mean_0_variance_1_then_a_scale_and_a_shift.py) | Layer normalization: mean 0, variance 1, then a scale and a shift |
| 8 | [demo_08_the_block_assembled.py](demo_08_the_block_assembled.py) | The block, assembled |
| 9 | [demo_09_where_the_kit_meets_the_block_tokens_and_their_ceilings.py](demo_09_where_the_kit_meets_the_block_tokens_and_their_ceilings.py) | Where the kit meets the block: tokens and their ceilings |

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

### demo_03_six_words_eight_numbers_each.py

Do it: build X, Rs 0

**`step_01_build_x_rs_0(session)` — Six words, eight numbers each / Do it: build X, Rs 0**

Do it: build X, Rs 0

Operation: bash — run in the same shell, in the basics venv (numpy only, no network).

Expected shape, not a promised result:

```text
tokens: 6 | numbers per token: 8
X = word vector + position vector
              thing   action   amount who/when slow sin slow cos fast sin fast cos
       the     0.00     0.00     0.00     0.00     0.00     1.00     0.00     1.00
  employee     1.00     0.00     0.00     1.00     0.71     0.71     1.00     0.00
    serves     0.00     1.00     0.00     0.00     1.00     0.00     0.00    -1.00
    ninety     0.00     0.00     1.00     0.00     0.71    -0.71    -1.00     0.00
      days     1.00     0.00     0.00    -1.00     0.00    -1.00     0.00     1.00
    notice     1.00     0.00     0.00     0.00    -0.71    -0.71     1.00     0.00
position . position: one position's waves against another's
              pos 0    pos 1    pos 2    pos 3    pos 4    pos 5
     pos 0     2.00     0.71    -1.00    -0.71     0.00    -0.71
     pos 1     0.71     2.00     0.71    -1.00    -0.71     0.00
     pos 2    -1.00     0.71     2.00     0.71    -1.00    -0.71
     pos 3    -0.71    -1.00     0.71     2.00     0.71    -1.00
     pos 4     0.00    -0.71    -1.00     0.71     2.00     0.71
     pos 5    -0.71     0.00    -0.71    -1.00     0.71     2.00
the same along every diagonal, so it measures distance only: True
every position's signal has the same length: 1.41 1.41 1.41 1.41 1.41 1.41
adding the two is the same as setting them side by side: True
```

### demo_04_one_head_queries_keys_values_and_the_weights.py

WQ is the matrix to read. It takes only the four wave columns, turns each wave back by one word's angle (45 degrees for the slow wave, 90 for the fast), and multiplies by 4. So the query of the word at position t is four times the waves of position t − 1. WK leaves each key as the word's own waves. By step 3's table, two positions' waves have their largest dot product when they are the same position, so every query scores highest against the key one word back. WV copies the meaning columns: what head 1 hands each word is, mostly, the meaning of the word before it.

**`step_01_head_1_one_word_back(session)` — One head: queries, keys, values and the weights / Head 1: one word back**

WQ is the matrix to read. It takes only the four wave columns, turns each wave back by one word's angle (45 degrees for the slow wave, 90 for the fast), and multiplies by 4. So the query of the word at position t is four times the waves of position t − 1. WK leaves each key as the word's own waves. By step 3's table, two positions' waves have their largest dot product when they are the same position, so every query scores highest against the key one word back. WV copies the meaning columns: what head 1 hands each word is, mostly, the meaning of the word before it.

Operation: bash — run in the same shell, in the basics venv (numpy only, no network).

Expected shape, not a promised result:

```text
W_Q: both waves turned back one word, times 4 (rows: X's columns)
                 q1       q2       q3       q4
     thing     0.00     0.00     0.00     0.00
    action     0.00     0.00     0.00     0.00
    amount     0.00     0.00     0.00     0.00
  who/when     0.00     0.00     0.00     0.00
  slow sin     2.83     2.83     0.00     0.00
  slow cos    -2.83     2.83     0.00     0.00
  fast sin     0.00     0.00     0.00     4.00
  fast cos     0.00     0.00    -4.00     0.00
Q | K
                 q1       q2       q3       q4       k1       k2       k3       k4
       the    -2.83     2.83    -4.00     0.00     0.00     1.00     0.00     1.00
  employee     0.00     4.00     0.00     4.00     0.71     0.71     1.00     0.00
    serves     2.83     2.83     4.00     0.00     1.00     0.00     0.00    -1.00
    ninety     4.00     0.00     0.00    -4.00     0.71    -0.71    -1.00     0.00
      days     2.83    -2.83    -4.00     0.00     0.00    -1.00     0.00     1.00
    notice     0.00    -4.00     0.00     4.00    -0.71    -0.71     1.00     0.00
scores = Q @ K.T / 2 (rows: the word asking; columns: the word it looks at)
                the employee   serves   ninety     days   notice
       the     1.41    -2.00    -1.41     0.00    -1.41    -2.00
  employee     4.00     1.41    -2.00    -1.41     0.00    -1.41
    serves     1.41     4.00     1.41    -2.00    -1.41     0.00
    ninety    -2.00     1.41     4.00     1.41    -2.00    -1.41
      days    -1.41    -2.00     1.41     4.00     1.41    -2.00
    notice     0.00    -1.41    -2.00     1.41     4.00     1.41
weights = softmax(scores)
                the employee   serves   ninety     days   notice
       the     0.70     0.02     0.04     0.17     0.04     0.02
  employee     0.90     0.07     0.00     0.00     0.02     0.00
    serves     0.06     0.85     0.06     0.00     0.00     0.02
    ninety     0.00     0.06     0.86     0.06     0.00     0.00
      days     0.00     0.00     0.06     0.86     0.06     0.00
    notice     0.02     0.00     0.00     0.06     0.85     0.06
each row sums to: 1.00 1.00 1.00 1.00 1.00 1.00
out = weights @ V: what head 1 hands each word
              thing   action   amount who/when
       the     0.09     0.04     0.17    -0.02
  employee     0.09     0.00     0.00     0.05
    serves     0.87     0.06     0.00     0.85
    ninety     0.07     0.86     0.06     0.06
      days     0.07     0.06     0.86    -0.06
    notice     0.92     0.00     0.06    -0.85
       the looks at the      0.70
  employee looks at the      0.90
    serves looks at employee 0.85
    ninety looks at serves   0.86
      days looks at ninety   0.86
    notice looks at days     0.85
```

### demo_05_two_heads_joined_and_what_a_head_may_see.py

Head 2 reads only the meaning columns, and each of its first three columns is one question and the answer it wants. A thing asks for an action (WQ reads thing, WK reads action). An action asks for a person (who/when at +1). An amount asks for a time (who/when at −1). Its fourth column is left empty. WO adds half of each head's output into the meaning columns and writes nothing into the position columns. An encoder, the BERT-style model of lesson B.4, lets every word attend to every word. A decoder, the GPT-style model of lesson B.5, writes one token after another, so a word must not attend to the words after it: when it is written, they do not exist yet. Before the softmax the decoder sets those scores to minus infinity, which the softmax turns into a share of exactly 0. That is the causal mask. The second half of the cell is the reason for step 3's position columns: reverse the six words, keep the positions where they were, and see which head notices.

**`step_01_head_2_the_word_it_fits_with(session)` — Two heads, joined, and what a head may see / Head 2: the word it fits with**

Head 2 reads only the meaning columns, and each of its first three columns is one question and the answer it wants. A thing asks for an action (WQ reads thing, WK reads action). An action asks for a person (who/when at +1). An amount asks for a time (who/when at −1). Its fourth column is left empty. WO adds half of each head's output into the meaning columns and writes nothing into the position columns.

Operation: bash — run in the same shell, in the basics venv (numpy only, no network).

Expected shape, not a promised result:

```text
W_Q2 | W_K2 (rows: X's columns)
                 q1       q2       q3       q4       k1       k2       k3       k4
     thing     6.00     0.00     0.00     0.00     0.00     0.00     0.00     0.00
    action     0.00     6.00     0.00     0.00     1.00     0.00     0.00     0.00
    amount     0.00     0.00     6.00     0.00     0.00     0.00     0.00     0.00
  who/when     0.00     0.00     0.00     0.00     0.00     1.00    -1.00     0.00
  slow sin     0.00     0.00     0.00     0.00     0.00     0.00     0.00     0.00
  slow cos     0.00     0.00     0.00     0.00     0.00     0.00     0.00     0.00
  fast sin     0.00     0.00     0.00     0.00     0.00     0.00     0.00     0.00
  fast cos     0.00     0.00     0.00     0.00     0.00     0.00     0.00     0.00
head 2's weights
                the employee   serves   ninety     days   notice
       the     0.17     0.17     0.17     0.17     0.17     0.17
  employee     0.04     0.04     0.80     0.04     0.04     0.04
    serves     0.04     0.83     0.04     0.04     0.00     0.04
    ninety     0.04     0.00     0.04     0.04     0.83     0.04
      days     0.04     0.04     0.80     0.04     0.04     0.04
    notice     0.04     0.04     0.80     0.04     0.04     0.04
       the asks nothing, so its attention spreads evenly
  employee looks at serves   0.80
    serves looks at employee 0.83
    ninety looks at days     0.83
      days looks at serves   0.80
    notice looks at serves   0.80
concat = [head 1 | head 2]
            1 thing 1 action 1 amount    1 who  2 thing 2 action 2 amount    2 who
       the     0.09     0.04     0.17    -0.02     0.50     0.17     0.17     0.00
  employee     0.09     0.00     0.00     0.05     0.12     0.80     0.04     0.00
    serves     0.87     0.06     0.00     0.85     0.88     0.04     0.04     0.83
    ninety     0.07     0.86     0.06     0.06     0.88     0.04     0.04    -0.83
      days     0.07     0.06     0.86    -0.06     0.12     0.80     0.04     0.00
    notice     0.92     0.00     0.06    -0.85     0.12     0.80     0.04     0.00
W_O (rows: the concat's columns)
              thing   action   amount who/when slow sin slow cos fast sin fast cos
   1 thing     0.50     0.00     0.00     0.00     0.00     0.00     0.00     0.00
  1 action     0.00     0.50     0.00     0.00     0.00     0.00     0.00     0.00
  1 amount     0.00     0.00     0.50     0.00     0.00     0.00     0.00     0.00
     1 who     0.00     0.00     0.00     0.50     0.00     0.00     0.00     0.00
   2 thing     0.50     0.00     0.00     0.00     0.00     0.00     0.00     0.00
  2 action     0.00     0.50     0.00     0.00     0.00     0.00     0.00     0.00
  2 amount     0.00     0.00     0.50     0.00     0.00     0.00     0.00     0.00
     2 who     0.00     0.00     0.00     0.50     0.00     0.00     0.00     0.00
attention output = concat @ W_O
              thing   action   amount who/when slow sin slow cos fast sin fast cos
       the     0.29     0.10     0.17    -0.01     0.00     0.00     0.00     0.00
  employee     0.10     0.40     0.02     0.03     0.00     0.00     0.00     0.00
    serves     0.87     0.05     0.02     0.84     0.00     0.00     0.00     0.00
    ninety     0.47     0.45     0.05    -0.38     0.00     0.00     0.00     0.00
      days     0.09     0.43     0.45    -0.03     0.00     0.00     0.00     0.00
    notice     0.52     0.40     0.05    -0.42     0.00     0.00     0.00     0.00
```

**`step_02_what_a_head_may_see_the_mask_and_the_order(session)` — Two heads, joined, and what a head may see / What a head may see: the mask, and the order of the words**

An encoder, the BERT-style model of lesson B.4, lets every word attend to every word. A decoder, the GPT-style model of lesson B.5, writes one token after another, so a word must not attend to the words after it: when it is written, they do not exist yet. Before the softmax the decoder sets those scores to minus infinity, which the softmax turns into a share of exactly 0. That is the causal mask. The second half of the cell is the reason for step 3's position columns: reverse the six words, keep the positions where they were, and see which head notices.

Operation: bash — run in the same shell, in the basics venv (numpy only, no network).

Expected shape, not a promised result:

```text
head 1's weights under the causal mask: each word sees itself and the words before it
                the employee   serves   ninety     days   notice
       the     1.00     0.00     0.00     0.00     0.00     0.00
  employee     0.93     0.07     0.00     0.00     0.00     0.00
    serves     0.07     0.87     0.07     0.00     0.00     0.00
    ninety     0.00     0.07     0.87     0.07     0.00     0.00
      days     0.00     0.00     0.07     0.86     0.07     0.00
    notice     0.02     0.00     0.00     0.06     0.85     0.06
head 2's weights under the causal mask
                the employee   serves   ninety     days   notice
       the     1.00     0.00     0.00     0.00     0.00     0.00
  employee     0.50     0.50     0.00     0.00     0.00     0.00
    serves     0.05     0.91     0.05     0.00     0.00     0.00
    ninety     0.33     0.02     0.33     0.33     0.00     0.00
      days     0.04     0.04     0.83     0.04     0.04     0.00
    notice     0.04     0.04     0.80     0.04     0.04     0.04
reversed: notice days ninety serves employee the
head 2 hands every word the same numbers as before: True
head 1 hands every word the same numbers as before: False
one word back from serves is now: ninety
```

### demo_06_the_residual_path_add_the_input_back.py

The cell adds the attention output to X, compares each word's new vector with its old one by cosine (1 is the same direction, 0 unrelated), then applies the attention sub-layer four times over, once without the residual path and once with it.

**`step_01_add_then_stack_four_times_with_and_without(session)` — The residual path: add the input back / Do it: add, then stack four times with and without it**

The cell adds the attention output to X, compares each word's new vector with its old one by cosine (1 is the same direction, 0 unrelated), then applies the attention sub-layer four times over, once without the residual path and once with it.

Operation: bash — run in the same shell, in the basics venv (numpy only, no network).

Expected shape, not a promised result:

```text
H = X + attention output
              thing   action   amount who/when slow sin slow cos fast sin fast cos
       the     0.29     0.10     0.17    -0.01     0.00     1.00     0.00     1.00
  employee     1.10     0.40     0.02     1.03     0.71     0.71     1.00     0.00
    serves     0.87     1.05     0.02     0.84     1.00     0.00     0.00    -1.00
    ninety     0.47     0.45     1.05    -0.38     0.71    -0.71    -1.00     0.00
      days     1.09     0.43     0.45    -1.03     0.00    -1.00     0.00     1.00
    notice     1.52     0.40     0.05    -0.42    -0.71    -0.71     1.00     0.00
            cos(X, attention output)  cos(X, H)
       the                      0.00       0.97
  employee                      0.16       0.98
    serves                      0.03       0.82
    ninety                      0.04       0.92
      days                      0.10       0.96
    notice                      0.38       0.94
layer 1: without the residual path the farthest two words are 1.36 apart; with it the closest two are 1.76
layer 2: without the residual path the farthest two words are 0.18 apart; with it the closest two are 1.81
layer 3: without the residual path the farthest two words are 0.00 apart; with it the closest two are 1.98
layer 4: without the residual path the farthest two words are 0.00 apart; with it the closest two are 2.07
```

### demo_07_layer_normalization_mean_0_variance_1_then_a_scale_and_a_shift.py

Do it: normalize H, Rs 0

**`step_01_normalize_h_rs_0(session)` — Layer normalization: mean 0, variance 1, then a scale and a shift / Do it: normalize H, Rs 0**

Do it: normalize H, Rs 0

Operation: bash — run in the same shell, in the basics venv (numpy only, no network).

Expected shape, not a promised result:

```text
each word's mean and variance, before and after
               mean  variance  ->       mean   variance
       the   0.3196    0.1635  ->   0.000000   0.999939
  employee   0.6210    0.1686  ->   0.000000   0.999941
    serves   0.3482    0.4504  ->   0.000000   0.999978
    ninety   0.0743    0.4550  ->   0.000000   0.999978
      days   0.1183    0.5675  ->   0.000000   0.999982
    notice   0.1418    0.5611  ->   0.000000   0.999982
H_hat = (H - mean) / sqrt(variance + eps)
              thing   action   amount who/when slow sin slow cos fast sin fast cos
       the    -0.06    -0.53    -0.37    -0.81    -0.79     1.68    -0.79     1.68
  employee     1.18    -0.53    -1.46     0.99     0.21     0.21     0.92    -1.51
    serves     0.78     1.05    -0.49     0.73     0.97    -0.52    -0.52    -2.01
    ninety     0.59     0.56     1.45    -0.68     0.94    -1.16    -1.59    -0.11
      days     1.30     0.42     0.44    -1.53    -0.16    -1.48    -0.16     1.17
    notice     1.84     0.35    -0.12    -0.75    -1.13    -1.13     1.15    -0.19
every word's length is now the square root of 8: 2.83 2.83 2.83 2.83 2.83 2.83
gamma * H_hat + beta: the meaning columns turned up, the position columns down
              thing   action   amount who/when slow sin slow cos fast sin fast cos
       the     0.10    -0.60    -0.36    -1.02    -0.40     0.84    -0.40     0.84
  employee     1.97    -0.60    -1.99     1.68     0.10     0.10     0.46    -0.76
    serves     1.37     1.77    -0.53     1.30     0.49    -0.26    -0.26    -1.00
    ninety     1.09     1.04     2.38    -0.82     0.47    -0.58    -0.80    -0.06
      days     2.14     0.83     0.86    -2.09    -0.08    -0.74    -0.08     0.59
    notice     2.96     0.72     0.02    -0.93    -0.57    -0.57     0.57    -0.09
a word ten times as loud comes out the same: True
changing one word moves no other word: True
RMSNorm per word, mean:             0.620  0.834  0.461  0.110  0.155  0.186
RMSNorm per word, mean of squares:  1.000  1.000  1.000  1.000  1.000  1.000
```

### demo_08_the_block_assembled.py

Do it: one block, both orders, Rs 0

**`step_01_one_block_both_orders_rs_0(session)` — The block, assembled / Do it: one block, both orders, Rs 0**

Do it: one block, both orders, Rs 0

Operation: bash — run in the same shell, in the basics venv (numpy only, no network).

Expected shape, not a promised result:

```text
Y = block(X)
              thing   action   amount who/when slow sin slow cos fast sin fast cos
       the    -0.12    -0.43    -0.44    -0.67    -0.85     1.68    -0.87     1.69
  employee     1.20    -0.57    -1.39     0.92     0.27     0.15     0.97    -1.55
    serves     0.77     1.08    -0.53     0.77     0.93    -0.48    -0.59    -1.98
    ninety     0.61     0.52     1.47    -0.70     0.96    -1.18    -1.55    -0.13
      days     1.21     0.55     0.24    -1.34    -0.46    -1.22    -0.52     1.54
    notice     1.84     0.53    -0.41    -0.52    -1.62    -0.82     0.74     0.27
in (6, 8) -> out (6, 8) -> a second block reads Y and returns (6, 8)
per word, mean:      0.000  0.000  0.000  0.000  0.000  0.000
per word, variance:  1.000  1.000  1.000  1.000  1.000  1.000
norm first, mean:      0.079  0.507  0.071  0.052  0.174  0.153
norm first, variance:  0.371  0.180  0.679  0.538  0.595  0.625
numbers a trained block learns: 840 {'attention': 256, 'feed-forward': 552, 'layer norms': 32}
```

### demo_09_where_the_kit_meets_the_block_tokens_and_their_ceilings.py

The cell copies those constants, the toy sentence's six tokens beside them, and puts each through the square, then fills one embedding request the way batches() does.

**`step_01_the_kit_s_numbers_squared_rs_0(session)` — Where the kit meets the block: tokens and their ceilings / Do it: the kit's numbers, squared, Rs 0**

The cell copies those constants, the toy sentence's six tokens beside them, and puts each through the square, then fills one embedding request the way batches() does.

Operation: bash — run in the same shell (plain Python, no network).

Expected shape, not a promised result:

```text
one sequence: its tokens, and the scores one head computes in one layer of a block like this page's
  the toy sentence                    6 tokens           36 scores
  one chunk of 2,000 characters     666 tokens      443,556 scores
  the API's prompt budget         8,000 tokens   64,000,000 scores
one embedding request of full chunks: 22 texts, 14,652 estimated tokens
  each text its own sequence: 22 x 443,556 = 9,758,232 scores
  the same tokens as one sequence: 214,681,104 scores, 22 times as many
```

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_B.3_Transformer_Block_WIX.html`. All 26 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `8a7a005243dfd1f5be3db61c27dc263c3c01451f`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
