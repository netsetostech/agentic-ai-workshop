# Lesson 2.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_2.3_Rerank_WIX.html`, reviewed at blob `8add3ea3d051cb7b8df416e54ddb7e3cb12dc3a9`. Learners read that page on the course site; this guide keeps its prose.

Lesson 2.2 measured the pool. This lesson follows it the rest of the way: to the ranking model that reads the question beside each of the twenty candidates and orders them, to the cut at the request's `top_k`, to the packer that fits what is left into the prompt, and to the citations, each carrying the ranker's score. You will read one answer end to end, send the API's own pool to the Ranking API with the API's own request and match its order, force the fallback on a candidate revision that takes no traffic, run `make usage` for p95 per stage, and find where `found_by` lives and how far it travels.

- What the reranker does, and what a clock on every stage is for

- The words: pool, record, reranker, rerank_score, top_k, timeout, fallback, stage, found_by, packed set, p95

- Before you run anything: set up the shell

- One answer, read end to end: the citations, their scores, the stages

- The Ranking API by hand: the API's pool, the API's request, the API's order

- The fallback: the pool by retrieval score, flagged on the row, forced on a candidate

- make usage: where the time went, p95 per stage, and the view behind it

- found_by: stamped on every chunk, counted on the answer, absent from the citation

- What the funnel costs, its knobs, and the packed set the citations come from

- Verify it yourself: the checklist

You will learn why a retriever's order is not the order to read, what the reranker is given and what it returns, how the API keeps a clock on each stage, and what it does when the ranker does not answer. Then you will prove it on your lane: read an answer's citations and stages end to end, rank the API's pool yourself with the same request and match its order, force the fallback on a candidate revision and read `rerank_fallback: 1`, run `make usage` for p95 per stage, and find where `found_by` lives.

### What the reranker does, and what a clock on every stage is for

A retriever guesses about pairs it never saw together; a reranker reads each pair; the row records what each stage cost and whether the ranker answered.

The retriever's order is a guess about the pair; the reranker reads the pair. The dense leg scored every chunk by the closeness of two vectors made apart: the chunk's, at ingest, with no question in sight; the question's, with no chunk in sight. That is fast enough to run over 1,628 chunks and blind to the one thing being asked, so "the notice period for a confirmed E3" lands near every clause about notice periods. The reranker is a model that reads the question and one candidate together and scores the pair. That is slow per pair, so it runs only over the pool of 20, and it decides the order of the five the caller gets. The API sends the pool to the Ranking API's `semantic-ranker-fast-004` as numbered records, text only, at most 200 of them; gets back the request's `top_k` records with a score each; and stamps that score on the chunk as `rerank_score`. That number, not the retrieval score, is the `score` on the citation.

Every stage has its own clock, and the row carries all three. `stage()` in main.py wraps retrieve, rerank and generate: each writes its own milliseconds into the answer's `stages` and opens a span of the same name in Cloud Trace. The usage row flattens the three clocks beside `pool`, the number of candidates the reranker saw, and the warehouse view takes the 95th percentile of each. A page that says "p95 is 3 seconds" tells you to worry; a row that says "generate is 2.6 of them" tells you where.

When the ranker does not answer, the pool by retrieval score stands in, and the row says so. The Ranking API gets `RERANK_TIMEOUT_S`, 5.0 seconds by default, for the whole call. Past it, or on any exception at all, `rerank()` sorts the pool by its retrieval score, marks every chunk, logs one `rerank_fallback` line with the error's type, and returns; the handler puts `rerank_fallback: 1` on the answer and the row, and the view sums those into a column. A worse order is a degraded answer that a person can count.

The shortlist. A recruiter pulls twenty CVs from thousands by the words on them, fast, reading each CV alone; that is the retriever, and the twenty are the pool. An interviewer reads each of the twenty against the job description and orders them; that is the reranker, and the panel room seats five, which is `top_k`. The brief for the panel has a page limit, so a clerk fits in as many of the five as the pages allow, most promising first; that is the packer. The offer letter names only people who were in the room; those are the citations. Every step is timed on the file, and when the interviewer is off sick the recruiter's order goes to the room instead, with a note on the file that says so: a worse shortlist than usual, but a shortlist today, and a note someone will read.

#### The funnel: four cuts between the corpus and a citation

- 1 · retrievethe tenant's chunks, one index, the tenant restrict, retired versions dropped → the pool: `TOP_K_RETRIEVE` = 20 candidates, each stamped with the rung that found itretrieve_ms · pool · vector_chunks · found_by

- 2 · rerank20 records to `semantic-ranker-fast-004` with the question → `top_k` of them back in the ranker's order, 5 by default and 20 at most, each with a `rerank_score`; or the pool by retrieval score, flaggedrerank_ms · rerank_fallback

- 3 · packmost relevant first into the chunk budget, 8,000 tokens less the fixed prompt → the packed set; anything that did not fit is one log linecontext_budget_drop

- 4 · generatethe model reads the packed set and cites by [N] → the citations, resolved against the packed list, each carrying the ranker's scoregenerate_ms · citations[].score

The widths are the cuts, not counts: 20 in, `top_k` out of the ranker, the budget's share out of the packer, and out of the model only the sources it used. Steps 3 to 8 put your lane's numbers on each row.

#### The usage reader: paste rows, read them the way `make usage` does

The kit's `evals/usage_rows.py` reads the last day of usage rows from Cloud Logging and groups them the way the warehouse view does, with the 95th percentile of each stage. The reader below is that arithmetic in the page, on rows you paste: a usage row per line as `gcloud logging read` prints its `jsonPayload`, an answer's `stages` block as step 3 prints it, or a whole answer. It starts on the three rows the kit's own selftest uses, and under the table it reads every row against the handler's rules: what a pool of zero means, when a clock reads zero honestly, which flag says the ranker stood down and which says the index did.

The table is `show_stages()` with the INR and unanswerable columns of `show()` beside it; `p95()` is ported line for line, including Python's rounding of the 95th position. The readings are main.py's rules: a pool of 0 with `backend cache` is the answer cache, with `backend none` the empty-pool refusal; `vector_chunks 0` under a vector backend is the Firestore rung; `rerank_fallback 1` is the ranker standing down. Paste your lane's rows from step 6 and the numbers are yours.

It is not the warehouse: `tenant_daily` runs the same GROUP BY in BigQuery over the sink's copy of the rows once the day has closed. And the four cases it can add are shaped by main.py's rules with the selftest's numbers left in place; a real fallback on your lane is step 5's business.

### The words: pool, record, reranker, rerank_score, top_k, timeout, fallback, stage, found_by, packed set, p95

Ten rows, each with the value it takes on your lane.

One word carries a trap: "score". On a citation it is the ranker's, between 0 and 1, and the citations sort by it into the ranker's order. On the pool it is the retriever's, a dot product on the index or 1 minus a cosine distance on Firestore, and the fallback sorts by that. When a citation's score looks like a retrieval score, check the row before you blame the answer.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible.

The index endpoint and the deployed index are for step 4's pool; the reranker's settings say what the API is running with, and an empty value means the setting's default. Step 4's rank call and the in-process calls in steps 5 and 7 need the API's Ranking client in the venv at the API's own pin; the pip line is harmless if it is already there. A name the service does not set is unset here rather than exported empty, because the kit's settings class reads an empty variable as a value, not as an absence, and a cell that imports the kit would refuse it.

### One answer, read end to end: the citations, their scores, the stages

The handler's order of work, the clock around each stage, the score a citation carries, and two answers to the same question at top_k 5 and 20.

#### Definition

The handler does its work in a fixed order: the roster, the filter keys, the backend and model for this request, the prompt guard, then the retrieve stage, which embeds the question once, asks the answer cache, and pools the candidates. It counts the pool and where each candidate came from. Then one of three things: a cache hit is returned as it was stored, with the rerank and generate clocks at 0; an empty pool is refused in the contract's own shape, same clocks; otherwise the rerank stage runs `rerank()` over the pool and the generate stage packs the result and asks the model. The answer carries the same `stages` dict the row gets. Its citations are the sources the model used, in the order it used them, and `resolve()` in shared/documind_schemas.py gives each one the chunk's `rerank_score` as its `score`, which is why sorting them by score gives the ranker's order among them.

#### The code

#### Do it: the same question at top_k 5 and top_k 20

The cell asks the notice-period question twice and prints, for each answer, the stages block on one line and every citation with its score, its chunk position, its source and the start of its quote. The second answer offers the model twenty chunks instead of five.

Two answers came back with the same pool, twenty candidates from the index, and the same first stage, because retrieval does not read `top_k`. The reranker read all twenty both times and returned five, then twenty; the model cited three or four either way, and each citation's score was the ranker's, so a citation at 0.9 sat above one at 0.6 whatever order the model mentioned them in. The generate clock grew with the second request because the model read four times the context: that is the cost of a wider `top_k`, not in the ranker, which is priced per request, but in the tokens. Nothing says `rerank_fallback` because the ranker answered; step 5 shows the row when it does not.

### The Ranking API by hand: the API's pool, the API's request, the API's order

The lines that build a rank request, and a cell that reproduces the API's citations from outside it.

#### Definition

`rerank()` cuts the pool to 200, the Ranking API's limit, which `TOP_K_RETRIEVE` never reaches; builds the ranking config path on the `global` location; numbers the chunks and sends each one's text as a record; asks for `top_n` of them back with the question; and writes each returned record's score onto the chunk it numbered. The order of the response is the order the caller gets. The whole call has one deadline, `RERANK_TIMEOUT_S`, and one exception handler, which is step 5. The call needs one role on the API's service account, `discoveryengine.viewer` in sa.tf, and your own account has it as the project's owner. The cell fetches the pool the way the API does, sends the API's request, and compares the first five with the citations you saved in step 3. It asks for all twenty back so that step 8 has the ranker's whole order; the ranker scores each record on its own, so `top_n` only truncates the list the API would get.

#### The code

#### Do it: embed, pool, rank, compare

You made the API's two calls with the API's own inputs and got the API's order. The pool came from the same endpoint under the same restrict, in the index's order with the index's scores, with the ledger's retired versions dropped as the reranker never sees them. The rank request was the kit's, record for record, and what came back was the citations' order from step 3: the model was handed those five in that order and cited three of them. Your milliseconds are the row's stages measured from a workstation instead of a container: yours to compare with the clocks, not to match. If the last line says False, the pool changed between the two calls, which a reindex in between will do; run the cell again.

### The fallback: the pool by retrieval score, flagged on the row, forced on a candidate

The two functions that stand in for the ranker, run offline on your pool; then a candidate revision that cannot reach the ranker in time, its answer, its row, and the undo.

#### Definition

`_by_retrieval_score()` sorts the pool by `score`, highest first, cuts it to `k`, and marks every chunk `rerank_fallback`; `rerank_fell_back()` is how the handler notices the mark and sets the flag on the answer and the row. The retrieval score is a similarity on both rungs, a dot product on the index and 1 minus the cosine distance on Firestore, so the fallback's order is the retriever's order. The deadline is a setting read once at startup, and the way to see the fallback without harming anyone is lesson 2.2's: a revision of `documind-api` with `--no-traffic` and a tag, whose deadline is one millisecond, so that no rank call can finish.

#### The code

#### Do it, offline: the kit's fallback on the pool you saved

#### Do it, on a candidate: a deadline no call can meet

Offline, the two functions turned your pool into what a caller gets when the ranker is silent: the retriever's order, cut to five, every chunk marked, and the mark is what the handler reads. On the candidate, the ranker had one millisecond and did not make it, so the answer still came, cited from the same pool in the retriever's order, with scores that look like distances rather than judgements and a row that says `rerank_fallback 1`; the log line named the error. A little worse and a lot faster is the trade the fallback makes on purpose, and the flag is what lets someone count how often it happened. Then the variable came out and the tag went, and the live service showed the ranker back. Step 6 reads the day this left behind.

### make usage: where the time went, p95 per stage, and the view behind it

The rows read from Cloud Logging while they are hot, grouped the way the warehouse groups them, with a column per stage; then your lane's day, and its rows in the reader.

#### Definition

`evals/usage_rows.py` reads the last N hours of usage rows off `documind-api` through `gcloud logging read`, at most two thousand of them, and groups them with the same GROUP BY as `tenant_daily`: by tenant, by model and backend, by brain, by surface, by retrieval backend. Its last table is where the time went: for each tenant, the p95 of the whole beside the p95 of each stage and the average pool the reranker saw. A row from before the stage clocks counts as an answer and in nothing else. Beside the stage columns the view sums `rerank_fallback` into `rerank_fallbacks`, the number that pages someone: a day with a number there served degraded orders, and step 5 put at least one on yours.

#### The code

#### Do it: the selftest, then the lane's last day, then its rows into the reader

Paste the file's lines into the reader in step 1 and its table is `make usage`'s last table for the same rows; under it every row is read, and the one from the candidate carries the flag. A number that comes back as `20.0` rather than `20` is Cloud Logging's doing, which stores every number as a double; `usage_rows.py` and the reader both cast.

The selftest proved the arithmetic on three rows you can check by eye: the dearest tenant first, tokens summed, the 95th latency, one flag making the rate 0.50, the stage p95s never above the whole. Then the same code read your lane's day and put a p95 on each stage, which is the measurement this module asks for: not "the API takes three seconds" but "the ranker takes a third of a second of it, and the model the rest". The rows you saved are the raw material of the tool and the view alike, and the reader shows there is no magic between a row and a column.

### found_by: stamped on every chunk, counted on the answer, absent from the citation

Where the stamp is written, how far it travels, the join that puts it on a citation, the kit's own path run in your process, and the smoke that refuses a pool the index did not serve.

#### Definition

Every rung of retrieval stamps the chunks it returns: `vector` on an id that came out of `find_neighbors`, `firestore` on a row from Firestore's own vector index, whether chosen by the deployment or a tenant's pin or fallen into when the index would not answer, `graph` on a chunk the knowledge graph pointed at, and the two managed names on their stores. The stamp lives on the chunk dict in the API's memory, from the retriever to the packer; what reaches the caller is a count, `stages.vector_chunks`, `graph_chunks` and `managed_chunks`, on the answer and the row. The Citation contract has nine fields and `found_by` is not among them: `resolve()` copies what a reader can open. To put the stamp on a citation from outside, join the citation's chunk id to a pool where the stamp is: the one you fetched in step 4, whose ids are by construction the ones the API stamps `vector`, or the kit's own `retrieve()` run in your process, which is what lesson 2.4's fallback checker does. `make smoke` reads the count and refuses a deployment on `vector` whose pool came from beneath.

#### The code

#### Do it: the join, then the kit's own retrieval in your process, then the smoke

The answer said twenty of twenty came from the index, and the citation had nine fields and none of them was a stamp. The join gave each citation its stamp from the pool you fetched, legitimately, because the API's pool and yours are the same query to the same index under the same restrict. Then the kit's own retriever ran in your process with the API's environment and returned twenty dicts each carrying `found_by: vector`, the stamp seen where it lives. And the smoke read the count the way a release day does, and would have failed with a sentence naming the fix had the Firestore rung answered. Lesson 2.4 makes that rung answer on purpose and shows the stamp read `firestore` with the filters still applied.

### What the funnel costs, its knobs, and the packed set the citations come from

The rupee line, the four numbers that shape the funnel and the one nothing reads, the two places the reranker never runs, and the last cut before a citation.

#### What it costs

#### The knobs, and the one nothing reads

Four numbers shape the funnel. `TOP_K_RETRIEVE`, 20 by default, is the pool's width and the number of records the ranker reads; the ablation's dense-50 arm is how a wider pool is judged, and the row's `rerank_ms` and `pool` columns are what the move costs. The request's `top_k`, 5 by default and 20 at most, is what the ranker returns and the packer is offered. `RERANK_TIMEOUT_S`, 5.0 seconds, is how long the ranker gets before the retriever's order stands in. And `max_context_tokens`, 8,000, is the prompt's whole, of which the chunks get what the fixed parts leave. The fifth number, `top_k_rerank` in config.py, is read by nothing: the request's `top_k` is the cut, and a setting no line reads is one a future reader will trust wrongly.

#### Where the reranker never runs

Two branches of the handler skip it on purpose, and both leave a clock at 0 honestly. An answer served from the answer cache never retrieved a pool, so there is nothing to rank; the row says `backend cache` and cost 0. An empty pool has nothing to rank and nothing to read, so `empty_pool_answer()` writes the refusal in the contract's own shape without a model call; the row says `backend none` and `unanswerable_flag 1`. The reader in step 1 tells the two apart by the backend, which is the handler's own rule. The ablation's first arm, dense 5 with no reranker, is the third place, and it exists to measure what the other arms gain.

#### The packed set: the last cut, and the list a citation resolves against

The ranker's list goes to `_pack()`, which fits the chunks most relevant first into the chunk budget and logs what did not fit as one `context_budget_drop` line. The budget is `max_context_tokens` less the fixed prompt, the system rules, the dated rule held in reserve, the scaffolding and the question at four characters a token: for this lesson's question, 7,832 of 8,000 tokens, with 2,048 reserved for the answer on top. Whether twenty chunks fit depends on the chunks. The handbook's sections average 140 tokens on the kit's mirror, so a notice-period pool of twenty fits with room; the Acts are cut into page windows of up to 500 tokens, and twenty full pages need more than the budget holds, so the packer keeps 15 and drops 5. Your lane's Document AI pages differ a little, and the log line tells you your count. Then the model numbers the packed chunks, cites by [N], and `resolve()` maps each N against the packed list, never the pool: a drop between the ranker and the prompt used to shift every later citation by one, silently, and the packed list is the fix.

#### Do it: the API's packer offline, then a pool of Act pages on the lane

The cell runs the kit's packer with the API's own budget over three lists: your ranked pool at `top_k` 5 and 20, and twenty full pages of the CGST Act's mirror, cut by the kit's own chunker from the file in `evals/corpus`. Then a golden question whose pool is Act pages goes to the API at `top_k` 20, and the log says what the packer dropped.

The kit's packer ran with the API's own budget, and three lists showed the three outcomes: five handbook sections with room to spare, twenty of them still inside the budget, and twenty full Act pages with the last few left in the corridor. The Act question then did the same on the lane, and the log line said how many pages the model was never shown. The dropped ones were the ranker's last, because packing is most relevant first, so a citation to them is impossible by construction, which is the whole reason the citations resolve against the packed list. The header line is what the model actually reads above each chunk, the source's name and its page when there is one, and the number it cites is that header's.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

Nothing that serves traffic. Step 5 created a revision of the API that took none and removed its tag and its variable again; the live revision never changed. The questions you asked left usage rows in Cloud Logging, one of them with `rerank_fallback 1`, and lesson 13's view will count it as a day with one degraded answer, which is true. The four files under `/tmp` are yours to delete. Lesson 2.4 takes the rung beneath the index, makes it answer on purpose, and shows the tenant and the filters holding on the way down.

Netsetos GenAI on GCP · Module 2 Retrieval · Lesson 2.3 Rerank and inspect retrieved candidates · v5.0

Next: Lesson 2.4 Test fallback without losing tenant or metadata filters.
