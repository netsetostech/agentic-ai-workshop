# Lesson 1.7: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_1.7_Versions_WIX.html`, reviewed at blob `3fc7051907aad57df30bf22596ebd56a662a00ac`. Learners read that page on the course site; this guide keeps its prose.

A document on the lane has exactly one current version, and this lesson is about how that stays true. A new version is published by one swap, never by a stream of writes. A version stops being current in one of three ways, each with its own name and its own way back: superseded by a newer one, retired because its object left the bucket, or withdrawn by a person. And an event that arrives late, carrying an older generation of the object, is refused before a byte is downloaded, because acting on it would publish the past. You will read all of it off your lane, replay three events yourself, and withdraw and restore a document by hand.

- What "current" means

- The words: staged, swap, superseded, retired, withdrawn, generation, tombstone

- Before you run anything: set up the shell

- Publish: the swap, and the reader's guard

- Superseded: the retired rows' bookkeeping, and the clock that removes them

- Stale: the generation guard, and three replayed events

- Withdrawn: retire a document by hand, then restore it

- The three states side by side

- The swap window, effective dates, and what a version costs

- Verify it yourself: the checklist

You will learn how a version is published (rows written staged and invisible, then flipped current in one pass while the previous version's rows are flagged, never deleted), the three states a version can leave "current" for and what brings each one back, and why an event for an older generation of an object is acknowledged and ignored. Then you will prove it on your lane: read the handbook's three versions and their flags, replay three events against the worker and watch the guard sort them, withdraw the note from lesson 1.4 by hand, see the tombstone hold against the same bytes, and restore it without embedding anything.

### What "current" means

One version a reader may see, how it becomes that version, the three ways it stops, and the one event that must not change anything.

Current is a flag, and exactly one version of a document carries it. Every chunk row has `current`. The reader filters on it, the search index carries it as a restrict, and the ledger row names the version that holds it. Publishing a version means flipping that flag on its rows and off the previous version's rows, and the worker does it as one pass over the source's rows: the new version's rows go first, so that no reader ever finds none, and the old rows are flagged with a successor, a timestamp and an expiry. For a document of a few hundred chunks that is one Firestore commit; for a longer one it is two, and the reader carries a guard for the moment in between: of two versions that are both current, keep the one whose rows landed last.

Three ways out of current, three names. Superseded: a newer version was published; the old rows keep their vectors for thirty days, so the same bytes again are reactivated rather than re-embedded, which lessons 1.3 and 1.6 used. Retired: the object left the bucket, which the nightly walk of lesson 1.8 notices; an object that comes back is re-ingested. Withdrawn: a person took the document down with `make retire`; the object stays where it is, the walk leaves it alone, the same bytes again are acknowledged and refused, and only `make restore` brings it back. The three are distinct on purpose: before the third existed, a hand retirement looked like a lost object, and the next night's walk put back what a person had just removed.

An older event is not an older version to publish. Delivery is at-least-once and not in order (lesson 1.5). The event for generation 41 of an object can arrive after generation 42 was indexed. The worker reads the ledger's generation before it downloads anything, and an older event is acknowledged as `stale`: one log line, nothing fetched, nothing changed. The bytes are always fetched by generation, never "whatever the object holds now", so an event and its bytes are one version; a generation that no longer exists is the same case, and the newer generation's own event is what indexes it.

A library's reference shelf. One edition of each standard sits on the shelf; that is what a reader may consult. A new edition goes on the shelf in one motion and the old one goes to the stacks with a slip saying which edition replaced it and when the stacks may discard it. Three things take a book off the shelf: a newer edition (superseded), the publisher withdrawing the title from sale (retired, when the walk finds the object gone), or the librarian pulling it by hand with a note that says do not reshelve (withdrawn). And when a courier turns up with last year's edition after this year's is already shelved, the librarian checks the edition number against the catalogue and sends it back unopened. That is the generation guard.

#### Play the lifecycle

The player below is the kit's rules as a state machine: one document, its ledger row, its versions and their rows, and what the worker or the walk says after each event. Press the events in any order that the rules allow; the greyed ones do not apply to the state you are in. Watch two things: the ledger status and what a reader would see.

The claim state is `documents/{doc_key}.status`, the rows state is the `current` flag with its `expire_at`, the ledger status is `sources/{name}.status`. Every transition here is a function you will read on this page: `swap_versions`, `retire_previous`, `reactivate`, `stale_generation`, `withdrawn`, and the reconcile CLI's `--retire` and `--restore`.

### The words: staged, swap, superseded, retired, withdrawn, generation, tombstone

Nine words, each with the value it takes on your lane.

Lesson 1.4 wrote these records and lesson 1.6 counted them. This lesson reads their flags, because the flags are the lifecycle: a row's state, a claim's state and a ledger row's state, and the events that move them.

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

### Publish: the swap, and the reader's guard

The one pass that makes a version current, the flags it leaves on the version it replaces, and the guard that closes the window between its two commits.

#### Definition

`swap_versions()` reads every row of the source and makes two passes in one batch. First the new version's rows: `current: true`, the stage marks deleted, any old successor and expiry deleted, because a reactivated row may carry them. Then every other current row: `current: false`, `superseded_by` the new key, `superseded_at` now, `expire_at` thirty days out, and `effective_to` the new version's declared date when it has one, so the old version's window closes where the new one opens. The claims of the retired versions become `superseded` with a `retired_at` that the undo will count against the window. A document longer than 400 rows flips in more than one commit, and between them two versions are current; the reader's `newest_per_source()` keeps the one whose rows landed last and drops the other, and `prefer_current()` drops retired rows before anything reaches the reranker.

#### The code

#### Read the handbook's versions, Rs 0

Three versions of one document, 849 rows, and exactly one version current: version 1, reactivated twice. The other two carry the successor's key, which is version 1's, because an undo is a swap like any other, and an expiry thirty days after the undo that retired them. Neither carries `effective_to`, because version 1 declares no date; revision 3's rows did, briefly, when revision 3 retired them in lesson 1.6, until the undo cleared the field. No row is staged: every swap on this lane completed.

### Superseded: the retired rows' bookkeeping, and the clock that removes them

What a retired row carries, why nothing in the worker deletes it, and the policy that does.

#### Definition

Retiring is a flag. `retire_previous()` and the swap write four fields and touch nothing else: the row keeps its text, its vector, its stamps and its locator, which is what makes reactivation free and what makes the undo window exactly thirty days long. The only deleter is a Firestore TTL policy on `expire_at`, declared in Terraform, which removes a row within a day of its expiry. `make purge` is the policy's manual twin: it lists the retired rows past their expiry and, with `APPLY=1`, deletes them; on a lane with the policy applied it finds nothing to do, which is the point of running it once.

#### The code

#### Do it: the purge plan, Rs 0

The plan found 566 retired rows for acme and none past their expiry, so it had nothing to do, and with the policy applied it never will: the platform gets there first. Read the date arithmetic once: a version undone on 22 September can be brought back until 22 October, and after that its bytes are a fresh version, parsed and embedded again. The window is a variable in Terraform, and lesson 1.3's embedding stamp is what lets the worker trust a row it finds inside it.

### Stale: the generation guard, and three replayed events

The check the worker makes before it downloads a byte, and three events you publish yourself to watch it decide.

#### Definition

The ledger row records the generation the worker indexed. When an event arrives, `stale_generation()` compares the event's generation with that number: older means a late redelivery, and the worker acknowledges it with one line, `ingest_stale_event`, reason `older than the ledger`. An event as new as the ledger, or newer, goes on: the bytes are downloaded by that generation, and a generation that cannot be fetched is the other stale case, `generation gone`. Note what the bucket does: it keeps every generation of an object for a year, so the older bytes still exist; the guard, not their absence, is what refuses them.

#### The code

#### Do it: three events, three verdicts, Rs 0

The block reads the handbook's generation off the ledger, then publishes three records into the ingest topic exactly as Cloud Storage would, with the generation before the ledger's, the ledger's own, and one after it. The push subscription delivers them to the worker, and the worker's three lines say what it did with each. Nothing on the lane changes.

Three identical-looking records, three different verdicts, all acknowledged. The older generation never reached a download: the ledger's number was enough. The ledger's own generation was fetched, hashed to version 1's key, found the claim already indexed, and was a duplicate, which is what a real redelivery of the last event looks like. The generation one past the ledger's was fetched and did not exist, and the worker said so rather than reading whatever the object holds now, because an event and its bytes are one version. Delivery can be late, doubled or out of order; the ledger and the generation are what make that harmless.

### Withdrawn: retire a document by hand, then restore it

The tombstone: what `make retire` writes, what it holds against, and the one command that clears it.

#### Definition

A person retires a document with `make retire SOURCE=`. The reconcile CLI retires every current row of the source with the usual four fields and a thirty-day expiry, tells the managed mirror the version left, sets the ledger row to `withdrawn` with a timestamp, and refreshes the tenant's fingerprint so the answer cache follows. The object is not touched: it stays in the bucket on purpose, and the nightly walk reports it as "withdrawn, object kept". The tombstone holds against two things that would otherwise bring the document back: a redelivery of its event, and the same bytes uploaded again, both acknowledged as `ingest_withdrawn`. `make restore SOURCE=` is the way back: it moves the ledger row to `retired`, the state a lost event recovers from, and rewrites the object onto itself, which is a new generation and a new event; the worker then reactivates the rows inside the window, or re-ingests the bytes after it.

#### The code

#### Do it: withdraw the note, test the tombstone, restore it

The document is the note lesson 1.4 indexed, three chunks under `acme/smoke_note_v1.md`, with its bytes still at `~/lesson34_note.md`; if you skipped that lesson, run its step 3 first. Four blocks: the withdrawal and what the API and Firestore say; a question that now has no source; the same bytes again, refused; the restore, and the same question answered. Everything here is a flag flip: no parse, no embedding. If the file is not on this machine, the box below gets it back before anything else runs.

Lesson 1.4 wrote the note into the home directory of the machine it ran on. On another machine, Cloud Shell instead of the workstation or a fresh workstation, the file is gone while the ledger still holds its hash, and a note rewritten with today's date has different bytes: the worker would index it as a new version, and every reactivation on this page would read `ingest_ok` with three embedded instead. Get the original bytes back and check them against the ledger. The uploads bucket is versioned, so the object itself is the first place to look, and its last generation serves when the object has been deleted, as lesson 1.8 does on purpose. If the bucket has nothing, the second block rebuilds the note the way 1.4 wrote it, the kit's fixture plus one line naming your account and the day, and tries the last sixty days against the ledger's hash.

`make retire` also tells the tenant's managed stores that the version left, because acme's data region allows copies there. If that call refuses (a store the lane never created, a permission), the line names it. `MANAGED_MIRROR=off make retire PROJECT=$PROJECT SOURCE=…` withdraws the kit's own rows and the ledger row alone; the managed copy is then the walk's to reconcile, which is lesson 1.8.

The withdrawal flipped three rows, wrote one word on the ledger row and moved the fingerprint, and the document was gone from every answer within a second, with its object untouched in the bucket. The same bytes came back and were refused with a hint, which no other state does: a superseded version would have been reactivated. The restore moved the row to `retired` and rewrote the object, the worker saw a new generation, found three retired rows inside the window, flipped them back and embedded nothing, and the ledger row is `indexed` again with `reused 3, embedded 0`. Nothing was parsed, nothing was embedded, nothing was deleted.

### The three states side by side

One table of the ledger, one excerpt of the walk that reads it, and the difference between a lost object and a withdrawn one.

#### Definition

The ledger row's `status` is what the nightly walk reads first when it compares the bucket with the ledger. `indexed` with the same generation is nothing to do. `withdrawn` is "object kept": the walk reports it and leaves both the object and the rows alone. `retired` is the state the walk itself sets when an object is gone, and an object that is back in the bucket under a retired row is re-ingested. The distinction is the lesson's whole reason for three words instead of one: before `withdrawn` existed, a hand retirement wrote `retired`, the object was still there, and the next night's walk read "retired but back in the bucket" and resurrected what a person had just taken down.

#### The code

#### Read the ledger as the operator does, Rs 0

The same rows the Versions table renders, from the shell, with the status column that step 6 moved twice: `withdrawn` after the retirement, `retired` for the seconds between the restore and the worker's reactivation, `indexed` now. The last line is the tenant's ledger document: the fingerprint that every change on this page moved, the number of indexed versions, and the last event that moved it. Lesson 1.8 runs the walk that reads this table every night.

### The swap window, effective dates, and what a version costs

Where the reader's guard earns its keep, the date a retired version's window closes on, how the index and the cache follow the flag, and the rupee line.

#### The two-commit window

A Firestore batch holds 500 writes and the swap commits every 400, so a document of more than 400 chunks flips in two commits, and for the milliseconds between them both versions are current. The reader does not rely on luck: `newest_per_source()` groups a candidate set by source and keeps the version whose rows landed last, by `indexed_at` or, for a reactivation, `reactivated_at`. On your lane no document is that long, so the guard has never fired; it is there for the 236-page Act and for the day a corpus load lands a thousand-chunk contract.

#### Effective dates, and the gap the ledger leaves open

A version may declare when it applies (`effective_from`, from its name or its first lines), and the swap closes the retired version's window with `effective_to` at the successor's date. The rows therefore carry a timeline: version 1 until 1 November, revision 3 from it. What the reader does with that timeline today is nothing: retrieval answers from the current version only, and a question about last month's policy gets this month's clause. The kit's README lists the as-of filter as the strategy's next phase; the fields are already on the rows so that the filter, when it comes, needs no re-index.

#### The index and the cache follow the flag

Two other stores must agree with `current`. The search index carries it as a restrict on every datapoint, and the worker removes a retired version's ids from the index after the swap and re-upserts them from the rows' own vectors on a reactivation, so the ANN rung and the Firestore rung answer the same version. The answer cache is keyed to the tenant's corpus fingerprint, which every swap, retirement, withdrawal and restore refreshes; a cached answer packed from the old corpus is simply not used until the cache is packed again. That is why the answer in step 6 changed twice without anyone touching a cache.

#### What a version costs

The asymmetry to remember: publishing is cheap and reversible because it is flags, and the expensive parts of a version, the parse and the embeddings, are paid once on the way in and never again while the window is open. Everything on this page cost less than the two questions you asked.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

The note was withdrawn and restored: its three rows carry a `reactivated_at`, its ledger row is `indexed` again, and the bucket holds one more generation of it. Three events were replayed and changed nothing. The handbook was only read. Lesson 1.8 runs the nightly walk that compares the bucket with this ledger, and brings back what it should and only that.

Netsetos GenAI on GCP · Module 1 RAG foundation · Lesson 1.7 Publish versions, retire documents and reject stale events · v5.0

Next: Lesson 1.8 Restore documents and reconcile index differences.
