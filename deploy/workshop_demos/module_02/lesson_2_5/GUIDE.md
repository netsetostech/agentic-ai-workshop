# Lesson 2.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_2.5_Query_Rewrite_WIX.html`, reviewed at blob `76838552527ab66dd3a37a38b8adae680c3864df`. Learners read that page on the course site; this guide keeps its prose.

Lesson 2.4 kept the tenant and the filters on every rung a pool can come from. This lesson changes what every rung is searched with. A person asks "How much can I claim per trip for domestic travel?"; the handbook's clause says "Domestic travel is reimbursed against original receipts, capped at Rs 40,000 per trip." The kit's rewrite stage asks `gemini-3.1-flash-lite` for the question as a search query in the documents' words, searches the index with that, and hands the reranker and the model the person's question unchanged. A literal guard refuses any rewrite that drops or changes a code, a grade or a figure, and every refusal and every failure searches the question as asked. The stage ships off. You will try the guard in the page, ask the Chat page a paraphrase with the stage off, read the stage in the kit, call the rewrite directly, turn it on for a candidate revision that takes no traffic and make it fail, then measure the rewrite arm against the lane's own retrieval on 47 golden rows and 24 paraphrases: a measurement written to read right when the rewrite earns nothing.

- What a rewrite is for, and the one rule it never breaks

- The words: rewrite, search query, literal, guard, outcome, query_rewrite line, prompt version, paraphrase, arm, lift

- Before you run anything: set up the shell

- The Chat page with the stage off: the stream never asks for a rewrite

- The stage in the kit: the call, the guard, one line in /v1/query, and two lines that did not change

- rewrite() called directly: one question, one call, one outcome

- The stage on a candidate: QUERY_REWRITE=on, a forced failure, and the undo

- The measurement: the rewrite arm against the lane, on the golden rows and the paraphrases

- Change it: delete the prompt's literal rule and measure the guard; where the stage cannot go

- Verify it yourself: the checklist

You will learn what a query rewrite may change and what it must not, how the kit's literal guard decides, and why the stage ships off until it is measured. Then you will prove it on your lane: the Chat page with the stage off, `rewrite()` called directly, `QUERY_REWRITE=on` on a candidate revision with a forced failure, and `make ablate` with `--rewrite` on the golden rows and their paraphrases.

### What a rewrite is for, and the one rule it never breaks

The asker's words and the documents' words, one cheap call between them, and a guard that keeps every code and figure.

People ask in their own words; documents are written in theirs. The dense leg compares meanings, so "quit" finds "resign", as lesson 2.2 showed. It bridges much of the gap between a question and the clause that answers it, not all of it: a question asked as a sentence, with an informal term, an abbreviation or a few filler words, is a different text from the clause. A query rewrite asks a cheap model to restate the question as a search query before retrieval runs: the formal term for an informal one, a law's full name beside its abbreviation, one line of at most 40 words, nothing answered and nothing added. The kit's prompt also takes a question in Hindi or in Hinglish and asks for the query in English.

It changes what is searched, never what is reranked or answered. On `/v1/query` the handler embeds the question once. On an answer-cache miss, one line, `search_query()`, decides what `retrieve()` searches: the question and its vector, or an accepted rewrite and the rewrite's own vector. Every line after it gets the person's question: `rerank()` orders the pool against `req.query`, `generate()` answers `req.query`, and the answer cache stores the answer under the question's own vector. The reranker's job is to judge the pool against what the person asked, and the model's job is to answer the person; a rewrite that narrowed or misread the question would be invisible if either of them read it. Confined to the search, a bad rewrite can cost recall, a clause missing from the pool, and the reranker still judges what did arrive against the real question.

Every code and figure survives, or the question is searched as asked. A model that tidies "Rs 3 lakh" into "Rs 3,00,000", or "E3" into "senior employees", has changed the question: for the index a different grade or amount is a different clause. The guard, `keeps_literals()`, lists the question's literals, every token with a digit in it plus an amount's rupee and a figure's unit, such as LV-07, E3, s.53, Rs 52,000 and 45 days. It compares them after a normalisation that forgives case, spacing, dashes, the rupee's spellings and digits of any script, and refuses the rewrite when one is missing. Then the stage searches the question. A timeout, an error, an answer outside the schema or an empty query search the question too. Each call ends in one of four outcomes, `rewritten`, `same`, `rejected` or `fallback`, which the answer's stages carry and one log line per call records, with no question text in it.

It ships off. `QUERY_REWRITE` is `off` unless a revision's environment says otherwise, so the API image every learner builds carries the stage without changing one answer. config.py's own comment says it stays off "until evals/ablate.py --rewrite measures it", and step 7 is that measurement. When the lane's retrieval was last measured, on 8 Sept 2026 over the 43 anchored rows the golden set had then, its recall at five was already 0.96, so this page is written to read right when the rewrite shows no lift; the paraphrases are where a rewrite may earn its call.

The reference librarian. You walk up to the desk and ask in your own words: "How much can I claim per trip for domestic travel?" The librarian does not search the catalogue for "claim" and "trip". She looks under the catalogue's own heading, travel reimbursement, and brings back the shelf. Then she steps aside: the specialist who reads the shelf and answers you works from your question, not from her heading, because yours is the question to be answered. If you quoted a call number, a form or a sum, LV-07, Form 16, Rs 3 lakh, she copies it onto her slip exactly as you said it, and if her heading would have lost it, she searches your words instead. And when she is away from the desk you are not turned away: the catalogue is searched with your words, as it would have been with no librarian at all.

#### Who reads which text: /v1/query, line by line

- question `qvec = embed_query(req.query)`: one vector for the question, which the answer cache and, unless a rewrite is accepted, retrieval share

- question `_semantic_hit(req, qvec, fingerprint)`: the answer cache's lookup; a hit retrieves nothing, so it asks for no rewrite (`SEMANTIC_CACHE` is off on the lane)

- chooses `search_query(req.query, qvec, stages, req.tenant_id)`: off, the question and qvec; on, the rewrite and its own embedding when the guard keeps it, else the question and qvec

- search query `retrieve(search_q, ..., vec=search_vec)`: the one line that reads what the stage chose

- question `rerank(req.query, chunks, ...)`: the pool ordered against what the person asked

- question `generate(req.query, chunks, ...)`: the answer to what the person asked

- question `_semantic_store(req, qvec, ans, fingerprint)`: the answer kept under the question and its own vector

Every line is main.py's, quoted whole in step 4. `/v1/stream`, the Chat page's route, and `/v1/passages` have no `search_query` line: they search the question whatever `QUERY_REWRITE` says.

#### The rewrite bench: the kit's guard in the page, and BM25 over acme's corpus

Pick one of nine rows, golden questions and paraphrases of them. For each the bench shows the question and its literals, a rewrite, the outcome the kit's rules give that rewrite, and where BM25 ranks the row's anchor clause among the 1,628 chunks the kit's chunker cuts from acme's 17 markdown mirrors, once for the question and once for the text the stage would search. Then type a rewrite of your own: the guard answers as the kit would, names every literal you dropped, and names any you added, which the guard does not look for. On this page, the rewrites are illustrations written for this page, following the prompt's six rules, not model output; step 5's cell records the model's own, and they replace these when the author's run is in.

The guard is `normalise()`, `literals()`, `dropped()` and `rewrite()`'s outcome rule, ported to JavaScript. When this page was built, node ran the port over every golden and paraphrase question and over 494 question-and-rewrite pairs, and every verdict equalled the kit's. The ranks are BM25 with rank_bm25's constants, lesson 2.2's port of the ablation's sparse leg, computed when the page was built. Of the nine rows, BM25 already puts the anchor first for the question as asked on six. The text the stage would search ranks the anchor higher on three, in the same place on six, and lower on none. Three of the nine search the question itself: two refused by the guard and one given back by the model.

It is not the lane. The lane searches by meaning, with a 768-number vector this page cannot compute without a model; BM25 counts the words a query shares with each chunk, weighted by how rare they are, which makes visible in a number what "the documents' words" means. On the contractor question, jn-07, the sentence as asked ranks the clause 420th, partly because this BM25, as rank_bm25 builds it, still gives "a", "to" and "and" a little weight, so a long sentence pulls long Act pages up; the rewrite, a search query rather than a sentence, ranks it 26th. Whether a dense retriever gains anything from the same rewrite is a separate question, and step 7 measures it on your lane. Your own rewrite gets the guard's verdict but no rank: ranking it would need the whole corpus in the page.

### The words: rewrite, search query, literal, guard, outcome, query_rewrite line, prompt version, paraphrase, arm, lift

Twelve rows, each with the value it takes on your lane.

Two of these words carry the lesson: search query and question. The first is all the stage may change; the second is what everything after retrieval reads. When an answer looks wrong with the stage on, `stages.search_query` says which text found its pool, and the question is still the one that was answered.

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

The stage's two settings and the retrieval backend live in the API's environment. A name the service does not set is unset here rather than exported empty, because the kit's settings class reads an empty variable as a value, and an empty `QUERY_REWRITE` is a value the validator refuses. `svc_env` is the helper lessons 2.2 to 2.4 define; step 6 reads the template with it again. Step 7's ablation reranks through the Ranking API's client at the API's own pin; the pip line is harmless if it is already there.

### The Chat page with the stage off: the stream never asks for a rewrite

One paraphrase asked the way a person asks it, the route the page sends it down, and the log that shows no rewrite was asked for.

#### Definition

The Chat page's direct brain is a thin client: `stream_answer()` posts the question to `/v1/stream` with `top_k` 5 and renders the citation and token events as they arrive. `/v1/stream` embeds the question, retrieves, reranks and streams the answer from the question as asked. It has no `search_query` line, so the stage cannot run there whatever `QUERY_REWRITE` says, and on the lane it is off anyway. What you see in the page is the answer with no rewrite, and it would stay so with the stage on: the stage serves only the callers of `/v1/query`, which are `make eval-live` and `shared/documind_tools.retrieve()`, the function the chat service's agent brains and the MCP server's retrieve tool call. The stream's usage row carries the brain's label, `ui`, the pool and the stage clocks; a rewrite's cost would be on a line of its own, and there is none.

#### The code

#### Do it: a paraphrase in the Chat page, then the log

In the Chat page, signed in as yourself, ask: How much can I claim per trip for domestic travel? It is a paraphrase of golden row lk-01, whose answer must contain 40,000. Then read the API's log for the last ten minutes.

The question went down `/v1/stream` and came back answered from its own words: the index was searched with the question's vector, the reranker ordered the pool against the question, and the model answered it. The log holds the stream's usage row, labelled `ui`, and no `query_rewrite` line, because the stream has no line that could write one and the lane's switch is off. Step 6 turns the switch on for a revision nobody else reaches and asks `/v1/query` the same words.

### The stage in the kit: the call, the guard, one line in /v1/query, and two lines that did not change

shared/query_rewrite.py does the work with the standard library and the price table; rewrite.py wires it into the service; main.py calls it once.

#### Definition: the call

`rewrite(client, question)` makes one call to `gemini-3.1-flash-lite` on the client its caller passes in; rag-api passes the generator's own client, built on location `global`, where Gemini 3.x generation is served. The request asks for JSON with one string field, `query`, with thinking budget 0, one attempt, a 3 s timeout and at most 256 output tokens. The prompt says what the desk's index holds and gives six rules; the question goes in fenced as data, cut to 4,000 characters, the request's own cap, with any fence marker taken out so the question cannot close its own fence. The prompt names no tenant, and its example literals are made up, so it names no code or figure of the corpus.

#### Definition: the guard

`normalise()` puts both texts in one form: any script's digits as ASCII, lower case, one kind of dash, every spelling of the rupee as "rs ", "%" for per cent, lakh and crore in the singular, single spaces. `literals()` reads the question's tokens in that form and keeps each one with a digit in it; a plain number takes the "rs " before it and the unit after it, so "Rs 52,000" and "45 days" are literals whole. `_present()` looks for each literal in the rewrite as a whole token, so 52,000 is not found inside 52,000,000 and E3 not inside E30. `dropped()` lists the misses, and `keeps_literals()` is true when there are none. What it does not guard is stated in the module itself: a figure written in words, a name, an acronym. It also looks in one direction only: a rewrite that adds a figure the question never had passes it, and the prompt's rule against adding a fact is the only line against that.

#### Definition: the outcome, and the line

`rewrite()` never raises. It reads the answer, `parse()` accepting exactly the schema's one field and nothing empty, then decides in a fixed order: no usable query is `fallback` with the error `parse`; the question given back, case and closing punctuation aside, is `same`; a dropped literal is `rejected`, with the literals it lost; anything else is `rewritten`. Any exception, a timeout or a 404 or a quota error, is `fallback` with the exception's class name. Its query is the rewrite only when the outcome is `rewritten`. The tokens are priced through `shared/prices.py` at list price, 0.25 and 1.50 US dollars per million tokens in and out for gemini-3.1-flash-lite, and a refused rewrite was still billed. `row()` turns a result into the `query_rewrite` line: the outcome, the number of literals dropped, the tokens, the cost and the time, never the question, the rewrite or a literal, any of which may be an amount or a name.

#### Definition: the stage on /v1/query

`search_query()` is the whole stage. Off, it returns the question and the vector the handler already has, makes no call, writes no line and leaves the stages as they were, so the answer and its usage row are what they always were. On, it calls `rewrite()`, embeds an accepted rewrite, and returns that pair; on anything else, a refusal or a failure of the call or of the second embedding, it returns the question and its vector. It writes one line per call and puts three keys on the answer's stages: `rewrite`, `search_query` and `rewrite_ms`, which sits inside `retrieve_ms`. main.py imports it below `_guard()` and calls it on one line, after the answer cache's lookup and only on a miss. The next line retrieves with what it returned. The rerank and generate stages read `req.query`, as they did before the stage existed, and the answer cache stores the question's own vector. config.py holds the switch and refuses a third value at import, so a typo cannot start a revision whose environment says on while it searches the question.

#### Do it, offline: the guard on the module's own example

The cell asks the kit's guard about one question and five rewrites of it: a faithful one, the same one spelt with an en dash, the rupee sign and Devanagari digits, the amount written without its comma, the unit given another word, and the section spelt out. Nothing leaves the machine.

The guard forgave every difference of spelling and refused every difference of substance. The en dash, the rupee sign and the Devanagari digits normalised to the question's own literals, so the second rewrite was kept. "52000" is not "52,000" as written, "45 working days" is not "45 days", and "section 53" is not "s.53", so those three were refused, each with the literal it lost. The last refusal is strict on purpose: a statute's section written out is the same section to a reader, and the guard still prefers to search the question rather than judge that, because a refusal costs one wasted call and a wrong literal costs the right clause. On the lane, every refusal searches the question as asked.

#### Do it, offline: the kit's own tests

evals/tests/test_query_rewrite.py holds 20 tests that need neither a model nor a lane: the guard on the design's examples and on the golden rows, every outcome against a fake client, the request against google-genai's own config class, the line with no question text, `search_query()` lifted from rewrite.py with the switch off and on, and the ablation's rewrite arm and paraphrase rows against a stand-in lane. The pipe keeps the summary and drops the timing.

### rewrite() called directly: one question, one call, one outcome

The kit's function on the global endpoint, over the bench's rows, with the outcome, the time and the rupees of each.

#### Definition

This is the function rag-api calls, called from your shell with your own credentials and a client on `global`. Each row prints its outcome, the call's milliseconds, and either the rewrite or what the stage would search instead; the last line adds up the tokens and the rupees at list price. The model's wording varies from run to run, so compare the outcomes and the guard's verdicts rather than the words. The rewrites the author's run records here are the ones the bench in step 1 shows.

#### Do it: the bench's nine questions, one call each

#### The bench's rows, computed when this page was built

For each row, the rewrite, its outcome under the kit's rules, the anchor, and where BM25 ranks the anchor among the 1,628 chunks for the question and for the searched text. On this page, the rewrites are illustrations written for this page, following the prompt's six rules, not model output; step 5's cell records the model's own, and they replace these when the author's run is in.

The kit's own function asked the model once per question and named an outcome for every call; nothing in it can raise. A rewrite that kept every literal came back as the text to search, a question given back or a rewrite the guard refused came back as the question, and the tally priced the calls in paise. Of the nine rows, BM25 already puts the anchor first for the question as asked on six. The text the stage would search ranks the anchor higher on three, in the same place on six, and lower on none. Three of the nine search the question itself: two refused by the guard and one given back by the model. A word-counting ruler moves where the words move; the lane's dense retriever is measured in step 7.

### The stage on a candidate: QUERY_REWRITE=on, a forced failure, and the undo

A revision that serves nobody, one question with the stage on, the same question with a model that does not exist, the two log lines, and the variables taken back out.

#### Definition

`QUERY_REWRITE` is read once, at startup, and the validator refuses anything but `off` or `on` before the revision serves. Neither make target sets it. `make deploy-services` sets the API's whole environment with `--set-env-vars`, and the variable is not in its list; `make candidate` updates its own list with `--update-env-vars`, and the variable is not in that one either. A revision gets the stage from `gcloud run services update --update-env-vars`, as below, and that has two consequences. The next `make deploy-services` replaces the whole environment and turns the stage off again: a variable set by hand is a hotfix that a routine deploy drops, which lesson 11.7 drills. And `--update-env-vars` merges, so the variable would ride into the next candidate, `make candidate`'s included, unless it is removed; the undo removes both. The pattern is lesson 2.2's: `--no-traffic` and a tag, a URL of its own, and the identity token's audience still the service's canonical URL.

#### The code

#### Do it: the stage on, one question

The cell creates the revision and asks it the paraphrase from step 3. `ask()` prints the stage's three keys, the clocks, the answer's cost and the citations. If the first line says `same`, the model judged the question a good search query already; ask another of step 5's questions, such as pp-10's, the same way.

#### Do it: a model that does not exist, the same question

`QUERY_REWRITE_MODEL` is a setting, so a revision whose model name is wrong is one variable away. The call fails, `rewrite()` catches it, and the stage searches the question: the answer still comes, with HTTP 200.

#### Do it: the two lines the two questions wrote

#### Do it: the undo

The variables exist only on the candidate's template, so they are removed rather than set back, and the tag is dropped. Both template lines must print empty.

A revision with the stage on answered the paraphrase on its own URL while the live revision served everyone else. Its answer said which text found the pool, `stages.search_query`, and what the stage did, `stages.rewrite`; its citations came from a pool the reranker ordered against the person's question. With a model that does not exist, the same request answered 200 with `fallback`: the question was searched, exactly as with the stage off, and the failure cost a call's latency and nothing else. The two log lines named the outcomes, the error's class, the tokens and the cost, and no word of the question. Then the variables came out of the template and the tag went; the next candidate starts clean, and the next `make deploy-services` would have taken them out anyway.

### The measurement: the rewrite arm against the lane, on the golden rows and the paraphrases

Lesson 2.2's harness with one arm added from outside the API, the paraphrases scored on their originals' anchors, the tally of the calls, and a reading that holds when there is no lift.

#### Definition

`--rewrite` adds one arm to `evals/ablate.py`, built beside the `--arms` keys and never as one of them: the lane's dense 20 then rerank 5, with the question rewritten first by the same `shared/query_rewrite.py`. The rewrite is what the Firestore rung searches and the question is what the reranker orders, as on `/v1/query`; a refused or failed rewrite searches the question, so the arm differs from the lane's only on the rows where a rewrite was accepted. Each distinct question gets one call, kept, so a retried row is not asked twice: 45 calls in the golden run, because two pairs of rows ask in the same words, and 69 in the paraphrase run. `--paraphrases` adds the file's 24 `same: true` rows after the golden ones, each scored on the anchors of the row it rewords, and prints under each arm the golden share and the paraphrase share apart; the 18 `same: false` rows ask something else and are never scored. So the paraphrase run re-scores the 47 golden rows too: if you want one run only, run that one, since its split line carries the golden share. `--limit` cuts the golden rows first.

#### The code

#### Do it: a wiring check, then the golden rows, then the paraphrases

The wiring check takes the first five anchored rows, two arms and five calls, and shows the lines are where they should be before the longer runs spend anything.

#### How to read it, and the baseline it is read against

The 8 September figures were measured over the 43 anchored rows the golden set had then; it has 47 now, four added since, so today's lane row is the baseline that counts, measured in the same run as the rewrite row. Read the two rows of each run against each other, never against another run. One row whose anchors all appear or all vanish moves recall@5 by 0.021 on the golden rows and by 0.042 on the paraphrases, so a difference of a row or two is the movement of single rows, which one run cannot separate from the model's own variation between runs. With the lane's own row at 0.96 when it was last measured, there is little left to win on the golden rows, so a rewrite row equal to the lane's is the likely result there, and the harness's own words for it are "the rewrite is not the knob on these questions". The paraphrases are where it may differ: the same anchors, asked in other words. The rewrite row's p95 carries the model call and a second embedding, and the tally line under it is what the calls cost.

Turn it on only where the measurement says so: the rewrite row ahead of the lane's on the paraphrases by at least one row's worth, and not behind it on the golden rows by as much. Then weigh what it costs per question: one gemini-3.1-flash-lite call, about Rs 9 a thousand questions (estimated from the prompt's length; your tally line prints the real figure), and the call's milliseconds inside every `retrieve_ms`. Below that line, leave it off; config.py's default says the same. Even on, it serves only `/v1/query`, and the kit has no make switch for it yet: a revision carries it until the next `make deploy-services`.

#### What the runs cost

Each row of the ablation costs two embeddings, in paise, and one Ranking API request per arm, at the listed rate lesson 2.3 states, one US dollar per thousand requests, Rs 0.085 each at 85 rupees to the dollar. Each rewrite call is priced here from the prompt's length through `shared/prices.py`; your tally lines print the real figure. An answer is priced by its tokens and printed on its own line; config.py's budgets cap one attempt at 8,000 tokens in and 2,048 out, Rs 2.33 at gemini-3.6-flash's list price.

Two retrieval recipes ran over the same rows in the same run, and the only knob between them was the text the index was searched with. Each was scored by whether the anchor came back in the top five, not by whether an answer sounded right, so no model's prose could flatter either. On the golden rows the lane's row was the bar, and a rewrite row level with it means the stage would add a call and its milliseconds to every question for nothing; on the paraphrases the same anchors were asked in other words, which is the case the stage exists for. The tally said how many calls the guard refused or the model gave back, and what they cost. Whichever way the two lines fell, the switch stays where config.py put it until a line like yours says otherwise.

### Change it: delete the prompt's literal rule and measure the guard; where the stage cannot go

Two defences against one failure, the first removed and the second measured on the rows it guards; then the routes, rows and deploys the stage never reaches.

#### Definition: two defences, one failure

A rewrite that loses a code or a figure is stopped twice. The prompt's second rule asks the model to copy every literal exactly as written; the guard refuses whatever the model sends back without one. Delete the rule and the guard is all that is left. The guard can refuse only a question that carries a literal: 13 of the 47 anchored golden rows, 12 distinct questions, all of them acme's. The five rows that `--limit 5` takes carry one literal between them, lk-02's "16", which is why this check takes a file of its own through `--golden` rather than a limit. The edit is to your clone of the kit only; the lane's image never sees it.

#### Do it: the rows the guard can refuse, Rs 0

#### Do it: delete the rule

#### Do it: the same arm, the edited prompt, those rows

Compare its tally with step 7's golden run. A question with no literal cannot be refused, so the golden run's refused count was already a count over these 12 questions: the same questions, the same model and the same guard, with one rule of the prompt between the two counts. More refusals with the rule gone is the guard doing the rule's work. Each refusal searched the question as asked, so on these rows the rewrite arm cannot fall below the lane's for a lost literal, only for a rewrite that kept every literal and searched worse; a weaker prompt costs refused calls, each one billed, before it costs a worse search.

#### Do it: put the kit back

The edit changed the prompt and left `PROMPT_VERSION` as it was, so any line written with the edited prompt would name a version that does not describe it. That is a reason to restore the file rather than keep the experiment; versioning a prompt properly is lesson 3.6's subject.

#### Where the stage cannot go

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it on your lane.

Nothing that serves traffic. Step 6 created three revisions of the API that took none, one with the stage on, one with a model that does not exist and one with both variables removed, then dropped the tag; the live revision never changed and `QUERY_REWRITE` is absent from the template again. Step 8 edited `shared/query_rewrite.py` in your clone and put it back; it also left `/tmp/literal_rows.jsonl`. The log holds the questions' usage rows and two `query_rewrite` lines. The bill: about Rs 24 for the 272 Ranking API requests of steps 7 and 8 and the rewrite calls of steps 5 to 8, computed from the row counts above, plus three generated answers in steps 3 and 6, each priced on its own line. Lesson 2.6 decides, from the reranked pool and before any answer is written, whether to answer at all or to refuse.

Netsetos GenAI on GCP · Module 2 Retrieval · Lesson 2.5 Rewrite the query before retrieval, and measure it · v5.0

Next: Lesson 2.6 Decide answer-or-refuse with a System One model (Jev).
