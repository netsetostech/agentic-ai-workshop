# Lesson 8.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_8.3_Size_Ten_Million_WIX.html`, reviewed at blob `1c3caa585c3e732c014c8b0ab3a1df7a2f200cb0`. Learners read that page on the course site; this guide keeps its prose.

Your lane holds the kit's 27 text documents. This lesson asks what the same kit would need for 10,000,000: how many vectors, how many gibibytes of index, how many embedding requests, how many rupees and how many days. Every answer is arithmetic on three kinds of number: the kit's constants, the kit's corpus as the kit's own chunker counts it, and the prices and limits Google publishes. None of them is a guess, and every number on this page is computed from those three when the page is built.

The arithmetic is the easy half. The useful half is the four places where the kit, exactly as it is today, stops working long before ten million: two that grow faster than the corpus, and two that stay fixed while the corpus grows past them. You will read each one in the kit's code, and see what would change it.

- What sizing a RAG system means

- The words: chunk, request, vector, shard, replica, compaction, in flight, fingerprint, walk

- Before you run anything: set up the shell

- The UI: your corpus, counted by the lane

- The kit's numbers: the chunk, the request, the vector, the shard, the row

- Measure the corpus with the kit's own chunker

- REST: the index's own size

- Direct reads: Firestore's counts and the worker's seconds

- Ten million: what breaks first, and what it costs

- Verify it yourself: the checklist

You will learn how one document becomes chunks, requests, vectors and rows, how those multiply to ten million, and which four limits in the kit break first. Then you will measure your own lane, its counts, its index and its seconds per document, and put your numbers into the same arithmetic.

### What sizing a RAG system means

One average document turned into numbers, multiplied, and set beside every price and limit it meets.

Sizing a RAG system means turning one average document into the numbers each part of the system sees, then multiplying by the number of documents. In DocuMind a document becomes chunks, pieces of up to 2,000 characters. Each chunk travels to the embedding model inside a request, comes back as a vector of 768 numbers, goes into the Vector Search index, and is written to Firestore as a row. Count those for an average document, multiply by 10,000,000, and put each total beside the price or the limit that applies to it. That is the whole method.

Three kinds of number go into it, and this page keeps them apart. The kit's constants set the rules: 2,000-character chunks with 200 characters of overlap, at most 250 texts and about 15,000 tokens in one embedding request, 768 numbers a vector, 30 documents worked on at once, a nightly walk with 1,200 seconds to finish, one replica. The corpus sets the averages: the kit's 27 text documents, chunked by the kit's own code, make 2,757 chunks, 102.11 a document. Google's prices and limits, which the kit does not hold, turn totals into rupees and machines: how much one shard of an index holds, what a serving node costs an hour, what 1,000 characters cost to embed. Those were read on 12 October 2026, and step 8 links each one, because they change.

Most of what grows, grows in a straight line. Ten times the documents is ten times the vectors, the gibibytes and the rupees, and a straight line is easy to read once you have one point on it. Sizing is really the search for what does not grow that way. Two things in the kit grow faster than the corpus, because every new document makes them re-read the documents before it. Two others stay the same size while the corpus grows past them: a fixed number of documents in flight, and a fixed number of replicas. Step 8 reads all four in the kit's code.

A wedding caterer in Jaipur, planning for ten thousand guests from a tasting for twenty-seven. The recipe card says what one plate holds: two rotis, a katori of dal, a spoon of pickle. The tasting shows what twenty-seven guests actually ate, second helpings included. The mandi's rate list, dated that morning, turns kilos into rupees. Multiply, and the flour, the dal and the bill all grow in a straight line. Then the caterer looks at the kitchen. It has thirty burners, however many guests come. The head cook insists on recounting every plate already served before sending out the next one. One night-watchman must walk past every table before dawn. And there is one serving counter.

The recipe card is the kit's constants, the tasting is the kit's corpus counted by its own chunker, and the dated rate list is Google's price page. The thirty burners are the worker's 30 documents in flight. The head cook's recount is the corpus fingerprint, which reads every indexed document of a tenant on every ingest. The night-watchman is the nightly walk and its 1,200 seconds, and the serving counter is the index's one replica. At twenty-seven guests none of these matters. At ten thousand, each is the first thing to fail.

#### The calculator: ten million, from the kit's numbers

The calculator is this page's arithmetic, running in your browser. Pick how many documents, what they look like (the kit's own documents of that kind supply the averages), how many tenants they belong to, and the shard size. Each row is one line of the bill or one limit, and a row turns orange where the kit, as it is, breaks. Prices are Google's list prices for Mumbai (asia-south1), where your lane runs, except the embedding model's, which the kit calls in us-central1. They were read on 12 October 2026, at Rs 85 to the dollar.

Not on the calculator: what a question costs to answer, Document AI's and DLP's own prices, the storage Firestore's point-in-time recovery adds, and the sparse half and the filters every vector carries, which Google says take shard space too. So every figure is a floor. The four kinds are averages of the kit's own documents: 17 Acts and Codes, 4 handbooks and policies, 6 short contracts, invoices, reports and transcripts, or all 27 as the corpus mixes them.

Read the default first: 10,000,000 documents shaped like the kit's corpus, all in one tenant, on MEDIUM shards. The straight lines are big but ordinary. 1,021,111,111 vectors make 2,921.4 GiB of index, which takes 147 MEDIUM shards and costs Rs 82.22 lakh a month to serve; embedding the corpus once costs Rs 27.33 lakh. Two rows are orange, and they are the lesson. The fingerprint row says the load would read Firestore 50,000,005,000,000 times, which is Rs 148.75 crore, more than everything else on the page together. The ingest row says that at 30 documents at a time, Document AI alone would take 150.3 days. Now move the tenants to 1,000: the fingerprint's reads fall about a thousandfold, because they grow with the square of each tenant's size, not with the corpus. Then move the documents down until both orange rows turn blue: that is roughly the size the kit, as it is, was built for.

### The words: chunk, request, vector, shard, replica, compaction, in flight, fingerprint, walk

Twelve terms, each with its value on your lane and at ten million documents of the corpus's mix.

Two pairs in this table are easy to confuse, and the lesson keeps them apart. A chunk is text and a vector is numbers: the bill for embedding counts characters, the bill for the index counts vectors. And a shard is a slice of the data while a replica is a copy of all of it: more data means more shards, more questions a second means more replicas, and the kit fixes the second at one.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson asks DocuMind no question: it reads counts, sizes and logs, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. If you ran it, leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible.

### The UI: your corpus, counted by the lane

The chunk counts the lane recorded, document by document, before any arithmetic.

Every size on this page starts from one number: how many chunks a document becomes. Your lane has already counted them, document by document, when the worker ingested the corpus. Read those counts first, in the browser, where an operator would. The UI's address is built from your project number, as the setup block built `API`:

Open it signed in to Google as yourself and choose Documents. The page shows your tenant's ledger under Versions: one row per current version of every document, with its status, its `chunks`, how many of them a re-issue reused or embedded, and when it was indexed. The caption above the table counts the current versions and prints the corpus fingerprint, a hash step 8 comes back to. Your email maps to acme, so these are acme's rows.

Now set the `chunks` column beside the kit's own count of the same documents. The table below is acme's 17 text documents as the kit's chunker counts them, run when this page was built (step 5 runs the same code on your machine):

The five Markdown documents went up as text, and the worker chunks text by exactly the rules the offline count uses, so their rows should match the table digit for digit. The Acts and the compliance handbook went up as PDFs: the worker sent each to Document AI, whose text is not byte for byte the pypdf text the offline count reads, so their counts can differ by a few chunks. Your table also has rows this one does not: the three figures, which the worker describes in words and embeds as one chunk each, and `posh_act_2013`, a scanned Act that only Document AI can read. The town hall is a text row unless you made its video in lesson 7.5; then the video takes its place.

The same rows come from the shell. `make sources` reads the ledger in Firestore directly, as you, the operator, with your Application Default Credentials. The UI asked the API, as you, and the API first checked your email against acme's roster. One table, two callers:

The last line is the ledger's summary for the tenant: its fingerprint and its count of current versions. Then the index itself. `make vector-status` asks gcloud to describe the Vector Search index and its deployment:

`vectorsCount` is every current chunk of all three tenants, text and media, because the worker upserts each chunk it makes current and removes the ones a re-issue retires, and since 13 October 2026 a source withdrawn by hand (`reconcile.py --retire`, lesson 1.8) or retired by the walk has its datapoints removed the same way. One case still runs ahead: a source withdrawn on an older kit, whose datapoints nothing removed, so the count exceeds the current rows by that document's chunks until the index is rebuilt. `shardsCount` is how many slices the index is cut into, and on your lane it is one. Hold both numbers: step 6 reads the same index over REST and asks how full that one shard is.

### The kit's numbers: the chunk, the request, the vector, the shard, the row

Every constant the arithmetic uses, read where the kit sets it.

Five things grow with the corpus: chunks, embedding requests, vectors, shards and Firestore rows. Each has its rule in one place in the kit. Read them in that order.

#### The chunk

2,000 characters with 200 of overlap. The comment's "~500 tokens per chunk" is the usual four characters a token; the kit's embedding batcher, below, counts more cautiously, at 3. The cutting is `_windows()`:

A window runs 2,000 characters, then moves back to the last full stop in its second half if it finds one, and the next window starts 200 characters before that cut. So a long text becomes a little more than its length divided by 2,000, and the characters sent to the model are more than the characters in the document: every overlap is sent twice. Text with `##` headings, which the kit's docstring calls a handbook, is cut by its headings first, one chunk per section, and a PDF's text page by page, so a page break also ends a chunk. Those two rules are why a short page or a short section costs a whole chunk: acme's contract is 927 characters, less than one window, and six chunks, the lines above its first heading and one for each of its five sections.

#### The request

Two ceilings on one request, and the shared copy of the same function says where they come from:

The model takes at most 250 texts and 20,000 tokens in one request; the kit stays under both, at 250 texts and about 15,000 tokens, counting a token as 3 characters. For full chunks, the token ceiling is the one that binds: a full 2,000-character chunk counts as 666 tokens, so one request carries 22 of them, never 250. Across the corpus, with its short chunks, a request carries 29.0 on average. And the requests for one document go one after another:

That loop matters at scale. The worker never sends two requests for the same document at once, so the only parallelism in embedding is the number of documents in flight, which step 8 reads.

#### The vector and the index

768 numbers a vector, and the index stores each in 4 bytes, so Google's data size for your index is its vectors times 3,072 bytes. That one number decides how many shards the index needs. The shard size is a property of the index, and the kit maps each size to the machine that serves it:

On your lane, vector.tf creates a new index SMALL and leaves an existing one the size it has; step 6 reads which. The deployed index, the part that answers queries and bills by the hour, has one replica, as both the minimum and the maximum:

So the serving bill is a simple product: shards, times replicas (one), times the machine's hourly price, times the hours in a month. Ten million documents changes only the first factor.

#### The row

Every chunk the index holds is also a row in Firestore, with the chunk's text, its version flags and its vector. The rows are what the API searches when the index cannot answer:

The row carries the chunk's text and its vector, which Firestore stores at 8 bytes a number, twice the index's 4. And the rows are indexed for vector search eight ways, one per combination of filters the fallback uses:

Six indexes come from that map and two more are declared above it in the same file; every one of them ends in the document's name and the 768-number vector. Firestore bills its storage for the rows and for every index entry, and each of the eight entries holds the whole vector again. By Google's published size rules, the corpus's average chunk is at least 59,092 bytes in Firestore: 8,044 for the row and 51,048 for its index entries, about 19 times the 3,072 bytes the same chunk counts for in Vector Search's data size. Step 8 prices it.

### Measure the corpus with the kit's own chunker

The averages the arithmetic multiplies, from the kit's code on the kit's files, in a second, with no network.

The cell below loads every text document of the three tenants with `shared/documind_corpus.py`, the loader, chunker and batcher the notebooks share. They apply the worker's two rules, 2,000 characters with 200 of overlap and a section per `##` heading, and the worker's two ceilings on a request. It counts, by document type, the characters, the chunks, the characters sent and the requests, then multiplies by 10,000,000. It reads only files in your clone of the kit: nothing on the lane, nothing billed.

Read the table from the bottom. 27 documents make 2,757 chunks and 95 requests, and the 3,471,913 characters sent are more than the 3,264,552 in the documents, because every overlap travels twice. The 17 statutes dominate: 2,067 of the 2,757 chunks. A contract is a few chunks and a Code is hundreds, so the average, 102.11 chunks a document, is a property of this mix, not of documents in general. That is why the calculator in step 1 offers four kinds: the statutes alone average 121.6 chunks, the handbooks 166.5, the short documents 4.0. Before you size a real corpus, run this measurement on a sample of it; the kind of document moves the answer more than anything else on this page.

The last four lines are the straight lines at 10,000,000: 1,021,111,111 vectors, 35,185,185 requests, 2,921.4 GiB of dense index, and Rs 27.33 lakh to embed it once at the online price. Lesson 8.2 changes the chunker and re-embeds; at ten million documents, every such change pays that last line again.

### REST: the index's own size

The index's vectors, shards and shard size, and the deployment's machine and replicas, read from the Vertex AI API.

`make vector-status` printed the fields gcloud was asked for. The API holds more: the index's shard size, its dimensions, and the deployed index's machine and replica range. The cell reads both with two GETs, then does the one sum that matters for sizing: how much of one shard your vectors fill.

Three things to read. The first line is the index as Vertex AI keeps it: its vector count should equal the datapoints `make vector-status` printed, and its shard size is the one it was created with; vector.tf creates a new index SMALL and leaves an existing one the size it has. The second line is the sum: your vectors times 3,072 bytes, as a share of one shard. It is a tiny fraction, which is the point: your lane's index is nowhere near a limit. The last line is the deployment: the machine the shard size names, and replicas from 1 to 1.

Now turn the sum around. By its dense vectors alone, one SMALL shard holds 6,845 documents of the corpus's mix, one MEDIUM shard 68,459, and one LARGE shard 171,149. Ten million documents need 1,461, 147 or 59 of them. Google's own formula for the count is the data size divided by the shard size, and its pricing page warns that "Dataset size and restricts (filtering) affect shard count". The kit's datapoints carry a sparse vector and three filters (tenant, kind and document type) beside the dense one, so the real count can only be higher.

### Direct reads: Firestore's counts and the worker's seconds

The rows the Firestore floor multiplies, and the one number no constant gives you: how long a document takes.

Two reads finish the measurement. The first counts rows in Firestore without fetching them: a `count()` query returns one number instead of the rows it matched.

`chunk rows` counts every version a tenant still holds: the current rows, and the rows a re-issue retired, which stay until their `expire_at` passes. `current` is what the index serves; added across the three tenants, it should match the index's vector count from steps 3 and 6. `indexed sources` is how many rows the fingerprint reads on every ingest to that tenant, which step 8 comes back to. Multiply your chunk rows by 59,092 bytes and you have your lane's Firestore floor for the chunks; for the 2,757 text chunks alone it is 155 MiB. At ten million documents it is 54.9 TiB.

The second read is the calibration. Cloud Run logs every delivery Pub/Sub made to the worker, with its HTTP status and how long it took, so the median of those times is your lane's seconds per document. The cell saves the last month of deliveries, then counts them by status:

Each line is one HTTP status. A `2xx` is a delivery the worker took and finished. A `429`, if you see one, is Cloud Run turning a delivery away because no instance was free; Pub/Sub tries again later, and step 8 reads what that does at scale. Anything in the 500s is a delivery that failed and will be retried. The median of the taken deliveries mixes long PDFs with short text files, and with re-deliveries that found the document already current, so treat it as this corpus's rough figure, not a constant. The last line multiplies it by 10,000,000 and divides by the 30 documents the worker takes at once. If the cell prints nothing, your lane's ingest is older than the log keeps; the calculator's ingest row still holds: 3.86 days for every second a document takes.

### Ten million: what breaks first, and what it costs

The straight lines priced, then the four limits read in the kit's code, then what would change each one.

#### The straight lines, priced

First the index, by shard size. The machine and its hourly price are Google's for Mumbai, the shard sizes are Google's documented sizes, and the count is the data size divided by the shard size, rounded up, with the kit's one replica on each:

Bigger shards are cheaper per gibibyte at this size: LARGE serves the same 2,921.4 GiB for Rs 44.52 lakh a month, against Rs 82.22 lakh on MEDIUM and Rs 1.02 crore on SMALL. Every line multiplies by the replica count, which the kit holds at one. Then everything else, for the same 10,000,000 documents of the corpus's mix, from the embedding price list, Vector Search's and Firestore's, with Firestore's bytes counted by its published size rules:

Three things stand out. Embedding is a one-off, and a batch job would pay Rs 21.86 lakh for it instead of Rs 27.33 lakh. Compaction is not a one-off: Google's page says "If the oldest uncompacted data is five days old, compaction is always triggered", billed as a rebuild of the whole index, so an index that takes updates every day is rebuilt at least every five days, six times in a 30-day month: Rs 44.70 lakh. And the fingerprint line is larger than all the others put together. That one is not a pricing problem. It is the first of the four limits.

#### 1. The fingerprint reads everything, on every ingest

After every successful ingest, the worker records the document in the ledger, then recomputes the tenant's fingerprint:

`corpus_fingerprint()` streams every indexed source row of the tenant to hash their keys. The ledger row is written first, so the ingest of a tenant's k-th document reads k rows, and loading N documents into one tenant reads 1 + 2 + ... + N rows, which is N(N + 1)/2. That is the curve that grows faster than the corpus: double the documents and the reads go up four times. At 10,000,000 documents in one tenant it is 50,000,005,000,000 reads, Rs 148.75 crore at Firestore's Mumbai price of $0.035 per 100,000 reads. Time breaks it as well: the last ingest has to stream 10,000,000 rows inside its 600-second request, 16,667 rows a second.

It overtakes the cost of embedding early. For the corpus's mix, embedding one document costs about as much as 9,185 Firestore reads, so once a tenant holds more than 9,185 documents, each new one costs more to fingerprint than to embed. For the statutes the crossing is at 12,793 documents; for short documents, which are cheap to embed, it is at 70. Spreading the same documents over more tenants flattens the curve, because each tenant's sum starts again from one, and the calculator's tenants control shows by how much.

#### 2. The nightly walk must finish in 1,200 seconds

The reconcile job is the backstop for every event the worker missed. It is off unless you turn it on, and when it runs, it runs as one task, with no retry and a 1,200-second limit:

Before it decides anything, it loads three complete lists: every object in the uploads bucket, every `sources` row and every `documents` row:

At 10,000,000 documents that is 30,000,000 objects and rows, listed and held in one task's memory within 1,200 seconds: 25,000 a second, before the first comparison. The reads are cheap, Rs 595 a night. The limit is the single task and the fixed time. When the time runs out, the task is stopped, the job does not retry, no drift number is printed, and the kit's Nightly reconcile failed alert pages. This limit grows in a straight line, but against a ceiling that does not move.

#### 3. Thirty documents in flight

The worker takes one document per instance and runs at most 30 instances:

So every second one document spends in the worker adds 10,000,000 ÷ 30 seconds to a ten-million-document load: 3.86 days. Your median from step 7 multiplies that. The kit itself states one floor for it, Document AI's pace on a PDF:

At roughly a second a page, and 39.0 PDF pages in the corpus's average document, Document AI alone keeps a ten-million-document load running for 150.3 days. Then there is what happens to the documents that wait. Pub/Sub delivers each upload's event at once; an event the worker cannot take is turned away and tried again, and the subscription counts every try:

The comment is the kit's own record that a refusal counts: the first live load sent a document to the dead-letter topic on five refusals, which is why the limit is now twelve. Twelve deliveries span at most eleven backoffs of at most 600 seconds: 110 minutes in all. Upload ten million documents at once and the last one waits 3,607.7 hours for Document AI time alone. Any document refused twelve times in those hours goes to the dead-letter topic, which lesson 8.1 reads, instead of the index. The limit was sized for thirty objects.

#### 4. One replica

Step 4's excerpt fixes the deployed index at one replica, as both the minimum and the maximum. Replicas are what carry more questions a second. Google's sizing example on its pricing page, priced in Iowa, serves 20 million vectors of 256 dimensions at 1,000 queries a second on one e2-standard-16 node, and at 3,000 on three. The kit's index cannot add a second node when traffic grows. One replica also means no spare: a node that restarts leaves its shard unserved until it is back, and at 147 MEDIUM shards there are 147 such nodes.

#### What the kit would change

Three of the four are not in the kit today, and the fourth is there only in part. Each adds machinery a 27-document lane does not need, and each is now a decision you can price with the calculator. Lesson 8.4 does that for a whole design: a documentation platform that keeps itself up to date, costed at three scales from the same arithmetic.

### Verify it yourself: the checklist

Seven checks, each one step above, each with what a pass looks like on your lane.

Nothing. Every command on this page reads: the ledger and Firestore's counts, two describes and two GETs on the Vertex AI API, one Cloud Logging read, and the kit's own code on the kit's own files. The one file written is `~/ingest-requests.json` in your home directory; delete it when you are done. If you pinned acme to the kit's index in the setup section, put the pin back. The lane still bills its standing cost for every hour it is up, as lesson 0.4 priced it.

Netsetos GenAI on GCP · Module 8 Ingestion practical · Lesson 8.3 Size RAG for ten million documents · v5.0

Next: Lesson 8.4 System design: a self-updating documentation platform.
