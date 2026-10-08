# Lesson 5.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_5.2_MCP_Tools_WIX.html`, reviewed at blob `3d3bcb639cec27a1d6e8a8182559d7ce705e358a`. Learners read that page on the course site; this guide keeps its prose.

The UI is how a person reaches your lane. MCP is how an agent does: Claude Desktop, Cursor, another team's ADK app, any agent you did not build. The kit's MCP server exposes four of the lane's own operations as tools. A client discovers them with one JSON-RPC method, `tools/list`, and invokes one with another, `tools/call`. You import the server and read what it declares. You start it on your machine with your lane behind it, send `tools/list` over plain HTTP, and call `retrieve` from fastmcp's client, the same client the smoke test and ADK use. Three calls that fail show where the server checks what.

- Expose, discover, invoke

- The words: MCP, server, client, tool, schema, tools/list, tools/call, tool error, transport

- Before you run anything: set up the shell

- Expose: what the server declares

- Start the server on your machine

- Discover: tools/list on the wire

- Invoke: retrieve from a local client

- Why the server is built this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what a server exposes, what a client discovers and what an invocation carries. You will also learn where the kit's server checks the arguments, the caller and the tenant. Then you will prove it: `tools/list` names four, and `retrieve` answers a local client with your lane's own citations.

### Expose, discover, invoke

Three verbs, and the checks between them.

Expose. An MCP server offers tools: named operations, each with a description and an input schema. FastMCP builds all three from an ordinary Python function. The name is the function's own, or the one given. The description is the docstring's first line. The schema comes from the signature, with each argument's line taken from the docstring's Args. The kit's server, `services/mcp/server.py`, exposes four tools: `retrieve`, `list_documents`, `corpus_stats` and `calculate_processing_cost`. Each is one of the lane's own operations. `retrieve` calls the one `retrieve()` the chat brains call, and the server keeps no index of its own.

Discover. A client asks `tools/list` and receives those declarations. A model reads them the way it read the kit's tool definitions in lesson 5.7: the description says when to use a tool, and the schema says what to send. The protocol is JSON-RPC 2.0 over HTTP. The kit's server is stateless, so a single POST to `/mcp` is enough, and the server answers as a server-sent event.

Invoke. `tools/call` names a tool and its arguments. The server runs it and returns the result as data, or a tool error with a message the caller can act on. The kit's server checks three things, in order. First the arguments. Then who is calling, from a bearer token minted for the server's own address. Then which tenant, from the roster. The `tenant` argument only chooses among rosters the caller is already on. The cost tool asks none of this, because it touches no tenant's data.

Where the checks are not. Listing needs no identity. Anyone who can reach the server can read its four declarations. On Cloud Run, IAM decides who can reach it, and that is lesson 5.3.

A restaurant's menu card. The card is `tools/list`: each dish's name, a line on what it is, and what you may choose, such as spice, portion, rice or roti. Anyone who sits down may read it. The order is `tools/call`: a dish and your choices, written on the waiter's pad. The kitchen checks the order first ("no memo on this menu"), then whose table it is, then whether that table's account is open. A refused order comes back as a note from the kitchen, not as silence. The price list on the back can be read and totted up by anyone, because it names no customer.

#### Compose a tools/call

Choose a tool, its arguments and who is calling. The panel shows the JSON-RPC request a client sends, and what the kit's server answers.

Every answer was returned by the kit's own `server.py`, run on localhost at build time with the token check, the roster, rag-api and Firestore stood in. The stand-ins hold each document under the class lesson 10.4's relabel gave it. So `statute` keeps the Act's passages, and `form`, a listed type that is no class, empties the pool.

It shows the server's checks and messages, not your lane's documents. Your corpus, your rosters and your answers will differ.

### The words: MCP, server, client, tool, schema, tools/list, tools/call, tool error, transport

Ten rows, each with the value it takes on your lane.

One distinction to hold: discovery tells a model what it may ask for, and invocation is where the server decides whether to answer.

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

The shell, in the kit's folder, with `PROJECT`, `API` and `tok`. You need fastmcp 3.4.7 in the operator venv, and the first cell installs it. Step 4 starts the kit's server on port 8121 of your machine, as a background process that uses your credentials. It reads the roster from Firestore and asks rag-api as `documind-ui-sa`. Step 6 stops it. Nothing on your lane changes.

### Expose: what the server declares

The kit's server imported, not run, and its tools listed in memory.

#### Definition

The cell imports the kit's `server.py` without running it, and lists its tools through fastmcp's in-memory client. That client talks to the server object directly, with no HTTP and no identity, and listing needs neither. It prints what an MCP client learns first: the server's name, the protocol version both sides agreed, and the instructions the server gives a model. Then it prints each tool with its arguments, their types, defaults and descriptions.

#### The code

#### Do it: fastmcp

#### Do it: what the server declares

Four tools, each built from a function. `retrieve`'s first docstring line became its description, and its Args lines became the four argument descriptions. Its signature made `query` required, and gave `doc_type`, `top_k` and `tenant` their defaults. `tenant` is "string or null" because the signature says `str | None`. The instructions are for the model: use `retrieve` for any question about the documents, and never state a figure that no citation carries. Nothing ran on your lane; this is the server describing itself.

### Start the server on your machine

The same code as the deployed `documind-mcp`, at another address, with your lane behind it.

#### Definition

The cell starts the kit's server with uvicorn on port 8121, in the background, with its log in `/tmp/mcp121.log`. `SELF_URL` is the audience every bearer token must carry, so it is the server's own address. `RAG_API_URL` and `DOCUMIND_IMPERSONATE_SA` point the one `retrieve()` at your lane's rag-api, as `documind-ui-sa`. `GOOGLE_CLOUD_PROJECT` lets the server read the roster from Firestore. Then the cell mints two tokens for that address as `documind-ui-sa`, one with its email and one without, and waits for `/health`.

#### The code

#### Do it

The server is running on your machine with the gcp profile, so it verifies every call's token and reads your lane's roster. It is the same code the deployed `documind-mcp` runs, at a different address. The token you minted names `localhost:8121` as its audience, and a token for any other address would fail the check.

### Discover: tools/list on the wire

One JSON-RPC request as a plain HTTP POST, and the reply it gets.

#### Definition

The cell sends one JSON-RPC request, `tools/list`, as a plain HTTP POST with your token. The server needs no `initialize` first, because it keeps no session. It answers with a server-sent event. The cell prints the status, the content type and the first line. Then it prints each tool with the arguments it needs and the ones it may take.

#### Do it

HTTP 200, `text/event-stream`, and a first line of `event: message`: the reply is one event, whose data line is the JSON-RPC response. `tools/list` names four, and that is the first half of the proof. Any client that can reach the server gets the same list, Claude Desktop or an ADK agent alike, because it is the protocol's answer, not fastmcp's.

### Invoke: retrieve from a local client

One answered call, three refused ones, and the line the server kept.

#### Definition

The cell uses fastmcp's client with the transport `make smoke-mcp` uses, pointed at your machine. It calls `retrieve` with the gratuity question for acme, and prints the answer and its first three sources. Then come three calls that fail in three different places: a `doc_type` the server does not know, a tenant `documind-ui-sa` is not on, and a token that carries no email. The last cell stops the server and prints the line it logged for each answered call.

#### Do it

#### Do it: stop the server

`retrieve` answered from your lane, for acme: rag-api's grounded answer and its citations, through the one `retrieve()`. That is the second half of the proof. The three failures came back as tool errors, each from a different check: the arguments, then the roster, then the token. The token without an email could still list the tools; only the call asked who it was.

The log has one `mcp_call` line, for the answered call. It records the tool, the tenant, the caller, whether the question was answerable, and how many citations came back. The refused calls left no such line.

### Why the server is built this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Agents you did not build. The UI is for people. MCP is the lane's surface for any agent that speaks the protocol, so a new client needs no code in the kit.

- No second index. The server owns no index, and `retrieve()` is the one implementation. An MCP answer and a chat answer can never disagree about what the corpus holds.

- The tenant from the roster. A model fills in tool arguments, but not the roster. A named tenant is honoured only when the roster already lists the caller on it.

- Stateless. Every request carries its own identity, so an instance keeps no session memory, and Cloud Run can scale it freely.

- Errors a caller can act on. A tool error says what to change: the argument, the tenant or the token.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- Anyone who can reach the server can list its tools. `tools/list` needs no identity, because the check is inside each tool. On Cloud Run, IAM decides who can reach the server, and that is lesson 5.3.

- The server has no sign-in of its own. A caller must bring a Google ID token minted for the server's address. An unauthenticated call is a tool error, not an HTTP 401, so an MCP client that signs in through the protocol's own flow never gets the prompt to.

- A refused call leaves no audit line. The `mcp_call` line is written only after the checks pass. A call refused for its tenant, its token or its arguments leaves no row naming the caller and the tenant.

- `retrieve` offers filters the corpus cannot honour. Its `doc_type` list names eight types, and six of them are classes from lesson 10.4's registry, which your registered documents now carry. `form` and `research_paper` are not classes, so no row carries them, and either one empties the pool. `transcript` is a class, but the list leaves it out, so the server refuses it. A class filter also skips every text upload still stamped `unknown`: an object the manifest does not name, and a new version nobody has re-pinned. The chat service's `retrieve`, which lesson 5.5 tested, still offers `form` and `research_paper` too.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

Nothing on your lane. Your machine ran the kit's server for a few minutes and stopped it, and `/tmp/mcp121.log` holds its log. rag-api's log has one more row, with the brain `mcp`. Lesson 5.3 deploys the same server behind Cloud Run and checks who may reach it.

Netsetos GenAI on GCP · Module 5 MCP and agents · Lesson 5.2 Expose, discover and invoke MCP tools · v5.0

Next: Lesson 5.3 Deploy MCP and verify authorized access.
