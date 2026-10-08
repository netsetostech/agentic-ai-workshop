# Lesson 6.6: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_6.6_Durable_Storage_WIX.html`, reviewed at blob `3f82eb1abf6a809f82f7d6b46288248b73c26c3e`. Learners read that page on the course site; this guide keeps its prose.

Lesson 6.5 showed that your lane's conversations live in `PostgresSaver` on Cloud SQL. This lesson opens that storage. Terraform made an instance, a database, a user and a secret; the service mounts them; a one-off job made the tables. Each turn then writes a checkpoint row per step and, for the conversation itself, the whole list of messages again at every new version. You count what a turn writes on the kit's own code, and read the configuration your lane runs. You connect to the database the way the service does, through the Cloud SQL connector, and list the tables and one row per thread. On the way you find which brain's conversations are not there at all.

- What holds a conversation

- The words: instance, DSN, connector, migration, checkpoint, blob, write, thread

- Before you run anything: set up the shell

- What a turn writes

- What your lane runs

- The tables, and one row per thread

- One thread, step by step

- Why storage is built this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn the four pieces that make a conversation outlive an instance, the four tables `PostgresSaver` keeps, and why a conversation's storage grows faster than the conversation. Then you will prove it: the checkpoints and versions two turns write, your lane's instance, secret and setup job, the checkpoint tables with one row per thread, and one thread's rows in order.

### What holds a conversation

Four pieces, four tables, and one store that is not there.

Four pieces. A conversation outlives an instance only if something outside the instance holds it. On your lane that is a Cloud SQL for PostgreSQL instance, `documind-checkpoint`: the smallest tier, one zone, 10 GB, no backups. Terraform gives it a database, `documind`, and a user, `chat`. It writes the connection string, the DSN, into a Secret Manager secret. The chat service mounts the secret as `CHECKPOINT_DSN` and the instance as a socket, so the password is never in its image or the repository. The instance has a public address and no authorized networks, so nothing on the internet can open a connection. The Cloud SQL connector checks an identity with IAM, and opens the connection for it.

Tables made once, by a job. `PostgresSaver` needs its tables before the first turn. `setup()` creates them, and it is safe to run twice, which makes it tempting to run at start-up. The kit does not: `setup()` takes exclusive locks, and several instances racing to run it fail at random. So `migrate.py` runs it as a Cloud Run job. Version 3.1.2 applies 10 migrations: four tables, three indexes, two column changes, and one that does nothing but keep the count right. The service opens one connection pool per instance at start-up, of one to four connections, and never calls `setup()`.

Four tables. `checkpoints` holds a row per step of every turn, keyed by the thread id. `checkpoint_blobs` holds the values of the graph's channels, a row per new version. `checkpoint_writes` holds what each step wrote. `checkpoint_migrations` holds a row per migration applied. The conversation itself is the `messages` channel, and every new version of it is stored whole: the list of all messages so far, again. A turn with one tool call adds four messages, so four new versions, each longer than the last.

What is not there. The ADK brain asks for a database store too, on the same DSN. That needs SQLAlchemy, which google-adk installs only with its `db` extra, and the chat image installs google-adk without it. So the import fails, `brains.py` logs a warning, and ADK keeps its sessions in the instance's memory. That is what the memory checkpointer does, without the warning at start-up.

A sub-registrar's record room. The deeds are not kept at a clerk's desk. They go to the record room, which outlives every shift. The room has no street door; head office issues keys to named staff. The shelves were built once, by a contractor, before the first deed arrived, not by each clerk on their first morning, which is how one corner gets two sets of shelves. This record room also files a full photocopy of the file after every entry, so the shelves fill much faster than the files grow. One counter never sends its files to the room at all. Its clerk keeps them in a drawer, and they are gone when the shift ends.

#### What keeping every version costs

Choose how long a conversation runs, its tool calls, and how many conversations a day your tenants hold. The panel counts the checkpoint rows and versions of messages one conversation leaves. It compares the bytes those versions take with the latest version alone, and how they grow against the instance's 10 GB disk.

A turn with k tool calls writes 3 + 2k checkpoints and 2 + 2k versions of messages, as step 3 counts them on the kit's `brains.py`. Each message adds what it added there: a question 215 bytes, a tool call 314, five passages 1,759, an answer 261. Only the messages are counted; the other channels and the writes add more rows.

It counts what `PostgresSaver` keeps of the messages, not what Cloud SQL bills. The instance costs roughly Rs 700 to 850 a month whether it holds one conversation or ten thousand, and its disk is 10 GB.

### The words: instance, DSN, connector, migration, checkpoint, blob, write, thread

Ten rows, each with the value it takes on your lane.

One distinction to hold: a checkpoint is a moment, and a blob is a value at that moment. Checkpoints share a blob while the value does not change.

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

The shell, in the kit's folder, with `PROJECT` and `REGION`. You need `~/graph-venv` from lesson 5.4. Step 3's first cell adds the Cloud SQL connector to it, with the chat image's pins, and makes it if it is missing. Your account must be able to read the DSN secret and connect to the instance, and a project owner can. Steps 5 and 6 read the tables and write nothing. Nothing on your lane changes.

### What a turn writes

Two turns of the kit's LangChain brain, their checkpoints and versions counted, then the ADK brain given the lane's DSN.

#### Definition

The cell runs two turns of the kit's LangChain brain on one thread, against `InMemorySaver`. It has the interface `PostgresSaver` implements, one checkpoint per step and one stored value per new version, held in memory instead of Postgres. The first turn asks the brain to remember a word, and the model answers at once. The second asks about gratuity, and the model calls `retrieve`, which stands in with five passages. After each turn the cell counts the checkpoints and the new versions of messages. Then it prints every version, with its length and size. Last, it gives the ADK brain the lane's DSN, in a venv that has google-adk and no SQLAlchemy, as the chat image does.

#### The code

#### Do it: the venv

#### Do it: two turns

The first turn wrote three checkpoints and two versions of messages: the question, then the answer. The second wrote five and four, because the tool call and its result are messages too. Every version holds the whole list. So the last one, 3,021 bytes, is the conversation, and 8,152 bytes, all six versions, is what the table keeps. The five passages `retrieve()` returned are by far the largest message, and every later version stores them again.

The ADK brain logged its warning and chose memory. The chat image does the same with the same DSN, because it installs google-adk without SQLAlchemy.

### What your lane runs

The instance, the secret and the setup job, read from your project.

#### Definition

The cell reads the four pieces from your project. It shows the instance's engine, tier, zone, disk, backups and network. Then its databases and users, and the DSN secret's versions, never its value. It compares the setup job with the service: the image each runs, and when the job last ran. Last, it searches 30 days of the chat service's log for the ADK brain's fallback warning.

#### The code

#### Do it

The instance is what Terraform asked for: POSTGRES_16 on db-f1-micro, one zone, 10 GB, no backups, and a public address with no authorized networks. The database and user are `documind` and `chat`; `postgres` is Cloud SQL's own. The secret holds the DSN, and nothing printed it.

The setup job runs on every deploy of the chat service, but the deploy script creates it only when it is missing, so it keeps the image it was first created with. If its image differs from the service's, as here, every later run applied the old library's migrations. A newer checkpointer in the service would never get its own. The ADK line is step 3's warning, logged by your service on an ADK turn: those conversations were never in this database.

### The tables, and one row per thread

A connection through the Cloud SQL connector, as the `chat` user, reading only.

#### Definition

The cell connects the way the service does, through the Cloud SQL connector, as the `chat` user. It reads the DSN from the secret into memory, never onto the screen, and opens the connection with the Cloud SQL Python Connector and the pg8000 driver. Your account's IAM decides whether it may connect, and no network is opened to the internet. Then it lists the tables and their rows, the migrations `setup()` has applied, and one row per thread. Each row shows the tenant, person, session, checkpoints, the last step, and when it ran.

#### Do it

Four tables, the ones `setup()` made, and migrations 0 to 9: the job ran. One row per thread is this lesson's proof. Each is a conversation from your earlier lessons: the gate's two agent threads, lesson 5.5's turn, and lesson 6.5's two sessions. A thread with one tool turn has five checkpoints. Lesson 6.5's session B, one turn without a tool and one with, has eight, and its step count ran on across both turns.

There is no `smoke-adk` thread and no ADK table. The ADK brain's conversations were in an instance's memory, and they are gone.

### One thread, step by step

The latest thread's checkpoints in order, and the size of every version of its messages.

#### Definition

The cell takes the latest thread and lists its checkpoints in order. For each it shows the step, whether the step took input or ran the loop, and whether the messages changed. Where they changed, it prints the size of the version that step stored.

#### Do it

Each turn opens with an input checkpoint, where the messages have not changed yet. Then every step that adds a message stores the whole list again. The sizes climb by the size of each new message, and the big jump is the five passages. The total is the sum of every version, several times the latest. That is the cost of keeping every version, and step 1's panel scales it to your tenants.

### Why storage is built this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Only a database outlives the instance. `cloudsql.tf` gives the reasons. `InMemorySaver` dies with the process, and `SqliteSaver` is a file on one instance. Only a database survives a deploy, a scale-to-zero and an instance dying.

- The DSN is a secret, not a setting. It is mounted by `--set-secrets` and readable by the chat service's account, so the image and the repository never hold the password.

- No authorized networks. The connector checks an identity with IAM, so nothing on the internet can open a connection. Your shell's connector in step 5 went through the same check.

- `setup()` is a job. Exclusive locks and a keyed migrations table make a start-up `setup()` race across instances. A job runs it once, and the service never does.

- Every version is kept. Because each version is stored whole, a thread can be read back at any step. The price is tables that grow faster than the conversations.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- ADK's conversations are not durable. `brains.py` says the ADK brain uses `DatabaseSessionService` on the same Cloud SQL. The image installs google-adk without its `db` extra, so SQLAlchemy is missing, and the ADK brain keeps its sessions in memory, with only a warning.

- The setup job keeps its first image. The deploy script creates the job only when it is missing, then executes it. A newer checkpointer library in the service never has its migrations applied.

- Nothing prunes a thread's versions. Every version of messages stays, so storage grows with the square of a conversation's length. The package ships `ShallowPostgresSaver`, which keeps only the latest checkpoint, and the kit does not use it.

- No backups. `backup_configuration` is off, so losing the instance loses every conversation.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

Nothing. The cells read your project and the database, and wrote nothing. `~/graph-venv` has the Cloud SQL connector. Lesson 6.7 redeploys the chat service, checks that a conversation continues, and checks that another person finds nothing.

Netsetos GenAI on GCP · Module 6 Context and memory · Lesson 6.6 Configure and inspect durable conversation storage · v5.0

Next: Lesson 6.7 Verify restart recovery and session isolation.
