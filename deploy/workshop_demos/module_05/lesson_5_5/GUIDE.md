# Lesson 5.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_5.5_Tool_Failures_WIX.html`, reviewed at blob `780a103bb4f0ddb0633a2c104547c46fa01b58c3`. Learners read that page on the course site; this guide keeps its prose.

A tool call can fail in more places than it can succeed. Some failures stop a request at the door, and some reach the model as an error. Some reach it as ordinary data that happens to say something went wrong. And some are not failures of a tool at all: a turn that never ends, because the model keeps asking. You force five failures through the kit's own LangChain brain: a blocked name, a wrong argument, a tool that does not exist, a retrieval that times out, and a retrieval cut at its budget. You stop a model that never stops asking, and see the next turn answer. Then you meet three identities at the chat service's door, and a filter argument the corpus cannot honour. For each one you find where it surfaced and who was told.

- Every failure has a place, and a reader

- The words: refusal, error result, payload, budget, Meter, stopped_by, door, empty pool

- Before you run anything: set up the shell

- Five failures through the kit's LangChain brain

- A turn that will not stop: the call cap, the rupees and the deadline

- Access failures at the chat service's door

- An argument the corpus cannot honour

- Reading a failure on the lane

- Why failures are handled this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn the three places a failure can surface (the HTTP status, the tool result, the log) and which failures land in `refusals`. You will also learn why a timed-out retrieval does not land there, and how a turn is held to 12 model calls, Rs 5 and 100 seconds. Then you will prove it: a non-empty `refusals`, a tool cut at its budget and listed in `limits.tool_timeouts` with `refusals []`, a capped turn on your lane that answers HTTP 200 with `stopped_by`, a 401 and a 403 from the door, and a filter that empties the pool.

### Every failure has a place, and a reader

Before a turn, inside a turn, and in a log line.

Before a turn, the caller is told. Cloud Run's IAM admits or refuses the token. The chat service then asks who the token names: a token that names nobody is a 401. It asks whether the roster lists them: an account on no roster is a 403. No brain runs and no model is called. The caller gets a status and a sentence, and the request log keeps the status. The tenant is decided here, from the roster, and it never becomes an argument a model could fill. So "search another tenant's documents" is not a failure the tool layer has to catch. It cannot be asked at all.

Inside a turn, the model is told, in two different ways. Some failures produce an error result: a tool message marked `error`, and `_summary()` puts its name in `refusals`. A blocked name is one, refused by the guard before the tool runs. An argument of the wrong type is another, rejected by LangChain's check. So is a tool the model named that does not exist, and so is a tier the cost tool does not know: the tool raises a `ToolException`, which LangChain also turns into an error result. Other failures produce an ordinary result that carries bad news. When rag-api does not answer within `RAG_TIMEOUT_S`, the one `retrieve()` returns `{"error": ...}` as data, and a filter that matches nothing returns an empty list. The model reads both, but `refusals` counts only the first kind.

A slow tool is cut, and the model is told as data. Every tool has a budget in `TIMEOUTS`: 95 seconds for `retrieve` on the lane, which is `RAG_TIMEOUT_S`'s 90 plus 5 for the token and the connection, and 10 for the cost tool. `limits.timed_tool_call` runs each call in a pool of threads and waits no longer than the smaller of that budget and the time the turn has left. A call past it is abandoned: the model reads a payload error that says so, `refusals` stays empty, and the tool's name goes into `limits.tool_timeouts`. A call still waiting for a thread is cancelled and never runs. One already running finishes, but it adds nothing to the turn's citations. All three agent brains time their tools this way.

A turn has limits of its own. A tool failure ends one call. A model that keeps asking for tools would keep a turn going until something outside it gave up. So every turn carries a `Meter`, made by the chat service for that turn: at most 12 model calls, Rs 5 for its own model calls and its searches, and 100 seconds. It is checked before each model call. A tripped limit ends the turn with HTTP 200, a fixed sentence as the answer, and `limits.stopped_by` naming the limit. The thread stays whole, so the next turn on it answers. The rupee cap is named here; lesson 11.6 takes it up beside the month's.

A bank branch clearing cheques. The guard stops a stranger at the door, and the teller refuses a cheque on an account that is not yours. Both are told to your face, before anything is processed. A cheque made out for a prohibited purpose goes to the manager and comes back marked "needs approval". One whose amount in words does not match the figures comes back marked "returned". A cheque that cannot be cleared in time comes back too: "unpaid, present again", which is an answer, not a rejection. A cheque the clearing house has not answered by the counter's cut-off is set aside, and you are told so, while the queue moves. And a customer who keeps presenting cheques is served a fixed number at one visit, then told the counter has closed for them and to come back, which they can.

#### Where a failure surfaces

Choose a failure to see which layer catches it, what the caller and the model are told, what the four keys say, what the logs keep, and whether the turn waits.

The texts are the kit's own. The five tool failures come from step 3's cell, run at build time on the kit's `brains.py` and `limits.py`; the two stops are the kit's `limits.py` and its tests. The door's texts are read from `agent.py` and `shared/iap.py`, and the empty pool from `main.py`.

It shows the LangChain brain, the chat service's default. The LangGraph brain refuses a blocked name with its refuse node (lesson 5.4), times its tools through the same `timed_tool_call`, and checks the `Meter` in its own `agent` node. The ADK brain has callbacks of its own for both, in lesson 5.7.

### The words: refusal, error result, payload, budget, Meter, stopped_by, door, empty pool

Thirteen rows, each with the value it takes on your lane.

One distinction to hold: an error result says the call did not happen, and a payload error says it happened and could not help. Only the first lands in `refusals`. A cut call is the second kind, and a stopped turn is neither: it is an answer that says it is incomplete.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `tok`. You need `~/graph-venv` from lesson 5.4, and the step 3 cell makes it if it is missing. The chat service must be running in your region, from lesson 5.1's step 3, built from this lesson's kit: an older image has no `limits` on its `/health`, and `make limits` says so. Step 4's drill changes one setting on the chat service for a minute or two and puts it back. Step 5 sends three requests to the chat service, and step 6 makes two retrievals.

### Five failures through the kit's LangChain brain

A scripted model asks for five things that go wrong. The kit's guard, LangChain, the timer and the tool layer answer.

#### Definition

The cell builds the kit's `LangChainBrain`, the chat service's default, with a scripted model and an in-memory saver. It starts a rag-api on your machine that takes two seconds to answer, points the one `retrieve()` at it with a client timeout of half a second, and stands in its ID token. It captures the log lines of the guard, the timer, the adapter and `retrieve()`. Then it runs five turns, each with a `Meter` of its own. Each asks for one tool call and prints how long the turn took, `refusals`, the Meter's `tool_timeouts`, and the result the model read, with its status. The five are:

- blocked: `delete_document`, a blocked name;

- bad args: the cost tool with `total_pages="many"`;

- no such: `summon_rain`, a tool that does not exist;

- timed out: `retrieve` against the slow rag-api, whose client gives up first;

- cut: `retrieve` again, with a client that would wait five seconds and a budget of one.

#### The code

#### Do it: the venv

#### Do it: five failures

Three turns ended with a non-empty `refusals`: the blocked name, the bad argument and the unknown tool. That is the first proof. Each was an error result, and the model read why. The three look alike in `refusals`. Only the result's text tells a policy refusal from a mistake. The timed-out retrieval took half a second, the client timeout, and was not left hanging. The model read `document search is unavailable` as ordinary data, so `refusals` stayed empty. The cut retrieval took one second, its budget, though its client would have waited five. The model read that `retrieve` did not answer within 1s and was abandoned, `refusals` stayed empty, and `tool_timeouts` named it. That is the second: a timed-out tool reported, and counted. The log shows each layer saying so in its own words: the one `retrieve()`, the adapter and the timer. The timer's line for the timed-out run names a budget of 25 seconds: `RAG_TIMEOUT_S` is not set in your shell, so it is its default, 20, plus 5, computed when `tools.py` was imported. Setting `dt.RAG_TIMEOUT_S` to 0.5 afterwards does not move it; the cell sets `tools.TIMEOUTS["retrieve"]` itself before the cut run, which is why the next line reads `budget 1s`. Read the last two lines: the abandoned call ran on in its thread and finished at two seconds, after the turn had moved on. On the lane, rag-api answers that call and bills it on its own row, but the call writes nothing into the turn: its cost is not charged to the turn's `Meter`, and a citation it brings back is not numbered, so the answer never lists a source the model did not read.

### A turn that will not stop: the call cap, the rupees and the deadline

A looping model on your machine, every brain in the kit's tests, then your lane's limits and a capped turn on it.

#### Definition

The chat service makes a `Meter` for each turn and hands it to the brain in the runtime context. Before each model call the brain asks it `allow_model_call()`. The first call is always allowed. After that the Meter refuses a call once the turn has made 12 calls, once it has spent Rs 5, or once fewer than 5 of its 100 seconds are left. Each model call also gets a timeout of its own: the smaller of 30 seconds and the time left divided by its 2 attempts. A refused call is never made. The brain ends the turn with the stop sentence instead, and the Meter records the reason. In the LangChain brain that check is `TurnLimitsMiddleware`, which wraps the model call and nothing else, so a turn writes the same checkpoints it did before.

The first cell builds the LangChain brain on a model that asks for the cost tool on every call, with a cap of 3 so the run is short, then asks a second question on the same thread with a model that answers. `make limits-check`, which is `commands/limits-check.sh`, runs the kit's own test file, `commands/tests/test_chat_limits.py`, on all three agent brains: the cap, the rupees and the deadline, a slow search, a hung model, and the chat service's HTTP 200. `make limits` reads what your deployed chat publishes. `make limits-drill STOP=model_calls`, which is `commands/limits-drill.sh`, sets `CHAT_MAX_MODEL_CALLS=1` on the chat service, runs `make smoke-chat`'s test expecting every agent brain to stop, puts the setting back and runs the test again. `STOP=turn_budget` does the same with the rupee cap, in lesson 11.6.

#### The code

#### Do it: a model that never stops asking

#### Do it: every brain, offline

#### Do it: your lane's limits

#### Do it: a capped turn on your lane

The looping model made three calls and ran the cost tool three times. The Meter refused the fourth call, so it was never made, and the turn ended with the stop sentence and `stopped_by model_calls`. The thread holds ten messages, and every tool call in it has its result, so the second question was answered as if nothing had happened. `make limits-check` ran 36 tests, and they include the same stop through the LangGraph and ADK brains. `make limits` shows the numbers your chat runs under. The A2A peer, which lesson 10.6 traces, publishes no cap yet, so ADK's own default of 500 applies there. In the drill, every agent brain answered HTTP 200 with the stop sentence after one model call, and `direct`, which makes no model call of its own here, answered as usual. With the setting restored, the same test passed with no stop. That is the proof for the turn's limits: a turn on your lane stopped at its limit, and still answered.

### Access failures at the chat service's door

The outsider, a token that names nobody, and a roster member, each asking the same question.

#### Definition

IAM admits all three accounts to the chat service: `documind-ui-sa` and `documind-outsider-sa` both hold the invoker role on it. The service then asks `shared/iap.identity()` who is calling. A bearer token minted without `--include-email` names nobody, which is a 401. The outsider is somebody, and `tenant_for()` finds them on no roster, which is a 403. The member reaches the default brain and gets an answer. The first two never reach a brain, a tool or a model.

#### The code

#### Do it

Three statuses, three layers. The 403 came from the roster: the outsider's token was fine, and no tenant lists it. The 401 came from the identity check: the token was genuine, but carried no email to look up. The 200 came from a member, whose tenant the roster supplied. None of the requests could have named a tenant, because the chat request has no field for one. These two refusals cost nothing, because they are decided before a model is called.

### An argument the corpus cannot honour

One question with and without a `doc_type` filter, then what rag-api's rows say about it.

#### Definition

The chat service's `retrieve` tool tells the model it may filter by `doc_type`: policy, contract, invoice, form or research_paper. The worker stamps every text upload `unknown`, as lesson 2.1 found, so each of those values filters out every text document. The filter is a valid argument, so nothing refuses it. The pool simply comes back empty, and rag-api answers with its fixed empty-pool text, at no model cost. The cell asks about the April invoice with no filter, then with `doc_type` `invoice`, through the one `retrieve()`. It then reads rag-api's rows for both calls.

#### Do it

Without the filter, five citations and the invoice's total. With `doc_type` `invoice`, nothing: no citations, `answerable` false, and the empty-pool text, which reads exactly like a corpus that holds no invoice. Asked by a model, this turn ends with `tool_calls ['retrieve']` and `refusals []`. The only trace of the bad argument is rag-api's row: `pool 0`, beside a question the corpus can answer. The filter itself appears on no row and in no log.

### Reading a failure on the lane

Where each signal lives, in the order to look.

When a chat turn goes wrong in production, the evidence is spread across three services and several stores. Look in this order.

Three patterns cover most cases. `stopped_by` set means the turn hit a limit: the answer says it is incomplete, and asking again, or a narrower question, usually answers. `refusals` non-empty means the model asked for something it could not have: read the log line for the name. `refusals` empty with an answer that says it found nothing means either the corpus lacks it or the model narrowed the search. rag-api's row tells those apart: `pool 0` on a question you know the corpus answers points to an argument.

### Why failures are handled this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- 401 is not 403. A 401 means the service does not know who is asking; a 403 means it knows and will not serve them. The difference is what you need when reading logs at three in the morning, and the kit keeps it deliberately.

- Errors as data. An exception inside a tool would end the turn with nothing to say. A payload lets the model tell the person what failed, in their own words, and keeps the turn alive.

- Refuse before dispatch. The guard checks the name before the tool runs, so a blocked tool never reaches its handler, not even to fail.

- The tenant is not an argument. A model cannot be talked into another tenant's corpus, because no argument exists to carry it. The runtime supplies the tenant from the roster.

- Budgets beside the tools. `BLOCKED` and `TIMEOUTS` sit next to the tool definitions, so adding a tool without a budget or a block decision shows up in review.

- A cut call is data, and a stop is an answer. An abandoned call returns a payload error like a failed search, so the model can explain it. A stopped turn answers HTTP 200 with a sentence that says it is incomplete, and leaves its thread whole: a 500 would lose the turn, and an open tool call would break the next one.

- A turn ends before the walls around it. The deadline is 100 seconds. One retry's backoff, about 2 seconds, and the last tool's one-second floor bring the worst case to about 103 seconds, under the UI's 120, gunicorn's 120 and Cloud Run's 300. The kit's test checks that sum. The framework's own step limits stay, at 58 steps for the LangChain and LangGraph brains, as a backstop the Meter reaches first.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- An abandoned call still runs, and is still billed. The turn stops waiting, but the call's thread runs on until its client gives up, and rag-api answers it and bills it. The turn's rupees do not count that answer.

- The month's counter does not see the turn's own spend. The chat row now carries the turn's `cost_usd`, but `tenant_daily` and `make usage` count rag-api's rows only, so the agent's own model calls are outside the monthly figure. Lesson 11.6 takes this up.

- The limits are the service's, not the tenant's. One setting on the chat service holds every tenant and every caller to the same 12 calls, Rs 5 and 100 seconds.

- The A2A peer has no cap of its own. Its `/health` names none, so ADK's default of 500 model calls a task applies to it.

- `refusals` mixes policy and mistakes. A blocked name, a bad argument, an unknown tool and an unknown tier all land in the same list, and nothing in the four keys says which is which.

- The arguments are logged nowhere. The guard logs names and times. The chat row keeps names. rag-api's row has no filters. A bad `doc_type` shows only as `pool 0`.

- The tool invites filters the corpus cannot honour. `retrieve`'s docstring offers policy, contract, invoice, form and research_paper, and the worker stamps every text upload `unknown`.

- The token is minted outside the `try`. In the one `retrieve()`, a failure to mint the ID token raises instead of returning data. No brain catches it, by design: an error result is for a call the model got wrong, and a mint failure is the service's own. So the whole turn fails, in all four brains: a 500, with no answer.

### Verify it yourself: the checklist

Twelve checks, each one block above, each with the value that proves it on your lane.

The chat service has two new revisions from the drill, and the last one runs with `CHAT_MAX_MODEL_CALLS` as it was before. Its log holds the drill's eight turns, three of them with `stopped_by model_calls` on their rows, and three requests from step 5: a 403, a 401 and one answered turn in session `lesson103`. rag-api has a row for each search: the drill's, the member's turn, and step 6's two retrievals, one of them an empty pool. Lesson 5.6 puts a door in front of every brain, for the questions the law hands to a person, and lesson 5.7 puts the same question through all four brains and compares their costs and traces.

Netsetos GenAI on GCP · Module 5 MCP and agents · Lesson 5.5 Diagnose tool arguments, access failures and timeouts · v5.0

Next: Lesson 5.6 Hand a question to the person the law names.
