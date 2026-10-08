# Lesson 9.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_9.3_VLLM_GKE_WIX.html`, reviewed at blob `383d76df919ed8e9e3c09d023f05584889c7ce6d`. Learners read that page on the course site; this guide keeps its prose.

Lesson 9.2 served the small model with Ollama. The kit holds two more ways to serve it, both optional, and no lesson deploys either. One is vLLM, an engine built to answer many requests at once, on the same Cloud Run L4. The other runs vLLM on GKE Autopilot: a pod that stays up all month, billed every hour, and the only self-serve L4 in Mumbai.

In this lesson you read the vLLM service and the GKE manifest from their files, the way you would before paying for either. Then you inspect what your lane actually has. Last, you work out from your own traffic when an always-on pod costs less than an instance that sleeps.

- Three ways to serve the same small model

- The words: vLLM, continuous batching, the gemma-vllm image, documind-inference, GKE Autopilot, the lab cluster, node billing, the manifest, ClusterIP, the duty cycle

- Before you run anything: set up the shell

- The vLLM service, read

- The manifest, read

- The lane's cluster, inspected

- The duty-cycle sum

- Why it works this way, what it costs, and what the kit does not do yet

- Verify it yourself: the checklist

You will learn what vLLM does that Ollama does not, and how GKE Autopilot bills a GPU. You will learn why an always-on pod and an instance that scales to zero are a question of duty cycle. Then you will prove it on your lane: the manifest read against the image it runs, and the duty-cycle sum for your own traffic.

### Three ways to serve the same small model

Ollama on Cloud Run, vLLM on Cloud Run, vLLM on GKE: the same L4 class, different engines, different bills.

vLLM on Cloud Run. vLLM is an inference engine built for many requests at once. It adds new requests to a running batch as they arrive (continuous batching), and pages the model's attention cache through GPU memory, as an operating system pages memory. Ollama answers a few requests at a time: the kit lets an Ollama instance take 4, and a vLLM instance 32.

- The service. The kit's vLLM service, `services/gemma-vllm`, is its own FastAPI app around vLLM's engine. It loads Gemma 3 4B into the GPU before it answers. Then it serves an OpenAI-compatible `/v1/chat/completions`, and two DocuMind endpoints that classify and extract with structured output.

- The targets. `make build-vllm` builds the image on Cloud Build. `make deploy-vllm` deploys it on the same L4 shape as the SLM, behind IAM, and lets the gateway's and the UI's accounts call it.

- The route. The gateway's `documind-inference` route points at it through the token proxy, and falls back to `documind-slm`, then to Gemini. `config.yaml` logs its answers at 6.80 USD a million tokens, against the SLM's 20.50. Both are rates, not prices: the price is the GPU's hour.

GKE Autopilot. Autopilot is Kubernetes where Google runs the nodes. You submit a pod, and Autopilot finds or creates a node that fits it. A pod that asks for a GPU gets a whole node of that class, here a `g2-standard-8` with one L4. It pays for the node plus an Autopilot premium, busy or not.

- The manifest. `gke/vllm-deployment.yaml` runs one replica of the vLLM image, with no autoscaler. It is always up and always has the model in the GPU, so there is no cold start, and there is a bill at 3 a.m.

- The address. Its Service is a ClusterIP: an address only inside the cluster, which you reach with `kubectl port-forward`.

- Mumbai. GKE is the only self-serve way to an L4 in Mumbai, because Cloud Run's L4 there is by invitation.

The lane's cluster. `make up` creates a cluster called `documind-autopilot`, but by default it is not Autopilot. Since 17 September 2026, `gke.tf` has built a Standard cluster with one small CPU node, an `e2-standard-2`, because Autopilot needs SSD quota a new project may not have. That lab cannot schedule the GPU pod, so `make gke-up` checks the mode and stops. Setting `gke_autopilot` to true replaces the cluster.

The duty cycle. Cloud Run bills an instance for as long as it lives: each burst of traffic, plus up to 10 idle minutes after it. The duty cycle is that time as a share of the month. Cloud Run bills it at $1.4209 an hour. An always-on pod bills every hour, but at less: $0.9558 in Iowa and $1.0113 in Mumbai, plus a $0.10 cluster fee unless the free tier pays it. So the sum has a crossover. Above roughly two-thirds to four-fifths of the month, the pod is cheaper; below it, the instance that sleeps.

Office lunches in Bengaluru: a caterer on call, or a canteen with its own cook. The caterer comes when you call, cooks, stays a few minutes to clear up, and bills for every hour he was in the building. The canteen cook is on the payroll every hour of the month, cooking or not. His hourly rate is lower, and lunch is ready the moment anyone walks in. If the office eats in short bursts, call the caterer. If someone is eating most of the day, hire the cook: past roughly three-quarters of the day, the payroll is the cheaper bill.

The caterer's firm works only from another city; the cook can be hired locally. Before hiring, you read the job description. This one gives the cook instructions he never reads, sends him to a kitchen with no tandoor, and forgets his groceries.

The caterer is Cloud Run, and clearing up is the idle window. The cook is the GKE pod, and the payroll is the always-on node. The job description is the manifest. The kitchen with no tandoor is the lane's CPU cluster, and the groceries are the model's weights.

#### Always on, or on demand?

Pick how often your traffic comes, how long each burst lasts, on how many days, where the pod would run, and who pays the cluster fee. The first box sums the time a Cloud Run instance lives. The second prices an always-on pod. The third says which is cheaper and where the crossover sits.

The rates are Google's, from the Cloud Run, Compute Engine and GKE pricing pages on 24 September 2026. The 10 idle minutes are Cloud Run's limit for a GPU instance, and a month is 730 hours, as Google counts it. The sum is compared with a Python version on all 280 combinations.

It counts only the minutes an instance lives, not the minutes an instance takes to start (lesson 9.2 timed that start on your lane). It prices Cloud Run in `us-central1`, the one self-serve L4 region the kit uses. It leaves out disks, image storage and network.

### The words: vLLM, continuous batching, the gemma-vllm image, documind-inference, GKE Autopilot, the lab cluster, node billing, the manifest, ClusterIP, the duty cycle

Ten rows, each with the value it takes on your lane.

One distinction to hold: Cloud Run bills an instance while it lives, and GKE bills a node while it exists. An idle instance stops by itself; a node stays until the pod or the cluster is deleted.

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

- The lane as `make up` left it. Its cluster, `documind-autopilot`, is what step 5 inspects.

- Nothing to build or deploy. The lesson's one live step reads the lane with gcloud. It also runs `make gke-up`, which stops on the lab cluster before it changes anything.

- No Hugging Face token, no GPU quota and no change to the cluster. The lesson reads what those would take instead: `make build-vllm` runs for 20 to 30 minutes on a 32-vCPU build machine, and needs a token with Gemma access.

- The GPU pod needs `gke_autopilot=true`, which replaces the cluster, and Compute Engine GPU quota in the region.

- What the lesson changes: nothing. The lab cluster already bills while it exists (step 5).

### The vLLM service, read

The image, the engine, the service's door and the gateway's route, from the kit's files. No network.

#### Definition

`make deploy-vllm` puts the image on the same L4 shape as the SLM, with room for 32 requests at a time:

The image is vLLM's own base, with the app installed on top:

The app loads the engine before the server answers:

And it keeps a door of its own, in front of every chat completion:

The cell reads these files, together with the token proxy, the gateway's config and Terraform. It prints what the service needs, and whether anything on the lane supplies it.

#### Do it

- The image carries no weights. The Dockerfile installs the app on vLLM's base image and never downloads a model. `cloudbuild.yaml` passes the Hugging Face token as a build-arg, but no `ARG` receives it. The Makefile's comment, the GKE manifest and the GKE README all say the weights are in the image, and they are not.

- So the engine would download Gemma 3 4B when it starts, and that download would be refused. Gemma's weights on Hugging Face are gated behind Google's licence, and `make deploy-vllm` gives the service no token.

- The service keeps its own door. Every chat completion needs an `X-API-Key`, hashed and looked up in Firestore. The gateway's token proxy sends an ID token and no `X-API-Key`. Nothing in the kit writes an `api_keys` document, and the service's account has no roles, Firestore's included. A request from the gateway would be refused, and `documind-inference` would fall back to the SLM.

- Its request log goes to a placeholder: a BigQuery table named `project.dataset.inference_logs`.

- What it would do well, once fed: 32 requests at a time on one L4, the model loaded before the first request (the startup probe allows 270 s), and structured output for classifying and extracting.

### The manifest, read

What gke/vllm-deployment.yaml asks the cluster for, checked against the image it names. No network.

#### Definition

`make gke-up` fills in the image's name and applies two objects. The Deployment's container:

The Service in front of it:

The cell reads the manifest the way Kubernetes would, and checks it against the image's own start: the Dockerfile's `ENTRYPOINT` and `CMD`, and what `main.py` reads.

#### Do it

- The manifest, read. That is the first proof. It asks for one replica on an L4 node, with 6 vCPU and 24 GiB, which stays under the `g2-standard-8`'s 8 and 32. Ask for all 8 and 32, the manifest's comment says, and Autopilot rounds up to a `g2-standard-12`. The weights get 600 seconds to load, and the Service is a ClusterIP.

- It cannot start this image. A container's `args` replace the image's `CMD` and run after its `ENTRYPOINT`. This image's `ENTRYPOINT` is empty, so Kubernetes runs the first arg, `--model=google/gemma-3-4b-it`, as the program. The args were written for vLLM's own server image, whose entrypoint is its API server. The kit's image starts uvicorn from `CMD`, and the args replace it.

- Even the right command would find nothing to load. The image holds no weights (step 3), and `HF_HUB_OFFLINE=1` forbids the download.

- The args would not configure it either. `main.py` takes its model from `MODEL_NAME` in its environment, and sets `max_model_len=8192` in code, whatever `--max-model-len` says.

### The lane's cluster, inspected

What documind-autopilot is, what it bills, what make gke-up says about it, and whether any vLLM service exists. Read-only.

#### Definition

The cell describes `documind-autopilot` with gcloud: its mode, its node pool and the hour it bills. It also looks for the vLLM service on Cloud Run and its image in the lane's registry. Then `make gke-up` checks the mode before anything else:

#### Do it

- The cluster is a Standard lab: one `e2-standard-2` with no GPU, in one zone, under a regional control plane.

- It bills while it exists: $0.1805 an hour, Rs 11,199 a month in Mumbai. $0.10 an hour is the control plane. The free tier covers that fee only for zonal and Autopilot clusters, and this one is regional.

- The rest is the node, and no lesson schedules a pod on it.

- `make gke-up` read the mode and stopped. This is the kit's own guard: without it, a GPU pod would sit Pending on a cluster that has no GPU node.

- No vLLM service and no image. Both are optional, and no lesson builds them.

- The gateway's GKE route has nowhere to go. Here it is:

`GKE_VLLM_URL` is never set: `make deploy-gateway` sets the SLM's and the vLLM service's URLs, and not this one. A ClusterIP has no address outside the cluster, and the gateway has no route into the VPC. So `documind-gke` falls through to `documind-inference`, and then to Gemini.

### The duty-cycle sum

Your traffic as bursts, the minutes an instance lives for them, and the crossover where an always-on pod gets cheaper.

#### Definition

The sum is an instance's life. Each burst of traffic, plus the idle minutes after it (up to 10, or less when the next burst is sooner), capped at a day, times the days with traffic. Cloud Run bills that share of the month's 730 hours at $1.4209 an hour. A GKE pod bills all 730 hours, at the node's price plus Autopilot's premiums, and the cluster fee unless the free tier pays it. The free tier pays one Autopilot cluster's fee per billing account.

Put your own traffic in the first line: how many bursts a day, how many minutes each, and on how many days a month.

#### Do it

- The duty-cycle sum. That is the second proof. Eight bursts of 30 minutes, each with 10 idle minutes after it, make 320 minutes a day. On 22 days that is 117.3 hours, 16.1% of the month: Rs 14,171 on Cloud Run.

- An always-on pod costs more than four times as much at this pattern: Rs 59,309 in Iowa and Rs 62,753 in Mumbai, before any cluster fee.

- The crossovers. GKE is cheaper above 67.3% of the month in Iowa (74.3% with the fee), and above 71.2% in Mumbai (78.2%). That is an instance alive for roughly 16 to 19 hours of every 24.

- The kit's README does the same sum for Iowa, with the fee, and gets 74%. It counts the fee as due "after the free-tier credit", but the credit pays that fee for one Autopilot cluster per billing account.

- For traffic in bursts during a working day, Cloud Run wins by a wide margin. GKE earns its bill with steady traffic, or when the model must run on an L4 in India.

### Why it works this way, what it costs, and what the kit does not do yet

The design choices, from the kit's own comments, then the bill and the gaps.

- vLLM is the engine for concurrency. Continuous batching lets 32 requests share one L4. The image runs one worker, because GPU memory is not shared across processes.

- The engine loads before the server answers, so the service's `/health` means the weights are on the GPU.

- The pod asks for 6 vCPU and 24 GiB, not 8 and 32. A pod that asks for the whole `g2-standard-8` leaves nothing for the kubelet, and Autopilot provisions a `g2-standard-12`, at about $0.16 an hour more.

- The Service is a ClusterIP on purpose: no public IP and no load-balancer charge, for a service only a benchmark talks to.

- The lab cluster is Standard, with standard disks, because Autopilot needs SSD quota a new project may lack. `make gke-up` checks the mode, instead of leaving a GPU pod Pending.

- Both are optional. The lane's self-hosted model is the SLM on Cloud Run; vLLM and GKE are the alternatives you price before you choose.

#### What it costs

Each point is checked in the kit's code, and the build asserts it, so this box changes when the kit does. The prices are Google's, read on 24 September 2026.

- The vLLM image carries no weights. The Dockerfile downloads nothing, and the Hugging Face token passed as a build-arg has no `ARG` to land in. The model is gated, and `make deploy-vllm` gives the service no token to fetch it at start-up.

- The vLLM service cannot answer the gateway. It wants an `X-API-Key` that the token proxy never sends, looked up in Firestore collections nothing writes, as an account with no roles. It also logs to a placeholder BigQuery table.

- The manifest cannot start its image. It sets args and no command on an image with an empty `ENTRYPOINT`, so the first arg runs as the program. `main.py` reads none of those args, and `HF_HUB_OFFLINE=1` meets an image with no weights.

- The `documind-gke` route reaches nothing. `GKE_VLLM_URL` is never set, a ClusterIP has no address outside the cluster, and the gateway has no VPC egress.

- The lab cluster bills for nothing. A regional Standard control plane, which the free tier does not cover, plus one CPU node, comes to about Rs 11,199 a month in Mumbai. No lesson schedules a pod on it, and only `make down` removes it.

- A GKE GPU pod is outside the three cost controls. `make gpu-cap` caps Cloud Run's GPU quota only.

- `gpu_left_warm` watches the two Cloud Run GPU services only.

- The nightly job skips the cluster.

- The nightly job's account keeps cluster-admin on a cluster it no longer touches: its script only prints a line about it.

- The docs lag the code. `gke/README.md` still lists "no VPC attachment", though `gke.tf` attaches `documind-vpc`. It also counts the $0.10 fee as due after the free-tier credit, which pays it for one Autopilot cluster.

- `UNOWNED.md` still calls `gke.tf` Autopilot, and still says the manifest pins `vllm/vllm-openai:v0.28.0`.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your lane.

Nothing. The lesson built and deployed nothing, and `make gke-up` stopped before it changed anything. The lab cluster, `documind-autopilot`, is still there and still billing, as it was before; `make down` removes it with the rest of the lane. Lesson 9.4 compares the backends that actually answer, and checks that no GPU instance is left running.

Netsetos GenAI on GCP · Module 9 Serving · Lesson 9.3 Inspect the vLLM service and the GKE alternative · v5.0

Next: Lesson 9.4 Compare actual backends and verify shutdown behavior.
