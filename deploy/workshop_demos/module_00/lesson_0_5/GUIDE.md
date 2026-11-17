# Lesson 0.5: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_0.5_Setup_Cloud_WIX.html`, reviewed at blob `d125af97fa93a38ec6b6abb8e4706f9be0d783fa`. Learners read that page on the course site; this guide keeps its prose.

One runbook, in order, from an empty browser tab to a working DocuMind in your own Google Cloud project. Phase 1 prepares Cloud Shell: the project, the tools, Python 3.12 and the kit from `main`. Phase 2 creates the infrastructure with one reviewed Terraform plan. Phase 3 pins the commit you build from, builds 7 images, deploys every service and the UI behind Google sign-in, and puts you and the services on the tenant rosters so the UI answers.

- The three phases: setup, Terraform, build and deploy

- The words: kit, settings file, GIT_SHA, state, plan, IAP, roster

- Before you run anything: open Cloud Shell and keep it alive

- Phase 1, S1 to S4: the project, the sign-in, the variables, the tools

- Phase 1, S5 to S7: Python 3.12, the kit from main, the dependencies, reopening a terminal

- Phase 2, T1 to T4: the APIs and the state bucket, Terraform's sign-in, the billing account, the inputs

- Phase 2, T5 to T8: init, one saved plan, the apply, the vector index

- Phase 3: restore the shell, pin GIT_SHA, export the runtime settings (F1), prepare the secrets (F2)

- Phase 3: the build gate, then all seven images (F3)

- Phase 3, F4 to F8: deploy the seven services

- Tenants: put people and services on the rosters

- Finish what make up finishes: the index wait, the managed stores and the BigQuery views

- Verify all seven services

- Open the UI and ask a first question

- Verify it yourself: the checklist

You stand up the whole DocuMind lane from Cloud Shell, block by block, stopping at every checkpoint that fails: set up the shell, apply the infrastructure with Terraform, pin the commit you build from, build and deploy 7 services, put people on the tenant rosters so the UI answers with citations, and close with the kit's own finishing targets, so the lane is the one `make up` would have built.

From the end of the Terraform apply, a handful of resources bill every hour whether anyone uses them or not: Rs 44.05 an hour if Vector Search picks a SMALL shard, Rs 111.10 if it picks MEDIUM (about Rs 1,057 to Rs 2,666 a day), at Mumbai list prices. Cloud Build minutes, Gemini calls and Document AI pages come on top. Use a project made for the course and delete it when you are done.

This lesson builds the same lane as lesson 0.3, by hand in Cloud Shell, block by block, where 0.3 runs `make plan` and `make up` from your own terminal. Choose one. Run this lesson instead of 0.3, then go on to lesson 0.4 with the lane it builds. If 0.3 already built your lane, read this lesson to see what `make up` does, but do not run it: S1 creates a second project, and the lane in it bills another Rs 1,057 to Rs 2,666 a day until you delete it.

### The three phases: setup, Terraform, build and deploy

What happens where, and why in this order.

Standing up a lane is three jobs, and each one needs what the one before it produced. Every block on this page runs in the same Cloud Shell terminal, and every block ends in a checkpoint: a PASS line, or a STOP line that names what to fix.

#### Setup

The project and billing, the tools, Python 3.12 and a clone of the kit. Settings go into one file so a new terminal can restore them.

#### Terraform

APIs, the state bucket, a saved plan you read, then the apply. Every resource the services need exists afterwards; no service runs yet.

#### Build and deploy

Pin the commit, build seven images under that tag, deploy each to Cloud Run as its own account, then write the rosters.

Setup changes almost nothing in your project. It makes Cloud Shell ready: the project selected, a Python 3.12 environment outside the source tree, and the kit cloned from `main` into `~/deploy_module_rag`. The values every later command needs (project, region, residency, bucket names) are saved to `~/rag-env.sh`, which is what lets you close the tab and continue tomorrow.

Terraform compares what the kit declares under `terraform/` with what your project has, writes the difference to a saved plan, and applies exactly that plan. Its record of what exists, the state, lives in a versioned bucket in your own project.

Build and deploy starts by pinning `GIT_SHA`: the one commit every image is built from and every service is deployed with. Cloud Build turns each service into an image tagged with it; `gcloud run deploy` runs each image as its own service account. The last step writes the rosters: IAP decides who may open the page, the roster decides which tenant's documents they may ask about.

Opening a branch office. Setup is collecting the drawings and filling in the site diary, so the next shift knows where things stand. Terraform is the builder: a signed list of every wall and door before work starts, and the site register kept in the office safe. Build and deploy is moving the staff in, every one hired from the same printed staff list (the pinned commit), each with their own ID card, and a receptionist (IAP) at the door with the tenant list (the roster) in hand.

### The words: kit, settings file, GIT_SHA, state, plan, IAP, roster

Every term the commands below use, in one table.

### Before you run anything: open Cloud Shell and keep it alive

Open the Google Cloud console signed in as the account that owns your billing account, and click Activate Cloud Shell. Start a `tmux` session: builds and the Terraform apply run for a long time, and inside tmux they keep running if the browser drops.

Some terminals drop or reorder characters when a long block is pasted. Use the copy button on each window, never select by hand, and make sure no line ends in a backslash followed by a space. If a block misbehaves, paste it into a file and run it in this shell: `nano /tmp/step.sh`, then `source /tmp/step.sh`. Use `source`, not `bash`, so the variables it sets stay in your terminal.

### Prepare the project and the shell: the project, the sign-in, the variables, the tools

Four blocks that change almost nothing in your project: a project with billing, gcloud signed in, one set of saved variables, Terraform 1.9 and the command-line tools.

### S1. Create the project and open Cloud Shell

Project, billing and a Bash prompt in Cloud Shell.

In the Google Cloud Console, open Manage resources and choose Create project. Enter a demo project name, note its generated Project ID, pick the organization or folder and the billing account, then choose Create. Use this one project for the whole guide.

If billing was not linked during creation, select the project, open Billing and link an active billing account you are allowed to use.

Select the project in the project picker, click Activate Cloud Shell, authorize it and wait for the Bash prompt. Every command in these guides is Bash, not PowerShell, Command Prompt, Colab or a Python prompt.

### S2. Sign in the gcloud CLI

The account every later command runs as.

Prints your operator email. If not, run `gcloud auth login --no-launch-browser` and check again.

### S3. Set the project and session variables

One set of variables, checked, then saved for new terminals.

Change `PROJECT` to your project ID. The block stops at the first failed check.

Ends with `PASS: project () is active, billed, operator `.

Write the helper that saves your settings for new terminals, then save. It now also keeps `GIT_SHA`, the source snapshot your images are built from (pinned in Phase 3).

Prints `PASS: settings saved to ~/rag-env.sh`.

### S4. Check Terraform and command-line tools

Terraform 1.9 or newer, git, jq, make and file.

Terraform v1.9.0 or newer and no MISSING lines: skip to S5. Otherwise run the matching install below.

Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository:

The fingerprint identifies HashiCorp's package-signing key. Do not continue if the download or conversion failed.

The last command prints Terraform v1.9.0 or newer.

Only if `terraform` still isn't found, or an older binary shadows it:

Packages installed outside your home directory may need reinstalling after a Cloud Shell VM reset. Never loosen `required_version` or provider constraints, and never use insecure TLS or unsigned-package flags.

Install git, jq, make or file (only if one is missing):

### Prepare Python and the kit: the 3.12 environment, the clone from main, the dependencies

Python 3.12 outside the source tree, the kit at ~/deploy_module_rag, the operator's packages; then how a new terminal gets it all back.

### S5. Create the Python 3.12 environment

Python 3.12 in ~/rag-shell-venv, outside the source tree.

The environment lives at `$HOME/rag-shell-venv`; project files stay in `$HOME/deploy_module_rag`.

The last line starts with PASS. Activate again in every new terminal.

### S6. Get all files from the latest main

The kit from main into ~/deploy_module_rag, and the commit it is at.

Clones `main` into `$DEMO_ROOT` the first time and fast-forwards to the latest `main` afterwards.

Once you have built images in Build and deploy, they are tied to the commit saved in `GIT_SHA`. Pulling newer code afterwards does not change the running services; the pin block in Phase 3 will notice the difference and tell you to either go back to the saved commit or rebuild every image.

Ends with `PASS: up to date with origin/main`, the full commit and the file count (1,630 on 14 October 2026).

If Git refuses to update because you edited a tracked file, commit or discard that change and rerun. Files Terraform writes (for example `terraform/.terraform.lock.hcl`) do not block the update.

### S7. Install Python dependencies

The operator's Python packages, checked against the kit's pins.

Needed for the build gate, ingestion, evaluation and smoke tests. Terraform does not need it.

Ends with `PASS: dependency evidence saved`.

### Reopening a terminal later

Restores your saved settings in a new terminal. To also pull the latest code, rerun S6.

Ends with `PASS: Terraform … is available` and shows the saved `GIT_SHA` (or “not pinned yet” before your first build).

If Terraform will run in this terminal and its sign-in has expired, repeat Terraform step T2.

Finish Phase 1 in this terminal first, with the Python environment active. Terraform works from `~/deploy_module_rag/terraform`, keeps its state at `gs://$PROJECT-tfstate` under the prefix `documind/$PROJECT`, the bucket and prefix the kit's Makefile uses (`TFSTATE_BUCKET`, `TFSTATE_PREFIX`), and reads its inputs from `terraform/runbook-project.auto.tfvars.json`, the file `make plan` writes, plus the `TF_VAR_` values in your settings file. Every later make target (`make drift`, `make deploy-services`, `make down`, `make off`) therefore reads this lane. Plan on one path at a time: this phase's saved plan, or `make plan`, never both in flight.

### Prepare Terraform: the APIs and the state bucket, its sign-in, the billing account, the inputs

Everything Terraform needs before it plans, each block ending in a PASS line.

### T1. Enable APIs, service agents and the state bucket

40 APIs, the service agents, the versioned state bucket.

Before you start, finish Phase 1 (S1 to S6) in this terminal with the Python environment active. The API list is the block `make apis` runs; this step adds the service agents and the state bucket.

Ends with `PASS: APIs, service agents and state bucket ready.` If `gcloud beta` asks to install a component, accept it.

### T2. Sign in Terraform and set its quota project

Application Default Credentials and the quota project.

Run this alone, open the URL and sign in with your operator account:

Ends with PASS.

### T3. Save the billing account for Terraform

The billing account Terraform's budget needs, verified and saved.

Prints PASS with your billing account ID.

### T4. Set the Terraform inputs

Every Terraform input, exported and saved.

Every input the kit's `make plan` would pass, and the CI trust, saved into the same inputs file. Inputs not listed keep their `variables.tf` defaults: the Google Chat door, the Desk job and GKE Autopilot stay off.

The CI trust (`terraform/wif.tf`) lets GitHub Actions workflows from one repository, on one branch, become `sa-documind-cicd` in your project with no key file. That account can deploy code that runs as your services, so the repository must be one you own. It is never the repository you cloned: `netsetos/agents_workshop_learner` is the course author's, and trusting it would let the author's workflows deploy into your lane. On GitHub, open that repository and choose Fork; your fork is `YOUR-GITHUB-USER/agents_workshop_learner`. Lesson 11.1 builds and deploys through this trust. Name your fork in `GH_REPO`; the block looks up its numeric id, the value the trust is really keyed on, and stops on the author's repository or an empty answer.

Prints `PASS: CI trust saved`, the inputs, including `GitHub repository:` your fork and its numeric id, and your alert email, then `PASS: settings saved`.

### Run Terraform: init, one saved plan, the apply, the vector index

Point Terraform at your bucket, read one plan, apply exactly that, then prove nothing is left to change.

### T5. Initialize Terraform

Point Terraform at its state in your bucket.

Init succeeds. On a first deployment the state list is empty; on a rerun it lists your existing resources, which is expected. This is the bucket and prefix the kit's make targets use, so `make drift`, `make deploy-services` and `make down` read this state later.

### T6. Plan the full infrastructure

A saved plan file, after validate and an input check.

Ends with `Plan: N to add, 0 to change, 0 to destroy.` Review the plan before applying.

### T7. Apply

Apply that exact plan, then prove nothing is left to change.

Run alone, in the same terminal as T6 (the plan file name is only in that shell).

Confirm nothing is left to change:

`exit code: 0`. Exit code 2 means changes remain; 1 means an error. If apply failed partway, fix the error and go back to T6 for a fresh plan.

### T8. Verify the vector index

The index, the endpoint and the deployed ID, still empty.

Shows the index, the endpoint and deployed ID `documind_chunks_v1`, with 0 vectors.

Billing runs continuously from here, even with no traffic: the VPC connector, vector index, two Cloud SQL instances, Spanner and GKE.

Run Phase 3 in one terminal. After any restart, run the restore block (the first block below) and F1 again, and the build-context block before any build: those values live only in the shell. Then continue from the step that was interrupted.

### Restore the shell, pin GIT_SHA, export the runtime settings and prepare the secrets

The commit every image is built from, the Terraform outputs every deploy reads, and the cookie secret the UI mounts.

### Restore the shell and pin GIT_SHA

Settings back, Python checked, and the commit every image is built from.

Run this first in every new terminal. It restores the settings saved in Phases 1 and 2, activates Python 3.12, loads the repository helpers from `commands/session-restart.sh` and checks Terraform and the Python dependencies. It changes nothing in the cloud.

Ends with `PASS: shell restored`. A Python STOP means rerun S7; a sign-in error means `gcloud auth login`, and for Terraform also T2.

Now pin `GIT_SHA`: the exact commit every image is built from and every service is deployed with. The first time, it records the commit you have checked out. After that, it checks the checkout still matches. Its form is the short hash, the one the kit's own `make build` tags images with (`GIT_SHA ?= git rev-parse --short HEAD` in the Makefile), so a later `make deploy-services` or `make promote` finds these images.

Prints PINNED or PASS, the snapshot line, and `PASS: settings saved`. The saved `GIT_SHA` now survives restarts.

Never set `GIT_SHA` by hand to a value that was not built. If you see the “not the checked-out commit” STOP, choose one of the two options it prints; do not mix images from different commits.

Check Python syntax in the build inputs:

### F1. Export runtime settings from Terraform state

The runtime settings every deploy reads, from Terraform's outputs.

Run only after the full reviewed Terraform plan has been applied. A missing or empty output is a stop condition. This block must run in your main shell (not a subshell) because it exports variables for every later step. Rerun it after any restart.

F1 prints PASS and the guard prints every value with no error.

`RETRIEVAL_CURRENT_ONLY=on` deliberately differs from the upstream Makefile default; an older corpus needs a backfill review first. Keep graph retrieval off for the first vector proof.

### F2. Prepare cookie-secret and the checkpoint DSN

The UI's cookie secret and the chat checkpoint DSN.

Terraform creates `cookie-secret` as an empty holder. The UI and admin services mount `:latest`, so it needs one enabled version. A permission error must be fixed; it is not evidence that no version exists.

The block ends with `PASS: cookie-secret and checkpoint DSN ready.`

### Gate the build, then build all seven images

The kit's own regression tests first; then seven images under one tag.

### Build gate: regression tests and shared imports

The kit's own regression tests, before anything is built.

Run the regression tests that ship with the pinned commit against the local source. Stop if the task-type, carry-over or repair tests fail.

Both suites report OK (12 and 8 tests on 14 October 2026) and the last line reads `PASS: shared sparse encoder available: blake2b-tf-v1`.

### F3. Build all seven images

Seven images, all tagged with the same GIT_SHA.

First prepare the build-source bucket. On an existing demo the bucket is reused; it is only created when the lookup says it does not exist.

Then prepare a fresh temporary build context from the original source directories and `cloudbuild.yaml`. It excludes Terraform state, providers and plan files. Rerun this block whenever any source file changes.

Build the images. The helper submits one build; the chain runs them in order and stops at the first build that does not report SUCCESS. The UI is built from its own directory because its Dockerfile expects `requirements.txt` at the context root.

All seven names (ingest, api, admin, ui, chat, mcp, agent) show the same `$GIT_SHA` tag.

A Docker dependency-resolution failure is a source compatibility issue. Stop and keep the exact error before editing any dependency pin.

### Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer

Each image runs as its own service account, the human surfaces behind IAP, each deploy ending in a PASS line.

### F4. Deploy the ingest worker and RAG API

The worker Pub/Sub pushes to, and the API every surface calls.

Promote the ready API revision. Keep other service updates idle while this runs.

Both deploy blocks print PASS, and the promotion helper confirms readiness and 100% traffic.

### F5. Deploy the admin console with IAP

The operator console, behind Google sign-in.

This deployment creates `documind-admin`; Terraform and the image build do not. Confirm the project (yours, documind-ai-YOUR-ID) and region (asia-south1), and complete F2 first.

If the project has no Google organization, or your operator is outside it, the first IAP setup may need the Console: Cloud Run → documind-admin → Security → Identity-Aware Proxy. Complete the OAuth setup there, then rerun the failed command. Do not disable authentication to make the page load.

The admin Usage tab reads the BigQuery views `make bq-views` creates after the API's first answer (the UI step); the closing-targets step defers them until then.

### F6. Initialize the checkpoint schema, then deploy chat

The chat memory schema, then the chat backend.

`services/chat/migrate.py` runs `PostgresSaver.setup()` once in a job; the app never runs the migration on startup.

The job execution succeeds.

Chat is deployed as the kit's own script deploys it (`commands/lesson-12.8.sh`): a private service the UI reaches with the person's forwarded IAP assertion (`services/frontend/chat.py`, `shared/iap.py`), its callers bound one by one, and then IAP in front of it as well, the same door the UI and the admin console have. The Desk's five eval accounts are bound as soon as Terraform has made them, so `make smoke-cases` works later.

Test chat through the main UI's brain selector as a signed-in person. Opening the backend chat link directly in a browser is not an authenticated request and is not the end-to-end check.

### F7. Deploy the UI

The page people open, behind IAP.

`ADMIN_URL` is forwarded to the frontend because its Admin page reads it; the upstream command omitted it. This does not grant admin access. If IAP setup needs the Console, use the F5 browser procedure for documind-ui.

### F8. Deploy MCP, then the A2A agent

The tool server, then the agent that calls it.

The MCP server calls the RAG API through `shared.documind_tools`. The A2A agent calls MCP and contains no shared RAG code.

### Tenants: put people and services on the rosters

Without this, you can sign in to the UI and still get 403 on every question.

Three separate checks stand between a person and an answer, and each one fails in its own way:

The roster command is the kit's own: `commands/lane.py roster`, the same code `make roster` runs. It puts the members you name on one tenant, and on every run it also puts the service accounts that call the API on behalf of people onto the tenants they serve, and sets each tenant's data-region policy:

So the UI, MCP and chat accounts go on all three golden tenants (acme, zeta and globex), the A2A agent's account on acme only, and the policies become acme `any`, zeta `any`, globex `in`. The command writes to Firestore with your Application Default Credentials; if it fails with a permission error, run `gcloud auth application-default login --no-launch-browser` again (Phase 2, T2).

Preview first. The dry run writes nothing:

Now write it. The command adds members only to the tenant named by `--tenant`, so put yourself on each tenant in turn. Repeating the service-account entries is harmless: each one is the same Firestore document every time.

Each pass prints one `... is on ` line per member and service account, then `acme: data_region=any`, `zeta: data_region=any` and `globex: data_region=in`.

Read the rosters back from Firestore, the same documents the API checks on every request:

Your email and `documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com` appear under every tenant; `documind-agent-sa` appears under acme only.

To let a colleague in, they need both the door and the list: IAP access on the UI, and a place on the tenant they work in. Add several at once with a comma-separated list.

The make target does the same write, if you prefer it: `make roster PROJECT="$PROJECT" TENANT=acme MEMBERS="$OPERATOR_EMAIL"`. A colleague who should also see the admin pages needs their email added to `ADMIN_EMAILS` and F5 and F7 run again.

### Finish what make up finishes: the index wait, the managed stores and the BigQuery views

Four make targets, so this lane is the one `make up` would have built.

The kit's own `make up` does not stop at the deploy. Its recipe names what follows, and this runbook has done most of it by hand: the drift check in T7, the cookie secret in F2, the builds in F3, the deploys in F4 to F8 and the roster in the step before this one:

Four remain, and they are the kit's targets, run as they are. `wait-index` blocks until Firestore's composite indexes leave CREATING. `managed-stores` switches RAG Engine on once for the project, makes a corpus for each tenant whose text may travel (acme and zeta) and pins acme to `rag_engine` and zeta to `vertex_search`, so one deployment answers from all three stores; the data stores themselves were declared by Terraform (`managed_search=true`). `bq-views-when-ready` creates the usage views the admin console reads, once the table they read exists: the log sink's table appears only after the API has answered a first request, so on a new lane it prints that the views are deferred and you create them after the first answer (step 13). `vector-status` prints the index's own vector count, 0 until the first document is ingested. These targets read the state Phase 2 wrote, because the bucket and prefix are the kit's.

`>> indexes READY`, then `>> managed stores ready: corpora for acme zeta; acme reads rag_engine, zeta vertex_search, globex the kit's rows`, then `>> bq-views deferred: the log sink's table appears after the API's first answer` on a new lane (or the view statements' results, once it has answered), and the index's vector count, 0.

RAG Engine corpora are not Terraform's to destroy: `make down` runs `managed-stores-down` before its destroy, and so must you if you take the lane apart by hand.

### Verify all seven services

Seven services, Ready, on one tag.

Every service must be Ready and running an image tagged with the same `$GIT_SHA`.

Seven OK lines. For any PROBLEM or MISSING line, rerun that service's step above with the same `GIT_SHA`.

A Ready service is an infrastructure checkpoint. Next, sign in to the UI through IAP, ingest a document and ask a grounded question through the brain selector.

### Open the UI and ask a first question

The end-to-end check a person makes.

Print the UI's address and open it in a browser signed in as your operator account:

Google asks you to sign in; that is IAP. The page then shows your tenant (acme first). Upload a document on the Documents tab, wait for it to be indexed, and ask a question about it in Chat: the answer comes back with citations. Open the same address in a private window signed in as an account that is not on `ADMIN_EMAILS`: Google refuses it before the UI loads.

A 403 after you signed in means the roster, not IAP: rerun the tenants step and read the rosters back. A first-time IAP setup on a project without an organization may also ask for the OAuth consent screen in the console (Cloud Run, the service, Security, Identity-Aware Proxy); complete it there and retry the failed command. Never switch authentication off to make the page load.

That first answer is what the usage views were waiting for: the log sink has now exported the API's first rows, so BigQuery has the table the views read. Create them, from the kit root:

The admin console's Usage tab reads them. If `bq` still says Not found: Table, the sink has not exported yet: wait a minute and run it again. A Ready service is an infrastructure checkpoint, not proof the usage query has data yet.

### Verify it yourself: the checklist

Each claim this page makes, the command that proves it, and what a pass looks like.

Everything, from nothing. Cloud Shell holds the kit at `~/deploy_module_rag`, Python 3.12 in `~/rag-shell-venv` and your settings in `~/rag-env.sh`, including the pinned `GIT_SHA`. Your project has the APIs, a versioned state bucket and everything Terraform declares: service accounts, buckets, Firestore, Vector Search with its deployed index, two Cloud SQL instances, Spanner, the network and the budget. Artifact Registry holds seven images under one tag; Cloud Run runs 7 services, the UI and admin console behind IAP; Firestore holds the rosters for acme, zeta and globex; RAG Engine holds a corpus for acme and one for zeta, with acme pinned to its corpus and zeta to its Vertex AI Search data store; BigQuery has the usage views. From the end of the apply until you delete the project, the standing items bill every hour.

Netsetos GenAI on GCP · Module 0 Setup · Lesson 0.5 Set up the cloud lane end to end: clone in Cloud Shell, create the infrastructure with Terraform, deploy every service and the UI · v5.0

Next: Lesson 1.1 Understand source, tenant, page and chunk contracts.
