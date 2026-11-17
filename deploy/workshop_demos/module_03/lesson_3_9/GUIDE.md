# Lesson 3.9: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_3.9_Design_Fact_Checking_WIX.html`, reviewed at blob `af82fe1d1e35eabd754b6aec0d095c10bf085032`. Learners read that page on the course site; this guide keeps its prose.

Module 3 built the parts one lesson at a time: the budget that packs the evidence, the contract that makes the model cite or refuse, the stream and its fallbacks, and the journey from an upload to a cited answer. This page puts them to a use none of those lessons had. A fact desk takes a claim and returns one of two things: a verdict that stands on a clause from the tenant's own documents, quoted and cited, or a refusal. It is a design page, written in the shape of the capstone rubric that lesson 11.8 publishes, so its sections are the rubric's five dimensions and each one shows what a 3 looks like. Every number on it is computed from the kit or read from a dated price page, and the sections on the first four dimensions each end in a script you can run for Rs 0.

- What a fact desk is, and how a design is scored

- The words: claim, door, passages, draft, quote check, judge, verdict, refusal, threshold, floor, ceiling, vacuous

- Before you run anything: set up the shell

- Architecture: the path a claim takes, station by station

- Architecture: three designs rejected, and the number that would change each

- Failure modes: four the kit reproduces, and which ones the alerts see

- Cost: a claim, a month and a floor, at 1k, 10k and 100k claims

- Cost at 10×: the limits the kit declares, and the one it does not

- Evals: what blocks, what advises, and what cannot fail

- Next month: the top item comes from the rows

- Verify it yourself: the checklist

You will learn how a system design is scored, on the capstone rubric's five dimensions, and what moves each answer from a 2 to a 3, by designing a fact desk from the kit's own parts. Then you will back every answer with a script: quotes held against their passages, the thresholds of three rejected designs, the alerts the kit declares, the cost at 1k, 10k and 100k claims a month, the limits that bind at ten times the load, and the eval rows that cannot fail.

### What a fact desk is, and how a design is scored

A claim goes in; a verdict on a quoted clause, or a refusal, comes out. The stations are the kit's, and the score is the rubric's.

A fact desk answers one kind of question. Someone has a sentence they want to publish or act on: a claim. The desk returns one of two things. A verdict that stands on a clause from the tenant's own documents, quoted and cited, so that a reader can open the page and find the words. Or a refusal that says the documents do not settle it. There is nothing in between, because a verdict without a clause is an opinion, and opinions are what the desk exists to catch. DocuMind already has every station such a desk needs. `/v1/passages` retrieves for a claim without a generation call and returns each passage's full text. The generator's contract makes the model say whether the passages answer, and cite each one it relies on with a quote. Rule 5 of its prompt says a quote is the clause that answers, at most 25 words. The judge reads answers against their passages and explains them. What the request path lacks is a station that holds each quote against the passage it cites: `resolve()` copies the model's quote as it came. The kit's training-set builder already has that check, `quote_holds()`, at Rs 0, and the design borrows it.

A design is scored the way the capstone is. The capstone rubric, which lesson 11.8 publishes, has eight components that must exist in the learner's fork, each checked PASS or FAIL by `make capstone-check`, and five dimensions the defence scores 0 to 3, 15 points in all, with 9 to pass and no dimension at 0. Three of the components are this page's proof: the architecture, naming at least three rejected options and why (component 5); the cost model at 1k, 10k and 100k queries a month, in rupees at 85 to the dollar and dated (component 6); and four failure modes, each proved by a script (component 7). The sections below follow the dimensions in order. Each one starts where a 2 ends and shows what makes it a 3.

The newsroom's fact desk. A reporter files a story with a claim in it. The desk does not ask what the checker thinks; it asks what the paper's own files say. A clerk at the door sends some calls straight to an editor, the ones the paper's rules say a person must take. A researcher pulls the clippings and has no opinion yet. The checker writes the verdict with the exact sentence and the clipping it came from. The copy chief lays the quoted sentence over the clipping, word for word, before anything is printed, which costs nothing but a minute. Once a week the standards editor reads a sample of past checks and writes notes; the notes improve the desk and never unprint a page. Some calls the desk never makes: it does not phone a stranger for a quote its files cannot source, it does not reread the whole archive for every claim, and it does not let the standards editor alone decide what runs. And when the files are silent, the desk says so.

#### The board: five fates of a claim, six stations

Pick what happens to a claim and follow it through the stations. Each station is a part of the kit, named with its file; each says what it does to this claim, what it costs at most, and what it leaves behind. The judge stands beside the path rather than on it: the verdict never waits for it.

- 1 · The doorservices/rag-api/desk_door.pyNone of the law's five classes: the body goes through as it was sent.Rs 0

- 2 · The passagesPOST /v1/passages, main.pyOne embedding of the claim, up to 20 candidates from the index, the Ranking API's top 5, each with its full text. Its row says event passages and cost 0.Rs 0.09 at most

- 3 · The generatorgenerator.py, ModelDraftanswerable true, and [1] cites NP-03 with the sentence the answer rests on.Rs 2.33 at the ceiling

- 4 · The quote checkquote_holds(), evals/make_trainset.py"A confirmed employee at grade E3 or above serves a notice period of 60 days." is in NP-03, in 15 words: it holds.Rs 0

- 5 · The judge, beside the pathevals/judge.pyOne standing verdict in twenty is read later, for groundedness and fulfilment. A low score sends the verdict to a person; it never changes it.Rs 0.47 when it reads one

- 6 · The verdictthe fact desk's own rowStands: the answer, NP-03's sentence, and hr_policy_2026.md, the source it cites.the row: stands

Stands, with its clause: Rs 2.42 at the ceiling, and the check on its quote cost nothing.

The door is `desk_door.py`, the passages are rag-api's own route, the generator is `generator.py`'s prompt with `ModelDraft`, the quote check is `quote_holds()` and the judge is `evals/judge.py`. The costs are ceilings, computed from the kit's rates and Google's list prices of 8 October 2026 (step 6). The quote verdicts are `quote_holds()`'s own, run on the handbook's NP-03 when this page was built (step 3).

It is the design's rules, not a run. The fact desk itself, the service that calls these stations in this order and writes one row per verdict, is the design: the kit has every station and not the desk. The costs are the most a claim can bill at the kit's token ceiling, not what any claim did; step 6 puts the measured average beside them.

### The words: claim, door, passages, draft, quote check, judge, verdict, refusal, threshold, floor, ceiling, vacuous

Twelve rows, each with the value it takes on your lane.

Two of these words carry the design. A refusal is a correct verdict, not a failure: the files are silent and the desk says so. And a held verdict is not a refusal: the model said the files answer, and the check that costs nothing could not find its words in them. A person reads every held verdict; nobody needs to read a refusal twice.

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

### Architecture: the path a claim takes, station by station

Six stations, each the kit's own; why each one is there rather than its alternative; and the one check the request path lacks, run offline.

#### Definition

The design is one small service, the fact desk, and every station it calls is already in the kit. A claim arrives for one tenant, and the desk calls rag-api's `/v1/passages` with its own identity. That identity needs what the MCP server's account has today: `roles/run.invoker` on documind-api, which the loop in `commands/lesson-12.2.sh` grants, and a place on each tenant's roster, which `make roster` writes. A 2 draws this path; it also says why each station is there rather than the obvious alternative, with reasons that belong to this workload:

- The door, rather than rules of the desk's own. The law's five classes are decided once, in front of every route into rag-api that takes a question. A desk with its own list would drift from the Desk's. A hit on `/v1/passages` comes back as `passages: []` with the law's reply in `answer`, so the desk can tell a claim handed to a person from an empty pool.

- `/v1/passages`, rather than `/v1/query`. One retrieval, used twice: the generator reads the passages, and the quote check reads them again, in full. A `Citation` carries a quote of at most 500 characters; a passage carries its whole chunk, which is what a quote has to be found in. An empty pool refuses before any generation is paid for. And retrieval keeps every rule rag-api keeps: the roster, the filters, the backend the tenant's data_region allows, the version rule, the rerank. The kit built this route for exactly this caller, one that writes its own answer.

- The generator's contract, rather than free text. `answerable` is a field the model fills, not a reading of its prose; each citation is a number resolved against the passages the model saw; each carries the words it relied on. The desk keeps `SYSTEM` as it is, so its answers are the lane's answers.

- The quote check, rather than trusting the quote. `resolve()` copies the model's quote as it came, and rule 5 is a request in the prompt that nothing on the request path enforces. `quote_holds()` is the kit's own rule, written for the tuning set: the helpdesk style of `make_trainset.py` drops every teacher pair whose quote does not hold in its chunk. It costs nothing, so it runs on every claim.

- A sampled judge, beside the path, rather than none or a judge on it. The computed checks cannot see an answer that says more than its passage; the judge can, and explains. It reads one standing verdict in twenty, after the fact, because each claim it reads is two autorater calls, and it never decides, because a model's score is not a verdict (lesson 4.2). It sends the cited passages to Vertex AI Evaluation in us-central1, so the design samples only tenants whose data_region is `any`: the caution the kit itself takes before a Google Chat door may carry an `in` tenant's quotes (step 4).

- A verdict row of the desk's own. One row per claim in `usage_row()`'s shape, with the verdict and any quote that failed beside it. No row the kit writes carries a verdict, and step 5 shows what that costs the alerts.

#### The code

#### Do it: the quote check on the handbook, offline

The cell cuts the handbook with the kit's chunker, takes NP-03, the notice-period clause, and holds six quotes against it with `quote_holds()`: the sentence as written, a sentence that crosses a line break, the same sentence with revision 2's figure, a paraphrase, the whole clause, and the whole clause as `_draft()` trims an over-long quote. Each line prints both halves of the rule and the kit's verdict.

Two quotes held and four did not, each of the four for its own reason, and `resolve()` would have passed all six. Revision 2's figure is the dangerous one: a fluent sentence, one number off, that a reader would believe; it fails because the passage the model read says 60. The paraphrase is true and still fails, which is the design's choice: a verdict stands on the passage's words, not on the model's. The whole clause is in the passage and fails rule 5's 25 words. The trimmed one fails twice, and the second reason matters: the three dots `_draft()` puts on an over-long quote are in no passage, so an answer the generator had to repair is held for a person by construction.

### Architecture: three designs rejected, and the number that would change each

A judge-only verifier, a cached long context, an agent with web search: each rejected with the kit's own numbers, each with the threshold that would bring it back.

#### Definition

A list of what was built is a description; a list of what was not built, and why, is a decision record. The rubric asks for at least three rejected options, and its 3 asks for more than a reason: the threshold at which the decision flips, stated so that someone could check it. Here are the three designs a fact desk is most often built as, each rejected on a number the kit holds.

#### The code

#### Do it: the three thresholds, from the kit's files

The cell rebuilds a claim's budget with the kit's own function, reads the cache's floor and its read rate from the kit, measures each tenant's corpus with the kit's estimate, reads the policies `make roster` writes, and prices the judge on every claim. Four prices come from Google's pages, dated in the cell: the cache's storage, the embedding, the ranking query and the judge's default autorater.

The cache lost on the two large corpora at every scale, by a margin no likely price change closes: acme's corpus is 5.9 times the bound at 100k claims, Rs 30,121 a month just to keep cached, and Rs 6.19 a claim to read. globex is the honest exception, small enough to cross at a few thousand claims a month if the retrieval path really sent its ceiling every time, which is why the line is a threshold and not a verdict. The floor bites the other way: the pack `make cache` builds for globex, its synthetic documents, is 239 tokens by the estimate, so the 4,096-token floor alone rules out a cache of that pack. The policy lines are the kit's own data, and the judge line is the price of making the adviser the decider. Each rejection is now a sentence someone can check.

"We retrieve instead of caching each tenant's corpus, because a cached corpus costs more per claim above 81,612 tokens at 100k claims a month, and acme's is 485,430. globex is under that line; if its measured tokens a claim put its corpus under the bound at its own volume, we would cache globex and keep retrieving for the others."

### Failure modes: four the kit reproduces, and which ones the alerts see

Each failure has a lesson that forces it; the alerts catch one of the four, partly, and the desk's own row is what would catch the rest.

#### Definition

A 2 documents four failure modes with real symptoms, each reproduced by a script. Every one below has a lesson that forces it, two of them on a candidate revision that takes no traffic. The 3 is the column after the symptom: what `terraform/alerts.tf` would catch, what it would not, and what the design does about the second group.

So the monitoring catches one of the four, and that one only in part. The rest are counted on rows nobody alerts on, or not counted at all, which is what the design's verdict row and its metrics are for. Two facts behind the table matter beyond this desk. First, `terraform/quota.tf` names five alerts as intents, and only two are declared, both in `alerts.tf`: `guardrail_blocks`, `cache_hit_low` and `burn_rate` are declared by nothing. Second, no policy counts documind-api's own errors. A reply the generator cannot parse is a 502, never a refusal (lesson 3.5): each one leaves a `generation_unparsed` line and no usage row, and no policy reads either. `burn_rate`, one of the three undeclared alerts, is the one that would have seen a run of them.

A rate needs claims to be a rate. The unanswerable rate is judged over windows of 30 minutes. At 1k claims a month one such window holds 0.7 claims on average, at 10k it holds 6.8, and at 100k about 68. A desk at the bottom of the range alerts on counts over a day; one at the top can alert on a share over half an hour.

#### The code

#### Do it: the alerts the kit declares, against the ones it names

The cell reads every Terraform file in the kit, lists the alert policies each declares, holds `quota.tf`'s named alerts against them, and prints what the unanswerable rate's denominator counts.

The kit declares its alerts in two files, and the list in `quota.tf` is older than both: two of its five names became policies, and three are still only names. The denominator line is the whole of failure mode 3 in one filter: the rate counts `query` and `stream` rows, so a desk built on `/v1/passages` refuses invisibly, and every claim the door hands to a person is just as invisible. A 3 on this dimension is that sentence, with the metric that closes the gap beside it.

### Cost: a claim, a month and a floor, at 1k, 10k and 100k claims

Model, retrieval, judge and floor, in rupees and dollars and dated; the ceiling no claim exceeds, and your lane's own average beside it.

#### Definition

A claim bills four things. The model: the generator's tokens at `shared/prices.py`'s rates for `gemini-3.6-flash`, $1.50 in and $7.50 out per million. The tokens come from the kit's own budget. `TokenBudget.fit()` splits `max_context_tokens`, 8,000 tokens by the kit's estimate, into 175 of fixed prompt for this page's claim and 7,825 for the passages, so no prompt is packed past 8,000; `max_answer_tokens` caps the answer and its thinking at 2,048. That makes 8,000 in and 2,048 out the ceiling of one attempt, Rs 2.33 a claim; the model's own count differs from the estimate by a little (lesson 3.4). A first attempt that runs out of room is tried once more with three times the room and both are billed; the log says `generation_truncated`, and a lane whose reserve is right has none. Retrieval: one embedding of the claim, `text-embedding-005` at $0.000025 per 1,000 characters, at most Rs 0.0085 for the longest claim the route accepts; and one Ranking API query for the pool of 20, at $1.00 per 1,000 queries of up to 100 documents, Rs 0.085. Together, Rs 0.09. The judge: two autorater calls on each claim it reads, at Gemini 2.0 Flash's $0.15 in and $0.60 out per million, which is how Gen AI Evals bills its default autorater: Rs 0.47 a claim read, at the ceiling, counting each metric's verdict as long as the answer, which is an assumption and not a measurement. The quote check costs nothing. The floor: what the lane bills by the hour with no claim at all, which lessons 0.1 and 0.4 price at Mumbai's list prices: Rs 32,157 a month on a SMALL index, Rs 81,100 on MEDIUM. Of that, the index and the connector that documind-api's deploy names come to Rs 8,240 on SMALL and Rs 57,183 on MEDIUM; the desk uses none of the rest.

#### The month, at the ceiling, with the judge reading one claim in twenty

Dated 8 October 2026. The model's rates are the kit's, which are Google's standard rate. Google bills `gemini-3.6-flash` at an introductory $0.75 in and $3.75 out until 31 December 2026, so until then the model column is twice what is billed; the kit and this page use the standard rate, so nothing here changes on 1 January. The embedding, ranking and judge prices are Google's list prices read on 8 October 2026, and the floor is Mumbai's list prices read on 7 October 2026. Rupees at 85 to the dollar. Not priced here: Cloud Run's request time, Firestore's reads (about 20 a claim, to fill the pool) and Cloud Logging.

Read the table the way the rubric does. At 1k claims a month the floor is 93 percent of a SMALL lane's bill, and the cost per claim, Rs 34.60, is mostly the lane standing still. At 100k it is 12 percent, and the model's column, Rs 2,32,560, is most of the Rs 2,76,393. The claims cost more than the floor above 13,166 claims a month on SMALL, 33,206 on MEDIUM. Below that line, the cheapest thing a desk can do about its bill is share a lane; above it, the next rupee is in the model's column, and the measured tokens decide how many there are.

#### The calculator: change the assumptions, not the arithmetic

The claims cost more than this floor above 13,166 claims a month, at these settings: Rs 2.44 a claim before the floor.

The arithmetic is the cell's below, line for line, in JavaScript: each part rounded to whole rupees and the total their sum. The rates are `shared/prices.py`'s, the floors are the ones lessons 0.1 and 0.4 state, and the ceiling is `TokenBudget.fit()`'s. The measured option appears once the author's run below is recorded.

The author's measured average goes here once the run below is recorded; until then the ceiling stands alone, and the ceiling is the number a cost model may not exceed.

#### The code

#### Do it: the cost model as a script

This is the table as a script you can keep: component 6's `COST-MODEL.md` starts from its output. It reads the rates and the rupee rate from the kit, rebuilds a claim's budget with the kit's own function, and carries the three prices the kit does not hold, the embedding, the ranking query and the judge's autorater, as constants with their date.

#### Do it: your lane's tokens a claim, from the rows

The ceiling is what no claim may exceed; the average is what claims cost. `make usage` reads the last day's usage rows, and its table by model and backend carries each model's answers and tokens; the second line divides them. Your average depends on what was asked on your lane, so it is yours, not the author's.

The script printed the table, part by part and shard by shard, from the kit's own files and three dated prices, so the cost model is something a reviewer can rerun rather than a figure in a document. The rows gave the other half: the tokens your lane's answers really used, against the 8,000 in and 2,048 out the budget allows. Whatever the gap between them, it moves only the model column; the floor stays where it is, so the smaller the average, the higher the line where the claims overtake the floor.

### Cost at 10×: the limits the kit declares, and the one it does not

Ten times the bill is arithmetic. What stops being linear is a ceiling: 40 at a time on 20 instances, 1 replica, 600 a minute.

#### Definition

The commonest 2 on this dimension, the rubric says, scales the bill by ten and stops. At ten times the load something stops being linear, and the kit declares where in its files: an instance count and a concurrency in the API's deploy, a replica count on the index, a quota on Gemini calls. The arithmetic takes the 730-hour month the price pages use and asks each ceiling one question: how much busier than the average minute would the busiest minute have to be for it to bind?

So what breaks first at 10×? Take the top scale and multiply it: a million claims a month is 22.8 a minute on average. The first ceiling the kit declares is `quota.tf`'s 600 generation calls a minute, and it is off. With `GEMINI_QUOTA_OVERRIDE` at its default the project has no cap of its own on generation calls, and a runaway spends at whatever rate Google's project quota allows. Switched on, it binds when the busiest minute is 26.3 times the average, and every Gemini caller in the project shares it: the chat service's brains, the router, the Desk's checks. The instances are much further away at the SLO, where 800 slots turn over 16,000 claims a minute at 3 s each. At the 120 s cut they turn over only 400, which is under the quota: once claims take longer than 80 s, the slots bind first, at a busiest minute 17.5 times the average. And the one replica has no number at all. One node answers every claim's search, its capacity is declared nowhere in the kit, and the honest answer at 10× is to measure it before the load arrives.

The bottom of the range is not linear either. With no instance kept warm, a claim that arrives after a quiet spell waits for an instance to start, and at 1k claims a month a claim arrives every 43.8 minutes on average; at 100k, every 26 seconds. `--cpu-boost` shortens the start; only a floor of one instance, which bills by the hour, removes it.

#### The code

#### Do it: the ceilings from the kit's files, then your lane's

The first cell reads the four ceilings from the kit's files and does the arithmetic for 1k, 10k, 100k and a million claims a month. The second block reads the same values from your lane: the API's scale and concurrency, the deployed index's machine and replicas, and whether quota.tf's override is in your Terraform state.

The files and the lane agreed: 20 instances, 40 at a time, a 120 s cut, 1 replica, and no override in the state, so on your lane today nothing of the kit's own caps generation calls. The arithmetic turned each ceiling into a busiest-minute factor, which is the number a 3 names. A desk that expects bursts, a newsroom on an election night for instance, now knows the factor it has to stay under, and which ceiling it meets first if its claims slow down.

"At ten times our top volume the first limit is the project's Gemini quota of 600 a minute, which we have switched on: it binds when our busiest minute reaches 26.3 times our average, and the chat service shares it. If claims slow past 80 seconds, the 800 slots bind first. The index's one replica is unmeasured, so we load-test it before we promise the volume."

### Evals: what blocks, what advises, and what cannot fail

Computed checks block, the judge advises, and 11 rows assert what the retriever already guarantees.

#### Definition

The kit's gate is `evals/run_eval.py`: 9 thresholds and 15 required rows over 65 golden rows (47 answerable), scored by code, green or red. The judge reads the same answers and explains them; its docstring calls it the other judge, and its last line says the gate decides. The fact desk keeps that split and adds one check to the blocking side. The quote check runs on every claim before a verdict is written, and as a threshold in the desk's own eval, because the passage it checks against is the very text the model read. The kit's live eval measures quote support against the tenant's whole corpus and reports it as information only, because a Doc AI extraction and a pypdf mirror hyphenate differently; the desk has no second copy to disagree with.

Then the rubric's hardest point: which assertions cannot fail. Of the 65 golden rows, 12 carry `must_not_contain`, and 11 of those are isolation rows. They are vacuous: the retriever filters by tenant before the generator reads anything, so another tenant's figure can appear only if the model invents it, which `check_isolation()` calls a hallucination lottery. What replaced them is `isolation_403_rate` at 1.00, asked by `documind-outsider-sa`, an account on no tenant's roster. The one version row is not vacuous: its figure lives only in a revision under `evals/demo`, and a version the ledger failed to retire can say it. For the desk, one more check would be vacuous: asserting that a quote is at most 200 characters, which `ModelDraft` and `_draft()` enforce before any eval could see it. The 25-word rule is not vacuous, because only the prompt asks for it, so `quote_holds()` keeps it. Lesson 4.1, next, builds the rows an eval like this is made of.

#### The code

#### Do it: the gate offline, and the rows that cannot fail

The offline gate judged the golden set itself and passed: every row can fail, which is a different claim from every row being worth having. The second cell sorted the `must_not_contain` rows by whether anything upstream stops them failing: the isolation rows by the retriever's tenant filter, the version row by nothing but the ledger. That sorting, and the gate that replaced the vacuous rows, is the 3 on this dimension, and it is the same sorting a desk's own rows will need.

### Next month: the top item comes from the rows

A 3 is an observation from operating, not a plan from before; the kit's own history shows what one looks like.

#### Definition

The fifth dimension cannot be designed in advance, and that is its point: a 3 is a top item nobody planned, found by running the thing. A design page can show only the shape. The kit's comments are a record of exactly this kind of item, each one reordering work because a live run showed something no plan had:

For the fact desk, a month of verdict rows answers the questions that could reorder its work: the share held for a person, by tenant, which separates a prompt problem from a corpus problem; the share not in our files, which separates a corpus missing documents from claims about things the tenant never wrote down; the judge's low scores on standing verdicts, which find passages that support less than they are quoted for; and the cost of a claim against the ceiling. A 3 names the one that surprised you, and says what it pushed down the list.

### Verify it yourself: the checklist

Eleven checks, each one block above, each with what passing looks like.

Nothing. Every cell on this page read the kit's files or your lane's settings and rows: the offline cells call nothing, and the reads in steps 6 and 7 write nothing. The fact desk is still a design; building it would add a service with its own account, which needs `roles/run.invoker` on documind-api and a place on each tenant's roster, and its own verdict row. Lesson 4.1 opens Module 4 with the rows an eval is made of, which is where a desk like this one would start proving itself.

Netsetos GenAI on GCP · Module 3 Generation · Lesson 3.9 System design: a fact-checking system built from DocuMind's parts · v5.0

Next: Lesson 4.1 Build a useful evaluation dataset.
