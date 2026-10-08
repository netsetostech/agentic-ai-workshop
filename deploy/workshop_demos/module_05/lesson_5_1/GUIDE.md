# Lesson 5.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_5.1_Agent_Loop_WIX.html`, reviewed at blob `95a50fda25e996ce7c223e579e4c5a7596c02941`. Learners read that page on the course site; this guide keeps its prose.

An agent is a model that is allowed to call functions. What it may call, with which arguments, and what comes back is a contract, and the kit writes that contract once. Every brain shares one `retrieve()`. The tenant reaches a tool through the runtime, never through an argument the model fills. A failure comes back as data. You deploy the chat service in your lane's region and read the contract the model sees. Then you call the one `retrieve()` from your shell, and ask the same questions of two brains: the direct brain, which has no loop at all, and the LangChain loop, which decides for itself.

- A tool is a contract, and the direct brain is the floor

- The words: tool, schema, runtime context, adapter, brain, tool_calls, refusals

- Before you run anything: set up the shell

- The chat service, in your lane's region

- The contract: what the model reads of each tool

- The one retrieve(), from your shell

- The direct brain: one retrieve(), no loop

- The loop: the model chooses its tools

- The rows: what each brain cost, and which row records it

- Why the contract is shaped this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what a model can and cannot see of a tool, why the kit keeps identity out of the model's reach, and why one retrieval function adapted per brain beats one per brain. You will also learn why the direct brain is the number an agent has to beat. Then you will prove it on your lane: the model-facing contract, a direct-brain answer with `retrieve` in `tool_calls`, the loop choosing a second tool on its own, and the rows that show what each turn cost.

### A tool is a contract, and the direct brain is the floor

What the model reads, what the runtime supplies, and a loop against no loop.

A tool is a contract with three parts. The model reads a name, a one-line description, and the arguments it may fill, each with a type and sometimes a default. That is the tool's schema. The runtime supplies everything else, and returns a result in a fixed shape. The model never runs code. It emits a request, "call `retrieve` with this query", and the runtime executes it and hands the result back as a message. So whatever the model can write, it can change. Whatever must not change belongs outside the schema.

Identity is outside the schema. In the chat service, the tenant is looked up from the roster using the verified caller's email, and placed in a runtime context. The tool reads it from there. The request has no tenant field, and the model-facing schema has no tenant argument, so neither the caller nor the model can choose one. A question that names another tenant is still searched in the caller's own corpus. The person's IAP assertion travels the same hidden way, to rag-api, so the retrieval is made in their name.

One retrieval, adapted per brain. `shared/documind_tools.py` holds the only function that reaches the corpus. It posts to rag-api, or reads a Chroma directory on the laptop lane. The chat service's `retrieve` tool is an adapter: it binds the tenant, renames the filter and reshapes the result, and calls that one function. The course's own check refuses a second implementation, however it is named. A failure comes back as data, `{"error": ...}`, so the model can say retrieval is down instead of the turn dying on an exception.

The direct brain is the floor. The chat service has four brains behind one endpoint. Three are agent loops: LangChain, LangGraph and ADK. The model reads the question and the tool schemas, calls tools, reads the results and decides again. The fourth, `direct`, has no loop. It calls `retrieve()` once, in code, and returns rag-api's own grounded answer. It is the cheapest and fastest brain, and it cannot do anything but look things up. An agent justifies its extra model turns only by answering what the floor cannot, or answering it better.

A government office counter. The clerk may use two registers, and the counter sheet lists what each one needs: a file number, a year. The sheet has no line for "whose file". The office fills that in from the token you were given at the gate, so no one at the counter can ask for someone else's file. At the simple window, an attendant takes your question, looks up the one register and reads out the entry. At the full counter, a clerk decides which registers to consult and in what order, and can do the arithmetic the attendant cannot. The simple window is where you judge whether the full counter is worth its wait.

#### One turn, two brains

Choose a brain and a question, and follow the turn: what the model reads, what the runtime adds, which tools run, and the two lists that come back.

The schemas are LangChain's own `tool_call_schema` for the kit's two tools, read at build time; the cell in step 4 prints the same from the source. The `tool_calls` and `refusals` come from the kit's `_summary()` run on these turns, and the direct brain's from `DirectBrain.answer()` run with a stand-in `retrieve()`. The loop's steps are the path a well-behaved model takes; on your lane, the model decides.

It shows the contract and the plumbing, not a model's judgement. A model may call `retrieve` twice, or skip the page-count search, and step 7 shows what yours did. Blocked tools, timeouts and refusals are lesson 5.5's subject, and the hand-built LangGraph loop is 5.4's.

### The words: tool, schema, runtime context, adapter, brain, tool_calls, refusals

Eleven rows, each with the value it takes on your lane.

One distinction to hold: the schema is what the model can change, and the context is what it cannot. Everything about identity lives in the second.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `ME`, `API` and `tok`, and `adc ok` from the setup block. Step 3 builds the chat service's image and deploys it in your region, which takes several minutes. Steps 5 to 7 ask five questions through rag-api and the chat service. Nothing else changes.

### The chat service, in your lane's region

A redeploy with the kit's current script, then where it points and which brains it builds.

#### Definition

`make up` deploys the chat service from `commands/lesson-12.8.sh`. Until 23 September 2026, that script named `us-central1` in all fourteen places a region appears. That meant the image registry, the service, the Cloud SQL instance, the migration job, and two URLs: `RAG_API_URL`, where the brains send every retrieval, and `SELF_URL`. The API's own script follows `REGION`, and Terraform creates the image registry in `REGION`. So on a lane in asia-south1, the chat build pushed to a registry the lane does not have, and the deploy stopped there: no chat service was created at all. Had one been, it would have called an API that does not exist. The kit's script now follows `REGION` in all fourteen places. The cell below runs just that script through `make deploy-services`. It builds the chat image, deploys it beside your API, grants the invoker role, runs the checkpointer's one-time migration and turns on IAP. The invoker role goes to seven accounts: the UI's account, the outsider, and five eval accounts the DocuMind Desk's live checks call the service as. Terraform creates them. The loop names an eighth, the account a Google Chat bridge calls the service as, which exists only on a lane planned with `GCHAT_DOOR=true`, as lesson 10.4 shows, and then it is bound too. The script prints a "not bound" line for each account that does not exist yet and binds the rest, so on a lane without the door the bridge's account gets that line. `ADMIN_EMAILS` is your own address, so the target's last step, the operator grant, succeeds.

#### Do it: deploy

#### Do it: where it points, and its brains

The chat service now runs in your region, and its `RAG_API_URL` is your API, the one the setup block reached. `/health` lists the four brains the image can build, and the default one: LangChain, from `DOCUMIND_BRAIN`. If the describe cell cannot find the service, or names another region's API, the deploy ran the old script. Check with `git log` that the kit is current, and run the cell again.

### The contract: what the model reads of each tool

The two tools as the model sees them, and the parameter it never sees.

#### Definition

LangChain builds a tool's schema from its signature and its docstring. The adapter's `runtime: ToolRuntime` parameter is filled by the framework and left out of the schema. That is the one kind of hidden parameter that is also delivered. The first version of this file used `InjectedToolArg` instead, which hides an argument and never fills it: the tool ran with an empty tenant, and rag-api refused it. The chat request itself has only three fields, and none of them names a tenant. The cell reads `services/chat/tools.py` as text and prints each tool the way its schema presents it, so it needs no LangChain on your machine. Its last line calls the shared `calculate_processing_cost`, the function the chat's cost tool hands its arguments to, with the tier `'express'` and prints its refusal. That refusal is the text the chat tool returns to the model as an error result. The build checked the printout against LangChain's own `tool_call_schema` for all 2 tools.

#### The code

#### Do it

Two tools, and not one argument names a tenant, a user or an assertion. `retrieve` has a hidden `runtime`, which is where agent.py's context arrives, and passes what it reads to `search()`, where every brain's retrieval ends. `calculate_processing_cost` needs none, because pricing pages concerns nobody's documents; it hands its arguments to the shared function, so an unknown tier is refused here as it is there. The first line of each docstring is the description the model uses to choose a tool, so a vague docstring is a tool the model picks at the wrong time.

### The one retrieve(), from your shell

The function every brain calls, called directly, as a roster member.

#### Definition

`retrieve()` builds the request itself: the query, the tenant, `top_k` limited to 1 to 20, and no stream. It adds a Bearer ID token minted for rag-api, and the person's assertion when there is one. It returns the citations, the verdict and the confidence, plus rag-api's own answer. A network failure becomes a dictionary with `error` set. From a shell there is no metadata server to mint the token, so `DOCUMIND_IMPERSONATE_SA` mints it as `documind-ui-sa`, the same account `tok` uses, through your Application Default Credentials. The cell also notes a start time, which step 8 uses to read the rows.

#### The code

#### Do it

Your shell ran the same function the chat service's brains run, and got the same contract back: five citations, a verdict, a confidence, and rag-api's own answer. That last field is the direct brain's whole job; the agent brains throw it away. A failure here prints `document retrieval is unavailable`, the tool layer's own words: a wrong `RAG_API_URL`, a missing role, or `adc NOT ok`. Those are the same words a model would read in a tool result, so it could tell you what went wrong.

### The direct brain: one retrieve(), no loop

A chat turn with no model in the chat service, and the tenant it was answered for.

#### Definition

`/v1/chat` first looks up the caller's tenant from the roster, then builds the thread id from the tenant, the user and the session, then hands the brain a context: the tenant, the user, the assertion and the brain's name. `DirectBrain.answer()` calls the one `retrieve()` with the question, the tenant from the context and `top_k` 5. It returns rag-api's answer with the citations, and `tool_calls` set to `['retrieve']`. That list is written by the code, not chosen by a model, because there is no model in this brain. The cell defines `chat10`, a small function that posts one turn as `documind-ui-sa` and prints the brain, the two lists, the citations (with their numbers, when an agent brain numbered them), the time and the start of the answer. `documind-ui-sa` is on three rosters, and `tenant_for()` takes the first, acme.

#### The code

#### Do it

A direct-brain answer with `retrieve` in `tool_calls`: this lesson's proof. The answer is rag-api's, with five citations, in about the time of one rag-api call. That is the floor. Every agent answer that follows has to justify its extra seconds against it. The turn was made for acme because the roster said so. Nothing in the request could have said otherwise.

### The loop: the model chooses its tools

The same question to the LangChain brain, then a question only a tool can answer, to both brains.

#### Definition

The LangChain brain is `create_agent` with the two tools, the system prompt and a guard. The model reads the question and the schemas and emits tool calls; the runtime runs them and returns each result as a message; the model decides again until it answers. The checkpointer hands back the whole conversation, so `_turn()` gives each question an id, and `_summary()` reads only that question and what follows it. `tool_calls` is every tool call the model made in this turn, in order. `refusals` is every tool result marked as an error. `citations` is every passage this turn's searches returned, numbered from 1 by `search()`; the system prompt asks the model to cite them as `[n]`. Every brain returns the same four keys, so the UI never asks which brain answered. The cost question needs a page count and a multiplication. The system prompt asks the model to search for a page count before it estimates a cost.

#### The code

#### Do it

On the policy question, the model chose `retrieve` itself and wrote its own answer from the citations; it took longer than the direct brain for the same fact. Its citations are numbered 1 to 5, and its answer cites `[1]`. The cost question went to the same session, so the thread held the first turn too, and the list still names only this turn's two tools, with its citations numbered from 1 again. The second tool, `calculate_processing_cost`, priced 33.96 US dollars for 283 pages at the priority rate, Rs 2,886.60. The direct brain could only look the question up, and could only answer from what the documents say. The two brains may even give different numbers, because they consult different sources: the tool's price list, and whatever rate a document mentions. Your lists are the truth for your lane. A model that skipped the search, or searched twice, is still inside the contract.

### The rows: what each brain cost, and which row records it

rag-api's row for every retrieve(), and the chat service's row for every turn.

Each `retrieve()` posts to rag-api's `/v1/query`, and rag-api writes its usage row, now labelled with the brain that asked. The chat service writes a row of its own for each turn: the brain, the tenant, the user, the session, the time and the two lists, and the turn's own model calls, their tokens and their cost, beside what its searches billed. Lesson 5.5 shows the limits those numbers are counted against. The cell reads both kinds since step 5, the shell's own retrieval included, labelled `ui` because it named no brain.

Every `retrieve()` left one rag-api row, whichever brain made it, and each row is a full answer: retrieval, reranking and a model call. The direct brain's row is its whole cost. The LangChain brain's rag-api row is only part of its cost. It paid for rag-api's grounded answer, threw that answer away, and then paid its own model to write another. Those model turns are on the chat service's row: the keys printed beside each turn include `model_calls`, `cost_usd` for its own calls, and `rag_cost_usd` for what its searches billed. That is why the floor matters. The direct brain makes no model call of its own, so its rag-api row states its whole cost.

### Why the contract is shaped this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- One retrieval, checked by shape. Nobody copies `retrieve` and keeps the name. The second copy is called `quick_lookup`, written under deadline for a different `top_k`. So the course's check parses the tool layer for any function that takes a query and reaches the corpus itself, and allows adapters that delegate.

- Removing a field beats validating it. The chat request once carried `tenant_id` and `user_id`, and the agent believed them. A validation is something a later edit can loosen; a field that does not exist is not.

- Hidden and delivered. `InjectedToolArg` hides an argument from the model and never fills it. `ToolRuntime` is hidden and filled. The first version used the former, and every tool call ran for an empty tenant.

- Failures are data. An exception ends the turn with nothing to say. A result with `error` set lets the model tell the person that retrieval is down, and the smoke test checks that no answer carries those words.

- A switch, not a fork. The brain is an allow-listed name on the request. Each framework is imported only when its brain is first used, so an image without one reports that brain as 501 rather than failing to start.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- An agent's retrieval pays for an answer it throws away. rag-api has one retrieval-only route, `/v1/passages`: the same retrieval with each passage's full text and no model call, which `retrieve(passages=True)` asks for. The chat brains do not use it yet. Their adapter calls `/v1/query`, which always generates, keeps the citations and drops rag-api's answer. Lesson 10.4's desks are its first callers.

- The month's totals leave the agent's own calls out. The chat service's row prices each turn, but the warehouse's `tenant_daily` view and `make usage` read rag-api's rows only.

- A check the kit names but does not ship. `documind_tools.py` tells you to run `tools/check_one_retrieval.py`. It lives in the course's own repository, not in the kit you cloned.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane.

The chat service runs in your region, from the kit's current script, with IAP on and its checkpointer migrated. The UI's account and the outsider may invoke it, and so may the Desk's six accounts once Terraform has created them. You may mint tokens as the UI's account and the outsider. The usage rows of five retrievals and four chat turns, and one conversation of two turns in the checkpointer, session `lesson101-langchain`. The direct brain keeps no conversation. No roster, policy or setting changed. Lesson 5.2 exposes the same tools to any MCP client, and lesson 5.4 opens the LangGraph brain: the hand-built graph, its refuse node, and the checkpointer that keeps a conversation.

Netsetos GenAI on GCP · Module 5 MCP and agents · Lesson 5.1 Understand tool contracts and the direct agent loop · v5.0

Next: Lesson 5.2 Expose, discover and invoke MCP tools.
