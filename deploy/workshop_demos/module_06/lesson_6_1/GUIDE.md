# Lesson 6.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_6.1_Context_Architecture_WIX.html`, reviewed at blob `272457217222d6e81f3450e0a57382c64f84b1d3`. Learners read that page on the course site; this guide keeps its prose.

A model keeps nothing between calls. Each time a chat brain calls Gemini it sends the whole context again: the system prompt, the tool declarations, the thread so far and the question, and from the second call on the model's own calls and what the tools gave back. This lesson takes one turn apart, source by source, on each of DocuMind's five brains, and prices every source in rupees. Then it moves one setting, TOP_K, to see which part of the bill moves with it. You run it offline first, for Rs 0, then on your lane, where the model's own counter counts each source.

- What rides every model call

- The words: context, source, system prompt, tool declaration, thread, question, the model's calls, tool result, rag-api's own call, estimate, count_tokens, residual, TOP_K, list price

- Before you run anything: set up the shell

- The UI: one number for the whole turn

- The kit: where each brain assembles its call

- Offline: one turn split by source, for Rs 0

- On your lane: the model's own counter, and the probe

- Five brains, one question, on your lane

- Change it: TOP_K, and which part of the bill moves

- The thread rides every call too

- Why the split is measured this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what a brain sends its model on each call of a turn, source by source, and what each source costs. Then you will prove it on your lane: one turn on each brain split into its system prompt, tool declarations, thread, question and tool results, with their tokens and rupees, and one setting moved to see which part of the bill moves with it.

### What rides every model call

A model keeps nothing between calls, so each call carries the whole context, and each token of it is billed on every call it rides.

A model keeps nothing between calls. Gemini answers each request from what that request carries, and from nothing else. A chat brain's turn is usually two calls. In the first the model asks for a search; in the second it answers from what came back. So the second call has to carry everything the first did, plus the search. A request has three fields, and the kit's command, `make context-sources`, splits them into six sources. The system instruction is the system prompt. The declared functions are the tool declarations. The contents, the conversation as a list of turns, are the thread so far, the question, the model's calls earlier in this turn, and the tool results those calls brought back.

Every token is billed on every call it rides. gemini-3.6-flash costs $1.50 per million input tokens: Rs 0.1275 a thousand, at the kit's Rs 85 to the dollar (`shared/prices.py`). The system prompt, the declarations, the thread and the question ride every call of the turn. The model's calls and the tool results ride every call after the search. A long system prompt or a long list of tools is paid for twice in a two-call turn, and up to 12 times in a turn that runs to the chat service's cap.

The brains assemble the request differently. LangChain's `create_agent` and the hand-built LangGraph node send the same request, token for token. ADK adds a line of its own to the system prompt and declares the same two tools in a longer form. The Desk's statute agent, the one lesson 10.5 runs, brings its own prompt and 4 tools. The direct brain makes no model call of its own: rag-api's answer is the turn.

The search has a model call inside it. A chat brain's `retrieve` asks rag-api's `/v1/query`. rag-api packs the top_k chunks into a prompt of its own and answers with its own model call; lesson 3.4 shows how it packs that prompt. rag-api bills the call on its own usage row, and the turn's Meter charges it to the turn. What comes back to the chat model as its tool result is not the chunks. It is the citations rag-api's answer chose, each a quote of one clause. The Desk's search asks `/v1/passages` instead, which returns each passage's whole text and makes no model call.

A trunk call to a consultant who keeps no notes. You pay by the minute, and the consultant forgets everything when the line drops. So every call starts the same way. You read out the standing instructions, the list of errands you can run for him, what was said on every earlier call, and today's question. When he asks for a record, you hang up, send a runner to the record room and call again: the whole file once more, and now the runner's slip as well. The record keeper is paid by the page he reads, and his slip carries only the lines he chose to quote. Ask him to read three files instead of five and his fee drops, but the slip you read out on the next call changes little. Ask the record room for photocopies of whole files instead, and every file it reads is one more thing to read out on the next call.

The consultant is the model and each call is a model call. The standing instructions are the system prompt, the errands are the tool declarations, the earlier calls are the thread and this turn's own requests, and the slip is the tool result. The record keeper is rag-api, whose own model call reads top_k chunks and quotes the clauses its answer chose. The photocopies are the Desk's `/v1/passages`.

#### One turn, by source: every brain, every source, in tokens and rupees

Pick a brain, a TOP_K and a turn. Each bar is one model call, split by source and drawn to one scale; the grey bar is rag-api's own call inside the search. Pick a bar to list its sources, with each one's tokens, its share of the call and its rupees. Under it is the turn by source, as the command prints it.

Computed when this page was built: the kit's own command, `context_sources.py --offline --json`, run 16 times on the kit you clone, once for each brain, TOP_K and turn the buttons offer. The brain, its adapter, its tools and its limits ran as they run on your lane. A script answered at the google-genai boundary in the model's place, and the search was the Rs 0 lane's, over the kit's own corpus. Every count is an estimate, a quarter of the characters each part carries (rag-api's own estimator), so the sources add up exactly; on your lane the model's own counter counts them (step 6). The rupees are list price on those estimates. Offline, nothing is billed.

The fixed price of asking. On a fresh turn, the LangGraph brain's first call is 361 tokens, and 346 of them (96%) are the system prompt and the tool declarations; the question is 15. The second call carries all of that again, plus the model's own call (21 tokens) and the search's result: 1,143 tokens, 67% of them tool results. Over the turn the declarations cost Rs 0.0612, 16 times what the question costs, because they are longer and ride both calls. On the statute desk, the prompt and its 4 declarations are 98% of call 1.

The search holds the biggest call. Inside the search, rag-api's own prompt is 1,957 tokens: its system prompt 105, the 5 chunks it packed 1,834, the question 18. That is more than both of the chat model's calls together, 1,504. The turn costs Rs 0.5018: Rs 0.2370 for the chat model's two calls and Rs 0.2648 for rag-api's answer. The direct brain pays the second alone, Rs 0.2648. The Desk pays no rag-api call at all, but its tool results are whole passages: 1,939 tokens, and Rs 0.5147 for the turn.

TOP_K, offline. Set TOP_K to 3 and two things shrink. rag-api packs three chunks instead of five, 1,095 tokens in. The tool results drop from 761 to 435 tokens. The system prompt, the declarations and the question do not move. Offline, the search returns all of the top_k passages, as if rag-api had cited every one. On your lane it returns only the citations rag-api's answer chose, so there TOP_K mostly moves the grey bar, not the orange one. Step 8 measures the difference. The Desk's passages move on both.

It is not your lane. The script does not think, so no call carries thinking tokens, and nothing was cached. Its tool results are the Rs 0 lane's citations: every one of the top_k passages, each quoted to up to 500 characters, where rag-api's are the clauses its answer chose, at most twenty-five words each, or a passage's first 500 characters for a source the answer cited only in its prose. And every count is an estimate. Step 6 runs the same turn on your lane, where each call's tokens are its own usage and each source is counted by the model's `count_tokens`.

### The words: context, source, system prompt, tool declaration, thread, question, the model's calls, tool result, rag-api's own call, estimate, count_tokens, residual, TOP_K, list price

Fourteen rows, each with the value it takes on your lane.

One distinction to hold: the model is billed per call, not per turn. A source that rides every call is paid for on every call, so the same thousand tokens cost twice as much in a turn that calls the model twice.

### Before you run anything: set up the shell

You need three things open: the DocuMind UI at `https://documind-ui-NUMBER.REGION.run.app` signed in as a roster member, the operator shell you set up in Module 0 (the `rag-shell-venv` environment, the kit at `$DEMO_ROOT` as a clone of the public learner repository, and the restart helper), and a Python cell in that same shell or in Colab with `google-cloud-firestore` installed and Application Default Credentials. Every command on this page is one you run; every output shown is what the lane prints. Where a value belongs to your lane (a project number, a hash), it is written as `NUMBER` or shortened with `...`.

Set up the shell once per session. The block below works on any machine with `git` and `gcloud` signed in. The first time, it clones the kit from the public learner repository, `netsetos/agents_workshop_learner`, into `~/deploy_module_rag`; every session after, it pulls the latest kit. Then it reads your project from the gcloud configuration (so there is nothing to type), moves into the kit, builds the API URL from the project number, and defines two small functions that mint identity tokens. The last line proves the API answers.

`PROJECT=` empty means gcloud has no default project on this machine: run `gcloud config set project YOUR-PROJECT-ID` with your real id, then the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login` first. A `ModuleNotFoundError: No module named 'google'` from any `make` target or Python cell, or an `externally-managed-environment` error from the pip line, means this shell is not inside the venv: the prompt should start with `(rag-shell-venv)`, so run the `source` line of the block again. If that line says the file is missing, the environment was never made on this machine: Module 0's install is `python -m pip install -r shared/requirements.txt -r services/ingest/requirements.txt -r services/rag-api/requirements.txt -r services/mcp/requirements.txt`, run inside `rag-shell-venv`; the setup block installs the one package this lesson needs. `adc NOT ok` means Python's own sign-in, Application Default Credentials, cannot read Firestore. The Python cells and every `make` target that reads Firestore use it, and gcloud's sign-in does not cover it. `Reauthentication is needed` in the message means the credentials file is there but your organisation's session rules have expired it; a `make` target reports the same as `RetryError: Timeout of 60.0s exceeded` after a minute of retries. `insufficient authentication scopes` or `credentials were not found` means there is no file, and Python fell back to the machine's own service-account token, which covers the bucket but not Firestore. Either way, run `gcloud auth application-default login --no-launch-browser`, open the link it prints, sign in as the account you use on this lane, paste the code back, and run the block again. A fresh workstation instance (the hostname changes) needs this again, as it needs the venv again. If `gcloud` itself asks you to reauthenticate, run `gcloud auth login`: the two sign-ins are separate, and each can expire on its own. `git clone` failing means this machine cannot reach GitHub. `git pull` refusing with Your local changes would be overwritten means a kit file was edited on this machine: `git -C "$DEMO_ROOT" status` names it, and `git -C "$DEMO_ROOT" stash` sets the edit aside. On a machine where Module 0 copied the kit file by file, the first run keeps that copy as `~/deploy_module_rag-before-git.tgz` and turns the folder into a clone; untracked files, `.terraform` and saved `.tfvars` stay where they are. If your kit lives somewhere else, set `DEMO_ROOT` before the block. A `403` from `print-identity-token` means your account lacks the Service Account Token Creator role on the two accounts; Module 0 granted it to the operator. If your machine has the restart helper from Module 0 (`commands/session-restart.sh` in the kit), `source` it and run `rag_resume` in place of the `export PROJECT` and `export ME` lines: it restores the same values from your saved session and also sets `API_URL`, which you then copy into `API`.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into the operator shell, whole, and press Enter; the Python cells are wrapped in `python - expected or log, is text to read: it is the kit's own code or the output you should see, and it has no copy button.

#### make, or the command it runs

Every `make` target on these pages is a short entry in one of the kit's `mk/*.mk` files; this lesson's, `context-sources`, is in `mk/memory.mk`. The entry runs a script under `commands/` or the kit's own Python, and you can run that directly: the same code, the same output, no make. `PROJECT` comes from the setup block above.

#### Which store answers acme? Pin it to the kit's own index for this lesson

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. `make up` pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like `acme:acme_497809ff...#rag-532341da71fe`, a `page` of `null` even for a PDF, and `stages.retrieval_backend: rag_engine`. This lesson reads what a search hands the chat model, so point acme at the kit's own index for the duration, whose citations carry the kit's chunk ids and pages as the offline runs' do, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

How to tell which store answered any call: read `stages.retrieval_backend` on the response and `stages.vector_chunks` beside it. With the pin on `vector`, the backend says `vector` and `vector_chunks` equals the pool. The stamp behind that count, `found_by`, sits on each chunk inside the API and is not a field of a citation; lesson 2.3 shows how to join it to one. The chunk ids are the kit's `tenant:sha256#position` form with the page on every PDF citation.

Calls from the shell impersonate `documind-ui-sa`, the UI's own account, which `make roster` put on the three golden tenants (acme, zeta, globex). That is why a shell call can name any of the three. `otok` mints a token for `documind-outsider-sa`, an account IAM admits into the service and no roster lists. Tokens last about an hour; the functions mint a fresh one on every call. Your browser session is different: IAP signs you in as yourself, and the roster maps your email to exactly one tenant. Keep the two apart in your head: step 3 asks in the browser as you, and every lane run from step 6 on searches as `documind-ui-sa`.

The shell, in the kit's folder, with `PROJECT` and `REGION` from the setup block, and acme pinned to the kit's own index with the setup section's `make tenant-backend` line. Step 3 asks two questions in the DocuMind UI's chat, which lesson 5.1's step 3 deployed. `make context-sources` runs in `~/graph-venv`, lesson 5.4's venv with the chat image's pins. Its first run makes the venv if it is missing and installs `services/chat/requirements.txt` into it, which takes a few minutes. Step 5, and the first cells of steps 8 and 9, run offline for Rs 0. Steps 6 to 9 run real turns on your lane, a few rupees each, and each output's last lines price yours. Nothing is configured. The Desk's run in step 7 searches the classes `statute` and `guidance`, which acme's rows carry only once lesson 10.4's doc_type registry has pinned them.

### The UI: one number for the whole turn

The chat page's caption gives the turn's bill as one figure. Nothing on the page says what the figure bought.

#### Definition

On an agent brain, the DocuMind UI's chat page writes a caption under each answer: the brain, the tools it called, the time it took and the rupees. The rupees are the limits the chat service returns with the turn: its Meter's model calls and rag-api's answers, at list price, rounded to two places. That is the whole turn's bill in one number. It does not say how much went on the system prompt, the declarations or the search. It cannot show the thread either, though every later turn in the session carries it.

#### The code

#### Do it: in the browser

Open the DocuMind UI in a new browser tab, so the chat starts a new session, and go to the chat page. Choose the brain `langgraph` and ask: After how many years of continuous service is gratuity payable? Read the caption under the answer. Then ask the same question again, in the same tab, and read the second caption.

Two turns, two numbers. The second turn carried the first one whole, as its thread: the first question, the model's call, the citations and the answer, on each of its own calls. The caption has no way to show that, or what any rupee of either figure bought. Do not read much into the difference between the two figures: each includes an answer of rag-api's, which varies from one ask to the next, and the caption rounds to two places. If a caption says `tools: none`, the model answered from the thread without searching, and that turn paid for no rag-api answer. The rest of this lesson takes a turn apart by source.

### The kit: where each brain assembles its call

One prompt and two tools, put in front of the model three ways; the Desk's own prompt and tools; and a brain that makes no call at all.

#### Definition

The chat brains share one prompt, `brains.SYSTEM`, and one tool list, `retrieve` and `calculate_processing_cost`. Each puts them in front of the model its own way. LangChain's `create_agent` takes the prompt as `system_prompt` and sends it with every model call. The hand-built LangGraph brain binds the tools to its model once. Then its node builds each call's message list itself: the prompt first, then the conversation from the checkpoint, which never stores the prompt. ADK's `LlmAgent` takes the prompt as its `instruction`. ADK then adds a line of its own naming the agent, and declares each tool with `parametersJsonSchema`, titles and defaults included.

A tool's declaration is made from its name, its docstring and its arguments: the model reads the docstring as the tool's description. What the search hands back is the adapter's projection of rag-api's answer: the citations, `answerable` and `confidence`, and nothing of rag-api's own answer text. The Desk's statute agent has its own prompt and 4 tools: `retrieve`, `gratuity_estimate`, `statutory_deadline`, `threshold_check`. Its `retrieve` asks `/v1/passages` with top_k 5 and gives the model every passage's whole text. The direct brain calls no model of its own: one search, and rag-api's answer is the turn.

#### The code

The system prompt and the declarations are written once in the kit and sent on every call of every turn, so they are the first thing to look at when a brain's calls cost more than you expect. ADK's two extra pieces, its line and its longer declarations, ride every one of its calls. The projection decides what a chat brain's tool result weighs: a few citations, each a short quote, never the chunks rag-api read. The Desk's tool results are the chunks themselves. The direct brain skips the chat model's loop altogether, and the agent brains must beat it to justify the calls they add (lesson 5.7).

### Offline: one turn split by source, for Rs 0

The kit's command reads each call where the adapter hands it to google-genai, splits it at the turn's question, and counts each part.

#### Definition

`make context-sources` runs one turn on a brain, built as `services/chat` builds it, with its thread kept on your machine (an `InMemorySaver`, or ADK's in-memory sessions), so your lane's threads are never read or written. For the run it wraps google-genai's two `generate_content` methods: the one LangChain's `ChatGoogleGenerativeAI` calls and the async one ADK's `Gemini` calls. So it reads what each adapter handed the SDK: the system instruction, the declarations and the contents. `label()` splits the contents at the turn's question. Before it is the thread; after it, a model content is the model's calls and a function response is a tool result.

`OFFLINE=1` puts a script in the model's place at that boundary. The script asks for a search for the question, then answers from the first passage found. The brain, its adapter, its tools and its limits run as they run on your lane. The search is the Rs 0 lane's `retrieve` over the kit's corpus, with no network and no credential. rag-api's own call inside it is estimated from `generator.py`'s prompt: its `SYSTEM`, the chunks `pack_chunks` fits in what is left of `max_context_tokens`, and the question. Every count is rag-api's own estimator, so each call's sources add up to exactly what the script reports it was sent.

#### The code

#### Do it

The same without make: `bash commands/graph-venv.sh commands/context_sources.py --offline --brain langgraph`. The first run makes `~/graph-venv` if it is missing and installs the chat image's pins into it; pip's notices may print before the output.

The header names what rides every call: a system prompt of 426 characters, the brain's own, and two declarations, each with its `parameters`. Model call 1 is 361 tokens: the system prompt 106, the declarations 240 and the question 15, and nothing else yet. It asked for `retrieve`. Under it is the search: top_k 5, 5 citations back in 2,004 characters, and inside it rag-api's own call, 1,957 tokens in.

Model call 2 is 1,143 tokens: the same three sources again, the model's call (21) and the tool results (761). The residual is 0 on both calls, because offline the script's input is the sum of its parts. Then comes the turn by source: each source's tokens over both calls, its rupees, and how it rode, `106 in each of 2 calls` for the system prompt and `from call 2 on` for the results. The model calls cost Rs 0.2370, and the line says the turn's Meter charged the same: the command prices each call as `limits.py` does. rag-api's answer adds Rs 0.2648, estimated. The turn is Rs 0.5018 at list price, and offline nothing is billed.

The kit holds this for every brain. Its test reads every captured call and checks that each content has one source and that the sources add up to what the call was sent. CI's chat-pins step runs the file on every push, and the file has 25 tests in all.

### On your lane: the model's own counter, and the probe

A real turn, each call's tokens from its usage, and each source counted by `count_tokens` in context. The probe at the end says whether the counter took every field.

#### Definition

Without `OFFLINE`, the turn is real. Gemini answers on location global through the brain's own model. Each search goes to your lane's rag-api as `documind-ui-sa`: the make target sets `RAG_API_URL` from your project's number, and `DOCUMIND_IMPERSONATE_SA`. The turn runs under the chat service's limits, 12 calls, Rs 5 and 100 s. Each call's tokens are its own `usage_metadata`: input, cached, output and thinking. Thinking is billed as output, and a cached token at a tenth of the input rate.

Then the command counts each source with the model's own `count_tokens` on location global, which is not billed. A piece counted on its own need not add up to its share of a request, so the command counts in context. It counts the question alone, then with the thread before it, with the system instruction, with the declarations, and then with each later content in turn. Each source's tokens are what adding it added, so the sources sum to the request's count. The residual is what the call billed less that count. A field `count_tokens` refuses, or accepts and counts as nothing, is estimated instead, marked `~`, and named in the probe at the end of the output.

#### The code

#### Do it: the probe

Whether `count_tokens` on location global takes the declarations and the system instruction at all was not known when the kit was written. The probe settles it before any count on this page is trusted, for both forms of declaration: LangChain's `parameters` on the LangGraph brain, and ADK's `parametersJsonSchema`. The cell prints only each run's probe. Step 7 shows the whole of each run.

`system_instruction: honoured: +N` means adding the system prompt raised the count by N, so the endpoint counts it. `tools: honoured: +N` means the same for the declarations, in the form this brain's adapter sends. Either line could instead say `refused: ...` or `accepted, but counted as nothing`. Then that source is estimated and marked `~` in the breakdown, and the residual shows how far off the estimate is. `contents: counted` means every content after the question was counted in context, including the model's function call and its result.

The last line compares call 1's count with its bill. A residual of a few tokens at most says `count_tokens` and the bill agree on what the call carried. Call 2's residual is in its own lines of the full output (step 7). If it is larger than call 1's, something rode call 2 that the counter did not count. A thought signature is one candidate: Gemini 3 attaches one to the function call it makes, the adapter sends it back on the next call, and the offline estimate counts nothing for it. The same line ends with the number of `count_tokens` requests the run made, none of them billed.

### Five brains, one question, on your lane

The same question through each brain: what each one sends, what its search hands back, and what the turn costs.

#### Definition

One real turn on each brain, with the same question each time. What differs is the request each brain assembles and what its search hands back. On the chat brains the tool result is the citations rag-api's answer chose. Inside each search the command prints rag-api's own call from the usage rag-api returns: its tokens in, cached and out, and its rupees. On your lane that call is not split into its prompt, its chunks and the question; lesson 3.4 measures rag-api's prompt. The Desk's search is `/v1/passages`, with no model call inside. The direct brain makes no call of its own, so its output is the search and rag-api's call alone.

The Desk searches the classes `statute` and `guidance`, and a row on your lane is `unknown` until lesson 10.4's doc_type registry pins its class. Before that, the statute desk's searches find no passage. Its tool results are then empty lists, and the model may search again in other words before it says the passages do not answer.

#### Do it

Read the five outputs side by side, a source at a time.

The fixed parts. The system prompt and the declarations count the same on every call of a turn, and the same for langchain and langgraph. ADK's are larger: its system prompt carries the framework's line, and its declarations are JSON Schema with titles and defaults. Offline the estimate put ADK's at 120 and 341 tokens to LangChain's 106 and 240. Your counts are the model's own.

The tool results. On the chat brains they are the clauses rag-api's answer cited, a short quote each unless the answer cited a source only in its prose, so they usually weigh less than offline, where every passage came back with up to 500 characters. On the Desk, when its search finds passages, they come back whole, and they are the largest source of any call that carries them.

The output. Thinking is output, billed at the output rate. The LangChain and LangGraph brains run their model with thinking low (`shared/profile.py`), and so does the Desk's agent. ADK's brain sets no thinking level, so its calls may think more.

The search's own call. On the chat brains and the direct brain, rag-api's answer is the line under the search, and its rupees are on the turn's bill as rag-api's. On the direct brain it is the whole bill.

The Meter. The model calls' rupees equal what the turn's `limits.Meter` charged. The chat service charges the same Meter on `/v1/chat`, and its total is step 3's caption.

### Change it: TOP_K, and which part of the bill moves

Three passages instead of five, offline and on your lane, on a chat brain and on the Desk.

#### Definition

`TOP_K=K` makes the command send `top_k` K with every search of the run, whatever the model asked for. `retrieve`'s declaration, and its default of 5, do not change, so the request the model reads is the same. What moves depends on what a search returns. Offline, the Rs 0 lane's search returns every one of the top_k passages, so the tool results shrink with TOP_K, and rag-api's estimated prompt packs three chunks instead of five.

On your lane, a chat brain's search is rag-api's `/v1/query`. rag-api packs top_k chunks into its own prompt and answers. `resolve()` then builds one citation for each source the answer cited, and for no other, with the quote the answer gave: rule 5 of rag-api's prompt keeps it to the clause that answers, at most twenty-five words. A source the answer cites only as an `[N]` in its prose comes with no quote, so its citation carries the passage's first 500 characters. The chat model's tool result is those citations. So on your lane TOP_K moves rag-api's own prompt, and rag-api's share of the turn's bill. It moves the tool results only as far as the answer's choice of clauses changes. The Desk's `/v1/passages` returns all of its top_k passages, whole, so TOP_K moves the Desk's tool results on both lanes.

#### The code

#### Do it: offline, the two records side by side

`make context-sources` prints its breakdown; with `JSON=1` it prints the turn as one record instead, the command's `--json`. Write one record with TOP_K unset and one with TOP_K 3, then compare them source by source.

Offline, exactly the two lines the kit's test pins moved: the tool results, from 761 tokens to 435, and rag-api's own prompt. The search's citations went from 2,004 characters to 1,087. The turn went from Rs 0.5018 to Rs 0.3504: Rs 0.2370 to Rs 0.1955 for the model calls, and Rs 0.2648 to Rs 0.1549 for rag-api.

#### Do it: on your lane, a chat brain and the Desk

Compare this one with step 7's `langgraph` output:

And this one with step 7's `desk` output:

Read three lines in each pair. The search line says `top_k 3 (TOP_K; 5 asked)`, and how many citations or passages came back, in how many characters. Under it, rag-api's own call: on `langgraph` its tokens in should drop by about the two chunks it no longer packs. Then the tool results in the second call. On `langgraph` they are the clauses rag-api's answer chose from what it packed. If the answer cited the same clauses from three chunks as from five, the tool results barely move. On the Desk every passage comes back whole, so the tool results drop by about the two passages it no longer returns.

The setting that looks like a knob on the chat model's context is, on your lane, mostly a knob on rag-api's. Offline it looked like the chat model's because the Rs 0 lane hands back all of its top_k passages. When a number you measured offline moves differently on your lane, look first at what the lane's search returns.

### The thread rides every call too

Three turns on one local thread, the third one measured: the earlier turns ride both of its calls, untrimmed.

#### Definition

`TURNS=3` asks two earlier questions on the same thread first: How many days of earned leave can I carry forward?, then Is gratuity payable to a contract employee? The thread lives in the command's own `InMemorySaver`, or for ADK in its in-memory session service, never in your lane's checkpoint database. The third turn is the one measured. Everything the first two left in the thread rides both of its calls: two questions, the model's calls and their citations, and two answers. Nothing trims it, and rag-api's own `TokenBudget` says as much in a comment: the chat brains resend whole threads. The direct brain and the Desk keep no thread, and the command refuses `TURNS` for them: `refused: direct keeps no thread (brains.DirectBrain answers one retrieve), so its turns are all first turns: leave TURNS out`.

#### The code

#### Do it: offline

The thread is 1,451 tokens on each call, 80% of call 1's 1,812. Over the turn it is 2,902 tokens and Rs 0.3700, more than everything else the two calls carried together. Every other source is the fresh turn's, token for token. The two earlier turns cost Rs 1.0857 on their own (4 model calls and 2 searches), and this one Rs 0.8718. TOP_K reaches the earlier turns' searches too: with TOP_K 3 the same thread is 909 tokens, as the widget in step 1 shows.

#### Do it: on your lane

Compare it with step 7's `langchain` run. The system prompt, the declarations and the question count as they did there. The thread is the new line, with the same count in each call. Any cached tokens on these calls are what each call's own usage reported as cached, billed at a tenth of the input rate, and the `cached` line prices them. Every turn adds its question, its calls, its citations and its answer to the thread, so the thread is the one source that grows with the conversation and never shrinks. Lesson 6.2 compares DocuMind's two caches. Lesson 6.9 budgets the thread: windowing, compaction and what a turn may write.

### Why the split is measured this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

At the SDK boundary, not in the framework. Every brain's model call passes through one of two google-genai methods, so one wrapper reads all of them. What it reads is what the adapter actually sent: ADK's extra line, its JSON Schema declarations, LangChain's conversion of the tools. The frameworks' own message objects would show none of the three.

Counted in context, not piece by piece. On your lane each source is what adding it to the request added, so the sources sum to the request's own count, and the residual against the bill shows what the counter missed. A field the counter will not take is estimated and marked, never quietly dropped.

rag-api's estimator offline. `OFFLINE=1` counts with `estimate_tokens`, the same rule `pack_chunks` budgets rag-api's prompt with (lesson 3.4), so the offline split adds up exactly and agrees with rag-api's own packing.

A local thread, never a lane thread. `TURNS` asks its earlier questions on a thread of the command's own. A lane run writes no thread and no chat row; rag-api logs each search as it logs any.

TOP_K at the search, not in the declaration. The model reads the same request either way, so whatever the bill does, the search did it.

#### What it costs

#### What the kit does not do yet

- No split on the chat row. `agent.py` logs a turn's `tokens_in` and its cost, never what they were spent on. The split exists only when you run this command.

- No trimming of the thread. Every turn resends all the earlier ones (step 9). Lesson 6.9 budgets it.

- No cache under the chat brains' calls. rag-api's tenant cache (lesson 6.2) sits on rag-api's prompt. The chat brains' fixed parts, a few hundred tokens, are far below the 4,096 tokens an explicit context cache needs on the Gemini 3 family (`cache_manager.py`).

- Only a local thread. The command measures a turn it runs itself; it cannot split a turn a person had in the UI. `make thread` (lesson 6.8) reads those back from the lane.

- The Desk needs lesson 10.4's registry on the lane. Until acme's rows carry their classes, the statute desk finds nothing to read.

- Offline, a thought signature counts as nothing. The script sends none, and the estimate copies none; only your lane's residual can show what one adds.

### Verify it yourself: the checklist

Eleven checks, each one block above, each with the value that proves it.

Nothing is configured. rag-api's log has a usage row for each search your lane runs made: event `query` for the chat brains and the direct brain, each with the brain's name, and event `passages`, with no tokens and no cost, for the Desk. `TURNS=3` added the searches of its two earlier turns. `make context-sources` wrote no thread and no chat row: its threads lived in its own process. Step 3's two questions are one session in your chat service's checkpointer, with two chat rows and a rag-api row for each search they made. `~/graph-venv` has the chat image's pins, and your home folder has `~/cs_default.json` and `~/cs_top3.json` from step 8. Put acme's pin back now, with the setup section's pin-back window. Lesson 6.2 compares the two caches DocuMind has: a cached prefix the model still reads, and a stored answer the model never sees.

Netsetos GenAI on GCP · Module 6 Context and memory · Lesson 6.1 Assemble the context: what rides every model call · v5.0

Next: Lesson 6.2 Compare context caching and answer caching.
