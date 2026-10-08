# Lesson 5.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_5.4_LangGraph_WIX.html`, reviewed at blob `0f0a7699c5f7e6eb5b1785fcdc570c29b0198022`. Learners read that page on the course site; this guide keeps its prose.

The LangChain brain hands its loop to a framework. The LangGraph brain draws it: an agent node that calls the model, a route that reads what the model asked for, a tools node, a refuse node, and a checkpointer that keeps each conversation. You list the kit's own graph and force the refuse node with a scripted model. The model on your lane is never offered a blocked tool, so it cannot reach that node any other way. Then you use the graph on your lane: a thread that remembers, a new thread that does not, and a request to delete that meets no tool at all.

- A loop you can draw, and a guard that is a node

- The words: StateGraph, node, route, ToolNode, refuse, error result, checkpointer, thread

- Before you run anything: set up the shell

- The graph, in a venv of its own

- The refuse node, forced to fire

- The graph on your lane: one thread, a new thread, and a request to delete

- What the checkpointer keeps

- Why the graph is built this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn how the LangGraph brain wires a tool-using loop by hand, why its guard is a node in the graph rather than a filter around it, and why a turn that asks for one blocked tool is refused whole. You will also learn what the checkpointer stores and what it deliberately leaves out. Then you will prove it: the refuse node firing on a blocked tool with an answer that says so, and a thread on your lane remembering its first turn.

### A loop you can draw, and a guard that is a node

Nodes, one conditional edge, and a saver compiled in.

A loop you can draw. The graph's state is the conversation, a list of messages. The `agent` node calls the model with the system prompt in front of the messages and appends its reply. A function called `route` reads that reply. If the model asked for no tool, the turn ends. If it asked only for allowed tools, the `tools` node runs them and appends their results. If it asked for any blocked tool, the `refuse` node answers instead. Both `tools` and `refuse` lead back to `agent`, which reads the new messages and decides again. Nothing is hidden: the whole harness is these nodes and edges, compiled.

The guard is a node, and it refuses the whole turn. `route` sends a turn to `refuse` if any requested name is in `BLOCKED`: `delete_document`, `send_email`, `modify_access`. Every call in that turn then gets an error result, including an allowed one asked for alongside. A model therefore cannot slip a deletion in beside a search and have the search run. Each error reads "requires manual approval", and the system prompt tells the model to say so plainly and never to claim the action was taken.

You have to force it. The model is bound to the two real tools only, and Gemini's function calling returns calls to the functions it was given, nothing else. On your lane the model has no way to ask for `delete_document`. The refuse node is defence in depth: for the day a blocked tool is registered by mistake, or another framework lets a name through. So the proof uses a scripted model: the kit's own graph, with a model that replies exactly as scripted, including a request for a blocked tool.

The checkpointer keeps the conversation, not the instructions. The graph is compiled with a checkpointer, which saves the thread's messages after each step. The next turn on the same thread starts from them. The thread id is `tenant:user:session`, built by the server from the verified identity. The system prompt is added on every call and never saved, so a changed prompt reaches old conversations too. On your lane the saver is Postgres on Cloud SQL. Its tables are created once by a job, not by the service at startup.

A file moving through a government office. Each officer writes a noting and passes the file on. When a noting asks only for records from the registry, the file goes to the registry and comes back with the papers attached. When any line asks for a record to be destroyed, the whole file goes to the competent authority. It comes back with every request on that noting marked "needs approval", the harmless ones included. Nothing leaves the file: the next officer reads every noting before writing the next one. The office rules are pinned on the wall, not copied into each file.

#### Step through the graph

Choose a turn and step it through the kit's graph: which node runs, what the route decides, and the two lists that come back.

Every turn here was run at build time through the kit's own `LangGraphBrain`, with a scripted model and LangGraph. The panel had to produce the same node path, the same `tool_calls` and `refusals`, and the same error texts. Step 4's cell runs three of them on your machine.

The model's replies are scripted; on your lane, the model decides what to ask for. The panel does not show the checkpointer, and the tools node's results are stood in. Step 5 is the real thing.

### The words: StateGraph, node, route, ToolNode, refuse, error result, checkpointer, thread

Eleven rows, each with the value it takes on your lane.

One distinction to hold: `route` decides where a turn goes, and `refuse` decides what the model hears about it. The first keeps a blocked call from running. The second is the only explanation the model gets.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER` and `tok`. The chat service must be running in your region, which lesson 5.1's step 3 deployed. Step 3 creates `~/graph-venv` in your home folder, and nothing on the lane changes for it. Step 5 asks the LangGraph brain four questions, and the checkpointer keeps two threads.

### The graph, in a venv of its own

The chat image's LangChain pins in a separate venv, then the kit's graph built and listed.

#### Definition

The operator shell's venv holds rag-api's packages and not LangChain, and the two sets of pins should not share an environment. So the lesson makes a small venv beside it. It holds the chat image's own versions: LangChain 1.4.0 and LangChain Core 1.6.2, which bring LangGraph with them, plus `requests` and `google-auth` for the tool layer. The graph cell builds the kit's `LangGraphBrain` with a scripted model and an in-memory saver, and prints its nodes and edges. Nothing calls a model or the network.

#### The code

#### Do it: the venv

#### Do it: the graph

Five nodes, counting LangGraph's own start and end, and six edges. Three of the edges leave `agent`, and `route` picks one of them each time the model has replied. `tools` and `refuse` each have one edge, back to `agent`. So a turn can run the tools any number of times, but it can never end straight from a tool result: the model always reads it first.

### The refuse node, forced to fire

Three scripted turns through the kit's own graph: a plain one, a blocked one, and a mixed one.

#### Definition

The scripted model returns its prepared replies in order: first a request for tools, then an answer. The cell streams each turn through the graph and prints the nodes it visited, the two lists from `_summary()`, every error result, and the final answer. `retrieve()` is stood in with a fixed result, so the plain turn needs no network. The blocked turn asks for `delete_document`. The mixed turn asks for `retrieve` and `delete_document` in the same reply. The `agent` node's first lines are the turn's limits, which lesson 5.7 reads; the scripted turns stay far inside them.

#### The code

#### Do it

The plain turn went `agent → tools → agent`. The blocked turn went `agent → refuse → agent`. The deletion never reached a tool, the model read an error result saying it needs manual approval, and its answer says nothing was removed. That is this lesson's proof: the refuse node fires on a blocked tool, and the answer says so. The mixed turn shows "refused whole". The search was refused too, and never ran. But read its error result: the model was told that `retrieve` requires manual approval, which is not true, and a real model may repeat it.

### The graph on your lane: one thread, a new thread, and a request to delete

Four turns to the LangGraph brain, through the chat service.

#### Definition

With `brain` set to `langgraph`, `/v1/chat` builds the thread id from the roster's tenant, your caller's email and the session you send. It then invokes the graph once on that thread, with the tenant in the runtime context. The graph loads the thread's saved messages, runs the turn, saves the new ones, and `_summary()` returns the four keys for this turn alone: `_turn()` gave the question an id, and the turn is that message and what follows it. If that message is missing from the thread, `_summary()` raises a `ValueError` rather than count the whole thread again, so anything that trims a thread must keep each turn's question. The cell asks the first question in session `lesson102`, then a follow-up that only makes sense after it: "how is it paid". It asks the follow-up again in a new session, `lesson102-new`. Finally it asks to delete a document, in the first session.

#### The code

#### Do it

The follow-up in the same session knew that "it" was gratuity. The graph started the turn from the saved thread, so the model read the first question and answer before the second question. The same words in a new session had no thread behind them, and the model could only ask what "it" meant. The request to delete called no tool: the model has no delete tool to call, so the refuse node was never involved, and `refusals` is empty. The model refused in words, as the system prompt asks. Each turn's `tool_calls` names its own calls only: the second turn ran on a thread that already held a retrieval, and lists one, and the last lists none. This is the other half of step 4. On your lane the refuse node is a net under a model that has not been offered the rope.

### What the checkpointer keeps

The saver behind step 5's threads, and what it stores.

On your lane the saver is `PostgresSaver` over a small connection pool to the Cloud SQL instance, opened once when the process starts and kept for its life. Returning from inside the saver's own connection helper would close it after the first request. The tables are created by a Cloud Run job, `documind-checkpoint-setup`, which lesson 5.1's deploy ran. The service never calls `setup()` itself, because its migrations take exclusive locks, and a scale-out of instances racing to run them fails at random. After every step, the saver stores the whole state: your question, the model's tool requests, every tool result with its quotes, and the answer. It does not store the system prompt, which the `agent` node adds on each call. The build checked this with the same graph: two turns on one thread leave four saved messages and no system message.

The laptop lane saves to a SQLite file instead, and `CHECKPOINT_DSN=memory` gives an in-memory saver that forgets on restart. The service logs a warning for it, because it is for tests only. The thread id puts the tenant first and refuses a `:` in any part, so no session name can reach into another tenant's conversations.

### Why the graph is built this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- The harness is edges and nodes. Nothing happens that is not drawn: no hidden retries, no middleware. Adding a step, such as a check before an answer is returned, is one more node and one more edge.

- A guard in the graph, not around it. The LangChain brain refuses inside a middleware that wraps each tool call. The LangGraph brain refuses with a node, so the refusal is part of the state, visible in the thread and in `refusals`, and the model reads it like any other result.

- Refused whole. A turn is the unit the model decided as a whole, so it is refused as a whole. Running the allowed calls and refusing the rest would let a model learn that a blocked call can travel with an allowed one.

- The prompt is not state. The system prompt is added per call and never saved, so fixing a prompt fixes every conversation, including old ones.

- One saver, one thread id. The LangChain and LangGraph brains are built with the process's one checkpointer and the same `tenant:user:session` ids. The ADK brain keeps its own sessions, which lesson 5.7 compares.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The refuse node cannot fire on the lane. No blocked name is ever bound to the model. Its proof is offline: step 4's cell, and the kit's own `commands/tests/test_chat_brains.py`, which runs this graph with a scripted model in the chat image's pins on every push.

- A refused mixed turn misinforms the model. Every call gets "requires manual approval", so an allowed `retrieve` asked for beside a blocked tool is reported to the model as needing approval.

- The graph's limits are written by hand. No middleware runs in a hand-built graph, so the `agent` node checks the turn's `Meter` itself before each model call, and `ToolNode` times each tool call through `limits.timed_tool_call`. A node added later that calls the model gets no limit unless it does the same. Lessons 5.5 and 5.7 show the limits.

- Nothing deletes a thread. No code in the kit removes checkpoints. Every conversation, with its questions, quotes and answers, stays in Cloud SQL until someone deletes it by hand.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

Two threads in the checkpointer: `lesson102` with three turns, and `lesson102-new` with one. There are two rag-api usage rows, from the two retrievals, and four chat rows. Your home folder has `~/graph-venv`; delete it whenever you like. No roster, role, policy or setting changed. Lesson 5.5 breaks the tools on purpose: a bad argument, a refused tenant, and a tool that takes too long.

Netsetos GenAI on GCP · Module 5 MCP and agents · Lesson 5.4 Implement the main LangGraph workflow · v5.0

Next: Lesson 5.5 Diagnose tool arguments, access failures and timeouts.
