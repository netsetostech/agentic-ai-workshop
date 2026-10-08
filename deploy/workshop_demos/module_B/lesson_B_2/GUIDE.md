# Lesson B.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_B.2_Tokens_Embeddings_WIX.html`, reviewed at blob `1395591d92dec2c9a56f1342d31a0d356441f8a6`. Learners read that page on the course site; this guide keeps its prose.

Every call the kit makes to Gemini is counted and billed in tokens, and every search it runs compares embeddings. This page builds both from the bottom, on your laptop. You will train a tokenizer small enough to read on two clauses of the kit's handbook, put the kit's two token estimates beside plain character counts, and price a sentence with the kit's own prices the way lesson 3.4 prices an answer. Then you will ask gemini-3.6-flash for its own count of that sentence, embed three clauses and two questions with text-embedding-005 under the task types the kit uses, and compare them by cosine similarity in numpy. Two cells call Vertex AI in your project, for a fraction of a paisa; the rest never leave your machine.

- What a token is, and what an embedding is

- The words: token, vocabulary, merge, estimate, count, price, embedding, task type, cosine

- Before you run anything: set up your laptop

- A tokenizer you can read: byte-pair merges on two handbook clauses

- The kit's two estimates against plain character counts

- The rupee line: tokens priced with the kit's prices

- The model's own count: count_tokens on gemini-3.6-flash

- Cosine similarity in numpy, on vectors you can read

- Real embeddings: text-embedding-005 under the kit's task types

- Verify it yourself: the checklist

You will learn what a token is (a piece of text from a vocabulary a tokenizer learned, the unit a model counts and bills), how the kit estimates tokens before a call and prices them after, and what an embedding is (768 numbers for a whole text) and how cosine similarity compares two. Then you will prove it on your laptop: one sentence's token count with its rupee line, and the cosine similarity of real embeddings.

### What a token is, and what an embedding is

Two readings of the same text: the pieces a model counts and bills, and the numbers retrieval compares.

A token is the unit a model reads, counts and bills. A language model does not read letters or words. A tokenizer reads first: it cuts the text into pieces from a fixed vocabulary, learned once from a large amount of text, and hands the model each piece's number. Common words come out as one piece, often with the space in front of them; rarer words come out as two or three; a word the vocabulary never saw falls apart into short pieces and, at worst, single characters or bytes, so no text is ever unreadable. A model's limits and a Gemini call's price are counted in these pieces: the price per million tokens in and out, the budget lesson 3.4 packs evidence into, and the 2,048 tokens text-embedding-005 reads of one text, cutting off the rest by default.

The exact count needs the model, so the kit estimates first. Counting exactly takes the model's own tokenizer, which means a call to the model's endpoint: Vertex AI does not charge for it, but it is a round trip for every text, and the kit sizes its prompts and its batches without one. So it estimates from the length. The API divides the characters by four to budget a prompt (lesson 3.4), and the ingest worker divides them by three to size its embedding requests (lesson 1.3). Google's pricing page writes the same rule of thumb down: about four characters to a token. It is a guess, and the toy tokenizer below shows why: the same number of characters can be very different numbers of pieces, depending on what the vocabulary has seen. Step 6 puts the model's own count beside the guess.

An embedding is a whole text as one list of numbers. An embedding model reads a text's tokens and returns a fixed number of numbers for the whole of it: 768 for text-embedding-005, whether the text is a question of 8 words or a clause of 28. The numbers mean nothing one at a time. Together they point in a direction, and the model is trained so that texts which mean similar things point in similar directions. Cosine similarity measures how alike two directions are: 1 for the same direction, 0 at right angles, -1 for opposite. Retrieval is that arithmetic: embed the question, and fetch the passages whose vectors point most nearly the same way.

Two readings, on every question. The kit does both every time someone asks DocuMind something. It estimates the prompt's tokens to pack it, and prices the answer's tokens in rupees afterwards. And it embeds the question with the same model and the same dimension it used for every stored passage, under a task type that tells the model which side of the search the text is on: RETRIEVAL_DOCUMENT for passages, RETRIEVAL_QUERY for questions. Generation runs on the `global` location and embeddings are served regionally, from `us-central1`, so the kit keeps two clients, and so will your cells.

The rubber-stamp press and the compass. A small press sets a page with rubber stamps: one stamp for each common word, syllable stamps for the rest, single letters as the last resort, and it charges by the stamp pressed. A familiar sentence takes few stamps; a sentence full of names the tray has no stamp for takes many, and a script the tray was never built for takes a stamp a letter. That is a tokenizer and its bill. An embedding is a different job: a reader who finishes the page and, instead of a summary, writes down a compass bearing in 768 directions. Two pages about the same thing get nearly the same bearing, however long each page is, and cosine similarity is how close two bearings are.

The text is the kit's own data: lk-06 is a row of the kit's golden set, the questions its evaluations ask (Module 4). The rest are the kit's numbers: the estimate is `estimate_tokens()` in rag-api's `context_budget.py`, the prices are `shared/prices.py`'s, and the two models and their locations are the ones `generator.py` and the ingest worker's `indexer.py` call. Steps 3 to 5 open the middle box; steps 6 to 8, the two on the right.

#### Try it: the token meter

The meter runs the toy tokenizer of step 3, the 65 merges it learns from two handbook clauses, on a text you pick or type, and puts beside it the two estimates the kit makes before a call and the rupee line at gemini-3.6-flash's standard rates. Pick the Hindi question and watch the toy fall back to a piece a character; type a sentence of your own about leave or notice and watch the words the handbook taught it come out whole.

Each chip is one piece, and a dot stands for the space a piece begins with. The counts are the text's characters, its UTF-8 bytes and its words. The estimates are the kit's two rules, `len // 4` in the API's `estimate_tokens()` and `len // 3` in the worker's `batches()`, and the price is `shared/prices.py`'s for gemini-3.6-flash at Rs 85, on the API's estimate. When this page was built, the meter's script and the Python of steps 3 to 5 were run on the same 12 texts, and they agreed on every piece and every paisa.

It is not Gemini's tokenizer. The toy learns 65 merges from 407 characters, so it knows the words those two clauses repeat and little else. Gemini's tokenizer is also learned from text, from vastly more of it, with a far larger vocabulary, so it cuts ordinary English into fewer, longer pieces; this page does not load it, and step 6 asks the model to count instead. The meter's estimates and prices are the kit's real rules, character for character. Only the pieces are a toy.

### The words: token, vocabulary, merge, estimate, count, price, embedding, task type, cosine

Ten rows, each with where the word lives on this page and in the kit.

Two of these words are the bill (token, price), two are how the kit learns a count (estimate, count_tokens), and the rest are retrieval's. Lesson 1.3 stamps the embedding's model, version and task type on every row the kit stores, and lesson 3.4 packs a prompt by the estimate and prices its tokens. This page is the arithmetic under both, run where you can see every number.

### Before you run anything: set up your laptop

Every cell on this page runs on your own laptop, in a bash shell: the Terminal on macOS or Linux, WSL or Git Bash on Windows, or Cloud Shell in a browser. The Python is 3.12, the version the kit's services run in their images (`python:3.12-slim`), inside a virtual environment of its own, `~/basics-venv`, so nothing is installed into the Python your system uses. Most cells need no account and no network. The cells that call Gemini need the Google Cloud project you create in lesson 0.1 and Application Default Credentials, and their labels say so.

Set up the venv once. The block below finds a Python 3.12 or newer, makes the venv the first time and activates it every time after. Then it installs the two libraries the Basics pages use, at fixed versions: numpy for the arithmetic, and google-genai, at the version the kit pins, for the calls to Gemini. The last line proves both import.

The cells that call Gemini need two more things: your project from lesson 0.1, and Application Default Credentials, the sign-in Google's client libraries read. Run the block below once, after lesson 0.1, in the same shell; the browser opens for the sign-in. It uses the gcloud CLI, which lesson 0.2 installs on a laptop and Cloud Shell already has. As in the kit, Gemini 3 models are called on the `global` location and the embedding model on `us-central1`.

### A tokenizer you can read: byte-pair merges on two handbook clauses

Learn a vocabulary from 407 characters of the kit's handbook, cut the golden question with it, and see why the same word can cost one piece or three.

#### Definition

Byte-pair encoding, the idea behind many real tokenizers, learns a vocabulary by counting. Start with every word of the training text as single characters, keeping the space in front of a word as part of it. Count every pair of neighbouring pieces across the whole text, join the commonest pair into one new piece wherever it occurs, and do it again. Each join is a merge, and the list of merges, in the order they were learned, is the tokenizer. To cut a new text, split it into words the same way and replay the merges in order: whatever the merges never joined stays in smaller pieces, down to single characters. The cell runs this on two clauses of the kit's handbook, NP-03 (the notice period) and PB-02 (probation), and stops when no pair occurs twice. It needs nothing but Python.

#### Do it: learn the merges, then cut five texts

The first merges were the commonest letter pairs in the two clauses (`on`, `ti`, `th`), then spaces joined to the letters after them (`' a'`, `' s'`), and pair by pair whole words formed: `' notice'` at merge 25, `' probation'` among the last. The golden question came out as 23 pieces for 45 characters: the words the clauses repeat (`' the'`, `' notice'`, `' period'`) whole, and the words they use once or never (`What`, `confirmed`) in letters and fragments. The same word cost one piece with a space before it, two with no space and three with a capital letter, because those are three different strings to a tokenizer. `Bengaluru`, which the clauses never contain, fell apart into its 9 letters. Nothing was unknown and nothing was lost: the pieces always join back into the text.

Not the idea: the scale and the base. Many real tokenizers work on bytes rather than characters, or fall back to bytes for a character they do not know, and in UTF-8 a Devanagari letter is three bytes (step 4 counts them). They learn from vastly more text, so far more words are whole pieces. And a model's vocabulary is fixed when the model is trained: the model is billed in, and limited by, the pieces of its own tokenizer and no other, which is why the count that matters is the model's own (step 6).

### The kit's two estimates against plain character counts

The API divides by four and the ingest worker by three: what each rule says about the same four texts, and where each one decides something.

#### Definition

Before it calls a model, the kit needs a token count it can compute for free, so it estimates from the length. rag-api's `estimate_tokens()` divides the characters by four, and lesson 3.4's packer uses it block by block to fill a prompt's budget. The ingest worker's `batches()` divides by three and closes an embedding request at 250 texts or 15,000 estimated tokens, because the embedding model takes at most 250 texts and 20,000 tokens in one request and refuses an over-full request whole (lesson 1.3); dividing by three counts more tokens for the same text than dividing by four, which errs on the safe side of that ceiling. Both round down and never return less than 1. Neither looks at anything but the length, so each rule treats English, Hindi and an amount in lakhs alike, so many characters for so many tokens, and the cell puts each answer beside the characters, the bytes and the words.

#### The code

#### Do it: four texts, five counts each

For English, characters and bytes are the same number: the golden question is 45 of each, 11 tokens to the API and 15 to the worker, and the NP-03 clause, 212 characters, is 53 or 70. The same question in Hindi is 48 characters, close to the English, so the estimates barely move (12 to the API), but it is 120 bytes, because every Devanagari letter and vowel sign takes three bytes in UTF-8. The estimate cannot see that; only the model's count can, and step 6 asks for it. Keep the two rules apart: `len // 4` is what lesson 3.4's budget is made of, and `len // 3` decides how many embedding requests a document takes.

### The rupee line: tokens priced with the kit's prices

Dollars per million tokens, input and output apart, then rupees at the rate the kit carries with every figure: lesson 3.4's arithmetic for a whole answer, run on one sentence.

#### Definition

A model's price is two numbers per million tokens: one for the input you send, one for the output it writes. The kit keeps them in `shared/prices.py` with the rupee rate beside them, and rag-api's `cost.price()` does the same arithmetic on every answer: the input at the input rate, cached input at a tenth of it, the output at the output rate, the total in dollars and in rupees, and the rate returned with the figures. Lesson 3.4 prices a whole answer that way. This cell prices one sentence, the golden question, on the API's estimate of its tokens: what it costs to send, what the same tokens would cost if the model wrote them, and what a lakh of such questions comes to.

#### The code

The two files carry the same numbers on purpose. The chat service has no access to the price table in BigQuery, so it prices from `shared/prices.py`, and a test in the kit holds that table equal to `cost.py`'s fallback. When this page was built, the cell's two constants were checked against both files, and its dollars and rupees against the kit's own `usd()` and `inr()`.

#### Do it: the golden question's rupee line, Rs 0

11 tokens of input cost $0.000017, which is Rs 0.0014, or 0.14 paise. That is the rupee line, and every cost the kit reports has its shape: a count, a rate, dollars, then rupees at a rate printed beside them. The same tokens as output cost 5 times as much, because gemini-3.6-flash's output rate is 5 times its input rate: what a model writes costs more than what you send it. A lakh of these questions as input comes to Rs 140.25, which is why the cost of one question is never the interesting number; the volume is. A real answer's input also carries the system prompt and the packed evidence, which is the part lesson 3.4 budgets.

The kit prices gemini-3.6-flash at Google's standard rate, $1.50 in and $7.50 out per million tokens. Google's pricing page lists an introductory rate for it of $0.75 in and $3.75 out through 31 December 2026, and the standard rate from 1 January 2027. So until the end of December a call on the `global` location costs you half the kit's line. The pages and the kit use the standard rate throughout, so their figures do not change on 1 January.

### The model's own count: count_tokens on gemini-3.6-flash

The proof this lesson is named for: one sentence counted by the model that would read it, with its rupee line, and two more texts beside it.

#### Definition

`count_tokens` runs the model's own tokenizer on a text and returns the number, without generating anything, and Google's page for it says there is no charge for using it. For the Gemini 3 family the call goes to the `global` location, where the kit's generation client lives. The API packs prompts by the estimate, but `context_budget.py` was written so that the model's counter can be handed in instead, and lesson 3.4 does exactly that to show where the estimate drifts. This cell counts three texts: the golden question, which is this lesson's proof, the same question in Hindi, and the handbook's sentence with an amount in lakh notation. Each line carries the length, the API's estimate, the model's count, and the rupee line on that count, with step 5's prices and step 5's arithmetic.

#### The code

#### Do it: three texts, the model's count, and the rupee line

The first line is the proof: a sentence's token count, from the model that would read it, and its rupee line, priced as step 5 priced the estimate. Put the count beside step 5's estimate of 11 and the toy's 23 pieces: the toy, with a vocabulary of 104 pieces (its 39 characters and 65 merges), had to spell out every word the two clauses did not repeat, and the count shows what a vocabulary learned from far more text does with the same 45 characters. The second line is the same meaning in another script, and the third is the same kind of sentence with digits and commas in it; read each count against its estimate, which saw only the length. Whatever the counts are, they are what the bill is made of: a price per token is only as good as the count it multiplies.

### Cosine similarity in numpy, on vectors you can read

The one formula retrieval runs, on two-number vectors first and then on word counts of three handbook clauses, before the model's vectors in step 8.

#### Definition

Cosine similarity is the dot product of two vectors divided by the product of their lengths. It is the cosine of the angle between them: 1 when they point the same way, 0 at right angles, -1 when they point opposite ways. It ignores how long they are, so a short question and a long clause can still score 1, and when both vectors already have length 1 the division changes nothing and the dot product alone is the cosine. The cell shows each of those on two-number vectors you could draw on paper. Then it builds vectors you can read: one dimension per distinct word in three handbook clauses and two questions, each value the word's count. The first question is golden row lk-05, whose answer is IT-SEC-04; the second asks the same thing in other words.

#### Do it: four cosines, then word counts against meaning

`a` and `b` scored 0.96; ten times `a` is still `a`, to the cosine; a vector at right angles scored 0 and the opposite one -1; and the same two directions at length 1 gave 0.96 again by the dot product alone. Then the word counts did what word counts do. The golden question shares four words with IT-SEC-04 (`are`, `company`, `on`, `usb`) and scores 0.2887 there, but it also scores 0.0680 against the payroll clause, because both contain `on`. The reworded question asks the same thing and shares no word with IT-SEC-04, so it scores 0 there, while the travel clause, which shares only `at`, comes first at 0.0550. A pen drive is a USB mass-storage device to anyone who reads English, and to a vector of word counts it is nothing at all. That gap is what an embedding model is for.

#### Where the kit computes this number

Three places, three spellings of the same arithmetic. The Firestore rung, which answers when Vector Search will not, asks Firestore for the nearest rows by cosine distance and turns the distance back into a similarity, 1 minus it, so the reranker can order both rungs the same way. The Vector Search index compares 768-number vectors by dot product, which is the cosine when the vectors have length 1; Google's guide to its text embedding models says their vectors come back normalized, and step 8 prints the lengths so you can see it for yourself. And the answer cache (Module 6) serves a stored answer to a new question only when the two questions' cosine similarity is at least 0.95: its comment says why the line sits there, with two questions that differ in one word.

### Real embeddings: text-embedding-005 under the kit's task types

The same three clauses and two questions, embedded the way the worker embeds a passage and the API embeds a question, and compared with step 7's function.

#### Definition

The kit embeds in two places with one model. The ingest worker embeds every passage it stores, in requests of at most 250 texts, under `RETRIEVAL_DOCUMENT`; the API embeds every question under `RETRIEVAL_QUERY`; both ask for 768 numbers, and both use a client on `us-central1`, because the embedding models are served regionally while Gemini 3 generation is served from `global`. The two task types are a pair: the model shapes a passage's vector and a question's vector so that the two can be compared, and a text sent with no task type at all is embedded as a query. This cell does what the kit does, with step 7's texts: one request for the clauses as documents, one for the questions as queries, then the cosine of every question against every clause, by step 7's own function. It also prints what the model reports about its reading: how many tokens each text was, and the characters it bills.

#### The code

#### Do it: five texts, two requests, six cosines

Every text became 768 numbers, the 8-word question as much as the 28-word clause. The lengths are your check on Google's word that the vectors come back normalized: at length 1, the index's dot product and step 7's cosine are the same number. The tokens are the model's own count for each text, from the embedding model's tokenizer this time. The two rows of cosines are the proof's second half, and they belong under step 7's word-count rows. For the golden question, see whether IT-SEC-04 still leads, and by how much. For the reworded one, see where IT-SEC-04 lands now that meaning is compared instead of spelling, and where the travel clause, first by word counts, lands now. That comparison is the whole case for embeddings, measured on your own laptop.

#### What the page's cells cost

The kit's own price table has no embedding price. The list price above was read off Google's pricing page, and the line prices every character sent, spaces included; the bill itself uses the billable characters the API reports with each response, which step 8 prints beside them.

### Verify it yourself: the checklist

Eight checks, each one cell above, each with the value that proves it.

Nothing was installed beyond the setup's venv, and no cell wrote a file. Steps 3, 4, 5 and 7 never left your machine. Step 6 made three `count_tokens` calls and step 8 two embedding requests, in your project on Vertex AI: no charge for the first, at most Rs 0.0011 for the second, and nothing stored anywhere. Lesson B.3 follows the tokens into the model: a transformer block in numpy, one attention head's weights over a sentence, and the layer normalization between its steps.

Netsetos GenAI on GCP · Basics · Lesson B.2 Turn text into tokens and embeddings · v5.0

Next: Lesson B.3 Read a transformer block, with layer normalization.
