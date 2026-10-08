# Lesson 9.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_9.1_Gateway_Routes_WIX.html`, reviewed at blob `30740fa186a22ed90c835763dc109fdeb2bf0409`. Learners read that page on the course site; this guide keeps its prose.

The gateway is one door in front of every model DocuMind can use: Gemini on the global endpoint, and the self-hosted models the next lessons deploy. It is a Cloud Run service behind IAM, and the caller's ID token is its only key. Every request passes a hook that decides whether its text may leave. Restricted text goes to the self-hosted model, with no fallback to Gemini, and confidential text is masked. Every completion carries a cost header, which the API writes on its usage row.

In this lesson you trace the hook's decisions offline, with the gateway image's own Presidio, and see which texts it re-routes and which it lets through. You see how the gateway calls a self-hosted backend with a token of its own. Then you deploy the gateway, run its smoke test, and send it three requests: one for its cost header, one PAN it re-routes, and the smoke test's PAN, which it does not.

- One door for every model

- The words: the gateway, the door, a route, a fallback, the sensitive route, the hook, the tiers, Presidio, the token proxy, the cost header

- Before you run anything: set up the shell

- The hook's decisions, traced

- The token the proxy sends

- The gateway, deployed and smoke-tested

- A PAN re-routed, and the cost header

- Why it works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn how the gateway decides who may call it, which model answers a request, and what that answer costs. You will learn how its classifier and hook decide whether text may leave, and where they fall short with the image's own Presidio. Then you will prove it on your lane: a PAN re-routed, and the cost header on a completion.

### One door for every model

IAM at the door, routes behind it, a hook in between, a token per backend, a price on every answer.

The door. The gateway is LiteLLM (`services/litellm`), a Cloud Run service like every other on the lane. `make deploy-gateway` deploys it with `--no-allow-unauthenticated`, and lets two accounts invoke it: the API's and the UI's. The caller's Google ID token is the key. There is no master key, because a master key would make every caller's ID token an invalid virtual key (`config.yaml`'s own words). The API reaches models through the gateway only when its `MODEL_BACKEND` is `gateway`; on your lane it is still `vertex`.

The routes. `config.yaml` names the model groups:

- Managed: `documind-general`, which is `gemini-3.6-flash` on the global endpoint, and `documind-reasoning`, which is `gemini-3.1-pro-preview`.

- Self-hosted: `documind-slm` and `documind-sensitive`, the small model on a Cloud Run GPU, which lesson 9.2 deploys.

- Optional: `documind-inference` (vLLM) and `documind-gke`, which lesson 9.3 inspects.

When a self-hosted backend is cold, scaled to zero or not deployed, the router hands the request down a chain of fallbacks that ends at Gemini. `documind-sensitive` has no fallback. Its point is that the text does not leave: a cold GPU means a slow answer or an error, never Gemini.

The hook. Before LiteLLM sends a request anywhere, a pre-call hook (`documind_router.py`) classifies all of its text, the question and any retrieved context, with `documind_classifier.py`. There are three tiers:

- RESTRICTED (a PAN, an Aadhaar number, an SSN, a card number): the request goes to `documind-sensitive`.

- CONFIDENTIAL (an email address or a phone number): Presidio masks every entity it finds, and the request goes to `documind-general`.

- PUBLIC: the request keeps the model it asked for.

RESTRICTED takes two layers: a pattern must match, and then Presidio, a PII detector, must confirm it with any entity it scores at 0.7 or more. `ROUTER_ENFORCE=0` is shadow mode, which classifies and logs but moves nothing.

The token proxy. LiteLLM reads a backend's key once, at startup, and a Cloud Run ID token lasts an hour. So the self-hosted routes point at a small proxy inside the gateway's container. It drops the caller's `Authorization` header and forwards each request with an ID token of its own for the backend's URL. That token is minted as the gateway's account, cached per backend, and replaced five minutes before the hour.

The cost header. Every completion carries `x-litellm-response-cost`: the answer's tokens at the per-token rates `config.yaml` gives the route that answered, a fallback included. When the API goes through the gateway, it writes that figure on its usage row.

A company's dispatch counter in Nariman Point. Every outgoing packet passes one counter, and you show your staff card to reach it; nobody holds a master pass. The clerk reads each label before choosing the courier. A label with an Aadhaar or PAN on it goes by the company's own van, never an outside courier, even when the van is late. A letter with an email address gets its personal details blacked out, then goes by the national courier. Everything else goes by the courier you asked for, and if a private courier is not running today, the national one takes it.

The van waits in another building, and the clerk carries the company's own pass there, renewed every hour; your card never leaves the counter. Every dispatch slip shows the charge. The catch is the clerk's rulebook: it knows American ID formats and not Indian ones, so a label with only a PAN on it goes out by the outside courier. And the black marker covers dates and figures too.

The counter is the gateway and the staff card is the ID token. The clerk is the hook, and the rulebook is Presidio. The company's van is the sensitive route, the national courier is Gemini, the pass is the token proxy's token, and the slip is the cost header.

#### Where would this request go?

Pick a request's text, the model it asks for, the shadow-mode switch, and whether the self-hosted model is deployed. The first box shows how the classifier reads the text. The second shows where the hook sends it, the chain of fallbacks, and what answers.

The patterns, the Presidio scores and the tiers are the kit's classifier's, computed with the gateway image's pins (Presidio 2.2.364 and `en_core_web_lg`) when this page was built. The routing is the kit's hook and `config.yaml`'s fallback chains, ported and compared with the kit's own on all 42 combinations.

It offers five texts, each classified when the page was built, because Presidio does not run in a browser. Step 3 runs the classifier itself, on any text you give it.

### The words: the gateway, the door, a route, a fallback, the sensitive route, the hook, the tiers, Presidio, the token proxy, the cost header

Ten rows, each with the value it takes on your lane.

One distinction to hold: the door decides who may call the gateway, and the hook decides where their text may go. The door is Cloud Run IAM, checked before LiteLLM sees the request. The hook runs inside LiteLLM, on the request's text.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION` and `NUMBER` set by the setup above.

- The checkout where `make up` ran. `make deploy-gateway` reads the gateway's database URL from Terraform's state; anywhere else it stops at `terraform output`. The database itself already exists, because Terraform declares it with the rest of the lane.

- About 750 MB for `~/gw-venv`. Step 3 installs the gateway image's Presidio and its 400 MB spaCy model once. Cloud Shell's home directory has room.

- No self-hosted model yet. Lesson 9.2 deploys it. Until then the sensitive route has no backend, which is how its missing fallback shows.

- What the lesson changes. It deploys `documind-gateway`, which scales to zero, stores its image in Artifact Registry, and lets two accounts invoke it. It also creates `~/gw-venv` and asks Gemini a handful of short questions.

### The hook's decisions, traced

The classifier's own test cases and four requests, run with the gateway image's Presidio. Offline.

#### Definition

The first cell makes a venv with the Presidio pins from the gateway's `requirements.txt`, and the spaCy model its `Dockerfile` downloads. The second imports the gateway's own classifier and hook, with LiteLLM's base class stood in, and prints three things:

- the recognizers Presidio loads for English;

- the classifier's own test cases, a list in `documind_classifier.py` that nothing runs;

- the hook's decision on four requests for `documind-general`, and what the last one would send to Gemini.

#### The code

#### Do it

- Presidio loads 17 recognizers, and none of them is Indian. There are American ones (SSN, ITIN, passport, driving licence, bank account) and none for a PAN or an Aadhaar number.

- 3 of the classifier's own five test cases fail. The Aadhaar number, the SSN and the PAN all come back PUBLIC. Their patterns match, but Presidio confirms nothing at 0.7, so the tier falls through to PUBLIC.

- The smoke test's own request, a bare PAN, is PUBLIC. It goes where it asked: `documind-general`, which is Gemini.

- The same PAN with a date is RESTRICTED. Presidio scored the date at 0.85, and the rule "any entity at 0.7" confirmed a pattern the date has nothing to do with. That request goes to `documind-sensitive`.

- An email address in the context makes a request CONFIDENTIAL, and the mask removes the answer. Every entity Presidio finds is replaced, whatever its score: the 60 days, the grade E3 (read as a US driving licence) and the file name. Gemini is asked for the notice period with the notice period taken out.

### The token the proxy sends

gcp_id_token.py with the metadata server stood in, and the headers the proxy drops. Offline.

#### Definition

The token proxy replaces the caller's credentials with the gateway's own:

It gets that token from `get_id_token()`, which keeps one token per backend:

The cell stands in the metadata server with a counter, moves a clock, and asks for tokens four times. Then it prints the headers the proxy drops.

#### Do it

- One token per backend. It is minted on the first call, reused for 55 minutes, and minted again five minutes before the hour. The vLLM engine's URL gets its own token; its `/v1` suffix is stripped first.

- The caller's token never reaches the backend. The proxy drops the `Authorization` header with the hop-by-hop ones, and adds a token minted as the gateway's account. The backend's own IAM then decides: each self-hosted service grants the gateway's account `run.invoker` when it is deployed.

### The gateway, deployed and smoke-tested

make deploy-gateway, then the kit's smoke test: the door, JSON, the cost header, the PAN and the fallback.

#### Definition

`make deploy-gateway` builds the image from `services/litellm` and deploys it behind IAM:

The first build downloads the 400 MB spaCy model into the image, so it takes several minutes. `make smoke-gateway` then runs six checks as the UI's account.

#### Do it

- The door works. With no token, Cloud Run answered 403 before LiteLLM saw anything. With the UI account's token, the gateway answered.

- `documind-general` answered in JSON, and the response carried the cost header.

- `documind-slm`'s backend is not deployed yet, so its fallback answered: Gemini.

- The PAN check passed, but read what it printed: served by `gemini-3.6-flash`. The check has two branches, and both pass:

Step 3 showed why the PAN went to Gemini.

### A PAN re-routed, and the cost header

Three requests for documind-general: no personal data, the smoke test's bare PAN, and a PAN with a date.

#### Definition

The cell mints the UI account's token for the gateway, as the smoke test does, and reads `config.yaml`'s rates. Then it sends three requests, and prints for each the status, the model that answered, the tokens and the cost header. When the API goes through the gateway, it prices the answer from that header:

#### Do it

- The cost header on a completion. `x-litellm-response-cost` was 0.0001665 USD for 11 tokens in and 20 out: `config.yaml`'s `documind-general` rates times the usage. On your lane the token counts are Gemini's own. That is the first proof.

- The bare PAN was answered by Gemini: the hook did not re-route it (step 3).

- The PAN with a date was re-routed. The hook sent it to `documind-sensitive`, whose backend is not deployed until lesson 9.2 and which has no fallback. So the gateway returned an error, not a Gemini answer. That is the second proof: a PAN re-routed. The stand-in's error is a 500; on your lane it is whatever LiteLLM returns for a backend that does not exist. After lesson 9.2, the same request is answered by the small model.

### Why it works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- IAM is the door. The gateway is behind IAM like every service on the lane. A master key would make every caller's ID token an invalid virtual key, so there is none.

- One place decides what may leave. Presidio lives in the gateway and only there, so the decision "may this text leave our perimeter" is made once, where every route passes.

- The sensitive route has no fallback. A cold GPU means a slow answer, not a leak.

- Shadow mode first. `ROUTER_ENFORCE=0` classifies and logs every request and changes nothing: the safe rollout for a classifier that moves traffic.

- The proxy mints its own tokens. A pasted token expires at 3 a.m., on a path nobody is watching.

- The gateway prices what it served, fallbacks included, and the API writes that price on its usage row.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does. The Presidio facts come from the gateway image's own pins, run when this page was built.

- A bare PAN or Aadhaar number leaves. Presidio 2.2.364 loads no Indian recognizer, and the classifier's second layer needs some entity scored at 0.7 or more; the pattern's own match does not count. A PAN alone is PUBLIC and goes to Gemini. The same PAN beside a date or a name is RESTRICTED.

- The classifier's test cases are a list nothing runs. Three of its five fail with the image's own pins.

- The smoke test's PAN check cannot fail. Both branches pass it, so `make smoke-gateway` is green while the PAN goes to Gemini.

- The mask removes the answer. A CONFIDENTIAL request has every entity Presidio finds replaced, whatever its score: durations and dates, grade codes, file names. The notice period is masked out of the very context that answers it.

- The tag budgets bind nothing. `config.yaml` sets budgets for `tenant-acme` and `tenant-enterprise`. The API sends the tenant as metadata, never as a tag, and the lane has no tenant called enterprise.

- `dlp_audit.py` is in the image, and nothing calls it. The gateway's `dlp.user` role serves an audit that never runs.

- The database bills without the gateway. Terraform declares the Cloud SQL instance with the rest of the lane, so it runs by the hour whether `make deploy-gateway` ever does or not.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

`documind-gateway` runs on Cloud Run, scaled to zero between calls, and the API's and the UI's accounts may invoke it. Its image is in Artifact Registry, `~/gw-venv` holds the image's Presidio, and Gemini answered a handful of short questions. The API still answers through Vertex AI (`MODEL_BACKEND=vertex`). Lesson 9.2 deploys the self-hosted model behind the sensitive route, and puts the API behind the gateway on a candidate revision.

Netsetos GenAI on GCP · Module 9 Serving · Lesson 9.1 Trace and authorize gateway routes · v5.0

Next: Lesson 9.2 Serve a supplied or stock model using Ollama.
