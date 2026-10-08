# Lesson 1.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_1.1_Contracts_WIX.html`, reviewed at blob `77b8143fc03414b24b415247dcdb9fa88ec56b1b`. Learners read that page on the course site; this guide keeps its prose.

Your DocuMind is deployed. The sidebar says Tenant: acme, the Documents page lists your documents with a chunk count each, and an answer in Chat cites a page. Each of those is a contract: an agreed shape of data that the ingest worker writes and every other part of the system trusts. This lesson starts with what ingestion is, names the four contracts, and then proves each one on your own lane - in the UI, in the function that enforces it, in a REST call you make, and in the Firestore row you read.

- What ingestion is

- The idea in plain words: four names, one document

- Before you run anything: set up the shell

- Tenant: something you are, never something you send

- Source: the object path is the document's identity

- Version: the bytes decide, and the same file in two tenants proves it

- Page and section: where inside the document

- Chunk: the unit a question can find

- Why it is built this way: the failures behind each rule

- Verify it yourself: the checklist

You will learn the four names every document carries inside DocuMind - its tenant, its source, its version, and its chunks with their page or section - and prove each one on your own lane with a UI action, a REST call and a Firestore read. By the end you can read any row or log line the ingest worker writes and say exactly what it means.

### What ingestion is

The part of DocuMind that turns a file someone uploads into rows a question can find - and why it deserves a whole module.

A language model cannot read a bucket. When you ask DocuMind "What is the notice period?", something has to have already opened the handbook, cut it into pieces small enough to compare with a question, turned each piece into numbers a search index understands, and written every piece down with its owner and its address. That something is ingestion: everything that happens between "a person uploads a file" and "a question can find a sentence in it".

Done carelessly, ingestion is where systems quietly go wrong. The same file gets indexed twice and the answer cites both copies. A corrected policy is indexed beside the old one and the answer picks whichever the ranker liked. One customer's document turns up in another customer's answer. A citation says "[Source 3]" and nobody can find the page. DocuMind avoids each of those with a rule about the shape of the data - a contract - and this lesson is about the four contracts that name a document. Module 1 follows a document from the bucket to a searchable row; Module 1 follows what happens when that document changes.

A courier hub's inward register. A parcel arrives at the hub (the upload). The clerk logs the sender's account and the waybill number (the tenant and the source). The parcel gets one consignment number that never changes, even if the same customer sends an identical parcel tomorrow, which gets a different one (the version). The contents are itemised line by line so any one item can be found later (the chunks). Each item is given a shelf coordinate (the vector). And all of it goes into the register, where the rest of the hub reads it (the rows). Nobody downstream re-opens the parcel; they trust the register.

#### The journey of one document, stage by stage

Step through the six stages below. Each stage lights up on the diagram and shows which of the four names is minted there, and the value it takes for the ACME handbook on your lane.

Stages 3 and 6 are this lesson; stage 4 is lesson 1.2, stage 5 is 1.3, and the writing in stage 6 is 1.4. Nothing here is drawn from memory: every value is one you will read back from your own lane below.

#### The services behind the stages

Those six stages run on Google Cloud services, and the diagram names each one. The bucket announces every upload to a Pub/Sub topic. A push subscription hands the message to the ingest worker on Cloud Run, retries it when the worker fails, and after twelve failures parks it on a dead-letter topic for a person to read. Inside the worker the stages run in order: the claim in Firestore, the reading (Document AI or Gemini), the cut, the Cloud DLP scan, the embeddings from Vertex AI, and the write. Firestore stays the source of truth. The Vector Search index, the BigQuery table and, where a tenant allows it, the RAG Engine and Vertex AI Search copies are all built from its rows.

Names are the kit's own: the topic, subscription and dead-letter topic from terraform/eventarc.tf, the index from vector.tf, the worker's steps from services/ingest/main.py. Lesson 1.4 follows the write itself, record by record.

The code that does each stage is a few hundred lines and it changes. The names do not. Retrieval (Module 2), caching (Module 6), the agents (Modules 5 and 10) and the evaluation gate (Module 4) all read these rows and trust these names. Learn the names first, and every later module is a reader of something you already understand.

### The idea in plain words: four names, one document

What a contract is here, and the four names a document carries from the upload bucket to a citation.

A contract, in this system, is a rule about the shape of a piece of data: which fields it has, where each value comes from, and who is allowed to set it. The ingest worker writes rows under these rules; the API, the chat service, the MCP server and the UI read those rows and trust the rules held. When two parts of a system agree on a shape, you can test one part without the other. That is the whole reason the contracts exist.

Every document that enters DocuMind carries four names, and they answer four different questions:

A university library. The tenant is the department whose shelf you may open: your library card decides, not what you write on the request slip. The source is the book's catalogue number: the same number covers every edition. The version is the edition: the 2019 printing and the 2020 printing are different objects. The page is where you open it. The chunk is the paragraph you quote - and the quote needs the edition and the page to be checkable later.

Hold that picture. Every rule below is one of those five ideas written down precisely enough for a computer to enforce.

#### The journey these names travel

Steps 2 to 5 are the next three lessons in detail. This lesson is about the names themselves, and it checks each one against your lane.

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

### Tenant: something you are, never something you send

Where the sidebar's "Tenant: acme" comes from, the Firestore roster behind it, and what happens to a caller who is not on it.

#### Definition

The tenant is the company whose documents you may see. On the way in, the worker takes it from the first folder of the object path and never from anything a client typed. On the way out, the API takes it from your verified identity and a roster in Firestore, never from a header or a request field. A tenant id that arrives in a request body is treated as a claim to be checked, not a fact.

#### See it in the UI

If your email were on no roster, the Chat and Documents pages would stop with "Your account is not a member of any DocuMind tenant." That is the contract failing safely.

#### The function that enforces it

The UI cannot import the kit's shared code (its image copies only its own folder), so it does the reverse lookup by hand: one collection-group query over every `members` sub-collection, filtered on the `email` field. The parent of the parent of the hit is the tenant.

On the ingest side the tenant is derived from the path, and two things are refused before a byte is downloaded: a path that tries to climb out of its folder, and an object that has no tenant folder at all.

And the roster itself is written by one function, called by `make roster`. A member is a document keyed by the lower-cased email, carrying the email again as a field so the reverse lookup above can filter on it.

#### Call it: the roster from the shell, and two REST calls

First, see how a tenant is created and a member added on your lane. `make roster` adds every address in `MEMBERS` to `TENANT`, then puts the UI's and the MCP server's accounts on all three golden tenants. Run it with your own address - `$ME`, the account gcloud is signed in as - once; a second run is harmless, it sets the same document again.

Now the same question through the API three times. As the UI's account, which is on acme's roster, a query for acme is answered. As the outsider account - a fixture account that IAM admits into the service but no roster lists - the same request gets through Cloud Run's door and is then refused by the roster. With no token at all, Cloud Run's door refuses it before the API ever runs. Both refusals are 403s, so print the body too: the roster's refusal is a one-line JSON from the API, the door's is Cloud Run's HTML page. That difference is the tenant contract at work: the second caller got in, and was still told no.

The two lines that say `WARNING: This command is using service account impersonation` come from gcloud each time a token is minted. They are expected, not errors.

#### Read it in Firestore

Three reads, in a Python cell. The first lists acme's roster. The second is the UI's reverse lookup, run by you. The third is the tenant's settings document - the `data_region: any` the Documents page caption showed you.

You saw the tenant contract from all four sides. The UI derived `acme` from your email with one query. The worker's validator refuses an object outside a tenant folder. The API let a roster member through, refused the outsider with its own JSON 403, and never even ran for the caller with no token, whom Cloud Run turned away with an HTML 403. And the roster is three plain documents you can list. Nowhere did a client get to say which tenant it was.

There is one Firestore database, one Vector Search index and one API for every tenant. Isolation is not a separate database per customer; it is the tenant name stamped on every row (`tenant_id`), inside every chunk id (`acme:...`), on every Vector Search datapoint as a restrict, in the chat service's thread id, and checked against the roster on every request by every surface. A tenant's settings (`tenant_settings/acme`) pin its data residency and, later in the course, its retrieval and model backends without a redeploy. The rest of this lesson shows that stamp on each row you read.

### Source: the object path is the document's identity

The Versions table on the Documents page, the ledger row behind each line, and the API call that serves it.

#### Definition

The source is the document as a thing that lasts across versions: `acme/hr_policy_2026.md` today, the same path when a corrected handbook is uploaded under the same name next month. It is simply the object path in the uploads bucket, tenant folder included. Firestore document ids cannot contain a slash, so the ledger keys the source as `acme~hr_policy_2026.md`. The ledger row for a source says which version is current, when it was indexed, and what the last ingest cost in chunks embedded and reused.

#### See it in the UI

Open Documents. The caption and the table are the ledger for your tenant, served by the API. Three rows from a real lane, trimmed:

Read the columns as the contract. document is the source, tenant folder first. status is the ledger's word for "this version is live". chunks is how many pieces the current version became. reused is zero on every row because each document has been ingested once; the day a re-issue arrives, that number is what you paid nothing for (Module 1). embedding names the model the current version's vectors were made with (lesson 1.3). The caption's corpus fingerprint is a hash of all current version keys for the tenant: it changes on every ingest, and the caches read it (Module 6).

#### The function that enforces it

The row itself is written once per successful ingest by `record_source()`. Every column you saw in the UI is a field here:

#### Call it: the bucket, then the API

The source lives in two places that must agree: the object in the bucket, and the ledger row. Cloud Storage numbers every rewrite of an object with a generation; the ledger records the generation it indexed. List the tenant's folder, describe one object, then ask the API for the ledger.

Two things to check by eye: the `generation` the API returns is the one the bucket reports for that object, and every `name` starts with `acme/`. If a generation ever differs, the bucket holds a newer object than the ledger knows, and Module 1's reconcile is the tool that closes the gap.

#### Read it in Firestore

The Versions table, the API's `/v1/sources` and the `sources` collection are the same eighteen rows seen three ways. The UI shows what the API serves; the API serves what the worker recorded; the worker recorded the generation the bucket assigned. The source contract is that chain, and you have now read every link of it.

### Version: the bytes decide, and the same file in two tenants proves it

Upload one small file to acme through the UI and to zeta from the shell, then watch the worker give it one SHA-256 and two keys.

#### Definition

A version is the content, not the upload. The worker reads the bytes, computes their SHA-256, and names the version `doc_key = tenant_sha256`. Upload the same file twice and the second upload finds the same key already claimed and is acknowledged as a duplicate. Change one character and the key changes. Put the same file under two tenants and you get two keys that share the hash and differ in the prefix - two versions, two sets of rows, one identical text.

#### Do it: one file, two tenants

In the UI, as an acme member: Documents, then Upload, then choose `evals/demo/gratuity_amendment_2026.md` from your kit folder (`$DEMO_ROOT` on the operator machine), then Index documents. The page reports the object it wrote and the generation the bucket assigned. Click Refresh indexing status after a few seconds until the new row appears in Versions.

The UI wrote the object under your tenant's folder as its own service account; it never touched Firestore. The worker did the rest. "Upload complete" is not "indexed" - the page says so itself.

From the shell, the same bytes to zeta. There is no UI session for zeta here, so the copy goes straight to the bucket, which is exactly what the UI does behind its Upload button.

The hash your shell computed is the suffix of both keys. Compute it on the exact bytes you uploaded: a Windows checkout that rewrites line endings produces a different file, and therefore a different hash, from the one Colab or Cloud Shell sees.

#### Read it in Firestore

The per-version claim lives in `documents/{doc_key}`. Build both keys from the local hash and read both claims. They differ in exactly one field.

One file became two versions because a version is tenant plus content. The worker never asked either upload for a name or a tenant: it took the tenant from the folder and the version from the bytes. Upload the acme copy again and nothing new is written - the worker logs `ingest_duplicate` and acknowledges the message. That behaviour, and what happens when the bytes change, is Module 1.

### Page and section: where inside the document

The locator on every chunk, the page on every citation, and the two ways the chunker decides where a chunk begins.

#### Definition

A locator says where a chunk sits inside its document, in words a reader can follow. The chunker has two rules. A document with `##` headings - the handbooks, the contracts - becomes one chunk per clause, and the locator is the clause code: `NP-03`, `PB-02`. Text before the first heading is `preamble`. A document without headings - every PDF Act, plain text - becomes windows of 2,000 characters with 200 characters of overlap, cut page by page so no window crosses a page break, and the locator is page and window, counted from zero: `p7-0` is the first window on page 7 and `p7-1` the second, with `page_start = 7` on the row. A handbook chunk has no page, so its `page_start` is `None`. The same locator appears on the citation the reader sees.

#### See it in the UI

The pill is the chunk; the line under it is the source and its locator. For a PDF the page comes from `page_start`; for a handbook the clause comes from `locator`. Figures and video clips render as `[Fig 3, p.12]` and `[Clip 2, 03:20]` in Module 7.

#### The function that enforces it

The chunker computes `locator`, `page_start` and `section`; the writer stamps them on the row with everything else. Lesson 1.2 reads the chunker; here is the part of the row that carries the answer to "where":

#### Call it: a question, and the page on each citation

A handbook chunk carries no page, so `page` is `None` and the clause code is on the row's `locator`. Ask a question the Code on Wages answers and the citations carry page numbers instead. Try it: "What does the Code on Wages say about the payment of wages?"

#### Read it in Firestore

Two documents, two kinds of locator, one row shape. The handbook's chunks are clauses and say so; the Act's chunks are page windows and carry the page. The citation the UI renders is built from those two fields, which is why a reader can open the source at the right place. The counts you printed are the same numbers the Versions table shows, because they are the same rows.

### Chunk: the unit a question can find

Two identities on every chunk - the id that names a version and a position, and the hash that names the text - and the filters a caller may and may not send.

#### Definition

Then acme is still pinned to RAG Engine. The managed store returns the text of a version and the version's key, and the API mints a temporary id from the text's hash because the store does not keep the kit's chunk ids, locators or pages. Run the `make tenant-backend ... RETRIEVAL_BACKEND=vector` line from the setup section and ask again: the ids become `acme:497809ff...#1`, the form this step is about.

A chunk row has two identities because two different things need to be stable. The id, `acme:497809ff...#7`, names the tenant, the version and the position; it is what a citation points at and what the golden set asserts on, so it must not change once written. The chunk_hash is the SHA-256 of the chunk's text with its whitespace collapsed; it names the text, so the same clause in two versions - or two tenants - has the same hash even when its id differs. Module 1 uses that to reuse vectors across versions. A third field, `current`, says whether the row is live; every reader filters on it.

The same stamps go onto the Vector Search datapoint as restricts, so the dense search, the hybrid search and the Firestore fallback all filter on the same four predicates. The tenant is one of them; a caller cannot widen it.

#### Call it: a filter the contract allows, one that finds nothing, and one it refuses

The API lets a caller narrow a search by `kind` or `doc_type`, because both are stamps on every row. It refuses any other key with a 400 that names the allowed ones - including `tenant_id` and `current`, which a caller might try to use as a filter and which are never theirs to set. One honest detail first: the worker stamps `kind` itself (`text`, or `figure` and `segment` for media), but it does not classify text documents, so every PDF and Markdown file it ingests carries `doc_type: unknown`. A `doc_type: policy` filter is allowed, and on your lane it matches nothing, so the API refuses to answer for lack of evidence. A filter is only as good as the stamp the writer put on the row.

#### Read it in Firestore: the twin rows from step 5

The file you uploaded to both tenants is the cleanest proof of the two identities. Read its chunk rows on each side and compare: the same number of rows, no id in common, and the same set of hashes.

Same text, two tenants: identical hashes, disjoint ids, and every row stamped with the tenant it belongs to. A question from zeta can never surface acme's row, not because a query remembers to filter, but because the row's id, its `tenant_id` field and its Vector Search restrict all carry the tenant, and the API refuses to let a caller change that filter. And the `doc_type` call showed the other half of the same rule: a filter can only find what a writer stamped, and today the worker stamps no document type on text.

### Why it is built this way: the failures behind each rule

Every contract above replaced a simpler design that broke on a real lane. The dates are from the code's own comments.

#### One more field a document may declare

A document can say when it applies from, and the pipeline never guesses it. Either the first lines carry `effective_from: 2026-10-01` (front matter or a header line), or a PDF nobody can edit carries `_effective_2026-10-01` in its object name. The date rides on the ledger row, on every chunk, and on the citation, so two documents that disagree become a question of dates rather than of which one the ranker preferred. The effective from column in the Versions table is empty on your lane because none of the corpus documents declares one; the re-issued handbook in Module 1 does.

#### The Firestore design these contracts add up to

#### Decode one line

Every ingest ends on one log line, and after this lesson you can read all of it:

`tenant` came from the path. `lane` says the push path handled it (files over 250 pages take the batch lane, Module 1). `doc_key` is the tenant and the hash of the bytes. `generation` is the bucket's version number for that object; the source itself is on the claim and the ledger row, not on this line. `chunks` is how many rows now carry `acme:5b62d236e0c1...#0` to `#2`, and `kinds` says they are text, not figures or clips. `pages` is null because a Markdown file has no pages to count. `effective_from` is null because the file declares no date. `fingerprint` is the tenant's new corpus fingerprint, the one the Documents caption shows. The next three lessons are about `reused`, `embedded` and `retired`.

### Verify it yourself: the checklist

Eight checks, each one command, each with the value that proves the contract held on your lane.

Two new versions: `acme/gratuity_amendment_2026.md` and `zeta/gratuity_amendment_2026.md`, three chunks each (the notification's preamble, then its two sections, whose headings carry no clause code and so get the locators `s1` and `s2`), and a new fingerprint on both tenants' ledgers. Everything else is exactly as Module 0 left it. Lesson 1.2 opens the parser and the chunker that turned those bytes into three rows, and shows why the boundary of a chunk decides what a question can find.

Netsetos GenAI on GCP · Module 1 RAG foundation · Lesson 1.1 Understand source, tenant, page and chunk contracts · v5.0

Next: Lesson 1.2 Parse documents and compare chunk boundaries.
