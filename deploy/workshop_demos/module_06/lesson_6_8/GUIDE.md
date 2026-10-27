# Lesson 6.8: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_6.8_Checkpoint_Resume_WIX.html`, reviewed at blob `348f42b5d8a0f3bd6fa7cd9413e7e42fd83d5a0f`. Learners read that page on the course site; this guide keeps its prose.

A turn is not one call. It is a run of steps, and LangGraph saves a checkpoint after every one: the question, the model's request for a tool, the tool's result, the answer. So a turn that stops halfway is not lost. Its last checkpoint says what was due next, and `graph.invoke(None, config)` runs exactly that, without repeating a step. You read your own conversation back from your lane, step by step. You finish the kit's cut-off turn from its checkpoint, then watch what the chat service does instead when the next question arrives. Last, you export your thread, replay and fork it on your machine with Gemini, and check that the lane's rows never moved.

- A turn, checkpoint by checkpoint

- The words: checkpoint, step, source, next, resume, replay, fork, repair

- Before you run anything: set up the shell

- Your conversation, read back step by step

- A turn cut off mid-flight, resumed from its checkpoint

- What the chat service does instead: a new question, and the repair

- One step read back, and the thread exported

- Your thread replayed and forked on your machine

- The table, read directly

- Why it is built this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn how a checkpoint's `next` shows that a turn was cut off, and why resuming it is `invoke(None)` and not a new question. Then you will prove it: your UI conversation read back step by step, the kit's cut-off turn finished from its checkpoint, a replay that matches, and your lane's thread replayed and forked on your machine while its rows stay as they were.

### A turn, checkpoint by checkpoint

What a checkpoint holds, what a cut-off turn looks like, and the ways on from it.

A turn is a chain of checkpoints. The LangGraph brain runs a turn as steps. The question is applied, the agent node calls the model, the tools node runs the search the model asked for, and the agent node reads the result and answers. After every step the checkpointer saves a checkpoint: the messages so far, each channel's version, the step number, what wrote it, and the checkpoint before it. Lesson 6.6 counted them, five for a turn with one search. Each checkpoint names its parent, so a thread is a chain you can walk back.

`next` is the work still due. A checkpoint does not store which node runs after it. LangGraph works that out from the channels' versions and the graph's edges, which is why reading a thread back means rebuilding the brain's graph, with a model that is never called. When a turn ends, its last checkpoint's `next` is empty. When a turn stops halfway, because the process running it stopped, the last checkpoint keeps a `next`. `tools` means the model asked for a search and the search never ran. The kit ships such a thread, `evals/threads/cut_off_turn.json`: its second turn was cut off by closing its stream right after the model asked for `retrieve`.

Resuming is `invoke(None)`. Calling the graph with no input on that checkpoint resumes it. LangGraph runs only what is due, the tool and then the model, and nothing before them again: the model's first call is not repeated, the search runs once, and no rupee is spent twice. Calling the graph with a new question is a different thing. LangGraph treats new input as a new run, and discards the tasks the last checkpoint left unfinished. The model's request stays in the thread with no answer, and every later turn sends it again.

A paused turn is the same checkpoint, stopped on purpose. Lesson 5.8's approval graph calls `interrupt()` where a person must decide, the checkpointer keeps the turn waiting there, and the decision resumes it with `Command(resume=...)`. That is also input that continues a checkpoint rather than starting a run. The chat service uses it only for a company whose `agent_actions` switch an operator set to `approval` (lesson 5.8's step 8); for every other company, and by default, no turn on your lane pauses. This lesson resumes turns that were cut off.

Replay and fork, on a copy. `invoke(None)` from an earlier checkpoint replays the turn from there, as a new branch beside the old line. `update_state()` on an earlier checkpoint with a different question, then `invoke(None)`, is a fork. The thread keeps every branch, and `get_state_history()` lists them all. The kit does neither on the lane. `make thread` reads your thread in a database session that cannot write, and `make replay` copies it into a saver on your machine and replays and forks the copy.

The chat service never resumes. Every `/v1/chat` request carries a question, so the brain always calls the graph with new input, and the request that was cut off has no caller left to ask. The kit repairs a thread in one case only, when the framework's recursion limit trips: `limits.repair_thread()` answers every open call with an error and ends the turn. A turn cut off any other way stays open on the lane.

A rain-stopped match. The scorer writes down every ball as it is bowled, so the scorebook says where the match stands after each one. Rain stops play just after the fielding side asks for a review, before the third umpire has ruled. When play resumes, nobody bowls the over again: the umpires restart from the last entry, the review is decided first, and the over goes on from there. Had play simply restarted with a fresh over, the review would sit in the book unanswered for the rest of the match, and only an umpire's ruling could close it. The broadcaster's replay of the over changes nothing in the scorebook. Nor does the commentators' "what if he had bowled it fuller", which plays a different ball from the same moment.

#### The kit's cut-off thread, step by step

This is the kit's own cut-off thread, read from `evals/threads/cut_off_turn.json` when this page was built: two turns, 8 checkpoints. Step through it, then choose what happens at the cut. Each way on was run on the kit's LangGraph brain when this page was built, with step 4's offline script, and asks the same next question: Is gratuity payable to an apprentice?

The ringed chip is the cut. A way on adds dashed chips: each is a checkpoint the kit's graph wrote when this page was built, with its step, its source, its `next`, the step it follows and its messages. Steps 4 and 5 run the same ways on in your shell.

It shows a thread the kit wrote offline with a scripted model, so the words are the script's. Its turn was cut off by a closed stream. On your lane a turn stops when the process running it stops, which no page can make happen on cue. The panel shows what such a checkpoint holds, and what each way on writes after it.

### The words: checkpoint, step, source, next, resume, replay, fork, repair

Thirteen rows, each with the value it takes on your lane.

One distinction to hold. Resume, replay and a new question all call the same graph, and what differs is the input. With no input, LangGraph continues the checkpoint you name. With a new question, it starts a new run and drops whatever that checkpoint left undone.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `ME` and `API`. `make thread` and `make replay` run in `~/graph-venv`, lesson 5.4's venv: `commands/graph-venv.sh` makes it if it is missing and installs the chat image's pins into it, and `make thread` adds lesson 6.6's Cloud SQL connector. The Python cells use the same venv, so run the steps in order. Your account must be able to read the DSN secret and connect to the instance, as in lesson 6.6, and to mint tokens as `documind-ui-sa`, as the setup's `tok` does. Step 3 needs you in a browser. Steps 4 and 5 run offline at Rs 0; the model calls in steps 3, 5 and 7 are priced in step 9. Nothing on your lane is written but your step 3 conversation.

### Your conversation, read back step by step

Two questions in the UI on the LangGraph brain, then the thread they wrote, a row per checkpoint.

#### Definition

The UI keeps one conversation per browser session and never shows its session id. The chat service files the conversation under `acme:`your email`:`that session, so `make thread EMAIL="$ME"` can find it: it lists your threads, one row per session, the latest written first. Given `SESSION=`, it decodes that thread along its latest history, a row per checkpoint: when it was written (UTC), its source, the brain that wrote it, its `next`, how many messages it holds, and the newest one. It connects the way lesson 6.6's cells did, through the Cloud SQL connector as the `chat` user, and makes its session read only before the first query. Every statement it sends after that is a `SELECT`.

#### The code

#### Do it: two questions in the UI

- Open that address, and sign in with the account the line names.

- In the sidebar, set Brain to `langgraph`. It starts on `direct`, which does not reach the chat service.

- Ask: After how many years of continuous service is gratuity payable?

- When the answer is in, ask: Is it payable to a contract employee?

Two answers with their citations, each with a caption that begins `brain: langgraph` and ends with the turn's own rupees.

#### Do it: your thread

Your two questions are one thread, under your email and the session the UI made. Each turn opens with an `input` checkpoint: the question is in the input, not yet in the messages, and `next` is `__start__`. Each `loop` checkpoint after it adds one message: the question, the model's call for `retrieve`, the passages, the answer. A turn with one search is five checkpoints, and the step runs on across turns, so two such turns are ten, steps -1 to 8.

No row's `next` was read from the table. `make thread` asked the LangGraph brain's own graph, built over a saver that refuses writes and a model that is never called. The last row's `next` is empty: your turn ended. A last row with `next` `tools` would be a turn cut off with its search still due.

### A turn cut off mid-flight, resumed from its checkpoint

The kit's cut-off thread copied into a local saver and finished with `invoke(None)`, then a finished turn replayed to match.

#### Definition

The kit's cut-off thread was written by running two turns of the kit's LangGraph brain offline and closing the second turn's stream right after the model asked for `retrieve`, as a client that goes away does. Its last checkpoint, step 6, holds the call and has `next` `tools`. `make replay OFFLINE=1` reads it and does four things, all on your machine. It copies the thread into a local `InMemorySaver`, one `update_state()` per checkpoint, each written as the node that wrote it, so every copied step has the file's step, `next` and messages. It resumes from where the turn stopped, with `graph.invoke(None, ...)`. It forks from the turn's input checkpoint with another question. And it lists every checkpoint with `get_state_history()`.

Offline, the model is a script: the thread's own model messages played back, then a rule (search for the question, then answer from the first passage). A search the thread recorded is answered as recorded, and any other by the kit's Rs 0 lane over `evals/corpus`. A socket guard refuses any connection that would leave your machine, and nothing mints a token.

#### The code

#### Do it: the cut-off turn, resumed

The copy matched the file step for step. The replay ran what step 6 said was due: the tools node searched, then the agent node called the model once and answered. Nothing before step 6 ran again, not the question and not the model's first call. That is the lesson's proof, a turn cut off mid-flight and resumed from its checkpoint.

The resumed turn went on from step 6, so it extends the copied line. The fork went back to step 4, the second turn's input, and wrote another question there. `get_state_history()` lists both, 14 checkpoints in 2 branches, each with the step it follows. The script costs nothing, and the lane was never touched.

#### Do it: a finished turn, replayed

At step 0 the first turn had not yet called the model, and the file recorded everything after it, so there is something to compare. The replay re-runs the turn from there and compares what it produced with what the file recorded: each message's kind and the tools it asked for, the sources each search returned, and the answer. A recording that stops mid-turn, like this thread's second turn, is compared as far as it goes, and the rest is what the replay added.

The replay matches: the same steps, the same 5 sources, the same answer. It is a new branch from step 0, and the recorded one is still there beside it. Offline, the script plays the recorded model messages back, so a match is exact. In step 7 the model is Gemini, and an answer's words can change from one run to the next, so read the steps and the sources first.

### What the chat service does instead: a new question, and the repair

The next question on the cut-off thread, as `/v1/chat` sends it, before and after `limits.repair_thread()`; then the same question to Gemini.

#### Definition

`/v1/chat` has no resume. Every request carries a question, and the brain calls `graph.invoke()` with it as new input; nothing in the service calls `invoke(None)`, and the request that was cut off has no caller left to ask. The cell copies the cut-off thread into a new saver twice. The first copy gets the next question as it is. The second is first repaired with `limits.repair_thread()`, the function the LangChain and LangGraph brains call when the framework's recursion limit trips, and then gets the same question. Both run offline, as in step 4.

#### The code

#### Do it: the next question, offline

On the first copy the new question was answered, and message 6, the model's call for `retrieve`, never was. New input makes LangGraph discard the tasks the last checkpoint left unfinished (langgraph 1.2.12, `pregel/_loop.py:978`), so the search step 6 was waiting for never ran. The thread went on to step 11 with the call still open, and every later turn will send it to the model again.

On the repaired copy, `repair_thread()` answered the open call with an error and ended the turn with the stop answer, written as the agent node, so nothing was due. The question then started on a whole thread, and reached step 12 with no call left open.

#### Do it: the next question, with Gemini

The script above accepts any history. Gemini is the model your lane runs, so this cell asks it the same question on a copy of the cut-off thread, through the kit's LangGraph brain, with your lane's rag-api as `documind-ui-sa`: what `/v1/chat` would do. It prints the answer, or the error that would have been the request's 500, then the messages from the open call on, the calls left open and what the turn cost.

Whatever Gemini made of a call with no answer, the call is still open in the thread. A refusal would repeat on every later turn of the session, since each one sends the whole thread; an answer means the model talked past a search that never ran. Either way the thread now records a request that was never met. So a cut-off turn needs finishing, as step 4 did, or repairing, as above, before the next question, and the chat service does neither today (step 9).

### One step read back, and the thread exported

The messages saved just before your first search ran, then your whole thread in a file.

#### Definition

`AT=` prints one checkpoint: its id and its parent's, when it was written, its metadata, any task's error, and every message saved there. `EXPORT=` writes the thread along its latest history to a file in the kit's `documind-thread/1` format: each checkpoint's step, source, brain, `next`, metadata and message ids, and every message once. Reading a checkpoint is the pinned library's own decode (langgraph-checkpoint-postgres 3.1.2). Its values are its plain values, kept inline in the row, plus the blob of each channel at the version the row names; each blob goes through a serializer that revives only the types langgraph lists as safe. Each checkpoint is then read through the graph of the brain that wrote it, and that is how its `next` is known.

#### The code

#### Do it

Step 1 holds two messages, your first question and the model's call for `retrieve`, with `next` `tools`: the moment before your first search ran. Had the process stopped there, this would be your thread's last row, and your turn would look like the kit's fixture. The export holds the same thread, which `make replay` reads in step 7. It is a file in your home directory, and the lane did not change.

### Your thread replayed and forked on your machine

Your follow-up asked again, with Gemini and your lane's rag-api; a fork with another follow-up; then the same with one clause taken out of the prompt.

#### Definition

`make replay FILE=` runs step 4's four steps on your export, with Gemini on location `global` and your lane's rag-api as `documind-ui-sa`. The target reads your project number to build the API's address, and sets the three variables the kit reads: the project Gemini is called in, the API's address, and the account each search is made as. A finished thread replays its last turn from its question, so the model is asked your follow-up again, with your first turn as its history. `FORK=` is the fork's question, asked from the same turn's input checkpoint. The replay and the fork each have their own `limits.Meter`, which prices their model calls and searches at list price, as the chat service does. Only the local copy is written.

#### The code

#### Do it

The copy matched your export step for step. The replay asked Gemini your follow-up again, and its comparison line says how close it came to your recorded turn. Read the steps and the sources first: whether the model searched again, and whether the search returned the same passages. A different answer in different words is the model, not the thread. The fork asked another follow-up from the same point, so its first new message is the new question, and your old follow-up is not in it. The history lists the copy, the replay and the fork, each with the step it branched from, and the last line gives what it cost. None of it reached the lane.

#### Change it: the prompt's rule for follow-ups

The system prompt tells the model to search for every document question, "a follow-up too". Take that clause out of your clone's `brains.py` and replay the same turn: the replay asks your follow-up again with the edited prompt and the same history. The lane's prompt does not change, since the replay runs the brain from your clone, on your machine.

The comparison line is the result. If the replay's steps read `ai` alone, the model answered your follow-up from the first turn's passages without searching. If they still read `ai asks retrieve, tool, ai`, the clause was not what made it search. Either way you tested a prompt change against a real conversation of yours, for the price of a turn or two, and deployed nothing. The checkout put the kit's prompt back.

### The table, read directly

Your thread's rows counted on the lane, and its newest messages blob decoded by hand.

#### Definition

The cell is lesson 6.6's thread cell, extended. It connects the same way and makes its session read only first, as `make thread` does. It counts your thread's checkpoints on the lane and sets the count beside step 6's export. Then it reads which version of `messages` the newest checkpoint names, fetches that version's row from `checkpoint_blobs`, and decodes it with the pinned serializer's `loads_typed()`, strict, as `thread_read.py` builds it.

#### Do it

The lane holds as many checkpoints as the export does. Step 7 replayed and forked your thread twice, and every checkpoint it wrote went into a saver on your machine, so your thread on the lane has not one more row. The blob is the whole conversation at its newest version, as lesson 6.6 found every version is, and it decodes into LangChain's own message classes, which are on langgraph's safe list. A type that is not on it would come back as plain data, and no module a database row names would be imported.

### Why it is built this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own code and comments, then the bill and the gaps.

- Every step is saved, so a turn resumes where it stopped. Resuming runs only what the last checkpoint says is due. No model call, search or rupee is spent twice, and nothing the person already saw is rewritten.

- `next` is asked, not stored. A row does not say what runs next, so `thread_read.py` rebuilds each brain's graph, with a model that is never called, and asks LangGraph. It reads each checkpoint through the graph of the brain that wrote it, since the LangChain brain's model node is `model` and the LangGraph brain's is `agent`.

- Reading cannot write. The session is made read only before its first query, every statement is a `SELECT`, the graphs read through a saver that refuses writes, and the serializer never imports a module a blob names.

- Replays and forks run on a copy. A customer's thread on the lane never gets a branch from someone's debugging. The copy is checked against the file step for step, so a replay starts where the lane's thread really was.

- Every version is kept. That is what makes any step of any thread readable, as step 6 read step 1. The price is lesson 6.6's storage, which grows faster than the conversations.

#### What it costs

An agent turn with one search is three calls: the model asking for `retrieve`, rag-api's grounded answer to the search, and the model's own answer. The estimates price each at the course's typical answer, 2,000 tokens in and 300 out at gemini-3.6-flash's list price: Rs 0.45 a call, Rs 1.34 a turn, about Rs 9.37 for the whole lesson at most. The UI's captions and the replay's last line print what yours actually cost.

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- The chat service never resumes, and never heals. Every `/v1/chat` turn is new input, and nothing in the service calls `invoke(None)`. A turn cut off on your lane keeps its open call, and the next question makes LangGraph discard the work that was due. `repair_thread()` runs only after a recursion error, and nothing heals a cut-off thread when the next question arrives.

- Two turns at once can branch a thread. Nothing in the service stops two requests on one session from starting from the same checkpoint. `make thread` counts the checkpoints off the latest line and decodes only that line.

- Forks exist only on your machine. The service has no route that writes a past checkpoint, so a person cannot edit an earlier question in the UI and branch the conversation there.

- Not every conversation can be read back. The ADK brain keeps its sessions in memory on this image, as lesson 6.6 found, so they are not in these tables, and `make thread` lists a Desk thread without decoding it.

### Verify it yourself: the checklist

Ten checks, each one block above, each with the value that proves it.

One new thread: your step 3 conversation, under your email, written by the chat service as every turn is. Nothing else in the checkpoint tables changed: `make thread` and step 8 read in sessions that cannot write, and every replay, fork and repair ran on a copy on your machine. rag-api logged a usage row for each search that step 5's Gemini cell and step 7's replays made, as `documind-ui-sa`. On your machine, `~/lesson68.json` holds your export, `/tmp/lesson68-threads.txt` your list of threads, and `~/graph-venv` the chat image's pins and the Cloud SQL connector; `services/chat/brains.py` is back as the kit has it. Lesson 6.9 keeps each model call's context under a ceiling while the thread itself grows.

Netsetos GenAI on GCP · Module 6 Context and memory · Lesson 6.8 Resume a paused or cut-off turn: checkpoint and resume · v5.0

Next: Lesson 6.9 Budget working memory: windowing, compaction and write rules.
