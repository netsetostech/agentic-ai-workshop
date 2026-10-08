# Lesson B.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_B.5_Decoder_Models_WIX.html`, reviewed at blob `456244a622c02be64d37a8550d556e129277b6ae`. Learners read that page on the course site; this guide keeps its prose.

Every answer DocuMind gives is written one token at a time: the model scores every candidate for the next token, one is picked, and the loop runs again. This page opens that loop. You will build it in numpy on a tiny vocabulary, watch greedy decoding repeat itself while sampling varies, see temperature, top-k and top-p reshape the odds, and read why the kit sends Gemini none of the three. Then you will send Gemini one question five times with the kit's own settings, count the distinct answers, and price its thinking at two levels in rupees.

- What a decoder does: one token at a time

- The words: logit, softmax, greedy, sampling, temperature, thinking

- Before you run anything: set up your laptop

- From scores to one token: greedy and sampling

- Reshape the odds: temperature, top-k and top-p

- The loop, and five runs of one prompt counted

- What the kit sends Gemini, and why no temperature

- Gemini, five times: count the distinct answers

- Two thinking levels: thought tokens and rupees

- Verify it yourself: the checklist

You will learn how a GPT-style model writes (one token at a time, each picked from a probability distribution) and why picking by chance makes one prompt give different answers. Then you will run the loop yourself in numpy, read what the kit sends Gemini instead of a temperature, and measure the real thing: one prompt asked five times, and one prompt at two thinking levels.

### What a decoder does: one token at a time

The loop every GPT-style model runs to write, where its randomness comes from, and the two things Gemini 3 changes.

A decoder writes by predicting the next token. Give a GPT-style model some text and it returns one number for every token in its vocabulary: a score, called a logit, for how well that token would continue the text. Softmax turns the scores into probabilities that add up to 1. Then one token is picked, appended to the text, and the model runs again on the longer text. An answer of a few hundred tokens is a few hundred turns of that loop, and each token is chosen knowing everything before it and nothing after it.

What makes it a decoder. Inside, it is the transformer block of lesson B.3, stacked, with one restriction: a position may attend only to itself and to the positions before it (the causal mask). Trained on that view to predict each next token, the model can be run forward to write. The encoders of lesson B.4 attend in both directions at once, which is what makes their embeddings and rankers good at reading, and why they are not the models that write.

Where run-to-run variance comes from. In principle the scores for a given text are arithmetic on fixed weights: the same text, the same scores. The randomness enters at the pick. Greedy decoding takes the likeliest token every time, so one prompt gives one answer however often you ask. Sampling draws a token at random in proportion to its probability, so the same prompt can give a different answer on every run. Three knobs reshape the probabilities before the draw: temperature sharpens or flattens them, top-k keeps only the k likeliest tokens, and top-p keeps only the likeliest tokens that together reach probability p.

The suggestion strip on your phone's keyboard. Type "running late, will reach by" and the strip offers three next words. Tap the likeliest one every time and the same start always ends in the same message: that is greedy decoding. Tap by chance, the likelier words more often, and two people who start from the same words send different messages: that is sampling, and it is where run-to-run variance comes from. The strip showing only three words is top-k. Temperature is how adventurous the tapping is. A Gemini 3 model also drafts in its head before it types, which is its thinking, and you pay for the draft even though nobody reads it.

The left column is every decoder; the right column is what DocuMind's API does at each step, read from `services/rag-api/generator.py` and `config.py` in step 6. Steps 3 to 5 of this page build the left column in numpy; steps 7 and 8 measure the right one on Gemini.

#### Try the knobs on a toy

The explorer below runs the loop on a toy model that writes from a vocabulary of 13 tokens: the same toy the cells in steps 3 to 5 run. The prompt is "A confirmed E3 employee serves a notice period of", and the toy's seven candidates for the next token are figures: 60, which is what the handbook's clause NP-03 says; sixty, the same figure in words; and five figures the clause does not say. Move the knobs and watch two things: the odds of the next token, and five whole answers written with the same five seeds.

Each bar is one candidate's probability after the knobs; a red bar is a figure the clause does not say. Temperature 0 is greedy. The five answers are the whole loop, run to the end token with the same five seeds, so when you move a knob only the knob changes. The script is the cells' own functions, checked against them on 603 runs when the page was built. On gemini-3.6-flash none of the three knobs is yours to turn: step 6 shows what Google's pages say and what the kit sends instead.

It is a toy, not a language model. Its logits are written by hand, it remembers only the last token it wrote, and it scores a handful of candidates where a real model scores every token in its vocabulary at every step. What it shares with a real decoder is the mechanism: the logits, the softmax, the knobs, the pick and the loop, which are the functions you will run in steps 3 to 5.

#### What Gemini 3 changes

Two things, and both shape what this page measures. First, a Gemini 3 model thinks before it answers: it writes thought tokens with the same loop, the kit never asks to see them, and they are billed as output. How much it thinks is a setting, `thinking_level`. Second, on `gemini-3.6-flash`, the model the kit calls, the three knobs above are not yours: Google's model page says custom values for temperature, top-k and top-p are ignored. So for the kit, run-to-run variance is a property of the model that you measure, not a knob that you turn, and the kit steers the two things it can: how much the model thinks, and the shape of the answer.

### The words: logit, softmax, greedy, sampling, temperature, thinking

Twelve words, each with what it means in the kit.

Two of these words are settings the kit sends (the thinking level and the cap), two are settings it deliberately leaves out (temperature, and top-k with top-p), and the rest are mechanism. The toy shows you the mechanism first, because once you have seen a loop pick its tokens, five different answers from one prompt stop being a mystery and become a measurement.

### Before you run anything: set up your laptop

Every cell on this page runs on your own laptop, in a bash shell: the Terminal on macOS or Linux, WSL or Git Bash on Windows, or Cloud Shell in a browser. The Python is 3.12, the version the kit's services run in their images (`python:3.12-slim`), inside a virtual environment of its own, `~/basics-venv`, so nothing is installed into the Python your system uses. Most cells need no account and no network. The cells that call Gemini need the Google Cloud project you create in lesson 0.1 and Application Default Credentials, and their labels say so.

Set up the venv once. The block below finds a Python 3.12 or newer, makes the venv the first time and activates it every time after. Then it installs the two libraries the Basics pages use, at fixed versions: numpy for the arithmetic, and google-genai, at the version the kit pins, for the calls to Gemini. The last line proves both import.

The cells that call Gemini need two more things: your project from lesson 0.1, and Application Default Credentials, the sign-in Google's client libraries read. Run the block below once, after lesson 0.1, in the same shell; the browser opens for the sign-in. It uses the gcloud CLI, which lesson 0.2 installs on a laptop and Cloud Shell already has. As in the kit, Gemini 3 models are called on the `global` location and the embedding model on `us-central1`.

Steps 3, 4 and 5 run on numpy alone, with no network and no account: Rs 0, and they print exactly what this page prints, because their random draws come from a seeded generator written out in the cell. Steps 7 and 8 call Gemini on the project you make in lesson 0.1, and each of their labels gives its ceiling in rupees.

### From scores to one token: greedy and sampling

Seven logits, the softmax that turns them into probabilities, and the two ways to pick: always the top one, or a seeded draw.

#### Definition

One turn of the loop, on the toy's seven candidates after "...serves a notice period of". The logits are the model's output. Softmax subtracts the largest logit first, so that no exponential overflows (the result is the same), then exponentiates and divides by the total. Greedy decoding reads off the largest probability and stops there. Sampling needs a random number: a draw u between 0 and 1, and the pick is the first candidate whose running total of probabilities passes u, so a candidate with probability 0.75 owns three quarters of the line from 0 to 1. The draws come from a tiny generator in the cell: give it the same seed and it gives the same draws, on any machine.

#### Do it: one turn of the loop, Rs 0

The seven logits became seven probabilities that add up to 1.000, still in the logits' order. 60 takes 0.750, sixty 0.185, and the five figures the clause does not say share 0.066 between them. Greedy picked 60, and would pick it on every run. The seeded draws picked 60 most of the time and something else now and then, and seed 1 printed the same ten picks both times, because a seed fixes the draws. Over 10,000 draws every candidate came out within 0.005 of its probability. That is sampling in one sentence: faithful to the distribution on average, unpredictable one draw at a time, and the second half is run-to-run variance.

60 and sixty are one figure in two spellings, which is why the cell counts them together. The kit's evaluator, `evals/run_eval.py`, turns number words into digits before it checks an answer for exactly this reason. The other five are not random either: 15, 45 and 90 all appear elsewhere in acme's documents (probation's notice, the cap on encashed leave, the contract's notice), which is the kind of mix-up a real model can make when it has read all of them.

### Reshape the odds: temperature, top-k and top-p

Three knobs that change the probabilities before the pick, and what each one does to the figures the clause does not say.

#### Definition

Temperature divides every logit by T before the softmax. Below 1 the gaps between the logits grow, so the likeliest token takes more of the probability; above 1 they shrink and the tail grows; as T falls to 0 the softmax becomes greedy, and 0 is used to mean exactly that. Top-k keeps the k likeliest candidates and gives the rest probability 0. Top-p, also called nucleus sampling, keeps the fewest likeliest candidates whose probabilities reach p. Both then renormalise what is left so that it adds up to 1 again. The function below applies the three in that order, and it is the order the explorer in step 1 uses.

#### Do it: eight settings on one turn, Rs 0

Temperature moved probability between the likeliest token and the tail without removing anything: 60 went from 0.941 at 0.5 to 0.582 at 1.5, and the chance of a figure the clause does not say went from 0.002 to 0.190, and to 0.299 at 2.0, while all seven candidates stayed possible. Top-k 2 and top-p 0.90 cut the tail off outright: two candidates left, both saying 60. Top-p 0.95 needed a third candidate to reach 0.95, and let 15 back in. A sharper distribution does not make the likeliest token any more correct; it only makes the others rarer. That is all these knobs can do, on a model that honours them.

### The loop, and five runs of one prompt counted

The whole decode loop on the toy, until the end token or the cap; then five seeded runs per setting, with the distinct answers counted.

#### Definition

The loop is step 3's turn, repeated until it stops. The toy remembers only the last token it wrote, so its whole "model" is a table: for each last token, the logits of the tokens that may follow. A real decoder computes those logits from the whole text, every time, but the loop around it is the same: score, shape, pick, append, look again. It stops in one of two ways, and the kit's code reads which: the model picks the end token (finish reason `STOP`), or the cap on output tokens comes first (`MAX_TOKENS`). Then the experiment this lesson is about: one prompt, five runs, the distinct answers counted, at five settings of the temperature and one of top-k, with the same five seeds every time so that only the setting changes.

#### Do it: thirty runs and one cut short, Rs 0

Greedy wrote "60 days ." five times: one distinct answer, because nothing in the loop was left to chance. Sampling at temperature 1.0 wrote 3 distinct answers of five, every one with the right figure: the variance was wording, "sixty" for "60" and "from acknowledgement" added, which a reader would accept. Heating it raised the count to 4 at 1.5 and 5 at 2.0, and the figure itself started to move: at 1.5, 1 of the five stated a figure the clause does not say, and at 2.0, 2. Top-k 2 at 2.0 kept 4 distinct wordings and the figure right in all five. The cap of two tokens cut the greedy answer off as "60 days" with finish reason MAX_TOKENS: an answer that never finished, which is a different failure from a wrong one, and the reason the kit's code reads the finish reason before it reads the answer.

Hold on to the shape of that result, because step 7 asks the same question of a real model: does it say the same thing five times, and when it does not, is the difference wording or the figure? The toy answered it by construction. Gemini answers it by measurement, with one difference that matters: there, you cannot turn the temperature down.

### What the kit sends Gemini, and why no temperature

The client, the model, the one generate_content call and its config; what Google's pages say about the knobs it leaves out; and how its thinking is priced.

#### Definition

You have not cloned the kit yet (that is lesson 0.2), so this step reads it here, verbatim. DocuMind's API writes every answer with one function, `_call()` in `services/rag-api/generator.py`: one `generate_content` on a client built for the `global` location, with the model from `config.py` (`gemini-3.6-flash` unless a deploy sets another) and a config of four settings: JSON as the reply's type, `ModelDraft` as its schema, `max_output_tokens` at 2,048, and thinking level LOW. A tenant's context cache joins them when one is live. What is not there is the point of this step: no temperature, no top-p, no top-k, no seed. The prompt is the system rules, the packed clauses and the question, in one text part; a packed figure adds its image.

#### The code

Read the comment in `_call()`. Its first half is the knobs: the model ignores all three, so passing one would only make the code look as if it controlled something. Its second half is the thinking: the kit asks for a level, not a budget of zero, because Gemini 3 thinking cannot be switched off. The streamed answer, further down the same file, asks for the same LOW.

- gemini-3.6-flash, the kit's model. Its model page says it does not support custom values for temperature, top-k and top-p: a custom value is ignored, not refused. Frequency and presence penalties are stricter: a custom value there throws an error. The model's developer's guide says to control output determinism with the thinking level or a structured JSON schema instead.

- The earlier Gemini 3 models. The Gemini API's Gemini 3 guide strongly recommends keeping temperature at its default of 1.0, because the models' reasoning is optimised for that setting, and warns that setting it below 1.0 may cause looping or degraded performance, particularly on complex maths and reasoning.

- Thinking. gemini-3.6-flash takes MINIMAL, LOW, MEDIUM or HIGH, and MEDIUM is its default. The Gemini 3 guide adds that MINIMAL does not guarantee that thinking is off, and that one request cannot carry both `thinking_level` and the older `thinking_budget`. The Gemini API's price list labels its output price "including thinking tokens".

So "Gemini 3 ignores temperature" is exact for the model the kit calls, and a simplification for the others, where Google advises against changing it rather than ignoring it.

Why would a lower temperature hurt? Google's guide gives its reason in one line: the reasoning is tuned for the default. Step 4 showed what a lower temperature does: it moves probability onto the likeliest token, and at 0 the loop always takes it. A loop that always takes the likeliest next token is known to fall into repeating itself on long outputs, and a model that writes many thought tokens before every answer runs its loop far longer than the answer you see. That fits the looping the guide warns about. For gemini-3.6-flash Google has gone one step further and stopped honouring the setting at all; its pages give no reason beyond naming the two levers to use instead. The kit uses both: thinking level LOW, and a schema that fixes the answer's shape.

#### Thinking, priced

Thought tokens are billed as output, and the kit counts them that way: `_usage()` adds `thoughts_token_count` to `candidates_token_count` for every attempt, and the price list in `shared/prices.py` charges output at USD 7.50 per million tokens on `gemini-3.6-flash`, against USD 1.50 for input. At the kit's Rs 85 to the dollar, that is Rs 0.64 per 1,000 output tokens, thinking included, and Rs 0.13 per 1,000 input tokens: a thought token costs 5 times what a prompt token costs. The cap bounds it: the thinking and the answer share the same 2,048 output tokens, at most Rs 1.31 a call. When a long think crowds the answer out and the reply is cut off, `generate()` asks once more with 6,144, at most Rs 3.92 more, and bills both attempts.

You read every setting the kit sends Gemini, and the ones it leaves out on purpose. The two live cells that follow use exactly these: the same client on `global`, the same model, the same schema copied from `shared/documind_schemas.py`, the same thinking level and cap, the prompt `generate()` builds, and the prices from `shared/prices.py`. The build ran both cells against a stand-in client to check that the config they send is `_call()`'s, setting for setting; only Gemini's answers are missing until you run them.

### Gemini, five times: count the distinct answers

The generator's own prompt for one golden question, sent five times with the kit's config; the distinct answers and the right figure counted, and the five calls priced.

#### Definition

This is the lesson's proof, on the real model. The prompt is the one `generate()` builds when retrieval hands it a single clause: the rules from step 6, the handbook's clause NP-03 as `[Source 1]`, and the question of golden row `lk-06`, whose check is that the answer states 60. The config is `_call()`'s, setting for setting. The cell asks five times, prints each answer, and counts two things: distinct answers (the exact text, with runs of spaces collapsed), and answers that state 60 by the boundary rule `run_eval.py` uses, where the figure must stand on its own, so "160" does not count (unlike `run_eval.py`, the cell does not read "sixty" as 60). The prompt is about 195 tokens by the kit's own estimate (four characters a token); the cell prints what the five calls cost, and they cannot cost more than Rs 6.53 in output even if every call ran to the cap.

This cell and the one in step 8 call Gemini on your own Google Cloud project, so they need lesson 0.1's project and the setup's second block (the sign-in and `PROJECT`). If you have not made the project yet, read the author's recorded output below, go on to lesson 0.1, and come back: the cells will wait.

Read the two counts together. More than one distinct answer with every answer stating 60 is variance in wording: the model drew different tokens around the same figure, as the toy did at temperature 1.0, and a reader loses nothing. An answer that drops the figure, or states another, is the variance that matters, and it is what the golden set's `must_contain` check exists to catch. The five calls were independent: nothing one run wrote could steer the next, and the schema held all five to the same shape (an answer, citations, a confidence and the answerable flag). Your counts may differ from the recorded ones. That difference is the subject of this lesson, and lesson 3.1 measures it properly, with more runs, on the kit's own generator.

### Two thinking levels: thought tokens and rupees

One golden question that needs two clauses, asked at the kit's level and at the deepest, with the thought tokens read off the usage and priced from the kit's list.

#### Definition

Golden row `jn-01` joins two clauses: probation's notice (PB-02) and leave on exit (LV-07), and its check is that the answer says 15 days and that leave cannot be encashed. The prompt is again `generate()`'s, with both clauses packed, about 252 tokens by the kit's estimate. The cell sends it at `LOW`, the kit's level, and at `HIGH`, and gives both the 6,144-token room that `generate()` gives its one retry, so that a long think at HIGH is not cut off. For each level it prints the thought tokens, the answer tokens, the prompt tokens, the finish reason, the cost at the kit's prices and the answer. Two calls: at most Rs 7.83 in output, even if both ran to the cap.

The thought tokens are the part of each bill you pay for and never read. They are charged at the output rate, the same as the answer, so a level that thinks more costs more even when the answer it leads to is the same length. Then compare the two answers against the row's check: if LOW already said 15 days and that leave cannot be encashed during probation, the extra thinking at HIGH bought nothing on this question, and the kit runs every answer at LOW. One call per level is one sample, and thought counts vary from run to run like everything else the loop writes; lesson 3.1 asks each level five times.

### Verify it yourself: the checklist

Eleven checks, each one cell or excerpt above, each with what proves it.

Nothing that lasts. The setup's venv, `~/basics-venv`, holds numpy and google-genai, and the offline cells in steps 3 to 5 only printed. If you ran steps 7 and 8, your project made seven calls to `gemini-3.6-flash`, five and then two, billed at the rupee figures the cells printed, and each call was independent of the others: nothing carries from one call to the next, which is why five calls can disagree. Lesson 0.1 is next: the billing account, the budget alert and the project those paid cells need, if you have not made them yet.

Netsetos GenAI on GCP · Basics · Lesson B.5 Generate with GPT-style models: decoding and run-to-run variance · v5.0

Next: Lesson 0.1 Set up the Google Cloud billing account, budget and project.
