# Lesson 9.4: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_9.4_Compare_Shutdown_WIX.html`, reviewed at blob `6279d8ef22f2b880414191dd9de3f5b9b4db124f`. Learners read that page on the course site; this guide keeps its prose.

The chapter ends with two questions a production team asks before it keeps a self-hosted model. Is the small model good enough, and at what price? And when the day is over, is the GPU really off? The kit answers the first with `make compare`, a table of four numbers a backend. It answers the second with `make off`, which lowers four floors to zero.

In this lesson you read what the table measures and what it cannot see. Then you run the kit's own comparison with a recorder beside it, which keeps what the table drops: the route each row asked for, the model that actually answered, and the price the gateway charged. Last, you switch the lane off and prove it from the instance count Google keeps, not from the floor.

- A table you can trust, and a GPU you can prove is off

- The words: make compare, groundedness, citation precision, p95, Rs per 1k, a rate, the recorder, make off, a floor, instance_count

- Before you run anything: set up the shell

- The table's maths, read

- The comparison, with the actual backends

- Everything off

- Zero GPU instances

- Why it works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what `make compare` measures, where its context comes from, and why a row can be scored under the wrong model's name. You will learn why a floor of zero is not zero instances. Then you will prove it on your lane: the comparison table with the model behind every row, and zero GPU instances.

### A table you can trust, and a GPU you can prove is off

What the comparison measures, what a row cannot see, the small model's rupees, and what "off" means for a GPU.

The comparison. `make compare` takes the first 20 golden questions and asks each of them of every backend it is given, through the gateway: `documind-general` and `documind-slm` by default. For each question it retrieves once and hands every backend the same context, so that the only variable between rows is the model. Each answer comes back as JSON, and the script prints four numbers a backend:

- Groundedness: the answerable rows it answered with every `must_contain` phrase.

- Citation precision: the cited chunks the golden set expects, over all the chunks it cited.

- p95 latency: the round trip to the gateway; the number a dashboard alerts on.

- Rs per 1k queries: a row's mean cost, times a thousand.

Where the context comes from. "Retrieves once" means asking the API. `shared/documind_tools.retrieve()` posts the question to `/v1/query`, the live revision answers it with Gemini, and the comparison keeps that answer's citations. What each backend receives is those citations' quotes: the words Gemini chose. So the small model is judged on restating Gemini's evidence, not on reading the retrieved chunks.

What a row records. A row is labelled with the route it asked for, and priced at the script's own rate for that route. It keeps the answer and the token counts, but neither the model that answered nor the gateway's cost header.

- When the gateway moves a request (the hook re-routing RESTRICTED text, or a fallback when a backend fails), the row still carries the route's name and price.

- The vLLM route is the plain case. With no vLLM service deployed, `documind-inference` is answered by its fallback, the small model. The script, which has no price for that route, charges it at Gemini's rates.

The small model's rupees are a rate. The script derives 20.50 USD a million tokens from the L4's Rs 86,904 a month over about 50 million tokens. The bill is the GPU's hour, Rs 120.78 of it. At another volume the real price of a question can be far above or below the rate; the panel below shows how far.

Shutdown. `make off` lowers the floors: min-instances 0 on the small model, the vLLM service, the gateway and the UI. It also removes the GKE workload, then prints each floor. Three more controls sit around it: the nightly job does the same at 23:00 IST, an alarm fires after two hours of any GPU instance, and `make gpu-cap` caps the L4 quota. But a floor is not a count. An idle GPU instance may live up to 10 minutes after its last request, billed, whatever the floor says. So zero GPU instances is a measurement: Cloud Monitoring's `instance_count`, read after the idle window.

A caterer's tasting in Hyderabad, and the gas meter at closing time. The caterer tries a cheaper cook against the head cook on twenty dishes. Each plate goes out with a slip naming the cook it was ordered from, priced from the menu by that name. If the new cook was busy and the head cook covered, the slip still names the new cook, at his price. And both cooks are handed the ingredients the head cook picked for his own version of the dish.

At closing, the manager sets the minimum staff to nobody and goes home. The burners stay lit until the last cook leaves, up to ten minutes later, and the gas is paid for. The only proof the kitchen is off is the meter.

The tasting is `make compare`, and the slip is the row's label and price. Covering is the gateway's fallback or re-route, and the head cook's ingredients are the quotes from the API's answer. The minimum staff is min-instances, the burners are the GPU instance, and the meter is `instance_count`.

#### The table's rupees, and the bill's

The table prices the small model at its rate, but the bill is the GPU's hour. Pick a volume, the tokens in each question and answer, the hours your traffic spans and the days. The boxes show the table's rupees per 1,000 questions, the bill's, and Gemini's for the same tokens.

The rate and Gemini's prices are the script's own table, which matches `config.yaml` for these two routes. The hour is Google's price for the L4 shape `make deploy-slm` deploys in `us-central1`, and the 10 idle minutes are Cloud Run's limit for a GPU instance. The sums are compared with a Python version on all 96 combinations.

It assumes one instance keeps up with the traffic (the service allows one, four requests at a time), and that the traffic fills its window with no idle gaps. It prices the small model's instance only: not the gateway or the API around it.

### The words: make compare, groundedness, citation precision, p95, Rs per 1k, a rate, the recorder, make off, a floor, instance_count

Ten rows, each with the value it takes on your lane.

One distinction to hold: a floor is a setting, and an instance count is a fact. `make off` changes the setting. Only the count, read after the idle window, says the GPU stopped.

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

- The gateway from lesson 9.1, the small model from lesson 9.2, and the API answering. The comparison asks the API for each question's context.

- The kit's Python, with requests and google-auth, and credentials that can act as the UI's account. The comparison mints its tokens the way `make compare` does.

- About five minutes for the comparison, and ten more before the zero check.

- What it costs. The comparison asks for 80 answers: 20 from the API, which uses Gemini, 20 from `documind-general`, and 40 from the small model, on its own route and on the vLLM route's fallback. The GPU wakes and bills its instance's whole life: the cold start, the answers, and up to 10 idle minutes. At Rs 120.78 an hour that is a few tens of rupees.

- What it changes. It writes `compare.csv` in the kit's folder. `make off` sets four floors to 0. The GPU services' are 0 already; the UI's is set to 0 too, whatever it was, so its next visitor may wait for a cold start.

### The table's maths, read

The script's own check of its sums, then what a row reads, where its context comes from, and how it is priced. No network.

#### Definition

For each question, `live()` retrieves once, then asks every backend and writes one row each:

Each backend gets the route's name and a context built from the citations' quotes:

The citations come from the API's own answer, and a failed request becomes an empty list:

The first cell is the script's own check of its sums, on a fixture. The second reads the script, the tools module and `config.yaml`, and prints what a row can and cannot see.

#### Do it

- The sums check themselves. Refusal rows stay out of groundedness, precision counts cited chunks, p95 is a sorted row, and the rupees are the mean cost times a thousand.

- Every backend reads what Gemini chose to quote. The context is the quotes of the API's answer. If that answer takes more than 20 seconds, the row's context is empty and every backend refuses it, so the table shows a model failure where the API was only slow.

- A row reads neither the model that answered nor the gateway's cost header. Its name and its price are the route's.

- Three of `config.yaml`'s six routes have no price in the script. They fall to `documind-general`'s: `documind-reasoning` (Gemini Pro, 2.00 and 12.00), `documind-sensitive` (the small model, 20.50) and `documind-inference` (6.80).

- p95 on 20 rows is the 19th sorted row. The slowest row, which for a model that sleeps is its cold start, never shows.

### The comparison, with the actual backends

make compare's own pass on three routes, the vLLM route included, with a recorder that keeps what the table drops.

#### Definition

`make compare` sets up the gateway, a token for it and the API, then runs the script twice: once for the rows, once for the table.

The cell sets the same environment and runs the same functions: `live()` writes `compare.csv`, and `summarise()` and `print_summary()` print the table. It adds one thing, a recorder wrapped around `requests.post`, which keeps each gateway reply's model and cost header. It asks three routes: the two defaults, and `documind-inference`, the vLLM route lesson 9.3 inspected.

#### Do it

- The comparison table. That is the first proof. Gemini grounded all 20 rows and the small model 17: the stand-in gives a partial answer on lk-02, refuses lk-08, and states half of the join jn-03. Your rows are your lane's. Citation precision is 1.000 for both, because every context holds only chunks the golden set expects.

- `documind-inference` was the small model on every row, not vLLM. No vLLM service exists, so its fallback answered. The table shows the small model's groundedness under vLLM's name, and prices it at Gemini's rates: Rs 0.77 for the 20 rows, where the gateway charged Rs 5.26.

- For the other two routes, the model that answered was the route's own, and the two prices agree. On your lane, read those lines first. A row whose model differs from its route was moved by the hook or by a fallback, and the table scored it under the wrong name.

- The cold start hid. The slowest small-model row took 55.7 s, and the table's p95 is 3.1 s.

- The rupees per 1,000 questions: Rs 38.69 for Gemini and Rs 262.77 for the small model, at its rate. The panel above shows what the bill would be.

### Everything off

make off: four floors to zero, the GKE workload removed, and the floors it prints.

#### Definition

`make off` runs each switch, and carries on past one that fails, such as the vLLM service that does not exist:

Then it prints each service's floor: the min-instances annotation on its revision template, or `absent` for a service that does not exist.

#### Do it

- Four floors read 0, or absent for the vLLM service. The GKE workload was removed (the lab cluster had none), and the lab cluster stays until `make down`.

- The small model's floor was 0 already: `make deploy-slm` set it. A floor of 0 means Cloud Run may stop the instance, not that it has.

- The instance the comparison woke is still up, and billing, until its idle window ends.

### Zero GPU instances

Cloud Monitoring's instance_count for each service, read at least 10 minutes after make off.

#### Definition

The kit reads an instance count in one place, the two-hour alarm:

The cell asks Cloud Monitoring for the same gauge directly, over the last 45 minutes: one point a minute per service, summed over active and idle instances. It prints the last minute each service had an instance. A GPU service with an instance in the last three minutes is still up; a sample can take two minutes to show. Wait at least 10 minutes after `make off` before you run it.

#### Do it

- Zero GPU instances. That is the second proof: no GPU service had an instance in the last three minutes.

- The small model's last instance was at 10:13, about nine minutes after its last answer. That was the idle window, billed at Rs 120.78 an hour while the floor said 0. The stand-in's times are illustrations; yours are your lane's.

- The gateway stopped at 10:09. It runs on CPU, and its bill ran by request.

- Neither backstop would have acted. The alarm waits two hours, and the nightly job would have changed nothing, because every floor was already 0.

- This completes the chapter's gate: `make smoke-gateway` in lesson 9.1, `make smoke-slm` in lesson 9.2, and zero GPU instances here.

### Why it works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- One retrieval for every backend, so that the only variable between rows is the model.

- p95, not the mean: the number a dashboard alerts on.

- The small model's rupees are a rate, and the script says so. Idle time is the variable.

- `make off` is four switches in one, then the lines that prove it. The nightly job makes a forgotten GPU cost an evening, not a month.

- The alarm reads the instance count, not the floor: two hours above zero.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does.

- A row names the route, not the model that answered. Its price comes from the script's own table, and the gateway's reply and cost header are never read. A row the hook or a fallback moved is scored and priced under the wrong name.

- The context is Gemini's quotes. `retrieve()` asks the API for its answer, and the comparison keeps its citations' quotes. A question Gemini refused gives every backend an empty context.

- A slow API becomes a failed model. After 20 seconds `retrieve()` returns no citations and the row's context is empty, and only a log line says so.

- Three routes have no price in the script. `documind-reasoning`, `documind-sensitive` and `documind-inference` fall to `documind-general`'s rates.

- The table never scores a refusal. Groundedness leaves out the rows the documents cannot answer, and the first 20 golden rows are all answerable. So a backend that answers everything scores as well as one that refuses correctly.

- p95 on 20 rows hides a cold start. It is the 19th sorted row.

- `make off` prints floors, not instances. Nothing but the two-hour alarm reads an instance count.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

`compare.csv` holds the comparison's 60 rows. Every floor is 0, and the GKE workload is gone; the lab cluster remains until `make down`. No GPU instance is running. That ends Module 9: the gateway routes and authorizes, the small model serves behind it, and the lane can prove it is off. Module 10 turns to agent patterns, starting with where an agent reasons.

Netsetos GenAI on GCP · Module 9 Serving · Lesson 9.4 Compare actual backends and verify shutdown behavior · v5.0

Next: Lesson 10.1 Choose where the agent reasons: observe-think-act and ReAct.
