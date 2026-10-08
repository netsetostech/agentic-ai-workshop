# Lesson B.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_B.3_Transformer_Block_WIX.html`, reviewed at blob `8a7a005243dfd1f5be3db61c27dc263c3c01451f`. Learners read that page on the course site; this guide keeps its prose.

Gemini, the model family that writes DocuMind's answers, is built from transformer blocks, and every token the kit sends it passes through every one of them. This page builds one block in numpy on a six-word sentence, a part at a time, so that each part is a few lines you can read and a matrix you can check: the words as vectors, one attention head and its weights, two heads joined, the residual path, layer normalization and the feed-forward step. You will watch a head's weights add up to 1 in every row, every word leave layer normalization at mean 0 and variance 1, and the block hand back six vectors of eight numbers, ready for the next block. Then you will see where the kit meets the same design: in the token counts it plans every call around.

- What a transformer block does

- The words: query, key, value, head, residual, layer norm

- Before you run anything: set up your laptop

- Six words, eight numbers each

- One head: queries, keys, values and the weights

- Two heads, joined, and what a head may see

- The residual path: add the input back

- Layer normalization: mean 0, variance 1, then a scale and a shift

- The block, assembled

- Where the kit meets the block: tokens and their ceilings

- Verify it yourself: the checklist

You will build one transformer block in numpy on the sentence the employee serves ninety days notice: the words as vectors, one attention head and the table of weights it computes, two heads joined, the residual path, layer normalization (each word's eight numbers checked at mean 0 and variance 1) and the feed-forward step, assembled in two orders. Then you will read where DocuMind's kit meets the design: the token ceilings of its embedding requests and the token budget of its prompts.

### What a transformer block does

Six vectors in, six vectors out, and the one step in between where the words look at each other.

A block takes vectors and returns vectors of the same shape. A model reads text as tokens, and each token as a vector of numbers (lesson B.2). A transformer block takes the vectors of a whole sequence at once, six of them for a six-word sentence, and hands back six vectors of the same size. A model is a stack of these blocks, each with weights of its own, the output of one being the input of the next. What changes on the way up is what the numbers carry. Going in, the vector for employee says only "employee, second word"; coming out of a block, it also carries something of the words around it, such as who does what.

Attention is the only step where words meet. Inside the block, three weight matrices turn each word's vector into three smaller ones: a query, what the word is looking for; a key, what it offers to be found by; and a value, what it hands over when it is found. Every query is compared with every key by a dot product, each row of scores becomes shares that add up to 1 (the softmax), and each word receives the share-weighted sum of all the values. One set of the three matrices is a head. A block runs several heads side by side, each free to look for something different, and joins what they return. Every other step in the block works on each word alone.

Two plain-looking parts make a deep stack work. The residual path adds each step's input back to its output, so a word keeps what it was and gains what it found. Layer normalization then moves each word's numbers to a mean of 0 and a variance of 1, followed by a learned scale and shift, so every step receives numbers on the same scale, whatever the step before it did. The last part, the feed-forward step, is a small two-layer network applied to every word on its own.

A stand-up meeting. Six engineers stand in a circle. Each writes the question on their mind on a card (the query), wears a badge saying what they can speak to (the key), and holds their notes (the value). Everyone reads every badge, splits their attention, all of it and no more, by how well each badge answers their card, and copies that share of each colleague's notes into a notebook. Two rounds run at once with different cards: one asks "who spoke just before me?", the other "whose work does mine fit with?". Those are two heads.

Nobody tears out their own pages: what they heard is written beside what they had (the residual path). Before the next meeting everyone rewrites their notebook to one standard size, so the colleague who writes large does not drown out the one who writes small (layer normalization). Then each one thinks alone for a minute over what they now have (the feed-forward step). The next meeting is the next block.

#### The block, part by part

The order is the one in the 2017 paper that introduced the design (Vaswani and others, Attention Is All You Need): each sub-layer, then add, then norm. GPT-2 and most models since move each norm to the front of its sub-layer and add one more at the very top; step 8 builds both orders from the same parts.

#### Try it: the toy sentence's attention, head by head

The explorer shows the weights this page's cells compute for the sentence the employee serves ninety days notice, one table per head. A row is a word asking, a column the word it looks at, and each row's six shares add up to 1. Head 1 looks one word back, and reads only the position numbers. Head 2 looks for the word each word fits with, and reads only the meaning numbers: a thing looks for the action, the action for the person, the amount for the time. The second switch applies the causal mask a GPT-style model uses, under which a word may look only at itself and the words before it.

Darker is a larger share. A hatched cell is masked: its score is set to minus infinity before the softmax, so the rest of the row shares the whole 1. Pick a word on the left to read its row in full. Every number here is one that step 4 or step 5 prints.

Every weight in this block was written by hand, so that each head does one thing you can name. A trained model learns its weights from text; its heads are rarely this tidy, and there are many more of them. What carries over is the arithmetic, which is exactly the same.

### The words: query, key, value, head, residual, layer norm

Thirteen words, each with the value it takes in this page's block.

Three of these come from lesson B.2: the token, the vector and the dot product. The rest is the machinery between them. Lesson B.4 and lesson B.5 put it to work, as an encoder that reads a whole text at once and as a decoder that writes one token after another.

### Before you run anything: set up your laptop

Every cell on this page runs on your own laptop, in a bash shell: the Terminal on macOS or Linux, WSL or Git Bash on Windows, or Cloud Shell in a browser. The Python is 3.12, the version the kit's services run in their images (`python:3.12-slim`), inside a virtual environment of its own, `~/basics-venv`, so nothing is installed into the Python your system uses. Most cells need no account and no network. The cells that call Gemini need the Google Cloud project you create in lesson 0.1 and Application Default Credentials, and their labels say so.

Set up the venv once. The block below finds a Python 3.12 or newer, makes the venv the first time and activates it every time after. Then it installs the two libraries the Basics pages use, at fixed versions: numpy for the arithmetic, and google-genai, at the version the kit pins, for the calls to Gemini. The last line proves both import.

The cells that call Gemini need two more things: your project from lesson 0.1, and Application Default Credentials, the sign-in Google's client libraries read. Run the block below once, after lesson 0.1, in the same shell; the browser opens for the sign-in. It uses the gcloud CLI, which lesson 0.2 installs on a laptop and Cloud Shell already has. As in the kit, Gemini 3 models are called on the `global` location and the embedding model on `us-central1`.

Every cell below is numpy and plain Python: no network, no account, no Google Cloud project and no cost. The second block above, the project and Application Default Credentials, is for the Basics pages that call Gemini; you can leave it for later. Each cell is complete on its own, so you can paste any of them first.

### Six words, eight numbers each

The sentence as the block reads it: each word's own numbers, plus a signal for where it stands.

#### Definition

A block never sees words, only numbers. Each token arrives as a vector; a trained model's vectors are learned and run to hundreds or thousands of numbers. This page's have eight, and you can read every one. Columns 0 to 3 are the word: four numbers set by hand, saying whether it is a thing, an action or an amount, and whether it names a person (+1) or a span of time (−1). Columns 4 to 7 are its position: the sine and cosine of two waves, a slow one that turns 45 degrees from one word to the next and a fast one that turns 90. The word's vector and the position's vector are added before the first block, as in the 2017 paper; here they sit in separate columns, so the sum is also the two side by side.

The position columns are not decoration. Attention compares every word with every word, in no particular order, so without them nothing in a block could tell the employee serves from serves the employee. Step 5 proves it.

#### Do it: build X, Rs 0

X is the whole input: 6 rows, one per token, 8 numbers each. The second table is the property step 4 will use. The dot product of two positions' waves is 2.00 for a position with itself, 0.71 for neighbours, −1.00 two apart and −0.71 three apart, and it is the same at every point in the sentence: it measures how far apart two words are and nothing else. Every position's signal has the same length, 1.41: positions differ in direction, not in size, so no position weighs more than another.

### One head: queries, keys, values and the weights

Three weight matrices, one table of scores, a softmax per row and a weighted sum: the whole of one head.

#### Definition

A head is four lines of arithmetic. Multiply X by three weight matrices to get the queries Q = X WQ, the keys K = X WK and the values V = X WV. Score every query against every key, Q KT / √dk, which for six words is a 6 × 6 table. Turn each row of scores into shares with the softmax: e to each score, over the row's total, so every share is positive and each row adds up to 1. Those shares are the head's weights. Finally, each word's output is its row of weights times V: a weighted sum of every word's value.

The division by √dk, the square root of how many numbers each query and key has, is the "scaled" in the paper's name for it, scaled dot-product attention. If a query's and a key's numbers were independent, with mean 0 and variance 1, their dot product would have a variance of dk: the longer the head, the larger the scores, until the softmax hands almost everything to one key. Dividing by √dk brings the variance back to 1. Here dk = 4, so every dot product is halved.

#### Head 1: one word back

WQ is the matrix to read. It takes only the four wave columns, turns each wave back by one word's angle (45 degrees for the slow wave, 90 for the fast), and multiplies by 4. So the query of the word at position t is four times the waves of position t − 1. WK leaves each key as the word's own waves. By step 3's table, two positions' waves have their largest dot product when they are the same position, so every query scores highest against the key one word back. WV copies the meaning columns: what head 1 hands each word is, mostly, the meaning of the word before it.

Read the employee row. Its query, 0 4 0 4, is four times the waves of position 0, and the key at position 0, the one for the, is 0 1 0 1. Their dot product is 8, which halved is 4.00, the largest score in the row, and the softmax turns it into 0.90. Every row after the first gives 0.85 to 0.90 of its attention to the word before it and spreads the rest thin, because a softmax never gives exactly nothing. The first word has no word before it. Its query points at position −1, so its best match is itself (0.70), with 0.17 left over for ninety, four places from position −1, where the fast wave comes round again. The `out` table is the payoff: serves receives 0.87 of a thing and 0.85 of a person, which is employee, the word before it.

That table of weights is this lesson's proof that a head is arithmetic you can check: 6 rows, each adding up to 1.00, each row one word's attention shared out over all six.

### Two heads, joined, and what a head may see

A second head with its own question, the two outputs side by side, WO; then the causal mask, and the order of the words.

#### Definition

A block runs several heads on the same input, each with its own three matrices, so that each can look for something different. Their outputs are set side by side (concatenated) and multiplied by one more matrix, WO, which maps them back to the block's own width; step 6 needs that, because it adds the result to X. In the cell, `head()` packs step 4's lines into one function, with a switch for the mask used below, and `attention()` runs both heads and WO.

#### Head 2: the word it fits with

Head 2 reads only the meaning columns, and each of its first three columns is one question and the answer it wants. A thing asks for an action (WQ reads `thing`, WK reads `action`). An action asks for a person (`who/when` at +1). An amount asks for a time (`who/when` at −1). Its fourth column is left empty. WO adds half of each head's output into the meaning columns and writes nothing into the position columns.

Head 2's rows read like grammar. employee, days and notice look at serves (0.80); serves looks at employee (0.83); ninety looks at days (0.83). the asks nothing, since none of its meaning numbers is set: all its scores are 0, and the softmax splits its attention evenly, one sixth each, 0.17. The concatenation is 6 × 8, head 1's four numbers and then head 2's, and WO folds the two back into X's eight columns. In the attention output, employee's action column, 0 in X, is 0.40: from head 2 it has picked up the action it goes with, serves.

#### What a head may see: the mask, and the order of the words

An encoder, the BERT-style model of lesson B.4, lets every word attend to every word. A decoder, the GPT-style model of lesson B.5, writes one token after another, so a word must not attend to the words after it: when it is written, they do not exist yet. Before the softmax the decoder sets those scores to minus infinity, which the softmax turns into a share of exactly 0. That is the causal mask. The second half of the cell is the reason for step 3's position columns: reverse the six words, keep the positions where they were, and see which head notices.

Head 1 barely changes under the mask: it was already looking back, and only the, with nothing before it, now gives itself everything. Head 2 changes wherever its answer lay ahead. employee can no longer see serves, so its row splits between the and itself, 0.50 each. ninety cannot see days: it spreads over itself and the words before it, still keeping away from employee (0.02). Reversed, head 2 hands every word the same numbers it handed before, because it reads no position: to head 2 a sentence is a bag of words. Head 1 does not, and one word back from serves is now ninety. In this block the position signal is the only thing that knows the order of the words.

### The residual path: add the input back

One addition that lets a word keep what it was, and what happens to six words without it.

#### Definition

The residual path is the plus sign in x + sublayer(x): the sub-layer's output is added to its input instead of replacing it. That is why WO had to map back to eight columns, since two arrays must have the same shape to be added. It does two jobs. A word keeps its own vector and gains what attention found, so a sub-layer only has to learn a correction to what is already there. And in a stack, the residual paths give the signal a direct route from the first block to the last, around every sub-layer; that is a large part of why dozens of blocks can be trained at all.

#### Do it: add, then stack four times with and without it

The cell adds the attention output to X, compares each word's new vector with its old one by cosine (1 is the same direction, 0 unrelated), then applies the attention sub-layer four times over, once without the residual path and once with it.

H is X plus the attention output, and every word stays close to itself: cos(X, H) is between 0.82 and 0.98. The attention output on its own points elsewhere (0.00 to 0.38), because it is made of the other words. The stack shows why the plus sign matters. Without it, the sub-layer averages the six words into one: by layer 3 the two farthest words are 0.00 apart to two decimals, six copies of a single vector. WO writes nothing into the position columns, so after one layer head 1 has no positions left to read, and each layer is then a weighted average of the one before: averages of averages converge. With the residual path, the position columns ride through every layer untouched, and the two closest words are never nearer than 1.76.

### Layer normalization: mean 0, variance 1, then a scale and a shift

Each word's eight numbers moved to one common scale, checked to six decimals, then given the scale and shift a model learns.

#### Definition

Layer normalization works on one word at a time, across that word's own numbers. Take its eight numbers, subtract their mean, divide by their standard deviation, and the eight come out with a mean of 0 and a variance of 1. A small ε (epsilon; here 0.00001, PyTorch's default) is added to the variance before the square root, so that a word whose eight numbers are all equal does not divide by zero. It leaves the variance a hair under 1, which the cell lets you see in the fifth decimal. Then two learned vectors give the model its say: γ (gamma), a scale for each column, and β (beta), a shift for each column. In one line, for each word: LN(x) = γ × (x − mean) / √(variance + ε) + β. Training starts with γ = 1 and β = 0, which leave the normalized numbers as they are.

It is not batch normalization, which normalizes each column across many examples, so that one example's result depends on the others in its batch. Layer normalization depends on the word alone, and the cell checks that too. Recent open models such as Llama and Gemma use a lighter variant, RMSNorm, which divides by the root of the mean square, with no mean taken off and no shift added; the cell computes it for comparison.

#### Do it: normalize H, Rs 0

Before, the six words sat on different scales: means from 0.0743 to 0.6210, variances from 0.1635 to 0.5675. After, every mean is 0.000000 and every variance 0.999939 to 0.999982: a hair under 1, by about ε divided by the word's own variance, so the most where the variance was smallest. Every normalized word now has the same length, √8 = 2.83: the notebooks of the analogy, rewritten to one size. γ and β then turn the meaning columns up and the position columns down, and the mean and variance become whatever they make them. A word ten times as loud comes out the same, and changing serves moves no other word: each word is normalized alone. RMSNorm's words have a mean square of 1.000, but their means are not 0.

Those six zeros and six variances of 1, to ε, are the second half of this lesson's proof.

### The block, assembled

Attention, add, norm, feed-forward, add, norm: the same parts in the 2017 order and in the norm-first order of GPT-2 and later.

#### Definition

The feed-forward step is the last part: two weight matrices with a ReLU between them (every negative number set to 0), applied to each word on its own. It takes eight numbers out to 32, four times the block's width, the ratio the 2017 paper used, and back to eight. Its weights here come from a cosine and a sine of their row and column numbers, standing in for trained ones, and its biases are zero. With it, the block is two sub-layers, each wrapped the same way. In the paper's order that is LayerNorm(x + Sublayer(x)). GPT-2 and most models since put the norm first, x + Sublayer(LayerNorm(x)), and add one final norm after the last block.

#### Do it: one block, both orders, Rs 0

Six vectors of eight numbers went in, six of eight came out, and a second block took them as they were: that is all a stack is. In the paper's order the block ends on a norm, so every word leaves at mean 0.000 and variance 1.000, with γ and β still at their starting values. In the norm-first order the block ends on an addition, and its words leave with means from 0.052 to 0.507 and variances from 0.180 to 0.679; that is why those models normalize once more at the very top. The block has 840 numbers a training run would set: 256 in attention, 552 in the feed-forward step and 32 in the two norms. In the standard design, where the feed-forward width is four times the block's, the feed-forward step holds about two thirds of a block's weights, as it does here.

### Where the kit meets the block: tokens and their ceilings

The kit never builds a block. It calls models that read tokens, and it plans every call in that unit.

#### Definition

DocuMind calls two kinds of model. Gemini writes the answers. Google's model card for Gemini 3 Pro describes it as a "sparse mixture-of-experts (MoE)" transformer-based model and cites the 2017 paper this page follows; in a mixture-of-experts model, each token is routed to a few of many sets of weights, the experts. The card gives no layer count, width or number of heads. `text-embedding-005` turns every chunk into the 768 numbers of lesson 1.3. The kit never touches a head or a norm. What it meets is the unit both models read, the token, and the ceilings on how many tokens one call may carry.

The reason those ceilings are counted in tokens is in the block you built. Its feed-forward step does the same work for every token, and its attention scores every token of a sequence against every other: in a block like this page's, n tokens make n × n scores, for every head in every layer.

#### The code: the ceilings the kit plans around

The worker cuts a document's text into chunks of at most 2,000 characters (lesson 1.2); the comment above this line in `main.py` calls that about 500 tokens.

The indexer embeds the chunks in requests. It cannot count tokens without a call, so it estimates at three characters a token, which puts a full chunk at 666, above the comment's 500 and so on the safe side. A request closes at 250 texts or 15,000 estimated tokens, whichever comes first.

The loader's copy of the rule says why: the model's own ceilings are 250 texts and 20,000 tokens per request, and a request over either fails whole. The indexer's 15,000 stays 5,000 below the model's 20,000, room for the estimate to be wrong.

On the answering side, the API packs the retrieved chunks into a prompt of at most 8,000 estimated tokens and caps the answer at 2,048 tokens (lesson 3.4). Its estimate is four characters a token; a real count, `client.models.count_tokens`, can be passed in its place.

#### Do it: the kit's numbers, squared, Rs 0

The cell copies those constants, the toy sentence's six tokens beside them, and puts each through the square, then fills one embedding request the way `batches()` does.

One chunk is 666 tokens by the indexer's estimate, and one head of a block like this page's computes 443,556 scores for it in one layer; for the API's prompt budget, 64 million. The embedding request shows that a request's tokens are not one sequence. 22 full chunks fill a request, 14,652 estimated tokens under the indexer's 15,000, and because each text is its own sequence, the request costs 22 small squares rather than one large one: 22 times fewer scores than the same tokens as a single text. Chunks are cut for retrieval (lesson 1.2); they keep every square small as well.

Google does not publish the inner workings of Gemini or `text-embedding-005`, and production models use many techniques to make long sequences cheaper. Read the squares as the arithmetic of the block you built, not as a measurement of either model. The ceilings themselves are Google's (250 texts and 20,000 tokens per embedding request) and the kit's own (the 15,000-token margin, the 8,000-token prompt and the 2,048-token answer), and the kit plans around all of them with estimates, because an exact count is a call of its own.

### Verify it yourself: the checklist

Nine checks, each one cell above, each with the value that proves it on your laptop.

Nothing outside the setup's `~/basics-venv`. Every cell computed in memory and printed: no file was written, nothing was sent anywhere, and no account or rupee was used. You have read every number in one transformer block, from the words' vectors to the six normalized rows it hands on. Lesson B.4 stacks blocks like this one into encoders, BERT-style, and compares the two ways they score a passage against a question: one vector each, or the two read together.

Netsetos GenAI on GCP · Basics · Lesson B.3 Read a transformer block, with layer normalization · v5.0

Next: Lesson B.4 Encode with BERT-style models: embeddings and rankers.
