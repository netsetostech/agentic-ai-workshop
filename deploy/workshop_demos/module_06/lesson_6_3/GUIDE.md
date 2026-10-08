# Lesson 6.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_6.3_Cache_Freshness_WIX.html`, reviewed at blob `42a67f4e01b8e91ddac46f96e60590b66df457d6`. Learners read that page on the course site; this guide keeps its prose.

A cache is right only while the thing it copied has not changed. This lesson changes things on purpose and watches both caches react. You ask the E3 notice-period question under three scopes, then release revision 2 of acme's handbook, which makes the answer 90 days instead of 60. The answer cache misses, the context cache goes stale, and `make cache` brings the second one back. Finally you put version 1 back and watch the old answer return, because the corpus it was given under has returned.

- What each cache checks, and the fingerprint both follow

- The words: fingerprint, doc_key, reindex, the undo, scope, cache_stale, the dated rule

- Before you run anything: set up the shell

- Both caches, and the corpus they follow

- Scope: the same words under other settings

- The corpus moves: revision 2, and both caches react

- make cache again: attached again, and what it packed

- The corpus comes back: version 1, and the old answer with it

- Why freshness works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn exactly what each cache compares before it is used, why one fingerprint of the corpus is enough to keep both caches honest, and which configuration changes the kit's caches see and which they do not. Then you will prove it on your lane: the miss after `make reindex`, a hit again after `make cache`, and the old answer served again once the old document is back.

### What each cache checks, and the fingerprint both follow

Two lists of conditions, one name for the corpus, and what each list leaves out.

Each cache checks its own list before it is used. The answer cache serves a stored answer only when four things hold. It must be for the same tenant, under the same corpus fingerprint, for the same scope (the filters, `top_k` and the prompt version), and less than 24 hours old. The context cache is attached only when its record exists with more than two minutes left, the request runs on the cache's model, and the fingerprint it was packed from is still the ledger's. Everything else about the request can change without either cache noticing.

The fingerprint is the corpus's name. After every reindex, retirement and reactivation, the worker hashes the tenant's sorted current `doc_key`s into `ledger/{tenant}`. A `doc_key` is the hash of a version's bytes, so a new version of any document gives the tenant a new fingerprint, even when the change is far from the question. The invalidation is coarse, but it is cheap and it is safe: one Firestore read per request, and no scan of the cache. Because the fingerprint names the set of current bytes and not a moment, putting the old bytes back brings the old fingerprint back. Every answer given under it that is still inside its 24 hours becomes a hit again. That is correct, because the same documents give the same answers.

The scope holds what changes an answer, and leaves some of it out. Filters, `top_k` and the prompt version are in the scope, because each can change what the model reads or how it answers. The model, the retrieval backend and mode, and the reranker are not. Change the generator model and the answer cache keeps serving the old model's answers for up to a day; the row names the model that gave each one. The context cache is stricter here: it refuses any request on another model.

Stale means something different for each cache. A stale answer is simply never served. Nothing deletes it, and Firestore's TTL policy reaps it after its day. A stale context cache is not attached. The API writes `cache_stale` in its log for every such request and answers uncached until `make cache` packs again. `make cache` records the new fingerprint, but it packs the kit's own copy of the documents, not the tenant's current corpus. So after a reindex, the new cache is labelled current while holding the old text. What keeps the answer right then is the prompt's dated rule: when sources disagree, follow the one with the latest effective date.

A bank's rate board. The counter answers "what is the one-year FD rate?" from a sheet stamped with the circular it was worked out under. A question for a senior citizen, or for two years, needs its own sheet: that is the scope. When a new circular arrives, every sheet stamped with the old one goes in the drawer, unread: that is the fingerprint moving. If head office withdraws the new circular and restores the old one, this morning's sheets are right again, and out they come. The thick rate manual on the counter is reissued for each circular too, but it is reprinted from head office's master copy, which may still carry last month's page.

#### Freshness over time

Start where step 3 leaves your lane: a context cache packed under version 1's fingerprint, and no stored answers. Then press the events in any order. Change the request's settings before an ask, and read what each cache did.

The timeline runs the kit's own rules. The build replayed 300 random sequences of these events, 905 asks in all, through `store()` and `lookup()` on a stand-in Firestore, and through `get()`, `stale_against()` and `generate_config_kwargs()` on a stand-in record. The panel agreed at every ask. The scope hashes shown are the kit's own `scope_of()`.

The question's words never change here; paraphrases and the near rung were lesson 6.2's. The clock jumps rather than runs. Every answer is taken as answerable and cited, so every miss is stored. Your lane's fingerprints are longer hashes than F1 and F2, and they depend on every document acme holds.

### The words: fingerprint, doc_key, reindex, the undo, scope, cache_stale, the dated rule

Eleven rows, each with the value it takes on your lane.

One distinction to hold: the fingerprint says whether the corpus is the same, and the scope says whether the question is the same. The answer cache needs both, and the context cache needs only the first.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `tok`. This lesson changes acme's handbook for a few minutes. Step 5 makes revision 2 current, and step 7 puts version 1 back. In between, everyone who asks acme about an E3's notice period is told 90 days, so run steps 5 to 7 without a break, on a lane nobody else is demonstrating on. Step 3 also creates acme's context cache and a candidate with `SEMANTIC_CACHE=on`; step 7 removes both.

### Both caches, and the corpus they follow

The fingerprint's source, both caches set up, and the E3 question asked three times.

#### Definition

The worker writes the fingerprint; the API reads it. `refresh_fingerprint()` runs at the end of every change to what is current, and stores the new value in `ledger/acme` with the event that caused it. `/v1/query` reads that document for the answer cache when `SEMANTIC_CACHE=on`, and `cache_manager` reads it again before it attaches a context cache. The first cell creates the context cache and the candidate. The second defines two functions. `ask92` asks the E3 question and prints the backend, the cache verdict, both token counts, the time and the start of the answer. `state92` prints the ledger's fingerprint beside the one the context cache was packed from. The cell then asks once on the live revision and twice on the candidate.

#### The code

#### Do it: the two caches

#### Do it: the state, and three asks

The state line shows the two fingerprints equal, so the context cache is current. The live revision answered with the cache attached: 60 days, and `cached_tokens` non-zero. The candidate's first answer did the same and was stored under this fingerprint and this scope. Its second came back from the answer cache: `cache`, zero tokens, a fraction of the time. That is the baseline everything after this changes.

### Scope: the same words under other settings

Two asks under changed settings, and the scope hashes behind them.

#### Definition

`scope_of()` hashes the filters, `top_k` and the prompt version into 16 characters stored on each answer. `_alive()` compares that hash, the fingerprint and `expire_at`. The cell asks the same words with `top_k` 8, then with the filter `kind: text`, which keeps the same handbook chunks. It then prints four scope hashes with the kit's own function: as asked, the two you just used, and prompt version `v4`. Changing the prompt version takes a new revision, so the hash is enough to show it would miss.

#### The code

#### Do it

Both asks missed, although the words were the same and the answer was the same 60 days. A wider pool or a filtered one may not give the same answer, and the cache cannot know that it did. So each scope keeps its own entry: two more answers are stored now. The four hashes are all different, and a `v4` prompt would miss for the same reason. The model is not in the list, so a candidate on another model would still be served these answers; the timeline's model setting shows it.

### The corpus moves: revision 2, and both caches react

A release of revision 2, the new fingerprint, and both caches asked again.

#### Definition

Revision 2 is version 1 with two changes: a dated line at the top, and NP-03's figure raised from 60 to 90 days. `make reindex` checks the golden rows that cite the handbook offline, uploads the file under the handbook's object name, and waits for the worker. Your lane has probably seen these bytes before, in lesson 1.3. If so, the worker brings back that version's rows without embedding anything (`ingest_reactivated`); if not, it embeds the changed chunks (`ingest_ok`). Either way, revision 2 becomes current, version 1 is retired, and the fingerprint moves. The next cell asks both revisions again and reads the API's `cache_stale` lines.

#### The code

#### Do it: the release

#### Do it: the state, both asks, and the log

The ledger's fingerprint changed, and the state line calls the context cache STALE. The live revision answered 90 days with `cached_tokens` 0: its cache was packed from the old corpus, so it was not attached, and the log says `cache_stale`. The candidate missed on the words it answered from its cache a minute ago, because that answer belongs to the old fingerprint. That is the first proof: the miss after `make reindex`. Its new answer is 90 days, and it is stored under the new fingerprint. Served from the cache instead, the old answer would have been the wrong number, delivered faster.

### make cache again: attached again, and what it packed

A new pack under the new fingerprint, and one question to the live revision.

#### Definition

`make cache` builds the pack from the kit's copies of acme's documents, which still hold version 1's 60 days. It records the ledger's current fingerprint, so the record is current and the API attaches it again. The model now reads two things that disagree: the cached pack, which says 60 days and carries no date, and the retrieved NP-03 chunk, which says 90 days from 1 October 2026. Because a packed chunk carries a date, the generator adds the dated rule, and the rule tells the model which source to follow.

#### The code

#### Do it

The state line is current again, and the live answer carries `cached_tokens`. That is the second proof: a hit again after `make cache`. Now read the answer, which should still say 90 days. The reason is not the cache, which holds version 1's text under revision 2's fingerprint. It is the dated rule, which sends the model to the dated source. The cache's label is current, but its content is a version behind the index. A revision without a date line would leave the model to choose between 60 and 90 on its own.

### The corpus comes back: version 1, and the old answer with it

Version 1's bytes again, the state, one ask, every row, and the clean-up.

The same release command with version 1's file puts the handbook back. The worker finds bytes it retired minutes ago, flips their rows back to current, retires revision 2 in turn, and recomputes the fingerprint. Because the set of current `doc_key`s is the same as at the start, the fingerprint is the same as at the start too.

The ledger shows step 3's fingerprint again, and the context cache, packed under revision 2's, is STALE in turn. The candidate's ask was a hit, and the answer is 60 days: the entry it stored in step 3. It was never deleted, only unread. Its fingerprint is the tenant's again and it is still inside its day, so it is right again. The fingerprint names a corpus, not a moment.

#### Every row of the walk

Read the rows in order. There are three live answers: with the cache, stale, then with the cache again. The candidate's rows show a miss, a hit, two scope misses, a fingerprint miss, and the returning hit. The `vertex` rows at `cached` 0 are the minutes between the reindex and `make cache`, when every acme answer ran without the pack. Nothing alerted; only the log said `cache_stale`.

#### Clean up

The answer cache keeps this lesson's entries until their day is up. The 60-day ones match the current fingerprint, so any revision with the switch on may serve them until then, which is correct. The service's configuration says `SEMANTIC_CACHE=on` until the next deploy or candidate sets it back.

### Why freshness works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Coarse on purpose. A new version of any document invalidates every answer the tenant has. A missed hit costs one model call, a wrong hit costs trust, and a fingerprint costs one read. A finer rule, tracing which documents each answer used, would be exact and would cost a join on every lookup.

- The fingerprint moves after the swap, never before. The worker recomputes it only once the new version is current and recorded, so no cache is invalidated for a version a reader cannot yet retrieve.

- Nothing is deleted on a reindex. Old answers and the old cache record stay where they are, unread, the same way the ledger retires a version with a flag. The undo brings the answers back for free.

- Five candidates, not one. A stale twin of the question sits beside the current entry after a reindex, and the lookup reads five neighbours so the stale one cannot hide the current one.

- The two-minute rule. A call never starts on a cache that could expire before the model reads it.

- The dated rule is the backstop. When two sources in one prompt disagree, the model is told to follow the latest effective date and to say so. Step 6 depended on it.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The scope leaves out the model. Every revision with the switch on shares one `answer_cache`. A candidate on a new model is served the answers other revisions stored, for up to a day, so evaluating a model through a cached candidate measures the old model on every cached question. The row names the model that answered, so this shows, but nothing stops it.

- `make cache` packs the kit's files, not the corpus. Step 6's cache was labelled current while it held version 1's text, and only the dated rule kept the answer right.

- Nothing alerts on `cache_stale`. After every upload, a tenant's answers run without the pack until someone runs `make cache`. No metric or alert in `terraform/` counts the log line.

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it on your lane.

acme's handbook is version 1 again, and revision 2 is retired for another 30 days, as it was before this lesson. The ledger's fingerprint is back to its starting value. The context cache is deleted. `documind-api` has one more revision, which serves no traffic and has no tag, and the service's configuration says `SEMANTIC_CACHE=on` until the next deploy. `answer_cache` holds this lesson's answers until their day is up. The usage rows of seven answered questions and two hits. Lesson 6.4 measures what these caches buy: latency, avoided calls in rupees, and the threshold that keeps the near rung from answering the wrong question.

Netsetos GenAI on GCP · Module 6 Context and memory · Lesson 6.3 Test cache scope, configuration changes and freshness · v5.0

Next: Lesson 6.4 Measure latency, avoided calls and false cache hits.
