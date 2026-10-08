# Lesson B.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_B.4_Encoder_Models_WIX.html`, reviewed at blob `c5e0d3ccaccb4143687b69cae20a2d562c329369`. Learners read that page on the course site; this guide keeps its prose.

BERT taught a machine to read a sentence in both directions at once, by hiding words and asking for them back. Encoders in that style do two jobs in a retrieval system, and DocuMind has a model for each. The embedding model turns every chunk, once, and every question, as it arrives, into 768 numbers that are compared by arithmetic: a bi-encoder, fast enough to search the whole corpus. The ranker reads the question beside each of the 20 candidates and scores the pair: a cross-encoder, too slow for the corpus and sharper on the shortlist. You will fill hidden words from counts, score four handbook clauses with a toy bi-encoder and a toy cross-encoder, read the kit's two calls in its own code, and then score the same clauses both ways with the real models on your own project.

- What an encoder is, and the two ways the kit uses one

- The words: encoder, mask, embedding, bi-encoder, cross-encoder, score

- Before you run anything: set up your laptop

- The masked-language idea: fill the blank from both sides

- A bi-encoder: two texts, encoded apart, compared by cosine

- A cross-encoder: one pair, read together, scored once

- The kit's two encoders, in its own code

- One question, four clauses, scored both ways on your project

- Where each encoder sits, and what each costs

- Verify it yourself: the checklist

You will learn how an encoder learns to read (by filling hidden words from both sides) and the two shapes it takes in retrieval: a bi-encoder that turns the question and each chunk into vectors apart and compares them by cosine, and a cross-encoder that reads the question and a chunk together and scores the pair. Then you will prove it: toys of both offline, the kit's two calls read in its own code, and the real two scoring one question side by side.

### What an encoder is, and the two ways the kit uses one

Reading in both directions, learning by filling blanks, and the two shapes an encoder takes when it scores a question against a passage.

An encoder reads the whole text at once. It is a transformer in which every token attends to every other token, the ones before it and the ones after it, so each token comes out as a vector shaped by its neighbours on both sides. The "leave" in "unused earned leave" and the "leave" in "I want to leave" come out as different vectors, because their neighbours differ. A decoder, the GPT-style model of lesson B.5, may only look left, because it writes one token after another; an encoder only has to read, so it looks both ways. Pool its token vectors into one (their average, or the output of a special first token) and a whole text becomes one vector.

BERT learned to read by filling blanks. School exams have a "fill in the blanks" section for a good reason: a student who can fill every blank in a passage has understood it, and the passage is its own answer key. BERT (Devlin and colleagues at Google, 2018) was pre-trained on that exercise over 3,300 million words of books and Wikipedia: hide 15% of the tokens and predict them from the context on both sides (beside a second, smaller task: guessing whether one sentence follows another). No person labels anything. To fill "serves a ___ period of 60 days" well, a model has to learn that periods of notice are served, counted in days and tied to a grade. Step 3 runs the idea on four clauses of the kit's handbook with nothing but counts.

One encoder, two ways to score a question against a passage. After pre-training, an encoder is trained further for a job, and retrieval uses it in two shapes. A bi-encoder encodes the question and each passage separately, one vector each, and compares the two vectors afterwards by cosine. Passages can be encoded once, long before any question, and stored; a question then costs one encoding and some arithmetic, the kind an index is built to do over millions of stored vectors. The price is that the model never sees the question and the passage together: whatever a passage's one vector did not keep, no comparison can recover. A cross-encoder takes the question and one passage as a single input and lets attention run across both, so each word of the question can bear on each word of the passage, and one relevance score comes out. It is usually the more accurate of the two, and nothing can be computed before the question arrives: every pair is a full pass of the model, so it only ever reads a shortlist.

DocuMind uses both, in that order. Every chunk was embedded once at ingest by `text-embedding-005` under the document task type; every question is embedded under the query task type; the index returns the 20 nearest chunks. Then the Ranking API's `semantic-ranker-fast-004` reads the question beside each of the 20 and returns the request's `top_k`, 5 by default, highest score first. Retrieve with the bi-encoder, rerank with the cross-encoder. Google documents what these two models take and return, and that is all the kit depends on, not how they are built: "bi-encoder" and "cross-encoder" name the two roles they play.

The broker's cards and the site visit. A broker keeps a card for every flat on the books, written when the flat was listed: two bedrooms, third floor, near the metro, the rent. When you call, the broker writes a card for you too and pulls the twenty flats whose cards look most like yours. That is fast, because cards are compared with cards, and no card was written with you in mind. That is the bi-encoder: every flat summarised once, every tenant summarised once, matched by comparing summaries. Then you visit five of the twenty with your own needs in your head, and find the lift that stops at the second floor and the "near the metro" that is a twenty-minute walk. A visit sees the flat and you together, which no card can, and it is far too slow to make for every flat in the city. That is the cross-encoder, and DocuMind books it the same way: cards for the whole corpus, visits for the shortlist.

The left column is the kit's retrieval: each clause was embedded at ingest under the document task type, each question is embedded under the query task type, and the two are compared by arithmetic, which is why it can run against the whole corpus. The right column is the kit's reranking: the question and a candidate's text go to the ranker together and come back as one score, which is why it runs only on the pool. The 1,628 is acme's corpus as the kit's chunker cuts it.

#### Try the two scorers

The explorer runs a toy of each on the four handbook clauses the rest of this page uses, plus one sentence twice: LV-07's last clause on its own, and the same words swapped round. The toy bi-encoder knows 23 hand-made words on five named axes, makes each clause and the question into one vector apiece, and compares them by cosine. The toy cross-encoder is one hand-written rule that reads the pair: how many of the question's ideas a sentence of the clause holds in the question's order. Pick the second question, which is the first one's words in another order, and watch which column moves.

Each row is one passage. The upper bar is the toy bi-encoder's cosine between the passage's vector, made once before any question, and the question's vector; the lower bar is the toy cross-encoder's score for the pair, the share of the question's ideas that the passage's best sentence holds in order. The first two questions have the same words, so every upper bar stays put between them: each text became one vector before the comparison, and these vectors are sums, which keep no order. The lower bars move, because the rule reads the two texts together.

It is two toys, not two models: 23 words, five axes and one rule, the same code as the cells in steps 4 and 5, checked against them on 54 question and passage pairs when this page was built. Words outside the 23 are ignored, and a question in the passive voice fools the rule. What carries over to the real models is the structure. A bi-encoder fixes each text's vector before it sees the other text, so whatever that vector dropped (here, all word order) no comparison can bring back; a cross-encoder reads the pair, so anything in either text can count.

### The words: encoder, mask, embedding, bi-encoder, cross-encoder, score

Ten words, each with what it is in the kit.

Some of this comes from earlier pages: lesson B.2 measured the cosine between two embeddings, and lesson B.3 computed an attention head's weights for one sentence, the operation every layer of an encoder runs. This page adds what they are for in retrieval: the training that teaches an encoder to read, and the two shapes an encoder takes when it scores a question against a passage.

### Before you run anything: set up your laptop

Every cell on this page runs on your own laptop, in a bash shell: the Terminal on macOS or Linux, WSL or Git Bash on Windows, or Cloud Shell in a browser. The Python is 3.12, the version the kit's services run in their images (`python:3.12-slim`), inside a virtual environment of its own, `~/basics-venv`, so nothing is installed into the Python your system uses. Most cells need no account and no network. The cells that call Gemini need the Google Cloud project you create in lesson 0.1 and Application Default Credentials, and their labels say so.

Set up the venv once. The block below finds a Python 3.12 or newer, makes the venv the first time and activates it every time after. Then it installs the two libraries the Basics pages use, at fixed versions: numpy for the arithmetic, and google-genai, at the version the kit pins, for the calls to Gemini. The last line proves both import.

The cells that call Gemini need two more things: your project from lesson 0.1, and Application Default Credentials, the sign-in Google's client libraries read. Run the block below once, after lesson 0.1, in the same shell; the browser opens for the sign-in. It uses the gcloud CLI, which lesson 0.2 installs on a laptop and Cloud Shell already has. As in the kit, Gemini 3 models are called on the `global` location and the embedding model on `us-central1`.

### The masked-language idea: fill the blank from both sides

How BERT learned to read without labels, tried on four clauses of the kit's handbook with nothing but counts.

#### Definition

BERT was pre-trained on BooksCorpus (800 million words) and English Wikipedia (2,500 million). In every sequence it is shown, 15% of the tokens are chosen; 80% of those become `[MASK]`, 10% become a random token and 10% stay as they are, so the model can never tell which tokens it will be asked about. It must predict each chosen token's original from a vocabulary of 30,000 word pieces, and it may look both ways to do it, because nothing in an encoder's attention hides the right-hand side. A left-to-right model, the GPT style of lesson B.5, may only look left, because it writes left to right. No person labels anything: the text is the answer key.

The cell runs the same exercise at toy scale. Its text is four clauses of the kit's handbook, the same four the rest of this page scores. It hides one word, leaves the blank in its sentence (so the hidden word is never counted), and asks the rest of the text which words have stood next to the blank's neighbours: first only the word on its left, then the words on both sides, one count each.

#### Do it: hide three words and ask the text for them, Rs 0

Three blanks, three outcomes. In the first, the word on the left, `a`, has been followed by `confirmed` once and `maximum` once, so the left side alone ties between two wrong answers. The word on the right, `period`, has been preceded by `notice` twice, so with both sides `notice` wins, 2 against 1. In the second, both sides together offer six candidates and not one of them is `15`: the right side says a number of days goes here, and no other sentence says which, because the value belongs to this clause alone. In the third, `earned` on the left is enough; in this text it has only ever been followed by `leave`.

The second blank is the line this course is built on. Language teaches a model what kind of word belongs in a blank; only the document says which one. A model that has read billions of words knows that a notice period is counted in days, and it cannot know that ACME's probationers serve 15 of them. That is why DocuMind retrieves the clause and hands it to the model rather than trusting the model's memory.

BERT does not count neighbours. Its attention reads every token of the sequence at once, not one word on each side; what it knows lives in learned weights (110 million in BERT-base), not in a table of pairs; and it predicts word pieces, so a word it never saw whole can still be spelled from parts. The counts share one thing with it, the objective: fill the blank from the context on both sides, with the text as the answer key.

### A bi-encoder: two texts, encoded apart, compared by cosine

One text in, one vector out; the clauses encoded before any question exists; the question scored by arithmetic.

#### Definition

A bi-encoder is a function from one text to one vector, and nothing more: it never sees two texts at once. Similarity is computed afterwards, between vectors, usually as a cosine. That one restriction is what makes it fast at scale. The documents' vectors can be made once, ahead of time, and stored; a question then costs one more vector and some arithmetic, and an index can do that arithmetic over millions of stored vectors. The toy below is a bi-encoder you can read: 23 hand-made words, each pointing along one of five named axes (leave, exit, pay, probation, reduce) with a weight. A text's vector is the sum of its known words' vectors, scaled to length 1; every other word is ignored. A real embedding model learns its 768 axes, which nobody can name, but the shape of the job is the same.

#### Do it: a five-axis bi-encoder on the four clauses, Rs 0

The store came first: four rows of five numbers, made before the question existed. LV-01 is all leave, PB-02 mostly probation, NP-03 mostly exit, and LV-07 is spread over all five axes, because the clause says several things. The question leans equally on leave and exit, with some reduce. NP-03 scores 0.926: its notice words meet the question's exit, and its last sentence adds leave and a word that shortens. LV-07, which also answers the question, scores 0.679, only 0.032 above LV-01, which does not: half of LV-07 is about encashment, and its pay axis pulls its one vector away from the question. That is the bi-encoder's weakness in one line: a clause becomes one vector, and the vector is a blend of everything the clause says.

The paraphrase shares a single word with the clauses, `notice`, and still ranks them in the same order, because `holidays` sits on the leave axis and `cut` on the reduce axis: meaning by direction, not by spelling. And the cost: the four rows were paid for before the question arrived, which in the kit means at ingest; the question cost one encoding and four dot products.

Three things the toy lacks. Learned axes: hundreds of them, set by training rather than by hand, so that "resign" and "quit" land near each other without anyone listing them. Context: a trained encoder reads each word with its neighbours, so the leave in "earned leave" and the leave in "leave the company" get different vectors, where this toy gives a spelling one vector wherever it appears. And roles: a task type, so a question's vector is made to be compared with documents' vectors. What does not change is the shape: one text in, one vector out, the comparison afterwards.

### A cross-encoder: one pair, read together, scored once

The question and the clause as one input, a score that belongs to the pair, and why a cross-encoder only ever reads a shortlist.

#### Definition

A cross-encoder takes the pair as its input. BERT's paper packs two texts into one sequence, `[CLS]` first text `[SEP]` second text `[SEP]`, and reads a judgement about the pair off the output vector of `[CLS]`. A BERT-style reranker is that design, trained on question and passage pairs to say how well the passage answers. Inside, attention runs across the boundary, so every word of the question can bear on every word of the passage: which grade, which way a rule runs, whether a "not" covers the part that matters. The score belongs to the pair and to nothing else, so nothing can be computed before the question arrives.

The toy's rule reads the pair too. It turns each text into its ideas: the axes of its known words, in order, with repeats merged. Then it scores a clause by its best sentence: how many of the question's ideas that sentence holds in the question's order, gaps allowed, out of all of them. Lining two sequences up against each other is a property of the pair, and the bi-encoder's vectors, being sums, keep no order to line up.

#### Do it: the same pairs, read together, Rs 0

The two clauses that answer the question score 1.00: NP-03's last sentence and LV-07's last sentence each hold leave, then a word that shortens, then notice, all three of the question's ideas in its order. The two clauses that only share its topic score 0.33: LV-01 holds leave and nothing else, and PB-02's best sentence holds notice and nothing else. Where the bi-encoder put LV-07 0.032 above LV-01, the rule puts two-thirds between them, because it read the one sentence of LV-07 that answers instead of a blend of the whole clause.

Then the swapped pair. The same words in another order make identical vectors, so the bi-encoder gives both sentences 0.980, though one says the opposite of the other. The rule, reading each against the question, gives 1.00 and 0.33.

#### Why a cross-encoder only ever reads a shortlist

A bi-encoder's work splits in two: the documents' half is done once, at ingest, and the question's half once per question, and what is left is arithmetic. A cross-encoder's work does not split, because the pair is the input. Ranking acme's 1,628 chunks against one question would take 1,628 passes of the model, and the next question as many again. The Sentence-BERT paper (Reimers and Gurevych, 2019), which made BERT-style bi-encoders practical, measured the gap: finding the most similar pair among 10,000 sentences means 49,995,000 pairs for a cross-encoder, about 65 hours of BERT on the authors' hardware, against about 5 seconds for a bi-encoder. So the two are used together: the bi-encoder narrows the corpus to a pool, and the cross-encoder reads only the pool. The kit's code, next, does exactly that.

### The kit's two encoders, in its own code

Where the question is embedded and where the chunks were, how the two are compared, and what rerank() sends instead of vectors.

#### Definition

The kit runs neither encoder itself: both are Google's models, called over the network, and the kit's code decides how each is used. The API's query handler embeds the question once, retrieves the pool with that vector, then reranks the pool. The worker embedded every chunk at ingest, under the document task type; the API embeds every question under the query task type, with the same model, through a client in the same region. The index compares the two by dot product, and the Firestore rung by cosine distance turned into a score; no word of text is read at this stage. Then `rerank()` sends the question and each candidate's text to the Ranking API, and the ranker's order and scores replace the retrieval's. Nothing here runs today: these are read-only excerpts from the kit you clone in lesson 0.2.

#### The order of work: the bi-encoder first, the cross-encoder second

#### The bi-encoder side: documents at ingest, the question at query time

These are the two halves of one bi-encoder, in two services. The worker's half runs once per chunk, in batches, and its vectors are stored; the API's half runs once per question and is never stored. Both name the same model and ask for the same 768 numbers, through a client on `us-central1`. They differ in one setting, the task type, and the difference is deliberate: `RETRIEVAL_DOCUMENT` and `RETRIEVAL_QUERY` are a pair the model makes to be compared with each other. The worker stamps the model, its version and the task type on every row, and lesson 1.3 shows how the kit uses that stamp to keep anything embedded another way out of the comparison.

#### The comparison: arithmetic on two vectors

Two stores, one comparison. Vector Search, which answers by default, ranks by dot product; Firestore, the rung beneath it, ranks by cosine distance and flips it into `1.0 - distance`, so both hand the reranker a similarity in which higher is closer. For vectors of length 1 the two give the same order, which is why the step 7 cell scales its vectors to length 1 before it multiplies. Read the excerpt's last line: on this rung each candidate drops its embedding on the way out, and whichever path found a candidate, what the reranker and the generator read from it is its text.

#### The cross-encoder side: text, not vectors, to the Ranking API

Everything the cross-encoder needs is in the request: the question, and each candidate's text as a numbered record. No vector is sent; the ranker reads words. The ranking config sits on `global`, the model is `semantic-ranker-fast-004`, and `top_n` is the request's `top_k`: 5 unless the caller asks for more, up to 20. The response comes back in the ranker's order, and each record's score is written on its chunk as `rerank_score`, the score a citation carries. The pool is cut to 200 records, the limit the kit's comment gives; Google's Ranking page now lists up to 1,000 a request, and a pool of 20 comes near neither. If the ranker raises or misses its deadline, the pool goes back in retrieval-score order (on the kit's default path, the bi-encoder's order), marked as a fallback; lesson 2.3 forces that on a lane and reads the mark.

The model is a choice. Google's launch post described `semantic-ranker-fast-004` as its fastest ranker, for latency-critical use, and `semantic-ranker-default-004` as its most accurate. Both read up to 1,024 tokens of a record and truncate the rest, and since 1 September 2026 Google's Ranking page also lists 005 versions of both. The kit pins fast-004 in `config.py`, so a change is one line.

Lesson 1.3 opens the document side on a lane: the stamp on every row, the batches and the vectors carried over when a document is re-issued. Lesson 2.1 opens the question side: the query's embedding and the filters that travel with it. Lesson 2.3 runs the rerank on a lane: the pool, the scores on the citations, the clock on the stage and the fallback. This page is the idea under all three.

### One question, four clauses, scored both ways on your project

The kit's two calls from your laptop: four embeddings and a cosine each, one rank request and a score each, then the two side by side.

#### One more API

The embedding cell uses Vertex AI, which the setup switched on. The Ranking API is served by Discovery Engine, a separate API: switch it on once for your project. Enabling it costs nothing; the ranker bills per request.

#### The bi-encoder side: text-embedding-005, a fraction of a paisa

The cell is the kit's two embedding calls in miniature. It embeds the four clauses in one request under `RETRIEVAL_DOCUMENT`, as the worker embeds a document's chunks, and the question under `RETRIEVAL_QUERY`, as the API embeds a question, with the kit's model, its 768 numbers and its region. Then it scales every vector to length 1 and takes the dot products: four cosines. It saves them to `~/b4_bi.json` for the comparison. The two requests carry 773 characters between them, about 0.16 paise.

#### The cross-encoder side: the Ranking API over REST, 8.5 paise

The kit calls the ranker through Google's Discovery Engine client library. Your Basics venv has only numpy and google-genai, and REST needs nothing more than libraries google-genai installed with it: `google-auth`, which turns your Application Default Credentials into an access token (through `requests`, another of them), and `httpx`, for the call itself. The path is the kit's ranking config, and the body is the kit's request (the model, the question, one record per clause with its text, and top_n) plus one flag that asks for ids and scores without the texts echoed back. The `X-Goog-User-Project` header is in Google's own example: with a person's sign-in rather than a service account, it names the project the call is billed to and counted against. Four records are one query, at USD 1 per 1,000 queries of up to 100 records each: Rs 0.085.

#### Side by side, Rs 0

The proof of the lesson: the same four pairs, scored both ways. The cell reads the two files, ranks the clauses by each score, and prints three things: each scorer's first choice, how many of the six pairs of clauses the two put in the same order, and how far each score spreads from its highest to its lowest.

Two models scored the same four pairs, and only one of them ever saw a pair. Each cosine came from two vectors the embedding model made separately, the clause's under the document task type and the question's under the query task type. Each ranker score came from one call that held the question and the clause's text together. Read the comparison by order, never across the columns by number: a cosine and a relevance score are different quantities on different scales, so a cosine beside a ranker's score says nothing on its own, however far apart they are.

Then hold it against the toys of steps 4 and 5, whose test was this same question: two clauses that answer it, NP-03 and LV-07, and two that only share its topic, LV-01 and PB-02. See whether the real bi-encoder also scores a topic clause close to an answer, and whether the ranker opens a wider gap between them. That gap is what the kit pays Rs 0.085 a question for.

### Where each encoder sits, and what each costs

Done ahead or not, one call or a pool's worth, and the rupees per question at the kit's scale.

The two encoders split the work by when it can be done. Everything below is computed from the kit and from Google's price pages (embeddings per 1,000 characters; ranking per 1,000 queries, a query being up to 100 records), at Rs 85 to the dollar.

For this page's question the ranker costs about 741 times what the question's embedding does, and it still costs only Rs 0.085. The asymmetry is the design. The bi-encoder's expensive half, the corpus, is paid once (Rs 4.39 for acme, and afterwards only for chunks that change); every question after that is nearly free, and fast because it is arithmetic. The cross-encoder pays per question and per record, so the kit gives it the 20 candidates the bi-encoder found and nothing more. Over the whole of acme it would be 17 queries, Rs 1.445, for every question, in two requests (one takes at most 1,000 records), before the wait for 1,628 pairs to be read.

Where the cross-encoder earns its price is in the two cases this page built by hand: a clause whose one vector is diluted by a second topic, and two texts with the same words and opposite meanings. Where the bi-encoder earns its place is everywhere else: it is the only one of the two that can look at the whole corpus. Neither replaces the other, and when the ranker does not answer, the kit falls back to the retrieval order, not to nothing.

### Verify it yourself: the checklist

Eleven checks, each one block above, each with the value that proves it.

Two small files in your home folder, `b4_bi.json` and `b4_cross.json`, written by step 7's cells and read by the comparison; delete them whenever you like. The Discovery Engine API is now on for your project; being on costs nothing, and the ranker bills per request. Step 7 made three paid requests, two to the embedding model and one to the ranker, about Rs 0.087 together. Everything else ran offline in `~/basics-venv`, and no cell installed anything. Lesson B.5 turns from the encoder to the decoder: the GPT-style model that writes the answer one token at a time, and why the same prompt can come back with different answers.

Netsetos GenAI on GCP · Basics · Lesson B.4 Encode with BERT-style models: embeddings and rankers · v5.0

Next: Lesson B.5 Generate with GPT-style models: decoding and run-to-run variance.
