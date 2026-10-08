# Lesson 6.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_6.5_State_History_WIX.html`, reviewed at blob `a4df41e28a582704ba318ce387bc1df09b3dfddb`. Learners read that page on the course site; this guide keeps its prose.

An agent seems to remember three kinds of thing, and they live in three different places. Agent state is what one turn builds: the question, the model's call for a tool, what the tool returned, the answer. Conversation history is that state, checkpointed after every step and read back on the next turn of the same thread. Knowledge is the tenant's corpus, which the agent never remembers: it looks it up, every time. You take one turn apart on the kit's own code. You start the chat service's checkpointer the way no deployment should, and read the line it logs when you do. Then you watch one conversation cross four brains and two sessions on your lane.

- Three kinds of memory

- The words: state, checkpoint, checkpointer, thread, history, session, knowledge

- Before you run anything: set up the shell

- One turn, taken apart

- The memory checkpointer, and the line it logs

- One conversation, four brains, two sessions

- Which checkpointer your lane runs

- Why memory is split this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn to tell the three apart by four questions: where it lives, what it is keyed by, how long it is kept, and who can read it. You will see why a tool result makes knowledge part of the history, and why the memory checkpointer is a valid setting that no deployment uses. Then you will prove it: one turn's messages and checkpoints, the warning line the chat service logs with `CHECKPOINT_DSN=memory`, a restart that forgets, and a conversation that follows the checkpointer's thread rather than the brain's name.

### Three kinds of memory

One turn, one thread, one tenant.

State is one turn. When a question arrives, the brain builds a list of messages: the question, the model's request for a tool, the tool's result, the answer. That list is the agent's state, and in LangChain and LangGraph it is literally the graph's `messages`. After every step, the checkpointer writes a checkpoint of it, 5 for a turn with one tool call. The system prompt is not in it. The brains send the prompt with every model call and never store it, so a changed prompt reaches old conversations too.

History is the thread. The checkpoints are kept under a thread id that the server builds from the verified identity: tenant, person, session. The next turn with the same three reads the latest checkpoint back, and the model sees the whole conversation so far. A new session is a new thread, and starts empty. What keeps the thread decides how long history lasts. On your lane it is `PostgresSaver` on Cloud SQL, shared by every instance. On a laptop it is a SQLite file. With `CHECKPOINT_DSN=memory` it is a dictionary inside one instance, and the service says so when it starts.

Knowledge is looked up. The tenant's documents live in rag-api's index, keyed by the tenant, and every conversation of every member reads the same corpus through `retrieve()`. The agent does not remember knowledge. But what `retrieve()` returned is a message in the state, so it is checkpointed like the rest. A copy of the knowledge sits in the history, as it was when it was fetched. When the corpus changes, the index changes and the copy does not.

Four brains, three stores. LangChain and LangGraph share the checkpointer and its thread, so either can continue the other's conversation. The ADK brain keeps its conversation in ADK's own session store, under the same thread id. On your lane that store is the instance's memory, because the image cannot open the database one; lesson 6.6 shows why. The direct brain keeps nothing: every turn stands alone.

A visit to a hospital's OPD. The doctor's notes during your consultation are the agent state: what you said, what the doctor looked up, what was decided, all on one sheet while you sit there. Your case paper is the conversation history. The hospital files it under your registration number, and the next doctor who opens it sees your last visit. Keep case papers only on one doctor's desk and they are gone when the shift ends, and the doctor in the next room never sees them. The formulary in the library is the knowledge. Every doctor looks things up there, for every patient. When the formulary is revised, old case papers still show the dose that was written then.

#### Where each thing lives

Choose something the agent seems to remember. The panel shows which kind it is, where it lives, what it is keyed by, how long it is kept, who reads it, and what `CHECKPOINT_DSN=memory` changes.

Every value is read from the kit's `agent.py`, `brains.py` and the UI's `chat.py` at build time. The 5 checkpoints a turn writes come from step 3's cell, run on the kit's `brains.py`.

It shows where things live, not what a model does with them. Whether a model searches again, or answers from a quote already in its history, is the model's choice. Step 3 shows only what the history holds.

### The words: state, checkpoint, checkpointer, thread, history, session, knowledge

Ten rows, each with the value it takes on your lane.

One distinction to hold. State is what one turn is building. History is what the checkpointer kept of earlier turns. Knowledge is what nobody keeps and everyone can look up.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER` and `tok`. You need `~/graph-venv` from lesson 5.4. Step 3's first cell adds FastAPI and the SQLite checkpointer to it, and makes it if it is missing. The chat service must be running in your region, from lesson 5.1's step 3. Step 5 asks six questions through the chat service. Nothing in your lane's configuration changes.

### One turn, taken apart

The kit's LangChain brain answers once; you read what the thread kept, then change the corpus under it.

#### Definition

The cell builds the kit's `LangChainBrain` on an in-memory checkpointer. It has a model that says what it is told, and a stand-in rag-api whose corpus says the notice period is 60 days. Turn 1 asks for the notice period, and the model calls `retrieve` and answers. The cell prints what the thread kept, whether the system prompt is among it, and how many checkpoints the turn wrote. Then the corpus changes to 90 days, as lesson 6.3's second handbook did. Turn 2 goes to the LangGraph brain, on the same thread. The cell prints what the history quotes and what the corpus now says. Last, it looks at a new session of the same person.

#### The code

#### Do it: the venv

#### Do it: one turn

Turn 1 left four messages in the thread: the question, the model's call for `retrieve`, the tool's result, the answer. That was the agent's state, and now it is history. The system prompt is not among them. The turn wrote 5 checkpoints, one per step, and the next turn reads only the latest.

Turn 2 went to a different brain, and it found turn 1, because LangChain and LangGraph share the checkpointer and the thread id. The history still quotes 60 days while the corpus says 90. The tool result is a copy of knowledge, made when it was fetched. Whether a real model searches again or answers from that copy is the model's choice, and nothing in the kit makes it search again. The new session found nothing: history is per thread, and the thread is tenant, person and session.

### The memory checkpointer, and the line it logs

The chat service's own start-up code with `CHECKPOINT_DSN=memory`, then a restart.

#### Definition

The chat service picks its checkpointer once, at start-up, in `build_checkpointer()`. `CHECKPOINT_DSN=memory` is a valid value, and the only one that logs anything: a warning that conversations die with the instance. The cell sets the value the way the service reads it, builds the checkpointer with the kit's own function, and keeps one turn in it. Then it builds the checkpointer again, as a restarted or second instance would, and looks for the turn. Last, it does the same with the laptop lane's `SqliteSaver`, a file on disk.

#### The code

#### Do it

The `WARNING` line is this lesson's proof, printed by the chat service's own code each time a checkpointer is built with memory. The first checkpointer kept the turn: two messages, the word and the reply. The second, built the way a restarted instance builds it, found nothing. On Cloud Run that happens whenever the service scales to zero. A second instance never sees the first one's dictionary at all.

The SQLite file kept the turn across the restart, because it is a file. It is still one file per machine, which is why `agent.py` keeps it for the laptop lane.

### One conversation, four brains, two sessions

A word to remember, asked for by every brain, then a question only the corpus can answer.

#### Definition

Six turns go through your chat service, as `documind-ui-sa`. In session A, the LangChain brain is given a word to remember. The LangGraph, ADK and direct brains are then each asked for it, in the same session. In session B, the LangChain brain is asked for the word, then a question only the corpus can answer. Each run uses two fresh session names.

#### The code

#### Do it

The word followed the checkpointer's thread. LangGraph found it because it reads the same thread as LangChain. ADK did not, though its session id is the same string, because it keeps its conversations in its own store, which on your lane is the instance's memory. The direct brain has no history, so it searched the corpus for your question and found nothing about a word.

Session B was a new thread and knew nothing of session A. But session B still answered the gratuity question: knowledge belongs to the tenant, not to a conversation. The UI's brain radio sends one session id whichever brain you pick. So switching to ADK or direct mid-conversation loses the thread in just this way.

### Which checkpointer your lane runs

What the service is configured with, and whether it ever warned.

#### Definition

The service's configuration decides which checkpointer it builds. The cell reads `CHECKPOINT_DSN` and the Cloud SQL instance from `documind-chat`'s current template. Then it searches 30 days of the service's log for the memory warning.

#### Do it

`CHECKPOINT_DSN` comes from a Secret Manager secret, the Postgres URL Terraform wrote, and the service mounts the Cloud SQL instance it points at. So the service builds `PostgresSaver`, and every instance reads and writes the same threads. The memory warning never appeared: `make deploy-services` always mounts the secret, and no make target deploys memory.

Notice what proved it: the configuration, not a log line. `PostgresSaver` and `SqliteSaver` open silently, and only the memory checkpointer announces itself. Lesson 6.6 opens the tables.

### Why memory is split this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- The thread id is the tenancy boundary. The tenant comes first, so nothing after it can name another tenant, and `:` is banned in every part, so two people cannot land on one thread. A session id from the request names a conversation, never a tenant.

- Instructions are not history. The system prompt is sent with every call and never stored, so a prompt change applies to old threads too.

- A conversation survives a restart. The checkpointer is opened once, when the service starts, and shared by every request. On Cloud SQL, every instance reads the same threads.

- Knowledge is looked up, never remembered. The tenant comes from the roster, and `retrieve()` asks rag-api every time. So a retired document stops being found, though an old thread may still quote it.

- ADK keeps its own sessions. `brains.py` names this as one of its two honest limits: the ADK brain's conversation lives in ADK's session service, not the LangGraph checkpointer.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- Nothing deletes a conversation. No route, job or expiry removes a thread. Every turn adds 5 checkpoints or more, and they stay.

- History keeps knowledge the corpus has replaced. A tool result is stored in the thread as it was fetched. `make retire` and a reindex change the index and never touch a thread, so an old conversation can still quote a superseded clause.

- Switching brains splits the history. LangChain and LangGraph share a thread, ADK keeps its own, and direct keeps none. The UI's brain radio keeps one session id for all four.

- Only the wrong checkpointer announces itself. `build_checkpointer()` logs one line, the memory warning. `PostgresSaver` and `SqliteSaver` open silently, so the checkpointer in use shows only in the service's configuration.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

Nothing is configured. Your chat service holds two more threads for `documind-ui-sa`, sessions A and B, and one instance holds ADK's session for A, in memory. rag-api's log has at least two more rows: the direct brain's search and the gratuity answer. `~/graph-venv` has FastAPI and the SQLite checkpointer. Lesson 6.6 opens the tables those threads live in.

Netsetos GenAI on GCP · Module 6 Context and memory · Lesson 6.5 Distinguish agent state, conversation history and knowledge · v5.0

Next: Lesson 6.6 Configure and inspect durable conversation storage.
