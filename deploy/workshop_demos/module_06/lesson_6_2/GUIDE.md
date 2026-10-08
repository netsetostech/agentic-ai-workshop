# Lesson 6.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_6.2_Cache_Compare_WIX.html`, reviewed at blob `9863ad496e4fb405ef06d3ff2257a01666b35f6a`. Learners read that page on the course site; this guide keeps its prose.

DocuMind has two caches, and they hold different things. Gemini's context cache holds part of the model's input: acme's documents, packed once and read at a tenth of the price by every question for an hour. The answer cache holds the model's output: the answer and its citations, returned without retrieval or a model call when the same question comes back. You create the first with `make cache` and read `cached_tokens` on the next usage row. You switch the second on for a candidate, ask one question twice, and read `model_backend=cache` on the second row. Along the way you find out what the first one really does to the bill.

- Two caches: a prefix the model still reads, an answer the model never sees

- The words: context cache, cached_tokens, TTL, fingerprint, answer cache, the two rungs, scope

- Before you run anything: set up the shell

- The context cache: a pack, a cache, and the next answer

- The rows: what the context cache did to the bill

- The answer cache: a candidate that remembers answers

- Four asks: a miss, two hits and a paraphrase

- What each cache is holding, and the clean-up

- Why the caches are shaped this way, what they cost, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what each cache stores, the conditions under which each is used, and what each costs to keep and to use. Then you will prove both on your lane: `cached_tokens` on a usage row once acme's context cache exists, and `model_backend=cache` at a cost of zero on the second of two identical questions. You will also measure something the kit's comments do not say: attached the way the kit attaches it, the context cache makes each answer dearer, not cheaper.

### Two caches: a prefix the model still reads, an answer the model never sees

One makes reading cheaper. The other skips the reading.

The two caches store different things. The context cache is Gemini's explicit cache: part of the model's input, a long prefix, stored on Google's side and referenced by name. Every question still goes to the model, which still reads the prefix. It reads the cached tokens at a tenth of the input rate, the figure `cost.py` uses, and Google bills the cache's storage by the hour while it lives. The answer cache is the kit's own: the model's output, the answer with its citations, stored in Firestore. A hit returns that answer without retrieval, without the reranker and without the model. The usage row then says `model_backend` `cache`, with zero tokens and a cost of zero.

The context cache has hard rules. It must hold at least 4,096 tokens for the Gemini 3 family. It belongs to one model. It lives for 60 minutes by default, and there is no maximum, so something has to refresh or delete it. The kit creates it on the global endpoint, where Gemini 3 generation runs, and falls back to the regional client only if global refuses. It records the cache in `tenant_caches/{tenant}`, together with the tenant's corpus fingerprint. The API attaches it to a question only when three things hold: more than two minutes are left, the request's model is the cache's model, and the fingerprint has not moved since packing. Otherwise the answer runs uncached, and a moved fingerprint writes `cache_stale` in the log.

What the kit puts in it is added to the prompt, not swapped for anything. The pack is acme's 5 synthetic documents: 164,618 characters, about 41,154 tokens by the kit's own four-characters-a-token estimate. The generator's prompt does not change when a cache is attached. The system text, the retrieved chunks and the question are sent exactly as before, and the cache is one more keyword on the call. So the model reads the whole pack as well as the chunks. The cache makes those extra tokens cheap but not free. At the kit's flash rates, the pack adds about Rs 0.53 to every acme question; sent uncached, the same pack would add Rs 5.26. Step 4 measures this on your lane.

The answer cache has rules too, all of them about when an old answer is still this question's answer. The cache is kept per tenant, always. The entry's corpus fingerprint must still be the tenant's, and its scope must match: the filters, `top_k` and the prompt version. It must be less than 24 hours old. There are two rungs. The exact rung matches the same words, lower-cased with punctuation removed. The near rung reads the five nearest earlier questions by cosine similarity and takes the first at 0.95 or closer. Only an answer that is answerable, cited and not blocked is ever stored. The switch, `SEMANTIC_CACHE`, is off by default, because 0.95 is a guess until lesson 6.4 measures it.

A chartered accountant's office in March. The client's file stays open on the CA's desk for the afternoon. Every question still takes the CA's time, but nobody fetches and re-reads the whole file for each one, and the desk is paid for by the hour. That is the context cache. At the front desk, the receptionist keeps this morning's written answers. If the same client asks what was asked earlier, in the same words or very nearly, the receptionist hands over that answer with the same references, and the CA is never disturbed. That is the answer cache. It works only for that client, only if nothing in the file has changed since, and only until the end of the day.

#### Two caches, one question

The first box decides whether the context cache is attached to a call, the second whether the answer cache answers, and the third prices one question each way. Every rule is the kit's.

The first box runs `get()`, `stale_against()` and `generate_config_kwargs()` from `cache_manager.py`, the second `lookup()` from `semantic_cache.py` with the switch and the store rule from `main.py`, and the third `price()` from `cost.py` with its fallback rates. The build executed the kit's own functions on all 16, all 128 and 36 combinations, against stand-in Firestore records, and every box had to agree.

It shows the kit's rules, not Google's cache or your embeddings. The two paraphrase similarities are set by the panel, not measured: how close a real paraphrase lands is lesson 6.4's work. The prices are `cost.py`'s fallback table, which the kit uses when BigQuery's price table does not answer. The kit carries no storage rate, so that one is yours to enter from your model's price page.

### The words: context cache, cached_tokens, TTL, fingerprint, answer cache, the two rungs, scope

Twelve rows, each with the value it takes on your lane.

One distinction to hold: the context cache lowers the price of reading, and the answer cache removes the reading. The first still sends every question to the model, so every answer is new. The second returns an old answer, so its risks are an answer that no longer fits the question (a false hit) or no longer fits the facts (a stale hit). The threshold guards against the first; the fingerprint and the 24 hours guard against the second.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `tok`. Step 3 creates acme's context cache. The live API attaches it to every acme question until step 7 deletes it, an hour at most, and each of those answers costs a little more in the meantime. Step 5 creates a candidate with `SEMANTIC_CACHE=on` that serves no traffic. Its answers stay in `answer_cache` for 24 hours, and nothing else reads them.

### The context cache: a pack, a cache, and the next answer

One question without a cache, `make cache`, and the same question with one.

#### Definition

`make cache` runs `cache_admin.py create`. It builds the pack from the kit's own copies of acme's synthetic documents: every `.md` file under `evals/corpus/acme/` that has no PDF twin. The generator's system text becomes the cache's system instruction, so the cache and the request agree on the rules. The cache is created with a one-hour TTL, and the record written to `tenant_caches/acme` keeps the ledger's fingerprint at packing time. From then on, every acme answer goes through `generate_config_kwargs()`. That costs one Firestore read of the record and one of the ledger, and it returns `cached_content` when the cache qualifies. The first cell below defines `ask91`, a small function that asks acme one question and prints the fields that show a cache at work. It notes the time for step 4 and asks once, before any cache exists. The question is a golden row whose answer is in the handbook, which is also in the pack.

#### The code

#### Do it: the question, uncached

#### Do it: the cache

#### Do it: the same question, with the cache

The first answer's `tokens_in` is the whole RAG prompt: the system text, the chunks the reranker kept, and the question. `make cache` then packed the 5 documents and printed where the cache landed. It should say `global`, the endpoint that serves generation; a regional location means global refused the create. It also printed Google's count of the cached tokens. The second answer is the same question with the cache attached. `cached_tokens` equals that count, and `tokens_in` grew by the same number, because the prompt itself did not change. If `cached_tokens` is 0, the panel's first box lists the reasons a cache is not attached.

### The rows: what the context cache did to the bill

The usage rows of both answers, priced the way the API prices them.

#### Definition

Every answer writes one usage row to the API's log. `tokens_in` is the whole prompt, the cached part included, and `cached_tokens` is the cached part. `price()` charges the uncached tokens at the input rate, the cached ones at a tenth of it, and the output at the output rate. The cell reads every acme row written since the first ask and prints the revision, the backend, both token counts, the cost in rupees at 85 to the dollar, and the latency. Cloud Logging can take half a minute to show a row, so if one is missing, run the cell again.

#### The code

#### Do it

The second row carries `cached_tokens`: this lesson's first proof. Now compare the two costs. The cached row is dearer, by about a tenth of the pack's full price. That is roughly Rs 0.53 at the kit's flash rates, against Rs 0.49 for the whole uncached answer in the expected block. The cache did exactly what it promises. The pack's tokens cost a tenth of their full price, Rs 5.26 if they had been sent uncached. But nothing was sent uncached before: the retrieved chunks carried the context, and they still do. Compare the latency on the two rows yourself, because the model now reads some forty thousand more tokens for each answer.

A context cache saves money when the same long prefix would otherwise travel uncached with every call. That covers a policy manual every answer must follow, a long contract that is questioned all afternoon, or a set of examples each prompt repeats. Then it replaces full-price tokens with cheap ones, and the saving has to beat the storage bill. The kit's cache does not replace anything: the pack is added beside the retrieval. What it buys is grounding. The model sees every acme policy, even when retrieval misses the right chunk, and that costs about Rs 0.53 an answer plus storage. Whether that is worth it is a quality question, and lesson 4.4's controlled comparison is how to answer it.

### The answer cache: a candidate that remembers answers

The lookup, the store rule, and a revision with the switch on.

#### Definition

With `SEMANTIC_CACHE=on`, `/v1/query` embeds the question once, as it does anyway for retrieval, and asks `lookup()` before any retrieval happens. The exact rung compares `qhash`es; the near rung asks Firestore's vector index for the tenant's five nearest earlier questions. An entry counts only if `_alive()` agrees: the same fingerprint, the same scope, not expired. A hit becomes a response carrying the stored answer and its original citations, with `backend` `cache` and a cost of 0. On a miss the question runs as usual. Afterwards `_semantic_store()` keeps the answer, but only if it is answerable and cited, and never if Model Armor blocked it. The switch belongs to one revision, so the candidate gets it and the live revision keeps it off. Both revisions share the same Firestore, and acme's context cache from step 3 is still alive, so the candidate's model calls carry it too.

#### The code

#### Do it

Cloud Run built a revision with `SEMANTIC_CACHE=on` and gave it the `candidate---` address. Every other request still reaches the live revision, whose switch stays off. The target recorded the revision's name in `.candidate-revision`, and step 7 deletes that file. The candidate accepts the same token as the live service, because the API checks every token against its canonical URL.

### Four asks: a miss, two hits and a paraphrase

One question four ways, then the rows.

The first ask is a miss: the candidate has never seen the question, so it retrieves, calls the model and stores the answer. The second is the same words, for the exact rung. The third is the same words in lower case without the question mark, which `qhash` treats as identical. The fourth says the same thing in other words. It is a hit only if its embedding lands within 0.95 of the first question's; otherwise it is a miss, and its own answer is stored beside the first.

The second and third asks came back from the answer cache. Their rows read `cache` with zero tokens and Rs 0, and that is this lesson's second proof. They were not free in every sense: their latency is the embedding plus a few Firestore reads. That is far shorter than a model call, but not zero, and neither cost appears on the row. The first ask shows both caches in one row: the answer cache missed, the model ran, and the context cache made `cached_tokens` non-zero. The fourth row tells you where your paraphrase landed. Lesson 6.4 measures that line on labelled pairs before anyone relies on the near rung.

### What each cache is holding, and the clean-up

The record behind the context cache, the entry behind the hit, and both caches put away.

The cell prints `tenant_caches/acme`, then the answer-cache entry for the question's words. It uses the kit's own `qhash`, imported from `services/rag-api`, so the key is computed exactly as the API computes it.

The two records show where each cache keeps its weight. For the context cache, Firestore holds only a pointer and a few facts, and the pack's forty-odd thousand tokens sit on Google's side, billed by the hour until they expire or are deleted. For the answer cache, Firestore holds everything: the answer, its citations and the question's 768-number embedding. That costs Firestore storage and reads, for 24 hours. The clean-up removes the candidate's tag and recorded name, and deletes the context cache. The next acme question to the live API finds no record and runs uncached at once.

The answer-cache entries stay until their `expire_at`, and Firestore's TTL policy deletes them some time after that. Nothing reads them in the meantime, because the live revision's switch is off. The candidate revision stays in the service's list with no traffic. The service's configuration says `SEMANTIC_CACHE=on` until the next deploy or candidate sets it: `make up` and `make candidate` both pass it, and both default it to `off`.

### Why the caches are shaped this way, what they cost, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Per tenant, always. An answer cache keyed on the question alone would serve one customer's answer to another. It would look like a performance win right up until someone noticed.

- Per fingerprint, and five candidates. Every entry carries the fingerprint it was answered under, so a reindex makes every earlier answer a miss without scanning anything. The near rung reads five neighbours, not one, so a stale twin of the question cannot hide the current entry.

- 0.95, not 0.92. A looser threshold answers "what is the probation period" with the notice period's answer: a wrong answer, served fast. The kit starts tight and leaves the switch off until 6.4 measures the line.

- Only the contract, and only a good one. An entry stores the answer, citations, confidence and answerable flag, never the envelope of tokens and cost. A refusal is not worth keeping for a day, and a blocked answer is not worth keeping at all.

- A failing cache is a miss, never an error. A context-cache problem returns no keyword and the answer runs uncached. An answer-cache failure logs `semantic_cache_failed` and the question runs as usual. Either way the answer is still one retrieval away.

- A context cache is one model's. A routed tier or a tuned endpoint is never handed another model's cache, which the API would refuse.

- The exact rung still pays for one embedding. The API embeds the question before the lookup, because on a miss retrieval needs the same vector. The hit saves the reranker and the model, not the embedding.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The context cache is added to the prompt, not substituted for anything. `cache_admin.py` says that without a cache "every answer paid full price for its context". With the cache, every answer still pays full price for the retrieved context, plus a tenth of the pack's price. Step 4 measured it.

- The pack is the kit's copy of the documents, not the tenant's corpus. `pack_for()` reads `evals/corpus/acme/`. After a reindex with a new version, such as lesson 1.6's handbook, `make cache` packs the old text again, and the fingerprint calls it current. The cache can then contradict the index it sits beside.

- Nothing refreshes a cache. `cache_manager.py`'s docstring names a Cloud Scheduler job that calls `refresh()` while a tenant is active. `terraform/` defines four scheduler jobs, and none of them touches caches. A cache simply expires after its hour, unless `make cache CACHE_OP=refresh` extends it.

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it on your lane.

acme's context cache lived from step 3 to step 7 and is deleted. `tenant_caches/acme` is gone, and the live API answers acme uncached again. `documind-api` has one more revision, which serves no traffic and has no tag. The service's configuration says `SEMANTIC_CACHE=on` until the next deploy sets it back, and `.candidate-revision` is gone. `answer_cache` holds this lesson's one or two acme answers until they expire in 24 hours. The usage rows of three or four answered questions and two or three hits. Lesson 6.3 tests what makes each cache miss (a reindex, a changed filter or prompt version, the clock) and gets a hit again after `make cache`.

Netsetos GenAI on GCP · Module 6 Context and memory · Lesson 6.2 Compare context caching and answer caching · v5.0

Next: Lesson 6.3 Test cache scope, configuration changes and freshness.
