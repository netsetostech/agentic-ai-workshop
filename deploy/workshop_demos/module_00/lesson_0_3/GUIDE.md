# Lesson 0.3: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_0.3_Deploy_Lane_WIX.html`, reviewed at blob `840ab0010164fb7bf8900b43fb668aa2e80d08fb`. Learners read that page on the course site; this guide keeps its prose.

Lesson 0.2 left you with an operator shell and a lane that runs on your laptop for nothing. This lesson builds the real one in your Google Cloud project, and reads it before it exists: the accounts the kit creates and what each of them may touch, the stores it declares, the switches that would add more, and the items that bill by the hour whether anyone uses them or not. Then you run one `make plan`, read it, let the kit's guard check it, and run one `make up` from a blank project: images built, every service deployed as its own account, the UI behind Google's sign-in, and your address on the roster.

- What a lane is: one project, its identities, its resource map

- The words: state, plan, account, actAs, invoker, IAP, roster

- Before you run anything: open the operator shell

- A blank project, made ready for a plan

- Identities: 19 accounts, seven of them running a service

- The stores, and the switches that add more

- make plan: a saved plan, checked before you apply it

- make up: apply that plan, then build, deploy and seed

- Seven services, and the account each runs as

- The UI behind IAP, and the roster behind the UI

- What bills by the hour, in rupees

- Verify it yourself: the checklist

You will learn what the kit creates in your project before it creates it: 19 service accounts and what each may touch, the stores, and the items that bill by the hour. Then you deploy the lane once from a blank project with `make plan` and `make up`, and prove it: every resource listed in the plan, seven services up, each as its own account, and the UI behind IAP.

### What a lane is: one project, its identities, its resource map

Three ideas the rest of the page rests on, and a map you can click.

A lane is one complete copy of DocuMind in one Google Cloud project: yours, made in lesson 0.1 with billing and a budget on it. Nothing in it is made by hand. Terraform, reading the kit's `terraform/` folder, declares the infrastructure: the accounts, the buckets, the databases and their indexes, the network, the search index, the alerts. Cloud Build turns each service's source into an image. Then seven gcloud scripts deploy the services, one script per service. `make plan` and `make up` are the two commands that drive all of it.

Identities are the part that is easy to skip and expensive to get wrong. A program on Google Cloud never acts as "the system". It acts as a service account, an identity with roles but no password, and every call it makes is allowed or refused by what that account holds. The kit gives each of the seven services its own account, and grants each one what its code uses and nothing it does not: the UI's account cannot read the warehouse, the ingest worker's cannot read a secret, the A2A peer's cannot touch Firestore at all. The same thinking guards the doors. IAM decides which accounts may call a service. IAP, Google's sign-in in front of the UI, decides which people may reach it. The roster, a few documents in Firestore, decides which tenant each signed-in person may read.

The resource map is the whole list: 234 resource instances for a blank project, by the kit's own files, and a small part of it that bills by the hour while it exists, used or idle. Knowing which part that is turns "I deployed something" into "I know what I am paying for", which is what lesson 0.4 needs when it switches the lane off.

A new office building. The project is the building, on one lease and one electricity meter (the billing account). The service accounts are the staff ID cards: the cleaner's card opens the store rooms, the accountant's opens the finance office, and nobody's card opens every door. The Terraform plan is the architect's drawing, signed before any wall goes up; the kit's guard refuses any drawing that would knock a wall down. `make up` is the construction crew: it builds exactly the signed drawing, moves the staff in, each with their own card, and hands reception the guest list.

IAP is the reception desk: it checks your ID at the front door and turns away anyone not on its list. The roster is the floor directory: it says which floor (which tenant) a visitor may go to once inside. And a few rooms keep their lights on day and night whether anyone is in them or not. Those are the hourly items, and step 10 names them with their price.

#### From a blank project to a running lane, in five moves

The counts are the kit's own, read from its Terraform and Makefile when this page was built. Steps 3 to 9 run each move on your project and show what it printed on the author's lane.

#### Click an account, see what it may touch

Every account the kit declares is in the menu below, grouped by what it is for. Choose one and the map lights the stores its roles reach, then lists the roles themselves, the grants on single resources (one bucket, one secret, one database), who may call it if it runs a service, and who may act as it. All of it is read from `terraform/*.tf` and from the deploy scripts `make up` runs, when this page was built: if the kit changes a grant, the map changes with it.

documind-ui-sa | DocuMind UI (Streamlit on Cloud Run) | terraform/sa.tf | touches 7 of 18 stores

- `documind-ui`, deployed by `commands/lesson-12.4.sh`

- ingress all, IAP in front

- min MIN_INSTANCES (0), max 10

- calls `documind-api`, `documind-chat`

- IAP's service agent

- `roles/aiplatform.user`

- `roles/datastore.user`

- `roles/documentai.apiUser`

- `roles/secretmanager.secretAccessor`

- `roles/speech.editor`

- bucket `PROJECT-uploads`: `roles/storage.objectAdmin`

- bucket `PROJECT-tts-cache`: `roles/storage.objectAdmin`

- bucket `PROJECT-media`: `roles/storage.objectViewer`

- secret `litellm-master-key`: `roles/secretmanager.secretAccessor`

- secret `cookie-secret`: `roles/secretmanager.secretAccessor`

- secret `oauth-client-id`: `roles/secretmanager.secretAccessor`

- secret `oauth-client-secret`: `roles/secretmanager.secretAccessor`

- secret `openai-fallback-key`: `roles/secretmanager.secretAccessor`

- secret `hf-token`: `roles/secretmanager.secretAccessor`

- `documind-off-sa`: `serviceAccountUser`

- `documind-ui-sa`: `serviceAccountTokenCreator`

- `sa-documind-cicd`: `serviceAccountUser`

- `sa-documind-cicd`: `serviceAccountTokenCreator`

- each address in ADMIN_EMAILS (make operators, run by make up): `serviceAccountTokenCreator`

A lit store is one the account's roles or grants reach. A role held at project scope reaches every resource of its kind, including any added later: that is why the ingest worker lights all five buckets while the UI's account lights three, each granted by name. Try `documind-agent-sa` (Vertex AI and nothing else), `documind-outsider-sa` (no role at all) and `sa-documind-cicd` (no data, but it may act as eight accounts).

It is what the kit's files grant, not a live read of your project's IAM. Google's own service agents (Pub/Sub's, IAP's, Dataplex's), roles your organization grants from above, and anything you add by hand are not in it. Two accounts appear that a default lane does not have: the Google Chat bridge's pair, declared only when `GCHAT_DOOR=true`. Step 8 checks the part that matters most on the live lane: the account each running service really uses.

### The words: state, plan, account, actAs, invoker, IAP, roster

Thirteen words, each with the value it takes on your lane.

Three of these words are about permission to reach something (project role, invoker, IAP) and three about permission to become something (actAs, Token Creator, the CI trust). The second kind is the dangerous kind: a role you cannot hold yourself is a role you can borrow from any account you may become. Every step below comes back to one of them.

### Before you run anything: open the operator shell

Every command on this page runs in the operator shell you set up in lesson 0.2: the kit cloned at `~/deploy_module_rag`, the `rag-shell-venv` environment with the kit's Python packages in it, and gcloud signed in with your lesson 0.1 project as its default. Later lessons open with a block that builds the API's address and mints tokens to call it. This one cannot: the lane does not exist yet. The block below brings the kit up to date, reads the project and the region from gcloud, names the state bucket you create in step 3, sets `ADMIN_EMAILS` to your own address (the people IAP will let in, and the first name on the roster), and checks the tools `make up` drives. Run it once per session; every block below uses the variables it exports.

No `kit` line, or `cd` failing, means the kit was never cloned on this machine: lesson 0.2's clone block makes it. `git pull` refusing with Your local changes would be overwritten means a kit file was edited here: `git -C "$DEMO_ROOT" status` names it and `git -C "$DEMO_ROOT" stash` sets the edit aside. A missing `activate` file means the venv was never made on this machine, which is lesson 0.2 again. `PROJECT=` empty means gcloud has no default project: `gcloud config set project YOUR-PROJECT-ID` with the id from lesson 0.1, then the block again. A `REGION` other than `asia-south1` means your gcloud configuration names another `run/region`: the course's lane runs in Mumbai and every later lesson's addresses say so, so run `gcloud config set run/region asia-south1` and the block again. `ME=` empty means gcloud is not signed in: `gcloud auth login`. No `Terraform` line, or a version below 1.9, is fixed in step 3, where `make preflight` prints the install line; `terraform/backend.tf` requires 1.9 or newer. No `BigQuery` line means the Google Cloud CLI on this machine lacks `bq`, which `make up`'s last steps call. `adc NOT ok` means Application Default Credentials, the sign-in Terraform and the kit's Python libraries use, is missing: it is separate from gcloud's own. Run `gcloud auth application-default login --no-launch-browser`, open the link, sign in as the account you use for this project, paste the code back, and run the block again.

#### Three kinds of code window on this page

A window labelled bash is a block to paste into the operator shell, whole, and press Enter; it has a copy button. A window labelled with a kit file is that file's own lines, verbatim, to read. A window labelled expected or text was computed from the kit when this page was built, with your values written as placeholders (`documind-ai-YOUR-ID`, `NUMBER`, `you@example.com`). A window labelled output is what the command printed on the author's lane, deployed once from a blank project for this lesson, with the project id, its number and the email replaced by the same placeholders. None of the read-only windows has a copy button.

#### make, or the command it runs

Each target this lesson uses is a short entry in the kit's `Makefile` or `mk/ingestion.mk` that runs a script or the kit's own Python, so you can run the same code without make:

### A blank project, made ready for a plan

The APIs, a state bucket of your own, the one repository you trust, and the sign-in screen IAP will show.

"Blank" here means the project from lesson 0.1 with billing linked and a budget on it, and nothing of the kit's yet: no Terraform state, no accounts, no services. Four things should exist before `make plan` and `make up` run, and the plan itself makes none of them: it reads the project, it never prepares it. Each takes a minute, and the kit's preflight then says whether the project is ready.

#### 1. The APIs

A Google Cloud API is off until a project turns it on, and Terraform cannot create a resource whose API is off. `make apis` turns on the 40 the lane uses, in two calls, because the Service Usage API takes at most twenty at a time. It is safe to run again; an API already on stays on.

What it prints is gcloud's own report of the operations it waited for. Step 5's preflight is the check that matters: it names any of the APIs it looks for that is still off.

#### 2. A state bucket of your own

Terraform keeps its record of what it built, the state, in a bucket, so that the next plan in any shell compares the files with what exists instead of trying to create everything again. Bucket names are global: the first person in the world to create a name owns it. The Makefile's default, `documind-tfstate`, is one name for the whole world and can serve only one lane, so the setup block named yours after your project, the form the kit's own `smoke/preflight.sh` uses in its example. It exported `TFSTATE_BUCKET` and `TFSTATE_PREFIX` too, so the targets that connect to the state later (`make tf-backend`, `make down`) find this one. Versioning keeps every earlier copy of the state file, which is how a damaged state is recovered.

The last command ends on Terraform's line Terraform has been successfully initialized! It connects this checkout to the state and downloads the providers `terraform/backend.tf` pins. Run it again only on a new machine or a fresh clone, and always with the same bucket and prefix: `terraform/` in a checkout pointed at another prefix is a checkout that believes the lane does not exist.

#### 3. The one repository you trust to deploy

The kit includes a keyless pipeline: `terraform/wif.tf` declares a workload identity pool that lets GitHub Actions workflows from one repository, on one branch, become `sa-documind-cicd`, the pipeline's account, with no key file anywhere. That account may act as 8 accounts (step 4), which makes this one of the most powerful settings in your project: whoever controls that repository's workflows can deploy code that runs as your services. Lesson 11.1 builds and deploys through this trust. A new project has to name it now, and the kit refuses to guess.

Name a repository you own, for instance your fork of `netsetos/agents_workshop_learner`. Its numeric id is what the trust is really keyed on, because a repository's name can be released and claimed by someone else and its id cannot. `prepare` then reads your project and its billing account, checks that the project has no GitHub provider the state does not know about, and saves the three values with your project, region and billing account in `terraform/runbook-project.auto.tfvars.json`, a local file Git ignores. Every later plan reads them from there.

The kit's `README.md` and `INFRASTRUCTURE.md` show a repository name, a numeric id and a branch in their examples. They are the kit author's. Pasted into your project, they would let that repository's workflows deploy into your lane as `sa-documind-cicd`. Use your own, and if `prepare` stops with Set the CI repository as OWNER/REPO or the CI repository's immutable numeric GitHub ID, one of the two variables above came back empty: `echo` them before running it again. Once applied, the trust is protected: a later plan that would change it is refused (step 6), so changing your mind later is a deliberate migration, not an accident.

#### 4. The sign-in screen IAP will show

IAP signs people in with Google's OAuth, and an OAuth sign-in needs a consent screen with a name on it. Configure it once in the console, under Google Auth Platform > Branding: an app name such as DocuMind and your address as the support e-mail. The kit cannot check this for you, and its preflight says so on its last line. Whether you need more depends on where your project lives:

If it prints `organization` and the people you will let in belong to that organization, IAP's Google-managed sign-in is enough. If it prints nothing, which is the usual case for a project made with a personal account, Google's IAP guide says you must bring your own OAuth client: IAP's managed client serves only people inside an organization, and a project outside any organization has none. In the console, create one under Google Auth Platform > Clients (or APIs & Services > Credentials), type Web application; once it exists, add the redirect URI `https://iap.googleapis.com/v1/oauth/clientIds/CLIENT_ID:handleRedirect` with its own client id in place of `CLIENT_ID`. Set the consent screen's audience to External; while it is in testing, list each address in `ADMIN_EMAILS` as a test user. Then hand the client to IAP for the whole project:

The settings file shape and the redirect URI are Google's, from the IAP guide Configure IAP with a custom OAuth client. The kit itself never sees the client: `terraform/secrets.tf` declares empty `oauth-client-id` and `oauth-client-secret` holders, and nothing in the kit reads them.

#### 5. Ask the kit whether the project is ready

`make preflight` reads, and creates nothing: the four tools on `PATH` and Terraform's version, your sign-in, the project and its billing, the state bucket, 22 of the APIs, and the one Python package `make roster` needs. A line that starts with `MISS` carries the command that fixes it.

### Identities: 19 accounts, seven of them running a service

Who each account is, who may become it, and who may call what.

The kit declares 19 service accounts on a default lane (21 with the Google Chat door on). Most live in `terraform/sa.tf`; the rest sit beside the resource that needs them, so the file that creates a thing also creates the identity it runs as. Read the table by its third column: seven accounts run the services `make up` deploys, two run a job or a machine, one is the pipeline, six are fixtures (identities that exist only so a test can call the lane as someone it must refuse or admit), two run services a later module deploys on request, and one is declared for a job no target deploys yet.

The file's own first comment still says three accounts, as the README's layout does (ui, api, admin). Most accounts added since carry a comment saying why they are not a reuse of an older one:

#### Seven services, seven accounts: what the deploy scripts say

Terraform does not create the services: `gcloud run deploy` in each deploy script does, and the script names the account the service runs as and the callers it admits. This table is read from the seven scripts `make up` runs. Step 8 checks it against the live lane.

Two columns carry the design. Who may call it is the caller graph: each service admits by name the accounts that call it and no one else. `roles/run.invoker` is never granted on the project, because a project-wide invoker would let every account call every service, the A2A peer included, and the peer refuses nobody by roster. The graph is written down twice, in `sa.tf` and in the loops of the scripts, and a check run on every change to the kit fails when the two disagree. This page's build makes the same comparison for the services `make up` deploys.

#### Who may become an account: actAs and token minting

A role you cannot hold yourself is a role you can borrow from any account you may become, so the grants on accounts matter as much as the grants they hold. The pipeline's account must act as every account it deploys a service as; that is inherent. What the kit controls is the list: 8 accounts named one by one, never `roles/iam.serviceAccountUser` on the project, which would include every account created later.

Minting tokens is the other way in. `make up` ends its deploy step with `make operators`, which lets each address in `ADMIN_EMAILS` mint tokens as the UI's account and the outsider; that is how your shell calls the API as a surface would (lesson 1.1's setup does exactly that) and as a stranger would. Project Owner does not carry this permission, and the kit's first live run stopped on its absence.

#### One account's roles, with the reasons for the missing ones

The UI's account is a good one to read in full, because its comments explain two roles it does not have: the invoker role, removed in favour of the caller graph, and every BigQuery role, kept out so that a flaw in the page that renders user chat cannot reach the warehouse.

The DocuMind Desk added the newest accounts: five people the Desk's live checks call the chat service as, each a service account because a script cannot mint a token as a person. None holds a project role. Each is admitted to `documind-chat` and to nothing else, and goes on one tenant's roster only when a later lesson puts it there.

### The stores, and the switches that add more

Every bucket, index and database the plan creates, where each lives, and what a switch would add.

Two variables decide where things go. `REGION` is where the services run, and with them the connector, the image repository, the search index, the databases and the cluster; the setup block set it to `asia-south1`. Data at rest that must stay in India, Firestore and the buckets, follows `india_region` in `terraform/variables.tf`, which is `asia-south1` whatever `REGION` says.

#### Five buckets

The last column is the one to read twice. Three accounts reach every bucket because they hold a storage role on the whole project, and `sa.tf` gives each one's reason: the ingest worker reads the uploaded object and writes audit rows, the MCP server writes audit rows, the admin console writes its exports to the audit bucket. Everyone else is granted bucket by bucket. The audit bucket keeps every object for five years and refuses to delete one inside that term; locking the policy as well is a separate, irreversible decision the kit leaves off for a lab:

#### Firestore: 17 composite indexes and four TTL fields

One database, `(default)`, in `asia-south1`, with point-in-time recovery and delete protection on. A vector search over chunks needs a composite index for every combination of filters a query can carry, which is why `chunks` alone has most of them; the graph walk and the Desk's case queue add their own. A TTL field names the timestamp after which Firestore deletes a row by itself: nothing else on the lane deletes a chunk.

A new index takes minutes to build, and a vector query against an index still building fails. That is why `make up` waits for them (step 7).

#### The other stores, and the rest of what a plan creates once

One line in `terraform/vector.tf` deserves a second look before step 10 prices it. The deployed index runs on a machine chosen by the index's shard size, and the index declares none, so the service picks it. The kit's own comment records an existing index whose service-selected size was MEDIUM, which deploys on `e2-standard-16`, not on SMALL's `e2-standard-2`. Step 8 reads which one your lane got.

#### 234 resource instances, file by file

Counting every resource block, with each `count` and `for_each` worked out for the values `make plan` passes, gives the number a blank project's plan should add. One variable moves it: each address in `ADMIN_EMAILS` adds one e-mail channel for the alerts.

#### The switches: off now, and refused once they have been on

Some of the kit's resources exist only while a Makefile variable says so: jobs that need an image to exist first, alerts that need data first, a door that needs Google Workspace. All six are off on a first lane. The trap is turning one off again: a later plan without it would delete what it declared, so the plan's guard refuses, and its refusal names these switches.

Nothing on this page turns a switch on. When a later lesson does, the rule is the same for all of them: keep the switch on every later `make plan` and `make up`, and on the other job targets, or the next plan stops.

### make plan: a saved plan, checked before you apply it

What the target passes, what `infrastructure.py` refuses, and the plan that lists every resource.

`make plan` is one line in the Makefile. It hands `commands/infrastructure.py` your project and region and a list of Terraform variables: the switches, the managed stores, the embedding, the budget. The critical values, the project, the region, the billing account and the three of the CI trust, are not on that list, and a `--var` that names one is refused. They come from the inputs file `prepare` saved in step 3, passed last so that nothing set in a shell can override them.

`plan()` does five things in order: it unselects any older plan, so a failed run can never leave yesterday's plan ready to apply; it reads the project, billing and trust again; it writes a new plan to a file with a unique name; it checks that file; and only then records it as the selected plan, with a hash of the file and the state's serial number, so that `make up` can tell whether anything moved in between.

The check reads Terraform's machine-readable plan, not the text you scroll through. It refuses an incomplete plan, inputs that differ from the confirmed ones, any change to the existing CI trust, and any delete: a replacement is a delete followed by a create, so it is refused too. On a blank project nothing exists to delete, and the check passes. It earns its place on every plan after this one.

Run it now. Terraform prints the whole plan, one block per resource, so the block keeps a copy in `~/plan.log` and then prints only the lines that summarize it.

The kit's files declare 234 resource instances for this lane (step 5, with one address in `ADMIN_EMAILS`), so Terraform's summary should be `Plan: 234 to add, 0 to change, 0 to destroy.` It sits between the two `PASS` lines `infrastructure.py` prints: the saved inputs before the plan, the passed check after it.

#### Every resource, counted from the saved plan

The plan file is binary; Terraform turns it into JSON on request. The cell below counts what the plan would create, by type, in the same format as the count this page made from the kit's files, so the two can be read side by side. Run it before `make up`: the apply consumes the selection record that names the file.

Every line of the two should match: 55 resource types, 234 instances, and only `create` among the actions. A count that differs means the plan read a file or a variable differently from the way this page assumed; find which before the apply, not after it. To read the plan itself, `terraform -chdir=terraform show "$PLAN" | less` prints it as text; on a later plan, the words to search for are must be replaced and will be destroyed.

### make up: apply that plan, then build, deploy and seed

One apply of the checked file, then nine more targets, in order.

`make up` never makes a plan to apply. Its first line applies the plan `make plan` selected, after checking it twice more: the file's hash, the backend, the inputs and the state's serial must all be what they were when the plan was checked. If anything moved, it stops and asks for a new plan. Then it removes the selection record, so the same file can never be applied twice.

The second line runs nine targets in one make, so the first one to fail stops the rest:

The build is Cloud Build, one image per service, each tagged with the kit's commit. Every service but the UI builds from the whole kit with one config and its own Dockerfile, because most of them import the kit's `shared/` folder; the UI is self-contained and builds from its own folder. `commands/lesson-12.8.sh` and `commands/lesson-8.4.sh` also carry a build of their own inside their DEPLOY block, so a first `make up` builds those two images twice.

The deploy step is the reason the kit has no second copy of its deploy flags: it cuts the block between `# ---- DEPLOY ----` and the next marker out of each script and runs it as it is, in the order the services must come up. The worker comes first, because the push subscription Terraform made already points at its address.

Now run it. It takes a long time: Cloud SQL, the GKE cluster and the deployed index each take minutes to create, and the builds run one after another. Run it inside `tmux` if your shell has it, so that a closed browser tab or a dropped connection does not stop an apply halfway; an interrupted apply needs a new plan. `time` reports how long it took.

A plan refused as stale (The saved plan is stale; create a new plan, or The selected plan is missing or changed): the state, the inputs or the file changed since `make plan`. Run step 6 again, read the new plan, then `make up`. An apply that failed halfway: keep the state as it is. Terraform has recorded everything it created, so the next `make plan` lists only what is still missing; read it, then `make up`. Never delete the state or `terraform/.terraform` to "start clean": the next apply would try to create everything again over resources that exist. A build that stops at `storage.objects.get` with a 403 naming the Compute Engine default account: Cloud Build runs as that account when the kit names none, and in an organization created on or after 3 May 2024 it is created without the broad role older projects gave it. Grant it exactly what a build needs (the block below), and wait a few minutes for IAM to apply the grants. The apply had already finished by then and its plan is used up, so run `make plan` (it reports no changes) and `make up`, which applies nothing and carries on from the build. A drift line after the apply means the plan after it is not empty: a resource the provider reads back differently from how it was written. It does not stop `make up`, but it is a definition to fix before the next apply repeats it. A `bq-views` failure naming a table or a field that does not exist: the view reads the log sink's table, and the kit's own comment on the target (below) says that table is typed by the rows the API has logged. Every service is deployed by then; run `make bq-views` again once the API has answered a question (lesson 0.4's smoke asks the first one), then `make vector-status`, the one step left.

Three narrow grants: read access to its own source bucket only, push access to the `documind` repository, and log writing. Not Editor, and not `roles/cloudbuild.builds.builder` on the project: either would let every build read, write and delete every object in every bucket, the uploads of customer documents included.

### Seven services, and the account each runs as

The first proof: the services are up, and each runs as the account step 4 said it would.

Cloud Run keeps the account a service runs as on the service itself. Listing the services with that one field beside the name is the whole check: 7 rows, each with its own account, matching the table in step 4.

A service missing from the list was not deployed: `~/up.log` shows which DEPLOY block stopped, and the services after it in the order (`documind-ingest`, `documind-api`, `documind-admin`, `documind-ui`, `documind-chat`, `documind-mcp`, `documind-agent`) are missing too, because the loop stops at the first failure. A service running as the Compute Engine default account would mean a script lost its `--service-account` flag; none of the seven does today. Besides the services, the lane now has two Cloud Run jobs: `documind-off`, from `terraform/off.tf`, and `documind-checkpoint-setup`, which the chat service's script creates and runs to prepare its database.

#### The shard size the service chose

Step 5 left one fact open: the deployed index's machine follows the index's shard size, and the kit lets the service choose it. Read both from the live lane; step 10 prices the row that matches.

### The UI behind IAP, and the roster behind the UI

Who gets in, who is turned away at the door, and who gets in but sees nothing.

The UI's script puts IAP on the service itself: the `run.app` address is the front door, and nothing reaches the container without passing IAP. Two grants finish the job. IAP's service agent may invoke the service, since it is now the only caller; and each address in `ADMIN_EMAILS` may pass IAP. Being let in is still not membership: the roster decides what a person sees.

So a visitor meets up to three checks, and each kind of visitor stops at a different one:

The first two rows can be checked from the shell. A request with no sign-in should come back as a redirect to Google's accounts page (the block cuts the redirect at its query string, which carries the OAuth client's id), and IAP's policy on the service should list your address with the accessor role.

The last two rows need a browser. Open the address the first line below prints, sign in as yourself, and look at the sidebar. Then open it in a private window and sign in with a Google account that is not in `ADMIN_EMAILS`.

A sign-in that fails before IAP's refusal page, with Google's Access blocked or an OAuth error, is the sign-in screen from step 3, not the lane: a project without an organization needs its own OAuth client, and while that client's consent screen is in testing it admits only the test users it lists.

#### The roster make up wrote

`make roster` ran inside `make up`, after the indexes were ready. It puts every member of `MEMBERS`, which defaults to `ADMIN_EMAILS`, on `TENANT`'s roster; the UI's, the MCP server's and the chat service's accounts on all three golden tenants, because each calls the API as itself; the A2A peer's on acme only; and it records where each tenant's text may be held. Lesson 1.1 reads these documents in Firestore, and lesson 4.6 follows one request through every check that reads them.

Its dry run prints the plan and writes nothing, so it can be read before it is trusted. This one was computed from `commands/lane.py` when this page was built, with your placeholders:

### What bills by the hour, in rupees

Five kinds of resource cost money every hour they exist, whether anyone asks the lane a question or not.

Most of the lane bills for what you do with it: a page parsed, a token generated, a gigabyte stored, a message delivered. A few things bill for existing. The kit says which, in its own words, in three places:

The cluster and the connector complete the list. The cluster is a regional Standard one, so its management fee is not covered by GKE's free-tier credit, and its node is an ordinary Compute Engine machine. The connector keeps at least two small machines running so that the services can reach the VPC.

The table prices each line as lesson 0.1 does: the declaration's size times Google's list price for Mumbai (`asia-south1`, where the course's lane runs its services and where `spanner.tf` keeps the graph), read from Google's pricing pages on 7 October 2026, at the kit's rate of Rs 85 to the dollar from `shared/prices.py`. Of the kit's own figures above, the cluster fee matches; Cloud SQL comes to $11.24 a month for each instance at these prices, above the roughly $8-10 that `cloudsql.tf`'s comment gives. The Vector Search row has two machines because the service chose the shard size: step 8's output says which line is yours.

What is not in the table matters as much. The seven Cloud Run services cost nothing while idle at their default floor of zero instances; `MIN_INSTANCES=1`, the kit's setting for a session day, would floor `documind-ui`, `documind-mcp` and `documind-agent` at one instance each. Firestore, the buckets, BigQuery, Pub/Sub, Secret Manager, Document AI, Gemini and the managed stores bill per use or per gigabyte stored, so they cost little until something is ingested or asked. `make off` floors the UI and the GPU services to zero but leaves every row of the table running; only `make down` and deleting the project remove them. Lesson 0.4 turns these rows into what a day of a lane left up costs, and switches it off.

### Verify it yourself: the checklist

Twelve checks, each one block above, each with the value that proves it on your lane.

Everything: the project went from blank to a running lane. 40 APIs are on. The state bucket you made yourself holds Terraform's record of 234 resources: 19 accounts with their roles, five buckets, Firestore with 17 indexes and four TTL fields, Vector Search with its deployed index, two Cloud SQL instances, Spanner, `rag_data` and `documind_observability` in BigQuery, a GKE cluster, the network, the alerts and the budget. Artifact Registry holds seven images; Cloud Run runs seven services and two jobs. Firestore holds the roster's 11 memberships and three data-region policies; RAG Engine holds empty corpora for acme and zeta. On your machine, `terraform/` is connected to the state and holds the saved inputs and the applied plan file. From the end of the apply, the rows of step 10 bill every hour. Lesson 0.4 proves the lane end to end, breaks it once on purpose, and switches it off.

Netsetos GenAI on GCP · Module 0 Setup · Lesson 0.3 Understand the project, identities and resource map, and deploy the lane · v5.0

Next: Lesson 0.4 Prove the lane, break it once, and switch it off.
