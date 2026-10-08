# Lesson 9.2: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_9.2_Ollama_SLM_WIX.html`, reviewed at blob `ef4d07a96774afec01f7a333d643d470b90ee1c3`. Learners read that page on the course site; this guide keeps its prose.

Lesson 9.1's sensitive route has nowhere to go until a model runs behind it. The kit serves one with Ollama on a Cloud Run L4 GPU, always under one name, `documind-slm`. That model is either supplied (a GGUF and the Modelfile generated from its tokenizer) or a stock model from Ollama's library, which stands in until a supplied one exists. The model is built into the image, the service scales to zero, and the GPU bills for every minute an instance lives.

In this lesson you generate a Modelfile from a tokenizer, and read from the kit how long each caller waits and what the GPU costs. Then you deploy the stand-in, smoke-test it and time a cold start. You send the gateway the PAN it re-routed in lesson 9.1. Then you put the small model behind the API on a candidate revision, and let the gate judge its answers.

- A small model on a GPU that sleeps

- The words: Ollama, a GGUF, the Modelfile, the stand-in, documind-slm, the startup probe, a cold start, keep-alive, the idle window, instance billing

- Before you run anything: set up the shell

- A Modelfile from the tokenizer

- The waits and the bill, from the kit

- The stand-in, deployed and smoke-tested

- The cold start, timed

- The small model behind the gateway and the API

- Why it works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn how the kit serves a model on a Cloud Run GPU under one name, whichever build it is. You will learn what a cold start is made of, how long each caller waits for one, and what the GPU bills while nobody is asking. Then you will prove it on your lane: the cold start timed, and a gated answer from the small model.

### A small model on a GPU that sleeps

Two builds under one name, an image that carries the model, an instance that starts on demand, a bill by the minute.

Two builds, one name. `make deploy-slm` stages a folder, `services/slm/build/`, and deploys it. The folder holds one of two builds:

- A stock model: with `SLM_STOCK` set (this lesson uses `gemma3:4b`), the folder holds only the model's name. The image pulls that model from Ollama's library and copies it to `documind-slm`. This is the stand-in.

- A supplied model: without `SLM_STOCK`, the folder gets two files from the datasets bucket. `documind-slm.gguf` holds the weights, and `documind-slm.Modelfile` was generated from the model's tokenizer. The image imports them with `ollama create`. The kit's comments expect a fine-tune of `unsloth/gemma-4-E2B-it`.

Either way the model is created when the image is built, not when an instance starts. Ollama serves it as `documind-slm`, and the service's `slm-source` label says which build is behind it: `stock` or `gguf`.

The Modelfile. A GGUF holds weights. Ollama also needs two things the weights were trained with: the format of a turn (the template), and the tokens that end an answer (the stops). `make_modelfile.py` takes both from the model's own tokenizer. The kit's comments say why: a template that disagrees with the checkpoint produces fluent text that never stops.

The service. One L4 GPU with 8 vCPU and 32 GiB. It runs at most one instance and at least zero, serves four requests at a time, allows 600 seconds a request, and sits behind IAM. The gateway's account and the UI's account may invoke it. A startup probe asks `/api/tags` every 5 seconds, starting 10 seconds in, and allows 30 failures. That gives Ollama 160 seconds to list the model before Cloud Run gives up on the instance.

The cold start. With zero instances, the first request after an idle spell waits for two things:

- An instance. Google says an L4 with its drivers is ready in about 5 seconds. Then the container, with its 3.3 GB model, must start and Ollama must answer.

- The model in the GPU's memory. The first generation loads it.

Ollama keeps a model loaded for 5 minutes after its last request, by default. Cloud Run may keep an idle GPU instance for up to 10 minutes, and may stop it sooner.

The bill. A GPU service is billed by the instance, from its start to its stop, idle minutes included, with at least a minute each time. For this shape in `us-central1` that is $1.42 an hour, Rs 120.78. An instance kept up all month (min-instances 1) costs Rs 86,904 by the kit's own figure. That is why `make deploy-slm` is its own act, never a side effect of deploying everything else, and why every session ends with `make slm-off`.

The routes and the API. The gateway's `documind-slm` route falls back to Gemini when the backend fails. `documind-sensitive`, where lesson 9.1's hook sends RESTRICTED text, has no fallback. The API reaches the small model on a revision that runs with `MODEL_BACKEND=gateway` and `GENERATOR_MODEL=documind-slm`: the same retrieval, the same prompt and the same gate as with Gemini.

A caterer's kitchen, rented by the minute. The kitchen is locked until the day's first order comes in. Unlocking it and lighting the gas takes a minute, and heating the tandoor takes a little longer. The tandoor cools five minutes after the last order, but the kitchen stays unlocked for up to ten, and the rent runs until the door is locked. Keeping it open all month costs as much as cooking in it all month.

The menu has one dish, the house thali. Either it is the caterer's own recipe, cooked from a card written from the chef's notes, or it is a branded thali bought in and served under the house name; a card on the door says which. A recipe card copied from a magazine instead of the chef's notes leaves the cook never knowing when to stop. And the kitchen is not in the city: the nearest one that rents by the minute takes guests by invitation only, so the default kitchen is abroad.

The kitchen is the Cloud Run instance, and the tandoor is the model in the GPU's memory. The rent is instance-based billing. The house thali is `documind-slm`, the card on the door is the `slm-source` label, and the recipe card is the Modelfile. The kitchen abroad is `us-central1`.

#### What does one request wait for?

Pick how long the service has been idle, how long your lane takes to start an instance and to load the model, and who asks. The first box shows what the request waits for. The second shows the timeouts along its path, which one fires first, and what the caller gets. The third shows what the GPU bills.

The timeouts are the kit's, read from the Makefile, `config.yaml`, the API's `config.py`, `run_eval.py` and `smoke_slm.py` when this page was built. The 5 minutes are Ollama's default, and the 10 minutes and the rates are Google's. The logic is compared with a Python version on all 256 combinations.

It does not know how long your lane takes to start an instance or to load the model: step 6 measures both. It counts a short answer as one second, and an answer to a real question can take several.

### The words: Ollama, a GGUF, the Modelfile, the stand-in, documind-slm, the startup probe, a cold start, keep-alive, the idle window, instance billing

Ten rows, each with the value it takes on your lane.

One distinction to hold: the model is built into the image once, and loaded into the GPU many times. Building takes minutes and happens on every deploy. Loading takes seconds and happens after every idle spell longer than Ollama's five minutes.

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

- The gateway from lesson 9.1. `make smoke-slm` checks the gateway's `documind-slm` route, and step 7 sends the gateway the PAN it re-routed.

- The API as `make up` deployed it. Step 7 puts a no-traffic candidate revision on it with the gateway backend. The API already knows the gateway's URL (`LITELLM_URL`, set when it was deployed), and `make deploy-gateway` let the API's account invoke the gateway.

- An L4 in `us-central1`. A project's first L4 deploy in a region is granted a quota of three GPUs, with zonal redundancy off, which is how the kit deploys. You need no request.

- About 240 MB for `~/tf-venv`, for step 3's transformers. Step 3 also downloads about 31 MB of tokenizer files from Hugging Face.

- Steps 6 and 7 in one sitting. Step 6 wakes the GPU; step 7 uses it while it is warm.

- What the lesson changes. It deploys `documind-slm`, which scales to zero, stores its image of more than 3.3 GB in Artifact Registry, and lets two accounts invoke it. It puts a candidate revision on the API and removes its tag, and creates `~/tf-venv`. The GPU bills while an instance lives: Rs 120.78 an hour, and up to 10 idle minutes after your last request.

### A Modelfile from the tokenizer

make_modelfile.py on the tokenizer of the model the kit expects a supplied fine-tune to start from. No GPU, no Google Cloud.

#### Definition

`make_modelfile.py` reads a model's tokenizer and renders one user turn through its chat template. It turns that render into Ollama's template, and takes the stop tokens from the tokenizer's own end tokens:

It needs the tokenizer's files, not the weights. The first cell makes a venv with a transformers that can read this tokenizer, and jinja2, which `apply_chat_template` needs. The second runs the generator on `unsloth/gemma-4-E2B-it`, the model the kit's comments name, and prints the Modelfile.

#### Do it

- The template is the tokenizer's own turn markers: `user`, `` and `model`. The stop is ``. Gemma 3 marks its turns with ``. A Modelfile typed from Gemma 3's documentation would be exactly the mismatch the generator exists to prevent.

- The file expects a GGUF beside it: `FROM ./documind-slm.gguf`. That is the name `make deploy-slm` fetches the weights under.

- The cell does not use the kit's pin. `services/slm/requirements.txt` pins transformers 4.57.1, which cannot load this tokenizer, even with jinja2 and protobuf added: it stops at an `AttributeError` while reading the special tokens. And jinja2, without which `apply_chat_template` refuses to run, is not in `requirements.txt`. So the cell installs transformers 5.17.0 and jinja2.

- The template carries the user turn and nothing else. It has `{{ .Prompt }}` and no `{{ .System }}`. Ollama fills a template like this one turn at a time, and passes the system message as `.System`, so a template that never names it drops it. The API sends its rules, and the JSON shape it parses, as the system turn (step 7). A supplied model served with this Modelfile never reads them. The stand-in's library template reads every message, and treats the system turn as a user turn.

- The warning is harmless. Reading a tokenizer needs no PyTorch.

### The waits and the bill, from the kit

Every timeout along a request's path, read from the kit's files, then the GPU's hour at Google's rates. No network.

#### Definition

A request to the small model passes up to four waits. `run_eval` waits for the API, the API waits for the gateway, the gateway waits for the SLM, and the SLM allows each request its own timeout. The gateway's route to the small model:

The API's side:

The cell reads these values and the rest from the kit's files, prints them in the order a request meets them, and prices the instance at Google's `us-central1` rates for an L4 without zonal redundancy.

#### Do it

- The API gives up before the gateway. The API waits 90 seconds, and the gateway waits 110 for either self-hosted route. When the small model takes longer than 90 seconds, the API returns 502 while the gateway is still waiting. `config.yaml` sends `documind-slm` to Gemini when the self-hosted model is "cold, scaled to zero or out of quota". After a slow cold start, that fallback can only answer a caller that has already gone. It still helps when the backend fails fast: a missing service, or a refused token.

- A cold start fits if it takes less than 90 seconds. The kit's own comment puts a cold GPU 30 to 60 seconds away. Step 6 measures yours. The panel above shows what each caller gets for any start and load time.

- The gate forgives one timeout. `run_eval` asks a row again two seconds after a timeout. By then, the first try has usually woken the instance.

- The GPU bills by the instance. $1.4209 an hour, Rs 120.78, whether it answers one request or none. The idle window can add up to Rs 20.13 after each session's last request. A month at min-instances 1 comes to Rs 86,960. The kit rounds the hour to $1.42 and says Rs 86,904.

### The stand-in, deployed and smoke-tested

make deploy-slm with SLM_STOCK, then the kit's smoke test: the model listed, both doors, the gateway's route, the label.

#### Definition

`make deploy-slm` stages the build, then deploys it on one L4 behind IAM:

The image creates the model while it is built:

Cloud Build builds a GPU service's source on an `e2-highcpu-8` machine, and this build pulls 3.3 GB into the image, so the first deploy takes several minutes. Then `make smoke-slm` runs five checks as the UI's account. The gateway check is this one:

#### Do it

- The model is listed. `/api/tags` answered in 0.1 s, because the instance the startup probe started was still up.

- The first generation took 12.0 s. The probe only asks `/api/tags`, so the smoke test's first `/api/generate` loaded the model into the GPU. The OpenAI-compatible door then answered in 0.6 s.

- The gateway's route answered, and its name says who served it: `ollama_chat/documind-slm`. Read that name every time. The check passes on any 200, so it also passes when `documind-slm`'s fallback answers with Gemini's name.

- The service says what it serves: the label `stock`, and the image's path in Artifact Registry.

### The cold start, timed

After more than 10 idle minutes: the instance, the model's load and a warm answer, each timed.

#### Definition

Leave `documind-slm` alone for more than 10 minutes, so that Cloud Run stops the instance. Then the cell mints the UI account's token, as the smoke test does, and times three calls:

- `/api/tags`, which waits for an instance;

- the first `/api/generate`, which loads the model into the GPU;

- a second `/api/generate`, warm.

If the instance is still up, the cell says so, and you run it again later.

#### Do it

- The cold start, timed. 53.4 s to the first answer: 41.4 s for an instance, then 11.4 s to load the model. That is the first proof. The stand-in's times are illustrations; yours are your lane's.

- Warm, the same call took 0.6 s.

- Under 90 seconds, so the API would have waited for it. Put your own two numbers in the panel above.

- Warm has two lengths. The model stays loaded for 5 minutes (Ollama's default; the kit sets no other) and the instance lives up to 10. A request between the fifth and the tenth minute pays the load again, on an instance that has been billing all along.

### The small model behind the gateway and the API

Lesson 9.1's PAN answered, the small model on a candidate revision, one answer priced, the scoped gate, and the cleanup.

#### Definition

Three things, in order:

- The gateway. Lesson 9.1's three requests again. The PAN with a date goes to `documind-sensitive`, which now has a backend.

- The API. `make candidate MODEL_BACKEND=gateway GENERATOR_MODEL=documind-slm` puts a no-traffic revision on the API; it is the command the Makefile's own comment gives for judging the self-hosted model. Then one golden question through it, lk-06. The API sends the gateway its rules and the JSON shape as the system turn, and the context and the question as the user turn:

Its answer names a model, but the name is the route it asked for, not the model that served it:

So the cell reads the price instead. The gateway prices the route that served the answer, at `config.yaml`'s rates, and the API passes that cost on. A self-hosted answer costs 20.50 USD a million tokens, in and out; a Gemini answer does not.

- The gate, scoped to the rows that cite the HR policy, then lk-06's row in its report. Last, the cleanup: the candidate's tag removed and the GPU scaled to zero.

#### Do it

- The sensitive route answered. The PAN with a date got an HTTP 200 from `ollama_chat/documind-slm`. Its cost header, 0.0010045 USD for 19 tokens in and 30 out, is the self-hosted rate. In lesson 9.1 the same request got an error. A GPU in `us-central1` answered it. So the text the hook kept from Gemini, because it must not leave, went to Iowa.

- The bare PAN still went to Gemini. The hook never re-routed it (lesson 9.1).

- The candidate answered lk-06 through the small model. The answer carries a citation, and its cost matches `documind-slm`'s rate. The model field says `documind-slm`, and it would say that whoever answered. When the hook reads a context as CONFIDENTIAL, it masks it and sends it to Gemini, and only the price shows it. The CONFIDENTIAL patterns are an email address or a ten-digit number, and acme's own CGST Act holds an email address.

- The gate judged it. lk-06 passed. That is the second proof: a gated answer from the small model. Of 10 rows, 8 passed. The stand-in missed lk-02 and lk-08: lk-02 answered without "15 June", and lk-08 refused a question the policy answers. That is still above every threshold. The misses are an illustration of what a 4B model does; your rows are your lane's.

- Two runs can differ. The API sends no temperature, which is right for Gemini 3: Google says to leave it at the default. A stock model samples at its library's default, and `gemma3:4b`'s is 1.

- The cleanup. The candidate's tag is gone, and the live revision never took its traffic. `make slm-off` set min-instances to 0, which `make deploy-slm` had already set. It cannot stop an idle instance: that stops by itself within 10 minutes, and bills until then. Lesson 9.4 proves zero GPU instances.

### Why it works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- The model is created when the image is built, because importing a 2 GB GGUF is time a cold start does not have.

- The Modelfile is generated, never typed. A template that disagrees with the checkpoint produces fluent text that never stops.

- Ollama is pinned to 0.33.3. Gemma 4 support arrived in the 0.33 line, and an older Ollama loads the GGUF and produces nonsense rather than refusing.

- The startup probe waits for the model, not the process. `/api/tags` lists the model only once Ollama has it.

- The GPU is its own act. `make deploy-slm` is never a side effect of deploying everything else, because of the bill.

- `us-central1`, not Mumbai. L4 GPUs in `asia-south1` are by invitation only. Delhi (`asia-south2`) has the RTX PRO 6000 if the data must stay in India, at a different price and a minimum of 20 vCPU and 80 GiB.

- The sensitive route has no fallback. A cold GPU means a slow answer, not a leak.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does. The transformers facts come from running `make_modelfile.py` under both versions when this page was built.

- The sensitive route leaves India. `SLM_REGION` defaults to `us-central1`, while `config.yaml` tags `documind-slm` `residency-in` and `documind-sensitive` `dpdpa`. The text the hook re-routes, because it must not leave, goes to a GPU in Iowa.

- `make_modelfile.py` does not run on the kit's pins. transformers 4.57.1 cannot load the Gemma 4 tokenizer. And jinja2, which `apply_chat_template` needs, is not in `requirements.txt`.

- The generated template drops the system turn. It has no `{{ .System }}`, and the API sends its rules and its JSON shape as the system turn. A supplied model served with it never reads them.

- The API names the route it asked for, not the model that answered. The gateway's reply says which model served it, and `generate()` returns the route instead. A context the hook reads as CONFIDENTIAL is masked and answered by Gemini, and the answer still says `documind-slm`. Only the price shows it.

- The fallback after a slow cold start never reaches the API. The API waits 90 seconds and the gateway 110. A cold start slower than 90 seconds is a 502 at the API, whatever `documind-slm`'s fallback does afterwards.

- The smoke test's gateway check passes whoever answers. It counts any 200, Gemini's fallback included.

- The model unloads at 5 minutes, and the instance bills for up to 10. The image sets no `OLLAMA_KEEP_ALIVE`. And nothing ends the idle window: `make slm-off` sets the same min-instances 0 that `make deploy-slm` set.

- A small model samples at its own default. The gateway path sends no temperature, so the stand-in answers at 1, and two runs of the gate can disagree.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

`documind-slm` runs on a Cloud Run L4 in `us-central1`, scaled to zero, serving the stand-in (`slm-source=stock`). Its image is in Artifact Registry, and the gateway's two self-hosted routes now have a backend. The API's candidate revision has lost its tag, and the live revision still answers through Vertex AI (`MODEL_BACKEND=vertex`). `~/tf-venv` holds transformers 5.17.0. Lesson 9.3 inspects the vLLM service and the GKE alternative.

Netsetos GenAI on GCP · Module 9 Serving · Lesson 9.2 Serve a supplied or stock model using Ollama · v5.0

Next: Lesson 9.3 Inspect the vLLM service and the GKE alternative.
