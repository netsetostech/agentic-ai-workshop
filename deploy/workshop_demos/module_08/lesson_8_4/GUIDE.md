# Lesson 8.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_8.4_Design_Self_Updating_Docs_WIX.html`, reviewed at blob `84d0e937ed8f263a6f0838649ecb9372dcec6dd5`. Learners read that page on the course site; this guide keeps its prose.

Module 1 built the parts one lesson at a time: the event an upload becomes, the reindex that pays only for what changed, the versions that retire instead of being deleted, and the walk that finds a lost event. Lesson 6.3 made the caches follow the ledger, and lesson 8.3 priced the kit at ten million documents. This page puts them together as one system with one job. When a document changes, the answers change with it, nobody rebuilds anything, and nothing stale is served in between. It is a design page, written in the shape of the capstone rubric that lesson 11.8 publishes. Every number on it is computed from the kit when the page is built, and the sections on the first four dimensions each end in a script you can run for Rs 0.

- What a self-updating documentation platform is, and how a design is scored

- The words: source, version, generation, claim, carry-over, swap, retire, withdraw, fingerprint, walk, drift

- Before you run anything: set up the shell

- The UI and the ledger: where a change lands on your lane

- Architecture: the path a change takes, station by station

- Architecture: three designs the kit rejected, and the number that would change each

- Failure modes: what pages, what does not, and what the design does about it

- Cost: standing still, staying fresh, and one change, at 1k, 100k and 10M documents

- Cost at 10×: the fingerprint breaks first

- Evals: a change is a release, and the check that cannot fail

- Next month: what the kit's own operating record moved to the top

- Verify it yourself: the checklist

You will learn how a documentation platform keeps its answers current as its documents change, by tracing one change through every part of the kit it touches, and how such a design is scored on the capstone rubric's five dimensions. Then you will back each answer with a script: the change re-run offline, three rejected designs with their thresholds, the alerts the kit declares and the ones it does not, the cost at 1k, 100k and 10M documents, and the eval rows that move with a document.

### What a self-updating documentation platform is, and how a design is scored

A document changes; the answers follow, every copy follows, and a missed change is found. The kit has every station, and the panel shows what each one does.

A documentation platform answers questions from a company's own documents, and keeping it current is the hard part. A handbook gets a new clause, an Act is amended, a policy is withdrawn. Within minutes the platform should answer from the new text, everywhere it keeps a copy. No person should have to rebuild an index, no reader should ever see two versions or none, and no cache should serve the old answer. When something goes wrong, an event that never arrives, a delivery refused twelve times, a worker cut off halfway, the platform should notice. And a person should be able to put the old version back for nothing.

DocuMind already does most of this, part by part. The bucket publishes an event for every upload. The worker refuses events older than what it has indexed, claims each version once, re-embeds only the chunks that changed, and makes the new version current in one swap. The ledger records what is current, and its fingerprint tells both caches when the corpus moved. A nightly walk compares the bucket with the ledger and repairs the difference. This page is the design those parts add up to, with an honest list of where they stop.

A design is scored the way the capstone is. The capstone rubric, which lesson 11.8 publishes, has eight components that must exist in the learner's fork, each checked PASS or FAIL by `make capstone-check`, and five dimensions the defence scores 0 to 3, 15 points in all, with 9 to pass and no dimension at 0. This page's proof is two of the components: the architecture, naming at least three rejected options and why, and the cost model at three scales, in rupees and dated. The sections below follow the dimensions in order, and each one shows what moves an answer from a 2 to a 3.

A newspaper's live edition. A paper that publishes online keeps every story current. When a reporter files a correction, the desk does not retype the paper: it sets the corrected story beside the page, then swaps it in whole, so no reader ever sees half a correction. The old version goes to the archive, stamped with the hour it was replaced, and stays there thirty days, so an editor who regrets the change can put it back in a minute. The syndication partners get the corrected story too, unless a contract keeps that story in the country. The paper's summaries, written from its stories, carry the edition they were written from, and a summary from an old edition is not reused. A night editor walks the shelves against the index and fixes what the day missed, if the paper has hired one. And some things the paper does not notice on its own: a story pulled from the shelf without a word to the desk, a wire that went quiet, a printer that froze halfway through a page.

The wire is the bucket's notification and its subscription. Setting the story beside the page and swapping it in is the staged swap; the archive is the retired rows and their 30-day window. The syndication partners are the managed stores, and the contract is the tenant's data_region. The edition stamp is the ledger's fingerprint, the summaries are the two caches, and the night editor is the walk, which the kit does not hire by default. The three things nobody notices are this page's failure modes.

#### The ripple panel: one change, fifteen stations

Pick a change and follow it through the stations, in the order the kit runs them. Each station is a part of the kit, named with its file, and says what it did with this change. Then flip a design choice. The nightly walk, the batch job and the answer cache are off on a lane deployed with the defaults, and acme's data_region decides whether its text may leave India. Every line below was produced when this page was built, by running the kit's own functions on a stand-in Firestore: nine changes under 16 settings of the switches.

- 1 · The eventterraform/eventarc.tfOBJECT_FINALIZE for the object's new generation: documind-ingest, then documind-ingest-push, which delivers it to the worker with an OIDC token. One document per instance, 30 at most, 600 s to answer.12 deliveries, then the DLQ

- 2 · Guard and claimidempotency.py: stale_generation, claimThe new generation is newer than the ledger's, so its bytes are fetched by generation. New bytes, a new sha256, a new doc_key: the claim is won in a transaction.claim: processing

- 3 · Parse and chunkmain.py: _parse, _chunkText, so no Document AI. Cut by section: 283 chunks, the preamble and one per ## heading. One DLP scan of all of them before anything is written. Class: unknown, as no registry names the file.283 chunks

- 4 · The carry-overindexer.py: embed_with_carry_over281 vectors reused by chunk_hash; 2 embedded, the preamble and the NP-03 chunks: 453 characters sent to text-embedding-005.Rs 0.0010

- 5 · Stage and swapidempotency.py: swap_versions283 rows written staged and invisible, then one pass: 283 flipped current, version 1's 283 retired (current false, expire_at in 30 days). Nothing deleted.855 writes in all

- 6 · Vector Searchindexer.py: upsert, remove_datapoints283 datapoints upserted under revision 2's ids and version 1's 283 removed. The 281 reused vectors go up again too: a chunk's id names its version.283 up, 283 out

- 7 · The managed storesmanaged.py: Mirrordata_region any, so after_swap() copies revision 2's text into the RAG Engine corpus (us-central1) and the Vertex AI Search data store (global), and deletes version 1 from both.2 upserts, 2 deletes

- 8 · BigQueryindexer.py: mirror_to_bigquery283 rows streamed into rag_data.chunk_source for revision 2. Version 1's 283 stay: the table has no current column, and nothing retires them.566 rows for one document

- 9 · The ledgeridempotency.py: finish, record_sourcedocuments/: revision 2 indexed with chunks 283, reused 281, embedded 2; version 1 superseded, its retired_at stamped. sources/: revision 2's doc_key and generation.the 30-day undo window opens

- 10 · The fingerprintidempotency.py: refresh_fingerprintledger/acme re-hashed from its 21 indexed sources: e8a7aa54... becomes b0cb1bd1..., the value both caches now compare with.21 rows read

- 11 · The context cachecache_manager.py: stale_againstA pack made under e8a7aa54... is stale against the ledger: cache_stale, and answers run uncached until make cache packs again.nothing alerts on cache_stale

- 12 · The answer cachesemantic_cache.py: _aliveSEMANTIC_CACHE ?= off: no answer is stored and none is served.off by default

- 13 · The answerretriever.py, golden.jsonlNP-03 now says 90 days, and prefer_current() drops version 1's rows. lk-06 and vr-01 fail live until they move with the document.60 days becomes 90

- 14 · Trail and pagerterraform/alerts.tfingest_superseded and ingest_ok, counted by documind/ingest_events; embedded and reused land in their two distributions. Nothing pages on a default lane. Where make doc-types pinned the handbook to version 1 (lesson 10.4), revision 2 is unreviewed: its class is unknown, and "A registered document arrived at a version nobody reviewed" pages within 10 minutes.0 pages, or 1 with a registry

- 15 · The nightly walkreconcile.py, reconcile.tfRECONCILE_JOB ?= false: no job is declared, so nothing runs at 23:30 IST. make reconcile from a shell is the walk.off by default

Revision 2 is live after one swap: 2 of 283 chunks embedded and 283 retired for 30 days. The fingerprint moved, so neither cache serves version 1, and nothing paged. BigQuery now holds both versions.

The worker's order is `push()`, then `index_document()`, in `services/ingest/main.py`; the walk's is `reconcile.py`'s. The counts are the handbook's: version 1 is `evals/corpus/acme/hr_policy_2026.md`, and revision 2 is `evals/demo/hr_policy_2026_v2.md`. The fingerprints are those of a lane holding exactly the kit's 21 acme objects, shortened; yours differ if your acme corpus does. Before the page was written, node ran this panel's own script on all 144 settings, and it had to show what the build computed.

It is the kit's rules, not your lane. The stores are stand-ins that record calls instead of making them: no Vector Search, RAG Engine, Vertex AI Search or BigQuery call was made. The times are the kit's settings (600 s to answer, 12 deliveries, a walk at 23:30 IST), not measurements. And a red station is not a bug report. It is a place where a copy or a signal does not follow the ledger, and the design has to answer for each one.

### The words: source, version, generation, claim, carry-over, swap, retire, withdraw, fingerprint, walk, drift

Thirteen rows, each with the value it takes on your lane.

Two of these words carry the design. A version is bytes, not a name: uploading the same file again changes nothing, and a one-character edit is a new version with a new `doc_key`. And the fingerprint names a corpus, not a moment. Put version 1 back and the fingerprint returns to its old value, so everything made under the old corpus is valid again.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson asks DocuMind no question: it reads the ledger, the caches' records and the alert policies, and no read on this page depends on which store answers. The two windows below are on every page; you can skip both here, or pin acme now and put it back at the end if you want the UI's answers to come from the kit's index while you read. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. If you ran it, leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible.

### The UI and the ledger: where a change lands on your lane

The Documents page as yourself, the same ledger through the API as the UI's account, then the three records the caches compare.

A change ends in the ledger, so read the ledger first, where an operator would. The UI's address is built from your project number, as the setup block built `API`:

Open it signed in to Google as yourself and choose Documents. The Versions table is the ledger: one row per source, with its status, its chunks, what its last change cost (reused, embedded, retired), the embedding it was made with, when it landed and where it is held. The caption above it prints the count of current versions, the corpus fingerprint, the last change and the tenant's data_region. Your email maps to acme, so these are acme's rows.

The same rows come from the API. `GET /v1/sources` is the versions view `main.py` serves. The shell calls it as `documind-ui-sa`, the UI's own account, which `make roster` put on all three tenants, so the call could name any of them. The UI asked as you, and only acme was yours. One ledger, two callers:

`any` is acme's data_region, set by `make roster`, and it is why the managed stores hold acme's copies. The handbook row's last three counts are what its last change cost: an undo shows 283 reused and 0 embedded, and a re-issue like revision 2 shows 281 and 2. Then the three records that decide whether a cache may be used. Firestore holds them, and the cell reads each one directly:

`ledger/acme` is what the worker writes after every change. `tenant_caches/acme` exists only if `make cache` packed a context cache, and it is current only while its fingerprint is the ledger's. Answer-cache entries exist only on a revision with `SEMANTIC_CACHE=on`, and only the ones under the current fingerprint can be served. On a lane deployed with the defaults, expect no context cache and no entries: both caches are things a design turns on, and step 4 says why each follows the ledger the way it does.

### Architecture: the path a change takes, station by station

The stations, each the kit's own; why each one is there rather than its obvious alternative; and the re-issue run offline.

#### Definition

The design is the kit's ingestion path with its freshness parts, and nothing new on the path itself. A 2 draws it, as the panel does. It also says why each station is there rather than its alternative, with reasons that belong to this workload:

- A notification into a push subscription, rather than a trigger straight to the worker. The bucket publishes `OBJECT_FINALIZE` into `documind-ingest`, and `documind-ingest-push` delivers each event with an OIDC token minted as the worker's own account. It gives the worker 600 s to answer, retries with backoff from 10 s to 600 s, and after 12 deliveries parks the message on `documind-ingest-dlq`. The retries, the ceiling and the dead-letter queue belong to the subscription, so the design gets them without writing them. The one thing it does not publish is a delete.

- A guard before a claim, rather than trusting the order of delivery. Push delivery is at-least-once and not in order. `stale_generation()` refuses an event older than the ledger's generation before a byte is fetched, and the bytes are fetched by generation, never as whatever the object holds now. Then `claim()` lets exactly one worker process a version, inside a transaction, because duplicates arrive at the same moment, and the claim holds for a lease, so a worker cut off halfway cannot keep it for ever (step 6).

- Sections and a carry-over, rather than re-embedding the document. A handbook is cut one chunk per `##` heading, so a chunk keeps its hash when a paragraph above it changes, and the carry-over reuses every vector whose hash the previous version holds. Revision 2 embeds two chunks of 283.

- A staged swap, rather than writing the new rows live. The new rows land invisible, then one pass flips them current and retires the old. The retriever keeps only the newest version per source, which covers the moment between two batches of a long document. A reader sees one version, never two and never none.

- Retire, rather than delete. A retired row keeps its vector for 30 days, the undo window, and the Firestore TTL policy is the only deleter. Step 5 holds this choice against its threshold.

- A fingerprint the caches compare, rather than caches that are flushed. `refresh_fingerprint()` hashes the tenant's current `doc_key`s after every change. The context cache is attached only while it was packed under the same fingerprint, and the answer cache serves an entry only if it was answered under it (and for the same filters, `top_k` and prompt version, within 24 hours). A change makes every older entry a miss without a scan; an undo makes them valid again.

- A nightly walk, rather than trusting every event. `reconcile.py` compares the bucket's current generations with the ledger and the claims. It retires what is gone, re-ingests what changed by rewriting the object onto itself, and ends on one number, drift. It is the backstop for every event the path missed, and it runs only on a lane that declares it.

#### The code

#### Do it: the re-issue, offline

The cell cuts version 1 and revision 2 of the handbook with `shared/documind_corpus.py`, the notebooks' twin of the worker's chunker, which mints the same chunk texts and hashes. It applies the carry-over's rule: a chunk is reused when its hash is held. Then it cuts the same two texts as whole-document windows, the way the worker cut a handbook before 12 September 2026.

By section, revision 2 costs two chunks and 453 characters. One is the preamble, because revision 2 opens with a new title and an effective date; the other is NP-03, the clause that changed. As whole-document windows, the lines inserted at the top moved every window: zero of 92 reused, 178,706 characters sent. Those are the numbers the kit's own comment records, reproduced. Everything after the carry-over, the swap, the index, the stores, BigQuery, the ledger and the fingerprint, is the panel's stations 5 to 10, and the panel's counts come from the same functions on a stand-in store: 855 Firestore writes for this one edit.

### Architecture: three designs the kit rejected, and the number that would change each

Each one is recorded, with its date, in the kit's own comments; each comes with the threshold that would bring it back.

#### Definition

A list of what was built is a description; a list of what was not built, and why, is a decision record. The rubric's 3 asks for more than a reason: the number at which the decision would flip, stated so that someone could check it. The three below are not invented for this page. Each one is in a kit comment with its date, written when the option was tried or weighed and set aside.

#### The code

The kit records two more, without a date. An earlier draft of `eventarc.tf` declared an Eventarc trigger, which delivered CloudEvents straight to the service, around the subscription's token, its retry ceiling and its DLQ; the worker, which parses a Pub/Sub envelope, answered 400. And `vector.tf` says why the index is `STREAM_UPDATE`: with `BATCH_UPDATE`, an uploaded document is simply absent for hours and nothing reports an error. Neither carries a date, so neither is one of the three, but both are the kit's own reasons.

#### Do it: the three thresholds, from the kit's files

The cell prices the same edit cut both ways at lesson 8.3's embedding price, reads the retention window and its floor from the Makefile and `variables.tf`, and reads the push lane's limits from `eventarc.tf` and the worker's deploy script to compute the rewrite bound.

Each rejection is now a sentence someone can check. For a one-clause edit, whole-document windows cost 394 times as much to embed as sections, and the meter that would say otherwise is already on the lane. The retention window cannot be set to zero, so the only change that brings delete-on-update back is an erasure deadline under a day. And the one-path repair holds until a night's rewrites outgrow the push lane's dead-letter bound; past it, the kit's own batch lane is the second path, already built.

"We retire instead of deleting, because an undo inside 30 days embeds nothing and keeps the trail, for about Rs 0.14 of storage per retired handbook. We would delete on retire only for a takedown that must be gone inside a day, the floor of `retention_days`. And we repair through the push lane until a night's repairs pass 198,000 documents at a second each; past that, they go to the batch lane."

### Failure modes: what pages, what does not, and what the design does about it

Four failures the kit's own scripts reproduce, the policies that catch two of them, and a fifth that no script reproduces.

#### Definition

A 2 documents four failure modes with real symptoms, each reproduced by a script. The 3 is the column after the symptom: what `terraform/` would catch, what it would not, and what the design does about the second group. The kit declares 11 alert policies on a lane deployed with the defaults, and 13 once the nightly walk is declared. Four of the default ones watch the document lifecycle: Ingest failed, Ingest dead-letter queue holds messages, Ingest subscription backlog: oldest message over 30 minutes (13 October 2026) and A registered document arrived at a version nobody reviewed.

So the monitoring catches two of the four: the poison twice, about half an hour in and again at the hour, and the backlog itself. The other two are counted on lines nobody alerts on, or not counted at all. The panel shows the same thing as red stations: the deleted handbook answering on, and the queued PDF that nothing takes.

A fifth, which no kit script reproduces: a claim cut off. `release()` gives a claim back when the pipeline raises. A worker that dies without raising, cut off at the request's 600 s or out of memory, never runs it, and the claim stays `processing`. Until 13 October 2026 `claim()` refused every later delivery and `push()` acked each one as a duplicate: the document was missing while every delivery succeeded, which is the warning `release()`'s own docstring gives, and the walk's nightly reingest was acked as a duplicate too. The design's answer was an age on the claim, and it is the kit's now: a claim holds for a lease counted from its `claimed_at`, 660 s on the push lane (the ack deadline and a minute) and 7,260 s for a claim the batch job took. A delivery inside the lease is nacked with a 409 and comes back; the first one after it takes the claim back in a transaction and indexes the bytes, logged as `ingest_claim_retaken`, which the lifecycle metric counts. With the walk on, the night's rewrite is that delivery. The cut-off itself pages nothing; Ingest subscription backlog: oldest message over 30 minutes pages only if the retries outlast 30 minutes.

#### The code

#### Do it: the policies the kit declares, read from its files

The cell reads every Terraform file, lists the alert policies that watch the document lifecycle with what each one reads and when it exists, and counts the policies that read the main subscription, its oldest unacknowledged age, and `cache_stale`.

#### Do it: the walk on three stuck states

The walk's planner is pure Python. The cell hands it three objects nobody indexed: one whose claim was cut off in `processing`, one zero-byte object, and one PDF the worker queued for the batch lane. Then it asks the claim's lease what the night's rewrite of the first will find.

#### Read it on your lane: the policies that exist

The same list from the Monitoring API: every policy on your lane by name, and whether any of them reads the main subscription or the dead-letter one.

The kit's files and your lane agreed: the lifecycle has four policies on a default lane and two more with the walk, and one of them reads `documind-ingest-push`'s oldest message. The planner showed the stuck state that never clears on its own: a poison object is re-ingested every night and refused every night. The cut-off claim is planned the same way, but its lease ran out hours before the walk, so the rewrite's delivery takes it back; and a queued PDF is not drift at all, so only its `ingest_queued_batch` line counts it. A 3 on this dimension is that list, with the alert, the switch or the fix that closes each gap beside it.

### Cost: standing still, staying fresh, and one change, at 1k, 100k and 10M documents

Three kinds of bill, the edit's parts counted from the kit's own functions, and the month at three scales from lesson 8.3's module.

#### Definition

A self-updating platform pays three kinds of bill. Standing still: the index's serving nodes and Firestore's storage, by the hour, whether anything changes or not. Staying fresh: Vector Search's compaction. An index that takes streamed updates is rebuilt at least every five days while updates keep arriving, at the batch-update price for the whole index, as lesson 8.3 read from Google's page: six rebuilds in a 30-day month. One change: what the panel's edit did, priced. The scales are documents of the kit's corpus mix in one tenant, computed with lesson 8.3's module from the same prices, read on 12 October 2026, at Rs 85 to the dollar.

#### One edit, part by part

The embedding is the smallest line. The carry-over saved the model its work, but a version's chunk ids name the version, so the swap writes every row three times (staged, flipped, retired) and the index takes every datapoint again. An edit costs its changed chunks in the model, and its whole document in Firestore and Vector Search. The kit records the choice: the id stays version and position, so citations and the golden set stay stable, and a chunk's identity across versions rides on `chunk_hash` and the locator.

#### The month, at three scales

Dated 12 October 2026. Every price is lesson 8.3's: Google's list prices for Mumbai (asia-south1) for Vector Search and Firestore, and the online embedding price, read on that date, at Rs 85 to the dollar. The serving line takes the cheapest of the three shard sizes lesson 8.3 prices: the kit declares SMALL for a new lane, and past one SMALL shard a larger size is cheaper. Not priced here: Cloud Run's request time, the DLP scan, Document AI for a PDF, the managed stores' imports and storage, and BigQuery's streaming inserts.

Read the table the rubric's way. At 1k documents the platform is its standing bill, Rs 7,488 a month, and an edit costs Rs 0.17: 43,769 edits a month would match it. At 10M, staying fresh costs as much as standing still, compaction at Rs 44.70 lakh a month beside serving at Rs 44.52 lakh, and one edit costs Rs 297.64, nearly all of it the fingerprint's ten million reads. The edit's own cost does not move with scale. The fingerprint is the line that does.

#### Do it: the cost model as a script

This is component 6's `COST-MODEL.md` as something a reviewer can rerun. It measures the kit's corpus with the kit's own chunker, carries lesson 8.3's prices as dated constants, and uses the edit's counts from this page: its characters, its datapoints, and the Firestore writes and reads the kit's functions made.

The script printed the table's three totals, the embedding once and the edit, scale by scale, from the kit's corpus and dated prices. Its last column is the number a design needs before it promises freshness: how many edits a month cost as much as keeping the platform up. Below it, edits are free in practice. Above it, the next rupee is in the fingerprint's column, which step 8 takes apart.

### Cost at 10×: the fingerprint breaks first

Ten times the bill is arithmetic. What stops being linear on the update path is a read that grows with the tenant, a walk with a fixed clock, and a burst the push lane cannot hold.

#### Definition

The commonest 2 on this dimension scales the bill by ten and stops. For a self-updating platform, ten times the load is ten times the changes, or a tenant ten times larger, and three limits on the update path stop being linear well before the index does. Lesson 8.3 found them in a ten-million-document load; here they are as limits on every change:

So what breaks first at 10×? Take the middle scale and multiply it by ten: a tenant of a million documents. Every change, however small, re-reads the tenant's million ledger rows, 1,667 a second inside one 600-second request, and Rs 29.75 in reads; the walk must list 2,500 objects and rows a second for 1,200 seconds. The fingerprint breaks first, because it is the one cost that grows with the tenant on every change. Past 4,751 documents in a tenant, it already costs more than the rest of a handbook-sized edit together. At the top scale it costs Rs 297.50 a change and must stream 16,667 rows a second. Spreading documents over tenants divides it, which lesson 8.3's calculator shows; an incremental fingerprint ends it, folding each change's `doc_key` into a running value on the ledger row in the same write that records it.

"At ten times our largest tenant, the first limit is the corpus fingerprint: every change reads the tenant's whole ledger inside a 600-second request, a million rows at a million documents. Before a tenant passes 4,751 documents we move to an incremental fingerprint. The second is compaction: at ten million documents, staying fresh costs as much as serving the index."

### Evals: a change is a release, and the check that cannot fail

The gate runs before a document is uploaded, the version row moves with it, and the anchors check never sees a chunk.

#### Definition

The kit treats a document change the way it treats a code change. `make reindex` runs the offline gate before it uploads anything, then `make eval-live SOURCE=` judges the rows that cite the document on a candidate; `deploy/INDEXING.md` calls this "a reindex is a release". The gate is `evals/run_eval.py`: 9 thresholds and 15 required rows over 65 golden rows. Its version row, `vr-01`, is this platform's own test. It asks `lk-06`'s question and forbids the figure only revision 2 holds, so a re-issue that leaves the rows behind turns the gate red, and the rows move with the document in the same commit.

Then the rubric's hardest point: which checks cannot fail. For this platform, the offline anchors check is one. It looks for each `must_retrieve` anchor in the tenant's files, filename and whole text joined, and never in a chunk. No chunker change, no carry-over bug and no lost event can turn it red. What replaced it here is the live gate scoped to the document, whose rows are answered from the real index, and the lifecycle smoke, `make smoke-reindex`, which re-issues a fixture and puts it back. One gap remains: `must_retrieve` recall over the real pool is printed as information, not judged, so a chunker change is judged by the answers it changes, not by the chunks it loses.

#### The code

#### Do it: the gate offline, and what moves with a document

The offline gate judged the golden set itself and passed. The second cell showed what a change of the handbook is judged by: the 10 rows `make eval-live SOURCE=hr_policy_2026.md` sends, and `vr-01`, which is required, so it blocks on its own. Then the vacuous one: the anchors check found no problems, and it would find none after any chunker change, because it never reads a chunk. A 3 names that check and what replaced it.

### Next month: what the kit's own operating record moved to the top

A 3 is an observation from operating, not a plan from before; the kit's dated comments show what one looks like.

#### Definition

The fifth dimension cannot be designed in advance, which is its point: a 3 is a top item nobody planned, found by running the thing. A design page can show only the shape. The kit's comments record exactly this kind of item for the document lifecycle, each one moved to the top because a live run showed something no plan had:

For this platform, a month of operating answers the questions that could reorder its work: the subscription's oldest unacknowledged age in its busiest hour, the share of each edit the carry-over reused, how long a cache ran stale after each change, how many cut-off claims the lease took back (`ingest_claim_retaken`), and the drift each night once the walk is on. A 3 names the one that surprised you, and says what it pushed down the list. The items already known are named in the kit: `deploy/INDEXING.md` lists a full re-embed of the corpus, under the name `reembed`, as not yet built, and lesson 8.3's last table names an incremental fingerprint and a sharded walk.

### Verify it yourself: the checklist

Twelve checks, each one step above, each with what passing looks like.

Nothing. Every cell on this page read the kit's files, your lane's ledger and cache records, or its alert policies: the offline cells call nothing, and the reads in steps 3 and 6 write nothing. The ripple ran on a stand-in. Two of the design's additions are in the kit since 13 October 2026, the alert on the subscription's age and the claim's lease: your lane has them once `make up` applies the policy and the worker is redeployed from this kit. The rest, the walk declared, a delete that retires at once and an incremental fingerprint, are proposals. If you pinned acme to the kit's index in the setup section, put the pin back. Module 9 starts with lesson 9.1, which traces and authorizes the routes through the model gateway.

Netsetos GenAI on GCP · Module 8 Ingestion practical · Lesson 8.4 System design: a self-updating documentation platform · v5.0

Next: Lesson 9.1 Trace and authorize gateway routes.
