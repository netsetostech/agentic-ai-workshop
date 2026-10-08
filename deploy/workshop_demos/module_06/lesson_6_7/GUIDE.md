# Lesson 6.7: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_6.7_Restart_Isolation_WIX.html`, reviewed at blob `7220ffa4bff89e61f6a508a13b032fb08f8673ac`. Learners read that page on the course site; this guide keeps its prose.

Two properties make the chat service safe to put in front of people. A conversation must outlive the instance that held it, because Cloud Run replaces instances whenever the service scales to zero or you deploy. And a conversation must be readable by its own person alone, in their own tenant and session, whoever else knows its name. The kit builds both: the checkpointer lives outside the instance, and the server makes the thread id from the verified identity. A property you have not tried to break is only a claim. So you try to break both. You put the kit's own app in front of eight different callers. You redeploy your chat service between two turns. Then you ask, in the UI, for a word you never gave.

- Two properties, and how to watch them hold

- The words: revision, instance, redeploy, durable, thread, isolation, bearer leg, assertion

- Before you run anything: set up the shell

- Isolation, on the kit's own app

- A conversation across a redeploy

- Another person finds nothing

- The rows behind both

- Why the properties hold, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn which part of the kit makes each property true, and how to test a property by trying to break it. Then you will prove both: eight callers against the kit's own app, a word that survives a redeploy of your chat service and a word the ADK brain forgets. You will also find nothing when you ask in the UI, and see the rows that show why.

### Two properties, and how to watch them hold

Durability is about the instance. Isolation is about the key.

Durability is about the instance. Cloud Run runs your service as instances of a revision. It adds instances when traffic grows and removes them when it falls. It stops the last one when nobody calls, since the chat service's minimum is zero, and it starts a new revision on every deploy. Anything an instance keeps in its own memory ends with it. The LangChain and LangGraph brains keep the conversation in `PostgresSaver`, outside every instance, so a new instance reads the thread where the old one left it. The ADK brain keeps its sessions in the instance's memory on this image, as lesson 6.6 found, and loses them.

Isolation is about the key. The request carries a question, a session name and a brain. It has no field for a tenant or a person, and a field it does not have is ignored if you send it. The person comes from the verified token or the forwarded assertion, and the tenant from the roster. The server joins tenant, person and session into the thread id. A colleague who knows your session name reaches a different thread, because their email is in it. So does a member of another tenant. A session name with a colon, which could split the id, is refused before it gets that far.

Verifying means trying to break it. The test is to create the conditions that would break a property and watch it hold. Replace the instances between two turns, ask as someone else, name another tenant, send a session name with a colon. Some callers cannot be made on your lane, so you run the kit's app under a test client for them. The restart cannot be faked, so you redeploy your lane.

A bank's lockers. Each customer's lockers are numbered in their own series, so two customers can both have a locker 113. The staff open the one registered to the person in front of them, checked against their ID card. A note on the form saying "I belong to the other branch" changes nothing, because the register says which branch you belong to. The lockers are in the vault, not behind a teller's counter, so a change of shift or a renovation leaves them where they were. One counter keeps its customers' things in a drawer instead, and they are gone when that counter closes.

#### Who finds the word

Alice gave a word in session `lesson113`. Choose who asks for it next, where the conversation is kept, what happens between the two turns, and which brain answers. The panel shows the status, the thread the question reaches, and what it finds.

The statuses and texts are the kit's own, from step 3's run of its chat app. The rule is checked against that run, and against the page's own copy of it for all 144 choices.

It follows the kit's rules, not a model's words. On your lane the model answers in its own way. What the panel predicts is whether the history it is sent contains the word.

### The words: revision, instance, redeploy, durable, thread, isolation, bearer leg, assertion

Ten rows, each with the value it takes on your lane.

One distinction to hold: durability decides whether the thread is still there, and isolation decides whose thread a question reaches. A turn needs both to find its own history.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `ME` and `tok`. You need `~/graph-venv` from lesson 5.4. Step 3's first cell adds FastAPI and lesson 6.6's connector to it, and makes it if it is missing. The chat service must be running in your region, with the UI beside it. Step 4 changes one setting on `documind-chat`, which makes a new revision, and moves all traffic to it. Step 5 needs you in a browser.

### Isolation, on the kit's own app

Eight callers against the kit's chat app, run on your machine, then a restart.

#### Definition

On your lane only one account can call the chat service from a shell, so the callers isolation is about cannot all be made there. You can run the kit's app on your machine instead, under FastAPI's `TestClient`, which runs it in-process with its own start-up and routes. Two things are stood in. The token check lets a bearer name alice, bob, carol, the outsider or nobody. The roster puts alice and bob in acme and carol in zeta. The model can answer only from the history it is sent: it recalls saffron if an earlier question in that history contains it. Everything else is the kit's: the request model, the door, the thread id, the LangChain brain and the checkpointer, in memory.

#### The code

#### Do it: the venv

#### Do it: eight callers

Alice's second turn found the word; her new session did not. Bob, in her tenant, used the same session name and reached `acme:bob@acme.example:lesson113`, another thread. Carol reached zeta's. The body that named zeta changed nothing: `ChatRequest` has no tenant field, so the key was dropped and the roster decided. The colon never reached the thread id, because the request model refused it with a 422. The roster refused the outsider (403), and the identity check refused the token that named nobody (401).

That left four threads, each under its own tenant and person. Then the app restarted, built a new memory checkpointer, and alice's word was gone. That is the failure step 4 must not show on your lane.

### A conversation across a redeploy

A word to two brains, a new revision of the chat service, and the word asked for again.

#### Definition

The cell gives the word to the LangChain brain and to the ADK brain, each in its own session. Then it redeploys the chat service: it changes one setting, `LESSON113_RESTART`, which makes a new revision, and moves all traffic to it. Every instance that served the first turns is replaced. Then it asks both brains for the word. It prints the serving revision before and after, and saves the sessions and the time of the redeploy for step 6.

#### The code

#### Do it

The revision changed, so every instance was new. The LangChain brain still had the word. The new instance opened its pool at start-up and read the thread from Cloud SQL, and the model was sent the whole conversation. This is the first half of the lesson's proof.

The ADK brain did not have it: its session was in the old instance's memory. With a minimum of zero instances, every quiet spell does the same to ADK's conversations.

### Another person finds nothing

You, through the UI, asking for a word you never gave.

#### Definition

From your shell, every call is `documind-ui-sa`. The other person on your lane is you. The UI forwards your IAP assertion, and the chat service takes your email from it. Open the UI, sign in, choose a brain other than direct in the sidebar, and ask for the word.

#### Do it

- Open that address, and sign in with the account the line names.

- In the sidebar, set Brain to `langchain`. It starts on `direct`, which does not reach the chat service.

- Ask: Which word did I ask you to remember?

An answer that has no word from you, and under it a caption beginning `brain: langchain`.

You asked as yourself, in a session the UI made for your browser, so your question reached `acme:` your email `:` that session. `documind-ui-sa`'s thread, with saffron in it, has a different key, and nothing in your request could name it. This is the second half of the proof: another person finds nothing. Had the UI let you type step 4's session name, you would still have reached a thread of your own, as bob did in step 3.

### The rows behind both

Step 4's sessions split at the redeploy, and each person's threads.

#### Definition

The cell connects as in lesson 6.6. For step 4's two sessions, it reads the checkpoints and when they were written, split at the time of the redeploy. Then it counts each person's threads: yours and `documind-ui-sa`'s.

#### Do it

The LangChain session has checkpoints on both sides of the redeploy, some written by the old revision and some by the new, in one thread. The ADK session has no rows at all. Your thread sits under your own email, beside `documind-ui-sa`'s. Two people, two sets of rows, one table.

### Why the properties hold, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- The store is outside the instance. Only a database survives a deploy, a scale-to-zero and an instance dying, which is why `cloudsql.tf` exists.

- The server builds the key. The tenant is looked up, never received. `agent.py` removed the fields rather than validating them, because a field that does not exist is stronger than a check a later edit can loosen.

- The door comes first. Who is asking and whether the roster lists them are settled before any brain runs, so a refused caller never reaches a thread.

- The colon is banned twice. The request model's pattern refuses it, and `thread_config()` checks again, so no part of the key can spill into the next.

- Each instance opens its own pool. The checkpointer is opened once, when an instance starts, so a new instance joins the same tables on its first request.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- ADK's conversations do not survive a restart. The image lacks SQLAlchemy, as lesson 6.6 found, so every redeploy and every scale-to-zero ends every ADK conversation.

- The memory checkpointer is accepted in production. `CHECKPOINT_DSN=memory` starts the service with a warning even under `DOCUMIND_PROFILE=gcp`. A mistaken setting would lose every conversation at every restart, with that one line as the only sign.

- A shared account is one person. Every caller with `documind-ui-sa`'s bearer token is the same person to the chat service: `make smoke-chat`, a notebook, an agent. Any of them reaches another's thread by using the same session name.

- A body that names a tenant is not refused. `ChatRequest` ignores keys it does not have. A client that believes it chose a tenant gets its own, with no error to say otherwise.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

`documind-chat` has a new revision, with one more setting, `LESSON113_RESTART`, and all traffic on it. The next `make deploy-services` replaces the service's settings and removes it. The chat service holds step 4's LangChain thread and your thread from the UI; ADK's session went with the old revision. `~/lesson113.json` holds step 4's sessions. Lesson 6.8 resumes a turn that was paused or cut off, from its checkpoint.

Netsetos GenAI on GCP · Module 6 Context and memory · Lesson 6.7 Verify restart recovery and session isolation · v5.0

Next: Lesson 6.8 Resume a paused or cut-off turn: checkpoint and resume.
