# Lesson 3.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_3.5_Structured_Answers_WIX.html`, reviewed at blob `be4ba0adff0eefafe272eebc8c9d04137e150d3b`. Learners read that page on the course site; this guide keeps its prose.

Lesson 3.4 packed the evidence. This lesson is what comes back. The model is not asked for an answer in prose; it is asked to fill a schema, `ModelDraft`, whose citations are the `[Source N]` numbers it read in the context and the words it relied on, because those are the only things it can see. `resolve()` turns that draft into the contract every module passes along, `RAGAnswer`, with real chunk ids, pages and scores it never saw, dropping a number that was never packed. A refusal has the same shape, `answerable false` and no citations, and it comes in two kinds: the model's, when the packed evidence does not answer, and the API's own, when nothing was retrieved at all and no model is called. Every answer carries what it cost, in dollars and in rupees, and the model that produced it is a setting: a name served from the global endpoint, or a tuned endpoint served from wherever its path says. You will validate and resolve drafts offline, read one lane answer field by field and check its quotes against the rows, watch three refusals differ in their envelopes, make the model's call yourself with the kit's own schema, and shrink the answer's reserve on a candidate to see the failure that is not a refusal.

- Three moments of one contract, and why the model cites by number

- The words: draft, citation, contract, envelope, schema, thinking, confidence, refusal, repair, price

- Before you run anything: set up the shell

- The contract offline: drafts that pass, drafts that fail, and the resolver on the kit's chunks

- One answer from the lane, field by field, with every quote checked against its row

- Three refusals: the model's twice, the API's once, and how their envelopes differ

- The model call by hand: the schema, the thinking, the usage, the price

- The model as a setting: the global client, a tuned endpoint, a pin and a router

- What an answer costs, and the failure that is not a refusal

- Verify it yourself: the checklist

You will learn why the answer contract has three moments rather than one, how structured output pins the model to a schema, how a draft's numbers become citations against the packed list, what a refusal looks like from the model and from the API, and where the model itself is chosen. Then you will prove it on your lane: resolve drafts offline, read one answer and check its quotes against the rows, compare three refusals, call the model with the kit's schema, and force the 502 that a cut-off answer produces instead of a fake refusal.

### Three moments of one contract, and why the model cites by number

What the model is asked for, what a caller receives, and what every module hands to the next; a refusal in two kinds; a price on every answer.

The contract has three moments because they are three different times. `ModelDraft` is what the model is asked for: an answer, citations by `[Source N]` index with the exact words relied on, a confidence and an `answerable` flag. It never knows a chunk id, a page or a score, and asking it for one invites it to invent one. `Citation` is what a caller receives: `resolve()` maps each draft number against the packed list, the chunks the model actually saw after the budget, and fills in the id, the source, the page, the quote cut to 500 characters and the ranker's score; a number outside the packed list is dropped, not raised, because the answer is still worth returning and a citation to a passage that was not in the context is not a citation. `RAGAnswer` is the contract every module passes along, answer, citations, confidence, answerable, and nothing about tokens or latency; the API adds those in its own envelope, `RAGResponse`. Until 5 September there were three shapes of a cited answer across the course; the shared module is why there is one, and two notebooks reproduce its classes word for word.

Structured output pins the model to the schema. `_call()` asks for JSON with `response_schema=ModelDraft`, a low thinking level and no temperature, because the 3.x family ignores it. The SDK parses the reply into the class; when it cannot, `_draft()` reads the text itself and validates, and one violation is repaired rather than failed: a quote longer than the draft's 200 characters is trimmed and logged as `generation_repaired`, because nine correct statute answers were once thrown away for an excerpt that was merely long. Anything else that fails validation is `generation_invalid`, and a reply that cannot be parsed at all becomes a 502, never a refusal, so that plumbing is counted as plumbing.

A refusal has one shape and two origins. Rule three of the system prompt tells the model to set `answerable` false when the context does not contain the answer; that refusal costs a model call, carries no citations and low confidence, and its usage row says so with `unanswerable_flag 1`, which the alert counts. When retrieval finds nothing at all, the API writes the same shape itself, `empty_pool_answer()`, with backend `none`, zero tokens and zero cost, because a model call over no evidence buys an invented answer or a refusal at full price. Every answer that did call a model carries its tokens and `cost.price()`'s two figures, dollars and rupees at 85, so that finance never re-does the conversion. And the model is a setting: a name is served from the global endpoint, a tuned endpoint from the location its path names, and a tenant's pin or the router can choose per request.

The examiner's answer sheet. A candidate answers on a numbered sheet and may refer only to the exhibits laid out on the desk, by their numbers; the candidate never sees the archive's catalogue. A clerk then rewrites each reference as the archive would: the catalogue id, the page, the exact line, the exhibit's grade. A reference to exhibit nine, when seven were laid out, is struck through, not sent back. A candidate who writes "the exhibits do not say" gets the honest mark for it, and the sitting is still billed. When the invigilator finds no exhibits to lay out at all, the sitting does not take place, and the sheet records that in the same words, for nothing. The mark sheet always shows the fee in rupees beside the dollars.

#### The resolver: a draft in, the contract out, on the kit's own chunks

The box holds a draft as the model would return it. The bench validates it against the contract's rules, repairs an over-long quote the way `_draft()` does, resolves the numbers against two packed chunks from the kit's handbook, and prints the `RAGAnswer` and its envelope, priced at the model's rates. The cases change the draft into the shapes that matter: an out-of-range number, an over-long quote, a value outside the schema, the model's refusal, and the empty pool that never reaches a model. One check the kit does not make is added beside each citation: whether the quote's words are in the chunk, which is what rule five asks of the model.

The packed chunks are the handbook's NP-03 and PB-02 sections through the kit's chunker, with the ids that chunker gives them; on the lane the ids are the worker's `tenant:sha256#position` and the score is the ranker's. The rules are ported from `shared/documind_schemas.py`, `generator._draft()`, `main.empty_pool_answer()` and `cost.price()`; the token numbers are yours to type from step 4.

It is not the model: the drafts here are written by hand, and what a model writes for a given context is step 6's business. Its validation is a port of the schema's rules, not pydantic itself; step 3 runs the real classes, offline, with the same cases.

### The words: draft, citation, contract, envelope, schema, thinking, confidence, refusal, repair, price

Ten rows, each with the value it takes on your lane.

One rule to keep in view: the model numbers what it saw, and the packed list is the only list those numbers mean anything against. A draft resolved against the pool before the budget shifted every citation after a drop by one, silently, and that is the bug the resolver was written to close.

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

The model, its location, the tuned base, the router, the backend, the prompt version and the answer's reserve live in the API's environment, each with a default the page names; a name the service does not set is unset rather than exported empty, because steps 3 and 6 import the kit. `/version` says what is actually serving.

### The contract offline: drafts that pass, drafts that fail, and the resolver on the kit's chunks

The three classes imported from the shared module, six drafts through them, one resolution with a dropped number, the model's refusal and the API's, for Rs 0.

#### Definition

The shared module is pure pydantic: the three classes and `resolve()`, importable anywhere the kit is, which is why the cell needs no cloud. It packs two handbook sections with the kit's chunker, writes a draft by hand that cites sources 1, 2 and 7, and resolves it: two citations come back with the chunks' ids and pages, the seventh is dropped. Then three drafts the schema refuses, a zero-based source, a confidence outside the three words, a quote over the limit, each with the field pydantic names. The last two lines are the two refusals side by side: the model's, resolved like any draft, and the API's constant for an empty pool, read from main.py. The output below was produced when this page was built by the same code on the same files.

#### The code

#### Do it: six drafts, one resolution, two refusals

The real classes did what the bench in step 1 imitated: two numbers became citations carrying ids and pages the draft never held, a third number was dropped because nothing was packed at that position, and the scores read 0 because no ranker stamped these offline chunks. Pydantic refused the three bad drafts by naming the field, which is what `_draft()` logs as `generation_invalid` when a model does the same, except for the over-long quote, which it repairs first. And the two refusals had the same four fields, with only their words to tell them apart; the envelope, next, is what really separates them.

### One answer from the lane, field by field, with every quote checked against its row

The contract and the envelope printed apart, the [N] marks against the citations, and each citation's row read from Firestore to see whether the quote's words are there.

#### Definition

The response is the contract plus the envelope, and the cell prints them apart. Then it does two checks the API does not: it lists the `[N]` marks in the answer's text and compares them with the citations that came back, and for each citation it reads the chunk's row from Firestore and asks whether the quote's words, whitespace folded, occur in the row's text. Rule five asks the model for the clause that answers, at most twenty-five words, exact; the contract stores up to 500 characters of it; nothing in the API verifies the words. A False on that line is the model paraphrasing where it was told to quote, which lesson 7's eval does not score either, and which is worth knowing about your model before you trust a quote in the UI.

#### The code

#### Do it: one question, two halves, three rows

One JSON came back with the contract's four fields and the envelope's eight. The marks in the text were the citations' numbers, because the model cited the packed positions and the resolver kept the numbers whose chunks existed; each chunk id opened a real row, the page was `None` because a markdown source has no pages, and the scores were the ranker's from lesson 2.3. The quotes were found in the rows, which is rule five obeyed; had one been missing, you would have learned something about your model that no other line on this lane reports.

### Three refusals: the model's twice, the API's once, and how their envelopes differ

Globex asked about a policy it does not have, acme asked about a year its report does not cover, and a filter that matches nothing; the same four fields, three different envelopes, three rows the alert counts.

#### Definition

The golden set keeps refusal rows on purpose: a question whose tenant has no such document, so a confident answer would mean the model borrowed another tenant's; a question about a year outside the report, so an answer would be an extrapolation. On both the pool is full, the model reads it and applies rule three, and the envelope shows a model call with its tokens. The third case never reaches a model: a `doc_type` filter that matches no row empties the pool, and the handler writes the refusal itself with backend `none` and cost zero, as lesson 2.1 first showed. All three rows carry `unanswerable_flag 1`, and the alert that counts them cannot tell the three apart, which is why the row also carries the backend.

#### The code

#### Do it: three questions, three envelopes, three rows

Three refusals, one shape. The first two cost a model call each because the pool was full and only the model could tell that it did not answer; their words are the model's, and both are correct refusals that a confident answer would have turned into a fabrication. The third cost nothing and cited nothing because there was nothing to read, and the handler said so in the contract's own words. On the rows the alert sees three flags; the backend column is what tells a day of empty pools from a day of honest model refusals, and only the first of those is a retrieval problem.

### The model call by hand: the schema, the thinking, the usage, the price

generate_content with the kit's own config and the kit's own schema on two packed chunks, the parsed draft, the resolution, and the usage priced as the API would.

#### Definition

`_call()` is one `generate_content` on the client the model needs, with the system prompt, the packed context and the question as one text part, the packed figures as image parts when a chunk is one, and a config of five lines: JSON as the mime type, `ModelDraft` as the schema, the reserve as `max_output_tokens`, a low thinking level, and the tenant's cache when one is live. No temperature, top-p or top-k, because the model ignores all three and a knob that does nothing reads like one that does. The reply's `parsed` is the draft; its `usage_metadata` carries the prompt tokens, the answer's and the thoughts', and the cached count. The cell does the same call with the same schema from the kit's shared module, on the global client, for two handbook sections packed by the kit's packer, then resolves and prices what came back.

#### The code

#### Do it: the same call, from the shell

The model was called the way the API calls it, and it returned the class, not prose: the SDK parsed the JSON into `ModelDraft` because the schema was in the config, and the draft's `[1]` became the chunk id the chunker gave NP-03, with a page of 1 because the kit's markdown mirror numbers its sections and a score of 0 because nothing ranked these two. The usage showed the three counts the row sums: the prompt, the answer, and the thoughts the model spent before it, which are billed as output whether or not you see them. The price was the kit's own arithmetic on those counts, in both currencies.

### The model as a setting: the global client, a tuned endpoint, a pin and a router

Where the model is decided per request, why a name and an endpoint path need different clients, and the three settings that can change the model without a code change.

#### Definition

The model for a request is decided in `choose_for()`: a tenant's pin in `tenant_settings` first, else the router's tier when `ROUTING` is on, else `GENERATOR_MODEL`. The value then chooses its own client: a model name is served from the global endpoint, where the 3.x family lives, and a tuned model is an endpoint path, `projects/.../locations/.../endpoints/...`, served from the location the path names, because the global client answers 404 for it; `GENERATOR_LOCATION` can override that without a code change, which the first live tuning job needed when its endpoint landed in the `us` multi-region. A tuned endpoint is priced as its base, `RAG_MODEL_BASE`, and the cache is the model's, not the tenant's. A 429 from a routed tier is answered by the default model with a `tier_exhausted` line, never a 500. Nothing above the API changes for any of this; the UI, the agents and the MCP server see the same contract.

#### The code

#### Read the lane, Rs 0

Three settings that could change the model, and on your lane none of them does: acme has no model pin, routing is off, and no tier has ever run out. The point is where they live. A pin is a field read once a minute, the router is a flag, and the generator model is a variable, so a tuned endpoint from Module 12 or a self-hosted route from Module 9 is a change of one value behind the same `retrieve()` and the same contract, and every answer's `model` field says which one answered.

### What an answer costs, and the failure that is not a refusal

The rupee line for an answer and for each refusal, and a candidate whose reserve is too small for any JSON: the 502, the two log lines, and the reserve back.

#### What it costs

#### The failure that is not a refusal

A reserve too small for any JSON is the cleanest way to see the rule that a cut-off answer is never scored as the model declining. On a candidate that takes no traffic, set the reserve to 16 tokens: the first attempt hits the cap before a draft exists, the generator logs `generation_truncated` and asks once more with 48, which is still not enough, and the handler returns 502 with `generation_unparsed` and the finish reason in the message. No usage row is written for it, so the tenant is not billed a refusal it never got, and lesson 7's gate counts it as plumbing. The variable is not set on the live service, so the undo removes it.

#### The code

The candidate produced no answer twice, said so with a 502 whose message names the finish reason, and wrote no row. That is the difference between a refusal and a failure made visible: a refusal is the contract with `answerable false`, a failure is an error the caller sees and the gate counts as plumbing, and before 12 September the second was disguised as the first. The reserve went back to its default with the variable's removal, and the live service never saw a request.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

Nothing that serves traffic. A candidate revision took no traffic, failed twice on purpose, and lost its variable before the tag was dropped. The questions you asked are usage rows, three of them with the unanswerable flag, which lesson 11.5's alert will count as three on a day it should. Lesson 3.6 checks each quote against the passage it cites and versions the prompt, and lesson 3.7 sends the same contract as a stream: the citations first, the tokens as they come, and every failure named as it degrades.

Netsetos GenAI on GCP · Module 3 Generation · Lesson 3.5 Generate structured answers, citations and refusals · v5.0

Next: Lesson 3.6 Check quotes and version prompts.
