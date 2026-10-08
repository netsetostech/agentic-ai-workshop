# Lesson 12.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_12.2_Managed_Tuning_WIX.html`, reviewed at blob `8d2fab91ee14935e4fdd422af3798cf76a95b6f7`. Learners read that page on the course site; this guide keeps its prose.

Lesson 12.1 froze a training file. Before Vertex AI trains on it, you check that it is the file the manifest describes, in the shape the trainer reads. You also check that it carries no personal data and no golden row, and that its tenant lets its text leave India. Only then do you start the job. It runs in `us-central1`, bills per training token, and returns a tuned model with an endpoint that answers from the location its path names.

In this lesson you run the kit's two self-tests and validate v2 from the datasets bucket. You submit the tuning job with a name that says v2, and wait for it. Then you call the endpoint once where its path says it lives, and twice where it does not.

- What a tuning job needs, does and returns

- The words: managed tuning, the adapter, an epoch, training tokens, config_for, the job, its states, the tuned model, the endpoint, _endpoint_location

- Before you run anything: set up the shell

- The checks that run before the spend

- The frozen file, validated

- The job, submitted

- The endpoint, and where it answers

- Optional: v3, validated and tuned with its validation file

- Why it works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what a managed tuning job needs, what it bills and what it hands back. You will learn which failures the kit catches for free before you submit, and which checks it leaves to you. Then you will prove it on your lane: the tuning job's id, and the endpoint's path with its location.

### What a tuning job needs, does and returns

A file, a base and a config in; an adapter trained in the US; an endpoint out, somewhere else.

What the job needs. Three things:

- A training file in Cloud Storage. JSON Lines: each line a system instruction and a conversation, a user turn and then a model turn. That is Google's format, and `make trainset` wrote v2 in it.

- A base Vertex AI can tune. Of the Gemini 3 models that is `gemini-3.5-flash` or `gemini-3.1-flash-lite`, not `gemini-3.6-flash`, the model you serve.

- A config: the number of epochs, the adapter size and a display name.

`tune.py`'s `config_for` refuses a base that cannot be tuned, and an adapter size the SDK cannot spell, before anything is submitted. The kit learned the second on its first live run (F37): the SDK spells the size as a word, and a bare 4 failed at submission.

What the job does. It leaves the base's weights as they are and trains a small adapter beside them, a LoRA adapter. The adapter size is its rank, which sets how many parameters it can learn. The job makes three passes over the rows, three epochs, and bills training tokens: every token in the file, times the epochs. Google's price to tune `gemini-3.1-flash-lite` is USD 3.00 a million training tokens.

The job runs where you ask. For both tunable Gemini 3 bases, Google tunes only in `us-central1` and `europe-west4`, and the kit asks `us-central1`. Google keeps the transformed dataset and the tuned model in the job's region, and may run the computation in other US or EU regions.

What it returns. A job, named by a path that is also its id: `projects/NUMBER/locations/us-central1/tuningJobs/...`. The job queues, runs, then succeeds, fails or is cancelled, and `tune.py --poll` prints its state once a minute. When it succeeds, it names a tuned model and the endpoint that serves it.

For Gemini 3, Google serves tuned models only from the `us` and `eu` multi-region endpoints, never from the region the job ran in. The kit's first live job put its endpoint in `us` while the API assumed `us-central1` (F41). So the endpoint's path names its location, and the generator calls it there unless `GENERATOR_LOCATION` says otherwise. `tune.py`'s own docstring still says the endpoint is regional.

Once it exists, the endpoint is billed per answer. From Gemini 3 onward, Google prices a tuned endpoint's predictions at 1.5 times the base's; `cost.py` still prices them at the base rate (lesson 12.1).

Five checks before the spend. The job reads the file by its URI, and checks none of the rules that make it defensible. So you validate the bytes the job will read:

- The bytes. They are the ones the manifest's SHA-256 records.

- The shape. Every row is a system instruction, one user turn and one model turn, text only. The chat file says the same, and every target parses as ModelDraft.

- The test set. `exclude_golden` drops none of the rows.

- Personal data. DLP scans the questions and answers, which `make trainset` scanned, and the chunks, which it did not. Weights cannot be filtered per tenant afterwards.

- Residency. The tenant's `data_region`, through the kit's own `permits()`: `any` may be held in `us-central1`, and `in` may not.

Then the size: the training tokens the job will bill, and the longest row against Google's limit of 131,072 tokens an example.

A ready-made kurta sent for alteration. The tailoring unit alters it; it does not sew a new one. The tailor takes in a few seams without re-cutting the cloth, over three fittings, and charges for every measurement worked at every fitting. At the counter, an order for a fabric they cannot alter, or a seam allowance they do not stock, is turned away before any cutting, free.

Before you hand it over, you check the measurement sheet yourself. It is the sheet you signed, written on the tailor's form, with nobody else's details on it. The unit is in another city, so your family's rule must also let the cloth leave town. When the work is done, the kurta waits at a showroom somewhere else again, and the pickup slip names it. Take the slip back to the unit and they tell you it is not there.

The kurta is the base model, the seams are the adapter and the fittings are the epochs. The charge per measurement is the training token, and the counter is `config_for`. The sheet checks are the validation, and the family's rule is `data_region`. The unit is `us-central1`, the showroom is the `us` multi-region, and the pickup slip is the endpoint's path.

#### Submit a job, then serve its endpoint

Set a tuning config and see what `tune.py` does with it before anything is sent, what the job would bill for this page's v2, and what the tuned model would be called. Then pick a `GENERATOR_MODEL` and a `GENERATOR_LOCATION`, and see which client the generator builds and whether that location answers.

The rules are the kit's: `tune.config_for`, and `generator._client_for` with `_endpoint_location`, ported and compared with the kit's own functions on all 225 combinations. The rest is Google's, checked on its pages on 24 September 2026: USD 3.00 a million training tokens for `gemini-3.1-flash-lite` and 10.00 for `gemini-3.5-flash`; adapter sizes 1, 2, 4, 8 and 16; and a tuned Gemini 3 endpoint answering only from its multi-region. The tokens are this page's v2, by the kit's estimate.

It follows one config and one setting, and submits nothing. It cannot tell whether your project has room for a job today: Google gives every project a quota of at least one concurrent tuning job, shared across all regions.

### The words: managed tuning, the adapter, an epoch, training tokens, config_for, the job, its states, the tuned model, the endpoint, _endpoint_location

Ten rows, each with the value it takes on your lane.

One distinction to hold: the job runs in a region, and the endpoint answers from a location. The job's path says `us-central1` and the endpoint's says `us`. Ask for the endpoint anywhere else, and it is not found.

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

You need the shell in the kit's folder, with `PROJECT`, `REGION`, `API` and `ME` set by the setup above, and lesson 12.1's v2.

- Lesson 12.1's frozen file. Step 4 reads v2's three files from the datasets bucket, the copy the job will read.

- The clients. `google-genai` and `google-cloud-dlp`, which 12.1's step 5 installed at the ingest image's pins. `tune.py` uses `google-genai`'s tunings.

- Room for one job. Google's quota counts concurrent tuning jobs, at least one a project. If another job is running, yours may have to wait until it ends.

- What the lesson changes. It runs one tuning job, billed once, about Rs 156. That leaves a tuned model and its endpoint in the `us` multi-region, which lesson 12.3 uses. It writes `~/tune172.log` and `~/poll172.log`.

### The checks that run before the spend

The two self-tests, config_for's refusals, and where the generator would call an endpoint. Offline.

#### Definition

The cell runs `make_trainset.py`'s and `tune.py`'s self-tests. Then it calls `tune.config_for` three times: with the served model, with a rank the SDK cannot spell, and with a rank it can. It prints `make tune`'s own defaults. Last, it lifts `_endpoint_location` out of `generator.py` and asks where an endpoint would be called, with and without `GENERATOR_LOCATION`.

#### The code

#### Do it

- Two refusals, both free. `gemini-3.6-flash` is not in `TUNABLE`, and 3 is not a rank. Both fail before the dataset is read or anything is billed.

- Rank 32 passes. The SDK can spell it, so `config_for` accepts it. Google's page lists 1, 2, 4, 8 and 16 for both tunable Gemini 3 bases: the check follows the SDK's list, not Google's.

- `make tune`'s defaults name the model `documind-sft-v1`. The display name is a flag with a default, and `make tune` passes none, so a v2 job would be called v1. Step 5 passes `--display-name documind-sft-v2`.

- An endpoint is called where its path says, unless `GENERATOR_LOCATION` overrides it.

### The frozen file, validated

The bytes the job will read, held to the manifest, the four rules, DLP and the tenant's data region.

#### Definition

The cell reads v2 from the datasets bucket, the copy `make tune` names, and runs the five checks from step 1, in order. Then it estimates the bill: the kit's own token estimate, characters divided by four, times `make tune`'s three epochs, at Google's price. The residency check is the kit's own rule:

#### Do it

- The bytes are the manifest's, and every row is in the shape Vertex AI reads. The chat file says the same, row by row, and every target parses.

- The golden set drops none, and the scan `make trainset` ran finds nothing. Both rules ran when the file was written; this is the file checked again, as the job will read it.

- The chunks carry what `make trainset` never scanned. On the stand-in, DLP's email pattern flags the CGST Act's front matter, which prints a public helpdesk address. Each finding names a row and an info type, never the value. Read the chunks it names: a helpdesk address printed in an Act is public, but a person's phone number would call for a new version without that row. The rule is drop, never rewrite.

- acme's `data_region` is `any`, so its rows may be held in `us-central1`. An `in` tenant's rows may not, and nothing in the kit asks (step 8).

- The bill: about 610,353 training tokens, about Rs 156. The estimate divides characters by four; Google counts real tokens. The longest row, about 863 tokens, is far inside Google's limit.

### The job, submitted

make tune with a name that says v2, returning at once with the job's id.

#### Definition

`make tune` runs `tune.py` on the frozen file, named by its URI:

The cell passes three things. `VERSION=v2`, because the recipe reads v1 otherwise (lesson 12.1). `--display-name documind-sft-v2`, because the default says v1. And `--no-wait`, so that `tune.py` prints the job's name and returns while the job runs on Google's side. `launch()` builds a client in `us-central1` and hands the job the file's URI:

The cell keeps the job's name in `~/tune172.log` and in `JOB`.

#### Do it

- make echoed its recipe with `VERSION` unexpanded. The shell read `VERSION=v2`, and `tune.py` printed the dataset it submitted: `documind_sft_v2.vertex.jsonl`.

- The job's name is its id, `projects/NUMBER/locations/us-central1/tuningJobs/...`, and it is in `~/tune172.log`. That is the first proof: the tuning job id.

- This was the billed act. The job trains, and bills, from here, whatever happens to your shell.

### The endpoint, and where it answers

The poll to the end, the endpoint's path with its location, then one call where the path says and two where it does not.

#### Definition

The first cell polls the job once a minute until it ends. The poll only reads, so it costs nothing, and after a disconnect it is safe to run again: it takes the job from step 5's log. When the job succeeds, `tune.py` prints:

The cell keeps the endpoint in `~/poll172.log` and in `ENDPOINT`.

The second cell asks the endpoint one question the way the generator would. It sends `SYSTEM`, one source under its header and the question, with `generator._call`'s settings: ModelDraft's schema, 2,048 tokens and thinking at LOW. The chunk is not one the rows were written from, and the question is not a golden one. The cell asks in three places: `us-central1`, the job's region; `global`, where the served model answers; and the location the generator would use, from the path.

- The job queued, ran and succeeded. It named a tuned model and an endpoint in `us`, not in the region it ran in. That is the second proof: the endpoint's path with its location.

- `us-central1` and `global` answered 404, and the path's location answered. The generator reads the same segment of the path, so the API will call the endpoint where it answers.

- The answer is a ModelDraft, the shape the rows taught. Count its `[N]` marks: lesson 12.1 found the training targets carry none. The stand-in answers the way the rows are written; your endpoint writes its own answer, and lesson 12.3 compares it with the served model's.

- The price line prints two numbers: Google's, at 1.5 times flash-lite, and what `cost.py` would log.

### Optional: v3, validated and tuned with its validation file

If you built lesson 12.1's v3: the five checks on the served shape, make tune with --validation, and the poll to a second endpoint.

Lesson 12.1's step 7 wrote v3: the prompt the generator really sends, the house style, a Hinglish twin for every second chunk, and a validation file. This step tunes a second model on it, next to the first. The first job and its endpoint do not change, and lesson 12.3's step 7 serves this one.

#### What is different about v3

- The shape. A v3 row has no system instruction. Its one user turn is the prompt the generator sends, with `SYSTEM` inside it, so the model trains on exactly what it will be served. A system instruction is optional in Vertex AI's tuning format.

- The checks read more. The golden check reads the rows index, which names the chunk behind every row and every chunk beside it in the prompt. DLP reads every prompt, and so every chunk.

- The validation file. `--validation` hands the job `documind_sft_v3.validation.vertex.jsonl`: 40 rows from one chunk in ten, which the job scores as it trains and never trains on. A validation loss that climbs while the training loss falls means the model is memorising its rows, not learning the habit. Google recommends a validation set, and `tune.py` has always taken one. v3 is the first file that comes with one.

- The size. With three sources in every prompt, v3 is about 2.7 times v2's tokens: about 551,632 an epoch, or about Rs 422 for three epochs. Expect the job to take longer than step 6's.

#### Do it

Then submit the job with a name that says v3 and the validation file, and return at once:

Then wait for it. The poll only reads, so after a disconnect it is safe to run again:

- v3 passed the checks the plain file needs, and more. Every row is the served prompt. No row and no chunk in a prompt is golden evidence, and DLP found nothing in any chunk, because `make trainset` had already dropped what it found.

- The job took the validation file. `make` echoes it in `TUNE_ARGS`, and the job scores it as it trains. The Vertex AI console's page for the job charts its loss beside the training loss.

- A second endpoint, in `us` like the first. `~/poll172v3.log` holds it, and `ENDPOINT_V3` holds it in this shell. It is billed only when it answers.

### Why it works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- Check before you spend. A base or a rank the service refuses is refused at submission, after the file is written, uploaded and paid for. `config_for` refuses it first, for nothing, and says why (F37).

- Tuning is an explicit act. It bills per training token, and nothing else on the lane starts it.

- Personal data and residency are checked before the job, not after. Weights cannot be filtered per tenant afterwards.

- A regional job, a multi-region endpoint: the path knows. The generator reads the location from the endpoint's path (F41), and `GENERATOR_LOCATION` overrides it without a code change.

- A tuned model is a setting. `GENERATOR_MODEL` names the endpoint and `RAG_MODEL_BASE` names its base, for pricing. Lesson 12.3 puts both on a candidate revision that takes no traffic.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does. Google's figures were checked on its pages on 24 September 2026.

- Nothing checks the file before the job. `tune.py` passes the file's URI and reads neither the manifest nor the bytes. The job trains on whatever the object holds when it starts. Step 4 is that check, and it lives on this page.

- Nothing checks residency. `make trainset` takes any `TENANT`, and `tune.py` submits to `us-central1`; neither reads `tenant_settings`. Google tunes these bases only in the US or the EU, so an `in` tenant's text would leave India. globex's policy is `in`, and `make trainset TENANT=globex` would write 118 of its chunks, its copies of the DPDP and IT Acts, into a file `make tune` would send.

- No validation split by default. Google strongly recommends a validation dataset. `tune.py` accepts `--validation`, but the plain `make trainset` writes none and `make tune` passes none, so a v2 job reports its training metrics only. v3 writes one, and step 7 passes it by hand.

- The display name says v1, whatever you tune. `--display-name` defaults to `documind-sft-v1`, and `make tune` passes none.

- The rank check is the SDK's, not Google's. `config_for` accepts 32, which Google's page does not list for either tunable Gemini 3 base.

- The kit prices a tuned endpoint at its base rate. `cost.py` bills an endpoint path at `RAG_MODEL_BASE`'s price, where Google's page says 1.5 times. The usage rows, `make usage` and `tenant_daily` would count a tuned model's answers at two thirds of their price.

- Nothing records what produced the endpoint. `tune.py` prints the job and the endpoint once and writes nothing down. `--poll` prints `RAG_MODEL_BASE` from its own default, not from the job's base. This page's two log files are the only record.

### Verify it yourself: the checklist

Nine checks, each one block above, each with the value that proves it on your lane. The ninth is for step 7, if you ran it.

Your project has one finished tuning job in `us-central1`, billed once. It has a tuned model and its endpoint in the `us` multi-region, billed only when the endpoint answers. `~/tune172.log` holds the job, `~/poll172.log` holds the endpoint, and `ENDPOINT` holds it in this shell. v2 and the datasets bucket are as lesson 12.1 left them. Lesson 12.3 serves the endpoint on a candidate revision with no traffic, with `make candidate PROJECT="$PROJECT" GENERATOR_MODEL="$ENDPOINT" RAG_MODEL_BASE=gemini-3.1-flash-lite`, and compares it with the served model. If you ran step 7, there is a second job and a second endpoint, with `~/tune172v3.log` and `~/poll172v3.log`, and lesson 12.3's step 7 serves that one.

Netsetos GenAI on GCP · Module 12 Tuning · Lesson 12.2 Validate sanitized datasets and run managed tuning · v5.0

Next: Lesson 12.3 Compare the tuned candidate with an uncontaminated baseline.
