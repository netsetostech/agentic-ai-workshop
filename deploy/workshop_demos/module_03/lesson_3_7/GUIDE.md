# Lesson 3.7: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_3.7_Streaming_WIX.html`, reviewed at blob `9ff597141a0ff947d0c0cf9acf42158424a2f234`. Learners read that page on the course site; this guide keeps its prose.

Lesson 3.5 returned one JSON. This lesson returns the same answer as it is written. `/v1/stream` keeps one connection open and sends Server-Sent Events down it: the citations first, because the packed set is known before a single token exists, then each piece of text as the model produces it, then one `done` event with the envelope, or an `error` when the guard refuses the finished answer. The stream takes the same roads as the query and keeps the same clocks; a cache hit and an empty pool each arrive as a single token; and when something on the way fails, the retriever's index, the ranker, the classifier, the cache, the month's counter, the tracing, the answer is still served and one line in the log says what stood in. You will read a stream in curl with a clock on each event, see why its citations differ from the query's, stream the empty pool, read the guard's two doors, force a failure on a candidate that takes no traffic and watch the stream continue, and read the table of everything that degrades and what it degrades to.

- Why a stream, what its four events carry, and what degrades into a line

- The words: SSE, citation event, token, done, error, held, blocked, fallback, stream row, first token

- Before you run anything: set up the shell

- A stream in curl: the raw events, their order, and a clock on each

- What a stream's citations are, and the streams of one token

- The guard: a prompt refused before the stream, an answer held until it is screened

- A failure forced on a candidate: the ranker silent, the stream still served, the line in the log

- Every failure and what it degrades to

- What a stream costs, what its row says, and who reads it

- Verify it yourself: the checklist

You will learn what the stream's four events carry and in what order, why its citations are the packed set rather than the model's, how the guard sits on both sides of the stream, and how each failure on the way degrades into a log line with the answer still served. Then you will prove it on your lane: time a stream event by event, stream the empty pool, read the guard's column on the rows, force the ranker to stand down on a candidate and read the line, and check the events the lane has never logged.

### Why a stream, what its four events carry, and what degrades into a line

The first token is the point, the sources come before it, the same clocks run without spans, and a failure is a line in the log rather than an empty screen.

A stream exists for the first token, and the sources come before it. `/v1/query` answers once, when everything is done. `/v1/stream` answers as Server-Sent Events on one connection: `event: citation` lines first, one per packed chunk with the fields a `Citation` carries and the first 240 characters of the text as its quote; then `event: token` for each piece of text as the model produces it; then one `event: done` with the envelope, tokens, model, backend, the three clocks and the pool, the cache verdict and the prompt version. The citations are the packed set because that is known before a single token exists, so the UI can render the sources while the answer is being written; the price is that a stream cites every packed source and the query cites only the ones the model used, and lesson 3.5's resolver never runs here, because JSON cannot usefully be streamed. The tokens are prose with `[N]` marks, and `N` is the packed position.

The stream takes the same roads and keeps the same clocks. The handler's order is the query's: the roster, the filter keys, the guard before the stream starts, so a blocked prompt is a 400 and never a broken stream; then retrieve, rerank with its fallback, and generate, on the same three clocks without spans, because a generator suspended between tokens is no place to hold a span. A cache hit arrives as one token with backend `cache`; an empty pool arrives as one token with backend `none` and no model call; the row is logged with event `stream` and the same columns as a query's. The clock the caller feels is different from the API's: the time to the first citation, the time to the first token, and the time to `done` are three numbers, and only the last is `latency_ms`.

A failure degrades into a line, not a 500. Every rung the request climbs has a stand-in and a name: a classifier that fails is `routing_fallback` and the generator model answers; a routed tier out of quota before the first token is `tier_exhausted` and the default model streams; an index that raises is `vector_search_fallback`; a silent ranker is `rerank_fallback`; a cache that cannot be read is `semantic_cache_failed` and a miss; a cache that cannot be written is `semantic_cache_store_failed`; a month's counter that cannot be written is `budget_record_failed`; tracing that cannot load is `telemetry_not_instrumented`. In each case the answer is served, the log names the cause, and where it matters the row counts it. Two things do not degrade, on purpose: a prompt the guard blocks is refused before the stream, and a finished answer the guard blocks becomes `event: error` after the held tokens are screened, with `blocked_response` on the row.

The live commentary. A radio commentator reads out the team sheets before the whistle, every player who is on the pitch, which is the citations from the packed set. Then the commentary runs play by play, which is the tokens. With the delay censor switched on, the broadcast runs a few seconds behind and either goes out whole or is cut with one announcement, which is the guard holding the tokens and the error event. When the scoreboard feed dies mid-match, the commentator carries on from the referee's list and the producer notes it in the log; nobody at home hears a gap. The final whistle carries the bill, the clocks and who was in the booth, which is `done`.

#### The stream reader: paste a transcript, read it event by event

The reader parses the text `curl -N` prints, or the transcript step 3 saves: the events in order, the citations with their kinds and dates, the tokens joined back into the answer, and the `done` event's envelope, read against the handler's rules. It starts on a transcript shaped exactly as main.py writes one, with two of the kit's handbook chunks as the citations and that chunk's own words standing in for the model's; the cases turn it into the other shapes a stream can take.

The event names and their fields are main.py's, the sample's clocks are the kit's usage selftest rows, and the readings under `done` are lesson 2.3's rules for a stages block. Paste your own transcript from step 3 and the numbers are yours.

It is not a client: it reads a finished transcript and cannot show the one thing a stream is for, the first token arriving before the rest. Step 3's cell times that. And its sample answer is a chunk's own words, because the model's are not known until it writes them.

### The words: SSE, citation event, token, done, error, held, blocked, fallback, stream row, first token

Ten rows, each with the value it takes on your lane.

One distinction carries the lesson: a fallback serves the answer and writes a line; a refusal serves the contract with `answerable false`; a failure is a status the caller sees. The stream has all three, and the reader below tells them apart by the events alone.

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

The guard, the answer cache, the router and the ranker's deadline live in the API's environment, each with a default the page names; a name the service does not set is unset rather than exported empty. `/version` reports the cache and the model.

### A stream in curl: the raw events, their order, and a clock on each

The handler that writes the events, the generator that yields the packed list once and then the text, and a cell that times the first citation, the first token and done.

#### Definition

`generate_stream()` yields three kinds of thing: `packed` once, with the list the budget kept; `token` for each piece of text from `generate_content_stream`; and `usage` at the end from the last chunk's metadata, which carries the totals. The handler turns the packed list into citation events with the fields a `Citation` carries, sends each token as it comes unless the guard is holding them, and closes with `done`. The cell asks the notice-period question on the stream, records the millisecond each event kind first arrived, saves the raw transcript for the reader, and asks the same question on the query to set the two citation counts side by side.

#### The code

#### Do it: one stream, timed, then the query's citations beside it

Three clocks the caller feels, one the API keeps. The citations arrived when retrieval and reranking were done, about a second in; the first token arrived when the model began, another second later; and `done` came when it stopped, which is the only number `latency_ms` measures. The five citations were the packed set, every chunk the model was shown, and the query's three were the ones it chose to cite, which is the difference between knowing the sources before the answer and knowing which sources the answer used. The tokens were prose with the packed positions in brackets, and the envelope in `done` was the query's minus the price, which the row carries.

### What a stream's citations are, and the streams of one token

The citation event from a packed chunk, the two cases that send one token and no model call, and the rows the three streams left.

#### Definition

A citation event is built from the packed chunk's own fields, the same nine a `Citation` carries, so the UI renders a figure or a video segment from the stream exactly as from the query. Two streams never reach the model. An answer-cache hit, when `SEMANTIC_CACHE` is on, sends the stored answer's citations, then the stored answer as one token, then `done` with backend `cache` and cost zero; the UI cannot tell, the row can. An empty pool sends no citation, one token that is the refusal the API writes itself, and `done` with backend `none`; the row's `answerable false` feeds the alert. The cell streams the empty pool with the same filter lessons 5.x used, and then reads the rows the streams of this step and the last have written, with the columns that tell them apart.

#### The code

#### Do it: the empty pool as one token, then the stream rows

The filter emptied the pool, and the stream did what the query does in the same case, without a model: no citation events, because nothing was packed, one token carrying the API's own refusal, and a `done` whose backend is `none` and whose rerank and generate clocks read zero because they never ran. The rows told the same story in the columns lesson 2.3 read: the empty stream with `answerable False` and no tokens, the cited one with its pool of twenty and the model's tokens, both with the guard `off`. Both also read `ui` in the brain column, although curl sent no label: the API records a request that names no brain as `ui`, so that column cannot tell a shell from the UI. The row's `user` can, and lesson 3.8 reads it.

### The guard: a prompt refused before the stream, an answer held until it is screened

Model Armor on both sides of the model, why the stream holds its tokens when the guard is on, and what each verdict does to the events and the row.

#### Definition

The guard is a setting, `ARMOR`, and a template, and it is imported only when the setting is on, so a revision that never asked for it neither pays for its client nor fails on a template it does not have. On, it sits on both sides of the model. Before retrieval it screens the prompt, because an injection that reaches the retriever has already chosen which documents the model reads; a block is a 400 with the reason and a `guard` line, and the stream never starts. After generation it screens the finished answer, and a token stream cannot be screened, so the stream holds every token, screens the whole once, and then sends either all of them or one `error` event; the row is logged first, with `blocked_response`, so the rate is counted even when the caller sees nothing. Off, as on your lane, every row says `guard: off`, and the tokens go out as they come. Turning it on needs the template in Model Armor and the role on the service account, which Module 4 does; here you read the two doors and the column.

#### The code

#### Read the lane, Rs 0

Every answer of the day carried the guard's verdict, and every verdict was `off`, which is the honest column for a lane that has not installed the template: not `pass`, which would claim a screening that did not happen. The two doors are in the code above, and the stream's held list is the part that costs something when the guard is on: the first token waits for the last, and the feature this lesson is about is traded for the screen. That trade is Module 4's to make.

### A failure forced on a candidate: the ranker silent, the stream still served, the line in the log

The stream's own rerank branch, a candidate whose ranker deadline is a millisecond, the citations and tokens that still arrive, the flag in done, and the line that names the cause.

#### Definition

The stream reranks on the same function as the query and reads the same mark: when the Ranking API does not answer inside `RERANK_TIMEOUT_S`, the pool by retrieval score stands in, every chunk is marked, and the handler puts `rerank_fallback 1` into the stages that `done` carries and the row logs. The caller sees citations in the retriever's order and tokens as usual; the log has one `rerank_fallback` line with the error's type. The way to see it without harming anyone is the candidate from lesson 2.3, a revision that takes no traffic with a deadline of one millisecond, asked on the stream this time; the undo removes the variable, because the live service does not set it. The same block reads the startup event the lane has never written, `telemetry_not_instrumented`, because a fallback that has never fired is worth one line of proof too.

#### The code

#### Do it: the ranker silent for one revision, the stream read, the line read, the undo

The ranker had one millisecond, did not make it, and the stream did not notice in any way a caller could see: three citations came first, then the tokens, then `done`. Only `done.stages` said what happened, `rerank_fallback 1`, and the log named the error, which is the whole design: a worse order served on time, counted where a person will look. The telemetry read printed nothing because the instrumentation loaded on every revision the lane has run, and a line that is absent when it should be is as much a proof as one that is present. Then the variable came out and the tag went.

### Every failure and what it degrades to

Eight named fallbacks in the API, where each one lives, what stands in, what the caller sees, and where it is counted; and the three things that do not degrade.

Three things do not degrade, on purpose. A prompt the guard blocks is a 400 before the stream starts, because a refusal dressed as an answer would hide the rate. A finished answer the guard blocks is one `error` event on the stream and a 502 on the query, after the row has said `blocked_response`. And a reply the generator cannot parse is a 502 on the query, never a refusal, which lesson 3.5 forced; on the stream there is no schema to fail, and a model that returns nothing simply ends the stream with `done` and no tokens. The managed stores' own fallbacks, `rag_engine_fallback` and `vertex_search_fallback`, take the same shape and belong to Module 7.

#### The code

Nothing ran here; the table is the map. Read it as one rule applied eight times: every place the request depends on something outside the container has a stand-in that serves, a name in the log, and, where the answer's quality changed, a count on the row. The two blocks and the 502 are the places where serving would be the wrong thing to do, and each says so to the caller instead.

### What a stream costs, what its row says, and who reads it

The rupee line, the rows by surface, the UI's own reader of the same events, and the two clocks a product manager will ask about.

#### What it costs

#### The rows by surface, and the reader in the UI

`make usage` groups the rows by the surface that wrote them, and a stream row is a query row with `event: stream`: the UI's chat page labels its streams `brain: ui`, and a request from a notebook or curl that names no brain is recorded as `ui` too, so the surface table counts the event, not who sent it. The UI reads the events with an iterator of a dozen lines, the same three names, and renders the sources as the citation events arrive and the answer as the tokens do, which is lesson 3.8's page. The two clocks worth keeping apart when someone asks whether the product is fast: the time to the first token, which is what the reader of a chat feels and which no row records, and `latency_ms`, which is when the model stopped. Step 3 measured both; a slow first token with a fast `done` points at retrieval and the ranker, the reverse at a long answer.

#### The code

#### Do it: the day by surface, Rs 0

The day's rows split by surface, and the stream rows were this lesson's: four of them, one unanswerable, priced like any query's, because a stream changes when the caller gets the answer and not what it costs. The UI's reader is the same dozen lines you wrote in step 3, which is why lesson 3.8 can render a cited answer as it streams without knowing anything about the model.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

Nothing that serves traffic. A candidate revision took no traffic, answered one stream with its ranker silenced, and lost its variable before the tag was dropped. The streams you ran are usage rows with `event: stream`, one of them unanswerable, and the transcript sits at `/tmp/stream63.txt`. Lesson 3.8 puts a screen in front of all of this: the upload, the versions list, and the chat that renders these events as they arrive.

Netsetos GenAI on GCP · Module 3 Generation · Lesson 3.7 Stream answers and handle failures · v5.0

Next: Lesson 3.8 Complete the Streamlit upload-to-answer journey.
