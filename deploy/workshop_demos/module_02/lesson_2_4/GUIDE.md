# Lesson 2.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_2.4_Fallback_WIX.html`, reviewed at blob `fc9115e7693b7a3af4ab9f5c5711b8b67aea351b`. Learners read that page on the course site; this guide keeps its prose.

Lesson 2.3 followed the pool through the ranker. This lesson takes the pool's other source. Firestore holds every embedding the worker wrote, as a field on the row, and its own vector index can answer a question when the kit's index will not, or when a tenant is pinned beneath it. What must not change on the way down is the three predicates: the tenant from the roster, the ledger's current, and the caller's filters. On Firestore each combination of them needs a composite vector index the kit declares, 8 of them, and without one Firestore refuses rather than degrades. Every chunk the rung returns is stamped `found_by: firestore`, the answer counts `vector_chunks 0`, and the smoke fails a vector deployment that answers from beneath, because that failure is the one a working demo hides. You will read the rung by hand with the API's predicates, move one tenant onto it and back, break the index for a candidate revision and watch the chaos rung answer with a line in the log, run the kit's own read-only probe of the combined filters, see the tier rebuilt from the rows, and price the rung.

- Why a second rung exists, and what must survive the drop

- The words: rung, backend, pin, chaos rung, found_by, pre-filter, composite index, policy, probe, backfill

- Before you run anything: set up the shell

- The Firestore rung by hand: the API's three predicates on Firestore's own vector index

- Moving one tenant beneath the index by hand, and back

- The chaos rung: an index that will not answer, on a candidate that takes no traffic

- The probe: the kit's read-only check of the combined filters

- The tier from the rows: vector-status, backfill-vectors, and the rows that count the rung

- What the rung costs, where it cannot go, and the policy that sends a tenant home

- Verify it yourself: the checklist

You will learn why Firestore holds a second copy of every vector, how the same three predicates are applied on that rung as pre-filters, why each combination needs its own composite index, and how a chosen rung and a fallen-into one read differently on the answer. Then you will prove it on your lane: reproduce the rung with the API's predicates, pin acme beneath the index and back, force the chaos rung on a candidate revision and read `vector_search_fallback`, run `commands/check-firestore-fallback.py`, and read `make smoke`'s verdict both ways.

### Why a second rung exists, and what must survive the drop

An outage is not a refusal, a filter is a predicate on the corpus and not on one way through it, and a substitution nobody noticed is the failure the smoke exists for.

Firestore already holds every vector, so an outage is not a refusal. The worker mirrors each chunk's 768 numbers into its row as a vector field, and Firestore's own vector index, a flat scan over the tenant's rows by cosine distance, can find the nearest chunks to a question. It is slower than the kit's index and it skips the ANN tier, but a slower answer is a different thing from no answer. Three roads lead onto that rung: the deployment's `RETRIEVAL_BACKEND=firestore`, a tenant pinned to it in `tenant_settings`, and the chaos rung, which is what `_dense_retrieve()` does when the index raises. On every road the chunks come back stamped `found_by: firestore`. The answer tells the two kinds apart: `stages.retrieval_backend` is the backend chosen for the request, and `stages.vector_chunks` is the index's share of the pool. A pinned tenant reads `firestore` and 0; a fallen-into rung reads `vector` and 0.

Three predicates hold on the way down. The tenant is the roster's, never the body's. `current` is the ledger's, applied when `RETRIEVAL_CURRENT_ONLY` is on. The caller's filters are the two keys the API allows, `doc_type` and `kind`, and any other key is a 400 before retrieval starts. On the index they travel as restricts; on Firestore they are pre-filters in front of `find_nearest`, an equality each, or one `in` for a `doc_type` list, which runs on the same composite index as the equality, and Firestore will only run a vector query whose pre-filter combination has a composite vector index of its own. The kit declares 8: the tenant alone, the tenant with current, and every combination of the two filter keys with and without current. That is why a new filter key is a Terraform change before it is a code change: without its index Firestore does not degrade, it refuses.

The smoke refuses a quiet substitution. A vector deployment answering from beneath looks right from every angle a demonstration checks: answers come, citations come, `/version` still says Vector Search. Only the row says what happened, `vector_chunks 0` under `retrieval_backend vector`, and `make smoke` fails on exactly that pair, naming the two commands that put the tier back: `make vector-status` to count it and `make backfill-vectors` to fill it from the rows' stored vectors, with no model call, because the vectors were never lost.

The second counter. A records office has a fast desk and an archive counter. The fast desk keeps an index card for every file and finds the nearest ones in a moment; the archive counter keeps the files themselves, every one, and finds the same ones by walking the shelf, slower. When the fast desk is closed, or a department has been told to use the archive, the archive counter serves the same person with the same three rules: it checks the badge for the department, it hands out current files only, and it applies whatever filing-cabinet restriction the request named, provided the shelf has a divider for that combination. Every slip is stamped with the counter that served it. And the office manager's audit rule is blunt: a day when the fast desk was open on paper but every slip came from the archive is a failed audit, however happy the customers were.

#### The ladder: three tiers, one contract

- managed storesRAG Engine or Vertex AI Search hold a copy of an `any` tenant's current versions and rank on their own terms (Module 7); the kit reranks, packs and cites as alwaysfound_by rag_engine | vertex_search · managed_chunks

- the kit's indexVector Search, dense or hybrid, with the tenant, current and filter restricts; the deployment's default and acme's pinfound_by vector · vector_chunks 20

- Firestore's own vector indexthe same rows, a flat cosine scan behind the same pre-filters; chosen by a setting or a pin, or fallen into when the index raisesfound_by firestore · vector_chunks 0 · vector_search_fallback when fallen into

Whatever rung answers, `prefer_current()` drops retired versions, the reranker orders, the packer fits, and the citations resolve against the packed set (lesson 2.3). The rung changes where the pool comes from, never what happens to it.

#### The rung finder: the handler's rules, on the settings you choose

Which rung answers a request is decided by four things in order: the startup validator, the deployment's backend against the tenant's pin, the tenant's data-region policy against a managed store, and then whether the index answers. The finder below applies the kit's rules in that order, `check_retrieval_modes()`, `choose_for()`, `retrieval_backend_for()` and `_dense_retrieve()`, and says what the answer, the log and the smoke would show, and which of the 8 composite indexes a Firestore query would need for the predicates you set.

The index list is read from `terraform/firestore_indexes.tf` when this page is built; the backend names from config.py; the smoke's two sentences from `smoke/smoke.py`. Nothing here calls your lane; steps 3 to 7 do.

It is not the lane: it says what the code would do, not what your lane did, and the pin it models is read once a minute by the API, so a change you make in step 4 takes up to a minute to show. The managed rungs are Module 7's; here they matter only as the case the policy sends home.

### The words: rung, backend, pin, chaos rung, found_by, pre-filter, composite index, policy, probe, backfill

Ten rows, each with the value it takes on your lane.

One pair of words carries the lesson: chosen and fallen into. Both produce a pool stamped `firestore`, and only the answer's `retrieval_backend` beside its `vector_chunks` tells you which happened. The smoke reads the pair; so should you.

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

The index names and the retrieval settings live in the API's environment; a name the service does not set is unset rather than exported empty, because the kit's settings class reads an empty variable as a value, and steps 5 and 6 import the kit. The pins live in Firestore, one document per tenant, and the lane helper prints them.

### The Firestore rung by hand: the API's three predicates on Firestore's own vector index

The one function that answers from beneath, the two keys it accepts from a caller, the indexes that let it, and a cell that runs it three ways for a fraction of a paisa.

#### Definition

`_firestore_fallback()` is short because Firestore does the work. It starts from the chunks collection filtered to the tenant, adds `current == true` when the switch is on, adds each caller filter as an equality, or as one `in` for a `doc_type` list, and asks `find_nearest` on the embedding field for the nearest rows by cosine distance, `TOP_K_RETRIEVE` of them. Each row becomes a chunk with its distance flipped into a score, so the reranker and the fallback's own ordering read it like an index result, the 768 numbers dropped so they never reach the model, and `found_by` set to `firestore`. The cell reproduces it with the same client calls, prints the first five rows with the fields the predicates read, and estimates what Firestore bills for the query: one read per hundred index entries it scans and one per document it returns.

#### The code

#### Do it: the rung under three predicate sets

Run the cell as it is, then twice more with a filter in front of its first line: `F='{"doc_type":"policy"}' python - <<'PY'` and `F='{"kind":"text"}' python - <<'PY'`, the rest unchanged. The worker stamped the lane's uploads `doc_type: unknown`, so the first filter empties the pool on this rung exactly as it did on the index in lesson 2.1, and the second keeps it whole.

Firestore found the same clause the index finds, NP-03 first, from the rows alone: the vector on the row was enough, which is the whole reason the rung exists. The predicates behaved as predicates on the corpus rather than on one way through it: the tenant narrowed the shelf, the `doc_type` filter emptied it exactly as it had on the index, and `kind` kept it whole. Each combination named a different composite index, and every one you asked for existed because the kit declares them all; ask for one that is not declared, a new key say, and the same call raises a failed-precondition error with a link, which is a Terraform change before it is a code change. The bill was tens of reads, which step 8 turns into paise.

### Moving one tenant beneath the index by hand, and back

The document that pins one tenant, the minute the API takes to notice, the same three predicates on the chosen rung, two tenants that do not cross, and the smoke's line for a chosen rung.

#### Definition

A pin is a field, `retrieval_backend` on `tenant_settings/{tenant}`, written by `make tenant-backend` and read by `choose_for()` once a minute per tenant. A pin the deployment cannot serve, an unknown name or a managed store under hybrid mode, is ignored with a `retrieval_pin_ignored` line rather than a 500; a pin to a managed store is then held against the tenant's `data_region`, which is step 8. A pin to `firestore` takes the chosen road in `_dense_retrieve()`: no endpoint is asked, the rung answers with the same predicates, and the answer says `retrieval_backend firestore` beside `vector_chunks 0`. The smoke reads that pair as a request that ran somewhere else and skips its vector-tier check, because a chosen rung is not a fault. The cells pin acme, wait for the API to notice, ask the same questions under the same filters as step 3, ask two tenants the same question, read the smoke's line, and pin acme back.

#### The code

#### Do it: pin acme beneath the index, and wait for the API to notice

#### Do it: the same predicates on the chosen rung, and two tenants that do not cross

#### Do it: the smoke's line for a chosen rung, then the pin back

One field moved a tenant beneath the index without a deploy, and the API noticed within its minute. On the chosen rung the three predicates held exactly as on the index: the `doc_type` filter emptied the pool again, the `kind` filter kept it, and the answer was the same clause. Two tenants asked the same question on two rungs and got their own handbooks' amounts, because the tenant predicate is the roster's on every rung. The smoke saw a request that ran on `firestore` by choice and said so instead of failing, which is the line to expect for a pinned tenant; after the pin came back it counted twenty of twenty again. Step 5 is the case it does fail.

### The chaos rung: an index that will not answer, on a candidate that takes no traffic

The except branch, a candidate revision whose deployed index does not exist, the answer that still comes, the log line that says why, the smoke's verdict on it, and the template put back.

#### Definition

When `find_neighbors` raises, for an undeployed index, an unreachable endpoint or a deployed index the endpoint does not know, `_dense_retrieve()` logs one `vector_search_fallback` line with the error's text and answers from Firestore with the same predicates; hybrid takes the same rung, dense only. The answer then says `retrieval_backend vector`, because that was the request's backend, and `vector_chunks 0`, because none came from the index, and that pair under a vector deployment is the one `make smoke` refuses. The safe way to see it is a candidate revision, no traffic and a tag, whose deployed index name is wrong: the endpoint raises for it as it would for an undeployed index, and the code path is the same one a release-day drill exercises by undeploying the real index for an hour. The undo is different from lesson 2.2's: the variable exists on the live service, so it is set back to its real value rather than removed, or the next revision would inherit the wrong one.

#### The code

#### Do it: a candidate that cannot reach the index

The candidate asked its endpoint for a deployed index that does not exist, the endpoint raised, and the request was answered anyway from the rows beneath, with the same citations as ever and one line in the log that names the cause. Nobody calling that revision would have known; the answer's own pair, `vector` with 0, is the only witness, and the smoke's rule turned it into a red line naming the two commands. Then the template got its real name back, in place, and the live service kept counting twenty of twenty throughout, because a candidate with no traffic never touched it. On a release day the same drill undeploys the real index, and the smoke stays red until the tier is back.

### The probe: the kit's read-only check of the combined filters

A command that verifies the rung's plumbing with a real source's stored metadata, both current modes, and leaves an evidence file; what it checks and what it refuses to certify.

#### Definition

`commands/check-firestore-fallback.py` is the kit's own probe of this rung, written for the day the fallback answered with the wrong tenant's rows. It reads the handbook's ledger row and refuses to continue unless the ledger's hash matches the kit's copy of the file, so the check runs against a version it can vouch for; it picks one current row as the seed, verifies the embedding stamps lesson 1.3 wrote, and uses that row's stored `doc_type` and `kind` as the combined filter. Then it calls `_firestore_fallback()` in-process with current off and on, and for every row that comes back it requires the tenant, both filters, no staging and, in the second mode, `current`. It writes what it saw to an evidence file and says plainly what it did not test: classification and answer quality are not its business, and it notes when the stored `doc_type` differs from the manifest, which on a lane whose uploads went through the bucket it does.

#### The code

#### Do it: the probe, then its evidence

The probe did in one command what steps 3 and 4 did by hand, against a source it first proved was the version the ledger holds: the combined filter held on the rung with current off and with it on, every returned row belonged to acme, carried both filter values, was not staged, and in the second mode was current. It refused nothing on your lane because the plumbing is right, and it said what it would not vouch for, which is the honest shape of a probe. The evidence file is the kind of artefact a release review reads: which key, which filters, which rows, in a file rather than in someone's memory. It sits inside the kit's clone; `git status` will show it, and it is yours to keep or delete.

### The tier from the rows: vector-status, backfill-vectors, and the rows that count the rung

The index's own count, the plan that would refill it from the rows without a model, and the usage rows that say which rung served the pool for the last hour.

#### Definition

Because Firestore holds every vector, the ANN tier is rebuildable from the rows: `backfill-vectors` reads every current row of a tenant, checks that its stored vector was made with the document profile, and streams the datapoints up, with no embedding call. It exists for two states, a worker deployed before the index did and an apply that lost its index, and it is the second half of the smoke's own advice. Without `APPLY=1` it is a plan: the current rows, how many would need a fresh document embedding, how many are invalid, and a note on what to pause during a repair. `vector-status` is the first half, the index's own datapoint count and the deployment's last sync, which is what a claim about Vector Search rests on. The last cell reads the usage rows the way lesson 2.3 did, grouped by the rung that served the pool: the pinned minutes of step 4 sit in a `firestore` row of their own.

#### The code

#### Do it: count the tier, plan its refill, read the rows by rung, Rs 0

The index reported its own count, a few thousand datapoints across the three tenants, synced; the plan found every current acme row already carrying a document-profile vector and nothing invalid, so a repair would upload them all and embed none; and the usage rows showed the last hour split by rung, the minutes acme spent pinned in a row of their own with the one unanswerable question from the emptied pool counted against it. That table is also where a day of silent fallbacks would show: a `vector` row whose answers came from beneath still reads `vector` here, which is why the smoke reads `vector_chunks` and not this column.

### What the rung costs, where it cannot go, and the policy that sends a tenant home

The rupee line, the two places the rung cannot serve, and the data-region rule run offline.

#### What it costs

#### Where the rung cannot go

Two places. It has no sparse leg, so `RETRIEVAL_MODE=hybrid` with `RETRIEVAL_BACKEND=firestore` is refused at startup by the validator lesson 2.2 ran, and a hybrid deployment that falls onto the rung is served dense for that request. And it holds only the kit's rows: a tenant whose pool comes from a managed store is on a different tier with its own copy, which is Module 7's, and the only part of that story this lesson needs is the policy below.

#### The policy that sends a tenant home

A tenant's `data_region` says where its text may be held: `any` lets the managed mirror copy its current versions abroad, `in` keeps it on the kit's rows in India, and a missing or unknown value is `in`, because an unreadable policy is the strict one. `retrieval_backend_for()` holds every request's backend against it: a managed pin for an `in` tenant is served from the kit's own rung instead, the deployment's if that is vector or firestore, otherwise Firestore, with `policy_fallback 1` on the row, which the warehouse sums into a column. The cell runs the two pure functions behind that decision offline; nothing leaves the machine.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

Nothing that serves traffic. acme's pin went to `firestore` and back to `vector`, where lesson 1.1 left it. A candidate revision of the API took no traffic and its wrong index name was replaced by the real one on the template before the tag was dropped; run `make plan` if you want Terraform's word that the service matches its declaration. The probe wrote `operator-evidence/firestore-combined-filters.json` inside the kit's clone. The questions you asked are usage rows, five of them under `firestore`. Lesson 2.5 rewrites the question before it reaches this pool and measures whether that helps; Module 3 then takes the pool into the prompt.

Netsetos GenAI on GCP · Module 2 Retrieval · Lesson 2.4 Test fallback without losing tenant or metadata filters · v5.0

Next: Lesson 2.5 Rewrite the query before retrieval, and measure it.
