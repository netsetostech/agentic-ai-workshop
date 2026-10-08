# Lesson 2.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_2.1_Query_Filters_WIX.html`, reviewed at blob `eec99fabc474ce0ab221815772043a8d9d45a33f`. Learners read that page on the course site; this guide keeps its prose.

Module 1 put the records in place. This module reads them. A question arrives as text and leaves the API as a vector; the caller's identity, not the request, decides whose documents it may search; two named filters may narrow the search and anything else is refused before any work is done; and the index is asked with restricts that make one index serve three tenants without a leak. You will embed a question yourself and compare a direct index search with the API's citations, ask the same question of two tenants with one identity and get two answers, send the wrong filters and read the 400s, and read the stages block that says which store answered.

- What retrieval sees

- The words: query vector, identity, roster, filter key, restrict, pool, stages

- Before you run anything: set up the shell

- Verify the deployed index and select the backend

- The question's vector: direct candidates and API citations

- Authorized: the tenant comes from identity, and one index serves three

- Filters: two keys, a 400 for everything else

- The restricts, the per-request backend, and the stages block

- Current is the ledger's filter, never the caller's

- The cache shares the vector, the pool is not the answer, and what a question costs

- Verify it yourself: the checklist

- Finish: restore the saved tenant pin

You will learn how a question becomes a vector under the query profile of the same declared model the worker stamped on every row, why the tenant a request may search is taken from the verified identity and the roster rather than from the request, which two filter keys a caller may send and why an unknown key is a 400 rather than an empty result, and how the tenant, the ledger's `current` and the caller's filters reach the index as restricts. Then you will prove it on your lane: inspect the index candidates with your own call, ask two tenants the same question, send four filters and read four verdicts, and read a full `stages` block.

### What retrieval sees

A vector instead of a question, an identity instead of a claim, and predicates instead of trust.

Retrieval never sees the question; it sees its vector. The API embeds the question once, under `RETRIEVAL_QUERY`, with the model and version the worker stamped on every row in lesson 1.3, and that one vector is used twice: the answer cache looks it up first, and the retrieval sends it to the index. The vector is 768 numbers made to be compared with the document vectors on the rows, which is why the pairing matters: a question embedded under the document profile, or with another model, would still return a ranked list, and the list would be wrong. The API reads the pair from the same environment variables the worker does, so the two cannot drift apart without a deploy.

The tenant comes from who is asking, never from what they ask. A request names a tenant, but the API does not believe it. The identity comes from the IAP assertion or the bearer token, verified for this service's own audience; then the roster in Firestore is asked one question: is this email on this tenant's roster? A yes proceeds; a no is a 403 before any embedding, any index call, any model. The body field that once named a user is accepted and unread, because a user named in the body is a header in disguise. The same identity may sit on several rosters, and then the same question to two tenants gets two answers from two corpora in one index, with nothing crossing between them.

Filters are predicates on the corpus, and there are two. A caller may send `doc_type` and `kind`, each a string; `doc_type` may instead be a list of up to five classes, any of which a row may carry. They become restricts on the index query and pre-filters on the Firestore rung, the same predicate on both paths. Any other key is refused with a 400 that names the allowed keys, because a key that filters nothing on one path and everything on another is a typo that would read like an honest "nothing found". Two things are never the caller's to filter: the tenant, which is the roster's, and `current`, which is the ledger's.

A records room with a badge reader. You do not tell the clerk which company's files you may see; your badge does, and the clerk checks it against the register before opening a drawer. Your question is not read out loud either: it is written on a card in the room's own code so the clerk can match it against the cards on the files. You may ask for a drawer by type or by kind, and the clerk will honour those two labels, but ask for "the files of the other company" and you are refused at the counter, not sent to an empty drawer. And a file that has been superseded is never handed over, whatever you ask, because the register, not you, decides which version is current.

#### Walk a request through the gates

The player below is the API's query handler as a sequence of gates, with your lane's real data: the identity you send, the tenant you name, and the filters. Pick a combination and read the verdict at each gate, the restricts that would reach the index, and the answer the two handbooks would give. The travel cap is Rs 40,000 in acme's handbook and Rs 25,000 in zeta's, which is what makes one question prove the tenant restrict.

The question is always "What is the per-trip cap on travel reimbursement?". The gates are the handler's own order: Cloud Run's door, `verify_iap`, `enforce_membership`, `check_filters`, then the restricts and the pool. The `doc_type: policy` case is real: the worker stamps a plain upload `unknown` (lesson 1.1), so the filter matches nothing and the API refuses with an empty pool rather than guessing.

### The words: query vector, identity, roster, filter key, restrict, pool, stages

Nine words, each with the value it takes on your lane.

Three of these words were written by the worker and are now read: the stamp behind the query vector, the restricts on the datapoint, the flag on the row. Retrieval adds only the identity and the two keys, and refuses everything else at the door.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a one-line entry in the kit's `mk/ingestion.mk` or `mk/lifecycle.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Select the backend after checking the index

The preflight below saves the original Acme pin and selects vector only after its endpoint check passes. Restore the saved pin at the end of the lesson; running a restore command here would immediately undo the demo setting.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head; step 3 makes the difference visible.

### Before the demo: verify the index, then select the tenant backend

`404 Index 'documind_chunks_nonesuch' is not found` means the requested deployed-index ID is absent from that endpoint. The old names box copied this value from the API without checking it. A shell export alone would leave the API unchanged. The direct Python call raises the error; the API can catch it and answer through Firestore, so a health check or an answer is not proof that Vector Search served the request.

There were two other demo traps: selecting `rag_engine` immediately after `vector` undoes the tenant setting, and a manual query with only the tenant restrict differs from an API with `RETRIEVAL_CURRENT_ONLY=on`. This page now validates the endpoint first, saves the original pin, matches the current-version filter and restores the pin only at the end.

#### Where the index comes from

`terraform/vector.tf` declares the index, its endpoint and the deployment ID `documind_chunks_v1`. The infrastructure apply in `make up` creates them; `services/ingest/indexer.py` fills the index with `upsert_datapoints()`. The Python cell below only embeds a question and searches the existing deployment. Read the actual endpoint before deciding that an index needs creating.

#### Run first: check the serving revision and save the original pin

Run in `$DEMO_ROOT`. This reads the single revision receiving traffic, checks that its deployed ID exists, saves only the relevant settings under `operator-evidence/lesson51/`, and then selects `vector` for Acme. Empty optional settings take their code defaults. It stops before any embedding or tenant change if the deployment is invalid. A split-traffic service needs a chosen revision before this single-revision demonstration can proceed.

Continue only after PASS. Keep Acme on `vector` through steps 3–9. The API environment's `RETRIEVAL_BACKEND` is a default; the tenant pin overrides it. If step 3 still reports the old backend, wait for that one-minute cache to expire, then retry.

This is a configuration repair for an existing index, not an index-creation step. Read the ID from the intended Terraform state and prove that it is deployed on the same endpoint. The following block refuses an endpoint mismatch or missing deployment. It creates a corrected API revision and routes 100% of the demo service's traffic to it. Other environment variables are retained; do not rerun the full infrastructure deployment to fix this one setting.

If Terraform has no outputs or the endpoint has no deployed indexes, return to the infrastructure setup and inspect its plan and deployment status. Exporting a name does not create an index. Cloud Run environment-variable updates and revision traffic routing describe these operations.

### The question's vector: direct candidates and API citations

The one function that embeds a question, and a cell that does what the API does and compares.

#### Definition

`embed_query()` sends the question to the embedding model with `task_type: RETRIEVAL_QUERY` and `output_dimensionality: 768`, on a regional client, with `settings.embed_model`, which is the same `EMBEDDING_MODEL` the worker read when it stamped the rows. The handler calls it once and passes the vector to both the answer cache and `retrieve()`. Everything after that is a search for the rows whose stored vectors point the same way, under the restricts of the next steps; you can inspect dense candidates yourself using the deployed model, pool size and tenant/current restricts. The API can then add hybrid or graph candidates, drop retired rows and rerank evidence; its citations need not have the direct search's order.

#### The code

#### Do it: embed, search, compare

Run the preflight first. This cell uses its verified settings, checks the endpoint and Acme pin again before paying for an embedding, searches with the same tenant/current restricts, then compares candidate IDs with the API citations. Overlap and first-citation order are observations, not pass/fail assertions. Hybrid retrieval, graph candidates, current-version checks and reranking can change the final selection.

You embedded the question with the API's configured model, searched its verified deployment with its tenant/current restricts, and inspected the returned rows. The API then reported its own backend and how many pooled chunks came from Vector Search. A backend label of `vector` alone is insufficient: the fallback path can still use Firestore. A different first citation does not invalidate the search; the API can select and reorder evidence after retrieval.

### Authorized: the tenant comes from identity, and one index serves three

The two checks before any work, and the question that gets two answers.

#### Definition

The handler's first line is `enforce_membership(user["email"], req.tenant_id)`, and `user` came from `verify_iap`: the IAP assertion when a person came through IAP, otherwise the bearer identity token verified for this service's own URL, otherwise a 401. Membership is one Firestore read on the roster, and a miss is a 403 that says so. What the request claims about itself is never consulted: `user_id` is accepted and unread, and an `x-user-email` header is only honoured in the dev mode that no deployed service runs. Because the tenant restrict is then built from the request's `tenant_id` only after the roster has allowed it, one index holds three tenants' datapoints and a caller can only ever search the ones the roster lets them name.

#### The code

#### Do it: one identity, two tenants, one outsider

The UI's service account, which your `tok()` impersonates, sits on all three rosters. The first two calls send it the same question against acme and zeta; the third sends the outsider's token; the fourth sends the UI's token with a header that claims to be someone else. Each line shows the HTTP status. A request turned away for a reason that passes, a model quota hit, a Cloud Run scale-up or a dropped connection, is asked once more after five seconds; anything else prints the reason the service gave instead of a traceback.

One identity, two tenants, two figures, each cited to its own handbook, from one index. The outsider, on no roster, was refused before the API embedded anything. The false header was ignored: the identity is the token's, and the roster decided what that identity may search. This is the isolation the golden set's `iso-` rows assert every time the gate runs, and it holds not because the tenants' rows are in different stores but because every query carries the tenant as a restrict the caller cannot set.

### Filters: two keys, a 400 for everything else

The keys the caller may send, the two ways to send them wrong, and the one honest filter that finds nothing.

#### Definition

`check_filters()` runs before any work: an unknown key is a 400 that names the allowed keys, a value that is not a non-empty string is a 400 that names the key. `doc_type` alone may also be a list of one to five non-empty strings, any of which a row may carry; the API sorts it and drops repeats in place, and a one-class list becomes that class, so one set of classes is one answer-cache scope whatever order it was sent in. A list for `kind` is a 400 (`filter kind takes one string, not a list: only doc_type takes a list`): its branches in the retriever are scalar and differ by path. The allowed keys are the two the worker stamps on every datapoint and every row, so a filter means the same thing on the index path and on the Firestore rung. A filter that matches nothing is not an error: the pool is empty, and the API refuses in the contract's own shape, `answerable: false`, no citations, no model call. On your lane `doc_type: policy` is that case, because the worker stamps a plain upload as `unknown`.

#### The code

#### Do it: four filters, four verdicts

Two requests were refused at the door with the reason, before an embedding was made; a filter that names the tenant is the roster's business and a number is not a value. The third was a valid filter that no row satisfies, and the API said so without guessing: an empty pool, no model, no cost. The fourth narrowed the search to text rows, which is every row on this lane, and the answer was the ordinary one. A filter is a predicate on the corpus, and the corpus, not the caller, decides whether it matches.

### The restricts, the per-request backend, and the stages block

What reaches the index, which store the request went to and why, and the clocks and counts every answer carries.

#### Definition

On the vector backend `_dense_retrieve()` builds the restricts in a fixed order: the tenant, then `current` when `RETRIEVAL_CURRENT_ONLY` is on, then each caller filter as a namespace. Under hybrid mode the same list goes with the sparse vector, and the tenant restrict is inserted exactly once. The ids come back with scores and are hydrated from Firestore in the index's order, thirty per query, each marked `found_by: vector`. Which backend a request goes to is decided per request: the deployment's default, unless the tenant pins another, and a managed store is refused for a tenant whose text must stay in India, with `policy_fallback: 1` on the row. The answer's `stages` carries the decision and the clocks.

#### The code

#### Do it: the tenant's pin and policy, then a full stages block, Rs 0 plus one question

The tenant is pinned to the kit's own index (this lesson's verified preflight did that) and its data may be held anywhere, so no policy fallback applied and the request went where the pin said. The stages block is the answer's own account: the retrieval took the first clock, pooled twenty candidates, all from the index; the reranker took the second and cut them to the three you asked for; the model took the third. A day of these blocks on the usage rows is how lesson 2.3 reads p95 per stage; one of them is how you read a single answer.

### Current is the ledger's filter, never the caller's

Two mechanisms keep a retired version out of an answer, and the handbook's three versions prove it.

#### Definition

Lesson 1.7 left three versions of the handbook on your lane: version 1 current, revision 2 and revision 3 retired with their vectors still on the rows. Nothing a caller sends can reach the retired ones. On the index they are gone: the worker removed their datapoints at the swap, and when `RETRIEVAL_CURRENT_ONLY` is on the query also carries `current: true`. On the Firestore rung the same setting adds the equality filter. And whichever path answered, `prefer_current()` drops any row whose flag is false before the reranker sees it, and `newest_per_source()` keeps one version per source. The revisions said 90 days; the answer says 60, and the citation's row is current.

#### The code

#### Do it: the question the revisions answered differently

Three rows for one clause, two of them saying 90 days, and the answer said 60 with a citation to the one current row. The caller sent no filter for that and could not have: `current` is not an allowed key, and the two retired rows are out of the index and out of the pool by the ledger's decision alone. This is what "one current version" from lesson 1.7 means at the reading end.

### The cache shares the vector, the pool is not the answer, and what a question costs

Why the handler embeds exactly once, what the two sizes on a request mean, and the rupee line.

#### One vector, two uses

The handler embeds the question once and hands the vector to the answer cache before the retrieval. With `SEMANTIC_CACHE=on` the cache looks for an earlier, near-enough question of the same tenant under the same corpus fingerprint and the same scope (the filters, the `top_k`, the prompt version); a hit is served with `cache_hit: semantic`, no reranker, no model, and the vector was the only cost. A miss goes on to retrieval with the same vector. Because the cache is keyed on the fingerprint from lesson 1.7, a reindex makes every earlier answer a miss without anyone clearing anything; and because the scope includes the filters, a filtered question never gets an unfiltered answer.

#### Two sizes

A request's `top_k` (default 5, at most 20) is how many citations the caller wants back. `TOP_K_RETRIEVE` (20 by default) is how many candidates retrieval pools for the reranker. The reranker orders the pool and cuts it to `top_k`; the model reads what survives. Asking for three citations does not make retrieval cheaper, and asking for twenty does not make it wider; the pool is the knob the ablation in lesson 2.2 moves.

#### What a question costs

The asymmetry to remember: everything that decides whether a question may be asked at all costs a read, and everything that decides what it costs happens after. The API refuses cheaply and spends only on questions it has already authorized.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

### Finish: restore the saved tenant pin

Run only after steps 3–9. Restore the value saved before the demo, which may be `rag_engine`, another backend or `default`. The last option removes the explicit pin. Do not assume every lane originally used RAG Engine, and do not place this command beside the setup command.

The preflight saved settings and the original Acme pin under `operator-evidence/lesson51/`; the demo selected `vector`, and the final block restored that saved pin. The query cells read the corpus and created query embeddings without changing document vectors. If you used the optional repair, the corrected API revision and deployed-index setting remain in place. Lesson 2.2 compares dense and hybrid retrieval.

Netsetos GenAI on GCP · Module 2 Retrieval · Lesson 2.1 Apply query embeddings and authorized filters · v5.0

Next: Lesson 2.2 Compare dense and hybrid retrieval.
