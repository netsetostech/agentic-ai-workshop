# Lesson 10.6: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_10.6_A2A_Peer_WIX.html`, reviewed at blob `6f13d04435a34279510124166f441b32d6337022`. Learners read that page on the course site; this guide keeps its prose.

`documind-agent` is the agent another team would build. It holds no kit code: it knows DocuMind by one address, `documind-mcp`. Other agents can reach it over A2A, through an agent card that describes it and `message/send`, which gives it a task. One task crosses three protocols: A2A from the caller to the peer, MCP from the peer to the server, and HTTPS from the server to rag-api. Each hop carries a different identity, and none carries the caller's. You read the peer's permissions from the kit's files and ask for its card with and without a token. Then you run the module's A2A gate, and trace one task through its history and the two logs.

- One task, three protocols, three identities

- The words: A2A, agent card, skill, message/send, task, history, peer, McpToolset

- Before you run anything: set up the shell

- The peer's permissions, as the kit writes them

- The card: refused without a token, read with one

- The gate: make smoke-agent

- One task, traced

- Why the peer is built this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what the peer may do and on whose behalf, which identity each hop carries, and why a task's caller disappears after the first door. Then you will prove it: the card refused without a token, and `message/send` completing as a task. You will also see the zeta request refused by the roster and relayed, and the outsider stopped at the peer's door.

### One task, three protocols, three identities

A peer, not a brain; and its permissions are its account's.

A peer, not a brain. The four chat brains live inside the kit and call `retrieve()` directly. The peer lives outside it. It is an ADK `LlmAgent` whose only tools are the lane's four, which `McpToolset` discovers from `documind-mcp`. Its image copies only its own folder, and `agent.py` imports nothing from the kit. ADK's `to_a2a` serves it over A2A. The agent card at `/.well-known/agent-card.json` says who it is and where to send tasks, and JSON-RPC at `/` takes `message/send`.

Three hops, three identities. A caller sends a task with an ID token minted for the peer's address. Cloud Run admits it only if the caller is one of the two invokers, `documind-ui-sa` or `documind-chat-sa`. A2A carries no identity of its own, so the peer never learns who asked. For each tool call, the peer mints a fresh token as its own account, `documind-agent-sa`, for `documind-mcp`'s address. The server verifies that token, finds `documind-agent-sa` on acme's roster alone, and calls rag-api as `documind-mcp-sa`.

The peer's permissions are its account's. `documind-agent-sa` may call `documind-mcp` and nothing else in the lane. It may call Gemini, and it is on one roster. So whoever the caller is, a task reads acme's documents and only acme's. A task naming zeta is refused by the server's roster check, and the peer relays the refusal as its answer.

The task carries its trail back. The reply to `message/send` is a task: its state, artifacts with the answer, and a history holding every message. The history includes each tool call the peer made, and what came back.

A travel agency with a corporate account. The agency has one login to an airline's corporate portal, set up for one company, and its door admits only its two regular clients. Whichever client walks in, the agent books through that one login, so every booking is that company's, and the portal knows only the agency. A request to book for another company is refused by the portal, and the agent passes the refusal on. The receipt the agency hands you lists every search it ran for you, and what the portal said.

#### Follow one task

Choose who sends the task and what it asks. The panel follows it through each service, with the identity each one saw.

Each hop is what the kit's peer and server did at build time. Gemini was stood in by a model that calls the tool a request names. The answers for ui-sa and chat-sa were identical, because the peer cannot tell them apart.

On your lane, Gemini chooses the tool and writes the answer. The doors and the identities are the kit's, and those do not change.

### The words: A2A, agent card, skill, message/send, task, history, peer, McpToolset

Ten rows, each with the value it takes on your lane.

One distinction to hold. The card is how an agent finds the peer, and the token is how Cloud Run lets it in. Neither tells the lane who asked.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER` and `tok`. The peer and the MCP server must be deployed: `make up` deploys both, and lesson 5.3 redeployed the server. Steps 5 and 6 send tasks, each a few model calls and at most one retrieval. Nothing changes on your lane.

### The peer's permissions, as the kit writes them

Its account, its callers, its one URL, its roster, its imports and its image.

#### Definition

The cell reads the peer's deploy block in `commands/lesson-8.4.sh`: the account it runs as, its model, the one URL it knows, and the two accounts bound to call it. It checks that `lesson-7.2.sh` binds `documind-agent-sa` on `documind-mcp`. It reads the peer's project roles from `terraform/sa.tf` and its rosters from `roster_plan`. Last, it lists what `agent.py` imports and what the image copies.

#### The code

#### Do it

The peer's whole reach fits in a few lines. It runs as `documind-agent-sa`, knows one URL, and may be called by two accounts. It may call `documind-mcp`, use Gemini and write logs, and it is on acme's roster. `agent.py` imports ADK, Starlette, uvicorn and the standard library, and nothing from `shared` or `services`. The image copies its own folder and nothing else. A peer that imported the kit would be a fifth brain.

### The card: refused without a token, read with one

What another agent fetches first, and who Cloud Run lets fetch it.

#### Definition

The card is the first thing another agent fetches. The cell asks for it twice: once without a token, as anyone on the internet would, and once with a token minted for the peer's address as `documind-ui-sa`. It prints the status of the first. For the second it prints the name, address, protocol, modes and skills. It also notes the time, for step 6's logs.

#### Do it

403 without a token: the card is behind Cloud Run's IAM, and that is the first half of the proof. With a token, the card names `documind_peer`, the address to send tasks to, and one JSON-RPC interface on A2A 1.0.

Its skills say `model` and nothing else, though the peer has four tools. ADK built the card when the peer started, by listing its tools with no request in hand. `McpToolset` mints the peer's token only for a request, so that listing reached `documind-mcp` without one, and Cloud Run refused it. The tools work in every task; they are only missing from the card.

### The gate: make smoke-agent

Five checks, in plain urllib and JSON-RPC, against your peer.

#### Definition

`make smoke-agent` is the module's A2A gate. It uses plain urllib and JSON-RPC, with no A2A library, and runs five checks:

- It asks for the card without a token.

- It reads the card with a token.

- It sends the gratuity question with `message/send`, and checks the task completed with five years in the answer.

- It sends the same question naming zeta, and checks the roster's refusal came back.

- It sends a task as the outsider, which may call `documind-mcp` but not the peer, and expects 403.

#### Do it

Five passes. The third is the second half of the proof: `message/send` completed, and the answer came from acme's corpus through `documind-mcp`. The fourth shows the peer's scope. The zeta request reached the server as `documind-agent-sa` and was refused by the roster, and the peer relayed that refusal as its answer. The fifth shows the peer's only door. The outsider holds a valid token and was stopped by Cloud Run, because the peer has no roster of its own to refuse it with.

### One task, traced

The task's own record, then what the lane recorded.

#### Definition

The first cell sends one task as `documind-ui-sa`, and prints the task's state and each message of its history. The second reads two logs since step 4: the MCP server's line for each tool call, and rag-api's row for each retrieval.

#### Do it: the task

#### Do it: what the lane saw

The history is the peer's own record of the task: your question, the model's call to `retrieve`, what the server sent back, and the answer. It travels back to whoever sent the task.

The logs show the lane's view. `documind-mcp` saw `documind-agent-sa` asking for acme, and rag-api saw `documind-mcp-sa`. `documind-ui-sa`, the account that sent the task, appears in neither. After Cloud Run's door, nothing in the lane records who asked the peer.

### Why the peer is built this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- A peer knows one URL. The peer reads `MCP_URL` and nothing else, and `check_authz.py` fails if it learns a second.

- IAM is the peer's only door. It has no verifier and no roster, so Cloud Run's invokers must be exactly the callers the caller graph allows: ui-sa and chat-sa, never the outsider.

- One roster. A peer scoped to one tenant needs no tenant argument, and a request naming another tenant is refused by the server, not by the peer's code.

- A token per tool call. The header provider runs on every call, so an ID token, which lasts an hour, is never used past its life.

- No kit inside. The image copies only `services/agent`, so the peer depends on the lane's public surface, as another team's agent would.

#### What it costs

Each point is checked in the kit's code, or in the pinned ADK the image installs, and the build asserts it, so this box changes when they do.

- The card lists no tools. ADK builds the card once, at start-up, by listing the tools without a request. `McpToolset` mints the peer's token only for a request, so Cloud Run refuses the tokenless listing, and the card says `model`. `make smoke-agent` checks the card's address, not its skills.

- Nothing records who asked the peer. `agent.py` logs its start-up and nothing else. A2A carries no identity, and the lane sees `documind-agent-sa`. Every admitted caller reads acme's documents, and no log says which one did.

- The gate it names does not exist. `agent.py` says `tools/check_auth_wiring.py` fails the build on a kit import, and there is no such file. The Dockerfile's COPY is what keeps the kit out, and a kit import would surface only as a crash at start-up.

- The history carries raw results to the caller. Every tool call and its full result go back in the task, with the service account's email in the zeta refusal's text.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

Nothing is configured. The peer answered your tasks, and `documind-mcp` and rag-api logged them as `documind-agent-sa` and `documind-mcp-sa`. Lesson 10.7 hands one question from the ADK brain to this peer as a bounded tool, and stops loops and deadlocks between agents.

Netsetos GenAI on GCP · Module 10 Agent patterns · Lesson 10.6 Trace the implemented A2A peer and its permissions · v5.0

Next: Lesson 10.7 Hand one question to the A2A peer, and stop loops and deadlocks.
