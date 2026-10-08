# Lesson 7.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_7.4_Mirror_Freshness_WIX.html`, reviewed at blob `52a2208d70780892bee65299e6a93e78318165ff`. Learners read that page on the course site; this guide keeps its prose.

Lesson 7.3 put a copy of acme's and zeta's documents into two Google-managed stores and read answers back from them. A copy raises two questions. Is it as good: does the store find the clause the kit's own index finds? Is it current: when the ledger changes, does every store change with it?

In this lesson you score the six retrieval arms on the golden set, the two stores beside the kit's four. Then you take zeta's handbook through a new version, the undo, a withdrawal and a restore. After each one, `make managed-status` holds both stores against the ledger, and zeta is asked the same question.

- As good, and as current

- The words: arm, anchor, recall@depth, recall@5 and MRR, the miss list, freshness, the undo, the tombstone, the restore, drift

- Before you run anything: set up the shell

- The four events through the kit's mirror, run

- Six arms, one golden set: is a store as good?

- A new version, then the undo

- A withdrawal, then the restore

- Why freshness works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn how the kit measures a store's quality: recall and MRR on the golden set's anchors, with a miss list for each arm. You will also learn how it keeps a store current: four events, each taking its own path to the stores, and one check after every event. Then you will prove it on your lane. `make managed-status` reads `in sync` after a reindex, an undo, a withdrawal and a restore, and zeta's answer changes with each one.

### As good, and as current

A measure of quality, four events that change the ledger, and one check after each.

Is the copy as good? A store retrieves by its own rules. RAG Engine cuts a version into pieces of 512 tokens and keeps what falls inside a distance threshold. Vertex AI Search returns extractive segments of whole documents. `make ablate ABLATE_ARGS="--arms all"` runs `evals/ablate.py`. It takes the golden rows that carry anchors, the phrases a right answer must retrieve, through six arms with one knob changed in each:

- The kit's four arms: dense 5 with no reranker; dense 20, then the reranker to 5, which is the lane's own path; dense 50, then the reranker; and 4.5's hybrid of dense and BM25, then the reranker.

- The two stores: a RAG Engine query and a Vertex AI Search query, each asked for 20, then reranked to 5 by the same reranker.

For each arm it prints recall at the arm's depth, which is the reranker's ceiling, then recall@5 after the reranker, MRR, the rows whose every anchor is in the five, and p95 latency. Under each arm is its miss list: every row that lost a point, and where the anchor went. No model answers anything, so this is retrieval alone.

Is the copy current? A copy is a second place where a version lives. The ledger changes in four ways, and each way takes its own path to the stores:

- A new version. The worker ingests the new bytes and swaps the versions, then calls `after_swap()`. The new text goes into each store, and the replaced version leaves each store as `delete:superseded`.

- The undo. The older bytes are uploaded again. The worker reactivates the older version's rows, with nothing parsed or embedded, then calls `after_undo()`. The text is read off those rows and sent again, and the newer version leaves.

- A withdrawal. `make retire` runs `reconcile.py`. It retires the rows, deletes each store's copy as `delete:withdrawn`, and turns the ledger row into a tombstone, `withdrawn`. The object stays in the bucket and the nightly walk leaves it alone. If the same bytes arrive again, the worker acknowledges them without indexing them.

- A restore. `make restore` lifts the tombstone to `retired` and rewrites the object onto itself. The new generation's event reaches the worker, which reactivates the rows and calls `after_undo()` again.

After each event, `make managed-status` holds each store against the ledger's current versions. It reads `in sync`, or `drift` with the missing and orphan doc_keys. The drills run on zeta, whose corpus has no pictures. Lesson 7.3 showed why that matters: `managed-status` counts every indexed version, and acme's three pictures are never copied, so acme never reads `in sync`.

A housing society's rule book and the copies at its two gates. The secretary keeps the master file. The security desks at Gate 1 and Gate 2 each keep a copy of the current rules. When the committee amends a rule, the secretary sends the new page to both gates and takes the old page back. When the amendment is reversed, the old page goes out again from the master file, and nobody retypes it.

When a rule is withdrawn pending a court case, both gates hand their copies back, and the file marks the rule "withdrawn". The signed original stays in the cupboard. When the court clears it, the rule goes out again the way a reversal does. Every evening the secretary phones both gates and counts their pages against the file. Once a year each desk is asked the same forty-seven questions, to see whether it finds the right page as surely as the office does.

The master file is the ledger, and the gates are the stores. The evening call is `make managed-status`, and the forty-seven questions are the golden set. The old page sent from the file is `after_undo()`. The file's "withdrawn" mark is the tombstone, and the original in the cupboard is the object the bucket keeps.

#### One document's life, and the stores behind it

Play events on one document of a tenant whose stores are both on. The first version is uploaded to start. Each button runs one event the way the kit runs it, and the panel shows:

- what the worker or `reconcile.py` made of the event, and each line the mirror wrote;

- the ledger row, what each store holds, and what `make managed-status` would read.

The lifecycle is the kit's. The worker's claim decides `indexed`, `duplicate`, `reactivated` or `withdrawn`. Then come `reconcile.py`'s `--retire`, `--restore` and walk, the mirror's calls, and `managed.status()`. 41 sequences of these events, 320 steps in all, were replayed through the kit's own worker and `reconcile.py` and compared with the panel step by step.

Here every copy lands at once. A real Vertex AI Search import is a long-running operation, and `make managed-status` reads `drift, missing` for that store until the import finishes. Steps 5 and 6 wait for it. A picture has no text, so it is never copied, and it stays missing from both stores for as long as the tenant holds it.

### The words: arm, anchor, recall@depth, recall@5 and MRR, the miss list, freshness, the undo, the tombstone, the restore, drift

Ten rows, each with the value it takes on your lane.

One distinction to hold: the ablation measures what a store finds, and `make managed-status` measures what it holds. The ablation cannot see a stale copy, because a store's context is scored by its source and its text, whichever version it came from. That is why freshness has its own check.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `API` and `ME` set by the setup above. You also need lesson 7.3's lane: `MANAGED_MIRROR=both`, zeta pinned to `vertex_search`, and zeta's two stores in sync.

- rank-bm25. The ablation's hybrid arm imports `rank_bm25`. The Makefile's comment above `ablate` names it, but no requirements file installs it, so step 4's first line does. Lesson 2.2 installed it already, and running it again is safe.

- The pin window. The setup moved acme to the kit's own index. Nothing here asks acme through the API: the ablation queries each store directly, and the drills ask zeta, which stays pinned to Vertex AI Search.

- What the lesson changes. It uploads a second version of zeta's handbook, then the first version's bytes again. Then it withdraws the handbook and restores it. It ends where it started: version 1 current, and in both stores.

### The four events through the kit's mirror, run

The kit's Mirror and the check behind `make managed-status`, with two stand-in stores and a stand-in ledger.

#### Definition

The cell imports the kit's `managed.py` and runs its `Mirror` with two stand-in stores, one in us-central1 and one in `global`, as the real ones declare. It also needs a stand-in ledger. That is the handbook's rows (`chunks`) and its ledger row (`sources`), the two collections the mirror and `status()` read. The five moves:

- v1 is ingested: the worker's swap, then `after_swap()`;

- v2 replaces it: `after_swap()`, with v1 in the swap's `retired_doc_keys`;

- the undo: the rows flipped back to v1, then `after_undo()`, which is given no text;

- `make retire`: the rows retired and the ledger row withdrawn, then `retired(..., "withdrawn")`;

- `make restore`, with the stand-in Vertex AI Search refusing one import: the rows current again, then `after_undo()`.

After each move, the kit's `status()`, which is what `make managed-status` prints, holds both stores against the ledger.

#### The code

#### Do it

- A new version is one call with two effects. `after_swap()` copied v2 into both stores and took v1 out of both (`delete:superseded`). Each store ends up holding one version, the one the ledger calls current.

- The undo was given no text. `after_undo()` read v1's text off its rows, which is why both stores now hold "a notice period of 30 days". Then it took v2 out. Nothing was parsed or embedded.

- `make retire` emptied both stores (`delete:withdrawn`). The ledger row is withdrawn, so the ledger has no current version, and `in sync` means that both stores hold nothing.

- The restore took the undo's path. When Vertex AI Search refused the import, the mirror wrote `mirror_failed` and went on, because a copy never fails an ingest. Only `make managed-status` saw it: `vertex_search drift, missing ['v1']`.

### Six arms, one golden set: is a store as good?

The kit's ablation harness, with the two stores beside its four arms: recall, MRR and a miss list for each.

#### Definition

`make ablate` runs `evals/ablate.py` with the lane's settings, and `--arms all` adds the two store arms to the kit's four. Every arm gets the same 47 rows, each asked of its own tenant. No model answers anything: the harness calls only the embeddings, the stores and the reranker, so it takes a few minutes.

A store's context names its version by doc_key, and `source_of()` finds that version's source through the kit's rows. So an anchor that is a file's name can match a store's chunk, as it does the kit's own. It reads the rows whatever their `current` flag says.

#### Do it

The expected output comes from a stand-in whose retrieval is word overlap. The shape is the kit's, but the numbers are not yours. Read it in the order the harness prints under the table:

- recall@depth is the reranker's ceiling. On the stand-in, dense 20, dense 50 and hybrid all reach 1.00 at their depth, and all score 0.94 recall@5. Depth is not the knob there, and their three misses are `ranked out`: the reranker's.

- A store arm's depth is what the store returned, not 20. RAG Engine returns only the contexts inside distance 0.5, and Vertex AI Search returns up to three segments a document. `not retrieved at depth 0` is a row for which the store returned nothing at all.

- The two failed rows are globex's. globex has no corpus and no data store (lesson 7.3), so each store arm scores 45 rows. The harness prints the failures beside the line instead of scoring them as zeros.

- Hold each store row against the lane's row. The rows and the reranker are the same, and only the retriever changed. For a real reference, the kit's docstring records one run from Cloud Shell on 8 September 2026, over 43 rows: dense 5 alone 0.91 recall@5 and 0.81 MRR; the lane's dense 20 → rerank 5 0.96 and 0.91; dense 50 → rerank 5 0.99 and 0.94.

### A new version, then the undo

zeta's handbook with a longer notice period, then its first bytes again, and the stores held against the ledger after each.

#### Definition

The cell writes a second version of zeta's handbook with one change: a confirmed employee's notice period goes from 30 days to 45. `make reindex` uploads it under the same name and waits for the worker's line. Then `fresh154` checks three things:

- the mirror's `doc.mirror` events for zeta since the upload, read from the audit bucket;

- `make managed-status TENANT_ONLY=zeta` every 20 seconds, until the handbook's ledger status is the one asked for and both stores are `in sync`. It prints only the changes of state;

- zeta, asked the notice-period question through the API as `documind-ui-sa`.

The audit events are the one record that every event leaves. Step 6 shows why the cell reads them instead of the logs: `make retire`'s deletes print no line. The cell defines `fresh154` in your shell, and the three cells after it call it again, so run all four in the same shell.

#### Do it

- The worker reused 282 of the 283 chunks and embedded one, the chunk with the changed clause. The swap retired version 1's 283 rows, which expire 30 days later.

- The mirror sent version 2 (`zeta_025c4143...`) to both stores and took version 1 out of both. Those are the four `doc.mirror` events, the same moves as step 3.

- `make managed-status` read `drift` for Vertex AI Search first. The import had been requested, not finished. At 0:20 both stores were in sync, with 7 versions each. On a real data store the import takes minutes, so expect the drift line to stand longer.

- zeta, answered from Vertex AI Search, says 45 days, and the chunk it cites carries version 2's doc_key.

Now the undo: the same name, with the first version's bytes, straight from the kit's corpus. This is the worker's branch for a version it has seen before:

- `ingest_reactivated`, with 283 reused and 0 embedded. The worker found version 1's claim superseded and flipped its rows back instead of ingesting the bytes again. Its `retired` column, 283, is version 2's rows.

- The mirror did the update in reverse: version 1 (`zeta_e920a147...`) into both stores, version 2 out of both. `after_undo()` read the text off version 1's rows.

- In sync at 0:20, and zeta says 30 days again, citing version 1's doc_key.

### A withdrawal, then the restore

The handbook taken down by hand, every store emptied of it, and then brought back.

#### Definition

`make retire SOURCE=` runs `reconcile.py --retire`, with the mirror and the audit bucket the nightly job has. It retires every current row of the source, tells every store, and turns the ledger row into a tombstone:

`make restore SOURCE=` refuses anything but a withdrawn source. For a withdrawn one, it lifts the tombstone to `retired` and rewrites the object onto itself:

#### Do it

- `reconcile_withdrawn` names the version it retired and its 283 chunk ids, cut here to the first and the last. It also carries a new fingerprint for zeta's corpus.

- Two `doc.mirror` events: `delete:withdrawn`, one from each store. The cell has to read them from the audit bucket. `reconcile.py` configures no logging, so the mirror's `mirror_ok` lines, which are INFO, are dropped, in your shell and in the nightly job alike.

- In sync at once: the ledger counts 6 current versions for zeta, and each store holds 6. A delete takes effect at once; only an import is long-running.

- zeta's answer is "The context does not say." The notice period is gone from both stores and from the kit's own index.

Then the restore:

`reconcile_restored`: the tombstone went to `retired`, and the object was rewritten onto itself as a new generation. Its event reached the worker, which reactivated version 1's rows inside the 30-day undo window, with nothing embedded. The mirror copied version 1 into both stores, and there was nothing to take out, because no other version was current. In sync at 0:20, 7 versions each, and zeta says 30 days again.

That is the proof: `make managed-status` reads `in sync` after a reindex, an undo, a withdrawal and a restore.

### Why freshness works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- The mirror follows the rows. A new version and the undo both come through the worker, and the mirror is called right after the rows change: `after_swap()` after the swap, `after_undo()` after the reactivation. A store is told what the kit's own index was just told.

- The undo re-sends from the rows, not the file. The rows are what the kit serves, so the copy matches the kit's own index, and nothing is parsed or embedded again.

- A withdrawal is a tombstone, not a deletion. The object stays in the bucket so that `make restore` can bring it back, and the walk leaves it alone. `reconcile.py`'s comment gives the reason: under the old rule, the next night's walk brought back what a person had taken down.

- The restore goes through the worker's one path. The rewrite makes a new generation, the same event and the same worker. Inside the 30-day undo window the worker reactivates the rows; after it, the bytes are ingested as a fresh version.

- A delete is never refused. Every store is told, whatever the tenant's policy, and a store that never held the version answers NotFound instead of failing.

- The check is not the writer. `make managed-status` reads the ledger and each store's own listing, so it sees what the mirror failed to do, as in step 3. It measures; it repairs nothing.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- A missing copy stays missing. The walk plans nothing for a document whose copy failed. The same bytes uploaded again are a duplicate that the worker acknowledges, and the mirror never sees them. Only another version's swap, or an undo, sends the text again. The panel shows this: fail the next copy, upload version 2, run the walk, then upload version 2 again. `make managed-status` is the only thing that notices.

- `make retire`'s store deletes print no line. `reconcile.py` configures no logging, so Python drops the mirror's INFO lines, in your shell and in the nightly Cloud Run job, which gets `MANAGED_MIRROR` too. Only a failure, which is a WARNING, reaches stderr. The `doc.mirror` audit events are the record, which is why `fresh154` reads the audit bucket.

- The ablation cannot see a stale copy. `source_of()` resolves a store's context through the kit's rows whatever their `current` flag says, while the dense arms filter on it. A store that still held a retired version would score that version's text as a hit. The ablation measures quality, and `make managed-status` measures freshness; neither does the other's job.

- Nothing waits for a Vertex AI Search import. After every event that copies, the data store reads `drift` until the long-running import finishes, and no make target waits for it; `fresh154` polls. `managed.py`'s comment says the walk verifies the import, but `reconcile.py` calls the mirror only to delete.

- The hybrid arm's `rank-bm25` is in no requirements file. Only the comment above `make ablate` names it, so a fresh shell fails the arm until it is installed by hand.

- `ablate.py`'s docstring is behind. It says 43 anchored rows and one managed arm. The golden set has 47 rows with anchors, and `--arms all` runs two store arms.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

zeta's handbook went to version 2 and back, and ends as it started: version 1 current, 283 chunks, in both stores. Version 2's copies are gone from both stores. Its 283 rows are retired and expire 30 days after the undo retired them. The object has new generations, from the uploads and the restore's rewrite, and `$HOME` holds `hr_policy_zeta_2026_v2.md`, which you can delete. Lesson 7.5 queries a video clip and validates media citations.

Netsetos GenAI on GCP · Module 7 Graph and multimodal · Lesson 7.4 Compare quality and test update/withdrawal freshness · v5.0

Next: Lesson 7.5 Query a video clip and validate media citations.
