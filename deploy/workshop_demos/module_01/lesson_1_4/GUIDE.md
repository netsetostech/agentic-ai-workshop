# Lesson 1.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_1.4_Indexed_Records_WIX.html`, reviewed at blob `25ca420f96d82cacd1aeaffd37bdfde92039ecbe`. Learners read that page on the course site; this guide keeps its prose.

Lessons 1.1 to 1.3 followed one document from bytes to vectors. This lesson is about what it leaves behind: the records in Firestore, in the Vector Search index, in BigQuery and in the audit bucket that say the document is indexed, and the order the worker writes them in so that a reader never sees half a document. You will index a three-chunk note, read every record it created from the store that holds it, check that they agree with each other, and learn which store is the truth when they do not.

- What an indexed record is

- The words: claim, row, datapoint, restrict, mirror, ledger, fingerprint

- Before you run anything: set up the shell

- Write: the order the worker keeps, and a fresh document to watch

- Inspect Firestore: the claim, the rows, the ledger row, the fingerprint

- Inspect Vector Search: the datapoint, its restricts, and a search for itself

- Inspect the mirror and the audit trail

- Verify: the two rungs that read the records

- Repair, expire, and what the records cost

- Verify it yourself: the checklist

You will learn what a document's indexed records are (a claim, its chunk rows, one datapoint per row, one mirror row per chunk, a ledger row and a tenant fingerprint), the order the worker writes them in and why that order is what keeps a reader from ever seeing two versions or none, and how the two read paths use the same predicates over two different stores. Then you will prove it on your lane: index a small note, read back every record it created, search the index for a row by its own vector, and run the kit's own verification commands.

### What an indexed record is

One upload, several registers, and why the order of writing decides what a question can find.

A record is what remains after the log line scrolls away. When the worker finishes a document it logs one line, `ingest_ok`, and that line is gone from the operator's screen in a minute. What stays is a set of records: a claim that says which worker took the version and how it ended, one row per chunk with the text and the vector, one datapoint per row in the search index, one row per chunk in a BigQuery table, one ledger row per document naming its current version, and a fingerprint per tenant that changes whenever any of that changes. Each lives in the store that is best at its job, and each can be read on its own, which is what makes the whole thing verifiable.

The order of writes is the design. No transaction spans Firestore, Vector Search and BigQuery, so the worker cannot make a document appear everywhere at once. What it can do is choose an order in which every intermediate state is safe. New rows land staged, invisible to every reader, and a single pass flips them current and retires the old ones; only then do the datapoints go up and the retired ids come out; only then are the claim, the ledger row and the fingerprint written. A reader that arrives between any two steps finds exactly one version of the document, or the one it had before. That property is what you will step through in the player below, and it is what "indexed" means in DocuMind: not "some rows exist", but "the sequence completed".

Verification is agreement. A record on its own proves little. The claim says three chunks; are there three current rows? The rows hold vectors; does the index hold the same numbers under the same ids? The ledger row names a version; do the rows carry that `doc_key`? When every register agrees, the document is indexed. When they disagree, one of them is the truth and the others are repaired from it, and in DocuMind that truth is the Firestore row: the index is rebuilt from the rows, never the other way around.

A property changes hands. One sale, several registers: the sale deed at the sub-registrar's office, the mutation in the municipal records, the 7/12 extract or property card, the bank's charge on the title. A careful buyer's lawyer does not read one of them and stop; they read all of them and check that every register tells the same story, because a property whose deed and mutation disagree is a dispute waiting to happen. In DocuMind the chunk row is the deed. The datapoint, the mirror row and the ledger must agree with it, and the verification in this lesson is the lawyer's walk from office to office.

#### Watch the worker write

The player steps through the worker's order for two real ingests on your lane: the three-chunk note you will index in step 3, and the handbook re-issue from lesson 1.3. Each card is one store; the highlighted card is the one the step writes, and the amber line says what a reader asking a question at that moment would find.

The order is the one in `services/ingest/main.py`, which you will read in step 3. Two things to watch for: the rows exist for two steps before a reader can see them (staged), and in the re-issue the reader moves from version 1 to version 2 in one step and never sees both. The numbers are the real counts from your lane.

The player starts once the worker has the message. What comes before it - the bucket's notification, the Pub/Sub topic, the push subscription and its dead-letter topic - and every service the worker calls are drawn end to end in lesson 1.1, under "The services behind the stages".

### The words: claim, row, datapoint, restrict, mirror, ledger, fingerprint

Nine words, each with the record it names and where that record lives on your lane.

The lifecycle of these records, what retires them, what deletes them, what brings them back, is the story of lessons 1.5 to 1.8. This lesson reads them as they are written and checks that they agree.

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

The index, the endpoint, the BigQuery table and the audit bucket are named in the environment of the two services that use them. Read them once into the shell; every cell below uses these variables. Both reads are read-only.

Steps 5 and 7 also need the two SDKs lesson 1.3 installed (`google-cloud-aiplatform`, `google-genai`); step 6 uses the `bq` command that ships with the Cloud SDK.

### Write: the order the worker keeps, and a fresh document to watch

The sequence in the worker's own words, the claim that starts it, and a three-chunk note indexed while you count the datapoints.

#### Definition

The worker writes seven records for one version, in a fixed order. The claim first, in a transaction, so that a duplicate delivery from Pub/Sub finds the document taken and does nothing. Then the rows, staged. Then the swap, which flips the staged rows current and retires the previous version's rows in one pass. Then the tier: the new datapoints up, the retired ids out. Then the BigQuery mirror. Then the claim is finished with its counts, the ledger row is written, the fingerprint refreshed, the audit event emitted, and last of all the log line. A failure anywhere gives the claim back with the error on it, so the next delivery can try again and an operator can read why.

#### See it in the UI

On the Documents page the button Refresh indexing status does one thing: it reloads the Versions table from the ledger. An upload confirmation is not an indexed document; the row appearing in that table is, because the ledger row is written after every other record.

#### The code

Read the four comments in the swap block again: staged and invisible, one pass, the tier follows, the retired ids come out. That block is the design; the rest is bookkeeping around it.

#### Do it: index a note, and count the datapoints before and after

The note is the kit's three-clause warehouse memo with one line added: your account and today's date. The line matters. A version is its bytes, and the kit's reindex smoke from Module 0 uploads the unchanged file under another name; if it ever ran on your lane, those bytes are already claimed, and the worker acks the same bytes again as a duplicate and writes nothing. One line of your own makes a new version key. The note is a Markdown file of about 500 characters with no PII: no Document AI, three embeddings, about a hundredth of a paisa. The block reads the index's datapoint count, writes and uploads the note, waits for the worker's line, then waits for the count to move. The index's statistics refresh on their own schedule, so the last wait can take a few minutes.

Two reads tell you what the worker did with an upload. The first lists every ingest event of the last twenty minutes with its verdict: `ingest_duplicate` means the bytes were already claimed on this lane, `ingest_failed` carries the error, and no line at all means the event never reached the worker. The second reads the claim for the unchanged demo bytes; its `gcs_uri` names the object that holds them, which on a lane where the smoke has run is `acme/smoke_note.md`. The claim is per version, not per name: that is the record this whole step is about.

One upload became one claim, three rows, three datapoints, three mirror rows, one ledger row, one fingerprint and one audit event, in that order, and the index's own counter moved by exactly the number of rows. The line the block printed carries the version key and the counts; the next three steps read the records that key names, one store at a time.

### Inspect Firestore: the claim, the rows, the ledger row, the fingerprint

Four records in one database, read by the key you can compute from the file's bytes.

#### Definition

Everything in Firestore hangs off two keys you already know from lesson 1.1. The version key, `doc_key = acme_`, names the claim and stamps every row. The document key, `acme~smoke_note_v1.md`, names the ledger row. Neither is assigned by a database; both are computed, so you can derive them on your laptop from the file and go straight to the records without a search.

#### The code

#### Read all four, Rs 0

Four records, one key, and every count agrees: the claim says three chunks, three rows are current, none is staged or carries an expiry, and the ledger row names the same version and the same bytes you hashed locally. `doc_type` reads `unknown` because the worker does not classify a plain text upload (lesson 1.1 met this); it is the same value the datapoint will carry as a restrict in the next step. The fingerprint is the one line that is about the tenant, not the document: it moved because the set of current versions did.

### Inspect Vector Search: the datapoint, its restricts, and a search for itself

The index as a store of records, not just a search engine: read a datapoint back by id, then ask the index to find a row by its own vector.

#### Definition

A Vector Search index is usually described by what it answers, but it is also a store: one datapoint per id, and the id is the chunk id from Firestore. The worker builds each datapoint from the row (the dense vector, the sparse vector, the four restricts) and streams it up; a retired row's id is removed the same way. Two calls let you inspect the store directly. Reading datapoints by id returns what the index holds for them. Searching with a row's own vector, under the same restricts the API sends, must return that row first with the highest possible score, because nothing is closer to a vector than itself.

#### The code

#### The index and its deployment, as gcloud sees them

Three things exist: the index, the endpoint, and the deployed index that joins them and is the one that costs money per hour. The kit's `make vector-status` runs `commands/vector-status.sh`, which takes the two names from the shell (the variables you exported above) or, failing that, from Terraform's outputs; the two commands below are the same reads by hand.

#### Read one datapoint back, then search for it

The index gave back, under the chunk's own id, the same 768 numbers Firestore holds and the four labels the worker attached, which is the whole agreement between the two stores: same ids, same vectors, same tenant. The search then found the row by its own vector with a dot product of 1.0, the score of a unit vector against itself, and put the note's two other clauses next, because the restricts confined the search to acme's current rows and the note's clauses share more meaning with each other than with an Act. This is the call the API makes for every question, with a question's vector in place of the row's.

### Inspect the mirror and the audit trail

The two records that are written last and read least: the SQL lane's copy of every chunk, and the event that outlives them all.

#### Definition

When the worker's environment names a BigQuery table, every indexed chunk is also streamed there as one row: the text, the page, the heading, the kind, and the PII verdict the worker computed before indexing. Nothing ever updates or deletes those rows; a re-issue appends its chunks beside the old ones, and whoever reads the table joins on the ledger to learn what is current. It is the copy Module 2's SQL lane reads, and the one place a chunk's text can be queried with `WHERE`. Separately, one audit event per upload goes into a retention-locked bucket as a small JSON object. It cannot be edited or removed inside the retention window, which is why it, and not the log line, is the record an auditor is shown.

#### The code

#### Read the mirror rows, then the audit event

The mirror holds the note's three chunks with the heading of each clause and a PII verdict of false, and it holds more rows for acme than Firestore has current rows, because the handbook's revision 2 from lesson 1.3 is still there: retired in Firestore, appended for ever here. The audit event names the version by the same key you computed from the bytes and carries the same counts as the claim. Three stores, three reads, one story.

### Verify: the two rungs that read the records

The API reads the records two ways, with one set of predicates. Run both against the note, then let the kit's own commands run the checks an operator runs.

#### Definition

A question reaches the records through one of two rungs. The first is the index: the question's vector, the tenant restrict, the `current` restrict and any caller filters go to `find_neighbors`, the ids come back with scores, and the rows are fetched from Firestore by id to get their text. The second is Firestore's own vector index on the `chunks` collection, used when the first rung raises or when a tenant is pinned to it: the same tenant, the same `current`, the same filters, as pre-filters on the rows (an equality each, or one `in` for a `doc_type` list). Every chunk that comes back carries `found_by`, so an answer can say which rung served it. The two rungs need different indexes to exist, the Vector Search index and the Firestore composite indexes, and the second one does not degrade without its index; it refuses.

#### The code

#### Do it: the fallback rung, then the API

The first cell runs the Firestore rung's exact query with the note's own vector: itself first, at a cosine distance of zero. The second asks the API a question only the note can answer and prints which rung served it and how many of the pooled chunks came from the index.

#### The operator's checks: two commands, and their tests

The kit ships two read-only commands for exactly this lesson. `verify-vector-index.py` reads Terraform's outputs and asks the API whether the index Terraform declared is the one attached to the endpoint, streaming, 768-dimensional, deployed exactly once; it needs a checkout with Terraform state, and the two `gcloud` reads in step 5 are the same checks by hand. `check-firestore-fallback.py` takes the handbook, proves the ledger row names the bytes in your checkout, and runs the Firestore rung with combined filters in both `current` modes; it imports the API's own modules, so it needs the API's packages in your venv. Both write their evidence under `operator-evidence/`. Their tests run offline in a fraction of a second.

Both rungs found the note. The Firestore rung put the row first at a distance of exactly zero, with the note's other clauses behind it, which is the fallback the chaos drill relies on. The API answered from the index, said so on `retrieval_backend`, and reported that every chunk in its pool came from `find_neighbors`; a zero there while the backend says `vector` is how you would learn that the index was down and Firestore answered instead. The fallback check refused to run until it had proved the handbook's ledger row names the bytes in your checkout, which after lesson 1.3's undo it does. Its NOTE line is the `doc_type: unknown` finding from lesson 1.1, reported by the kit itself.

### Repair, expire, and what the records cost

Which store is the truth when two disagree, the only thing that ever deletes a row, and where the rupees go.

#### The rows rebuild the tier

Firestore holds everything the index holds and more: the text, the vector, the stamps and the flags. So when the index and the rows disagree, the index is rebuilt from the rows, and nothing in the rows is ever derived from the index. `backfill()` reads every current row (of one tenant, or all), rebuilds each datapoint with the row's own vector, re-embeds only a row whose stamp fails the check from lesson 1.3, and checkpoints the repaired vector back on the row with optimistic concurrency so that a concurrent writer is never overwritten. Its plan is the count you saw in 1.3; `APPLY=1` is the repair, and the two states it exists for are a worker deployed before the index existed and an apply that lost its index and succeeded on the second run.

#### Two clocks on a row, and the one deleter

Nothing in the worker calls delete on a chunk row. A staged row that nothing ever swapped carries an `expire_at` one day out; a retired row carries one thirty days out; and a Firestore TTL policy on that field, declared in Terraform, removes the row after it. That is the whole deletion story, and it is why the undo in lesson 1.3 could be free for thirty days and not a minute longer. The second Terraform excerpt is the index the fallback rung needed in step 7: one composite vector index per predicate combination, because Firestore refuses a vector query it has no index for.

#### What the records cost, and what they do not

The asymmetry to remember: the records are cheap, the deployed index is not, and the deployed index holds nothing that Firestore does not. A team that must cut cost undeploys the index and answers from the Firestore rung, slower and with the same records; a team that must cut risk keeps both and verifies that they agree, which is the walk you have just done.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

One new document under acme: `smoke_note_v1.md`, your personalised note, three rows, three datapoints, three mirror rows, one ledger row, one audit event, and a new tenant fingerprint. If the reindex smoke had left the unchanged demo bytes on your lane as `smoke_note.md`, that document is untouched. Everything else was read. Ingestion ends here: a document's path from bytes to records is now something you can follow, count and prove. Lessons 1.5 to 1.8 take the same records through their lifetime, starting with what happens when the write does not go to plan.

Netsetos GenAI on GCP · Module 1 RAG foundation · Lesson 1.4 Write, inspect and verify indexed records · v5.0

Next: Lesson 1.5 Follow upload events, retries, dead-letter handling and the batch lane.
