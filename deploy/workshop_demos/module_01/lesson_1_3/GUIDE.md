# Lesson 1.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_1.3_Embeddings_WIX.html`, reviewed at blob `56ae46416219aee8c45075960c9f86bab98015ac`. Learners read that page on the course site; this guide keeps its prose.

A chunk becomes searchable the moment it has its 768 numbers. This lesson opens the step that makes them in DocuMind: which model, under which task profile, how many texts per request, what is stamped on the row so the lane can tell its own vectors from anyone else's, and how a re-issued document keeps the vectors of every clause that did not change. You will read the stamp off a real row, validate every row of a tenant with the kit's own function, re-issue the handbook and watch 281 vectors carry over while 2 are made, then undo it for nothing.

- What an embedding is

- The words: vector, task type, stamp, batch, carry-over, sparse

- Before you run anything: set up the shell

- One declared embedding, from Terraform to the row

- The call: 768 numbers under the document task type

- Batches: 250 texts and 15,000 tokens per request

- Validate: the stamp, and the function that reads it

- Carry-over: re-issue the handbook, embed only what changed

- The sparse twin, the notebook twin, and what embedding bills

- Verify it yourself: the checklist

You will learn what an embedding is (a chunk's meaning as 768 numbers, made by a model under a task profile), why compatible is a property of four things at once (the model, its version, the task type and the dimension), and how DocuMind stamps them on every row so that nothing incompatible is ever compared. Then you will prove it on your lane: read the stamp, validate a tenant's rows with the kit's function, re-issue a document and count what was reused, and put it back for nothing.

### What an embedding is

A list of numbers that stands for a piece of text, why two lists are only comparable when they come from the same space, and what a task type does to the numbers.

An embedding is meaning as numbers. Give `text-embedding-005` a chunk and it returns 768 floating-point numbers. The numbers have no meaning one at a time; together they place the chunk in a space where texts that mean similar things sit close together. A clause about notice periods and a question about resigning land near each other; a clause about GST returns lands far away. Retrieval is arithmetic on those lists: embed the question the same way, find the chunks whose numbers point in the same direction (a dot product), and hand those chunks to the model that writes the answer.

Compatible means the same space. Numbers are only comparable when they were made the same way: the same model, the same version of it, the same task profile, the same number of dimensions. Change any one of the four and the question's vector and the chunk's vector are two rulers with different marks. The comparison still runs, it still returns a ranked list, and the list is wrong, silently. That is why DocuMind treats the embedding as a declared thing, with a stamp on every row that says which space its numbers belong to, and a function that refuses any row whose stamp does not match.

A task type shapes the vector for its role. The model can be told what a text is for: `RETRIEVAL_DOCUMENT` for a passage being stored, `RETRIEVAL_QUERY` for a question about it, `SEMANTIC_SIMILARITY` for comparing two texts on equal terms. A document vector and a query vector are designed to be compared with each other; two vectors made under the wrong pairing are not. The worker stores every chunk under the document profile and the API embeds every question under the query profile. A row embedded under the query profile (which is what the API gives you when you pass no task type at all) is the legacy mistake the kit's validation exists to catch.

A PIN code for meaning. Two addresses with nearby PIN codes are near each other on the ground, and you can tell without a map: 400001 and 400002 are both in south Mumbai. An embedding is a 768-digit PIN code for meaning; nearby numbers, nearby meaning, no map needed. But a PIN code is only useful inside one postal system. A Mumbai PIN and a London postcode can both be six characters and still say nothing about the distance between them. The stamp on every row says which postal system the code belongs to, and the comparison only ever runs between codes from the same one.

The worker embeds every chunk once, under the document profile, and stores the numbers on the row with a stamp naming the model, its version and the profile. The API embeds every question under the query profile and keeps nothing. The comparison is a dot product between the two, which is only meaningful because both came from the same model in the same version. The chunks nearest the question (teal) are what the answer is written from; the grey ones are the same space, just far away.

#### What you can compute without the model

The dense vector needs the model, and you will call it in step 4. But DocuMind gives every chunk a second, humbler representation you can compute right here: a count of its words, hashed into a fixed space. It is the sparse half of hybrid search (lesson 2.2), and it only measures shared words. Pick two texts. The meter runs the kit's own tokeniser and weighting rule on them and shows how alike they are by words alone; the gap between that number and what a reader knows is exactly what the dense vector is for.

The meter tokenises both texts with the kit's rule (lower-case runs of letters, digits and hyphens), weights a word that appears n times as 1 + 0.5 (n - 1), and reports the cosine between the two weighted word lists: the sparse encoder's similarity, minus the hashing, which only changes ids. Try the third question against LV-07: no shared word says "resign", yet the clause is the answer. That is the case the dense vector solves and the sparse one cannot.

It is not an embedding. It cannot tell that "quit" and "resign" mean the same thing, because it never sees meaning, only spellings. It is here so you can feel the difference between shared words and shared meaning before you pay a fraction of a paisa for the real thing in step 4. The rule it runs is the one in step 8, character for character.

### The words: vector, task type, stamp, batch, carry-over, sparse

Eight words, each with the value it takes on your lane.

Two of these words were already on the row in lesson 1.1: the chunk hash is what carry-over matches on, and the version (the `doc_key`) is what a re-issue creates. This lesson adds the stamp beside them and the numbers under them. Everything else on this page is mechanism.

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

Steps 6 and 7 import the worker's own `indexer.py`, which imports the Vector Search and Gemini SDKs at the top. The setup block installed only the Firestore client; add the other two once. Nothing in this lesson writes to Vector Search.

### One declared embedding, from Terraform to the row

Where the model and its version are written down once, how the same pair reaches the worker and the API, and the three places you can read it back.

#### Definition

DocuMind never lets the embedding be an accident of whichever library default was current on deploy day. The pair is declared once, as two Terraform variables, and the deploy passes the same two values into the environment of the ingest worker and the API. The worker stamps them on every row it writes and on the ledger row of every source it indexes. The API embeds every question with the same model and reports the pair on `/version`, beside the generator and the prompt, because when an answer changes and nobody deployed, the embedding pair is the first thing to compare. Bumping the version is a migration: new rows behind a new stamp, old rows repaired by the backfill, never a silent swap.

#### See it in the UI

Open the deployed UI, go to Documents, and scroll to the Versions table under the upload box. The last column, `embedding`, reads `text-embedding-005@1` on every row. It is not a setting the page knows; it is the pair the worker recorded on that source's ledger row the last time it indexed it. The two columns before it, `reused` and `embedded`, are the carry-over counts you will change in step 7.

#### The code

Four excerpts, one per hop. The Terraform variables are the declaration; the worker reads them from its environment into two module constants; the API reads the same two names into its settings and embeds questions with the first of them.

Notice two things in the worker's constants. The client is regional, `us-central1`, because embedding models are served regionally while Gemini 3.x generation is served only from `global`: the two-client rule from Module 0, seen from the ingestion side. And the task type and the dimension are not environment variables at all; they are fixed in the file, because they are part of what "this embedding" means, not something an operator should be able to change per deploy.

#### Call it: three reads of one pair

All read-only. The first prints the worker's environment, the second asks the API what it is serving, the third reads the pair off the ledger rows the Versions table renders.

You read the same two values from three places that never talk to each other: the worker's environment, the API's process, and the ledger rows in Firestore. They agree because one deploy set them, not because anything checks. The `reused 0, embedded N` on every row says these sources were embedded once, in full, when the corpus was loaded; step 7 is the first time a row on your lane will say anything else.

### The call: 768 numbers under the document task type

The one function that talks to the model, what it insists on before it returns, and a fraction of a paisa to see the task type matter.

#### Definition

`embed_all()` is the whole of the worker's conversation with the embedding model. It sends a batch of texts with two settings, `output_dimensionality: 768` and `task_type: RETRIEVAL_DOCUMENT`, and gets one vector per text back. Then it checks: exactly as many vectors as texts, every one 768 numbers long, every number finite. Any shortfall raises, the request fails whole, and the document's ingest fails with it (the claim is released, the message retried, and a repeat failure ends in the dead-letter queue from lesson 1.1). Nothing partial is ever written, because a row with a bad vector is a row retrieval would rank wrongly for ever.

#### The code

`valid_vector()` is the same test the validation in step 6 uses on rows that are already stored, so a vector is held to one rule on the way in and on the way back out.

#### Do it: embed one clause yourself, both ways

This cell costs money, a very small amount: two calls on a 234-character clause, about a tenth of a paisa. It reads NP-03's text and stored vector off the lane, embeds the same text under the document profile with the worker's exact settings, and compares by cosine. Then it embeds the same text under the query profile and compares again.

The first comparison came back at 1.0, or within rounding of it: the same model, the same profile and the same text give the same numbers, which is why the lane can copy a vector from one version to the next instead of asking again. The second came back lower on the same text, because the query profile shapes the numbers differently. That gap is not an error; it is the model doing what the profile asks. It is also why the task type is part of the stamp: a row embedded under the query profile would sit at that gap from every properly stored neighbour, and rank accordingly.

The cell built its client with `location="us-central1"` because `embed_content` is served regionally. A client on `global` would answer 404 for the embedding model, and a client on `us-central1` answers 404 for Gemini 3.x generation. A notebook that does both needs both, which is the rule Module 0 set and every worker in the kit follows.

### Batches: 250 texts and 15,000 tokens per request

Two ceilings on one request, the estimate the worker uses to stay under them, and the corpus load that found the ceiling the hard way.

#### Definition

The model takes up to 250 texts in one request and up to 20,000 tokens across all of them, and a request over either limit fails whole: not the last text, the whole request. The worker cannot count tokens without a call, so it estimates: three characters per token, and it closes a batch at 250 texts or 15,000 estimated tokens, whichever comes first. The 5,000-token gap is headroom for the estimate being rough. The rule is small, and it was written after the first live corpus load failed every long Act at exactly this point: two-thousand-character windows are about 500 tokens each, and 250 of them are about 125,000.

#### The code

The same rule twice: once in the worker's file and once in the loader the notebooks use, with the loader's docstring carrying the date and the failure. The two copies are held to identical output on the same texts.

#### Try the ceilings

The planner below runs the batching rule on real chunk lengths from your corpus: the handbook's 283 clauses (97 to 599 characters) and the Code on Wages mirror's 65 windows (211 to 2,000). Move the two ceilings and watch the request count change; tick the last box to see what one request per document would have sent.

Each bar is one request: its width is its estimated tokens against the model's 20,000-token ceiling, its label the texts it carries. A red bar is a request the model would refuse whole. The worker's own settings (250 and 15,000) never produce one; the box at the end shows why the first corpus load did.

#### Do it: plan the handbook, Rs 0

The loader's copy of the rule, on the chunks you cut in lesson 1.2. No call is made; a plan is printed.

The handbook's short clauses fill a batch by tokens long before they reach 250 texts, so its four requests carry 85, 78, 78 and 42 texts, each just under the 15,000 estimate. The Act's long windows hit the token ceiling at 28. Neither document ever comes near 250 texts; the text ceiling exists for a corpus of one-line chunks. Every number here came from a loop over string lengths, which is the point of estimating: the plan is free, and the call that follows it cannot fail on size.

### Validate: the stamp, and the function that reads it

What the worker writes beside every vector, the one function that judges a row compatible, and three ways to run it over a whole tenant.

#### Definition

When the worker mirrors a version into Firestore, every row gets the vector and, beside it, the stamp: `embedding_model`, `embedding_version`, `embedding_task_type`, plus `sparse_encoder_version` for the sparse half and `schema_version` for the row shape. One function, `document_embedding_matches()`, reads the stamp and the vector and says yes or no. It is asked in three places: by the carry-over, before a previous row is allowed to lend its vector; by the "already current" check, before a version the other lane seeded is accepted without re-embedding; and by the backfill, which repairs whatever fails. A row with no task type on it fails, by design: such rows were embedded under the API's default query profile before the stamp existed, and they are the reason the stamp exists.

#### The code

#### Read the stamp off one row, Rs 0

#### Validate every current row of a tenant, with the worker's own function

This cell imports the worker's `indexer.py` as deployed and runs its test over every current acme row. The import builds the worker's embedding client (which is why the project must be in the environment) but nothing is embedded.

#### The same check as an operator runs it, and as the tests run it

The backfill target prints a plan when `APPLY=1` is absent: it reads every current row and counts the ones that fail the same function. On a healthy lane the count is zero, and the target is how you would find out otherwise. It needs the index name from Terraform's outputs; if your checkout has no Terraform state, the second form takes the name from the API instead. The unit tests run the worker's file against doubled SDKs, offline, in a fraction of a second.

You ran the worker's own test over a whole tenant three ways and got the same zero each time: from a cell, from the operator's target, and from the plan the repair would follow. The twelve offline tests are what pin the rule: a response with a missing, short, NaN or infinite vector is rejected; a row stamped with the query profile, another version, another model or the wrong length lends nothing to a carry-over; a row without the document stamp is not "already current". Read their names in `commands/tests/test_document_embeddings.py`; each one is a mistake the kit once made or refused to make.

### Carry-over: re-issue the handbook, embed only what changed

How a new version borrows the vectors of every clause that did not change, proved on your lane with a real re-issue and a real undo.

#### Definition

A re-issue is the same object name with new bytes: a new `doc_key`, a fresh set of chunks. Before the worker embeds any of them, `held_vectors()` reads the source's current rows and keeps, by `chunk_hash`, the vector of every row that passes the compatibility test. `plan_carry_over()` then walks the new chunks: a chunk whose hash is held gets the held vector, a chunk whose hash is new is a miss. Only the misses go to `embed_all()`. The handbook's revision 2 changes one number in NP-03 and adds two lines above the first heading, so its plan is 281 reused and 2 embedded, and the log line, the ledger row and the Versions table all say so.

#### The code

Two details carry the weight. A held row must be current and compatible, so a version embedded under another stamp lends nothing even when every hash matches. And the match is on the hash of the whitespace-collapsed text from lesson 1.1, so a clause that only gained a line break is still the same clause.

#### Plan it locally, Rs 0

The worker's planner on the two versions of the handbook, with a stand-in for what `held_vectors()` would lend: one vector per version-1 hash.

#### Do it on the lane: revision 2 over the same name

The upload must keep the object name, `acme/hr_policy_2026.md`, or it is a new source and nothing is held. The loop then waits for the worker's `ingest_ok` line and prints its counts. Cost: two clauses, 453 characters, about a hundredth of a paisa; a Markdown file pays no Document AI.

#### See it in the UI, then read it three more ways

Refresh Documents. The handbook's row in the Versions table now reads `reused 281, embedded 2, retired 283`, with an effective date of 1 October 2026 that the revision declares in its first lines. The first call below is the same row from the API; the second reads the rows themselves and checks the thing the counts claim: an unchanged clause's new row carries the same numbers as its retired predecessor, and a changed clause's does not. The third asks the question the revision changed the answer to.

The worker cut revision 2 into 283 chunks, found 281 of their hashes on the current rows, copied those rows' vectors number for number, and called the model for two texts: one request instead of four, and every unchanged clause keeps exactly the vector it had, so its rank against any question does not move by a hair. The answer changed to 90 days without anyone touching a cache, because the answer cache is keyed to the corpus fingerprint the ledger refreshed. The retired rows are still there, flagged, with their vectors: that is what makes the next block free.

#### Undo it: the same bytes again, and nothing is embedded

Upload version 1 again under the same name. Its `doc_key` is the one the lane retired a minute ago, so the worker does not parse, chunk or embed anything: it flips the retired rows back to current, retires revision 2, and logs `ingest_reactivated` with `embedded 0`. This is the undo from lesson 1.1, seen from the embedding side: nothing was ever deleted, so nothing has to be made again.

Embedding the whole handbook again would cost about 34 paise. Carry-over earns its place three other ways. Determinism: an unchanged clause keeps its exact numbers, so a re-issue cannot shuffle the ranking of clauses nobody touched. Requests: two texts are one request, not four, and on a corpus of a few lakh chunks that is the difference between minutes and a rate-limit ticket. And the undo: a version that was never deleted costs nothing to bring back, which is only true because the vectors travelled with the rows.

### The sparse twin, the notebook twin, and what embedding bills

The second vector every chunk gets, the second copy of the embedding rules, and where the numbers and the rupees go.

#### One sparse space, shared by ingest and query

Hybrid retrieval (lesson 2.2) fuses two ranked lists: one by meaning, from the dense vectors, and one by words, from a sparse vector. The sparse vector is made by a function with no model behind it: split the text into lower-case words, hash each word into one of 220 dimensions, weight it by how often it appears. It is deterministic, dependency-free and shared, so the datapoint the worker writes and the query the API sends live in the same space. The row records only the encoder's version; the values go to Vector Search with the dense vector and the restricts, and Firestore's fallback rung searches dense only.

#### Run it on the lane's text, Rs 0

#### Where the numbers go

#### The notebook twin

The loader the notebook course's Module 4 notebooks use to seed a lane carries the same batching rule (step 5) and the same carry-over by hash, and it stamps the model and the version on every row it writes. It does not stamp the task type; that field is the worker's, and the worker's "already current" check requires it. So a version a notebook seeded is not adopted as-is: the worker treats its rows as an incompatible version, the carry-over lends nothing, and the backfill repairs them. The test `test_notebook_adoption_requires_document_stamp` pins exactly this.

#### What embedding bills, and what it does not

The asymmetry to remember when you design a migration: embedding is cheap per character and expensive per mistake. A model or version bump re-embeds every chunk of every tenant once (a few rupees on this corpus), and until the backfill has finished, any row still on the old stamp is a row the validation excludes rather than one it compares wrongly. That is the whole reason the stamp exists.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

The handbook went to revision 2 and back: two vectors were made, and they now sit on 283 retired rows that the retention policy removes in 30 days. The ledger row for `hr_policy_2026.md` reads `reused 283, embedded 0` until its next re-issue. Two paid calls in step 4 embedded one clause twice and kept nothing. Everything else was read. Lesson 1.4 takes the rows, the datapoints and the ledger you have been reading one at a time and inspects them side by side, as the records one document leaves behind.

Netsetos GenAI on GCP · Module 1 RAG foundation · Lesson 1.3 Create and validate compatible embeddings · v5.0

Next: Lesson 1.4 Write, inspect and verify indexed records.
