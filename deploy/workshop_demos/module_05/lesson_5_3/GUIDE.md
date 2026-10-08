# Lesson 5.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_5.3_MCP_Deploy_WIX.html`, reviewed at blob `84a7e098461d32a587731e9d8ffc358d0dd77573`. Learners read that page on the course site; this guide keeps its prose.

Lesson 5.2 ran the kit's MCP server on your machine. This lesson puts it behind Cloud Run and checks who gets through. Three doors stand in front of a tenant's documents. Cloud Run lets in only the accounts bound as invokers. The server accepts only a token minted for its own address, with an email in it. The roster decides which tenant's documents that email may read. Behind the doors, the server fetches from rag-api as its own account, which every golden roster lists. You read the door as the kit writes it down, deploy it with the kit's own target, and run the module's gate. Then you call once at each door, and read the two logs that show who asked and who was served.

- Three doors and a deputy

- The words: invoker, audience, roster, named tenant, deputy, caller graph, gate

- Before you run anything: set up the shell

- The door, as the kit writes it down

- Deploy, and read it back

- The gate: make smoke-mcp

- One call at each door, and both sides of the answer

- Why access is split this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn which door refuses which caller, what each refusal looks like, and why the server's roster check is the one that guards the tenants. Then you will prove it: `make smoke-mcp` green, the outsider refused when it names acme, and every door answering the caller it is there for.

### Three doors and a deputy

Who may knock, who is named, whose documents, and who fetches them.

The first door is Cloud Run's. `documind-mcp` is deployed with no unauthenticated calls, so Cloud Run checks every request's token before the server's code runs. With no token, or one it cannot verify for this address, the request never arrives. `roles/run.invoker` is bound on the service for three accounts only, per the kit's caller graph. `documind-ui-sa` is for the operators' smoke tests, and `documind-agent-sa` is the A2A peer. `documind-outsider-sa` is the eval gate's outsider, let in on purpose, so that its refusal comes from the roster and not from the network.

The second door is the server's token check. Cloud Run has proved the token was minted for the service. The server checks again that the audience is its own `SELF_URL`, and that the token carries a verified email. A token without an email names nobody, and a tool call that carries one is a tool error.

The third door is the roster. The email must be on the tenant's roster in Firestore. With no tenant named, the server takes the caller's own. A named tenant is accepted only if the roster already lists the caller on it. The outsider is on no roster, so when it names acme it is refused: another tenant's documents, refused by the roster.

Behind the doors, a deputy. The server then calls rag-api through the one `retrieve()`, as `documind-mcp-sa`, and does not pass on who asked. `make roster` puts `documind-mcp-sa` on all three golden tenants, so rag-api's own roster check always passes it. rag-api's row therefore names the deputy, not the person or agent who asked. The server's roster check is what keeps a caller out of another tenant's documents, and the server's own log line is the only record of who asked.

An office tower. The security desk lets in only people with a visitor pass issued for this building. Reception checks that the pass has a name on it. The floor's register checks that the company on that floor expects the visitor. Behind the desk, the tower's own runner fetches files from the records room. The records room sees the runner's badge, which opens every floor's shelves, and never the visitor's. So the floor register is what keeps a visitor away from another company's files, and the runner's logbook is the only place the visitor's name is written.

#### Which door stops it

Choose a caller, a tool and a tenant to name. The panel shows each door in turn, whether it let the call through, the answer, and what rag-api sees.

The 150 answers come from the kit's `server.py`, run on localhost at build time with the roster from `roster_plan`. Cloud Run's two statuses come from a local stand-in that refuses as Cloud Run does: 403 without a token, and 401 for a token minted for another address.

It shows the kit's rules on a stand-in lane. Your lane's documents, and any change you have made to a roster, decide your answers.

### The words: invoker, audience, roster, named tenant, deputy, caller graph, gate

Ten rows, each with the value it takes on your lane.

One distinction to hold: IAM decides who may reach the server, and the server decides whose documents they may read.

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

The shell, in the kit's folder, with `PROJECT`, `REGION`, `NUMBER`, `API` and `ME`, and fastmcp in the operator venv from lesson 5.2. Step 4 builds the MCP image with Cloud Build and deploys it, which takes a few minutes and makes a new revision of `documind-mcp`. Steps 5 and 6 make two retrievals.

### The door, as the kit writes it down

The deploy script's flags and invokers, and the rosters `make roster` writes.

#### Definition

The cell reads the deploy block of `commands/lesson-7.2.sh`. It shows the flags that set the first door, the environment that sets the second (`SELF_URL`), and the loop that binds the invokers. Then it runs `lane.py`'s `roster_plan`, the function `make roster` uses, to list the tenants each invoker may read. Nothing is called; this is the configuration as the kit writes it.

#### The code

#### Do it

Three invokers, three different rosters. `documind-ui-sa` may read all three golden tenants, `documind-agent-sa` acme alone, and the outsider none. The outsider may knock, but every tool that reads a tenant will refuse it. The last line is the deputy. `documind-mcp-sa` is on all three rosters, so whatever the server asks rag-api for, rag-api's roster check says yes. The server's own check is the one that matters.

### Deploy, and read it back

The kit's own build-and-deploy, then the service as Cloud Run holds it.

#### Definition

`make build deploy-services` builds the MCP image from the kit with Cloud Build, then runs `lesson-7.2.sh`'s deploy block: the `gcloud run deploy` with its flags, and the loop that binds the three invokers. It ends by making sure you may mint tokens as `documind-ui-sa` and the outsider. The second cell reads the service back: the revision serving, the account it runs as, its ingress, its `SELF_URL`, and the invokers bound on it now, compared with the script's three.

#### Do it: build and deploy

Cloud Build runs a build as the project's default build account, and the kit names no other: `cloudbuild.yaml` has no `serviceAccount`, and `make build` passes no `--service-account`. On a project made since mid-2024 that account is the Compute Engine default account, `NUMBER-compute@developer.gserviceaccount.com`. In an organization created on or after 3 May 2024 it is created without the Editor role Google used to give it. The build then cannot read its own source, the archive `gcloud builds submit` has just uploaded to the `documind-ai-YOUR-ID_cloudbuild` bucket, and stops at `could not resolve source` with a 403 naming that account.

This grants that account the three things this build does, once, as a project owner: read its source in that one bucket, push the image to the `documind` repository, and write its log lines (`cloudbuild.yaml` logs to Cloud Logging only). It does not grant Editor or `roles/cloudbuild.builds.builder`. Granted on the project, either one can read, write and delete every object in every bucket, the uploads bucket of customer documents included, and the Compute Engine default account is also what a VM or a Cloud Run service runs as when nobody names another.

Then run the build and deploy again. IAM applies a grant in about two minutes, sometimes seven or more, so a second 403 on the same object soon after is that wait, not a wrong grant. If the 403 names another account, set `BUILD_SA` to that one.

#### Do it: read it back

The service runs as `documind-mcp-sa` with ingress `all`: anyone can reach it, and the boundary is identity. `SELF_URL` is its own run.app address, the audience every token must carry. The invokers are the script's three. If yours says DIFFERENT, someone bound another account by hand. The script only ever adds bindings, so a redeploy does not remove it.

### The gate: make smoke-mcp

Health, tools, an answer, and the outsider refused by the roster.

#### Definition

`make smoke-mcp` is the module's gate for the MCP server. It mints a token as `documind-ui-sa` for the service's address, reads `/health` through Cloud Run, lists the tools, and asks `retrieve` the gratuity question for acme. Then it mints a token as the outsider and asks the same question, naming acme. It passes only if the roster refuses that, and not Cloud Run or the token check. The cell first notes the time, for step 6's logs.

#### Do it

Four passes: the first half of the proof. The last is the second half: another tenant refused. The outsider got through Cloud Run, because it is an invoker, and through the token check, because its token names it. Then the roster refused it: `documind-outsider-sa` is not on acme's roster. A refusal from Cloud Run would have proved only that the network is closed. This one proves the roster is enforced.

### One call at each door, and both sides of the answer

Five callers, one raw `tools/call` each, then the MCP server's log beside rag-api's.

#### Definition

The first cell sends one raw `tools/call` to `retrieve` for each of five callers, and prints which door answered:

- no token at all;

- a token `documind-ui-sa` minted for rag-api's address;

- a token minted without its email;

- the outsider, naming acme;

- `documind-ui-sa` naming zeta, a tenant it is on.

The second cell reads the two logs since step 5: the MCP server's line for each answered call, and rag-api's row for each retrieval it served.

#### The code

#### Do it: every door

#### Do it: both sides

The first two calls never reached the server. Cloud Run answered: 403 with no token, and 401 for a token minted for another address. The third reached the server and named nobody. The fourth named somebody on no roster. The fifth was answered, for zeta.

The logs show both sides of the two answered calls, the gate's and the fifth. The MCP server's line names the caller, `documind-ui-sa`. rag-api's row names `documind-mcp-sa`, for the same tenants. rag-api never learned who asked.

### Why access is split this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- The boundary is identity. With ingress `all` and a public run.app address, the network does not hide the server; IAM and the token do.

- Invokers per service, not per project. Since 12 September 2026, the caller graph binds `run.invoker` on each service for exactly its callers, and `check_authz.py` fails when the scripts and the graph disagree.

- The outsider is let in on purpose. The gate's refusal then comes from the roster, the check that protects tenants, and not from the network.

- The audience is checked twice. Cloud Run checks that the token was minted for the service, and the server checks its own address, so a token minted for another service cannot be replayed here.

- The deputy keeps rag-api simple. rag-api has a handful of callers and one roster. The MCP server does the per-caller check, then asks as itself.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- rag-api cannot tell who asked. The server calls rag-api as `documind-mcp-sa`, which is on every golden roster, and does not pass on who asked. rag-api's row names the deputy. The server's roster check is the only thing between a caller and another tenant's documents.

- The server logs only answered calls. The `mcp_call` line is written after the checks, so step 6's refusals left no line naming their caller.

- The deploy block does not build. `lesson-7.2.sh` deploys `mcp:$GIT_SHA` and never builds it, where `lesson-12.8.sh` builds its own image. After a new commit, `make deploy-services` on its own points Cloud Run at an image that does not exist.

- Bindings are only ever added. The script adds the three invokers and removes nothing. An account bound by hand survives every redeploy, and `check_authz.py` reads the scripts, not the live policy.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

`documind-mcp` has a new revision, built from your kit's commit, with the same three invokers. Two retrievals ran, for acme and zeta, and rag-api's rows for them name `documind-mcp-sa`. Lesson 5.4 opens the LangGraph brain, and lesson 10.6 later follows the A2A peer, `documind-agent-sa`, through this server to rag-api.

Netsetos GenAI on GCP · Module 5 MCP and agents · Lesson 5.3 Deploy MCP and verify authorized access · v5.0

Next: Lesson 5.4 Implement the main LangGraph workflow.
