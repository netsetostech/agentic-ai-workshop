# Lesson 5.7: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_5.7_Adapters_WIX.html`, reviewed at blob `38fb9d89de6f76a3929d154aa4d2e3b39a759159`. Learners read that page on the course site; this guide keeps its prose.

The chat service can answer with four brains, and all four reach the same `retrieve()`. What differs is the adapter between each framework and that one tool. It decides what the model is shown, what is filled in behind its back, what the model reads back and what happens when a call fails. It also decides where the conversation is kept and what gets counted. You put the LangChain adapter beside the ADK adapter offline, on the kit's own code. You also see the turn's limits from lesson 5.5 wired into each harness its own way. Then you ask one question through all four brains on your lane and read the four cost lines that rag-api's rows and the chat rows give together. Last, you take each agent's loop apart, call by call.

- One tool, four harnesses

- The words: adapter, harness, ToolRuntime, FunctionTool, REQUEST, callback, session, limits, cost line

- Before you run anything: set up the shell

- Two adapters over one tool, side by side

- Four brains on /health, and the module's gate

- Four cost lines, from rag-api's rows and the chat rows

- The loop, call by call

- Why the adapters differ, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn the six things an adapter decides, how the kit makes the LangChain and ADK adapters decide them alike, and what the two harnesses still decide differently. You will also see the same turn limits wired three ways, and why a cost line needs two kinds of row: rag-api's for the search, the chat service's for the loop. Then you will prove it: four brains and one `limits` block on `/health`, one answer from each through the module's gate, a looping model stopped by every harness, four cost lines from the rows, and each agent brain's own model calls, call by call.

### One tool, four harnesses

What an adapter decides, and why two frameworks decide it differently.

The tool is one. `shared/documind_tools.retrieve()` is the only code that talks to rag-api. A brain decides when to call it and what to do with the result, and nothing more. Between each framework and that function sits an adapter. The adapter decides six things: what the model is shown, what is filled in behind it, what the model reads back, what happens when a call fails, where the conversation is kept, and what gets counted.

The LangChain adapter wraps. The LangChain and LangGraph brains use `services/chat/tools.py`: two `@tool` functions, `retrieve` and `calculate_processing_cost`. The tenant, the person's assertion and the brain's name arrive through `ToolRuntime`, which the framework injects and leaves out of the schema. So the model is shown `query`, `doc_type` and `top_k`, and nothing else. The adapter's `search()` drops rag-api's own answer from the result, rewords a failure and numbers each citation for the turn. The framework turns a bad argument, a missing one or an unknown name into an error result, which the model reads and explains.

The ADK adapter is the same adapter. ADK's `FunctionTool` builds a declaration from a Python function's signature and docstring, so whatever the function takes, the model is shown. The ADK brain therefore wraps the two plain functions `tools.for_adk()` returns, which take only what the model may choose and end in the same `search()`. The tenant, the assertion and the brain reach them through `tools.REQUEST`, a context variable the brain sets for the turn. Two callbacks give ADK LangChain's error contract: `on_tool_error_callback` turns a name ADK does not hold, a refused argument or a mistyped one into an error result, and `after_tool_callback` marks ADK's own answer to a missing argument as one. What still differs is the harness: the loop, where the conversation is kept, the thinking level, and how many characters each framework spends declaring the same tools.

The limits sit at each harness's own seam. Lesson 5.5's `Meter` is one object, made by the chat service for each turn, and every agent brain checks it before each model call. Where the check goes is the harness's choice. The LangChain brain adds one middleware, `TurnLimitsMiddleware`, that wraps the model call. LangChain also ships `ModelCallLimitMiddleware`, an off-the-shelf call cap, but it hooks in before and after the model as two graph nodes of its own, so every turn would save more checkpoints. The LangGraph brain has no middleware: its `agent` node checks the Meter itself. The ADK brain uses three model callbacks, before the call, after it and on its error, and keeps `RunConfig.max_llm_calls` as a backstop the Meter reaches first.

The cost line has two halves. The direct brain has no loop: one `retrieve()`, and rag-api's grounded answer is the answer. Every `retrieve()`, from any brain, leaves a row in rag-api's log with the brain's name, the tokens and the cost. The agent's own model calls, at least two a turn for each agent brain, are on the chat service's row for the turn: its model calls, tokens and cost, priced at `cost.py`'s rates. The two halves add up to the line. rag-api's half looks alike for all four brains, because it counts the one thing they share. The chat row's half is where they differ.

A sub-registrar's record room, and four ways to get a certified copy. The record room is one. Every request goes through its counter, and its register notes the fee and the name of the clerk who asked. One clerk follows the office manual, with a supervisor checking each slip. One follows a flowchart you drew yourself. The third comes from an agency with its own way of working, but the record room hands it the same slips as the others, with no box for "whose file?": the name is written on the clerk's token at the door. When a slip is rejected, this clerk comes back to explain, as the other two do. The fourth window simply hands you the copy. The register shows four nearly equal fees. The clerks' own time, which is where they differ, is written on each clerk's own docket. And each clerk, however they work, stops after the same number of trips to the counter.

#### Two brains, side by side

Choose two brains to see how each decides the 15 things below. The rows where they differ are shaded.

Each value is read from the kit's code at build time. The arguments, the character counts, what each model reads and the failures come from step 3's cell, run on the kit's `brains.py` and `tools.py` with google-adk 2.8.0.

It compares the adapters as the kit builds them, not the quality of their answers. Lesson 4.2's judge scores answers. With `CHAT_URL` set, `make judge` also checks each agent brain's tool calls against the one call the kit expects, a single `retrieve`.

### The words: adapter, harness, ToolRuntime, FunctionTool, REQUEST, callback, session, limits, cost line

Eleven rows, each with the value it takes on your lane.

One distinction to hold: an adapter decides what crosses the boundary, and a harness decides how many times it is crossed. Both show up in the cost line, and the Meter caps the second.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `tok`. You need `~/graph-venv` from lesson 5.4. Step 3 adds google-adk and the Gemini client to it, and makes it if it is missing. The chat service must be running in your region, from lesson 5.1's step 3. Step 4 asks one question through each brain, and step 6 asks it three more times from your machine. Run steps 4 to 6 in the same shell, in order. Nothing changes on your lane.

### Two adapters over one tool, side by side

The kit's LangChain brain and the kit's ADK brain, each with a model that says what it is told, against a rag-api on your machine that notes what it is sent.

#### Definition

The cell builds the kit's `LangChainBrain` and `AdkBrain`, each with a scripted model. A stand-in rag-api on your machine notes the tenant, the brain and the assertion header of every request, and answers. The cell prints five things:

- What each model is shown for `retrieve`: the arguments, the required ones starred, and the declaration's size. A third line, `raw`, is what ADK would show for the shared `retrieve()` wrapped as it is. Then each brain's tools.

- One `retrieve()` through each adapter. The ADK model writes `tenant_id` "globex" and `assertion` "anything", arguments it was never shown. The cell prints what rag-api received, which keys the model read back, and the number each citation carries.

- Four calls that go wrong: a blocked name, an argument of the wrong type, a tier the tool does not know, and a call with its required argument missing.

- Where ADK keeps sessions when no database is configured, and its cap on model calls.

- The turn's limits, wired three ways. A model that asks for a tool on every call, under a `Meter` capped at 2, through each agent brain. Then one turn with one tool call through `create_agent` twice, with the kit's middleware and with `ModelCallLimitMiddleware`, counting the graph's nodes and the checkpoints the turn saves.

The LangGraph brain uses the same `tools.py` as the LangChain brain, so its schema, its results and its failures are the same. Its guard is the refuse node from lesson 5.4. `commands/tests/test_chat_brains.py` runs the same comparison across all three agent brains in CI, in the chat image's pins.

#### The code

#### Do it: the venv

#### Do it: side by side

Both models were shown the same three arguments: LangChain's declaration in 481 characters, ADK's in 635, because each framework writes declarations its own way. The `raw` line is what `for_adk()` replaces: seven arguments, two of them required, in 3,420 characters, carried by every model call. Both requests reached rag-api for acme, with no assertion header. The ADK model's globex and "anything" went nowhere: `for_adk()`'s `retrieve` has no argument for them, so ADK dropped them, and the tenant came from `REQUEST`. Both models read the same three keys, and the one citation carried `n` 1, the number the answer cites it by.

Then the four failures. Both brains turned all four into error results, which the model read, and `refusals` named each one. In ADK, `for_adk()` checked the arguments with the `@tool`'s own schema, so the wrong type was refused by the rule LangChain applies. `tool_failed` turned that refusal, the unknown tier and the unknown name into error results, and `mark_error` marked ADK's own answer to the missing argument, which comes with no status. The words differ, because each framework writes its own; the contract is the same. Anything else still ends the turn in every brain, the token mint from lesson 5.5 among it: `tool_failed` passes on only a name ADK does not hold and a `ToolException`.

Last, the limits. All three brains stopped the looping model after its second call, with the same sentence, though each checks the Meter at a different place: a middleware, a node, a callback. The LangChain brain's graph still has only its `model` and `tools` nodes, and a turn with a tool saves 5 checkpoints. With `ModelCallLimitMiddleware` the graph gains two nodes, and the same turn saves 9. That is why the kit wraps the model call instead: lesson 6.6 counts these checkpoints.

### Four brains on /health, and the module's gate

The list the service promises, then one answer from each brain, then the outsider refused.

#### Definition

`/health` returns the four names in `BRAINS`, a constant in `brains.py`, and one `limits` block for all four. It builds no brain and imports no framework. Each brain is built on its first turn, and a framework the image lacks is a 501 then. `make smoke-chat` is Module 5's gate. It reads `/health` and asks one question through each brain as `documind-ui-sa`, a member of acme. For each answer it checks that `retrieve` was among the tool calls and that the answer does not say retrieval was unavailable. Each answer must carry its `limits`: no stop, the model calls within the cap, and, for an agent brain, a cost above Rs 0. From every brain it also wants citations. An agent brain's citations must be numbered 1 to k, and every `[n]` in its answer must name one of them. The direct brain's `[n]` is a place in rag-api's packed context, and its citations are only the sources the model quoted, so its markers are not checked. Each run asks in new sessions. Then it asks as the outsider and expects the roster's 403. The cell first saves the time, for step 5.

#### The code

#### Do it

`/health` listed four brains and the limits every turn on them runs under: the first half of the proof. That list is a promise. The four answers are the check: each brain was built, called `retrieve()` and answered from the corpus. The first turn of each agent brain was the slow one, because it imported its framework. Each agent brain made two model calls and reported their cost; the direct brain made none of its own. The outsider was refused by the roster before any brain ran.

A brain fails the gate if it answers with no citation. An agent brain also fails if it cites an `[n]` it did not return. The `FAIL` line shows the numbers, the citations and the markers it found. Each run of the gate starts new sessions, so running it again asks the same first question, and no conversation grows.

### Four cost lines, from rag-api's rows and the chat rows

One row per retrieval and one per turn, added up by brain.

#### Definition

Each `retrieve()` leaves one row in rag-api's log. The row holds the brain that asked, the tokens rag-api spent, and the cost at its model's rate. Each chat turn leaves one row in the chat service's log: the brain, its own model calls, their tokens and their cost, at the same rates. The cell reads both kinds of row since step 4, adds them up by brain, and prints each line whole. A line's whole can differ from the same turn's rupees in step 4's smoke line by Rs 0.0001: the response rounds the turn's rupees once, to four places, while each row keeps its dollars to six places and the cell adds the two. `make usage` draws rag-api's half of the same table over whole hours. The cell saves the four lines to `~/lesson104_lines.json`.

#### Do it

Four lines, one `retrieve()` each. rag-api's half is within a few paise across the brains: every brain asked rag-api the same question, and rag-api did the same work each time. The direct brain returned that answer. The agent brains paid for it too, and their adapter dropped it. The chat rows' half is where the brains differ: the direct brain made no model call of its own, and each agent brain made two, the ADK brain's the larger. That is the second half of the proof: four cost lines from the rows.

A line with 0 retrievals means that brain made no `retrieve()`. A line with 2 means its model searched twice. With the answer cache on (Module 6), a repeated question is a hit: cost 0, and backend `cache`.

### The loop, call by call

The kit's three agent brains on your machine, asking the same question, each model call counted.

#### Definition

The chat row adds up a turn's model calls. The cell takes one turn apart. It builds the kit's three agent brains on your machine from the same `brains.py` the image runs: the same model, system prompt, tools and limits. It asks the same question once through each brain, through your rag-api, as `documind-ui-sa`, each with a `Meter` of its own. Then it reads the usage each framework keeps for each call: LangChain on every `AIMessage`, ADK on the session's events. Thinking is counted as output, as Vertex AI bills it. Under each brain it prints the Meter's totals, which is what the chat row would record, priced by `shared/prices.py` at `cost.py`'s rate for gemini-3.6-flash.

#### Do it

Each agent brain made two model calls: one to ask for `retrieve`, one to answer from what came back. The second call carries everything the first did, plus the tool result, so it is the larger. The ADK brain's calls are still larger than LangChain's, though both show the same arguments and read the same result. ADK declares the same tools in more characters, 635 against 481 for `retrieve`, and adds a line of its own to the system instruction. Your run can show a third reason: the ADK brain sets no thinking level, and the LangChain brains set it to low.

The Meter's totals are the calls added up, in each brain, whichever seam it was charged at. Each agent brain costs its retrieval plus its own loop, and the direct brain costs its retrieval alone. The loop is the price of the harness, and it is paid on every turn.

### Why the adapters differ, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- The tenant is not an argument. If it were an ordinary parameter, the model would choose the tenant, as `agent.py`'s docstring puts it. `tools.py` keeps it out of the schema with `ToolRuntime` for LangChain, and out of ADK's declaration by declaring a function that does not take it. Both keep the boundary out of the model's sight.

- One retrieval, one adapter, one tool list. `documind_tools.py` allows no second implementation, and `tools.py` allows no second adapter: `for_adk()` copies each tool's docstring from `TOOLS` and ends in the same `search()`. A tool added for one framework is a tool added for both.

- The brain is a switch, not a fork. Brains are built lazily and cached, and a missing framework is a 501, not a failed start. That is why `/health` can list four names without importing anything, and why the gate has to ask each brain.

- Errors as data. The shared `retrieve()` returns a failure as data, so the model can explain it rather than the turn dying. The LangChain framework does the same for bad arguments and unknown names, and ADK does it through `for_adk()`'s check against the same schema, `tool_failed` and `mark_error`. Every such result carries status `"error"`, and that status is what `refusals` counts, in every brain. Anything else, such as a token that cannot be minted, still fails the turn.

- One Meter, each harness's own seam. The limits are counted in one object the chat service makes, and checked where each framework allows it without changing its shape: a wrapper around the model call, the node that makes the call, the callbacks around it. The frameworks' own caps stay as backstops.

- The direct brain is the floor. `brains.py` calls it the one the other three have to beat to justify their harness. Step 6 measures what they have to beat.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The month's totals leave the loop out. The chat row carries each turn's own cost, but `tenant_daily` and `make usage` read rag-api's rows only. So the by-brain table in `evals/usage_rows.py` still compares the one thing the brains share, and a tenant's monthly figure has no agent model calls in it. Lesson 11.6 takes this up.

- ADK's guard cannot fire yet. ADK looks a name up before `before_tool_callback` runs, and no blocked name is declared, so `guard_tool`'s refusal is unreachable; a blocked name reaches `tool_failed` as a name not found. It becomes reachable when a tool that needs approval is declared.

- The error words are each framework's own. The status and `refusals` agree across the brains; the text the model reads for a wrong type or a missing argument is written by LangChain or by google-adk 2.8.0, and differs.

- The brains are not configured alike. The LangChain brains set `thinking_level` low, and the ADK brain sets none. A cost comparison of the harnesses is also a comparison of their settings.

- `/health` lists a constant. It builds no brain, so a framework missing from the image still shows on `/health`, and answers 501 on its first turn.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

Nothing is configured. The three agent brains each keep the gate's conversation in a new session, `smoke-` and the brain's name and the run's id, one per run of the gate. The direct brain keeps none. rag-api's log has seven more rows, four from the gate and three from step 6. The chat service's log has four more rows, one for each of the gate's turns, with the turn's model calls and cost. Your home folder has `~/lesson104_lines.json`, and `~/graph-venv` has google-adk. Lesson 5.8 pauses a turn for a person: approval, clarification and escalation. Module 6 picks up these conversations, and lesson 10.4 later sends the other questions to one desk each.

Netsetos GenAI on GCP · Module 5 MCP and agents · Lesson 5.7 Compare the LangChain and ADK adapters · v5.0

Next: Lesson 5.8 Pause, approve, clarify and escalate: human in the loop.
