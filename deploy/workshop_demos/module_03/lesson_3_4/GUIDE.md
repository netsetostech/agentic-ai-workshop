# Lesson 3.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_3.4_Context_Budget_WIX.html`, reviewed at blob `451850344630a66cad10a9fdc60c7712b39b2c4f`. Learners read that page on the course site; this guide keeps its prose.

Module 2 ended with a ranked pool. This lesson is about the space it has to fit into. A prompt is a sum of lines, the system rules, the question, the evidence, and a reserve for the answer, and the kit gives the evidence whatever is left of a total after the fixed parts are counted. `pack_chunks()` fills that room most relevant first, one `[Source N]` header per chunk carrying the file, the page and the date the document declares, drops what does not fit and logs the drop, and the citations resolve against what was packed. The count behind all of it is an estimate, four characters a token, and a real counter can be injected where the estimate misleads. You will read the budget's lines from the kit, pack real chunks offline with the kit's own functions, put the model's counter beside the estimate for English and for Hindi, read one answer's `tokens_in` against the estimate of its packed set and price it in rupees, watch a dated document put its date on the header and the dated rule in the prompt, and shrink the budget on a candidate revision to see the drop line appear.

- What a prompt is made of, and why the evidence gets the remainder

- The words: budget line, fit, estimate, counter, header, dated rule, drop, reserve, tokens_in, price

- Before you run anything: set up the shell

- The budget's lines and the packer, offline on the kit's own documents

- The model's counter beside the estimate: English, Hindi, and a pool trimmed by the exact count

- One answer's tokens: the packed set's estimate, the model's count, and the price

- A dated document on the lane: the header's date, the rule in the prompt, the citation event

- The answer's reserve, the retry, and the tokens on the rows

- What the budget costs, the knob on a candidate, and the lines this lesson leaves empty

- Verify it yourself: the checklist

You will learn what the five lines of a request's budget are, how the API computes its own with `TokenBudget.fit()`, why packing is most relevant first with a header per source and a log line per drop, and why the four-characters rule is an estimate that a real counter can replace. Then you will prove it on your lane: pack the kit's documents offline, count with the model, read `tokens_in` and price an answer, see a document's date reach the header and the citation event, and shrink the budget on a candidate that takes no traffic.

### What a prompt is made of, and why the evidence gets the remainder

Five lines, one total, a packer that walks the ranker's order, and a count that is an estimate until a counter says otherwise.

A prompt has lines, and the budget is their sum. The kit's `TokenBudget` names five: the system prompt, a tenant pack that Module 6 fills as a cached prefix, the chunks, a rolling history that the chat service keeps, and a reserve for the answer. The kit's teaching split is 1,500, 40,000, 6,000, 2,000 and 2,000 tokens. The API builds its own with `fit()`: it counts the fixed parts of its prompt, the system rules, the dated rule held in reserve, the scaffolding and the question, and gives the chunks whatever is left of `max_context_tokens`, 8,000 by default, with the pack and history lines at zero because this service holds neither. Until 12 September the whole total went to the chunks and the fixed parts rode on top, so every full request was over budget by their size.

Packing is most relevant first, one header per source. `pack_chunks()` walks the ranker's order. Each block is a header and the chunk's text; the header is `[Source N]` with the file's name, the page when there is one, the section, and `effective from` a date when the ledger stamped one on the row, which the worker read off the document's first lines or its name. A block that does not fit is dropped whole, never cut, and the walk goes on, so a smaller chunk later in the order can still get in. Every drop is one `context_budget_drop` line in the log, because "the answer got worse after we added documents" starts there. The model cites by `[N]`, and `resolve()` maps that number against the packed list, never the pool. When any packed chunk carries a date, a sixth rule joins the system prompt: follow the source with the latest effective date, cite it, say from when it applies. The five rules themselves never change, so the tuned model is served behind the prompt it was trained behind.

The count is an estimate until a counter says otherwise. `estimate_tokens()` is the length in characters divided by four: close for English prose, wrong for a script that costs more tokens a character, which Devanagari does. So `pack_chunks()` takes a `count_fn`: after packing by the estimate it asks the counter for the exact size and trims from the tail while it exceeds the budget; the API passes the estimate, and the model's own `count_tokens` can be passed in its place, there and in `fit()` alike. What the packed set finally costs is on the answer as `tokens_in`, the model's own count of the prompt, and `cost.price()` turns it into dollars and rupees at the model's rate, with cached input at a tenth. The answer's reserve is 2,048 tokens because thinking draws from the same output budget and a cut-off JSON was once scored as a refusal; when a first attempt is cut off, the generator asks once more with three times the room and bills both.

The briefing folder. A secretary fills a folder for a minister who reads a fixed number of pages. The cover note and the question go in first and take their pages. Then the evidence, most important memo first, each with a tab that names the file, the page and the date it took effect; a memo that would not fit stays on the desk, and a note on the folder says how many stayed. The folder is weighed by page count, a rough scale that is right for typed English and wrong for a dense script, so a real scale stands beside it and when the real scale says heavier, the last memos come out. The reply has its own page allowance, and a reply that runs over is asked for again with triple the pages. The minister cites tabs, never memos that stayed on the desk.

#### The packing bench: the kit's rules on the kit's chunks

Pick a golden question. The pool is acme's own chunks in the order lesson 2.2's BM25 leg puts them, standing in for the ranker's. The bench applies `fit()` to the fixed prompt, packs the first `top_k` chunks by `pack_chunks()` with the kit's headers, and shows the lines, the packed and dropped sets, the log line, the estimate of `tokens_in` and the rupee price of the request at the model's rate. Two switches change the arithmetic: a counter that reads more than the estimate, as the model does for some scripts, and the dated smoke note from Module 1 put first, whose date reaches its header and adds the sixth rule.

Computed when this page was built by the kit's own code: the chunks are acme's mirrors through `shared/documind_corpus.py`, their order lesson 2.2's BM25 port; the fixed prompt is `generator.SYSTEM` and the dated rule; the rates are `cost.py`'s for `gemini-3.6-flash` at USD_INR 85. The packing, the headers and the trim are the kit's functions, line for line, in JavaScript.

It is not the ranker: BM25 orders the pool here because the ranker needs your lane, and the API's order for the same question can differ. It is not the model's counter either: the second counter is a stand-in that reads sixty percent more everywhere, where the real one reads more for some scripts and less for others; step 4 puts the real one beside the estimate.

### The words: budget line, fit, estimate, counter, header, dated rule, drop, reserve, tokens_in, price

Ten rows, each with the value it takes on your lane.

One number to keep apart from the rest: `top_k` is how many chunks the packer is offered, and the budget is how many it keeps. At the default budget the two agree for handbook sections and disagree for full Act pages, which is the whole reason the drop line exists.

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

The budget's total, the answer's reserve, the model and the rupee rate live in the API's environment, each with a default the page names; a name the service does not set is unset rather than exported empty, because steps 4 and 5 import the kit and its settings class reads an empty variable as a value.

### The budget's lines and the packer, offline on the kit's own documents

The class, the fit, the header and the packer, run on the handbook, the dated smoke note and the CGST Act with no cloud call, and a counter injected to watch the trim.

#### Definition

Everything in `context_budget.py` is pure Python: the class with its five lines, `fit()`, the estimate, the header and the packer, and the generator adds only the fixed prompt it counts and the log line it writes. The cell rebuilds the API's budget for one question from the generator's own strings, cuts three documents with the kit's chunker, stamps the smoke note's date the way the worker does with the worker's own reader, and packs two pools twice each: handbook sections, which fit at any `top_k`, and full Act pages, which do not. Then it injects a counter that reads more than the estimate and watches the packer take chunks back off the tail. Its output below was produced when this page was built, by the same code on the same files, so what you see on your machine should match it to the token.

#### The code

#### Do it: the lines, then two pools twice, then a counter

The two budgets told the story in one line each: the teaching split reserves room for a cached tenant pack and a chat history the API does not carry, so the API's own fit gives almost the whole total to the chunks after 168 tokens of fixed prompt. Handbook sections fit at twenty; full Act pages do not, and the log line said so. The headers carried what a citation needs, the file, the page, the section, and for the smoke note the date the worker's reader took off its first lines, which is the line that adds the dated rule. Then a counter that reads more than the estimate made the packer take pages back off the tail, which is the trim loop doing for a denser script what the estimate could not.

### The model's counter beside the estimate: English, Hindi, and a pool trimmed by the exact count

count_tokens on the global client, the ratio it gives for a handbook clause, a Hindi clause and an Act page, and twenty pages packed by each counter.

#### Definition

The model counts its own tokens, and on Vertex AI the 3.x family answers `count_tokens` from the `global` location, like generation; it is not billed as generation. The cell counts three texts both ways: the notice-period clause, a Hindi sentence of the same kind, and one full Act page. English prose lands near the estimate; Devanagari costs several tokens where the estimate sees one, because the rule of four characters was written for Latin script. Then it packs twenty Act pages twice, by the estimate and by the model, which is exactly what injecting `count_fn` into the API would do: the second pack asks the model for the context's exact size and trims while it exceeds the budget.

#### The code

#### Do it: three texts, two counters, one pool twice

For English the estimate landed near the model's count, which is why the API can afford to pack by it. For the Hindi clause the model counted well above what the estimate saw, so a handbook in Hindi packed by the estimate would overrun the budget the API thinks it kept, and the counter is the fix the code already allows: injected, it trims the pool by whatever the exact count exceeds. The pool of English pages packed the same or a page fewer under the model's count, which is the estimate's error showing up at the tail.

### One answer's tokens: the packed set's estimate, the model's count, and the price

The proof this lesson is named for: what one question's packed set cost, on the answer, against the estimate of the same set, priced by the kit's own function.

#### Definition

Every answer carries `tokens_in`, the model's count of the whole prompt, `tokens_out`, which on the 3.x family is the answer and the thinking together, and `cached_tokens`, the prompt tokens a context cache served, zero on this lane. `cost.price()` reads a price table from BigQuery and falls back to the rates in the file: the billable input at the model's rate, cached input at a tenth of it, the output at its rate, in USD and in INR at the rate carried with the figure, so two numbers for one month cannot exist. The cell asks one question at `top_k` 5, prints the four fields, prices them again with the kit's function, and, when lesson 2.3's saved pool is on disk, packs the same five chunks offline and puts the estimate beside the model's count.

#### The code

#### Do it: one question, its tokens, its price, and the estimate beside it

One question's packed set was five handbook sections, and its price was the model's count of the prompt times the input rate plus the answer and its thinking times the output rate: well under a rupee, with the rupee figure carried beside the dollar one. The kit's function reproduced the answer's `cost_usd` exactly, because it is the same function. The estimate of the same set came within a tenth of the model's count, and the difference is the tokenizer's, not the packer's: the schema the model is asked to fill and the scaffolding cost a few tokens the four-characters rule does not see.

### A dated document on the lane: the header's date, the rule in the prompt, the citation event

The smoke note's revision 2 declares a date; the worker stamps it on every row; the packer puts it on the header, the generator adds the sixth rule, and the stream's citation event carries it out.

#### Definition

A document declares when it applies in its first lines, `Effective from: 2026-10-01`, or in its object name for a PDF nobody can edit; the worker's reader takes the date, the ledger row keeps it, and `indexer.py` stamps it on every chunk row. From there the packer prints it on the source's header, `_dated_rule()` appends rule six to the prompt because a packed chunk carries a date, and the stream's citation event carries `effective_from` to the caller, which is the only place outside the container the header's date can be seen. The cells re-issue the smoke fixture's revision 2 under the smoke's own name, wait for the worker, stream the question and read the event, then put revision 1 back the way the smoke does.

#### The code

#### Do it: the dated revision in, the stream read, revision 1 back

Revision 2 came back with the date the ledger had kept for it, nothing embedded, and the question was answered from its rows: the citation event carried `effective_from 2026-10-01`, which is the row's stamp, which is what the packer wrote on the header the model read, and the answer said from when the fact applies because rule six was in the prompt for this request and not for the handbook's. Then revision 1 came back, undated, and the same question would again be answered without the rule. Lesson 1.6 did this to the handbook; the header and the rule are why it mattered.

### The answer's reserve, the retry, and the tokens on the rows

Why the reserve is 2,048 and not 1,024, what the generator does when a first attempt is cut off, and where the tokens of a day are read.

#### Definition

The output reserve is what the model may spend on the answer and, on the 3.x family, on the thinking before it: both draw from `max_output_tokens`. At 1,024 a statute answer with its quotes ran out fourteen times in one live eval, and each cut-off JSON was scored as a refusal, which is why the setting reads 2,048 and why the generator, when the finish reason says the cap was hit and no draft could be parsed, logs `generation_truncated` and asks once more with three times the room. Both attempts are billed and summed into the row, because a truncated-then-retried answer used to cost the tenant two calls and count as one. The rows carry the tokens of every answer, and `make usage` sums them by tenant with the rupee column beside; the log carries the retries, and a lane whose reserve is right has none.

#### The code

#### Do it: the day's tokens, and the retries there were not

The day's tokens sat in two columns with their price beside them, which is the budget seen from the bill: `tok_in` is the packed sets of every answer plus their fixed prompts, and a wider `top_k` or a larger budget moves that column before it moves anything else. The log held no truncation, because the reserve was sized for the answers this corpus produces, and the drop lines it held were the ones you caused on purpose.

### What the budget costs, the knob on a candidate, and the lines this lesson leaves empty

The rupee line, a candidate revision with a budget too small for five sections, and the two budget lines that belong to later modules.

#### What it costs

#### The knob: a budget too small, on a candidate that takes no traffic

`max_context_tokens` is a setting, so the way to see the drop on the live corpus without touching the live service is a candidate revision, as in lessons 2.2 to 2.4: a budget of 600 tokens leaves room for about three handbook sections after the fixed prompt, so the same question at `top_k` 5 packs three, drops two, logs the drop, and answers from what it packed. The variable is not set on the live service, so the undo removes it and the default returns.

#### The lines this lesson leaves empty

Two of the five lines are zero in the API's budget on purpose. The tenant pack is a stable prefix of the tenant's corpus that a context cache serves at a tenth of the rate, from 4,096 tokens up, and Module 6 fills it: on the answer it appears as `cached_tokens` inside `tokens_in`. The history is the chat service's rolling summary, and Module 6 keeps it outside this API. The budget class knows both so that the sum can be read in one place when they are filled; the packer only ever sees the chunks line.

A budget a thirteenth of the default packed three sections and dropped two, the log said so, the answer came from the three, and the live service never knew; the variable came out again and the template returned to the default. That is the whole shape of the knob: a number in the environment, judged on a candidate, with the drop line and `tokens_in` as the two measurements, and lesson 7's eval as the judge of whether the smaller prompt still answers.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

Nothing that serves traffic. The smoke fixture went to revision 2 and back to revision 1, where lesson 1.8's smoke leaves it; a candidate revision took no traffic and its variable was removed before the tag was dropped. The questions you asked are usage rows with their tokens on them. Lesson 3.5 takes the packed set into the model and out again as a contract: the draft the model fills, the citations resolved to real chunk ids, and the refusal on an empty pool.

Netsetos GenAI on GCP · Module 3 Generation · Lesson 3.4 Pack evidence within the context budget · v5.0

Next: Lesson 3.5 Generate structured answers, citations and refusals.
