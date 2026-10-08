# Lesson 1.6: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_1.6_Reindex_WIX.html`, reviewed at blob `a687d81609b23483c7d84b8575ae6615b57d9f0c`. Learners read that page on the course site; this guide keeps its prose.

A document changes one clause and comes back under the same name. What should happen is exact: the golden questions that cite it are checked before anything is uploaded, the worker keeps the vector of every clause that did not change and embeds only the ones that did, the previous version is retired but kept, and the questions that now have a new answer turn the release gate red until their expected answers move with the document. This lesson does all of that on your lane with the handbook, measures what reuse saves for six different kinds of edit, and puts the document back for nothing.

- What a reindex is

- The words: re-issue, gate, carry-over, reused, retired, required row

- Before you run anything: set up the shell

- The gate: the golden set, scoped to one document

- Measure reuse: six kinds of edit, Rs 0

- Do it: revision 3 of the handbook, on the lane

- Inspect: the ledger row, the claims, the vectors

- The gate goes red, and the two ways back to green

- The claim's four states, what reuse cannot save, and what a reindex costs

- Verify it yourself: the checklist

You will learn what a reindex is (a new version under an old name, released through a gate), why the golden questions that cite a document are checked before it is uploaded and judged live after, and how the carry-over decides, clause by clause, what is embedded again. Then you will prove it on your lane: measure reuse for six kinds of edit with the kit's own functions, re-issue the handbook with one clause changed and watch `reused 281, embedded 2, retired 283` arrive on the log line, read the three records the re-issue left, see the live gate block on the row whose answer moved, and undo the release without embedding anything.

### What a reindex is

A new version under an old name, a gate on both sides of the upload, and a rule that decides what is paid for again.

A reindex is a release. Uploading a document under a name the lane already holds is not a correction; it changes what every question about that document answers from the moment the swap completes. The kit treats it the way it treats a code release: something must be checked before it goes out, and something must be judged after. Before the upload, `make reindex` runs the offline half of the evaluation gate and lists the golden rows that cite the document. After the swap, the live half of the same gate, scoped to those rows, asks the deployed API every one of those questions and blocks if a mandatory row no longer passes. A question whose expected answer was "60 days" does not pass when the document now says 90, and that is the gate doing its job: the golden rows must move with the document, in the same commit.

Reuse is decided per chunk, by hash. Lesson 1.3 showed the mechanism: the worker reads the previous version's current rows, keeps each vector under the hash of its whitespace-collapsed text, and embeds only the chunks whose hash it does not hold. This lesson measures what that rule buys for real edits. A figure changed inside one clause costs one embedding. A paragraph re-wrapped costs nothing, because whitespace is collapsed before hashing. A heading renamed costs one, because the heading is part of the clause's text. A clause inserted costs one, because the others keep their hashes even though their positions change. Two clauses swapped cost nothing. And in a document cut by windows rather than headings, an inserted sentence costs the windows it lands in, not the whole page after it, because the cuts re-align on the next sentence end.

The previous version is retired, never deleted, and the ledger remembers it. Retired rows keep their vectors for thirty days, which is what makes the undo free, and it has a consequence you will meet in step 5: bytes the ledger has already seen are never embedded again. Upload revision 2 today and the worker reactivates its retired rows instead of indexing; to measure reuse you need bytes the lane has not seen, which is why this lesson writes a revision 3.

A price list with a stamp on every line. A shop reprints its price list every month. A careless printer typesets all two hundred lines again and charges for all of them. A careful one keeps a stamp of every line's text and reprints only the lines whose stamp changed: one price moved, one line reset. Re-arranging the pages changes no stamp. Widening the margins changes no stamp. Renaming a heading changes the lines under it, because the heading is printed with them. And before the new list goes on the counter, someone checks the three questions customers always ask against it, and if the answer to one has changed, the answer card on the counter is changed in the same hour. That is a reindex: stamps, a check, a swap.

#### Try an edit, count the embeddings

The meter below holds the first five clauses of the handbook, cut by the kit's own section rule. Edit the text, or press a button for a typical edit, and every clause whose whitespace-collapsed text changed is marked as one to embed again. The count and the paise line are what the worker's carry-over would report for that edit.

Each card is one chunk as the kit would cut it, labelled with its locator. A teal card kept its hash and would borrow its vector from the previous version; an amber card would be embedded again, and its characters are what the paise line prices, at the embedding rate lesson 1.3 quoted. The rule is the one in step 4, character for character.

### The words: re-issue, gate, carry-over, reused, retired, required row

Nine words, each with the value it takes on your lane.

Two of these are lesson 1.3's words in their operational clothes: the carry-over is the mechanism, and the counts are what an operator reads. The gate is new here, and it is what makes a reindex a release rather than an upload.

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

### The gate: the golden set, scoped to one document

What `make reindex` runs before it uploads anything, and the ten rows it says the live gate will judge.

#### Definition

The evaluation gate has two halves. The offline half runs anywhere, without credentials: it reads the golden set and the corpus and checks that the set can still judge a model, that every expected answer could fail, that every anchor a row names resolves to a clause or a document, and that the isolation rows have not been quietly removed. With `--source` it also lists the rows that cite one document, which is the set the live half will send to the API after the reindex. `make reindex` runs that offline half first and refuses to upload when it is red, because a reindex with an unsound gate is a release nobody can judge. A row cites a document when the document's slug appears among its anchors, or when the row names it as its `source`.

#### The code

#### Do it: the offline gate, scoped to the handbook, Rs 0

The gate read all 65 golden rows over the three tenants, found the set sound, and named the ten rows that cite the handbook: nine lookups and one version row, `vr-01`. Two of those ten ask the notice period for a confirmed E3 and expect 60 days. Keep them in mind; they are what step 7 is about. Nothing was uploaded and nothing was asked of the API: this is the half of the gate that runs on every pull request.

### Measure reuse: six kinds of edit, Rs 0

The carry-over planner from lesson 1.3, run on six edits you would actually make, with the number of embeddings each one costs.

#### Definition

The plan the worker makes is a pure function of two texts: the version it holds and the version that arrived. It needs no lane, so you can measure it on your machine for any edit before you upload, with the same chunker and the same planner the worker runs. The table below is what the cell after it prints. Read it as a set of rules about text: whitespace is free, position is free, a heading is part of its clause, a window is cut again around an insertion but re-aligns on the next sentence.

#### The code

#### Do it: the six edits through the worker's planner

Seven plans, no lane, no cost. The two figure changes cost one clause each, the re-wrap and the swap cost nothing, the heading rename costs the clause under it, the inserted clause costs itself and nothing around it, and the sentence added to the Act cost the two windows on that page and none of the pages after. The cheapest edit is the one you would expect to be free, and the rule that makes it free is one line in `chunk_hash()`. Everything on the lane in the next step follows from this table.

### Do it: revision 3 of the handbook, on the lane

New bytes the ledger has not seen, the gate, the upload, and the line with the three counts.

#### Definition

Revision 3 is version 1 with two changes: the notice period for a confirmed E3 goes from 60 to 90 days in NP-03, and a dated line above the first heading declares when it applies. The kit ships a revision 2 that makes the same clause change, and lesson 1.3 used it; but your lane has seen revision 2, its rows are retired within the thirty-day window, and uploading it again would reactivate them: `embedded 0`, nothing to measure. Revision 3 has a different date line, so its bytes are new, its version key is new, and the carry-over runs for real: 281 clauses lent by version 1, two embedded. The cost is two clauses, 453 characters, about a hundredth of a paisa; a Markdown file pays no Document AI.

#### Do it

#### See it in the UI

Refresh Documents: the handbook's row reads `reused 281, embedded 2, retired 283` with an effective date of 1 November 2026. Then ask in Chat: "What is the notice period for a confirmed E3?" The answer is 90 days, cited to NP-03, and the answer cache did not have to be told: the tenant's fingerprint moved with the ledger.

The gate listed ten rows and stayed green, the upload landed, and the worker's line said what the table in step 4 predicted: 283 chunks, 281 vectors borrowed from version 1, two embedded, and version 1's 283 rows retired with thirty days to live. The effective date came from the line you added; the version key from the bytes. One request to the embedding model, where a full index would have made four.

### Inspect: the ledger row, the claims, the vectors

Three records that say the same thing three ways, and the check that the counts are true.

#### Definition

A re-issue leaves the records lesson 1.4 catalogued, with one addition: the ledger now holds more than one claim for the document. The ledger row (`sources/`) names the current version and its counts. The claims (`documents/`) are one per version the lane has ever indexed, and their statuses tell the document's history: version 1 `superseded` by revision 3, version 2 `superseded` since lesson 1.3, revision 3 `indexed` with its counts. And the rows prove the counts: an unchanged clause's new row carries the same 768 numbers as version 1's retired row, because they were copied, not computed; NP-03's does not.

#### Read the three

The ledger row, the claims and the rows agree. Version 1's claim is `superseded` by revision 3 and still carries the mark of its reactivation in lesson 1.3; version 2's claim was superseded by version 1 when you undid it; revision 3 is the one that is `indexed`. LV-01's current row holds exactly the numbers version 1's retired row holds, which is what "reused" means: a copy, not a second call. NP-03's does not, which is what "embedded" means. Three versions of one document, each with its rows, none deleted, one current.

### The gate goes red, and the two ways back to green

The live half of the gate, scoped to the handbook, against a lane where the answer moved; then the release path and the undo path.

#### Definition

The live half sends each row's question to the API as a rostered member, validates the answer's shape, checks its citations name the tenant's own current documents, and looks for the expected figure on its own word boundary. It scores the rows against thresholds, and it treats the required rows separately: a version row or an isolation row that fails blocks the release on its own, whatever the averages say. Against revision 3, the two rows that expect 60 days fail: `lk-06` costs a point, and `vr-01`, a required row, blocks. There are two honest ways back to green. The release path changes the two rows' expected answer to 90 in `evals/golden.jsonl`, in the same commit as the document, and re-runs the gate. The undo path uploads version 1's bytes again, which the worker reactivates for nothing, and the unchanged rows pass. This lesson takes the undo, so your lane and your checkout agree at the end.

#### The code

#### Do it: the live gate, red

Ten questions to the API, each a generation call: a few rupees at most. The target mints two identity tokens, the UI's account as the member and the outsider's for the isolation rows, which is why it takes a moment to start.

#### The undo, then the gate, green

Version 1's bytes again, through the same release command. The offline gate passes, the upload lands, and the worker finds a version it has retired within the window: `ingest_reactivated`, nothing embedded, revision 3 retired in turn. The live gate then passes with the rows as they are.

A real revision 3 ships with its rows. In the same commit as the document, the two rows that cite NP-03's figure change their expectation from `"60"` to `"90"`: `lk-06` and `vr-01` in `evals/golden.jsonl`. The offline gate then still finds the set sound (a 90 could still fail), the live gate passes against the new version, and a later upload of version 1 would turn it red the other way, which is the gate protecting you from an accidental rollback. The demo's README says it in one line: the golden rows move with the policy in the same commit, and the red gate in between is the demo.

The gate did exactly what a release gate is for. Eight of the nine lookups still passed, the two rows that asserted the old figure failed, and one of them was mandatory, so the run was blocked regardless of the averages. Then the undo put version 1 back without a single embedding, and the same ten questions passed. Between the two runs nothing was deleted: revision 3's rows are retired with their vectors, and uploading its bytes again within thirty days would reactivate them just as version 1's were.

### The claim's four states, what reuse cannot save, and what a reindex costs

The record that tells a version's story, the costs the carry-over does not touch, and the rupee line.

#### The claim's four states

A claim is taken in a transaction and ends in one of four states. `processing` while a worker holds it. `indexed` when it finished, with its counts. `failed` when the worker released it with the error, and a failed claim is not a claim but a record of one: the next delivery may take it again, which is what `retakes` is for. `superseded` when a newer version retired its rows; the same bytes again reactivate it, and only when the reactivation is refused (too few rows left, or the window closed) is a superseded claim retaken and the bytes indexed as a fresh version. The three-version history you read in step 6 is these states, one claim per version.

#### What reuse cannot save

The lesson of the table: the carry-over saves model calls, which are the part that could drift, and the part that is billed per character. It does not save writes, and it cannot save the parse. A re-issue of a long PDF is priced by its pages; a re-issue of a Markdown handbook by its changed clauses.

#### What a reindex bills

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

The handbook went to revision 3 and back to version 1. Revision 3's 283 rows are retired with their two fresh vectors and expire with the policy in thirty days; version 1 is current again, reactivated a second time. The golden set in your checkout is unchanged. Lesson 1.7 stays with these records and asks what "current" means when three versions exist: how the swap publishes one, how a person retires a document by hand, and why an event for an older generation is refused.

Netsetos GenAI on GCP · Module 1 RAG foundation · Lesson 1.6 Reindex a changed section and measure embedding reuse · v5.0

Next: Lesson 1.7 Publish versions, retire documents and reject stale events.
